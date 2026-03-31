# -*- coding: utf-8 -*-
"""
TerraScout AI - Libraries & Archives Maps Module
Explore the greatest libraries, ancient archives, and rare book collections worldwide.
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


# ---------------------------------------------------------------------------
# Curated datasets for each map mode
# ---------------------------------------------------------------------------

def _greatest_libraries():
    """25+ of the world's greatest libraries."""
    return [
        {"name": "Library of Congress", "city": "Washington D.C.", "country": "USA",
         "lat": 38.8887, "lon": -77.0047, "founded": 1800,
         "volumes": "170 million items", "continent": "North America",
         "note": "Largest library in the world by catalogue size"},
        {"name": "British Library", "city": "London", "country": "UK",
         "lat": 51.5299, "lon": -0.1272, "founded": 1753,
         "volumes": "170-200 million items", "continent": "Europe",
         "note": "Legal deposit library of the United Kingdom"},
        {"name": "Bibliothèque nationale de France", "city": "Paris", "country": "France",
         "lat": 48.8336, "lon": 2.3756, "founded": 1461,
         "volumes": "40 million items", "continent": "Europe",
         "note": "National library of France, one of the oldest in the world"},
        {"name": "Vatican Apostolic Library", "city": "Vatican City", "country": "Vatican",
         "lat": 41.9029, "lon": 12.4534, "founded": 1475,
         "volumes": "1.1 million books", "continent": "Europe",
         "note": "One of the oldest libraries in the world, priceless manuscripts"},
        {"name": "Bodleian Library", "city": "Oxford", "country": "UK",
         "lat": 51.7536, "lon": -1.2544, "founded": 1602,
         "volumes": "13 million items", "continent": "Europe",
         "note": "Main research library of the University of Oxford"},
        {"name": "New York Public Library", "city": "New York", "country": "USA",
         "lat": 40.7532, "lon": -73.9822, "founded": 1895,
         "volumes": "55 million items", "continent": "North America",
         "note": "Iconic Beaux-Arts building on Fifth Avenue"},
        {"name": "Russian State Library", "city": "Moscow", "country": "Russia",
         "lat": 55.7519, "lon": 37.6102, "founded": 1862,
         "volumes": "47 million items", "continent": "Europe",
         "note": "Largest library in Russia and continental Europe"},
        {"name": "National Diet Library", "city": "Tokyo", "country": "Japan",
         "lat": 35.6785, "lon": 139.7468, "founded": 1948,
         "volumes": "45 million items", "continent": "Asia",
         "note": "Only national library in Japan"},
        {"name": "Library and Archives Canada", "city": "Ottawa", "country": "Canada",
         "lat": 45.3955, "lon": -75.6898, "founded": 1953,
         "volumes": "54 million items", "continent": "North America",
         "note": "Preserves Canadian documentary heritage"},
        {"name": "National Library of China", "city": "Beijing", "country": "China",
         "lat": 39.9423, "lon": 116.3189, "founded": 1909,
         "volumes": "41 million items", "continent": "Asia",
         "note": "Largest library in Asia"},
        {"name": "Royal Library of Denmark", "city": "Copenhagen", "country": "Denmark",
         "lat": 55.6736, "lon": 12.5822, "founded": 1648,
         "volumes": "35 million items", "continent": "Europe",
         "note": "Known as the Black Diamond for its modern extension"},
        {"name": "Bavarian State Library", "city": "Munich", "country": "Germany",
         "lat": 48.1500, "lon": 11.5808, "founded": 1558,
         "volumes": "34 million items", "continent": "Europe",
         "note": "One of Europe's most important universal libraries"},
        {"name": "National Library of Australia", "city": "Canberra", "country": "Australia",
         "lat": -35.2965, "lon": 149.1294, "founded": 1960,
         "volumes": "10 million items", "continent": "Oceania",
         "note": "Largest reference library in Australia"},
        {"name": "Royal Library of Belgium", "city": "Brussels", "country": "Belgium",
         "lat": 50.8432, "lon": 4.3560, "founded": 1837,
         "volumes": "6 million items", "continent": "Europe",
         "note": "Also known as KBR"},
        {"name": "National Library of Spain", "city": "Madrid", "country": "Spain",
         "lat": 40.4237, "lon": -3.6907, "founded": 1712,
         "volumes": "33 million items", "continent": "Europe",
         "note": "Houses the earliest editions of Don Quixote"},
        {"name": "National Library of Sweden", "city": "Stockholm", "country": "Sweden",
         "lat": 59.3430, "lon": 18.0718, "founded": 1661,
         "volumes": "18 million items", "continent": "Europe",
         "note": "Kungliga biblioteket, legal deposit since 1661"},
        {"name": "National Library of Brazil", "city": "Rio de Janeiro", "country": "Brazil",
         "lat": -22.9102, "lon": -43.1737, "founded": 1810,
         "volumes": "9 million items", "continent": "South America",
         "note": "Largest library in Latin America"},
        {"name": "Austrian National Library", "city": "Vienna", "country": "Austria",
         "lat": 48.2066, "lon": 16.3660, "founded": 1368,
         "volumes": "12 million items", "continent": "Europe",
         "note": "Baroque State Hall is UNESCO Memory of the World"},
        {"name": "National Central Library", "city": "Taipei", "country": "Taiwan",
         "lat": 25.0258, "lon": 121.5176, "founded": 1933,
         "volumes": "4 million items", "continent": "Asia",
         "note": "Preserves rare Chinese texts and manuscripts"},
        {"name": "National Library of South Africa", "city": "Cape Town",
         "country": "South Africa", "lat": -33.9302, "lon": 18.4191,
         "founded": 1818, "volumes": "6 million items", "continent": "Africa",
         "note": "One of the oldest libraries in Africa"},
        {"name": "Biblioteca Nacional de México", "city": "Mexico City",
         "country": "Mexico", "lat": 19.3326, "lon": -99.1794,
         "founded": 1867, "volumes": "5 million items", "continent": "North America",
         "note": "Housed in a former church of San Agustín"},
        {"name": "National Library of India", "city": "Kolkata", "country": "India",
         "lat": 22.5355, "lon": 88.3396, "founded": 1836,
         "volumes": "2.2 million items", "continent": "Asia",
         "note": "Largest library in India by volume"},
        {"name": "National Library of the Czech Republic", "city": "Prague",
         "country": "Czech Republic", "lat": 50.0865, "lon": 14.4158,
         "founded": 1777, "volumes": "7 million items", "continent": "Europe",
         "note": "Located in the historic Klementinum complex"},
        {"name": "National Széchényi Library", "city": "Budapest", "country": "Hungary",
         "lat": 47.4963, "lon": 19.0398, "founded": 1802,
         "volumes": "8 million items", "continent": "Europe",
         "note": "Located in Buda Castle"},
        {"name": "Trinity College Library", "city": "Dublin", "country": "Ireland",
         "lat": 53.3440, "lon": -6.2543, "founded": 1592,
         "volumes": "7 million items", "continent": "Europe",
         "note": "Home of the Book of Kells"},
        {"name": "State Library of Berlin", "city": "Berlin", "country": "Germany",
         "lat": 52.5082, "lon": 13.3702, "founded": 1661,
         "volumes": "24 million items", "continent": "Europe",
         "note": "One of the largest academic libraries in Europe"},
        {"name": "National Library of Poland", "city": "Warsaw", "country": "Poland",
         "lat": 52.2399, "lon": 21.0274, "founded": 1747,
         "volumes": "9 million items", "continent": "Europe",
         "note": "Rebuilt after near-total destruction in WWII"},
        {"name": "National Library of Iran", "city": "Tehran", "country": "Iran",
         "lat": 35.7219, "lon": 51.3347, "founded": 1937,
         "volumes": "7 million items", "continent": "Asia",
         "note": "Houses rare Persian and Islamic manuscripts"},
    ]


