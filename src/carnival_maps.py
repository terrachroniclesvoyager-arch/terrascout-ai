"""
Carnival & Festival Explorer module for TerraScout AI.
Displays curated maps of world carnivals, parades, mask traditions,
dance festivals, fire festivals, flower festivals, lantern festivals,
and music festivals with preset coordinate data and interactive Folium maps.
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
import html as html_module
from streamlit.components.v1 import html as st_html


# ═══════════════════════════════════════════
# MODE DEFINITIONS
# ═══════════════════════════════════════════
MODE_OPTIONS = [
    "World Carnival Festivals",
    "Mask Traditions Worldwide",
    "Parade Routes",
    "Samba Schools",
    "Street Dance Festivals",
    "Ice & Snow Festivals",
    "Fire Festivals",
    "Flower Festivals",
    "Lantern Festivals",
    "Music Festivals Map",
]

# ═══════════════════════════════════════════
# PRESET DATA PER MODE
# ═══════════════════════════════════════════

WORLD_CARNIVALS = [
    {"name": "Rio Carnival", "lat": -22.9068, "lon": -43.1729,
     "desc": "The world's largest carnival, held annually in Rio de Janeiro with samba parades, floats, and costumes.",
     "country": "Brazil", "month": "February", "color": "#f59e0b"},
    {"name": "Venice Carnival", "lat": 45.4408, "lon": 12.3155,
     "desc": "Historic carnival famous for elaborate masks and costumes, dating back to the 12th century.",
     "country": "Italy", "month": "February", "color": "#8b5cf6"},
    {"name": "Notting Hill Carnival", "lat": 51.5170, "lon": -0.2048,
     "desc": "Europe's largest street festival celebrating Caribbean culture in London.",
     "country": "United Kingdom", "month": "August", "color": "#10b981"},
    {"name": "Cologne Carnival", "lat": 50.9375, "lon": 6.9603,
     "desc": "One of Europe's biggest carnivals, known as the 'fifth season' in Cologne, Germany.",
     "country": "Germany", "month": "February", "color": "#ef4444"},
    {"name": "New Orleans Mardi Gras", "lat": 29.9511, "lon": -90.0715,
     "desc": "Iconic Mardi Gras celebration with parades, jazz, and bead-throwing krewes.",
     "country": "USA", "month": "February/March", "color": "#a855f7"},
    {"name": "Trinidad & Tobago Carnival", "lat": 10.6918, "lon": -61.2225,
     "desc": "Vibrant Caribbean carnival with calypso, soca music, and elaborate mas costumes.",
     "country": "Trinidad & Tobago", "month": "February", "color": "#ec4899"},
    {"name": "Barranquilla Carnival", "lat": 10.9685, "lon": -74.7813,
     "desc": "UNESCO-listed Colombian carnival blending Indigenous, African, and European traditions.",
     "country": "Colombia", "month": "February", "color": "#06b6d4"},
    {"name": "Santa Cruz de Tenerife Carnival", "lat": 28.4636, "lon": -16.2518,
     "desc": "Second-largest carnival in the world after Rio, held in the Canary Islands.",
     "country": "Spain", "month": "February", "color": "#f97316"},
    {"name": "Basel Fasnacht", "lat": 47.5596, "lon": 7.5886,
     "desc": "Switzerland's biggest carnival featuring Morgestraich lantern procession at 4 AM.",
     "country": "Switzerland", "month": "February/March", "color": "#14b8a6"},
    {"name": "Binche Carnival", "lat": 50.4114, "lon": 4.1672,
     "desc": "UNESCO-recognized Belgian carnival with the famous Gilles dancers and wax masks.",
     "country": "Belgium", "month": "February/March", "color": "#38bdf8"},
    {"name": "Oruro Carnival", "lat": -17.9647, "lon": -67.1140,
     "desc": "UNESCO Masterpiece of Intangible Heritage with La Diablada dance in Bolivia.",
     "country": "Bolivia", "month": "February", "color": "#d946ef"},
    {"name": "Goa Carnival", "lat": 15.2993, "lon": 74.1240,
     "desc": "Three-day festival with floats, music, and dancing rooted in Portuguese colonial heritage.",
     "country": "India", "month": "February", "color": "#fbbf24"},
]

MASK_TRADITIONS = [
    {"name": "Venetian Mask Studios - Venice", "lat": 45.4342, "lon": 12.3388,
     "desc": "Centuries-old tradition of handcrafted Bauta, Colombina, and Plague Doctor masks.",
     "country": "Italy", "tradition": "Venetian Masquerade", "color": "#8b5cf6"},
    {"name": "Dogon Mask Ceremonies - Mali", "lat": 14.3475, "lon": -3.5840,
     "desc": "Sacred Kanaga and Sirige masks used in Dama funerary ceremonies.",
     "country": "Mali", "tradition": "West African Ritual", "color": "#f59e0b"},
    {"name": "Noh Theater Masks - Kyoto", "lat": 35.0116, "lon": 135.7681,
     "desc": "Refined Japanese Noh masks representing spirits, women, demons, and elders.",
     "country": "Japan", "tradition": "Japanese Noh Theater", "color": "#ef4444"},
    {"name": "Day of the Dead Masks - Oaxaca", "lat": 17.0732, "lon": -96.7266,
     "desc": "Calavera skulls and painted masks honoring the deceased in Dia de los Muertos.",
     "country": "Mexico", "tradition": "Dia de los Muertos", "color": "#ec4899"},
    {"name": "Hahoe Mask Village - Andong", "lat": 36.5404, "lon": 128.5183,
     "desc": "Korean National Treasure masks used in Hahoe Byeolsin gut shamanic rituals.",
     "country": "South Korea", "tradition": "Korean Talchum", "color": "#06b6d4"},
    {"name": "Chewa Nyau Masks - Malawi", "lat": -14.2860, "lon": 34.3079,
     "desc": "Sacred Gule Wamkulu secret society masks and dance performances.",
     "country": "Malawi", "tradition": "Gule Wamkulu", "color": "#10b981"},
    {"name": "Commedia dell'Arte Museum - Bergamo", "lat": 45.6983, "lon": 9.6773,
     "desc": "Home of Harlequin and Pantalone masks from the Italian theatrical tradition.",
     "country": "Italy", "tradition": "Commedia dell'Arte", "color": "#a855f7"},
    {"name": "Barong & Rangda Masks - Bali", "lat": -8.3405, "lon": 115.0920,
     "desc": "Protective Barong lion masks battling demon queen Rangda in sacred dance-drama.",
     "country": "Indonesia", "tradition": "Balinese Dance", "color": "#f97316"},
    {"name": "Alebrije Workshop - Mexico City", "lat": 19.4326, "lon": -99.1332,
     "desc": "Colorful fantastical creature masks and sculptures from Mexican folk art tradition.",
     "country": "Mexico", "tradition": "Folk Art Masks", "color": "#d946ef"},
    {"name": "Burkina Faso Mask Festival - Dedougou", "lat": 12.4600, "lon": -3.4600,
     "desc": "FESTIMA international mask festival celebrating African mask traditions biennially.",
     "country": "Burkina Faso", "tradition": "Pan-African Festival", "color": "#14b8a6"},
]

PARADE_ROUTES = [
    {"name": "Sambodromo Parade Route - Rio", "lat": -22.9122, "lon": -43.1967,
     "desc": "700m purpose-built parade avenue for Rio's samba school competitions.",
     "country": "Brazil", "length_km": 0.7, "color": "#f59e0b"},
    {"name": "Mardi Gras Route - St. Charles Ave", "lat": 29.9350, "lon": -90.0930,
     "desc": "Traditional uptown parade route along historic St. Charles Avenue, New Orleans.",
     "country": "USA", "length_km": 9.6, "color": "#a855f7"},
    {"name": "Rose Parade Route - Pasadena", "lat": 34.1478, "lon": -118.1445,
     "desc": "5.5-mile route along Colorado Boulevard for the annual Tournament of Roses.",
     "country": "USA", "length_km": 8.8, "color": "#ec4899"},
    {"name": "Notting Hill Carnival Route", "lat": 51.5155, "lon": -0.2055,
     "desc": "Winding route through Notting Hill and Ladbroke Grove in West London.",
     "country": "United Kingdom", "length_km": 5.0, "color": "#10b981"},
    {"name": "Cologne Rosenmontagszug Route", "lat": 50.9381, "lon": 6.9600,
     "desc": "7km Rose Monday parade route through Cologne city center.",
     "country": "Germany", "length_km": 7.0, "color": "#ef4444"},
    {"name": "Nice Carnival Promenade", "lat": 43.6961, "lon": 7.2660,
     "desc": "Battle of Flowers parade along Place Massena and the Promenade du Paillon.",
     "country": "France", "length_km": 2.5, "color": "#06b6d4"},
    {"name": "Viareggio Carnival Boulevard", "lat": 43.8714, "lon": 10.2503,
     "desc": "Seafront boulevard parade with giant papier-mache floats in Tuscany.",
     "country": "Italy", "length_km": 2.0, "color": "#8b5cf6"},
    {"name": "Aalborg Carnival Route", "lat": 57.0488, "lon": 9.9217,
     "desc": "Northern Europe's largest carnival parade through Aalborg, Denmark.",
     "country": "Denmark", "length_km": 4.0, "color": "#38bdf8"},
    {"name": "Toronto Caribbean Carnival Route", "lat": 43.6315, "lon": -79.4173,
     "desc": "Grand Parade route along Lake Shore Boulevard for Caribana celebrations.",
     "country": "Canada", "length_km": 3.5, "color": "#f97316"},
    {"name": "Tenerife Coso Parade Route", "lat": 28.4686, "lon": -16.2546,
     "desc": "Main carnival parade through the streets of Santa Cruz de Tenerife.",
     "country": "Spain", "length_km": 3.0, "color": "#d946ef"},
]

SAMBA_SCHOOLS = [
    {"name": "Mangueira", "lat": -22.9125, "lon": -43.2282,
     "desc": "Founded 1928 in Mangueira hill. Colors: green and pink. One of the oldest samba schools.",
     "neighborhood": "Mangueira", "color": "#10b981"},
    {"name": "Portela", "lat": -22.8563, "lon": -43.3048,
     "desc": "Record 22 carnival championships. Colors: blue and white. Founded 1923.",
     "neighborhood": "Madureira", "color": "#3b82f6"},
    {"name": "Beija-Flor", "lat": -22.7595, "lon": -43.3111,
     "desc": "Known for spectacular floats. Colors: blue and white. Based in Nilopolis.",
     "neighborhood": "Nilopolis", "color": "#06b6d4"},
    {"name": "Salgueiro", "lat": -22.9022, "lon": -43.2355,
     "desc": "Famous for Afro-Brazilian themes. Colors: red and white. Founded 1953.",
     "neighborhood": "Andarai", "color": "#ef4444"},
    {"name": "Mocidade Independente", "lat": -22.8831, "lon": -43.3459,
     "desc": "Powerful drum section (bateria). Colors: green and white. Based in Padre Miguel.",
     "neighborhood": "Padre Miguel", "color": "#22c55e"},
    {"name": "Imperatriz Leopoldinense", "lat": -22.7975, "lon": -43.2911,
     "desc": "Multiple championship winner. Colors: green, gold, and white.",
     "neighborhood": "Ramos", "color": "#fbbf24"},
    {"name": "Unidos da Tijuca", "lat": -22.9244, "lon": -43.2282,
     "desc": "Known for innovative technology in floats. Colors: blue, gold, and white.",
     "neighborhood": "Tijuca", "color": "#8b5cf6"},
    {"name": "Vila Isabel", "lat": -22.9156, "lon": -43.2581,
     "desc": "Named after the neighborhood. Colors: blue and white. Founded 1946.",
     "neighborhood": "Vila Isabel", "color": "#38bdf8"},
    {"name": "Grande Rio", "lat": -22.8172, "lon": -43.2826,
     "desc": "Based in Duque de Caxias. Colors: red, green, and white. Rising powerhouse.",
     "neighborhood": "Duque de Caxias", "color": "#f97316"},
    {"name": "Viradouro", "lat": -22.8808, "lon": -43.1049,
     "desc": "Based in Niteroi across the bay. Colors: red and white. 2020 champion.",
     "neighborhood": "Niteroi", "color": "#ec4899"},
    {"name": "Sambodromo (Parade Venue)", "lat": -22.9122, "lon": -43.1967,
     "desc": "The Marques de Sapucai Sambodromo - purpose-built parade ground seating 72,000.",
     "neighborhood": "Centro", "color": "#f59e0b"},
]

STREET_DANCE_FESTIVALS = [
    {"name": "Edinburgh Festival Fringe", "lat": 55.9533, "lon": -3.1883,
     "desc": "World's largest arts festival with street performers, dance, theater, and comedy.",
     "country": "United Kingdom", "month": "August", "color": "#8b5cf6"},
    {"name": "Burning Man", "lat": 40.7864, "lon": -119.2065,
     "desc": "Radical self-expression festival in Black Rock Desert with art installations and dance.",
     "country": "USA", "month": "August/September", "color": "#f59e0b"},
    {"name": "La Tomatina", "lat": 39.4926, "lon": -0.7770,
     "desc": "Massive tomato-throwing street festival in Bunol, Valencia, Spain.",
     "country": "Spain", "month": "August", "color": "#ef4444"},
    {"name": "Holi Festival - Mathura", "lat": 27.4924, "lon": 77.6737,
     "desc": "Hindu spring festival of colors with street dancing and powder throwing.",
     "country": "India", "month": "March", "color": "#ec4899"},
    {"name": "Songkran Water Festival - Bangkok", "lat": 13.7563, "lon": 100.5018,
     "desc": "Thai New Year water fight festival with street parties across Bangkok.",
     "country": "Thailand", "month": "April", "color": "#06b6d4"},
    {"name": "San Fermin (Running of the Bulls)", "lat": 42.8125, "lon": -1.6458,
     "desc": "Famous Pamplona festival with bull runs, street parties, and traditional dance.",
     "country": "Spain", "month": "July", "color": "#ef4444"},
    {"name": "Oktoberfest", "lat": 48.1315, "lon": 11.5497,
     "desc": "World's largest folk festival in Munich with traditional Bavarian dance and beer.",
     "country": "Germany", "month": "September/October", "color": "#f97316"},
    {"name": "Day of the Dead Parade - Mexico City", "lat": 19.4326, "lon": -99.1332,
     "desc": "Massive street parade with calavera costumes, floats, and traditional dance.",
     "country": "Mexico", "month": "November", "color": "#d946ef"},
    {"name": "Carnival of Cultures - Berlin", "lat": 52.4870, "lon": 13.4241,
     "desc": "Multicultural street festival in Kreuzberg with dance groups from around the world.",
     "country": "Germany", "month": "May/June", "color": "#10b981"},
    {"name": "Awa Odori Dance Festival - Tokushima", "lat": 34.0658, "lon": 134.5593,
     "desc": "Japan's largest dance festival with 1.3 million visitors performing Awa dance.",
     "country": "Japan", "month": "August", "color": "#a855f7"},
]

ICE_SNOW_FESTIVALS = [
    {"name": "Harbin Ice & Snow Festival", "lat": 45.8038, "lon": 126.5350,
     "desc": "World's largest ice festival with massive illuminated ice sculptures in northeast China.",
     "country": "China", "month": "January-February", "color": "#06b6d4"},
    {"name": "Sapporo Snow Festival", "lat": 43.0621, "lon": 141.3544,
     "desc": "Hundreds of snow and ice sculptures across Odori Park and Susukino district.",
     "country": "Japan", "month": "February", "color": "#38bdf8"},
    {"name": "Quebec Winter Carnival", "lat": 46.8139, "lon": -71.2080,
     "desc": "World's biggest winter carnival with ice canoe racing, night parades, and Bonhomme mascot.",
     "country": "Canada", "month": "January-February", "color": "#3b82f6"},
    {"name": "Snow & Ice Festival - Bruges", "lat": 51.2093, "lon": 3.2247,
     "desc": "Exquisite ice sculpture exhibitions in medieval Belgian city.",
     "country": "Belgium", "month": "November-January", "color": "#8b5cf6"},
    {"name": "Ice Magic Festival - Lake Louise", "lat": 51.4254, "lon": -116.1773,
     "desc": "Ice carving competition set against the stunning Canadian Rockies.",
     "country": "Canada", "month": "January", "color": "#14b8a6"},
    {"name": "Winterlude - Ottawa", "lat": 45.4215, "lon": -75.6972,
     "desc": "Canada's capital winter festival with Rideau Canal ice skating and snow sculptures.",
     "country": "Canada", "month": "February", "color": "#a855f7"},
    {"name": "Ice Festival - Jokkmokk", "lat": 66.6068, "lon": 19.8286,
     "desc": "Sami winter market and ice festival above the Arctic Circle in Swedish Lapland.",
     "country": "Sweden", "month": "February", "color": "#10b981"},
    {"name": "Valloire Ice Sculpture Contest", "lat": 45.1667, "lon": 6.4333,
     "desc": "International ice and snow sculpture competition in the French Alps.",
     "country": "France", "month": "January", "color": "#ec4899"},
    {"name": "Ice Lantern Festival - Zhaolin Park", "lat": 45.7700, "lon": 126.6400,
     "desc": "Companion event to Harbin festival featuring delicate ice lantern artworks.",
     "country": "China", "month": "January-February", "color": "#f59e0b"},
    {"name": "Geilo Ice Music Festival", "lat": 60.5342, "lon": 8.2063,
     "desc": "Unique Norwegian festival where musicians play instruments carved entirely from ice.",
     "country": "Norway", "month": "January", "color": "#d946ef"},
]

FIRE_FESTIVALS = [
    {"name": "Las Fallas - Valencia", "lat": 39.4699, "lon": -0.3763,
     "desc": "Giant satirical papier-mache figures (ninots) built then burned in spectacular La Crema.",
     "country": "Spain", "month": "March", "color": "#f59e0b"},
    {"name": "Up Helly Aa - Lerwick", "lat": 60.1551, "lon": -1.1499,
     "desc": "Viking fire festival in Shetland Islands with torchlight procession and galley burning.",
     "country": "United Kingdom", "month": "January", "color": "#ef4444"},
    {"name": "Beltane Fire Festival - Edinburgh", "lat": 55.9556, "lon": -3.1826,
     "desc": "Ancient Celtic May Day celebration on Calton Hill with fire performers and drummers.",
     "country": "United Kingdom", "month": "April/May", "color": "#f97316"},
    {"name": "Noche de San Juan - Spain", "lat": 39.4561, "lon": -0.3545,
     "desc": "Midsummer beach bonfires across Spain celebrating St. John's Eve.",
     "country": "Spain", "month": "June", "color": "#fbbf24"},
    {"name": "Diwali Festival of Lights - Varanasi", "lat": 25.3176, "lon": 83.0064,
     "desc": "Hindu festival of lights with millions of oil lamps along the Ganges River ghats.",
     "country": "India", "month": "October/November", "color": "#d946ef"},
    {"name": "Jeju Fire Festival", "lat": 33.4890, "lon": 126.4983,
     "desc": "Korean festival burning hillside grasslands to ensure a good harvest and ward off pests.",
     "country": "South Korea", "month": "March", "color": "#ec4899"},
    {"name": "Burning of Judas - Greece", "lat": 37.7478, "lon": 26.9747,
     "desc": "Easter Saturday tradition of burning Judas effigies and fireworks on Greek islands.",
     "country": "Greece", "month": "April", "color": "#8b5cf6"},
    {"name": "Luminarias - San Bartolome", "lat": 40.3330, "lon": -5.7000,
     "desc": "Horses leap through bonfires in this ancient Spanish purification ritual.",
     "country": "Spain", "month": "January", "color": "#a855f7"},
    {"name": "Walpurgis Night - Sweden", "lat": 59.8586, "lon": 17.6389,
     "desc": "Bonfires lit across Sweden on April 30 to welcome spring and ward off evil spirits.",
     "country": "Sweden", "month": "April", "color": "#10b981"},
    {"name": "Lag BaOmer Bonfires - Meron", "lat": 32.9981, "lon": 35.4414,
     "desc": "Massive hilltop bonfires in northern Israel celebrating Jewish holiday Lag BaOmer.",
     "country": "Israel", "month": "May", "color": "#06b6d4"},
]

FLOWER_FESTIVALS = [
    {"name": "Rose Parade - Pasadena", "lat": 34.1478, "lon": -118.1445,
     "desc": "Annual New Year's Day parade with elaborate flower-covered floats since 1890.",
     "country": "USA", "month": "January", "color": "#ec4899"},
    {"name": "Keukenhof Gardens - Lisse", "lat": 52.2697, "lon": 4.5462,
     "desc": "World's largest flower garden with 7 million tulip bulbs across 79 acres.",
     "country": "Netherlands", "month": "March-May", "color": "#f59e0b"},
    {"name": "Chiang Mai Flower Festival", "lat": 18.7883, "lon": 98.9853,
     "desc": "Three-day festival with flower floats, garden exhibitions, and beauty pageant.",
     "country": "Thailand", "month": "February", "color": "#d946ef"},
    {"name": "Chelsea Flower Show - London", "lat": 51.4860, "lon": -0.1587,
     "desc": "Prestigious Royal Horticultural Society show held since 1913.",
     "country": "United Kingdom", "month": "May", "color": "#10b981"},
    {"name": "Cherry Blossom Festival - Tokyo", "lat": 35.7141, "lon": 139.7747,
     "desc": "Ueno Park hanami celebrations under thousands of blooming cherry trees.",
     "country": "Japan", "month": "March/April", "color": "#f9a8d4"},
    {"name": "Festa da Flor - Madeira", "lat": 32.6669, "lon": -16.9241,
     "desc": "Funchal flower festival with floral carpets, parades, and Wall of Hope flower display.",
     "country": "Portugal", "month": "May", "color": "#a855f7"},
    {"name": "Floriade - Netherlands", "lat": 52.3934, "lon": 5.2838,
     "desc": "World horticultural expo held once every 10 years in the Netherlands.",
     "country": "Netherlands", "month": "April-October", "color": "#8b5cf6"},
    {"name": "Medellin Flower Festival", "lat": 6.2442, "lon": -75.5812,
     "desc": "Feria de las Flores with silleteros carrying elaborate flower arrangements.",
     "country": "Colombia", "month": "August", "color": "#ef4444"},
    {"name": "Canadian Tulip Festival - Ottawa", "lat": 45.3830, "lon": -75.7040,
     "desc": "One million tulips bloom to celebrate Dutch-Canadian friendship since WWII.",
     "country": "Canada", "month": "May", "color": "#f97316"},
    {"name": "Girona Flower Festival (Temps de Flors)", "lat": 41.9794, "lon": 2.8214,
     "desc": "Historic streets and courtyards of Girona decorated with stunning floral installations.",
     "country": "Spain", "month": "May", "color": "#06b6d4"},
]

LANTERN_FESTIVALS = [
    {"name": "Chinese Lantern Festival - Beijing", "lat": 39.9042, "lon": 116.4074,
     "desc": "Yuan Xiao Jie marking the end of Lunar New Year with thousands of lit lanterns.",
     "country": "China", "month": "February/March", "color": "#ef4444"},
    {"name": "Loi Krathong - Chiang Mai", "lat": 18.7883, "lon": 98.9853,
     "desc": "Thai festival of floating lanterns (krathongs) and sky lanterns (Yi Peng) on rivers.",
     "country": "Thailand", "month": "November", "color": "#f59e0b"},
    {"name": "Obon Festival - Kyoto", "lat": 35.0116, "lon": 135.7681,
     "desc": "Japanese Buddhist festival honoring ancestors with floating lanterns and Bon Odori dance.",
     "country": "Japan", "month": "August", "color": "#ec4899"},
    {"name": "Pingxi Sky Lantern Festival", "lat": 25.0253, "lon": 121.7384,
     "desc": "Thousands of sky lanterns released simultaneously over Pingxi District, Taiwan.",
     "country": "Taiwan", "month": "February", "color": "#f97316"},
    {"name": "Hoi An Lantern Festival", "lat": 15.8801, "lon": 108.3380,
     "desc": "Ancient town lit by hundreds of colorful silk lanterns on every full moon.",
     "country": "Vietnam", "month": "Monthly (full moon)", "color": "#d946ef"},
    {"name": "Seoul Lantern Festival", "lat": 37.5690, "lon": 126.9785,
     "desc": "Cheonggyecheon Stream lined with elaborate illuminated lantern sculptures.",
     "country": "South Korea", "month": "November", "color": "#8b5cf6"},
    {"name": "Diwali Lanterns - Jaipur", "lat": 26.9124, "lon": 75.7873,
     "desc": "City of Jaipur illuminated with millions of diyas and decorative lanterns.",
     "country": "India", "month": "October/November", "color": "#fbbf24"},
    {"name": "Loy Krathong - Sukhothai", "lat": 17.0072, "lon": 99.8231,
     "desc": "Historic Sukhothai ruins provide a magical backdrop for floating lantern ceremonies.",
     "country": "Thailand", "month": "November", "color": "#06b6d4"},
    {"name": "St. Martin's Day Lanterns - Germany", "lat": 50.9375, "lon": 6.9603,
     "desc": "Children's lantern parades through German cities on November 11th (Martinszug).",
     "country": "Germany", "month": "November", "color": "#10b981"},
    {"name": "Giant Lantern Festival - San Fernando", "lat": 15.0286, "lon": 120.6940,
     "desc": "Filipino festival with giant parol lanterns up to 20 feet in diameter.",
     "country": "Philippines", "month": "December", "color": "#a855f7"},
]

MUSIC_FESTIVALS = [
    {"name": "Glastonbury Festival", "lat": 51.1554, "lon": -2.5862,
     "desc": "Legendary UK festival at Worthy Farm with 200,000+ attendees and iconic Pyramid Stage.",
     "country": "United Kingdom", "month": "June", "color": "#10b981"},
    {"name": "Coachella", "lat": 33.6803, "lon": -116.2373,
     "desc": "Massive desert music and arts festival in Indio, California.",
     "country": "USA", "month": "April", "color": "#f59e0b"},
    {"name": "Tomorrowland", "lat": 51.0862, "lon": 4.3755,
     "desc": "Premier electronic dance music festival in Boom, Belgium with spectacular stages.",
     "country": "Belgium", "month": "July", "color": "#8b5cf6"},
    {"name": "Fuji Rock Festival", "lat": 36.9481, "lon": 138.8001,
     "desc": "Japan's largest outdoor music festival set in the Naeba ski resort mountains.",
     "country": "Japan", "month": "July", "color": "#06b6d4"},
    {"name": "Rock in Rio", "lat": -22.9764, "lon": -43.3656,
     "desc": "Mega festival in Rio de Janeiro's Olympic Park with capacity of 100,000+.",
     "country": "Brazil", "month": "September", "color": "#ef4444"},
    {"name": "Primavera Sound", "lat": 41.3874, "lon": 2.1961,
     "desc": "Acclaimed indie and alternative festival at Parc del Forum, Barcelona.",
     "country": "Spain", "month": "June", "color": "#ec4899"},
    {"name": "Roskilde Festival", "lat": 55.6167, "lon": 12.0833,
     "desc": "Northern Europe's largest music festival in Denmark since 1971.",
     "country": "Denmark", "month": "June/July", "color": "#f97316"},
    {"name": "Lollapalooza - Chicago", "lat": 41.8758, "lon": -87.6189,
     "desc": "Four-day festival in Grant Park, Chicago with 100,000+ daily attendance.",
     "country": "USA", "month": "August", "color": "#3b82f6"},
    {"name": "Montreux Jazz Festival", "lat": 46.4312, "lon": 6.9107,
     "desc": "Prestigious jazz and music festival on the shores of Lake Geneva since 1967.",
     "country": "Switzerland", "month": "July", "color": "#a855f7"},
    {"name": "Sonar Festival - Barcelona", "lat": 41.3763, "lon": 2.1493,
     "desc": "International festival of advanced music and new media art.",
     "country": "Spain", "month": "June", "color": "#d946ef"},
    {"name": "Exit Festival - Novi Sad", "lat": 45.2524, "lon": 19.8614,
     "desc": "Award-winning festival held in the 18th-century Petrovaradin Fortress, Serbia.",
     "country": "Serbia", "month": "July", "color": "#14b8a6"},
    {"name": "Sziget Festival - Budapest", "lat": 47.5463, "lon": 19.0583,
     "desc": "Week-long island festival on the Danube hosting 500,000+ visitors annually.",
     "country": "Hungary", "month": "August", "color": "#fbbf24"},
]

# ═══════════════════════════════════════════
# MODE -> DATA MAP
# ═══════════════════════════════════════════
MODE_DATA = {
    "World Carnival Festivals": WORLD_CARNIVALS,
    "Mask Traditions Worldwide": MASK_TRADITIONS,
    "Parade Routes": PARADE_ROUTES,
    "Samba Schools": SAMBA_SCHOOLS,
    "Street Dance Festivals": STREET_DANCE_FESTIVALS,
    "Ice & Snow Festivals": ICE_SNOW_FESTIVALS,
    "Fire Festivals": FIRE_FESTIVALS,
    "Flower Festivals": FLOWER_FESTIVALS,
    "Lantern Festivals": LANTERN_FESTIVALS,
    "Music Festivals Map": MUSIC_FESTIVALS,
}

MODE_ICONS = {
    "World Carnival Festivals": "🎭",
    "Mask Traditions Worldwide": "🎭",
    "Parade Routes": "🎺",
    "Samba Schools": "💃",
    "Street Dance Festivals": "🕺",
    "Ice & Snow Festivals": "❄️",
    "Fire Festivals": "🔥",
    "Flower Festivals": "🌸",
    "Lantern Festivals": "🏮",
    "Music Festivals Map": "🎵",
}

MODE_DESCRIPTIONS = {
    "World Carnival Festivals": "Major carnival celebrations across the globe, from Rio to Venice.",
    "Mask Traditions Worldwide": "Ancient and living mask traditions from every continent.",
    "Parade Routes": "Famous parade routes and procession paths around the world.",
    "Samba Schools": "Rio de Janeiro's legendary samba schools and their practice venues.",
    "Street Dance Festivals": "Major street festivals and dance celebrations worldwide.",
    "Ice & Snow Festivals": "Spectacular winter festivals featuring ice and snow artistry.",
    "Fire Festivals": "Dramatic fire celebrations, bonfires, and pyrotechnic traditions.",
    "Flower Festivals": "World-renowned flower festivals, parades, and garden shows.",
    "Lantern Festivals": "Luminous lantern festivals across Asia and beyond.",
    "Music Festivals Map": "The world's most iconic music festivals and concert events.",
}


# ═══════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════

def _build_map(items: list, mode: str) -> folium.Map:
    """Build a Folium dark-theme map with MarkerCluster for the given items."""
    if not items:
        return folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    avg_lat = sum(it["lat"] for it in items) / len(items)
    avg_lon = sum(it["lon"] for it in items) / len(items)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=3 if mode != "Samba Schools" else 11,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name="Festivals").add_to(m)

    for item in items:
        name_safe = html_module.escape(item["name"])
        desc_safe = html_module.escape(item["desc"])
        color = item.get("color", "#06b6d4")

        extra_lines = ""
        if "country" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Country: {html_module.escape(item["country"])}</span>'
        if "month" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">When: {html_module.escape(item["month"])}</span>'
        if "tradition" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Tradition: {html_module.escape(item["tradition"])}</span>'
        if "neighborhood" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Neighborhood: {html_module.escape(item["neighborhood"])}</span>'
        if "length_km" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Route: {item["length_km"]} km</span>'

        popup_html = f"""
        <div style="max-width:240px;">
            <strong style="color:{color};">{name_safe}</strong>
            {extra_lines}
            <br/><span style="font-size:0.78rem; color:#555;">{desc_safe}</span>
            <br/><span style="font-size:0.72rem; color:#888;">{item['lat']:.4f}, {item['lon']:.4f}</span>
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
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=name_safe,
        ).add_to(cluster)

    return m


