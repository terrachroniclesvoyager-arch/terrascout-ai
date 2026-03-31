# -*- coding: utf-8 -*-
"""
Cryptography, Codes & Mysteries module for TerraScout AI.
Explores the geography of codebreaking, espionage, unsolved ciphers,
intelligence agencies, number stations, submarine cables, treasure hunts,
spy museums, and cryptocurrency mining hubs.
All data is curated -- no API keys required.
"""

import io
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit as st
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# =====================================================================
# THEME CONSTANTS
# =====================================================================
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT_CYAN = "#06b6d4"
ACCENT_AMBER = "#f59e0b"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_EMERALD = "#10b981"
ACCENT_RED = "#ef4444"
ACCENT_PINK = "#ec4899"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"

MAP_MODES = [
    "1. Enigma & WW2 Codebreaking",
    "2. Cold War Espionage",
    "3. Ancient Codes & Ciphers",
    "4. NSA & Intelligence HQs",
    "5. Famous Unsolved Codes",
    "6. Submarine Cable Tapping",
    "7. Number Stations",
    "8. Treasure Maps & Hidden Codes",
    "9. Spy Museums & Monuments",
    "10. Cryptocurrency Mining Hubs",
]

# =====================================================================
# MODE 1 -- ENIGMA & WW2 CODEBREAKING
# =====================================================================
ENIGMA_DATA = [
    {"name": "Bletchley Park", "lat": 51.9977, "lon": -0.7407, "country": "UK",
     "type": "Codebreaking HQ",
     "desc": "Home of the Government Code & Cypher School; Alan Turing and team broke Enigma here.",
     "year": "1939-1945", "color": ACCENT_CYAN},
    {"name": "Station X - Hut 8", "lat": 51.9983, "lon": -0.7395, "country": "UK",
     "type": "Naval Enigma",
     "desc": "Hut 8 focused on breaking German naval Enigma codes under Turing and Hugh Alexander.",
     "year": "1939-1945", "color": ACCENT_CYAN},
    {"name": "Enigma Factory - Heimsoeth & Rinke, Berlin", "lat": 52.5200, "lon": 13.4050,
     "country": "Germany", "type": "Enigma Manufacturing",
     "desc": "Primary manufacturer of Enigma machines for the German military.",
     "year": "1920s-1945", "color": ACCENT_RED},
    {"name": "Polish Cipher Bureau, Warsaw", "lat": 52.2297, "lon": 21.0122,
     "country": "Poland", "type": "Codebreaking Pioneer",
     "desc": "Marian Rejewski, Jerzy Rozycki & Henryk Zygalski first broke Enigma in 1932.",
     "year": "1932-1939", "color": ACCENT_VIOLET},
    {"name": "Pyry Forest Meeting Site", "lat": 52.0833, "lon": 21.0667,
     "country": "Poland", "type": "Intelligence Handover",
     "desc": "Polish cryptanalysts shared Enigma secrets with British & French allies in July 1939.",
     "year": "1939", "color": ACCENT_VIOLET},
    {"name": "Arlington Hall, Virginia", "lat": 38.8635, "lon": -77.0964,
     "country": "USA", "type": "Signals Intelligence",
     "desc": "US Army Signal Intelligence Service; broke Japanese PURPLE cipher.",
     "year": "1942-1945", "color": ACCENT_BLUE},
    {"name": "OP-20-G, Washington DC", "lat": 38.8863, "lon": -77.0365,
     "country": "USA", "type": "Naval Codebreaking",
     "desc": "US Navy cryptanalysis unit that broke JN-25, enabling the Battle of Midway victory.",
     "year": "1922-1946", "color": ACCENT_BLUE},
    {"name": "Navajo Code Talkers Training, Camp Pendleton", "lat": 33.3052, "lon": -117.3542,
     "country": "USA", "type": "Unbreakable Code",
     "desc": "Navajo Marines trained here to use their language as an unbreakable military code.",
     "year": "1942-1945", "color": ACCENT_EMERALD},
    {"name": "Iwo Jima (Navajo Code in Action)", "lat": 24.7580, "lon": 141.2917,
     "country": "Japan", "type": "Code Talker Deployment",
     "desc": "Navajo Code Talkers transmitted over 800 messages without error during the battle.",
     "year": "1945", "color": ACCENT_EMERALD},
    {"name": "Lorenz Cipher Intercept, Knockholt", "lat": 51.3150, "lon": 0.0900,
     "country": "UK", "type": "Y Station Intercept",
     "desc": "Intercepted Lorenz SZ40/42 teleprinter cipher traffic (Hitler's strategic comms).",
     "year": "1941-1945", "color": ACCENT_AMBER},
    {"name": "Colossus Computer, Dollis Hill", "lat": 51.5640, "lon": -0.2320,
     "country": "UK", "type": "First Electronic Computer",
     "desc": "Tommy Flowers designed Colossus here; the world's first programmable electronic computer.",
     "year": "1943", "color": ACCENT_AMBER},
    {"name": "Beaumanor Hall, Leicestershire", "lat": 52.7466, "lon": -1.2910,
     "country": "UK", "type": "War Office Y Group",
     "desc": "Major radio intercept station; fed raw intercepts to Bletchley Park for decryption.",
     "year": "1939-1945", "color": ACCENT_CYAN},
    {"name": "Gustave Bertrand's PC Bruno, Gretz-Armainvilliers", "lat": 48.7419, "lon": 2.7297,
     "country": "France", "type": "Allied Codebreaking",
     "desc": "French intelligence ran Polish-French codebreaking team that continued Enigma work.",
     "year": "1939-1940", "color": ACCENT_PINK},
    {"name": "FRUMEL, Melbourne", "lat": -37.8136, "lon": 144.9631,
     "country": "Australia", "type": "Signals Intelligence",
     "desc": "Fleet Radio Unit Melbourne; Allied codebreaking centre for the Pacific War.",
     "year": "1942-1945", "color": ACCENT_ORANGE},
    {"name": "Central Bureau, Brisbane", "lat": -27.4698, "lon": 153.0251,
     "country": "Australia", "type": "Signals Intelligence",
     "desc": "Joint Allied SIGINT bureau decrypting Japanese army and air force communications.",
     "year": "1942-1945", "color": ACCENT_ORANGE},
]

# =====================================================================
# MODE 2 -- COLD WAR ESPIONAGE
# =====================================================================
COLD_WAR_DATA = [
    {"name": "CIA Headquarters, Langley", "lat": 38.9510, "lon": -77.1464,
     "country": "USA", "type": "Intelligence HQ",
     "desc": "Central Intelligence Agency HQ since 1961; nerve centre of Western espionage.",
     "color": ACCENT_BLUE},
    {"name": "KGB Headquarters, Lubyanka", "lat": 55.7602, "lon": 37.6276,
     "country": "Russia", "type": "Intelligence HQ",
     "desc": "KGB/FSB headquarters; feared prison and interrogation centre during the Cold War.",
     "color": ACCENT_RED},
    {"name": "Glienicke Bridge (Bridge of Spies)", "lat": 52.4131, "lon": 13.0903,
     "country": "Germany", "type": "Spy Exchange",
     "desc": "Bridge between East and West Berlin used for exchanging captured spies, including Rudolf Abel and Francis Gary Powers.",
     "color": ACCENT_AMBER},
    {"name": "Berlin Spy Tunnel (Operation Gold)", "lat": 52.4373, "lon": 13.5098,
     "country": "Germany", "type": "Intelligence Operation",
     "desc": "CIA/MI6 tunnel tapping Soviet telephone lines in East Berlin, 1953-1956.",
     "color": ACCENT_AMBER},
    {"name": "Checkpoint Charlie, Berlin", "lat": 52.5075, "lon": 13.3904,
     "country": "Germany", "type": "Cold War Crossing",
     "desc": "Famous crossing point between East and West Berlin; spy and defector route.",
     "color": ACCENT_AMBER},
    {"name": "Cambridge Five Recruitment, Trinity College", "lat": 52.2073, "lon": 0.1168,
     "country": "UK", "type": "Spy Recruitment",
     "desc": "Where Kim Philby, Donald Maclean, Guy Burgess, Anthony Blunt, and John Cairncross were recruited as Soviet agents.",
     "color": ACCENT_VIOLET},
    {"name": "MI6 HQ (SIS Building), London", "lat": 51.4875, "lon": -0.1245,
     "country": "UK", "type": "Intelligence HQ",
     "desc": "Secret Intelligence Service headquarters at Vauxhall Cross since 1994.",
     "color": ACCENT_CYAN},
    {"name": "Dead Drop: Oleg Penkovsky, Moscow", "lat": 55.7558, "lon": 37.6173,
     "country": "Russia", "type": "Dead Drop",
     "desc": "Colonel Penkovsky used dead drops in Moscow to pass Soviet nuclear secrets to MI6/CIA.",
     "color": ACCENT_RED},
    {"name": "Aldrich Ames Dead Drop, Georgetown", "lat": 38.9076, "lon": -77.0723,
     "country": "USA", "type": "Dead Drop",
     "desc": "CIA officer Aldrich Ames used dead drops in Georgetown to pass secrets to the KGB.",
     "color": ACCENT_BLUE},
    {"name": "Vienna Spy Hub (Hotel Imperial)", "lat": 48.2010, "lon": 16.3728,
     "country": "Austria", "type": "Espionage Hub",
     "desc": "Neutral Vienna was the espionage capital of the Cold War; all major agencies operated here.",
     "color": ACCENT_ORANGE},
    {"name": "Teufelsberg Listening Station, Berlin", "lat": 52.4971, "lon": 13.2417,
     "country": "Germany", "type": "Signals Intelligence",
     "desc": "NSA/GCHQ listening station atop rubble hill; intercepted Eastern Bloc communications.",
     "color": ACCENT_CYAN},
    {"name": "Stasi HQ (Normannenstrasse), East Berlin", "lat": 52.5133, "lon": 13.4872,
     "country": "Germany", "type": "Intelligence HQ",
     "desc": "Ministry for State Security (Stasi) headquarters; one of the most pervasive spy agencies ever.",
     "color": ACCENT_RED},
    {"name": "U-2 Incident Site, Sverdlovsk", "lat": 56.8389, "lon": 60.6057,
     "country": "Russia", "type": "Espionage Incident",
     "desc": "Gary Powers' CIA U-2 spy plane was shot down near Sverdlovsk (Yekaterinburg) in 1960.",
     "color": ACCENT_RED},
    {"name": "Venona Project, Fort Meade", "lat": 39.1087, "lon": -76.7714,
     "country": "USA", "type": "Signals Intelligence",
     "desc": "VENONA project decrypted Soviet espionage communications, exposing hundreds of spies.",
     "color": ACCENT_BLUE},
    {"name": "Havana Station (Havana Syndrome)", "lat": 23.1136, "lon": -82.3666,
     "country": "Cuba", "type": "Anomalous Event",
     "desc": "US Embassy in Havana where mysterious 'Havana Syndrome' was first reported in 2016.",
     "color": ACCENT_PINK},
]

