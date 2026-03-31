# -*- coding: utf-8 -*-
"""
Silk Road & Ancient Trade Explorer module for TerraScout AI.
Provides 10 curated map modes covering the Silk Road, maritime trade,
caravanserais, spice routes, the Amber Road, Incense Route, Trans-Saharan
trade, Bronze Age tin routes, Roman trade networks, and the modern Belt
& Road Initiative. All location data is hardcoded -- no API keys required.
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

# ═══════════════════════════════════════════════════════════════════════════════
# COLOUR PALETTE (TerraScout dark theme)
# ═══════════════════════════════════════════════════════════════════════════════
_BG = "#0a0e1a"
_SURFACE = "#111827"
_BORDER = "#2a3550"
_TEXT_PRI = "#e8ecf4"
_TEXT_SEC = "#8b97b0"
_ACCENT = "#06b6d4"

ROUTE_COLORS = {
    "land": "#f59e0b",
    "sea": "#06b6d4",
    "branch": "#8b5cf6",
    "spice": "#10b981",
    "amber": "#f97316",
    "incense": "#ec4899",
    "saharan": "#ef4444",
    "tin": "#3b82f6",
    "roman": "#a855f7",
    "belt_road": "#14b8a6",
}

CITY_COLORS = {
    "capital": "#ef4444",
    "major": "#f59e0b",
    "port": "#06b6d4",
    "oasis": "#10b981",
    "caravanserai": "#f97316",
    "market": "#ec4899",
    "mine": "#8b5cf6",
    "fortress": "#a855f7",
    "hub": "#14b8a6",
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _base_map(center=(35.0, 60.0), zoom=3):
    """Return a Folium map with CartoDB dark_matter tiles."""
    m = folium.Map(location=list(center), zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark Matter",
        name="Dark Base",
    ).add_to(m)
    return m


def _stats_row(metrics: dict):
    """Display a row of st.metric cards."""
    cols = st.columns(min(len(metrics), 5))
    for i, (label, value) in enumerate(metrics.items()):
        cols[i % len(cols)].metric(label, value)


def _popup_html(title: str, fields: dict, max_width: int = 260) -> str:
    """Build a dark-themed popup HTML snippet."""
    body = f"<div style='max-width:{max_width}px;font-family:sans-serif;'>"
    body += f"<strong style='font-size:0.95rem;'>{html_module.escape(title)}</strong><br/>"
    for k, v in fields.items():
        body += (
            f"<span style='font-size:0.78rem;color:#aaa;'>{html_module.escape(str(k))}:</span> "
            f"<span style='font-size:0.78rem;'>{html_module.escape(str(v))}</span><br/>"
        )
    body += "</div>"
    return body


def _table_and_download(df: pd.DataFrame, label: str, filename: str, key: str):
    """Show an expandable dataframe table and a CSV download button."""
    with st.expander(f"Full Data Table ({len(df)} {label})", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} {label} (CSV)",
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def _add_markers(m, locations, color, radius=7):
    """Add CircleMarkers to a folium map from a list of location dicts."""
    for loc in locations:
        fields = {k: v for k, v in loc.items() if k not in ("name", "lat", "lon")}
        popup = folium.Popup(
            _popup_html(loc["name"], fields),
            max_width=280,
        )
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)


def _add_route_line(m, locations, color, tooltip_text="Route"):
    """Draw a PolyLine through a sequence of locations."""
    coords = [[loc["lat"], loc["lon"]] for loc in locations]
    folium.PolyLine(
        coords, color=color, weight=4, opacity=0.85,
        tooltip=html_module.escape(tooltip_text),
    ).add_to(m)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CLASSIC SILK ROAD CITIES
# ═══════════════════════════════════════════════════════════════════════════════
CLASSIC_SILK_ROAD = [
    {"name": "Xi'an (Chang'an)", "lat": 34.26, "lon": 108.94, "type": "capital", "period": "206 BCE onwards", "note": "Eastern terminus; Tang Dynasty capital; start of the Silk Road"},
    {"name": "Lanzhou", "lat": 36.06, "lon": 103.83, "type": "major", "period": "Han Dynasty", "note": "Yellow River crossing; gateway to Hexi Corridor"},
    {"name": "Wuwei (Liangzhou)", "lat": 37.87, "lon": 101.78, "type": "major", "period": "Han Dynasty", "note": "Flying Horse of Gansu discovered here; Hexi Corridor hub"},
    {"name": "Zhangye (Ganzhou)", "lat": 38.93, "lon": 100.45, "type": "oasis", "period": "Han Dynasty", "note": "Marco Polo stayed 1 year; Danxia rainbow mountains nearby"},
    {"name": "Dunhuang", "lat": 40.14, "lon": 94.66, "type": "oasis", "period": "111 BCE onwards", "note": "Mogao Caves with 492 grottoes; gateway to Taklamakan Desert"},
    {"name": "Turpan", "lat": 42.95, "lon": 89.18, "type": "oasis", "period": "2nd century BCE", "note": "Lowest point in China (-154m); Flaming Mountains; Gaochang ruins"},
    {"name": "Kashgar", "lat": 39.47, "lon": 75.99, "type": "market", "period": "2nd century BCE", "note": "Sunday market for 2000 years; meeting of northern and southern routes"},
    {"name": "Samarkand", "lat": 39.65, "lon": 66.96, "type": "capital", "period": "700 BCE", "note": "Registan Square; Timurid capital; papermaking reached West here"},
    {"name": "Bukhara", "lat": 39.77, "lon": 64.42, "type": "major", "period": "500 BCE", "note": "Centre of Islamic scholarship; Ark Fortress; 140+ architectural monuments"},
    {"name": "Khiva", "lat": 41.38, "lon": 60.36, "type": "major", "period": "6th century", "note": "Ichan Kala inner walled city; last slave market in Central Asia"},
    {"name": "Merv (Mary)", "lat": 37.66, "lon": 62.17, "type": "oasis", "period": "3rd millennium BCE", "note": "Once largest city in world; destroyed by Mongols 1221; UNESCO site"},
    {"name": "Tehran", "lat": 35.69, "lon": 51.39, "type": "capital", "period": "Medieval", "note": "Crossroads of Silk Road branches; bazaars and caravanserais"},
    {"name": "Tabriz", "lat": 38.08, "lon": 46.29, "type": "market", "period": "1500 BCE", "note": "Grand Bazaar UNESCO site; key trading point for silk and carpets"},
    {"name": "Baghdad", "lat": 33.31, "lon": 44.37, "type": "capital", "period": "762 CE", "note": "Abbasid capital; House of Wisdom; major trade hub"},
    {"name": "Damascus", "lat": 33.51, "lon": 36.29, "type": "capital", "period": "3000 BCE", "note": "Oldest continuously inhabited city; Umayyad Mosque; souks"},
    {"name": "Aleppo", "lat": 36.20, "lon": 37.16, "type": "market", "period": "5000 BCE", "note": "Ancient souks; citadel; crossroads of trade routes"},
    {"name": "Palmyra", "lat": 34.55, "lon": 38.27, "type": "oasis", "period": "2nd millennium BCE", "note": "Desert oasis caravan city; Roman colonnaded streets; Zenobia"},
    {"name": "Antioch (Antakya)", "lat": 36.20, "lon": 36.16, "type": "major", "period": "300 BCE", "note": "Seleucid capital; terminus of overland eastern routes"},
    {"name": "Constantinople (Istanbul)", "lat": 41.01, "lon": 28.98, "type": "capital", "period": "330 CE", "note": "Western terminus; Grand Bazaar; bridge between Europe and Asia"},
    {"name": "Tashkent", "lat": 41.30, "lon": 69.28, "type": "major", "period": "2nd century BCE", "note": "Major Silk Road oasis; Chorsu Bazaar; modern Uzbekistan capital"},
    {"name": "Balkh", "lat": 36.76, "lon": 66.90, "type": "major", "period": "1500 BCE", "note": "Mother of Cities; Zoroastrian holy site; conquered by Alexander"},
    {"name": "Herat", "lat": 34.35, "lon": 62.20, "type": "major", "period": "600 BCE", "note": "Timurid cultural centre; citadel of Alexander; Friday Mosque"},
    {"name": "Taxila", "lat": 33.75, "lon": 72.83, "type": "major", "period": "600 BCE", "note": "Gandhara Buddhist centre; university city; UNESCO World Heritage"},
    {"name": "Khotan (Hotan)", "lat": 37.11, "lon": 79.93, "type": "oasis", "period": "3rd century BCE", "note": "Southern Silk Road jade centre; Buddhist kingdom"},
    {"name": "Yarkand", "lat": 38.42, "lon": 77.27, "type": "oasis", "period": "2nd century BCE", "note": "Southern route oasis; music and arts centre; Yarkand Khanate"},
    {"name": "Kucha", "lat": 41.73, "lon": 82.94, "type": "oasis", "period": "2nd century BCE", "note": "Kizil Caves Buddhist art; northern route oasis kingdom"},
    {"name": "Tyre", "lat": 33.27, "lon": 35.20, "type": "port", "period": "2750 BCE", "note": "Phoenician port; Tyrian purple dye; Alexander's siege causeway"},
    {"name": "Petra", "lat": 30.33, "lon": 35.44, "type": "major", "period": "4th century BCE", "note": "Nabataean rock-cut city; incense and spice trade crossroads"},
    {"name": "Dura-Europos", "lat": 34.75, "lon": 40.73, "type": "fortress", "period": "303 BCE", "note": "Fortress city on Euphrates; earliest Christian church; multicultural"},
    {"name": "Ctesiphon", "lat": 33.09, "lon": 44.58, "type": "capital", "period": "120 BCE", "note": "Parthian and Sasanian capital; Taq Kasra arch; trade depot"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 2. MARITIME SILK ROAD PORTS
# ═══════════════════════════════════════════════════════════════════════════════
MARITIME_PORTS = [
    {"name": "Guangzhou (Canton)", "lat": 23.13, "lon": 113.26, "country": "China", "period": "3rd century BCE", "note": "Primary Chinese maritime trade port; Arab and Indian merchants"},
    {"name": "Quanzhou (Zayton)", "lat": 24.87, "lon": 118.68, "country": "China", "period": "Tang Dynasty", "note": "Largest port in medieval world; Marco Polo's departure point"},
    {"name": "Fuzhou", "lat": 26.07, "lon": 119.30, "country": "China", "period": "Tang Dynasty", "note": "Major shipbuilding centre; tea export port"},
    {"name": "Malacca", "lat": 2.20, "lon": 102.25, "country": "Malaysia", "period": "1400 CE", "note": "Strategic strait control; Malay sultanate; spice entrepot"},
    {"name": "Calicut (Kozhikode)", "lat": 11.25, "lon": 75.77, "country": "India", "period": "Ancient", "note": "Spice capital; Vasco da Gama landed 1498; pepper trade"},
    {"name": "Muscat", "lat": 23.59, "lon": 58.54, "country": "Oman", "period": "Ancient", "note": "Persian Gulf trade hub; frankincense export; dhow building"},
    {"name": "Aden", "lat": 12.79, "lon": 45.04, "country": "Yemen", "period": "5th century BCE", "note": "Red Sea gateway; mentioned by Ezekiel; monsoon trade winds hub"},
    {"name": "Kilwa Kisiwani", "lat": -8.96, "lon": 39.52, "country": "Tanzania", "period": "9th century", "note": "Richest Swahili coast city; gold and ivory trade; Great Mosque"},
    {"name": "Mogadishu", "lat": 2.05, "lon": 45.34, "country": "Somalia", "period": "10th century", "note": "Swahili trade city; Ibn Battuta visited 1331; cloth and gold"},
    {"name": "Hormuz", "lat": 27.08, "lon": 56.46, "country": "Iran", "period": "Ancient", "note": "Persian Gulf strait; spice and silk distribution; Marco Polo visited"},
    {"name": "Basra", "lat": 30.51, "lon": 47.78, "country": "Iraq", "period": "636 CE", "note": "Sindbad's legendary home port; Tigris-Euphrates delta; pearl trade"},
    {"name": "Jeddah", "lat": 21.49, "lon": 39.19, "country": "Saudi Arabia", "period": "Ancient", "note": "Red Sea pilgrimage and trade port; gateway to Mecca"},
    {"name": "Alexandria", "lat": 31.20, "lon": 29.92, "country": "Egypt", "period": "331 BCE", "note": "Lighthouse (Pharos); library; Roman grain and spice hub"},
    {"name": "Berenice", "lat": 23.95, "lon": 35.48, "country": "Egypt", "period": "275 BCE", "note": "Red Sea Roman trade port; pepper imports from India"},
    {"name": "Adulis", "lat": 15.38, "lon": 39.67, "country": "Eritrea", "period": "5th century BCE", "note": "Aksumite Empire port; ivory and gold export to Rome"},
    {"name": "Srivijaya (Palembang)", "lat": -2.99, "lon": 104.76, "country": "Indonesia", "period": "7th century", "note": "Maritime empire controlling Malacca Strait; Buddhist centre"},
    {"name": "Champa (Hoi An)", "lat": 15.88, "lon": 108.33, "country": "Vietnam", "period": "2nd century", "note": "Cham kingdom port; Japanese merchant quarter; silk and porcelain"},
    {"name": "Nagapattinam", "lat": 10.77, "lon": 79.84, "country": "India", "period": "Ancient", "note": "Chola Dynasty port; Chinese Buddhist pilgrimage site"},
    {"name": "Goa", "lat": 15.50, "lon": 73.83, "country": "India", "period": "3rd century BCE", "note": "Portuguese colonial port 1510; spice trade gateway"},
    {"name": "Siraf", "lat": 27.67, "lon": 52.35, "country": "Iran", "period": "7th century", "note": "Richest Persian Gulf port before Hormuz; Chinese ceramics found"},
    {"name": "Socotra", "lat": 12.50, "lon": 54.00, "country": "Yemen", "period": "Ancient", "note": "Indian Ocean waypoint; dragon blood tree; aloe trade"},
    {"name": "Zanzibar", "lat": -6.17, "lon": 39.19, "country": "Tanzania", "period": "10th century", "note": "Clove island; Swahili trading emporium; Stone Town"},
    {"name": "Sofala", "lat": -20.15, "lon": 34.72, "country": "Mozambique", "period": "10th century", "note": "Southern African gold export port; Great Zimbabwe connection"},
    {"name": "Arikamedu", "lat": 11.90, "lon": 79.83, "country": "India", "period": "2nd century BCE", "note": "Roman trading post near Pondicherry; beads and pottery found"},
    {"name": "Mantai", "lat": 8.87, "lon": 79.82, "country": "Sri Lanka", "period": "Ancient", "note": "Sri Lankan trade port; gems, cinnamon, and pearls"},
    {"name": "Hangzhou", "lat": 30.27, "lon": 120.15, "country": "China", "period": "Song Dynasty", "note": "Marco Polo's finest city; southern Song capital; silk centre"},
    {"name": "Ningbo", "lat": 29.87, "lon": 121.55, "country": "China", "period": "Tang Dynasty", "note": "Major Chinese maritime trade port; ceramics export hub"},
    {"name": "Dhofar (Salalah)", "lat": 17.02, "lon": 54.09, "country": "Oman", "period": "Ancient", "note": "Frankincense production heartland; Land of Frankincense UNESCO site"},
    {"name": "Cochin (Kochi)", "lat": 9.97, "lon": 76.27, "country": "India", "period": "Ancient", "note": "Queen of the Arabian Sea; Jewish traders; Portuguese spice trade"},
    {"name": "Broach (Bharuch)", "lat": 21.71, "lon": 73.00, "country": "India", "period": "Ancient", "note": "Periplus mentions as Barygaza; major Roman-Indian trade port"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 3. CARAVANSERAI & REST STOPS
# ═══════════════════════════════════════════════════════════════════════════════
CARAVANSERAIS = [
    {"name": "Sultan Han (Aksaray)", "lat": 38.49, "lon": 33.55, "country": "Turkey", "built": "1229 CE", "note": "Largest Seljuk caravanserai; ornate portal; 3900 sq.m; UNESCO tentative"},
    {"name": "Agzikarahan", "lat": 38.57, "lon": 34.52, "country": "Turkey", "built": "1231 CE", "note": "Well-preserved Seljuk han; relief carvings; Cappadocia route"},
    {"name": "Zein-o-Din Caravanserai", "lat": 32.38, "lon": 54.31, "country": "Iran", "built": "16th century", "note": "Round caravanserai; now a hotel; Yazd-Kerman route"},
    {"name": "Shah Abbasi Caravanserai (Meybod)", "lat": 32.25, "lon": 54.02, "country": "Iran", "built": "1602 CE", "note": "Safavid era; Meybod citadel complex; restored as hotel"},
    {"name": "Robat-e Sharaf", "lat": 36.40, "lon": 59.71, "country": "Iran", "built": "1114 CE", "note": "Double caravanserai; finest Seljuk brick architecture; Khorasan road"},
    {"name": "Tash Rabat", "lat": 40.84, "lon": 75.52, "country": "Kyrgyzstan", "built": "15th century", "note": "Stone caravanserai at 3500m altitude; Torugart Pass route to China"},
    {"name": "Sarihan (Avanos)", "lat": 38.72, "lon": 34.83, "country": "Turkey", "built": "1249 CE", "note": "Seljuk han; now hosts Whirling Dervish ceremonies; Cappadocia"},
    {"name": "Daulatabad Caravanserai", "lat": 19.94, "lon": 75.22, "country": "India", "built": "14th century", "note": "Deccan Plateau way station; near Ellora and Ajanta caves"},
    {"name": "Shaki Caravanserai", "lat": 41.19, "lon": 47.17, "country": "Azerbaijan", "built": "18th century", "note": "Two-storey trading han; now hotel; Caucasus silk route"},
    {"name": "Multani Caravanserai (Baku)", "lat": 40.37, "lon": 49.84, "country": "Azerbaijan", "built": "15th century", "note": "Old City merchants' lodge; Indian traders from Multan"},
    {"name": "Burana Tower Complex", "lat": 42.75, "lon": 75.25, "country": "Kyrgyzstan", "built": "11th century", "note": "Karakhanid minaret; Balasagun Silk Road city remains"},
    {"name": "Nokhur Caravanserai", "lat": 38.35, "lon": 56.62, "country": "Turkmenistan", "built": "12th century", "note": "Seljuk-era rest stop; Khorasan-Khiva route; desert waypoint"},
    {"name": "Qasr al-Kharana", "lat": 31.73, "lon": 36.46, "country": "Jordan", "built": "8th century", "note": "Umayyad desert castle/caravanserai; eastern Jordan steppe"},
    {"name": "Khan al-Umdan", "lat": 32.92, "lon": 35.07, "country": "Israel", "built": "1784 CE", "note": "Ottoman caravanserai in Acre; clock tower; merchant accommodation"},
    {"name": "Sultanhanli", "lat": 38.25, "lon": 33.54, "country": "Turkey", "built": "1232 CE", "note": "Konya-Aksaray road; monumental entrance; Seljuk sultan Alaeddin"},
    {"name": "Alay Han", "lat": 39.07, "lon": 38.80, "country": "Turkey", "built": "13th century", "note": "Eastern Anatolian route; fortified rest stop"},
    {"name": "Ribat-i Mahi", "lat": 35.93, "lon": 58.82, "country": "Iran", "built": "12th century", "note": "Khorasan route fortified inn; fish-shaped plan"},
    {"name": "Caravanserai of Sa'd al-Saltaneh", "lat": 36.25, "lon": 50.00, "country": "Iran", "built": "Qajar era", "note": "Largest urban caravanserai in Iran; now Qazvin bazaar complex"},
    {"name": "Han el-Ba'rur", "lat": 37.01, "lon": 39.02, "country": "Turkey", "built": "1128 CE", "note": "Hexagonal-plan Artukid caravanserai; unique architecture; Harran road"},
    {"name": "Hekim Han", "lat": 38.82, "lon": 37.93, "country": "Turkey", "built": "1218 CE", "note": "Seljuk caravanserai; Sivas-Malatya road; doctor's han"},
    {"name": "Obruk Han", "lat": 38.12, "lon": 33.05, "country": "Turkey", "built": "1210 CE", "note": "Near Obruk sinkhole lake; Konya road; Seljuk architecture"},
    {"name": "Aksaray Sultan Han", "lat": 38.32, "lon": 34.04, "country": "Turkey", "built": "1229 CE", "note": "Second Sultan Han; Kayseri-Aksaray road; open and closed sections"},
    {"name": "Mama Khatun Caravanserai", "lat": 39.91, "lon": 40.29, "country": "Turkey", "built": "1191 CE", "note": "Saltukid circular caravanserai; Tercan; unique octagonal tomb"},
    {"name": "Kiziloren Han", "lat": 37.87, "lon": 32.48, "country": "Turkey", "built": "1206 CE", "note": "First Seljuk caravanserai; Konya outskirts; modest but historic"},
    {"name": "Shahrestan Bridge Caravanserai", "lat": 32.63, "lon": 51.76, "country": "Iran", "built": "Safavid era", "note": "Near Isfahan; Zayandeh River bridge complex; royal road"},
    {"name": "Deyr-e Gachin", "lat": 35.20, "lon": 51.75, "country": "Iran", "built": "Sasanian era", "note": "Oldest caravanserai in Iran; desert south of Tehran; 3rd century"},
    {"name": "Pasargadae Caravanserai", "lat": 30.19, "lon": 53.17, "country": "Iran", "built": "Safavid era", "note": "Near Cyrus the Great's tomb; royal road rest stop"},
    {"name": "Izadkhast Caravanserai", "lat": 31.52, "lon": 51.79, "country": "Iran", "built": "Safavid era", "note": "Cliff-top castle and caravanserai; Isfahan-Shiraz road"},
    {"name": "Toki-Zargaron", "lat": 39.77, "lon": 64.42, "country": "Uzbekistan", "built": "16th century", "note": "Covered bazaar/caravanserai in Bukhara; jewellers' dome"},
    {"name": "Tim Abdulla Khan", "lat": 39.77, "lon": 64.42, "country": "Uzbekistan", "built": "1577 CE", "note": "Silk merchants' caravanserai; Bukhara's covered market"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 4. SPICE TRADE ROUTES
# ═══════════════════════════════════════════════════════════════════════════════
SPICE_TRADE = [
    {"name": "Kozhikode (Calicut)", "lat": 11.25, "lon": 75.77, "region": "India", "spices": "Pepper, Cardamom, Ginger", "note": "Pepper capital of the world; Zamorin rulers; Vasco da Gama 1498"},
    {"name": "Kochi (Cochin)", "lat": 9.97, "lon": 76.27, "region": "India", "spices": "Pepper, Cloves, Cinnamon", "note": "Queen of Arabian Sea; Jewish and Chinese traders; Portuguese base"},
    {"name": "Maluku Islands (Ternate)", "lat": 0.79, "lon": 127.38, "region": "Indonesia", "spices": "Cloves, Nutmeg", "note": "Original Spice Islands; clove monopoly; Portuguese fort 1522"},
    {"name": "Banda Islands", "lat": -4.52, "lon": 129.89, "region": "Indonesia", "spices": "Nutmeg, Mace", "note": "Only source of nutmeg until 19th century; VOC massacre 1621"},
    {"name": "Galle", "lat": 6.03, "lon": 80.22, "region": "Sri Lanka", "spices": "Cinnamon, Cardamom", "note": "Sri Lankan spice port; Dutch fort; cinnamon gardens"},
    {"name": "Zanzibar (Stone Town)", "lat": -6.17, "lon": 39.19, "region": "Tanzania", "spices": "Cloves, Vanilla, Cardamom", "note": "Spice Island; Omani sultans; clove plantations"},
    {"name": "Aden", "lat": 12.79, "lon": 45.04, "region": "Yemen", "spices": "Frankincense, Myrrh", "note": "Red Sea spice entrepot; monsoon trade winds hub"},
    {"name": "Venice", "lat": 45.44, "lon": 12.34, "region": "Italy", "spices": "All Eastern spices", "note": "European spice monopoly; Rialto Market; Marco Polo"},
    {"name": "Genoa", "lat": 44.41, "lon": 8.93, "region": "Italy", "spices": "All Eastern spices", "note": "Rival of Venice; Black Sea and Levant trade routes"},
    {"name": "Lisbon", "lat": 38.72, "lon": -9.14, "region": "Portugal", "spices": "Pepper, Cinnamon, Ginger", "note": "Broke Venetian monopoly; Cape route to India; Casa da India"},
    {"name": "Amsterdam", "lat": 52.37, "lon": 4.90, "region": "Netherlands", "spices": "Nutmeg, Cloves, Pepper", "note": "VOC headquarters; Dutch East India Company; spice warehouse"},
    {"name": "Mocha", "lat": 13.32, "lon": 43.25, "region": "Yemen", "spices": "Coffee, Myrrh", "note": "Coffee trade origin port; name gave 'mocha' to the world"},
    {"name": "Muscat", "lat": 23.59, "lon": 58.54, "region": "Oman", "spices": "Frankincense, Myrrh", "note": "Persian Gulf spice entrepot; dhow trade fleet"},
    {"name": "Cairo", "lat": 30.04, "lon": 31.24, "region": "Egypt", "spices": "All Eastern spices", "note": "Khan el-Khalili bazaar; Mamluk spice trade control; distribution hub"},
    {"name": "Constantinople (Istanbul)", "lat": 41.01, "lon": 28.98, "region": "Turkey", "spices": "All Eastern spices", "note": "Spice Bazaar (Misir Carsisi) built 1660; East-West gateway"},
    {"name": "Kollam (Quilon)", "lat": 8.89, "lon": 76.60, "region": "India", "spices": "Pepper, Cashew", "note": "Oldest spice trade port of Kerala; Chinese and Arab merchants"},
    {"name": "Surat", "lat": 21.17, "lon": 72.83, "region": "India", "spices": "Pepper, Opium, Textiles", "note": "Mughal port; English and Dutch factories; pilgrim port"},
    {"name": "Hormuz Island", "lat": 27.06, "lon": 56.46, "region": "Iran", "spices": "All Eastern spices", "note": "Strait controller; Portuguese fortress 1515; spice transshipment"},
    {"name": "Colombo", "lat": 6.93, "lon": 79.85, "region": "Sri Lanka", "spices": "Cinnamon, Pepper", "note": "Portuguese then Dutch colonial spice port; cinnamon trade"},
    {"name": "Antwerp", "lat": 51.22, "lon": 4.40, "region": "Belgium", "spices": "All Eastern spices", "note": "16th century spice distribution for Northern Europe"},
    {"name": "Seville", "lat": 37.39, "lon": -5.98, "region": "Spain", "spices": "New World spices", "note": "Casa de Contratacion; vanilla, chilli from Americas; treasure fleet"},
    {"name": "Aceh (Banda Aceh)", "lat": 5.55, "lon": 95.32, "region": "Indonesia", "spices": "Pepper, Betel", "note": "Gateway to Malacca Strait; Sultanate of Aceh; pepper king"},
    {"name": "Kannur (Cannanore)", "lat": 11.87, "lon": 75.37, "region": "India", "spices": "Pepper, Cardamom", "note": "Malabar Coast spice port; Portuguese St. Angelo Fort"},
    {"name": "Mangalore", "lat": 12.87, "lon": 74.88, "region": "India", "spices": "Pepper, Cashew, Cardamom", "note": "Arabian Sea spice trade port; Alupe and Portuguese connections"},
    {"name": "Goa (Old Goa)", "lat": 15.50, "lon": 73.91, "region": "India", "spices": "Pepper, Cloves, Cinnamon", "note": "Portuguese Estado da India capital; spice trade control"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 5. AMBER ROAD OF EUROPE
# ═══════════════════════════════════════════════════════════════════════════════
AMBER_ROAD = [
    {"name": "Kaliningrad (Konigsberg)", "lat": 54.71, "lon": 20.51, "country": "Russia", "role": "Source", "note": "Baltic amber capital; 90% of world amber deposits; Amber Room origin"},
    {"name": "Gdansk (Danzig)", "lat": 54.35, "lon": 18.65, "country": "Poland", "role": "Source/Port", "note": "Major Baltic amber port; Amber Museum in prison tower; Hanseatic"},
    {"name": "Elblag", "lat": 54.15, "lon": 19.40, "country": "Poland", "role": "Trading Post", "note": "Vistula Lagoon amber collection point; Teutonic Knights trade"},
    {"name": "Torun", "lat": 53.01, "lon": 18.61, "country": "Poland", "role": "Trading Post", "note": "Vistula River crossing; Copernicus birthplace; gingerbread and amber"},
    {"name": "Wroclaw (Breslau)", "lat": 51.11, "lon": 17.04, "country": "Poland", "role": "Trading Hub", "note": "Oder River junction; Silesian amber workshops; medieval trade fair"},
    {"name": "Prague", "lat": 50.08, "lon": 14.44, "country": "Czech Republic", "role": "Trading Hub", "note": "Bohemian crossroads; amber jewellery workshops; Vltava trade"},
    {"name": "Brno", "lat": 49.20, "lon": 16.61, "country": "Czech Republic", "role": "Waypoint", "note": "Moravian Gate corridor; ancient amber finds in archaeological digs"},
    {"name": "Vienna", "lat": 48.21, "lon": 16.37, "country": "Austria", "role": "Trading Hub", "note": "Danube crossroads; Roman Vindobona amber workshops"},
    {"name": "Bratislava", "lat": 48.15, "lon": 17.11, "country": "Slovakia", "role": "Waypoint", "note": "Danube crossing; Celtic and Roman amber route station"},
    {"name": "Budapest", "lat": 47.50, "lon": 19.04, "country": "Hungary", "role": "Trading Hub", "note": "Danube hub; Aquincum Roman amber market; Hungarian plain crossing"},
    {"name": "Sopron", "lat": 47.69, "lon": 16.59, "country": "Hungary", "role": "Waypoint", "note": "Roman Scarbantia; Amber Road milestone found here; border crossing"},
    {"name": "Graz", "lat": 47.07, "lon": 15.44, "country": "Austria", "role": "Waypoint", "note": "Mur River valley route; Celtic amber artifacts found"},
    {"name": "Ptuj", "lat": 46.42, "lon": 15.87, "country": "Slovenia", "role": "Waypoint", "note": "Roman Poetovio; oldest Slovenian town; Amber Road station"},
    {"name": "Ljubljana", "lat": 46.06, "lon": 14.51, "country": "Slovenia", "role": "Trading Hub", "note": "Roman Emona; amber found in pile dwellings; Julian Alps gateway"},
    {"name": "Carnuntum", "lat": 48.11, "lon": 16.86, "country": "Austria", "role": "Major Station", "note": "Roman legionary camp; key Amber Road junction; amphitheatre"},
    {"name": "Aquileia", "lat": 45.77, "lon": 13.37, "country": "Italy", "role": "Major Hub", "note": "Roman amber-working capital; 2nd largest Italian city; port"},
    {"name": "Venice", "lat": 45.44, "lon": 12.34, "country": "Italy", "role": "Distribution", "note": "Medieval amber distribution; murano glass with amber trade"},
    {"name": "Ravenna", "lat": 44.42, "lon": 12.20, "country": "Italy", "role": "Waypoint", "note": "Roman and Byzantine capital; amber in mosaics and jewellery"},
    {"name": "Rome", "lat": 41.90, "lon": 12.50, "country": "Italy", "role": "Destination", "note": "Ultimate destination; gladiator amber amulets; Nero collected amber"},
    {"name": "Trieste", "lat": 45.65, "lon": 13.78, "country": "Italy", "role": "Port", "note": "Adriatic port on Amber Road; Roman Tergeste; amber transshipment"},
    {"name": "Kaunas", "lat": 54.90, "lon": 23.90, "country": "Lithuania", "role": "Source Area", "note": "Lithuanian amber coast access; Nemunas River route"},
    {"name": "Liepaja", "lat": 56.51, "lon": 21.01, "country": "Latvia", "role": "Source Area", "note": "Baltic amber coast; Latvian amber jewellery tradition"},
    {"name": "Samland Peninsula", "lat": 54.86, "lon": 20.18, "country": "Russia", "role": "Source", "note": "Richest amber deposits on Earth; Yantarny open-pit mine"},
    {"name": "Passau", "lat": 48.57, "lon": 13.46, "country": "Germany", "role": "Waypoint", "note": "Three rivers confluence; Inn/Danube junction; amber route crossing"},
    {"name": "Salzburg", "lat": 47.80, "lon": 13.04, "country": "Austria", "role": "Waypoint", "note": "Alpine salt and amber trade; Hallstatt culture connection"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 6. INCENSE ROUTE OF ARABIA
# ═══════════════════════════════════════════════════════════════════════════════
INCENSE_ROUTE = [
    {"name": "Dhofar (Salalah)", "lat": 17.02, "lon": 54.09, "country": "Oman", "role": "Source", "note": "Frankincense production heartland; Boswellia sacra trees; UNESCO"},
    {"name": "Shabwa", "lat": 15.36, "lon": 47.02, "country": "Yemen", "role": "Capital", "note": "Hadhramaut kingdom capital; incense collecting point"},
    {"name": "Marib", "lat": 15.46, "lon": 45.35, "country": "Yemen", "role": "Capital", "note": "Sabaean capital; Great Dam of Marib; Queen of Sheba legend"},
    {"name": "Timna (Yemen)", "lat": 14.76, "lon": 46.10, "country": "Yemen", "role": "Capital", "note": "Qatabanian kingdom capital; incense route junction"},
    {"name": "Najran", "lat": 17.49, "lon": 44.13, "country": "Saudi Arabia", "role": "Waypoint", "note": "Yemen-Arabia border crossing; early Christian community"},
    {"name": "Yathrib (Medina)", "lat": 24.47, "lon": 39.61, "country": "Saudi Arabia", "role": "Waypoint", "note": "Pre-Islamic trade stop; oasis settlement; later Holy City"},
    {"name": "Dedan (Al-Ula)", "lat": 26.62, "lon": 37.92, "country": "Saudi Arabia", "role": "Trading Post", "note": "Lihyanite and Dedanite kingdoms; rock-cut tombs; Hegra nearby"},
    {"name": "Hegra (Mada'in Saleh)", "lat": 26.79, "lon": 37.95, "country": "Saudi Arabia", "role": "Nabataean City", "note": "Southern Nabataean capital; 131 rock-cut tombs; UNESCO site"},
    {"name": "Petra", "lat": 30.33, "lon": 35.44, "country": "Jordan", "role": "Capital", "note": "Nabataean capital; controlled incense trade; Treasury and Siq"},
    {"name": "Gaza", "lat": 31.50, "lon": 34.47, "country": "Palestine", "role": "Port/Terminus", "note": "Mediterranean terminus; incense shipped to Greece and Rome"},
    {"name": "Avdat (Oboda)", "lat": 30.79, "lon": 34.77, "country": "Israel", "role": "Nabataean City", "note": "Negev Desert caravan city; wine production; UNESCO site"},
    {"name": "Mamshit", "lat": 31.03, "lon": 35.06, "country": "Israel", "role": "Nabataean City", "note": "Wealthiest Negev city; horse stables; mosaics; UNESCO"},
    {"name": "Shivta", "lat": 30.88, "lon": 34.63, "country": "Israel", "role": "Nabataean City", "note": "Negev farming town; Byzantine churches; water systems; UNESCO"},
    {"name": "Haluza (Elusa)", "lat": 31.09, "lon": 34.67, "country": "Israel", "role": "Nabataean City", "note": "Largest Negev Nabataean city; theatre; wine trade"},
    {"name": "Gerrha", "lat": 25.38, "lon": 49.96, "country": "Saudi Arabia", "role": "Port", "note": "Arabian Gulf port; pearl and incense trade; enormous wealth"},
    {"name": "Qana (Bir Ali)", "lat": 13.97, "lon": 48.33, "country": "Yemen", "role": "Port", "note": "Hadhramaut incense export port; Indian Ocean trade"},
    {"name": "Sumhuram (Khor Rori)", "lat": 17.04, "lon": 54.44, "country": "Oman", "role": "Port", "note": "Frankincense export harbour; archaeological park; Land of Frankincense"},
    {"name": "Adulis", "lat": 15.38, "lon": 39.67, "country": "Eritrea", "role": "Port", "note": "Aksumite Empire port; myrrh and incense redistribution"},
    {"name": "Tayma", "lat": 27.62, "lon": 38.55, "country": "Saudi Arabia", "role": "Oasis Hub", "note": "Ancient oasis city; Babylonian King Nabonidus lived here 10 years"},
    {"name": "Mecca", "lat": 21.42, "lon": 39.83, "country": "Saudi Arabia", "role": "Trading Hub", "note": "Pre-Islamic trade fair; Kaaba pilgrimage and commerce combined"},
    {"name": "Leuke Kome", "lat": 27.24, "lon": 36.47, "country": "Saudi Arabia", "role": "Port", "note": "Roman-era Red Sea port; customs station; Nabataean harbor"},
    {"name": "Myos Hormos", "lat": 27.18, "lon": 33.93, "country": "Egypt", "role": "Port", "note": "Roman Red Sea port; incense import to Egypt; desert road to Nile"},
    {"name": "Berenice (Troglodytica)", "lat": 23.95, "lon": 35.48, "country": "Egypt", "role": "Port", "note": "Ptolemaic Red Sea port; incense, pepper, and gems imported"},
    {"name": "Coptos (Qift)", "lat": 25.99, "lon": 32.82, "country": "Egypt", "role": "Hub", "note": "Nile to Red Sea caravan starting point; Eastern Desert gateway"},
    {"name": "Alexandria", "lat": 31.20, "lon": 29.92, "country": "Egypt", "role": "Destination", "note": "Mediterranean terminus; incense distributed to Rome and Greece"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 7. TRANS-SAHARAN TRADE
# ═══════════════════════════════════════════════════════════════════════════════
TRANS_SAHARAN = [
    {"name": "Timbuktu", "lat": 16.77, "lon": -3.01, "country": "Mali", "goods": "Gold, Salt, Books", "note": "City of 333 saints; Sankore University; gold-salt exchange centre"},
    {"name": "Djenne", "lat": 13.91, "lon": -4.56, "country": "Mali", "goods": "Gold, Salt, Grain", "note": "Great Mosque (largest mud-brick building); ancient market town"},
    {"name": "Gao", "lat": 16.27, "lon": -0.04, "country": "Mali", "goods": "Gold, Salt, Slaves", "note": "Songhai Empire capital; Tomb of Askia; Niger River trade"},
    {"name": "Sijilmasa", "lat": 31.28, "lon": -4.28, "country": "Morocco", "goods": "Gold, Salt, Dates", "note": "Northern gateway to Saharan trade; 757-1393; Tafilalet oasis"},
    {"name": "Fez", "lat": 34.03, "lon": -5.00, "country": "Morocco", "goods": "Leather, Textiles", "note": "Oldest university (al-Qarawiyyin 859); medina UNESCO; tanneries"},
    {"name": "Marrakech", "lat": 31.63, "lon": -8.00, "country": "Morocco", "goods": "Gold, Textiles, Spices", "note": "Red City; Jemaa el-Fnaa market square; Almoravid to Saadian trade"},
    {"name": "Tunis", "lat": 36.81, "lon": 10.18, "country": "Tunisia", "goods": "Gold, Slaves, Leather", "note": "Mediterranean trade terminus; Medina of Tunis; Hafsid port"},
    {"name": "Tripoli", "lat": 32.90, "lon": 13.18, "country": "Libya", "goods": "Gold, Slaves, Ostrich", "note": "Fezzan route terminus; Ottoman regency port"},
    {"name": "Ghadames", "lat": 30.13, "lon": 9.50, "country": "Libya", "goods": "Salt, Dates, Gold", "note": "Pearl of the Desert; underground old city; oasis junction"},
    {"name": "Agadez", "lat": 16.97, "lon": 7.99, "country": "Niger", "goods": "Salt, Gold, Slaves", "note": "Air sultanate; Grand Mosque minaret; Tuareg caravan centre"},
    {"name": "Kano", "lat": 12.00, "lon": 8.52, "country": "Nigeria", "goods": "Leather, Cloth, Indigo", "note": "Hausa city-state; Kurmi Market; indigo dye pits; groundnut trade"},
    {"name": "Ouadane", "lat": 20.93, "lon": -11.62, "country": "Mauritania", "goods": "Salt, Gold, Dates", "note": "Caravan city; Adrar Plateau; UNESCO World Heritage"},
    {"name": "Chinguetti", "lat": 20.46, "lon": -12.36, "country": "Mauritania", "goods": "Salt, Books, Gold", "note": "Seventh holy city of Islam; manuscript libraries; desert oasis"},
    {"name": "Oualata (Walata)", "lat": 17.30, "lon": -7.03, "country": "Mauritania", "goods": "Gold, Salt, Copper", "note": "Southern Mauritania trading post; Ibn Battuta visited 1352"},
    {"name": "Kumbi Saleh", "lat": 15.77, "lon": -7.97, "country": "Mauritania", "goods": "Gold, Salt", "note": "Probable capital of Ghana Empire; 20,000 residents; gold trade"},
    {"name": "Taghaza", "lat": 23.55, "lon": -4.43, "country": "Mali", "goods": "Salt", "note": "Salt mine; buildings made of salt blocks; inhospitable but vital"},
    {"name": "Tadmekka", "lat": 18.97, "lon": 1.57, "country": "Mali", "goods": "Gold, Salt, Copper", "note": "Lost city of Essouk; gold workshop; currency minting"},
    {"name": "Bilma", "lat": 18.69, "lon": 12.92, "country": "Niger", "goods": "Salt, Dates, Natron", "note": "Salt oasis; annual Tuareg azalai salt caravan destination"},
    {"name": "Murzuq", "lat": 25.91, "lon": 13.92, "country": "Libya", "goods": "Gold, Slaves, Dates", "note": "Fezzan Saharan crossroads; Ottoman garrison; desert oasis"},
    {"name": "Zawila", "lat": 26.13, "lon": 15.70, "country": "Libya", "goods": "Slaves, Gold, Salt", "note": "Early trans-Saharan terminus; Ibadi Muslim centre"},
    {"name": "Niani", "lat": 11.38, "lon": -8.41, "country": "Guinea", "goods": "Gold, Salt, Kola", "note": "Capital of Mali Empire under Sundiata and Mansa Musa"},
    {"name": "Koumbi-Saleh (Ghana)", "lat": 15.77, "lon": -7.97, "country": "Mali/Mauritania", "goods": "Gold, Salt", "note": "Ghana Empire probable capital; twin-city trading centre"},
    {"name": "Awdaghust", "lat": 17.80, "lon": -11.20, "country": "Mauritania", "goods": "Gold, Salt, Slaves", "note": "Sanhaja Berber trade town; Almoravid capture 1054"},
    {"name": "Kairouan", "lat": 35.68, "lon": 10.10, "country": "Tunisia", "goods": "Textiles, Carpets", "note": "Islamic holy city; Great Mosque; Aghlabid trade; carpet centre"},
    {"name": "Taoudeni", "lat": 22.67, "lon": -3.98, "country": "Mali", "goods": "Salt", "note": "Replaced Taghaza; active salt mine; annual camel caravan continues"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 8. TIN & BRONZE AGE TRADE
# ═══════════════════════════════════════════════════════════════════════════════
TIN_BRONZE_TRADE = [
    {"name": "Cornwall (St. Austell)", "lat": 50.34, "lon": -4.79, "country": "England", "role": "Tin Source", "note": "Phoenicians traded for Cornish tin; 2000 BCE onwards; cassiterite"},
    {"name": "Erzgebirge (Freiberg)", "lat": 50.92, "lon": 13.34, "country": "Germany", "role": "Tin Source", "note": "Ore Mountains; Central European tin supply; Bronze Age mining"},
    {"name": "Iberian Peninsula (Huelva)", "lat": 37.26, "lon": -6.95, "country": "Spain", "role": "Tin & Copper", "note": "Rio Tinto mines; Tartessian tin trade; Phoenician contact"},
    {"name": "Ugarit (Ras Shamra)", "lat": 35.60, "lon": 35.78, "country": "Syria", "role": "Bronze Hub", "note": "Bronze Age port; cuneiform tablets record tin trade; alphabet origin"},
    {"name": "Byblos", "lat": 34.12, "lon": 35.65, "country": "Lebanon", "role": "Port", "note": "Egyptian-Levantine trade; cedar and bronze exports; 5000+ years"},
    {"name": "Knossos", "lat": 35.30, "lon": 25.16, "country": "Greece", "role": "Bronze Hub", "note": "Minoan palace; bronze weapons and tools; maritime trade network"},
    {"name": "Mycenae", "lat": 37.73, "lon": 22.76, "country": "Greece", "role": "Bronze Hub", "note": "Mycenaean citadel; bronze weapons; Lion Gate; shaft graves gold"},
    {"name": "Troy (Hisarlik)", "lat": 39.96, "lon": 26.24, "country": "Turkey", "role": "Trading Post", "note": "Dardanelles control; Bronze Age trade chokepoint; Schliemann gold"},
    {"name": "Hattusa", "lat": 40.02, "lon": 34.61, "country": "Turkey", "role": "Capital", "note": "Hittite Empire capital; iron and bronze smelting; lion gate"},
    {"name": "Ur", "lat": 30.96, "lon": 46.10, "country": "Iraq", "role": "Market", "note": "Sumerian city; ziggurat; Royal Tombs gold and bronze artifacts"},
    {"name": "Dilmun (Bahrain)", "lat": 26.23, "lon": 50.56, "country": "Bahrain", "role": "Entrepot", "note": "Mesopotamian-Indus Valley intermediary; pearl and copper trade"},
    {"name": "Lothal", "lat": 22.52, "lon": 72.25, "country": "India", "role": "Port/Workshop", "note": "Indus Valley dockyard; bronze casting; bead and shell trade"},
    {"name": "Mohenjo-daro", "lat": 27.33, "lon": 68.14, "country": "Pakistan", "role": "Bronze Centre", "note": "Dancing Girl bronze sculpture; planned city; 2500 BCE trade"},
    {"name": "Thebes (Luxor)", "lat": 25.70, "lon": 32.64, "country": "Egypt", "role": "Consumer", "note": "Egyptian capital; massive bronze weapon arsenals; tin imports"},
    {"name": "Memphis (Mit Rahina)", "lat": 29.85, "lon": 31.25, "country": "Egypt", "role": "Consumer/Hub", "note": "Old Kingdom capital; bronze tool production; trade with Levant"},
    {"name": "Sidon", "lat": 33.56, "lon": 35.37, "country": "Lebanon", "role": "Port", "note": "Phoenician port; bronze and glass trade; Purple Dye Coast"},
    {"name": "Kultepe (Kanesh)", "lat": 38.85, "lon": 35.64, "country": "Turkey", "role": "Trading Colony", "note": "Assyrian trading colony; 20,000 cuneiform tablets; tin trade records"},
    {"name": "Mari (Tell Hariri)", "lat": 34.55, "lon": 40.89, "country": "Syria", "role": "Trading Hub", "note": "Euphrates trade city; royal archives; tin route from Iran"},
    {"name": "Susa", "lat": 32.19, "lon": 48.26, "country": "Iran", "role": "Hub", "note": "Elamite capital; bronze metallurgy; tin from Afghanistan route"},
    {"name": "Shortugai", "lat": 37.35, "lon": 69.48, "country": "Afghanistan", "role": "Tin/Lapis Source", "note": "Indus Valley trading post; lapis lazuli and tin extraction"},
    {"name": "Oman (Magan)", "lat": 23.00, "lon": 57.00, "country": "Oman", "role": "Copper Source", "note": "Ancient Magan; copper smelting for Mesopotamia; 3rd millennium BCE"},
    {"name": "Cyprus (Enkomi)", "lat": 35.15, "lon": 33.88, "country": "Cyprus", "role": "Copper Source", "note": "Name means copper; Late Bronze Age smelting centre; oxhide ingots"},
    {"name": "Alashiya (Hala Sultan Tekke)", "lat": 34.88, "lon": 33.61, "country": "Cyprus", "role": "Port", "note": "Largest Bronze Age port in Cyprus; copper ingot exports"},
    {"name": "Santorini (Akrotiri)", "lat": 36.35, "lon": 25.40, "country": "Greece", "role": "Trading Hub", "note": "Minoan trading port; destroyed by eruption 1628 BCE; Pompeii of Aegean"},
    {"name": "Ebla (Tell Mardikh)", "lat": 35.80, "lon": 36.80, "country": "Syria", "role": "City-State", "note": "Royal archives; bronze weapons trade; 2400 BCE commercial empire"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 9. ROMAN TRADE NETWORKS
# ═══════════════════════════════════════════════════════════════════════════════
ROMAN_TRADE = [
    {"name": "Rome", "lat": 41.90, "lon": 12.50, "province": "Italia", "goods": "All imports", "note": "Caput mundi; 1 million inhabitants; consumed goods from entire empire"},
    {"name": "Ostia Antica", "lat": 41.76, "lon": 12.29, "province": "Italia", "goods": "Grain, Oil, Wine", "note": "Port of Rome; 100,000 pop; Piazzale delle Corporazioni trade guilds"},
    {"name": "Puteoli (Pozzuoli)", "lat": 40.82, "lon": 14.12, "province": "Italia", "goods": "Eastern imports", "note": "Main eastern trade port before Ostia expanded; volcanic cement export"},
    {"name": "Carthage", "lat": 36.85, "lon": 10.32, "province": "Africa", "goods": "Grain, Olive Oil", "note": "Roman Africa breadbasket; rebuilt by Augustus; second city of West"},
    {"name": "Alexandria", "lat": 31.20, "lon": 29.92, "province": "Aegyptus", "goods": "Grain, Papyrus, Spices", "note": "Roman grain fleet; Pharos lighthouse; Eastern trade hub; 500,000 pop"},
    {"name": "Antioch (Antakya)", "lat": 36.20, "lon": 36.16, "province": "Syria", "goods": "Silk, Spices", "note": "Third largest Roman city; Eastern frontier; silk market"},
    {"name": "Ephesus", "lat": 37.94, "lon": 27.34, "province": "Asia", "goods": "Textiles, Marble", "note": "Library of Celsus; Temple of Artemis; major Asian province port"},
    {"name": "Corinth", "lat": 37.94, "lon": 22.93, "province": "Achaea", "goods": "Bronze, Pottery", "note": "Diolkos portage; isthmus trade; Corinthian bronze famous worldwide"},
    {"name": "Londinium (London)", "lat": 51.51, "lon": -0.08, "province": "Britannia", "goods": "Tin, Lead, Wool", "note": "Thames port; amphitheatre; Billingsgate Roman bath house"},
    {"name": "Lugdunum (Lyon)", "lat": 45.76, "lon": 4.84, "province": "Gallia", "goods": "Wine, Pottery", "note": "Capital of Three Gauls; Rhone-Saone junction; amphitheatre"},
    {"name": "Gades (Cadiz)", "lat": 36.53, "lon": -6.29, "province": "Hispania", "goods": "Garum, Olive Oil", "note": "Oldest city in Western Europe; garum fish sauce factory"},
    {"name": "Augusta Treverorum (Trier)", "lat": 49.76, "lon": 6.64, "province": "Gallia Belgica", "goods": "Wine, Glass", "note": "Northern capital; Porta Nigra; imperial baths; Moselle wine"},
    {"name": "Leptis Magna", "lat": 32.64, "lon": 14.29, "province": "Africa", "goods": "Olive Oil, Animals", "note": "Septimius Severus birthplace; harbour; olive oil magnate city"},
    {"name": "Caesarea Maritima", "lat": 32.50, "lon": 34.89, "province": "Judaea", "goods": "Balsam, Dates", "note": "Herod's harbour; Roman provincial capital; aqueduct"},
    {"name": "Aquileia", "lat": 45.77, "lon": 13.37, "province": "Italia", "goods": "Amber, Wine, Iron", "note": "Amber Road southern terminus; 4th largest Italian city; port"},
    {"name": "Colonia Agrippina (Cologne)", "lat": 50.94, "lon": 6.96, "province": "Germania", "goods": "Glass, Pottery", "note": "Rhine frontier; famous glass workshops; Ubii oppidum"},
    {"name": "Palmyra", "lat": 34.55, "lon": 38.27, "province": "Syria", "goods": "Silk, Spices", "note": "Caravan city; Zenobia's rebellion; controlled Silk Road access"},
    {"name": "Petra", "lat": 30.33, "lon": 35.44, "province": "Arabia Petraea", "goods": "Incense, Spices", "note": "Annexed 106 CE; Nabataean incense route; Roman theatre added"},
    {"name": "Thessalonica", "lat": 40.64, "lon": 22.94, "province": "Macedonia", "goods": "Wine, Textiles", "note": "Via Egnatia terminus; harbour; second city after Constantinople"},
    {"name": "Byzantium (Constantinople)", "lat": 41.01, "lon": 28.98, "province": "Thracia", "goods": "Silk, Grain, Gold", "note": "Refounded 330 CE; New Rome; controlled Bosporus trade"},
    {"name": "Volubilis", "lat": 34.07, "lon": -5.55, "province": "Mauretania", "goods": "Olive Oil, Grain", "note": "Westernmost Roman city; Moroccan olive oil production; mosaics"},
    {"name": "Baelo Claudia", "lat": 36.09, "lon": -5.77, "province": "Hispania", "goods": "Garum, Fish", "note": "Strait of Gibraltar; garum factories; tuna fishing industry"},
    {"name": "Arelate (Arles)", "lat": 43.68, "lon": 4.63, "province": "Gallia", "goods": "Wine, Grain", "note": "Rhone River port; Constantine's capital; amphitheatre; sarcophagi"},
    {"name": "Dura-Europos", "lat": 34.75, "lon": 40.73, "province": "Syria", "goods": "Silk, Textiles", "note": "Euphrates fortress; earliest church and synagogue; papyri trade"},
    {"name": "Tingis (Tangier)", "lat": 35.79, "lon": -5.81, "province": "Mauretania", "goods": "Garum, Purple Dye", "note": "Strait of Gibraltar control; Hercules legend; African trade"},
]

# ═══════════════════════════════════════════════════════════════════════════════
# 10. MODERN BELT & ROAD INITIATIVE
# ═══════════════════════════════════════════════════════════════════════════════
BELT_ROAD = [
    {"name": "Beijing", "lat": 39.91, "lon": 116.40, "type": "HQ", "corridor": "All", "note": "BRI headquarters; announced 2013; trillion-dollar infrastructure plan"},
    {"name": "Xi'an", "lat": 34.26, "lon": 108.94, "type": "Rail Hub", "corridor": "Land Bridge", "note": "Starting point of China-Europe freight rail; historic Silk Road start"},
    {"name": "Urumqi", "lat": 43.83, "lon": 87.62, "type": "Rail Hub", "corridor": "Land Bridge", "note": "Xinjiang gateway; rail junction to Central Asia; dry port"},
    {"name": "Khorgos", "lat": 44.23, "lon": 80.30, "type": "Border Port", "corridor": "Land Bridge", "note": "China-Kazakhstan dry port; largest inland port; free trade zone"},
    {"name": "Astana (Nur-Sultan)", "lat": 51.17, "lon": 71.45, "type": "Capital", "corridor": "Land Bridge", "note": "Kazakhstan capital; Nurly Zhol programme integrated with BRI"},
    {"name": "Moscow", "lat": 55.76, "lon": 37.62, "type": "Hub", "corridor": "Land Bridge", "note": "Trans-Siberian connection; Europe-Asia rail junction"},
    {"name": "Duisburg", "lat": 51.43, "lon": 6.76, "type": "Terminus", "corridor": "Land Bridge", "note": "European rail terminus; Yuxinou Railway from Chongqing; Rhine port"},
    {"name": "Hamburg", "lat": 53.55, "lon": 9.99, "type": "Port", "corridor": "Land Bridge", "note": "European rail and sea hub; container terminal; China Rail Express"},
    {"name": "Piraeus", "lat": 37.94, "lon": 23.65, "type": "Port", "corridor": "Maritime", "note": "COSCO-operated Greek port; maritime Silk Road Mediterranean gateway"},
    {"name": "Gwadar", "lat": 25.12, "lon": 62.33, "type": "Port", "corridor": "CPEC", "note": "China-Pakistan Economic Corridor; deep-water port; Arabian Sea access"},
    {"name": "Islamabad", "lat": 33.69, "lon": 73.04, "type": "Hub", "corridor": "CPEC", "note": "CPEC northern terminus; Karakoram Highway upgrade; $62 billion corridor"},
    {"name": "Colombo (Port City)", "lat": 6.93, "lon": 79.85, "type": "Port", "corridor": "Maritime", "note": "Chinese-built reclaimed land port city; Indian Ocean hub"},
    {"name": "Hambantota", "lat": 6.12, "lon": 81.12, "type": "Port", "corridor": "Maritime", "note": "Chinese-built and leased port; 99-year lease; strategic location"},
    {"name": "Djibouti", "lat": 11.59, "lon": 43.15, "type": "Base/Port", "corridor": "Maritime", "note": "Chinese naval base; Djibouti-Ethiopia railway; Horn of Africa hub"},
    {"name": "Mombasa", "lat": -4.04, "lon": 39.67, "type": "Port/Rail", "corridor": "Maritime", "note": "SGR railway to Nairobi; Chinese-built; East African gateway"},
    {"name": "Nairobi", "lat": -1.29, "lon": 36.82, "type": "Rail Hub", "corridor": "East Africa", "note": "Mombasa-Nairobi SGR terminus; $3.8 billion railway; freight hub"},
    {"name": "Kyaukpyu", "lat": 19.43, "lon": 93.55, "type": "Port", "corridor": "CMEC", "note": "Myanmar deep-water port; oil and gas pipelines to Yunnan; SEZ"},
    {"name": "Vientiane", "lat": 17.97, "lon": 102.63, "type": "Rail", "corridor": "Indo-China", "note": "China-Laos high-speed rail; opened 2021; Kunming connection"},
    {"name": "Jakarta", "lat": -6.21, "lon": 106.85, "type": "Rail", "corridor": "Maritime", "note": "Jakarta-Bandung high-speed rail; Chinese-built; ASEAN hub"},
    {"name": "Addis Ababa", "lat": 9.02, "lon": 38.75, "type": "Rail Hub", "corridor": "East Africa", "note": "AU headquarters; Addis-Djibouti Chinese-built electric railway"},
    {"name": "Tashkent", "lat": 41.30, "lon": 69.28, "type": "Hub", "corridor": "Land Bridge", "note": "Uzbekistan capital; China-Central Asia-West Asia corridor node"},
    {"name": "Colombo", "lat": 6.93, "lon": 79.85, "type": "Port", "corridor": "Maritime", "note": "Sri Lanka port city project; strategic Indian Ocean positioning"},
    {"name": "Kuantan", "lat": 3.81, "lon": 103.33, "type": "Port", "corridor": "Maritime", "note": "Malaysia-China Kuantan Industrial Park; deep-water port expansion"},
    {"name": "Sihanoukville", "lat": 10.63, "lon": 103.50, "type": "SEZ", "corridor": "Indo-China", "note": "Cambodia special economic zone; Chinese investment; casino boom"},
    {"name": "Haifa", "lat": 32.79, "lon": 34.99, "type": "Port", "corridor": "Maritime", "note": "Chinese-operated Israeli port; Mediterranean BRI endpoint"},
    {"name": "Venice", "lat": 45.44, "lon": 12.34, "type": "Destination", "corridor": "Maritime", "note": "Italy joined BRI 2019 (later withdrew); historic Silk Road endpoint"},
    {"name": "Dar es Salaam", "lat": -6.79, "lon": 39.28, "type": "Port", "corridor": "East Africa", "note": "Chinese-built Bagamoyo port project; Tanzanian trade hub"},
    {"name": "Chongqing", "lat": 29.56, "lon": 106.55, "type": "Rail Hub", "corridor": "Land Bridge", "note": "Inland rail freight terminus; Yuxinou Railway to Europe origin"},
    {"name": "Kashgar", "lat": 39.47, "lon": 75.99, "type": "Hub", "corridor": "CPEC/Central Asia", "note": "Western China gateway; ancient and modern Silk Road junction"},
    {"name": "Malacca", "lat": 2.20, "lon": 102.25, "type": "Port", "corridor": "Maritime", "note": "Malacca Gateway project; strategic strait; Malaysia-China port"},
]


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTE LINES (for polyline rendering)
# ═══════════════════════════════════════════════════════════════════════════════
CLASSIC_SILK_NORTHERN = [
    {"lat": 34.26, "lon": 108.94}, {"lat": 36.06, "lon": 103.83},
    {"lat": 37.87, "lon": 101.78}, {"lat": 38.93, "lon": 100.45},
    {"lat": 40.14, "lon": 94.66}, {"lat": 42.95, "lon": 89.18},
    {"lat": 41.73, "lon": 82.94}, {"lat": 39.47, "lon": 75.99},
    {"lat": 41.30, "lon": 69.28}, {"lat": 39.65, "lon": 66.96},
    {"lat": 39.77, "lon": 64.42}, {"lat": 37.66, "lon": 62.17},
    {"lat": 35.69, "lon": 51.39}, {"lat": 38.08, "lon": 46.29},
    {"lat": 41.01, "lon": 28.98},
]

CLASSIC_SILK_SOUTHERN = [
    {"lat": 34.26, "lon": 108.94}, {"lat": 36.06, "lon": 103.83},
    {"lat": 40.14, "lon": 94.66}, {"lat": 37.11, "lon": 79.93},
    {"lat": 38.42, "lon": 77.27}, {"lat": 39.47, "lon": 75.99},
    {"lat": 33.75, "lon": 72.83}, {"lat": 34.35, "lon": 62.20},
    {"lat": 36.76, "lon": 66.90}, {"lat": 39.65, "lon": 66.96},
]

MARITIME_ROUTE_COORDS = [
    {"lat": 30.27, "lon": 120.15}, {"lat": 24.87, "lon": 118.68},
    {"lat": 23.13, "lon": 113.26}, {"lat": 15.88, "lon": 108.33},
    {"lat": 2.20, "lon": 102.25}, {"lat": -2.99, "lon": 104.76},
    {"lat": 9.97, "lon": 76.27}, {"lat": 11.25, "lon": 75.77},
    {"lat": 23.59, "lon": 58.54}, {"lat": 12.79, "lon": 45.04},
    {"lat": 31.20, "lon": 29.92}, {"lat": 41.01, "lon": 28.98},
]

INCENSE_ROUTE_COORDS = [
    {"lat": 17.02, "lon": 54.09}, {"lat": 15.36, "lon": 47.02},
    {"lat": 15.46, "lon": 45.35}, {"lat": 17.49, "lon": 44.13},
    {"lat": 21.42, "lon": 39.83}, {"lat": 24.47, "lon": 39.61},
    {"lat": 26.62, "lon": 37.92}, {"lat": 26.79, "lon": 37.95},
    {"lat": 30.33, "lon": 35.44}, {"lat": 30.79, "lon": 34.77},
    {"lat": 31.50, "lon": 34.47},
]

AMBER_ROUTE_COORDS = [
    {"lat": 54.71, "lon": 20.51}, {"lat": 54.35, "lon": 18.65},
    {"lat": 53.01, "lon": 18.61}, {"lat": 51.11, "lon": 17.04},
    {"lat": 50.08, "lon": 14.44}, {"lat": 48.21, "lon": 16.37},
    {"lat": 48.11, "lon": 16.86}, {"lat": 47.69, "lon": 16.59},
    {"lat": 46.06, "lon": 14.51}, {"lat": 45.77, "lon": 13.37},
    {"lat": 41.90, "lon": 12.50},
]

TRANS_SAHARAN_ROUTE_COORDS = [
    {"lat": 34.03, "lon": -5.00}, {"lat": 31.28, "lon": -4.28},
    {"lat": 22.67, "lon": -3.98}, {"lat": 16.77, "lon": -3.01},
    {"lat": 13.91, "lon": -4.56},
]

TRANS_SAHARAN_EAST_COORDS = [
    {"lat": 32.90, "lon": 13.18}, {"lat": 25.91, "lon": 13.92},
    {"lat": 18.69, "lon": 12.92}, {"lat": 16.97, "lon": 7.99},
    {"lat": 12.00, "lon": 8.52},
]


# ═══════════════════════════════════════════════════════════════════════════════
# INDIVIDUAL RENDERERS
# ═══════════════════════════════════════════════════════════════════════════════

def _render_classic_silk_road():
    """Mode 1: Classic Silk Road Cities."""
    st.markdown("#### Classic Silk Road Cities")
    st.caption("30 key cities along the overland Silk Road from Chang'an (Xi'an) to Constantinople (Istanbul), spanning 6400 km and over 1500 years of commerce.")

    type_counts = {}
    for c in CLASSIC_SILK_ROAD:
        t = c["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    _stats_row({
        "Total Cities": len(CLASSIC_SILK_ROAD),
        "Capitals": type_counts.get("capital", 0),
        "Oasis Towns": type_counts.get("oasis", 0),
        "Markets": type_counts.get("market", 0),
        "Route Length": "~6,400 km",
    })

    m = _base_map(center=(38.0, 65.0), zoom=4)

    # Route polylines
    _add_route_line(m, CLASSIC_SILK_NORTHERN, ROUTE_COLORS["land"], "Northern Silk Road")
    _add_route_line(m, CLASSIC_SILK_SOUTHERN, ROUTE_COLORS["branch"], "Southern Silk Road")

    # City markers
    for loc in CLASSIC_SILK_ROAD:
        color = CITY_COLORS.get(loc["type"], "#f59e0b")
        fields = {"Type": loc["type"].title(), "Period": loc["period"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=280)
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=8,
            color=color, fill=True, fill_color=color, fill_opacity=0.75, weight=2,
            popup=popup, tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    # Legend
    legend_items = " ".join(
        f'<span style="color:{CITY_COLORS.get(t, "#8b97b0")}; font-size:0.8rem;">&#9679; {html_module.escape(t.title())}</span>'
        for t in sorted(type_counts.keys())
    )
    st.markdown(f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>', unsafe_allow_html=True)
    st_html(m._repr_html_(), height=500)

    df = pd.DataFrame(CLASSIC_SILK_ROAD)
    _table_and_download(df, "Silk Road Cities", "silk_road_cities.csv", "dl_silk_cities")


def _render_maritime_silk_road():
    """Mode 2: Maritime Silk Road Ports."""
    st.markdown("#### Maritime Silk Road Ports")
    st.caption("30 historic ports along the Maritime Silk Road from Hangzhou to Alexandria, tracing centuries of ocean-going trade.")

    country_counts = {}
    for p in MARITIME_PORTS:
        c = p["country"]
        country_counts[c] = country_counts.get(c, 0) + 1
    top_countries = sorted(country_counts.items(), key=lambda x: -x[1])[:4]
    _stats_row({
        "Total Ports": len(MARITIME_PORTS),
        "Countries": len(country_counts),
        **{k: v for k, v in top_countries},
    })

    m = _base_map(center=(15.0, 70.0), zoom=3)
    _add_route_line(m, MARITIME_ROUTE_COORDS, ROUTE_COLORS["sea"], "Maritime Silk Road")

    for loc in MARITIME_PORTS:
        fields = {"Country": loc["country"], "Period": loc["period"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=280)
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=7,
            color=ROUTE_COLORS["sea"], fill=True, fill_color=ROUTE_COLORS["sea"],
            fill_opacity=0.75, weight=2, popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(MARITIME_PORTS)
    _table_and_download(df, "Maritime Ports", "maritime_silk_road.csv", "dl_maritime")


def _render_caravanserais():
    """Mode 3: Caravanserai & Rest Stops."""
    st.markdown("#### Caravanserai & Rest Stops")
    st.caption("30 historic caravanserais across Turkey, Iran, Central Asia and beyond -- the roadside inns of the Silk Road.")

    country_counts = {}
    for c in CARAVANSERAIS:
        co = c["country"]
        country_counts[co] = country_counts.get(co, 0) + 1
    top_countries = sorted(country_counts.items(), key=lambda x: -x[1])[:4]
    _stats_row({
        "Total Caravanserais": len(CARAVANSERAIS),
        "Countries": len(country_counts),
        **{k: v for k, v in top_countries},
    })

    m = _base_map(center=(38.0, 50.0), zoom=4)
    for loc in CARAVANSERAIS:
        fields = {"Country": loc["country"], "Built": loc["built"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=280)
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=7,
            color=ROUTE_COLORS["land"], fill=True, fill_color=ROUTE_COLORS["land"],
            fill_opacity=0.75, weight=2, popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(CARAVANSERAIS)
    _table_and_download(df, "Caravanserais", "caravanserais.csv", "dl_caravanserais")


def _render_spice_trade():
    """Mode 4: Spice Trade Routes."""
    st.markdown("#### Spice Trade Routes")
    st.caption("25 key spice trade ports and cities from the Maluku Islands to Amsterdam, covering 2000 years of the global spice trade.")

    region_counts = {}
    for s in SPICE_TRADE:
        r = s["region"]
        region_counts[r] = region_counts.get(r, 0) + 1
    top = sorted(region_counts.items(), key=lambda x: -x[1])[:4]
    _stats_row({
        "Spice Centres": len(SPICE_TRADE),
        "Regions": len(region_counts),
        **{k: v for k, v in top},
    })

    m = _base_map(center=(15.0, 60.0), zoom=3)
    for loc in SPICE_TRADE:
        fields = {"Region": loc["region"], "Spices": loc["spices"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=300)
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=7,
            color=ROUTE_COLORS["spice"], fill=True, fill_color=ROUTE_COLORS["spice"],
            fill_opacity=0.75, weight=2, popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(SPICE_TRADE)
    _table_and_download(df, "Spice Trade Sites", "spice_trade.csv", "dl_spice")


def _render_amber_road():
    """Mode 5: Amber Road of Europe."""
    st.markdown("#### Amber Road of Europe")
    st.caption("25 stops along the prehistoric and Roman Amber Road from the Baltic Sea to the Mediterranean.")

    role_counts = {}
    for a in AMBER_ROAD:
        r = a["role"]
        role_counts[r] = role_counts.get(r, 0) + 1
    top = sorted(role_counts.items(), key=lambda x: -x[1])[:4]
    _stats_row({
        "Total Stops": len(AMBER_ROAD),
        "Countries": len(set(a["country"] for a in AMBER_ROAD)),
        **{k: v for k, v in top},
    })

    m = _base_map(center=(49.0, 14.0), zoom=5)
    _add_route_line(m, AMBER_ROUTE_COORDS, ROUTE_COLORS["amber"], "Amber Road")

    for loc in AMBER_ROAD:
        fields = {"Country": loc["country"], "Role": loc["role"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=280)
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=7,
            color=ROUTE_COLORS["amber"], fill=True, fill_color=ROUTE_COLORS["amber"],
            fill_opacity=0.75, weight=2, popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(AMBER_ROAD)
    _table_and_download(df, "Amber Road Stops", "amber_road.csv", "dl_amber")


def _render_incense_route():
    """Mode 6: Incense Route of Arabia."""
    st.markdown("#### Incense Route of Arabia")
    st.caption("25 sites along the ancient Incense Route from Dhofar (Oman) through Arabia to the Mediterranean.")

    role_counts = {}
    for loc in INCENSE_ROUTE:
        r = loc["role"]
        role_counts[r] = role_counts.get(r, 0) + 1
    top = sorted(role_counts.items(), key=lambda x: -x[1])[:4]
    _stats_row({
        "Total Sites": len(INCENSE_ROUTE),
        "Countries": len(set(loc["country"] for loc in INCENSE_ROUTE)),
        **{k: v for k, v in top},
    })

    m = _base_map(center=(25.0, 40.0), zoom=5)
    _add_route_line(m, INCENSE_ROUTE_COORDS, ROUTE_COLORS["incense"], "Incense Route")

    for loc in INCENSE_ROUTE:
        fields = {"Country": loc["country"], "Role": loc["role"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=280)
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=7,
            color=ROUTE_COLORS["incense"], fill=True, fill_color=ROUTE_COLORS["incense"],
            fill_opacity=0.75, weight=2, popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(INCENSE_ROUTE)
    _table_and_download(df, "Incense Route Sites", "incense_route.csv", "dl_incense")


def _render_trans_saharan():
    """Mode 7: Trans-Saharan Trade."""
    st.markdown("#### Trans-Saharan Trade Routes")
    st.caption("25 key cities and oases along the trans-Saharan gold-salt trade routes connecting North and West Africa.")

    country_counts = {}
    for loc in TRANS_SAHARAN:
        c = loc["country"]
        country_counts[c] = country_counts.get(c, 0) + 1
    top = sorted(country_counts.items(), key=lambda x: -x[1])[:4]
    _stats_row({
        "Trade Sites": len(TRANS_SAHARAN),
        "Countries": len(country_counts),
        **{k: v for k, v in top},
    })

    m = _base_map(center=(22.0, 0.0), zoom=4)
    _add_route_line(m, TRANS_SAHARAN_ROUTE_COORDS, ROUTE_COLORS["saharan"], "Western Trans-Saharan Route")
    _add_route_line(m, TRANS_SAHARAN_EAST_COORDS, "#f97316", "Eastern Trans-Saharan Route")

    for loc in TRANS_SAHARAN:
        fields = {"Country": loc["country"], "Goods": loc["goods"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=280)
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=7,
            color=ROUTE_COLORS["saharan"], fill=True, fill_color=ROUTE_COLORS["saharan"],
            fill_opacity=0.75, weight=2, popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(TRANS_SAHARAN)
    _table_and_download(df, "Trans-Saharan Sites", "trans_saharan.csv", "dl_saharan")


def _render_tin_bronze():
    """Mode 8: Tin & Bronze Age Trade."""
    st.markdown("#### Tin & Bronze Age Trade Networks")
    st.caption("25 key sites in the Bronze Age tin and copper trade network, from Cornwall to the Indus Valley (3000-1200 BCE).")

    role_counts = {}
    for loc in TIN_BRONZE_TRADE:
        r = loc["role"]
        role_counts[r] = role_counts.get(r, 0) + 1
    top = sorted(role_counts.items(), key=lambda x: -x[1])[:4]
    _stats_row({
        "Bronze Age Sites": len(TIN_BRONZE_TRADE),
        "Countries": len(set(loc["country"] for loc in TIN_BRONZE_TRADE)),
        **{k: v for k, v in top},
    })

    m = _base_map(center=(35.0, 40.0), zoom=4)
    for loc in TIN_BRONZE_TRADE:
        fields = {"Country": loc["country"], "Role": loc["role"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=280)
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=7,
            color=ROUTE_COLORS["tin"], fill=True, fill_color=ROUTE_COLORS["tin"],
            fill_opacity=0.75, weight=2, popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(TIN_BRONZE_TRADE)
    _table_and_download(df, "Bronze Age Sites", "bronze_age_trade.csv", "dl_bronze")


def _render_roman_trade():
    """Mode 9: Roman Trade Networks."""
    st.markdown("#### Roman Trade Networks")
    st.caption("25 major Roman trade cities and ports, from Londinium to Palmyra, spanning the height of Roman commercial power.")

    province_counts = {}
    for loc in ROMAN_TRADE:
        p = loc["province"]
        province_counts[p] = province_counts.get(p, 0) + 1
    top = sorted(province_counts.items(), key=lambda x: -x[1])[:4]
    _stats_row({
        "Roman Trade Sites": len(ROMAN_TRADE),
        "Provinces": len(province_counts),
        **{k: v for k, v in top},
    })

    m = _base_map(center=(38.0, 15.0), zoom=4)
    for loc in ROMAN_TRADE:
        fields = {"Province": loc["province"], "Goods": loc["goods"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=280)
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=7,
            color=ROUTE_COLORS["roman"], fill=True, fill_color=ROUTE_COLORS["roman"],
            fill_opacity=0.75, weight=2, popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(ROMAN_TRADE)
    _table_and_download(df, "Roman Trade Sites", "roman_trade.csv", "dl_roman")


def _render_belt_road():
    """Mode 10: Modern Belt & Road Initiative."""
    st.markdown("#### Modern Belt & Road Initiative")
    st.caption("30 key infrastructure nodes of China's Belt and Road Initiative (BRI), the modern successor to the Silk Road.")

    type_counts = {}
    for loc in BELT_ROAD:
        t = loc["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    top = sorted(type_counts.items(), key=lambda x: -x[1])[:4]
    _stats_row({
        "BRI Nodes": len(BELT_ROAD),
        "Node Types": len(type_counts),
        **{k: v for k, v in top},
    })

    m = _base_map(center=(25.0, 60.0), zoom=3)
    for loc in BELT_ROAD:
        fields = {"Type": loc["type"], "Corridor": loc["corridor"], "Info": loc["note"]}
        popup = folium.Popup(_popup_html(loc["name"], fields), max_width=280)
        color = ROUTE_COLORS["belt_road"]
        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]], radius=7,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.75, weight=2, popup=popup,
            tooltip=html_module.escape(loc["name"]),
        ).add_to(m)

    st_html(m._repr_html_(), height=500)
    df = pd.DataFrame(BELT_ROAD)
    _table_and_download(df, "BRI Nodes", "belt_road_initiative.csv", "dl_bri")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
_MODE_RENDERERS = {
    "Classic Silk Road Cities": _render_classic_silk_road,
    "Maritime Silk Road Ports": _render_maritime_silk_road,
    "Caravanserai & Rest Stops": _render_caravanserais,
    "Spice Trade Routes": _render_spice_trade,
    "Amber Road of Europe": _render_amber_road,
    "Incense Route Arabia": _render_incense_route,
    "Trans-Saharan Trade": _render_trans_saharan,
    "Tin & Bronze Age Trade": _render_tin_bronze,
    "Roman Trade Networks": _render_roman_trade,
    "Modern Belt & Road Initiative": _render_belt_road,
}


def render_silk_road_maps_tab():
    """Render the Silk Road & Ancient Trade Explorer tab."""
    st.markdown(
        '<div class="tab-header amber">'
        '<h4>Silk Road & Ancient Trade Explorer</h4>'
        '<p>Silk Road caravanserais, spice routes, maritime trade, ancient markets & bazaars</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        list(_MODE_RENDERERS.keys()),
        key="silk_road_maps_mode",
    )

    st.markdown("---")
    renderer = _MODE_RENDERERS.get(mode)
    if renderer:
        renderer()
