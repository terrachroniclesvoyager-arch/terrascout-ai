# -*- coding: utf-8 -*-
"""
Ancient Calendars & Observatories module for TerraScout AI.
Provides 10 interactive map modes covering ancient astronomical observatories,
calendar systems, sundials, stone circles, solstice sites, navigation heritage,
and modern observatories. All data is curated for offline reliability -- no API
keys needed.
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
import numpy as np

# =====================================================================
# COLOUR PALETTE  (TerraScout dark theme)
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

MODE_COLORS = [
    "#06b6d4", "#ec4899", "#8b5cf6", "#f59e0b", "#10b981",
    "#ef4444", "#3b82f6", "#f97316", "#14b8a6", "#a855f7",
]

MAP_MODES = [
    "Ancient Observatories",
    "Mayan Calendar Sites",
    "Egyptian Sun Temples",
    "Stone Circles & Henges",
    "World Time Zones",
    "Ancient Sundials",
    "Modern Observatories",
    "Solstice & Equinox Sites",
    "Navigation & Star Maps",
    "Calendar Systems Origins",
]


def _color_for(index: int) -> str:
    return MODE_COLORS[index % len(MODE_COLORS)]


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
        center = [25, 10]
    return folium.Map(
        location=center, zoom_start=zoom,
        tiles="CartoDB dark_matter", width="100%", height=500,
    )


def _show_map(m):
    components.html(m._repr_html_(), height=500)


def _df_to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def _add_marker(m, lat, lon, name, popup_html, color="#06b6d4", icon="star",
                radius=None):
    """Add a circle marker or icon marker to a folium map."""
    if radius:
        folium.CircleMarker(
            location=[lat, lon], radius=radius, color=color,
            fill=True, fill_color=color, fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(str(name)),
        ).add_to(m)
    else:
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(str(name)),
            icon=folium.Icon(color="purple", icon=icon, prefix="fa"),
        ).add_to(m)


def _popup_html(fields: dict) -> str:
    """Build safe popup HTML from a dict of label: value pairs."""
    rows = "".join(
        f"<tr><td style='padding:2px 6px;color:#8b97b0;'><b>{escape(str(k))}</b></td>"
        f"<td style='padding:2px 6px;color:#e8ecf4;'>{escape(str(v))}</td></tr>"
        for k, v in fields.items()
    )
    return (
        f"<div style='background:#111827;border-radius:8px;padding:6px;'>"
        f"<table style='font-size:12px;'>{rows}</table></div>"
    )


# =====================================================================
# 1. ANCIENT OBSERVATORIES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_ancient_observatories():
    sites = [
        {"name": "Stonehenge", "country": "England", "lat": 51.1789, "lon": -1.8262,
         "era": "~3000 BC", "alignment": "Summer solstice sunrise / winter solstice sunset",
         "notes": "Neolithic circle aligned with solstice axis, Heel Stone marks midsummer sunrise"},
        {"name": "Chankillo Solar Observatory", "country": "Peru", "lat": -9.5588, "lon": -78.2253,
         "era": "~250 BC", "alignment": "13 towers span annual sunrise arc",
         "notes": "Oldest known solar observatory in the Americas, UNESCO World Heritage"},
        {"name": "Angkor Wat", "country": "Cambodia", "lat": 13.4125, "lon": 103.8670,
         "era": "12th century AD", "alignment": "Spring equinox sunrise over central tower",
         "notes": "Aligned to equinox; solar alignment marks changing seasons"},
        {"name": "Chichen Itza - El Castillo", "country": "Mexico", "lat": 20.6843, "lon": -88.5678,
         "era": "~600 AD", "alignment": "Equinox serpent shadow on north staircase",
         "notes": "Kukulkan pyramid shows feathered serpent shadow at equinox"},
        {"name": "Goseck Circle", "country": "Germany", "lat": 51.1990, "lon": 11.8530,
         "era": "~4900 BC", "alignment": "Winter solstice sunrise and sunset gates",
         "notes": "Neolithic circular enclosure, oldest known solar observatory in Europe"},
        {"name": "Kokino Observatory", "country": "North Macedonia", "lat": 42.2636, "lon": 21.9536,
         "era": "~1800 BC", "alignment": "Markers for solstices and equinoxes",
         "notes": "Megalithic observatory on rocky hilltop, Bronze Age astronomical site"},
        {"name": "Nabta Playa", "country": "Egypt", "lat": 22.5100, "lon": 30.7100,
         "era": "~5000 BC", "alignment": "Summer solstice zenith passage",
         "notes": "Stone circle in Sahara predates Stonehenge by 1000 years"},
        {"name": "Jantar Mantar (Jaipur)", "country": "India", "lat": 26.9249, "lon": 75.8245,
         "era": "1734 AD", "alignment": "Multiple instruments for solstice/equinox/stars",
         "notes": "Collection of 19 astronomical instruments, largest stone sundial in the world"},
        {"name": "Jantar Mantar (Delhi)", "country": "India", "lat": 28.6271, "lon": 77.2166,
         "era": "1724 AD", "alignment": "Samrat Yantra tracks sun position",
         "notes": "First of five Jantar Mantar observatories built by Maharaja Jai Singh II"},
        {"name": "Caracol (Chichen Itza)", "country": "Mexico", "lat": 20.6790, "lon": -88.5710,
         "era": "~800 AD", "alignment": "Venus rise/set alignments in windows",
         "notes": "Mayan astronomical observatory tower tracking Venus cycle"},
        {"name": "Gaocheng Astronomical Observatory", "country": "China", "lat": 34.4050, "lon": 113.0230,
         "era": "1276 AD", "alignment": "Measures shadow length for solstices",
         "notes": "Built by Guo Shoujing; used to create the Shoushi Calendar"},
        {"name": "Tower of the Winds (Athens)", "country": "Greece", "lat": 37.9745, "lon": 23.7267,
         "era": "~50 BC", "alignment": "8-sided sundial and wind vane",
         "notes": "Horologion of Andronikos, served as clock, weather station, compass"},
        {"name": "Ulugh Beg Observatory", "country": "Uzbekistan", "lat": 39.6720, "lon": 66.9780,
         "era": "1420 AD", "alignment": "Giant sextant for star positions",
         "notes": "Largest quadrant sextant, produced star catalog of 1018 stars"},
        {"name": "Arkaim", "country": "Russia", "lat": 52.6464, "lon": 59.5677,
         "era": "~2000 BC", "alignment": "Sunrise/sunset observation points",
         "notes": "Bronze Age fortified settlement with astronomical observation features"},
        {"name": "Great Zimbabwe", "country": "Zimbabwe", "lat": -20.2712, "lon": 30.9336,
         "era": "11th century AD", "alignment": "Possible solstice alignments in tower walls",
         "notes": "Medieval stone city, some scholars suggest astronomical alignments"},
        {"name": "Cheomseongdae", "country": "South Korea", "lat": 35.8347, "lon": 129.2191,
         "era": "647 AD", "alignment": "12 base stones for months, 362 stones for days",
         "notes": "Oldest surviving astronomical observatory in East Asia"},
        {"name": "Mnajdra Temple", "country": "Malta", "lat": 35.8269, "lon": 14.4363,
         "era": "~3600 BC", "alignment": "Equinox/solstice light through doorway",
         "notes": "Megalithic temple with precise solar alignment through main entrance"},
        {"name": "Ales Stenar", "country": "Sweden", "lat": 55.3836, "lon": 14.0536,
         "era": "~600 AD", "alignment": "Ship-shaped stones mark solstice sun positions",
         "notes": "59 boulders arranged in a 67m ship shape, possible Viking solar calendar"},
    ]
    return sites


def _render_ancient_observatories():
    sites = _get_ancient_observatories()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites", len(sites))
    c2.metric("Oldest", "~5000 BC")
    c3.metric("Countries", df["country"].nunique())
    c4.metric("Continents", 6)

    st.markdown("##### Global Distribution of Ancient Astronomical Observatories")
    m = _base_map([25, 10], 2)
    for _, row in df.iterrows():
        html = _popup_html({
            "Site": row["name"], "Country": row["country"],
            "Era": row["era"], "Alignment": row["alignment"],
            "Notes": row["notes"],
        })
        _add_marker(m, row["lat"], row["lon"], row["name"], html,
                     color=ACCENT_CYAN, radius=8)
    _show_map(m)

    # Timeline chart
    fig, ax = _dark_fig(figsize=(10, 4))
    eras = df["era"].tolist()
    names = df["name"].tolist()
    y_pos = range(len(names))
    colors = [_color_for(i) for i in range(len(names))]
    ax.barh(y_pos, [1] * len(names), color=colors, alpha=0.7)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([f"{n} ({e})" for n, e in zip(names, eras)],
                        fontsize=7, color=TEXT_SECONDARY)
    ax.set_xlabel("")
    ax.set_title("Ancient Observatory Sites by Era", color=TEXT_PRIMARY, fontsize=11)
    ax.get_xaxis().set_visible(False)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "ancient_observatories.csv", "text/csv")


# =====================================================================
# 2. MAYAN CALENDAR SITES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_mayan_sites():
    sites = [
        {"name": "Tikal", "country": "Guatemala", "lat": 17.2220, "lon": -89.6237,
         "period": "Classic (200-900 AD)", "calendar_feature": "Long Count inscriptions on stelae",
         "alignment": "Temple I sunrise alignment at equinox",
         "notes": "One of the largest Mayan cities; Temple IV has astronomical sightlines"},
        {"name": "Copan", "country": "Honduras", "lat": 14.8400, "lon": -89.1400,
         "period": "Classic (426-822 AD)", "calendar_feature": "Altar Q records dynastic dates",
         "alignment": "Stela 12 tracks April 12 sunset alignment",
         "notes": "Major center for Mayan astronomy and mathematics"},
        {"name": "Palenque", "country": "Mexico", "lat": 17.4838, "lon": -92.0461,
         "period": "Classic (226-799 AD)", "calendar_feature": "Temple of Inscriptions Long Count",
         "alignment": "Winter solstice sun sets behind Temple of Inscriptions ridge",
         "notes": "Tomb of Pakal with elaborate calendar dates spanning mythical epochs"},
        {"name": "Uxmal", "country": "Mexico", "lat": 20.3594, "lon": -89.7714,
         "period": "Classic (500-1000 AD)", "calendar_feature": "Pyramid of the Magician Venus alignment",
         "alignment": "Governor's Palace aligned to Venus maximum southerly rising",
         "notes": "Governor's Palace is one of the most precise astronomical buildings in Mesoamerica"},
        {"name": "Chichen Itza", "country": "Mexico", "lat": 20.6843, "lon": -88.5678,
         "period": "Terminal Classic (600-1200 AD)", "calendar_feature": "El Castillo as calendar: 365 steps",
         "alignment": "Equinox serpent shadow, Caracol Venus windows",
         "notes": "El Castillo has 91 steps on each side plus top platform = 365 days"},
        {"name": "Calakmul", "country": "Mexico", "lat": 18.1056, "lon": -89.8117,
         "period": "Classic (500 BC - 900 AD)", "calendar_feature": "Rival to Tikal with Long Count stelae",
         "alignment": "Structure II sunrise alignment observations",
         "notes": "Largest Mayan site in Mexico, paired astronomical stelae"},
        {"name": "Bonampak", "country": "Mexico", "lat": 16.7038, "lon": -91.0638,
         "period": "Classic (580-800 AD)", "calendar_feature": "Mural dates record precise calendar rounds",
         "alignment": "Rooms oriented to cardinal directions",
         "notes": "Famous for murals with calendar dates and astronomical references"},
        {"name": "Tulum", "country": "Mexico", "lat": 20.2145, "lon": -87.4291,
         "period": "Post-Classic (1200-1521 AD)", "calendar_feature": "Coastal Venus tracking station",
         "alignment": "El Castillo window aligns with Venus rising",
         "notes": "Walled seaside city used for astronomical navigation and trade"},
        {"name": "Quirigua", "country": "Guatemala", "lat": 15.2700, "lon": -89.0400,
         "period": "Classic (426-810 AD)", "calendar_feature": "Stela E: longest Long Count date",
         "alignment": "Stelae oriented to mark solstice positions",
         "notes": "Has tallest carved stone monuments in the Maya world"},
        {"name": "Xochicalco", "country": "Mexico", "lat": 18.8033, "lon": -99.2958,
         "period": "Epiclassic (650-900 AD)", "calendar_feature": "Cave zenith tube sun observation",
         "alignment": "Zenith passage marked in underground chamber",
         "notes": "Underground observatory where sunbeam enters cave on zenith days"},
        {"name": "Uaxactun", "country": "Guatemala", "lat": 17.3940, "lon": -89.6340,
         "period": "Classic (900 BC - 900 AD)", "calendar_feature": "Earliest known solstice observation group",
         "alignment": "Group E: temples mark solstice and equinox sunrises",
         "notes": "Group E complex is the prototype for Mayan astronomical observatory layouts"},
        {"name": "Dzibilchaltun", "country": "Mexico", "lat": 21.0919, "lon": -89.5983,
         "period": "Classic (500 BC - 1500 AD)", "calendar_feature": "Temple of the Seven Dolls equinox",
         "alignment": "Sun shines through doorway on spring/fall equinox",
         "notes": "Equinox sunrise pierces the temple doorway creating dramatic light effect"},
        {"name": "Edzna", "country": "Mexico", "lat": 19.5979, "lon": -90.2310,
         "period": "Classic (400 BC - 1500 AD)", "calendar_feature": "Five-story pyramid observatory",
         "alignment": "Building of Five Stories has astronomical sightlines",
         "notes": "Sophisticated hydraulic and astronomical engineering"},
        {"name": "Coba", "country": "Mexico", "lat": 20.4947, "lon": -87.7361,
         "period": "Classic (100 BC - 1550 AD)", "calendar_feature": "Nohoch Mul largest pyramid in Yucatan",
         "alignment": "Network of causeways aligned to cardinal points",
         "notes": "42m high pyramid with extensive sacbe (road) network"},
    ]
    return sites


def _render_mayan_sites():
    sites = _get_mayan_sites()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites", len(sites))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Calendar System", "Long Count")
    c4.metric("Base", "Vigesimal (20)")

    st.markdown("##### Mayan Calendar & Astronomical Sites")
    st.caption("The Maya Long Count calendar begins August 11, 3114 BC and tracks "
               "cycles of 144,000 days (b'ak'tun). The 260-day Tzolk'in and 365-day "
               "Haab' interlock to form 52-year Calendar Rounds.")

    m = _base_map([18.5, -89.0], 6)
    cluster = MarkerCluster().add_to(m)
    for i, row in df.iterrows():
        html = _popup_html({
            "Site": row["name"], "Country": row["country"],
            "Period": row["period"], "Calendar": row["calendar_feature"],
            "Alignment": row["alignment"], "Notes": row["notes"],
        })
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(html, max_width=340),
            tooltip=escape(str(row["name"])),
            icon=folium.Icon(color="red", icon="sun-o", prefix="fa"),
        ).add_to(cluster)
    _show_map(m)

    # Chart: sites by period
    fig, ax = _dark_fig(figsize=(10, 4))
    period_counts = df["period"].value_counts()
    bars = ax.barh(range(len(period_counts)), period_counts.values,
                    color=[_color_for(i) for i in range(len(period_counts))], alpha=0.8)
    ax.set_yticks(range(len(period_counts)))
    ax.set_yticklabels(period_counts.index, fontsize=8, color=TEXT_SECONDARY)
    ax.set_xlabel("Number of Sites", fontsize=9)
    ax.set_title("Mayan Sites by Period", color=TEXT_PRIMARY, fontsize=11)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "mayan_calendar_sites.csv", "text/csv")


# =====================================================================
# 3. EGYPTIAN SUN TEMPLES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_egyptian_temples():
    sites = [
        {"name": "Abu Simbel - Great Temple", "lat": 22.3360, "lon": 31.6256,
         "pharaoh": "Ramesses II", "era": "~1264 BC",
         "alignment": "Feb 22 & Oct 22 sunlight illuminates inner sanctuary statues",
         "notes": "Sun penetrates 60m to light three of four statues; Ptah remains in shadow"},
        {"name": "Karnak - Temple of Amun-Ra", "lat": 25.7188, "lon": 32.6573,
         "pharaoh": "Multiple pharaohs", "era": "~2055-100 BC",
         "alignment": "Winter solstice sunrise along main axis",
         "notes": "Great Hypostyle Hall, 134 columns, main axis aligned to winter solstice"},
        {"name": "Luxor Temple", "lat": 25.6995, "lon": 32.6392,
         "pharaoh": "Amenhotep III", "era": "~1400 BC",
         "alignment": "Aligned with Karnak processional avenue",
         "notes": "Inner sanctum receives solstice light, connected to Karnak by sphinx avenue"},
        {"name": "Hatshepsut Temple (Deir el-Bahari)", "lat": 25.7379, "lon": 32.6072,
         "pharaoh": "Hatshepsut", "era": "~1470 BC",
         "alignment": "Winter solstice light enters inner chapel",
         "notes": "Mortuary temple built into cliffs, solar alignment to Amun sanctuary"},
        {"name": "Temple of Horus (Edfu)", "lat": 24.9779, "lon": 32.8734,
         "pharaoh": "Ptolemy III", "era": "237-57 BC",
         "alignment": "Annual festival of 'Beautiful Reunion' sun alignment",
         "notes": "Best-preserved ancient Egyptian temple, detailed astronomical ceiling texts"},
        {"name": "Temple of Isis (Philae)", "lat": 24.0246, "lon": 32.8842,
         "pharaoh": "Ptolemaic", "era": "380 BC - 117 AD",
         "alignment": "Aligned to Sirius (Sopdet) heliacal rising",
         "notes": "Dedicated to Isis; Sirius rising marked start of Nile flood/New Year"},
        {"name": "Dendera Temple (Hathor)", "lat": 26.1417, "lon": 32.6700,
         "pharaoh": "Ptolemaic", "era": "54 BC",
         "alignment": "New Year sunrise through axis, zodiac ceiling",
         "notes": "Famous circular zodiac relief, light shaft for New Year celebration"},
        {"name": "Great Pyramid of Giza", "lat": 29.9792, "lon": 31.1342,
         "pharaoh": "Khufu", "era": "~2560 BC",
         "alignment": "Shafts point to Orion's Belt and Thuban (pole star)",
         "notes": "Air shafts in King's Chamber aligned to Orion (Osiris) and Thuban"},
        {"name": "Pyramid of Khafre", "lat": 29.9761, "lon": 31.1308,
         "pharaoh": "Khafre", "era": "~2520 BC",
         "alignment": "Equinox shadow alignment with Sphinx",
         "notes": "The Great Sphinx faces due east to catch equinox sunrise"},
        {"name": "Abu Simbel - Small Temple", "lat": 22.3370, "lon": 31.6276,
         "pharaoh": "Ramesses II (for Nefertari)", "era": "~1264 BC",
         "alignment": "Dedicated to Hathor; oriented to rising sun",
         "notes": "Temple of Nefertari, six colossal statues, Hathor-sun connection"},
        {"name": "Heliopolis (Tell Hisn)", "lat": 30.1310, "lon": 31.3110,
         "pharaoh": "Multiple dynasties", "era": "~2600 BC onward",
         "alignment": "Center of Ra sun worship, obelisk gnomon observations",
         "notes": "Ancient center of sun-god Ra worship; only Senusret I obelisk remains"},
        {"name": "Temple of Kom Ombo", "lat": 24.4520, "lon": 32.9280,
         "pharaoh": "Ptolemy VI", "era": "180-47 BC",
         "alignment": "Double temple: half to Sobek (moon), half to Horus (sun)",
         "notes": "Unique dual-deity temple, one of few with astronomical calendar reliefs"},
        {"name": "Medinet Habu", "lat": 25.7196, "lon": 32.6015,
         "pharaoh": "Ramesses III", "era": "~1150 BC",
         "alignment": "Festival calendar carved on walls",
         "notes": "Mortuary temple with extensive astronomical and calendrical inscriptions"},
        {"name": "Amarna - Aten Temples", "lat": 27.6453, "lon": 30.8990,
         "pharaoh": "Akhenaten", "era": "~1346 BC",
         "alignment": "Open-air temples oriented to sunrise for Aten worship",
         "notes": "Akhenaten's monotheistic sun-disk worship required open-roofed temples"},
    ]
    return sites


def _render_egyptian_temples():
    sites = _get_egyptian_temples()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temples", len(sites))
    c2.metric("Oldest", "~2600 BC")
    c3.metric("Key Alignment", "Solstice")
    c4.metric("Star Ref.", "Sirius / Orion")

    st.markdown("##### Egyptian Sun Temples & Solar Alignments")
    st.caption("Egyptian temple architecture was intimately connected with solar "
               "astronomy. The annual heliacal rising of Sirius (Sopdet) signaled "
               "the Nile flood and the start of the Egyptian New Year.")

    m = _base_map([26.0, 31.5], 6)
    for i, row in df.iterrows():
        html = _popup_html({
            "Temple": row["name"], "Pharaoh": row["pharaoh"],
            "Era": row["era"], "Alignment": row["alignment"],
            "Notes": row["notes"],
        })
        _add_marker(m, row["lat"], row["lon"], row["name"], html,
                     color=ACCENT_AMBER, radius=8)
    _show_map(m)

    # Nile corridor timeline
    fig, ax = _dark_fig(figsize=(10, 5))
    lats = df["lat"].tolist()
    names = df["name"].tolist()
    ax.scatter(lats, range(len(names)), color=ACCENT_AMBER, s=60, zorder=3)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=7, color=TEXT_SECONDARY)
    ax.set_xlabel("Latitude (south to north along Nile)", fontsize=9)
    ax.set_title("Egyptian Sun Temples along the Nile", color=TEXT_PRIMARY, fontsize=11)
    ax.invert_yaxis()
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "egyptian_sun_temples.csv", "text/csv")


# =====================================================================
# 4. STONE CIRCLES & HENGES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_stone_circles():
    sites = [
        {"name": "Stonehenge", "country": "England", "lat": 51.1789, "lon": -1.8262,
         "era": "~3000 BC", "diameter_m": 33, "stones": 93,
         "type": "Stone circle + trilithons",
         "notes": "Most famous prehistoric monument, solstice aligned sarsen circle"},
        {"name": "Avebury", "country": "England", "lat": 51.4288, "lon": -1.8544,
         "era": "~2850 BC", "diameter_m": 331, "stones": 154,
         "type": "Henge with outer and inner stone circles",
         "notes": "Largest stone circle in the world, village built inside it"},
        {"name": "Ring of Brodgar", "country": "Scotland", "lat": 59.0015, "lon": -3.2295,
         "era": "~2500 BC", "diameter_m": 104, "stones": 60,
         "type": "Stone circle in henge",
         "notes": "27 of original 60 stones survive, part of Heart of Neolithic Orkney"},
        {"name": "Callanish Stones", "country": "Scotland", "lat": 58.1974, "lon": -6.7456,
         "era": "~2900 BC", "diameter_m": 13, "stones": 50,
         "type": "Cruciform stone setting",
         "notes": "Cross-shaped layout aligned to moonrise/set over 18.6-year lunar cycle"},
        {"name": "Almendres Cromlech", "country": "Portugal", "lat": 38.5569, "lon": -8.0614,
         "era": "~6000 BC", "diameter_m": 60, "stones": 95,
         "type": "Elliptical megalithic complex",
         "notes": "Oldest stone circle in Iberian Peninsula, possibly oldest in Europe"},
        {"name": "Nabta Playa", "country": "Egypt", "lat": 22.5100, "lon": 30.7100,
         "era": "~5000 BC", "diameter_m": 4, "stones": 30,
         "type": "Stone circle in former lake bed",
         "notes": "Saharan circle predating Stonehenge by 1000+ years, summer solstice marker"},
        {"name": "Drombeg Stone Circle", "country": "Ireland", "lat": 51.5646, "lon": -9.0869,
         "era": "~1100 BC", "diameter_m": 9, "stones": 17,
         "type": "Recumbent stone circle",
         "notes": "Axial stone marks winter solstice sunset, nearby fulacht fiadh"},
        {"name": "Swinside Stone Circle", "country": "England", "lat": 54.2923, "lon": -3.2689,
         "era": "~2600 BC", "diameter_m": 26, "stones": 55,
         "type": "Flattened stone circle",
         "notes": "One of the most complete stone circles in England, entrance faces SE"},
        {"name": "Castlerigg Stone Circle", "country": "England", "lat": 54.6025, "lon": -3.0983,
         "era": "~3000 BC", "diameter_m": 30, "stones": 38,
         "type": "Oval stone circle with rectangle",
         "notes": "Set in dramatic Lake District landscape, possible astronomical alignments"},
        {"name": "Carnac Stones", "country": "France", "lat": 47.5846, "lon": -3.0746,
         "era": "~3300 BC", "diameter_m": 0, "stones": 3000,
         "type": "Megalithic stone rows",
         "notes": "3000+ standing stones in parallel rows extending 4km, largest collection"},
        {"name": "Rujm el-Hiri (Gilgal Refaim)", "country": "Israel", "lat": 32.9000, "lon": 35.8200,
         "era": "~3000 BC", "diameter_m": 152, "stones": 42000,
         "type": "Concentric stone circles",
         "notes": "Massive concentric stone circles in Golan Heights, summer solstice gate"},
        {"name": "Zorats Karer (Carahunge)", "country": "Armenia", "lat": 39.5514, "lon": 46.0283,
         "era": "~5500 BC", "diameter_m": 0, "stones": 223,
         "type": "Standing stones with holes",
         "notes": "Stones with carved holes possibly for astronomical sighting, debated dating"},
        {"name": "Wassu Stone Circles", "country": "Gambia", "lat": 13.6900, "lon": -14.8900,
         "era": "3rd century BC - 16th century AD", "diameter_m": 8, "stones": 200,
         "type": "Laterite stone circles",
         "notes": "UNESCO World Heritage, part of Senegambian stone circles (over 1000 monuments)"},
        {"name": "Mzora Stone Circle", "country": "Morocco", "lat": 35.4283, "lon": -5.6933,
         "era": "~1600 BC", "diameter_m": 55, "stones": 167,
         "type": "Elliptical stone ring",
         "notes": "Largest stone circle in North Africa, possible astronomical alignments"},
    ]
    return sites


def _render_stone_circles():
    sites = _get_stone_circles()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Circles", len(sites))
    c2.metric("Oldest", "~6000 BC")
    c3.metric("Total Stones", f"{df['stones'].sum():,}")
    c4.metric("Countries", df["country"].nunique())

    st.markdown("##### Stone Circles & Henges Worldwide")
    m = _base_map([45, 0], 3)
    for i, row in df.iterrows():
        html = _popup_html({
            "Name": row["name"], "Country": row["country"],
            "Era": row["era"], "Diameter": f"{row['diameter_m']}m",
            "Stones": row["stones"], "Type": row["type"],
            "Notes": row["notes"],
        })
        _add_marker(m, row["lat"], row["lon"], row["name"], html,
                     color=ACCENT_VIOLET, radius=7)
    _show_map(m)

    # Stone count chart
    fig, ax = _dark_fig(figsize=(10, 4))
    sorted_df = df.sort_values("stones", ascending=True)
    ax.barh(range(len(sorted_df)), sorted_df["stones"].values,
             color=[_color_for(i) for i in range(len(sorted_df))], alpha=0.8)
    ax.set_yticks(range(len(sorted_df)))
    ax.set_yticklabels(sorted_df["name"].values, fontsize=7, color=TEXT_SECONDARY)
    ax.set_xlabel("Number of Stones", fontsize=9)
    ax.set_title("Stone Circles by Stone Count", color=TEXT_PRIMARY, fontsize=11)
    ax.set_xscale("log")
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "stone_circles.csv", "text/csv")


# =====================================================================
# 5. WORLD TIME ZONES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_timezone_landmarks():
    sites = [
        {"name": "Royal Observatory Greenwich", "country": "England", "lat": 51.4769, "lon": -0.0005,
         "utc_offset": "UTC+0", "significance": "Prime Meridian (0 longitude)",
         "notes": "International reference for time and longitude since 1884"},
        {"name": "International Date Line - Fiji", "country": "Fiji", "lat": -17.7134, "lon": 179.9999,
         "utc_offset": "UTC+12", "significance": "Date Line crossing",
         "notes": "Where today becomes yesterday, 180 degrees from Greenwich"},
        {"name": "International Date Line - Tonga", "country": "Tonga", "lat": -21.1789, "lon": -175.1982,
         "utc_offset": "UTC+13", "significance": "First country to see new day",
         "notes": "Tonga and Kiribati are the first places to start each new calendar day"},
        {"name": "Chatham Islands", "country": "New Zealand", "lat": -43.8853, "lon": -176.4620,
         "utc_offset": "UTC+12:45", "significance": "45-minute offset time zone",
         "notes": "One of several places with a non-standard 45-minute UTC offset"},
        {"name": "Kathmandu", "country": "Nepal", "lat": 27.7172, "lon": 85.3240,
         "utc_offset": "UTC+5:45", "significance": "15-minute offset time zone",
         "notes": "Nepal is one of the few countries using a 15-minute offset"},
        {"name": "Mumbai (Bombay)", "country": "India", "lat": 19.0760, "lon": 72.8777,
         "utc_offset": "UTC+5:30", "significance": "IST covers 30-degree longitude span",
         "notes": "India uses a single time zone despite spanning 30 degrees of longitude"},
        {"name": "Urumqi", "country": "China", "lat": 43.8256, "lon": 87.6168,
         "utc_offset": "UTC+8 (Beijing Time)", "significance": "Single zone covers entire China",
         "notes": "China spans 5 geographic time zones but uses one official time (UTC+8)"},
        {"name": "Eucla", "country": "Australia", "lat": -31.6800, "lon": 128.8800,
         "utc_offset": "UTC+8:45", "significance": "Unofficial 45-minute offset",
         "notes": "Tiny border community on the Nullarbor uses unofficial time zone"},
        {"name": "Baker Island", "country": "US Territory", "lat": 0.1936, "lon": -176.4769,
         "utc_offset": "UTC-12", "significance": "Last place on Earth to see each day end",
         "notes": "Uninhabited atoll, UTC-12, among the last places where day ends"},
        {"name": "Line Islands (Kiribati)", "country": "Kiribati", "lat": 1.8721, "lon": -157.4750,
         "utc_offset": "UTC+14", "significance": "Furthest ahead of UTC",
         "notes": "Kiribati moved Line Islands to UTC+14 in 1995 to be same day as rest of country"},
        {"name": "Lord Howe Island", "country": "Australia", "lat": -31.5553, "lon": 159.0821,
         "utc_offset": "UTC+10:30", "significance": "30-minute DST shift",
         "notes": "Only place on Earth that uses a 30-minute daylight saving shift"},
        {"name": "Tehran", "country": "Iran", "lat": 35.6892, "lon": 51.3890,
         "utc_offset": "UTC+3:30", "significance": "IRST 30-minute offset",
         "notes": "Iran Standard Time is 30 minutes offset, unique in the Middle East"},
        {"name": "Marquesas Islands", "country": "French Polynesia", "lat": -9.7710, "lon": -139.0140,
         "utc_offset": "UTC-9:30", "significance": "30-minute offset in Pacific",
         "notes": "One of the most remote 30-minute offset zones in the world"},
        {"name": "Krasnoyarsk", "country": "Russia", "lat": 56.0153, "lon": 92.8932,
         "utc_offset": "UTC+7", "significance": "Russia spans 11 time zones",
         "notes": "Russia has the most time zones of any country (11 zones)"},
        {"name": "Newfoundland (St. John's)", "country": "Canada", "lat": 47.5615, "lon": -52.7126,
         "utc_offset": "UTC-3:30", "significance": "NST 30-minute offset",
         "notes": "Newfoundland Standard Time is 30 minutes ahead of Atlantic Time"},
    ]
    return sites


def _render_time_zones():
    sites = _get_timezone_landmarks()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Landmarks", len(sites))
    c2.metric("Range", "UTC-12 to UTC+14")
    c3.metric("Total Offsets", "~38 unique")
    c4.metric("Oddest", "UTC+5:45 (Nepal)")

    st.markdown("##### World Time Zone Landmarks & Curiosities")
    st.caption("The world has approximately 38 unique UTC offsets, including half-hour "
               "and quarter-hour zones. The International Date Line zigzags through the "
               "Pacific to keep island nations on the same calendar day.")

    m = _base_map([20, 0], 2)
    # Draw Prime Meridian
    folium.PolyLine(
        locations=[[85, 0], [-85, 0]], color=ACCENT_CYAN,
        weight=2, dash_array="8", opacity=0.6,
        tooltip="Prime Meridian (0 longitude)",
    ).add_to(m)
    # Draw International Date Line (approximate)
    folium.PolyLine(
        locations=[[85, 180], [65, 169], [52, 170], [45, 180],
                    [0, 180], [-15, 180], [-45, 180], [-85, 180]],
        color=ACCENT_RED, weight=2, dash_array="8", opacity=0.6,
        tooltip="International Date Line (approximate)",
    ).add_to(m)
    for i, row in df.iterrows():
        html = _popup_html({
            "Location": row["name"], "Country": row["country"],
            "UTC Offset": row["utc_offset"],
            "Significance": row["significance"], "Notes": row["notes"],
        })
        _add_marker(m, row["lat"], row["lon"], row["name"], html,
                     color=ACCENT_EMERALD, radius=7)
    _show_map(m)

    # Offset chart
    fig, ax = _dark_fig(figsize=(10, 4))
    names = df["name"].tolist()
    offsets_str = df["utc_offset"].tolist()
    ax.barh(range(len(names)), [1] * len(names),
             color=[_color_for(i) for i in range(len(names))], alpha=0.7)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels([f"{n}  [{o}]" for n, o in zip(names, offsets_str)],
                        fontsize=7, color=TEXT_SECONDARY)
    ax.set_title("World Time Zone Landmarks", color=TEXT_PRIMARY, fontsize=11)
    ax.get_xaxis().set_visible(False)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "time_zone_landmarks.csv", "text/csv")


# =====================================================================
# 6. ANCIENT SUNDIALS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_ancient_sundials():
    sites = [
        {"name": "Obelisk of Thutmose III", "city": "Heliopolis (now London)", "country": "Egypt/England",
         "lat": 51.5081, "lon": -0.1205, "era": "~1450 BC",
         "type": "Obelisk gnomon", "notes": "Cleopatra's Needle on Thames Embankment, originally a gnomon in Heliopolis"},
        {"name": "Augustus Sundial (Horologium Augusti)", "city": "Rome", "country": "Italy",
         "lat": 41.9009, "lon": 12.4750, "era": "10 BC",
         "type": "Monumental obelisk sundial",
         "notes": "Used the Obelisk of Montecitorio as gnomon, shadow marked on pavement grid"},
        {"name": "Tower of the Winds", "city": "Athens", "country": "Greece",
         "lat": 37.9745, "lon": 23.7267, "era": "~50 BC",
         "type": "Octagonal sundial tower",
         "notes": "Eight sundials on exterior walls, each for a different wind direction"},
        {"name": "Samrat Yantra (Jaipur)", "city": "Jaipur", "country": "India",
         "lat": 26.9249, "lon": 75.8245, "era": "1734 AD",
         "type": "Giant equatorial sundial",
         "notes": "World's largest stone sundial, 27m tall, accurate to 2 seconds"},
        {"name": "Bernini Sundial (St. Peter's)", "city": "Vatican City", "country": "Vatican",
         "lat": 41.9022, "lon": 12.4539, "era": "1817 AD",
         "type": "Obelisk gnomon in piazza",
         "notes": "Vatican Obelisk casts shadow on meridian line in St. Peter's Square"},
        {"name": "Sundial of Ahaz (Biblical)", "city": "Jerusalem", "country": "Israel",
         "lat": 31.7767, "lon": 35.2345, "era": "~700 BC",
         "type": "Staircase sundial",
         "notes": "Referenced in Bible (2 Kings 20:11), possibly a stairway shadow clock"},
        {"name": "Egyptian Shadow Clock (Cairo Museum)", "city": "Cairo", "country": "Egypt",
         "lat": 30.0478, "lon": 31.2336, "era": "~1500 BC",
         "type": "L-shaped shadow clock",
         "notes": "Earliest surviving portable sundial, limestone L-shape with hour markings"},
        {"name": "Horrebow-Paulsen Sundial", "city": "Copenhagen", "country": "Denmark",
         "lat": 55.6838, "lon": 12.5786, "era": "1642 AD",
         "type": "Equatorial sundial",
         "notes": "Round Tower observatory sundial, used for astronomical time-keeping"},
        {"name": "Chinese Sundial (Forbidden City)", "city": "Beijing", "country": "China",
         "lat": 39.9163, "lon": 116.3972, "era": "Ming Dynasty (~1420 AD)",
         "type": "Equatorial dial on marble base",
         "notes": "Symbolic of imperial power over time, placed before the Hall of Supreme Harmony"},
        {"name": "Konark Sun Temple Sundial", "city": "Konark", "country": "India",
         "lat": 19.8876, "lon": 86.0945, "era": "13th century AD",
         "type": "Chariot wheel sundial",
         "notes": "24 wheels act as sundials, shadow from spokes tells time to the minute"},
        {"name": "Mayan Sundial (Xochicalco)", "city": "Xochicalco", "country": "Mexico",
         "lat": 18.8033, "lon": -99.2958, "era": "~700 AD",
         "type": "Zenith tube / cave sundial",
         "notes": "Underground cave where sunbeam enters at zenith passage to mark the season"},
        {"name": "San Miniato al Monte Sundial", "city": "Florence", "country": "Italy",
         "lat": 43.7629, "lon": 11.2650, "era": "1207 AD",
         "type": "Church facade sundial",
         "notes": "Zodiac-decorated sundial on marble inlay facade of Romanesque basilica"},
        {"name": "Qutub Minar Complex", "city": "Delhi", "country": "India",
         "lat": 28.5245, "lon": 77.1855, "era": "1193 AD",
         "type": "Iron pillar gnomon",
         "notes": "Rust-free Iron Pillar may have served as a gnomon for solar observations"},
    ]
    return sites


def _render_ancient_sundials():
    sites = _get_ancient_sundials()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sundials", len(sites))
    c2.metric("Oldest", "~1500 BC")
    c3.metric("Countries", df["country"].nunique())
    c4.metric("Largest", "Samrat Yantra (27m)")

    st.markdown("##### Ancient & Historical Sundials")
    st.caption("Sundials are humanity's oldest scientific instruments for measuring "
               "time. From obelisks used as gnomons in ancient Egypt to the giant "
               "Samrat Yantra in Jaipur accurate to 2 seconds.")

    m = _base_map([30, 30], 2)
    for i, row in df.iterrows():
        html = _popup_html({
            "Sundial": row["name"], "City": row["city"],
            "Country": row["country"], "Era": row["era"],
            "Type": row["type"], "Notes": row["notes"],
        })
        _add_marker(m, row["lat"], row["lon"], row["name"], html,
                     color=ACCENT_AMBER, radius=7)
    _show_map(m)

    # Type distribution
    fig, ax = _dark_fig(figsize=(8, 4))
    type_counts = df["type"].value_counts()
    colors = [_color_for(i) for i in range(len(type_counts))]
    wedges, texts, autotexts = ax.pie(
        type_counts.values, labels=None, autopct="%1.0f%%",
        colors=colors, textprops={"color": TEXT_PRIMARY, "fontsize": 8},
        pctdistance=0.85,
    )
    for t in autotexts:
        t.set_color(TEXT_PRIMARY)
    ax.legend(type_counts.index, loc="center left", bbox_to_anchor=(1, 0.5),
               fontsize=7, labelcolor=TEXT_SECONDARY,
               facecolor=SURFACE, edgecolor="#2a3550")
    ax.set_title("Sundial Types", color=TEXT_PRIMARY, fontsize=11)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "ancient_sundials.csv", "text/csv")


# =====================================================================
# 7. MODERN OBSERVATORIES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_modern_observatories():
    sites = [
        {"name": "Mauna Kea Observatories", "country": "USA (Hawaii)", "lat": 19.8207, "lon": -155.4681,
         "altitude_m": 4205, "type": "Optical / Infrared",
         "telescopes": "Keck I & II, Subaru, Gemini North, CFHT",
         "notes": "13 telescopes on dormant volcano; best ground-based observing conditions on Earth"},
        {"name": "Atacama Large Millimeter Array (ALMA)", "country": "Chile", "lat": -23.0193, "lon": -67.7532,
         "altitude_m": 5058, "type": "Radio / Millimeter",
         "telescopes": "66 antennas (54x12m + 12x7m)",
         "notes": "Highest observatory in the world, imaged first black hole shadow with EHT"},
        {"name": "Paranal Observatory (VLT)", "country": "Chile", "lat": -24.6272, "lon": -70.4042,
         "altitude_m": 2635, "type": "Optical / Infrared",
         "telescopes": "4 x 8.2m Unit Telescopes (VLT), 4 Auxiliaries",
         "notes": "ESO's flagship observatory, VLT Interferometer combines four telescopes"},
        {"name": "La Silla Observatory", "country": "Chile", "lat": -29.2563, "lon": -70.7300,
         "altitude_m": 2400, "type": "Optical",
         "telescopes": "ESO 3.6m, NTT, HARPS spectrograph",
         "notes": "ESO's first observatory in Chile, HARPS discovers exoplanets"},
        {"name": "Palomar Observatory", "country": "USA (California)", "lat": 33.3564, "lon": -116.8650,
         "altitude_m": 1712, "type": "Optical",
         "telescopes": "200-inch (5.1m) Hale Telescope",
         "notes": "Dominated astronomy for decades; Hubble used it to measure cosmic expansion"},
        {"name": "Arecibo Observatory (collapsed 2020)", "country": "Puerto Rico", "lat": 18.3464, "lon": -66.7528,
         "altitude_m": 498, "type": "Radio",
         "telescopes": "305m dish (was world's largest for 53 years)",
         "notes": "Collapsed Dec 2020; sent Arecibo Message to M13 in 1974; mapped asteroids"},
        {"name": "FAST (Five-hundred-meter Aperture)", "country": "China", "lat": 25.6528, "lon": 106.8567,
         "altitude_m": 1000, "type": "Radio",
         "telescopes": "500m single-dish radio telescope",
         "notes": "World's largest single-dish telescope since 2016, Guizhou province karst basin"},
        {"name": "Jodrell Bank Observatory", "country": "England", "lat": 53.2367, "lon": -2.3085,
         "altitude_m": 77, "type": "Radio",
         "telescopes": "Lovell Telescope (76.2m dish)",
         "notes": "Tracked Sputnik in 1957, UNESCO World Heritage Site since 2019"},
        {"name": "Green Bank Observatory", "country": "USA (West Virginia)", "lat": 38.4330, "lon": -79.8397,
         "altitude_m": 800, "type": "Radio",
         "telescopes": "Green Bank Telescope (100m, world's largest steerable dish)",
         "notes": "In National Radio Quiet Zone; used for SETI, pulsar timing, and VLBI"},
        {"name": "South Pole Telescope", "country": "Antarctica", "lat": -89.9910, "lon": -44.3900,
         "altitude_m": 2835, "type": "Millimeter / CMB",
         "telescopes": "10m dish for cosmic microwave background",
         "notes": "Studies cosmic microwave background; extreme cold and dryness ideal for mm-wave"},
        {"name": "Roque de los Muchachos Observatory", "country": "Spain (Canary Islands)", "lat": 28.7567, "lon": -17.8850,
         "altitude_m": 2396, "type": "Optical / Gamma",
         "telescopes": "Gran Telescopio Canarias (10.4m), MAGIC gamma-ray telescopes",
         "notes": "GTC is world's largest single-mirror optical telescope (10.4m)"},
        {"name": "LIGO Hanford", "country": "USA (Washington)", "lat": 46.4551, "lon": -119.4076,
         "altitude_m": 142, "type": "Gravitational Wave",
         "telescopes": "4km L-shaped laser interferometer",
         "notes": "Detected gravitational waves from merging black holes in 2015 (Nobel Prize)"},
        {"name": "LIGO Livingston", "country": "USA (Louisiana)", "lat": 30.5629, "lon": -90.7742,
         "altitude_m": 7, "type": "Gravitational Wave",
         "telescopes": "4km L-shaped laser interferometer",
         "notes": "Twin detector to LIGO Hanford, 3000 km apart for signal confirmation"},
        {"name": "European Southern Observatory (Garching HQ)", "country": "Germany", "lat": 48.2617, "lon": 11.6717,
         "altitude_m": 480, "type": "Headquarters",
         "telescopes": "ESO HQ and data center",
         "notes": "Headquarters of the European Southern Observatory, 16 member states"},
        {"name": "Goldstone Deep Space Complex", "country": "USA (California)", "lat": 35.4267, "lon": -116.8900,
         "altitude_m": 900, "type": "Deep Space Network",
         "telescopes": "70m antenna + multiple dishes",
         "notes": "Part of NASA's Deep Space Network, communicates with interplanetary spacecraft"},
        {"name": "Canberra Deep Space Communication Complex", "country": "Australia", "lat": -35.4014, "lon": 148.9817,
         "altitude_m": 680, "type": "Deep Space Network",
         "telescopes": "70m antenna DSS-43",
         "notes": "Only antenna that can communicate with Voyager 2 in the southern sky"},
    ]
    return sites


def _render_modern_observatories():
    sites = _get_modern_observatories()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Observatories", len(sites))
    c2.metric("Highest", "5058m (ALMA)")
    c3.metric("Largest Dish", "500m (FAST)")
    c4.metric("Countries", df["country"].nunique())

    st.markdown("##### Modern Astronomical Observatories & Space Tracking")
    st.caption("From mountaintop optical telescopes to gravitational wave detectors, "
               "modern observatories push the boundaries of our understanding of the cosmos.")

    m = _base_map([20, 0], 2)
    for i, row in df.iterrows():
        html = _popup_html({
            "Observatory": row["name"], "Country": row["country"],
            "Altitude": f"{row['altitude_m']}m", "Type": row["type"],
            "Telescopes": row["telescopes"], "Notes": row["notes"],
        })
        color = ACCENT_CYAN if "Radio" in row["type"] else (
            ACCENT_VIOLET if "Optical" in row["type"] else ACCENT_EMERALD)
        _add_marker(m, row["lat"], row["lon"], row["name"], html,
                     color=color, radius=8)
    _show_map(m)

    # Altitude chart
    fig, ax = _dark_fig(figsize=(10, 5))
    sorted_df = df.sort_values("altitude_m", ascending=True)
    colors = []
    for t in sorted_df["type"]:
        if "Radio" in t:
            colors.append(ACCENT_CYAN)
        elif "Optical" in t:
            colors.append(ACCENT_VIOLET)
        elif "Gravitational" in t:
            colors.append(ACCENT_PINK)
        else:
            colors.append(ACCENT_EMERALD)
    ax.barh(range(len(sorted_df)), sorted_df["altitude_m"].values,
             color=colors, alpha=0.8)
    ax.set_yticks(range(len(sorted_df)))
    ax.set_yticklabels(sorted_df["name"].values, fontsize=7, color=TEXT_SECONDARY)
    ax.set_xlabel("Altitude (m)", fontsize=9)
    ax.set_title("Observatories by Altitude", color=TEXT_PRIMARY, fontsize=11)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "modern_observatories.csv", "text/csv")


# =====================================================================
# 8. SOLSTICE & EQUINOX SITES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_solstice_sites():
    sites = [
        {"name": "Newgrange", "country": "Ireland", "lat": 53.6947, "lon": -6.4753,
         "event": "Winter Solstice", "era": "~3200 BC",
         "phenomenon": "Sunrise beam enters roof box and illuminates passage tomb chamber for 17 minutes",
         "notes": "Older than Stonehenge and the Great Pyramids; UNESCO World Heritage"},
        {"name": "Stonehenge", "country": "England", "lat": 51.1789, "lon": -1.8262,
         "event": "Summer Solstice", "era": "~3000 BC",
         "phenomenon": "Midsummer sunrise aligns with Heel Stone and main axis",
         "notes": "Thousands gather at solstice; winter solstice sunset also aligned"},
        {"name": "El Castillo (Chichen Itza)", "country": "Mexico", "lat": 20.6843, "lon": -88.5678,
         "event": "Spring/Fall Equinox", "era": "~600 AD",
         "phenomenon": "Triangular shadow pattern descends staircase as serpent Kukulkan",
         "notes": "Shadow serpent appears for ~45 min during equinox afternoons"},
        {"name": "Mnajdra Temple", "country": "Malta", "lat": 35.8269, "lon": 14.4363,
         "event": "Equinox + Solstices", "era": "~3600 BC",
         "phenomenon": "Equinox light floods main axis; solstice light hits side slabs",
         "notes": "Precision megalithic alignment older than most Egyptian temples"},
        {"name": "Maeshowe", "country": "Scotland", "lat": 58.9963, "lon": -3.1879,
         "event": "Winter Solstice", "era": "~2800 BC",
         "phenomenon": "Setting sun shines down passage to illuminate back wall",
         "notes": "Neolithic chambered cairn, Viking runes carved inside walls"},
        {"name": "Angkor Wat", "country": "Cambodia", "lat": 13.4125, "lon": 103.8670,
         "event": "Spring Equinox", "era": "12th century AD",
         "phenomenon": "Sun rises directly over central tower on equinox morning",
         "notes": "Aligned to equinox sunrise; temple represents Mount Meru cosmology"},
        {"name": "Karnak Temple", "country": "Egypt", "lat": 25.7188, "lon": 32.6573,
         "event": "Winter Solstice", "era": "~2055 BC",
         "phenomenon": "Winter solstice sunrise aligns with main temple axis (east-west)",
         "notes": "The Great Temple of Amun-Ra oriented to shortest day of the year"},
        {"name": "Abu Simbel", "country": "Egypt", "lat": 22.3360, "lon": 31.6256,
         "event": "Feb 22 / Oct 22", "era": "~1264 BC",
         "phenomenon": "Sunlight penetrates 60m to illuminate 3 of 4 inner statues",
         "notes": "Occurs on Ramesses II birthday and coronation day; Ptah stays dark"},
        {"name": "Goseck Circle", "country": "Germany", "lat": 51.1990, "lon": 11.8530,
         "event": "Winter Solstice", "era": "~4900 BC",
         "phenomenon": "Southern gates frame winter solstice sunrise and sunset",
         "notes": "One of the oldest known solar observatories in Europe"},
        {"name": "Chaco Canyon (Fajada Butte)", "country": "USA", "lat": 36.0604, "lon": -107.9567,
         "event": "Summer Solstice / Equinox", "era": "~1000 AD",
         "phenomenon": "Sun Dagger: light shafts bisect spiral petroglyph at solstice",
         "notes": "Ancestral Puebloan site; rock slabs create light dagger on spiral carving"},
        {"name": "Grianan of Aileach", "country": "Ireland", "lat": 55.0233, "lon": -7.4300,
         "event": "Summer Solstice", "era": "~1700 BC",
         "phenomenon": "Hilltop fort entrance aligned to midsummer sunrise",
         "notes": "Iron Age hillfort with possible Neolithic origins, panoramic views"},
        {"name": "Gavr'inis", "country": "France", "lat": 47.5711, "lon": -2.8967,
         "event": "Winter Solstice", "era": "~3500 BC",
         "phenomenon": "Passage alignment illuminates carved chamber stones at solstice",
         "notes": "Megalithic cairn on island in Gulf of Morbihan, elaborate carvings"},
        {"name": "Dowth", "country": "Ireland", "lat": 53.7019, "lon": -6.4494,
         "event": "Winter Solstice", "era": "~3200 BC",
         "phenomenon": "Afternoon winter solstice sun enters south tomb passage",
         "notes": "Part of Bru na Boinne complex with Newgrange and Knowth"},
        {"name": "Kokino Observatory", "country": "North Macedonia", "lat": 42.2636, "lon": 21.9536,
         "event": "Equinox + Solstices", "era": "~1800 BC",
         "phenomenon": "Rock markers positioned for solstice and equinox sunrise observations",
         "notes": "Megalithic hilltop observatory, recognized by NASA as ancient observatory"},
    ]
    return sites


def _render_solstice_sites():
    sites = _get_solstice_sites()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sites", len(sites))
    c2.metric("Oldest", "~4900 BC")
    c3.metric("Countries", df["country"].nunique())
    c4.metric("Events", df["event"].nunique())

    st.markdown("##### Solstice & Equinox Alignment Sites")
    st.caption("Across millennia, humans built structures precisely aligned to "
               "solstice and equinox sun positions -- marking the turning points of "
               "the year for agriculture, religion, and governance.")

    m = _base_map([35, 10], 3)
    event_colors = {
        "Winter Solstice": ACCENT_CYAN,
        "Summer Solstice": ACCENT_AMBER,
        "Spring/Fall Equinox": ACCENT_EMERALD,
        "Equinox + Solstices": ACCENT_VIOLET,
        "Spring Equinox": ACCENT_EMERALD,
        "Feb 22 / Oct 22": ACCENT_PINK,
        "Summer Solstice / Equinox": ACCENT_AMBER,
    }
    for i, row in df.iterrows():
        html = _popup_html({
            "Site": row["name"], "Country": row["country"],
            "Event": row["event"], "Era": row["era"],
            "Phenomenon": row["phenomenon"], "Notes": row["notes"],
        })
        color = event_colors.get(row["event"], ACCENT_CYAN)
        _add_marker(m, row["lat"], row["lon"], row["name"], html,
                     color=color, radius=8)
    _show_map(m)

    # Event type chart
    fig, ax = _dark_fig(figsize=(8, 4))
    event_counts = df["event"].value_counts()
    bars = ax.bar(range(len(event_counts)), event_counts.values,
                   color=[event_colors.get(e, ACCENT_CYAN) for e in event_counts.index],
                   alpha=0.8)
    ax.set_xticks(range(len(event_counts)))
    ax.set_xticklabels(event_counts.index, fontsize=7, color=TEXT_SECONDARY, rotation=25, ha="right")
    ax.set_ylabel("Number of Sites", fontsize=9)
    ax.set_title("Sites by Astronomical Event", color=TEXT_PRIMARY, fontsize=11)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "solstice_equinox_sites.csv", "text/csv")


# =====================================================================
# 9. NAVIGATION & STAR MAPS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_navigation_sites():
    sites = [
        {"name": "Polynesian Navigation Origin (Tahiti)", "region": "Polynesia",
         "lat": -17.6509, "lon": -149.4260, "era": "~3000 BC onward",
         "tradition": "Polynesian wayfinding", "method": "Star compass, wave patterns, bird migration",
         "notes": "Master navigators (palu) sailed vast Pacific using star paths, swells, and cloud reading"},
        {"name": "Hokule'a Home Port (Honolulu)", "region": "Hawaii",
         "lat": 21.3069, "lon": -157.8583, "era": "1976 AD (revival)",
         "tradition": "Hawaiian voyaging canoe", "method": "Traditional star navigation revived by Nainoa Thompson",
         "notes": "Double-hulled canoe sailed Hawaii-Tahiti without instruments in 1976"},
        {"name": "Rapa Nui (Easter Island)", "region": "Polynesia",
         "lat": -27.1127, "lon": -109.3497, "era": "~400 AD",
         "tradition": "Polynesian settlement", "method": "Star path navigation across open Pacific",
         "notes": "Most remote inhabited island; Polynesian navigators found it using star paths"},
        {"name": "Viking Navigation (Trondheim)", "region": "Scandinavia",
         "lat": 63.4305, "lon": 10.3951, "era": "~800-1100 AD",
         "tradition": "Norse seafaring", "method": "Sun stones (Iceland spar), sun compass, bearing dial",
         "notes": "Vikings may have used calcite sun stones to locate sun through clouds"},
        {"name": "Viking Navigation (Reykjavik)", "region": "Iceland",
         "lat": 64.1466, "lon": -21.9426, "era": "~870 AD",
         "tradition": "Norse settlement", "method": "Latitude sailing, sun stone, ravens",
         "notes": "Settlement of Iceland via latitude sailing and releasing ravens to find land"},
        {"name": "L'Anse aux Meadows", "region": "North America",
         "lat": 51.5882, "lon": -55.5334, "era": "~1000 AD",
         "tradition": "Viking transatlantic", "method": "Star / sun navigation across North Atlantic",
         "notes": "Only confirmed Norse site in Americas, navigated using Polaris and sun stones"},
        {"name": "Marshall Islands Stick Charts", "region": "Micronesia",
         "lat": 7.1164, "lon": 171.1858, "era": "Traditional (pre-contact)",
         "tradition": "Marshallese navigation", "method": "Stick charts mapping wave refraction patterns",
         "notes": "Palm rib and shell charts encoded ocean swell patterns around atolls"},
        {"name": "Astrolabe Origins (Alexandria)", "region": "Mediterranean",
         "lat": 31.2001, "lon": 29.9187, "era": "~150 BC",
         "tradition": "Hellenistic astronomy", "method": "Astrolabe: star map + analog computer",
         "notes": "Attributed to Hipparchus; planispheric astrolabe models sky on flat plate"},
        {"name": "Islamic Golden Age Navigation (Baghdad)", "region": "Middle East",
         "lat": 33.3152, "lon": 44.3661, "era": "~800-1200 AD",
         "tradition": "Islamic astronomy", "method": "Refined astrolabe, kamal, star tables (zij)",
         "notes": "Al-Khwarizmi, Al-Sufi, and others refined star catalogs and navigation instruments"},
        {"name": "Chinese Star Map (Dunhuang)", "region": "China",
         "lat": 40.1420, "lon": 94.6619, "era": "~700 AD",
         "tradition": "Chinese astronomy", "method": "Oldest complete star atlas (1300+ stars)",
         "notes": "Dunhuang star chart from Cave 17 is the oldest complete preserved star atlas"},
        {"name": "Portuguese School of Navigation (Sagres)", "region": "Europe",
         "lat": 37.0029, "lon": -8.9483, "era": "15th century AD",
         "tradition": "Age of Discovery", "method": "Cross-staff, astrolabe, Polaris latitude",
         "notes": "Henry the Navigator's school pioneered celestial navigation for ocean exploration"},
        {"name": "Greenwich Observatory", "region": "Europe",
         "lat": 51.4769, "lon": -0.0005, "era": "1675 AD",
         "tradition": "British astronomy", "method": "Chronometer method (longitude by time)",
         "notes": "Founded to solve the longitude problem for maritime navigation"},
        {"name": "Aboriginal Songlines (Uluru)", "region": "Australia",
         "lat": -25.3444, "lon": 131.0369, "era": "60000+ years",
         "tradition": "Indigenous Australian", "method": "Star maps in oral tradition (songlines)",
         "notes": "Aboriginal Australians encode navigation routes in songs referencing star positions"},
        {"name": "Inuit Star Navigation (Iqaluit)", "region": "Arctic",
         "lat": 63.7467, "lon": -68.5170, "era": "Traditional",
         "tradition": "Inuit wayfinding", "method": "Star trails, snow drift patterns, wind direction",
         "notes": "Inuit navigated featureless Arctic using stars, wind-carved snow patterns (sastrugi)"},
    ]
    return sites


def _render_navigation():
    sites = _get_navigation_sites()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Traditions", len(sites))
    c2.metric("Oldest", "60000+ yrs")
    c3.metric("Regions", df["region"].nunique())
    c4.metric("Methods", "Stars, waves, wind")

    st.markdown("##### Navigation & Star Map Heritage Sites")
    st.caption("From Polynesian wayfinders reading waves and stars to Viking sun stones "
               "and Islamic astrolabes, diverse cultures developed sophisticated methods "
               "of celestial navigation.")

    m = _base_map([20, 0], 2)
    tradition_colors = {
        "Polynesian wayfinding": ACCENT_CYAN,
        "Hawaiian voyaging canoe": ACCENT_CYAN,
        "Polynesian settlement": ACCENT_CYAN,
        "Norse seafaring": ACCENT_RED,
        "Norse settlement": ACCENT_RED,
        "Viking transatlantic": ACCENT_RED,
        "Marshallese navigation": ACCENT_EMERALD,
        "Hellenistic astronomy": ACCENT_AMBER,
        "Islamic astronomy": ACCENT_VIOLET,
        "Chinese astronomy": ACCENT_PINK,
        "Age of Discovery": ACCENT_AMBER,
        "British astronomy": ACCENT_EMERALD,
        "Indigenous Australian": "#f97316",
        "Inuit wayfinding": "#38bdf8",
    }
    for i, row in df.iterrows():
        html = _popup_html({
            "Site": row["name"], "Region": row["region"],
            "Era": row["era"], "Tradition": row["tradition"],
            "Method": row["method"], "Notes": row["notes"],
        })
        color = tradition_colors.get(row["tradition"], ACCENT_CYAN)
        _add_marker(m, row["lat"], row["lon"], row["name"], html,
                     color=color, radius=8)
    # Draw Polynesian triangle
    folium.Polygon(
        locations=[[-17.65, -149.43], [21.31, -157.86], [-27.11, -109.35], [-17.65, -149.43]],
        color=ACCENT_CYAN, fill=True, fill_color=ACCENT_CYAN, fill_opacity=0.05,
        weight=1, dash_array="6",
        tooltip="Polynesian Triangle",
    ).add_to(m)
    _show_map(m)

    # Traditions chart
    fig, ax = _dark_fig(figsize=(10, 4))
    region_counts = df["region"].value_counts()
    ax.barh(range(len(region_counts)), region_counts.values,
             color=[_color_for(i) for i in range(len(region_counts))], alpha=0.8)
    ax.set_yticks(range(len(region_counts)))
    ax.set_yticklabels(region_counts.index, fontsize=8, color=TEXT_SECONDARY)
    ax.set_xlabel("Number of Sites", fontsize=9)
    ax.set_title("Navigation Heritage by Region", color=TEXT_PRIMARY, fontsize=11)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "navigation_star_maps.csv", "text/csv")


# =====================================================================
# 10. CALENDAR SYSTEMS ORIGINS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_calendar_origins():
    sites = [
        {"name": "Gregorian Calendar (Vatican)", "system": "Gregorian",
         "lat": 41.9022, "lon": 12.4539, "origin_year": "1582 AD",
         "type": "Solar", "epoch": "Birth of Christ (Anno Domini)",
         "year_length": "365.2425 days", "months": 12,
         "notes": "Introduced by Pope Gregory XIII to correct Julian drift; standard world calendar"},
        {"name": "Julian Calendar (Rome)", "system": "Julian",
         "lat": 41.9028, "lon": 12.4964, "origin_year": "45 BC",
         "type": "Solar", "epoch": "Roman founding (Ab Urbe Condita)",
         "year_length": "365.25 days", "months": 12,
         "notes": "Introduced by Julius Caesar with help from Sosigenes of Alexandria"},
        {"name": "Islamic Calendar (Medina)", "system": "Islamic (Hijri)",
         "lat": 24.4686, "lon": 39.6142, "origin_year": "622 AD",
         "type": "Lunar", "epoch": "Hijra (migration to Medina)",
         "year_length": "354.37 days", "months": 12,
         "notes": "Pure lunar calendar; months begin with new crescent moon sighting"},
        {"name": "Hebrew Calendar (Jerusalem)", "system": "Hebrew",
         "lat": 31.7683, "lon": 35.2137, "origin_year": "~3761 BC",
         "type": "Lunisolar", "epoch": "Creation of the World (Anno Mundi)",
         "year_length": "353-385 days", "months": "12-13",
         "notes": "Intercalary month (Adar II) added 7 times in 19-year Metonic cycle"},
        {"name": "Hindu Calendar (Ujjain)", "system": "Hindu (Vikram Samvat)",
         "lat": 23.1793, "lon": 75.7849, "origin_year": "57 BC",
         "type": "Lunisolar", "epoch": "Coronation of King Vikramaditya",
         "year_length": "~365.2588 days", "months": 12,
         "notes": "Multiple regional variants (Saka, Vikram Samvat); based on sidereal year"},
        {"name": "Chinese Calendar (Xian)", "system": "Chinese",
         "lat": 34.2658, "lon": 108.9541, "origin_year": "~2637 BC",
         "type": "Lunisolar", "epoch": "Reign of Yellow Emperor (traditional)",
         "year_length": "353-385 days", "months": "12-13",
         "notes": "60-year cycle of Heavenly Stems and Earthly Branches; zodiac animals"},
        {"name": "Egyptian Calendar (Heliopolis)", "system": "Egyptian",
         "lat": 30.1310, "lon": 31.3110, "origin_year": "~4236 BC",
         "type": "Solar", "epoch": "Heliacal rising of Sirius (Sopdet)",
         "year_length": "365 days (no leap year)", "months": 12,
         "notes": "3 seasons of 4 months of 30 days + 5 epagomenal days; basis for Julian calendar"},
        {"name": "Mayan Long Count (Izapa)", "system": "Mayan Long Count",
         "lat": 14.9500, "lon": -92.2333, "origin_year": "3114 BC",
         "type": "Vigesimal count", "epoch": "Creation date (August 11, 3114 BC)",
         "year_length": "365.2420 days (Haab')", "months": "18 + Wayeb",
         "notes": "Long Count tracks days from creation; interlocking Tzolk'in (260d) and Haab' (365d)"},
        {"name": "Persian Calendar (Isfahan)", "system": "Solar Hijri",
         "lat": 32.6546, "lon": 51.6680, "origin_year": "622 AD",
         "type": "Solar", "epoch": "Hijra (migration of Muhammad)",
         "year_length": "365.2424 days", "months": 12,
         "notes": "Most accurate calendar in use; based on astronomical observation of vernal equinox"},
        {"name": "Ethiopian Calendar (Axum)", "system": "Ethiopian (Ge'ez)",
         "lat": 14.1310, "lon": 38.7469, "origin_year": "~8 AD",
         "type": "Solar", "epoch": "Annunciation (differs from Gregorian by 7-8 years)",
         "year_length": "365.25 days", "months": "13 (12 x 30d + 1 x 5-6d)",
         "notes": "13-month calendar still in official use; 7-8 years behind Gregorian"},
        {"name": "Buddhist Calendar (Bodh Gaya)", "system": "Buddhist",
         "lat": 24.6961, "lon": 84.9911, "origin_year": "544 BC",
         "type": "Lunisolar", "epoch": "Parinirvana of Buddha",
         "year_length": "354-384 days", "months": "12-13",
         "notes": "Used in Southeast Asia; intercalary months keep synchronized with solar year"},
        {"name": "Zoroastrian Calendar (Yazd)", "system": "Zoroastrian (Qadimi/Fasli)",
         "lat": 31.8974, "lon": 54.3569, "origin_year": "~389 BC",
         "type": "Solar", "epoch": "Coronation of Yazdegerd III (or earlier)",
         "year_length": "365 days", "months": "12 (30 days each + 5 Gatha days)",
         "notes": "Ancient Iranian calendar; each day and month named after Zoroastrian deities"},
        {"name": "Babylonian Calendar (Babylon)", "system": "Babylonian",
         "lat": 32.5363, "lon": 44.4209, "origin_year": "~2000 BC",
         "type": "Lunisolar", "epoch": "Seleucid era (later standardization)",
         "year_length": "354-384 days", "months": "12-13",
         "notes": "First systematic lunisolar calendar; Metonic cycle discovered here for intercalation"},
        {"name": "Aztec Calendar (Tenochtitlan)", "system": "Aztec (Tonalpohualli + Xiuhpohualli)",
         "lat": 19.4326, "lon": -99.1332, "origin_year": "~14th century AD",
         "type": "Dual count", "epoch": "Fifth Sun creation myth",
         "year_length": "365 days (Xiuhpohualli)", "months": "18 x 20d + 5 nemontemi",
         "notes": "Sun Stone encodes cosmological calendar; 260-day ritual + 365-day solar count"},
    ]
    return sites


def _render_calendar_origins():
    sites = _get_calendar_origins()
    df = pd.DataFrame(sites)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Systems", len(sites))
    c2.metric("Oldest", "~4236 BC")
    c3.metric("Solar", len(df[df["type"].str.contains("Solar")]))
    c4.metric("Lunisolar", len(df[df["type"].str.contains("Lunisolar")]))

    st.markdown("##### Calendar Systems of the World -- Origins & Principles")
    st.caption("Human civilizations independently developed calendar systems to track "
               "agricultural seasons, religious observances, and civic life. Some are "
               "solar, some lunar, and many are lunisolar hybrids.")

    m = _base_map([25, 40], 2)
    type_colors = {
        "Solar": ACCENT_AMBER,
        "Lunar": "#a0a0ff",
        "Lunisolar": ACCENT_EMERALD,
        "Vigesimal count": ACCENT_RED,
        "Dual count": ACCENT_PINK,
    }
    for i, row in df.iterrows():
        html = _popup_html({
            "System": row["system"], "Location": row["name"],
            "Origin": row["origin_year"], "Type": row["type"],
            "Epoch": row["epoch"], "Year Length": str(row["year_length"]),
            "Months": str(row["months"]), "Notes": row["notes"],
        })
        color = type_colors.get(row["type"], ACCENT_CYAN)
        _add_marker(m, row["lat"], row["lon"], row["name"], html,
                     color=color, radius=8)
    _show_map(m)

    # Calendar type distribution
    fig, ax = _dark_fig(figsize=(8, 4))
    type_counts = df["type"].value_counts()
    colors = [type_colors.get(t, ACCENT_CYAN) for t in type_counts.index]
    wedges, texts, autotexts = ax.pie(
        type_counts.values, labels=type_counts.index, autopct="%1.0f%%",
        colors=colors, textprops={"color": TEXT_PRIMARY, "fontsize": 9},
        pctdistance=0.8,
    )
    for t in autotexts:
        t.set_color(TEXT_PRIMARY)
    ax.set_title("Calendar Systems by Type", color=TEXT_PRIMARY, fontsize=11)
    st.image(_fig_to_bytes(fig), use_container_width=True)

    # Month comparison chart
    fig2, ax2 = _dark_fig(figsize=(10, 4))
    display_df = df[["system", "months"]].copy()
    display_df["months_num"] = pd.to_numeric(display_df["months"], errors="coerce").fillna(12.5)
    sorted_cal = display_df.sort_values("months_num")
    ax2.barh(range(len(sorted_cal)), sorted_cal["months_num"].values,
              color=[_color_for(i) for i in range(len(sorted_cal))], alpha=0.8)
    ax2.set_yticks(range(len(sorted_cal)))
    ax2.set_yticklabels(sorted_cal["system"].values, fontsize=8, color=TEXT_SECONDARY)
    ax2.set_xlabel("Months per Year", fontsize=9)
    ax2.set_title("Calendar Systems by Months per Year", color=TEXT_PRIMARY, fontsize=11)
    ax2.axvline(x=12, color=TEXT_SECONDARY, linestyle="--", alpha=0.4, label="12 months")
    st.image(_fig_to_bytes(fig2), use_container_width=True)

    st.dataframe(df, use_container_width=True)
    st.download_button("Download CSV", _df_to_csv(df),
                        "calendar_origins.csv", "text/csv")


# =====================================================================
# OVERPASS SEARCH (enrichment for observatories/sundials nearby)
# =====================================================================
@st.cache_data(ttl=3600)
def _search_nearby_heritage(lat: float, lon: float, radius_km: float = 20) -> list:
    """Search for astronomical/historical heritage features near a point
    using the Overpass API (free, no key needed)."""
    import requests
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:30];
(
  node["historic"="archaeological_site"](around:{radius_m},{lat},{lon});
  node["tourism"="attraction"](around:{radius_m},{lat},{lon});
  node["man_made"="observatory"](around:{radius_m},{lat},{lon});
  node["man_made"="sundial"](around:{radius_m},{lat},{lon});
);
out body;
"""
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query}, timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        results = []
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            results.append({
                "name": tags.get("name", "Unnamed"),
                "type": tags.get("historic", tags.get("man_made", tags.get("tourism", "unknown"))),
                "lat": el.get("lat", 0),
                "lon": el.get("lon", 0),
            })
        return results
    except Exception:
        return []


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_calendar_maps_tab():
    """Main entry point -- renders the Ancient Calendars & Observatories tab."""

    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001f319 Ancient Calendars & Observatories</h4>'
        '<p>Explore astronomical observatories, calendar systems, stone circles, '
        'sundials, and celestial navigation heritage across the ages.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        key="calendar_maps_mode",
    )

    st.markdown("---")

    # -----------------------------------------------------------------
    if mode == "Ancient Observatories":
        st.markdown("### Ancient Astronomical Observatories")
        st.markdown(
            "From Neolithic stone circles to medieval sextants, ancient peoples built "
            "structures to observe and predict celestial events. These observatories "
            "tracked solstices, equinoxes, lunar cycles, and planetary movements with "
            "remarkable precision."
        )
        _render_ancient_observatories()

    # -----------------------------------------------------------------
    elif mode == "Mayan Calendar Sites":
        st.markdown("### Mayan Calendar & Astronomical Sites")
        st.markdown(
            "The Maya civilization developed one of the most sophisticated calendar "
            "systems in human history. The Long Count, Tzolk'in (260-day), and "
            "Haab' (365-day) calendars interlocked to create precise astronomical "
            "tracking spanning millions of years."
        )
        _render_mayan_sites()

    # -----------------------------------------------------------------
    elif mode == "Egyptian Sun Temples":
        st.markdown("### Egyptian Sun Temples & Solar Alignments")
        st.markdown(
            "Ancient Egyptian temple architecture was deeply intertwined with solar "
            "astronomy. Temples were oriented to catch solstice or equinox sunlight, "
            "and the heliacal rising of Sirius (Sopdet) signaled the Nile flood "
            "and the new year."
        )
        _render_egyptian_temples()

    # -----------------------------------------------------------------
    elif mode == "Stone Circles & Henges":
        st.markdown("### Stone Circles & Henges of the World")
        st.markdown(
            "Megalithic stone circles appear across Europe, Africa, and the Middle "
            "East. Many show precise astronomical alignments, serving as calendars, "
            "ceremonial sites, and gathering places for communities tracking the "
            "cycles of sun, moon, and stars."
        )
        _render_stone_circles()

    # -----------------------------------------------------------------
    elif mode == "World Time Zones":
        st.markdown("### World Time Zone Landmarks & Curiosities")
        st.markdown(
            "The modern system of 24 time zones was adopted in 1884 at the "
            "International Meridian Conference. Today, approximately 38 unique UTC "
            "offsets exist, including unusual half-hour and quarter-hour zones that "
            "reflect political, geographic, and cultural decisions."
        )
        _render_time_zones()

    # -----------------------------------------------------------------
    elif mode == "Ancient Sundials":
        st.markdown("### Ancient & Historical Sundials")
        st.markdown(
            "Sundials are the oldest known instruments for measuring the passage "
            "of time. Ancient Egyptians used obelisks as gnomons, Romans built "
            "monumental sundials, and Indian astronomers created stone dials "
            "accurate to the second."
        )
        _render_ancient_sundials()

    # -----------------------------------------------------------------
    elif mode == "Modern Observatories":
        st.markdown("### Modern Astronomical Observatories")
        st.markdown(
            "Today's observatories use cutting-edge technology -- optical mirrors "
            "over 10 meters wide, radio antenna arrays spanning kilometers, and "
            "laser interferometers detecting gravitational waves from colliding "
            "black holes billions of light-years away."
        )
        _render_modern_observatories()

    # -----------------------------------------------------------------
    elif mode == "Solstice & Equinox Sites":
        st.markdown("### Solstice & Equinox Alignment Sites")
        st.markdown(
            "For thousands of years, humans have marked the turning points of "
            "the year -- the solstices (longest and shortest days) and equinoxes "
            "(equal day and night) -- by building structures that capture dramatic "
            "light effects at these precise moments."
        )
        _render_solstice_sites()

    # -----------------------------------------------------------------
    elif mode == "Navigation & Star Maps":
        st.markdown("### Celestial Navigation & Star Map Heritage")
        st.markdown(
            "Before GPS and compasses, navigators crossed oceans using the stars, "
            "sun, waves, and wind. Polynesian wayfinders, Viking seafarers, Arab "
            "astronomers, and indigenous peoples worldwide developed sophisticated "
            "techniques for finding their way across the Earth."
        )
        _render_navigation()

    # -----------------------------------------------------------------
    elif mode == "Calendar Systems Origins":
        st.markdown("### Calendar Systems of the World")
        st.markdown(
            "Every civilization developed methods to track time. Solar calendars "
            "follow the sun, lunar calendars follow the moon, and lunisolar "
            "calendars harmonize both. From the 365-day Egyptian calendar to the "
            "vigesimal Mayan Long Count, these systems reflect humanity's deep "
            "connection to celestial cycles."
        )
        _render_calendar_origins()

    # -----------------------------------------------------------------
    # Enrichment: Nearby Heritage Search
    # -----------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Search Nearby Astronomical Heritage")
    st.caption("Use the Overpass API to search for observatories, sundials, and "
               "archaeological sites near any coordinates.")

    col_lat, col_lon, col_rad = st.columns(3)
    search_lat = col_lat.number_input("Latitude", value=51.18, step=0.01,
                                       key="cal_search_lat")
    search_lon = col_lon.number_input("Longitude", value=-1.83, step=0.01,
                                       key="cal_search_lon")
    search_rad = col_rad.number_input("Radius (km)", value=20.0, step=5.0,
                                       min_value=1.0, max_value=100.0,
                                       key="cal_search_rad")

    if st.button("Search Nearby", key="cal_search_btn"):
        with st.spinner("Querying Overpass API..."):
            results = _search_nearby_heritage(search_lat, search_lon, search_rad)
        if results:
            st.success(f"Found {len(results)} features within {search_rad} km")
            res_df = pd.DataFrame(results)

            rc1, rc2 = st.columns(2)
            rc1.metric("Features Found", len(results))
            rc2.metric("Types", res_df["type"].nunique())

            rm = _base_map([search_lat, search_lon], 11)
            folium.CircleMarker(
                location=[search_lat, search_lon], radius=5,
                color=ACCENT_RED, fill=True, fill_opacity=0.8,
                tooltip="Search Center",
            ).add_to(rm)
            for _, row in res_df.iterrows():
                html = _popup_html({
                    "Name": row["name"], "Type": row["type"],
                    "Lat": f"{row['lat']:.4f}", "Lon": f"{row['lon']:.4f}",
                })
                _add_marker(rm, row["lat"], row["lon"], row["name"], html,
                             color=ACCENT_VIOLET, radius=6)
            _show_map(rm)

            st.dataframe(res_df, use_container_width=True)
            st.download_button("Download Search Results CSV",
                                _df_to_csv(res_df),
                                "nearby_heritage.csv", "text/csv",
                                key="cal_search_download")
        else:
            st.info("No features found in this area. Try increasing the radius "
                    "or searching near a known heritage site.")
