# -*- coding: utf-8 -*-
"""
TerraScout AI - Dance & Performing Arts Maps
=============================================

Explore dance traditions, ballet companies, and performing arts worldwide.
This module provides 10 curated map modes covering global dance culture from
classical ballet to street dance, from flamenco to festival carnivals.

Each mode contains 15-25 hand-curated locations with coordinates, style
classifications, founding dates, and descriptive notes.

Map Modes:
    1. Ballet Companies & Theaters
    2. Flamenco Origins
    3. Tango & Latin Dance
    4. Indian Classical Dance
    5. African Dance Traditions
    6. Traditional Asian Dance
    7. Ballroom & Swing
    8. Street Dance & Hip-Hop
    9. Irish & Celtic Dance
   10. Dance Festivals & Competitions
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
# Color palettes per mode — each mode gets a distinct accent color
# ---------------------------------------------------------------------------
MODE_COLORS = {
    "Ballet Companies & Theaters": "#e91e90",
    "Flamenco Origins": "#ff4500",
    "Tango & Latin Dance": "#ff1493",
    "Indian Classical Dance": "#ff9933",
    "African Dance Traditions": "#ffd700",
    "Traditional Asian Dance": "#00cec9",
    "Ballroom & Swing": "#a29bfe",
    "Street Dance & Hip-Hop": "#00ff88",
    "Irish & Celtic Dance": "#2ecc71",
    "Dance Festivals & Competitions": "#e84393",
}

# ---------------------------------------------------------------------------
# Icon emojis per mode — used in popups and headers
# ---------------------------------------------------------------------------
MODE_ICONS = {
    "Ballet Companies & Theaters": "\U0001fa70",
    "Flamenco Origins": "\U0001f339",
    "Tango & Latin Dance": "\U0001f339",
    "Indian Classical Dance": "\U0001fab7",
    "African Dance Traditions": "\U0001f941",
    "Traditional Asian Dance": "\U0001f3ad",
    "Ballroom & Swing": "\U0001f3a9",
    "Street Dance & Hip-Hop": "\U0001f3a4",
    "Irish & Celtic Dance": "\u2618\ufe0f",
    "Dance Festivals & Competitions": "\U0001f389",
}

# ---------------------------------------------------------------------------
# Descriptions per mode — shown as captions below the selector
# ---------------------------------------------------------------------------
MODE_DESCRIPTIONS = {
    "Ballet Companies & Theaters": (
        "Major ballet companies, opera houses, and classical dance institutions "
        "around the world. From the Bolshoi to the Royal Ballet, explore the "
        "grand tradition of classical and neoclassical ballet."
    ),
    "Flamenco Origins": (
        "The birthplaces, tablaos, and pe\u00f1as of flamenco across Andalusia "
        "and Spain. Discover where buler\u00eda, solea, and alegr\u00edas were born."
    ),
    "Tango & Latin Dance": (
        "Tango milongas, salsa clubs, cumbia scenes, samba schools, and Latin "
        "dance traditions across the Americas and Caribbean."
    ),
    "Indian Classical Dance": (
        "Bharatanatyam, Kathak, Odissi, Kathakali, Kuchipudi, Manipuri, and "
        "other classical and folk dance forms across the Indian subcontinent."
    ),
    "African Dance Traditions": (
        "Djembe drumming, gumboot dance, eskista, intore, kizomba, and "
        "traditional dances spanning the entire African continent."
    ),
    "Traditional Asian Dance": (
        "Balinese gamelan dances, Thai Khon, Japanese Kabuki and Noh, Chinese "
        "opera, Korean pansori, Sufi whirling, and more from across Asia."
    ),
    "Ballroom & Swing": (
        "Historic ballrooms, Lindy Hop origins, Viennese waltz capitals, "
        "competitive dancesport venues, and swing dance landmarks."
    ),
    "Street Dance & Hip-Hop": (
        "Breaking, popping, locking, krumping, K-pop choreography, voguing, "
        "and urban street dance scenes from the Bronx to Seoul."
    ),
    "Irish & Celtic Dance": (
        "Irish step dance, Scottish Highland, Breton fest-noz, Welsh clog "
        "dancing, and Celtic dance traditions from six Celtic nations."
    ),
    "Dance Festivals & Competitions": (
        "Major dance festivals, carnivals, and competitions from Rio Carnival "
        "and Notting Hill to contemporary dance biennales."
    ),
}


# ---------------------------------------------------------------------------
# Curated data functions — each returns a list of dicts
# ---------------------------------------------------------------------------

def _ballet_data():
    """Ballet Companies & Theaters worldwide (22 locations).

    Covers the most prestigious classical and contemporary ballet
    companies across Europe, the Americas, Asia, and Oceania.
    """
    return [
        {"name": "Bolshoi Theatre", "city": "Moscow", "country": "Russia",
         "lat": 55.7601, "lon": 37.6186, "style": "Classical Ballet",
         "founded": 1776,
         "notes": "One of the oldest and most prestigious ballet companies in the world, legendary for Swan Lake and Spartacus productions"},
        {"name": "Royal Ballet", "city": "London", "country": "UK",
         "lat": 51.5129, "lon": -0.1223, "style": "Classical Ballet",
         "founded": 1931,
         "notes": "Resident at the Royal Opera House, Covent Garden, founded by Ninette de Valois and Frederick Ashton"},
        {"name": "Paris Opera Ballet", "city": "Paris", "country": "France",
         "lat": 48.8720, "lon": 2.3316, "style": "Classical Ballet",
         "founded": 1669,
         "notes": "Oldest national ballet company in the world at Palais Garnier, birthplace of romantic ballet"},
        {"name": "New York City Ballet", "city": "New York", "country": "USA",
         "lat": 40.7725, "lon": -73.9835, "style": "Neoclassical Ballet",
         "founded": 1948,
         "notes": "Founded by George Balanchine and Lincoln Kirstein, revolutionized ballet with neoclassical style"},
        {"name": "Teatro alla Scala Ballet", "city": "Milan", "country": "Italy",
         "lat": 45.4675, "lon": 9.1895, "style": "Classical Ballet",
         "founded": 1778,
         "notes": "La Scala ballet academy is one of the finest in the world, training ground for Italian ballet stars"},
        {"name": "Mariinsky Ballet", "city": "St Petersburg", "country": "Russia",
         "lat": 59.9256, "lon": 30.2960, "style": "Classical Ballet",
         "founded": 1740,
         "notes": "Home of the Kirov Ballet, premiered Swan Lake, Nutcracker, and Sleeping Beauty under Petipa"},
        {"name": "American Ballet Theatre", "city": "New York", "country": "USA",
         "lat": 40.7614, "lon": -73.9776, "style": "Classical/Contemporary",
         "founded": 1940,
         "notes": "One of the great ballet companies, based at Lincoln Center, known for diverse repertoire"},
        {"name": "Royal Danish Ballet", "city": "Copenhagen", "country": "Denmark",
         "lat": 55.6793, "lon": 12.5859, "style": "Bournonville Style",
         "founded": 1748,
         "notes": "Third oldest ballet company, keepers of the Bournonville tradition of light jumps and epaulement"},
        {"name": "Stuttgart Ballet", "city": "Stuttgart", "country": "Germany",
         "lat": 48.7786, "lon": 9.1799, "style": "Narrative Ballet",
         "founded": 1609,
         "notes": "Famed for dramatic narrative ballets under John Cranko, one of Europe's leading companies"},
        {"name": "Dutch National Ballet", "city": "Amsterdam", "country": "Netherlands",
         "lat": 52.3602, "lon": 4.9209, "style": "Classical/Contemporary",
         "founded": 1961,
         "notes": "Based at Dutch National Opera & Ballet building (Stopera), versatile repertoire"},
        {"name": "National Ballet of Canada", "city": "Toronto", "country": "Canada",
         "lat": 43.6465, "lon": -79.3876, "style": "Classical Ballet",
         "founded": 1951,
         "notes": "One of the premier ballet companies in North America, based at Four Seasons Centre"},
        {"name": "San Francisco Ballet", "city": "San Francisco", "country": "USA",
         "lat": 37.7782, "lon": -122.4195, "style": "Classical/Contemporary",
         "founded": 1933,
         "notes": "Oldest professional ballet company in the United States, pioneer of American ballet"},
        {"name": "The Australian Ballet", "city": "Melbourne", "country": "Australia",
         "lat": -37.8214, "lon": 144.9688, "style": "Classical/Contemporary",
         "founded": 1962,
         "notes": "National ballet company of Australia, based at Arts Centre Melbourne, tours extensively"},
        {"name": "Royal Swedish Ballet", "city": "Stockholm", "country": "Sweden",
         "lat": 59.3302, "lon": 18.0704, "style": "Classical Ballet",
         "founded": 1773,
         "notes": "Based at the Royal Swedish Opera, one of Europe's oldest companies with rich tradition"},
        {"name": "National Ballet of China", "city": "Beijing", "country": "China",
         "lat": 39.9042, "lon": 116.4074, "style": "Classical/Chinese",
         "founded": 1959,
         "notes": "Famous for Red Detachment of Women and blending Chinese themes with classical technique"},
        {"name": "Cuban National Ballet", "city": "Havana", "country": "Cuba",
         "lat": 23.1365, "lon": -82.3816, "style": "Cuban Ballet School",
         "founded": 1948,
         "notes": "Founded by Alicia Alonso, developed unique Cuban ballet technique combining athleticism and artistry"},
        {"name": "Bavarian State Ballet", "city": "Munich", "country": "Germany",
         "lat": 48.1394, "lon": 11.5786, "style": "Classical/Contemporary",
         "founded": 1653,
         "notes": "Based at the Nationaltheater, one of Europe's leading ballet companies with long history"},
        {"name": "Hamburg Ballet", "city": "Hamburg", "country": "Germany",
         "lat": 53.5565, "lon": 9.9880, "style": "Narrative Ballet",
         "founded": 1661,
         "notes": "Led by John Neumeier since 1973, master of narrative ballet and full-evening works"},
        {"name": "Vienna State Ballet", "city": "Vienna", "country": "Austria",
         "lat": 48.2034, "lon": 16.3695, "style": "Classical Ballet",
         "founded": 1626,
         "notes": "Based at the Vienna State Opera, rich Viennese ballet tradition dating to the Habsburg era"},
        {"name": "Tokyo Ballet", "city": "Tokyo", "country": "Japan",
         "lat": 35.6762, "lon": 139.6503, "style": "Classical Ballet",
         "founded": 1964,
         "notes": "Japan's foremost classical ballet company, frequent world tours, collaborates with B\u00e9jart"},
        {"name": "English National Ballet", "city": "London", "country": "UK",
         "lat": 51.5093, "lon": -0.0760, "style": "Classical Ballet",
         "founded": 1950,
         "notes": "Based at London City Island, tours extensively across the UK bringing ballet to wide audiences"},
        {"name": "Mikhailovsky Ballet", "city": "St Petersburg", "country": "Russia",
         "lat": 59.9369, "lon": 30.3281, "style": "Classical Ballet",
         "founded": 1833,
         "notes": "Historic company at the Mikhailovsky Theatre on Arts Square, rival to the Mariinsky"},
    ]


def _flamenco_data():
    """Flamenco Origins and venues across Spain (17 locations).

    Covers the traditional heartlands of flamenco in Andalusia as well
    as major tablaos in Madrid and Barcelona.
    """
    return [
        {"name": "Triana Quarter", "city": "Seville", "country": "Spain",
         "lat": 37.3828, "lon": -6.0034, "style": "Seville flamenco",
         "founded": "16th century",
         "notes": "Historic birthplace of Seville-style flamenco, cradle of great artists and the seguiriya form"},
        {"name": "Santiago Quarter", "city": "Jerez de la Frontera", "country": "Spain",
         "lat": 36.6850, "lon": -6.1372, "style": "Jerez buler\u00eda",
         "founded": "18th century",
         "notes": "Heartland of buler\u00eda rhythm and Romani flamenco families like the Sorderas and Ag\u00fcjetas"},
        {"name": "Santa Mar\u00eda Quarter", "city": "C\u00e1diz", "country": "Spain",
         "lat": 36.5350, "lon": -6.2993, "style": "Alegr\u00edas",
         "founded": "18th century",
         "notes": "Origin of alegr\u00edas, one of the most joyful flamenco forms, influenced by the sea"},
        {"name": "Sacromonte Caves", "city": "Granada", "country": "Spain",
         "lat": 37.1813, "lon": -3.5880, "style": "Zambra",
         "founded": "15th century",
         "notes": "Famous cave performances by Gitano communities, zambra flamenca in whitewashed caves"},
        {"name": "Corral de la Moreria", "city": "Madrid", "country": "Spain",
         "lat": 40.4130, "lon": -3.7138, "style": "Tablao flamenco",
         "founded": 1956,
         "notes": "World-famous tablao rated best flamenco venue in the world, every major artist has performed here"},
        {"name": "Tablao Flamenco Cordobes", "city": "Barcelona", "country": "Spain",
         "lat": 41.3804, "lon": 2.1724, "style": "Tablao flamenco",
         "founded": 1970,
         "notes": "Premier flamenco tablao on La Rambla, nightly high-quality performances for decades"},
        {"name": "Pe\u00f1a Flamenca Torres Macarena", "city": "Seville", "country": "Spain",
         "lat": 37.4000, "lon": -5.9870, "style": "Pe\u00f1a flamenco",
         "founded": "1960s",
         "notes": "Authentic pe\u00f1a flamenca gathering for purist flamenco aficionados and local artists"},
        {"name": "Centro Andaluz de Flamenco", "city": "Jerez de la Frontera", "country": "Spain",
         "lat": 36.6868, "lon": -6.1378, "style": "Archive/Museum",
         "founded": 1993,
         "notes": "Official center for flamenco research, preservation, and documentation by the Junta de Andaluc\u00eda"},
        {"name": "Barrio de la Vi\u00f1a", "city": "C\u00e1diz", "country": "Spain",
         "lat": 36.5275, "lon": -6.3010, "style": "Tangos de C\u00e1diz",
         "founded": "19th century",
         "notes": "Neighborhood famous for tangos de C\u00e1diz, carnival chirigotas, and coastal flamenco flavor"},
        {"name": "Museo del Baile Flamenco", "city": "Seville", "country": "Spain",
         "lat": 37.3912, "lon": -5.9927, "style": "Museum/Performance",
         "founded": 2006,
         "notes": "Founded by dancer Cristina Hoyos, interactive museum and nightly live performance venue"},
        {"name": "Pe\u00f1a La Plateria", "city": "Granada", "country": "Spain",
         "lat": 37.1760, "lon": -3.5986, "style": "Pe\u00f1a flamenco",
         "founded": 1949,
         "notes": "One of the oldest pe\u00f1as flamencas in Spain, intimate setting in the Albaicin quarter"},
        {"name": "Casa Patas", "city": "Madrid", "country": "Spain",
         "lat": 40.4126, "lon": -3.7010, "style": "Tablao flamenco",
         "founded": 1985,
         "notes": "Legendary Madrid tablao and flamenco cultural center, closed 2020 but iconic legacy remains"},
        {"name": "Bienal de Flamenco", "city": "Seville", "country": "Spain",
         "lat": 37.3886, "lon": -5.9953, "style": "Festival",
         "founded": 1980,
         "notes": "Biennial international flamenco festival, the world's largest and most prestigious flamenco event"},
        {"name": "Ronda Flamenco Heritage", "city": "Ronda", "country": "Spain",
         "lat": 36.7462, "lon": -5.1613, "style": "Rural flamenco",
         "founded": "19th century",
         "notes": "Mountain town with deep flamenco roots, bullfighting tradition intertwined with dance"},
        {"name": "M\u00e1laga Verdiales", "city": "M\u00e1laga", "country": "Spain",
         "lat": 36.7213, "lon": -4.4214, "style": "Verdiales/Malague\u00f1a",
         "founded": "18th century",
         "notes": "Origin of malague\u00f1a and verdiales folk traditions, Moorish-influenced coastal flamenco"},
        {"name": "Moreria Quarter", "city": "C\u00f3rdoba", "country": "Spain",
         "lat": 37.8796, "lon": -4.7794, "style": "C\u00f3rdoba flamenco",
         "founded": "17th century",
         "notes": "Historic quarter with intimate flamenco venues near the Mezquita and Roman bridge"},
        {"name": "Utrera Solea Heartland", "city": "Utrera", "country": "Spain",
         "lat": 37.1857, "lon": -5.7817, "style": "Solear/Buler\u00eda",
         "founded": "18th century",
         "notes": "Small town that produced legendary flamenco artists like Fernanda and Bernarda de Utrera"},
    ]


def _tango_latin_data():
    """Tango & Latin Dance destinations across the Americas (21 locations).

    From Buenos Aires milongas to Havana salsa clubs, Cali's salsa
    capital to Kingston's dancehall, plus samba, cumbia, and more.
    """
    return [
        {"name": "La Boca / Caminito", "city": "Buenos Aires", "country": "Argentina",
         "lat": -34.6345, "lon": -58.3631, "style": "Tango",
         "founded": "1880s",
         "notes": "Birthplace of tango in the colorful port barrio, street tango performances daily on Caminito"},
        {"name": "Salon Canning", "city": "Buenos Aires", "country": "Argentina",
         "lat": -34.5903, "lon": -58.4265, "style": "Milonga",
         "founded": "1920s",
         "notes": "One of the most famous milongas in Buenos Aires for traditional tango, Parakultural nights"},
        {"name": "Confiteria Ideal", "city": "Buenos Aires", "country": "Argentina",
         "lat": -34.6040, "lon": -58.3815, "style": "Milonga",
         "founded": 1912,
         "notes": "Historic grand salon milonga in a stunning belle \u00e9poque building, featured in tango films"},
        {"name": "San Telmo Quarter", "city": "Buenos Aires", "country": "Argentina",
         "lat": -34.6210, "lon": -58.3700, "style": "Tango",
         "founded": "1890s",
         "notes": "Historic neighborhood with tango on every corner, Sunday antique market with live music"},
        {"name": "Joventango", "city": "Montevideo", "country": "Uruguay",
         "lat": -34.9011, "lon": -56.1645, "style": "Uruguayan Tango",
         "founded": "1910s",
         "notes": "Uruguay claims co-creation of tango with Argentina; vibrant milonga scene in Montevideo"},
        {"name": "Tropicana Club", "city": "Havana", "country": "Cuba",
         "lat": 23.0998, "lon": -82.4300, "style": "Salsa/Cabaret",
         "founded": 1939,
         "notes": "Iconic open-air cabaret under the stars, legendary salsa and Cuban dance spectacles"},
        {"name": "Casa de la M\u00fasica", "city": "Havana", "country": "Cuba",
         "lat": 23.1400, "lon": -82.3590, "style": "Salsa/Son",
         "founded": "1990s",
         "notes": "Live son cubano and timba venue, birthplace of modern Cuban dance music and casino rueda"},
        {"name": "Cali Salsa Capital", "city": "Cali", "country": "Colombia",
         "lat": 3.4516, "lon": -76.5320, "style": "Cali-style Salsa",
         "founded": "1970s",
         "notes": "World capital of salsa with unique fast-footwork Cali style, annual Feria de Cali"},
        {"name": "Santo Domingo Merengue", "city": "Santo Domingo", "country": "Dominican Republic",
         "lat": 18.4861, "lon": -69.9312, "style": "Merengue",
         "founded": "1850s",
         "notes": "Birthplace of merengue, national dance of the Dominican Republic, Festival del Merengue"},
        {"name": "Bogot\u00e1 Cumbia Scene", "city": "Bogot\u00e1", "country": "Colombia",
         "lat": 4.7110, "lon": -74.0721, "style": "Cumbia",
         "founded": "1940s",
         "notes": "Urban center for Colombian cumbia and champeta dance clubs, vibrant nightlife district"},
        {"name": "San Juan Bomba y Plena", "city": "San Juan", "country": "Puerto Rico",
         "lat": 18.4655, "lon": -66.1057, "style": "Bomba/Plena/Reggaeton",
         "founded": "17th century",
         "notes": "Afro-Puerto Rican bomba and plena traditions at Loiza, plus birthplace of reggaeton"},
        {"name": "Barranquilla Cumbia Origins", "city": "Barranquilla", "country": "Colombia",
         "lat": 10.9685, "lon": -74.7813, "style": "Cumbia",
         "founded": "19th century",
         "notes": "Coastal city where cumbia originated from African, indigenous, and Spanish roots, UNESCO carnival"},
        {"name": "Rio Samba Scene", "city": "Rio de Janeiro", "country": "Brazil",
         "lat": -22.9068, "lon": -43.1729, "style": "Samba",
         "founded": "1920s",
         "notes": "Heart of samba, escolas de samba and year-round samba dance culture in Lapa district"},
        {"name": "Salvador Afro-Brazilian Dance", "city": "Salvador", "country": "Brazil",
         "lat": -12.9714, "lon": -38.5124, "style": "Samba de Roda/Ax\u00e9",
         "founded": "17th century",
         "notes": "Afro-Brazilian dance capital, samba de roda, capoeira, and ax\u00e9 music origins in Pelourinho"},
        {"name": "Medell\u00edn Tango District", "city": "Medell\u00edn", "country": "Colombia",
         "lat": 6.2442, "lon": -75.5812, "style": "Tango",
         "founded": "1920s",
         "notes": "Surprising tango culture due to Carlos Gardel's fatal crash here, annual tango festival in Manrique"},
        {"name": "Lima Marinera", "city": "Lima", "country": "Peru",
         "lat": -12.0464, "lon": -77.0428, "style": "Marinera",
         "founded": "19th century",
         "notes": "Marinera is Peru's elegant national dance, annual contests in Trujillo draw thousands"},
        {"name": "Santiago Cueca", "city": "Santiago", "country": "Chile",
         "lat": -33.4489, "lon": -70.6693, "style": "Cueca",
         "founded": "19th century",
         "notes": "National dance of Chile, handkerchief courtship dance performed at Fiestas Patrias"},
        {"name": "Caracas Joropo", "city": "Caracas", "country": "Venezuela",
         "lat": 10.4806, "lon": -66.9036, "style": "Joropo",
         "founded": "18th century",
         "notes": "Joropo is the national dance of Venezuela, energetic couples dance with harp and maracas"},
        {"name": "Mexico City Ballet Folkl\u00f3rico", "city": "Mexico City", "country": "Mexico",
         "lat": 19.4326, "lon": -99.1332, "style": "Son/Folkl\u00f3rico",
         "founded": "Colonial era",
         "notes": "Ballet Folkl\u00f3rico de Mexico at Palacio de Bellas Artes, son jarocho and jarabe tape\u00f1o"},
        {"name": "Kingston Dancehall", "city": "Kingston", "country": "Jamaica",
         "lat": 18.0179, "lon": -76.8099, "style": "Dancehall/Ska",
         "founded": "1970s",
         "notes": "Global birthplace of dancehall culture, sound system parties and viral dance moves"},
        {"name": "Port-au-Prince Kompa", "city": "Port-au-Prince", "country": "Haiti",
         "lat": 18.5944, "lon": -72.3074, "style": "Kompa/Vodou Dance",
         "founded": "1950s",
         "notes": "Kompa music and partner dance tradition, influenced by African vodou ceremonial rituals"},
    ]


def _indian_classical_data():
    """Indian Classical Dance forms and centers (21 locations).

    Spans the eight recognized classical forms plus major folk traditions
    and teaching institutions across India.
    """
    return [
        {"name": "Bharatanatyam - Thanjavur Temple", "city": "Thanjavur", "country": "India",
         "lat": 10.7870, "lon": 79.1378, "style": "Bharatanatyam",
         "founded": "2000+ years",
         "notes": "Temple town origin of Bharatanatyam, Brihadeeswara Temple devadasi tradition and Tanjore Quartet"},
        {"name": "Bharatanatyam - Chennai Hub", "city": "Chennai", "country": "India",
         "lat": 13.0827, "lon": 80.2707, "style": "Bharatanatyam",
         "founded": "20th century revival",
         "notes": "Modern center for Bharatanatyam revival, December Margazhi season draws thousands of dancers"},
        {"name": "Kathak - Lucknow Gharana", "city": "Lucknow", "country": "India",
         "lat": 26.8467, "lon": 80.9462, "style": "Kathak (Lucknow Gharana)",
         "founded": "Mughal era",
         "notes": "Lucknow gharana emphasizes grace, expressiveness, and nazakat under Nawabi patronage"},
        {"name": "Kathak - Jaipur Gharana", "city": "Jaipur", "country": "India",
         "lat": 26.9124, "lon": 75.7873, "style": "Kathak (Jaipur Gharana)",
         "founded": "Mughal era",
         "notes": "Jaipur gharana known for vigorous footwork, pirouettes, and tatkar rhythmic patterns"},
        {"name": "Odissi - Bhubaneswar Temples", "city": "Bhubaneswar", "country": "India",
         "lat": 20.2961, "lon": 85.8245, "style": "Odissi",
         "founded": "2nd century BCE",
         "notes": "Ancient temple dance of Odisha, tribhanga sculptural poses inspired by Konark Sun Temple"},
        {"name": "Kathakali - Thrissur", "city": "Thrissur", "country": "India",
         "lat": 10.5276, "lon": 76.2144, "style": "Kathakali",
         "founded": "17th century",
         "notes": "Kerala's dramatic dance-theater with elaborate chutty makeup and towering kireedam crowns"},
        {"name": "Kathakali - Kochi Kerala", "city": "Kochi", "country": "India",
         "lat": 9.9312, "lon": 76.2673, "style": "Kathakali",
         "founded": "17th century",
         "notes": "Major Kathakali performance center, Kerala Kalamandalam graduates perform nightly"},
        {"name": "Manipuri - Imphal Ras Lila", "city": "Imphal", "country": "India",
         "lat": 24.8170, "lon": 93.9368, "style": "Manipuri",
         "founded": "Ancient",
         "notes": "Lyrical Ras Lila dance from Manipur, devotional and graceful with distinctive white costumes"},
        {"name": "Kuchipudi - Origin Village", "city": "Kuchipudi", "country": "India",
         "lat": 16.2620, "lon": 80.9220, "style": "Kuchipudi",
         "founded": "3rd century BCE",
         "notes": "Origin village of Kuchipudi dance-drama in Andhra Pradesh, all-male tradition turned inclusive"},
        {"name": "Mohiniyattam - Thiruvananthapuram", "city": "Thiruvananthapuram", "country": "India",
         "lat": 8.5241, "lon": 76.9366, "style": "Mohiniyattam",
         "founded": "16th century",
         "notes": "Graceful feminine dance of Kerala, enchanting swaying movements like palm trees in the wind"},
        {"name": "Sattriya - Majuli Island", "city": "Majuli", "country": "India",
         "lat": 26.9500, "lon": 94.1700, "style": "Sattriya",
         "founded": "15th century",
         "notes": "Assamese classical dance from the world's largest river island, monastery (sattra) tradition"},
        {"name": "Chhau - Purulia Masks", "city": "Purulia", "country": "India",
         "lat": 23.3320, "lon": 86.3650, "style": "Chhau (Purulia)",
         "founded": "Ancient",
         "notes": "Masked martial dance form from West Bengal tribal traditions, vigorous and acrobatic"},
        {"name": "Chhau - Seraikela Style", "city": "Seraikela", "country": "India",
         "lat": 22.6100, "lon": 85.8200, "style": "Chhau (Seraikela)",
         "founded": "Ancient",
         "notes": "Jharkhand masked dance form, more lyrical and refined than Purulia style"},
        {"name": "Bharatanatyam - Chidambaram", "city": "Chidambaram", "country": "India",
         "lat": 11.3992, "lon": 79.6912, "style": "Bharatanatyam",
         "founded": "2000+ years",
         "notes": "Nataraja temple with cosmic dance of Shiva sculpture, 108 karanas carved in stone"},
        {"name": "Kathak - Varanasi Gharana", "city": "Varanasi", "country": "India",
         "lat": 25.3176, "lon": 83.0064, "style": "Kathak (Banaras Gharana)",
         "founded": "Ancient",
         "notes": "Banaras gharana known for powerful expressions, tabla-driven rhythms, and temple tradition"},
        {"name": "Yakshagana - Udupi Coast", "city": "Udupi", "country": "India",
         "lat": 13.3409, "lon": 74.7421, "style": "Yakshagana",
         "founded": "16th century",
         "notes": "Karnataka's vibrant all-night dance-drama tradition with elaborate costumes and headgear"},
        {"name": "Bihu Dance - Guwahati", "city": "Guwahati", "country": "India",
         "lat": 26.1445, "lon": 91.7362, "style": "Bihu",
         "founded": "Ancient",
         "notes": "Assamese folk dance celebrating Rongali Bihu spring harvest with joyful movements"},
        {"name": "Bhangra - Amritsar Punjab", "city": "Amritsar", "country": "India",
         "lat": 31.6340, "lon": 74.8723, "style": "Bhangra",
         "founded": "14th century",
         "notes": "High-energy Punjabi harvest dance, globally influential through diaspora and music fusion"},
        {"name": "Garba/Dandiya - Ahmedabad", "city": "Ahmedabad", "country": "India",
         "lat": 23.0225, "lon": 72.5714, "style": "Garba/Dandiya Raas",
         "founded": "Ancient",
         "notes": "Gujarati circle dances performed during nine nights of Navratri with decorated sticks"},
        {"name": "Lavani - Pune Maharashtra", "city": "Pune", "country": "India",
         "lat": 18.5204, "lon": 73.8567, "style": "Lavani",
         "founded": "18th century",
         "notes": "Energetic Maharashtrian folk dance with powerful feminine expression and dholki beats"},
        {"name": "Kalakshetra Foundation", "city": "Chennai", "country": "India",
         "lat": 12.9911, "lon": 80.2490, "style": "Bharatanatyam/Multi",
         "founded": 1936,
         "notes": "Premier institution for Indian classical dance founded by Rukmini Devi Arundale on the beach"},
    ]


def _african_dance_data():
    """African Dance Traditions spanning the continent (20 locations).

    From West African djembe to South African gumboot, Ethiopian eskista
    to Angolan kizomba, covering dance traditions across all regions.
    """
    return [
        {"name": "Djembe Drumming Heartland", "city": "Conakry", "country": "Guinea",
         "lat": 9.6412, "lon": -13.5784, "style": "Djembe/West African",
         "founded": "Ancient",
         "notes": "Guinea is the heartland of djembe drumming and West African dance, Les Ballets Africains founded here"},
        {"name": "Sabar Dance Arena", "city": "Dakar", "country": "Senegal",
         "lat": 14.7167, "lon": -17.4677, "style": "Sabar",
         "founded": "Ancient",
         "notes": "Wolof sabar drumming and acrobatic dance tradition, communal sabar events fill neighborhoods"},
        {"name": "Dununba Dance Center", "city": "Bamako", "country": "Mali",
         "lat": 12.6392, "lon": -8.0029, "style": "Dununba/Mandinka",
         "founded": "Ancient",
         "notes": "Mandinka dance traditions, griot storytelling through movement, Festival sur le Niger"},
        {"name": "Azonto & Adowa Scene", "city": "Accra", "country": "Ghana",
         "lat": 5.6037, "lon": -0.1870, "style": "Azonto/Adowa",
         "founded": "Traditional/2010s",
         "notes": "Modern azonto dance craze originated here alongside traditional Akan adowa funeral dance"},
        {"name": "Afrobeat & Bata Drum", "city": "Lagos", "country": "Nigeria",
         "lat": 6.5244, "lon": 3.3792, "style": "Afrobeat/Bata",
         "founded": "1970s/Ancient",
         "notes": "Fela Kuti's New Afrika Shrine for afrobeat dance and ancient Yoruba bata drumming traditions"},
        {"name": "Gumboot Dance Mines", "city": "Johannesburg", "country": "South Africa",
         "lat": -26.2041, "lon": 28.0473, "style": "Gumboot/Pantsula",
         "founded": "1890s",
         "notes": "Gold mine workers' boot-slapping communication dance, evolved into performance art form"},
        {"name": "Zulu Indlamu Warriors", "city": "Durban", "country": "South Africa",
         "lat": -29.8587, "lon": 31.0218, "style": "Indlamu/Zulu",
         "founded": "Ancient",
         "notes": "Powerful Zulu warrior dance with high kicks and stomping, performed at ceremonies and festivals"},
        {"name": "Eskista Shoulder Dance", "city": "Addis Ababa", "country": "Ethiopia",
         "lat": 9.0250, "lon": 38.7469, "style": "Eskista",
         "founded": "Ancient",
         "notes": "Mesmerizing shoulder-shaking Ethiopian dance, each region has its own variation"},
        {"name": "Intore Warrior Dance", "city": "Kigali", "country": "Rwanda",
         "lat": -1.9403, "lon": 29.8739, "style": "Intore",
         "founded": "Ancient",
         "notes": "Elegant Rwandan warrior dance of strength, grace, and leaping, performed for royalty"},
        {"name": "Ngoma Drum Dance", "city": "Dar es Salaam", "country": "Tanzania",
         "lat": -6.7924, "lon": 39.2083, "style": "Ngoma",
         "founded": "Ancient",
         "notes": "Pan-East African drum and dance tradition, ngoma means both drum and dance in Swahili"},
        {"name": "Agbadza Ewe Dance", "city": "Ho", "country": "Ghana",
         "lat": 6.6009, "lon": 0.4719, "style": "Agbadza/Ewe",
         "founded": "Ancient",
         "notes": "Ewe people's social dance, originally a war dance transformed into celebration dance"},
        {"name": "Maasai Adumu Jumping", "city": "Nairobi", "country": "Kenya",
         "lat": -1.2921, "lon": 36.8219, "style": "Adumu/Maasai",
         "founded": "Ancient",
         "notes": "Famous competitive jumping dance of Maasai morani warriors, higher jumps bring prestige"},
        {"name": "Kizomba & Semba Origins", "city": "Luanda", "country": "Angola",
         "lat": -8.8390, "lon": 13.2894, "style": "Kizomba/Semba",
         "founded": "1980s",
         "notes": "Birthplace of kizomba and semba partner dance, now a global social dance phenomenon"},
        {"name": "Mapiko Masked Dance", "city": "Maputo", "country": "Mozambique",
         "lat": -25.9692, "lon": 32.5732, "style": "Mapiko/Makonde",
         "founded": "Ancient",
         "notes": "Makonde masked dance tradition from northern Mozambique, male initiation ceremonies"},
        {"name": "Cape Malay Riel Dance", "city": "Cape Town", "country": "South Africa",
         "lat": -33.9249, "lon": 18.4241, "style": "Cape Malay/Riel",
         "founded": "18th century",
         "notes": "Bo-Kaap community dance traditions and energetic riel dance from the Cape Coloured community"},
        {"name": "Tuareg Tende Dance", "city": "Timbuktu", "country": "Mali",
         "lat": 16.7666, "lon": -3.0026, "style": "Tuareg/Tende",
         "founded": "Ancient",
         "notes": "Desert nomad dance traditions with tende mortar drum, women lead the singing and dancing"},
        {"name": "Coup\u00e9-D\u00e9cal\u00e9 Scene", "city": "Abidjan", "country": "Ivory Coast",
         "lat": 5.3600, "lon": -4.0083, "style": "Coup\u00e9-D\u00e9cal\u00e9/Zouglou",
         "founded": "2000s",
         "notes": "Modern Ivorian dance craze, energetic and celebratory, invented by Douk Saga"},
        {"name": "Gnawa Trance Dance", "city": "Essaouira", "country": "Morocco",
         "lat": 31.5085, "lon": -9.7595, "style": "Gnawa",
         "founded": "Ancient",
         "notes": "Sub-Saharan-Moroccan trance healing dance and music ritual, annual Gnaoua Festival"},
        {"name": "Venda Domba Python Dance", "city": "Thohoyandou", "country": "South Africa",
         "lat": -23.0000, "lon": 30.3833, "style": "Tshikona/Domba",
         "founded": "Ancient",
         "notes": "Venda python dance (domba) female initiation ceremony, undulating serpentine movements"},
        {"name": "Bwola Royal Dance", "city": "Gulu", "country": "Uganda",
         "lat": 2.7746, "lon": 32.2990, "style": "Bwola/Acholi",
         "founded": "Ancient",
         "notes": "Royal Acholi dance performed by chiefs and elders, stately circular movements with drums"},
    ]


def _asian_dance_data():
    """Traditional Asian Dance forms across the continent (21 locations).

    From Southeast Asian court dances to East Asian opera traditions,
    Central Asian Sufi whirling, and South Asian island dance forms.
    """
    return [
        {"name": "Balinese Legong & Barong", "city": "Ubud", "country": "Indonesia",
         "lat": -8.5069, "lon": 115.2625, "style": "Legong/Barong",
         "founded": "Ancient",
         "notes": "Sacred Balinese temple dances with gamelan orchestra, nightly performances at Ubud Palace"},
        {"name": "Thai Classical Khon", "city": "Bangkok", "country": "Thailand",
         "lat": 13.7563, "lon": 100.5018, "style": "Khon/Lakhon",
         "founded": "15th century",
         "notes": "Masked dance-drama of the Ramakien (Thai Ramayana), UNESCO intangible heritage since 2018"},
        {"name": "Kabuki-za Theatre", "city": "Tokyo", "country": "Japan",
         "lat": 35.6695, "lon": 139.7648, "style": "Kabuki",
         "founded": 1603,
         "notes": "Kabuki-za Theatre in Ginza, elaborate dance-drama with onnagata female impersonation tradition"},
        {"name": "Noh Theater - Kanze School", "city": "Kyoto", "country": "Japan",
         "lat": 35.0116, "lon": 135.7681, "style": "Noh/Nohgaku",
         "founded": "14th century",
         "notes": "Refined masked dance-theater by Zeami, slow meditative movements, UNESCO heritage since 2008"},
        {"name": "Beijing Opera National Centre", "city": "Beijing", "country": "China",
         "lat": 39.9042, "lon": 116.4074, "style": "Jingju/Beijing Opera",
         "founded": 1790,
         "notes": "Combining music, singing, mime, martial arts dance, and acrobatics in elaborate costumes"},
        {"name": "Korean Pansori & Talchum", "city": "Jeonju", "country": "South Korea",
         "lat": 35.8242, "lon": 127.1480, "style": "Pansori/Talchum",
         "founded": "17th century",
         "notes": "Traditional narrative singing and satirical mask dance (talchum), UNESCO intangible heritage"},
        {"name": "Apsara Royal Ballet", "city": "Siem Reap", "country": "Cambodia",
         "lat": 13.3671, "lon": 103.8448, "style": "Apsara/Royal Ballet",
         "founded": "Ancient Khmer",
         "notes": "Royal Cambodian ballet inspired by celestial dancer carvings at Angkor Wat temple complex"},
        {"name": "Thang Long Water Puppets", "city": "Hanoi", "country": "Vietnam",
         "lat": 21.0285, "lon": 105.8542, "style": "M\u00faa r\u1ed1i n\u01b0\u1edbc",
         "founded": "11th century",
         "notes": "Water puppet theater unique to Vietnam, puppeteers stand waist-deep controlling figures"},
        {"name": "Gion Geisha Dance", "city": "Kyoto", "country": "Japan",
         "lat": 35.0031, "lon": 135.7736, "style": "Nihon buy\u014d",
         "founded": "17th century",
         "notes": "Gion district geisha performing traditional Japanese dance at Miyako Odori spring festival"},
        {"name": "Sichuan Opera Face-Changing", "city": "Chengdu", "country": "China",
         "lat": 30.5728, "lon": 104.0668, "style": "Sichuan Opera",
         "founded": "Qing Dynasty",
         "notes": "Famous bian lian (face-changing) technique where masks change in a split second"},
        {"name": "Javanese Court Bedhaya", "city": "Yogyakarta", "country": "Indonesia",
         "lat": -7.7972, "lon": 110.3688, "style": "Bedhaya/Srimpi",
         "founded": "8th century",
         "notes": "Refined Javanese court dances at Sultan's Kraton Palace, nine sacred bedhaya dancers"},
        {"name": "Philippine Tinikling", "city": "Manila", "country": "Philippines",
         "lat": 14.5995, "lon": 120.9842, "style": "Tinikling",
         "founded": "Spanish era",
         "notes": "National folk dance mimicking tikling birds stepping between bamboo poles rhythmically"},
        {"name": "Burmese Classical Yama", "city": "Mandalay", "country": "Myanmar",
         "lat": 21.9588, "lon": 96.0891, "style": "Yama Zatdaw",
         "founded": "Ancient",
         "notes": "Classical Burmese dance-drama, marionette-inspired fluid movements and finger extensions"},
        {"name": "Lao Lam Vong Circle Dance", "city": "Vientiane", "country": "Laos",
         "lat": 17.9757, "lon": 102.6331, "style": "Lam Vong",
         "founded": "Traditional",
         "notes": "Lao national circle dance, partners orbit each other with graceful curving hand movements"},
        {"name": "Mongolian Tsam Mask Dance", "city": "Ulaanbaatar", "country": "Mongolia",
         "lat": 47.8864, "lon": 106.9057, "style": "Tsam/Buddhist",
         "founded": "Buddhist era",
         "notes": "Masked ritual dance of Tibetan Buddhist origin, elaborate deity costumes in monasteries"},
        {"name": "Mevlevi Sufi Whirling", "city": "Konya", "country": "Turkey",
         "lat": 37.8746, "lon": 32.4932, "style": "Sema/Whirling",
         "founded": "13th century",
         "notes": "Mevlevi dervish sema ceremony founded by followers of Rumi, spiritual spinning dance"},
        {"name": "Kandyan Ves Dance", "city": "Kandy", "country": "Sri Lanka",
         "lat": 7.2906, "lon": 80.6337, "style": "Ves/Kandyan",
         "founded": "Ancient",
         "notes": "Sri Lankan classical dance with silver headdress, traditionally performed for temple rituals"},
        {"name": "Bhutanese Cham Festival", "city": "Thimphu", "country": "Bhutan",
         "lat": 27.4728, "lon": 89.6390, "style": "Cham/Buddhist",
         "founded": "8th century",
         "notes": "Sacred Buddhist mask dances at tshechu festivals, believed to bestow blessings on viewers"},
        {"name": "Dunhuang Ribbon Dance", "city": "Xi'an", "country": "China",
         "lat": 34.3416, "lon": 108.9398, "style": "Ribbon Dance/Dunhuang",
         "founded": "Han Dynasty",
         "notes": "Ancient silk ribbon dancing tradition inspired by flying apsara murals in Dunhuang caves"},
        {"name": "Khon Mask Workshop", "city": "Nakhon Pathom", "country": "Thailand",
         "lat": 13.8195, "lon": 100.0621, "style": "Khon",
         "founded": "15th century",
         "notes": "Traditional Khon mask crafting center near Bangkok, artisans preserve this dying art"},
        {"name": "Okinawan Eisa Festival", "city": "Okinawa", "country": "Japan",
         "lat": 26.3344, "lon": 127.8056, "style": "Eisa",
         "founded": "Edo period",
         "notes": "Bon festival drum dance unique to Okinawa, energetic group performance with taiko drums"},
    ]


def _ballroom_swing_data():
    """Ballroom & Swing Dance landmarks and venues (16 locations).

    From the grandeur of Blackpool Tower to the birth of Lindy Hop
    in Harlem, the Viennese waltz tradition, and modern swing camps.
    """
    return [
        {"name": "Blackpool Tower Ballroom", "city": "Blackpool", "country": "UK",
         "lat": 53.8159, "lon": -3.0553, "style": "Ballroom",
         "founded": 1894,
         "notes": "Most prestigious ballroom dance competition venue in the world, annual Blackpool Dance Festival"},
        {"name": "Savoy Ballroom (Historical)", "city": "New York", "country": "USA",
         "lat": 40.8183, "lon": -73.9395, "style": "Lindy Hop/Swing",
         "founded": 1926,
         "notes": "Legendary integrated Harlem ballroom where Lindy Hop was born, closed 1958, demolished 1959"},
        {"name": "Frankie Manning's Harlem", "city": "New York", "country": "USA",
         "lat": 40.8116, "lon": -73.9465, "style": "Lindy Hop",
         "founded": "1930s",
         "notes": "Frankie Manning, father of Lindy Hop aerials, developed air steps dancing in Harlem ballrooms"},
        {"name": "Vienna Opera Ball", "city": "Vienna", "country": "Austria",
         "lat": 48.2082, "lon": 16.3738, "style": "Viennese Waltz",
         "founded": "18th century",
         "notes": "Home of the Viennese waltz tradition, annual Opera Ball is the world's premier waltz event"},
        {"name": "Hammersmith Palais (Historical)", "city": "London", "country": "UK",
         "lat": 51.4613, "lon": -0.1156, "style": "Ballroom",
         "founded": 1919,
         "notes": "Historic Hammersmith Palais de Danse, birthplace of British dance hall culture, closed 2007"},
        {"name": "Arthur Murray Studios HQ", "city": "Miami", "country": "USA",
         "lat": 25.7617, "lon": -80.1918, "style": "Ballroom",
         "founded": 1912,
         "notes": "Franchise that popularized ballroom dance instruction across America and then worldwide"},
        {"name": "Cotton Club (Historical)", "city": "New York", "country": "USA",
         "lat": 40.8100, "lon": -73.9488, "style": "Swing/Jazz Dance",
         "founded": 1923,
         "notes": "Legendary Harlem jazz club with spectacular floor shows and dance performances"},
        {"name": "Cat's Corner Swing Venue", "city": "Montreal", "country": "Canada",
         "lat": 45.5200, "lon": -73.5670, "style": "Swing/Lindy Hop",
         "founded": "2000s",
         "notes": "World-renowned swing dance venue hosting weekly social dances and international workshops"},
        {"name": "Herr\u00e4ng Dance Camp", "city": "Herr\u00e4ng", "country": "Sweden",
         "lat": 60.1500, "lon": 18.3500, "style": "Lindy Hop/Swing",
         "founded": 1982,
         "notes": "Largest swing dance camp in the world, five weeks every summer in a tiny Swedish village"},
        {"name": "Roseland Ballroom (Historical)", "city": "New York", "country": "USA",
         "lat": 40.7625, "lon": -73.9862, "style": "Ballroom",
         "founded": 1919,
         "notes": "NYC's most famous ballroom for nearly a century of dancing, closed 2014 after 95 years"},
        {"name": "Tanztheater Wuppertal Pina Bausch", "city": "Wuppertal", "country": "Germany",
         "lat": 51.2562, "lon": 7.1508, "style": "Tanztheater",
         "founded": 1973,
         "notes": "Home of Pina Bausch's revolutionary Tanztheater that changed contemporary dance forever"},
        {"name": "Strictly Ballroom Scene", "city": "Sydney", "country": "Australia",
         "lat": -33.8688, "lon": 151.2093, "style": "Ballroom",
         "founded": "1980s",
         "notes": "Australian competitive ballroom scene, inspired Baz Luhrmann's famous 1992 film"},
        {"name": "Moscow Dancesport Centre", "city": "Moscow", "country": "Russia",
         "lat": 55.7558, "lon": 37.6173, "style": "Ballroom/Latin",
         "founded": "1990s",
         "notes": "Russia's competitive ballroom and Latin dance training powerhouse, produces world champions"},
        {"name": "West Coast Swing Hub", "city": "Los Angeles", "country": "USA",
         "lat": 34.0522, "lon": -118.2437, "style": "West Coast Swing",
         "founded": "1940s",
         "notes": "Birthplace of West Coast Swing, evolved from Lindy Hop in California dance halls"},
        {"name": "Buenos Aires Milonga Circuit", "city": "Buenos Aires", "country": "Argentina",
         "lat": -34.6037, "lon": -58.3816, "style": "Argentine Tango",
         "founded": "1890s",
         "notes": "World capital of social tango with hundreds of milongas operating nightly across the city"},
        {"name": "Memphis Jive & Rock'n'Roll", "city": "Memphis", "country": "USA",
         "lat": 35.1495, "lon": -90.0490, "style": "Jive/Rock'n'Roll",
         "founded": "1950s",
         "notes": "Memphis rock'n'roll era gave birth to jive dance and early rock and roll partner dancing"},
    ]


def _street_dance_data():
    """Street Dance & Hip-Hop scenes worldwide (20 locations).

    From the birthplace of breakdancing in the Bronx to K-pop dance
    culture in Seoul, covering all major urban dance movements.
    """
    return [
        {"name": "Bronx Breakdance Origins", "city": "New York", "country": "USA",
         "lat": 40.8448, "lon": -73.8648, "style": "Breaking/B-boying",
         "founded": "1970s",
         "notes": "Birthplace of breakdancing in the South Bronx at DJ Kool Herc's 1520 Sedgwick Ave block parties"},
        {"name": "Rock Steady Crew Territory", "city": "New York", "country": "USA",
         "lat": 40.7980, "lon": -73.9381, "style": "Breaking",
         "founded": 1977,
         "notes": "Legendary b-boy crew featuring Crazy Legs and Ken Swift, helped spread breaking worldwide"},
        {"name": "Compton Krumping Scene", "city": "Compton", "country": "USA",
         "lat": 33.8958, "lon": -118.2201, "style": "Krumping",
         "founded": "2000s",
         "notes": "Birthplace of krumping by Tight Eyez and Big Mijo, raw expressive energy, featured in Rize film"},
        {"name": "Detroit Jit & Techno", "city": "Detroit", "country": "USA",
         "lat": 42.3314, "lon": -83.0458, "style": "Jit/Detroit Techno",
         "founded": "1980s",
         "notes": "Detroit jit fast footwork and techno dance culture, born in the same warehouses as electronic music"},
        {"name": "Chicago House & Footwork", "city": "Chicago", "country": "USA",
         "lat": 41.8781, "lon": -87.6298, "style": "Footwork/House",
         "founded": "1980s",
         "notes": "Birthplace of house dance at The Warehouse club, evolved into lightning-fast Chicago footwork"},
        {"name": "Seoul K-Pop Dance Culture", "city": "Seoul", "country": "South Korea",
         "lat": 37.5665, "lon": 126.9780, "style": "K-Pop/Street",
         "founded": "2000s",
         "notes": "Global K-pop choreography phenomenon, Hongdae street dance busking, idol dance practice culture"},
        {"name": "Paris Hip-Hop Capital", "city": "Paris", "country": "France",
         "lat": 48.8566, "lon": 2.3522, "style": "Hip-Hop/Popping",
         "founded": "1980s",
         "notes": "Europe's hip-hop dance capital, birthplace of Juste Debout competition and French new style"},
        {"name": "Oakland Turfing Scene", "city": "Oakland", "country": "USA",
         "lat": 37.8044, "lon": -122.2712, "style": "Turfing",
         "founded": "2000s",
         "notes": "Oakland turf dancing combining gliding, miming, storytelling, and hyphy culture movement"},
        {"name": "London Grime & UK Street", "city": "London", "country": "UK",
         "lat": 51.5074, "lon": -0.1278, "style": "Grime/UK Street",
         "founded": "2000s",
         "notes": "UK grime scene skanking, UK street dance community, home of Boy Blue Entertainment"},
        {"name": "LA Popping & Locking Origins", "city": "Los Angeles", "country": "USA",
         "lat": 34.0522, "lon": -118.2437, "style": "Popping/Locking",
         "founded": "1970s",
         "notes": "Don Campbell invented locking at The Campbellock, Boogaloo Sam brought popping from Fresno"},
        {"name": "Fresno Electric Boogaloos", "city": "Fresno", "country": "USA",
         "lat": 36.7378, "lon": -119.7871, "style": "Popping",
         "founded": 1975,
         "notes": "Boogaloo Sam created the Electric Boogaloos crew and popping funk style right here in Fresno"},
        {"name": "Atlanta Trap Dance Scene", "city": "Atlanta", "country": "USA",
         "lat": 33.7490, "lon": -84.3880, "style": "Atlanta Dance/Trap",
         "founded": "2000s",
         "notes": "Trap music dance culture, Atlanta-originated viral dance challenges dominate social media"},
        {"name": "Tokyo Street Dance Parks", "city": "Tokyo", "country": "Japan",
         "lat": 35.6590, "lon": 139.7006, "style": "All Styles",
         "founded": "1980s",
         "notes": "Yoyogi Park weekend dancers, Japan produces world-class poppers, lockers, and b-boys"},
        {"name": "Montreal Kiki Ball Scene", "city": "Montreal", "country": "Canada",
         "lat": 45.5017, "lon": -73.5673, "style": "Voguing/Ballroom",
         "founded": "2010s",
         "notes": "Growing ballroom and voguing scene with regular kiki balls and house gatherings"},
        {"name": "Harlem Ballroom & Vogue", "city": "New York", "country": "USA",
         "lat": 40.7425, "lon": -73.9925, "style": "Voguing/Ballroom",
         "founded": "1970s",
         "notes": "Harlem ballroom scene where voguing was born in LGBTQ+ ball culture, Paris Is Burning legacy"},
        {"name": "Johannesburg Pantsula Streets", "city": "Johannesburg", "country": "South Africa",
         "lat": -26.2041, "lon": 28.0473, "style": "Pantsula",
         "founded": "1980s",
         "notes": "South African township pantsula with sharp footwork and body isolations born in Soweto"},
        {"name": "Lagos Afrobeats Dance Viral", "city": "Lagos", "country": "Nigeria",
         "lat": 6.5244, "lon": 3.3792, "style": "Afrobeats/Shaku Shaku",
         "founded": "2010s",
         "notes": "Afrobeats dance challenges from Lagos go viral globally, new moves created weekly"},
        {"name": "Berlin Urban Dance Labs", "city": "Berlin", "country": "Germany",
         "lat": 52.5200, "lon": 13.4050, "style": "Urban/Contemporary",
         "founded": "1990s",
         "notes": "Berlin urban dance scene, experimental contemporary-street fusion at Radialsystem and HAU"},
        {"name": "Amsterdam House Dance Forever", "city": "Amsterdam", "country": "Netherlands",
         "lat": 52.3676, "lon": 4.9041, "style": "House Dance",
         "founded": "1990s",
         "notes": "Strong house dance community, Summer Dance Forever festival draws global house dancers"},
        {"name": "Red Bull BC One Global", "city": "Zurich", "country": "Switzerland",
         "lat": 47.3769, "lon": 8.5417, "style": "Breaking",
         "founded": 2004,
         "notes": "World's biggest one-on-one b-boy/b-girl competition, launched breaking into Olympic spotlight"},
    ]


def _irish_celtic_data():
    """Irish & Celtic Dance traditions across six Celtic nations (16 locations).

    From Riverdance in Dublin to Highland games in Scotland, Breton
    fest-noz in France, and Galician muineira in Spain.
    """
    return [
        {"name": "Riverdance - Gaiety Theatre", "city": "Dublin", "country": "Ireland",
         "lat": 53.3413, "lon": -6.2625, "style": "Irish Step Dance",
         "founded": 1994,
         "notes": "Where the Riverdance phenomenon debuted at Eurovision, transforming Irish dance globally forever"},
        {"name": "Galway Sean-n\u00f3s Dance", "city": "Galway", "country": "Ireland",
         "lat": 53.2707, "lon": -9.0568, "style": "Sean-n\u00f3s/Step",
         "founded": "Traditional",
         "notes": "Sean-n\u00f3s old-style free-form dance from Connemara, individualistic and rhythmically complex"},
        {"name": "Siamsa Tire National Folk Theatre", "city": "Tralee", "country": "Ireland",
         "lat": 52.2713, "lon": -9.7023, "style": "Irish Folk Dance",
         "founded": 1974,
         "notes": "National Folk Theatre of Ireland, traditional music, song, and dance performances year-round"},
        {"name": "Comhaltas Ceolt\u00f3ir\u00ed HQ", "city": "Dublin", "country": "Ireland",
         "lat": 53.3175, "lon": -6.2207, "style": "C\u00e9il\u00ed Dance",
         "founded": 1951,
         "notes": "Comhaltas Ceolt\u00f3ir\u00ed \u00c9ireann headquarters, promoting c\u00e9il\u00ed and set dancing worldwide"},
        {"name": "Clare Set Dancing Country", "city": "Ennis", "country": "Ireland",
         "lat": 52.8432, "lon": -8.9861, "style": "Set Dancing",
         "founded": "18th century",
         "notes": "County Clare is the heartland of Irish set dancing, weekly sets in pubs across the county"},
        {"name": "Edinburgh Military Tattoo", "city": "Edinburgh", "country": "Scotland",
         "lat": 55.9486, "lon": -3.1999, "style": "Highland Dance",
         "founded": 1950,
         "notes": "Spectacular Highland dance at Edinburgh Castle esplanade, viewed by 220,000 annually"},
        {"name": "Braemar Royal Highland Gathering", "city": "Braemar", "country": "Scotland",
         "lat": 57.0055, "lon": -3.3990, "style": "Highland Dance",
         "founded": 1832,
         "notes": "Royal Highland Games with Highland fling, sword dance, and seann triubhas competitions"},
        {"name": "Glasgow Celtic Connections", "city": "Glasgow", "country": "Scotland",
         "lat": 55.8642, "lon": -4.2518, "style": "Scottish/Celtic",
         "founded": 1994,
         "notes": "Major Celtic music and dance festival each January, Scottish and cross-Celtic traditions"},
        {"name": "Brittany Fest-Noz", "city": "Rennes", "country": "France",
         "lat": 48.1173, "lon": -1.6778, "style": "Fest-Noz",
         "founded": "Medieval",
         "notes": "Breton fest-noz night festival dances, circle and chain dances (an dro, hanter dro), UNESCO heritage"},
        {"name": "Lorient Interceltic Festival", "city": "Lorient", "country": "France",
         "lat": 47.7483, "lon": -3.3702, "style": "Pan-Celtic",
         "founded": 1971,
         "notes": "Largest Celtic festival gathering in the world, dance from all Celtic nations, 800,000 visitors"},
        {"name": "Oireachtas Irish Dance Championships", "city": "Killarney", "country": "Ireland",
         "lat": 52.0599, "lon": -9.5044, "style": "Irish Step",
         "founded": 1897,
         "notes": "All-Ireland championship for Irish dancing, top competitive step dance event hosted annually"},
        {"name": "Welsh National Eisteddfod", "city": "Cardiff", "country": "Wales",
         "lat": 51.4816, "lon": -3.1791, "style": "Welsh Folk Dance",
         "founded": "12th century",
         "notes": "National Eisteddfod features traditional Welsh clog dancing and folk dance competitions"},
        {"name": "Manx Folk Dance Society", "city": "Douglas", "country": "Isle of Man",
         "lat": 54.1509, "lon": -4.4814, "style": "Manx Dance",
         "founded": "Traditional",
         "notes": "Unique Manx folk dance tradition revived in the 20th century, cross-hand hold dances"},
        {"name": "Cornish Furry Dance Helston", "city": "Truro", "country": "England",
         "lat": 50.2632, "lon": -5.0510, "style": "Cornish/Furry Dance",
         "founded": "Medieval",
         "notes": "Helston Furry Dance on Flora Day and broader Cornish folk dance revival movement"},
        {"name": "Galician Muineira Tradition", "city": "Santiago de Compostela", "country": "Spain",
         "lat": 42.8782, "lon": -8.5448, "style": "Muineira",
         "founded": "Celtic",
         "notes": "Galician Celtic dance tradition with quick 6/8 time, similar to Irish jig with gaita bagpipes"},
        {"name": "Asturian Celtic Dance", "city": "Oviedo", "country": "Spain",
         "lat": 43.3619, "lon": -5.8494, "style": "Asturian Folk",
         "founded": "Celtic",
         "notes": "Asturian Celtic dance tradition with gaita asturiana bagpipe accompaniment, pericote dance"},
    ]


def _festival_data():
    """Dance Festivals & Competitions worldwide (21 locations).

    Major carnival celebrations, contemporary dance biennales, and
    landmark festival venues spanning all continents.
    """
    return [
        {"name": "Carnival Sambadrome Parade", "city": "Rio de Janeiro", "country": "Brazil",
         "lat": -22.9122, "lon": -43.1967, "style": "Samba",
         "founded": 1984,
         "notes": "World's largest dance spectacle, samba school parades with 70,000 performers at Carnival"},
        {"name": "Notting Hill Carnival", "city": "London", "country": "UK",
         "lat": 51.5169, "lon": -0.2023, "style": "Caribbean/Soca",
         "founded": 1966,
         "notes": "Europe's largest street festival with 2 million visitors, Caribbean dance, steel pan, and soca"},
        {"name": "Burning Man Playa Dance", "city": "Black Rock City", "country": "USA",
         "lat": 40.7864, "lon": -119.2065, "style": "Eclectic/EDM",
         "founded": 1986,
         "notes": "Radical self-expression in the desert with massive sound camps and dance art installations"},
        {"name": "Mardi Gras Second Line", "city": "New Orleans", "country": "USA",
         "lat": 29.9511, "lon": -90.0715, "style": "Second Line/Bounce",
         "founded": 1699,
         "notes": "Second line dancing with brass bands, Mardi Gras Indians, and New Orleans bounce music"},
        {"name": "Trinidad Carnival", "city": "Port of Spain", "country": "Trinidad & Tobago",
         "lat": 10.6918, "lon": -61.2225, "style": "Soca/Calypso",
         "founded": "18th century",
         "notes": "Original Caribbean carnival, soca wine and jump-up dancing, J'ouvert mud paint celebrations"},
        {"name": "Edinburgh Fringe Dance Programme", "city": "Edinburgh", "country": "Scotland",
         "lat": 55.9533, "lon": -3.1883, "style": "Contemporary/Mixed",
         "founded": 1947,
         "notes": "World's largest arts festival with hundreds of dance performances across dozens of venues"},
        {"name": "Festival d'Avignon", "city": "Avignon", "country": "France",
         "lat": 43.9493, "lon": 4.8055, "style": "Contemporary",
         "founded": 1947,
         "notes": "Premier European performing arts festival with groundbreaking dance commissions in papal palace"},
        {"name": "Venice Carnival Masked Balls", "city": "Venice", "country": "Italy",
         "lat": 45.4408, "lon": 12.3155, "style": "Masked Ball",
         "founded": "13th century",
         "notes": "Historic masked carnival with elaborate costume balls, minuet dances in Palazzo ballrooms"},
        {"name": "Tomorrowland EDM Festival", "city": "Boom", "country": "Belgium",
         "lat": 51.0909, "lon": 4.3699, "style": "EDM/Festival",
         "founded": 2005,
         "notes": "Massive electronic dance music festival with 400,000+ attendees and fantasy stage designs"},
        {"name": "D\u00eda de los Muertos Parade", "city": "Mexico City", "country": "Mexico",
         "lat": 19.4326, "lon": -99.1332, "style": "Folkloric",
         "founded": "Pre-Columbian",
         "notes": "Day of the Dead parade with folkloric dance troupes, blending indigenous and Spanish traditions"},
        {"name": "Holi Raas Lila Dance", "city": "Mathura", "country": "India",
         "lat": 27.4924, "lon": 77.6737, "style": "Raas Lila/Folk",
         "founded": "Ancient",
         "notes": "Festival of colors with traditional Raas Lila dance celebrations at Krishna's birthplace"},
        {"name": "Carnival of Barranquilla", "city": "Barranquilla", "country": "Colombia",
         "lat": 10.9685, "lon": -74.7813, "style": "Cumbia/Mapal\u00e9",
         "founded": "19th century",
         "notes": "UNESCO heritage carnival, cumbia and mapal\u00e9 dance spectacular, Battle of Flowers parade"},
        {"name": "Obon Bon Odori Festival", "city": "Kyoto", "country": "Japan",
         "lat": 35.0116, "lon": 135.7681, "style": "Bon Odori",
         "founded": "Buddhist",
         "notes": "Ghost festival communal circle dances honoring ancestors with lanterns and taiko drums"},
        {"name": "Kadooment Day Crop Over", "city": "Bridgetown", "country": "Barbados",
         "lat": 13.1132, "lon": -59.5988, "style": "Crop Over/Soca",
         "founded": "1780s",
         "notes": "Barbados Crop Over festival Grand Kadooment Day with costumed soca dance parade to the sea"},
        {"name": "Junkanoo Rush Festival", "city": "Nassau", "country": "Bahamas",
         "lat": 25.0443, "lon": -77.3504, "style": "Junkanoo",
         "founded": "17th century",
         "notes": "Afro-Bahamian street parade with elaborate costumes, cowbells, and rush dancing at dawn"},
        {"name": "Sadler's Wells Theatre", "city": "London", "country": "UK",
         "lat": 51.5292, "lon": -0.1060, "style": "Contemporary/All",
         "founded": 1683,
         "notes": "World's leading dance theater hosting international companies from Akram Khan to Hofesh Shechter"},
        {"name": "Jacob's Pillow Dance Festival", "city": "Becket", "country": "USA",
         "lat": 42.3248, "lon": -73.0893, "style": "All Styles",
         "founded": 1933,
         "notes": "Oldest and longest-running dance festival in the United States, founded by Ted Shawn"},
        {"name": "Biennale Danza Venice", "city": "Venice", "country": "Italy",
         "lat": 45.4295, "lon": 12.3372, "style": "Contemporary",
         "founded": 1999,
         "notes": "Venice Biennale international dance section, cutting-edge choreographic works and Golden Lion prize"},
        {"name": "ImPulsTanz Vienna International", "city": "Vienna", "country": "Austria",
         "lat": 48.2082, "lon": 16.3738, "style": "Contemporary",
         "founded": 1984,
         "notes": "Europe's largest contemporary dance festival with 200+ workshops, performances, and research projects"},
        {"name": "Montpellier Danse Festival", "city": "Montpellier", "country": "France",
         "lat": 43.6108, "lon": 3.8767, "style": "Contemporary",
         "founded": 1981,
         "notes": "Major international contemporary dance festival in southern France, launched many choreographers"},
        {"name": "Carnival of Oruro Diablada", "city": "Oruro", "country": "Bolivia",
         "lat": -17.9622, "lon": -67.1143, "style": "Diablada/Morenada",
         "founded": "18th century",
         "notes": "UNESCO masterpiece, spectacular diablada devil dance processions over 20 hours of parading"},
    ]


# ---------------------------------------------------------------------------
# Cached fetch functions — wrap data builders with Streamlit caching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _fetch_ballet_companies():
    """Return ballet companies as a cached DataFrame."""
    return pd.DataFrame(_ballet_data())


@st.cache_data(ttl=3600)
def _fetch_flamenco_origins():
    """Return flamenco origins as a cached DataFrame."""
    return pd.DataFrame(_flamenco_data())


@st.cache_data(ttl=3600)
def _fetch_tango_latin():
    """Return tango and Latin dance locations as a cached DataFrame."""
    return pd.DataFrame(_tango_latin_data())


@st.cache_data(ttl=3600)
def _fetch_indian_classical():
    """Return Indian classical dance centers as a cached DataFrame."""
    return pd.DataFrame(_indian_classical_data())


@st.cache_data(ttl=3600)
def _fetch_african_dance():
    """Return African dance tradition locations as a cached DataFrame."""
    return pd.DataFrame(_african_dance_data())


@st.cache_data(ttl=3600)
def _fetch_asian_dance():
    """Return traditional Asian dance locations as a cached DataFrame."""
    return pd.DataFrame(_asian_dance_data())


@st.cache_data(ttl=3600)
def _fetch_ballroom_swing():
    """Return ballroom and swing dance venues as a cached DataFrame."""
    return pd.DataFrame(_ballroom_swing_data())


@st.cache_data(ttl=3600)
def _fetch_street_dance():
    """Return street dance and hip-hop scenes as a cached DataFrame."""
    return pd.DataFrame(_street_dance_data())


@st.cache_data(ttl=3600)
def _fetch_irish_celtic():
    """Return Irish and Celtic dance locations as a cached DataFrame."""
    return pd.DataFrame(_irish_celtic_data())


@st.cache_data(ttl=3600)
def _fetch_festivals():
    """Return dance festival locations as a cached DataFrame."""
    return pd.DataFrame(_festival_data())


# ---------------------------------------------------------------------------
# Mode -> fetch function mapping
# ---------------------------------------------------------------------------
FETCH_MAP = {
    "Ballet Companies & Theaters": _fetch_ballet_companies,
    "Flamenco Origins": _fetch_flamenco_origins,
    "Tango & Latin Dance": _fetch_tango_latin,
    "Indian Classical Dance": _fetch_indian_classical,
    "African Dance Traditions": _fetch_african_dance,
    "Traditional Asian Dance": _fetch_asian_dance,
    "Ballroom & Swing": _fetch_ballroom_swing,
    "Street Dance & Hip-Hop": _fetch_street_dance,
    "Irish & Celtic Dance": _fetch_irish_celtic,
    "Dance Festivals & Competitions": _fetch_festivals,
}


# ---------------------------------------------------------------------------
# Build folium map with CircleMarkers
# ---------------------------------------------------------------------------

def _calculate_zoom(df: pd.DataFrame) -> int:
    """Determine appropriate zoom level based on coordinate spread.

    Args:
        df: DataFrame with 'lat' and 'lon' columns.

    Returns:
        Integer zoom level from 2 (world) to 7 (regional).
    """
    lat_range = df["lat"].max() - df["lat"].min()
    lon_range = df["lon"].max() - df["lon"].min()
    spread = max(lat_range, lon_range)

    if spread > 120:
        return 2
    elif spread > 80:
        return 2
    elif spread > 50:
        return 3
    elif spread > 20:
        return 4
    elif spread > 10:
        return 5
    elif spread > 5:
        return 6
    else:
        return 7


def _build_popup_html(row, color: str, icon_char: str) -> str:
    """Build an HTML popup for a single location.

    All user-originated content is escaped through html_module.escape()
    to prevent XSS in the folium popup iframe.

    Args:
        row: A pandas Series representing one location.
        color: Hex color string for the mode.
        icon_char: Emoji icon for the mode.

    Returns:
        HTML string for the folium Popup.
    """
    safe_name = html_module.escape(str(row["name"]))
    safe_city = html_module.escape(str(row["city"]))
    safe_country = html_module.escape(str(row["country"]))
    safe_style = html_module.escape(str(row["style"]))
    safe_founded = html_module.escape(str(row.get("founded", "N/A")))
    safe_notes = html_module.escape(str(row.get("notes", "")))

    return f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif;
                min-width: 230px; max-width: 310px;
                background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                color: #e8ecf4; border-radius: 12px; padding: 14px;
                border: 1px solid {color}50;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <div style="font-size: 14px; font-weight: 700; color: {color};
                    margin-bottom: 6px; letter-spacing: 0.3px;">
            {icon_char} {safe_name}
        </div>
        <div style="font-size: 12px; color: #8b97b0; margin-bottom: 4px;">
            {safe_city}, {safe_country}
        </div>
        <hr style="border: 0; border-top: 1px solid #2a3550; margin: 8px 0;">
        <div style="font-size: 11px; margin-bottom: 4px;">
            <b style="color: #06b6d4;">Style:</b>
            <span style="color: #e8ecf4;">{safe_style}</span>
        </div>
        <div style="font-size: 11px; margin-bottom: 4px;">
            <b style="color: #06b6d4;">Founded:</b>
            <span style="color: #e8ecf4;">{safe_founded}</span>
        </div>
        <div style="font-size: 11px; color: #8b97b0; margin-top: 8px;
                    line-height: 1.5; border-left: 2px solid {color}40;
                    padding-left: 8px;">
            {safe_notes}
        </div>
    </div>
    """


