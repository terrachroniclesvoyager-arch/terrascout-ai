# -*- coding: utf-8 -*-
"""
TerraScout AI - Opera & Theater Maps Module
Provides 10 curated map modes covering opera houses, theaters, concert halls,
ancient amphitheaters, comedy venues, film studios, and performing arts
landmarks worldwide.  All data is hardcoded (no external API required).
"""

import html as html_module
import io

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as st_html


# ============================================================================
# Color palette per mode
# ============================================================================

MODE_COLORS = {
    "Greatest Opera Houses": "#e74c3c",
    "Shakespeare's World": "#8b5cf6",
    "Ancient Theaters": "#d4a017",
    "Broadway & West End": "#f59e0b",
    "Puppet & Mask Theater": "#ec4899",
    "Circus & Variety": "#f97316",
    "Famous Composers' Birthplaces": "#06b6d4",
    "Concert Halls": "#3b82f6",
    "Film & TV Studios": "#10b981",
    "Comedy & Cabaret": "#a855f7",
}

# ============================================================================
# 1. Greatest Opera Houses (25)
# ============================================================================

OPERA_HOUSES = [
    {"name": "Teatro alla Scala", "lat": 45.4654, "lon": 9.1890, "city": "Milan", "country": "Italy", "year": 1778, "seats": 2030, "style": "Neoclassical", "famous_for": "Verdi premieres, world-renowned opera"},
    {"name": "Vienna State Opera", "lat": 48.2035, "lon": 16.3689, "city": "Vienna", "country": "Austria", "year": 1869, "seats": 2284, "style": "Neo-Renaissance", "famous_for": "Vienna Philharmonic, New Year concerts"},
    {"name": "Metropolitan Opera House", "lat": 40.7725, "lon": -73.9835, "city": "New York", "country": "USA", "year": 1966, "seats": 3800, "style": "Modernist", "famous_for": "Largest classical music organization in N. America"},
    {"name": "Royal Opera House", "lat": 51.5129, "lon": -0.1224, "city": "London", "country": "UK", "year": 1858, "seats": 2256, "style": "Victorian / Neoclassical", "famous_for": "Royal Ballet, world-class opera"},
    {"name": "Sydney Opera House", "lat": -33.8568, "lon": 151.2153, "city": "Sydney", "country": "Australia", "year": 1973, "seats": 5738, "style": "Expressionist / Modernist", "famous_for": "Iconic sail-shaped roof, UNESCO site"},
    {"name": "Bolshoi Theatre", "lat": 55.7601, "lon": 37.6186, "city": "Moscow", "country": "Russia", "year": 1825, "seats": 2150, "style": "Neoclassical", "famous_for": "Bolshoi Ballet, Russian opera tradition"},
    {"name": "Palais Garnier", "lat": 48.8720, "lon": 2.3316, "city": "Paris", "country": "France", "year": 1875, "seats": 1979, "style": "Beaux-Arts / Second Empire", "famous_for": "Phantom of the Opera inspiration"},
    {"name": "Teatro di San Carlo", "lat": 40.8376, "lon": 14.2497, "city": "Naples", "country": "Italy", "year": 1737, "seats": 1386, "style": "Baroque / Neoclassical", "famous_for": "Oldest active opera house in the world"},
    {"name": "La Fenice", "lat": 45.4338, "lon": 12.3341, "city": "Venice", "country": "Italy", "year": 1792, "seats": 1000, "style": "Neoclassical", "famous_for": "Risen from fire three times (the Phoenix)"},
    {"name": "Semperoper", "lat": 51.0543, "lon": 13.7352, "city": "Dresden", "country": "Germany", "year": 1841, "seats": 1300, "style": "Neo-Renaissance", "famous_for": "Richard Strauss premieres"},
    {"name": "Teatro Colon", "lat": -34.6010, "lon": -58.3833, "city": "Buenos Aires", "country": "Argentina", "year": 1908, "seats": 2487, "style": "Eclectic (Italian Renaissance)", "famous_for": "Outstanding acoustics, South American jewel"},
    {"name": "Bavarian State Opera", "lat": 48.1397, "lon": 11.5786, "city": "Munich", "country": "Germany", "year": 1818, "seats": 2100, "style": "Neoclassical", "famous_for": "Wagner premieres, Munich Opera Festival"},
    {"name": "Gran Teatre del Liceu", "lat": 41.3809, "lon": 2.1734, "city": "Barcelona", "country": "Spain", "year": 1847, "seats": 2292, "style": "Neoclassical", "famous_for": "Largest opera house in Spain"},
    {"name": "Royal Swedish Opera", "lat": 59.3298, "lon": 18.0700, "city": "Stockholm", "country": "Sweden", "year": 1898, "seats": 1200, "style": "Neo-Baroque", "famous_for": "Historic royal patronage"},
    {"name": "Mariinsky Theatre", "lat": 59.9256, "lon": 30.2961, "city": "St. Petersburg", "country": "Russia", "year": 1860, "seats": 1625, "style": "Neo-Byzantine", "famous_for": "Tchaikovsky, Mussorgsky premieres"},
    {"name": "Operaen (Copenhagen Opera House)", "lat": 55.6815, "lon": 12.6013, "city": "Copenhagen", "country": "Denmark", "year": 2005, "seats": 1703, "style": "Modern / Minimalist", "famous_for": "One of most expensive opera houses ever built"},
    {"name": "Oslo Opera House", "lat": 59.9075, "lon": 10.7533, "city": "Oslo", "country": "Norway", "year": 2008, "seats": 1364, "style": "Modernist", "famous_for": "Walk-on rooftop, angular iceberg design"},
    {"name": "Teatro Massimo", "lat": 38.1200, "lon": 13.3574, "city": "Palermo", "country": "Italy", "year": 1897, "seats": 1350, "style": "Neoclassical", "famous_for": "Largest opera house in Italy, Godfather III scene"},
    {"name": "Zurich Opera House", "lat": 47.3653, "lon": 8.5469, "city": "Zurich", "country": "Switzerland", "year": 1891, "seats": 1100, "style": "Neo-Baroque", "famous_for": "Consistently top-ranked globally"},
    {"name": "National Centre for the Performing Arts", "lat": 39.9037, "lon": 116.3835, "city": "Beijing", "country": "China", "year": 2007, "seats": 5452, "style": "Ultra-modern (egg shape)", "famous_for": "The Egg: titanium and glass dome"},
    {"name": "Opera Bastille", "lat": 48.8517, "lon": 2.3692, "city": "Paris", "country": "France", "year": 1989, "seats": 2723, "style": "Modernist", "famous_for": "Main venue of Paris National Opera"},
    {"name": "Teatro Real", "lat": 40.4181, "lon": -3.7108, "city": "Madrid", "country": "Spain", "year": 1850, "seats": 1746, "style": "Neoclassical", "famous_for": "Royal opera house of Spain"},
    {"name": "Hungarian State Opera House", "lat": 47.5024, "lon": 19.0583, "city": "Budapest", "country": "Hungary", "year": 1884, "seats": 1261, "style": "Neo-Renaissance", "famous_for": "Designed by Miklos Ybl, ornate interior"},
    {"name": "Staatsoper Unter den Linden", "lat": 52.5167, "lon": 13.3948, "city": "Berlin", "country": "Germany", "year": 1742, "seats": 1356, "style": "Baroque / Neoclassical", "famous_for": "Frederick the Great's opera house"},
    {"name": "La Monnaie", "lat": 50.8504, "lon": 4.3554, "city": "Brussels", "country": "Belgium", "year": 1700, "seats": 1152, "style": "Neoclassical", "famous_for": "Belgian revolution started here in 1830"},
    {"name": "Finnish National Opera", "lat": 60.1825, "lon": 24.9281, "city": "Helsinki", "country": "Finland", "year": 1993, "seats": 1350, "style": "Modernist", "famous_for": "White granite lakeside opera house"},
    {"name": "National Opera of Ukraine", "lat": 50.4513, "lon": 30.5131, "city": "Kyiv", "country": "Ukraine", "year": 1901, "seats": 1300, "style": "Neo-Renaissance", "famous_for": "Third largest in Europe by volume"},
    {"name": "Grand Theatre Warsaw", "lat": 52.2414, "lon": 21.0070, "city": "Warsaw", "country": "Poland", "year": 1833, "seats": 1841, "style": "Neoclassical", "famous_for": "One of the largest theater buildings in Europe"},
    {"name": "Margravial Opera House", "lat": 49.9444, "lon": 11.5781, "city": "Bayreuth", "country": "Germany", "year": 1748, "seats": 500, "style": "Baroque", "famous_for": "UNESCO site, finest Baroque theater surviving"},
    {"name": "Bayreuth Festspielhaus", "lat": 49.9608, "lon": 11.5783, "city": "Bayreuth", "country": "Germany", "year": 1876, "seats": 1974, "style": "Purpose-built Wagnerian", "famous_for": "Built by Wagner for The Ring Cycle"},
]

# ============================================================================
# 2. Shakespeare's World (20)
# ============================================================================

