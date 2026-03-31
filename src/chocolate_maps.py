import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module
import pandas as pd


def _popup(name, details):
    """Build a rich HTML popup string with escaped content.

    Creates a styled dark-themed popup for Folium markers with a gold
    accent header and tabular detail rows.  All user-facing text is
    escaped with ``html_module.escape`` to prevent injection.
    """
    safe_name = html_module.escape(str(name))
    rows = ""
    for k, v in details.items():
        safe_key = html_module.escape(str(k))
        safe_val = html_module.escape(str(v))
        rows += (
            f"<tr>"
            f"<td style='padding:4px 10px;color:#f0c040;font-weight:600;"
            f"white-space:nowrap;vertical-align:top;'>{safe_key}</td>"
            f"<td style='padding:4px 10px;color:#e8ecf4;'>{safe_val}</td>"
            f"</tr>"
        )
    return (
        f"<div style=\"font-family:'Segoe UI',Arial,sans-serif;"
        f"background:#1a1a2e;border:1px solid #f0c040;border-radius:10px;"
        f"padding:12px 14px;min-width:240px;max-width:360px;\">"
        f"<h4 style=\"margin:0 0 8px 0;color:#f0c040;font-size:14px;\">"
        f"{safe_name}</h4>"
        f"<table style=\"border-collapse:collapse;width:100%;\">{rows}</table>"
        f"</div>"
    )


def _build_map(locations, zoom=3, center=None):
    """Create a Folium map using the CartoDB dark_matter tile set.

    Parameters
    ----------
    locations : list[dict]
        Each dict must contain ``lat``, ``lon``, and ``name`` keys.
        Optional ``color`` key controls the marker icon colour.
        All remaining keys are rendered inside the marker popup.
    zoom : int
        Initial zoom level for the map (default 3 for world view).
    center : list | None
        ``[lat, lon]`` centre point.  When *None* the centroid of all
        supplied locations is computed automatically.

    Returns
    -------
    folium.Map
        A fully-populated Folium map object ready for rendering.
    """
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
        color = loc.get("color", "orange")
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


def _show_map_and_data(locations, zoom=3, center=None):
    """Render the interactive map, a dataframe preview, and a CSV download.

    This helper is shared by every mode inside ``render_chocolate_maps_tab``
    so that the visual layout is consistent across all ten map modes.
    """
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
        "chocolate_data.csv",
        "text/csv",
        key="choc_dl_" + str(hash(str(locations[:3]))),
    )


# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------

CACAO_REGIONS = [
    {"name": "Chuao, Venezuela", "lat": 10.49, "lon": -67.53, "Type": "Criollo", "Notes": "World's finest cacao, limited harvest", "Annual Tonnes": "~20", "color": "orange"},
    {"name": "Soconusco, Mexico", "lat": 15.15, "lon": -92.45, "Type": "Criollo/Trinitario", "Notes": "Ancient Mesoamerican cacao heartland", "Annual Tonnes": "~500", "color": "orange"},
    {"name": "Sulawesi, Indonesia", "lat": -1.50, "lon": 121.00, "Type": "Forastero", "Notes": "Third-largest global producer", "Annual Tonnes": "~270,000", "color": "red"},
    {"name": "Bahia, Brazil", "lat": -14.80, "lon": -39.05, "Type": "Forastero/Trinitario", "Notes": "Historic cacao fazendas, recovering from witches broom", "Annual Tonnes": "~120,000", "color": "orange"},
    {"name": "Ashanti Region, Ghana", "lat": 6.75, "lon": -1.52, "Type": "Forastero", "Notes": "Second-largest world producer, Cocobod regulated", "Annual Tonnes": "~800,000", "color": "red"},
    {"name": "Ivory Coast (San Pedro)", "lat": 4.75, "lon": -6.63, "Type": "Forastero", "Notes": "Worlds largest cacao producer, ~40% of global supply", "Annual Tonnes": "~2,200,000", "color": "darkred"},
    {"name": "Sambirano Valley, Madagascar", "lat": -14.28, "lon": 48.33, "Type": "Criollo/Trinitario", "Notes": "Distinctive fruity flavor, high-end market", "Annual Tonnes": "~10,000", "color": "orange"},
    {"name": "Papua New Guinea Highlands", "lat": -5.95, "lon": 145.78, "Type": "Trinitario", "Notes": "Smallholder farms, unique flavor profile", "Annual Tonnes": "~40,000", "color": "orange"},
    {"name": "Trinidad & Tobago", "lat": 10.45, "lon": -61.25, "Type": "Trinitario", "Notes": "Birthplace of Trinitario variety after 1727 hurricane", "Annual Tonnes": "~600", "color": "orange"},
    {"name": "Piura, Peru", "lat": -5.19, "lon": -80.63, "Type": "Native White Cacao", "Notes": "Rare white cacao beans, Premio Cacao award winner", "Annual Tonnes": "~3,000", "color": "orange"},
    {"name": "Tabasco, Mexico", "lat": 17.99, "lon": -92.93, "Type": "Criollo", "Notes": "Historic region, pre-Columbian cacao culture", "Annual Tonnes": "~15,000", "color": "orange"},
    {"name": "Cameroon (Centre Region)", "lat": 3.87, "lon": 11.52, "Type": "Forastero", "Notes": "Fifth-largest producer, growing exports", "Annual Tonnes": "~290,000", "color": "red"},
    {"name": "Nigeria (Ondo State)", "lat": 7.10, "lon": 4.83, "Type": "Forastero", "Notes": "Fourth-largest producer, smallholder dominated", "Annual Tonnes": "~340,000", "color": "red"},
    {"name": "Ecuador (Los Rios)", "lat": -1.55, "lon": -79.62, "Type": "Nacional (Arriba)", "Notes": "Fine-flavor cacao, floral aroma", "Annual Tonnes": "~350,000", "color": "orange"},
    {"name": "Colombia (Santander)", "lat": 7.13, "lon": -73.13, "Type": "Criollo/Trinitario", "Notes": "Rising fine-flavor origin, peace-driven expansion", "Annual Tonnes": "~65,000", "color": "orange"},
    {"name": "Dominican Republic (Duarte)", "lat": 19.28, "lon": -69.85, "Type": "Trinitario/Hispaniola", "Notes": "Largest organic cacao exporter", "Annual Tonnes": "~85,000", "color": "orange"},
    {"name": "Uganda (Bundibugyo)", "lat": 0.70, "lon": 30.06, "Type": "Forastero/Trinitario", "Notes": "Emerging East African origin", "Annual Tonnes": "~35,000", "color": "orange"},
    {"name": "Vietnam (Ben Tre)", "lat": 10.24, "lon": 106.38, "Type": "Trinitario", "Notes": "Rapidly growing Asian producer, Marou sourcing", "Annual Tonnes": "~5,000", "color": "orange"},
    {"name": "Sierra Leone (Kenema)", "lat": 7.88, "lon": -11.19, "Type": "Forastero", "Notes": "Post-conflict recovery crop", "Annual Tonnes": "~15,000", "color": "orange"},
    {"name": "Sao Tome & Principe", "lat": 0.19, "lon": 6.61, "Type": "Forastero/Amelonado", "Notes": "Island cacao, colonial plantation heritage", "Annual Tonnes": "~3,500", "color": "orange"},
    {"name": "Togo (Plateaux Region)", "lat": 7.00, "lon": 1.10, "Type": "Forastero", "Notes": "Small but consistent West African exporter", "Annual Tonnes": "~10,000", "color": "orange"},
    {"name": "Bolivia (Alto Beni)", "lat": -15.50, "lon": -67.50, "Type": "Wild Criollo", "Notes": "Wild-harvested Amazonian cacao, rare genetics", "Annual Tonnes": "~8,000", "color": "orange"},
    {"name": "Hawaii (Big Island)", "lat": 19.90, "lon": -155.10, "Type": "Various hybrids", "Notes": "Only US state growing cacao commercially", "Annual Tonnes": "~100", "color": "orange"},
    {"name": "Philippines (Davao)", "lat": 7.19, "lon": 125.46, "Type": "Trinitario/Forastero", "Notes": "Historic Southeast Asian producer, tablea tradition", "Annual Tonnes": "~10,000", "color": "orange"},
    {"name": "Tanzania (Kilombero Valley)", "lat": -8.05, "lon": 36.70, "Type": "Trinitario", "Notes": "Organic-focused, Kokoa Kamili operations", "Annual Tonnes": "~5,000", "color": "orange"},
    {"name": "India (Kerala)", "lat": 10.85, "lon": 76.27, "Type": "Forastero/Trinitario", "Notes": "Growing domestic chocolate market driving production", "Annual Tonnes": "~25,000", "color": "orange"},
    {"name": "Belize (Toledo District)", "lat": 16.20, "lon": -88.90, "Type": "Trinitario/Criollo", "Notes": "Maya cacao heritage, craft chocolate movement", "Annual Tonnes": "~200", "color": "orange"},
    {"name": "Honduras (La Mosquitia)", "lat": 15.00, "lon": -84.50, "Type": "Criollo", "Notes": "Ancient cacao forests, genetic treasure", "Annual Tonnes": "~500", "color": "orange"},
    {"name": "Vanuatu", "lat": -17.73, "lon": 168.32, "Type": "Trinitario", "Notes": "Pacific Island origin, growing specialty market", "Annual Tonnes": "~2,000", "color": "orange"},
    {"name": "Costa Rica (Talamanca)", "lat": 9.63, "lon": -82.83, "Type": "Trinitario/Matina", "Notes": "Indigenous Bribri cacao traditions, agroforestry", "Annual Tonnes": "~600", "color": "orange"},
]