def _ancient_libraries():
    """20+ sites of ancient and historical libraries."""
    return [
        {"name": "Library of Alexandria", "city": "Alexandria", "country": "Egypt",
         "lat": 31.2089, "lon": 29.9092, "era": "3rd century BC",
         "type": "Ancient", "continent": "Africa",
         "note": "Most famous library of antiquity, founded by Ptolemy I"},
        {"name": "Bibliotheca Alexandrina (Modern)", "city": "Alexandria",
         "country": "Egypt", "lat": 31.2089, "lon": 29.9097,
         "era": "2002 AD", "type": "Modern Revival", "continent": "Africa",
         "note": "Modern commemoration of the ancient library"},
        {"name": "Library of Pergamum", "city": "Bergama", "country": "Turkey",
         "lat": 39.1317, "lon": 27.1841, "era": "3rd century BC",
         "type": "Ancient", "continent": "Asia",
         "note": "Rival to Alexandria, birthplace of parchment"},
        {"name": "Library of Celsus", "city": "Ephesus", "country": "Turkey",
         "lat": 37.9405, "lon": 27.3412, "era": "117 AD",
         "type": "Ancient Roman", "continent": "Asia",
         "note": "Stunning Roman facade, held 12,000 scrolls"},
        {"name": "Library of Ashurbanipal", "city": "Mosul (Nineveh)",
         "country": "Iraq", "lat": 36.3580, "lon": 43.1521,
         "era": "7th century BC", "type": "Ancient Assyrian", "continent": "Asia",
         "note": "Oldest known systematically collected library, cuneiform tablets"},
        {"name": "Nalanda University Library", "city": "Rajgir", "country": "India",
         "lat": 25.1362, "lon": 85.4428, "era": "5th century AD",
         "type": "Ancient Buddhist", "continent": "Asia",
         "note": "Dharmaganja library said to have burned for months"},
        {"name": "Timbuktu Manuscripts", "city": "Timbuktu", "country": "Mali",
         "lat": 16.7735, "lon": -3.0074, "era": "13th century AD",
         "type": "Medieval African", "continent": "Africa",
         "note": "Hundreds of thousands of manuscripts in private collections"},
        {"name": "House of Wisdom (Bayt al-Hikma)", "city": "Baghdad",
         "country": "Iraq", "lat": 33.3152, "lon": 44.3661,
         "era": "8th century AD", "type": "Islamic Golden Age", "continent": "Asia",
         "note": "Major intellectual center of the Abbasid Caliphate"},
        {"name": "Imperial Library of Constantinople", "city": "Istanbul",
         "country": "Turkey", "lat": 41.0082, "lon": 28.9784,
         "era": "4th century AD", "type": "Byzantine", "continent": "Europe",
         "note": "Last of the great libraries of the ancient world"},
        {"name": "Villa of the Papyri", "city": "Herculaneum", "country": "Italy",
         "lat": 40.8058, "lon": 14.3478, "era": "1st century BC",
         "type": "Roman", "continent": "Europe",
         "note": "Buried by Vesuvius, carbonized scrolls being read with AI"},
        {"name": "Library of Aristotle", "city": "Athens", "country": "Greece",
         "lat": 37.9755, "lon": 23.7258, "era": "4th century BC",
         "type": "Ancient Greek", "continent": "Europe",
         "note": "One of the first private libraries in antiquity"},
        {"name": "Hadrian's Library", "city": "Athens", "country": "Greece",
         "lat": 37.9756, "lon": 23.7261, "era": "132 AD",
         "type": "Roman", "continent": "Europe",
         "note": "Built by Emperor Hadrian, ruins still visible"},
        {"name": "Library of Pantainos", "city": "Athens", "country": "Greece",
         "lat": 37.9712, "lon": 23.7254, "era": "100 AD",
         "type": "Roman", "continent": "Europe",
         "note": "Inscribed rules: No book shall be taken out"},
        {"name": "Theological Library of Caesarea", "city": "Caesarea",
         "country": "Israel", "lat": 32.4996, "lon": 34.8903,
         "era": "3rd century AD", "type": "Early Christian", "continent": "Asia",
         "note": "Founded by Origen, expanded by Eusebius"},
        {"name": "Libraries of Ugarit", "city": "Ras Shamra", "country": "Syria",
         "lat": 35.6006, "lon": 35.7854, "era": "13th century BC",
         "type": "Bronze Age", "continent": "Asia",
         "note": "Archives with first known alphabet tablets"},
        {"name": "Library of Ebla", "city": "Tell Mardikh", "country": "Syria",
         "lat": 35.7981, "lon": 36.7987, "era": "24th century BC",
         "type": "Bronze Age", "continent": "Asia",
         "note": "Approx 20,000 cuneiform tablets discovered"},
        {"name": "Library of Trajan", "city": "Rome", "country": "Italy",
         "lat": 41.8961, "lon": 12.4843, "era": "112 AD",
         "type": "Roman", "continent": "Europe",
         "note": "Part of Trajan's Forum, separate Greek and Latin sections"},
        {"name": "Vivarium Monastery Library", "city": "Squillace",
         "country": "Italy", "lat": 38.7789, "lon": 16.5176,
         "era": "6th century AD", "type": "Medieval Monastic", "continent": "Europe",
         "note": "Cassiodorus' scriptorium preserved classical works"},
        {"name": "Palatine Library", "city": "Rome", "country": "Italy",
         "lat": 41.8892, "lon": 12.4874, "era": "28 BC",
         "type": "Roman Imperial", "continent": "Europe",
         "note": "Founded by Augustus on the Palatine Hill"},
        {"name": "Library of Timgad", "city": "Timgad", "country": "Algeria",
         "lat": 35.4847, "lon": 6.4687, "era": "3rd century AD",
         "type": "Roman Provincial", "continent": "Africa",
         "note": "Best preserved example of a Roman provincial library"},
        {"name": "Library of the Serapeum", "city": "Alexandria", "country": "Egypt",
         "lat": 31.1849, "lon": 29.8961, "era": "3rd century BC",
         "type": "Ancient", "continent": "Africa",
         "note": "Daughter library of the Great Library, in the Temple of Serapis"},
        {"name": "Hattusa Royal Archives", "city": "Bogazkoy", "country": "Turkey",
         "lat": 40.0192, "lon": 34.6157, "era": "14th century BC",
         "type": "Hittite", "continent": "Asia",
         "note": "Over 30,000 cuneiform tablets of the Hittite empire"},
    ]


def _beautiful_libraries():
    """20+ architecturally stunning libraries."""
    return [
        {"name": "Strahov Monastery Library", "city": "Prague",
         "country": "Czech Republic", "lat": 50.0862, "lon": 14.3886,
         "style": "Baroque", "built": "1679", "continent": "Europe",
         "note": "Theological and Philosophical Halls with stunning ceiling frescoes"},
        {"name": "Admont Abbey Library", "city": "Admont", "country": "Austria",
         "lat": 47.5752, "lon": 14.4615, "style": "Baroque", "built": "1776",
         "continent": "Europe",
         "note": "Largest monastery library in the world"},
        {"name": "Trinity College Long Room", "city": "Dublin", "country": "Ireland",
         "lat": 53.3440, "lon": -6.2543, "style": "Baroque/Georgian",
         "built": "1732", "continent": "Europe",
         "note": "65-metre long barrel-vaulted chamber, Book of Kells"},
        {"name": "Real Gabinete Português de Leitura", "city": "Rio de Janeiro",
         "country": "Brazil", "lat": -22.9069, "lon": -43.1822,
         "style": "Neo-Manueline", "built": "1887", "continent": "South America",
         "note": "Royal Portuguese Reading Room, ornate ironwork and stained glass"},
        {"name": "George Peabody Library", "city": "Baltimore", "country": "USA",
         "lat": 39.2976, "lon": -76.6155, "style": "Neo-Grec", "built": "1878",
         "continent": "North America",
         "note": "Cathedral of books with soaring atrium and cast-iron balconies"},
        {"name": "Austrian National Library State Hall", "city": "Vienna",
         "country": "Austria", "lat": 48.2066, "lon": 16.3660,
         "style": "Baroque", "built": "1726", "continent": "Europe",
         "note": "Prunksaal with Daniel Gran ceiling fresco"},
        {"name": "Wiblingen Monastery Library", "city": "Ulm", "country": "Germany",
         "lat": 48.3639, "lon": 9.9779, "style": "Rococo", "built": "1744",
         "continent": "Europe",
         "note": "Exuberant Rococo interior with trompe-l'oeil ceiling"},
        {"name": "Biblioteca Joanina", "city": "Coimbra", "country": "Portugal",
         "lat": 40.2070, "lon": -8.4267, "style": "Baroque", "built": "1728",
         "continent": "Europe",
         "note": "Gilded Baroque library at University of Coimbra, bat colony preserves books"},
        {"name": "Klementinum Library", "city": "Prague", "country": "Czech Republic",
         "lat": 50.0862, "lon": 14.4163, "style": "Baroque", "built": "1722",
         "continent": "Europe",
         "note": "Ceiling fresco depicting the Temple of Wisdom"},
        {"name": "Bibliothèque Sainte-Geneviève", "city": "Paris", "country": "France",
         "lat": 48.8469, "lon": 2.3464, "style": "Neo-Renaissance",
         "built": "1851", "continent": "Europe",
         "note": "Henri Labrouste's iron-frame masterpiece"},
        {"name": "Stuttgart City Library", "city": "Stuttgart", "country": "Germany",
         "lat": 48.7898, "lon": 9.1817, "style": "Modern Minimalist",
         "built": "2011", "continent": "Europe",
         "note": "Stark white cube interior by Yi Architects"},
        {"name": "Tianjin Binhai Library", "city": "Tianjin", "country": "China",
         "lat": 39.0462, "lon": 117.7131, "style": "Futuristic",
         "built": "2017", "continent": "Asia",
         "note": "The Eye of Binhai, undulating shelves around spherical auditorium"},
        {"name": "National Library of Finland", "city": "Helsinki", "country": "Finland",
         "lat": 60.1697, "lon": 24.9500, "style": "Neoclassical",
         "built": "1845", "continent": "Europe",
         "note": "Carl Ludvig Engel's white columned hall"},
        {"name": "Abbey Library of Saint Gall", "city": "St. Gallen",
         "country": "Switzerland", "lat": 47.4235, "lon": 9.3774,
         "style": "Rococo", "built": "1767", "continent": "Europe",
         "note": "UNESCO World Heritage, one of the richest medieval libraries"},
        {"name": "Mafra Palace Library", "city": "Mafra", "country": "Portugal",
         "lat": 38.9363, "lon": -9.3266, "style": "Baroque", "built": "1771",
         "continent": "Europe",
         "note": "88-metre long room, colony of bats protect from insects"},
        {"name": "Bibliotheca Hertziana", "city": "Rome", "country": "Italy",
         "lat": 41.9061, "lon": 12.4848, "style": "Contemporary",
         "built": "2013", "continent": "Europe",
         "note": "Juan Navarro Baldeweg's modern reading room in Renaissance palazzo"},
        {"name": "Seattle Central Library", "city": "Seattle", "country": "USA",
         "lat": 47.6067, "lon": -122.3327, "style": "Deconstructivist",
         "built": "2004", "continent": "North America",
         "note": "Rem Koolhaas glass and steel diamond grid"},
        {"name": "Sainte-Marie de la Tourette Library", "city": "Eveux",
         "country": "France", "lat": 45.8192, "lon": 4.6200,
         "style": "Brutalist", "built": "1961", "continent": "Europe",
         "note": "Le Corbusier's Dominican monastery with light cannons"},
        {"name": "Biblioteca Vasconcelos", "city": "Mexico City", "country": "Mexico",
         "lat": 19.4431, "lon": -99.1530, "style": "Contemporary",
         "built": "2006", "continent": "North America",
         "note": "Mega-library with suspended steel shelving and whale skeleton"},
        {"name": "National Library of Kosovo", "city": "Pristina", "country": "Kosovo",
         "lat": 42.6594, "lon": 21.1598, "style": "Brutalist", "built": "1982",
         "continent": "Europe",
         "note": "Distinctive domed structure, love-it-or-hate-it Brutalism"},
        {"name": "Oodi Helsinki Central Library", "city": "Helsinki",
         "country": "Finland", "lat": 60.1740, "lon": 24.9382,
         "style": "Contemporary", "built": "2018", "continent": "Europe",
         "note": "ALA Architects wave-form wood and glass public library"},
        {"name": "Melk Abbey Library", "city": "Melk", "country": "Austria",
         "lat": 48.2278, "lon": 15.3326, "style": "Baroque", "built": "1736",
         "continent": "Europe",
         "note": "Stunning frescoes by Paul Troger above gilded shelves"},
        {"name": "Rampur Raza Library", "city": "Rampur", "country": "India",
         "lat": 28.7931, "lon": 79.0250, "style": "Indo-Islamic",
         "built": "1774", "continent": "Asia",
         "note": "Rare Mughal, Sanskrit, and Persian manuscripts in ornate halls"},
        {"name": "Qatar National Library", "city": "Doha", "country": "Qatar",
         "lat": 25.3166, "lon": 51.4419, "style": "Contemporary",
         "built": "2018", "continent": "Asia",
         "note": "Rem Koolhaas diamond-shaped design with heritage collection below"},
    ]