SHAKESPEARE_WORLD = [
    {"name": "Shakespeare's Globe Theatre", "lat": 51.5081, "lon": -0.0972, "city": "London", "country": "UK", "year": 1997, "type": "Reconstruction", "connection": "Rebuilt replica of 1599 original"},
    {"name": "Original Globe Theatre Site", "lat": 51.5075, "lon": -0.0950, "city": "London", "country": "UK", "year": 1599, "type": "Historic Site", "connection": "Where Shakespeare's plays were first performed"},
    {"name": "Shakespeare's Birthplace", "lat": 52.1936, "lon": -1.7078, "city": "Stratford-upon-Avon", "country": "UK", "year": 1564, "type": "Birthplace", "connection": "Born here April 23, 1564"},
    {"name": "Anne Hathaway's Cottage", "lat": 52.1988, "lon": -1.7246, "city": "Stratford-upon-Avon", "country": "UK", "year": 1463, "type": "Historic Home", "connection": "Wife's family home before marriage"},
    {"name": "Holy Trinity Church", "lat": 52.1890, "lon": -1.7075, "city": "Stratford-upon-Avon", "country": "UK", "year": 1210, "type": "Burial Site", "connection": "Shakespeare's burial place"},
    {"name": "Royal Shakespeare Theatre", "lat": 52.1920, "lon": -1.7057, "city": "Stratford-upon-Avon", "country": "UK", "year": 1932, "type": "Theater", "connection": "Royal Shakespeare Company's home"},
    {"name": "Kronborg Castle (Elsinore)", "lat": 56.0390, "lon": 12.6218, "city": "Helsingor", "country": "Denmark", "year": 1420, "type": "Hamlet Setting", "connection": "Inspiration for Hamlet's Elsinore castle"},
    {"name": "Juliet's House (Casa di Giulietta)", "lat": 45.4421, "lon": 10.9988, "city": "Verona", "country": "Italy", "year": 1300, "type": "Romeo & Juliet", "connection": "Legendary balcony of Juliet"},
    {"name": "Verona Arena", "lat": 45.4390, "lon": 10.9943, "city": "Verona", "country": "Italy", "year": 30, "type": "Performance Venue", "connection": "Setting of Romeo & Juliet; hosts opera"},
    {"name": "Tower of London", "lat": 51.5081, "lon": -0.0759, "city": "London", "country": "UK", "year": 1066, "type": "Richard III Setting", "connection": "Where Richard III imprisoned the princes"},
    {"name": "Windsor Castle", "lat": 51.4839, "lon": -0.6044, "city": "Windsor", "country": "UK", "year": 1070, "type": "Merry Wives Setting", "connection": "Setting of The Merry Wives of Windsor"},
    {"name": "Glamis Castle", "lat": 56.6168, "lon": -3.0003, "city": "Glamis", "country": "UK", "year": 1372, "type": "Macbeth Setting", "connection": "Traditionally linked to Macbeth"},
    {"name": "Forest of Arden (Ardennes)", "lat": 50.1000, "lon": 5.5000, "city": "Ardennes", "country": "Belgium", "year": 0, "type": "As You Like It", "connection": "Inspiration for the Forest of Arden"},
    {"name": "Athens Acropolis", "lat": 37.9715, "lon": 23.7257, "city": "Athens", "country": "Greece", "year": -447, "type": "Midsummer Night's Dream", "connection": "Setting of A Midsummer Night's Dream"},
    {"name": "Alexandria (Antony & Cleopatra)", "lat": 31.2001, "lon": 29.9187, "city": "Alexandria", "country": "Egypt", "year": -331, "type": "Antony & Cleopatra", "connection": "Setting of Antony and Cleopatra"},
    {"name": "Rome Capitoline Hill", "lat": 41.8931, "lon": 12.4828, "city": "Rome", "country": "Italy", "year": -509, "type": "Julius Caesar", "connection": "Setting of Julius Caesar, Coriolanus"},
    {"name": "Venice Rialto Bridge", "lat": 45.4380, "lon": 12.3360, "city": "Venice", "country": "Italy", "year": 1591, "type": "Merchant of Venice", "connection": "Setting of The Merchant of Venice"},
    {"name": "Rossillion (Roussillon)", "lat": 43.8508, "lon": 3.7942, "city": "Roussillon", "country": "France", "year": 0, "type": "All's Well Setting", "connection": "Setting of All's Well That Ends Well"},
    {"name": "Inverness Castle", "lat": 57.4779, "lon": -4.2247, "city": "Inverness", "country": "UK", "year": 1057, "type": "Macbeth Setting", "connection": "Macbeth's castle in the play"},
    {"name": "Ephesus Ancient City", "lat": 37.9394, "lon": 27.3417, "city": "Selcuk", "country": "Turkey", "year": -1000, "type": "Comedy of Errors", "connection": "Setting of The Comedy of Errors"},
    {"name": "Dunsinane Hill", "lat": 56.5000, "lon": -3.3000, "city": "Perth", "country": "UK", "year": 0, "type": "Macbeth Setting", "connection": "Birnam Wood comes to Dunsinane in Macbeth"},
    {"name": "Messina (Much Ado About Nothing)", "lat": 38.1937, "lon": 15.5540, "city": "Messina", "country": "Italy", "year": 0, "type": "Much Ado Setting", "connection": "Setting of Much Ado About Nothing"},
    {"name": "Illyria / Dubrovnik", "lat": 42.6507, "lon": 18.0944, "city": "Dubrovnik", "country": "Croatia", "year": 0, "type": "Twelfth Night", "connection": "Adriatic coast inspired Illyria in Twelfth Night"},
    {"name": "Blackfriars Theatre Site", "lat": 51.5117, "lon": -0.1040, "city": "London", "country": "UK", "year": 1596, "type": "Historic Site", "connection": "Indoor theater used by Shakespeare's company"},
]

# ============================================================================
# 3. Ancient Theaters (22)
# ============================================================================

ANCIENT_THEATERS = [
    {"name": "Theatre of Epidaurus", "lat": 37.5961, "lon": 23.0791, "city": "Epidaurus", "country": "Greece", "year": -340, "capacity": 14000, "condition": "Excellent", "famous_for": "Perfect acoustics, still hosts performances"},
    {"name": "Theatre of Dionysus", "lat": 37.9700, "lon": 23.7275, "city": "Athens", "country": "Greece", "year": -534, "capacity": 17000, "condition": "Ruins", "famous_for": "Birthplace of Greek tragedy"},
    {"name": "Odeon of Herodes Atticus", "lat": 37.9707, "lon": 23.7245, "city": "Athens", "country": "Greece", "year": 161, "capacity": 5000, "condition": "Restored", "famous_for": "Still used for Athens Festival performances"},
    {"name": "Theatre of Aspendos", "lat": 36.9390, "lon": 31.1720, "city": "Aspendos", "country": "Turkey", "year": 155, "capacity": 15000, "condition": "Excellent", "famous_for": "Best-preserved Roman theater"},
    {"name": "Roman Theatre of Orange", "lat": 44.1362, "lon": 4.8088, "city": "Orange", "country": "France", "year": 25, "capacity": 9000, "condition": "Excellent", "famous_for": "Best-preserved Roman theater wall in Europe"},
    {"name": "Theatre at Delphi", "lat": 38.4824, "lon": 22.5013, "city": "Delphi", "country": "Greece", "year": -400, "capacity": 5000, "condition": "Ruins", "famous_for": "Spectacular mountain setting, oracle site"},
    {"name": "Colosseum (Flavian Amphitheatre)", "lat": 41.8902, "lon": 12.4922, "city": "Rome", "country": "Italy", "year": 80, "capacity": 50000, "condition": "Partially restored", "famous_for": "Largest ancient amphitheatre ever built"},
    {"name": "Theatre of Leptis Magna", "lat": 32.6380, "lon": 14.2896, "city": "Al-Khums", "country": "Libya", "year": 1, "capacity": 16000, "condition": "Ruins", "famous_for": "Roman Africa's grandest theater"},
    {"name": "Roman Theatre of Merida", "lat": 38.9153, "lon": -6.3387, "city": "Merida", "country": "Spain", "year": -15, "capacity": 6000, "condition": "Restored", "famous_for": "Classical drama festival venue"},
    {"name": "Amphitheatre of El Jem", "lat": 35.2962, "lon": 10.7069, "city": "El Jem", "country": "Tunisia", "year": 238, "capacity": 35000, "condition": "Good", "famous_for": "Third largest Roman amphitheatre"},
    {"name": "Theatre of Pergamon", "lat": 39.1313, "lon": 27.1780, "city": "Bergama", "country": "Turkey", "year": -197, "capacity": 10000, "condition": "Ruins", "famous_for": "Steepest ancient Greek theater"},
    {"name": "Theatre of Taormina", "lat": 37.8522, "lon": 15.2922, "city": "Taormina", "country": "Italy", "year": -300, "capacity": 5400, "condition": "Restored", "famous_for": "Stunning Mt. Etna and sea backdrop"},
    {"name": "Jerash South Theatre", "lat": 32.2784, "lon": 35.8914, "city": "Jerash", "country": "Jordan", "year": 90, "capacity": 3000, "condition": "Excellent", "famous_for": "Best preserved of Gerasa's theaters"},
    {"name": "Bosra Roman Theatre", "lat": 32.5163, "lon": 36.4817, "city": "Bosra", "country": "Syria", "year": 150, "capacity": 15000, "condition": "Good", "famous_for": "Enclosed in medieval citadel walls"},
    {"name": "Arena of Nimes", "lat": 43.8345, "lon": 4.3596, "city": "Nimes", "country": "France", "year": 70, "capacity": 24000, "condition": "Excellent", "famous_for": "Best-preserved Roman arena, still used for events"},
    {"name": "Theatre of Pompeii", "lat": 40.7493, "lon": 14.4863, "city": "Pompeii", "country": "Italy", "year": -200, "capacity": 5000, "condition": "Ruins", "famous_for": "Preserved by Vesuvius eruption 79 AD"},
    {"name": "Amphitheatre of Pula", "lat": 44.8733, "lon": 13.8500, "city": "Pula", "country": "Croatia", "year": 27, "capacity": 23000, "condition": "Excellent", "famous_for": "6th largest Roman arena, hosts concerts"},
    {"name": "Roman Theatre of Amman", "lat": 31.9516, "lon": 35.9385, "city": "Amman", "country": "Jordan", "year": 138, "capacity": 6000, "condition": "Restored", "famous_for": "Cut into hillside, city center landmark"},
    {"name": "Odeion of Gortyna", "lat": 35.0610, "lon": 24.9460, "city": "Gortyna", "country": "Greece", "year": -100, "capacity": 3000, "condition": "Ruins", "famous_for": "Site of ancient Cretan law codes"},
    {"name": "Theatre of Sabratha", "lat": 32.7930, "lon": 12.4840, "city": "Sabratha", "country": "Libya", "year": 175, "capacity": 5000, "condition": "Partially restored", "famous_for": "Ornate three-story stage wall"},
    {"name": "Theatre of Miletus", "lat": 37.5310, "lon": 27.2780, "city": "Miletus", "country": "Turkey", "year": -300, "capacity": 15000, "condition": "Ruins", "famous_for": "Impressive Hellenistic theater on the coast"},
    {"name": "Verona Arena", "lat": 45.4390, "lon": 10.9943, "city": "Verona", "country": "Italy", "year": 30, "capacity": 30000, "condition": "Excellent", "famous_for": "World-famous summer opera festival"},
    {"name": "Theatre of Ephesus", "lat": 37.9410, "lon": 27.3420, "city": "Selcuk", "country": "Turkey", "year": -300, "capacity": 25000, "condition": "Partially restored", "famous_for": "St. Paul preached here, largest in Anatolia"},
    {"name": "Theatre of Segesta", "lat": 37.9420, "lon": 12.8360, "city": "Segesta", "country": "Italy", "year": -300, "capacity": 4000, "condition": "Good", "famous_for": "Overlooking a valley in western Sicily"},
    {"name": "Butrint Theatre", "lat": 39.7440, "lon": 20.0200, "city": "Butrint", "country": "Albania", "year": -300, "capacity": 2500, "condition": "Ruins", "famous_for": "UNESCO site, Roman-era theater in Albania"},
]

