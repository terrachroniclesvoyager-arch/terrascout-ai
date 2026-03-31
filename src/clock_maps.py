# -*- coding: utf-8 -*-
"""
Clocks & Timekeeping Maps module for TerraScout AI.
Provides 10 thematic map modes covering famous clock towers, watchmaking
capitals, Greenwich & time zones, sundials, atomic clocks, observatories,
horology museums, church clocks, cuckoo clocks, and time capsules.

All data is hardcoded (curated). No API keys needed.
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
import requests
import html as html_module

# =====================================================================
# CONSTANTS
# =====================================================================

MAP_MODES = [
    "Famous Clock Towers",
    "Watchmaking Capitals",
    "Greenwich & Time Zones",
    "Sundials & Ancient Timekeeping",
    "Atomic Clock Facilities",
    "Astronomical Observatories",
    "Horology Museums",
    "Church & Cathedral Clocks",
    "Cuckoo Clock & Folk Clocks",
    "Time Capsule Locations",
]

MODE_COLORS = {
    "Famous Clock Towers": "#f59e0b",
    "Watchmaking Capitals": "#06b6d4",
    "Greenwich & Time Zones": "#10b981",
    "Sundials & Ancient Timekeeping": "#ec4899",
    "Atomic Clock Facilities": "#ef4444",
    "Astronomical Observatories": "#8b5cf6",
    "Horology Museums": "#3b82f6",
    "Church & Cathedral Clocks": "#a855f7",
    "Cuckoo Clock & Folk Clocks": "#f97316",
    "Time Capsule Locations": "#14b8a6",
}

# =====================================================================
# 1. FAMOUS CLOCK TOWERS (27)
# =====================================================================
FAMOUS_CLOCK_TOWERS = [
    {"name": "Big Ben (Elizabeth Tower)", "lat": 51.5007, "lon": -0.1246, "city": "London", "country": "UK", "year": 1859, "height_m": 96, "notes": "Iconic Gothic Revival clock tower at Palace of Westminster; Great Bell weighs 13.7 tonnes"},
    {"name": "Prague Astronomical Clock", "lat": 50.0870, "lon": 14.4208, "city": "Prague", "country": "Czech Republic", "year": 1410, "height_m": 28, "notes": "Oldest working astronomical clock in the world; animated apostles appear every hour"},
    {"name": "Zytglogge", "lat": 46.9480, "lon": 7.4474, "city": "Bern", "country": "Switzerland", "year": 1530, "height_m": 23, "notes": "Medieval clock tower with astronomical clock and animated figures; landmark of Bern old town"},
    {"name": "Rajabai Clock Tower", "lat": 18.9267, "lon": 72.8313, "city": "Mumbai", "country": "India", "year": 1878, "height_m": 85, "notes": "Gothic Revival tower at University of Mumbai; plays Rule Britannia and God Save the Queen tunes"},
    {"name": "Makkah Royal Clock Tower", "lat": 21.4187, "lon": 39.8253, "city": "Mecca", "country": "Saudi Arabia", "year": 2012, "height_m": 601, "notes": "Tallest clock tower in the world; four 43m clock faces visible from 25km away"},
    {"name": "Spasskaya Tower", "lat": 55.7525, "lon": 37.6231, "city": "Moscow", "country": "Russia", "year": 1491, "height_m": 71, "notes": "Main tower of the Kremlin wall; chiming clock broadcast on Russian radio since 1996"},
    {"name": "Clock Tower of Izmir", "lat": 38.4192, "lon": 27.1287, "city": "Izmir", "country": "Turkey", "year": 1901, "height_m": 25, "notes": "Ottoman clock tower in Konak Square; gift from German Kaiser Wilhelm II"},
    {"name": "Peace Tower", "lat": 45.4236, "lon": -75.7009, "city": "Ottawa", "country": "Canada", "year": 1927, "height_m": 92.2, "notes": "Centre block of Canadian Parliament; 53-bell carillon and Memorial Chamber"},
    {"name": "Joseph Chamberlain Memorial Clock Tower", "lat": 52.4505, "lon": -1.9304, "city": "Birmingham", "country": "UK", "year": 1908, "height_m": 100, "notes": "Tallest freestanding clock tower in the world; University of Birmingham campus"},
    {"name": "Torre dell'Orologio", "lat": 45.4345, "lon": 12.3389, "city": "Venice", "country": "Italy", "year": 1499, "height_m": 20, "notes": "St Mark's Clocktower with astronomical clock, Moor statues strike the bell on the hour"},
    {"name": "Zimmer Tower", "lat": 51.0861, "lon": 4.5700, "city": "Lier", "country": "Belgium", "year": 1930, "height_m": 30, "notes": "Houses 13 clocks, Centenary Clock with 57 dials showing lunar cycles, tides, zodiac"},
    {"name": "Rathaus-Glockenspiel", "lat": 48.1375, "lon": 11.5755, "city": "Munich", "country": "Germany", "year": 1908, "height_m": 85, "notes": "New Town Hall carillon with 43 bells and 32 life-size animated figures"},
    {"name": "Venetian Tower Clock (Nafplio)", "lat": 37.5673, "lon": 22.7996, "city": "Nafplio", "country": "Greece", "year": 1713, "height_m": 15, "notes": "Clock on top of the Palamidi fortress town; landmark of the first Greek capital"},
    {"name": "Tsim Sha Tsui Clock Tower", "lat": 22.2934, "lon": 114.1685, "city": "Hong Kong", "country": "China", "year": 1915, "height_m": 44, "notes": "Last remnant of the former Kowloon Station; declared monument and icon of Victoria Harbour"},
    {"name": "Clock Tower (Jodhpur)", "lat": 26.2976, "lon": 73.0190, "city": "Jodhpur", "country": "India", "year": 1912, "height_m": 30, "notes": "Ghanta Ghar overlooking Sardar Market; built by Maharaja Sardar Singh"},
    {"name": "Allen-Bradley Clock Tower", "lat": 43.0139, "lon": -87.9159, "city": "Milwaukee", "country": "USA", "year": 1962, "height_m": 64, "notes": "Largest four-faced clock in the Western Hemisphere; octagonal faces 12.2m diameter"},
    {"name": "Torre de Reloj (Cartagena)", "lat": 10.4237, "lon": -75.5511, "city": "Cartagena", "country": "Colombia", "year": 1601, "height_m": 30, "notes": "Main entrance to the walled city; original drawbridge replaced by clock in 1888"},
    {"name": "Mons Belfry", "lat": 50.4542, "lon": 3.9514, "city": "Mons", "country": "Belgium", "year": 1661, "height_m": 87, "notes": "Baroque belfry; UNESCO World Heritage Site; 49-bell carillon"},
    {"name": "Custom House Tower", "lat": 42.3599, "lon": -71.0531, "city": "Boston", "country": "USA", "year": 1915, "height_m": 151, "notes": "Tallest building in Boston until 1964; four 6.7m clock faces"},
    {"name": "Charminar Clock", "lat": 17.3616, "lon": 78.4747, "city": "Hyderabad", "country": "India", "year": 1889, "height_m": 56, "notes": "Clocks added to four arches of the 1591 Charminar monument by Nizam Mahbub Ali Khan"},
    {"name": "Dolmabahce Clock Tower", "lat": 41.0391, "lon": 29.0003, "city": "Istanbul", "country": "Turkey", "year": 1895, "height_m": 27, "notes": "Neo-Baroque tower near Dolmabahce Palace; French-made clock by Paul Garnier"},
    {"name": "Victoria Tower (Kolkata)", "lat": 22.5448, "lon": 88.3426, "city": "Kolkata", "country": "India", "year": 1906, "height_m": 50, "notes": "Clock tower within Victoria Memorial grounds; Italian Renaissance style"},
    {"name": "Brisbane City Hall Clock Tower", "lat": -27.4688, "lon": 153.0234, "city": "Brisbane", "country": "Australia", "year": 1930, "height_m": 92, "notes": "Heritage-listed sandstone tower; four 4.3m diameter illuminated clock faces"},
    {"name": "Torre dei Lamberti", "lat": 45.4425, "lon": 10.9980, "city": "Verona", "country": "Italy", "year": 1172, "height_m": 84, "notes": "Tallest tower in Verona; bells Rengo and Marangona have rung since medieval times"},
    {"name": "Savannah City Hall Clock", "lat": 32.0809, "lon": -81.0912, "city": "Savannah", "country": "USA", "year": 1906, "height_m": 21, "notes": "Copper-domed Renaissance Revival city hall overlooking Bull Street"},
    {"name": "Wuhan Custom House Clock", "lat": 30.5728, "lon": 114.2836, "city": "Wuhan", "country": "China", "year": 1924, "height_m": 46, "notes": "Neoclassical customs house on the Bund; Westminster chimes audible across the Yangtze"},
    {"name": "Torre Colpatria Clock", "lat": 4.6130, "lon": -74.0685, "city": "Bogota", "country": "Colombia", "year": 1979, "height_m": 196, "notes": "Tallest building in Bogota with illuminated clock and LED facade"},
]

# =====================================================================
# 2. WATCHMAKING CAPITALS (22)
# =====================================================================
WATCHMAKING_CAPITALS = [
    {"name": "La Chaux-de-Fonds", "lat": 47.0997, "lon": 6.8281, "country": "Switzerland", "year_est": 1705, "specialty": "Swiss watchmaking cradle", "notes": "UNESCO World Heritage; birthplace of Le Corbusier; entire city planned for watchmakers"},
    {"name": "Le Locle", "lat": 47.0567, "lon": 6.7487, "country": "Switzerland", "year_est": 1680, "specialty": "Precision watchmaking origin", "notes": "UNESCO WHS alongside La Chaux-de-Fonds; Daniel JeanRichard started watchmaking here"},
    {"name": "Geneva", "lat": 46.2044, "lon": 6.1432, "country": "Switzerland", "year_est": 1601, "specialty": "Haute horlogerie capital", "notes": "Patek Philippe, Rolex, Vacheron Constantin HQs; Geneva Seal quality mark since 1886"},
    {"name": "Biel/Bienne", "lat": 47.1375, "lon": 7.2461, "country": "Switzerland", "year_est": 1793, "specialty": "Swatch Group HQ, Omega", "notes": "Bilingual city; Swatch Group, Omega, and Rolex movement production"},
    {"name": "Schaffhausen", "lat": 47.6960, "lon": 8.6340, "country": "Switzerland", "year_est": 1868, "specialty": "IWC Schaffhausen", "notes": "Founded by American Florentine Ariosto Jones; Rhine Falls nearby"},
    {"name": "Grenchen", "lat": 47.1922, "lon": 7.3958, "country": "Switzerland", "year_est": 1851, "specialty": "Breitling, ETA movements", "notes": "Major movement manufacturing center; ETA SA produces millions of movements annually"},
    {"name": "Vallee de Joux", "lat": 46.6144, "lon": 6.3258, "country": "Switzerland", "year_est": 1740, "specialty": "Audemars Piguet, Jaeger-LeCoultre", "notes": "Remote Jura valley; ultra-complicated movements crafted here since 18th century"},
    {"name": "Glashutte", "lat": 50.8520, "lon": 13.7825, "country": "Germany", "year_est": 1845, "specialty": "German precision watchmaking", "notes": "A. Lange und Sohne, NOMOS, Glashutte Original; Ferdinand Adolph Lange founded industry here"},
    {"name": "Pforzheim", "lat": 48.8934, "lon": 8.7042, "country": "Germany", "year_est": 1767, "specialty": "Jewelry and watch city", "notes": "Goldstadt (Gold City); historically 75 percent of German jewelry and watch production"},
    {"name": "Besancon", "lat": 47.2378, "lon": 6.0241, "country": "France", "year_est": 1793, "specialty": "French watchmaking capital", "notes": "Controlled 96 percent of French watch production by 1900; Lip watches founded here"},
    {"name": "Morteau", "lat": 47.0569, "lon": 6.6022, "country": "France", "year_est": 1680, "specialty": "French Jura watchmaking", "notes": "Near Swiss border; cross-border watchmaking tradition with Le Locle"},
    {"name": "Tokyo (Seiko district)", "lat": 35.6897, "lon": 139.6922, "country": "Japan", "year_est": 1881, "specialty": "Seiko, Citizen, Casio", "notes": "Kintaro Hattori founded Seiko in Ginza; Grand Seiko competes with Swiss haute horlogerie"},
    {"name": "Suwa (Seiko Epson)", "lat": 36.0390, "lon": 138.1146, "country": "Japan", "year_est": 1942, "specialty": "Seiko Epson precision", "notes": "Suwa Seikosha produced first quartz wristwatch (Seiko Astron 35SQ) in 1969"},
    {"name": "Shenzhen", "lat": 22.5431, "lon": 114.0579, "country": "China", "year_est": 1980, "specialty": "World watch factory", "notes": "Produces over 60 percent of the world's watches by volume; massive OEM industry"},
    {"name": "Coventry", "lat": 52.4068, "lon": -1.5197, "country": "UK", "year_est": 1670, "specialty": "Historic English watchmaking", "notes": "By 1860 had 50+ watchmaking firms; industry declined after Swiss competition"},
    {"name": "Prescot", "lat": 53.4293, "lon": -2.8017, "country": "UK", "year_est": 1590, "specialty": "Lancashire watch tool making", "notes": "Made watch tools and movements for the entire British industry; Museum of Clock and Watch Making"},
    {"name": "Waltham", "lat": 42.3765, "lon": -71.2356, "country": "USA", "year_est": 1850, "specialty": "American Watch Company", "notes": "Waltham Watch Company pioneered interchangeable parts in watchmaking; Watch City"},
    {"name": "Lancaster (Hamilton)", "lat": 40.0379, "lon": -76.3055, "country": "USA", "year_est": 1892, "specialty": "Hamilton Watch Company", "notes": "The Watch of Railroad Accuracy; supplied military watches in both World Wars"},
    {"name": "Jura Mountains Region", "lat": 46.8000, "lon": 6.6000, "country": "Switzerland/France", "year_est": 1600, "specialty": "Watch Valley corridor", "notes": "200km arc from Geneva to Basel; greatest concentration of watchmakers on Earth"},
    {"name": "Villeret", "lat": 47.1547, "lon": 7.0233, "country": "Switzerland", "year_est": 1735, "specialty": "Blancpain origin", "notes": "Blancpain, oldest watch brand, founded here by Jehan-Jacques Blancpain in 1735"},
    {"name": "Fleurier", "lat": 46.9017, "lon": 6.5836, "country": "Switzerland", "year_est": 1730, "specialty": "Parmigiani, Chopard movements", "notes": "Val-de-Travers; Fleurier Quality Foundation certification; Vaucher Manufacture"},
    {"name": "Novosibirsk", "lat": 55.0084, "lon": 82.9357, "country": "Russia", "year_est": 1941, "specialty": "Vostok, Raketa heritage", "notes": "Soviet watch factories relocated here during WWII; Pobeda, Vostok brands"},
]

# =====================================================================
# 3. GREENWICH & TIME ZONES (17)
# =====================================================================
GREENWICH_TIME_ZONES = [
    {"name": "Royal Observatory Greenwich", "lat": 51.4769, "lon": -0.0005, "country": "UK", "type": "Prime Meridian origin", "notes": "Prime Meridian (0 degrees longitude) established here in 1884; home of GMT"},
    {"name": "Prime Meridian Line (Airy Transit Circle)", "lat": 51.4772, "lon": 0.0015, "country": "UK", "type": "Original 0-degree line", "notes": "Airy Transit Circle defined the meridian in 1851; ground marker and laser line"},
    {"name": "International Date Line - Taveuni, Fiji", "lat": -16.9417, "lon": -179.9833, "country": "Fiji", "type": "Date Line crossing", "notes": "Where today meets tomorrow; 180th meridian passes through Taveuni island"},
    {"name": "International Date Line - Diomede Islands", "lat": 65.7572, "lon": -169.0075, "country": "USA/Russia", "type": "Date Line crossing", "notes": "Big Diomede (Russia) and Little Diomede (USA) are 3.8km apart but 21 hours different"},
    {"name": "Paris Observatory (competing meridian)", "lat": 48.8362, "lon": 2.3365, "country": "France", "type": "Historic rival meridian", "notes": "Paris Meridian used by France until 1911; Arago medallions mark its path through Paris"},
    {"name": "US Naval Observatory", "lat": 38.9216, "lon": -77.0669, "country": "USA", "type": "US time standard", "notes": "Master Clock facility; provides precise time for GPS, military, and civilian use"},
    {"name": "Chatham Islands", "lat": -43.8840, "lon": -176.4613, "country": "New Zealand", "type": "UTC+12:45 zone", "notes": "One of the first inhabited places to see each new day; unique 45-minute offset"},
    {"name": "Kiribati (Line Islands)", "lat": 1.8721, "lon": -157.3637, "country": "Kiribati", "type": "UTC+14 (first to new day)", "notes": "First place on Earth to enter each new calendar day; Line Islands shifted to UTC+14 in 1995"},
    {"name": "Baker Island", "lat": 0.1936, "lon": -176.4769, "country": "USA", "type": "UTC-12 (last timezone)", "notes": "Uninhabited US territory; last place on Earth where each calendar day exists"},
    {"name": "Nepal Standard Time marker", "lat": 27.7172, "lon": 85.3240, "country": "Nepal", "type": "UTC+5:45 (unique offset)", "notes": "Nepal uses UTC+5:45, one of only a few 45-minute offset zones in the world"},
    {"name": "India Standard Time (Mirzapur)", "lat": 25.1466, "lon": 82.5789, "country": "India", "type": "IST reference longitude", "notes": "82.5 degrees E passes through Mirzapur; single timezone for 1.4 billion people"},
    {"name": "China unified timezone (Beijing)", "lat": 39.9042, "lon": 116.4074, "country": "China", "type": "Single timezone for huge nation", "notes": "All of China uses Beijing Time (UTC+8) despite spanning 5 geographical time zones"},
    {"name": "Eucla (Australia)", "lat": -31.6800, "lon": 128.8800, "country": "Australia", "type": "Unofficial UTC+8:45", "notes": "Small settlement uses unofficial UTC+8:45 timezone not recognized by any government"},
    {"name": "Newfoundland (St. Johns)", "lat": 47.5615, "lon": -52.7126, "country": "Canada", "type": "UTC-3:30", "notes": "Only timezone in North America with a 30-minute offset; Newfoundland Standard Time"},
    {"name": "Tehran (Iran Standard Time)", "lat": 35.6892, "lon": 51.3890, "country": "Iran", "type": "UTC+3:30", "notes": "Iran Standard Time; one of few countries using a 30-minute offset from UTC"},
    {"name": "Samoa Date Line shift", "lat": -13.8333, "lon": -171.7500, "country": "Samoa", "type": "Date line shifted in 2011", "notes": "Samoa skipped December 30, 2011 entirely when it moved west of the date line"},
    {"name": "Marquesas Islands", "lat": -9.7500, "lon": -139.0000, "country": "French Polynesia", "type": "UTC-9:30", "notes": "Uses unique UTC-9:30 offset; one of the most remote inhabited island chains"},
]

# =====================================================================
# 4. SUNDIALS & ANCIENT TIMEKEEPING (20)
# =====================================================================
SUNDIALS_ANCIENT = [
    {"name": "Obelisk of Thutmose III (Cleopatra's Needle)", "lat": 40.7794, "lon": -73.9654, "city": "New York", "country": "USA/Egypt", "era": "1450 BC", "type": "Shadow clock / obelisk", "notes": "Egyptian obelisk originally used as a shadow clock; now in Central Park"},
    {"name": "Tower of the Winds (Athens)", "lat": 37.9744, "lon": 23.7269, "city": "Athens", "country": "Greece", "era": "50 BC", "type": "Combined sundial/water clock", "notes": "Octagonal marble tower with 8 sundials, water clock, and wind vane; Roman-era"},
    {"name": "Jantar Mantar (Jaipur)", "lat": 26.9248, "lon": 75.8247, "city": "Jaipur", "country": "India", "era": "1734", "type": "Monumental sundial complex", "notes": "World's largest stone sundial (Samrat Yantra, 27m tall); UNESCO World Heritage"},
    {"name": "Jantar Mantar (Delhi)", "lat": 28.6271, "lon": 77.2166, "city": "New Delhi", "country": "India", "era": "1724", "type": "Astronomical instruments", "notes": "Built by Maharaja Jai Singh II; Misra Yantra measures shortest and longest days"},
    {"name": "Sundial of Augustus (Rome)", "lat": 41.9009, "lon": 12.4773, "city": "Rome", "country": "Italy", "era": "10 BC", "type": "Monumental obelisk sundial", "notes": "Solarium Augusti used an Egyptian obelisk as gnomon; 160m x 75m sundial on Campus Martius"},
    {"name": "Great Sundial of Jai Singh (Ujjain)", "lat": 23.1793, "lon": 75.7849, "city": "Ujjain", "country": "India", "era": "1725", "type": "Observatory sundials", "notes": "One of five Jantar Mantar observatories; Ujjain was the reference for Hindu prime meridian"},
    {"name": "Corpus Christi Sundial (Cambridge)", "lat": 52.2037, "lon": 0.1187, "city": "Cambridge", "country": "UK", "era": "1581", "type": "Vertical sundial", "notes": "Historic sundial on Corpus Christi College; painted polychrome design"},
    {"name": "Queen's College Sundial (Oxford)", "lat": 51.7520, "lon": -1.2477, "city": "Oxford", "country": "UK", "era": "1734", "type": "Vertical sundial", "notes": "Elaborate sundial on High Street facade; designed by an unknown maker"},
    {"name": "Cleopatra's Needle (London)", "lat": 51.5083, "lon": -0.1161, "city": "London", "country": "UK/Egypt", "era": "1450 BC", "type": "Obelisk shadow clock", "notes": "Egyptian granite obelisk on Victoria Embankment; originally at Heliopolis"},
    {"name": "Luxor Obelisk (Paris)", "lat": 48.8656, "lon": 2.3212, "city": "Paris", "country": "France/Egypt", "era": "1300 BC", "type": "Obelisk from Luxor Temple", "notes": "3300-year-old obelisk in Place de la Concorde; bronze markings show sundial lines added in 1999"},
    {"name": "Bernini Sundial Obelisk (Rome)", "lat": 41.8986, "lon": 12.4769, "city": "Rome", "country": "Italy", "era": "1667", "type": "Piazza sundial", "notes": "Obelisk in Piazza di Montecitorio; restored as sundial by Pope Clement XI in 1792"},
    {"name": "Seville Cathedral Sundial", "lat": 37.3861, "lon": -5.9926, "city": "Seville", "country": "Spain", "era": "1760", "type": "Vertical cathedral sundial", "notes": "Large sundial on the south wall of the world's largest Gothic cathedral"},
    {"name": "Great Wall Sundials (Beijing)", "lat": 40.4319, "lon": 116.5704, "city": "Beijing", "country": "China", "era": "700 BC", "type": "Chinese sundial (rigui)", "notes": "Ancient Chinese sundials found at the Forbidden City and Temple of Heaven"},
    {"name": "Temple of Heaven Sundial", "lat": 39.8822, "lon": 116.4066, "city": "Beijing", "country": "China", "era": "1420", "type": "Imperial sundial (rigui)", "notes": "Bronze equatorial sundial from Ming Dynasty; used for ceremonial timekeeping"},
    {"name": "Kathedrale Munster Sundial", "lat": 47.5596, "lon": 7.5886, "city": "Basel", "country": "Switzerland", "era": "1523", "type": "Cathedral sundial", "notes": "Painted sundial on the Munster cathedral; shows Basler Fasnacht time"},
    {"name": "Phra Pathom Chedi Sundial", "lat": 13.8196, "lon": 100.0600, "city": "Nakhon Pathom", "country": "Thailand", "era": "300 BC", "type": "Buddhist shadow marker", "notes": "Oldest Buddhist monument in Thailand; ancient shadow measurements for prayer times"},
    {"name": "Water Clock of Karnak", "lat": 25.7188, "lon": 32.6573, "city": "Luxor", "country": "Egypt", "era": "1400 BC", "type": "Clepsydra (water clock)", "notes": "Oldest known water clock found at Karnak Temple; alabaster vessel with hour markings"},
    {"name": "Ctesibius Water Clock site (Alexandria)", "lat": 31.2001, "lon": 29.9187, "city": "Alexandria", "country": "Egypt", "era": "250 BC", "type": "Mechanical water clock", "notes": "Ctesibius invented the most accurate water clock of antiquity; feedback-regulated flow"},
    {"name": "Su Song Water Clock Tower site", "lat": 34.7784, "lon": 114.3056, "city": "Kaifeng", "country": "China", "era": "1088", "type": "Astronomical clock tower", "notes": "Su Song built a 12m water-powered astronomical clock with escapement mechanism"},
    {"name": "Sundial Bridge (Redding, CA)", "lat": 40.5865, "lon": -122.3763, "city": "Redding", "country": "USA", "era": "2004", "type": "Functional sundial bridge", "notes": "Santiago Calatrava-designed bridge acts as a working sundial; 65m pylon as gnomon"},
]

# =====================================================================
# 5. ATOMIC CLOCK FACILITIES (15)
# =====================================================================
ATOMIC_CLOCK_FACILITIES = [
    {"name": "NIST-F2 Cesium Fountain Clock", "lat": 39.9905, "lon": -105.2631, "city": "Boulder", "country": "USA", "type": "Cesium fountain", "accuracy": "1 second in 300 million years", "notes": "US primary frequency standard since 2014; NIST campus in Boulder, Colorado"},
    {"name": "PTB (Physikalisch-Technische Bundesanstalt)", "lat": 52.2961, "lon": 10.4612, "city": "Braunschweig", "country": "Germany", "type": "Cesium fountain CS2", "accuracy": "1 second in 30 million years", "notes": "German national metrology institute; broadcasts DCF77 time signal across Europe"},
    {"name": "NPL (National Physical Laboratory)", "lat": 51.4264, "lon": -0.3444, "city": "Teddington", "country": "UK", "type": "Cesium fountain NPL-CsF2", "accuracy": "1 second in 158 million years", "notes": "UK time standard; contributes to UTC; MSF time signal on 60 kHz"},
    {"name": "BIPM (Bureau International des Poids et Mesures)", "lat": 48.8280, "lon": 2.2207, "city": "Sevres", "country": "France", "type": "UTC coordinator", "accuracy": "Coordinates global UTC", "notes": "Calculates International Atomic Time (TAI) and UTC from 450+ clocks worldwide"},
    {"name": "USNO Master Clock", "lat": 38.9216, "lon": -77.0669, "city": "Washington DC", "country": "USA", "type": "Ensemble of cesium/hydrogen maser", "accuracy": "1 second in 100 million years", "notes": "Provides precise time for US military, GPS constellation, and Department of Defense"},
    {"name": "GPS Master Control Station", "lat": 38.8230, "lon": -104.7005, "city": "Colorado Springs", "country": "USA", "type": "Rubidium/cesium on satellites", "accuracy": "10 nanoseconds", "notes": "Schriever Space Force Base; controls 31 GPS satellites each carrying atomic clocks"},
    {"name": "JILA Strontium Lattice Clock", "lat": 40.0076, "lon": -105.2630, "city": "Boulder", "country": "USA", "type": "Optical lattice (strontium)", "accuracy": "1 second in 15 billion years", "notes": "JILA/University of Colorado; most precise clock ever built as of 2022; next-gen standard"},
    {"name": "INRIM (Istituto Nazionale di Ricerca Metrologica)", "lat": 45.0147, "lon": 7.6394, "city": "Turin", "country": "Italy", "type": "Cesium fountain IT-CsF2", "accuracy": "1 second in 100 million years", "notes": "Italian national frequency standard; contributes to TAI"},
    {"name": "NICT (National Institute of ICT, Japan)", "lat": 35.7101, "lon": 139.5437, "city": "Tokyo", "country": "Japan", "type": "Cesium/optical clocks", "accuracy": "1 second in 160 million years", "notes": "Japan Standard Time source; operates JJY time signal broadcasts on 40/60 kHz"},
    {"name": "NIM (National Institute of Metrology, China)", "lat": 40.0017, "lon": 116.2261, "city": "Beijing", "country": "China", "type": "Cesium fountain NIM5", "accuracy": "1 second in 30 million years", "notes": "Chinese primary frequency standard; contributes to TAI and maintains BeiDou time"},
    {"name": "KRISS (Korea Research Institute)", "lat": 36.3852, "lon": 127.3720, "city": "Daejeon", "country": "South Korea", "type": "Cesium fountain KRISS-F1", "accuracy": "1 second in 50 million years", "notes": "Korean time standard; part of Daedeok Science Town research complex"},
    {"name": "VNIIFTRI (Russia)", "lat": 56.0171, "lon": 37.2095, "city": "Mendeleevo", "country": "Russia", "type": "Hydrogen maser ensemble", "accuracy": "1 second in 100 million years", "notes": "Russian State Time and Frequency Service; maintains GLONASS time"},
    {"name": "NPL India (National Physical Laboratory)", "lat": 28.6353, "lon": 77.1722, "city": "New Delhi", "country": "India", "type": "Cesium beam", "accuracy": "1 second in 3 million years", "notes": "Maintains Indian Standard Time (IST); broadcasts on All India Radio"},
    {"name": "Galileo Precise Timing Facility", "lat": 48.0639, "lon": 11.2556, "city": "Oberpfaffenhofen", "country": "Germany", "type": "Hydrogen maser + cesium", "accuracy": "28 nanoseconds", "notes": "DLR center; Galileo GNSS timing facility for European satellite navigation"},
    {"name": "National Research Council Canada", "lat": 45.3929, "lon": -75.7175, "city": "Ottawa", "country": "Canada", "type": "Cesium fountain FCs1", "accuracy": "1 second in 30 million years", "notes": "Maintains official Canadian time; NRC CHU time signal broadcasts"},
]

# =====================================================================
# 6. ASTRONOMICAL OBSERVATORIES (21)
# =====================================================================
ASTRONOMICAL_OBSERVATORIES = [
    {"name": "Royal Observatory Greenwich", "lat": 51.4769, "lon": -0.0005, "city": "Greenwich", "country": "UK", "founded": 1675, "notes": "Founded by Charles II; defined the Prime Meridian; home of GMT"},
    {"name": "Jantar Mantar (Jaipur)", "lat": 26.9248, "lon": 75.8247, "city": "Jaipur", "country": "India", "founded": 1734, "notes": "UNESCO WHS; 19 astronomical instruments including world's largest stone sundial"},
    {"name": "Ulugh Beg Observatory", "lat": 39.6714, "lon": 66.9783, "city": "Samarkand", "country": "Uzbekistan", "founded": 1420, "notes": "Built by Timurid ruler Ulugh Beg; 40m sextant; star catalog of 1018 stars"},
    {"name": "Paris Observatory", "lat": 48.8362, "lon": 2.3365, "city": "Paris", "country": "France", "founded": 1667, "notes": "Oldest operating observatory in the world; founded by Louis XIV; Paris meridian"},
    {"name": "Pulkovo Observatory", "lat": 59.7714, "lon": 30.3268, "city": "Saint Petersburg", "country": "Russia", "founded": 1839, "notes": "Astronomical capital of the world in 19th century; Pulkovo meridian reference"},
    {"name": "Vatican Observatory (Castel Gandolfo)", "lat": 41.7478, "lon": 12.6500, "city": "Castel Gandolfo", "country": "Vatican/Italy", "founded": 1891, "notes": "One of oldest astronomical research institutions; now headquartered at Steward Observatory"},
    {"name": "Mount Wilson Observatory", "lat": 34.2258, "lon": -118.0594, "city": "Los Angeles", "country": "USA", "founded": 1904, "notes": "Hubble discovered expanding universe here in 1929; 100-inch Hooker telescope"},
    {"name": "Palomar Observatory", "lat": 33.3564, "lon": -116.8650, "city": "San Diego County", "country": "USA", "founded": 1948, "notes": "200-inch Hale Telescope was world's largest for 45 years; Caltech operated"},
    {"name": "Mauna Kea Observatories", "lat": 19.8207, "lon": -155.4681, "city": "Hawaii", "country": "USA", "founded": 1970, "notes": "13 telescopes at 4205m altitude; best ground-based site; Keck, Subaru, Gemini"},
    {"name": "Yerkes Observatory", "lat": 42.5700, "lon": -88.5561, "city": "Williams Bay", "country": "USA", "founded": 1897, "notes": "Houses world's largest refracting telescope (40-inch); founded by George Ellery Hale"},
    {"name": "Arecibo Observatory (collapsed)", "lat": 18.3464, "lon": -66.7528, "city": "Arecibo", "country": "Puerto Rico", "founded": 1963, "notes": "305m radio dish collapsed Dec 2020; was largest single-aperture telescope for 53 years"},
    {"name": "Beijing Ancient Observatory", "lat": 39.9023, "lon": 116.4264, "city": "Beijing", "country": "China", "founded": 1442, "notes": "One of oldest observatories in the world; bronze Qing-dynasty instruments on rooftop"},
    {"name": "Griffith Observatory", "lat": 34.1184, "lon": -118.3004, "city": "Los Angeles", "country": "USA", "founded": 1935, "notes": "Most visited public observatory in the world; free telescope viewing; Hollywood Hills"},
    {"name": "Sydney Observatory", "lat": -33.8599, "lon": 151.2042, "city": "Sydney", "country": "Australia", "founded": 1858, "notes": "Oldest observatory in Australia; originally dropped time ball for ships in harbour"},
    {"name": "Maragheh Observatory", "lat": 37.3906, "lon": 46.2226, "city": "Maragheh", "country": "Iran", "founded": 1259, "notes": "Built by Nasir al-Din al-Tusi; most advanced observatory of the Islamic Golden Age"},
    {"name": "Istanbul Observatory (Taqi ad-Din)", "lat": 41.0602, "lon": 29.0148, "city": "Istanbul", "country": "Turkey", "founded": 1577, "notes": "Built by Taqi ad-Din Muhammad; rivaled Tycho Brahe's Uraniborg; destroyed in 1580"},
    {"name": "Paranal Observatory (ESO)", "lat": -24.6275, "lon": -70.4044, "city": "Atacama", "country": "Chile", "founded": 1998, "notes": "Very Large Telescope (VLT); four 8.2m telescopes; driest place on Earth for astronomy"},
    {"name": "ALMA (Atacama Large Millimeter Array)", "lat": -23.0193, "lon": -67.7532, "city": "Chajnantor", "country": "Chile", "founded": 2013, "notes": "66 radio antennas at 5058m altitude; most expensive ground-based telescope ever built"},
    {"name": "Pic du Midi Observatory", "lat": 42.9364, "lon": 0.1423, "city": "Pyrenees", "country": "France", "founded": 1878, "notes": "At 2877m in the Pyrenees; mapped the Moon for Apollo missions; dark sky reserve"},
    {"name": "Jodrell Bank Observatory", "lat": 53.2367, "lon": -2.3085, "city": "Cheshire", "country": "UK", "founded": 1945, "notes": "76m Lovell Telescope; UNESCO World Heritage; tracked Sputnik and early space missions"},
    {"name": "Leander McCormick Observatory", "lat": 38.0333, "lon": -78.5236, "city": "Charlottesville", "country": "USA", "founded": 1885, "notes": "University of Virginia; 26-inch refractor; measured parallax of nearby stars"},
]

# =====================================================================
# 7. HOROLOGY MUSEUMS (16)
# =====================================================================
HOROLOGY_MUSEUMS = [
    {"name": "Musee International d'Horlogerie", "lat": 47.1011, "lon": 6.8275, "city": "La Chaux-de-Fonds", "country": "Switzerland", "collection_size": "4500+ pieces", "notes": "World's foremost clock and watch museum; underground building; 500 years of timekeeping"},
    {"name": "Beyer Clock and Watch Museum", "lat": 47.3686, "lon": 8.5391, "city": "Zurich", "country": "Switzerland", "collection_size": "500+ pieces", "notes": "Oldest clock shop in Switzerland (since 1760); collection spans 5000 years of timekeeping"},
    {"name": "NAWCC National Watch & Clock Museum", "lat": 40.0335, "lon": -76.5026, "city": "Columbia, PA", "country": "USA", "collection_size": "12000+ pieces", "notes": "Largest horological collection in North America; National Association of Watch and Clock Collectors"},
    {"name": "Deutsches Uhrenmuseum", "lat": 48.0569, "lon": 8.2172, "city": "Furtwangen", "country": "Germany", "collection_size": "8000+ pieces", "notes": "German Clock Museum in the Black Forest; world's largest cuckoo clock collection"},
    {"name": "Science Museum Clock Gallery", "lat": 51.4978, "lon": -0.1745, "city": "London", "country": "UK", "collection_size": "1500+ pieces", "notes": "Includes Harrison's marine chronometers H1-H4 that solved the longitude problem"},
    {"name": "Clockmakers' Museum (Science Museum)", "lat": 51.4978, "lon": -0.1745, "city": "London", "country": "UK", "collection_size": "600+ pieces", "notes": "Worshipful Company of Clockmakers collection; oldest horological collection (since 1814)"},
    {"name": "Patek Philippe Museum", "lat": 46.1974, "lon": 6.1412, "city": "Geneva", "country": "Switzerland", "collection_size": "2500+ pieces", "notes": "Five centuries of watchmaking; Caliber 89 with 33 complications; Art Deco building"},
    {"name": "Musee d'Horlogerie du Locle", "lat": 47.0564, "lon": 6.7491, "city": "Le Locle", "country": "Switzerland", "collection_size": "3000+ pieces", "notes": "Chateau des Monts; comprehensive Swiss watchmaking history; UNESCO region"},
    {"name": "Glashutte Uhrenmuseum", "lat": 50.8522, "lon": 13.7831, "city": "Glashutte", "country": "Germany", "collection_size": "500+ pieces", "notes": "German Watchmaking Museum; traces Ferdinand Adolph Lange's legacy from 1845"},
    {"name": "Clock Museum (Vienna)", "lat": 48.2105, "lon": 16.3534, "city": "Vienna", "country": "Austria", "collection_size": "3000+ pieces", "notes": "Uhrenmuseum Wien; three floors of clocks spanning 600 years; housed in Schulhof palace"},
    {"name": "Musee de l'Horlogerie (Geneva)", "lat": 46.1875, "lon": 6.1570, "city": "Geneva", "country": "Switzerland", "collection_size": "1000+ pieces", "notes": "Free museum in Malagnou Park villa; Genevan enameled watches and cloisonne art"},
    {"name": "American Clock and Watch Museum", "lat": 41.6757, "lon": -72.9426, "city": "Bristol, CT", "country": "USA", "collection_size": "5500+ pieces", "notes": "In the former clock capital of the US; Seth Thomas, New Haven Clock history"},
    {"name": "National Maritime Museum (Longitude Gallery)", "lat": 51.4809, "lon": -0.0054, "city": "Greenwich", "country": "UK", "collection_size": "200+ chronometers", "notes": "John Harrison's H1-H4 sea clocks that solved the longitude problem; Dava Sobel's Longitude"},
    {"name": "Musee du Temps", "lat": 47.2378, "lon": 6.0241, "city": "Besancon", "country": "France", "collection_size": "1500+ pieces", "notes": "Museum of Time in Renaissance palace; Besancon was capital of French watchmaking"},
    {"name": "Willard House and Clock Museum", "lat": 42.2779, "lon": -71.8105, "city": "Grafton, MA", "country": "USA", "collection_size": "80+ pieces", "notes": "Birthplace of four Willard brothers who revolutionized American clockmaking (banjo clock)"},
    {"name": "Seiko Museum Ginza", "lat": 35.6722, "lon": 139.7650, "city": "Tokyo", "country": "Japan", "collection_size": "1000+ pieces", "notes": "Seiko corporate museum; chronicles the quartz revolution and Spring Drive development"},
]

# =====================================================================
# 8. CHURCH & CATHEDRAL CLOCKS (20)
# =====================================================================
CHURCH_CATHEDRAL_CLOCKS = [
    {"name": "Strasbourg Cathedral Astronomical Clock", "lat": 48.5818, "lon": 7.7510, "city": "Strasbourg", "country": "France", "year": 1843, "type": "Astronomical clock", "notes": "Third clock on this site; perpetual calendar, orrery, eclipses; noon automaton procession"},
    {"name": "Wells Cathedral Clock", "lat": 51.2090, "lon": -2.6475, "city": "Wells", "country": "UK", "year": 1390, "type": "Medieval mechanical clock", "notes": "Second oldest surviving clock mechanism in England; jousting knights quarter-jack"},
    {"name": "Salisbury Cathedral Clock", "lat": 51.0650, "lon": -1.7978, "city": "Salisbury", "country": "UK", "year": 1386, "type": "Oldest working clock", "notes": "Oldest surviving mechanical clock in the world (no face, just strikes hours)"},
    {"name": "Rouen Gros Horloge", "lat": 49.4432, "lon": 1.0932, "city": "Rouen", "country": "France", "year": 1389, "type": "Astronomical street clock", "notes": "14th-century mechanism in Renaissance arch; single hand shows hour; phases of moon"},
    {"name": "Exeter Cathedral Clock", "lat": 50.7225, "lon": -3.5310, "city": "Exeter", "country": "UK", "year": 1484, "type": "Astronomical clock", "notes": "Shows hours, minutes, moon phase, and Ptolemaic Earth-centered universe"},
    {"name": "Ottery St Mary Church Clock", "lat": 50.7500, "lon": -3.2300, "city": "Ottery St Mary", "country": "UK", "year": 1400, "type": "Astronomical clock", "notes": "One of the oldest surviving church clocks in England; planetary dial"},
    {"name": "Lund Cathedral Astronomical Clock", "lat": 55.7036, "lon": 13.1937, "city": "Lund", "country": "Sweden", "year": 1425, "type": "Astronomical clock", "notes": "In Nomine Domini; three kings procession twice daily; calendar until 2123"},
    {"name": "Bern Zytglogge", "lat": 46.9480, "lon": 7.4474, "city": "Bern", "country": "Switzerland", "year": 1530, "type": "Astronomical clock tower", "notes": "Animated bears, rooster, and Father Time; Einstein walked past daily inspiring relativity"},
    {"name": "Lyon Cathedral Astronomical Clock", "lat": 45.7602, "lon": 4.8268, "city": "Lyon", "country": "France", "year": 1598, "type": "Astronomical clock", "notes": "14th-century mechanism in Cathedral of Saint-Jean-Baptiste; automaton figures at noon"},
    {"name": "Munster Cathedral Clock", "lat": 51.9628, "lon": 7.6256, "city": "Munster", "country": "Germany", "year": 1540, "type": "Astronomical clock", "notes": "Shows calendar until 2071; Magi procession at noon; one of few surviving Renaissance clocks"},
    {"name": "St. Mark's Clocktower (Venice)", "lat": 45.4345, "lon": 12.3389, "city": "Venice", "country": "Italy", "year": 1499, "type": "Moor clock", "notes": "Two bronze Moors strike the bell; zodiac, moon phases; gateway to Merceria shopping street"},
    {"name": "Beauvais Cathedral Clock", "lat": 49.4311, "lon": 2.0804, "city": "Beauvais", "country": "France", "year": 1868, "type": "Monumental astronomical clock", "notes": "12m tall with 90000 parts; 52 dials; shows tides, eclipses, sunrise/sunset; Auguste-Lucien Verite"},
    {"name": "Canterbury Cathedral Clock", "lat": 51.2798, "lon": 1.0830, "city": "Canterbury", "country": "UK", "year": 1292, "type": "Medieval clock", "notes": "One of England's earliest documented church clocks; original mechanism lost"},
    {"name": "Olomouc Astronomical Clock", "lat": 49.5955, "lon": 17.2518, "city": "Olomouc", "country": "Czech Republic", "year": 1422, "type": "Town hall astronomical clock", "notes": "Rebuilt in Socialist Realist style in 1955; originally Gothic; mosaic workers parade at noon"},
    {"name": "Messina Cathedral Clock", "lat": 38.1922, "lon": 15.5570, "city": "Messina", "country": "Italy", "year": 1933, "type": "Mechanical astronomical", "notes": "Largest and most complex astronomical clock in the world; built by Ungerer of Strasbourg"},
    {"name": "Cremona Torrazzo Clock", "lat": 45.1337, "lon": 10.0236, "city": "Cremona", "country": "Italy", "year": 1588, "type": "Astronomical tower clock", "notes": "On the tallest medieval brick tower in Europe (112m); shows zodiac and moon phases"},
    {"name": "Padua Clock Tower", "lat": 45.4064, "lon": 11.8768, "city": "Padua", "country": "Italy", "year": 1344, "type": "Astronomical clock", "notes": "One of the oldest astronomical clocks; designed by Jacopo Dondi; zodiac display"},
    {"name": "Hampton Court Palace Clock", "lat": 51.4037, "lon": -0.3378, "city": "London", "country": "UK", "year": 1540, "type": "Astronomical clock", "notes": "Made for Henry VIII; shows hour, month, day, zodiac, moon phase, high tide at London Bridge"},
    {"name": "Chartres Cathedral Clock", "lat": 48.4478, "lon": 1.4883, "city": "Chartres", "country": "France", "year": 1528, "type": "Astronomical clock", "notes": "Inside the UNESCO World Heritage cathedral; perpetual calendar mechanism"},
    {"name": "Gdansk St Mary's Church Clock", "lat": 54.3500, "lon": 18.6533, "city": "Gdansk", "country": "Poland", "year": 1470, "type": "Astronomical clock", "notes": "Hans Dueringer's masterpiece; 14m tall; calendar until 2017 then restored; Adam and Eve automata"},
]

# =====================================================================
# 9. CUCKOO CLOCK & FOLK CLOCKS (16)
# =====================================================================
CUCKOO_FOLK_CLOCKS = [
    {"name": "Triberg - World's Largest Cuckoo Clocks", "lat": 48.1303, "lon": 8.2314, "city": "Triberg", "country": "Germany", "type": "Giant cuckoo clock", "notes": "Two competing world's largest cuckoo clocks; Eble Uhren-Park and Schonach versions"},
    {"name": "Schonach - World Record Cuckoo Clock", "lat": 48.1422, "lon": 8.2017, "city": "Schonach", "country": "Germany", "type": "Guinness record cuckoo", "notes": "15m x 4.5m; officially recognized by Guinness as the world's largest cuckoo clock"},
    {"name": "Furtwangen German Clock Museum", "lat": 48.0569, "lon": 8.2172, "city": "Furtwangen", "country": "Germany", "type": "Cuckoo clock museum", "notes": "Largest collection of Black Forest clocks; Robert Gerwig founded the museum in 1852"},
    {"name": "Villingen-Schwenningen (clock industry)", "lat": 48.0603, "lon": 8.4936, "city": "Villingen-Schwenningen", "country": "Germany", "type": "Clock manufacturing town", "notes": "Historic center of Black Forest clock industry; Kienzle and Mauthe clockworks founded here"},
    {"name": "St. Goar - German Clock Road", "lat": 50.1539, "lon": 7.7111, "city": "St. Goar", "country": "Germany", "type": "Cuckoo clock shops", "notes": "Rhine Valley cuckoo clock capital; Deutsche Uhrenstrasse (German Clock Road) passes through"},
    {"name": "Titisee-Neustadt", "lat": 47.9036, "lon": 8.1578, "city": "Titisee-Neustadt", "country": "Germany", "type": "Black Forest clock village", "notes": "Traditional cuckoo clock shops around Lake Titisee; Drubba cuckoo clock house"},
    {"name": "Hofgut Sternen (Ravenna Gorge)", "lat": 47.8867, "lon": 8.0936, "city": "Breitnau", "country": "Germany", "type": "Historic clock workshop", "notes": "Traditional Black Forest farmstead with working cuckoo clock demonstration workshop"},
    {"name": "Vosges Mountains Clock Trail", "lat": 48.2000, "lon": 7.1000, "city": "Vosges", "country": "France", "type": "Alsatian clockmaking", "notes": "French side of the clockmaking tradition; Route de l'Horlogerie connects Alsatian workshops"},
    {"name": "Jura Comtoise Clock Region", "lat": 47.0000, "lon": 6.0500, "city": "Franche-Comte", "country": "France", "type": "Comtoise clocks", "notes": "Morbier and Comtoise longcase clocks made here since 1680; distinctive wavy pendulum"},
    {"name": "Mora Clock Village", "lat": 61.0042, "lon": 14.5450, "city": "Mora", "country": "Sweden", "type": "Swedish folk clock", "notes": "Mora clocks (Moraklockor) handmade since 1750s; tall case clocks with painted folk art"},
    {"name": "Frisian Tail Clock Region", "lat": 53.2000, "lon": 5.8000, "city": "Friesland", "country": "Netherlands", "type": "Staartklok (tail clock)", "notes": "Distinctive wall clocks with exposed pendulum and weights; Joure clockmaking tradition"},
    {"name": "Zaandam Clock District", "lat": 52.4383, "lon": 4.8264, "city": "Zaandam", "country": "Netherlands", "type": "Zaandam wall clocks", "notes": "Ornate wall clocks with carved wooden cases; Zaanse Schans preserves traditional crafts"},
    {"name": "Selva di Val Gardena", "lat": 46.5561, "lon": 11.7561, "city": "Val Gardena", "country": "Italy", "type": "Carved wooden clocks", "notes": "South Tyrolean wood carving tradition; cuckoo clocks with hand-carved Alpine scenes"},
    {"name": "Brienz Wood Carving Village", "lat": 46.7553, "lon": 8.0453, "city": "Brienz", "country": "Switzerland", "type": "Swiss carved clocks", "notes": "Famous wood carving school since 1884; Swiss chalet clocks with music box movements"},
    {"name": "Appenzell Folk Clock Tradition", "lat": 47.3319, "lon": 9.4069, "city": "Appenzell", "country": "Switzerland", "type": "Painted folk clocks", "notes": "Sennenstreifen paintings on clock faces; traditional farmer's almanac imagery"},
    {"name": "Tokei Jikake no Kuni (Japan)", "lat": 35.2220, "lon": 136.9300, "city": "Nagoya", "country": "Japan", "type": "Karakuri puppet clocks", "notes": "Karakuri automaton clocks; 17th-century Japanese mechanical puppet clockwork tradition"},
]

# =====================================================================
# 10. TIME CAPSULE LOCATIONS (16)
# =====================================================================
TIME_CAPSULE_LOCATIONS = [
    {"name": "Westinghouse Time Capsule (1939)", "lat": 40.7462, "lon": -73.8448, "city": "Queens, New York", "country": "USA", "year_buried": 1939, "open_date": "6939", "notes": "Buried at 1939 World's Fair in Flushing Meadows; cupaloy torpedo shell; to be opened in 5000 years"},
    {"name": "Westinghouse Time Capsule II (1965)", "lat": 40.7462, "lon": -73.8448, "city": "Queens, New York", "country": "USA", "year_buried": 1965, "open_date": "6965", "notes": "Buried 10 feet from the 1939 capsule at 1964 World's Fair; contains credit card, bikini, contact lens"},
    {"name": "Crypt of Civilization", "lat": 33.7906, "lon": -84.3229, "city": "Atlanta", "country": "USA", "year_buried": 1940, "open_date": "8113", "notes": "Sealed room at Oglethorpe University; first successful time capsule; to be opened in 6177 years"},
    {"name": "KEO Satellite (planned)", "lat": 48.8566, "lon": 2.3522, "city": "Paris (HQ)", "country": "France", "year_buried": 2024, "open_date": "52000", "notes": "Planned orbital time capsule to reenter in 50000 years; carries messages from millions of people"},
    {"name": "Helium Centennial Time Columns", "lat": 35.1897, "lon": -101.8313, "city": "Amarillo", "country": "USA", "year_buried": 1968, "open_date": "1993-2968", "notes": "Four stainless steel columns; first opened in 1993 (25 yrs), next in 2068, 2168, 2968"},
    {"name": "MOMA Time Capsule (Andy Warhol)", "lat": 40.7614, "lon": -73.9776, "city": "New York", "country": "USA", "year_buried": 1967, "open_date": "Opened 1987", "notes": "Warhol created 610 cardboard Time Capsules stuffed with ephemera; now in museum archives"},
    {"name": "Voyager Golden Record (in space)", "lat": 28.5721, "lon": -80.6480, "city": "Cape Canaveral (launch)", "country": "USA", "year_buried": 1977, "open_date": "Indefinite", "notes": "Two gold-plated records on Voyagers 1 and 2; sounds of Earth, music, images; now in interstellar space"},
    {"name": "International Time Capsule Society HQ", "lat": 33.7906, "lon": -84.3229, "city": "Atlanta", "country": "USA", "year_buried": 1990, "open_date": "N/A (registry)", "notes": "Founded at Oglethorpe University to track world's time capsules; estimates 10000+ exist worldwide"},
    {"name": "Osaka Castle Time Capsule", "lat": 34.6873, "lon": 135.5262, "city": "Osaka", "country": "Japan", "year_buried": 1970, "open_date": "6970", "notes": "Two capsules buried at Expo 70; one opened every 100 years, other in 5000 years; 2098 items"},
    {"name": "MIT Bottle of Good Wishes", "lat": 42.3601, "lon": -71.0942, "city": "Cambridge, MA", "country": "USA", "year_buried": 1957, "open_date": "2957", "notes": "Stainless steel time capsule placed during new building construction at MIT; 1000-year seal"},
    {"name": "Bicentennial Wagon Train Capsule", "lat": 38.8951, "lon": -77.0364, "city": "Washington DC", "country": "USA", "year_buried": 1976, "open_date": "2076", "notes": "Buried at the National Archives; 22000 messages from Americans during Bicentennial celebration"},
    {"name": "Yahoo Time Capsule", "lat": 37.7749, "lon": -122.4194, "city": "San Francisco", "country": "USA", "year_buried": 2006, "open_date": "2020", "notes": "Digital time capsule with contributions from people in 200+ countries via Smithsonian partnership"},
    {"name": "Detroit Century Box", "lat": 42.3314, "lon": -83.0458, "city": "Detroit", "country": "USA", "year_buried": 1900, "open_date": "Opened 2000", "notes": "Sealed by Detroit Mayor Maybury in 1900; opened on Dec 31, 2000; photos, city plans, messages"},
    {"name": "Samuel Adams Time Capsule (Boston)", "lat": 42.3588, "lon": -71.0637, "city": "Boston", "country": "USA", "year_buried": 1795, "open_date": "Opened 2014", "notes": "Found in Massachusetts State House cornerstone; placed by Samuel Adams and Paul Revere; coins, newspapers"},
    {"name": "Norwegian Svalbard Global Seed Vault", "lat": 78.2355, "lon": 15.4917, "city": "Longyearbyen", "country": "Norway", "year_buried": 2008, "open_date": "Ongoing", "notes": "Not a traditional time capsule but a biological archive; 1.1 million seed samples from every nation"},
    {"name": "Memory of Mankind (Hallstatt Salt Mine)", "lat": 47.5622, "lon": 13.6493, "city": "Hallstatt", "country": "Austria", "year_buried": 2012, "open_date": "Indefinite (1M years)", "notes": "Ceramic tablets archived deep in salt mine; designed to survive for one million years"},
]


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================

def _make_base_map(lat: float = 30.0, lon: float = 0.0, zoom: int = 2) -> folium.Map:
    """Create a dark-themed folium map."""
    return folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )


def _render_map(m: folium.Map, height: int = 500):
    """Render a folium map in Streamlit using st_html."""
    st_html(m._repr_html_(), height=height)


def _csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Provide CSV download button."""
    buf = df.to_csv(index=False).encode("utf-8")
    st.download_button(label, buf, file_name=filename, mime="text/csv")


