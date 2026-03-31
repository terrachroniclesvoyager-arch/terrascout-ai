# -*- coding: utf-8 -*-
"""
Education & Research Maps module for TerraScout AI.
Explores universities, libraries, research institutions, Nobel Prize origins,
UNESCO sites, museums, science parks, observatories, botanical gardens,
and ancient universities worldwide using free APIs and curated datasets.
"""

import io
import html
import json
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import requests
import streamlit.components.v1 as components
try:
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

from src.overpass_client import query_overpass

# ---------------------------------------------------------------------------
# Hardcoded datasets
# ---------------------------------------------------------------------------

WORLD_UNIVERSITIES = [
    {"name": "Harvard University", "lat": 42.3770, "lon": -71.1167, "country": "USA", "ranking": 1, "founded": 1636, "type": "Private"},
    {"name": "Massachusetts Institute of Technology", "lat": 42.3601, "lon": -71.0942, "country": "USA", "ranking": 2, "founded": 1861, "type": "Private"},
    {"name": "University of Oxford", "lat": 51.7548, "lon": -1.2544, "country": "UK", "ranking": 3, "founded": 1096, "type": "Public"},
    {"name": "University of Cambridge", "lat": 52.2043, "lon": 0.1149, "country": "UK", "ranking": 4, "founded": 1209, "type": "Public"},
    {"name": "Stanford University", "lat": 37.4275, "lon": -122.1697, "country": "USA", "ranking": 5, "founded": 1885, "type": "Private"},
    {"name": "ETH Zurich", "lat": 47.3763, "lon": 8.5480, "country": "Switzerland", "ranking": 6, "founded": 1855, "type": "Public"},
    {"name": "University of Tokyo", "lat": 35.7128, "lon": 139.7621, "country": "Japan", "ranking": 7, "founded": 1877, "type": "Public"},
    {"name": "Peking University", "lat": 39.9869, "lon": 116.3059, "country": "China", "ranking": 8, "founded": 1898, "type": "Public"},
    {"name": "University of Melbourne", "lat": -37.7963, "lon": 144.9614, "country": "Australia", "ranking": 9, "founded": 1853, "type": "Public"},
    {"name": "California Institute of Technology", "lat": 34.1377, "lon": -118.1253, "country": "USA", "ranking": 10, "founded": 1891, "type": "Private"},
    {"name": "Princeton University", "lat": 40.3431, "lon": -74.6551, "country": "USA", "ranking": 11, "founded": 1746, "type": "Private"},
    {"name": "Yale University", "lat": 41.3163, "lon": -72.9223, "country": "USA", "ranking": 12, "founded": 1701, "type": "Private"},
    {"name": "Columbia University", "lat": 40.8075, "lon": -73.9626, "country": "USA", "ranking": 13, "founded": 1754, "type": "Private"},
    {"name": "University of Chicago", "lat": 41.7886, "lon": -87.5987, "country": "USA", "ranking": 14, "founded": 1890, "type": "Private"},
    {"name": "Imperial College London", "lat": 51.4988, "lon": -0.1749, "country": "UK", "ranking": 15, "founded": 1907, "type": "Public"},
    {"name": "University College London", "lat": 51.5246, "lon": -0.1340, "country": "UK", "ranking": 16, "founded": 1826, "type": "Public"},
    {"name": "National University of Singapore", "lat": 1.2966, "lon": 103.7764, "country": "Singapore", "ranking": 17, "founded": 1905, "type": "Public"},
    {"name": "Tsinghua University", "lat": 40.0003, "lon": 116.3267, "country": "China", "ranking": 18, "founded": 1911, "type": "Public"},
    {"name": "University of Toronto", "lat": 43.6629, "lon": -79.3957, "country": "Canada", "ranking": 19, "founded": 1827, "type": "Public"},
    {"name": "University of Edinburgh", "lat": 55.9443, "lon": -3.1893, "country": "UK", "ranking": 20, "founded": 1583, "type": "Public"},
    {"name": "Technical University of Munich", "lat": 48.1497, "lon": 11.5679, "country": "Germany", "ranking": 21, "founded": 1868, "type": "Public"},
    {"name": "Ecole Polytechnique Federale de Lausanne", "lat": 46.5191, "lon": 6.5668, "country": "Switzerland", "ranking": 22, "founded": 1853, "type": "Public"},
    {"name": "University of Hong Kong", "lat": 22.2830, "lon": 114.1372, "country": "Hong Kong", "ranking": 23, "founded": 1911, "type": "Public"},
    {"name": "Johns Hopkins University", "lat": 39.3299, "lon": -76.6205, "country": "USA", "ranking": 24, "founded": 1876, "type": "Private"},
    {"name": "University of Pennsylvania", "lat": 39.9522, "lon": -75.1932, "country": "USA", "ranking": 25, "founded": 1740, "type": "Private"},
    {"name": "Seoul National University", "lat": 37.4602, "lon": 126.9520, "country": "South Korea", "ranking": 26, "founded": 1946, "type": "Public"},
    {"name": "Kyoto University", "lat": 35.0265, "lon": 135.7809, "country": "Japan", "ranking": 27, "founded": 1897, "type": "Public"},
    {"name": "McGill University", "lat": 45.5048, "lon": -73.5772, "country": "Canada", "ranking": 28, "founded": 1821, "type": "Public"},
    {"name": "University of Michigan", "lat": 42.2780, "lon": -83.7382, "country": "USA", "ranking": 29, "founded": 1817, "type": "Public"},
    {"name": "University of Sydney", "lat": -33.8888, "lon": 151.1872, "country": "Australia", "ranking": 30, "founded": 1850, "type": "Public"},
    {"name": "Sorbonne University", "lat": 48.8487, "lon": 2.3471, "country": "France", "ranking": 31, "founded": 1257, "type": "Public"},
    {"name": "Ludwig Maximilian University of Munich", "lat": 48.1508, "lon": 11.5800, "country": "Germany", "ranking": 32, "founded": 1472, "type": "Public"},
    {"name": "University of British Columbia", "lat": 49.2606, "lon": -123.2460, "country": "Canada", "ranking": 33, "founded": 1908, "type": "Public"},
    {"name": "Nanyang Technological University", "lat": 1.3483, "lon": 103.6831, "country": "Singapore", "ranking": 34, "founded": 1991, "type": "Public"},
    {"name": "King's College London", "lat": 51.5115, "lon": -0.1160, "country": "UK", "ranking": 35, "founded": 1829, "type": "Public"},
    {"name": "University of California Berkeley", "lat": 37.8719, "lon": -122.2585, "country": "USA", "ranking": 36, "founded": 1868, "type": "Public"},
    {"name": "Australian National University", "lat": -35.2777, "lon": 149.1185, "country": "Australia", "ranking": 37, "founded": 1946, "type": "Public"},
    {"name": "University of Manchester", "lat": 53.4668, "lon": -2.2339, "country": "UK", "ranking": 38, "founded": 1824, "type": "Public"},
    {"name": "Fudan University", "lat": 31.2984, "lon": 121.5016, "country": "China", "ranking": 39, "founded": 1905, "type": "Public"},
    {"name": "Heidelberg University", "lat": 49.4093, "lon": 8.7061, "country": "Germany", "ranking": 40, "founded": 1386, "type": "Public"},
    {"name": "University of Amsterdam", "lat": 52.3559, "lon": 4.9554, "country": "Netherlands", "ranking": 41, "founded": 1632, "type": "Public"},
    {"name": "Indian Institute of Science", "lat": 13.0219, "lon": 77.5671, "country": "India", "ranking": 42, "founded": 1909, "type": "Public"},
    {"name": "University of Cape Town", "lat": -33.9577, "lon": 18.4612, "country": "South Africa", "ranking": 43, "founded": 1829, "type": "Public"},
    {"name": "Karolinska Institute", "lat": 59.3478, "lon": 18.0256, "country": "Sweden", "ranking": 44, "founded": 1810, "type": "Public"},
    {"name": "University of Buenos Aires", "lat": -34.5997, "lon": -58.3731, "country": "Argentina", "ranking": 45, "founded": 1821, "type": "Public"},
    {"name": "University of Sao Paulo", "lat": -23.5593, "lon": -46.7318, "country": "Brazil", "ranking": 46, "founded": 1934, "type": "Public"},
    {"name": "Moscow State University", "lat": 55.7033, "lon": 37.5303, "country": "Russia", "ranking": 47, "founded": 1755, "type": "Public"},
    {"name": "Hebrew University of Jerusalem", "lat": 31.7942, "lon": 35.2436, "country": "Israel", "ranking": 48, "founded": 1918, "type": "Public"},
    {"name": "University of Copenhagen", "lat": 55.6802, "lon": 12.5724, "country": "Denmark", "ranking": 49, "founded": 1479, "type": "Public"},
    {"name": "University of Zurich", "lat": 47.3744, "lon": 8.5509, "country": "Switzerland", "ranking": 50, "founded": 1833, "type": "Public"},
]

