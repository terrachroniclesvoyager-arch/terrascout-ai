# -*- coding: utf-8 -*-
"""
Sports & Events Maps module for TerraScout AI.
Provides 10 thematic sports map types covering Olympic host cities,
FIFA World Cups, F1 circuits, tennis grand slams, world marathons,
football stadiums, ski resorts, surf spots, cycling climbs, and
motorsport circuits. All data is either hardcoded or sourced from
Overpass API (for football stadiums).
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# =====================================================================
# CONSTANTS & THEME
# =====================================================================
DARK_BG = "#0a0e1a"
SURFACE = "#111827"
CARD_BG = "#1a2235"
BORDER = "#2a3550"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT = "#06b6d4"

MAP_TYPES = [
    "Olympic Host Cities",
    "FIFA World Cup",
    "F1 Circuits",
    "Tennis Grand Slams",
    "World Marathons",
    "Football Stadiums",
    "Ski Resorts",
    "Surf Spots",
    "Cycling Climbs",
    "Motorsport Circuits",
]

# =====================================================================
# 1. OLYMPIC HOST CITIES DATA
# =====================================================================
SUMMER_OLYMPICS = [
    {"year": 1896, "city": "Athens", "country": "Greece", "lat": 37.97, "lon": 23.72, "notable": "First modern Olympics"},
    {"year": 1900, "city": "Paris", "country": "France", "lat": 48.86, "lon": 2.35, "notable": "Women competed for the first time"},
    {"year": 1904, "city": "St. Louis", "country": "USA", "lat": 38.63, "lon": -90.20, "notable": "First Games in North America"},
    {"year": 1908, "city": "London", "country": "UK", "lat": 51.51, "lon": -0.13, "notable": "Marathon distance standardized"},
    {"year": 1912, "city": "Stockholm", "country": "Sweden", "lat": 59.33, "lon": 18.07, "notable": "Electronic timing introduced"},
    {"year": 1920, "city": "Antwerp", "country": "Belgium", "lat": 51.22, "lon": 4.40, "notable": "Olympic flag and oath debut"},
    {"year": 1924, "city": "Paris", "country": "France", "lat": 48.86, "lon": 2.35, "notable": "Olympic motto Citius Altius Fortius"},
    {"year": 1928, "city": "Amsterdam", "country": "Netherlands", "lat": 52.37, "lon": 4.90, "notable": "Olympic flame introduced"},
    {"year": 1932, "city": "Los Angeles", "country": "USA", "lat": 34.05, "lon": -118.24, "notable": "First Olympic Village"},
    {"year": 1936, "city": "Berlin", "country": "Germany", "lat": 52.52, "lon": 13.41, "notable": "First televised Olympics"},
    {"year": 1948, "city": "London", "country": "UK", "lat": 51.51, "lon": -0.13, "notable": "Post-WWII Austerity Games"},
    {"year": 1952, "city": "Helsinki", "country": "Finland", "lat": 60.17, "lon": 24.94, "notable": "Soviet Union debut"},
    {"year": 1956, "city": "Melbourne", "country": "Australia", "lat": -37.81, "lon": 144.96, "notable": "First Games in Southern Hemisphere"},
    {"year": 1960, "city": "Rome", "country": "Italy", "lat": 41.90, "lon": 12.50, "notable": "Abebe Bikila barefoot marathon"},
    {"year": 1964, "city": "Tokyo", "country": "Japan", "lat": 35.68, "lon": 139.69, "notable": "First Asian host, satellite broadcast"},
    {"year": 1968, "city": "Mexico City", "country": "Mexico", "lat": 19.43, "lon": -99.13, "notable": "High altitude, Black Power salute"},
    {"year": 1972, "city": "Munich", "country": "Germany", "lat": 48.14, "lon": 11.58, "notable": "Munich massacre tragedy"},
    {"year": 1976, "city": "Montreal", "country": "Canada", "lat": 45.50, "lon": -73.57, "notable": "Nadia Comaneci perfect 10"},
    {"year": 1980, "city": "Moscow", "country": "USSR", "lat": 55.76, "lon": 37.62, "notable": "Western boycott"},
    {"year": 1984, "city": "Los Angeles", "country": "USA", "lat": 34.05, "lon": -118.24, "notable": "Eastern bloc boycott, Carl Lewis"},
    {"year": 1988, "city": "Seoul", "country": "South Korea", "lat": 37.57, "lon": 126.98, "notable": "Ben Johnson disqualification"},
    {"year": 1992, "city": "Barcelona", "country": "Spain", "lat": 41.39, "lon": 2.17, "notable": "Dream Team in basketball"},
    {"year": 1996, "city": "Atlanta", "country": "USA", "lat": 33.75, "lon": -84.39, "notable": "Centennial Olympics"},
    {"year": 2000, "city": "Sydney", "country": "Australia", "lat": -33.87, "lon": 151.21, "notable": "Best Games ever proclaimed"},
    {"year": 2004, "city": "Athens", "country": "Greece", "lat": 37.97, "lon": 23.72, "notable": "Return to birthplace"},
    {"year": 2008, "city": "Beijing", "country": "China", "lat": 39.91, "lon": 116.40, "notable": "Michael Phelps 8 golds"},
    {"year": 2012, "city": "London", "country": "UK", "lat": 51.51, "lon": -0.13, "notable": "Usain Bolt triple-triple"},
    {"year": 2016, "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.91, "lon": -43.17, "notable": "First South American host"},
    {"year": 2021, "city": "Tokyo", "country": "Japan", "lat": 35.68, "lon": 139.69, "notable": "COVID-delayed, no spectators"},
    {"year": 2024, "city": "Paris", "country": "France", "lat": 48.86, "lon": 2.35, "notable": "Seine opening ceremony"},
]

WINTER_OLYMPICS = [
    {"year": 1924, "city": "Chamonix", "country": "France", "lat": 45.92, "lon": 6.87, "notable": "First Winter Olympics"},
    {"year": 1928, "city": "St. Moritz", "country": "Switzerland", "lat": 46.50, "lon": 9.84, "notable": "First Olympic flame at Winter Games"},
    {"year": 1932, "city": "Lake Placid", "country": "USA", "lat": 44.28, "lon": -73.99, "notable": "Sonja Henie skating star"},
    {"year": 1936, "city": "Garmisch-Partenkirchen", "country": "Germany", "lat": 47.50, "lon": 11.10, "notable": "Alpine skiing debut"},
    {"year": 1948, "city": "St. Moritz", "country": "Switzerland", "lat": 46.50, "lon": 9.84, "notable": "Post-war return"},
    {"year": 1952, "city": "Oslo", "country": "Norway", "lat": 59.91, "lon": 10.75, "notable": "Norway dominates cross-country"},
    {"year": 1956, "city": "Cortina d'Ampezzo", "country": "Italy", "lat": 46.54, "lon": 12.14, "notable": "First televised Winter Games"},
    {"year": 1960, "city": "Squaw Valley", "country": "USA", "lat": 39.20, "lon": -120.23, "notable": "Computer used for results"},
    {"year": 1964, "city": "Innsbruck", "country": "Austria", "lat": 47.26, "lon": 11.39, "notable": "Luge introduced"},
    {"year": 1968, "city": "Grenoble", "country": "France", "lat": 45.19, "lon": 5.72, "notable": "Jean-Claude Killy triple gold"},
    {"year": 1972, "city": "Sapporo", "country": "Japan", "lat": 43.06, "lon": 141.35, "notable": "First Asian Winter Games"},
    {"year": 1976, "city": "Innsbruck", "country": "Austria", "lat": 47.26, "lon": 11.39, "notable": "Replaced Denver as host"},
    {"year": 1980, "city": "Lake Placid", "country": "USA", "lat": 44.28, "lon": -73.99, "notable": "Miracle on Ice"},
    {"year": 1984, "city": "Sarajevo", "country": "Yugoslavia", "lat": 43.86, "lon": 18.41, "notable": "Torvill and Dean Bolero"},
    {"year": 1988, "city": "Calgary", "country": "Canada", "lat": 51.05, "lon": -114.07, "notable": "Cool Runnings inspiration"},
    {"year": 1992, "city": "Albertville", "country": "France", "lat": 45.68, "lon": 6.39, "notable": "Last same-year Summer/Winter"},
    {"year": 1994, "city": "Lillehammer", "country": "Norway", "lat": 61.12, "lon": 10.47, "notable": "New two-year cycle begins"},
    {"year": 1998, "city": "Nagano", "country": "Japan", "lat": 36.65, "lon": 138.18, "notable": "NHL players in hockey"},
    {"year": 2002, "city": "Salt Lake City", "country": "USA", "lat": 40.76, "lon": -111.89, "notable": "Figure skating scandal"},
    {"year": 2006, "city": "Turin", "country": "Italy", "lat": 45.07, "lon": 7.69, "notable": "Italy strong at home"},
    {"year": 2010, "city": "Vancouver", "country": "Canada", "lat": 49.28, "lon": -123.12, "notable": "Canada record golds at home"},
    {"year": 2014, "city": "Sochi", "country": "Russia", "lat": 43.60, "lon": 39.73, "notable": "Most expensive Games ever"},
    {"year": 2018, "city": "PyeongChang", "country": "South Korea", "lat": 37.37, "lon": 128.39, "notable": "Unified Korean team"},
    {"year": 2022, "city": "Beijing", "country": "China", "lat": 39.91, "lon": 116.40, "notable": "First dual Summer/Winter host city"},
    {"year": 2026, "city": "Milan-Cortina", "country": "Italy", "lat": 45.46, "lon": 9.19, "notable": "Dual-city host"},
]

# =====================================================================
# 2. FIFA WORLD CUP DATA
# =====================================================================
FIFA_WORLD_CUPS = [
    {"year": 1930, "host": "Uruguay", "winner": "Uruguay", "runner_up": "Argentina", "venue": "Estadio Centenario", "lat": -34.89, "lon": -56.15},
    {"year": 1934, "host": "Italy", "winner": "Italy", "runner_up": "Czechoslovakia", "venue": "Stadio Nazionale PNF", "lat": 41.90, "lon": 12.50},
    {"year": 1938, "host": "France", "winner": "Italy", "runner_up": "Hungary", "venue": "Stade Olympique", "lat": 48.93, "lon": 2.32},
    {"year": 1950, "host": "Brazil", "winner": "Uruguay", "runner_up": "Brazil", "venue": "Maracana", "lat": -22.91, "lon": -43.23},
    {"year": 1954, "host": "Switzerland", "winner": "W. Germany", "runner_up": "Hungary", "venue": "Wankdorf Stadium", "lat": 46.96, "lon": 7.47},
    {"year": 1958, "host": "Sweden", "winner": "Brazil", "runner_up": "Sweden", "venue": "Rasunda Stadium", "lat": 59.37, "lon": 18.00},
    {"year": 1962, "host": "Chile", "winner": "Brazil", "runner_up": "Czechoslovakia", "venue": "Estadio Nacional", "lat": -33.47, "lon": -70.61},
    {"year": 1966, "host": "England", "winner": "England", "runner_up": "W. Germany", "venue": "Wembley Stadium", "lat": 51.56, "lon": -0.28},
    {"year": 1970, "host": "Mexico", "winner": "Brazil", "runner_up": "Italy", "venue": "Estadio Azteca", "lat": 19.30, "lon": -99.15},
    {"year": 1974, "host": "W. Germany", "winner": "W. Germany", "runner_up": "Netherlands", "venue": "Olympiastadion Munich", "lat": 48.17, "lon": 11.55},
    {"year": 1978, "host": "Argentina", "winner": "Argentina", "runner_up": "Netherlands", "venue": "Estadio Monumental", "lat": -34.55, "lon": -58.45},
    {"year": 1982, "host": "Spain", "winner": "Italy", "runner_up": "W. Germany", "venue": "Santiago Bernabeu", "lat": 40.45, "lon": -3.69},
    {"year": 1986, "host": "Mexico", "winner": "Argentina", "runner_up": "W. Germany", "venue": "Estadio Azteca", "lat": 19.30, "lon": -99.15},
    {"year": 1990, "host": "Italy", "winner": "W. Germany", "runner_up": "Argentina", "venue": "Stadio Olimpico", "lat": 41.93, "lon": 12.45},
    {"year": 1994, "host": "USA", "winner": "Brazil", "runner_up": "Italy", "venue": "Rose Bowl", "lat": 34.16, "lon": -118.17},
    {"year": 1998, "host": "France", "winner": "France", "runner_up": "Brazil", "venue": "Stade de France", "lat": 48.92, "lon": 2.36},
    {"year": 2002, "host": "S. Korea / Japan", "winner": "Brazil", "runner_up": "Germany", "venue": "International Stadium Yokohama", "lat": 35.51, "lon": 139.61},
    {"year": 2006, "host": "Germany", "winner": "Italy", "runner_up": "France", "venue": "Olympiastadion Berlin", "lat": 52.51, "lon": 13.24},
    {"year": 2010, "host": "South Africa", "winner": "Spain", "runner_up": "Netherlands", "venue": "Soccer City", "lat": -26.24, "lon": 27.98},
    {"year": 2014, "host": "Brazil", "winner": "Germany", "runner_up": "Argentina", "venue": "Maracana", "lat": -22.91, "lon": -43.23},
    {"year": 2018, "host": "Russia", "winner": "France", "runner_up": "Croatia", "venue": "Luzhniki Stadium", "lat": 55.72, "lon": 37.55},
    {"year": 2022, "host": "Qatar", "winner": "Argentina", "runner_up": "France", "venue": "Lusail Stadium", "lat": 25.43, "lon": 51.49},
    {"year": 2026, "host": "USA / Mexico / Canada", "winner": "TBD", "runner_up": "TBD", "venue": "MetLife Stadium", "lat": 40.81, "lon": -74.07},
]

# =====================================================================
# 3. F1 CIRCUITS DATA (24 current circuits)
# =====================================================================
F1_CIRCUITS = [
    {"name": "Bahrain International Circuit", "location": "Sakhir, Bahrain", "lat": 26.03, "lon": 50.51, "length_km": 5.412, "lap_record": "1:31.447 (de la Rosa, 2005)", "first_gp": 2004},
    {"name": "Jeddah Corniche Circuit", "location": "Jeddah, Saudi Arabia", "lat": 21.63, "lon": 39.10, "length_km": 6.174, "lap_record": "1:30.734 (Hamilton, 2021)", "first_gp": 2021},
    {"name": "Albert Park Circuit", "location": "Melbourne, Australia", "lat": -37.85, "lon": 144.97, "length_km": 5.278, "lap_record": "1:19.813 (Leclerc, 2024)", "first_gp": 1996},
    {"name": "Suzuka International Racing Course", "location": "Suzuka, Japan", "lat": 34.84, "lon": 136.54, "length_km": 5.807, "lap_record": "1:30.983 (Hamilton, 2019)", "first_gp": 1987},
    {"name": "Shanghai International Circuit", "location": "Shanghai, China", "lat": 31.34, "lon": 121.22, "length_km": 5.451, "lap_record": "1:32.238 (M. Schumacher, 2004)", "first_gp": 2004},
    {"name": "Miami International Autodrome", "location": "Miami, USA", "lat": 25.96, "lon": -80.24, "length_km": 5.412, "lap_record": "1:29.708 (Verstappen, 2023)", "first_gp": 2022},
    {"name": "Autodromo Enzo e Dino Ferrari", "location": "Imola, Italy", "lat": 44.34, "lon": 11.71, "length_km": 4.909, "lap_record": "1:15.484 (Hamilton, 2020)", "first_gp": 1980},
    {"name": "Circuit de Monaco", "location": "Monte Carlo, Monaco", "lat": 43.73, "lon": 7.42, "length_km": 3.337, "lap_record": "1:12.909 (Hamilton, 2021)", "first_gp": 1950},
    {"name": "Circuit Gilles Villeneuve", "location": "Montreal, Canada", "lat": 45.50, "lon": -73.52, "length_km": 4.361, "lap_record": "1:13.078 (Bottas, 2019)", "first_gp": 1978},
    {"name": "Circuit de Barcelona-Catalunya", "location": "Barcelona, Spain", "lat": 41.57, "lon": 2.26, "length_km": 4.657, "lap_record": "1:16.330 (Verstappen, 2023)", "first_gp": 1991},
    {"name": "Red Bull Ring", "location": "Spielberg, Austria", "lat": 47.22, "lon": 14.76, "length_km": 4.318, "lap_record": "1:05.619 (Sainz, 2020)", "first_gp": 1970},
    {"name": "Silverstone Circuit", "location": "Silverstone, UK", "lat": 52.07, "lon": -1.02, "length_km": 5.891, "lap_record": "1:27.097 (Verstappen, 2020)", "first_gp": 1950},
    {"name": "Hungaroring", "location": "Budapest, Hungary", "lat": 47.58, "lon": 19.25, "length_km": 4.381, "lap_record": "1:16.627 (Hamilton, 2020)", "first_gp": 1986},
    {"name": "Circuit de Spa-Francorchamps", "location": "Stavelot, Belgium", "lat": 50.44, "lon": 5.97, "length_km": 7.004, "lap_record": "1:46.286 (Bottas, 2018)", "first_gp": 1950},
    {"name": "Circuit Zandvoort", "location": "Zandvoort, Netherlands", "lat": 52.39, "lon": 4.54, "length_km": 4.259, "lap_record": "1:11.097 (Hamilton, 2023)", "first_gp": 1952},
    {"name": "Autodromo Nazionale Monza", "location": "Monza, Italy", "lat": 45.62, "lon": 9.29, "length_km": 5.793, "lap_record": "1:21.046 (Barrichello, 2004)", "first_gp": 1950},
    {"name": "Baku City Circuit", "location": "Baku, Azerbaijan", "lat": 40.37, "lon": 49.85, "length_km": 6.003, "lap_record": "1:43.009 (Leclerc, 2019)", "first_gp": 2016},
    {"name": "Marina Bay Street Circuit", "location": "Singapore", "lat": 1.29, "lon": 103.86, "length_km": 4.940, "lap_record": "1:35.867 (Hamilton, 2023)", "first_gp": 2008},
    {"name": "Circuit of the Americas", "location": "Austin, USA", "lat": 30.13, "lon": -97.64, "length_km": 5.513, "lap_record": "1:36.169 (Leclerc, 2019)", "first_gp": 2012},
    {"name": "Autodromo Hermanos Rodriguez", "location": "Mexico City, Mexico", "lat": 19.40, "lon": -99.09, "length_km": 4.304, "lap_record": "1:17.774 (Bottas, 2021)", "first_gp": 1963},
    {"name": "Interlagos", "location": "Sao Paulo, Brazil", "lat": -23.70, "lon": -46.70, "length_km": 4.309, "lap_record": "1:10.540 (Bottas, 2018)", "first_gp": 1973},
    {"name": "Las Vegas Street Circuit", "location": "Las Vegas, USA", "lat": 36.12, "lon": -115.17, "length_km": 6.201, "lap_record": "1:35.490 (Piastri, 2023)", "first_gp": 2023},
    {"name": "Losail International Circuit", "location": "Lusail, Qatar", "lat": 25.49, "lon": 51.45, "length_km": 5.380, "lap_record": "1:24.319 (Verstappen, 2023)", "first_gp": 2021},
    {"year": 2004, "name": "Yas Marina Circuit", "location": "Abu Dhabi, UAE", "lat": 24.47, "lon": 54.60, "length_km": 5.281, "lap_record": "1:26.103 (Verstappen, 2021)", "first_gp": 2009},
]

# =====================================================================
# 4. TENNIS GRAND SLAMS & MAJOR VENUES
# =====================================================================
TENNIS_VENUES = [
    {"name": "Australian Open", "venue": "Melbourne Park", "city": "Melbourne", "country": "Australia", "lat": -37.82, "lon": 144.98, "surface": "Hard (GreenSet)", "capacity": 15000, "founded": 1905, "type": "Grand Slam"},
    {"name": "French Open", "venue": "Roland Garros", "city": "Paris", "country": "France", "lat": 48.85, "lon": 2.25, "surface": "Clay", "capacity": 15225, "founded": 1891, "type": "Grand Slam"},
    {"name": "Wimbledon", "venue": "All England Club", "city": "London", "country": "UK", "lat": 51.43, "lon": -0.21, "surface": "Grass", "capacity": 15000, "founded": 1877, "type": "Grand Slam"},
    {"name": "US Open", "venue": "Flushing Meadows", "city": "New York", "country": "USA", "lat": 40.75, "lon": -73.85, "surface": "Hard (DecoTurf)", "capacity": 23771, "founded": 1881, "type": "Grand Slam"},
    {"name": "Indian Wells Masters", "venue": "Indian Wells Tennis Garden", "city": "Indian Wells", "country": "USA", "lat": 33.72, "lon": -116.31, "surface": "Hard", "capacity": 16100, "founded": 1987, "type": "Masters 1000"},
    {"name": "Miami Open", "venue": "Hard Rock Stadium", "city": "Miami", "country": "USA", "lat": 25.96, "lon": -80.24, "surface": "Hard", "capacity": 13800, "founded": 1985, "type": "Masters 1000"},
    {"name": "Monte-Carlo Masters", "venue": "Monte-Carlo Country Club", "city": "Roquebrune-Cap-Martin", "country": "France", "lat": 43.75, "lon": 7.44, "surface": "Clay", "capacity": 10200, "founded": 1897, "type": "Masters 1000"},
    {"name": "Madrid Open", "venue": "Caja Magica", "city": "Madrid", "country": "Spain", "lat": 40.37, "lon": -3.69, "surface": "Clay", "capacity": 12442, "founded": 2002, "type": "Masters 1000"},
    {"name": "Italian Open", "venue": "Foro Italico", "city": "Rome", "country": "Italy", "lat": 41.93, "lon": 12.46, "surface": "Clay", "capacity": 10500, "founded": 1930, "type": "Masters 1000"},
    {"name": "Canadian Open", "venue": "IGA Stadium", "city": "Montreal", "country": "Canada", "lat": 45.53, "lon": -73.62, "surface": "Hard", "capacity": 11815, "founded": 1881, "type": "Masters 1000"},
    {"name": "Cincinnati Masters", "venue": "Lindner Family Tennis Center", "city": "Mason", "country": "USA", "lat": 39.35, "lon": -84.31, "surface": "Hard", "capacity": 11400, "founded": 1899, "type": "Masters 1000"},
    {"name": "Shanghai Masters", "venue": "Qizhong Forest Sports City", "city": "Shanghai", "country": "China", "lat": 31.14, "lon": 121.33, "surface": "Hard", "capacity": 15000, "founded": 2009, "type": "Masters 1000"},
    {"name": "Paris Masters", "venue": "Accor Arena", "city": "Paris", "country": "France", "lat": 48.84, "lon": 2.38, "surface": "Hard (indoor)", "capacity": 15609, "founded": 1968, "type": "Masters 1000"},
    {"name": "ATP Finals", "venue": "Pala Alpitour", "city": "Turin", "country": "Italy", "lat": 45.07, "lon": 7.66, "surface": "Hard (indoor)", "capacity": 15400, "founded": 1970, "type": "ATP Finals"},
    {"name": "Davis Cup Finals", "venue": "Various", "city": "Malaga", "country": "Spain", "lat": 36.72, "lon": -4.42, "surface": "Hard (indoor)", "capacity": 12000, "founded": 1900, "type": "Team Event"},
    {"name": "Dubai Tennis Championships", "venue": "Dubai Duty Free Tennis Stadium", "city": "Dubai", "country": "UAE", "lat": 25.24, "lon": 55.30, "surface": "Hard", "capacity": 5000, "founded": 1993, "type": "ATP 500"},
    {"name": "Queen's Club Championships", "venue": "Queen's Club", "city": "London", "country": "UK", "lat": 51.49, "lon": -0.21, "surface": "Grass", "capacity": 7500, "founded": 1890, "type": "ATP 500"},
    {"name": "Halle Open", "venue": "OWL Arena", "city": "Halle", "country": "Germany", "lat": 52.06, "lon": 8.36, "surface": "Grass", "capacity": 12300, "founded": 1993, "type": "ATP 500"},
    {"name": "Brisbane International", "venue": "Queensland Tennis Centre", "city": "Brisbane", "country": "Australia", "lat": -27.54, "lon": 153.07, "surface": "Hard", "capacity": 5500, "founded": 2009, "type": "ATP 250"},
    {"name": "Rio Open", "venue": "Jockey Club Brasileiro", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.97, "lon": -43.22, "surface": "Clay", "capacity": 6200, "founded": 2014, "type": "ATP 500"},
    {"name": "China Open", "venue": "National Tennis Center", "city": "Beijing", "country": "China", "lat": 39.99, "lon": 116.39, "surface": "Hard", "capacity": 15000, "founded": 2004, "type": "ATP 500"},
    {"name": "Basel Indoors", "venue": "St. Jakobshalle", "city": "Basel", "country": "Switzerland", "lat": 47.54, "lon": 7.62, "surface": "Hard (indoor)", "capacity": 9500, "founded": 1970, "type": "ATP 500"},
    {"name": "Vienna Open", "venue": "Wiener Stadthalle", "city": "Vienna", "country": "Austria", "lat": 48.20, "lon": 16.33, "surface": "Hard (indoor)", "capacity": 9000, "founded": 1974, "type": "ATP 500"},
    {"name": "Stockholm Open", "venue": "Kungliga Tennishallen", "city": "Stockholm", "country": "Sweden", "lat": 59.35, "lon": 18.08, "surface": "Hard (indoor)", "capacity": 4000, "founded": 1969, "type": "ATP 250"},
]

# =====================================================================
# 5. WORLD MARATHONS DATA
# =====================================================================
WORLD_MARATHONS = [
    {"name": "Boston Marathon", "city": "Boston", "country": "USA", "lat": 42.35, "lon": -71.06, "record": "2:03:02", "record_holder": "Geoffrey Mutai", "elevation_m": -137, "participants": 30000, "founded": 1897},
    {"name": "London Marathon", "city": "London", "country": "UK", "lat": 51.50, "lon": -0.08, "record": "2:01:25", "record_holder": "Kelvin Kiptum", "elevation_m": 30, "participants": 50000, "founded": 1981},
    {"name": "Berlin Marathon", "city": "Berlin", "country": "Germany", "lat": 52.51, "lon": 13.38, "record": "2:00:35", "record_holder": "Kelvin Kiptum", "elevation_m": 20, "participants": 45000, "founded": 1974},
    {"name": "Chicago Marathon", "city": "Chicago", "country": "USA", "lat": 41.88, "lon": -87.63, "record": "2:03:45", "record_holder": "Kelvin Kiptum", "elevation_m": 10, "participants": 47000, "founded": 1977},
    {"name": "New York City Marathon", "city": "New York", "country": "USA", "lat": 40.71, "lon": -74.01, "record": "2:05:06", "record_holder": "Geoffrey Mutai", "elevation_m": 85, "participants": 53000, "founded": 1970},
    {"name": "Tokyo Marathon", "city": "Tokyo", "country": "Japan", "lat": 35.68, "lon": 139.69, "record": "2:02:16", "record_holder": "Eliud Kipchoge", "elevation_m": 30, "participants": 38000, "founded": 2007},
    {"name": "Paris Marathon", "city": "Paris", "country": "France", "lat": 48.87, "lon": 2.30, "record": "2:04:21", "record_holder": "Elisha Rotich", "elevation_m": 50, "participants": 50000, "founded": 1976},
    {"name": "Dubai Marathon", "city": "Dubai", "country": "UAE", "lat": 25.20, "lon": 55.27, "record": "2:03:34", "record_holder": "Haile Gebrselassie", "elevation_m": 5, "participants": 30000, "founded": 2000},
    {"name": "Seoul Marathon", "city": "Seoul", "country": "South Korea", "lat": 37.57, "lon": 126.98, "record": "2:05:13", "record_holder": "Wilson Loyanae", "elevation_m": 40, "participants": 25000, "founded": 1931},
    {"name": "Sydney Marathon", "city": "Sydney", "country": "Australia", "lat": -33.86, "lon": 151.21, "record": "2:07:31", "record_holder": "Lemi Berhanu", "elevation_m": 55, "participants": 20000, "founded": 2000},
    {"name": "Amsterdam Marathon", "city": "Amsterdam", "country": "Netherlands", "lat": 52.37, "lon": 4.90, "record": "2:03:36", "record_holder": "Tamirat Tola", "elevation_m": 5, "participants": 20000, "founded": 1975},
    {"name": "Rotterdam Marathon", "city": "Rotterdam", "country": "Netherlands", "lat": 51.92, "lon": 4.48, "record": "2:04:27", "record_holder": "Marius Kipserem", "elevation_m": 3, "participants": 15000, "founded": 1981},
    {"name": "Rome Marathon", "city": "Rome", "country": "Italy", "lat": 41.90, "lon": 12.49, "record": "2:07:17", "record_holder": "Benjamin Kiptoo", "elevation_m": 40, "participants": 15000, "founded": 1995},
    {"name": "Valencia Marathon", "city": "Valencia", "country": "Spain", "lat": 39.47, "lon": -0.38, "record": "2:01:53", "record_holder": "Kelvin Kiptum", "elevation_m": 10, "participants": 30000, "founded": 1981},
    {"name": "Mumbai Marathon", "city": "Mumbai", "country": "India", "lat": 18.93, "lon": 72.83, "record": "2:08:35", "record_holder": "Abera Kuma", "elevation_m": 15, "participants": 55000, "founded": 2004},
    {"name": "Athens Marathon", "city": "Athens", "country": "Greece", "lat": 37.97, "lon": 23.73, "record": "2:10:10", "record_holder": "Felix Kandie", "elevation_m": 200, "participants": 20000, "founded": 1972},
    {"name": "Comrades Marathon", "city": "Durban", "country": "South Africa", "lat": -29.86, "lon": 31.02, "record": "5:18:19", "record_holder": "David Gatebe", "elevation_m": 800, "participants": 25000, "founded": 1921},
    {"name": "Honolulu Marathon", "city": "Honolulu", "country": "USA", "lat": 21.28, "lon": -157.82, "record": "2:07:59", "record_holder": "Jimmy Muindi", "elevation_m": 60, "participants": 25000, "founded": 1973},
    {"name": "Osaka Marathon", "city": "Osaka", "country": "Japan", "lat": 34.69, "lon": 135.50, "record": "2:06:13", "record_holder": "Dathan Ritzenhein", "elevation_m": 15, "participants": 32000, "founded": 2011},
    {"name": "Cape Town Marathon", "city": "Cape Town", "country": "South Africa", "lat": -33.93, "lon": 18.42, "record": "2:08:04", "record_holder": "Stephen Mokoka", "elevation_m": 50, "participants": 16000, "founded": 2014},
]

# =====================================================================
# 6. FOOTBALL STADIUMS — Overpass API region definitions
# =====================================================================
STADIUM_REGIONS = {
    "England": {"lat": 52.0, "lon": -1.0, "radius": 250000},
    "Spain": {"lat": 40.0, "lon": -3.5, "radius": 350000},
    "Germany": {"lat": 51.0, "lon": 10.0, "radius": 350000},
    "Italy": {"lat": 42.0, "lon": 12.5, "radius": 350000},
    "France": {"lat": 47.0, "lon": 2.5, "radius": 400000},
    "Brazil": {"lat": -15.0, "lon": -47.0, "radius": 600000},
    "Argentina": {"lat": -34.6, "lon": -58.5, "radius": 300000},
    "Portugal": {"lat": 39.0, "lon": -8.0, "radius": 200000},
    "Netherlands": {"lat": 52.0, "lon": 5.0, "radius": 150000},
    "Turkey": {"lat": 40.0, "lon": 32.0, "radius": 400000},
}

# =====================================================================
# 7. SKI RESORTS DATA
# =====================================================================
SKI_RESORTS = [
    {"name": "Chamonix Mont-Blanc", "country": "France", "lat": 45.92, "lon": 6.87, "vertical_m": 2807, "runs": 69, "snowfall_cm": 855, "top_elev_m": 3842},
    {"name": "Zermatt", "country": "Switzerland", "lat": 46.02, "lon": 7.75, "vertical_m": 2200, "runs": 145, "snowfall_cm": 450, "top_elev_m": 3883},
    {"name": "St. Anton am Arlberg", "country": "Austria", "lat": 47.13, "lon": 10.27, "vertical_m": 1507, "runs": 88, "snowfall_cm": 700, "top_elev_m": 2811},
    {"name": "Val d'Isere", "country": "France", "lat": 45.45, "lon": 6.98, "vertical_m": 1900, "runs": 78, "snowfall_cm": 600, "top_elev_m": 3456},
    {"name": "Verbier", "country": "Switzerland", "lat": 46.10, "lon": 7.23, "vertical_m": 1813, "runs": 82, "snowfall_cm": 530, "top_elev_m": 3330},
    {"name": "Whistler Blackcomb", "country": "Canada", "lat": 50.12, "lon": -122.95, "vertical_m": 1609, "runs": 200, "snowfall_cm": 1071, "top_elev_m": 2284},
    {"name": "Jackson Hole", "country": "USA", "lat": 43.59, "lon": -110.83, "vertical_m": 1262, "runs": 131, "snowfall_cm": 1168, "top_elev_m": 3185},
    {"name": "Aspen Snowmass", "country": "USA", "lat": 39.21, "lon": -106.95, "vertical_m": 1343, "runs": 337, "snowfall_cm": 762, "top_elev_m": 3813},
    {"name": "Vail", "country": "USA", "lat": 39.64, "lon": -106.37, "vertical_m": 1052, "runs": 195, "snowfall_cm": 889, "top_elev_m": 3527},
    {"name": "Cortina d'Ampezzo", "country": "Italy", "lat": 46.54, "lon": 12.14, "vertical_m": 1400, "runs": 120, "snowfall_cm": 500, "top_elev_m": 2930},
    {"name": "Kitzbuhel", "country": "Austria", "lat": 47.45, "lon": 12.39, "vertical_m": 1200, "runs": 57, "snowfall_cm": 500, "top_elev_m": 2000},
    {"name": "Courchevel", "country": "France", "lat": 45.42, "lon": 6.64, "vertical_m": 1500, "runs": 150, "snowfall_cm": 600, "top_elev_m": 2738},
    {"name": "Niseko", "country": "Japan", "lat": 42.86, "lon": 140.70, "vertical_m": 884, "runs": 30, "snowfall_cm": 1500, "top_elev_m": 1308},
    {"name": "Mammoth Mountain", "country": "USA", "lat": 37.63, "lon": -119.03, "vertical_m": 953, "runs": 150, "snowfall_cm": 914, "top_elev_m": 3369},
    {"name": "Telluride", "country": "USA", "lat": 37.94, "lon": -107.81, "vertical_m": 1070, "runs": 148, "snowfall_cm": 762, "top_elev_m": 3831},
    {"name": "Lech-Zurs am Arlberg", "country": "Austria", "lat": 47.21, "lon": 10.14, "vertical_m": 1300, "runs": 131, "snowfall_cm": 700, "top_elev_m": 2811},
    {"name": "Banff Sunshine", "country": "Canada", "lat": 51.07, "lon": -115.77, "vertical_m": 1070, "runs": 137, "snowfall_cm": 900, "top_elev_m": 2730},
    {"name": "Cervinia", "country": "Italy", "lat": 45.93, "lon": 7.63, "vertical_m": 1837, "runs": 73, "snowfall_cm": 400, "top_elev_m": 3480},
    {"name": "Tignes", "country": "France", "lat": 45.47, "lon": 6.91, "vertical_m": 1900, "runs": 78, "snowfall_cm": 600, "top_elev_m": 3456},
    {"name": "Grindelwald-Wengen", "country": "Switzerland", "lat": 46.62, "lon": 8.04, "vertical_m": 1400, "runs": 110, "snowfall_cm": 450, "top_elev_m": 2971},
    {"name": "Big Sky", "country": "USA", "lat": 45.28, "lon": -111.40, "vertical_m": 1330, "runs": 317, "snowfall_cm": 762, "top_elev_m": 3403},
    {"name": "Park City", "country": "USA", "lat": 40.65, "lon": -111.51, "vertical_m": 943, "runs": 330, "snowfall_cm": 889, "top_elev_m": 3048},
    {"name": "Breckenridge", "country": "USA", "lat": 39.48, "lon": -106.07, "vertical_m": 1036, "runs": 187, "snowfall_cm": 762, "top_elev_m": 3962},
    {"name": "Morzine-Avoriaz", "country": "France", "lat": 46.18, "lon": 6.71, "vertical_m": 1000, "runs": 75, "snowfall_cm": 800, "top_elev_m": 2277},
    {"name": "Innsbruck-Nordkette", "country": "Austria", "lat": 47.30, "lon": 11.39, "vertical_m": 1340, "runs": 22, "snowfall_cm": 400, "top_elev_m": 2334},
    {"name": "Lake Louise", "country": "Canada", "lat": 51.44, "lon": -116.17, "vertical_m": 1000, "runs": 145, "snowfall_cm": 365, "top_elev_m": 2637},
    {"name": "Engelberg-Titlis", "country": "Switzerland", "lat": 46.82, "lon": 8.40, "vertical_m": 2000, "runs": 36, "snowfall_cm": 700, "top_elev_m": 3028},
    {"name": "La Grave", "country": "France", "lat": 45.05, "lon": 6.30, "vertical_m": 2150, "runs": 0, "snowfall_cm": 600, "top_elev_m": 3568},
    {"name": "Revelstoke", "country": "Canada", "lat": 51.00, "lon": -118.20, "vertical_m": 1713, "runs": 69, "snowfall_cm": 1049, "top_elev_m": 2225},
    {"name": "Hakuba Valley", "country": "Japan", "lat": 36.70, "lon": 137.83, "vertical_m": 1071, "runs": 137, "snowfall_cm": 1100, "top_elev_m": 1831},
]

# =====================================================================
# 8. SURF SPOTS DATA
# =====================================================================
SURF_SPOTS = [
    {"name": "Pipeline", "location": "Oahu, Hawaii", "country": "USA", "lat": 21.66, "lon": -158.05, "wave_type": "Barrel/Reef", "best_season": "Nov-Feb", "max_height_ft": 20},
    {"name": "Teahupo'o", "location": "Tahiti", "country": "French Polynesia", "lat": -17.85, "lon": -149.26, "wave_type": "Heavy Barrel/Reef", "best_season": "May-Oct", "max_height_ft": 25},
    {"name": "Nazare", "location": "Nazare", "country": "Portugal", "lat": 39.60, "lon": -9.07, "wave_type": "Big Wave/Beach", "best_season": "Oct-Mar", "max_height_ft": 100},
    {"name": "Jaws (Pe'ahi)", "location": "Maui, Hawaii", "country": "USA", "lat": 20.94, "lon": -156.28, "wave_type": "Big Wave/Reef", "best_season": "Nov-Mar", "max_height_ft": 70},
    {"name": "Mavericks", "location": "Half Moon Bay, CA", "country": "USA", "lat": 37.49, "lon": -122.50, "wave_type": "Big Wave/Reef", "best_season": "Nov-Mar", "max_height_ft": 60},
    {"name": "Jeffrey's Bay", "location": "Eastern Cape", "country": "South Africa", "lat": -33.97, "lon": 25.97, "wave_type": "Point Break", "best_season": "Jun-Sep", "max_height_ft": 12},
    {"name": "Uluwatu", "location": "Bali", "country": "Indonesia", "lat": -8.82, "lon": 115.09, "wave_type": "Reef Break", "best_season": "Apr-Oct", "max_height_ft": 12},
    {"name": "Cloudbreak", "location": "Namotu Island", "country": "Fiji", "lat": -17.80, "lon": 177.18, "wave_type": "Reef Break", "best_season": "May-Oct", "max_height_ft": 15},
    {"name": "Hossegor", "location": "Landes", "country": "France", "lat": 43.67, "lon": -1.44, "wave_type": "Beach Break", "best_season": "Sep-Nov", "max_height_ft": 15},
    {"name": "Supertubos", "location": "Peniche", "country": "Portugal", "lat": 39.35, "lon": -9.37, "wave_type": "Beach Break", "best_season": "Sep-Dec", "max_height_ft": 12},
    {"name": "Bells Beach", "location": "Torquay, Victoria", "country": "Australia", "lat": -38.37, "lon": 144.28, "wave_type": "Point Break", "best_season": "Mar-May", "max_height_ft": 12},
    {"name": "Snapper Rocks", "location": "Gold Coast", "country": "Australia", "lat": -28.16, "lon": 153.55, "wave_type": "Point Break", "best_season": "Feb-May", "max_height_ft": 10},
    {"name": "Trestles", "location": "San Clemente, CA", "country": "USA", "lat": 33.38, "lon": -117.59, "wave_type": "Cobblestone Point", "best_season": "Jun-Oct", "max_height_ft": 8},
    {"name": "Skeleton Bay", "location": "Luderitz", "country": "Namibia", "lat": -26.65, "lon": 15.17, "wave_type": "Sand Bottom Barrel", "best_season": "Jun-Sep", "max_height_ft": 8},
    {"name": "Mundaka", "location": "Basque Country", "country": "Spain", "lat": 43.41, "lon": -2.70, "wave_type": "River Mouth Barrel", "best_season": "Sep-Dec", "max_height_ft": 12},
    {"name": "Chicama", "location": "La Libertad", "country": "Peru", "lat": -7.84, "lon": -79.45, "wave_type": "Long Left Point", "best_season": "Mar-Oct", "max_height_ft": 8},
    {"name": "G-Land", "location": "East Java", "country": "Indonesia", "lat": -8.73, "lon": 114.37, "wave_type": "Reef Break", "best_season": "Apr-Oct", "max_height_ft": 15},
    {"name": "Raglan", "location": "Waikato", "country": "New Zealand", "lat": -37.81, "lon": 174.87, "wave_type": "Left Point Break", "best_season": "Mar-Aug", "max_height_ft": 10},
    {"name": "Punta de Lobos", "location": "Pichilemu", "country": "Chile", "lat": -34.43, "lon": -72.05, "wave_type": "Left Point Break", "best_season": "Apr-Sep", "max_height_ft": 20},
    {"name": "Thurso East", "location": "Caithness", "country": "Scotland", "lat": 58.60, "lon": -3.53, "wave_type": "Reef Break", "best_season": "Oct-Mar", "max_height_ft": 12},
    {"name": "Puerto Escondido", "location": "Oaxaca", "country": "Mexico", "lat": 15.86, "lon": -97.07, "wave_type": "Beach Break Barrel", "best_season": "May-Aug", "max_height_ft": 18},
    {"name": "Ericeira", "location": "Lisbon coast", "country": "Portugal", "lat": 38.96, "lon": -9.42, "wave_type": "Reef/Point Mix", "best_season": "Sep-Mar", "max_height_ft": 10},
    {"name": "Siargao (Cloud 9)", "location": "Siargao Island", "country": "Philippines", "lat": 9.80, "lon": 126.17, "wave_type": "Reef Break", "best_season": "Aug-Nov", "max_height_ft": 10},
    {"name": "Santa Cruz", "location": "California", "country": "USA", "lat": 36.96, "lon": -122.03, "wave_type": "Various", "best_season": "Nov-Mar", "max_height_ft": 25},
    {"name": "Taghazout", "location": "Agadir region", "country": "Morocco", "lat": 30.54, "lon": -9.71, "wave_type": "Point Break", "best_season": "Oct-Mar", "max_height_ft": 10},
]

# =====================================================================
# 9. CYCLING CLIMBS DATA (Tour/Giro/Vuelta)
# =====================================================================
CYCLING_CLIMBS = [
    {"name": "Alpe d'Huez", "race": "Tour de France", "country": "France", "lat": 45.09, "lon": 6.07, "altitude_m": 1850, "length_km": 13.8, "gradient_pct": 8.1, "category": "HC"},
    {"name": "Col du Tourmalet", "race": "Tour de France", "country": "France", "lat": 42.91, "lon": 0.15, "altitude_m": 2115, "length_km": 17.1, "gradient_pct": 7.3, "category": "HC"},
    {"name": "Mont Ventoux", "race": "Tour de France", "country": "France", "lat": 44.17, "lon": 5.28, "altitude_m": 1909, "length_km": 21.5, "gradient_pct": 7.5, "category": "HC"},
    {"name": "Col du Galibier", "race": "Tour de France", "country": "France", "lat": 45.06, "lon": 6.41, "altitude_m": 2642, "length_km": 17.7, "gradient_pct": 6.9, "category": "HC"},
    {"name": "Col d'Aubisque", "race": "Tour de France", "country": "France", "lat": 42.97, "lon": -0.34, "altitude_m": 1709, "length_km": 16.6, "gradient_pct": 7.2, "category": "HC"},
    {"name": "Stelvio Pass", "race": "Giro d'Italia", "country": "Italy", "lat": 46.53, "lon": 10.45, "altitude_m": 2758, "length_km": 24.3, "gradient_pct": 7.4, "category": "HC"},
    {"name": "Mortirolo", "race": "Giro d'Italia", "country": "Italy", "lat": 46.25, "lon": 10.30, "altitude_m": 1852, "length_km": 12.4, "gradient_pct": 10.5, "category": "HC"},
    {"name": "Passo del Zoncolan", "race": "Giro d'Italia", "country": "Italy", "lat": 46.49, "lon": 12.93, "altitude_m": 1730, "length_km": 10.1, "gradient_pct": 11.5, "category": "HC"},
    {"name": "Monte Zoncolan (Ovaro)", "race": "Giro d'Italia", "country": "Italy", "lat": 46.48, "lon": 12.94, "altitude_m": 1730, "length_km": 10.5, "gradient_pct": 11.9, "category": "HC"},
    {"name": "Passo Gavia", "race": "Giro d'Italia", "country": "Italy", "lat": 46.34, "lon": 10.49, "altitude_m": 2621, "length_km": 16.5, "gradient_pct": 7.9, "category": "HC"},
    {"name": "Angliru", "race": "Vuelta a Espana", "country": "Spain", "lat": 43.21, "lon": -5.93, "altitude_m": 1570, "length_km": 12.5, "gradient_pct": 10.1, "category": "HC"},
    {"name": "Lagos de Covadonga", "race": "Vuelta a Espana", "country": "Spain", "lat": 43.27, "lon": -4.98, "altitude_m": 1134, "length_km": 12.6, "gradient_pct": 6.9, "category": "1"},
    {"name": "Alto de l'Angliru", "race": "Vuelta a Espana", "country": "Spain", "lat": 43.22, "lon": -5.94, "altitude_m": 1573, "length_km": 12.2, "gradient_pct": 9.8, "category": "HC"},
    {"name": "La Planche des Belles Filles", "race": "Tour de France", "country": "France", "lat": 47.77, "lon": 6.78, "altitude_m": 1148, "length_km": 7.0, "gradient_pct": 8.5, "category": "1"},
    {"name": "Col de la Madeleine", "race": "Tour de France", "country": "France", "lat": 45.44, "lon": 6.38, "altitude_m": 2000, "length_km": 19.2, "gradient_pct": 8.0, "category": "HC"},
    {"name": "Col d'Izoard", "race": "Tour de France", "country": "France", "lat": 44.82, "lon": 6.73, "altitude_m": 2360, "length_km": 14.1, "gradient_pct": 7.3, "category": "HC"},
    {"name": "Passo Fedaia (Marmolada)", "race": "Giro d'Italia", "country": "Italy", "lat": 46.46, "lon": 11.87, "altitude_m": 2057, "length_km": 14.0, "gradient_pct": 7.6, "category": "HC"},
    {"name": "Plan de Corones", "race": "Giro d'Italia", "country": "Italy", "lat": 46.74, "lon": 11.95, "altitude_m": 2275, "length_km": 3.5, "gradient_pct": 14.0, "category": "1"},
    {"name": "Col du Portet", "race": "Tour de France", "country": "France", "lat": 42.80, "lon": 0.38, "altitude_m": 2215, "length_km": 16.0, "gradient_pct": 8.7, "category": "HC"},
    {"name": "Blockhaus", "race": "Giro d'Italia", "country": "Italy", "lat": 42.14, "lon": 14.10, "altitude_m": 1665, "length_km": 13.6, "gradient_pct": 8.4, "category": "1"},
    {"name": "Alto de Velefique", "race": "Vuelta a Espana", "country": "Spain", "lat": 37.24, "lon": -2.39, "altitude_m": 1820, "length_km": 13.2, "gradient_pct": 7.6, "category": "HC"},
    {"name": "Puerto de Navacerrada", "race": "Vuelta a Espana", "country": "Spain", "lat": 40.78, "lon": -4.01, "altitude_m": 1858, "length_km": 12.8, "gradient_pct": 6.0, "category": "1"},
    {"name": "Col de Vars", "race": "Tour de France", "country": "France", "lat": 44.54, "lon": 6.70, "altitude_m": 2108, "length_km": 9.9, "gradient_pct": 7.5, "category": "1"},
    {"name": "Passo dello Spluga", "race": "Giro d'Italia", "country": "Italy/Switz.", "lat": 46.51, "lon": 9.33, "altitude_m": 2113, "length_km": 12.0, "gradient_pct": 6.9, "category": "1"},
    {"name": "Sierra de la Pandera", "race": "Vuelta a Espana", "country": "Spain", "lat": 37.71, "lon": -3.79, "altitude_m": 1830, "length_km": 11.0, "gradient_pct": 8.0, "category": "HC"},
]

# =====================================================================
# 10. MOTORSPORT CIRCUITS DATA
# =====================================================================
MOTORSPORT_CIRCUITS = [
    {"name": "Circuit de la Sarthe (Le Mans)", "location": "Le Mans, France", "lat": 47.96, "lon": 0.21, "length_km": 13.626, "type": "Endurance", "first_race": 1923, "famous_event": "24 Hours of Le Mans"},
    {"name": "Nurburgring Nordschleife", "location": "Nurburg, Germany", "lat": 50.33, "lon": 6.94, "length_km": 20.832, "type": "Road Circuit", "first_race": 1927, "famous_event": "ADAC 24h Race"},
    {"name": "Daytona International Speedway", "location": "Daytona Beach, USA", "lat": 29.19, "lon": -81.07, "length_km": 4.023, "type": "Oval/Road", "first_race": 1959, "famous_event": "Daytona 500"},
    {"name": "Indianapolis Motor Speedway", "location": "Indianapolis, USA", "lat": 39.79, "lon": -86.24, "length_km": 4.023, "type": "Oval", "first_race": 1909, "famous_event": "Indianapolis 500"},
    {"name": "Spa-Francorchamps", "location": "Stavelot, Belgium", "lat": 50.44, "lon": 5.97, "length_km": 7.004, "type": "Road Circuit", "first_race": 1925, "famous_event": "24H of Spa / Belgian GP"},
    {"name": "Mount Panorama (Bathurst)", "location": "Bathurst, Australia", "lat": -33.45, "lon": 149.56, "length_km": 6.213, "type": "Street/Hill", "first_race": 1938, "famous_event": "Bathurst 1000"},
    {"name": "Laguna Seca", "location": "Monterey, USA", "lat": 36.58, "lon": -121.75, "length_km": 3.602, "type": "Road Circuit", "first_race": 1957, "famous_event": "WSBK / MotoGP races"},
    {"name": "Mugello Circuit", "location": "Scarperia, Italy", "lat": 43.99, "lon": 11.37, "length_km": 5.245, "type": "Road Circuit", "first_race": 1974, "famous_event": "Italian MotoGP"},
    {"name": "Phillip Island Grand Prix Circuit", "location": "Phillip Island, Australia", "lat": -38.50, "lon": 145.23, "length_km": 4.448, "type": "Road Circuit", "first_race": 1956, "famous_event": "Australian MotoGP"},
    {"name": "Isle of Man TT Course", "location": "Isle of Man, UK", "lat": 54.17, "lon": -4.51, "length_km": 60.725, "type": "Public Road", "first_race": 1907, "famous_event": "Isle of Man TT"},
    {"name": "Sebring International Raceway", "location": "Sebring, USA", "lat": 27.45, "lon": -81.35, "length_km": 6.019, "type": "Road Circuit", "first_race": 1950, "famous_event": "12 Hours of Sebring"},
    {"name": "Watkins Glen International", "location": "Watkins Glen, USA", "lat": 42.34, "lon": -76.93, "length_km": 5.430, "type": "Road Circuit", "first_race": 1948, "famous_event": "6 Hours of Watkins Glen"},
    {"name": "Circuit de Catalunya", "location": "Barcelona, Spain", "lat": 41.57, "lon": 2.26, "length_km": 4.657, "type": "Road Circuit", "first_race": 1991, "famous_event": "Spanish GP / MotoGP"},
    {"name": "Fuji Speedway", "location": "Oyama, Japan", "lat": 35.37, "lon": 138.93, "length_km": 4.563, "type": "Road Circuit", "first_race": 1966, "famous_event": "WEC 6H Fuji"},
    {"name": "Brands Hatch", "location": "Fawkham, UK", "lat": 51.36, "lon": 0.26, "length_km": 3.908, "type": "Road Circuit", "first_race": 1950, "famous_event": "British GP (historic)"},
    {"name": "Road America", "location": "Elkhart Lake, USA", "lat": 43.80, "lon": -87.99, "length_km": 6.515, "type": "Road Circuit", "first_race": 1955, "famous_event": "IMSA SportsCar Weekend"},
    {"name": "Hockenheimring", "location": "Hockenheim, Germany", "lat": 49.33, "lon": 8.57, "length_km": 4.574, "type": "Road Circuit", "first_race": 1932, "famous_event": "German GP (historic)"},
    {"name": "Autodromo di Monza", "location": "Monza, Italy", "lat": 45.62, "lon": 9.29, "length_km": 5.793, "type": "Road Circuit", "first_race": 1922, "famous_event": "Italian GP"},
    {"name": "Interlagos (Autodromo Jose Carlos Pace)", "location": "Sao Paulo, Brazil", "lat": -23.70, "lon": -46.70, "length_km": 4.309, "type": "Road Circuit", "first_race": 1940, "famous_event": "Brazilian GP"},
    {"name": "Buddh International Circuit", "location": "Greater Noida, India", "lat": 28.35, "lon": 77.53, "length_km": 5.125, "type": "Road Circuit", "first_race": 2011, "famous_event": "Indian GP (2011-2013)"},
    {"name": "Tsukuba Circuit", "location": "Shimotsuma, Japan", "lat": 36.16, "lon": 140.01, "length_km": 2.070, "type": "Road Circuit", "first_race": 1970, "famous_event": "Super GT / Time Attack"},
    {"name": "Imola (Autodromo Enzo e Dino Ferrari)", "location": "Imola, Italy", "lat": 44.34, "lon": 11.71, "length_km": 4.909, "type": "Road Circuit", "first_race": 1953, "famous_event": "Emilia-Romagna GP"},
    {"name": "Sepang International Circuit", "location": "Sepang, Malaysia", "lat": 2.76, "lon": 101.74, "length_km": 5.543, "type": "Road Circuit", "first_race": 1999, "famous_event": "Malaysian GP / MotoGP"},
    {"name": "Circuit of Zolder", "location": "Heusden-Zolder, Belgium", "lat": 50.99, "lon": 5.26, "length_km": 4.011, "type": "Road Circuit", "first_race": 1963, "famous_event": "Belgian GP (historic)"},
    {"name": "Portimao (Algarve International Circuit)", "location": "Portimao, Portugal", "lat": 37.23, "lon": -8.63, "length_km": 4.653, "type": "Road Circuit", "first_race": 2008, "famous_event": "Portuguese GP"},
]


# =====================================================================
# DATA FETCH / CACHE FUNCTIONS
# =====================================================================
@st.cache_data(ttl=3600)
def get_olympic_data() -> pd.DataFrame:
    """Combine Summer + Winter Olympics into a single DataFrame."""
    rows = []
    for o in SUMMER_OLYMPICS:
        rows.append({
            "Year": o["year"], "Season": "Summer", "City": o["city"],
            "Country": o["country"], "Notable": o["notable"],
            "Lat": o["lat"], "Lon": o["lon"],
        })
    for o in WINTER_OLYMPICS:
        rows.append({
            "Year": o["year"], "Season": "Winter", "City": o["city"],
            "Country": o["country"], "Notable": o["notable"],
            "Lat": o["lat"], "Lon": o["lon"],
        })
    return pd.DataFrame(rows).sort_values("Year").reset_index(drop=True)


@st.cache_data(ttl=3600)
def get_fifa_data() -> pd.DataFrame:
    rows = []
    for wc in FIFA_WORLD_CUPS:
        rows.append({
            "Year": wc["year"], "Host": wc["host"], "Winner": wc["winner"],
            "Runner-Up": wc["runner_up"], "Final Venue": wc["venue"],
            "Lat": wc["lat"], "Lon": wc["lon"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_f1_data() -> pd.DataFrame:
    rows = []
    for c in F1_CIRCUITS:
        rows.append({
            "Circuit": c["name"], "Location": c["location"],
            "Length (km)": c["length_km"], "Lap Record": c["lap_record"],
            "First GP": c["first_gp"], "Lat": c["lat"], "Lon": c["lon"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_tennis_data() -> pd.DataFrame:
    rows = []
    for v in TENNIS_VENUES:
        rows.append({
            "Tournament": v["name"], "Venue": v["venue"], "City": v["city"],
            "Country": v["country"], "Surface": v["surface"],
            "Capacity": v["capacity"], "Founded": v["founded"],
            "Type": v["type"], "Lat": v["lat"], "Lon": v["lon"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_marathon_data() -> pd.DataFrame:
    rows = []
    for m in WORLD_MARATHONS:
        rows.append({
            "Marathon": m["name"], "City": m["city"], "Country": m["country"],
            "Record": m["record"], "Record Holder": m["record_holder"],
            "Elevation (m)": m["elevation_m"],
            "Participants": m["participants"], "Founded": m["founded"],
            "Lat": m["lat"], "Lon": m["lon"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def fetch_football_stadiums(region: str) -> list[dict]:
    """Fetch football/soccer stadiums from Overpass API in a given region."""
    cfg = STADIUM_REGIONS[region]
    query = f"""
    [out:json][timeout:60];
    (
      node["leisure"="stadium"]["sport"="soccer"](around:{cfg['radius']},{cfg['lat']},{cfg['lon']});
      way["leisure"="stadium"]["sport"="soccer"](around:{cfg['radius']},{cfg['lat']},{cfg['lon']});
      relation["leisure"="stadium"]["sport"="soccer"](around:{cfg['radius']},{cfg['lat']},{cfg['lon']});
    );
    out center 200;
    """
    data = query_overpass(query)
    if data is None or "_error" in data:
        return []
    stadiums = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat and lon:
            stadiums.append({
                "name": tags.get("name", "Unknown Stadium"),
                "capacity": tags.get("capacity", "N/A"),
                "sport": tags.get("sport", "soccer"),
                "operator": tags.get("operator", "N/A"),
                "lat": lat,
                "lon": lon,
            })
    return stadiums


@st.cache_data(ttl=3600)
def get_ski_data() -> pd.DataFrame:
    rows = []
    for s in SKI_RESORTS:
        rows.append({
            "Resort": s["name"], "Country": s["country"],
            "Vertical Drop (m)": s["vertical_m"], "Runs": s["runs"],
            "Snowfall (cm)": s["snowfall_cm"],
            "Top Elevation (m)": s["top_elev_m"],
            "Lat": s["lat"], "Lon": s["lon"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_surf_data() -> pd.DataFrame:
    rows = []
    for s in SURF_SPOTS:
        rows.append({
            "Spot": s["name"], "Location": s["location"],
            "Country": s["country"], "Wave Type": s["wave_type"],
            "Best Season": s["best_season"],
            "Max Height (ft)": s["max_height_ft"],
            "Lat": s["lat"], "Lon": s["lon"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_cycling_data() -> pd.DataFrame:
    rows = []
    for c in CYCLING_CLIMBS:
        rows.append({
            "Climb": c["name"], "Race": c["race"], "Country": c["country"],
            "Altitude (m)": c["altitude_m"], "Length (km)": c["length_km"],
            "Gradient (%)": c["gradient_pct"], "Category": c["category"],
            "Lat": c["lat"], "Lon": c["lon"],
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def get_motorsport_data() -> pd.DataFrame:
    rows = []
    for c in MOTORSPORT_CIRCUITS:
        rows.append({
            "Circuit": c["name"], "Location": c["location"],
            "Length (km)": c["length_km"], "Type": c["type"],
            "First Race": c["first_race"], "Famous Event": c["famous_event"],
            "Lat": c["lat"], "Lon": c["lon"],
        })
    return pd.DataFrame(rows)


# =====================================================================
# CHART BUILDERS
# =====================================================================
def _build_olympics_chart(df: pd.DataFrame):
    """Bar chart of Olympics by country."""
    counts = df.groupby("Country").size().sort_values(ascending=True).tail(15)
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(SURFACE)
    ax.barh(counts.index, counts.values, color=ACCENT, edgecolor=DARK_BG)
    ax.set_xlabel("Times Hosted", color=TEXT_PRIMARY)
    ax.set_title("Top Olympic Host Countries", color=TEXT_PRIMARY, fontsize=14)
    ax.tick_params(colors=TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(SURFACE)
    plt.tight_layout()
    return fig


def _build_fifa_winners_chart():
    """Horizontal bar chart of FIFA World Cup wins by country."""
    from collections import Counter
    wins = Counter(wc["winner"] for wc in FIFA_WORLD_CUPS if wc["winner"] != "TBD")
    sorted_wins = sorted(wins.items(), key=lambda x: x[1])
    countries = [x[0] for x in sorted_wins]
    counts = [x[1] for x in sorted_wins]
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(SURFACE)
    ax.barh(countries, counts, color="#f59e0b", edgecolor=DARK_BG)
    ax.set_xlabel("World Cup Wins", color=TEXT_PRIMARY)
    ax.set_title("FIFA World Cup Winners", color=TEXT_PRIMARY, fontsize=14)
    ax.tick_params(colors=TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(SURFACE)
    plt.tight_layout()
    return fig


def _build_marathon_chart():
    """Bar chart of fastest marathon records."""
    sorted_m = sorted(WORLD_MARATHONS, key=lambda x: x["record"])[:12]
    names = [m["name"].replace(" Marathon", "") for m in sorted_m]
    records = [m["record"] for m in sorted_m]
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(SURFACE)
    ax.barh(names, range(len(names)), color="#10b981", edgecolor=DARK_BG)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([f"{n} ({r})" for n, r in zip(names, records)])
    ax.set_xlabel("Rank (fastest first)", color=TEXT_PRIMARY)
    ax.set_title("Fastest Marathon Courses (by Record)", color=TEXT_PRIMARY, fontsize=14)
    ax.tick_params(colors=TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(SURFACE)
    plt.tight_layout()
    return fig


def _build_cycling_gradient_chart():
    """Bar chart of steepest cycling climbs by gradient."""
    sorted_c = sorted(CYCLING_CLIMBS, key=lambda x: x["gradient_pct"], reverse=True)[:15]
    names = [c["name"] for c in sorted_c]
    grads = [c["gradient_pct"] for c in sorted_c]
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(SURFACE)
    ax.barh(names[::-1], grads[::-1], color="#ef4444", edgecolor=DARK_BG)
    ax.set_xlabel("Average Gradient (%)", color=TEXT_PRIMARY)
    ax.set_title("Steepest Cycling Climbs", color=TEXT_PRIMARY, fontsize=14)
    ax.tick_params(colors=TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(SURFACE)
    plt.tight_layout()
    return fig


def _build_ski_vertical_chart():
    """Bar chart of ski resorts by vertical drop."""
    sorted_s = sorted(SKI_RESORTS, key=lambda x: x["vertical_m"], reverse=True)[:15]
    names = [s["name"] for s in sorted_s]
    verts = [s["vertical_m"] for s in sorted_s]
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(DARK_BG)
    ax.set_facecolor(SURFACE)
    ax.barh(names[::-1], verts[::-1], color="#3b82f6", edgecolor=DARK_BG)
    ax.set_xlabel("Vertical Drop (m)", color=TEXT_PRIMARY)
    ax.set_title("Ski Resorts by Vertical Drop", color=TEXT_PRIMARY, fontsize=14)
    ax.tick_params(colors=TEXT_SECONDARY)
    for spine in ax.spines.values():
        spine.set_color(SURFACE)
    plt.tight_layout()
    return fig


# =====================================================================
# MAP BUILDER FUNCTIONS
# =====================================================================
def _build_olympics_map(df: pd.DataFrame) -> folium.Map:
    fmap = folium.Map(location=[30, 0], zoom_start=2,
                      tiles="CartoDB dark_matter")
    cluster = MarkerCluster().add_to(fmap)
    for _, row in df.iterrows():
        color = "blue" if row["Season"] == "Summer" else "lightblue"
        icon_name = "sun-o" if row["Season"] == "Summer" else "snowflake-o"
        popup_html = (
            f"<b>{escape(str(row['Year']))} {escape(row['Season'])} Olympics</b><br>"
            f"City: {escape(row['City'])}, {escape(row['Country'])}<br>"
            f"Notable: {escape(row['Notable'])}"
        )
        folium.Marker(
            location=[row["Lat"], row["Lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(color=color, icon=icon_name, prefix="fa"),
        ).add_to(cluster)
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
    background:rgba(15,23,42,0.85);padding:10px 14px;border-radius:8px;
    border:1px solid #2a3550;font-size:13px;color:#e8ecf4;">
    <b>Olympics</b><br>
    <span style="color:#3b82f6;">&#9679;</span> Summer<br>
    <span style="color:#87ceeb;">&#9679;</span> Winter
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))
    return fmap


def _build_fifa_map() -> folium.Map:
    fmap = folium.Map(location=[20, 0], zoom_start=2,
                      tiles="CartoDB dark_matter")
    for wc in FIFA_WORLD_CUPS:
        popup_html = (
            f"<b>{escape(str(wc['year']))} FIFA World Cup</b><br>"
            f"Host: {escape(wc['host'])}<br>"
            f"Winner: {escape(wc['winner'])}<br>"
            f"Runner-Up: {escape(wc['runner_up'])}<br>"
            f"Final: {escape(wc['venue'])}"
        )
        folium.CircleMarker(
            location=[wc["lat"], wc["lon"]],
            radius=8, color="#f59e0b", fill=True,
            fill_color="#f59e0b", fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(fmap)
    return fmap


def _build_f1_map() -> folium.Map:
    fmap = folium.Map(location=[25, 10], zoom_start=2,
                      tiles="CartoDB dark_matter")
    for c in F1_CIRCUITS:
        popup_html = (
            f"<b>{escape(c['name'])}</b><br>"
            f"Location: {escape(c['location'])}<br>"
            f"Length: {c['length_km']} km<br>"
            f"Lap Record: {escape(c['lap_record'])}<br>"
            f"First GP: {c['first_gp']}"
        )
        folium.Marker(
            location=[c["lat"], c["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(color="red", icon="flag-checkered", prefix="fa"),
        ).add_to(fmap)
    return fmap


def _build_tennis_map() -> folium.Map:
    fmap = folium.Map(location=[30, 0], zoom_start=2,
                      tiles="CartoDB dark_matter")
    type_colors = {
        "Grand Slam": "green", "Masters 1000": "orange",
        "ATP Finals": "purple", "Team Event": "blue",
        "ATP 500": "cadetblue", "ATP 250": "lightgray",
    }
    for v in TENNIS_VENUES:
        color = type_colors.get(v["type"], "gray")
        popup_html = (
            f"<b>{escape(v['name'])}</b><br>"
            f"Venue: {escape(v['venue'])}<br>"
            f"City: {escape(v['city'])}, {escape(v['country'])}<br>"
            f"Surface: {escape(v['surface'])}<br>"
            f"Capacity: {v['capacity']:,}<br>"
            f"Founded: {v['founded']}"
        )
        folium.Marker(
            location=[v["lat"], v["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(color=color, icon="trophy", prefix="fa"),
        ).add_to(fmap)
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
    background:rgba(15,23,42,0.85);padding:10px 14px;border-radius:8px;
    border:1px solid #2a3550;font-size:13px;color:#e8ecf4;">
    <b>Tournament Type</b><br>
    <span style="color:#28a745;">&#9679;</span> Grand Slam<br>
    <span style="color:#f0ad4e;">&#9679;</span> Masters 1000<br>
    <span style="color:#6f42c1;">&#9679;</span> ATP Finals<br>
    <span style="color:#17a2b8;">&#9679;</span> ATP 500<br>
    <span style="color:#6c757d;">&#9679;</span> ATP 250
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))
    return fmap


def _build_marathon_map() -> folium.Map:
    fmap = folium.Map(location=[30, 0], zoom_start=2,
                      tiles="CartoDB dark_matter")
    max_p = max(m["participants"] for m in WORLD_MARATHONS)
    for m in WORLD_MARATHONS:
        radius = max(6, (m["participants"] / max_p) * 18)
        popup_html = (
            f"<b>{escape(m['name'])}</b><br>"
            f"City: {escape(m['city'])}, {escape(m['country'])}<br>"
            f"Record: {escape(m['record'])} ({escape(m['record_holder'])})<br>"
            f"Participants: ~{m['participants']:,}<br>"
            f"Founded: {m['founded']}"
        )
        folium.CircleMarker(
            location=[m["lat"], m["lon"]],
            radius=radius, color="#10b981", fill=True,
            fill_color="#10b981", fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(fmap)
    return fmap


def _build_stadium_map(stadiums: list[dict]) -> folium.Map:
    if not stadiums:
        return folium.Map(location=[45, 0], zoom_start=4,
                          tiles="CartoDB dark_matter")
    avg_lat = sum(s["lat"] for s in stadiums) / len(stadiums)
    avg_lon = sum(s["lon"] for s in stadiums) / len(stadiums)
    fmap = folium.Map(location=[avg_lat, avg_lon], zoom_start=6,
                      tiles="CartoDB dark_matter")
    cluster = MarkerCluster().add_to(fmap)
    for s in stadiums:
        popup_html = (
            f"<b>{escape(s['name'])}</b><br>"
            f"Capacity: {escape(str(s['capacity']))}<br>"
            f"Operator: {escape(s['operator'])}"
        )
        folium.Marker(
            location=[s["lat"], s["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color="green", icon="futbol-o", prefix="fa"),
        ).add_to(cluster)
    return fmap


def _build_ski_map() -> folium.Map:
    fmap = folium.Map(location=[47, 10], zoom_start=3,
                      tiles="CartoDB dark_matter")
    for s in SKI_RESORTS:
        popup_html = (
            f"<b>{escape(s['name'])}</b><br>"
            f"Country: {escape(s['country'])}<br>"
            f"Vertical Drop: {s['vertical_m']}m<br>"
            f"Runs: {s['runs']}<br>"
            f"Annual Snowfall: {s['snowfall_cm']}cm<br>"
            f"Top Elevation: {s['top_elev_m']}m"
        )
        folium.Marker(
            location=[s["lat"], s["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(color="lightblue", icon="snowflake-o", prefix="fa"),
        ).add_to(fmap)
    return fmap


def _build_surf_map() -> folium.Map:
    fmap = folium.Map(location=[10, 0], zoom_start=2,
                      tiles="CartoDB dark_matter")
    for s in SURF_SPOTS:
        popup_html = (
            f"<b>{escape(s['name'])}</b><br>"
            f"Location: {escape(s['location'])}, {escape(s['country'])}<br>"
            f"Wave Type: {escape(s['wave_type'])}<br>"
            f"Best Season: {escape(s['best_season'])}<br>"
            f"Max Height: {s['max_height_ft']}ft"
        )
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=max(5, s["max_height_ft"] / 5),
            color="#06b6d4", fill=True,
            fill_color="#06b6d4", fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(fmap)
    return fmap


def _build_cycling_map() -> folium.Map:
    fmap = folium.Map(location=[45, 6], zoom_start=5,
                      tiles="CartoDB dark_matter")
    race_colors = {
        "Tour de France": "#f59e0b",
        "Giro d'Italia": "#ec4899",
        "Vuelta a Espana": "#ef4444",
    }
    for c in CYCLING_CLIMBS:
        color = race_colors.get(c["race"], "#8b97b0")
        popup_html = (
            f"<b>{escape(c['name'])}</b><br>"
            f"Race: {escape(c['race'])}<br>"
            f"Altitude: {c['altitude_m']}m<br>"
            f"Length: {c['length_km']}km<br>"
            f"Gradient: {c['gradient_pct']}%<br>"
            f"Category: {escape(c['category'])}"
        )
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=max(5, c["gradient_pct"]),
            color=color, fill=True,
            fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=280),
        ).add_to(fmap)
    legend_html = """
    <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
    background:rgba(15,23,42,0.85);padding:10px 14px;border-radius:8px;
    border:1px solid #2a3550;font-size:13px;color:#e8ecf4;">
    <b>Grand Tour</b><br>
    <span style="color:#f59e0b;">&#9679;</span> Tour de France<br>
    <span style="color:#ec4899;">&#9679;</span> Giro d'Italia<br>
    <span style="color:#ef4444;">&#9679;</span> Vuelta a Espana
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))
    return fmap


