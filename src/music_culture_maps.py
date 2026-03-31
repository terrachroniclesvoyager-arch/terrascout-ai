# -*- coding: utf-8 -*-
"""
Music & Culture Maps module for TerraScout AI.
Provides 10 interactive map types covering music genres, concert venues,
film locations, art movements, world festivals, museums, UNESCO intangible
heritage, cuisine capitals, Nobel laureate birthplaces, and famous authors.
All data is hardcoded for offline reliability.
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

# =====================================================================
# COLOUR HELPERS
# =====================================================================
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
ACCENT_CYAN = "#06b6d4"
ACCENT_PINK = "#ec4899"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_AMBER = "#f59e0b"
ACCENT_EMERALD = "#10b981"
ACCENT_RED = "#ef4444"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"

CATEGORY_COLORS = [
    "#06b6d4", "#ec4899", "#8b5cf6", "#f59e0b", "#10b981",
    "#ef4444", "#3b82f6", "#f97316", "#14b8a6", "#a855f7",
    "#e11d48", "#84cc16", "#facc15", "#22d3ee", "#c084fc",
]


def _color_for(index: int) -> str:
    return CATEGORY_COLORS[index % len(CATEGORY_COLORS)]


def _dark_fig(rows=1, cols=1, figsize=(10, 5)):
    fig, ax = plt.subplots(rows, cols, figsize=figsize, facecolor=BG_DARK)
    if rows == 1 and cols == 1:
        ax.set_facecolor(SURFACE)
        ax.tick_params(colors=TEXT_SECONDARY)
        ax.xaxis.label.set_color(TEXT_PRIMARY)
        ax.yaxis.label.set_color(TEXT_PRIMARY)
        ax.title.set_color(TEXT_PRIMARY)
        for spine in ax.spines.values():
            spine.set_color("#2a3550")
    return fig, ax


def _fig_to_bytes(fig) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _base_map(center=None, zoom=2):
    if center is None:
        center = [20, 0]
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        width="100%",
        height=550,
    )
    return m


def _show_map(m):
    components.html(m._repr_html_(), height=550)


def _df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# =====================================================================
# 1. MUSIC GENRE ORIGINS
# =====================================================================
MUSIC_GENRES = [
    {"genre": "Jazz", "origin_city": "New Orleans", "country": "USA", "decade": "1900s", "lat": 29.9511, "lon": -90.0715, "color": "#f59e0b", "icon": "music"},
    {"genre": "Blues", "origin_city": "Mississippi Delta", "country": "USA", "decade": "1860s", "lat": 33.4504, "lon": -90.8429, "color": "#3b82f6", "icon": "music"},
    {"genre": "Rock and Roll", "origin_city": "Memphis", "country": "USA", "decade": "1950s", "lat": 35.1495, "lon": -90.0490, "color": "#ef4444", "icon": "music"},
    {"genre": "Reggae", "origin_city": "Kingston", "country": "Jamaica", "decade": "1960s", "lat": 18.0179, "lon": -76.8099, "color": "#10b981", "icon": "music"},
    {"genre": "Hip-Hop", "origin_city": "New York City", "country": "USA", "decade": "1970s", "lat": 40.8176, "lon": -73.9209, "color": "#8b5cf6", "icon": "music"},
    {"genre": "Samba", "origin_city": "Rio de Janeiro", "country": "Brazil", "decade": "1910s", "lat": -22.9068, "lon": -43.1729, "color": "#06b6d4", "icon": "music"},
    {"genre": "Bossa Nova", "origin_city": "Rio de Janeiro", "country": "Brazil", "decade": "1950s", "lat": -22.9568, "lon": -43.1829, "color": "#14b8a6", "icon": "music"},
    {"genre": "Fado", "origin_city": "Lisbon", "country": "Portugal", "decade": "1820s", "lat": 38.7223, "lon": -9.1393, "color": "#a855f7", "icon": "music"},
    {"genre": "Flamenco", "origin_city": "Seville", "country": "Spain", "decade": "1700s", "lat": 37.3891, "lon": -5.9845, "color": "#e11d48", "icon": "music"},
    {"genre": "Tango", "origin_city": "Buenos Aires", "country": "Argentina", "decade": "1880s", "lat": -34.6037, "lon": -58.3816, "color": "#ec4899", "icon": "music"},
    {"genre": "K-Pop", "origin_city": "Seoul", "country": "South Korea", "decade": "1990s", "lat": 37.5665, "lon": 126.9780, "color": "#f97316", "icon": "music"},
    {"genre": "Afrobeat", "origin_city": "Lagos", "country": "Nigeria", "decade": "1960s", "lat": 6.5244, "lon": 3.3792, "color": "#84cc16", "icon": "music"},
    {"genre": "Highlife", "origin_city": "Accra", "country": "Ghana", "decade": "1920s", "lat": 5.6037, "lon": -0.1870, "color": "#facc15", "icon": "music"},
    {"genre": "Punk Rock", "origin_city": "London", "country": "UK", "decade": "1970s", "lat": 51.5074, "lon": -0.1278, "color": "#ef4444", "icon": "music"},
    {"genre": "Heavy Metal", "origin_city": "Birmingham", "country": "UK", "decade": "1960s", "lat": 52.4862, "lon": -1.8904, "color": "#6b7280", "icon": "music"},
    {"genre": "Electronic / Techno", "origin_city": "Detroit", "country": "USA", "decade": "1980s", "lat": 42.3314, "lon": -83.0458, "color": "#22d3ee", "icon": "music"},
    {"genre": "House Music", "origin_city": "Chicago", "country": "USA", "decade": "1980s", "lat": 41.8781, "lon": -87.6298, "color": "#c084fc", "icon": "music"},
    {"genre": "Grunge", "origin_city": "Seattle", "country": "USA", "decade": "1980s", "lat": 47.6062, "lon": -122.3321, "color": "#78716c", "icon": "music"},
    {"genre": "Country", "origin_city": "Nashville", "country": "USA", "decade": "1920s", "lat": 36.1627, "lon": -86.7816, "color": "#d97706", "icon": "music"},
    {"genre": "Calypso", "origin_city": "Port of Spain", "country": "Trinidad", "decade": "1900s", "lat": 10.6596, "lon": -61.5086, "color": "#0ea5e9", "icon": "music"},
    {"genre": "Raga / Classical", "origin_city": "Varanasi", "country": "India", "decade": "Ancient", "lat": 25.3176, "lon": 82.9739, "color": "#f43f5e", "icon": "music"},
    {"genre": "Gamelan", "origin_city": "Yogyakarta", "country": "Indonesia", "decade": "Ancient", "lat": -7.7972, "lon": 110.3688, "color": "#a3e635", "icon": "music"},
    {"genre": "Mariachi", "origin_city": "Guadalajara", "country": "Mexico", "decade": "1700s", "lat": 20.6597, "lon": -103.3496, "color": "#16a34a", "icon": "music"},
    {"genre": "Cumbia", "origin_city": "Barranquilla", "country": "Colombia", "decade": "1800s", "lat": 10.9685, "lon": -74.7813, "color": "#fb923c", "icon": "music"},
    {"genre": "Salsa", "origin_city": "Havana / New York", "country": "Cuba / USA", "decade": "1960s", "lat": 23.1136, "lon": -82.3666, "color": "#dc2626", "icon": "music"},
    {"genre": "Disco", "origin_city": "Philadelphia", "country": "USA", "decade": "1970s", "lat": 39.9526, "lon": -75.1652, "color": "#d946ef", "icon": "music"},
    {"genre": "Grime", "origin_city": "London", "country": "UK", "decade": "2000s", "lat": 51.5374, "lon": -0.0678, "color": "#475569", "icon": "music"},
]


@st.cache_data(ttl=3600)
def _get_music_genres():
    return pd.DataFrame(MUSIC_GENRES)


# =====================================================================
# 2. FAMOUS CONCERT VENUES
# =====================================================================
CONCERT_VENUES = [
    {"venue": "Madison Square Garden", "city": "New York City", "country": "USA", "capacity": 20789, "opened": 1968, "lat": 40.7505, "lon": -73.9934},
    {"venue": "Royal Albert Hall", "city": "London", "country": "UK", "capacity": 5272, "opened": 1871, "lat": 51.5009, "lon": -0.1774},
    {"venue": "Red Rocks Amphitheatre", "city": "Morrison, CO", "country": "USA", "capacity": 9525, "opened": 1906, "lat": 39.6654, "lon": -105.2057},
    {"venue": "Sydney Opera House", "city": "Sydney", "country": "Australia", "capacity": 5738, "opened": 1973, "lat": -33.8568, "lon": 151.2153},
    {"venue": "Carnegie Hall", "city": "New York City", "country": "USA", "capacity": 2804, "opened": 1891, "lat": 40.7651, "lon": -73.9799},
    {"venue": "The O2 Arena", "city": "London", "country": "UK", "capacity": 20000, "opened": 2007, "lat": 51.5030, "lon": 0.0032},
    {"venue": "Hollywood Bowl", "city": "Los Angeles", "country": "USA", "capacity": 17500, "opened": 1922, "lat": 34.1122, "lon": -118.3391},
    {"venue": "Wembley Stadium", "city": "London", "country": "UK", "capacity": 90000, "opened": 2007, "lat": 51.5560, "lon": -0.2795},
    {"venue": "Budokan", "city": "Tokyo", "country": "Japan", "capacity": 14471, "opened": 1964, "lat": 35.6934, "lon": 139.7500},
    {"venue": "Olympia Paris", "city": "Paris", "country": "France", "capacity": 1996, "opened": 1893, "lat": 48.8698, "lon": 2.3282},
    {"venue": "Ryman Auditorium", "city": "Nashville", "country": "USA", "capacity": 2362, "opened": 1892, "lat": 36.1612, "lon": -86.7769},
    {"venue": "Apollo Theater", "city": "New York City", "country": "USA", "capacity": 1506, "opened": 1914, "lat": 40.8100, "lon": -73.9500},
    {"venue": "Zenith Paris", "city": "Paris", "country": "France", "capacity": 6293, "opened": 1984, "lat": 48.8938, "lon": 2.3934},
    {"venue": "Fillmore", "city": "San Francisco", "country": "USA", "capacity": 1315, "opened": 1912, "lat": 37.7842, "lon": -122.4330},
    {"venue": "Paradiso", "city": "Amsterdam", "country": "Netherlands", "capacity": 1500, "opened": 1968, "lat": 52.3622, "lon": 4.8838},
    {"venue": "Brixton Academy", "city": "London", "country": "UK", "capacity": 4921, "opened": 1929, "lat": 51.4613, "lon": -0.1148},
    {"venue": "Estadio Azteca", "city": "Mexico City", "country": "Mexico", "capacity": 87523, "opened": 1966, "lat": 19.3029, "lon": -99.1506},
    {"venue": "Maracana", "city": "Rio de Janeiro", "country": "Brazil", "capacity": 78838, "opened": 1950, "lat": -22.9121, "lon": -43.2302},
    {"venue": "Berghain", "city": "Berlin", "country": "Germany", "capacity": 1500, "opened": 2004, "lat": 52.5112, "lon": 13.4433},
    {"venue": "Arena di Verona", "city": "Verona", "country": "Italy", "capacity": 15000, "opened": 30, "lat": 45.4392, "lon": 10.9942},
    {"venue": "Concertgebouw", "city": "Amsterdam", "country": "Netherlands", "capacity": 2037, "opened": 1888, "lat": 52.3563, "lon": 4.8790},
    {"venue": "La Scala", "city": "Milan", "country": "Italy", "capacity": 2030, "opened": 1778, "lat": 45.4675, "lon": 9.1895},
    {"venue": "Vienna State Opera", "city": "Vienna", "country": "Austria", "capacity": 2284, "opened": 1869, "lat": 48.2035, "lon": 16.3689},
    {"venue": "Blue Note", "city": "New York City", "country": "USA", "capacity": 250, "opened": 1981, "lat": 40.7310, "lon": -74.0005},
    {"venue": "Cavern Club", "city": "Liverpool", "country": "UK", "capacity": 500, "opened": 1957, "lat": 53.4063, "lon": -2.9930},
    {"venue": "Montreux Jazz Cafe", "city": "Montreux", "country": "Switzerland", "capacity": 4000, "opened": 1967, "lat": 46.4312, "lon": 6.9107},
    {"venue": "Preservation Hall", "city": "New Orleans", "country": "USA", "capacity": 100, "opened": 1961, "lat": 29.9580, "lon": -90.0643},
    {"venue": "Vicar Street", "city": "Dublin", "country": "Ireland", "capacity": 1050, "opened": 1998, "lat": 53.3414, "lon": -6.2803},
    {"venue": "Shepherds Bush Empire", "city": "London", "country": "UK", "capacity": 2000, "opened": 1903, "lat": 51.5036, "lon": -0.2252},
    {"venue": "Ziggo Dome", "city": "Amsterdam", "country": "Netherlands", "capacity": 17000, "opened": 2012, "lat": 52.3142, "lon": 4.9370},
    {"venue": "AccorHotels Arena", "city": "Paris", "country": "France", "capacity": 20300, "opened": 1984, "lat": 48.8386, "lon": 2.3787},
]


@st.cache_data(ttl=3600)
def _get_concert_venues():
    return pd.DataFrame(CONCERT_VENUES)


# =====================================================================
# 3. FILM LOCATIONS
# =====================================================================
FILM_LOCATIONS = [
    {"film": "The Lord of the Rings", "location": "Matamata (Hobbiton)", "country": "New Zealand", "year": 2001, "lat": -37.8721, "lon": 175.6830},
    {"film": "Star Wars (Tatooine)", "location": "Matmata / Tozeur", "country": "Tunisia", "year": 1977, "lat": 33.5443, "lon": 7.9757},
    {"film": "The Sound of Music", "location": "Salzburg", "country": "Austria", "year": 1965, "lat": 47.8095, "lon": 13.0550},
    {"film": "Roman Holiday", "location": "Rome", "country": "Italy", "year": 1953, "lat": 41.9028, "lon": 12.4964},
    {"film": "Amelie", "location": "Montmartre, Paris", "country": "France", "year": 2001, "lat": 48.8867, "lon": 2.3431},
    {"film": "Harry Potter", "location": "Alnwick Castle", "country": "UK", "year": 2001, "lat": 55.4155, "lon": -1.7058},
    {"film": "Indiana Jones (Petra)", "location": "Petra", "country": "Jordan", "year": 1989, "lat": 30.3285, "lon": 35.4444},
    {"film": "The Beach", "location": "Maya Bay, Koh Phi Phi", "country": "Thailand", "year": 2000, "lat": 7.6781, "lon": 98.7650},
    {"film": "Braveheart", "location": "Glen Nevis", "country": "UK (Scotland)", "year": 1995, "lat": 56.7964, "lon": -5.0067},
    {"film": "James Bond (Skyfall)", "location": "Glencoe", "country": "UK (Scotland)", "year": 2012, "lat": 56.6833, "lon": -5.1024},
    {"film": "Lost in Translation", "location": "Tokyo", "country": "Japan", "year": 2003, "lat": 35.6762, "lon": 139.6503},
    {"film": "Midnight in Paris", "location": "Paris", "country": "France", "year": 2011, "lat": 48.8566, "lon": 2.3522},
    {"film": "The Godfather", "location": "Savoca, Sicily", "country": "Italy", "year": 1972, "lat": 37.9533, "lon": 15.3414},
    {"film": "Lawrence of Arabia", "location": "Wadi Rum", "country": "Jordan", "year": 1962, "lat": 29.5321, "lon": 35.4133},
    {"film": "Crouching Tiger Hidden Dragon", "location": "Zhangjiajie", "country": "China", "year": 2000, "lat": 29.1170, "lon": 110.4793},
    {"film": "Troy", "location": "Canakkale", "country": "Turkey", "year": 2004, "lat": 39.8568, "lon": 26.0588},
    {"film": "The Dark Knight", "location": "Chicago", "country": "USA", "year": 2008, "lat": 41.8781, "lon": -87.6298},
    {"film": "Mamma Mia!", "location": "Skopelos", "country": "Greece", "year": 2008, "lat": 39.1220, "lon": 23.7275},
    {"film": "Blade Runner 2049", "location": "Budapest", "country": "Hungary", "year": 2017, "lat": 47.4979, "lon": 19.0402},
    {"film": "Mission Impossible (Burj)", "location": "Dubai", "country": "UAE", "year": 2011, "lat": 25.1972, "lon": 55.2744},
    {"film": "The Grand Budapest Hotel", "location": "Gorlitz", "country": "Germany", "year": 2014, "lat": 51.1525, "lon": 14.9875},
    {"film": "Life of Pi", "location": "Pondicherry", "country": "India", "year": 2012, "lat": 11.9416, "lon": 79.8083},
    {"film": "Slumdog Millionaire", "location": "Mumbai", "country": "India", "year": 2008, "lat": 19.0760, "lon": 72.8777},
    {"film": "Casino Royale (Montenegro)", "location": "Karlovy Vary", "country": "Czech Republic", "year": 2006, "lat": 50.2316, "lon": 12.8711},
    {"film": "Gladiator", "location": "Ouarzazate", "country": "Morocco", "year": 2000, "lat": 30.9189, "lon": -6.8936},
    {"film": "Jurassic Park", "location": "Kauai, Hawaii", "country": "USA", "year": 1993, "lat": 22.0964, "lon": -159.5261},
    {"film": "The Revenant", "location": "Kananaskis, Alberta", "country": "Canada", "year": 2015, "lat": 50.9425, "lon": -115.1279},
    {"film": "Notting Hill", "location": "Notting Hill, London", "country": "UK", "year": 1999, "lat": 51.5115, "lon": -0.2059},
    {"film": "Eat Pray Love", "location": "Bali", "country": "Indonesia", "year": 2010, "lat": -8.3405, "lon": 115.0920},
    {"film": "Out of Africa", "location": "Nairobi", "country": "Kenya", "year": 1985, "lat": -1.2921, "lon": 36.8219},
    {"film": "The Motorcycle Diaries", "location": "Machu Picchu", "country": "Peru", "year": 2004, "lat": -13.1631, "lon": -72.5450},
]


@st.cache_data(ttl=3600)
def _get_film_locations():
    return pd.DataFrame(FILM_LOCATIONS)


# =====================================================================
# 4. ART MOVEMENTS
# =====================================================================
ART_MOVEMENTS = [
    {"movement": "Renaissance", "city": "Florence", "country": "Italy", "period": "1400-1600", "artists": "Da Vinci, Michelangelo, Botticelli", "lat": 43.7696, "lon": 11.2558, "color": "#f59e0b"},
    {"movement": "Impressionism", "city": "Paris", "country": "France", "period": "1860-1890", "artists": "Monet, Renoir, Degas", "lat": 48.8566, "lon": 2.3522, "color": "#3b82f6"},
    {"movement": "Surrealism", "city": "Paris", "country": "France", "period": "1920-1950", "artists": "Dali, Magritte, Ernst", "lat": 48.8666, "lon": 2.3622, "color": "#8b5cf6"},
    {"movement": "Cubism", "city": "Paris", "country": "France", "period": "1907-1920", "artists": "Picasso, Braque, Gris", "lat": 48.8466, "lon": 2.3422, "color": "#06b6d4"},
    {"movement": "Baroque", "city": "Rome", "country": "Italy", "period": "1600-1750", "artists": "Caravaggio, Bernini, Rubens", "lat": 41.9028, "lon": 12.4964, "color": "#ec4899"},
    {"movement": "Abstract Expressionism", "city": "New York City", "country": "USA", "period": "1940-1960", "artists": "Pollock, Rothko, de Kooning", "lat": 40.7128, "lon": -74.0060, "color": "#ef4444"},
    {"movement": "Pop Art", "city": "New York / London", "country": "USA / UK", "period": "1950-1970", "artists": "Warhol, Lichtenstein, Hockney", "lat": 40.7328, "lon": -73.9960, "color": "#10b981"},
    {"movement": "Bauhaus", "city": "Weimar / Dessau", "country": "Germany", "period": "1919-1933", "artists": "Klee, Kandinsky, Moholy-Nagy", "lat": 50.9795, "lon": 11.3235, "color": "#14b8a6"},
    {"movement": "Art Nouveau", "city": "Brussels / Paris", "country": "Belgium / France", "period": "1890-1910", "artists": "Mucha, Gaudi, Klimt", "lat": 50.8503, "lon": 4.3517, "color": "#a855f7"},
    {"movement": "Dutch Golden Age", "city": "Amsterdam", "country": "Netherlands", "period": "1588-1672", "artists": "Rembrandt, Vermeer, Hals", "lat": 52.3676, "lon": 4.9041, "color": "#d97706"},
    {"movement": "Ukiyo-e", "city": "Edo (Tokyo)", "country": "Japan", "period": "1603-1868", "artists": "Hokusai, Hiroshige, Utamaro", "lat": 35.6762, "lon": 139.6503, "color": "#e11d48"},
    {"movement": "Constructivism", "city": "Moscow", "country": "Russia", "period": "1913-1940", "artists": "Tatlin, Rodchenko, Lissitzky", "lat": 55.7558, "lon": 37.6173, "color": "#dc2626"},
    {"movement": "De Stijl", "city": "Leiden", "country": "Netherlands", "period": "1917-1931", "artists": "Mondrian, van Doesburg, Rietveld", "lat": 52.1601, "lon": 4.4970, "color": "#facc15"},
    {"movement": "Minimalism", "city": "New York City", "country": "USA", "period": "1960-1975", "artists": "Judd, Flavin, Andre", "lat": 40.7528, "lon": -73.9760, "color": "#6b7280"},
    {"movement": "Dadaism", "city": "Zurich", "country": "Switzerland", "period": "1916-1924", "artists": "Duchamp, Arp, Tzara", "lat": 47.3769, "lon": 8.5417, "color": "#78716c"},
    {"movement": "Romanticism", "city": "London / Paris", "country": "UK / France", "period": "1770-1850", "artists": "Turner, Delacroix, Friedrich", "lat": 51.5074, "lon": -0.1278, "color": "#fb923c"},
]


@st.cache_data(ttl=3600)
def _get_art_movements():
    return pd.DataFrame(ART_MOVEMENTS)


# =====================================================================
# 5. WORLD FESTIVALS
# =====================================================================
WORLD_FESTIVALS = [
    {"festival": "Carnival", "city": "Rio de Janeiro", "country": "Brazil", "month": "February", "type": "Cultural", "lat": -22.9068, "lon": -43.1729},
    {"festival": "Oktoberfest", "city": "Munich", "country": "Germany", "month": "September", "type": "Cultural", "lat": 48.1351, "lon": 11.5820},
    {"festival": "Diwali Festival of Lights", "city": "Varanasi", "country": "India", "month": "October/November", "type": "Religious", "lat": 25.3176, "lon": 82.9739},
    {"festival": "La Tomatina", "city": "Bunol", "country": "Spain", "month": "August", "type": "Cultural", "lat": 39.4197, "lon": -0.7905},
    {"festival": "Holi", "city": "Mathura", "country": "India", "month": "March", "type": "Religious", "lat": 27.4924, "lon": 77.6737},
    {"festival": "Mardi Gras", "city": "New Orleans", "country": "USA", "month": "February", "type": "Cultural", "lat": 29.9511, "lon": -90.0715},
    {"festival": "Chinese New Year", "city": "Beijing", "country": "China", "month": "January/February", "type": "Cultural", "lat": 39.9042, "lon": 116.4074},
    {"festival": "Burning Man", "city": "Black Rock City, NV", "country": "USA", "month": "August", "type": "Art", "lat": 40.7864, "lon": -119.2065},
    {"festival": "Day of the Dead", "city": "Oaxaca", "country": "Mexico", "month": "November", "type": "Cultural", "lat": 17.0732, "lon": -96.7266},
    {"festival": "Songkran", "city": "Bangkok", "country": "Thailand", "month": "April", "type": "Cultural", "lat": 13.7563, "lon": 100.5018},
    {"festival": "Edinburgh Fringe", "city": "Edinburgh", "country": "UK", "month": "August", "type": "Art", "lat": 55.9533, "lon": -3.1883},
    {"festival": "Glastonbury", "city": "Somerset", "country": "UK", "month": "June", "type": "Music", "lat": 51.1588, "lon": -2.5856},
    {"festival": "Coachella", "city": "Indio, CA", "country": "USA", "month": "April", "type": "Music", "lat": 33.6803, "lon": -116.2376},
    {"festival": "Tomorrowland", "city": "Boom", "country": "Belgium", "month": "July", "type": "Music", "lat": 51.0939, "lon": 4.3700},
    {"festival": "Notting Hill Carnival", "city": "London", "country": "UK", "month": "August", "type": "Cultural", "lat": 51.5115, "lon": -0.2059},
    {"festival": "Lantern Festival", "city": "Pingxi", "country": "Taiwan", "month": "February", "type": "Cultural", "lat": 25.0266, "lon": 121.7380},
    {"festival": "Venice Biennale", "city": "Venice", "country": "Italy", "month": "May-November", "type": "Art", "lat": 45.4408, "lon": 12.3155},
    {"festival": "Cannes Film Festival", "city": "Cannes", "country": "France", "month": "May", "type": "Film", "lat": 43.5528, "lon": 7.0174},
    {"festival": "Sundance Film Festival", "city": "Park City, UT", "country": "USA", "month": "January", "type": "Film", "lat": 40.6461, "lon": -111.4980},
    {"festival": "St. Patrick's Day", "city": "Dublin", "country": "Ireland", "month": "March", "type": "Cultural", "lat": 53.3498, "lon": -6.2603},
    {"festival": "Cherry Blossom Festival", "city": "Tokyo", "country": "Japan", "month": "March/April", "type": "Cultural", "lat": 35.6762, "lon": 139.6503},
    {"festival": "Inti Raymi", "city": "Cusco", "country": "Peru", "month": "June", "type": "Cultural", "lat": -13.5319, "lon": -71.9675},
    {"festival": "Bayreuth Festival", "city": "Bayreuth", "country": "Germany", "month": "July/August", "type": "Music", "lat": 49.9427, "lon": 11.5783},
    {"festival": "Salzburg Festival", "city": "Salzburg", "country": "Austria", "month": "July/August", "type": "Music", "lat": 47.8095, "lon": 13.0550},
    {"festival": "Running of the Bulls", "city": "Pamplona", "country": "Spain", "month": "July", "type": "Cultural", "lat": 42.8125, "lon": -1.6458},
    {"festival": "Loi Krathong", "city": "Chiang Mai", "country": "Thailand", "month": "November", "type": "Religious", "lat": 18.7883, "lon": 98.9853},
    {"festival": "Gion Matsuri", "city": "Kyoto", "country": "Japan", "month": "July", "type": "Cultural", "lat": 35.0116, "lon": 135.7681},
    {"festival": "Carnival of Venice", "city": "Venice", "country": "Italy", "month": "February", "type": "Cultural", "lat": 45.4408, "lon": 12.3255},
    {"festival": "Fete de la Musique", "city": "Paris", "country": "France", "month": "June", "type": "Music", "lat": 48.8566, "lon": 2.3522},
    {"festival": "Dia de los Muertos Parade", "city": "Mexico City", "country": "Mexico", "month": "November", "type": "Cultural", "lat": 19.4326, "lon": -99.1332},
]


@st.cache_data(ttl=3600)
def _get_world_festivals():
    return pd.DataFrame(WORLD_FESTIVALS)


# =====================================================================
# 6. TOP MUSEUMS
# =====================================================================
TOP_MUSEUMS = [
    {"museum": "Louvre", "city": "Paris", "country": "France", "visitors_m": 8.9, "founded": 1793, "highlight": "Mona Lisa", "lat": 48.8606, "lon": 2.3376},
    {"museum": "National Museum of China", "city": "Beijing", "country": "China", "visitors_m": 7.6, "founded": 2003, "highlight": "Ancient bronzes", "lat": 39.9042, "lon": 116.3912},
    {"museum": "Vatican Museums", "city": "Vatican City", "country": "Vatican", "visitors_m": 6.9, "founded": 1506, "highlight": "Sistine Chapel", "lat": 41.9065, "lon": 12.4536},
    {"museum": "Metropolitan Museum of Art", "city": "New York City", "country": "USA", "visitors_m": 6.5, "founded": 1870, "highlight": "Temple of Dendur", "lat": 40.7794, "lon": -73.9632},
    {"museum": "British Museum", "city": "London", "country": "UK", "visitors_m": 5.8, "founded": 1753, "highlight": "Rosetta Stone", "lat": 51.5194, "lon": -0.1270},
    {"museum": "Tate Modern", "city": "London", "country": "UK", "visitors_m": 5.9, "founded": 2000, "highlight": "Turbine Hall", "lat": 51.5076, "lon": -0.0994},
    {"museum": "National Gallery", "city": "London", "country": "UK", "visitors_m": 5.7, "founded": 1824, "highlight": "Sunflowers (van Gogh)", "lat": 51.5089, "lon": -0.1283},
    {"museum": "Hermitage Museum", "city": "St. Petersburg", "country": "Russia", "visitors_m": 4.2, "founded": 1764, "highlight": "Winter Palace", "lat": 59.9398, "lon": 30.3146},
    {"museum": "Uffizi Gallery", "city": "Florence", "country": "Italy", "visitors_m": 4.4, "founded": 1581, "highlight": "Birth of Venus", "lat": 43.7678, "lon": 11.2553},
    {"museum": "Rijksmuseum", "city": "Amsterdam", "country": "Netherlands", "visitors_m": 2.7, "founded": 1800, "highlight": "Night Watch", "lat": 52.3600, "lon": 4.8852},
    {"museum": "Museo del Prado", "city": "Madrid", "country": "Spain", "visitors_m": 3.5, "founded": 1819, "highlight": "Las Meninas", "lat": 40.4138, "lon": -3.6921},
    {"museum": "Musee d'Orsay", "city": "Paris", "country": "France", "visitors_m": 3.7, "founded": 1986, "highlight": "Starry Night Over the Rhone", "lat": 48.8600, "lon": 2.3266},
    {"museum": "National Palace Museum", "city": "Taipei", "country": "Taiwan", "visitors_m": 3.8, "founded": 1925, "highlight": "Jadeite Cabbage", "lat": 25.1024, "lon": 121.5485},
    {"museum": "Smithsonian NASM", "city": "Washington, D.C.", "country": "USA", "visitors_m": 6.2, "founded": 1976, "highlight": "Wright Flyer", "lat": 38.8882, "lon": -77.0199},
    {"museum": "MoMA", "city": "New York City", "country": "USA", "visitors_m": 2.8, "founded": 1929, "highlight": "Starry Night", "lat": 40.7614, "lon": -73.9776},
    {"museum": "Art Institute of Chicago", "city": "Chicago", "country": "USA", "visitors_m": 1.7, "founded": 1879, "highlight": "American Gothic", "lat": 41.8796, "lon": -87.6237},
    {"museum": "Acropolis Museum", "city": "Athens", "country": "Greece", "visitors_m": 1.8, "founded": 2009, "highlight": "Parthenon Gallery", "lat": 37.9685, "lon": 23.7283},
    {"museum": "Egyptian Museum", "city": "Cairo", "country": "Egypt", "visitors_m": 2.0, "founded": 1902, "highlight": "Tutankhamun mask", "lat": 30.0478, "lon": 31.2336},
    {"museum": "Museo Reina Sofia", "city": "Madrid", "country": "Spain", "visitors_m": 4.4, "founded": 1992, "highlight": "Guernica", "lat": 40.4087, "lon": -3.6943},
    {"museum": "Van Gogh Museum", "city": "Amsterdam", "country": "Netherlands", "visitors_m": 2.1, "founded": 1973, "highlight": "Almond Blossom", "lat": 52.3584, "lon": 4.8811},
    {"museum": "Guggenheim Bilbao", "city": "Bilbao", "country": "Spain", "visitors_m": 1.3, "founded": 1997, "highlight": "Titanium architecture", "lat": 43.2687, "lon": -2.9340},
    {"museum": "National Museum Tokyo", "city": "Tokyo", "country": "Japan", "visitors_m": 2.6, "founded": 1872, "highlight": "Samurai armor", "lat": 35.7189, "lon": 139.7765},
    {"museum": "Pergamon Museum", "city": "Berlin", "country": "Germany", "visitors_m": 2.3, "founded": 1930, "highlight": "Ishtar Gate", "lat": 52.5212, "lon": 13.3967},
    {"museum": "Museu de Arte de Sao Paulo", "city": "Sao Paulo", "country": "Brazil", "visitors_m": 0.7, "founded": 1947, "highlight": "Latin American art", "lat": -23.5614, "lon": -46.6558},
    {"museum": "Getty Center", "city": "Los Angeles", "country": "USA", "visitors_m": 1.8, "founded": 1997, "highlight": "Irises (van Gogh)", "lat": 34.0780, "lon": -118.4741},
]


@st.cache_data(ttl=3600)
def _get_top_museums():
    return pd.DataFrame(TOP_MUSEUMS)


# =====================================================================
# 7. UNESCO INTANGIBLE HERITAGE
# =====================================================================
UNESCO_INTANGIBLE = [
    {"heritage": "Flamenco", "country": "Spain", "year_inscribed": 2010, "domain": "Performing arts", "lat": 37.3891, "lon": -5.9845},
    {"heritage": "Art of Neapolitan Pizzaiuolo", "country": "Italy", "year_inscribed": 2017, "domain": "Culinary", "lat": 40.8518, "lon": 14.2681},
    {"heritage": "Tango", "country": "Argentina / Uruguay", "year_inscribed": 2009, "domain": "Performing arts", "lat": -34.6037, "lon": -58.3816},
    {"heritage": "Peking Opera", "country": "China", "year_inscribed": 2010, "domain": "Performing arts", "lat": 39.9042, "lon": 116.4074},
    {"heritage": "Yoga", "country": "India", "year_inscribed": 2016, "domain": "Social practices", "lat": 30.0869, "lon": 78.2676},
    {"heritage": "Nowruz", "country": "Iran (and others)", "year_inscribed": 2009, "domain": "Festive events", "lat": 35.6892, "lon": 51.3890},
    {"heritage": "Reggae Music", "country": "Jamaica", "year_inscribed": 2018, "domain": "Performing arts", "lat": 18.0179, "lon": -76.8099},
    {"heritage": "Washoku (Japanese cuisine)", "country": "Japan", "year_inscribed": 2013, "domain": "Culinary", "lat": 35.6762, "lon": 139.6503},
    {"heritage": "Kimchi-making", "country": "South Korea", "year_inscribed": 2013, "domain": "Culinary", "lat": 37.5665, "lon": 126.9780},
    {"heritage": "French Gastronomic Meal", "country": "France", "year_inscribed": 2010, "domain": "Culinary", "lat": 48.8566, "lon": 2.3522},
    {"heritage": "Carnival of Barranquilla", "country": "Colombia", "year_inscribed": 2003, "domain": "Festive events", "lat": 10.9685, "lon": -74.7813},
    {"heritage": "Turkish Coffee", "country": "Turkey", "year_inscribed": 2013, "domain": "Culinary", "lat": 41.0082, "lon": 28.9784},
    {"heritage": "Kabuki Theatre", "country": "Japan", "year_inscribed": 2008, "domain": "Performing arts", "lat": 35.6662, "lon": 139.7703},
    {"heritage": "Samba de Roda", "country": "Brazil", "year_inscribed": 2008, "domain": "Performing arts", "lat": -12.9714, "lon": -38.5124},
    {"heritage": "Mevlevi Sema (Whirling Dervishes)", "country": "Turkey", "year_inscribed": 2008, "domain": "Performing arts", "lat": 37.8719, "lon": 32.4930},
    {"heritage": "Falconry", "country": "UAE (and others)", "year_inscribed": 2016, "domain": "Social practices", "lat": 24.4539, "lon": 54.3773},
    {"heritage": "Beer Culture in Belgium", "country": "Belgium", "year_inscribed": 2016, "domain": "Culinary", "lat": 50.8503, "lon": 4.3517},
    {"heritage": "Mediterranean Diet", "country": "Italy / Spain / Greece", "year_inscribed": 2013, "domain": "Culinary", "lat": 40.8518, "lon": 14.2681},
    {"heritage": "Capoeira", "country": "Brazil", "year_inscribed": 2014, "domain": "Performing arts", "lat": -12.9714, "lon": -38.5124},
    {"heritage": "Gamelan", "country": "Indonesia", "year_inscribed": 2021, "domain": "Performing arts", "lat": -7.7972, "lon": 110.3688},
    {"heritage": "Mariachi", "country": "Mexico", "year_inscribed": 2011, "domain": "Performing arts", "lat": 20.6597, "lon": -103.3496},
    {"heritage": "Georgian Polyphonic Singing", "country": "Georgia", "year_inscribed": 2008, "domain": "Performing arts", "lat": 41.7151, "lon": 44.8271},
    {"heritage": "Al-Ayyala (Traditional Dance)", "country": "UAE / Oman", "year_inscribed": 2014, "domain": "Performing arts", "lat": 24.4539, "lon": 54.3773},
    {"heritage": "Haka", "country": "New Zealand", "year_inscribed": 2011, "domain": "Performing arts", "lat": -38.4165, "lon": 176.2497},
    {"heritage": "Chinese Calligraphy", "country": "China", "year_inscribed": 2009, "domain": "Traditional crafts", "lat": 34.2658, "lon": 108.9541},
]


@st.cache_data(ttl=3600)
def _get_unesco_intangible():
    return pd.DataFrame(UNESCO_INTANGIBLE)


# =====================================================================
# 8. CUISINE CAPITALS
# =====================================================================
CUISINE_CAPITALS = [
    {"city": "Tokyo", "country": "Japan", "michelin_stars": 263, "signature_dish": "Sushi / Ramen", "cuisine_style": "Japanese", "lat": 35.6762, "lon": 139.6503},
    {"city": "Paris", "country": "France", "michelin_stars": 118, "signature_dish": "Croissant / Coq au Vin", "cuisine_style": "French", "lat": 48.8566, "lon": 2.3522},
    {"city": "Bangkok", "country": "Thailand", "michelin_stars": 35, "signature_dish": "Pad Thai / Tom Yum", "cuisine_style": "Thai", "lat": 13.7563, "lon": 100.5018},
    {"city": "New York City", "country": "USA", "michelin_stars": 72, "signature_dish": "Pizza / Bagels", "cuisine_style": "Diverse", "lat": 40.7128, "lon": -74.0060},
    {"city": "Mexico City", "country": "Mexico", "michelin_stars": 20, "signature_dish": "Tacos al Pastor", "cuisine_style": "Mexican", "lat": 19.4326, "lon": -99.1332},
    {"city": "Istanbul", "country": "Turkey", "michelin_stars": 14, "signature_dish": "Kebab / Baklava", "cuisine_style": "Turkish", "lat": 41.0082, "lon": 28.9784},
    {"city": "Lima", "country": "Peru", "michelin_stars": 5, "signature_dish": "Ceviche", "cuisine_style": "Peruvian", "lat": -12.0464, "lon": -77.0428},
    {"city": "Bologna", "country": "Italy", "michelin_stars": 12, "signature_dish": "Ragu / Tortellini", "cuisine_style": "Italian", "lat": 44.4949, "lon": 11.3426},
    {"city": "Barcelona", "country": "Spain", "michelin_stars": 24, "signature_dish": "Paella / Tapas", "cuisine_style": "Spanish", "lat": 41.3874, "lon": 2.1686},
    {"city": "Singapore", "country": "Singapore", "michelin_stars": 50, "signature_dish": "Hainanese Chicken Rice", "cuisine_style": "Fusion", "lat": 1.3521, "lon": 103.8198},
    {"city": "Lyon", "country": "France", "michelin_stars": 25, "signature_dish": "Quenelles / Lyonnaise Salad", "cuisine_style": "French", "lat": 45.7640, "lon": 4.8357},
    {"city": "Hong Kong", "country": "China", "michelin_stars": 81, "signature_dish": "Dim Sum / Roast Goose", "cuisine_style": "Cantonese", "lat": 22.3193, "lon": 114.1694},
    {"city": "Copenhagen", "country": "Denmark", "michelin_stars": 23, "signature_dish": "New Nordic cuisine", "cuisine_style": "Nordic", "lat": 55.6761, "lon": 12.5683},
    {"city": "Jaipur", "country": "India", "michelin_stars": 0, "signature_dish": "Dal Baati Churma", "cuisine_style": "Rajasthani", "lat": 26.9124, "lon": 75.7873},
    {"city": "Marrakech", "country": "Morocco", "michelin_stars": 0, "signature_dish": "Tagine / Couscous", "cuisine_style": "Moroccan", "lat": 31.6295, "lon": -7.9811},
    {"city": "Seoul", "country": "South Korea", "michelin_stars": 36, "signature_dish": "Bibimbap / Korean BBQ", "cuisine_style": "Korean", "lat": 37.5665, "lon": 126.9780},
    {"city": "Naples", "country": "Italy", "michelin_stars": 8, "signature_dish": "Pizza Margherita", "cuisine_style": "Italian", "lat": 40.8518, "lon": 14.2681},
    {"city": "Chengdu", "country": "China", "michelin_stars": 10, "signature_dish": "Mapo Tofu / Hotpot", "cuisine_style": "Sichuan", "lat": 30.5728, "lon": 104.0668},
    {"city": "San Sebastian", "country": "Spain", "michelin_stars": 18, "signature_dish": "Pintxos / Bacalao", "cuisine_style": "Basque", "lat": 43.3183, "lon": -1.9812},
    {"city": "Oaxaca", "country": "Mexico", "michelin_stars": 0, "signature_dish": "Mole / Mezcal", "cuisine_style": "Oaxacan", "lat": 17.0732, "lon": -96.7266},
    {"city": "Osaka", "country": "Japan", "michelin_stars": 117, "signature_dish": "Takoyaki / Okonomiyaki", "cuisine_style": "Japanese", "lat": 34.6937, "lon": 135.5023},
    {"city": "Hanoi", "country": "Vietnam", "michelin_stars": 4, "signature_dish": "Pho / Bun Cha", "cuisine_style": "Vietnamese", "lat": 21.0278, "lon": 105.8342},
    {"city": "Buenos Aires", "country": "Argentina", "michelin_stars": 5, "signature_dish": "Asado / Empanadas", "cuisine_style": "Argentine", "lat": -34.6037, "lon": -58.3816},
    {"city": "Addis Ababa", "country": "Ethiopia", "michelin_stars": 0, "signature_dish": "Injera / Doro Wat", "cuisine_style": "Ethiopian", "lat": 9.0250, "lon": 38.7469},
    {"city": "Beirut", "country": "Lebanon", "michelin_stars": 3, "signature_dish": "Hummus / Tabbouleh", "cuisine_style": "Lebanese", "lat": 33.8938, "lon": 35.5018},
]


@st.cache_data(ttl=3600)
def _get_cuisine_capitals():
    return pd.DataFrame(CUISINE_CAPITALS)


# =====================================================================
# 9. NOBEL LAUREATE BIRTHPLACES
# =====================================================================
NOBEL_LAUREATES = [
    {"name": "Albert Einstein", "field": "Physics", "year": 1921, "birthplace": "Ulm", "country": "Germany", "lat": 48.4011, "lon": 9.9876},
    {"name": "Marie Curie", "field": "Physics / Chemistry", "year": 1903, "birthplace": "Warsaw", "country": "Poland", "lat": 52.2297, "lon": 21.0122},
    {"name": "Niels Bohr", "field": "Physics", "year": 1922, "birthplace": "Copenhagen", "country": "Denmark", "lat": 55.6761, "lon": 12.5683},
    {"name": "Ernest Hemingway", "field": "Literature", "year": 1954, "birthplace": "Oak Park, IL", "country": "USA", "lat": 41.8850, "lon": -87.7845},
    {"name": "Gabriel Garcia Marquez", "field": "Literature", "year": 1982, "birthplace": "Aracataca", "country": "Colombia", "lat": 10.5919, "lon": -74.1896},
    {"name": "Rabindranath Tagore", "field": "Literature", "year": 1913, "birthplace": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639},
    {"name": "Martin Luther King Jr.", "field": "Peace", "year": 1964, "birthplace": "Atlanta, GA", "country": "USA", "lat": 33.7490, "lon": -84.3880},
    {"name": "Nelson Mandela", "field": "Peace", "year": 1993, "birthplace": "Mvezo", "country": "South Africa", "lat": -31.9686, "lon": 28.7744},
    {"name": "Malala Yousafzai", "field": "Peace", "year": 2014, "birthplace": "Mingora", "country": "Pakistan", "lat": 34.7717, "lon": 72.3601},
    {"name": "Alexander Fleming", "field": "Medicine", "year": 1945, "birthplace": "Darvel", "country": "UK", "lat": 55.6105, "lon": -4.2748},
    {"name": "Werner Heisenberg", "field": "Physics", "year": 1932, "birthplace": "Wurzburg", "country": "Germany", "lat": 49.7913, "lon": 9.9534},
    {"name": "Max Planck", "field": "Physics", "year": 1918, "birthplace": "Kiel", "country": "Germany", "lat": 54.3233, "lon": 10.1228},
    {"name": "Richard Feynman", "field": "Physics", "year": 1965, "birthplace": "New York City", "country": "USA", "lat": 40.7282, "lon": -73.7949},
    {"name": "Toni Morrison", "field": "Literature", "year": 1993, "birthplace": "Lorain, OH", "country": "USA", "lat": 41.4529, "lon": -82.1824},
    {"name": "Pablo Neruda", "field": "Literature", "year": 1971, "birthplace": "Parral", "country": "Chile", "lat": -36.1397, "lon": -71.8244},
    {"name": "Bob Dylan", "field": "Literature", "year": 2016, "birthplace": "Duluth, MN", "country": "USA", "lat": 46.7867, "lon": -92.1005},
    {"name": "Mother Teresa", "field": "Peace", "year": 1979, "birthplace": "Skopje", "country": "North Macedonia", "lat": 41.9973, "lon": 21.4280},
    {"name": "Wangari Maathai", "field": "Peace", "year": 2004, "birthplace": "Ihithe", "country": "Kenya", "lat": -0.6683, "lon": 37.1531},
    {"name": "Ivan Pavlov", "field": "Medicine", "year": 1904, "birthplace": "Ryazan", "country": "Russia", "lat": 54.6269, "lon": 39.6916},
    {"name": "Erwin Schrodinger", "field": "Physics", "year": 1933, "birthplace": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738},
    {"name": "William Faulkner", "field": "Literature", "year": 1949, "birthplace": "New Albany, MS", "country": "USA", "lat": 34.4940, "lon": -89.0012},
    {"name": "Naguib Mahfouz", "field": "Literature", "year": 1988, "birthplace": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357},
    {"name": "Yasunari Kawabata", "field": "Literature", "year": 1968, "birthplace": "Osaka", "country": "Japan", "lat": 34.6937, "lon": 135.5023},
    {"name": "Aung San Suu Kyi", "field": "Peace", "year": 1991, "birthplace": "Rangoon (Yangon)", "country": "Myanmar", "lat": 16.8661, "lon": 96.1951},
    {"name": "Linus Pauling", "field": "Chemistry / Peace", "year": 1954, "birthplace": "Portland, OR", "country": "USA", "lat": 45.5152, "lon": -122.6784},
    {"name": "Tu Youyou", "field": "Medicine", "year": 2015, "birthplace": "Ningbo", "country": "China", "lat": 29.8683, "lon": 121.5440},
    {"name": "Orhan Pamuk", "field": "Literature", "year": 2006, "birthplace": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784},
    {"name": "Wole Soyinka", "field": "Literature", "year": 1986, "birthplace": "Abeokuta", "country": "Nigeria", "lat": 7.1558, "lon": 3.3459},
    {"name": "Octavio Paz", "field": "Literature", "year": 1990, "birthplace": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332},
    {"name": "Svetlana Alexievich", "field": "Literature", "year": 2015, "birthplace": "Stanislav", "country": "Ukraine", "lat": 48.9226, "lon": 24.7111},
    {"name": "Dorothy Hodgkin", "field": "Chemistry", "year": 1964, "birthplace": "Cairo", "country": "Egypt (British)", "lat": 30.0444, "lon": 31.2357},
    {"name": "Amartya Sen", "field": "Economics", "year": 1998, "birthplace": "Santiniketan", "country": "India", "lat": 23.6783, "lon": 87.6856},
    {"name": "Friedrich Hayek", "field": "Economics", "year": 1974, "birthplace": "Vienna", "country": "Austria", "lat": 48.2182, "lon": 16.3638},
    {"name": "Daniel Kahneman", "field": "Economics", "year": 2002, "birthplace": "Tel Aviv", "country": "Israel", "lat": 32.0853, "lon": 34.7818},
    {"name": "Muhammad Yunus", "field": "Peace", "year": 2006, "birthplace": "Chittagong", "country": "Bangladesh", "lat": 22.3569, "lon": 91.7832},
    {"name": "Abdulrazak Gurnah", "field": "Literature", "year": 2021, "birthplace": "Zanzibar", "country": "Tanzania", "lat": -6.1659, "lon": 39.2026},
    {"name": "Kazuo Ishiguro", "field": "Literature", "year": 2017, "birthplace": "Nagasaki", "country": "Japan", "lat": 32.7503, "lon": 129.8779},
    {"name": "Alice Munro", "field": "Literature", "year": 2013, "birthplace": "Wingham, ON", "country": "Canada", "lat": 43.8867, "lon": -81.3117},
    {"name": "Mikhail Gorbachev", "field": "Peace", "year": 1990, "birthplace": "Privolnoye", "country": "Russia", "lat": 45.9256, "lon": 42.7211},
    {"name": "Liu Xiaobo", "field": "Peace", "year": 2010, "birthplace": "Changchun", "country": "China", "lat": 43.8171, "lon": 125.3235},
]


@st.cache_data(ttl=3600)
def _get_nobel_laureates():
    return pd.DataFrame(NOBEL_LAUREATES)


# =====================================================================
# 10. FAMOUS AUTHORS
# =====================================================================
FAMOUS_AUTHORS = [
    {"author": "William Shakespeare", "birthplace": "Stratford-upon-Avon", "country": "UK", "era": "1564-1616", "genre": "Drama / Poetry", "notable_work": "Hamlet", "lat": 52.1917, "lon": -1.7083},
    {"author": "Franz Kafka", "birthplace": "Prague", "country": "Czech Republic", "era": "1883-1924", "genre": "Modernism", "notable_work": "The Metamorphosis", "lat": 50.0755, "lon": 14.4378},
    {"author": "Leo Tolstoy", "birthplace": "Yasnaya Polyana", "country": "Russia", "era": "1828-1910", "genre": "Realism", "notable_work": "War and Peace", "lat": 54.0755, "lon": 37.5285},
    {"author": "Jane Austen", "birthplace": "Steventon", "country": "UK", "era": "1775-1817", "genre": "Romance / Satire", "notable_work": "Pride and Prejudice", "lat": 51.2443, "lon": -1.2130},
    {"author": "Fyodor Dostoevsky", "birthplace": "Moscow", "country": "Russia", "era": "1821-1881", "genre": "Psychological fiction", "notable_work": "Crime and Punishment", "lat": 55.7558, "lon": 37.6173},
    {"author": "Mark Twain", "birthplace": "Florida, MO", "country": "USA", "era": "1835-1910", "genre": "Satire / Adventure", "notable_work": "Adventures of Huckleberry Finn", "lat": 39.4975, "lon": -91.7990},
    {"author": "Victor Hugo", "birthplace": "Besancon", "country": "France", "era": "1802-1885", "genre": "Romanticism", "notable_work": "Les Miserables", "lat": 47.2378, "lon": 6.0241},
    {"author": "Charles Dickens", "birthplace": "Portsmouth", "country": "UK", "era": "1812-1870", "genre": "Social realism", "notable_work": "A Tale of Two Cities", "lat": 50.8198, "lon": -1.0880},
    {"author": "Jorge Luis Borges", "birthplace": "Buenos Aires", "country": "Argentina", "era": "1899-1986", "genre": "Magical realism", "notable_work": "Ficciones", "lat": -34.6037, "lon": -58.3816},
    {"author": "Haruki Murakami", "birthplace": "Kyoto", "country": "Japan", "era": "1949-", "genre": "Surrealism / Fiction", "notable_work": "Norwegian Wood", "lat": 35.0116, "lon": 135.7681},
    {"author": "Gabriel Garcia Marquez", "birthplace": "Aracataca", "country": "Colombia", "era": "1927-2014", "genre": "Magical realism", "notable_work": "One Hundred Years of Solitude", "lat": 10.5919, "lon": -74.1896},
    {"author": "Chinua Achebe", "birthplace": "Ogidi", "country": "Nigeria", "era": "1930-2013", "genre": "Post-colonial", "notable_work": "Things Fall Apart", "lat": 6.1687, "lon": 6.8347},
    {"author": "Miguel de Cervantes", "birthplace": "Alcala de Henares", "country": "Spain", "era": "1547-1616", "genre": "Novel", "notable_work": "Don Quixote", "lat": 40.4818, "lon": -3.3635},
    {"author": "Dante Alighieri", "birthplace": "Florence", "country": "Italy", "era": "1265-1321", "genre": "Epic poetry", "notable_work": "The Divine Comedy", "lat": 43.7696, "lon": 11.2558},
    {"author": "Homer", "birthplace": "Ionia (Smyrna)", "country": "Ancient Greece", "era": "~8th c. BC", "genre": "Epic poetry", "notable_work": "The Odyssey", "lat": 38.4189, "lon": 27.1287},
    {"author": "Marcel Proust", "birthplace": "Auteuil, Paris", "country": "France", "era": "1871-1922", "genre": "Modernism", "notable_work": "In Search of Lost Time", "lat": 48.8476, "lon": 2.2614},
    {"author": "Virginia Woolf", "birthplace": "London", "country": "UK", "era": "1882-1941", "genre": "Modernism", "notable_work": "Mrs Dalloway", "lat": 51.4954, "lon": -0.1760},
    {"author": "James Joyce", "birthplace": "Dublin", "country": "Ireland", "era": "1882-1941", "genre": "Modernism", "notable_work": "Ulysses", "lat": 53.3498, "lon": -6.2603},
    {"author": "Murasaki Shikibu", "birthplace": "Kyoto", "country": "Japan", "era": "~978-1014", "genre": "Novel", "notable_work": "The Tale of Genji", "lat": 35.0016, "lon": 135.7581},
    {"author": "Paulo Coelho", "birthplace": "Rio de Janeiro", "country": "Brazil", "era": "1947-", "genre": "Fiction / Fable", "notable_work": "The Alchemist", "lat": -22.9068, "lon": -43.1729},
    {"author": "Agatha Christie", "birthplace": "Torquay", "country": "UK", "era": "1890-1976", "genre": "Mystery", "notable_work": "Murder on the Orient Express", "lat": 50.4619, "lon": -3.5253},
    {"author": "Rumi", "birthplace": "Balkh", "country": "Afghanistan", "era": "1207-1273", "genre": "Sufi poetry", "notable_work": "Masnavi", "lat": 36.7581, "lon": 66.8981},
    {"author": "Hans Christian Andersen", "birthplace": "Odense", "country": "Denmark", "era": "1805-1875", "genre": "Fairy tales", "notable_work": "The Little Mermaid", "lat": 55.3959, "lon": 10.3883},
    {"author": "Oscar Wilde", "birthplace": "Dublin", "country": "Ireland", "era": "1854-1900", "genre": "Drama / Wit", "notable_work": "The Picture of Dorian Gray", "lat": 53.3398, "lon": -6.2703},
    {"author": "Isabel Allende", "birthplace": "Lima", "country": "Peru (Chilean)", "era": "1942-", "genre": "Magical realism", "notable_work": "The House of the Spirits", "lat": -12.0464, "lon": -77.0428},
    {"author": "Anton Chekhov", "birthplace": "Taganrog", "country": "Russia", "era": "1860-1904", "genre": "Drama / Short stories", "notable_work": "The Cherry Orchard", "lat": 47.2362, "lon": 38.8969},
]


@st.cache_data(ttl=3600)
def _get_famous_authors():
    return pd.DataFrame(FAMOUS_AUTHORS)


# =====================================================================
# MAP RENDERING FUNCTIONS
# =====================================================================

def _render_music_genres():
    """Map 1: Music Genre Origins."""
    df = _get_music_genres()
    st.markdown("#### Music Genre Origins Worldwide")
    c1, c2, c3 = st.columns(3)
    c1.metric("Genres", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Decades Span", f"{df['decade'].iloc[0]} - {df['decade'].iloc[-1]}")

    # Chart: genres per country
    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    bars = ax.barh(country_counts.index[::-1], country_counts.values[::-1],
                   color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Genres")
    ax.set_title("Music Genre Origins by Country")
    st.image(_fig_to_bytes(fig), width=800)

    # Map
    m = _base_map()
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['genre'])}</b><br>"
            f"Origin: {escape(row['origin_city'])}, {escape(row['country'])}<br>"
            f"Decade: {escape(row['decade'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=escape(row["genre"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["genre", "origin_city", "country", "decade"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "music_genres.csv", "text/csv")


def _render_concert_venues():
    """Map 2: Famous Concert Venues."""
    df = _get_concert_venues()
    st.markdown("#### Famous Concert Venues")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Venues", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Largest Capacity", f"{df['capacity'].max():,}")
    c4.metric("Oldest", int(df[df["opened"] > 0]["opened"].min()))

    # Chart: top 10 by capacity
    top10 = df.nlargest(10, "capacity")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["venue"].values[::-1], top10["capacity"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Capacity")
    ax.set_title("Top 10 Concert Venues by Capacity")
    st.image(_fig_to_bytes(fig), width=800)

    # Map
    m = _base_map()
    mc = MarkerCluster(name="Venues").add_to(m)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['venue'])}</b><br>"
            f"{escape(row['city'])}, {escape(row['country'])}<br>"
            f"Capacity: {row['capacity']:,}<br>"
            f"Opened: {row['opened']}"
        )
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(row["venue"]),
            icon=folium.Icon(color="red", icon="music", prefix="fa"),
        ).add_to(mc)
    _show_map(m)

    st.dataframe(df[["venue", "city", "country", "capacity", "opened"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "concert_venues.csv", "text/csv")


def _render_film_locations():
    """Map 3: Iconic Film Locations."""
    df = _get_film_locations()
    st.markdown("#### Iconic Film Locations")
    c1, c2, c3 = st.columns(3)
    c1.metric("Film Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Year Range", f"{df['year'].min()} - {df['year'].max()}")

    # Chart: films per decade
    df_temp = df.copy()
    df_temp["decade"] = (df_temp["year"] // 10) * 10
    decade_counts = df_temp["decade"].value_counts().sort_index()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.bar([str(d) + "s" for d in decade_counts.index], decade_counts.values,
           color=[_color_for(i) for i in range(len(decade_counts))])
    ax.set_xlabel("Decade")
    ax.set_ylabel("Films")
    ax.set_title("Film Locations by Decade")
    plt.xticks(rotation=45)
    st.image(_fig_to_bytes(fig), width=800)

    # Map
    m = _base_map()
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['film'])}</b><br>"
            f"Location: {escape(row['location'])}<br>"
            f"Country: {escape(row['country'])}<br>"
            f"Year: {row['year']}"
        )
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(row["film"]),
            icon=folium.Icon(color="cadetblue", icon="film", prefix="fa"),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["film", "location", "country", "year"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "film_locations.csv", "text/csv")


def _render_art_movements():
    """Map 4: Art Movements."""
    df = _get_art_movements()
    st.markdown("#### Art Movements Around the World")
    c1, c2 = st.columns(2)
    c1.metric("Movements", len(df))
    c2.metric("Cities", df["city"].nunique())

    # Map
    m = _base_map(center=[45, 10], zoom=3)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['movement'])}</b><br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Period: {escape(row['period'])}<br>"
            f"Key artists: {escape(row['artists'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=12,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["movement"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["movement", "city", "country", "period", "artists"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "art_movements.csv", "text/csv")


def _render_world_festivals():
    """Map 5: World Festivals."""
    df = _get_world_festivals()
    st.markdown("#### Major World Festivals")
    c1, c2, c3 = st.columns(3)
    c1.metric("Festivals", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())

    # Chart: festivals by type
    type_counts = df["type"].value_counts()
    fig, ax = _dark_fig(figsize=(7, 4))
    wedges, texts, autotexts = ax.pie(
        type_counts.values,
        labels=type_counts.index,
        autopct="%1.0f%%",
        colors=[_color_for(i) for i in range(len(type_counts))],
        textprops={"color": TEXT_PRIMARY, "fontsize": 10},
    )
    for t in autotexts:
        t.set_color(TEXT_PRIMARY)
    ax.set_title("Festivals by Type", color=TEXT_PRIMARY)
    st.image(_fig_to_bytes(fig), width=600)

    type_colors = {
        "Cultural": "orange", "Religious": "purple", "Art": "blue",
        "Music": "red", "Film": "green",
    }

    # Map
    m = _base_map()
    mc = MarkerCluster(name="Festivals").add_to(m)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['festival'])}</b><br>"
            f"{escape(row['city'])}, {escape(row['country'])}<br>"
            f"Month: {escape(row['month'])}<br>"
            f"Type: {escape(row['type'])}"
        )
        icon_color = type_colors.get(row["type"], "gray")
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(row["festival"]),
            icon=folium.Icon(color=icon_color, icon="star", prefix="fa"),
        ).add_to(mc)
    _show_map(m)

    st.dataframe(df[["festival", "city", "country", "month", "type"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "world_festivals.csv", "text/csv")


def _render_top_museums():
    """Map 6: Top Museums."""
    df = _get_top_museums()
    st.markdown("#### Most-Visited Museums Worldwide")
    c1, c2, c3 = st.columns(3)
    c1.metric("Museums", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Visitors", f"{df['visitors_m'].sum():.1f}M")

    # Chart: top 10 by visitors
    top10 = df.nlargest(10, "visitors_m")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["museum"].values[::-1], top10["visitors_m"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Annual Visitors (millions)")
    ax.set_title("Top 10 Museums by Visitors")
    st.image(_fig_to_bytes(fig), width=800)

    # Map
    m = _base_map(center=[35, 10], zoom=3)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['museum'])}</b><br>"
            f"{escape(row['city'])}, {escape(row['country'])}<br>"
            f"Visitors: {row['visitors_m']}M/year<br>"
            f"Founded: {row['founded']}<br>"
            f"Highlight: {escape(row['highlight'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(5, row["visitors_m"] * 1.5),
            color=ACCENT_AMBER,
            fill=True,
            fill_color=ACCENT_AMBER,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["museum"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["museum", "city", "country", "visitors_m", "founded", "highlight"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "top_museums.csv", "text/csv")


def _render_unesco_intangible():
    """Map 7: UNESCO Intangible Heritage."""
    df = _get_unesco_intangible()
    st.markdown("#### UNESCO Intangible Cultural Heritage")
    c1, c2, c3 = st.columns(3)
    c1.metric("Heritage Items", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Domains", df["domain"].nunique())

    # Chart: by domain
    domain_counts = df["domain"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(domain_counts.index[::-1], domain_counts.values[::-1],
            color=[_color_for(i) for i in range(len(domain_counts))])
    ax.set_xlabel("Count")
    ax.set_title("UNESCO Intangible Heritage by Domain")
    st.image(_fig_to_bytes(fig), width=800)

    domain_colors = {
        "Performing arts": "#ec4899",
        "Culinary": "#f59e0b",
        "Social practices": "#10b981",
        "Festive events": "#8b5cf6",
        "Traditional crafts": "#06b6d4",
    }

    # Map
    m = _base_map()
    for _, row in df.iterrows():
        color = domain_colors.get(row["domain"], "#3b82f6")
        popup_html = (
            f"<b>{escape(row['heritage'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Domain: {escape(row['domain'])}<br>"
            f"Inscribed: {row['year_inscribed']}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(row["heritage"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["heritage", "country", "domain", "year_inscribed"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "unesco_intangible.csv", "text/csv")


def _render_cuisine_capitals():
    """Map 8: Cuisine Capitals."""
    df = _get_cuisine_capitals()
    st.markdown("#### World Cuisine Capitals")
    c1, c2, c3 = st.columns(3)
    c1.metric("Food Cities", len(df))
    c2.metric("Total Michelin Stars", int(df["michelin_stars"].sum()))
    c3.metric("Cuisine Styles", df["cuisine_style"].nunique())

    # Chart: top 10 by Michelin stars
    top10 = df.nlargest(10, "michelin_stars")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["city"].values[::-1], top10["michelin_stars"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Michelin Stars")
    ax.set_title("Top 10 Cities by Michelin Stars")
    st.image(_fig_to_bytes(fig), width=800)

    # Map
    m = _base_map()
    for _, row in df.iterrows():
        stars = row["michelin_stars"]
        radius = max(6, min(18, stars / 15))
        popup_html = (
            f"<b>{escape(row['city'])}</b>, {escape(row['country'])}<br>"
            f"Cuisine: {escape(row['cuisine_style'])}<br>"
            f"Michelin Stars: {stars}<br>"
            f"Signature: {escape(row['signature_dish'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=ACCENT_AMBER,
            fill=True,
            fill_color=ACCENT_AMBER,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{escape(row['city'])} ({stars} stars)",
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["city", "country", "michelin_stars", "signature_dish", "cuisine_style"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "cuisine_capitals.csv", "text/csv")


def _render_nobel_laureates():
    """Map 9: Nobel Laureate Birthplaces."""
    df = _get_nobel_laureates()
    st.markdown("#### Nobel Laureate Birthplaces")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Laureates", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Fields", df["field"].nunique())
    c4.metric("Year Range", f"{df['year'].min()} - {df['year'].max()}")

    # Chart: laureates by field
    field_counts = df["field"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(field_counts.index[::-1], field_counts.values[::-1],
            color=[_color_for(i) for i in range(len(field_counts))])
    ax.set_xlabel("Count")
    ax.set_title("Nobel Laureates by Field")
    st.image(_fig_to_bytes(fig), width=800)

    field_colors = {
        "Physics": "#3b82f6",
        "Physics / Chemistry": "#06b6d4",
        "Chemistry": "#10b981",
        "Chemistry / Peace": "#14b8a6",
        "Literature": "#f59e0b",
        "Peace": "#ec4899",
        "Medicine": "#ef4444",
        "Economics": "#8b5cf6",
    }

    # Map
    m = _base_map()
    mc = MarkerCluster(name="Nobel Laureates").add_to(m)
    for _, row in df.iterrows():
        color = field_colors.get(row["field"], "gray")
        popup_html = (
            f"<b>{escape(row['name'])}</b><br>"
            f"Field: {escape(row['field'])}<br>"
            f"Year: {row['year']}<br>"
            f"Birthplace: {escape(row['birthplace'])}, {escape(row['country'])}"
        )
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(row["name"]),
            icon=folium.Icon(color=color if color in [
                "red", "blue", "green", "purple", "orange", "gray",
                "cadetblue", "darkred", "darkblue", "darkgreen",
            ] else "blue", icon="trophy", prefix="fa"),
        ).add_to(mc)
    _show_map(m)

    st.dataframe(
        df[["name", "field", "year", "birthplace", "country"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "nobel_laureates.csv", "text/csv")


def _render_famous_authors():
    """Map 10: Famous Authors."""
    df = _get_famous_authors()
    st.markdown("#### Famous Authors and Their Birthplaces")
    c1, c2, c3 = st.columns(3)
    c1.metric("Authors", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Genres", df["genre"].nunique())

    # Chart: authors by country
    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Authors")
    ax.set_title("Famous Authors by Country of Birth")
    st.image(_fig_to_bytes(fig), width=800)

    # Map
    m = _base_map(center=[30, 10], zoom=3)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['author'])}</b><br>"
            f"Birthplace: {escape(row['birthplace'])}, {escape(row['country'])}<br>"
            f"Era: {escape(row['era'])}<br>"
            f"Genre: {escape(row['genre'])}<br>"
            f"Notable work: {escape(row['notable_work'])}"
        )
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["author"]),
            icon=folium.Icon(color="purple", icon="book", prefix="fa"),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["author", "birthplace", "country", "era", "genre", "notable_work"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "famous_authors.csv", "text/csv")


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
MAP_OPTIONS = {
    "Music Genre Origins": _render_music_genres,
    "Famous Concert Venues": _render_concert_venues,
    "Film Locations": _render_film_locations,
    "Art Movements": _render_art_movements,
    "World Festivals": _render_world_festivals,
    "Top Museums": _render_top_museums,
    "UNESCO Intangible Heritage": _render_unesco_intangible,
    "Cuisine Capitals": _render_cuisine_capitals,
    "Nobel Laureate Birthplaces": _render_nobel_laureates,
    "Famous Authors": _render_famous_authors,
}


def render_music_culture_maps_tab():
    """Main entry point for the Music & Culture Maps tab."""
    st.markdown(
        '<div class="tab-header pink">'
        "<h4>Music &amp; Culture</h4>"
        "<p>Explore the geography of music, art, film, cuisine, literature, "
        "and cultural heritage around the world.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    selected_map = st.selectbox(
        "Select map type",
        list(MAP_OPTIONS.keys()),
        key="music_culture_map_select",
    )

    if st.button("Generate Map", key="music_culture_generate", type="primary"):
        with st.spinner("Building map..."):
            MAP_OPTIONS[selected_map]()
    else:
        st.info("Select a map type above and click **Generate Map** to explore.")