WORLD_LIBRARIES = [
    {"name": "Library of Congress", "lat": 38.8887, "lon": -77.0047, "country": "USA", "founded": 1800, "collection": "170 million items", "type": "National"},
    {"name": "British Library", "lat": 51.5299, "lon": -0.1271, "country": "UK", "founded": 1753, "collection": "170 million items", "type": "National"},
    {"name": "Vatican Apostolic Library", "lat": 41.9029, "lon": 12.4534, "country": "Vatican City", "founded": 1451, "collection": "1.1 million books", "type": "Religious"},
    {"name": "Bibliotheque nationale de France", "lat": 48.8336, "lon": 2.3762, "country": "France", "founded": 1461, "collection": "40 million items", "type": "National"},
    {"name": "Russian State Library", "lat": 55.7520, "lon": 37.6100, "country": "Russia", "founded": 1862, "collection": "47 million items", "type": "National"},
    {"name": "National Diet Library", "lat": 35.6789, "lon": 139.7453, "country": "Japan", "founded": 1948, "collection": "45 million items", "type": "National"},
    {"name": "Library and Archives Canada", "lat": 45.4292, "lon": -75.6888, "country": "Canada", "founded": 1953, "collection": "54 million items", "type": "National"},
    {"name": "National Library of China", "lat": 39.9416, "lon": 116.3191, "country": "China", "founded": 1909, "collection": "41 million items", "type": "National"},
    {"name": "Royal Library of Denmark", "lat": 55.6731, "lon": 12.5838, "country": "Denmark", "founded": 1648, "collection": "35 million items", "type": "National"},
    {"name": "Bodleian Library", "lat": 51.7539, "lon": -1.2547, "country": "UK", "founded": 1602, "collection": "13 million items", "type": "Academic"},
    {"name": "New York Public Library", "lat": 40.7532, "lon": -73.9822, "country": "USA", "founded": 1895, "collection": "55 million items", "type": "Public"},
    {"name": "Yale University Library", "lat": 41.3112, "lon": -72.9287, "country": "USA", "founded": 1701, "collection": "15 million volumes", "type": "Academic"},
    {"name": "Harvard Library", "lat": 42.3738, "lon": -71.1163, "country": "USA", "founded": 1638, "collection": "17 million volumes", "type": "Academic"},
    {"name": "Biblioteca Nacional de Espana", "lat": 40.4236, "lon": -3.6904, "country": "Spain", "founded": 1712, "collection": "30 million items", "type": "National"},
    {"name": "National Library of Australia", "lat": -35.2966, "lon": 149.1297, "country": "Australia", "founded": 1960, "collection": "10 million items", "type": "National"},
    {"name": "Bavarian State Library", "lat": 48.1499, "lon": 11.5789, "country": "Germany", "founded": 1558, "collection": "33 million items", "type": "National"},
    {"name": "Austrian National Library", "lat": 48.2065, "lon": 16.3661, "country": "Austria", "founded": 1368, "collection": "12 million items", "type": "National"},
    {"name": "National Library of Sweden", "lat": 59.3430, "lon": 18.0714, "country": "Sweden", "founded": 1661, "collection": "18 million items", "type": "National"},
    {"name": "Trinity College Library Dublin", "lat": 53.3438, "lon": -6.2546, "country": "Ireland", "founded": 1592, "collection": "7 million items", "type": "Academic"},
    {"name": "National Library of South Africa", "lat": -33.9304, "lon": 18.4180, "country": "South Africa", "founded": 1818, "collection": "4 million items", "type": "National"},
    {"name": "Royal Library of Belgium", "lat": 50.8427, "lon": 4.3555, "country": "Belgium", "founded": 1837, "collection": "6 million items", "type": "National"},
    {"name": "National Library of Brazil", "lat": -22.9105, "lon": -43.1747, "country": "Brazil", "founded": 1810, "collection": "9 million items", "type": "National"},
    {"name": "State Library of Victoria", "lat": -37.8098, "lon": 144.9652, "country": "Australia", "founded": 1854, "collection": "5 million items", "type": "Public"},
    {"name": "National Central Library Taiwan", "lat": 25.0316, "lon": 121.5192, "country": "Taiwan", "founded": 1933, "collection": "4 million items", "type": "National"},
    {"name": "Koninklijke Bibliotheek", "lat": 52.0817, "lon": 4.3280, "country": "Netherlands", "founded": 1798, "collection": "7 million items", "type": "National"},
    {"name": "Swiss National Library", "lat": 46.9419, "lon": 7.4485, "country": "Switzerland", "founded": 1895, "collection": "5 million items", "type": "National"},
    {"name": "National Library of Scotland", "lat": 55.9477, "lon": -3.1928, "country": "UK", "founded": 1925, "collection": "24 million items", "type": "National"},
    {"name": "Helsinki University Library", "lat": 60.1709, "lon": 24.9501, "country": "Finland", "founded": 1640, "collection": "4 million items", "type": "Academic"},
    {"name": "Alexandria Bibliotheca", "lat": 31.2089, "lon": 29.9092, "country": "Egypt", "founded": 2002, "collection": "2 million volumes", "type": "Public"},
    {"name": "National Library of India", "lat": 22.5308, "lon": 88.3323, "country": "India", "founded": 1836, "collection": "3 million items", "type": "National"},
    {"name": "National Library of Poland", "lat": 52.2084, "lon": 21.0580, "country": "Poland", "founded": 1747, "collection": "9 million items", "type": "National"},
    {"name": "National Library of Israel", "lat": 31.7747, "lon": 35.1972, "country": "Israel", "founded": 1892, "collection": "5 million items", "type": "National"},
    {"name": "National Library of Korea", "lat": 37.4932, "lon": 127.0069, "country": "South Korea", "founded": 1945, "collection": "12 million items", "type": "National"},
    {"name": "National Library of New Zealand", "lat": -41.2764, "lon": 174.7767, "country": "New Zealand", "founded": 1965, "collection": "3 million items", "type": "National"},
    {"name": "National Szechenyi Library", "lat": 47.4912, "lon": 19.0391, "country": "Hungary", "founded": 1802, "collection": "8 million items", "type": "National"},
    {"name": "Strahov Monastery Library", "lat": 50.0863, "lon": 14.3887, "country": "Czech Republic", "founded": 1143, "collection": "200,000 volumes", "type": "Religious"},
    {"name": "Admont Abbey Library", "lat": 47.5747, "lon": 14.4612, "country": "Austria", "founded": 1776, "collection": "70,000 volumes", "type": "Religious"},
    {"name": "Joanina Library Coimbra", "lat": 40.2074, "lon": -8.4261, "country": "Portugal", "founded": 1728, "collection": "300,000 volumes", "type": "Academic"},
    {"name": "Anna Amalia Library Weimar", "lat": 50.9779, "lon": 11.3317, "country": "Germany", "founded": 1691, "collection": "1 million items", "type": "Public"},
    {"name": "National Library of the Czech Republic", "lat": 50.0865, "lon": 14.4156, "country": "Czech Republic", "founded": 1777, "collection": "7 million items", "type": "National"},
]

RESEARCH_INSTITUTIONS = [
    {"name": "CERN", "lat": 46.2330, "lon": 6.0557, "country": "Switzerland", "field": "Particle Physics", "founded": 1954, "type": "International"},
    {"name": "NASA Goddard Space Flight Center", "lat": 38.9914, "lon": -76.8524, "country": "USA", "field": "Space Science", "founded": 1959, "type": "Government"},
    {"name": "NASA Jet Propulsion Laboratory", "lat": 34.2013, "lon": -118.1714, "country": "USA", "field": "Space Exploration", "founded": 1936, "type": "Government"},
    {"name": "Max Planck Institute for Physics", "lat": 48.2649, "lon": 11.6712, "country": "Germany", "field": "Physics", "founded": 1917, "type": "Research"},
    {"name": "CSIRO - Clayton", "lat": -37.9090, "lon": 145.1355, "country": "Australia", "field": "Multidisciplinary", "founded": 1926, "type": "Government"},
    {"name": "Fermi National Accelerator Laboratory", "lat": 41.8405, "lon": -88.2526, "country": "USA", "field": "Particle Physics", "founded": 1967, "type": "Government"},
    {"name": "RIKEN", "lat": 35.7677, "lon": 139.6100, "country": "Japan", "field": "Multidisciplinary", "founded": 1917, "type": "Research"},
    {"name": "Pasteur Institute", "lat": 48.8402, "lon": 2.3115, "country": "France", "field": "Biology/Medicine", "founded": 1887, "type": "Research"},
    {"name": "Fraunhofer Society HQ", "lat": 48.1100, "lon": 11.5682, "country": "Germany", "field": "Applied Science", "founded": 1949, "type": "Research"},
    {"name": "Chinese Academy of Sciences", "lat": 39.9775, "lon": 116.3290, "country": "China", "field": "Multidisciplinary", "founded": 1949, "type": "Government"},
    {"name": "INRIA Rocquencourt", "lat": 48.8320, "lon": 2.1040, "country": "France", "field": "Computer Science", "founded": 1967, "type": "Government"},
    {"name": "Brookhaven National Laboratory", "lat": 40.8690, "lon": -72.8868, "country": "USA", "field": "Physics", "founded": 1947, "type": "Government"},
    {"name": "Los Alamos National Laboratory", "lat": 35.8441, "lon": -106.2873, "country": "USA", "field": "Nuclear Science", "founded": 1943, "type": "Government"},
    {"name": "Lawrence Berkeley National Laboratory", "lat": 37.8755, "lon": -122.2477, "country": "USA", "field": "Energy Science", "founded": 1931, "type": "Government"},
    {"name": "Sanger Institute", "lat": 52.0834, "lon": 0.1846, "country": "UK", "field": "Genomics", "founded": 1992, "type": "Research"},
    {"name": "European Space Agency ESTEC", "lat": 52.2193, "lon": 4.4202, "country": "Netherlands", "field": "Space Technology", "founded": 1968, "type": "International"},
    {"name": "ITER", "lat": 43.7079, "lon": 5.7537, "country": "France", "field": "Fusion Energy", "founded": 2007, "type": "International"},
    {"name": "National Institute of Standards and Technology", "lat": 39.1327, "lon": -77.2190, "country": "USA", "field": "Metrology", "founded": 1901, "type": "Government"},
    {"name": "Weizmann Institute of Science", "lat": 31.9050, "lon": 34.8082, "country": "Israel", "field": "Multidisciplinary", "founded": 1934, "type": "Research"},
    {"name": "CNRS Paris", "lat": 48.8468, "lon": 2.2624, "country": "France", "field": "Multidisciplinary", "founded": 1939, "type": "Government"},
    {"name": "Helmholtz Association Berlin", "lat": 52.5200, "lon": 13.3884, "country": "Germany", "field": "Multidisciplinary", "founded": 1995, "type": "Research"},
    {"name": "National Institutes of Health", "lat": 39.0003, "lon": -77.1038, "country": "USA", "field": "Biomedical", "founded": 1887, "type": "Government"},
    {"name": "Oak Ridge National Laboratory", "lat": 35.9319, "lon": -84.3099, "country": "USA", "field": "Energy/Materials", "founded": 1943, "type": "Government"},
    {"name": "Sandia National Laboratories", "lat": 35.0581, "lon": -106.5357, "country": "USA", "field": "Engineering", "founded": 1949, "type": "Government"},
    {"name": "DESY Hamburg", "lat": 53.5754, "lon": 9.8797, "country": "Germany", "field": "Particle Physics", "founded": 1959, "type": "Research"},
    {"name": "Paul Scherrer Institute", "lat": 47.5355, "lon": 8.2273, "country": "Switzerland", "field": "Physics/Materials", "founded": 1988, "type": "Research"},
    {"name": "Institute of Science and Technology Austria", "lat": 48.3100, "lon": 16.2592, "country": "Austria", "field": "Multidisciplinary", "founded": 2009, "type": "Research"},
    {"name": "KAIST", "lat": 36.3721, "lon": 127.3604, "country": "South Korea", "field": "Technology", "founded": 1971, "type": "Research"},
    {"name": "Tata Institute of Fundamental Research", "lat": 19.0057, "lon": 72.8534, "country": "India", "field": "Physics/Math", "founded": 1945, "type": "Research"},
    {"name": "Rutherford Appleton Laboratory", "lat": 51.5735, "lon": -1.3140, "country": "UK", "field": "Physics", "founded": 1957, "type": "Government"},
    {"name": "European Molecular Biology Laboratory", "lat": 49.3836, "lon": 8.7088, "country": "Germany", "field": "Molecular Biology", "founded": 1974, "type": "International"},
    {"name": "Canadian Light Source", "lat": 52.1420, "lon": -106.6263, "country": "Canada", "field": "Synchrotron Science", "founded": 2004, "type": "Research"},
    {"name": "National Research Council of Italy", "lat": 41.9007, "lon": 12.5132, "country": "Italy", "field": "Multidisciplinary", "founded": 1923, "type": "Government"},
    {"name": "Korea Institute of Science and Technology", "lat": 37.6013, "lon": 127.0447, "country": "South Korea", "field": "Applied Science", "founded": 1966, "type": "Government"},
    {"name": "Agency for Science Technology and Research", "lat": 1.2994, "lon": 103.7874, "country": "Singapore", "field": "Multidisciplinary", "founded": 1991, "type": "Government"},
    {"name": "Joint Institute for Nuclear Research", "lat": 56.7472, "lon": 37.1888, "country": "Russia", "field": "Nuclear Physics", "founded": 1956, "type": "International"},
    {"name": "National Centre for Biological Sciences", "lat": 13.0718, "lon": 77.5808, "country": "India", "field": "Biology", "founded": 1992, "type": "Research"},
    {"name": "Instituto Nacional de Pesquisas Espaciais", "lat": -23.2108, "lon": -45.8670, "country": "Brazil", "field": "Space Research", "founded": 1961, "type": "Government"},
    {"name": "SLAC National Accelerator Laboratory", "lat": 37.4192, "lon": -122.2043, "country": "USA", "field": "Particle Physics", "founded": 1962, "type": "Government"},
    {"name": "Argonne National Laboratory", "lat": 41.7137, "lon": -87.9813, "country": "USA", "field": "Energy/Computing", "founded": 1946, "type": "Government"},
]