# =====================================================================
# MODE 3 -- ANCIENT CODES & CIPHERS
# =====================================================================
ANCIENT_CODES_DATA = [
    {"name": "Rosetta Stone Discovery, Rashid", "lat": 31.4048, "lon": 30.4175,
     "country": "Egypt", "type": "Decipherment Key",
     "desc": "Found in 1799; allowed Champollion to decode Egyptian hieroglyphs in 1822.",
     "year": "196 BC", "color": ACCENT_AMBER},
    {"name": "Voynich Manuscript Origin (Estimated: Italy)", "lat": 45.4408, "lon": 12.3155,
     "country": "Italy", "type": "Unsolved Manuscript",
     "desc": "Written in an unknown script with strange illustrations; never decoded. Possibly 15th century Italian.",
     "year": "c. 1404-1438", "color": ACCENT_VIOLET},
    {"name": "Beinecke Library (Voynich Location)", "lat": 41.3111, "lon": -72.9267,
     "country": "USA", "type": "Manuscript Archive",
     "desc": "Voynich Manuscript is currently housed at Yale's Beinecke Rare Book Library.",
     "year": "Present", "color": ACCENT_VIOLET},
    {"name": "Phaistos Disc Discovery, Crete", "lat": 35.0512, "lon": 24.8156,
     "country": "Greece", "type": "Unsolved Script",
     "desc": "Clay disc with 242 tokens of 45 distinct signs; undeciphered Minoan artifact.",
     "year": "c. 1700 BC", "color": ACCENT_EMERALD},
    {"name": "Linear A Tablets, Knossos", "lat": 35.2979, "lon": 25.1630,
     "country": "Greece", "type": "Unsolved Script",
     "desc": "Minoan writing system used across Crete; still undeciphered unlike Linear B.",
     "year": "c. 1800-1450 BC", "color": ACCENT_EMERALD},
    {"name": "Linear B Decipherment, London", "lat": 51.5194, "lon": -0.1270,
     "country": "UK", "type": "Decipherment",
     "desc": "Michael Ventris deciphered Linear B as an early form of Greek in 1952.",
     "year": "1952", "color": ACCENT_CYAN},
    {"name": "Behistun Inscription, Iran", "lat": 34.3892, "lon": 47.4361,
     "country": "Iran", "type": "Decipherment Key",
     "desc": "Trilingual cuneiform inscription; key to deciphering Mesopotamian writing systems.",
     "year": "c. 522 BC", "color": ACCENT_AMBER},
    {"name": "Dead Sea Scrolls, Qumran", "lat": 31.7414, "lon": 35.4594,
     "country": "Israel/Palestine", "type": "Coded Texts",
     "desc": "Copper Scroll contains coded directions to hidden Temple treasure; partly decoded.",
     "year": "c. 150 BC - 70 AD", "color": ACCENT_ORANGE},
    {"name": "Caesar Cipher Origin, Rome", "lat": 41.8933, "lon": 12.4829,
     "country": "Italy", "type": "Classical Cipher",
     "desc": "Julius Caesar used substitution ciphers for military communications -- the first known cipher.",
     "year": "c. 58 BC", "color": ACCENT_RED},
    {"name": "Al-Kindi's Frequency Analysis, Baghdad", "lat": 33.3152, "lon": 44.3661,
     "country": "Iraq", "type": "Cryptanalysis Origin",
     "desc": "Al-Kindi invented frequency analysis c. 850 AD -- the fundamental technique for breaking ciphers.",
     "year": "c. 850 AD", "color": ACCENT_PINK},
    {"name": "Alberti Cipher Disk, Vatican City", "lat": 41.9029, "lon": 12.4534,
     "country": "Vatican", "type": "Polyalphabetic Cipher",
     "desc": "Leon Battista Alberti created the first polyalphabetic cipher device around 1467.",
     "year": "c. 1467", "color": ACCENT_ORANGE},
    {"name": "Indus Valley Script, Mohenjo-daro", "lat": 27.3290, "lon": 68.1385,
     "country": "Pakistan", "type": "Unsolved Script",
     "desc": "Over 400 symbols on seals from the Indus Valley civilisation; still undeciphered.",
     "year": "c. 2600-1900 BC", "color": ACCENT_EMERALD},
    {"name": "Rongorongo Tablets, Easter Island", "lat": -27.1127, "lon": -109.3497,
     "country": "Chile", "type": "Unsolved Script",
     "desc": "Mysterious glyphs carved on wooden tablets; possibly the only writing invented in Oceania.",
     "year": "Pre-1860s", "color": ACCENT_PINK},
    {"name": "Proto-Elamite Tablets, Susa", "lat": 32.1876, "lon": 48.2529,
     "country": "Iran", "type": "Unsolved Script",
     "desc": "Oldest undeciphered writing system; roughly 1,600 tablets from ancient Susa.",
     "year": "c. 3100-2900 BC", "color": ACCENT_AMBER},
    {"name": "Vigenere Cipher, Paris", "lat": 48.8566, "lon": 2.3522,
     "country": "France", "type": "Polyalphabetic Cipher",
     "desc": "Blaise de Vigenere published his 'unbreakable' cipher in 1586; broken by Babbage/Kasiski.",
     "year": "1586", "color": ACCENT_BLUE},
]

