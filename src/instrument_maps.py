# -*- coding: utf-8 -*-
"""
Musical Instruments Maps module for TerraScout AI.
Provides 10 interactive map types covering piano/keyboard heritage, guitar making,
violin/string instruments, drums/percussion, wind instruments, traditional world
instruments, organs/church music, brass instruments, electronic music instruments,
and music instrument museums.
All data is hardcoded/curated for offline reliability.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module

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
        height=500,
    )
    return m


def _show_map(m):
    st_html(m._repr_html_(), height=500)


def _df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _esc(val) -> str:
    """Safely escape any value for HTML popup content."""
    return html_module.escape(str(val))


# =====================================================================
# 1. PIANO & KEYBOARD HERITAGE
# =====================================================================
PIANO_HERITAGE = [
    {"maker": "Steinway & Sons", "city": "New York City", "country": "USA", "founded": 1853, "type": "Grand Piano", "note": "World-renowned concert grand pianos", "lat": 40.7728, "lon": -73.9290, "color": "#f59e0b"},
    {"maker": "Steinway & Sons Hamburg", "city": "Hamburg", "country": "Germany", "founded": 1880, "type": "Grand Piano", "note": "European Steinway factory", "lat": 53.5511, "lon": 9.9937, "color": "#f59e0b"},
    {"maker": "Bosendorfer", "city": "Vienna", "country": "Austria", "founded": 1828, "type": "Grand Piano", "note": "Imperial grand pianos, 97-key model", "lat": 48.2082, "lon": 16.3738, "color": "#8b5cf6"},
    {"maker": "Yamaha", "city": "Hamamatsu", "country": "Japan", "founded": 1887, "type": "Grand/Upright", "note": "Largest piano manufacturer globally", "lat": 34.7108, "lon": 137.7261, "color": "#06b6d4"},
    {"maker": "Fazioli", "city": "Sacile", "country": "Italy", "founded": 1981, "type": "Grand Piano", "note": "Handcrafted Italian concert grands", "lat": 45.9547, "lon": 12.5014, "color": "#10b981"},
    {"maker": "C. Bechstein", "city": "Berlin", "country": "Germany", "founded": 1853, "type": "Grand Piano", "note": "Preferred by Liszt, Debussy", "lat": 52.5200, "lon": 13.4050, "color": "#ec4899"},
    {"maker": "Bluthner", "city": "Leipzig", "country": "Germany", "founded": 1853, "type": "Grand Piano", "note": "Aliquot stringing system", "lat": 51.3397, "lon": 12.3731, "color": "#ef4444"},
    {"maker": "Kawai", "city": "Hamamatsu", "country": "Japan", "founded": 1927, "type": "Grand/Digital", "note": "ABS-Carbon action technology", "lat": 34.7200, "lon": 137.7350, "color": "#3b82f6"},
    {"maker": "Grotrian-Steinweg", "city": "Braunschweig", "country": "Germany", "founded": 1835, "type": "Grand/Upright", "note": "Original Steinweg family line", "lat": 52.2689, "lon": 10.5268, "color": "#14b8a6"},
    {"maker": "Sauter", "city": "Spaichingen", "country": "Germany", "founded": 1819, "type": "Grand/Upright", "note": "Oldest family-owned piano maker", "lat": 48.0752, "lon": 8.7372, "color": "#a855f7"},
    {"maker": "Schimmel", "city": "Braunschweig", "country": "Germany", "founded": 1885, "type": "Grand/Upright", "note": "German precision craftsmanship", "lat": 52.2750, "lon": 10.5200, "color": "#e11d48"},
    {"maker": "Mason & Hamlin", "city": "Boston", "country": "USA", "founded": 1854, "type": "Grand Piano", "note": "Tension resonator design", "lat": 42.3601, "lon": -71.0589, "color": "#84cc16"},
    {"maker": "Estonia Piano", "city": "Tallinn", "country": "Estonia", "founded": 1893, "type": "Grand Piano", "note": "Baltic spruce soundboards", "lat": 59.4370, "lon": 24.7536, "color": "#facc15"},
    {"maker": "Petrof", "city": "Hradec Kralove", "country": "Czech Republic", "founded": 1864, "type": "Grand/Upright", "note": "Largest European piano maker", "lat": 50.2104, "lon": 15.8252, "color": "#22d3ee"},
    {"maker": "Stuart & Sons", "city": "Tumut", "country": "Australia", "founded": 1990, "type": "Grand Piano", "note": "102-key extended range grand", "lat": -35.3058, "lon": 148.2279, "color": "#c084fc"},
    {"maker": "Baldwin Piano", "city": "Cincinnati", "country": "USA", "founded": 1862, "type": "Grand Piano", "note": "Historic American piano maker", "lat": 39.1031, "lon": -84.5120, "color": "#f97316"},
    {"maker": "Chickering & Sons", "city": "Boston", "country": "USA", "founded": 1823, "type": "Grand Piano", "note": "Pioneer of iron frame grands", "lat": 42.3550, "lon": -71.0650, "color": "#d97706"},
    {"maker": "Pleyel", "city": "Paris", "country": "France", "founded": 1807, "type": "Grand Piano", "note": "Chopin's favorite piano maker", "lat": 48.8566, "lon": 2.3522, "color": "#dc2626"},
    {"maker": "Erard", "city": "Paris", "country": "France", "founded": 1780, "type": "Grand Piano", "note": "Invented double escapement action", "lat": 48.8700, "lon": 2.3400, "color": "#fb923c"},
    {"maker": "Pearl River", "city": "Guangzhou", "country": "China", "founded": 1956, "type": "Grand/Upright", "note": "World's largest piano producer by volume", "lat": 23.1291, "lon": 113.2644, "color": "#0ea5e9"},
    {"maker": "Young Chang", "city": "Incheon", "country": "South Korea", "founded": 1956, "type": "Grand/Upright", "note": "Major Asian piano manufacturer", "lat": 37.4563, "lon": 126.7052, "color": "#78716c"},
]


@st.cache_data(ttl=3600)
def _get_piano_data():
    return pd.DataFrame(PIANO_HERITAGE)


# =====================================================================
# 2. GUITAR MAKING TRADITIONS
# =====================================================================
GUITAR_TRADITIONS = [
    {"maker": "C.F. Martin & Co.", "city": "Nazareth, PA", "country": "USA", "founded": 1833, "type": "Acoustic", "note": "Dreadnought acoustic guitar pioneers", "lat": 40.7401, "lon": -75.3107, "color": "#f59e0b"},
    {"maker": "Fender", "city": "Corona, CA", "country": "USA", "founded": 1946, "type": "Electric", "note": "Telecaster, Stratocaster icons", "lat": 33.8753, "lon": -117.5664, "color": "#ef4444"},
    {"maker": "Gibson", "city": "Nashville, TN", "country": "USA", "founded": 1902, "type": "Electric/Acoustic", "note": "Les Paul, SG, ES-335", "lat": 36.1627, "lon": -86.7816, "color": "#ec4899"},
    {"maker": "Antonio de Torres", "city": "Almeria", "country": "Spain", "founded": 1850, "type": "Classical", "note": "Father of modern classical guitar", "lat": 36.8340, "lon": -2.4637, "color": "#8b5cf6"},
    {"maker": "Ramirez Guitars", "city": "Madrid", "country": "Spain", "founded": 1882, "type": "Classical/Flamenco", "note": "Five generations of luthiers", "lat": 40.4168, "lon": -3.7038, "color": "#a855f7"},
    {"maker": "Cordoba Flamenco Tradition", "city": "Cordoba", "country": "Spain", "founded": 1500, "type": "Flamenco", "note": "Birthplace of flamenco guitar", "lat": 37.8882, "lon": -4.7794, "color": "#e11d48"},
    {"maker": "Taylor Guitars", "city": "El Cajon, CA", "country": "USA", "founded": 1974, "type": "Acoustic", "note": "Innovative bolt-on neck design", "lat": 32.7948, "lon": -116.9625, "color": "#06b6d4"},
    {"maker": "PRS Guitars", "city": "Stevensville, MD", "country": "USA", "founded": 1985, "type": "Electric", "note": "Paul Reed Smith custom electrics", "lat": 38.9810, "lon": -76.3210, "color": "#10b981"},
    {"maker": "Rickenbacker", "city": "Santa Ana, CA", "country": "USA", "founded": 1931, "type": "Electric", "note": "First commercially successful electric guitar", "lat": 33.7455, "lon": -117.8677, "color": "#3b82f6"},
    {"maker": "Gretsch", "city": "Savannah, GA", "country": "USA", "founded": 1883, "type": "Electric/Acoustic", "note": "Hollow-body electric heritage", "lat": 32.0809, "lon": -81.0912, "color": "#f97316"},
    {"maker": "Ibanez (Hoshino Gakki)", "city": "Nagoya", "country": "Japan", "founded": 1957, "type": "Electric", "note": "Shred and jazz fusion guitars", "lat": 35.1815, "lon": 136.9066, "color": "#14b8a6"},
    {"maker": "Yamaha Guitars", "city": "Hamamatsu", "country": "Japan", "founded": 1966, "type": "Acoustic/Classical", "note": "Reliable student to pro range", "lat": 34.7108, "lon": 137.7261, "color": "#22d3ee"},
    {"maker": "Conde Hermanos", "city": "Madrid", "country": "Spain", "founded": 1915, "type": "Flamenco", "note": "Legendary flamenco guitar makers", "lat": 40.4250, "lon": -3.7100, "color": "#dc2626"},
    {"maker": "Lowden Guitars", "city": "Downpatrick", "country": "N. Ireland", "founded": 1974, "type": "Acoustic", "note": "Handcrafted Irish acoustics", "lat": 54.3288, "lon": -5.7150, "color": "#84cc16"},
    {"maker": "Takamine", "city": "Sakashita", "country": "Japan", "founded": 1962, "type": "Acoustic/Electric", "note": "Pioneered acoustic-electric guitars", "lat": 35.4917, "lon": 137.2833, "color": "#facc15"},
    {"maker": "Alhambra Guitars", "city": "Muro de Alcoy", "country": "Spain", "founded": 1965, "type": "Classical", "note": "Spanish classical guitar tradition", "lat": 38.7806, "lon": -0.4303, "color": "#c084fc"},
    {"maker": "Collings Guitars", "city": "Austin, TX", "country": "USA", "founded": 1973, "type": "Acoustic/Electric", "note": "Boutique American craftsmanship", "lat": 30.2672, "lon": -97.7431, "color": "#0ea5e9"},
    {"maker": "Guild Guitars", "city": "Westerly, RI", "country": "USA", "founded": 1952, "type": "Acoustic/Electric", "note": "12-string and jazz guitar legacy", "lat": 41.3776, "lon": -71.8270, "color": "#78716c"},
    {"maker": "Kremona", "city": "Kazanlak", "country": "Bulgaria", "founded": 1924, "type": "Classical", "note": "Eastern European luthier tradition", "lat": 42.6199, "lon": 25.3993, "color": "#d946ef"},
    {"maker": "Hauser Guitars", "city": "Munich", "country": "Germany", "founded": 1882, "type": "Classical", "note": "Segovia's preferred guitar maker", "lat": 48.1351, "lon": 11.5820, "color": "#fb923c"},
    {"maker": "Maton Guitars", "city": "Melbourne", "country": "Australia", "founded": 1946, "type": "Acoustic", "note": "Australia's premier guitar brand", "lat": -37.8136, "lon": 144.9631, "color": "#d97706"},
]


@st.cache_data(ttl=3600)
def _get_guitar_data():
    return pd.DataFrame(GUITAR_TRADITIONS)


# =====================================================================
# 3. VIOLIN & STRING INSTRUMENTS
# =====================================================================
VIOLIN_STRINGS = [
    {"maker": "Antonio Stradivari", "city": "Cremona", "country": "Italy", "period": "1644-1737", "type": "Violin/Cello/Viola", "note": "Greatest luthier in history, ~650 instruments survive", "lat": 45.1333, "lon": 10.0244, "color": "#f59e0b"},
    {"maker": "Giuseppe Guarneri del Gesu", "city": "Cremona", "country": "Italy", "period": "1698-1744", "type": "Violin", "note": "Paganini's preferred violins", "lat": 45.1380, "lon": 10.0200, "color": "#ec4899"},
    {"maker": "Andrea Amati", "city": "Cremona", "country": "Italy", "period": "1505-1577", "type": "Violin", "note": "Founder of Cremonese violin making", "lat": 45.1310, "lon": 10.0280, "color": "#8b5cf6"},
    {"maker": "Nicolo Amati", "city": "Cremona", "country": "Italy", "period": "1596-1684", "type": "Violin", "note": "Teacher of Stradivari and Guarneri", "lat": 45.1350, "lon": 10.0260, "color": "#a855f7"},
    {"maker": "Jacob Stainer", "city": "Absam", "country": "Austria", "period": "1617-1683", "type": "Violin", "note": "Most valued maker pre-Stradivari", "lat": 47.2974, "lon": 11.5009, "color": "#06b6d4"},
    {"maker": "Mittenwald School", "city": "Mittenwald", "country": "Germany", "period": "1684-present", "type": "Violin/String", "note": "Matthias Klotz founded major school", "lat": 47.4425, "lon": 11.2639, "color": "#10b981"},
    {"maker": "Mirecourt Luthiers", "city": "Mirecourt", "country": "France", "period": "1600-present", "type": "Violin/Bow", "note": "French violin and bow making capital", "lat": 48.3011, "lon": 6.1308, "color": "#ef4444"},
    {"maker": "Jean-Baptiste Vuillaume", "city": "Paris", "country": "France", "period": "1798-1875", "type": "Violin", "note": "Greatest French luthier, master copyist", "lat": 48.8566, "lon": 2.3522, "color": "#3b82f6"},
    {"maker": "Markneukirchen Tradition", "city": "Markneukirchen", "country": "Germany", "period": "1677-present", "type": "All Strings", "note": "UNESCO-recognized instrument town", "lat": 50.3128, "lon": 12.3264, "color": "#14b8a6"},
    {"maker": "Giovanni Paolo Maggini", "city": "Brescia", "country": "Italy", "period": "1580-1632", "type": "Violin", "note": "Brescian school master builder", "lat": 45.5416, "lon": 10.2118, "color": "#f97316"},
    {"maker": "Carlo Bergonzi", "city": "Cremona", "country": "Italy", "period": "1683-1747", "type": "Violin", "note": "Last great Cremonese master", "lat": 45.1360, "lon": 10.0230, "color": "#84cc16"},
    {"maker": "Suzuki Method Origin", "city": "Matsumoto", "country": "Japan", "period": "1933-present", "type": "Violin Pedagogy", "note": "Shinichi Suzuki's talent education", "lat": 36.2381, "lon": 137.9720, "color": "#facc15"},
    {"maker": "W.E. Hill & Sons", "city": "London", "country": "UK", "period": "1880-1992", "type": "Violin/Bow", "note": "Premier British restorers and bow makers", "lat": 51.5074, "lon": -0.1278, "color": "#22d3ee"},
    {"maker": "D'Addario Strings", "city": "Farmingdale, NY", "country": "USA", "period": "1680-present", "type": "Strings", "note": "World's largest string manufacturer", "lat": 40.7326, "lon": -73.4454, "color": "#c084fc"},
    {"maker": "Pirastro Strings", "city": "Offenbach", "country": "Germany", "period": "1798-present", "type": "Strings", "note": "Premium gut and synthetic strings", "lat": 50.1054, "lon": 8.7684, "color": "#e11d48"},
    {"maker": "Luby Violin Workshop", "city": "Luby (Schonbach)", "country": "Czech Republic", "period": "1600-present", "type": "Violin", "note": "Bohemian instrument making center", "lat": 50.2450, "lon": 12.3920, "color": "#0ea5e9"},
    {"maker": "Erhu Tradition", "city": "Wuxi", "country": "China", "period": "Ancient-present", "type": "Erhu (Chinese fiddle)", "note": "Center of Chinese erhu making", "lat": 31.4912, "lon": 120.3119, "color": "#dc2626"},
    {"maker": "Sarangi Makers", "city": "Varanasi", "country": "India", "period": "Ancient-present", "type": "Sarangi", "note": "100-stringed Hindustani bowed instrument", "lat": 25.3176, "lon": 82.9739, "color": "#d946ef"},
    {"maker": "Hardanger Fiddle", "city": "Hardanger", "country": "Norway", "period": "1651-present", "type": "Hardingfele", "note": "Sympathetic string Norwegian fiddle", "lat": 60.4733, "lon": 6.5567, "color": "#fb923c"},
    {"maker": "Morin Khuur", "city": "Ulaanbaatar", "country": "Mongolia", "period": "Ancient-present", "type": "Horsehead Fiddle", "note": "Mongolian national instrument", "lat": 47.8864, "lon": 106.9057, "color": "#78716c"},
]


@st.cache_data(ttl=3600)
def _get_violin_data():
    return pd.DataFrame(VIOLIN_STRINGS)


# =====================================================================
# 4. DRUMS & PERCUSSION ORIGINS
# =====================================================================
DRUMS_PERCUSSION = [
    {"instrument": "Djembe", "origin": "Bamako region", "country": "Mali", "period": "12th century", "type": "Hand Drum", "note": "Rope-tuned goblet drum of the Mande people", "lat": 12.6392, "lon": -8.0029, "color": "#f59e0b"},
    {"instrument": "Talking Drum (Dondo)", "origin": "Oyo Empire region", "country": "Nigeria", "period": "Ancient", "type": "Tension Drum", "note": "Pitch-bending drum mimicking tonal languages", "lat": 7.8500, "lon": 3.9333, "color": "#ec4899"},
    {"instrument": "Tabla", "origin": "Delhi / Lucknow", "country": "India", "period": "18th century", "type": "Paired Hand Drums", "note": "Foundation of Hindustani classical rhythm", "lat": 28.7041, "lon": 77.1025, "color": "#8b5cf6"},
    {"instrument": "Taiko", "origin": "Various regions", "country": "Japan", "period": "6th century", "type": "Barrel Drum", "note": "Ancestral Japanese ensemble drumming", "lat": 35.0116, "lon": 135.7681, "color": "#ef4444"},
    {"instrument": "Bodhran", "origin": "County Kerry", "country": "Ireland", "period": "17th century", "type": "Frame Drum", "note": "Essential to Irish traditional music", "lat": 52.1545, "lon": -9.5669, "color": "#10b981"},
    {"instrument": "Steel Pan", "origin": "Port of Spain", "country": "Trinidad & Tobago", "period": "1930s", "type": "Idiophone", "note": "Only acoustic instrument invented in 20th century", "lat": 10.6596, "lon": -61.5086, "color": "#06b6d4"},
    {"instrument": "Cajon", "origin": "Lima", "country": "Peru", "period": "18th century", "type": "Box Drum", "note": "Afro-Peruvian box percussion", "lat": -12.0464, "lon": -77.0428, "color": "#3b82f6"},
    {"instrument": "Conga", "origin": "Havana", "country": "Cuba", "period": "19th century", "type": "Barrel Drum", "note": "Afro-Cuban staved drum", "lat": 23.1136, "lon": -82.3666, "color": "#14b8a6"},
    {"instrument": "Timpani", "origin": "Central Europe", "country": "Austria", "period": "15th century", "type": "Kettledrum", "note": "Orchestral timpani from cavalry drums", "lat": 48.2082, "lon": 16.3738, "color": "#a855f7"},
    {"instrument": "Snare Drum", "origin": "Basel", "country": "Switzerland", "period": "14th century", "type": "Drum", "note": "Basel carnival snare tradition", "lat": 47.5596, "lon": 7.5886, "color": "#f97316"},
    {"instrument": "Gamelan Gongs", "origin": "Central Java", "country": "Indonesia", "period": "Ancient", "type": "Gong/Metallophone", "note": "Bronze percussion ensemble", "lat": -7.5755, "lon": 110.8243, "color": "#84cc16"},
    {"instrument": "Berimbau", "origin": "Salvador da Bahia", "country": "Brazil", "period": "16th century", "type": "Musical Bow", "note": "Afro-Brazilian capoeira instrument", "lat": -12.9714, "lon": -38.5124, "color": "#facc15"},
    {"instrument": "Mridangam", "origin": "Tamil Nadu", "country": "India", "period": "Ancient", "type": "Double-headed Drum", "note": "Carnatic classical percussion", "lat": 13.0827, "lon": 80.2707, "color": "#22d3ee"},
    {"instrument": "Darbuka (Doumbek)", "origin": "Cairo", "country": "Egypt", "period": "Ancient", "type": "Goblet Drum", "note": "Middle Eastern goblet drum", "lat": 30.0444, "lon": 31.2357, "color": "#c084fc"},
    {"instrument": "Hang / Handpan", "origin": "Bern", "country": "Switzerland", "period": "2000", "type": "Steel Idiophone", "note": "PANArt invention, modern steel tongue drum", "lat": 46.9480, "lon": 7.4474, "color": "#e11d48"},
    {"instrument": "Maracas", "origin": "Venezuela/Colombia", "country": "Venezuela", "period": "Pre-Columbian", "type": "Rattle", "note": "Indigenous Taino shaker instrument", "lat": 10.4806, "lon": -66.9036, "color": "#dc2626"},
    {"instrument": "Dundun (Doundounba)", "origin": "Guinea", "country": "Guinea", "period": "Ancient", "type": "Bass Drum", "note": "Mande bass drum trio ensemble", "lat": 9.9456, "lon": -9.6966, "color": "#d946ef"},
    {"instrument": "Drum Kit (Modern)", "origin": "New Orleans", "country": "USA", "period": "1900s", "type": "Drum Set", "note": "Combined kit for jazz and popular music", "lat": 29.9511, "lon": -90.0715, "color": "#0ea5e9"},
    {"instrument": "Surdo", "origin": "Rio de Janeiro", "country": "Brazil", "period": "1920s", "type": "Bass Drum", "note": "Heart of samba school bateria", "lat": -22.9068, "lon": -43.1729, "color": "#fb923c"},
    {"instrument": "Bongo", "origin": "Eastern Cuba", "country": "Cuba", "period": "Late 1800s", "type": "Paired Drums", "note": "Son cubano paired drums", "lat": 20.3585, "lon": -76.3045, "color": "#78716c"},
    {"instrument": "Janggu (Changgo)", "origin": "Seoul", "country": "South Korea", "period": "Ancient", "type": "Hourglass Drum", "note": "Korean traditional hourglass drum", "lat": 37.5665, "lon": 126.9780, "color": "#d97706"},
]


@st.cache_data(ttl=3600)
def _get_drums_data():
    return pd.DataFrame(DRUMS_PERCUSSION)


# =====================================================================
# 5. WIND INSTRUMENTS
# =====================================================================
WIND_INSTRUMENTS = [
    {"instrument": "Saxophone (invention)", "city": "Dinant", "country": "Belgium", "year": 1846, "type": "Woodwind (single reed)", "maker": "Adolphe Sax", "note": "Birthplace and museum of Adolphe Sax", "lat": 50.2604, "lon": 4.9123, "color": "#f59e0b"},
    {"instrument": "Buffet Crampon Clarinets", "city": "Paris / Mantes-la-Ville", "country": "France", "year": 1825, "type": "Clarinet/Oboe", "maker": "Buffet Crampon", "note": "Premier French woodwind maker", "lat": 48.9741, "lon": 1.7106, "color": "#ec4899"},
    {"instrument": "Selmer Saxophones", "city": "Paris", "country": "France", "year": 1885, "type": "Saxophone/Clarinet", "maker": "Henri Selmer Paris", "note": "Mark VI sax legendary model", "lat": 48.8566, "lon": 2.3522, "color": "#8b5cf6"},
    {"instrument": "Didgeridoo", "city": "Arnhem Land", "country": "Australia", "year": -1500, "type": "Drone Pipe", "maker": "Aboriginal Australians", "note": "Oldest wind instrument, 1500+ years", "lat": -12.4634, "lon": 132.8456, "color": "#06b6d4"},
    {"instrument": "Shakuhachi", "city": "Kyoto", "country": "Japan", "year": 1600, "type": "End-blown Flute", "maker": "Zen Buddhist monks", "note": "Bamboo meditation flute", "lat": 35.0116, "lon": 135.7681, "color": "#ef4444"},
    {"instrument": "Pan Flute (Nai)", "city": "Bucharest", "country": "Romania", "year": -500, "type": "Panpipe", "maker": "Gheorghe Zamfir tradition", "note": "Romanian pan flute mastery", "lat": 44.4268, "lon": 26.1025, "color": "#10b981"},
    {"instrument": "Heckel Bassoon", "city": "Wiesbaden", "country": "Germany", "year": 1831, "type": "Bassoon", "maker": "Wilhelm Heckel", "note": "Gold standard German bassoon", "lat": 50.0826, "lon": 8.2400, "color": "#3b82f6"},
    {"instrument": "Bansuri", "city": "Varanasi", "country": "India", "year": -500, "type": "Transverse Flute", "maker": "Pannalal Ghosh lineage", "note": "Bamboo flute of Hindustani music", "lat": 25.3176, "lon": 82.9739, "color": "#14b8a6"},
    {"instrument": "Duduk", "city": "Yerevan", "country": "Armenia", "year": -300, "type": "Double Reed", "maker": "Apricot wood tradition", "note": "UNESCO intangible heritage, apricot wood", "lat": 40.1792, "lon": 44.4991, "color": "#a855f7"},
    {"instrument": "Suona", "city": "Beijing", "country": "China", "year": 300, "type": "Double Reed", "maker": "Chinese folk tradition", "note": "Loud ceremonial Chinese oboe", "lat": 39.9042, "lon": 116.4074, "color": "#f97316"},
    {"instrument": "Uilleann Pipes", "city": "Dublin", "country": "Ireland", "year": 1700, "type": "Bagpipe", "maker": "Na Piobair Uilleann", "note": "Bellows-blown Irish bagpipes", "lat": 53.3498, "lon": -6.2603, "color": "#84cc16"},
    {"instrument": "Great Highland Bagpipe", "city": "Edinburgh", "country": "Scotland", "year": 1400, "type": "Bagpipe", "maker": "Scottish pipers", "note": "Iconic Scottish military pipe", "lat": 55.9533, "lon": -3.1883, "color": "#facc15"},
    {"instrument": "Zurna", "city": "Istanbul", "country": "Turkey", "year": -500, "type": "Double Reed", "maker": "Ottoman tradition", "note": "Loud oboe of Ottoman military bands", "lat": 41.0082, "lon": 28.9784, "color": "#22d3ee"},
    {"instrument": "Powell Flutes", "city": "Waltham, MA", "country": "USA", "year": 1927, "type": "Flute", "maker": "Verne Q. Powell", "note": "Premium American concert flutes", "lat": 42.3765, "lon": -71.2356, "color": "#c084fc"},
    {"instrument": "Yamaha Wind Instruments", "city": "Hamamatsu", "country": "Japan", "year": 1967, "type": "All Winds", "maker": "Yamaha Corporation", "note": "Major global wind instrument maker", "lat": 34.7108, "lon": 137.7261, "color": "#e11d48"},
    {"instrument": "Harmonica (invention)", "city": "Trossingen", "country": "Germany", "year": 1857, "type": "Free Reed", "maker": "Matthias Hohner", "note": "Hohner harmonica factory town", "lat": 48.0761, "lon": 8.6411, "color": "#dc2626"},
    {"instrument": "Quena", "city": "Cusco", "country": "Peru", "year": -500, "type": "End-blown Flute", "maker": "Andean tradition", "note": "Traditional Andean notched flute", "lat": -13.5319, "lon": -71.9675, "color": "#d946ef"},
    {"instrument": "Kaval", "city": "Plovdiv", "country": "Bulgaria", "year": 500, "type": "End-blown Flute", "maker": "Balkan shepherd tradition", "note": "Bulgarian/Turkish pastoral flute", "lat": 42.6977, "lon": 23.3219, "color": "#0ea5e9"},
    {"instrument": "Ocarina", "city": "Budrio", "country": "Italy", "year": 1853, "type": "Vessel Flute", "maker": "Giuseppe Donati", "note": "Italian invention, globular flute", "lat": 44.5375, "lon": 11.5314, "color": "#fb923c"},
    {"instrument": "Accordion (invention)", "city": "Vienna", "country": "Austria", "year": 1829, "type": "Free Reed", "maker": "Cyrill Demian", "note": "Patented in Vienna, spread worldwide", "lat": 48.2082, "lon": 16.3738, "color": "#78716c"},
    {"instrument": "Dizi", "city": "Hangzhou", "country": "China", "year": -500, "type": "Transverse Flute", "maker": "Chinese bamboo tradition", "note": "Chinese bamboo transverse flute with membrane", "lat": 30.2741, "lon": 120.1551, "color": "#d97706"},
]


@st.cache_data(ttl=3600)
def _get_wind_data():
    return pd.DataFrame(WIND_INSTRUMENTS)


# =====================================================================
# 6. TRADITIONAL WORLD INSTRUMENTS
# =====================================================================
TRADITIONAL_WORLD = [
    {"instrument": "Sitar", "city": "Varanasi / Delhi", "country": "India", "region": "South Asia", "type": "Plucked String", "note": "Ravi Shankar popularized worldwide", "lat": 25.3176, "lon": 82.9739, "color": "#f59e0b"},
    {"instrument": "Koto", "city": "Kyoto", "country": "Japan", "region": "East Asia", "type": "Plucked Zither", "note": "13-string Japanese floor zither", "lat": 35.0116, "lon": 135.7681, "color": "#ec4899"},
    {"instrument": "Guqin", "city": "Beijing / Nanjing", "country": "China", "region": "East Asia", "type": "Plucked Zither", "note": "UNESCO heritage, 3000+ years old", "lat": 39.9042, "lon": 116.4074, "color": "#8b5cf6"},
    {"instrument": "Balalaika", "city": "Moscow / St. Petersburg", "country": "Russia", "region": "Eastern Europe", "type": "Plucked String", "note": "Triangular-bodied Russian folk lute", "lat": 55.7558, "lon": 37.6173, "color": "#ef4444"},
    {"instrument": "Gamelan Ensemble", "city": "Yogyakarta", "country": "Indonesia", "region": "Southeast Asia", "type": "Percussion Ensemble", "note": "Bronze orchestra of Java and Bali", "lat": -7.7972, "lon": 110.3688, "color": "#10b981"},
    {"instrument": "Oud", "city": "Baghdad / Damascus", "country": "Iraq / Syria", "region": "Middle East", "type": "Plucked Lute", "note": "Ancestor of the European lute", "lat": 33.3152, "lon": 44.3661, "color": "#06b6d4"},
    {"instrument": "Kora", "city": "Casamance", "country": "Senegal / Gambia", "region": "West Africa", "type": "Bridge Harp", "note": "21-string West African harp-lute", "lat": 12.5858, "lon": -15.6727, "color": "#3b82f6"},
    {"instrument": "Mbira (Thumb Piano)", "city": "Harare region", "country": "Zimbabwe", "region": "Southern Africa", "type": "Lamellophone", "note": "Sacred Shona spiritual instrument", "lat": -17.8292, "lon": 31.0522, "color": "#14b8a6"},
    {"instrument": "Didgeridoo", "city": "Arnhem Land", "country": "Australia", "region": "Oceania", "type": "Aerophone", "note": "Aboriginal drone instrument, 1500+ years", "lat": -12.4634, "lon": 132.8456, "color": "#a855f7"},
    {"instrument": "Charango", "city": "Potosi", "country": "Bolivia", "region": "South America", "type": "Plucked Lute", "note": "Small Andean 10-string lute", "lat": -19.5836, "lon": -65.7531, "color": "#f97316"},
    {"instrument": "Nyckelharpa", "city": "Uppland", "country": "Sweden", "region": "Northern Europe", "type": "Bowed String", "note": "Keyed fiddle, UNESCO heritage", "lat": 59.8586, "lon": 17.6389, "color": "#84cc16"},
    {"instrument": "Bouzouki", "city": "Athens", "country": "Greece", "region": "Southern Europe", "type": "Plucked Lute", "note": "Rebetiko and Greek folk music", "lat": 37.9838, "lon": 23.7275, "color": "#facc15"},
    {"instrument": "Bandura", "city": "Kyiv", "country": "Ukraine", "region": "Eastern Europe", "type": "Plucked Zither/Lute", "note": "Ukrainian national string instrument", "lat": 50.4501, "lon": 30.5234, "color": "#22d3ee"},
    {"instrument": "Erhu", "city": "Wuxi / Beijing", "country": "China", "region": "East Asia", "type": "Bowed String", "note": "Two-string Chinese fiddle", "lat": 31.4912, "lon": 120.3119, "color": "#c084fc"},
    {"instrument": "Shamisen", "city": "Osaka", "country": "Japan", "region": "East Asia", "type": "Plucked Lute", "note": "Three-string Japanese banjo-like lute", "lat": 34.6937, "lon": 135.5023, "color": "#e11d48"},
    {"instrument": "Kanun (Qanun)", "city": "Istanbul / Cairo", "country": "Turkey / Egypt", "region": "Middle East", "type": "Plucked Zither", "note": "Trapezoidal plucked zither", "lat": 41.0082, "lon": 28.9784, "color": "#dc2626"},
    {"instrument": "Pipa", "city": "Shanghai / Beijing", "country": "China", "region": "East Asia", "type": "Plucked Lute", "note": "Four-stringed pear-shaped lute", "lat": 31.2304, "lon": 121.4737, "color": "#d946ef"},
    {"instrument": "Gayageum", "city": "Seoul", "country": "South Korea", "region": "East Asia", "type": "Plucked Zither", "note": "12-string Korean zither", "lat": 37.5665, "lon": 126.9780, "color": "#0ea5e9"},
    {"instrument": "Rebab", "city": "Fez / Marrakech", "country": "Morocco", "region": "North Africa", "type": "Bowed String", "note": "Spike fiddle of Arab-Andalusian music", "lat": 34.0181, "lon": -5.0078, "color": "#fb923c"},
    {"instrument": "Santur", "city": "Isfahan", "country": "Iran", "region": "Middle East", "type": "Hammered Dulcimer", "note": "Persian hammered dulcimer", "lat": 32.6546, "lon": 51.6680, "color": "#78716c"},
    {"instrument": "Hurdy-Gurdy", "city": "Auvergne region", "country": "France", "region": "Western Europe", "type": "Bowed String (crank)", "note": "Medieval crank-operated string instrument", "lat": 45.7772, "lon": 3.0870, "color": "#d97706"},
    {"instrument": "Kantele", "city": "Karelia / Helsinki", "country": "Finland", "region": "Northern Europe", "type": "Plucked Zither", "note": "Finnish national instrument from Kalevala", "lat": 60.1699, "lon": 24.9384, "color": "#0ea5e9"},
    {"instrument": "Berimbau", "city": "Salvador da Bahia", "country": "Brazil", "region": "South America", "type": "Musical Bow", "note": "Single-string Afro-Brazilian bow", "lat": -12.9714, "lon": -38.5124, "color": "#10b981"},
    {"instrument": "Ukulele", "city": "Honolulu", "country": "USA (Hawaii)", "region": "Oceania", "type": "Plucked String", "note": "Portuguese-Hawaiian small guitar", "lat": 21.3069, "lon": -157.8583, "color": "#ec4899"},
    {"instrument": "Morin Khuur", "city": "Ulaanbaatar", "country": "Mongolia", "region": "Central Asia", "type": "Bowed String", "note": "Horsehead fiddle, Mongolian national symbol", "lat": 47.8864, "lon": 106.9057, "color": "#8b5cf6"},
]


@st.cache_data(ttl=3600)
def _get_traditional_data():
    return pd.DataFrame(TRADITIONAL_WORLD)


# =====================================================================
# 7. ORGAN & CHURCH MUSIC
# =====================================================================
ORGAN_CHURCH = [
    {"organ": "Notre-Dame de Paris", "city": "Paris", "country": "France", "builder": "Cavaille-Coll / Thierry", "pipes": 7952, "year": 1403, "note": "Five-manual grand organ, survived 2019 fire", "lat": 48.8530, "lon": 2.3499, "color": "#f59e0b"},
    {"organ": "St. Peter's Basilica", "city": "Vatican City", "country": "Vatican", "builder": "Tamburini", "pipes": 5000, "year": 1962, "note": "Two organs in world's largest church", "lat": 41.9022, "lon": 12.4539, "color": "#ec4899"},
    {"organ": "Thomaskirche (Bach)", "city": "Leipzig", "country": "Germany", "builder": "Various", "pipes": 5112, "year": 1525, "note": "J.S. Bach served as Thomaskantor 1723-1750", "lat": 51.3390, "lon": 12.3720, "color": "#8b5cf6"},
    {"organ": "Haarlem Grote Kerk (Muller)", "city": "Haarlem", "country": "Netherlands", "builder": "Christian Muller", "pipes": 5068, "year": 1738, "note": "Mozart and Handel played here", "lat": 52.3812, "lon": 4.6360, "color": "#06b6d4"},
    {"organ": "St-Sulpice (Cavaille-Coll)", "city": "Paris", "country": "France", "builder": "Aristide Cavaille-Coll", "pipes": 6588, "year": 1862, "note": "Masterwork of French organ building", "lat": 48.8510, "lon": 2.3347, "color": "#10b981"},
    {"organ": "Passau Cathedral", "city": "Passau", "country": "Germany", "builder": "Eisenbarth", "pipes": 17974, "year": 1928, "note": "Largest cathedral organ in Europe", "lat": 48.5748, "lon": 13.4654, "color": "#ef4444"},
    {"organ": "Atlantic City Convention Hall", "city": "Atlantic City, NJ", "country": "USA", "builder": "Midmer-Losh", "pipes": 33114, "year": 1932, "note": "World's largest pipe organ", "lat": 39.3571, "lon": -74.4376, "color": "#3b82f6"},
    {"organ": "Wanamaker Organ", "city": "Philadelphia", "country": "USA", "builder": "Los Angeles Art Organ Co.", "pipes": 28750, "year": 1904, "note": "World's largest playable pipe organ", "lat": 39.9526, "lon": -75.1652, "color": "#14b8a6"},
    {"organ": "Westminster Abbey", "city": "London", "country": "UK", "builder": "Harrison & Harrison", "pipes": 5700, "year": 1937, "note": "Royal coronation organ", "lat": 51.4994, "lon": -0.1273, "color": "#a855f7"},
    {"organ": "Freiburger Munster", "city": "Freiburg", "country": "Germany", "builder": "Rieger", "pipes": 5232, "year": 1965, "note": "Acclaimed modern instrument in Gothic minster", "lat": 47.9959, "lon": 7.8522, "color": "#f97316"},
    {"organ": "Sydney Town Hall Grand Organ", "city": "Sydney", "country": "Australia", "builder": "William Hill", "pipes": 8756, "year": 1890, "note": "Largest 19th-century organ extant", "lat": -33.8731, "lon": 151.2065, "color": "#84cc16"},
    {"organ": "Salzburg Cathedral", "city": "Salzburg", "country": "Austria", "builder": "Multiple builders", "pipes": 4000, "year": 1703, "note": "Mozart baptized and served as organist", "lat": 47.7981, "lon": 13.0465, "color": "#facc15"},
    {"organ": "King of Instruments (Moscow)", "city": "Moscow", "country": "Russia", "builder": "Cavaille-Coll", "pipes": 6000, "year": 1901, "note": "Great Hall of Moscow Conservatory", "lat": 55.7558, "lon": 37.6173, "color": "#22d3ee"},
    {"organ": "Buxtehude Organ (Lubeck)", "city": "Lubeck", "country": "Germany", "builder": "Stellwagen", "pipes": 4684, "year": 1637, "note": "Buxtehude served here, Bach walked 250 miles to hear", "lat": 53.8655, "lon": 10.6866, "color": "#c084fc"},
    {"organ": "Walt Disney Concert Hall", "city": "Los Angeles", "country": "USA", "builder": "Glatter-Gotz/Rosales", "pipes": 6125, "year": 2004, "note": "Frank Gehry designed cases, 'French Fries' organ", "lat": 34.0553, "lon": -118.2498, "color": "#e11d48"},
    {"organ": "Dom zu Trier", "city": "Trier", "country": "Germany", "builder": "Klais", "pipes": 6258, "year": 1974, "note": "Germany's oldest cathedral", "lat": 49.7567, "lon": 6.6431, "color": "#dc2626"},
    {"organ": "Hallgrimskirkja", "city": "Reykjavik", "country": "Iceland", "builder": "Johannes Klais", "pipes": 5275, "year": 1992, "note": "Iconic Icelandic church organ, 15m tall", "lat": 64.1418, "lon": -21.9267, "color": "#d946ef"},
    {"organ": "Cologne Cathedral", "city": "Cologne", "country": "Germany", "builder": "Klais", "pipes": 5622, "year": 1998, "note": "Swallow's nest organ in Gothic nave", "lat": 50.9413, "lon": 6.9583, "color": "#0ea5e9"},
    {"organ": "Marienbasilika", "city": "Kevelaer", "country": "Germany", "builder": "Seifert", "pipes": 7854, "year": 1907, "note": "Major pilgrimage church organ", "lat": 51.5833, "lon": 6.2500, "color": "#fb923c"},
    {"organ": "Cathedral of St. John the Divine", "city": "New York City", "country": "USA", "builder": "Aeolian-Skinner", "pipes": 8514, "year": 1954, "note": "Largest cathedral in North America", "lat": 40.8038, "lon": -73.9615, "color": "#78716c"},
]


@st.cache_data(ttl=3600)
def _get_organ_data():
    return pd.DataFrame(ORGAN_CHURCH)


# =====================================================================
# 8. BRASS INSTRUMENTS
# =====================================================================
BRASS_INSTRUMENTS = [
    {"maker": "Monette Instruments", "city": "Portland, OR", "country": "USA", "founded": 1983, "type": "Trumpet", "note": "Radical heavy-wall trumpet design", "lat": 45.5152, "lon": -122.6784, "color": "#f59e0b"},
    {"maker": "Bach Stradivarius (Conn-Selmer)", "city": "Elkhart, IN", "country": "USA", "founded": 1924, "type": "Trumpet/Trombone", "note": "Vincent Bach; most popular pro trumpets", "lat": 41.6820, "lon": -85.9767, "color": "#ec4899"},
    {"maker": "C.G. Conn", "city": "Elkhart, IN", "country": "USA", "founded": 1876, "type": "All Brass", "note": "Pioneer American brass manufacturer", "lat": 41.6850, "lon": -85.9800, "color": "#8b5cf6"},
    {"maker": "King Musical Instruments", "city": "Eastlake, OH", "country": "USA", "founded": 1893, "type": "Trombone/Tuba", "note": "King 2B trombone legend", "lat": 41.6536, "lon": -81.4503, "color": "#ef4444"},
    {"maker": "Yamaha Brass", "city": "Hamamatsu", "country": "Japan", "founded": 1966, "type": "All Brass", "note": "Xeno and Custom series pro horns", "lat": 34.7108, "lon": 137.7261, "color": "#06b6d4"},
    {"maker": "Miraphone", "city": "Waldkraiburg", "country": "Germany", "founded": 1946, "type": "Tuba/Euphonium", "note": "Premier German tuba maker", "lat": 48.2079, "lon": 12.3994, "color": "#10b981"},
    {"maker": "Alexander Horns", "city": "Mainz", "country": "Germany", "founded": 1782, "type": "French Horn", "note": "Model 103 horn standard for orchestras", "lat": 49.9929, "lon": 8.2473, "color": "#3b82f6"},
    {"maker": "Courtois", "city": "Paris", "country": "France", "founded": 1803, "type": "Trumpet/Trombone/Tuba", "note": "Historic French brass maker", "lat": 48.8566, "lon": 2.3522, "color": "#14b8a6"},
    {"maker": "Besson", "city": "London / Paris", "country": "UK / France", "founded": 1837, "type": "Cornet/Euphonium", "note": "Sovereign and Prestige series", "lat": 51.5074, "lon": -0.1278, "color": "#a855f7"},
    {"maker": "B&S (B. & S. GmbH)", "city": "Markneukirchen", "country": "Germany", "founded": 1770, "type": "Trumpet/Tuba", "note": "Challenger and 3 Valve rotary trumpets", "lat": 50.3128, "lon": 12.3264, "color": "#f97316"},
    {"maker": "Schilke Music", "city": "Melrose Park, IL", "country": "USA", "founded": 1956, "type": "Trumpet", "note": "Renold Schilke, acoustics-based design", "lat": 41.9006, "lon": -87.8567, "color": "#84cc16"},
    {"maker": "Edwards Instrument Co.", "city": "Elkhart, IN", "country": "USA", "founded": 1960, "type": "Trombone", "note": "Custom-built professional trombones", "lat": 41.6870, "lon": -85.9730, "color": "#facc15"},
    {"maker": "Willson Brass", "city": "Flums", "country": "Switzerland", "founded": 1920, "type": "Euphonium/Tuba", "note": "Swiss precision euphoniums", "lat": 47.0921, "lon": 9.3460, "color": "#22d3ee"},
    {"maker": "Adams Musical Instruments", "city": "Ittervoort", "country": "Netherlands", "founded": 1970, "type": "Trumpet/Flugelhorn", "note": "Dutch custom brass, selected series", "lat": 51.1983, "lon": 5.8561, "color": "#c084fc"},
    {"maker": "Paxman Horns", "city": "London", "country": "UK", "founded": 1945, "type": "French Horn", "note": "Handmade London French horns", "lat": 51.5200, "lon": -0.1400, "color": "#e11d48"},
    {"maker": "Josef Lidl", "city": "Brno", "country": "Czech Republic", "founded": 1892, "type": "All Brass", "note": "Major Czech brass manufacturer", "lat": 49.1951, "lon": 16.6068, "color": "#dc2626"},
    {"maker": "Thein Brass", "city": "Bremen", "country": "Germany", "founded": 1969, "type": "Trombone/Horn", "note": "Custom German trombones", "lat": 53.0793, "lon": 8.8017, "color": "#d946ef"},
    {"maker": "Holton (Leblanc)", "city": "Elkhorn, WI", "country": "USA", "founded": 1898, "type": "French Horn/Trombone", "note": "Farkas model horn favored by many", "lat": 42.6728, "lon": -88.5443, "color": "#0ea5e9"},
    {"maker": "Getzen Trumpets", "city": "Elkhorn, WI", "country": "USA", "founded": 1939, "type": "Trumpet/Trombone", "note": "Family-owned American brass maker", "lat": 42.6750, "lon": -88.5500, "color": "#fb923c"},
    {"maker": "Jupiter Band Instruments", "city": "Taipei", "country": "Taiwan", "founded": 1930, "type": "All Brass", "note": "KHS Musical Instruments, major global brand", "lat": 25.0330, "lon": 121.5654, "color": "#78716c"},
]


@st.cache_data(ttl=3600)
def _get_brass_data():
    return pd.DataFrame(BRASS_INSTRUMENTS)


# =====================================================================
# 9. ELECTRONIC MUSIC INSTRUMENTS
# =====================================================================
ELECTRONIC_INSTRUMENTS = [
    {"instrument": "Theremin", "city": "Saint Petersburg", "country": "Russia", "year": 1920, "inventor": "Leon Theremin", "type": "Electronic", "note": "First electronic instrument, played without touch", "lat": 59.9343, "lon": 30.3351, "color": "#f59e0b"},
    {"instrument": "Moog Synthesizer", "city": "Asheville, NC", "country": "USA", "year": 1964, "inventor": "Robert Moog", "type": "Analog Synth", "note": "Minimoog revolutionized popular music", "lat": 35.5951, "lon": -82.5515, "color": "#ec4899"},
    {"instrument": "Roland Synthesizers", "city": "Hamamatsu", "country": "Japan", "year": 1972, "inventor": "Ikutaro Kakehashi", "type": "Digital/Analog Synth", "note": "TR-808, TB-303, Jupiter-8 legends", "lat": 34.7108, "lon": 137.7261, "color": "#8b5cf6"},
    {"instrument": "Korg Synthesizers", "city": "Tokyo", "country": "Japan", "year": 1962, "inventor": "Tsutomu Katoh", "type": "Analog/Digital Synth", "note": "MS-20, M1, Minilogue", "lat": 35.6762, "lon": 139.6503, "color": "#ef4444"},
    {"instrument": "ARP Instruments", "city": "Lexington, MA", "country": "USA", "year": 1969, "inventor": "Alan R. Pearlman", "type": "Analog Synth", "note": "ARP 2600, Odyssey classics", "lat": 42.4473, "lon": -71.2245, "color": "#06b6d4"},
    {"instrument": "Buchla Modular", "city": "San Francisco", "country": "USA", "year": 1963, "inventor": "Don Buchla", "type": "Modular Synth", "note": "West Coast synthesis pioneer", "lat": 37.7749, "lon": -122.4194, "color": "#10b981"},
    {"instrument": "Ondes Martenot", "city": "Paris", "country": "France", "year": 1928, "inventor": "Maurice Martenot", "type": "Electronic", "note": "Used by Messiaen, Radiohead", "lat": 48.8566, "lon": 2.3522, "color": "#3b82f6"},
    {"instrument": "Mellotron", "city": "Birmingham", "country": "UK", "year": 1963, "inventor": "Streetly Electronics", "type": "Electro-mechanical", "note": "Tape-replay keyboard, Beatles used it", "lat": 52.4862, "lon": -1.8904, "color": "#14b8a6"},
    {"instrument": "Fairlight CMI", "city": "Sydney", "country": "Australia", "year": 1979, "inventor": "Fairlight Instruments", "type": "Digital Sampler", "note": "First practical digital sampling workstation", "lat": -33.8688, "lon": 151.2093, "color": "#a855f7"},
    {"instrument": "E-mu Systems / Emulator", "city": "Scotts Valley, CA", "country": "USA", "year": 1981, "inventor": "Dave Rossum", "type": "Sampler", "note": "Affordable sampling revolution", "lat": 37.0513, "lon": -122.0147, "color": "#f97316"},
    {"instrument": "Oberheim Synthesizers", "city": "Los Angeles", "country": "USA", "year": 1969, "inventor": "Tom Oberheim", "type": "Analog Synth", "note": "OB-Xa, Matrix-12 polyphonic synths", "lat": 34.0522, "lon": -118.2437, "color": "#84cc16"},
    {"instrument": "Sequential Circuits Prophet", "city": "San Jose, CA", "country": "USA", "year": 1978, "inventor": "Dave Smith", "type": "Analog Polysynth", "note": "Prophet-5 first fully programmable poly synth", "lat": 37.3382, "lon": -121.8863, "color": "#facc15"},
    {"instrument": "Nord Keyboards", "city": "Stockholm", "country": "Sweden", "year": 1983, "inventor": "Clavia Digital Instruments", "type": "Digital Synth/Organ", "note": "Nord Lead, Stage, Electro lines", "lat": 59.3293, "lon": 18.0686, "color": "#22d3ee"},
    {"instrument": "Teenage Engineering", "city": "Stockholm", "country": "Sweden", "year": 2005, "inventor": "Jesper Kouthoofd", "type": "Digital/Synth", "note": "OP-1, Pocket Operators", "lat": 59.3350, "lon": 18.0750, "color": "#c084fc"},
    {"instrument": "Elektron", "city": "Gothenburg", "country": "Sweden", "year": 1998, "inventor": "Elektron team", "type": "Digital/Hybrid", "note": "Digitakt, Octatrack, Analog series", "lat": 57.7089, "lon": 11.9746, "color": "#e11d48"},
    {"instrument": "Hammond Organ", "city": "Chicago", "country": "USA", "year": 1935, "inventor": "Laurens Hammond", "type": "Electro-mechanical Organ", "note": "B-3 organ, tonewheel technology", "lat": 41.8781, "lon": -87.6298, "color": "#dc2626"},
    {"instrument": "Eurorack Modular (Doepfer)", "city": "Grafelfing (Munich)", "country": "Germany", "year": 1995, "inventor": "Dieter Doepfer", "type": "Modular Synth", "note": "Defined modern Eurorack standard", "lat": 48.1172, "lon": 11.4300, "color": "#d946ef"},
    {"instrument": "Akai MPC", "city": "Tokyo", "country": "Japan", "year": 1988, "inventor": "Roger Linn / Akai", "type": "Sampler/Sequencer", "note": "MPC60/2000/3000 shaped hip-hop production", "lat": 35.6800, "lon": 139.6900, "color": "#0ea5e9"},
    {"instrument": "Novation Synthesizers", "city": "High Wycombe", "country": "UK", "year": 1992, "inventor": "Focusrite/Novation", "type": "Digital/Hybrid Synth", "note": "Bass Station, Peak, Summit series", "lat": 51.6296, "lon": -0.7482, "color": "#fb923c"},
    {"instrument": "Arturia", "city": "Grenoble", "country": "France", "year": 1999, "inventor": "Arturia team", "type": "Digital/Analog Hybrid", "note": "MiniBrute, MatrixBrute, software synths", "lat": 45.1885, "lon": 5.7245, "color": "#78716c"},
]


@st.cache_data(ttl=3600)
def _get_electronic_data():
    return pd.DataFrame(ELECTRONIC_INSTRUMENTS)


# =====================================================================
# 10. MUSIC INSTRUMENT MUSEUMS
# =====================================================================
INSTRUMENT_MUSEUMS = [
    {"museum": "Musical Instrument Museum (MIM)", "city": "Phoenix, AZ", "country": "USA", "founded": 2010, "collection": 8000, "note": "World's largest instrument museum, 200+ countries", "lat": 33.6680, "lon": -111.9783, "color": "#f59e0b"},
    {"museum": "Musee de la Musique", "city": "Paris", "country": "France", "founded": 1997, "collection": 7000, "note": "Inside Cite de la Musique, Villette", "lat": 48.8895, "lon": 2.3936, "color": "#ec4899"},
    {"museum": "Musical Instruments Museum (MIM Brussels)", "city": "Brussels", "country": "Belgium", "founded": 2000, "collection": 8000, "note": "Art Nouveau Old England building", "lat": 50.8427, "lon": 4.3580, "color": "#8b5cf6"},
    {"museum": "Metropolitan Museum of Art - Musical Instruments", "city": "New York City", "country": "USA", "founded": 1889, "collection": 5000, "note": "Oldest Stradivari violin in Americas", "lat": 40.7794, "lon": -73.9632, "color": "#ef4444"},
    {"museum": "Hamamatsu Museum of Musical Instruments", "city": "Hamamatsu", "country": "Japan", "founded": 1995, "collection": 3300, "note": "Asia's only public instrument museum", "lat": 34.7054, "lon": 137.7302, "color": "#06b6d4"},
    {"museum": "Museo degli Strumenti Musicali", "city": "Rome", "country": "Italy", "founded": 1974, "collection": 3000, "note": "Barberini Harp and Stradivari pieces", "lat": 41.8899, "lon": 12.5078, "color": "#10b981"},
    {"museum": "Ringve Museum", "city": "Trondheim", "country": "Norway", "founded": 1952, "collection": 2000, "note": "Norway's national music museum", "lat": 63.4400, "lon": 10.4500, "color": "#3b82f6"},
    {"museum": "Grassi Museum of Musical Instruments", "city": "Leipzig", "country": "Germany", "founded": 1929, "collection": 5500, "note": "One of the oldest music museums globally", "lat": 51.3400, "lon": 12.3880, "color": "#14b8a6"},
    {"museum": "Museo Stradivari", "city": "Cremona", "country": "Italy", "founded": 1893, "collection": 700, "note": "Stradivari's tools, forms, and instruments", "lat": 45.1336, "lon": 10.0244, "color": "#a855f7"},
    {"museum": "Horniman Museum", "city": "London", "country": "UK", "founded": 1901, "collection": 9000, "note": "Largest instrument collection in UK", "lat": 51.4414, "lon": -0.0554, "color": "#f97316"},
    {"museum": "Germanisches Nationalmuseum", "city": "Nuremberg", "country": "Germany", "founded": 1852, "collection": 3200, "note": "Historic German instruments collection", "lat": 49.4479, "lon": 11.0760, "color": "#84cc16"},
    {"museum": "Royal College of Music Museum", "city": "London", "country": "UK", "founded": 1894, "collection": 1000, "note": "Rare European instruments from 1480", "lat": 51.4985, "lon": -0.1768, "color": "#facc15"},
    {"museum": "Shrine to Music Museum", "city": "Vermillion, SD", "country": "USA", "founded": 1973, "collection": 15000, "note": "National Music Museum at USD, largest US collection", "lat": 42.7794, "lon": -96.9289, "color": "#22d3ee"},
    {"museum": "Museo de Instrumentos Musicales", "city": "La Paz", "country": "Bolivia", "founded": 1962, "collection": 2800, "note": "Andean and colonial instruments", "lat": -16.4897, "lon": -68.1193, "color": "#c084fc"},
    {"museum": "Sammlung alter Musikinstrumente (KHM)", "city": "Vienna", "country": "Austria", "founded": 1916, "collection": 1100, "note": "Renaissance instruments in Hofburg", "lat": 48.2040, "lon": 16.3630, "color": "#e11d48"},
    {"museum": "Museu de la Musica", "city": "Barcelona", "country": "Spain", "founded": 1946, "collection": 2000, "note": "Torres guitars, historical keyboard collection", "lat": 41.3979, "lon": 2.1818, "color": "#dc2626"},
    {"museum": "St Cecilia's Hall", "city": "Edinburgh", "country": "UK", "founded": 1968, "collection": 500, "note": "Edinburgh University collection, oldest concert hall", "lat": 55.9486, "lon": -3.1870, "color": "#d946ef"},
    {"museum": "Musikinstrumenten-Museum Berlin", "city": "Berlin", "country": "Germany", "founded": 1888, "collection": 3500, "note": "Mighty Wurlitzer and historic keyboards", "lat": 52.5100, "lon": 13.3700, "color": "#0ea5e9"},
    {"museum": "Cite de la Musique - Philharmonie", "city": "Paris", "country": "France", "founded": 1995, "collection": 1000, "note": "Concert hall complex with instrument displays", "lat": 48.8910, "lon": 2.3940, "color": "#fb923c"},
    {"museum": "Museo del Violino", "city": "Cremona", "country": "Italy", "founded": 2013, "collection": 600, "note": "Stradivari, Amati, Guarneri masterpieces playable", "lat": 45.1336, "lon": 10.0260, "color": "#78716c"},
]


@st.cache_data(ttl=3600)
def _get_museum_data():
    return pd.DataFrame(INSTRUMENT_MUSEUMS)


# =====================================================================
# RENDER FUNCTIONS
# =====================================================================

def _render_piano():
    """Map 1: Piano & Keyboard Heritage."""
    df = _get_piano_data()
    st.markdown("#### Piano & Keyboard Heritage")
    c1, c2, c3 = st.columns(3)
    c1.metric("Makers", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest Founded", int(df["founded"].min()))

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Makers")
    ax.set_title("Piano Makers by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[35, 10], zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:180px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['maker'])}</b><br>"
            f"<b>City:</b> {_esc(row['city'])}, {_esc(row['country'])}<br>"
            f"<b>Founded:</b> {_esc(row['founded'])}<br>"
            f"<b>Type:</b> {_esc(row['type'])}<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=_esc(row["maker"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["maker", "city", "country", "founded", "type", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "piano_heritage.csv", "text/csv",
                       key="dl_piano")


def _render_guitar():
    """Map 2: Guitar Making Traditions."""
    df = _get_guitar_data()
    st.markdown("#### Guitar Making Traditions")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Makers", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest Founded", int(df["founded"].min()))
    c4.metric("Types", df["type"].nunique())

    type_counts = df["type"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(type_counts.index[::-1], type_counts.values[::-1],
            color=[_color_for(i) for i in range(len(type_counts))])
    ax.set_xlabel("Number of Makers")
    ax.set_title("Guitar Makers by Type")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[30, -20], zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:180px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['maker'])}</b><br>"
            f"<b>City:</b> {_esc(row['city'])}, {_esc(row['country'])}<br>"
            f"<b>Founded:</b> {_esc(row['founded'])}<br>"
            f"<b>Type:</b> {_esc(row['type'])}<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=_esc(row["maker"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["maker", "city", "country", "founded", "type", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "guitar_traditions.csv", "text/csv",
                       key="dl_guitar")


def _render_violin():
    """Map 3: Violin & String Instruments."""
    df = _get_violin_data()
    st.markdown("#### Violin & String Instruments")
    c1, c2, c3 = st.columns(3)
    c1.metric("Makers/Traditions", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Instrument Types", df["type"].nunique())

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Makers")
    ax.set_title("String Instrument Makers by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[40, 20], zoom=3)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:180px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['maker'])}</b><br>"
            f"<b>City:</b> {_esc(row['city'])}, {_esc(row['country'])}<br>"
            f"<b>Period:</b> {_esc(row['period'])}<br>"
            f"<b>Type:</b> {_esc(row['type'])}<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=_esc(row["maker"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["maker", "city", "country", "period", "type", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "violin_strings.csv", "text/csv",
                       key="dl_violin")


def _render_drums():
    """Map 4: Drums & Percussion Origins."""
    df = _get_drums_data()
    st.markdown("#### Drums & Percussion Origins")
    c1, c2, c3 = st.columns(3)
    c1.metric("Instruments", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Instruments")
    ax.set_title("Percussion Instruments by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[10, 20], zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:180px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['instrument'])}</b><br>"
            f"<b>Origin:</b> {_esc(row['origin'])}, {_esc(row['country'])}<br>"
            f"<b>Period:</b> {_esc(row['period'])}<br>"
            f"<b>Type:</b> {_esc(row['type'])}<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=_esc(row["instrument"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["instrument", "origin", "country", "period", "type", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "drums_percussion.csv", "text/csv",
                       key="dl_drums")


def _render_wind():
    """Map 5: Wind Instruments."""
    df = _get_wind_data()
    st.markdown("#### Wind Instruments")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Instruments", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())
    c4.metric("Makers", df["maker"].nunique())

    type_counts = df["type"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(type_counts.index[::-1], type_counts.values[::-1],
            color=[_color_for(i) for i in range(len(type_counts))])
    ax.set_xlabel("Count")
    ax.set_title("Wind Instruments by Type")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[30, 20], zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:180px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['instrument'])}</b><br>"
            f"<b>Location:</b> {_esc(row['city'])}, {_esc(row['country'])}<br>"
            f"<b>Year:</b> {_esc(row['year'])}<br>"
            f"<b>Type:</b> {_esc(row['type'])}<br>"
            f"<b>Maker:</b> {_esc(row['maker'])}<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=_esc(row["instrument"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["instrument", "city", "country", "year", "type", "maker", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "wind_instruments.csv", "text/csv",
                       key="dl_wind")


def _render_traditional():
    """Map 6: Traditional World Instruments."""
    df = _get_traditional_data()
    st.markdown("#### Traditional World Instruments")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Instruments", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Regions", df["region"].nunique())
    c4.metric("Types", df["type"].nunique())

    region_counts = df["region"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(region_counts.index[::-1], region_counts.values[::-1],
            color=[_color_for(i) for i in range(len(region_counts))])
    ax.set_xlabel("Number of Instruments")
    ax.set_title("Traditional Instruments by Region")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[20, 40], zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:180px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['instrument'])}</b><br>"
            f"<b>Origin:</b> {_esc(row['city'])}, {_esc(row['country'])}<br>"
            f"<b>Region:</b> {_esc(row['region'])}<br>"
            f"<b>Type:</b> {_esc(row['type'])}<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=_esc(row["instrument"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["instrument", "city", "country", "region", "type", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "traditional_world_instruments.csv",
                       "text/csv", key="dl_traditional")


def _render_organ():
    """Map 7: Organ & Church Music."""
    df = _get_organ_data()
    st.markdown("#### Organ & Church Music")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Organs", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Pipes", f"{df['pipes'].sum():,}")
    c4.metric("Largest (pipes)", f"{df['pipes'].max():,}")

    top10 = df.nlargest(10, "pipes")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["organ"].values[::-1], top10["pipes"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Number of Pipes")
    ax.set_title("Top 10 Pipe Organs by Size")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[45, 5], zoom=3)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['organ'])}</b><br>"
            f"<b>City:</b> {_esc(row['city'])}, {_esc(row['country'])}<br>"
            f"<b>Builder:</b> {_esc(row['builder'])}<br>"
            f"<b>Pipes:</b> {row['pipes']:,}<br>"
            f"<b>Year:</b> {_esc(row['year'])}<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(6, min(14, row["pipes"] / 3000)),
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=_esc(row["organ"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["organ", "city", "country", "builder", "pipes", "year", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "organ_church.csv", "text/csv",
                       key="dl_organ")


def _render_brass():
    """Map 8: Brass Instruments."""
    df = _get_brass_data()
    st.markdown("#### Brass Instruments")
    c1, c2, c3 = st.columns(3)
    c1.metric("Makers", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Makers")
    ax.set_title("Brass Instrument Makers by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[40, -20], zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:180px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['maker'])}</b><br>"
            f"<b>City:</b> {_esc(row['city'])}, {_esc(row['country'])}<br>"
            f"<b>Founded:</b> {_esc(row['founded'])}<br>"
            f"<b>Type:</b> {_esc(row['type'])}<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=_esc(row["maker"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["maker", "city", "country", "founded", "type", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "brass_instruments.csv", "text/csv",
                       key="dl_brass")


def _render_electronic():
    """Map 9: Electronic Music Instruments."""
    df = _get_electronic_data()
    st.markdown("#### Electronic Music Instruments")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Instruments", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())
    c4.metric("Earliest", int(df["year"].min()))

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Instruments")
    ax.set_title("Electronic Instruments by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[35, -30], zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['instrument'])}</b><br>"
            f"<b>Location:</b> {_esc(row['city'])}, {_esc(row['country'])}<br>"
            f"<b>Year:</b> {_esc(row['year'])}<br>"
            f"<b>Inventor:</b> {_esc(row['inventor'])}<br>"
            f"<b>Type:</b> {_esc(row['type'])}<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=_esc(row["instrument"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["instrument", "city", "country", "year", "inventor", "type", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "electronic_instruments.csv", "text/csv",
                       key="dl_electronic")


def _render_museums():
    """Map 10: Music Instrument Museums."""
    df = _get_museum_data()
    st.markdown("#### Music Instrument Museums")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Museums", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Items", f"{df['collection'].sum():,}")
    c4.metric("Largest Collection", f"{df['collection'].max():,}")

    top10 = df.nlargest(10, "collection")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["museum"].values[::-1], top10["collection"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Collection Size")
    ax.set_title("Top 10 Instrument Museums by Collection Size")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[30, 0], zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<div style='min-width:200px'>"
            f"<b style='color:{_esc(row['color'])}'>{_esc(row['museum'])}</b><br>"
            f"<b>City:</b> {_esc(row['city'])}, {_esc(row['country'])}<br>"
            f"<b>Founded:</b> {_esc(row['founded'])}<br>"
            f"<b>Collection:</b> {row['collection']:,} items<br>"
            f"<i>{_esc(row['note'])}</i>"
            f"</div>"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(6, min(14, row["collection"] / 1500)),
            color=row["color"],
            fill=True,
            fill_color=row["color"],
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=_esc(row["museum"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["museum", "city", "country", "founded", "collection", "note"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "instrument_museums.csv", "text/csv",
                       key="instm_dl_museums")


# =====================================================================
# MAP OPTIONS DISPATCH
# =====================================================================
MAP_OPTIONS = {
    "Piano & Keyboard Heritage": _render_piano,
    "Guitar Making Traditions": _render_guitar,
    "Violin & String Instruments": _render_violin,
    "Drums & Percussion Origins": _render_drums,
    "Wind Instruments": _render_wind,
    "Traditional World Instruments": _render_traditional,
    "Organ & Church Music": _render_organ,
    "Brass Instruments": _render_brass,
    "Electronic Music Instruments": _render_electronic,
    "Music Instrument Museums": _render_museums,
}


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_instrument_maps_tab():
    """Main entry point for the Musical Instruments Maps tab."""
    st.markdown(
        '<div class="tab-header pink">'
        '<h4>\U0001f3b8 Musical Instruments Maps</h4>'
        '<p>Origins, makers, and traditions of musical instruments worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    selected_map = st.selectbox(
        "Map Mode",
        list(MAP_OPTIONS.keys()),
        key="instrument_maps_select",
    )

    if st.button("Generate Map", key="instrument_maps_generate", type="primary"):
        with st.spinner("Building map..."):
            MAP_OPTIONS[selected_map]()
    else:
        st.info("Select a map mode above and click **Generate Map** to explore.")