NOBEL_LAUREATES_BY_COUNTRY = {
    "USA": 403, "UK": 137, "Germany": 114, "France": 73, "Sweden": 33,
    "Japan": 29, "Russia": 27, "Switzerland": 27, "Canada": 27, "Netherlands": 22,
    "Italy": 20, "Austria": 22, "Denmark": 14, "Norway": 13, "Poland": 12,
    "Belgium": 11, "Australia": 12, "Israel": 13, "India": 9, "Hungary": 9,
    "South Africa": 11, "China": 9, "Spain": 8, "Ireland": 7, "Argentina": 5,
    "Egypt": 4, "Finland": 5, "Czech Republic": 4, "Colombia": 2, "Portugal": 2,
    "Mexico": 3, "New Zealand": 3, "Chile": 2, "Turkey": 2, "Brazil": 1,
    "Greece": 2, "Guatemala": 2, "Iceland": 1, "Kenya": 1, "South Korea": 1,
    "Nigeria": 2, "Pakistan": 2, "Peru": 2, "Taiwan": 2, "Vietnam": 1,
    "Myanmar": 1, "Costa Rica": 1, "Ethiopia": 1, "Ghana": 1, "Iran": 1,
    "Liberia": 2, "Luxembourg": 1, "Saint Lucia": 2, "Tanzania": 1, "Yemen": 1,
    "Belarus": 1, "Trinidad and Tobago": 2, "East Timor": 2,
}

WORLD_MUSEUMS = [
    {"name": "Louvre Museum", "lat": 48.8606, "lon": 2.3376, "country": "France", "founded": 1793, "type": "Art", "visitors_m": 7.8},
    {"name": "The Metropolitan Museum of Art", "lat": 40.7794, "lon": -73.9632, "country": "USA", "founded": 1870, "type": "Art", "visitors_m": 5.4},
    {"name": "Hermitage Museum", "lat": 59.9398, "lon": 30.3146, "country": "Russia", "founded": 1764, "type": "Art/History", "visitors_m": 3.1},
    {"name": "British Museum", "lat": 51.5194, "lon": -0.1270, "country": "UK", "founded": 1753, "type": "History", "visitors_m": 5.8},
    {"name": "Smithsonian National Museum of Natural History", "lat": 38.8913, "lon": -77.0260, "country": "USA", "founded": 1910, "type": "Natural History", "visitors_m": 4.2},
    {"name": "Vatican Museums", "lat": 41.9065, "lon": 12.4536, "country": "Vatican City", "founded": 1506, "type": "Art/Religious", "visitors_m": 5.0},
    {"name": "National Gallery London", "lat": 51.5089, "lon": -0.1283, "country": "UK", "founded": 1824, "type": "Art", "visitors_m": 5.3},
    {"name": "Musee d'Orsay", "lat": 48.8600, "lon": 2.3266, "country": "France", "founded": 1986, "type": "Art", "visitors_m": 3.3},
    {"name": "Rijksmuseum", "lat": 52.3600, "lon": 4.8852, "country": "Netherlands", "founded": 1800, "type": "Art/History", "visitors_m": 2.7},
    {"name": "Uffizi Gallery", "lat": 43.7677, "lon": 11.2553, "country": "Italy", "founded": 1581, "type": "Art", "visitors_m": 2.2},
    {"name": "Prado Museum", "lat": 40.4138, "lon": -3.6921, "country": "Spain", "founded": 1819, "type": "Art", "visitors_m": 2.9},
    {"name": "Smithsonian National Air and Space Museum", "lat": 38.8882, "lon": -77.0199, "country": "USA", "founded": 1976, "type": "Science", "visitors_m": 3.2},
    {"name": "Museum of Modern Art (MoMA)", "lat": 40.7614, "lon": -73.9776, "country": "USA", "founded": 1929, "type": "Art", "visitors_m": 1.6},
    {"name": "National Palace Museum Taipei", "lat": 25.1024, "lon": 121.5485, "country": "Taiwan", "founded": 1925, "type": "Art/History", "visitors_m": 3.8},
    {"name": "Tate Modern", "lat": 51.5076, "lon": -0.0994, "country": "UK", "founded": 2000, "type": "Art", "visitors_m": 4.7},
    {"name": "Egyptian Museum Cairo", "lat": 30.0478, "lon": 31.2336, "country": "Egypt", "founded": 1858, "type": "Archaeology", "visitors_m": 1.5},
    {"name": "Deutsches Museum", "lat": 48.1299, "lon": 11.5833, "country": "Germany", "founded": 1903, "type": "Science", "visitors_m": 1.5},
    {"name": "National Museum of Korea", "lat": 37.5241, "lon": 126.9806, "country": "South Korea", "founded": 1945, "type": "History", "visitors_m": 3.4},
    {"name": "Tokyo National Museum", "lat": 35.7189, "lon": 139.7766, "country": "Japan", "founded": 1872, "type": "Art/History", "visitors_m": 1.1},
    {"name": "Guggenheim Museum Bilbao", "lat": 43.2686, "lon": -2.9340, "country": "Spain", "founded": 1997, "type": "Art", "visitors_m": 1.2},
    {"name": "National Gallery of Art Washington", "lat": 38.8913, "lon": -77.0200, "country": "USA", "founded": 1937, "type": "Art", "visitors_m": 3.2},
    {"name": "Acropolis Museum Athens", "lat": 37.9685, "lon": 23.7282, "country": "Greece", "founded": 2009, "type": "Archaeology", "visitors_m": 1.4},
    {"name": "Pergamon Museum Berlin", "lat": 52.5213, "lon": 13.3963, "country": "Germany", "founded": 1930, "type": "Archaeology", "visitors_m": 0.8},
    {"name": "National Museum of Anthropology Mexico", "lat": 19.4260, "lon": -99.1862, "country": "Mexico", "founded": 1964, "type": "Anthropology", "visitors_m": 2.2},
    {"name": "Art Institute of Chicago", "lat": 41.8796, "lon": -87.6237, "country": "USA", "founded": 1879, "type": "Art", "visitors_m": 1.1},
    {"name": "Museo del Prado", "lat": 40.4138, "lon": -3.6921, "country": "Spain", "founded": 1819, "type": "Art", "visitors_m": 2.9},
    {"name": "National Museum of China", "lat": 39.9043, "lon": 116.3958, "country": "China", "founded": 1912, "type": "History", "visitors_m": 7.4},
    {"name": "Natural History Museum London", "lat": 51.4967, "lon": -0.1764, "country": "UK", "founded": 1881, "type": "Natural History", "visitors_m": 4.6},
    {"name": "Museum of Islamic Art Doha", "lat": 25.2955, "lon": 51.5397, "country": "Qatar", "founded": 2008, "type": "Art", "visitors_m": 0.5},
    {"name": "Tretyakov Gallery", "lat": 55.7415, "lon": 37.6208, "country": "Russia", "founded": 1856, "type": "Art", "visitors_m": 2.1},
    {"name": "Victoria and Albert Museum", "lat": 51.4966, "lon": -0.1722, "country": "UK", "founded": 1852, "type": "Art/Design", "visitors_m": 3.9},
    {"name": "Australian Museum", "lat": -33.8742, "lon": 151.2140, "country": "Australia", "founded": 1827, "type": "Natural History", "visitors_m": 0.8},
    {"name": "National Gallery of Victoria", "lat": -37.8226, "lon": 144.9689, "country": "Australia", "founded": 1861, "type": "Art", "visitors_m": 2.3},
    {"name": "Museum of New Zealand Te Papa", "lat": -41.2906, "lon": 174.7819, "country": "New Zealand", "founded": 1998, "type": "Natural History", "visitors_m": 1.5},
    {"name": "Canadian Museum of History", "lat": 45.4302, "lon": -75.7095, "country": "Canada", "founded": 1856, "type": "History", "visitors_m": 1.2},
    {"name": "National Museum of Brazil", "lat": -22.9056, "lon": -43.2262, "country": "Brazil", "founded": 1818, "type": "Natural History", "visitors_m": 0.5},
    {"name": "Indian Museum Kolkata", "lat": 22.5577, "lon": 88.3510, "country": "India", "founded": 1814, "type": "History", "visitors_m": 1.0},
    {"name": "Kunsthistorisches Museum Vienna", "lat": 48.2036, "lon": 16.3613, "country": "Austria", "founded": 1891, "type": "Art/History", "visitors_m": 1.4},
    {"name": "Topkapi Palace Museum", "lat": 41.0115, "lon": 28.9834, "country": "Turkey", "founded": 1924, "type": "History", "visitors_m": 2.0},
    {"name": "Galleria degli Uffizi", "lat": 43.7677, "lon": 11.2553, "country": "Italy", "founded": 1581, "type": "Art", "visitors_m": 2.2},
    {"name": "Science Museum London", "lat": 51.4978, "lon": -0.1745, "country": "UK", "founded": 1857, "type": "Science", "visitors_m": 3.3},
    {"name": "National Museum of Scotland", "lat": 55.9471, "lon": -3.1912, "country": "UK", "founded": 1866, "type": "History", "visitors_m": 2.2},
    {"name": "Zeughaus Berlin (DHM)", "lat": 52.5179, "lon": 13.3965, "country": "Germany", "founded": 1952, "type": "History", "visitors_m": 0.7},
    {"name": "Museum of Fine Arts Boston", "lat": 42.3394, "lon": -71.0940, "country": "USA", "founded": 1870, "type": "Art", "visitors_m": 1.1},
    {"name": "Van Gogh Museum", "lat": 52.3584, "lon": 4.8811, "country": "Netherlands", "founded": 1973, "type": "Art", "visitors_m": 1.6},
    {"name": "Museo Nacional del Prado", "lat": 40.4139, "lon": -3.6922, "country": "Spain", "founded": 1819, "type": "Art", "visitors_m": 2.9},
    {"name": "Getty Center", "lat": 34.0781, "lon": -118.4741, "country": "USA", "founded": 1997, "type": "Art", "visitors_m": 1.8},
    {"name": "Field Museum Chicago", "lat": 41.8663, "lon": -87.6170, "country": "USA", "founded": 1893, "type": "Natural History", "visitors_m": 1.3},
    {"name": "Museo Archeologico Nazionale Napoli", "lat": 40.8535, "lon": 14.2505, "country": "Italy", "founded": 1816, "type": "Archaeology", "visitors_m": 0.6},
    {"name": "Shanghai Museum", "lat": 31.2292, "lon": 121.4735, "country": "China", "founded": 1952, "type": "Art/History", "visitors_m": 2.0},
]