HISTORIC_FACTORIES = [
    {"name": "Cadbury Bournville, Birmingham", "lat": 52.43, "lon": -1.93, "Founded": 1879, "Country": "UK", "Famous For": "Dairy Milk, model village for workers", "Status": "Active (Mondelez)", "color": "purple"},
    {"name": "Hershey Factory, Hershey PA", "lat": 40.29, "lon": -76.65, "Founded": 1903, "Country": "USA", "Famous For": "Hershey Bars, Kisses, company town", "Status": "Active", "color": "purple"},
    {"name": "Menier Chocolate, Noisiel", "lat": 48.85, "lon": 2.63, "Founded": 1825, "Country": "France", "Famous For": "First mass-produced chocolate bars", "Status": "Heritage site (Nestle)", "color": "purple"},
    {"name": "Van Houten, Weesp", "lat": 52.31, "lon": 5.04, "Founded": 1828, "Country": "Netherlands", "Famous For": "Invented cocoa press, dutching process", "Status": "Brand continues, factory closed", "color": "purple"},
    {"name": "Fry's, Bristol", "lat": 51.46, "lon": -2.58, "Founded": 1759, "Country": "UK", "Famous For": "First chocolate bar (1847), Cream eggs ancestor", "Status": "Closed (merged Cadbury)", "color": "purple"},
    {"name": "Baker Chocolate, Dorchester MA", "lat": 42.29, "lon": -71.06, "Founded": 1764, "Country": "USA", "Famous For": "Oldest American chocolate company", "Status": "Historic site", "color": "purple"},
    {"name": "Ghirardelli, San Francisco", "lat": 37.81, "lon": -122.42, "Founded": 1852, "Country": "USA", "Famous For": "Gold Rush era chocolate, Ghirardelli Square", "Status": "Active (Lindt)", "color": "purple"},
    {"name": "Suchard, Serrières", "lat": 46.99, "lon": 6.87, "Founded": 1826, "Country": "Switzerland", "Famous For": "Milka brand, purple cow branding", "Status": "Brand active (Mondelez)", "color": "purple"},
    {"name": "Rowntree, York", "lat": 53.96, "lon": -1.09, "Founded": 1862, "Country": "UK", "Famous For": "Kit Kat, Smarties, Aero", "Status": "Active (Nestle)", "color": "purple"},
    {"name": "Terry's, York", "lat": 53.95, "lon": -1.09, "Founded": 1767, "Country": "UK", "Famous For": "Chocolate Orange, All Gold", "Status": "Closed 2005, brand continues", "color": "purple"},
    {"name": "Ferrero, Alba", "lat": 44.70, "lon": 8.04, "Founded": 1946, "Country": "Italy", "Famous For": "Nutella, Ferrero Rocher, Kinder", "Status": "Active, global HQ", "color": "purple"},
    {"name": "Tobler/Toblerone, Bern", "lat": 46.95, "lon": 7.45, "Founded": 1908, "Country": "Switzerland", "Famous For": "Toblerone triangular bar, nougat", "Status": "Brand active (Mondelez)", "color": "purple"},
    {"name": "Stollwerck, Cologne", "lat": 50.94, "lon": 6.96, "Founded": 1839, "Country": "Germany", "Famous For": "Chocolate vending machines pioneer", "Status": "Closed, brand revived", "color": "purple"},
    {"name": "Fazer, Helsinki", "lat": 60.17, "lon": 24.94, "Founded": 1891, "Country": "Finland", "Famous For": "Fazer Blue milk chocolate, Nordic icon", "Status": "Active", "color": "purple"},
    {"name": "Marabou/Freia, Oslo", "lat": 59.92, "lon": 10.75, "Founded": 1898, "Country": "Norway", "Famous For": "Freia Melkesjokolade, Nordic favorite", "Status": "Active (Mondelez)", "color": "purple"},
    {"name": "Perugina, Perugia", "lat": 43.11, "lon": 12.39, "Founded": 1907, "Country": "Italy", "Famous For": "Baci Perugina, love note wrappers", "Status": "Active (Nestle)", "color": "purple"},
    {"name": "Cailler, Broc", "lat": 46.60, "lon": 7.09, "Founded": 1819, "Country": "Switzerland", "Famous For": "Oldest Swiss chocolate brand still active", "Status": "Active (Nestle), museum", "color": "purple"},
    {"name": "Cote dOr, Brussels", "lat": 50.85, "lon": 4.35, "Founded": 1883, "Country": "Belgium", "Famous For": "Elephant logo, Belgian heritage", "Status": "Brand active (Mondelez)", "color": "purple"},
    {"name": "Lindt, Kilchberg", "lat": 47.32, "lon": 8.55, "Founded": 1845, "Country": "Switzerland", "Famous For": "Conching invention, Lindor truffles", "Status": "Active, global HQ", "color": "purple"},
    {"name": "Mars Factory, Chicago", "lat": 41.88, "lon": -87.63, "Founded": 1911, "Country": "USA", "Famous For": "Milky Way, Snickers, M&Ms", "Status": "Active (McLean VA HQ)", "color": "purple"},
    {"name": "Nestlé, Vevey", "lat": 46.46, "lon": 6.84, "Founded": 1866, "Country": "Switzerland", "Famous For": "Milk chocolate co-invention with Daniel Peter", "Status": "Active, global HQ", "color": "purple"},
    {"name": "Whitman's, Philadelphia", "lat": 39.95, "lon": -75.17, "Founded": 1842, "Country": "USA", "Famous For": "Whitman's Sampler box", "Status": "Brand continues", "color": "purple"},
    {"name": "Droste, Haarlem", "lat": 52.38, "lon": 4.64, "Founded": 1863, "Country": "Netherlands", "Famous For": "Droste effect (recursive image), pastilles", "Status": "Brand continues", "color": "purple"},
    {"name": "Wilbur Chocolate, Lititz PA", "lat": 40.16, "lon": -76.31, "Founded": 1884, "Country": "USA", "Famous For": "Wilbur Buds (pre-date Kisses), museum", "Status": "Active (Cargill)", "color": "purple"},
    {"name": "Guylian, Sint-Niklaas", "lat": 51.16, "lon": 4.14, "Founded": 1960, "Country": "Belgium", "Famous For": "Seashell-shaped pralines", "Status": "Active", "color": "purple"},
    {"name": "Ritter Sport, Waldenbuch", "lat": 48.64, "lon": 9.13, "Founded": 1912, "Country": "Germany", "Famous For": "Square chocolate bars, Schokogarten", "Status": "Active, family-owned", "color": "purple"},
    {"name": "Moser Roth, Stuttgart", "lat": 48.78, "lon": 9.18, "Founded": 1841, "Country": "Germany", "Famous For": "Premium German confections", "Status": "Brand revived (Aldi)", "color": "purple"},
    {"name": "Poulain, Blois", "lat": 47.59, "lon": 1.33, "Founded": 1848, "Country": "France", "Famous For": "Iconic French chocolate, collectible cards", "Status": "Brand active (Carambar&Co)", "color": "purple"},
    {"name": "Milka (Suchard), Lörrach", "lat": 47.61, "lon": 7.66, "Founded": 1901, "Country": "Germany", "Famous For": "Alpine milk chocolate, purple branding", "Status": "Active (Mondelez)", "color": "purple"},
    {"name": "Valor, Villajoyosa", "lat": 38.51, "lon": -0.23, "Founded": 1881, "Country": "Spain", "Famous For": "Spanish drinking chocolate, museum town", "Status": "Active, family-owned", "color": "purple"},
]

BELGIAN_HERITAGE = [
    {"name": "Neuhaus, Brussels", "lat": 50.845, "lon": 4.355, "Founded": 1857, "Specialty": "Invented the praline (1912), ballotin box", "District": "Galerie de la Reine", "color": "orange"},
    {"name": "Godiva, Brussels", "lat": 50.847, "lon": 4.357, "Founded": 1926, "Specialty": "Luxury truffles, global brand", "District": "Grand Place area", "color": "orange"},
    {"name": "Leonidas, Brussels", "lat": 50.854, "lon": 4.352, "Founded": 1913, "Specialty": "Affordable fresh pralines, 1300+ shops", "District": "Boulevard Anspach", "color": "orange"},
    {"name": "Pierre Marcolini, Sablon", "lat": 50.840, "lon": 4.355, "Founded": 1995, "Specialty": "Bean-to-bar haute chocolaterie", "District": "Place du Grand Sablon", "color": "orange"},
    {"name": "Wittamer, Sablon", "lat": 50.841, "lon": 4.354, "Founded": 1910, "Specialty": "Patisserie and ganaches, royal warrant", "District": "Place du Grand Sablon", "color": "orange"},
    {"name": "Mary Chocolatier, Brussels", "lat": 50.843, "lon": 4.360, "Founded": 1919, "Specialty": "Royal warrant holder, Art Deco boxes", "District": "Rue Royale", "color": "orange"},
    {"name": "Cote dOr Museum, Brussels", "lat": 50.850, "lon": 4.348, "Founded": 1883, "Specialty": "Elephant logo heritage, Belgian icon", "District": "Central Brussels", "color": "orange"},
    {"name": "Belgian Chocolate Village, Brussels", "lat": 50.867, "lon": 4.321, "Founded": 2014, "Specialty": "Museum in former Koekelberg brewery", "District": "Koekelberg", "color": "orange"},
    {"name": "Choco-Story Bruges", "lat": 51.210, "lon": 3.227, "Founded": 2004, "Specialty": "Chocolate museum, Mayan cacao history", "District": "Historic center", "color": "orange"},
    {"name": "Dumon Chocolatier, Bruges", "lat": 51.211, "lon": 3.225, "Founded": 1992, "Specialty": "Hand-dipped fresh truffles", "District": "Eiermarkt", "color": "orange"},
    {"name": "The Chocolate Line, Bruges", "lat": 51.209, "lon": 3.228, "Founded": 2000, "Specialty": "Dominique Persoone, avant-garde flavors", "District": "Simon Stevinplein", "color": "orange"},
    {"name": "Guylian Factory, Sint-Niklaas", "lat": 51.155, "lon": 4.144, "Founded": 1960, "Specialty": "Seashell pralines, hazelnut filling", "District": "Sint-Niklaas industrial", "color": "orange"},
    {"name": "Callebaut Factory, Wieze", "lat": 51.00, "lon": 4.01, "Founded": 1911, "Specialty": "Worlds largest couverture supplier", "District": "Wieze", "color": "red"},
    {"name": "Jacques Chocolate, Eupen", "lat": 50.63, "lon": 6.04, "Founded": 1896, "Specialty": "Belgian mass-market, Callets", "District": "Eupen", "color": "orange"},
    {"name": "Galler, Liège", "lat": 50.64, "lon": 5.57, "Founded": 1976, "Specialty": "Galler bars, cat tongue chocolates", "District": "Liège center", "color": "orange"},
    {"name": "Belvas, Ghislenghien", "lat": 50.62, "lon": 3.89, "Founded": 2005, "Specialty": "Organic & fair-trade Belgian truffles", "District": "Wallonia", "color": "orange"},
    {"name": "Darcis, Verviers", "lat": 50.59, "lon": 5.87, "Founded": 1994, "Specialty": "Macarons & chocolate, pastry champion", "District": "Verviers", "color": "orange"},
    {"name": "Frederic Blondeel, Brussels", "lat": 50.850, "lon": 4.345, "Founded": 2010, "Specialty": "Bean-to-bar, roastery on site", "District": "Quai au Bois a Bruler", "color": "orange"},
    {"name": "Planète Chocolat, Brussels", "lat": 50.847, "lon": 4.349, "Founded": 1991, "Specialty": "Live praline workshops, demonstrations", "District": "Rue du Lombard", "color": "orange"},
    {"name": "BbyB, Antwerp", "lat": 51.22, "lon": 4.40, "Founded": 2005, "Specialty": "Minimalist luxury, Dominique Persoone protege", "District": "Antwerp center", "color": "orange"},
    {"name": "Neuhaus Factory, Vlezenbeek", "lat": 50.81, "lon": 4.22, "Founded": 1912, "Specialty": "Main praline production facility", "District": "Flemish Brabant", "color": "orange"},
    {"name": "Elisabeth Chocolatier, Brussels", "lat": 50.846, "lon": 4.353, "Founded": 2014, "Specialty": "Artisan bonbons, small-batch", "District": "Rue au Beurre", "color": "orange"},
    {"name": "Laurent Gerbaud, Brussels", "lat": 50.843, "lon": 4.352, "Founded": 2008, "Specialty": "No cream, fruit & nut focused", "District": "Rue Ravenstein", "color": "orange"},
    {"name": "Corné Port-Royal, Brussels", "lat": 50.848, "lon": 4.358, "Founded": 1935, "Specialty": "Manon blanc praline, royal warrants", "District": "Grand Place", "color": "orange"},
    {"name": "Passion Chocolat, Brussels", "lat": 50.849, "lon": 4.351, "Founded": 2009, "Specialty": "Single-origin ganaches, tasting events", "District": "Rue Bodenbroek", "color": "orange"},
]

