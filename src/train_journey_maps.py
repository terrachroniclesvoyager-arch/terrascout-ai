"""
Epic Train Journeys Explorer module for TerraScout AI.
Preset data for 10 legendary train routes worldwide with interactive
folium maps, route polylines, station markers, stats, and CSV download.
No external API required -- all route data is embedded.
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
import requests
import html as html_module
import streamlit.components.v1 as components

# ═══════════════════════════════════════════
# ROUTE DATA -- 10 Epic Train Journeys
# ═══════════════════════════════════════════

TRAIN_ROUTES = {
    "Trans-Siberian Railway": {
        "subtitle": "Moscow to Vladivostok",
        "description": "The longest railway line in the world, spanning 9,289 km across Russia from Moscow to Vladivostok over 7 time zones.",
        "color": "#ef4444",
        "total_km": 9289,
        "duration": "6 days 2 hours",
        "country": "Russia",
        "stops": [
            {"name": "Moscow (Yaroslavsky Station)", "lat": 55.7720, "lon": 37.6595, "desc": "Capital of Russia, starting point of the Trans-Siberian Railway", "km": 0},
            {"name": "Vladimir", "lat": 56.1290, "lon": 40.4066, "desc": "Historic Golden Ring city with medieval cathedrals", "km": 210},
            {"name": "Nizhny Novgorod", "lat": 56.3269, "lon": 44.0065, "desc": "Confluence of Volga and Oka rivers, major industrial city", "km": 442},
            {"name": "Perm", "lat": 58.0105, "lon": 56.2502, "desc": "Gateway to the Ural Mountains, cultural center", "km": 1437},
            {"name": "Yekaterinburg", "lat": 56.8389, "lon": 60.6057, "desc": "Border of Europe and Asia, Russia's 4th largest city", "km": 1816},
            {"name": "Tyumen", "lat": 57.1522, "lon": 65.5272, "desc": "First Russian settlement in Siberia, oil capital", "km": 2144},
            {"name": "Omsk", "lat": 54.9885, "lon": 73.3242, "desc": "Major Siberian city on the Irtysh River", "km": 2716},
            {"name": "Novosibirsk", "lat": 55.0084, "lon": 82.9357, "desc": "Capital of Siberia, Russia's 3rd largest city, Ob River crossing", "km": 3343},
            {"name": "Krasnoyarsk", "lat": 56.0153, "lon": 92.8932, "desc": "On the Yenisei River, gateway to Eastern Siberia", "km": 4104},
            {"name": "Irkutsk", "lat": 52.2978, "lon": 104.2964, "desc": "Paris of Siberia, near Lake Baikal, cultural gem", "km": 5185},
            {"name": "Ulan-Ude", "lat": 51.8272, "lon": 107.5930, "desc": "Buddhist center of Russia, Buryat capital", "km": 5642},
            {"name": "Chita", "lat": 52.0515, "lon": 113.4712, "desc": "Gateway to Transbaikal region, Decembrist exile city", "km": 6199},
            {"name": "Khabarovsk", "lat": 48.4827, "lon": 135.0838, "desc": "Major Far Eastern city on the Amur River near China", "km": 8523},
            {"name": "Vladivostok", "lat": 43.1198, "lon": 131.8869, "desc": "Pacific terminus, Russia's Far East naval base", "km": 9289},
        ],
    },
    "Orient Express Route": {
        "subtitle": "Paris to Istanbul",
        "description": "The legendary luxury train connecting Western Europe to the East, immortalized by Agatha Christie. The historic route traversed some of Europe's most elegant cities.",
        "color": "#f59e0b",
        "total_km": 3094,
        "duration": "3 days",
        "country": "France / Germany / Austria / Hungary / Romania / Bulgaria / Turkey",
        "stops": [
            {"name": "Paris (Gare de l'Est)", "lat": 48.8763, "lon": 2.3592, "desc": "City of Light, departure from the grand Gare de l'Est", "km": 0},
            {"name": "Strasbourg", "lat": 48.5734, "lon": 7.7521, "desc": "Franco-German border city with Gothic cathedral", "km": 504},
            {"name": "Munich", "lat": 48.1408, "lon": 11.5580, "desc": "Bavarian capital, beer gardens and baroque palaces", "km": 832},
            {"name": "Vienna", "lat": 48.2082, "lon": 16.3738, "desc": "Imperial capital of the Habsburgs, music and coffeehouses", "km": 1250},
            {"name": "Budapest", "lat": 47.4979, "lon": 19.0402, "desc": "Pearl of the Danube, thermal baths and grand parliament", "km": 1507},
            {"name": "Bucharest", "lat": 44.4268, "lon": 26.1025, "desc": "Little Paris of the East, Romanian capital", "km": 2186},
            {"name": "Sofia", "lat": 42.6977, "lon": 23.3219, "desc": "Ancient Serdica, Bulgarian capital at the foot of Vitosha", "km": 2550},
            {"name": "Plovdiv", "lat": 42.1354, "lon": 24.7453, "desc": "One of the world's oldest cities, Roman amphitheatre", "km": 2700},
            {"name": "Edirne", "lat": 41.6818, "lon": 26.5623, "desc": "Former Ottoman capital, Selimiye Mosque masterpiece", "km": 2900},
            {"name": "Istanbul (Sirkeci Station)", "lat": 41.0136, "lon": 28.9768, "desc": "Where East meets West, terminus at the Golden Horn", "km": 3094},
        ],
    },
    "Glacier Express": {
        "subtitle": "Zermatt to St. Moritz",
        "description": "The slowest express train in the world winds through 91 tunnels, over 291 bridges, and across the Oberalp Pass at 2,033m in the Swiss Alps.",
        "color": "#06b6d4",
        "total_km": 291,
        "duration": "7 hours 52 minutes",
        "country": "Switzerland",
        "stops": [
            {"name": "Zermatt", "lat": 46.0207, "lon": 7.7491, "desc": "Car-free village beneath the iconic Matterhorn", "km": 0},
            {"name": "Visp", "lat": 46.2937, "lon": 7.8829, "desc": "Junction in the Rhone valley, gateway to Zermatt", "km": 35},
            {"name": "Brig", "lat": 46.3167, "lon": 7.9878, "desc": "Historic town at the foot of the Simplon Pass", "km": 44},
            {"name": "Fiesch", "lat": 46.4017, "lon": 8.1353, "desc": "Access to the Aletsch Glacier, largest in the Alps", "km": 65},
            {"name": "Andermatt", "lat": 46.6369, "lon": 8.5936, "desc": "Alpine crossroads, Furka and Gotthard passes meet", "km": 125},
            {"name": "Oberalp Pass (2,033m)", "lat": 46.6595, "lon": 8.6714, "desc": "Highest point of the journey, source of the Rhine", "km": 140},
            {"name": "Disentis", "lat": 46.7037, "lon": 8.8537, "desc": "Benedictine monastery village in Surselva", "km": 165},
            {"name": "Ilanz", "lat": 46.7742, "lon": 9.2042, "desc": "First town on the Rhine, Surselva region", "km": 195},
            {"name": "Chur", "lat": 46.8499, "lon": 9.5329, "desc": "Oldest city in Switzerland, capital of Graubunden", "km": 225},
            {"name": "Thusis", "lat": 46.6966, "lon": 9.4401, "desc": "Entrance to the Via Mala gorge, Hinterrhein valley", "km": 245},
            {"name": "Filisur", "lat": 46.6726, "lon": 9.6883, "desc": "Famous Landwasser Viaduct, UNESCO World Heritage", "km": 260},
            {"name": "St. Moritz", "lat": 46.4908, "lon": 9.8355, "desc": "Glamorous alpine resort, birthplace of winter tourism", "km": 291},
        ],
    },
    "Rocky Mountaineer": {
        "subtitle": "Canadian Rockies Scenic Routes",
        "description": "A luxury daylight-only train through the Canadian Rockies, offering breathtaking views of snow-capped peaks, pristine lakes, and wild rivers.",
        "color": "#10b981",
        "total_km": 1060,
        "duration": "2 days (daylight only)",
        "country": "Canada",
        "stops": [
            {"name": "Vancouver", "lat": 49.2827, "lon": -123.1207, "desc": "Pacific coast metropolis surrounded by mountains and ocean", "km": 0},
            {"name": "Fraser Canyon", "lat": 49.3814, "lon": -121.4575, "desc": "Dramatic gorge carved by the Fraser River, Hell's Gate rapids", "km": 200},
            {"name": "Kamloops", "lat": 50.6745, "lon": -120.3273, "desc": "Overnight stop in the Thompson River valley, semi-arid hills", "km": 450},
            {"name": "Revelstoke", "lat": 51.0000, "lon": -118.1953, "desc": "Mountain town in the Columbia Range, heritage railway hub", "km": 575},
            {"name": "Glacier National Park", "lat": 51.2653, "lon": -117.5169, "desc": "Rogers Pass through the Selkirk Mountains, avalanche galleries", "km": 640},
            {"name": "Golden", "lat": 51.2981, "lon": -116.9675, "desc": "Columbia River wetlands, gateway to six national parks", "km": 700},
            {"name": "Kicking Horse Pass", "lat": 51.3567, "lon": -116.8067, "desc": "Continental Divide crossing, Spiral Tunnels engineering marvel", "km": 740},
            {"name": "Lake Louise", "lat": 51.4254, "lon": -116.1773, "desc": "Iconic turquoise lake set against Victoria Glacier", "km": 790},
            {"name": "Banff", "lat": 51.1784, "lon": -115.5708, "desc": "Canada's first national park, hot springs and elk", "km": 850},
            {"name": "Jasper", "lat": 52.8737, "lon": -118.0814, "desc": "Northern Rockies town, dark sky preserve, Columbia Icefield", "km": 1060},
        ],
    },
    "Blue Train South Africa": {
        "subtitle": "Pretoria to Cape Town",
        "description": "One of the most luxurious train experiences in the world, traversing 1,600 km of diverse South African landscape from highveld to winelands.",
        "color": "#3b82f6",
        "total_km": 1600,
        "duration": "27 hours",
        "country": "South Africa",
        "stops": [
            {"name": "Pretoria", "lat": -25.7461, "lon": 28.1876, "desc": "Administrative capital of South Africa, Union Buildings", "km": 0},
            {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473, "desc": "City of Gold, economic powerhouse of Africa", "km": 60},
            {"name": "Klerksdorp", "lat": -26.8522, "lon": 26.6679, "desc": "Western Transvaal mining town, gold rush heritage", "km": 250},
            {"name": "Kimberley", "lat": -28.7282, "lon": 24.7499, "desc": "Diamond capital, the Big Hole open-pit mine", "km": 500},
            {"name": "De Aar", "lat": -30.6498, "lon": 24.0096, "desc": "Railway junction in the Karoo semi-desert", "km": 750},
            {"name": "Three Sisters", "lat": -31.5400, "lon": 24.2300, "desc": "Named for three flat-topped hills in the Great Karoo", "km": 850},
            {"name": "Beaufort West", "lat": -32.3567, "lon": 22.5850, "desc": "Oldest town in the Karoo, Karoo National Park", "km": 1000},
            {"name": "Matjiesfontein", "lat": -33.2290, "lon": 20.5800, "desc": "Perfectly preserved Victorian village in the Karoo", "km": 1150},
            {"name": "Worcester", "lat": -33.6461, "lon": 19.4448, "desc": "Breede River valley, gateway to the winelands", "km": 1350},
            {"name": "Paarl", "lat": -33.7340, "lon": 18.9699, "desc": "Historic wine town, Afrikaans Language Monument", "km": 1450},
            {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241, "desc": "Mother City beneath Table Mountain, journey's end", "km": 1600},
        ],
    },
    "Shinkansen Network": {
        "subtitle": "Japan Bullet Train System",
        "description": "The world's first high-speed rail network, running at up to 320 km/h with legendary punctuality. The Tokaido line alone carries 150 million passengers per year.",
        "color": "#ec4899",
        "total_km": 2765,
        "duration": "Varies (Tokyo-Osaka: 2h 15m)",
        "country": "Japan",
        "stops": [
            {"name": "Tokyo Station", "lat": 35.6812, "lon": 139.7671, "desc": "Central hub, 1914 red-brick station, start of Tokaido Shinkansen", "km": 0},
            {"name": "Shin-Yokohama", "lat": 35.5073, "lon": 139.6166, "desc": "Gateway to Yokohama, Japan's second-largest city", "km": 29},
            {"name": "Nagoya", "lat": 35.1709, "lon": 136.8815, "desc": "Industrial powerhouse, Toyota city, Nagoya Castle", "km": 366},
            {"name": "Kyoto", "lat": 34.9855, "lon": 135.7584, "desc": "Ancient capital, 2000 temples and shrines, geisha district", "km": 513},
            {"name": "Shin-Osaka", "lat": 34.7336, "lon": 135.5001, "desc": "Junction for western Shinkansen lines, street food capital", "km": 553},
            {"name": "Shin-Kobe", "lat": 34.7055, "lon": 135.1972, "desc": "Port city rebuilt after 1995 earthquake, beef capital", "km": 589},
            {"name": "Okayama", "lat": 34.6652, "lon": 133.9184, "desc": "Korakuen Garden, gateway to Seto Inland Sea islands", "km": 733},
            {"name": "Hiroshima", "lat": 34.3963, "lon": 132.4596, "desc": "Peace Memorial, rebuilt city of resilience, Miyajima Island", "km": 894},
            {"name": "Hakata (Fukuoka)", "lat": 33.5904, "lon": 130.4207, "desc": "Western terminus of Sanyo Shinkansen, ramen capital", "km": 1175},
            {"name": "Shin-Aomori", "lat": 40.8243, "lon": 140.7210, "desc": "Northern Honshu terminus, gateway to Tohoku region", "km": 713},
            {"name": "Shin-Hakodate-Hokuto", "lat": 41.9049, "lon": 140.6488, "desc": "Hokkaido Shinkansen terminus via Seikan undersea tunnel", "km": 863},
            {"name": "Kagoshima-Chuo", "lat": 31.5842, "lon": 130.5414, "desc": "Southern terminus, facing active Sakurajima volcano", "km": 1325},
        ],
    },
    "Indian Palace on Wheels": {
        "subtitle": "Rajasthan Luxury Train Tour",
        "description": "A week-long royal journey through Rajasthan's forts, palaces, and desert landscapes aboard one of India's most luxurious heritage trains.",
        "color": "#f97316",
        "total_km": 2960,
        "duration": "7 nights / 8 days",
        "country": "India",
        "stops": [
            {"name": "Delhi (Safdarjung Station)", "lat": 28.5849, "lon": 77.2068, "desc": "National capital, start of the royal circuit, Mughal heritage", "km": 0},
            {"name": "Jaipur", "lat": 26.9124, "lon": 75.7873, "desc": "Pink City, Hawa Mahal, Amber Fort, royal observatories", "km": 280},
            {"name": "Sawai Madhopur", "lat": 26.0163, "lon": 76.3609, "desc": "Ranthambore National Park, tiger safaris in ancient fort ruins", "km": 480},
            {"name": "Chittorgarh", "lat": 24.8887, "lon": 74.6269, "desc": "Largest fort in India, legendary Rajput citadel of honor", "km": 680},
            {"name": "Udaipur", "lat": 24.5854, "lon": 73.7125, "desc": "City of Lakes, Venice of the East, floating palace", "km": 870},
            {"name": "Jaisalmer", "lat": 26.9157, "lon": 70.9083, "desc": "Golden City rising from the Thar Desert, living fort", "km": 1350},
            {"name": "Jodhpur", "lat": 26.2389, "lon": 73.0243, "desc": "Blue City, massive Mehrangarh Fort, Umaid Bhawan Palace", "km": 1650},
            {"name": "Bharatpur", "lat": 27.2152, "lon": 77.4890, "desc": "Keoladeo Bird Sanctuary, UNESCO World Heritage wetland", "km": 2400},
            {"name": "Agra", "lat": 27.1767, "lon": 78.0081, "desc": "Taj Mahal, Agra Fort, pinnacle of Mughal architecture", "km": 2580},
            {"name": "Delhi (Return)", "lat": 28.6139, "lon": 77.2090, "desc": "Return to Delhi, completing the Rajasthan royal circuit", "km": 2960},
        ],
    },
    "Bernina Express": {
        "subtitle": "Swiss-Italian Alpine Crossing",
        "description": "A UNESCO World Heritage railway crossing the Alps from Chur to Tirano, reaching 2,253m at the Bernina Pass with spectacular glaciers and viaducts.",
        "color": "#8b5cf6",
        "total_km": 144,
        "duration": "4 hours 9 minutes",
        "country": "Switzerland / Italy",
        "stops": [
            {"name": "Chur", "lat": 46.8499, "lon": 9.5329, "desc": "Oldest city in Switzerland, starting point in the Rhine valley", "km": 0},
            {"name": "Landquart", "lat": 46.9689, "lon": 9.5590, "desc": "Railway junction in the Rhine valley, Rhaetian Railway hub", "km": 15},
            {"name": "Davos", "lat": 46.8027, "lon": 9.8360, "desc": "Highest city in Europe, famous for World Economic Forum", "km": 50},
            {"name": "Filisur", "lat": 46.6726, "lon": 9.6883, "desc": "Landwasser Viaduct, iconic curved stone bridge over gorge", "km": 60},
            {"name": "Berguen", "lat": 46.6300, "lon": 9.7458, "desc": "Albula spiral tunnels, UNESCO engineering marvel", "km": 68},
            {"name": "Samedan", "lat": 46.5339, "lon": 9.8722, "desc": "Upper Engadin valley floor, highest airport in Europe", "km": 85},
            {"name": "Pontresina", "lat": 46.4948, "lon": 9.9002, "desc": "Mountaineering base, Morteratsch Glacier access", "km": 90},
            {"name": "Bernina Pass (Ospizio Bernina, 2,253m)", "lat": 46.4108, "lon": 10.0246, "desc": "Highest point, alpine lakes, glaciers on both sides", "km": 105},
            {"name": "Alp Grum", "lat": 46.3738, "lon": 10.0461, "desc": "Stunning viewpoint over Palu Glacier and Lake Palue", "km": 110},
            {"name": "Poschiavo", "lat": 46.3225, "lon": 10.0608, "desc": "Italian-speaking valley town, Mediterranean feel in the Alps", "km": 125},
            {"name": "Brusio Spiral Viaduct", "lat": 46.2599, "lon": 10.1127, "desc": "Unique circular viaduct descending into the valley", "km": 135},
            {"name": "Tirano", "lat": 46.2153, "lon": 10.1687, "desc": "Italian border town, Valtellina wine region, palm trees", "km": 144},
        ],
    },
    "The Ghan": {
        "subtitle": "Adelaide to Darwin",
        "description": "Named after Afghan cameleers who explored the outback, The Ghan traverses 2,979 km of Australia's red center from the Southern Ocean to the Timor Sea.",
        "color": "#dc2626",
        "total_km": 2979,
        "duration": "54 hours (2 nights)",
        "country": "Australia",
        "stops": [
            {"name": "Adelaide", "lat": -34.9285, "lon": 138.6007, "desc": "City of churches, wine capital, Southern Ocean coast", "km": 0},
            {"name": "Port Augusta", "lat": -32.4907, "lon": 137.7847, "desc": "Crossroads of Australia, Spencer Gulf, Flinders Ranges", "km": 310},
            {"name": "Woomera", "lat": -31.1622, "lon": 136.8328, "desc": "Former rocket range in the vast outback, restricted zone", "km": 485},
            {"name": "Coober Pedy", "lat": -29.0135, "lon": 134.7544, "desc": "Underground opal mining town, moonscape terrain", "km": 740},
            {"name": "Manguri", "lat": -28.3300, "lon": 134.2800, "desc": "Remote siding, gateway to the painted desert and Breakaways", "km": 830},
            {"name": "Alice Springs", "lat": -23.6980, "lon": 133.8807, "desc": "Red Centre hub, MacDonnell Ranges, Aboriginal culture", "km": 1530},
            {"name": "Tennant Creek", "lat": -19.6522, "lon": 134.1903, "desc": "Gold mining town, Devil's Marbles nearby", "km": 2010},
            {"name": "Katherine", "lat": -14.4521, "lon": 132.2636, "desc": "Katherine Gorge (Nitmiluk), tropical Top End gateway", "km": 2640},
            {"name": "Adelaide River", "lat": -13.2381, "lon": 131.1043, "desc": "War cemetery, jumping crocodile cruises", "km": 2850},
            {"name": "Darwin", "lat": -12.4634, "lon": 130.8456, "desc": "Tropical capital, Timor Sea, gateway to Kakadu", "km": 2979},
        ],
    },
    "Jacobite Steam Train": {
        "subtitle": "Scotland Harry Potter Viaduct Route",
        "description": "The real-life Hogwarts Express steams across the Glenfinnan Viaduct and past lochs and mountains in the Scottish Highlands, Fort William to Mallaig.",
        "color": "#a855f7",
        "total_km": 67,
        "duration": "2 hours 10 minutes (one way)",
        "country": "United Kingdom (Scotland)",
        "stops": [
            {"name": "Fort William", "lat": 56.8198, "lon": -5.1052, "desc": "Outdoor capital of the UK, beneath Ben Nevis, Britain's highest peak", "km": 0},
            {"name": "Banavie (Neptune's Staircase)", "lat": 56.8434, "lon": -5.1013, "desc": "Caledonian Canal locks, views of Ben Nevis and Aonach Mor", "km": 3},
            {"name": "Corpach", "lat": 56.8440, "lon": -5.1218, "desc": "Where Loch Linnhe meets the canal, Corpach Basin", "km": 5},
            {"name": "Glenfinnan", "lat": 56.8714, "lon": -5.4384, "desc": "Iconic 21-arch viaduct (Harry Potter), Bonnie Prince Charlie monument", "km": 20},
            {"name": "Lochailort", "lat": 56.8724, "lon": -5.6646, "desc": "Remote village, SOE training base in WWII, sea loch views", "km": 33},
            {"name": "Arisaig", "lat": 56.9123, "lon": -5.8415, "desc": "White sand beaches, views to Rum, Eigg, and Skye", "km": 45},
            {"name": "Morar", "lat": 56.9369, "lon": -5.8258, "desc": "Silver sands beach, deepest freshwater loch in Britain", "km": 55},
            {"name": "Mallaig", "lat": 57.0063, "lon": -5.8283, "desc": "Fishing harbor, ferry to Skye and Small Isles, journey's end", "km": 67},
        ],
    },
}

# Route line colors for polylines
ROUTE_COLORS = {
    "Trans-Siberian Railway": "#ef4444",
    "Orient Express Route": "#f59e0b",
    "Glacier Express": "#06b6d4",
    "Rocky Mountaineer": "#10b981",
    "Blue Train South Africa": "#3b82f6",
    "Shinkansen Network": "#ec4899",
    "Indian Palace on Wheels": "#f97316",
    "Bernina Express": "#8b5cf6",
    "The Ghan": "#dc2626",
    "Jacobite Steam Train": "#a855f7",
}


# ═══════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════

def _get_zoom_for_route(route_name: str) -> int:
    """Return an appropriate zoom level based on route length."""
    total_km = TRAIN_ROUTES[route_name]["total_km"]
    if total_km > 5000:
        return 3
    elif total_km > 2000:
        return 4
    elif total_km > 1000:
        return 5
    elif total_km > 500:
        return 6
    elif total_km > 200:
        return 8
    elif total_km > 100:
        return 9
    return 10


def _get_center(stops: list) -> tuple:
    """Calculate center point of all stops."""
    lats = [s["lat"] for s in stops]
    lons = [s["lon"] for s in stops]
    return (sum(lats) / len(lats), sum(lons) / len(lons))


@st.cache_data(ttl=3600)
def _get_route_elevation_profile(stops: list) -> list:
    """Fetch elevation data for route stops from Open-Elevation API.
    Returns list of dicts with stop name and elevation, or empty list on failure.
    """
    locations = "|".join(f"{s['lat']},{s['lon']}" for s in stops)
    try:
        resp = requests.get(
            "https://api.open-elevation.com/api/v1/lookup",
            params={"locations": locations},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        elevations = []
        for i, r in enumerate(results):
            if i < len(stops):
                elevations.append({
                    "stop": stops[i]["name"],
                    "elevation_m": r.get("elevation", 0),
                    "km": stops[i].get("km", 0),
                })
        return elevations
    except Exception:
        return []


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════

def render_train_journey_maps_tab():
    """Main render function for the Epic Train Journeys Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header amber">
        <h4>Epic Train Journeys Explorer</h4>
        <p>Explore 10 legendary railway routes across the globe &mdash; from the Trans-Siberian to the Hogwarts Express. Interactive maps, station data, and route profiles.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Route selector ──
    route_names = list(TRAIN_ROUTES.keys())
    selected_route = st.selectbox(
        "Select Train Journey",
        route_names,
        key="train_route_select",
        help="Choose one of 10 epic train routes to explore on the map.",
    )

    route = TRAIN_ROUTES[selected_route]
    stops = route["stops"]
    color = route["color"]

    # ── Route info banner ──
    st.markdown(f"""
    <div style="background:rgba(15,23,42,0.65); border:1px solid #2a3550; border-left:4px solid {color};
                border-radius:8px; padding:1rem 1.25rem; margin:0.75rem 0;">
        <div style="color:{color}; font-weight:700; font-size:1.05rem;">{html_module.escape(selected_route)}</div>
        <div style="color:#e8ecf4; font-size:0.9rem; margin-top:0.25rem;">{html_module.escape(route['subtitle'])}</div>
        <div style="color:#8b97b0; font-size:0.82rem; margin-top:0.35rem;">{html_module.escape(route['description'])}</div>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Stats
    # ══════════════════════════════════════════
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Distance", f"{route['total_km']:,} km")
    with c2:
        st.metric("Duration", route["duration"])
    with c3:
        st.metric("Stations / Stops", f"{len(stops)}")
    with c4:
        st.metric("Countries", route["country"].count("/") + 1 if "/" in route["country"] else "1")

    # ══════════════════════════════════════════
    # SECTION 2: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Route Map")

    # Color legend
    st.markdown(f"""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem; align-items:center;">
        <span style="color:{color}; font-size:0.85rem; font-weight:600;">&#9679; {html_module.escape(selected_route)}</span>
        <span style="color:#8b97b0; font-size:0.8rem;">| Stations marked with popups | Click markers for details</span>
    </div>
    """, unsafe_allow_html=True)

    center = _get_center(stops)
    zoom = _get_zoom_for_route(selected_route)

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    # Route polyline
    route_coords = [[s["lat"], s["lon"]] for s in stops]
    folium.PolyLine(
        locations=route_coords,
        color=color,
        weight=3,
        opacity=0.85,
        dash_array="8 4",
        tooltip=html_module.escape(selected_route),
    ).add_to(m)

    # Station markers
    for i, stop in enumerate(stops):
        safe_name = html_module.escape(stop["name"])
        safe_desc = html_module.escape(stop["desc"])
        km_label = f"Km {stop.get('km', '?')}" if "km" in stop else ""

        # First and last stops get special styling
        if i == 0:
            marker_color = "#10b981"
            label = "START"
        elif i == len(stops) - 1:
            marker_color = "#ef4444"
            label = "END"
        else:
            marker_color = color
            label = f"Stop {i}"

        popup_html = f"""
        <div style="background:#1a2235; color:#e8ecf4; padding:10px; border-radius:8px;
                    min-width:180px; max-width:260px; border:1px solid #2a3550;">
            <div style="color:{marker_color}; font-weight:700; font-size:0.95rem;
                        border-bottom:1px solid #2a3550; padding-bottom:6px; margin-bottom:6px;">
                {safe_name}
            </div>
            <div style="color:#8b97b0; font-size:0.82rem; margin-bottom:4px;">{safe_desc}</div>
            <div style="color:#5a6580; font-size:0.75rem;">{html_module.escape(km_label)} &bull; {html_module.escape(label)}</div>
        </div>
        """

        folium.CircleMarker(
            location=[stop["lat"], stop["lon"]],
            radius=7 if i in (0, len(stops) - 1) else 5,
            color=marker_color,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.85,
            weight=2 if i in (0, len(stops) - 1) else 1,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=safe_name,
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 3: Station Details Table
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Station Details")

    table_rows = []
    for i, stop in enumerate(stops):
        table_rows.append({
            "#": i + 1,
            "Station": stop["name"],
            "Latitude": round(stop["lat"], 4),
            "Longitude": round(stop["lon"], 4),
            "Km from Start": stop.get("km", ""),
            "Description": stop["desc"],
        })

    df = pd.DataFrame(table_rows)
    st.dataframe(df, width="stretch", hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 4: Station Cards
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Station Highlights")

    for i, stop in enumerate(stops):
        safe_name = html_module.escape(stop["name"])
        safe_desc = html_module.escape(stop["desc"])
        km_val = stop.get("km", "")

        if i == 0:
            badge_html = '<span style="background:#10b981; color:#0a0e1a; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:700;">DEPARTURE</span>'
        elif i == len(stops) - 1:
            badge_html = '<span style="background:#ef4444; color:#fff; padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:700;">ARRIVAL</span>'
        else:
            badge_html = f'<span style="color:#5a6580; font-size:0.72rem;">Stop {i}</span>'

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
            <div style="width:50px; height:50px; border-radius:50%; background:{color}18;
                        display:flex; align-items:center; justify-content:center;
                        margin-right:0.75rem; flex-shrink:0; border:2px solid {color}40;">
                <span style="color:{color}; font-weight:800; font-size:0.75rem;">{km_val}</span>
            </div>
            <div style="flex:1;">
                <div style="color:#e8ecf4; font-weight:600; font-size:0.88rem;">{safe_name} {badge_html}</div>
                <div style="color:#8b97b0; font-size:0.78rem; margin-top:2px;">{safe_desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 5: Elevation Profile (optional API call)
    # ══════════════════════════════════════════
    st.markdown("---")
    with st.expander("Elevation Profile (fetches from Open-Elevation API)", expanded=False):
        if st.button("Load Elevation Data", key="train_elev_btn"):
            with st.spinner("Fetching elevation data for station stops..."):
                elevations = _get_route_elevation_profile(stops)
            if elevations:
                st.session_state.train_elevations = elevations
            else:
                st.warning("Could not retrieve elevation data. The Open-Elevation API may be unavailable.")

        if "train_elevations" in st.session_state:
            elev_data = st.session_state.train_elevations
            elev_df = pd.DataFrame(elev_data)
            st.dataframe(elev_df, width="stretch", hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 6: Compare All Routes
    # ══════════════════════════════════════════
    st.markdown("---")
    with st.expander("Compare All 10 Routes", expanded=False):
        compare_rows = []
        for rname, rdata in TRAIN_ROUTES.items():
            compare_rows.append({
                "Route": rname,
                "From - To": rdata["subtitle"],
                "Distance (km)": rdata["total_km"],
                "Duration": rdata["duration"],
                "Stops": len(rdata["stops"]),
                "Country": rdata["country"],
            })
        compare_df = pd.DataFrame(compare_rows)
        st.dataframe(compare_df, width="stretch", hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 7: CSV Download
    # ══════════════════════════════════════════
    st.markdown("---")

    # Build export rows for the selected route
    export_rows = []
    for i, stop in enumerate(stops):
        export_rows.append({
            "route": selected_route,
            "stop_number": i + 1,
            "station": stop["name"],
            "latitude": stop["lat"],
            "longitude": stop["lon"],
            "km_from_start": stop.get("km", ""),
            "description": stop["desc"],
            "total_route_km": route["total_km"],
            "duration": route["duration"],
            "country": route["country"],
        })
    export_df = pd.DataFrame(export_rows)

    csv_buf = io.StringIO()
    export_df.to_csv(csv_buf, index=False)

    safe_filename = selected_route.lower().replace(" ", "_").replace("'", "")
    st.download_button(
        f"Download {len(stops)} Stations - {selected_route} (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"train_journey_{safe_filename}.csv",
        mime="text/csv",
        key="train_csv_download",
    )