# ============================================================================
# 4. Broadway & West End (22)
# ============================================================================

BROADWAY_WEST_END = [
    {"name": "Majestic Theatre", "lat": 40.7590, "lon": -73.9875, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1645, "famous_show": "The Phantom of the Opera"},
    {"name": "Gershwin Theatre", "lat": 40.7623, "lon": -73.9845, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1933, "famous_show": "Wicked"},
    {"name": "Richard Rodgers Theatre", "lat": 40.7596, "lon": -73.9865, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1319, "famous_show": "Hamilton"},
    {"name": "New Amsterdam Theatre", "lat": 40.7563, "lon": -73.9879, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1702, "famous_show": "Aladdin / The Lion King"},
    {"name": "Winter Garden Theatre", "lat": 40.7620, "lon": -73.9847, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1526, "famous_show": "Cats / Beetlejuice"},
    {"name": "St. James Theatre", "lat": 40.7584, "lon": -73.9873, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1623, "famous_show": "Oklahoma! / The Producers"},
    {"name": "Shubert Theatre", "lat": 40.7579, "lon": -73.9870, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1460, "famous_show": "A Chorus Line"},
    {"name": "Palace Theatre", "lat": 40.7579, "lon": -73.9872, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1743, "famous_show": "Harry Potter and the Cursed Child"},
    {"name": "Lyceum Theatre", "lat": 40.7575, "lon": -73.9860, "city": "New York", "country": "USA", "district": "Broadway", "seats": 922, "famous_show": "Oldest continually active Broadway theater"},
    {"name": "Her Majesty's Theatre", "lat": 51.5094, "lon": -0.1322, "city": "London", "country": "UK", "district": "West End", "seats": 1216, "famous_show": "The Phantom of the Opera"},
    {"name": "Theatre Royal Drury Lane", "lat": 51.5125, "lon": -0.1205, "city": "London", "country": "UK", "district": "West End", "seats": 2196, "famous_show": "Oldest theater in continuous use (1663)"},
    {"name": "London Palladium", "lat": 51.5146, "lon": -0.1403, "city": "London", "country": "UK", "district": "West End", "seats": 2286, "famous_show": "The Wizard of Oz / Joseph"},
    {"name": "Apollo Victoria Theatre", "lat": 51.4958, "lon": -0.1437, "city": "London", "country": "UK", "district": "West End", "seats": 2328, "famous_show": "Wicked"},
    {"name": "Prince Edward Theatre", "lat": 51.5138, "lon": -0.1309, "city": "London", "country": "UK", "district": "West End", "seats": 1666, "famous_show": "Miss Saigon / Mary Poppins"},
    {"name": "Old Vic Theatre", "lat": 51.5022, "lon": -0.1096, "city": "London", "country": "UK", "district": "West End", "seats": 1067, "famous_show": "Founded National Theatre, Kevin Spacey era"},
    {"name": "Princess Theatre", "lat": -37.8100, "lon": 144.9690, "city": "Melbourne", "country": "Australia", "district": "Melbourne", "seats": 1488, "famous_show": "Harry Potter and the Cursed Child"},
    {"name": "Capitol Theatre", "lat": -33.8826, "lon": 151.2048, "city": "Sydney", "country": "Australia", "district": "Sydney", "seats": 2094, "famous_show": "Hamilton / Les Miserables"},
    {"name": "Tokyu Theatre Orb", "lat": 35.6590, "lon": 139.7020, "city": "Tokyo", "country": "Japan", "district": "Tokyo", "seats": 1972, "famous_show": "Broadway touring shows"},
    {"name": "Deutsches Theater Berlin", "lat": 52.5243, "lon": 13.3876, "city": "Berlin", "country": "Germany", "district": "Berlin", "seats": 600, "famous_show": "Max Reinhardt's legendary theater"},
    {"name": "Chatelet Theatre", "lat": 48.8580, "lon": 2.3475, "city": "Paris", "country": "France", "district": "Paris", "seats": 2500, "famous_show": "An American in Paris"},
    {"name": "Mogador Theatre", "lat": 48.8742, "lon": 2.3382, "city": "Paris", "country": "France", "district": "Paris", "seats": 1600, "famous_show": "French adaptations of musicals"},
    {"name": "Stage Theater an der Elbe", "lat": 53.5394, "lon": 9.9300, "city": "Hamburg", "country": "Germany", "district": "Hamburg", "seats": 1850, "famous_show": "The Lion King (German)"},
    {"name": "Minskoff Theatre", "lat": 40.7580, "lon": -73.9862, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1710, "famous_show": "The Lion King"},
    {"name": "Al Hirschfeld Theatre", "lat": 40.7593, "lon": -73.9888, "city": "New York", "country": "USA", "district": "Broadway", "seats": 1437, "famous_show": "Moulin Rouge! The Musical"},
    {"name": "Victoria Palace Theatre", "lat": 51.4978, "lon": -0.1434, "city": "London", "country": "UK", "district": "West End", "seats": 1550, "famous_show": "Hamilton (London)"},
    {"name": "Donmar Warehouse", "lat": 51.5132, "lon": -0.1250, "city": "London", "country": "UK", "district": "West End", "seats": 251, "famous_show": "Intimate avant-garde productions"},
]

# ============================================================================
# 5. Puppet & Mask Theater (17)
# ============================================================================

PUPPET_MASK_THEATER = [
    {"name": "National Bunraku Theatre", "lat": 34.6690, "lon": 135.5157, "city": "Osaka", "country": "Japan", "tradition": "Bunraku", "year": 1984, "description": "Japan's premier puppet theater, UNESCO heritage art form"},
    {"name": "Wayang Museum", "lat": -6.1344, "lon": 106.8133, "city": "Jakarta", "country": "Indonesia", "tradition": "Wayang", "year": 1975, "description": "Shadow puppet heritage of Java and Bali"},
    {"name": "Salzburg Marionette Theatre", "lat": 47.8010, "lon": 13.0425, "city": "Salzburg", "country": "Austria", "tradition": "Marionette", "year": 1913, "description": "Oldest marionette theater, performs Mozart operas"},
    {"name": "Bread and Puppet Theater", "lat": 44.5620, "lon": -72.1452, "city": "Glover, VT", "country": "USA", "tradition": "Giant Puppets", "year": 1963, "description": "Political giant puppet performances, museum"},
    {"name": "TOPIC (Int'l Puppet Centre)", "lat": 43.1714, "lon": -2.4220, "city": "Tolosa", "country": "Spain", "tradition": "International", "year": 1987, "description": "One of Europe's largest puppet collections"},
    {"name": "Commedia dell'Arte - Venice", "lat": 45.4408, "lon": 12.3155, "city": "Venice", "country": "Italy", "tradition": "Commedia dell'Arte", "year": 1550, "description": "Birthplace of masked improvisational comedy"},
    {"name": "National Marionette Theatre Prague", "lat": 50.0879, "lon": 14.4178, "city": "Prague", "country": "Czech Republic", "tradition": "Czech Marionettes", "year": 1991, "description": "Don Giovanni and other operas with marionettes"},
    {"name": "Obraztsov Puppet Theatre", "lat": 55.7720, "lon": 37.6156, "city": "Moscow", "country": "Russia", "tradition": "Rod Puppets", "year": 1931, "description": "World's largest puppet theater, 1000+ puppets"},
    {"name": "Thang Long Water Puppet Theatre", "lat": 21.0285, "lon": 105.8525, "city": "Hanoi", "country": "Vietnam", "tradition": "Water Puppetry", "year": 1969, "description": "Traditional Vietnamese water puppet performances"},
    {"name": "Rajasthan Puppet Theatre", "lat": 26.9124, "lon": 75.7873, "city": "Jaipur", "country": "India", "tradition": "Kathputli", "year": 1500, "description": "Traditional Rajasthani string puppetry"},
    {"name": "Museum of Greek Folk Art - Puppet Collection", "lat": 37.9738, "lon": 23.7275, "city": "Athens", "country": "Greece", "tradition": "Karagiozis", "year": 1918, "description": "Greek shadow puppet tradition from Ottoman era"},
    {"name": "Little Angel Theatre", "lat": 51.5390, "lon": -0.1030, "city": "London", "country": "UK", "tradition": "Various", "year": 1961, "description": "UK's only permanent puppet theater"},
    {"name": "Teatro dei Pupi", "lat": 38.1157, "lon": 13.3615, "city": "Palermo", "country": "Italy", "tradition": "Opera dei Pupi", "year": 1800, "description": "Sicilian rod-puppet tradition, UNESCO heritage"},
    {"name": "Center for Puppetry Arts", "lat": 33.7907, "lon": -84.3885, "city": "Atlanta", "country": "USA", "tradition": "Various", "year": 1978, "description": "Largest puppetry center in the US, Jim Henson wing"},
    {"name": "Bali Topeng Dance Theatre", "lat": -8.5069, "lon": 115.2625, "city": "Ubud", "country": "Indonesia", "tradition": "Topeng (Mask)", "year": 1500, "description": "Traditional Balinese masked dance drama"},
    {"name": "Noh Theatre National", "lat": 35.6876, "lon": 139.7270, "city": "Tokyo", "country": "Japan", "tradition": "Noh (Masked)", "year": 1983, "description": "National Noh Theatre, masked musical drama since 14th c."},
    {"name": "Figurentheater Luzern", "lat": 47.0502, "lon": 8.3093, "city": "Lucerne", "country": "Switzerland", "tradition": "Figure Theater", "year": 1986, "description": "Swiss figure and puppet theater festival hub"},
    {"name": "Museo dei Burattini", "lat": 44.8015, "lon": 10.3279, "city": "Parma", "country": "Italy", "tradition": "Burattini (Glove)", "year": 2002, "description": "Italian glove puppet museum, Emilian tradition"},
    {"name": "Sbek Thom Theatre (Shadow)", "lat": 13.3633, "lon": 103.8600, "city": "Siem Reap", "country": "Cambodia", "tradition": "Sbek Thom", "year": 1200, "description": "Khmer large shadow puppet theater, UNESCO heritage"},
    {"name": "Tolu Bommalata (Andhra Shadow)", "lat": 15.8281, "lon": 78.0373, "city": "Kurnool", "country": "India", "tradition": "Tolu Bommalata", "year": 1500, "description": "Andhra Pradesh leather shadow puppetry tradition"},
]