SCIENCE_PARKS = [
    {"name": "Silicon Valley", "lat": 37.3861, "lon": -122.0839, "country": "USA", "focus": "Technology", "founded": 1951, "notable": "Apple, Google, Meta"},
    {"name": "Zhongguancun", "lat": 39.9784, "lon": 116.3114, "country": "China", "focus": "Technology", "founded": 1988, "notable": "Baidu, Lenovo"},
    {"name": "Bangalore IT Hub", "lat": 12.9352, "lon": 77.6245, "country": "India", "focus": "IT Services", "founded": 1990, "notable": "Infosys, Wipro"},
    {"name": "Shenzhen Hi-Tech Park", "lat": 22.5431, "lon": 113.9544, "country": "China", "focus": "Electronics", "founded": 1996, "notable": "Huawei, Tencent, DJI"},
    {"name": "Cambridge Science Park", "lat": 52.2263, "lon": 0.1521, "country": "UK", "focus": "Biotech/Tech", "founded": 1970, "notable": "ARM Holdings"},
    {"name": "Sophia Antipolis", "lat": 43.6161, "lon": 7.0556, "country": "France", "focus": "Tech/Telecom", "founded": 1969, "notable": "SAP, Amadeus"},
    {"name": "Research Triangle Park", "lat": 35.8996, "lon": -78.8638, "country": "USA", "focus": "Biotech/Pharma", "founded": 1959, "notable": "IBM, Cisco"},
    {"name": "Tsukuba Science City", "lat": 36.0835, "lon": 140.0766, "country": "Japan", "focus": "Research", "founded": 1963, "notable": "AIST, KEK"},
    {"name": "Skolkovo Innovation Center", "lat": 55.6959, "lon": 37.3597, "country": "Russia", "focus": "Technology", "founded": 2010, "notable": "Skoltech"},
    {"name": "Hsinchu Science Park", "lat": 24.7878, "lon": 121.0017, "country": "Taiwan", "focus": "Semiconductors", "founded": 1980, "notable": "TSMC, MediaTek"},
    {"name": "Daedeok Innopolis", "lat": 36.3825, "lon": 127.3678, "country": "South Korea", "focus": "Research", "founded": 1973, "notable": "KAIST, ETRI"},
    {"name": "Kista Science City", "lat": 59.4039, "lon": 17.9484, "country": "Sweden", "focus": "ICT", "founded": 1976, "notable": "Ericsson"},
    {"name": "Oulu Innovation Hub", "lat": 65.0121, "lon": 25.4651, "country": "Finland", "focus": "ICT/Wireless", "founded": 1982, "notable": "Nokia R&D"},
    {"name": "Cyberjaya", "lat": 2.9254, "lon": 101.6579, "country": "Malaysia", "focus": "ICT", "founded": 1997, "notable": "MSC Malaysia"},
    {"name": "One-North Singapore", "lat": 1.2995, "lon": 103.7870, "country": "Singapore", "focus": "Biomedical/ICT", "founded": 2003, "notable": "Biopolis, Fusionopolis"},
    {"name": "Biopolis Singapore", "lat": 1.3045, "lon": 103.7897, "country": "Singapore", "focus": "Biomedical", "founded": 2003, "notable": "A*STAR labs"},
    {"name": "Adlershof Science City Berlin", "lat": 52.4323, "lon": 13.5309, "country": "Germany", "focus": "Photonics/IT", "founded": 1991, "notable": "BESSY, DLR"},
    {"name": "Grenoble Innovation Park", "lat": 45.1972, "lon": 5.7575, "country": "France", "focus": "Nanotech", "founded": 1971, "notable": "CEA, ESRF"},
    {"name": "Eindhoven Brainport", "lat": 51.4416, "lon": 5.4697, "country": "Netherlands", "focus": "High-Tech", "founded": 1998, "notable": "Philips, ASML"},
    {"name": "Station F Paris", "lat": 48.8344, "lon": 2.3700, "country": "France", "focus": "Startups", "founded": 2017, "notable": "Largest startup campus"},
    {"name": "Toronto MaRS Discovery District", "lat": 43.6596, "lon": -79.3882, "country": "Canada", "focus": "Health/Cleantech", "founded": 2005, "notable": "MaRS Innovation"},
    {"name": "Waterloo Region", "lat": 43.4643, "lon": -80.5204, "country": "Canada", "focus": "Technology", "founded": 2010, "notable": "Communitech"},
    {"name": "Medicon Valley", "lat": 55.6631, "lon": 12.5839, "country": "Denmark/Sweden", "focus": "Life Sciences", "founded": 1997, "notable": "Novo Nordisk"},
    {"name": "Cyberport Hong Kong", "lat": 22.2610, "lon": 114.1290, "country": "Hong Kong", "focus": "Tech/Fintech", "founded": 2004, "notable": "Digital hub"},
    {"name": "Melbourne Innovation District", "lat": -37.8027, "lon": 144.9557, "country": "Australia", "focus": "Biotech/Health", "founded": 2016, "notable": "Bio21, WEHI"},
    {"name": "Cape Town Silicon Cape", "lat": -33.9249, "lon": 18.4241, "country": "South Africa", "focus": "Tech Startups", "founded": 2009, "notable": "Naspers"},
    {"name": "Tel Aviv Innovation District", "lat": 32.0633, "lon": 34.7708, "country": "Israel", "focus": "Tech/Cyber", "founded": 2000, "notable": "Startup Nation hub"},
    {"name": "Nairobi iHub", "lat": -1.2890, "lon": 36.7834, "country": "Kenya", "focus": "Tech Startups", "founded": 2010, "notable": "Silicon Savannah"},
    {"name": "Route 128 Boston", "lat": 42.3736, "lon": -71.2358, "country": "USA", "focus": "Biotech/Defense", "founded": 1955, "notable": "Raytheon, Moderna"},
    {"name": "Jurong Innovation District", "lat": 1.3425, "lon": 103.6887, "country": "Singapore", "focus": "Advanced Manufacturing", "founded": 2017, "notable": "NTU partnership"},
]

ASTRONOMICAL_OBSERVATORIES = [
    {"name": "Very Large Telescope (VLT)", "lat": -24.6275, "lon": -70.4044, "country": "Chile", "operator": "ESO", "type": "Optical/IR", "altitude_m": 2635},
    {"name": "Keck Observatory", "lat": 19.8264, "lon": -155.4744, "country": "USA", "operator": "Caltech/UC", "type": "Optical/IR", "altitude_m": 4145},
    {"name": "Hubble Space Telescope Control", "lat": 38.9984, "lon": -76.8523, "country": "USA", "operator": "NASA/ESA", "type": "Space Optical", "altitude_m": 0},
    {"name": "Arecibo Observatory (legacy)", "lat": 18.3464, "lon": -66.7528, "country": "Puerto Rico", "operator": "NSF (closed 2020)", "type": "Radio", "altitude_m": 498},
    {"name": "ALMA", "lat": -23.0193, "lon": -67.7532, "country": "Chile", "operator": "ESO/NAOJ/NRAO", "type": "Radio/Submm", "altitude_m": 5058},
    {"name": "Gemini North", "lat": 19.8238, "lon": -155.4691, "country": "USA", "operator": "NSF/NOIRLab", "type": "Optical/IR", "altitude_m": 4213},
    {"name": "Gemini South", "lat": -30.2407, "lon": -70.7366, "country": "Chile", "operator": "NSF/NOIRLab", "type": "Optical/IR", "altitude_m": 2722},
    {"name": "Subaru Telescope", "lat": 19.8256, "lon": -155.4761, "country": "USA (Hawaii)", "operator": "NAOJ", "type": "Optical/IR", "altitude_m": 4163},
    {"name": "Jodrell Bank", "lat": 53.2367, "lon": -2.3085, "country": "UK", "operator": "University of Manchester", "type": "Radio", "altitude_m": 77},
    {"name": "Parkes Observatory", "lat": -32.9983, "lon": 148.2636, "country": "Australia", "operator": "CSIRO", "type": "Radio", "altitude_m": 414},
    {"name": "Green Bank Observatory", "lat": 38.4330, "lon": -79.8398, "country": "USA", "operator": "NSF", "type": "Radio", "altitude_m": 807},
    {"name": "Very Large Array (VLA)", "lat": 34.0784, "lon": -107.6184, "country": "USA", "operator": "NRAO", "type": "Radio", "altitude_m": 2124},
    {"name": "Palomar Observatory", "lat": 33.3564, "lon": -116.8650, "country": "USA", "operator": "Caltech", "type": "Optical", "altitude_m": 1706},
    {"name": "Gran Telescopio Canarias", "lat": 28.7567, "lon": -17.8920, "country": "Spain", "operator": "IAC", "type": "Optical/IR", "altitude_m": 2267},
    {"name": "La Silla Observatory", "lat": -29.2563, "lon": -70.7380, "country": "Chile", "operator": "ESO", "type": "Optical", "altitude_m": 2400},
    {"name": "South African Astronomical Observatory", "lat": -32.3779, "lon": 20.8109, "country": "South Africa", "operator": "NRF", "type": "Optical", "altitude_m": 1798},
    {"name": "Mount Wilson Observatory", "lat": 34.2258, "lon": -118.0564, "country": "USA", "operator": "Mount Wilson Institute", "type": "Optical", "altitude_m": 1742},
    {"name": "Royal Greenwich Observatory (historic)", "lat": 51.4769, "lon": -0.0005, "country": "UK", "operator": "Historic", "type": "Optical (historic)", "altitude_m": 47},
    {"name": "European Extremely Large Telescope (ELT)", "lat": -24.5893, "lon": -70.1916, "country": "Chile", "operator": "ESO", "type": "Optical/IR (under construction)", "altitude_m": 3046},
    {"name": "FAST (Five-hundred-meter)", "lat": 25.6529, "lon": 106.8566, "country": "China", "operator": "NAOC", "type": "Radio", "altitude_m": 1000},
    {"name": "Cerro Tololo Inter-American Observatory", "lat": -30.1691, "lon": -70.8066, "country": "Chile", "operator": "NOIRLab", "type": "Optical", "altitude_m": 2200},
    {"name": "Mauna Kea Observatories", "lat": 19.8207, "lon": -155.4681, "country": "USA", "operator": "Multiple", "type": "Multiple", "altitude_m": 4205},
    {"name": "Lick Observatory", "lat": 37.3414, "lon": -121.6429, "country": "USA", "operator": "UC Santa Cruz", "type": "Optical", "altitude_m": 1283},
    {"name": "Apache Point Observatory", "lat": 32.7803, "lon": -105.8203, "country": "USA", "operator": "ARC", "type": "Optical", "altitude_m": 2788},
    {"name": "Siding Spring Observatory", "lat": -31.2733, "lon": 149.0667, "country": "Australia", "operator": "ANU", "type": "Optical", "altitude_m": 1165},
    {"name": "Roque de los Muchachos", "lat": 28.7606, "lon": -17.8816, "country": "Spain", "operator": "IAC", "type": "Multiple", "altitude_m": 2396},
    {"name": "Observatorio del Teide", "lat": 28.3007, "lon": -16.5107, "country": "Spain", "operator": "IAC", "type": "Solar", "altitude_m": 2390},
    {"name": "Vainu Bappu Observatory", "lat": 12.5766, "lon": 78.8286, "country": "India", "operator": "IIA", "type": "Optical", "altitude_m": 725},
    {"name": "Pic du Midi Observatory", "lat": 42.9369, "lon": 0.1424, "country": "France", "operator": "CNRS", "type": "Optical", "altitude_m": 2877},
    {"name": "Nancay Radio Observatory", "lat": 47.3803, "lon": 2.1965, "country": "France", "operator": "Paris Observatory", "type": "Radio", "altitude_m": 150},
]

