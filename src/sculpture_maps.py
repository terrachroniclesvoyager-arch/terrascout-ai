# -*- coding: utf-8 -*-
"""
TerraScout AI - Sculpture & Statues Maps Module
Explore the world's tallest statues, sculpture parks, classical masterpieces,
and monumental art across 10 curated map modes.

10 Map Modes:
  1. World's Tallest Statues
  2. Classical Greek & Roman Sculptures
  3. Renaissance Masterpieces
  4. Modern Sculpture Parks
  5. Ancient Megalithic Monuments
  6. Buddhist & Hindu Monumental Art
  7. Public Art & Urban Sculptures
  8. Stone Carving Traditions
  9. Ice & Sand Sculpture Festivals
 10. Famous Equestrian Statues
"""

import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module
import pandas as pd

# ============================================================================
# CONSTANTS
# ============================================================================

_MODE_LIST = [
    "World's Tallest Statues",
    "Classical Greek & Roman Sculptures",
    "Renaissance Masterpieces",
    "Modern Sculpture Parks",
    "Ancient Megalithic Monuments",
    "Buddhist & Hindu Monumental Art",
    "Public Art & Urban Sculptures",
    "Stone Carving Traditions",
    "Ice & Sand Sculpture Festivals",
    "Famous Equestrian Statues",
]

_MODE_DESCRIPTIONS = {
    "World's Tallest Statues": (
        "The planet's most colossal statues -- towering monuments of faith, "
        "nationalism, and artistic ambition. From the Statue of Unity in India "
        "at 182 m to the towering Spring Temple Buddha and the Statue of Liberty."
    ),
    "Classical Greek & Roman Sculptures": (
        "Masterworks of antiquity: the Venus de Milo, Winged Victory, Laocoon, "
        "and other marble and bronze sculptures that defined Western aesthetics "
        "and continue to inspire artists thousands of years later."
    ),
    "Renaissance Masterpieces": (
        "The pinnacle of figurative sculpture from Michelangelo's David to "
        "Bernini's ecstatic saints. Explore the locations where Renaissance "
        "and Baroque masterpieces reside in churches, piazzas, and galleries."
    ),
    "Modern Sculpture Parks": (
        "Open-air museums and sculpture gardens featuring works by Calder, "
        "Moore, Bourgeois, Serra, and other modern and contemporary masters. "
        "Where art meets landscape on a monumental scale."
    ),
    "Ancient Megalithic Monuments": (
        "Prehistoric stone structures that have endured millennia: Stonehenge, "
        "Carnac, Gobekli Tepe, Easter Island moai, and dolmens from Korea to "
        "Ireland. Humanity's earliest monumental sculpture."
    ),
    "Buddhist & Hindu Monumental Art": (
        "Monumental religious sculpture across Asia: the Buddhas of Bamiyan "
        "(destroyed), Leshan Giant Buddha, Angkor Wat reliefs, Ellora cave "
        "temples, and the great bronze Buddhas of Japan and Thailand."
    ),
    "Public Art & Urban Sculptures": (
        "Iconic sculptures that define city skylines and public spaces: the "
        "Bean in Chicago, Manneken Pis in Brussels, the Little Mermaid in "
        "Copenhagen, and LOVE sculptures around the world."
    ),
    "Stone Carving Traditions": (
        "Living traditions of stone carving from Maori tikis to Balinese "
        "temple guardians, Inuit inukshuks, and the intricate jali screens "
        "of Mughal India. Craft as cultural identity."
    ),
    "Ice & Sand Sculpture Festivals": (
        "Ephemeral art at its grandest: the Harbin Ice Festival, Sapporo Snow "
        "Festival, sand sculpture championships, and temporary installations "
        "that draw millions before melting away."
    ),
    "Famous Equestrian Statues": (
        "Riders immortalized in bronze and stone: Marcus Aurelius in Rome, "
        "the Bronze Horseman in St. Petersburg, Joan of Arc in Paris, and "
        "generals and kings on horseback across Europe and the Americas."
    ),
}

_MODE_COLORS = {
    "World's Tallest Statues": "#06b6d4",
    "Classical Greek & Roman Sculptures": "#d97706",
    "Renaissance Masterpieces": "#8b5cf6",
    "Modern Sculpture Parks": "#10b981",
    "Ancient Megalithic Monuments": "#78716c",
    "Buddhist & Hindu Monumental Art": "#f59e0b",
    "Public Art & Urban Sculptures": "#ec4899",
    "Stone Carving Traditions": "#a3785f",
    "Ice & Sand Sculpture Festivals": "#38bdf8",
    "Famous Equestrian Statues": "#ef4444",
}

_MODE_ICONS = {
    "World's Tallest Statues": "\U0001f5fd",
    "Classical Greek & Roman Sculptures": "\U0001f3db\ufe0f",
    "Renaissance Masterpieces": "\U0001f3a8",
    "Modern Sculpture Parks": "\U0001f333",
    "Ancient Megalithic Monuments": "\U0001faaa",
    "Buddhist & Hindu Monumental Art": "\U0001f6d5",
    "Public Art & Urban Sculptures": "\U0001f5ff",
    "Stone Carving Traditions": "\u2692\ufe0f",
    "Ice & Sand Sculpture Festivals": "\u2744\ufe0f",
    "Famous Equestrian Statues": "\U0001f40e",
}


# ============================================================================
# DATA LOADERS -- each returns a list of dicts
# ============================================================================

def _worlds_tallest_statues():
    return [
        {"name": "Statue of Unity", "lat": 21.8380, "lon": 73.7191, "country": "India", "height_m": 182, "subject": "Sardar Vallabhbhai Patel", "year": 2018, "material": "Bronze cladding, steel frame", "notes": "Tallest statue in the world"},
        {"name": "Spring Temple Buddha", "lat": 33.7753, "lon": 112.4514, "country": "China", "height_m": 153, "subject": "Vairocana Buddha", "year": 2008, "material": "Copper, steel", "notes": "Stands on a 25 m lotus throne"},
        {"name": "Laykyun Sekkya", "lat": 21.2833, "lon": 95.1667, "country": "Myanmar", "height_m": 116, "subject": "Gautama Buddha", "year": 2008, "material": "Concrete, gold paint", "notes": "Standing Buddha, reclining Buddha at base"},
        {"name": "Ushiku Daibutsu", "lat": 36.0000, "lon": 140.2167, "country": "Japan", "height_m": 110, "subject": "Amitabha Buddha", "year": 1993, "material": "Bronze", "notes": "Was tallest statue 1993-2008"},
        {"name": "Sendai Daikannon", "lat": 38.2886, "lon": 140.8564, "country": "Japan", "height_m": 100, "subject": "Kannon (Guanyin)", "year": 1991, "material": "Concrete", "notes": "White goddess of mercy statue"},
        {"name": "Guanyin of the South Sea", "lat": 18.2972, "lon": 109.2050, "country": "China", "height_m": 108, "subject": "Guanyin Bodhisattva", "year": 2005, "material": "Gold, white jade", "notes": "Three-faced Guanyin on Hainan Island"},
        {"name": "Statue of Liberty", "lat": 40.6892, "lon": -74.0445, "country": "United States", "height_m": 93, "subject": "Libertas / Freedom", "year": 1886, "material": "Copper, iron", "notes": "Iconic gift from France, UNESCO site"},
        {"name": "The Motherland Calls", "lat": 48.7423, "lon": 44.5370, "country": "Russia", "height_m": 85, "subject": "Mother Russia / WWII victory", "year": 1967, "material": "Concrete, steel", "notes": "Volgograd (Stalingrad), tallest statue in Europe"},
        {"name": "Christ the Redeemer", "lat": -22.9519, "lon": -43.2105, "country": "Brazil", "height_m": 38, "subject": "Jesus Christ", "year": 1931, "material": "Reinforced concrete, soapstone", "notes": "One of the New Seven Wonders of the World"},
        {"name": "African Renaissance Monument", "lat": 14.7225, "lon": -17.4931, "country": "Senegal", "height_m": 49, "subject": "African family/rebirth", "year": 2010, "material": "Bronze, copper", "notes": "Tallest statue in Africa"},
        {"name": "Garuda Wisnu Kencana", "lat": -8.8103, "lon": 115.1675, "country": "Indonesia", "height_m": 121, "subject": "Vishnu riding Garuda", "year": 2018, "material": "Copper, brass, steel", "notes": "Tallest statue in Indonesia"},
        {"name": "Peter the Great Statue", "lat": 55.7350, "lon": 37.6100, "country": "Russia", "height_m": 98, "subject": "Peter the Great", "year": 1997, "material": "Stainless steel, bronze, copper", "notes": "One of tallest statues in Russia"},
        {"name": "Emperors Yan and Huang", "lat": 34.8927, "lon": 113.3808, "country": "China", "height_m": 106, "subject": "Legendary Chinese emperors", "year": 2007, "material": "Concrete, stone cladding", "notes": "Carved into a hillside near Zhengzhou"},
        {"name": "Guishan Guanyin", "lat": 28.7167, "lon": 112.3333, "country": "China", "height_m": 99, "subject": "Guanyin", "year": 2009, "material": "Bronze, gilded", "notes": "Changsha, Hunan province"},
        {"name": "Grand Buddha at Ling Shan", "lat": 31.4161, "lon": 120.1283, "country": "China", "height_m": 88, "subject": "Sakyamuni Buddha", "year": 1997, "material": "Bronze", "notes": "Wuxi, major pilgrimage site"},
        {"name": "Awaji Kannon", "lat": 34.5333, "lon": 134.9167, "country": "Japan", "height_m": 80, "subject": "Kannon (Guanyin)", "year": 1982, "material": "Concrete, steel", "notes": "Awaji Island, now closed to public"},
        {"name": "Statue of Belief (Vishwas Swaroopam)", "lat": 25.1550, "lon": 73.6747, "country": "India", "height_m": 106, "subject": "Lord Shiva", "year": 2024, "material": "Concrete, steel, stone", "notes": "Nathdwara, Rajasthan"},
        {"name": "Great Buddha of Thailand", "lat": 14.6833, "lon": 100.6333, "country": "Thailand", "height_m": 92, "subject": "Seated Buddha", "year": 2008, "material": "Concrete, gold paint", "notes": "Ang Thong province"},
        {"name": "Rodina-Mat (Motherland Monument)", "lat": 50.4267, "lon": 30.5631, "country": "Ukraine", "height_m": 62, "subject": "Motherland / WWII", "year": 1981, "material": "Stainless steel, titanium", "notes": "Kyiv, part of WWII museum complex"},
        {"name": "Cristo de la Concordia", "lat": -17.3946, "lon": -66.1461, "country": "Bolivia", "height_m": 34, "subject": "Jesus Christ", "year": 1994, "material": "Reinforced concrete, steel", "notes": "Slightly taller than Christ the Redeemer"},
        {"name": "Guan Yu Statue", "lat": 30.3167, "lon": 112.2333, "country": "China", "height_m": 58, "subject": "Guan Yu (warrior god)", "year": 2016, "material": "Bronze", "notes": "Jingzhou, 4000 tonnes of bronze strips"},
        {"name": "The Angel of the North", "lat": 54.9140, "lon": -1.5893, "country": "United Kingdom", "height_m": 20, "subject": "Angel / industrial heritage", "year": 1998, "material": "Weathering steel", "notes": "Antony Gormley; wingspan 54 m"},
        {"name": "Crazy Horse Memorial", "lat": 43.8372, "lon": -103.6242, "country": "United States", "height_m": 172, "subject": "Crazy Horse (Lakota leader)", "year": 0, "material": "Granite (mountain carving)", "notes": "Unfinished; will be tallest sculpture if completed"},
        {"name": "Mount Rushmore", "lat": 43.8791, "lon": -103.4591, "country": "United States", "height_m": 18, "subject": "Four US Presidents", "year": 1941, "material": "Granite (mountain carving)", "notes": "Washington, Jefferson, T. Roosevelt, Lincoln"},
        {"name": "Christ the King (Swiebodzin)", "lat": 52.2489, "lon": 15.5303, "country": "Poland", "height_m": 36, "subject": "Jesus Christ", "year": 2010, "material": "Concrete, fiberglass", "notes": "Claims to be tallest Jesus statue"},
        {"name": "Genghis Khan Equestrian Statue", "lat": 47.8069, "lon": 107.5308, "country": "Mongolia", "height_m": 40, "subject": "Genghis Khan on horseback", "year": 2008, "material": "Stainless steel", "notes": "Largest equestrian statue in the world"},
        {"name": "Statue of Mevlana", "lat": 38.5500, "lon": 42.9667, "country": "Turkey", "height_m": 42, "subject": "Rumi (Mevlana)", "year": 2023, "material": "Bronze, copper", "notes": "Near Lake Van, Bitlis province"},
        {"name": "Dignity (Chamberlain, SD)", "lat": 43.7500, "lon": -99.3167, "country": "United States", "height_m": 15, "subject": "Native American woman", "year": 2016, "material": "Stainless steel", "notes": "Overlooks Missouri River"},
        {"name": "Colossus of Rhodes (site)", "lat": 36.4511, "lon": 28.2278, "country": "Greece", "height_m": 33, "subject": "Helios (sun god)", "year": -280, "material": "Bronze, iron (destroyed 226 BC)", "notes": "Ancient Wonder of the World; original site"},
        {"name": "Leshan Giant Buddha", "lat": 29.5443, "lon": 103.7734, "country": "China", "height_m": 71, "subject": "Maitreya Buddha", "year": 803, "material": "Stone (carved cliff face)", "notes": "UNESCO site, largest stone Buddha in the world"},
    ]


