"""
Street Food World Explorer module for TerraScout AI.
Curated maps of iconic street food destinations across 10 cities worldwide.
Preset data with markers, stats, DataFrame, and CSV download for each mode.
"""

import streamlit as st
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module
import pandas as pd


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _popup(name, details):
    """Build a rich HTML popup string with escaped content."""
    safe_name = html_module.escape(str(name))
    rows = ""
    for k, v in details.items():
        safe_key = html_module.escape(str(k))
        safe_val = html_module.escape(str(v))
        rows += (
            f"<tr>"
            f"<td style='padding:4px 10px;color:#f472b6;font-weight:600;"
            f"white-space:nowrap;vertical-align:top;'>{safe_key}</td>"
            f"<td style='padding:4px 10px;color:#e8ecf4;'>{safe_val}</td>"
            f"</tr>"
        )
    return (
        f"<div style=\"font-family:'Segoe UI',Arial,sans-serif;"
        f"background:#1a1a2e;border:1px solid #f472b6;border-radius:10px;"
        f"padding:12px 14px;min-width:240px;max-width:360px;\">"
        f"<h4 style=\"margin:0 0 8px 0;color:#f472b6;font-size:14px;\">"
        f"{safe_name}</h4>"
        f"<table style=\"border-collapse:collapse;width:100%;\">{rows}</table>"
        f"</div>"
    )


def _build_map(locations, zoom=3, center=None):
    """Create a Folium map with CartoDB dark_matter tiles and MarkerCluster."""
    if center is None:
        lats = [loc["lat"] for loc in locations]
        lons = [loc["lon"] for loc in locations]
        center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )
    cluster = MarkerCluster(name="Street Food Spots").add_to(m)
    for loc in locations:
        details = {
            k: v
            for k, v in loc.items()
            if k not in ("lat", "lon", "name", "color")
        }
        color = loc.get("color", "red")
        folium.Marker(
            location=[loc["lat"], loc["lon"]],
            popup=folium.Popup(
                _popup(loc["name"], details),
                max_width=360,
            ),
            tooltip=html_module.escape(str(loc["name"])),
            icon=folium.Icon(color=color, icon="cutlery", prefix="fa"),
        ).add_to(cluster)
    return m


def _show_map_and_data(locations, zoom=3, center=None, csv_prefix="street_food"):
    """Render the interactive map, a dataframe preview, and a CSV download."""
    m = _build_map(locations, zoom=zoom, center=center)
    st_html(m._repr_html_(), height=500)

    st.markdown("---")
    st.markdown("#### Data Table")
    df = pd.DataFrame(locations)
    display_cols = [c for c in df.columns if c != "color"]
    st.dataframe(df[display_cols], use_container_width=True)

    csv = df[display_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download CSV",
        csv,
        f"{csv_prefix}_data.csv",
        "text/csv",
        key=f"sf_dl_{csv_prefix}_" + str(hash(str(locations[:2]))),
    )


# ---------------------------------------------------------------------------
# DATA: Bangkok Street Food
# ---------------------------------------------------------------------------

BANGKOK_STREET_FOOD = [
    {"name": "Yaowarat Road (Chinatown)", "lat": 13.7412, "lon": 100.5100, "Area": "Chinatown", "Specialty": "Seafood, pad thai, mango sticky rice", "Hours": "Evening to midnight", "Price Range": "40-200 THB", "color": "red"},
    {"name": "Chatuchak Weekend Market", "lat": 13.7999, "lon": 100.5530, "Area": "Chatuchak", "Specialty": "Coconut ice cream, grilled meats, Thai crepes", "Hours": "Sat-Sun 6am-6pm", "Price Range": "30-150 THB", "color": "orange"},
    {"name": "Khao San Road", "lat": 13.7589, "lon": 100.4974, "Area": "Banglamphu", "Specialty": "Pad thai, scorpion skewers, fruit shakes", "Hours": "Evening to late night", "Price Range": "50-200 THB", "color": "red"},
    {"name": "Soi Rambuttri", "lat": 13.7617, "lon": 100.4964, "Area": "Banglamphu", "Specialty": "Spring rolls, fried bananas, Thai iced tea", "Hours": "Afternoon to midnight", "Price Range": "30-120 THB", "color": "orange"},
    {"name": "Or Tor Kor Market", "lat": 13.8017, "lon": 100.5530, "Area": "Chatuchak", "Specialty": "Premium fruits, curries, Thai desserts", "Hours": "Daily 6am-6pm", "Price Range": "50-300 THB", "color": "red"},
    {"name": "Thip Samai (Pad Thai Pratu Pi)", "lat": 13.7524, "lon": 100.5070, "Area": "Phra Nakhon", "Specialty": "Pad Thai wrapped in egg omelette", "Hours": "5pm-2am", "Price Range": "60-100 THB", "color": "darkred"},
    {"name": "Jay Fai (Michelin Star Street Food)", "lat": 13.7536, "lon": 100.5060, "Area": "Phra Nakhon", "Specialty": "Crab omelette, drunken noodles, tom yum", "Hours": "3pm-midnight", "Price Range": "200-1000 THB", "color": "darkred"},
    {"name": "Wang Lang Market", "lat": 13.7594, "lon": 100.4850, "Area": "Bangkok Noi", "Specialty": "Boat noodles, Thai sweets, sticky rice", "Hours": "Daily 7am-6pm", "Price Range": "20-100 THB", "color": "orange"},
    {"name": "Silom Soi 20 Night Food", "lat": 13.7230, "lon": 100.5304, "Area": "Silom", "Specialty": "Grilled satay, som tam, mango sticky rice", "Hours": "Evening to midnight", "Price Range": "40-150 THB", "color": "red"},
    {"name": "Hua Lamphong Night Market", "lat": 13.7380, "lon": 100.5170, "Area": "Pathum Wan", "Specialty": "Khao kha moo (braised pork leg), noodles", "Hours": "Evening to late night", "Price Range": "40-120 THB", "color": "orange"},
    {"name": "Ratchawat Market", "lat": 13.7760, "lon": 100.5140, "Area": "Dusit", "Specialty": "Boat noodles, kuay teow, charcoal grills", "Hours": "Morning to afternoon", "Price Range": "30-80 THB", "color": "orange"},
    {"name": "Petchaburi Soi 5", "lat": 13.7490, "lon": 100.5410, "Area": "Ratchathewi", "Specialty": "Chicken rice, fish ball noodles, Thai tea", "Hours": "Lunch to evening", "Price Range": "35-100 THB", "color": "orange"},
    {"name": "Saphan Lueng (Yellow Bridge) Market", "lat": 13.7305, "lon": 100.5235, "Area": "Bang Rak", "Specialty": "Hoy tod (crispy mussel crepe), fried rice", "Hours": "Evening to midnight", "Price Range": "50-200 THB", "color": "red"},
    {"name": "Nang Loeng Market", "lat": 13.7620, "lon": 100.5100, "Area": "Nakhon Sawan", "Specialty": "Khanom bueng, century-old recipes, coconut sweets", "Hours": "Morning to afternoon", "Price Range": "20-80 THB", "color": "orange"},
    {"name": "Ari Neighborhood Food Street", "lat": 13.7790, "lon": 100.5450, "Area": "Phaya Thai", "Specialty": "Craft coffee, fusion street food, artisan desserts", "Hours": "All day", "Price Range": "50-200 THB", "color": "red"},
]

# ---------------------------------------------------------------------------
# DATA: Mexico City Tacos
# ---------------------------------------------------------------------------

