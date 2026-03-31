# -*- coding: utf-8 -*-
"""
Global Hidden & Isolated Structures module for TerraScout AI.
Visualizes a curated database of the world's most remote, isolated, and
hidden structures, specifically including extreme outposts in the Amazon,
Congo, Siberia, and Antarctica.
Users can filter by category to see these hidden gems light up globally.
"""

import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import html as html_module
from streamlit.components.v1 import html as st_html

# ── Theme ──
_BG, _SURFACE, _CARD = "#0a0e1a", "#111827", "#1a2235"
_BORDER, _TEXT, _TEXT2, _ACCENT = "#2a3550", "#e8ecf4", "#8b97b0", "#ef4444"

# ── Categories ──
HIDDEN_CATEGORIES = [
    "All Hidden Structures",
    "Remote Ancient Ruins",
    "Isolated Monasteries & Temples",
    "Deserted Fortresses & Castles",
    "Extreme Outposts & Research",
    "Abandoned Industrial & Mining",
    "Isolated Lighthouses",
    "Mystery & Unexplained",
]

MODE_CONFIG = {
    "All Hidden Structures": {"color": "#ef4444", "icon": "globe", "desc": "All mapped isolated structures worldwide."},
    "Remote Ancient Ruins": {"color": "#f59e0b", "icon": "ruins", "desc": "Ancient cities, lost pyramids, and ruins far from modern civilization."},
    "Isolated Monasteries & Temples": {"color": "#a855f7", "icon": "temple", "desc": "Hermitages, cliffside monasteries, and remote spiritual sites."},
    "Deserted Fortresses & Castles": {"color": "#8b5cf6", "icon": "fortress", "desc": "Hidden castles, forts, and military holdouts in extreme terrain."},
    "Extreme Outposts & Research": {"color": "#10b981", "icon": "satellite", "desc": "Deep space tracking, polar stations, and the most remote human habitation."},
    "Abandoned Industrial & Mining": {"color": "#f97316", "icon": "industry", "desc": "Ghost towns, forgotten mines, and industrial relics reclaimed by nature."},
    "Isolated Lighthouses": {"color": "#3b82f6", "icon": "lighthouse", "desc": "Beacons on jagged lonely rocks surrounded by ocean."},
    "Mystery & Unexplained": {"color": "#ec4899", "icon": "question", "desc": "Peculiar structures, crop marks, and unidentified isolated anomalies."},
}