def _classical_greek_roman():
    return [
        {"name": "Venus de Milo", "lat": 48.8606, "lon": 2.3376, "country": "France", "location": "Louvre Museum, Paris", "period": "c. 130-100 BC", "sculptor": "Alexandros of Antioch", "material": "Parian marble", "notes": "Greek goddess Aphrodite; found on Milos island 1820"},
        {"name": "Winged Victory of Samothrace", "lat": 48.8619, "lon": 2.3378, "country": "France", "location": "Louvre Museum, Paris", "period": "c. 190 BC", "sculptor": "Unknown (Rhodian)", "material": "Parian marble", "notes": "Nike alighting on a ship's prow"},
        {"name": "Laocoon and His Sons", "lat": 41.9065, "lon": 12.4536, "country": "Italy", "location": "Vatican Museums, Rome", "period": "c. 40-30 BC", "sculptor": "Agesander, Athenodoros, Polydorus", "material": "Marble", "notes": "Trojan priest attacked by sea serpents"},
        {"name": "Discobolus (Discus Thrower)", "lat": 41.9110, "lon": 12.4923, "country": "Italy", "location": "Museo Nazionale Romano, Rome", "period": "c. 450 BC (Roman copy)", "sculptor": "After Myron", "material": "Marble (original bronze lost)", "notes": "Iconic athlete in mid-throw"},
        {"name": "Apollo Belvedere", "lat": 41.9065, "lon": 12.4536, "country": "Italy", "location": "Vatican Museums, Rome", "period": "c. 120-140 AD (Roman copy)", "sculptor": "After Leochares", "material": "Marble", "notes": "Epitome of classical male beauty"},
        {"name": "Doryphoros (Spear Bearer)", "lat": 40.7500, "lon": 14.4856, "country": "Italy", "location": "Naples Archaeological Museum", "period": "c. 440 BC (Roman copy)", "sculptor": "After Polykleitos", "material": "Marble", "notes": "Canon of ideal human proportions"},
        {"name": "Augustus of Prima Porta", "lat": 41.9065, "lon": 12.4536, "country": "Italy", "location": "Vatican Museums, Rome", "period": "1st century AD", "sculptor": "Unknown", "material": "Marble (originally painted)", "notes": "Idealized portrait of Emperor Augustus"},
        {"name": "Artemision Bronze (Zeus or Poseidon)", "lat": 37.9892, "lon": 23.7315, "country": "Greece", "location": "National Archaeological Museum, Athens", "period": "c. 460 BC", "sculptor": "Unknown", "material": "Bronze", "notes": "One of few surviving large Greek bronzes"},
        {"name": "Hermes of Praxiteles", "lat": 37.6386, "lon": 21.6297, "country": "Greece", "location": "Archaeological Museum of Olympia", "period": "c. 330 BC", "sculptor": "Praxiteles (attributed)", "material": "Parian marble", "notes": "Hermes with infant Dionysus"},
        {"name": "Aphrodite of Knidos (copy)", "lat": 41.9065, "lon": 12.4536, "country": "Italy", "location": "Vatican Museums, Rome", "period": "c. 360 BC (Roman copy)", "sculptor": "After Praxiteles", "material": "Marble", "notes": "First life-size female nude in Greek sculpture"},
        {"name": "Nike of Paionios", "lat": 37.6386, "lon": 21.6297, "country": "Greece", "location": "Archaeological Museum of Olympia", "period": "c. 420 BC", "sculptor": "Paionios of Mende", "material": "Marble", "notes": "Victory figure from Temple of Zeus"},
        {"name": "Caryatid Porch (Erechtheion)", "lat": 37.9722, "lon": 23.7264, "country": "Greece", "location": "Acropolis, Athens", "period": "c. 421-406 BC", "sculptor": "Unknown Athenian", "material": "Pentelic marble", "notes": "Six draped female figures as columns"},
        {"name": "Charioteer of Delphi", "lat": 38.4824, "lon": 22.5008, "country": "Greece", "location": "Delphi Archaeological Museum", "period": "c. 478 BC", "sculptor": "Unknown", "material": "Bronze", "notes": "Victory monument; inlaid glass eyes"},
        {"name": "Elgin Marbles (Parthenon Sculptures)", "lat": 51.5194, "lon": -0.1270, "country": "United Kingdom", "location": "British Museum, London", "period": "c. 447-432 BC", "sculptor": "Workshop of Phidias", "material": "Pentelic marble", "notes": "Parthenon frieze, metopes, pediment figures"},
        {"name": "Farnese Hercules", "lat": 40.7500, "lon": 14.4856, "country": "Italy", "location": "Naples Archaeological Museum", "period": "3rd century AD (Roman copy)", "sculptor": "After Lysippos", "material": "Marble", "notes": "Muscular Hercules leaning on club"},
        {"name": "Dying Gaul", "lat": 41.9032, "lon": 12.4833, "country": "Italy", "location": "Capitoline Museums, Rome", "period": "c. 230 BC (Roman copy)", "sculptor": "After Epigonus", "material": "Marble", "notes": "Wounded Gallic warrior; great pathos"},
        {"name": "Riace Bronzes", "lat": 38.1100, "lon": 15.6500, "country": "Italy", "location": "Museo Nazionale, Reggio Calabria", "period": "c. 460-430 BC", "sculptor": "Unknown (Phidias school?)", "material": "Bronze", "notes": "Two Greek warriors found in the sea 1972"},
        {"name": "Boxer at Rest", "lat": 41.9110, "lon": 12.4923, "country": "Italy", "location": "Museo Nazionale Romano, Rome", "period": "c. 330-50 BC", "sculptor": "Unknown", "material": "Bronze with copper inlays", "notes": "Battered boxer with caestus gloves"},
        {"name": "Marcus Aurelius Equestrian", "lat": 41.8932, "lon": 12.4828, "country": "Italy", "location": "Capitoline Museums, Rome", "period": "c. 175 AD", "sculptor": "Unknown", "material": "Bronze, gilded", "notes": "Only surviving ancient equestrian bronze"},
        {"name": "Pergamon Altar Frieze", "lat": 52.5210, "lon": 13.3969, "country": "Germany", "location": "Pergamon Museum, Berlin", "period": "c. 180-160 BC", "sculptor": "Unknown Pergamene", "material": "Marble", "notes": "Gigantomachy frieze; monumental Hellenistic relief"},
        {"name": "Barberini Faun", "lat": 48.1496, "lon": 11.5720, "country": "Germany", "location": "Glyptothek, Munich", "period": "c. 220 BC", "sculptor": "Unknown", "material": "Marble", "notes": "Sleeping satyr in relaxed pose"},
        {"name": "Antinous Mondragone", "lat": 48.8606, "lon": 2.3376, "country": "France", "location": "Louvre Museum, Paris", "period": "c. 130 AD", "sculptor": "Unknown Roman", "material": "Marble", "notes": "Colossal bust of Hadrian's beloved"},
        {"name": "Capitoline Wolf", "lat": 41.8932, "lon": 12.4828, "country": "Italy", "location": "Capitoline Museums, Rome", "period": "c. 5th century BC (wolf) / 15th century (twins)", "sculptor": "Unknown Etruscan + Renaissance", "material": "Bronze", "notes": "She-wolf suckling Romulus and Remus"},
        {"name": "Nike Adjusting Her Sandal", "lat": 37.9714, "lon": 23.7258, "country": "Greece", "location": "Acropolis Museum, Athens", "period": "c. 410 BC", "sculptor": "Unknown", "material": "Marble relief", "notes": "From parapet of Temple of Athena Nike"},
        {"name": "Terme Boxer / Seated Boxer", "lat": 41.9110, "lon": 12.4923, "country": "Italy", "location": "Palazzo Massimo, Rome", "period": "c. 330-50 BC", "sculptor": "Unknown", "material": "Bronze", "notes": "Hellenistic realism at its finest"},
    ]