MEXICO_CITY_TACOS = [
    {"name": "Taqueria El Vilsito", "lat": 19.3735, "lon": -99.1628, "Area": "Narvarte", "Specialty": "Tacos al pastor, suadero, longaniza", "Hours": "Night (auto shop by day)", "Price Range": "15-30 MXN", "color": "red"},
    {"name": "Mercado de Coyoacan", "lat": 19.3497, "lon": -99.1623, "Area": "Coyoacan", "Specialty": "Tostadas, quesadillas, elote, churros", "Hours": "Daily 7am-7pm", "Price Range": "20-80 MXN", "color": "orange"},
    {"name": "Tacos de Canasta (La Guerrero)", "lat": 19.4454, "lon": -99.1510, "Area": "La Guerrero", "Specialty": "Basket tacos with bean, chicharron, potato", "Hours": "Morning to early afternoon", "Price Range": "5-15 MXN", "color": "darkred"},
    {"name": "Taqueria Orinoco", "lat": 19.4280, "lon": -99.1620, "Area": "Roma Norte", "Specialty": "Norteño-style tacos, flour tortillas, grilled meats", "Hours": "8am-midnight", "Price Range": "30-80 MXN", "color": "red"},
    {"name": "Mercado de San Juan", "lat": 19.4296, "lon": -99.1424, "Area": "Centro Historico", "Specialty": "Exotic meats, gourmet tacos, ceviche, insects", "Hours": "Daily 9am-5pm", "Price Range": "30-200 MXN", "color": "orange"},
    {"name": "El Huequito", "lat": 19.4332, "lon": -99.1383, "Area": "Centro Historico", "Specialty": "Tacos al pastor (since 1959)", "Hours": "Daily 9am-11pm", "Price Range": "20-50 MXN", "color": "darkred"},
    {"name": "Mercado de Jamaica", "lat": 19.4162, "lon": -99.1270, "Area": "Jamaica", "Specialty": "Flowers, fresh produce, antojitos, tamales", "Hours": "Daily 6am-6pm", "Price Range": "15-60 MXN", "color": "orange"},
    {"name": "Taqueria Los Cocuyos", "lat": 19.4350, "lon": -99.1370, "Area": "Centro Historico", "Specialty": "Suadero, cabeza, tripa tacos on tiny tortillas", "Hours": "Evening to 3am", "Price Range": "10-25 MXN", "color": "red"},
    {"name": "Mercado de la Merced", "lat": 19.4270, "lon": -99.1240, "Area": "La Merced", "Specialty": "Quesadillas, tlacoyos, tamales, esquites", "Hours": "Daily 6am-6pm", "Price Range": "10-50 MXN", "color": "orange"},
    {"name": "Tacos Don Juan (Roma)", "lat": 19.4190, "lon": -99.1620, "Area": "Roma Sur", "Specialty": "Birria tacos, consomme, carne asada", "Hours": "Noon to midnight", "Price Range": "25-60 MXN", "color": "red"},
    {"name": "Mercado de Medellin", "lat": 19.4130, "lon": -99.1610, "Area": "Roma Sur", "Specialty": "Colombian, Cuban and Mexican antojitos", "Hours": "Daily 7am-6pm", "Price Range": "30-100 MXN", "color": "orange"},
    {"name": "El Tizoncito (Condesa)", "lat": 19.4130, "lon": -99.1730, "Area": "Condesa", "Specialty": "Claims to have invented tacos al pastor", "Hours": "1pm-3am", "Price Range": "25-60 MXN", "color": "darkred"},
    {"name": "Puesto de Tamales (Reforma)", "lat": 19.4340, "lon": -99.1530, "Area": "Cuauhtemoc", "Specialty": "Tamales oaxaquenos, rajas, mole, atole", "Hours": "6am-noon", "Price Range": "15-30 MXN", "color": "orange"},
    {"name": "Taqueria El Califa de Leon", "lat": 19.4250, "lon": -99.1640, "Area": "Roma Norte", "Specialty": "Costilla, bistec tacos (Michelin Bib Gourmand)", "Hours": "Evening to midnight", "Price Range": "25-70 MXN", "color": "darkred"},
    {"name": "Esquites Cart (Chapultepec)", "lat": 19.4200, "lon": -99.1816, "Area": "Chapultepec", "Specialty": "Esquites, elote en vaso with mayo, chili, lime", "Hours": "All day", "Price Range": "20-40 MXN", "color": "orange"},
]

# ---------------------------------------------------------------------------
# DATA: Istanbul Street Food
# ---------------------------------------------------------------------------

ISTANBUL_STREET_FOOD = [
    {"name": "Eminonu Balik Ekmek (Fish Bread)", "lat": 41.0186, "lon": 28.9730, "Area": "Eminonu", "Specialty": "Balik ekmek (grilled mackerel sandwich)", "Hours": "Morning to evening", "Price Range": "50-100 TRY", "color": "red"},
    {"name": "Simit Sarayi - Galata Bridge", "lat": 41.0196, "lon": 28.9736, "Area": "Galata Bridge", "Specialty": "Simit (sesame bread ring), cay", "Hours": "All day", "Price Range": "15-40 TRY", "color": "orange"},
    {"name": "Istiklal Caddesi Street Vendors", "lat": 41.0340, "lon": 28.9770, "Area": "Beyoglu", "Specialty": "Chestnuts, ice cream, waffle, midye dolma", "Hours": "All day and evening", "Price Range": "20-80 TRY", "color": "red"},
    {"name": "Karakoy Gulluoglu", "lat": 41.0218, "lon": 28.9760, "Area": "Karakoy", "Specialty": "Baklava (since 1871), pistachio rolls", "Hours": "Daily 7am-midnight", "Price Range": "80-200 TRY", "color": "darkred"},
    {"name": "Ortakoy Square", "lat": 41.0477, "lon": 29.0268, "Area": "Ortakoy", "Specialty": "Kumpir (loaded baked potatoes), waffle", "Hours": "Afternoon to late night", "Price Range": "60-120 TRY", "color": "red"},
    {"name": "Kadikoy Market (Asian Side)", "lat": 40.9893, "lon": 29.0236, "Area": "Kadikoy", "Specialty": "Pickles, borek, kokorec, fresh fish", "Hours": "Daily 8am-8pm", "Price Range": "30-100 TRY", "color": "orange"},
    {"name": "Sultanahmet Kofte (Historic)", "lat": 41.0086, "lon": 28.9760, "Area": "Sultanahmet", "Specialty": "Traditional meatball kofte since 1920", "Hours": "Daily 11am-11pm", "Price Range": "80-150 TRY", "color": "darkred"},
    {"name": "Beyoglu Cicek Pasaji", "lat": 41.0330, "lon": 28.9765, "Area": "Beyoglu", "Specialty": "Midye dolma (stuffed mussels), tavuk gogsu", "Hours": "Afternoon to midnight", "Price Range": "40-100 TRY", "color": "red"},
    {"name": "Taksim Doner Row", "lat": 41.0370, "lon": 28.9850, "Area": "Taksim", "Specialty": "Rotating vertical doner kebab, durum wraps", "Hours": "Lunch to late night", "Price Range": "60-120 TRY", "color": "red"},
    {"name": "Fatih Corn Vendors (Misir)", "lat": 41.0195, "lon": 28.9500, "Area": "Fatih", "Specialty": "Roasted corn on the cob, boiled corn", "Hours": "All day", "Price Range": "15-30 TRY", "color": "orange"},
    {"name": "Grand Bazaar Lokum & Spices", "lat": 41.0108, "lon": 28.9680, "Area": "Fatih", "Specialty": "Turkish delight, spice teas, dried fruit", "Hours": "Mon-Sat 9am-7pm", "Price Range": "50-300 TRY", "color": "orange"},
    {"name": "Bebek Waffle & Ice Cream", "lat": 41.0765, "lon": 29.0435, "Area": "Bebek", "Specialty": "Belgian waffles, Maras ice cream, kunefe", "Hours": "Afternoon to midnight", "Price Range": "60-150 TRY", "color": "red"},
    {"name": "Balat Neighborhood Street Eats", "lat": 41.0305, "lon": 28.9485, "Area": "Balat", "Specialty": "Borek stands, lahmacun, fresh juice carts", "Hours": "Morning to evening", "Price Range": "20-80 TRY", "color": "orange"},
    {"name": "Uskudar Kanlica Yogurt", "lat": 41.0720, "lon": 29.0570, "Area": "Kanlica", "Specialty": "Famous creamy yogurt with powdered sugar", "Hours": "Daily 8am-10pm", "Price Range": "40-70 TRY", "color": "orange"},
    {"name": "Besiktas Carsi Fish Market", "lat": 41.0430, "lon": 29.0035, "Area": "Besiktas", "Specialty": "Grilled fish, mussels, pickled vegetables", "Hours": "Daily 8am-8pm", "Price Range": "50-150 TRY", "color": "red"},
]