# ============================================================================
# 6. Circus & Variety (17)
# ============================================================================

CIRCUS_VARIETY = [
    {"name": "Cirque du Soleil HQ", "lat": 45.5598, "lon": -73.5770, "city": "Montreal", "country": "Canada", "type": "Contemporary Circus", "year": 1984, "description": "World-famous new circus without animals"},
    {"name": "Blackpool Tower Circus", "lat": 53.8159, "lon": -3.0553, "city": "Blackpool", "country": "UK", "type": "Traditional Circus", "year": 1894, "description": "Oldest permanent circus in the world"},
    {"name": "Circus Krone Building", "lat": 48.1451, "lon": 11.5494, "city": "Munich", "country": "Germany", "type": "Traditional Circus", "year": 1919, "description": "Largest circus building in Europe"},
    {"name": "Moscow State Circus on Tsvetnoy", "lat": 55.7714, "lon": 37.6218, "city": "Moscow", "country": "Russia", "type": "State Circus", "year": 1880, "description": "Old Moscow Circus, legendary acts since 1880"},
    {"name": "Great Moscow State Circus on Vernadsky", "lat": 55.6957, "lon": 37.5428, "city": "Moscow", "country": "Russia", "type": "State Circus", "year": 1971, "description": "Largest permanent circus in the world (3400 seats)"},
    {"name": "Shanghai Circus World", "lat": 31.2797, "lon": 121.4578, "city": "Shanghai", "country": "China", "type": "Chinese Acrobatics", "year": 2005, "description": "Chinese acrobatic performances, ERA show"},
    {"name": "Chaoyang Theatre Beijing", "lat": 39.9304, "lon": 116.4700, "city": "Beijing", "country": "China", "type": "Chinese Acrobatics", "year": 1984, "description": "Beijing's premier acrobatics and kung fu shows"},
    {"name": "Circus Maximus (site)", "lat": 41.8862, "lon": 12.4853, "city": "Rome", "country": "Italy", "type": "Ancient", "year": -600, "description": "Ancient Rome's chariot racing and spectacles arena"},
    {"name": "Hippodrome London", "lat": 51.5106, "lon": -0.1283, "city": "London", "country": "UK", "type": "Variety Theater", "year": 1900, "description": "Historic variety theater, now casino-theater"},
    {"name": "Wintergarten Variete Berlin", "lat": 52.5074, "lon": 13.3832, "city": "Berlin", "country": "Germany", "type": "Variety", "year": 1992, "description": "Germany's most famous variete theater, 1890s tradition"},
    {"name": "Pegasus Theatre (Festival Mondial du Cirque)", "lat": 48.8810, "lon": 2.3528, "city": "Paris", "country": "France", "type": "Contemporary Circus", "year": 1977, "description": "Festival Mondial du Cirque de Demain host city"},
    {"name": "Zippos Circus (London Base)", "lat": 51.5074, "lon": -0.1278, "city": "London", "country": "UK", "type": "Traditional Circus", "year": 1986, "description": "Britain's favorite big top touring circus"},
    {"name": "Circus Arts Conservatory", "lat": 27.3307, "lon": -82.5390, "city": "Sarasota, FL", "country": "USA", "type": "Training / Museum", "year": 1997, "description": "Winter home of Ringling Bros, circus heritage center"},
    {"name": "Wuqiao Acrobatics World", "lat": 37.6050, "lon": 116.3830, "city": "Wuqiao", "country": "China", "type": "Chinese Acrobatics", "year": 1993, "description": "Birthplace of Chinese acrobatics, 2000+ year tradition"},
    {"name": "National Circus School of Montreal", "lat": 45.5290, "lon": -73.5500, "city": "Montreal", "country": "Canada", "type": "Training", "year": 1981, "description": "Premier circus training school in the Americas"},
    {"name": "Circo Price", "lat": 40.4115, "lon": -3.6965, "city": "Madrid", "country": "Spain", "type": "Contemporary Circus", "year": 2007, "description": "Madrid's permanent circus and performing arts venue"},
    {"name": "Phare Cambodian Circus", "lat": 13.3548, "lon": 103.8590, "city": "Siem Reap", "country": "Cambodia", "type": "Social Circus", "year": 2013, "description": "Cambodian circus using arts for social change"},
    {"name": "Cirque d'Hiver Bouglione", "lat": 48.8614, "lon": 2.3700, "city": "Paris", "country": "France", "type": "Traditional Circus", "year": 1852, "description": "Historic permanent circus in Paris, Bouglione family"},
    {"name": "Roncalli Circus (HQ)", "lat": 50.9375, "lon": 6.9603, "city": "Cologne", "country": "Germany", "type": "Contemporary Circus", "year": 1976, "description": "German new circus, first to eliminate animal acts"},
    {"name": "Circus Oz (Melbourne)", "lat": -37.8020, "lon": 144.9520, "city": "Melbourne", "country": "Australia", "type": "Contemporary Circus", "year": 1978, "description": "Australian rock-and-roll contemporary circus"},
]

# ============================================================================
# 7. Famous Composers' Birthplaces (25)
# ============================================================================