# =====================================================================
# MODE 4 -- NSA & INTELLIGENCE HQs
# =====================================================================
INTEL_HQ_DATA = [
    {"name": "NSA - Fort Meade", "lat": 39.1087, "lon": -76.7714,
     "country": "USA", "type": "SIGINT", "alliance": "Five Eyes",
     "desc": "National Security Agency; world's largest signals intelligence organisation.",
     "color": ACCENT_BLUE},
    {"name": "GCHQ - Cheltenham (The Doughnut)", "lat": 51.8985, "lon": -2.1238,
     "country": "UK", "type": "SIGINT", "alliance": "Five Eyes",
     "desc": "Government Communications HQ; UK signals intelligence and cyber security centre.",
     "color": ACCENT_CYAN},
    {"name": "CSE - Ottawa", "lat": 45.3459, "lon": -75.7675,
     "country": "Canada", "type": "SIGINT", "alliance": "Five Eyes",
     "desc": "Communications Security Establishment; Canada's signals intelligence agency.",
     "color": ACCENT_RED},
    {"name": "ASD - Canberra", "lat": -35.3106, "lon": 149.1253,
     "country": "Australia", "type": "SIGINT", "alliance": "Five Eyes",
     "desc": "Australian Signals Directorate; part of the Five Eyes alliance.",
     "color": ACCENT_EMERALD},
    {"name": "GCSB - Wellington", "lat": -41.2865, "lon": 174.7762,
     "country": "New Zealand", "type": "SIGINT", "alliance": "Five Eyes",
     "desc": "Government Communications Security Bureau; New Zealand's SIGINT agency.",
     "color": ACCENT_EMERALD},
    {"name": "BND - Berlin (New HQ)", "lat": 52.5163, "lon": 13.3629,
     "country": "Germany", "type": "Foreign Intelligence",
     "alliance": "European",
     "desc": "Bundesnachrichtendienst; Germany's foreign intelligence service relocated to Berlin in 2019.",
     "color": ACCENT_AMBER},
    {"name": "DGSE - Paris", "lat": 48.8359, "lon": 2.3878,
     "country": "France", "type": "Foreign Intelligence",
     "alliance": "European",
     "desc": "Direction Generale de la Securite Exterieure; France's external intelligence agency.",
     "color": ACCENT_BLUE},
    {"name": "Mossad - Tel Aviv (Estimated)", "lat": 32.0879, "lon": 34.7866,
     "country": "Israel", "type": "Foreign Intelligence",
     "alliance": "Independent",
     "desc": "Institute for Intelligence and Special Operations; one of the world's most effective agencies.",
     "color": ACCENT_ORANGE},
    {"name": "SVR / GRU - Moscow", "lat": 55.5812, "lon": 37.5183,
     "country": "Russia", "type": "Foreign Intelligence",
     "alliance": "CSTO",
     "desc": "Foreign Intelligence Service at Yasenevo; successor to the KGB's First Chief Directorate.",
     "color": ACCENT_RED},
    {"name": "MSS - Beijing", "lat": 39.9042, "lon": 116.4074,
     "country": "China", "type": "Intelligence/Security",
     "alliance": "Independent",
     "desc": "Ministry of State Security; China's main intelligence and security agency.",
     "color": ACCENT_RED},
    {"name": "RAW - New Delhi", "lat": 28.5900, "lon": 77.1800,
     "country": "India", "type": "Foreign Intelligence",
     "alliance": "Independent",
     "desc": "Research and Analysis Wing; India's external intelligence agency formed in 1968.",
     "color": ACCENT_ORANGE},
    {"name": "Pine Gap (Joint Defence Facility)", "lat": -23.7991, "lon": 133.7370,
     "country": "Australia", "type": "Satellite Surveillance",
     "alliance": "Five Eyes",
     "desc": "US-Australian satellite ground station; critical for missile early warning and SIGINT.",
     "color": ACCENT_EMERALD},
    {"name": "NSA Utah Data Center", "lat": 40.3216, "lon": -111.9309,
     "country": "USA", "type": "Data Storage",
     "alliance": "Five Eyes",
     "desc": "Massive data centre for intelligence community storage and processing; opened 2014.",
     "color": ACCENT_BLUE},
    {"name": "RAF Menwith Hill, Yorkshire", "lat": 54.0155, "lon": -1.6895,
     "country": "UK", "type": "SIGINT Station",
     "alliance": "Five Eyes",
     "desc": "NSA/GCHQ facility; largest electronic monitoring station outside the USA.",
     "color": ACCENT_CYAN},
    {"name": "ASIS HQ - Canberra", "lat": -35.3075, "lon": 149.1244,
     "country": "Australia", "type": "Foreign Intelligence",
     "alliance": "Five Eyes",
     "desc": "Australian Secret Intelligence Service; Australia's overseas human intelligence agency.",
     "color": ACCENT_EMERALD},
    {"name": "NIS - Seoul", "lat": 37.4749, "lon": 127.0390,
     "country": "South Korea", "type": "Intelligence",
     "alliance": "Independent",
     "desc": "National Intelligence Service; handles espionage, counterintelligence, and North Korea affairs.",
     "color": ACCENT_VIOLET},
]

# =====================================================================
# MODE 5 -- FAMOUS UNSOLVED CODES
# =====================================================================
UNSOLVED_CODES_DATA = [
    {"name": "Kryptos Sculpture, CIA HQ", "lat": 38.9518, "lon": -77.1460,
     "country": "USA", "type": "Encrypted Sculpture",
     "desc": "Jim Sanborn's copper sculpture; 4 panels, 3 solved, 4th panel remains uncracked since 1990.",
     "year": "1990", "color": ACCENT_CYAN},
    {"name": "Zodiac Killer Z340 Cipher, San Francisco", "lat": 37.7749, "lon": -122.4194,
     "country": "USA", "type": "Serial Killer Cipher",
     "desc": "Z340 cipher cracked in 2020 after 51 years. Z13 and Z32 remain unsolved.",
     "year": "1969", "color": ACCENT_RED},
    {"name": "Beale Ciphers, Bedford County VA", "lat": 37.3343, "lon": -79.5232,
     "country": "USA", "type": "Treasure Cipher",
     "desc": "Three ciphertexts allegedly pointing to a buried treasure. Only Cipher #2 has been solved.",
     "year": "1885 (published)", "color": ACCENT_AMBER},
    {"name": "Dorabella Cipher, Wolverhampton", "lat": 52.5863, "lon": -2.1282,
     "country": "UK", "type": "Personal Cipher",
     "desc": "87-character cipher sent by composer Edward Elgar to Dora Penny in 1897; never decoded.",
     "year": "1897", "color": ACCENT_VIOLET},
    {"name": "Shugborough Inscription, Staffordshire", "lat": 52.8012, "lon": -1.9995,
     "country": "UK", "type": "Monument Cipher",
     "desc": "Eight letters O U O S V A V V on the Shepherd's Monument; linked to Holy Grail legends.",
     "year": "c. 1748-1763", "color": ACCENT_AMBER},
    {"name": "Tamam Shud (Somerton Man), Adelaide", "lat": -34.9788, "lon": 138.5330,
     "country": "Australia", "type": "Mystery Death + Code",
     "desc": "Unidentified man found dead with a coded message; identified via DNA as Carl Webb in 2022.",
     "year": "1948", "color": ACCENT_ORANGE},
    {"name": "D'Agapeyeff Cipher (Challenge)", "lat": 51.5074, "lon": -0.1278,
     "country": "UK", "type": "Book Cipher",
     "desc": "Published in 1939 as a challenge; author admitted he forgot his own method of encipherment.",
     "year": "1939", "color": ACCENT_PINK},
    {"name": "Chaocipher Artifacts, National Cryptologic Museum", "lat": 39.1076, "lon": -76.7734,
     "country": "USA", "type": "Mechanical Cipher",
     "desc": "John Byrne's Chaocipher (1918); algorithm finally revealed publicly in 2010.",
     "year": "1918", "color": ACCENT_BLUE},
    {"name": "Ricky McCormick Notes, St Louis", "lat": 38.6270, "lon": -90.1994,
     "country": "USA", "type": "Encrypted Notes",
     "desc": "Encrypted notes found on murder victim in 1999; the FBI lists these as top unsolved codes.",
     "year": "1999", "color": ACCENT_RED},
    {"name": "Blitz Ciphers, London", "lat": 51.5074, "lon": -0.1278,
     "country": "UK", "type": "Carrier Pigeon Cipher",
     "desc": "Coded WW2 message found on a carrier pigeon skeleton in a chimney in 2012; still unsolved.",
     "year": "c. 1944", "color": ACCENT_AMBER},
    {"name": "Chinese Gold Bar Ciphers", "lat": 29.5630, "lon": 106.5516,
     "country": "China", "type": "Gold Bar Cipher",
     "desc": "Seven gold bars with encrypted messages; possibly certificates for a massive gold deposit.",
     "year": "1933", "color": ACCENT_AMBER},
    {"name": "Copiale Cipher Origin (Germany)", "lat": 52.5200, "lon": 13.4050,
     "country": "Germany", "type": "Secret Society Cipher",
     "desc": "105-page enciphered manuscript of the Oculist secret society; decoded in 2011.",
     "year": "c. 1760-1780", "color": ACCENT_VIOLET},
]