def _renaissance_masterpieces():
    return [
        {"name": "David (Michelangelo)", "lat": 43.7764, "lon": 11.2587, "country": "Italy", "location": "Galleria dell'Accademia, Florence", "artist": "Michelangelo", "year": 1504, "material": "Carrara marble", "notes": "17 ft tall; symbol of the Florentine Republic"},
        {"name": "Pieta (Michelangelo)", "lat": 41.9022, "lon": 12.4539, "country": "Italy", "location": "St. Peter's Basilica, Vatican", "artist": "Michelangelo", "year": 1499, "material": "Carrara marble", "notes": "Only work Michelangelo ever signed"},
        {"name": "Moses (Michelangelo)", "lat": 41.8939, "lon": 12.4953, "country": "Italy", "location": "San Pietro in Vincoli, Rome", "artist": "Michelangelo", "year": 1515, "material": "Marble", "notes": "Part of tomb of Pope Julius II; famous horns"},
        {"name": "Perseus with the Head of Medusa", "lat": 43.7696, "lon": 11.2558, "country": "Italy", "location": "Loggia dei Lanzi, Florence", "artist": "Benvenuto Cellini", "year": 1554, "material": "Bronze", "notes": "Mannerist masterpiece in open-air gallery"},
        {"name": "Rape of the Sabine Women", "lat": 43.7696, "lon": 11.2558, "country": "Italy", "location": "Loggia dei Lanzi, Florence", "artist": "Giambologna", "year": 1583, "material": "Marble", "notes": "Three intertwined figures; spiral composition"},
        {"name": "Ecstasy of Saint Teresa", "lat": 41.9039, "lon": 12.4966, "country": "Italy", "location": "Santa Maria della Vittoria, Rome", "artist": "Gian Lorenzo Bernini", "year": 1652, "material": "Marble", "notes": "Baroque theatricality; hidden window lighting"},
        {"name": "Apollo and Daphne (Bernini)", "lat": 41.9142, "lon": 12.4922, "country": "Italy", "location": "Galleria Borghese, Rome", "artist": "Gian Lorenzo Bernini", "year": 1625, "material": "Carrara marble", "notes": "Transformation captured in stone"},
        {"name": "David (Bernini)", "lat": 41.9142, "lon": 12.4922, "country": "Italy", "location": "Galleria Borghese, Rome", "artist": "Gian Lorenzo Bernini", "year": 1624, "material": "Marble", "notes": "Dynamic David mid-sling; Baroque energy"},
        {"name": "David (Donatello, bronze)", "lat": 43.7734, "lon": 11.2550, "country": "Italy", "location": "Bargello Museum, Florence", "artist": "Donatello", "year": 1440, "material": "Bronze", "notes": "First free-standing nude since antiquity"},
        {"name": "Gattamelata", "lat": 45.4015, "lon": 11.8810, "country": "Italy", "location": "Piazza del Santo, Padua", "artist": "Donatello", "year": 1453, "material": "Bronze", "notes": "First large equestrian statue since Marcus Aurelius"},
        {"name": "Fountain of the Four Rivers", "lat": 41.8990, "lon": 12.4731, "country": "Italy", "location": "Piazza Navona, Rome", "artist": "Gian Lorenzo Bernini", "year": 1651, "material": "Travertine marble", "notes": "Nile, Ganges, Danube, Rio de la Plata"},
        {"name": "Colleoni Monument", "lat": 45.4410, "lon": 12.3405, "country": "Italy", "location": "Campo SS. Giovanni e Paolo, Venice", "artist": "Andrea del Verrocchio", "year": 1496, "material": "Bronze", "notes": "Fierce equestrian; completed after Verrocchio's death"},
        {"name": "Gates of Paradise", "lat": 43.7732, "lon": 11.2550, "country": "Italy", "location": "Baptistery, Florence", "artist": "Lorenzo Ghiberti", "year": 1452, "material": "Gilded bronze", "notes": "East doors of the Baptistery; 10 panels of Old Testament"},
        {"name": "Dying Slave", "lat": 48.8606, "lon": 2.3376, "country": "France", "location": "Louvre Museum, Paris", "artist": "Michelangelo", "year": 1516, "material": "Marble", "notes": "Intended for Julius II tomb; non-finito style"},
        {"name": "Hercules and Cacus", "lat": 43.7694, "lon": 11.2553, "country": "Italy", "location": "Piazza della Signoria, Florence", "artist": "Baccio Bandinelli", "year": 1534, "material": "Marble", "notes": "Rival to Michelangelo's David"},
        {"name": "Neptune Fountain", "lat": 43.7698, "lon": 11.2554, "country": "Italy", "location": "Piazza della Signoria, Florence", "artist": "Bartolomeo Ammannati", "year": 1575, "material": "Marble and bronze", "notes": "Biancone (big white one); Florentines mocked it"},
        {"name": "Pluto and Proserpina (Bernini)", "lat": 41.9142, "lon": 12.4922, "country": "Italy", "location": "Galleria Borghese, Rome", "artist": "Gian Lorenzo Bernini", "year": 1622, "material": "Carrara marble", "notes": "Fingers pressing into marble flesh"},
        {"name": "Tomb of Lorenzo de' Medici", "lat": 43.7752, "lon": 11.2530, "country": "Italy", "location": "Medici Chapel, Florence", "artist": "Michelangelo", "year": 1534, "material": "Marble", "notes": "Dawn and Dusk allegorical figures"},
        {"name": "St. George (Donatello)", "lat": 43.7734, "lon": 11.2550, "country": "Italy", "location": "Bargello Museum, Florence", "artist": "Donatello", "year": 1417, "material": "Marble", "notes": "Originally in niche at Orsanmichele"},
        {"name": "The Thinker (Rodin)", "lat": 48.8554, "lon": 2.3158, "country": "France", "location": "Musee Rodin, Paris", "artist": "Auguste Rodin", "year": 1904, "material": "Bronze", "notes": "Originally part of The Gates of Hell"},
        {"name": "The Kiss (Rodin)", "lat": 48.8554, "lon": 2.3158, "country": "France", "location": "Musee Rodin, Paris", "artist": "Auguste Rodin", "year": 1882, "material": "Marble", "notes": "Paolo and Francesca from Dante's Inferno"},
        {"name": "The Gates of Hell", "lat": 48.8554, "lon": 2.3158, "country": "France", "location": "Musee Rodin, Paris", "artist": "Auguste Rodin", "year": 1917, "material": "Bronze", "notes": "237 figures; based on Dante's Inferno"},
        {"name": "The Burghers of Calais", "lat": 50.9435, "lon": 1.8508, "country": "France", "location": "Calais Town Hall", "artist": "Auguste Rodin", "year": 1889, "material": "Bronze", "notes": "Six citizens surrendering during Hundred Years War"},
        {"name": "Diana of Versailles", "lat": 48.8606, "lon": 2.3376, "country": "France", "location": "Louvre Museum, Paris", "artist": "Leochares (Roman copy)", "year": "1st-2nd century AD", "material": "Marble", "notes": "Artemis with deer; in royal French collections since 16th c."},
        {"name": "Nymph of Fontainebleau", "lat": 48.8606, "lon": 2.3376, "country": "France", "location": "Louvre Museum, Paris", "artist": "Benvenuto Cellini", "year": 1543, "material": "Bronze", "notes": "Lunette originally for Fontainebleau doorway"},
    ]


def _modern_sculpture_parks():
    return [
        {"name": "Storm King Art Center", "lat": 41.4194, "lon": -74.0606, "country": "United States", "city": "New Windsor, NY", "area_acres": 500, "artists": "Calder, Serra, Goldsworthy, di Suvero", "founded": 1960, "notes": "Premier outdoor sculpture museum in rolling hills"},
        {"name": "Yorkshire Sculpture Park", "lat": 53.6105, "lon": -1.5760, "country": "United Kingdom", "city": "Wakefield, England", "area_acres": 500, "artists": "Hepworth, Moore, Kapoor, Ai Weiwei", "founded": 1977, "notes": "UK's first sculpture park; Bretton Hall estate"},
        {"name": "Hakone Open-Air Museum", "lat": 35.2333, "lon": 139.0500, "country": "Japan", "city": "Hakone, Kanagawa", "area_acres": 17, "artists": "Picasso, Moore, Niki de Saint Phalle", "founded": 1969, "notes": "Japan's first open-air museum; mountain setting"},
        {"name": "Vigeland Sculpture Park", "lat": 59.9269, "lon": 10.7008, "country": "Norway", "city": "Oslo", "area_acres": 80, "artists": "Gustav Vigeland", "founded": 1940, "notes": "212 bronze and granite sculptures; Monolith centerpiece"},
        {"name": "Kroller-Muller Sculpture Garden", "lat": 52.0972, "lon": 5.8144, "country": "Netherlands", "city": "Otterlo, Gelderland", "area_acres": 62, "artists": "Rodin, Moore, Dubuffet, Serra, Oldenburg", "founded": 1961, "notes": "One of Europe's largest sculpture gardens"},
        {"name": "Inhotim", "lat": -20.1222, "lon": -44.2256, "country": "Brazil", "city": "Brumadinho, Minas Gerais", "area_acres": 3500, "artists": "Kapoor, Oiticica, Barney, Eliasson", "founded": 2006, "notes": "Contemporary art + botanical garden; largest open-air museum in South America"},
        {"name": "Grounds for Sculpture", "lat": 40.2222, "lon": -74.7250, "country": "United States", "city": "Hamilton, NJ", "area_acres": 42, "artists": "Seward Johnson, Lichtenstein", "founded": 1992, "notes": "270+ sculptures amid landscaped gardens"},
        {"name": "DeCordova Sculpture Park", "lat": 42.4464, "lon": -71.3213, "country": "United States", "city": "Lincoln, MA", "area_acres": 30, "artists": "Nam June Paik, Ursula von Rydingsvard", "founded": 1950, "notes": "New England's largest outdoor sculpture collection"},
        {"name": "Gibbs Farm", "lat": -36.3833, "lon": 174.4167, "country": "New Zealand", "city": "Kaipara Harbour", "area_acres": 1000, "artists": "Kapoor, Serra, Turrell, Graham", "founded": 1991, "notes": "Private farm with monumental commissions; limited public access"},
        {"name": "Chianti Sculpture Park", "lat": 43.3889, "lon": 11.2500, "country": "Italy", "city": "Pievasciata, Tuscany", "area_acres": 17, "artists": "Various international", "founded": 2004, "notes": "Sculptures in Tuscan oak woodland"},
        {"name": "Benesse Art Site Naoshima", "lat": 34.4600, "lon": 133.9956, "country": "Japan", "city": "Naoshima Island", "area_acres": 0, "artists": "Kusama, Sugimoto, de Maria, Turrell", "founded": 1992, "notes": "Art island with yellow pumpkin and Chichu Art Museum"},
        {"name": "Olympic Sculpture Park", "lat": 47.6164, "lon": -122.3553, "country": "United States", "city": "Seattle, WA", "area_acres": 9, "artists": "Calder, Serra, Oldenburg", "founded": 2007, "notes": "Free waterfront park by Seattle Art Museum"},
        {"name": "Socrates Sculpture Park", "lat": 40.7694, "lon": -73.9356, "country": "United States", "city": "Long Island City, NY", "area_acres": 5, "artists": "Rotating emerging artists", "founded": 1986, "notes": "Reclaimed landfill; free outdoor gallery"},
        {"name": "Jupiter Artland", "lat": 55.8958, "lon": -3.4375, "country": "United Kingdom", "city": "Edinburgh, Scotland", "area_acres": 100, "artists": "Gormley, Kapoor, Goldsworthy, Turrell", "founded": 2009, "notes": "Private estate with land art and sculpture"},
        {"name": "Europos Parkas", "lat": 54.8500, "lon": 25.3000, "country": "Lithuania", "city": "Vilnius", "area_acres": 135, "artists": "Oppenheim, LeWitt, Abakanowicz", "founded": 1991, "notes": "Near geographical centre of Europe"},
        {"name": "Louisiana Museum of Modern Art", "lat": 55.9683, "lon": 12.5417, "country": "Denmark", "city": "Humlebaek", "area_acres": 0, "artists": "Moore, Calder, Giacometti, Arp", "founded": 1958, "notes": "Seaside sculpture garden overlooking Oresund"},
        {"name": "Fondation Maeght", "lat": 43.6928, "lon": 7.0458, "country": "France", "city": "Saint-Paul-de-Vence", "area_acres": 0, "artists": "Miro, Giacometti, Calder, Chagall", "founded": 1964, "notes": "Miro labyrinth, Giacometti courtyard"},
        {"name": "Hakone Pavilion / Museum San", "lat": 37.5583, "lon": 128.7167, "country": "South Korea", "city": "Wonju, Gangwon", "area_acres": 0, "artists": "Tadao Ando (architect), James Turrell", "founded": 2013, "notes": "Art museum in mountainous landscape"},
        {"name": "Chatsworth House Sculpture", "lat": 53.2272, "lon": -1.6114, "country": "United Kingdom", "city": "Bakewell, Derbyshire", "area_acres": 105, "artists": "Various rotating exhibitions", "founded": 2006, "notes": "Annual contemporary sculpture in historic parkland"},
        {"name": "Skulptur Projekte Munster (sites)", "lat": 51.9607, "lon": 7.6261, "country": "Germany", "city": "Munster", "area_acres": 0, "artists": "Claes Oldenburg, Bruce Nauman", "founded": 1977, "notes": "Decennial public art exhibition; permanent works remain"},
        {"name": "Wanas Konst", "lat": 55.7833, "lon": 13.9667, "country": "Sweden", "city": "Knislinge, Skane", "area_acres": 100, "artists": "Yoko Ono, Maya Lin, Robert Wilson", "founded": 1987, "notes": "Art in Swedish forest and castle grounds"},
        {"name": "Ekebergparken", "lat": 59.8969, "lon": 10.7628, "country": "Norway", "city": "Oslo", "area_acres": 64, "artists": "Rodin, Renoir, Dali, Bourgeois, Damien Hirst", "founded": 2013, "notes": "40+ sculptures in hillside park above Oslo fjord"},
        {"name": "Laumeier Sculpture Park", "lat": 38.5547, "lon": -90.3958, "country": "United States", "city": "St. Louis, MO", "area_acres": 105, "artists": "di Suvero, Beverly Pepper", "founded": 1976, "notes": "Free museum in suburban woodland"},
        {"name": "Bad Ragaz Sculpture Trail", "lat": 47.0022, "lon": 9.5025, "country": "Switzerland", "city": "Bad Ragaz, St. Gallen", "area_acres": 0, "artists": "Rotating triennial", "founded": 2003, "notes": "Switzerland's largest outdoor sculpture show"},
        {"name": "Sculpture by the Sea", "lat": -33.8917, "lon": 151.2750, "country": "Australia", "city": "Bondi Beach, Sydney", "area_acres": 0, "artists": "100+ annually rotating", "founded": 1997, "notes": "Annual coastal walk exhibition; free"},
    ]