def _build_map(df: pd.DataFrame, color: str, mode: str) -> folium.Map:
    """Build a dark-themed folium map with CircleMarkers for each location.

    Args:
        df: DataFrame with location data including lat, lon, name, city, etc.
        color: Hex color string for markers.
        mode: Current map mode name.

    Returns:
        A folium.Map object ready for rendering.
    """
    # Calculate map center from data centroid
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()
    zoom = _calculate_zoom(df)

    # Create base map with dark tiles
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Get icon for this mode
    icon_char = MODE_ICONS.get(mode, "\U0001f483")

    # Add a CircleMarker for each location
    for _, row in df.iterrows():
        popup_html = _build_popup_html(row, color, icon_char)
        safe_name = html_module.escape(str(row["name"]))
        safe_city = html_module.escape(str(row["city"]))

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=330),
            tooltip=f"{safe_name} \u2014 {safe_city}",
        ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Stats row rendering
# ---------------------------------------------------------------------------

def _render_stats(df: pd.DataFrame, mode: str):
    """Render a row of metric cards summarizing the dataset.

    Displays total locations, unique countries, unique dance styles,
    and unique cities in a four-column layout.

    Args:
        df: DataFrame with the current mode's location data.
        mode: Current map mode name (for potential mode-specific labels).
    """
    total_locations = len(df)
    unique_countries = df["country"].nunique()
    unique_styles = df["style"].nunique()
    unique_cities = df["city"].nunique()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Locations", total_locations)
    with col2:
        st.metric("Countries", unique_countries)
    with col3:
        st.metric("Dance Styles", unique_styles)
    with col4:
        st.metric("Cities", unique_cities)


