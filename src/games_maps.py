# -*- coding: utf-8 -*-
"""
Video Games & Board Games Maps module for TerraScout AI.
Provides 10 interactive map types covering major game studios, esports arenas,
video game museums, arcade culture, board game capitals, chess history,
pinball & retro gaming, game development hubs, real-world game locations,
and gaming conventions. All data is hardcoded for offline reliability.
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

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# =====================================================================
# COLOUR HELPERS & CONSTANTS
# =====================================================================
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
CARD_BG = "#1a2235"
BORDER = "#2a3550"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT_CYAN = "#06b6d4"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_PINK = "#ec4899"
ACCENT_AMBER = "#f59e0b"
ACCENT_EMERALD = "#10b981"
ACCENT_RED = "#ef4444"

CATEGORY_COLORS = [
    "#06b6d4", "#ec4899", "#8b5cf6", "#f59e0b", "#10b981",
    "#ef4444", "#3b82f6", "#f97316", "#14b8a6", "#a855f7",
    "#e11d48", "#84cc16", "#facc15", "#22d3ee", "#c084fc",
]

MAP_MODES = [
    "Major Game Studios",
    "Esports Arenas & Venues",
    "Video Game Museums",
    "Arcade Culture Origins",
    "Board Game Capitals",
    "Chess History",
    "Pinball & Retro Gaming",
    "Game Development Hubs",
    "Real-World Game Locations",
    "Gaming Conventions",
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
            spine.set_color(BORDER)
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


# =====================================================================
# 1. MAJOR GAME STUDIOS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_game_studios():
    data = [
        {"studio": "Nintendo Co., Ltd.", "city": "Kyoto", "country": "Japan", "founded": 1889, "lat": 34.9693, "lon": 135.7557, "notes": "Mario, Zelda, Pokemon. Originally a playing card company"},
        {"studio": "Sony Interactive Entertainment", "city": "Santa Monica", "country": "USA", "founded": 1993, "lat": 34.0195, "lon": -118.4912, "notes": "PlayStation brand, God of War, The Last of Us (via Naughty Dog)"},
        {"studio": "Rockstar North", "city": "Edinburgh", "country": "UK", "founded": 1984, "lat": 55.9533, "lon": -3.1883, "notes": "Grand Theft Auto series, formerly DMA Design (Lemmings)"},
        {"studio": "CD Projekt Red", "city": "Warsaw", "country": "Poland", "founded": 1994, "lat": 52.2297, "lon": 21.0122, "notes": "The Witcher trilogy, Cyberpunk 2077"},
        {"studio": "Valve Corporation", "city": "Bellevue", "country": "USA", "founded": 1996, "lat": 47.6101, "lon": -122.2015, "notes": "Half-Life, Portal, Dota 2, Steam platform"},
        {"studio": "Ubisoft Montreal", "city": "Montreal", "country": "Canada", "founded": 1997, "lat": 45.5256, "lon": -73.5977, "notes": "Assassin's Creed, Far Cry, largest Ubisoft studio"},
        {"studio": "Blizzard Entertainment", "city": "Irvine", "country": "USA", "founded": 1991, "lat": 33.6846, "lon": -117.8265, "notes": "World of Warcraft, Overwatch, Diablo, StarCraft"},
        {"studio": "Electronic Arts (EA)", "city": "Redwood City", "country": "USA", "founded": 1982, "lat": 37.4830, "lon": -122.2322, "notes": "FIFA/EA Sports FC, Madden, Battlefield, The Sims"},
        {"studio": "Bethesda Game Studios", "city": "Rockville", "country": "USA", "founded": 1986, "lat": 39.0840, "lon": -77.1528, "notes": "The Elder Scrolls, Fallout, Starfield"},
        {"studio": "Epic Games", "city": "Cary", "country": "USA", "founded": 1991, "lat": 35.7915, "lon": -78.7811, "notes": "Fortnite, Unreal Engine, Gears of War"},
        {"studio": "Square Enix", "city": "Tokyo", "country": "Japan", "founded": 1975, "lat": 35.6897, "lon": 139.7050, "notes": "Final Fantasy, Dragon Quest, Kingdom Hearts"},
        {"studio": "Capcom", "city": "Osaka", "country": "Japan", "founded": 1979, "lat": 34.6937, "lon": 135.5023, "notes": "Street Fighter, Resident Evil, Monster Hunter"},
        {"studio": "Konami", "city": "Tokyo", "country": "Japan", "founded": 1969, "lat": 35.6580, "lon": 139.7016, "notes": "Metal Gear Solid, Castlevania, Silent Hill, PES"},
        {"studio": "Sega", "city": "Tokyo", "country": "Japan", "founded": 1960, "lat": 35.6614, "lon": 139.7289, "notes": "Sonic the Hedgehog, Yakuza/Like a Dragon, Phantasy Star"},
        {"studio": "Bandai Namco Studios", "city": "Tokyo", "country": "Japan", "founded": 2012, "lat": 35.6280, "lon": 139.7187, "notes": "Tekken, Dark Souls (publisher), Pac-Man, Elden Ring"},
        {"studio": "Naughty Dog", "city": "Santa Monica", "country": "USA", "founded": 1984, "lat": 34.0180, "lon": -118.4695, "notes": "Uncharted, The Last of Us, Crash Bandicoot (original)"},
        {"studio": "Bungie", "city": "Bellevue", "country": "USA", "founded": 1991, "lat": 47.6149, "lon": -122.1921, "notes": "Halo (original trilogy), Destiny, Marathon"},
        {"studio": "BioWare", "city": "Edmonton", "country": "Canada", "founded": 1995, "lat": 53.5461, "lon": -113.4938, "notes": "Mass Effect, Dragon Age, Star Wars: Knights of the Old Republic"},
        {"studio": "FromSoftware", "city": "Tokyo", "country": "Japan", "founded": 1986, "lat": 35.7005, "lon": 139.7726, "notes": "Dark Souls, Bloodborne, Elden Ring, Sekiro"},
        {"studio": "Insomniac Games", "city": "Burbank", "country": "USA", "founded": 1994, "lat": 34.1808, "lon": -118.3090, "notes": "Spider-Man PS4/PS5, Ratchet & Clank, Spyro (original)"},
        {"studio": "Riot Games", "city": "Los Angeles", "country": "USA", "founded": 2006, "lat": 34.0543, "lon": -118.3950, "notes": "League of Legends, Valorant, Teamfight Tactics"},
        {"studio": "Supercell", "city": "Helsinki", "country": "Finland", "founded": 2010, "lat": 60.1699, "lon": 24.9384, "notes": "Clash of Clans, Clash Royale, Brawl Stars"},
        {"studio": "Mojang Studios", "city": "Stockholm", "country": "Sweden", "founded": 2009, "lat": 59.3293, "lon": 18.0686, "notes": "Minecraft, the best-selling video game of all time"},
        {"studio": "Guerrilla Games", "city": "Amsterdam", "country": "Netherlands", "founded": 2000, "lat": 52.3676, "lon": 4.9041, "notes": "Horizon Zero Dawn, Horizon Forbidden West, Killzone"},
        {"studio": "Remedy Entertainment", "city": "Espoo", "country": "Finland", "founded": 1995, "lat": 60.2055, "lon": 24.6559, "notes": "Alan Wake, Control, Max Payne (original), Quantum Break"},
        {"studio": "Larian Studios", "city": "Ghent", "country": "Belgium", "founded": 1996, "lat": 51.0543, "lon": 3.7174, "notes": "Baldur's Gate 3, Divinity: Original Sin series"},
        {"studio": "Rockstar Games (HQ)", "city": "New York City", "country": "USA", "founded": 1998, "lat": 40.7282, "lon": -74.0007, "notes": "GTA, Red Dead Redemption, publishing headquarters"},
        {"studio": "Tencent Games", "city": "Shenzhen", "country": "China", "founded": 2003, "lat": 22.5431, "lon": 114.0579, "notes": "Honor of Kings, PUBG Mobile, major industry investor"},
        {"studio": "miHoYo / HoYoverse", "city": "Shanghai", "country": "China", "founded": 2012, "lat": 31.2304, "lon": 121.4737, "notes": "Genshin Impact, Honkai: Star Rail, Zenless Zone Zero"},
        {"studio": "Atlus", "city": "Tokyo", "country": "Japan", "founded": 1986, "lat": 35.6895, "lon": 139.6917, "notes": "Persona series, Shin Megami Tensei, Catherine"},
        {"studio": "PlatinumGames", "city": "Osaka", "country": "Japan", "founded": 2006, "lat": 34.6937, "lon": 135.5023, "notes": "Bayonetta, NieR: Automata, Metal Gear Rising"},
        {"studio": "Team Cherry", "city": "Adelaide", "country": "Australia", "founded": 2014, "lat": -34.9285, "lon": 138.6007, "notes": "Hollow Knight, Hollow Knight: Silksong indie phenomenon"},
        {"studio": "Santa Monica Studio", "city": "Los Angeles", "country": "USA", "founded": 1999, "lat": 34.0195, "lon": -118.4912, "notes": "God of War series, PlayStation first-party studio"},
        {"studio": "Respawn Entertainment", "city": "Los Angeles", "country": "USA", "founded": 2010, "lat": 34.0219, "lon": -118.3965, "notes": "Apex Legends, Titanfall, Star Wars Jedi series"},
        {"studio": "Sucker Punch Productions", "city": "Bellevue", "country": "USA", "founded": 1997, "lat": 47.6101, "lon": -122.2015, "notes": "Ghost of Tsushima, Infamous series, Sly Cooper"},
    ]
    return pd.DataFrame(data)


def _render_game_studios():
    """Map 1: Major Game Studios worldwide."""
    df = _get_game_studios()
    st.markdown("#### Major Game Studios")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Studios", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["founded"].min()))
    c4.metric("Newest", int(df["founded"].max()))

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Studios")
    ax.set_title("Game Studios by Country (Top 10)")
    st.image(_fig_to_bytes(fig), width=800)

    # Chart: studios founded by decade
    df_temp = df.copy()
    df_temp["decade"] = (df_temp["founded"] // 10) * 10
    decade_counts = df_temp["decade"].value_counts().sort_index()
    fig2, ax2 = _dark_fig(figsize=(10, 4))
    ax2.bar([str(int(d)) + "s" for d in decade_counts.index], decade_counts.values,
            color=[_color_for(i) for i in range(len(decade_counts))])
    ax2.set_xlabel("Decade")
    ax2.set_ylabel("Studios Founded")
    ax2.set_title("Game Studios Founded by Decade")
    for tick in ax2.get_xticklabels():
        tick.set_rotation(45)
    st.image(_fig_to_bytes(fig2), width=800)

    m = _base_map(zoom=2)
    cluster = MarkerCluster().add_to(m)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{html_module.escape(row['studio'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Founded: {row['founded']}<br>"
            f"Notable: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=ACCENT_VIOLET,
            fill=True,
            fill_color=ACCENT_VIOLET,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["studio"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["studio", "city", "country", "founded", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "game_studios.csv", "text/csv",
                       key="dl_game_studios")


# =====================================================================
# 2. ESPORTS ARENAS & VENUES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_esports_arenas():
    data = [
        {"venue": "LoL Park", "city": "Seoul", "country": "South Korea", "lat": 37.5115, "lon": 127.0590, "capacity": 450, "games": "League of Legends LCK", "notes": "Dedicated LCK arena in Jongno-gu district"},
        {"venue": "Giga Arena (OGN Studio)", "city": "Seoul", "country": "South Korea", "lat": 37.5094, "lon": 127.0432, "capacity": 500, "games": "Various esports", "notes": "Historic OGN esports broadcasting studio"},
        {"venue": "Busan Esports Arena", "city": "Busan", "country": "South Korea", "lat": 35.1796, "lon": 129.0756, "capacity": 600, "games": "Overwatch, LoL", "notes": "Multi-game esports venue in Busan"},
        {"venue": "Mercedes-Benz Arena", "city": "Shanghai", "country": "China", "lat": 31.2120, "lon": 121.4816, "capacity": 18000, "games": "LoL Worlds 2020, Dota 2 TI", "notes": "Major esports finals venue in Pudong"},
        {"venue": "National Exhibition Centre (NEC)", "city": "Shanghai", "country": "China", "lat": 31.1919, "lon": 121.3106, "capacity": 12000, "games": "Various esports", "notes": "Hosts ChinaJoy and esports finals"},
        {"venue": "HyperX Arena Las Vegas", "city": "Las Vegas", "country": "USA", "lat": 36.1063, "lon": -115.1711, "capacity": 500, "games": "Various esports", "notes": "First dedicated esports arena on the Vegas Strip"},
        {"venue": "Esports Stadium Arlington", "city": "Arlington", "country": "USA", "lat": 32.7481, "lon": -97.0825, "capacity": 2500, "games": "Various esports", "notes": "Largest dedicated esports facility in North America"},
        {"venue": "LANXESS Arena", "city": "Cologne", "country": "Germany", "lat": 50.9382, "lon": 6.9454, "capacity": 20000, "games": "ESL One Cologne (CS:GO/CS2)", "notes": "Iconic CS venue, cathedral of Counter-Strike"},
        {"venue": "Barclays Center", "city": "Brooklyn", "country": "USA", "lat": 40.6826, "lon": -73.9754, "capacity": 19000, "games": "Overwatch League Grand Finals", "notes": "NBA arena used for major esports finals"},
        {"venue": "Chase Center", "city": "San Francisco", "country": "USA", "lat": 37.7680, "lon": -122.3877, "capacity": 18064, "games": "LoL Worlds, VCT", "notes": "Warriors arena hosting major esports events"},
        {"venue": "Copper Box Arena", "city": "London", "country": "UK", "lat": 51.5465, "lon": -0.0130, "capacity": 7500, "games": "Gfinity, ECS Finals", "notes": "Olympic legacy venue used for UK esports"},
        {"venue": "Zenith Paris", "city": "Paris", "country": "France", "lat": 48.8953, "lon": 2.3935, "capacity": 6300, "games": "LoL EU Finals, Six Invitational", "notes": "Regular host of European esports finals"},
        {"venue": "AccorHotels Arena (Bercy)", "city": "Paris", "country": "France", "lat": 48.8387, "lon": 2.3786, "capacity": 20300, "games": "LoL Worlds 2019 Finals", "notes": "Hosted the legendary FPX vs G2 Worlds final"},
        {"venue": "Makuhari Messe", "city": "Chiba", "country": "Japan", "lat": 35.6484, "lon": 140.0340, "capacity": 9000, "games": "EVO Japan, TGS esports", "notes": "Major convention and esports venue near Tokyo"},
        {"venue": "Saitama Super Arena", "city": "Saitama", "country": "Japan", "lat": 35.8950, "lon": 139.6311, "capacity": 37000, "games": "EVO Japan, LoL", "notes": "One of the largest arenas in Japan"},
        {"venue": "Spodek Arena", "city": "Katowice", "country": "Poland", "lat": 50.2655, "lon": 19.0243, "capacity": 11500, "games": "IEM Katowice (CS2, SC2)", "notes": "Intel Extreme Masters flagship venue, iconic UFO shape"},
        {"venue": "International Convention Centre", "city": "Katowice", "country": "Poland", "lat": 50.2615, "lon": 19.0223, "capacity": 8000, "games": "IEM Katowice overflow", "notes": "Adjacent to Spodek, used for IEM expansion"},
        {"venue": "Riot Games Arena", "city": "Berlin", "country": "Germany", "lat": 52.5061, "lon": 13.3207, "capacity": 800, "games": "LEC (League of Legends EMEA)", "notes": "Dedicated LEC studio in Berlin-Mitte"},
        {"venue": "T1 Headquarters Arena", "city": "Seoul", "country": "South Korea", "lat": 37.5662, "lon": 126.9785, "capacity": 300, "games": "LoL practice/show matches", "notes": "T1/SKT flagship facility with streaming studios"},
        {"venue": "Climate Pledge Arena", "city": "Seattle", "country": "USA", "lat": 47.6222, "lon": -122.3540, "capacity": 17459, "games": "Dota 2 The International", "notes": "Historic TI venue, formerly KeyArena"},
        {"venue": "Rogers Arena", "city": "Vancouver", "country": "Canada", "lat": 49.2778, "lon": -123.1089, "capacity": 18910, "games": "Dota 2 TI8", "notes": "Hosted The International 2018"},
        {"venue": "Singapore Indoor Stadium", "city": "Singapore", "country": "Singapore", "lat": 1.3010, "lon": 103.8742, "capacity": 12000, "games": "Dota 2 TI11, LoL", "notes": "Southeast Asian esports hub"},
        {"venue": "Estadio Akron (Omnilife)", "city": "Guadalajara", "country": "Mexico", "lat": 20.6816, "lon": -103.2555, "capacity": 49850, "games": "LoL events, various esports", "notes": "Used for large-scale Latin American esports"},
        {"venue": "Afreeca Colosseum", "city": "Seoul", "country": "South Korea", "lat": 37.4979, "lon": 127.0276, "capacity": 400, "games": "StarCraft, LoL", "notes": "AfreecaTV dedicated esports studio and arena"},
        {"venue": "Esports Tower", "city": "Tokyo", "country": "Japan", "lat": 35.6938, "lon": 139.7034, "capacity": 300, "games": "Various esports", "notes": "Multi-floor esports facility in Shinjuku"},
        {"venue": "Dreamhall", "city": "Jonkoping", "country": "Sweden", "lat": 57.7826, "lon": 14.1618, "capacity": 10000, "games": "DreamHack events", "notes": "Home of DreamHack LAN parties, historic esports venue"},
        {"venue": "Zenith Munich", "city": "Munich", "country": "Germany", "lat": 48.1775, "lon": 11.6060, "capacity": 5800, "games": "ESL events, Valorant", "notes": "German esports venue for major European events"},
        {"venue": "Qudos Bank Arena", "city": "Sydney", "country": "Australia", "lat": -33.8472, "lon": 151.0698, "capacity": 21032, "games": "IEM Sydney, LoL OPL", "notes": "Australias premier esports arena venue"},
    ]
    return pd.DataFrame(data)


def _render_esports_arenas():
    """Map 2: Esports Arenas & Venues."""
    df = _get_esports_arenas()
    st.markdown("#### Esports Arenas & Venues")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Venues", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Max Capacity", f"{int(df['capacity'].max()):,}")
    c4.metric("Total Seats", f"{int(df['capacity'].sum()):,}")

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Venues")
    ax.set_title("Esports Venues by Country")
    st.image(_fig_to_bytes(fig), width=800)

    # Chart: top venues by capacity
    top_venues = df.nlargest(10, "capacity")
    fig2, ax2 = _dark_fig(figsize=(10, 5))
    ax2.barh(
        top_venues["venue"].values[::-1],
        top_venues["capacity"].values[::-1],
        color=[_color_for(i) for i in range(len(top_venues))],
    )
    ax2.set_xlabel("Capacity")
    ax2.set_title("Top 10 Esports Venues by Capacity")
    st.image(_fig_to_bytes(fig2), width=800)

    m = _base_map(zoom=2)
    cluster = MarkerCluster().add_to(m)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{html_module.escape(row['venue'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Capacity: {row['capacity']:,}<br>"
            f"Games: {html_module.escape(row['games'])}<br>"
            f"Notes: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=ACCENT_CYAN,
            fill=True,
            fill_color=ACCENT_CYAN,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["venue"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["venue", "city", "country", "capacity", "games", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "esports_arenas.csv", "text/csv",
                       key="dl_esports_arenas")


# =====================================================================
# 3. VIDEO GAME MUSEUMS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_game_museums():
    data = [
        {"museum": "National Videogame Museum", "city": "Frisco", "country": "USA", "lat": 33.1507, "lon": -96.8236, "year_opened": 2016, "notes": "Largest video game museum in the US, interactive exhibits"},
        {"museum": "Computerspielemuseum", "city": "Berlin", "country": "Germany", "lat": 52.5128, "lon": 13.4351, "year_opened": 1997, "notes": "One of the first dedicated video game museums in the world"},
        {"museum": "The Strong National Museum of Play", "city": "Rochester", "country": "USA", "lat": 43.1560, "lon": -77.6036, "year_opened": 1969, "notes": "Home of the Video Game Hall of Fame"},
        {"museum": "MuseoGames (CNAM)", "city": "Paris", "country": "France", "lat": 48.8668, "lon": 2.3550, "year_opened": 2010, "notes": "Part of Conservatoire National des Arts et Metiers"},
        {"museum": "National Videogame Museum (UK)", "city": "Sheffield", "country": "UK", "lat": 53.3798, "lon": -1.4686, "year_opened": 2015, "notes": "UK national collection of video game history"},
        {"museum": "Vigamus - Video Game Museum of Rome", "city": "Rome", "country": "Italy", "lat": 41.9137, "lon": 12.4677, "year_opened": 2012, "notes": "Italy first permanent video game museum"},
        {"museum": "Museum of Art and Digital Entertainment (MADE)", "city": "Oakland", "country": "USA", "lat": 37.8044, "lon": -122.2712, "year_opened": 2011, "notes": "Playable exhibits, game preservation non-profit"},
        {"museum": "Helsinki Computer & Game Console Museum", "city": "Helsinki", "country": "Finland", "lat": 60.1699, "lon": 24.9384, "year_opened": 2013, "notes": "Finnish computing and gaming history"},
        {"museum": "Nostalgia Box", "city": "Perth", "country": "Australia", "lat": -31.9505, "lon": 115.8605, "year_opened": 2015, "notes": "Australias first video game console museum"},
        {"museum": "Moscow Museum of Arcade Machines", "city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173, "year_opened": 2007, "notes": "Collection of Soviet-era arcade machines"},
        {"museum": "Nexon Computer Museum", "city": "Jeju City", "country": "South Korea", "lat": 33.4507, "lon": 126.5709, "year_opened": 2013, "notes": "Built by Nexon, covers Korean and world gaming history"},
        {"museum": "Game On Exhibition (Touring)", "city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "year_opened": 2002, "notes": "Major touring exhibition by Barbican Centre"},
        {"museum": "Nintendo Museum", "city": "Uji", "country": "Japan", "lat": 34.8844, "lon": 135.7899, "year_opened": 2024, "notes": "Official Nintendo museum in former Uji Ogura factory"},
        {"museum": "Retro Computer Museum", "city": "Leicester", "country": "UK", "lat": 52.6369, "lon": -1.1398, "year_opened": 2008, "notes": "Hands-on retro computing and gaming exhibits"},
        {"museum": "Museu do Videogame Itinerante", "city": "Sao Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "year_opened": 2014, "notes": "Traveling video game museum across Brazil"},
        {"museum": "Game Science Center", "city": "Berlin", "country": "Germany", "lat": 52.5119, "lon": 13.3907, "year_opened": 2013, "notes": "Interactive technology and gaming exhibits"},
        {"museum": "Centro Studi Videoludici", "city": "Turin", "country": "Italy", "lat": 45.0703, "lon": 7.6869, "year_opened": 2016, "notes": "Italian video game studies and exhibition center"},
        {"museum": "Museum of the Moving Image", "city": "New York City", "country": "USA", "lat": 40.7564, "lon": -73.9237, "year_opened": 1988, "notes": "Extensive video game section alongside film and TV history"},
        {"museum": "International Center for the History of Electronic Games", "city": "Rochester", "country": "USA", "lat": 43.1560, "lon": -77.6036, "year_opened": 2009, "notes": "Archive of 60,000+ video game items at The Strong museum"},
        {"museum": "Mana Bar (Closed)", "city": "Brisbane", "country": "Australia", "lat": -27.4698, "lon": 153.0251, "year_opened": 2010, "notes": "Australias first video game bar, co-founded by Yahtzee Croshaw"},
        {"museum": "Korean Game Museum", "city": "Seongnam", "country": "South Korea", "lat": 37.4449, "lon": 127.1389, "year_opened": 2018, "notes": "Dedicated to Korean gaming history from StarCraft to mobile"},
        {"museum": "Lisbon Game Dev Museum", "city": "Lisbon", "country": "Portugal", "lat": 38.7223, "lon": -9.1393, "year_opened": 2019, "notes": "Portuguese gaming heritage and indie development exhibits"},
    ]
    return pd.DataFrame(data)


def _render_game_museums():
    """Map 3: Video Game Museums."""
    df = _get_game_museums()
    st.markdown("#### Video Game Museums")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Museums", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["year_opened"].min()))
    c4.metric("Newest", int(df["year_opened"].max()))

    # Chart: museums by country
    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Museums")
    ax.set_title("Video Game Museums by Country")
    st.image(_fig_to_bytes(fig), width=800)

    # Chart: museums opened by decade
    df_temp = df.copy()
    df_temp["decade"] = (df_temp["year_opened"] // 10) * 10
    decade_counts = df_temp["decade"].value_counts().sort_index()
    fig2, ax2 = _dark_fig(figsize=(10, 4))
    ax2.bar([str(int(d)) + "s" for d in decade_counts.index], decade_counts.values,
            color=[_color_for(i) for i in range(len(decade_counts))])
    ax2.set_xlabel("Decade")
    ax2.set_ylabel("Museums Opened")
    ax2.set_title("Video Game Museums by Decade Opened")
    st.image(_fig_to_bytes(fig2), width=800)

    m = _base_map(zoom=2)
    cluster = MarkerCluster().add_to(m)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{html_module.escape(row['museum'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Opened: {row['year_opened']}<br>"
            f"Notes: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=ACCENT_EMERALD,
            fill=True,
            fill_color=ACCENT_EMERALD,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["museum"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["museum", "city", "country", "year_opened", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "game_museums.csv", "text/csv",
                       key="dl_game_museums")


# =====================================================================
# 4. ARCADE CULTURE ORIGINS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_arcade_culture():
    data = [
        {"name": "Akihabara Electric Town", "city": "Tokyo", "country": "Japan", "lat": 35.7023, "lon": 139.7745, "type": "District", "notes": "World-famous electronics and arcade district, home of SEGA arcades and game centers"},
        {"name": "Taito Game Station Shinjuku", "city": "Tokyo", "country": "Japan", "lat": 35.6938, "lon": 139.7034, "type": "Arcade", "notes": "Multi-floor arcade in Shinjuku, classic and modern games"},
        {"name": "Den Den Town", "city": "Osaka", "country": "Japan", "lat": 34.6601, "lon": 135.5055, "type": "District", "notes": "Osakas equivalent of Akihabara, retro gaming paradise"},
        {"name": "Namco Namjatown", "city": "Tokyo", "country": "Japan", "lat": 35.7295, "lon": 139.7188, "type": "Theme Park", "notes": "Indoor Bandai Namco theme park in Ikebukuro Sunshine City"},
        {"name": "Super Potato", "city": "Tokyo", "country": "Japan", "lat": 35.7010, "lon": 139.7714, "type": "Retro Shop", "notes": "Legendary retro game store in Akihabara, playable consoles"},
        {"name": "Funspot", "city": "Laconia", "country": "USA", "lat": 43.5055, "lon": -71.4523, "type": "Arcade", "notes": "Largest arcade in the world, featured in King of Kong documentary"},
        {"name": "Chinatown Fair", "city": "New York City", "country": "USA", "lat": 40.7148, "lon": -74.0000, "type": "Arcade", "notes": "Iconic NYC arcade since 1944, fighting game community hub"},
        {"name": "Twin Galaxies (Original)", "city": "Ottumwa", "country": "USA", "lat": 41.0200, "lon": -92.4113, "type": "Arcade/Records", "notes": "Founded 1981, original video game world records authority"},
        {"name": "Galloping Ghost Arcade", "city": "Brookfield", "country": "USA", "lat": 41.8231, "lon": -87.8473, "type": "Arcade", "notes": "Largest arcade in the USA with 900+ games, all on free play"},
        {"name": "Ground Kontrol", "city": "Portland", "country": "USA", "lat": 45.5243, "lon": -122.6782, "type": "Arcade Bar", "notes": "Classic arcade bar with 100+ vintage and modern games"},
        {"name": "Barcade (Original)", "city": "Brooklyn", "country": "USA", "lat": 40.7128, "lon": -73.9536, "type": "Arcade Bar", "notes": "Pioneered the arcade-bar concept in 2004"},
        {"name": "Planet Arcadia", "city": "London", "country": "UK", "lat": 51.5074, "lon": -0.0847, "type": "Arcade", "notes": "London retro gaming and arcade community venue"},
        {"name": "Arcade Club", "city": "Bury", "country": "UK", "lat": 53.5933, "lon": -2.2966, "type": "Arcade", "notes": "UKs largest free-play arcade, 600+ machines across 3 floors"},
        {"name": "Game Over Bar", "city": "Toronto", "country": "Canada", "lat": 43.6544, "lon": -79.4089, "type": "Arcade Bar", "notes": "Retro gaming bar with classic cabinets and craft beer"},
        {"name": "Reset Bar", "city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "type": "Arcade Bar", "notes": "Retro arcade bar in Melbournes CBD"},
        {"name": "Insert Coin(s)", "city": "Lyon", "country": "France", "lat": 45.7640, "lon": 4.8357, "type": "Arcade Bar", "notes": "French retro gaming bar with rotating game library"},
        {"name": "Timezone", "city": "Manila", "country": "Philippines", "lat": 14.5564, "lon": 121.0244, "type": "Arcade Chain", "notes": "Major Southeast Asian arcade chain, malls across Philippines"},
        {"name": "TonTon Club", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3680, "lon": 4.8997, "type": "Arcade Bar", "notes": "Arcade bar with Japanese games and Asian street food"},
        {"name": "Coin-Op Game Room", "city": "San Diego", "country": "USA", "lat": 32.7140, "lon": -117.1628, "type": "Arcade Bar", "notes": "Craft cocktails and classic arcade games in Gaslamp Quarter"},
        {"name": "Versus Barcade", "city": "Quezon City", "country": "Philippines", "lat": 14.6507, "lon": 121.0497, "type": "Arcade Bar", "notes": "Fighting game community hub and retro arcade bar"},
        {"name": "Hey! (Hirose Entertainment Yard)", "city": "Tokyo", "country": "Japan", "lat": 35.6992, "lon": 139.7710, "type": "Arcade", "notes": "Famous Akihabara arcade specializing in retro and STG games"},
        {"name": "Mikado Game Center", "city": "Tokyo", "country": "Japan", "lat": 35.6593, "lon": 139.6984, "type": "Arcade", "notes": "Legendary Shinjuku retro arcade, fighting game tournaments"},
        {"name": "Round1 Arcade", "city": "Tokyo", "country": "Japan", "lat": 35.6580, "lon": 139.7016, "type": "Arcade Chain", "notes": "Major Japanese arcade chain expanding globally, rhythm and crane games"},
        {"name": "Musee Mecanique", "city": "San Francisco", "country": "USA", "lat": 37.8093, "lon": -122.4175, "type": "Museum/Arcade", "notes": "Historic penny arcade museum at Fishermans Wharf, mechanical games from 1800s"},
        {"name": "Retro Game Camp", "city": "Seoul", "country": "South Korea", "lat": 37.5563, "lon": 126.9234, "type": "Retro Shop", "notes": "Korean retro game shop and cafe in Hongdae district"},
        {"name": "Space Station Arcade", "city": "Osaka", "country": "Japan", "lat": 34.6937, "lon": 135.5023, "type": "Arcade", "notes": "Classic Osaka arcade in Namba area, rhythm game focus"},
    ]
    return pd.DataFrame(data)


def _render_arcade_culture():
    """Map 4: Arcade Culture Origins."""
    df = _get_arcade_culture()
    st.markdown("#### Arcade Culture Origins")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())
    c4.metric("In Japan", int((df["country"] == "Japan").sum()))

    type_counts = df["type"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(type_counts.index[::-1], type_counts.values[::-1],
            color=[_color_for(i) for i in range(len(type_counts))])
    ax.set_xlabel("Count")
    ax.set_title("Arcade Locations by Type")
    st.image(_fig_to_bytes(fig), width=800)

    # Chart: arcade locations by country
    country_counts = df["country"].value_counts().head(10)
    fig2, ax2 = _dark_fig(figsize=(10, 4))
    ax2.barh(country_counts.index[::-1], country_counts.values[::-1],
             color=[_color_for(i) for i in range(len(country_counts))])
    ax2.set_xlabel("Locations")
    ax2.set_title("Arcade Locations by Country")
    st.image(_fig_to_bytes(fig2), width=800)

    m = _base_map(center=[35, 100], zoom=3)
    cluster = MarkerCluster().add_to(m)
    type_colors = {t: _color_for(i) for i, t in enumerate(df["type"].unique())}
    for _, row in df.iterrows():
        color = type_colors.get(row["type"], ACCENT_PINK)
        popup_html = (
            f"<b>{html_module.escape(row['name'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Type: {html_module.escape(row['type'])}<br>"
            f"Notes: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["name"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["name", "city", "country", "type", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "arcade_culture.csv", "text/csv",
                       key="dl_arcade_culture")


# =====================================================================
# 5. BOARD GAME CAPITALS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_board_game_capitals():
    data = [
        {"name": "Messe Essen (SPIEL)", "city": "Essen", "country": "Germany", "lat": 51.4323, "lon": 6.9831, "type": "Convention", "notes": "SPIEL Essen: worlds largest board game fair, 200,000+ visitors annually"},
        {"name": "Gen Con (Indiana Convention Center)", "city": "Indianapolis", "country": "USA", "lat": 39.7640, "lon": -86.1626, "type": "Convention", "notes": "Largest tabletop gaming convention in North America, since 1968"},
        {"name": "UK Games Expo", "city": "Birmingham", "country": "UK", "lat": 52.4524, "lon": -1.7296, "type": "Convention", "notes": "Largest tabletop gaming convention in the UK"},
        {"name": "Snakes & Lattes", "city": "Toronto", "country": "Canada", "lat": 43.6649, "lon": -79.3997, "type": "Cafe", "notes": "Pioneering board game cafe, opened 2010, global model"},
        {"name": "Draughts Board Game Cafe", "city": "London", "country": "UK", "lat": 51.5368, "lon": -0.0593, "type": "Cafe", "notes": "Londons first dedicated board game cafe, Haggerston"},
        {"name": "Cafe Meeple", "city": "Bristol", "country": "UK", "lat": 51.4545, "lon": -2.5879, "type": "Cafe", "notes": "Popular UK board game cafe with huge library"},
        {"name": "Spielwiese", "city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "type": "Cafe", "notes": "Berlin board game cafe with 2000+ games library"},
        {"name": "De Tafelberg", "city": "Amsterdam", "country": "Netherlands", "lat": 52.3561, "lon": 4.8932, "type": "Cafe", "notes": "Dutch board game cafe and gaming community hub"},
        {"name": "Le Dernier Bar Avant La Fin Du Monde", "city": "Paris", "country": "France", "lat": 48.8588, "lon": 2.3470, "type": "Cafe", "notes": "Geek-themed bar with extensive board game collection"},
        {"name": "Thirsty Meeples", "city": "Oxford", "country": "UK", "lat": 51.7520, "lon": -1.2577, "type": "Cafe", "notes": "UKs first board game cafe, 2500+ games"},
        {"name": "BoardGameGeek HQ", "city": "Dallas", "country": "USA", "lat": 32.7767, "lon": -96.7970, "type": "Community", "notes": "HQ of the worlds largest board game community website"},
        {"name": "Ravensburger Spieleland", "city": "Meckenbeuren", "country": "Germany", "lat": 47.6943, "lon": 9.5589, "type": "Theme Park", "notes": "Theme park by Ravensburger, board game company since 1883"},
        {"name": "Hasbro Global HQ", "city": "Pawtucket", "country": "USA", "lat": 41.8787, "lon": -71.3826, "type": "HQ", "notes": "Monopoly, Risk, Scrabble, Trivial Pursuit maker"},
        {"name": "Asmodee Group HQ", "city": "Guyancourt", "country": "France", "lat": 48.7733, "lon": 2.0746, "type": "HQ", "notes": "Catan, Ticket to Ride, Pandemic, Dobble publisher"},
        {"name": "Mattel Global HQ", "city": "El Segundo", "country": "USA", "lat": 33.9164, "lon": -118.3996, "type": "HQ", "notes": "UNO, Scrabble (outside NA), Blokus maker"},
        {"name": "Dice Tower Studio", "city": "Miami", "country": "USA", "lat": 25.7617, "lon": -80.1918, "type": "Media", "notes": "Most popular board game media channel, reviews and playthroughs"},
        {"name": "Shut Up & Sit Down Studio", "city": "London", "country": "UK", "lat": 51.5294, "lon": -0.0716, "type": "Media", "notes": "Influential UK board game review website and video channel"},
        {"name": "Jellycat Cafe & Games", "city": "Melbourne", "country": "Australia", "lat": -37.8117, "lon": 144.9663, "type": "Cafe", "notes": "Melbourne board game cafe with 700+ games"},
        {"name": "Dice Cup Cafe", "city": "Nottingham", "country": "UK", "lat": 52.9548, "lon": -1.1581, "type": "Cafe", "notes": "Nottingham board game cafe near Games Workshop HQ"},
        {"name": "Games Workshop HQ", "city": "Nottingham", "country": "UK", "lat": 52.9476, "lon": -1.1473, "type": "HQ", "notes": "Warhammer 40K, Age of Sigmar, miniature wargaming giant"},
        {"name": "Tokyo Board Game Club", "city": "Tokyo", "country": "Japan", "lat": 35.6895, "lon": 139.6917, "type": "Cafe", "notes": "Japanese board game cafe scene, Shibuya area"},
        {"name": "Juegos de la Mesa Redonda", "city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816, "type": "Cafe", "notes": "Popular board game cafe in Argentinas capital"},
        {"name": "Lucky Dice Cafe", "city": "Taipei", "country": "Taiwan", "lat": 25.0330, "lon": 121.5654, "type": "Cafe", "notes": "Taiwanese board game cafe with 1500+ games"},
        {"name": "Boardroom Cafe", "city": "Bangalore", "country": "India", "lat": 12.9716, "lon": 77.5946, "type": "Cafe", "notes": "Indian board game cafe scene, growing tabletop community"},
        {"name": "Fantasy Flight Games HQ", "city": "Roseville", "country": "USA", "lat": 45.0061, "lon": -93.1566, "type": "HQ", "notes": "Arkham Horror, X-Wing Miniatures, Star Wars: Armada publisher"},
        {"name": "Czech Games Edition", "city": "Prague", "country": "Czech Republic", "lat": 50.0755, "lon": 14.4378, "type": "HQ", "notes": "Codenames, Galaxy Trucker, Through the Ages publisher"},
    ]
    return pd.DataFrame(data)


def _render_board_game_capitals():
    """Map 5: Board Game Capitals."""
    df = _get_board_game_capitals()
    st.markdown("#### Board Game Capitals")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())
    c4.metric("Cafes", int((df["type"] == "Cafe").sum()))

    type_counts = df["type"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    colors = [_color_for(i) for i in range(len(type_counts))]
    ax.pie(type_counts.values, labels=type_counts.index, colors=colors,
           autopct="%1.0f%%", textprops={"color": TEXT_PRIMARY})
    ax.set_title("Board Game Locations by Type")
    st.image(_fig_to_bytes(fig), width=600)

    # Chart: locations by country
    country_counts = df["country"].value_counts().head(10)
    fig2, ax2 = _dark_fig(figsize=(10, 4))
    ax2.barh(country_counts.index[::-1], country_counts.values[::-1],
             color=[_color_for(i) for i in range(len(country_counts))])
    ax2.set_xlabel("Locations")
    ax2.set_title("Board Game Locations by Country")
    st.image(_fig_to_bytes(fig2), width=800)

    m = _base_map(zoom=2)
    cluster = MarkerCluster().add_to(m)
    type_colors = {t: _color_for(i) for i, t in enumerate(df["type"].unique())}
    for _, row in df.iterrows():
        color = type_colors.get(row["type"], ACCENT_AMBER)
        popup_html = (
            f"<b>{html_module.escape(row['name'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Type: {html_module.escape(row['type'])}<br>"
            f"Notes: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["name"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["name", "city", "country", "type", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "board_game_capitals.csv", "text/csv",
                       key="dl_board_game_capitals")


# =====================================================================
# 6. CHESS HISTORY
# =====================================================================
@st.cache_data(ttl=3600)
def _get_chess_history():
    data = [
        {"name": "Cafe de la Regence", "city": "Paris", "country": "France", "lat": 48.8606, "lon": 2.3376, "type": "Historic Cafe", "notes": "Most famous chess cafe 18th-19th century, Philidor, Napoleon, Voltaire played here"},
        {"name": "Simpsons-in-the-Strand", "city": "London", "country": "UK", "lat": 51.5107, "lon": -0.1200, "type": "Historic Cafe", "notes": "Grand Divan chess room 1828-1903, Morphy and Steinitz played here"},
        {"name": "Marshall Chess Club", "city": "New York City", "country": "USA", "lat": 40.7328, "lon": -73.9988, "type": "Chess Club", "notes": "Founded 1915 by Frank Marshall, Bobby Fischer played here as a teen"},
        {"name": "Reykjavik City Hall (1972 Match)", "city": "Reykjavik", "country": "Iceland", "lat": 64.1466, "lon": -21.9426, "type": "Championship", "notes": "Fischer vs Spassky 1972 World Championship, Match of the Century"},
        {"name": "Tchigirin Chess Club", "city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173, "type": "Chess Club", "notes": "Historic Russian chess club, Soviet chess school tradition"},
        {"name": "Central Chess Club of Moscow", "city": "Moscow", "country": "Russia", "lat": 55.7608, "lon": 37.6033, "type": "Chess Club", "notes": "Soviet-era chess headquarters, Karpov and Kasparov trained here"},
        {"name": "Bobby Fischer Birthplace", "city": "Chicago", "country": "USA", "lat": 41.8781, "lon": -87.6298, "type": "Historic Site", "notes": "Born March 9 1943, became youngest US champion at 14"},
        {"name": "Magnus Carlsen Hometown", "city": "Tonsberg", "country": "Norway", "lat": 59.2671, "lon": 10.4076, "type": "Hometown", "notes": "Birthplace of Magnus Carlsen, worlds highest rated player ever"},
        {"name": "Garry Kasparov Birthplace", "city": "Baku", "country": "Azerbaijan", "lat": 40.4093, "lon": 49.8671, "type": "Birthplace", "notes": "Born 1963, youngest undisputed World Champion at 22"},
        {"name": "Cafe Central", "city": "Vienna", "country": "Austria", "lat": 48.2106, "lon": 16.3654, "type": "Historic Cafe", "notes": "Legendary Viennese chess cafe, Freud and Trotsky played here"},
        {"name": "Seville Championship Venue (1987)", "city": "Seville", "country": "Spain", "lat": 37.3886, "lon": -5.9823, "type": "Championship", "notes": "Kasparov vs Karpov 1987 World Championship match"},
        {"name": "Hall of Columns Moscow (1985 Match)", "city": "Moscow", "country": "Russia", "lat": 55.7612, "lon": 37.6084, "type": "Championship", "notes": "Kasparov vs Karpov 1985, Kasparov becomes champion"},
        {"name": "Elista Chess City", "city": "Elista", "country": "Russia", "lat": 46.3078, "lon": 44.2558, "type": "Chess City", "notes": "Chess City built for 1998 Olympiad by Kirsan Ilyumzhinov"},
        {"name": "Tromso Chess Olympiad Venue (2014)", "city": "Tromso", "country": "Norway", "lat": 69.6496, "lon": 18.9560, "type": "Championship", "notes": "2014 Chess Olympiad, northernmost major chess event"},
        {"name": "Chennai FIDE WC (2013)", "city": "Chennai", "country": "India", "lat": 13.0827, "lon": 80.2707, "type": "Championship", "notes": "Carlsen vs Anand 2013, Carlsen becomes World Champion"},
        {"name": "Linares Chess Tournament Venue", "city": "Linares", "country": "Spain", "lat": 38.0953, "lon": -3.6361, "type": "Tournament", "notes": "Linares super-tournament, Wimbledon of Chess 1978-2010"},
        {"name": "Wijk aan Zee (Tata Steel)", "city": "Wijk aan Zee", "country": "Netherlands", "lat": 52.4944, "lon": 4.6003, "type": "Tournament", "notes": "Annual Tata Steel Masters, top super-tournament since 1938"},
        {"name": "Saint Louis Chess Club", "city": "Saint Louis", "country": "USA", "lat": 38.6270, "lon": -90.1994, "type": "Chess Club", "notes": "Americas chess capital, hosts US Championship, Sinquefield Cup"},
        {"name": "Viswanathan Anand Hometown", "city": "Chennai", "country": "India", "lat": 13.0827, "lon": 80.2707, "type": "Hometown", "notes": "Hometown of Vishy Anand, 5-time World Champion, Indian chess legend"},
        {"name": "Astana FIDE WC (2023)", "city": "Astana", "country": "Kazakhstan", "lat": 51.1694, "lon": 71.4491, "type": "Championship", "notes": "Ding Liren vs Nepomniachtchi 2023, first Chinese World Champion"},
        {"name": "Dubai Expo Chess (2021 WC)", "city": "Dubai", "country": "UAE", "lat": 25.1972, "lon": 55.2744, "type": "Championship", "notes": "Carlsen vs Nepomniachtchi 2021 World Championship match"},
        {"name": "Jose Raul Capablanca Club", "city": "Havana", "country": "Cuba", "lat": 23.1136, "lon": -82.3666, "type": "Chess Club", "notes": "Named after Cuban WC champion, Havana chess tradition since 1921"},
        {"name": "Mechelen Steinitz Birthplace", "city": "Prague", "country": "Czech Republic", "lat": 50.0755, "lon": 14.4378, "type": "Birthplace", "notes": "Birthplace of Wilhelm Steinitz, first official World Champion 1886"},
        {"name": "Biel Chess Festival Venue", "city": "Biel", "country": "Switzerland", "lat": 47.1376, "lon": 7.2427, "type": "Tournament", "notes": "Annual Biel chess festival, one of Europes top tournaments since 1968"},
        {"name": "Ding Liren Hometown", "city": "Wenzhou", "country": "China", "lat": 28.0015, "lon": 120.6722, "type": "Hometown", "notes": "Hometown of Ding Liren, 2023 World Chess Champion"},
        {"name": "Anatoly Karpov Birthplace", "city": "Zlatoust", "country": "Russia", "lat": 55.1715, "lon": 59.6722, "type": "Birthplace", "notes": "Birthplace of 12th World Champion, FIDE champion 1975-1985"},
        {"name": "Mikhail Botvinnik Institute", "city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173, "type": "Historic Site", "notes": "School of Botvinnik, trained Karpov and Kasparov, Soviet chess patriarch"},
    ]
    return pd.DataFrame(data)


def _render_chess_history():
    """Map 6: Chess History."""
    df = _get_chess_history()
    st.markdown("#### Chess History")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())
    c4.metric("Championships", int((df["type"] == "Championship").sum()))

    type_counts = df["type"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(type_counts.index[::-1], type_counts.values[::-1],
            color=[_color_for(i) for i in range(len(type_counts))])
    ax.set_xlabel("Count")
    ax.set_title("Chess Locations by Type")
    st.image(_fig_to_bytes(fig), width=800)

    # Chart: chess locations by country
    country_counts = df["country"].value_counts().head(10)
    fig2, ax2 = _dark_fig(figsize=(10, 4))
    ax2.barh(country_counts.index[::-1], country_counts.values[::-1],
             color=[_color_for(i) for i in range(len(country_counts))])
    ax2.set_xlabel("Locations")
    ax2.set_title("Chess History Locations by Country")
    st.image(_fig_to_bytes(fig2), width=800)

    m = _base_map(center=[48, 20], zoom=3)
    cluster = MarkerCluster().add_to(m)
    type_colors = {t: _color_for(i) for i, t in enumerate(df["type"].unique())}
    for _, row in df.iterrows():
        color = type_colors.get(row["type"], ACCENT_AMBER)
        popup_html = (
            f"<b>{html_module.escape(row['name'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Type: {html_module.escape(row['type'])}<br>"
            f"Notes: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["name"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["name", "city", "country", "type", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "chess_history.csv", "text/csv",
                       key="dl_chess_history")


# =====================================================================
# 7. PINBALL & RETRO GAMING
# =====================================================================
@st.cache_data(ttl=3600)
def _get_pinball_retro():
    data = [
        {"name": "Pacific Pinball Museum", "city": "Alameda", "country": "USA", "lat": 37.7652, "lon": -122.2416, "type": "Museum", "notes": "90+ playable pinball machines from 1879 to present"},
        {"name": "Pinball Hall of Fame", "city": "Las Vegas", "country": "USA", "lat": 36.1108, "lon": -115.1531, "type": "Museum", "notes": "Largest pinball museum in the world, 200+ machines"},
        {"name": "Silverball Museum", "city": "Asbury Park", "country": "USA", "lat": 40.2204, "lon": -74.0001, "type": "Museum", "notes": "Beachside pinball museum, 600+ machines on free play"},
        {"name": "Flippermuseum", "city": "Neuwied", "country": "Germany", "lat": 50.4268, "lon": 7.4618, "type": "Museum", "notes": "German pinball museum with 80+ machines"},
        {"name": "Stern Pinball Factory", "city": "Elk Grove Village", "country": "USA", "lat": 42.0072, "lon": -87.9709, "type": "Factory", "notes": "Last remaining large-scale pinball manufacturer in the world"},
        {"name": "Dutch Pinball Museum", "city": "Rotterdam", "country": "Netherlands", "lat": 51.9225, "lon": 4.4792, "type": "Museum", "notes": "Rotterdam pinball collection with 40+ playable machines"},
        {"name": "Budapest Pinball Museum", "city": "Budapest", "country": "Hungary", "lat": 47.4979, "lon": 19.0402, "type": "Museum", "notes": "130+ pinball machines from 1871 to modern era"},
        {"name": "Retro Game Base", "city": "Warsaw", "country": "Poland", "lat": 52.2319, "lon": 21.0067, "type": "Museum", "notes": "Polish retro gaming museum with playable vintage consoles"},
        {"name": "Computerspielemuseum", "city": "Berlin", "country": "Germany", "lat": 52.5128, "lon": 13.4351, "type": "Museum", "notes": "German video game museum, Pong to modern VR exhibits"},
        {"name": "Free Play Bar & Arcade", "city": "Providence", "country": "USA", "lat": 41.8236, "lon": -71.4222, "type": "Arcade Bar", "notes": "Pinball and retro arcade bar, 50+ machines"},
        {"name": "Bally Midway Birthplace", "city": "Chicago", "country": "USA", "lat": 41.8819, "lon": -87.6278, "type": "Historic Site", "notes": "Where Bally and Midway pinball/arcade companies were headquartered"},
        {"name": "National Pinball Museum (Closed)", "city": "Baltimore", "country": "USA", "lat": 39.2904, "lon": -76.6122, "type": "Museum", "notes": "Historic pinball museum, collection now distributed"},
        {"name": "Arcade Vintage Museum", "city": "Petrer", "country": "Spain", "lat": 38.4881, "lon": -0.7677, "type": "Museum", "notes": "Spanish retro gaming and arcade museum in Alicante region"},
        {"name": "Replay Amusement Museum", "city": "Tarpon Springs", "country": "USA", "lat": 28.1461, "lon": -82.7568, "type": "Museum", "notes": "Florida vintage amusement and pinball museum"},
        {"name": "Nostalgia Box", "city": "Perth", "country": "Australia", "lat": -31.9505, "lon": 115.8605, "type": "Museum", "notes": "Australian retro console and gaming museum"},
        {"name": "Game Masters Exhibition (ACMI)", "city": "Melbourne", "country": "Australia", "lat": -37.8180, "lon": 144.9691, "type": "Exhibition", "notes": "ACMI traveling exhibition on game history and design"},
        {"name": "Klassik Pinball Museum", "city": "Sturtevant", "country": "USA", "lat": 42.6978, "lon": -87.8945, "type": "Museum", "notes": "Wisconsin pinball museum with rare vintage machines"},
        {"name": "Flippaut Flippermuseum", "city": "Schwerin", "country": "Germany", "lat": 53.6355, "lon": 11.4012, "type": "Museum", "notes": "Northern German pinball museum with classic European machines"},
        {"name": "Retro Games Museum", "city": "Bucharest", "country": "Romania", "lat": 44.4268, "lon": 26.1025, "type": "Museum", "notes": "Romanian retro gaming museum with Eastern European gaming artifacts"},
        {"name": "Arcade Odyssey", "city": "Miami", "country": "USA", "lat": 25.7617, "lon": -80.1918, "type": "Arcade", "notes": "Miami retro arcade with Japanese imports and fighting game community"},
        {"name": "Museum of Soviet Arcade Machines (SPB)", "city": "Saint Petersburg", "country": "Russia", "lat": 59.9343, "lon": 30.3351, "type": "Museum", "notes": "Branch of Moscow museum with playable Soviet-era arcade machines"},
    ]
    return pd.DataFrame(data)


def _render_pinball_retro():
    """Map 7: Pinball & Retro Gaming."""
    df = _get_pinball_retro()
    st.markdown("#### Pinball & Retro Gaming")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Museums", int((df["type"] == "Museum").sum()))
    c4.metric("In USA", int((df["country"] == "USA").sum()))

    # Chart: locations by type
    type_counts = df["type"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(type_counts.index[::-1], type_counts.values[::-1],
            color=[_color_for(i) for i in range(len(type_counts))])
    ax.set_xlabel("Count")
    ax.set_title("Pinball & Retro Locations by Type")
    st.image(_fig_to_bytes(fig), width=800)

    # Chart: locations by country
    country_counts = df["country"].value_counts().head(8)
    fig2, ax2 = _dark_fig(figsize=(10, 4))
    colors = [_color_for(i) for i in range(len(country_counts))]
    ax2.pie(country_counts.values, labels=country_counts.index, colors=colors,
            autopct="%1.0f%%", textprops={"color": TEXT_PRIMARY})
    ax2.set_title("Pinball & Retro by Country")
    st.image(_fig_to_bytes(fig2), width=600)

    m = _base_map(center=[38, -40], zoom=3)
    cluster = MarkerCluster().add_to(m)
    type_colors = {t: _color_for(i) for i, t in enumerate(df["type"].unique())}
    for _, row in df.iterrows():
        color = type_colors.get(row["type"], ACCENT_RED)
        popup_html = (
            f"<b>{html_module.escape(row['name'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Type: {html_module.escape(row['type'])}<br>"
            f"Notes: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["name"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["name", "city", "country", "type", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "pinball_retro.csv", "text/csv",
                       key="dl_pinball_retro")


# =====================================================================
# 8. GAME DEVELOPMENT HUBS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_game_dev_hubs():
    data = [
        {"hub": "San Francisco / Bay Area", "city": "San Francisco", "country": "USA", "lat": 37.7749, "lon": -122.4194, "studios_estimate": 500, "notes": "EA, Zynga, Roblox, Niantic, 2K Games, many indie studios"},
        {"hub": "Los Angeles / Southern California", "city": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437, "studios_estimate": 400, "notes": "Riot, Naughty Dog, Insomniac, Respawn, Treyarch, Infinity Ward"},
        {"hub": "Seattle / Bellevue", "city": "Seattle", "country": "USA", "lat": 47.6062, "lon": -122.3321, "studios_estimate": 250, "notes": "Valve, Bungie, Nintendo of America, Sucker Punch, Xbox/343i"},
        {"hub": "Tokyo Game District", "city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "studios_estimate": 600, "notes": "Nintendo, Square Enix, Capcom, Konami, Sega, FromSoftware, Bandai Namco"},
        {"hub": "Osaka Game Corridor", "city": "Osaka", "country": "Japan", "lat": 34.6937, "lon": 135.5023, "studios_estimate": 150, "notes": "Capcom HQ, PlatinumGames, SNK, key fighting game development hub"},
        {"hub": "Seoul Pangyo Techno Valley", "city": "Seoul", "country": "South Korea", "lat": 37.3948, "lon": 127.1112, "studios_estimate": 300, "notes": "Nexon, NCSoft, Netmarble, Smilegate, Krafton (PUBG), Pearl Abyss"},
        {"hub": "Montreal Game Cluster", "city": "Montreal", "country": "Canada", "lat": 45.5017, "lon": -73.5673, "studios_estimate": 280, "notes": "Ubisoft Montreal, Warner Bros. Montreal, Eidos-Montreal, Behaviour"},
        {"hub": "Helsinki / Finland Hub", "city": "Helsinki", "country": "Finland", "lat": 60.1699, "lon": 24.9384, "studios_estimate": 120, "notes": "Supercell, Remedy, Rovio, Housemarque, Colossal Order, Small Giant"},
        {"hub": "Stockholm / Sweden Hub", "city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686, "studios_estimate": 100, "notes": "Mojang, DICE, Paradox, Avalanche, King, Sharkmob"},
        {"hub": "London Game Scene", "city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "studios_estimate": 200, "notes": "Rocksteady, Sports Interactive, Splash Damage, Media Molecule"},
        {"hub": "Dundee / Edinburgh Scotland", "city": "Dundee", "country": "UK", "lat": 56.4620, "lon": -2.9707, "studios_estimate": 50, "notes": "Rockstar North, 4J Studios, Ninja Kiwi, Abertay University game design"},
        {"hub": "Shenzhen Tech Hub", "city": "Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579, "studios_estimate": 400, "notes": "Tencent HQ, many mobile game studios, hardware integration"},
        {"hub": "Shanghai Game Valley", "city": "Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737, "studios_estimate": 350, "notes": "miHoYo, Giant Network, Lilith Games, Yostar"},
        {"hub": "Austin Game Dev", "city": "Austin", "country": "USA", "lat": 30.2672, "lon": -97.7431, "studios_estimate": 100, "notes": "id Software, Retro Studios, Bioware Austin, Certain Affinity"},
        {"hub": "Kyoto Game Hub", "city": "Kyoto", "country": "Japan", "lat": 34.9850, "lon": 135.7586, "studios_estimate": 60, "notes": "Nintendo HQ, key console development and design center"},
        {"hub": "Warsaw / Poland Hub", "city": "Warsaw", "country": "Poland", "lat": 52.2297, "lon": 21.0122, "studios_estimate": 80, "notes": "CD Projekt Red, Techland, 11 bit studios, People Can Fly"},
        {"hub": "Guildford Game Corridor", "city": "Guildford", "country": "UK", "lat": 51.2362, "lon": -0.5704, "studios_estimate": 70, "notes": "EA Criterion, Hello Games, Supermassive, Media Molecule, Bullfrog legacy"},
        {"hub": "Toronto Game Hub", "city": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832, "studios_estimate": 90, "notes": "Ubisoft Toronto, Xbox Game Studios Toronto, DrinkBox, Capybara"},
        {"hub": "Bengaluru India Hub", "city": "Bengaluru", "country": "India", "lat": 12.9716, "lon": 77.5946, "studios_estimate": 60, "notes": "Growing Indian game development scene, Zynga India, Moonfrog Labs"},
        {"hub": "Singapore Game Hub", "city": "Singapore", "country": "Singapore", "lat": 1.3521, "lon": 103.8198, "studios_estimate": 40, "notes": "Ubisoft Singapore, Koei Tecmo, Bandai Namco Asia HQ"},
        {"hub": "Berlin Indie Hub", "city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "studios_estimate": 80, "notes": "Wooga, Kolibri, Yager, thriving indie scene, A MAZE festival"},
        {"hub": "Hamburg Games Hub", "city": "Hamburg", "country": "Germany", "lat": 53.5511, "lon": 9.9937, "studios_estimate": 60, "notes": "InnoGames, Goodgame Studios, Daedalic, Bigpoint"},
        {"hub": "Lyon Game Hub", "city": "Lyon", "country": "France", "lat": 45.7640, "lon": 4.8357, "studios_estimate": 40, "notes": "Arkane Lyon, Ivory Tower, growing French game dev scene"},
        {"hub": "Vancouver Game Hub", "city": "Vancouver", "country": "Canada", "lat": 49.2827, "lon": -123.1207, "studios_estimate": 80, "notes": "EA Vancouver, Relic, Blackbird Interactive, mobile studios"},
        {"hub": "Krakow / Wroclaw Hub", "city": "Krakow", "country": "Poland", "lat": 50.0647, "lon": 19.9450, "studios_estimate": 50, "notes": "Techland Wroclaw, Bloober Team, growing Polish dev scene"},
        {"hub": "Melbourne Game Hub", "city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631, "studios_estimate": 45, "notes": "League of Geeks, Hipster Whale, Australian indie scene capital"},
    ]
    return pd.DataFrame(data)


def _render_game_dev_hubs():
    """Map 8: Game Development Hubs."""
    df = _get_game_dev_hubs()
    st.markdown("#### Game Development Hubs")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Hubs", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Studios (est.)", f"{int(df['studios_estimate'].sum()):,}")
    c4.metric("Largest Hub", df.loc[df["studios_estimate"].idxmax(), "hub"].split("/")[0].strip())

    top_hubs = df.nlargest(12, "studios_estimate")
    fig, ax = _dark_fig(figsize=(10, 5))
    ax.barh(top_hubs["hub"].values[::-1], top_hubs["studios_estimate"].values[::-1],
            color=[_color_for(i) for i in range(len(top_hubs))])
    ax.set_xlabel("Estimated Studios")
    ax.set_title("Largest Game Development Hubs")
    st.image(_fig_to_bytes(fig), width=800)

    # Chart: total estimated studios by country
    country_studios = df.groupby("country")["studios_estimate"].sum().sort_values(ascending=True)
    fig2, ax2 = _dark_fig(figsize=(10, 5))
    ax2.barh(country_studios.index, country_studios.values,
             color=[_color_for(i) for i in range(len(country_studios))])
    ax2.set_xlabel("Total Estimated Studios")
    ax2.set_title("Game Studios by Country (Estimated Total)")
    st.image(_fig_to_bytes(fig2), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        radius = max(6, min(18, row["studios_estimate"] / 40))
        popup_html = (
            f"<b>{html_module.escape(row['hub'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Est. Studios: {row['studios_estimate']}<br>"
            f"Notes: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=ACCENT_CYAN,
            fill=True,
            fill_color=ACCENT_CYAN,
            fill_opacity=0.65,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["hub"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["hub", "city", "country", "studios_estimate", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "game_dev_hubs.csv", "text/csv",
                       key="dl_game_dev_hubs")


# =====================================================================
# 9. REAL-WORLD GAME LOCATIONS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_real_world_locations():
    data = [
        {"location": "Florence (Firenze)", "city": "Florence", "country": "Italy", "lat": 43.7696, "lon": 11.2558, "game": "Assassins Creed II", "notes": "Ezio Auditore's home city, Duomo, Palazzo Vecchio faithfully recreated"},
        {"location": "Venice (Venezia)", "city": "Venice", "country": "Italy", "lat": 45.4408, "lon": 12.3155, "game": "Assassins Creed II", "notes": "Canals, St. Marks Basilica, and Venetian architecture in-game"},
        {"location": "Paris (Revolution era)", "city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "game": "Assassins Creed Unity", "notes": "Notre-Dame, Louvre, French Revolution era Paris recreated"},
        {"location": "Ancient Egypt - Giza", "city": "Giza", "country": "Egypt", "lat": 29.9792, "lon": 31.1342, "game": "Assassins Creed Origins", "notes": "Pyramids of Giza and Ancient Egyptian landmarks recreated"},
        {"location": "Ancient Athens - Acropolis", "city": "Athens", "country": "Greece", "lat": 37.9715, "lon": 23.7267, "game": "Assassins Creed Odyssey", "notes": "Parthenon and Ancient Greek world recreated"},
        {"location": "Los Santos (Los Angeles)", "city": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437, "game": "GTA V", "notes": "Los Santos is a detailed parody of Los Angeles, Hollywood, Venice Beach"},
        {"location": "Liberty City (New York)", "city": "New York City", "country": "USA", "lat": 40.7128, "lon": -74.0060, "game": "GTA IV", "notes": "Liberty City closely mirrors Manhattan, Brooklyn, and the Bronx"},
        {"location": "Vice City (Miami)", "city": "Miami", "country": "USA", "lat": 25.7617, "lon": -80.1918, "game": "GTA Vice City", "notes": "1980s Miami recreated as Vice City with neon and art deco"},
        {"location": "Toussaint (Beaune, Burgundy)", "city": "Beaune", "country": "France", "lat": 47.0222, "lon": 4.8400, "game": "The Witcher 3: Blood and Wine", "notes": "Toussaint region inspired by Southern France/Burgundy wine country"},
        {"location": "Skellige (Skellig Michael)", "city": "Skellig Michael", "country": "Ireland", "lat": 51.7701, "lon": -10.5387, "game": "The Witcher 3", "notes": "Skellige islands inspired by Skellig Michael and Norse-Celtic culture"},
        {"location": "Novigrad (Gdansk/Dubrovnik)", "city": "Gdansk", "country": "Poland", "lat": 54.3520, "lon": 18.6466, "game": "The Witcher 3", "notes": "Novigrad inspired by medieval Gdansk and Dubrovnik architecture"},
        {"location": "Kamurocho (Kabukicho)", "city": "Tokyo", "country": "Japan", "lat": 35.6940, "lon": 139.7036, "game": "Yakuza / Like a Dragon series", "notes": "Kamurocho is a near 1:1 recreation of Tokyos Kabukicho district"},
        {"location": "Sotenbori (Dotonbori)", "city": "Osaka", "country": "Japan", "lat": 34.6687, "lon": 135.5013, "game": "Yakuza / Like a Dragon series", "notes": "Sotenbori mirrors Osakas famous Dotonbori entertainment district"},
        {"location": "Hyrule Field (various inspirations)", "city": "Kyoto", "country": "Japan", "lat": 34.9850, "lon": 135.7586, "game": "Legend of Zelda: BotW/TotK", "notes": "Hyrule draws from Japanese and European landscapes, Kyoto gardens"},
        {"location": "Saint-Denis (New Orleans)", "city": "New Orleans", "country": "USA", "lat": 29.9511, "lon": -90.0715, "game": "Red Dead Redemption 2", "notes": "Saint-Denis is modeled after early 1900s New Orleans, French Quarter"},
        {"location": "Valentine (Valentine, NE)", "city": "Valentine", "country": "USA", "lat": 42.8725, "lon": -100.5508, "game": "Red Dead Redemption 2", "notes": "Small Western town, inspired by Nebraska frontier towns"},
        {"location": "Prague (Deus Ex)", "city": "Prague", "country": "Czech Republic", "lat": 50.0755, "lon": 14.4378, "game": "Deus Ex: Mankind Divided", "notes": "Cyberpunk Prague with real landmarks reimagined in a dystopian future"},
        {"location": "Boston (1775)", "city": "Boston", "country": "USA", "lat": 42.3601, "lon": -71.0589, "game": "Assassins Creed III", "notes": "Colonial Boston during American Revolution faithfully recreated"},
        {"location": "London (Victorian era)", "city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "game": "Assassins Creed Syndicate", "notes": "Victorian London, Buckingham Palace, Big Ben, Thames recreated"},
        {"location": "Tsushima Island", "city": "Tsushima", "country": "Japan", "lat": 34.4038, "lon": 129.3326, "game": "Ghost of Tsushima", "notes": "Real Japanese island during 1274 Mongol invasion, landscapes faithfully recreated"},
        {"location": "Yharnam (Edinburgh/Prague mix)", "city": "Edinburgh", "country": "UK", "lat": 55.9533, "lon": -3.1883, "game": "Bloodborne", "notes": "Yharnams Gothic Victorian architecture inspired by Edinburgh and Prague"},
        {"location": "Raccoon City (various US cities)", "city": "Denver", "country": "USA", "lat": 39.7392, "lon": -104.9903, "game": "Resident Evil 2/3", "notes": "Raccoon City loosely based on Midwest US cities, mountain setting"},
        {"location": "Baghdad (Ancient)", "city": "Baghdad", "country": "Iraq", "lat": 33.3128, "lon": 44.3615, "game": "Assassins Creed Mirage", "notes": "9th century Baghdad during the Abbasid Caliphate faithfully recreated"},
        {"location": "Washington D.C. (post-apocalyptic)", "city": "Washington D.C.", "country": "USA", "lat": 38.9072, "lon": -77.0369, "game": "Fallout 3", "notes": "Capitol Wasteland: post-nuclear D.C. with Lincoln Memorial, Capitol Building"},
        {"location": "Nevada/Mojave Desert", "city": "Las Vegas", "country": "USA", "lat": 36.1699, "lon": -115.1398, "game": "Fallout: New Vegas", "notes": "Post-apocalyptic Las Vegas Strip and Hoover Dam recreated"},
        {"location": "Hong Kong (Sleeping Dogs)", "city": "Hong Kong", "country": "China", "lat": 22.3193, "lon": 114.1694, "game": "Sleeping Dogs", "notes": "Hong Kong island districts faithfully recreated with street markets and triads"},
        {"location": "Constantinople (1511)", "city": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784, "game": "Assassins Creed Revelations", "notes": "Ottoman-era Constantinople with Hagia Sophia, Grand Bazaar recreated"},
        {"location": "Nordic Wilderness (Skyrim)", "city": "Lofoten Islands", "country": "Norway", "lat": 68.2352, "lon": 14.5635, "game": "The Elder Scrolls V: Skyrim", "notes": "Skyrims landscape heavily inspired by Norwegian fjords and mountains"},
    ]
    return pd.DataFrame(data)


def _render_real_world_locations():
    """Map 9: Real-World Game Locations."""
    df = _get_real_world_locations()
    st.markdown("#### Real-World Game Locations")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Games", df["game"].nunique())
    c4.metric("Franchises", len(set(g.split(":")[0].strip() for g in df["game"])))

    game_counts = df["game"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(game_counts.index[::-1], game_counts.values[::-1],
            color=[_color_for(i) for i in range(len(game_counts))])
    ax.set_xlabel("Locations")
    ax.set_title("Real-World Locations by Game")
    st.image(_fig_to_bytes(fig), width=800)

    # Chart: locations by country
    country_counts = df["country"].value_counts().head(10)
    fig2, ax2 = _dark_fig(figsize=(10, 4))
    ax2.barh(country_counts.index[::-1], country_counts.values[::-1],
             color=[_color_for(i) for i in range(len(country_counts))])
    ax2.set_xlabel("Locations")
    ax2.set_title("Real-World Game Locations by Country")
    st.image(_fig_to_bytes(fig2), width=800)

    m = _base_map(zoom=2)
    cluster = MarkerCluster().add_to(m)
    game_list = list(df["game"].unique())
    game_colors = {g: _color_for(i) for i, g in enumerate(game_list)}
    for _, row in df.iterrows():
        color = game_colors.get(row["game"], ACCENT_PINK)
        popup_html = (
            f"<b>{html_module.escape(row['location'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Game: {html_module.escape(row['game'])}<br>"
            f"Notes: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["location"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["location", "city", "country", "game", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "real_world_game_locations.csv", "text/csv",
                       key="dl_real_world_locations")


# =====================================================================
# 10. GAMING CONVENTIONS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_gaming_conventions():
    data = [
        {"convention": "E3 (Electronic Entertainment Expo)", "city": "Los Angeles", "country": "USA", "lat": 34.0407, "lon": -118.2668, "frequency": "Annual (1995-2023)", "notes": "Legendary gaming expo at LA Convention Center, industry landmark"},
        {"convention": "Gamescom", "city": "Cologne", "country": "Germany", "lat": 50.9461, "lon": 6.9527, "frequency": "Annual", "notes": "Worlds largest gaming event by attendance, 300,000+ visitors"},
        {"convention": "Tokyo Game Show (TGS)", "city": "Chiba", "country": "Japan", "lat": 35.6484, "lon": 140.0340, "frequency": "Annual", "notes": "Asias biggest gaming convention at Makuhari Messe since 1996"},
        {"convention": "PAX West", "city": "Seattle", "country": "USA", "lat": 47.6117, "lon": -122.3316, "frequency": "Annual", "notes": "Penny Arcade Expo, major fan-focused gaming convention since 2004"},
        {"convention": "PAX East", "city": "Boston", "country": "USA", "lat": 42.3465, "lon": -71.0421, "frequency": "Annual", "notes": "East Coast PAX, Boston Convention and Exhibition Center"},
        {"convention": "PAX Aus", "city": "Melbourne", "country": "Australia", "lat": -37.8253, "lon": 144.9540, "frequency": "Annual", "notes": "PAX Australia, Melbourne Convention and Exhibition Centre"},
        {"convention": "ChinaJoy", "city": "Shanghai", "country": "China", "lat": 31.1919, "lon": 121.3106, "frequency": "Annual", "notes": "China Digital Entertainment Expo, Asias second largest game show"},
        {"convention": "Brasil Game Show (BGS)", "city": "Sao Paulo", "country": "Brazil", "lat": -23.5164, "lon": -46.6370, "frequency": "Annual", "notes": "Largest gaming event in Latin America, 300,000+ attendees"},
        {"convention": "G-Star", "city": "Busan", "country": "South Korea", "lat": 35.1283, "lon": 129.0597, "frequency": "Annual", "notes": "Global Game Exhibition in Busan, showcases Korean and Asian games"},
        {"convention": "DreamHack", "city": "Jonkoping", "country": "Sweden", "lat": 57.7826, "lon": 14.1618, "frequency": "Multiple/year", "notes": "Worlds largest LAN party and digital festival since 1994"},
        {"convention": "Game Developers Conference (GDC)", "city": "San Francisco", "country": "USA", "lat": 37.7849, "lon": -122.4005, "frequency": "Annual", "notes": "Premier industry event for developers at Moscone Center since 1988"},
        {"convention": "EVO (Evolution Championship Series)", "city": "Las Vegas", "country": "USA", "lat": 36.1215, "lon": -115.1739, "frequency": "Annual", "notes": "Worlds largest fighting game tournament, at Mandalay Bay/Las Vegas"},
        {"convention": "EVO Japan", "city": "Tokyo", "country": "Japan", "lat": 35.6584, "lon": 139.7454, "frequency": "Annual", "notes": "Japanese edition of EVO for Asian fighting game community"},
        {"convention": "BlizzCon", "city": "Anaheim", "country": "USA", "lat": 33.8003, "lon": -117.9190, "frequency": "Annual/Biennial", "notes": "Blizzard Entertainment fan convention at Anaheim Convention Center"},
        {"convention": "The Game Awards", "city": "Los Angeles", "country": "USA", "lat": 34.0432, "lon": -118.2673, "frequency": "Annual", "notes": "Hosted by Geoff Keighley, gamings biggest awards show since 2014"},
        {"convention": "Indie Games Festival (IGF)", "city": "San Francisco", "country": "USA", "lat": 37.7849, "lon": -122.4005, "frequency": "Annual", "notes": "Part of GDC, showcases best independent games since 1998"},
        {"convention": "Paris Games Week", "city": "Paris", "country": "France", "lat": 48.8322, "lon": 2.2863, "frequency": "Annual", "notes": "Frances major gaming convention at Paris Expo Porte de Versailles"},
        {"convention": "Milan Games Week", "city": "Milan", "country": "Italy", "lat": 45.4743, "lon": 9.1013, "frequency": "Annual", "notes": "Italys biggest gaming and esports event at Fiera Milano Rho"},
        {"convention": "Madrid Games Week", "city": "Madrid", "country": "Spain", "lat": 40.4656, "lon": -3.6138, "frequency": "Annual", "notes": "Spains main gaming convention at IFEMA Madrid"},
        {"convention": "Taipei Game Show", "city": "Taipei", "country": "Taiwan", "lat": 25.0330, "lon": 121.5654, "frequency": "Annual", "notes": "Major Asian gaming event at Taipei Nangang Exhibition Center"},
        {"convention": "Insomnia Gaming Festival", "city": "Birmingham", "country": "UK", "lat": 52.4524, "lon": -1.7296, "frequency": "Multiple/year", "notes": "UKs biggest gaming festival at NEC Birmingham"},
        {"convention": "Comic-Con International (Gaming)", "city": "San Diego", "country": "USA", "lat": 32.7073, "lon": -117.1628, "frequency": "Annual", "notes": "Major gaming presence at worlds biggest pop culture convention"},
        {"convention": "Nordic Game Conference", "city": "Malmo", "country": "Sweden", "lat": 55.6050, "lon": 13.0038, "frequency": "Annual", "notes": "Nordic game industry conference, indie and AAA developers"},
        {"convention": "Reboot Develop", "city": "Dubrovnik", "country": "Croatia", "lat": 42.6507, "lon": 18.0944, "frequency": "Annual", "notes": "European game dev conference on Croatian coast"},
        {"convention": "Tokyo Indie Fest (BitSummit)", "city": "Kyoto", "country": "Japan", "lat": 35.0116, "lon": 135.7681, "frequency": "Annual", "notes": "Japans premier indie game festival at Miyako Messe"},
    ]
    return pd.DataFrame(data)


def _render_gaming_conventions():
    """Map 10: Gaming Conventions."""
    df = _get_gaming_conventions()
    st.markdown("#### Gaming Conventions")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Conventions", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("In USA", int((df["country"] == "USA").sum()))
    c4.metric("In Europe", int(df["country"].isin(["Germany", "Sweden", "France", "Italy", "Spain", "UK", "Croatia"]).sum()))

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Conventions")
    ax.set_title("Gaming Conventions by Country")
    st.image(_fig_to_bytes(fig), width=800)

    # Chart: frequency distribution
    freq_counts = df["frequency"].value_counts()
    fig2, ax2 = _dark_fig(figsize=(10, 4))
    colors = [_color_for(i) for i in range(len(freq_counts))]
    ax2.pie(freq_counts.values, labels=freq_counts.index, colors=colors,
            autopct="%1.0f%%", textprops={"color": TEXT_PRIMARY})
    ax2.set_title("Convention Frequency Distribution")
    st.image(_fig_to_bytes(fig2), width=600)

    m = _base_map(zoom=2)
    cluster = MarkerCluster().add_to(m)
    for idx, row in df.iterrows():
        color = _color_for(idx)
        popup_html = (
            f"<b>{html_module.escape(row['convention'])}</b><br>"
            f"City: {html_module.escape(row['city'])}, {html_module.escape(row['country'])}<br>"
            f"Frequency: {html_module.escape(row['frequency'])}<br>"
            f"Notes: {html_module.escape(row['notes'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=html_module.escape(row["convention"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["convention", "city", "country", "frequency", "notes"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "gaming_conventions.csv", "text/csv",
                       key="dl_gaming_conventions")


# =====================================================================
# MODE DISPATCH MAP
# =====================================================================
MAP_OPTIONS = {
    "Major Game Studios": _render_game_studios,
    "Esports Arenas & Venues": _render_esports_arenas,
    "Video Game Museums": _render_game_museums,
    "Arcade Culture Origins": _render_arcade_culture,
    "Board Game Capitals": _render_board_game_capitals,
    "Chess History": _render_chess_history,
    "Pinball & Retro Gaming": _render_pinball_retro,
    "Game Development Hubs": _render_game_dev_hubs,
    "Real-World Game Locations": _render_real_world_locations,
    "Gaming Conventions": _render_gaming_conventions,
}


# =====================================================================
# MAIN TAB ENTRY POINT
# =====================================================================
def render_games_maps_tab():
    """Main entry point for the Video Games & Board Games Maps tab."""
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001f3ae Video Games & Board Games Maps</h4>'
        '<p>Gaming history, studios, and esports worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    selected_mode = st.selectbox(
        "Map Mode",
        MAP_MODES,
        key="games_maps_mode_select",
    )

    if st.button("Generate Map", key="games_maps_generate", type="primary"):
        with st.spinner("Building map..."):
            MAP_OPTIONS[selected_mode]()
    else:
        st.info("Select a map mode above and click **Generate Map** to explore.")
