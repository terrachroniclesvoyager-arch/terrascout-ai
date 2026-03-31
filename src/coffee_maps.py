"""
Coffee & Cafe Culture Explorer module for TerraScout AI.
Displays hardcoded locations for coffee-growing origins, famous cafes,
specialty roasters, processing methods, trade routes, Japanese kissaten,
espresso machine heritage, visitor plantations, barista championships,
and coffee museums worldwide.
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


# ========================================================================
# COLOR PALETTE
# ========================================================================
COFFEE_COLORS = {
    "arabica": "#10b981",
    "robusta": "#f59e0b",
    "liberica": "#8b5cf6",
    "cafe": "#ec4899",
    "roaster": "#06b6d4",
    "process": "#ef4444",
    "route": "#f97316",
    "kissaten": "#a855f7",
    "machine": "#3b82f6",
    "plantation": "#22c55e",
    "barista": "#e879f9",
    "museum": "#14b8a6",
}


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================
def _popup(name, details):
    """Build a rich HTML popup string with escaped content."""
    safe_name = html_module.escape(str(name))
    rows = ""
    for k, v in details.items():
        safe_key = html_module.escape(str(k))
        safe_val = html_module.escape(str(v))
        rows += (
            f"<tr>"
            f"<td style='padding:4px 10px;color:#10b981;font-weight:600;"
            f"white-space:nowrap;vertical-align:top;'>{safe_key}</td>"
            f"<td style='padding:4px 10px;color:#e8ecf4;'>{safe_val}</td>"
            f"</tr>"
        )
    return (
        f"<div style=\"font-family:'Segoe UI',Arial,sans-serif;"
        f"background:#1a1a2e;border:1px solid #10b981;border-radius:10px;"
        f"padding:12px 14px;min-width:240px;max-width:360px;\">"
        f"<h4 style=\"margin:0 0 8px 0;color:#10b981;font-size:14px;\">"
        f"{safe_name}</h4>"
        f"<table style=\"border-collapse:collapse;width:100%;\">{rows}</table>"
        f"</div>"
    )


def _build_map(locations, zoom=3, center=None):
    """Create a Folium map using CartoDB dark_matter tiles."""
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
    for loc in locations:
        details = {
            k: v
            for k, v in loc.items()
            if k not in ("lat", "lon", "name", "color")
        }
        color = loc.get("color", "green")
        folium.Marker(
            location=[loc["lat"], loc["lon"]],
            popup=folium.Popup(
                _popup(loc["name"], details),
                max_width=360,
            ),
            tooltip=loc["name"],
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)
    return m


def _show_map_and_data(locations, zoom=3, center=None, csv_prefix="coffee"):
    """Render the interactive map, dataframe, and CSV download."""
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
        key=f"coffee_dl_{csv_prefix}_{len(locations)}",
    )


# ========================================================================
# DATA: 1. COFFEE BELT ORIGINS
# ========================================================================
COFFEE_BELT_ORIGINS = [
    {"name": "Yirgacheffe, Ethiopia", "lat": 6.16, "lon": 38.21, "Country": "Ethiopia", "Species": "Arabica", "Altitude": "1,700-2,200m", "Flavor": "Floral, citrus, jasmine", "Notes": "Birthplace of Arabica coffee; wild forest coffee", "color": "green"},
    {"name": "Sidamo, Ethiopia", "lat": 6.71, "lon": 38.48, "Country": "Ethiopia", "Species": "Arabica", "Altitude": "1,550-2,200m", "Flavor": "Berry, wine-like, complex", "Notes": "One of three trademarked Ethiopian origins", "color": "green"},
    {"name": "Harar, Ethiopia", "lat": 9.31, "lon": 42.12, "Country": "Ethiopia", "Species": "Arabica", "Altitude": "1,500-2,100m", "Flavor": "Blueberry, chocolate, spice", "Notes": "Ancient walled city; dry-processed heritage", "color": "green"},
    {"name": "Kaffa Forest, Ethiopia", "lat": 7.30, "lon": 36.25, "Country": "Ethiopia", "Species": "Arabica", "Altitude": "1,500-2,000m", "Flavor": "Wild, earthy, fruit", "Notes": "Legendary origin of the word 'coffee'; UNESCO biosphere", "color": "green"},
    {"name": "Huila, Colombia", "lat": 2.53, "lon": -75.53, "Country": "Colombia", "Species": "Arabica", "Altitude": "1,250-2,000m", "Flavor": "Caramel, red fruit, bright acidity", "Notes": "Colombia's top specialty region; volcanic soil", "color": "green"},
    {"name": "Narino, Colombia", "lat": 1.29, "lon": -77.35, "Country": "Colombia", "Species": "Arabica", "Altitude": "1,500-2,300m", "Flavor": "Citric, sweet, floral", "Notes": "Equatorial highlands; extreme altitude micro-lots", "color": "green"},
    {"name": "Eje Cafetero, Colombia", "lat": 4.81, "lon": -75.69, "Country": "Colombia", "Species": "Arabica", "Altitude": "1,200-1,800m", "Flavor": "Balanced, nutty, caramel", "Notes": "UNESCO Coffee Cultural Landscape; three departments", "color": "green"},
    {"name": "Minas Gerais, Brazil", "lat": -21.13, "lon": -44.26, "Country": "Brazil", "Species": "Arabica", "Altitude": "900-1,350m", "Flavor": "Chocolate, nutty, low acidity", "Notes": "World's largest coffee-producing state", "color": "green"},
    {"name": "Cerrado Mineiro, Brazil", "lat": -19.00, "lon": -47.50, "Country": "Brazil", "Species": "Arabica", "Altitude": "800-1,300m", "Flavor": "Nutty, sweet, full body", "Notes": "First non-European designated origin for coffee", "color": "green"},
    {"name": "Mogiana, Sao Paulo, Brazil", "lat": -21.18, "lon": -48.80, "Country": "Brazil", "Species": "Arabica", "Altitude": "900-1,100m", "Flavor": "Chocolate, caramel, smooth", "Notes": "Historic coffee heartland of Brazil", "color": "green"},
    {"name": "Central Highlands, Vietnam", "lat": 12.68, "lon": 108.05, "Country": "Vietnam", "Species": "Robusta", "Altitude": "500-800m", "Flavor": "Bold, earthy, bitter", "Notes": "World's second-largest producer; Dak Lak province", "color": "red"},
    {"name": "Lam Dong, Vietnam", "lat": 11.94, "lon": 108.44, "Country": "Vietnam", "Species": "Arabica/Robusta", "Altitude": "800-1,500m", "Flavor": "Fruity, mild, tea-like", "Notes": "Da Lat region specialty Arabica growth", "color": "red"},
    {"name": "Toraja, Sulawesi", "lat": -3.07, "lon": 119.82, "Country": "Indonesia", "Species": "Arabica", "Altitude": "1,200-1,800m", "Flavor": "Earthy, herbal, dark chocolate", "Notes": "Tana Toraja highlands; wet-hulled (Giling Basah)", "color": "orange"},
    {"name": "Kintamani, Bali", "lat": -8.29, "lon": 115.37, "Country": "Indonesia", "Species": "Arabica", "Altitude": "900-1,200m", "Flavor": "Citrus, floral, clean", "Notes": "Volcanic soil; subak abian cooperative system", "color": "orange"},
    {"name": "Gayo Highlands, Sumatra", "lat": 4.60, "lon": 96.85, "Country": "Indonesia", "Species": "Arabica", "Altitude": "1,100-1,600m", "Flavor": "Earthy, spicy, full body", "Notes": "Lake Takengon region; Mandheling process", "color": "orange"},
    {"name": "Mount Elgon, Uganda", "lat": 1.13, "lon": 34.55, "Country": "Uganda", "Species": "Arabica/Robusta", "Altitude": "1,500-2,000m", "Flavor": "Wine-like, berry, clean", "Notes": "Rising specialty origin; Bugisu washed coffees", "color": "green"},
    {"name": "Nyeri, Kenya", "lat": -0.42, "lon": 36.95, "Country": "Kenya", "Species": "Arabica (SL28/SL34)", "Altitude": "1,600-2,000m", "Flavor": "Blackcurrant, tomato, sparkling acidity", "Notes": "Kenya's premier origin; auction system", "color": "green"},
    {"name": "Ngorongoro, Tanzania", "lat": -3.24, "lon": 35.48, "Country": "Tanzania", "Species": "Arabica", "Altitude": "1,400-1,800m", "Flavor": "Berry, bright, juicy", "Notes": "Northern highlands; peaberry famous", "color": "green"},
    {"name": "Antigua Guatemala", "lat": 14.56, "lon": -90.73, "Country": "Guatemala", "Species": "Arabica", "Altitude": "1,500-1,700m", "Flavor": "Chocolate, spice, smoky", "Notes": "Three volcanoes; colonial heritage", "color": "green"},
    {"name": "Tarrazu, Costa Rica", "lat": 9.66, "lon": -84.02, "Country": "Costa Rica", "Species": "Arabica", "Altitude": "1,200-1,900m", "Flavor": "Bright, citrus, clean", "Notes": "Strictest altitude classification; SHB grade", "color": "green"},
    {"name": "Kona, Hawaii", "lat": 19.64, "lon": -155.99, "Country": "USA (Hawaii)", "Species": "Arabica", "Altitude": "150-900m", "Flavor": "Smooth, nutty, mild acidity", "Notes": "Volcanic Mauna Loa slopes; premium single-origin", "color": "green"},
    {"name": "Blue Mountain, Jamaica", "lat": 18.17, "lon": -76.58, "Country": "Jamaica", "Species": "Arabica", "Altitude": "900-1,500m", "Flavor": "Balanced, sweet, no bitterness", "Notes": "One of world's most expensive coffees; Japanese market", "color": "green"},
    {"name": "Marcala, Honduras", "lat": 14.16, "lon": -88.06, "Country": "Honduras", "Species": "Arabica", "Altitude": "1,200-1,700m", "Flavor": "Caramel, orange, honey", "Notes": "First denomination of origin in Central America", "color": "green"},
    {"name": "San Marcos, Cajamarca, Peru", "lat": -7.33, "lon": -78.17, "Country": "Peru", "Species": "Arabica", "Altitude": "1,400-1,900m", "Flavor": "Floral, cocoa, sweet", "Notes": "Emerging specialty origin; organic by default", "color": "green"},
    {"name": "Jimma, Ethiopia", "lat": 7.67, "lon": 36.83, "Country": "Ethiopia", "Species": "Arabica", "Altitude": "1,400-1,800m", "Flavor": "Fruity, winey, complex", "Notes": "Major commercial hub; Limmu and Jimma grades", "color": "green"},
    {"name": "Doi Chaang, Thailand", "lat": 20.15, "lon": 99.83, "Country": "Thailand", "Species": "Arabica", "Altitude": "1,200-1,500m", "Flavor": "Chocolatey, smooth, mild", "Notes": "Akha hill tribe social enterprise", "color": "green"},
    {"name": "Luwak Plateau, Java", "lat": -7.95, "lon": 112.63, "Country": "Indonesia", "Species": "Arabica/Robusta", "Altitude": "900-1,400m", "Flavor": "Smooth, earthy, low acidity", "Notes": "Java Arabica estate tradition since Dutch colonial era", "color": "orange"},
]

# ========================================================================
# DATA: 2. FAMOUS CAFE CULTURE
# ========================================================================
FAMOUS_CAFE_CULTURE = [
    {"name": "Cafe Central, Vienna", "lat": 48.21, "lon": 16.37, "Country": "Austria", "Style": "Viennese Coffeehouse", "Founded": 1876, "Specialty": "Melange, Einspanner", "Notes": "Freud, Trotsky, and Loos were regulars; UNESCO Intangible Heritage", "color": "purple"},
    {"name": "Cafe Demel, Vienna", "lat": 48.21, "lon": 16.37, "Country": "Austria", "Style": "Viennese Coffeehouse", "Founded": 1786, "Specialty": "Sachertorte, Fiaker coffee", "Notes": "Imperial purveyor; rival of Hotel Sacher", "color": "purple"},
    {"name": "Cafe Sacher, Vienna", "lat": 48.20, "lon": 16.37, "Country": "Austria", "Style": "Viennese Coffeehouse", "Founded": 1876, "Specialty": "Original Sachertorte", "Notes": "Hotel cafe; won Sachertorte legal battle", "color": "purple"},
    {"name": "Cafe Sperl, Vienna", "lat": 48.20, "lon": 16.35, "Country": "Austria", "Style": "Viennese Coffeehouse", "Founded": 1880, "Specialty": "Sperl Torte, billiards", "Notes": "Artists' and writers' cafe; Art Nouveau interior", "color": "purple"},
    {"name": "Cafe de Flore, Paris", "lat": 48.85, "lon": 2.33, "Country": "France", "Style": "Parisian Bistro", "Founded": 1887, "Specialty": "Cafe creme, chocolat chaud", "Notes": "Sartre and de Beauvoir's headquarters; existentialism hub", "color": "pink"},
    {"name": "Les Deux Magots, Paris", "lat": 48.85, "lon": 2.33, "Country": "France", "Style": "Parisian Bistro", "Founded": 1885, "Specialty": "Grand creme, hot chocolate", "Notes": "Literary prize namesake; Hemingway, Picasso haunt", "color": "pink"},
    {"name": "Cafe Procope, Paris", "lat": 48.85, "lon": 2.34, "Country": "France", "Style": "Parisian Bistro", "Founded": 1686, "Specialty": "Oldest cafe in Paris", "Notes": "Voltaire, Rousseau, Franklin visited; French Revolution hub", "color": "pink"},
    {"name": "Antico Caffe Greco, Rome", "lat": 41.91, "lon": 12.48, "Country": "Italy", "Style": "Italian Espresso Bar", "Founded": 1760, "Specialty": "Espresso, Granita di Caffe", "Notes": "Keats, Goethe, Stendhal were patrons; Via Condotti", "color": "red"},
    {"name": "Caffe Florian, Venice", "lat": 45.43, "lon": 12.34, "Country": "Italy", "Style": "Italian Espresso Bar", "Founded": 1720, "Specialty": "Caffe con panna, hot chocolate", "Notes": "Oldest continuously operating cafe in the world; Piazza San Marco", "color": "red"},
    {"name": "Caffe Gambrinus, Naples", "lat": 40.84, "lon": 14.25, "Country": "Italy", "Style": "Italian Espresso Bar", "Founded": 1860, "Specialty": "Neapolitan espresso, sfogliatella", "Notes": "Oscar Wilde visited; birthplace of caffe sospeso tradition", "color": "red"},
    {"name": "Bar Giubbe Rosse, Florence", "lat": 43.77, "lon": 11.25, "Country": "Italy", "Style": "Italian Espresso Bar", "Founded": 1897, "Specialty": "Espresso, literary debates", "Notes": "Futurist movement headquarters; Piazza della Repubblica", "color": "red"},
    {"name": "Mandabatmaz, Istanbul", "lat": 41.03, "lon": 28.97, "Country": "Turkey", "Style": "Turkish Kahve", "Founded": 1967, "Specialty": "Turkish coffee (ibrik)", "Notes": "Legendary thick foam; tiny Istiklal side-street", "color": "darkred"},
    {"name": "Kurukahveci Mehmet Efendi, Istanbul", "lat": 41.02, "lon": 28.97, "Country": "Turkey", "Style": "Turkish Kahve", "Founded": 1871, "Specialty": "Ground Turkish coffee", "Notes": "First to sell pre-ground coffee; Spice Bazaar icon", "color": "darkred"},
    {"name": "Cafe Tortoni, Buenos Aires", "lat": -34.61, "lon": -58.38, "Country": "Argentina", "Style": "Porteño Cafe", "Founded": 1858, "Specialty": "Cafe con leche, tango shows", "Notes": "National Historic Monument; Borges and Gardel haunt", "color": "orange"},
    {"name": "Confeitaria Colombo, Rio de Janeiro", "lat": -22.90, "lon": -43.18, "Country": "Brazil", "Style": "Belle Epoque Cafe", "Founded": 1894, "Specialty": "Cafezinho, pasteis", "Notes": "Art Nouveau mirrors and stained glass; national landmark", "color": "orange"},
    {"name": "Cafe Hawelka, Vienna", "lat": 48.21, "lon": 16.37, "Country": "Austria", "Style": "Viennese Coffeehouse", "Founded": 1939, "Specialty": "Buchteln (yeast pastry)", "Notes": "Bohemian artists' cafe; Leopold Hawelka legacy", "color": "purple"},
    {"name": "The Elephant House, Edinburgh", "lat": 55.95, "lon": -3.19, "Country": "UK", "Style": "British Coffee House", "Founded": 1995, "Specialty": "Filter coffee, cakes", "Notes": "Where J.K. Rowling wrote early Harry Potter chapters", "color": "blue"},
    {"name": "Bewley's, Dublin", "lat": 53.34, "lon": -6.26, "Country": "Ireland", "Style": "Irish Coffee House", "Founded": 1927, "Specialty": "Bewley's blend, scones", "Notes": "Grafton Street landmark; Harry Clarke stained glass", "color": "blue"},
    {"name": "Cafe A Brasileira, Lisbon", "lat": 38.71, "lon": -9.14, "Country": "Portugal", "Style": "Lisbon Cafe", "Founded": 1905, "Specialty": "Bica (espresso), pasteis", "Notes": "Fernando Pessoa bronze statue outside; Chiado district", "color": "orange"},
    {"name": "Cafe New York, Budapest", "lat": 47.50, "lon": 19.07, "Country": "Hungary", "Style": "Grand Cafe", "Founded": 1894, "Specialty": "Lungo, New York cake", "Notes": "World's most beautiful cafe; Renaissance Revival palace", "color": "purple"},
    {"name": "Gerbeaud Cafe, Budapest", "lat": 47.50, "lon": 19.05, "Country": "Hungary", "Style": "Grand Cafe", "Founded": 1858, "Specialty": "Gerbeaud slice, Dobos torte", "Notes": "Vorosmarty Square icon; Swiss-Hungarian confectionery", "color": "purple"},
    {"name": "Cafe Gijón, Madrid", "lat": 40.42, "lon": -3.69, "Country": "Spain", "Style": "Spanish Tertulias", "Founded": 1888, "Specialty": "Cafe con leche, tertulia debates", "Notes": "Literary gathering place for over a century; Paseo de Recoletos", "color": "orange"},
    {"name": "Gran Caffe Gambrinus, Naples", "lat": 40.84, "lon": 14.25, "Country": "Italy", "Style": "Neapolitan Espresso", "Founded": 1860, "Specialty": "Caffe sospeso (suspended coffee)", "Notes": "Pay-it-forward coffee tradition born here", "color": "red"},
    {"name": "Toma Cafe, Madrid", "lat": 40.43, "lon": -3.70, "Country": "Spain", "Style": "Third Wave Spanish", "Founded": 2012, "Specialty": "Single-origin pour-over", "Notes": "Pioneer of specialty coffee in Madrid", "color": "orange"},
    {"name": "Cafe de la Paix, Paris", "lat": 48.87, "lon": 2.33, "Country": "France", "Style": "Parisian Grand Cafe", "Founded": 1862, "Specialty": "Cafe express, patisserie", "Notes": "Opera Garnier adjacent; Napoleon III era grandeur", "color": "pink"},
    {"name": "Ruszwurm, Budapest", "lat": 47.50, "lon": 19.03, "Country": "Hungary", "Style": "Historic Patisserie", "Founded": 1827, "Specialty": "Ruszwurm cream cake", "Notes": "Oldest confectionery in Budapest; Buda Castle district", "color": "purple"},
    {"name": "Majestic Cafe, Porto", "lat": 41.15, "lon": -8.61, "Country": "Portugal", "Style": "Belle Epoque Cafe", "Founded": 1921, "Specialty": "Galao, francesinha", "Notes": "Art Nouveau gem; Rowling also wrote here", "color": "orange"},
]

# ========================================================================
# DATA: 3. SPECIALTY COFFEE ROASTERS
# ========================================================================
SPECIALTY_ROASTERS = [
    {"name": "Blue Bottle Coffee, Oakland", "lat": 37.80, "lon": -122.27, "Country": "USA", "Founded": 2002, "Style": "Third Wave pioneer", "Signature": "Single-origin pour-over, 48-hour freshness", "Notes": "James Freeman's garage origin; now Nestle-owned", "color": "blue"},
    {"name": "Stumptown Coffee, Portland", "lat": 45.52, "lon": -122.68, "Country": "USA", "Founded": 1999, "Style": "Direct trade pioneer", "Signature": "Hair Bender blend, cold brew", "Notes": "Duane Sorenson; pioneered direct-trade relationships", "color": "blue"},
    {"name": "Tim Wendelboe, Oslo", "lat": 59.92, "lon": 10.77, "Country": "Norway", "Founded": 2007, "Style": "Nordic light roast", "Signature": "Single-estate washed, AeroPress champion", "Notes": "2004 World Barista Champion; tiny Grunerløkka roastery", "color": "blue"},
    {"name": "Intelligentsia, Chicago", "lat": 41.88, "lon": -87.67, "Country": "USA", "Founded": 1995, "Style": "Direct trade leader", "Signature": "Black Cat espresso", "Notes": "Coined 'direct trade'; multiple US cafes", "color": "blue"},
    {"name": "Counter Culture, Durham NC", "lat": 35.99, "lon": -78.90, "Country": "USA", "Founded": 1995, "Style": "Sustainability pioneer", "Signature": "Hologram blend, training centers", "Notes": "First carbon-neutral roaster in USA", "color": "blue"},
    {"name": "Square Mile Coffee, London", "lat": 51.53, "lon": -0.08, "Country": "UK", "Founded": 2008, "Style": "Nordic-British hybrid", "Signature": "Red Brick espresso blend", "Notes": "James Hoffmann (2007 WBC) + Anette Moldvaer", "color": "blue"},
    {"name": "Koppi, Helsingborg", "lat": 56.05, "lon": 12.69, "Country": "Sweden", "Founded": 2007, "Style": "Scandinavian light roast", "Signature": "Filter-focused single origins", "Notes": "Anne Lunell + Charles Nystrom; minimalist ethos", "color": "blue"},
    {"name": "The Barn, Berlin", "lat": 52.53, "lon": 13.41, "Country": "Germany", "Founded": 2010, "Style": "Berlin specialty", "Signature": "Seasonal single-origin filter", "Notes": "Ralf Ruller's strict light-roast philosophy", "color": "blue"},
    {"name": "Onyx Coffee Lab, Rogers AR", "lat": 36.33, "lon": -94.12, "Country": "USA", "Founded": 2012, "Style": "Competition roaster", "Signature": "Monarch espresso, Tropical Weather", "Notes": "Multiple US Roaster Championship wins", "color": "blue"},
    {"name": "Coffee Collective, Copenhagen", "lat": 55.68, "lon": 12.55, "Country": "Denmark", "Founded": 2007, "Style": "Nordic cooperative", "Signature": "Seasonal espresso, Jaegersborggade cafe", "Notes": "Three barista champions founded it; B-Corp certified", "color": "blue"},
    {"name": "Heart Coffee, Portland", "lat": 45.52, "lon": -122.65, "Country": "USA", "Founded": 2009, "Style": "Japanese-Pacific NW fusion", "Signature": "Japanese-style pour-over, light roast", "Notes": "Wille Yli-Luoma; originally from Japan", "color": "blue"},
    {"name": "Proud Mary Coffee, Melbourne", "lat": -37.81, "lon": 144.98, "Country": "Australia", "Founded": 2009, "Style": "Australian specialty", "Signature": "Experimental processing, cascara", "Notes": "Nolan Hirte; expanded to Portland USA", "color": "blue"},
    {"name": "La Cabra, Aarhus", "lat": 56.16, "lon": 10.21, "Country": "Denmark", "Founded": 2012, "Style": "Nordic precision", "Signature": "Washed Ethiopians, Nordic baking", "Notes": "Esben Piper; Michelin-guide recognized bakery-cafe", "color": "blue"},
    {"name": "Fuglen, Tokyo/Oslo", "lat": 35.67, "lon": 139.69, "Country": "Japan/Norway", "Founded": 2012, "Style": "Nordic-Japanese hybrid", "Signature": "Tim Wendelboe beans, cocktails at night", "Notes": "Tomigaya cafe; vintage furniture meets specialty coffee", "color": "blue"},
    {"name": "Workshop Coffee, London", "lat": 51.52, "lon": -0.10, "Country": "UK", "Founded": 2011, "Style": "London specialty", "Signature": "Cult of Done espresso blend", "Notes": "Multiple London locations; training lab", "color": "blue"},
    {"name": "Da Matteo, Gothenburg", "lat": 57.70, "lon": 11.97, "Country": "Sweden", "Founded": 1993, "Style": "Swedish specialty pioneer", "Signature": "Cardamom bun + filter coffee", "Notes": "Matts Johansson; bakery-roaster hybrid", "color": "blue"},
    {"name": "SEY Coffee, Brooklyn", "lat": 40.70, "lon": -73.96, "Country": "USA", "Founded": 2017, "Style": "Transparency pioneer", "Signature": "Price transparency model, light roast", "Notes": "Lance Schnorenberg; full supply-chain cost disclosure", "color": "blue"},
    {"name": "April Coffee, Copenhagen", "lat": 55.69, "lon": 12.56, "Country": "Denmark", "Founded": 2016, "Style": "Nordic innovation", "Signature": "2015 WBC champion roasts", "Notes": "Patrik Rolf (2015 Brewers Cup); omakase coffee tasting", "color": "blue"},
    {"name": "Five Elephant, Berlin", "lat": 52.49, "lon": 13.42, "Country": "Germany", "Founded": 2010, "Style": "Berlin roaster-bakery", "Signature": "Cheesecake + specialty coffee", "Notes": "Kreuzberg neighborhood institution", "color": "blue"},
    {"name": "Gardelli Specialty Coffees, Forli", "lat": 44.22, "lon": 12.04, "Country": "Italy", "Founded": 2007, "Style": "Italian specialty rebel", "Signature": "Light roast Italian-style", "Notes": "Rubens Gardelli; challenging Italy's dark-roast tradition", "color": "blue"},
    {"name": "George Howell Coffee, Boston", "lat": 42.36, "lon": -71.06, "Country": "USA", "Founded": 2004, "Style": "Terroir coffee pioneer", "Signature": "Tarrazu, vintage crop lots", "Notes": "George Howell coined 'terroir' in coffee; Cup of Excellence co-founder", "color": "blue"},
    {"name": "Cafe Grumpy, Brooklyn", "lat": 40.72, "lon": -73.95, "Country": "USA", "Founded": 2005, "Style": "NYC craft roaster", "Signature": "Heartbreaker espresso", "Notes": "Featured in HBO's Girls; multiple Manhattan locations", "color": "blue"},
    {"name": "Verve Coffee, Santa Cruz", "lat": 36.97, "lon": -122.03, "Country": "USA", "Founded": 2007, "Style": "California coastal", "Signature": "Streetlevel espresso, Sermon blend", "Notes": "Ryan O'Donovan + Colby Barr; expanded to Japan", "color": "blue"},
    {"name": "3fe Coffee, Dublin", "lat": 53.34, "lon": -6.24, "Country": "Ireland", "Founded": 2009, "Style": "Irish specialty", "Signature": "Seasonal single-origin espresso", "Notes": "Colin Harmon; 4x Irish Barista Champion", "color": "blue"},
    {"name": "Passenger Coffee, Lancaster PA", "lat": 40.04, "lon": -76.31, "Country": "USA", "Founded": 2014, "Style": "East Coast craft", "Signature": "Thoughtfully sourced single origins", "Notes": "Former baristas from ReAnimator; Amish country roaster", "color": "blue"},
    {"name": "Nomad Coffee, Barcelona", "lat": 41.38, "lon": 2.18, "Country": "Spain", "Founded": 2014, "Style": "Mediterranean specialty", "Signature": "Espresso + vermouth pairing", "Notes": "Jordi Mestre; El Born neighborhood", "color": "blue"},
]

# ========================================================================
# DATA: 4. COFFEE PROCESSING METHODS
# ========================================================================
COFFEE_PROCESSING = [
    {"name": "Yirgacheffe Washed, Ethiopia", "lat": 6.16, "lon": 38.21, "Country": "Ethiopia", "Method": "Washed (Wet Process)", "Description": "Cherry depulped, fermented 24-72hrs, washed clean", "Flavor Impact": "Clean, bright, floral, transparent terroir", "color": "blue"},
    {"name": "Harar Natural, Ethiopia", "lat": 9.31, "lon": 42.12, "Country": "Ethiopia", "Method": "Natural (Dry Process)", "Description": "Whole cherry dried on raised beds 2-4 weeks", "Flavor Impact": "Fruity, boozy, blueberry, full body", "color": "red"},
    {"name": "Costa Rica Honey Process", "lat": 9.93, "lon": -84.08, "Country": "Costa Rica", "Method": "Honey (Pulped Natural)", "Description": "Depulped but mucilage left on during drying", "Flavor Impact": "Sweet, syrupy, balanced fruit + clarity", "color": "orange"},
    {"name": "Sumatra Wet-Hull, Gayo", "lat": 4.60, "lon": 96.85, "Country": "Indonesia", "Method": "Giling Basah (Wet-Hull)", "Description": "Hulled at high moisture, unique Sumatran method", "Flavor Impact": "Earthy, herbal, low acidity, full body", "color": "darkred"},
    {"name": "Anaerobic Fermentation, Colombia", "lat": 2.53, "lon": -75.53, "Country": "Colombia", "Method": "Anaerobic Fermentation", "Description": "Sealed tank fermentation without oxygen 48-120hrs", "Flavor Impact": "Intense fruit, wine-like, complex", "color": "purple"},
    {"name": "Kenya Double Washed", "lat": -0.42, "lon": 36.95, "Country": "Kenya", "Method": "Double Washed (Kenya Process)", "Description": "Two fermentation cycles with soaking between", "Flavor Impact": "Sparkling acidity, blackcurrant, juicy", "color": "blue"},
    {"name": "Brazil Natural Cerrado", "lat": -19.00, "lon": -47.50, "Country": "Brazil", "Method": "Natural (Terreiro Drying)", "Description": "Dried on concrete patios; mechanical drying assist", "Flavor Impact": "Chocolate, nutty, heavy body, low acid", "color": "red"},
    {"name": "Guatemala Washed Highland", "lat": 14.56, "lon": -90.73, "Country": "Guatemala", "Method": "Fully Washed", "Description": "Pulped, fermented, channel-washed, patio dried", "Flavor Impact": "Chocolate, spice, balanced structure", "color": "blue"},
    {"name": "Rwanda Washed A1", "lat": -1.94, "lon": 29.87, "Country": "Rwanda", "Method": "Fully Washed", "Description": "Washing station model; strict cherry selection", "Flavor Impact": "Floral, citrus, tea-like elegance", "color": "blue"},
    {"name": "Panama Geisha Natural", "lat": 8.80, "lon": -82.43, "Country": "Panama", "Method": "Natural Process", "Description": "Boquete estate natural dried Geisha variety", "Flavor Impact": "Jasmine, bergamot, honey, tropical fruit", "color": "red"},
    {"name": "El Salvador Honey Yellow", "lat": 13.79, "lon": -89.19, "Country": "El Salvador", "Method": "Yellow Honey", "Description": "25% mucilage left; fastest honey drying", "Flavor Impact": "Light fruit, clean sweetness, mild body", "color": "orange"},
    {"name": "El Salvador Honey Red", "lat": 13.83, "lon": -89.25, "Country": "El Salvador", "Method": "Red Honey", "Description": "50% mucilage left; slower shade drying", "Flavor Impact": "Stone fruit, plum, syrupy sweetness", "color": "orange"},
    {"name": "El Salvador Honey Black", "lat": 13.77, "lon": -89.30, "Country": "El Salvador", "Method": "Black Honey", "Description": "Nearly all mucilage retained; longest drying", "Flavor Impact": "Rich, molasses, dried fruit, winey", "color": "darkred"},
    {"name": "Java Wet-Hulled Estate", "lat": -7.95, "lon": 112.63, "Country": "Indonesia", "Method": "Wet-Hulled (Giling Basah)", "Description": "Parchment removed at 30-50% moisture", "Flavor Impact": "Earthy, woody, spiced, thick mouthfeel", "color": "darkred"},
    {"name": "Yemen Natural Sun-Dried", "lat": 15.35, "lon": 44.20, "Country": "Yemen", "Method": "Ancient Natural", "Description": "Traditional rooftop sun-drying; minimal processing", "Flavor Impact": "Winey, spicy, dried fruit, complex", "color": "red"},
    {"name": "Colombia Thermal Shock", "lat": 5.07, "lon": -75.52, "Country": "Colombia", "Method": "Thermal Shock Fermentation", "Description": "Hot/cold water cycling during fermentation", "Flavor Impact": "Candy-like, tropical, lactic sweetness", "color": "purple"},
    {"name": "Myanmar Natural Process", "lat": 20.78, "lon": 96.47, "Country": "Myanmar", "Method": "Natural", "Description": "Shan State natural drying on bamboo beds", "Flavor Impact": "Stone fruit, herbal, unique terroir", "color": "red"},
    {"name": "Burundi Fully Washed", "lat": -3.38, "lon": 29.36, "Country": "Burundi", "Method": "Fully Washed", "Description": "Community washing stations; 24hr fermentation", "Flavor Impact": "Juicy, berry, red grape, bright", "color": "blue"},
    {"name": "Kintamani Washed, Bali", "lat": -8.29, "lon": 115.37, "Country": "Indonesia", "Method": "Washed (vs typical Indonesian)", "Description": "Clean washed Bali Arabica; atypical for Indonesia", "Flavor Impact": "Citrus, clean, floral -- unusual for Indo", "color": "blue"},
    {"name": "Bolivia Washed Caranavi", "lat": -15.83, "lon": -67.57, "Country": "Bolivia", "Method": "Fully Washed", "Description": "Yungas valley washed micro-lots", "Flavor Impact": "Peach, jasmine, silky", "color": "blue"},
    {"name": "India Monsooned Malabar", "lat": 12.50, "lon": 74.99, "Country": "India", "Method": "Monsoon Process", "Description": "Exposed to monsoon winds 3-4 months; absorbs moisture", "Flavor Impact": "Low acidity, musty, earthy, spicy, huge body", "color": "darkgreen"},
    {"name": "Lactic Fermentation, Huila Colombia", "lat": 1.75, "lon": -76.08, "Country": "Colombia", "Method": "Lactic Fermentation", "Description": "Lactobacillus culture added; 100+ hr fermentation", "Flavor Impact": "Yogurt-like, tropical, creamy, funky", "color": "purple"},
    {"name": "Carbonic Maceration, Colombia", "lat": 4.53, "lon": -75.68, "Country": "Colombia", "Method": "Carbonic Maceration", "Description": "CO2 injected sealed tank; borrowed from wine", "Flavor Impact": "Strawberry, candy, effervescent", "color": "purple"},
    {"name": "Sulawesi Semi-Washed", "lat": -3.07, "lon": 119.82, "Country": "Indonesia", "Method": "Semi-Washed", "Description": "Partial wet-hull with controlled fermentation", "Flavor Impact": "Complex, herbal, dark chocolate, clean earth", "color": "orange"},
    {"name": "Hawaiian Natural, Kona", "lat": 19.64, "lon": -155.99, "Country": "USA", "Method": "Natural (Experimental)", "Description": "Raised-bed natural drying in Kona; emerging trend", "Flavor Impact": "Tropical fruit, sweet, pineapple", "color": "red"},
    {"name": "DRC Washed Kivu", "lat": -1.68, "lon": 29.23, "Country": "DR Congo", "Method": "Fully Washed", "Description": "Lake Kivu shore washing stations", "Flavor Impact": "Brown sugar, stone fruit, delicate", "color": "blue"},
]

# ========================================================================
# DATA: 5. HISTORIC COFFEE TRADE ROUTES
# ========================================================================
HISTORIC_TRADE_ROUTES = [
    {"name": "Port of Mocha, Yemen", "lat": 13.32, "lon": 43.25, "Country": "Yemen", "Era": "1400s-1700s", "Role": "Origin export port", "Route": "Mocha to Egypt, Ottoman Empire, Europe", "Notes": "Gave name to 'Mocha' coffee; world's first coffee trade hub", "color": "darkred"},
    {"name": "Jeddah, Saudi Arabia", "lat": 21.49, "lon": 39.19, "Country": "Saudi Arabia", "Era": "1400s-1600s", "Role": "Hajj transit hub", "Route": "Yemen to Mecca/Medina pilgrim routes", "Notes": "Pilgrims spread coffee culture across Islamic world", "color": "darkred"},
    {"name": "Cairo Coffeehouses, Egypt", "lat": 30.04, "lon": 31.24, "Country": "Egypt", "Era": "1500s-present", "Role": "Cultural diffusion center", "Route": "Yemen via Red Sea to Cairo", "Notes": "First qahwa houses; coffee debate with Islamic scholars", "color": "darkred"},
    {"name": "Constantinople (Istanbul)", "lat": 41.01, "lon": 28.98, "Country": "Turkey", "Era": "1554-present", "Role": "Ottoman coffee capital", "Route": "Yemen to Ottoman Empire to Europe", "Notes": "Kiva Han (1554) first coffeehouse; ibrik brewing tradition", "color": "darkred"},
    {"name": "Venice, Italy", "lat": 45.44, "lon": 12.34, "Country": "Italy", "Era": "1570s-present", "Role": "European gateway", "Route": "Ottoman trade via Mediterranean", "Notes": "First European city to import coffee; Caffe Florian 1720", "color": "orange"},
    {"name": "Amsterdam, Netherlands", "lat": 52.37, "lon": 4.90, "Country": "Netherlands", "Era": "1616-1800s", "Role": "Colonial trade HQ", "Route": "Dutch East Indies (Java) to Europe", "Notes": "VOC smuggled coffee plants from Yemen; Java monopoly", "color": "orange"},
    {"name": "Batavia (Jakarta), Java", "lat": -6.17, "lon": 106.85, "Country": "Indonesia", "Era": "1696-1900s", "Role": "Dutch colonial plantation center", "Route": "Java to Amsterdam via Cape of Good Hope", "Notes": "First large-scale coffee cultivation outside Arabia", "color": "orange"},
    {"name": "Martinique, Caribbean", "lat": 14.64, "lon": -61.02, "Country": "France (Martinique)", "Era": "1720-1800s", "Role": "French colonial seedling origin", "Route": "Paris botanical garden to Caribbean", "Notes": "Gabriel de Clieu's single seedling gave coffee to Americas", "color": "orange"},
    {"name": "Santos, Brazil", "lat": -23.96, "lon": -46.33, "Country": "Brazil", "Era": "1727-present", "Role": "World's greatest coffee port", "Route": "Minas Gerais/Sao Paulo to world", "Notes": "Largest coffee export port in history; Bolsa do Cafe", "color": "green"},
    {"name": "Rio de Janeiro, Brazil", "lat": -22.91, "lon": -43.17, "Country": "Brazil", "Era": "1760-1900s", "Role": "Early Brazilian export hub", "Route": "Paraiba Valley to European markets", "Notes": "Coffee barons funded Rio's development", "color": "green"},
    {"name": "London Coffee Houses", "lat": 51.51, "lon": -0.12, "Country": "UK", "Era": "1652-present", "Role": "Financial trading hub", "Route": "Ottoman/Dutch imports", "Notes": "Lloyd's of London started in a coffeehouse; Penny Universities", "color": "blue"},
    {"name": "Vienna, Austria", "lat": 48.21, "lon": 16.37, "Country": "Austria", "Era": "1683-present", "Role": "European coffeehouse culture origin", "Route": "Ottoman siege spoils", "Notes": "Coffee bags left after 1683 siege; Kolschitzky legend", "color": "purple"},
    {"name": "Reunion Island (Bourbon)", "lat": -21.11, "lon": 55.54, "Country": "France (Reunion)", "Era": "1715-1800s", "Role": "Bourbon variety origin", "Route": "Yemen to Bourbon Island to Americas", "Notes": "Mocha seedlings mutated into Bourbon variety here", "color": "orange"},
    {"name": "Malabar Coast, India", "lat": 12.50, "lon": 74.99, "Country": "India", "Era": "1670-present", "Role": "Sufi smuggling origin", "Route": "Yemen to Mysore via Baba Budan", "Notes": "Baba Budan smuggled 7 beans from Yemen; Chikmagalur", "color": "orange"},
    {"name": "Havre (Le Havre), France", "lat": 49.49, "lon": 0.11, "Country": "France", "Era": "1700s-1900s", "Role": "French coffee import port", "Route": "Caribbean/West Africa to France", "Notes": "Major European coffee import dock", "color": "blue"},
    {"name": "Hamburg, Germany", "lat": 53.55, "lon": 9.99, "Country": "Germany", "Era": "1677-present", "Role": "German coffee import capital", "Route": "Global beans to central Europe", "Notes": "Largest European coffee port today; Speicherstadt warehouses", "color": "blue"},
    {"name": "New York City, USA", "lat": 40.71, "lon": -74.01, "Country": "USA", "Era": "1696-present", "Role": "American coffee gateway", "Route": "Brazil/Central America to USA", "Notes": "Coffee exchange on Wall Street; replaced tea after Revolution", "color": "blue"},
    {"name": "New Orleans, USA", "lat": 29.95, "lon": -90.07, "Country": "USA", "Era": "1700s-present", "Role": "Chicory coffee origin", "Route": "Caribbean/Central American imports", "Notes": "Cafe Du Monde; French influence; chicory-coffee tradition", "color": "blue"},
    {"name": "Trieste, Italy", "lat": 45.65, "lon": 13.78, "Country": "Italy", "Era": "1700s-present", "Role": "Habsburg coffee port", "Route": "Ottoman/East Mediterranean to Central Europe", "Notes": "Illy headquarters; free port coffee trade history", "color": "orange"},
    {"name": "Aden, Yemen", "lat": 12.79, "lon": 45.02, "Country": "Yemen", "Era": "1400s-1700s", "Role": "Secondary Yemeni port", "Route": "Yemen highlands to Red Sea/Indian Ocean", "Notes": "Early coffee export alongside Mocha", "color": "darkred"},
    {"name": "Dire Dawa, Ethiopia", "lat": 9.60, "lon": 41.85, "Country": "Ethiopia", "Era": "1900s-present", "Role": "Ethiopian railway coffee hub", "Route": "Harar/Sidamo to Djibouti/export", "Notes": "French railway transported coffee to coast", "color": "green"},
    {"name": "Mombasa, Kenya", "lat": -4.04, "lon": 39.67, "Country": "Kenya", "Era": "1900s-present", "Role": "East African export port", "Route": "Kenya/Uganda/Tanzania to world", "Notes": "Coffee auction system; Nairobi Coffee Exchange", "color": "green"},
    {"name": "Colombo, Sri Lanka", "lat": 6.93, "lon": 79.85, "Country": "Sri Lanka", "Era": "1658-1870s", "Role": "Dutch/British colonial trade", "Route": "Ceylon to Europe", "Notes": "Major coffee exporter until leaf rust (1869) forced switch to tea", "color": "orange"},
    {"name": "Singapore Entrepot", "lat": 1.35, "lon": 103.82, "Country": "Singapore", "Era": "1800s-present", "Role": "Asian coffee trading hub", "Route": "Indonesia/Vietnam to global markets", "Notes": "Kopitiam culture; Robusta blending traditions", "color": "orange"},
    {"name": "Antwerp, Belgium", "lat": 51.22, "lon": 4.40, "Country": "Belgium", "Era": "1700s-present", "Role": "European green-bean trade port", "Route": "Congo/colonial Africa to Europe", "Notes": "Still major green coffee trading center", "color": "blue"},
    {"name": "Djibouti Port", "lat": 11.59, "lon": 43.15, "Country": "Djibouti", "Era": "1800s-present", "Role": "Ethiopian export corridor", "Route": "Ethiopian highland coffee to world via rail", "Notes": "Key transit for Ethiopian exports via Addis-Djibouti railway", "color": "green"},
]

# ========================================================================
# DATA: 6. JAPANESE KISSATEN & POUR-OVER
# ========================================================================
JAPANESE_KISSATEN = [
    {"name": "Cafe de l'Ambre, Tokyo", "lat": 35.67, "lon": 139.77, "Country": "Japan", "Founded": 1948, "Style": "Classic Kissaten", "Specialty": "Aged beans (up to 30 years), nel drip", "Notes": "Sekiguchi Ichiro's legendary Ginza kissaten; 70+ years", "color": "purple"},
    {"name": "Chatei Hatou, Tokyo", "lat": 35.66, "lon": 139.71, "Country": "Japan", "Founded": 1989, "Style": "Kissaten/Specialty hybrid", "Specialty": "Flannel (nel) drip, dark roast", "Notes": "Shibuya; owner Kanbe-san roasts on vintage Fuji Royal", "color": "purple"},
    {"name": "Daibo Coffee, Tokyo", "lat": 35.73, "lon": 139.74, "Country": "Japan", "Founded": 1975, "Style": "Classic Kissaten", "Specialty": "Master-roasted nel drip", "Notes": "Oji station; legendary roaster Mr. Daibo", "color": "purple"},
    {"name": "Café Bach, Tokyo", "lat": 35.73, "lon": 139.80, "Country": "Japan", "Founded": 1968, "Style": "Kissaten pioneer", "Specialty": "Paper drip, Bach Blend", "Notes": "Minami-Senju; Tanaka Katsuhiko's coffee education legacy", "color": "purple"},
    {"name": "Bear Pond Espresso, Tokyo", "lat": 35.66, "lon": 139.67, "Country": "Japan", "Founded": 2000, "Style": "Espresso kissaten hybrid", "Specialty": "Angel Stain espresso (limited daily)", "Notes": "Shimokitazawa; Katsuyuki Tanaka's slow espresso ritual", "color": "purple"},
    {"name": "Glitch Coffee, Tokyo", "lat": 35.70, "lon": 139.76, "Country": "Japan", "Founded": 2015, "Style": "Third Wave x Kissaten", "Specialty": "Single-origin pour-over, light roast", "Notes": "Jimbocho; Kiyokazu Suzuki bridges tradition and modern", "color": "blue"},
    {"name": "Koffee Mameya, Tokyo", "lat": 35.67, "lon": 139.71, "Country": "Japan", "Founded": 2018, "Style": "Curated bean shop", "Specialty": "25+ roasters represented, tasting omakase", "Notes": "Omotesando; choose beans like wine; Kakiyasu bldg", "color": "blue"},
    {"name": "Onibus Coffee, Tokyo", "lat": 35.63, "lon": 139.70, "Country": "Japan", "Founded": 2012, "Style": "Tokyo Third Wave", "Specialty": "Light roast pour-over, open-air roastery", "Notes": "Nakameguro; Atsushi Sakao; converted wooden house", "color": "blue"},
    {"name": "Sarutahiko Coffee, Tokyo", "lat": 35.66, "lon": 139.71, "Country": "Japan", "Founded": 2011, "Style": "Tokyo specialty chain", "Specialty": "Hand drip, espresso, chai latte", "Notes": "Omotesando flagship; barista training academy", "color": "blue"},
    {"name": "Horiguchi Coffee, Tokyo", "lat": 35.66, "lon": 139.67, "Country": "Japan", "Founded": 1990, "Style": "Specialty roaster", "Specialty": "Direct trade single origins", "Notes": "Sengawa origin; Horiguchi-san's sourcing philosophy", "color": "blue"},
    {"name": "Siphon Coffee, Osaka", "lat": 34.69, "lon": 135.50, "Country": "Japan", "Founded": 1952, "Style": "Siphon specialist kissaten", "Specialty": "Halogen siphon brewing", "Notes": "Namba; Osaka's siphon coffee tradition", "color": "purple"},
    {"name": "Rokumei Coffee, Nara", "lat": 34.68, "lon": 135.83, "Country": "Japan", "Founded": 1974, "Style": "Kissaten-to-specialty", "Specialty": "Japan Roaster Championship winner beans", "Notes": "Nara roastery; Yoshiaki Inoue won roasting competitions", "color": "blue"},
    {"name": "Maruyama Coffee, Karuizawa", "lat": 36.35, "lon": 138.64, "Country": "Japan", "Founded": 1991, "Style": "Alpine specialty roaster", "Specialty": "Cup of Excellence auction buyer", "Notes": "Kentaro Maruyama; Nagano mountain roastery", "color": "blue"},
    {"name": "% Arabica, Kyoto", "lat": 35.00, "lon": 135.77, "Country": "Japan", "Founded": 2014, "Style": "Minimalist global brand", "Specialty": "Slayer espresso, latte art", "Notes": "Kenneth Shoji; Higashiyama original; expanded globally", "color": "blue"},
    {"name": "Weekenders Coffee, Kyoto", "lat": 35.01, "lon": 135.76, "Country": "Japan", "Founded": 2005, "Style": "Kyoto specialty", "Specialty": "Nordic-style light roast in Kyoto", "Notes": "Tominokoji-dori; roastery in machiya townhouse", "color": "blue"},
    {"name": "Vermillion Cafe, Kyoto", "lat": 34.97, "lon": 135.77, "Country": "Japan", "Founded": 2015, "Style": "Shrine-side cafe", "Specialty": "Single origin beside Fushimi Inari", "Notes": "At foot of 10,000 torii gates; seasonal drinks", "color": "blue"},
    {"name": "Trunk Coffee, Nagoya", "lat": 35.17, "lon": 136.93, "Country": "Japan", "Founded": 2014, "Style": "Nagoya third wave", "Specialty": "Nordic light roast, V60", "Notes": "Suzuki Yasuo; trained in Copenhagen; Scandi-meets-Japan", "color": "blue"},
    {"name": "Mel Coffee Roasters, Takayama", "lat": 36.14, "lon": 137.25, "Country": "Japan", "Founded": 2012, "Style": "Rural specialty", "Specialty": "Hand-roasted mountainside coffee", "Notes": "Hida region; traditional architecture + modern coffee", "color": "blue"},
    {"name": "Passage Coffee, Tokyo", "lat": 35.68, "lon": 139.77, "Country": "Japan", "Founded": 2016, "Style": "Tokyo micro-roaster", "Specialty": "Aeropress, V60, Kalita Wave", "Notes": "Nihonbashi; minimalist space near Tokyo Station", "color": "blue"},
    {"name": "Light Up Coffee, Tokyo", "lat": 35.72, "lon": 139.58, "Country": "Japan", "Founded": 2014, "Style": "West Tokyo specialty", "Specialty": "Fruit-forward light roasts", "Notes": "Kichijoji; Kawano-san; name refers to highlighting origin", "color": "blue"},
    {"name": "Kyoto Okaffe, Kyoto", "lat": 35.00, "lon": 135.76, "Country": "Japan", "Founded": 2016, "Style": "Kyoto modern kissaten", "Specialty": "Okada-san's hand drip", "Notes": "Gion district; personal service style", "color": "purple"},
    {"name": "Hibi Coffee, Fukuoka", "lat": 33.59, "lon": 130.41, "Country": "Japan", "Founded": 2016, "Style": "Fukuoka specialty", "Specialty": "Competition-grade pour-over", "Notes": "Southern Japan specialty movement", "color": "blue"},
    {"name": "Miki Cafe, Sapporo", "lat": 43.06, "lon": 141.35, "Country": "Japan", "Founded": 1970, "Style": "Hokkaido kissaten", "Specialty": "Siphon coffee, jazz music", "Notes": "Tanukikoji arcade; classic Hokkaido jazz kissaten", "color": "purple"},
    {"name": "Takamura Wine & Coffee, Osaka", "lat": 34.68, "lon": 135.49, "Country": "Japan", "Founded": 2015, "Style": "Wine-shop coffee bar", "Specialty": "Coffee curated like wine selection", "Notes": "Nishi-ku; terroir approach to coffee buying", "color": "blue"},
    {"name": "Philocoffea, Chiba", "lat": 35.60, "lon": 140.12, "Country": "Japan", "Founded": 2016, "Style": "Competition roaster", "Specialty": "2016 World Brewers Cup winner roasts", "Notes": "Tetsu Kasuya's roastery; 4:6 V60 method inventor", "color": "blue"},
    {"name": "Obscura Coffee, Tokyo", "lat": 35.64, "lon": 139.68, "Country": "Japan", "Founded": 2009, "Style": "Sangenjaya specialty", "Specialty": "Espresso + hand drip dual menu", "Notes": "Setagaya; neighborhood roaster with global sourcing", "color": "blue"},
]

# ========================================================================
# DATA: 7. ESPRESSO MACHINE HERITAGE
# ========================================================================
ESPRESSO_MACHINE_HERITAGE = [
    {"name": "La Marzocco, Scarperia, Florence", "lat": 43.99, "lon": 11.35, "Country": "Italy", "Founded": 1927, "Machine": "Linea, GB5, Strada", "Innovation": "First dual-boiler espresso machine (GS series)", "Notes": "Bambi family; handmade in Tuscany; global specialty standard", "color": "red"},
    {"name": "Gaggia Factory, Milan", "lat": 45.47, "lon": 9.19, "Country": "Italy", "Founded": 1947, "Machine": "Classic, Baby, Achille", "Innovation": "Invented lever-piston crema espresso (1948)", "Notes": "Achille Gaggia; first to produce crema; revolutionized espresso", "color": "red"},
    {"name": "Faema, Milan", "lat": 45.49, "lon": 9.23, "Country": "Italy", "Founded": 1945, "Machine": "E61 (1961), Faemina", "Innovation": "E61 thermosiphon group head -- most copied design ever", "Notes": "Carlo Ernesto Valente; E61 changed espresso engineering forever", "color": "red"},
    {"name": "Rancilio, Parabiago, Milan", "lat": 45.56, "lon": 8.95, "Country": "Italy", "Founded": 1927, "Machine": "Silvia, Classe series", "Innovation": "Home espresso pioneer with Silvia (1997)", "Notes": "Roberto Rancilio; Silvia democratized home espresso", "color": "red"},
    {"name": "Nuova Simonelli, Belforte del Chienti", "lat": 43.16, "lon": 13.24, "Country": "Italy", "Founded": 1936, "Machine": "Aurelia, Victoria Arduino", "Innovation": "T3 temperature technology; WBC official machine", "Notes": "Orlando Simonelli; official World Barista Championship sponsor", "color": "red"},
    {"name": "Victoria Arduino, Belforte del Chienti", "lat": 43.16, "lon": 13.24, "Country": "Italy", "Founded": 1905, "Machine": "Black Eagle, Eagle One", "Innovation": "Gravimetric dosing (Black Eagle), thermal stability", "Notes": "Now Simonelli Group; premium line for specialty coffee", "color": "red"},
    {"name": "Cimbali, Milan", "lat": 45.52, "lon": 9.22, "Country": "Italy", "Founded": 1912, "Machine": "M100, S30, M39", "Innovation": "Turbosteam milk technology, GTi grinder integration", "Notes": "Giuseppe Cimbali; one of Italy's largest manufacturers", "color": "red"},
    {"name": "Sanremo, Treviso", "lat": 45.67, "lon": 12.24, "Country": "Italy", "Founded": 2002, "Machine": "Opera, Cafe Racer", "Innovation": "Cafe Racer customizable design, multi-boiler", "Notes": "Newer Italian brand; Veneto artisan manufacturing", "color": "red"},
    {"name": "Dalla Corte, Milan", "lat": 45.46, "lon": 9.17, "Country": "Italy", "Founded": 2001, "Machine": "Mina, Zero, EVO2", "Innovation": "Individual digital PID per group", "Notes": "Paulo Dalla Corte; precision engineering focus", "color": "red"},
    {"name": "Elektra, Treviso", "lat": 45.67, "lon": 12.25, "Country": "Italy", "Founded": 1947, "Machine": "Micro Casa, Belle Epoque", "Innovation": "Art-Deco copper design aesthetic", "Notes": "Family-run Veneto manufacturer; iconic hand-lever machines", "color": "red"},
    {"name": "Bezzera, Milan", "lat": 45.48, "lon": 9.19, "Country": "Italy", "Founded": 1901, "Machine": "BZ10, Strega, Matrix", "Innovation": "Luigi Bezzera patented first espresso machine (1901)", "Notes": "Literally invented espresso; patent sold to Pavoni in 1903", "color": "red"},
    {"name": "La Pavoni, Milan", "lat": 45.47, "lon": 9.20, "Country": "Italy", "Founded": 1905, "Machine": "Europiccola, Professional", "Innovation": "First commercial espresso machine manufacturer", "Notes": "Desiderio Pavoni bought Bezzera's patent; mass-produced espresso", "color": "red"},
    {"name": "Slayer Espresso, Seattle", "lat": 47.61, "lon": -122.33, "Country": "USA", "Founded": 2007, "Machine": "Slayer V3, Steam LP", "Innovation": "Needle valve for pre-infusion pressure profiling", "Notes": "Jason Prefontaine; hand-built in Seattle; pressure profiling pioneer", "color": "blue"},
    {"name": "Synesso, Seattle", "lat": 47.62, "lon": -122.35, "Country": "USA", "Founded": 2004, "Machine": "Hydra, MVP, S200", "Innovation": "Multi-group independent PID temperature control", "Notes": "Mark Barnett; ex-La Marzocco; thermal stability obsession", "color": "blue"},
    {"name": "Kees van der Westen, Hilvarenbeek", "lat": 51.49, "lon": 5.17, "Country": "Netherlands", "Founded": 1995, "Machine": "Spirit, Mirage, Speedster", "Innovation": "Design-art meets espresso; stripped-back engineering", "Notes": "Dutch craftsman; each machine hand-assembled; limited production", "color": "orange"},
    {"name": "Decent Espresso, Vancouver", "lat": 49.28, "lon": -123.12, "Country": "Canada", "Founded": 2015, "Machine": "Decent DE1", "Innovation": "Tablet-controlled flow/pressure profiling; open-source approach", "Notes": "John Buckman; most advanced home espresso; data-driven extraction", "color": "blue"},
    {"name": "Rocket Espresso, Milan", "lat": 45.48, "lon": 9.18, "Country": "Italy", "Founded": 2007, "Machine": "Appartamento, Giotto, R58", "Innovation": "Premium home dual-boiler machines", "Notes": "Daniele Berenbruch + Andrew Meo; NZ-Italian collaboration", "color": "red"},
    {"name": "Ascaso, Barcelona", "lat": 41.40, "lon": 2.17, "Country": "Spain", "Founded": 1962, "Machine": "Dream, Steel Duo", "Innovation": "Colorful retro home espresso design", "Notes": "Spanish manufacturer; thermoblock technology", "color": "orange"},
    {"name": "Breville (Sage), Sydney", "lat": -33.87, "lon": 151.21, "Country": "Australia", "Founded": 1932, "Machine": "Barista Express, Oracle, Bambino", "Innovation": "Integrated grinder home machines; auto-dosing", "Notes": "Most popular home espresso brand globally", "color": "green"},
    {"name": "Lelit, Brescia", "lat": 45.54, "lon": 10.22, "Country": "Italy", "Founded": 1986, "Machine": "Bianca, Mara X, Elizabeth", "Innovation": "Bianca paddle flow control; LCC display", "Notes": "Brescia manufacturing; acquired by De'Longhi group", "color": "red"},
    {"name": "ECM Manufacture, Heidelberg", "lat": 49.40, "lon": 8.69, "Country": "Germany", "Founded": 1999, "Machine": "Synchronika, Mechanika, Classika", "Innovation": "German-engineered Italian-style machines", "Notes": "Espresso Coffee Machines GmbH; premium home segment", "color": "orange"},
    {"name": "Profitec, Maintal", "lat": 50.15, "lon": 8.83, "Country": "Germany", "Founded": 2008, "Machine": "Pro 800, Pro 700, Pro 300", "Innovation": "Lever + pump dual-system machines", "Notes": "German engineering; rapid market ascent in home segment", "color": "orange"},
    {"name": "Marzocco Home, Florence", "lat": 43.77, "lon": 11.25, "Country": "Italy", "Founded": 2015, "Machine": "Linea Mini, GS3", "Innovation": "Professional-grade home machines (GS3 pressure profiling)", "Notes": "La Marzocco's home division; Linea Mini became design icon", "color": "red"},
    {"name": "UNIC, Nice", "lat": 43.71, "lon": 7.26, "Country": "France", "Founded": 1919, "Machine": "Stella di Caffe, Tango", "Innovation": "French espresso engineering; modular design", "Notes": "One of few non-Italian commercial manufacturers; Groupe SEB", "color": "orange"},
    {"name": "Wega, Treviso", "lat": 45.67, "lon": 12.25, "Country": "Italy", "Founded": 1985, "Machine": "Pegasus, Polaris, IO", "Innovation": "Robust commercial workhorses", "Notes": "Veneto manufacturer; wide commercial range", "color": "red"},
    {"name": "Reneka, Strasbourg", "lat": 48.58, "lon": 7.75, "Country": "France", "Founded": 1948, "Machine": "Viva, R65", "Innovation": "Heat-exchange French espresso machines", "Notes": "Alsatian manufacturer; 70+ year heritage", "color": "orange"},
]

# ========================================================================
# DATA: 8. COFFEE PLANTATIONS OPEN TO VISITORS
# ========================================================================
VISITOR_PLANTATIONS = [
    {"name": "Greenwell Farms, Kona Hawaii", "lat": 19.52, "lon": -155.93, "Country": "USA", "Variety": "Kona Typica", "Tour": "Free farm tours daily", "Altitude": "450m", "Notes": "Third-generation family farm; free tasting", "color": "green"},
    {"name": "Mountain Thunder, Kona Hawaii", "lat": 19.56, "lon": -155.95, "Country": "USA", "Variety": "Kona Arabica", "Tour": "Farm + roasting facility tours", "Altitude": "900m", "Notes": "Highest Kona farm; cloud-forest microclimate", "color": "green"},
    {"name": "Blue Mountain Coffee Estate, Jamaica", "lat": 18.17, "lon": -76.58, "Country": "Jamaica", "Variety": "Blue Mountain Typica", "Tour": "Guided plantation walks", "Altitude": "1,200m", "Notes": "UNESCO consideration; Japanese market specialty", "color": "green"},
    {"name": "Finca El Injerto, Huehuetenango Guatemala", "lat": 15.32, "lon": -91.47, "Country": "Guatemala", "Variety": "Bourbon, Pacamara", "Tour": "By appointment", "Altitude": "1,900m", "Notes": "Cup of Excellence record-holder; Aguirre family", "color": "green"},
    {"name": "Hacienda La Esmeralda, Boquete Panama", "lat": 8.80, "lon": -82.43, "Country": "Panama", "Variety": "Geisha", "Tour": "By appointment, auction lots", "Altitude": "1,600m", "Notes": "World's most expensive coffee; Geisha variety rediscovered here", "color": "green"},
    {"name": "Doka Estate, Alajuela Costa Rica", "lat": 10.10, "lon": -84.22, "Country": "Costa Rica", "Variety": "Caturra, Catuai", "Tour": "Daily guided mill + roasting tour", "Altitude": "1,350m", "Notes": "Three generations; century-old wet mill; Poas volcano view", "color": "green"},
    {"name": "Hacienda Venecia, Manizales Colombia", "lat": 5.07, "lon": -75.52, "Country": "Colombia", "Variety": "Colombia, Castillo", "Tour": "Full immersion farm stay", "Altitude": "1,500m", "Notes": "Award-winning eco-tourism; pick-your-own experience", "color": "green"},
    {"name": "Kintamani Plantation, Bali", "lat": -8.29, "lon": 115.37, "Country": "Indonesia", "Variety": "Arabica, Luwak", "Tour": "Subak abian cooperative visits", "Altitude": "1,100m", "Notes": "Volcanic terroir; traditional irrigation system", "color": "orange"},
    {"name": "Finca de Cafe, Antigua Guatemala", "lat": 14.56, "lon": -90.73, "Country": "Guatemala", "Variety": "Bourbon, Typica", "Tour": "Walking tours and cupping", "Altitude": "1,530m", "Notes": "Three volcanos setting; UNESCO city nearby", "color": "green"},
    {"name": "Sidama Coffee Farmers, Ethiopia", "lat": 6.71, "lon": 38.48, "Country": "Ethiopia", "Variety": "Heirloom Arabica", "Tour": "Community cooperative visits", "Altitude": "1,800m", "Notes": "Birthplace of coffee; wild forest genetics", "color": "green"},
    {"name": "Fazenda Santa Ines, Minas Gerais Brazil", "lat": -22.00, "lon": -44.20, "Country": "Brazil", "Variety": "Yellow Bourbon", "Tour": "Agro-tourism estate", "Altitude": "1,100m", "Notes": "Cup of Excellence winner; heritage fazenda", "color": "green"},
    {"name": "Tata Coffee, Coorg India", "lat": 12.42, "lon": 75.74, "Country": "India", "Variety": "Arabica, Robusta", "Tour": "Plantation bungalow stays", "Altitude": "1,000m", "Notes": "Western Ghats; shade-grown under silver oak", "color": "green"},
    {"name": "Doi Chaang Village, Thailand", "lat": 20.15, "lon": 99.83, "Country": "Thailand", "Variety": "Arabica (Catimor)", "Tour": "Hill tribe village visits", "Altitude": "1,300m", "Notes": "Akha tribe social enterprise; from opium to coffee", "color": "green"},
    {"name": "Finca Lerida, Boquete Panama", "lat": 8.79, "lon": -82.42, "Country": "Panama", "Variety": "Catuai, Geisha", "Tour": "Eco-lodge + birdwatching + coffee", "Altitude": "1,600m", "Notes": "Cloud forest estate; quetzal habitat", "color": "green"},
    {"name": "Cafe Ruiz, Boquete Panama", "lat": 8.78, "lon": -82.44, "Country": "Panama", "Variety": "Caturra, Typica", "Tour": "Seed-to-cup guided tour", "Altitude": "1,400m", "Notes": "Four-generation family; complete process demo", "color": "green"},
    {"name": "Ngorongoro Coffee Estate, Tanzania", "lat": -3.24, "lon": 35.48, "Country": "Tanzania", "Variety": "Bourbon, Kent", "Tour": "Crater rim plantation tour", "Altitude": "1,700m", "Notes": "Safari + coffee experience; Ngorongoro crater edge", "color": "green"},
    {"name": "Son Pacamara, El Salvador", "lat": 13.80, "lon": -89.25, "Country": "El Salvador", "Variety": "Pacamara", "Tour": "Boutique hotel + cupping lab", "Altitude": "1,400m", "Notes": "Aida Batlle's family finca; multiple CoE wins", "color": "green"},
    {"name": "Finca Nueva Armenia, Guatemala", "lat": 14.31, "lon": -91.51, "Country": "Guatemala", "Variety": "Geisha, SL28", "Tour": "Atitlan lakeside visits", "Altitude": "1,600m", "Notes": "Lake Atitlan terroir; volcanic mineral soil", "color": "green"},
    {"name": "Sumatra Ketiara Cooperative", "lat": 4.55, "lon": 96.90, "Country": "Indonesia", "Variety": "Gayo Arabica", "Tour": "Women-led cooperative tours", "Altitude": "1,300m", "Notes": "Fairtrade women's cooperative; Takengon region", "color": "orange"},
    {"name": "Nyeri Hill Estate, Kenya", "lat": -0.42, "lon": 36.95, "Country": "Kenya", "Variety": "SL28, SL34, Ruiru 11", "Tour": "Estate visits by arrangement", "Altitude": "1,800m", "Notes": "Mt. Kenya slopes; famous blackcurrant flavor profile", "color": "green"},
    {"name": "Selva Negra, Matagalpa Nicaragua", "lat": 12.88, "lon": -85.92, "Country": "Nicaragua", "Variety": "Bourbon, Caturra", "Tour": "Eco-lodge + organic farm tour", "Altitude": "1,200m", "Notes": "German-Nicaraguan heritage; rainforest reserve", "color": "green"},
    {"name": "Toraja Highland Farm, Sulawesi", "lat": -3.07, "lon": 119.82, "Country": "Indonesia", "Variety": "S-795, Typica", "Tour": "Cultural + coffee trekking", "Altitude": "1,500m", "Notes": "Tana Toraja funeral culture + ancient coffee tradition", "color": "orange"},
    {"name": "Cuzco Coffee Route, Peru", "lat": -13.53, "lon": -71.97, "Country": "Peru", "Variety": "Typica, Bourbon", "Tour": "Quillabamba valley agritourism", "Altitude": "1,300m", "Notes": "Inca trail to coffee trail; Machu Picchu region", "color": "green"},
    {"name": "Hacienda Carmona, El Salvador", "lat": 13.68, "lon": -89.28, "Country": "El Salvador", "Variety": "Bourbon, Pacas", "Tour": "Heritage coffee museum and tour", "Altitude": "1,100m", "Notes": "Museo del Cafe Carmona; El Salvador coffee history", "color": "green"},
    {"name": "Ijen Plateau, East Java", "lat": -8.06, "lon": 114.24, "Country": "Indonesia", "Variety": "Java Arabica", "Tour": "Blue fire crater + coffee tour", "Altitude": "1,500m", "Notes": "Volcanic crater sunrise then plantation visit", "color": "orange"},
    {"name": "Makaibari Tea & Coffee, Darjeeling India", "lat": 27.05, "lon": 88.28, "Country": "India", "Variety": "Arabica shade-grown", "Tour": "Plantation homestay", "Altitude": "1,500m", "Notes": "Biodynamic; primarily tea but growing Arabica", "color": "green"},
]

# ========================================================================
# DATA: 9. WORLD BARISTA CHAMPIONSHIP VENUES
# ========================================================================
BARISTA_CHAMPIONSHIP = [
    {"name": "Monte Carlo, Monaco (WBC 2001)", "lat": 43.74, "lon": 7.42, "Country": "Monaco", "Year": 2001, "Winner": "Robert Thoresen (Norway)", "Event": "1st WBC", "Notes": "Inaugural World Barista Championship", "color": "pink"},
    {"name": "Oslo, Norway (WBC 2002)", "lat": 59.91, "lon": 10.75, "Country": "Norway", "Year": 2002, "Winner": "Fritz Storm (Denmark)", "Event": "WBC 2002", "Notes": "Nordic coffee scene emerging", "color": "pink"},
    {"name": "Boston, USA (WBC 2003)", "lat": 42.36, "lon": -71.06, "Country": "USA", "Year": 2003, "Winner": "Paul Bassett (Australia)", "Event": "WBC 2003", "Notes": "First non-European winner", "color": "pink"},
    {"name": "Trieste, Italy (WBC 2004)", "lat": 45.65, "lon": 13.78, "Country": "Italy", "Year": 2004, "Winner": "Tim Wendelboe (Norway)", "Event": "WBC 2004", "Notes": "Wendelboe went on to open legendary Oslo roastery", "color": "pink"},
    {"name": "Seattle, USA (WBC 2005)", "lat": 47.61, "lon": -122.33, "Country": "USA", "Year": 2005, "Winner": "Troels Overdal Poulsen (Denmark)", "Event": "WBC 2005", "Notes": "Held in coffee capital of America", "color": "pink"},
    {"name": "Bern, Switzerland (WBC 2006)", "lat": 46.95, "lon": 7.45, "Country": "Switzerland", "Year": 2006, "Winner": "Klaus Thomsen (Denmark)", "Event": "WBC 2006", "Notes": "Third Danish winner", "color": "pink"},
    {"name": "Tokyo, Japan (WBC 2007)", "lat": 35.68, "lon": 139.69, "Country": "Japan", "Year": 2007, "Winner": "James Hoffmann (UK)", "Event": "WBC 2007", "Notes": "Hoffmann became global coffee influencer; Square Mile founder", "color": "pink"},
    {"name": "Copenhagen, Denmark (WBC 2008)", "lat": 55.68, "lon": 12.57, "Country": "Denmark", "Year": 2008, "Winner": "Stephen Morrissey (Ireland)", "Event": "WBC 2008", "Notes": "Ireland's first WBC champion", "color": "pink"},
    {"name": "Atlanta, USA (WBC 2009)", "lat": 33.75, "lon": -84.39, "Country": "USA", "Year": 2009, "Winner": "Gwilym Davies (UK)", "Event": "WBC 2009", "Notes": "Davies became street-cart espresso legend", "color": "pink"},
    {"name": "London, UK (WBC 2010)", "lat": 51.51, "lon": -0.08, "Country": "UK", "Year": 2010, "Winner": "Michael Phillips (USA)", "Event": "WBC 2010", "Notes": "Phillips from Intelligentsia; first US winner", "color": "pink"},
    {"name": "Bogota, Colombia (WBC 2011)", "lat": 4.71, "lon": -74.07, "Country": "Colombia", "Year": 2011, "Winner": "Alejandro Mendez (El Salvador)", "Event": "WBC 2011", "Notes": "First producing-country host; Central American winner", "color": "pink"},
    {"name": "Vienna, Austria (WBC 2012)", "lat": 48.21, "lon": 16.37, "Country": "Austria", "Year": 2012, "Winner": "Raul Rodas (Guatemala)", "Event": "WBC 2012", "Notes": "Origin-country winner in coffeehouse capital", "color": "pink"},
    {"name": "Melbourne, Australia (WBC 2013)", "lat": -37.81, "lon": 144.96, "Country": "Australia", "Year": 2013, "Winner": "Pete Licata (USA)", "Event": "WBC 2013", "Notes": "Australia's cafe capital hosted", "color": "pink"},
    {"name": "Rimini, Italy (WBC 2014)", "lat": 44.06, "lon": 12.57, "Country": "Italy", "Year": 2014, "Winner": "Hidenori Izaki (Japan)", "Event": "WBC 2014", "Notes": "Japan's first WBC champion", "color": "pink"},
    {"name": "Seattle, USA (WBC 2015)", "lat": 47.61, "lon": -122.33, "Country": "USA", "Year": 2015, "Winner": "Sasa Sestic (Australia)", "Event": "WBC 2015", "Notes": "Sestic famous for OCD distribution tool", "color": "pink"},
    {"name": "Dublin, Ireland (WBC 2016)", "lat": 53.35, "lon": -6.26, "Country": "Ireland", "Year": 2016, "Winner": "Berg Wu (Taiwan)", "Event": "WBC 2016", "Notes": "First Asian winner from Taiwan", "color": "pink"},
    {"name": "Seoul, South Korea (WBC 2017)", "lat": 37.57, "lon": 126.98, "Country": "South Korea", "Year": 2017, "Winner": "Dale Harris (UK)", "Event": "WBC 2017", "Notes": "Korean specialty scene showcase", "color": "pink"},
    {"name": "Amsterdam, Netherlands (WBC 2018)", "lat": 52.37, "lon": 4.90, "Country": "Netherlands", "Year": 2018, "Winner": "Agnieszka Rojewska (Poland)", "Event": "WBC 2018", "Notes": "First female WBC champion", "color": "pink"},
    {"name": "Boston, USA (WBC 2019)", "lat": 42.36, "lon": -71.06, "Country": "USA", "Year": 2019, "Winner": "Jooyeon Jeon (South Korea)", "Event": "WBC 2019", "Notes": "Korean winner used experimental processing", "color": "pink"},
    {"name": "Milan, Italy (WBC 2021)", "lat": 45.47, "lon": 9.19, "Country": "Italy", "Year": 2021, "Winner": "Diego Campos (Colombia)", "Event": "WBC 2021", "Notes": "Post-pandemic return; Colombian champion", "color": "pink"},
    {"name": "Melbourne, Australia (WBC 2022)", "lat": -37.81, "lon": 144.96, "Country": "Australia", "Year": 2022, "Winner": "Anthony Douglas (Australia)", "Event": "WBC 2022", "Notes": "Home-crowd Australian victory", "color": "pink"},
    {"name": "Athens, Greece (WBC 2023)", "lat": 37.98, "lon": 23.73, "Country": "Greece", "Year": 2023, "Winner": "Boram Um (South Korea)", "Event": "WBC 2023", "Notes": "Third Korean winner; Greek specialty scene debut", "color": "pink"},
    {"name": "SCA Training Campus, Portland", "lat": 45.52, "lon": -122.68, "Country": "USA", "Year": "Ongoing", "Winner": "N/A", "Event": "SCA Education Hub", "Notes": "Specialty Coffee Association training center", "color": "lightblue"},
    {"name": "London School of Coffee, London", "lat": 51.54, "lon": -0.10, "Country": "UK", "Year": "Ongoing", "Winner": "N/A", "Event": "Training Academy", "Notes": "SCA-certified; barista and roasting courses", "color": "lightblue"},
    {"name": "Accademia del Caffe, Florence", "lat": 43.77, "lon": 11.25, "Country": "Italy", "Year": "Ongoing", "Winner": "N/A", "Event": "La Marzocco Academy", "Notes": "Espresso training at La Marzocco HQ", "color": "lightblue"},
    {"name": "Copenhagen Coffee Lab, Copenhagen", "lat": 55.68, "lon": 12.57, "Country": "Denmark", "Year": "Ongoing", "Winner": "N/A", "Event": "Nordic Training Center", "Notes": "Brewing research and barista certification", "color": "lightblue"},
]

# ========================================================================
# DATA: 10. COFFEE MUSEUMS & EXPERIENCES
# ========================================================================
COFFEE_MUSEUMS = [
    {"name": "Coffee Museum Santos (Museu do Cafe), Brazil", "lat": -23.93, "lon": -46.33, "Country": "Brazil", "Type": "Museum", "Highlight": "Housed in historic Bolsa do Cafe palace; coffee exchange trading floor", "Year Opened": 1998, "Notes": "Art Deco coffee exchange building; Santos port history", "color": "green"},
    {"name": "Starbucks Reserve Roastery, Seattle", "lat": 47.61, "lon": -122.33, "Country": "USA", "Type": "Immersive Experience", "Highlight": "Flagship 15,000 sq ft roastery; Siphon bar, barrel-aged coffee", "Year Opened": 2014, "Notes": "Capitol Hill; premium Reserve brand birthplace", "color": "green"},
    {"name": "Starbucks Reserve Roastery, Shanghai", "lat": 31.23, "lon": 121.47, "Country": "China", "Type": "Immersive Experience", "Highlight": "World's largest Starbucks; 30,000 sq ft; AR experience", "Year Opened": 2017, "Notes": "Nanjing Road; augmented reality coffee journey", "color": "green"},
    {"name": "Starbucks Reserve Roastery, Milan", "lat": 45.47, "lon": 9.19, "Country": "Italy", "Type": "Immersive Experience", "Highlight": "Former post office; Princi bakery; Arriviamo cocktail bar", "Year Opened": 2018, "Notes": "Cordusio; Starbucks enters Italian espresso homeland", "color": "green"},
    {"name": "Starbucks Reserve Roastery, Tokyo", "lat": 35.66, "lon": 139.69, "Country": "Japan", "Type": "Immersive Experience", "Highlight": "Kengo Kuma designed; Nakameguro cherry blossom location", "Year Opened": 2019, "Notes": "Four floors; wood and copper; terrace overlooking sakura", "color": "green"},
    {"name": "Starbucks Reserve Roastery, Chicago", "lat": 41.89, "lon": -87.63, "Country": "USA", "Type": "Immersive Experience", "Highlight": "Magnificent Mile; five floors; cocktail experiences", "Year Opened": 2019, "Notes": "Largest in USA; Princi + Arriviamo + Teavana", "color": "green"},
    {"name": "Emirates Coffee Museum, Dubai", "lat": 25.27, "lon": 55.30, "Country": "UAE", "Type": "Museum", "Highlight": "Traditional Arabic coffee heritage; dallah collection", "Year Opened": 2014, "Notes": "Al Fahidi historical district; Arabic coffee UNESCO heritage", "color": "green"},
    {"name": "Museo del Cafe, Cartagena Colombia", "lat": 10.42, "lon": -75.55, "Country": "Colombia", "Type": "Museum", "Highlight": "Colombian coffee culture immersion; cupping lab", "Year Opened": 2012, "Notes": "Walled city; regional variety tasting", "color": "green"},
    {"name": "Kopi Museum, Penang Malaysia", "lat": 5.42, "lon": 100.34, "Country": "Malaysia", "Type": "Museum", "Highlight": "Kopitiam heritage; traditional roasting with butter/sugar", "Year Opened": 2016, "Notes": "Southeast Asian coffee (kopi) tradition preserved", "color": "green"},
    {"name": "Museo Nacional del Cafe, Coatepec Mexico", "lat": 19.45, "lon": -96.96, "Country": "Mexico", "Type": "Museum", "Highlight": "Veracruz coffee heritage; finca tours", "Year Opened": 2000, "Notes": "Mexican coffee history from colonial era to present", "color": "green"},
    {"name": "Coffee Museum, Coskun Ankara Turkey", "lat": 39.94, "lon": 32.85, "Country": "Turkey", "Type": "Museum", "Highlight": "Turkish coffee UNESCO heritage; ibrik collection", "Year Opened": 2019, "Notes": "Turkish coffee brewing tradition since 15th century", "color": "green"},
    {"name": "Lavazza Museum (Nuvola), Turin", "lat": 45.07, "lon": 7.69, "Country": "Italy", "Type": "Corporate Museum", "Highlight": "Interactive coffee journey; Cini Boeri architecture", "Year Opened": 2018, "Notes": "Nuvola complex; Italian espresso culture history", "color": "green"},
    {"name": "Illycaffe, Trieste Italy", "lat": 45.65, "lon": 13.78, "Country": "Italy", "Type": "Corporate Experience", "Highlight": "Universita del Caffe; art collection cups", "Year Opened": 2002, "Notes": "Illy art cups; single-origin lab; espresso education", "color": "green"},
    {"name": "Museo del Cafe Hacienda La Victoria, Venezuela", "lat": 10.36, "lon": -67.04, "Country": "Venezuela", "Type": "Plantation Museum", "Highlight": "19th century coffee hacienda restored", "Year Opened": 2004, "Notes": "Henri Pittier park; colonial-era processing equipment", "color": "green"},
    {"name": "The Coffee Experience, Amsterdam", "lat": 52.37, "lon": 4.90, "Country": "Netherlands", "Type": "Interactive Experience", "Highlight": "Cupping workshops, roasting demos", "Year Opened": 2019, "Notes": "Dutch coffee trading heritage; VOC history", "color": "green"},
    {"name": "Parque Nacional del Cafe, Montenegro Colombia", "lat": 4.55, "lon": -75.79, "Country": "Colombia", "Type": "Theme Park", "Highlight": "Coffee-themed amusement park; roller coasters + coffee education", "Year Opened": 1995, "Notes": "Quindio department; Coffee Cultural Landscape UNESCO zone", "color": "green"},
    {"name": "Museo del Cafe de Chiapas, Mexico", "lat": 16.75, "lon": -93.12, "Country": "Mexico", "Type": "Museum", "Highlight": "Chiapas coffee heritage; indigenous grower culture", "Year Opened": 2008, "Notes": "Tuxtla Gutierrez; Maya and Zoque coffee traditions", "color": "green"},
    {"name": "UCC Coffee Museum, Kobe Japan", "lat": 34.69, "lon": 135.19, "Country": "Japan", "Type": "Museum", "Highlight": "Only coffee museum in Japan; global coffee history", "Year Opened": 1987, "Notes": "Port Island; antique grinders; worldwide bean collection", "color": "green"},
    {"name": "Britt Coffee Tour, Heredia Costa Rica", "lat": 10.00, "lon": -84.12, "Country": "Costa Rica", "Type": "Tour Experience", "Highlight": "Theater + plantation + roasting + tasting", "Year Opened": 1991, "Notes": "Café Britt pioneered Costa Rica specialty tourism", "color": "green"},
    {"name": "Pergamino Coffee Lab, Medellin Colombia", "lat": 6.25, "lon": -75.57, "Country": "Colombia", "Type": "Lab Experience", "Highlight": "Cupping lab; single-estate flights", "Year Opened": 2012, "Notes": "El Poblado; farm-to-cup Colombian specialty", "color": "green"},
    {"name": "Coffee Island Museum, Patras Greece", "lat": 38.25, "lon": 21.73, "Country": "Greece", "Type": "Corporate Museum", "Highlight": "Greek coffee chain heritage; Mediterranean coffee culture", "Year Opened": 2015, "Notes": "Coffee Island brand; Greek frappe and freddo history", "color": "green"},
    {"name": "Jamaica Blue Mountain Coffee Tour, Mavis Bank", "lat": 18.08, "lon": -76.62, "Country": "Jamaica", "Type": "Factory Tour", "Highlight": "Jablum processing plant; tasting room", "Year Opened": 1981, "Notes": "Mavis Bank central processing; Blue Mountain certification", "color": "green"},
    {"name": "Kaffemuseum, Hamburg Germany", "lat": 53.55, "lon": 9.99, "Country": "Germany", "Type": "Museum", "Highlight": "Speicherstadt warehouse museum; roasting heritage", "Year Opened": 2006, "Notes": "Historic warehouse district; German coffee import history", "color": "green"},
    {"name": "Museo del Cafe, Havana Cuba", "lat": 23.14, "lon": -82.35, "Country": "Cuba", "Type": "Museum", "Highlight": "Cuban coffee culture; colada tradition", "Year Opened": 2001, "Notes": "Plaza Vieja; Sierra Maestra coffee heritage", "color": "green"},
    {"name": "Whittard of Chelsea Coffee Experience, London", "lat": 51.51, "lon": -0.17, "Country": "UK", "Type": "Tasting Experience", "Highlight": "British coffee and tea tasting rooms", "Year Opened": 2019, "Notes": "Flagship store; cupping and brewing workshops", "color": "green"},
    {"name": "Toby's Estate Coffee Academy, Brooklyn", "lat": 40.72, "lon": -73.96, "Country": "USA", "Type": "Training Academy", "Highlight": "Professional barista and brewing courses", "Year Opened": 2012, "Notes": "Williamsburg roastery; SCA certification courses", "color": "green"},
]


# ========================================================================
# MAIN RENDER FUNCTION
# ========================================================================
def render_coffee_maps_tab():
    """Render the Coffee & Cafe Culture Explorer tab."""
    st.markdown(
        '<div class="tab-header emerald"><h4>Coffee &amp; Cafe Culture Explorer</h4>'
        '<p>Coffee origins, roasters, cafe traditions, processing methods &amp; global coffee heritage</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        [
            "Coffee Belt Origins",
            "Famous Cafe Culture",
            "Specialty Coffee Roasters",
            "Coffee Processing Methods",
            "Historic Coffee Trade Routes",
            "Japanese Kissaten & Pour-Over",
            "Espresso Machine Heritage",
            "Coffee Plantations Open to Visitors",
            "World Barista Championship Venues",
            "Coffee Museums & Experiences",
        ],
        key="coffee_maps_mode",
    )

    # -----------------------------------------------------------------
    # MODE: Coffee Belt Origins
    # -----------------------------------------------------------------
    if mode == "Coffee Belt Origins":
        data = COFFEE_BELT_ORIGINS
        st.markdown("### Coffee Belt Origins")
        st.markdown(
            "The Coffee Belt stretches roughly between the Tropics of Cancer "
            "and Capricorn, spanning equatorial regions of Africa, Asia, and "
            "the Americas. **Arabica** (Coffea arabica) accounts for about "
            "60-70 percent of world production and grows best at 800-2,200m "
            "altitude. **Robusta** (Coffea canephora) thrives at lower "
            "altitudes with higher yields and caffeine content. Ethiopia "
            "remains the birthplace of Arabica, while Brazil is the largest "
            "producer worldwide."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Origins Mapped", len(data))
        c2.metric("Countries", len(set(d["Country"] for d in data)))
        c3.metric("Top Producer", "Brazil")
        c4.metric("Species Focus", "Arabica & Robusta")
        _show_map_and_data(data, zoom=2, csv_prefix="coffee_belt")

    # -----------------------------------------------------------------
    # MODE: Famous Cafe Culture
    # -----------------------------------------------------------------
    elif mode == "Famous Cafe Culture":
        data = FAMOUS_CAFE_CULTURE
        st.markdown("### Famous Cafe Culture")
        st.markdown(
            "From the grand Viennese coffeehouse tradition (UNESCO Intangible "
            "Heritage) to Parisian literary bistros, Italian espresso bars, "
            "and Turkish kahve houses, cafe culture has shaped intellectual "
            "life, art, politics, and social customs across centuries. These "
            "iconic establishments are living monuments to coffee's role in "
            "human civilization."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cafes Mapped", len(data))
        c2.metric("Countries", len(set(d["Country"] for d in data)))
        styles = set(d["Style"] for d in data)
        c3.metric("Cafe Styles", len(styles))
        oldest = min(d["Founded"] for d in data if isinstance(d["Founded"], int))
        c4.metric("Oldest Founded", oldest)
        _show_map_and_data(data, zoom=3, center=[45.0, 10.0], csv_prefix="cafe_culture")

    # -----------------------------------------------------------------
    # MODE: Specialty Coffee Roasters
    # -----------------------------------------------------------------
    elif mode == "Specialty Coffee Roasters":
        data = SPECIALTY_ROASTERS
        st.markdown("### Specialty Coffee Roasters (Third Wave)")
        st.markdown(
            "The Third Wave coffee movement treats coffee as an artisanal "
            "food product rather than a commodity. These pioneering roasters "
            "emphasize direct trade relationships, light-to-medium roast "
            "profiles that highlight terroir, and transparent sourcing. "
            "From Blue Bottle's 48-hour freshness philosophy to Tim "
            "Wendelboe's Nordic light-roast revolution, these roasters "
            "have redefined what coffee can taste like."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Roasters Mapped", len(data))
        c2.metric("Countries", len(set(d["Country"] for d in data)))
        c3.metric("Movement", "Third Wave")
        c4.metric("Era", "1990s - Present")
        _show_map_and_data(data, zoom=2, csv_prefix="specialty_roasters")

    # -----------------------------------------------------------------
    # MODE: Coffee Processing Methods
    # -----------------------------------------------------------------
    elif mode == "Coffee Processing Methods":
        data = COFFEE_PROCESSING
        st.markdown("### Coffee Processing Methods")
        st.markdown(
            "How coffee cherries are processed after picking dramatically "
            "affects flavor. **Washed** (wet) processing yields clean, bright, "
            "terroir-transparent cups. **Natural** (dry) processing, where "
            "the whole cherry dries intact, produces fruity, boozy flavors. "
            "**Honey** processing leaves mucilage on the bean during drying. "
            "**Wet-hulled** (Giling Basah) is unique to Indonesia. Newer "
            "experimental methods like **anaerobic fermentation** and "
            "**carbonic maceration** push boundaries."
        )
        methods = {}
        for d in data:
            m_name = d["Method"].split(" (")[0].split(" -")[0]
            methods[m_name] = methods.get(m_name, 0) + 1
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations Mapped", len(data))
        c2.metric("Methods Shown", len(methods))
        c3.metric("Countries", len(set(d["Country"] for d in data)))
        c4.metric("Most Common", "Washed & Natural")
        _show_map_and_data(data, zoom=2, csv_prefix="coffee_processing")

    # -----------------------------------------------------------------
    # MODE: Historic Coffee Trade Routes
    # -----------------------------------------------------------------
    elif mode == "Historic Coffee Trade Routes":
        data = HISTORIC_TRADE_ROUTES
        st.markdown("### Historic Coffee Trade Routes")
        st.markdown(
            "Coffee's journey from the Ethiopian highlands to global commodity "
            "spans six centuries of trade, colonialism, and cultural exchange. "
            "The Port of **Mocha** in Yemen gave coffee its early name and "
            "served as the sole export point until the Dutch smuggled plants "
            "to Java. The **Bourbon** variety emerged on Reunion Island. A "
            "single seedling carried to **Martinique** seeded the Americas. "
            "**Santos** became the world's greatest coffee port as Brazil "
            "dominated 19th-century production."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Trade Points Mapped", len(data))
        c2.metric("Countries", len(set(d["Country"] for d in data)))
        c3.metric("Earliest Era", "1400s")
        c4.metric("Key Port", "Mocha, Yemen")
        _show_map_and_data(data, zoom=2, csv_prefix="coffee_trade_routes")

    # -----------------------------------------------------------------
    # MODE: Japanese Kissaten & Pour-Over
    # -----------------------------------------------------------------
    elif mode == "Japanese Kissaten & Pour-Over":
        data = JAPANESE_KISSATEN
        st.markdown("### Japanese Kissaten & Pour-Over Culture")
        st.markdown(
            "Japan's **kissaten** (pure coffee shops) represent a unique "
            "coffee philosophy emphasizing craftsmanship, patience, and "
            "ritual. Masters like Sekiguchi Ichiro of Cafe de l'Ambre age "
            "beans for decades and brew through hand-sewn flannel (nel) "
            "drip filters. The modern **Third Wave** Japanese scene, led "
            "by roasters like Glitch, Onibus, and % Arabica, blends this "
            "meticulous tradition with global specialty sourcing. Japan's "
            "**siphon** brewing heritage and the **4:6 V60 method** by "
            "Tetsu Kasuya have influenced baristas worldwide."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cafes Mapped", len(data))
        kissaten_count = sum(1 for d in data if "Kissaten" in d.get("Style", ""))
        c2.metric("Classic Kissaten", kissaten_count)
        c3.metric("Third Wave", len(data) - kissaten_count)
        c4.metric("City Focus", "Tokyo & Kyoto")
        _show_map_and_data(data, zoom=6, center=[36.0, 137.0], csv_prefix="japanese_kissaten")

    # -----------------------------------------------------------------
    # MODE: Espresso Machine Heritage
    # -----------------------------------------------------------------
    elif mode == "Espresso Machine Heritage":
        data = ESPRESSO_MACHINE_HERITAGE
        st.markdown("### Espresso Machine Heritage")
        st.markdown(
            "Modern espresso owes its existence to Italian engineering. "
            "**Luigi Bezzera** patented the first espresso machine in 1901. "
            "**Achille Gaggia** invented the lever-piston that creates "
            "crema in 1948. The **Faema E61** (1961) introduced the "
            "thermosiphon group head copied by nearly every manufacturer "
            "since. **La Marzocco** pioneered dual-boiler technology. "
            "Today, innovators like **Slayer**, **Decent**, and **Kees "
            "van der Westen** push boundaries with pressure profiling "
            "and digital control."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Manufacturers Mapped", len(data))
        c2.metric("Countries", len(set(d["Country"] for d in data)))
        italian_count = sum(1 for d in data if d["Country"] == "Italy")
        c3.metric("Italian Makers", italian_count)
        c4.metric("First Patent", "1901 (Bezzera)")
        _show_map_and_data(data, zoom=3, center=[47.0, 10.0], csv_prefix="espresso_machines")

    # -----------------------------------------------------------------
    # MODE: Coffee Plantations Open to Visitors
    # -----------------------------------------------------------------
    elif mode == "Coffee Plantations Open to Visitors":
        data = VISITOR_PLANTATIONS
        st.markdown("### Coffee Plantations Open to Visitors")
        st.markdown(
            "From the volcanic slopes of **Kona, Hawaii** to the cloud "
            "forests of **Boquete, Panama** and the ancient highlands of "
            "**Ethiopian Sidamo**, these plantations and cooperatives "
            "welcome visitors for farm tours, cupping sessions, and "
            "immersive seed-to-cup experiences. Many offer eco-lodge "
            "accommodation, letting guests wake up surrounded by coffee "
            "trees and experience harvest firsthand."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Plantations Mapped", len(data))
        c2.metric("Countries", len(set(d["Country"] for d in data)))
        c3.metric("Continents", 5)
        c4.metric("Highlight", "Esmeralda Geisha")
        _show_map_and_data(data, zoom=2, csv_prefix="visitor_plantations")

    # -----------------------------------------------------------------
    # MODE: World Barista Championship Venues
    # -----------------------------------------------------------------
    elif mode == "World Barista Championship Venues":
        data = BARISTA_CHAMPIONSHIP
        st.markdown("### World Barista Championship Venues")
        st.markdown(
            "The **World Barista Championship** (WBC), organized by the "
            "Specialty Coffee Association (SCA), has crowned the world's "
            "best barista annually since 2000. Competitors prepare espresso, "
            "milk beverages, and a signature drink for judges in 15 minutes. "
            "Nordic countries dominated early years, while South Korea, "
            "Australia, and producing nations like Colombia and Guatemala "
            "have risen. Training academies worldwide prepare the next "
            "generation of champions."
        )
        c1, c2, c3, c4 = st.columns(4)
        competitions = [d for d in data if isinstance(d.get("Year"), int)]
        c1.metric("Competitions Mapped", len(competitions))
        countries_won = set(d["Winner"].split("(")[-1].rstrip(")") for d in competitions if d.get("Winner", "N/A") != "N/A")
        c2.metric("Winning Nations", len(countries_won))
        c3.metric("Training Centers", len(data) - len(competitions))
        c4.metric("Since", 2001)
        _show_map_and_data(data, zoom=2, csv_prefix="barista_championships")

    # -----------------------------------------------------------------
    # MODE: Coffee Museums & Experiences
    # -----------------------------------------------------------------
    elif mode == "Coffee Museums & Experiences":
        data = COFFEE_MUSEUMS
        st.markdown("### Coffee Museums & Experiences")
        st.markdown(
            "From the majestic **Bolsa do Cafe** palace in Santos, Brazil "
            "to the towering **Starbucks Reserve Roasteries** in Seattle, "
            "Shanghai, Milan, and Tokyo, coffee museums and immersive "
            "experiences celebrate every aspect of coffee heritage. "
            "Visitors can explore cupping labs in Colombia, Turkish "
            "coffee UNESCO traditions, Japanese antique grinder collections, "
            "and theme parks dedicated to the coffee bean."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Venues Mapped", len(data))
        c2.metric("Countries", len(set(d["Country"] for d in data)))
        types = set(d["Type"] for d in data)
        c3.metric("Venue Types", len(types))
        c4.metric("Highlight", "Starbucks Reserve")
        _show_map_and_data(data, zoom=2, csv_prefix="coffee_museums")