# ── Global Pre-Calculated Dataset (incl. Amazon & Congo) ──
GLOBAL_HIDDEN_DATA = [
    # Remote Ancient Ruins
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "cat": "Remote Ancient Ruins", "iso_km": 45, "country": "Peru", "desc": "Incan citadel set high in the Andes Mountains."},
    {"name": "Petra", "lat": 30.3285, "lon": 35.4444, "cat": "Remote Ancient Ruins", "iso_km": 30, "country": "Jordan", "desc": "Ancient capital carved into rose-red rock faces."},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "cat": "Remote Ancient Ruins", "iso_km": 15, "country": "Cambodia", "desc": "Massive temple complex swallowed by the jungle."},
    {"name": "Tikal", "lat": 17.2220, "lon": -89.6237, "cat": "Remote Ancient Ruins", "iso_km": 50, "country": "Guatemala", "desc": "Ancient Mayan citadel deep in the rainforest."},
    {"name": "Great Zimbabwe", "lat": -20.2675, "lon": 30.9333, "cat": "Remote Ancient Ruins", "iso_km": 25, "country": "Zimbabwe", "desc": "Ruined city in the south-eastern hills of Zimbabwe."},
    {"name": "Nan Madol", "lat": 6.8450, "lon": 158.3340, "cat": "Remote Ancient Ruins", "iso_km": 800, "country": "Micronesia", "desc": "Ruined city built on a coral reef, the 'Venice of the Pacific'."},
    {"name": "Borobudur", "lat": -7.6079, "lon": 110.2038, "cat": "Remote Ancient Ruins", "iso_km": 20, "country": "Indonesia", "desc": "World's largest Buddhist temple nestled in a remote valley."},
    {"name": "Ciudad Perdida", "lat": 11.0381, "lon": -73.9250, "cat": "Remote Ancient Ruins", "iso_km": 60, "country": "Colombia", "desc": "The 'Lost City' hidden high in the Sierra Nevada de Santa Marta."},
    {"name": "Kuelap Fortress", "lat": -6.4183, "lon": -77.9230, "cat": "Remote Ancient Ruins", "iso_km": 40, "country": "Peru", "desc": "Walled settlement built by the Chachapoyas in the high Andes."},

    # Isolated Monasteries & Temples
    {"name": "Paro Taktsang (Tiger's Nest)", "lat": 27.4919, "lon": 89.3620, "cat": "Isolated Monasteries & Temples", "iso_km": 12, "country": "Bhutan", "desc": "Himalayan Buddhist sacred site clinging to a cliff face."},
    {"name": "Meteora Monasteries", "lat": 39.7130, "lon": 21.6310, "cat": "Isolated Monasteries & Temples", "iso_km": 8, "country": "Greece", "desc": "Monasteries built on immense natural pillars and hill-like rounded boulders."},
    {"name": "Katskhi Pillar", "lat": 42.2877, "lon": 43.2157, "cat": "Isolated Monasteries & Temples", "iso_km": 15, "country": "Georgia", "desc": "Hermitage placed on top of a 130ft natural limestone monolith."},
    {"name": "Phugtal Monastery", "lat": 33.2644, "lon": 77.1725, "cat": "Isolated Monasteries & Temples", "iso_km": 80, "country": "India", "desc": "Monastery built into a cliff cave in the remote Zanskar region."},
    {"name": "Key Monastery", "lat": 32.2981, "lon": 78.0121, "cat": "Isolated Monasteries & Temples", "iso_km": 60, "country": "India", "desc": "Tibetan Buddhist monastery located at an altitude of 4,166m."},
    {"name": "Hanging Temple of Hengshan", "lat": 39.0658, "lon": 113.6703, "cat": "Isolated Monasteries & Temples", "iso_km": 25, "country": "China", "desc": "Temple built into a cliff 75 meters above the ground."},
    {"name": "Ostrog Monastery", "lat": 42.6750, "lon": 19.0300, "cat": "Isolated Monasteries & Temples", "iso_km": 20, "country": "Montenegro", "desc": "Serbian Orthodox monastery placed against an almost vertical background."},

    # Deserted Fortresses & Castles
    {"name": "Krak des Chevaliers", "lat": 34.7570, "lon": 36.2944, "cat": "Deserted Fortresses & Castles", "iso_km": 35, "country": "Syria", "desc": "Crusader castle situated on a strategic hilltop, severely isolated."},
    {"name": "Derawar Fort", "lat": 28.7678, "lon": 71.3340, "cat": "Deserted Fortresses & Castles", "iso_km": 40, "country": "Pakistan", "desc": "Massive square fortress rising out of the Cholistan Desert."},
    {"name": "Ghat of Kumbhalgarh", "lat": 25.1485, "lon": 73.5826, "cat": "Deserted Fortresses & Castles", "iso_km": 30, "country": "India", "desc": "Massive hill fort with extremely remote and continuous walls."},
    {"name": "Fortress of Guaita", "lat": 43.9351, "lon": 12.4503, "cat": "Deserted Fortresses & Castles", "iso_km": 5, "country": "San Marino", "desc": "Impregnable fortress on a high rocky peak."},
    {"name": "Spis Castle", "lat": 48.9998, "lon": 20.7681, "cat": "Deserted Fortresses & Castles", "iso_km": 10, "country": "Slovakia", "desc": "Vast castle ruins dominating the surrounding remote landscape."},

    # Extreme Outposts & Research (Including Amazon & Congo)
    {"name": "Amundsen-Scott South Pole Station", "lat": -90.0000, "lon": 0.0000, "cat": "Extreme Outposts & Research", "iso_km": 1300, "country": "Antarctica", "desc": "US scientific station at the geographic South Pole."},
    {"name": "Concordia Station", "lat": -75.1000, "lon": 123.3333, "cat": "Extreme Outposts & Research", "iso_km": 1000, "country": "Antarctica", "desc": "French-Italian research facility on the Antarctic Plateau."},
    {"name": "Vostok Station", "lat": -78.4644, "lon": 106.8373, "cat": "Extreme Outposts & Research", "iso_km": 1200, "country": "Antarctica", "desc": "Russian polar station, site of the lowest recorded temperature on Earth."},
    {"name": "Svalbard Global Seed Vault", "lat": 78.2356, "lon": 15.4913, "cat": "Extreme Outposts & Research", "iso_km": 800, "country": "Norway", "desc": "Secure seed bank located deep inside a mountain in the Arctic."},
    {"name": "Tristan da Cunha Settlement", "lat": -37.0676, "lon": -12.3115, "cat": "Extreme Outposts & Research", "iso_km": 2400, "country": "UK", "desc": "The most remote inhabited archipelago in the world."},
    {"name": "Alert Climate Station", "lat": 82.5018, "lon": -62.3281, "cat": "Extreme Outposts & Research", "iso_km": 800, "country": "Canada", "desc": "The northernmost permanently inhabited place in the world."},
    {"name": "Macmillan River Outpost", "lat": 63.2625, "lon": -132.8427, "cat": "Extreme Outposts & Research", "iso_km": 400, "country": "Canada", "desc": "Extreme isolation research and trap cabin in the Yukon wilderness."},
    {"name": "Oymyakon Station", "lat": 63.4608, "lon": 142.7738, "cat": "Extreme Outposts & Research", "iso_km": 300, "country": "Russia", "desc": "The coldest permanently inhabited settlement on Earth."},
    # Amazonian & Remote Forest Outposts
    {"name": "São Gabriel da Cachoeira Outpost", "lat": -0.1300, "lon": -67.0800, "cat": "Extreme Outposts & Research", "iso_km": 450, "country": "Brazil", "desc": "Deep Amazonian research and military outpost isolated by hundreds of kilometers of jungle."},
    {"name": "Yanomami Village (Demini)", "lat": 1.5430, "lon": -63.5010, "cat": "Extreme Outposts & Research", "iso_km": 300, "country": "Brazil", "desc": "Remote isolated indigenous communal dwelling deep in the Amazon."},
    {"name": "Salonga National Park Station", "lat": -2.0000, "lon": 21.0000, "cat": "Extreme Outposts & Research", "iso_km": 280, "country": "DR Congo", "desc": "Anti-poaching and ecological research station deep in the Congo rainforest."},
    {"name": "Jau National Park Base", "lat": -1.9000, "lon": -61.5000, "cat": "Extreme Outposts & Research", "iso_km": 200, "country": "Brazil", "desc": "Isolated base camp for one of the largest forest reserves in South America."},
    {"name": "Iquitos Jungle Lodge", "lat": -3.7500, "lon": -73.2500, "cat": "Extreme Outposts & Research", "iso_km": 150, "country": "Peru", "desc": "Lodge accessible only by multiple days of river travel in the Amazon."},
    {"name": "Ituri Forest Camp", "lat": 1.4000, "lon": 28.6000, "cat": "Extreme Outposts & Research", "iso_km": 180, "country": "DR Congo", "desc": "Mbuti research and observation camp hidden in the Ituri rainforest."},

    # Abandoned Industrial & Mining
    {"name": "Kolmanskop", "lat": -26.7011, "lon": 15.2217, "cat": "Abandoned Industrial & Mining", "iso_km": 15, "country": "Namibia", "desc": "Ghost town in the Namib desert, half buried in sand."},
    {"name": "Kennecott Copper Mine", "lat": 61.4851, "lon": -142.8860, "cat": "Abandoned Industrial & Mining", "iso_km": 120, "country": "USA", "desc": "Abandoned copper mining camp deep in the Alaskan wilderness."},
    {"name": "Bodie Ghost Town", "lat": 38.2122, "lon": -119.0111, "cat": "Abandoned Industrial & Mining", "iso_km": 40, "country": "USA", "desc": "Arrested decay gold-mining ghost town in California."},
    {"name": "Pyramiden", "lat": 78.6558, "lon": 16.3242, "cat": "Abandoned Industrial & Mining", "iso_km": 60, "country": "Norway", "desc": "Abandoned Soviet coal mining settlement in Svalbard."},
    {"name": "Hashima Island (Gunkanjima)", "lat": 32.6276, "lon": 129.7386, "cat": "Abandoned Industrial & Mining", "iso_km": 5, "country": "Japan", "desc": "Abandoned, concrete-covered island that formally housed miners."},
    {"name": "Fordlândia", "lat": -3.8315, "lon": -55.4952, "cat": "Abandoned Industrial & Mining", "iso_km": 150, "country": "Brazil", "desc": "Henry Ford's abandoned rubber plantation town deep in the Amazon rainforest."},

    # Isolated Lighthouses
    {"name": "Bell Rock Lighthouse", "lat": 56.4331, "lon": -2.3872, "cat": "Isolated Lighthouses", "iso_km": 18, "country": "UK", "desc": "World's oldest surviving sea-washed lighthouse."},
    {"name": "Phare de la Jument", "lat": 48.4262, "lon": -5.1325, "cat": "Isolated Lighthouses", "iso_km": 20, "country": "France", "desc": "Extreme lighthouse braving terrifying Atlantic storms in Brittany."},
    {"name": "Bishops Rock", "lat": 49.8732, "lon": -6.4444, "cat": "Isolated Lighthouses", "iso_km": 45, "country": "UK", "desc": "Smallest island in the world with a building on it (Guinness record)."},
    {"name": "Thridrangaviti Lighthouse", "lat": 63.2929, "lon": -20.3129, "cat": "Isolated Lighthouses", "iso_km": 25, "country": "Iceland", "desc": "Incredibly remote lighthouse built on top of a steep rock pillar in the ocean."},

    # Mystery & Unexplained
    {"name": "Nazca Lines", "lat": -14.7390, "lon": -75.1300, "cat": "Mystery & Unexplained", "iso_km": 40, "country": "Peru", "desc": "Gigantic geoglyphs in the desert, visible only from the air."},
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "cat": "Mystery & Unexplained", "iso_km": 15, "country": "UK", "desc": "Prehistoric stone circle monument spanning thousands of years."},
    {"name": "Moai of Easter Island", "lat": -27.1127, "lon": -109.3497, "cat": "Mystery & Unexplained", "iso_km": 3500, "country": "Chile", "desc": "Massive monolithic human figures carved by the Rapa Nui."},
    {"name": "Gobekli Tepe", "lat": 37.2232, "lon": 38.9224, "cat": "Mystery & Unexplained", "iso_km": 25, "country": "Turkey", "desc": "The world's oldest known megaliths, pre-dating agriculture."},
    {"name": "Marree Man", "lat": -29.5300, "lon": 137.4650, "cat": "Mystery & Unexplained", "iso_km": 60, "country": "Australia", "desc": "Massive 2.7 mile long modern geoglyph in the Outback of unknown origin."},
]

