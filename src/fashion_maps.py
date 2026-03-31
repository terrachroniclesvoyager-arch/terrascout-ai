# -*- coding: utf-8 -*-
"""
Fashion & Design Maps module for TerraScout AI.
Provides 10 interactive map types covering fashion capitals, luxury brands,
textile production, fashion weeks, design schools, jewelry origins,
traditional clothing, silk road textile trade, horology, and perfumery.
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
# 1. FASHION CAPITALS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_fashion_capitals():
    data = [
        {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "score": 98, "specialty": "Haute couture, luxury fashion", "notable_brands": "Chanel, Dior, Louis Vuitton, Hermes"},
        {"city": "Milan", "country": "Italy", "lat": 45.4642, "lon": 9.1900, "score": 96, "specialty": "Ready-to-wear, leather goods", "notable_brands": "Prada, Versace, Armani, Dolce & Gabbana"},
        {"city": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "score": 95, "specialty": "Sportswear, streetwear, avant-garde", "notable_brands": "Ralph Lauren, Calvin Klein, Marc Jacobs"},
        {"city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "score": 94, "specialty": "Bespoke tailoring, punk-inspired", "notable_brands": "Burberry, Alexander McQueen, Vivienne Westwood"},
        {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "score": 91, "specialty": "Avant-garde, streetwear, Harajuku", "notable_brands": "Comme des Garcons, Issey Miyake, Yohji Yamamoto"},
        {"city": "Los Angeles", "country": "USA", "lat": 34.0522, "lon": -118.2437, "score": 88, "specialty": "Casual luxury, celebrity fashion", "notable_brands": "Tom Ford, The Row, Fear of God"},
        {"city": "Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737, "score": 86, "specialty": "Fast fashion, emerging designers", "notable_brands": "Shang Xia, Uma Wang, Angel Chen"},
        {"city": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780, "score": 85, "specialty": "K-fashion, beauty-driven style", "notable_brands": "Gentle Monster, Ader Error, Wooyoungmi"},
        {"city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "score": 82, "specialty": "Underground fashion, minimalism", "notable_brands": "Hugo Boss, Jil Sander, 032c"},
        {"city": "Florence", "country": "Italy", "lat": 43.7696, "lon": 11.2558, "score": 81, "specialty": "Leather craftsmanship, menswear", "notable_brands": "Gucci, Salvatore Ferragamo, Emilio Pucci"},
        {"city": "Barcelona", "country": "Spain", "lat": 41.3874, "lon": 2.1686, "score": 79, "specialty": "Mediterranean chic, avant-garde", "notable_brands": "Balenciaga (origin), Desigual, Custo Barcelona"},
        {"city": "Copenhagen", "country": "Denmark", "lat": 55.6761, "lon": 12.5683, "score": 78, "specialty": "Scandinavian minimalism, sustainability", "notable_brands": "Ganni, Stine Goya, Cecilie Bahnsen"},
        {"city": "Antwerp", "country": "Belgium", "lat": 51.2194, "lon": 4.4025, "score": 77, "specialty": "Deconstructivism, conceptual fashion", "notable_brands": "Dries Van Noten, Ann Demeulemeester, Raf Simons"},
        {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "score": 76, "specialty": "Bridal couture, textiles, Bollywood fashion", "notable_brands": "Sabyasachi, Manish Malhotra, Tarun Tahiliani"},
        {"city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "score": 74, "specialty": "Resort wear, swim, outdoor", "notable_brands": "Zimmermann, Dion Lee, Sass & Bide"},
        {"city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173, "score": 73, "specialty": "Luxury consumption, fur fashion", "notable_brands": "Gosha Rubchinskiy, Ulyana Sergeenko"},
        {"city": "Sao Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "score": 72, "specialty": "Colorful prints, beachwear", "notable_brands": "Osklen, Alexandre Herchcovitch, Farm Rio"},
        {"city": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708, "score": 71, "specialty": "Luxury retail hub, modest fashion", "notable_brands": "Elie Saab boutiques, The Modist"},
        {"city": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792, "score": 69, "specialty": "Afro-futurism, vibrant prints", "notable_brands": "Lisa Folawiyo, Maki Oh, Orange Culture"},
        {"city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686, "score": 68, "specialty": "Sustainable fashion, clean lines", "notable_brands": "Acne Studios, H&M, COS, Filippa K"},
        {"city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "score": 67, "specialty": "Artisanal textiles, contemporary craft", "notable_brands": "Carla Fernandez, Lydia Lavin, Pineda Covalin"},
        {"city": "Johannesburg", "country": "South Africa", "lat": -26.2041, "lon": 28.0473, "score": 66, "specialty": "African contemporary, street style", "notable_brands": "Thebe Magugu, Rich Mnisi, Maxhosa"},
        {"city": "Tbilisi", "country": "Georgia", "lat": 41.7151, "lon": 44.8271, "score": 65, "specialty": "Post-Soviet avant-garde", "notable_brands": "Demna (Balenciaga), Situationist, George Keburia"},
        {"city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "score": 64, "specialty": "Denim, sustainable fashion", "notable_brands": "Viktor & Rolf, Scotch & Soda, G-Star RAW"},
        {"city": "Marrakech", "country": "Morocco", "lat": 31.6295, "lon": -7.9811, "score": 62, "specialty": "Artisanal textiles, caftans", "notable_brands": "Artsi Ifrach, ABURY, Norya Ayron"},
        {"city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816, "score": 61, "specialty": "Leather goods, tango fashion", "notable_brands": "Rapsodia, Jazmin Chebar, Tramando"},
        {"city": "Vienna", "country": "Austria", "lat": 48.2082, "lon": 16.3738, "score": 60, "specialty": "Traditional tailoring, ball gowns", "notable_brands": "Helmut Lang (origin), Lena Hoschek"},
        {"city": "Nairobi", "country": "Kenya", "lat": -1.2921, "lon": 36.8219, "score": 58, "specialty": "East African prints, sustainable craft", "notable_brands": "Katush, Adele Dejak, KikoRomeo"},
        {"city": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018, "score": 57, "specialty": "Silk, streetwear, tropical fashion", "notable_brands": "Asava, Sretsis, Greyhound Original"},
        {"city": "Accra", "country": "Ghana", "lat": 5.6037, "lon": -0.1870, "score": 55, "specialty": "Kente cloth, Afro-contemporary", "notable_brands": "Studio 189, Christie Brown, Pistis Ghana"},
    ]
    return pd.DataFrame(data)


def _render_fashion_capitals():
    """Map 1: Fashion Capitals."""
    df = _get_fashion_capitals()
    st.markdown("#### Global Fashion Capitals")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Cities", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Top Score", int(df["score"].max()))
    c4.metric("Avg Score", round(df["score"].mean(), 1))

    top10 = df.nlargest(10, "score")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["city"].values[::-1], top10["score"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Fashion Score")
    ax.set_title("Top 10 Fashion Capitals by Score")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['city'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Score: {row['score']}/100<br>"
            f"Specialty: {escape(row['specialty'])}<br>"
            f"Brands: {escape(row['notable_brands'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(5, row["score"] / 8),
            color=ACCENT_PINK,
            fill=True,
            fill_color=ACCENT_PINK,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['city'])} ({row['score']})",
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["city", "country", "score", "specialty", "notable_brands"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "fashion_capitals.csv", "text/csv",
                       key="dl_fashion_capitals")


# =====================================================================
# 2. LUXURY BRAND HEADQUARTERS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_luxury_brands():
    data = [
        {"brand": "Louis Vuitton", "parent": "LVMH", "city": "Paris", "country": "France", "founded": 1854, "lat": 48.8698, "lon": 2.3075, "category": "Leather goods, fashion"},
        {"brand": "Chanel", "parent": "Chanel Ltd", "city": "Paris", "country": "France", "founded": 1910, "lat": 48.8680, "lon": 2.3050, "category": "Haute couture, fragrance"},
        {"brand": "Hermes", "parent": "Hermes International", "city": "Paris", "country": "France", "founded": 1837, "lat": 48.8688, "lon": 2.3210, "category": "Leather goods, scarves"},
        {"brand": "Dior", "parent": "LVMH", "city": "Paris", "country": "France", "founded": 1946, "lat": 48.8660, "lon": 2.3060, "category": "Haute couture, cosmetics"},
        {"brand": "Gucci", "parent": "Kering", "city": "Florence", "country": "Italy", "founded": 1921, "lat": 43.7700, "lon": 11.2530, "category": "Leather goods, fashion"},
        {"brand": "Prada", "parent": "Prada Group", "city": "Milan", "country": "Italy", "founded": 1913, "lat": 45.4685, "lon": 9.1954, "category": "Fashion, leather goods"},
        {"brand": "Versace", "parent": "Capri Holdings", "city": "Milan", "country": "Italy", "founded": 1978, "lat": 45.4710, "lon": 9.1890, "category": "Fashion, accessories"},
        {"brand": "Armani", "parent": "Giorgio Armani S.p.A.", "city": "Milan", "country": "Italy", "founded": 1975, "lat": 45.4700, "lon": 9.1860, "category": "Fashion, lifestyle"},
        {"brand": "Dolce & Gabbana", "parent": "Dolce & Gabbana S.r.l.", "city": "Milan", "country": "Italy", "founded": 1985, "lat": 45.4690, "lon": 9.1920, "category": "Fashion, beauty"},
        {"brand": "Burberry", "parent": "Burberry Group", "city": "London", "country": "UK", "founded": 1856, "lat": 51.5130, "lon": -0.1440, "category": "Outerwear, trench coats"},
        {"brand": "Alexander McQueen", "parent": "Kering", "city": "London", "country": "UK", "founded": 1992, "lat": 51.5115, "lon": -0.1480, "category": "Avant-garde fashion"},
        {"brand": "Vivienne Westwood", "parent": "Vivienne Westwood Ltd", "city": "London", "country": "UK", "founded": 1981, "lat": 51.5090, "lon": -0.1370, "category": "Punk-inspired fashion"},
        {"brand": "Ralph Lauren", "parent": "Ralph Lauren Corp", "city": "New York", "country": "USA", "founded": 1967, "lat": 40.7634, "lon": -73.9730, "category": "Preppy, American classic"},
        {"brand": "Calvin Klein", "parent": "PVH Corp", "city": "New York", "country": "USA", "founded": 1968, "lat": 40.7560, "lon": -73.9870, "category": "Minimalist fashion, underwear"},
        {"brand": "Tom Ford", "parent": "Estee Lauder", "city": "New York", "country": "USA", "founded": 2005, "lat": 40.7620, "lon": -73.9690, "category": "Luxury fashion, fragrance"},
        {"brand": "Marc Jacobs", "parent": "LVMH", "city": "New York", "country": "USA", "founded": 1984, "lat": 40.7410, "lon": -74.0010, "category": "Fashion, accessories"},
        {"brand": "Tiffany & Co.", "parent": "LVMH", "city": "New York", "country": "USA", "founded": 1837, "lat": 40.7625, "lon": -73.9735, "category": "Jewelry, luxury accessories"},
        {"brand": "Balenciaga", "parent": "Kering", "city": "Paris", "country": "France", "founded": 1919, "lat": 48.8655, "lon": 2.3085, "category": "Fashion, sneakers"},
        {"brand": "Saint Laurent", "parent": "Kering", "city": "Paris", "country": "France", "founded": 1961, "lat": 48.8670, "lon": 2.3100, "category": "Fashion, leather goods"},
        {"brand": "Givenchy", "parent": "LVMH", "city": "Paris", "country": "France", "founded": 1952, "lat": 48.8645, "lon": 2.3140, "category": "Haute couture, fragrance"},
        {"brand": "Valentino", "parent": "Kering", "city": "Rome", "country": "Italy", "founded": 1960, "lat": 41.9053, "lon": 12.4820, "category": "Haute couture, red gowns"},
        {"brand": "Fendi", "parent": "LVMH", "city": "Rome", "country": "Italy", "founded": 1925, "lat": 41.9060, "lon": 12.4840, "category": "Fur, leather, fashion"},
        {"brand": "Salvatore Ferragamo", "parent": "Ferragamo S.p.A.", "city": "Florence", "country": "Italy", "founded": 1927, "lat": 43.7696, "lon": 11.2520, "category": "Shoes, leather goods"},
        {"brand": "Bottega Veneta", "parent": "Kering", "city": "Vicenza", "country": "Italy", "founded": 1966, "lat": 45.5485, "lon": 11.5474, "category": "Leather goods, intrecciato"},
        {"brand": "Cartier", "parent": "Richemont", "city": "Paris", "country": "France", "founded": 1847, "lat": 48.8682, "lon": 2.3280, "category": "Jewelry, watches"},
        {"brand": "Rolex", "parent": "Hans Wilsdorf Foundation", "city": "Geneva", "country": "Switzerland", "founded": 1905, "lat": 46.2044, "lon": 6.1432, "category": "Luxury watches"},
        {"brand": "Patek Philippe", "parent": "Stern family", "city": "Geneva", "country": "Switzerland", "founded": 1839, "lat": 46.2000, "lon": 6.1500, "category": "Luxury watches"},
        {"brand": "Bulgari", "parent": "LVMH", "city": "Rome", "country": "Italy", "founded": 1884, "lat": 41.9030, "lon": 12.4800, "category": "Jewelry, watches, fragrance"},
        {"brand": "Loewe", "parent": "LVMH", "city": "Madrid", "country": "Spain", "founded": 1846, "lat": 40.4230, "lon": -3.6900, "category": "Leather goods, fashion"},
        {"brand": "Moncler", "parent": "Moncler S.p.A.", "city": "Milan", "country": "Italy", "founded": 1952, "lat": 45.4650, "lon": 9.1870, "category": "Luxury outerwear, down jackets"},
        {"brand": "Issey Miyake", "parent": "Issey Miyake Inc.", "city": "Tokyo", "country": "Japan", "founded": 1970, "lat": 35.6620, "lon": 139.7300, "category": "Avant-garde, pleats"},
        {"brand": "Comme des Garcons", "parent": "Comme des Garcons Co.", "city": "Tokyo", "country": "Japan", "founded": 1969, "lat": 35.6700, "lon": 139.7020, "category": "Deconstructionist fashion"},
        {"brand": "Yohji Yamamoto", "parent": "Yohji Yamamoto Inc.", "city": "Tokyo", "country": "Japan", "founded": 1972, "lat": 35.6580, "lon": 139.7100, "category": "Dark avant-garde, draping"},
        {"brand": "Ermenegildo Zegna", "parent": "Zegna Group", "city": "Trivero", "country": "Italy", "founded": 1910, "lat": 45.6690, "lon": 8.1920, "category": "Menswear, fine textiles"},
        {"brand": "Chloé", "parent": "Richemont", "city": "Paris", "country": "France", "founded": 1952, "lat": 48.8710, "lon": 2.3160, "category": "Feminine ready-to-wear"},
        {"brand": "Stella McCartney", "parent": "LVMH", "city": "London", "country": "UK", "founded": 2001, "lat": 51.5140, "lon": -0.1450, "category": "Sustainable luxury fashion"},
        {"brand": "Brunello Cucinelli", "parent": "Brunello Cucinelli S.p.A.", "city": "Solomeo", "country": "Italy", "founded": 1978, "lat": 43.0190, "lon": 12.3490, "category": "Cashmere, humanistic capitalism"},
        {"brand": "Acne Studios", "parent": "Acne Studios", "city": "Stockholm", "country": "Sweden", "founded": 1996, "lat": 59.3340, "lon": 18.0630, "category": "Scandinavian minimalism"},
        {"brand": "Thom Browne", "parent": "Zegna Group", "city": "New York", "country": "USA", "founded": 2001, "lat": 40.7400, "lon": -73.9930, "category": "Tailored menswear, avant-garde"},
        {"brand": "Giambattista Valli", "parent": "Giambattista Valli SAS", "city": "Paris", "country": "France", "founded": 2005, "lat": 48.8640, "lon": 2.3200, "category": "Haute couture, tulle gowns"},
    ]
    return pd.DataFrame(data)


def _render_luxury_brands():
    """Map 2: Luxury Brand HQs."""
    df = _get_luxury_brands()
    st.markdown("#### Luxury Brand Headquarters")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Brands", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["founded"].min()))
    c4.metric("Newest", int(df["founded"].max()))

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Brands")
    ax.set_title("Luxury Brands by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[46, 8], zoom=4)
    cluster = MarkerCluster().add_to(m)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['brand'])}</b><br>"
            f"Parent: {escape(row['parent'])}<br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Founded: {row['founded']}<br>"
            f"Category: {escape(row['category'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=ACCENT_VIOLET,
            fill=True,
            fill_color=ACCENT_VIOLET,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=escape(row["brand"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["brand", "parent", "city", "country", "founded", "category"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "luxury_brands.csv", "text/csv",
                       key="dl_luxury_brands")


# =====================================================================
# 3. TEXTILE PRODUCTION HUBS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_textile_production():
    data = [
        {"region": "Dhaka", "country": "Bangladesh", "lat": 23.8103, "lon": 90.4125, "specialty": "Ready-made garments, knitwear", "workers_millions": 4.0, "export_rank": 2},
        {"region": "Guangzhou", "country": "China", "lat": 23.1291, "lon": 113.2644, "specialty": "Fast fashion, synthetic textiles", "workers_millions": 5.5, "export_rank": 1},
        {"region": "Tirupur", "country": "India", "lat": 11.1085, "lon": 77.3411, "specialty": "Cotton knitwear, T-shirts", "workers_millions": 0.6, "export_rank": 5},
        {"region": "Ho Chi Minh City", "country": "Vietnam", "lat": 10.8231, "lon": 106.6297, "specialty": "Sportswear, footwear", "workers_millions": 2.5, "export_rank": 3},
        {"region": "Istanbul", "country": "Turkey", "lat": 41.0082, "lon": 28.9784, "specialty": "Denim, cotton fabrics, leather", "workers_millions": 1.2, "export_rank": 7},
        {"region": "Faisalabad", "country": "Pakistan", "lat": 31.4504, "lon": 73.1350, "specialty": "Cotton textiles, towels, bedding", "workers_millions": 1.5, "export_rank": 8},
        {"region": "Surat", "country": "India", "lat": 21.1702, "lon": 72.8311, "specialty": "Silk, synthetic sarees, embroidery", "workers_millions": 0.8, "export_rank": 10},
        {"region": "Hangzhou", "country": "China", "lat": 30.2741, "lon": 120.1551, "specialty": "Silk, high-end textiles", "workers_millions": 1.0, "export_rank": 4},
        {"region": "Phnom Penh", "country": "Cambodia", "lat": 11.5564, "lon": 104.9282, "specialty": "Garment assembly, sportswear", "workers_millions": 0.7, "export_rank": 12},
        {"region": "Addis Ababa", "country": "Ethiopia", "lat": 9.0250, "lon": 38.7469, "specialty": "Cotton garments, emerging hub", "workers_millions": 0.3, "export_rank": 20},
        {"region": "Coimbatore", "country": "India", "lat": 11.0168, "lon": 76.9558, "specialty": "Cotton spinning, hosiery", "workers_millions": 0.5, "export_rank": 11},
        {"region": "Jakarta", "country": "Indonesia", "lat": -6.2088, "lon": 106.8456, "specialty": "Batik, woven textiles, footwear", "workers_millions": 1.8, "export_rank": 6},
        {"region": "Biella", "country": "Italy", "lat": 45.5628, "lon": 8.0580, "specialty": "Fine wool, luxury suiting fabrics", "workers_millions": 0.03, "export_rank": 15},
        {"region": "Prato", "country": "Italy", "lat": 43.8777, "lon": 11.0968, "specialty": "Recycled wool, fast fashion textiles", "workers_millions": 0.04, "export_rank": 18},
        {"region": "Lesotho (Maseru)", "country": "Lesotho", "lat": -29.3167, "lon": 27.4833, "specialty": "Denim, jeans for US market (AGOA)", "workers_millions": 0.05, "export_rank": 25},
        {"region": "Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579, "specialty": "Electronics textiles, wearable tech fabrics", "workers_millions": 0.9, "export_rank": 9},
        {"region": "Yangon", "country": "Myanmar", "lat": 16.8661, "lon": 96.1951, "specialty": "Cut-make-trim garments", "workers_millions": 0.5, "export_rank": 14},
        {"region": "Colombo", "country": "Sri Lanka", "lat": 6.9271, "lon": 79.8612, "specialty": "Intimate apparel, ethical manufacturing", "workers_millions": 0.35, "export_rank": 16},
        {"region": "Cairo", "country": "Egypt", "lat": 30.0444, "lon": 31.2357, "specialty": "Egyptian cotton, luxury linens", "workers_millions": 0.4, "export_rank": 19},
        {"region": "Leon", "country": "Mexico", "lat": 21.1250, "lon": -101.6860, "specialty": "Leather shoes, leather goods", "workers_millions": 0.3, "export_rank": 22},
        {"region": "Bursa", "country": "Turkey", "lat": 40.1885, "lon": 29.0610, "specialty": "Silk, towels, automotive textiles", "workers_millions": 0.25, "export_rank": 17},
        {"region": "Ludhiana", "country": "India", "lat": 30.9010, "lon": 75.8573, "specialty": "Woolen knitwear, hosiery", "workers_millions": 0.4, "export_rank": 13},
        {"region": "Narayanganj", "country": "Bangladesh", "lat": 23.6238, "lon": 90.5000, "specialty": "Jute, muslin, hosiery", "workers_millions": 0.6, "export_rank": 21},
        {"region": "Ningbo", "country": "China", "lat": 29.8683, "lon": 121.5440, "specialty": "Garment export hub, knitwear", "workers_millions": 0.7, "export_rank": 8},
        {"region": "Chittagong", "country": "Bangladesh", "lat": 22.3569, "lon": 91.7832, "specialty": "Garment production, export processing", "workers_millions": 0.8, "export_rank": 11},
        {"region": "Panipat", "country": "India", "lat": 29.3909, "lon": 76.9635, "specialty": "Recycled textiles, blankets, rugs", "workers_millions": 0.2, "export_rank": 24},
        {"region": "Xintang", "country": "China", "lat": 23.1400, "lon": 113.6100, "specialty": "Denim capital of the world, jeans", "workers_millions": 0.3, "export_rank": 6},
        {"region": "Denizli", "country": "Turkey", "lat": 37.7765, "lon": 29.0864, "specialty": "Home textiles, towels, robes", "workers_millions": 0.15, "export_rank": 23},
        {"region": "North Carolina (Piedmont)", "country": "USA", "lat": 35.7796, "lon": -78.6382, "specialty": "Technical textiles, legacy denim", "workers_millions": 0.1, "export_rank": 26},
        {"region": "Rajkot", "country": "India", "lat": 22.3039, "lon": 70.8022, "specialty": "Embroidered textiles, bandhani", "workers_millions": 0.15, "export_rank": 27},
        {"region": "Mulhouse", "country": "France", "lat": 47.7508, "lon": 7.3359, "specialty": "Printed textiles, historic cotton hub", "workers_millions": 0.02, "export_rank": 30},
        {"region": "Suzhou", "country": "China", "lat": 31.2990, "lon": 120.5853, "specialty": "Silk brocade, traditional weaving", "workers_millions": 0.4, "export_rank": 10},
        {"region": "Tangier", "country": "Morocco", "lat": 35.7595, "lon": -5.8340, "specialty": "Fast fashion garments for Europe", "workers_millions": 0.2, "export_rank": 28},
        {"region": "Managua", "country": "Nicaragua", "lat": 12.1364, "lon": -86.2514, "specialty": "T-shirts, basics for US brands", "workers_millions": 0.1, "export_rank": 29},
        {"region": "Tegucigalpa", "country": "Honduras", "lat": 14.0723, "lon": -87.1921, "specialty": "Knit garments, socks, underwear", "workers_millions": 0.15, "export_rank": 26},
    ]
    return pd.DataFrame(data)


def _render_textile_production():
    """Map 3: Textile Production Hubs."""
    df = _get_textile_production()
    st.markdown("#### Global Textile & Garment Production Hubs")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Regions", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Workers (M)", round(df["workers_millions"].sum(), 1))
    c4.metric("Top Producer", df.loc[df["export_rank"].idxmin(), "region"])

    top10 = df.nlargest(10, "workers_millions")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["region"].values[::-1], top10["workers_millions"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Workers (Millions)")
    ax.set_title("Top 10 Textile Hubs by Workforce")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[20, 80], zoom=3)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['region'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Specialty: {escape(row['specialty'])}<br>"
            f"Workers: {row['workers_millions']}M<br>"
            f"Export Rank: #{row['export_rank']}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(5, row["workers_millions"] * 5),
            color=ACCENT_AMBER,
            fill=True,
            fill_color=ACCENT_AMBER,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['region'])} ({row['workers_millions']}M workers)",
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["region", "country", "specialty", "workers_millions", "export_rank"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "textile_production.csv", "text/csv",
                       key="dl_textile_production")


# =====================================================================
# 4. FASHION WEEK CITIES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_fashion_weeks():
    data = [
        {"city": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "event": "Paris Fashion Week", "founded": 1973, "season": "Jan/Feb & Jun/Jul", "prestige": 10},
        {"city": "Milan", "country": "Italy", "lat": 45.4642, "lon": 9.1900, "event": "Milan Fashion Week", "founded": 1958, "season": "Feb/Mar & Sep/Oct", "prestige": 9},
        {"city": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "event": "New York Fashion Week", "founded": 1943, "season": "Feb & Sep", "prestige": 9},
        {"city": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "event": "London Fashion Week", "founded": 1984, "season": "Feb & Sep", "prestige": 9},
        {"city": "Berlin", "country": "Germany", "lat": 52.5200, "lon": 13.4050, "event": "Berlin Fashion Week", "founded": 2007, "season": "Jan & Jul", "prestige": 7},
        {"city": "Tokyo", "country": "Japan", "lat": 35.6762, "lon": 139.6503, "event": "Tokyo Fashion Week", "founded": 2005, "season": "Mar & Oct", "prestige": 7},
        {"city": "Seoul", "country": "South Korea", "lat": 37.5665, "lon": 126.9780, "event": "Seoul Fashion Week", "founded": 2000, "season": "Mar & Oct", "prestige": 7},
        {"city": "Shanghai", "country": "China", "lat": 31.2304, "lon": 121.4737, "event": "Shanghai Fashion Week", "founded": 2003, "season": "Apr & Oct", "prestige": 7},
        {"city": "Sao Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333, "event": "Sao Paulo Fashion Week", "founded": 1996, "season": "Apr & Oct", "prestige": 6},
        {"city": "Copenhagen", "country": "Denmark", "lat": 55.6761, "lon": 12.5683, "event": "Copenhagen Fashion Week", "founded": 2006, "season": "Jan/Feb & Aug", "prestige": 7},
        {"city": "Sydney", "country": "Australia", "lat": -33.8688, "lon": 151.2093, "event": "Australian Fashion Week", "founded": 1996, "season": "May", "prestige": 6},
        {"city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173, "event": "Moscow Fashion Week", "founded": 1994, "season": "Mar & Oct", "prestige": 5},
        {"city": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792, "event": "Lagos Fashion Week", "founded": 2011, "season": "Oct/Nov", "prestige": 6},
        {"city": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708, "event": "Arab Fashion Week", "founded": 2014, "season": "Mar & Oct", "prestige": 5},
        {"city": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "event": "Lakme Fashion Week", "founded": 1999, "season": "Mar & Oct", "prestige": 6},
        {"city": "Tbilisi", "country": "Georgia", "lat": 41.7151, "lon": 44.8271, "event": "Tbilisi Fashion Week", "founded": 2015, "season": "May & Nov", "prestige": 5},
        {"city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332, "event": "Mercedes-Benz Fashion Week Mexico", "founded": 2005, "season": "Apr & Oct", "prestige": 5},
        {"city": "Johannesburg", "country": "South Africa", "lat": -26.2041, "lon": 28.0473, "event": "SA Fashion Week", "founded": 1997, "season": "Apr & Oct", "prestige": 5},
        {"city": "Stockholm", "country": "Sweden", "lat": 59.3293, "lon": 18.0686, "event": "Stockholm Fashion Week", "founded": 2005, "season": "Jan & Aug", "prestige": 6},
        {"city": "Madrid", "country": "Spain", "lat": 40.4168, "lon": -3.7038, "event": "Mercedes-Benz Fashion Week Madrid", "founded": 1985, "season": "Feb & Sep", "prestige": 6},
        {"city": "Amsterdam", "country": "Netherlands", "lat": 52.3676, "lon": 4.9041, "event": "Amsterdam Fashion Week", "founded": 2004, "season": "Jan & Jul", "prestige": 5},
        {"city": "Accra", "country": "Ghana", "lat": 5.6037, "lon": -0.1870, "event": "Accra Fashion Week", "founded": 2016, "season": "Mar & Oct", "prestige": 4},
        {"city": "Nairobi", "country": "Kenya", "lat": -1.2921, "lon": 36.8219, "event": "Nairobi Fashion Week", "founded": 2019, "season": "May & Nov", "prestige": 4},
        {"city": "Vancouver", "country": "Canada", "lat": 49.2827, "lon": -123.1207, "event": "Vancouver Fashion Week", "founded": 2001, "season": "Mar & Sep", "prestige": 5},
        {"city": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018, "event": "Bangkok International Fashion Week", "founded": 2004, "season": "Mar & Sep", "prestige": 5},
    ]
    return pd.DataFrame(data)


def _render_fashion_weeks():
    """Map 4: Fashion Week Cities."""
    df = _get_fashion_weeks()
    st.markdown("#### Fashion Week Cities Around the World")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fashion Weeks", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["founded"].min()))
    c4.metric("Avg Prestige", round(df["prestige"].mean(), 1))

    top10 = df.nlargest(10, "prestige")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["city"].values[::-1], top10["prestige"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Prestige Score (1-10)")
    ax.set_title("Top Fashion Weeks by Prestige")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['event'])}</b><br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Founded: {row['founded']}<br>"
            f"Season: {escape(row['season'])}<br>"
            f"Prestige: {row['prestige']}/10"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=max(5, row["prestige"]),
            color=ACCENT_CYAN,
            fill=True,
            fill_color=ACCENT_CYAN,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['event'])} ({row['prestige']}/10)",
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["city", "country", "event", "founded", "season", "prestige"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "fashion_weeks.csv", "text/csv",
                       key="dl_fashion_weeks")


# =====================================================================
# 5. DESIGN SCHOOLS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_design_schools():
    data = [
        {"school": "Central Saint Martins", "city": "London", "country": "UK", "lat": 51.5360, "lon": -0.1257, "founded": 1854, "specialty": "Fashion, fine art, textiles", "alumni": "Alexander McQueen, John Galliano, Stella McCartney"},
        {"school": "Royal College of Art", "city": "London", "country": "UK", "lat": 51.5013, "lon": -0.1793, "founded": 1837, "specialty": "Fashion, textiles, ceramics", "alumni": "Ossie Clark, Zandra Rhodes, Philip Treacy"},
        {"school": "London College of Fashion", "city": "London", "country": "UK", "lat": 51.5151, "lon": -0.1346, "founded": 1906, "specialty": "Fashion business, design, curation", "alumni": "Jimmy Choo, Rupert Sanderson"},
        {"school": "Parsons School of Design", "city": "New York", "country": "USA", "lat": 40.7353, "lon": -73.9975, "founded": 1896, "specialty": "Fashion design, illustration", "alumni": "Marc Jacobs, Tom Ford, Donna Karan"},
        {"school": "Fashion Institute of Technology (FIT)", "city": "New York", "country": "USA", "lat": 40.7472, "lon": -73.9947, "founded": 1944, "specialty": "Fashion design, merchandising", "alumni": "Calvin Klein, Michael Kors, Carolina Herrera"},
        {"school": "Pratt Institute", "city": "New York", "country": "USA", "lat": 40.6893, "lon": -73.9634, "founded": 1887, "specialty": "Fashion, industrial design", "alumni": "Jeremy Scott, Betsey Johnson"},
        {"school": "ESMOD Paris", "city": "Paris", "country": "France", "lat": 48.8730, "lon": 2.3440, "founded": 1841, "specialty": "Pattern making, fashion design", "alumni": "Oldest fashion school in the world"},
        {"school": "Institut Francais de la Mode", "city": "Paris", "country": "France", "lat": 48.8420, "lon": 2.3750, "founded": 1986, "specialty": "Fashion management, design", "alumni": "Iris van Herpen (guest), emerging designers"},
        {"school": "Chambre Syndicale de la Haute Couture", "city": "Paris", "country": "France", "lat": 48.8700, "lon": 2.3310, "founded": 1927, "specialty": "Haute couture techniques", "alumni": "Yves Saint Laurent, Valentino Garavani"},
        {"school": "Polimoda", "city": "Florence", "country": "Italy", "lat": 43.7710, "lon": 11.2490, "founded": 1986, "specialty": "Fashion design, luxury management", "alumni": "Fashion talents from 70+ countries"},
        {"school": "Istituto Marangoni", "city": "Milan", "country": "Italy", "lat": 45.4750, "lon": 9.1830, "founded": 1935, "specialty": "Fashion design, styling", "alumni": "Franco Moschino, Domenico Dolce"},
        {"school": "Domus Academy", "city": "Milan", "country": "Italy", "lat": 45.4780, "lon": 9.2120, "founded": 1982, "specialty": "Design, fashion, experience design", "alumni": "Postgraduate design leaders"},
        {"school": "Antwerp Royal Academy of Fine Arts", "city": "Antwerp", "country": "Belgium", "lat": 51.2170, "lon": 4.4130, "founded": 1663, "specialty": "Fashion department since 1963", "alumni": "Antwerp Six, Raf Simons, Demna"},
        {"school": "Bunka Fashion College", "city": "Tokyo", "country": "Japan", "lat": 35.6880, "lon": 139.6970, "founded": 1919, "specialty": "Fashion design, sewing technology", "alumni": "Yohji Yamamoto, Kenzo Takada, Junya Watanabe"},
        {"school": "SCAD - Savannah College of Art and Design", "city": "Savannah", "country": "USA", "lat": 32.0762, "lon": -81.0932, "founded": 1978, "specialty": "Fashion, fibers, accessory design", "alumni": "Industry-leading placement rates"},
        {"school": "Rhode Island School of Design (RISD)", "city": "Providence", "country": "USA", "lat": 41.8260, "lon": -71.4067, "founded": 1877, "specialty": "Textile design, apparel", "alumni": "Nicole Miller, Siki Im"},
        {"school": "Royal Academy of Fine Arts (KASK)", "city": "Ghent", "country": "Belgium", "lat": 51.0543, "lon": 3.7174, "founded": 1751, "specialty": "Fashion, fine art", "alumni": "Emerging Belgian designers"},
        {"school": "Beckmans College of Design", "city": "Stockholm", "country": "Sweden", "lat": 59.3410, "lon": 18.0770, "founded": 1939, "specialty": "Fashion, visual communication", "alumni": "Scandinavian design leaders"},
        {"school": "NIFT (National Institute of Fashion Technology)", "city": "New Delhi", "country": "India", "lat": 28.5517, "lon": 77.2043, "founded": 1986, "specialty": "Fashion design, textile design", "alumni": "Manish Arora, Rahul Mishra"},
        {"school": "HEAD Geneva", "city": "Geneva", "country": "Switzerland", "lat": 46.1980, "lon": 6.1440, "founded": 2006, "specialty": "Fashion, jewelry, accessories", "alumni": "Swiss design innovators"},
        {"school": "Shenkar College", "city": "Ramat Gan", "country": "Israel", "lat": 32.0833, "lon": 34.8097, "founded": 1970, "specialty": "Fashion design, textile engineering", "alumni": "Alber Elbaz, Nili Lotan"},
        {"school": "Berlin University of the Arts (UdK)", "city": "Berlin", "country": "Germany", "lat": 52.5080, "lon": 13.3270, "founded": 1696, "specialty": "Fashion, fine arts, design", "alumni": "German fashion vanguard"},
        {"school": "Accademia di Costume e di Moda", "city": "Rome", "country": "Italy", "lat": 41.9060, "lon": 12.4880, "founded": 1964, "specialty": "Costume design, fashion", "alumni": "Italian costume designers"},
        {"school": "Royal Danish Academy", "city": "Copenhagen", "country": "Denmark", "lat": 55.6800, "lon": 12.5820, "founded": 1754, "specialty": "Fashion, textile design", "alumni": "Cecilie Bahnsen, Henrik Vibskov"},
        {"school": "AMD Akademie Mode & Design", "city": "Hamburg", "country": "Germany", "lat": 53.5511, "lon": 9.9937, "founded": 1989, "specialty": "Fashion, media, brand management", "alumni": "German fashion industry leaders"},
        {"school": "Tsinghua University Academy of Arts", "city": "Beijing", "country": "China", "lat": 40.0027, "lon": 116.3265, "founded": 1956, "specialty": "Fashion, textile, visual design", "alumni": "Leading Chinese fashion designers"},
        {"school": "RMIT University", "city": "Melbourne", "country": "Australia", "lat": -37.8081, "lon": 144.9631, "founded": 1887, "specialty": "Fashion, textiles, merchandising", "alumni": "Toni Maticevski, Dion Lee"},
        {"school": "Aalto University School of Arts", "city": "Helsinki", "country": "Finland", "lat": 60.1841, "lon": 24.8300, "founded": 2010, "specialty": "Fashion, textile art, sustainability", "alumni": "Finnish sustainable design leaders"},
        {"school": "Escola de Moda de Lisboa", "city": "Lisbon", "country": "Portugal", "lat": 38.7223, "lon": -9.1393, "founded": 1989, "specialty": "Fashion design, Portuguese textiles", "alumni": "Portuguese fashion talents"},
        {"school": "AFDA Cape Town", "city": "Cape Town", "country": "South Africa", "lat": -33.9249, "lon": 18.4241, "founded": 1994, "specialty": "Fashion, film, performance", "alumni": "African fashion innovators"},
    ]
    return pd.DataFrame(data)


def _render_design_schools():
    """Map 5: Design Schools."""
    df = _get_design_schools()
    st.markdown("#### Top Fashion & Design Schools")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Schools", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Oldest", int(df["founded"].min()))
    c4.metric("Newest", int(df["founded"].max()))

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Schools")
    ax.set_title("Fashion Schools by Country (Top 10)")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[45, 5], zoom=3)
    cluster = MarkerCluster().add_to(m)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['school'])}</b><br>"
            f"City: {escape(row['city'])}, {escape(row['country'])}<br>"
            f"Founded: {row['founded']}<br>"
            f"Specialty: {escape(row['specialty'])}<br>"
            f"Alumni: {escape(row['alumni'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=ACCENT_EMERALD,
            fill=True,
            fill_color=ACCENT_EMERALD,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(row["school"]),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["school", "city", "country", "founded", "specialty", "alumni"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "design_schools.csv", "text/csv",
                       key="dl_design_schools")


# =====================================================================
# 6. JEWELRY & GEMSTONES
# =====================================================================
@st.cache_data(ttl=3600)
def _get_jewelry_gemstones():
    data = [
        {"location": "Antwerp", "country": "Belgium", "lat": 51.2194, "lon": 4.4025, "gemstone": "Diamonds", "role": "World diamond trading capital", "annual_value_billions": 40.0},
        {"location": "Surat", "country": "India", "lat": 21.1702, "lon": 72.8311, "gemstone": "Diamonds", "role": "90% of world's diamonds cut and polished here", "annual_value_billions": 24.0},
        {"location": "Jaipur", "country": "India", "lat": 26.9124, "lon": 75.7873, "gemstone": "Emeralds, rubies, sapphires", "role": "Colored gemstone cutting capital", "annual_value_billions": 8.0},
        {"location": "Kimberley", "country": "South Africa", "lat": -28.7282, "lon": 24.7499, "gemstone": "Diamonds", "role": "Historic Big Hole, De Beers origin", "annual_value_billions": 3.0},
        {"location": "Mogok", "country": "Myanmar", "lat": 22.9216, "lon": 96.5095, "gemstone": "Rubies, sapphires", "role": "Valley of Rubies, finest pigeon blood rubies", "annual_value_billions": 2.5},
        {"location": "Muzo", "country": "Colombia", "lat": 5.5333, "lon": -74.1000, "gemstone": "Emeralds", "role": "World's finest emeralds since Inca era", "annual_value_billions": 1.5},
        {"location": "Ratnapura", "country": "Sri Lanka", "lat": 6.6828, "lon": 80.3992, "gemstone": "Sapphires, rubies", "role": "City of Gems, Ceylon sapphires", "annual_value_billions": 1.0},
        {"location": "Bangkok", "country": "Thailand", "lat": 13.7563, "lon": 100.5018, "gemstone": "Rubies, sapphires", "role": "Major gemstone trading and cutting hub", "annual_value_billions": 12.0},
        {"location": "Idar-Oberstein", "country": "Germany", "lat": 49.6553, "lon": 7.3018, "gemstone": "Agates, jasper", "role": "Historic gemstone cutting center since 1500s", "annual_value_billions": 0.5},
        {"location": "Pforzheim", "country": "Germany", "lat": 48.8922, "lon": 8.6942, "gemstone": "Gold, jewelry", "role": "Gold City, 75% of German jewelry production", "annual_value_billions": 3.5},
        {"location": "Place Vendome, Paris", "country": "France", "lat": 48.8680, "lon": 2.3290, "gemstone": "High jewelry", "role": "Cartier, Van Cleef, Boucheron flagships", "annual_value_billions": 15.0},
        {"location": "Hatton Garden, London", "country": "UK", "lat": 51.5210, "lon": -0.1080, "gemstone": "Diamonds, jewelry", "role": "London's jewelry quarter since medieval times", "annual_value_billions": 5.0},
        {"location": "47th Street, New York", "country": "USA", "lat": 40.7580, "lon": -73.9790, "gemstone": "Diamonds, all gems", "role": "Diamond District, $24B annual trade", "annual_value_billions": 24.0},
        {"location": "Mirpur (Dhaka)", "country": "Bangladesh", "lat": 23.8042, "lon": 90.3654, "gemstone": "Gold jewelry", "role": "Traditional gold smithing center", "annual_value_billions": 2.0},
        {"location": "Valenza", "country": "Italy", "lat": 45.0113, "lon": 8.6480, "gemstone": "Gold, high jewelry", "role": "Italian goldsmithing capital, 1000+ workshops", "annual_value_billions": 4.0},
        {"location": "Arezzo", "country": "Italy", "lat": 43.4637, "lon": 11.8798, "gemstone": "Gold chain, fashion jewelry", "role": "Largest gold jewelry manufacturing in Europe", "annual_value_billions": 5.5},
        {"location": "Tucson", "country": "USA", "lat": 32.2226, "lon": -110.9747, "gemstone": "All gemstones, minerals", "role": "World's largest gem & mineral show (annual)", "annual_value_billions": 1.0},
        {"location": "Hong Kong", "country": "China", "lat": 22.3193, "lon": 114.1694, "gemstone": "Jade, pearls, diamonds", "role": "Asian jewelry trading hub", "annual_value_billions": 18.0},
        {"location": "Chanthaburi", "country": "Thailand", "lat": 12.6112, "lon": 102.1044, "gemstone": "Rubies, sapphires", "role": "Thai gem mining and trading center", "annual_value_billions": 1.5},
        {"location": "Taxco", "country": "Mexico", "lat": 18.5564, "lon": -99.6048, "gemstone": "Silver", "role": "Silver capital of the world", "annual_value_billions": 0.8},
        {"location": "Opal Fields (Lightning Ridge)", "country": "Australia", "lat": -29.4278, "lon": 147.9808, "gemstone": "Black opals", "role": "World's rarest and most valuable opals", "annual_value_billions": 0.3},
        {"location": "Minas Gerais", "country": "Brazil", "lat": -18.5122, "lon": -44.5550, "gemstone": "Tourmaline, aquamarine, topaz", "role": "World's most diverse gemstone region", "annual_value_billions": 2.0},
        {"location": "Merelani Hills", "country": "Tanzania", "lat": -3.5500, "lon": 37.0500, "gemstone": "Tanzanite", "role": "Only source of tanzanite on Earth", "annual_value_billions": 0.5},
        {"location": "Pailin", "country": "Cambodia", "lat": 12.8517, "lon": 102.6098, "gemstone": "Sapphires, rubies", "role": "Historic sapphire mining region", "annual_value_billions": 0.2},
        {"location": "Kalgoorlie", "country": "Australia", "lat": -30.7490, "lon": 121.4660, "gemstone": "Gold", "role": "Western Australian goldfields", "annual_value_billions": 8.0},
        {"location": "Zambia (Kagem Mine)", "country": "Zambia", "lat": -13.0200, "lon": 28.3000, "gemstone": "Emeralds", "role": "World's largest emerald mine", "annual_value_billions": 0.6},
        {"location": "Luc Yen", "country": "Vietnam", "lat": 22.1000, "lon": 104.7500, "gemstone": "Rubies, sapphires, spinels", "role": "Vietnamese gem mining district", "annual_value_billions": 0.3},
        {"location": "Tsavorite Hills (Tsavo)", "country": "Kenya", "lat": -3.5000, "lon": 38.5000, "gemstone": "Tsavorite garnets", "role": "Rare green garnet found only here and Tanzania", "annual_value_billions": 0.1},
        {"location": "Coober Pedy", "country": "Australia", "lat": -29.0135, "lon": 134.7544, "gemstone": "Opals", "role": "Opal capital of the world, underground town", "annual_value_billions": 0.3},
        {"location": "Ekaterinburg", "country": "Russia", "lat": 56.8389, "lon": 60.6057, "gemstone": "Emeralds, alexandrite", "role": "Historic Ural Mountains gemstone source", "annual_value_billions": 0.5},
        {"location": "Peshawar", "country": "Pakistan", "lat": 34.0151, "lon": 71.5249, "gemstone": "Emeralds, tourmaline", "role": "Gateway to Afghan/Pakistani gemstones", "annual_value_billions": 0.4},
        {"location": "Ilakaka", "country": "Madagascar", "lat": -22.6833, "lon": 45.2167, "gemstone": "Sapphires", "role": "Major sapphire deposit discovered 1998", "annual_value_billions": 0.3},
        {"location": "Mikawa", "country": "Japan", "lat": 34.8000, "lon": 137.3000, "gemstone": "Pearls", "role": "Mikimoto cultured pearl origin (Ise Bay)", "annual_value_billions": 1.5},
        {"location": "Tahiti (Papeete)", "country": "French Polynesia", "lat": -17.5516, "lon": -149.5585, "gemstone": "Black pearls", "role": "Famous Tahitian black pearl farms", "annual_value_billions": 0.2},
        {"location": "Broome", "country": "Australia", "lat": -17.9614, "lon": 122.2359, "gemstone": "South Sea pearls", "role": "Premier South Sea pearl farming", "annual_value_billions": 0.4},
    ]
    return pd.DataFrame(data)


def _render_jewelry_gemstones():
    """Map 6: Jewelry & Gemstones."""
    df = _get_jewelry_gemstones()
    st.markdown("#### World Jewelry & Gemstone Origins")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Total Value ($B)", round(df["annual_value_billions"].sum(), 1))
    c4.metric("Top Hub", df.loc[df["annual_value_billions"].idxmax(), "location"])

    top10 = df.nlargest(10, "annual_value_billions")
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(top10["location"].values[::-1], top10["annual_value_billions"].values[::-1],
            color=[_color_for(i) for i in range(10)])
    ax.set_xlabel("Annual Value ($ Billions)")
    ax.set_title("Top 10 Jewelry & Gemstone Hubs by Value")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['location'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Gemstone: {escape(row['gemstone'])}<br>"
            f"Role: {escape(row['role'])}<br>"
            f"Annual Value: ${row['annual_value_billions']}B"
        )
        radius = max(5, min(15, row["annual_value_billions"] / 2))
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=ACCENT_AMBER,
            fill=True,
            fill_color=ACCENT_AMBER,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{escape(row['location'])} - {escape(row['gemstone'])}",
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["location", "country", "gemstone", "role", "annual_value_billions"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "jewelry_gemstones.csv", "text/csv",
                       key="dl_jewelry_gemstones")


# =====================================================================
# 7. TRADITIONAL CLOTHING
# =====================================================================
@st.cache_data(ttl=3600)
def _get_traditional_clothing():
    data = [
        {"garment": "Kimono", "country": "Japan", "region": "Kyoto", "lat": 35.0116, "lon": 135.7681, "description": "Iconic wrapped robe with obi sash, silk or cotton", "era": "Heian period (794 AD)"},
        {"garment": "Sari", "country": "India", "region": "Varanasi", "lat": 25.3176, "lon": 82.9739, "description": "5-9 meter draped fabric, Banarasi silk most prized", "era": "Indus Valley (2800 BC)"},
        {"garment": "Hanbok", "country": "South Korea", "region": "Seoul", "lat": 37.5665, "lon": 126.9780, "description": "Vibrant jeogori jacket and chima skirt", "era": "Three Kingdoms (1st century BC)"},
        {"garment": "Ao Dai", "country": "Vietnam", "region": "Hue", "lat": 16.4637, "lon": 107.5909, "description": "Fitted tunic over flowing trousers", "era": "Nguyen Dynasty (1802)"},
        {"garment": "Dirndl & Lederhosen", "country": "Germany/Austria", "region": "Munich", "lat": 48.1351, "lon": 11.5820, "description": "Alpine dress and leather breeches", "era": "18th century peasant wear"},
        {"garment": "Kilt", "country": "Scotland", "region": "Edinburgh", "lat": 55.9533, "lon": -3.1883, "description": "Pleated tartan wool skirt, clan patterns", "era": "16th century Highlands"},
        {"garment": "Dashiki", "country": "West Africa", "region": "Lagos", "lat": 6.5244, "lon": 3.3792, "description": "Colorful pullover garment with V-shaped collar", "era": "Yoruba tradition, centuries old"},
        {"garment": "Cheongsam / Qipao", "country": "China", "region": "Shanghai", "lat": 31.2304, "lon": 121.4737, "description": "Form-fitting dress with mandarin collar", "era": "1920s Shanghai (modernized)"},
        {"garment": "Flamenco Dress (Traje de Flamenca)", "country": "Spain", "region": "Seville", "lat": 37.3891, "lon": -5.9845, "description": "Ruffled polka-dot dress for dance", "era": "19th century Andalusia"},
        {"garment": "Caftan / Djellaba", "country": "Morocco", "region": "Fez", "lat": 34.0181, "lon": -5.0078, "description": "Long flowing robe with hood, ornate embroidery", "era": "Mesopotamian origins, 600 BC"},
        {"garment": "Toga", "country": "Italy", "region": "Rome", "lat": 41.9028, "lon": 12.4964, "description": "Draped cloth of Roman citizens", "era": "Roman Republic (509 BC)"},
        {"garment": "Sarong", "country": "Indonesia", "region": "Bali", "lat": -8.3405, "lon": 115.0920, "description": "Wrapped tubular cloth, batik patterns", "era": "Southeast Asian tradition"},
        {"garment": "Poncho", "country": "Peru", "region": "Cusco", "lat": -13.5319, "lon": -71.9675, "description": "Woven rectangular cloak with head opening", "era": "Pre-Inca Andean cultures (500 AD)"},
        {"garment": "Thobe / Dishdasha", "country": "Saudi Arabia", "region": "Riyadh", "lat": 24.7136, "lon": 46.6753, "description": "Long white ankle-length robe", "era": "Arabian Peninsula tradition"},
        {"garment": "Sherwani", "country": "India", "region": "Lucknow", "lat": 26.8467, "lon": 80.9462, "description": "Long coat-like garment for formal occasions", "era": "Mughal era (16th century)"},
        {"garment": "Huipil", "country": "Mexico/Guatemala", "region": "Oaxaca", "lat": 17.0732, "lon": -96.7266, "description": "Woven blouse with indigenous motifs", "era": "Pre-Columbian Maya tradition"},
        {"garment": "Kente Cloth", "country": "Ghana", "region": "Kumasi", "lat": 6.6885, "lon": -1.6244, "description": "Handwoven strip cloth, Ashanti royal fabric", "era": "17th century Ashanti Kingdom"},
        {"garment": "Deel", "country": "Mongolia", "region": "Ulaanbaatar", "lat": 47.8864, "lon": 106.9057, "description": "Padded wrapped robe for harsh steppe climate", "era": "Mongol Empire era"},
        {"garment": "Shalwar Kameez", "country": "Pakistan", "region": "Lahore", "lat": 31.5204, "lon": 74.3587, "description": "Tunic and loose trousers, national dress", "era": "Central Asian origin (12th century)"},
        {"garment": "Gho & Kira", "country": "Bhutan", "region": "Thimphu", "lat": 27.4728, "lon": 89.6393, "description": "Knee-length robe (men) and ankle dress (women)", "era": "17th century, still mandatory"},
        {"garment": "Bunad", "country": "Norway", "region": "Bergen", "lat": 60.3913, "lon": 5.3221, "description": "Regional folk costume with silver jewelry", "era": "19th century national romanticism"},
        {"garment": "Sarafan", "country": "Russia", "region": "Moscow", "lat": 55.7558, "lon": 37.6173, "description": "Jumper dress worn over rubakha blouse", "era": "14th century Russian folk"},
        {"garment": "Agbada", "country": "Nigeria", "region": "Ibadan", "lat": 7.3775, "lon": 3.9470, "description": "Wide-sleeved flowing robe, Yoruba formal wear", "era": "Yoruba and Hausa tradition"},
        {"garment": "Barong Tagalog", "country": "Philippines", "region": "Manila", "lat": 14.5995, "lon": 120.9842, "description": "Embroidered sheer formal shirt", "era": "Spanish colonial era adaptation"},
        {"garment": "Kebaya", "country": "Indonesia/Malaysia", "region": "Yogyakarta", "lat": -7.7956, "lon": 110.3695, "description": "Fitted lace blouse paired with batik sarong", "era": "15th century Javanese courts"},
        {"garment": "Fustanella", "country": "Greece", "region": "Athens", "lat": 37.9838, "lon": 23.7275, "description": "Pleated white skirt worn by Evzones guards", "era": "Albanian/Greek folk tradition"},
        {"garment": "Sampot", "country": "Cambodia", "region": "Phnom Penh", "lat": 11.5564, "lon": 104.9282, "description": "Wrapped lower garment, silk brocade", "era": "Angkor era (9th century)"},
        {"garment": "Changshan", "country": "China", "region": "Beijing", "lat": 39.9042, "lon": 116.4074, "description": "Full-length men's mandarin-collar robe", "era": "Manchu Qing Dynasty"},
        {"garment": "Gele (Headwrap)", "country": "Nigeria", "region": "Abeokuta", "lat": 7.1557, "lon": 3.3450, "description": "Elaborately wrapped headtie for ceremonies", "era": "Yoruba tradition, centuries old"},
        {"garment": "Maasai Shuka", "country": "Kenya/Tanzania", "region": "Narok", "lat": -1.0834, "lon": 35.8693, "description": "Red plaid cloth wrap of Maasai warriors", "era": "19th century adoption (replaced leather)"},
    ]
    return pd.DataFrame(data)


def _render_traditional_clothing():
    """Map 7: Traditional Clothing."""
    df = _get_traditional_clothing()
    st.markdown("#### Traditional Clothing Around the World")
    c1, c2, c3 = st.columns(3)
    c1.metric("Garments", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Regions", df["region"].nunique())

    continent_map = {
        "Japan": "Asia", "India": "Asia", "South Korea": "Asia", "Vietnam": "Asia",
        "China": "Asia", "Mongolia": "Asia", "Pakistan": "Asia", "Bhutan": "Asia",
        "Cambodia": "Asia", "Indonesia": "Asia", "Indonesia/Malaysia": "Asia",
        "Philippines": "Asia", "Saudi Arabia": "Middle East",
        "Germany/Austria": "Europe", "Scotland": "Europe", "Spain": "Europe",
        "Italy": "Europe", "Norway": "Europe", "Russia": "Europe", "Greece": "Europe",
        "Morocco": "Africa", "Ghana": "Africa", "Nigeria": "Africa",
        "Kenya/Tanzania": "Africa", "West Africa": "Africa",
        "Peru": "Americas", "Mexico/Guatemala": "Americas",
    }
    df["continent"] = df["country"].map(continent_map).fillna("Other")
    cont_counts = df["continent"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(cont_counts.index[::-1], cont_counts.values[::-1],
            color=[_color_for(i) for i in range(len(cont_counts))])
    ax.set_xlabel("Number of Garments")
    ax.set_title("Traditional Garments by Continent")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(zoom=2)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['garment'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Region: {escape(row['region'])}<br>"
            f"Description: {escape(row['description'])}<br>"
            f"Era: {escape(row['era'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=ACCENT_RED,
            fill=True,
            fill_color=ACCENT_RED,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{escape(row['garment'])} ({escape(row['country'])})",
        ).add_to(m)
    _show_map(m)

    display_cols = ["garment", "country", "region", "description", "era"]
    st.dataframe(df[display_cols], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df[display_cols]), "traditional_clothing.csv", "text/csv",
                       key="dl_traditional_clothing")


# =====================================================================
# 8. SILK ROAD TEXTILE TRADE
# =====================================================================
@st.cache_data(ttl=3600)
def _get_silk_road():
    data = [
        {"location": "Xi'an (Chang'an)", "country": "China", "lat": 34.2658, "lon": 108.9541, "role": "Eastern terminus, silk production origin", "goods": "Silk, brocade, damask", "era": "206 BC - Tang Dynasty"},
        {"location": "Dunhuang", "country": "China", "lat": 40.1421, "lon": 94.6619, "role": "Gateway to western deserts, Mogao Caves", "goods": "Silk, paper, lacquerware", "era": "Han Dynasty onward"},
        {"location": "Turpan", "country": "China", "lat": 42.9513, "lon": 89.1895, "role": "Oasis city, textile depot", "goods": "Cotton, silk, dried fruits", "era": "1st century AD onward"},
        {"location": "Kashgar", "country": "China", "lat": 39.4547, "lon": 75.9797, "role": "Major crossroads of northern and southern routes", "goods": "Silk, jade, carpets", "era": "2nd century BC onward"},
        {"location": "Samarkand", "country": "Uzbekistan", "lat": 39.6542, "lon": 66.9597, "role": "Timurid textile center, ikat weaving capital", "goods": "Silk ikat, cotton, gold thread", "era": "4th century BC - 15th century AD"},
        {"location": "Bukhara", "country": "Uzbekistan", "lat": 39.7747, "lon": 64.4286, "role": "Major silk trading bazaar, suzani embroidery", "goods": "Silk carpets, suzani, gold embroidery", "era": "6th century onward"},
        {"location": "Khiva", "country": "Uzbekistan", "lat": 41.3787, "lon": 60.3568, "role": "Silk weaving, carpet making center", "goods": "Silk, cotton, carpets", "era": "6th century onward"},
        {"location": "Merv (Mary)", "country": "Turkmenistan", "lat": 37.6600, "lon": 62.1600, "role": "One of world's largest ancient cities", "goods": "Silk, cotton, Turkmen carpets", "era": "3rd century BC - 13th century AD"},
        {"location": "Balkh", "country": "Afghanistan", "lat": 36.7580, "lon": 66.8975, "role": "Mother of Cities, textile trade hub", "goods": "Silk, cotton, lapis lazuli", "era": "6th century BC onward"},
        {"location": "Kabul", "country": "Afghanistan", "lat": 34.5553, "lon": 69.2075, "role": "Mountain pass trade junction", "goods": "Silk, wool, gemstones", "era": "Ancient crossroads"},
        {"location": "Tehran", "country": "Iran", "lat": 35.6892, "lon": 51.3890, "role": "Persian textile trading center", "goods": "Persian silk, carpets, brocade", "era": "Safavid era (16th century)"},
        {"location": "Isfahan", "country": "Iran", "lat": 32.6546, "lon": 51.6680, "role": "Safavid capital, finest Persian textiles", "goods": "Silk carpets, velvet, termeh", "era": "Safavid Dynasty (1501-1736)"},
        {"location": "Tabriz", "country": "Iran", "lat": 38.0800, "lon": 46.2919, "role": "Grand bazaar textile center", "goods": "Silk carpets, wool textiles", "era": "Mongol-era trading post"},
        {"location": "Baghdad", "country": "Iraq", "lat": 33.3152, "lon": 44.3661, "role": "Abbasid caliphate textile center", "goods": "Silk, cotton, tiraz textiles", "era": "8th - 13th century"},
        {"location": "Aleppo", "country": "Syria", "lat": 36.2021, "lon": 37.1343, "role": "Medieval textile souk, brocade center", "goods": "Silk brocade, cotton, soap", "era": "Antiquity through Ottoman era"},
        {"location": "Damascus", "country": "Syria", "lat": 33.5138, "lon": 36.2765, "role": "Damask fabric origin, silk weaving", "goods": "Damask silk, brocade, steel", "era": "Named fabric after this city"},
        {"location": "Antioch (Antakya)", "country": "Turkey", "lat": 36.2000, "lon": 36.1500, "role": "Roman textile trading port", "goods": "Silk, purple dye, linen", "era": "Roman period onward"},
        {"location": "Constantinople (Istanbul)", "country": "Turkey", "lat": 41.0082, "lon": 28.9784, "role": "Western terminus, Byzantine silk monopoly", "goods": "Imperial purple silk, brocade, gold thread", "era": "4th - 15th century AD"},
        {"location": "Venice", "country": "Italy", "lat": 45.4408, "lon": 12.3155, "role": "European silk trade gateway, velvet production", "goods": "Silk velvet, brocade, glass beads", "era": "13th - 17th century"},
        {"location": "Genoa", "country": "Italy", "lat": 44.4056, "lon": 8.9463, "role": "Rival maritime silk trade port", "goods": "Velvet, silk, jeans fabric (origin of denim)", "era": "Medieval maritime republic"},
        {"location": "Lucca", "country": "Italy", "lat": 43.8376, "lon": 10.4951, "role": "Medieval European silk weaving capital", "goods": "Silk damask, brocade, taffeta", "era": "12th - 14th century"},
        {"location": "Lyon", "country": "France", "lat": 45.7640, "lon": 4.8357, "role": "European silk capital from Renaissance", "goods": "Jacquard silk, haute couture fabrics", "era": "15th century - present"},
        {"location": "Bruges", "country": "Belgium", "lat": 51.2093, "lon": 3.2247, "role": "Flemish textile trading center", "goods": "Wool, lace, tapestries", "era": "13th - 15th century"},
        {"location": "Almaty", "country": "Kazakhstan", "lat": 43.2220, "lon": 76.8512, "role": "Northern silk road branch", "goods": "Felt, silk, horse goods", "era": "Nomadic trade traditions"},
        {"location": "Tashkent", "country": "Uzbekistan", "lat": 41.2995, "lon": 69.2401, "role": "Central Asian trade hub", "goods": "Cotton, silk, adras ikat", "era": "2nd century BC onward"},
        {"location": "Palmyra", "country": "Syria", "lat": 34.5502, "lon": 38.2834, "role": "Desert oasis caravan stop", "goods": "Silk, Chinese goods westbound", "era": "1st - 3rd century AD"},
        {"location": "Hangzhou", "country": "China", "lat": 30.2741, "lon": 120.1551, "role": "Song Dynasty silk capital, finest brocades", "goods": "Silk brocade, satin, parasols", "era": "Song Dynasty (960-1279)"},
        {"location": "Suzhou", "country": "China", "lat": 31.2990, "lon": 120.5853, "role": "Garden city, embroidery capital", "goods": "Su embroidery, silk, fans", "era": "Song Dynasty onward"},
        {"location": "Lanzhou", "country": "China", "lat": 36.0611, "lon": 103.8343, "role": "Yellow River crossing, Hexi Corridor gateway", "goods": "Silk, wool, tea", "era": "Han Dynasty corridor"},
        {"location": "Petra", "country": "Jordan", "lat": 30.3285, "lon": 35.4414, "role": "Nabataean caravan city, textile waypoint", "goods": "Silk transshipment, incense, spices", "era": "4th century BC - 2nd century AD"},
        {"location": "Alexandria", "country": "Egypt", "lat": 31.2001, "lon": 29.9187, "role": "Mediterranean textile port, linen center", "goods": "Linen, silk, cotton from India", "era": "Ptolemaic era onward"},
        {"location": "Quanzhou", "country": "China", "lat": 24.8740, "lon": 118.6757, "role": "Maritime Silk Road origin, largest medieval port", "goods": "Silk, porcelain, tea", "era": "Song-Yuan Dynasty (10th-14th c.)"},
        {"location": "Muscat", "country": "Oman", "lat": 23.5880, "lon": 58.3829, "role": "Maritime silk road port, Indian Ocean trade", "goods": "Silk, textiles, frankincense", "era": "Ancient maritime hub"},
        {"location": "Ctesiphon (near Baghdad)", "country": "Iraq", "lat": 33.0947, "lon": 44.5820, "role": "Sassanid textile capital, silk weaving", "goods": "Sassanid silk, royal brocade", "era": "3rd - 7th century AD"},
        {"location": "Herat", "country": "Afghanistan", "lat": 34.3529, "lon": 62.2040, "role": "Timurid artistic center, carpet weaving", "goods": "Silk, wool carpets, miniatures", "era": "Timurid period (14th-15th c.)"},
        {"location": "Margilan", "country": "Uzbekistan", "lat": 40.4703, "lon": 71.7244, "role": "Silk ikat weaving center, Fergana Valley", "goods": "Atlas silk, adras ikat, khan-atlas", "era": "Ancient tradition still active"},
        {"location": "Khotan (Hotan)", "country": "China", "lat": 37.1120, "lon": 79.9302, "role": "Southern Silk Road, jade and silk hub", "goods": "Jade, silk, atlas fabric", "era": "2nd century BC onward"},
        {"location": "Taxila", "country": "Pakistan", "lat": 33.7463, "lon": 72.7988, "role": "Gandharan trade crossroads", "goods": "Silk, cotton, Buddhist art", "era": "6th century BC - 5th century AD"},
        {"location": "Surat", "country": "India", "lat": 21.1702, "lon": 72.8311, "role": "Indian Ocean maritime silk/cotton port", "goods": "Cotton textiles, silk, indigo dye", "era": "Mughal era, European trade"},
        {"location": "Calicut (Kozhikode)", "country": "India", "lat": 11.2588, "lon": 75.7804, "role": "Spice and calico cotton origin port", "goods": "Calico cotton, spices, silk imports", "era": "Medieval Indian Ocean trade"},
    ]
    return pd.DataFrame(data)


def _render_silk_road():
    """Map 8: Silk Road Textile Trade."""
    df = _get_silk_road()
    st.markdown("#### Silk Road Textile Trade Routes")
    c1, c2, c3 = st.columns(3)
    c1.metric("Trade Points", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Goods Types", df["goods"].str.split(",").explode().str.strip().nunique())

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Trade Points")
    ax.set_title("Silk Road Trade Points by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[38, 65], zoom=4)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['location'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Role: {escape(row['role'])}<br>"
            f"Goods: {escape(row['goods'])}<br>"
            f"Era: {escape(row['era'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=ACCENT_VIOLET,
            fill=True,
            fill_color=ACCENT_VIOLET,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=f"{escape(row['location'])}",
        ).add_to(m)

    # Draw approximate route lines
    route_coords = [
        [34.2658, 108.9541], [36.0611, 103.8343], [40.1421, 94.6619],
        [42.9513, 89.1895], [39.4547, 75.9797], [41.2995, 69.2401],
        [39.6542, 66.9597], [39.7747, 64.4286], [37.6600, 62.1600],
        [34.3529, 62.2040], [36.7580, 66.8975], [35.6892, 51.3890],
        [32.6546, 51.6680], [33.3152, 44.3661], [36.2021, 37.1343],
        [41.0082, 28.9784],
    ]
    folium.PolyLine(
        locations=route_coords,
        color=ACCENT_AMBER,
        weight=2,
        opacity=0.6,
        dash_array="8",
    ).add_to(m)
    _show_map(m)

    st.dataframe(df[["location", "country", "role", "goods", "era"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "silk_road_textile.csv", "text/csv",
                       key="dl_silk_road")


# =====================================================================
# 9. WATCH & HOROLOGY CENTERS
# =====================================================================
@st.cache_data(ttl=3600)
def _get_horology():
    data = [
        {"center": "Geneva", "country": "Switzerland", "lat": 46.2044, "lon": 6.1432, "specialty": "Haute horlogerie, complications", "brands": "Patek Philippe, Rolex, Vacheron Constantin", "heritage": "Geneva Seal since 1886"},
        {"center": "La Chaux-de-Fonds", "country": "Switzerland", "lat": 47.1035, "lon": 6.8296, "specialty": "Watch manufacturing, UNESCO city", "brands": "Girard-Perregaux, Zenith, Corum", "heritage": "UNESCO World Heritage, birthplace of Le Corbusier"},
        {"center": "Le Brassus (Vallee de Joux)", "country": "Switzerland", "lat": 46.5580, "lon": 6.2090, "specialty": "Ultra-complicated movements", "brands": "Audemars Piguet, Blancpain, Jaeger-LeCoultre", "heritage": "Cradle of haute horlogerie since 18th century"},
        {"center": "Biel/Bienne", "country": "Switzerland", "lat": 47.1368, "lon": 7.2467, "specialty": "Mass-market luxury, Swatch Group HQ", "brands": "Omega, Swatch, Tissot, Longines", "heritage": "Swiss watch industry capital"},
        {"center": "Schaffhausen", "country": "Switzerland", "lat": 47.6960, "lon": 8.6347, "specialty": "Precision engineering, pilot watches", "brands": "IWC Schaffhausen", "heritage": "Rhine River hydropower for watch manufacturing"},
        {"center": "Glashutte", "country": "Germany", "lat": 50.8513, "lon": 13.7829, "specialty": "German precision watchmaking", "brands": "A. Lange & Sohne, Glashutte Original, NOMOS", "heritage": "Saxon watchmaking tradition since 1845"},
        {"center": "Pforzheim", "country": "Germany", "lat": 48.8922, "lon": 8.6942, "specialty": "Jewelry and watch production", "brands": "Laco, Stowa, Tourby", "heritage": "Gold City, 250-year tradition"},
        {"center": "Le Locle", "country": "Switzerland", "lat": 47.0591, "lon": 6.7491, "specialty": "Watch manufacturing, UNESCO heritage", "brands": "Tissot (origin), Ulysse Nardin (origin)", "heritage": "UNESCO World Heritage watch town"},
        {"center": "Besancon", "country": "France", "lat": 47.2378, "lon": 6.0241, "specialty": "French watchmaking capital", "brands": "Lip, French Haute Horlogerie ateliers", "heritage": "Historic observatory for chronometer testing"},
        {"center": "Tokyo (Ginza)", "country": "Japan", "lat": 35.6717, "lon": 139.7649, "specialty": "Precision quartz revolution, Spring Drive", "brands": "Grand Seiko, Seiko, Citizen, Casio", "heritage": "Quartz revolution origin (1969)"},
        {"center": "Suwa (Nagano)", "country": "Japan", "lat": 36.0393, "lon": 138.1140, "specialty": "Seiko Epson manufacturing", "brands": "Seiko, Orient", "heritage": "Grand Seiko Studio Shizukuishi"},
        {"center": "Fleurier", "country": "Switzerland", "lat": 46.9020, "lon": 6.5810, "specialty": "Fine watchmaking, Fleurier Quality Foundation", "brands": "Parmigiani Fleurier, Chopard movements", "heritage": "Fleurier Quality Foundation certification"},
        {"center": "Le Sentier", "country": "Switzerland", "lat": 46.6010, "lon": 6.2350, "specialty": "Movement manufacturing", "brands": "Jaeger-LeCoultre", "heritage": "Manufacture complète since 1833"},
        {"center": "Grenchen", "country": "Switzerland", "lat": 47.1920, "lon": 7.3960, "specialty": "ETA movement production", "brands": "Breitling, ETA SA", "heritage": "Supplies movements to hundreds of brands"},
        {"center": "Coventry", "country": "UK", "lat": 52.4068, "lon": -1.5197, "specialty": "Historic British watchmaking", "brands": "Heritage: Thomas Mudge, Joseph Williamson", "heritage": "British watchmaking capital 17th-19th century"},
        {"center": "Waltham", "country": "USA", "lat": 42.3765, "lon": -71.2356, "specialty": "American mass-production watchmaking", "brands": "Waltham Watch Company (historic)", "heritage": "Pioneered machine-made interchangeable parts"},
        {"center": "Lancaster", "country": "USA", "lat": 40.0379, "lon": -76.3055, "specialty": "American precision watchmaking", "brands": "Hamilton Watch Company (historic)", "heritage": "Railroad chronometer production"},
        {"center": "Neuchatel", "country": "Switzerland", "lat": 46.9920, "lon": 6.9310, "specialty": "Watch research, observatory testing", "brands": "Tag Heuer (origin nearby)", "heritage": "Neuchatel Observatory chronometer trials"},
        {"center": "Sainte-Croix", "country": "Switzerland", "lat": 46.8220, "lon": 6.5030, "specialty": "Music boxes, automata, micro-mechanics", "brands": "Reuge, PAMP, micro-component makers", "heritage": "Centre of micro-mechanical arts"},
        {"center": "Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579, "specialty": "Mass-market watch manufacturing", "brands": "Fiyta, Seagull movements assembly", "heritage": "World's largest watch production volume"},
        {"center": "Tianjin", "country": "China", "lat": 39.3434, "lon": 117.3616, "specialty": "Chinese mechanical movement production", "brands": "Seagull Watch (Sea-Gull)", "heritage": "First Chinese mechanical movement (1955)"},
        {"center": "Jura Mountains (various)", "country": "Switzerland", "lat": 47.2000, "lon": 6.9500, "specialty": "Component suppliers, springs, dials", "brands": "Hundreds of specialized suppliers", "heritage": "Entire region dedicated to horology supply chain"},
        {"center": "Mumbai", "country": "India", "lat": 19.0760, "lon": 72.8777, "specialty": "Affordable watch market, Titan HQ", "brands": "Titan, HMT (historic), Fastrack", "heritage": "India's largest watch manufacturer"},
        {"center": "Manaus", "country": "Brazil", "lat": -3.1190, "lon": -60.0217, "specialty": "Watch assembly, free trade zone", "brands": "Orient (Brazil), Technos, Mondaine (Brazil)", "heritage": "South American watch assembly hub"},
        {"center": "Seoul (Gangnam)", "country": "South Korea", "lat": 37.4979, "lon": 127.0276, "specialty": "Watch retail, micro-brand movement", "brands": "Samsung Galaxy Watch, Korean micro-brands", "heritage": "Growing smartwatch and indie scene"},
    ]
    return pd.DataFrame(data)


def _render_horology():
    """Map 9: Watch & Horology Centers."""
    df = _get_horology()
    st.markdown("#### Watch & Horology Centers of the World")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Centers", len(df))
    c2.metric("Countries", df["country"].nunique())
    swiss_count = len(df[df["country"] == "Switzerland"])
    c3.metric("Swiss Centers", swiss_count)
    c4.metric("Non-Swiss", len(df) - swiss_count)

    country_counts = df["country"].value_counts()
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Centers")
    ax.set_title("Horology Centers by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[47, 7], zoom=5)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['center'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Specialty: {escape(row['specialty'])}<br>"
            f"Brands: {escape(row['brands'])}<br>"
            f"Heritage: {escape(row['heritage'])}"
        )
        color = ACCENT_CYAN if row["country"] == "Switzerland" else ACCENT_PINK
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(row["center"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["center", "country", "specialty", "brands", "heritage"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "horology_centers.csv", "text/csv",
                       key="dl_horology")


# =====================================================================
# 10. PERFUME & FRAGRANCE
# =====================================================================
@st.cache_data(ttl=3600)
def _get_perfume():
    data = [
        {"location": "Grasse", "country": "France", "lat": 43.6590, "lon": 6.9215, "role": "World perfume capital, flower fields", "specialty": "Jasmine, rose, tuberose, lavender extraction", "brands": "Chanel No. 5 sourcing, Fragonard, Molinard, Galimard"},
        {"location": "Paris", "country": "France", "lat": 48.8566, "lon": 2.3522, "role": "Global fragrance industry HQ", "specialty": "Haute parfumerie, master perfumers (nez)", "brands": "Guerlain, Dior, Chanel, Frederic Malle"},
        {"location": "New York", "country": "USA", "lat": 40.7128, "lon": -74.0060, "role": "Fragrance marketing and HQ capital", "specialty": "Celebrity fragrances, niche brands", "brands": "Estee Lauder, Le Labo, Bond No. 9, By Kilian"},
        {"location": "Kannauj", "country": "India", "lat": 27.0551, "lon": 79.9137, "role": "India's perfume city, attar tradition", "specialty": "Traditional attar (essential oil) distillation", "brands": "M.L. Ramnarain, Pragati, centuries-old attarwalas"},
        {"location": "Taif", "country": "Saudi Arabia", "lat": 21.2703, "lon": 40.4158, "role": "Arabian rose perfume center", "specialty": "Taif rose water, oud, Arabian perfumery", "brands": "Abdul Samad Al Qurashi, Taif rose producers"},
        {"location": "Geneva", "country": "Switzerland", "lat": 46.2044, "lon": 6.1432, "role": "Fragrance conglomerates HQ", "specialty": "Firmenich, Givaudan ingredient houses", "brands": "Firmenich, Givaudan (world's largest)"},
        {"location": "Florence", "country": "Italy", "lat": 43.7696, "lon": 11.2558, "role": "Renaissance perfumery origin", "specialty": "Oldest pharmacy perfumes, iris root (orris)", "brands": "Santa Maria Novella (1221), Aqua Flor, Lorenzo Villoresi"},
        {"location": "London", "country": "UK", "lat": 51.5074, "lon": -0.1278, "role": "British perfumery tradition, niche hub", "specialty": "English garden scents, tailored fragrances", "brands": "Penhaligon's, Jo Malone, Floris (1730)"},
        {"location": "Cologne (Koln)", "country": "Germany", "lat": 50.9375, "lon": 6.9603, "role": "Birthplace of eau de cologne (1709)", "specialty": "Citrus-based cologne tradition", "brands": "4711, Farina (original Eau de Cologne, 1709)"},
        {"location": "Dubai", "country": "UAE", "lat": 25.2048, "lon": 55.2708, "role": "Arabian perfume culture, oud capital", "specialty": "Oud, bakhoor, Arabian attars", "brands": "Ajmal, Swiss Arabian, Amouage boutiques"},
        {"location": "Muscat", "country": "Oman", "lat": 23.5880, "lon": 58.3829, "role": "Frankincense land, Amouage origin", "specialty": "Frankincense, oud, luxury Arabian perfumery", "brands": "Amouage (1983, royal warrant)"},
        {"location": "Holzminden", "country": "Germany", "lat": 51.8300, "lon": 9.4500, "role": "Symrise global ingredient HQ", "specialty": "Fragrance and flavor ingredient synthesis", "brands": "Symrise (world's 3rd largest flavor/fragrance)"},
        {"location": "Barcelona", "country": "Spain", "lat": 41.3874, "lon": 2.1686, "role": "Spanish perfumery, Antonio Puig HQ", "specialty": "Mediterranean florals, Puig luxury group", "brands": "Puig (Paco Rabanne, Carolina Herrera, Jean Paul Gaultier)"},
        {"location": "Dhofar (Salalah)", "country": "Oman", "lat": 17.0151, "lon": 54.0924, "role": "Frankincense origin, UNESCO heritage", "specialty": "Boswellia sacra frankincense harvesting", "brands": "Traditional frankincense trade since antiquity"},
        {"location": "Provence (Valensole)", "country": "France", "lat": 43.8367, "lon": 5.9833, "role": "Lavender fields, aromatic herb capital", "specialty": "Lavender, rosemary, thyme essential oils", "brands": "L'Occitane en Provence sourcing"},
        {"location": "Isfahan", "country": "Iran", "lat": 32.6546, "lon": 51.6680, "role": "Persian rosewater tradition", "specialty": "Damask rose distillation, golab production", "brands": "Kashan rose water artisans (Qamsar)"},
        {"location": "Kyoto", "country": "Japan", "lat": 35.0116, "lon": 135.7681, "role": "Japanese incense and kodo tradition", "specialty": "Kodo (way of incense), agarwood appreciation", "brands": "Shoyeido (1705), Nippon Kodo, Kungyokudo"},
        {"location": "Mysore", "country": "India", "lat": 12.2958, "lon": 76.6394, "role": "Indian sandalwood capital", "specialty": "Santalum album, world's finest sandalwood", "brands": "Karnataka Soaps (Mysore Sandal), traditional attars"},
        {"location": "Madagascar (Antsirabe)", "country": "Madagascar", "lat": -19.8659, "lon": 47.0333, "role": "Vanilla and ylang-ylang origin", "specialty": "Bourbon vanilla, ylang-ylang, clove", "brands": "Vanilla suppliers to global perfume industry"},
        {"location": "Comoros Islands", "country": "Comoros", "lat": -12.2361, "lon": 44.3504, "role": "Ylang-ylang capital of the world", "specialty": "70% of world's ylang-ylang essential oil", "brands": "Global supply for Chanel No. 5 and others"},
        {"location": "Egypt (Fayoum)", "country": "Egypt", "lat": 29.3084, "lon": 30.8428, "role": "Ancient perfumery origin, lotus scent", "specialty": "Ancient Egyptian kyphi, enfleurage techniques", "brands": "Replicated ancient fragrances, modern artisans"},
        {"location": "Seville", "country": "Spain", "lat": 37.3891, "lon": -5.9845, "role": "Bitter orange blossom (neroli) capital", "specialty": "Neroli, petitgrain, bitter orange essential oils", "brands": "Supplied to global fine fragrance houses"},
        {"location": "Calabria", "country": "Italy", "lat": 38.9100, "lon": 16.5877, "role": "Bergamot capital of the world", "specialty": "95% of world's bergamot production", "brands": "Essential for Earl Grey and hundreds of perfumes"},
        {"location": "Haiti (Port-au-Prince)", "country": "Haiti", "lat": 18.5944, "lon": -72.3074, "role": "Vetiver production center", "specialty": "World's major vetiver essential oil producer", "brands": "Vetiver supplied to Guerlain, Chanel, etc."},
        {"location": "Reunion Island", "country": "France (overseas)", "lat": -21.1151, "lon": 55.5364, "role": "Bourbon geranium and vanilla", "specialty": "Geranium bourbon, vanilla bourbon", "brands": "High-quality botanical ingredients"},
        {"location": "Aomori", "country": "Japan", "lat": 40.8246, "lon": 140.7400, "role": "Japanese hiba wood and hinoki source", "specialty": "Hinoki cypress, hiba arborvitae essential oils", "brands": "Japanese aromatherapy and fragrance houses"},
        {"location": "Sandalwood Coast (Timor)", "country": "East Timor", "lat": -8.5569, "lon": 125.5603, "role": "Southeast Asian sandalwood source", "specialty": "Santalum album wild harvesting", "brands": "Traditional and export sandalwood oil"},
        {"location": "Versailles", "country": "France", "lat": 48.8014, "lon": 2.1301, "role": "Royal perfumery, glove-making perfumers", "specialty": "Court of Louis XIV perfume culture origin", "brands": "Historical birthplace of French perfume culture"},
        {"location": "Beirut", "country": "Lebanon", "lat": 33.8938, "lon": 35.5018, "role": "Middle Eastern niche perfumery hub", "specialty": "Cross-cultural East-West fragrance blending", "brands": "Berdoues, Oud Milano boutiques, local niche houses"},
        {"location": "Cape Town", "country": "South Africa", "lat": -33.9249, "lon": 18.4241, "role": "Fynbos botanical fragrance source", "specialty": "Cape fynbos, buchu, rooibos aromatics", "brands": "African Botanics, local artisan perfumers"},
    ]
    return pd.DataFrame(data)


def _render_perfume():
    """Map 10: Perfume & Fragrance."""
    df = _get_perfume()
    st.markdown("#### Perfume & Fragrance Capitals")
    c1, c2, c3 = st.columns(3)
    c1.metric("Locations", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Roles", df["role"].nunique())

    country_counts = df["country"].value_counts().head(10)
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.barh(country_counts.index[::-1], country_counts.values[::-1],
            color=[_color_for(i) for i in range(len(country_counts))])
    ax.set_xlabel("Number of Locations")
    ax.set_title("Perfume & Fragrance Locations by Country")
    st.image(_fig_to_bytes(fig), width=800)

    m = _base_map(center=[35, 20], zoom=3)
    for _, row in df.iterrows():
        popup_html = (
            f"<b>{escape(row['location'])}</b><br>"
            f"Country: {escape(row['country'])}<br>"
            f"Role: {escape(row['role'])}<br>"
            f"Specialty: {escape(row['specialty'])}<br>"
            f"Brands: {escape(row['brands'])}"
        )
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=ACCENT_PINK,
            fill=True,
            fill_color=ACCENT_PINK,
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=escape(row["location"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["location", "country", "role", "specialty", "brands"]], width="stretch")
    st.download_button("Download CSV", _df_to_csv(df), "perfume_fragrance.csv", "text/csv",
                       key="dl_perfume")


# =====================================================================
# MAP OPTIONS REGISTRY
# =====================================================================
MAP_OPTIONS = {
    "Fashion Capitals": _render_fashion_capitals,
    "Luxury Brand HQs": _render_luxury_brands,
    "Textile Production Hubs": _render_textile_production,
    "Fashion Week Cities": _render_fashion_weeks,
    "Design Schools": _render_design_schools,
    "Jewelry & Gemstones": _render_jewelry_gemstones,
    "Traditional Clothing": _render_traditional_clothing,
    "Silk Road Textile Trade": _render_silk_road,
    "Watch & Horology Centers": _render_horology,
    "Perfume & Fragrance": _render_perfume,
}


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================
def render_fashion_maps_tab():
    """Main entry point for the Fashion & Design Maps tab."""
    st.markdown(
        '<div class="tab-header pink">'
        "<h4>Fashion &amp; Design Maps</h4>"
        "<p>Explore global fashion capitals, luxury brands, textile trade routes, "
        "traditional garments, jewelry origins, and fragrance houses.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    selected_map = st.selectbox(
        "Select map type",
        list(MAP_OPTIONS.keys()),
        key="fashion_maps_select",
    )

    if st.button("Generate Map", key="fashion_maps_generate", type="primary"):
        with st.spinner("Building map..."):
            MAP_OPTIONS[selected_map]()
    else:
        st.info("Select a map type above and click **Generate Map** to explore.")