COMPOSERS_BIRTHPLACES = [
    {"name": "Wolfgang Amadeus Mozart", "lat": 47.8003, "lon": 13.0433, "city": "Salzburg", "country": "Austria", "born": 1756, "died": 1791, "genre": "Classical", "notable_work": "The Magic Flute, Don Giovanni, Requiem"},
    {"name": "Ludwig van Beethoven", "lat": 50.7339, "lon": 7.0994, "city": "Bonn", "country": "Germany", "born": 1770, "died": 1827, "genre": "Classical / Romantic", "notable_work": "Symphony No. 9, Moonlight Sonata"},
    {"name": "Giuseppe Verdi", "lat": 44.9175, "lon": 10.1297, "city": "Le Roncole", "country": "Italy", "born": 1813, "died": 1901, "genre": "Opera", "notable_work": "Aida, La Traviata, Rigoletto"},
    {"name": "Richard Wagner", "lat": 51.3397, "lon": 12.3731, "city": "Leipzig", "country": "Germany", "born": 1813, "died": 1883, "genre": "Opera", "notable_work": "The Ring Cycle, Tristan und Isolde"},
    {"name": "Johann Sebastian Bach", "lat": 50.9807, "lon": 10.3150, "city": "Eisenach", "country": "Germany", "born": 1685, "died": 1750, "genre": "Baroque", "notable_work": "Brandenburg Concertos, Mass in B minor"},
    {"name": "Pyotr Ilyich Tchaikovsky", "lat": 56.7733, "lon": 51.3508, "city": "Votkinsk", "country": "Russia", "born": 1840, "died": 1893, "genre": "Romantic", "notable_work": "Swan Lake, The Nutcracker, 1812 Overture"},
    {"name": "Frederic Chopin", "lat": 52.0844, "lon": 20.3775, "city": "Zelazowa Wola", "country": "Poland", "born": 1810, "died": 1849, "genre": "Romantic", "notable_work": "Nocturnes, Ballades, Etudes"},
    {"name": "Giacomo Puccini", "lat": 43.8429, "lon": 10.5027, "city": "Lucca", "country": "Italy", "born": 1858, "died": 1924, "genre": "Opera", "notable_work": "La Boheme, Tosca, Madama Butterfly"},
    {"name": "Antonio Vivaldi", "lat": 45.4408, "lon": 12.3155, "city": "Venice", "country": "Italy", "born": 1678, "died": 1741, "genre": "Baroque", "notable_work": "The Four Seasons"},
    {"name": "Franz Schubert", "lat": 48.2278, "lon": 16.3551, "city": "Vienna", "country": "Austria", "born": 1797, "died": 1828, "genre": "Romantic", "notable_work": "Ave Maria, Unfinished Symphony"},
    {"name": "Johannes Brahms", "lat": 53.5511, "lon": 9.9937, "city": "Hamburg", "country": "Germany", "born": 1833, "died": 1897, "genre": "Romantic", "notable_work": "Hungarian Dances, German Requiem"},
    {"name": "George Frideric Handel", "lat": 51.4819, "lon": 11.9695, "city": "Halle", "country": "Germany", "born": 1685, "died": 1759, "genre": "Baroque", "notable_work": "Messiah, Water Music"},
    {"name": "Claude Debussy", "lat": 48.8600, "lon": 2.1589, "city": "Saint-Germain-en-Laye", "country": "France", "born": 1862, "died": 1918, "genre": "Impressionist", "notable_work": "Clair de Lune, La Mer"},
    {"name": "Igor Stravinsky", "lat": 59.3430, "lon": 30.1248, "city": "Oranienbaum", "country": "Russia", "born": 1882, "died": 1971, "genre": "Modern", "notable_work": "The Rite of Spring, Firebird"},
    {"name": "Gioachino Rossini", "lat": 43.7228, "lon": 12.6367, "city": "Pesaro", "country": "Italy", "born": 1792, "died": 1868, "genre": "Opera", "notable_work": "The Barber of Seville, William Tell"},
    {"name": "Richard Strauss", "lat": 48.1351, "lon": 11.5820, "city": "Munich", "country": "Germany", "born": 1864, "died": 1949, "genre": "Late Romantic / Opera", "notable_work": "Also sprach Zarathustra, Der Rosenkavalier"},
    {"name": "Hector Berlioz", "lat": 45.3694, "lon": 5.6273, "city": "La Cote-Saint-Andre", "country": "France", "born": 1803, "died": 1869, "genre": "Romantic", "notable_work": "Symphonie fantastique"},
    {"name": "Antonin Dvorak", "lat": 50.2646, "lon": 14.2990, "city": "Nelahozeves", "country": "Czech Republic", "born": 1841, "died": 1904, "genre": "Romantic", "notable_work": "New World Symphony, Slavonic Dances"},
    {"name": "Edvard Grieg", "lat": 60.3913, "lon": 5.3221, "city": "Bergen", "country": "Norway", "born": 1843, "died": 1907, "genre": "Romantic / Nationalist", "notable_work": "Peer Gynt, Piano Concerto in A minor"},
    {"name": "Jean Sibelius", "lat": 60.9919, "lon": 24.4603, "city": "Hameenlinna", "country": "Finland", "born": 1865, "died": 1957, "genre": "Romantic / Nationalist", "notable_work": "Finlandia, Violin Concerto"},
    {"name": "Sergei Rachmaninoff", "lat": 58.5228, "lon": 31.2695, "city": "Semyonovo", "country": "Russia", "born": 1873, "died": 1943, "genre": "Late Romantic", "notable_work": "Piano Concerto No. 2, Rhapsody on Paganini"},
    {"name": "Gustav Mahler", "lat": 49.3960, "lon": 15.5905, "city": "Kaliště", "country": "Czech Republic", "born": 1860, "died": 1911, "genre": "Late Romantic", "notable_work": "Symphony No. 2 Resurrection"},
    {"name": "Sergei Prokofiev", "lat": 47.9133, "lon": 36.5417, "city": "Sontsivka", "country": "Ukraine", "born": 1891, "died": 1953, "genre": "Modern", "notable_work": "Peter and the Wolf, Romeo and Juliet"},
    {"name": "Bela Bartok", "lat": 46.3833, "lon": 21.5000, "city": "Nagyszentmiklos", "country": "Romania", "born": 1881, "died": 1945, "genre": "Modern / Folk", "notable_work": "Concerto for Orchestra, Mikrokosmos"},
    {"name": "Gaetano Donizetti", "lat": 45.6983, "lon": 9.6773, "city": "Bergamo", "country": "Italy", "born": 1797, "died": 1848, "genre": "Opera", "notable_work": "Lucia di Lammermoor, L'elisir d'amore"},
    {"name": "Camille Saint-Saens", "lat": 48.8566, "lon": 2.3522, "city": "Paris", "country": "France", "born": 1835, "died": 1921, "genre": "Romantic", "notable_work": "Carnival of the Animals, Organ Symphony"},
    {"name": "Georges Bizet", "lat": 48.8566, "lon": 2.3522, "city": "Paris", "country": "France", "born": 1838, "died": 1875, "genre": "Opera", "notable_work": "Carmen, Les pecheurs de perles"},
    {"name": "Dmitri Shostakovich", "lat": 59.9343, "lon": 30.3351, "city": "St. Petersburg", "country": "Russia", "born": 1906, "died": 1975, "genre": "Modern", "notable_work": "Symphony No. 5, Lady Macbeth of Mtsensk"},
    {"name": "Benjamin Britten", "lat": 52.1872, "lon": 1.5304, "city": "Lowestoft", "country": "UK", "born": 1913, "died": 1976, "genre": "Modern", "notable_work": "Peter Grimes, War Requiem"},
    {"name": "Ralph Vaughan Williams", "lat": 51.7670, "lon": -2.4350, "city": "Down Ampney", "country": "UK", "born": 1872, "died": 1958, "genre": "Romantic / Nationalist", "notable_work": "The Lark Ascending, Fantasia on Greensleeves"},
]

# ============================================================================
# 8. Concert Halls (22)
# ============================================================================

CONCERT_HALLS = [
    {"name": "Carnegie Hall", "lat": 40.7651, "lon": -73.9801, "city": "New York", "country": "USA", "year": 1891, "seats": 2804, "style": "Italian Renaissance", "famous_for": "Tchaikovsky conducted opening night"},
    {"name": "Royal Albert Hall", "lat": 51.5009, "lon": -0.1774, "city": "London", "country": "UK", "year": 1871, "seats": 5272, "style": "Italianate", "famous_for": "BBC Proms, iconic dome shape"},
    {"name": "Wiener Musikverein", "lat": 48.2007, "lon": 16.3726, "city": "Vienna", "country": "Austria", "year": 1870, "seats": 1744, "style": "Historicist", "famous_for": "Golden Hall, Vienna New Year's Concert"},
    {"name": "Berlin Philharmonie", "lat": 52.5103, "lon": 13.3694, "city": "Berlin", "country": "Germany", "year": 1963, "seats": 2440, "style": "Modernist", "famous_for": "Vineyard-style seating, Karajan's hall"},
    {"name": "Concertgebouw", "lat": 52.3564, "lon": 4.8789, "city": "Amsterdam", "country": "Netherlands", "year": 1888, "seats": 2037, "style": "Neoclassical", "famous_for": "World-renowned acoustics"},
    {"name": "Elbphilharmonie", "lat": 53.5413, "lon": 9.9842, "city": "Hamburg", "country": "Germany", "year": 2017, "seats": 2100, "style": "Ultra-Modern", "famous_for": "Glass wave building atop old warehouse"},
    {"name": "Walt Disney Concert Hall", "lat": 34.0554, "lon": -118.2498, "city": "Los Angeles", "country": "USA", "year": 2003, "seats": 2265, "style": "Deconstructivist (Gehry)", "famous_for": "Frank Gehry's stainless steel design"},
    {"name": "Suntory Hall", "lat": 35.6665, "lon": 139.7410, "city": "Tokyo", "country": "Japan", "year": 1986, "seats": 2006, "style": "Modern vineyard", "famous_for": "Japan's first vineyard-style concert hall"},
    {"name": "Philharmonie de Paris", "lat": 48.8909, "lon": 2.3936, "city": "Paris", "country": "France", "year": 2015, "seats": 2400, "style": "Contemporary", "famous_for": "Jean Nouvel aluminum design"},
    {"name": "Symphony Hall Boston", "lat": 42.3429, "lon": -71.0860, "city": "Boston", "country": "USA", "year": 1900, "seats": 2625, "style": "Italian Renaissance", "famous_for": "First hall designed using acoustic science"},
    {"name": "Tchaikovsky Concert Hall", "lat": 55.7710, "lon": 37.5970, "city": "Moscow", "country": "Russia", "year": 1940, "seats": 1505, "style": "Stalinist Neoclassical", "famous_for": "Home of Moscow Philharmonic"},
    {"name": "Sydney Town Hall", "lat": -33.8738, "lon": 151.2071, "city": "Sydney", "country": "Australia", "year": 1889, "seats": 2000, "style": "Victorian Second Empire", "famous_for": "Grand pipe organ, civic concerts"},
    {"name": "Rudolfinum (Dvorak Hall)", "lat": 50.0895, "lon": 14.4145, "city": "Prague", "country": "Czech Republic", "year": 1885, "seats": 1147, "style": "Neo-Renaissance", "famous_for": "Czech Philharmonic home, Prague Spring festival"},
    {"name": "Musikhuset Aarhus", "lat": 56.1539, "lon": 10.2015, "city": "Aarhus", "country": "Denmark", "year": 1982, "seats": 1600, "style": "Modernist", "famous_for": "Scandinavia's largest concert venue"},
    {"name": "KKL Luzern", "lat": 47.0510, "lon": 8.3070, "city": "Lucerne", "country": "Switzerland", "year": 1998, "seats": 1898, "style": "Modern (Jean Nouvel)", "famous_for": "Lucerne Festival venue, lakeside design"},
    {"name": "Sala Sao Paulo", "lat": -23.5341, "lon": -46.6388, "city": "Sao Paulo", "country": "Brazil", "year": 1999, "seats": 1484, "style": "Converted railway station", "famous_for": "Converted from Sorocabana station"},
    {"name": "Palau de la Musica Catalana", "lat": 41.3876, "lon": 2.1752, "city": "Barcelona", "country": "Spain", "year": 1908, "seats": 2049, "style": "Art Nouveau / Catalan Modernisme", "famous_for": "Stained glass, ornate ceiling, UNESCO site"},
    {"name": "Harpa Concert Hall", "lat": 64.1507, "lon": -21.9327, "city": "Reykjavik", "country": "Iceland", "year": 2011, "seats": 1800, "style": "Modern crystalline", "famous_for": "Geometric glass facade by Olafur Eliasson"},
    {"name": "Esplanade Concert Hall", "lat": 1.2899, "lon": 103.8556, "city": "Singapore", "country": "Singapore", "year": 2002, "seats": 1600, "style": "Modern (Durian shape)", "famous_for": "Southeast Asia's premier performing arts center"},
    {"name": "Auditorio Nacional de Musica", "lat": 40.4423, "lon": -3.6773, "city": "Madrid", "country": "Spain", "year": 1988, "seats": 2324, "style": "Postmodern", "famous_for": "Spain's top symphony venue"},
    {"name": "Gewandhaus Leipzig", "lat": 51.3378, "lon": 12.3803, "city": "Leipzig", "country": "Germany", "year": 1981, "seats": 1900, "style": "Modern", "famous_for": "Gewandhaus Orchestra, oldest civic concert society"},
    {"name": "Barbican Hall", "lat": 51.5198, "lon": -0.0935, "city": "London", "country": "UK", "year": 1982, "seats": 1943, "style": "Brutalist", "famous_for": "London Symphony Orchestra home"},
    {"name": "Wigmore Hall", "lat": 51.5172, "lon": -0.1509, "city": "London", "country": "UK", "year": 1901, "seats": 552, "style": "Arts and Crafts", "famous_for": "World-renowned chamber music venue"},
    {"name": "Tonhalle Zurich", "lat": 47.3650, "lon": 8.5420, "city": "Zurich", "country": "Switzerland", "year": 1895, "seats": 1455, "style": "Neo-Baroque", "famous_for": "Zurich Tonhalle Orchestra home"},
    {"name": "BOZAR / Henry Le Boeuf Hall", "lat": 50.8440, "lon": 4.3610, "city": "Brussels", "country": "Belgium", "year": 1929, "seats": 2200, "style": "Art Deco", "famous_for": "Victor Horta design, Queen Elisabeth Competition"},
    {"name": "Muziekgebouw aan 't IJ", "lat": 52.3786, "lon": 4.9130, "city": "Amsterdam", "country": "Netherlands", "year": 2005, "seats": 735, "style": "Ultra-Modern glass", "famous_for": "Contemporary and new music, waterfront"},
]