def _ancient_megalithic():
    return [
        {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "country": "United Kingdom", "period": "c. 3000-2000 BC", "type": "Stone circle", "notes": "Iconic sarsen trilithons and bluestones from Wales; UNESCO site"},
        {"name": "Moai of Easter Island (Ahu Tongariki)", "lat": -27.1256, "lon": -109.2772, "country": "Chile", "period": "c. 1250-1500 AD", "type": "Monolithic statues", "notes": "15 moai on largest ahu; carved from volcanic tuff"},
        {"name": "Gobekli Tepe", "lat": 37.2233, "lon": 38.9225, "country": "Turkey", "period": "c. 9500-8000 BC", "type": "Megalithic temple", "notes": "World's oldest known temple; carved T-pillars with animal reliefs"},
        {"name": "Carnac Stones", "lat": 47.5925, "lon": -3.0769, "country": "France", "period": "c. 4500-3300 BC", "type": "Stone rows", "notes": "3,000+ standing stones in parallel alignments"},
        {"name": "Newgrange", "lat": 53.6947, "lon": -6.4755, "country": "Ireland", "period": "c. 3200 BC", "type": "Passage tomb", "notes": "Older than Pyramids; solstice light box; UNESCO site"},
        {"name": "Dolmen of Menga", "lat": 37.0236, "lon": -4.5483, "country": "Spain", "period": "c. 3700 BC", "type": "Megalithic dolmen", "notes": "One of largest known European megaliths; UNESCO site"},
        {"name": "Callanish Stones", "lat": 58.1978, "lon": -6.7444, "country": "United Kingdom", "period": "c. 2900-2600 BC", "type": "Stone circle + avenue", "notes": "Cruciform setting; Lewis, Outer Hebrides"},
        {"name": "Avebury Stone Circle", "lat": 51.4289, "lon": -1.8547, "country": "United Kingdom", "period": "c. 2850 BC", "type": "Henge + stone circle", "notes": "Largest stone circle in world; village built inside"},
        {"name": "Dolmen of Ganghwa", "lat": 37.7467, "lon": 126.4328, "country": "South Korea", "period": "c. 1000 BC", "type": "Dolmens", "notes": "Part of Korean dolmen sites; UNESCO World Heritage"},
        {"name": "Tiya Stelae Field", "lat": 8.4333, "lon": 38.6167, "country": "Ethiopia", "period": "c. 12th-14th century AD", "type": "Carved stelae", "notes": "36 carved pillars with sword-like symbols; UNESCO site"},
        {"name": "Ring of Brodgar", "lat": 59.0017, "lon": -3.2292, "country": "United Kingdom", "period": "c. 2500-2000 BC", "type": "Stone circle", "notes": "60 original stones on Orkney; Heart of Neolithic Orkney"},
        {"name": "Great Zimbabwe Walls", "lat": -20.2674, "lon": 30.9338, "country": "Zimbabwe", "period": "c. 1100-1450 AD", "type": "Dry stone walls", "notes": "Largest ancient structure south of the Sahara"},
        {"name": "Baalbek Trilithon", "lat": 34.0069, "lon": 36.2042, "country": "Lebanon", "period": "c. 27 BC (Roman) on older foundations", "type": "Megalithic stones", "notes": "Three 800-tonne stones in temple foundation"},
        {"name": "Tiahuanaco (Tiwanaku)", "lat": -16.5547, "lon": -68.6739, "country": "Bolivia", "period": "c. 500-900 AD", "type": "Megalithic city", "notes": "Gateway of the Sun; pre-Inca ceremonial center"},
        {"name": "Almendres Cromlech", "lat": 38.5555, "lon": -8.0611, "country": "Portugal", "period": "c. 6000-4000 BC", "type": "Stone circle", "notes": "Oldest megalithic complex on Iberian Peninsula"},
        {"name": "Puma Punku", "lat": -16.5617, "lon": -68.6806, "country": "Bolivia", "period": "c. 536-600 AD", "type": "Megalithic temple", "notes": "Precision-cut H-blocks; part of Tiwanaku complex"},
        {"name": "Ales Stenar", "lat": 55.3842, "lon": 14.0539, "country": "Sweden", "period": "c. 600 AD", "type": "Stone ship", "notes": "59 boulders forming 67 m ship outline on cliff top"},
        {"name": "Mnajdra Temples", "lat": 35.8267, "lon": 14.4361, "country": "Malta", "period": "c. 3600-3200 BC", "type": "Megalithic temple", "notes": "Solar-aligned chambers; UNESCO with Hagar Qim"},
        {"name": "Hagar Qim", "lat": 35.8278, "lon": 14.4419, "country": "Malta", "period": "c. 3600-3200 BC", "type": "Megalithic temple", "notes": "Oldest free-standing structures in the world"},
        {"name": "Ollantaytambo", "lat": -13.2589, "lon": -72.2636, "country": "Peru", "period": "c. 1400 AD", "type": "Megalithic fortress", "notes": "Inca temple fortress with 50-tonne stone blocks"},
        {"name": "Sacsayhuaman", "lat": -13.5069, "lon": -71.9822, "country": "Peru", "period": "c. 1400 AD", "type": "Megalithic fortress", "notes": "Zigzag walls; stones up to 200 tonnes perfectly fitted"},
        {"name": "Jelling Stones", "lat": 55.7553, "lon": 9.4194, "country": "Denmark", "period": "c. 965 AD", "type": "Runestones", "notes": "Denmark's birth certificate; oldest depiction of Christ in Scandinavia"},
        {"name": "Bryn Celli Ddu", "lat": 53.2067, "lon": -4.2369, "country": "United Kingdom", "period": "c. 3000 BC", "type": "Passage tomb", "notes": "Neolithic burial chamber on Anglesey, Wales"},
        {"name": "Moai Quarry (Rano Raraku)", "lat": -27.1217, "lon": -109.2883, "country": "Chile", "period": "c. 1100-1500 AD", "type": "Quarry + unfinished moai", "notes": "Nearly 400 moai in various stages of carving"},
        {"name": "Nabta Playa Stone Circle", "lat": 22.5167, "lon": 30.7167, "country": "Egypt", "period": "c. 4500 BC", "type": "Stone circle", "notes": "Possibly oldest astronomical alignment in the world"},
    ]