ANCIENT_UNIVERSITIES = [
    {"name": "University of Bologna", "lat": 44.4949, "lon": 11.3426, "country": "Italy", "founded": 1088, "claim": "Oldest in continuous operation (Western world)", "notable": "First degree-granting university"},
    {"name": "University of Oxford", "lat": 51.7548, "lon": -1.2544, "country": "UK", "founded": 1096, "claim": "Oldest English-speaking university", "notable": "26 British Prime Ministers"},
    {"name": "University of Salamanca", "lat": 40.9607, "lon": -5.6680, "country": "Spain", "founded": 1134, "claim": "Oldest Spanish university", "notable": "School of Salamanca economics"},
    {"name": "University of Paris (Sorbonne)", "lat": 48.8487, "lon": 2.3471, "country": "France", "founded": 1150, "claim": "Medieval theological center", "notable": "Thomas Aquinas taught here"},
    {"name": "University of Cambridge", "lat": 52.2043, "lon": 0.1149, "country": "UK", "founded": 1209, "claim": "Second-oldest English university", "notable": "Newton, Darwin, Hawking"},
    {"name": "University of Padua", "lat": 45.4064, "lon": 11.8768, "country": "Italy", "founded": 1222, "claim": "Galileo taught here", "notable": "First anatomical theatre"},
    {"name": "University of Naples Federico II", "lat": 40.8451, "lon": 14.2519, "country": "Italy", "founded": 1224, "claim": "Oldest state university", "notable": "Founded by Frederick II"},
    {"name": "University of Toulouse", "lat": 43.6047, "lon": 1.4442, "country": "France", "founded": 1229, "claim": "Founded by Papal decree", "notable": "Third-oldest in France"},
    {"name": "University of Siena", "lat": 43.3188, "lon": 11.3307, "country": "Italy", "founded": 1240, "claim": "Ancient Tuscan university", "notable": "Known for law and medicine"},
    {"name": "University of Coimbra", "lat": 40.2074, "lon": -8.4261, "country": "Portugal", "founded": 1290, "claim": "Oldest Portuguese university", "notable": "UNESCO World Heritage Site"},
    {"name": "University of Valladolid", "lat": 41.6523, "lon": -4.7245, "country": "Spain", "founded": 1241, "claim": "One of the oldest in Spain", "notable": "Columbus studied geography here"},
    {"name": "University of Macerata", "lat": 43.2994, "lon": 13.4527, "country": "Italy", "founded": 1290, "claim": "Among oldest in Italy", "notable": "Humanities focus"},
    {"name": "Al-Azhar University", "lat": 30.0459, "lon": 31.2627, "country": "Egypt", "founded": 970, "claim": "One of oldest in the world", "notable": "Center of Islamic scholarship"},
    {"name": "University of al-Qarawiyyin", "lat": 34.0640, "lon": -4.9735, "country": "Morocco", "founded": 859, "claim": "Oldest existing university (UNESCO/Guinness)", "notable": "Founded by Fatima al-Fihri"},
    {"name": "Charles University Prague", "lat": 50.0862, "lon": 14.4201, "country": "Czech Republic", "founded": 1348, "claim": "Oldest in Central Europe", "notable": "Founded by Charles IV"},
    {"name": "Jagiellonian University", "lat": 50.0614, "lon": 19.9333, "country": "Poland", "founded": 1364, "claim": "Second-oldest in Central Europe", "notable": "Copernicus studied here"},
    {"name": "University of Vienna", "lat": 48.2130, "lon": 16.3599, "country": "Austria", "founded": 1365, "claim": "Oldest German-speaking university", "notable": "15 Nobel laureates"},
    {"name": "University of Heidelberg", "lat": 49.4093, "lon": 8.7061, "country": "Germany", "founded": 1386, "claim": "Oldest in Germany", "notable": "Birthplace of German Romanticism"},
    {"name": "University of Erfurt", "lat": 50.9787, "lon": 11.0328, "country": "Germany", "founded": 1389, "claim": "Martin Luther studied here", "notable": "Re-founded 1994"},
    {"name": "University of St Andrews", "lat": 56.3398, "lon": -2.7967, "country": "UK", "founded": 1413, "claim": "Oldest in Scotland", "notable": "Prince William attended"},
    {"name": "University of Glasgow", "lat": 55.8721, "lon": -4.2882, "country": "UK", "founded": 1451, "claim": "Fourth-oldest English speaking", "notable": "Adam Smith, Lord Kelvin"},
    {"name": "University of Barcelona", "lat": 41.3862, "lon": 2.1649, "country": "Spain", "founded": 1450, "claim": "Premier Catalan university", "notable": "Oldest in Catalonia"},
    {"name": "Uppsala University", "lat": 59.8586, "lon": 17.6389, "country": "Sweden", "founded": 1477, "claim": "Oldest in Scandinavia", "notable": "Linnaeus, Celsius"},
    {"name": "University of Copenhagen", "lat": 55.6802, "lon": 12.5724, "country": "Denmark", "founded": 1479, "claim": "Oldest in Denmark", "notable": "Niels Bohr"},
    {"name": "University of Aberdeen", "lat": 57.1644, "lon": -2.0999, "country": "UK", "founded": 1495, "claim": "Fifth-oldest English speaking", "notable": "Five Nobel laureates"},
]

# ---------------------------------------------------------------------------
# Color palettes
# ---------------------------------------------------------------------------

MODE_COLORS = {
    "World Universities": "#06b6d4",
    "Libraries of the World": "#8b5cf6",
    "Research Institutions": "#10b981",
    "Nobel Prize Origins": "#f59e0b",
    "UNESCO World Heritage": "#ef4444",
    "Museums & Galleries": "#ec4899",
    "Science Parks & Innovation Hubs": "#3b82f6",
    "Astronomical Observatories": "#a855f7",
    "Botanical Gardens": "#14b8a6",
    "Ancient Universities": "#f97316",
}

COUNTRY_COORDS = {
    "USA": [39.8283, -98.5795], "UK": [55.3781, -3.4360],
    "Germany": [51.1657, 10.4515], "France": [46.2276, 2.2137],
    "Japan": [36.2048, 138.2529], "China": [35.8617, 104.1954],
    "Switzerland": [46.8182, 8.2275], "Australia": [-25.2744, 133.7751],
    "Canada": [56.1304, -106.3468], "Singapore": [1.3521, 103.8198],
    "Sweden": [60.1282, 18.6435], "Russia": [61.5240, 105.3188],
    "India": [20.5937, 78.9629], "Italy": [41.8719, 12.5674],
    "Netherlands": [52.1326, 5.2913], "Israel": [31.0461, 34.8516],
    "South Korea": [35.9078, 127.7669], "Brazil": [-14.2350, -51.9253],
    "Spain": [40.4637, -3.7492], "Austria": [47.5162, 14.5501],
    "Denmark": [56.2639, 9.5018], "Hong Kong": [22.3193, 114.1694],
    "South Africa": [-30.5595, 22.9375], "Taiwan": [23.6978, 120.9605],
    "Argentina": [-38.4161, -63.6167], "Ireland": [53.1424, -7.6921],
    "Poland": [51.9194, 19.1451], "Finland": [61.9241, 25.7482],
    "Norway": [60.4720, 8.4689], "Egypt": [26.8206, 30.8025],
    "Hungary": [47.1625, 19.5033], "Czech Republic": [49.8175, 15.4730],
    "Belgium": [50.5039, 4.4699], "Portugal": [39.3999, -8.2245],
    "Mexico": [23.6345, -102.5528], "New Zealand": [-40.9006, 174.8860],
    "Turkey": [38.9637, 35.2433], "Greece": [39.0742, 21.8243],
    "Colombia": [4.5709, -74.2973], "Chile": [-35.6751, -71.5430],
    "Qatar": [25.3548, 51.1839], "Malaysia": [4.2105, 101.9758],
    "Kenya": [-0.0236, 37.9062], "Morocco": [31.7917, -7.0926],
    "Vatican City": [41.9029, 12.4534],
}

# ---------------------------------------------------------------------------
# API fetch functions
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def fetch_unesco_sites(lat: float, lon: float, radius_km: float) -> list:
    """Fetch UNESCO World Heritage sites via Overpass API."""
    r_deg = radius_km / 111.0
    south = lat - r_deg
    north = lat + r_deg
    west = lon - r_deg
    east = lon + r_deg
    query = f"""
    [out:json][timeout:90];
    (
      node["heritage"="world_heritage"]({south},{west},{north},{east});
      way["heritage"="world_heritage"]({south},{west},{north},{east});
      relation["heritage"="world_heritage"]({south},{west},{north},{east});
      node["heritage:operator"="whc"]({south},{west},{north},{east});
      way["heritage:operator"="whc"]({south},{west},{north},{east});
      relation["heritage:operator"="whc"]({south},{west},{north},{east});
    );
    out center 500;
    """
    data = query_overpass(query)
    if data is None or "_error" in data:
        return []
    sites = []
    for el in data.get("elements", []):
        lat_v = el.get("lat") or el.get("center", {}).get("lat")
        lon_v = el.get("lon") or el.get("center", {}).get("lon")
        tags = el.get("tags", {})
        name = tags.get("name", tags.get("name:en", "Unknown Site"))
        if lat_v and lon_v:
            sites.append({
                "name": name,
                "lat": lat_v,
                "lon": lon_v,
                "heritage_ref": tags.get("ref:whc", "N/A"),
                "description": tags.get("description", tags.get("heritage:description", "")),
                "wikidata": tags.get("wikidata", ""),
                "wikipedia": tags.get("wikipedia", ""),
            })
    return sites


@st.cache_data(ttl=3600)
def fetch_botanical_gardens(lat: float, lon: float, radius_km: float) -> list:
    """Fetch botanical gardens via Overpass API."""
    r_deg = radius_km / 111.0
    south = lat - r_deg
    north = lat + r_deg
    west = lon - r_deg
    east = lon + r_deg
    query = f"""
    [out:json][timeout:90];
    (
      node["leisure"="garden"]["garden:type"="botanical"]({south},{west},{north},{east});
      way["leisure"="garden"]["garden:type"="botanical"]({south},{west},{north},{east});
      relation["leisure"="garden"]["garden:type"="botanical"]({south},{west},{north},{east});
      node["leisure"="garden"]["name"~"[Bb]otanic"]({south},{west},{north},{east});
      way["leisure"="garden"]["name"~"[Bb]otanic"]({south},{west},{north},{east});
      relation["leisure"="garden"]["name"~"[Bb]otanic"]({south},{west},{north},{east});
    );
    out center 500;
    """
    data = query_overpass(query)
    if data is None or "_error" in data:
        return []
    gardens = []
    seen = set()
    for el in data.get("elements", []):
        lat_v = el.get("lat") or el.get("center", {}).get("lat")
        lon_v = el.get("lon") or el.get("center", {}).get("lon")
        tags = el.get("tags", {})
        name = tags.get("name", tags.get("name:en", "Unknown Garden"))
        if lat_v and lon_v and name not in seen:
            seen.add(name)
            gardens.append({
                "name": name,
                "lat": lat_v,
                "lon": lon_v,
                "wikidata": tags.get("wikidata", ""),
                "wikipedia": tags.get("wikipedia", ""),
                "website": tags.get("website", tags.get("contact:website", "")),
                "operator": tags.get("operator", ""),
            })
    return gardens


# ---------------------------------------------------------------------------
# Map builders
# ---------------------------------------------------------------------------

def _create_base_map(center: list = None, zoom: int = 2) -> folium.Map:
    """Create a dark-themed folium map."""
    if center is None:
        center = [20, 0]
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    return m


def _add_circle_marker(fg, lat, lon, name, color, popup_html, radius=7):
    """Add a circle marker to a feature group."""
    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=folium.Popup(popup_html, max_width=350),
        tooltip=name,
    ).add_to(fg)


def build_universities_map(data: list) -> folium.Map:
    """Build map of world universities."""
    m = _create_base_map()
    fg = folium.FeatureGroup(name="Universities")
    for u in data:
        safe_name = html.escape(u["name"])
        safe_country = html.escape(u["country"])
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;">
            <b style="color:#06b6d4;font-size:14px;">{safe_name}</b><br>
            <b>Country:</b> {safe_country}<br>
            <b>Ranking:</b> #{u['ranking']}<br>
            <b>Founded:</b> {u['founded']}<br>
            <b>Type:</b> {html.escape(u['type'])}
        </div>
        """
        rank = u["ranking"]
        radius = max(4, 12 - (rank // 5))
        _add_circle_marker(fg, u["lat"], u["lon"], safe_name, "#06b6d4", popup_html, radius)
    fg.add_to(m)
    return m


def build_libraries_map(data: list) -> folium.Map:
    """Build map of world libraries."""
    m = _create_base_map()
    fg = folium.FeatureGroup(name="Libraries")
    for lib in data:
        safe_name = html.escape(lib["name"])
        safe_country = html.escape(lib["country"])
        safe_collection = html.escape(lib["collection"])
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;">
            <b style="color:#8b5cf6;font-size:14px;">{safe_name}</b><br>
            <b>Country:</b> {safe_country}<br>
            <b>Founded:</b> {lib['founded']}<br>
            <b>Collection:</b> {safe_collection}<br>
            <b>Type:</b> {html.escape(lib['type'])}
        </div>
        """
        _add_circle_marker(fg, lib["lat"], lib["lon"], safe_name, "#8b5cf6", popup_html, 7)
    fg.add_to(m)
    return m