# ---------------------------------------------------------------------------
# DATA: Mumbai Chaat & Vada Pav
# ---------------------------------------------------------------------------

MUMBAI_CHAAT = [
    {"name": "Juhu Beach Chaat Stalls", "lat": 19.0988, "lon": 72.8267, "Area": "Juhu", "Specialty": "Pav bhaji, bhel puri, pani puri, sev puri", "Hours": "Evening to midnight", "Price Range": "30-100 INR", "color": "red"},
    {"name": "Ashok Vada Pav (Kirti College)", "lat": 19.1078, "lon": 72.8358, "Area": "Andheri", "Specialty": "Original Mumbai vada pav since 1970s", "Hours": "7am-10pm", "Price Range": "15-30 INR", "color": "darkred"},
    {"name": "Chowpatty Beach", "lat": 18.9555, "lon": 72.8137, "Area": "Marine Drive", "Specialty": "Kulfi falooda, bhel puri, pav bhaji, gola", "Hours": "Evening to midnight", "Price Range": "30-150 INR", "color": "red"},
    {"name": "Churchgate Khau Galli", "lat": 18.9350, "lon": 72.8275, "Area": "Churchgate", "Specialty": "Frankies, sandwiches, Chinese bhel, vada pav", "Hours": "Lunch to evening", "Price Range": "30-100 INR", "color": "orange"},
    {"name": "Mohammad Ali Road", "lat": 18.9600, "lon": 72.8360, "Area": "Bhendi Bazaar", "Specialty": "Kebabs, malpua, rabri, nihari (Ramadan specials)", "Hours": "Evening to late night", "Price Range": "50-200 INR", "color": "darkred"},
    {"name": "Crawford Market Area", "lat": 18.9475, "lon": 72.8365, "Area": "Fort", "Specialty": "Fresh juice carts, falooda, chaat, samosa", "Hours": "Daily 8am-8pm", "Price Range": "20-80 INR", "color": "orange"},
    {"name": "Dadar Station Vendors", "lat": 19.0183, "lon": 72.8427, "Area": "Dadar", "Specialty": "Vada pav, misal pav, poha, cutting chai", "Hours": "Early morning to evening", "Price Range": "10-50 INR", "color": "orange"},
    {"name": "VT (CST) Station Stalls", "lat": 18.9402, "lon": 72.8360, "Area": "Fort", "Specialty": "Samosa pav, vada pav, kanda bhaji, chai", "Hours": "All day", "Price Range": "10-40 INR", "color": "orange"},
    {"name": "Ghatkopar Khau Galli", "lat": 19.0866, "lon": 72.9081, "Area": "Ghatkopar", "Specialty": "Ragda pattice, dahi puri, sev puri, dabeli", "Hours": "Evening to 11pm", "Price Range": "30-80 INR", "color": "red"},
    {"name": "Linking Road Snack Vendors", "lat": 19.0680, "lon": 72.8325, "Area": "Bandra", "Specialty": "Frankies, shawarma, ice gola, momos", "Hours": "Afternoon to midnight", "Price Range": "30-120 INR", "color": "red"},
    {"name": "Andheri Station East Food Lane", "lat": 19.1190, "lon": 72.8467, "Area": "Andheri", "Specialty": "Vada pav, Schezwan dosa, Chinese bhel", "Hours": "All day", "Price Range": "20-80 INR", "color": "orange"},
    {"name": "Tardeo Jain Chaat Corner", "lat": 18.9710, "lon": 72.8130, "Area": "Tardeo", "Specialty": "Jain-style pani puri, dahi puri, bhel", "Hours": "4pm-10pm", "Price Range": "40-80 INR", "color": "orange"},
    {"name": "Khau Galli (Ghatkopar East)", "lat": 19.0870, "lon": 72.9150, "Area": "Ghatkopar", "Specialty": "Gujarati farsan, dabeli, handvo, fafda-jalebi", "Hours": "Morning to evening", "Price Range": "20-80 INR", "color": "red"},
    {"name": "Bandra Reclamation Food Trucks", "lat": 19.0520, "lon": 72.8300, "Area": "Bandra", "Specialty": "Gourmet burgers, fusion tacos, artisan pizza", "Hours": "Evening to midnight", "Price Range": "100-300 INR", "color": "red"},
    {"name": "Haji Ali Juice Centre", "lat": 18.9820, "lon": 72.8120, "Area": "Mahalaxmi", "Specialty": "Fresh fruit juices, milkshakes, falooda", "Hours": "5am-1:30am", "Price Range": "50-200 INR", "color": "darkred"},
]

# ---------------------------------------------------------------------------
# DATA: Marrakech Food Stalls
# ---------------------------------------------------------------------------

MARRAKECH_FOOD = [
    {"name": "Jemaa el-Fnaa Night Market", "lat": 31.6258, "lon": -7.9891, "Area": "Medina", "Specialty": "Sheep head, snails, harira, grilled meats, fresh juice", "Hours": "Sunset to midnight", "Price Range": "10-60 MAD", "color": "darkred"},
    {"name": "Jemaa el-Fnaa Orange Juice Row", "lat": 31.6255, "lon": -7.9885, "Area": "Medina", "Specialty": "Fresh-squeezed orange juice, pomegranate juice", "Hours": "All day", "Price Range": "4-10 MAD", "color": "orange"},
    {"name": "Souk Semmarine Snack Vendors", "lat": 31.6310, "lon": -7.9870, "Area": "Souks", "Specialty": "Msemen, baghrir, almond pastries, mint tea", "Hours": "Daily 9am-8pm", "Price Range": "5-30 MAD", "color": "orange"},
    {"name": "Rue Bani Marine Street Food", "lat": 31.6280, "lon": -7.9870, "Area": "Medina", "Specialty": "Tangia, mechoui, fried sardines, brochettes", "Hours": "Lunch to evening", "Price Range": "20-60 MAD", "color": "red"},
    {"name": "Mellah (Jewish Quarter) Market", "lat": 31.6205, "lon": -7.9855, "Area": "Mellah", "Specialty": "Dried fruits, nuts, spice mixes, preserved lemons", "Hours": "Daily 8am-7pm", "Price Range": "10-50 MAD", "color": "orange"},
    {"name": "Bab Doukkala Food Street", "lat": 31.6340, "lon": -7.9990, "Area": "Bab Doukkala", "Specialty": "Tajine, kefta sandwiches, boiled chickpeas", "Hours": "Lunch to evening", "Price Range": "15-50 MAD", "color": "red"},
    {"name": "Derb Dabachi Hole-in-the-Wall", "lat": 31.6230, "lon": -7.9920, "Area": "Derb Dabachi", "Specialty": "Tanjia (slow-cooked in hammam ashes)", "Hours": "Lunch", "Price Range": "40-80 MAD", "color": "darkred"},
    {"name": "Marche Central (Gueliz)", "lat": 31.6370, "lon": -8.0080, "Area": "Gueliz", "Specialty": "Fresh seafood, rotisserie chicken, olive stalls", "Hours": "Daily 7am-2pm", "Price Range": "20-80 MAD", "color": "orange"},
    {"name": "Bab Ighli Cart Row", "lat": 31.6150, "lon": -7.9920, "Area": "Bab Ighli", "Specialty": "Bissara (fava bean soup), bread, harira", "Hours": "Early morning", "Price Range": "5-15 MAD", "color": "orange"},
    {"name": "Mouassine Quarter Vendors", "lat": 31.6310, "lon": -7.9930, "Area": "Mouassine", "Specialty": "Rfissa, pastilla, zaalouk, mint tea", "Hours": "Daily 10am-8pm", "Price Range": "10-40 MAD", "color": "red"},
    {"name": "Sidi Mimoun Gate Grills", "lat": 31.6120, "lon": -7.9850, "Area": "Kasbah", "Specialty": "Lamb brochettes, merguez, kofta sandwiches", "Hours": "Evening to midnight", "Price Range": "20-50 MAD", "color": "red"},
    {"name": "Arset El Maach Bread Ovens", "lat": 31.6270, "lon": -7.9950, "Area": "Medina", "Specialty": "Khobz (communal oven bread), msemen, beghrir", "Hours": "Early morning", "Price Range": "2-10 MAD", "color": "orange"},
    {"name": "Rahba Lakdima Spice Square", "lat": 31.6300, "lon": -7.9870, "Area": "Souks", "Specialty": "Ras el hanout, dried herbs, natural cosmetics", "Hours": "Daily 9am-7pm", "Price Range": "10-100 MAD", "color": "orange"},
    {"name": "Bab el-Khemis Flea Market Eats", "lat": 31.6380, "lon": -7.9780, "Area": "Bab el-Khemis", "Specialty": "Fried fish, roasted corn, snail soup", "Hours": "Thu morning", "Price Range": "10-40 MAD", "color": "red"},
    {"name": "Jemaa el-Fnaa Snail Soup Stalls", "lat": 31.6260, "lon": -7.9895, "Area": "Medina", "Specialty": "Babouche (spiced snail broth), herbal infusion", "Hours": "Afternoon to midnight", "Price Range": "5-15 MAD", "color": "darkred"},
]