def _build_motorsport_map() -> folium.Map:
    fmap = folium.Map(location=[30, 0], zoom_start=2,
                      tiles="CartoDB dark_matter")
    for c in MOTORSPORT_CIRCUITS:
        popup_html = (
            f"<b>{escape(c['name'])}</b><br>"
            f"Location: {escape(c['location'])}<br>"
            f"Length: {c['length_km']} km<br>"
            f"Type: {escape(c['type'])}<br>"
            f"First Race: {c['first_race']}<br>"
            f"Famous Event: {escape(c['famous_event'])}"
        )
        folium.Marker(
            location=[c["lat"], c["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(color="darkred", icon="flag", prefix="fa"),
        ).add_to(fmap)
    return fmap


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_sports_maps_tab():
    """Render the Sports & Events Maps tab in the Streamlit app."""
    st.markdown(
        '<div class="tab-header amber"><h4>Sports &amp; Events</h4>'
        '<p>10 sports maps: Olympics, FIFA, F1, tennis, marathons, '
        'stadiums, ski resorts, surf spots, cycling climbs &amp; motorsport</p></div>',
        unsafe_allow_html=True,
    )

    selected_map = st.selectbox(
        "Select Sports Map",
        MAP_TYPES,
        key="sports_map_type",
    )

    st.markdown("---")

    # =================================================================
    # 1. OLYMPIC HOST CITIES
    # =================================================================
    if selected_map == "Olympic Host Cities":
        st.markdown(
            "<p style='color:#8b97b0;'>All Summer (30) and Winter (25) "
            "Olympic host cities from 1896 to 2026. Blue markers for "
            "Summer Games, light blue for Winter Games.</p>",
            unsafe_allow_html=True,
        )
        season_filter = st.radio(
            "Filter by Season", ["All", "Summer", "Winter"],
            horizontal=True, key="olympic_season_filter",
        )
        df = get_olympic_data()
        if season_filter != "All":
            df = df[df["Season"] == season_filter].reset_index(drop=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Games Shown", len(df))
        summer_count = len(df[df["Season"] == "Summer"]) if season_filter == "All" else (len(df) if season_filter == "Summer" else 0)
        winter_count = len(df[df["Season"] == "Winter"]) if season_filter == "All" else (len(df) if season_filter == "Winter" else 0)
        c2.metric("Summer Games", summer_count)
        c3.metric("Winter Games", winter_count)

        fmap = _build_olympics_map(df)
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Host Countries Distribution")
        fig = _build_olympics_chart(df)
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Olympic Host Cities Data")
        st.dataframe(df.drop(columns=["Lat", "Lon"]), width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Olympics CSV", csv,
            "olympic_host_cities.csv", "text/csv",
            key="dl_olympics",
        )

    # =================================================================
    # 2. FIFA WORLD CUP
    # =================================================================
    elif selected_map == "FIFA World Cup":
        st.markdown(
            "<p style='color:#8b97b0;'>All 23 FIFA World Cup tournaments "
            "from 1930 (Uruguay) to 2026 (USA/Mexico/Canada). Shows host "
            "location, winner, runner-up and final venue.</p>",
            unsafe_allow_html=True,
        )
        df = get_fifa_data()
        c1, c2, c3 = st.columns(3)
        c1.metric("Tournaments", len(df))
        most_wins = df[df["Winner"] != "TBD"]["Winner"].value_counts().idxmax()
        most_wins_n = df[df["Winner"] != "TBD"]["Winner"].value_counts().max()
        c2.metric("Most Wins", f"{most_wins} ({most_wins_n})")
        c3.metric("Latest Host", "USA/Mexico/Canada (2026)")

        fmap = _build_fifa_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("World Cup Winners")
        fig = _build_fifa_winners_chart()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("FIFA World Cup Data")
        st.dataframe(df.drop(columns=["Lat", "Lon"]), width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download FIFA World Cup CSV", csv,
            "fifa_world_cups.csv", "text/csv",
            key="dl_fifa",
        )

    # =================================================================
    # 3. F1 CIRCUITS
    # =================================================================
    elif selected_map == "F1 Circuits":
        st.markdown(
            "<p style='color:#8b97b0;'>All 24 current Formula 1 circuits "
            "with track length, lap records and first Grand Prix year. "
            "Red flag markers on a dark world map.</p>",
            unsafe_allow_html=True,
        )
        df = get_f1_data()
        c1, c2, c3 = st.columns(3)
        c1.metric("Active Circuits", len(df))
        longest = df.loc[df["Length (km)"].idxmax()]
        c2.metric("Longest Track", f"{longest['Circuit'].split('(')[0].strip()}")
        oldest = df.loc[df["First GP"].idxmin()]
        c3.metric("Oldest Venue", f"{oldest['Circuit'].split('(')[0].strip()} ({oldest['First GP']})")

        fmap = _build_f1_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("F1 Circuits Data")
        st.dataframe(df.drop(columns=["Lat", "Lon"]), width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download F1 Circuits CSV", csv,
            "f1_circuits.csv", "text/csv",
            key="dl_f1",
        )

    # =================================================================
    # 4. TENNIS GRAND SLAMS
    # =================================================================
    elif selected_map == "Tennis Grand Slams":
        st.markdown(
            "<p style='color:#8b97b0;'>4 Grand Slams and 20 major tennis "
            "venues worldwide. Color-coded by tournament tier: Grand Slam, "
            "Masters 1000, ATP 500/250, and ATP Finals.</p>",
            unsafe_allow_html=True,
        )
        df = get_tennis_data()
        type_filter = st.multiselect(
            "Filter by Tournament Type",
            df["Type"].unique().tolist(),
            default=[],
            key="tennis_type_filter",
        )
        if type_filter:
            df = df[df["Type"].isin(type_filter)].reset_index(drop=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Venues Shown", len(df))
        c2.metric("Grand Slams", len(df[df["Type"] == "Grand Slam"]))
        total_cap = df["Capacity"].sum()
        c3.metric("Total Capacity", f"{total_cap:,}")

        fmap = _build_tennis_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Tennis Venues Data")
        st.dataframe(df.drop(columns=["Lat", "Lon"]), width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Tennis Venues CSV", csv,
            "tennis_venues.csv", "text/csv",
            key="dl_tennis",
        )

    # =================================================================
    # 5. WORLD MARATHONS
    # =================================================================
    elif selected_map == "World Marathons":
        st.markdown(
            "<p style='color:#8b97b0;'>20 major world marathons with course "
            "records, elevation profiles and participant numbers. Circle size "
            "proportional to participant count.</p>",
            unsafe_allow_html=True,
        )
        df = get_marathon_data()
        c1, c2, c3 = st.columns(3)
        c1.metric("Marathons", len(df))
        fastest = df.loc[df["Record"].idxmin()]
        c2.metric("Fastest Course", f"{fastest['Marathon']} ({fastest['Record']})")
        biggest = df.loc[df["Participants"].idxmax()]
        c3.metric("Largest Field", f"{biggest['Marathon']} (~{biggest['Participants']:,})")

        fmap = _build_marathon_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Course Records Ranking")
        fig = _build_marathon_chart()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("World Marathons Data")
        st.dataframe(df.drop(columns=["Lat", "Lon"]), width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Marathons CSV", csv,
            "world_marathons.csv", "text/csv",
            key="dl_marathons",
        )

    # =================================================================
    # 6. FOOTBALL STADIUMS (Overpass)
    # =================================================================
    elif selected_map == "Football Stadiums":
        st.markdown(
            "<p style='color:#8b97b0;'>Search for football (soccer) stadiums "
            "using OpenStreetMap data via Overpass API. Select a region to "
            "find stadiums with name, capacity and operator info.</p>",
            unsafe_allow_html=True,
        )
        region = st.selectbox(
            "Select Region",
            list(STADIUM_REGIONS.keys()),
            key="stadium_region",
        )
        if st.button("Search Stadiums", key="btn_stadiums"):
            with st.spinner("Querying Overpass API for stadiums..."):
                stadiums = fetch_football_stadiums(region)
            c1, c2, c3 = st.columns(3)
            c1.metric("Stadiums Found", len(stadiums))
            named = len([s for s in stadiums if s["name"] != "Unknown Stadium"])
            c2.metric("Named Stadiums", named)
            c3.metric("Region", region)

            fmap = _build_stadium_map(stadiums)
            components.html(fmap._repr_html_(), height=550)

            if stadiums:
                st.subheader("Football Stadiums Data")
                df = pd.DataFrame(stadiums)
                st.dataframe(df, width="stretch")
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Stadiums CSV", csv,
                    "football_stadiums.csv", "text/csv",
                    key="dl_stadiums",
                )
            else:
                st.info("No stadiums found in this region. Try a different region.")

    # =================================================================
    # 7. SKI RESORTS
    # =================================================================
    elif selected_map == "Ski Resorts":
        st.markdown(
            "<p style='color:#8b97b0;'>30 world-class ski resorts with "
            "vertical drop, number of runs, annual snowfall and peak "
            "elevation data. From the Alps to Japan to the Rockies.</p>",
            unsafe_allow_html=True,
        )
        df = get_ski_data()
        country_filter = st.multiselect(
            "Filter by Country",
            sorted(df["Country"].unique().tolist()),
            default=[],
            key="ski_country_filter",
        )
        if country_filter:
            df = df[df["Country"].isin(country_filter)].reset_index(drop=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Resorts Shown", len(df))
        if len(df) > 0:
            best_vert = df.loc[df["Vertical Drop (m)"].idxmax()]
            c2.metric("Greatest Vertical", f"{best_vert['Resort']} ({best_vert['Vertical Drop (m)']}m)")
            most_snow = df.loc[df["Snowfall (cm)"].idxmax()]
            c3.metric("Most Snow", f"{most_snow['Resort']} ({most_snow['Snowfall (cm)']}cm)")
        else:
            c2.metric("Greatest Vertical", "N/A")
            c3.metric("Most Snow", "N/A")

        fmap = _build_ski_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Vertical Drop Comparison")
        fig = _build_ski_vertical_chart()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Ski Resorts Data")
        st.dataframe(df.drop(columns=["Lat", "Lon"]), width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Ski Resorts CSV", csv,
            "ski_resorts.csv", "text/csv",
            key="dl_ski",
        )

    # =================================================================
    # 8. SURF SPOTS
    # =================================================================
    elif selected_map == "Surf Spots":
        st.markdown(
            "<p style='color:#8b97b0;'>25 legendary surf breaks worldwide "
            "with wave type, best season and maximum wave height. Circle "
            "size proportional to maximum wave height.</p>",
            unsafe_allow_html=True,
        )
        df = get_surf_data()
        c1, c2, c3 = st.columns(3)
        c1.metric("Surf Spots", len(df))
        biggest_wave = df.loc[df["Max Height (ft)"].idxmax()]
        c2.metric("Biggest Waves", f"{biggest_wave['Spot']} ({biggest_wave['Max Height (ft)']}ft)")
        countries = df["Country"].nunique()
        c3.metric("Countries", countries)

        fmap = _build_surf_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Surf Spots Data")
        st.dataframe(df.drop(columns=["Lat", "Lon"]), width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Surf Spots CSV", csv,
            "surf_spots.csv", "text/csv",
            key="dl_surf",
        )

    # =================================================================
    # 9. CYCLING CLIMBS
    # =================================================================
    elif selected_map == "Cycling Climbs":
        st.markdown(
            "<p style='color:#8b97b0;'>25 legendary climbs from the Tour de "
            "France, Giro d'Italia and Vuelta a Espana. Color-coded by "
            "grand tour, circle size by gradient steepness.</p>",
            unsafe_allow_html=True,
        )
        df = get_cycling_data()
        race_filter = st.multiselect(
            "Filter by Grand Tour",
            df["Race"].unique().tolist(),
            default=[],
            key="cycling_race_filter",
        )
        if race_filter:
            df = df[df["Race"].isin(race_filter)].reset_index(drop=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Climbs Shown", len(df))
        if len(df) > 0:
            steepest = df.loc[df["Gradient (%)"].idxmax()]
            c2.metric("Steepest", f"{steepest['Climb']} ({steepest['Gradient (%)']}%)")
            highest = df.loc[df["Altitude (m)"].idxmax()]
            c3.metric("Highest", f"{highest['Climb']} ({highest['Altitude (m)']}m)")
        else:
            c2.metric("Steepest", "N/A")
            c3.metric("Highest", "N/A")

        fmap = _build_cycling_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Steepest Climbs")
        fig = _build_cycling_gradient_chart()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Cycling Climbs Data")
        st.dataframe(df.drop(columns=["Lat", "Lon"]), width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Cycling Climbs CSV", csv,
            "cycling_climbs.csv", "text/csv",
            key="dl_cycling",
        )

    # =================================================================
    # 10. MOTORSPORT CIRCUITS
    # =================================================================
    elif selected_map == "Motorsport Circuits":
        st.markdown(
            "<p style='color:#8b97b0;'>25 iconic motorsport circuits "
            "worldwide including Le Mans, Nurburgring, Daytona, Bathurst, "
            "Isle of Man TT and more. Dark red flag markers.</p>",
            unsafe_allow_html=True,
        )
        df = get_motorsport_data()
        c1, c2, c3 = st.columns(3)
        c1.metric("Circuits", len(df))
        longest = df.loc[df["Length (km)"].idxmax()]
        c2.metric("Longest", f"{longest['Circuit'].split('(')[0].strip()} ({longest['Length (km)']}km)")
        oldest = df.loc[df["First Race"].idxmin()]
        c3.metric("Oldest", f"{oldest['Circuit'].split('(')[0].strip()} ({oldest['First Race']})")

        fmap = _build_motorsport_map()
        components.html(fmap._repr_html_(), height=550)

        st.subheader("Motorsport Circuits Data")
        st.dataframe(df.drop(columns=["Lat", "Lon"]), width="stretch")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Motorsport Circuits CSV", csv,
            "motorsport_circuits.csv", "text/csv",
            key="dl_motorsport",
        )
