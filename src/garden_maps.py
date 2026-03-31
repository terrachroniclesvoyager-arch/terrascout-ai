# -*- coding: utf-8 -*-
"""
TerraScout AI - Gardens & Parks Maps Module
Provides 10 garden/park map modes including royal gardens, Japanese gardens,
largest urban parks, tulip/flower gardens, ancient gardens, zen gardens,
tropical gardens, sculpture gardens, maze gardens, and rooftop/vertical gardens.
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


# ---------------------------------------------------------------------------
# Map mode definitions
# ---------------------------------------------------------------------------

MAP_MODES = [
    "Royal & Palace Gardens",
    "Japanese Gardens",
    "Largest Urban Parks",
    "Tulip & Flower Gardens",
    "Ancient & Historical Gardens",
    "Zen & Meditation Gardens",
    "Tropical & Rainforest Gardens",
    "Sculpture Gardens",
    "Maze & Labyrinth Gardens",
    "Rooftop & Vertical Gardens",
]

MAP_DESCRIPTIONS = {
    "Royal & Palace Gardens": "Magnificent gardens of kings, queens, and emperors across centuries of landscape design.",
    "Japanese Gardens": "Serene and meticulously designed Japanese gardens embodying wabi-sabi and harmony with nature.",
    "Largest Urban Parks": "The world's most iconic urban green spaces providing nature within the city.",
    "Tulip & Flower Gardens": "Spectacular flower gardens and tulip fields bursting with color around the globe.",
    "Ancient & Historical Gardens": "Gardens with deep historical roots spanning millennia of horticultural tradition.",
    "Zen & Meditation Gardens": "Contemplative dry-landscape and meditation gardens designed for spiritual reflection.",
    "Tropical & Rainforest Gardens": "Lush tropical botanical gardens showcasing exotic flora from equatorial regions.",
    "Sculpture Gardens": "Open-air museums blending art and nature with world-class sculpture collections.",
    "Maze & Labyrinth Gardens": "Intricate hedge mazes and garden labyrinths that challenge and delight visitors.",
    "Rooftop & Vertical Gardens": "Innovative green architecture including rooftop parks, vertical forests, and sky gardens.",
}

MAP_COLORS = {
    "Royal & Palace Gardens": "#a855f7",
    "Japanese Gardens": "#ec4899",
    "Largest Urban Parks": "#10b981",
    "Tulip & Flower Gardens": "#f59e0b",
    "Ancient & Historical Gardens": "#d97706",
    "Zen & Meditation Gardens": "#8b5cf6",
    "Tropical & Rainforest Gardens": "#14b8a6",
    "Sculpture Gardens": "#3b82f6",
    "Maze & Labyrinth Gardens": "#ef4444",
    "Rooftop & Vertical Gardens": "#06b6d4",
}


# ---------------------------------------------------------------------------
# Curated data constants  (15-25+ entries per mode)
# ---------------------------------------------------------------------------

ROYAL_PALACE_GARDENS = [
    {"name": "Gardens of Versailles", "lat": 48.8049, "lon": 2.1204, "country": "France", "city": "Versailles", "style": "French Formal", "area_ha": 800, "year_created": 1661, "notable": "Fountains, Grand Canal, orangery"},
    {"name": "Kew Royal Botanic Gardens", "lat": 51.4787, "lon": -0.2956, "country": "UK", "city": "London", "style": "English Landscape", "area_ha": 132, "year_created": 1759, "notable": "Palm House, Temperate House, Pagoda"},
    {"name": "Boboli Gardens", "lat": 43.7626, "lon": 11.2480, "country": "Italy", "city": "Florence", "style": "Italian Renaissance", "area_ha": 45, "year_created": 1550, "notable": "Amphitheatre, Neptune Fountain, grottos"},
    {"name": "Schoenbrunn Palace Gardens", "lat": 48.1845, "lon": 16.3122, "country": "Austria", "city": "Vienna", "style": "Baroque", "area_ha": 186, "year_created": 1695, "notable": "Gloriette, Neptune Fountain, Palm House"},
    {"name": "Peterhof Palace Gardens", "lat": 59.8863, "lon": 29.9086, "country": "Russia", "city": "St. Petersburg", "style": "Baroque / French Formal", "area_ha": 607, "year_created": 1714, "notable": "Grand Cascade, 150+ fountains"},
    {"name": "Alhambra Generalife Gardens", "lat": 37.1773, "lon": -3.5856, "country": "Spain", "city": "Granada", "style": "Moorish / Islamic", "area_ha": 12, "year_created": 1319, "notable": "Patio de la Acequia, water channels"},
    {"name": "Gardens of the Royal Palace of Caserta", "lat": 41.0737, "lon": 14.3270, "country": "Italy", "city": "Caserta", "style": "Italian Baroque", "area_ha": 120, "year_created": 1752, "notable": "Grand Cascade, English Garden, Diana fountain"},
    {"name": "Nymphenburg Palace Gardens", "lat": 48.1583, "lon": 11.5036, "country": "Germany", "city": "Munich", "style": "Baroque / English Landscape", "area_ha": 200, "year_created": 1671, "notable": "Amalienburg, canals, pagodas"},
    {"name": "Hampton Court Palace Gardens", "lat": 51.4036, "lon": -0.3378, "country": "UK", "city": "London", "style": "Tudor / Baroque", "area_ha": 24, "year_created": 1530, "notable": "Privy Garden, Great Vine, maze"},
    {"name": "Sanssouci Park", "lat": 52.4042, "lon": 13.0385, "country": "Germany", "city": "Potsdam", "style": "Rococo / English Landscape", "area_ha": 290, "year_created": 1745, "notable": "Terraced vineyards, Orangery, New Palace"},
    {"name": "Tuileries Garden", "lat": 48.8634, "lon": 2.3275, "country": "France", "city": "Paris", "style": "French Formal", "area_ha": 25, "year_created": 1564, "notable": "Sculptures, fountains, Jeu de Paume"},
    {"name": "Royal Palace of La Granja Gardens", "lat": 40.8994, "lon": -4.0037, "country": "Spain", "city": "Segovia", "style": "French Formal / Baroque", "area_ha": 146, "year_created": 1720, "notable": "26 monumental fountains, parterre"},
    {"name": "Herrenhausen Gardens", "lat": 52.3916, "lon": 9.6983, "country": "Germany", "city": "Hanover", "style": "Baroque", "area_ha": 50, "year_created": 1666, "notable": "Great Fountain, hedge theatre, grotto"},
    {"name": "Het Loo Palace Gardens", "lat": 52.2343, "lon": 5.9456, "country": "Netherlands", "city": "Apeldoorn", "style": "Dutch Baroque", "area_ha": 100, "year_created": 1684, "notable": "Symmetrical parterres, Queen's Garden"},
    {"name": "Summer Palace Gardens", "lat": 39.9998, "lon": 116.2755, "country": "China", "city": "Beijing", "style": "Chinese Imperial", "area_ha": 297, "year_created": 1750, "notable": "Kunming Lake, Long Corridor, Marble Boat"},
    {"name": "Topkapi Palace Gardens", "lat": 41.0115, "lon": 28.9833, "country": "Turkey", "city": "Istanbul", "style": "Ottoman", "area_ha": 70, "year_created": 1460, "notable": "Four courtyards, tulip gardens, Bosphorus views"},
    {"name": "Queluz National Palace Gardens", "lat": 38.7503, "lon": -9.2589, "country": "Portugal", "city": "Queluz", "style": "French / Baroque", "area_ha": 16, "year_created": 1747, "notable": "Canal of Tiles, Neptune Garden, topiary"},
    {"name": "Drottningholm Palace Gardens", "lat": 59.3217, "lon": 17.8867, "country": "Sweden", "city": "Stockholm", "style": "Baroque / English Landscape", "area_ha": 27, "year_created": 1662, "notable": "Chinese Pavilion, baroque terraces"},
    {"name": "Aranjuez Royal Palace Gardens", "lat": 40.0368, "lon": -3.6112, "country": "Spain", "city": "Aranjuez", "style": "French / English", "area_ha": 150, "year_created": 1560, "notable": "Parterre Garden, Island Garden, Prince's Garden"},
    {"name": "Royal Botanic Gardens Melbourne", "lat": -37.8304, "lon": 144.9796, "country": "Australia", "city": "Melbourne", "style": "English Landscape", "area_ha": 38, "year_created": 1846, "notable": "Ornamental Lake, fern gully, herb garden"},
    {"name": "Mughal Gardens Rashtrapati Bhavan", "lat": 28.6143, "lon": 77.1994, "country": "India", "city": "New Delhi", "style": "Mughal", "area_ha": 6, "year_created": 1929, "notable": "Terraced design, circular garden, rose beds"},
    {"name": "Isola Bella Gardens", "lat": 45.9070, "lon": 8.5340, "country": "Italy", "city": "Lake Maggiore", "style": "Italian Baroque", "area_ha": 3, "year_created": 1632, "notable": "10 terraces, unicorn statues, exotic plants"},
    {"name": "Chateau de Villandry Gardens", "lat": 47.3406, "lon": 0.5137, "country": "France", "city": "Villandry", "style": "French Renaissance", "area_ha": 7, "year_created": 1536, "notable": "Ornamental kitchen garden, water garden"},
    {"name": "Blenheim Palace Gardens", "lat": 51.8414, "lon": -1.3608, "country": "UK", "city": "Woodstock", "style": "English Landscape", "area_ha": 810, "year_created": 1705, "notable": "Capability Brown landscape, water terraces"},
    {"name": "Forbidden City Imperial Garden", "lat": 39.9208, "lon": 116.3976, "country": "China", "city": "Beijing", "style": "Chinese Imperial", "area_ha": 1.2, "year_created": 1420, "notable": "Ancient cypresses, rockeries, Qianqiu Pavilion"},
]

JAPANESE_GARDENS = [
    {"name": "Kenroku-en", "lat": 36.5625, "lon": 136.6628, "city": "Kanazawa", "country": "Japan", "type": "Strolling", "area_ha": 11.4, "period": "Edo", "notable": "One of Japan's Three Great Gardens, Kotoji lantern"},
    {"name": "Ryoan-ji Rock Garden", "lat": 35.0345, "lon": 135.7185, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape (Karesansui)", "area_ha": 0.025, "period": "Muromachi", "notable": "15 rocks in raked gravel, UNESCO World Heritage"},
    {"name": "Katsura Imperial Villa Garden", "lat": 34.9840, "lon": 135.7131, "city": "Kyoto", "country": "Japan", "type": "Strolling", "area_ha": 5.8, "period": "Edo", "notable": "Masterpiece of Japanese garden design, tea houses"},
    {"name": "Adachi Museum of Art Garden", "lat": 35.3806, "lon": 133.2744, "city": "Yasugi", "country": "Japan", "type": "Viewing", "area_ha": 4.5, "period": "Modern (1970)", "notable": "Ranked #1 Japanese garden for 20+ years"},
    {"name": "Portland Japanese Garden", "lat": 45.5189, "lon": -122.7084, "city": "Portland", "country": "USA", "type": "Strolling / Mixed", "area_ha": 2.2, "period": "Modern (1967)", "notable": "Finest Japanese garden outside Japan"},
    {"name": "Korakuen", "lat": 34.6674, "lon": 133.9340, "city": "Okayama", "country": "Japan", "type": "Strolling", "area_ha": 13.3, "period": "Edo", "notable": "One of Three Great Gardens, crane aviary"},
    {"name": "Ritsurin Garden", "lat": 34.3310, "lon": 134.0457, "city": "Takamatsu", "country": "Japan", "type": "Strolling", "area_ha": 75, "period": "Edo", "notable": "Six ponds, 13 mounds, Mt. Shuin backdrop"},
    {"name": "Koraku-en (Tokyo)", "lat": 35.7084, "lon": 139.7522, "city": "Tokyo", "country": "Japan", "type": "Strolling", "area_ha": 7, "period": "Edo", "notable": "Oldest garden in Tokyo, plum grove"},
    {"name": "Shinjuku Gyoen", "lat": 35.6852, "lon": 139.7100, "city": "Tokyo", "country": "Japan", "type": "Mixed (Japanese/English/French)", "area_ha": 58, "period": "Meiji", "notable": "Cherry blossoms, greenhouse, three garden styles"},
    {"name": "Suizen-ji Joju-en", "lat": 32.7935, "lon": 130.7285, "city": "Kumamoto", "country": "Japan", "type": "Strolling", "area_ha": 7.3, "period": "Edo", "notable": "Miniature Mt. Fuji, Tokaido road replica"},
    {"name": "Huntington Japanese Garden", "lat": 34.1292, "lon": -118.1147, "city": "San Marino", "country": "USA", "type": "Strolling", "area_ha": 4.9, "period": "Modern (1912)", "notable": "Moon bridge, zen court, bonsai collection"},
    {"name": "Morikami Japanese Gardens", "lat": 26.3898, "lon": -80.1688, "city": "Delray Beach", "country": "USA", "type": "Strolling / Mixed", "area_ha": 8, "period": "Modern (1977)", "notable": "Six distinct garden styles, bonsai"},
    {"name": "Nitobe Memorial Garden", "lat": 49.2668, "lon": -123.2631, "city": "Vancouver", "country": "Canada", "type": "Strolling / Tea", "area_ha": 1, "period": "Modern (1960)", "notable": "Top five Japanese gardens outside Japan"},
    {"name": "Saiho-ji (Moss Temple)", "lat": 35.0002, "lon": 135.6833, "city": "Kyoto", "country": "Japan", "type": "Moss / Strolling", "area_ha": 3.5, "period": "Kamakura", "notable": "120+ varieties of moss, UNESCO site"},
    {"name": "Tenryu-ji Garden", "lat": 35.0155, "lon": 135.6738, "city": "Kyoto", "country": "Japan", "type": "Strolling / Pond", "area_ha": 1.2, "period": "Muromachi", "notable": "Borrowed scenery of Arashiyama, UNESCO site"},
    {"name": "Nanzen-ji Garden", "lat": 35.0113, "lon": 135.7928, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape / Strolling", "area_ha": 2, "period": "Muromachi", "notable": "Tiger cubs crossing water, aqueduct"},
    {"name": "Rikugien Garden", "lat": 35.7331, "lon": 139.7459, "city": "Tokyo", "country": "Japan", "type": "Strolling", "area_ha": 8.8, "period": "Edo", "notable": "88 scenes from poetry, weeping cherry"},
    {"name": "Chicago Botanic Japanese Garden", "lat": 42.1497, "lon": -87.7893, "city": "Glencoe", "country": "USA", "type": "Strolling / Island", "area_ha": 3, "period": "Modern (1982)", "notable": "Three islands, dry garden, bonsai collection"},
    {"name": "Cowra Japanese Garden", "lat": -33.8343, "lon": 148.6833, "city": "Cowra", "country": "Australia", "type": "Strolling", "area_ha": 5, "period": "Modern (1979)", "notable": "Largest Japanese garden in Southern Hemisphere"},
    {"name": "Kyoto Botanical Garden", "lat": 35.0518, "lon": 135.7625, "city": "Kyoto", "country": "Japan", "type": "Botanical / Mixed", "area_ha": 24, "period": "Taisho (1924)", "notable": "12,000 plant species, cherry avenue, conservatory"},
]

LARGEST_URBAN_PARKS = [
    {"name": "Central Park", "lat": 40.7829, "lon": -73.9654, "city": "New York", "country": "USA", "area_ha": 341, "year_opened": 1858, "annual_visitors_m": 42, "notable": "Bethesda Fountain, The Mall, Strawberry Fields"},
    {"name": "Hyde Park", "lat": 51.5073, "lon": -0.1657, "city": "London", "country": "UK", "area_ha": 142, "year_opened": 1637, "annual_visitors_m": 10, "notable": "Serpentine Lake, Speakers' Corner, Diana Fountain"},
    {"name": "Bois de Boulogne", "lat": 48.8627, "lon": 2.2491, "city": "Paris", "country": "France", "area_ha": 845, "year_opened": 1852, "annual_visitors_m": 12, "notable": "Bagatelle rose garden, lakes, Louis Vuitton Foundation"},
    {"name": "Ibirapuera Park", "lat": -23.5874, "lon": -46.6576, "city": "Sao Paulo", "country": "Brazil", "area_ha": 158, "year_opened": 1954, "annual_visitors_m": 14, "notable": "Oscar Niemeyer buildings, MAM, Japanese pavilion"},
    {"name": "Griffith Park", "lat": 34.1365, "lon": -118.2940, "city": "Los Angeles", "country": "USA", "area_ha": 1740, "year_opened": 1896, "annual_visitors_m": 10, "notable": "Griffith Observatory, LA Zoo, Hollywood Sign views"},
    {"name": "Stanley Park", "lat": 49.3017, "lon": -123.1417, "city": "Vancouver", "country": "Canada", "area_ha": 405, "year_opened": 1888, "annual_visitors_m": 8, "notable": "Seawall, totem poles, Vancouver Aquarium"},
    {"name": "Chapultepec Park", "lat": 19.4204, "lon": -99.1893, "city": "Mexico City", "country": "Mexico", "area_ha": 686, "year_opened": 1530, "annual_visitors_m": 15, "notable": "Chapultepec Castle, anthropology museum, zoo"},
    {"name": "Phoenix Park", "lat": 53.3559, "lon": -6.3298, "city": "Dublin", "country": "Ireland", "area_ha": 707, "year_opened": 1662, "annual_visitors_m": 10, "notable": "Largest enclosed urban park in Europe, deer herd"},
    {"name": "Englischer Garten", "lat": 48.1642, "lon": 11.6054, "city": "Munich", "country": "Germany", "area_ha": 375, "year_opened": 1789, "annual_visitors_m": 5, "notable": "Chinese Tower beer garden, Eisbach surfing wave"},
    {"name": "Golden Gate Park", "lat": 37.7694, "lon": -122.4862, "city": "San Francisco", "country": "USA", "area_ha": 412, "year_opened": 1870, "annual_visitors_m": 24, "notable": "Japanese Tea Garden, de Young Museum, bison paddock"},
    {"name": "Tiergarten", "lat": 52.5145, "lon": 13.3501, "city": "Berlin", "country": "Germany", "area_ha": 210, "year_opened": 1527, "annual_visitors_m": 7, "notable": "Victory Column, beer gardens, Berlin Zoo"},
    {"name": "Lumpini Park", "lat": 13.7310, "lon": 100.5418, "city": "Bangkok", "country": "Thailand", "area_ha": 57, "year_opened": 1925, "annual_visitors_m": 3, "notable": "Monitor lizards, paddle boats, tai chi area"},
    {"name": "Yoyogi Park", "lat": 35.6717, "lon": 139.6949, "city": "Tokyo", "country": "Japan", "area_ha": 54, "year_opened": 1967, "annual_visitors_m": 20, "notable": "Cherry blossoms, Sunday performers, forested paths"},
    {"name": "El Retiro Park", "lat": 40.4153, "lon": -3.6845, "city": "Madrid", "country": "Spain", "area_ha": 125, "year_opened": 1767, "annual_visitors_m": 8, "notable": "Crystal Palace, Rosaleda rose garden, lake"},
    {"name": "Vondelpark", "lat": 52.3580, "lon": 4.8686, "city": "Amsterdam", "country": "Netherlands", "area_ha": 47, "year_opened": 1865, "annual_visitors_m": 10, "notable": "Open-air theatre, rose garden, Picasso sculpture"},
    {"name": "Parque da Cidade Porto", "lat": 41.1666, "lon": -8.6739, "city": "Porto", "country": "Portugal", "area_ha": 83, "year_opened": 1993, "annual_visitors_m": 3, "notable": "Largest urban park in Portugal, Serralves pavilion"},
    {"name": "Kings Park", "lat": -31.9613, "lon": 115.8324, "city": "Perth", "country": "Australia", "area_ha": 400, "year_opened": 1895, "annual_visitors_m": 6, "notable": "Botanic garden, war memorial, treetop walkway"},
    {"name": "Ueno Park", "lat": 35.7146, "lon": 139.7744, "city": "Tokyo", "country": "Japan", "area_ha": 53, "year_opened": 1873, "annual_visitors_m": 10, "notable": "National Museum, zoo, cherry blossom hanami"},
    {"name": "Millennium Park", "lat": 41.8826, "lon": -87.6226, "city": "Chicago", "country": "USA", "area_ha": 10, "year_opened": 2004, "annual_visitors_m": 25, "notable": "Cloud Gate (The Bean), Crown Fountain, Pritzker Pavilion"},
    {"name": "Villa Borghese", "lat": 41.9142, "lon": 12.4854, "city": "Rome", "country": "Italy", "area_ha": 80, "year_opened": 1903, "annual_visitors_m": 6, "notable": "Borghese Gallery, Pincio terrace, lake, zoo"},
    {"name": "Flushing Meadows Corona Park", "lat": 40.7400, "lon": -73.8408, "city": "New York", "country": "USA", "area_ha": 508, "year_opened": 1939, "annual_visitors_m": 9, "notable": "Unisphere, Queens Museum, USTA tennis center"},
    {"name": "Gorky Park", "lat": 55.7312, "lon": 37.6006, "city": "Moscow", "country": "Russia", "area_ha": 120, "year_opened": 1928, "annual_visitors_m": 10, "notable": "Neskuchny Garden, Muzeon sculpture park, ice rink"},
    {"name": "Royal Park Melbourne", "lat": -37.7884, "lon": 144.9527, "city": "Melbourne", "country": "Australia", "area_ha": 181, "year_opened": 1854, "annual_visitors_m": 4, "notable": "Melbourne Zoo, sports ovals, native garden circle"},
    {"name": "Jardin du Luxembourg", "lat": 48.8462, "lon": 2.3372, "city": "Paris", "country": "France", "area_ha": 23, "year_opened": 1612, "annual_visitors_m": 6, "notable": "Medici Fountain, model sailboats, orchard"},
    {"name": "Balboa Park", "lat": 32.7341, "lon": -117.1441, "city": "San Diego", "country": "USA", "area_ha": 490, "year_opened": 1868, "annual_visitors_m": 12, "notable": "San Diego Zoo, Spanish colonial architecture, museums"},
]

TULIP_FLOWER_GARDENS = [
    {"name": "Keukenhof", "lat": 52.2697, "lon": 4.5462, "city": "Lisse", "country": "Netherlands", "type": "Tulip / Bulb", "area_ha": 32, "season": "Mar-May", "notable": "7 million bulbs, 800 tulip varieties"},
    {"name": "Butchart Gardens", "lat": 48.5634, "lon": -123.4706, "city": "Brentwood Bay", "country": "Canada", "type": "Multi-flower", "area_ha": 22, "season": "Year-round", "notable": "Sunken Garden, Rose Garden, Japanese Garden"},
    {"name": "Dubai Miracle Garden", "lat": 25.0553, "lon": 55.2437, "city": "Dubai", "country": "UAE", "type": "Flower", "area_ha": 7.2, "season": "Nov-May", "notable": "150 million flowers, Airbus A380 floral display"},
    {"name": "Kawachi Fuji Garden", "lat": 33.7243, "lon": 130.6570, "city": "Kitakyushu", "country": "Japan", "type": "Wisteria", "area_ha": 1, "season": "Apr-May", "notable": "Wisteria tunnels, 150 wisteria plants, 20+ varieties"},
    {"name": "Hitachi Seaside Park", "lat": 36.3965, "lon": 140.5939, "city": "Hitachinaka", "country": "Japan", "type": "Nemophila / Multi", "area_ha": 190, "season": "Apr-May / Oct", "notable": "4.5M nemophila, kochia bushes, tulips, daffodils"},
    {"name": "Skagit Valley Tulip Festival", "lat": 48.4540, "lon": -122.3382, "city": "Mount Vernon", "country": "USA", "type": "Tulip", "area_ha": 120, "season": "Apr", "notable": "Largest tulip festival in USA, multiple farms"},
    {"name": "Floriade (Commonwealth Park)", "lat": -35.2920, "lon": 149.1246, "city": "Canberra", "country": "Australia", "type": "Multi-flower", "area_ha": 30, "season": "Sep-Oct", "notable": "Over 1 million flowers, largest flower festival Southern Hemisphere"},
    {"name": "Canadian Tulip Festival", "lat": 45.3895, "lon": -75.7058, "city": "Ottawa", "country": "Canada", "type": "Tulip", "area_ha": 40, "season": "May", "notable": "3 million tulips, Dutch-Canadian friendship heritage"},
    {"name": "Ashikaga Flower Park", "lat": 36.3142, "lon": 139.5194, "city": "Ashikaga", "country": "Japan", "type": "Wisteria / Multi", "area_ha": 9.4, "season": "Apr-May", "notable": "Great Wisteria, illumination festival, 350+ trees"},
    {"name": "Kirstenbosch National Botanical Garden", "lat": -33.9882, "lon": 18.4328, "city": "Cape Town", "country": "South Africa", "type": "Fynbos / Native", "area_ha": 528, "season": "Year-round", "notable": "Tree canopy walkway, protea garden, Table Mountain"},
    {"name": "Powerscourt Gardens", "lat": 53.1843, "lon": -6.1862, "city": "Enniskerry", "country": "Ireland", "type": "Multi-flower / Estate", "area_ha": 19, "season": "May-Sep", "notable": "Italianate terraces, Japanese garden, Triton Lake"},
    {"name": "RHS Garden Wisley", "lat": 51.3215, "lon": -0.4742, "city": "Woking", "country": "UK", "type": "Multi-flower", "area_ha": 97, "season": "Year-round", "notable": "Mixed borders, glasshouse, alpine meadow"},
    {"name": "Giverny (Monet's Garden)", "lat": 49.0759, "lon": 1.5335, "city": "Giverny", "country": "France", "type": "Impressionist / Water", "area_ha": 1, "season": "Apr-Oct", "notable": "Water lilies, Japanese bridge, Monet's house"},
    {"name": "Sissinghurst Castle Garden", "lat": 51.1158, "lon": 0.5830, "city": "Cranbrook", "country": "UK", "type": "Multi-flower / Rooms", "area_ha": 4, "season": "Apr-Oct", "notable": "White Garden, rose garden, cottage garden rooms"},
    {"name": "Descanso Gardens", "lat": 34.2016, "lon": -118.2105, "city": "La Canada Flintridge", "country": "USA", "type": "Camellia / Multi", "area_ha": 60, "season": "Year-round", "notable": "World's largest camellia collection, rose garden, lilacs"},
    {"name": "Mainau Island Flower Garden", "lat": 47.7052, "lon": 9.1919, "city": "Konstanz", "country": "Germany", "type": "Multi-flower", "area_ha": 45, "season": "Mar-Oct", "notable": "Flower Island on Lake Constance, orchid house, dahlias"},
    {"name": "Tulip Garden Srinagar", "lat": 34.0833, "lon": 74.8500, "city": "Srinagar", "country": "India", "type": "Tulip", "area_ha": 12, "season": "Mar-Apr", "notable": "Asia's largest tulip garden, 1.5M+ bulbs, Zabarwan foothills"},
    {"name": "Nong Nooch Tropical Garden", "lat": 12.7617, "lon": 100.9337, "city": "Pattaya", "country": "Thailand", "type": "Tropical / Orchid", "area_ha": 243, "season": "Year-round", "notable": "French garden, Stonehenge replica, cycad collection"},
    {"name": "Tesselaar Tulip Festival", "lat": -37.8508, "lon": 145.3375, "city": "Silvan", "country": "Australia", "type": "Tulip", "area_ha": 22, "season": "Sep-Oct", "notable": "Over 900,000 tulips, largest tulip festival in Australia"},
    {"name": "Holland Tulip Festival", "lat": 42.7876, "lon": -86.1089, "city": "Holland", "country": "USA", "type": "Tulip", "area_ha": 15, "season": "May", "notable": "Dutch heritage, Windmill Island, Veldheer gardens"},
]

ANCIENT_HISTORICAL_GARDENS = [
    {"name": "Hanging Gardens of Babylon (site)", "lat": 32.5362, "lon": 44.4209, "city": "Hillah", "country": "Iraq", "era": "Ancient (c. 600 BC)", "style": "Mesopotamian", "notable": "One of Seven Ancient Wonders, terraced gardens"},
    {"name": "Villa d'Este Gardens", "lat": 41.9633, "lon": 12.7958, "city": "Tivoli", "country": "Italy", "era": "Renaissance (1560)", "style": "Italian Renaissance", "notable": "500 fountains, terraced hillside, water organs"},
    {"name": "Generalife Gardens", "lat": 37.1773, "lon": -3.5858, "city": "Granada", "country": "Spain", "era": "Medieval (1319)", "style": "Moorish / Islamic", "notable": "Patio de la Acequia, Escalera del Agua"},
    {"name": "Humble Administrator's Garden", "lat": 31.3252, "lon": 120.6298, "city": "Suzhou", "country": "China", "era": "Ming Dynasty (1509)", "style": "Chinese Classical", "notable": "UNESCO site, largest Suzhou garden, 48 buildings"},
    {"name": "Lingering Garden", "lat": 31.3128, "lon": 120.5897, "city": "Suzhou", "country": "China", "era": "Ming Dynasty (1593)", "style": "Chinese Classical", "notable": "UNESCO site, famous for rockeries and calligraphy"},
    {"name": "Master of the Nets Garden", "lat": 31.2956, "lon": 120.6377, "city": "Suzhou", "country": "China", "era": "Song Dynasty (1140)", "style": "Chinese Classical", "notable": "UNESCO site, smallest Suzhou garden, moonlit tours"},
    {"name": "Villa Lante Gardens", "lat": 42.4233, "lon": 12.0833, "city": "Bagnaia", "country": "Italy", "era": "Renaissance (1566)", "style": "Italian Mannerist", "notable": "Water chain, geometric parterres, Fountain of Moors"},
    {"name": "Shalimar Bagh", "lat": 34.1415, "lon": 74.8580, "city": "Srinagar", "country": "India", "era": "Mughal (1619)", "style": "Mughal / Persian", "notable": "Terraced garden, Dal Lake, chinar trees"},
    {"name": "Fin Garden", "lat": 33.9833, "lon": 51.4480, "city": "Kashan", "country": "Iran", "era": "Safavid (1590)", "style": "Persian", "notable": "UNESCO site, oldest extant Persian garden, turquoise pools"},
    {"name": "Hadrian's Villa Gardens", "lat": 41.9422, "lon": 12.7744, "city": "Tivoli", "country": "Italy", "era": "Ancient Roman (125 AD)", "style": "Roman", "notable": "UNESCO site, Canopus pool, Maritime Theatre"},
    {"name": "Pasargadae Garden (site)", "lat": 30.1992, "lon": 53.1828, "city": "Pasargadae", "country": "Iran", "era": "Ancient Persian (546 BC)", "style": "Persian Chahar Bagh", "notable": "Oldest known four-fold garden (chahar bagh) design"},
    {"name": "Taj Mahal Gardens", "lat": 27.1751, "lon": 78.0421, "city": "Agra", "country": "India", "era": "Mughal (1632)", "style": "Mughal / Persian", "notable": "Chahar Bagh layout, reflecting pools, 42-acre complex"},
    {"name": "Alcazar Gardens Seville", "lat": 37.3828, "lon": -5.9908, "city": "Seville", "country": "Spain", "era": "Medieval / Renaissance", "style": "Moorish / Renaissance", "notable": "Mercury Pond, Labyrinth, Game of Thrones filming"},
    {"name": "Bagh-e Eram", "lat": 29.6382, "lon": 52.5256, "city": "Shiraz", "country": "Iran", "era": "Qajar (19th c.)", "style": "Persian", "notable": "UNESCO site, cypress-lined avenues, botanical garden"},
    {"name": "Nishat Bagh", "lat": 34.1300, "lon": 74.8684, "city": "Srinagar", "country": "India", "era": "Mughal (1633)", "style": "Mughal / Persian", "notable": "12 terraces, largest Mughal garden in Kashmir"},
    {"name": "Lion Grove Garden", "lat": 31.3222, "lon": 120.6330, "city": "Suzhou", "country": "China", "era": "Yuan Dynasty (1342)", "style": "Chinese Classical", "notable": "UNESCO site, famous labyrinthine rockery"},
    {"name": "Bagh-e Fin (Fin Garden)", "lat": 33.9833, "lon": 51.4480, "city": "Kashan", "country": "Iran", "era": "Safavid (1590)", "style": "Persian", "notable": "UNESCO, turquoise-tiled pools, natural spring"},
    {"name": "Boboli Gardens", "lat": 43.7626, "lon": 11.2480, "city": "Florence", "country": "Italy", "era": "Renaissance (1550)", "style": "Italian Renaissance", "notable": "Amphitheatre, Isolotto island, Grotta del Buontalenti"},
    {"name": "Yu Garden", "lat": 31.2271, "lon": 121.4920, "city": "Shanghai", "country": "China", "era": "Ming Dynasty (1559)", "style": "Chinese Classical", "notable": "Exquisite Jade Rock, dragon walls, 40+ scenic spots"},
    {"name": "Courances Castle Gardens", "lat": 48.4390, "lon": 2.3920, "city": "Courances", "country": "France", "era": "Renaissance (1622)", "style": "French Formal / Water", "notable": "Water mirror parterres, canals, Japanese garden"},
]

ZEN_MEDITATION_GARDENS = [
    {"name": "Ryoan-ji Zen Garden", "lat": 35.0345, "lon": 135.7185, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape (Karesansui)", "period": "Muromachi (1499)", "notable": "15 stones in raked gravel, most famous zen garden"},
    {"name": "Daisen-in Garden", "lat": 35.0437, "lon": 135.7448, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape", "period": "Muromachi (1509)", "notable": "3D landscape in tiny space, river of gravel"},
    {"name": "Tofuku-ji Hojo Garden", "lat": 34.9759, "lon": 135.7727, "city": "Kyoto", "country": "Japan", "type": "Modern Zen", "period": "Showa (1939)", "notable": "Mirei Shigemori design, checkerboard moss, four gardens"},
    {"name": "Portland Japanese Garden Zen", "lat": 45.5189, "lon": -122.7084, "city": "Portland", "country": "USA", "type": "Flat Garden (Hira-niwa)", "period": "Modern (1967)", "notable": "Sand and Stone Garden, authentic outside Japan"},
    {"name": "Ginkaku-ji (Silver Pavilion) Garden", "lat": 35.0270, "lon": 135.7983, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape / Strolling", "period": "Muromachi (1490)", "notable": "Sand cone Kogetsudai, Sea of Silver Sand"},
    {"name": "Zuiho-in Garden", "lat": 35.0444, "lon": 135.7439, "city": "Kyoto", "country": "Japan", "type": "Modern Zen", "period": "Showa (1961)", "notable": "Mirei Shigemori design, hidden cross pattern"},
    {"name": "Taizo-in Garden", "lat": 35.0199, "lon": 135.7224, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape / Pond", "period": "Muromachi (1404)", "notable": "Oldest dry garden in Myoshin-ji complex"},
    {"name": "Konchi-in Garden", "lat": 35.0108, "lon": 135.7923, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape", "period": "Edo (1632)", "notable": "Kobori Enshu design, crane and turtle islands"},
    {"name": "Entsu-ji Garden", "lat": 35.0655, "lon": 135.7755, "city": "Kyoto", "country": "Japan", "type": "Borrowed Scenery (Shakkei)", "period": "Edo (1678)", "notable": "Mt. Hiei borrowed scenery, hedge framing"},
    {"name": "Shitenno-ji Gokuraku-jodo Garden", "lat": 34.6533, "lon": 135.5163, "city": "Osaka", "country": "Japan", "type": "Paradise Garden", "period": "Asuka (593, rebuilt)", "notable": "Pure Land Buddhist paradise garden"},
    {"name": "Adachi Museum Dry Landscape", "lat": 35.3806, "lon": 133.2744, "city": "Yasugi", "country": "Japan", "type": "Viewing Zen", "period": "Modern (1970)", "notable": "Living painting, mountain backdrop, immaculate"},
    {"name": "Bloedel Reserve Japanese Garden", "lat": 47.7131, "lon": -122.5260, "city": "Bainbridge Island", "country": "USA", "type": "Zen / Strolling", "period": "Modern (1986)", "notable": "Reflection Pool, moss garden, Pacific NW setting"},
    {"name": "Kenmin-no-Mori Zen Garden", "lat": 35.0034, "lon": 135.7755, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape", "period": "Kamakura (1202)", "notable": "Oldest Zen temple in Kyoto, Cho-on-tei garden"},
    {"name": "Japanese Garden The Hague", "lat": 52.0835, "lon": 4.3285, "city": "The Hague", "country": "Netherlands", "type": "Zen / Strolling", "period": "Modern (1982)", "notable": "Largest Japanese garden in Europe, tea house"},
    {"name": "Reiun-in Garden", "lat": 35.0436, "lon": 135.7440, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape", "period": "Muromachi", "notable": "Intimate sub-temple of Daitoku-ji, raked gravel"},
    {"name": "Anderson Japanese Gardens", "lat": 42.2583, "lon": -89.0631, "city": "Rockford", "country": "USA", "type": "Strolling / Zen", "period": "Modern (1978)", "notable": "Top-rated Japanese garden in North America"},
    {"name": "Funda-in Garden", "lat": 35.0440, "lon": 135.7445, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape", "period": "Muromachi (1490)", "notable": "Daitoku-ji sub-temple, Sesshu Toyo attributed"},
    {"name": "Kokedera (Moss Garden)", "lat": 35.0002, "lon": 135.6832, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape / Moss", "period": "Kamakura (1339)", "notable": "Reservation-only, 120+ moss species, upper dry garden"},
    {"name": "Joju-in Zen Garden", "lat": 34.9984, "lon": 135.7850, "city": "Kyoto", "country": "Japan", "type": "Dry Landscape", "period": "Edo", "notable": "Hidden gem near Kiyomizu-dera, moon garden"},
]

TROPICAL_RAINFOREST_GARDENS = [
    {"name": "Singapore Botanic Gardens", "lat": 1.3138, "lon": 103.8159, "city": "Singapore", "country": "Singapore", "area_ha": 82, "year_founded": 1859, "notable": "UNESCO site, National Orchid Garden, 10,000+ species"},
    {"name": "Jardim Botanico Rio de Janeiro", "lat": -22.9671, "lon": -43.2247, "city": "Rio de Janeiro", "country": "Brazil", "area_ha": 54, "year_founded": 1808, "notable": "Imperial palm avenue, 6,500+ species, Atlantic Forest"},
    {"name": "Royal Botanic Garden Peradeniya", "lat": 7.2710, "lon": 80.5957, "city": "Kandy", "country": "Sri Lanka", "area_ha": 60, "year_founded": 1821, "notable": "Mahaweli River loop, spice garden, giant bamboo"},
    {"name": "SSR Botanic Garden Pamplemousses", "lat": -20.1087, "lon": 57.5806, "city": "Pamplemousses", "country": "Mauritius", "area_ha": 37, "year_founded": 1770, "notable": "Giant water lilies, talipot palm, spice collection"},
    {"name": "Fairchild Tropical Botanic Garden", "lat": 25.6771, "lon": -80.2738, "city": "Coral Gables", "country": "USA", "area_ha": 34, "year_founded": 1938, "notable": "World-class palm and cycad collection, butterfly garden"},
    {"name": "Jardim Botanico de Brasilia", "lat": -15.8706, "lon": -47.8345, "city": "Brasilia", "country": "Brazil", "area_ha": 526, "year_founded": 1985, "notable": "Cerrado biome plants, medicinal garden, water garden"},
    {"name": "Hawaii Tropical Bioreserve & Garden", "lat": 19.8322, "lon": -155.0923, "city": "Papaikou", "country": "USA", "area_ha": 7, "year_founded": 1984, "notable": "Onomea Falls, 2,000+ tropical species, rainforest valley"},
    {"name": "Bogor Botanical Gardens", "lat": -6.5960, "lon": 106.7972, "city": "Bogor", "country": "Indonesia", "area_ha": 87, "year_founded": 1817, "notable": "15,000+ species, Rafflesia, orchid house, palace grounds"},
    {"name": "Jardin Botanique de Deshaies", "lat": 16.3095, "lon": -61.7847, "city": "Deshaies", "country": "Guadeloupe", "area_ha": 7, "year_founded": 1979, "notable": "Caribbean tropical garden, parrots, water lilies"},
    {"name": "Perdana Botanical Garden KL", "lat": 3.1445, "lon": 101.6872, "city": "Kuala Lumpur", "country": "Malaysia", "area_ha": 92, "year_founded": 1888, "notable": "Orchid & Hibiscus Garden, deer park, bird park"},
    {"name": "Naples Botanical Garden", "lat": 26.1085, "lon": -81.7695, "city": "Naples", "country": "USA", "area_ha": 67, "year_founded": 2009, "notable": "Brazilian Garden, Caribbean Garden, Asian Garden"},
    {"name": "Limbe Botanic Garden", "lat": 4.0190, "lon": 9.2050, "city": "Limbe", "country": "Cameroon", "area_ha": 48, "year_founded": 1892, "notable": "Rare tropical species, Mt. Cameroon backdrop, primates"},
    {"name": "Lyon Arboretum", "lat": 21.3329, "lon": -157.8022, "city": "Honolulu", "country": "USA", "area_ha": 78, "year_founded": 1918, "notable": "Hawaiian rainforest, 5,000+ tropical plants, native plants"},
    {"name": "Queen Sirikit Botanic Garden", "lat": 18.8892, "lon": 98.8619, "city": "Chiang Mai", "country": "Thailand", "area_ha": 375, "year_founded": 1993, "notable": "Glasshouses, canopy walk, ethnobotanical garden"},
    {"name": "Jardin de Balata", "lat": 14.6681, "lon": -61.0856, "city": "Fort-de-France", "country": "Martinique", "area_ha": 3, "year_founded": 1982, "notable": "Treetop walkway, 3,000 tropical species, hummingbirds"},
    {"name": "Rio de Janeiro Botanical Garden Orchidarium", "lat": -22.9680, "lon": -43.2240, "city": "Rio de Janeiro", "country": "Brazil", "area_ha": 2, "year_founded": 2005, "notable": "1,500+ orchid species, dedicated orchid conservatory"},
    {"name": "Aburi Botanical Gardens", "lat": 5.8506, "lon": -0.1683, "city": "Aburi", "country": "Ghana", "area_ha": 65, "year_founded": 1890, "notable": "Akuapem Ridge, tropical timber trees, palm collection"},
    {"name": "Lancetilla Botanical Garden", "lat": 15.7400, "lon": -87.4600, "city": "Tela", "country": "Honduras", "area_ha": 1681, "year_founded": 1926, "notable": "Largest tropical botanical garden in Americas, 1,500+ species"},
    {"name": "Henarathgoda Botanical Garden", "lat": 7.0692, "lon": 79.9972, "city": "Gampaha", "country": "Sri Lanka", "area_ha": 17, "year_founded": 1876, "notable": "First rubber trees in Asia, golden bamboo, cinnamon"},
    {"name": "Gardens by the Bay", "lat": 1.2816, "lon": 103.8636, "city": "Singapore", "country": "Singapore", "area_ha": 101, "year_founded": 2012, "notable": "Supertree Grove, Cloud Forest, Flower Dome"},
]

SCULPTURE_GARDENS = [
    {"name": "Storm King Art Center", "lat": 41.4279, "lon": -74.0568, "city": "Mountainville", "country": "USA", "area_ha": 202, "year_founded": 1960, "artists": "Calder, Serra, Goldsworthy", "notable": "500-acre open-air museum, monumental sculptures"},
    {"name": "Yorkshire Sculpture Park", "lat": 53.6090, "lon": -1.5785, "city": "Wakefield", "country": "UK", "area_ha": 202, "year_founded": 1977, "artists": "Moore, Hepworth, Ai Weiwei", "notable": "500 acres of parkland, underground gallery"},
    {"name": "Vigeland Sculpture Park", "lat": 59.9271, "lon": 10.7005, "city": "Oslo", "country": "Norway", "area_ha": 32, "year_founded": 1940, "artists": "Gustav Vigeland", "notable": "212 bronze and granite sculptures, Monolith"},
    {"name": "Hakone Open-Air Museum", "lat": 35.2494, "lon": 139.0078, "city": "Hakone", "country": "Japan", "area_ha": 7, "year_founded": 1969, "artists": "Picasso, Moore, Niki de Saint Phalle", "notable": "First open-air museum in Japan, hot spring foot bath"},
    {"name": "Kroller-Muller Sculpture Garden", "lat": 52.0967, "lon": 5.8167, "city": "Otterlo", "country": "Netherlands", "area_ha": 25, "year_founded": 1961, "artists": "Rodin, Moore, Dubuffet", "notable": "One of largest sculpture gardens in Europe, 160+ works"},
    {"name": "Inhotim", "lat": -20.1222, "lon": -44.2264, "city": "Brumadinho", "country": "Brazil", "area_ha": 140, "year_founded": 2006, "artists": "Weiwei, Kapoor, Oiticica", "notable": "Largest open-air art center in Latin America, botanical"},
    {"name": "Gibbs Farm", "lat": -36.3167, "lon": 174.4500, "city": "Kaipara Harbour", "country": "New Zealand", "area_ha": 400, "year_founded": 1991, "artists": "Serra, Kapoor, McCall", "notable": "Private farm open limited days, monumental land art"},
    {"name": "Olympic Sculpture Park", "lat": 47.6166, "lon": -122.3554, "city": "Seattle", "country": "USA", "area_ha": 3.6, "year_founded": 2007, "artists": "Calder, Serra, Oldenburg", "notable": "Free urban waterfront park, SAM outdoor collection"},
    {"name": "Fondation Maeght Sculpture Garden", "lat": 43.7020, "lon": 7.0435, "city": "Saint-Paul-de-Vence", "country": "France", "area_ha": 4, "year_founded": 1964, "artists": "Miro, Giacometti, Chagall", "notable": "Miro labyrinth, Giacometti courtyard"},
    {"name": "Chianti Sculpture Park", "lat": 43.3600, "lon": 11.2533, "city": "Pievasciata", "country": "Italy", "area_ha": 3, "year_founded": 2004, "artists": "International contemporary", "notable": "Tuscan woodland setting, site-specific installations"},
    {"name": "Grounds for Sculpture", "lat": 40.2345, "lon": -74.7280, "city": "Hamilton", "country": "USA", "area_ha": 17, "year_founded": 1992, "artists": "Seward Johnson, contemporary", "notable": "Recreations of Impressionist paintings, 270+ sculptures"},
    {"name": "DeCordova Sculpture Park", "lat": 42.4383, "lon": -71.3260, "city": "Lincoln", "country": "USA", "area_ha": 12, "year_founded": 1950, "artists": "New England contemporary", "notable": "30-acre outdoor gallery, museum, Flint's Pond views"},
    {"name": "Frederik Meijer Gardens", "lat": 43.0003, "lon": -85.5789, "city": "Grand Rapids", "country": "USA", "area_ha": 62, "year_founded": 1995, "artists": "da Vinci Horse, Rodin, Degas", "notable": "Japanese Garden, tropical conservatory, 300+ sculptures"},
    {"name": "Middelheim Museum", "lat": 51.1746, "lon": 4.4048, "city": "Antwerp", "country": "Belgium", "area_ha": 12, "year_founded": 1950, "artists": "Rodin, Moore, Ai Weiwei", "notable": "Open-air museum in city park, 215+ modern sculptures"},
    {"name": "Benesse Art Site Naoshima", "lat": 34.4556, "lon": 133.9958, "city": "Naoshima", "country": "Japan", "area_ha": 8, "year_founded": 1992, "artists": "Kusama, Monet, Turrell", "notable": "Island art site, yellow pumpkin, Chichu Art Museum"},
    {"name": "Jupiter Artland", "lat": 55.8936, "lon": -3.4278, "city": "Edinburgh", "country": "UK", "area_ha": 40, "year_founded": 2009, "artists": "Kapoor, Turrell, Gormley", "notable": "Private estate, land art, Cells of Life"},
    {"name": "Ekebergparken Sculpture Park", "lat": 59.8995, "lon": 10.7680, "city": "Oslo", "country": "Norway", "area_ha": 26, "year_founded": 2013, "artists": "Dali, Rodin, Renoir", "notable": "Hillside park overlooking Oslo fjord, 40+ sculptures"},
    {"name": "Crystal Bridges Art Trail", "lat": 36.3828, "lon": -94.2026, "city": "Bentonville", "country": "USA", "area_ha": 49, "year_founded": 2011, "artists": "Turrell, Kusama, contemporary", "notable": "Frank Lloyd Wright house, Skyspace, nature trails"},
    {"name": "Wanas Konst", "lat": 56.0100, "lon": 13.9600, "city": "Knislinge", "country": "Sweden", "area_ha": 30, "year_founded": 1987, "artists": "Kabakov, Plensa, Hirst", "notable": "Art in nature, permanent outdoor collection, castle"},
    {"name": "Santander Sculpture Park", "lat": -22.9050, "lon": -43.1762, "city": "Rio de Janeiro", "country": "Brazil", "area_ha": 5, "year_founded": 2012, "artists": "Weissmann, Krajcberg, Brazilian artists", "notable": "Waterfront location, modern Brazilian sculpture"},
]

MAZE_LABYRINTH_GARDENS = [
    {"name": "Hampton Court Palace Maze", "lat": 51.4036, "lon": -0.3378, "city": "London", "country": "UK", "type": "Hedge", "area_m2": 1350, "year_created": 1690, "notable": "Oldest surviving hedge maze in England, yew hedges"},
    {"name": "Longleat Hedge Maze", "lat": 51.1820, "lon": -2.2820, "city": "Warminster", "country": "UK", "type": "Hedge (3D)", "area_m2": 6000, "year_created": 1975, "notable": "Longest hedge maze in Britain, 2.7 km of paths, 6 bridges"},
    {"name": "Villa Pisani Labyrinth", "lat": 45.4052, "lon": 12.1100, "city": "Stra", "country": "Italy", "type": "Hedge", "area_m2": 3000, "year_created": 1720, "notable": "One of most difficult mazes in Europe, central turret"},
    {"name": "Dole Plantation Pineapple Maze", "lat": 21.5270, "lon": -158.0376, "city": "Wahiawa", "country": "USA", "type": "Hedge (Pineapple shape)", "area_m2": 12500, "year_created": 2008, "notable": "World's largest plant maze (Guinness), 3.11 miles of paths"},
    {"name": "Reignac-sur-Indre Maze", "lat": 47.2250, "lon": 1.0050, "city": "Reignac-sur-Indre", "country": "France", "type": "Sunflower/Corn", "area_m2": 40000, "year_created": 1996, "notable": "Largest plant maze in the world by area, seasonal"},
    {"name": "Masone Labyrinth", "lat": 44.6960, "lon": 10.0960, "city": "Fontanellato", "country": "Italy", "type": "Bamboo", "area_m2": 70000, "year_created": 2015, "notable": "Largest labyrinth in the world, 200,000 bamboo plants"},
    {"name": "Schonbrunn Palace Maze", "lat": 48.1845, "lon": 16.3122, "city": "Vienna", "country": "Austria", "type": "Hedge", "area_m2": 1715, "year_created": 1720, "notable": "Classic hedge maze, labyrinthikon playground"},
    {"name": "Blenheim Palace Marlborough Maze", "lat": 51.8414, "lon": -1.3608, "city": "Woodstock", "country": "UK", "type": "Hedge", "area_m2": 5500, "year_created": 1991, "notable": "World's largest symbolic hedge maze, cannon design"},
    {"name": "Samsoe Labyrinth", "lat": 55.8645, "lon": 10.5850, "city": "Samsoe", "country": "Denmark", "type": "Hedge", "area_m2": 6174, "year_created": 2000, "notable": "World's largest permanent hedge maze by area (2000-2015)"},
    {"name": "Pineapple Garden Maze (Dole)", "lat": 21.5270, "lon": -158.0380, "city": "Wahiawa", "country": "USA", "type": "Tropical hedge", "area_m2": 12500, "year_created": 2008, "notable": "Tropical plants forming world-record maze"},
    {"name": "Chateau de Villandry Maze", "lat": 47.3406, "lon": 0.5137, "city": "Villandry", "country": "France", "type": "Hedge (Hornbeam)", "area_m2": 2000, "year_created": 1906, "notable": "Renaissance ornamental maze, part of famous gardens"},
    {"name": "Peace Maze Castlewellan", "lat": 54.2559, "lon": -5.9336, "city": "Castlewellan", "country": "UK (N. Ireland)", "type": "Hedge (Yew)", "area_m2": 11215, "year_created": 2001, "notable": "Largest permanent hedge maze in Europe, peace symbol"},
    {"name": "Glendurgan Garden Maze", "lat": 50.1100, "lon": -5.1100, "city": "Falmouth", "country": "UK", "type": "Hedge (Cherry laurel)", "area_m2": 800, "year_created": 1833, "notable": "Valley setting, asymmetric design, National Trust"},
    {"name": "Ashcombe Maze", "lat": -38.4167, "lon": 144.8833, "city": "Shoreham", "country": "Australia", "type": "Hedge (Multiple)", "area_m2": 4000, "year_created": 1988, "notable": "Australia's oldest hedge maze, rose maze, lavender"},
    {"name": "Richardson Adventure Farm Corn Maze", "lat": 42.0250, "lon": -88.4000, "city": "Spring Grove", "country": "USA", "type": "Corn", "area_m2": 120000, "year_created": 2001, "notable": "World's largest corn maze, seasonal autumn attraction"},
    {"name": "Itchan Kala Labyrinth", "lat": 41.3794, "lon": 60.3627, "city": "Khiva", "country": "Uzbekistan", "type": "Architectural", "area_m2": 260000, "year_created": 500, "notable": "Ancient walled inner city, labyrinthine streets, UNESCO"},
    {"name": "Chatsworth House Maze", "lat": 53.2270, "lon": -1.6117, "city": "Bakewell", "country": "UK", "type": "Hedge (Yew)", "area_m2": 1800, "year_created": 1962, "notable": "Devonshire estate, 1,209 yew trees, fountain center"},
    {"name": "Luray Caverns Garden Maze", "lat": 38.6634, "lon": -78.4830, "city": "Luray", "country": "USA", "type": "Hedge", "area_m2": 2000, "year_created": 2006, "notable": "Adjacent to Luray Caverns, ornamental hedges"},
    {"name": "Labirinto di Borges", "lat": 44.9628, "lon": 8.3383, "city": "San Giorgio Monferrato", "country": "Italy", "type": "Hedge (Cypress)", "area_m2": 1500, "year_created": 2011, "notable": "Tribute to Jorge Luis Borges, inspired by his writings"},
    {"name": "Drielandenpunt Labyrinth", "lat": 50.7546, "lon": 5.9900, "city": "Vaals", "country": "Netherlands", "type": "Hedge", "area_m2": 3000, "year_created": 1990, "notable": "Tri-border point maze where NL, BE, DE meet"},
    {"name": "Cherry Crest Adventure Farm Maze", "lat": 40.0067, "lon": -76.1750, "city": "Ronks", "country": "USA", "type": "Corn", "area_m2": 20000, "year_created": 2003, "notable": "Amazing Maize Maze, 5 acres, bridges and checkpoints"},
]

ROOFTOP_VERTICAL_GARDENS = [
    {"name": "The High Line", "lat": 40.7480, "lon": -74.0048, "city": "New York", "country": "USA", "type": "Elevated Linear Park", "year_opened": 2009, "length_m": 2330, "notable": "Repurposed rail line, 500+ plant species, public art"},
    {"name": "ACROS Fukuoka Building", "lat": 33.5907, "lon": 130.4017, "city": "Fukuoka", "country": "Japan", "type": "Terraced Green Roof", "year_opened": 1995, "length_m": 0, "notable": "15 stepped terraces, 76 varieties, 50,000 plants"},
    {"name": "Bosco Verticale (Vertical Forest)", "lat": 45.4861, "lon": 9.1904, "city": "Milan", "country": "Italy", "type": "Vertical Forest Tower", "year_opened": 2014, "length_m": 0, "notable": "900 trees, 20,000 plants on two residential towers"},
    {"name": "Gardens by the Bay", "lat": 1.2816, "lon": 103.8636, "city": "Singapore", "country": "Singapore", "type": "Supertree / Vertical", "year_opened": 2012, "length_m": 0, "notable": "Supertree Grove, Cloud Forest, OCBC Skyway"},
    {"name": "One Central Park Sydney", "lat": -33.8918, "lon": 151.1977, "city": "Sydney", "country": "Australia", "type": "Vertical Garden (Building)", "year_opened": 2014, "length_m": 0, "notable": "Patrick Blanc vertical garden, cantilever heliostat"},
    {"name": "Caixa Forum Green Wall", "lat": 40.4111, "lon": -3.6928, "city": "Madrid", "country": "Spain", "type": "Vertical Garden Wall", "year_opened": 2008, "length_m": 0, "notable": "Patrick Blanc design, 15,000 plants, 24m tall"},
    {"name": "Musee du Quai Branly Green Wall", "lat": 48.8611, "lon": 2.2975, "city": "Paris", "country": "France", "type": "Vertical Garden Wall", "year_opened": 2005, "length_m": 0, "notable": "Patrick Blanc, 15,000 plants from Japan/China/Europe"},
    {"name": "Namba Parks", "lat": 34.6620, "lon": 135.5016, "city": "Osaka", "country": "Japan", "type": "Terraced Rooftop Park", "year_opened": 2003, "length_m": 0, "notable": "Canyon-like terraces, 300 plant species, waterfall"},
    {"name": "High Line Canal Denver", "lat": 39.6389, "lon": -104.9300, "city": "Denver", "country": "USA", "type": "Linear Trail Park", "year_opened": 1883, "length_m": 109000, "notable": "71-mile historic canal trail through metro Denver"},
    {"name": "Jewel Changi Airport", "lat": 1.3604, "lon": 103.9893, "city": "Singapore", "country": "Singapore", "type": "Indoor Garden / Waterfall", "year_opened": 2019, "length_m": 0, "notable": "40m indoor waterfall (Rain Vortex), 2,000+ trees"},
    {"name": "Cheonggyecheon Stream", "lat": 37.5695, "lon": 126.9886, "city": "Seoul", "country": "South Korea", "type": "Restored Stream Park", "year_opened": 2005, "length_m": 5800, "notable": "Elevated highway replaced with green stream corridor"},
    {"name": "Parkroyal on Pickering", "lat": 1.2857, "lon": 103.8468, "city": "Singapore", "country": "Singapore", "type": "Sky Gardens Hotel", "year_opened": 2013, "length_m": 0, "notable": "15,000 sqm of sky gardens, twice the floor area"},
    {"name": "Promenade Plantee", "lat": 48.8492, "lon": 2.3734, "city": "Paris", "country": "France", "type": "Elevated Linear Park", "year_opened": 1993, "length_m": 4700, "notable": "Original elevated park (inspired High Line), Viaduc des Arts"},
    {"name": "Sky Garden London", "lat": 51.5114, "lon": -0.0836, "city": "London", "country": "UK", "type": "Rooftop Garden", "year_opened": 2015, "length_m": 0, "notable": "Highest public garden in London (155m), 360 panorama"},
    {"name": "Salesforce Transit Center Park", "lat": 37.7897, "lon": -122.3969, "city": "San Francisco", "country": "USA", "type": "Rooftop Park", "year_opened": 2018, "length_m": 440, "notable": "2.2-hectare rooftop park, amphitheatre, 600 trees"},
    {"name": "Thammasat University Rooftop Farm", "lat": 14.0708, "lon": 100.6027, "city": "Pathum Thani", "country": "Thailand", "type": "Rooftop Farm / Terrace", "year_opened": 2019, "length_m": 0, "notable": "Asia's largest rooftop farm, rice terraces, 22,000 sqm"},
    {"name": "Kampung Admiralty", "lat": 1.4401, "lon": 103.8013, "city": "Singapore", "country": "Singapore", "type": "Rooftop Community Garden", "year_opened": 2017, "length_m": 0, "notable": "World Building of the Year 2018, community farm"},
    {"name": "Luchtsingel Rotterdam", "lat": 51.9225, "lon": 4.4792, "city": "Rotterdam", "country": "Netherlands", "type": "Elevated Pedestrian Bridge/Park", "year_opened": 2015, "length_m": 390, "notable": "Crowdfunded yellow bridge connecting rooftop gardens"},
    {"name": "Copenhill (Amager Bakke)", "lat": 55.6687, "lon": 12.6132, "city": "Copenhagen", "country": "Denmark", "type": "Rooftop Ski Slope / Park", "year_opened": 2019, "length_m": 450, "notable": "Ski slope and hiking trail on waste-to-energy plant"},
    {"name": "Brooklyn Grange Rooftop Farm", "lat": 40.7378, "lon": -73.9248, "city": "New York", "country": "USA", "type": "Rooftop Farm", "year_opened": 2010, "length_m": 0, "notable": "World's largest rooftop soil farm, 2.5 acres total"},
    {"name": "Oasia Hotel Downtown", "lat": 1.2779, "lon": 103.8465, "city": "Singapore", "country": "Singapore", "type": "Vertical Garden Tower", "year_opened": 2016, "length_m": 0, "notable": "Red mesh facade with 21 species of creepers"},
    {"name": "Crossrail Place Roof Garden", "lat": 51.5055, "lon": -0.0182, "city": "London", "country": "UK", "type": "Rooftop Garden", "year_opened": 2015, "length_m": 300, "notable": "Canary Wharf rooftop, ETFE roof, exotic plants"},
    {"name": "Seoullo 7017 Skygarden", "lat": 37.5557, "lon": 126.9713, "city": "Seoul", "country": "South Korea", "type": "Elevated Linear Park", "year_opened": 2017, "length_m": 983, "notable": "Converted highway overpass, 24,000 plants, 228 species"},
    {"name": "Valley (MVRDV Building)", "lat": 52.3469, "lon": 4.9527, "city": "Amsterdam", "country": "Netherlands", "type": "Terraced Green Building", "year_opened": 2022, "length_m": 0, "notable": "Cascading terraces, stone facade, 13,500 plants"},
]


# ---------------------------------------------------------------------------
# Cached data retrieval (wrapping hardcoded data as pattern requires)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _get_royal_gardens() -> list[dict]:
    """Return curated Royal & Palace Gardens data."""
    return ROYAL_PALACE_GARDENS


@st.cache_data(ttl=3600)
def _get_japanese_gardens() -> list[dict]:
    """Return curated Japanese Gardens data."""
    return JAPANESE_GARDENS


@st.cache_data(ttl=3600)
def _get_urban_parks() -> list[dict]:
    """Return curated Largest Urban Parks data."""
    return LARGEST_URBAN_PARKS


@st.cache_data(ttl=3600)
def _get_flower_gardens() -> list[dict]:
    """Return curated Tulip & Flower Gardens data."""
    return TULIP_FLOWER_GARDENS


@st.cache_data(ttl=3600)
def _get_ancient_gardens() -> list[dict]:
    """Return curated Ancient & Historical Gardens data."""
    return ANCIENT_HISTORICAL_GARDENS


@st.cache_data(ttl=3600)
def _get_zen_gardens() -> list[dict]:
    """Return curated Zen & Meditation Gardens data."""
    return ZEN_MEDITATION_GARDENS


@st.cache_data(ttl=3600)
def _get_tropical_gardens() -> list[dict]:
    """Return curated Tropical & Rainforest Gardens data."""
    return TROPICAL_RAINFOREST_GARDENS


@st.cache_data(ttl=3600)
def _get_sculpture_gardens() -> list[dict]:
    """Return curated Sculpture Gardens data."""
    return SCULPTURE_GARDENS


@st.cache_data(ttl=3600)
def _get_maze_gardens() -> list[dict]:
    """Return curated Maze & Labyrinth Gardens data."""
    return MAZE_LABYRINTH_GARDENS


@st.cache_data(ttl=3600)
def _get_rooftop_gardens() -> list[dict]:
    """Return curated Rooftop & Vertical Gardens data."""
    return ROOFTOP_VERTICAL_GARDENS


# ---------------------------------------------------------------------------
# Legend helper
# ---------------------------------------------------------------------------

def _add_legend(m: folium.Map, title: str, color: str, items: list[tuple[str, str]]) -> None:
    """Add a simple HTML legend to a folium map.

    Parameters
    ----------
    m : folium.Map
        The map to add the legend to.
    title : str
        Legend title.
    color : str
        Title accent color.
    items : list[tuple[str, str]]
        List of (label, color_hex) pairs.
    """
    legend_items = "".join(
        f"<li style='margin:2px 0'>"
        f"<span style='display:inline-block;width:12px;height:12px;"
        f"border-radius:50%;background:{c};margin-right:6px;vertical-align:middle'></span>"
        f"<span style='color:#ddd;font-size:12px'>{html_module.escape(label)}</span>"
        f"</li>"
        for label, c in items
    )
    legend_html = (
        f"<div style='position:fixed;bottom:40px;left:40px;z-index:1000;"
        f"background:rgba(15,23,42,0.85);padding:12px 16px;border-radius:8px;"
        f"border:1px solid #2a3550;max-width:220px'>"
        f"<div style='color:{color};font-weight:700;font-size:13px;"
        f"margin-bottom:6px'>{html_module.escape(title)}</div>"
        f"<ul style='list-style:none;padding:0;margin:0'>{legend_items}</ul>"
        f"</div>"
    )
    m.get_root().html.add_child(folium.Element(legend_html))


# ---------------------------------------------------------------------------
# Country statistics helper
# ---------------------------------------------------------------------------

def _country_distribution(data: list[dict]) -> dict[str, int]:
    """Return a {country: count} distribution from a data list."""
    dist: dict[str, int] = {}
    for item in data:
        country = item.get("country", "Unknown")
        dist[country] = dist.get(country, 0) + 1
    return dict(sorted(dist.items(), key=lambda x: x[1], reverse=True))


# ---------------------------------------------------------------------------
# Map builder functions
# ---------------------------------------------------------------------------

def _build_royal_gardens_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Royal & Palace Gardens."""
    data = _get_royal_gardens()
    color = MAP_COLORS["Royal & Palace Gardens"]
    m = folium.Map(location=[35.0, 15.0], zoom_start=3, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Style:</b> {html_module.escape(g['style'])}<br>"
            f"<b>Area:</b> {g['area_ha']} ha<br>"
            f"<b>Created:</b> {g['year_created']}<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=max(5, min(12, g["area_ha"] / 60)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    # Group by style for legend
    styles = sorted(set(g["style"] for g in data))
    style_colors = {
        "French Formal": "#a855f7",
        "English Landscape": "#10b981",
        "Italian Renaissance": "#f59e0b",
        "Baroque": "#ec4899",
        "Chinese Imperial": "#ef4444",
    }
    legend_items = [(s, style_colors.get(s, color)) for s in styles[:8]]
    _add_legend(m, "Royal & Palace Gardens", color, legend_items)
    df = pd.DataFrame(data)
    df = df.sort_values("area_ha", ascending=False).reset_index(drop=True)
    return m, df


def _build_japanese_gardens_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Japanese Gardens."""
    data = _get_japanese_gardens()
    color = MAP_COLORS["Japanese Gardens"]
    m = folium.Map(location=[36.0, 138.0], zoom_start=4, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Type:</b> {html_module.escape(g['type'])}<br>"
            f"<b>Area:</b> {g['area_ha']} ha<br>"
            f"<b>Period:</b> {html_module.escape(g['period'])}<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=max(5, min(12, g["area_ha"] / 5)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    # Group by type for legend
    types = sorted(set(g["type"] for g in data))
    type_colors = {
        "Strolling": "#ec4899",
        "Dry Landscape (Karesansui)": "#8b5cf6",
        "Viewing": "#06b6d4",
        "Moss / Strolling": "#10b981",
    }
    legend_items = [(t, type_colors.get(t, color)) for t in types[:8]]
    _add_legend(m, "Japanese Garden Types", color, legend_items)
    df = pd.DataFrame(data)
    df = df.sort_values("area_ha", ascending=False).reset_index(drop=True)
    return m, df


def _build_urban_parks_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Largest Urban Parks."""
    data = _get_urban_parks()
    color = MAP_COLORS["Largest Urban Parks"]
    m = folium.Map(location=[30.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Area:</b> {g['area_ha']} ha<br>"
            f"<b>Opened:</b> {g['year_opened']}<br>"
            f"<b>Annual Visitors:</b> ~{g['annual_visitors_m']}M<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=max(5, min(14, g["area_ha"] / 100)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    # Legend: top countries
    dist = _country_distribution(data)
    top_countries = list(dist.items())[:6]
    legend_items = [(f"{c} ({n})", color) for c, n in top_countries]
    _add_legend(m, "Urban Parks by Country", color, legend_items)
    df = pd.DataFrame(data)
    df = df.sort_values("area_ha", ascending=False).reset_index(drop=True)
    return m, df


def _build_flower_gardens_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Tulip & Flower Gardens."""
    data = _get_flower_gardens()
    color = MAP_COLORS["Tulip & Flower Gardens"]
    m = folium.Map(location=[35.0, 10.0], zoom_start=2, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Type:</b> {html_module.escape(g['type'])}<br>"
            f"<b>Area:</b> {g['area_ha']} ha<br>"
            f"<b>Season:</b> {html_module.escape(g['season'])}<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=max(5, min(12, g["area_ha"] / 15)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    # Legend: flower types
    ftypes = sorted(set(g["type"] for g in data))
    ftype_colors = {
        "Tulip": "#ef4444", "Tulip / Bulb": "#ef4444",
        "Wisteria": "#a855f7", "Wisteria / Multi": "#a855f7",
        "Multi-flower": "#f59e0b", "Fynbos / Native": "#10b981",
    }
    legend_items = [(ft, ftype_colors.get(ft, color)) for ft in ftypes[:8]]
    _add_legend(m, "Flower Garden Types", color, legend_items)
    df = pd.DataFrame(data)
    df = df.sort_values("area_ha", ascending=False).reset_index(drop=True)
    return m, df


def _build_ancient_gardens_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Ancient & Historical Gardens."""
    data = _get_ancient_gardens()
    color = MAP_COLORS["Ancient & Historical Gardens"]
    m = folium.Map(location=[32.0, 50.0], zoom_start=3, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Era:</b> {html_module.escape(g['era'])}<br>"
            f"<b>Style:</b> {html_module.escape(g['style'])}<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    # Legend: garden styles
    styles = sorted(set(g["style"] for g in data))
    style_colors = {
        "Chinese Classical": "#ef4444",
        "Italian Renaissance": "#f59e0b",
        "Moorish / Islamic": "#10b981",
        "Persian": "#06b6d4",
        "Mughal / Persian": "#8b5cf6",
        "Roman": "#ec4899",
    }
    legend_items = [(s, style_colors.get(s, color)) for s in styles[:8]]
    _add_legend(m, "Historical Garden Styles", color, legend_items)
    df = pd.DataFrame(data)
    return m, df


def _build_zen_gardens_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Zen & Meditation Gardens."""
    data = _get_zen_gardens()
    color = MAP_COLORS["Zen & Meditation Gardens"]
    m = folium.Map(location=[36.0, 136.0], zoom_start=5, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Type:</b> {html_module.escape(g['type'])}<br>"
            f"<b>Period:</b> {html_module.escape(g['period'])}<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


def _build_tropical_gardens_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Tropical & Rainforest Gardens."""
    data = _get_tropical_gardens()
    color = MAP_COLORS["Tropical & Rainforest Gardens"]
    m = folium.Map(location=[5.0, 40.0], zoom_start=2, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Area:</b> {g['area_ha']} ha<br>"
            f"<b>Founded:</b> {g['year_founded']}<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=max(5, min(12, g["area_ha"] / 50)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    df = df.sort_values("area_ha", ascending=False).reset_index(drop=True)
    return m, df


def _build_sculpture_gardens_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Sculpture Gardens."""
    data = _get_sculpture_gardens()
    color = MAP_COLORS["Sculpture Gardens"]
    m = folium.Map(location=[40.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Area:</b> {g['area_ha']} ha<br>"
            f"<b>Founded:</b> {g['year_founded']}<br>"
            f"<b>Artists:</b> {html_module.escape(g['artists'])}<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=max(5, min(12, g["area_ha"] / 20)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    df = df.sort_values("area_ha", ascending=False).reset_index(drop=True)
    return m, df


def _build_maze_gardens_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Maze & Labyrinth Gardens."""
    data = _get_maze_gardens()
    color = MAP_COLORS["Maze & Labyrinth Gardens"]
    m = folium.Map(location=[40.0, 0.0], zoom_start=2, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Type:</b> {html_module.escape(g['type'])}<br>"
            f"<b>Area:</b> {g['area_m2']:,} m&sup2;<br>"
            f"<b>Created:</b> {g['year_created']}<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=max(5, min(14, g["area_m2"] / 8000)),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    df = df.sort_values("area_m2", ascending=False).reset_index(drop=True)
    return m, df


def _build_rooftop_gardens_map() -> tuple[folium.Map, pd.DataFrame]:
    """Build a map of Rooftop & Vertical Gardens."""
    data = _get_rooftop_gardens()
    color = MAP_COLORS["Rooftop & Vertical Gardens"]
    m = folium.Map(location=[25.0, 30.0], zoom_start=2, tiles="CartoDB dark_matter")
    for g in data:
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{color}'>{html_module.escape(g['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(g['city'])}, {html_module.escape(g['country'])}<br>"
            f"<b>Type:</b> {html_module.escape(g['type'])}<br>"
            f"<b>Opened:</b> {g['year_opened']}<br>"
            f"<b>Notable:</b> {html_module.escape(g['notable'])}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(g["name"]),
        ).add_to(m)
    df = pd.DataFrame(data)
    return m, df


# ---------------------------------------------------------------------------
# Stats rendering functions
# ---------------------------------------------------------------------------

def _render_stats_royal_gardens():
    """Render summary statistics for Royal & Palace Gardens."""
    data = _get_royal_gardens()
    total = len(data)
    countries = len(set(g["country"] for g in data))
    total_area = sum(g["area_ha"] for g in data)
    oldest = min(data, key=lambda g: g["year_created"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Gardens", total)
    c2.metric("Countries", countries)
    c3.metric("Total Area", f"{total_area:,.0f} ha")
    c4.metric("Oldest", f"{oldest['year_created']}")


def _render_stats_japanese_gardens():
    """Render summary statistics for Japanese Gardens."""
    data = _get_japanese_gardens()
    total = len(data)
    in_japan = sum(1 for g in data if g["country"] == "Japan")
    outside = total - in_japan
    total_area = sum(g["area_ha"] for g in data)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Gardens", total)
    c2.metric("In Japan", in_japan)
    c3.metric("Outside Japan", outside)
    c4.metric("Total Area", f"{total_area:,.1f} ha")


def _render_stats_urban_parks():
    """Render summary statistics for Largest Urban Parks."""
    data = _get_urban_parks()
    total = len(data)
    total_area = sum(g["area_ha"] for g in data)
    total_visitors = sum(g["annual_visitors_m"] for g in data)
    largest = max(data, key=lambda g: g["area_ha"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Parks", total)
    c2.metric("Combined Area", f"{total_area:,.0f} ha")
    c3.metric("Total Visitors/yr", f"~{total_visitors}M")
    c4.metric("Largest", f"{largest['name']} ({largest['area_ha']} ha)")


def _render_stats_flower_gardens():
    """Render summary statistics for Tulip & Flower Gardens."""
    data = _get_flower_gardens()
    total = len(data)
    countries = len(set(g["country"] for g in data))
    year_round = sum(1 for g in data if "Year-round" in g["season"])
    total_area = sum(g["area_ha"] for g in data)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Gardens", total)
    c2.metric("Countries", countries)
    c3.metric("Year-Round", year_round)
    c4.metric("Total Area", f"{total_area:,.0f} ha")


def _render_stats_ancient_gardens():
    """Render summary statistics for Ancient & Historical Gardens."""
    data = _get_ancient_gardens()
    total = len(data)
    countries = len(set(g["country"] for g in data))
    styles = len(set(g["style"] for g in data))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Gardens", total)
    c2.metric("Countries", countries)
    c3.metric("Garden Styles", styles)
    c4.metric("Eras Covered", "Ancient to Renaissance")


def _render_stats_zen_gardens():
    """Render summary statistics for Zen & Meditation Gardens."""
    data = _get_zen_gardens()
    total = len(data)
    in_kyoto = sum(1 for g in data if g["city"] == "Kyoto")
    types = len(set(g["type"] for g in data))
    countries = len(set(g["country"] for g in data))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Gardens", total)
    c2.metric("In Kyoto", in_kyoto)
    c3.metric("Garden Types", types)
    c4.metric("Countries", countries)


def _render_stats_tropical_gardens():
    """Render summary statistics for Tropical & Rainforest Gardens."""
    data = _get_tropical_gardens()
    total = len(data)
    countries = len(set(g["country"] for g in data))
    total_area = sum(g["area_ha"] for g in data)
    oldest = min(data, key=lambda g: g["year_founded"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Gardens", total)
    c2.metric("Countries", countries)
    c3.metric("Combined Area", f"{total_area:,.0f} ha")
    c4.metric("Oldest", f"{oldest['name']} ({oldest['year_founded']})")


def _render_stats_sculpture_gardens():
    """Render summary statistics for Sculpture Gardens."""
    data = _get_sculpture_gardens()
    total = len(data)
    countries = len(set(g["country"] for g in data))
    total_area = sum(g["area_ha"] for g in data)
    largest = max(data, key=lambda g: g["area_ha"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Gardens", total)
    c2.metric("Countries", countries)
    c3.metric("Combined Area", f"{total_area:,.0f} ha")
    c4.metric("Largest", f"{largest['name']} ({largest['area_ha']} ha)")


def _render_stats_maze_gardens():
    """Render summary statistics for Maze & Labyrinth Gardens."""
    data = _get_maze_gardens()
    total = len(data)
    countries = len(set(g["country"] for g in data))
    types = len(set(g["type"] for g in data))
    largest = max(data, key=lambda g: g["area_m2"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Mazes", total)
    c2.metric("Countries", countries)
    c3.metric("Maze Types", types)
    c4.metric("Largest", f"{largest['name']} ({largest['area_m2']:,} m\u00b2)")


def _render_stats_rooftop_gardens():
    """Render summary statistics for Rooftop & Vertical Gardens."""
    data = _get_rooftop_gardens()
    total = len(data)
    countries = len(set(g["country"] for g in data))
    types = len(set(g["type"] for g in data))
    newest = max(data, key=lambda g: g["year_opened"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", total)
    c2.metric("Countries", countries)
    c3.metric("Garden Types", types)
    c4.metric("Newest", f"{newest['name']} ({newest['year_opened']})")


# ---------------------------------------------------------------------------
# Dispatch maps
# ---------------------------------------------------------------------------

_BUILD_MAP = {
    "Royal & Palace Gardens": _build_royal_gardens_map,
    "Japanese Gardens": _build_japanese_gardens_map,
    "Largest Urban Parks": _build_urban_parks_map,
    "Tulip & Flower Gardens": _build_flower_gardens_map,
    "Ancient & Historical Gardens": _build_ancient_gardens_map,
    "Zen & Meditation Gardens": _build_zen_gardens_map,
    "Tropical & Rainforest Gardens": _build_tropical_gardens_map,
    "Sculpture Gardens": _build_sculpture_gardens_map,
    "Maze & Labyrinth Gardens": _build_maze_gardens_map,
    "Rooftop & Vertical Gardens": _build_rooftop_gardens_map,
}

_RENDER_STATS = {
    "Royal & Palace Gardens": _render_stats_royal_gardens,
    "Japanese Gardens": _render_stats_japanese_gardens,
    "Largest Urban Parks": _render_stats_urban_parks,
    "Tulip & Flower Gardens": _render_stats_flower_gardens,
    "Ancient & Historical Gardens": _render_stats_ancient_gardens,
    "Zen & Meditation Gardens": _render_stats_zen_gardens,
    "Tropical & Rainforest Gardens": _render_stats_tropical_gardens,
    "Sculpture Gardens": _render_stats_sculpture_gardens,
    "Maze & Labyrinth Gardens": _render_stats_maze_gardens,
    "Rooftop & Vertical Gardens": _render_stats_rooftop_gardens,
}


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_garden_maps_tab():
    """Render the Gardens & Parks Maps tab in the Streamlit app."""

    st.markdown(
        '<div class="tab-header emerald">'
        "<h4>\U0001f33a Gardens &amp; Parks Maps</h4>"
        "<p>Famous gardens, royal parks, and landscape architecture worldwide</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ----- Controls -----
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected_mode = st.selectbox(
            "Map Mode",
            MAP_MODES,
            index=0,
            key="garden_maps_mode",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        generate = st.button(
            "Generate Map",
            key="garden_maps_generate",
            type="primary",
        )

    st.caption(MAP_DESCRIPTIONS.get(selected_mode, ""))

    if not generate:
        st.info("Select a map mode and click **Generate Map** to explore gardens and parks worldwide.")
        return

    # ----- Build map -----
    builder = _BUILD_MAP.get(selected_mode)
    if builder is None:
        st.error("Unknown map mode.")
        return

    with st.spinner(f"Building {selected_mode} map..."):
        m, df = builder()

    # ----- Stats metrics -----
    st.markdown("---")
    st.subheader("Summary Statistics")
    stats_fn = _RENDER_STATS.get(selected_mode)
    if stats_fn:
        stats_fn()

    # ----- Folium Map -----
    st.markdown("---")
    st.subheader(f"{selected_mode} Map")
    st_html(m._repr_html_(), height=500)

    # ----- Data Table -----
    st.markdown("---")
    st.subheader("Data Table")
    if not df.empty:
        st.dataframe(df, width="stretch")
    else:
        st.warning("No data to display.")

    # ----- Download CSV -----
    if not df.empty:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        csv_data = csv_buf.getvalue()
        file_label = selected_mode.lower().replace(" ", "_").replace("&", "and")
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name=f"garden_maps_{file_label}.csv",
            mime="text/csv",
            key="garden_maps_csv_download",
        )


# ---------------------------------------------------------------------------
# Allow standalone testing
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    st.set_page_config(page_title="Gardens & Parks Maps", layout="wide")
    render_garden_maps_tab()