def _national_archives():
    """20+ national archives around the world."""
    return [
        {"name": "US National Archives", "city": "Washington D.C.", "country": "USA",
         "lat": 38.8937, "lon": -77.0230, "founded": 1934,
         "holdings": "Billions of records", "continent": "North America",
         "note": "Houses the Declaration of Independence, Constitution, Bill of Rights"},
        {"name": "The National Archives (Kew)", "city": "London", "country": "UK",
         "lat": 51.4783, "lon": -0.2821, "founded": 1838,
         "holdings": "11 million records", "continent": "Europe",
         "note": "1000 years of British government records"},
        {"name": "Archives Nationales", "city": "Paris", "country": "France",
         "lat": 48.8609, "lon": 2.3569, "founded": 1790,
         "holdings": "406 km of shelving", "continent": "Europe",
         "note": "Created during the French Revolution"},
        {"name": "Federal Archives of Germany", "city": "Koblenz",
         "country": "Germany", "lat": 50.3596, "lon": 7.5889,
         "founded": 1952, "holdings": "540 km of files", "continent": "Europe",
         "note": "Bundesarchiv, also sites in Berlin and Bayreuth"},
        {"name": "National Archives of India", "city": "New Delhi",
         "country": "India", "lat": 28.6126, "lon": 77.2380,
         "founded": 1891, "holdings": "Vast Mughal and colonial records",
         "continent": "Asia",
         "note": "Imperial Records Department of British India origins"},
        {"name": "National Archives of Japan", "city": "Tokyo", "country": "Japan",
         "lat": 35.6900, "lon": 139.7536, "founded": 1971,
         "holdings": "3.2 million items", "continent": "Asia",
         "note": "Adjacent to the Imperial Palace"},
        {"name": "Russian State Archive", "city": "Moscow", "country": "Russia",
         "lat": 55.7500, "lon": 37.5636, "founded": 1920,
         "holdings": "Millions of files", "continent": "Europe",
         "note": "GARF, Soviet and Russian Federation records"},
        {"name": "National Archives of Australia", "city": "Canberra",
         "country": "Australia", "lat": -35.2906, "lon": 149.1343,
         "founded": 1961, "holdings": "40 million items", "continent": "Oceania",
         "note": "Commonwealth government records since 1901"},
        {"name": "Arquivo Nacional", "city": "Rio de Janeiro", "country": "Brazil",
         "lat": -22.9114, "lon": -43.1690, "founded": 1838,
         "holdings": "55 km of documents", "continent": "South America",
         "note": "Brazilian Imperial and Republican records"},
        {"name": "National Archives of South Africa", "city": "Pretoria",
         "country": "South Africa", "lat": -25.7477, "lon": 28.1880,
         "founded": 1922, "holdings": "Extensive colonial and apartheid records",
         "continent": "Africa",
         "note": "Key resource for apartheid-era research"},
        {"name": "National Archives of the Netherlands", "city": "The Hague",
         "country": "Netherlands", "lat": 52.0810, "lon": 4.3310,
         "founded": 1802, "holdings": "137 km of archives", "continent": "Europe",
         "note": "Nationaal Archief, VOC records among holdings"},
        {"name": "Swedish National Archives", "city": "Stockholm",
         "country": "Sweden", "lat": 59.3252, "lon": 18.0532,
         "founded": 1618, "holdings": "500,000 shelf metres", "continent": "Europe",
         "note": "Riksarkivet, oldest national archive institution in the world"},
        {"name": "Vatican Apostolic Archive", "city": "Vatican City",
         "country": "Vatican", "lat": 41.9024, "lon": 12.4516,
         "founded": 1612, "holdings": "85 km of shelving", "continent": "Europe",
         "note": "Now called Vatican Apostolic Archive, 12 centuries of papal documents"},
        {"name": "National Archives of Canada", "city": "Ottawa", "country": "Canada",
         "lat": 45.3955, "lon": -75.6898, "founded": 1872,
         "holdings": "Over 3 million maps", "continent": "North America",
         "note": "Part of Library and Archives Canada since 2004"},
        {"name": "Archivo General de Indias", "city": "Seville", "country": "Spain",
         "lat": 37.3852, "lon": -5.9924, "founded": 1785,
         "holdings": "43,000 volumes", "continent": "Europe",
         "note": "UNESCO site, documents of the Spanish Empire in the Americas"},
        {"name": "National Archives of China", "city": "Beijing", "country": "China",
         "lat": 39.9068, "lon": 116.3913, "founded": 1959,
         "holdings": "Vast CPC and government records", "continent": "Asia",
         "note": "Also known as the Central Archives"},
        {"name": "Archivio di Stato", "city": "Venice", "country": "Italy",
         "lat": 45.4313, "lon": 12.3360, "founded": 1815,
         "holdings": "70 km of shelving", "continent": "Europe",
         "note": "1000 years of Venetian Republic records in the Frari church"},
        {"name": "National Archives of Korea", "city": "Daejeon",
         "country": "South Korea", "lat": 36.3715, "lon": 127.3722,
         "founded": 1969, "holdings": "Joseon dynasty to modern records",
         "continent": "Asia",
         "note": "Multiple branches including Sejongno"},
        {"name": "National Archives of Nigeria", "city": "Ibadan",
         "country": "Nigeria", "lat": 7.3878, "lon": 3.8963,
         "founded": 1954, "holdings": "Colonial and post-independence records",
         "continent": "Africa",
         "note": "Headquarters in Ibadan with regional branches"},
        {"name": "National Archives of Mexico", "city": "Mexico City",
         "country": "Mexico", "lat": 19.4378, "lon": -99.1422,
         "founded": 1823, "holdings": "375 million documents",
         "continent": "North America",
         "note": "Archivo General de la Nacion in Lecumberri Palace"},
        {"name": "National Archives of Norway", "city": "Oslo", "country": "Norway",
         "lat": 59.9174, "lon": 10.7389, "founded": 1817,
         "holdings": "200+ km of shelving", "continent": "Europe",
         "note": "Riksarkivet, medieval and modern Norwegian records"},
        {"name": "National Archives of Egypt", "city": "Cairo", "country": "Egypt",
         "lat": 30.0444, "lon": 31.2357, "founded": 1828,
         "holdings": "Ottoman and Khedival records", "continent": "Africa",
         "note": "Dar al-Watha'iq al-Qawmiyya, records from the Muhammad Ali era"},
    ]