SWISS_MAKERS = [
    {"name": "Lindt & Sprüngli, Kilchberg", "lat": 47.32, "lon": 8.55, "Founded": 1845, "Specialty": "Invented conching, Lindor truffles", "Region": "Zurich", "color": "red"},
    {"name": "Cailler (Nestlé), Broc", "lat": 46.60, "lon": 7.09, "Founded": 1819, "Specialty": "Oldest Swiss brand, Maison Cailler museum", "Region": "Fribourg", "color": "red"},
    {"name": "Toblerone (Mondelez), Bern", "lat": 46.95, "lon": 7.45, "Founded": 1908, "Specialty": "Triangular nougat bar, Matterhorn logo", "Region": "Bern", "color": "red"},
    {"name": "Sprüngli Confiserie, Zurich", "lat": 47.37, "lon": 8.54, "Founded": 1836, "Specialty": "Luxemburgerli macarons, Paradeplatz", "Region": "Zurich", "color": "red"},
    {"name": "Läderach, Ennenda", "lat": 47.04, "lon": 9.07, "Founded": 1962, "Specialty": "FrischSchoggi fresh chocolate slabs", "Region": "Glarus", "color": "red"},
    {"name": "Villars, Fribourg", "lat": 46.80, "lon": 7.16, "Founded": 1901, "Specialty": "Swiss chocolate with Alpine milk", "Region": "Fribourg", "color": "red"},
    {"name": "Frey (Migros), Buchs AG", "lat": 47.39, "lon": 8.08, "Founded": 1887, "Specialty": "Switzerlands best-selling chocolate", "Region": "Aargau", "color": "red"},
    {"name": "Camille Bloch, Courtelary", "lat": 47.18, "lon": 7.07, "Founded": 1929, "Specialty": "Ragusa, Torino bars", "Region": "Jura bernois", "color": "red"},
    {"name": "Favarger, Versoix", "lat": 46.28, "lon": 6.16, "Founded": 1826, "Specialty": "Avelines pralines, oldest Geneva chocolate", "Region": "Geneva", "color": "red"},
    {"name": "Maestrani, Flawil", "lat": 47.42, "lon": 9.19, "Founded": 1852, "Specialty": "Minor, Munz brands, Chocolarium", "Region": "St. Gallen", "color": "red"},
    {"name": "Alprose, Caslano", "lat": 45.96, "lon": 8.87, "Founded": 1957, "Specialty": "Chocolate museum, Ticino production", "Region": "Ticino", "color": "red"},
    {"name": "Auer, Geneva", "lat": 46.20, "lon": 6.15, "Founded": 1939, "Specialty": "Truffes du Jour, fresh daily truffles", "Region": "Geneva", "color": "red"},
    {"name": "Durig, Lausanne", "lat": 46.52, "lon": 6.63, "Founded": 2004, "Specialty": "Organic bean-to-bar, fair trade", "Region": "Vaud", "color": "red"},
    {"name": "Felchlin, Ibach", "lat": 46.97, "lon": 8.65, "Founded": 1908, "Specialty": "Professional couverture, Grand Cru", "Region": "Schwyz", "color": "red"},
    {"name": "Max Chocolatier, Lucerne", "lat": 47.05, "lon": 8.31, "Founded": 2009, "Specialty": "Artisan Swiss, local ingredients", "Region": "Lucerne", "color": "red"},
    {"name": "Beschle, Basel", "lat": 47.56, "lon": 7.59, "Founded": 1898, "Specialty": "Basel pralines, seasonal specialties", "Region": "Basel", "color": "red"},
    {"name": "Taucherli, Zurich", "lat": 47.38, "lon": 8.53, "Founded": 2013, "Specialty": "Micro bean-to-bar, minimal ingredients", "Region": "Zurich", "color": "red"},
    {"name": "Stella Bernrain, Kreuzlingen", "lat": 47.65, "lon": 9.18, "Founded": 1928, "Specialty": "Organic and fair-trade, Bodensee", "Region": "Thurgau", "color": "red"},
    {"name": "Chocolat Schönenberger, Bern", "lat": 46.94, "lon": 7.44, "Founded": 2018, "Specialty": "Swiss raw chocolate, minimal processing", "Region": "Bern", "color": "red"},
    {"name": "Teuscher, Zurich", "lat": 47.37, "lon": 8.54, "Founded": 1932, "Specialty": "Champagne truffles, luxury gift boxes", "Region": "Zurich", "color": "red"},
    {"name": "Confiserie Bachmann, Lucerne", "lat": 47.05, "lon": 8.30, "Founded": 1897, "Specialty": "Luzerner Chatzestreckerli cat tongue", "Region": "Lucerne", "color": "red"},
    {"name": "Gysi, Aarau", "lat": 47.39, "lon": 8.05, "Founded": 1897, "Specialty": "Traditional Aargau confiserie", "Region": "Aargau", "color": "red"},
    {"name": "du Rhône, Geneva", "lat": 46.20, "lon": 6.15, "Founded": 1875, "Specialty": "Geneva institution, drinking chocolate", "Region": "Geneva", "color": "red"},
    {"name": "Suchard Heritage, Serrières", "lat": 46.99, "lon": 6.87, "Founded": 1826, "Specialty": "Historic factory, Milka birthplace", "Region": "Neuchatel", "color": "red"},
    {"name": "Chocolaterie de lIle, Geneva", "lat": 46.21, "lon": 6.15, "Founded": 1978, "Specialty": "Island location, Genevan classic", "Region": "Geneva", "color": "red"},
]