# =====================================================================
# MODE 6 -- SUBMARINE CABLE TAPPING
# =====================================================================
CABLE_TAP_DATA = [
    {"name": "Operation Ivy Bells, Sea of Okhotsk", "lat": 53.0000, "lon": 148.0000,
     "country": "Russia/USA", "type": "Undersea Cable Tap",
     "desc": "US Navy divers tapped Soviet submarine communication cables using USS Halibut (1971-1981).",
     "year": "1971-1981", "color": ACCENT_BLUE},
    {"name": "USS Jimmy Carter (Cable Tap Sub)", "lat": 47.7376, "lon": -122.7287,
     "country": "USA", "type": "Submarine",
     "desc": "Modified Seawolf-class submarine widely believed to conduct cable-tapping operations.",
     "year": "2005-present", "color": ACCENT_BLUE},
    {"name": "GCHQ Bude (TEMPORA)", "lat": 50.8341, "lon": -4.5492,
     "country": "UK", "type": "Cable Intercept Station",
     "desc": "GCHQ station tapping transatlantic fibre-optic cables under the TEMPORA programme.",
     "year": "2011-present", "color": ACCENT_CYAN},
    {"name": "Cornwall Cable Landing, Bude", "lat": 50.8303, "lon": -4.5547,
     "country": "UK", "type": "Cable Landing Point",
     "desc": "Multiple transatlantic cables land here: TAT-14, Apollo, others. Near GCHQ station.",
     "year": "Various", "color": ACCENT_CYAN},
    {"name": "Djibouti Cable Hub", "lat": 11.5880, "lon": 43.1457,
     "country": "Djibouti", "type": "Strategic Cable Hub",
     "desc": "15+ submarine cables pass through Djibouti; strategic chokepoint with US, Chinese, and French bases.",
     "year": "Ongoing", "color": ACCENT_ORANGE},
    {"name": "Fujairah Cable Landing, UAE", "lat": 25.1224, "lon": 56.3440,
     "country": "UAE", "type": "Cable Landing Point",
     "desc": "One of the world's busiest cable landing points; connects Europe-Asia traffic.",
     "year": "Ongoing", "color": ACCENT_ORANGE},
    {"name": "Marseille Cable Landing, France", "lat": 43.2965, "lon": 5.3698,
     "country": "France", "type": "Cable Landing Point",
     "desc": "Major European cable hub connecting to Africa, Middle East, and Asia via the Mediterranean.",
     "year": "Ongoing", "color": ACCENT_BLUE},
    {"name": "Singapore Cable Hub", "lat": 1.3521, "lon": 103.8198,
     "country": "Singapore", "type": "Strategic Cable Hub",
     "desc": "Major Asian cable hub; virtually all Asia-Europe traffic passes through here.",
     "year": "Ongoing", "color": ACCENT_EMERALD},
    {"name": "NSA San Antonio TAO Center", "lat": 29.4241, "lon": -98.4936,
     "country": "USA", "type": "Hacking Unit",
     "desc": "NSA Tailored Access Operations; implants firmware in routers and taps network traffic.",
     "year": "2000s-present", "color": ACCENT_BLUE},
    {"name": "Tong Fuk Cable Landing, Hong Kong", "lat": 22.2167, "lon": 113.9333,
     "country": "Hong Kong", "type": "Cable Landing Point",
     "desc": "Multiple trans-Pacific cables land here; key node for Asia-Pacific internet traffic.",
     "year": "Ongoing", "color": ACCENT_RED},
    {"name": "Fortaleza Cable Landing, Brazil", "lat": -3.7172, "lon": -38.5433,
     "country": "Brazil", "type": "Cable Landing Point",
     "desc": "Landing for EllaLink (direct Europe-South America) and SACS (South Atlantic) cables.",
     "year": "2021", "color": ACCENT_EMERALD},
    {"name": "Svalbard SVALSAT & Cable", "lat": 78.2297, "lon": 15.3975,
     "country": "Norway", "type": "Strategic Cable + Satellite",
     "desc": "Arctic satellite ground station connected by undersea cable; cables sabotaged in 2022.",
     "year": "2004-present", "color": ACCENT_VIOLET},
]

# =====================================================================
# MODE 7 -- NUMBER STATIONS
# =====================================================================
NUMBER_STATIONS_DATA = [
    {"name": "UVB-76 (The Buzzer), Pskov Region", "lat": 57.8136, "lon": 28.3496,
     "country": "Russia", "type": "Continuous Buzzer",
     "desc": "Shortwave station on 4625 kHz buzzing since 1982; occasional voice messages. Purpose debated.",
     "freq": "4625 kHz", "color": ACCENT_RED},
    {"name": "The Lincolnshire Poacher, Cyprus", "lat": 34.6105, "lon": 33.0104,
     "country": "Cyprus/UK", "type": "MI6 Station",
     "desc": "British number station broadcasting from RAF Akrotiri; played folk tune then numbers until 2008.",
     "freq": "Various HF", "color": ACCENT_CYAN},
    {"name": "Cherry Ripe (Australian Station), Shoal Bay", "lat": -12.3667, "lon": 130.9500,
     "country": "Australia", "type": "Intelligence Station",
     "desc": "Similar to Lincolnshire Poacher; played 'Cherry Ripe' folk tune. Attributed to Australian DSD.",
     "freq": "Various HF", "color": ACCENT_EMERALD},
    {"name": "Atencion! (Cuban Numbers), Havana Area", "lat": 22.9068, "lon": -82.2580,
     "country": "Cuba", "type": "Cuban Intelligence",
     "desc": "Spanish-language numbers station linked to Cuban Direccion de Inteligencia.",
     "freq": "Various HF", "color": ACCENT_ORANGE},
    {"name": "Yosemite Sam, Albuquerque NM", "lat": 35.0844, "lon": -106.6504,
     "country": "USA", "type": "Mysterious Broadcast",
     "desc": "Repeated a Yosemite Sam audio clip and data burst from 2004-2014; purpose unknown.",
     "freq": "1.710 MHz", "color": ACCENT_BLUE},
    {"name": "Pip / The Pip (S30), Rostov-on-Don", "lat": 47.2357, "lon": 39.7015,
     "country": "Russia", "type": "Russian Military",
     "desc": "Continuous pip sound on 3756 kHz with occasional coded messages; partner to The Buzzer.",
     "freq": "3756 kHz", "color": ACCENT_RED},
    {"name": "Swedish Rhapsody (E11), Poland/Germany",
     "lat": 51.1079, "lon": 17.0385,
     "country": "Poland/Germany", "type": "Stasi Station",
     "desc": "Used a child's voice reciting numbers over 'Swedish Rhapsody' music box tune. East German Stasi.",
     "freq": "Various HF", "color": ACCENT_VIOLET},
    {"name": "Warrenton Training Center, Virginia", "lat": 38.7318, "lon": -77.7953,
     "country": "USA", "type": "CIA Communications",
     "desc": "CIA facility believed to be one source of US-originated number station transmissions.",
     "freq": "Various HF", "color": ACCENT_BLUE},
    {"name": "HM01 (The Chinese Robot), Beijing Area", "lat": 39.7500, "lon": 116.5000,
     "country": "China", "type": "Chinese Military",
     "desc": "Chinese number station with synthesized female voice reading numbers in Mandarin.",
     "freq": "Various HF", "color": ACCENT_RED},
    {"name": "V02a (Ready? Ready!), Moscow Area", "lat": 55.9500, "lon": 37.7000,
     "country": "Russia", "type": "Russian Intelligence",
     "desc": "Russian-language station beginning with 'Gotovy? Gotovy!' (Ready? Ready!). Still active.",
     "freq": "Various HF", "color": ACCENT_RED},
    {"name": "E10 (Mossad Station), Negev Desert", "lat": 30.8500, "lon": 34.7500,
     "country": "Israel", "type": "Mossad",
     "desc": "Phonetic alphabet numbers station attributed to Israeli Mossad intelligence.",
     "freq": "Various HF", "color": ACCENT_ORANGE},
    {"name": "S06 (Russian Female Station), Kerch", "lat": 45.3500, "lon": 36.4700,
     "country": "Russia", "type": "Russian Military",
     "desc": "Russian female voice number station broadcasting from Crimea region.",
     "freq": "Various HF", "color": ACCENT_RED},
]