def _buddhist_hindu_monumental():
    return [
        {"name": "Leshan Giant Buddha", "lat": 29.5443, "lon": 103.7734, "country": "China", "religion": "Buddhism", "height_m": 71, "period": "713-803 AD", "notes": "Largest stone Buddha in the world; UNESCO site"},
        {"name": "Tian Tan Buddha (Big Buddha)", "lat": 22.2540, "lon": 113.9050, "country": "Hong Kong", "religion": "Buddhism", "height_m": 34, "period": "1993", "notes": "Bronze seated Buddha on Lantau Island"},
        {"name": "Great Buddha of Kamakura", "lat": 35.3167, "lon": 139.5356, "country": "Japan", "religion": "Buddhism", "height_m": 13, "period": "1252 AD", "notes": "Outdoor bronze Amitabha; originally inside a hall"},
        {"name": "Todai-ji Great Buddha (Nara)", "lat": 34.6891, "lon": 135.8398, "country": "Japan", "religion": "Buddhism", "height_m": 15, "period": "752 AD (recast 1692)", "notes": "World's largest bronze Buddha in largest wooden building"},
        {"name": "Buddhas of Bamiyan (site)", "lat": 34.8328, "lon": 67.8272, "country": "Afghanistan", "religion": "Buddhism", "height_m": 55, "period": "6th century AD (destroyed 2001)", "notes": "Destroyed by Taliban; carved into sandstone cliff"},
        {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "country": "Cambodia", "religion": "Hinduism/Buddhism", "height_m": 65, "period": "12th century AD", "notes": "Largest religious monument; bas-relief galleries"},
        {"name": "Bayon Temple Faces", "lat": 13.4412, "lon": 103.8590, "country": "Cambodia", "religion": "Buddhism", "height_m": 43, "period": "Late 12th century", "notes": "216 serene stone faces on tower temples"},
        {"name": "Borobudur", "lat": -7.6079, "lon": 110.2038, "country": "Indonesia", "religion": "Buddhism", "height_m": 35, "period": "c. 800 AD", "notes": "Largest Buddhist temple; 504 Buddha statues, 2672 relief panels"},
        {"name": "Gomateswara (Bahubali)", "lat": 12.8585, "lon": 76.4838, "country": "India", "religion": "Jainism", "height_m": 17, "period": "981 AD", "notes": "Monolithic granite statue; Mahamastakabhisheka every 12 years"},
        {"name": "Ellora Kailasa Temple", "lat": 20.0258, "lon": 75.1792, "country": "India", "religion": "Hinduism", "height_m": 33, "period": "8th century AD", "notes": "Largest monolithic rock excavation in the world"},
        {"name": "Wat Pho Reclining Buddha", "lat": 13.7468, "lon": 100.4927, "country": "Thailand", "religion": "Buddhism", "height_m": 15, "period": "1832", "notes": "46 m long reclining Buddha covered in gold leaf"},
        {"name": "Emerald Buddha (Wat Phra Kaew)", "lat": 13.7516, "lon": 100.4927, "country": "Thailand", "religion": "Buddhism", "height_m": 0.66, "period": "15th century", "notes": "Carved from single jade block; most sacred Thai image"},
        {"name": "Murudeshwara Shiva", "lat": 14.0944, "lon": 74.4844, "country": "India", "religion": "Hinduism", "height_m": 37, "period": 2002, "notes": "Second tallest Shiva statue in the world"},
        {"name": "Aukana Buddha", "lat": 7.8594, "lon": 80.5819, "country": "Sri Lanka", "religion": "Buddhism", "height_m": 12, "period": "5th century AD", "notes": "Finely carved standing Buddha from single granite rock"},
        {"name": "Spring Temple Buddha", "lat": 33.7753, "lon": 112.4514, "country": "China", "religion": "Buddhism", "height_m": 153, "period": "2008", "notes": "Second tallest statue in the world"},
        {"name": "Prambanan Temple", "lat": -7.7520, "lon": 110.4914, "country": "Indonesia", "religion": "Hinduism", "height_m": 47, "period": "9th century AD", "notes": "Largest Hindu temple in Indonesia; Shiva, Vishnu, Brahma"},
        {"name": "Longmen Grottoes", "lat": 34.5653, "lon": 112.4711, "country": "China", "religion": "Buddhism", "height_m": 17, "period": "493-1127 AD", "notes": "100,000+ Buddhist carvings; Vairocana Buddha is largest"},
        {"name": "Yungang Grottoes", "lat": 40.1117, "lon": 113.1319, "country": "China", "religion": "Buddhism", "height_m": 17, "period": "460-525 AD", "notes": "51,000+ statues; oldest are most impressive"},
        {"name": "Ajanta Caves", "lat": 20.5519, "lon": 75.7033, "country": "India", "religion": "Buddhism", "height_m": 0, "period": "2nd century BC - 6th century AD", "notes": "30 rock-cut caves with paintings and sculpture; UNESCO"},
        {"name": "Daibutsu of Gifu", "lat": 35.4333, "lon": 136.7833, "country": "Japan", "religion": "Buddhism", "height_m": 14, "period": "1832", "notes": "Lacquered bamboo frame covered in clay and gold leaf"},
        {"name": "Laykyun Sekkya", "lat": 21.2833, "lon": 95.1667, "country": "Myanmar", "religion": "Buddhism", "height_m": 116, "period": "2008", "notes": "Standing Buddha with reclining Buddha at base"},
        {"name": "Thiruvalluvar Statue", "lat": 8.0783, "lon": 77.5567, "country": "India", "religion": "Hinduism/Philosophy", "height_m": 40, "period": "2000", "notes": "133 ft (1330 chapters of Thirukkural); Kanyakumari"},
        {"name": "Great Buddha of Ling Shan", "lat": 31.4161, "lon": 120.1283, "country": "China", "religion": "Buddhism", "height_m": 88, "period": "1997", "notes": "Bronze standing Sakyamuni; major pilgrimage site"},
        {"name": "Batu Caves Murugan Statue", "lat": 3.2372, "lon": 101.6839, "country": "Malaysia", "religion": "Hinduism", "height_m": 43, "period": "2006", "notes": "Gold-painted statue of Lord Murugan at cave entrance"},
        {"name": "Nara Deer Park Sculptures", "lat": 34.6851, "lon": 135.8429, "country": "Japan", "religion": "Buddhism/Shinto", "height_m": 0, "period": "Various", "notes": "Stone lanterns and guardian statues among sacred deer"},
    ]


def _public_art_urban():
    return [
        {"name": "Cloud Gate (The Bean)", "lat": 41.8827, "lon": -87.6233, "country": "United States", "city": "Chicago, IL", "artist": "Anish Kapoor", "year": 2006, "material": "Stainless steel", "notes": "110-tonne mirrored bean; Millennium Park icon"},
        {"name": "Manneken Pis", "lat": 50.8450, "lon": 4.3500, "country": "Belgium", "city": "Brussels", "artist": "Hiëronymus Duquesnoy the Elder", "year": 1619, "material": "Bronze", "notes": "Small boy fountain; dressed in costumes 130+ times/year"},
        {"name": "The Little Mermaid", "lat": 55.6929, "lon": 12.5994, "country": "Denmark", "city": "Copenhagen", "artist": "Edvard Eriksen", "year": 1913, "material": "Bronze", "notes": "Based on Hans Christian Andersen fairy tale"},
        {"name": "LOVE Sculpture (original)", "lat": 39.9543, "lon": -75.1720, "country": "United States", "city": "Philadelphia, PA", "artist": "Robert Indiana", "year": 1976, "material": "Cor-Ten steel", "notes": "Iconic tilted O; LOVE Park"},
        {"name": "Charging Bull", "lat": 40.7056, "lon": -74.0134, "country": "United States", "city": "New York, NY", "artist": "Arturo Di Modica", "year": 1989, "material": "Bronze", "notes": "Guerrilla art near Wall Street; 3,200 kg"},
        {"name": "Fearless Girl", "lat": 40.7069, "lon": -74.0089, "country": "United States", "city": "New York, NY", "artist": "Kristen Visbal", "year": 2017, "material": "Bronze", "notes": "Now facing NYSE; originally opposite Charging Bull"},
        {"name": "Kapoor's Sky Mirror", "lat": 40.7614, "lon": -73.9776, "country": "United States", "city": "New York, NY", "artist": "Anish Kapoor", "year": 2006, "material": "Stainless steel", "notes": "Concave/convex mirror; Rockefeller Center installation"},
        {"name": "The Kelpies", "lat": 56.0172, "lon": -3.7533, "country": "United Kingdom", "city": "Falkirk, Scotland", "artist": "Andy Scott", "year": 2013, "material": "Stainless steel", "notes": "30 m horse-head sculptures; mythical water spirits"},
        {"name": "Spoonbridge and Cherry", "lat": 44.9694, "lon": -93.2894, "country": "United States", "city": "Minneapolis, MN", "artist": "Claes Oldenburg & Coosje van Bruggen", "year": 1988, "material": "Aluminum, stainless steel", "notes": "Minneapolis Sculpture Garden landmark"},
        {"name": "Atomium", "lat": 50.8950, "lon": 4.3417, "country": "Belgium", "city": "Brussels", "artist": "Andre Waterkeyn", "year": 1958, "material": "Steel, aluminum cladding", "notes": "102 m unit cell of iron crystal; 1958 World Fair"},
        {"name": "Cristo Redentor (Rio)", "lat": -22.9519, "lon": -43.2105, "country": "Brazil", "city": "Rio de Janeiro", "artist": "Paul Landowski / Heitor da Silva Costa", "year": 1931, "material": "Concrete, soapstone", "notes": "38 m; Corcovado peak; New 7 Wonders"},
        {"name": "Puppy (Jeff Koons)", "lat": 43.2688, "lon": -2.9344, "country": "Spain", "city": "Bilbao", "artist": "Jeff Koons", "year": 1992, "material": "Steel, living flowers", "notes": "12 m terrier covered in flowers; Guggenheim Bilbao entrance"},
        {"name": "Spider (Maman) - Ottawa", "lat": 45.4286, "lon": -75.6993, "country": "Canada", "city": "Ottawa", "artist": "Louise Bourgeois", "year": 1999, "material": "Bronze, stainless steel, marble", "notes": "9 m spider; National Gallery of Canada"},
        {"name": "Umbrellas (Gifu)", "lat": 51.5078, "lon": -0.0986, "country": "United Kingdom", "city": "London", "artist": "Do Ho Suh (various public art)", "year": 2012, "material": "Various", "notes": "London has 1000+ public art pieces; rotating commissions"},
        {"name": "Freedom (Zenos Frudakis)", "lat": 39.9530, "lon": -75.1600, "country": "United States", "city": "Philadelphia, PA", "artist": "Zenos Frudakis", "year": 2001, "material": "Bronze", "notes": "Figure breaking free from wall; powerful liberation theme"},
        {"name": "Expansion (Paige Bradley)", "lat": 40.7540, "lon": -73.9870, "country": "United States", "city": "New York, NY", "artist": "Paige Bradley", "year": 2004, "material": "Bronze, electricity", "notes": "Cracked meditating figure with light shining through"},
        {"name": "Non-Violence (Knotted Gun)", "lat": 40.7489, "lon": -73.9680, "country": "United States", "city": "New York (UN HQ)", "artist": "Carl Fredrik Reutersward", "year": 1988, "material": "Bronze", "notes": "Oversized revolver with knotted barrel; peace symbol"},
        {"name": "Floralis Generica", "lat": -34.5706, "lon": -58.4117, "country": "Argentina", "city": "Buenos Aires", "artist": "Eduardo Catalano", "year": 2002, "material": "Steel, aluminum", "notes": "23 m flower that opens at dawn, closes at dusk"},
        {"name": "Verity", "lat": 51.2117, "lon": -3.4687, "country": "United Kingdom", "city": "Ilfracombe, Devon", "artist": "Damien Hirst", "year": 2012, "material": "Bronze, stainless steel", "notes": "20 m pregnant woman with exposed anatomy; truth allegory"},
        {"name": "Mustangs of Las Colinas", "lat": 32.8770, "lon": -96.9419, "country": "United States", "city": "Irving, TX", "artist": "Robert Glen", "year": 1984, "material": "Bronze", "notes": "9 wild mustangs crossing water; largest equestrian sculpture"},
        {"name": "Bean Sculpture (India Gate)", "lat": 28.6129, "lon": 77.2295, "country": "India", "city": "New Delhi", "artist": "Edwin Lutyens (India Gate)", "year": 1931, "material": "Sandstone", "notes": "42 m war memorial arch; national monument"},
        {"name": "The Shark (Headington)", "lat": 51.7520, "lon": -1.2201, "country": "United Kingdom", "city": "Oxford", "artist": "John Buckley", "year": 1986, "material": "Fiberglass", "notes": "25-ft shark crashing through roof of terraced house"},
        {"name": "Le Pouce (The Thumb)", "lat": 43.5844, "lon": 7.1200, "country": "France", "city": "La Defense, Paris", "artist": "Cesar Baldaccini", "year": 1965, "material": "Bronze", "notes": "12 m giant thumb; Pop Art monument"},
        {"name": "Homeless Jesus", "lat": 43.6544, "lon": -79.3807, "country": "Canada", "city": "Toronto", "artist": "Timothy Schmalz", "year": 2013, "material": "Bronze", "notes": "Figure under blanket on park bench; copies worldwide"},
        {"name": "Digital Orca", "lat": 49.2897, "lon": -123.1175, "country": "Canada", "city": "Vancouver", "artist": "Douglas Coupland", "year": 2009, "material": "Aluminum, steel, LED", "notes": "Pixelated killer whale; Jack Poole Plaza"},
    ]