def _build_dataframe(items: list, mode: str) -> pd.DataFrame:
    """Build a display DataFrame from item list."""
    rows = []
    for item in items:
        row = {
            "Name": item["name"],
            "Latitude": item["lat"],
            "Longitude": item["lon"],
            "Description": item["desc"],
        }
        if "country" in item:
            row["Country"] = item["country"]
        if "month" in item:
            row["When"] = item["month"]
        if "tradition" in item:
            row["Tradition"] = item["tradition"]
        if "neighborhood" in item:
            row["Neighborhood"] = item["neighborhood"]
        if "length_km" in item:
            row["Route (km)"] = item["length_km"]
        rows.append(row)
    return pd.DataFrame(rows)


def _get_csv(df: pd.DataFrame) -> str:
    """Convert DataFrame to CSV string."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════

def render_carnival_maps_tab():
    """Main render function for the Carnival & Festival Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header pink">
        <h4>\U0001f3ad Carnival & Festival Explorer</h4>
        <p>Discover world carnivals, mask traditions, parade routes, samba schools, fire festivals, lantern festivals, and iconic music events on an interactive dark-theme map.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode Selection
    # ══════════════════════════════════════════
    mode = st.selectbox(
        "Festival Map Mode",
        MODE_OPTIONS,
        key="carnival_mode",
        help="Choose a festival category to explore on the map.",
    )

    icon = MODE_ICONS.get(mode, "🎭")
    mode_desc = MODE_DESCRIPTIONS.get(mode, "")
    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem;">{icon} {html_module.escape(mode_desc)}</p>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # SECTION 2: Load Data
    # ══════════════════════════════════════════
    items = MODE_DATA.get(mode, [])

    if not items:
        st.warning("No data available for this mode.")
        return

    # ══════════════════════════════════════════
    # SECTION 3: Stats Row
    # ══════════════════════════════════════════
    st.markdown("---")

    countries = set(it.get("country", it.get("neighborhood", "")) for it in items)
    months = set(it.get("month", "") for it in items if it.get("month"))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Locations", len(items))
    with c2:
        st.metric("Countries / Areas", len(countries))
    with c3:
        if months:
            st.metric("Distinct Periods", len(months))
        else:
            st.metric("Category", mode.split(" ")[0])
    with c4:
        lat_range = max(it["lat"] for it in items) - min(it["lat"] for it in items)
        st.metric("Lat Spread", f"{lat_range:.1f}\u00b0")

    # ══════════════════════════════════════════
    # SECTION 4: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {icon} {html_module.escape(mode)} Map")

    # Legend
    legend_items = " ".join(
        f'<span style="color:{it["color"]}; font-size:0.8rem;">\u25cf {html_module.escape(it["name"][:30])}</span>'
        for it in items[:12]
    )
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
        unsafe_allow_html=True,
    )

    m = _build_map(items, mode)
    st_html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 5: Data Table
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Festival Data")

    df = _build_dataframe(items, mode)

    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 6: Notable Entries Cards
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Highlights")

    for item in items[:8]:
        name_safe = html_module.escape(item["name"])
        desc_safe = html_module.escape(item["desc"])
        color = item.get("color", "#06b6d4")

        sub_info = ""
        if "country" in item:
            sub_info += html_module.escape(item["country"])
        if "month" in item:
            sub_info += f" &mdash; {html_module.escape(item['month'])}"
        if "tradition" in item:
            sub_info += f" &mdash; {html_module.escape(item['tradition'])}"
        if "neighborhood" in item:
            sub_info += f" &mdash; {html_module.escape(item['neighborhood'])}"

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
            <div style="width:10px; height:56px; border-radius:5px; background:{color};
                        margin-right:0.75rem; flex-shrink:0;"></div>
            <div>
                <div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{name_safe}</div>
                <div style="color:#8b97b0; font-size:0.75rem;">{sub_info}</div>
                <div style="color:#5a6580; font-size:0.7rem;">{desc_safe[:120]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 7: CSV Download
    # ══════════════════════════════════════════
    st.markdown("---")

    csv_data = _get_csv(df)
    filename = mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        f"Download {len(df)} {mode} Locations (CSV)",
        data=csv_data,
        file_name=f"carnival_{filename}.csv",
        mime="text/csv",
        key="carnival_download",
    )