def _popup(f: dict) -> str:
    """Dark-themed popup for hidden structures."""
    name = html_module.escape(str(f["name"]))
    iso = f["iso_km"]
    desc = html_module.escape(str(f.get("desc", "")))
    cat = html_module.escape(str(f.get("cat", "")))
    country = html_module.escape(str(f.get("country", "")))
    color = MODE_CONFIG.get(cat, MODE_CONFIG["All Hidden Structures"])["color"]

    return f"""
    <div style='min-width:240px;background:{_CARD};color:{_TEXT};padding:12px;border-radius:8px;border:1px solid {color};'>
        <b style='color:{color}; font-size:1.1em;'>{name}</b><br>
        <span style='color:{_TEXT2};'>{(country)}</span><br><br>
        <span style='color:#fca5a5;font-weight:bold;'>Isolation Distance: ~{iso} km</span><br>
        <span style='color:{_TEXT2};'>Type: </span>{cat}<br>
        <br><span style='color:{_TEXT2};font-size:0.9em;'>{desc}</span><br>
        <span style='color:#5a6580;font-size:0.75em;'>{f['lat']:.5f}, {f['lon']:.5f}</span>
    </div>
    """

def _build_map(features: list, zoom: int = 2):
    """Build a global dark folium map with colored markers."""
    m = folium.Map(location=[20, 0], zoom_start=zoom, tiles="CartoDB dark_matter")
    for f in features:
        color = MODE_CONFIG.get(f["cat"], MODE_CONFIG["All Hidden Structures"])["color"]
        folium.CircleMarker(
            location=[f["lat"], f["lon"]],
            radius=6, color=color, fill=True, fill_color=color,
            fill_opacity=0.85, weight=1,
            popup=folium.Popup(_popup(f), max_width=320),
            tooltip=html_module.escape(str(f["name"])),
        ).add_to(m)
    return m

