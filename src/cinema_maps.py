# -*- coding: utf-8 -*-
"""
Cinema & Film Locations Maps module for TerraScout AI.
Provides 10 interactive map types covering Hollywood studios, iconic film
franchises (LOTR, GoT, Star Wars, James Bond), film festivals, famous
movie scenes, animation studios, world cinema capitals, and horror locations.
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
# 1. HOLLYWOOD & MAJOR STUDIOS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_studios():
    data = [
        {"studio": "Warner Bros. Studios", "city": "Burbank", "country": "USA", "founded": 1923, "lat": 34.1483, "lon": -118.3381, "notes": "Harry Potter, DC Universe, The Matrix"},
        {"studio": "Universal Studios", "city": "Universal City", "country": "USA", "founded": 1912, "lat": 34.1381, "lon": -118.3534, "notes": "Jurassic Park, Fast & Furious, Jaws"},
        {"studio": "Paramount Pictures", "city": "Hollywood", "country": "USA", "founded": 1912, "lat": 34.0836, "lon": -118.3187, "notes": "The Godfather, Mission Impossible, Top Gun"},
        {"studio": "20th Century Studios", "city": "Century City", "country": "USA", "founded": 1935, "lat": 34.0555, "lon": -118.4122, "notes": "Avatar, Alien, Planet of the Apes"},
        {"studio": "Columbia Pictures / Sony", "city": "Culver City", "country": "USA", "founded": 1924, "lat": 34.0151, "lon": -118.4003, "notes": "Spider-Man, Ghostbusters, Men in Black"},
        {"studio": "Walt Disney Studios", "city": "Burbank", "country": "USA", "founded": 1923, "lat": 34.1561, "lon": -118.3254, "notes": "Snow White, The Lion King, Frozen"},
        {"studio": "Metro-Goldwyn-Mayer (MGM)", "city": "Beverly Hills", "country": "USA", "founded": 1924, "lat": 34.0696, "lon": -118.3968, "notes": "James Bond, Rocky, The Wizard of Oz"},
        {"studio": "Lionsgate Films", "city": "Santa Monica", "country": "USA", "founded": 1997, "lat": 34.0195, "lon": -118.4912, "notes": "The Hunger Games, John Wick, Saw"},
        {"studio": "A24", "city": "New York City", "country": "USA", "founded": 2012, "lat": 40.7265, "lon": -74.0014, "notes": "Moonlight, Everything Everywhere All at Once"},
        {"studio": "Netflix Studios", "city": "Los Gatos", "country": "USA", "founded": 1997, "lat": 37.2358, "lon": -121.9624, "notes": "Stranger Things, The Irishman, Glass Onion"},
        {"studio": "Pinewood Studios", "city": "Iver Heath", "country": "UK", "founded": 1936, "lat": 51.5477, "lon": -0.5329, "notes": "James Bond, Star Wars, Marvel UK shoots"},
        {"studio": "Shepperton Studios", "city": "Shepperton", "country": "UK", "founded": 1931, "lat": 51.3930, "lon": -0.4702, "notes": "Alien, Gravity, 1917"},
        {"studio": "Elstree Studios", "city": "Borehamwood", "country": "UK", "founded": 1926, "lat": 51.6586, "lon": -0.2798, "notes": "Star Wars original trilogy, Indiana Jones"},
        {"studio": "Ealing Studios", "city": "London", "country": "UK", "founded": 1902, "lat": 51.5096, "lon": -0.3053, "notes": "The Ladykillers, Downton Abbey"},
        {"studio": "Cinecitt\u00e0", "city": "Rome", "country": "Italy", "founded": 1937, "lat": 41.8499, "lon": 12.5738, "notes": "La Dolce Vita, Ben-Hur, Gangs of New York"},
        {"studio": "Bavaria Film", "city": "Munich", "country": "Germany", "founded": 1919, "lat": 48.0896, "lon": 11.5262, "notes": "Das Boot, The NeverEnding Story, Cabaret"},
        {"studio": "Studio Babelsberg", "city": "Potsdam", "country": "Germany", "founded": 1912, "lat": 52.3874, "lon": 13.1201, "notes": "Metropolis, The Grand Budapest Hotel, V for Vendetta"},
        {"studio": "Barrandov Studios", "city": "Prague", "country": "Czech Republic", "founded": 1931, "lat": 50.0377, "lon": 14.3917, "notes": "Mission Impossible, Casino Royale interiors"},
        {"studio": "Bollywood Film City", "city": "Mumbai", "country": "India", "founded": 1911, "lat": 19.1647, "lon": 72.8624, "notes": "Lagaan, Dilwale Dulhania Le Jayenge, 3 Idiots"},
        {"studio": "Ramoji Film City", "city": "Hyderabad", "country": "India", "founded": 1996, "lat": 17.2543, "lon": 78.6808, "notes": "Baahubali, largest film studio complex in the world"},
        {"studio": "Toho Studios", "city": "Tokyo", "country": "Japan", "founded": 1932, "lat": 35.6660, "lon": 139.3960, "notes": "Godzilla, Seven Samurai, Akira Kurosawa films"},
        {"studio": "Shaw Brothers Studio", "city": "Hong Kong", "country": "China", "founded": 1925, "lat": 22.3440, "lon": 114.1220, "notes": "Kung fu classics, 36th Chamber of Shaolin"},
        {"studio": "CJ ENM / KOFIC Studios", "city": "Seoul", "country": "South Korea", "founded": 1995, "lat": 37.5139, "lon": 127.1052, "notes": "Parasite, Oldboy, Train to Busan"},
        {"studio": "Mosfilm", "city": "Moscow", "country": "Russia", "founded": 1920, "lat": 55.7167, "lon": 37.5333, "notes": "Solaris, Stalker, Andrei Rublev"},
        {"studio": "Churubusco Studios", "city": "Mexico City", "country": "Mexico", "founded": 1945, "lat": 19.3533, "lon": -99.1400, "notes": "Spectre, Y Tu Mama Tambien, Roma scenes"},
        {"studio": "Fox Studios Australia", "city": "Sydney", "country": "Australia", "founded": 1998, "lat": -33.8914, "lon": 151.2079, "notes": "The Matrix sequels, Moulin Rouge, Furiosa"},
        {"studio": "Weta Workshop / Stone Street", "city": "Wellington", "country": "New Zealand", "founded": 1987, "lat": -41.3080, "lon": 174.8270, "notes": "Lord of the Rings, Avatar, King Kong"},
        {"studio": "Nu Boyana Film Studios", "city": "Sofia", "country": "Bulgaria", "founded": 1962, "lat": 42.6516, "lon": 23.2846, "notes": "The Expendables, Angel Has Fallen, Hellboy"},
        {"studio": "Nordisk Film", "city": "Copenhagen", "country": "Denmark", "founded": 1906, "lat": 55.6761, "lon": 12.5683, "notes": "Oldest continuously operating film studio"},
        {"studio": "Canal+ / StudioCanal", "city": "Paris", "country": "France", "founded": 1988, "lat": 48.8866, "lon": 2.2844, "notes": "Paddington, Mulholland Drive (distribution)"},
        {"studio": "Nollywood Film Village", "city": "Lagos", "country": "Nigeria", "founded": 1992, "lat": 6.5244, "lon": 3.3792, "notes": "Second largest film industry by volume"},
        {"studio": "Cape Town Film Studios", "city": "Cape Town", "country": "South Africa", "founded": 2010, "lat": -33.8675, "lon": 18.5530, "notes": "Maze Runner, Resident Evil: The Final Chapter"},
        {"studio": "Dino de Laurentiis Studios", "city": "Turin", "country": "Italy", "founded": 1956, "lat": 45.0703, "lon": 7.6869, "notes": "Hannibal, Dune (1984), Barbarella"},
        {"studio": "Estudios Picasso", "city": "Madrid", "country": "Spain", "founded": 2002, "lat": 40.4368, "lon": -3.5786, "notes": "The Impossible, Exodus: Gods and Kings"},
        {"studio": "Amazon MGM Studios", "city": "Culver City", "country": "USA", "founded": 2010, "lat": 34.0209, "lon": -118.3965, "notes": "The Rings of Power, The Boys"},
        {"studio": "Hengdian World Studios", "city": "Hengdian", "country": "China", "founded": 1996, "lat": 29.1500, "lon": 120.2333, "notes": "Largest outdoor film studio in the world"},
        {"studio": "Film City Mumbai (Goregaon)", "city": "Mumbai", "country": "India", "founded": 1978, "lat": 19.1637, "lon": 72.8516, "notes": "Dabangg, countless Bollywood productions"},
        {"studio": "Trollywood (Film i V\u00e4st)", "city": "Trollh\u00e4ttan", "country": "Sweden", "founded": 1997, "lat": 58.2834, "lon": 12.2886, "notes": "Melancholia, Dancer in the Dark (Lars von Trier)"},
        {"studio": "Astra Film Studios", "city": "Bucharest", "country": "Romania", "founded": 1950, "lat": 44.4268, "lon": 26.1025, "notes": "Cold Mountain, The Nun, Wednesday"},
        {"studio": "MediaPro Studios", "city": "Buftea", "country": "Romania", "founded": 1959, "lat": 44.5667, "lon": 25.9500, "notes": "The Brothers Grimm, Borat scenes"},
    ]
    return pd.DataFrame(data)


def _render_studios():
    """Map 1: Hollywood & Major Studios."""
    df = _get_studios()
    st.markdown("#### Hollywood & Major Film Studios")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Studios", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["founded"].min()))
    c4.metric("Newest", int(df["founded"].max()))

    # Chart: studios by country
    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Studios")
    ax.set_title("Film Studios by Country (Top 10)")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    cluster = MarkerCluster().add_to(m)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['studio'])}</b><br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Founded: {row['founded']}<br>"
            f"Notable: {escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=ACCENT_CYAN,
            fill=True,
            fill_color=ACCENT_CYAN,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["studio"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["studio", "city", "country", "founded", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "film_studios.csv", "text/csv",
                       key="dl_studios")


# =====================================================================
# 2. LORD OF THE RINGS LOCATIONS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_lotr_locations():
    data = [
        {"location": "Hobbiton Movie Set", "region": "Matamata, Waikato", "lat": -37.8721, "lon": 175.6830, "scene": "The Shire, Bag End, Green Dragon Inn", "film": "All three films"},
        {"location": "Tongariro National Park", "region": "Central North Island", "lat": -39.2002, "lon": 175.5814, "scene": "Mount Doom / Mordor exteriors", "film": "The Two Towers, Return of the King"},
        {"location": "Mount Sunday", "region": "Canterbury", "lat": -43.5286, "lon": 171.0534, "scene": "Edoras, capital of Rohan", "film": "The Two Towers"},
        {"location": "Kaitoke Regional Park", "region": "Upper Hutt", "lat": -41.0644, "lon": 175.1522, "scene": "Rivendell, home of Elrond", "film": "The Fellowship of the Ring"},
        {"location": "Paradise, Glenorchy", "region": "Otago", "lat": -44.7170, "lon": 168.3830, "scene": "Lothl\u00f3rien, Isengard, Amon Hen", "film": "The Fellowship of the Ring"},
        {"location": "Remarkables Mountain Range", "region": "Queenstown", "lat": -45.0553, "lon": 168.8168, "scene": "Dimrill Dale, Misty Mountains", "film": "The Fellowship of the Ring"},
        {"location": "Weta Workshop", "region": "Miramar, Wellington", "lat": -41.3131, "lon": 174.8113, "scene": "All props, costumes, creatures, miniatures", "film": "All three films"},
        {"location": "Deer Park Heights", "region": "Queenstown", "lat": -45.0244, "lon": 168.6370, "scene": "Rohan refugee trail, warg attack scene", "film": "The Two Towers"},
        {"location": "Closeburn Station", "region": "Queenstown", "lat": -45.0000, "lon": 168.5500, "scene": "Amon Hen, Anduin River", "film": "The Fellowship of the Ring"},
        {"location": "Mavora Lakes", "region": "Southland", "lat": -45.3000, "lon": 168.1833, "scene": "Nen Hithoel, Silverlode River, Fangorn border", "film": "The Fellowship of the Ring"},
        {"location": "Poolburn Reservoir", "region": "Central Otago", "lat": -45.1333, "lon": 169.8667, "scene": "Rohan plains, riders of Rohan charge", "film": "The Two Towers"},
        {"location": "Nelson Boulder", "region": "Nelson", "lat": -41.2706, "lon": 173.2840, "scene": "One Ring replica sculpture (tourist attraction)", "film": "Publicity"},
        {"location": "Putangirua Pinnacles", "region": "Wairarapa", "lat": -41.4425, "lon": 175.2533, "scene": "Dimholt Road, Paths of the Dead entrance", "film": "Return of the King"},
        {"location": "Mount Ngauruhoe", "region": "Tongariro", "lat": -39.1570, "lon": 175.6320, "scene": "Mount Doom close-up shots", "film": "The Two Towers, Return of the King"},
        {"location": "Twizel", "region": "Mackenzie Country", "lat": -44.2580, "lon": 170.1000, "scene": "Battle of Pelennor Fields", "film": "Return of the King"},
        {"location": "Lake Pukaki", "region": "Canterbury", "lat": -44.0833, "lon": 170.1667, "scene": "Lake-town approach scenes", "film": "The Hobbit trilogy"},
        {"location": "Mangaotaki Rocks", "region": "Piopio", "lat": -38.4167, "lon": 174.9000, "scene": "Trollshaw Forest, troll scene", "film": "The Hobbit: An Unexpected Journey"},
        {"location": "Port Waikato", "region": "Waikato", "lat": -37.3833, "lon": 174.7167, "scene": "Mouth of Anduin River", "film": "The Fellowship of the Ring"},
        {"location": "Harcourt Park", "region": "Upper Hutt", "lat": -41.1244, "lon": 175.0533, "scene": "Isengard gardens before destruction", "film": "The Fellowship of the Ring"},
        {"location": "Fernside Lodge", "region": "Featherston", "lat": -41.1167, "lon": 175.3333, "scene": "Lothl\u00f3rien interior forest scenes", "film": "The Fellowship of the Ring"},
        {"location": "Takaka Hill", "region": "Golden Bay", "lat": -41.0167, "lon": 172.8500, "scene": "Chetwood Forest, leaving Bree", "film": "The Fellowship of the Ring"},
        {"location": "Mount Owen", "region": "Nelson Lakes", "lat": -41.5500, "lon": 172.5833, "scene": "Dimrill Dale aerial shots", "film": "The Fellowship of the Ring"},
        {"location": "Rangitikei River", "region": "Manawatu", "lat": -39.9333, "lon": 175.8500, "scene": "River Anduin canyon shots", "film": "The Fellowship of the Ring"},
        {"location": "Lake Alta", "region": "The Remarkables", "lat": -45.0667, "lon": 168.8167, "scene": "Dimrill Dale lakeside", "film": "The Fellowship of the Ring"},
        {"location": "Earnslaw Burn", "region": "Glenorchy", "lat": -44.7667, "lon": 168.4000, "scene": "Isengard flooding, Ent scenes background", "film": "The Two Towers"},
    ]
    return pd.DataFrame(data)


def _render_lotr():
    """Map 2: Lord of the Rings Locations."""
    df = _get_lotr_locations()
    st.markdown("#### Lord of the Rings Filming Locations")
    c1, c2, c3 = st.columns(3)
    c1.metric("Locations", len(df))
    c2.metric("Regions", df["region"].nunique())
    c3.metric("Films Covered", df["film"].nunique())

    # Chart: locations by film
    film_counts = df["film"].value_counts().head(8)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(film_counts.index[::-1], film_counts.values[::-1],
            color=[_color_for(i) for i in range(len(film_counts))])
    ax.set_xlabel("Number of Locations")
    ax.set_title("Filming Locations by Film")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[-41.5, 173.0], zoom=6)
    for idx, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['location'])}</b><br>"
            f"Region: {escape(row['region'])}<br>"
            f"Scene: {escape(row['scene'])}<br>"
            f"Film: {escape(row['film'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=10,
            color=ACCENT_EMERALD,
            fill=True,
            fill_color=ACCENT_EMERALD,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["location"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["location", "region", "scene", "film"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "lotr_locations.csv", "text/csv",
                       key="dl_lotr")


# =====================================================================
# 3. GAME OF THRONES LOCATIONS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_got_locations():
    data = [
        {"location": "Dubrovnik Old Town", "country": "Croatia", "lat": 42.6407, "lon": 18.1082, "scene": "King's Landing exterior walls and streets", "season": "S2-S8"},
        {"location": "Fort Lovrijenac", "country": "Croatia", "lat": 42.6411, "lon": 18.1036, "scene": "The Red Keep exterior", "season": "S2-S8"},
        {"location": "Diocletian's Palace, Split", "country": "Croatia", "lat": 43.5081, "lon": 16.4402, "scene": "Meereen basement (dragon dungeon)", "season": "S4-S5"},
        {"location": "Klis Fortress", "country": "Croatia", "lat": 43.5619, "lon": 16.5236, "scene": "Meereen city exterior", "season": "S4"},
        {"location": "Trsteno Arboretum", "country": "Croatia", "lat": 42.7130, "lon": 17.9780, "scene": "King's Landing gardens (Tyrell scenes)", "season": "S3-S4"},
        {"location": "\u0160ibenik St. James Cathedral", "country": "Croatia", "lat": 43.7358, "lon": 15.8908, "scene": "Iron Bank of Braavos", "season": "S5"},
        {"location": "Dark Hedges", "country": "Northern Ireland", "lat": 55.1348, "lon": -6.3828, "scene": "The King's Road", "season": "S2"},
        {"location": "Castle Ward", "country": "Northern Ireland", "lat": 54.3907, "lon": -5.5841, "scene": "Winterfell courtyard and exteriors", "season": "S1"},
        {"location": "Tollymore Forest Park", "country": "Northern Ireland", "lat": 54.2230, "lon": -5.9330, "scene": "The Haunted Forest, opening scene", "season": "S1"},
        {"location": "Downhill Strand", "country": "Northern Ireland", "lat": 55.1702, "lon": -6.8165, "scene": "Dragonstone beach (burning of the Seven)", "season": "S2"},
        {"location": "Ballintoy Harbour", "country": "Northern Ireland", "lat": 55.2417, "lon": -6.2354, "scene": "Iron Islands harbour, Lordsport", "season": "S2-S3"},
        {"location": "Cushendun Caves", "country": "Northern Ireland", "lat": 55.2115, "lon": -6.0436, "scene": "Shadow baby birth (Melisandre)", "season": "S2"},
        {"location": "Titanic Studios Belfast", "country": "Northern Ireland", "lat": 54.6084, "lon": -5.9009, "scene": "Interior sets: Winterfell, Castle Black, etc.", "season": "S1-S8"},
        {"location": "A\u00eet Benhaddou", "country": "Morocco", "lat": 31.0472, "lon": -7.1299, "scene": "Yunkai, Pentos", "season": "S3"},
        {"location": "Essaouira", "country": "Morocco", "lat": 31.5085, "lon": -9.7595, "scene": "Astapor slave market", "season": "S3"},
        {"location": "Ouarzazate", "country": "Morocco", "lat": 30.9335, "lon": -6.8936, "scene": "Various Essos locations", "season": "S3"},
        {"location": "Bardenas Reales", "country": "Spain", "lat": 42.2056, "lon": -1.5703, "scene": "Dothraki Sea", "season": "S6"},
        {"location": "Alc\u00e1zar of Seville", "country": "Spain", "lat": 37.3826, "lon": -5.9910, "scene": "Water Gardens of Dorne", "season": "S5"},
        {"location": "Girona Cathedral", "country": "Spain", "lat": 41.9871, "lon": 2.8254, "scene": "Great Sept of Baelor, Braavos streets", "season": "S6"},
        {"location": "Gaztelugatxe", "country": "Spain", "lat": 43.4474, "lon": -2.7835, "scene": "Dragonstone island", "season": "S7-S8"},
        {"location": "Castle of Zafra", "country": "Spain", "lat": 40.6850, "lon": -1.5744, "scene": "Tower of Joy", "season": "S6"},
        {"location": "Italica Roman Ruins", "country": "Spain", "lat": 37.4413, "lon": -6.0458, "scene": "Dragonpit, Lannister-Targaryen meeting", "season": "S7"},
        {"location": "Thingvellir National Park", "country": "Iceland", "lat": 64.2559, "lon": -21.1290, "scene": "The Bloody Gate, Eyrie approach", "season": "S4"},
        {"location": "Grj\u00f3tagj\u00e1 Cave", "country": "Iceland", "lat": 65.6265, "lon": -16.8828, "scene": "Jon Snow and Ygritte love scene", "season": "S3"},
        {"location": "Kirkjufell Mountain", "country": "Iceland", "lat": 64.9426, "lon": -23.3072, "scene": "The arrowhead mountain (Beyond the Wall)", "season": "S7"},
        {"location": "Sk\u00f3gafoss Waterfall", "country": "Iceland", "lat": 63.5321, "lon": -19.5115, "scene": "Beyond the Wall landscapes", "season": "S7-S8"},
        {"location": "M\u00fdr\u00edalsjandur", "country": "Iceland", "lat": 65.6830, "lon": -16.8470, "scene": "Beyond the Wall desolate landscape", "season": "S3"},
        {"location": "H\u00f6fn\u00f0in", "country": "Iceland", "lat": 65.6000, "lon": -16.9000, "scene": "White Walker territory approach", "season": "S2-S3"},
        {"location": "Mdina, Malta", "country": "Malta", "lat": 35.8858, "lon": 14.4028, "scene": "King's Landing streets (pilot/S1)", "season": "S1"},
        {"location": "Azure Window, Gozo", "country": "Malta", "lat": 36.0530, "lon": 14.1880, "scene": "Dothraki wedding site (collapsed 2017)", "season": "S1"},
    ]
    return pd.DataFrame(data)


def _render_got():
    """Map 3: Game of Thrones Locations."""
    df = _get_got_locations()
    st.markdown("#### Game of Thrones Filming Locations")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Seasons Covered", "S1-S8")
    c4.metric("Primary Sites", "Croatia & N. Ireland")

    country_colors = {
        "Croatia": "#06b6d4", "Northern Ireland": "#8b5cf6",
        "Morocco": "#f59e0b", "Spain": "#ef4444",
        "Iceland": "#3b82f6", "Malta": "#ec4899",
    }

    # Chart: locations by country
    country_counts = df["country"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    colors = [country_colors.get(c, "#888") for c in country_counts.index[::-1]]
    ax.barh(country_counts.index[::-1], country_counts.values[::-1], color=colors)
    ax.set_xlabel("Number of Locations")
    ax.set_title("Game of Thrones Locations by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[48, 0], zoom=4)
    for _, row in df.iterrows():
        color = country_colors.get(row["country"], "#888")
        popup_html = (
            f"<b>{escape(row['location'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Scene: {escape(row['scene'])}<br>"
            f"Season: {escape(row['season'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["location"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["location", "country", "scene", "season"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "got_locations.csv", "text/csv",
                       key="dl_got")


# =====================================================================
# 4. STAR WARS FILMING SITES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_star_wars_locations():
    data = [
        {"location": "Matmata (Hotel Sidi Driss)", "country": "Tunisia", "lat": 33.5444, "lon": 9.9764, "scene": "Luke Skywalker's home interior, Lars homestead", "film": "A New Hope / Attack of the Clones"},
        {"location": "Ong Jemal", "country": "Tunisia", "lat": 34.0472, "lon": 7.8333, "scene": "Mos Espa podrace arena canyon", "film": "The Phantom Menace"},
        {"location": "Chott el Jerid", "country": "Tunisia", "lat": 33.9167, "lon": 8.4167, "scene": "Binary sunset location, Tatooine desert", "film": "A New Hope"},
        {"location": "Ksar Ouled Soltane", "country": "Tunisia", "lat": 33.0347, "lon": 10.2894, "scene": "Slave quarters on Tatooine", "film": "The Phantom Menace"},
        {"location": "Ksar Hadada", "country": "Tunisia", "lat": 33.1833, "lon": 10.1167, "scene": "Mos Espa streets", "film": "The Phantom Menace"},
        {"location": "Tataouine (city)", "country": "Tunisia", "lat": 32.9297, "lon": 10.4517, "scene": "Namesake of the planet Tatooine", "film": "Inspiration"},
        {"location": "Ajim, Djerba", "country": "Tunisia", "lat": 33.7167, "lon": 10.7500, "scene": "Mos Eisley Cantina exterior", "film": "A New Hope"},
        {"location": "Skellig Michael", "country": "Ireland", "lat": 51.7703, "lon": -10.5386, "scene": "Ahch-To, Luke's island exile", "film": "The Force Awakens / The Last Jedi"},
        {"location": "Malin Head", "country": "Ireland", "lat": 55.3819, "lon": -7.3736, "scene": "Ahch-To additional coastline shots", "film": "The Last Jedi"},
        {"location": "Loop Head", "country": "Ireland", "lat": 52.5600, "lon": -9.9300, "scene": "Ahch-To cliff scenes", "film": "The Last Jedi"},
        {"location": "Redwood National Park", "country": "USA", "lat": 41.2132, "lon": -124.0046, "scene": "Forest Moon of Endor speeder bike chase", "film": "Return of the Jedi"},
        {"location": "Death Valley", "country": "USA", "lat": 36.5323, "lon": -116.9325, "scene": "Tatooine landscape (Mesquite Flat Dunes)", "film": "A New Hope / Return of the Jedi"},
        {"location": "Buttercup Valley (Yuma)", "country": "USA", "lat": 32.7500, "lon": -115.1000, "scene": "Tatooine Sarlacc pit / Jabba's barge", "film": "Return of the Jedi"},
        {"location": "Elstree Studios", "country": "UK", "lat": 51.6586, "lon": -0.2798, "scene": "Interior sets for original trilogy", "film": "Original Trilogy"},
        {"location": "Pinewood Studios", "country": "UK", "lat": 51.5477, "lon": -0.5329, "scene": "Sequel trilogy interior sets", "film": "Sequel Trilogy"},
        {"location": "Puzzlewood Forest", "country": "UK", "lat": 51.7811, "lon": -2.6106, "scene": "Takodana forest, Starkiller Base woods", "film": "The Force Awakens"},
        {"location": "Wadi Rum", "country": "Jordan", "lat": 29.5328, "lon": 35.4082, "scene": "Pasaana desert planet", "film": "The Rise of Skywalker"},
        {"location": "Salar de Uyuni", "country": "Bolivia", "lat": -20.1338, "lon": -67.4891, "scene": "Crait salt planet inspiration", "film": "The Last Jedi"},
        {"location": "Plaza de Espa\u00f1a, Seville", "country": "Spain", "lat": 37.3772, "lon": -5.9869, "scene": "Naboo city Theed, palace approach", "film": "Attack of the Clones"},
        {"location": "Lake Como (Villa Balbianello)", "country": "Italy", "lat": 45.9653, "lon": 9.2042, "scene": "Naboo lake retreat, Anakin & Padme wedding", "film": "Attack of the Clones"},
        {"location": "Caserta Royal Palace", "country": "Italy", "lat": 41.0733, "lon": 14.3269, "scene": "Naboo Royal Palace interiors", "film": "The Phantom Menace / Attack of the Clones"},
        {"location": "Guilin (karst mountains)", "country": "China", "lat": 25.2744, "lon": 110.2900, "scene": "Kashyyyk landscape inspiration (concept art)", "film": "Revenge of the Sith"},
        {"location": "Grindelwald, Switzerland", "country": "Switzerland", "lat": 46.6243, "lon": 8.0413, "scene": "Alderaan mountain landscapes", "film": "Revenge of the Sith"},
        {"location": "Tikal, Guatemala", "country": "Guatemala", "lat": 17.2220, "lon": -89.6237, "scene": "Yavin 4 rebel base jungle approach", "film": "A New Hope"},
        {"location": "Fox Studios Sydney", "country": "Australia", "lat": -33.8914, "lon": 151.2079, "scene": "Prequel trilogy interior sets", "film": "Prequel Trilogy"},
    ]
    return pd.DataFrame(data)


def _render_star_wars():
    """Map 4: Star Wars Filming Sites."""
    df = _get_star_wars_locations()
    st.markdown("#### Star Wars Filming Sites")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Trilogies", "Original, Prequel, Sequel")
    c4.metric("Primary Desert", "Tunisia")

    # Chart: locations by country
    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Locations")
    ax.set_title("Star Wars Filming Locations by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[30, 10], zoom=3)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['location'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Scene: {escape(row['scene'])}<br>"
            f"Film: {escape(row['film'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=10,
            color=ACCENT_AMBER,
            fill=True,
            fill_color=ACCENT_AMBER,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["location"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["location", "country", "scene", "film"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "star_wars_locations.csv", "text/csv",
                       key="dl_starwars")


# =====================================================================
# 5. JAMES BOND LOCATIONS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_bond_locations():
    data = [
        {"location": "MI6 / SIS Building", "city": "London", "country": "UK", "lat": 51.4875, "lon": -0.1245, "film": "GoldenEye, The World Is Not Enough, Skyfall", "scene": "MI6 headquarters on the Thames"},
        {"location": "Aston Martin Factory", "city": "Gaydon", "country": "UK", "lat": 52.2316, "lon": -1.5234, "film": "Various", "scene": "Home of Bond's iconic car"},
        {"location": "Pinewood Studios", "city": "Iver Heath", "country": "UK", "lat": 51.5477, "lon": -0.5329, "film": "All Bond films", "scene": "007 Stage, interior sets"},
        {"location": "Istanbul Grand Bazaar", "city": "Istanbul", "country": "Turkey", "lat": 41.0106, "lon": 28.9684, "film": "Skyfall", "scene": "Motorcycle chase through the bazaar"},
        {"location": "Taj Lake Palace", "city": "Udaipur", "country": "India", "lat": 24.5757, "lon": 73.6803, "film": "Octopussy", "scene": "Floating palace lair"},
        {"location": "Sugarloaf Mountain", "city": "Rio de Janeiro", "country": "Brazil", "lat": -22.9486, "lon": -43.1566, "film": "Moonraker", "scene": "Cable car fight scene"},
        {"location": "Schilthorn (Piz Gloria)", "city": "Murren", "country": "Switzerland", "lat": 46.5579, "lon": 7.8360, "film": "On Her Majesty's Secret Service", "scene": "Blofeld's alpine hideout"},
        {"location": "Furka Pass", "city": "Uri", "country": "Switzerland", "lat": 46.5733, "lon": 8.4150, "film": "Goldfinger", "scene": "DB5 mountain road chase"},
        {"location": "Siena, Palio Race", "city": "Siena", "country": "Italy", "lat": 43.3188, "lon": 11.3308, "film": "Quantum of Solace", "scene": "Rooftop chase during horse race"},
        {"location": "Lake Garda (Villa)", "city": "Malcesine", "country": "Italy", "lat": 45.7619, "lon": 10.8145, "film": "Quantum of Solace", "scene": "Opening car chase along lake roads"},
        {"location": "Venice Grand Canal", "city": "Venice", "country": "Italy", "lat": 45.4344, "lon": 12.3388, "film": "Casino Royale, From Russia with Love", "scene": "Building collapse, gondola scenes"},
        {"location": "Cit\u00e9 des Sciences Paris", "city": "Paris", "country": "France", "lat": 48.8956, "lon": 2.3878, "film": "A View to a Kill", "scene": "Paris chase, Eiffel Tower"},
        {"location": "Monte Carlo Casino", "city": "Monte Carlo", "country": "Monaco", "lat": 43.7396, "lon": 7.4282, "film": "GoldenEye, Never Say Never Again", "scene": "Casino gambling scenes"},
        {"location": "Ngor Beach", "city": "Dakar", "country": "Senegal", "lat": 14.7469, "lon": -17.5143, "film": "Casino Royale", "scene": "Madagascar chase opening scenes (doubles)"},
        {"location": "Karlovy Vary", "city": "Karlovy Vary", "country": "Czech Republic", "lat": 50.2297, "lon": 12.8714, "film": "Casino Royale", "scene": "Casino Royale hotel exteriors"},
        {"location": "Bahamas (Nassau)", "city": "Nassau", "country": "Bahamas", "lat": 25.0443, "lon": -77.3504, "film": "Casino Royale, Thunderball", "scene": "Ocean scenes, beach resort"},
        {"location": "James Bond Island (Khao Phing Kan)", "city": "Phang Nga Bay", "country": "Thailand", "lat": 8.2751, "lon": 98.5011, "film": "The Man with the Golden Gun", "scene": "Scaramanga's island lair"},
        {"location": "Macau (casino district)", "city": "Macau", "country": "China", "lat": 22.1987, "lon": 113.5439, "film": "Skyfall", "scene": "Floating casino, komodo dragon pit"},
        {"location": "Hashima Island (Gunkanjima)", "city": "Nagasaki", "country": "Japan", "lat": 32.6277, "lon": 129.7384, "film": "Skyfall", "scene": "Inspiration for Silva's abandoned island lair"},
        {"location": "Shanghai skyline", "city": "Shanghai", "country": "China", "lat": 31.2397, "lon": 121.4998, "film": "Skyfall", "scene": "Neon-lit skyscraper assassination scene"},
        {"location": "Bregenz Floating Stage", "city": "Bregenz", "country": "Austria", "lat": 47.5031, "lon": 9.7471, "film": "Quantum of Solace", "scene": "Tosca opera performance, shootout"},
        {"location": "Panama City", "city": "Panama City", "country": "Panama", "lat": 8.9824, "lon": -79.5199, "film": "Quantum of Solace", "scene": "Hotel rooftop, city chase"},
        {"location": "Mexico City (D\u00eda de los Muertos)", "city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "film": "Spectre", "scene": "Day of the Dead opening sequence"},
        {"location": "Tangier Medina", "city": "Tangier", "country": "Morocco", "lat": 35.7851, "lon": -5.8130, "film": "The Living Daylights, Spectre", "scene": "Chase through narrow streets"},
        {"location": "Otztal Alps (Ice Q)", "city": "S\u00f6lden", "country": "Austria", "lat": 46.9320, "lon": 10.8690, "film": "Spectre", "scene": "Hoffler Klinik, alpine clinic"},
        {"location": "Altaussee", "city": "Altaussee", "country": "Austria", "lat": 47.6375, "lon": 13.7631, "film": "Spectre", "scene": "Madeleine Swann's childhood home"},
        {"location": "Glen Coe", "city": "Scottish Highlands", "country": "UK", "lat": 56.6833, "lon": -5.1000, "film": "Skyfall", "scene": "Bond's family estate, final battle"},
        {"location": "Hankley Common", "city": "Surrey", "country": "UK", "lat": 51.1667, "lon": -0.7833, "film": "Skyfall", "scene": "Training grounds for secret agents"},
        {"location": "Matera (Sassi)", "city": "Matera", "country": "Italy", "lat": 40.6665, "lon": 16.6044, "film": "No Time to Die", "scene": "Pre-title car and motorcycle chase"},
        {"location": "Port Antonio", "city": "Jamaica", "country": "Jamaica", "lat": 18.1790, "lon": -76.4510, "film": "Dr. No, No Time to Die", "scene": "Bond's Caribbean retreat"},
        {"location": "Faroe Islands", "city": "V\u00e1gar", "country": "Denmark", "lat": 62.0764, "lon": -7.1300, "film": "No Time to Die", "scene": "Villain's secret island base (Safin)"},
        {"location": "Norway (Atlantic Road)", "city": "Averoy", "country": "Norway", "lat": 63.0167, "lon": 7.3500, "film": "No Time to Die", "scene": "Mountain road chase, bridge scenes"},
        {"location": "Cu Chi Tunnels area", "city": "Ho Chi Minh City", "country": "Vietnam", "lat": 11.1421, "lon": 106.4632, "film": "Tomorrow Never Dies", "scene": "Vietnam motorcycle chase"},
        {"location": "Crab Key / Laughing Waters", "city": "Ocho Rios", "country": "Jamaica", "lat": 18.4100, "lon": -77.1000, "film": "Dr. No", "scene": "Honey Ryder emerging from the sea"},
        {"location": "Key West", "city": "Key West", "country": "USA", "lat": 24.5551, "lon": -81.7800, "film": "Licence to Kill", "scene": "Hemingway house, seaplane chase"},
    ]
    return pd.DataFrame(data)


def _render_bond():
    """Map 5: James Bond Locations."""
    df = _get_bond_locations()
    st.markdown("#### James Bond Filming Locations")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Films Referenced", df["film"].str.split(",").explode().str.strip().nunique())
    c4.metric("Continents", "6")

    # Chart: locations by country
    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Locations")
    ax.set_title("James Bond Locations by Country (Top 10)")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[30, 10], zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['location'])}</b><br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Film: {escape(row['film'])}<br>"
            f"Scene: {escape(row['scene'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=ACCENT_VIOLET,
            fill=True,
            fill_color=ACCENT_VIOLET,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["location"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["location", "city", "country", "film", "scene"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "bond_locations.csv", "text/csv",
                       key="dl_bond")


# =====================================================================
# 6. FILM FESTIVALS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_film_festivals():
    data = [
        {"festival": "Cannes Film Festival", "city": "Cannes", "country": "France", "lat": 43.5528, "lon": 7.0174, "founded": 1946, "month": "May", "award": "Palme d'Or"},
        {"festival": "Venice Film Festival", "city": "Venice", "country": "Italy", "lat": 45.3518, "lon": 12.3605, "founded": 1932, "month": "Sep", "award": "Golden Lion"},
        {"festival": "Berlin International Film Festival", "city": "Berlin", "country": "Germany", "lat": 52.5095, "lon": 13.3421, "founded": 1951, "month": "Feb", "award": "Golden Bear"},
        {"festival": "Sundance Film Festival", "city": "Park City", "country": "USA", "lat": 40.6461, "lon": -111.4980, "founded": 1978, "month": "Jan", "award": "Grand Jury Prize"},
        {"festival": "Toronto International Film Festival", "city": "Toronto", "country": "Canada", "lat": 43.6510, "lon": -79.3470, "founded": 1976, "month": "Sep", "award": "People's Choice Award"},
        {"festival": "Tribeca Film Festival", "city": "New York City", "country": "USA", "lat": 40.7195, "lon": -74.0089, "founded": 2002, "month": "Jun", "award": "Audience Award"},
        {"festival": "San Sebasti\u00e1n Film Festival", "city": "San Sebasti\u00e1n", "country": "Spain", "lat": 43.3183, "lon": -1.9812, "founded": 1953, "month": "Sep", "award": "Golden Shell"},
        {"festival": "Locarno Film Festival", "city": "Locarno", "country": "Switzerland", "lat": 46.1670, "lon": 8.7950, "founded": 1946, "month": "Aug", "award": "Golden Leopard"},
        {"festival": "Karlovy Vary International Film Festival", "city": "Karlovy Vary", "country": "Czech Republic", "lat": 50.2297, "lon": 12.8714, "founded": 1946, "month": "Jul", "award": "Crystal Globe"},
        {"festival": "Busan International Film Festival", "city": "Busan", "country": "South Korea", "lat": 35.1605, "lon": 129.1612, "founded": 1996, "month": "Oct", "award": "New Currents Award"},
        {"festival": "Tokyo International Film Festival", "city": "Tokyo", "country": "Japan", "lat": 35.6603, "lon": 139.7292, "founded": 1985, "month": "Oct", "award": "Tokyo Grand Prix"},
        {"festival": "Shanghai International Film Festival", "city": "Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737, "founded": 1993, "month": "Jun", "award": "Golden Goblet Award"},
        {"festival": "Mumbai Film Festival (MAMI)", "city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "founded": 1997, "month": "Oct", "award": "Golden Gateway Award"},
        {"festival": "Cairo International Film Festival", "city": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "founded": 1976, "month": "Nov", "award": "Golden Pyramid"},
        {"festival": "Marrakech International Film Festival", "city": "Marrakech", "country": "Morocco", "lat": 31.6295, "lon": -7.9811, "founded": 2001, "month": "Dec", "award": "Golden Star"},
        {"festival": "FESPACO", "city": "Ouagadougou", "country": "Burkina Faso", "lat": 12.3714, "lon": -1.5197, "founded": 1969, "month": "Feb", "award": "Yennenga Gold Stallion"},
        {"festival": "Durban International Film Festival", "city": "Durban", "country": "South Africa", "lat": -29.8587, "lon": 31.0218, "founded": 1979, "month": "Jul", "award": "Best Feature Film"},
        {"festival": "Melbourne International Film Festival", "city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "founded": 1952, "month": "Aug", "award": "Grand Prize"},
        {"festival": "Sydney Film Festival", "city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "founded": 1954, "month": "Jun", "award": "Sydney Film Prize"},
        {"festival": "Telluride Film Festival", "city": "Telluride", "country": "USA", "lat": 37.9375, "lon": -107.8123, "founded": 1974, "month": "Sep", "award": "Silver Medallion"},
        {"festival": "South by Southwest (SXSW)", "city": "Austin", "country": "USA", "lat": 30.2672, "lon": -97.7431, "founded": 1987, "month": "Mar", "award": "Audience Award"},
        {"festival": "Rotterdam International Film Festival", "city": "Rotterdam", "country": "Netherlands", "lat": 51.9225, "lon": 4.4792, "founded": 1972, "month": "Jan", "award": "Tiger Award"},
        {"festival": "Tallinn Black Nights Film Festival", "city": "Tallinn", "country": "Estonia", "lat": 59.4370, "lon": 24.7536, "founded": 1997, "month": "Nov", "award": "Grand Prix"},
        {"festival": "Mar del Plata International Film Festival", "city": "Mar del Plata", "country": "Argentina", "lat": -38.0055, "lon": -57.5426, "founded": 1954, "month": "Nov", "award": "Astor d'Oro"},
        {"festival": "Guadalajara International Film Festival", "city": "Guadalajara", "country": "Mexico", "lat": 20.6597, "lon": -103.3496, "founded": 1986, "month": "Jun", "award": "Mezcal Award"},
        {"festival": "Havana Film Festival", "city": "Havana", "country": "Cuba", "lat": 23.1136, "lon": -82.3666, "founded": 1979, "month": "Dec", "award": "Grand Coral Prize"},
        {"festival": "Hong Kong International Film Festival", "city": "Hong Kong", "country": "China", "lat": 22.3193, "lon": 114.1694, "founded": 1977, "month": "Apr", "award": "FIPRESCI Prize"},
        {"festival": "Annecy International Animation Film Festival", "city": "Annecy", "country": "France", "lat": 45.8992, "lon": 6.1294, "founded": 1960, "month": "Jun", "award": "Cristal du long m\u00e9trage"},
        {"festival": "Sitges Film Festival", "city": "Sitges", "country": "Spain", "lat": 41.2349, "lon": 1.8068, "founded": 1968, "month": "Oct", "award": "Best Feature Film"},
        {"festival": "Fantastic Fest", "city": "Austin", "country": "USA", "lat": 30.2572, "lon": -97.7431, "founded": 2005, "month": "Sep", "award": "Best Picture"},
    ]
    return pd.DataFrame(data)


def _render_festivals():
    """Map 6: Film Festivals."""
    df = _get_film_festivals()
    st.markdown("#### Major Film Festivals Worldwide")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Festivals", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["founded"].min()))
    c4.metric("Newest", int(df["founded"].max()))

    # Chart: festivals by founding decade
    df_chart = df.copy()
    df_chart["decade"] = (df_chart["founded"] // 10) * 10
    decade_counts = df_chart["decade"].value_counts().sort_index()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.bar([str(d) + "s" for d in decade_counts.index], decade_counts.values,
           color=[_color_for(i) for i in range(len(decade_counts))])
    ax.set_xlabel("Decade")
    ax.set_ylabel("Number of Festivals")
    ax.set_title("Film Festivals by Founding Decade")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['festival'])}</b><br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Founded: {row['founded']}<br>"
            f"Month: {escape(row['month'])}<br>"
            f"Top Award: {escape(row['award'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=10,
            color=ACCENT_PINK,
            fill=True,
            fill_color=ACCENT_PINK,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["festival"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["festival", "city", "country", "founded", "month", "award"]],
                 width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "film_festivals.csv", "text/csv",
                       key="dl_festivals")


# =====================================================================
# 7. FAMOUS MOVIE SCENES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_famous_scenes():
    data = [
        {"movie": "The Shawshank Redemption", "year": 1994, "location": "Ohio State Reformatory", "city": "Mansfield, OH", "country": "USA", "lat": 40.7839, "lon": -82.5074, "scene": "Shawshank State Penitentiary"},
        {"movie": "The Godfather", "year": 1972, "location": "Savoca & Forza d'Agr\u00f2", "city": "Sicily", "country": "Italy", "lat": 37.9556, "lon": 15.3403, "scene": "Michael's Sicilian exile, Bar Vitelli wedding"},
        {"movie": "Breakfast at Tiffany's", "year": 1961, "location": "Tiffany & Co. flagship", "city": "New York City", "country": "USA", "lat": 40.7625, "lon": -73.9735, "scene": "Holly Golightly window-shopping at dawn"},
        {"movie": "Roman Holiday", "year": 1953, "location": "Spanish Steps", "city": "Rome", "country": "Italy", "lat": 41.9060, "lon": 12.4828, "scene": "Princess Anne eating gelato"},
        {"movie": "Inception", "year": 2010, "location": "Rue de Miromesnil fold", "city": "Paris", "country": "France", "lat": 48.8756, "lon": 2.3147, "scene": "City folding dream sequence"},
        {"movie": "The Sound of Music", "year": 1965, "location": "Mirabell Gardens", "city": "Salzburg", "country": "Austria", "lat": 47.8056, "lon": 13.0427, "scene": "Do-Re-Mi song through the gardens"},
        {"movie": "Lost in Translation", "year": 2003, "location": "Park Hyatt Tokyo", "city": "Tokyo", "country": "Japan", "lat": 35.6855, "lon": 139.6922, "scene": "New York Bar panoramic city views"},
        {"movie": "The Third Man", "year": 1949, "location": "Vienna Sewers / Riesenrad", "city": "Vienna", "country": "Austria", "lat": 48.2166, "lon": 16.3964, "scene": "Ferris wheel speech, sewer chase"},
        {"movie": "Midnight in Paris", "year": 2011, "location": "Steps of Sacr\u00e9-C\u0153ur", "city": "Paris", "country": "France", "lat": 48.8867, "lon": 2.3431, "scene": "Gil time-travels from these steps"},
        {"movie": "The Bourne Identity", "year": 2002, "location": "Pont Neuf / Place de la Contrescarpe", "city": "Paris", "country": "France", "lat": 48.8570, "lon": 2.3405, "scene": "Jason Bourne rooftop chase"},
        {"movie": "Before Sunrise", "year": 1995, "location": "Kleines Caf\u00e9 / Albertina", "city": "Vienna", "country": "Austria", "lat": 48.2042, "lon": 16.3686, "scene": "Jesse and C\u00e9line walking Vienna at dawn"},
        {"movie": "La La Land", "year": 2016, "location": "Griffith Observatory", "city": "Los Angeles", "country": "USA", "lat": 34.1184, "lon": -118.3004, "scene": "Mia and Sebastian's planetarium dance"},
        {"movie": "Notting Hill", "year": 1999, "location": "Portobello Road Market", "city": "London", "country": "UK", "lat": 51.5152, "lon": -0.2046, "scene": "Hugh Grant's bookshop neighborhood"},
        {"movie": "The Dark Knight", "year": 2008, "location": "Lower Wacker Drive", "city": "Chicago", "country": "USA", "lat": 41.8866, "lon": -87.6354, "scene": "Batmobile truck chase flip scene"},
        {"movie": "Amélie", "year": 2001, "location": "Caf\u00e9 des Deux Moulins", "city": "Paris", "country": "France", "lat": 48.8849, "lon": 2.3336, "scene": "Am\u00e9lie's workplace caf\u00e9"},
        {"movie": "Rocky", "year": 1976, "location": "Philadelphia Museum of Art Steps", "city": "Philadelphia", "country": "USA", "lat": 39.9654, "lon": -75.1810, "scene": "Iconic training run up the steps"},
        {"movie": "The Truman Show", "year": 1998, "location": "Seaside, FL", "city": "Seaside", "country": "USA", "lat": 30.3204, "lon": -86.1416, "scene": "The entire town of Seahaven"},
        {"movie": "Slumdog Millionaire", "year": 2008, "location": "Chhatrapati Shivaji Terminus", "city": "Mumbai", "country": "India", "lat": 18.9398, "lon": 72.8355, "scene": "Final Bollywood dance number"},
        {"movie": "In the Mood for Love", "year": 2000, "location": "Bangkok Chinatown (for HK doubles)", "city": "Bangkok", "country": "Thailand", "lat": 13.7415, "lon": 100.5112, "scene": "Narrow alley noodle shop scenes"},
        {"movie": "Casablanca", "year": 1942, "location": "Rick's Caf\u00e9 (now reconstructed)", "city": "Casablanca", "country": "Morocco", "lat": 33.5886, "lon": -7.6114, "scene": "Rick's Caf\u00e9 Am\u00e9ricain (studio set, tribute caf\u00e9 exists)"},
        {"movie": "Lawrence of Arabia", "year": 1962, "location": "Wadi Rum", "city": "Aqaba", "country": "Jordan", "lat": 29.5328, "lon": 35.4082, "scene": "Vast desert landscapes of Arabia"},
        {"movie": "The Grand Budapest Hotel", "year": 2014, "location": "G\u00f6rlitzer Warenhaus", "city": "G\u00f6rlitz", "country": "Germany", "lat": 51.1528, "lon": 14.9875, "scene": "Hotel lobby interior, department store"},
        {"movie": "Kill Bill: Vol. 1", "year": 2003, "location": "The House of Blue Leaves", "city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "scene": "Gonpachi restaurant (O-Ren Ishii fight)"},
        {"movie": "Braveheart", "year": 1995, "location": "Glen Nevis Valley", "city": "Fort William", "country": "UK", "lat": 56.7968, "lon": -5.0038, "scene": "Wallace's village, battle scenes"},
        {"movie": "Trainspotting", "year": 1996, "location": "Princes Street & Leith", "city": "Edinburgh", "country": "UK", "lat": 55.9533, "lon": -3.1883, "scene": "Choose life opening run down the street"},
        {"movie": "The Beach", "year": 2000, "location": "Maya Bay, Ko Phi Phi Leh", "city": "Krabi", "country": "Thailand", "lat": 7.6781, "lon": 98.7649, "scene": "Paradise hidden beach community"},
        {"movie": "Indiana Jones and the Last Crusade", "year": 1989, "location": "Al-Khazneh (The Treasury)", "city": "Petra", "country": "Jordan", "lat": 30.3228, "lon": 35.4514, "scene": "Temple of the Holy Grail entrance"},
        {"movie": "Forrest Gump", "year": 1994, "location": "Chippewa Square (bench site)", "city": "Savannah", "country": "USA", "lat": 32.0770, "lon": -81.0948, "scene": "Life is like a box of chocolates bench"},
        {"movie": "Mission: Impossible - Fallout", "year": 2018, "location": "Preikestolen (Pulpit Rock)", "city": "Stavanger", "country": "Norway", "lat": 58.9862, "lon": 6.1905, "scene": "Cliff-edge helicopter fight finale"},
        {"movie": "Blade Runner 2049", "year": 2017, "location": "Origo Film Studios + Budapest", "city": "Budapest", "country": "Hungary", "lat": 47.4979, "lon": 19.0402, "scene": "Dystopian Los Angeles interiors"},
        {"movie": "The Revenant", "year": 2015, "location": "Kananaskis / Spray Lakes", "city": "Alberta", "country": "Canada", "lat": 50.8831, "lon": -115.3755, "scene": "Frontier wilderness, bear attack"},
        {"movie": "Gladiator", "year": 2000, "location": "A\u00eft Benhaddou", "city": "Ouarzazate", "country": "Morocco", "lat": 31.0472, "lon": -7.1299, "scene": "Gladiator training camp, Zucchabar"},
        {"movie": "The Talented Mr. Ripley", "year": 1999, "location": "Ischia & Procida islands", "city": "Naples", "country": "Italy", "lat": 40.7302, "lon": 13.9500, "scene": "Mongibello (fictitious) coastal town"},
        {"movie": "Life of Pi", "year": 2012, "location": "Pondicherry", "city": "Pondicherry", "country": "India", "lat": 11.9416, "lon": 79.8083, "scene": "Pi's childhood home and botanical garden"},
        {"movie": "Skyfall", "year": 2012, "location": "Glen Coe", "city": "Scottish Highlands", "country": "UK", "lat": 56.6833, "lon": -5.1000, "scene": "Bond's ancestral Skyfall Lodge"},
        {"movie": "Harry Potter", "year": 2001, "location": "Glenfinnan Viaduct", "city": "Lochaber", "country": "UK", "lat": 56.8761, "lon": -5.4317, "scene": "Hogwarts Express crossing the viaduct"},
        {"movie": "The Lord of the Rings", "year": 2001, "location": "Hobbiton Movie Set", "city": "Matamata", "country": "New Zealand", "lat": -37.8721, "lon": 175.6830, "scene": "The Shire, Bag End"},
        {"movie": "Mad Max: Fury Road", "year": 2015, "location": "Dorob National Park", "city": "Swakopmund", "country": "Namibia", "lat": -22.6792, "lon": 14.5272, "scene": "The entire Fury Road desert chase"},
        {"movie": "Crouching Tiger, Hidden Dragon", "year": 2000, "location": "Anji Bamboo Forest", "city": "Huzhou", "country": "China", "lat": 30.6342, "lon": 119.6816, "scene": "Bamboo treetop sword fight"},
        {"movie": "The Motorcycle Diaries", "year": 2004, "location": "Machu Picchu", "city": "Cusco", "country": "Peru", "lat": -13.1631, "lon": -72.5450, "scene": "Che Guevara arrives at Machu Picchu"},
    ]
    return pd.DataFrame(data)


def _render_famous_scenes():
    """Map 7: Famous Movie Scenes."""
    df = _get_famous_scenes()
    st.markdown("#### Famous Movie Scenes - Real Locations")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Year Range", f"{df['year'].min()}-{df['year'].max()}")
    c4.metric("Cities", df["city"].nunique())

    # Chart: locations by decade
    df_chart = df.copy()
    df_chart["decade"] = (df_chart["year"] // 10) * 10
    decade_counts = df_chart["decade"].value_counts().sort_index()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.bar([str(d) + "s" for d in decade_counts.index], decade_counts.values,
           color=[_color_for(i) for i in range(len(decade_counts))])
    ax.set_xlabel("Decade")
    ax.set_ylabel("Number of Scenes")
    ax.set_title("Iconic Movie Scenes by Decade")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    cluster = MarkerCluster().add_to(m)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['movie'])} ({row['year']})</b><br>"
            f"Location: {escape(row['location'])}<br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Scene: {escape(row['scene'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=ACCENT_RED,
            fill=True,
            fill_color=ACCENT_RED,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['movie'])} ({row['year']})",
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["movie", "year", "location", "city", "country", "scene"]],
                 width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "famous_movie_scenes.csv", "text/csv",
                       key="dl_famous")


# =====================================================================
# 8. ANIMATION STUDIOS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_animation_studios():
    data = [
        {"studio": "Pixar Animation Studios", "city": "Emeryville", "country": "USA", "lat": 37.8327, "lon": -122.2847, "founded": 1986, "parent": "The Walt Disney Company", "notable": "Toy Story, Finding Nemo, Up, Inside Out"},
        {"studio": "Walt Disney Animation Studios", "city": "Burbank", "country": "USA", "lat": 34.1558, "lon": -118.3253, "founded": 1923, "parent": "The Walt Disney Company", "notable": "Snow White, The Lion King, Frozen, Moana"},
        {"studio": "DreamWorks Animation", "city": "Glendale", "country": "USA", "lat": 34.1425, "lon": -118.2551, "founded": 1994, "parent": "NBCUniversal", "notable": "Shrek, Kung Fu Panda, How to Train Your Dragon"},
        {"studio": "Studio Ghibli", "city": "Koganei, Tokyo", "country": "Japan", "lat": 35.7006, "lon": 139.5026, "founded": 1985, "parent": "Independent", "notable": "Spirited Away, My Neighbor Totoro, Princess Mononoke"},
        {"studio": "Illumination Entertainment", "city": "Santa Monica", "country": "USA", "lat": 34.0195, "lon": -118.4912, "founded": 2007, "parent": "NBCUniversal", "notable": "Despicable Me, Minions, The Secret Life of Pets"},
        {"studio": "Blue Sky Studios", "city": "Greenwich, CT", "country": "USA", "lat": 41.0262, "lon": -73.6282, "founded": 1987, "parent": "Closed (was Disney/Fox)", "notable": "Ice Age, Rio, Ferdinand"},
        {"studio": "Laika Entertainment", "city": "Hillsboro, OR", "country": "USA", "lat": 45.5229, "lon": -122.9898, "founded": 2005, "parent": "Independent", "notable": "Coraline, Kubo and the Two Strings, Missing Link"},
        {"studio": "Aardman Animations", "city": "Bristol", "country": "UK", "lat": 51.4498, "lon": -2.6010, "founded": 1972, "parent": "Independent", "notable": "Wallace & Gromit, Shaun the Sheep, Chicken Run"},
        {"studio": "Industrial Light & Magic (ILM)", "city": "San Francisco", "country": "USA", "lat": 37.7850, "lon": -122.3990, "founded": 1975, "parent": "Lucasfilm / Disney", "notable": "Star Wars VFX, Jurassic Park VFX, Marvel VFX"},
        {"studio": "Toei Animation", "city": "Nerima, Tokyo", "country": "Japan", "lat": 35.7384, "lon": 139.6535, "founded": 1948, "parent": "Toei Company", "notable": "Dragon Ball Z, One Piece, Sailor Moon"},
        {"studio": "Sunrise Inc.", "city": "Suginami, Tokyo", "country": "Japan", "lat": 35.6993, "lon": 139.6369, "founded": 1972, "parent": "Bandai Namco", "notable": "Mobile Suit Gundam, Cowboy Bebop, Code Geass"},
        {"studio": "Madhouse", "city": "Nakano, Tokyo", "country": "Japan", "lat": 35.7076, "lon": 139.6659, "founded": 1972, "parent": "Independent", "notable": "Death Note, One Punch Man, Paprika"},
        {"studio": "Cartoon Saloon", "city": "Kilkenny", "country": "Ireland", "lat": 52.6541, "lon": -7.2448, "founded": 1999, "parent": "Independent", "notable": "The Secret of Kells, Song of the Sea, Wolfwalkers"},
        {"studio": "Folimage", "city": "Valence", "country": "France", "lat": 44.9334, "lon": 4.8924, "founded": 1981, "parent": "Independent", "notable": "A Cat in Paris, Mia and the Migoo"},
        {"studio": "Nelvana", "city": "Toronto", "country": "Canada", "lat": 43.6426, "lon": -79.3871, "founded": 1971, "parent": "Corus Entertainment", "notable": "Babar, Care Bears, Franklin"},
        {"studio": "Sony Pictures Imageworks", "city": "Vancouver", "country": "Canada", "lat": 49.2827, "lon": -123.1207, "founded": 1992, "parent": "Sony Pictures", "notable": "Spider-Verse, Hotel Transylvania, Cloudy with Meatballs"},
        {"studio": "Animal Logic", "city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "founded": 1991, "parent": "Netflix", "notable": "Happy Feet, The LEGO Movie, Legend of the Guardians"},
        {"studio": "Weta Digital (now Weta FX)", "city": "Wellington", "country": "New Zealand", "lat": -41.3131, "lon": 174.8113, "founded": 1993, "parent": "Unity Technologies", "notable": "Lord of the Rings VFX, Avatar, Planet of the Apes"},
        {"studio": "Gaumont Animation", "city": "Paris", "country": "France", "lat": 48.8718, "lon": 2.3316, "founded": 2010, "parent": "Gaumont Film Company", "notable": "F.I.S.T., Lanfeust Quest"},
        {"studio": "Xilam Animation", "city": "Paris", "country": "France", "lat": 48.8800, "lon": 2.3500, "founded": 1999, "parent": "Independent", "notable": "Oggy and the Cockroaches, Zig & Sharko"},
        {"studio": "MAPPA", "city": "Suginami, Tokyo", "country": "Japan", "lat": 35.6986, "lon": 139.6380, "founded": 2011, "parent": "Independent", "notable": "Jujutsu Kaisen, Attack on Titan Final, Chainsaw Man"},
        {"studio": "CoMix Wave Films", "city": "Chiyoda, Tokyo", "country": "Japan", "lat": 35.6938, "lon": 139.7533, "founded": 2007, "parent": "Independent", "notable": "Your Name, Weathering with You (Makoto Shinkai)"},
        {"studio": "Triggerfish Animation", "city": "Cape Town", "country": "South Africa", "lat": -33.9258, "lon": 18.4232, "founded": 1996, "parent": "Independent", "notable": "Khumba, Seal Team, Adventures in Zambezia"},
        {"studio": "Ufotable", "city": "Suginami, Tokyo", "country": "Japan", "lat": 35.7020, "lon": 139.6410, "founded": 2000, "parent": "Independent", "notable": "Demon Slayer, Fate/Stay Night, God Eater"},
        {"studio": "Wit Studio", "city": "Musashino, Tokyo", "country": "Japan", "lat": 35.7175, "lon": 139.5663, "founded": 2012, "parent": "Production I.G sub", "notable": "Attack on Titan S1-S3, Spy x Family, Vinland Saga"},
    ]
    return pd.DataFrame(data)


def _render_animation_studios():
    """Map 8: Animation Studios."""
    df = _get_animation_studios()
    st.markdown("#### Animation Studios Worldwide")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Studios", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["founded"].min()))
    c4.metric("Newest", int(df["founded"].max()))

    # Chart: studios by country
    country_counts = df["country"].value_counts().head(8)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Studios")
    ax.set_title("Animation Studios by Country")
    st.image(_fig_to_bytes(fig), width=800)

    country_colors = {
        "USA": "#3b82f6", "Japan": "#ef4444", "UK": "#8b5cf6",
        "France": "#06b6d4", "Canada": "#10b981", "Ireland": "#f59e0b",
        "Australia": "#f97316", "New Zealand": "#14b8a6", "South Africa": "#ec4899",
    }

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        color = country_colors.get(row["country"], "#888")
        popup_html = (
            f"<b>{escape(row['studio'])}</b><br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Founded: {row['founded']}<br>"
            f"Parent: {escape(row['parent'])}<br>"
            f"Notable: {escape(row['notable'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["studio"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["studio", "city", "country", "founded", "parent", "notable"]],
                 width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "animation_studios.csv", "text/csv",
                       key="dl_animation")


# =====================================================================
# 9. WORLD CINEMA CAPITALS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_cinema_capitals():
    data = [
        {"city": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437, "industry": "Hollywood", "annual_films": 700, "notable_genre": "Blockbusters, Sci-Fi", "iconic_film": "Casablanca"},
        {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "industry": "Bollywood", "annual_films": 1800, "notable_genre": "Musical Drama, Romance", "iconic_film": "Dilwale Dulhania Le Jayenge"},
        {"city": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792, "industry": "Nollywood", "annual_films": 2500, "notable_genre": "Drama, Comedy, Horror", "iconic_film": "The Figurine"},
        {"city": "Hong Kong", "country": "China", "lat": 22.3193, "lon": 114.1694, "industry": "Hong Kong Cinema", "annual_films": 300, "notable_genre": "Martial Arts, Action", "iconic_film": "In the Mood for Love"},
        {"city": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780, "industry": "Hallyuwood", "annual_films": 500, "notable_genre": "Thriller, Horror, Drama", "iconic_film": "Parasite"},
        {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "industry": "Japanese Cinema", "annual_films": 600, "notable_genre": "Anime, Horror, Drama", "iconic_film": "Seven Samurai"},
        {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "industry": "French Cinema", "annual_films": 300, "notable_genre": "New Wave, Art House", "iconic_film": "Am\u00e9lie"},
        {"city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "industry": "British Cinema", "annual_films": 250, "notable_genre": "Period Drama, Comedy", "iconic_film": "The Third Man"},
        {"city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "industry": "German Cinema", "annual_films": 200, "notable_genre": "Expressionism, Art House", "iconic_film": "Metropolis"},
        {"city": "Rome", "country": "Italy", "lat": 41.9028, "lon": 12.4964, "industry": "Italian Cinema", "annual_films": 180, "notable_genre": "Neorealism, Spaghetti Western", "iconic_film": "La Dolce Vita"},
        {"city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "industry": "Mexican Cinema", "annual_films": 200, "notable_genre": "Drama, Dark Comedy", "iconic_film": "Roma"},
        {"city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816, "industry": "Argentine Cinema", "annual_films": 150, "notable_genre": "Drama, Political", "iconic_film": "The Secret in Their Eyes"},
        {"city": "Tehran", "country": "Iran", "lat": 35.6892, "lon": 51.3890, "industry": "Iranian Cinema", "annual_films": 120, "notable_genre": "Art House, Realism", "iconic_film": "A Separation"},
        {"city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686, "industry": "Swedish Cinema", "annual_films": 60, "notable_genre": "Drama, Bergman Legacy", "iconic_film": "The Seventh Seal"},
        {"city": "Copenhagen", "country": "Denmark", "lat": 55.6761, "lon": 12.5683, "industry": "Danish Cinema / Dogme 95", "annual_films": 50, "notable_genre": "Minimalist Drama", "iconic_film": "Festen"},
        {"city": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784, "industry": "Yesilcam / New Turkish Cinema", "annual_films": 180, "notable_genre": "Drama, Historical", "iconic_film": "Winter Sleep"},
        {"city": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "industry": "Egyptian Cinema", "annual_films": 80, "notable_genre": "Drama, Musical", "iconic_film": "Cairo Station"},
        {"city": "Beijing", "country": "China", "lat": 39.9042, "lon": 116.4074, "industry": "Chinese Cinema", "annual_films": 900, "notable_genre": "Wuxia, Drama, Propaganda", "iconic_film": "Farewell My Concubine"},
        {"city": "Taipei", "country": "Taiwan", "lat": 25.0330, "lon": 121.5654, "industry": "Taiwanese New Wave", "annual_films": 70, "notable_genre": "Art House, Social Drama", "iconic_film": "A City of Sadness"},
        {"city": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018, "industry": "Thai Cinema", "annual_films": 150, "notable_genre": "Horror, Martial Arts", "iconic_film": "Uncle Boonmee Who Can Recall His Past Lives"},
        {"city": "Manila", "country": "Philippines", "lat": 14.5995, "lon": 120.9842, "industry": "Filipino Cinema", "annual_films": 100, "notable_genre": "Social Realism, Horror", "iconic_film": "The Woman Who Left"},
        {"city": "Ouagadougou", "country": "Burkina Faso", "lat": 12.3714, "lon": -1.5197, "industry": "Burkinab\u00e9 / Pan-African Cinema", "annual_films": 20, "notable_genre": "Social Drama, FESPACO hub", "iconic_film": "Tilaai"},
        {"city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173, "industry": "Russian Cinema", "annual_films": 200, "notable_genre": "Art House, War", "iconic_film": "Stalker"},
        {"city": "Warsaw", "country": "Poland", "lat": 52.2297, "lon": 21.0122, "industry": "Polish Cinema", "annual_films": 50, "notable_genre": "Drama, Moral Anxiety", "iconic_film": "Ida"},
        {"city": "Prague", "country": "Czech Republic", "lat": 50.0755, "lon": 14.4378, "industry": "Czech New Wave", "annual_films": 60, "notable_genre": "Surrealism, Comedy", "iconic_film": "Closely Watched Trains"},
        {"city": "Kolkata", "country": "India", "lat": 22.5726, "lon": 88.3639, "industry": "Tollywood (Bengali)", "annual_films": 200, "notable_genre": "Art House, Satyajit Ray legacy", "iconic_film": "Pather Panchali"},
        {"city": "Chennai", "country": "India", "lat": 13.0827, "lon": 80.2707, "industry": "Kollywood (Tamil)", "annual_films": 300, "notable_genre": "Action, Musical", "iconic_film": "Kahaani"},
        {"city": "Accra", "country": "Ghana", "lat": 5.6037, "lon": -0.1870, "industry": "Ghallywood", "annual_films": 80, "notable_genre": "Drama, Comedy", "iconic_film": "Azali"},
        {"city": "S\u00e3o Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "industry": "Cinema Novo / Modern Brazilian", "annual_films": 150, "notable_genre": "Social Realism, Crime", "iconic_film": "City of God"},
        {"city": "Wellington", "country": "New Zealand", "lat": -41.2865, "lon": 174.7762, "industry": "Wellywood", "annual_films": 30, "notable_genre": "Fantasy, VFX-driven", "iconic_film": "The Lord of the Rings"},
    ]
    return pd.DataFrame(data)


def _render_cinema_capitals():
    """Map 9: World Cinema Capitals."""
    df = _get_cinema_capitals()
    st.markdown("#### World Cinema Capitals")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Annual Films", f"{int(df['annual_films'].sum()):,}")
    c4.metric("Top Producer", df.loc[df["annual_films"].idxmax(), "city"])

    # Chart: top 10 by annual films
    top10 = df.nlargest(10, "annual_films")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["city"].values[::-1], top10["annual_films"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Annual Films Produced")
    ax.set_title("Top 10 Film-Producing Cities")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    max_films = df["annual_films"].max()
    for _, row in df.iterrows():
        radius = max(6, min(20, row["annual_films"] / max_films * 20))
        popup_html = (
            f"<b>{escape(row['city'])}</b>, {escape(row['country'])}<br>"
            f"Industry: {escape(row['industry'])}<br>"
            f"Annual Films: ~{row['annual_films']}<br>"
            f"Genre Strength: {escape(row['notable_genre'])}<br>"
            f"Iconic Film: {escape(row['iconic_film'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=ACCENT_CYAN,
            fill=True,
            fill_color=ACCENT_CYAN,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['city'])} ({escape(row['industry'])})",
        ).add_to(m)
    _show_map(m)

    st.dataframe(
        df[["city", "country", "industry", "annual_films", "notable_genre", "iconic_film"]],
        width="stretch",
    )
    st.download_button("Download CSV", _df_to_csv(df), "cinema_capitals.csv", "text/csv",
                       key="dl_cinema_capitals")


# =====================================================================
# 10. HORROR MOVIE LOCATIONS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_horror_locations():
    data = [
        {"movie": "The Shining", "year": 1980, "location": "Timberline Lodge", "city": "Mount Hood, OR", "country": "USA", "lat": 45.3311, "lon": -121.7113, "scene": "The Overlook Hotel exterior"},
        {"movie": "The Shining", "year": 1980, "location": "Ahwahnee Hotel (now Majestic)", "city": "Yosemite, CA", "country": "USA", "lat": 37.7468, "lon": -119.5756, "scene": "Interior inspiration for the Overlook"},
        {"movie": "The Exorcist", "year": 1973, "location": "Exorcist Steps (M Street NW)", "city": "Washington D.C.", "country": "USA", "lat": 38.9043, "lon": -77.0710, "scene": "Father Karras falls down the steps"},
        {"movie": "Psycho", "year": 1960, "location": "Universal Studios Bates Motel set", "city": "Universal City, CA", "country": "USA", "lat": 34.1384, "lon": -118.3531, "scene": "Bates Motel and the house on the hill"},
        {"movie": "The Texas Chain Saw Massacre", "year": 1974, "location": "Quick Hill (original house)", "city": "Round Rock, TX", "country": "USA", "lat": 30.5083, "lon": -97.6789, "scene": "Leatherface's farmhouse"},
        {"movie": "Halloween", "year": 1978, "location": "South Pasadena houses", "city": "South Pasadena, CA", "country": "USA", "lat": 34.1161, "lon": -118.1503, "scene": "Haddonfield, Illinois neighborhood streets"},
        {"movie": "A Nightmare on Elm Street", "year": 1984, "location": "1428 N. Genesee Avenue", "city": "Los Angeles, CA", "country": "USA", "lat": 34.0975, "lon": -118.3614, "scene": "Nancy Thompson's house"},
        {"movie": "The Amityville Horror", "year": 1979, "location": "112 Ocean Avenue", "city": "Amityville, NY", "country": "USA", "lat": 40.6660, "lon": -73.4189, "scene": "The haunted DeFeo/Lutz house"},
        {"movie": "Rosemary's Baby", "year": 1968, "location": "The Dakota Building", "city": "New York City", "country": "USA", "lat": 40.7766, "lon": -73.9762, "scene": "The Bramford apartment exterior"},
        {"movie": "The Omen", "year": 1976, "location": "Guildford Cathedral", "city": "Guildford", "country": "UK", "lat": 51.2432, "lon": -0.5840, "scene": "Church where Father Brennan is killed"},
        {"movie": "The Wicker Man", "year": 1973, "location": "Burrowhead", "city": "Dumfries & Galloway", "country": "UK", "lat": 54.6667, "lon": -4.3833, "scene": "Summerisle cliff wicker man burning"},
        {"movie": "An American Werewolf in London", "year": 1981, "location": "Piccadilly Circus", "city": "London", "country": "UK", "lat": 51.5099, "lon": -0.1349, "scene": "Werewolf rampage in central London"},
        {"movie": "28 Days Later", "year": 2002, "location": "Westminster Bridge (deserted)", "city": "London", "country": "UK", "lat": 51.5009, "lon": -0.1218, "scene": "Jim wakes to empty London"},
        {"movie": "The Ring (Ringu)", "year": 1998, "location": "Izu Oshima Island", "city": "Tokyo Prefecture", "country": "Japan", "lat": 34.7500, "lon": 139.3500, "scene": "Sadako's well and origin story"},
        {"movie": "Ju-On: The Grudge", "year": 2002, "location": "Tokorozawa suburban house", "city": "Saitama", "country": "Japan", "lat": 35.7994, "lon": 139.4690, "scene": "The cursed Saeki family house"},
        {"movie": "Nosferatu", "year": 1922, "location": "Orava Castle", "city": "Oravsk\u00fd Podz\u00e1mok", "country": "Slovakia", "lat": 49.2596, "lon": 19.3558, "scene": "Count Orlok's Transylvanian castle"},
        {"movie": "Dracula (1992)", "year": 1992, "location": "Bran Castle", "city": "Bra\u0219ov", "country": "Romania", "lat": 45.5150, "lon": 25.3672, "scene": "Dracula's castle (tourist association)"},
        {"movie": "Suspiria", "year": 1977, "location": "Freiburg Haus zum Walfisch", "city": "Freiburg", "country": "Germany", "lat": 47.9959, "lon": 7.8494, "scene": "Tanz Dance Academy exterior inspiration"},
        {"movie": "The Orphanage", "year": 2007, "location": "Palacio de Partarr\u00edu", "city": "Llanes, Asturias", "country": "Spain", "lat": 43.4189, "lon": -4.7456, "scene": "The orphanage building exterior"},
        {"movie": "REC", "year": 2007, "location": "L'Eixample apartment building", "city": "Barcelona", "country": "Spain", "lat": 41.3874, "lon": 2.1686, "scene": "Quarantined apartment building"},
        {"movie": "Midsommar", "year": 2019, "location": "H\u00e4rga village (set in Hungary)", "city": "Budapest region", "country": "Hungary", "lat": 47.4100, "lon": 19.0800, "scene": "Swedish pagan commune (built set)"},
        {"movie": "The Blair Witch Project", "year": 1999, "location": "Seneca Creek State Park", "city": "Gaithersburg, MD", "country": "USA", "lat": 39.1767, "lon": -77.2276, "scene": "Black Hills Forest, lost footage"},
        {"movie": "Get Out", "year": 2017, "location": "Fairhope / Daphne estates", "city": "Fairhope, AL", "country": "USA", "lat": 30.5227, "lon": -87.9033, "scene": "The Armitage family estate"},
        {"movie": "It (2017)", "year": 2017, "location": "Port Hope", "city": "Port Hope, ON", "country": "Canada", "lat": 43.9515, "lon": -78.2911, "scene": "Town of Derry, Maine exteriors"},
        {"movie": "Hereditary", "year": 2018, "location": "Herriman, UT homes", "city": "Herriman, UT", "country": "USA", "lat": 40.5141, "lon": -112.0330, "scene": "Graham family house exterior"},
    ]
    return pd.DataFrame(data)


def _render_horror():
    """Map 10: Horror Movie Locations."""
    df = _get_horror_locations()
    st.markdown("#### Horror Movie Locations")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Movies", df["movie"].nunique())
    c3.metric("Countries", df["country"].nunique())
    c4.metric("Year Range", f"{df['year'].min()}-{df['year'].max()}")

    # Chart: horror films by decade
    df_chart = df.drop_duplicates(subset="movie").copy()
    df_chart["decade"] = (df_chart["year"] // 10) * 10
    decade_counts = df_chart["decade"].value_counts().sort_index()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.bar([str(d) + "s" for d in decade_counts.index], decade_counts.values,
           color=[ACCENT_RED] * len(decade_counts))
    ax.set_xlabel("Decade")
    ax.set_ylabel("Number of Films")
    ax.set_title("Horror Films by Decade")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['movie'])} ({row['year']})</b><br>"
            f"Location: {escape(row['location'])}<br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Scene: {escape(row['scene'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=10,
            color=ACCENT_RED,
            fill=True,
            fill_color=ACCENT_RED,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['movie'])} ({row['year']})",
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["movie", "year", "location", "city", "country", "scene"]],
                 width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "horror_locations.csv", "text/csv",
                       key="dl_horror")


# =====================================================================
# MAP OPTIONS REGISTRY
# =====================================================================
MAP_OPTIONS = {
    "Hollywood & Major Studios": _render_studios,
    "Lord of the Rings Locations": _render_lotr,
    "Game of Thrones Locations": _render_got,
    "Star Wars Filming Sites": _render_star_wars,
    "James Bond Locations": _render_bond,
    "Film Festivals": _render_festivals,
    "Famous Movie Scenes": _render_famous_scenes,
    "Animation Studios": _render_animation_studios,
    "World Cinema Capitals": _render_cinema_capitals,
    "Horror Movie Locations": _render_horror,
}


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================
def render_cinema_maps_tab():
    """Main entry point for the Cinema & Film Locations Maps tab."""
    st.markdown(
        '<div class="tab-header pink">'
        "<h4>Cinema &amp; Film Maps</h4>"
        "<p>Explore filming locations, studios, festivals, and cinema capitals "
        "from Hollywood blockbusters to world cinema treasures.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    selected_map = st.selectbox(
        "Select map type",
        list(MAP_OPTIONS.keys()),
        key="cinema_maps_select",
    )

    if st.button("Generate Map", key="cinema_maps_generate", type="primary"):
        with st.spinner("Building map..."):
            MAP_OPTIONS[selected_map]()
    else:
        st.info("Select a map type above and click **Generate Map** to explore.")