# ============================================================================
# 9. Film & TV Studios (22)
# ============================================================================

FILM_TV_STUDIOS = [
    {"name": "Hollywood Sign / Studios Area", "lat": 34.1341, "lon": -118.3215, "city": "Los Angeles", "country": "USA", "founded": 1911, "type": "Film District", "famous_for": "Global capital of film industry"},
    {"name": "Universal Studios Hollywood", "lat": 34.1381, "lon": -118.3534, "city": "Los Angeles", "country": "USA", "founded": 1912, "type": "Major Studio", "famous_for": "Oldest continuously operating studio"},
    {"name": "Warner Bros. Studios Burbank", "lat": 34.1533, "lon": -118.3426, "city": "Burbank", "country": "USA", "founded": 1923, "type": "Major Studio", "famous_for": "Batman, Harry Potter, Casablanca"},
    {"name": "Paramount Pictures", "lat": 34.0834, "lon": -118.3196, "city": "Los Angeles", "country": "USA", "founded": 1912, "type": "Major Studio", "famous_for": "The Godfather, Star Trek, Mission Impossible"},
    {"name": "Pinewood Studios", "lat": 51.5481, "lon": -0.5340, "city": "Iver Heath", "country": "UK", "founded": 1936, "type": "Major Studio", "famous_for": "James Bond, Star Wars, Marvel films"},
    {"name": "Cinecitta Studios", "lat": 41.8518, "lon": 12.5733, "city": "Rome", "country": "Italy", "founded": 1937, "type": "Major Studio", "famous_for": "Fellini films, Ben-Hur, Hollywood on the Tiber"},
    {"name": "Babelsberg Studio", "lat": 52.3878, "lon": 13.1198, "city": "Potsdam", "country": "Germany", "founded": 1912, "type": "Major Studio", "famous_for": "World's oldest large-scale studio, Metropolis"},
    {"name": "Film City Mumbai (Goregaon)", "lat": 19.1644, "lon": 72.8514, "city": "Mumbai", "country": "India", "founded": 1977, "type": "Film Complex", "famous_for": "Bollywood production hub"},
    {"name": "Ramoji Film City", "lat": 17.2543, "lon": 78.6808, "city": "Hyderabad", "country": "India", "founded": 1996, "type": "Mega Complex", "famous_for": "World's largest film studio complex (Guinness)"},
    {"name": "Toho Studios", "lat": 35.6714, "lon": 139.5655, "city": "Tokyo", "country": "Japan", "founded": 1932, "type": "Major Studio", "famous_for": "Godzilla, Akira Kurosawa films"},
    {"name": "Shaw Brothers Studio (Site)", "lat": 22.3540, "lon": 114.1260, "city": "Hong Kong", "country": "China", "founded": 1958, "type": "Historic Studio", "famous_for": "Martial arts cinema golden age"},
    {"name": "Mosfilm Studios", "lat": 55.7136, "lon": 37.5260, "city": "Moscow", "country": "Russia", "founded": 1920, "type": "State Studio", "famous_for": "Eisenstein, Tarkovsky masterpieces"},
    {"name": "Barrandov Studios", "lat": 50.0332, "lon": 14.3788, "city": "Prague", "country": "Czech Republic", "founded": 1931, "type": "Major Studio", "famous_for": "Amadeus, Mission Impossible, many Hollywood films"},
    {"name": "Shepperton Studios", "lat": 51.3960, "lon": -0.4620, "city": "Shepperton", "country": "UK", "founded": 1931, "type": "Major Studio", "famous_for": "Alien, Gravity, Star Wars sequels"},
    {"name": "Fox Studios Australia", "lat": -33.8921, "lon": 151.2184, "city": "Sydney", "country": "Australia", "founded": 1998, "type": "Major Studio", "famous_for": "The Matrix, Star Wars prequels"},
    {"name": "CJ ENM Studio Center", "lat": 37.4219, "lon": 127.1260, "city": "Paju", "country": "South Korea", "founded": 2012, "type": "Major Studio", "famous_for": "K-drama and Korean cinema production"},
    {"name": "DEFA Studio Potsdam (historic)", "lat": 52.3850, "lon": 13.1150, "city": "Potsdam", "country": "Germany", "founded": 1946, "type": "Historic Studio", "famous_for": "East German cinema, now part of Babelsberg"},
    {"name": "Estudios Churubusco", "lat": 19.3482, "lon": -99.1223, "city": "Mexico City", "country": "Mexico", "founded": 1945, "type": "Major Studio", "famous_for": "Mexican Golden Age cinema, Hollywood co-productions"},
    {"name": "Nu Boyana Film Studios", "lat": 42.6510, "lon": 23.3280, "city": "Sofia", "country": "Bulgaria", "founded": 1962, "type": "Major Studio", "famous_for": "Expendables, London Has Fallen, affordable filming"},
    {"name": "Korda Studios", "lat": 47.5520, "lon": 18.8390, "city": "Etyek", "country": "Hungary", "founded": 2007, "type": "Modern Studio", "famous_for": "Blade Runner 2049, The Martian, Dune"},
    {"name": "Leavesden Studios", "lat": 51.6930, "lon": -0.4210, "city": "Watford", "country": "UK", "founded": 1994, "type": "Major Studio", "famous_for": "All Harry Potter films, Warner Bros. tour"},
    {"name": "Trollhattan (Film i Vast)", "lat": 58.2830, "lon": 12.2890, "city": "Trollhattan", "country": "Sweden", "founded": 1997, "type": "Film Center", "famous_for": "Lars von Trier's Dogville, Scandinavian cinema hub"},
    {"name": "Weta Workshop / Stone Street Studios", "lat": -41.3081, "lon": 174.8245, "city": "Wellington", "country": "New Zealand", "founded": 1987, "type": "Major Studio / VFX", "famous_for": "Lord of the Rings, Avatar VFX, Peter Jackson"},
    {"name": "Orion Pictures / MGM (Culver City)", "lat": 34.0226, "lon": -118.3965, "city": "Culver City", "country": "USA", "founded": 1924, "type": "Historic Studio", "famous_for": "Gone with the Wind, MGM musicals, Wizard of Oz"},
    {"name": "Hengdian World Studios", "lat": 29.1530, "lon": 120.2340, "city": "Hengdian", "country": "China", "founded": 1996, "type": "Mega Complex", "famous_for": "World's largest outdoor film studio, Chinese epics"},
]

# ============================================================================
# 10. Comedy & Cabaret (17)
# ============================================================================

COMEDY_CABARET = [
    {"name": "The Comedy Store (London)", "lat": 51.5100, "lon": -0.1312, "city": "London", "country": "UK", "type": "Stand-up", "year": 1979, "description": "UK's top stand-up comedy venue, launched many careers"},
    {"name": "The Comedy Store (LA)", "lat": 34.0980, "lon": -118.3682, "city": "Los Angeles", "country": "USA", "type": "Stand-up", "year": 1972, "description": "Legendary Sunset Strip comedy club"},
    {"name": "Moulin Rouge", "lat": 48.8841, "lon": 2.3322, "city": "Paris", "country": "France", "type": "Cabaret", "year": 1889, "description": "World's most famous cabaret, can-can birthplace"},
    {"name": "Second City Chicago", "lat": 41.9120, "lon": -87.6349, "city": "Chicago", "country": "USA", "type": "Improv", "year": 1959, "description": "Launched Belushi, Fey, Colbert, improv comedy mecca"},
    {"name": "Upright Citizens Brigade Theatre", "lat": 40.7426, "lon": -73.9984, "city": "New York", "country": "USA", "type": "Improv", "year": 1999, "description": "Amy Poehler co-founded, NYC improv institution"},
    {"name": "Friedrichstadt-Palast", "lat": 52.5248, "lon": 13.3878, "city": "Berlin", "country": "Germany", "type": "Revue/Cabaret", "year": 1919, "description": "World's largest revue theater, spectacular shows"},
    {"name": "Lido de Paris", "lat": 48.8716, "lon": 2.3035, "city": "Paris", "country": "France", "type": "Cabaret", "year": 1946, "description": "Champs-Elysees cabaret, spectacular revues"},
    {"name": "Crazy Horse Paris", "lat": 48.8660, "lon": 2.3026, "city": "Paris", "country": "France", "type": "Cabaret", "year": 1951, "description": "Avant-garde cabaret and burlesque"},
    {"name": "Tigerpalast Frankfurt", "lat": 50.1100, "lon": 8.6850, "city": "Frankfurt", "country": "Germany", "type": "Variety/Cabaret", "year": 1988, "description": "Germany's premier variete cabaret with fine dining"},
    {"name": "Comedy Cellar NYC", "lat": 40.7300, "lon": -74.0003, "city": "New York", "country": "USA", "type": "Stand-up", "year": 1982, "description": "Greenwich Village legend, Seinfeld, CK, Chappelle"},
    {"name": "The Groundlings", "lat": 34.0837, "lon": -118.3423, "city": "Los Angeles", "country": "USA", "type": "Improv/Sketch", "year": 1974, "description": "Launched Will Ferrell, Melissa McCarthy, Phil Hartman"},
    {"name": "Just for Laughs (HQ)", "lat": 45.5131, "lon": -73.5628, "city": "Montreal", "country": "Canada", "type": "Comedy Festival", "year": 1983, "description": "World's largest comedy festival"},
    {"name": "Edinburgh Festival Fringe Venues", "lat": 55.9480, "lon": -3.1883, "city": "Edinburgh", "country": "UK", "type": "Festival", "year": 1947, "description": "World's largest arts festival, comedy central"},
    {"name": "Boom Chicago Amsterdam", "lat": 52.3650, "lon": 4.8820, "city": "Amsterdam", "country": "Netherlands", "type": "Improv", "year": 1993, "description": "English-language improv in Amsterdam, Seth Meyers alum"},
    {"name": "Bar Jeder Vernunft", "lat": 52.5010, "lon": 13.3260, "city": "Berlin", "country": "Germany", "type": "Cabaret", "year": 1992, "description": "Legendary Berlin mirror-tent cabaret"},
    {"name": "Melbourne International Comedy Festival HQ", "lat": -37.8115, "lon": 144.9689, "city": "Melbourne", "country": "Australia", "type": "Comedy Festival", "year": 1987, "description": "Third-largest comedy festival in the world"},
    {"name": "Yuk Yuk's Toronto", "lat": 43.6470, "lon": -79.3960, "city": "Toronto", "country": "Canada", "type": "Stand-up", "year": 1976, "description": "Canada's premier stand-up comedy chain, Jim Carrey alum"},
    {"name": "The Improv (Hollywood)", "lat": 34.0901, "lon": -118.3575, "city": "Los Angeles", "country": "USA", "type": "Stand-up", "year": 1975, "description": "Legendary stand-up venue, Budd Friedman's legacy"},
    {"name": "Quatsch Comedy Club", "lat": 52.5096, "lon": 13.3776, "city": "Berlin", "country": "Germany", "type": "Stand-up", "year": 1992, "description": "Germany's most successful stand-up comedy club"},
    {"name": "Wintergarten Berlin (Original Site)", "lat": 52.5110, "lon": 13.3790, "city": "Berlin", "country": "Germany", "type": "Historic Cabaret", "year": 1887, "description": "First cinema screening venue, legendary cabaret 1887-1944"},
]