MESOAMERICAN_ORIGINS = [
    {"name": "Soconusco, Chiapas", "lat": 15.15, "lon": -92.45, "Period": "1900 BCE - present", "Culture": "Mokaya / Maya / Aztec", "Significance": "Earliest known cacao cultivation", "color": "darkred"},
    {"name": "Colha, Belize", "lat": 18.17, "lon": -88.56, "Period": "600 BCE", "Culture": "Maya", "Significance": "Cacao residue in pottery vessels", "color": "darkred"},
    {"name": "Tikal, Guatemala", "lat": 17.22, "lon": -89.62, "Period": "300-900 CE", "Culture": "Classic Maya", "Significance": "Cacao glyphs on royal vessels", "color": "darkred"},
    {"name": "Copan, Honduras", "lat": 14.84, "lon": -89.14, "Period": "400-800 CE", "Culture": "Classic Maya", "Significance": "Cacao-themed sculptures, royal feasts", "color": "darkred"},
    {"name": "Palenque, Mexico", "lat": 17.48, "lon": -92.05, "Period": "600-800 CE", "Culture": "Classic Maya", "Significance": "Palace cacao preparation scenes", "color": "darkred"},
    {"name": "Calakmul, Mexico", "lat": 18.11, "lon": -89.81, "Period": "500-700 CE", "Culture": "Classic Maya", "Significance": "Cacao tribute records, murals", "color": "darkred"},
    {"name": "Teotihuacan, Mexico", "lat": 19.69, "lon": -98.84, "Period": "200-600 CE", "Culture": "Teotihuacano", "Significance": "Imported cacao trade, murals", "color": "darkred"},
    {"name": "Tenochtitlan (Mexico City)", "lat": 19.43, "lon": -99.13, "Period": "1325-1521 CE", "Culture": "Aztec", "Significance": "Cacao beans as currency, xocolatl drink", "color": "darkred"},
    {"name": "Monte Alban, Oaxaca", "lat": 17.04, "lon": -96.77, "Period": "500 BCE - 700 CE", "Culture": "Zapotec", "Significance": "Cacao in elite burials", "color": "darkred"},
    {"name": "Chichen Itza, Mexico", "lat": 20.68, "lon": -88.57, "Period": "600-1200 CE", "Culture": "Maya-Toltec", "Significance": "Cacao trade hub, cenote offerings", "color": "darkred"},
    {"name": "Uxmal, Mexico", "lat": 20.36, "lon": -89.77, "Period": "700-1000 CE", "Culture": "Puuc Maya", "Significance": "Cacao in ceremonial contexts", "color": "darkred"},
    {"name": "Cerén, El Salvador", "lat": 13.82, "lon": -89.35, "Period": "600 CE", "Culture": "Maya commoners", "Significance": "Cacao plants preserved by ash, household use", "color": "darkred"},
    {"name": "Izapa, Mexico", "lat": 14.95, "lon": -92.16, "Period": "1500 BCE - 100 CE", "Culture": "Izapan/pre-Maya", "Significance": "Possible cacao deity representations", "color": "darkred"},
    {"name": "San Lorenzo, Veracruz", "lat": 17.75, "lon": -94.76, "Period": "1800-1200 BCE", "Culture": "Olmec", "Significance": "Earliest Mesoamerican cacao residue evidence", "color": "darkred"},
    {"name": "La Venta, Tabasco", "lat": 18.10, "lon": -94.04, "Period": "900-400 BCE", "Culture": "Olmec", "Significance": "Cacao in ceremonial offerings", "color": "darkred"},
    {"name": "Cholula, Mexico", "lat": 19.06, "lon": -98.30, "Period": "500 BCE - 1519 CE", "Culture": "Various", "Significance": "Continuous cacao use over 2000 years", "color": "darkred"},
    {"name": "Tazumal, El Salvador", "lat": 13.98, "lon": -89.67, "Period": "100-1200 CE", "Culture": "Maya / Pipil", "Significance": "Cacao-centric trade routes", "color": "darkred"},
    {"name": "Kaminaljuyu, Guatemala", "lat": 14.63, "lon": -90.54, "Period": "800 BCE - 1200 CE", "Culture": "Maya Highland", "Significance": "Cacao trade with lowlands and Pacific coast", "color": "darkred"},
    {"name": "Quirigua, Guatemala", "lat": 15.27, "lon": -89.04, "Period": "400-900 CE", "Culture": "Classic Maya", "Significance": "Cacao mentioned in royal stelae", "color": "darkred"},
    {"name": "Bonampak, Mexico", "lat": 16.70, "lon": -91.07, "Period": "600-800 CE", "Culture": "Classic Maya", "Significance": "Murals showing cacao in court scenes", "color": "darkred"},
    {"name": "Tres Zapotes, Veracruz", "lat": 18.47, "lon": -95.44, "Period": "1000 BCE - 1000 CE", "Culture": "Olmec/Epi-Olmec", "Significance": "Cacao beverages in elite contexts", "color": "darkred"},
    {"name": "Yaxchilan, Mexico", "lat": 16.90, "lon": -90.97, "Period": "400-800 CE", "Culture": "Classic Maya", "Significance": "Cacao tribute and royal chocolate feasting", "color": "darkred"},
    {"name": "El Mirador, Guatemala", "lat": 17.75, "lon": -89.92, "Period": "600 BCE - 100 CE", "Culture": "Preclassic Maya", "Significance": "Massive pyramids funded by cacao trade", "color": "darkred"},
    {"name": "Xochicalco, Mexico", "lat": 18.80, "lon": -99.30, "Period": "650-900 CE", "Culture": "Epiclassic", "Significance": "Trade center linking cacao routes", "color": "darkred"},
    {"name": "Tulum, Mexico", "lat": 20.21, "lon": -87.43, "Period": "1200-1521 CE", "Culture": "Postclassic Maya", "Significance": "Coastal cacao trading port", "color": "darkred"},
    {"name": "Santa Leticia, El Salvador", "lat": 13.85, "lon": -89.80, "Period": "500 BCE", "Culture": "Preclassic", "Significance": "Fat Boy sculptures linked to cacao elite", "color": "darkred"},
    {"name": "Caracol, Belize", "lat": 16.76, "lon": -89.12, "Period": "300-900 CE", "Culture": "Classic Maya", "Significance": "Hieroglyphic cacao references", "color": "darkred"},
    {"name": "Naj Tunich Cave, Guatemala", "lat": 16.07, "lon": -89.32, "Period": "700-900 CE", "Culture": "Classic Maya", "Significance": "Cave paintings depicting cacao rituals", "color": "darkred"},
    {"name": "Mixco Viejo, Guatemala", "lat": 14.87, "lon": -90.66, "Period": "1100-1524 CE", "Culture": "Kaqchikel Maya", "Significance": "Cacao stores found in fortress", "color": "darkred"},
    {"name": "Puerto Escondido, Honduras", "lat": 15.32, "lon": -87.83, "Period": "1100 BCE", "Culture": "Early Formative", "Significance": "Cacao beverage residue, earliest pottery evidence", "color": "darkred"},
]

CONFECTIONERY_CAPITALS = [
    {"name": "Brussels, Belgium", "lat": 50.85, "lon": 4.35, "Title": "Chocolate Capital of the World", "Chocolatiers": "2000+", "Annual Production": "220,000 tonnes", "color": "orange"},
    {"name": "Zurich, Switzerland", "lat": 47.37, "lon": 8.54, "Title": "Swiss Chocolate Hub", "Chocolatiers": "500+", "Annual Production": "200,000 tonnes (national)", "color": "red"},
    {"name": "Modica, Sicily", "lat": 36.84, "lon": 14.76, "Title": "Aztec-Style Chocolate City", "Chocolatiers": "30+", "Annual Production": "Artisan-scale, cold-process", "color": "orange"},
    {"name": "Turin, Italy", "lat": 45.07, "lon": 7.69, "Title": "Gianduiotto Capital", "Chocolatiers": "100+", "Annual Production": "85,000 tonnes", "color": "orange"},
    {"name": "Villajoyosa, Spain", "lat": 38.51, "lon": -0.23, "Title": "Spanish Chocolate Town", "Chocolatiers": "10+", "Annual Production": "Heritage scale", "color": "orange"},
    {"name": "Bayonne, France", "lat": 43.49, "lon": -1.47, "Title": "Frances Chocolate City", "Chocolatiers": "30+", "Annual Production": "Artisan-focused", "color": "orange"},
    {"name": "York, England", "lat": 53.96, "lon": -1.08, "Title": "UK Chocolate City", "Chocolatiers": "Heritage trail", "Annual Production": "Rowntree/Terry legacy", "color": "purple"},
    {"name": "Hershey, Pennsylvania", "lat": 40.29, "lon": -76.65, "Title": "Sweetest Place on Earth", "Chocolatiers": "Hershey Co HQ", "Annual Production": "Billions of units", "color": "orange"},
    {"name": "Perugia, Italy", "lat": 43.11, "lon": 12.39, "Title": "Eurochocolate Festival Host", "Chocolatiers": "50+", "Annual Production": "Baci capital", "color": "orange"},
    {"name": "Oaxaca, Mexico", "lat": 17.07, "lon": -96.72, "Title": "Traditional Chocolate Heartland", "Chocolatiers": "Molinillo tradition", "Annual Production": "Artisan cacao", "color": "orange"},
    {"name": "Astorga, Spain", "lat": 42.46, "lon": -6.06, "Title": "Museo del Chocolate", "Chocolatiers": "Historic mills", "Annual Production": "Heritage", "color": "orange"},
    {"name": "Cologne, Germany", "lat": 50.94, "lon": 6.96, "Title": "Chocolate Museum City", "Chocolatiers": "Imhoff-Schokoladenmuseum", "Annual Production": "German chocolate hub", "color": "orange"},
    {"name": "Alba, Italy", "lat": 44.70, "lon": 8.04, "Title": "Ferrero/Nutella Birthplace", "Chocolatiers": "Ferrero HQ + artisans", "Annual Production": "365,000 tonnes Nutella/yr", "color": "orange"},
    {"name": "Bruges, Belgium", "lat": 51.21, "lon": 3.23, "Title": "Chocolate Tourism Capital", "Chocolatiers": "50+ shops", "Annual Production": "Tourism-focused artisan", "color": "orange"},
    {"name": "Tokyo, Japan", "lat": 35.68, "lon": 139.69, "Title": "Bean-to-Bar Innovation Capital", "Chocolatiers": "200+ craft", "Annual Production": "~250,000 tonnes (national)", "color": "orange"},
    {"name": "Accra, Ghana", "lat": 5.60, "lon": -0.19, "Title": "West African Cacao Capital", "Chocolatiers": "Growing local scene", "Annual Production": "800,000t cacao export", "color": "orange"},
    {"name": "Abidjan, Ivory Coast", "lat": 5.36, "lon": -4.01, "Title": "Worlds Cacao Hub", "Chocolatiers": "Processing plants", "Annual Production": "2.2M tonnes cacao", "color": "red"},
    {"name": "Quito, Ecuador", "lat": -0.18, "lon": -78.47, "Title": "Fine-Flavor Cacao Capital", "Chocolatiers": "Pacari, Republica del Cacao", "Annual Production": "350,000t fine cacao", "color": "orange"},
    {"name": "São Paulo, Brazil", "lat": -23.55, "lon": -46.63, "Title": "South American Chocolate Hub", "Chocolatiers": "Dengo, AMMA, Nugali presence", "Annual Production": "~270,000 tonnes national", "color": "orange"},
    {"name": "Antwerp, Belgium", "lat": 51.22, "lon": 4.40, "Title": "Diamond & Chocolate City", "Chocolatiers": "Major craft scene", "Annual Production": "Significant", "color": "orange"},
    {"name": "Paris, France", "lat": 48.86, "lon": 2.35, "Title": "Haute Chocolaterie Capital", "Chocolatiers": "300+ artisan", "Annual Production": "Premium market leader", "color": "orange"},
    {"name": "Grenada, Caribbean", "lat": 12.05, "lon": -61.75, "Title": "Chocolate Island", "Chocolatiers": "Grenada Chocolate Co", "Annual Production": "Organic island cacao", "color": "orange"},
    {"name": "Tabasco, Mexico", "lat": 17.99, "lon": -92.93, "Title": "Pre-Columbian Cacao Region", "Chocolatiers": "Traditional producers", "Annual Production": "Heritage cacao", "color": "orange"},
    {"name": "Lviv, Ukraine", "lat": 49.84, "lon": 24.03, "Title": "Lviv Chocolate Capital", "Chocolatiers": "Lviv Handmade Chocolate", "Annual Production": "Artisan tourism", "color": "orange"},
    {"name": "Copenhagen, Denmark", "lat": 55.68, "lon": 12.57, "Title": "Nordic Chocolate Innovation", "Chocolatiers": "Friis-Holm, Summerbird", "Annual Production": "Craft-focused", "color": "orange"},
]