def _esc(value) -> str:
    """Safely escape a value for HTML popup content."""
    return html_module.escape(str(value))


# =====================================================================
# MODE 1: FAMOUS CLOCK TOWERS
# =====================================================================

def _render_famous_clock_towers():
    """Render the Famous Clock Towers map mode."""
    st.markdown("#### Famous Clock Towers")
    st.markdown(
        "Iconic clock towers from around the world spanning centuries of "
        "timekeeping architecture, from medieval bell towers to modern megatowers."
    )

    data = FAMOUS_CLOCK_TOWERS

    # --- Stats ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Clock Towers", len(data))
    with col2:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)
    with col3:
        avg_h = sum(d["height_m"] for d in data) / len(data)
        st.metric("Avg Height", f"{avg_h:.0f} m")
    with col4:
        oldest = min(data, key=lambda d: d["year"])
        st.metric("Oldest", f"{oldest['year']}", oldest["name"][:20])

    # --- Filters ---
    all_countries = sorted(set(d["country"] for d in data))
    sel = st.multiselect("Filter by Country", all_countries, default=[], key="ct_country")
    filtered = [d for d in data if d["country"] in sel] if sel else data
    st.info(f"Showing {len(filtered)} of {len(data)} clock towers")

    # --- Map ---
    m = _make_base_map(lat=30, lon=10, zoom=2)
    color = MODE_COLORS["Famous Clock Towers"]
    for item in filtered:
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>City:</b> {_esc(item['city'])}<br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Year:</b> {_esc(item['year'])}<br>"
            f"<b>Height:</b> {item['height_m']} m<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Clock Tower Data")
    df = pd.DataFrame(filtered)
    col_order = ["name", "city", "country", "year", "height_m", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "famous_clock_towers.csv")