# ---------------------------------------------------------------------------
# Country breakdown visualization
# ---------------------------------------------------------------------------

def _render_country_breakdown(df: pd.DataFrame):
    """Render a bar chart showing how many locations exist per country.

    Args:
        df: DataFrame with a 'country' column.
    """
    country_counts = df["country"].value_counts().reset_index()
    country_counts.columns = ["Country", "Locations"]
    st.bar_chart(
        country_counts.set_index("Country"),
        height=280,
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Style breakdown table
# ---------------------------------------------------------------------------

def _render_style_breakdown(df: pd.DataFrame):
    """Render a table summarizing the dance styles present in the data.

    Args:
        df: DataFrame with a 'style' column.
    """
    style_counts = df["style"].value_counts().reset_index()
    style_counts.columns = ["Dance Style", "Count"]
    st.dataframe(
        style_counts,
        use_container_width=True,
        height=220,
        hide_index=True,
    )


# ---------------------------------------------------------------------------
# Location detail viewer
# ---------------------------------------------------------------------------

def _render_location_detail(df: pd.DataFrame, mode: str):
    """Render a selectbox to view detailed info about a single location.

    Args:
        df: DataFrame with location data.
        mode: Current map mode name.
    """
    location_names = df["name"].tolist()
    selected = st.selectbox(
        "Explore a Location",
        location_names,
        index=0,
        key=f"dance_detail_{mode}",
    )
    if selected:
        row = df[df["name"] == selected].iloc[0]
        icon = MODE_ICONS.get(mode, "\U0001f483")
        color = MODE_COLORS.get(mode, "#e91e90")

        st.markdown(
            f"**{icon} {html_module.escape(str(row['name']))}**"
        )
        detail_col1, detail_col2 = st.columns(2)
        with detail_col1:
            st.markdown(f"**City:** {html_module.escape(str(row['city']))}")
            st.markdown(f"**Country:** {html_module.escape(str(row['country']))}")
            st.markdown(f"**Coordinates:** {row['lat']:.4f}, {row['lon']:.4f}")
        with detail_col2:
            st.markdown(f"**Style:** {html_module.escape(str(row['style']))}")
            st.markdown(f"**Founded:** {html_module.escape(str(row.get('founded', 'N/A')))}")
        st.info(html_module.escape(str(row.get("notes", ""))))


# ---------------------------------------------------------------------------
# Data table and CSV download
# ---------------------------------------------------------------------------

def _render_data_table(df: pd.DataFrame, mode: str):
    """Render the full data table and a CSV download button.

    Args:
        df: DataFrame with all location data for the current mode.
        mode: Current map mode name (used for the CSV filename).
    """
    st.subheader("Location Data")

    # Define display column order
    display_cols = [
        "name", "city", "country", "style",
        "founded", "notes", "lat", "lon",
    ]
    available_cols = [c for c in display_cols if c in df.columns]
    display_df = df[available_cols].copy()

    # Rename columns for display
    rename_map = {
        "name": "Name",
        "city": "City",
        "country": "Country",
        "style": "Style",
        "founded": "Founded",
        "notes": "Notes",
        "lat": "Latitude",
        "lon": "Longitude",
    }
    display_df = display_df.rename(
        columns={k: v for k, v in rename_map.items() if k in display_df.columns}
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=380,
        hide_index=True,
    )

    # CSV download
    csv_data = display_df.to_csv(index=False).encode("utf-8")
    safe_filename = mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        label="Download CSV",
        data=csv_data,
        file_name=f"dance_maps_{safe_filename}.csv",
        mime="text/csv",
        key=f"dance_csv_{safe_filename}",
    )