CHOCOLATE_MUSEUMS = [
    {"name": "Lindt Home of Chocolate, Kilchberg", "lat": 47.32, "lon": 8.55, "Country": "Switzerland", "Highlight": "Worlds tallest chocolate fountain (9m)", "Year Opened": 2020, "color": "green"},
    {"name": "Choco-Story, Bruges", "lat": 51.21, "lon": 3.23, "Country": "Belgium", "Highlight": "Mayan cacao history, live demos", "Year Opened": 2004, "color": "green"},
    {"name": "Imhoff-Schokoladenmuseum, Cologne", "lat": 50.93, "lon": 6.96, "Country": "Germany", "Highlight": "Rhine-side museum, chocolate fountain", "Year Opened": 1993, "color": "green"},
    {"name": "Cadbury World, Bournville", "lat": 52.43, "lon": -1.93, "Country": "UK", "Highlight": "4D cinema, Cadabra ride, history tour", "Year Opened": 1990, "color": "green"},
    {"name": "Hershey's Chocolate World, PA", "lat": 40.29, "lon": -76.65, "Country": "USA", "Highlight": "Free factory tour ride, tasting", "Year Opened": 1973, "color": "green"},
    {"name": "Musée du Chocolat, Bayonne", "lat": 43.49, "lon": -1.48, "Country": "France", "Highlight": "Jewish chocolate-making heritage", "Year Opened": 2012, "color": "green"},
    {"name": "Maison Cailler, Broc", "lat": 46.60, "lon": 7.09, "Country": "Switzerland", "Highlight": "Immersive sensory journey, free samples", "Year Opened": 2010, "color": "green"},
    {"name": "Museo del Cioccolato, Modica", "lat": 36.84, "lon": 14.76, "Country": "Italy", "Highlight": "Ancient Aztec cold-process technique", "Year Opened": 2008, "color": "green"},
    {"name": "Chocolate Museum, Barcelona", "lat": 41.39, "lon": 2.18, "Country": "Spain", "Highlight": "Chocolate sculpture gallery, workshops", "Year Opened": 2000, "color": "green"},
    {"name": "Belgian Chocolate Village, Brussels", "lat": 50.87, "lon": 4.32, "Country": "Belgium", "Highlight": "Former brewery, tropical greenhouse", "Year Opened": 2014, "color": "green"},
    {"name": "Museo del Cacao y del Chocolate, Mexico City", "lat": 19.43, "lon": -99.14, "Country": "Mexico", "Highlight": "Mesoamerican cacao history, molinillo demos", "Year Opened": 2012, "color": "green"},
    {"name": "Alprose Chocolate Museum, Caslano", "lat": 45.96, "lon": 8.87, "Country": "Switzerland", "Highlight": "Factory tour in Ticino", "Year Opened": 1998, "color": "green"},
    {"name": "Chocolarium (Maestrani), Flawil", "lat": 47.42, "lon": 9.19, "Country": "Switzerland", "Highlight": "Interactive chocolate adventure", "Year Opened": 2017, "color": "green"},
    {"name": "Valor Chocolate Museum, Villajoyosa", "lat": 38.51, "lon": -0.23, "Country": "Spain", "Highlight": "Historic Valor factory exhibits", "Year Opened": 1999, "color": "green"},
    {"name": "ChocoMuseo, Cusco", "lat": -13.52, "lon": -71.97, "Country": "Peru", "Highlight": "Bean-to-bar workshops, cacao farm visits", "Year Opened": 2009, "color": "green"},
    {"name": "Musée Les Secrets du Chocolat, Strasbourg", "lat": 48.58, "lon": 7.68, "Country": "France", "Highlight": "Schaal chocolate factory tours", "Year Opened": 2003, "color": "green"},
    {"name": "Jacques Torres Chocolate, NYC", "lat": 40.72, "lon": -74.00, "Country": "USA", "Highlight": "Factory viewing, Mr. Chocolate", "Year Opened": 2000, "color": "green"},
    {"name": "Chocolate Museum, Astorga", "lat": 42.46, "lon": -6.06, "Country": "Spain", "Highlight": "Maragato chocolate history", "Year Opened": 1994, "color": "green"},
    {"name": "Ritter Sport Schokogarten, Waldenbuch", "lat": 48.64, "lon": 9.13, "Country": "Germany", "Highlight": "Custom chocolate bar workshop", "Year Opened": 2005, "color": "green"},
    {"name": "Chocolate Museum, Lviv", "lat": 49.84, "lon": 24.03, "Country": "Ukraine", "Highlight": "Handmade chocolate, miniature city models", "Year Opened": 2008, "color": "green"},
    {"name": "York's Chocolate Story, York", "lat": 53.96, "lon": -1.08, "Country": "UK", "Highlight": "Rowntree/Terry heritage, guided tours", "Year Opened": 2012, "color": "green"},
    {"name": "ChocoMuseo, Lima", "lat": -12.05, "lon": -77.03, "Country": "Peru", "Highlight": "Peruvian cacao workshops", "Year Opened": 2012, "color": "green"},
    {"name": "Haigh's Chocolate Visitors Centre, Adelaide", "lat": -34.92, "lon": 138.60, "Country": "Australia", "Highlight": "Oldest Australian chocolate factory", "Year Opened": 2008, "color": "green"},
    {"name": "Chocolate Museum, Istanbul", "lat": 41.01, "lon": 28.98, "Country": "Turkey", "Highlight": "Pelit Chocolate Museum, 10,000 pieces", "Year Opened": 2013, "color": "green"},
    {"name": "Museu de la Xocolata, Barcelona", "lat": 41.39, "lon": 2.18, "Country": "Spain", "Highlight": "Pastry guild history, Easter egg art", "Year Opened": 2000, "color": "green"},
    {"name": "Chocolate Happy Land, Shiroi", "lat": 35.79, "lon": 140.07, "Country": "Japan", "Highlight": "Lotte factory tour, samples", "Year Opened": 2007, "color": "green"},
    {"name": "Grenada Chocolate Festival", "lat": 12.05, "lon": -61.75, "Country": "Grenada", "Highlight": "Annual tree-to-bar festival", "Year Opened": 2014, "color": "green"},
]

BEAN_TO_BAR = [
    {"name": "Dandelion Chocolate, San Francisco", "lat": 37.76, "lon": -122.42, "Country": "USA", "Style": "Two-ingredient bars, single origin", "Founded": 2010, "color": "orange"},
    {"name": "Mast Brothers, Brooklyn", "lat": 40.72, "lon": -73.96, "Country": "USA", "Style": "Artisan bars, minimalist packaging", "Founded": 2007, "color": "orange"},
    {"name": "Dick Taylor Craft Chocolate, Eureka CA", "lat": 40.80, "lon": -124.16, "Country": "USA", "Style": "Redwood Country craft, single-origin", "Founded": 2010, "color": "orange"},
    {"name": "Marou Faiseurs de Chocolat, HCMC", "lat": 10.78, "lon": 106.70, "Country": "Vietnam", "Style": "Vietnamese single-estate, vibrant packaging", "Founded": 2011, "color": "orange"},
    {"name": "Friis-Holm, Copenhagen", "lat": 55.68, "lon": 12.57, "Country": "Denmark", "Style": "Nicaraguan cacao specialist, fermentation focus", "Founded": 2007, "color": "orange"},
    {"name": "Pump Street Chocolate, Orford UK", "lat": 52.10, "lon": 1.53, "Country": "UK", "Style": "Bakery-turned-chocolate maker, sourdough bars", "Founded": 2012, "color": "orange"},
    {"name": "Amedei, Pontedera Italy", "lat": 43.66, "lon": 10.63, "Country": "Italy", "Style": "Porcelana bars, Toscano Black", "Founded": 1990, "color": "orange"},
    {"name": "Domori, Turin Italy", "lat": 45.07, "lon": 7.69, "Country": "Italy", "Style": "Criollo specialist, Hacienda relationships", "Founded": 1997, "color": "orange"},
    {"name": "Original Beans, Amsterdam", "lat": 52.37, "lon": 4.90, "Country": "Netherlands", "Style": "Conservation chocolate, one bar = one tree", "Founded": 2008, "color": "orange"},
    {"name": "Pacari, Quito Ecuador", "lat": -0.18, "lon": -78.47, "Country": "Ecuador", "Style": "Worlds most awarded organic chocolate", "Founded": 2002, "color": "orange"},
    {"name": "Raaka, Brooklyn NY", "lat": 40.68, "lon": -73.97, "Country": "USA", "Style": "Unroasted virgin chocolate, bold flavors", "Founded": 2010, "color": "orange"},
    {"name": "Fjak, Eidfjord Norway", "lat": 60.47, "lon": 7.07, "Country": "Norway", "Style": "Nordic minimalism, fjord-side production", "Founded": 2016, "color": "orange"},
    {"name": "Standout Chocolate, Gothenburg", "lat": 57.71, "lon": 11.97, "Country": "Sweden", "Style": "Swedish craft, award-winning", "Founded": 2014, "color": "orange"},
    {"name": "Zotter, Riegersburg Austria", "lat": 47.00, "lon": 15.93, "Country": "Austria", "Style": "Hand-scooped, edible zoo, 500+ varieties", "Founded": 1999, "color": "orange"},
    {"name": "Menakao, Antananarivo", "lat": -18.91, "lon": 47.52, "Country": "Madagascar", "Style": "First Malagasy bean-to-bar, fruity cacao", "Founded": 2010, "color": "orange"},
    {"name": "Grenada Chocolate Co", "lat": 12.05, "lon": -61.75, "Country": "Grenada", "Style": "Solar-powered, co-operative, tree-to-bar", "Founded": 1999, "color": "orange"},
    {"name": "Mashpi Chocolate, Quito", "lat": -0.16, "lon": -78.87, "Country": "Ecuador", "Style": "Cloud forest cacao, eco-lodge linked", "Founded": 2012, "color": "orange"},
    {"name": "Fu Wan Chocolate, Pingtung Taiwan", "lat": 22.67, "lon": 120.49, "Country": "Taiwan", "Style": "Taiwanese cacao, ICA gold winner", "Founded": 2014, "color": "orange"},
    {"name": "Soma Chocolatemaker, Toronto", "lat": 43.65, "lon": -79.38, "Country": "Canada", "Style": "Distillery District workshop, gelato too", "Founded": 2003, "color": "orange"},
    {"name": "Bahen & Co, Margaret River", "lat": -33.95, "lon": 115.07, "Country": "Australia", "Style": "Stone-ground, hand-wrapped, small batch", "Founded": 2010, "color": "orange"},
    {"name": "Naive, Vilnius Lithuania", "lat": 54.69, "lon": 25.28, "Country": "Lithuania", "Style": "Wild inclusions: porcini, hemp, black bread", "Founded": 2010, "color": "orange"},
    {"name": "Cacao Hunters, Bogota", "lat": 4.71, "lon": -74.07, "Country": "Colombia", "Style": "Colombian single-origin champion", "Founded": 2013, "color": "orange"},
    {"name": "Ocelot, Edinburgh", "lat": 55.95, "lon": -3.19, "Country": "UK", "Style": "Scottish craft, vibrant branding", "Founded": 2014, "color": "orange"},
    {"name": "Qantu Chocolate, Montreal", "lat": 45.50, "lon": -73.57, "Country": "Canada", "Style": "Peruvian-Canadian, minimal sugar", "Founded": 2015, "color": "orange"},
    {"name": "Ritual Chocolate, Park City UT", "lat": 40.65, "lon": -111.50, "Country": "USA", "Style": "Small-batch, mountain craft", "Founded": 2010, "color": "orange"},
    {"name": "Krak Chocolade, Amsterdam", "lat": 52.36, "lon": 4.92, "Country": "Netherlands", "Style": "Micro-batch, 30+ origins", "Founded": 2013, "color": "orange"},
    {"name": "Solkiki, Exeter UK", "lat": 50.72, "lon": -3.53, "Country": "UK", "Style": "Award-winning inclusion bars", "Founded": 2014, "color": "orange"},
    {"name": "Akesson's, London", "lat": 51.51, "lon": -0.13, "Country": "UK", "Style": "Estate-grown Madagascar & Brazil", "Founded": 2009, "color": "orange"},
]