# =====================================================================
# MODE 2: WATCHMAKING CAPITALS
# =====================================================================

def _render_watchmaking_capitals():
    """Render the Watchmaking Capitals map mode."""
    st.markdown("#### Watchmaking Capitals")
    st.markdown(
        "The cities and regions that shaped the global watchmaking industry, "
        "from the Swiss Jura to Glashutte, Seiko's Tokyo, and beyond."
    )

    data = WATCHMAKING_CAPITALS

    # --- Stats ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Watchmaking Centers", len(data))
    with col2:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)
    with col3:
        oldest = min(data, key=lambda d: d["year_est"])
        st.metric("Oldest Est.", str(oldest["year_est"]), oldest["name"][:20])

    # --- Map ---
    m = _make_base_map(lat=47, lon=7, zoom=4)
    color = MODE_COLORS["Watchmaking Capitals"]
    for item in data:
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Established:</b> {_esc(item['year_est'])}<br>"
            f"<b>Specialty:</b> {_esc(item['specialty'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Watchmaking Data")
    df = pd.DataFrame(data)
    col_order = ["name", "country", "year_est", "specialty", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "watchmaking_capitals.csv")


# =====================================================================
# MODE 3: GREENWICH & TIME ZONES
# =====================================================================

def _render_greenwich_time_zones():
    """Render the Greenwich & Time Zones map mode."""
    st.markdown("#### Greenwich & Time Zones")
    st.markdown(
        "The Prime Meridian, International Date Line, and the world's most unusual "
        "time zones -- from 45-minute offsets to countries that skipped an entire day."
    )

    data = GREENWICH_TIME_ZONES

    # --- Stats ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Locations", len(data))
    with col2:
        types = len(set(d["type"] for d in data))
        st.metric("Zone Types", types)
    with col3:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)

    # --- Map ---
    m = _make_base_map(lat=20, lon=0, zoom=2)
    color = MODE_COLORS["Greenwich & Time Zones"]
    for item in data:
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Type:</b> {_esc(item['type'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Time Zone Locations")
    df = pd.DataFrame(data)
    col_order = ["name", "country", "type", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "greenwich_time_zones.csv")


# =====================================================================
# MODE 4: SUNDIALS & ANCIENT TIMEKEEPING
# =====================================================================

def _render_sundials():
    """Render the Sundials & Ancient Timekeeping map mode."""
    st.markdown("#### Sundials & Ancient Timekeeping")
    st.markdown(
        "From Egyptian obelisk shadow clocks and Roman sundials to monumental "
        "Jantar Mantar instruments and the world's great clepsydrae (water clocks)."
    )

    data = SUNDIALS_ANCIENT

    # --- Stats ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sites", len(data))
    with col2:
        types = len(set(d["type"] for d in data))
        st.metric("Instrument Types", types)
    with col3:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)
    with col4:
        st.metric("Span", "3500+ years")

    # --- Map ---
    m = _make_base_map(lat=30, lon=30, zoom=2)
    color = MODE_COLORS["Sundials & Ancient Timekeeping"]
    for item in data:
        popup_html = (
            f"<div style='min-width:230px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>City:</b> {_esc(item['city'])}<br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Era:</b> {_esc(item['era'])}<br>"
            f"<b>Type:</b> {_esc(item['type'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Sundial & Ancient Timekeeping Data")
    df = pd.DataFrame(data)
    col_order = ["name", "city", "country", "era", "type", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "sundials_ancient_timekeeping.csv")


# =====================================================================
# MODE 5: ATOMIC CLOCK FACILITIES
# =====================================================================

def _render_atomic_clocks():
    """Render the Atomic Clock Facilities map mode."""
    st.markdown("#### Atomic Clock Facilities")
    st.markdown(
        "The laboratories and installations that define the world's most precise "
        "time standards, from NIST cesium fountains to optical lattice clocks."
    )

    data = ATOMIC_CLOCK_FACILITIES

    # --- Stats ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Facilities", len(data))
    with col2:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)
    with col3:
        types = len(set(d["type"] for d in data))
        st.metric("Clock Types", types)

    # --- Map ---
    m = _make_base_map(lat=35, lon=10, zoom=2)
    color = MODE_COLORS["Atomic Clock Facilities"]
    for item in data:
        popup_html = (
            f"<div style='min-width:240px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>City:</b> {_esc(item['city'])}<br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Type:</b> {_esc(item['type'])}<br>"
            f"<b>Accuracy:</b> {_esc(item['accuracy'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=340),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Atomic Clock Facility Data")
    df = pd.DataFrame(data)
    col_order = ["name", "city", "country", "type", "accuracy", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "atomic_clock_facilities.csv")


# =====================================================================
# MODE 6: ASTRONOMICAL OBSERVATORIES
# =====================================================================

def _render_observatories():
    """Render the Astronomical Observatories map mode."""
    st.markdown("#### Astronomical Observatories")
    st.markdown(
        "Historic and modern observatories that have shaped our understanding of "
        "time, the cosmos, and navigation -- from Greenwich to Mauna Kea."
    )

    data = ASTRONOMICAL_OBSERVATORIES

    # --- Stats ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Observatories", len(data))
    with col2:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)
    with col3:
        oldest = min(data, key=lambda d: d["founded"])
        st.metric("Oldest Founded", str(oldest["founded"]), oldest["name"][:20])
    with col4:
        newest = max(data, key=lambda d: d["founded"])
        st.metric("Newest Founded", str(newest["founded"]), newest["name"][:20])

    # --- Map ---
    m = _make_base_map(lat=25, lon=10, zoom=2)
    color = MODE_COLORS["Astronomical Observatories"]
    for item in data:
        popup_html = (
            f"<div style='min-width:230px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>City:</b> {_esc(item['city'])}<br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Founded:</b> {_esc(item['founded'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Observatory Data")
    df = pd.DataFrame(data)
    col_order = ["name", "city", "country", "founded", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "astronomical_observatories.csv")