def _rare_book_collections():
    """16+ important rare book collections."""
    return [
        {"name": "Morgan Library & Museum", "city": "New York", "country": "USA",
         "lat": 40.7491, "lon": -73.9812,
         "specialty": "Medieval manuscripts, Gutenberg Bibles",
         "founded": 1906, "continent": "North America",
         "note": "Pierpont Morgan's personal collection, 3 Gutenberg Bibles"},
        {"name": "Huntington Library", "city": "San Marino", "country": "USA",
         "lat": 34.1292, "lon": -118.1146,
         "specialty": "Gutenberg Bible, early Shakespeare",
         "founded": 1919, "continent": "North America",
         "note": "Ellesmere Chaucer and a Gutenberg Bible on vellum"},
        {"name": "Plantin-Moretus Museum", "city": "Antwerp", "country": "Belgium",
         "lat": 51.2178, "lon": 4.3976,
         "specialty": "Early printing, Biblia Polyglotta",
         "founded": 1876, "continent": "Europe",
         "note": "UNESCO World Heritage, oldest printing presses in the world"},
        {"name": "Folger Shakespeare Library", "city": "Washington D.C.",
         "country": "USA", "lat": 38.8897, "lon": -77.0028,
         "specialty": "Shakespeare First Folios",
         "founded": 1932, "continent": "North America",
         "note": "82 copies of the First Folio, largest collection anywhere"},
        {"name": "Beinecke Rare Book Library", "city": "New Haven", "country": "USA",
         "lat": 41.3113, "lon": -72.9268,
         "specialty": "Voynich Manuscript, Gutenberg Bible",
         "founded": 1963, "continent": "North America",
         "note": "Yale University, translucent marble panels filter light"},
        {"name": "Chester Beatty Library", "city": "Dublin", "country": "Ireland",
         "lat": 53.3429, "lon": -6.2672,
         "specialty": "Biblical papyri, Islamic manuscripts",
         "founded": 1950, "continent": "Europe",
         "note": "Earliest known New Testament texts (P45, P46)"},
        {"name": "Biblioteca Medicea Laurenziana", "city": "Florence",
         "country": "Italy", "lat": 43.7744, "lon": 11.2534,
         "specialty": "Medici manuscripts, Virgil codex",
         "founded": 1571, "continent": "Europe",
         "note": "Michelangelo-designed reading room"},
        {"name": "Bibliothèque Mazarine", "city": "Paris", "country": "France",
         "lat": 48.8564, "lon": 2.3372,
         "specialty": "First public library in France",
         "founded": 1643, "continent": "Europe",
         "note": "Cardinal Mazarin's collection, Gutenberg Bible"},
        {"name": "John Rylands Library", "city": "Manchester", "country": "UK",
         "lat": 53.4803, "lon": -2.2484,
         "specialty": "St John Fragment (P52), oldest NT manuscript",
         "founded": 1900, "continent": "Europe",
         "note": "Neo-Gothic masterpiece, University of Manchester"},
        {"name": "Wellcome Library", "city": "London", "country": "UK",
         "lat": 51.5253, "lon": -0.1342,
         "specialty": "History of medicine",
         "founded": 1936, "continent": "Europe",
         "note": "Over 750,000 books on the history of medicine and science"},
        {"name": "Harry Ransom Center", "city": "Austin", "country": "USA",
         "lat": 30.2849, "lon": -97.7411,
         "specialty": "Gutenberg Bible, literary archives",
         "founded": 1957, "continent": "North America",
         "note": "University of Texas, first photograph and Gutenberg Bible"},
        {"name": "Biblioteca Ambrosiana", "city": "Milan", "country": "Italy",
         "lat": 45.4636, "lon": 9.1834,
         "specialty": "Leonardo da Vinci Codex Atlanticus",
         "founded": 1609, "continent": "Europe",
         "note": "One of the first public libraries in Europe"},
        {"name": "Lilly Library", "city": "Bloomington", "country": "USA",
         "lat": 39.1680, "lon": -86.5222,
         "specialty": "Gutenberg Bible, mechanical puzzles",
         "founded": 1960, "continent": "North America",
         "note": "Indiana University, 100,000 rare books including Gutenberg"},
        {"name": "Bibliotheca Bodmeriana", "city": "Cologny", "country": "Switzerland",
         "lat": 46.2560, "lon": 6.1830,
         "specialty": "Biblical papyri, world literature first editions",
         "founded": 1971, "continent": "Europe",
         "note": "UNESCO Memory of the World papyri collection"},
        {"name": "National Library of Scotland", "city": "Edinburgh", "country": "UK",
         "lat": 55.9482, "lon": -3.1918,
         "specialty": "Gutenberg Bible, Scottish literary archives",
         "founded": 1925, "continent": "Europe",
         "note": "Legal deposit library, one of only 49 Gutenberg Bibles"},
        {"name": "Scheide Library", "city": "Princeton", "country": "USA",
         "lat": 40.3497, "lon": -74.6593,
         "specialty": "Gutenberg Bible, Beethoven sketchbooks",
         "founded": 1959, "continent": "North America",
         "note": "Privately assembled, now at Princeton University Library"},
        {"name": "Topkapi Palace Library", "city": "Istanbul", "country": "Turkey",
         "lat": 41.0115, "lon": 28.9833,
         "specialty": "Islamic calligraphy, Ottoman miniatures",
         "founded": 1465, "continent": "Asia",
         "note": "Ottoman sultans' collection of illuminated Qurans and court records"},
    ]


def _dead_sea_scrolls():
    """15+ locations related to Dead Sea Scrolls and ancient manuscripts."""
    return [
        {"name": "Qumran Caves", "city": "Qumran", "country": "Israel/Palestine",
         "lat": 31.7414, "lon": 35.4593, "type": "Discovery Site",
         "era": "1947", "continent": "Asia",
         "note": "Where Bedouin shepherds found the first Dead Sea Scrolls"},
        {"name": "Shrine of the Book", "city": "Jerusalem", "country": "Israel",
         "lat": 31.7728, "lon": 35.2042, "type": "Museum",
         "era": "1965", "continent": "Asia",
         "note": "Israel Museum, houses the Isaiah Scroll and other DSS"},
        {"name": "British Museum", "city": "London", "country": "UK",
         "lat": 51.5194, "lon": -0.1270, "type": "Museum",
         "era": "Ongoing", "continent": "Europe",
         "note": "Codex Sinaiticus fragments, Rosetta Stone, cuneiform tablets"},
        {"name": "Nag Hammadi Site", "city": "Nag Hammadi", "country": "Egypt",
         "lat": 26.0540, "lon": 32.2820, "type": "Discovery Site",
         "era": "1945", "continent": "Africa",
         "note": "Gnostic texts found in sealed jar, Gospel of Thomas"},
        {"name": "Coptic Museum", "city": "Cairo", "country": "Egypt",
         "lat": 30.0059, "lon": 31.2296, "type": "Museum",
         "era": "1908", "continent": "Africa",
         "note": "Houses the Nag Hammadi codices"},
        {"name": "Monastery of Saint Catherine", "city": "Sinai", "country": "Egypt",
         "lat": 28.5562, "lon": 33.9769, "type": "Monastery",
         "era": "565 AD", "continent": "Africa",
         "note": "Codex Sinaiticus discovered here, oldest complete NT manuscript"},
        {"name": "Dunhuang Caves (Mogao)", "city": "Dunhuang", "country": "China",
         "lat": 40.0396, "lon": 94.8054, "type": "Cave Library",
         "era": "1900", "continent": "Asia",
         "note": "Diamond Sutra (868 AD), oldest printed book, sealed cave library"},
        {"name": "Oxyrhynchus", "city": "El Bahnasa", "country": "Egypt",
         "lat": 28.5350, "lon": 30.6590, "type": "Archaeological Site",
         "era": "1896-", "continent": "Africa",
         "note": "Massive papyrus finds including early Christian texts"},
        {"name": "Berlin Papyrus Collection", "city": "Berlin", "country": "Germany",
         "lat": 52.5211, "lon": 13.3969, "type": "Museum",
         "era": "1899", "continent": "Europe",
         "note": "Neues Museum, major papyrus collection including mathematical texts"},
        {"name": "Chester Beatty Papyri Site", "city": "Faiyum", "country": "Egypt",
         "lat": 29.3084, "lon": 30.8428, "type": "Discovery Region",
         "era": "1930s", "continent": "Africa",
         "note": "Early biblical papyri found in the Faiyum region"},
        {"name": "National Library of France (Papyri)", "city": "Paris",
         "country": "France", "lat": 48.8336, "lon": 2.3756,
         "type": "Collection", "era": "Ongoing", "continent": "Europe",
         "note": "Major collection of Egyptian papyri and Coptic manuscripts"},
        {"name": "Geniza at Ben Ezra Synagogue", "city": "Cairo", "country": "Egypt",
         "lat": 30.0053, "lon": 31.2310, "type": "Geniza",
         "era": "1896", "continent": "Africa",
         "note": "Cairo Geniza, 400,000 manuscript fragments spanning 1000 years"},
        {"name": "Turfan Manuscript Sites", "city": "Turfan", "country": "China",
         "lat": 42.9513, "lon": 89.1895, "type": "Archaeological Site",
         "era": "Various", "continent": "Asia",
         "note": "Manichaean, Buddhist, and Christian texts in multiple languages"},
        {"name": "Bodmer Papyri Collection", "city": "Cologny",
         "country": "Switzerland", "lat": 46.2560, "lon": 6.1830,
         "type": "Museum", "era": "1952-", "continent": "Europe",
         "note": "Earliest known copies of Luke and John gospels (P75)"},
        {"name": "Rylands Papyrus P52", "city": "Manchester", "country": "UK",
         "lat": 53.4803, "lon": -2.2484, "type": "Collection",
         "era": "c.125 AD", "continent": "Europe",
         "note": "Oldest known New Testament fragment, Gospel of John"},
        {"name": "Schottenstein Talmud Collection", "city": "New York",
         "country": "USA", "lat": 40.7128, "lon": -74.0060,
         "type": "Collection", "era": "Ongoing", "continent": "North America",
         "note": "Major collection of Talmudic manuscripts at JTS and YIVO"},
    ]


