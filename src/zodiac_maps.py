# -*- coding: utf-8 -*-
"""
Astrology & Zodiac Explorer module for TerraScout AI.
Provides 10 curated map modes covering ancient observatories, zodiac origins,
Chinese astrology, Hindu/Vedic astronomy, Mayan/Aztec sites, medieval astrolabes,
planetariums, ley lines, feng shui centers, and solstice alignment sites.
All data is hardcoded -- no external API required.
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
import streamlit.components.v1 as components

# ═══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

BG_DARK = "#0a0e1a"
BG_SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
GRID_COLOR = "#2a3550"

ACCENT_CYAN = "#06b6d4"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_EMERALD = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_PINK = "#ec4899"
ACCENT_RED = "#ef4444"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"
ACCENT_TEAL = "#14b8a6"
ACCENT_FUCHSIA = "#d946ef"

MODE_COLORS = {
    "Ancient Observatories & Star Temples": ACCENT_AMBER,
    "Zodiac Origins & Babylonian Astronomy": ACCENT_VIOLET,
    "Chinese Astrology Heritage Sites": ACCENT_RED,
    "Hindu & Vedic Astronomy Centers": ACCENT_ORANGE,
    "Mayan & Aztec Astronomical Sites": ACCENT_EMERALD,
    "Medieval Astrolabe Workshops": ACCENT_TEAL,
    "Famous Planetariums Worldwide": ACCENT_BLUE,
    "Ley Lines & Geomancy Sites": ACCENT_FUCHSIA,
    "Feng Shui Cultural Centers": ACCENT_PINK,
    "Solstice & Equinox Alignment Sites": ACCENT_CYAN,
}

# ═══════════════════════════════════════════════════════════════════════════════
# CURATED DATASETS
# ═══════════════════════════════════════════════════════════════════════════════

ANCIENT_OBSERVATORIES = [
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "country": "England", "era": "c. 3000 BCE", "type": "Stone Circle", "note": "Solstice-aligned megalithic monument, UNESCO World Heritage"},
    {"name": "Newgrange", "lat": 53.6947, "lon": -6.4754, "country": "Ireland", "era": "c. 3200 BCE", "type": "Passage Tomb", "note": "Winter solstice sunrise illuminates inner chamber"},
    {"name": "Nabta Playa", "lat": 22.5100, "lon": 30.7100, "country": "Egypt", "era": "c. 5000 BCE", "type": "Stone Circle", "note": "Oldest known astronomical alignment in the world"},
    {"name": "Chankillo", "lat": -9.5589, "lon": -78.2272, "country": "Peru", "era": "c. 250 BCE", "type": "Solar Observatory", "note": "Thirteen Towers mark sunrise positions through the year"},
    {"name": "Goseck Circle", "lat": 51.1989, "lon": 11.8628, "country": "Germany", "era": "c. 4900 BCE", "type": "Circular Enclosure", "note": "Oldest known solar observatory in Europe"},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "era": "12th century CE", "type": "Temple Complex", "note": "Spring equinox sunrise directly over central tower"},
    {"name": "Machu Picchu - Intihuatana", "lat": -13.1631, "lon": -72.5450, "country": "Peru", "era": "c. 1450 CE", "type": "Solar Hitching Post", "note": "Inca sun-tying stone, precise equinox marker"},
    {"name": "Karnak Temple - Axis", "lat": 25.7188, "lon": 32.6573, "country": "Egypt", "era": "c. 2000 BCE", "type": "Temple Axis", "note": "Main axis aligned with winter solstice sunset"},
    {"name": "Kokino Observatory", "lat": 42.2639, "lon": 21.9528, "country": "North Macedonia", "era": "c. 1800 BCE", "type": "Megalithic Observatory", "note": "Bronze Age astronomical markers on volcanic peak"},
    {"name": "Mnajdra Temples", "lat": 35.8269, "lon": 14.4364, "country": "Malta", "era": "c. 3600 BCE", "type": "Megalithic Temple", "note": "Lower temple aligned with equinox and solstice sunrises"},
    {"name": "Callanish Stones", "lat": 58.1975, "lon": -6.7456, "country": "Scotland", "era": "c. 2900 BCE", "type": "Stone Circle", "note": "Cruciform stone setting aligned with lunar standstill"},
    {"name": "Almendres Cromlech", "lat": 38.5567, "lon": -7.9700, "country": "Portugal", "era": "c. 6000 BCE", "type": "Stone Circle", "note": "Largest megalithic complex in Iberian Peninsula"},
    {"name": "Arkaim", "lat": 52.6500, "lon": 59.5667, "country": "Russia", "era": "c. 2000 BCE", "type": "Fortified Settlement", "note": "Bronze Age proto-city with astronomical alignments"},
    {"name": "Externsteine", "lat": 51.8689, "lon": 8.9164, "country": "Germany", "era": "c. 1000 BCE+", "type": "Rock Formation", "note": "Chapel window aligned with summer solstice sunrise"},
    {"name": "Abu Simbel", "lat": 22.3360, "lon": 31.6256, "country": "Egypt", "era": "c. 1264 BCE", "type": "Rock Temple", "note": "Sun illuminates inner sanctum twice yearly on precise dates"},
    {"name": "Caracol (Chichen Itza)", "lat": 20.6830, "lon": -88.5686, "country": "Mexico", "era": "c. 906 CE", "type": "Observatory Tower", "note": "Windows aligned with Venus positions and equinoxes"},
    {"name": "Cheomseongdae", "lat": 35.8347, "lon": 129.2192, "country": "South Korea", "era": "c. 632 CE", "type": "Stone Observatory", "note": "Oldest surviving astronomical observatory in East Asia"},
    {"name": "Gaocheng Observatory", "lat": 34.3878, "lon": 113.0106, "country": "China", "era": "c. 1276 CE", "type": "Gnomon Tower", "note": "Yuan Dynasty observatory, measured tropical year precisely"},
    {"name": "Jantar Mantar (Delhi)", "lat": 28.6273, "lon": 77.2166, "country": "India", "era": "1724 CE", "type": "Masonry Instruments", "note": "Maharaja Jai Singh II's monumental astronomical instruments"},
    {"name": "Tower of the Winds", "lat": 37.9741, "lon": 23.7269, "country": "Greece", "era": "c. 50 BCE", "type": "Horologion", "note": "Octagonal clocktower with sundials and water clock"},
    {"name": "Ale's Stones", "lat": 55.3833, "lon": 14.0536, "country": "Sweden", "era": "c. 600 CE", "type": "Stone Ship", "note": "59 boulders in ship shape, possible solar calendar"},
    {"name": "Zorats Karer (Carahunge)", "lat": 39.5514, "lon": 46.0286, "country": "Armenia", "era": "c. 5500 BCE", "type": "Stone Circle", "note": "Stones with holes possibly aligned to stars and sun"},
    {"name": "Ring of Brodgar", "lat": 59.0014, "lon": -3.2294, "country": "Scotland", "era": "c. 2500 BCE", "type": "Stone Circle", "note": "Neolithic henge and stone circle, 27 surviving stones"},
    {"name": "Bryn Celli Ddu", "lat": 53.2072, "lon": -4.2364, "country": "Wales", "era": "c. 3000 BCE", "type": "Passage Tomb", "note": "Summer solstice sunrise lights the passage chamber"},
    {"name": "Avebury", "lat": 51.4288, "lon": -1.8544, "country": "England", "era": "c. 2850 BCE", "type": "Henge & Stone Circle", "note": "Largest stone circle in Europe, 348m diameter"},
    {"name": "Casa Rinconada", "lat": 36.0600, "lon": -107.9700, "country": "USA", "era": "c. 1100 CE", "type": "Great Kiva", "note": "Chacoan kiva with solstice light alignment through niches"},
    {"name": "Chimney Rock", "lat": 37.1781, "lon": -107.3064, "country": "USA", "era": "c. 1076 CE", "type": "Ancestral Puebloan Site", "note": "Lunar standstill alignment between twin rock spires"},
    {"name": "Woodhenge (Cahokia)", "lat": 38.6556, "lon": -90.0625, "country": "USA", "era": "c. 1100 CE", "type": "Post Circle", "note": "Red cedar posts marking solstice and equinox sunrises"},
    {"name": "Sun Dagger (Chaco Canyon)", "lat": 36.0600, "lon": -107.9560, "country": "USA", "era": "c. 1000 CE", "type": "Petroglyph Marker", "note": "Light dagger bisects spiral at solstice on Fajada Butte"},
    {"name": "Wurdi Youang", "lat": -37.7700, "lon": 144.3400, "country": "Australia", "era": "c. 11000 BCE?", "type": "Stone Arrangement", "note": "Aboriginal stone arrangement, possible solstice alignment"},
    {"name": "Sarmizegetusa Regia", "lat": 45.6222, "lon": 23.3139, "country": "Romania", "era": "c. 1st century BCE", "type": "Dacian Sanctuary", "note": "Circular sanctuary functioning as lunisolar calendar"},
    {"name": "El Castillo (Kukulcan)", "lat": 20.6843, "lon": -88.5678, "country": "Mexico", "era": "c. 1000 CE", "type": "Step Pyramid", "note": "Equinox shadow creates serpent descending the staircase"},
    {"name": "Loughcrew Cairns", "lat": 53.7447, "lon": -7.1186, "country": "Ireland", "era": "c. 3300 BCE", "type": "Passage Cairn", "note": "Equinox sunrise illuminates decorated backstone"},
    {"name": "Puma Punku", "lat": -16.5617, "lon": -68.6797, "country": "Bolivia", "era": "c. 536 CE", "type": "Temple Platform", "note": "Precisely cut stone blocks with astronomical alignments"},
    {"name": "Modhera Sun Temple", "lat": 23.5833, "lon": 72.1333, "country": "India", "era": "1026 CE", "type": "Sun Temple", "note": "Designed so equinox sun illuminates the sanctum deity"},
    {"name": "Konark Sun Temple", "lat": 19.8876, "lon": 86.0945, "country": "India", "era": "c. 1250 CE", "type": "Sun Temple", "note": "Chariot-shaped temple dedicated to Surya, the Sun god"},
    {"name": "Great Zimbabwe", "lat": -20.2674, "lon": 30.9339, "country": "Zimbabwe", "era": "c. 11th century CE", "type": "Stone Enclosure", "note": "Conical tower possibly aligned with stars and solstice"},
    {"name": "Tiwanaku - Kalasasaya", "lat": -16.5544, "lon": -68.6731, "country": "Bolivia", "era": "c. 200 CE", "type": "Semi-subterranean Temple", "note": "Gateway of the Sun marks solstice and equinox precisely"},
]

ZODIAC_ORIGINS = [
    {"name": "Babylon (Hillah)", "lat": 32.5422, "lon": 44.4211, "country": "Iraq", "era": "c. 1800 BCE", "tradition": "Babylonian", "note": "Birthplace of the zodiac, MUL.APIN star catalogue"},
    {"name": "Nineveh (Mosul)", "lat": 36.3600, "lon": 43.1500, "country": "Iraq", "era": "c. 700 BCE", "tradition": "Assyrian", "note": "Library of Ashurbanipal, cuneiform astral omen texts"},
    {"name": "Uruk (Warka)", "lat": 31.3228, "lon": 45.6369, "country": "Iraq", "era": "c. 3500 BCE", "tradition": "Sumerian", "note": "Earliest known astronomical records on clay tablets"},
    {"name": "Sippar (Abu Habba)", "lat": 33.0611, "lon": 44.2500, "country": "Iraq", "era": "c. 1600 BCE", "tradition": "Babylonian", "note": "Sun-god temple, center of astronomical calculations"},
    {"name": "Ur (Tell el-Muqayyar)", "lat": 30.9628, "lon": 46.1031, "country": "Iraq", "era": "c. 2100 BCE", "tradition": "Sumerian", "note": "Ziggurat dedicated to moon god Nanna, lunar observations"},
    {"name": "Dendera Temple", "lat": 26.1417, "lon": 32.6694, "country": "Egypt", "era": "c. 50 BCE", "tradition": "Egyptian-Greek", "note": "Famous zodiac ceiling depicting all 12 signs, now in Louvre"},
    {"name": "Alexandria (Pharos)", "lat": 31.2001, "lon": 29.9187, "country": "Egypt", "era": "c. 150 CE", "tradition": "Hellenistic", "note": "Ptolemy wrote the Almagest and Tetrabiblos here"},
    {"name": "Athens - Academy", "lat": 37.9838, "lon": 23.7275, "country": "Greece", "era": "c. 350 BCE", "tradition": "Greek", "note": "Eudoxus developed the first Greek celestial sphere model"},
    {"name": "Rhodes", "lat": 36.4341, "lon": 28.2176, "country": "Greece", "era": "c. 150 BCE", "tradition": "Greek", "note": "Hipparchus discovered precession of equinoxes, star catalogue"},
    {"name": "Harran", "lat": 36.8633, "lon": 39.0322, "country": "Turkey", "era": "c. 800 BCE", "tradition": "Sabian", "note": "Astral worship center, preserved Babylonian astrology through Islam"},
    {"name": "Persepolis", "lat": 29.9353, "lon": 52.8914, "country": "Iran", "era": "c. 500 BCE", "tradition": "Persian", "note": "Nowruz equinox celebrations, zodiac in Persian royal culture"},
    {"name": "Antioch (Antakya)", "lat": 36.2000, "lon": 36.1500, "country": "Turkey", "era": "c. 100 BCE", "tradition": "Hellenistic", "note": "Vettius Valens and other Hellenistic astrologers worked here"},
    {"name": "Rome - Pantheon", "lat": 41.8986, "lon": 12.4769, "country": "Italy", "era": "c. 125 CE", "tradition": "Roman", "note": "Oculus designed as celestial marker, seven planetary niches"},
    {"name": "Constantinople (Istanbul)", "lat": 41.0082, "lon": 28.9784, "country": "Turkey", "era": "c. 500 CE", "tradition": "Byzantine", "note": "Preserved Greek astrological manuscripts through the Middle Ages"},
    {"name": "Baghdad - House of Wisdom", "lat": 33.3152, "lon": 44.3661, "country": "Iraq", "era": "c. 830 CE", "tradition": "Islamic", "note": "Abu Ma'shar and al-Kindi developed Islamic astrology here"},
    {"name": "Edessa (Sanliurfa)", "lat": 37.1591, "lon": 38.7969, "country": "Turkey", "era": "c. 200 CE", "tradition": "Syriac", "note": "Bardesanes integrated Babylonian astrology with Christian thought"},
    {"name": "Samos", "lat": 37.7579, "lon": 26.9750, "country": "Greece", "era": "c. 530 BCE", "tradition": "Pythagorean", "note": "Pythagoras studied celestial harmony and music of the spheres"},
    {"name": "Cnidus", "lat": 36.6880, "lon": 27.3750, "country": "Turkey", "era": "c. 370 BCE", "tradition": "Greek", "note": "Eudoxus wrote on constellations and planetary spheres"},
    {"name": "Heliopolis (Baalbek)", "lat": 34.0069, "lon": 36.2042, "country": "Lebanon", "era": "c. 100 CE", "tradition": "Phoenician-Roman", "note": "Temple of Jupiter-Baal, astral worship and zodiac mosaics"},
    {"name": "Palmyra", "lat": 34.5518, "lon": 38.2685, "country": "Syria", "era": "c. 200 CE", "tradition": "Syrian", "note": "Temple of Bel with zodiac and planetary dedications"},
    {"name": "Ctesiphon", "lat": 33.0925, "lon": 44.5764, "country": "Iraq", "era": "c. 300 CE", "tradition": "Sassanid", "note": "Sassanid court astrologers compiled Zij star tables"},
    {"name": "Thebes (Luxor)", "lat": 25.6969, "lon": 32.6422, "country": "Egypt", "era": "c. 1500 BCE", "tradition": "Egyptian", "note": "Decan star system, astronomical ceilings in royal tombs"},
    {"name": "Knossos", "lat": 35.2981, "lon": 25.1631, "country": "Greece", "era": "c. 1700 BCE", "tradition": "Minoan", "note": "Possible early Aegean star lore predating Greek zodiac"},
    {"name": "Sidon", "lat": 33.5600, "lon": 35.3722, "country": "Lebanon", "era": "c. 100 BCE", "tradition": "Phoenician", "note": "Dorotheus of Sidon wrote influential astrological poem"},
    {"name": "Memphis (Mit Rahina)", "lat": 29.8481, "lon": 31.2544, "country": "Egypt", "era": "c. 2600 BCE", "tradition": "Egyptian", "note": "Imhotep's astronomical observations at Saqqara complex"},
    {"name": "Delphi", "lat": 38.4824, "lon": 22.5010, "country": "Greece", "era": "c. 600 BCE", "tradition": "Greek", "note": "Oracle prophecies intertwined with celestial omen reading"},
    {"name": "Miletus", "lat": 37.5306, "lon": 27.2778, "country": "Turkey", "era": "c. 585 BCE", "tradition": "Ionian", "note": "Thales predicted solar eclipse, pioneered rational astronomy"},
    {"name": "Jundishapur", "lat": 32.2733, "lon": 48.5308, "country": "Iran", "era": "c. 500 CE", "tradition": "Sassanid", "note": "Academy transmitted Babylonian and Greek astrology to Islam"},
    {"name": "Pergamon", "lat": 39.1217, "lon": 27.1839, "country": "Turkey", "era": "c. 200 BCE", "tradition": "Hellenistic", "note": "Great library and zodiac reliefs in the Asclepion"},
    {"name": "Croton", "lat": 39.0808, "lon": 17.1272, "country": "Italy", "era": "c. 520 BCE", "tradition": "Pythagorean", "note": "Pythagorean school developed celestial mathematical models"},
    {"name": "Assur (Qal'at Sherqat)", "lat": 35.4575, "lon": 43.2589, "country": "Iraq", "era": "c. 2000 BCE", "tradition": "Assyrian", "note": "Early Assyrian astronomical omen tablets discovered here"},
]

CHINESE_ASTROLOGY = [
    {"name": "Beijing Ancient Observatory", "lat": 39.9025, "lon": 116.4300, "country": "China", "era": "1442 CE", "type": "Imperial Observatory", "note": "Ming/Qing dynasty instruments, 500+ years of continuous observations"},
    {"name": "Purple Mountain Observatory", "lat": 32.0667, "lon": 118.8333, "country": "China", "era": "1934 CE", "type": "Modern Observatory", "note": "Houses ancient Chinese astronomical instruments collection"},
    {"name": "Temple of Heaven", "lat": 39.8822, "lon": 116.4066, "country": "China", "era": "1420 CE", "type": "Ceremonial Complex", "note": "Cosmological design: round heaven, square earth principle"},
    {"name": "Dengfeng Observatory", "lat": 34.4536, "lon": 113.0478, "country": "China", "era": "1276 CE", "type": "Gnomon Tower", "note": "Guo Shoujing measured tropical year to 365.2425 days"},
    {"name": "Xi'an - Ancient Capital", "lat": 34.2658, "lon": 108.9541, "country": "China", "era": "c. 200 BCE", "type": "Imperial Capital", "note": "Han Dynasty court astrologers developed Chinese zodiac system"},
    {"name": "Luoyang - Eastern Capital", "lat": 34.6197, "lon": 112.4540, "country": "China", "era": "c. 25 CE", "type": "Imperial Capital", "note": "Zhang Heng invented celestial globe and seismoscope"},
    {"name": "Qufu - Confucius Temple", "lat": 35.5967, "lon": 116.9861, "country": "China", "era": "c. 500 BCE", "type": "Cultural Center", "note": "Confucian integration of heavenly mandate with zodiac cycles"},
    {"name": "Mount Wudang", "lat": 32.4000, "lon": 111.0042, "country": "China", "era": "c. 600 CE", "type": "Taoist Mountain", "note": "Taoist astrology and five-element cycle teachings"},
    {"name": "Longhu Mountain", "lat": 28.0817, "lon": 116.9667, "country": "China", "era": "c. 100 CE", "type": "Taoist Mountain", "note": "Birthplace of Zhengyi Taoism, celestial feng shui practice"},
    {"name": "Gyeongju - Cheomseongdae", "lat": 35.8347, "lon": 129.2192, "country": "South Korea", "era": "632 CE", "type": "Stone Observatory", "note": "Oldest astronomical observatory in East Asia, 362 stones"},
    {"name": "Nara - Asuka", "lat": 34.4744, "lon": 135.8100, "country": "Japan", "era": "c. 600 CE", "type": "Imperial Site", "note": "Chinese zodiac adopted into Japanese Onmyodo divination"},
    {"name": "Kyoto Imperial Palace", "lat": 35.0253, "lon": 135.7625, "country": "Japan", "era": "c. 794 CE", "type": "Imperial Residence", "note": "Onmyoryo (Bureau of Divination) practiced Chinese astrology"},
    {"name": "Hanoi - Temple of Literature", "lat": 21.0285, "lon": 105.8356, "country": "Vietnam", "era": "1070 CE", "type": "Cultural Center", "note": "Vietnamese adoption of Chinese zodiac and lunar calendar"},
    {"name": "Ulaanbaatar - Gandantegchinlen", "lat": 47.9210, "lon": 106.8956, "country": "Mongolia", "era": "1809 CE", "type": "Monastery", "note": "Mongolian Buddhist astrology blended with Chinese zodiac"},
    {"name": "Taipei - Longshan Temple", "lat": 25.0372, "lon": 121.5000, "country": "Taiwan", "era": "1738 CE", "type": "Temple", "note": "Folk zodiac worship and fortune-telling traditions"},
    {"name": "Singapore - Tiger Balm Gardens", "lat": 1.2644, "lon": 103.8208, "country": "Singapore", "era": "1937 CE", "type": "Cultural Park", "note": "Chinese zodiac statues and Ten Courts of Hell dioramas"},
    {"name": "Kaifeng - Song Capital", "lat": 34.7972, "lon": 114.3081, "country": "China", "era": "c. 960 CE", "type": "Imperial Capital", "note": "Song Dynasty refined star catalogues to 1464 stars"},
    {"name": "Nanjing - Ming Tombs", "lat": 32.0583, "lon": 118.7964, "country": "China", "era": "1381 CE", "type": "Imperial Necropolis", "note": "Tomb orientations follow zodiac and feng shui principles"},
    {"name": "Dunhuang - Mogao Caves", "lat": 40.0422, "lon": 94.8019, "country": "China", "era": "c. 700 CE", "type": "Cave Temples", "note": "Contains oldest known complete star chart (649 CE)"},
    {"name": "Suzhou - Pan Gate", "lat": 31.2900, "lon": 120.6100, "country": "China", "era": "c. 1247 CE", "type": "Cultural City", "note": "Song Dynasty star chart carved in stone, 1434 stars mapped"},
    {"name": "Lhasa - Potala Palace", "lat": 29.6525, "lon": 91.1169, "country": "Tibet/China", "era": "637 CE", "type": "Palace-Monastery", "note": "Tibetan astrology (Kartsi) blending Chinese and Indian systems"},
    {"name": "Hue - Imperial City", "lat": 16.4698, "lon": 107.5774, "country": "Vietnam", "era": "1802 CE", "type": "Imperial Capital", "note": "Nguyen Dynasty court astrologers used Chinese zodiac system"},
    {"name": "Chengdu - Jinsha Ruins", "lat": 30.6833, "lon": 104.0167, "country": "China", "era": "c. 1200 BCE", "type": "Archaeological Site", "note": "Sun-bird gold artifact linked to ancient Shu solar worship"},
    {"name": "Hong Kong - Wong Tai Sin Temple", "lat": 22.3422, "lon": 114.1936, "country": "China", "era": "1921 CE", "type": "Temple", "note": "Fortune telling with Chinese zodiac, busiest temple at Lunar New Year"},
    {"name": "Penang - Kek Lok Si", "lat": 5.3992, "lon": 100.2728, "country": "Malaysia", "era": "1891 CE", "type": "Buddhist Temple", "note": "Chinese zodiac garden and Southeast Asian astrology center"},
    {"name": "Bangkok - Wat Pho", "lat": 13.7469, "lon": 100.4928, "country": "Thailand", "era": "1788 CE", "type": "Royal Temple", "note": "Zodiac-influenced Thai massage and traditional medicine"},
    {"name": "Yangon - Shwedagon Pagoda", "lat": 16.8714, "lon": 96.1497, "country": "Myanmar", "era": "c. 600 BCE", "type": "Buddhist Pagoda", "note": "Eight planetary posts for day-of-week zodiac worship"},
    {"name": "Seoul - Changdeokgung", "lat": 37.5794, "lon": 126.9910, "country": "South Korea", "era": "1405 CE", "type": "Royal Palace", "note": "Joseon Dynasty court astrologers, astronomical clocks"},
    {"name": "Phnom Penh - Royal Palace", "lat": 11.5639, "lon": 104.9311, "country": "Cambodia", "era": "1866 CE", "type": "Royal Palace", "note": "Khmer astrology combines Chinese zodiac with Hindu nakshatras"},
    {"name": "Macau - A-Ma Temple", "lat": 22.1867, "lon": 113.5364, "country": "Macau/China", "era": "1488 CE", "type": "Temple", "note": "Maritime zodiac traditions and Chinese seafarer astrology"},
]

HINDU_VEDIC = [
    {"name": "Jantar Mantar - Jaipur", "lat": 26.9247, "lon": 75.8244, "country": "India", "era": "1734 CE", "type": "Masonry Observatory", "note": "World's largest stone sundial (Samrat Yantra), UNESCO site"},
    {"name": "Jantar Mantar - Delhi", "lat": 28.6273, "lon": 77.2166, "country": "India", "era": "1724 CE", "type": "Masonry Observatory", "note": "First of five observatories built by Maharaja Jai Singh II"},
    {"name": "Jantar Mantar - Ujjain", "lat": 23.1828, "lon": 75.7683, "country": "India", "era": "1725 CE", "type": "Masonry Observatory", "note": "Ujjain was the prime meridian of ancient Indian astronomy"},
    {"name": "Jantar Mantar - Varanasi", "lat": 25.3103, "lon": 82.9856, "country": "India", "era": "1737 CE", "type": "Masonry Observatory", "note": "On the banks of the Ganges, astronomical instrument complex"},
    {"name": "Jantar Mantar - Mathura", "lat": 27.4924, "lon": 77.6737, "country": "India", "era": "1738 CE", "type": "Masonry Observatory", "note": "Fifth Jai Singh observatory, mostly ruined"},
    {"name": "Konark Sun Temple", "lat": 19.8876, "lon": 86.0945, "country": "India", "era": "c. 1250 CE", "type": "Sun Temple", "note": "Chariot of Surya with 12 pairs of wheels as sundials"},
    {"name": "Modhera Sun Temple", "lat": 23.5833, "lon": 72.1333, "country": "India", "era": "1026 CE", "type": "Sun Temple", "note": "Equinox alignment illuminates shrine, Solanki dynasty"},
    {"name": "Nalanda University Ruins", "lat": 25.1362, "lon": 85.4428, "country": "India", "era": "c. 427 CE", "type": "University", "note": "Aryabhata studied here, pioneer of Indian mathematical astronomy"},
    {"name": "Ujjain - Mahakaleshwar", "lat": 23.1828, "lon": 75.7681, "country": "India", "era": "c. 400 CE", "type": "Temple-Observatory", "note": "Indian Greenwich: Tropic of Cancer passes through Ujjain"},
    {"name": "Varanasi - Kashi Vishwanath", "lat": 25.3109, "lon": 83.0107, "country": "India", "era": "c. 1000 CE", "type": "Sacred City", "note": "Center of Jyotish Shastra (Vedic astrology) scholarship"},
    {"name": "Thiruvananthapuram - Padmanabhaswamy", "lat": 8.4828, "lon": 76.9439, "country": "India", "era": "c. 1500 CE", "type": "Temple", "note": "Kerala school of astronomy, Madhava's infinite series"},
    {"name": "Kodungallur", "lat": 10.2258, "lon": 76.1953, "country": "India", "era": "c. 1400 CE", "type": "Cultural Center", "note": "Parameshvara of Kerala developed precise planetary models"},
    {"name": "Kathmandu - Pashupatinath", "lat": 27.7106, "lon": 85.3487, "country": "Nepal", "era": "c. 400 CE", "type": "Temple Complex", "note": "Nepal's Jyotish tradition blending Hindu and Buddhist elements"},
    {"name": "Bodh Gaya", "lat": 24.6961, "lon": 84.9869, "country": "India", "era": "c. 500 BCE", "type": "Sacred Site", "note": "Buddhist astronomical calculations for auspicious dates"},
    {"name": "Anuradhapura", "lat": 8.3114, "lon": 80.4037, "country": "Sri Lanka", "era": "c. 300 BCE", "type": "Ancient Capital", "note": "Sri Lankan Sinhala astrology rooted in Vedic jyotish tradition"},
    {"name": "Kandy - Temple of the Tooth", "lat": 7.2936, "lon": 80.6413, "country": "Sri Lanka", "era": "c. 1600 CE", "type": "Buddhist Temple", "note": "Sinhalese astrological calendar determines all rituals"},
    {"name": "Taxila", "lat": 33.7460, "lon": 72.7997, "country": "Pakistan", "era": "c. 500 BCE", "type": "University City", "note": "Ancient Gandhara astronomy mixing Indian and Greek traditions"},
    {"name": "Madurai - Meenakshi Temple", "lat": 9.9195, "lon": 78.1193, "country": "India", "era": "c. 1600 CE", "type": "Temple", "note": "Navagraha shrine venerating nine celestial bodies"},
    {"name": "Tirumala - Tirupati", "lat": 13.6833, "lon": 79.3472, "country": "India", "era": "c. 300 CE", "type": "Temple", "note": "Panchangam (Vedic almanac) determines all festival dates"},
    {"name": "Hampi - Vijayanagara", "lat": 15.3350, "lon": 76.4600, "country": "India", "era": "c. 1336 CE", "type": "Imperial Capital", "note": "Royal court astrologers and astronomical orientation of temples"},
    {"name": "Puri - Jagannath Temple", "lat": 19.8048, "lon": 85.8183, "country": "India", "era": "c. 1100 CE", "type": "Temple", "note": "Rath Yatra date determined by precise Vedic astrological calculations"},
    {"name": "Khajuraho", "lat": 24.8318, "lon": 79.9199, "country": "India", "era": "c. 1000 CE", "type": "Temple Complex", "note": "Navagraha panels and zodiac carvings on Chandela temples"},
    {"name": "Ellora Caves", "lat": 20.0258, "lon": 75.1780, "country": "India", "era": "c. 600 CE", "type": "Rock-Cut Temples", "note": "Astronomical alignments in Kailasa temple construction"},
    {"name": "Mahabalipuram", "lat": 12.6169, "lon": 80.1927, "country": "India", "era": "c. 700 CE", "type": "Shore Temple", "note": "Pallava dynasty temple aligned with astronomical events"},
    {"name": "Thanjavur - Brihadeeswarar", "lat": 10.7828, "lon": 79.1318, "country": "India", "era": "1010 CE", "type": "Temple", "note": "Chola temple shadow astronomy, navagraha shrine"},
    {"name": "Rishikesh", "lat": 30.0869, "lon": 78.2676, "country": "India", "era": "Ancient", "type": "Spiritual Center", "note": "Traditional Vedic astrology (Jyotish) teaching center"},
    {"name": "Bhubaneswar - Lingaraja", "lat": 20.2381, "lon": 85.8315, "country": "India", "era": "c. 1100 CE", "type": "Temple", "note": "Kalinga school of astronomy, equinox-aligned temple axis"},
    {"name": "Srirangam", "lat": 10.8560, "lon": 78.6878, "country": "India", "era": "c. 800 CE", "type": "Temple Island", "note": "Largest functioning Hindu temple, navagraha shrine"},
    {"name": "Dwarka", "lat": 22.2376, "lon": 68.9674, "country": "India", "era": "c. 1500 BCE", "type": "Sacred City", "note": "Mythological Krishna's city, jyotish pilgrimage center"},
    {"name": "Rameswaram", "lat": 9.2876, "lon": 79.3129, "country": "India", "era": "c. 1200 CE", "type": "Temple", "note": "Navagraha worship and astrological remedy rituals"},
    {"name": "Sigiriya", "lat": 7.9569, "lon": 80.7603, "country": "Sri Lanka", "era": "c. 477 CE", "type": "Rock Fortress", "note": "Mirror wall and garden layout reflecting cosmic principles"},
]

MAYAN_AZTEC = [
    {"name": "Chichen Itza - El Castillo", "lat": 20.6843, "lon": -88.5678, "country": "Mexico", "era": "c. 1000 CE", "type": "Step Pyramid", "note": "Equinox serpent shadow, 365 steps = days of the year"},
    {"name": "Chichen Itza - Caracol", "lat": 20.6830, "lon": -88.5686, "country": "Mexico", "era": "c. 906 CE", "type": "Observatory", "note": "Circular tower with Venus-aligned windows"},
    {"name": "Uxmal - Governor's Palace", "lat": 20.3594, "lon": -89.7714, "country": "Mexico", "era": "c. 900 CE", "type": "Palace", "note": "Aligned with Venus rise at its southernmost point"},
    {"name": "Palenque - Temple of Inscriptions", "lat": 17.4847, "lon": -92.0464, "country": "Mexico", "era": "c. 683 CE", "type": "Funerary Temple", "note": "K'inich Janaab Pakal's tomb with astronomical inscriptions"},
    {"name": "Copan - Stela Platform", "lat": 14.8400, "lon": -89.1400, "country": "Honduras", "era": "c. 700 CE", "type": "Stela Complex", "note": "Venus tables and solar observations by Maya astronomers"},
    {"name": "Tikal - Temple IV", "lat": 17.2220, "lon": -89.6237, "country": "Guatemala", "era": "c. 741 CE", "type": "Pyramid-Temple", "note": "Aligned with solstice sunset viewed from Temple I"},
    {"name": "Calakmul", "lat": 18.1053, "lon": -89.8108, "country": "Mexico", "era": "c. 500 CE", "type": "Pyramid Complex", "note": "Structure II aligned with December solstice sunrise"},
    {"name": "Teotihuacan - Pyramid of the Sun", "lat": 19.6925, "lon": -98.8438, "country": "Mexico", "era": "c. 200 CE", "type": "Pyramid", "note": "Aligned to sunset on August 13 (start of Mayan calendar)"},
    {"name": "Teotihuacan - Pyramid of the Moon", "lat": 19.6983, "lon": -98.8448, "country": "Mexico", "era": "c. 250 CE", "type": "Pyramid", "note": "Avenue of the Dead aligned 15.5 degrees east of north"},
    {"name": "Monte Alban", "lat": 17.0444, "lon": -96.7678, "country": "Mexico", "era": "c. 500 BCE", "type": "Hilltop City", "note": "Building J is an arrow-shaped astronomical observatory"},
    {"name": "Xochicalco - Observatory Cave", "lat": 18.8039, "lon": -99.2958, "country": "Mexico", "era": "c. 700 CE", "type": "Cave Observatory", "note": "Zenithal sun tube: sunlight enters cave at solar zenith"},
    {"name": "Tulum", "lat": 20.2145, "lon": -87.4291, "country": "Mexico", "era": "c. 1200 CE", "type": "Coastal City", "note": "Building with small window aligned with Venus rise"},
    {"name": "Dzibilchaltun - Temple of the Seven Dolls", "lat": 21.0919, "lon": -89.5944, "country": "Mexico", "era": "c. 500 CE", "type": "Temple", "note": "Equinox sun shines directly through temple doorways"},
    {"name": "Tonina", "lat": 16.9022, "lon": -92.0097, "country": "Mexico", "era": "c. 700 CE", "type": "Acropolis", "note": "Astronomical inscriptions and calendar round records"},
    {"name": "Quirigua", "lat": 15.2700, "lon": -89.0400, "country": "Guatemala", "era": "c. 800 CE", "type": "Stela Site", "note": "Stela C records the Long Count creation date 4 Ahau 8 Kumku"},
    {"name": "Mayapan", "lat": 20.6308, "lon": -89.4619, "country": "Mexico", "era": "c. 1200 CE", "type": "Walled City", "note": "Observatory with Venus alignment openings"},
    {"name": "Edzna", "lat": 19.5983, "lon": -90.2311, "country": "Mexico", "era": "c. 400 BCE", "type": "City Complex", "note": "Five-story pyramid with rooftop astronomical observation platform"},
    {"name": "Bonampak", "lat": 16.7036, "lon": -91.0647, "country": "Mexico", "era": "c. 790 CE", "type": "Temple", "note": "Murals depict celestial events and astronomical rituals"},
    {"name": "Templo Mayor - Tenochtitlan", "lat": 19.4348, "lon": -99.1313, "country": "Mexico", "era": "c. 1375 CE", "type": "Aztec Temple", "note": "Dual pyramid aligned with equinox sunrise between temples"},
    {"name": "Malinalco", "lat": 18.9453, "lon": -99.4958, "country": "Mexico", "era": "c. 1500 CE", "type": "Aztec Temple", "note": "Eagle warrior temple carved from living rock, solstice alignment"},
    {"name": "Cholula - Great Pyramid", "lat": 19.0578, "lon": -98.3017, "country": "Mexico", "era": "c. 200 BCE", "type": "Pyramid", "note": "World's largest pyramid by volume, astronomical orientations"},
    {"name": "Cahal Pech", "lat": 17.1506, "lon": -89.0700, "country": "Belize", "era": "c. 1000 BCE", "type": "Maya Site", "note": "Early Maya settlement with celestial observation platforms"},
    {"name": "Caracol (Belize)", "lat": 16.7640, "lon": -89.1170, "country": "Belize", "era": "c. 600 CE", "type": "Major Maya City", "note": "Caana pyramid aligned with astronomical events"},
    {"name": "El Mirador", "lat": 17.7547, "lon": -89.9208, "country": "Guatemala", "era": "c. 600 BCE", "type": "Preclassic City", "note": "La Danta pyramid, one of the largest in the ancient world"},
    {"name": "Kabah", "lat": 20.2500, "lon": -89.6500, "country": "Mexico", "era": "c. 800 CE", "type": "Puuc City", "note": "Codz Poop palace facade with astronomical Chaac masks"},
    {"name": "Yaxchilan", "lat": 16.9000, "lon": -90.9667, "country": "Mexico", "era": "c. 700 CE", "type": "Maya City", "note": "Lintels depict celestial events tied to royal rituals"},
    {"name": "Mitla", "lat": 16.9256, "lon": -96.3617, "country": "Mexico", "era": "c. 900 CE", "type": "Zapotec City", "note": "Palace of Columns with geometric patterns encoding calendar cycles"},
    {"name": "Coba", "lat": 20.4944, "lon": -87.7361, "country": "Mexico", "era": "c. 600 CE", "type": "Maya City", "note": "Nohoch Mul pyramid, sacbe roads radiate in star-like pattern"},
    {"name": "Izapa", "lat": 14.9528, "lon": -92.1639, "country": "Mexico", "era": "c. 300 BCE", "type": "Preclassic Site", "note": "Origin of Long Count calendar, stela astronomical iconography"},
    {"name": "Tula - Atlantes", "lat": 20.0650, "lon": -99.3417, "country": "Mexico", "era": "c. 1000 CE", "type": "Toltec Capital", "note": "Warrior columns facing astronomical alignment directions"},
    {"name": "Tajin - Pyramid of Niches", "lat": 20.4486, "lon": -97.3783, "country": "Mexico", "era": "c. 600 CE", "type": "Totonac City", "note": "365 niches representing each day of the solar year"},
]

MEDIEVAL_ASTROLABES = [
    {"name": "Toledo", "lat": 39.8628, "lon": -4.0273, "country": "Spain", "era": "c. 1060 CE", "type": "Workshop City", "note": "Al-Zarqali (Azarquiel) crafted famous astrolabes, invented saphaea"},
    {"name": "Cordoba", "lat": 37.8882, "lon": -4.7794, "country": "Spain", "era": "c. 950 CE", "type": "Caliphate Capital", "note": "Maslama al-Majriti's school of astrolabe-making and astronomy"},
    {"name": "Baghdad", "lat": 33.3152, "lon": 44.3661, "country": "Iraq", "era": "c. 830 CE", "type": "House of Wisdom", "note": "Al-Khwarizmi and al-Farghani designed astrolabes here"},
    {"name": "Isfahan", "lat": 32.6546, "lon": 51.6680, "country": "Iran", "era": "c. 1100 CE", "type": "Workshop City", "note": "Persian astrolabe tradition, Omar Khayyam's observatory"},
    {"name": "Damascus", "lat": 33.5138, "lon": 36.2765, "country": "Syria", "era": "c. 700 CE", "type": "Umayyad Capital", "note": "Early Islamic brass astrolabe production center"},
    {"name": "Cairo - Al-Azhar", "lat": 30.0444, "lon": 31.2357, "country": "Egypt", "era": "c. 1000 CE", "type": "University", "note": "Ibn Yunus compiled astronomical tables with astrolabe observations"},
    {"name": "Samarkand", "lat": 39.6550, "lon": 66.9597, "country": "Uzbekistan", "era": "1420 CE", "type": "Observatory", "note": "Ulugh Beg's observatory produced star catalogue of 1018 stars"},
    {"name": "Maragheh", "lat": 37.3900, "lon": 46.2200, "country": "Iran", "era": "1259 CE", "type": "Observatory", "note": "Nasir al-Din al-Tusi's observatory, Tusi couple model"},
    {"name": "Fez - Qarawiyyin", "lat": 34.0633, "lon": -4.9731, "country": "Morocco", "era": "c. 900 CE", "type": "University", "note": "Oldest university in the world, astrolabe studies since 9th century"},
    {"name": "Nuremberg", "lat": 49.4521, "lon": 11.0767, "country": "Germany", "era": "c. 1470 CE", "type": "Workshop City", "note": "Regiomontanus established printing press for astronomical works"},
    {"name": "Prague", "lat": 50.0870, "lon": 14.4205, "country": "Czech Republic", "era": "1410 CE", "type": "Clock City", "note": "Astronomical Clock (Orloj) - oldest working astro clock in world"},
    {"name": "Paris - Notre-Dame", "lat": 48.8530, "lon": 2.3499, "country": "France", "era": "c. 1200 CE", "type": "University City", "note": "University of Paris taught astronomy with astrolabes"},
    {"name": "Oxford", "lat": 51.7548, "lon": -1.2544, "country": "England", "era": "c. 1280 CE", "type": "University", "note": "Chaucer wrote A Treatise on the Astrolabe (1391)"},
    {"name": "Padua", "lat": 45.4064, "lon": 11.8768, "country": "Italy", "era": "c. 1344 CE", "type": "University City", "note": "Giovanni de' Dondi built the Astrarium astronomical clock"},
    {"name": "Florence", "lat": 43.7696, "lon": 11.2558, "country": "Italy", "era": "c. 1480 CE", "type": "Renaissance City", "note": "Lorenzo Della Volpaia crafted planetary clock for Lorenzo de' Medici"},
    {"name": "Strasbourg", "lat": 48.5734, "lon": 7.7521, "country": "France", "era": "1574 CE", "type": "Cathedral City", "note": "Strasbourg Cathedral astronomical clock, one of the finest"},
    {"name": "Lund", "lat": 55.7047, "lon": 13.1910, "country": "Sweden", "era": "c. 1380 CE", "type": "Cathedral City", "note": "Horologium Mirabile Lundense astronomical clock"},
    {"name": "Marrakech", "lat": 31.6295, "lon": -7.9811, "country": "Morocco", "era": "c. 1150 CE", "type": "Workshop City", "note": "Almohad-era astrolabe production and astronomical scholarship"},
    {"name": "Seville", "lat": 37.3891, "lon": -5.9845, "country": "Spain", "era": "c. 1250 CE", "type": "Translation Center", "note": "Alfonso X 'El Sabio' commissioned Alfonsine Tables here"},
    {"name": "Constantinople (Istanbul)", "lat": 41.0082, "lon": 28.9784, "country": "Turkey", "era": "c. 1450 CE", "type": "Imperial Capital", "note": "Byzantine astrolabe collection, now in Topkapi Palace"},
    {"name": "Herat", "lat": 34.3529, "lon": 62.2040, "country": "Afghanistan", "era": "c. 1400 CE", "type": "Timurid Center", "note": "Timurid-era astronomical instrument workshop"},
    {"name": "Bruges", "lat": 51.2094, "lon": 3.2247, "country": "Belgium", "era": "c. 1300 CE", "type": "Trading City", "note": "Flemish astronomers and instrument makers traded astrolabes"},
    {"name": "Augsburg", "lat": 48.3705, "lon": 10.8978, "country": "Germany", "era": "c. 1530 CE", "type": "Workshop City", "note": "Georg Hartmann mass-produced astrolabes and sundials"},
    {"name": "Louvain", "lat": 50.8798, "lon": 4.7005, "country": "Belgium", "era": "c. 1425 CE", "type": "University City", "note": "Gemma Frisius and Mercator studied astronomical instruments here"},
    {"name": "Shiraz", "lat": 29.5918, "lon": 52.5836, "country": "Iran", "era": "c. 1300 CE", "type": "Cultural Center", "note": "Qutb al-Din al-Shirazi explained rainbows and crafted astrolabes"},
    {"name": "Tabriz", "lat": 38.0800, "lon": 46.2919, "country": "Iran", "era": "c. 1280 CE", "type": "Ilkhanid Capital", "note": "Patronage of Maragheh astronomers, astrolabe workshops"},
    {"name": "Ghazni", "lat": 33.5533, "lon": 68.4208, "country": "Afghanistan", "era": "c. 1000 CE", "type": "Ghaznavid Capital", "note": "Al-Biruni measured Earth's circumference, used astrolabes"},
    {"name": "Aleppo", "lat": 36.2021, "lon": 37.1343, "country": "Syria", "era": "c. 1200 CE", "type": "Trading City", "note": "Ayyubid-era astrolabe workshops and astronomical education"},
    {"name": "Konya", "lat": 37.8714, "lon": 32.4847, "country": "Turkey", "era": "c. 1250 CE", "type": "Seljuk Capital", "note": "Rumi's poetry references celestial spheres and astrolabe imagery"},
    {"name": "Cracow", "lat": 50.0647, "lon": 19.9450, "country": "Poland", "era": "c. 1490 CE", "type": "University City", "note": "Copernicus studied astronomy and used astrolabes at Jagiellonian"},
]

PLANETARIUMS = [
    {"name": "Hayden Planetarium", "lat": 40.7812, "lon": -73.9730, "country": "USA", "city": "New York", "opened": 1935, "note": "Rose Center for Earth and Space, rebuilt 2000"},
    {"name": "Adler Planetarium", "lat": 41.8663, "lon": -87.6068, "country": "USA", "city": "Chicago", "opened": 1930, "note": "First planetarium in the Western Hemisphere"},
    {"name": "Griffith Observatory", "lat": 34.1184, "lon": -118.3004, "country": "USA", "city": "Los Angeles", "opened": 1935, "note": "Iconic hilltop observatory, free public telescopes"},
    {"name": "Planetario de Buenos Aires", "lat": -34.5696, "lon": -58.4139, "country": "Argentina", "city": "Buenos Aires", "opened": 1966, "note": "Galileo Galilei Planetarium in Palermo park"},
    {"name": "Nagoya City Science Museum", "lat": 35.1653, "lon": 136.9000, "country": "Japan", "city": "Nagoya", "opened": 2011, "note": "World's largest planetarium dome at 35 meters"},
    {"name": "Beijing Planetarium", "lat": 39.9339, "lon": 116.3417, "country": "China", "city": "Beijing", "opened": 1957, "note": "First large planetarium in Asia"},
    {"name": "Moscow Planetarium", "lat": 55.7614, "lon": 37.5839, "country": "Russia", "city": "Moscow", "opened": 1929, "note": "One of the oldest and largest planetariums in the world"},
    {"name": "Deutsches Museum Planetarium", "lat": 48.1298, "lon": 11.5831, "country": "Germany", "city": "Munich", "opened": 1925, "note": "First projection planetarium, Zeiss Mark I projector"},
    {"name": "Royal Observatory Greenwich", "lat": 51.4769, "lon": -0.0005, "country": "England", "city": "London", "opened": 1675, "note": "Home of the Prime Meridian and Greenwich Mean Time"},
    {"name": "Cite de l'Espace", "lat": 43.5875, "lon": 1.4914, "country": "France", "city": "Toulouse", "opened": 1997, "note": "Space theme park with planetarium and Ariane 5 rocket"},
    {"name": "Tycho Brahe Planetarium", "lat": 55.6636, "lon": 12.5534, "country": "Denmark", "city": "Copenhagen", "opened": 1989, "note": "Named after the famous Danish astronomer, IMAX dome"},
    {"name": "Melbourne Planetarium", "lat": -37.8030, "lon": 144.9684, "country": "Australia", "city": "Melbourne", "opened": 1965, "note": "Inside Scienceworks museum, digital dome shows"},
    {"name": "Planetarium Rio Tinto Alcan", "lat": 45.5280, "lon": -73.5322, "country": "Canada", "city": "Montreal", "opened": 2013, "note": "Two immersive domes with 360-degree projections"},
    {"name": "Hong Kong Space Museum", "lat": 22.2944, "lon": 114.1714, "country": "China", "city": "Hong Kong", "opened": 1980, "note": "Iconic egg-shaped dome on Tsim Sha Tsui waterfront"},
    {"name": "Nehru Planetarium", "lat": 28.6011, "lon": 77.1772, "country": "India", "city": "New Delhi", "opened": 1984, "note": "Part of Nehru Memorial Museum, astronomy outreach"},
    {"name": "Fiske Planetarium", "lat": 40.0036, "lon": -105.2631, "country": "USA", "city": "Boulder", "opened": 1975, "note": "University of Colorado, state-of-the-art digital dome"},
    {"name": "Shanghai Astronomy Museum", "lat": 30.8883, "lon": 121.7900, "country": "China", "city": "Shanghai", "opened": 2021, "note": "World's largest astronomy museum, no straight lines design"},
    {"name": "Planetario de Madrid", "lat": 40.3917, "lon": -3.6833, "country": "Spain", "city": "Madrid", "opened": 1986, "note": "Modern planetarium in Tierno Galvan Park"},
    {"name": "ESO Supernova Planetarium", "lat": 48.2600, "lon": 11.6708, "country": "Germany", "city": "Garching", "opened": 2018, "note": "European Southern Observatory visitor center, free admission"},
    {"name": "Birla Planetarium Kolkata", "lat": 22.5512, "lon": 88.3517, "country": "India", "city": "Kolkata", "opened": 1963, "note": "Second largest planetarium in Asia, circular design"},
    {"name": "Planetarium Bochum", "lat": 51.4744, "lon": 7.2147, "country": "Germany", "city": "Bochum", "opened": 1964, "note": "Picked up first signals from Sputnik 1 in 1957"},
    {"name": "Clark Planetarium", "lat": 40.7653, "lon": -111.9019, "country": "USA", "city": "Salt Lake City", "opened": 2003, "note": "Hansen Dome Theatre with digital projection"},
    {"name": "Armagh Planetarium", "lat": 54.3528, "lon": -6.6500, "country": "N. Ireland", "city": "Armagh", "opened": 1968, "note": "Located at historic Armagh Observatory, founded 1790"},
    {"name": "Morehead Planetarium", "lat": 35.9132, "lon": -79.0511, "country": "USA", "city": "Chapel Hill", "opened": 1949, "note": "Trained NASA astronauts in celestial navigation"},
    {"name": "Singapore Science Centre Planetarium", "lat": 1.3325, "lon": 103.7356, "country": "Singapore", "city": "Singapore", "opened": 1987, "note": "Omni-Theatre dome with astronomy and science shows"},
    {"name": "Istanbul Planetarium", "lat": 40.9917, "lon": 29.0292, "country": "Turkey", "city": "Istanbul", "opened": 2016, "note": "Inside Rahmi M. Koc Museum, digital projection"},
    {"name": "Planetarium de la Villette", "lat": 48.8953, "lon": 2.3872, "country": "France", "city": "Paris", "opened": 1986, "note": "Inside Cite des Sciences, largest science museum in Europe"},
    {"name": "McAuliffe-Shepard Discovery Center", "lat": 43.2081, "lon": -71.5376, "country": "USA", "city": "Concord", "opened": 1990, "note": "Named for Christa McAuliffe and Alan Shepard"},
    {"name": "Zeiss-Planetarium Jena", "lat": 50.9256, "lon": 11.5864, "country": "Germany", "city": "Jena", "opened": 1926, "note": "World's oldest continuously operating planetarium"},
    {"name": "Lowell Observatory", "lat": 35.2028, "lon": -111.6647, "country": "USA", "city": "Flagstaff", "opened": 1894, "note": "Where Pluto was discovered in 1930, dark sky pioneer"},
    {"name": "National Air and Space Museum", "lat": 38.8882, "lon": -77.0199, "country": "USA", "city": "Washington DC", "opened": 1976, "note": "Albert Einstein Planetarium, most visited museum"},
    {"name": "Fundacao Planetario - Rio", "lat": -22.9481, "lon": -43.2344, "country": "Brazil", "city": "Rio de Janeiro", "opened": 1970, "note": "Two domes in Gavea, largest planetarium in Latin America"},
    {"name": "Cosmonova - Stockholm", "lat": 59.3697, "lon": 18.0536, "country": "Sweden", "city": "Stockholm", "opened": 1992, "note": "IMAX dome at Swedish Museum of Natural History"},
    {"name": "Cape Town Planetarium", "lat": -33.9367, "lon": 18.4636, "country": "South Africa", "city": "Cape Town", "opened": 1987, "note": "Part of Iziko Museums, Southern Hemisphere skies"},
    {"name": "Peter Harrison Planetarium", "lat": 51.4769, "lon": -0.0005, "country": "England", "city": "London", "opened": 2007, "note": "120-seat digital planetarium at Royal Observatory Greenwich"},
]

LEY_LINES = [
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "country": "England", "type": "Stone Circle", "line": "St. Michael's Ley", "note": "Major node on Britain's most famous ley line"},
    {"name": "Avebury", "lat": 51.4288, "lon": -1.8544, "country": "England", "type": "Henge", "line": "St. Michael's Ley", "note": "Largest stone circle in Europe, ley line intersection"},
    {"name": "Glastonbury Tor", "lat": 51.1442, "lon": -2.6983, "country": "England", "type": "Sacred Hill", "line": "St. Michael's Ley", "note": "Mythic Isle of Avalon, major ley node and geomancy site"},
    {"name": "St. Michael's Mount", "lat": 50.1178, "lon": -5.4773, "country": "England", "type": "Tidal Island", "line": "St. Michael's Ley", "note": "Western terminus of St. Michael ley, mirror of Mont-Saint-Michel"},
    {"name": "Mont-Saint-Michel", "lat": 48.6361, "lon": -1.5114, "country": "France", "type": "Tidal Island", "line": "Apollo-St. Michael Axis", "note": "On the great European alignment from Ireland to Israel"},
    {"name": "Sacra di San Michele", "lat": 45.0961, "lon": 7.3444, "country": "Italy", "type": "Abbey", "line": "Apollo-St. Michael Axis", "note": "Perched on Monte Pirchiriano, Archangel Michael dedication"},
    {"name": "Monte Sant'Angelo", "lat": 41.7075, "lon": 15.9547, "country": "Italy", "type": "Sanctuary", "line": "Apollo-St. Michael Axis", "note": "Grotto of St. Michael, oldest Michael shrine in Western Europe"},
    {"name": "Delphi", "lat": 38.4824, "lon": 22.5010, "country": "Greece", "type": "Oracle Site", "line": "Apollo-St. Michael Axis", "note": "Ancient Greek omphalos (navel of the world) on Apollo axis"},
    {"name": "Symi Island - Panormitis", "lat": 36.5550, "lon": 27.8433, "country": "Greece", "type": "Monastery", "line": "Apollo-St. Michael Axis", "note": "Monastery of Archangel Michael, Apollo axis waypoint"},
    {"name": "Mount Carmel", "lat": 32.7419, "lon": 34.9826, "country": "Israel", "type": "Sacred Mountain", "line": "Apollo-St. Michael Axis", "note": "Southeastern extent of the great European ley alignment"},
    {"name": "Skellig Michael", "lat": 51.7703, "lon": -10.5386, "country": "Ireland", "type": "Island Monastery", "line": "Apollo-St. Michael Axis", "note": "Northwestern end of the great alignment, Star Wars filming site"},
    {"name": "Externsteine", "lat": 51.8689, "lon": 8.9164, "country": "Germany", "type": "Rock Pillars", "line": "Germanic Ley", "note": "Sacred site claimed to be on a major Central European ley"},
    {"name": "Carnac", "lat": 47.5861, "lon": -3.0750, "country": "France", "type": "Stone Rows", "line": "Breton Alignment", "note": "3000+ menhirs in parallel rows, largest megalithic site in world"},
    {"name": "Chartres Cathedral", "lat": 48.4478, "lon": 1.4878, "country": "France", "type": "Gothic Cathedral", "line": "Druidic Ley", "note": "Built on ancient sacred site, labyrinth and telluric energies"},
    {"name": "Rennes-le-Chateau", "lat": 42.9258, "lon": 2.2614, "country": "France", "type": "Hilltop Village", "line": "Rose Line", "note": "Mystery of Abbe Sauniere, alleged Paris Meridian alignment"},
    {"name": "Rosslyn Chapel", "lat": 55.8553, "lon": -3.1603, "country": "Scotland", "type": "Chapel", "line": "Rose Line / N-S Ley", "note": "Templar connections, alleged ley line node on Rose Line"},
    {"name": "Newgrange", "lat": 53.6947, "lon": -6.4754, "country": "Ireland", "type": "Passage Tomb", "line": "Irish Ley", "note": "Part of Bru na Boinne alignment with Knowth and Dowth"},
    {"name": "Tara Hill", "lat": 53.5786, "lon": -6.6117, "country": "Ireland", "type": "Royal Seat", "line": "Irish Ley", "note": "Seat of High Kings of Ireland, five ancient roads converge"},
    {"name": "Sedona - Bell Rock", "lat": 34.8067, "lon": -111.7628, "country": "USA", "type": "Vortex Site", "note": "Claimed energy vortex, major New Age pilgrimage site", "line": "Sedona Vortex"},
    {"name": "Sedona - Cathedral Rock", "lat": 34.8175, "lon": -111.7897, "country": "USA", "type": "Vortex Site", "note": "Feminine energy vortex, icon of red rock country", "line": "Sedona Vortex"},
    {"name": "Sedona - Airport Mesa", "lat": 34.8486, "lon": -111.7794, "country": "USA", "type": "Vortex Site", "note": "Electromagnetic vortex with panoramic views", "line": "Sedona Vortex"},
    {"name": "Nazca Lines", "lat": -14.7350, "lon": -75.1300, "country": "Peru", "type": "Geoglyphs", "note": "Massive ground drawings visible from air, alleged ley alignments", "line": "Andean Alignment"},
    {"name": "Giza Pyramids", "lat": 29.9792, "lon": 31.1342, "country": "Egypt", "type": "Pyramid Complex", "note": "Great Pyramid aligned precisely with cardinal directions", "line": "Global Grid Node"},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "country": "Peru", "type": "Inca City", "note": "Mountain citadel on claimed South American ley network", "line": "Andean Alignment"},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "type": "Temple Complex", "note": "Part of proposed global alignment of ancient monuments", "line": "Global Grid Node"},
    {"name": "Easter Island (Rapa Nui)", "lat": -27.1127, "lon": -109.3497, "country": "Chile", "type": "Island Monument", "note": "Moai statues aligned along the coast, global grid connection", "line": "Global Grid Node"},
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8438, "country": "Mexico", "type": "Pyramid Complex", "note": "Avenue of the Dead, claimed node on global sacred geometry", "line": "Global Grid Node"},
    {"name": "Uluru (Ayers Rock)", "lat": -25.3444, "lon": 131.0369, "country": "Australia", "type": "Sacred Monolith", "note": "Aboriginal songlines converge, immense spiritual significance", "line": "Songline / Dream Track"},
    {"name": "Kata Tjuta (The Olgas)", "lat": -25.3050, "lon": 130.7350, "country": "Australia", "type": "Sacred Rock Formation", "note": "36 domed rock formations, linked to Uluru by songlines", "line": "Songline / Dream Track"},
    {"name": "Mount Shasta", "lat": 41.4092, "lon": -122.1949, "country": "USA", "type": "Sacred Mountain", "note": "Claimed major vortex, Lemurian legends and ley connections", "line": "Pacific Ley"},
    {"name": "Serpent Mound", "lat": 39.0253, "lon": -83.4303, "country": "USA", "type": "Effigy Mound", "note": "1348-foot serpent effigy, aligned with solstice sunset", "line": "Ohio Valley Ley"},
    {"name": "Bodmin Moor - The Hurlers", "lat": 50.5178, "lon": -4.4589, "country": "England", "type": "Stone Circles", "note": "Three circles on Cornish ley, aligned with Cheesewring", "line": "Cornish Ley"},
    {"name": "Silbury Hill", "lat": 51.4156, "lon": -1.8575, "country": "England", "type": "Artificial Mound", "note": "Largest prehistoric mound in Europe, on St. Michael ley", "line": "St. Michael's Ley"},
]

FENG_SHUI = [
    {"name": "Forbidden City", "lat": 39.9163, "lon": 116.3972, "country": "China", "city": "Beijing", "era": "1420 CE", "note": "Ultimate feng shui layout: mountain behind, water before, central axis"},
    {"name": "Temple of Heaven", "lat": 39.8822, "lon": 116.4066, "country": "China", "city": "Beijing", "era": "1420 CE", "note": "Round heaven, square earth cosmology embedded in architecture"},
    {"name": "Hong Kong - Bank of China Tower", "lat": 22.2796, "lon": 114.1619, "country": "China", "city": "Hong Kong", "era": "1990 CE", "note": "Controversial sharp angles said to create negative feng shui"},
    {"name": "Hong Kong - HSBC Building", "lat": 22.2803, "lon": 114.1588, "country": "China", "city": "Hong Kong", "era": "1985 CE", "note": "Escalators angled per feng shui, lion guardians at entrance"},
    {"name": "Singapore - Marina Bay Sands", "lat": 1.2834, "lon": 103.8607, "country": "Singapore", "city": "Singapore", "era": "2010 CE", "note": "Designed with feng shui consultant, water features for wealth"},
    {"name": "Singapore - Wealth Fountain", "lat": 1.2947, "lon": 103.8589, "country": "Singapore", "city": "Singapore", "era": "1995 CE", "note": "World's largest fountain, feng shui design for prosperity"},
    {"name": "Taipei 101", "lat": 25.0340, "lon": 121.5645, "country": "Taiwan", "city": "Taipei", "era": "2004 CE", "note": "8 sections (lucky number), ruyi motifs, feng shui coin shape base"},
    {"name": "Ming Tombs - Sacred Way", "lat": 40.2533, "lon": 116.2217, "country": "China", "city": "Beijing", "era": "1409 CE", "note": "Imperial feng shui: mountains shield north, valley opens south"},
    {"name": "Summer Palace", "lat": 39.9994, "lon": 116.2755, "country": "China", "city": "Beijing", "era": "1750 CE", "note": "Kunming Lake and Longevity Hill follow feng shui water-mountain principle"},
    {"name": "Potala Palace", "lat": 29.6525, "lon": 91.1169, "country": "Tibet/China", "city": "Lhasa", "era": "637 CE", "note": "Built on Red Mountain for spiritual and feng shui elevation"},
    {"name": "Suzhou Gardens", "lat": 31.3200, "lon": 120.6200, "country": "China", "city": "Suzhou", "era": "c. 1500 CE", "note": "Classical gardens designed with feng shui balance of yin and yang"},
    {"name": "Hong Kong - Repulse Bay", "lat": 22.2375, "lon": 114.1972, "country": "China", "city": "Hong Kong", "era": "1989 CE", "note": "Building with square hole to let dragon pass to the sea"},
    {"name": "Gyeongbokgung Palace", "lat": 37.5796, "lon": 126.9770, "country": "South Korea", "city": "Seoul", "era": "1395 CE", "note": "Mountain behind (Bugaksan), river before - classic feng shui siting"},
    {"name": "Himeji Castle", "lat": 34.8394, "lon": 134.6939, "country": "Japan", "city": "Himeji", "era": "1346 CE", "note": "Japanese fusui (feng shui) principles in castle placement"},
    {"name": "Meiji Shrine", "lat": 35.6764, "lon": 139.6993, "country": "Japan", "city": "Tokyo", "era": "1920 CE", "note": "170,000 trees planted following Japanese geomancy traditions"},
    {"name": "Kuala Lumpur - Petronas Towers", "lat": 3.1579, "lon": 101.7116, "country": "Malaysia", "city": "Kuala Lumpur", "era": "1998 CE", "note": "Islamic geometry and feng shui principles in the design"},
    {"name": "Macau - Grand Lisboa", "lat": 22.1897, "lon": 113.5406, "country": "Macau/China", "city": "Macau", "era": "2008 CE", "note": "Lotus flower design following feng shui for gambling luck"},
    {"name": "Nanjing - Sun Yat-sen Mausoleum", "lat": 32.0617, "lon": 118.8483, "country": "China", "city": "Nanjing", "era": "1929 CE", "note": "Purple Mountain backdrop, bell-shaped layout for feng shui"},
    {"name": "Hangzhou - West Lake", "lat": 30.2500, "lon": 120.1500, "country": "China", "city": "Hangzhou", "era": "Ancient", "note": "Mountains on three sides, lake to east: ideal feng shui landscape"},
    {"name": "Wudang Mountain Temples", "lat": 32.4000, "lon": 111.0042, "country": "China", "city": "Shiyan", "era": "c. 1400 CE", "note": "Taoist temples positioned for qi flow along mountain ridges"},
    {"name": "Luang Prabang - Royal Palace", "lat": 19.8925, "lon": 102.1347, "country": "Laos", "city": "Luang Prabang", "era": "1904 CE", "note": "Between Mekong and Khan rivers, feng shui water convergence"},
    {"name": "Dragon's Back Ridge", "lat": 25.7833, "lon": 110.0333, "country": "China", "city": "Guilin", "era": "Ancient", "note": "Longji Rice Terraces follow natural dragon-vein feng shui contours"},
    {"name": "Jokhang Temple", "lat": 29.6525, "lon": 91.1319, "country": "Tibet/China", "city": "Lhasa", "era": "647 CE", "note": "Built to subdue demoness, geomantic placement on sacred lake"},
    {"name": "Chengde Mountain Resort", "lat": 40.9833, "lon": 117.9333, "country": "China", "city": "Chengde", "era": "1703 CE", "note": "Qing Dynasty retreat, miniature feng shui landscape of China"},
    {"name": "Thean Hou Temple", "lat": 3.1243, "lon": 101.6866, "country": "Malaysia", "city": "Kuala Lumpur", "era": "1989 CE", "note": "Six-tiered temple designed by feng shui master on Robson Hill"},
    {"name": "Todai-ji", "lat": 34.6889, "lon": 135.8397, "country": "Japan", "city": "Nara", "era": "752 CE", "note": "Largest wooden building, placement follows Japanese geomancy"},
    {"name": "Confucius Temple - Qufu", "lat": 35.5967, "lon": 116.9861, "country": "China", "city": "Qufu", "era": "478 BCE", "note": "2500-year feng shui tradition, north-south axis alignment"},
    {"name": "Doi Suthep Temple", "lat": 18.8048, "lon": 98.9217, "country": "Thailand", "city": "Chiang Mai", "era": "1383 CE", "note": "Mountain temple following Thai adaptation of feng shui (huat sa)"},
    {"name": "Reunification Palace", "lat": 10.7792, "lon": 106.6953, "country": "Vietnam", "city": "Ho Chi Minh City", "era": "1966 CE", "note": "Designed by Ngo Viet Thu with feng shui principles for power"},
    {"name": "Emperor Jade Pagoda", "lat": 10.7897, "lon": 106.6903, "country": "Vietnam", "city": "Ho Chi Minh City", "era": "1909 CE", "note": "Feng shui temple mixing Taoist and Buddhist geomancy"},
]

SOLSTICE_EQUINOX = [
    {"name": "Stonehenge - Summer Solstice Axis", "lat": 51.1789, "lon": -1.8262, "country": "England", "era": "c. 3000 BCE", "event": "Summer Solstice", "note": "Heel Stone aligns with midsummer sunrise, 25,000+ gather annually"},
    {"name": "Newgrange - Winter Solstice", "lat": 53.6947, "lon": -6.4754, "country": "Ireland", "era": "c. 3200 BCE", "event": "Winter Solstice", "note": "Roofbox channels solstice sunrise into 19m passage for 17 minutes"},
    {"name": "Chichen Itza - Equinox Serpent", "lat": 20.6843, "lon": -88.5678, "country": "Mexico", "era": "c. 1000 CE", "event": "Spring/Fall Equinox", "note": "Shadow of feathered serpent Kukulcan descends pyramid staircase"},
    {"name": "Abu Simbel - Solar Alignment", "lat": 22.3360, "lon": 31.6256, "country": "Egypt", "era": "c. 1264 BCE", "event": "Feb 22 & Oct 22", "note": "Sunlight illuminates Ramesses II and gods but not Ptah (darkness god)"},
    {"name": "Karnak Temple - Winter Solstice", "lat": 25.7188, "lon": 32.6573, "country": "Egypt", "era": "c. 2000 BCE", "event": "Winter Solstice", "note": "Central axis points to winter solstice sunset"},
    {"name": "Angkor Wat - Spring Equinox", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "era": "12th century CE", "event": "Spring Equinox", "note": "Sun rises directly over the central tower on equinox morning"},
    {"name": "Machu Picchu - Intihuatana", "lat": -13.1631, "lon": -72.5450, "country": "Peru", "era": "c. 1450 CE", "event": "Equinoxes", "note": "Hitching Post of the Sun casts no shadow at noon on equinoxes"},
    {"name": "Mnajdra - Equinox & Solstice", "lat": 35.8269, "lon": 14.4364, "country": "Malta", "era": "c. 3600 BCE", "event": "Equinox/Solstice", "note": "Lower temple doorway frames equinox sunrise, edges mark solstices"},
    {"name": "Chankillo - 13 Towers", "lat": -9.5589, "lon": -78.2272, "country": "Peru", "era": "c. 250 BCE", "event": "Full Solar Year", "note": "Sunrise moves tower-to-tower marking every date of the year"},
    {"name": "Goseck Circle - Winter Solstice", "lat": 51.1989, "lon": 11.8628, "country": "Germany", "era": "c. 4900 BCE", "event": "Winter Solstice", "note": "Palisade gates aligned with sunrise and sunset at winter solstice"},
    {"name": "Bryn Celli Ddu - Summer Solstice", "lat": 53.2072, "lon": -4.2364, "country": "Wales", "era": "c. 3000 BCE", "event": "Summer Solstice", "note": "Midsummer sunrise lights up the passage and rear stone"},
    {"name": "Loughcrew Cairn T - Equinox", "lat": 53.7447, "lon": -7.1186, "country": "Ireland", "era": "c. 3300 BCE", "event": "Spring/Fall Equinox", "note": "Equinox sunrise beam illuminates the decorated backstone"},
    {"name": "Dzibilchaltun - Equinox Sun", "lat": 21.0919, "lon": -89.5944, "country": "Mexico", "era": "c. 500 CE", "event": "Spring/Fall Equinox", "note": "Sun blazes through Temple of Seven Dolls doorway at equinox"},
    {"name": "Cahokia Woodhenge - Equinox", "lat": 38.6556, "lon": -90.0625, "country": "USA", "era": "c. 1100 CE", "event": "Equinox/Solstice", "note": "Cedar post circle marks solstice and equinox sunrises"},
    {"name": "Temple of Kukulcan - Uxmal", "lat": 20.3594, "lon": -89.7714, "country": "Mexico", "era": "c. 900 CE", "event": "Solstice", "note": "Governor's Palace facade split by solstice Venus alignment"},
    {"name": "Callanish Stones - Lunar Standstill", "lat": 58.1975, "lon": -6.7456, "country": "Scotland", "era": "c. 2900 BCE", "event": "Lunar Standstill", "note": "Moon skims southern hills every 18.6 years at major standstill"},
    {"name": "Externsteine - Summer Solstice", "lat": 51.8689, "lon": 8.9164, "country": "Germany", "era": "c. 1000 CE+", "event": "Summer Solstice", "note": "Chapel window catches first light of summer solstice sunrise"},
    {"name": "Kokino - Solstice Markers", "lat": 42.2639, "lon": 21.9528, "country": "North Macedonia", "era": "c. 1800 BCE", "event": "Equinox/Solstice", "note": "Stone thrones mark sunrise positions at solstices and equinoxes"},
    {"name": "Ale's Stones - Winter Solstice", "lat": 55.3833, "lon": 14.0536, "country": "Sweden", "era": "c. 600 CE", "event": "Winter Solstice", "note": "Ship-shaped stone setting oriented to solstice sunset in NW"},
    {"name": "Modhera Sun Temple - Equinox", "lat": 23.5833, "lon": 72.1333, "country": "India", "era": "1026 CE", "event": "Spring/Fall Equinox", "note": "Equinox sun illuminates the inner sanctum's gold idol"},
    {"name": "Konark Sun Temple - Solstice", "lat": 19.8876, "lon": 86.0945, "country": "India", "era": "c. 1250 CE", "event": "Winter Solstice", "note": "Chariot faces east, first rays strike Surya on winter solstice"},
    {"name": "Templo Mayor - Equinox Sunrise", "lat": 19.4348, "lon": -99.1313, "country": "Mexico", "era": "c. 1375 CE", "event": "Spring Equinox", "note": "Equinox sun rises between twin temple shrines atop the pyramid"},
    {"name": "Chimney Rock - Lunar Standstill", "lat": 37.1781, "lon": -107.3064, "country": "USA", "era": "c. 1076 CE", "event": "Lunar Standstill", "note": "Full moon rises between twin spires every 18.6 years"},
    {"name": "Sun Dagger - Solstice Spiral", "lat": 36.0600, "lon": -107.9560, "country": "USA", "era": "c. 1000 CE", "event": "Summer Solstice", "note": "Dagger of light bisects spiral petroglyph on Fajada Butte"},
    {"name": "Knowth - Equinox", "lat": 53.7014, "lon": -6.4900, "country": "Ireland", "era": "c. 3200 BCE", "event": "Spring/Fall Equinox", "note": "Eastern passage receives equinox sunrise, western gets sunset"},
    {"name": "Sarmizegetusa - Solstice", "lat": 45.6222, "lon": 23.3139, "country": "Romania", "era": "c. 1st century BCE", "event": "Solstice/Equinox", "note": "Circular sanctuary with posts aligned to solstice sunrise"},
    {"name": "Tiwanaku - Equinox Gateway", "lat": -16.5544, "lon": -68.6731, "country": "Bolivia", "era": "c. 200 CE", "event": "Equinox", "note": "Gateway of the Sun frames equinox sunrise precisely"},
    {"name": "Great Zimbabwe - Solstice", "lat": -20.2674, "lon": 30.9339, "country": "Zimbabwe", "era": "c. 11th century CE", "event": "Winter Solstice", "note": "Conical tower and monoliths may mark solstice sunrise"},
    {"name": "Ring of Brodgar - Solstice", "lat": 59.0014, "lon": -3.2294, "country": "Scotland", "era": "c. 2500 BCE", "event": "Summer Solstice", "note": "Henge diameter relates to midwinter sunset alignment"},
    {"name": "El Castillo (Xunantunich)", "lat": 17.0892, "lon": -89.1417, "country": "Belize", "era": "c. 800 CE", "event": "Equinox", "note": "Sun illuminates eastern face stucco frieze at equinox"},
    {"name": "Gavrinis - Winter Solstice", "lat": 47.5719, "lon": -2.8961, "country": "France", "era": "c. 3500 BCE", "event": "Winter Solstice", "note": "Passage tomb on island, solstice sunrise lights carved stones"},
    {"name": "Nabta Playa - Summer Solstice", "lat": 22.5100, "lon": 30.7100, "country": "Egypt", "era": "c. 5000 BCE", "event": "Summer Solstice", "note": "Stone rows and circle aligned with summer solstice sunrise"},
    {"name": "Almendres Cromlech - Equinox", "lat": 38.5567, "lon": -7.9700, "country": "Portugal", "era": "c. 6000 BCE", "event": "Spring Equinox", "note": "Stone oval alignment tracks equinox sunrise over the horizon"},
    {"name": "Zorats Karer - Summer Solstice", "lat": 39.5514, "lon": 46.0286, "country": "Armenia", "era": "c. 5500 BCE", "event": "Summer Solstice", "note": "Holed stones frame sunrise and sunset at solstice"},
    {"name": "Wurdi Youang - Equinox", "lat": -37.7700, "lon": 144.3400, "country": "Australia", "era": "c. 11000 BCE?", "event": "Equinox/Solstice", "note": "Aboriginal stone arrangement showing equinox and solstice positions"},
    {"name": "Puma Punku - Equinox", "lat": -16.5617, "lon": -68.6797, "country": "Bolivia", "era": "c. 536 CE", "event": "Equinox", "note": "Platform oriented to equinox sunrise, precise stone engineering"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def _safe_popup(title: str, fields: dict, max_width: int = 280) -> folium.Popup:
    """Build an HTML popup with html-escaped user data."""
    safe_title = html_module.escape(str(title))
    lines = [f'<div style="max-width:{max_width}px;">',
             f'<strong style="font-size:0.9rem;">{safe_title}</strong>']
    for label, value in fields.items():
        if value:
            safe_val = html_module.escape(str(value))
            lines.append(f'<br/><span style="font-size:0.75rem; color:#999;">'
                         f'{html_module.escape(label)}:</span> '
                         f'<span style="font-size:0.78rem;">{safe_val}</span>')
    lines.append('</div>')
    return folium.Popup("\n".join(lines), max_width=max_width + 20)


def _build_map(lat: float = 20.0, lon: float = 0.0, zoom: int = 2) -> folium.Map:
    """Create a dark-themed folium map."""
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )


def _add_markers(m: folium.Map, items: list, lat_key: str, lon_key: str,
                 popup_fields: list, color: str, radius: int = 7):
    """Add CircleMarkers from a list of dicts to a folium Map."""
    for item in items:
        fields = {k: item.get(k, "") for k in popup_fields}
        popup = _safe_popup(item.get("name", "Unknown"), fields)
        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=popup,
        ).add_to(m)


def _show_map(m: folium.Map):
    """Render a folium map via Streamlit components."""
    folium.LayerControl().add_to(m)
    components.html(m._repr_html_(), height=500)


def _csv_download(df: pd.DataFrame, filename: str, label: str, key: str):
    """Offer a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, data=buf.getvalue(), file_name=filename,
                       mime="text/csv", key=key)


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 1 - ANCIENT OBSERVATORIES & STAR TEMPLES
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_ancient_observatories():
    st.markdown("#### Ancient Observatories & Star Temples")
    st.markdown(
        '<p style="color:#8b97b0;">Prehistoric and ancient sites built to track the sun, '
        'moon, planets, and stars -- humanity\'s oldest astronomical instruments.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(ANCIENT_OBSERVATORIES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest Site", "c. 6000 BCE")
    c4.metric("Site Types", df["type"].nunique())

    st.markdown("##### Global Observatory Map")
    m = _build_map(25, 10, zoom=2)
    _add_markers(m, ANCIENT_OBSERVATORIES, "lat", "lon",
                 ["country", "era", "type", "note"],
                 ACCENT_AMBER, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "ancient_observatories.csv",
                  f"Download {len(df)} Observatories (CSV)", "dl_observatories")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 2 - ZODIAC ORIGINS & BABYLONIAN ASTRONOMY
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_zodiac_origins():
    st.markdown("#### Zodiac Origins & Babylonian Astronomy")
    st.markdown(
        '<p style="color:#8b97b0;">The birthplaces of the zodiac, from Sumerian clay tablets '
        'to Ptolemy\'s Tetrabiblos -- tracing how astrology spread across the ancient world.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(ZODIAC_ORIGINS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Traditions", df["tradition"].nunique())
    c4.metric("Earliest", "c. 3500 BCE")

    st.markdown("##### Zodiac Heritage Map")
    m = _build_map(33, 38, zoom=4)
    _add_markers(m, ZODIAC_ORIGINS, "lat", "lon",
                 ["country", "era", "tradition", "note"],
                 ACCENT_VIOLET, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "zodiac_origins.csv",
                  f"Download {len(df)} Zodiac Sites (CSV)", "dl_zodiac_origins")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 3 - CHINESE ASTROLOGY HERITAGE SITES
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_chinese_astrology():
    st.markdown("#### Chinese Astrology Heritage Sites")
    st.markdown(
        '<p style="color:#8b97b0;">From the Beijing Ancient Observatory to Korean and '
        'Japanese adaptations -- the vast network of East Asian zodiac and star-lore traditions.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(CHINESE_ASTROLOGY)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Site Types", df["type"].nunique())
    c4.metric("Oldest Site", "c. 1200 BCE")

    st.markdown("##### East Asian Astrology Map")
    m = _build_map(28, 108, zoom=4)
    _add_markers(m, CHINESE_ASTROLOGY, "lat", "lon",
                 ["country", "era", "type", "note"],
                 ACCENT_RED, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "chinese_astrology.csv",
                  f"Download {len(df)} Chinese Astrology Sites (CSV)", "dl_chinese_astro")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 4 - HINDU & VEDIC ASTRONOMY CENTERS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_hindu_vedic():
    st.markdown("#### Hindu & Vedic Astronomy Centers")
    st.markdown(
        '<p style="color:#8b97b0;">India\'s monumental Jantar Mantar observatories, '
        'sun temples, and the living tradition of Jyotish Shastra (Vedic astrology).</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(HINDU_VEDIC)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Site Types", df["type"].nunique())
    c4.metric("Oldest Tradition", "c. 1500 BCE")

    st.markdown("##### South Asian Astronomy Map")
    m = _build_map(20, 78, zoom=4)
    _add_markers(m, HINDU_VEDIC, "lat", "lon",
                 ["country", "era", "type", "note"],
                 ACCENT_ORANGE, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "hindu_vedic_astronomy.csv",
                  f"Download {len(df)} Vedic Sites (CSV)", "dl_hindu_vedic")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 5 - MAYAN & AZTEC ASTRONOMICAL SITES
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_mayan_aztec():
    st.markdown("#### Mayan & Aztec Astronomical Sites")
    st.markdown(
        '<p style="color:#8b97b0;">Mesoamerican civilizations that created the Long Count '
        'calendar, tracked Venus with astonishing precision, and built pyramid-observatories.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(MAYAN_AZTEC)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Site Types", df["type"].nunique())
    c4.metric("Oldest Site", "c. 1000 BCE")

    st.markdown("##### Mesoamerican Astronomy Map")
    m = _build_map(18, -90, zoom=5)
    _add_markers(m, MAYAN_AZTEC, "lat", "lon",
                 ["country", "era", "type", "note"],
                 ACCENT_EMERALD, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "mayan_aztec_astronomy.csv",
                  f"Download {len(df)} Mesoamerican Sites (CSV)", "dl_mayan_aztec")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 6 - MEDIEVAL ASTROLABE WORKSHOPS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_medieval_astrolabes():
    st.markdown("#### Medieval Astrolabe Workshops")
    st.markdown(
        '<p style="color:#8b97b0;">The cities where astrolabes were designed, crafted, '
        'and taught -- from Baghdad\'s House of Wisdom to Nuremberg\'s printing houses.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(MEDIEVAL_ASTROLABES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Workshop Types", df["type"].nunique())
    c4.metric("Earliest", "c. 700 CE")

    st.markdown("##### Astrolabe Heritage Map")
    m = _build_map(38, 25, zoom=3)
    _add_markers(m, MEDIEVAL_ASTROLABES, "lat", "lon",
                 ["country", "era", "type", "note"],
                 ACCENT_TEAL, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} cities)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "medieval_astrolabes.csv",
                  f"Download {len(df)} Astrolabe Cities (CSV)", "dl_astrolabes")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 7 - FAMOUS PLANETARIUMS WORLDWIDE
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_planetariums():
    st.markdown("#### Famous Planetariums Worldwide")
    st.markdown(
        '<p style="color:#8b97b0;">The world\'s greatest planetariums and public '
        'observatories -- domes where millions experience the cosmos.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(PLANETARIUMS)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Planetariums Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["opened"].min()))
    c4.metric("Newest", int(df["opened"].max()))

    st.markdown("##### Global Planetarium Map")
    m = _build_map(25, 0, zoom=2)
    _add_markers(m, PLANETARIUMS, "lat", "lon",
                 ["country", "city", "opened", "note"],
                 ACCENT_BLUE, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} planetariums)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "famous_planetariums.csv",
                  f"Download {len(df)} Planetariums (CSV)", "dl_planetariums")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 8 - LEY LINES & GEOMANCY SITES
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_ley_lines():
    st.markdown("#### Ley Lines & Geomancy Sites")
    st.markdown(
        '<p style="color:#8b97b0;">Alleged alignments of ancient monuments, sacred sites, '
        'and energy vortices -- from St. Michael\'s Ley to the Nazca Lines.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(LEY_LINES)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Ley Lines Named", df["line"].nunique())
    c4.metric("Site Types", df["type"].nunique())

    st.markdown("##### Global Ley Lines & Geomancy Map")
    m = _build_map(30, 0, zoom=2)
    _add_markers(m, LEY_LINES, "lat", "lon",
                 ["country", "type", "line", "note"],
                 ACCENT_FUCHSIA, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "ley_lines_geomancy.csv",
                  f"Download {len(df)} Ley Line Sites (CSV)", "dl_ley_lines")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 9 - FENG SHUI CULTURAL CENTERS
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_feng_shui():
    st.markdown("#### Feng Shui Cultural Centers")
    st.markdown(
        '<p style="color:#8b97b0;">Architecture designed by feng shui principles -- '
        'from the Forbidden City to modern skyscrapers oriented for qi flow and prosperity.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(FENG_SHUI)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest Site", "478 BCE")
    c4.metric("Newest", "2010 CE")

    st.markdown("##### Feng Shui Architecture Map")
    m = _build_map(25, 110, zoom=3)
    _add_markers(m, FENG_SHUI, "lat", "lon",
                 ["country", "city", "era", "note"],
                 ACCENT_PINK, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "feng_shui_centers.csv",
                  f"Download {len(df)} Feng Shui Sites (CSV)", "dl_feng_shui")


# ═══════════════════════════════════════════════════════════════════════════════
# MODE 10 - SOLSTICE & EQUINOX ALIGNMENT SITES
# ═══════════════════════════════════════════════════════════════════════════════

def _mode_solstice_equinox():
    st.markdown("#### Solstice & Equinox Alignment Sites")
    st.markdown(
        '<p style="color:#8b97b0;">Ancient structures precisely aligned to mark solstices, '
        'equinoxes, and lunar standstills -- humanity\'s deepest connection to celestial cycles.</p>',
        unsafe_allow_html=True,
    )

    df = pd.DataFrame(SOLSTICE_EQUINOX)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites Listed", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Event Types", df["event"].nunique())
    c4.metric("Oldest", "c. 6000 BCE")

    st.markdown("##### Global Alignment Sites Map")
    m = _build_map(25, 0, zoom=2)
    _add_markers(m, SOLSTICE_EQUINOX, "lat", "lon",
                 ["country", "era", "event", "note"],
                 ACCENT_CYAN, radius=8)
    _show_map(m)

    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True)

    _csv_download(df, "solstice_equinox_sites.csv",
                  f"Download {len(df)} Alignment Sites (CSV)", "dl_solstice")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

MAP_MODES = [
    "Ancient Observatories & Star Temples",
    "Zodiac Origins & Babylonian Astronomy",
    "Chinese Astrology Heritage Sites",
    "Hindu & Vedic Astronomy Centers",
    "Mayan & Aztec Astronomical Sites",
    "Medieval Astrolabe Workshops",
    "Famous Planetariums Worldwide",
    "Ley Lines & Geomancy Sites",
    "Feng Shui Cultural Centers",
    "Solstice & Equinox Alignment Sites",
]

MODE_ICONS = {
    "Ancient Observatories & Star Temples": "\u2728",
    "Zodiac Origins & Babylonian Astronomy": "\u2648",
    "Chinese Astrology Heritage Sites": "\U0001f409",
    "Hindu & Vedic Astronomy Centers": "\U0001f549",
    "Mayan & Aztec Astronomical Sites": "\U0001f3db",
    "Medieval Astrolabe Workshops": "\u2699",
    "Famous Planetariums Worldwide": "\U0001f52d",
    "Ley Lines & Geomancy Sites": "\U0001f300",
    "Feng Shui Cultural Centers": "\u262f",
    "Solstice & Equinox Alignment Sites": "\u2600",
}


def render_zodiac_maps_tab():
    """Main render function for the Astrology & Zodiac Explorer tab."""

    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\u2648 Astrology & Zodiac Explorer</h4>'
        '<p>Zodiac origins, astrology traditions, observatories & celestial mapping heritage</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "\u2648 Select Map Mode",
        MAP_MODES,
        format_func=lambda x: f"{MODE_ICONS.get(x, '')} {x}",
        key="zodiac_maps_mode",
    )

    st.markdown("---")

    if mode == "Ancient Observatories & Star Temples":
        _mode_ancient_observatories()
    elif mode == "Zodiac Origins & Babylonian Astronomy":
        _mode_zodiac_origins()
    elif mode == "Chinese Astrology Heritage Sites":
        _mode_chinese_astrology()
    elif mode == "Hindu & Vedic Astronomy Centers":
        _mode_hindu_vedic()
    elif mode == "Mayan & Aztec Astronomical Sites":
        _mode_mayan_aztec()
    elif mode == "Medieval Astrolabe Workshops":
        _mode_medieval_astrolabes()
    elif mode == "Famous Planetariums Worldwide":
        _mode_planetariums()
    elif mode == "Ley Lines & Geomancy Sites":
        _mode_ley_lines()
    elif mode == "Feng Shui Cultural Centers":
        _mode_feng_shui()
    elif mode == "Solstice & Equinox Alignment Sites":
        _mode_solstice_equinox()