def _stone_carving_traditions():
    return [
        {"name": "Maori Meeting House Carvings", "lat": -38.1368, "lon": 176.2497, "country": "New Zealand", "tradition": "Maori Whakairo", "period": "Ongoing", "material": "Totara wood, stone", "notes": "Ancestor figures on wharenui (meeting houses); Rotorua"},
        {"name": "Balinese Temple Guardians", "lat": -8.3405, "lon": 115.3600, "country": "Indonesia", "tradition": "Balinese stone carving", "period": "Ongoing", "material": "Volcanic paras stone", "notes": "Dvarapala guardians and Barong masks at temple gates"},
        {"name": "Inuit Inukshuks (Rankin Inlet)", "lat": 62.8058, "lon": -92.0858, "country": "Canada", "tradition": "Inuit sculpture", "period": "Pre-contact to present", "material": "Soapstone, serpentine, granite", "notes": "Stone figures for wayfinding and spiritual purposes"},
        {"name": "Khajuraho Temples", "lat": 24.8318, "lon": 79.9199, "country": "India", "tradition": "Hindu temple sculpture", "period": "950-1050 AD", "material": "Sandstone", "notes": "Erotic carvings and divine figures; UNESCO site"},
        {"name": "Konark Sun Temple", "lat": 19.8876, "lon": 86.0945, "country": "India", "tradition": "Odia stone carving", "period": "13th century", "material": "Chlorite, laterite", "notes": "Temple as giant chariot with 24 wheels; UNESCO"},
        {"name": "Mahabalipuram Shore Temple", "lat": 12.6169, "lon": 80.1999, "country": "India", "tradition": "Pallava sculpture", "period": "7th-8th century", "material": "Granite", "notes": "Arjuna's Penance relief and shore temple; UNESCO"},
        {"name": "Petra Treasury (Al-Khazneh)", "lat": 30.3285, "lon": 35.4444, "country": "Jordan", "tradition": "Nabataean rock carving", "period": "1st century BC", "material": "Sandstone (rock-cut)", "notes": "39 m facade carved from cliff face; UNESCO"},
        {"name": "Abu Simbel Temples", "lat": 22.3360, "lon": 31.6256, "country": "Egypt", "tradition": "Egyptian monumental sculpture", "period": "c. 1264 BC", "material": "Sandstone (rock-cut)", "notes": "Four 20 m colossi of Ramesses II; relocated 1968"},
        {"name": "Lalibela Rock-Hewn Churches", "lat": 12.0319, "lon": 39.0472, "country": "Ethiopia", "tradition": "Ethiopian Orthodox", "period": "12th-13th century", "material": "Volcanic tuff (monolithic)", "notes": "11 churches carved from bedrock; UNESCO"},
        {"name": "Jali Screens of Mughal India", "lat": 27.1751, "lon": 78.0421, "country": "India", "tradition": "Mughal jali carving", "period": "17th century", "material": "White marble", "notes": "Intricate lattice screens at Taj Mahal; geometric perfection"},
        {"name": "Shona Sculpture Village (Tengenenge)", "lat": -16.6500, "lon": 30.9333, "country": "Zimbabwe", "tradition": "Shona sculpture", "period": "1966-present", "material": "Serpentine, springstone", "notes": "Artist community producing internationally exhibited stone art"},
        {"name": "Oaxacan Alebrijes Workshop", "lat": 16.8906, "lon": -96.7625, "country": "Mexico", "tradition": "Zapotec wood/stone carving", "period": "Ongoing", "material": "Copal wood (and stone)", "notes": "Fantastical painted creatures; San Martin Tilcajete"},
        {"name": "Axum Stelae Field", "lat": 14.1307, "lon": 38.7208, "country": "Ethiopia", "tradition": "Aksumite monumental art", "period": "3rd-4th century AD", "material": "Granite", "notes": "Tallest 33 m obelisks with carved doors and windows; UNESCO"},
        {"name": "Sanchi Stupa Gateways", "lat": 23.4793, "lon": 77.7397, "country": "India", "tradition": "Buddhist torana carving", "period": "1st century BC", "material": "Sandstone", "notes": "Four ornately carved gateways (toranas); UNESCO"},
        {"name": "Angkor Stone Carving (Banteay Srei)", "lat": 13.5986, "lon": 103.9628, "country": "Cambodia", "tradition": "Khmer bas-relief", "period": "967 AD", "material": "Red sandstone", "notes": "Finest stone carvings in Angkor; intricate female deities"},
        {"name": "Romanesque Tympanum (Vezelay)", "lat": 47.4664, "lon": 3.7489, "country": "France", "tradition": "Romanesque sculpture", "period": "12th century", "material": "Limestone", "notes": "Christ in Majesty tympanum; Basilica of Sainte-Marie-Madeleine"},
        {"name": "Moai Carving Site (Rano Raraku)", "lat": -27.1217, "lon": -109.2883, "country": "Chile", "tradition": "Rapa Nui carving", "period": "c. 1100-1500 AD", "material": "Volcanic tuff", "notes": "Quarry where moai were carved from the mountainside"},
        {"name": "Haida Heritage Centre", "lat": 53.2527, "lon": -131.9883, "country": "Canada", "tradition": "Haida cedar carving", "period": "Ongoing", "material": "Red cedar (and argillite stone)", "notes": "Totem poles and argillite carvings; Haida Gwaii"},
        {"name": "Marble Quarries of Carrara", "lat": 44.0792, "lon": 10.0958, "country": "Italy", "tradition": "Italian marble carving", "period": "Roman era to present", "material": "Carrara marble", "notes": "Source of Michelangelo's marble; active quarries"},
        {"name": "Sukhothai Historical Park", "lat": 17.0200, "lon": 99.7000, "country": "Thailand", "tradition": "Thai Buddhist sculpture", "period": "13th-14th century", "material": "Laterite, stucco, bronze", "notes": "Walking Buddha style originated here; UNESCO"},
        {"name": "Igbo-Ukwu Bronzes (site)", "lat": 6.0167, "lon": 7.0167, "country": "Nigeria", "tradition": "Igbo lost-wax casting", "period": "9th century AD", "material": "Bronze (leaded)", "notes": "Oldest known bronze castings in West Africa"},
        {"name": "Benin Bronzes (historic site)", "lat": 6.3350, "lon": 5.6270, "country": "Nigeria", "tradition": "Edo kingdom casting", "period": "13th-16th century", "material": "Bronze, brass, ivory", "notes": "Royal court art; many now repatriated from Western museums"},
        {"name": "Georgian Stone Cross-Stones (Jvari)", "lat": 41.8381, "lon": 44.7333, "country": "Georgia", "tradition": "Georgian khachkar/church carving", "period": "6th century AD", "material": "Stone", "notes": "Jvari Monastery with carved stone cross facade"},
        {"name": "Armenian Khachkar (Goshavank)", "lat": 40.7283, "lon": 44.9950, "country": "Armenia", "tradition": "Armenian cross-stone", "period": "13th century", "material": "Tufa stone", "notes": "Finest khachkar in Armenia; intricate lace-like carving"},
        {"name": "Borobudur Relief Panels", "lat": -7.6079, "lon": 110.2038, "country": "Indonesia", "tradition": "Javanese Buddhist sculpture", "period": "c. 800 AD", "material": "Andesite stone", "notes": "2,672 narrative relief panels; longest Buddhist story in stone"},
    ]


