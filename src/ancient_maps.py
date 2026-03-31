# -*- coding: utf-8 -*-
"""
Ancient World Explorer module for TerraScout AI.
Curated databases of the oldest cities, ancient libraries, ports, wonders,
observatories, water systems, mining sites, cave art, ancient sports venues,
and historic roads of the ancient world.
No API keys required -- all data is curated/embedded.
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

# ===============================================================================
# THEME CONSTANTS (TerraScout AI dark theme)
# ===============================================================================
_BG = "#0a0e1a"
_SURFACE = "#111827"
_CARD = "#1a2235"
_BORDER = "#2a3550"
_TEXT = "#e8ecf4"
_TEXT2 = "#8b97b0"
_MUTED = "#5a6580"
_ACCENT = "#06b6d4"
_AMBER = "#f59e0b"
_VIOLET = "#8b5cf6"
_EMERALD = "#10b981"
_RED = "#ef4444"
_PINK = "#ec4899"
_ORANGE = "#f97316"
_BLUE = "#3b82f6"
_GOLD = "#eab308"
_TEAL = "#14b8a6"

# ===============================================================================
# MODE DESCRIPTIONS
# ===============================================================================
MODE_DESCRIPTIONS = {
    "Oldest Cities in the World": (
        "The oldest continuously inhabited cities on Earth, with roots stretching "
        "back 5,000 to 11,000 years. From Damascus and Jericho to Varanasi and "
        "Athens, these urban centers have witnessed the entire arc of human civilization."
    ),
    "Ancient Libraries & Archives": (
        "The great repositories of ancient knowledge: the Library of Alexandria, "
        "the clay tablet archives of Ebla and Nineveh, the scrolls of Pergamum, "
        "and other centers of learning that preserved the wisdom of antiquity."
    ),
    "Ancient Ports & Harbors": (
        "Phoenician, Greek, Roman, and other ancient harbors that connected the "
        "Mediterranean world and beyond. These ports drove commerce, colonization, "
        "and cultural exchange for millennia."
    ),
    "Seven Wonders of the Ancient World": (
        "The original sites of the Seven Wonders as described by ancient Greek "
        "travelers: the Great Pyramid, Hanging Gardens, Temple of Artemis, Statue "
        "of Zeus, Mausoleum, Colossus, and Lighthouse of Alexandria."
    ),
    "Ancient Observatories": (
        "Prehistoric and ancient astronomical sites where early humans tracked the "
        "stars, solstices, and equinoxes. From Stonehenge to Angkor Wat, these "
        "structures reveal sophisticated celestial knowledge."
    ),
    "Ancient Water Systems": (
        "Roman aqueducts, Persian qanats, Incan channels, and other engineering "
        "marvels that brought water across deserts, over valleys, and through "
        "mountains -- feats that still inspire modern engineers."
    ),
    "Ancient Mining Sites": (
        "The mines that fueled ancient economies: Laurion silver funded the "
        "Athenian navy, Hallstatt salt preserved a Bronze Age culture, and Timna "
        "copper supplied the pharaohs. Resources shaped empires."
    ),
    "Prehistoric Cave Art": (
        "The oldest known artworks of humanity: painted caves from Lascaux and "
        "Altamira to Chauvet and the Indonesian caves of Sulawesi. Some paintings "
        "are over 45,000 years old."
    ),
    "Ancient Games & Sports Venues": (
        "Where the ancient world played and competed: the Olympic stadium at "
        "Olympia, the Roman Colosseum, Mesoamerican ball courts, Greek hippodromes, "
        "and the great amphitheaters of antiquity."
    ),
    "Ancient Roads & Highways": (
        "The great road networks of antiquity: the Roman Via Appia, the Persian "
        "Royal Road, the Incan Qhapaq Nan, and other highways that connected "
        "empires and enabled the movement of armies, trade, and ideas."
    ),
}

# ===============================================================================
# CURATED DATASETS
# ===============================================================================

OLDEST_CITIES = [
    {"name": "Damascus", "lat": 33.5138, "lon": 36.2765, "country": "Syria", "est": "c. 10000 BC", "desc": "One of the oldest continuously inhabited cities in the world. Capital of the Umayyad Caliphate and a crossroads of civilizations for over 11,000 years.", "color": _AMBER},
    {"name": "Aleppo", "lat": 36.2021, "lon": 37.1343, "country": "Syria", "est": "c. 5000 BC", "desc": "Ancient city at the crossroads of trade routes. The Citadel of Aleppo sits on a tell with evidence of occupation since the 3rd millennium BC.", "color": _AMBER},
    {"name": "Jericho", "lat": 31.8611, "lon": 35.4597, "country": "Palestine", "est": "c. 9000 BC", "desc": "Often cited as the oldest city on Earth. Tel es-Sultan shows continuous habitation for over 11,000 years, with the oldest known protective wall.", "color": _GOLD},
    {"name": "Athens", "lat": 37.9838, "lon": 23.7275, "country": "Greece", "est": "c. 5000 BC", "desc": "Birthplace of democracy, Western philosophy, and classical civilization. The Acropolis has been inhabited since at least the 4th millennium BC.", "color": _VIOLET},
    {"name": "Varanasi", "lat": 25.3176, "lon": 82.9739, "country": "India", "est": "c. 3000 BC", "desc": "The holiest city in Hinduism, continuously inhabited for over 5,000 years. Mark Twain called it 'older than history, older than tradition.'", "color": _ORANGE},
    {"name": "Byblos", "lat": 34.1236, "lon": 35.6511, "country": "Lebanon", "est": "c. 7000 BC", "desc": "Ancient Phoenician port city. The word 'Bible' derives from Byblos, as the Greeks imported papyrus from here. UNESCO World Heritage Site.", "color": _AMBER},
    {"name": "Sidon", "lat": 33.5600, "lon": 35.3729, "country": "Lebanon", "est": "c. 4000 BC", "desc": "Major Phoenician city-state and one of the most important ports of the ancient Mediterranean. Known for purple dye production and glassmaking.", "color": _TEAL},
    {"name": "Plovdiv", "lat": 42.1354, "lon": 24.7453, "country": "Bulgaria", "est": "c. 6000 BC", "desc": "One of Europe's oldest continuously inhabited cities. The ancient Thracian settlement of Eumolpias predates Athens and Rome by millennia.", "color": _EMERALD},
    {"name": "Susa", "lat": 32.1942, "lon": 48.2480, "country": "Iran", "est": "c. 4200 BC", "desc": "Capital of the Elamite Empire and later a key Achaemenid Persian city. The Code of Hammurabi was discovered here. One of the oldest known settlements.", "color": _AMBER},
    {"name": "Luxor (Thebes)", "lat": 25.6872, "lon": 32.6396, "country": "Egypt", "est": "c. 3200 BC", "desc": "Ancient Thebes, capital of Egypt's New Kingdom. Home to the Valley of the Kings, Karnak Temple, and Luxor Temple.", "color": _GOLD},
    {"name": "Jerusalem", "lat": 31.7683, "lon": 35.2137, "country": "Israel/Palestine", "est": "c. 4500 BC", "desc": "Sacred city to Judaism, Christianity, and Islam. The Old City contains the Western Wall, Church of the Holy Sepulchre, and Dome of the Rock.", "color": _VIOLET},
    {"name": "Balkh", "lat": 36.7583, "lon": 66.8972, "country": "Afghanistan", "est": "c. 1500 BC", "desc": "Called the 'Mother of Cities' by the Arabs. Ancient Bactra was a center of Zoroastrianism and a key stop on the Silk Road.", "color": _AMBER},
    {"name": "Argos", "lat": 37.6319, "lon": 22.7294, "country": "Greece", "est": "c. 5000 BC", "desc": "Claims to be the oldest continuously inhabited city in Europe. Home to many mythological tales including the story of Perseus.", "color": _EMERALD},
    {"name": "Faiyum", "lat": 29.3084, "lon": 30.8428, "country": "Egypt", "est": "c. 4000 BC", "desc": "Oasis city in Egypt with evidence of habitation since the Neolithic. The Faiyum portraits are among the earliest known realistic painted portraits.", "color": _GOLD},
    {"name": "Beirut", "lat": 33.8938, "lon": 35.5018, "country": "Lebanon", "est": "c. 3000 BC", "desc": "Ancient Berytus was famous for its Roman law school. Excavations in the city center have revealed layers of Phoenician, Hellenistic, Roman, and Ottoman remains.", "color": _TEAL},
    {"name": "Erbil", "lat": 36.1901, "lon": 44.0119, "country": "Iraq", "est": "c. 5000 BC", "desc": "The Citadel of Erbil (Hawler) has been continuously inhabited for over 6,000 years, making it one of the oldest continuously occupied settlements in the world.", "color": _AMBER},
    {"name": "Gaziantep", "lat": 37.0662, "lon": 37.3833, "country": "Turkey", "est": "c. 3650 BC", "desc": "Ancient Antep, located near several important archaeological sites. The Zeugma Mosaic Museum houses extraordinary Roman-era mosaics.", "color": _ORANGE},
    {"name": "Cholula", "lat": 19.0633, "lon": -98.3031, "country": "Mexico", "est": "c. 500 BC", "desc": "Continuously inhabited since at least 500 BC. The Great Pyramid of Cholula is the largest pyramid by volume in the world, with a church built on top.", "color": _RED},
    {"name": "Luoyang", "lat": 34.6197, "lon": 112.4540, "country": "China", "est": "c. 2070 BC", "desc": "One of the Four Great Ancient Capitals of China. Served as capital for 13 dynasties and was the eastern terminus of the Silk Road.", "color": _ORANGE},
    {"name": "Cadiz", "lat": 36.5271, "lon": -6.2886, "country": "Spain", "est": "c. 1104 BC", "desc": "Founded as Gadir by the Phoenicians, it is considered the oldest continuously inhabited city in Western Europe. A major port for over 3,000 years.", "color": _TEAL},
    {"name": "Zurich", "lat": 47.3769, "lon": 8.5417, "country": "Switzerland", "est": "c. 3000 BC", "desc": "Lacustrine settlements on Lake Zurich date back 5,000 years. The Romans established Turicum here, and it has been continuously settled since.", "color": _EMERALD},
    {"name": "Rayy (Tehran)", "lat": 35.5847, "lon": 51.4486, "country": "Iran", "est": "c. 6000 BC", "desc": "Ancient Rhages, one of the great cities of medieval Islam. Mentioned in the Avesta and the Book of Tobit. Now part of greater Tehran.", "color": _AMBER},
    {"name": "Kirkuk", "lat": 35.4681, "lon": 44.3922, "country": "Iraq", "est": "c. 3000 BC", "desc": "Ancient Arrapha, strategically located on the route between Mesopotamia and the Iranian plateau. The Kirkuk Citadel is one of the oldest inhabited sites.", "color": _AMBER},
    {"name": "Lisbon", "lat": 38.7223, "lon": -9.1393, "country": "Portugal", "est": "c. 1200 BC", "desc": "Phoenician traders established Olisipo, making Lisbon one of the oldest cities in Western Europe. Predates London, Paris, and Rome by centuries.", "color": _TEAL},
    {"name": "Matera", "lat": 40.6664, "lon": 16.6044, "country": "Italy", "est": "c. 7000 BC", "desc": "The Sassi cave dwellings of Matera have been continuously inhabited for about 9,000 years, making it one of the oldest continuously inhabited places on Earth.", "color": _EMERALD},
]

ANCIENT_LIBRARIES = [
    {"name": "Library of Alexandria", "lat": 31.2001, "lon": 29.9187, "country": "Egypt", "era": "c. 295 BC - 48 BC", "desc": "The most famous library of antiquity, founded by Ptolemy I. Said to have held up to 400,000 scrolls. Its destruction is one of history's greatest cultural losses.", "color": _GOLD},
    {"name": "Library of Pergamum", "lat": 39.1319, "lon": 27.1842, "country": "Turkey", "era": "c. 197 BC", "desc": "Second greatest library of the ancient world with 200,000 volumes. Rival to Alexandria. The word 'parchment' derives from Pergamum.", "color": _VIOLET},
    {"name": "Library of Ashurbanipal", "lat": 36.3594, "lon": 43.1528, "country": "Iraq", "era": "c. 668-627 BC", "desc": "Royal library of the Assyrian king at Nineveh. Over 30,000 clay tablets including the Epic of Gilgamesh, the oldest known literary work.", "color": _AMBER},
    {"name": "Archives of Ebla", "lat": 35.7982, "lon": 36.7983, "country": "Syria", "era": "c. 2500-2250 BC", "desc": "Nearly 20,000 cuneiform tablets discovered in 1975. One of the oldest archives ever found, revealing an unknown Semitic language and Bronze Age diplomacy.", "color": _AMBER},
    {"name": "Villa of the Papyri", "lat": 40.8061, "lon": 14.3478, "country": "Italy", "era": "c. 1st century BC", "desc": "Library in Herculaneum buried by Vesuvius in 79 AD. Over 1,800 carbonized papyrus scrolls found, mostly Epicurean philosophy. Modern tech is unrolling them.", "color": _RED},
    {"name": "Hattusa Archives", "lat": 40.0197, "lon": 34.6153, "country": "Turkey", "era": "c. 1650-1200 BC", "desc": "Capital of the Hittite Empire with thousands of clay tablets. Revealed the Hittite language and the earliest known peace treaty (with Egypt).", "color": _AMBER},
    {"name": "Library of Celsus", "lat": 37.9395, "lon": 27.3417, "country": "Turkey", "era": "c. 114-117 AD", "desc": "Roman library at Ephesus that held 12,000 scrolls. Its magnificent facade still stands as one of the best-preserved Roman structures in the world.", "color": _TEAL},
    {"name": "House of Wisdom (Bayt al-Hikma)", "lat": 33.3152, "lon": 44.3661, "country": "Iraq", "era": "c. 830 AD", "desc": "Abbasid-era library and translation center in Baghdad. Scholars translated Greek, Persian, and Indian works, preserving classical knowledge for Europe.", "color": _EMERALD},
    {"name": "Imperial Library of Constantinople", "lat": 41.0082, "lon": 28.9784, "country": "Turkey", "era": "c. 330-1453 AD", "desc": "Founded by Constantius II, it preserved countless Greek and Roman texts through the Middle Ages. Its destruction in 1204 and 1453 was catastrophic.", "color": _VIOLET},
    {"name": "Nalanda University Library", "lat": 25.1367, "lon": 85.4430, "country": "India", "era": "c. 427-1197 AD", "desc": "Dharmaganja -- the 'Treasury of Truth' -- had three multi-story buildings. Said to have burned for months when Turkic invaders destroyed it in 1193.", "color": _ORANGE},
    {"name": "Timbuktu Libraries", "lat": 16.7666, "lon": -3.0026, "country": "Mali", "era": "c. 1300-1600 AD", "desc": "Sankore University and private libraries held hundreds of thousands of manuscripts on astronomy, medicine, law, and theology. Many survive to this day.", "color": _EMERALD},
    {"name": "Library of Aristotle", "lat": 40.5169, "lon": 23.6767, "country": "Greece", "era": "c. 335 BC", "desc": "Aristotle assembled one of the first great private libraries at the Lyceum in Athens. His collection influenced the organization of Alexandria.", "color": _VIOLET},
    {"name": "Ugarit Archives", "lat": 35.6025, "lon": 35.7839, "country": "Syria", "era": "c. 1400-1185 BC", "desc": "Bronze Age coastal city where the earliest known alphabet was discovered. Thousands of tablets in multiple languages revealed ancient Near Eastern culture.", "color": _AMBER},
    {"name": "Mari Archives", "lat": 34.5564, "lon": 40.8903, "country": "Syria", "era": "c. 1800 BC", "desc": "Over 25,000 tablets found at the royal palace of Mari on the Euphrates. Extraordinary insight into Bronze Age diplomacy, trade, and daily life.", "color": _AMBER},
    {"name": "Dunhuang Cave Library", "lat": 40.1420, "lon": 94.6619, "country": "China", "era": "c. 400-1000 AD", "desc": "Cave 17 of the Mogao Grottoes contained 50,000 manuscripts sealed for 900 years, including the oldest printed book (Diamond Sutra, 868 AD).", "color": _ORANGE},
    {"name": "Theological Library of Caesarea", "lat": 32.4998, "lon": 34.8903, "country": "Israel", "era": "c. 3rd-7th century AD", "desc": "Founded by Origen and expanded by Eusebius. One of the most important Christian libraries of antiquity with over 30,000 manuscripts.", "color": _TEAL},
    {"name": "Library of Trajan", "lat": 41.8956, "lon": 12.4843, "country": "Italy", "era": "c. 112 AD", "desc": "Part of Trajan's Forum in Rome, this twin library (one Greek, one Latin) was one of the great public libraries of imperial Rome.", "color": _RED},
    {"name": "Sippar Library", "lat": 33.0583, "lon": 44.2500, "country": "Iraq", "era": "c. 6th century BC", "desc": "Neo-Babylonian temple library discovered in the 19th century with thousands of tablets, including important mathematical and astronomical texts.", "color": _AMBER},
    {"name": "Biblioteca Ulpia", "lat": 41.8956, "lon": 12.4853, "country": "Italy", "era": "c. 114 AD", "desc": "Adjacent to Trajan's Column in Rome. Held imperial records and literary works in both Greek and Latin wings. One of 28 public libraries in ancient Rome.", "color": _RED},
    {"name": "Hadrian's Library", "lat": 37.9755, "lon": 23.7260, "country": "Greece", "era": "c. 132 AD", "desc": "Built by Emperor Hadrian in Athens, this grand library had 100 columns and held thousands of scrolls. The ruins remain in the heart of Athens.", "color": _VIOLET},
]

ANCIENT_PORTS = [
    {"name": "Tyre", "lat": 33.2704, "lon": 35.1964, "country": "Lebanon", "era": "c. 2750 BC", "desc": "Greatest Phoenician port city. Founded Carthage. Known for Tyrian purple dye. Alexander the Great built a causeway to conquer its island fortress.", "color": _AMBER},
    {"name": "Carthage", "lat": 36.8528, "lon": 10.3233, "country": "Tunisia", "era": "c. 814 BC", "desc": "Founded by Phoenician settlers from Tyre. Its Cothon harbor was an engineering marvel. Rival of Rome until destroyed in 146 BC.", "color": _RED},
    {"name": "Piraeus", "lat": 37.9475, "lon": 23.6417, "country": "Greece", "era": "c. 5th century BC", "desc": "Port of Athens and base of the Athenian navy. Themistocles built the Long Walls connecting it to Athens. Hub of Mediterranean trade.", "color": _VIOLET},
    {"name": "Ostia Antica", "lat": 41.7556, "lon": 12.2917, "country": "Italy", "era": "c. 620 BC", "desc": "Main port of ancient Rome at the mouth of the Tiber. At its peak, 100,000 people lived here. Remarkably preserved ruins rival Pompeii.", "color": _RED},
    {"name": "Alexandria", "lat": 31.2001, "lon": 29.9187, "country": "Egypt", "era": "332 BC", "desc": "Founded by Alexander the Great. Greatest port of the ancient world with the Pharos Lighthouse. Connected Mediterranean trade to Egypt and the East.", "color": _GOLD},
    {"name": "Byblos", "lat": 34.1236, "lon": 35.6511, "country": "Lebanon", "era": "c. 3000 BC", "desc": "One of the oldest Phoenician ports. Major exporter of cedar wood and papyrus. The ancient harbor is still visible today.", "color": _AMBER},
    {"name": "Sidon", "lat": 33.5600, "lon": 35.3729, "country": "Lebanon", "era": "c. 4000 BC", "desc": "Great Phoenician port famous for purple dye and glassmaking. Homer praised it as the wealthiest city in the world.", "color": _AMBER},
    {"name": "Caesarea Maritima", "lat": 32.4998, "lon": 34.8903, "country": "Israel", "era": "25-13 BC", "desc": "Herod the Great built this magnificent port with an artificial harbor rivaling Alexandria. Used innovative Roman concrete that set underwater.", "color": _TEAL},
    {"name": "Portus", "lat": 41.7800, "lon": 12.2600, "country": "Italy", "era": "42-64 AD", "desc": "Built by Claudius and Trajan to replace Ostia as Rome's main port. Trajan's hexagonal basin was an engineering marvel visible from space.", "color": _RED},
    {"name": "Corinth (Lechaion)", "lat": 37.9204, "lon": 22.8951, "country": "Greece", "era": "c. 700 BC", "desc": "Corinth controlled two harbors: Lechaion on the Gulf of Corinth and Cenchreae on the Saronic Gulf. The Diolkos portage road connected them.", "color": _VIOLET},
    {"name": "Ephesus", "lat": 37.9395, "lon": 27.3417, "country": "Turkey", "era": "c. 1000 BC", "desc": "Major Greek and Roman port on the Aegean. Silting eventually moved it inland. Home to the Temple of Artemis, one of the Seven Wonders.", "color": _VIOLET},
    {"name": "Berenice", "lat": 23.9100, "lon": 35.4783, "country": "Egypt", "era": "275 BC", "desc": "Ptolemaic Red Sea port that connected Egypt to India via monsoon-driven trade routes. Gateway for spices, incense, and exotic animals.", "color": _GOLD},
    {"name": "Lothal", "lat": 22.5217, "lon": 72.2519, "country": "India", "era": "c. 2400 BC", "desc": "Indus Valley Civilization port with the world's oldest known dock. Traded with Mesopotamia and the Persian Gulf over 4,000 years ago.", "color": _ORANGE},
    {"name": "Delos", "lat": 37.3967, "lon": 25.2683, "country": "Greece", "era": "c. 3rd century BC", "desc": "Sacred island and major commercial port. After 167 BC it became the largest slave market in the Mediterranean, handling 10,000 slaves per day.", "color": _VIOLET},
    {"name": "Leptis Magna", "lat": 32.6381, "lon": 14.2886, "country": "Libya", "era": "c. 1000 BC", "desc": "Phoenician trading post that became one of the Roman Empire's grandest cities under Septimius Severus. Stunning harbor ruins survive.", "color": _AMBER},
    {"name": "Gades (Cadiz)", "lat": 36.5271, "lon": -6.2886, "country": "Spain", "era": "c. 1104 BC", "desc": "Founded by Phoenicians as the westernmost major port in the ancient world. Gateway to Atlantic trade routes and the tin of Britain.", "color": _TEAL},
    {"name": "Massalia (Marseille)", "lat": 43.2965, "lon": 5.3698, "country": "France", "era": "c. 600 BC", "desc": "Founded by Greek colonists from Phocaea. Oldest city in France. Key trading hub connecting the Mediterranean to Gaul and the Celtic world.", "color": _EMERALD},
    {"name": "Syracuse", "lat": 37.0755, "lon": 15.2866, "country": "Italy", "era": "c. 734 BC", "desc": "Greatest Greek city in Sicily. Under Dionysius I it was the most powerful city in the Western Mediterranean. Archimedes defended its harbor.", "color": _VIOLET},
    {"name": "Puteoli (Pozzuoli)", "lat": 40.8222, "lon": 14.1194, "country": "Italy", "era": "c. 194 BC", "desc": "Major Roman port before Ostia. Grain from Egypt and goods from the East arrived here. St. Paul landed at Puteoli on his journey to Rome.", "color": _RED},
    {"name": "Myos Hormos", "lat": 27.1847, "lon": 33.8089, "country": "Egypt", "era": "c. 3rd century BC", "desc": "Red Sea port vital for Roman trade with India. Ships sailed with the monsoon carrying Roman gold, returning with spices, silk, and gems.", "color": _GOLD},
    {"name": "Guangzhou (Canton)", "lat": 23.1291, "lon": 113.2644, "country": "China", "era": "c. 214 BC", "desc": "Ancient Panyu, one of the earliest Chinese ports open to foreign trade. Starting point of the Maritime Silk Road connecting China to Rome.", "color": _ORANGE},
    {"name": "Motya", "lat": 37.8672, "lon": 12.4650, "country": "Italy (Sicily)", "era": "c. 8th century BC", "desc": "Phoenician island port off western Sicily. A unique Cothon (artificial harbor) served its merchant fleet until Dionysius I destroyed it in 397 BC.", "color": _AMBER},
    {"name": "Utica", "lat": 37.0556, "lon": 10.0614, "country": "Tunisia", "era": "c. 1101 BC", "desc": "Even older than Carthage, Utica was one of the first Phoenician colonies in North Africa. Key port in the Punic Wars.", "color": _AMBER},
    {"name": "Adulis", "lat": 15.2800, "lon": 39.6700, "country": "Eritrea", "era": "c. 5th century BC", "desc": "Major port of the Aksumite Empire on the Red Sea. Connected the Ethiopian highlands to Indian Ocean trade. Mentioned in the Periplus.", "color": _EMERALD},
    {"name": "Knossos (Heraklion port)", "lat": 35.2978, "lon": 25.1600, "country": "Greece (Crete)", "era": "c. 2000 BC", "desc": "Port of the Minoan civilization, the first great maritime power. Minoan ships traded across the eastern Mediterranean from this base.", "color": _VIOLET},
]

SEVEN_WONDERS = [
    {"name": "Great Pyramid of Giza", "lat": 29.9792, "lon": 31.1342, "country": "Egypt", "built": "c. 2560 BC", "status": "Still standing", "desc": "The only surviving Wonder. Built for Pharaoh Khufu, it was the tallest structure on Earth for 3,800 years. Contains over 2 million stone blocks.", "color": _GOLD},
    {"name": "Hanging Gardens of Babylon", "lat": 32.5355, "lon": 44.4275, "country": "Iraq", "built": "c. 600 BC", "status": "Destroyed / Existence debated", "desc": "Said to have been built by Nebuchadnezzar II for his wife. Elaborate terraced gardens with sophisticated irrigation. Some scholars doubt they existed in Babylon.", "color": _EMERALD},
    {"name": "Statue of Zeus at Olympia", "lat": 37.6388, "lon": 21.6300, "country": "Greece", "built": "c. 435 BC", "status": "Destroyed c. 5th century AD", "desc": "Phidias created this 13-meter chryselephantine (gold and ivory) statue. One of the greatest artistic achievements of classical Greece. Destroyed by fire.", "color": _VIOLET},
    {"name": "Temple of Artemis at Ephesus", "lat": 37.9497, "lon": 27.3639, "country": "Turkey", "built": "c. 550 BC", "status": "Destroyed 262 AD", "desc": "Greek temple of extraordinary size, twice the dimensions of the Parthenon. Rebuilt three times. Antipater of Sidon declared it the greatest Wonder.", "color": _TEAL},
    {"name": "Mausoleum at Halicarnassus", "lat": 37.0379, "lon": 27.4241, "country": "Turkey", "built": "c. 351 BC", "status": "Destroyed by earthquakes 12th-15th century", "desc": "Tomb built for Mausolus, satrap of Caria. So magnificent that his name became the word 'mausoleum.' Stood for over 1,600 years.", "color": _AMBER},
    {"name": "Colossus of Rhodes", "lat": 36.4510, "lon": 28.2278, "country": "Greece", "built": "c. 280 BC", "status": "Destroyed by earthquake 226 BC", "desc": "Bronze statue of the sun god Helios, about 33 meters tall. Stood for only 54 years before an earthquake toppled it. Its ruins were impressive for centuries.", "color": _RED},
    {"name": "Lighthouse of Alexandria (Pharos)", "lat": 31.2139, "lon": 29.8856, "country": "Egypt", "built": "c. 280 BC", "status": "Destroyed by earthquakes 1303-1480 AD", "desc": "One of the tallest structures in the world for centuries at 100-130 meters. Its light could be seen 50 km away. The Citadel of Qaitbay now stands on its base.", "color": _BLUE},
]

ANCIENT_OBSERVATORIES = [
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "country": "England", "era": "c. 3000-2000 BC", "desc": "Neolithic monument aligned with the summer solstice sunrise and winter solstice sunset. Its purpose and construction methods remain debated after centuries of study.", "color": _AMBER},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "era": "c. 1150 AD", "desc": "The world's largest religious monument has precise astronomical alignments. At the spring equinox, the sun rises directly over the central tower.", "color": _GOLD},
    {"name": "Chichen Itza (El Castillo)", "lat": 20.6843, "lon": -88.5678, "country": "Mexico", "era": "c. 600-1200 AD", "desc": "The Kukulkan pyramid produces a serpent shadow at equinoxes. The Maya were extraordinary astronomers who predicted eclipses with remarkable accuracy.", "color": _RED},
    {"name": "Goseck Circle", "lat": 51.1989, "lon": 11.8525, "country": "Germany", "era": "c. 4900 BC", "desc": "Oldest known solar observatory in the world. Neolithic circular enclosure aligned to sunrise and sunset at winter solstice. Predates Stonehenge by 2,000 years.", "color": _EMERALD},
    {"name": "Newgrange", "lat": 53.6947, "lon": -6.4756, "country": "Ireland", "era": "c. 3200 BC", "desc": "Passage tomb older than the pyramids. A roof box allows sunlight to penetrate the chamber only at winter solstice dawn -- a feat of prehistoric engineering.", "color": _AMBER},
    {"name": "Nabta Playa", "lat": 22.5200, "lon": 30.7200, "country": "Egypt", "era": "c. 5000 BC", "desc": "Stone circle in the Sahara predating Stonehenge by 1,000 years. Aligned to summer solstice and possibly to stars including Sirius and the belt of Orion.", "color": _GOLD},
    {"name": "Uxmal (Governor's Palace)", "lat": 20.3597, "lon": -89.7714, "country": "Mexico", "era": "c. 900 AD", "desc": "Maya structure precisely aligned to the extreme southerly rising of Venus. The entire building is oriented to within 0.1 degree of this astronomical event.", "color": _RED},
    {"name": "Jantar Mantar (Jaipur)", "lat": 26.9246, "lon": 75.8244, "country": "India", "era": "1734 AD", "desc": "Collection of nineteen astronomical instruments built by Maharaja Jai Singh II. The Samrat Yantra is the world's largest stone sundial. UNESCO World Heritage.", "color": _ORANGE},
    {"name": "Carnac Stones", "lat": 47.5847, "lon": -3.0717, "country": "France", "era": "c. 4500-3300 BC", "desc": "Over 3,000 standing stones in Brittany in alignments stretching for kilometers. Possible lunar and solar alignments, though their exact purpose is debated.", "color": _AMBER},
    {"name": "Kokino", "lat": 42.2603, "lon": 21.9525, "country": "North Macedonia", "era": "c. 1800 BC", "desc": "Bronze Age megalithic observatory ranked by NASA as the fourth-oldest in the world. Stone markers track solstices and equinoxes from the mountain summit.", "color": _EMERALD},
    {"name": "Chankillo", "lat": -9.5581, "lon": -78.2281, "country": "Peru", "era": "c. 250 BC", "desc": "Thirteen towers on a hilltop ridge form the oldest known solar observatory in the Americas. The towers precisely track the sun's position throughout the year.", "color": _VIOLET},
    {"name": "Arkaim", "lat": 52.6389, "lon": 59.5672, "country": "Russia", "era": "c. 2000 BC", "desc": "Bronze Age fortified settlement in the Urals with possible astronomical alignments. Compared to Stonehenge in significance for understanding ancient astronomy.", "color": _TEAL},
    {"name": "Ales Stenar", "lat": 55.3833, "lon": 14.0536, "country": "Sweden", "era": "c. 600 AD (disputed)", "desc": "Ship-shaped stone setting in southern Sweden. Some researchers claim astronomical alignments to solstices, others see it as a burial monument.", "color": _TEAL},
    {"name": "Mnajdra Temples", "lat": 35.8269, "lon": 14.4364, "country": "Malta", "era": "c. 3600 BC", "desc": "Megalithic temple aligned to equinox sunrise. At equinoxes, sunlight illuminates the main altar. One of the oldest free-standing structures in the world.", "color": _AMBER},
    {"name": "Ahu Tongariki", "lat": -27.1258, "lon": -109.2778, "country": "Chile (Easter Island)", "era": "c. 1400 AD", "desc": "Platform of 15 moai aligned with the summer solstice sunrise. The Rapanui people tracked celestial events using the moai and ahu platforms.", "color": _VIOLET},
    {"name": "Cheomseongdae", "lat": 35.8342, "lon": 129.2194, "country": "South Korea", "era": "c. 647 AD", "desc": "Oldest surviving astronomical observatory in East Asia. Built during the Silla dynasty with 362 stones representing the days of the lunar year.", "color": _ORANGE},
    {"name": "Callanish Stones", "lat": 58.1981, "lon": -6.7447, "country": "Scotland", "era": "c. 2900 BC", "desc": "Cruciform stone setting on the Isle of Lewis with alignments to the lunar standstill cycle. Every 18.6 years the moon appears to dance along the horizon.", "color": _AMBER},
    {"name": "Ulugh Beg Observatory", "lat": 39.6719, "lon": 66.9781, "country": "Uzbekistan", "era": "1420 AD", "desc": "Built by the Timurid sultan-astronomer Ulugh Beg in Samarkand. His star catalog was the most accurate until Tycho Brahe 150 years later.", "color": _TEAL},
    {"name": "Wurdi Youang", "lat": -37.7717, "lon": 144.3258, "country": "Australia", "era": "c. 11000 BC (estimated)", "desc": "Aboriginal stone arrangement in Victoria that may be aligned to solstices and equinoxes. If confirmed, it could be the oldest astronomical observatory on Earth.", "color": _GOLD},
    {"name": "Almendres Cromlech", "lat": 38.5567, "lon": -8.0608, "country": "Portugal", "era": "c. 6000-4000 BC", "desc": "Megalithic complex of 95 standing stones predating Stonehenge. Alignments suggest sophisticated astronomical knowledge among Iberia's Neolithic peoples.", "color": _EMERALD},
]

ANCIENT_WATER_SYSTEMS = [
    {"name": "Pont du Gard", "lat": 43.9472, "lon": 4.5353, "country": "France", "era": "c. 19 BC", "desc": "Roman aqueduct bridge crossing the Gardon River in three tiers. Carried water 50 km to Nimes. One of the best-preserved Roman structures anywhere.", "color": _AMBER},
    {"name": "Aqueduct of Segovia", "lat": 40.9481, "lon": -4.1176, "country": "Spain", "era": "c. 1st century AD", "desc": "Iconic Roman aqueduct with 167 arches built without mortar. Still carried water to Segovia until the 20th century -- nearly 2,000 years of service.", "color": _AMBER},
    {"name": "Qanat of Gonabad", "lat": 34.3528, "lon": 58.6836, "country": "Iran", "era": "c. 500 BC", "desc": "One of the oldest and largest qanats in the world, still functioning after 2,700 years. Its main well is over 360 meters deep.", "color": _GOLD},
    {"name": "Cloaca Maxima", "lat": 41.8903, "lon": 12.4864, "country": "Italy", "era": "c. 600 BC", "desc": "One of the world's earliest sewage systems, built by the Etruscans to drain the Roman Forum. Parts of this 2,600-year-old sewer are still in use today.", "color": _RED},
    {"name": "Tipon Aqueducts", "lat": -13.5647, "lon": -71.7858, "country": "Peru", "era": "c. 1400 AD", "desc": "Incan water engineering masterpiece near Cusco. Sophisticated fountains, canals, and terraces demonstrate extraordinary hydraulic knowledge.", "color": _VIOLET},
    {"name": "Tambomachay", "lat": -13.4797, "lon": -71.9617, "country": "Peru", "era": "c. 1400 AD", "desc": "Incan site known as the 'Bath of the Inca.' Water channels and aqueducts create ceremonial fountains that still flow today after 600 years.", "color": _VIOLET},
    {"name": "Jerwan Aqueduct", "lat": 36.5708, "lon": 43.3131, "country": "Iraq", "era": "c. 688 BC", "desc": "Built by Sennacherib to bring water to Nineveh. The oldest known large-scale aqueduct in the world, predating Roman aqueducts by centuries.", "color": _AMBER},
    {"name": "Eupalinos Tunnel", "lat": 37.6917, "lon": 26.9333, "country": "Greece", "era": "c. 530 BC", "desc": "1,036-meter water tunnel dug through a mountain on Samos, starting from both ends and meeting in the middle. Herodotus called it one of the great Greek achievements.", "color": _EMERALD},
    {"name": "Aqua Appia", "lat": 41.8902, "lon": 12.4922, "country": "Italy", "era": "312 BC", "desc": "First Roman aqueduct, built by Appius Claudius Caecus. Ran mostly underground for 16 km to bring water to Rome. Marked the beginning of Roman hydraulic engineering.", "color": _RED},
    {"name": "Aqua Marcia", "lat": 41.8900, "lon": 12.5000, "country": "Italy", "era": "144 BC", "desc": "Longest of the eleven ancient Roman aqueducts at 91 km. Praetor Marcius Rex built it to supply Rome with the purest and coldest water.", "color": _RED},
    {"name": "Mohenjo-daro Water System", "lat": 27.3244, "lon": 68.1358, "country": "Pakistan", "era": "c. 2500 BC", "desc": "Indus Valley city with the world's first known urban sanitation system. Every house had a private well and bathroom connected to covered drains.", "color": _ORANGE},
    {"name": "Minoan Plumbing (Knossos)", "lat": 35.2978, "lon": 25.1628, "country": "Greece (Crete)", "era": "c. 1700 BC", "desc": "The Minoans built sophisticated water supply and drainage systems with tapered terracotta pipes, flush toilets, and rainwater collection systems.", "color": _VIOLET},
    {"name": "Shushtar Water System", "lat": 32.0461, "lon": 48.8564, "country": "Iran", "era": "5th century BC", "desc": "UNESCO masterpiece of creative genius. Dams, canals, tunnels, and watermills built by Roman prisoners of war. Possibly the earliest multi-purpose dam.", "color": _GOLD},
    {"name": "Hezekiah's Tunnel", "lat": 31.7719, "lon": 35.2344, "country": "Israel", "era": "c. 701 BC", "desc": "Carved through 533 meters of solid rock to bring water into Jerusalem before the Assyrian siege. Diggers worked from both ends and met in the middle.", "color": _TEAL},
    {"name": "Dujiangyan Irrigation System", "lat": 31.0050, "lon": 103.6089, "country": "China", "era": "256 BC", "desc": "Still functioning after 2,300 years. Li Bing built this system to control flooding and irrigate the Chengdu Plain. No dam needed -- pure hydraulic genius.", "color": _ORANGE},
    {"name": "Tank Cascade System (Sigiriya)", "lat": 7.9569, "lon": 80.7603, "country": "Sri Lanka", "era": "c. 5th century AD", "desc": "Ancient hydraulic systems of Sri Lanka connected thousands of tanks in cascading networks. The gardens of Sigiriya used gravity-fed fountains still working today.", "color": _EMERALD},
    {"name": "Pergamon Siphon", "lat": 39.1319, "lon": 27.1842, "country": "Turkey", "era": "c. 2nd century BC", "desc": "Hellenistic pressurized water pipeline crossing a valley under 200 meters of pressure using lead pipes. One of the most impressive ancient hydraulic feats.", "color": _TEAL},
    {"name": "Nimes Castellum Divisorium", "lat": 43.8367, "lon": 4.3600, "country": "France", "era": "c. 19 BC", "desc": "Roman water distribution terminal at the end of the Pont du Gard aqueduct. Water arrived here and was distributed to 10 outlets serving the city.", "color": _AMBER},
    {"name": "Falaj Al-Khatmeen", "lat": 22.9344, "lon": 57.5306, "country": "Oman", "era": "c. 500 AD", "desc": "Part of Oman's UNESCO-listed aflaj irrigation system. Thousands of km of channels carry water from mountain springs to farmland using only gravity.", "color": _GOLD},
    {"name": "Marib Dam", "lat": 15.3881, "lon": 45.2767, "country": "Yemen", "era": "c. 750 BC", "desc": "One of the oldest known dams in the world. Irrigated 100 sq km supporting the Sabean kingdom. Its collapse is mentioned in the Quran.", "color": _AMBER},
]

ANCIENT_MINING_SITES = [
    {"name": "Laurion Silver Mines", "lat": 37.7261, "lon": 24.0428, "country": "Greece", "era": "c. 3000 BC - 1st century BC", "mineral": "Silver, Lead", "desc": "The silver from Laurion funded the Athenian navy that defeated Persia at Salamis. Thousands of slaves worked these mines that powered Athenian democracy.", "color": _VIOLET},
    {"name": "Hallstatt Salt Mines", "lat": 47.5622, "lon": 13.6493, "country": "Austria", "era": "c. 5000 BC - present", "mineral": "Salt", "desc": "World's oldest salt mine, continuously operated for 7,000 years. Gave its name to the Hallstatt culture. Preserved prehistoric artifacts in the salt.", "color": _AMBER},
    {"name": "Timna Copper Mines", "lat": 29.7875, "lon": 34.9886, "country": "Israel", "era": "c. 5000 BC - Roman era", "mineral": "Copper", "desc": "Ancient copper mines in the Negev desert, once attributed to King Solomon. Egyptian mining operations here date back 7,000 years.", "color": _GOLD},
    {"name": "Rio Tinto Mines", "lat": 37.6958, "lon": -6.5986, "country": "Spain", "era": "c. 3000 BC - present", "mineral": "Copper, Gold, Silver", "desc": "Mined continuously for 5,000 years by Iberians, Phoenicians, Romans, and moderns. The red river gave the name Rio Tinto. Largest open pit in Europe.", "color": _RED},
    {"name": "Wieliczka Salt Mine", "lat": 49.9833, "lon": 20.0556, "country": "Poland", "era": "c. 3500 BC - 1996", "mineral": "Salt", "desc": "Continuous salt mining for 5,500 years. Underground chapels carved entirely from salt. UNESCO World Heritage Site with subterranean cathedral.", "color": _AMBER},
    {"name": "Sar-e-Sang Lapis Lazuli Mines", "lat": 36.2167, "lon": 70.8000, "country": "Afghanistan", "era": "c. 7000 BC - present", "mineral": "Lapis Lazuli", "desc": "Source of the world's finest lapis lazuli for 9,000 years. Supplied the pharaohs, Sumerian kings, and Renaissance painters. The oldest gem mine.", "color": _BLUE},
    {"name": "Great Orme Copper Mines", "lat": 53.3307, "lon": -3.8494, "country": "Wales", "era": "c. 2000-600 BC", "mineral": "Copper", "desc": "Extensive Bronze Age copper mines tunneled deep underground. Over 1,800 stone hammers and 30,000 animal bone tools have been found.", "color": _EMERALD},
    {"name": "Grimes Graves", "lat": 52.4750, "lon": 0.6750, "country": "England", "era": "c. 3000-1900 BC", "mineral": "Flint", "desc": "Neolithic flint mine with over 400 shafts dug up to 12 meters deep. Miners carved underground galleries following the best flint seams.", "color": _AMBER},
    {"name": "Las Medulas", "lat": 42.4658, "lon": -6.7681, "country": "Spain", "era": "c. 1st century AD", "mineral": "Gold", "desc": "Largest open-cast gold mine in the Roman Empire. Romans used ruina montium (mountain collapse) hydraulic mining, reshaping the landscape dramatically.", "color": _GOLD},
    {"name": "King Solomon's Mines (Khirbat en-Nahas)", "lat": 30.6531, "lon": 35.3917, "country": "Jordan", "era": "c. 1000 BC", "mineral": "Copper", "desc": "Massive copper smelting site in Edom. Radiocarbon dating places major activity in the 10th century BC, aligning with the biblical era of Solomon.", "color": _GOLD},
    {"name": "Dolaucothi Gold Mines", "lat": 52.0333, "lon": -3.9333, "country": "Wales", "era": "c. 75-300 AD", "mineral": "Gold", "desc": "Only known Roman gold mine in Britain. Sophisticated aqueduct system brought water for hydraulic mining. Possibly worked since the Bronze Age.", "color": _EMERALD},
    {"name": "Gebel el-Asr Quarries", "lat": 22.6400, "lon": 31.4800, "country": "Egypt", "era": "c. 3100-1500 BC", "mineral": "Diorite, Gneiss", "desc": "Remote quarry in the Western Desert. Egyptian expeditions traveled hundreds of km to extract hard stone for royal statues and vessels.", "color": _GOLD},
    {"name": "Mount Pangaion Mines", "lat": 40.9167, "lon": 24.0833, "country": "Greece", "era": "c. 5th century BC", "mineral": "Gold, Silver", "desc": "Philip II of Macedon captured these gold mines, funding the army that Alexander the Great used to conquer the known world.", "color": _VIOLET},
    {"name": "Zaruma Gold Mines", "lat": -3.6936, "lon": -79.6114, "country": "Ecuador", "era": "Pre-Inca - present", "mineral": "Gold", "desc": "Ancient gold mines worked by pre-Inca peoples and later the Spanish. The town of Zaruma grew from this mining tradition.", "color": _GOLD},
    {"name": "Aswan Quarries", "lat": 24.0889, "lon": 32.8997, "country": "Egypt", "era": "c. 3000 BC - Roman era", "mineral": "Granite", "desc": "Source of red granite for obelisks, temples, and sarcophagi. The Unfinished Obelisk -- 42 meters long -- still lies in the quarry, cracked during carving.", "color": _GOLD},
    {"name": "Rudna Glava", "lat": 44.2250, "lon": 21.9583, "country": "Serbia", "era": "c. 5000 BC", "mineral": "Copper", "desc": "One of the oldest copper mines in the world. Vinca culture miners extracted copper ore over 7,000 years ago at the dawn of metallurgy.", "color": _RED},
    {"name": "Erzgebirge (Ore Mountains)", "lat": 50.6500, "lon": 13.0500, "country": "Germany/Czech Republic", "era": "c. 1168 AD - present", "mineral": "Silver, Tin, Cobalt", "desc": "Medieval silver mining boom created wealth that funded the Renaissance. The word 'dollar' derives from the thaler coins minted from Erzgebirge silver.", "color": _TEAL},
    {"name": "Potosi Silver Mountain", "lat": -19.5836, "lon": -65.7531, "country": "Bolivia", "era": "1545 - present", "mineral": "Silver", "desc": "The Cerro Rico produced so much silver it funded the Spanish Empire for 200 years. Up to 8 million miners died in its tunnels.", "color": _RED},
    {"name": "Wadi Hammamat Quarries", "lat": 25.9500, "lon": 33.4500, "country": "Egypt", "era": "c. 4000 BC", "mineral": "Greywacke, Gold", "desc": "Pharaonic quarry and gold mining site with some of the oldest known geological maps. Rock inscriptions from every period of Egyptian history.", "color": _GOLD},
    {"name": "Iglesiente Mines", "lat": 39.3114, "lon": 8.5350, "country": "Italy (Sardinia)", "era": "c. 3000 BC - 20th century", "mineral": "Lead, Zinc, Silver", "desc": "One of Europe's oldest mining districts. Phoenicians, Carthaginians, and Romans all extracted metals from these Sardinian hills over 5,000 years.", "color": _AMBER},
]

PREHISTORIC_CAVE_ART = [
    {"name": "Lascaux", "lat": 45.0544, "lon": 1.1686, "country": "France", "era": "c. 17000 BC", "desc": "The 'Sistine Chapel of Prehistory.' Over 600 paintings of horses, bulls, and deer in stunning color. Discovered in 1940 by four teenagers.", "color": _AMBER},
    {"name": "Altamira", "lat": 43.3808, "lon": -4.1203, "country": "Spain", "era": "c. 36000-13000 BC", "desc": "Polychrome bison paintings so vivid they were initially dismissed as forgeries. One of the first caves to demonstrate Paleolithic artistic genius.", "color": _RED},
    {"name": "Chauvet Cave", "lat": 44.3883, "lon": 4.4106, "country": "France", "era": "c. 36000-32000 BC", "desc": "Oldest known figurative paintings: lions, rhinoceroses, mammoths. Werner Herzog documented it in 'Cave of Forgotten Dreams.' UNESCO World Heritage.", "color": _GOLD},
    {"name": "Leang Tedongnge", "lat": -4.9750, "lon": 119.6500, "country": "Indonesia (Sulawesi)", "era": "c. 45500 BC", "desc": "World's oldest known figurative artwork: a life-sized painting of a Sulawesi warty pig. Pushes back the origins of representational art.", "color": _ORANGE},
    {"name": "Leang Bulu' Sipong 4", "lat": -5.0333, "lon": 119.8333, "country": "Indonesia (Sulawesi)", "era": "c. 43900 BC", "desc": "Earliest known narrative scene in art: therianthropes (part-human, part-animal figures) hunting pigs and buffalo. Over 43,900 years old.", "color": _ORANGE},
    {"name": "Cueva de las Manos", "lat": -47.1528, "lon": -70.6656, "country": "Argentina", "era": "c. 7300 BC", "desc": "Stunning gallery of hand stencils sprayed with pigment blown through bone tubes. Over 800 hand prints from 9,000 years ago in Patagonia.", "color": _VIOLET},
    {"name": "Bhimbetka Rock Shelters", "lat": 22.9375, "lon": 77.6111, "country": "India", "era": "c. 30000 BC", "desc": "Over 700 rock shelters with paintings spanning 30,000 years of human habitation. Shows continuous evolution of art from the Paleolithic to the medieval period.", "color": _ORANGE},
    {"name": "Cosquer Cave", "lat": 43.2030, "lon": 5.4470, "country": "France", "era": "c. 27000-19000 BC", "desc": "Underwater cave near Marseille with hand stencils and animal paintings. The entrance is 37 meters below sea level due to post-Ice Age sea rise.", "color": _TEAL},
    {"name": "Font-de-Gaume", "lat": 44.9386, "lon": 1.0700, "country": "France", "era": "c. 17000 BC", "desc": "One of the last original caves with polychrome paintings still open to the public. Over 200 figures including bison, horses, and mammoths.", "color": _AMBER},
    {"name": "Niaux Cave", "lat": 42.8169, "lon": 1.5978, "country": "France", "era": "c. 14000 BC", "desc": "The Salon Noir contains masterful paintings of bison, horses, and ibex deep within the mountain. Artists walked 800 meters underground to paint.", "color": _AMBER},
    {"name": "Kakadu Rock Art (Ubirr)", "lat": -12.4094, "lon": 132.9556, "country": "Australia", "era": "c. 20000 BC", "desc": "Aboriginal rock art galleries spanning 20,000 years. X-ray style paintings show internal organs of animals. Living cultural landscape.", "color": _EMERALD},
    {"name": "Apollo 11 Cave", "lat": -27.7481, "lon": 17.1003, "country": "Namibia", "era": "c. 25000 BC", "desc": "Contains some of Africa's oldest portable art: stone slabs painted with animals. Named by the archaeologist because he received news of the Moon landing while excavating.", "color": _RED},
    {"name": "Serra da Capivara", "lat": -8.8333, "lon": -42.5500, "country": "Brazil", "era": "c. 25000 BC", "desc": "Over 1,000 sites with rock paintings showing hunting, dancing, and ceremonial scenes. Some of the oldest evidence of human presence in the Americas.", "color": _VIOLET},
    {"name": "Tassili n'Ajjer", "lat": 25.5000, "lon": 9.0000, "country": "Algeria", "era": "c. 8000 BC", "desc": "Over 15,000 rock engravings and paintings in the Sahara. Records the transformation from green savannah to desert. Swimming figures, cattle, elephants.", "color": _GOLD},
    {"name": "Magura Cave", "lat": 43.7247, "lon": 22.5828, "country": "Bulgaria", "era": "c. 6000 BC", "desc": "Paintings made with bat guano depicting hunting, fertility dances, and a possible solar calendar. One of the best-preserved cave art sites in Europe.", "color": _EMERALD},
    {"name": "Pech Merle", "lat": 44.5050, "lon": 1.6403, "country": "France", "era": "c. 25000 BC", "desc": "Famous for its 'Spotted Horses' painting. DNA analysis proved that spotted horses actually existed in the Ice Age, vindicating the prehistoric artists.", "color": _AMBER},
    {"name": "El Castillo Cave", "lat": 43.2914, "lon": -3.9667, "country": "Spain", "era": "c. 40000 BC", "desc": "Red disk paintings dated to at least 40,800 years ago -- possibly the oldest cave art in Europe. May have been created by Neanderthals.", "color": _RED},
    {"name": "Laas Geel", "lat": 9.7817, "lon": 44.4650, "country": "Somalia", "era": "c. 3000 BC", "desc": "Remarkably well-preserved rock art depicting cattle, dogs, and human figures. Some of the most vivid and colorful Neolithic paintings in Africa.", "color": _ORANGE},
    {"name": "Rouffignac Cave", "lat": 44.9953, "lon": 0.9883, "country": "France", "era": "c. 13000 BC", "desc": "Known as the 'Cave of a Hundred Mammoths.' Over 250 engravings and paintings, most depicting mammoths, accessed via an underground railway.", "color": _AMBER},
    {"name": "Gabarnmung Rock Shelter", "lat": -13.6000, "lon": 133.2000, "country": "Australia", "era": "c. 28000 BC", "desc": "Aboriginal rock art shelter with paintings spanning 28,000 years. The oldest known stone structure in the world, with pillars supporting the roof.", "color": _EMERALD},
]

ANCIENT_GAMES_VENUES = [
    {"name": "Olympia", "lat": 37.6388, "lon": 21.6300, "country": "Greece", "era": "776 BC - 393 AD", "sport": "Olympic Games", "desc": "Birthplace of the Olympic Games. Athletes competed in running, wrestling, boxing, chariot racing, and pentathlon for over 1,000 years.", "color": _GOLD},
    {"name": "Colosseum (Rome)", "lat": 41.8902, "lon": 12.4922, "country": "Italy", "era": "80 AD - 6th century", "sport": "Gladiatorial combat, venationes", "desc": "The greatest amphitheater ever built, seating 50,000-80,000 spectators. Gladiators, wild animal hunts, and even mock naval battles were staged here.", "color": _RED},
    {"name": "Circus Maximus", "lat": 41.8860, "lon": 12.4853, "country": "Italy", "era": "6th century BC - 549 AD", "sport": "Chariot racing", "desc": "The largest stadium in ancient Rome, holding 250,000 spectators. Chariot racing teams (Reds, Whites, Blues, Greens) inspired fierce fan loyalty.", "color": _RED},
    {"name": "Chichen Itza Ball Court", "lat": 20.6829, "lon": -88.5686, "country": "Mexico", "era": "c. 600-1200 AD", "sport": "Mesoamerican ballgame", "desc": "Largest and best-preserved Mesoamerican ball court. Players used hips to pass a rubber ball through stone rings. Ritual significance, possibly with sacrifice.", "color": _VIOLET},
    {"name": "Delphi Stadium", "lat": 38.4824, "lon": 22.5008, "country": "Greece", "era": "5th century BC", "sport": "Pythian Games", "desc": "Stadium for the Pythian Games, second only to the Olympics in prestige. Held every four years in honor of Apollo. 7,000 spectators.", "color": _EMERALD},
    {"name": "Isthmia", "lat": 37.9125, "lon": 22.9878, "country": "Greece", "era": "6th century BC - 4th century AD", "sport": "Isthmian Games", "desc": "Site of the Isthmian Games near Corinth. One of the four Panhellenic Games. Pine wreaths were given to victors. Earliest known starting gates found here.", "color": _EMERALD},
    {"name": "Nemea", "lat": 37.8081, "lon": 22.7139, "country": "Greece", "era": "573 BC - 271 BC", "sport": "Nemean Games", "desc": "Fourth of the great Panhellenic Games. Athletes entered the stadium through a vaulted tunnel with ancient graffiti still visible on its walls.", "color": _EMERALD},
    {"name": "Amphitheater of El Jem", "lat": 35.2961, "lon": 10.7069, "country": "Tunisia", "era": "c. 238 AD", "sport": "Gladiatorial combat", "desc": "Third-largest Roman amphitheater ever built, seating 35,000. Remarkably intact in the Tunisian steppe. UNESCO World Heritage Site.", "color": _AMBER},
    {"name": "Monte Alban Ball Court", "lat": 17.0436, "lon": -96.7675, "country": "Mexico", "era": "c. 500 BC - 800 AD", "sport": "Mesoamerican ballgame", "desc": "Zapotec ball court at the hilltop city of Monte Alban. The ballgame had deep ritual significance connecting the human and divine worlds.", "color": _VIOLET},
    {"name": "Hippodrome of Constantinople", "lat": 41.0064, "lon": 28.9750, "country": "Turkey", "era": "203 AD - 1453 AD", "sport": "Chariot racing", "desc": "Center of Byzantine public life for over 1,000 years. Held 100,000 spectators. The Nika Riots of 532 started here, nearly toppling Justinian.", "color": _GOLD},
    {"name": "Paestum Amphitheater", "lat": 40.4219, "lon": 15.0058, "country": "Italy", "era": "c. 1st century BC", "sport": "Gladiatorial combat", "desc": "Roman amphitheater at the Greek colony of Paestum. Smaller but well-preserved, giving a sense of gladiatorial combat outside Rome.", "color": _RED},
    {"name": "Amphitheater of Pompeii", "lat": 40.7509, "lon": 14.4953, "country": "Italy", "era": "c. 70 BC", "sport": "Gladiatorial combat", "desc": "Oldest known permanent stone amphitheater in the Roman world. Scene of a notorious riot between Pompeians and Nucerians in 59 AD.", "color": _RED},
    {"name": "Xochicalco Ball Court", "lat": 18.8039, "lon": -99.2956, "country": "Mexico", "era": "c. 650-900 AD", "sport": "Mesoamerican ballgame", "desc": "Ball court at the hilltop fortress-city of Xochicalco. The site blends Maya, Zapotec, and Teotihuacan influences.", "color": _VIOLET},
    {"name": "Palaestra of Olympia", "lat": 37.6400, "lon": 21.6283, "country": "Greece", "era": "3rd century BC", "sport": "Wrestling, Boxing", "desc": "Training facility for combat sports at Olympia. Athletes trained naked and oiled. The palaestra had changing rooms, baths, and practice courts.", "color": _GOLD},
    {"name": "Stadium of Aphrodisias", "lat": 37.7092, "lon": 28.7297, "country": "Turkey", "era": "c. 1st century AD", "sport": "Athletic contests", "desc": "Best-preserved ancient stadium in the Mediterranean, seating 30,000. Later used for gladiatorial combat and venationes (animal hunts).", "color": _TEAL},
    {"name": "Amphitheatre of Arles", "lat": 43.6778, "lon": 4.6311, "country": "France", "era": "c. 90 AD", "sport": "Gladiatorial combat", "desc": "Roman amphitheater seating 20,000, still used for bullfights and concerts. During the Middle Ages, it was converted into a fortified village.", "color": _AMBER},
    {"name": "Verona Arena", "lat": 45.4393, "lon": 10.9942, "country": "Italy", "era": "c. 30 AD", "sport": "Gladiatorial combat", "desc": "Third-largest Roman amphitheater, almost entirely intact. Now hosts world-famous opera performances in the same arena where gladiators fought.", "color": _RED},
    {"name": "Copan Ball Court", "lat": 14.8400, "lon": -89.1400, "country": "Honduras", "era": "c. 738 AD", "sport": "Mesoamerican ballgame", "desc": "Beautifully decorated Maya ball court with macaw-head markers. The ballgame at Copan had strong connections to Maya mythology and kingship.", "color": _VIOLET},
    {"name": "Leptis Magna Amphitheater", "lat": 32.6381, "lon": 14.2886, "country": "Libya", "era": "56 AD", "sport": "Gladiatorial combat", "desc": "Carved into a natural depression, this amphitheater is one of the best examples of Roman provincial entertainment architecture.", "color": _AMBER},
    {"name": "Epidaurus Theater", "lat": 37.5969, "lon": 23.0789, "country": "Greece", "era": "4th century BC", "sport": "Drama, Music", "desc": "Most acoustically perfect ancient theater, seating 14,000. A coin dropped at center stage can be heard from the top row. Still hosts performances.", "color": _EMERALD},
    {"name": "Uxmal Ball Court", "lat": 20.3597, "lon": -89.7714, "country": "Mexico", "era": "c. 900 AD", "sport": "Mesoamerican ballgame", "desc": "Maya ball court at Uxmal in the Puuc region of Yucatan. The ring through which the ball had to pass is carved with feathered serpents.", "color": _VIOLET},
    {"name": "Aspendos Theater", "lat": 36.9389, "lon": 31.1717, "country": "Turkey", "era": "155 AD", "sport": "Drama, Music", "desc": "Best-preserved Roman theater in the world with original stage building intact. Seating 15,000, it is still used for performances today.", "color": _TEAL},
    {"name": "Great Ball Court of Coba", "lat": 20.4950, "lon": -87.7361, "country": "Mexico", "era": "c. 600-900 AD", "sport": "Mesoamerican ballgame", "desc": "Ball court at the Maya city of Coba, connected by the longest known sacbe (white road) to other cities across the Yucatan.", "color": _VIOLET},
    {"name": "Nimes Arena", "lat": 43.8345, "lon": 4.3596, "country": "France", "era": "c. 70 AD", "sport": "Gladiatorial combat", "desc": "One of the best-preserved Roman amphitheaters, seating 24,000. The Visigoths converted it into a fortress. Now hosts concerts and bullfights.", "color": _AMBER},
    {"name": "Trier Amphitheater", "lat": 49.7478, "lon": 6.6417, "country": "Germany", "era": "c. 100 AD", "sport": "Gladiatorial combat", "desc": "Amphitheater of Augusta Treverorum, seating 20,000. Cellars beneath the arena held wild animals and gladiators before combat.", "color": _TEAL},
]

ANCIENT_ROADS = [
    {"name": "Via Appia (Rome start)", "lat": 41.8760, "lon": 12.5060, "country": "Italy", "era": "312 BC", "desc": "The 'Queen of Roads,' stretching 563 km from Rome to Brindisi. Built by Appius Claudius Caecus. Many original paving stones remain after 2,300 years.", "color": _RED},
    {"name": "Via Appia (Brindisi end)", "lat": 40.6381, "lon": 17.9411, "country": "Italy", "era": "264 BC (extended)", "desc": "Eastern terminus of the Via Appia. Brindisi was the gateway to Greece and the East. A Roman column marks the road's endpoint at the harbor.", "color": _RED},
    {"name": "Persian Royal Road (Susa)", "lat": 32.1942, "lon": 48.2480, "country": "Iran", "era": "c. 500 BC", "desc": "Western end of the Persian Royal Road. Couriers could travel the 2,700 km route to Sardis in 7 days using relay stations. Described by Herodotus.", "color": _AMBER},
    {"name": "Persian Royal Road (Sardis)", "lat": 38.4878, "lon": 28.0400, "country": "Turkey", "era": "c. 500 BC", "desc": "Western terminus of the Royal Road. Lydian capital where Croesus minted the world's first coins. Connected to Susa by the fastest road in antiquity.", "color": _AMBER},
    {"name": "Qhapaq Nan (Cusco hub)", "lat": -13.5319, "lon": -71.9675, "country": "Peru", "era": "c. 1438-1533 AD", "desc": "Center of the Incan road network spanning 30,000 km through six countries. Rope bridges, tunnels, and stairways crossed the Andes at over 5,000 meters.", "color": _VIOLET},
    {"name": "Qhapaq Nan (Quito end)", "lat": -0.1807, "lon": -78.4678, "country": "Ecuador", "era": "c. 1438-1533 AD", "desc": "Northern extent of the Incan road system. Chasqui runners could relay messages from Quito to Cusco (2,400 km) in just 5-7 days.", "color": _VIOLET},
    {"name": "Silk Road (Xi'an start)", "lat": 34.2658, "lon": 108.9541, "country": "China", "era": "c. 130 BC", "desc": "Eastern terminus of the Silk Road at the capital of the Han Dynasty. The world's greatest trade route carried silk, spices, ideas, and religions.", "color": _ORANGE},
    {"name": "Silk Road (Antioch end)", "lat": 36.2000, "lon": 36.1500, "country": "Turkey", "era": "c. 130 BC", "desc": "Major western terminus of the Silk Road. Goods from China reached the Mediterranean here. Antioch was one of the Roman Empire's greatest cities.", "color": _ORANGE},
    {"name": "Via Egnatia (Durres start)", "lat": 41.3275, "lon": 19.4515, "country": "Albania", "era": "146 BC", "desc": "Roman road connecting the Adriatic to Byzantium. Western starting point at the Adriatic coast. Vital military and trade route for 2,000 years.", "color": _RED},
    {"name": "Via Egnatia (Thessaloniki)", "lat": 40.6401, "lon": 22.9444, "country": "Greece", "era": "146 BC", "desc": "Key waypoint on the Via Egnatia. St. Paul traveled this road during his missionary journeys. The road ran through the heart of the city.", "color": _RED},
    {"name": "Amber Road (Aquileia start)", "lat": 45.7696, "lon": 13.3722, "country": "Italy", "era": "c. 1600 BC", "desc": "Trade route carrying Baltic amber to the Mediterranean. Aquileia was the Roman terminus where amber arrived from northern Europe.", "color": _GOLD},
    {"name": "Amber Road (Baltic end - Gdansk)", "lat": 54.3520, "lon": 18.6466, "country": "Poland", "era": "c. 1600 BC", "desc": "Northern end of the ancient Amber Road. Baltic amber was worth its weight in gold in the Mediterranean world. Trade predates recorded history.", "color": _GOLD},
    {"name": "King's Highway (Aqaba)", "lat": 29.5167, "lon": 35.0000, "country": "Jordan", "era": "c. 3000 BC", "desc": "One of the oldest trade routes. Ran from Egypt through Jordan to Damascus. Mentioned in the Book of Numbers. Used by Nabataeans and Romans.", "color": _AMBER},
    {"name": "King's Highway (Damascus)", "lat": 33.5138, "lon": 36.2765, "country": "Syria", "era": "c. 3000 BC", "desc": "Northern end of the King's Highway at Damascus. Caravans of incense, spices, and textiles traveled this route for over 5,000 years.", "color": _AMBER},
    {"name": "Watling Street (Dover start)", "lat": 51.1279, "lon": 1.3134, "country": "England", "era": "c. 43 AD", "desc": "Major Roman road from the Channel coast through London to Wales. Later became the boundary of the Danelaw between Anglo-Saxons and Vikings.", "color": _EMERALD},
    {"name": "Watling Street (Wroxeter end)", "lat": 52.6567, "lon": -2.6433, "country": "England", "era": "c. 43 AD", "desc": "Roman road terminus at Viroconium (Wroxeter), the fourth-largest Roman town in Britain. The road covered 440 km through the heart of Roman Britain.", "color": _EMERALD},
    {"name": "Via de la Plata (Merida start)", "lat": 38.9163, "lon": -6.3458, "country": "Spain", "era": "c. 1st century BC", "desc": "Roman silver route from Merida to the mines of Asturias. Later became a major medieval pilgrimage road to Santiago de Compostela.", "color": _RED},
    {"name": "Via de la Plata (Astorga end)", "lat": 42.4589, "lon": -6.0567, "country": "Spain", "era": "c. 1st century BC", "desc": "Northern end of the silver road. Astorga was a key Roman military and mining town where the road connected to routes to the gold mines.", "color": _RED},
    {"name": "Incense Route (Dhofar)", "lat": 17.0150, "lon": 54.0925, "country": "Oman", "era": "c. 3rd century BC", "desc": "Southern starting point of the incense trade. Frankincense from the trees of Dhofar was worth more than gold in the ancient world.", "color": _GOLD},
    {"name": "Incense Route (Gaza end)", "lat": 31.5017, "lon": 34.4668, "country": "Palestine", "era": "c. 3rd century BC", "desc": "Mediterranean terminus of the incense route. From Gaza, frankincense and myrrh were shipped to Egypt, Greece, and Rome.", "color": _GOLD},
    {"name": "Stane Street (London start)", "lat": 51.5074, "lon": -0.0917, "country": "England", "era": "c. 50 AD", "desc": "Roman road from Londinium to Noviomagus (Chichester). Remarkably straight, demonstrating Roman surveying skills across 90 km of varied terrain.", "color": _EMERALD},
    {"name": "Via Augusta (Cadiz start)", "lat": 36.5271, "lon": -6.2886, "country": "Spain", "era": "c. 8 BC", "desc": "Longest Roman road in Hispania, running 1,500 km from Cadiz to the Pyrenees. Built on the route of Hannibal's legendary march with elephants.", "color": _RED},
    {"name": "Grand Trunk Road (Kabul start)", "lat": 34.5553, "lon": 69.2075, "country": "Afghanistan", "era": "c. 3rd century BC", "desc": "One of Asia's oldest roads, running 2,500 km from Kabul to Kolkata. Chandragupta Maurya, Sher Shah Suri, and the British all maintained this route.", "color": _ORANGE},
    {"name": "Grand Trunk Road (Kolkata end)", "lat": 22.5726, "lon": 88.3639, "country": "India", "era": "c. 3rd century BC", "desc": "Eastern terminus of the Grand Trunk Road. Kipling called it 'the river of life' in Kim. Still one of South Asia's most important highways.", "color": _ORANGE},
    {"name": "Way of Horus (Pelusium start)", "lat": 31.0333, "lon": 32.5667, "country": "Egypt", "era": "c. 2000 BC", "desc": "Egyptian military road along the Sinai coast connecting Egypt to Canaan. Fortified with forts and water stations. Used by pharaohs' armies for millennia.", "color": _GOLD},
]

# ===============================================================================
# POPUP BUILDER
# ===============================================================================

def _popup(title, fields, desc, color):
    """Build an HTML popup for folium markers."""
    esc = html_module.escape
    rows = "".join(
        f"<tr><td style='padding:3px 8px;color:#8b97b0;font-size:12px;'>{esc(str(k))}</td>"
        f"<td style='padding:3px 8px;color:#e8ecf4;font-size:12px;'>{esc(str(v))}</td></tr>"
        for k, v in fields.items() if v
    )
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:320px;background:#111827;
                border:1px solid {color};border-radius:10px;padding:12px;">
        <h4 style="margin:0 0 8px;color:{color};font-size:14px;">{esc(title)}</h4>
        <table style="width:100%;border-collapse:collapse;">{rows}</table>
        <p style="margin:8px 0 0;color:#8b97b0;font-size:11px;line-height:1.4;">{esc(desc)}</p>
    </div>
    """