FAMOUS_PATISSERIES = [
    {"name": "Ladurée, Paris", "lat": 48.87, "lon": 2.33, "Country": "France", "Famous For": "Macarons, invented double-decker macaron", "Founded": 1862, "color": "pink"},
    {"name": "Pierre Hermé, Paris", "lat": 48.85, "lon": 2.33, "Country": "France", "Famous For": "Ispahan macaron, Picasso of Pastry", "Founded": 1998, "color": "pink"},
    {"name": "Demel, Vienna", "lat": 48.21, "lon": 16.37, "Country": "Austria", "Famous For": "Sachertorte rival, imperial purveyor", "Founded": 1786, "color": "pink"},
    {"name": "Hotel Sacher, Vienna", "lat": 48.20, "lon": 16.37, "Country": "Austria", "Famous For": "Original Sachertorte since 1832", "Founded": 1876, "color": "pink"},
    {"name": "Café Gerbeaud, Budapest", "lat": 47.50, "lon": 19.05, "Country": "Hungary", "Famous For": "Dobos torte, Gerbeaud slice", "Founded": 1858, "color": "pink"},
    {"name": "Confeitaria Nacional, Lisbon", "lat": 38.71, "lon": -9.14, "Country": "Portugal", "Famous For": "Pastéis de nata, oldest Lisbon pastry shop", "Founded": 1829, "color": "pink"},
    {"name": "Pastéis de Belém, Lisbon", "lat": 38.70, "lon": -9.20, "Country": "Portugal", "Famous For": "Original custard tarts, secret recipe", "Founded": 1837, "color": "pink"},
    {"name": "Escriba, Barcelona", "lat": 41.38, "lon": 2.17, "Country": "Spain", "Famous For": "Art Nouveau facade, fantasy pastry", "Founded": 1906, "color": "pink"},
    {"name": "Caffè Florian, Venice", "lat": 45.43, "lon": 12.34, "Country": "Italy", "Famous For": "Oldest café in world, hot chocolate", "Founded": 1720, "color": "pink"},
    {"name": "Angelina, Paris", "lat": 48.87, "lon": 2.33, "Country": "France", "Famous For": "Mont-Blanc pastry, Africain hot chocolate", "Founded": 1903, "color": "pink"},
    {"name": "Toraya, Tokyo", "lat": 35.68, "lon": 139.73, "Country": "Japan", "Famous For": "Yokan wagashi, 500-year Imperial purveyor", "Founded": 1526, "color": "pink"},
    {"name": "Sprüngli, Zurich", "lat": 47.37, "lon": 8.54, "Country": "Switzerland", "Famous For": "Luxemburgerli, Paradeplatz institution", "Founded": 1836, "color": "pink"},
    {"name": "Café Central, Vienna", "lat": 48.21, "lon": 16.37, "Country": "Austria", "Famous For": "Intellectual coffeehouse, Apfelstrudel", "Founded": 1876, "color": "pink"},
    {"name": "Dominique Ansel Bakery, NYC", "lat": 40.73, "lon": -74.00, "Country": "USA", "Famous For": "Cronut inventor, pastry innovation", "Founded": 2011, "color": "pink"},
    {"name": "Du Pain et des Idées, Paris", "lat": 48.87, "lon": 2.36, "Country": "France", "Famous For": "Pain des Amis, historic boulangerie", "Founded": 2002, "color": "pink"},
    {"name": "Hofbäckerei Edegger-Tax, Graz", "lat": 47.07, "lon": 15.44, "Country": "Austria", "Famous For": "Oldest bakery in Styria, imperial warrant", "Founded": 1569, "color": "pink"},
    {"name": "Sadaharu Aoki, Paris", "lat": 48.85, "lon": 2.32, "Country": "France", "Famous For": "Japanese-French fusion pastry, matcha eclairs", "Founded": 2001, "color": "pink"},
    {"name": "Bouley Bakery, NYC", "lat": 40.72, "lon": -74.01, "Country": "USA", "Famous For": "Fine-dining pastry tradition", "Founded": 1987, "color": "pink"},
    {"name": "Konditorei Schatz, Salzburg", "lat": 47.80, "lon": 13.04, "Country": "Austria", "Famous For": "Salzburger Nockerl, Mozart Kugeln", "Founded": 1877, "color": "pink"},
    {"name": "Zumbo Patisserie, Sydney", "lat": -33.87, "lon": 151.21, "Country": "Australia", "Famous For": "V8 Cake, Netflix Zumbo's Just Desserts", "Founded": 2007, "color": "pink"},
    {"name": "Maison Kayser, Paris", "lat": 48.85, "lon": 2.35, "Country": "France", "Famous For": "Liquid levain technique, global expansion", "Founded": 1996, "color": "pink"},
    {"name": "Cafe Demel, Vienna", "lat": 48.21, "lon": 16.37, "Country": "Austria", "Famous For": "Anna Demel torte, Kohlmarkt", "Founded": 1786, "color": "pink"},
    {"name": "Pasticceria Marchesi, Milan", "lat": 45.47, "lon": 9.19, "Country": "Italy", "Famous For": "Milanese panettone, Prada-owned", "Founded": 1824, "color": "pink"},
    {"name": "Tartine Bakery, San Francisco", "lat": 37.76, "lon": -122.42, "Country": "USA", "Famous For": "Country bread, morning buns", "Founded": 2002, "color": "pink"},
    {"name": "Tak Fung Bakery, Hong Kong", "lat": 22.28, "lon": 114.15, "Country": "China (HK)", "Famous For": "Egg tarts, traditional HK pastry", "Founded": 1940, "color": "pink"},
]