def _ice_sand_festivals():
    return [
        {"name": "Harbin International Ice and Snow Festival", "lat": 45.7500, "lon": 126.6500, "country": "China", "city": "Harbin, Heilongjiang", "type": "Ice & Snow", "months": "Jan-Feb", "founded": 1963, "notes": "World's largest; full-size illuminated ice buildings"},
        {"name": "Sapporo Snow Festival", "lat": 43.0621, "lon": 141.3544, "country": "Japan", "city": "Sapporo, Hokkaido", "type": "Snow", "months": "Feb", "founded": 1950, "notes": "250+ snow and ice sculptures; Odori Park main site"},
        {"name": "Quebec Winter Carnival Ice Palace", "lat": 46.8139, "lon": -71.2078, "country": "Canada", "city": "Quebec City", "type": "Ice & Snow", "months": "Jan-Feb", "founded": 1955, "notes": "Bonhomme Carnaval ice palace; world's largest winter carnival"},
        {"name": "World Ice Art Championships", "lat": 64.8378, "lon": -147.7164, "country": "United States", "city": "Fairbanks, AK", "type": "Ice", "months": "Feb-Mar", "founded": 1988, "notes": "Multi-block and single-block competitions"},
        {"name": "Ice Magic Festival (Lake Louise)", "lat": 51.4167, "lon": -116.1767, "country": "Canada", "city": "Lake Louise, Alberta", "type": "Ice", "months": "Jan", "founded": 1992, "notes": "Professional ice carving at Chateau Lake Louise"},
        {"name": "Bruges Ice Sculpture Festival", "lat": 51.2094, "lon": 3.2247, "country": "Belgium", "city": "Bruges", "type": "Ice", "months": "Nov-Jan", "founded": 2000, "notes": "Indoor festival at Bruges train station"},
        {"name": "International Sand Sculpture Festival (FIESA)", "lat": 37.1244, "lon": -8.5250, "country": "Portugal", "city": "Pera, Algarve", "type": "Sand", "months": "Mar-Oct", "founded": 2003, "notes": "World's largest sand sculpture festival; 40,000 tonnes of sand"},
        {"name": "Revere Beach Sand Sculpting Festival", "lat": 42.4072, "lon": -70.9922, "country": "United States", "city": "Revere, MA", "type": "Sand", "months": "Jul", "founded": 2004, "notes": "Master sand sculptors compete on America's first public beach"},
        {"name": "Weston-super-Mare Sand Sculpture Festival", "lat": 51.3461, "lon": -2.9781, "country": "United Kingdom", "city": "Weston-super-Mare", "type": "Sand", "months": "Apr-Sep", "founded": 2005, "notes": "Themed annual exhibition on the Somerset coast"},
        {"name": "Texas SandFest", "lat": 27.8339, "lon": -97.0611, "country": "United States", "city": "Port Aransas, TX", "type": "Sand", "months": "Apr", "founded": 1997, "notes": "One of the largest sand sculpture competitions in the US"},
        {"name": "Jesolo Sand Nativity", "lat": 45.5083, "lon": 12.6472, "country": "Italy", "city": "Jesolo, Veneto", "type": "Sand", "months": "Dec-Feb", "founded": 2002, "notes": "Largest sand nativity scene in the world"},
        {"name": "Asahikawa Winter Festival", "lat": 43.7667, "lon": 142.3667, "country": "Japan", "city": "Asahikawa, Hokkaido", "type": "Snow", "months": "Feb", "founded": 1960, "notes": "Massive snow sculptures; Guinness record snow statue"},
        {"name": "Poznan Ice Festival", "lat": 52.4064, "lon": 16.9252, "country": "Poland", "city": "Poznan", "type": "Ice", "months": "Dec", "founded": 2005, "notes": "Live carving competition in city center"},
        {"name": "Icehotel (Jukkasjarvi)", "lat": 67.8500, "lon": 20.5833, "country": "Sweden", "city": "Jukkasjarvi, Lapland", "type": "Ice", "months": "Dec-Apr (rebuilt annually)", "founded": 1989, "notes": "World's first ice hotel; entirely rebuilt each winter"},
        {"name": "Sounkyo Ice Waterfall Festival", "lat": 43.7167, "lon": 143.1000, "country": "Japan", "city": "Kamikawa, Hokkaido", "type": "Ice", "months": "Jan-Mar", "founded": 1976, "notes": "Frozen waterfall illuminations in Daisetsuzan National Park"},
        {"name": "Hampton Beach Sand Sculpting Classic", "lat": 42.9078, "lon": -70.8117, "country": "United States", "city": "Hampton Beach, NH", "type": "Sand", "months": "Jun", "founded": 2000, "notes": "Master sculptors and amateur competitions on the beach"},
        {"name": "Australian Sand Sculpting Championships", "lat": -38.3950, "lon": 144.8864, "country": "Australia", "city": "Frankston, Victoria", "type": "Sand", "months": "Jan-Apr", "founded": 2005, "notes": "Southern hemisphere's largest sand sculpture exhibition"},
        {"name": "Snow Village (Lainio)", "lat": 67.4667, "lon": 23.7000, "country": "Finland", "city": "Kittila, Lapland", "type": "Snow & Ice", "months": "Dec-Apr", "founded": 1999, "notes": "Snow hotel with themed ice suites and ice restaurant"},
        {"name": "Ice and Snow World (Changchun)", "lat": 43.8800, "lon": 125.3228, "country": "China", "city": "Changchun, Jilin", "type": "Ice", "months": "Jan-Feb", "founded": 2003, "notes": "Major ice festival in northeast China"},
        {"name": "Blankenberge Sand Sculpture Festival", "lat": 51.3128, "lon": 3.1339, "country": "Belgium", "city": "Blankenberge", "type": "Sand", "months": "Jun-Sep", "founded": 2003, "notes": "Themed sand sculptures on the Belgian coast"},
        {"name": "Valloire Ice & Snow Sculpture Contest", "lat": 45.1667, "lon": 6.4278, "country": "France", "city": "Valloire, Savoie", "type": "Ice & Snow", "months": "Jan", "founded": 1992, "notes": "International competition in Alpine ski village"},
        {"name": "Ottawa Winterlude Ice Carvings", "lat": 45.4215, "lon": -75.6972, "country": "Canada", "city": "Ottawa", "type": "Ice", "months": "Feb", "founded": 1979, "notes": "Crystal Garden ice carving exhibition on Confederation Park"},
        {"name": "Jelgava Ice Sculpture Festival", "lat": 56.6514, "lon": 23.7133, "country": "Latvia", "city": "Jelgava", "type": "Ice", "months": "Feb", "founded": 2000, "notes": "Largest open-air ice sculpture festival in the Baltics"},
        {"name": "Antalya Sand Sculpture Museum", "lat": 36.8608, "lon": 30.6367, "country": "Turkey", "city": "Antalya", "type": "Sand", "months": "Year-round (covered)", "founded": 2005, "notes": "Permanent covered sand sculpture exhibition"},
        {"name": "Hwacheon Sancheoneo Ice Festival", "lat": 38.1064, "lon": 127.7089, "country": "South Korea", "city": "Hwacheon, Gangwon", "type": "Ice", "months": "Jan", "founded": 2003, "notes": "Ice fishing and ice sculpture; 1M+ visitors annually"},
    ]


def _equestrian_statues():
    return [
        {"name": "Bronze Horseman", "lat": 59.9364, "lon": 30.3022, "country": "Russia", "city": "St. Petersburg", "rider": "Peter the Great", "sculptor": "Etienne Maurice Falconet", "year": 1782, "material": "Bronze on granite", "notes": "Commissioned by Catherine the Great; rearing horse on Thunder Stone"},
        {"name": "Marcus Aurelius (original)", "lat": 41.8932, "lon": 12.4828, "country": "Italy", "city": "Rome", "rider": "Emperor Marcus Aurelius", "sculptor": "Unknown Roman", "year": 175, "material": "Bronze, gilded", "notes": "Only surviving ancient equestrian bronze; Capitoline Museums"},
        {"name": "Joan of Arc (Place des Pyramides)", "lat": 48.8627, "lon": 2.3333, "country": "France", "city": "Paris", "rider": "Joan of Arc", "sculptor": "Emmanuel Fremiet", "year": 1874, "material": "Bronze, gilded", "notes": "Near where Joan was wounded; gilded restoration"},
        {"name": "Genghis Khan Equestrian Statue", "lat": 47.8069, "lon": 107.5308, "country": "Mongolia", "city": "Tsonjin Boldog", "rider": "Genghis Khan", "sculptor": "D. Erdenebileg", "year": 2008, "material": "Stainless steel", "notes": "40 m; world's tallest equestrian statue"},
        {"name": "Gattamelata (Donatello)", "lat": 45.4015, "lon": 11.8810, "country": "Italy", "city": "Padua", "rider": "Erasmo da Narni", "sculptor": "Donatello", "year": 1453, "material": "Bronze", "notes": "First large equestrian since Marcus Aurelius; Renaissance landmark"},
        {"name": "Colleoni Monument", "lat": 45.4410, "lon": 12.3405, "country": "Italy", "city": "Venice", "rider": "Bartolomeo Colleoni", "sculptor": "Andrea del Verrocchio", "year": 1496, "material": "Bronze", "notes": "Fierce warrior expression; completed after Verrocchio died"},
        {"name": "Statue of Rani Lakshmibai", "lat": 25.4484, "lon": 78.5685, "country": "India", "city": "Jhansi", "rider": "Rani Lakshmibai", "sculptor": "Various", "year": 2001, "material": "Bronze", "notes": "Warrior queen of the 1857 Indian Rebellion"},
        {"name": "El Cid (Seville)", "lat": 37.3886, "lon": -5.9822, "country": "Spain", "city": "Seville", "rider": "El Cid (Rodrigo Diaz)", "sculptor": "Anna Hyatt Huntington", "year": 1927, "material": "Bronze", "notes": "Copy also in San Diego; medieval Spanish hero"},
        {"name": "Equestrian Statue of Cosimo I", "lat": 43.7694, "lon": 11.2553, "country": "Italy", "city": "Florence", "rider": "Cosimo I de' Medici", "sculptor": "Giambologna", "year": 1594, "material": "Bronze", "notes": "Piazza della Signoria; set the standard for equestrian monuments"},
        {"name": "George Washington (Boston Public Garden)", "lat": 42.3540, "lon": -71.0700, "country": "United States", "city": "Boston, MA", "rider": "George Washington", "sculptor": "Thomas Ball", "year": 1869, "material": "Bronze", "notes": "Overlooking the Public Garden lagoon"},
        {"name": "Statue of Simon Bolivar", "lat": 4.5981, "lon": -74.0758, "country": "Colombia", "city": "Bogota", "rider": "Simon Bolivar", "sculptor": "Pietro Tenerani", "year": 1846, "material": "Bronze", "notes": "Plaza de Bolivar; the Liberator of South America"},
        {"name": "Duke of Wellington (Glasgow)", "lat": 55.8611, "lon": -4.2500, "country": "United Kingdom", "city": "Glasgow", "rider": "Duke of Wellington", "sculptor": "Carlo Marochetti", "year": 1844, "material": "Bronze", "notes": "Famous for the traffic cone on its head"},
        {"name": "King Jose I (Lisbon)", "lat": 38.7078, "lon": -9.1364, "country": "Portugal", "city": "Lisbon", "rider": "King Jose I", "sculptor": "Machado de Castro", "year": 1775, "material": "Bronze", "notes": "Praca do Comercio; survived the 1755 earthquake aftermath"},
        {"name": "Ulysses S. Grant Memorial", "lat": 38.8894, "lon": -77.0125, "country": "United States", "city": "Washington, DC", "rider": "Ulysses S. Grant", "sculptor": "Henry Merwin Shrady", "year": 1922, "material": "Bronze, marble", "notes": "Largest equestrian statue in the US; 44 ft long"},
        {"name": "Mounted Samurai (Date Masamune)", "lat": 38.2555, "lon": 140.8563, "country": "Japan", "city": "Sendai", "rider": "Date Masamune", "sculptor": "Entaro Ogawa (original)", "year": 1935, "material": "Bronze", "notes": "One-eyed dragon of the north; overlooking Sendai from Aoba Castle"},
        {"name": "Statue of Maharana Pratap", "lat": 24.5833, "lon": 73.6833, "country": "India", "city": "Udaipur, Rajasthan", "rider": "Maharana Pratap Singh", "sculptor": "Various", "year": 1997, "material": "Bronze", "notes": "On Chetak horse; Moti Magri hilltop overlooking Lake Fateh Sagar"},
        {"name": "Frederick the Great (Unter den Linden)", "lat": 52.5167, "lon": 13.3936, "country": "Germany", "city": "Berlin", "rider": "Frederick II of Prussia", "sculptor": "Christian Daniel Rauch", "year": 1851, "material": "Bronze", "notes": "13.5 m total; elaborate base with historical figures"},
        {"name": "Anita Garibaldi Monument", "lat": 41.8912, "lon": 12.4633, "country": "Italy", "city": "Rome (Janiculum)", "rider": "Anita Garibaldi", "sculptor": "Mario Rutelli", "year": 1932, "material": "Bronze", "notes": "Rare female equestrian; wife of Giuseppe Garibaldi"},
        {"name": "Jan Zizka Statue", "lat": 50.0833, "lon": 14.4528, "country": "Czech Republic", "city": "Prague (Vitkov Hill)", "rider": "Jan Zizka", "sculptor": "Bohumil Kafka", "year": 1950, "material": "Bronze", "notes": "3rd largest equestrian statue in the world; 9 m rider + 22 m pedestal"},
        {"name": "Skanderbeg Statue", "lat": 41.3275, "lon": 19.8187, "country": "Albania", "city": "Tirana", "rider": "Gjergj Kastrioti Skanderbeg", "sculptor": "Odhise Paskali", "year": 1968, "material": "Bronze", "notes": "Albanian national hero; Skanderbeg Square"},
        {"name": "Prince Eugene of Savoy (Budapest)", "lat": 47.4969, "lon": 19.0394, "country": "Hungary", "city": "Budapest", "rider": "Prince Eugene of Savoy", "sculptor": "Jozsef Rona", "year": 1900, "material": "Bronze", "notes": "Buda Castle terrace; celebrates liberation from Ottoman rule"},
        {"name": "Robert the Bruce (Bannockburn)", "lat": 56.0892, "lon": -3.9089, "country": "United Kingdom", "city": "Stirling, Scotland", "rider": "Robert the Bruce", "sculptor": "Pilkington Jackson", "year": 1964, "material": "Bronze", "notes": "Battle of Bannockburn site; Scottish Independence"},
        {"name": "Mounted Policeman (RCMP Musical Ride)", "lat": 45.3235, "lon": -75.6699, "country": "Canada", "city": "Ottawa", "rider": "RCMP officer", "sculptor": "Rich Fougere", "year": 1992, "material": "Bronze", "notes": "Tribute to the Royal Canadian Mounted Police tradition"},
        {"name": "Andrew Jackson (Lafayette Square)", "lat": 38.9003, "lon": -77.0367, "country": "United States", "city": "Washington, DC", "rider": "Andrew Jackson", "sculptor": "Clark Mills", "year": 1853, "material": "Bronze", "notes": "First equestrian statue in US; rearing horse balanced on hind legs"},
        {"name": "Vercingetorix (Alesia)", "lat": 47.5361, "lon": 4.5003, "country": "France", "city": "Alise-Sainte-Reine", "rider": "Vercingetorix (standing, not mounted)", "sculptor": "Aime Millet", "year": 1865, "material": "Copper", "notes": "Gallic chieftain at defeat site; commissioned by Napoleon III"},
    ]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _render_detail_expanders(df, mode, color):
    """Render an expander for each location with all details."""
    icon = _MODE_ICONS.get(mode, "\U0001f5ff")
    skip_keys = {"lat", "lon"}

    for idx, row in df.iterrows():
        name = str(row.get("name", f"Site {idx + 1}"))
        country = str(row.get("country", ""))
        label = f"{icon} {name}"
        if country:
            label += f" ({country})"

        with st.expander(label, expanded=False):
            detail_cols = st.columns([1, 2])
            with detail_cols[0]:
                st.markdown(
                    f'<div style="background:{color}22;border-left:3px solid {color};'
                    f'padding:8px 12px;border-radius:4px;">'
                    f'<b style="color:{color};">{html_module.escape(name)}</b>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(f"**Latitude:** {row['lat']:.4f}")
                st.markdown(f"**Longitude:** {row['lon']:.4f}")

            with detail_cols[1]:
                for key, val in row.items():
                    if key in skip_keys or key == "name" or val is None or str(val).strip() == "":
                        continue
                    pretty_key = str(key).replace("_", " ").title()
                    st.markdown(f"**{pretty_key}:** {val}")


def _build_popup_html(row, mode):
    """Build a rich HTML popup for a Folium marker."""
    name = html_module.escape(str(row.get("name", "Unknown")))
    color = _MODE_COLORS.get(mode, "#06b6d4")

    lines = [
        f'<div style="font-family:Arial,sans-serif;min-width:220px;max-width:300px;">',
        f'<h4 style="margin:0 0 6px 0;color:{color};font-size:14px;">{name}</h4>',
    ]

    skip_keys = {"name", "lat", "lon"}
    for key, val in row.items():
        if key in skip_keys or val is None or val == "":
            continue
        label = html_module.escape(str(key).replace("_", " ").title())
        value = html_module.escape(str(val))
        lines.append(
            f'<div style="margin:2px 0;font-size:12px;">'
            f'<b style="color:#ccc;">{label}:</b> '
            f'<span style="color:#eee;">{value}</span></div>'
        )

    lines.append("</div>")
    return "\n".join(lines)


def _build_map(df, mode, color):
    """Build a Folium map with CircleMarkers for the given DataFrame."""
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles="CartoDB dark_matter",
    )

    for _, row in df.iterrows():
        popup_html = _build_popup_html(row.to_dict(), mode)
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=html_module.escape(str(row.get("name", ""))),
        ).add_to(m)

    return m