# ---------------------------------------------------------------------------
# DATA: Singapore Hawker Centers
# ---------------------------------------------------------------------------

SINGAPORE_HAWKER = [
    {"name": "Maxwell Food Centre", "lat": 1.2804, "lon": 103.8448, "Area": "Chinatown", "Specialty": "Tian Tian chicken rice, char kway teow, fried hokkien mee", "Hours": "Daily 8am-2am", "Price Range": "3-8 SGD", "color": "red"},
    {"name": "Lau Pa Sat (Telok Ayer Market)", "lat": 1.2806, "lon": 103.8504, "Area": "CBD", "Specialty": "Satay street, nasi lemak, rojak, laksa", "Hours": "Daily 24 hours", "Price Range": "4-12 SGD", "color": "red"},
    {"name": "Newton Food Centre", "lat": 1.3121, "lon": 103.8389, "Area": "Newton", "Specialty": "Chilli crab, BBQ sambal stingray, oyster omelette", "Hours": "Daily noon-2am", "Price Range": "5-25 SGD", "color": "darkred"},
    {"name": "Chinatown Complex Food Centre", "lat": 1.2823, "lon": 103.8434, "Area": "Chinatown", "Specialty": "Hong Kong soya sauce chicken (Hawker Chan), carrot cake", "Hours": "Daily 6am-10pm", "Price Range": "2-6 SGD", "color": "darkred"},
    {"name": "Old Airport Road Food Centre", "lat": 1.3084, "lon": 103.8834, "Area": "Geylang", "Specialty": "Fried carrot cake, bak chor mee, rojak, lontong", "Hours": "Daily 6am-11pm", "Price Range": "3-8 SGD", "color": "red"},
    {"name": "Tiong Bahru Market", "lat": 1.2840, "lon": 103.8311, "Area": "Tiong Bahru", "Specialty": "Chwee kueh, lor mee, pork congee", "Hours": "Daily 6am-10pm", "Price Range": "2-6 SGD", "color": "orange"},
    {"name": "Tekka Centre (Little India)", "lat": 1.3068, "lon": 103.8503, "Area": "Little India", "Specialty": "Roti prata, biryani, fish head curry, murtabak", "Hours": "Daily 6:30am-9pm", "Price Range": "3-10 SGD", "color": "red"},
    {"name": "East Coast Lagoon Food Village", "lat": 1.3025, "lon": 103.9290, "Area": "East Coast", "Specialty": "Satay, BBQ chicken wings, laksa, mee goreng", "Hours": "Daily 11am-midnight", "Price Range": "3-10 SGD", "color": "orange"},
    {"name": "Chomp Chomp Food Centre", "lat": 1.3637, "lon": 103.8683, "Area": "Serangoon", "Specialty": "BBQ stingray, satay, hokkien mee, carrot cake", "Hours": "Evening to midnight", "Price Range": "4-12 SGD", "color": "red"},
    {"name": "Amoy Street Food Centre", "lat": 1.2806, "lon": 103.8466, "Area": "CBD", "Specialty": "A Noodle Story (Michelin), thunder tea rice, popiah", "Hours": "Daily 7am-3pm", "Price Range": "3-8 SGD", "color": "darkred"},
    {"name": "Zion Riverside Food Centre", "lat": 1.2898, "lon": 103.8309, "Area": "River Valley", "Specialty": "Famous fried kway teow, lor mee, chai tow kway", "Hours": "Daily 6am-10pm", "Price Range": "3-7 SGD", "color": "orange"},
    {"name": "Adam Road Food Centre", "lat": 1.3242, "lon": 103.8138, "Area": "Bukit Timah", "Specialty": "Nasi lemak, Malay classics, teh tarik", "Hours": "Daily 7am-3pm", "Price Range": "3-8 SGD", "color": "orange"},
    {"name": "Ghim Moh Market & Food Centre", "lat": 1.3104, "lon": 103.7871, "Area": "Buona Vista", "Specialty": "Wanton mee, fish soup, economic rice, kueh", "Hours": "Daily 6am-2pm", "Price Range": "3-6 SGD", "color": "orange"},
    {"name": "Hong Lim Market & Food Centre", "lat": 1.2849, "lon": 103.8449, "Area": "Chinatown", "Specialty": "Famous lor mee, Soon Kueh, boneless duck rice", "Hours": "Daily 6am-8pm", "Price Range": "3-7 SGD", "color": "red"},
    {"name": "Whampoa Makan Place", "lat": 1.3235, "lon": 103.8572, "Area": "Whampoa", "Specialty": "Roasted meats, fishball noodles, Teochew porridge", "Hours": "Daily 6am-midnight", "Price Range": "3-8 SGD", "color": "orange"},
]

# ---------------------------------------------------------------------------
# DATA: Tokyo Yokocho Alleys
# ---------------------------------------------------------------------------