TRADE_ROUTES = [
    {"name": "Veracruz, Mexico (departure)", "lat": 19.20, "lon": -96.13, "Route": "Cacao to Spain", "Period": "1500s-1700s", "Cargo": "Raw cacao beans", "color": "cadetblue"},
    {"name": "Seville, Spain (arrival)", "lat": 37.39, "lon": -5.98, "Route": "Cacao from Americas", "Period": "1500s-1700s", "Cargo": "Cacao processing, royal court supply", "color": "cadetblue"},
    {"name": "Cadiz, Spain", "lat": 36.53, "lon": -6.29, "Route": "Atlantic cacao trade", "Period": "1600s-1800s", "Cargo": "Cacao transshipment to Europe", "color": "cadetblue"},
    {"name": "Amsterdam, Netherlands", "lat": 52.37, "lon": 4.90, "Route": "Dutch cacao trade", "Period": "1600s-1800s", "Cargo": "Van Houten processing, cocoa press invention", "color": "cadetblue"},
    {"name": "Guayaquil, Ecuador", "lat": -2.19, "lon": -79.90, "Route": "Nacional cacao export", "Period": "1700s-present", "Cargo": "Fine-flavor Arriba cacao", "color": "cadetblue"},
    {"name": "Bahia, Brazil", "lat": -12.97, "lon": -38.51, "Route": "Brazilian cacao export", "Period": "1700s-present", "Cargo": "Forastero cacao to Europe", "color": "cadetblue"},
    {"name": "Accra, Ghana (Gold Coast)", "lat": 5.56, "lon": -0.19, "Route": "West African cacao", "Period": "1870s-present", "Cargo": "Bulk cacao to UK/Europe", "color": "cadetblue"},
    {"name": "Abidjan, Ivory Coast", "lat": 5.36, "lon": -4.01, "Route": "Worlds largest cacao port", "Period": "1960s-present", "Cargo": "40% of global cacao supply", "color": "cadetblue"},
    {"name": "London, UK", "lat": 51.51, "lon": -0.08, "Route": "British chocolate trade hub", "Period": "1650s-present", "Cargo": "Cacao import, first chocolate houses 1657", "color": "cadetblue"},
    {"name": "Genoa, Italy", "lat": 44.41, "lon": 8.93, "Route": "Italian chocolate gateway", "Period": "1600s-1800s", "Cargo": "Cacao to Piedmont", "color": "cadetblue"},
    {"name": "Turin, Italy", "lat": 45.07, "lon": 7.69, "Route": "Piedmont chocolate center", "Period": "1600s-present", "Cargo": "Gianduia creation, bicerin tradition", "color": "cadetblue"},
    {"name": "Bayonne, France", "lat": 43.49, "lon": -1.47, "Route": "Sephardic chocolate route", "Period": "1600s-1800s", "Cargo": "Jewish refugees brought chocolate-making", "color": "cadetblue"},
    {"name": "Manila, Philippines", "lat": 14.60, "lon": 120.98, "Route": "Galleon trade cacao", "Period": "1565-1815", "Cargo": "Cacao via Acapulco-Manila galleons", "color": "cadetblue"},
    {"name": "Acapulco, Mexico", "lat": 16.85, "lon": -99.88, "Route": "Pacific cacao route", "Period": "1565-1815", "Cargo": "Cacao to Philippines and Asia", "color": "cadetblue"},
    {"name": "Hamburg, Germany", "lat": 53.55, "lon": 10.00, "Route": "German cacao import hub", "Period": "1700s-present", "Cargo": "Northern Europe cacao distribution", "color": "cadetblue"},
    {"name": "Lisbon, Portugal", "lat": 38.72, "lon": -9.14, "Route": "Portuguese cacao route", "Period": "1500s-1800s", "Cargo": "Sao Tome and Brazilian cacao", "color": "cadetblue"},
    {"name": "Trinidad Port of Spain", "lat": 10.65, "lon": -61.50, "Route": "Trinitario export", "Period": "1700s-present", "Cargo": "Trinitario variety after 1727 origins", "color": "cadetblue"},
    {"name": "Zanzibar, Tanzania", "lat": -6.16, "lon": 39.19, "Route": "East African spice & cacao", "Period": "1800s-present", "Cargo": "Spice trade adjunct, cacao cultivation", "color": "cadetblue"},
    {"name": "Colombo, Sri Lanka", "lat": 6.93, "lon": 79.85, "Route": "Colonial cacao plantation", "Period": "1834-present", "Cargo": "British-introduced cacao alongside tea", "color": "cadetblue"},
    {"name": "Singapore", "lat": 1.35, "lon": 103.82, "Route": "Asian cacao transshipment", "Period": "1900s-present", "Cargo": "Regional processing and distribution", "color": "cadetblue"},
    {"name": "Le Havre, France", "lat": 49.49, "lon": 0.11, "Route": "French cacao import port", "Period": "1700s-present", "Cargo": "African cacao to French factories", "color": "cadetblue"},
    {"name": "Douala, Cameroon", "lat": 4.05, "lon": 9.77, "Route": "Central African cacao export", "Period": "1880s-present", "Cargo": "Cameroonian cacao to Europe", "color": "cadetblue"},
    {"name": "Antwerp, Belgium", "lat": 51.22, "lon": 4.40, "Route": "Belgian cacao import hub", "Period": "1850s-present", "Cargo": "Cacao from Congo and global origins", "color": "cadetblue"},
    {"name": "New York, USA", "lat": 40.71, "lon": -74.01, "Route": "American cacao import gateway", "Period": "1765-present", "Cargo": "Caribbean and South American cacao", "color": "cadetblue"},
    {"name": "Bordeaux, France", "lat": 44.84, "lon": -0.58, "Route": "Atlantic cacao route", "Period": "1600s-1800s", "Cargo": "West Indies cacao, colonial trade", "color": "cadetblue"},
    {"name": "Jakarta, Indonesia", "lat": -6.21, "lon": 106.85, "Route": "Southeast Asian cacao hub", "Period": "1880s-present", "Cargo": "Sulawesi cacao export coordination", "color": "cadetblue"},
    {"name": "Makassar, Indonesia", "lat": -5.14, "lon": 119.42, "Route": "Sulawesi cacao port", "Period": "1980s-present", "Cargo": "Indonesian cacao to processors", "color": "cadetblue"},
    {"name": "Lagos, Nigeria", "lat": 6.45, "lon": 3.40, "Route": "Nigerian cacao export", "Period": "1890s-present", "Cargo": "West African cacao to global buyers", "color": "cadetblue"},
    {"name": "Santos, Brazil", "lat": -23.96, "lon": -46.33, "Route": "Brazilian cacao & coffee port", "Period": "1800s-present", "Cargo": "Bahian cacao export to Europe", "color": "cadetblue"},
    {"name": "Marseille, France", "lat": 43.30, "lon": 5.37, "Route": "Mediterranean cacao entry", "Period": "1700s-1900s", "Cargo": "Colonial cacao from Africa & Levant", "color": "cadetblue"},
]


# ---------------------------------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------------------------------