# =====================================================================
# MODE 7: HOROLOGY MUSEUMS
# =====================================================================

def _render_horology_museums():
    """Render the Horology Museums map mode."""
    st.markdown("#### Horology Museums")
    st.markdown(
        "The world's finest museums dedicated to clocks, watches, and the art of "
        "measuring time -- from La Chaux-de-Fonds to Tokyo's Seiko Museum."
    )

    data = HOROLOGY_MUSEUMS

    # --- Stats ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Museums", len(data))
    with col2:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)
    with col3:
        swiss = sum(1 for d in data if "Switzerland" in d["country"])
        st.metric("In Switzerland", swiss)

    # --- Map ---
    m = _make_base_map(lat=47, lon=5, zoom=3)
    color = MODE_COLORS["Horology Museums"]
    for item in data:
        popup_html = (
            f"<div style='min-width:230px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>City:</b> {_esc(item['city'])}<br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Collection:</b> {_esc(item['collection_size'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Museum Data")
    df = pd.DataFrame(data)
    col_order = ["name", "city", "country", "collection_size", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "horology_museums.csv")


# =====================================================================
# MODE 8: CHURCH & CATHEDRAL CLOCKS
# =====================================================================

def _render_church_clocks():
    """Render the Church & Cathedral Clocks map mode."""
    st.markdown("#### Church & Cathedral Clocks")
    st.markdown(
        "Medieval and Renaissance astronomical clocks in Europe's great cathedrals, "
        "from Salisbury's 1386 mechanism to Strasbourg's 19th-century masterpiece."
    )

    data = CHURCH_CATHEDRAL_CLOCKS

    # --- Stats ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cathedral Clocks", len(data))
    with col2:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)
    with col3:
        oldest = min(data, key=lambda d: d["year"])
        st.metric("Oldest", str(oldest["year"]), oldest["name"][:20])
    with col4:
        astro = sum(1 for d in data if "astronomical" in d["type"].lower())
        st.metric("Astronomical", astro)

    # --- Map ---
    m = _make_base_map(lat=49, lon=5, zoom=4)
    color = MODE_COLORS["Church & Cathedral Clocks"]
    for item in data:
        popup_html = (
            f"<div style='min-width:230px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>City:</b> {_esc(item['city'])}<br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Year:</b> {_esc(item['year'])}<br>"
            f"<b>Type:</b> {_esc(item['type'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Cathedral Clock Data")
    df = pd.DataFrame(data)
    col_order = ["name", "city", "country", "year", "type", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "church_cathedral_clocks.csv")