# =====================================================================
# MODE 8 -- TREASURE MAPS & HIDDEN CODES
# =====================================================================
TREASURE_DATA = [
    {"name": "Oak Island Money Pit, Nova Scotia", "lat": 44.5134, "lon": -64.2988,
     "country": "Canada", "type": "Treasure Legend",
     "desc": "Mysterious shaft discovered 1795; 200+ years of excavation. Linked to Knights Templar, pirates, and Shakespeare manuscripts.",
     "estimated_value": "$2 million+", "color": ACCENT_AMBER},
    {"name": "Treasure of Lima, Cocos Island", "lat": 5.5272, "lon": -87.0567,
     "country": "Costa Rica", "type": "Pirate Treasure",
     "desc": "Gold and silver plundered from Lima in 1820 by Captain William Thompson; never recovered.",
     "estimated_value": "$200 million+", "color": ACCENT_AMBER},
    {"name": "Amber Room (Last Known: Konigsberg)", "lat": 54.7104, "lon": 20.4522,
     "country": "Russia (Kaliningrad)", "type": "Lost Art Treasure",
     "desc": "Chamber of amber panels gifted to Peter the Great; looted by Nazis in 1941; vanished.",
     "estimated_value": "$500 million+", "color": ACCENT_ORANGE},
    {"name": "Fenn's Treasure, Yellowstone Area", "lat": 44.7260, "lon": -110.6758,
     "country": "USA", "type": "Hidden Treasure",
     "desc": "Forrest Fenn hid a chest of gold in the Rockies in 2010; found by Jack Stuef in 2020 near Yellowstone.",
     "estimated_value": "$2 million", "color": ACCENT_EMERALD},
    {"name": "Knights Templar Treasury, Temple Mount", "lat": 31.7767, "lon": 35.2345,
     "country": "Israel/Palestine", "type": "Legendary Treasure",
     "desc": "Templar wealth was never fully recovered after their dissolution in 1312. Theories link it to Rosslyn Chapel, Rennes-le-Chateau.",
     "estimated_value": "Incalculable", "color": ACCENT_VIOLET},
    {"name": "Rennes-le-Chateau, France", "lat": 42.9261, "lon": 2.2617,
     "country": "France", "type": "Mystery Treasure",
     "desc": "Pere Sauniere allegedly found treasure; inspiration for Holy Blood/Holy Grail and The Da Vinci Code.",
     "estimated_value": "Unknown", "color": ACCENT_VIOLET},
    {"name": "El Dorado (Lake Guatavita)", "lat": 5.0200, "lon": -73.7700,
     "country": "Colombia", "type": "Golden Legend",
     "desc": "Muisca chieftains coated in gold dust, threw treasures into the lake. Drainage attempts partially successful.",
     "estimated_value": "$300 million+", "color": ACCENT_AMBER},
    {"name": "San Jose Galleon Wreck, Cartagena", "lat": 10.2913, "lon": -75.9304,
     "country": "Colombia", "type": "Shipwreck Treasure",
     "desc": "Spanish galleon sunk 1708 with gold, silver, emeralds. Found 2015; legal battle ongoing.",
     "estimated_value": "$17 billion", "color": ACCENT_AMBER},
    {"name": "Yamashita's Gold, Philippines", "lat": 16.4023, "lon": 120.5960,
     "country": "Philippines", "type": "War Loot",
     "desc": "Japanese General Yamashita allegedly buried vast WW2 plunder across the Philippines.",
     "estimated_value": "Unknown - billions?", "color": ACCENT_RED},
    {"name": "Flor de la Mar Wreck, Strait of Malacca", "lat": 2.5000, "lon": 103.5000,
     "country": "Malaysia/Indonesia", "type": "Shipwreck Treasure",
     "desc": "Portuguese carrack sank 1511 with Malaccan royal treasure. One of the richest wrecks ever.",
     "estimated_value": "$2.6 billion+", "color": ACCENT_ORANGE},
    {"name": "Rosslyn Chapel, Scotland", "lat": 55.8554, "lon": -3.1602,
     "country": "UK", "type": "Coded Architecture",
     "desc": "Medieval chapel with 213 carved 'music cubes' forming a melody; linked to Templar and Masonic secrets.",
     "estimated_value": "N/A", "color": ACCENT_CYAN},
    {"name": "Copper Scroll Treasure Sites, Judean Desert", "lat": 31.7600, "lon": 35.4600,
     "country": "Israel/Palestine", "type": "Ancient Treasure Map",
     "desc": "Dead Sea Scroll listing 64 locations of hidden gold and silver; 4,630 talents total.",
     "estimated_value": "$1 billion+", "color": ACCENT_ORANGE},
]

# =====================================================================
# MODE 9 -- SPY MUSEUMS & MONUMENTS
# =====================================================================
SPY_MUSEUMS_DATA = [
    {"name": "International Spy Museum, Washington DC", "lat": 38.8831, "lon": -77.0231,
     "country": "USA", "type": "Museum",
     "desc": "World's largest collection of espionage artifacts; interactive spy experiences.",
     "color": ACCENT_BLUE},
    {"name": "National Cryptologic Museum, Fort Meade", "lat": 39.1076, "lon": -76.7734,
     "country": "USA", "type": "Museum",
     "desc": "NSA museum with Enigma machines, supercomputers, and cryptologic history.",
     "color": ACCENT_BLUE},
    {"name": "Bletchley Park Museum, UK", "lat": 51.9977, "lon": -0.7407,
     "country": "UK", "type": "Heritage Site/Museum",
     "desc": "Preserved WW2 codebreaking centre; home to the Alan Turing exhibition.",
     "color": ACCENT_CYAN},
    {"name": "KGB Museum, Prague", "lat": 50.0874, "lon": 14.4213,
     "country": "Czech Republic", "type": "Museum",
     "desc": "Private museum with KGB espionage equipment, execution devices, and spy cameras.",
     "color": ACCENT_RED},
    {"name": "Stasi Museum (Normannenstrasse), Berlin", "lat": 52.5133, "lon": 13.4872,
     "country": "Germany", "type": "Museum",
     "desc": "Original Stasi headquarters; Erich Mielke's office preserved intact.",
     "color": ACCENT_RED},
    {"name": "German Spy Museum, Berlin", "lat": 52.5095, "lon": 13.3810,
     "country": "Germany", "type": "Museum",
     "desc": "Interactive museum at Potsdamer Platz covering espionage from ancient times to cyber warfare.",
     "color": ACCENT_AMBER},
    {"name": "Checkpoint Charlie Museum, Berlin", "lat": 52.5075, "lon": 13.3904,
     "country": "Germany", "type": "Museum",
     "desc": "Documents escape attempts and espionage at the Berlin Wall crossing point.",
     "color": ACCENT_AMBER},
    {"name": "Berlin-Hohenschoenhausen Memorial", "lat": 52.5528, "lon": 13.5000,
     "country": "Germany", "type": "Memorial",
     "desc": "Former Stasi remand prison; tours by former inmates reveal interrogation techniques.",
     "color": ACCENT_RED},
    {"name": "Spy Museum, Tampere Finland", "lat": 61.4978, "lon": 23.7610,
     "country": "Finland", "type": "Museum",
     "desc": "Covers Finnish intelligence history and Cold War espionage on the Soviet border.",
     "color": ACCENT_VIOLET},
    {"name": "CIA Museum (Classified), Langley", "lat": 38.9510, "lon": -77.1464,
     "country": "USA", "type": "Classified Museum",
     "desc": "Inside CIA HQ; not open to public. Contains spy gadgets, disguises, and covert tech.",
     "color": ACCENT_BLUE},
    {"name": "Enigma Cipher Centre, Poznan", "lat": 52.4064, "lon": 16.9252,
     "country": "Poland", "type": "Museum",
     "desc": "Dedicated to the Polish cryptanalysts who first broke the Enigma code in 1932.",
     "color": ACCENT_VIOLET},
    {"name": "Cold War Museum, Lorton VA", "lat": 38.7190, "lon": -77.2264,
     "country": "USA", "type": "Museum",
     "desc": "Housed in former Nike missile base; Cold War artifacts and spy history.",
     "color": ACCENT_BLUE},
    {"name": "Alan Turing Memorial, Manchester", "lat": 53.4760, "lon": -2.2360,
     "country": "UK", "type": "Monument",
     "desc": "Bronze statue of Turing holding an apple in Sackville Park; a tribute to the father of computing.",
     "color": ACCENT_CYAN},
    {"name": "Monument to Codebreakers, Bletchley", "lat": 51.9979, "lon": -0.7400,
     "country": "UK", "type": "Monument",
     "desc": "Memorial commemorating the 12,000+ staff who worked at Bletchley Park during WW2.",
     "color": ACCENT_CYAN},
    {"name": "NSA National Vigilance Park, Fort Meade", "lat": 39.1070, "lon": -76.7720,
     "country": "USA", "type": "Memorial",
     "desc": "Outdoor memorial with reconnaissance aircraft honouring those killed in SIGINT missions.",
     "color": ACCENT_BLUE},
]