def render_chocolate_maps_tab():
    """Render the Chocolate & Confectionery Explorer tab."""
    st.markdown(
        '<div class="tab-header amber"><h4>Chocolate & Confectionery Explorer</h4>'
        '<p>Cacao origins, chocolate factories, confectionery traditions & sweet heritage</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        [
            "Cacao Growing Regions",
            "Historic Chocolate Factories",
            "Belgian Chocolate Heritage",
            "Swiss Chocolate Makers",
            "Mesoamerican Cacao Origins",
            "World Confectionery Capitals",
            "Chocolate Museums & Tours",
            "Bean-to-Bar Craft Chocolate",
            "Famous Patisseries & Bakeries",
            "Sugar & Spice Trade Routes",
        ],
        key="chocolate_maps_mode",
    )

    # -----------------------------------------------------------------
    # MODE: Cacao Growing Regions
    # -----------------------------------------------------------------
    if mode == "Cacao Growing Regions":
        data = CACAO_REGIONS
        st.markdown("### Cacao Growing Regions of the World")
        st.markdown(
            "Theobroma cacao, the tree whose seeds become chocolate, grows "
            "exclusively within the tropical band roughly 20 degrees north "
            "and south of the equator.  Three main genetic groups dominate "
            "world production: **Forastero** (bulk, ~80 percent of supply), "
            "**Criollo** (rare, fine-flavour, less than 5 percent), and "
            "**Trinitario** (a robust hybrid of both).  West Africa leads "
            "global output, but Latin America and Southeast Asia contribute "
            "critically to both volume and specialty markets."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Regions Mapped", len(data))
        c2.metric("Continents", 5)
        c3.metric("Top Producer", "Ivory Coast")
        c4.metric("Cacao Varieties", "Criollo / Forastero / Trinitario")

        st.markdown("---")
        st.markdown("##### Variety Breakdown")
        variety_counts = {}
        for d in data:
            for v in d["Type"].split("/"):
                v = v.strip()
                variety_counts[v] = variety_counts.get(v, 0) + 1
        vc1, vc2, vc3 = st.columns(3)
        vc1.metric("Forastero regions", variety_counts.get("Forastero", 0))
        vc2.metric("Trinitario regions", variety_counts.get("Trinitario", 0))
        vc3.metric("Criollo regions", variety_counts.get("Criollo", 0))

        _show_map_and_data(data, zoom=2)

    # -----------------------------------------------------------------
    # MODE: Historic Chocolate Factories
    # -----------------------------------------------------------------
    elif mode == "Historic Chocolate Factories":
        data = HISTORIC_FACTORIES
        st.markdown("### Historic Chocolate Factories")
        st.markdown(
            "From Fry's of Bristol casting the first moulded chocolate bar "
            "in 1847 to the vast Hershey works in Pennsylvania, these "
            "factories transformed cacao from an elite beverage into an "
            "affordable global treat.  Many are now heritage landmarks; "
            "others continue to produce millions of bars every day under "
            "multinational ownership."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Factories", len(data))
        oldest = min(data, key=lambda x: x["Founded"])
        c2.metric(
            "Oldest",
            f"{oldest['name'].split(',')[0]} ({oldest['Founded']})",
        )
        c3.metric("Countries", len(set(d["Country"] for d in data)))
        c4.metric(
            "Still Active",
            sum(1 for d in data if "Active" in d.get("Status", "")),
        )

        st.markdown("---")
        st.markdown("##### Country Distribution")
        country_counts = {}
        for d in data:
            country_counts[d["Country"]] = country_counts.get(d["Country"], 0) + 1
        sorted_countries = sorted(country_counts.items(), key=lambda x: -x[1])
        cc1, cc2, cc3, cc4 = st.columns(4)
        for col, (country, count) in zip(
            [cc1, cc2, cc3, cc4], sorted_countries[:4]
        ):
            col.metric(country, f"{count} factories")

        _show_map_and_data(data, zoom=3, center=[48, 5])

    # -----------------------------------------------------------------
    # MODE: Belgian Chocolate Heritage
    # -----------------------------------------------------------------
    elif mode == "Belgian Chocolate Heritage":
        data = BELGIAN_HERITAGE
        st.markdown("### Belgian Chocolate Heritage")
        st.markdown(
            "Belgium's love affair with chocolate dates to the 17th century, "
            "but it was Jean Neuhaus Jr.'s invention of the filled praline in "
            "1912 that put the country on the confectionery map forever.  "
            "Today, Brussels alone is home to over 2,000 chocolatiers, and "
            "the nation produces roughly 220,000 tonnes of chocolate per year.  "
            "From the cobblestone shops of the Grand Sablon to the industrial "
            "couverture plants of Wieze, Belgium's chocolate heritage is "
            "unmatched in density and diversity."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations", len(data))
        c2.metric("Praline Invented", "1912 (Neuhaus)")
        c3.metric("Belgian Chocolatiers", "2,000+")
        c4.metric("Annual Output", "220,000 tonnes")

        st.markdown("---")
        st.markdown("##### District Spread")
        districts = {}
        for d in data:
            dist = d.get("District", "Unknown")
            districts[dist] = districts.get(dist, 0) + 1
        dc1, dc2, dc3 = st.columns(3)
        sorted_districts = sorted(districts.items(), key=lambda x: -x[1])
        for col, (dist, cnt) in zip([dc1, dc2, dc3], sorted_districts[:3]):
            col.metric(dist, f"{cnt} locations")

        _show_map_and_data(data, zoom=8, center=[50.85, 4.35])

    # -----------------------------------------------------------------
    # MODE: Swiss Chocolate Makers
    # -----------------------------------------------------------------
    elif mode == "Swiss Chocolate Makers":
        data = SWISS_MAKERS
        st.markdown("### Swiss Chocolate Makers")
        st.markdown(
            "Switzerland may not grow a single cacao bean, yet it arguably "
            "perfected the art of turning them into chocolate.  Daniel Peter "
            "invented milk chocolate in Vevey (1875), Rodolphe Lindt "
            "developed the conching process in Bern (1879), and the country "
            "today consumes more chocolate per capita than any other nation "
            "on Earth -- roughly 10 kilograms per person per year.  Swiss "
            "chocolate exports exceed CHF 1.8 billion annually."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Makers Mapped", len(data))
        c2.metric("Oldest Brand", "Cailler (1819)")
        c3.metric("Per Capita Consumption", "~10 kg/yr")
        c4.metric("Swiss Chocolate Exports", "CHF 1.8B")

        st.markdown("---")
        st.markdown("##### Regional Clusters")
        regions = {}
        for d in data:
            r = d.get("Region", "Unknown")
            regions[r] = regions.get(r, 0) + 1
        sorted_regions = sorted(regions.items(), key=lambda x: -x[1])
        rc1, rc2, rc3, rc4 = st.columns(4)
        for col, (region, cnt) in zip(
            [rc1, rc2, rc3, rc4], sorted_regions[:4]
        ):
            col.metric(region, f"{cnt} makers")

        _show_map_and_data(data, zoom=8, center=[47.0, 8.2])

    # -----------------------------------------------------------------
    # MODE: Mesoamerican Cacao Origins
    # -----------------------------------------------------------------
    elif mode == "Mesoamerican Cacao Origins":
        data = MESOAMERICAN_ORIGINS
        st.markdown("### Mesoamerican Cacao Origins")
        st.markdown(
            "Long before European contact, the civilizations of Mesoamerica "
            "revered cacao as the food of the gods.  The Olmecs of San "
            "Lorenzo left the earliest chemical traces of cacao beverages "
            "around 1800 BCE.  By the Classic Maya period, cacao was painted "
            "on palace walls, inscribed on royal vessels, and offered in "
            "sacred cenotes.  The Aztecs used cacao beans as currency -- "
            "a single turkey cost roughly 100 beans -- and reserved the "
            "bitter, spiced xocolatl drink for warriors and nobility."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sites Mapped", len(data))
        c2.metric("Earliest Evidence", "1900 BCE")
        c3.metric("Civilizations", "Olmec / Maya / Aztec")
        c4.metric("Cacao as Currency", "Aztec era")

        st.markdown("---")
        st.markdown("##### Cultural Attribution")
        cultures = {}
        for d in data:
            for c_name in d["Culture"].split("/"):
                c_name = c_name.strip()
                cultures[c_name] = cultures.get(c_name, 0) + 1
        sorted_cultures = sorted(cultures.items(), key=lambda x: -x[1])
        cu1, cu2, cu3, cu4 = st.columns(4)
        for col, (culture, cnt) in zip(
            [cu1, cu2, cu3, cu4], sorted_cultures[:4]
        ):
            col.metric(culture, f"{cnt} sites")

        _show_map_and_data(data, zoom=6, center=[17.0, -90.0])

    # -----------------------------------------------------------------
    # MODE: World Confectionery Capitals
    # -----------------------------------------------------------------
    elif mode == "World Confectionery Capitals":
        data = CONFECTIONERY_CAPITALS
        st.markdown("### World Confectionery Capitals")
        st.markdown(
            "Certain cities have become synonymous with chocolate itself.  "
            "Brussels wears the crown of Chocolate Capital of the World, "
            "while Bruges offers the highest density of chocolate shops per "
            "square kilometre.  In Italy, Turin invented gianduiotto and "
            "Modica preserves the ancient Aztec cold-grinding method.  "
            "Beyond Europe, Tokyo leads the bean-to-bar innovation wave, "
            "and Abidjan coordinates the supply chain for over 40 percent "
            "of the planet's raw cacao."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Capitals Mapped", len(data))
        c2.metric("Top Title", "Brussels")
        c3.metric("Continents Covered", 6)
        c4.metric("Major Festivals", "Eurochocolate, Salon du Chocolat")

        st.markdown("---")
        st.markdown("##### Production Scale")
        large = sum(1 for d in data if "000" in d.get("Annual Production", ""))
        artisan = sum(1 for d in data if "Artisan" in d.get("Annual Production", "") or "Heritage" in d.get("Annual Production", ""))
        ps1, ps2, ps3 = st.columns(3)
        ps1.metric("Industrial Scale", large)
        ps2.metric("Artisan / Heritage", artisan)
        ps3.metric("Total Cities", len(data))

        _show_map_and_data(data, zoom=2)

    # -----------------------------------------------------------------
    # MODE: Chocolate Museums & Tours
    # -----------------------------------------------------------------
    elif mode == "Chocolate Museums & Tours":
        data = CHOCOLATE_MUSEUMS
        st.markdown("### Chocolate Museums & Tours")
        st.markdown(
            "From Lindt's nine-metre chocolate fountain in Kilchberg to "
            "the immersive Mayan-history experience at Choco-Story in "
            "Bruges, chocolate museums attract millions of visitors each "
            "year.  Most offer live demonstrations, tasting sessions, and "
            "hands-on workshops where guests can temper chocolate and mould "
            "their own pralines.  Several double as working factories with "
            "viewing galleries that reveal the entire bean-to-bar process."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Museums & Tours", len(data))
        unique_countries = sorted(set(d["Country"] for d in data))
        c2.metric("Countries", len(unique_countries))
        c3.metric("Tallest Choc Fountain", "9m (Lindt)")
        c4.metric("Oldest Museum", "Hershey (1973)")

        st.markdown("---")
        st.markdown("##### Top Museum Countries")
        mcountries = {}
        for d in data:
            mcountries[d["Country"]] = mcountries.get(d["Country"], 0) + 1
        sorted_mc = sorted(mcountries.items(), key=lambda x: -x[1])
        mc1, mc2, mc3, mc4 = st.columns(4)
        for col, (ctry, cnt) in zip([mc1, mc2, mc3, mc4], sorted_mc[:4]):
            col.metric(ctry, f"{cnt} venues")

        _show_map_and_data(data, zoom=2)

    # -----------------------------------------------------------------
    # MODE: Bean-to-Bar Craft Chocolate
    # -----------------------------------------------------------------
    elif mode == "Bean-to-Bar Craft Chocolate":
        data = BEAN_TO_BAR
        st.markdown("### Bean-to-Bar Craft Chocolate")
        st.markdown(
            "The craft chocolate movement exploded in the mid-2000s when "
            "small makers began sourcing raw cacao directly from farms, "
            "roasting it in converted warehouses, and hand-moulding bars "
            "with as few as two ingredients -- cacao and cane sugar.  "
            "Today the International Chocolate Awards and the Academy of "
            "Chocolate recognize hundreds of micro-producers spanning every "
            "continent.  Many emphasise single-origin transparency, paying "
            "farmers well above commodity prices and printing the farm name "
            "right on the wrapper."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Makers Mapped", len(data))
        c2.metric("Countries", len(set(d["Country"] for d in data)))
        c3.metric("Movement Since", "~2005")
        c4.metric("Award Bodies", "ICA, Academy of Chocolate")

        st.markdown("---")
        st.markdown("##### Makers by Country")
        b2b_countries = {}
        for d in data:
            b2b_countries[d["Country"]] = b2b_countries.get(d["Country"], 0) + 1
        sorted_b2b = sorted(b2b_countries.items(), key=lambda x: -x[1])
        bc1, bc2, bc3, bc4 = st.columns(4)
        for col, (ctry, cnt) in zip([bc1, bc2, bc3, bc4], sorted_b2b[:4]):
            col.metric(ctry, f"{cnt} makers")

        _show_map_and_data(data, zoom=2)

    # -----------------------------------------------------------------
    # MODE: Famous Patisseries & Bakeries
    # -----------------------------------------------------------------
    elif mode == "Famous Patisseries & Bakeries":
        data = FAMOUS_PATISSERIES
        st.markdown("### Famous Patisseries & Bakeries")
        st.markdown(
            "Where chocolate meets the art of pastry, legends are born.  "
            "Laduree popularised the macaron on the Champs-Elysees; Hotel "
            "Sacher has guarded its Sachertorte recipe since 1832; and "
            "Toraya in Tokyo has served yokan to the Imperial family for "
            "five centuries.  These establishments represent the pinnacle "
            "of confectionery craftsmanship, where butter, sugar, cream, "
            "and chocolate are transformed into ephemeral works of art."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Patisseries", len(data))
        c2.metric("Countries", len(set(d["Country"] for d in data)))
        oldest = min(data, key=lambda x: x["Founded"])
        c3.metric(
            "Oldest",
            f"{oldest['name'].split(',')[0]} ({oldest['Founded']})",
        )
        c4.metric("Macaron Capital", "Paris")

        st.markdown("---")
        st.markdown("##### Patisseries by Country")
        pat_countries = {}
        for d in data:
            pat_countries[d["Country"]] = pat_countries.get(d["Country"], 0) + 1
        sorted_pat = sorted(pat_countries.items(), key=lambda x: -x[1])
        pc1, pc2, pc3, pc4 = st.columns(4)
        for col, (ctry, cnt) in zip([pc1, pc2, pc3, pc4], sorted_pat[:4]):
            col.metric(ctry, f"{cnt} shops")

        _show_map_and_data(data, zoom=2)

    # -----------------------------------------------------------------
    # MODE: Sugar & Spice Trade Routes
    # -----------------------------------------------------------------
    elif mode == "Sugar & Spice Trade Routes":
        data = TRADE_ROUTES
        st.markdown("### Sugar & Spice Trade Routes")
        st.markdown(
            "Cacao has criss-crossed the oceans for five centuries.  Spanish "
            "galleons carried the first beans from Veracruz to Seville in "
            "the 1500s.  The Dutch, Portuguese, and British soon established "
            "their own colonial supply lines through West Africa, Brazil, "
            "and Southeast Asia.  Today, the global cacao trade exceeds five "
            "million tonnes per year, flowing from equatorial farms to "
            "processing hubs in Amsterdam, Hamburg, and Abidjan before "
            "reaching chocolate factories worldwide."
        )
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ports & Nodes", len(data))
        c2.metric("Earliest Route", "1500s (Spain)")
        c3.metric("Largest Modern Port", "Abidjan")
        c4.metric("Trade Volume Today", "~5M tonnes/yr")

        st.markdown("---")
        st.markdown("##### Trade Period Breakdown")
        colonial = sum(1 for d in data if "1500" in d.get("Period", "") or "1600" in d.get("Period", ""))
        modern = sum(1 for d in data if "present" in d.get("Period", ""))
        historical = len(data) - modern
        tp1, tp2, tp3 = st.columns(3)
        tp1.metric("Early Colonial (1500-1600s)", colonial)
        tp2.metric("Still Active", modern)
        tp3.metric("Historical Only", historical)

        _show_map_and_data(data, zoom=2)