TOKYO_YOKOCHO = [
    {"name": "Omoide Yokocho (Memory Lane)", "lat": 35.6940, "lon": 139.6988, "Area": "Shinjuku", "Specialty": "Yakitori, motsu-yaki, shochu, beer", "Hours": "5pm-midnight", "Price Range": "500-2000 JPY", "color": "red"},
    {"name": "Golden Gai", "lat": 35.6935, "lon": 139.7030, "Area": "Shinjuku", "Specialty": "Tiny 6-seat bars, sake, whisky, light bites", "Hours": "8pm-late", "Price Range": "500-3000 JPY", "color": "darkred"},
    {"name": "Hoppy Street (Hoppy Dori)", "lat": 35.7125, "lon": 139.7940, "Area": "Asakusa", "Specialty": "Beef stew, oden, nikomi, hoppy beer", "Hours": "3pm-midnight", "Price Range": "300-1500 JPY", "color": "red"},
    {"name": "Yurakucho Under-Rail Izakayas", "lat": 35.6747, "lon": 139.7630, "Area": "Yurakucho", "Specialty": "Yakitori under rail tracks, beer, edamame", "Hours": "4pm-midnight", "Price Range": "300-2000 JPY", "color": "red"},
    {"name": "Harmonica Yokocho (Kichijoji)", "lat": 35.7035, "lon": 139.5797, "Area": "Kichijoji", "Specialty": "Ramen, gyoza, izakaya snacks, matcha sweets", "Hours": "11am-midnight", "Price Range": "400-1500 JPY", "color": "orange"},
    {"name": "Ameyoko Market Street", "lat": 35.7102, "lon": 139.7740, "Area": "Ueno", "Specialty": "Fresh seafood, taiyaki, kebab, chocolate banana", "Hours": "Daily 10am-7pm", "Price Range": "200-1500 JPY", "color": "red"},
    {"name": "Tsukishima Monja Street", "lat": 35.6604, "lon": 139.7798, "Area": "Tsukishima", "Specialty": "Monjayaki (Tokyo-style savory pancake)", "Hours": "11am-10pm", "Price Range": "800-1500 JPY", "color": "orange"},
    {"name": "Nakano Broadway Snack Zone", "lat": 35.7074, "lon": 139.6655, "Area": "Nakano", "Specialty": "Soft-serve ice cream, takoyaki, crepes, ramen", "Hours": "Daily noon-8pm", "Price Range": "300-1000 JPY", "color": "orange"},
    {"name": "Ebisu Yokocho", "lat": 35.6468, "lon": 139.7102, "Area": "Ebisu", "Specialty": "Small plates, grilled meats, craft beer, sake", "Hours": "5pm-midnight", "Price Range": "500-2000 JPY", "color": "red"},
    {"name": "Nonbei Yokocho (Drunkards Alley)", "lat": 35.6583, "lon": 139.7023, "Area": "Shibuya", "Specialty": "Tiny standing bars, oden, yakitori, sake", "Hours": "6pm-late", "Price Range": "500-2500 JPY", "color": "darkred"},
    {"name": "Togoshi Ginza Shotengai", "lat": 35.6143, "lon": 139.7166, "Area": "Shinagawa", "Specialty": "Croquettes, taiyaki, onigiri, yakisoba", "Hours": "Daily 10am-8pm", "Price Range": "100-800 JPY", "color": "orange"},
    {"name": "Sunamachi Ginza Shotengai", "lat": 35.6861, "lon": 139.8362, "Area": "Koto", "Specialty": "Tempura, oden, senbei, old-school sweets", "Hours": "Daily 10am-6pm", "Price Range": "100-600 JPY", "color": "orange"},
    {"name": "Yanaka Ginza", "lat": 35.7258, "lon": 139.7674, "Area": "Yanaka", "Specialty": "Menchi katsu, yakisoba bread, senbei, cat-tail donuts", "Hours": "Daily 10am-7pm", "Price Range": "100-600 JPY", "color": "orange"},
    {"name": "Ramen Street (Tokyo Station)", "lat": 35.6812, "lon": 139.7671, "Area": "Marunouchi", "Specialty": "Eight curated top ramen shops under one roof", "Hours": "Daily 11am-11pm", "Price Range": "800-1500 JPY", "color": "darkred"},
    {"name": "Sangenjaya Triangle", "lat": 35.6434, "lon": 139.6695, "Area": "Setagaya", "Specialty": "Gyoza, ramen, standing bars, craft sake", "Hours": "5pm-midnight", "Price Range": "400-1500 JPY", "color": "red"},
]

# ---------------------------------------------------------------------------
# DATA: New York City Hot Dog & Pizza
# ---------------------------------------------------------------------------

NYC_STREET_FOOD = [
    {"name": "Papaya King (86th St)", "lat": 40.7788, "lon": -73.9543, "Area": "Upper East Side", "Specialty": "Hot dogs and tropical fruit drinks since 1932", "Hours": "Daily 8am-midnight", "Price Range": "$3-8", "color": "red"},
    {"name": "Joe's Pizza (Greenwich Village)", "lat": 40.7306, "lon": -74.0021, "Area": "Greenwich Village", "Specialty": "Classic New York thin-crust cheese slice", "Hours": "Daily 10am-5am", "Price Range": "$3-6", "color": "darkred"},
    {"name": "Di Fara Pizza", "lat": 40.6250, "lon": -73.9613, "Area": "Midwood, Brooklyn", "Specialty": "Legendary hand-crafted pizza since 1965", "Hours": "Wed-Sun noon-closing", "Price Range": "$5-35", "color": "darkred"},
    {"name": "The Halal Guys (53rd & 6th)", "lat": 40.7643, "lon": -73.9797, "Area": "Midtown", "Specialty": "Chicken & gyro over rice, white sauce, hot sauce", "Hours": "Daily 10am-4am", "Price Range": "$8-12", "color": "red"},
    {"name": "Gray's Papaya (72nd St)", "lat": 40.7804, "lon": -73.9802, "Area": "Upper West Side", "Specialty": "Hot dogs and papaya juice", "Hours": "Daily 24 hours", "Price Range": "$3-7", "color": "red"},
    {"name": "Prince Street Pizza", "lat": 40.7231, "lon": -73.9948, "Area": "Nolita", "Specialty": "Pepperoni square slice (spicy spring), soho style", "Hours": "Daily 11am-11pm", "Price Range": "$4-7", "color": "darkred"},
    {"name": "Smorgasburg (Williamsburg)", "lat": 40.7215, "lon": -73.9617, "Area": "Williamsburg", "Specialty": "100+ food vendors, ramen burger, artisan tacos", "Hours": "Sat 11am-6pm (seasonal)", "Price Range": "$5-18", "color": "red"},
    {"name": "Nathan's Famous (Coney Island)", "lat": 40.5756, "lon": -73.9814, "Area": "Coney Island", "Specialty": "Original hot dog since 1916, crinkle-cut fries", "Hours": "Daily 10am-midnight", "Price Range": "$4-12", "color": "darkred"},
    {"name": "L&B Spumoni Gardens", "lat": 40.5942, "lon": -73.9814, "Area": "Gravesend, Brooklyn", "Specialty": "Sicilian square pizza, spumoni ice cream since 1939", "Hours": "Daily 11am-10pm", "Price Range": "$4-20", "color": "red"},
    {"name": "Xi'an Famous Foods", "lat": 40.7564, "lon": -73.9876, "Area": "Midtown", "Specialty": "Hand-pulled noodles, spicy cumin lamb, liang pi", "Hours": "Daily 11am-9pm", "Price Range": "$8-15", "color": "red"},
    {"name": "Jackson Heights Food Carts", "lat": 40.7467, "lon": -73.8912, "Area": "Jackson Heights, Queens", "Specialty": "Arepa, pupusa, Tibetan momos, South Asian chaat", "Hours": "Daily all day", "Price Range": "$3-10", "color": "orange"},
    {"name": "Scarr's Pizza (LES)", "lat": 40.7161, "lon": -73.9909, "Area": "Lower East Side", "Specialty": "Wood-fired pizza with house-milled flour", "Hours": "Daily noon-midnight", "Price Range": "$4-7", "color": "darkred"},
    {"name": "Red Hook Ball Fields (Vendors)", "lat": 40.6741, "lon": -74.0075, "Area": "Red Hook, Brooklyn", "Specialty": "Latin American huaraches, pupusas, tacos, elote", "Hours": "Sat-Sun 10am-dusk (seasonal)", "Price Range": "$5-12", "color": "orange"},
    {"name": "Flushing Night Market", "lat": 40.7549, "lon": -73.8302, "Area": "Flushing, Queens", "Specialty": "East Asian street food, skewers, bubble tea, pancakes", "Hours": "Sat evening (seasonal)", "Price Range": "$3-12", "color": "red"},
    {"name": "Sahadi's & Atlantic Ave Carts", "lat": 40.6862, "lon": -73.9880, "Area": "Boerum Hill, Brooklyn", "Specialty": "Middle Eastern falafel, shawarma, knafeh, baklava", "Hours": "Daily", "Price Range": "$5-15", "color": "orange"},
]

# ---------------------------------------------------------------------------
# DATA: Penang Street Food
# ---------------------------------------------------------------------------