def render_hidden_structures_maps_tab():
    """Render the Global Hidden Structures tab."""
    st.markdown(
        f'<div class="tab-header pink"><h4>🏚️ Global Hidden Structures</h4>'
        f'<p>A worldwide map of the most remote, isolated, and mysterious structures — '
        f'from lost ancient cities to extreme outposts in the Amazon, Congo, and Antarctica.</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox("Structure Category", HIDDEN_CATEGORIES, key="hidden_mode")
    min_iso = st.slider(
        "Min Isolation (km)", 0, 1000, 0, 50, key="hidden_iso",
        help="Filter by how far the structure is from other major settlements/structures."
    )

    cfg = MODE_CONFIG[mode]
    st.markdown(
        f"<p style='color:{cfg['color']};'>{html_module.escape(cfg['desc'])}</p>",
        unsafe_allow_html=True,
    )

    features = [f for f in GLOBAL_HIDDEN_DATA if f["iso_km"] >= min_iso]
    if mode != "All Hidden Structures":
        features = [f for f in features if f["cat"] == mode]

    if not features:
        st.warning("No structures match these filters. Try reducing the isolation distance.")
        return

    st.markdown("---")
    st.markdown(
        f"<span style='color:{cfg['color']};font-weight:600;'>"
        f"● {html_module.escape(mode)} ({len(features)} locations)</span>",
        unsafe_allow_html=True,
    )

    m = _build_map(features)
    st_html(m._repr_html_(), height=550)

    st.markdown("#### 🏆 Most Isolated:")
    top_5 = sorted(features, key=lambda x: x["iso_km"], reverse=True)[:5]
    for i, f in enumerate(top_5):
        color = MODE_CONFIG.get(f["cat"])["color"]
        st.markdown(
            f'<div style="display:flex;align-items:center;margin:6px 0;background:{_CARD};border:1px solid {color};border-radius:8px;padding:8px;">'
            f'<span style="color:{color};font-weight:bold;font-size:1.2em;min-width:30px;text-align:center;">{i+1}</span>'
            f'<div style="margin-left:10px;">'
            f'<div style="color:{_TEXT};font-weight:600;">{html_module.escape(f["name"])} <span style="font-size:0.8em;color:{_TEXT2};">({html_module.escape(f["country"])})</span></div>'
            f'<div style="color:#fca5a5;font-size:0.85em;">Isolation: {f["iso_km"]} km</div>'
            f'<div style="color:{_TEXT2};font-size:0.8em; margin-top:2px;">{html_module.escape(f["desc"])}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    rows = [{"Name": f["name"], "Country": f["country"], "Category": f["cat"], "Isolation (km)": f["iso_km"], "Latitude": f["lat"], "Longitude": f["lon"], "Description": f["desc"]} for f in features]
    df = pd.DataFrame(rows)
    with st.expander(f"Full Data Table ({len(df)} structures)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    csv_buf = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Data (CSV)",
        data=csv_buf,
        file_name=f"global_hidden_structures_{mode.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="hidden_dl",
    )