def build_research_map(data: list) -> folium.Map:
    """Build map of research institutions."""
    m = _create_base_map()
    fg = folium.FeatureGroup(name="Research Institutions")
    field_colors = {
        "Particle Physics": "#ef4444",
        "Space Science": "#3b82f6",
        "Space Exploration": "#3b82f6",
        "Physics": "#a855f7",
        "Multidisciplinary": "#06b6d4",
        "Biology/Medicine": "#10b981",
        "Applied Science": "#f59e0b",
        "Computer Science": "#ec4899",
        "Nuclear Science": "#ef4444",
        "Energy Science": "#f97316",
        "Genomics": "#14b8a6",
        "Space Technology": "#3b82f6",
        "Fusion Energy": "#f59e0b",
        "Metrology": "#8b5cf6",
        "Molecular Biology": "#10b981",
        "Synchrotron Science": "#a855f7",
        "Biomedical": "#10b981",
        "Energy/Materials": "#f97316",
        "Engineering": "#f59e0b",
        "Technology": "#06b6d4",
        "Nuclear Physics": "#ef4444",
        "Biology": "#10b981",
        "Space Research": "#3b82f6",
        "Physics/Materials": "#a855f7",
        "Physics/Math": "#a855f7",
        "Energy/Computing": "#f97316",
    }
    for inst in data:
        safe_name = html.escape(inst["name"])
        safe_country = html.escape(inst["country"])
        safe_field = html.escape(inst["field"])
        color = field_colors.get(inst["field"], "#06b6d4")
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;">
            <b style="color:{color};font-size:14px;">{safe_name}</b><br>
            <b>Country:</b> {safe_country}<br>
            <b>Field:</b> {safe_field}<br>
            <b>Founded:</b> {inst['founded']}<br>
            <b>Type:</b> {html.escape(inst['type'])}
        </div>
        """
        _add_circle_marker(fg, inst["lat"], inst["lon"], safe_name, color, popup_html, 7)
    fg.add_to(m)
    return m


def build_nobel_map(data: dict) -> folium.Map:
    """Build choropleth-style map of Nobel laureates by country."""
    m = _create_base_map(zoom=2)
    fg = folium.FeatureGroup(name="Nobel Laureates")
    max_count = max(data.values()) if data else 1
    for country, count in data.items():
        coords = COUNTRY_COORDS.get(country)
        if coords is None:
            continue
        safe_country = html.escape(country)
        intensity = min(1.0, count / max_count)
        radius = max(5, int(8 + 30 * intensity))
        r = int(6 + 239 * intensity)
        g = int(182 - 120 * intensity)
        b = int(212 - 180 * intensity)
        color = f"#{r:02x}{g:02x}{b:02x}"
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:150px;">
            <b style="color:#f59e0b;font-size:14px;">{safe_country}</b><br>
            <b>Nobel Laureates:</b> {count}
        </div>
        """
        folium.CircleMarker(
            location=coords,
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.6,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{safe_country}: {count} laureates",
        ).add_to(fg)
    fg.add_to(m)
    return m


def build_unesco_map(sites: list) -> folium.Map:
    """Build map of UNESCO World Heritage sites."""
    if sites:
        avg_lat = sum(s["lat"] for s in sites) / len(sites)
        avg_lon = sum(s["lon"] for s in sites) / len(sites)
        m = _create_base_map(center=[avg_lat, avg_lon], zoom=5)
    else:
        m = _create_base_map()
    cluster = MarkerCluster(name="UNESCO Sites")
    for site in sites:
        safe_name = html.escape(site["name"])
        safe_desc = html.escape(site.get("description", ""))
        ref = html.escape(site.get("heritage_ref", "N/A"))
        wiki_link = ""
        if site.get("wikipedia"):
            parts = site["wikipedia"].split(":", 1)
            if len(parts) == 2:
                wiki_url = f"https://{parts[0]}.wikipedia.org/wiki/{parts[1].replace(' ', '_')}"
                wiki_link = f'<br><a href="{html.escape(wiki_url)}" target="_blank">Wikipedia</a>'
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;">
            <b style="color:#ef4444;font-size:14px;">{safe_name}</b><br>
            <b>WHC Ref:</b> {ref}<br>
            {f'<b>Description:</b> {safe_desc}<br>' if safe_desc else ''}
            {wiki_link}
        </div>
        """
        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=7,
            color="#ef4444",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=safe_name,
        ).add_to(cluster)
    cluster.add_to(m)
    return m


def build_museums_map(data: list) -> folium.Map:
    """Build map of world museums."""
    m = _create_base_map()
    fg = folium.FeatureGroup(name="Museums")
    type_colors = {
        "Art": "#ec4899",
        "History": "#f59e0b",
        "Natural History": "#10b981",
        "Science": "#06b6d4",
        "Archaeology": "#f97316",
        "Art/History": "#a855f7",
        "Art/Religious": "#8b5cf6",
        "Art/Design": "#ec4899",
        "Anthropology": "#14b8a6",
    }
    for mus in data:
        safe_name = html.escape(mus["name"])
        safe_country = html.escape(mus["country"])
        color = type_colors.get(mus["type"], "#ec4899")
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;">
            <b style="color:{color};font-size:14px;">{safe_name}</b><br>
            <b>Country:</b> {safe_country}<br>
            <b>Type:</b> {html.escape(mus['type'])}<br>
            <b>Founded:</b> {mus['founded']}<br>
            <b>Annual Visitors:</b> ~{mus['visitors_m']}M
        </div>
        """
        radius = max(4, int(4 + mus["visitors_m"] * 1.2))
        _add_circle_marker(fg, mus["lat"], mus["lon"], safe_name, color, popup_html, radius)
    fg.add_to(m)
    return m