PENANG_STREET_FOOD = [
    {"name": "Gurney Drive Hawker Centre", "lat": 5.4370, "lon": 100.3100, "Area": "Gurney Drive", "Specialty": "Char kway teow, laksa, rojak, pasembur", "Hours": "Evening to midnight", "Price Range": "5-15 MYR", "color": "red"},
    {"name": "New Lane (Lorong Baru) Hawkers", "lat": 5.4135, "lon": 100.3310, "Area": "George Town", "Specialty": "Fried oyster, char kway teow, economy rice", "Hours": "Evening to midnight", "Price Range": "4-12 MYR", "color": "red"},
    {"name": "Kimberly Street (Lebuh Kimberley)", "lat": 5.4168, "lon": 100.3370, "Area": "George Town", "Specialty": "Duck rice, koay chiap, fried kway teow, popiah", "Hours": "Evening to 11pm", "Price Range": "5-15 MYR", "color": "darkred"},
    {"name": "Chulia Street Night Hawkers", "lat": 5.4144, "lon": 100.3400, "Area": "George Town", "Specialty": "Nasi kandar, roti canai, mee goreng, satay", "Hours": "Evening to midnight", "Price Range": "3-12 MYR", "color": "red"},
    {"name": "Cecil Street Market", "lat": 5.4120, "lon": 100.3420, "Area": "George Town", "Specialty": "Hokkien mee, char kway teow, ice kacang", "Hours": "Morning to afternoon", "Price Range": "4-10 MYR", "color": "orange"},
    {"name": "Air Itam Laksa (Assam Laksa)", "lat": 5.3980, "lon": 100.2850, "Area": "Air Itam", "Specialty": "Famous Penang assam laksa (sour fish noodle soup)", "Hours": "Daily 9am-5pm", "Price Range": "5-8 MYR", "color": "darkred"},
    {"name": "Padang Brown Hawker Centre", "lat": 5.4165, "lon": 100.3155, "Area": "George Town", "Specialty": "Koay teow th'ng, Malay kuih, nasi lemak", "Hours": "Morning to afternoon", "Price Range": "3-10 MYR", "color": "orange"},
    {"name": "Pulau Tikus Market", "lat": 5.4295, "lon": 100.3105, "Area": "Pulau Tikus", "Specialty": "Dim sum, popiah, yam cake, Nyonya kuih", "Hours": "Morning to noon", "Price Range": "3-10 MYR", "color": "orange"},
    {"name": "Tek Sen Restaurant (Carnarvon St)", "lat": 5.4170, "lon": 100.3370, "Area": "George Town", "Specialty": "Double-roasted pork, claypot noodles, stir fry", "Hours": "Lunch & dinner (closed Mon)", "Price Range": "8-25 MYR", "color": "darkred"},
    {"name": "Transfer Road Roti Canai", "lat": 5.4120, "lon": 100.3310, "Area": "George Town", "Specialty": "Roti canai with rich dhal and fish curry", "Hours": "Morning to noon", "Price Range": "2-5 MYR", "color": "orange"},
    {"name": "Penang Road Famous Teochew Chendul", "lat": 5.4170, "lon": 100.3310, "Area": "George Town", "Specialty": "Iced chendul with gula melaka, red beans, coconut milk", "Hours": "Daily 10am-7pm", "Price Range": "3-5 MYR", "color": "darkred"},
    {"name": "Siam Road Char Kway Teow", "lat": 5.4210, "lon": 100.3250, "Area": "George Town", "Specialty": "Charcoal-fried flat rice noodles with cockles and lap cheong", "Hours": "Afternoon to evening", "Price Range": "6-10 MYR", "color": "darkred"},
    {"name": "Batu Lanchang Market", "lat": 5.3990, "lon": 100.3110, "Area": "Batu Lanchang", "Specialty": "Curry mee, prawn mee, nasi lemak bungkus", "Hours": "Morning to afternoon", "Price Range": "4-10 MYR", "color": "orange"},
    {"name": "Tanjung Bungah Floating Mosque Stalls", "lat": 5.4590, "lon": 100.2790, "Area": "Tanjung Bungah", "Specialty": "Pasembur, mee udang, grilled fish, coconut shake", "Hours": "Evening to 10pm", "Price Range": "5-15 MYR", "color": "red"},
    {"name": "Balik Pulau Town Hawkers", "lat": 5.3560, "lon": 100.2290, "Area": "Balik Pulau", "Specialty": "Laksa, nutmeg juice, durian, belacan fried rice", "Hours": "Morning to afternoon", "Price Range": "3-10 MYR", "color": "orange"},
]

# ---------------------------------------------------------------------------
# DATA: Seoul Pojangmacha
# ---------------------------------------------------------------------------

SEOUL_POJANGMACHA = [
    {"name": "Gwangjang Market", "lat": 37.5700, "lon": 126.9993, "Area": "Jongno-gu", "Specialty": "Bindaetteok, mayak gimbap, yukhoe, tteokbokki", "Hours": "Daily 9am-11pm", "Price Range": "3,000-15,000 KRW", "color": "darkred"},
    {"name": "Myeongdong Street Food Alley", "lat": 37.5636, "lon": 126.9850, "Area": "Jung-gu", "Specialty": "Egg bread, tornado potato, hotteok, mozzarella corn dogs", "Hours": "Daily 11am-10pm", "Price Range": "1,000-5,000 KRW", "color": "red"},
    {"name": "Namdaemun Market Food Lane", "lat": 37.5593, "lon": 126.9775, "Area": "Jung-gu", "Specialty": "Kalguksu, japchae, hotteok, bindaetteok", "Hours": "Daily 5am-midnight", "Price Range": "3,000-10,000 KRW", "color": "red"},
    {"name": "Jongno 3-ga Pojangmacha Row", "lat": 37.5710, "lon": 126.9920, "Area": "Jongno-gu", "Specialty": "Soju tent bars, odeng, dakkochi, tteokbokki", "Hours": "Evening to 3am", "Price Range": "3,000-15,000 KRW", "color": "darkred"},
    {"name": "Euljiro Tent Bars (Hipjiro)", "lat": 37.5663, "lon": 126.9920, "Area": "Jung-gu", "Specialty": "Retro tent bars, somaek, fried chicken, sundae", "Hours": "Evening to late night", "Price Range": "5,000-20,000 KRW", "color": "red"},
    {"name": "Tongin Market (Dosirak Cafe)", "lat": 37.5754, "lon": 126.9700, "Area": "Jongno-gu", "Specialty": "Lunch-box cafe with traditional coins, tteok-galbi", "Hours": "Daily 9am-6pm", "Price Range": "5,000-10,000 KRW", "color": "orange"},
    {"name": "Sindang-dong Tteokbokki Town", "lat": 37.5660, "lon": 127.0100, "Area": "Jung-gu", "Specialty": "Spicy rice cake alley, rabokki, chewy tteok", "Hours": "Daily 11am-1am", "Price Range": "5,000-12,000 KRW", "color": "darkred"},
    {"name": "Dongdaemun Night Food Stalls", "lat": 37.5667, "lon": 127.0087, "Area": "Jung-gu", "Specialty": "Grilled skewers, sundae, odeng, fish cake soup", "Hours": "Evening to 4am", "Price Range": "2,000-10,000 KRW", "color": "red"},
    {"name": "Mangwon Market", "lat": 37.5560, "lon": 126.9085, "Area": "Mapo-gu", "Specialty": "Mandu, tteokbokki, fresh juice, artisan bakes", "Hours": "Daily 8am-9pm", "Price Range": "2,000-8,000 KRW", "color": "orange"},
    {"name": "Noryangjin Fish Market", "lat": 37.5127, "lon": 126.9405, "Area": "Dongjak-gu", "Specialty": "Live sashimi, grilled seafood, spicy fish stew", "Hours": "Daily 24 hours", "Price Range": "10,000-40,000 KRW", "color": "darkred"},
    {"name": "Ikseon-dong Hanok Snack Alley", "lat": 37.5735, "lon": 126.9910, "Area": "Jongno-gu", "Specialty": "Hotteok, egg tart, dalgona coffee, bingsu", "Hours": "Daily 10am-10pm", "Price Range": "3,000-10,000 KRW", "color": "orange"},
    {"name": "Hongdae Street Food Zone", "lat": 37.5563, "lon": 126.9232, "Area": "Mapo-gu", "Specialty": "Corn dogs, churros, takoyaki, crepes, bubble waffles", "Hours": "Afternoon to midnight", "Price Range": "2,000-6,000 KRW", "color": "red"},
    {"name": "Itaewon Global Food Alley", "lat": 37.5345, "lon": 126.9945, "Area": "Yongsan-gu", "Specialty": "Kebabs, shawarma, pad thai, craft tacos", "Hours": "Daily noon to late night", "Price Range": "5,000-15,000 KRW", "color": "orange"},
    {"name": "Bukchon Hanok Village Vendors", "lat": 37.5828, "lon": 126.9850, "Area": "Jongno-gu", "Specialty": "Traditional rice cake, sikhye, sweet pancakes", "Hours": "Daily 10am-6pm", "Price Range": "2,000-5,000 KRW", "color": "orange"},
    {"name": "Yeouido Pojangmacha (Han River)", "lat": 37.5283, "lon": 126.9345, "Area": "Yeongdeungpo-gu", "Specialty": "Fried chicken & beer, ramyeon, grilled meats by river", "Hours": "Evening to midnight", "Price Range": "5,000-20,000 KRW", "color": "red"},
]