# =====================================================================
# MODE 10 -- CRYPTOCURRENCY MINING HUBS
# =====================================================================
CRYPTO_MINING_DATA = [
    {"name": "Rockdale, Texas (Riot Platforms)", "lat": 30.6566, "lon": -97.0072,
     "country": "USA", "type": "Bitcoin Mining Farm",
     "desc": "One of the largest Bitcoin mining facilities in North America; ~750 MW capacity.",
     "energy": "Grid (ERCOT)", "color": ACCENT_AMBER},
    {"name": "Keflavik, Iceland (Genesis Mining)", "lat": 63.9975, "lon": -22.5608,
     "country": "Iceland", "type": "Bitcoin Mining Farm",
     "desc": "Geothermal and hydroelectric powered mining in naturally cool climate.",
     "energy": "Geothermal/Hydro", "color": ACCENT_EMERALD},
    {"name": "Bratsk, Siberia (BitRiver)", "lat": 56.1325, "lon": 101.6140,
     "country": "Russia", "type": "Bitcoin Mining Farm",
     "desc": "Colocation mining facility powered by cheap Siberian hydroelectricity.",
     "energy": "Hydroelectric", "color": ACCENT_RED},
    {"name": "Sichuan Province Hub, China", "lat": 30.5728, "lon": 104.0668,
     "country": "China", "type": "Former Mining Hub",
     "desc": "Was the world's largest mining region until China banned crypto mining in 2021.",
     "energy": "Hydro (seasonal)", "color": ACCENT_RED},
    {"name": "Inner Mongolia Mining Hub, Ordos", "lat": 39.6088, "lon": 109.7812,
     "country": "China", "type": "Former Mining Hub",
     "desc": "Massive coal-powered mining farms; shut down after China's 2021 crypto mining ban.",
     "energy": "Coal", "color": ACCENT_RED},
    {"name": "El Salvador Bitcoin City (Planned)", "lat": 13.4484, "lon": -87.9259,
     "country": "El Salvador", "type": "Volcanic Mining",
     "desc": "President Bukele's plan for a Bitcoin-mining city powered by Conchagua volcano geothermal.",
     "energy": "Geothermal (planned)", "color": ACCENT_ORANGE},
    {"name": "Massena, New York (Coinmint)", "lat": 44.9281, "lon": -74.8913,
     "country": "USA", "type": "Bitcoin Mining Farm",
     "desc": "Former Alcoa aluminium smelter converted to crypto mine; cheap St. Lawrence River hydro.",
     "energy": "Hydroelectric", "color": ACCENT_BLUE},
    {"name": "Norrbotten, Sweden (Hive Blockchain)", "lat": 65.5848, "lon": 22.1547,
     "country": "Sweden", "type": "Bitcoin Mining Farm",
     "desc": "Arctic mining operation using green energy and natural cooling.",
     "energy": "Hydro/Wind", "color": ACCENT_EMERALD},
    {"name": "Kazakhstan Mining Hub, Ekibastuz", "lat": 51.7234, "lon": 75.3221,
     "country": "Kazakhstan", "type": "Mining Hub",
     "desc": "Became world's #2 mining country after China ban; coal-powered, later restricted.",
     "energy": "Coal", "color": ACCENT_ORANGE},
    {"name": "Paraguay (Bitfarms), Villarrica", "lat": -25.7536, "lon": -56.4434,
     "country": "Paraguay", "type": "Bitcoin Mining Farm",
     "desc": "Powered by cheap Itaipu Dam hydroelectricity; one of the cheapest energy sources globally.",
     "energy": "Hydroelectric", "color": ACCENT_EMERALD},
    {"name": "Bhutan Royal Bitcoin Mine, Thimphu", "lat": 27.4728, "lon": 89.6393,
     "country": "Bhutan", "type": "State Mining",
     "desc": "Bhutan's government secretly mined Bitcoin using hydroelectric power since at least 2019.",
     "energy": "Hydroelectric", "color": ACCENT_VIOLET},
    {"name": "Abu Dhabi (Marathon Digital)", "lat": 24.4539, "lon": 54.3773,
     "country": "UAE", "type": "Bitcoin Mining Farm",
     "desc": "250 MW immersion-cooled mining facility; part of Abu Dhabi's diversification strategy.",
     "energy": "Natural Gas", "color": ACCENT_ORANGE},
    {"name": "Binance HQ (Registered), Malta/Dubai", "lat": 25.2048, "lon": 55.2708,
     "country": "UAE", "type": "Crypto Exchange",
     "desc": "World's largest cryptocurrency exchange by trading volume.",
     "energy": "N/A (Exchange)", "color": ACCENT_AMBER},
    {"name": "Coinbase HQ, San Francisco", "lat": 37.7749, "lon": -122.4194,
     "country": "USA", "type": "Crypto Exchange",
     "desc": "First major crypto exchange to IPO (Nasdaq, 2021); largest US-based exchange.",
     "energy": "N/A (Exchange)", "color": ACCENT_BLUE},
]


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
def _build_folium_map(data: list, center: list = None, zoom: int = 3,
                      popup_fields: list = None, extra_fields_fn=None) -> folium.Map:
    """Build a dark-themed folium map with circle markers from a data list."""
    if not center:
        avg_lat = sum(d["lat"] for d in data) / len(data)
        avg_lon = sum(d["lon"] for d in data) / len(data)
        center = [avg_lat, avg_lon]

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )

    for item in data:
        name_safe = escape(str(item.get("name", "")))
        desc_safe = escape(str(item.get("desc", "")))
        type_safe = escape(str(item.get("type", "")))
        country_safe = escape(str(item.get("country", "")))

        popup_parts = [
            f"<div style='min-width:220px;max-width:320px;font-family:sans-serif;"
            f"background:#1a2235;color:#e8ecf4;padding:10px;border-radius:8px;"
            f"border:1px solid #2a3550;'>",
            f"<b style='color:#06b6d4;font-size:13px;'>{name_safe}</b><br>",
            f"<span style='color:#f59e0b;font-size:11px;'>{type_safe}</span><br>",
            f"<span style='color:#8b97b0;font-size:11px;'>{country_safe}</span><br>",
            f"<hr style='border-color:#2a3550;margin:4px 0;'>",
            f"<span style='color:#e8ecf4;font-size:11px;'>{desc_safe}</span>",
        ]

        # Add extra fields if provided
        if popup_fields:
            for field in popup_fields:
                if field in item and item[field]:
                    val_safe = escape(str(item[field]))
                    label = field.replace("_", " ").title()
                    popup_parts.append(
                        f"<br><span style='color:#5a6580;font-size:10px;'>"
                        f"{label}: </span><span style='color:#8b97b0;font-size:10px;'>"
                        f"{val_safe}</span>"
                    )

        if extra_fields_fn:
            popup_parts.append(extra_fields_fn(item))

        popup_parts.append("</div>")
        popup_html = "".join(popup_parts)

        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=item.get("color", ACCENT_CYAN),
            fill=True,
            fill_color=item.get("color", ACCENT_CYAN),
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=name_safe,
        ).add_to(m)

    return m


def _render_map(m: folium.Map, height: int = 500):
    """Render a folium map via components.html."""
    components.html(m._repr_html_(), height=height)


def _data_to_df(data: list, columns: list = None) -> pd.DataFrame:
    """Convert data list to a cleaned DataFrame."""
    df = pd.DataFrame(data)
    if columns:
        available = [c for c in columns if c in df.columns]
        df = df[available]
    return df


def _csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Offer a CSV download button."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label=label,
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
    )


def _stats_row(data: list, stat_definitions: list):
    """Display a row of metrics from stat definitions.
    stat_definitions: list of (label, value) tuples.
    """
    cols = st.columns(len(stat_definitions))
    for col, (label, value) in zip(cols, stat_definitions):
        col.metric(label, value)


def _make_bar_chart(labels: list, values: list, title: str,
                    xlabel: str = "", ylabel: str = "",
                    color: str = ACCENT_CYAN, horizontal: bool = True):
    """Create a dark-themed matplotlib bar chart and display it."""
    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.45)))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)

    if horizontal:
        bars = ax.barh(labels, values, color=color, edgecolor=color, alpha=0.8)
        ax.set_xlabel(xlabel, color=TEXT_PRIMARY, fontsize=10)
        ax.set_ylabel(ylabel, color=TEXT_PRIMARY, fontsize=10)
        ax.invert_yaxis()
    else:
        bars = ax.bar(labels, values, color=color, edgecolor=color, alpha=0.8)
        ax.set_xlabel(xlabel, color=TEXT_PRIMARY, fontsize=10)
        ax.set_ylabel(ylabel, color=TEXT_PRIMARY, fontsize=10)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(title, color=TEXT_PRIMARY, fontsize=12, pad=10)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x" if horizontal else "y", color="#2a3550", alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# =====================================================================
# MODE RENDER FUNCTIONS
# =====================================================================
def _render_enigma():
    """Mode 1: Enigma & WW2 Codebreaking."""
    st.markdown("#### Enigma & WW2 Codebreaking")
    st.markdown(
        "Explore the locations that shaped the greatest codebreaking effort in history. "
        "From Polish mathematicians who first cracked Enigma to the Navajo Code Talkers "
        "whose language became an unbreakable cipher in the Pacific theater."
    )

    # Stats
    countries = set(d["country"] for d in ENIGMA_DATA)
    types = set(d["type"] for d in ENIGMA_DATA)
    _stats_row(ENIGMA_DATA, [
        ("Sites", len(ENIGMA_DATA)),
        ("Countries", len(countries)),
        ("Categories", len(types)),
        ("Era", "1920s-1945"),
    ])

    # Map
    m = _build_folium_map(ENIGMA_DATA, center=[48.0, 10.0], zoom=3,
                          popup_fields=["year"])
    _render_map(m)

    # Chart: sites by country
    country_counts = {}
    for d in ENIGMA_DATA:
        country_counts[d["country"]] = country_counts.get(d["country"], 0) + 1
    sorted_cc = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    _make_bar_chart(
        [c[0] for c in sorted_cc],
        [c[1] for c in sorted_cc],
        "WW2 Codebreaking Sites by Country",
        xlabel="Number of Sites",
        color=ACCENT_CYAN,
    )

    # Table
    df = _data_to_df(ENIGMA_DATA, ["name", "country", "type", "year", "desc"])
    st.dataframe(df, width="stretch")

    # Download
    _csv_download(df, "enigma_ww2_codebreaking.csv",
                  "Download Enigma & WW2 Data CSV")