# ===============================================================================
# MAP BUILDER
# ===============================================================================

def _build_map(data, field_keys, center=None, zoom=3):
    """Build a folium map with markers for the given data."""
    if not data:
        return None
    if center is None:
        lats = [d["lat"] for d in data]
        lons = [d["lon"] for d in data]
        center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter",
                   width="100%", height="100%")
    for item in data:
        fields = {k: item.get(k, "") for k in field_keys}
        popup_html = _popup(item["name"], fields, item.get("desc", ""), item.get("color", _ACCENT))
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=item.get("color", _ACCENT),
            fill=True,
            fill_color=item.get("color", _ACCENT),
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=item["name"],
        ).add_to(m)
    return m


# ===============================================================================
# MAIN RENDER FUNCTION
# ===============================================================================

def render_ancient_maps_tab():
    """Render the Ancient World Explorer tab."""

    st.markdown(
        '<div class="tab-header amber">'
        '<h4>Ancient World Explorer</h4>'
        '<p>Oldest cities, ancient libraries, ports, wonders, observatories & more</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox("Select Map Mode", [
        "Oldest Cities in the World",
        "Ancient Libraries & Archives",
        "Ancient Ports & Harbors",
        "Seven Wonders of the Ancient World",
        "Ancient Observatories",
        "Ancient Water Systems",
        "Ancient Mining Sites",
        "Prehistoric Cave Art",
        "Ancient Games & Sports Venues",
        "Ancient Roads & Highways",
    ], key="ancient_maps_mode")

    # Show mode description
    desc = MODE_DESCRIPTIONS.get(mode, "")
    if desc:
        st.info(desc)

    st.markdown("---")

    # -- Oldest Cities in the World ------------------------------------------------
    if mode == "Oldest Cities in the World":
        data = OLDEST_CITIES
        st.markdown("#### Oldest Continuously Inhabited Cities")
        st.caption("Urban centers with roots stretching back thousands of years, many still thriving today.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cities Mapped", len(data))
        middle_east = sum(1 for d in data if d["lon"] > 30 and d["lon"] < 60 and d["lat"] > 25 and d["lat"] < 40)
        c2.metric("Middle East", middle_east)
        european = sum(1 for d in data if d["lon"] > -10 and d["lon"] < 30 and d["lat"] > 35)
        c3.metric("European", european)
        c4.metric("Countries", len(set(d["country"] for d in data)))
        m = _build_map(data, ["country", "est"], center=[33, 40], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Established": d["est"],
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "oldest_cities.csv", "text/csv", key="dl_oldest_cities")

    # -- Ancient Libraries & Archives ----------------------------------------------
    elif mode == "Ancient Libraries & Archives":
        data = ANCIENT_LIBRARIES
        st.markdown("#### Ancient Libraries & Archives")
        st.caption("The great repositories of ancient knowledge, from clay tablets to papyrus scrolls.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Libraries Mapped", len(data))
        clay_tablet = sum(1 for d in data if "tablet" in d.get("desc", "").lower() or "cuneiform" in d.get("desc", "").lower())
        c2.metric("Clay Tablet Archives", clay_tablet)
        roman_greek = sum(1 for d in data if d.get("color") in (_RED, _VIOLET))
        c3.metric("Roman / Greek", roman_greek)
        c4.metric("Countries", len(set(d["country"] for d in data)))
        m = _build_map(data, ["country", "era"], center=[33, 35], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Era": d["era"],
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "ancient_libraries.csv", "text/csv", key="dl_libraries")

    # -- Ancient Ports & Harbors ---------------------------------------------------
    elif mode == "Ancient Ports & Harbors":
        data = ANCIENT_PORTS
        st.markdown("#### Ancient Ports & Harbors")
        st.caption("Phoenician, Greek, Roman, and other harbors that connected the ancient world.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ports Mapped", len(data))
        phoenician = sum(1 for d in data if d.get("color") == _AMBER)
        c2.metric("Phoenician", phoenician)
        greek = sum(1 for d in data if d.get("color") == _VIOLET)
        c3.metric("Greek", greek)
        roman = sum(1 for d in data if d.get("color") == _RED)
        c4.metric("Roman", roman)
        m = _build_map(data, ["country", "era"], center=[35, 25], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Era": d["era"],
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "ancient_ports.csv", "text/csv", key="dl_ports")

    # -- Seven Wonders of the Ancient World ----------------------------------------
    elif mode == "Seven Wonders of the Ancient World":
        data = SEVEN_WONDERS
        st.markdown("#### Seven Wonders of the Ancient World")
        st.caption("The original sites of the seven greatest monuments of classical antiquity.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Wonders", len(data))
        surviving = sum(1 for d in data if "standing" in d.get("status", "").lower())
        c2.metric("Still Standing", surviving)
        destroyed = sum(1 for d in data if "destroyed" in d.get("status", "").lower() or "debated" in d.get("status", "").lower())
        c3.metric("Destroyed / Lost", destroyed)
        c4.metric("Countries", len(set(d["country"] for d in data)))
        m = _build_map(data, ["country", "built", "status"], center=[33, 30], zoom=4)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Built": d["built"],
            "Status": d["status"], "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "seven_wonders.csv", "text/csv", key="dl_wonders")

    # -- Ancient Observatories -----------------------------------------------------
    elif mode == "Ancient Observatories":
        data = ANCIENT_OBSERVATORIES
        st.markdown("#### Ancient & Prehistoric Observatories")
        st.caption("Where ancient peoples tracked the stars, solstices, and equinoxes with astonishing precision.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Observatories", len(data))
        neolithic = sum(1 for d in data if "BC" in d.get("era", "") and any(yr in d.get("era", "") for yr in ["3000", "4000", "5000", "6000", "7000", "8000", "9000", "10000", "11000"]))
        c2.metric("Neolithic Era", neolithic)
        european = sum(1 for d in data if d["lat"] > 35 and d["lon"] > -15 and d["lon"] < 40)
        c3.metric("European", european)
        c4.metric("Countries", len(set(d["country"] for d in data)))
        m = _build_map(data, ["country", "era"], center=[30, 15], zoom=2)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Era": d["era"],
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "ancient_observatories.csv", "text/csv", key="dl_observatories")

    # -- Ancient Water Systems -----------------------------------------------------
    elif mode == "Ancient Water Systems":
        data = ANCIENT_WATER_SYSTEMS
        st.markdown("#### Ancient Water Systems & Aqueducts")
        st.caption("Engineering marvels that brought water across deserts, over valleys, and through mountains.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sites Mapped", len(data))
        roman = sum(1 for d in data if d.get("color") == _RED)
        c2.metric("Roman Systems", roman)
        persian = sum(1 for d in data if d.get("color") == _GOLD)
        c3.metric("Persian / Middle Eastern", persian)
        incan = sum(1 for d in data if d.get("color") == _VIOLET)
        c4.metric("Incan / S. American", incan)
        m = _build_map(data, ["country", "era"], center=[33, 30], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Era": d["era"],
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "ancient_water_systems.csv", "text/csv", key="dl_water")

    # -- Ancient Mining Sites ------------------------------------------------------
    elif mode == "Ancient Mining Sites":
        data = ANCIENT_MINING_SITES
        st.markdown("#### Ancient Mining Sites")
        st.caption("The mines that fueled ancient economies: silver, gold, copper, salt, and precious stones.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sites Mapped", len(data))
        gold_sites = sum(1 for d in data if "gold" in d.get("mineral", "").lower())
        c2.metric("Gold Mines", gold_sites)
        silver_sites = sum(1 for d in data if "silver" in d.get("mineral", "").lower())
        c3.metric("Silver Mines", silver_sites)
        copper_sites = sum(1 for d in data if "copper" in d.get("mineral", "").lower())
        c4.metric("Copper Mines", copper_sites)
        m = _build_map(data, ["country", "era", "mineral"], center=[38, 15], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Era": d["era"],
            "Mineral": d["mineral"], "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "ancient_mines.csv", "text/csv", key="dl_mines")

    # -- Prehistoric Cave Art ------------------------------------------------------
    elif mode == "Prehistoric Cave Art":
        data = PREHISTORIC_CAVE_ART
        st.markdown("#### Prehistoric Cave Art Sites")
        st.caption("The oldest artworks of humanity: painted caves and rock shelters spanning 45,000 years of creativity.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sites Mapped", len(data))
        french = sum(1 for d in data if d["country"] == "France")
        c2.metric("French Caves", french)
        spanish = sum(1 for d in data if d["country"] == "Spain")
        c3.metric("Spanish Caves", spanish)
        oldest = sum(1 for d in data if "40000" in d.get("era", "") or "45" in d.get("era", "") or "43" in d.get("era", ""))
        c4.metric("Over 40,000 Years", oldest)
        m = _build_map(data, ["country", "era"], center=[30, 10], zoom=2)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Era": d["era"],
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "cave_art_sites.csv", "text/csv", key="dl_cave_art")

    # -- Ancient Games & Sports Venues ---------------------------------------------
    elif mode == "Ancient Games & Sports Venues":
        data = ANCIENT_GAMES_VENUES
        st.markdown("#### Ancient Games & Sports Venues")
        st.caption("Where the ancient world played and competed: stadiums, amphitheaters, ball courts, and hippodromes.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Venues Mapped", len(data))
        gladiatorial = sum(1 for d in data if "gladiator" in d.get("sport", "").lower())
        c2.metric("Gladiatorial Arenas", gladiatorial)
        ballgame = sum(1 for d in data if "ballgame" in d.get("sport", "").lower())
        c3.metric("Ball Courts", ballgame)
        greek_games = sum(1 for d in data if d.get("color") in (_GOLD, _EMERALD) and d["country"] == "Greece")
        c4.metric("Greek Athletic Sites", greek_games)
        m = _build_map(data, ["country", "era", "sport"], center=[35, 15], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Era": d["era"],
            "Sport": d["sport"], "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "ancient_games.csv", "text/csv", key="dl_games")

    # -- Ancient Roads & Highways --------------------------------------------------
    elif mode == "Ancient Roads & Highways":
        data = ANCIENT_ROADS
        st.markdown("#### Ancient Roads & Highways")
        st.caption("The great road networks of antiquity that connected empires and enabled civilizations to flourish.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations Mapped", len(data))
        roman_roads = sum(1 for d in data if d.get("color") == _RED)
        c2.metric("Roman Roads", roman_roads)
        eastern_roads = sum(1 for d in data if d.get("color") in (_AMBER, _ORANGE))
        c3.metric("Eastern / Asian", eastern_roads)
        c4.metric("Route Networks", len(set(d["name"].split("(")[0].strip() for d in data)))
        m = _build_map(data, ["country", "era"], center=[35, 30], zoom=2)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Era": d["era"],
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "ancient_roads.csv", "text/csv", key="dl_roads")