# =====================================================================
# MODE 9: CUCKOO CLOCK & FOLK CLOCKS
# =====================================================================

def _render_cuckoo_folk_clocks():
    """Render the Cuckoo Clock & Folk Clocks map mode."""
    st.markdown("#### Cuckoo Clock & Folk Clocks")
    st.markdown(
        "The Black Forest's cuckoo clock tradition, Scandinavian Mora clocks, "
        "Dutch tail clocks, and folk clockmaking villages across Europe and Japan."
    )

    data = CUCKOO_FOLK_CLOCKS

    # --- Stats ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Locations", len(data))
    with col2:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)
    with col3:
        german = sum(1 for d in data if d["country"] == "Germany")
        st.metric("In Germany", german)

    # --- Map ---
    m = _make_base_map(lat=48, lon=8, zoom=5)
    color = MODE_COLORS["Cuckoo Clock & Folk Clocks"]
    for item in data:
        popup_html = (
            f"<div style='min-width:220px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>City:</b> {_esc(item['city'])}<br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Type:</b> {_esc(item['type'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Cuckoo & Folk Clock Data")
    df = pd.DataFrame(data)
    col_order = ["name", "city", "country", "type", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "cuckoo_folk_clocks.csv")


# =====================================================================
# MODE 10: TIME CAPSULE LOCATIONS
# =====================================================================