def _printing_press_history():
    """16+ locations in printing history."""
    return [
        {"name": "Gutenberg Museum", "city": "Mainz", "country": "Germany",
         "lat": 49.9994, "lon": 8.2741, "era": "c.1440",
         "figure": "Johannes Gutenberg", "continent": "Europe",
         "note": "Birthplace of movable type printing in Europe, Gutenberg Bibles on display"},
        {"name": "Aldine Press (Aldus Manutius)", "city": "Venice",
         "country": "Italy", "lat": 45.4383, "lon": 12.3355,
         "era": "1494-1515", "figure": "Aldus Manutius", "continent": "Europe",
         "note": "Invented italic type, portable octavo books, the semicolon in print"},
        {"name": "Plantin-Moretus Workshop", "city": "Antwerp", "country": "Belgium",
         "lat": 51.2178, "lon": 4.3976, "era": "1555-1876",
         "figure": "Christophe Plantin", "continent": "Europe",
         "note": "UNESCO World Heritage printing workshop and museum"},
        {"name": "Jikji Printing Site", "city": "Cheongju",
         "country": "South Korea", "lat": 36.6372, "lon": 127.4898,
         "era": "1377", "figure": "Heungdeok Temple", "continent": "Asia",
         "note": "Oldest known book printed with movable metal type"},
        {"name": "William Caxton Site", "city": "London", "country": "UK",
         "lat": 51.4993, "lon": -0.1268, "era": "1476",
         "figure": "William Caxton", "continent": "Europe",
         "note": "First printing press in England, at Westminster Abbey precincts"},
        {"name": "Estienne (Stephanus) Press", "city": "Paris", "country": "France",
         "lat": 48.8490, "lon": 2.3444, "era": "1502-1674",
         "figure": "Robert Estienne", "continent": "Europe",
         "note": "Royal Printers, first verse-numbered Bible, Latin Thesaurus"},
        {"name": "Elzevir Press", "city": "Leiden", "country": "Netherlands",
         "lat": 52.1601, "lon": 4.4970, "era": "1583-1712",
         "figure": "Elzevir Family", "continent": "Europe",
         "note": "Pioneered affordable small-format books across Europe"},
        {"name": "Oxford University Press", "city": "Oxford", "country": "UK",
         "lat": 51.7559, "lon": -1.2588, "era": "1478",
         "figure": "University of Oxford", "continent": "Europe",
         "note": "Oldest university press in the world, still active"},
        {"name": "Cambridge University Press", "city": "Cambridge", "country": "UK",
         "lat": 52.2053, "lon": 0.1218, "era": "1534",
         "figure": "University of Cambridge", "continent": "Europe",
         "note": "Oldest active publisher in the world"},
        {"name": "Subiaco Monastery Press", "city": "Subiaco", "country": "Italy",
         "lat": 41.9247, "lon": 13.0962, "era": "1465",
         "figure": "Sweynheym & Pannartz", "continent": "Europe",
         "note": "First printing press in Italy, introduced printing south of Alps"},
        {"name": "Baskerville Press", "city": "Birmingham", "country": "UK",
         "lat": 52.4862, "lon": -1.8904, "era": "1757",
         "figure": "John Baskerville", "continent": "Europe",
         "note": "Revolutionized typography with the Baskerville typeface"},
        {"name": "Benjamin Franklin Print Shop", "city": "Philadelphia",
         "country": "USA", "lat": 39.9523, "lon": -75.1478,
         "era": "1728", "figure": "Benjamin Franklin",
         "continent": "North America",
         "note": "Printing house and Pennsylvania Gazette"},
        {"name": "Kelmscott Press", "city": "London", "country": "UK",
         "lat": 51.4860, "lon": -0.2138, "era": "1891-1898",
         "figure": "William Morris", "continent": "Europe",
         "note": "Arts and Crafts movement fine press, Kelmscott Chaucer"},
        {"name": "Bi Sheng Movable Type Origin", "city": "Hangzhou",
         "country": "China", "lat": 30.2741, "lon": 120.1551,
         "era": "c.1040", "figure": "Bi Sheng", "continent": "Asia",
         "note": "Invented the first movable type system using ceramic pieces"},
        {"name": "Doves Press", "city": "London", "country": "UK",
         "lat": 51.4883, "lon": -0.2368, "era": "1900-1916",
         "figure": "T.J. Cobden-Sanderson", "continent": "Europe",
         "note": "Famous Doves Type thrown into Thames, recovered in 2015"},
        {"name": "Imprimerie Nationale", "city": "Paris", "country": "France",
         "lat": 48.8348, "lon": 2.3892, "era": "1640",
         "figure": "French State", "continent": "Europe",
         "note": "Official French government printing office since Louis XIII"},
        {"name": "Woodblock Printing at Jiajiang", "city": "Jiajiang",
         "country": "China", "lat": 29.7355, "lon": 103.5494,
         "era": "7th century", "figure": "Chinese craftsmen", "continent": "Asia",
         "note": "Oldest surviving woodblock printing tradition, UNESCO heritage"},
    ]


def _bookshop_capitals():
    """20+ legendary bookshops around the world."""
    return [
        {"name": "Shakespeare and Company", "city": "Paris", "country": "France",
         "lat": 48.8526, "lon": 2.3471, "type": "Independent",
         "founded": 1951, "continent": "Europe",
         "note": "Iconic Left Bank bookshop opposite Notre-Dame, literary haven"},
        {"name": "Powell's City of Books", "city": "Portland", "country": "USA",
         "lat": 45.5231, "lon": -122.6813, "type": "Independent",
         "founded": 1971, "continent": "North America",
         "note": "Largest independent bookstore in the world, entire city block"},
        {"name": "Strand Bookstore", "city": "New York", "country": "USA",
         "lat": 40.7335, "lon": -73.9910, "type": "Independent",
         "founded": 1927, "continent": "North America",
         "note": "18 miles of books on Broadway, NYC institution"},
        {"name": "Libreria Acqua Alta", "city": "Venice", "country": "Italy",
         "lat": 45.4385, "lon": 12.3440, "type": "Independent",
         "founded": 2004, "continent": "Europe",
         "note": "Books stored in gondolas and bathtubs to survive flooding"},
        {"name": "Livraria Lello", "city": "Porto", "country": "Portugal",
         "lat": 41.1468, "lon": -8.6150, "type": "Independent",
         "founded": 1906, "continent": "Europe",
         "note": "Neo-Gothic masterpiece, rumored inspiration for Harry Potter"},
        {"name": "El Ateneo Grand Splendid", "city": "Buenos Aires",
         "country": "Argentina", "lat": -34.5957, "lon": -58.3977,
         "type": "Chain", "founded": 2000, "continent": "South America",
         "note": "Converted 1919 theater with frescoed ceiling and stage-cafe"},
        {"name": "Daunt Books", "city": "London", "country": "UK",
         "lat": 51.5216, "lon": -0.1514, "type": "Independent",
         "founded": 1990, "continent": "Europe",
         "note": "Edwardian oak galleries with long skylight, Marylebone"},
        {"name": "City Lights Bookstore", "city": "San Francisco", "country": "USA",
         "lat": 37.7976, "lon": -122.4064, "type": "Independent",
         "founded": 1953, "continent": "North America",
         "note": "Beat Generation HQ, published Ginsberg's Howl"},
        {"name": "Boekhandel Dominicanen", "city": "Maastricht",
         "country": "Netherlands", "lat": 50.8503, "lon": 5.6875,
         "type": "Chain (Selexyz)", "founded": 2006, "continent": "Europe",
         "note": "13th-century Dominican church converted into a bookstore"},
        {"name": "Atlantis Books", "city": "Oia, Santorini", "country": "Greece",
         "lat": 36.4618, "lon": 25.3756, "type": "Independent",
         "founded": 2004, "continent": "Europe",
         "note": "Cave bookshop on Santorini cliffs, founded by travellers"},
        {"name": "The Bookworm", "city": "Beijing", "country": "China",
         "lat": 39.9332, "lon": 116.4535, "type": "Independent",
         "founded": 2005, "continent": "Asia",
         "note": "Library-bar-event space in Sanlitun, literary festival host"},
        {"name": "Munro's Books", "city": "Victoria", "country": "Canada",
         "lat": 48.4260, "lon": -123.3697, "type": "Independent",
         "founded": 1963, "continent": "North America",
         "note": "Founded by Nobel laureate Alice Munro's ex-husband in heritage building"},
        {"name": "Librairie Avant-Garde", "city": "Nanjing", "country": "China",
         "lat": 32.0584, "lon": 118.7745, "type": "Independent",
         "founded": 1999, "continent": "Asia",
         "note": "Underground car park turned vast bookstore, cross-shaped light"},
        {"name": "Selexyz Dominicanen", "city": "Zwolle", "country": "Netherlands",
         "lat": 52.5100, "lon": 6.0949, "type": "Chain",
         "founded": 2013, "continent": "Europe",
         "note": "Another converted church bookshop in the Netherlands"},
        {"name": "Hay-on-Wye (Town of Books)", "city": "Hay-on-Wye",
         "country": "UK", "lat": 52.0746, "lon": -3.1242,
         "type": "Town", "founded": 1961, "continent": "Europe",
         "note": "Self-declared independent kingdom of books, annual literary festival"},
        {"name": "Bart's Books", "city": "Ojai", "country": "USA",
         "lat": 34.4480, "lon": -119.2429, "type": "Independent (Outdoor)",
         "founded": 1964, "continent": "North America",
         "note": "Largest outdoor bookstore in the world, honor system"},
        {"name": "Tattered Cover", "city": "Denver", "country": "USA",
         "lat": 39.7312, "lon": -104.9826, "type": "Independent",
         "founded": 1971, "continent": "North America",
         "note": "Beloved Denver institution across multiple floors"},
        {"name": "Libreria Gandhi", "city": "Mexico City", "country": "Mexico",
         "lat": 19.4068, "lon": -99.1675, "type": "Chain",
         "founded": 1971, "continent": "North America",
         "note": "Iconic Mexican bookstore chain with purple branding"},
        {"name": "John K. King Used & Rare Books", "city": "Detroit",
         "country": "USA", "lat": 42.3346, "lon": -83.0578,
         "type": "Independent", "founded": 1983, "continent": "North America",
         "note": "Four-story former glove factory packed with a million books"},
        {"name": "Honesty Bookshop", "city": "Hay-on-Wye", "country": "UK",
         "lat": 52.0740, "lon": -3.1250, "type": "Outdoor/Honor",
         "founded": 1970, "continent": "Europe",
         "note": "Open-air shelves against the castle wall, pay what you think"},
        {"name": "Tsutaya Books Daikanyama", "city": "Tokyo", "country": "Japan",
         "lat": 35.6497, "lon": 139.6986, "type": "Chain",
         "founded": 2011, "continent": "Asia",
         "note": "Klein Dytham Architecture T-Site, lifestyle and design bookshop"},
    ]