# ============================================================================
# Map builder helpers
# ============================================================================

def _create_base_map(data: list, zoom: int = 3) -> folium.Map:
    """Create a dark-themed base folium map centered on the data."""
    if data:
        avg_lat = sum(d["lat"] for d in data) / len(data)
        avg_lon = sum(d["lon"] for d in data) / len(data)
    else:
        avg_lat, avg_lon = 30.0, 0.0
    return folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )


def _popup_html(title: str, rows: list[tuple[str, str]], color: str) -> str:
    """Build a styled popup HTML string. All values are escaped."""
    safe_title = html_module.escape(str(title))
    header = (
        f'<div style="font-family:Arial,sans-serif;min-width:200px;max-width:300px;">'
        f'<h4 style="margin:0 0 6px;color:{color};">{safe_title}</h4>'
    )
    body = ""
    for label, value in rows:
        safe_label = html_module.escape(str(label))
        safe_value = html_module.escape(str(value))
        body += (
            f'<div style="margin:2px 0;font-size:13px;">'
            f'<b style="color:#ccc;">{safe_label}:</b> '
            f'<span style="color:#eee;">{safe_value}</span></div>'
        )
    return header + body + "</div>"


# ============================================================================
# Individual map builders — each returns (folium.Map, pd.DataFrame)
# ============================================================================

@st.cache_data(ttl=3600)
def _get_opera_houses_df() -> list[dict]:
    return OPERA_HOUSES

def _build_opera_houses_map() -> tuple:
    data = _get_opera_houses_df()
    color = MODE_COLORS["Greatest Opera Houses"]
    m = _create_base_map(data, zoom=3)
    for d in data:
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Year Opened", d["year"]),
            ("Seats", f'{d["seats"]:,}'),
            ("Style", d["style"]),
            ("Famous For", d["famous_for"]),
        ], color)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


@st.cache_data(ttl=3600)
def _get_shakespeare_df() -> list[dict]:
    return SHAKESPEARE_WORLD

def _build_shakespeare_map() -> tuple:
    data = _get_shakespeare_df()
    color = MODE_COLORS["Shakespeare's World"]
    m = _create_base_map(data, zoom=4)
    for d in data:
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Year", d["year"]),
            ("Type", d["type"]),
            ("Connection", d["connection"]),
        ], color)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


@st.cache_data(ttl=3600)
def _get_ancient_theaters_df() -> list[dict]:
    return ANCIENT_THEATERS

def _build_ancient_theaters_map() -> tuple:
    data = _get_ancient_theaters_df()
    color = MODE_COLORS["Ancient Theaters"]
    m = _create_base_map(data, zoom=4)
    for d in data:
        radius = max(5, min(14, d["capacity"] / 5000))
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Year Built", d["year"]),
            ("Capacity", f'{d["capacity"]:,}'),
            ("Condition", d["condition"]),
            ("Famous For", d["famous_for"]),
        ], color)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


@st.cache_data(ttl=3600)
def _get_broadway_df() -> list[dict]:
    return BROADWAY_WEST_END

def _build_broadway_map() -> tuple:
    data = _get_broadway_df()
    color = MODE_COLORS["Broadway & West End"]
    m = _create_base_map(data, zoom=3)
    district_colors = {
        "Broadway": "#f59e0b",
        "West End": "#ef4444",
        "Melbourne": "#10b981",
        "Sydney": "#06b6d4",
        "Tokyo": "#ec4899",
        "Berlin": "#8b5cf6",
        "Paris": "#3b82f6",
        "Hamburg": "#f97316",
    }
    for d in data:
        c = district_colors.get(d["district"], color)
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("District", d["district"]),
            ("Seats", f'{d["seats"]:,}'),
            ("Famous Show", d["famous_show"]),
        ], c)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=8,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


@st.cache_data(ttl=3600)
def _get_puppet_mask_df() -> list[dict]:
    return PUPPET_MASK_THEATER

def _build_puppet_mask_map() -> tuple:
    data = _get_puppet_mask_df()
    color = MODE_COLORS["Puppet & Mask Theater"]
    m = _create_base_map(data, zoom=3)
    tradition_colors = {
        "Bunraku": "#ef4444",
        "Wayang": "#f59e0b",
        "Marionette": "#8b5cf6",
        "Giant Puppets": "#10b981",
        "International": "#3b82f6",
        "Commedia dell'Arte": "#ec4899",
        "Czech Marionettes": "#a855f7",
        "Rod Puppets": "#06b6d4",
        "Water Puppetry": "#14b8a6",
        "Kathputli": "#f97316",
        "Karagiozis": "#d4a017",
        "Various": "#8b97b0",
        "Opera dei Pupi": "#e74c3c",
        "Topeng (Mask)": "#c084fc",
        "Noh (Masked)": "#fb923c",
        "Figure Theater": "#38bdf8",
    }
    for d in data:
        c = tradition_colors.get(d["tradition"], color)
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Tradition", d["tradition"]),
            ("Year", d["year"]),
            ("Description", d["description"]),
        ], c)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=8,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


@st.cache_data(ttl=3600)
def _get_circus_df() -> list[dict]:
    return CIRCUS_VARIETY

def _build_circus_map() -> tuple:
    data = _get_circus_df()
    color = MODE_COLORS["Circus & Variety"]
    m = _create_base_map(data, zoom=3)
    type_colors = {
        "Contemporary Circus": "#06b6d4",
        "Traditional Circus": "#f59e0b",
        "State Circus": "#ef4444",
        "Chinese Acrobatics": "#ec4899",
        "Ancient": "#d4a017",
        "Variety Theater": "#8b5cf6",
        "Variety": "#a855f7",
        "Training / Museum": "#10b981",
        "Training": "#3b82f6",
        "Social Circus": "#14b8a6",
    }
    for d in data:
        c = type_colors.get(d["type"], color)
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Type", d["type"]),
            ("Year", d["year"]),
            ("Description", d["description"]),
        ], c)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=8,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


@st.cache_data(ttl=3600)
def _get_composers_df() -> list[dict]:
    return COMPOSERS_BIRTHPLACES

def _build_composers_map() -> tuple:
    data = _get_composers_df()
    color = MODE_COLORS["Famous Composers' Birthplaces"]
    m = _create_base_map(data, zoom=4)
    genre_colors = {
        "Baroque": "#f59e0b",
        "Classical": "#3b82f6",
        "Classical / Romantic": "#6366f1",
        "Romantic": "#ef4444",
        "Romantic / Nationalist": "#e11d48",
        "Late Romantic": "#dc2626",
        "Late Romantic / Opera": "#b91c1c",
        "Opera": "#ec4899",
        "Impressionist": "#06b6d4",
        "Modern": "#10b981",
        "Modern / Folk": "#14b8a6",
    }
    for d in data:
        c = genre_colors.get(d["genre"], color)
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Born", d["born"]),
            ("Died", d["died"]),
            ("Genre", d["genre"]),
            ("Notable Work", d["notable_work"]),
        ], c)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=8,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


@st.cache_data(ttl=3600)
def _get_concert_halls_df() -> list[dict]:
    return CONCERT_HALLS

def _build_concert_halls_map() -> tuple:
    data = _get_concert_halls_df()
    color = MODE_COLORS["Concert Halls"]
    m = _create_base_map(data, zoom=3)
    for d in data:
        radius = max(5, min(12, d["seats"] / 500))
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Year Opened", d["year"]),
            ("Seats", f'{d["seats"]:,}'),
            ("Style", d["style"]),
            ("Famous For", d["famous_for"]),
        ], color)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


@st.cache_data(ttl=3600)
def _get_film_studios_df() -> list[dict]:
    return FILM_TV_STUDIOS