def _render_time_capsules():
    """Render the Time Capsule Locations map mode."""
    st.markdown("#### Time Capsule Locations")
    st.markdown(
        "Sealed messages to the future: from the Westinghouse capsules at the "
        "1939 World's Fair to the Svalbard Seed Vault and Memory of Mankind."
    )

    data = TIME_CAPSULE_LOCATIONS

    # --- Stats ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Time Capsules", len(data))
    with col2:
        countries = len(set(d["country"] for d in data))
        st.metric("Countries", countries)
    with col3:
        oldest = min(data, key=lambda d: d["year_buried"])
        st.metric("Oldest Buried", str(oldest["year_buried"]), oldest["name"][:20])
    with col4:
        us_count = sum(1 for d in data if "USA" in d["country"])
        st.metric("In the USA", us_count)

    # --- Map ---
    m = _make_base_map(lat=35, lon=-30, zoom=2)
    color = MODE_COLORS["Time Capsule Locations"]
    for item in data:
        popup_html = (
            f"<div style='min-width:240px;'>"
            f"<b>{_esc(item['name'])}</b><br>"
            f"<b>City:</b> {_esc(item['city'])}<br>"
            f"<b>Country:</b> {_esc(item['country'])}<br>"
            f"<b>Year Buried:</b> {_esc(item['year_buried'])}<br>"
            f"<b>Open Date:</b> {_esc(item['open_date'])}<br>"
            f"<hr style='margin:4px 0;'>"
            f"<i>{_esc(item['notes'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=340),
            tooltip=_esc(item["name"]),
        ).add_to(m)
    _render_map(m)

    # --- Data Table ---
    st.markdown("##### Time Capsule Data")
    df = pd.DataFrame(data)
    col_order = ["name", "city", "country", "year_buried", "open_date", "lat", "lon", "notes"]
    df = df[[c for c in col_order if c in df.columns]]
    st.dataframe(df, width="stretch")
    _csv_download(df, "time_capsule_locations.csv")


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================