def _render_cold_war():
    """Mode 2: Cold War Espionage."""
    st.markdown("#### Cold War Espionage")
    st.markdown(
        "The shadow war between East and West played out across dead drops, "
        "spy tunnels, and bridge exchanges. From the Cambridge Five to Aldrich Ames, "
        "these are the locations where the Cold War's secret battles were fought."
    )

    countries = set(d["country"] for d in COLD_WAR_DATA)
    types = set(d["type"] for d in COLD_WAR_DATA)
    _stats_row(COLD_WAR_DATA, [
        ("Sites", len(COLD_WAR_DATA)),
        ("Countries", len(countries)),
        ("Categories", len(types)),
        ("Era", "1945-1991+"),
    ])

    m = _build_folium_map(COLD_WAR_DATA, center=[48.0, 10.0], zoom=3)
    _render_map(m)

    # Chart by type
    type_counts = {}
    for d in COLD_WAR_DATA:
        type_counts[d["type"]] = type_counts.get(d["type"], 0) + 1
    sorted_tc = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    _make_bar_chart(
        [t[0] for t in sorted_tc],
        [t[1] for t in sorted_tc],
        "Cold War Sites by Type",
        xlabel="Count",
        color=ACCENT_RED,
    )

    df = _data_to_df(COLD_WAR_DATA, ["name", "country", "type", "desc"])
    st.dataframe(df, width="stretch")
    _csv_download(df, "cold_war_espionage.csv", "Download Cold War Data CSV")


def _render_ancient_codes():
    """Mode 3: Ancient Codes & Ciphers."""
    st.markdown("#### Ancient Codes & Ciphers")
    st.markdown(
        "From the Rosetta Stone to the Voynich Manuscript, humanity has always written "
        "in codes. Some have been cracked; others remain stubbornly resistant after millennia. "
        "This map traces the world's most significant ciphers and undeciphered scripts."
    )

    solved = sum(1 for d in ANCIENT_CODES_DATA
                 if any(kw in d["type"].lower() for kw in ["decipherment", "classical", "polyalphabetic"]))
    unsolved = sum(1 for d in ANCIENT_CODES_DATA if "unsolved" in d["type"].lower())
    _stats_row(ANCIENT_CODES_DATA, [
        ("Sites", len(ANCIENT_CODES_DATA)),
        ("Solved", solved),
        ("Unsolved", unsolved),
        ("Span", "3100 BC - Present"),
    ])

    m = _build_folium_map(ANCIENT_CODES_DATA, center=[30.0, 30.0], zoom=3,
                          popup_fields=["year"])
    _render_map(m)

    # Chart by type
    type_counts = {}
    for d in ANCIENT_CODES_DATA:
        type_counts[d["type"]] = type_counts.get(d["type"], 0) + 1
    sorted_tc = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    _make_bar_chart(
        [t[0] for t in sorted_tc],
        [t[1] for t in sorted_tc],
        "Ancient Codes by Category",
        xlabel="Count",
        color=ACCENT_VIOLET,
    )

    df = _data_to_df(ANCIENT_CODES_DATA, ["name", "country", "type", "year", "desc"])
    st.dataframe(df, width="stretch")
    _csv_download(df, "ancient_codes_ciphers.csv", "Download Ancient Codes CSV")


def _render_intel_hqs():
    """Mode 4: NSA & Intelligence HQs."""
    st.markdown("#### NSA & Intelligence Headquarters")
    st.markdown(
        "The world's major signals intelligence agencies and their headquarters. "
        "From the Five Eyes alliance to independent services like Mossad and MSS, "
        "these are the nerve centres of global surveillance and intelligence gathering."
    )

    alliances = set(d.get("alliance", "Unknown") for d in INTEL_HQ_DATA)
    five_eyes = sum(1 for d in INTEL_HQ_DATA if d.get("alliance") == "Five Eyes")
    _stats_row(INTEL_HQ_DATA, [
        ("Agencies", len(INTEL_HQ_DATA)),
        ("Five Eyes", five_eyes),
        ("Alliances", len(alliances)),
        ("Countries", len(set(d["country"] for d in INTEL_HQ_DATA))),
    ])

    m = _build_folium_map(INTEL_HQ_DATA, center=[30.0, 20.0], zoom=2,
                          popup_fields=["alliance"])
    _render_map(m)

    # Chart by alliance
    alliance_counts = {}
    for d in INTEL_HQ_DATA:
        a = d.get("alliance", "Unknown")
        alliance_counts[a] = alliance_counts.get(a, 0) + 1
    sorted_ac = sorted(alliance_counts.items(), key=lambda x: x[1], reverse=True)
    _make_bar_chart(
        [a[0] for a in sorted_ac],
        [a[1] for a in sorted_ac],
        "Intelligence Agencies by Alliance",
        xlabel="Count",
        color=ACCENT_BLUE,
    )

    df = _data_to_df(INTEL_HQ_DATA,
                     ["name", "country", "type", "alliance", "desc"])
    st.dataframe(df, width="stretch")
    _csv_download(df, "intelligence_headquarters.csv",
                  "Download Intelligence HQs CSV")


def _render_unsolved_codes():
    """Mode 5: Famous Unsolved Codes."""
    st.markdown("#### Famous Unsolved Codes")
    st.markdown(
        "From the Kryptos sculpture at CIA headquarters to the Zodiac Killer's ciphers, "
        "these are the world's most famous codes that have defied cryptanalysts for decades. "
        "Some have been partially cracked; others remain completely mysterious."
    )

    countries = set(d["country"] for d in UNSOLVED_CODES_DATA)
    _stats_row(UNSOLVED_CODES_DATA, [
        ("Codes", len(UNSOLVED_CODES_DATA)),
        ("Countries", len(countries)),
        ("Oldest", "c. 1748"),
        ("Newest", "1999"),
    ])

    m = _build_folium_map(UNSOLVED_CODES_DATA, center=[40.0, -20.0], zoom=3,
                          popup_fields=["year"])
    _render_map(m)

    # Chart by country
    country_counts = {}
    for d in UNSOLVED_CODES_DATA:
        country_counts[d["country"]] = country_counts.get(d["country"], 0) + 1
    sorted_cc = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    _make_bar_chart(
        [c[0] for c in sorted_cc],
        [c[1] for c in sorted_cc],
        "Unsolved Codes by Country",
        xlabel="Count",
        color=ACCENT_AMBER,
    )

    df = _data_to_df(UNSOLVED_CODES_DATA,
                     ["name", "country", "type", "year", "desc"])
    st.dataframe(df, width="stretch")
    _csv_download(df, "unsolved_codes.csv", "Download Unsolved Codes CSV")


def _render_cable_tapping():
    """Mode 6: Submarine Cable Tapping."""
    st.markdown("#### Submarine Cable Tapping & Surveillance")
    st.markdown(
        "Over 95% of intercontinental data flows through undersea fibre-optic cables. "
        "From the Cold War's Operation Ivy Bells to GCHQ's TEMPORA programme, "
        "these cables have been prime targets for intelligence agencies worldwide."
    )

    landing_pts = sum(1 for d in CABLE_TAP_DATA
                      if "landing" in d["type"].lower() or "hub" in d["type"].lower())
    tap_ops = sum(1 for d in CABLE_TAP_DATA
                  if "tap" in d["type"].lower() or "intercept" in d["type"].lower())
    _stats_row(CABLE_TAP_DATA, [
        ("Sites", len(CABLE_TAP_DATA)),
        ("Cable Points", landing_pts),
        ("Tap Operations", tap_ops),
        ("Countries", len(set(d["country"] for d in CABLE_TAP_DATA))),
    ])

    # Use wider zoom for global cable network
    m = _build_folium_map(CABLE_TAP_DATA, center=[20.0, 30.0], zoom=2,
                          popup_fields=["year"])

    # Draw approximate cable lines between key hubs
    cable_routes = [
        # Transatlantic
        ([50.83, -4.55], [44.93, -74.89], ACCENT_CYAN),
        # Europe-Asia via Mediterranean
        ([43.30, 5.37], [25.12, 56.34], ACCENT_BLUE),
        # Asia hub connections
        ([25.12, 56.34], [1.35, 103.82], ACCENT_EMERALD),
        # Trans-Pacific
        ([22.22, 113.93], [37.77, -122.42], ACCENT_VIOLET),
        # South Atlantic
        ([-3.72, -38.54], [43.30, 5.37], ACCENT_ORANGE),
    ]
    for start, end, color in cable_routes:
        folium.PolyLine(
            [start, end],
            color=color,
            weight=2,
            opacity=0.5,
            dash_array="8 4",
        ).add_to(m)

    _render_map(m, height=550)

    df = _data_to_df(CABLE_TAP_DATA,
                     ["name", "country", "type", "year", "desc"])
    st.dataframe(df, width="stretch")
    _csv_download(df, "submarine_cable_tapping.csv",
                  "Download Cable Tapping Data CSV")


