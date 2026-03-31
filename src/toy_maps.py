# -*- coding: utf-8 -*-
"""
Toys & Collectibles Maps module for TerraScout AI.
Provides 10 interactive map modes covering LEGO landmarks, toy museums,
famous toy factories, doll & puppet traditions, model train heritage,
teddy bear origins, video game console history, comic & action figure hubs,
traditional toy crafts, and theme park toy shops.
All data is hardcoded/curated for offline reliability.
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


# =====================================================================
# COLOUR PALETTE  (TerraScout dark theme)
# =====================================================================
_CLR_CYAN = "#06b6d4"
_CLR_PINK = "#ec4899"
_CLR_VIOLET = "#8b5cf6"
_CLR_AMBER = "#f59e0b"
_CLR_EMERALD = "#10b981"
_CLR_RED = "#ef4444"
_CLR_BLUE = "#3b82f6"
_CLR_ORANGE = "#f97316"
_CLR_TEAL = "#14b8a6"
_CLR_PURPLE = "#a855f7"
_CLR_ROSE = "#e11d48"
_CLR_LIME = "#84cc16"
_CLR_YELLOW = "#facc15"
_CLR_SKY = "#22d3ee"
_CLR_FUCHSIA = "#c084fc"

_PALETTE = [
    _CLR_CYAN, _CLR_PINK, _CLR_VIOLET, _CLR_AMBER, _CLR_EMERALD,
    _CLR_RED, _CLR_BLUE, _CLR_ORANGE, _CLR_TEAL, _CLR_PURPLE,
    _CLR_ROSE, _CLR_LIME, _CLR_YELLOW, _CLR_SKY, _CLR_FUCHSIA,
]


def _clr(idx: int) -> str:
    """Return a colour from the rotating palette."""
    return _PALETTE[idx % len(_PALETTE)]


def _esc(val) -> str:
    """Escape a value for safe HTML embedding in popups."""
    return html_module.escape(str(val))


def _base_map(center=None, zoom=2):
    """Return a dark-themed folium map."""
    if center is None:
        center = [20, 0]
    return folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        width="100%",
    )


def _show(m):
    """Render a folium map inside Streamlit via st_html."""
    st_html(m._repr_html_(), height=500)


def _csv(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode("utf-8")


def _popup(title, color, fields):
    """Build a styled popup HTML string from field pairs."""
    body = "".join(
        f"<b>{k}:</b> {_esc(v)}<br>" for k, v in fields
    )
    return (
        f"<div style='font-family:sans-serif;min-width:210px;'>"
        f"<b style='color:{color};font-size:13px;'>{_esc(title)}</b><br>"
        f"{body}</div>"
    )


# =====================================================================
# 1. LEGO WORLD
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_lego_world():
    rows = [
        {
            "name": "LEGO House",
            "city": "Billund",
            "country": "Denmark",
            "type": "Experience Centre",
            "lat": 55.7316,
            "lon": 9.1265,
            "year": 2017,
            "notes": "Home of the Brick designed by BIG with 25 million bricks inside",
        },
        {
            "name": "LEGO Headquarters Campus",
            "city": "Billund",
            "country": "Denmark",
            "type": "HQ",
            "lat": 55.7308,
            "lon": 9.1190,
            "year": 1932,
            "notes": "Global headquarters since Ole Kirk Christiansen founded the company",
        },
        {
            "name": "LEGO Factory Billund",
            "city": "Billund",
            "country": "Denmark",
            "type": "Factory",
            "lat": 55.7350,
            "lon": 9.1100,
            "year": 1934,
            "notes": "Original production facility still operating as a major moulding plant",
        },
        {
            "name": "LEGOLAND Billund Resort",
            "city": "Billund",
            "country": "Denmark",
            "type": "Theme Park",
            "lat": 55.7354,
            "lon": 9.1267,
            "year": 1968,
            "notes": "The original Legoland park with Miniland and over 60 rides",
        },
        {
            "name": "LEGOLAND Windsor Resort",
            "city": "Windsor",
            "country": "UK",
            "type": "Theme Park",
            "lat": 51.4636,
            "lon": -0.6486,
            "year": 1996,
            "notes": "Over 150 rides and attractions with a Miniland of London landmarks",
        },
        {
            "name": "LEGOLAND California Resort",
            "city": "Carlsbad",
            "country": "USA",
            "type": "Theme Park",
            "lat": 33.1268,
            "lon": -117.3114,
            "year": 1999,
            "notes": "Over 60 rides with LEGO Star Wars Miniland and Sea Life Aquarium",
        },
        {
            "name": "LEGOLAND Deutschland Resort",
            "city": "Guenzburg",
            "country": "Germany",
            "type": "Theme Park",
            "lat": 48.4260,
            "lon": 10.2977,
            "year": 2002,
            "notes": "25 million bricks in Miniland across 11 themed adventure areas",
        },
        {
            "name": "LEGOLAND Florida Resort",
            "city": "Winter Haven",
            "country": "USA",
            "type": "Theme Park",
            "lat": 28.0986,
            "lon": -81.6911,
            "year": 2011,
            "notes": "Built on the former Cypress Gardens site with an attached water park",
        },
        {
            "name": "LEGOLAND Malaysia Resort",
            "city": "Johor Bahru",
            "country": "Malaysia",
            "type": "Theme Park",
            "lat": 1.4293,
            "lon": 103.6279,
            "year": 2012,
            "notes": "First Legoland in Asia with over 70 rides and family attractions",
        },
        {
            "name": "LEGOLAND Dubai",
            "city": "Dubai",
            "country": "UAE",
            "type": "Theme Park",
            "lat": 24.9216,
            "lon": 55.0048,
            "year": 2016,
            "notes": "Part of Dubai Parks and Resorts with over 40 rides and shows",
        },
        {
            "name": "LEGOLAND Japan Resort",
            "city": "Nagoya",
            "country": "Japan",
            "type": "Theme Park",
            "lat": 35.0443,
            "lon": 136.8443,
            "year": 2017,
            "notes": "Over 10000 LEGO models across 7 themed areas in Minato-ku district",
        },
        {
            "name": "LEGOLAND New York Resort",
            "city": "Goshen",
            "country": "USA",
            "type": "Theme Park",
            "lat": 41.3682,
            "lon": -74.3821,
            "year": 2021,
            "notes": "154 acres making it the largest LEGOLAND park in the world",
        },
        {
            "name": "LEGOLAND Korea Resort",
            "city": "Chuncheon",
            "country": "South Korea",
            "type": "Theme Park",
            "lat": 37.8564,
            "lon": 127.7222,
            "year": 2022,
            "notes": "Over 40 rides built on Hajungdo Island in Gangwon Province",
        },
        {
            "name": "LEGO Discovery Centre Toronto",
            "city": "Toronto",
            "country": "Canada",
            "type": "Discovery Centre",
            "lat": 43.7132,
            "lon": -79.3419,
            "year": 2013,
            "notes": "Indoor LEGO attraction with 4D cinema and build-and-test zones",
        },
        {
            "name": "LEGO Discovery Centre Berlin",
            "city": "Berlin",
            "country": "Germany",
            "type": "Discovery Centre",
            "lat": 52.5115,
            "lon": 13.3757,
            "year": 2007,
            "notes": "Located at Potsdamer Platz with Berlin landmarks in Miniland",
        },
        {
            "name": "LEGO Discovery Centre Osaka",
            "city": "Osaka",
            "country": "Japan",
            "type": "Discovery Centre",
            "lat": 34.6690,
            "lon": 135.4325,
            "year": 2015,
            "notes": "Family attraction with LEGO 4D cinema and creative workshops",
        },
        {
            "name": "LEGO Factory Nyiregyhaza",
            "city": "Nyiregyhaza",
            "country": "Hungary",
            "type": "Factory",
            "lat": 47.9553,
            "lon": 21.7168,
            "year": 2014,
            "notes": "Major European moulding and packaging production facility",
        },
        {
            "name": "LEGO Factory Monterrey",
            "city": "Monterrey",
            "country": "Mexico",
            "type": "Factory",
            "lat": 25.6866,
            "lon": -100.3161,
            "year": 2008,
            "notes": "Largest LEGO production factory outside of the European continent",
        },
        {
            "name": "LEGO Factory Jiaxing",
            "city": "Jiaxing",
            "country": "China",
            "type": "Factory",
            "lat": 30.7530,
            "lon": 120.7500,
            "year": 2016,
            "notes": "Carbon-neutral factory designed to serve the entire Asian market",
        },
        {
            "name": "LEGOLAND Water Park Gardaland",
            "city": "Castelnuovo del Garda",
            "country": "Italy",
            "type": "Water Park",
            "lat": 45.4546,
            "lon": 10.7138,
            "year": 2021,
            "notes": "Europes first standalone LEGOLAND Water Park at Gardaland Resort",
        },
        {
            "name": "LEGO Discovery Centre Shanghai",
            "city": "Shanghai",
            "country": "China",
            "type": "Discovery Centre",
            "lat": 31.2381,
            "lon": 121.4737,
            "year": 2016,
            "notes": "Interactive indoor attraction with Shanghai skyline in LEGO bricks",
        },
    ]
    return pd.DataFrame(rows)


def _render_lego_world():
    df = _fetch_lego_world()
    st.markdown("#### LEGO World: Parks, Factories & Experience Centres")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["year"].min()))
    c4.metric("Newest", int(df["year"].max()))

    m = _base_map(center=[30, 10], zoom=2)
    type_clr = {
        "Theme Park": _CLR_AMBER,
        "Factory": _CLR_CYAN,
        "HQ": _CLR_EMERALD,
        "Experience Centre": _CLR_PINK,
        "Discovery Centre": _CLR_VIOLET,
        "Water Park": _CLR_BLUE,
    }
    for _, r in df.iterrows():
        clr = type_clr.get(r["type"], _CLR_AMBER)
        p = _popup(r["name"], clr, [
            ("City", f"{r['city']}, {r['country']}"),
            ("Type", r["type"]),
            ("Opened", str(r["year"])),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["name", "city", "country", "type", "year", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df), "lego_world.csv", "text/csv", key="dl_lego",
    )


# =====================================================================
# 2. TOY MUSEUMS
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_toy_museums():
    rows = [
        {
            "museum": "V&A Museum of Childhood",
            "city": "London",
            "country": "UK",
            "lat": 51.5287,
            "lon": -0.0474,
            "founded": 1872,
            "notes": "Bethnal Green branch with one of the worlds largest childhood collections",
        },
        {
            "museum": "Nuremberg Toy Museum (Spielzeugmuseum)",
            "city": "Nuremberg",
            "country": "Germany",
            "lat": 49.4529,
            "lon": 11.0781,
            "founded": 1971,
            "notes": "1400 sqm of toy history housed in a medieval building in the old town",
        },
        {
            "museum": "The Strong National Museum of Play",
            "city": "Rochester",
            "country": "USA",
            "lat": 43.1559,
            "lon": -77.6041,
            "founded": 1968,
            "notes": "Home of the National Toy Hall of Fame with the largest toy and game collection",
        },
        {
            "museum": "Pollocks Toy Museum",
            "city": "London",
            "country": "UK",
            "lat": 51.5206,
            "lon": -0.1338,
            "founded": 1956,
            "notes": "Fitzrovia gem showcasing Victorian toy theatres and antique playthings",
        },
        {
            "museum": "Musee des Arts Decoratifs Toy Gallery",
            "city": "Paris",
            "country": "France",
            "lat": 48.8625,
            "lon": 2.3329,
            "founded": 1882,
            "notes": "Extensive collection of French dolls, tin toys, and mechanical automata",
        },
        {
            "museum": "Spielzeug Welten Museum Basel",
            "city": "Basel",
            "country": "Switzerland",
            "lat": 47.5562,
            "lon": 7.5888,
            "founded": 1998,
            "notes": "Teddy bears, dollhouses, and miniature shops spread over 4 museum floors",
        },
        {
            "museum": "MINT Museum of Toys",
            "city": "Singapore",
            "country": "Singapore",
            "lat": 1.2966,
            "lon": 103.8544,
            "founded": 2006,
            "notes": "50000 vintage toys from over 40 countries in a purpose-built museum",
        },
        {
            "museum": "Istanbul Toy Museum",
            "city": "Istanbul",
            "country": "Turkey",
            "lat": 40.9629,
            "lon": 29.0736,
            "founded": 2005,
            "notes": "Over 4000 toys from the 1700s onward, founded by poet Sunay Akin",
        },
        {
            "museum": "Museo del Juguete Antiguo Mexico (MUJAM)",
            "city": "Mexico City",
            "country": "Mexico",
            "lat": 19.4550,
            "lon": -99.1265,
            "founded": 2008,
            "notes": "Over 40000 Mexican and international vintage toys in Doctores district",
        },
        {
            "museum": "Penang Toy Museum",
            "city": "Penang",
            "country": "Malaysia",
            "lat": 5.4636,
            "lon": 100.1847,
            "founded": 1999,
            "notes": "Over 100000 items including rare Star Wars and superhero collections",
        },
        {
            "museum": "Warabekan Toy Museum",
            "city": "Kurayoshi",
            "country": "Japan",
            "lat": 35.4309,
            "lon": 133.8250,
            "founded": 1999,
            "notes": "Traditional Japanese toys, figures, and nostalgic Showa-era items",
        },
        {
            "museum": "Musee du Jouet Colmar",
            "city": "Colmar",
            "country": "France",
            "lat": 48.0810,
            "lon": 7.3595,
            "founded": 1993,
            "notes": "Former cinema converted to toy museum, items from 1800s to present",
        },
        {
            "museum": "Deutsches Spielzeugmuseum Sonneberg",
            "city": "Sonneberg",
            "country": "Germany",
            "lat": 50.3500,
            "lon": 11.1667,
            "founded": 1901,
            "notes": "Oldest German toy museum in the historic Thuringian toy capital",
        },
        {
            "museum": "Museo del Giocattolo",
            "city": "Santo Stefano Lodigiano",
            "country": "Italy",
            "lat": 45.0928,
            "lon": 9.7701,
            "founded": 2003,
            "notes": "Italian toy heritage from artisan workshops to collectible Lenci dolls",
        },
        {
            "museum": "Toy Museum Valletta",
            "city": "Valletta",
            "country": "Malta",
            "lat": 35.8989,
            "lon": 14.5146,
            "founded": 1998,
            "notes": "Unique Mediterranean toy collection in a 17th-century townhouse",
        },
        {
            "museum": "Benaki Toy Museum",
            "city": "Athens",
            "country": "Greece",
            "lat": 37.9768,
            "lon": 23.7351,
            "founded": 2017,
            "notes": "Museum of Greek Childhood at Plaka with shadow puppets and folk toys",
        },
        {
            "museum": "Brighton Toy and Model Museum",
            "city": "Brighton",
            "country": "UK",
            "lat": 50.8313,
            "lon": -0.1426,
            "founded": 1991,
            "notes": "Over 10000 toys in vaulted arches under Brighton train station",
        },
        {
            "museum": "Museo do Brinquedo Sintra",
            "city": "Sintra",
            "country": "Portugal",
            "lat": 38.7984,
            "lon": -9.3881,
            "founded": 1997,
            "notes": "40000 items spanning 600 years of play in a palatial Portuguese setting",
        },
        {
            "museum": "Suomenlinna Toy Museum",
            "city": "Helsinki",
            "country": "Finland",
            "lat": 60.1454,
            "lon": 24.9881,
            "founded": 1985,
            "notes": "Antique toys in a 19th-century Russian villa on the fortress island",
        },
        {
            "museum": "Toy and Miniature Museum of Kansas City",
            "city": "Kansas City",
            "country": "USA",
            "lat": 39.0380,
            "lon": -94.5803,
            "founded": 1982,
            "notes": "72-room museum with fine-scale miniatures and antique toys from many eras",
        },
        {
            "museum": "Hida Takayama Showa Museum",
            "city": "Takayama",
            "country": "Japan",
            "lat": 36.1408,
            "lon": 137.2521,
            "founded": 1999,
            "notes": "Nostalgic Showa-era Japanese toys, games, and everyday objects on display",
        },
    ]
    return pd.DataFrame(rows)


def _render_toy_museums():
    df = _fetch_toy_museums()
    st.markdown("#### Toy Museums of the World")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Museums", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["founded"].min()))
    c4.metric("Newest", int(df["founded"].max()))

    m = _base_map(center=[30, 10], zoom=2)
    for _, r in df.iterrows():
        p = _popup(r["museum"], _CLR_VIOLET, [
            ("City", f"{r['city']}, {r['country']}"),
            ("Founded", str(r["founded"])),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=_CLR_VIOLET,
            fill=True,
            fill_color=_CLR_VIOLET,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["museum"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["museum", "city", "country", "founded", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df), "toy_museums.csv", "text/csv", key="toym_dl_museums",
    )


# =====================================================================
# 3. FAMOUS TOY FACTORIES
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_toy_factories():
    rows = [
        {
            "name": "Mattel Headquarters",
            "city": "El Segundo",
            "country": "USA",
            "brand": "Barbie, Hot Wheels, Fisher-Price",
            "lat": 33.9178,
            "lon": -118.4003,
            "founded": 1945,
            "notes": "Worlds second largest toy company, Barbie created by Ruth Handler 1959",
        },
        {
            "name": "Hasbro Headquarters",
            "city": "Pawtucket",
            "country": "USA",
            "brand": "Transformers, Nerf, Play-Doh, Monopoly",
            "lat": 41.8787,
            "lon": -71.3826,
            "founded": 1923,
            "notes": "Founded as Hassenfeld Brothers, now a global toy and gaming giant",
        },
        {
            "name": "Bandai Namco Headquarters",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "Gundam, Tamagotchi, Power Rangers",
            "lat": 35.6265,
            "lon": 139.7775,
            "founded": 1950,
            "notes": "Japanese toy and entertainment powerhouse merged with Namco 2005",
        },
        {
            "name": "Takara Tomy Headquarters",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "Tomica, Plarail, Beyblade, Licca-chan",
            "lat": 35.6935,
            "lon": 139.7036,
            "founded": 1953,
            "notes": "Major Japanese toymaker and Transformers co-creator since 1984",
        },
        {
            "name": "Playmobil FunPark and Factory",
            "city": "Zirndorf",
            "country": "Germany",
            "brand": "Playmobil system figures",
            "lat": 49.4392,
            "lon": 10.9553,
            "founded": 1974,
            "notes": "Geobra Brandstaetter created Playmobil, factory tours available",
        },
        {
            "name": "LEGO Headquarters Campus",
            "city": "Billund",
            "country": "Denmark",
            "brand": "LEGO building bricks",
            "lat": 55.7308,
            "lon": 9.1190,
            "founded": 1932,
            "notes": "Worlds most powerful toy brand with over 150 billion bricks produced",
        },
        {
            "name": "Schleich Factory",
            "city": "Schwabisch Gmund",
            "country": "Germany",
            "brand": "Animal figurines, former Smurf figures",
            "lat": 48.7995,
            "lon": 9.7980,
            "founded": 1935,
            "notes": "Hand-painted animal and fantasy figurines beloved by children worldwide",
        },
        {
            "name": "Ravensburger Headquarters",
            "city": "Ravensburg",
            "country": "Germany",
            "brand": "Puzzles, board games",
            "lat": 47.7824,
            "lon": 9.6112,
            "founded": 1883,
            "notes": "Blue triangle brand renowned for premium jigsaw puzzles and games",
        },
        {
            "name": "Simba Dickie Group",
            "city": "Fuerth",
            "country": "Germany",
            "brand": "Majorette, Big Bobby Car, Eichhorn",
            "lat": 49.4778,
            "lon": 10.9897,
            "founded": 1982,
            "notes": "Europes largest toy company by revenue with many subsidiary brands",
        },
        {
            "name": "Spin Master Headquarters",
            "city": "Toronto",
            "country": "Canada",
            "brand": "PAW Patrol, Hatchimals, Kinetic Sand",
            "lat": 43.6532,
            "lon": -79.3832,
            "founded": 1994,
            "notes": "Canadian toy innovator with rapid growth through IP acquisitions",
        },
        {
            "name": "MGA Entertainment Headquarters",
            "city": "Van Nuys",
            "country": "USA",
            "brand": "LOL Surprise, Bratz, Rainbow High",
            "lat": 34.1867,
            "lon": -118.4487,
            "founded": 1979,
            "notes": "Major disruptor in collectible toys and fashion dolls worldwide",
        },
        {
            "name": "Shantou Chenghai Toy District",
            "city": "Shantou",
            "country": "China",
            "brand": "OEM plastic toys and RC vehicles",
            "lat": 23.4610,
            "lon": 116.7677,
            "founded": 1980,
            "notes": "Chinas toy capital producing 70 percent of all Chinese toy exports",
        },
        {
            "name": "Guangdong Dongguan Toy Cluster",
            "city": "Dongguan",
            "country": "China",
            "brand": "OEM for Mattel, Hasbro, others",
            "lat": 23.0207,
            "lon": 113.7518,
            "founded": 1985,
            "notes": "Major OEM hub manufacturing toys for international brand giants",
        },
        {
            "name": "Nuremberg Toy District Heritage",
            "city": "Nuremberg",
            "country": "Germany",
            "brand": "Tin toys and model trains",
            "lat": 49.4521,
            "lon": 11.0767,
            "founded": 1500,
            "notes": "Historic capital of European toy making since the late Middle Ages",
        },
        {
            "name": "Seiffen Toy Village",
            "city": "Seiffen",
            "country": "Germany",
            "brand": "Erzgebirge wooden crafts",
            "lat": 50.6452,
            "lon": 13.4523,
            "founded": 1600,
            "notes": "Nutcrackers, smoking men, Christmas pyramids, UNESCO candidate",
        },
        {
            "name": "Epoch Company (Sylvanian Families)",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "Sylvanian Families, Aquabeads",
            "lat": 35.6812,
            "lon": 139.7671,
            "founded": 1958,
            "notes": "Creator of the beloved Sylvanian Families miniature animal world",
        },
        {
            "name": "Hape Toys Headquarters",
            "city": "Shanghai",
            "country": "China",
            "brand": "Wooden educational toys",
            "lat": 31.2304,
            "lon": 121.4737,
            "founded": 1986,
            "notes": "German-founded sustainable wooden toy manufacturer based in China",
        },
        {
            "name": "Hornby Hobbies Ltd",
            "city": "Margate",
            "country": "UK",
            "brand": "Hornby trains, Airfix, Scalextric",
            "lat": 51.3890,
            "lon": 1.3838,
            "founded": 1901,
            "notes": "British model railway, slot car racing, and plastic model kit icon",
        },
        {
            "name": "Crayola Experience and Factory",
            "city": "Easton",
            "country": "USA",
            "brand": "Crayola crayons and art supplies",
            "lat": 40.6884,
            "lon": -75.2207,
            "founded": 1903,
            "notes": "Interactive factory attraction producing 3 billion crayons per year",
        },
        {
            "name": "Melissa and Doug Headquarters",
            "city": "Wilton",
            "country": "USA",
            "brand": "Wooden toys, puzzles, crafts",
            "lat": 41.1954,
            "lon": -73.4379,
            "founded": 1988,
            "notes": "Screen-free play advocates acquired by Spin Master in 2023",
        },
    ]
    return pd.DataFrame(rows)


def _render_toy_factories():
    df = _fetch_toy_factories()
    st.markdown("#### Famous Toy Factories & Company Headquarters")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["founded"].min()))
    c4.metric("Newest", int(df["founded"].max()))

    m = _base_map(center=[30, 20], zoom=2)
    for idx, r in df.iterrows():
        clr = _clr(idx)
        p = _popup(r["name"], _CLR_CYAN, [
            ("City", f"{r['city']}, {r['country']}"),
            ("Brand", r["brand"]),
            ("Founded", str(r["founded"])),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["name", "city", "country", "brand", "founded", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df), "toy_factories.csv", "text/csv", key="dl_factories",
    )


# =====================================================================
# 4. DOLL & PUPPET TRADITIONS
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_doll_puppet():
    rows = [
        {
            "name": "National Bunraku Theatre",
            "city": "Osaka",
            "country": "Japan",
            "tradition": "Bunraku",
            "lat": 34.6687,
            "lon": 135.5080,
            "era": "1684",
            "notes": "UNESCO ICH three-person puppet manipulation classical narrative art",
        },
        {
            "name": "National Marionette Theatre",
            "city": "Prague",
            "country": "Czech Republic",
            "tradition": "Czech Marionettes",
            "lat": 50.0870,
            "lon": 14.4185,
            "era": "1700s",
            "notes": "UNESCO ICH Baroque-era puppetry with Don Giovanni performances",
        },
        {
            "name": "Rajasthani Puppet Heritage (Kathputli)",
            "city": "Jaipur",
            "country": "India",
            "tradition": "Kathputli",
            "lat": 26.9124,
            "lon": 75.7873,
            "era": "1000 CE",
            "notes": "String puppets telling stories of kings, heroes, and folklore",
        },
        {
            "name": "Wayang Museum Jakarta",
            "city": "Jakarta",
            "country": "Indonesia",
            "tradition": "Wayang Kulit",
            "lat": -6.1347,
            "lon": 106.8133,
            "era": "800 CE",
            "notes": "UNESCO ICH leather shadow puppets depicting Hindu and Javanese epics",
        },
        {
            "name": "Karagoz Shadow Theatre Museum",
            "city": "Bursa",
            "country": "Turkey",
            "tradition": "Karagoz",
            "lat": 40.1826,
            "lon": 29.0610,
            "era": "1300s",
            "notes": "UNESCO ICH Ottoman leather shadow puppet comedy and satire tradition",
        },
        {
            "name": "Water Puppet Theatre Hanoi",
            "city": "Hanoi",
            "country": "Vietnam",
            "tradition": "Mua roi nuoc",
            "lat": 21.0285,
            "lon": 105.8542,
            "era": "1000 CE",
            "notes": "Unique water-surface puppetry from Red River Delta rice paddy culture",
        },
        {
            "name": "Sicilian Puppet Opera Museum",
            "city": "Palermo",
            "country": "Italy",
            "tradition": "Opera dei Pupi",
            "lat": 38.1157,
            "lon": 13.3615,
            "era": "1800s",
            "notes": "UNESCO ICH Charlemagne and Orlando epic knight puppet theatre",
        },
        {
            "name": "Salzburg Marionette Theatre",
            "city": "Salzburg",
            "country": "Austria",
            "tradition": "Marionette Opera",
            "lat": 47.8027,
            "lon": 13.0375,
            "era": "1913",
            "notes": "UNESCO ICH performing full operas with string marionettes since 1913",
        },
        {
            "name": "Augsburger Puppenkiste",
            "city": "Augsburg",
            "country": "Germany",
            "tradition": "Marionettes",
            "lat": 48.3669,
            "lon": 10.8963,
            "era": "1948",
            "notes": "Beloved German theatre known for Jim Knopf and Urmel characters",
        },
        {
            "name": "Mattel - Barbie Origins",
            "city": "El Segundo",
            "country": "USA",
            "tradition": "Fashion Dolls",
            "lat": 33.9178,
            "lon": -118.4003,
            "era": "1959",
            "notes": "Ruth Handler created Barbie in 1959, over 1 billion dolls sold",
        },
        {
            "name": "Kathe Kruse Doll Museum",
            "city": "Donauworth",
            "country": "Germany",
            "tradition": "Cloth Dolls",
            "lat": 48.7183,
            "lon": 10.7795,
            "era": "1911",
            "notes": "Pioneering naturalistic handmade cloth dolls for children since 1911",
        },
        {
            "name": "Musee de la Poupee Paris",
            "city": "Paris",
            "country": "France",
            "tradition": "French Fashion Dolls",
            "lat": 48.8617,
            "lon": 2.3510,
            "era": "1800s",
            "notes": "Over 500 antique French fashion and bebe dolls from 1800 to 1959",
        },
        {
            "name": "Guignol Theatre Lyon",
            "city": "Lyon",
            "country": "France",
            "tradition": "Guignol",
            "lat": 45.7640,
            "lon": 4.8357,
            "era": "1808",
            "notes": "Laurent Mourguet created Guignol, Frances most iconic hand puppet",
        },
        {
            "name": "Jim Henson Company Lot",
            "city": "Los Angeles",
            "country": "USA",
            "tradition": "Muppets",
            "lat": 34.0872,
            "lon": -118.3190,
            "era": "1955",
            "notes": "Jim Henson created Kermit in 1955, historic Charlie Chaplin Studios",
        },
        {
            "name": "Punch and Judy Heritage Covent Garden",
            "city": "London",
            "country": "UK",
            "tradition": "Punch and Judy",
            "lat": 51.5117,
            "lon": -0.1224,
            "era": "1662",
            "notes": "Samuel Pepys recorded the first Punch show in England here May 1662",
        },
        {
            "name": "Royal de Luxe Giant Puppets HQ",
            "city": "Nantes",
            "country": "France",
            "tradition": "Street Puppetry",
            "lat": 47.2184,
            "lon": -1.5536,
            "era": "1979",
            "notes": "Giant mechanical marionettes walking through cities for millions",
        },
        {
            "name": "Bread and Puppet Theater",
            "city": "Glover",
            "country": "USA",
            "tradition": "Political Puppetry",
            "lat": 44.7025,
            "lon": -72.1879,
            "era": "1963",
            "notes": "Peter Schumann giant puppet activism, barn museum in Vermont",
        },
        {
            "name": "Hina Matsuri Doll Tradition",
            "city": "Kyoto",
            "country": "Japan",
            "tradition": "Hina Dolls",
            "lat": 35.0116,
            "lon": 135.7681,
            "era": "800 CE",
            "notes": "Girls Day festival dolls displayed on tiered red platforms each March",
        },
        {
            "name": "Lenci Doll Heritage Turin",
            "city": "Turin",
            "country": "Italy",
            "tradition": "Felt Art Dolls",
            "lat": 45.0703,
            "lon": 7.6869,
            "era": "1919",
            "notes": "Elena Scavini felt art dolls are highly collectible worldwide",
        },
        {
            "name": "Center for Puppetry Arts",
            "city": "Atlanta",
            "country": "USA",
            "tradition": "Modern Puppetry",
            "lat": 33.7908,
            "lon": -84.3835,
            "era": "1978",
            "notes": "Largest US puppetry museum with Jim Henson collection wing",
        },
        {
            "name": "Museu da Marioneta Lisbon",
            "city": "Lisbon",
            "country": "Portugal",
            "tradition": "Portuguese Puppetry",
            "lat": 38.7069,
            "lon": -9.1457,
            "era": "2001",
            "notes": "National puppet museum in a former convent with world collection",
        },
    ]
    return pd.DataFrame(rows)


def _render_doll_puppet():
    df = _fetch_doll_puppet()
    st.markdown("#### Doll & Puppet Traditions Worldwide")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Traditions", df["tradition"].nunique())
    c4.metric("Unique Eras", df["era"].nunique())

    m = _base_map(center=[25, 30], zoom=2)
    for idx, r in df.iterrows():
        clr = _clr(idx)
        p = _popup(r["name"], _CLR_RED, [
            ("City", f"{r['city']}, {r['country']}"),
            ("Tradition", r["tradition"]),
            ("Era", r["era"]),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["name", "city", "country", "tradition", "era", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df),
        "doll_puppet_traditions.csv", "text/csv", key="dl_dolls",
    )


# =====================================================================
# 5. MODEL TRAIN HERITAGE
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_model_trains():
    rows = [
        {
            "name": "Miniatur Wunderland",
            "city": "Hamburg",
            "country": "Germany",
            "type": "Exhibition",
            "lat": 53.5437,
            "lon": 9.9887,
            "year": 2001,
            "notes": "Worlds largest model railway with 16 km of track and 1040 trains",
        },
        {
            "name": "Maerklin Museum",
            "city": "Goeppingen",
            "country": "Germany",
            "type": "Museum",
            "lat": 48.7059,
            "lon": 9.6528,
            "year": 2005,
            "notes": "Home of Maerklin tinplate trains since 1859, H0 and Z gauge pioneers",
        },
        {
            "name": "Maerklin Factory",
            "city": "Goeppingen",
            "country": "Germany",
            "type": "Factory",
            "lat": 48.7016,
            "lon": 9.6475,
            "year": 1859,
            "notes": "Oldest continuously operating model train manufacturer in the world",
        },
        {
            "name": "Hornby Visitor Centre",
            "city": "Margate",
            "country": "UK",
            "type": "Museum",
            "lat": 51.3890,
            "lon": 1.3838,
            "year": 1920,
            "notes": "British model railway icon known for Dublo and OO gauge heritage",
        },
        {
            "name": "Lionel Store and Museum",
            "city": "Concord",
            "country": "USA",
            "type": "Museum/Retail",
            "lat": 35.4087,
            "lon": -80.5795,
            "year": 1900,
            "notes": "Iconic American O-gauge trains founded by Joshua Lionel Cowen",
        },
        {
            "name": "Pendon Museum",
            "city": "Long Wittenham",
            "country": "UK",
            "type": "Museum",
            "lat": 51.6363,
            "lon": -1.2084,
            "year": 1954,
            "notes": "Exquisitely hand-built English countryside model in OO scale",
        },
        {
            "name": "Fleischmann Heritage Nuremberg",
            "city": "Nuremberg",
            "country": "Germany",
            "type": "Historic",
            "lat": 49.4521,
            "lon": 11.0767,
            "year": 1887,
            "notes": "Fleischmann began with tinplate toys, later pioneered HO trains",
        },
        {
            "name": "Model Railroader Magazine HQ",
            "city": "Waukesha",
            "country": "USA",
            "type": "Publishing",
            "lat": 43.0117,
            "lon": -88.2312,
            "year": 1934,
            "notes": "Kalmbach Media publishes the most influential railroad periodical",
        },
        {
            "name": "Train World Brussels",
            "city": "Brussels",
            "country": "Belgium",
            "type": "Museum",
            "lat": 50.8607,
            "lon": 4.3626,
            "year": 2015,
            "notes": "Belgian railway heritage museum at Schaerbeek with stunning layouts",
        },
        {
            "name": "Northlandz",
            "city": "Flemington",
            "country": "USA",
            "type": "Exhibition",
            "lat": 40.5123,
            "lon": -74.8596,
            "year": 1997,
            "notes": "Worlds largest model railroad exhibit with 8 miles of track",
        },
        {
            "name": "Swiss Transport Museum Railway",
            "city": "Lucerne",
            "country": "Switzerland",
            "type": "Museum",
            "lat": 47.0530,
            "lon": 8.3375,
            "year": 1959,
            "notes": "Massive Swiss railway model recreating the famous Gotthard route",
        },
        {
            "name": "Hara Model Railway Museum",
            "city": "Yokohama",
            "country": "Japan",
            "type": "Museum",
            "lat": 35.4558,
            "lon": 139.6317,
            "year": 2012,
            "notes": "Worlds largest private model train collection with 6000+ items",
        },
        {
            "name": "LGB Garden Railway (Lehmann)",
            "city": "Nuremberg",
            "country": "Germany",
            "type": "Historic",
            "lat": 49.4500,
            "lon": 11.0830,
            "year": 1968,
            "notes": "Lehmann Gross Bahn pioneered large-scale outdoor garden railways",
        },
        {
            "name": "Bachmann Industries HQ",
            "city": "Philadelphia",
            "country": "USA",
            "type": "HQ",
            "lat": 39.9526,
            "lon": -75.1652,
            "year": 1833,
            "notes": "Major HO and N scale manufacturer, Thomas and Friends trains",
        },
        {
            "name": "Kato USA Headquarters",
            "city": "Schaumburg",
            "country": "USA",
            "type": "HQ",
            "lat": 42.0334,
            "lon": -88.0834,
            "year": 1986,
            "notes": "Japanese precision N-scale and HO gauge trains for the US market",
        },
        {
            "name": "Modelspoor Museum",
            "city": "Sneek",
            "country": "Netherlands",
            "type": "Museum",
            "lat": 53.0335,
            "lon": 5.6605,
            "year": 2007,
            "notes": "Dutch model railway museum with interactive exhibits and layouts",
        },
    ]
    return pd.DataFrame(rows)


def _render_model_trains():
    df = _fetch_model_trains()
    st.markdown("#### Model Train Heritage")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())
    c4.metric("Oldest", int(df["year"].min()))

    m = _base_map(center=[45, 5], zoom=3)
    for _, r in df.iterrows():
        p = _popup(r["name"], _CLR_EMERALD, [
            ("City", f"{r['city']}, {r['country']}"),
            ("Type", r["type"]),
            ("Since", str(r["year"])),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=_CLR_EMERALD,
            fill=True,
            fill_color=_CLR_EMERALD,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["name", "city", "country", "type", "year", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df), "model_trains.csv", "text/csv", key="dl_trains",
    )


# =====================================================================
# 6. TEDDY BEAR ORIGINS
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_teddy_bears():
    rows = [
        {
            "name": "Steiff Museum and Factory",
            "city": "Giengen an der Brenz",
            "country": "Germany",
            "type": "Museum/Factory",
            "lat": 48.6223,
            "lon": 10.2432,
            "year": 1880,
            "notes": "Inventor of the teddy bear 1902, button-in-ear trademark, Margarete Steiff",
        },
        {
            "name": "Vermont Teddy Bear Factory",
            "city": "Shelburne",
            "country": "USA",
            "type": "Factory/Tour",
            "lat": 44.3831,
            "lon": -73.2268,
            "year": 1981,
            "notes": "Handmade in Vermont with factory tours and Bear-Gram gift service",
        },
        {
            "name": "Merrythought Factory",
            "city": "Ironbridge",
            "country": "UK",
            "type": "Factory",
            "lat": 52.6275,
            "lon": -2.4873,
            "year": 1930,
            "notes": "The last British teddy bear factory still operating in Shropshire",
        },
        {
            "name": "Teddy Bear Museum Stratford",
            "city": "Stratford-upon-Avon",
            "country": "UK",
            "type": "Museum",
            "lat": 52.1917,
            "lon": -1.7083,
            "year": 1988,
            "notes": "Collection of antique and artist teddy bears in Shakespeare country",
        },
        {
            "name": "Spielzeug Welten Museum Teddy Collection",
            "city": "Basel",
            "country": "Switzerland",
            "type": "Museum",
            "lat": 47.5562,
            "lon": 7.5888,
            "year": 1998,
            "notes": "Worlds largest teddy bear collection with over 6000 bears on display",
        },
        {
            "name": "Ideal Toy Company Heritage Site",
            "city": "New York City",
            "country": "USA",
            "type": "Historic",
            "lat": 40.7128,
            "lon": -74.0060,
            "year": 1903,
            "notes": "Morris Michtom created the teddy bear after a Roosevelt cartoon 1902",
        },
        {
            "name": "Teddy Bear Museum Jeju Island",
            "city": "Jeju",
            "country": "South Korea",
            "type": "Museum",
            "lat": 33.2503,
            "lon": 126.4101,
            "year": 2001,
            "notes": "Popular tourist museum with teddy bear dioramas of world history",
        },
        {
            "name": "Teddy Island Pattaya",
            "city": "Pattaya",
            "country": "Thailand",
            "type": "Museum",
            "lat": 12.9236,
            "lon": 100.8825,
            "year": 2014,
            "notes": "Themed rooms with over 2000 teddy bears in immersive settings",
        },
        {
            "name": "Hermann Teddy Original Factory",
            "city": "Hirschaid",
            "country": "Germany",
            "type": "Factory",
            "lat": 49.8167,
            "lon": 10.9833,
            "year": 1920,
            "notes": "Fourth-generation family German teddy bear maker for collectors",
        },
        {
            "name": "Clemens Bears Factory",
            "city": "Kirchardt",
            "country": "Germany",
            "type": "Factory",
            "lat": 49.2167,
            "lon": 8.9833,
            "year": 1948,
            "notes": "Family-run German teddy bear manufacturer with handmade plush",
        },
        {
            "name": "Canterbury Bears Workshop",
            "city": "Canterbury",
            "country": "UK",
            "type": "Workshop",
            "lat": 51.2802,
            "lon": 1.0789,
            "year": 1980,
            "notes": "Award-winning British handmade teddy bears artisan workshop",
        },
        {
            "name": "Charlie Bears HQ",
            "city": "Launceston",
            "country": "UK",
            "type": "HQ",
            "lat": 50.6370,
            "lon": -4.3595,
            "year": 2005,
            "notes": "Modern collectible bear brand designed by Charlie and William Morris",
        },
        {
            "name": "Teddy Museum Gimhae",
            "city": "Gimhae",
            "country": "South Korea",
            "type": "Museum",
            "lat": 35.2285,
            "lon": 128.8894,
            "year": 2010,
            "notes": "Korean teddy museum with historical scenes recreated by bears",
        },
        {
            "name": "Steiff Flagship Store Berlin",
            "city": "Berlin",
            "country": "Germany",
            "type": "Retail",
            "lat": 52.5200,
            "lon": 13.4050,
            "year": 2007,
            "notes": "Premium Steiff brand flagship store in the German capital city",
        },
        {
            "name": "Teddy Bear Republic N Seoul Tower",
            "city": "Seoul",
            "country": "South Korea",
            "type": "Museum",
            "lat": 37.5519,
            "lon": 126.9918,
            "year": 2015,
            "notes": "Museum atop N Seoul Tower with miniature dioramas of Korean culture",
        },
    ]
    return pd.DataFrame(rows)


def _render_teddy_bears():
    df = _fetch_teddy_bears()
    st.markdown("#### Teddy Bear Origins & Museums")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())
    c4.metric("Oldest", int(df["year"].min()))

    m = _base_map(center=[45, 10], zoom=3)
    type_clr = {
        "Museum/Factory": _CLR_AMBER,
        "Factory/Tour": _CLR_EMERALD,
        "Factory": _CLR_CYAN,
        "Museum": _CLR_VIOLET,
        "Historic": _CLR_RED,
        "Workshop": _CLR_PINK,
        "HQ": _CLR_BLUE,
        "Retail": _CLR_ORANGE,
    }
    for _, r in df.iterrows():
        clr = type_clr.get(r["type"], _CLR_AMBER)
        p = _popup(r["name"], _CLR_AMBER, [
            ("City", f"{r['city']}, {r['country']}"),
            ("Type", r["type"]),
            ("Year", str(r["year"])),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["name", "city", "country", "type", "year", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df), "teddy_bears.csv", "text/csv", key="dl_teddy",
    )


# =====================================================================
# 7. VIDEO GAME CONSOLE HISTORY
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_video_games():
    rows = [
        {
            "name": "Nintendo Headquarters",
            "city": "Kyoto",
            "country": "Japan",
            "brand": "NES, SNES, N64, Wii, Switch",
            "lat": 34.9700,
            "lon": 135.7568,
            "founded": 1889,
            "notes": "Started as playing card company, launched Famicom 1983 and Switch 2017",
        },
        {
            "name": "Atari Birthplace Sunnyvale",
            "city": "Sunnyvale",
            "country": "USA",
            "brand": "Atari 2600, Pong",
            "lat": 37.3688,
            "lon": -122.0363,
            "founded": 1972,
            "notes": "Nolan Bushnell and Ted Dabney founded Atari and launched Pong 1972",
        },
        {
            "name": "Sega Headquarters Tokyo",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "Genesis/Mega Drive, Dreamcast",
            "lat": 35.6634,
            "lon": 139.7300,
            "founded": 1960,
            "notes": "Genesis challenged Nintendo, Dreamcast pioneered online gaming 1999",
        },
        {
            "name": "Xbox / Microsoft Campus",
            "city": "Redmond",
            "country": "USA",
            "brand": "Xbox, Xbox 360, Xbox Series X/S",
            "lat": 47.6740,
            "lon": -122.1215,
            "founded": 2001,
            "notes": "Microsoft entered console market 2001 with Halo as launch title",
        },
        {
            "name": "PlayStation / Sony Interactive HQ",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "PlayStation 1 through 5",
            "lat": 35.6595,
            "lon": 139.7406,
            "founded": 1994,
            "notes": "PS1 launched 1994, PS2 best-selling console ever at 155 million units",
        },
        {
            "name": "Valve Corporation (Steam Deck)",
            "city": "Bellevue",
            "country": "USA",
            "brand": "Steam platform, Steam Deck",
            "lat": 47.6101,
            "lon": -122.2015,
            "founded": 1996,
            "notes": "Steam revolutionized PC gaming distribution, Steam Deck launched 2022",
        },
        {
            "name": "Magnavox Odyssey Origin",
            "city": "Fort Wayne",
            "country": "USA",
            "brand": "Magnavox Odyssey",
            "lat": 41.0793,
            "lon": -85.1394,
            "founded": 1972,
            "notes": "Ralph Baer designed the first home console, the Odyssey released 1972",
        },
        {
            "name": "Coleco Industries Heritage",
            "city": "Hartford",
            "country": "USA",
            "brand": "ColecoVision",
            "lat": 41.7658,
            "lon": -72.6734,
            "founded": 1932,
            "notes": "ColecoVision 1982 brought near arcade-quality home gaming",
        },
        {
            "name": "NEC PC Engine Origins",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "PC Engine / TurboGrafx-16",
            "lat": 35.6894,
            "lon": 139.6917,
            "founded": 1987,
            "notes": "First console with CD-ROM add-on, hugely popular in Japan",
        },
        {
            "name": "SNK Headquarters Osaka",
            "city": "Osaka",
            "country": "Japan",
            "brand": "Neo Geo AES/MVS",
            "lat": 34.6937,
            "lon": 135.5023,
            "founded": 1978,
            "notes": "Neo Geo arcade/home hybrid, King of Fighters and Metal Slug home",
        },
        {
            "name": "Mattel Intellivision Heritage",
            "city": "El Segundo",
            "country": "USA",
            "brand": "Intellivision",
            "lat": 33.9178,
            "lon": -118.4003,
            "founded": 1979,
            "notes": "Mattel Intellivision was the first serious Atari 2600 competitor",
        },
        {
            "name": "Commodore HQ Heritage",
            "city": "West Chester",
            "country": "USA",
            "brand": "Commodore 64, Amiga",
            "lat": 39.9607,
            "lon": -75.6055,
            "founded": 1954,
            "notes": "Commodore 64 best-selling single computer model ever at 17M units",
        },
        {
            "name": "Strong Museum Video Game Hall of Fame",
            "city": "Rochester",
            "country": "USA",
            "brand": "Video Game Hall of Fame",
            "lat": 43.1559,
            "lon": -77.6041,
            "founded": 2015,
            "notes": "World Video Game Hall of Fame inductees include Pong, Tetris, Doom",
        },
        {
            "name": "National Videogame Museum Sheffield",
            "city": "Sheffield",
            "country": "UK",
            "brand": "National museum",
            "lat": 53.3811,
            "lon": -1.4701,
            "founded": 2015,
            "notes": "UKs national museum of video games with playable exhibits",
        },
        {
            "name": "Computerspielemuseum Berlin",
            "city": "Berlin",
            "country": "Germany",
            "brand": "Video game museum",
            "lat": 52.5153,
            "lon": 13.4497,
            "founded": 1997,
            "notes": "One of the worlds first video game museums, 300+ playable exhibits",
        },
    ]
    return pd.DataFrame(rows)


def _render_video_games():
    df = _fetch_video_games()
    st.markdown("#### Video Game Console History")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Brands", df["brand"].nunique())
    c4.metric("Oldest", int(df["founded"].min()))

    m = _base_map(center=[35, -30], zoom=2)
    for idx, r in df.iterrows():
        clr = _clr(idx)
        p = _popup(r["name"], _CLR_BLUE, [
            ("City", f"{r['city']}, {r['country']}"),
            ("Brand", r["brand"]),
            ("Founded", str(r["founded"])),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["name", "city", "country", "brand", "founded", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df),
        "video_game_consoles.csv", "text/csv", key="dl_consoles",
    )


# =====================================================================
# 8. COMIC & ACTION FIGURE HUBS
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_comic_figures():
    rows = [
        {
            "name": "Marvel Comics Headquarters",
            "city": "New York City",
            "country": "USA",
            "brand": "Marvel / Disney",
            "lat": 40.7580,
            "lon": -73.9855,
            "year": 1939,
            "notes": "Timely Comics 1939, became Marvel, now Disney-owned, midtown Manhattan",
        },
        {
            "name": "DC Comics Headquarters",
            "city": "Burbank",
            "country": "USA",
            "brand": "DC / Warner Bros Discovery",
            "lat": 34.1531,
            "lon": -118.3240,
            "year": 1934,
            "notes": "Home of Batman and Superman, part of Warner Bros Discovery",
        },
        {
            "name": "Funko Headquarters and Store",
            "city": "Everett",
            "country": "USA",
            "brand": "Funko Pop! vinyl figures",
            "lat": 47.9790,
            "lon": -122.2021,
            "year": 1998,
            "notes": "Funko Pop vinyl collectibles with massive HQ store and exclusives",
        },
        {
            "name": "Tamashii Nations (Bandai Spirits)",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "S.H. Figuarts, Chogokin",
            "lat": 35.6265,
            "lon": 139.7775,
            "year": 1997,
            "notes": "Premium collector figures for Gundam, Dragon Ball, Kamen Rider",
        },
        {
            "name": "McFarlane Toys Headquarters",
            "city": "Tempe",
            "country": "USA",
            "brand": "McFarlane Toys, Spawn",
            "lat": 33.4255,
            "lon": -111.9400,
            "year": 1994,
            "notes": "Todd McFarlane Spawn creator, DC Multiverse and sports figures",
        },
        {
            "name": "NECA Headquarters",
            "city": "Hillside",
            "country": "USA",
            "brand": "NECA, WizKids",
            "lat": 40.6964,
            "lon": -74.2301,
            "year": 1996,
            "notes": "Specializing in horror and movie licensed collectible figures",
        },
        {
            "name": "Hasbro (G.I. Joe and Transformers)",
            "city": "Pawtucket",
            "country": "USA",
            "brand": "G.I. Joe, Transformers, Marvel Legends",
            "lat": 41.8787,
            "lon": -71.3826,
            "year": 1964,
            "notes": "G.I. Joe coined action figure term 1964, Transformers launched 1984",
        },
        {
            "name": "Good Smile Company HQ",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "Nendoroid, figma",
            "lat": 35.6997,
            "lon": 139.7745,
            "year": 2001,
            "notes": "Japanese figure maker known for Nendoroid chibi and figma lines",
        },
        {
            "name": "Kotobukiya Headquarters",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "ARTFX, Bishoujo statues",
            "lat": 35.7052,
            "lon": 139.7710,
            "year": 1947,
            "notes": "Japanese model kit and statue maker, DC and Marvel licenses",
        },
        {
            "name": "Medicom Toy (BE@RBRICK)",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "BE@RBRICK, MAFEX, RAH",
            "lat": 35.6580,
            "lon": 139.7015,
            "year": 1996,
            "notes": "BE@RBRICK designer bears and MAFEX action figures, art toy pioneer",
        },
        {
            "name": "Super7 Headquarters",
            "city": "San Francisco",
            "country": "USA",
            "brand": "ReAction Figures, Ultimates",
            "lat": 37.7749,
            "lon": -122.4194,
            "year": 2001,
            "notes": "Retro ReAction figures and Thundercats/TMNT Ultimates lines",
        },
        {
            "name": "Mezco Toyz Studio",
            "city": "New York City",
            "country": "USA",
            "brand": "One:12 Collective",
            "lat": 40.7484,
            "lon": -73.9967,
            "year": 2000,
            "notes": "Premium 1/12 cloth-costumed figures and Living Dead Dolls",
        },
        {
            "name": "Cite de la Bande Dessinee",
            "city": "Angouleme",
            "country": "France",
            "brand": "Angouleme BD Festival/Museum",
            "lat": 45.6500,
            "lon": 0.1600,
            "year": 1991,
            "notes": "French comic strip national museum, worlds second largest BD festival",
        },
        {
            "name": "Belgian Comic Strip Center",
            "city": "Brussels",
            "country": "Belgium",
            "brand": "Tintin, Smurfs, Lucky Luke",
            "lat": 50.8528,
            "lon": 4.3592,
            "year": 1989,
            "notes": "Art Nouveau Horta building with Herge Tintin archives",
        },
        {
            "name": "Akihabara Electric Town",
            "city": "Tokyo",
            "country": "Japan",
            "brand": "Anime and manga figure mecca",
            "lat": 35.6984,
            "lon": 139.7731,
            "year": 1950,
            "notes": "Tokyos anime and figure paradise with hundreds of collector shops",
        },
        {
            "name": "San Diego Comic-Con International",
            "city": "San Diego",
            "country": "USA",
            "brand": "SDCC Exclusive figures",
            "lat": 32.7157,
            "lon": -117.1611,
            "year": 1970,
            "notes": "Worlds largest comic and pop culture convention with exclusives",
        },
        {
            "name": "Tezuka Osamu Manga Museum",
            "city": "Takarazuka",
            "country": "Japan",
            "brand": "Astro Boy, Black Jack",
            "lat": 34.8004,
            "lon": 135.3475,
            "year": 1994,
            "notes": "Museum honoring the God of Manga and creator of Astro Boy",
        },
        {
            "name": "Hot Toys Headquarters",
            "city": "Hong Kong",
            "country": "China",
            "brand": "Hot Toys 1/6 scale figures",
            "lat": 22.3193,
            "lon": 114.1694,
            "year": 2000,
            "notes": "Premium hyper-realistic 1/6 scale movie figures, Marvel and DC",
        },
        {
            "name": "Jakks Pacific Headquarters",
            "city": "Santa Monica",
            "country": "USA",
            "brand": "World of Nintendo, WWE, Disney",
            "lat": 34.0195,
            "lon": -118.4912,
            "year": 1995,
            "notes": "Licensed mass-market figures for Nintendo, Disney, and wrestling",
        },
        {
            "name": "Diamond Comic Distributors",
            "city": "Hunt Valley",
            "country": "USA",
            "brand": "Diamond Select Toys",
            "lat": 39.4945,
            "lon": -76.6412,
            "year": 1982,
            "notes": "Major US comic and collectible distributor with own toy line",
        },
    ]
    return pd.DataFrame(rows)


def _render_comic_figures():
    df = _fetch_comic_figures()
    st.markdown("#### Comic & Action Figure Hubs")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Brands", df["brand"].nunique())
    c4.metric("Oldest", int(df["year"].min()))

    m = _base_map(center=[35, -20], zoom=2)
    for idx, r in df.iterrows():
        clr = _clr(idx)
        p = _popup(r["name"], _CLR_PINK, [
            ("City", f"{r['city']}, {r['country']}"),
            ("Brand", r["brand"]),
            ("Year", str(r["year"])),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["name", "city", "country", "brand", "year", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df),
        "comic_action_figures.csv", "text/csv", key="dl_comics",
    )


# =====================================================================
# 9. TRADITIONAL TOY CRAFTS
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_traditional_crafts():
    rows = [
        {
            "toy": "Matryoshka Nesting Dolls",
            "country": "Russia",
            "region": "Sergiev Posad, Moscow Oblast",
            "lat": 56.3000,
            "lon": 38.1333,
            "era": "1890s",
            "notes": "Carved and painted wooden nesting dolls inspired by Japanese Daruma",
        },
        {
            "toy": "Daruma Doll",
            "country": "Japan",
            "region": "Takasaki, Gunma Prefecture",
            "lat": 36.3219,
            "lon": 139.0032,
            "era": "1700s",
            "notes": "Weighted roly-poly Bodhidharma doll for goal-setting and luck",
        },
        {
            "toy": "Pinata",
            "country": "Mexico",
            "region": "Mexico City and Acolman",
            "lat": 19.4326,
            "lon": -99.1332,
            "era": "1500s",
            "notes": "Paper-mache party vessel filled with candy, seven-pointed star form",
        },
        {
            "toy": "Erzgebirge Wooden Toys",
            "country": "Germany",
            "region": "Seiffen, Saxony",
            "lat": 50.6452,
            "lon": 13.4523,
            "era": "1600s",
            "notes": "Nutcrackers, smoking men, Christmas pyramids, UNESCO candidate",
        },
        {
            "toy": "Dala Horse (Dalahast)",
            "country": "Sweden",
            "region": "Nusnas, Dalarna",
            "lat": 60.9544,
            "lon": 14.7611,
            "era": "1600s",
            "notes": "Hand-carved and painted red wooden horse, national symbol of Sweden",
        },
        {
            "toy": "Kendama",
            "country": "Japan",
            "region": "Hatsukaichi, Hiroshima",
            "lat": 34.3486,
            "lon": 132.3317,
            "era": "1700s",
            "notes": "Cup-and-ball skill toy now a competitive sport with World Cups",
        },
        {
            "toy": "Kite (Patang)",
            "country": "India",
            "region": "Ahmedabad, Gujarat",
            "lat": 23.0225,
            "lon": 72.5714,
            "era": "Ancient",
            "notes": "Uttarayan festival with fighter kites using glass-coated string",
        },
        {
            "toy": "Wayang Kulit Shadow Puppets",
            "country": "Indonesia",
            "region": "Central Java",
            "lat": -7.6145,
            "lon": 110.7128,
            "era": "800 CE",
            "notes": "UNESCO ICH leather shadow puppets depicting Hindu and Javanese epics",
        },
        {
            "toy": "Kokeshi Dolls",
            "country": "Japan",
            "region": "Tohoku Region, Miyagi",
            "lat": 38.2682,
            "lon": 140.8694,
            "era": "1800s",
            "notes": "Handmade limbless cylindrical wooden dolls from hot spring towns",
        },
        {
            "toy": "Bilboquet (Cup and Ball)",
            "country": "France",
            "region": "Paris",
            "lat": 48.8566,
            "lon": 2.3522,
            "era": "1500s",
            "notes": "Popular with French royalty, King Henri III was famously addicted",
        },
        {
            "toy": "Boomerang",
            "country": "Australia",
            "region": "Central Australia",
            "lat": -23.7000,
            "lon": 133.8800,
            "era": "10000 BC",
            "notes": "Aboriginal returning throw-stick, oldest aerodynamic toy in the world",
        },
        {
            "toy": "Bamboo Dragonfly (Taketombo)",
            "country": "Japan",
            "region": "Nationwide Japan",
            "lat": 36.2048,
            "lon": 138.2529,
            "era": "400 CE",
            "notes": "Ancient helicopter propeller toy, precursor to rotary flight ideas",
        },
        {
            "toy": "Caga Tio (Pooping Log)",
            "country": "Spain",
            "region": "Catalonia",
            "lat": 41.3874,
            "lon": 2.1686,
            "era": "1600s",
            "notes": "Catalan Christmas tradition, a log that poops presents when hit",
        },
        {
            "toy": "Mancala Board Game",
            "country": "Ethiopia",
            "region": "Aksum, Tigray",
            "lat": 14.1210,
            "lon": 38.7469,
            "era": "600 CE",
            "notes": "Ancient counting and strategy game played across Africa and Asia",
        },
        {
            "toy": "Alebrije Spirit Animals",
            "country": "Mexico",
            "region": "Oaxaca",
            "lat": 17.0732,
            "lon": -96.7266,
            "era": "1930s",
            "notes": "Brightly painted fantastical creature carvings from copal wood",
        },
        {
            "toy": "Otedama Beanbags",
            "country": "Japan",
            "region": "Kyoto",
            "lat": 35.0116,
            "lon": 135.7681,
            "era": "700 CE",
            "notes": "Japanese juggling beanbags used in traditional singing games",
        },
        {
            "toy": "Tin Toys (Lithographed)",
            "country": "Germany",
            "region": "Nuremberg, Bavaria",
            "lat": 49.4521,
            "lon": 11.0767,
            "era": "1850s",
            "notes": "Lithographed tinplate mechanical toys from the world tin toy capital",
        },
        {
            "toy": "Whirligig Buzzer",
            "country": "Greece",
            "region": "Athens, Attica",
            "lat": 37.9838,
            "lon": 23.7275,
            "era": "500 BC",
            "notes": "Ancient spinning disc toy found in archaeological sites worldwide",
        },
        {
            "toy": "Kaleidoscope",
            "country": "UK",
            "region": "Edinburgh, Scotland",
            "lat": 55.9533,
            "lon": -3.1883,
            "era": "1817",
            "notes": "Invented by Sir David Brewster in Scotland, patented 1817",
        },
        {
            "toy": "Pelota Mixteca Ball",
            "country": "Mexico",
            "region": "Oaxaca Valley",
            "lat": 16.8531,
            "lon": -96.7170,
            "era": "1500 BC",
            "notes": "Ancient Mesoamerican ball game still played with leather gloves",
        },
    ]
    return pd.DataFrame(rows)


def _render_traditional_crafts():
    df = _fetch_traditional_crafts()
    st.markdown("#### Traditional Toy Crafts Around the World")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Crafts", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Regions", df["region"].nunique())
    c4.metric("Distinct Eras", df["era"].nunique())

    m = _base_map(center=[25, 30], zoom=2)
    for idx, r in df.iterrows():
        clr = _clr(idx)
        p = _popup(r["toy"], _CLR_ORANGE, [
            ("Country", r["country"]),
            ("Region", r["region"]),
            ("Era", r["era"]),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=9,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["toy"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["toy", "country", "region", "era", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df),
        "traditional_toy_crafts.csv", "text/csv", key="dl_crafts",
    )


# =====================================================================
# 10. THEME PARK TOY SHOPS
# =====================================================================
@st.cache_data(ttl=3600)
def _fetch_theme_park_shops():
    rows = [
        {
            "name": "World of Disney (Disney Springs)",
            "city": "Orlando",
            "country": "USA",
            "type": "Disney Store",
            "lat": 28.3712,
            "lon": -81.5193,
            "year": 1996,
            "notes": "Largest Disney character merchandise store in the world",
        },
        {
            "name": "World of Disney (Downtown Disney)",
            "city": "Anaheim",
            "country": "USA",
            "type": "Disney Store",
            "lat": 33.8091,
            "lon": -117.9220,
            "year": 2001,
            "notes": "Major Disney retail destination at the Disneyland Resort California",
        },
        {
            "name": "Disney Store Champs-Elysees",
            "city": "Paris",
            "country": "France",
            "type": "Disney Store",
            "lat": 48.8698,
            "lon": 2.3076,
            "year": 2012,
            "notes": "Flagship Disney Store on the most famous avenue in Paris",
        },
        {
            "name": "Disney Store Shibuya",
            "city": "Tokyo",
            "country": "Japan",
            "type": "Disney Store",
            "lat": 35.6595,
            "lon": 139.7004,
            "year": 2012,
            "notes": "Multi-floor Disney flagship in Tokyos busiest shopping district",
        },
        {
            "name": "Emporium (Magic Kingdom Main Street)",
            "city": "Orlando",
            "country": "USA",
            "type": "Theme Park Shop",
            "lat": 28.4177,
            "lon": -81.5812,
            "year": 1971,
            "notes": "Iconic Main Street USA merchandise shop at Magic Kingdom",
        },
        {
            "name": "FAO Schwarz Rockefeller Center",
            "city": "New York City",
            "country": "USA",
            "type": "Flagship Toy Store",
            "lat": 40.7587,
            "lon": -73.9787,
            "year": 1862,
            "notes": "Legendary NYC toy store, famous piano scene in the movie Big",
        },
        {
            "name": "Hamleys Regent Street",
            "city": "London",
            "country": "UK",
            "type": "Flagship Toy Store",
            "lat": 51.5130,
            "lon": -0.1400,
            "year": 1760,
            "notes": "Worlds oldest and largest toy store, 7 floors on Regent Street",
        },
        {
            "name": "Toys R Us Flagship Times Square (former)",
            "city": "New York City",
            "country": "USA",
            "type": "Flagship Toy Store",
            "lat": 40.7580,
            "lon": -73.9855,
            "year": 2001,
            "notes": "Iconic 110000 sq ft store with indoor Ferris wheel, closed 2015",
        },
        {
            "name": "Toys R Us Tokyo Sunshine City",
            "city": "Tokyo",
            "country": "Japan",
            "type": "Flagship Toy Store",
            "lat": 35.7295,
            "lon": 139.7193,
            "year": 1991,
            "notes": "Major location in Ikebukuro, Japan kept stores after US bankruptcy",
        },
        {
            "name": "LEGO Store Leicester Square",
            "city": "London",
            "country": "UK",
            "type": "LEGO Store",
            "lat": 51.5103,
            "lon": -0.1301,
            "year": 2016,
            "notes": "Worlds largest LEGO store with Big Ben mosaic and facade dragon",
        },
        {
            "name": "LEGO Store Fifth Avenue",
            "city": "New York City",
            "country": "USA",
            "type": "LEGO Store",
            "lat": 40.7584,
            "lon": -73.9748,
            "year": 2021,
            "notes": "Immersive LEGO retail with brick-built Statue of Liberty replica",
        },
        {
            "name": "Build-A-Bear Workshop Flagship",
            "city": "St. Louis",
            "country": "USA",
            "type": "Experience Store",
            "lat": 38.6270,
            "lon": -90.1994,
            "year": 1997,
            "notes": "Original Build-A-Bear concept store for interactive plush creation",
        },
        {
            "name": "Hamleys Mumbai",
            "city": "Mumbai",
            "country": "India",
            "type": "Flagship Toy Store",
            "lat": 18.9388,
            "lon": 72.8354,
            "year": 2016,
            "notes": "Largest toy store in India, Hamleys branded, across 5 floors",
        },
        {
            "name": "Kiddy Land Harajuku",
            "city": "Tokyo",
            "country": "Japan",
            "type": "Character Goods Store",
            "lat": 35.6695,
            "lon": 139.7074,
            "year": 1950,
            "notes": "Iconic Harajuku toy and character goods store, 4 floors of kawaii",
        },
        {
            "name": "Pokemon Center Mega Tokyo",
            "city": "Tokyo",
            "country": "Japan",
            "type": "Character Store",
            "lat": 35.7295,
            "lon": 139.7193,
            "year": 2014,
            "notes": "Largest official Pokemon store in Japan with exclusive merchandise",
        },
        {
            "name": "Universal Studios Store CityWalk",
            "city": "Orlando",
            "country": "USA",
            "type": "Theme Park Shop",
            "lat": 28.4747,
            "lon": -81.4662,
            "year": 1999,
            "notes": "Harry Potter, Jurassic World, Minions merchandise hub",
        },
        {
            "name": "Ollivanders Wand Shop (Wizarding World)",
            "city": "Orlando",
            "country": "USA",
            "type": "Theme Park Shop",
            "lat": 28.4722,
            "lon": -81.4725,
            "year": 2010,
            "notes": "Interactive wand selection at the Wizarding World of Harry Potter",
        },
        {
            "name": "Star Wars Trading Post Disney Springs",
            "city": "Orlando",
            "country": "USA",
            "type": "Disney Store",
            "lat": 28.3702,
            "lon": -81.5181,
            "year": 2020,
            "notes": "Dedicated Star Wars store with custom lightsaber building",
        },
        {
            "name": "Joypolis Sega Odaiba",
            "city": "Tokyo",
            "country": "Japan",
            "type": "Arcade and Shop",
            "lat": 35.6267,
            "lon": 139.7750,
            "year": 1996,
            "notes": "Sega indoor theme park in Odaiba with arcade and merchandise",
        },
    ]
    return pd.DataFrame(rows)


def _render_theme_park_shops():
    df = _fetch_theme_park_shops()
    st.markdown("#### Theme Park Toy Shops & Flagship Stores")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Types", df["type"].nunique())
    c4.metric("Oldest", int(df["year"].min()))

    m = _base_map(center=[30, -20], zoom=2)
    type_clr = {
        "Disney Store": _CLR_BLUE,
        "Theme Park Shop": _CLR_AMBER,
        "Flagship Toy Store": _CLR_PINK,
        "LEGO Store": _CLR_YELLOW,
        "Experience Store": _CLR_EMERALD,
        "Character Goods Store": _CLR_VIOLET,
        "Character Store": _CLR_PURPLE,
        "Arcade and Shop": _CLR_TEAL,
    }
    for _, r in df.iterrows():
        clr = type_clr.get(r["type"], _CLR_CYAN)
        p = _popup(r["name"], _CLR_AMBER, [
            ("City", f"{r['city']}, {r['country']}"),
            ("Type", r["type"]),
            ("Year", str(r["year"])),
            ("Notes", r["notes"]),
        ])
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.75,
            popup=folium.Popup(p, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show(m)

    st.dataframe(
        df[["name", "city", "country", "type", "year", "notes"]],
        use_container_width=True,
    )
    st.download_button(
        "Download CSV", _csv(df),
        "theme_park_toy_shops.csv", "text/csv", key="dl_shops",
    )


# =====================================================================
# MAP MODE REGISTRY
# =====================================================================
_MAP_MODES = {
    "LEGO World": _render_lego_world,
    "Toy Museums": _render_toy_museums,
    "Famous Toy Factories": _render_toy_factories,
    "Doll & Puppet Traditions": _render_doll_puppet,
    "Model Train Heritage": _render_model_trains,
    "Teddy Bear Origins": _render_teddy_bears,
    "Video Game Console History": _render_video_games,
    "Comic & Action Figure Hubs": _render_comic_figures,
    "Traditional Toy Crafts": _render_traditional_crafts,
    "Theme Park Toy Shops": _render_theme_park_shops,
}


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================
def render_toy_maps_tab():
    """Main entry point for the Toys & Collectibles Maps tab."""
    st.markdown(
        '<div class="tab-header amber">'
        '<h4>\U0001f9f8 Toys & Collectibles Maps</h4>'
        '<p>Toy history, factories, museums, and collectors worldwide</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    selected = st.selectbox(
        "Map Mode",
        list(_MAP_MODES.keys()),
        key="toy_maps_mode_select",
    )

    if st.button("Generate Map", key="toy_maps_gen", type="primary"):
        with st.spinner("Building map..."):
            _MAP_MODES[selected]()
    else:
        st.info(
            "Select a map mode above and click **Generate Map** to explore."
        )
