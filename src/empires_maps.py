# -*- coding: utf-8 -*-
"""
Ancient Empires & Kingdoms Maps module for TerraScout AI.
Provides 10 interactive map modes covering the rise and fall of major
historical empires, capital cities, battle sites, and territorial extents.
All data is curated/hardcoded for offline reliability — no API keys needed.
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
# COLOUR PALETTE (TerraScout dark theme)
# =====================================================================
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
ACCENT_CYAN = "#06b6d4"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_AMBER = "#f59e0b"
ACCENT_EMERALD = "#10b981"
ACCENT_PINK = "#ec4899"
ACCENT_RED = "#ef4444"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"

EMPIRE_COLORS = [
    "#06b6d4", "#ec4899", "#8b5cf6", "#f59e0b", "#10b981",
    "#ef4444", "#3b82f6", "#f97316", "#14b8a6", "#a855f7",
    "#e11d48", "#84cc16", "#facc15", "#22d3ee", "#c084fc",
]


def _color_for(index: int) -> str:
    return EMPIRE_COLORS[index % len(EMPIRE_COLORS)]


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
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


def _base_map(center=None, zoom=3):
    if center is None:
        center = [30, 20]
    return folium.Map(
        location=center, zoom_start=zoom,
        tiles="CartoDB dark_matter", width="100%", height=500,
    )


def _show_map(m):
    components.html(m._repr_html_(), height=500)


def _df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


# =====================================================================
# 1. ROMAN EMPIRE
# Curated dataset of major cities, provinces, road network, and the
# approximate polygon for maximum territorial extent under Trajan (117 AD).
# Population estimates from ancient census records and modern scholarship.
# =====================================================================
@st.cache_data(ttl=3600)
def _get_roman_data():
    cities = [
        {"name": "Roma", "type": "Capital", "province": "Italia", "lat": 41.9028, "lon": 12.4964, "pop_est": 1000000, "notes": "Caput Mundi, eternal capital of the empire"},
        {"name": "Constantinople", "type": "Capital (East)", "province": "Thracia", "lat": 41.0082, "lon": 28.9784, "pop_est": 500000, "notes": "Founded 330 AD by Constantine I"},
        {"name": "Alexandria", "type": "Major City", "province": "Aegyptus", "lat": 31.2001, "lon": 29.9187, "pop_est": 600000, "notes": "Great Library, Pharos lighthouse"},
        {"name": "Antioch", "type": "Major City", "province": "Syria", "lat": 36.2021, "lon": 36.1605, "pop_est": 250000, "notes": "Third largest city, gateway to the East"},
        {"name": "Carthage", "type": "Major City", "province": "Africa Proconsularis", "lat": 36.8528, "lon": 10.3234, "pop_est": 300000, "notes": "Rebuilt by Rome after Punic Wars"},
        {"name": "Londinium", "type": "Provincial Capital", "province": "Britannia", "lat": 51.5074, "lon": -0.1278, "pop_est": 60000, "notes": "Capital of Roman Britain"},
        {"name": "Lutetia", "type": "Town", "province": "Gallia Lugdunensis", "lat": 48.8566, "lon": 2.3522, "pop_est": 30000, "notes": "Modern Paris, Gallic-Roman settlement"},
        {"name": "Mediolanum", "type": "Imperial Seat", "province": "Italia", "lat": 45.4642, "lon": 9.1900, "pop_est": 100000, "notes": "Western imperial capital from 286 AD"},
        {"name": "Ravenna", "type": "Imperial Seat", "province": "Italia", "lat": 44.4184, "lon": 12.2035, "pop_est": 50000, "notes": "Capital of Western Empire from 402 AD"},
        {"name": "Augusta Treverorum", "type": "Imperial Seat", "province": "Gallia Belgica", "lat": 49.7490, "lon": 6.6371, "pop_est": 80000, "notes": "Modern Trier, imperial residence"},
        {"name": "Ephesus", "type": "Major City", "province": "Asia", "lat": 37.9394, "lon": 27.3417, "pop_est": 250000, "notes": "Temple of Artemis, Library of Celsus"},
        {"name": "Corinth", "type": "Provincial Capital", "province": "Achaea", "lat": 37.9057, "lon": 22.8765, "pop_est": 100000, "notes": "Rebuilt by Julius Caesar in 44 BC"},
        {"name": "Athens", "type": "Cultural Center", "province": "Achaea", "lat": 37.9838, "lon": 23.7275, "pop_est": 50000, "notes": "Philosophical and cultural heart of the empire"},
        {"name": "Jerusalem", "type": "Provincial City", "province": "Judaea", "lat": 31.7683, "lon": 35.2137, "pop_est": 80000, "notes": "Destroyed 70 AD, renamed Aelia Capitolina"},
        {"name": "Colonia Agrippina", "type": "Provincial Capital", "province": "Germania Inferior", "lat": 50.9375, "lon": 6.9603, "pop_est": 40000, "notes": "Modern Cologne, major Rhine garrison"},
        {"name": "Leptis Magna", "type": "Major City", "province": "Africa", "lat": 32.6383, "lon": 14.2933, "pop_est": 80000, "notes": "Birthplace of Septimius Severus"},
        {"name": "Pompeii", "type": "Town", "province": "Italia", "lat": 40.7509, "lon": 14.4869, "pop_est": 20000, "notes": "Buried by Vesuvius 79 AD"},
        {"name": "Byzantium", "type": "Major City", "province": "Thracia", "lat": 41.0136, "lon": 28.9550, "pop_est": 40000, "notes": "Refounded as Constantinople"},
        {"name": "Massilia", "type": "Trading City", "province": "Gallia Narbonensis", "lat": 43.2965, "lon": 5.3698, "pop_est": 50000, "notes": "Modern Marseille, Greek-Roman port"},
        {"name": "Hispalis", "type": "Provincial Capital", "province": "Baetica", "lat": 37.3886, "lon": -5.9823, "pop_est": 50000, "notes": "Modern Seville"},
    ]
    roads = [
        {"name": "Via Appia", "from": "Roma", "to": "Brindisi", "coords": [[41.90, 12.50], [41.12, 14.78], [40.63, 16.87]], "length_km": 540, "built": "312 BC"},
        {"name": "Via Aurelia", "from": "Roma", "to": "Massilia", "coords": [[41.90, 12.50], [42.44, 11.11], [43.30, 5.37]], "length_km": 1100, "built": "241 BC"},
        {"name": "Via Flaminia", "from": "Roma", "to": "Ariminum", "coords": [[41.90, 12.50], [42.72, 12.60], [44.06, 12.57]], "length_km": 310, "built": "220 BC"},
        {"name": "Via Egnatia", "from": "Dyrrachium", "to": "Constantinople", "coords": [[41.32, 19.45], [40.64, 22.94], [41.01, 28.98]], "length_km": 1120, "built": "146 BC"},
        {"name": "Via Salaria", "from": "Roma", "to": "Castrum Truentinum", "coords": [[41.90, 12.50], [42.46, 13.25], [42.89, 13.89]], "length_km": 242, "built": "4th century BC"},
        {"name": "Via Domitia", "from": "Nemausus", "to": "Hispania", "coords": [[43.84, 4.36], [43.18, 2.35], [42.70, 0.50]], "length_km": 560, "built": "118 BC"},
        {"name": "Via Augusta", "from": "Narbo", "to": "Gades", "coords": [[43.18, 3.00], [41.38, 2.17], [39.47, -0.38], [37.39, -5.98], [36.53, -6.29]], "length_km": 1500, "built": "8 BC"},
    ]
    extent = [
        [55.0, -5.0], [53.0, 1.0], [51.0, 5.0], [48.0, 8.0], [47.0, 16.0],
        [48.0, 25.0], [44.0, 28.0], [42.0, 40.0], [37.0, 42.0], [33.0, 44.0],
        [30.0, 36.0], [29.0, 33.0], [24.0, 33.0], [31.0, 30.0], [32.0, 24.0],
        [33.0, 13.0], [35.0, 10.0], [36.5, -1.0], [37.5, -8.0], [43.0, -9.0],
        [48.0, -5.0], [55.0, -5.0],
    ]
    return cities, roads, extent


def _render_roman_empire():
    cities, roads, extent = _get_roman_data()
    df = pd.DataFrame(cities)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities", len(cities))
    c2.metric("Roman Roads", len(roads))
    c3.metric("Peak Population", "~70M")
    c4.metric("Duration", "753 BC - 476 AD")

    m = _base_map([41.0, 18.0], 4)
    folium.Polygon(locations=extent, color=ACCENT_RED, fill=True,
                   fill_color=ACCENT_RED, fill_opacity=0.08, weight=1,
                   popup="Roman Empire max extent ~117 AD").add_to(m)
    for rd in roads:
        folium.PolyLine(rd["coords"], color=ACCENT_AMBER, weight=3,
                        dash_array="8 4",
                        popup=f"<b>{escape(rd['name'])}</b><br>{escape(rd['from'])} to {escape(rd['to'])}<br>{rd['length_km']} km, built {rd['built']}").add_to(m)
    for _, r in df.iterrows():
        color = ACCENT_RED if r["type"] in ("Capital", "Capital (East)") else ACCENT_CYAN
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=8 if "Capital" in r["type"] else 5,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>{escape(r['name'])}</b><br>{escape(r['type'])} — {escape(r['province'])}<br>Pop: ~{r['pop_est']:,}<br>{escape(r['notes'])}",
        ).add_to(m)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_df = df.sort_values("pop_est", ascending=True)
    ax.barh(sorted_df["name"], sorted_df["pop_est"], color=ACCENT_CYAN)
    ax.set_xlabel("Estimated Population")
    ax.set_title("Roman Empire — Major Cities by Population")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    st.image(_fig_to_bytes(fig), use_container_width=True)

    # Roads chart
    df_roads = pd.DataFrame(roads)
    fig2, ax2 = _dark_fig(figsize=(8, 3))
    ax2.barh(df_roads["name"], df_roads["length_km"], color=ACCENT_AMBER)
    ax2.set_xlabel("Length (km)")
    ax2.set_title("Roman Roads — Length in Kilometers")
    st.image(_fig_to_bytes(fig2), use_container_width=True)

    st.subheader("Cities")
    st.dataframe(df[["name", "type", "province", "pop_est", "lat", "lon", "notes"]], width="stretch")
    st.subheader("Roads")
    st.dataframe(df_roads[["name", "from", "to", "length_km", "built"]], width="stretch")
    st.download_button("Download Roman Cities CSV", _df_to_csv(df), "roman_empire_cities.csv", "text/csv")


# =====================================================================
# 2. GREEK CITY-STATES
# Curated data covering the major poleis of Classical, Hellenistic, and
# pre-Classical Greece including Minoan and Mycenaean precursors.
# =====================================================================
@st.cache_data(ttl=3600)
def _get_greek_data():
    return [
        {"name": "Athens", "type": "Polis", "region": "Attica", "lat": 37.9715, "lon": 23.7267, "peak_year": -450, "pop_est": 250000, "gov": "Democracy", "notes": "Birthplace of democracy, Parthenon, Socrates, Plato, Aristotle"},
        {"name": "Sparta", "type": "Polis", "region": "Laconia", "lat": 37.0755, "lon": 22.4303, "peak_year": -500, "pop_est": 50000, "gov": "Diarchy", "notes": "Warrior society, Thermopylae, Peloponnesian League"},
        {"name": "Corinth", "type": "Polis", "region": "Corinthia", "lat": 37.9057, "lon": 22.8765, "peak_year": -500, "pop_est": 90000, "gov": "Oligarchy", "notes": "Trade hub, two harbors, Corinthian order"},
        {"name": "Thebes", "type": "Polis", "region": "Boeotia", "lat": 38.3191, "lon": 23.3178, "peak_year": -371, "pop_est": 40000, "gov": "Oligarchy", "notes": "Sacred Band, Epaminondas, briefly hegemon of Greece"},
        {"name": "Argos", "type": "Polis", "region": "Argolis", "lat": 37.6316, "lon": 22.7258, "peak_year": -600, "pop_est": 30000, "gov": "Mixed", "notes": "Oldest city in Greece, rival of Sparta"},
        {"name": "Delphi", "type": "Sanctuary", "region": "Phocis", "lat": 38.4824, "lon": 22.5010, "peak_year": -500, "pop_est": 5000, "gov": "Sacred", "notes": "Oracle of Apollo, Pythia, navel of the world"},
        {"name": "Olympia", "type": "Sanctuary", "region": "Elis", "lat": 37.6388, "lon": 21.6299, "peak_year": -500, "pop_est": 3000, "gov": "Sacred", "notes": "Olympic Games founded 776 BC"},
        {"name": "Miletus", "type": "Polis", "region": "Ionia", "lat": 37.5308, "lon": 27.2783, "peak_year": -600, "pop_est": 100000, "gov": "Mixed", "notes": "Thales, first philosophers, Ionian Revolt"},
        {"name": "Ephesus", "type": "Polis", "region": "Ionia", "lat": 37.9394, "lon": 27.3417, "peak_year": -500, "pop_est": 60000, "gov": "Mixed", "notes": "Temple of Artemis, one of Seven Wonders"},
        {"name": "Syracuse", "type": "Colony", "region": "Sicily", "lat": 37.0755, "lon": 15.2866, "peak_year": -400, "pop_est": 250000, "gov": "Tyranny/Democracy", "notes": "Archimedes, rival of Athens and Carthage"},
        {"name": "Megara", "type": "Polis", "region": "Megaris", "lat": 37.9976, "lon": 23.3430, "peak_year": -600, "pop_est": 25000, "gov": "Oligarchy", "notes": "Founded Byzantium, mother of colonies"},
        {"name": "Pergamon", "type": "Kingdom", "region": "Mysia", "lat": 39.1217, "lon": 27.1838, "peak_year": -200, "pop_est": 80000, "gov": "Monarchy", "notes": "Library, Altar of Zeus, parchment invention"},
        {"name": "Rhodes", "type": "Polis", "region": "Dodecanese", "lat": 36.4341, "lon": 28.2176, "peak_year": -300, "pop_est": 60000, "gov": "Democracy", "notes": "Colossus of Rhodes, naval power"},
        {"name": "Halicarnassus", "type": "Polis", "region": "Caria", "lat": 37.0383, "lon": 27.4240, "peak_year": -350, "pop_est": 50000, "gov": "Satrapy", "notes": "Mausoleum, Herodotus birthplace"},
        {"name": "Mycenae", "type": "Citadel", "region": "Argolis", "lat": 37.7308, "lon": 22.7564, "peak_year": -1250, "pop_est": 30000, "gov": "Monarchy", "notes": "Agamemnon, Lion Gate, Mycenaean civilization"},
        {"name": "Knossos", "type": "Palace", "region": "Crete", "lat": 35.2979, "lon": 25.1631, "peak_year": -1700, "pop_est": 100000, "gov": "Monarchy", "notes": "Minoan civilization, labyrinth of the Minotaur"},
    ]


def _render_greek_city_states():
    data = _get_greek_data()
    df = pd.DataFrame(data)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("City-States", len(data))
    c2.metric("Peak City", "Athens")
    c3.metric("Oldest", "Argos")
    c4.metric("Civilizations", "Minoan, Mycenaean, Classical")

    m = _base_map([38.0, 24.0], 6)
    for i, r in df.iterrows():
        color = ACCENT_AMBER if r["type"] == "Sanctuary" else _color_for(i)
        radius = 9 if r["name"] in ("Athens", "Sparta") else 6
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>{escape(r['name'])}</b><br>{escape(r['type'])} — {escape(r['region'])}<br>Gov: {escape(r['gov'])}<br>Pop: ~{r['pop_est']:,}<br>Peak: {r['peak_year']} {'BC' if r['peak_year'] < 0 else 'AD'}<br>{escape(r['notes'])}",
        ).add_to(m)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_df = df.sort_values("pop_est", ascending=True)
    colors = [ACCENT_CYAN if n in ("Athens", "Sparta") else ACCENT_VIOLET for n in sorted_df["name"]]
    ax.barh(sorted_df["name"], sorted_df["pop_est"], color=colors)
    ax.set_xlabel("Estimated Population at Peak")
    ax.set_title("Greek City-States — Population Estimates")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df[["name", "type", "region", "gov", "pop_est", "peak_year", "notes"]], width="stretch")
    st.download_button("Download Greek City-States CSV", _df_to_csv(df), "greek_city_states.csv", "text/csv")


# =====================================================================
# 3. EGYPTIAN DYNASTIES
# Nile valley sites from the Early Dynastic Period through the Ptolemaic
# era, plus a dynastic timeline for the Gantt-style chart.
# =====================================================================
@st.cache_data(ttl=3600)
def _get_egyptian_data():
    sites = [
        {"name": "Memphis", "type": "Capital", "dynasty": "Old Kingdom", "lat": 29.8443, "lon": 31.2505, "period": "3100-2181 BC", "notes": "First capital, founded by Menes/Narmer"},
        {"name": "Thebes (Luxor)", "type": "Capital", "dynasty": "New Kingdom", "lat": 25.6872, "lon": 32.6396, "period": "1550-1070 BC", "notes": "Karnak & Luxor temples, Valley of the Kings"},
        {"name": "Alexandria", "type": "Capital", "dynasty": "Ptolemaic", "lat": 31.2001, "lon": 29.9187, "period": "332-30 BC", "notes": "Great Library, Pharos, Cleopatra"},
        {"name": "Akhetaten (Amarna)", "type": "Capital", "dynasty": "18th Dynasty", "lat": 27.6450, "lon": 30.8975, "period": "1346-1332 BC", "notes": "Akhenaten's monotheist capital"},
        {"name": "Tanis", "type": "Capital", "dynasty": "21st Dynasty", "lat": 30.9790, "lon": 31.8780, "period": "1069-945 BC", "notes": "Northern capital during Third Intermediate"},
        {"name": "Pi-Ramesses", "type": "Capital", "dynasty": "19th Dynasty", "lat": 30.7880, "lon": 31.8340, "period": "1279-1213 BC", "notes": "Ramesses II's grand capital in the Delta"},
        {"name": "Giza", "type": "Pyramid Complex", "dynasty": "4th Dynasty", "lat": 29.9792, "lon": 31.1342, "period": "2560-2490 BC", "notes": "Great Pyramid of Khufu, Sphinx"},
        {"name": "Saqqara", "type": "Necropolis", "dynasty": "3rd Dynasty", "lat": 29.8713, "lon": 31.2165, "period": "2670 BC", "notes": "Step Pyramid of Djoser, first stone monument"},
        {"name": "Dashur", "type": "Pyramid Complex", "dynasty": "4th Dynasty", "lat": 29.7908, "lon": 31.2068, "period": "2600 BC", "notes": "Bent Pyramid and Red Pyramid of Sneferu"},
        {"name": "Abu Simbel", "type": "Temple", "dynasty": "19th Dynasty", "lat": 22.3360, "lon": 31.6256, "period": "1264 BC", "notes": "Ramesses II rock temples, relocated 1968"},
        {"name": "Philae", "type": "Temple", "dynasty": "Ptolemaic", "lat": 24.0246, "lon": 32.8841, "period": "380-362 BC", "notes": "Temple of Isis, last hieroglyphic inscription 394 AD"},
        {"name": "Karnak", "type": "Temple Complex", "dynasty": "Multiple", "lat": 25.7189, "lon": 32.6573, "period": "2000-100 BC", "notes": "Largest religious complex ever built"},
        {"name": "Dendera", "type": "Temple", "dynasty": "Ptolemaic", "lat": 26.1417, "lon": 32.6700, "period": "54-20 BC", "notes": "Temple of Hathor, famous zodiac ceiling"},
        {"name": "Edfu", "type": "Temple", "dynasty": "Ptolemaic", "lat": 24.9779, "lon": 32.8734, "period": "237-57 BC", "notes": "Best-preserved temple in Egypt, Temple of Horus"},
        {"name": "Abydos", "type": "Sacred City", "dynasty": "Multiple", "lat": 26.1853, "lon": 31.9190, "period": "3100 BC+", "notes": "Osiris cult center, Temple of Seti I"},
        {"name": "Heliopolis", "type": "Religious Center", "dynasty": "Old Kingdom", "lat": 30.1313, "lon": 31.3084, "period": "2600 BC+", "notes": "Sun worship center, oldest obelisks"},
    ]
    timeline = [
        {"dynasty": "Early Dynastic", "start": -3100, "end": -2686, "capital": "Memphis"},
        {"dynasty": "Old Kingdom", "start": -2686, "end": -2181, "capital": "Memphis"},
        {"dynasty": "1st Intermediate", "start": -2181, "end": -2055, "capital": "Heracleopolis"},
        {"dynasty": "Middle Kingdom", "start": -2055, "end": -1650, "capital": "Thebes"},
        {"dynasty": "2nd Intermediate", "start": -1650, "end": -1550, "capital": "Avaris (Hyksos)"},
        {"dynasty": "New Kingdom", "start": -1550, "end": -1070, "capital": "Thebes"},
        {"dynasty": "3rd Intermediate", "start": -1070, "end": -664, "capital": "Tanis"},
        {"dynasty": "Late Period", "start": -664, "end": -332, "capital": "Sais"},
        {"dynasty": "Ptolemaic", "start": -332, "end": -30, "capital": "Alexandria"},
    ]
    return sites, timeline


def _render_egyptian_dynasties():
    sites, timeline = _get_egyptian_data()
    df = pd.DataFrame(sites)
    df_tl = pd.DataFrame(timeline)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites", len(sites))
    c2.metric("Dynasties", "31")
    c3.metric("Span", "3100 BC - 30 BC")
    c4.metric("Great Pyramids", "3 (Giza)")

    m = _base_map([27.0, 31.0], 6)
    nile = [[31.5, 31.0], [30.8, 31.2], [30.1, 31.3], [29.9, 31.2],
            [28.0, 30.9], [26.2, 32.7], [25.7, 32.6], [24.1, 32.9], [22.3, 31.6]]
    folium.PolyLine(nile, color="#3b82f6", weight=3, opacity=0.6,
                    popup="Nile River").add_to(m)
    for _, r in df.iterrows():
        color = ACCENT_AMBER if "Pyramid" in r["type"] or "Necropolis" in r["type"] else (ACCENT_RED if r["type"] == "Capital" else ACCENT_CYAN)
        icon_char = "\u25b2" if "Pyramid" in r["type"] else "\u2605" if r["type"] == "Capital" else "\u25cf"
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=8 if r["type"] == "Capital" else 6,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>{escape(r['name'])}</b><br>{escape(r['type'])} — {escape(r['dynasty'])}<br>{escape(r['period'])}<br>{escape(r['notes'])}",
        ).add_to(m)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(12, 5))
    colors = [_color_for(i) for i in range(len(df_tl))]
    for i, row in df_tl.iterrows():
        ax.barh(row["dynasty"], row["end"] - row["start"], left=row["start"],
                color=colors[i], edgecolor="#2a3550", linewidth=0.5)
        ax.text(row["start"] + (row["end"] - row["start"]) / 2, i,
                row["capital"], ha="center", va="center", fontsize=7, color=TEXT_PRIMARY)
    ax.set_xlabel("Year (negative = BC)")
    ax.set_title("Egyptian Kingdoms & Periods Timeline")
    ax.invert_yaxis()
    st.image(_fig_to_bytes(fig), use_container_width=True)

    # Site type distribution pie chart
    fig2, ax2 = _dark_fig(figsize=(6, 4))
    type_counts = df["type"].value_counts()
    wedges, texts, autotexts = ax2.pie(
        type_counts.values, labels=type_counts.index,
        colors=[_color_for(i) for i in range(len(type_counts))],
        autopct="%1.0f%%", textprops={"color": TEXT_PRIMARY, "fontsize": 8},
    )
    for at in autotexts:
        at.set_color(TEXT_PRIMARY)
    ax2.set_title("Egyptian Sites by Type")
    st.image(_fig_to_bytes(fig2), use_container_width=True)

    st.subheader("Sites")
    st.dataframe(df[["name", "type", "dynasty", "period", "lat", "lon", "notes"]], width="stretch")
    st.subheader("Dynasty Timeline")
    st.dataframe(df_tl[["dynasty", "start", "end", "capital"]], width="stretch")
    st.download_button("Download Egyptian Sites CSV", _df_to_csv(df), "egyptian_sites.csv", "text/csv")


# =====================================================================
# 4. MONGOL EMPIRE
# =====================================================================
@st.cache_data(ttl=3600)
def _get_mongol_data():
    cities = [
        {"name": "Karakorum", "type": "Capital", "role": "Imperial Capital", "lat": 47.1977, "lon": 102.7800, "year": 1235, "notes": "Founded by Ogedei Khan, capital until 1260"},
        {"name": "Khanbaliq (Beijing)", "type": "Capital", "role": "Yuan Dynasty Capital", "lat": 39.9042, "lon": 116.4074, "year": 1271, "notes": "Kublai Khan's capital, visited by Marco Polo"},
        {"name": "Sarai Batu", "type": "Capital", "role": "Golden Horde Capital", "lat": 48.6208, "lon": 45.2600, "year": 1250, "notes": "Batu Khan, capital on the Volga"},
        {"name": "Tabriz", "type": "Capital", "role": "Ilkhanate Capital", "lat": 38.0800, "lon": 46.2919, "year": 1265, "notes": "Hulagu Khan, center of Ilkhanate"},
        {"name": "Bukhara", "type": "Conquered", "role": "Campaign Target", "lat": 39.7681, "lon": 64.4556, "year": 1220, "notes": "Destroyed by Genghis Khan, Silk Road city"},
        {"name": "Samarkand", "type": "Conquered", "role": "Campaign Target", "lat": 39.6542, "lon": 66.9597, "year": 1220, "notes": "Major Silk Road city, later Timurid capital"},
        {"name": "Merv", "type": "Conquered", "role": "Campaign Target", "lat": 37.6639, "lon": 62.1500, "year": 1221, "notes": "Destroyed, possibly 1M killed"},
        {"name": "Baghdad", "type": "Conquered", "role": "Campaign Target", "lat": 33.3152, "lon": 44.3661, "year": 1258, "notes": "Fall of Abbasid Caliphate, House of Wisdom destroyed"},
        {"name": "Nishapur", "type": "Conquered", "role": "Campaign Target", "lat": 36.2132, "lon": 58.7962, "year": 1221, "notes": "Razed after death of Genghis Khan's son-in-law"},
        {"name": "Urgench", "type": "Conquered", "role": "Campaign Target", "lat": 41.5503, "lon": 60.6317, "year": 1221, "notes": "Khwarezmian capital, destroyed completely"},
        {"name": "Kiev", "type": "Conquered", "role": "Campaign Target", "lat": 50.4501, "lon": 30.5234, "year": 1240, "notes": "Batu Khan's westward campaign, Rus devastated"},
        {"name": "Cracow", "type": "Raided", "role": "Furthest West", "lat": 50.0647, "lon": 19.9450, "year": 1241, "notes": "Battle of Legnica, Europe terrified"},
        {"name": "Hangzhou", "type": "Conquered", "role": "Song Dynasty Capital", "lat": 30.2741, "lon": 120.1551, "year": 1276, "notes": "Fall of Southern Song, Kublai Khan"},
        {"name": "Xiangyang", "type": "Siege", "role": "Key Battle", "lat": 32.0420, "lon": 112.1222, "year": 1273, "notes": "5-year siege, fall opened path to South China"},
        {"name": "Herat", "type": "Conquered", "role": "Campaign Target", "lat": 34.3529, "lon": 62.2041, "year": 1221, "notes": "Destroyed, population massacred, rebuilt by Timurids"},
        {"name": "Tbilisi", "type": "Conquered", "role": "Campaign Target", "lat": 41.7151, "lon": 44.8271, "year": 1236, "notes": "Georgian capital sacked, Caucasus campaign"},
        {"name": "Aleppo", "type": "Conquered", "role": "Campaign Target", "lat": 36.2021, "lon": 37.1343, "year": 1260, "notes": "Sacked by Hulagu, citadel destroyed"},
        {"name": "Moscow", "type": "Conquered", "role": "Campaign Target", "lat": 55.7558, "lon": 37.6173, "year": 1238, "notes": "Burned by Batu Khan, Grand Duchy devastated"},
    ]
    extent = [
        [55.0, 25.0], [60.0, 40.0], [58.0, 65.0], [52.0, 80.0],
        [50.0, 100.0], [52.0, 120.0], [45.0, 130.0], [35.0, 120.0],
        [25.0, 115.0], [20.0, 105.0], [25.0, 95.0], [30.0, 70.0],
        [25.0, 60.0], [30.0, 45.0], [35.0, 35.0], [45.0, 25.0], [55.0, 25.0],
    ]
    return cities, extent


def _render_mongol_empire():
    cities, extent = _get_mongol_data()
    df = pd.DataFrame(cities)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites", len(cities))
    c2.metric("Peak Area", "24M km\u00b2")
    c3.metric("Peak Year", "1279 AD")
    c4.metric("Founded", "1206 by Genghis Khan")

    m = _base_map([42.0, 75.0], 3)
    folium.Polygon(locations=extent, color=ACCENT_RED, fill=True,
                   fill_color=ACCENT_RED, fill_opacity=0.08, weight=1,
                   popup="Mongol Empire max extent ~1279 AD").add_to(m)
    campaign_route = [[47.20, 102.78], [39.77, 64.46], [37.66, 62.15],
                      [36.21, 58.80], [33.32, 44.37], [50.45, 30.52], [50.06, 19.95]]
    folium.PolyLine(campaign_route, color=ACCENT_AMBER, weight=2, dash_array="6 4",
                    popup="Mongol Campaign Routes (simplified)").add_to(m)
    for _, r in df.iterrows():
        color = ACCENT_RED if r["type"] == "Capital" else (ACCENT_AMBER if r["type"] == "Conquered" else ACCENT_VIOLET)
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=8 if r["type"] == "Capital" else 6,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>{escape(r['name'])}</b><br>{escape(r['type'])} — {escape(r['role'])}<br>Year: {r['year']}<br>{escape(r['notes'])}",
        ).add_to(m)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_df = df.sort_values("year")
    colors = [ACCENT_RED if t == "Capital" else ACCENT_AMBER for t in sorted_df["type"]]
    ax.barh(sorted_df["name"], sorted_df["year"], color=colors)
    ax.set_xlabel("Year")
    ax.set_title("Mongol Empire — Cities by Year of Event")
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df[["name", "type", "role", "year", "lat", "lon", "notes"]], width="stretch")
    st.download_button("Download Mongol Empire CSV", _df_to_csv(df), "mongol_empire.csv", "text/csv")


# =====================================================================
# 5. OTTOMAN EMPIRE
# =====================================================================
@st.cache_data(ttl=3600)
def _get_ottoman_data():
    cities = [
        {"name": "Constantinople (Istanbul)", "type": "Capital", "year": 1453, "lat": 41.0082, "lon": 28.9784, "pop_est": 700000, "notes": "Conquered 1453 by Mehmed II, renamed Istanbul"},
        {"name": "Bursa", "type": "Former Capital", "year": 1326, "lat": 40.1828, "lon": 29.0665, "pop_est": 50000, "notes": "First Ottoman capital, tombs of early sultans"},
        {"name": "Edirne", "type": "Former Capital", "year": 1369, "lat": 41.6771, "lon": 26.5557, "pop_est": 80000, "notes": "Selimiye Mosque, capital 1369-1453"},
        {"name": "Cairo", "type": "Major City", "year": 1517, "lat": 30.0444, "lon": 31.2357, "pop_est": 300000, "notes": "Center of Mamluk Sultanate, conquered by Selim I"},
        {"name": "Damascus", "type": "Major City", "year": 1516, "lat": 33.5138, "lon": 36.2765, "pop_est": 100000, "notes": "Umayyad Mosque, ancient trading center"},
        {"name": "Baghdad", "type": "Major City", "year": 1534, "lat": 33.3152, "lon": 44.3661, "pop_est": 100000, "notes": "Conquered by Suleiman the Magnificent"},
        {"name": "Mecca", "type": "Holy City", "year": 1517, "lat": 21.4225, "lon": 39.8262, "pop_est": 40000, "notes": "Holiest city of Islam, under Ottoman protection"},
        {"name": "Medina", "type": "Holy City", "year": 1517, "lat": 24.4672, "lon": 39.6024, "pop_est": 20000, "notes": "Prophet's Mosque, Hejaz Railway terminal"},
        {"name": "Jerusalem", "type": "Holy City", "year": 1517, "lat": 31.7683, "lon": 35.2137, "pop_est": 20000, "notes": "Dome of the Rock restored by Suleiman"},
        {"name": "Athens", "type": "Provincial", "year": 1458, "lat": 37.9838, "lon": 23.7275, "pop_est": 10000, "notes": "Parthenon used as mosque, under Ottoman rule until 1833"},
        {"name": "Belgrade", "type": "Fortress", "year": 1521, "lat": 44.7866, "lon": 20.4489, "pop_est": 40000, "notes": "Key fortress, conquered by Suleiman"},
        {"name": "Budapest", "type": "Provincial", "year": 1541, "lat": 47.4979, "lon": 19.0402, "pop_est": 25000, "notes": "Ottoman Buda, thermal baths built"},
        {"name": "Sarajevo", "type": "Provincial", "year": 1461, "lat": 43.8563, "lon": 18.4131, "pop_est": 30000, "notes": "Bascarsija bazaar, Gazi Husrev-beg Mosque"},
        {"name": "Algiers", "type": "Provincial", "year": 1529, "lat": 36.7538, "lon": 3.0588, "pop_est": 60000, "notes": "Barbary Coast, Hayreddin Barbarossa"},
        {"name": "Tripoli", "type": "Provincial", "year": 1551, "lat": 32.9022, "lon": 13.1800, "pop_est": 20000, "notes": "North African Ottoman province"},
        {"name": "Tunis", "type": "Provincial", "year": 1574, "lat": 36.8065, "lon": 10.1815, "pop_est": 35000, "notes": "Conquered from Hafsids"},
        {"name": "Thessaloniki", "type": "Provincial", "year": 1430, "lat": 40.6401, "lon": 22.9444, "pop_est": 30000, "notes": "Second city of European Ottoman territory"},
        {"name": "Aleppo", "type": "Major City", "year": 1516, "lat": 36.2021, "lon": 37.1343, "pop_est": 90000, "notes": "Major Silk Road trading hub, Great Mosque"},
        {"name": "Basra", "type": "Provincial", "year": 1546, "lat": 30.5085, "lon": 47.7834, "pop_est": 40000, "notes": "Persian Gulf trade port, Shatt al-Arab"},
    ]
    extent = [
        [48.0, 16.0], [47.5, 20.0], [45.0, 21.0], [44.5, 28.0],
        [42.0, 44.0], [38.0, 48.0], [33.0, 48.0], [30.0, 40.0],
        [25.0, 40.0], [15.0, 42.0], [12.0, 44.0], [20.0, 40.0],
        [30.0, 33.0], [32.0, 25.0], [33.0, 12.0], [37.0, 2.0],
        [40.0, -2.0], [42.0, 5.0], [43.0, 16.0], [48.0, 16.0],
    ]
    return cities, extent


def _render_ottoman_empire():
    cities, extent = _get_ottoman_data()
    df = pd.DataFrame(cities)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Major Sites", len(cities))
    c2.metric("Peak Area", "5.2M km\u00b2")
    c3.metric("Duration", "1299 - 1922")
    c4.metric("Peak Sultan", "Suleiman I")

    m = _base_map([36.0, 30.0], 4)
    folium.Polygon(locations=extent, color=ACCENT_EMERALD, fill=True,
                   fill_color=ACCENT_EMERALD, fill_opacity=0.08, weight=1,
                   popup="Ottoman Empire peak extent ~1683").add_to(m)
    for _, r in df.iterrows():
        color = ACCENT_RED if "Capital" in r["type"] else (ACCENT_AMBER if r["type"] == "Holy City" else ACCENT_CYAN)
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=8 if "Capital" in r["type"] else 6,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>{escape(r['name'])}</b><br>{escape(r['type'])}<br>Year: {r['year']}<br>Pop: ~{r['pop_est']:,}<br>{escape(r['notes'])}",
        ).add_to(m)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_df = df.sort_values("year")
    colors = [ACCENT_RED if "Capital" in t else ACCENT_CYAN for t in sorted_df["type"]]
    ax.barh(sorted_df["name"], sorted_df["year"], color=colors)
    ax.set_xlabel("Year of Conquest/Foundation")
    ax.set_title("Ottoman Empire — Expansion Timeline")
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df[["name", "type", "year", "pop_est", "lat", "lon", "notes"]], width="stretch")
    st.download_button("Download Ottoman Empire CSV", _df_to_csv(df), "ottoman_empire.csv", "text/csv")


# =====================================================================
# 6. BRITISH EMPIRE
# =====================================================================
@st.cache_data(ttl=3600)
def _get_british_data():
    colonies = [
        {"name": "London", "type": "Imperial Capital", "region": "Europe", "lat": 51.5074, "lon": -0.1278, "year_acq": 0, "year_lost": 0, "notes": "Heart of the Empire, seat of Parliament"},
        {"name": "Delhi", "type": "Colony Capital", "region": "South Asia", "lat": 28.6139, "lon": 77.2090, "year_acq": 1803, "year_lost": 1947, "notes": "British Raj capital from 1911, Mughal seat"},
        {"name": "Calcutta (Kolkata)", "type": "Colonial Hub", "region": "South Asia", "lat": 22.5726, "lon": 88.3639, "year_acq": 1757, "year_lost": 1947, "notes": "East India Company HQ, Raj capital until 1911"},
        {"name": "Cape Town", "type": "Colony", "region": "Africa", "lat": -33.9249, "lon": 18.4241, "year_acq": 1795, "year_lost": 1910, "notes": "Cape Colony, strategic route to India"},
        {"name": "Sydney", "type": "Colony", "region": "Oceania", "lat": -33.8688, "lon": 151.2093, "year_acq": 1788, "year_lost": 1901, "notes": "First Fleet penal colony, NSW capital"},
        {"name": "Hong Kong", "type": "Colony", "region": "East Asia", "lat": 22.3193, "lon": 114.1694, "year_acq": 1842, "year_lost": 1997, "notes": "Treaty of Nanking, returned to China 1997"},
        {"name": "Singapore", "type": "Colony", "region": "Southeast Asia", "lat": 1.3521, "lon": 103.8198, "year_acq": 1819, "year_lost": 1963, "notes": "Stamford Raffles, strategic Malacca Straits"},
        {"name": "Cairo", "type": "Protectorate", "region": "Africa", "lat": 30.0444, "lon": 31.2357, "year_acq": 1882, "year_lost": 1922, "notes": "Suez Canal control, veiled protectorate"},
        {"name": "Kingston (Jamaica)", "type": "Colony", "region": "Caribbean", "lat": 18.0179, "lon": -76.8099, "year_acq": 1655, "year_lost": 1962, "notes": "Sugar trade, Port Royal pirate haven"},
        {"name": "Ottawa", "type": "Dominion", "region": "North America", "lat": 45.4215, "lon": -75.6972, "year_acq": 1763, "year_lost": 1867, "notes": "Dominion of Canada, Westminster system"},
        {"name": "Wellington", "type": "Dominion", "region": "Oceania", "lat": -41.2865, "lon": 174.7762, "year_acq": 1840, "year_lost": 1907, "notes": "Treaty of Waitangi, NZ dominion"},
        {"name": "Nairobi", "type": "Colony", "region": "Africa", "lat": -1.2921, "lon": 36.8219, "year_acq": 1895, "year_lost": 1963, "notes": "British East Africa, railway hub"},
        {"name": "Gibraltar", "type": "Colony", "region": "Europe", "lat": 36.1408, "lon": -5.3536, "year_acq": 1713, "year_lost": 0, "notes": "Treaty of Utrecht, still British territory"},
        {"name": "Aden", "type": "Colony", "region": "Middle East", "lat": 12.8000, "lon": 45.0345, "year_acq": 1839, "year_lost": 1967, "notes": "Strategic Red Sea coaling station"},
        {"name": "Malta", "type": "Colony", "region": "Europe", "lat": 35.8997, "lon": 14.5146, "year_acq": 1800, "year_lost": 1964, "notes": "Mediterranean naval base, WWII siege"},
    ]
    battles = [
        {"name": "Battle of Plassey", "year": 1757, "lat": 23.8022, "lon": 88.2643, "result": "Victory", "notes": "Clive defeats Siraj ud-Daulah, Bengal conquered"},
        {"name": "Battle of Trafalgar", "year": 1805, "lat": 36.1833, "lon": -6.2333, "result": "Victory", "notes": "Nelson defeats Franco-Spanish fleet"},
        {"name": "Battle of Isandlwana", "year": 1879, "lat": -28.3535, "lon": 30.6536, "result": "Defeat", "notes": "Zulu victory over British in South Africa"},
        {"name": "Battle of Rorke's Drift", "year": 1879, "lat": -28.3492, "lon": 30.5344, "result": "Victory", "notes": "Legendary defense, 11 Victoria Crosses"},
        {"name": "Siege of Khartoum", "year": 1885, "lat": 15.5007, "lon": 32.5599, "result": "Defeat", "notes": "Gordon killed, Mahdist revolt"},
        {"name": "Battle of Omdurman", "year": 1898, "lat": 15.6161, "lon": 32.4783, "result": "Victory", "notes": "Kitchener avenges Gordon, Mahdist state crushed"},
        {"name": "Siege of Lucknow", "year": 1857, "lat": 26.8467, "lon": 80.9462, "result": "Victory", "notes": "Indian Rebellion of 1857, British relief force"},
        {"name": "Battle of Quebec", "year": 1759, "lat": 46.8032, "lon": -71.2154, "result": "Victory", "notes": "Wolfe defeats Montcalm, Britain takes New France"},
    ]
    return colonies, battles


def _render_british_empire():
    colonies, battles = _get_british_data()
    df_col = pd.DataFrame(colonies)
    df_bat = pd.DataFrame(battles)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Territories", len(colonies))
    c2.metric("Peak Area", "35.5M km\u00b2")
    c3.metric("Peak Pop.", "~530M (1938)")
    c4.metric("Key Battles", len(battles))

    m = _base_map([20, 20], 2)
    for _, r in df_col.iterrows():
        color = ACCENT_RED if r["type"] == "Imperial Capital" else ACCENT_CYAN
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=7,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>{escape(r['name'])}</b><br>{escape(r['type'])} — {escape(r['region'])}<br>Acquired: {r['year_acq'] if r['year_acq'] else 'N/A'}<br>{escape(r['notes'])}",
        ).add_to(m)
    for _, r in df_bat.iterrows():
        color = ACCENT_EMERALD if r["result"] == "Victory" else ACCENT_RED
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=8,
            color=color, fill=True, fill_color=color, fill_opacity=0.9,
            popup=f"<b>\u2694 {escape(r['name'])}</b><br>Year: {r['year']}<br>Result: {escape(r['result'])}<br>{escape(r['notes'])}",
        ).add_to(m)
    trade_routes = [
        [[51.5, -0.1], [36.1, -5.4], [30.0, 31.2], [12.8, 45.0], [22.6, 88.4]],
        [[51.5, -0.1], [36.1, -5.4], [-33.9, 18.4], [-1.3, 36.8]],
        [[51.5, -0.1], [18.0, -76.8], [45.4, -75.7]],
    ]
    for route in trade_routes:
        folium.PolyLine(route, color=ACCENT_AMBER, weight=2, dash_array="6 4",
                        opacity=0.5).add_to(m)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(10, 5))
    valid = df_col[df_col["year_acq"] > 0].sort_values("year_acq")
    ax.barh(valid["name"], valid["year_acq"], color=ACCENT_CYAN)
    ax.set_xlabel("Year Acquired")
    ax.set_title("British Empire — Territorial Acquisitions")
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df_col[["name", "type", "region", "year_acq", "year_lost", "notes"]], width="stretch")
    st.download_button("Download British Empire CSV", _df_to_csv(df_col), "british_empire.csv", "text/csv")


# =====================================================================
# 7. CHINESE DYNASTIES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_chinese_data():
    capitals = [
        {"name": "Xi'an (Chang'an)", "dynasty": "Han / Tang", "lat": 34.2658, "lon": 108.9541, "period": "202 BC - 907 AD", "pop_est": 1000000, "notes": "Silk Road terminus, Tang golden age, terracotta warriors nearby"},
        {"name": "Luoyang", "dynasty": "Eastern Han / Tang", "lat": 34.6197, "lon": 112.4540, "period": "25 - 220 AD", "pop_est": 500000, "notes": "Second capital, Longmen Grottoes, White Horse Temple"},
        {"name": "Nanjing", "dynasty": "Ming (early)", "lat": 32.0603, "lon": 118.7969, "period": "1368 - 1421", "pop_est": 470000, "notes": "Ming Xiaoling Mausoleum, city walls"},
        {"name": "Beijing", "dynasty": "Ming / Qing", "lat": 39.9042, "lon": 116.4074, "period": "1421 - 1912", "pop_est": 1100000, "notes": "Forbidden City, Temple of Heaven, Summer Palace"},
        {"name": "Kaifeng", "dynasty": "Song (Northern)", "lat": 34.7972, "lon": 114.3076, "period": "960 - 1127", "pop_est": 600000, "notes": "Largest city in world c.1100, Iron Pagoda"},
        {"name": "Hangzhou", "dynasty": "Song (Southern)", "lat": 30.2741, "lon": 120.1551, "period": "1127 - 1276", "pop_est": 1000000, "notes": "Marco Polo's finest city in the world, West Lake"},
        {"name": "Anyang", "dynasty": "Shang", "lat": 36.1000, "lon": 114.3500, "period": "1300 - 1046 BC", "pop_est": 100000, "notes": "Oracle bones discovered, earliest Chinese writing"},
        {"name": "Xianyang", "dynasty": "Qin", "lat": 34.3290, "lon": 108.7143, "period": "221 - 206 BC", "pop_est": 300000, "notes": "Qin Shi Huang's capital, first unified empire"},
        {"name": "Chengdu", "dynasty": "Shu Han", "lat": 30.5728, "lon": 104.0668, "period": "221 - 263 AD", "pop_est": 200000, "notes": "Zhuge Liang, Three Kingdoms period"},
        {"name": "Lhasa", "dynasty": "Qing (Tibet)", "lat": 29.6500, "lon": 91.1000, "period": "1720 - 1912", "pop_est": 25000, "notes": "Potala Palace, Qing protectorate"},
        {"name": "Guangzhou (Canton)", "dynasty": "Multiple", "lat": 23.1291, "lon": 113.2644, "period": "214 BC+", "notes": "Southern trade port, Canton System, Opium Wars gateway", "pop_est": 200000},
        {"name": "Zhengzhou", "dynasty": "Shang (early)", "lat": 34.7466, "lon": 113.6253, "period": "1600 BC", "pop_est": 80000, "notes": "Early Shang capital, ancient walled city remains"},
        {"name": "Dunhuang", "dynasty": "Multiple", "lat": 40.1421, "lon": 94.6619, "period": "111 BC+", "pop_est": 15000, "notes": "Mogao Caves, Silk Road oasis, 1000 Buddhas"},
    ]
    great_wall = [
        [40.35, 98.22], [40.63, 100.10], [40.72, 103.00], [40.80, 106.50],
        [40.65, 109.80], [40.50, 111.70], [40.85, 114.00], [40.42, 116.57],
        [40.43, 117.23], [40.68, 119.80], [40.03, 121.00],
    ]
    return capitals, great_wall


def _render_chinese_dynasties():
    capitals, great_wall = _get_chinese_data()
    df = pd.DataFrame(capitals)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Capitals", len(capitals))
    c2.metric("Dynasties", "Han, Tang, Song, Ming, Qing")
    c3.metric("Span", "1600 BC - 1912 AD")
    c4.metric("Great Wall", "~21,196 km")

    m = _base_map([35.0, 110.0], 4)
    folium.PolyLine(great_wall, color=ACCENT_AMBER, weight=4,
                    popup="Great Wall of China (simplified route)").add_to(m)
    for i, r in df.iterrows():
        color = ACCENT_RED if r["dynasty"] in ("Ming / Qing", "Han / Tang") else _color_for(i)
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=8,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>{escape(r['name'])}</b><br>Dynasty: {escape(r['dynasty'])}<br>{escape(r['period'])}<br>Pop: ~{r['pop_est']:,}<br>{escape(r['notes'])}",
        ).add_to(m)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_df = df.sort_values("pop_est", ascending=True)
    ax.barh(sorted_df["name"], sorted_df["pop_est"],
            color=[_color_for(i) for i in range(len(sorted_df))])
    ax.set_xlabel("Estimated Population at Peak")
    ax.set_title("Chinese Dynastic Capitals — Population")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df[["name", "dynasty", "period", "pop_est", "lat", "lon", "notes"]], width="stretch")
    st.download_button("Download Chinese Dynasties CSV", _df_to_csv(df), "chinese_dynasties.csv", "text/csv")


# =====================================================================
# 8. PERSIAN EMPIRE
# =====================================================================
@st.cache_data(ttl=3600)
def _get_persian_data():
    cities = [
        {"name": "Persepolis", "type": "Ceremonial Capital", "empire": "Achaemenid", "lat": 29.9352, "lon": 52.8914, "year": -515, "notes": "Built by Darius I, burned by Alexander 330 BC"},
        {"name": "Susa", "type": "Administrative Capital", "empire": "Achaemenid", "lat": 32.1877, "lon": 48.2462, "year": -4000, "notes": "One of oldest cities, Apadana palace"},
        {"name": "Pasargadae", "type": "Capital", "empire": "Achaemenid", "lat": 30.1938, "lon": 53.1674, "year": -546, "notes": "Cyrus the Great's capital, his tomb survives"},
        {"name": "Ecbatana (Hamadan)", "type": "Summer Capital", "empire": "Median / Achaemenid", "lat": 34.7988, "lon": 48.5146, "year": -678, "notes": "Median capital, summer retreat of Persian kings"},
        {"name": "Babylon", "type": "Conquered Capital", "empire": "Achaemenid", "lat": 32.5427, "lon": 44.4209, "year": -539, "notes": "Cyrus conquered 539 BC, Ishtar Gate"},
        {"name": "Ctesiphon", "type": "Capital", "empire": "Sassanid", "lat": 33.0917, "lon": 44.5813, "year": 226, "notes": "Taq Kasra arch, Sassanid seat of power"},
        {"name": "Isfahan", "type": "Capital", "empire": "Safavid", "lat": 32.6546, "lon": 51.6680, "year": 1598, "notes": "Half the World, Naqsh-e Jahan Square"},
        {"name": "Shiraz", "type": "Capital", "empire": "Zand", "lat": 29.5918, "lon": 52.5837, "year": 1750, "notes": "City of poets (Hafez, Saadi), gardens"},
        {"name": "Tabriz", "type": "Capital", "empire": "Safavid (early)", "lat": 38.0800, "lon": 46.2919, "year": 1501, "notes": "First Safavid capital, Grand Bazaar"},
        {"name": "Tehran", "type": "Capital", "empire": "Qajar / Pahlavi", "lat": 35.6892, "lon": 51.3890, "year": 1786, "notes": "Modern capital from Qajar dynasty"},
        {"name": "Sardis", "type": "Satrap Seat", "empire": "Achaemenid", "lat": 38.4893, "lon": 28.0361, "year": -547, "notes": "Former Lydian capital, Royal Road terminus"},
        {"name": "Naqsh-e Rostam", "type": "Necropolis", "empire": "Achaemenid", "lat": 29.9877, "lon": 52.8740, "year": -500, "notes": "Royal tombs of Darius I, Xerxes, Artaxerxes"},
        {"name": "Bishapur", "type": "City", "empire": "Sassanid", "lat": 29.7840, "lon": 51.5730, "year": 266, "notes": "Shapur I's victory city, Roman prisoner labor"},
        {"name": "Firuzabad", "type": "Capital", "empire": "Sassanid (early)", "lat": 28.8423, "lon": 52.5261, "year": 224, "notes": "Ardashir I's circular city, Palace of Ardashir"},
        {"name": "Hatra", "type": "Fortress City", "empire": "Parthian", "lat": 35.5877, "lon": 42.7183, "year": -100, "notes": "Resisted Roman sieges, circular walled city, UNESCO site"},
    ]
    royal_road = [
        [38.49, 28.04], [37.95, 32.85], [37.00, 36.00], [35.69, 41.00],
        [34.80, 48.51], [33.32, 44.42], [32.19, 48.25], [29.94, 52.89],
    ]
    return cities, royal_road


def _render_persian_empire():
    cities, royal_road = _get_persian_data()
    df = pd.DataFrame(cities)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites", len(cities))
    c2.metric("Peak Area", "5.5M km\u00b2")
    c3.metric("Founded", "550 BC by Cyrus")
    c4.metric("Empires", "Achaemenid, Sassanid, Safavid")

    m = _base_map([33.0, 48.0], 5)
    folium.PolyLine(royal_road, color=ACCENT_AMBER, weight=3, dash_array="8 4",
                    popup="Royal Road — Sardis to Persepolis (~2,700 km)").add_to(m)
    achaemenid_extent = [
        [42.0, 26.0], [40.0, 32.0], [38.0, 44.0], [37.0, 50.0],
        [38.0, 60.0], [37.0, 68.0], [33.0, 72.0], [25.0, 68.0],
        [24.0, 58.0], [25.0, 44.0], [30.0, 33.0], [32.0, 30.0],
        [37.0, 26.0], [42.0, 26.0],
    ]
    folium.Polygon(locations=achaemenid_extent, color=ACCENT_VIOLET, fill=True,
                   fill_color=ACCENT_VIOLET, fill_opacity=0.07, weight=1,
                   popup="Achaemenid Empire max extent ~500 BC").add_to(m)
    for _, r in df.iterrows():
        is_cap = "Capital" in r["type"]
        color = ACCENT_RED if is_cap else ACCENT_CYAN
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=8 if is_cap else 6,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>{escape(r['name'])}</b><br>{escape(r['type'])} — {escape(r['empire'])}<br>Year: {r['year']} {'BC' if r['year'] < 0 else 'AD'}<br>{escape(r['notes'])}",
        ).add_to(m)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_df = df.sort_values("year")
    colors = [ACCENT_VIOLET if "Achaemenid" in e else ACCENT_CYAN for e in sorted_df["empire"]]
    ax.barh(sorted_df["name"], sorted_df["year"], color=colors)
    ax.set_xlabel("Year (negative = BC)")
    ax.set_title("Persian Sites — Chronological Order")
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df[["name", "type", "empire", "year", "lat", "lon", "notes"]], width="stretch")
    st.download_button("Download Persian Empire CSV", _df_to_csv(df), "persian_empire.csv", "text/csv")


# =====================================================================
# 9. FAMOUS BATTLES
# Curated list of 30+ decisive battles spanning 2,500 years of warfare,
# from Marathon (490 BC) to the Siege of Leningrad (1944). Includes
# combatants, approximate casualties, and geographic coordinates.
# =====================================================================
@st.cache_data(ttl=3600)
def _get_battles_data():
    return [
        {"name": "Battle of Marathon", "year": -490, "lat": 38.1553, "lon": 23.9642, "combatants": "Athens vs Persia", "result": "Greek victory", "casualties": "~7,000", "notes": "Pheidippides ran to Athens, origin of marathon race"},
        {"name": "Battle of Thermopylae", "year": -480, "lat": 38.7963, "lon": 22.5347, "combatants": "Sparta/Greece vs Persia", "result": "Persian victory", "casualties": "~21,000", "notes": "300 Spartans under Leonidas, legendary last stand"},
        {"name": "Battle of Salamis", "year": -480, "lat": 37.9523, "lon": 23.5988, "combatants": "Greece vs Persia", "result": "Greek victory", "casualties": "~40,000", "notes": "Themistocles naval victory, turning point of Persian Wars"},
        {"name": "Battle of Gaugamela", "year": -331, "lat": 36.5600, "lon": 43.4300, "combatants": "Macedonia vs Persia", "result": "Macedonian victory", "casualties": "~53,000", "notes": "Alexander the Great defeats Darius III, end of Achaemenid Empire"},
        {"name": "Battle of Cannae", "year": -216, "lat": 41.3000, "lon": 16.0833, "combatants": "Carthage vs Rome", "result": "Carthaginian victory", "casualties": "~70,000", "notes": "Hannibal's double envelopment, worst Roman defeat"},
        {"name": "Battle of Zama", "year": -202, "lat": 36.2333, "lon": 8.3167, "combatants": "Rome vs Carthage", "result": "Roman victory", "casualties": "~25,000", "notes": "Scipio Africanus defeats Hannibal, ends Second Punic War"},
        {"name": "Battle of Actium", "year": -31, "lat": 38.9500, "lon": 20.7178, "combatants": "Octavian vs Antony/Cleopatra", "result": "Octavian victory", "casualties": "~7,000", "notes": "Birth of the Roman Empire"},
        {"name": "Battle of Teutoburg Forest", "year": 9, "lat": 52.4050, "lon": 8.1300, "combatants": "Germania vs Rome", "result": "Germanic victory", "casualties": "~20,000", "notes": "Arminius destroys 3 legions, Rome abandons Germania"},
        {"name": "Battle of Adrianople", "year": 378, "lat": 41.6771, "lon": 26.5557, "combatants": "Goths vs Rome", "result": "Gothic victory", "casualties": "~20,000", "notes": "Emperor Valens killed, beginning of the end for Rome"},
        {"name": "Battle of Tours", "year": 732, "lat": 46.9167, "lon": 0.8167, "combatants": "Franks vs Umayyad Caliphate", "result": "Frankish victory", "casualties": "~12,000", "notes": "Charles Martel halts Muslim expansion into Europe"},
        {"name": "Battle of Hastings", "year": 1066, "lat": 50.9141, "lon": 0.4878, "combatants": "Normandy vs England", "result": "Norman victory", "casualties": "~10,000", "notes": "William the Conqueror defeats Harold II, reshapes England"},
        {"name": "Battle of Hattin", "year": 1187, "lat": 32.8058, "lon": 35.4750, "combatants": "Saladin vs Crusaders", "result": "Muslim victory", "casualties": "~20,000", "notes": "Saladin captures Jerusalem, triggers Third Crusade"},
        {"name": "Battle of Ain Jalut", "year": 1260, "lat": 32.5500, "lon": 35.4000, "combatants": "Mamluks vs Mongols", "result": "Mamluk victory", "casualties": "~2,000", "notes": "First major Mongol defeat, saves Egypt"},
        {"name": "Battle of Agincourt", "year": 1415, "lat": 50.4600, "lon": 2.1400, "combatants": "England vs France", "result": "English victory", "casualties": "~10,000", "notes": "Henry V's longbow victory, immortalized by Shakespeare"},
        {"name": "Fall of Constantinople", "year": 1453, "lat": 41.0082, "lon": 28.9784, "combatants": "Ottoman vs Byzantium", "result": "Ottoman victory", "casualties": "~8,000", "notes": "Mehmed II ends Roman/Byzantine Empire, dawn of Ottoman era"},
        {"name": "Battle of Lepanto", "year": 1571, "lat": 38.3667, "lon": 21.1500, "combatants": "Holy League vs Ottoman", "result": "Holy League victory", "casualties": "~47,000", "notes": "Last great galley battle, halts Ottoman Mediterranean advance"},
        {"name": "Battle of Vienna", "year": 1683, "lat": 48.2082, "lon": 16.3738, "combatants": "Habsburg/Polish vs Ottoman", "result": "Habsburg victory", "casualties": "~30,000", "notes": "Jan Sobieski's charge, Ottoman high-water mark in Europe"},
        {"name": "Battle of Blenheim", "year": 1704, "lat": 48.6269, "lon": 10.5978, "combatants": "England/Austria vs France/Bavaria", "result": "Allied victory", "casualties": "~33,000", "notes": "Duke of Marlborough, War of Spanish Succession"},
        {"name": "Battle of Trafalgar", "year": 1805, "lat": 36.1833, "lon": -6.2333, "combatants": "Britain vs France/Spain", "result": "British victory", "casualties": "~7,000", "notes": "Nelson's death, established British naval supremacy"},
        {"name": "Battle of Austerlitz", "year": 1805, "lat": 49.1378, "lon": 16.7628, "combatants": "France vs Austria/Russia", "result": "French victory", "casualties": "~35,000", "notes": "Napoleon's masterpiece, Battle of the Three Emperors"},
        {"name": "Battle of Waterloo", "year": 1815, "lat": 50.6803, "lon": 4.4122, "combatants": "Britain/Prussia vs France", "result": "Coalition victory", "casualties": "~48,000", "notes": "Napoleon's final defeat, Wellington and Blucher"},
        {"name": "Battle of Gettysburg", "year": 1863, "lat": 39.8109, "lon": -77.2261, "combatants": "Union vs Confederacy", "result": "Union victory", "casualties": "~51,000", "notes": "Turning point of American Civil War, Pickett's Charge"},
        {"name": "Battle of Tsushima", "year": 1905, "lat": 34.0833, "lon": 129.5000, "combatants": "Japan vs Russia", "result": "Japanese victory", "casualties": "~10,000", "notes": "Japanese naval dominance, end of Russo-Japanese War"},
        {"name": "Battle of the Somme", "year": 1916, "lat": 50.0100, "lon": 2.7000, "combatants": "Britain/France vs Germany", "result": "Inconclusive", "casualties": "~1,100,000", "notes": "First day: 57,470 British casualties, WWI horror"},
        {"name": "Battle of Verdun", "year": 1916, "lat": 49.1608, "lon": 5.3886, "combatants": "France vs Germany", "result": "French defense", "casualties": "~700,000", "notes": "Ils ne passeront pas, 10-month battle of attrition"},
        {"name": "Battle of Stalingrad", "year": 1943, "lat": 48.7080, "lon": 44.5133, "combatants": "USSR vs Nazi Germany", "result": "Soviet victory", "casualties": "~2,000,000", "notes": "Bloodiest battle in history, turning point of WWII"},
        {"name": "D-Day (Normandy)", "year": 1944, "lat": 49.3700, "lon": -0.8700, "combatants": "Allies vs Nazi Germany", "result": "Allied victory", "casualties": "~12,000", "notes": "Largest seaborne invasion, liberation of France begins"},
        {"name": "Battle of Midway", "year": 1942, "lat": 28.2000, "lon": -177.3500, "combatants": "USA vs Japan", "result": "American victory", "casualties": "~3,500", "notes": "Turning point in Pacific, 4 Japanese carriers sunk"},
        {"name": "Battle of Kursk", "year": 1943, "lat": 51.7166, "lon": 36.1543, "combatants": "USSR vs Nazi Germany", "result": "Soviet victory", "casualties": "~700,000", "notes": "Largest tank battle ever, 6,000+ tanks engaged"},
        {"name": "Battle of the Bulge", "year": 1944, "lat": 50.2860, "lon": 5.7940, "combatants": "Allies vs Nazi Germany", "result": "Allied victory", "casualties": "~186,000", "notes": "Last major German offensive, Bastogne siege"},
        {"name": "Siege of Leningrad", "year": 1944, "lat": 59.9343, "lon": 30.3351, "combatants": "USSR vs Nazi Germany", "result": "Soviet defense", "casualties": "~1,500,000", "notes": "872-day siege, deadliest in history"},
    ]


def _render_famous_battles():
    data = _get_battles_data()
    df = pd.DataFrame(data)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Battles", len(data))
    c2.metric("Timespan", "490 BC - 1944 AD")
    c3.metric("Bloodiest", "Stalingrad")
    c4.metric("Earliest", "Marathon (490 BC)")

    m = _base_map([35, 15], 2)
    cluster = MarkerCluster(name="Battles").add_to(m)
    for _, r in df.iterrows():
        color = ACCENT_EMERALD if "victory" in r["result"].lower() and ("Greek" in r["combatants"].split(" vs ")[0] or "Allied" in r["combatants"] or "Union" in r["combatants"] or "Soviet" in r["combatants"] or "British" in r["combatants"] or "American" in r["combatants"]) else ACCENT_RED
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=7,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>\u2694 {escape(r['name'])}</b><br>Year: {r['year']} {'BC' if r['year'] < 0 else 'AD'}<br>{escape(r['combatants'])}<br>Result: {escape(r['result'])}<br>Casualties: {escape(str(r['casualties']))}<br>{escape(r['notes'])}",
        ).add_to(cluster)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(12, 8))
    sorted_df = df.sort_values("year")
    colors = [_color_for(i) for i in range(len(sorted_df))]
    ax.barh(sorted_df["name"], sorted_df["year"], color=colors)
    ax.set_xlabel("Year (negative = BC)")
    ax.set_title("Famous Battles — Chronological Timeline")
    ax.tick_params(axis="y", labelsize=7)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df[["name", "year", "combatants", "result", "casualties", "notes"]], width="stretch")
    st.download_button("Download Famous Battles CSV", _df_to_csv(df), "famous_battles.csv", "text/csv")


# =====================================================================
# 10. FALLEN CAPITALS
# Curated list of 28 cities that were once seats of power but fell to
# conquest, environmental change, or internal collapse. Spans every
# inhabited continent and over 4,000 years of history.
# =====================================================================
@st.cache_data(ttl=3600)
def _get_fallen_capitals():
    return [
        {"name": "Constantinople", "empire": "Byzantine Empire", "lat": 41.0082, "lon": 28.9784, "fell": 1453, "cause": "Ottoman conquest", "modern": "Istanbul, Turkey", "notes": "1,100 years as capital, fell to Mehmed II"},
        {"name": "Carthage", "empire": "Carthaginian Republic", "lat": 36.8528, "lon": 10.3234, "fell": -146, "cause": "Roman destruction", "modern": "Tunis suburb, Tunisia", "notes": "Delenda est Carthago, salt legend, later rebuilt by Rome"},
        {"name": "Tenochtitlan", "empire": "Aztec Empire", "lat": 19.4326, "lon": -99.1332, "fell": 1521, "cause": "Spanish conquest", "modern": "Mexico City, Mexico", "notes": "Cortes siege, smallpox, built on lake island, pop ~200,000"},
        {"name": "Angkor", "empire": "Khmer Empire", "lat": 13.4125, "lon": 103.8670, "fell": 1431, "cause": "Thai invasion / decline", "modern": "Siem Reap, Cambodia", "notes": "Largest pre-industrial city, Angkor Wat temple complex"},
        {"name": "Babylon", "empire": "Neo-Babylonian Empire", "lat": 32.5427, "lon": 44.4209, "fell": -539, "cause": "Persian conquest", "modern": "Hillah, Iraq", "notes": "Cyrus the Great, Hanging Gardens, Ishtar Gate"},
        {"name": "Persepolis", "empire": "Achaemenid Empire", "lat": 29.9352, "lon": 52.8914, "fell": -330, "cause": "Alexander the Great", "modern": "Ruins near Shiraz, Iran", "notes": "Burned in revenge for Xerxes' sack of Athens"},
        {"name": "Troy", "empire": "Kingdom of Troy", "lat": 39.9578, "lon": 26.2389, "fell": -1180, "cause": "Greek siege", "modern": "Hisarlik, Turkey", "notes": "Trojan War, wooden horse, Homer's Iliad"},
        {"name": "Memphis", "empire": "Ancient Egypt", "lat": 29.8443, "lon": 31.2505, "fell": -332, "cause": "Alexander's conquest", "modern": "Mit Rahina, Egypt", "notes": "3,000 years as Egyptian capital, eclipsed by Alexandria"},
        {"name": "Nineveh", "empire": "Assyrian Empire", "lat": 36.3600, "lon": 43.1500, "fell": -612, "cause": "Babylonian/Median alliance", "modern": "Mosul, Iraq", "notes": "Largest city in world ~700 BC, library of Ashurbanipal"},
        {"name": "Teotihuacan", "empire": "Teotihuacan Civilization", "lat": 19.6925, "lon": -98.8438, "fell": 550, "cause": "Internal revolt / fire", "modern": "NE of Mexico City, Mexico", "notes": "Pyramid of the Sun, pop ~125,000, mysterious collapse"},
        {"name": "Rome", "empire": "Western Roman Empire", "lat": 41.9028, "lon": 12.4964, "fell": 476, "cause": "Germanic deposition", "modern": "Rome, Italy", "notes": "Romulus Augustulus deposed by Odoacer"},
        {"name": "Ctesiphon", "empire": "Sassanid Empire", "lat": 33.0917, "lon": 44.5813, "fell": 637, "cause": "Arab conquest", "modern": "Salman Pak, Iraq", "notes": "Taq Kasra arch survives, fell to Rashidun Caliphate"},
        {"name": "Vijayanagara", "empire": "Vijayanagara Empire", "lat": 15.3350, "lon": 76.4600, "fell": 1565, "cause": "Deccan Sultanates", "modern": "Hampi, India", "notes": "Battle of Talikota, city looted for months"},
        {"name": "Cusco", "empire": "Inca Empire", "lat": -13.5319, "lon": -71.9675, "fell": 1533, "cause": "Spanish conquest", "modern": "Cusco, Peru", "notes": "Pizarro captures Atahualpa, Sacsayhuaman fortress"},
        {"name": "Chan Chan", "empire": "Chimu Kingdom", "lat": -8.1067, "lon": -79.0744, "fell": 1470, "cause": "Inca conquest", "modern": "Trujillo, Peru", "notes": "Largest adobe city ever built, UNESCO site"},
        {"name": "Great Zimbabwe", "empire": "Kingdom of Zimbabwe", "lat": -20.2712, "lon": 30.9336, "fell": 1450, "cause": "Environmental decline", "modern": "Masvingo, Zimbabwe", "notes": "Largest stone structures in sub-Saharan Africa"},
        {"name": "Palmyra", "empire": "Palmyrene Empire", "lat": 34.5514, "lon": 38.2689, "fell": 273, "cause": "Roman reconquest", "modern": "Tadmur, Syria", "notes": "Queen Zenobia, destroyed by Aurelian"},
        {"name": "Mohenjo-daro", "empire": "Indus Valley Civilization", "lat": 27.3244, "lon": 68.1382, "fell": -1900, "cause": "Climate change / floods", "modern": "Sindh, Pakistan", "notes": "Great Bath, advanced urban planning, script undeciphered"},
        {"name": "Kaifeng", "empire": "Northern Song Dynasty", "lat": 34.7972, "lon": 114.3076, "fell": 1127, "cause": "Jurchen conquest", "modern": "Kaifeng, China", "notes": "Largest city in world ~1100, flooded repeatedly by Yellow River"},
        {"name": "Samarkand", "empire": "Timurid Empire", "lat": 39.6542, "lon": 66.9597, "fell": 1500, "cause": "Uzbek conquest", "modern": "Samarkand, Uzbekistan", "notes": "Timur's capital, Registan Square, Silk Road jewel"},
        {"name": "Uxmal", "empire": "Maya City-State", "lat": 20.3597, "lon": -89.7700, "fell": 1000, "cause": "Drought / collapse", "modern": "Yucatan, Mexico", "notes": "Puuc-style architecture, Pyramid of the Magician"},
        {"name": "Hattusa", "empire": "Hittite Empire", "lat": 40.0187, "lon": 34.6148, "fell": -1178, "cause": "Bronze Age collapse", "modern": "Bogazkoy, Turkey", "notes": "Lion Gate, cuneiform archives, Sea Peoples era"},
        {"name": "Tikal", "empire": "Maya City-State", "lat": 17.2220, "lon": -89.6237, "fell": 900, "cause": "Classic Maya collapse", "modern": "Peten, Guatemala", "notes": "Temple IV tallest pre-Columbian structure, pop ~100,000"},
        {"name": "Mycenae", "empire": "Mycenaean Greece", "lat": 37.7308, "lon": 22.7564, "fell": -1100, "cause": "Bronze Age collapse", "modern": "Argolis, Greece", "notes": "Agamemnon's citadel, Lion Gate, shaft graves of gold"},
        {"name": "Aksum", "empire": "Aksumite Empire", "lat": 14.1211, "lon": 38.7195, "fell": 960, "cause": "Queen Gudit / Islamic expansion", "modern": "Axum, Ethiopia", "notes": "Stelae field, claimed Ark of the Covenant, obelisks"},
        {"name": "Merv", "empire": "Seljuk Empire", "lat": 37.6639, "lon": 62.1500, "fell": 1221, "cause": "Mongol destruction", "modern": "Mary, Turkmenistan", "notes": "Silk Road oasis, possibly 1M killed by Mongols"},
        {"name": "Tiwanaku", "empire": "Tiwanaku State", "lat": -16.5525, "lon": -68.6736, "fell": 1000, "cause": "Drought / collapse", "modern": "La Paz region, Bolivia", "notes": "Gateway of the Sun, pre-Inca civilization near Lake Titicaca"},
        {"name": "Ur", "empire": "Third Dynasty of Ur", "lat": 30.9625, "lon": 46.1033, "fell": -2004, "cause": "Elamite invasion", "modern": "Nasiriyah, Iraq", "notes": "Ziggurat of Ur, birthplace of Abraham tradition"},
    ]


def _render_fallen_capitals():
    data = _get_fallen_capitals()
    df = pd.DataFrame(data)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fallen Capitals", len(data))
    c2.metric("Earliest", "Ur (~2004 BC)")
    c3.metric("Latest", "Tenochtitlan (1521)")
    c4.metric("Continents", "6")

    m = _base_map([20, 20], 2)
    cluster = MarkerCluster(name="Fallen Capitals").add_to(m)
    for i, r in df.iterrows():
        color = _color_for(i)
        folium.CircleMarker(
            [r["lat"], r["lon"]], radius=7,
            color=color, fill=True, fill_color=color, fill_opacity=0.8,
            popup=f"<b>\U0001F3db {escape(r['name'])}</b><br>Empire: {escape(r['empire'])}<br>Fell: {r['fell']} {'BC' if r['fell'] < 0 else 'AD'}<br>Cause: {escape(r['cause'])}<br>Modern: {escape(r['modern'])}<br>{escape(r['notes'])}",
        ).add_to(cluster)
    _show_map(m)

    fig, ax = _dark_fig(figsize=(12, 8))
    sorted_df = df.sort_values("fell")
    colors = [_color_for(i) for i in range(len(sorted_df))]
    ax.barh(sorted_df["name"], sorted_df["fell"], color=colors)
    ax.set_xlabel("Year of Fall (negative = BC)")
    ax.set_title("Fallen Capitals — Chronological Order")
    ax.tick_params(axis="y", labelsize=7)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df[["name", "empire", "fell", "cause", "modern", "notes"]], width="stretch")
    st.download_button("Download Fallen Capitals CSV", _df_to_csv(df), "fallen_capitals.csv", "text/csv")


# =====================================================================
# MAIN ENTRY POINT
# Dispatches to the appropriate render function based on the user's
# radio selection. Each mode follows the same pattern:
#   stats row -> interactive Folium map -> Matplotlib chart -> dataframe -> CSV
# =====================================================================
MODE_MAP = {
    "Roman Empire": _render_roman_empire,
    "Greek City-States": _render_greek_city_states,
    "Egyptian Dynasties": _render_egyptian_dynasties,
    "Mongol Empire": _render_mongol_empire,
    "Ottoman Empire": _render_ottoman_empire,
    "British Empire": _render_british_empire,
    "Chinese Dynasties": _render_chinese_dynasties,
    "Persian Empire": _render_persian_empire,
    "Famous Battles (30+)": _render_famous_battles,
    "Fallen Capitals (25+)": _render_fallen_capitals,
}

MODE_DESCRIPTIONS = {
    "Roman Empire": "Cities, roads, provinces and maximum territorial extent of the Roman Empire",
    "Greek City-States": "Athens, Sparta, Corinth, Thebes and other poleis of the Greek world",
    "Egyptian Dynasties": "Nile cities, pyramid sites, temples and dynastic timeline from 3100 BC",
    "Mongol Empire": "Campaigns of Genghis Khan, conquered cities and the largest contiguous empire",
    "Ottoman Empire": "Major cities, mosques, palaces and the empire at its peak extent",
    "British Empire": "Colonies, trade routes, key battles and peak territories spanning the globe",
    "Chinese Dynasties": "Capitals of Han, Tang, Song, Ming, Qing and the Great Wall route",
    "Persian Empire": "Persepolis, Susa, Pasargadae, the Royal Road and Achaemenid extent",
    "Famous Battles (30+)": "Thermopylae, Hastings, Waterloo, Stalingrad and more with dates and combatants",
    "Fallen Capitals (25+)": "Constantinople, Carthage, Tenochtitlan, Angkor and other lost cities",
}


def render_empires_maps_tab():
    """Main entry point for the Ancient Empires & Kingdoms tab."""
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001F451 Ancient Empires & Kingdoms</h4>'
        '<p>Rise and fall of empires, capital cities, battle sites & historical territories</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Select Empire / Topic",
        list(MODE_MAP.keys()),
        horizontal=True,
        help="Choose an empire or historical topic to explore on the map.",
    )

    st.caption(MODE_DESCRIPTIONS.get(mode, ""))
    st.markdown("---")

    MODE_MAP[mode]()