def _render_stats(df, mode):
    """Render summary metric cards for the current mode."""
    cols = st.columns(4)

    with cols[0]:
        st.metric("Total Sites", len(df))

    if "country" in df.columns:
        with cols[1]:
            st.metric("Countries", df["country"].nunique())

    if "height_m" in df.columns:
        with cols[2]:
            st.metric("Tallest (m)", int(df["height_m"].max()))
        with cols[3]:
            st.metric("Avg Height (m)", f"{df['height_m'].mean():.1f}")
    elif "year" in df.columns:
        numeric_years = pd.to_numeric(df["year"], errors="coerce").dropna()
        if len(numeric_years) > 0:
            with cols[2]:
                st.metric("Oldest Year", int(numeric_years.min()))
            with cols[3]:
                st.metric("Newest Year", int(numeric_years.max()))
    elif "founded" in df.columns:
        with cols[2]:
            st.metric("Oldest Founded", int(df["founded"].min()))
        with cols[3]:
            st.metric("Newest Founded", int(df["founded"].max()))
    elif "area_acres" in df.columns:
        valid_areas = df[df["area_acres"] > 0]["area_acres"]
        if len(valid_areas) > 0:
            with cols[2]:
                st.metric("Largest (acres)", int(valid_areas.max()))
            with cols[3]:
                st.metric("Avg Area (acres)", f"{valid_areas.mean():.0f}")
    else:
        if "country" not in df.columns:
            with cols[1]:
                st.metric("Data Points", len(df.columns))


# ============================================================================
# MAIN RENDER FUNCTION
# ============================================================================

def render_sculpture_maps_tab():
    """Render the Sculpture & Statues Explorer tab in TerraScout AI."""

    # ---- Header ----
    st.markdown(
        '<div class="tab-header violet">'
        "<h4>\U0001f5ff Sculpture & Statues Explorer</h4>"
        "<p>World tallest statues, sculpture parks, classical masterpieces & monumental art</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    mode = st.selectbox(
        "\U0001f5ff Select Map Mode",
        _MODE_LIST,
        key="sculpture_maps_mode",
    )
    color = _MODE_COLORS.get(mode, "#06b6d4")

    # ---- Mode description ----
    desc = _MODE_DESCRIPTIONS.get(mode, "")
    if desc:
        icon = _MODE_ICONS.get(mode, "\U0001f5ff")
        st.info(f"{icon} **{mode}** -- {desc}")

    # ---- Data loader dispatch ----
    _data_loaders = {
        "World's Tallest Statues": _worlds_tallest_statues,
        "Classical Greek & Roman Sculptures": _classical_greek_roman,
        "Renaissance Masterpieces": _renaissance_masterpieces,
        "Modern Sculpture Parks": _modern_sculpture_parks,
        "Ancient Megalithic Monuments": _ancient_megalithic,
        "Buddhist & Hindu Monumental Art": _buddhist_hindu_monumental,
        "Public Art & Urban Sculptures": _public_art_urban,
        "Stone Carving Traditions": _stone_carving_traditions,
        "Ice & Sand Sculpture Festivals": _ice_sand_festivals,
        "Famous Equestrian Statues": _equestrian_statues,
    }
    loader = _data_loaders.get(mode, _worlds_tallest_statues)
    df = pd.DataFrame(loader())

    # ---- Filters ----
    st.markdown("---")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        search_query = st.text_input(
            "Search by name",
            value="",
            placeholder="Type to filter locations...",
            key="sculpture_text_search",
        )
    with filter_col2:
        if "country" in df.columns:
            all_countries = sorted(df["country"].unique().tolist())
            selected_countries = st.multiselect(
                "Filter by country",
                options=all_countries,
                default=all_countries,
                key="sculpture_country_filter",
            )
        else:
            selected_countries = None

    # Apply filters
    if search_query and search_query.strip():
        df = df[df["name"].str.contains(search_query.strip(), case=False, na=False)]
    if selected_countries is not None and selected_countries:
        df = df[df["country"].isin(selected_countries)]
    df = df.reset_index(drop=True)

    if df.empty:
        st.warning(
            "No locations match the current filters. "
            "Adjust your search or country selection."
        )
        return

    # ---- Stats row ----
    st.markdown("---")
    _render_stats(df, mode)

    # ---- Map ----
    st.markdown("---")
    st.subheader(f"Map: {mode}")
    m = _build_map(df, mode, color)
    st_html(m._repr_html_(), height=500)

    # ---- Detail expanders ----
    st.markdown("---")
    st.subheader(f"Location Details ({len(df)} sites)")
    _render_detail_expanders(df, mode, color)

    # ---- Country distribution chart ----
    if "country" in df.columns and df["country"].nunique() > 1:
        st.markdown("---")
        st.subheader("Distribution by Country")
        country_counts = df["country"].value_counts().head(15)
        chart_df = pd.DataFrame({
            "Country": country_counts.index,
            "Count": country_counts.values,
        })
        st.bar_chart(chart_df.set_index("Country"), color=color, height=320)

    # ---- Data table ----
    st.markdown("---")
    st.subheader(f"Data Table ({len(df)} sites)")
    st.dataframe(df, use_container_width=True)

    # ---- CSV download ----
    csv_data = df.to_csv(index=False).encode("utf-8")
    filename = mode.lower().replace(" ", "_").replace("&", "and").replace("'", "") + ".csv"
    st.download_button(
        label=f"Download {mode} CSV",
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=f"sculpture_csv_{mode}",
    )

    # ---- Height/size ranking for applicable modes ----
    if "height_m" in df.columns:
        st.markdown("---")
        st.subheader("Height Ranking")
        ranked = df[df["height_m"] > 0].sort_values("height_m", ascending=False).head(10)
        if not ranked.empty:
            ranking_df = pd.DataFrame({
                "Name": ranked["name"].values,
                "Height (m)": ranked["height_m"].values,
            })
            st.bar_chart(
                ranking_df.set_index("Name"),
                color=color,
                height=350,
            )

    # ---- Footer ----
    st.caption(
        f"Showing {len(df)} curated locations for **{mode}**. "
        "Data is hardcoded from reputable sources including UNESCO, "
        "museum catalogs, and art history references."
    )
