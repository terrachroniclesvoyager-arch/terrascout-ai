# -*- coding: utf-8 -*-
"""
Circus & Street Performance Maps module for TerraScout AI.
Hardcoded datasets of circus venues, street performance capitals, magic schools,
carnival heritage, puppet theaters, acrobatic schools, clown festivals,
fire performance traditions, and vaudeville theaters worldwide.
All data is embedded - no API key needed.
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
from streamlit.components.v1 import html as st_html
import html as html_module

# ===================================================================
# THEME CONSTANTS
# ===================================================================
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
ACCENT_COLOR = "#ec4899"
MUTED_COLOR = "#5a6580"

MODE_COLORS = {
    "Historic Circus Venues": "#ec4899",
    "Cirque du Soleil & Modern Circus": "#8b5cf6",
    "Street Performance Capitals": "#06b6d4",
    "Magic & Illusion Schools": "#f59e0b",
    "Carnival & Mardi Gras Traditions": "#10b981",
    "Puppet Theater Heritage": "#f97316",
    "Acrobatic & Gymnastic Schools": "#ef4444",
    "Clown & Comedy Festivals": "#facc15",
    "Fire Performance Traditions": "#e11d48",
    "Vaudeville & Variety Theater": "#a855f7",
}

# ===================================================================
# DATA: HISTORIC CIRCUS VENUES (30)
# ===================================================================
HISTORIC_CIRCUS = [
    {"name": "Circus Maximus", "city": "Rome", "country": "Italy", "lat": 41.8860, "lon": 12.4853, "founded": "600 BC", "type": "Ancient Arena", "capacity": 250000, "description": "Largest ancient Roman chariot racing and mass entertainment venue"},
    {"name": "Astley's Amphitheatre", "city": "London", "country": "UK", "lat": 51.5025, "lon": -0.1100, "founded": "1773", "type": "Ring Circus", "capacity": 3000, "description": "Philip Astley's original circus ring, birthplace of modern circus"},
    {"name": "Cirque d'Hiver", "city": "Paris", "country": "France", "lat": 48.8650, "lon": 2.3672, "founded": "1852", "type": "Permanent Circus", "capacity": 1800, "description": "Winter Circus - one of the oldest permanent circus buildings still active"},
    {"name": "Hippodrome de l'Alma", "city": "Paris", "country": "France", "lat": 48.8640, "lon": 2.3010, "founded": "1877", "type": "Hippodrome", "capacity": 5000, "description": "Grand Parisian hippodrome for equestrian and acrobatic spectacles"},
    {"name": "Circus Krone Building", "city": "Munich", "country": "Germany", "lat": 48.1445, "lon": 11.5535, "founded": "1919", "type": "Permanent Circus", "capacity": 3000, "description": "Europe's largest permanent circus building, home of Circus Krone"},
    {"name": "Ringling Bros. Winter Quarters", "city": "Sarasota", "country": "USA", "lat": 27.3365, "lon": -82.5307, "founded": "1927", "type": "Winter Quarters", "capacity": 0, "description": "Winter home of the Greatest Show on Earth, now a museum"},
    {"name": "Moscow State Circus", "city": "Moscow", "country": "Russia", "lat": 55.7642, "lon": 37.5930, "founded": "1880", "type": "State Circus", "capacity": 3400, "description": "Nikulin Moscow Circus on Tsvetnoy Boulevard, legendary venue"},
    {"name": "Blackpool Tower Circus", "city": "Blackpool", "country": "UK", "lat": 53.8159, "lon": -3.0553, "founded": "1894", "type": "Tower Circus", "capacity": 1500, "description": "Permanent circus inside Blackpool Tower with water spectacles"},
    {"name": "Big Apple Circus Tent", "city": "New York", "country": "USA", "lat": 40.7712, "lon": -73.9740, "founded": "1977", "type": "Tent Circus", "capacity": 1700, "description": "Intimate one-ring circus that performed at Lincoln Center for decades"},
    {"name": "Barnum's American Museum", "city": "New York", "country": "USA", "lat": 40.7115, "lon": -74.0096, "founded": "1841", "type": "Museum/Show", "capacity": 3000, "description": "P.T. Barnum's original entertainment museum on Broadway"},
    {"name": "Circo Price", "city": "Madrid", "country": "Spain", "lat": 40.4100, "lon": -3.6970, "founded": "1853", "type": "Permanent Circus", "capacity": 1800, "description": "Teatro Circo Price, Madrid's historic circus and performance venue"},
    {"name": "Circus Roncalli Home", "city": "Cologne", "country": "Germany", "lat": 50.9413, "lon": 6.9583, "founded": "1976", "type": "Poetic Circus", "capacity": 1500, "description": "Bernhard Paul's poetic circus using holograms instead of animals"},
    {"name": "Billy Smart's Circus HQ", "city": "Windsor", "country": "UK", "lat": 51.4816, "lon": -0.6044, "founded": "1946", "type": "Touring Circus", "capacity": 6000, "description": "One of Britain's most famous big top touring circuses"},
    {"name": "Zippos Circus Base", "city": "London", "country": "UK", "lat": 51.4975, "lon": -0.1357, "founded": "1986", "type": "Touring Circus", "capacity": 1000, "description": "Britain's leading touring big top circus, animal-free since 2003"},
    {"name": "Cirque Phenix", "city": "Paris", "country": "France", "lat": 48.8367, "lon": 2.3876, "founded": "1999", "type": "Touring Circus", "capacity": 6000, "description": "Grand circus spectacular at Pelouse de Reuilly each winter"},
    {"name": "Circus Oz Home", "city": "Melbourne", "country": "Australia", "lat": -37.8057, "lon": 144.9854, "founded": "1978", "type": "Contemporary", "capacity": 1200, "description": "Pioneering Australian contemporary circus with rock-and-roll energy"},
    {"name": "Gran Circo Mundial", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6131, "lon": -58.3772, "founded": "1960", "type": "Touring Circus", "capacity": 2500, "description": "Major South American touring circus with Latin performance traditions"},
    {"name": "Chinese National Circus Home", "city": "Beijing", "country": "China", "lat": 39.9179, "lon": 116.4070, "founded": "1953", "type": "Acrobatic", "capacity": 2000, "description": "China's premier acrobatic troupe showcasing 2000+ years of tradition"},
    {"name": "Circus Theater Scheveningen", "city": "The Hague", "country": "Netherlands", "lat": 52.1068, "lon": 4.2768, "founded": "1904", "type": "Theater/Circus", "capacity": 1800, "description": "Historic Dutch seaside circus theater still hosting grand shows"},
    {"name": "Cirkus Summarum Venue", "city": "Copenhagen", "country": "Denmark", "lat": 55.6739, "lon": 12.5691, "founded": "2002", "type": "Family Circus", "capacity": 1500, "description": "Popular Danish family circus performing in Dyrehaven park"},
    {"name": "Hippodrome Circus", "city": "Great Yarmouth", "country": "UK", "lat": 52.6064, "lon": 1.7310, "founded": "1903", "type": "Water Circus", "capacity": 900, "description": "Only surviving complete circus building in Britain with water spectacle"},
    {"name": "Circus World Museum", "city": "Baraboo", "country": "USA", "lat": 43.4700, "lon": -89.7468, "founded": "1959", "type": "Museum", "capacity": 800, "description": "On the original Ringling Bros. winter quarters site in Wisconsin"},
    {"name": "Cirque Royal", "city": "Brussels", "country": "Belgium", "lat": 50.8531, "lon": 4.3621, "founded": "1878", "type": "Permanent Circus", "capacity": 2000, "description": "Historic circus building repurposed as concert and show venue"},
    {"name": "Moscow Circus on Vernadsky", "city": "Moscow", "country": "Russia", "lat": 55.6910, "lon": 37.5420, "founded": "1971", "type": "State Circus", "capacity": 3400, "description": "The Great Moscow Circus with transformable arena and high tech"},
    {"name": "Cirkus Arena", "city": "Aarslev", "country": "Denmark", "lat": 55.3667, "lon": 10.2833, "founded": "1955", "type": "Touring Circus", "capacity": 2200, "description": "Scandinavia's largest touring circus, family-run for generations"},
    {"name": "Shanghai Circus World", "city": "Shanghai", "country": "China", "lat": 31.2832, "lon": 121.4600, "founded": "1999", "type": "Modern Arena", "capacity": 1650, "description": "Permanent acrobatic circus arena hosting ERA Intersection of Time"},
    {"name": "Circo Atayde", "city": "Mexico City", "country": "Mexico", "lat": 19.4260, "lon": -99.1320, "founded": "1888", "type": "Touring Circus", "capacity": 3000, "description": "Oldest circus in the Americas, family-run for over 130 years"},
    {"name": "Circus Flora Home", "city": "St. Louis", "country": "USA", "lat": 38.6340, "lon": -90.2210, "founded": "1986", "type": "One-Ring", "capacity": 1000, "description": "Intimate one-ring circus in Grand Center arts district"},
    {"name": "Palazzo Columbian", "city": "Berlin", "country": "Germany", "lat": 52.5163, "lon": 13.3905, "founded": "1995", "type": "Dinner Circus", "capacity": 600, "description": "Spiegeltent dinner-show circus combining acrobatics and gastronomy"},
    {"name": "Circo Raluy", "city": "Barcelona", "country": "Spain", "lat": 41.3770, "lon": 2.1866, "founded": "1911", "type": "Classic Circus", "capacity": 1200, "description": "Spanish family circus with vintage charm and traditional artistry"},
]

# ===================================================================
# DATA: CIRQUE DU SOLEIL & MODERN CIRCUS (30)
# ===================================================================
MODERN_CIRCUS = [
    {"name": "Cirque du Soleil HQ", "city": "Montreal", "country": "Canada", "lat": 45.5580, "lon": -73.5510, "founded": 1984, "type": "New Circus HQ", "show": "Headquarters", "description": "International headquarters where all Cirque shows are created and rehearsed"},
    {"name": "O Theatre - Bellagio", "city": "Las Vegas", "country": "USA", "lat": 36.1129, "lon": -115.1765, "founded": 1998, "type": "Aquatic Show", "show": "O", "description": "Permanent water-based Cirque du Soleil show with 1.5M gallon pool"},
    {"name": "Mystere - Treasure Island", "city": "Las Vegas", "country": "USA", "lat": 36.1249, "lon": -115.1717, "founded": 1993, "type": "Resident Show", "show": "Mystere", "description": "First permanent Cirque du Soleil show in Las Vegas"},
    {"name": "KA Theatre - MGM Grand", "city": "Las Vegas", "country": "USA", "lat": 36.1025, "lon": -115.1689, "founded": 2004, "type": "Battle Theater", "show": "KA", "description": "Martial arts themed show with a rotating 360-degree stage platform"},
    {"name": "The Beatles LOVE - Mirage", "city": "Las Vegas", "country": "USA", "lat": 36.1211, "lon": -115.1742, "founded": 2006, "type": "Music Tribute", "show": "LOVE", "description": "Beatles-themed circus show with remixed George Martin soundtrack"},
    {"name": "Zumanity Theatre - NYNY", "city": "Las Vegas", "country": "USA", "lat": 36.1023, "lon": -115.1745, "founded": 2003, "type": "Cabaret", "show": "Zumanity", "description": "Sensual adult cabaret by Cirque du Soleil (closed 2020)"},
    {"name": "La Nouba - Disney Springs", "city": "Orlando", "country": "USA", "lat": 28.3697, "lon": -81.5185, "founded": 1998, "type": "Family Show", "show": "La Nouba", "description": "Cirque du Soleil's long-running family show at Walt Disney World"},
    {"name": "TOTEM Big Top Site", "city": "London", "country": "UK", "lat": 51.5032, "lon": -0.0195, "founded": 2010, "type": "Touring Show", "show": "TOTEM", "description": "Evolution-themed touring show performed under the Grand Chapiteau"},
    {"name": "Chamäleon Theatre", "city": "Berlin", "country": "Germany", "lat": 52.5242, "lon": 13.3958, "founded": 2004, "type": "New Circus", "show": "Various", "description": "Intimate contemporary circus in restored Hackesche Hofe ballroom"},
    {"name": "Circa Contemporary Circus", "city": "Brisbane", "country": "Australia", "lat": -27.4650, "lon": 153.0260, "founded": 2004, "type": "Contemporary", "show": "Various", "description": "Australian troupe blending acrobatics and physical theater"},
    {"name": "Les 7 Doigts de la Main", "city": "Montreal", "country": "Canada", "lat": 45.5230, "lon": -73.5880, "founded": 2002, "type": "New Circus", "show": "Various", "description": "Seven Fingers collective pushing circus toward intimate storytelling"},
    {"name": "NoFit State Circus", "city": "Cardiff", "country": "UK", "lat": 51.4750, "lon": -3.1784, "founded": 1986, "type": "Contemporary", "show": "Various", "description": "Wales-based contemporary circus creating immersive big top shows"},
    {"name": "Cie XY", "city": "Lille", "country": "France", "lat": 50.6320, "lon": 3.0586, "founded": 2005, "type": "Acrobatic", "show": "Various", "description": "French acrobatic collective specializing in human pyramids and portee"},
    {"name": "Cirque Eloize", "city": "Montreal", "country": "Canada", "lat": 45.5150, "lon": -73.5610, "founded": 1993, "type": "New Circus", "show": "Various", "description": "Montreal-based cirque mixing circus arts with theater and dance"},
    {"name": "Teatro ZinZanni", "city": "Seattle", "country": "USA", "lat": 47.6134, "lon": -122.3417, "founded": 1998, "type": "Dinner Circus", "show": "Love Chaos Dinner", "description": "Spiegeltent dinner-theater circus combining fine dining and chaos"},
    {"name": "Phare Cambodian Circus", "city": "Siem Reap", "country": "Cambodia", "lat": 13.3530, "lon": 103.8600, "founded": 2013, "type": "Social Circus", "show": "Various", "description": "Cambodian circus using performance to tell Khmer cultural stories"},
    {"name": "Spiegelworld", "city": "Las Vegas", "country": "USA", "lat": 36.1162, "lon": -115.1745, "founded": 2006, "type": "Immersive", "show": "Absinthe", "description": "Absinthe and other edgy spiegeltent shows on the Las Vegas Strip"},
    {"name": "Cirkus Cirkoor", "city": "Stockholm", "country": "Sweden", "lat": 59.3466, "lon": 18.0174, "founded": 1995, "type": "Contemporary", "show": "Various", "description": "Sweden's leading contemporary circus company"},
    {"name": "Drawn to Life - Disney Springs", "city": "Orlando", "country": "USA", "lat": 28.3701, "lon": -81.5190, "founded": 2021, "type": "Animation Circus", "show": "Drawn to Life", "description": "Cirque du Soleil and Disney animation collaboration show"},
    {"name": "Gandini Juggling", "city": "London", "country": "UK", "lat": 51.5230, "lon": -0.0888, "founded": 1992, "type": "Juggling", "show": "Various", "description": "World-leading juggling company blending math, rhythm, and dance"},
    {"name": "Gravity & Other Myths", "city": "Adelaide", "country": "Australia", "lat": -34.9270, "lon": 138.5986, "founded": 2009, "type": "Acrobatic", "show": "Backbone/Out of Chaos", "description": "Adelaide troupe known for raw acrobatics without sets or costumes"},
    {"name": "Machine de Cirque", "city": "Quebec City", "country": "Canada", "lat": 46.8120, "lon": -71.2160, "founded": 2013, "type": "New Circus", "show": "Various", "description": "Quebec collective merging circus with Rube Goldberg contraptions"},
    {"name": "Wintergarten Variete", "city": "Berlin", "country": "Germany", "lat": 52.5073, "lon": 13.3680, "founded": 1992, "type": "Variete", "show": "Various", "description": "Revived legendary Berlin variety theater with contemporary circus"},
    {"name": "Archaos", "city": "Marseille", "country": "France", "lat": 43.2965, "lon": 5.3698, "founded": 1986, "type": "Punk Circus", "show": "Various", "description": "Pioneering punk circus using chainsaws and motorcycles in the ring"},
    {"name": "Cirque Plume", "city": "Besancon", "country": "France", "lat": 47.2380, "lon": 6.0240, "founded": 1984, "type": "Poetic Circus", "show": "Various", "description": "Poetic French nouveau cirque company blending music and imagery"},
    {"name": "Svalbard Circus", "city": "Longyearbyen", "country": "Norway", "lat": 78.2232, "lon": 15.6267, "founded": 2015, "type": "Arctic Circus", "show": "Arctic Show", "description": "World's northernmost circus performances in the Arctic"},
    {"name": "Zip Zap Circus School", "city": "Cape Town", "country": "South Africa", "lat": -33.9220, "lon": 18.4210, "founded": 1992, "type": "Social Circus", "show": "Training/Shows", "description": "Social circus school bridging divides in post-apartheid South Africa"},
    {"name": "Circus Abyssinia", "city": "Addis Ababa", "country": "Ethiopia", "lat": 9.0050, "lon": 38.7634, "founded": 2013, "type": "Ethiopian Circus", "show": "Ethiopian Dreams", "description": "First Ethiopian circus to tour internationally"},
    {"name": "Cirque Arlette Gruss", "city": "Paris", "country": "France", "lat": 48.8920, "lon": 2.3430, "founded": 1985, "type": "Classic Circus", "show": "Annual Tour", "description": "Leading French traditional circus with spectacular productions"},
    {"name": "Circus Monti", "city": "Zurich", "country": "Switzerland", "lat": 47.3769, "lon": 8.5417, "founded": 2003, "type": "New Circus", "show": "Various", "description": "Swiss circus merging traditional artistry with modern storytelling"},
]

# ===================================================================
# DATA: STREET PERFORMANCE CAPITALS (30)
# ===================================================================
STREET_PERFORMANCE = [
    {"name": "Covent Garden", "city": "London", "country": "UK", "lat": 51.5117, "lon": -0.1228, "tradition": "Licensed Busking", "era": "1662-present", "specialty": "All genres", "description": "World's most prestigious licensed busking pitch with auditioned performers"},
    {"name": "Place du Tertre", "city": "Paris", "country": "France", "lat": 48.8865, "lon": 2.3408, "tradition": "Artist Quarter", "era": "1800s-present", "specialty": "Portrait artists, mimes", "description": "Montmartre square where street artists and mimes gather daily"},
    {"name": "Las Ramblas", "city": "Barcelona", "country": "Spain", "lat": 41.3810, "lon": 2.1732, "tradition": "Living Statues", "era": "1700s-present", "specialty": "Living statues, musicians", "description": "Iconic promenade famous for elaborate living statues and performers"},
    {"name": "Times Square", "city": "New York", "country": "USA", "lat": 40.7580, "lon": -73.9855, "tradition": "Street Theater", "era": "1900s-present", "specialty": "All genres", "description": "Crossroads of the world with costumed characters and breakdancers"},
    {"name": "Grafton Street", "city": "Dublin", "country": "Ireland", "lat": 53.3414, "lon": -6.2594, "tradition": "Busking", "era": "1700s-present", "specialty": "Musicians, poets", "description": "Where Glen Hansard and Damien Rice launched careers busking"},
    {"name": "Faneuil Hall Marketplace", "city": "Boston", "country": "USA", "lat": 42.3601, "lon": -71.0568, "tradition": "Licensed Pitches", "era": "1742-present", "specialty": "Magicians, jugglers", "description": "Historic marketplace with long tradition of street entertainment"},
    {"name": "Pike Place Market", "city": "Seattle", "country": "USA", "lat": 47.6097, "lon": -122.3422, "tradition": "Busking", "era": "1907-present", "specialty": "Musicians, fish throwers", "description": "Famous market with buskers and the iconic fish-throwing performers"},
    {"name": "Piazza Navona", "city": "Rome", "country": "Italy", "lat": 41.8992, "lon": 12.4731, "tradition": "Commedia dell'Arte", "era": "1500s-present", "specialty": "Mime, caricature artists", "description": "Baroque piazza carrying on centuries of Roman street theater"},
    {"name": "Djemaa el-Fna", "city": "Marrakech", "country": "Morocco", "lat": 31.6258, "lon": -7.9891, "tradition": "Halqa Circle", "era": "1050-present", "specialty": "Storytellers, acrobats, snake charmers", "description": "UNESCO-listed square where halqa circle performances continue daily"},
    {"name": "Circular Quay", "city": "Sydney", "country": "Australia", "lat": -33.8614, "lon": 151.2109, "tradition": "Busking", "era": "1900s-present", "specialty": "Aboriginal performers, musicians", "description": "Sydney harbor busking spot with didgeridoo players and acrobats"},
    {"name": "Temple Bar", "city": "Dublin", "country": "Ireland", "lat": 53.3456, "lon": -6.2643, "tradition": "Street Music", "era": "1600s-present", "specialty": "Trad music, comedy", "description": "Cultural quarter where Irish traditional musicians busk nightly"},
    {"name": "Edinburgh Royal Mile", "city": "Edinburgh", "country": "UK", "lat": 55.9504, "lon": -3.1883, "tradition": "Fringe Festival", "era": "1947-present", "specialty": "All genres", "description": "Home of Edinburgh Fringe, world's largest arts festival with 3000+ acts"},
    {"name": "Venice Beach Boardwalk", "city": "Los Angeles", "country": "USA", "lat": 33.9850, "lon": -118.4695, "tradition": "Boardwalk Acts", "era": "1920s-present", "specialty": "Chainsaw jugglers, body builders", "description": "Eccentric boardwalk with muscle beach and wild street performers"},
    {"name": "Dam Square", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3730, "lon": 4.8932, "tradition": "Busking", "era": "1600s-present", "specialty": "Musicians, living statues", "description": "Central Amsterdam square with international buskers year-round"},
    {"name": "Galway Latin Quarter", "city": "Galway", "country": "Ireland", "lat": 53.2719, "lon": -9.0489, "tradition": "Arts Festival", "era": "1978-present", "specialty": "Comedy, fire acts, music", "description": "Galway Arts Festival turns streets into open-air circus stages"},
    {"name": "Portobello Road", "city": "London", "country": "UK", "lat": 51.5155, "lon": -0.2057, "tradition": "Market Busking", "era": "1800s-present", "specialty": "Musicians, magicians", "description": "Notting Hill market street alive with eclectic buskers on Saturdays"},
    {"name": "Fisherman's Wharf", "city": "San Francisco", "country": "USA", "lat": 37.8080, "lon": -122.4177, "tradition": "Busking", "era": "1900s-present", "specialty": "Bush Man, musicians", "description": "Home of the famous Bush Man and generations of waterfront buskers"},
    {"name": "La Boca - Caminito", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6394, "lon": -58.3635, "tradition": "Tango Street", "era": "1890s-present", "specialty": "Tango dancers, musicians", "description": "Colorful street where tango dancers perform spontaneously"},
    {"name": "Insadong", "city": "Seoul", "country": "South Korea", "lat": 37.5742, "lon": 126.9850, "tradition": "Street Art", "era": "1900s-present", "specialty": "Traditional performers, K-pop buskers", "description": "Art district with traditional Korean performers and modern buskers"},
    {"name": "Jemaa el-Fnaa Night Market", "city": "Marrakech", "country": "Morocco", "lat": 31.6260, "lon": -7.9893, "tradition": "Night Performance", "era": "1000-present", "specialty": "Fire eaters, musicians, storytellers", "description": "After-dark transformation with fire acts, Gnawa musicians, and tales"},
    {"name": "Shibuya Crossing", "city": "Tokyo", "country": "Japan", "lat": 35.6595, "lon": 139.7004, "tradition": "Street Dance", "era": "1990s-present", "specialty": "Breakdance, anime cosplay", "description": "World's busiest crossing doubles as spontaneous performance space"},
    {"name": "Alexanderplatz", "city": "Berlin", "country": "Germany", "lat": 52.5219, "lon": 13.4132, "tradition": "Busking", "era": "1990s-present", "specialty": "Musicians, acrobats", "description": "Post-reunification busking hotspot with diverse international acts"},
    {"name": "Istiklal Avenue", "city": "Istanbul", "country": "Turkey", "lat": 41.0340, "lon": 28.9770, "tradition": "Street Music", "era": "1800s-present", "specialty": "Musicians, dervish performers", "description": "Bustling pedestrian avenue with musicians and whirling performers"},
    {"name": "Mallory Square", "city": "Key West", "country": "USA", "lat": 24.5605, "lon": -81.8086, "tradition": "Sunset Celebration", "era": "1984-present", "specialty": "Fire acts, escape artists, cat circus", "description": "Nightly sunset festival with jugglers, tightrope walkers, and cat shows"},
    {"name": "Plaza Dorrego", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6152, "lon": -58.3700, "tradition": "Tango & Market", "era": "1800s-present", "specialty": "Tango, antique market performers", "description": "San Telmo square with Sunday tango and street performance traditions"},
    {"name": "Charles Bridge", "city": "Prague", "country": "Czech Republic", "lat": 50.0865, "lon": 14.4114, "tradition": "Bridge Busking", "era": "1600s-present", "specialty": "Jazz bands, puppet shows", "description": "Medieval bridge lined with musicians, artists, and puppet shows"},
    {"name": "Meiji Shrine Bridge - Harajuku", "city": "Tokyo", "country": "Japan", "lat": 35.6714, "lon": 139.7023, "tradition": "Cosplay", "era": "1990s-present", "specialty": "Cosplay, street dance", "description": "Harajuku bridge where cosplay culture and street performance merge"},
    {"name": "Place Jacques-Cartier", "city": "Montreal", "country": "Canada", "lat": 45.5075, "lon": -73.5525, "tradition": "Festival Busking", "era": "1800s-present", "specialty": "All genres, Just for Laughs", "description": "Old Montreal square hosting world-class street acts and festivals"},
    {"name": "South Bank", "city": "London", "country": "UK", "lat": 51.5060, "lon": -0.1168, "tradition": "Licensed Busking", "era": "1951-present", "specialty": "All genres", "description": "Thames riverside cultural strip with buskers, skaters, and book stalls"},
    {"name": "Rua Augusta", "city": "Lisbon", "country": "Portugal", "lat": 38.7109, "lon": -9.1375, "tradition": "Busking", "era": "1700s-present", "specialty": "Fado singers, living statues", "description": "Lisbon's main pedestrian street with fado buskers and living statues"},
]

# ===================================================================
# DATA: MAGIC & ILLUSION SCHOOLS (30)
# ===================================================================
MAGIC_SCHOOLS = [
    {"name": "The Magic Castle", "city": "Hollywood", "country": "USA", "lat": 34.1015, "lon": -118.3407, "founded": 1963, "type": "Private Club", "specialty": "Close-up & Stage Magic", "description": "Exclusive clubhouse for the Academy of Magical Arts, global mecca for magicians"},
    {"name": "The Magic Circle HQ", "city": "London", "country": "UK", "lat": 51.5287, "lon": -0.1177, "founded": 1905, "type": "Society", "specialty": "All branches of magic", "description": "World's premier magic society with museum and theater in Euston"},
    {"name": "Blackpool Magic Convention", "city": "Blackpool", "country": "UK", "lat": 53.8175, "lon": -3.0518, "founded": 1947, "type": "Convention", "specialty": "All branches", "description": "World's largest annual magic convention attracting 4000+ magicians"},
    {"name": "Tannen's Magic Camp", "city": "New York", "country": "USA", "lat": 40.7488, "lon": -73.9936, "founded": 1925, "type": "Magic Shop/Camp", "specialty": "Youth magic education", "description": "America's oldest magic shop running summer magic camps for kids"},
    {"name": "McBride's Magic & Mystery School", "city": "Las Vegas", "country": "USA", "lat": 36.1500, "lon": -115.1500, "founded": 1991, "type": "Master Class School", "specialty": "Performance & Illusion", "description": "Jeff McBride's intensive master classes in magic and performance"},
    {"name": "Escola de Magia de Madrid", "city": "Madrid", "country": "Spain", "lat": 40.4200, "lon": -3.7025, "founded": 1995, "type": "School", "specialty": "Stage & Close-up", "description": "Formal magic school offering structured curriculum in Spanish magic"},
    {"name": "SAM National HQ", "city": "Denver", "country": "USA", "lat": 39.7392, "lon": -104.9903, "founded": 1902, "type": "Society", "specialty": "All branches", "description": "Society of American Magicians founded by Harry Houdini as president"},
    {"name": "FISM Headquarters", "city": "Lausanne", "country": "Switzerland", "lat": 46.5197, "lon": 6.6323, "founded": 1948, "type": "Federation", "specialty": "Competition Magic", "description": "International Federation of Magic Societies organizing World Championships"},
    {"name": "Chavez Studio of Magic", "city": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437, "founded": 1940, "type": "Studio", "specialty": "Stage Illusion", "description": "Where Neil Foster trained generations of professional stage magicians"},
    {"name": "Centre National des Arts du Cirque", "city": "Chalons-en-Champagne", "country": "France", "lat": 48.9563, "lon": 4.3631, "founded": 1985, "type": "National School", "specialty": "Circus & Magic Arts", "description": "France's national circus arts school with magic specialization"},
    {"name": "Houdini Museum", "city": "Scranton", "country": "USA", "lat": 41.4090, "lon": -75.6624, "founded": 1990, "type": "Museum", "specialty": "Escape & History", "description": "Dedicated to Houdini's legacy with live magic shows and artifacts"},
    {"name": "Melbourne Magic Festival", "city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "founded": 2009, "type": "Festival", "specialty": "All branches", "description": "Australia's premier magic festival with workshops and competitions"},
    {"name": "Dai Vernon Foundation", "city": "Los Angeles", "country": "USA", "lat": 34.0980, "lon": -118.3350, "founded": 1965, "type": "Foundation", "specialty": "Close-up Magic", "description": "Legacy of 'The Professor' - the man who fooled Houdini with card magic"},
    {"name": "Teatro di Magia", "city": "Rome", "country": "Italy", "lat": 41.8967, "lon": 12.4822, "founded": 2001, "type": "Theater", "specialty": "Italian Magic", "description": "Dedicated magic theater showcasing Italian illusionists nightly"},
    {"name": "Museo de la Magia", "city": "Paris", "country": "France", "lat": 48.8530, "lon": 2.3580, "founded": 1993, "type": "Museum", "specialty": "History & Automata", "description": "Underground magic museum in medieval vaults with live performances"},
    {"name": "Zauber Theater", "city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738, "founded": 1998, "type": "Theater", "specialty": "Close-up & Parlor", "description": "Intimate Viennese magic theater with nightly close-up performances"},
    {"name": "Magic Nordic Convention", "city": "Helsinki", "country": "Finland", "lat": 60.1699, "lon": 24.9384, "founded": 1975, "type": "Convention", "specialty": "Nordic Magic", "description": "Largest Nordic magic gathering with Scandinavian magic traditions"},
    {"name": "College of Magic", "city": "Cape Town", "country": "South Africa", "lat": -33.9470, "lon": 18.4733, "founded": 1980, "type": "School", "specialty": "Youth Development", "description": "Free magic education for underprivileged youth using magic as social tool"},
    {"name": "Japan Close-Up Magicians Club", "city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "founded": 1960, "type": "Club", "specialty": "Close-up Magic", "description": "Japanese close-up magic association with meticulous sleight-of-hand tradition"},
    {"name": "Escuela de Magia Ana Tamariz", "city": "Seville", "country": "Spain", "lat": 37.3886, "lon": -5.9823, "founded": 1975, "type": "School", "specialty": "Spanish Card Magic", "description": "Juan Tamariz school of misdirection and Spanish card magic tradition"},
    {"name": "International Brotherhood of Magicians", "city": "St. Louis", "country": "USA", "lat": 38.6270, "lon": -90.1994, "founded": 1922, "type": "Brotherhood", "specialty": "All branches", "description": "World's largest magic organization with 300+ local rings worldwide"},
    {"name": "Copperfield's Magic Underground", "city": "New York", "country": "USA", "lat": 40.7235, "lon": -73.9994, "founded": 2000, "type": "Private Collection", "specialty": "Historic Apparatus", "description": "David Copperfield's secret warehouse of historic magic props and automata"},
    {"name": "Penn & Teller Theater", "city": "Las Vegas", "country": "USA", "lat": 36.1166, "lon": -115.1725, "founded": 2001, "type": "Resident Show", "specialty": "Comedy Magic", "description": "Penn & Teller's long-running residency deconstructing magic nightly"},
    {"name": "School of Busking Magic", "city": "Adelaide", "country": "Australia", "lat": -34.9290, "lon": 138.6010, "founded": 2012, "type": "Workshop School", "specialty": "Street Magic", "description": "Teaching street magic performance at Adelaide Fringe Festival"},
    {"name": "Chinese Magic Association", "city": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074, "founded": 1956, "type": "Association", "specialty": "Traditional Chinese Magic", "description": "Preserving ancient Chinese conjuring traditions dating back 2000 years"},
    {"name": "Indian Magicians Society", "city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "founded": 1938, "type": "Society", "specialty": "Indian Street Magic", "description": "India's oldest magic society preserving jadoo-wallah street traditions"},
    {"name": "El Rey de la Magia", "city": "Barcelona", "country": "Spain", "lat": 41.3844, "lon": 2.1780, "founded": 1881, "type": "Magic Shop", "specialty": "Classic Props", "description": "One of the oldest magic shops in the world, still family-run"},
    {"name": "Maison de la Magie", "city": "Blois", "country": "France", "lat": 47.5870, "lon": 1.3310, "founded": 1998, "type": "Museum", "specialty": "Robert-Houdin Legacy", "description": "Museum honoring Jean-Eugene Robert-Houdin, father of modern magic"},
    {"name": "Stockholm Magic Theater", "city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686, "founded": 2005, "type": "Theater", "specialty": "Nordic Magic", "description": "Intimate theater showcasing Scandinavian magicians in old town"},
    {"name": "Hocus Pocus Magic School", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "founded": 2010, "type": "Workshop", "specialty": "Beginner Magic", "description": "Hands-on magic workshops for tourists and aspiring conjurers"},
]

# ===================================================================
# DATA: CARNIVAL & MARDI GRAS TRADITIONS (30)
# ===================================================================
CARNIVAL_DATA = [
    {"name": "Rio Carnival", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9068, "lon": -43.1729, "founded": 1723, "type": "Samba Carnival", "visitors": 5000000, "description": "World's largest carnival with samba schools parading in the Sambadrome"},
    {"name": "Mardi Gras", "city": "New Orleans", "country": "USA", "lat": 29.9511, "lon": -90.0715, "founded": 1699, "type": "Krewe Parades", "visitors": 1400000, "description": "Iconic Fat Tuesday celebration with krewes, floats, and beads"},
    {"name": "Venice Carnival", "city": "Venice", "country": "Italy", "lat": 45.4408, "lon": 12.3155, "founded": 1094, "type": "Masked Carnival", "visitors": 3000000, "description": "Elegant masked carnival dating back almost a millennium"},
    {"name": "Carnival of Binche", "city": "Binche", "country": "Belgium", "lat": 50.4117, "lon": 4.1656, "founded": 1394, "type": "Gilles Carnival", "visitors": 100000, "description": "UNESCO-listed carnival with Gilles dancers throwing blood oranges"},
    {"name": "Trinidad Carnival", "city": "Port of Spain", "country": "Trinidad", "lat": 10.6596, "lon": -61.5086, "founded": 1783, "type": "Soca/Calypso", "visitors": 400000, "description": "Caribbean carnival with steelpan, soca, and elaborate masquerade"},
    {"name": "Carnival of Santa Cruz", "city": "Santa Cruz de Tenerife", "country": "Spain", "lat": 28.4636, "lon": -16.2518, "founded": 1894, "type": "Island Carnival", "visitors": 1000000, "description": "Second largest carnival after Rio with drag queen gala and comparsas"},
    {"name": "Cologne Carnival", "city": "Cologne", "country": "Germany", "lat": 50.9375, "lon": 6.9603, "founded": 1823, "type": "Karneval", "visitors": 1500000, "description": "Rhineland Karneval with Rose Monday parade and Prince Carnival"},
    {"name": "Carnival of Barranquilla", "city": "Barranquilla", "country": "Colombia", "lat": 10.9685, "lon": -74.7813, "founded": 1865, "type": "Colombian Carnival", "visitors": 1500000, "description": "UNESCO masterpiece of oral heritage with cumbia and marimonda masks"},
    {"name": "Basel Fasnacht", "city": "Basel", "country": "Switzerland", "lat": 47.5596, "lon": 7.5886, "founded": 1529, "type": "Lantern Carnival", "visitors": 200000, "description": "Begins at 4am Monday with Morgestraich lantern procession in darkness"},
    {"name": "Nice Carnival", "city": "Nice", "country": "France", "lat": 43.7102, "lon": 7.2620, "founded": 1294, "type": "Flower Battle", "visitors": 1200000, "description": "Medieval-origin carnival with flower battles and giant float heads"},
    {"name": "Oruro Carnival", "city": "Oruro", "country": "Bolivia", "lat": -17.9647, "lon": -67.1142, "founded": 1789, "type": "Diablada", "visitors": 400000, "description": "UNESCO-listed Andean carnival with Diablada devil dancers"},
    {"name": "Notting Hill Carnival", "city": "London", "country": "UK", "lat": 51.5155, "lon": -0.2057, "founded": 1966, "type": "Caribbean Street", "visitors": 2500000, "description": "Europe's largest street carnival celebrating Caribbean culture"},
    {"name": "Mardi Gras Sydney", "city": "Sydney", "country": "Australia", "lat": -33.8836, "lon": 151.2149, "founded": 1978, "type": "LGBTQ+ Pride", "visitors": 500000, "description": "Sydney Gay and Lesbian Mardi Gras parade and festival"},
    {"name": "Ivrea Orange Battle", "city": "Ivrea", "country": "Italy", "lat": 45.4670, "lon": 7.8750, "founded": 1808, "type": "Battle Carnival", "visitors": 50000, "description": "Historic carnival culminating in massive orange battle reenactment"},
    {"name": "Carnival of Viareggio", "city": "Viareggio", "country": "Italy", "lat": 43.8677, "lon": 10.2534, "founded": 1873, "type": "Float Carnival", "visitors": 600000, "description": "Famous for giant satirical papier-mache floats parading on the coast"},
    {"name": "Carnival of Cadiz", "city": "Cadiz", "country": "Spain", "lat": 36.5271, "lon": -6.2886, "founded": 1500, "type": "Musical Carnival", "visitors": 200000, "description": "Famed for chirigotas - satirical musical comedy groups performing in streets"},
    {"name": "Thaipusam Festival", "city": "Kuala Lumpur", "country": "Malaysia", "lat": 3.2374, "lon": 101.6836, "founded": 1888, "type": "Hindu Festival", "visitors": 1000000, "description": "Hindu carnival with kavadi body piercing processions to Batu Caves"},
    {"name": "Carnival of Rijeka", "city": "Rijeka", "country": "Croatia", "lat": 45.3271, "lon": 14.4422, "founded": 1982, "type": "Adriatic Carnival", "visitors": 150000, "description": "Croatia's largest carnival with Zvoncari bell-wearing masked figures"},
    {"name": "Crop Over Festival", "city": "Bridgetown", "country": "Barbados", "lat": 13.0969, "lon": -59.6145, "founded": 1780, "type": "Harvest Carnival", "visitors": 200000, "description": "Sugar cane harvest celebration culminating in Grand Kadooment Day"},
    {"name": "Junkanoo", "city": "Nassau", "country": "Bahamas", "lat": 25.0480, "lon": -77.3554, "founded": 1700, "type": "Junkanoo Rush", "visitors": 100000, "description": "Bahamian Boxing Day rush-out with goatskin drums and elaborate costumes"},
    {"name": "Philadelphia Mummers Parade", "city": "Philadelphia", "country": "USA", "lat": 39.9526, "lon": -75.1652, "founded": 1901, "type": "Mummers", "visitors": 100000, "description": "New Year's Day parade with string bands, comics, and fancy brigades"},
    {"name": "Carnival of Dunkirk", "city": "Dunkirk", "country": "France", "lat": 51.0343, "lon": 2.3768, "founded": 1676, "type": "Fishermen's Carnival", "visitors": 60000, "description": "Wild northern French carnival with herring-throwing and band parades"},
    {"name": "Goa Carnival", "city": "Panaji", "country": "India", "lat": 15.4909, "lon": 73.8278, "founded": 1800, "type": "Portuguese Heritage", "visitors": 300000, "description": "Four-day Portuguese-influenced carnival with King Momo figure"},
    {"name": "Carnival of Aalst", "city": "Aalst", "country": "Belgium", "lat": 50.9387, "lon": 4.0403, "founded": 1432, "type": "Satirical Carnival", "visitors": 100000, "description": "Three-day satirical carnival with dirty jokes and ajuin throwing"},
    {"name": "Carnival of Recife-Olinda", "city": "Recife", "country": "Brazil", "lat": -8.0476, "lon": -34.8770, "founded": 1710, "type": "Frevo Carnival", "visitors": 2000000, "description": "Massive street carnival with frevo music and giant puppet Bonecos"},
    {"name": "Fasching Munich", "city": "Munich", "country": "Germany", "lat": 48.1351, "lon": 11.5820, "founded": 1500, "type": "Bavarian Carnival", "visitors": 500000, "description": "Bavarian carnival season with dance of the market women tradition"},
    {"name": "Carnival of Patras", "city": "Patras", "country": "Greece", "lat": 38.2466, "lon": 21.7346, "founded": 1829, "type": "Greek Carnival", "visitors": 300000, "description": "Greece's largest carnival ending with ritual burning of the Carnival King"},
    {"name": "Quebec Winter Carnival", "city": "Quebec City", "country": "Canada", "lat": 46.8139, "lon": -71.2080, "founded": 1894, "type": "Winter Carnival", "visitors": 500000, "description": "World's largest winter carnival with Bonhomme mascot and ice palace"},
    {"name": "Masskara Festival", "city": "Bacolod", "country": "Philippines", "lat": 10.6840, "lon": 122.9740, "founded": 1980, "type": "Smiling Masks", "visitors": 200000, "description": "Festival of Smiles with colorful smiling mask dances in the streets"},
    {"name": "Carnival of Mazatlan", "city": "Mazatlan", "country": "Mexico", "lat": 23.2494, "lon": -106.4111, "founded": 1898, "type": "Mexican Carnival", "visitors": 500000, "description": "Third largest carnival in the world along the Pacific malecon"},
]

# ===================================================================
# DATA: PUPPET THEATER HERITAGE (30)
# ===================================================================
PUPPET_THEATER = [
    {"name": "Salzburg Marionette Theatre", "city": "Salzburg", "country": "Austria", "lat": 47.8005, "lon": 13.0410, "founded": 1913, "type": "String Marionettes", "tradition": "European", "description": "UNESCO-recognized marionette opera performing Mozart and more for 110+ years"},
    {"name": "Bunraku National Theatre", "city": "Osaka", "country": "Japan", "lat": 34.6687, "lon": 135.5125, "founded": 1684, "type": "Bunraku Puppetry", "tradition": "Japanese", "description": "Traditional Japanese puppet theater with three operators per puppet"},
    {"name": "Wayang Museum", "city": "Jakarta", "country": "Indonesia", "lat": -6.1344, "lon": 106.8134, "founded": 1975, "type": "Shadow Puppets", "tradition": "Javanese/Balinese", "description": "Museum of wayang kulit shadow puppetry, UNESCO masterpiece"},
    {"name": "Teatro dei Pupi", "city": "Palermo", "country": "Italy", "lat": 38.1157, "lon": 13.3615, "founded": 1830, "type": "Rod Marionettes", "tradition": "Sicilian", "description": "Opera dei Pupi - Sicilian knight puppet theater, UNESCO heritage"},
    {"name": "National Marionette Theatre", "city": "Prague", "country": "Czech Republic", "lat": 50.0875, "lon": 14.4179, "founded": 1991, "type": "Marionettes", "tradition": "Czech", "description": "Czech marionette tradition performing Don Giovanni with puppets"},
    {"name": "Puppet Theatre Barge", "city": "London", "country": "UK", "lat": 51.5071, "lon": -0.1862, "founded": 1982, "type": "Barge Theater", "tradition": "British", "description": "Unique floating puppet theater on a Thames barge in Little Venice"},
    {"name": "Karagoz Shadow Theater", "city": "Istanbul", "country": "Turkey", "lat": 41.0119, "lon": 28.9790, "founded": 1500, "type": "Shadow Puppets", "tradition": "Ottoman", "description": "Traditional Ottoman shadow puppet comedy with Karagoz and Hacivat"},
    {"name": "Henson Workshop", "city": "New York", "country": "USA", "lat": 40.7690, "lon": -73.9895, "founded": 1963, "type": "Muppet Workshop", "tradition": "American", "description": "Jim Henson's creature shop where the Muppets were born"},
    {"name": "Teatru Manoel", "city": "Valletta", "country": "Malta", "lat": 35.8993, "lon": 14.5123, "founded": 1731, "type": "Opera & Puppets", "tradition": "Mediterranean", "description": "Historic theater hosting traditional Maltese puppet shows"},
    {"name": "Center for Puppetry Arts", "city": "Atlanta", "country": "USA", "lat": 33.7910, "lon": -84.3877, "founded": 1978, "type": "Museum & Theater", "tradition": "American", "description": "Largest puppetry organization in the US with Jim Henson collection"},
    {"name": "Bread and Puppet Theater", "city": "Glover", "country": "USA", "lat": 44.6920, "lon": -72.1900, "founded": 1963, "type": "Political Puppetry", "tradition": "Protest Art", "description": "Radical political puppet theater with giant papier-mache figures"},
    {"name": "Rajasthani Puppet House", "city": "Jaipur", "country": "India", "lat": 26.9124, "lon": 75.7873, "founded": 1600, "type": "Kathputli Puppets", "tradition": "Indian", "description": "Kathputli string puppet tradition from Rajasthan dating back 400 years"},
    {"name": "Museu da Marioneta", "city": "Lisbon", "country": "Portugal", "lat": 38.7072, "lon": -9.1490, "founded": 2001, "type": "Museum", "tradition": "Portuguese", "description": "Puppet museum in a medieval convent with global puppet collection"},
    {"name": "Handspring Puppet Company", "city": "Cape Town", "country": "South Africa", "lat": -33.9230, "lon": 18.4130, "founded": 1981, "type": "Life-Size Puppets", "tradition": "African", "description": "Created War Horse puppets for the National Theatre, globally acclaimed"},
    {"name": "Lutkovno Gledalisce", "city": "Ljubljana", "country": "Slovenia", "lat": 46.0511, "lon": 14.5051, "founded": 1948, "type": "State Puppet Theater", "tradition": "Slovenian", "description": "One of Europe's oldest professional puppet theaters"},
    {"name": "Thai Puppet Theatre", "city": "Bangkok", "country": "Thailand", "lat": 13.7390, "lon": 100.4896, "founded": 2001, "type": "Hun Lakhon Lek", "tradition": "Thai", "description": "Reviving traditional Thai small puppet theater with intricate figures"},
    {"name": "Guignol de Lyon", "city": "Lyon", "country": "France", "lat": 45.7640, "lon": 4.8357, "founded": 1808, "type": "Glove Puppets", "tradition": "French", "description": "Home of Guignol, France's beloved slapstick puppet character"},
    {"name": "Water Puppet Theater", "city": "Hanoi", "country": "Vietnam", "lat": 21.0285, "lon": 105.8542, "founded": 1000, "type": "Water Puppets", "tradition": "Vietnamese", "description": "Mua roi nuoc - 1000-year-old tradition of puppets dancing on water"},
    {"name": "Obraztsov Puppet Theater", "city": "Moscow", "country": "Russia", "lat": 55.7710, "lon": 37.6273, "founded": 1931, "type": "State Puppet Theater", "tradition": "Russian", "description": "World's largest puppet theater collection with 60,000 puppets"},
    {"name": "Teatro de Marionetas Porto", "city": "Porto", "country": "Portugal", "lat": 41.1496, "lon": -8.6157, "founded": 1988, "type": "Contemporary", "tradition": "Portuguese", "description": "Contemporary Portuguese puppet theater with innovative productions"},
    {"name": "Compagnie Philippe Genty", "city": "Paris", "country": "France", "lat": 48.8720, "lon": 2.3390, "founded": 1968, "type": "Visual Theater", "tradition": "French", "description": "Surrealist puppet and visual theater company touring worldwide"},
    {"name": "Figurentheater Koln", "city": "Cologne", "country": "Germany", "lat": 50.9361, "lon": 6.9484, "founded": 1976, "type": "Figure Theater", "tradition": "German", "description": "Renowned German puppet theater festival and permanent venue"},
    {"name": "Stuffed Puppet Theatre", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3658, "lon": 4.8809, "founded": 1979, "type": "Foam Puppets", "tradition": "Dutch", "description": "Neville Tranter's dark-humored life-size foam puppet theater"},
    {"name": "Unima HQ", "city": "Charleville-Mezieres", "country": "France", "lat": 49.7706, "lon": 4.7162, "founded": 1929, "type": "International HQ", "tradition": "Global", "description": "World puppetry union HQ in city that hosts triennial World Puppet Festival"},
    {"name": "Puppet State Theatre", "city": "Edinburgh", "country": "UK", "lat": 55.9396, "lon": -3.1940, "founded": 1999, "type": "Touring Company", "tradition": "Scottish", "description": "Award-winning Scottish puppet theater company touring internationally"},
    {"name": "Tolosa Puppet Museum", "city": "Tolosa", "country": "Spain", "lat": 43.1347, "lon": -2.0790, "founded": 2009, "type": "Museum", "tradition": "Basque", "description": "Basque Country puppet museum hosting the international TOPIC festival"},
    {"name": "Anurupa Roy Studio", "city": "New Delhi", "country": "India", "lat": 28.5650, "lon": 77.2100, "founded": 2003, "type": "Contemporary Puppetry", "tradition": "Indian", "description": "Contemporary Indian puppeteer bridging tradition and modern themes"},
    {"name": "Taiwan Puppet Theater", "city": "Taipei", "country": "Taiwan", "lat": 25.0320, "lon": 121.5189, "founded": 1999, "type": "Glove Puppets", "tradition": "Taiwanese", "description": "Budaixi glove puppetry tradition brought to modern theater stages"},
    {"name": "Tillstrom Legacy Workshop", "city": "Chicago", "country": "USA", "lat": 41.8851, "lon": -87.6265, "founded": 1947, "type": "TV Puppetry", "tradition": "American", "description": "Legacy of Kukla, Fran and Ollie - pioneering TV puppetry from Chicago"},
    {"name": "Puppet & Its Double", "city": "Taipei", "country": "Taiwan", "lat": 25.0480, "lon": 121.5295, "founded": 1999, "type": "Contemporary", "tradition": "Taiwanese", "description": "Innovative Taiwanese troupe merging puppetry with multimedia art"},
]

# ===================================================================
# DATA: ACROBATIC & GYMNASTIC SCHOOLS (30)
# ===================================================================
ACROBATIC_SCHOOLS = [
    {"name": "Ecole Nationale de Cirque", "city": "Montreal", "country": "Canada", "lat": 45.5190, "lon": -73.5560, "founded": 1981, "type": "National School", "specialty": "All circus arts", "description": "Premier professional circus school training Cirque du Soleil artists"},
    {"name": "CNAC", "city": "Chalons-en-Champagne", "country": "France", "lat": 48.9563, "lon": 4.3631, "founded": 1985, "type": "National School", "specialty": "French circus arts", "description": "France's national circus arts center producing world-class graduates"},
    {"name": "DOCH", "city": "Stockholm", "country": "Sweden", "lat": 59.3220, "lon": 18.0649, "founded": 1997, "type": "University", "specialty": "Circus & Dance", "description": "Stockholm University of the Arts circus program at degree level"},
    {"name": "ESAC", "city": "Brussels", "country": "Belgium", "lat": 50.8151, "lon": 4.3510, "founded": 2003, "type": "Higher School", "specialty": "Circus Arts", "description": "Belgium's higher education school for circus arts"},
    {"name": "SPAAC", "city": "London", "country": "UK", "lat": 51.5391, "lon": -0.0601, "founded": 2004, "type": "Academy", "specialty": "Aerial & Acrobatics", "description": "National Centre for Circus Arts training professional performers"},
    {"name": "Wuqiao Acrobatics School", "city": "Wuqiao", "country": "China", "lat": 37.6178, "lon": 116.3817, "founded": 1958, "type": "Acrobatics School", "specialty": "Chinese acrobatics", "description": "Heart of Chinese acrobatics in the 'Hometown of Acrobatics'"},
    {"name": "Beijing International Acrobatics School", "city": "Beijing", "country": "China", "lat": 39.9242, "lon": 116.4074, "founded": 1950, "type": "State School", "specialty": "Chinese acrobatics", "description": "Training ground for China's Olympic-caliber acrobats and contortionists"},
    {"name": "Circus Space (now NCCA)", "city": "London", "country": "UK", "lat": 51.5390, "lon": -0.0600, "founded": 1989, "type": "Training Center", "specialty": "All circus arts", "description": "UK's premier professional circus training center in Hoxton"},
    {"name": "Codarts Circus Arts", "city": "Rotterdam", "country": "Netherlands", "lat": 51.9173, "lon": 4.4784, "founded": 1988, "type": "University", "specialty": "Circus & Performance", "description": "Dutch university-level circus arts program with BA degree"},
    {"name": "Lido de Paris Academy", "city": "Paris", "country": "France", "lat": 48.8711, "lon": 2.3040, "founded": 1946, "type": "Cabaret School", "specialty": "Cabaret acrobatics", "description": "Training dancers and acrobats for the famous Champs-Elysees cabaret"},
    {"name": "Moscow State Circus School", "city": "Moscow", "country": "Russia", "lat": 55.7540, "lon": 37.5970, "founded": 1927, "type": "State School", "specialty": "Russian circus arts", "description": "Soviet-era school producing generations of legendary circus performers"},
    {"name": "Sarasota Sailor Circus", "city": "Sarasota", "country": "USA", "lat": 27.3364, "lon": -82.5307, "founded": 1949, "type": "Youth Circus", "specialty": "Youth training", "description": "America's oldest youth circus training future performers since 1949"},
    {"name": "Ecole de Cirque de Quebec", "city": "Quebec City", "country": "Canada", "lat": 46.8200, "lon": -71.2200, "founded": 1995, "type": "Professional School", "specialty": "Quebec circus", "description": "Quebec's professional circus training school feeding the industry"},
    {"name": "Flic Scuola di Circo", "city": "Turin", "country": "Italy", "lat": 45.0703, "lon": 7.6869, "founded": 2002, "type": "Professional School", "specialty": "Italian circus", "description": "Italy's leading professional circus school in a converted factory"},
    {"name": "National Circus School of Mongolia", "city": "Ulaanbaatar", "country": "Mongolia", "lat": 47.9218, "lon": 106.9110, "founded": 1961, "type": "National School", "specialty": "Contortion", "description": "World-famous for producing supreme contortionists and acrobats"},
    {"name": "Escola Nacional de Circo", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9100, "lon": -43.1830, "founded": 1982, "type": "National School", "specialty": "Brazilian circus", "description": "Brazil's national circus school in the Lapa neighborhood"},
    {"name": "Carampa", "city": "Madrid", "country": "Spain", "lat": 40.4100, "lon": -3.7010, "founded": 1998, "type": "Professional School", "specialty": "Spanish circus arts", "description": "Spain's leading professional circus arts training center"},
    {"name": "Cirkus Minimus School", "city": "Oslo", "country": "Norway", "lat": 59.9139, "lon": 10.7522, "founded": 1999, "type": "School", "specialty": "Nordic circus", "description": "Norway's circus school training next-generation Nordic performers"},
    {"name": "Philadelphia School of Circus Arts", "city": "Philadelphia", "country": "USA", "lat": 39.9657, "lon": -75.1342, "founded": 2008, "type": "Community School", "specialty": "All circus arts", "description": "Largest circus school in the US with aerial, tumbling, and trapeze"},
    {"name": "Sirkuskoulu", "city": "Helsinki", "country": "Finland", "lat": 60.1699, "lon": 24.9384, "founded": 2001, "type": "Academy", "specialty": "Finnish circus", "description": "Finnish circus academy producing internationally touring performers"},
    {"name": "Circus Arts Conservatory", "city": "Sarasota", "country": "USA", "lat": 27.3420, "lon": -82.5302, "founded": 1997, "type": "Conservatory", "specialty": "Professional training", "description": "Professional circus training in the traditional US circus capital"},
    {"name": "Escola Picolino de Artes do Circo", "city": "Salvador", "country": "Brazil", "lat": -12.9704, "lon": -38.5124, "founded": 1985, "type": "Social Circus", "specialty": "Social inclusion", "description": "Social circus school transforming lives of at-risk youth in Bahia"},
    {"name": "Circomedia", "city": "Bristol", "country": "UK", "lat": 51.4508, "lon": -2.5885, "founded": 1986, "type": "Academy", "specialty": "Physical theater & circus", "description": "BA degree in circus arts in a converted church in Bristol"},
    {"name": "Die Etage", "city": "Berlin", "country": "Germany", "lat": 52.4870, "lon": 13.4190, "founded": 1994, "type": "Academy", "specialty": "Circus & Performance", "description": "Berlin's professional circus and performance art training academy"},
    {"name": "Escuela de Circo Criollo", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6100, "lon": -58.3800, "founded": 2000, "type": "Creole Circus School", "specialty": "Argentine circus", "description": "Preserving Argentina's unique criollo circus tradition"},
    {"name": "Siam Niramit Academy", "city": "Bangkok", "country": "Thailand", "lat": 13.7519, "lon": 100.5564, "founded": 2005, "type": "Performance Academy", "specialty": "Thai acrobatics", "description": "Training performers for Thailand's grand cultural spectacle shows"},
    {"name": "Galiny Circus School", "city": "Kyiv", "country": "Ukraine", "lat": 50.4501, "lon": 30.5234, "founded": 1965, "type": "State School", "specialty": "Eastern European circus", "description": "Ukrainian circus school in the tradition of Soviet circus excellence"},
    {"name": "Australian National Circus Centre", "city": "Melbourne", "country": "Australia", "lat": -37.8050, "lon": 144.9870, "founded": 2001, "type": "National Center", "specialty": "Australian circus", "description": "Swinburne University circus program training Australian performers"},
    {"name": "Flying Fruit Fly Circus", "city": "Albury", "country": "Australia", "lat": -36.0737, "lon": 146.9135, "founded": 1979, "type": "Youth Circus", "specialty": "Youth training", "description": "Australia's renowned youth circus based on the Murray River"},
    {"name": "Taller de Circo Escalando", "city": "Mexico City", "country": "Mexico", "lat": 19.4150, "lon": -99.1550, "founded": 2005, "type": "Social Circus", "specialty": "Social circus", "description": "Mexican social circus empowering communities through circus arts"},
]

# ===================================================================
# DATA: CLOWN & COMEDY FESTIVALS (25)
# ===================================================================
CLOWN_FESTIVALS = [
    {"name": "Clown Festival of Villanova", "city": "Villanova d'Asti", "country": "Italy", "lat": 44.9417, "lon": 8.0333, "founded": 1998, "type": "Clown Festival", "duration": "3 days", "description": "Italian festival celebrating European clown traditions and new acts"},
    {"name": "World Clown Association Convention", "city": "Orlando", "country": "USA", "lat": 28.5383, "lon": -81.3792, "founded": 1984, "type": "Convention", "duration": "5 days", "description": "Annual gathering of professional clowns from around the world"},
    {"name": "Just for Laughs / Juste pour Rire", "city": "Montreal", "country": "Canada", "lat": 45.5120, "lon": -73.5680, "founded": 1983, "type": "Comedy Festival", "duration": "14 days", "description": "World's largest comedy festival with street performers and galas"},
    {"name": "Edinburgh Festival Fringe", "city": "Edinburgh", "country": "UK", "lat": 55.9504, "lon": -3.1883, "founded": 1947, "type": "Arts Festival", "duration": "25 days", "description": "World's largest arts festival with 3500+ comedy and circus shows"},
    {"name": "Grimaldi Memorial Service", "city": "London", "country": "UK", "lat": 51.5314, "lon": -0.1047, "founded": 1946, "type": "Memorial/Festival", "duration": "1 day", "description": "Annual clown church service honoring Joseph Grimaldi at Holy Trinity"},
    {"name": "Festival Mondial du Cirque de Demain", "city": "Paris", "country": "France", "lat": 48.8650, "lon": 2.3672, "founded": 1977, "type": "Circus Competition", "duration": "4 days", "description": "World's most prestigious young circus artist competition at Cirque d'Hiver"},
    {"name": "Melbourne International Comedy Festival", "city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "founded": 1987, "type": "Comedy Festival", "duration": "30 days", "description": "Third largest comedy festival globally with street and clown shows"},
    {"name": "Bognor Regis Clown Convention", "city": "Bognor Regis", "country": "UK", "lat": 50.7829, "lon": -0.6812, "founded": 1946, "type": "Clown Convention", "duration": "4 days", "description": "Clowns International annual convention with egg registration tradition"},
    {"name": "Fool's Festival", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "founded": 1975, "type": "Fool/Clown Festival", "duration": "3 days", "description": "Dutch festival celebrating court jester and fool traditions"},
    {"name": "Clown-Fest", "city": "Seaside Heights", "country": "USA", "lat": 39.9443, "lon": -74.0713, "founded": 1990, "type": "Boardwalk Festival", "duration": "2 days", "description": "New Jersey boardwalk clown festival with competitions and parades"},
    {"name": "International Clown Festival", "city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "founded": 1995, "type": "Clown Gathering", "duration": "5 days", "description": "Massive gathering of Latin American clowns with payaso competitions"},
    {"name": "Festival Internacional de Pallassos", "city": "Cornella de Llobregat", "country": "Spain", "lat": 41.3486, "lon": 2.0726, "founded": 2003, "type": "Clown Festival", "duration": "3 days", "description": "Spanish international clown festival near Barcelona"},
    {"name": "Patch Adams Clown Trips", "city": "Urbana", "country": "USA", "lat": 40.1106, "lon": -88.2073, "founded": 1985, "type": "Humanitarian Clowning", "duration": "Ongoing", "description": "Gesundheit Institute organizing clown trips to hospitals worldwide"},
    {"name": "Clown Doctors of Australia", "city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "founded": 1996, "type": "Hospital Clowning", "duration": "Year-round", "description": "Professional clown doctors bringing laughter to sick children"},
    {"name": "Festival de Teatro de Calle", "city": "Valladolid", "country": "Spain", "lat": 41.6523, "lon": -4.7245, "founded": 2006, "type": "Street Theater", "duration": "4 days", "description": "TAC street arts festival with clown and comedy performances"},
    {"name": "Giffords Circus", "city": "Stroud", "country": "UK", "lat": 51.7460, "lon": -2.2190, "founded": 2000, "type": "Touring Festival", "duration": "5 months", "description": "Magical English country circus touring Cotswolds villages in summer"},
    {"name": "Festival of Fools", "city": "Belfast", "country": "UK", "lat": 54.5973, "lon": -5.9301, "founded": 2004, "type": "Street Comedy", "duration": "5 days", "description": "Belfast's international street arts and comedy festival"},
    {"name": "Circus Next Competition", "city": "Auch", "country": "France", "lat": 43.6460, "lon": 0.5856, "founded": 2010, "type": "Circus Creation", "duration": "5 days", "description": "Platform for emerging European circus creators in Auch"},
    {"name": "Fira Tarrega", "city": "Tarrega", "country": "Spain", "lat": 41.6509, "lon": 1.1388, "founded": 1981, "type": "Street Arts Fair", "duration": "3 days", "description": "Major Catalan street performance fair with 200,000+ spectators"},
    {"name": "Yokohama Clown Festival", "city": "Yokohama", "country": "Japan", "lat": 35.4437, "lon": 139.6380, "founded": 1998, "type": "Clown Festival", "duration": "3 days", "description": "Japan's premier clown gathering with international performers"},
    {"name": "Winterfest Clown Show", "city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738, "founded": 2002, "type": "Clown Cabaret", "duration": "2 weeks", "description": "Vienna's winter clown and cabaret showcase in intimate theaters"},
    {"name": "Adelaide Fringe", "city": "Adelaide", "country": "Australia", "lat": -34.9285, "lon": 138.6007, "founded": 1960, "type": "Fringe Festival", "duration": "30 days", "description": "Second-largest fringe festival with extensive circus and clown program"},
    {"name": "Red Nose Day Origins", "city": "London", "country": "UK", "lat": 51.5100, "lon": -0.1180, "founded": 1988, "type": "Charity Event", "duration": "1 day", "description": "Comic Relief's global charity day born from clown nose symbolism"},
    {"name": "International Laughter Day", "city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "founded": 1998, "type": "Laughter Movement", "duration": "1 day", "description": "Dr. Madan Kataria's Laughter Yoga movement celebrated globally"},
    {"name": "La Strada Street Festival", "city": "Graz", "country": "Austria", "lat": 47.0707, "lon": 15.4395, "founded": 1998, "type": "Street Festival", "duration": "8 days", "description": "Graz international street arts festival with circus and comedy"},
]

# ===================================================================
# DATA: FIRE PERFORMANCE TRADITIONS (25)
# ===================================================================
FIRE_PERFORMANCE = [
    {"name": "Beltane Fire Festival", "city": "Edinburgh", "country": "UK", "lat": 55.9533, "lon": -3.1825, "founded": 1988, "type": "Celtic Fire Festival", "tradition": "Celtic/Pagan", "description": "Ancient Celtic fire festival revived on Calton Hill each May Day eve"},
    {"name": "Full Moon Party", "city": "Ko Pha-ngan", "country": "Thailand", "lat": 9.7319, "lon": 100.0622, "founded": 1985, "type": "Beach Fire Party", "tradition": "Thai Beach", "description": "Legendary beach party with fire dancers and fire jump rope"},
    {"name": "Burning Man", "city": "Black Rock City", "country": "USA", "lat": 40.7864, "lon": -119.2065, "founded": 1986, "type": "Art/Fire Festival", "tradition": "Radical Expression", "description": "Iconic desert festival culminating in burning of giant effigy"},
    {"name": "Las Fallas", "city": "Valencia", "country": "Spain", "lat": 39.4699, "lon": -0.3763, "founded": 1497, "type": "Fire Festival", "tradition": "Spanish", "description": "Giant satirical sculptures burned on Saint Joseph's night"},
    {"name": "Up Helly Aa", "city": "Lerwick", "country": "UK", "lat": 60.1534, "lon": -1.1496, "founded": 1881, "type": "Viking Fire Festival", "tradition": "Norse/Shetland", "description": "Europe's largest fire festival with Viking longship burning"},
    {"name": "Fire Gardens - Compagnie Carabosse", "city": "Aix-en-Provence", "country": "France", "lat": 43.5297, "lon": 5.4474, "founded": 1997, "type": "Fire Installation", "tradition": "French Fire Art", "description": "Fire garden installations transforming public spaces with flame"},
    {"name": "Poi Spinning Origins", "city": "Rotorua", "country": "New Zealand", "lat": -38.1368, "lon": 176.2497, "founded": 0, "type": "Traditional Poi", "tradition": "Maori", "description": "Maori poi spinning tradition - origin of modern fire poi worldwide"},
    {"name": "FireDrums Festival", "city": "Lake County", "country": "USA", "lat": 38.9913, "lon": -122.5886, "founded": 2003, "type": "Fire Arts Festival", "tradition": "Flow Arts", "description": "Premier North American fire spinning and flow arts gathering"},
    {"name": "Loy Krathong Fire Festival", "city": "Chiang Mai", "country": "Thailand", "lat": 18.7883, "lon": 98.9853, "founded": 1200, "type": "Lantern/Fire Festival", "tradition": "Thai Buddhist", "description": "Thousands of fire lanterns released into sky during Yi Peng"},
    {"name": "Hogmanay Fire Procession", "city": "Edinburgh", "country": "UK", "lat": 55.9533, "lon": -3.1883, "founded": 1993, "type": "New Year Fire", "tradition": "Scottish", "description": "Torchlight procession of 35,000 people down the Royal Mile"},
    {"name": "Noche de San Juan", "city": "Alicante", "country": "Spain", "lat": 38.3452, "lon": -0.4810, "founded": 1928, "type": "Bonfire Festival", "tradition": "Spanish Midsummer", "description": "Midsummer bonfire night with hogueras burned on the beaches"},
    {"name": "Lewes Bonfire Night", "city": "Lewes", "country": "UK", "lat": 50.8742, "lon": 0.0087, "founded": 1605, "type": "Bonfire Festival", "tradition": "English", "description": "England's most intense Guy Fawkes celebration with burning effigies"},
    {"name": "Samhain Fire Festival", "city": "Dublin", "country": "Ireland", "lat": 53.3498, "lon": -6.2603, "founded": 2006, "type": "Celtic Fire", "tradition": "Celtic/Irish", "description": "Ancient Celtic new year fire celebration on the Hill of Ward"},
    {"name": "Fire Dancing of Anastenaria", "city": "Langadas", "country": "Greece", "lat": 40.7500, "lon": 23.1000, "founded": 1250, "type": "Firewalking", "tradition": "Greek Orthodox", "description": "Ancient Greek firewalking tradition on saints' feast days"},
    {"name": "Walpurgis Night", "city": "Harz Mountains", "country": "Germany", "lat": 51.7988, "lon": 10.6153, "founded": 800, "type": "Bonfire Night", "tradition": "Germanic Pagan", "description": "Night of witches on the Brocken with bonfires driving away evil"},
    {"name": "Kurama Fire Festival", "city": "Kyoto", "country": "Japan", "lat": 35.1207, "lon": 135.7702, "founded": 794, "type": "Torch Festival", "tradition": "Shinto", "description": "Young men carry giant flaming torches through narrow mountain streets"},
    {"name": "Fire Knife Dance Championship", "city": "Laie", "country": "USA", "lat": 21.6450, "lon": -157.9244, "founded": 1992, "type": "Competition", "tradition": "Samoan", "description": "World Fireknife Championship celebrating Samoan siva afi tradition"},
    {"name": "Jeju Fire Festival", "city": "Jeju", "country": "South Korea", "lat": 33.3616, "lon": 126.5292, "founded": 1997, "type": "Agricultural Fire", "tradition": "Korean", "description": "Setting fire to Mt. Saebyeol hillsides to drive out vermin"},
    {"name": "Flow Show at Esalen", "city": "Big Sur", "country": "USA", "lat": 36.1280, "lon": -121.6287, "founded": 2005, "type": "Flow Arts", "tradition": "California Flow", "description": "Coastal fire flow gatherings at the iconic Esalen Institute cliffs"},
    {"name": "Djembe Fire Circle", "city": "Accra", "country": "Ghana", "lat": 5.6037, "lon": -0.1870, "founded": 1950, "type": "Drum & Fire", "tradition": "West African", "description": "Traditional fire dancing circle accompanied by djembe drumming"},
    {"name": "Fiesta de San Anton", "city": "San Bartolome de Pinares", "country": "Spain", "lat": 40.5833, "lon": -4.3667, "founded": 1500, "type": "Horse Fire Festival", "tradition": "Spanish", "description": "Luminarias festival where horses ride through bonfires in the streets"},
    {"name": "Stonehenge Summer Solstice", "city": "Salisbury", "country": "UK", "lat": 51.1789, "lon": -1.8262, "founded": 1970, "type": "Solstice Fire", "tradition": "Druidic/Pagan", "description": "Fire performers join druids at sunrise on the longest day"},
    {"name": "Tazaungdaing Festival", "city": "Taunggyi", "country": "Myanmar", "lat": 20.7833, "lon": 97.0333, "founded": 1894, "type": "Fire Balloon", "tradition": "Burmese Buddhist", "description": "Hot air fire balloon festival with firework-laden balloons launched"},
    {"name": "Parrandas de Remedios", "city": "Remedios", "country": "Cuba", "lat": 22.4958, "lon": -79.5458, "founded": 1820, "type": "Fire/Fireworks", "tradition": "Cuban", "description": "Cuba's Christmas Eve firework and fire celebration between neighborhoods"},
    {"name": "SpinJam Community", "city": "San Francisco", "country": "USA", "lat": 37.7599, "lon": -122.4148, "founded": 2004, "type": "Fire Jam", "tradition": "Flow Arts", "description": "Weekly fire spinning community gathering in Golden Gate Park area"},
]

# ===================================================================
# DATA: VAUDEVILLE & VARIETY THEATER (25)
# ===================================================================
VAUDEVILLE_DATA = [
    {"name": "Palace Theatre", "city": "New York", "country": "USA", "lat": 40.7578, "lon": -73.9876, "founded": 1913, "type": "Vaudeville Palace", "era": "1913-1932", "description": "The cathedral of vaudeville - performing here meant you had arrived"},
    {"name": "Moulin Rouge", "city": "Paris", "country": "France", "lat": 48.8841, "lon": 2.3323, "founded": 1889, "type": "Cabaret/Variety", "era": "1889-present", "description": "Iconic Montmartre cabaret with cancan and variety acts since 1889"},
    {"name": "London Palladium", "city": "London", "country": "UK", "lat": 51.5152, "lon": -0.1401, "founded": 1910, "type": "Variety Theater", "era": "1910-present", "description": "West End variety theater hosting Royal Variety Performance"},
    {"name": "Apollo Theater", "city": "New York", "country": "USA", "lat": 40.8100, "lon": -73.9500, "founded": 1914, "type": "Variety/Music Hall", "era": "1914-present", "description": "Harlem's legendary Amateur Night stage launching countless careers"},
    {"name": "Friedrichstadt-Palast", "city": "Berlin", "country": "Germany", "lat": 52.5244, "lon": 13.3870, "founded": 1919, "type": "Revue Theater", "era": "1919-present", "description": "World's largest revue theater with spectacular variety productions"},
    {"name": "Wintergarten Berlin (Original)", "city": "Berlin", "country": "Germany", "lat": 52.5075, "lon": 13.3700, "founded": 1887, "type": "Variete", "era": "1887-1944", "description": "Where the Skladanowsky brothers held the first film screening in 1895"},
    {"name": "Folies Bergere", "city": "Paris", "country": "France", "lat": 48.8719, "lon": 2.3466, "founded": 1869, "type": "Music Hall", "era": "1869-present", "description": "Legendary Parisian music hall famous for Josephine Baker and revues"},
    {"name": "The Hippodrome", "city": "New York", "country": "USA", "lat": 40.7530, "lon": -73.9870, "founded": 1905, "type": "Mega-Theater", "era": "1905-1939", "description": "Largest theater in the world with 5300 seats and water spectacles"},
    {"name": "Orpheum Theatre", "city": "Los Angeles", "country": "USA", "lat": 34.0442, "lon": -118.2556, "founded": 1926, "type": "Vaudeville Circuit", "era": "1926-1950s", "description": "Last grande dame of the Orpheum vaudeville circuit on Broadway"},
    {"name": "The Old Vic", "city": "London", "country": "UK", "lat": 51.5020, "lon": -0.1091, "founded": 1818, "type": "Music Hall/Theater", "era": "1818-present", "description": "Started as Royal Coburg music hall, now prestigious theater"},
    {"name": "Crazy Horse Paris", "city": "Paris", "country": "France", "lat": 48.8665, "lon": 2.3013, "founded": 1951, "type": "Cabaret/Variety", "era": "1951-present", "description": "Avant-garde cabaret combining choreography and light art"},
    {"name": "Hackney Empire", "city": "London", "country": "UK", "lat": 51.5466, "lon": -0.0558, "founded": 1901, "type": "Music Hall", "era": "1901-present", "description": "Edwardian music hall where Charlie Chaplin and Stan Laurel performed"},
    {"name": "Lido de Paris", "city": "Paris", "country": "France", "lat": 48.8711, "lon": 2.3040, "founded": 1946, "type": "Cabaret/Revue", "era": "1946-2022", "description": "Champs-Elysees cabaret famous for Bluebell Girls and grand spectacle"},
    {"name": "Keith's New Theatre", "city": "Boston", "country": "USA", "lat": 42.3520, "lon": -71.0638, "founded": 1894, "type": "Vaudeville Temple", "era": "1894-1928", "description": "B.F. Keith's flagship vaudeville house, birthplace of refined variety"},
    {"name": "Tivoli Gardens Theater", "city": "Copenhagen", "country": "Denmark", "lat": 55.6736, "lon": 12.5681, "founded": 1843, "type": "Pleasure Garden", "era": "1843-present", "description": "World's oldest amusement park with pantomime theater and variety"},
    {"name": "Coliseum Theatre", "city": "London", "country": "UK", "lat": 51.5097, "lon": -0.1266, "founded": 1904, "type": "Variety/Opera", "era": "1904-present", "description": "Oswald Stoll's variety palace, now English National Opera"},
    {"name": "Ronacher Theater", "city": "Vienna", "country": "Austria", "lat": 48.2045, "lon": 16.3730, "founded": 1872, "type": "Variete", "era": "1872-present", "description": "Historic Viennese variety theater now hosting musicals"},
    {"name": "Teatro Colon Variety", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6011, "lon": -58.3833, "founded": 1857, "type": "Opera/Variety", "era": "1857-present", "description": "Grand opera house that also hosted variety and circus acts"},
    {"name": "Pantages Theatre", "city": "Hollywood", "country": "USA", "lat": 34.1017, "lon": -118.3256, "founded": 1930, "type": "Vaudeville/Film", "era": "1930-present", "description": "Art Deco vaudeville palace turned premiere movie and show venue"},
    {"name": "Chicago Theatre", "city": "Chicago", "country": "USA", "lat": 41.8854, "lon": -87.6275, "founded": 1921, "type": "Movie Palace/Variety", "era": "1921-present", "description": "Lavish movie palace with live variety acts and iconic marquee"},
    {"name": "Empire Leicester Square", "city": "London", "country": "UK", "lat": 51.5103, "lon": -0.1304, "founded": 1884, "type": "Music Hall/Cinema", "era": "1884-present", "description": "Victorian music hall turned cinema at the heart of Theatreland"},
    {"name": "Cabaret Voltaire", "city": "Zurich", "country": "Switzerland", "lat": 47.3738, "lon": 8.5435, "founded": 1916, "type": "Avant-garde Cabaret", "era": "1916-present", "description": "Birthplace of Dadaism - avant-garde variety shows and performance art"},
    {"name": "Tigerpalast", "city": "Frankfurt", "country": "Germany", "lat": 50.1109, "lon": 8.6821, "founded": 1988, "type": "Variete/Dinner", "era": "1988-present", "description": "Frankfurt's premier variety dinner theater with world-class acts"},
    {"name": "Cotton Club (Revival)", "city": "New York", "country": "USA", "lat": 40.8180, "lon": -73.9513, "founded": 1923, "type": "Jazz/Variety Club", "era": "1923-1940", "description": "Legendary Harlem jazz and variety club, Duke Ellington's stage"},
    {"name": "Scala London (Original)", "city": "London", "country": "UK", "lat": 51.5300, "lon": -0.1205, "founded": 1772, "type": "Music Hall", "era": "1772-present", "description": "One of London's oldest entertainment venues, now live music venue"},
]


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def _get_data_for_mode(mode: str) -> list:
    """Return the hardcoded data list for the given mode."""
    mapping = {
        "Historic Circus Venues": HISTORIC_CIRCUS,
        "Cirque du Soleil & Modern Circus": MODERN_CIRCUS,
        "Street Performance Capitals": STREET_PERFORMANCE,
        "Magic & Illusion Schools": MAGIC_SCHOOLS,
        "Carnival & Mardi Gras Traditions": CARNIVAL_DATA,
        "Puppet Theater Heritage": PUPPET_THEATER,
        "Acrobatic & Gymnastic Schools": ACROBATIC_SCHOOLS,
        "Clown & Comedy Festivals": CLOWN_FESTIVALS,
        "Fire Performance Traditions": FIRE_PERFORMANCE,
        "Vaudeville & Variety Theater": VAUDEVILLE_DATA,
    }
    return mapping.get(mode, [])


def _build_dataframe(mode: str) -> pd.DataFrame:
    """Build a DataFrame from the hardcoded data for the given mode."""
    data = _get_data_for_mode(mode)
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def _popup_html(row: pd.Series, mode: str) -> str:
    """Build a rich HTML popup for a folium marker."""
    name = html_module.escape(str(row.get("name", "Unknown")))
    desc = html_module.escape(str(row.get("description", "")))
    city = html_module.escape(str(row.get("city", "")))
    country = html_module.escape(str(row.get("country", "")))
    lat = row.get("lat", 0)
    lon = row.get("lon", 0)

    extra_rows = ""
    optional_keys = [
        "founded", "type", "tradition", "specialty", "show", "era",
        "capacity", "visitors", "duration", "pattern",
    ]
    for key in optional_keys:
        val = row.get(key)
        if val is not None and str(val) != "nan" and str(val) != "":
            label = key.replace("_", " ").title()
            extra_rows += (
                f'<tr><td style="color:#8b97b0;padding:2px 8px 2px 0;">{label}</td>'
                f'<td style="color:#e8ecf4;padding:2px 0;">{html_module.escape(str(val))}</td></tr>'
            )

    return f"""
    <div style="font-family:Inter,sans-serif;background:#111827;color:#e8ecf4;
                padding:12px;border-radius:8px;min-width:240px;max-width:320px;
                border:1px solid #2a3550;">
        <div style="font-size:14px;font-weight:700;color:#ec4899;margin-bottom:4px;">
            {name}
        </div>
        <div style="font-size:11px;color:#8b97b0;margin-bottom:6px;">
            {city}, {country} &bull; {lat:.4f}, {lon:.4f}
        </div>
        <table style="font-size:12px;border-collapse:collapse;margin-bottom:6px;">
            {extra_rows}
        </table>
        <div style="font-size:12px;color:#cbd5e1;line-height:1.4;">
            {desc}
        </div>
    </div>
    """


def _marker_color(mode: str) -> str:
    """Return a folium marker color for the mode."""
    color_map = {
        "Historic Circus Venues": "pink",
        "Cirque du Soleil & Modern Circus": "purple",
        "Street Performance Capitals": "cadetblue",
        "Magic & Illusion Schools": "orange",
        "Carnival & Mardi Gras Traditions": "green",
        "Puppet Theater Heritage": "orange",
        "Acrobatic & Gymnastic Schools": "red",
        "Clown & Comedy Festivals": "beige",
        "Fire Performance Traditions": "darkred",
        "Vaudeville & Variety Theater": "darkpurple",
    }
    return color_map.get(mode, "blue")


def _marker_icon(mode: str) -> str:
    """Return a Font Awesome icon for the mode."""
    icon_map = {
        "Historic Circus Venues": "star",
        "Cirque du Soleil & Modern Circus": "certificate",
        "Street Performance Capitals": "music",
        "Magic & Illusion Schools": "magic",
        "Carnival & Mardi Gras Traditions": "mask",
        "Puppet Theater Heritage": "hand-paper",
        "Acrobatic & Gymnastic Schools": "child",
        "Clown & Comedy Festivals": "smile",
        "Fire Performance Traditions": "fire",
        "Vaudeville & Variety Theater": "theater-masks",
    }
    return icon_map.get(mode, "info-sign")


def _get_group_col(mode: str) -> str:
    """Return the best column to group by for each mode."""
    mapping = {
        "Historic Circus Venues": "type",
        "Cirque du Soleil & Modern Circus": "type",
        "Street Performance Capitals": "tradition",
        "Magic & Illusion Schools": "type",
        "Carnival & Mardi Gras Traditions": "type",
        "Puppet Theater Heritage": "type",
        "Acrobatic & Gymnastic Schools": "type",
        "Clown & Comedy Festivals": "type",
        "Fire Performance Traditions": "type",
        "Vaudeville & Variety Theater": "type",
    }
    return mapping.get(mode, "type")


def _get_mode_description(mode: str) -> str:
    """Return a short description for each map mode."""
    descriptions = {
        "Historic Circus Venues": "Legendary circus buildings, big tops, and arenas spanning from ancient Rome to 20th century touring circuses. These venues shaped the art of circus performance worldwide.",
        "Cirque du Soleil & Modern Circus": "Contemporary nouveau cirque companies, resident shows in Las Vegas, and innovative troupes reinventing circus arts for the 21st century.",
        "Street Performance Capitals": "The world's greatest busking pitches, street performance squares, and public spaces where live entertainment thrives in the open air.",
        "Magic & Illusion Schools": "Magic societies, schools, clubs, and theaters dedicated to the art of prestidigitation, from historic institutions to modern training centers.",
        "Carnival & Mardi Gras Traditions": "Global carnival heritage from Rio to Venice, Mardi Gras to Fasching - the wildest street celebrations and their deep cultural roots.",
        "Puppet Theater Heritage": "Puppetry traditions from Bunraku to Wayang, marionettes to shadow puppets - the ancient and modern art of bringing figures to life.",
        "Acrobatic & Gymnastic Schools": "Professional circus training schools, national acrobatics academies, and youth circuses developing the next generation of aerialists and acrobats.",
        "Clown & Comedy Festivals": "Clown conventions, comedy festivals, and gatherings celebrating the art of laughter, from Edinburgh Fringe to world clown congresses.",
        "Fire Performance Traditions": "Ancient fire festivals, modern fire arts gatherings, and cultural traditions where flame becomes a tool for spectacle and ritual.",
        "Vaudeville & Variety Theater": "Historic vaudeville palaces, cabarets, music halls, and variety theaters that defined popular entertainment before cinema and television.",
    }
    return descriptions.get(mode, "")


# ===================================================================
# MAIN RENDER FUNCTION
# ===================================================================

def render_circus_maps_tab():
    """Main render function for the Circus & Performance Explorer tab."""

    # -- Header --
    st.markdown(
        '<div class="tab-header pink"><h4>Circus & Performance Explorer</h4>'
        '<p>Historic circuses, street performance traditions, magic schools &amp; carnival heritage</p></div>',
        unsafe_allow_html=True,
    )

    # ============================================
    # SECTION 1: Mode Selection & Controls
    # ============================================
    st.markdown("#### Map Mode")

    mode_options = [
        "Historic Circus Venues",
        "Cirque du Soleil & Modern Circus",
        "Street Performance Capitals",
        "Magic & Illusion Schools",
        "Carnival & Mardi Gras Traditions",
        "Puppet Theater Heritage",
        "Acrobatic & Gymnastic Schools",
        "Clown & Comedy Festivals",
        "Fire Performance Traditions",
        "Vaudeville & Variety Theater",
    ]

    mode = st.selectbox(
        "Select Circus & Performance Category",
        mode_options,
        key="circus_maps_mode",
        help="Choose a category of circus and performance heritage to explore",
    )

    # Display mode description
    mode_desc = _get_mode_description(mode)
    mode_color = MODE_COLORS.get(mode, ACCENT_COLOR)
    st.markdown(
        f'<div style="background:{SURFACE_COLOR};border-left:3px solid {mode_color};'
        f'padding:10px 14px;border-radius:4px;margin:8px 0 16px 0;'
        f'color:{TEXT_COLOR};font-size:14px;">{html_module.escape(mode_desc)}</div>',
        unsafe_allow_html=True,
    )

    # Controls row
    col_cluster, col_search = st.columns(2)
    with col_cluster:
        use_clustering = st.checkbox(
            "Cluster markers", value=True, key="circus_cluster",
            help="Group nearby markers into clusters",
        )
    with col_search:
        search_text = st.text_input(
            "Search locations",
            key="circus_search",
            placeholder="e.g. Paris, marionette, fire...",
        )

    # ============================================
    # SECTION 2: Build & Filter Data
    # ============================================
    df = _build_dataframe(mode)

    if df.empty:
        st.warning("No data available for this mode.")
        return

    # Apply text search filter
    filtered = df.copy()
    if search_text and search_text.strip():
        search_lower = search_text.strip().lower()
        mask = pd.Series(False, index=filtered.index)
        for col in filtered.columns:
            if filtered[col].dtype == object:
                mask = mask | filtered[col].astype(str).str.lower().str.contains(
                    search_lower, na=False
                )
        filtered = filtered[mask]

    if filtered.empty:
        st.warning("No locations match your current search. Try broadening your query.")
        return

    # ============================================
    # SECTION 3: Statistics Dashboard
    # ============================================
    st.markdown("---")
    st.markdown("#### Statistics")

    total_locations = len(filtered)
    total_unfiltered = len(df)
    group_col = _get_group_col(mode)
    unique_types = filtered[group_col].nunique() if group_col in filtered.columns else 0
    unique_countries = filtered["country"].nunique() if "country" in filtered.columns else 0

    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        delta = None if total_locations == total_unfiltered else f"{total_locations - total_unfiltered}"
        st.metric("Locations Shown", f"{total_locations}", delta=delta)
    with stat2:
        st.metric("Unique Categories", f"{unique_types}")
    with stat3:
        st.metric("Countries", f"{unique_countries}")
    with stat4:
        northern = (filtered["lat"] > 0).sum()
        southern = (filtered["lat"] <= 0).sum()
        st.metric("N / S Hemisphere", f"{northern} / {southern}")

    # Extra stats for modes with numeric data
    if "capacity" in filtered.columns:
        caps = filtered["capacity"].dropna()
        caps = caps[caps > 0]
        if len(caps) > 0:
            s1, s2, s3, s4 = st.columns(4)
            with s1:
                st.metric("Total Capacity", f"{int(caps.sum()):,}")
            with s2:
                st.metric("Largest Venue", f"{int(caps.max()):,}")
            with s3:
                st.metric("Average Capacity", f"{int(caps.mean()):,}")
            with s4:
                st.metric("Venues with Data", f"{len(caps)}")

    if "visitors" in filtered.columns:
        vis = filtered["visitors"].dropna()
        if len(vis) > 0:
            v1, v2, v3, v4 = st.columns(4)
            with v1:
                st.metric("Total Annual Visitors", f"{int(vis.sum()):,}")
            with v2:
                st.metric("Largest Festival", f"{int(vis.max()):,}")
            with v3:
                st.metric("Average Visitors", f"{int(vis.mean()):,}")
            with v4:
                st.metric("Festivals with Data", f"{len(vis)}")

    # ============================================
    # SECTION 4: Interactive Map
    # ============================================
    st.markdown("---")
    st.markdown("#### Interactive Map")
    st.caption(f"Showing {total_locations} locations | Mode: {mode}")

    with st.spinner("Generating circus map..."):
        center_lat = filtered["lat"].mean()
        center_lon = filtered["lon"].mean()
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=3,
            tiles="CartoDB dark_matter",
            width="100%",
            height=500,
        )

        marker_color = _marker_color(mode)
        marker_icon = _marker_icon(mode)

        if use_clustering:
            cluster = MarkerCluster(name=mode)
            for _, row in filtered.iterrows():
                popup_content = _popup_html(row, mode)
                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=folium.Popup(popup_content, max_width=340),
                    tooltip=str(row.get("name", "")),
                    icon=folium.Icon(color=marker_color, icon=marker_icon, prefix="fa"),
                ).add_to(cluster)
            cluster.add_to(m)
        else:
            for _, row in filtered.iterrows():
                popup_content = _popup_html(row, mode)
                folium.Marker(
                    location=[row["lat"], row["lon"]],
                    popup=folium.Popup(popup_content, max_width=340),
                    tooltip=str(row.get("name", "")),
                    icon=folium.Icon(color=marker_color, icon=marker_icon, prefix="fa"),
                ).add_to(m)

        st_html(m._repr_html_(), height=500)

    # ============================================
    # SECTION 5: Data Table
    # ============================================
    st.markdown("---")
    st.markdown("#### Location Data")

    display_cols = ["name"]
    if "city" in filtered.columns:
        display_cols.append("city")
    if "country" in filtered.columns:
        display_cols.append("country")
    display_cols.extend(["lat", "lon"])
    for optional in [
        "founded", "type", "tradition", "specialty", "show", "era",
        "capacity", "visitors", "duration", "description",
    ]:
        if optional in filtered.columns:
            display_cols.append(optional)

    # Remove duplicates while preserving order
    seen = set()
    ordered_cols = []
    for c in display_cols:
        if c not in seen and c in filtered.columns:
            seen.add(c)
            ordered_cols.append(c)

    display_df = filtered[ordered_cols].reset_index(drop=True)
    display_df.index = display_df.index + 1
    display_df.index.name = "#"

    st.dataframe(display_df, use_container_width=True)

    # ============================================
    # SECTION 6: CSV Download
    # ============================================
    csv_buffer = io.StringIO()
    display_df.to_csv(csv_buffer, index=True)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    safe_name = mode.lower().replace(" ", "_").replace("&", "and").replace("/", "_")

    st.download_button(
        label=f"Download {mode} CSV ({total_locations} locations)",
        data=csv_bytes,
        file_name=f"terrascout_circus_{safe_name}.csv",
        mime="text/csv",
        key=f"circus_download_{safe_name}",
    )

    # ============================================
    # SECTION 7: Notable Highlights
    # ============================================
    st.markdown("---")
    st.markdown("#### Notable Highlights")

    highlights = filtered.head(5)
    for _, row in highlights.iterrows():
        name = html_module.escape(str(row.get("name", "Unknown")))
        desc = html_module.escape(str(row.get("description", "")))
        lat = row.get("lat", 0)
        lon = row.get("lon", 0)

        extra_bits = []
        for key in ["founded", "type", "tradition", "specialty", "show", "era",
                     "capacity", "visitors", "duration", "country"]:
            val = row.get(key)
            if val is not None and str(val) != "nan" and str(val) != "":
                extra_bits.append(f"{key.replace('_', ' ').title()}: {html_module.escape(str(val))}")
        extra_line = " | ".join(extra_bits) if extra_bits else ""

        st.markdown(
            f'<div style="background:{SURFACE_COLOR};border-left:3px solid {mode_color};'
            f'padding:12px 16px;border-radius:6px;margin-bottom:10px;">'
            f'<b style="color:{mode_color};font-size:15px;">{name}</b>'
            f'<span style="color:{MUTED_COLOR};font-size:12px;margin-left:12px;">'
            f'{lat:.4f}, {lon:.4f}</span><br>'
            f'{f"<span style=color:{TEXT_COLOR};font-size:12px;>{extra_line}</span><br>" if extra_line else ""}'
            f'<span style="color:{TEXT_COLOR};font-size:13px;">{desc}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ============================================
    # SECTION 8: Fun Facts
    # ============================================
    st.markdown("---")
    st.markdown("#### Did You Know?")

    fun_facts = {
        "Historic Circus Venues": [
            "Philip Astley established the modern circus ring diameter of 42 feet (13m) in 1773 - still the standard today.",
            "The Circus Maximus in Rome could hold 250,000 spectators, dwarfing any modern stadium.",
            "Circus Krone in Munich is the largest permanent circus building in Europe, seating 3,000 people.",
            "The word 'circus' comes from the Latin word for 'circle' or 'ring'.",
        ],
        "Cirque du Soleil & Modern Circus": [
            "Cirque du Soleil was started by two former street performers, Guy Laliberte and Gilles Ste-Croix.",
            "The 'O' show at the Bellagio uses a 1.5 million gallon pool that can transform into a solid stage.",
            "Cirque du Soleil has entertained over 200 million spectators in over 60 countries.",
            "The company was founded in 1984 in Baie-Saint-Paul, Quebec, Canada.",
        ],
        "Street Performance Capitals": [
            "Covent Garden in London has the oldest licensed busking program, requiring performers to audition.",
            "Djemaa el-Fna in Marrakech is UNESCO-recognized as a Masterpiece of Oral and Intangible Heritage.",
            "Edinburgh Fringe Festival hosts over 3,500 shows annually, making it the world's largest arts festival.",
            "The term 'busking' likely derives from the Spanish word 'buscar' meaning 'to seek'.",
        ],
        "Magic & Illusion Schools": [
            "The Magic Castle in Hollywood requires formal attire and membership or invitation to enter.",
            "Harry Houdini served as president of the Society of American Magicians from 1917 until his death in 1926.",
            "Jean-Eugene Robert-Houdin, the father of modern magic, inspired the stage name 'Houdini'.",
            "The Magic Circle's motto is 'Indocilis Privata Loqui' - 'Not apt to disclose secrets'.",
        ],
        "Carnival & Mardi Gras Traditions": [
            "Rio Carnival attracts 5 million visitors annually, making it the world's largest carnival.",
            "Venice Carnival masks were originally worn to blur social class distinctions.",
            "Mardi Gras in New Orleans dates back to 1699 when French explorers held a small celebration.",
            "The Carnival of Binche's Gilles costumes weigh up to 40kg with their wax masks and ostrich plumes.",
        ],
        "Puppet Theater Heritage": [
            "Vietnamese water puppetry is over 1,000 years old, originally performed in flooded rice paddies.",
            "The Salzburg Marionette Theatre has performed for over 110 years and is UNESCO-recognized.",
            "Bunraku puppets require three operators each - one for the head and right hand, one for the left hand, and one for the feet.",
            "Jim Henson's Muppets were named by combining 'marionette' and 'puppet'.",
        ],
        "Acrobatic & Gymnastic Schools": [
            "The Ecole Nationale de Cirque in Montreal has trained most Cirque du Soleil performers.",
            "Chinese acrobatics tradition dates back over 2,000 years to the Han Dynasty.",
            "Mongolia's National Circus School is world-renowned for producing extraordinary contortionists.",
            "The Flying Fruit Fly Circus in Australia has been training youth performers since 1979.",
        ],
        "Clown & Comedy Festivals": [
            "Joseph Grimaldi (1778-1837) is considered the father of modern clowning - clowns are called 'Joeys' in his honor.",
            "The Clowns International egg register paints each clown's unique face on an egg to record their design.",
            "Just for Laughs in Montreal is the world's largest comedy festival, running since 1983.",
            "Dr. Patch Adams has led over 100 clown trips to hospitals in 50+ countries.",
        ],
        "Fire Performance Traditions": [
            "Modern fire poi originated from the Maori people of New Zealand, who used it for training and rituals.",
            "The Burning Man effigy has grown from 8 feet tall in 1986 to over 100 feet in recent years.",
            "Las Fallas in Valencia burns over 700 artistic sculptures in a single night.",
            "Up Helly Aa in Shetland is Europe's largest fire festival, with a full-size Viking longship burned.",
        ],
        "Vaudeville & Variety Theater": [
            "The Palace Theatre in New York was so prestigious that 'playing the Palace' became the ultimate goal.",
            "The Moulin Rouge's famous cancan dance was considered scandalous when it debuted in 1889.",
            "Charlie Chaplin got his start performing at the Hackney Empire music hall in London.",
            "Cabaret Voltaire in Zurich gave birth to the Dada art movement in 1916.",
        ],
    }

    facts = fun_facts.get(mode, ["No additional facts available for this category."])
    for fact in facts:
        st.markdown(
            f'<div style="background:{SURFACE_COLOR};padding:10px 14px;border-radius:4px;'
            f'margin-bottom:6px;color:{TEXT_COLOR};font-size:13px;'
            f'border-left:2px solid {mode_color};">'
            f'{html_module.escape(fact)}</div>',
            unsafe_allow_html=True,
        )

    # ============================================
    # SECTION 9: Footer
    # ============================================
    st.markdown("---")
    st.caption(
        f"Data: {total_locations} curated locations for {mode}. "
        "All data is hardcoded for offline reliability. "
        "Coordinates are approximate and may represent general area locations."
    )