def _secret_libraries():
    """15+ secret, underground, and hidden libraries."""
    return [
        {"name": "Vatican Apostolic Archive", "city": "Vatican City",
         "country": "Vatican", "lat": 41.9024, "lon": 12.4516,
         "type": "Restricted Archive", "era": "1612", "continent": "Europe",
         "note": "Formerly Secret Archives, 85 km of shelves, scholars only by permission"},
        {"name": "Herculaneum Papyri Villa", "city": "Herculaneum",
         "country": "Italy", "lat": 40.8058, "lon": 14.3478,
         "type": "Buried Library", "era": "79 AD", "continent": "Europe",
         "note": "Villa of the Papyri, scrolls buried by Vesuvius, being read by AI and X-ray"},
        {"name": "Monastery of Saint Catherine Library", "city": "Sinai",
         "country": "Egypt", "lat": 28.5562, "lon": 33.9769,
         "type": "Fortress Library", "era": "6th century", "continent": "Africa",
         "note": "Remote desert monastery, second largest early manuscript collection after Vatican"},
        {"name": "Iron Mountain Underground Vault", "city": "Boyers",
         "country": "USA", "lat": 41.1076, "lon": -79.8978,
         "type": "Underground Vault", "era": "1951", "continent": "North America",
         "note": "220 acres of limestone caverns storing billions of documents and film"},
        {"name": "Svalbard Global Seed Vault (Arctic Archive)",
         "city": "Longyearbyen", "country": "Norway",
         "lat": 78.2380, "lon": 15.4464, "type": "Arctic Vault",
         "era": "2017", "continent": "Europe",
         "note": "Arctic World Archive stores digital data alongside seed vault in permafrost"},
        {"name": "Stasi Records Archive", "city": "Berlin", "country": "Germany",
         "lat": 52.5144, "lon": 13.4875, "type": "Secret Police Archive",
         "era": "1990", "continent": "Europe",
         "note": "111 km of files from East German secret police, shredded docs being reassembled"},
        {"name": "Library of Matenadaran", "city": "Yerevan", "country": "Armenia",
         "lat": 40.1920, "lon": 44.5210,
         "type": "Ancient Manuscript Repository", "era": "5th century",
         "continent": "Asia",
         "note": "17,000 Armenian manuscripts, one of the oldest repositories in the world"},
        {"name": "Sakya Monastery Library", "city": "Sakya",
         "country": "China (Tibet)", "lat": 28.8944, "lon": 88.0178,
         "type": "Hidden Wall Library", "era": "11th century", "continent": "Asia",
         "note": "60-metre wall of scriptures discovered behind a 750-year-old wall"},
        {"name": "Library Cave (Dunhuang Cave 17)", "city": "Dunhuang",
         "country": "China", "lat": 40.0396, "lon": 94.8054,
         "type": "Sealed Cave Library", "era": "Sealed c.1000 AD",
         "continent": "Asia",
         "note": "40,000 manuscripts sealed in a cave for 900 years, discovered 1900"},
        {"name": "Hereford Cathedral Chained Library", "city": "Hereford",
         "country": "UK", "lat": 52.0543, "lon": -2.7164,
         "type": "Chained Library", "era": "1611", "continent": "Europe",
         "note": "Largest surviving chained library in the world, Mappa Mundi"},
        {"name": "Bibliotheca Corviniana Remnants", "city": "Budapest",
         "country": "Hungary", "lat": 47.4963, "lon": 19.0398,
         "type": "Dispersed Collection", "era": "15th century",
         "continent": "Europe",
         "note": "Matthias Corvinus' legendary library, scattered across Europe after Ottoman invasion"},
        {"name": "Malatestiana Library", "city": "Cesena", "country": "Italy",
         "lat": 44.1396, "lon": 12.2429, "type": "First Public Library",
         "era": "1454", "continent": "Europe",
         "note": "First European civic library, original chained manuscripts intact"},
        {"name": "Al-Qarawiyyin Library", "city": "Fez", "country": "Morocco",
         "lat": 34.0639, "lon": -4.9738, "type": "Mosque Library",
         "era": "859 AD", "continent": "Africa",
         "note": "Oldest continually operating library in the world, restored 2016"},
        {"name": "Timbuktu Private Libraries", "city": "Timbuktu",
         "country": "Mali", "lat": 16.7735, "lon": -3.0074,
         "type": "Hidden Private", "era": "13th century", "continent": "Africa",
         "note": "Families hid manuscripts from extremists, smuggled to Bamako in 2013"},
        {"name": "Marsh's Library", "city": "Dublin", "country": "Ireland",
         "lat": 53.3396, "lon": -6.2717, "type": "Caged Reading",
         "era": "1701", "continent": "Europe",
         "note": "Ireland's first public library, readers locked in cages with rare books"},
        {"name": "Chetham's Library", "city": "Manchester", "country": "UK",
         "lat": 53.4858, "lon": -2.2440, "type": "Hidden Medieval",
         "era": "1653", "continent": "Europe",
         "note": "Oldest free public reference library in the English-speaking world"},
        {"name": "Ethiopian Monasteries (Lake Tana)", "city": "Bahir Dar",
         "country": "Ethiopia", "lat": 11.5936, "lon": 37.3886,
         "type": "Island Monastery", "era": "14th century", "continent": "Africa",
         "note": "Remote island monasteries with illuminated Ge'ez manuscripts"},
    ]