def render_clock_maps_tab():
    """Main entry point for the Clocks & Timekeeping Maps tab."""
    st.markdown(
        '<div class="tab-header cyan">'
        '<h4>\U0001f570\ufe0f Clocks &amp; Timekeeping Maps</h4>'
        '<p>World clocks, observatories, and timekeeping history</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    map_mode = st.selectbox("Map Mode", MAP_MODES, key="clock_maps_mode")

    st.markdown("---")

    if map_mode == "Famous Clock Towers":
        _render_famous_clock_towers()
    elif map_mode == "Watchmaking Capitals":
        _render_watchmaking_capitals()
    elif map_mode == "Greenwich & Time Zones":
        _render_greenwich_time_zones()
    elif map_mode == "Sundials & Ancient Timekeeping":
        _render_sundials()
    elif map_mode == "Atomic Clock Facilities":
        _render_atomic_clocks()
    elif map_mode == "Astronomical Observatories":
        _render_observatories()
    elif map_mode == "Horology Museums":
        _render_horology_museums()
    elif map_mode == "Church & Cathedral Clocks":
        _render_church_clocks()
    elif map_mode == "Cuckoo Clock & Folk Clocks":
        _render_cuckoo_folk_clocks()
    elif map_mode == "Time Capsule Locations":
        _render_time_capsules()
