# -*- coding: utf-8 -*-
"""
Marathon & Running Maps module for TerraScout AI.
Provides 10 thematic running map modes covering world major marathons,
ultramarathon trails, historic Olympic running venues, trail running,
parkrun locations, ancient Olympic sites, Ironman triathlon venues,
mountain running races, city running routes, and running museums.
All data is hardcoded.
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

# =====================================================================
# CONSTANTS
# =====================================================================
DARK_TILES = "CartoDB dark_matter"

# =====================================================================
# 1. WORLD MAJOR MARATHONS
# =====================================================================
WORLD_MAJOR_MARATHONS = [
    {"name": "Boston Marathon", "city": "Boston", "country": "USA", "lat": 42.3501, "lon": -71.0789, "founded": 1897, "month": "April", "distance": "42.195 km", "record": "2:03:02", "record_holder": "Geoffrey Mutai", "finishers_approx": 30000, "elevation_gain_m": 146, "note": "Oldest annual marathon, requires qualifying time"},
    {"name": "New York City Marathon", "city": "New York", "country": "USA", "lat": 40.7686, "lon": -73.9669, "founded": 1970, "month": "November", "distance": "42.195 km", "record": "2:05:06", "record_holder": "Geoffrey Mutai", "finishers_approx": 53000, "elevation_gain_m": 93, "note": "Largest marathon in the world by finishers"},
    {"name": "Chicago Marathon", "city": "Chicago", "country": "USA", "lat": 41.8745, "lon": -87.6245, "founded": 1977, "month": "October", "distance": "42.195 km", "record": "2:03:45", "record_holder": "Dennis Kimetto", "finishers_approx": 45000, "elevation_gain_m": 30, "note": "Flat and fast course through downtown"},
    {"name": "London Marathon", "city": "London", "country": "UK", "lat": 51.4826, "lon": -0.0077, "founded": 1981, "month": "April", "distance": "42.195 km", "record": "2:01:25", "record_holder": "Kelvin Kiptum", "finishers_approx": 42000, "elevation_gain_m": 47, "note": "Iconic route past Tower Bridge and Big Ben"},
    {"name": "Berlin Marathon", "city": "Berlin", "country": "Germany", "lat": 52.5145, "lon": 13.3501, "founded": 1974, "month": "September", "distance": "42.195 km", "record": "2:00:35", "record_holder": "Kelvin Kiptum", "finishers_approx": 45000, "elevation_gain_m": 20, "note": "Fastest course in the world, most world records set here"},
    {"name": "Tokyo Marathon", "city": "Tokyo", "country": "Japan", "lat": 35.6894, "lon": 139.6917, "founded": 2007, "month": "March", "distance": "42.195 km", "record": "2:02:40", "record_holder": "Eliud Kipchoge", "finishers_approx": 38000, "elevation_gain_m": 42, "note": "Newest World Marathon Major, massive crowd support"},
    {"name": "Paris Marathon", "city": "Paris", "country": "France", "lat": 48.8738, "lon": 2.2950, "founded": 1976, "month": "April", "distance": "42.195 km", "record": "2:05:04", "record_holder": "Kenenisa Bekele", "finishers_approx": 50000, "elevation_gain_m": 65, "note": "Starts at Champs-Elysees, scenic route"},
    {"name": "Rotterdam Marathon", "city": "Rotterdam", "country": "Netherlands", "lat": 51.9244, "lon": 4.4777, "founded": 1981, "month": "April", "distance": "42.195 km", "record": "2:04:27", "record_holder": "Marius Kipserem", "finishers_approx": 15000, "elevation_gain_m": 10, "note": "Extremely flat course, known for fast times"},
    {"name": "Athens Classic Marathon", "city": "Athens", "country": "Greece", "lat": 37.9838, "lon": 23.7275, "founded": 1972, "month": "November", "distance": "42.195 km", "record": "2:10:55", "record_holder": "Felix Kandie", "finishers_approx": 18000, "elevation_gain_m": 250, "note": "Historic route from Marathon to Athens, original marathon course"},
    {"name": "Dubai Marathon", "city": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708, "founded": 2000, "month": "January", "distance": "42.195 km", "record": "2:04:11", "record_holder": "Mosinet Geremew", "finishers_approx": 8000, "elevation_gain_m": 5, "note": "Richest marathon prize purse"},
    {"name": "Sydney Marathon", "city": "Sydney", "country": "Australia", "lat": -33.8568, "lon": 151.2153, "founded": 2000, "month": "September", "distance": "42.195 km", "record": "2:08:16", "record_holder": "Yuta Shitara", "finishers_approx": 16000, "elevation_gain_m": 78, "note": "Course crosses the iconic Harbour Bridge"},
    {"name": "Comrades Marathon", "city": "Durban", "country": "South Africa", "lat": -29.8587, "lon": 31.0218, "founded": 1921, "month": "June", "distance": "89 km", "record": "5:18:19", "record_holder": "David Gatebe", "finishers_approx": 20000, "elevation_gain_m": 870, "note": "Oldest and largest ultra-marathon, up/down run alternates yearly"},
    {"name": "Honolulu Marathon", "city": "Honolulu", "country": "USA", "lat": 21.2740, "lon": -157.8212, "founded": 1973, "month": "December", "distance": "42.195 km", "record": "2:09:59", "record_holder": "Jimmy Muindi", "finishers_approx": 25000, "elevation_gain_m": 55, "note": "No cutoff time, popular with Japanese runners"},
    {"name": "Seville Marathon", "city": "Seville", "country": "Spain", "lat": 37.3891, "lon": -5.9845, "founded": 1985, "month": "February", "distance": "42.195 km", "record": "2:05:37", "record_holder": "Mule Wasihun", "finishers_approx": 10000, "elevation_gain_m": 12, "note": "One of the fastest marathon courses in Europe"},
    {"name": "Valencia Marathon", "city": "Valencia", "country": "Spain", "lat": 39.4699, "lon": -0.3763, "founded": 1981, "month": "December", "distance": "42.195 km", "record": "2:01:53", "record_holder": "Sisay Lemma", "finishers_approx": 25000, "elevation_gain_m": 9, "note": "Emerged as one of the fastest courses globally"},
    {"name": "Vienna City Marathon", "city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738, "founded": 1984, "month": "April", "distance": "42.195 km", "record": "2:05:41", "record_holder": "Robert Chemosin", "finishers_approx": 10000, "elevation_gain_m": 40, "note": "Beautiful course through imperial Vienna"},
    {"name": "Rome Marathon", "city": "Rome", "country": "Italy", "lat": 41.8902, "lon": 12.4922, "founded": 1995, "month": "March", "distance": "42.195 km", "record": "2:07:17", "record_holder": "Joshua Kipkoech", "finishers_approx": 12000, "elevation_gain_m": 70, "note": "Route passes Colosseum, Vatican, and Roman Forum"},
    {"name": "Mexico City Marathon", "city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "founded": 1983, "month": "August", "distance": "42.195 km", "record": "2:12:00", "record_holder": "Julius Kogo", "finishers_approx": 28000, "elevation_gain_m": 95, "note": "Run at 2,240m altitude, challenging conditions"},
    {"name": "Cape Town Marathon", "city": "Cape Town", "country": "South Africa", "lat": -33.9249, "lon": 18.4241, "founded": 2014, "month": "October", "distance": "42.195 km", "record": "2:08:31", "record_holder": "Stephen Mokoka", "finishers_approx": 11000, "elevation_gain_m": 90, "note": "Stunning coastal route with Table Mountain views"},
    {"name": "Buenos Aires Marathon", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816, "founded": 2008, "month": "October", "distance": "42.195 km", "record": "2:08:50", "record_holder": "Leul Gebresilase", "finishers_approx": 10000, "elevation_gain_m": 18, "note": "Fast flat course through the Paris of South America"},
    {"name": "Mumbai Marathon", "city": "Mumbai", "country": "India", "lat": 18.9440, "lon": 72.8237, "founded": 2004, "month": "January", "distance": "42.195 km", "record": "2:07:32", "record_holder": "Deressa Chiala", "finishers_approx": 12000, "elevation_gain_m": 25, "note": "Largest marathon in Asia by field size"},
    {"name": "Singapore Marathon", "city": "Singapore", "country": "Singapore", "lat": 1.2903, "lon": 103.8520, "founded": 2002, "month": "December", "distance": "42.195 km", "record": "2:13:39", "record_holder": "Joshua Kipkorir", "finishers_approx": 10000, "elevation_gain_m": 15, "note": "Night race to beat tropical heat"},
    {"name": "Istanbul Marathon", "city": "Istanbul", "country": "Turkey", "lat": 41.0424, "lon": 29.0010, "founded": 1979, "month": "November", "distance": "42.195 km", "record": "2:09:57", "record_holder": "Felix Kimutai", "finishers_approx": 12000, "elevation_gain_m": 85, "note": "Only marathon that crosses two continents (Asia to Europe)"},
    {"name": "Seoul Marathon", "city": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780, "founded": 1931, "month": "March", "distance": "42.195 km", "record": "2:05:13", "record_holder": "Wilson Loyanae", "finishers_approx": 25000, "elevation_gain_m": 55, "note": "One of the oldest marathons in Asia"},
    {"name": "Beirut Marathon", "city": "Beirut", "country": "Lebanon", "lat": 33.8938, "lon": 35.5018, "founded": 2003, "month": "November", "distance": "42.195 km", "record": "2:17:46", "record_holder": "El Hassan El Abbassi", "finishers_approx": 6000, "elevation_gain_m": 60, "note": "Symbol of unity and peace in the Middle East"},
    {"name": "Nairobi Marathon", "city": "Nairobi", "country": "Kenya", "lat": -1.2921, "lon": 36.8219, "founded": 2003, "month": "October", "distance": "42.195 km", "record": "2:10:52", "record_holder": "Lucas Rotich", "finishers_approx": 5000, "elevation_gain_m": 200, "note": "Run at 1,795m altitude in the home of distance running"},
    {"name": "Amsterdam Marathon", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "founded": 1975, "month": "October", "distance": "42.195 km", "record": "2:03:36", "record_holder": "Tamirat Tola", "finishers_approx": 15000, "elevation_gain_m": 8, "note": "Pancake-flat course finishing in Olympic Stadium"},
    {"name": "Osaka Marathon", "city": "Osaka", "country": "Japan", "lat": 34.6937, "lon": 135.5023, "founded": 2011, "month": "February", "distance": "42.195 km", "record": "2:07:31", "record_holder": "Titus Ekiru", "finishers_approx": 32000, "elevation_gain_m": 18, "note": "Vibrant route through Japan second city"},
    {"name": "Zurich Marathon", "city": "Zurich", "country": "Switzerland", "lat": 47.3769, "lon": 8.5417, "founded": 2003, "month": "April", "distance": "42.195 km", "record": "2:12:11", "record_holder": "Tadesse Abraham", "finishers_approx": 5000, "elevation_gain_m": 80, "note": "Scenic lakeside route through Swiss financial capital"},
    {"name": "Reykjavik Marathon", "city": "Reykjavik", "country": "Iceland", "lat": 64.1466, "lon": -21.9426, "founded": 1984, "month": "August", "distance": "42.195 km", "record": "2:20:12", "record_holder": "Jon Hallgrimsson", "finishers_approx": 3000, "elevation_gain_m": 55, "note": "Northernmost major marathon, midnight sun potential"},
]

# =====================================================================
# 2. ULTRAMARATHON TRAILS
# =====================================================================
ULTRAMARATHON_TRAILS = [
    {"name": "Western States 100", "location": "Squaw Valley to Auburn, CA", "country": "USA", "lat": 39.1968, "lon": -120.2354, "distance_km": 161, "elevation_gain_m": 5500, "founded": 1974, "terrain": "Mountain trail", "record": "14:09:28", "record_holder": "Jim Walmsley", "note": "Oldest 100-mile trail race, gold standard of ultras"},
    {"name": "Ultra-Trail du Mont-Blanc (UTMB)", "location": "Chamonix", "country": "France", "lat": 45.9237, "lon": 6.8694, "distance_km": 171, "elevation_gain_m": 10000, "founded": 2003, "terrain": "Alpine", "record": "19:01:29", "record_holder": "Kilian Jornet", "note": "Circumnavigates Mont Blanc through 3 countries"},
    {"name": "Badwater 135", "location": "Death Valley, CA", "country": "USA", "lat": 36.2291, "lon": -116.7679, "distance_km": 217, "elevation_gain_m": 4450, "founded": 1987, "terrain": "Road/desert", "record": "21:33:01", "record_holder": "Pete Kostelnick", "note": "From lowest point in N. America, temps exceed 54C"},
    {"name": "Marathon des Sables", "location": "Sahara Desert", "country": "Morocco", "lat": 31.0797, "lon": -4.0083, "distance_km": 251, "elevation_gain_m": 1200, "founded": 1986, "terrain": "Desert sand", "record": "16:22:29", "record_holder": "Rachid El Morabity", "note": "6-day self-supported stage race through the Sahara"},
    {"name": "Tor des Geants", "location": "Aosta Valley", "country": "Italy", "lat": 45.7370, "lon": 7.3200, "distance_km": 330, "elevation_gain_m": 24000, "founded": 2010, "terrain": "Alpine trail", "record": "62:01:00", "record_holder": "Franco Colle", "note": "One of the toughest ultras, 150 hour time limit"},
    {"name": "Barkley Marathons", "location": "Frozen Head State Park, TN", "country": "USA", "lat": 36.1350, "lon": -84.4280, "distance_km": 160, "elevation_gain_m": 18000, "founded": 1986, "terrain": "Off-trail bushwhack", "record": "52:03:08", "record_holder": "Brett Maune", "note": "Notoriously difficult, fewer than 20 finishers ever"},
    {"name": "Spartathlon", "location": "Athens to Sparta", "country": "Greece", "lat": 37.9838, "lon": 23.7275, "distance_km": 246, "elevation_gain_m": 1200, "founded": 1983, "terrain": "Road/mountain", "record": "20:25:00", "record_holder": "Yiannis Kouros", "note": "Retraces Pheidippides run from Athens to Sparta"},
    {"name": "Hardrock 100", "location": "Silverton, CO", "country": "USA", "lat": 37.8120, "lon": -107.6614, "distance_km": 161, "elevation_gain_m": 10000, "founded": 1992, "terrain": "Mountain/alpine", "record": "21:41:28", "record_holder": "Kilian Jornet", "note": "Average elevation 3,400m, extreme mountain ultra"},
    {"name": "Leadville Trail 100", "location": "Leadville, CO", "country": "USA", "lat": 39.2477, "lon": -106.2925, "distance_km": 161, "elevation_gain_m": 4800, "founded": 1983, "terrain": "Mountain trail", "record": "15:42:59", "record_holder": "Matt Carpenter", "note": "Race Across the Sky at extreme altitude"},
    {"name": "Comrades Marathon", "location": "Durban to Pietermaritzburg", "country": "South Africa", "lat": -29.8587, "lon": 31.0218, "distance_km": 89, "elevation_gain_m": 870, "founded": 1921, "terrain": "Road", "record": "5:18:19", "record_holder": "David Gatebe", "note": "Oldest and largest ultramarathon in the world"},
    {"name": "The Spine Race", "location": "Pennine Way, England", "country": "UK", "lat": 53.3695, "lon": -2.0935, "distance_km": 431, "elevation_gain_m": 12500, "founded": 2012, "terrain": "Moorland/trail", "record": "77:44:00", "record_holder": "Jasmin Paris", "note": "Non-stop winter race along entire Pennine Way"},
    {"name": "Dragon's Back Race", "location": "Wales", "country": "UK", "lat": 53.0685, "lon": -3.8614, "distance_km": 380, "elevation_gain_m": 17000, "founded": 1992, "terrain": "Mountain", "record": "42:26:00", "record_holder": "Jim Mann", "note": "5-day race traversing the spine of Wales"},
    {"name": "Lavaredo Ultra Trail", "location": "Cortina d'Ampezzo", "country": "Italy", "lat": 46.5404, "lon": 12.1357, "distance_km": 120, "elevation_gain_m": 5800, "founded": 2007, "terrain": "Dolomite trails", "record": "10:32:29", "record_holder": "Kilian Jornet", "note": "Stunning Dolomites scenery, UTMB qualifying race"},
    {"name": "Diagonale des Fous", "location": "Reunion Island", "country": "France", "lat": -21.1151, "lon": 55.5364, "distance_km": 165, "elevation_gain_m": 9576, "founded": 1993, "terrain": "Volcanic island", "record": "22:20:00", "record_holder": "Francois D'Haene", "note": "Crosses volcanic Reunion Island diagonally"},
    {"name": "Transgrancanaria", "location": "Gran Canaria", "country": "Spain", "lat": 28.0000, "lon": -15.5900, "distance_km": 128, "elevation_gain_m": 7500, "founded": 2003, "terrain": "Island mountain", "record": "11:51:00", "record_holder": "Cristofer Clemente", "note": "Crosses Gran Canaria from south to north"},
    {"name": "Jungle Ultra", "location": "Manu National Park", "country": "Peru", "lat": -12.8394, "lon": -71.3584, "distance_km": 230, "elevation_gain_m": 3000, "founded": 2013, "terrain": "Amazon jungle", "record": "36:15:00", "record_holder": "Rufus Maybank", "note": "5-day self-supported race through Amazon rainforest"},
    {"name": "Ultra Fiord", "location": "Patagonia", "country": "Chile", "lat": -51.7230, "lon": -72.5100, "distance_km": 100, "elevation_gain_m": 4500, "founded": 2015, "terrain": "Patagonian trail", "record": "14:30:00", "record_holder": "Sergio Rota", "note": "Remote Patagonian fjords and glaciers"},
    {"name": "Omani Desert Ultra", "location": "Wahiba Sands", "country": "Oman", "lat": 22.0000, "lon": 58.5000, "distance_km": 165, "elevation_gain_m": 500, "founded": 2015, "terrain": "Desert dunes", "record": "28:45:00", "record_holder": "Various", "note": "Self-supported through Omani desert dunes"},
    {"name": "Ultra-Trail Australia", "location": "Blue Mountains, NSW", "country": "Australia", "lat": -33.7282, "lon": 150.3119, "distance_km": 100, "elevation_gain_m": 4400, "founded": 2008, "terrain": "Bush/canyon trail", "record": "7:58:22", "record_holder": "Tom Evans", "note": "Through UNESCO World Heritage Blue Mountains"},
    {"name": "Eiger Ultra Trail", "location": "Grindelwald", "country": "Switzerland", "lat": 46.6244, "lon": 8.0413, "distance_km": 101, "elevation_gain_m": 6700, "founded": 2011, "terrain": "Alpine", "record": "9:36:00", "record_holder": "Pascal Egli", "note": "Circles the famous North Face of the Eiger"},
    {"name": "Tahoe 200", "location": "Lake Tahoe, CA/NV", "country": "USA", "lat": 39.0968, "lon": -120.0324, "distance_km": 322, "elevation_gain_m": 12200, "founded": 2014, "terrain": "Mountain trail", "record": "41:09:00", "record_holder": "Karel Sabbe", "note": "Full circumnavigation of Lake Tahoe"},
    {"name": "Mozart 100", "location": "Salzburg", "country": "Austria", "lat": 47.8095, "lon": 13.0550, "distance_km": 100, "elevation_gain_m": 4600, "founded": 2015, "terrain": "Alpine trail", "record": "10:15:00", "record_holder": "Florian Grasel", "note": "Scenic alpine trails around Salzburg region"},
    {"name": "Grand Raid Reunion", "location": "Reunion Island", "country": "France", "lat": -21.1151, "lon": 55.5364, "distance_km": 165, "elevation_gain_m": 9576, "founded": 1993, "terrain": "Volcanic", "record": "22:20:00", "record_holder": "Francois D'Haene", "note": "Volcanic terrain through tropical island"},
    {"name": "Tarawera Ultra", "location": "Rotorua", "country": "New Zealand", "lat": -38.1368, "lon": 176.2497, "distance_km": 102, "elevation_gain_m": 2200, "founded": 2010, "terrain": "Bush/lakeside", "record": "7:13:13", "record_holder": "Jim Walmsley", "note": "Through geothermal landscapes and native bush"},
    {"name": "MIUT - Madeira Island Ultra Trail", "location": "Madeira", "country": "Portugal", "lat": 32.6669, "lon": -16.9241, "distance_km": 115, "elevation_gain_m": 7200, "founded": 2008, "terrain": "Island mountain", "record": "12:53:00", "record_holder": "Francois D'Haene", "note": "From sea level to 1,862m peak and back"},
]

# =====================================================================
# 3. HISTORIC OLYMPIC RUNNING VENUES
# =====================================================================
OLYMPIC_RUNNING_VENUES = [
    {"name": "Panathenaic Stadium", "city": "Athens", "country": "Greece", "lat": 37.9687, "lon": 23.7411, "year": 1896, "event": "Track events & marathon finish", "note": "Original 1896 Olympic venue, marble stadium rebuilt from ancient ruins"},
    {"name": "White City Stadium", "city": "London", "country": "UK", "lat": 51.5139, "lon": -0.2312, "year": 1908, "event": "Marathon & track", "note": "Where the marathon distance was standardized to 26.2 miles"},
    {"name": "Stockholm Olympic Stadium", "city": "Stockholm", "country": "Sweden", "lat": 59.3453, "lon": 18.0786, "year": 1912, "event": "Track & marathon", "note": "Jim Thorpe dominated, still in use today"},
    {"name": "Stade Olympique de Colombes", "city": "Paris", "country": "France", "lat": 48.9261, "lon": 2.2491, "year": 1924, "event": "Track events", "note": "Setting for Chariots of Fire, Paavo Nurmi era"},
    {"name": "Olympic Stadium Amsterdam", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3432, "lon": 4.8554, "year": 1928, "event": "Track events", "note": "First Olympic flame lit here, women first ran 800m"},
    {"name": "Los Angeles Memorial Coliseum", "city": "Los Angeles", "country": "USA", "lat": 34.0141, "lon": -118.2879, "year": 1932, "event": "Track & marathon", "note": "Only stadium to host 3 Olympic Games (1932, 1984, 2028)"},
    {"name": "Olympiastadion Berlin", "city": "Berlin", "country": "Germany", "lat": 52.5147, "lon": 13.2395, "year": 1936, "event": "Track events", "note": "Jesse Owens won 4 gold medals, defying Nazi ideology"},
    {"name": "Wembley Stadium (old)", "city": "London", "country": "UK", "lat": 51.5560, "lon": -0.2796, "year": 1948, "event": "Track events", "note": "Fanny Blankers-Koen won 4 golds, Austerity Games"},
    {"name": "Helsinki Olympic Stadium", "city": "Helsinki", "country": "Finland", "lat": 60.1869, "lon": 24.9271, "year": 1952, "event": "Track & marathon", "note": "Emil Zatopek triple gold (5K, 10K, Marathon)"},
    {"name": "Melbourne Cricket Ground", "city": "Melbourne", "country": "Australia", "lat": -37.8200, "lon": 144.9835, "year": 1956, "event": "Track events", "note": "Vladimir Kuts dominated distance running"},
    {"name": "Stadio Olimpico", "city": "Rome", "country": "Italy", "lat": 41.9341, "lon": 12.4547, "year": 1960, "event": "Marathon", "note": "Abebe Bikila won marathon barefoot through torch-lit Rome"},
    {"name": "National Stadium Tokyo (1964)", "city": "Tokyo", "country": "Japan", "lat": 35.6780, "lon": 139.7145, "year": 1964, "event": "Track events", "note": "Bikila repeated marathon gold, Bob Hayes won 100m"},
    {"name": "Estadio Olimpico Universitario", "city": "Mexico City", "country": "Mexico", "lat": 19.3038, "lon": -99.1526, "year": 1968, "event": "Track events", "note": "Bob Beamon long jump, Tommie Smith Black Power salute"},
    {"name": "Olympiastadion Munich", "city": "Munich", "country": "Germany", "lat": 48.1735, "lon": 11.5466, "year": 1972, "event": "Track & marathon", "note": "Frank Shorter marathon gold, Lasse Viren 5K/10K double"},
    {"name": "Olympic Stadium Montreal", "city": "Montreal", "country": "Canada", "lat": 45.5579, "lon": -73.5515, "year": 1976, "event": "Track events", "note": "Lasse Viren repeated 5K/10K double, Alberto Juantorena 400/800"},
    {"name": "Luzhniki Stadium", "city": "Moscow", "country": "Russia", "lat": 55.7155, "lon": 37.5536, "year": 1980, "event": "Track events", "note": "Steve Ovett/Sebastian Coe rivalry, boycott Games"},
    {"name": "Seoul Olympic Stadium", "city": "Seoul", "country": "South Korea", "lat": 37.5152, "lon": 127.0729, "year": 1988, "event": "Track events", "note": "Ben Johnson scandal, Florence Griffith-Joyner sprints"},
    {"name": "Estadi Olimpic Lluis Companys", "city": "Barcelona", "country": "Spain", "lat": 41.3647, "lon": 2.1553, "year": 1992, "event": "Track events", "note": "Derek Redmond's famous carry by his father"},
    {"name": "Centennial Olympic Stadium", "city": "Atlanta", "country": "USA", "lat": 33.7573, "lon": -84.3901, "year": 1996, "event": "Track events", "note": "Michael Johnson 200m/400m double, now Turner Field"},
    {"name": "Stadium Australia", "city": "Sydney", "country": "Australia", "lat": -33.8474, "lon": 151.0633, "year": 2000, "event": "Track & marathon", "note": "Cathy Freeman 400m gold, Haile Gebrselassie 10K"},
    {"name": "Olympic Stadium Athens 2004", "city": "Athens", "country": "Greece", "lat": 38.0364, "lon": 23.7876, "year": 2004, "event": "Track & marathon", "note": "Hicham El Guerrouj 1500/5000 double, return to Greece"},
    {"name": "Beijing National Stadium", "city": "Beijing", "country": "China", "lat": 39.9929, "lon": 116.3966, "year": 2008, "event": "Track events", "note": "Usain Bolt burst onto scene with 100m/200m world records"},
    {"name": "London Olympic Stadium", "city": "London", "country": "UK", "lat": 51.5385, "lon": -0.0164, "year": 2012, "event": "Track events", "note": "Mo Farah 5K/10K double, Super Saturday for GB"},
    {"name": "Estadio Olimpico Joao Havelange", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9121, "lon": -43.2396, "year": 2016, "event": "Track events", "note": "Usain Bolt triple-triple, Eliud Kipchoge marathon gold"},
    {"name": "Japan National Stadium", "city": "Tokyo", "country": "Japan", "lat": 35.6779, "lon": 139.7136, "year": 2021, "event": "Track events", "note": "COVID-delayed Games, Karsten Warholm 400m hurdles WR"},
    {"name": "Stade de France", "city": "Paris", "country": "France", "lat": 48.9244, "lon": 2.3601, "year": 2024, "event": "Track events", "note": "Noah Lyles 100m, Jakob Ingebrigtsen, packed crowd at marathon"},
]

# =====================================================================
# 4. TRAIL RUNNING PARADISES
# =====================================================================
TRAIL_RUNNING_PARADISES = [
    {"name": "Chamonix Valley", "location": "French Alps", "country": "France", "lat": 45.9237, "lon": 6.8694, "terrain": "Alpine", "best_month": "July-September", "signature_trail": "Tour du Mont Blanc", "distance_km": 170, "note": "UTMB capital, endless alpine trails around Mont Blanc"},
    {"name": "Zermatt Trails", "location": "Valais Alps", "country": "Switzerland", "lat": 46.0207, "lon": 7.7491, "terrain": "Alpine", "best_month": "June-September", "signature_trail": "Matterhorn Ultraks", "distance_km": 49, "note": "Running beneath the iconic Matterhorn"},
    {"name": "Dolomites", "location": "South Tyrol", "country": "Italy", "lat": 46.4102, "lon": 11.8440, "terrain": "Rocky alpine", "best_month": "June-September", "signature_trail": "Alta Via 1", "distance_km": 120, "note": "Dramatic limestone spires and refugio network"},
    {"name": "Annapurna Circuit", "location": "Nepal Himalaya", "country": "Nepal", "lat": 28.5966, "lon": 83.8200, "terrain": "Himalayan", "best_month": "Oct-November", "signature_trail": "Annapurna Trail Running", "distance_km": 230, "note": "Highest trail pass at 5,416m Thorong La"},
    {"name": "Moab Desert", "location": "Utah", "country": "USA", "lat": 38.5733, "lon": -109.5498, "terrain": "Desert/canyon", "best_month": "March-May", "signature_trail": "Moab Red Hot 55K", "distance_km": 55, "note": "Red rock canyons, slickrock, and Colorado River trails"},
    {"name": "Scottish Highlands", "location": "Highlands", "country": "UK", "lat": 57.1200, "lon": -5.7100, "terrain": "Moorland/mountain", "best_month": "May-September", "signature_trail": "West Highland Way", "distance_km": 154, "note": "Wild and remote terrain, midges and weather add challenge"},
    {"name": "Table Mountain", "location": "Cape Town", "country": "South Africa", "lat": -33.9628, "lon": 18.4098, "terrain": "Mountain/fynbos", "best_month": "March-May", "signature_trail": "Table Mountain Ultra", "distance_km": 65, "note": "Biodiversity hotspot with ocean views"},
    {"name": "Torres del Paine", "location": "Patagonia", "country": "Chile", "lat": -50.9423, "lon": -73.4068, "terrain": "Patagonian steppe", "best_month": "Nov-March", "signature_trail": "Ultra Paine", "distance_km": 80, "note": "Granite towers, glaciers, and fierce winds"},
    {"name": "Blue Mountains", "location": "New South Wales", "country": "Australia", "lat": -33.7282, "lon": 150.3119, "terrain": "Eucalyptus bush", "best_month": "March-May", "signature_trail": "UTA100", "distance_km": 100, "note": "Deep canyons, sandstone cliffs, and eucalyptus forests"},
    {"name": "Madeira Island", "location": "Atlantic Ocean", "country": "Portugal", "lat": 32.6669, "lon": -16.9241, "terrain": "Island volcanic", "best_month": "April-June", "signature_trail": "MIUT", "distance_km": 115, "note": "Levada irrigation channels make unique running paths"},
    {"name": "Gran Canaria", "location": "Canary Islands", "country": "Spain", "lat": 28.0000, "lon": -15.5900, "terrain": "Volcanic island", "best_month": "February-April", "signature_trail": "Transgrancanaria", "distance_km": 128, "note": "From beaches to 1,949m peak, miniature continent"},
    {"name": "Laugavegur Trail", "location": "Icelandic Highlands", "country": "Iceland", "lat": 63.8600, "lon": -19.4700, "terrain": "Volcanic/geothermal", "best_month": "June-August", "signature_trail": "Laugavegur Ultra", "distance_km": 55, "note": "Colorful rhyolite mountains and hot springs"},
    {"name": "Hong Kong Trail", "location": "Hong Kong", "country": "China", "lat": 22.2694, "lon": 114.1880, "terrain": "Tropical mountain", "best_month": "November-February", "signature_trail": "HK100", "distance_km": 100, "note": "Surprising wilderness minutes from skyscrapers"},
    {"name": "Reunion Island", "location": "Indian Ocean", "country": "France", "lat": -21.1151, "lon": 55.5364, "terrain": "Volcanic tropical", "best_month": "October", "signature_trail": "Grand Raid", "distance_km": 165, "note": "Active volcano, dramatic cirques and calderas"},
    {"name": "Canadian Rockies", "location": "Banff/Jasper", "country": "Canada", "lat": 51.1784, "lon": -115.5708, "terrain": "Rocky mountain", "best_month": "July-August", "signature_trail": "Canadian Death Race", "distance_km": 125, "note": "Bear country with turquoise glacial lakes"},
    {"name": "Lake District", "location": "Cumbria", "country": "UK", "lat": 54.4609, "lon": -3.0886, "terrain": "Fell/mountain", "best_month": "May-September", "signature_trail": "Lakeland 100", "distance_km": 161, "note": "Birthplace of fell running, Bob Graham Round country"},
    {"name": "Azores Trails", "location": "Azores", "country": "Portugal", "lat": 37.7410, "lon": -25.6756, "terrain": "Volcanic island", "best_month": "April-June", "signature_trail": "Azores Trail Run", "distance_km": 70, "note": "Mid-Atlantic volcanic islands with crater lakes"},
    {"name": "Queenstown Trails", "location": "South Island", "country": "New Zealand", "lat": -45.0312, "lon": 168.6626, "terrain": "Alpine/lakeside", "best_month": "Dec-March", "signature_trail": "Routeburn Track", "distance_km": 32, "note": "Lord of the Rings scenery, pristine trails"},
    {"name": "Mount Olympus", "location": "Pieria", "country": "Greece", "lat": 40.0859, "lon": 22.3583, "terrain": "Mediterranean alpine", "best_month": "May-October", "signature_trail": "Olympus Marathon", "distance_km": 44, "note": "Home of the gods, run where ancient athletes trained"},
    {"name": "Inca Trail", "location": "Cusco Region", "country": "Peru", "lat": -13.1631, "lon": -72.5450, "terrain": "Andean mountain", "best_month": "May-September", "signature_trail": "Inca Trail Marathon", "distance_km": 42, "note": "Ancient Incan pathways to Machu Picchu at altitude"},
    {"name": "Corsica GR20", "location": "Corsica", "country": "France", "lat": 42.1750, "lon": 9.0972, "terrain": "Mediterranean mountain", "best_month": "June-September", "signature_trail": "GR20", "distance_km": 180, "note": "Toughest GR trail in Europe, rocky ridgelines"},
    {"name": "Atlas Mountains", "location": "High Atlas", "country": "Morocco", "lat": 31.0600, "lon": -7.9100, "terrain": "North African alpine", "best_month": "April-June", "signature_trail": "Ultra Trail Atlas Toubkal", "distance_km": 105, "note": "Berber villages and North Africa highest peak"},
    {"name": "Hallasan Trails", "location": "Jeju Island", "country": "South Korea", "lat": 33.3617, "lon": 126.5292, "terrain": "Volcanic island", "best_month": "April-May", "signature_trail": "Jeju Trail Running", "distance_km": 50, "note": "UNESCO volcanic island with unique olle paths"},
    {"name": "Ethiopian Highlands", "location": "Simien Mountains", "country": "Ethiopia", "lat": 13.2500, "lon": 38.4000, "terrain": "Afro-alpine", "best_month": "October-January", "signature_trail": "Simien Mountains Trail", "distance_km": 60, "note": "Where champion runners train, dramatic escarpments"},
    {"name": "Tatra Mountains", "location": "Zakopane", "country": "Poland", "lat": 49.2992, "lon": 19.9496, "terrain": "Alpine", "best_month": "June-September", "signature_trail": "Tatra Running Festival", "distance_km": 80, "note": "Smallest alpine range, dramatic granite peaks"},
]

# =====================================================================
# 5. PARKRUN LOCATIONS WORLDWIDE
# =====================================================================
PARKRUN_LOCATIONS = [
    {"name": "Bushy Park parkrun", "city": "London", "country": "UK", "lat": 51.4096, "lon": -0.3392, "founded": 2004, "avg_runners": 1200, "note": "The very first parkrun, birthplace of the movement"},
    {"name": "Albert parkrun", "city": "Melbourne", "country": "Australia", "lat": -37.8436, "lon": 144.9801, "founded": 2011, "avg_runners": 700, "note": "Largest parkrun in Australia around Albert Park Lake"},
    {"name": "Woodhouse Moor parkrun", "city": "Leeds", "country": "UK", "lat": 53.8110, "lon": -1.5598, "founded": 2007, "avg_runners": 500, "note": "Popular northern England parkrun"},
    {"name": "Killerton parkrun", "city": "Exeter", "country": "UK", "lat": 50.7778, "lon": -3.4470, "founded": 2012, "avg_runners": 350, "note": "Beautiful National Trust estate parkrun"},
    {"name": "College Park parkrun", "city": "Johannesburg", "country": "South Africa", "lat": -26.1872, "lon": 28.0200, "founded": 2011, "avg_runners": 600, "note": "First parkrun in Africa"},
    {"name": "Roosevelt Island parkrun", "city": "Washington DC", "country": "USA", "lat": 38.8954, "lon": -77.0659, "founded": 2012, "avg_runners": 250, "note": "Scenic parkrun along the Potomac River"},
    {"name": "North Beach parkrun", "city": "Durban", "country": "South Africa", "lat": -29.8467, "lon": 31.0323, "founded": 2012, "avg_runners": 800, "note": "Beachfront parkrun with ocean views"},
    {"name": "Centennial Park parkrun", "city": "Sydney", "country": "Australia", "lat": -33.8953, "lon": 151.2339, "founded": 2011, "avg_runners": 500, "note": "Iconic Sydney park with beautiful scenery"},
    {"name": "Bois de Boulogne parkrun", "city": "Paris", "country": "France", "lat": 48.8620, "lon": 2.2489, "founded": 2017, "avg_runners": 200, "note": "First parkrun in France"},
    {"name": "Dublin Phoenix Park parkrun", "city": "Dublin", "country": "Ireland", "lat": 53.3558, "lon": -6.3298, "founded": 2012, "avg_runners": 500, "note": "In Europe largest enclosed city park with deer"},
    {"name": "Berlin Hasenheide parkrun", "city": "Berlin", "country": "Germany", "lat": 52.4820, "lon": 13.4210, "founded": 2019, "avg_runners": 150, "note": "Growing parkrun community in Berlin"},
    {"name": "Crissy Field parkrun", "city": "San Francisco", "country": "USA", "lat": 37.8039, "lon": -122.4636, "founded": 2015, "avg_runners": 200, "note": "Golden Gate Bridge views during parkrun"},
    {"name": "Hagley Park parkrun", "city": "Christchurch", "country": "New Zealand", "lat": -43.5321, "lon": 172.6194, "founded": 2012, "avg_runners": 300, "note": "Flat fast parkrun in Christchurch main park"},
    {"name": "Two Oceans parkrun", "city": "Cape Town", "country": "South Africa", "lat": -34.0816, "lon": 18.3155, "founded": 2014, "avg_runners": 350, "note": "At famous Two Oceans Marathon course area"},
    {"name": "Stanley Park parkrun", "city": "Vancouver", "country": "Canada", "lat": 49.2943, "lon": -123.1417, "founded": 2017, "avg_runners": 200, "note": "Seawall views with mountain backdrop"},
    {"name": "Kowloon Park parkrun", "city": "Hong Kong", "country": "China", "lat": 22.3013, "lon": 114.1694, "founded": 2018, "avg_runners": 100, "note": "Compact urban parkrun in Tsim Sha Tsui"},
    {"name": "Ueno Park parkrun", "city": "Tokyo", "country": "Japan", "lat": 35.7141, "lon": 139.7750, "founded": 2019, "avg_runners": 150, "note": "Cherry blossom season makes this magical"},
    {"name": "Sathorn parkrun", "city": "Bangkok", "country": "Thailand", "lat": 13.7221, "lon": 100.5296, "founded": 2018, "avg_runners": 100, "note": "Early morning start to beat the tropical heat"},
    {"name": "Polokwane parkrun", "city": "Polokwane", "country": "South Africa", "lat": -23.9045, "lon": 29.4689, "founded": 2013, "avg_runners": 400, "note": "One of the largest parkruns in Limpopo province"},
    {"name": "Noosa parkrun", "city": "Noosa", "country": "Australia", "lat": -26.3929, "lon": 153.0714, "founded": 2012, "avg_runners": 600, "note": "Coastal Queensland paradise parkrun"},
    {"name": "Neckarau parkrun", "city": "Mannheim", "country": "Germany", "lat": 49.4506, "lon": 8.4879, "founded": 2019, "avg_runners": 120, "note": "Riverside parkrun along the Neckar"},
    {"name": "Parque Centenario parkrun", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6063, "lon": -58.4346, "founded": 2018, "avg_runners": 80, "note": "First parkrun in South America"},
    {"name": "Porirua parkrun", "city": "Wellington", "country": "New Zealand", "lat": -41.1337, "lon": 174.8404, "founded": 2012, "avg_runners": 200, "note": "Waterfront parkrun near Wellington"},
    {"name": "Dinton Pastures parkrun", "city": "Reading", "country": "UK", "lat": 51.4277, "lon": -0.8695, "founded": 2008, "avg_runners": 450, "note": "Scenic lakeside parkrun in Berkshire"},
    {"name": "Wuhan parkrun", "city": "Wuhan", "country": "China", "lat": 30.5728, "lon": 114.2879, "founded": 2017, "avg_runners": 100, "note": "Growing parkrun community in central China"},
]

# =====================================================================
# 6. ANCIENT OLYMPIC SITES
# =====================================================================
ANCIENT_OLYMPIC_SITES = [
    {"name": "Ancient Olympia", "location": "Peloponnese", "country": "Greece", "lat": 37.6388, "lon": 21.6300, "period": "776 BC - 393 AD", "events": "Stadion, diaulos, dolichos, pentathlon", "note": "Birthplace of the Olympic Games, Temple of Zeus"},
    {"name": "Delphi Stadium", "location": "Phocis", "country": "Greece", "lat": 38.4824, "lon": 22.5011, "period": "582 BC - 394 AD", "events": "Pythian Games footraces", "note": "Stadium at 600m elevation, Apollo sanctuary"},
    {"name": "Isthmia", "location": "Corinthia", "country": "Greece", "lat": 37.9135, "lon": 22.9987, "period": "582 BC - 4th c. AD", "events": "Isthmian Games sprint & distance", "note": "Biennial games in honor of Poseidon"},
    {"name": "Nemea Stadium", "location": "Corinthia", "country": "Greece", "lat": 37.8080, "lon": 22.7100, "period": "573 BC - 271 BC", "events": "Nemean Games footraces", "note": "Well-preserved ancient starting mechanism (hysplex)"},
    {"name": "Epidaurus Stadium", "location": "Argolid", "country": "Greece", "lat": 37.5966, "lon": 23.0728, "period": "4th c. BC", "events": "Asclepian Games athletic contests", "note": "Adjacent to famous theater, healing sanctuary"},
    {"name": "Athens Ancient Agora", "location": "Athens", "country": "Greece", "lat": 37.9747, "lon": 23.7225, "period": "6th c. BC onward", "events": "Panathenaic Games preparation", "note": "Training ground for Panathenaic athletes"},
    {"name": "Panathenaic Way", "location": "Athens", "country": "Greece", "lat": 37.9755, "lon": 23.7240, "period": "566 BC onward", "events": "Panathenaic procession & races", "note": "Sacred road used for the Great Panathenaia torch race"},
    {"name": "Aphrodisias Stadium", "location": "Caria", "country": "Turkey", "lat": 37.7091, "lon": 28.7289, "period": "1st c. BC - 6th c. AD", "events": "Athletic & gladiatorial contests", "note": "Best preserved ancient stadium, seats 30,000"},
    {"name": "Perge Stadium", "location": "Antalya", "country": "Turkey", "lat": 36.9614, "lon": 30.8545, "period": "2nd c. AD", "events": "Athletic games", "note": "Roman-era stadium with vaulted galleries"},
    {"name": "Laodicea Stadium", "location": "Denizli", "country": "Turkey", "lat": 37.8362, "lon": 29.1065, "period": "1st c. AD", "events": "Athletic festivals", "note": "Roman stadium in prosperous trading city"},
    {"name": "Delos Athletic Facilities", "location": "Delos", "country": "Greece", "lat": 37.3966, "lon": 25.2684, "period": "5th c. BC", "events": "Delian Games", "note": "Sacred island with gymnasium and palaestra"},
    {"name": "Cyrene Gymnasium", "location": "Shahhat", "country": "Libya", "lat": 32.8244, "lon": 21.8568, "period": "4th c. BC", "events": "Greek colonial athletics", "note": "Major Greek colony with extensive athletic facilities"},
    {"name": "Pergamon Gymnasium", "location": "Bergama", "country": "Turkey", "lat": 39.1303, "lon": 27.1804, "period": "2nd c. BC", "events": "Hellenistic athletics", "note": "Three-terrace gymnasium complex, largest in ancient world"},
    {"name": "Priene Stadium", "location": "Soke", "country": "Turkey", "lat": 37.6594, "lon": 27.2971, "period": "2nd c. BC", "events": "Athletic competitions", "note": "Compact well-preserved Hellenistic stadium"},
    {"name": "Miletus Stadium", "location": "Didim", "country": "Turkey", "lat": 37.5308, "lon": 27.2783, "period": "3rd c. BC", "events": "Panhellenic-style games", "note": "Could seat 15,000 spectators"},
    {"name": "Syracuse Greek Theater & Stadium", "location": "Syracuse", "country": "Italy", "lat": 37.0756, "lon": 15.2788, "period": "5th c. BC", "events": "Athletic & dramatic contests", "note": "Greek colonial athletic tradition in Sicily"},
    {"name": "Messene Stadium", "location": "Messinia", "country": "Greece", "lat": 37.1704, "lon": 21.9208, "period": "3rd c. BC", "events": "Athletic games", "note": "Remarkably well-preserved Hellenistic stadium"},
    {"name": "Olympia Gymnasium", "location": "Ancient Olympia", "country": "Greece", "lat": 37.6410, "lon": 21.6285, "period": "3rd c. BC", "events": "Olympic athlete training", "note": "Where athletes trained for one month before the Games"},
    {"name": "Dion Athletic Grounds", "location": "Pieria", "country": "Greece", "lat": 40.1682, "lon": 22.4876, "period": "5th c. BC", "events": "Olympia ta en Dii games", "note": "Macedonian athletic festival at foot of Olympus"},
    {"name": "Tyre Hippodrome", "location": "Tyre", "country": "Lebanon", "lat": 33.2705, "lon": 35.1963, "period": "2nd c. AD", "events": "Chariot races and athletics", "note": "Roman-era hippodrome, UNESCO World Heritage"},
    {"name": "Jerash Hippodrome", "location": "Jerash", "country": "Jordan", "lat": 32.2748, "lon": 35.8919, "period": "2nd c. AD", "events": "Chariot races, athletics", "note": "Well-preserved Roman provincial hippodrome"},
    {"name": "Caesarea Stadium", "location": "Caesarea", "country": "Israel", "lat": 32.5000, "lon": 34.8890, "period": "1st c. BC", "events": "Herodian athletic games", "note": "Built by Herod the Great in honor of Augustus"},
    {"name": "Nikopolis Stadium", "location": "Preveza", "country": "Greece", "lat": 38.9564, "lon": 20.7353, "period": "31 BC", "events": "Actian Games", "note": "Founded by Augustus to celebrate Battle of Actium"},
    {"name": "Didyma Sacred Way", "location": "Didim", "country": "Turkey", "lat": 37.3862, "lon": 27.2564, "period": "6th c. BC", "events": "Sacred races", "note": "Processional route with athletic competitions"},
    {"name": "Sardis Gymnasium", "location": "Salihli", "country": "Turkey", "lat": 38.4856, "lon": 28.0406, "period": "2nd c. AD", "events": "Roman athletics", "note": "Massive marble gymnasium-bath complex"},
]

# =====================================================================
# 7. IRONMAN TRIATHLON VENUES
# =====================================================================
IRONMAN_VENUES = [
    {"name": "Ironman World Championship", "city": "Kailua-Kona", "country": "USA", "lat": 19.6400, "lon": -155.9969, "founded": 1978, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "7:40:24", "record_holder": "Patrick Lange", "note": "The original and most prestigious Ironman, lava fields"},
    {"name": "Ironman Frankfurt", "city": "Frankfurt", "country": "Germany", "lat": 50.1109, "lon": 8.6821, "founded": 2002, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "7:41:33", "record_holder": "Jan Frodeno", "note": "European Championship, fast flat course"},
    {"name": "Ironman Lanzarote", "city": "Puerto del Carmen", "country": "Spain", "lat": 28.9209, "lon": -13.6657, "founded": 1992, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:36:36", "record_holder": "Eneko Llanos", "note": "Toughest Ironman course, volcanic wind and heat"},
    {"name": "Ironman Nice", "city": "Nice", "country": "France", "lat": 43.7102, "lon": 7.2620, "founded": 2005, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:09:15", "record_holder": "Patrick Lange", "note": "Mediterranean swim, hilly bike through Provence"},
    {"name": "Ironman Lake Placid", "city": "Lake Placid", "country": "USA", "lat": 44.2795, "lon": -73.9799, "founded": 1999, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:17:32", "record_holder": "Tim DeBoom", "note": "Adirondack Mountain setting, former Winter Olympics venue"},
    {"name": "Ironman South Africa", "city": "Port Elizabeth", "country": "South Africa", "lat": -33.9608, "lon": 25.6022, "founded": 2005, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "7:52:11", "record_holder": "Matt Trautman", "note": "Wind-swept coastal African Ironman"},
    {"name": "Ironman Australia", "city": "Port Macquarie", "country": "Australia", "lat": -31.4333, "lon": 152.9000, "founded": 2002, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "7:57:58", "record_holder": "Cameron Brown", "note": "Asia-Pacific Championship, scenic coastal route"},
    {"name": "Ironman Cairns", "city": "Cairns", "country": "Australia", "lat": -16.9186, "lon": 145.7781, "founded": 2012, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:12:00", "record_holder": "Cameron Wurf", "note": "Tropical Queensland, near Great Barrier Reef"},
    {"name": "Ironman New Zealand", "city": "Taupo", "country": "New Zealand", "lat": -38.6857, "lon": 176.0702, "founded": 1985, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:03:56", "record_holder": "Cameron Brown", "note": "Lake Taupo swim, volcanic plateau bike and run"},
    {"name": "Ironman Canada", "city": "Whistler", "country": "Canada", "lat": 50.1163, "lon": -122.9574, "founded": 2013, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:17:25", "record_holder": "Brent McMahon", "note": "Sea to Sky corridor, beautiful mountain course"},
    {"name": "Ironman Italy", "city": "Cervia", "country": "Italy", "lat": 44.2603, "lon": 12.3496, "founded": 2017, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:01:12", "record_holder": "Giulio Molinari", "note": "Adriatic Sea swim, flat Emilia-Romagna bike"},
    {"name": "Ironman Hamburg", "city": "Hamburg", "country": "Germany", "lat": 53.5511, "lon": 9.9937, "founded": 2017, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "7:51:34", "record_holder": "Jan Frodeno", "note": "City center triathlon with huge crowd support"},
    {"name": "Ironman Copenhagen", "city": "Copenhagen", "country": "Denmark", "lat": 55.6761, "lon": 12.5683, "founded": 2013, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "7:51:32", "record_holder": "Patrik Nilsson", "note": "Flat and fast Scandinavian course"},
    {"name": "Ironman Malaysia", "city": "Langkawi", "country": "Malaysia", "lat": 6.3500, "lon": 99.8000, "founded": 2007, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:22:31", "record_holder": "Pete Jacobs", "note": "Tropical island paradise triathlon"},
    {"name": "Ironman Japan", "city": "Hokkaido", "country": "Japan", "lat": 42.8048, "lon": 141.6963, "founded": 2013, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:20:44", "record_holder": "Braden Currie", "note": "Lake Toyako swim with volcano backdrop"},
    {"name": "Ironman Brazil", "city": "Florianopolis", "country": "Brazil", "lat": -27.5954, "lon": -48.5480, "founded": 2000, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:08:47", "record_holder": "Igor Amorelli", "note": "South American Championship, beach culture"},
    {"name": "Ironman Switzerland", "city": "Thun", "country": "Switzerland", "lat": 46.7580, "lon": 7.6280, "founded": 2007, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:06:41", "record_holder": "Jan van Berkel", "note": "Lake Thun swim beneath the Bernese Alps"},
    {"name": "Ironman Barcelona", "city": "Barcelona", "country": "Spain", "lat": 41.3851, "lon": 2.1734, "founded": 2016, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "7:53:34", "record_holder": "Bart Aernouts", "note": "Mediterranean swim, fast course with great support"},
    {"name": "Ironman Texas", "city": "The Woodlands", "country": "USA", "lat": 30.1658, "lon": -95.4613, "founded": 2011, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "7:53:46", "record_holder": "Matt Hanson", "note": "Flat fast course, early season race"},
    {"name": "Ironman Wales", "city": "Tenby", "country": "UK", "lat": 51.6720, "lon": -4.7066, "founded": 2011, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:34:17", "record_holder": "Andi Boecherer", "note": "Hilly Welsh course, amazing Pembrokeshire coastline"},
    {"name": "Ironman Tallinn", "city": "Tallinn", "country": "Estonia", "lat": 59.4370, "lon": 24.7536, "founded": 2018, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:12:00", "record_holder": "Various", "note": "Baltic Sea swim, medieval city run finish"},
    {"name": "Ironman South Africa (70.3)", "city": "Durban", "country": "South Africa", "lat": -29.8587, "lon": 31.0218, "founded": 2007, "swim_km": 1.93, "bike_km": 90, "run_km": 21.1, "record": "3:44:12", "record_holder": "Various", "note": "Half Ironman with beachfront atmosphere"},
    {"name": "Ironman Vitoria-Gasteiz", "city": "Vitoria-Gasteiz", "country": "Spain", "lat": 42.8467, "lon": -2.6716, "founded": 2015, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:05:42", "record_holder": "Eneko Llanos", "note": "Basque Country Ironman with passionate crowds"},
    {"name": "Ironman Chattanooga", "city": "Chattanooga", "country": "USA", "lat": 35.0456, "lon": -85.3097, "founded": 2014, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "7:59:34", "record_holder": "Andrew Starykowicz", "note": "Tennessee River current-assisted swim, scenic course"},
    {"name": "Ironman Taiwan", "city": "Penghu", "country": "Taiwan", "lat": 23.5711, "lon": 119.5793, "founded": 2011, "swim_km": 3.86, "bike_km": 180.25, "run_km": 42.2, "record": "8:38:00", "record_holder": "Various", "note": "Island archipelago race in the Taiwan Strait"},
]

# =====================================================================
# 8. MOUNTAIN RUNNING RACES
# =====================================================================
MOUNTAIN_RUNNING_RACES = [
    {"name": "Sierre-Zinal", "location": "Valais", "country": "Switzerland", "lat": 46.2915, "lon": 7.5352, "distance_km": 31, "elevation_gain_m": 2200, "founded": 1974, "record": "2:25:35", "record_holder": "Kilian Jornet", "note": "Race of the Five 4000ers, crown jewel of mountain running"},
    {"name": "Zegama-Aizkorri", "location": "Basque Country", "country": "Spain", "lat": 42.9722, "lon": -2.2903, "distance_km": 42, "elevation_gain_m": 2736, "founded": 2002, "terrain": "Technical karst", "record": "3:46:07", "record_holder": "Kilian Jornet", "note": "Brutal Basque mountain marathon, technical descents"},
    {"name": "Pikes Peak Ascent", "location": "Manitou Springs, CO", "country": "USA", "lat": 38.8588, "lon": -104.9367, "distance_km": 21.4, "elevation_gain_m": 2380, "founded": 1956, "record": "2:01:06", "record_holder": "Matt Carpenter", "note": "America mountain race, summit at 4,302m"},
    {"name": "Jungfrau Marathon", "location": "Interlaken", "country": "Switzerland", "lat": 46.6863, "lon": 7.8632, "distance_km": 42.195, "elevation_gain_m": 1829, "founded": 1993, "record": "2:49:46", "record_holder": "Jonathan Wyatt", "note": "From Interlaken to Kleine Scheidegg, Eiger views"},
    {"name": "Mont Blanc Marathon", "location": "Chamonix", "country": "France", "lat": 45.9237, "lon": 6.8694, "distance_km": 42, "elevation_gain_m": 2730, "founded": 2003, "record": "3:28:47", "record_holder": "Kilian Jornet", "note": "Marathon distance through the Mont Blanc massif"},
    {"name": "Olympus Marathon", "location": "Litochoro", "country": "Greece", "lat": 40.1032, "lon": 22.5022, "distance_km": 44, "elevation_gain_m": 3200, "founded": 2005, "record": "4:02:31", "record_holder": "Luis Alberto Hernando", "note": "Up and over mythological Mount Olympus"},
    {"name": "Grossglockner Mountain Run", "location": "Heiligenblut", "country": "Austria", "lat": 47.0442, "lon": 12.8424, "distance_km": 13.2, "elevation_gain_m": 1890, "founded": 2001, "record": "1:03:57", "record_holder": "Isaac Kosgei", "note": "Steep ascent up Austria highest peak area"},
    {"name": "Trofeo Kima", "location": "Val Masino", "country": "Italy", "lat": 46.2490, "lon": 9.6170, "distance_km": 52, "elevation_gain_m": 4200, "founded": 1993, "record": "5:28:00", "record_holder": "Kilian Jornet", "note": "Extreme via ferrata sections, most technical skyrace"},
    {"name": "Matterhorn Ultraks", "location": "Zermatt", "country": "Switzerland", "lat": 46.0207, "lon": 7.7491, "distance_km": 49, "elevation_gain_m": 3600, "founded": 2014, "record": "4:17:13", "record_holder": "Remi Bonnet", "note": "Beneath the iconic Matterhorn peak"},
    {"name": "Ring of Steall Skyrace", "location": "Glen Nevis", "country": "UK", "lat": 56.7963, "lon": -5.0190, "distance_km": 29, "elevation_gain_m": 2500, "founded": 2015, "record": "2:52:13", "record_holder": "Kilian Jornet", "note": "Technical Scottish Highlands skyrunning"},
    {"name": "Dolomites Skyrace", "location": "Canazei", "country": "Italy", "lat": 46.4764, "lon": 11.7700, "distance_km": 22, "elevation_gain_m": 1800, "founded": 2006, "record": "1:55:06", "record_holder": "Kilian Jornet", "note": "Stunning Dolomite scenery, demanding climbs"},
    {"name": "Tromsoe Skyrace", "location": "Tromso", "country": "Norway", "lat": 69.6496, "lon": 18.9560, "distance_km": 57, "elevation_gain_m": 4800, "founded": 2014, "record": "6:11:57", "record_holder": "Kilian Jornet", "note": "Arctic Norway above 69N, midnight sun potential"},
    {"name": "High Trail Vanoise", "location": "Val d'Isere", "country": "France", "lat": 45.4484, "lon": 6.9783, "distance_km": 70, "elevation_gain_m": 4700, "founded": 2015, "record": "6:14:31", "record_holder": "Davide Magnini", "note": "Technical Vanoise high-altitude trail running"},
    {"name": "K42 Patagonia", "location": "Villa La Angostura", "country": "Argentina", "lat": -40.7616, "lon": -71.6468, "distance_km": 42, "elevation_gain_m": 2000, "founded": 2008, "record": "3:22:00", "record_holder": "Various", "note": "Andean Patagonia mountain marathon"},
    {"name": "Mt Kinabalu Climbathon", "location": "Sabah", "country": "Malaysia", "lat": 6.0535, "lon": 116.5586, "distance_km": 21, "elevation_gain_m": 2229, "founded": 1987, "record": "2:26:03", "record_holder": "Kilian Jornet", "note": "Sprint up and down Southeast Asia highest peak"},
    {"name": "Limone Skyrace", "location": "Limone sul Garda", "country": "Italy", "lat": 45.8133, "lon": 10.7900, "distance_km": 24, "elevation_gain_m": 2300, "founded": 2003, "record": "2:20:29", "record_holder": "Kilian Jornet", "note": "Lake Garda to mountain summit skyrunning classic"},
    {"name": "Lantau 2 Peaks", "location": "Lantau Island", "country": "Hong Kong", "lat": 22.2573, "lon": 113.9376, "distance_km": 23, "elevation_gain_m": 1600, "founded": 2012, "record": "2:01:00", "record_holder": "Various", "note": "Steep mountain trail on Hong Kong largest island"},
    {"name": "Snowdon International", "location": "Llanberis", "country": "UK", "lat": 53.0791, "lon": -4.0763, "distance_km": 16, "elevation_gain_m": 980, "founded": 1976, "record": "1:02:29", "record_holder": "Kenny Stuart", "note": "Classic up-and-down Snowdon, Wales highest peak"},
    {"name": "Hochkonig Skyrace", "location": "Maria Alm", "country": "Austria", "lat": 47.4070, "lon": 12.9120, "distance_km": 32, "elevation_gain_m": 2500, "founded": 2018, "record": "3:12:00", "record_holder": "Various", "note": "Austrian Alps dramatic limestone ridges"},
    {"name": "Otter African Trail Run", "location": "Tsitsikamma", "country": "South Africa", "lat": -33.9700, "lon": 23.8800, "distance_km": 42, "elevation_gain_m": 2100, "founded": 2016, "record": "3:37:00", "record_holder": "Various", "note": "Along the famous Otter Trail, Garden Route"},
    {"name": "Penyagolosa Trails", "location": "Castellon", "country": "Spain", "lat": 40.2244, "lon": -0.3500, "distance_km": 60, "elevation_gain_m": 3100, "founded": 2011, "record": "5:44:00", "record_holder": "Thibaut Garrivier", "note": "Valencia mountain trail classic"},
    {"name": "Ben Nevis Race", "location": "Fort William", "country": "UK", "lat": 56.7969, "lon": -5.0036, "distance_km": 16, "elevation_gain_m": 1340, "founded": 1895, "record": "1:25:34", "record_holder": "Kenny Stuart", "note": "Up and down Britain highest peak since 1895"},
    {"name": "Kilimanjaro Trail Run", "location": "Moshi", "country": "Tanzania", "lat": -3.0674, "lon": 37.3556, "distance_km": 42, "elevation_gain_m": 2700, "founded": 2015, "record": "4:05:00", "record_holder": "Various", "note": "Through coffee plantations on Africa highest mountain"},
    {"name": "Elbrus Mountain Race", "location": "Elbrus", "country": "Russia", "lat": 43.3499, "lon": 42.4453, "distance_km": 11, "elevation_gain_m": 2393, "founded": 2005, "record": "3:24:14", "record_holder": "Vitaly Shkel", "note": "Race to the summit of Europe highest peak at 5,642m"},
    {"name": "Everest Trail Race", "location": "Solu-Khumbu", "country": "Nepal", "lat": 27.9881, "lon": 86.9250, "distance_km": 160, "elevation_gain_m": 22000, "founded": 2013, "record": "28:15:00", "record_holder": "Various", "note": "6-day stage race to Everest Base Camp and beyond"},
]

# =====================================================================
# 9. CITY RUNNING ROUTES
# =====================================================================
CITY_RUNNING_ROUTES = [
    {"name": "Central Park Loop", "city": "New York", "country": "USA", "lat": 40.7829, "lon": -73.9654, "distance_km": 9.7, "surface": "Paved path", "highlights": "Reservoir, Great Lawn, Bethesda Fountain", "note": "Iconic NYC running loop, millions of runners annually"},
    {"name": "Thames Path", "city": "London", "country": "UK", "lat": 51.5014, "lon": -0.1195, "distance_km": 12, "surface": "Mixed paved/path", "highlights": "Big Ben, London Eye, Tower Bridge", "note": "Run past London greatest landmarks along the river"},
    {"name": "Tiergarten Loop", "city": "Berlin", "country": "Germany", "lat": 52.5145, "lon": 13.3501, "distance_km": 8, "surface": "Gravel/paved", "highlights": "Brandenburg Gate, Victory Column, canals", "note": "Green heart of Berlin, flat and scenic"},
    {"name": "Lakefront Trail", "city": "Chicago", "country": "USA", "lat": 41.8959, "lon": -87.6163, "distance_km": 29, "surface": "Paved", "highlights": "Navy Pier, Soldier Field, skyline views", "note": "29km of uninterrupted lakeside running"},
    {"name": "Bois de Boulogne", "city": "Paris", "country": "France", "lat": 48.8620, "lon": 2.2489, "distance_km": 10, "surface": "Gravel/paved", "highlights": "Lakes, gardens, Roland Garros nearby", "note": "Parisian escape with forested trails"},
    {"name": "Imperial Palace Loop", "city": "Tokyo", "country": "Japan", "lat": 35.6852, "lon": 139.7528, "distance_km": 5, "surface": "Sidewalk", "highlights": "Imperial Palace, moats, gardens", "note": "Japan most popular running route, runner culture hub"},
    {"name": "Bondi to Coogee", "city": "Sydney", "country": "Australia", "lat": -33.8915, "lon": 151.2767, "distance_km": 6, "surface": "Coastal path", "highlights": "Bondi Beach, Bronte, cliffside views", "note": "Spectacular ocean coastal run"},
    {"name": "Stanley Park Seawall", "city": "Vancouver", "country": "Canada", "lat": 49.2943, "lon": -123.1417, "distance_km": 10, "surface": "Paved", "highlights": "Mountains, ocean, totem poles, Lions Gate Bridge", "note": "One of the most scenic urban runs in the world"},
    {"name": "Ibirapuera Park", "city": "Sao Paulo", "country": "Brazil", "lat": -23.5874, "lon": -46.6576, "distance_km": 7, "surface": "Paved", "highlights": "Modernist architecture, lake, museums", "note": "Sao Paulo running hub, busy at dawn and dusk"},
    {"name": "Retiro Park", "city": "Madrid", "country": "Spain", "lat": 40.4153, "lon": -3.6845, "distance_km": 6, "surface": "Gravel/paved", "highlights": "Crystal Palace, rose garden, lake", "note": "Royal park running in the heart of Madrid"},
    {"name": "Table Mountain Pipeline", "city": "Cape Town", "country": "South Africa", "lat": -33.9628, "lon": 18.4098, "distance_km": 8, "surface": "Trail", "highlights": "Mountain views, fynbos, ravines", "note": "Contour path with city and ocean panoramas"},
    {"name": "Han River Trail", "city": "Seoul", "country": "South Korea", "lat": 37.5279, "lon": 126.9341, "distance_km": 40, "surface": "Paved", "highlights": "River parks, bridges, Yeouido", "note": "Extensive riverside paths through the entire city"},
    {"name": "Champ de Mars", "city": "Paris", "country": "France", "lat": 48.8560, "lon": 2.2980, "distance_km": 4, "surface": "Gravel", "highlights": "Eiffel Tower, Ecole Militaire", "note": "Run with the Eiffel Tower as your backdrop"},
    {"name": "Foro Italico / Lungotevere", "city": "Rome", "country": "Italy", "lat": 41.9283, "lon": 12.4578, "distance_km": 10, "surface": "Paved", "highlights": "Tiber River, Vatican views, Olympic stadium", "note": "Riverside run past ancient and modern Rome"},
    {"name": "Prater Hauptallee", "city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.4057, "distance_km": 4.4, "surface": "Asphalt", "highlights": "Ferris wheel, chestnut trees, park", "note": "Vienna classic running avenue, arrow-straight"},
    {"name": "Vondelpark", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3579, "lon": 4.8686, "distance_km": 3.3, "surface": "Paved", "highlights": "Open-air theater, ponds, rose garden", "note": "Amsterdam most popular running spot"},
    {"name": "Copacabana Promenade", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9711, "lon": -43.1823, "distance_km": 6, "surface": "Boardwalk/sand", "highlights": "Beach, Sugarloaf views, Ipanema", "note": "Iconic beachfront running with mountain backdrop"},
    {"name": "Marina Bay", "city": "Singapore", "country": "Singapore", "lat": 1.2809, "lon": 103.8584, "distance_km": 5, "surface": "Boardwalk", "highlights": "Marina Bay Sands, Gardens by the Bay, skyline", "note": "Futuristic waterfront run in the tropics"},
    {"name": "Chapultepec Park", "city": "Mexico City", "country": "Mexico", "lat": 19.4200, "lon": -99.1896, "distance_km": 8, "surface": "Paved/trail", "highlights": "Castle, zoo, museums, ancient trees", "note": "Largest urban park in Latin America for running"},
    {"name": "Englischer Garten", "city": "Munich", "country": "Germany", "lat": 48.1642, "lon": 11.6055, "distance_km": 12, "surface": "Gravel/grass", "highlights": "Chinese tower, surfers on Eisbach, beer gardens", "note": "One of Europe largest urban parks"},
    {"name": "Phoenix Park", "city": "Dublin", "country": "Ireland", "lat": 53.3558, "lon": -6.3298, "distance_km": 11, "surface": "Road/grass", "highlights": "Deer herds, Magazine Fort, Papal Cross", "note": "Europe largest enclosed urban park with wild deer"},
    {"name": "Frogner / Vigeland Park", "city": "Oslo", "country": "Norway", "lat": 59.9271, "lon": 10.7008, "distance_km": 5, "surface": "Gravel/paved", "highlights": "Vigeland sculptures, fountain, rose garden", "note": "Run among 200+ Gustav Vigeland sculptures"},
    {"name": "Kings Park", "city": "Perth", "country": "Australia", "lat": -31.9622, "lon": 115.8420, "distance_km": 6, "surface": "Paved/trail", "highlights": "Swan River views, botanic garden, war memorial", "note": "Hilltop park overlooking Perth and the river"},
    {"name": "Gorky Park to Sparrow Hills", "city": "Moscow", "country": "Russia", "lat": 55.7298, "lon": 37.6011, "distance_km": 10, "surface": "Paved/path", "highlights": "Moscow River, MSU viewpoint, park sculptures", "note": "Moscow premier running route along the river"},
    {"name": "East Coast Park", "city": "Singapore", "country": "Singapore", "lat": 1.3008, "lon": 103.9120, "distance_km": 15, "surface": "Paved", "highlights": "Beach, cycling path, hawker centres", "note": "Flat coastal route popular for long runs"},
]

# =====================================================================
# 10. RUNNING MUSEUMS & HALL OF FAME
# =====================================================================
RUNNING_MUSEUMS = [
    {"name": "National Distance Running Hall of Fame", "city": "Utica", "country": "USA", "lat": 43.1009, "lon": -75.2327, "founded": 1998, "type": "Hall of Fame", "highlights": "Boilermaker Road Race history, inductee exhibits", "note": "Honors American distance running legends"},
    {"name": "Olympic Museum", "city": "Lausanne", "country": "Switzerland", "lat": 46.5080, "lon": 6.6340, "founded": 1993, "type": "Museum", "highlights": "Olympic running artifacts, Jesse Owens spikes, torches", "note": "IOC official museum with extensive athletics collection"},
    {"name": "Ancient Olympia Museum", "city": "Olympia", "country": "Greece", "lat": 37.6388, "lon": 21.6300, "founded": 1982, "type": "Archaeological Museum", "highlights": "Ancient athletic equipment, discus, starting blocks", "note": "Artifacts from 1,000+ years of ancient Olympic Games"},
    {"name": "Nike World Headquarters", "city": "Beaverton", "country": "USA", "lat": 45.5088, "lon": -122.8288, "founded": 1990, "type": "Campus/Museum", "highlights": "Running shoe evolution, athlete tributes, innovation lab", "note": "Not public but campus features running heritage throughout"},
    {"name": "New Balance Archive", "city": "Lawrence", "country": "USA", "lat": 42.7070, "lon": -71.1631, "founded": 2015, "type": "Archive", "highlights": "Historic running shoes, manufacturing history", "note": "Heritage collection of running footwear since 1906"},
    {"name": "Bowerman Track Building", "city": "Eugene", "country": "USA", "lat": 44.0583, "lon": -123.0753, "founded": 2010, "type": "Heritage Site", "highlights": "Bill Bowerman legacy, Oregon track heritage", "note": "TrackTown USA, birthplace of Nike and jogging movement"},
    {"name": "IAAF Heritage Collection", "city": "Monte Carlo", "country": "Monaco", "lat": 43.7384, "lon": 7.4246, "founded": 2019, "type": "Collection", "highlights": "World Athletics heritage, historic medals, records", "note": "World Athletics official heritage displays"},
    {"name": "National Running Centre", "city": "Loughborough", "country": "UK", "lat": 52.7654, "lon": -1.2271, "founded": 2003, "type": "Training/Heritage Centre", "highlights": "British athletics training, historical exhibits", "note": "Center of British endurance running development"},
    {"name": "Pheidippides Statue", "city": "Marathon", "country": "Greece", "lat": 38.1535, "lon": 23.9635, "founded": 2010, "type": "Monument", "highlights": "Statue of legendary runner, Marathon town", "note": "Where the marathon began with Pheidippides legendary run"},
    {"name": "Boston Marathon Museum", "city": "Hopkinton", "country": "USA", "lat": 42.2287, "lon": -71.5226, "founded": 2017, "type": "Museum", "highlights": "Boston Marathon history, start line memorabilia", "note": "At the historic start line of the world oldest annual marathon"},
    {"name": "Zatopek Memorial", "city": "Koprivnice", "country": "Czech Republic", "lat": 49.5944, "lon": 18.1447, "founded": 2002, "type": "Memorial", "highlights": "Emil Zatopek birthplace, memorial statue", "note": "Honors the greatest distance runner of the 20th century"},
    {"name": "Paavo Nurmi Museum", "city": "Turku", "country": "Finland", "lat": 60.4518, "lon": 22.2666, "founded": 1997, "type": "Museum", "highlights": "Flying Finn memorabilia, Olympic medals, training records", "note": "Dedicated to the legendary 9-time Olympic gold medalist"},
    {"name": "Iffley Road Track", "city": "Oxford", "country": "UK", "lat": 51.7440, "lon": -1.2260, "founded": 1876, "type": "Historic Track", "highlights": "Where Roger Bannister broke 4-minute mile (1954)", "note": "The most famous running track in history"},
    {"name": "Comrades Marathon Museum", "city": "Pietermaritzburg", "country": "South Africa", "lat": -29.6006, "lon": 30.3794, "founded": 2001, "type": "Museum", "highlights": "100 years of Comrades history, Arthur Newton memorabilia", "note": "World oldest ultramarathon archive and exhibits"},
    {"name": "Tokyo National Stadium Museum", "city": "Tokyo", "country": "Japan", "lat": 35.6779, "lon": 139.7136, "founded": 2020, "type": "Museum", "highlights": "Japanese running heritage, Olympic history", "note": "Ekiden and marathon culture exhibits"},
    {"name": "Marathon Battlefield & Tumulus", "city": "Marathon", "country": "Greece", "lat": 38.1170, "lon": 23.9715, "founded": "490 BC site", "type": "Archaeological Site", "highlights": "Burial mound of the 192 Athenian fallen, battlefield", "note": "Where the legendary run to Athens originated after battle"},
    {"name": "Iten Running Center", "city": "Iten", "country": "Kenya", "lat": 0.6696, "lon": 35.5080, "founded": 2010, "type": "Training Center/Heritage", "highlights": "Home of Champions, Kenyan running legacy", "note": "The world capital of distance running at 2,400m altitude"},
    {"name": "Bekoji Running Heritage", "city": "Bekoji", "country": "Ethiopia", "lat": 7.5327, "lon": 39.2534, "founded": 2000, "type": "Heritage Town", "highlights": "Birthplace of Tirunesh Dibaba, Kenenisa Bekele, Derartu Tulu", "note": "Tiny town that produced more Olympic gold medalists than most countries"},
    {"name": "Pre's Rock", "city": "Eugene", "country": "USA", "lat": 44.0390, "lon": -123.0460, "founded": 1975, "type": "Memorial", "highlights": "Memorial to Steve Prefontaine at crash site", "note": "Pilgrimage site for runners honoring Pre's legacy"},
    {"name": "Haile Gebrselassie Museum", "city": "Addis Ababa", "country": "Ethiopia", "lat": 9.0054, "lon": 38.7636, "founded": 2015, "type": "Museum", "highlights": "Olympic medals, world records, running shoes", "note": "Personal museum of the Ethiopian running legend"},
    {"name": "Bannister Mile Track Plaque", "city": "Oxford", "country": "UK", "lat": 51.7440, "lon": -1.2260, "founded": 2004, "type": "Plaque/Memorial", "highlights": "50th anniversary plaque of sub-4 mile", "note": "Commemorates May 6, 1954 - the day the impossible happened"},
    {"name": "Kipchoge 1:59 Challenge Site", "city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738, "founded": 2019, "type": "Historic Site", "highlights": "Prater park where Kipchoge broke 2-hour marathon", "note": "Where Eliud Kipchoge ran 1:59:40, breaking the 2-hour barrier"},
    {"name": "Roger Bannister Track (renamed)", "city": "Oxford", "country": "UK", "lat": 51.7440, "lon": -1.2260, "founded": 2019, "type": "Renamed Track", "highlights": "Officially renamed to honor Sir Roger Bannister", "note": "Iffley Road track officially renamed after Bannister's death"},
    {"name": "Western States Museum", "city": "Auburn", "country": "USA", "lat": 38.8966, "lon": -121.0769, "founded": 2005, "type": "Museum", "highlights": "Western States 100 history, Gordy Ainsleigh legacy", "note": "History of the world most prestigious 100-mile trail race"},
    {"name": "Berlin Wall Marathon Monument", "city": "Berlin", "country": "Germany", "lat": 52.5145, "lon": 13.3501, "founded": 2014, "type": "Monument", "highlights": "Marathon course along former Berlin Wall route", "note": "Commemorates how the Berlin Marathon crossed the Wall after reunification"},
]


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
def _build_map(data, lat_key="lat", lon_key="lon", name_key="name", popup_fn=None, zoom=2, center=None):
    """Build a folium dark-themed map with markers."""
    if center is None:
        avg_lat = sum(d[lat_key] for d in data) / len(data)
        avg_lon = sum(d[lon_key] for d in data) / len(data)
        center = [avg_lat, avg_lon]
    m = folium.Map(location=center, zoom_start=zoom, tiles=DARK_TILES)
    for item in data:
        popup_html = popup_fn(item) if popup_fn else f"<b>{html_module.escape(str(item[name_key]))}</b>"
        folium.Marker(
            location=[item[lat_key], item[lon_key]],
            popup=folium.Popup(popup_html, max_width=340),
            tooltip=html_module.escape(str(item[name_key])),
            icon=folium.Icon(color="red", icon="info-sign"),
        ).add_to(m)
    return m


def _show_map(m):
    """Render a folium map in Streamlit."""
    st_html(m._repr_html_(), height=500)


def _show_download(df, filename):
    """Show a CSV download button."""
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=filename,
        mime="text/csv",
    )


# =====================================================================
# MODE RENDERERS
# =====================================================================

def _render_world_major_marathons():
    data = WORLD_MAJOR_MARATHONS
    cols = st.columns(4)
    cols[0].metric("Total Marathons", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    oldest = min(data, key=lambda x: x["founded"])
    cols[2].metric("Oldest", f"{oldest['name']} ({oldest['founded']})")
    cols[3].metric("Avg Finishers", f"{int(sum(d['finishers_approx'] for d in data) / len(data)):,}")

    def popup_fn(d):
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(d['city'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Founded:</b> {d['founded']}<br>"
            f"<b>Month:</b> {html_module.escape(d['month'])}<br>"
            f"<b>Distance:</b> {html_module.escape(d['distance'])}<br>"
            f"<b>Course Record:</b> {html_module.escape(d['record'])} ({html_module.escape(d['record_holder'])})<br>"
            f"<b>Approx Finishers:</b> {d['finishers_approx']:,}<br>"
            f"<b>Elevation Gain:</b> {d['elevation_gain_m']}m<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=2)
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "world_major_marathons.csv")


def _render_ultramarathon_trails():
    data = ULTRAMARATHON_TRAILS
    cols = st.columns(4)
    cols[0].metric("Ultra Races", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    cols[2].metric("Max Distance", f"{max(d['distance_km'] for d in data)} km")
    cols[3].metric("Max Elevation", f"{max(d['elevation_gain_m'] for d in data):,}m")

    def popup_fn(d):
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>Location:</b> {html_module.escape(d['location'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Distance:</b> {d['distance_km']} km<br>"
            f"<b>Elevation Gain:</b> {d['elevation_gain_m']:,}m<br>"
            f"<b>Founded:</b> {d['founded']}<br>"
            f"<b>Terrain:</b> {html_module.escape(d['terrain'])}<br>"
            f"<b>Record:</b> {html_module.escape(d['record'])} ({html_module.escape(d['record_holder'])})<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=2)
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "ultramarathon_trails.csv")


def _render_olympic_running_venues():
    data = OLYMPIC_RUNNING_VENUES
    cols = st.columns(4)
    cols[0].metric("Olympic Venues", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    cols[2].metric("Span", f"{min(d['year'] for d in data)}-{max(d['year'] for d in data)}")
    cols[3].metric("Cities", len(set(d["city"] for d in data)))

    def popup_fn(d):
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(d['city'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Year:</b> {d['year']}<br>"
            f"<b>Event:</b> {html_module.escape(d['event'])}<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=2)
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "olympic_running_venues.csv")


def _render_trail_running_paradises():
    data = TRAIL_RUNNING_PARADISES
    cols = st.columns(4)
    cols[0].metric("Trail Paradises", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    total_km = sum(d["distance_km"] for d in data)
    cols[2].metric("Total Trail km", f"{total_km:,}")
    terrains = len(set(d["terrain"] for d in data))
    cols[3].metric("Terrain Types", terrains)

    def popup_fn(d):
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>Location:</b> {html_module.escape(d['location'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Terrain:</b> {html_module.escape(d['terrain'])}<br>"
            f"<b>Best Month:</b> {html_module.escape(d['best_month'])}<br>"
            f"<b>Signature Trail:</b> {html_module.escape(d['signature_trail'])} ({d['distance_km']} km)<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=2)
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "trail_running_paradises.csv")


def _render_parkrun_locations():
    data = PARKRUN_LOCATIONS
    cols = st.columns(4)
    cols[0].metric("Parkrun Locations", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    total_runners = sum(d["avg_runners"] for d in data)
    cols[2].metric("Total Weekly Runners", f"{total_runners:,}")
    cols[3].metric("Oldest", f"{min(d['founded'] for d in data)}")

    def popup_fn(d):
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(d['city'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Founded:</b> {d['founded']}<br>"
            f"<b>Avg Weekly Runners:</b> {d['avg_runners']}<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=2)
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "parkrun_locations.csv")


def _render_ancient_olympic_sites():
    data = ANCIENT_OLYMPIC_SITES
    cols = st.columns(4)
    cols[0].metric("Ancient Sites", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    greece_count = sum(1 for d in data if d["country"] == "Greece")
    cols[2].metric("Greek Sites", greece_count)
    turkey_count = sum(1 for d in data if d["country"] == "Turkey")
    cols[3].metric("Turkey Sites", turkey_count)

    def popup_fn(d):
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>Location:</b> {html_module.escape(d['location'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Period:</b> {html_module.escape(d['period'])}<br>"
            f"<b>Events:</b> {html_module.escape(d['events'])}<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=4, center=[38.0, 25.0])
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "ancient_olympic_sites.csv")


def _render_ironman_venues():
    data = IRONMAN_VENUES
    cols = st.columns(4)
    cols[0].metric("Ironman Venues", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    oldest = min(data, key=lambda x: x["founded"])
    cols[2].metric("Oldest", f"{oldest['city']} ({oldest['founded']})")
    cols[3].metric("Total Distance", f"{data[0]['swim_km'] + data[0]['bike_km'] + data[0]['run_km']:.1f} km")

    def popup_fn(d):
        total = d['swim_km'] + d['bike_km'] + d['run_km']
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(d['city'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Founded:</b> {d['founded']}<br>"
            f"<b>Swim:</b> {d['swim_km']} km | <b>Bike:</b> {d['bike_km']} km | <b>Run:</b> {d['run_km']} km<br>"
            f"<b>Total:</b> {total:.1f} km<br>"
            f"<b>Record:</b> {html_module.escape(d['record'])} ({html_module.escape(d['record_holder'])})<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=2)
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "ironman_venues.csv")


def _render_mountain_running_races():
    data = MOUNTAIN_RUNNING_RACES
    cols = st.columns(4)
    cols[0].metric("Mountain Races", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    cols[2].metric("Max Elevation Gain", f"{max(d['elevation_gain_m'] for d in data):,}m")
    avg_dist = sum(d["distance_km"] for d in data) / len(data)
    cols[3].metric("Avg Distance", f"{avg_dist:.1f} km")

    def popup_fn(d):
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>Location:</b> {html_module.escape(d['location'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Distance:</b> {d['distance_km']} km<br>"
            f"<b>Elevation Gain:</b> {d['elevation_gain_m']:,}m<br>"
            f"<b>Founded:</b> {d['founded']}<br>"
            f"<b>Record:</b> {html_module.escape(d['record'])} ({html_module.escape(d['record_holder'])})<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=2)
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "mountain_running_races.csv")


def _render_city_running_routes():
    data = CITY_RUNNING_ROUTES
    cols = st.columns(4)
    cols[0].metric("City Routes", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    total_km = sum(d["distance_km"] for d in data)
    cols[2].metric("Total Route km", f"{total_km:.1f}")
    cols[3].metric("Avg Route Length", f"{total_km / len(data):.1f} km")

    def popup_fn(d):
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(d['city'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Distance:</b> {d['distance_km']} km<br>"
            f"<b>Surface:</b> {html_module.escape(d['surface'])}<br>"
            f"<b>Highlights:</b> {html_module.escape(d['highlights'])}<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=2)
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "city_running_routes.csv")


def _render_running_museums():
    data = RUNNING_MUSEUMS
    cols = st.columns(4)
    cols[0].metric("Museums & Memorials", len(data))
    cols[1].metric("Countries", len(set(d["country"] for d in data)))
    types = set(d["type"] for d in data)
    cols[2].metric("Venue Types", len(types))
    usa_count = sum(1 for d in data if d["country"] == "USA")
    cols[3].metric("USA Venues", usa_count)

    def popup_fn(d):
        return (
            f"<div style='font-family:sans-serif;min-width:260px;'>"
            f"<b style='font-size:14px;'>{html_module.escape(d['name'])}</b><br>"
            f"<b>City:</b> {html_module.escape(d['city'])}, {html_module.escape(d['country'])}<br>"
            f"<b>Founded:</b> {html_module.escape(str(d['founded']))}<br>"
            f"<b>Type:</b> {html_module.escape(d['type'])}<br>"
            f"<b>Highlights:</b> {html_module.escape(d['highlights'])}<br>"
            f"<em>{html_module.escape(d['note'])}</em></div>"
        )

    m = _build_map(data, popup_fn=popup_fn, zoom=2)
    _show_map(m)
    df = pd.DataFrame(data)
    st.dataframe(df, use_container_width=True)
    _show_download(df, "running_museums.csv")


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================

def render_marathon_maps_tab():
    """Main entry point for the Marathon & Running Explorer tab."""
    st.markdown(
        '<div class="tab-header pink"><h4>Marathon & Running Explorer</h4>'
        '<p>World marathons, ultramarathons, historic running routes & athletic heritage</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        [
            "World Major Marathons",
            "Ultramarathon Trails",
            "Historic Olympic Running Venues",
            "Trail Running Paradises",
            "Parkrun Locations Worldwide",
            "Ancient Olympic Sites",
            "Ironman Triathlon Venues",
            "Mountain Running Races",
            "City Running Routes",
            "Running Museums & Hall of Fame",
        ],
        key="marathon_maps_mode",
    )

    st.markdown("---")

    if mode == "World Major Marathons":
        _render_world_major_marathons()
    elif mode == "Ultramarathon Trails":
        _render_ultramarathon_trails()
    elif mode == "Historic Olympic Running Venues":
        _render_olympic_running_venues()
    elif mode == "Trail Running Paradises":
        _render_trail_running_paradises()
    elif mode == "Parkrun Locations Worldwide":
        _render_parkrun_locations()
    elif mode == "Ancient Olympic Sites":
        _render_ancient_olympic_sites()
    elif mode == "Ironman Triathlon Venues":
        _render_ironman_venues()
    elif mode == "Mountain Running Races":
        _render_mountain_running_races()
    elif mode == "City Running Routes":
        _render_city_running_routes()
    elif mode == "Running Museums & Hall of Fame":
        _render_running_museums()