def _digital_libraries():
    """15+ digital library and data center locations."""
    return [
        {"name": "Internet Archive HQ", "city": "San Francisco", "country": "USA",
         "lat": 37.7824, "lon": -122.4716, "type": "Digital Archive",
         "founded": 1996, "continent": "North America",
         "note": "Wayback Machine, 735 billion web pages archived, former church"},
        {"name": "Google Books / Google HQ", "city": "Mountain View",
         "country": "USA", "lat": 37.4220, "lon": -122.0841,
         "type": "Digitization Project", "founded": 2004,
         "continent": "North America",
         "note": "Over 40 million books scanned, largest digital scanning project"},
        {"name": "Svalbard World Archive (Arctic)", "city": "Longyearbyen",
         "country": "Norway", "lat": 78.2380, "lon": 15.4464,
         "type": "Arctic Digital Vault", "founded": 2017, "continent": "Europe",
         "note": "GitHub Arctic Code Vault, piqlFilm technology in decommissioned coal mine"},
        {"name": "HathiTrust Data Center", "city": "Ann Arbor", "country": "USA",
         "lat": 42.2808, "lon": -83.7430, "type": "Academic Digital Library",
         "founded": 2008, "continent": "North America",
         "note": "17 million digitized volumes from research libraries"},
        {"name": "Europeana / Koninklijke Bibliotheek", "city": "The Hague",
         "country": "Netherlands", "lat": 52.0810, "lon": 4.3265,
         "type": "European Digital Library", "founded": 2008,
         "continent": "Europe",
         "note": "60+ million cultural heritage items from European institutions"},
        {"name": "Digital Public Library of America", "city": "Boston",
         "country": "USA", "lat": 42.3601, "lon": -71.0589,
         "type": "National Digital Library", "founded": 2013,
         "continent": "North America",
         "note": "Aggregates metadata from US libraries, archives, museums"},
        {"name": "Project Gutenberg (Founder's City)", "city": "Urbana",
         "country": "USA", "lat": 40.1106, "lon": -88.2073,
         "type": "Free eBook Library", "founded": 1971,
         "continent": "North America",
         "note": "First digital library, 70,000+ free eBooks, founded by Michael Hart"},
        {"name": "Bibliotheca Alexandrina Digital", "city": "Alexandria",
         "country": "Egypt", "lat": 31.2089, "lon": 29.9097,
         "type": "Digital Preservation", "founded": 2002, "continent": "Africa",
         "note": "Web archive mirror, Internet Archive partner site"},
        {"name": "National Digital Library of India", "city": "Kharagpur",
         "country": "India", "lat": 22.3149, "lon": 87.3105,
         "type": "National Digital Library", "founded": 2016, "continent": "Asia",
         "note": "IIT Kharagpur-managed, 70 million+ digital resources"},
        {"name": "Gallica (BnF Digital)", "city": "Paris", "country": "France",
         "lat": 48.8336, "lon": 2.3756, "type": "National Digital Library",
         "founded": 1997, "continent": "Europe",
         "note": "BnF digital library, 9+ million documents freely available"},
        {"name": "World Digital Library (UNESCO/LoC)", "city": "Washington D.C.",
         "country": "USA", "lat": 38.8887, "lon": -77.0047,
         "type": "UNESCO Initiative", "founded": 2009,
         "continent": "North America",
         "note": "UNESCO and Library of Congress partnership, multilingual access"},
        {"name": "British Library Digital", "city": "Boston Spa", "country": "UK",
         "lat": 53.9023, "lon": -1.3720, "type": "Digitization Center",
         "founded": 2000, "continent": "Europe",
         "note": "Mass digitization facility, document supply centre"},
        {"name": "JSTOR / Ithaka", "city": "New York", "country": "USA",
         "lat": 40.7369, "lon": -73.9903, "type": "Academic Journal Archive",
         "founded": 1995, "continent": "North America",
         "note": "12+ million academic journal articles, books, and primary sources"},
        {"name": "arXiv (Cornell University)", "city": "Ithaca", "country": "USA",
         "lat": 42.4534, "lon": -76.4735, "type": "Open Access Preprints",
         "founded": 1991, "continent": "North America",
         "note": "2.4+ million scientific papers, physics/math/CS preprint server"},
        {"name": "Long Now Foundation", "city": "San Francisco", "country": "USA",
         "lat": 37.7983, "lon": -122.4010, "type": "Long-term Archive",
         "founded": 1996, "continent": "North America",
         "note": "Rosetta Project micro-etched nickel disk, 10,000-year thinking"},
        {"name": "Trove (National Library of Australia)", "city": "Canberra",
         "country": "Australia", "lat": -35.2965, "lon": 149.1294,
         "type": "Aggregation Platform", "founded": 2009, "continent": "Oceania",
         "note": "Australian digitised newspapers, books, images, and music"},
    ]


# ---------------------------------------------------------------------------
# Colors, icons, and data-function registry
# ---------------------------------------------------------------------------

MODE_COLORS = {
    "Greatest Libraries": "#06b6d4",
    "Ancient Libraries": "#d4a406",
    "Beautiful Library Architecture": "#a855f7",
    "National Archives": "#ef4444",
    "Rare Book Collections": "#f59e0b",
    "Dead Sea Scrolls & Ancient Manuscripts": "#10b981",
    "Printing Press History": "#6366f1",
    "Bookshop Capitals": "#ec4899",
    "Secret & Underground Libraries": "#8b5cf6",
    "Digital Library & Data Centers": "#3b82f6",
}

MODE_ICONS = {
    "Greatest Libraries": "🏛️",
    "Ancient Libraries": "🏺",
    "Beautiful Library Architecture": "✨",
    "National Archives": "🗄️",
    "Rare Book Collections": "📜",
    "Dead Sea Scrolls & Ancient Manuscripts": "🪬",
    "Printing Press History": "🖨️",
    "Bookshop Capitals": "📖",
    "Secret & Underground Libraries": "🔒",
    "Digital Library & Data Centers": "💾",
}

MODE_DATA_FN = {
    "Greatest Libraries": _greatest_libraries,
    "Ancient Libraries": _ancient_libraries,
    "Beautiful Library Architecture": _beautiful_libraries,
    "National Archives": _national_archives,
    "Rare Book Collections": _rare_book_collections,
    "Dead Sea Scrolls & Ancient Manuscripts": _dead_sea_scrolls,
    "Printing Press History": _printing_press_history,
    "Bookshop Capitals": _bookshop_capitals,
    "Secret & Underground Libraries": _secret_libraries,
    "Digital Library & Data Centers": _digital_libraries,
}

MODE_DESCRIPTIONS = {
    "Greatest Libraries": (
        "The world's largest and most important libraries by collection size, "
        "cultural significance, and historical importance. From the Library of "
        "Congress with its 170 million items to ancient legal deposit institutions "
        "spanning six continents."
    ),
    "Ancient Libraries": (
        "Sites of the great libraries of antiquity -- from Alexandria and "
        "Pergamum to Ashurbanipal's cuneiform archive and Nalanda's Buddhist "
        "university. Includes Bronze Age tablet archives and medieval Islamic "
        "centres of learning."
    ),
    "Beautiful Library Architecture": (
        "Architecturally stunning libraries spanning Baroque splendour, "
        "Rococo exuberance, Brutalist geometry, and cutting-edge contemporary "
        "design. Every style from Strahov's frescoed ceilings to Tianjin's "
        "futuristic Eye."
    ),
    "National Archives": (
        "Government archives and record offices preserving centuries of "
        "administrative, legal, and cultural documents. From the US National "
        "Archives (home of the Constitution) to the Archivo General de Indias "
        "documenting the Spanish colonial era."
    ),
    "Rare Book Collections": (
        "Major repositories of rare books, incunabula, Gutenberg Bibles, "
        "illuminated manuscripts, and literary treasures. Houses holding the "
        "Voynich Manuscript, Shakespeare First Folios, and Leonardo's codices."
    ),
    "Dead Sea Scrolls & Ancient Manuscripts": (
        "Discovery sites, museums, and collections housing the Dead Sea Scrolls, "
        "Nag Hammadi codices, biblical papyri, the Cairo Geniza, and other "
        "ancient texts that transformed our understanding of history."
    ),
    "Printing Press History": (
        "Key locations in the history of printing -- from Bi Sheng's ceramic type "
        "in Song Dynasty China and Gutenberg's Mainz workshop to the great "
        "scholarly presses of Oxford and Cambridge and the Arts and Crafts revival."
    ),
    "Bookshop Capitals": (
        "Legendary bookshops from Shakespeare and Company in Paris to converted "
        "churches in Maastricht, outdoor stalls in Ojai, and entire towns like "
        "Hay-on-Wye devoted to the printed word."
    ),
    "Secret & Underground Libraries": (
        "Hidden, restricted, sealed, and underground collections -- from the "
        "Vatican archives and Stasi files to libraries buried by volcanoes, "
        "hidden in monastery walls, and locked in Arctic permafrost vaults."
    ),
    "Digital Library & Data Centers": (
        "The digital frontier of knowledge preservation: the Internet Archive's "
        "Wayback Machine, mass digitisation projects like Google Books and "
        "Gallica, arctic data vaults, and open-access repositories like arXiv."
    ),
}


# ---------------------------------------------------------------------------
# Cached data loader
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _load_mode_data(mode: str) -> list[dict]:
    """Return the curated data for a given mode. Cached for 1 hour."""
    fn = MODE_DATA_FN.get(mode)
    if fn is None:
        return []
    return fn()


@st.cache_data(ttl=3600)
def _fetch_wikipedia_summary(name: str) -> str:
    """Fetch a short summary from the Wikipedia REST API for a location name."""
    try:
        safe_title = name.replace(" ", "_")
        url = (
            f"https://en.wikipedia.org/api/rest_v1/page/summary/"
            f"{requests.utils.quote(safe_title)}"
        )
        resp = requests.get(url, timeout=6, headers={
            "User-Agent": "TerraScoutAI/1.0 (library-maps-module)"
        })
        if resp.status_code == 200:
            data = resp.json()
            return data.get("extract", "No summary available.")
        return "Wikipedia summary not found."
    except Exception:
        return "Could not reach Wikipedia API."


# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------