# ---------------------------------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------------------------------

def render_street_food_maps_tab():
    """Render the Street Food World Explorer tab."""
    st.markdown(
        '<div class="tab-header pink"><h4>\U0001f35c Street Food World Explorer</h4>'
        '<p>Explore legendary street food destinations, hawker centres, night markets &amp; food alleys across the globe</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        [
            "Bangkok Street Food",
            "Mexico City Tacos",
            "Istanbul Street Food",
            "Mumbai Chaat & Vada Pav",
            "Marrakech Food Stalls",
            "Singapore Hawker Centers",
            "Tokyo Yokocho Alleys",
            "New York City Hot Dog & Pizza",
            "Penang Street Food",
            "Seoul Pojangmacha",
        ],
        key="street_food_maps_mode",
    )

    # -----------------------------------------------------------------
    # MODE: Bangkok Street Food
    # -----------------------------------------------------------------
    if mode == "Bangkok Street Food":
        data = BANGKOK_STREET_FOOD
        st.markdown("### Bangkok Street Food")
        st.markdown(
            "Bangkok is the undisputed street food capital of the world.  From "
            "the sizzling woks of Yaowarat (Chinatown) to the sprawling stalls "
            "of Chatuchak Weekend Market, the city offers an endless stream of "
            "flavours at astonishingly low prices.  Jay Fai earned a Michelin "
            "star while cooking over charcoal on the pavement, and the ubiquitous "
            "pad thai carts serve what many consider the planet's perfect noodle "
            "dish.  Eating on the street is not just common in Bangkok -- it is "
            "the very heartbeat of the city's food culture."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spots Mapped", len(data))
        c2.metric("Michelin Street Food", "Jay Fai + Thip Samai")
        c3.metric("Cheapest Dish", "~20 THB ($0.55)")
        c4.metric("Best Time", "Evening to midnight")

        st.markdown("---")
        st.markdown("##### Area Breakdown")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        ac1, ac2, ac3 = st.columns(3)
        for col, (area, cnt) in zip([ac1, ac2, ac3], sorted_areas[:3]):
            col.metric(area, f"{cnt} spots")

        _show_map_and_data(data, zoom=12, center=[13.755, 100.510], csv_prefix="bangkok_street_food")

    # -----------------------------------------------------------------
    # MODE: Mexico City Tacos
    # -----------------------------------------------------------------
    elif mode == "Mexico City Tacos":
        data = MEXICO_CITY_TACOS
        st.markdown("### Mexico City Tacos")
        st.markdown(
            "Mexico City is taco heaven.  Virtually every street corner has a "
            "taqueria, and locals debate fiercely over who makes the best tacos "
            "al pastor -- the spit-roasted, Lebanese-influenced pork that has "
            "become the city's signature dish.  Tacos de canasta (basket tacos) "
            "cost as little as 5 pesos, while upscale spots like El Califa de "
            "Leon hold a Michelin Bib Gourmand.  Markets like La Merced and San "
            "Juan burst with quesadillas, tlacoyos, and tamales from dawn until "
            "well after dark."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spots Mapped", len(data))
        c2.metric("Iconic Dish", "Tacos al Pastor")
        c3.metric("Cheapest Taco", "~5 MXN ($0.28)")
        c4.metric("Taco Capital Since", "Pre-Columbian era")

        st.markdown("---")
        st.markdown("##### Neighbourhood Spread")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        nc1, nc2, nc3 = st.columns(3)
        for col, (area, cnt) in zip([nc1, nc2, nc3], sorted_areas[:3]):
            col.metric(area, f"{cnt} spots")

        _show_map_and_data(data, zoom=12, center=[19.425, -99.155], csv_prefix="mexico_city_tacos")

    # -----------------------------------------------------------------
    # MODE: Istanbul Street Food
    # -----------------------------------------------------------------
    elif mode == "Istanbul Street Food":
        data = ISTANBUL_STREET_FOOD
        st.markdown("### Istanbul Street Food")
        st.markdown(
            "Straddling two continents, Istanbul's street food scene draws from "
            "both European and Asian culinary traditions.  The iconic simit -- a "
            "sesame-encrusted bread ring -- is sold from crimson carts on every "
            "corner.  At Eminonu, fishermen grill mackerel on rocking boats and "
            "serve balik ekmek to queues that never end.  The towering doner "
            "kebabs of Taksim, the stuffed mussels (midye dolma) of Beyoglu, "
            "and the legendary baklava of Karakoy Gulluoglu make Istanbul one "
            "of the world's greatest cities for eating on the go."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spots Mapped", len(data))
        c2.metric("Signature Snack", "Simit + Balik Ekmek")
        c3.metric("Baklava Since", "1871 (Gulluoglu)")
        c4.metric("Two Continents", "Europe & Asia")

        st.markdown("---")
        st.markdown("##### District Distribution")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        dc1, dc2, dc3 = st.columns(3)
        for col, (area, cnt) in zip([dc1, dc2, dc3], sorted_areas[:3]):
            col.metric(area, f"{cnt} spots")

        _show_map_and_data(data, zoom=12, center=[41.025, 28.980], csv_prefix="istanbul_street_food")

    # -----------------------------------------------------------------
    # MODE: Mumbai Chaat & Vada Pav
    # -----------------------------------------------------------------
    elif mode == "Mumbai Chaat & Vada Pav":
        data = MUMBAI_CHAAT
        st.markdown("### Mumbai Chaat & Vada Pav")
        st.markdown(
            "Mumbai runs on vada pav -- the spiced potato fritter sandwich that "
            "costs as little as 15 rupees and fuels millions of commuters daily.  "
            "The city's beaches (Juhu, Chowpatty) come alive each evening with "
            "chaat vendors serving bhel puri, pani puri, and sev puri in a "
            "symphony of sweet, sour, spicy and crunchy.  Mohammad Ali Road "
            "transforms during Ramadan into a mile-long open-air feast of kebabs "
            "and malpua.  From station-side cutting chai to the legendary Haji "
            "Ali Juice Centre, Mumbai's street food is inseparable from the "
            "rhythm of the city."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spots Mapped", len(data))
        c2.metric("Iconic Dish", "Vada Pav (~15 INR)")
        c3.metric("Beach Chaat Capital", "Juhu & Chowpatty")
        c4.metric("Best Season", "Oct-Mar (post-monsoon)")

        st.markdown("---")
        st.markdown("##### Area Highlights")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        mc1, mc2, mc3 = st.columns(3)
        for col, (area, cnt) in zip([mc1, mc2, mc3], sorted_areas[:3]):
            col.metric(area, f"{cnt} spots")

        _show_map_and_data(data, zoom=12, center=[19.02, 72.85], csv_prefix="mumbai_chaat")

    # -----------------------------------------------------------------
    # MODE: Marrakech Food Stalls
    # -----------------------------------------------------------------
    elif mode == "Marrakech Food Stalls":
        data = MARRAKECH_FOOD
        st.markdown("### Marrakech Food Stalls")
        st.markdown(
            "As the sun sets over the Medina, Jemaa el-Fnaa transforms into one "
            "of the world's most extraordinary open-air restaurants.  Numbered "
            "stalls serve everything from slow-cooked sheep head and snail soup "
            "to fresh-squeezed orange juice at four dirhams a glass.  Beyond the "
            "main square, the labyrinthine souks hide hole-in-the-wall tanjia "
            "kitchens (clay-pot lamb slow-cooked in hammam ashes), communal bread "
            "ovens turning out khobz at dawn, and spice-market stalls offering "
            "ras el hanout blends passed down for generations."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spots Mapped", len(data))
        c2.metric("UNESCO Heritage", "Jemaa el-Fnaa")
        c3.metric("Cheapest Juice", "4 MAD ($0.40)")
        c4.metric("Signature Dish", "Tanjia (hammam-cooked)")

        st.markdown("---")
        st.markdown("##### Quarter Distribution")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        mq1, mq2, mq3 = st.columns(3)
        for col, (area, cnt) in zip([mq1, mq2, mq3], sorted_areas[:3]):
            col.metric(area, f"{cnt} spots")

        _show_map_and_data(data, zoom=14, center=[31.627, -7.990], csv_prefix="marrakech_food")

    # -----------------------------------------------------------------
    # MODE: Singapore Hawker Centers
    # -----------------------------------------------------------------
    elif mode == "Singapore Hawker Centers":
        data = SINGAPORE_HAWKER
        st.markdown("### Singapore Hawker Centers")
        st.markdown(
            "Singapore's hawker culture was inscribed on the UNESCO Intangible "
            "Cultural Heritage list in 2020 -- a testament to the central role "
            "these open-air food courts play in the nation's identity.  For as "
            "little as two Singapore dollars, you can eat Michelin-starred soya "
            "sauce chicken at Chinatown Complex (Hawker Chan), world-class char "
            "kway teow at Maxwell, or chilli crab at Newton.  With over 110 "
            "hawker centres island-wide, Singaporeans often eat out three meals "
            "a day, making the hawker centre the true communal dining room of "
            "the city-state."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Centres Mapped", len(data))
        c2.metric("UNESCO Heritage", "2020")
        c3.metric("Cheapest Meal", "~2 SGD ($1.50)")
        c4.metric("Michelin Hawkers", "Hawker Chan, A Noodle Story")

        st.markdown("---")
        st.markdown("##### Regional Spread")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        sc1, sc2, sc3 = st.columns(3)
        for col, (area, cnt) in zip([sc1, sc2, sc3], sorted_areas[:3]):
            col.metric(area, f"{cnt} centres")

        _show_map_and_data(data, zoom=12, center=[1.310, 103.850], csv_prefix="singapore_hawker")

    # -----------------------------------------------------------------
    # MODE: Tokyo Yokocho Alleys
    # -----------------------------------------------------------------
    elif mode == "Tokyo Yokocho Alleys":
        data = TOKYO_YOKOCHO
        st.markdown("### Tokyo Yokocho Alleys")
        st.markdown(
            "Hidden beneath railway arches and tucked into narrow post-war "
            "alleyways, Tokyo's yokocho (side streets) are where the city's "
            "food soul truly lives.  Omoide Yokocho near Shinjuku Station -- "
            "nicknamed 'Piss Alley' -- is a smoky labyrinth of yakitori grills "
            "unchanged since the 1940s.  Golden Gai packs over 200 micro-bars "
            "into six interconnected alleys.  From Ebisu Yokocho's refined small "
            "plates to the old-school shotengai of Togoshi Ginza, these narrow "
            "passages offer an intimate, authentic eating experience that no "
            "modern food hall can replicate."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Alleys Mapped", len(data))
        c2.metric("Oldest Yokocho", "Omoide (1940s)")
        c3.metric("Golden Gai Bars", "200+")
        c4.metric("Cheapest Yakitori", "~100 JPY ($0.70)")

        st.markdown("---")
        st.markdown("##### District Clusters")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        tc1, tc2, tc3 = st.columns(3)
        for col, (area, cnt) in zip([tc1, tc2, tc3], sorted_areas[:3]):
            col.metric(area, f"{cnt} alleys")

        _show_map_and_data(data, zoom=11, center=[35.685, 139.740], csv_prefix="tokyo_yokocho")

    # -----------------------------------------------------------------
    # MODE: New York City Hot Dog & Pizza
    # -----------------------------------------------------------------
    elif mode == "New York City Hot Dog & Pizza":
        data = NYC_STREET_FOOD
        st.markdown("### New York City Hot Dog & Pizza")
        st.markdown(
            "New York's street food identity is built on two pillars: the hot "
            "dog and the pizza slice.  Nathan's has been serving franks at Coney "
            "Island since 1916, while Papaya King and Gray's Papaya perfected "
            "the hot-dog-and-tropical-juice combo uptown.  The dollar slice may "
            "be fading, but Joe's Pizza in the Village and Di Fara in Brooklyn "
            "remain pilgrimage sites.  Beyond the classics, NYC's food carts "
            "and night markets reflect the world's cuisines -- from Halal Guys' "
            "chicken over rice to Jackson Heights' Tibetan momos and Red Hook's "
            "huaraches."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spots Mapped", len(data))
        c2.metric("Nathan's Since", "1916")
        c3.metric("Pizza Slice From", "~$3")
        c4.metric("Street Vendors (city-wide)", "~10,000")

        st.markdown("---")
        st.markdown("##### Borough Breakdown")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        nb1, nb2, nb3 = st.columns(3)
        for col, (area, cnt) in zip([nb1, nb2, nb3], sorted_areas[:3]):
            col.metric(area, f"{cnt} spots")

        _show_map_and_data(data, zoom=11, center=[40.720, -73.960], csv_prefix="nyc_street_food")

    # -----------------------------------------------------------------
    # MODE: Penang Street Food
    # -----------------------------------------------------------------
    elif mode == "Penang Street Food":
        data = PENANG_STREET_FOOD
        st.markdown("### Penang Street Food")
        st.markdown(
            "Penang is consistently ranked among the world's best street food "
            "destinations.  The island's unique Malay, Chinese, Indian, and "
            "Peranakan heritage produces a dizzying range of dishes found "
            "nowhere else.  Char kway teow fried over charcoal at Siam Road, "
            "the tangy assam laksa of Air Itam, and the cool sweetness of "
            "Penang Road chendul are legendary.  Gurney Drive and New Lane "
            "come alive each evening with hawker stalls stretching into the "
            "night, while George Town's UNESCO-listed old quarter hides some "
            "of the best kopitiam breakfasts in Southeast Asia."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spots Mapped", len(data))
        c2.metric("UNESCO Town", "George Town (2008)")
        c3.metric("Signature Dish", "Char Kway Teow")
        c4.metric("Cheapest Meal", "~2 MYR ($0.45)")

        st.markdown("---")
        st.markdown("##### Area Highlights")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        pc1, pc2, pc3 = st.columns(3)
        for col, (area, cnt) in zip([pc1, pc2, pc3], sorted_areas[:3]):
            col.metric(area, f"{cnt} spots")

        _show_map_and_data(data, zoom=12, center=[5.415, 100.320], csv_prefix="penang_street_food")

    # -----------------------------------------------------------------
    # MODE: Seoul Pojangmacha
    # -----------------------------------------------------------------
    elif mode == "Seoul Pojangmacha":
        data = SEOUL_POJANGMACHA
        st.markdown("### Seoul Pojangmacha")
        st.markdown(
            "The pojangmacha -- a covered tent bar on the sidewalk -- is an "
            "essential part of Korean nightlife.  Under orange tarps, office "
            "workers unwind with soju, tteokbokki, and skewered fish cake while "
            "rain patters overhead.  Gwangjang Market, one of the oldest in "
            "Seoul, is a mecca for bindaetteok (mung bean pancakes) and mayak "
            "gimbap (addictive mini rice rolls).  Myeongdong's neon-lit food "
            "alley sells tornado potatoes and mozzarella corn dogs to millions, "
            "while the pojangmacha rows of Jongno 3-ga offer an atmosphere that "
            "no restaurant can match."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Spots Mapped", len(data))
        c2.metric("Gwangjang Market", "Since 1905")
        c3.metric("Iconic Snack", "Tteokbokki")
        c4.metric("Soju + Tent Bar", "Pojangmacha culture")

        st.markdown("---")
        st.markdown("##### District Clusters")
        areas = {}
        for d in data:
            a = d.get("Area", "Unknown")
            areas[a] = areas.get(a, 0) + 1
        sorted_areas = sorted(areas.items(), key=lambda x: -x[1])
        sk1, sk2, sk3 = st.columns(3)
        for col, (area, cnt) in zip([sk1, sk2, sk3], sorted_areas[:3]):
            col.metric(area, f"{cnt} spots")

        _show_map_and_data(data, zoom=12, center=[37.560, 126.975], csv_prefix="seoul_pojangmacha")