def build_science_parks_map(data: list) -> folium.Map:
    """Build map of science parks and innovation hubs."""
    m = _create_base_map()
    fg = folium.FeatureGroup(name="Science Parks")
    focus_colors = {
        "Technology": "#06b6d4",
        "IT Services": "#3b82f6",
        "Electronics": "#10b981",
        "Biotech/Tech": "#14b8a6",
        "Tech/Telecom": "#8b5cf6",
        "Biotech/Pharma": "#10b981",
        "Research": "#a855f7",
        "Semiconductors": "#f59e0b",
        "ICT": "#3b82f6",
        "ICT/Wireless": "#3b82f6",
        "Biomedical/ICT": "#ec4899",
        "Biomedical": "#ec4899",
        "Photonics/IT": "#a855f7",
        "Nanotech": "#f97316",
        "High-Tech": "#06b6d4",
        "Startups": "#ef4444",
        "Health/Cleantech": "#10b981",
        "Life Sciences": "#14b8a6",
        "Tech/Fintech": "#f59e0b",
        "Biotech/Health": "#10b981",
        "Tech Startups": "#ef4444",
        "Tech/Cyber": "#06b6d4",
        "Biotech/Defense": "#8b5cf6",
        "Advanced Manufacturing": "#f97316",
    }
    for park in data:
        safe_name = html.escape(park["name"])
        safe_country = html.escape(park["country"])
        safe_notable = html.escape(park["notable"])
        color = focus_colors.get(park["focus"], "#3b82f6")
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;">
            <b style="color:{color};font-size:14px;">{safe_name}</b><br>
            <b>Country:</b> {safe_country}<br>
            <b>Focus:</b> {html.escape(park['focus'])}<br>
            <b>Founded:</b> {park['founded']}<br>
            <b>Notable:</b> {safe_notable}
        </div>
        """
        _add_circle_marker(fg, park["lat"], park["lon"], safe_name, color, popup_html, 8)
    fg.add_to(m)
    return m


def build_observatories_map(data: list) -> folium.Map:
    """Build map of astronomical observatories."""
    m = _create_base_map()
    fg = folium.FeatureGroup(name="Observatories")
    for obs in data:
        safe_name = html.escape(obs["name"])
        safe_country = html.escape(obs["country"])
        safe_operator = html.escape(obs["operator"])
        is_radio = "Radio" in obs["type"]
        color = "#f59e0b" if is_radio else "#a855f7"
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;">
            <b style="color:{color};font-size:14px;">{safe_name}</b><br>
            <b>Country:</b> {safe_country}<br>
            <b>Operator:</b> {safe_operator}<br>
            <b>Type:</b> {html.escape(obs['type'])}<br>
            <b>Altitude:</b> {obs['altitude_m']:,}m
        </div>
        """
        radius = max(5, min(10, obs["altitude_m"] // 500 + 3))
        _add_circle_marker(fg, obs["lat"], obs["lon"], safe_name, color, popup_html, radius)
    fg.add_to(m)
    return m


def build_botanical_gardens_map(gardens: list) -> folium.Map:
    """Build map of botanical gardens."""
    if gardens:
        avg_lat = sum(g["lat"] for g in gardens) / len(gardens)
        avg_lon = sum(g["lon"] for g in gardens) / len(gardens)
        m = _create_base_map(center=[avg_lat, avg_lon], zoom=5)
    else:
        m = _create_base_map()
    cluster = MarkerCluster(name="Botanical Gardens")
    for g in gardens:
        safe_name = html.escape(g["name"])
        safe_operator = html.escape(g.get("operator", ""))
        website = g.get("website", "")
        website_link = ""
        if website:
            safe_url = html.escape(website)
            website_link = f'<br><a href="{safe_url}" target="_blank">Website</a>'
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:200px;">
            <b style="color:#14b8a6;font-size:14px;">{safe_name}</b><br>
            {f'<b>Operator:</b> {safe_operator}<br>' if safe_operator else ''}
            {website_link}
        </div>
        """
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=7,
            color="#14b8a6",
            fill=True,
            fill_color="#14b8a6",
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=safe_name,
        ).add_to(cluster)
    cluster.add_to(m)
    return m


def build_ancient_universities_map(data: list) -> folium.Map:
    """Build map of ancient universities."""
    m = _create_base_map(center=[42, 10], zoom=4)
    fg = folium.FeatureGroup(name="Ancient Universities")
    for u in data:
        safe_name = html.escape(u["name"])
        safe_country = html.escape(u["country"])
        safe_claim = html.escape(u["claim"])
        safe_notable = html.escape(u["notable"])
        age = 2026 - u["founded"]
        if u["founded"] < 1000:
            color = "#ef4444"
            radius = 10
        elif u["founded"] < 1200:
            color = "#f59e0b"
            radius = 9
        elif u["founded"] < 1350:
            color = "#f97316"
            radius = 8
        else:
            color = "#06b6d4"
            radius = 7
        popup_html = f"""
        <div style="font-family:sans-serif;min-width:220px;">
            <b style="color:{color};font-size:14px;">{safe_name}</b><br>
            <b>Country:</b> {safe_country}<br>
            <b>Founded:</b> {u['founded']} ({age} years old)<br>
            <b>Claim:</b> {safe_claim}<br>
            <b>Notable:</b> {safe_notable}
        </div>
        """
        _add_circle_marker(fg, u["lat"], u["lon"], safe_name, color, popup_html, radius)
    fg.add_to(m)
    return m


# ---------------------------------------------------------------------------
# Chart builders
# ---------------------------------------------------------------------------

def build_bar_chart(labels: list, values: list, title: str, xlabel: str, ylabel: str, color: str = "#06b6d4"):
    """Build a dark-themed matplotlib bar chart and return the figure."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    bars = ax.barh(labels, values, color=color, edgecolor=color, alpha=0.85)
    ax.set_xlabel(xlabel, color="#e8ecf4", fontsize=11)
    ax.set_ylabel(ylabel, color="#e8ecf4", fontsize=11)
    ax.set_title(title, color="#e8ecf4", fontsize=13, fontweight="bold")
    ax.tick_params(colors="#8b97b0", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#2a3550")
    ax.spines["left"].set_color("#2a3550")
    for bar_val, bar_obj in zip(values, bars):
        ax.text(bar_val + max(values) * 0.01, bar_obj.get_y() + bar_obj.get_height() / 2,
                str(bar_val), va="center", color="#e8ecf4", fontsize=9)
    plt.tight_layout()
    return fig


def build_pie_chart(labels: list, values: list, title: str, colors: list = None):
    """Build a dark-themed matplotlib pie chart and return the figure."""
    import matplotlib.pyplot as plt
    if colors is None:
        colors = ["#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444",
                  "#ec4899", "#3b82f6", "#a855f7", "#14b8a6", "#f97316",
                  "#64748b", "#38bdf8"]
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=colors[:len(labels)],
        autopct="%1.1f%%", startangle=140,
        textprops={"color": "#e8ecf4", "fontsize": 9},
    )
    for t in autotexts:
        t.set_color("#0a0e1a")
        t.set_fontsize(8)
    ax.set_title(title, color="#e8ecf4", fontsize=13, fontweight="bold")
    plt.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_education_maps_tab():
    """Render the Education & Research Maps tab."""
    st.markdown(
        '<div class="tab-header violet">'
        "<h4>Education & Research Maps</h4>"
        "<p>Explore universities, libraries, research institutions, museums, "
        "and centers of knowledge worldwide</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    MAP_MODES = [
        "World Universities",
        "Libraries of the World",
        "Research Institutions",
        "Nobel Prize Origins",
        "UNESCO World Heritage",
        "Museums & Galleries",
        "Science Parks & Innovation Hubs",
        "Astronomical Observatories",
        "Botanical Gardens",
        "Ancient Universities",
    ]

    mode = st.selectbox("Map Mode", MAP_MODES, key="edu_map_mode")

    st.markdown("---")

    # -----------------------------------------------------------------------
    # MODE 1: World Universities
    # -----------------------------------------------------------------------
    if mode == "World Universities":
        st.subheader("World Universities")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            country_filter = st.selectbox(
                "Filter by Country",
                ["All"] + sorted(set(u["country"] for u in WORLD_UNIVERSITIES)),
                key="edu_uni_country",
            )
        with col_f2:
            type_filter = st.selectbox(
                "Filter by Type",
                ["All", "Public", "Private"],
                key="edu_uni_type",
            )
        with col_f3:
            top_n = st.slider("Show Top N", 10, 50, 50, key="edu_uni_topn")

        filtered = WORLD_UNIVERSITIES[:top_n]
        if country_filter != "All":
            filtered = [u for u in filtered if u["country"] == country_filter]
        if type_filter != "All":
            filtered = [u for u in filtered if u["type"] == type_filter]

        countries_represented = len(set(u["country"] for u in filtered))
        avg_founded = int(sum(u["founded"] for u in filtered) / len(filtered)) if filtered else 0
        public_count = sum(1 for u in filtered if u["type"] == "Public")
        private_count = sum(1 for u in filtered if u["type"] == "Private")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Universities", len(filtered))
        c2.metric("Countries", countries_represented)
        c3.metric("Public / Private", f"{public_count} / {private_count}")
        c4.metric("Avg. Founded", str(avg_founded))

        if filtered:
            m = build_universities_map(filtered)
            components.html(m._repr_html_(), height=550)

            df = pd.DataFrame(filtered)
            df = df.sort_values("ranking")
            st.dataframe(df, width="stretch")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "world_universities.csv", "text/csv", key="dl_uni")

            country_counts = df["country"].value_counts().head(15)
            fig = build_bar_chart(
                country_counts.index.tolist(),
                country_counts.values.tolist(),
                "Universities by Country (Top 15)",
                "Count", "Country", "#06b6d4",
            )
            st.pyplot(fig)
        else:
            st.info("No universities match the current filters.")

    # -----------------------------------------------------------------------
    # MODE 2: Libraries of the World
    # -----------------------------------------------------------------------
    elif mode == "Libraries of the World":
        st.subheader("Great Libraries of the World")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            lib_type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + sorted(set(lib["type"] for lib in WORLD_LIBRARIES)),
                key="edu_lib_type",
            )
        with col_f2:
            lib_country_filter = st.selectbox(
                "Filter by Country",
                ["All"] + sorted(set(lib["country"] for lib in WORLD_LIBRARIES)),
                key="edu_lib_country",
            )

        filtered = WORLD_LIBRARIES[:]
        if lib_type_filter != "All":
            filtered = [lib for lib in filtered if lib["type"] == lib_type_filter]
        if lib_country_filter != "All":
            filtered = [lib for lib in filtered if lib["country"] == lib_country_filter]

        countries_lib = len(set(lib["country"] for lib in filtered))
        oldest_lib = min(filtered, key=lambda x: x["founded"])["name"] if filtered else "N/A"
        national_count = sum(1 for lib in filtered if lib["type"] == "National")
        academic_count = sum(1 for lib in filtered if lib["type"] == "Academic")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Libraries", len(filtered))
        c2.metric("Countries", countries_lib)
        c3.metric("National", national_count)
        c4.metric("Academic", academic_count)

        if filtered:
            m = build_libraries_map(filtered)
            components.html(m._repr_html_(), height=550)

            df = pd.DataFrame(filtered)
            df = df.sort_values("founded")
            st.dataframe(df, width="stretch")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "world_libraries.csv", "text/csv", key="dl_lib")

            type_counts = df["type"].value_counts()
            fig = build_pie_chart(
                type_counts.index.tolist(),
                type_counts.values.tolist(),
                "Libraries by Type",
            )
            st.pyplot(fig)
        else:
            st.info("No libraries match the current filters.")

    # -----------------------------------------------------------------------
    # MODE 3: Research Institutions
    # -----------------------------------------------------------------------
    elif mode == "Research Institutions":
        st.subheader("Research Institutions Worldwide")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            field_filter = st.selectbox(
                "Filter by Field",
                ["All"] + sorted(set(r["field"] for r in RESEARCH_INSTITUTIONS)),
                key="edu_res_field",
            )
        with col_f2:
            res_type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + sorted(set(r["type"] for r in RESEARCH_INSTITUTIONS)),
                key="edu_res_type",
            )
        with col_f3:
            res_country_filter = st.selectbox(
                "Filter by Country",
                ["All"] + sorted(set(r["country"] for r in RESEARCH_INSTITUTIONS)),
                key="edu_res_country",
            )

        filtered = RESEARCH_INSTITUTIONS[:]
        if field_filter != "All":
            filtered = [r for r in filtered if r["field"] == field_filter]
        if res_type_filter != "All":
            filtered = [r for r in filtered if r["type"] == res_type_filter]
        if res_country_filter != "All":
            filtered = [r for r in filtered if r["country"] == res_country_filter]

        countries_res = len(set(r["country"] for r in filtered))
        fields_res = len(set(r["field"] for r in filtered))
        govt_count = sum(1 for r in filtered if r["type"] == "Government")
        intl_count = sum(1 for r in filtered if r["type"] == "International")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Institutions", len(filtered))
        c2.metric("Countries", countries_res)
        c3.metric("Research Fields", fields_res)
        c4.metric("Government Labs", govt_count)

        if filtered:
            m = build_research_map(filtered)
            components.html(m._repr_html_(), height=550)

            df = pd.DataFrame(filtered)
            df = df.sort_values("founded")
            st.dataframe(df, width="stretch")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "research_institutions.csv", "text/csv", key="dl_res")

            field_counts = df["field"].value_counts().head(12)
            fig = build_bar_chart(
                field_counts.index.tolist(),
                field_counts.values.tolist(),
                "Institutions by Research Field",
                "Count", "Field", "#10b981",
            )
            st.pyplot(fig)
        else:
            st.info("No institutions match the current filters.")

    # -----------------------------------------------------------------------
    # MODE 4: Nobel Prize Origins
    # -----------------------------------------------------------------------
    elif mode == "Nobel Prize Origins":
        st.subheader("Nobel Prize Laureates by Country")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            min_laureates = st.slider("Minimum Laureates", 1, 50, 1, key="edu_nobel_min")
        with col_f2:
            sort_order = st.selectbox("Sort Order", ["Descending", "Ascending"], key="edu_nobel_sort")

        filtered_nobel = {k: v for k, v in NOBEL_LAUREATES_BY_COUNTRY.items() if v >= min_laureates}
        total_laureates = sum(filtered_nobel.values())
        top_country = max(filtered_nobel, key=filtered_nobel.get) if filtered_nobel else "N/A"
        top_count = filtered_nobel.get(top_country, 0)
        avg_per_country = round(total_laureates / len(filtered_nobel), 1) if filtered_nobel else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Countries Shown", len(filtered_nobel))
        c2.metric("Total Laureates", f"{total_laureates:,}")
        c3.metric("Top Country", f"{top_country} ({top_count})")
        c4.metric("Avg per Country", avg_per_country)

        if filtered_nobel:
            m = build_nobel_map(filtered_nobel)
            components.html(m._repr_html_(), height=550)

            ascending = sort_order == "Ascending"
            df_data = [{"Country": k, "Nobel Laureates": v} for k, v in filtered_nobel.items()]
            df = pd.DataFrame(df_data).sort_values("Nobel Laureates", ascending=ascending)
            st.dataframe(df, width="stretch")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "nobel_laureates.csv", "text/csv", key="dl_nobel")

            top_20 = df.head(20).sort_values("Nobel Laureates", ascending=True)
            fig = build_bar_chart(
                top_20["Country"].tolist(),
                top_20["Nobel Laureates"].tolist(),
                "Top 20 Countries by Nobel Laureates",
                "Laureates", "Country", "#f59e0b",
            )
            st.pyplot(fig)
        else:
            st.info("No countries match the current filter.")

    # -----------------------------------------------------------------------
    # MODE 5: UNESCO World Heritage
    # -----------------------------------------------------------------------
    elif mode == "UNESCO World Heritage":
        st.subheader("UNESCO World Heritage Sites")

        PRESETS = {
            "Custom Location": None,
            "Rome, Italy": {"lat": 41.8933, "lon": 12.4829},
            "Paris, France": {"lat": 48.8566, "lon": 2.3522},
            "London, UK": {"lat": 51.5074, "lon": -0.1278},
            "Cairo, Egypt": {"lat": 30.0444, "lon": 31.2357},
            "Beijing, China": {"lat": 39.9042, "lon": 116.4074},
            "Kyoto, Japan": {"lat": 35.0116, "lon": 135.7681},
            "Athens, Greece": {"lat": 37.9838, "lon": 23.7275},
            "Istanbul, Turkey": {"lat": 41.0082, "lon": 28.9784},
            "Mexico City, Mexico": {"lat": 19.4326, "lon": -99.1332},
            "Cusco, Peru": {"lat": -13.5320, "lon": -71.9675},
        }

        preset = st.selectbox("Quick Location", list(PRESETS.keys()), key="edu_unesco_preset")

        col_f1, col_f2, col_f3 = st.columns(3)
        if preset != "Custom Location" and PRESETS[preset]:
            default_lat = PRESETS[preset]["lat"]
            default_lon = PRESETS[preset]["lon"]
        else:
            default_lat = 41.89
            default_lon = 12.48
        with col_f1:
            lat = st.number_input("Latitude", -90.0, 90.0, default_lat, 0.01, key="edu_unesco_lat")
        with col_f2:
            lon = st.number_input("Longitude", -180.0, 180.0, default_lon, 0.01, key="edu_unesco_lon")
        with col_f3:
            radius_km = st.slider("Radius (km)", 5, 200, 50, key="edu_unesco_radius")

        if st.button("Search UNESCO Sites", key="edu_unesco_search", type="primary"):
            with st.spinner("Querying Overpass API for UNESCO World Heritage sites..."):
                sites = fetch_unesco_sites(lat, lon, radius_km)

            if not sites:
                st.warning("No UNESCO World Heritage sites found in this area. Try expanding the radius or changing location.")
            else:
                st.success(f"Found {len(sites)} UNESCO World Heritage site(s)")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Sites Found", len(sites))
                with_ref = sum(1 for s in sites if s.get("heritage_ref", "N/A") != "N/A")
                c2.metric("With WHC Ref", with_ref)
                with_wiki = sum(1 for s in sites if s.get("wikipedia"))
                c3.metric("With Wikipedia", with_wiki)
                c4.metric("Search Radius", f"{radius_km} km")

                m = build_unesco_map(sites)
                components.html(m._repr_html_(), height=550)

                df = pd.DataFrame(sites)
                st.dataframe(df, width="stretch")

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "unesco_sites.csv", "text/csv", key="edum_dl_unesco")
        else:
            st.info("Configure a location and click **Search UNESCO Sites** to find World Heritage sites nearby.")

    # -----------------------------------------------------------------------
    # MODE 6: Museums & Galleries
    # -----------------------------------------------------------------------
    elif mode == "Museums & Galleries":
        st.subheader("Museums & Galleries Worldwide")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            mus_type_filter = st.selectbox(
                "Filter by Type",
                ["All"] + sorted(set(m["type"] for m in WORLD_MUSEUMS)),
                key="edu_mus_type",
            )
        with col_f2:
            mus_country_filter = st.selectbox(
                "Filter by Country",
                ["All"] + sorted(set(m["country"] for m in WORLD_MUSEUMS)),
                key="edu_mus_country",
            )
        with col_f3:
            min_visitors = st.slider("Min. Visitors (M/year)", 0.0, 8.0, 0.0, 0.5, key="edu_mus_vis")

        filtered = WORLD_MUSEUMS[:]
        if mus_type_filter != "All":
            filtered = [m for m in filtered if m["type"] == mus_type_filter]
        if mus_country_filter != "All":
            filtered = [m for m in filtered if m["country"] == mus_country_filter]
        if min_visitors > 0:
            filtered = [m for m in filtered if m["visitors_m"] >= min_visitors]

        countries_mus = len(set(m["country"] for m in filtered))
        total_visitors = sum(m["visitors_m"] for m in filtered)
        avg_founded_mus = int(sum(m["founded"] for m in filtered) / len(filtered)) if filtered else 0
        most_visited = max(filtered, key=lambda x: x["visitors_m"])["name"] if filtered else "N/A"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Museums", len(filtered))
        c2.metric("Countries", countries_mus)
        c3.metric("Total Visitors", f"{total_visitors:.1f}M")
        c4.metric("Avg. Founded", str(avg_founded_mus))

        if filtered:
            m_map = build_museums_map(filtered)
            components.html(m_map._repr_html_(), height=550)

            df = pd.DataFrame(filtered)
            df = df.sort_values("visitors_m", ascending=False)
            st.dataframe(df, width="stretch")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "world_museums.csv", "text/csv", key="dl_mus")

            top_15 = df.head(15).sort_values("visitors_m", ascending=True)
            fig = build_bar_chart(
                top_15["name"].tolist(),
                top_15["visitors_m"].tolist(),
                "Top 15 Museums by Annual Visitors (Millions)",
                "Visitors (M)", "Museum", "#ec4899",
            )
            st.pyplot(fig)
        else:
            st.info("No museums match the current filters.")

    # -----------------------------------------------------------------------
    # MODE 7: Science Parks & Innovation Hubs
    # -----------------------------------------------------------------------
    elif mode == "Science Parks & Innovation Hubs":
        st.subheader("Science Parks & Innovation Hubs")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            sp_focus_filter = st.selectbox(
                "Filter by Focus",
                ["All"] + sorted(set(p["focus"] for p in SCIENCE_PARKS)),
                key="edu_sp_focus",
            )
        with col_f2:
            sp_country_filter = st.selectbox(
                "Filter by Country",
                ["All"] + sorted(set(p["country"] for p in SCIENCE_PARKS)),
                key="edu_sp_country",
            )

        filtered = SCIENCE_PARKS[:]
        if sp_focus_filter != "All":
            filtered = [p for p in filtered if p["focus"] == sp_focus_filter]
        if sp_country_filter != "All":
            filtered = [p for p in filtered if p["country"] == sp_country_filter]

        countries_sp = len(set(p["country"] for p in filtered))
        focuses_sp = len(set(p["focus"] for p in filtered))
        oldest_sp = min(filtered, key=lambda x: x["founded"])["name"] if filtered else "N/A"
        newest_sp = max(filtered, key=lambda x: x["founded"])["name"] if filtered else "N/A"

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Innovation Hubs", len(filtered))
        c2.metric("Countries", countries_sp)
        c3.metric("Focus Areas", focuses_sp)
        c4.metric("Oldest", oldest_sp[:25] + "..." if len(oldest_sp) > 25 else oldest_sp)

        if filtered:
            m = build_science_parks_map(filtered)
            components.html(m._repr_html_(), height=550)

            df = pd.DataFrame(filtered)
            df = df.sort_values("founded")
            st.dataframe(df, width="stretch")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "science_parks.csv", "text/csv", key="dl_sp")

            focus_counts = df["focus"].value_counts()
            fig = build_pie_chart(
                focus_counts.index.tolist(),
                focus_counts.values.tolist(),
                "Innovation Hubs by Focus Area",
            )
            st.pyplot(fig)
        else:
            st.info("No science parks match the current filters.")

    # -----------------------------------------------------------------------
    # MODE 8: Astronomical Observatories
    # -----------------------------------------------------------------------
    elif mode == "Astronomical Observatories":
        st.subheader("Astronomical Observatories Worldwide")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            obs_type_filter = st.selectbox(
                "Filter by Type",
                ["All", "Optical", "Radio", "Optical/IR", "Multiple", "Space", "Solar"],
                key="edu_obs_type",
            )
        with col_f2:
            min_altitude = st.slider("Min. Altitude (m)", 0, 5000, 0, 100, key="edu_obs_alt")

        filtered = ASTRONOMICAL_OBSERVATORIES[:]
        if obs_type_filter != "All":
            filtered = [o for o in filtered if obs_type_filter.lower() in o["type"].lower()]
        if min_altitude > 0:
            filtered = [o for o in filtered if o["altitude_m"] >= min_altitude]

        countries_obs = len(set(o["country"] for o in filtered))
        max_alt = max(filtered, key=lambda x: x["altitude_m"]) if filtered else None
        avg_alt = int(sum(o["altitude_m"] for o in filtered) / len(filtered)) if filtered else 0
        radio_count = sum(1 for o in filtered if "Radio" in o["type"])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Observatories", len(filtered))
        c2.metric("Countries", countries_obs)
        c3.metric("Avg Altitude", f"{avg_alt:,}m")
        c4.metric("Highest", f"{max_alt['altitude_m']:,}m" if max_alt else "N/A")

        if filtered:
            m = build_observatories_map(filtered)
            components.html(m._repr_html_(), height=550)

            df = pd.DataFrame(filtered)
            df = df.sort_values("altitude_m", ascending=False)
            st.dataframe(df, width="stretch")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "observatories.csv", "text/csv", key="dl_obs")

            top_alt = df.head(15).sort_values("altitude_m", ascending=True)
            fig = build_bar_chart(
                top_alt["name"].tolist(),
                top_alt["altitude_m"].tolist(),
                "Top Observatories by Altitude",
                "Altitude (m)", "Observatory", "#a855f7",
            )
            st.pyplot(fig)
        else:
            st.info("No observatories match the current filters.")

    # -----------------------------------------------------------------------
    # MODE 9: Botanical Gardens
    # -----------------------------------------------------------------------
    elif mode == "Botanical Gardens":
        st.subheader("Botanical Gardens")

        GARDEN_PRESETS = {
            "Custom Location": None,
            "London, UK": {"lat": 51.5074, "lon": -0.1278},
            "Berlin, Germany": {"lat": 52.5200, "lon": 13.4050},
            "New York, USA": {"lat": 40.7128, "lon": -74.0060},
            "Sydney, Australia": {"lat": -33.8688, "lon": 151.2093},
            "Singapore": {"lat": 1.3521, "lon": 103.8198},
            "Cape Town, South Africa": {"lat": -33.9249, "lon": 18.4241},
            "Rio de Janeiro, Brazil": {"lat": -22.9068, "lon": -43.1729},
            "Kyoto, Japan": {"lat": 35.0116, "lon": 135.7681},
            "Edinburgh, UK": {"lat": 55.9533, "lon": -3.1883},
        }

        preset = st.selectbox("Quick Location", list(GARDEN_PRESETS.keys()), key="edu_garden_preset")

        col_f1, col_f2, col_f3 = st.columns(3)
        if preset != "Custom Location" and GARDEN_PRESETS[preset]:
            g_lat = GARDEN_PRESETS[preset]["lat"]
            g_lon = GARDEN_PRESETS[preset]["lon"]
        else:
            g_lat = 51.47
            g_lon = -0.30
        with col_f1:
            lat = st.number_input("Latitude", -90.0, 90.0, g_lat, 0.01, key="edu_garden_lat")
        with col_f2:
            lon = st.number_input("Longitude", -180.0, 180.0, g_lon, 0.01, key="edu_garden_lon")
        with col_f3:
            radius_km = st.slider("Radius (km)", 5, 200, 50, key="edu_garden_radius")

        if st.button("Search Botanical Gardens", key="edu_garden_search", type="primary"):
            with st.spinner("Querying Overpass API for botanical gardens..."):
                gardens = fetch_botanical_gardens(lat, lon, radius_km)

            if not gardens:
                st.warning("No botanical gardens found in this area. Try expanding the radius or changing location.")
            else:
                st.success(f"Found {len(gardens)} botanical garden(s)")

                with_website = sum(1 for g in gardens if g.get("website"))
                with_operator = sum(1 for g in gardens if g.get("operator"))
                with_wiki = sum(1 for g in gardens if g.get("wikidata") or g.get("wikipedia"))

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Gardens Found", len(gardens))
                c2.metric("With Website", with_website)
                c3.metric("With Operator", with_operator)
                c4.metric("Search Radius", f"{radius_km} km")

                m = build_botanical_gardens_map(gardens)
                components.html(m._repr_html_(), height=550)

                df = pd.DataFrame(gardens)
                st.dataframe(df, width="stretch")

                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("Download CSV", csv, "botanical_gardens.csv", "text/csv", key="dl_garden")
        else:
            st.info("Configure a location and click **Search Botanical Gardens** to find gardens nearby.")

    # -----------------------------------------------------------------------
    # MODE 10: Ancient Universities
    # -----------------------------------------------------------------------
    elif mode == "Ancient Universities":
        st.subheader("Ancient Universities Still Operating")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            anc_country_filter = st.selectbox(
                "Filter by Country",
                ["All"] + sorted(set(u["country"] for u in ANCIENT_UNIVERSITIES)),
                key="edu_anc_country",
            )
        with col_f2:
            max_year = st.slider("Founded Before Year", 800, 1500, 1500, 10, key="edu_anc_year")

        filtered = [u for u in ANCIENT_UNIVERSITIES if u["founded"] <= max_year]
        if anc_country_filter != "All":
            filtered = [u for u in filtered if u["country"] == anc_country_filter]

        countries_anc = len(set(u["country"] for u in filtered))
        oldest_uni = min(filtered, key=lambda x: x["founded"]) if filtered else None
        avg_age = int(sum(2026 - u["founded"] for u in filtered) / len(filtered)) if filtered else 0
        pre_1200 = sum(1 for u in filtered if u["founded"] < 1200)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Universities", len(filtered))
        c2.metric("Countries", countries_anc)
        c3.metric("Avg Age (years)", f"{avg_age:,}")
        c4.metric("Oldest", f"{oldest_uni['name'][:20]} ({oldest_uni['founded']})" if oldest_uni else "N/A")

        if filtered:
            m = build_ancient_universities_map(filtered)
            components.html(m._repr_html_(), height=550)

            df = pd.DataFrame(filtered)
            df["age_years"] = 2026 - df["founded"]
            df = df.sort_values("founded")
            st.dataframe(df, width="stretch")

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", csv, "ancient_universities.csv", "text/csv", key="dl_anc")

            timeline_df = df.sort_values("founded", ascending=True)
            fig = build_bar_chart(
                timeline_df["name"].tolist(),
                timeline_df["age_years"].tolist(),
                "Ancient Universities by Age (Years)",
                "Age (years)", "University", "#f97316",
            )
            st.pyplot(fig)
        else:
            st.info("No ancient universities match the current filters.")