def _build_map(data: list[dict], color: str, mode: str) -> folium.Map:
    """Create a dark-themed folium map with CircleMarkers for each location."""
    if not data:
        return folium.Map(location=[20, 0], zoom_start=2,
                          tiles="CartoDB dark_matter")

    avg_lat = sum(d["lat"] for d in data) / len(data)
    avg_lon = sum(d["lon"] for d in data) / len(data)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=2,
        tiles="CartoDB dark_matter",
        width="100%",
        height="100%",
    )

    icon = MODE_ICONS.get(mode, "📚")

    for item in data:
        name_safe = html_module.escape(str(item.get("name", "")))
        city_safe = html_module.escape(str(item.get("city", "")))
        country_safe = html_module.escape(str(item.get("country", "")))
        note_safe = html_module.escape(str(item.get("note", "")))

        # Build detail rows from available metadata keys
        detail_lines = ""
        for key in ("founded", "volumes", "era", "type", "style", "built",
                     "holdings", "specialty", "figure", "continent"):
            val = item.get(key)
            if val is not None:
                key_label = html_module.escape(
                    key.replace("_", " ").title()
                )
                val_safe = html_module.escape(str(val))
                detail_lines += (
                    f"<tr>"
                    f"<td style='color:#94a3b8;padding:2px 8px 2px 0;"
                    f"font-size:11px;white-space:nowrap;'>{key_label}</td>"
                    f"<td style='color:#e2e8f0;padding:2px 0;"
                    f"font-size:11px;'>{val_safe}</td>"
                    f"</tr>"
                )

        popup_html = f"""
        <div style="
            font-family:'Segoe UI',system-ui,sans-serif;
            min-width:220px;max-width:310px;
            background:#1e293b;color:#e2e8f0;
            border:1px solid {color};border-radius:8px;
            padding:12px;line-height:1.5;
        ">
            <div style="font-size:14px;font-weight:700;color:{color};
                         margin-bottom:4px;">
                {icon} {name_safe}
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-bottom:6px;">
                {city_safe}, {country_safe}
            </div>
            <table style="border-collapse:collapse;width:100%;">
                {detail_lines}
            </table>
            <div style="font-size:11px;color:#cbd5e1;margin-top:6px;
                         border-top:1px solid #334155;padding-top:6px;">
                {note_safe}
            </div>
        </div>
        """

        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{name_safe} -- {city_safe}",
        ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def _compute_stats(data: list[dict], mode: str) -> dict:
    """Compute summary statistics from the data list."""
    total = len(data)
    countries = set(d.get("country", "") for d in data)
    num_countries = len(countries - {""})
    continents = set(d.get("continent", "") for d in data)
    num_continents = len(continents - {""})

    # Attempt to compute a time range
    years = []
    for d in data:
        for key in ("founded", "built"):
            val = d.get(key)
            if isinstance(val, (int, float)):
                years.append(int(val))
            elif isinstance(val, str):
                digits = "".join(c for c in val if c.isdigit())
                if digits:
                    try:
                        years.append(int(digits[:4]))
                    except ValueError:
                        pass

    earliest = min(years) if years else None
    latest = max(years) if years else None

    return {
        "total": total,
        "countries": num_countries,
        "continents": num_continents,
        "earliest": earliest,
        "latest": latest,
    }


def _country_breakdown(data: list[dict]) -> pd.DataFrame:
    """Return a DataFrame with location counts per country."""
    if not data:
        return pd.DataFrame()
    countries = {}
    for d in data:
        c = d.get("country", "Unknown")
        countries[c] = countries.get(c, 0) + 1
    rows = sorted(countries.items(), key=lambda x: -x[1])
    return pd.DataFrame(rows, columns=["Country", "Locations"])


def _continent_breakdown(data: list[dict]) -> pd.DataFrame:
    """Return a DataFrame with location counts per continent."""
    if not data:
        return pd.DataFrame()
    continents = {}
    for d in data:
        c = d.get("continent", "Unknown")
        continents[c] = continents.get(c, 0) + 1
    rows = sorted(continents.items(), key=lambda x: -x[1])
    return pd.DataFrame(rows, columns=["Continent", "Locations"])


# ---------------------------------------------------------------------------
# DataFrame builder
# ---------------------------------------------------------------------------

def _build_dataframe(data: list[dict]) -> pd.DataFrame:
    """Convert the list of dicts into a clean DataFrame."""
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    # Reorder: name first, note last, continent before note
    cols = list(df.columns)
    preferred_start = ["name", "city", "country", "lat", "lon"]
    ordered = [c for c in preferred_start if c in cols]
    middle = [c for c in cols
              if c not in ordered and c not in ("note", "continent")]
    if "continent" in cols:
        middle.append("continent")
    if "note" in cols:
        middle.append("note")
    ordered += middle
    df = df[ordered]
    # Prettify column names
    df.columns = [c.replace("_", " ").title() for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def _apply_filters(data: list[dict], search_text: str,
                   continent_filter: str) -> list[dict]:
    """Filter data by search text and continent."""
    filtered = data
    if continent_filter and continent_filter != "All":
        filtered = [d for d in filtered
                    if d.get("continent", "") == continent_filter]
    if search_text:
        low = search_text.lower()
        filtered = [
            d for d in filtered
            if low in d.get("name", "").lower()
            or low in d.get("city", "").lower()
            or low in d.get("country", "").lower()
            or low in d.get("note", "").lower()
        ]
    return filtered


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_library_maps_tab():
    """Render the Libraries & Archives Maps tab for TerraScout AI."""

    # ---- Tab header ----
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>📚 Libraries & Archives Maps</h4>'
        '<p>Greatest libraries, ancient archives, and rare book '
        'collections worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    modes = list(MODE_DATA_FN.keys())
    selected_mode = st.selectbox(
        "Map Mode",
        modes,
        index=0,
        help="Choose a thematic map of libraries, archives, or book history sites.",
    )

    # ---- Load raw data ----
    raw_data = _load_mode_data(selected_mode)
    color = MODE_COLORS.get(selected_mode, "#06b6d4")
    icon = MODE_ICONS.get(selected_mode, "📚")

    if not raw_data:
        st.warning("No data available for this mode.")
        return

    # ---- Filters row ----
    filter_cols = st.columns([2, 1])
    with filter_cols[0]:
        search_text = st.text_input(
            "Search locations",
            placeholder="Type a name, city, or keyword...",
            key="lib_search",
        )
    with filter_cols[1]:
        continents = sorted(
            set(d.get("continent", "Unknown") for d in raw_data)
        )
        continent_options = ["All"] + continents
        continent_filter = st.selectbox(
            "Continent", continent_options, index=0, key="lib_continent"
        )

    data = _apply_filters(raw_data, search_text, continent_filter)

    if not data:
        st.info("No locations match your filters. Try broadening your search.")
        return

    # ---- Stats row ----
    stats = _compute_stats(data, selected_mode)
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.metric("Locations", stats["total"])
    with s2:
        st.metric("Countries", stats["countries"])
    with s3:
        st.metric("Continents", stats["continents"])
    with s4:
        if stats["earliest"] is not None:
            label = str(stats["earliest"])
            if stats["earliest"] < 0:
                label = f"{abs(stats['earliest'])} BC"
            st.metric("Earliest", label)
        else:
            st.metric("Earliest", "N/A")
    with s5:
        if stats["latest"] is not None:
            st.metric("Latest", str(stats["latest"]))
        else:
            st.metric("Latest", "N/A")

    # ---- Description blurb ----
    desc = MODE_DESCRIPTIONS.get(selected_mode, "")
    if desc:
        st.markdown(
            f"<div style='background:rgba(30,41,59,0.6);"
            f"border-left:3px solid {color};"
            f"padding:10px 14px;border-radius:4px;margin:8px 0 12px 0;"
            f"color:#cbd5e1;font-size:13px;line-height:1.6;'>"
            f"{icon} {html_module.escape(desc)}</div>",
            unsafe_allow_html=True,
        )

    # ---- Folium map ----
    m = _build_map(data, color, selected_mode)
    st_html(m._repr_html_(), height=500)

    # ---- Breakdown section ----
    st.markdown("---")
    bc1, bc2 = st.columns(2)
    with bc1:
        st.markdown(f"**Country Breakdown** ({icon})")
        country_df = _country_breakdown(data)
        if not country_df.empty:
            st.dataframe(country_df, use_container_width=True, hide_index=True)
    with bc2:
        st.markdown(f"**Continent Breakdown** ({icon})")
        continent_df = _continent_breakdown(data)
        if not continent_df.empty:
            st.dataframe(continent_df, use_container_width=True,
                         hide_index=True)

    # ---- Wikipedia quick lookup ----
    st.markdown("---")
    st.markdown(f"### {icon} Quick Wikipedia Lookup")
    location_names = [d["name"] for d in data]
    selected_location = st.selectbox(
        "Select a location for a Wikipedia summary",
        location_names,
        index=0,
        key="lib_wiki_select",
    )
    if st.button("Fetch Wikipedia Summary", key="lib_wiki_btn"):
        with st.spinner("Fetching summary..."):
            summary = _fetch_wikipedia_summary(selected_location)
        st.markdown(
            f"<div style='background:rgba(30,41,59,0.5);"
            f"border:1px solid #334155;border-radius:6px;"
            f"padding:12px;color:#e2e8f0;font-size:13px;'>"
            f"<strong>{html_module.escape(selected_location)}</strong>"
            f"<br><br>{html_module.escape(summary)}</div>",
            unsafe_allow_html=True,
        )

    # ---- Full data table ----
    st.markdown("---")
    st.markdown(
        f"### {icon} {html_module.escape(selected_mode)} -- Full Data Table"
    )
    df = _build_dataframe(data)
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)

        # ---- CSV download ----
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        safe_filename = (
            selected_mode.lower()
            .replace(" ", "_")
            .replace("&", "and")
        )
        st.download_button(
            label=f"Download {selected_mode} CSV",
            data=csv_bytes,
            file_name=f"terrascout_{safe_filename}.csv",
            mime="text/csv",
        )
    else:
        st.info("No tabular data to display.")