def _render_number_stations():
    """Mode 7: Number Stations."""
    st.markdown("#### Number Stations & Shortwave Mysteries")
    st.markdown(
        "Number stations are shortwave radio broadcasts of coded messages -- "
        "monotone voices reading strings of numbers, sometimes preceded by eerie music. "
        "Active since the Cold War, many are still broadcasting. Their purpose: "
        "sending one-time pad encrypted orders to intelligence agents in the field."
    )

    russian = sum(1 for d in NUMBER_STATIONS_DATA if "Russia" in d["country"])
    active = sum(1 for d in NUMBER_STATIONS_DATA
                 if any(kw in d.get("desc", "").lower()
                        for kw in ["still active", "present", "since"]))
    _stats_row(NUMBER_STATIONS_DATA, [
        ("Stations", len(NUMBER_STATIONS_DATA)),
        ("Russian", russian),
        ("Countries", len(set(d["country"] for d in NUMBER_STATIONS_DATA))),
        ("Active (est.)", active),
    ])

    m = _build_folium_map(NUMBER_STATIONS_DATA, center=[40.0, 20.0], zoom=3,
                          popup_fields=["freq"])
    _render_map(m)

    # Chart by country
    country_counts = {}
    for d in NUMBER_STATIONS_DATA:
        country_counts[d["country"]] = country_counts.get(d["country"], 0) + 1
    sorted_cc = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    _make_bar_chart(
        [c[0] for c in sorted_cc],
        [c[1] for c in sorted_cc],
        "Number Stations by Country/Region",
        xlabel="Count",
        color=ACCENT_RED,
    )

    df = _data_to_df(NUMBER_STATIONS_DATA,
                     ["name", "country", "type", "freq", "desc"])
    st.dataframe(df, width="stretch")
    _csv_download(df, "number_stations.csv", "Download Number Stations CSV")


def _render_treasure():
    """Mode 8: Treasure Maps & Hidden Codes."""
    st.markdown("#### Treasure Maps & Hidden Codes")
    st.markdown(
        "Lost treasure, coded maps, and legendary hoards. From the Oak Island Money Pit "
        "to the $17 billion San Jose galleon, these are the world's greatest treasure "
        "mysteries -- some solved, most still waiting to be found."
    )

    found = sum(1 for d in TREASURE_DATA
                if any(kw in d.get("desc", "").lower()
                       for kw in ["found", "recovered", "successful"]))
    _stats_row(TREASURE_DATA, [
        ("Treasures", len(TREASURE_DATA)),
        ("Found/Partial", found),
        ("Still Lost", len(TREASURE_DATA) - found),
        ("Countries", len(set(d["country"] for d in TREASURE_DATA))),
    ])

    m = _build_folium_map(TREASURE_DATA, center=[20.0, 0.0], zoom=2,
                          popup_fields=["estimated_value"])
    _render_map(m)

    # Chart by estimated value (simple bar based on available values)
    value_labels = []
    for d in TREASURE_DATA:
        val = d.get("estimated_value", "Unknown")
        value_labels.append({"name": d["name"][:30], "value": val})

    _make_bar_chart(
        [d["name"] for d in TREASURE_DATA],
        list(range(len(TREASURE_DATA), 0, -1)),  # rank order
        "Treasure Sites (Ranked by Notoriety)",
        xlabel="Notoriety Rank",
        color=ACCENT_AMBER,
    )

    df = _data_to_df(TREASURE_DATA,
                     ["name", "country", "type", "estimated_value", "desc"])
    st.dataframe(df, width="stretch")
    _csv_download(df, "treasure_maps_hidden_codes.csv",
                  "Download Treasure Data CSV")


def _render_spy_museums():
    """Mode 9: Spy Museums & Monuments."""
    st.markdown("#### Spy Museums & Monuments")
    st.markdown(
        "Visit the world's spy museums, Cold War memorials, and monuments to codebreakers. "
        "From the International Spy Museum in Washington DC to the Stasi Prison Memorial "
        "in Berlin, these sites preserve the hidden history of espionage."
    )

    museums = sum(1 for d in SPY_MUSEUMS_DATA if "museum" in d["type"].lower())
    memorials = sum(1 for d in SPY_MUSEUMS_DATA
                    if "memorial" in d["type"].lower() or "monument" in d["type"].lower())
    _stats_row(SPY_MUSEUMS_DATA, [
        ("Sites", len(SPY_MUSEUMS_DATA)),
        ("Museums", museums),
        ("Memorials", memorials),
        ("Countries", len(set(d["country"] for d in SPY_MUSEUMS_DATA))),
    ])

    m = _build_folium_map(SPY_MUSEUMS_DATA, center=[48.0, -10.0], zoom=3)
    _render_map(m)

    # Chart by country
    country_counts = {}
    for d in SPY_MUSEUMS_DATA:
        country_counts[d["country"]] = country_counts.get(d["country"], 0) + 1
    sorted_cc = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    _make_bar_chart(
        [c[0] for c in sorted_cc],
        [c[1] for c in sorted_cc],
        "Spy Museums & Monuments by Country",
        xlabel="Count",
        color=ACCENT_VIOLET,
    )

    df = _data_to_df(SPY_MUSEUMS_DATA, ["name", "country", "type", "desc"])
    st.dataframe(df, width="stretch")
    _csv_download(df, "spy_museums_monuments.csv",
                  "Download Spy Museums CSV")


def _render_crypto_mining():
    """Mode 10: Cryptocurrency Mining Hubs."""
    st.markdown("#### Cryptocurrency Mining Hubs & Exchanges")
    st.markdown(
        "The geography of cryptocurrency mining is shaped by cheap electricity, "
        "cold climates, and regulatory environments. After China's 2021 ban, "
        "mining shifted to the USA, Kazakhstan, Russia, and green-energy countries "
        "like Iceland, Sweden, and Paraguay."
    )

    green = sum(1 for d in CRYPTO_MINING_DATA
                if any(kw in d.get("energy", "").lower()
                       for kw in ["hydro", "geothermal", "wind", "green"]))
    fossil = sum(1 for d in CRYPTO_MINING_DATA
                 if any(kw in d.get("energy", "").lower()
                        for kw in ["coal", "gas", "grid"]))
    exchanges = sum(1 for d in CRYPTO_MINING_DATA
                    if "exchange" in d["type"].lower())
    _stats_row(CRYPTO_MINING_DATA, [
        ("Sites", len(CRYPTO_MINING_DATA)),
        ("Green Energy", green),
        ("Fossil Fuel", fossil),
        ("Exchanges", exchanges),
    ])

    m = _build_folium_map(CRYPTO_MINING_DATA, center=[30.0, 20.0], zoom=2,
                          popup_fields=["energy"])
    _render_map(m)

    # Chart by energy source
    energy_counts = {}
    for d in CRYPTO_MINING_DATA:
        e = d.get("energy", "Unknown")
        energy_counts[e] = energy_counts.get(e, 0) + 1
    sorted_ec = sorted(energy_counts.items(), key=lambda x: x[1], reverse=True)
    _make_bar_chart(
        [e[0] for e in sorted_ec],
        [e[1] for e in sorted_ec],
        "Mining Sites by Energy Source",
        xlabel="Count",
        color=ACCENT_EMERALD,
    )

    df = _data_to_df(CRYPTO_MINING_DATA,
                     ["name", "country", "type", "energy", "desc"])
    st.dataframe(df, width="stretch")
    _csv_download(df, "crypto_mining_hubs.csv",
                  "Download Crypto Mining CSV")


# =====================================================================
# MAIN TAB RENDER FUNCTION
# =====================================================================
def render_crypto_maps_tab():
    """Main render function for the Cryptography, Codes & Mysteries tab."""

    # ── Tab Header ──
    st.markdown(
        '<div class="tab-header amber">'
        '<h4>\U0001f510 Cryptography, Codes & Mysteries</h4>'
        '<p>Enigma, cipher history, unsolved codes, spy networks & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode Selector ──
    st.markdown("#### Select Map Mode")
    mode = st.selectbox(
        "Choose a topic to explore",
        MAP_MODES,
        key="crypto_map_mode",
    )

    st.markdown("---")

    # ── Dispatch to mode renderer ──
    mode_index = MAP_MODES.index(mode)

    if mode_index == 0:
        _render_enigma()
    elif mode_index == 1:
        _render_cold_war()
    elif mode_index == 2:
        _render_ancient_codes()
    elif mode_index == 3:
        _render_intel_hqs()
    elif mode_index == 4:
        _render_unsolved_codes()
    elif mode_index == 5:
        _render_cable_tapping()
    elif mode_index == 6:
        _render_number_stations()
    elif mode_index == 7:
        _render_treasure()
    elif mode_index == 8:
        _render_spy_museums()
    elif mode_index == 9:
        _render_crypto_mining()