# ---------------------------------------------------------------------------
# Main render function — the single public API
# ---------------------------------------------------------------------------

def render_dance_maps_tab():
    """Render the Dance & Performing Arts Maps tab for TerraScout AI.

    This is the single entry point called from app.py. It renders:
    - A tab header with pink styling
    - A mode selector with 10 dance map modes
    - A stats row with metric cards
    - An interactive folium map with CircleMarkers
    - Country and style breakdowns in expanders
    - A location detail viewer
    - A full data table with CSV download
    """

    # ---- Tab header ----
    st.markdown(
        '<div class="tab-header pink">'
        "<h4>\U0001f483 Dance & Performing Arts Maps</h4>"
        "<p>Dance traditions, ballet companies, and performing arts worldwide</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Mode selector with all 10 modes ----
    modes = [
        "Ballet Companies & Theaters",
        "Flamenco Origins",
        "Tango & Latin Dance",
        "Indian Classical Dance",
        "African Dance Traditions",
        "Traditional Asian Dance",
        "Ballroom & Swing",
        "Street Dance & Hip-Hop",
        "Irish & Celtic Dance",
        "Dance Festivals & Competitions",
    ]

    selected_mode = st.selectbox(
        "Map Mode",
        modes,
        index=0,
        key="dance_maps_mode_selector",
    )

    # ---- Mode description caption ----
    description = MODE_DESCRIPTIONS.get(selected_mode, "")
    if description:
        st.caption(description)

    # ---- Fetch data for the selected mode ----
    fetch_fn = FETCH_MAP.get(selected_mode)
    if fetch_fn is None:
        st.error("Unknown map mode selected. Please choose a valid mode.")
        return

    with st.spinner(f"Loading {selected_mode} data..."):
        df = fetch_fn()

    if df is None or df.empty:
        st.warning("No data available for this mode. Please try another.")
        return

    # ---- Stats row with metric cards ----
    _render_stats(df, selected_mode)

    # ---- Interactive folium map ----
    color = MODE_COLORS.get(selected_mode, "#e91e90")
    dance_map = _build_map(df, color, selected_mode)
    st_html(dance_map._repr_html_(), height=500)

    # ---- Analytical breakdowns in expanders ----
    with st.expander("Country Breakdown", expanded=False):
        _render_country_breakdown(df)

    with st.expander("Dance Styles Represented", expanded=False):
        _render_style_breakdown(df)

    # ---- Location detail viewer ----
    with st.expander("Explore Location Details", expanded=False):
        _render_location_detail(df, selected_mode)

    # ---- Full data table and CSV download ----
    _render_data_table(df, selected_mode)