def _build_film_studios_map() -> tuple:
    data = _get_film_studios_df()
    color = MODE_COLORS["Film & TV Studios"]
    m = _create_base_map(data, zoom=3)
    type_colors = {
        "Film District": "#f59e0b",
        "Major Studio": "#10b981",
        "Film Complex": "#ec4899",
        "Mega Complex": "#ef4444",
        "Historic Studio": "#8b5cf6",
        "State Studio": "#06b6d4",
        "Modern Studio": "#3b82f6",
        "Film Center": "#14b8a6",
    }
    for d in data:
        c = type_colors.get(d["type"], color)
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Founded", d["founded"]),
            ("Type", d["type"]),
            ("Famous For", d["famous_for"]),
        ], c)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=8,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


@st.cache_data(ttl=3600)
def _get_comedy_cabaret_df() -> list[dict]:
    return COMEDY_CABARET

def _build_comedy_cabaret_map() -> tuple:
    data = _get_comedy_cabaret_df()
    color = MODE_COLORS["Comedy & Cabaret"]
    m = _create_base_map(data, zoom=3)
    type_colors = {
        "Stand-up": "#f59e0b",
        "Cabaret": "#ec4899",
        "Improv": "#06b6d4",
        "Improv/Sketch": "#14b8a6",
        "Revue/Cabaret": "#8b5cf6",
        "Comedy Festival": "#10b981",
        "Festival": "#3b82f6",
        "Variety/Cabaret": "#f97316",
    }
    for d in data:
        c = type_colors.get(d["type"], color)
        popup_content = _popup_html(d["name"], [
            ("City", d["city"]),
            ("Country", d["country"]),
            ("Type", d["type"]),
            ("Year", d["year"]),
            ("Description", d["description"]),
        ], c)
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=8,
            color=c,
            fill=True,
            fill_color=c,
            fill_opacity=0.7,
            popup=folium.Popup(popup_content, max_width=320),
            tooltip=html_module.escape(d["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


# ============================================================================
# Stats renderers
# ============================================================================

def _render_stats_opera_houses(df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Opera Houses", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Avg. Seats", f'{int(df["seats"].mean()):,}')
    c4.metric("Oldest", f'{int(df["year"].min())}')


def _render_stats_shakespeare(df: pd.DataFrame) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Site Types", df["type"].nunique())


def _render_stats_ancient_theaters(df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Theaters", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Capacity", f'{int(df["capacity"].sum()):,}')
    c4.metric("Largest", f'{int(df["capacity"].max()):,}')


def _render_stats_broadway(df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Theaters", len(df))
    c2.metric("Districts", df["district"].nunique())
    c3.metric("Avg. Seats", f'{int(df["seats"].mean()):,}')
    c4.metric("Countries", df["country"].nunique())


def _render_stats_puppet_mask(df: pd.DataFrame) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Venues", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Traditions", df["tradition"].nunique())


def _render_stats_circus(df: pd.DataFrame) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Venues", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())


def _render_stats_composers(df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Composers", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Genres", df["genre"].nunique())
    c4.metric("Earliest Born", int(df["born"].min()))


def _render_stats_concert_halls(df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Halls", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Avg. Seats", f'{int(df["seats"].mean()):,}')
    c4.metric("Oldest", int(df["year"].min()))


def _render_stats_film_studios(df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Studios", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())
    c4.metric("Oldest", int(df["founded"].min()))


def _render_stats_comedy_cabaret(df: pd.DataFrame) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Venues", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())


# ============================================================================
# Main render function
# ============================================================================

MAP_MODES = [
    "Greatest Opera Houses",
    "Shakespeare's World",
    "Ancient Theaters",
    "Broadway & West End",
    "Puppet & Mask Theater",
    "Circus & Variety",
    "Famous Composers' Birthplaces",
    "Concert Halls",
    "Film & TV Studios",
    "Comedy & Cabaret",
]

MODE_DESCRIPTIONS = {
    "Greatest Opera Houses": (
        "Explore the world's most prestigious opera houses, from the "
        "historic Teatro di San Carlo in Naples (1737) to the futuristic "
        "National Centre for the Performing Arts in Beijing. Each venue "
        "is a masterpiece of architecture and a temple of vocal art."
    ),
    "Shakespeare's World": (
        "Journey through the real-world locations connected to William "
        "Shakespeare's life and plays. From the Globe Theatre in London "
        "to Juliet's balcony in Verona and Hamlet's Elsinore in Denmark."
    ),
    "Ancient Theaters": (
        "Discover the magnificent amphitheaters and theaters of the "
        "ancient Greek and Roman world. Many of these 2,000+ year old "
        "venues still host performances today, including Epidaurus, "
        "Aspendos, and the Verona Arena."
    ),
    "Broadway & West End": (
        "Map the great theater districts of the world, from New York's "
        "Broadway to London's West End and beyond. Home to legendary "
        "musicals like Hamilton, Wicked, and The Phantom of the Opera."
    ),
    "Puppet & Mask Theater": (
        "Explore ancient and living puppet traditions around the globe: "
        "Japanese Bunraku, Indonesian Wayang shadow puppets, Czech "
        "marionettes, Sicilian Opera dei Pupi, and Vietnamese water puppets."
    ),
    "Circus & Variety": (
        "From the ancient Circus Maximus in Rome to Cirque du Soleil in "
        "Montreal, trace the worldwide history of circus arts. Includes "
        "traditional big tops, Chinese acrobatics, and contemporary circus."
    ),
    "Famous Composers' Birthplaces": (
        "Visit the birthplaces of the greatest classical composers in "
        "history. From Bach in Eisenach to Mozart in Salzburg, Beethoven "
        "in Bonn, and Verdi in Le Roncole -- walk in the footsteps of genius."
    ),
    "Concert Halls": (
        "Discover the world's finest concert halls, celebrated for their "
        "acoustics and architecture. From the golden Musikverein in Vienna "
        "to the soaring Elbphilharmonie in Hamburg and Gehry's Walt Disney "
        "Concert Hall in Los Angeles."
    ),
    "Film & TV Studios": (
        "Map the major film and television studios across the globe, from "
        "Hollywood and Pinewood to Cinecitta and Bollywood. These studios "
        "have produced the most iconic films in cinema history."
    ),
    "Comedy & Cabaret": (
        "Explore the homes of laughter worldwide: legendary stand-up clubs, "
        "Parisian cabarets like the Moulin Rouge, improv theaters like "
        "Second City, and comedy festival venues from Edinburgh to Montreal."
    ),
}


def render_opera_maps_tab() -> None:
    """Render the Opera & Theater Maps tab in TerraScout AI."""

    # ---- Header ----
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001f3ad Opera & Theater Maps</h4>'
        '<p>Opera houses, theaters, and performing arts venues worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    selected_mode = st.selectbox(
        "Map Mode",
        MAP_MODES,
        key="opera_maps_mode",
    )

    # ---- Mode description ----
    mode_desc = MODE_DESCRIPTIONS.get(selected_mode, "")
    if mode_desc:
        st.caption(mode_desc)

    generate = st.button("Generate Map", key="opera_maps_generate", type="primary")

    if not generate:
        st.info(
            "Select a map mode and click **Generate Map** to explore "
            "performing arts locations worldwide. Each mode features "
            "curated locations with detailed information, interactive "
            "map markers, statistics, and downloadable CSV data."
        )
        return

    # ---- Build map + DataFrame ----
    with st.spinner(f"Building {selected_mode} map..."):
        if selected_mode == "Greatest Opera Houses":
            m, df = _build_opera_houses_map()
        elif selected_mode == "Shakespeare's World":
            m, df = _build_shakespeare_map()
        elif selected_mode == "Ancient Theaters":
            m, df = _build_ancient_theaters_map()
        elif selected_mode == "Broadway & West End":
            m, df = _build_broadway_map()
        elif selected_mode == "Puppet & Mask Theater":
            m, df = _build_puppet_mask_map()
        elif selected_mode == "Circus & Variety":
            m, df = _build_circus_map()
        elif selected_mode == "Famous Composers' Birthplaces":
            m, df = _build_composers_map()
        elif selected_mode == "Concert Halls":
            m, df = _build_concert_halls_map()
        elif selected_mode == "Film & TV Studios":
            m, df = _build_film_studios_map()
        elif selected_mode == "Comedy & Cabaret":
            m, df = _build_comedy_cabaret_map()
        else:
            st.error("Unknown map mode.")
            return

    # ---- Stats row ----
    st.markdown("---")
    st.subheader("Summary Statistics")

    if selected_mode == "Greatest Opera Houses":
        _render_stats_opera_houses(df)
    elif selected_mode == "Shakespeare's World":
        _render_stats_shakespeare(df)
    elif selected_mode == "Ancient Theaters":
        _render_stats_ancient_theaters(df)
    elif selected_mode == "Broadway & West End":
        _render_stats_broadway(df)
    elif selected_mode == "Puppet & Mask Theater":
        _render_stats_puppet_mask(df)
    elif selected_mode == "Circus & Variety":
        _render_stats_circus(df)
    elif selected_mode == "Famous Composers' Birthplaces":
        _render_stats_composers(df)
    elif selected_mode == "Concert Halls":
        _render_stats_concert_halls(df)
    elif selected_mode == "Film & TV Studios":
        _render_stats_film_studios(df)
    elif selected_mode == "Comedy & Cabaret":
        _render_stats_comedy_cabaret(df)

    # ---- Folium Map ----
    st.markdown("---")
    st.subheader(f"{selected_mode} Map")
    st_html(m._repr_html_(), height=500)

    # ---- Data Table ----
    st.markdown("---")
    st.subheader("Data Table")
    if not df.empty:
        st.dataframe(df, width="stretch")
    else:
        st.warning("No data to display.")

    # ---- CSV Download ----
    if not df.empty:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        csv_data = csv_buf.getvalue()
        file_label = selected_mode.lower().replace(" ", "_").replace("'", "")
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"opera_theater_{file_label}.csv",
            mime="text/csv",
            key="opera_maps_csv_download",
        )


# ============================================================================
# Standalone testing
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Opera & Theater Maps", layout="wide")
    render_opera_maps_tab()
