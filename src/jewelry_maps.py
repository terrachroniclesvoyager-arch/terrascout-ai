import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module
import pandas as pd


def render_jewelry_maps_tab():
    st.markdown(
        '<div class="tab-header amber"><h4>Jewelry & Gemstones Explorer</h4>'
        "<p>Diamond mines, gemstone origins, famous jewelers & precious stone trade routes</p></div>",
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Map Mode",
        [
            "World Diamond Mines",
            "Gemstone Mining Regions",
            "Famous Jewelry Houses",
            "Pearl Farming Locations",
            "Ancient Jewelry Archaeological Sites",
            "Gold & Silver Smithing Traditions",
            "Amber Trade Routes",
            "Jade & Nephrite Sources",
            "Crown Jewels Collections",
            "Gemstone Cutting Centers",
        ],
        key="jewelry_maps_mode",
    )

    # ------------------------------------------------------------------ #
    #  1. World Diamond Mines
    # ------------------------------------------------------------------ #
    if mode == "World Diamond Mines":
        locations = [
            {"name": "Jwaneng Mine", "lat": -24.53, "lon": 24.73, "country": "Botswana", "owner": "Debswana", "type": "Open-pit", "carats_year": "12.5 million", "opened": 1982, "notes": "Richest diamond mine in the world by value"},
            {"name": "Orapa Mine", "lat": -21.31, "lon": 25.37, "country": "Botswana", "owner": "Debswana", "type": "Open-pit", "carats_year": "10.8 million", "opened": 1971, "notes": "One of the largest open-pit mines by area"},
            {"name": "Argyle Mine", "lat": -16.71, "lon": 128.39, "country": "Australia", "owner": "Rio Tinto", "type": "Underground/Open-pit", "carats_year": "8 million (closed 2020)", "opened": 1983, "notes": "Famous for rare pink diamonds"},
            {"name": "Catoca Mine", "lat": -9.28, "lon": 20.18, "country": "Angola", "owner": "Endiama/Alrosa", "type": "Open-pit", "carats_year": "6.8 million", "opened": 1997, "notes": "Largest diamond mine in Angola"},
            {"name": "Jubilee Mine (Aikhal)", "lat": 65.95, "lon": 111.48, "country": "Russia", "owner": "Alrosa", "type": "Open-pit", "carats_year": "9.7 million", "opened": 1986, "notes": "Among Russia's top producing mines"},
            {"name": "Udachny Mine", "lat": 66.43, "lon": 112.32, "country": "Russia", "owner": "Alrosa", "type": "Underground", "carats_year": "5.5 million", "opened": 1971, "notes": "One of the deepest open-pit mines converted to underground"},
            {"name": "Mir Mine", "lat": 62.53, "lon": 113.99, "country": "Russia", "owner": "Alrosa", "type": "Underground (pit closed)", "carats_year": "2 million", "opened": 1957, "notes": "Iconic Soviet-era mine with massive pit"},
            {"name": "Venetia Mine", "lat": -22.45, "lon": 29.32, "country": "South Africa", "owner": "De Beers", "type": "Underground", "carats_year": "4.2 million", "opened": 1992, "notes": "South Africa's largest diamond mine"},
            {"name": "Cullinan Mine (Premier)", "lat": -25.40, "lon": 28.53, "country": "South Africa", "owner": "Petra Diamonds", "type": "Underground", "carats_year": "1.8 million", "opened": 1903, "notes": "Source of the Cullinan Diamond (3,106 ct)"},
            {"name": "Diavik Mine", "lat": 64.50, "lon": -110.27, "country": "Canada", "owner": "Rio Tinto", "type": "Open-pit/Underground", "carats_year": "6.2 million", "opened": 2003, "notes": "Located on an island in Lac de Gras"},
            {"name": "Ekati Mine", "lat": 64.72, "lon": -110.62, "country": "Canada", "owner": "Arctic Canadian Diamond", "type": "Open-pit/Underground", "carats_year": "4.5 million", "opened": 1998, "notes": "Canada's first surface diamond mine"},
            {"name": "Gahcho Kue Mine", "lat": 63.43, "lon": -109.19, "country": "Canada", "owner": "De Beers/Mountain Province", "type": "Open-pit", "carats_year": "5.4 million", "opened": 2016, "notes": "One of the world's largest new diamond mines"},
            {"name": "Letlhakane Mine", "lat": -21.47, "lon": 25.57, "country": "Botswana", "owner": "Debswana", "type": "Open-pit", "carats_year": "1.1 million", "opened": 1977, "notes": "Includes large tailings retreatment plant"},
            {"name": "Lulo Alluvial Mine", "lat": -9.08, "lon": 19.92, "country": "Angola", "owner": "Lucapa Diamond", "type": "Alluvial", "carats_year": "0.3 million", "opened": 2015, "notes": "Famous for exceptional large stones (400+ ct)"},
            {"name": "Karowe Mine", "lat": -21.48, "lon": 25.46, "country": "Botswana", "owner": "Lucara Diamond", "type": "Open-pit", "carats_year": "0.4 million", "opened": 2012, "notes": "Produced the 1,758 ct Sewelo diamond"},
            {"name": "Williamson Mine", "lat": -3.65, "lon": 33.65, "country": "Tanzania", "owner": "Petra Diamonds", "type": "Open-pit", "carats_year": "0.3 million", "opened": 1940, "notes": "Famous Williamson Pink diamond found here"},
            {"name": "Komsomolskaya Mine", "lat": 62.87, "lon": 113.63, "country": "Russia", "owner": "Alrosa", "type": "Open-pit", "carats_year": "3.5 million", "opened": 2000, "notes": "Important Yakutian diamond pipe"},
            {"name": "Nyurbinskaya Mine", "lat": 63.18, "lon": 118.33, "country": "Russia", "owner": "Alrosa", "type": "Open-pit", "carats_year": "4.8 million", "opened": 2003, "notes": "Rich alluvial and primary deposit"},
            {"name": "Renard Mine", "lat": 52.80, "lon": -72.20, "country": "Canada", "owner": "Stornoway Diamond", "type": "Open-pit/Underground", "carats_year": "1.6 million", "opened": 2016, "notes": "Quebec's first diamond mine"},
            {"name": "Finsch Mine", "lat": -28.38, "lon": 23.45, "country": "South Africa", "owner": "Petra Diamonds", "type": "Underground", "carats_year": "1.9 million", "opened": 1967, "notes": "Deep underground block-caving operation"},
            {"name": "Koffiefontein Mine", "lat": -29.42, "lon": 25.00, "country": "South Africa", "owner": "Petra Diamonds", "type": "Underground", "carats_year": "0.1 million", "opened": 1870, "notes": "One of South Africa's oldest diamond mines"},
            {"name": "Marange Diamond Fields", "lat": -19.85, "lon": 32.85, "country": "Zimbabwe", "owner": "ZCDC", "type": "Alluvial/Open-pit", "carats_year": "3.4 million", "opened": 2006, "notes": "Controversial large-scale alluvial deposit"},
            {"name": "Lerala Mine", "lat": -22.14, "lon": 27.78, "country": "Botswana", "owner": "Kim Knit", "type": "Open-pit", "carats_year": "0.25 million", "opened": 2017, "notes": "Small-scale kimberlite operation"},
            {"name": "Liqhobong Mine", "lat": -29.17, "lon": 28.75, "country": "Lesotho", "owner": "Firestone Diamonds", "type": "Open-pit", "carats_year": "0.9 million", "opened": 2017, "notes": "High-altitude diamond mine at 2,400m"},
            {"name": "Murowa Mine", "lat": -20.05, "lon": 30.05, "country": "Zimbabwe", "owner": "RioZim", "type": "Open-pit", "carats_year": "0.4 million", "opened": 2004, "notes": "Zimbabwe's primary kimberlite mine"},
            {"name": "Victor Mine", "lat": 52.82, "lon": -83.89, "country": "Canada", "owner": "De Beers (closed 2019)", "type": "Open-pit", "carats_year": "0.6 million", "opened": 2008, "notes": "Ontario's first diamond mine, now closed"},
            {"name": "Kollur Mine", "lat": 16.72, "lon": 80.08, "country": "India", "owner": "Historical", "type": "Alluvial (historical)", "carats_year": "Historical", "opened": 1600, "notes": "Source of the Hope Diamond and Koh-i-Noor"},
            {"name": "Panna Diamond Mine", "lat": 24.72, "lon": 80.19, "country": "India", "owner": "NMDC", "type": "Open-pit", "carats_year": "0.03 million", "opened": 1960, "notes": "India's only active diamond mine"},
            {"name": "Crater of Diamonds State Park", "lat": 34.03, "lon": -93.68, "country": "USA", "owner": "Arkansas State Parks", "type": "Open field (public)", "carats_year": "0.001 million", "opened": 1972, "notes": "Only diamond mine open to public finders-keepers"},
            {"name": "Botuobinskaya Pipe", "lat": 63.80, "lon": 118.10, "country": "Russia", "owner": "Alrosa", "type": "Underground (developing)", "carats_year": "Projected 2+ million", "opened": 2024, "notes": "Major new Russian deposit under development"},
            {"name": "Kelsey Lake Mine", "lat": 40.85, "lon": -105.85, "country": "USA", "owner": "Inactive", "type": "Open-pit (closed)", "carats_year": "Closed", "opened": 1996, "notes": "Colorado's only commercial diamond mine, yielded 28 ct stones"},
            {"name": "Bunder Diamond Project", "lat": 24.80, "lon": 78.30, "country": "India", "owner": "Rio Tinto (returned)", "type": "Undeveloped", "carats_year": "27.4 million ct resource", "opened": 0, "notes": "Massive deposit in Madhya Pradesh, environmental concerns halted"},
            {"name": "Chidliak Project", "lat": 65.20, "lon": -64.90, "country": "Canada", "owner": "De Beers", "type": "Exploration", "carats_year": "Projected significant", "opened": 0, "notes": "Baffin Island kimberlite cluster, 74 kimberlites found"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Mines", len(df))
        c2.metric("Countries", df["country"].nunique())
        c3.metric("Oldest Mine", int(df[df["opened"] > 0]["opened"].min()))
        c4.metric("Newest Mine", int(df["opened"].max()))

        m = folium.Map(location=[10, 25], zoom_start=3, tiles="CartoDB dark_matter")
        for loc in locations:
            popup_html = f"""
            <div style='min-width:220px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>Country:</b> {html_module.escape(loc['country'])}<br>
            <b>Owner:</b> {html_module.escape(loc['owner'])}<br>
            <b>Type:</b> {html_module.escape(loc['type'])}<br>
            <b>Carats/year:</b> {html_module.escape(loc['carats_year'])}<br>
            <b>Opened:</b> {loc['opened']}<br>
            <b>Notes:</b> {html_module.escape(loc['notes'])}
            </div>"""
            folium.Marker(
                [loc["lat"], loc["lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=loc["name"],
                icon=folium.Icon(color="blue", icon="diamond", prefix="fa"),
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "diamond_mines.csv", "text/csv", key="dl_diamond")

    # ------------------------------------------------------------------ #
    #  2. Gemstone Mining Regions
    # ------------------------------------------------------------------ #
    elif mode == "Gemstone Mining Regions":
        locations = [
            {"name": "Mogok Valley", "lat": 22.92, "lon": 96.50, "country": "Myanmar", "gemstones": "Ruby, Sapphire, Spinel", "fame": "World's finest pigeon-blood rubies", "status": "Active"},
            {"name": "Jegdalek", "lat": 34.35, "lon": 69.95, "country": "Afghanistan", "gemstones": "Ruby, Emerald, Lapis Lazuli", "fame": "Ancient gem source along Silk Road", "status": "Active"},
            {"name": "Panjshir Valley", "lat": 35.30, "lon": 70.20, "country": "Afghanistan", "gemstones": "Emerald", "fame": "High-quality emeralds rivaling Colombian", "status": "Active"},
            {"name": "Muzo", "lat": 5.53, "lon": -74.10, "country": "Colombia", "gemstones": "Emerald", "fame": "Finest emeralds in the world", "status": "Active"},
            {"name": "Chivor", "lat": 4.86, "lon": -73.37, "country": "Colombia", "gemstones": "Emerald", "fame": "Historic emerald mines since pre-Colombian era", "status": "Active"},
            {"name": "Coscuez", "lat": 5.56, "lon": -74.05, "country": "Colombia", "gemstones": "Emerald", "fame": "Intense green emeralds", "status": "Active"},
            {"name": "Ratnapura", "lat": 6.68, "lon": 80.40, "country": "Sri Lanka", "gemstones": "Sapphire, Ruby, Cat's Eye", "fame": "City of Gems - 40+ gem varieties", "status": "Active"},
            {"name": "Ilakaka", "lat": -22.73, "lon": 45.17, "country": "Madagascar", "gemstones": "Sapphire", "fame": "World's largest sapphire deposit", "status": "Active"},
            {"name": "Umba Valley", "lat": -4.95, "lon": 38.35, "country": "Tanzania", "gemstones": "Sapphire, Garnet, Tourmaline", "fame": "Fancy color sapphires", "status": "Active"},
            {"name": "Merelani Hills", "lat": -3.55, "lon": 37.05, "country": "Tanzania", "gemstones": "Tanzanite", "fame": "Only source of tanzanite in the world", "status": "Active"},
            {"name": "Minas Gerais", "lat": -18.50, "lon": -44.00, "country": "Brazil", "gemstones": "Tourmaline, Topaz, Aquamarine, Emerald", "fame": "Richest gem-producing state globally", "status": "Active"},
            {"name": "Paraiba State Mines", "lat": -6.85, "lon": -35.50, "country": "Brazil", "gemstones": "Paraiba Tourmaline", "fame": "Electric neon-blue tourmalines, extremely rare", "status": "Active"},
            {"name": "Opal Fields - Lightning Ridge", "lat": -29.43, "lon": 147.98, "country": "Australia", "gemstones": "Black Opal", "fame": "World's finest black opals", "status": "Active"},
            {"name": "Coober Pedy", "lat": -29.01, "lon": 134.75, "country": "Australia", "gemstones": "White/Crystal Opal", "fame": "Opal capital of the world", "status": "Active"},
            {"name": "Welo Province", "lat": 11.60, "lon": 39.60, "country": "Ethiopia", "gemstones": "Opal", "fame": "Hydrophane opals with vivid play-of-color", "status": "Active"},
            {"name": "Kagem Emerald Mine", "lat": -13.10, "lon": 28.22, "country": "Zambia", "gemstones": "Emerald", "fame": "World's single largest emerald mine", "status": "Active"},
            {"name": "Montepuez", "lat": -13.12, "lon": 39.00, "country": "Mozambique", "gemstones": "Ruby", "fame": "Major new ruby source rivaling Myanmar", "status": "Active"},
            {"name": "Tsavorite Deposits - Tsavo", "lat": -3.50, "lon": 38.60, "country": "Kenya", "gemstones": "Tsavorite Garnet", "fame": "Bright green garnets discovered 1967", "status": "Active"},
            {"name": "Swat Valley", "lat": 35.22, "lon": 72.35, "country": "Pakistan", "gemstones": "Emerald, Peridot", "fame": "Fine emeralds and world's best peridot", "status": "Active"},
            {"name": "Hunza Valley", "lat": 36.30, "lon": 74.65, "country": "Pakistan", "gemstones": "Ruby, Spinel", "fame": "High-altitude ruby deposits", "status": "Active"},
            {"name": "Bo Rai District", "lat": 12.60, "lon": 102.55, "country": "Thailand", "gemstones": "Ruby, Sapphire", "fame": "Historic Thai gem mining district", "status": "Declining"},
            {"name": "Pailin", "lat": 12.85, "lon": 102.62, "country": "Cambodia", "gemstones": "Sapphire, Ruby, Zircon", "fame": "Famous blue sapphires", "status": "Declining"},
            {"name": "San Carlos Apache Reservation", "lat": 33.35, "lon": -110.45, "country": "USA", "gemstones": "Peridot", "fame": "Major source of peridot worldwide", "status": "Active"},
            {"name": "Franklin/Sterling Hill", "lat": 41.12, "lon": -74.58, "country": "USA", "gemstones": "Fluorescent Minerals, Zincite", "fame": "Fluorescent mineral capital of the world", "status": "Museum"},
            {"name": "Luc Yen District", "lat": 22.10, "lon": 104.75, "country": "Vietnam", "gemstones": "Ruby, Sapphire, Spinel", "fame": "Fine rubies discovered in the 1980s", "status": "Active"},
            {"name": "Yogo Gulch", "lat": 47.07, "lon": -110.37, "country": "USA", "gemstones": "Sapphire", "fame": "Cornflower blue sapphires, only US deposit of gem quality", "status": "Active"},
            {"name": "Tunduru", "lat": -11.10, "lon": 37.35, "country": "Tanzania", "gemstones": "Sapphire, Chrysoberyl, Garnet", "fame": "Multi-gem alluvial deposits", "status": "Active"},
            {"name": "Winza", "lat": -6.67, "lon": 34.73, "country": "Tanzania", "gemstones": "Ruby", "fame": "Exceptional rubies discovered 2007", "status": "Active"},
            {"name": "Mahenge", "lat": -8.68, "lon": 36.72, "country": "Tanzania", "gemstones": "Spinel", "fame": "Hot-pink to red spinels of exceptional quality", "status": "Active"},
            {"name": "Tajikistan Pamir Mines", "lat": 38.50, "lon": 72.50, "country": "Tajikistan", "gemstones": "Spinel, Ruby", "fame": "Historic Balas ruby (spinel) source", "status": "Active"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Mining Regions", len(df))
        c2.metric("Countries", df["country"].nunique())
        active = len(df[df["status"] == "Active"])
        c3.metric("Active Regions", active)
        unique_gems = set()
        for g in df["gemstones"]:
            for gem in g.split(", "):
                unique_gems.add(gem.strip())
        c4.metric("Gemstone Types", len(unique_gems))

        m = folium.Map(location=[10, 60], zoom_start=3, tiles="CartoDB dark_matter")
        color_map = {"Active": "green", "Declining": "orange", "Museum": "gray"}
        for loc in locations:
            popup_html = f"""
            <div style='min-width:220px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>Country:</b> {html_module.escape(loc['country'])}<br>
            <b>Gemstones:</b> {html_module.escape(loc['gemstones'])}<br>
            <b>Fame:</b> {html_module.escape(loc['fame'])}<br>
            <b>Status:</b> {html_module.escape(loc['status'])}
            </div>"""
            folium.Marker(
                [loc["lat"], loc["lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=loc["name"],
                icon=folium.Icon(color=color_map.get(loc["status"], "blue"), icon="gem", prefix="fa"),
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "gemstone_regions.csv", "text/csv", key="dl_gems")

    # ------------------------------------------------------------------ #
    #  3. Famous Jewelry Houses
    # ------------------------------------------------------------------ #
    elif mode == "Famous Jewelry Houses":
        locations = [
            {"name": "Cartier - Paris HQ", "lat": 48.8686, "lon": 2.3291, "city": "Paris", "country": "France", "founded": 1847, "specialty": "High jewelry, watches, Love bracelet", "famous_piece": "Tutti Frutti necklaces"},
            {"name": "Tiffany & Co. - Fifth Ave", "lat": 40.7635, "lon": -73.9735, "city": "New York", "country": "USA", "founded": 1837, "specialty": "Diamonds, engagement rings, silver", "famous_piece": "Tiffany Yellow Diamond (128.54 ct)"},
            {"name": "Bulgari - Via dei Condotti", "lat": 41.9057, "lon": 12.4805, "city": "Rome", "country": "Italy", "founded": 1884, "specialty": "Colored gemstones, Serpenti collection", "famous_piece": "Elizabeth Taylor emerald suite"},
            {"name": "Van Cleef & Arpels - Place Vendome", "lat": 48.8675, "lon": 2.3296, "city": "Paris", "country": "France", "founded": 1906, "specialty": "Mystery Setting, Alhambra motif", "famous_piece": "Zip necklace transformable to bracelet"},
            {"name": "Harry Winston - Fifth Ave", "lat": 40.7641, "lon": -73.9724, "city": "New York", "country": "USA", "founded": 1932, "specialty": "Exceptional diamonds, high jewelry", "famous_piece": "Hope Diamond (donated to Smithsonian)"},
            {"name": "Chopard - Geneva", "lat": 46.1922, "lon": 6.1310, "city": "Geneva", "country": "Switzerland", "founded": 1860, "specialty": "Happy Diamonds, ethical gold", "famous_piece": "Palme d'Or trophy for Cannes"},
            {"name": "Graff Diamonds - London", "lat": 51.5074, "lon": -0.1443, "city": "London", "country": "UK", "founded": 1960, "specialty": "Rare diamonds, record auction stones", "famous_piece": "Graff Pink Diamond (24.78 ct)"},
            {"name": "Piaget - Geneva", "lat": 46.2012, "lon": 6.1425, "city": "Geneva", "country": "Switzerland", "founded": 1874, "specialty": "Ultra-thin watches, gold jewelry", "famous_piece": "Possession turning ring"},
            {"name": "Buccellati - Milan", "lat": 45.4654, "lon": 9.1892, "city": "Milan", "country": "Italy", "founded": 1919, "specialty": "Renaissance-inspired goldsmithing", "famous_piece": "Textured gold cuff bracelets"},
            {"name": "Mikimoto - Tokyo Ginza", "lat": 35.6717, "lon": 139.7650, "city": "Tokyo", "country": "Japan", "founded": 1893, "specialty": "Cultured pearls", "famous_piece": "First cultured pearl (1893)"},
            {"name": "Chaumet - Place Vendome", "lat": 48.8680, "lon": 2.3290, "city": "Paris", "country": "France", "founded": 1780, "specialty": "Tiaras, bridal jewelry", "famous_piece": "Napoleon's coronation sword"},
            {"name": "Boucheron - Place Vendome", "lat": 48.8682, "lon": 2.3294, "city": "Paris", "country": "France", "founded": 1858, "specialty": "Nature-inspired high jewelry", "famous_piece": "Serpent Boheme collection"},
            {"name": "De Beers Jewellers - London", "lat": 51.5098, "lon": -0.1450, "city": "London", "country": "UK", "founded": 1888, "specialty": "Diamond solitaires, bridal", "famous_piece": "Millennium Star (203 ct)"},
            {"name": "Pomellato - Milan", "lat": 45.4680, "lon": 9.1920, "city": "Milan", "country": "Italy", "founded": 1967, "specialty": "Colored gemstone prêt-à-porter jewelry", "famous_piece": "Nudo ring collection"},
            {"name": "David Yurman - New York", "lat": 40.7614, "lon": -73.9738, "city": "New York", "country": "USA", "founded": 1980, "specialty": "Cable motif, mixed metals", "famous_piece": "Cable Classics bracelet"},
            {"name": "Faberge - London", "lat": 51.5090, "lon": -0.1400, "city": "London", "country": "UK", "founded": 1842, "specialty": "Enameling, Imperial eggs", "famous_piece": "Imperial Easter Eggs for Russian Tsars"},
            {"name": "Messika - Paris", "lat": 48.8700, "lon": 2.3070, "city": "Paris", "country": "France", "founded": 2005, "specialty": "Diamond-centric modern designs", "famous_piece": "Move collection"},
            {"name": "Paspaley - Darwin", "lat": -12.4634, "lon": 130.8456, "city": "Darwin", "country": "Australia", "founded": 1935, "specialty": "South Sea pearls", "famous_piece": "World's finest South Sea pearl jewelry"},
            {"name": "Chow Tai Fook - Hong Kong", "lat": 22.2815, "lon": 114.1580, "city": "Hong Kong", "country": "China", "founded": 1929, "specialty": "Gold, diamond, jade jewelry", "famous_piece": "CTF Pink Star Diamond (59.60 ct)"},
            {"name": "Tanishq - Bangalore", "lat": 12.9716, "lon": 77.5946, "city": "Bangalore", "country": "India", "founded": 1994, "specialty": "Gold and diamond Indian jewelry", "famous_piece": "Padmavati collection"},
            {"name": "Hemmerle - Munich", "lat": 48.1351, "lon": 11.5820, "city": "Munich", "country": "Germany", "founded": 1893, "specialty": "Avant-garde, mixed materials", "famous_piece": "Harmony bangle in iron and gold"},
            {"name": "JAR (Joel Arthur Rosenthal) - Paris", "lat": 48.8657, "lon": 2.3289, "city": "Paris", "country": "France", "founded": 1978, "specialty": "Ultra-exclusive one-of-a-kind pieces", "famous_piece": "Camellia brooch (record auction price)"},
            {"name": "Nirav Modi - Mumbai", "lat": 19.0760, "lon": 72.8777, "city": "Mumbai", "country": "India", "founded": 2010, "specialty": "Jasmine collection, embrace bangles", "famous_piece": "Golconda Lotus necklace"},
            {"name": "Roberto Coin - Vicenza", "lat": 45.5455, "lon": 11.5354, "city": "Vicenza", "country": "Italy", "founded": 1977, "specialty": "Hidden ruby signature, Italian gold", "famous_piece": "Princess collection"},
            {"name": "Wellendorff - Pforzheim", "lat": 48.8922, "lon": 8.6944, "city": "Pforzheim", "country": "Germany", "founded": 1893, "specialty": "Spinning rings, cold enamel", "famous_piece": "Genuine Delight spinning ring"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Jewelry Houses", len(df))
        c2.metric("Countries", df["country"].nunique())
        c3.metric("Oldest Founded", int(df["founded"].min()))
        c4.metric("Newest Founded", int(df["founded"].max()))

        m = folium.Map(location=[35, 10], zoom_start=3, tiles="CartoDB dark_matter")
        for loc in locations:
            popup_html = f"""
            <div style='min-width:240px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>City:</b> {html_module.escape(loc['city'])}, {html_module.escape(loc['country'])}<br>
            <b>Founded:</b> {loc['founded']}<br>
            <b>Specialty:</b> {html_module.escape(loc['specialty'])}<br>
            <b>Famous Piece:</b> {html_module.escape(loc['famous_piece'])}
            </div>"""
            folium.Marker(
                [loc["lat"], loc["lon"]],
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=loc["name"],
                icon=folium.Icon(color="purple", icon="crown", prefix="fa"),
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "jewelry_houses.csv", "text/csv", key="dl_houses")

    # ------------------------------------------------------------------ #
    #  4. Pearl Farming Locations
    # ------------------------------------------------------------------ #
    elif mode == "Pearl Farming Locations":
        locations = [
            {"name": "Mikimoto Pearl Island", "lat": 34.48, "lon": 136.85, "country": "Japan", "pearl_type": "Akoya", "species": "Pinctada fucata", "notes": "Birthplace of cultured pearl industry"},
            {"name": "Ago Bay Farms", "lat": 34.30, "lon": 136.82, "country": "Japan", "pearl_type": "Akoya", "species": "Pinctada fucata", "notes": "Traditional Japanese pearl farming center"},
            {"name": "Uwajima Pearl Farms", "lat": 33.22, "lon": 132.56, "country": "Japan", "pearl_type": "Akoya", "species": "Pinctada fucata", "notes": "Major Akoya production region"},
            {"name": "Broome - Cygnet Bay", "lat": -16.80, "lon": 122.22, "country": "Australia", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Australia's oldest pearl farm"},
            {"name": "Kuri Bay", "lat": -15.48, "lon": 124.54, "country": "Australia", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Remote pearl farm, among world's finest"},
            {"name": "Eighty Mile Beach", "lat": -19.40, "lon": 121.30, "country": "Australia", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Historic pearling ground since 1860s"},
            {"name": "Lombok Pearl Farms", "lat": -8.65, "lon": 116.35, "country": "Indonesia", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Golden and white South Sea pearls"},
            {"name": "Sumbawa Pearl Farms", "lat": -8.50, "lon": 117.50, "country": "Indonesia", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Large-scale Indonesian pearl cultivation"},
            {"name": "Palawan Pearl Farms", "lat": 10.20, "lon": 118.75, "country": "Philippines", "pearl_type": "South Sea Golden", "species": "Pinctada maxima", "notes": "Famous for golden South Sea pearls"},
            {"name": "Davao Pearl Farm", "lat": 7.07, "lon": 125.61, "country": "Philippines", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Luxury resort with pearl farm tours"},
            {"name": "Tuamotu Archipelago", "lat": -16.50, "lon": -145.50, "country": "French Polynesia", "pearl_type": "Tahitian Black", "species": "Pinctada margaritifera", "notes": "Heart of Tahitian pearl production"},
            {"name": "Gambier Islands - Mangareva", "lat": -23.10, "lon": -134.97, "country": "French Polynesia", "pearl_type": "Tahitian Black", "species": "Pinctada margaritifera", "notes": "Premium Tahitian pearl quality"},
            {"name": "Fakarava Atoll", "lat": -16.30, "lon": -145.65, "country": "French Polynesia", "pearl_type": "Tahitian Black", "species": "Pinctada margaritifera", "notes": "UNESCO biosphere with pearl farms"},
            {"name": "Rangiroa Atoll", "lat": -15.13, "lon": -147.65, "country": "French Polynesia", "pearl_type": "Tahitian Black", "species": "Pinctada margaritifera", "notes": "Second largest atoll in the world, major pearl farms"},
            {"name": "Beihai Pearl Farms", "lat": 21.48, "lon": 109.12, "country": "China", "pearl_type": "Freshwater / Akoya", "species": "Hyriopsis cumingii / P. fucata", "notes": "Historic South China Sea pearl center"},
            {"name": "Zhuji Pearl Market", "lat": 29.72, "lon": 120.24, "country": "China", "pearl_type": "Freshwater", "species": "Hyriopsis cumingii", "notes": "World's largest freshwater pearl trading center"},
            {"name": "Lake Biwa (Historical)", "lat": 35.25, "lon": 136.10, "country": "Japan", "pearl_type": "Freshwater (historical)", "species": "Hyriopsis schlegelii", "notes": "First freshwater pearl cultivation, now largely depleted"},
            {"name": "Halong Bay Pearl Farm", "lat": 20.95, "lon": 107.10, "country": "Vietnam", "pearl_type": "Akoya / South Sea", "species": "Pinctada fucata / maxima", "notes": "Growing Vietnamese pearl industry"},
            {"name": "Phu Quoc Pearl Farm", "lat": 10.22, "lon": 103.96, "country": "Vietnam", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Japanese-Vietnamese joint venture"},
            {"name": "Arafura Sea Farms", "lat": -9.50, "lon": 135.00, "country": "Indonesia", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Remote eastern Indonesian pearl grounds"},
            {"name": "Myanmar Pearl Farms - Myeik", "lat": 12.44, "lon": 98.60, "country": "Myanmar", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Mergui Archipelago pearl cultivation"},
            {"name": "Cook Islands Pearl Farms", "lat": -21.24, "lon": -159.78, "country": "Cook Islands", "pearl_type": "Black-lip", "species": "Pinctada margaritifera", "notes": "Small-scale premium pearl farming"},
            {"name": "Ras Al Khaimah Pearl Farm", "lat": 25.79, "lon": 55.95, "country": "UAE", "pearl_type": "Natural / Cultured", "species": "Pinctada radiata", "notes": "Revival of Arabian Gulf pearling heritage"},
            {"name": "Bahrain Pearl Beds", "lat": 26.07, "lon": 50.55, "country": "Bahrain", "pearl_type": "Natural", "species": "Pinctada radiata", "notes": "UNESCO World Heritage natural pearl beds"},
            {"name": "Tennessee River Mussel Farms", "lat": 35.05, "lon": -87.95, "country": "USA", "pearl_type": "Freshwater nuclei", "species": "Various Unionidae", "notes": "Supplies bead nuclei for cultured pearl industry worldwide"},
            {"name": "Toba Akoya Farms", "lat": 34.48, "lon": 136.84, "country": "Japan", "pearl_type": "Akoya", "species": "Pinctada fucata", "notes": "Toba city pearl museum and active farming"},
            {"name": "Fiji Pearl Farm - Savusavu", "lat": -16.77, "lon": 179.34, "country": "Fiji", "pearl_type": "Golden-lip", "species": "Pinctada margaritifera", "notes": "J. Hunter Pearls - rare Fijian black pearls"},
            {"name": "Abrolhos Islands Pearl", "lat": -28.72, "lon": 113.77, "country": "Australia", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Western Australian pearling grounds"},
            {"name": "Penang Pearl Farm", "lat": 5.28, "lon": 100.20, "country": "Malaysia", "pearl_type": "South Sea", "species": "Pinctada maxima", "notes": "Malaysian pearl cultivation and tourism"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pearl Farms", len(df))
        c2.metric("Countries", df["country"].nunique())
        c3.metric("Pearl Types", df["pearl_type"].nunique())
        c4.metric("Species", df["species"].nunique())

        m = folium.Map(location=[5, 120], zoom_start=3, tiles="CartoDB dark_matter")
        type_colors = {"Akoya": "white", "South Sea": "beige", "Tahitian Black": "black", "Freshwater": "lightblue"}
        for loc in locations:
            popup_html = f"""
            <div style='min-width:220px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>Country:</b> {html_module.escape(loc['country'])}<br>
            <b>Pearl Type:</b> {html_module.escape(loc['pearl_type'])}<br>
            <b>Species:</b> <i>{html_module.escape(loc['species'])}</i><br>
            <b>Notes:</b> {html_module.escape(loc['notes'])}
            </div>"""
            folium.CircleMarker(
                [loc["lat"], loc["lon"]],
                radius=8,
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=loc["name"],
                color="white",
                fill=True,
                fill_color="#e0d5c0",
                fill_opacity=0.8,
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "pearl_farms.csv", "text/csv", key="dl_pearls")

    # ------------------------------------------------------------------ #
    #  5. Ancient Jewelry Archaeological Sites
    # ------------------------------------------------------------------ #
    elif mode == "Ancient Jewelry Archaeological Sites":
        locations = [
            {"name": "Tomb of Tutankhamun", "lat": 25.74, "lon": 32.60, "country": "Egypt", "period": "c. 1323 BCE", "civilization": "Ancient Egypt", "finds": "Gold death mask, pectorals, rings, amulets", "significance": "Most complete ancient royal jewelry collection"},
            {"name": "Royal Tombs of Ur", "lat": 30.96, "lon": 46.10, "country": "Iraq", "period": "c. 2600 BCE", "civilization": "Sumerian", "finds": "Gold headdresses, lapis lazuli jewelry, carnelian beads", "significance": "Earliest known complex gold jewelry"},
            {"name": "Varna Necropolis", "lat": 43.22, "lon": 27.91, "country": "Bulgaria", "period": "c. 4600 BCE", "civilization": "Varna Culture", "finds": "Oldest processed gold in the world (6kg+)", "significance": "World's oldest gold artifacts"},
            {"name": "Mycenae - Shaft Graves", "lat": 37.73, "lon": 22.76, "country": "Greece", "period": "c. 1600 BCE", "civilization": "Mycenaean", "finds": "Mask of Agamemnon, gold cups, diadems", "significance": "Richest Bronze Age Greek burial finds"},
            {"name": "Mohenjo-daro", "lat": 27.33, "lon": 68.14, "country": "Pakistan", "period": "c. 2500 BCE", "civilization": "Indus Valley", "finds": "Gold and carnelian beads, bronze Dancing Girl", "significance": "Advanced bead-making and metallurgy"},
            {"name": "Tillya Tepe (Golden Hill)", "lat": 36.67, "lon": 66.07, "country": "Afghanistan", "period": "c. 100 BCE", "civilization": "Kushan/Bactrian", "finds": "20,000+ gold ornaments, turquoise inlays", "significance": "Bactrian Hoard - finest Central Asian goldwork"},
            {"name": "Sutton Hoo", "lat": 52.09, "lon": 1.34, "country": "UK", "period": "c. 625 CE", "civilization": "Anglo-Saxon", "finds": "Gold and garnet shoulder clasps, helmet, buckle", "significance": "Greatest Anglo-Saxon treasure find"},
            {"name": "Staffordshire Hoard Site", "lat": 52.66, "lon": -1.93, "country": "UK", "period": "c. 650 CE", "civilization": "Anglo-Saxon", "finds": "5kg gold, 1.4kg silver, garnet fittings", "significance": "Largest Anglo-Saxon gold hoard ever found"},
            {"name": "Sipan - Lord of Sipan Tomb", "lat": -6.80, "lon": -79.60, "country": "Peru", "period": "c. 250 CE", "civilization": "Moche", "finds": "Gold and turquoise ear ornaments, pectorals, headdresses", "significance": "Richest unlooted tomb in the Americas"},
            {"name": "Monte Alban - Tomb 7", "lat": 17.04, "lon": -96.77, "country": "Mexico", "period": "c. 1350 CE", "civilization": "Mixtec", "finds": "Gold pectorals, jade, turquoise mosaics, crystal cups", "significance": "Finest Mixtec goldwork collection"},
            {"name": "Vergina Royal Tombs", "lat": 40.49, "lon": 22.31, "country": "Greece", "period": "c. 336 BCE", "civilization": "Macedonian", "finds": "Gold larnax, diadem, wreaths of Philip II", "significance": "Tomb of Alexander the Great's father"},
            {"name": "Pompeii", "lat": 40.75, "lon": 14.49, "country": "Italy", "period": "79 CE", "civilization": "Roman", "finds": "Gold earrings, emerald rings, snake bracelets", "significance": "Snapshot of Roman jewelry in daily life"},
            {"name": "Hoxne Hoard Site", "lat": 52.35, "lon": 1.19, "country": "UK", "period": "c. 400 CE", "civilization": "Late Roman", "finds": "Gold body chain, pepper pot, 569 gold coins", "significance": "Largest late-Roman gold/silver hoard in Britain"},
            {"name": "Taxila", "lat": 33.78, "lon": 72.83, "country": "Pakistan", "period": "c. 500 BCE - 500 CE", "civilization": "Gandharan", "finds": "Gold Greco-Buddhist jewelry, gemstone beads", "significance": "Crossroads of Hellenistic and South Asian jewelry"},
            {"name": "Nimrud (Kalhu) Palace", "lat": 36.10, "lon": 43.33, "country": "Iraq", "period": "c. 800 BCE", "civilization": "Assyrian", "finds": "Queens' gold crowns, necklaces, earrings (Nimrud Treasure)", "significance": "Finest Neo-Assyrian royal jewelry"},
            {"name": "Troy - Priams Treasure", "lat": 39.96, "lon": 26.24, "country": "Turkey", "period": "c. 2400 BCE", "civilization": "Early Bronze Age Anatolian", "finds": "Gold diadems, earrings, bracelets, 8,700 rings", "significance": "Schliemann's legendary treasure find"},
            {"name": "Sanxingdui", "lat": 31.00, "lon": 104.20, "country": "China", "period": "c. 1200 BCE", "civilization": "Shu Kingdom", "finds": "Gold masks, gold-foil-covered staffs, jade ornaments", "significance": "Mysterious civilization with unique gold artifacts"},
            {"name": "Maikop Kurgan", "lat": 44.60, "lon": 40.10, "country": "Russia", "period": "c. 3500 BCE", "civilization": "Maikop Culture", "finds": "Gold and silver vessels, turquoise beads, bull figurines", "significance": "Earliest gold artifacts from the Caucasus"},
            {"name": "Siphnian Treasury - Delphi", "lat": 38.48, "lon": 22.50, "country": "Greece", "period": "c. 530 BCE", "civilization": "Classical Greek", "finds": "Gold and silver votive jewelry offerings", "significance": "Evidence of Siphnos gold/silver mining wealth"},
            {"name": "Ban Chiang", "lat": 17.41, "lon": 103.25, "country": "Thailand", "period": "c. 2100 BCE", "civilization": "Ban Chiang Culture", "finds": "Bronze bracelets, glass beads, ceramic jewelry", "significance": "Earliest Southeast Asian metallurgy site"},
            {"name": "Eberswalde Hoard Site", "lat": 52.83, "lon": 13.82, "country": "Germany", "period": "c. 1000 BCE", "civilization": "Bronze Age Germanic", "finds": "81 gold objects totaling 2.59 kg", "significance": "Largest prehistoric gold hoard in Germany"},
            {"name": "Nahal Qanah Cave", "lat": 32.18, "lon": 35.05, "country": "Israel", "period": "c. 4500 BCE", "civilization": "Chalcolithic", "finds": "Gold rings - among oldest gold objects in Levant", "significance": "Earliest gold jewelry in the Near East"},
            {"name": "Amlash Region", "lat": 37.15, "lon": 50.18, "country": "Iran", "period": "c. 1000 BCE", "civilization": "Iron Age Iranian", "finds": "Gold cups, animal-form jewelry, electrum ornaments", "significance": "Exquisite animal-style goldwork"},
            {"name": "Bactria-Margiana Sites", "lat": 38.00, "lon": 62.00, "country": "Turkmenistan", "period": "c. 2200 BCE", "civilization": "BMAC", "finds": "Gold and silver pins, seals, compartmented amulets", "significance": "Bronze Age Central Asian jewelry traditions"},
            {"name": "Kerch Kurgans (Panticapaeum)", "lat": 45.35, "lon": 36.47, "country": "Ukraine/Russia", "period": "c. 400 BCE", "civilization": "Scythian-Greek", "finds": "Gold pectorals, torcs, animal-style plaques", "significance": "Supreme examples of Scythian gold artistry"},
            {"name": "Heuneburg Celtic Hillfort", "lat": 48.09, "lon": 9.42, "country": "Germany", "period": "c. 600 BCE", "civilization": "Celtic Hallstatt", "finds": "Gold neck rings, fibulae, amber beads", "significance": "Earliest evidence of Celtic elite gold jewelry"},
            {"name": "Hochdorf Chieftain Burial", "lat": 48.84, "lon": 9.12, "country": "Germany", "period": "c. 530 BCE", "civilization": "Celtic", "finds": "Gold shoes, gold-plated torc, gold dagger", "significance": "Complete Celtic chieftain's gold burial goods"},
            {"name": "Alaca Hoyuk Royal Tombs", "lat": 40.23, "lon": 36.40, "country": "Turkey", "period": "c. 2500 BCE", "civilization": "Hattian", "finds": "Gold diadems, sun discs, gold bull figurines", "significance": "Pre-Hittite Anatolian royal goldwork"},
            {"name": "Byblos Royal Tombs", "lat": 34.12, "lon": 35.65, "country": "Lebanon", "period": "c. 1800 BCE", "civilization": "Phoenician", "finds": "Gold falcon pectoral, obsidian box with gold", "significance": "Finest Phoenician gold artifacts known"},
            {"name": "Dilbat/Tell ed-Duleim", "lat": 32.40, "lon": 44.40, "country": "Iraq", "period": "c. 2000 BCE", "civilization": "Old Babylonian", "finds": "Gold earrings, lapis and carnelian necklaces", "significance": "Middle Babylonian jewelry styles"},
            {"name": "Chimu Chan Chan", "lat": -8.10, "lon": -79.07, "country": "Peru", "period": "c. 1100 CE", "civilization": "Chimu", "finds": "Gold ear spools, nose ornaments, tumi knives", "significance": "Largest Pre-Columbian city with extensive goldwork"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Archaeological Sites", len(df))
        c2.metric("Countries", df["country"].nunique())
        c3.metric("Civilizations", df["civilization"].nunique())
        c4.metric("Oldest Find", df["period"].iloc[2])

        m = folium.Map(location=[30, 40], zoom_start=3, tiles="CartoDB dark_matter")
        for loc in locations:
            popup_html = f"""
            <div style='min-width:250px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>Country:</b> {html_module.escape(loc['country'])}<br>
            <b>Period:</b> {html_module.escape(loc['period'])}<br>
            <b>Civilization:</b> {html_module.escape(loc['civilization'])}<br>
            <b>Finds:</b> {html_module.escape(loc['finds'])}<br>
            <b>Significance:</b> {html_module.escape(loc['significance'])}
            </div>"""
            folium.Marker(
                [loc["lat"], loc["lon"]],
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=loc["name"],
                icon=folium.Icon(color="orange", icon="university", prefix="fa"),
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "ancient_jewelry_sites.csv", "text/csv", key="jwlm_dl_ancient")

    # ------------------------------------------------------------------ #
    #  6. Gold & Silver Smithing Traditions
    # ------------------------------------------------------------------ #
    elif mode == "Gold & Silver Smithing Traditions":
        locations = [
            {"name": "Jaipur - Kundan & Meenakari", "lat": 26.91, "lon": 75.79, "country": "India", "tradition": "Kundan, Meenakari, Thewa", "period": "16th century onward", "specialty": "Stone setting with gold foil, enamel work", "status": "Living tradition"},
            {"name": "Taxco - Silver Capital", "lat": 18.56, "lon": -99.60, "country": "Mexico", "tradition": "Mexican Silversmithing", "period": "Pre-Columbian + 1930s revival", "specialty": "Bold silver designs, obsidian inlay", "status": "Living tradition"},
            {"name": "Pforzheim - Gold City", "lat": 48.89, "lon": 8.70, "country": "Germany", "tradition": "German precision goldsmithing", "period": "1767 onward", "specialty": "Technical excellence, jewelry manufacturing", "status": "Living tradition"},
            {"name": "Birmingham Jewellery Quarter", "lat": 52.49, "lon": -1.91, "country": "UK", "tradition": "English silversmithing & jewelry", "period": "1700s onward", "specialty": "Hallmarking, mass production, fine silver", "status": "Living tradition"},
            {"name": "Istanbul Grand Bazaar", "lat": 41.01, "lon": 28.97, "country": "Turkey", "tradition": "Ottoman goldsmithing", "period": "15th century onward", "specialty": "Filigree, granulation, enamel, tugra motifs", "status": "Living tradition"},
            {"name": "Arezzo", "lat": 43.46, "lon": 11.88, "country": "Italy", "tradition": "Etruscan-inspired Italian goldsmithing", "period": "Ancient + modern industrial", "specialty": "Gold chain manufacturing, electroforming", "status": "Living tradition"},
            {"name": "Valenza Po", "lat": 45.01, "lon": 8.64, "country": "Italy", "tradition": "High jewelry craftsmanship", "period": "19th century onward", "specialty": "Gem-set high jewelry, artisan workshops", "status": "Living tradition"},
            {"name": "Vicenza", "lat": 45.55, "lon": 11.54, "country": "Italy", "tradition": "Italian gold jewelry", "period": "Medieval onward", "specialty": "Gold manufacturing hub, VicenzaOro trade fair", "status": "Living tradition"},
            {"name": "Chiang Mai Silver District", "lat": 18.79, "lon": 98.98, "country": "Thailand", "tradition": "Lanna silverwork", "period": "13th century onward", "specialty": "Repousse bowls, hill-tribe silver jewelry", "status": "Living tradition"},
            {"name": "Fez Medina - Metalworkers Souk", "lat": 34.06, "lon": -4.97, "country": "Morocco", "tradition": "Amazigh & Andalusian metalwork", "period": "8th century onward", "specialty": "Filigree, niello, enamel, Berber jewelry", "status": "Living tradition"},
            {"name": "Cusco - Inca Gold Heritage", "lat": -13.52, "lon": -71.97, "country": "Peru", "tradition": "Andean goldsmithing", "period": "Pre-Inca to present", "specialty": "Lost-wax casting, repoussé, tumbaga alloy", "status": "Living tradition"},
            {"name": "Oaxaca - Filigree Workshops", "lat": 17.06, "lon": -96.73, "country": "Mexico", "tradition": "Zapotec filigree", "period": "Pre-Columbian roots", "specialty": "Gold and silver filigree, Mixtec reproductions", "status": "Living tradition"},
            {"name": "Dubrovnik Gold Street", "lat": 42.64, "lon": 18.11, "country": "Croatia", "tradition": "Dalmatian filigree", "period": "Medieval", "specialty": "Dubrovnik button earrings, filigree pendants", "status": "Living tradition"},
            {"name": "Yerevan Goldsmithing Quarter", "lat": 40.18, "lon": 44.51, "country": "Armenia", "tradition": "Armenian metalwork", "period": "Ancient Urartu onward", "specialty": "Pomegranate motifs, religious jewelry, obsidian", "status": "Living tradition"},
            {"name": "Bukhara - Silk Road Smiths", "lat": 39.77, "lon": 64.42, "country": "Uzbekistan", "tradition": "Central Asian zargarlik", "period": "Ancient Silk Road", "specialty": "Turquoise-set silver, wedding jewelry", "status": "Reviving"},
            {"name": "Bali - Silver Village Celuk", "lat": -8.60, "lon": 115.29, "country": "Indonesia", "tradition": "Balinese silverwork", "period": "Ancient Hindu tradition", "specialty": "Granulation, filigree, ritual jewelry", "status": "Living tradition"},
            {"name": "Lalibela - Ethiopian Cross Makers", "lat": 12.03, "lon": 39.04, "country": "Ethiopia", "tradition": "Ethiopian cross jewelry", "period": "4th century onward", "specialty": "Coptic cross pendants, lost-wax silver casting", "status": "Living tradition"},
            {"name": "Navajo Nation - Silversmithing", "lat": 36.10, "lon": -109.19, "country": "USA", "tradition": "Navajo/Dine silverwork", "period": "1860s onward", "specialty": "Turquoise & silver, squash blossom necklaces", "status": "Living tradition"},
            {"name": "Kanazawa Gold Leaf", "lat": 36.56, "lon": 136.66, "country": "Japan", "tradition": "Kinpaku (gold leaf)", "period": "16th century", "specialty": "99% of Japan's gold leaf, lacquerware", "status": "Living tradition"},
            {"name": "San Miguel de Allende", "lat": 20.91, "lon": -100.74, "country": "Mexico", "tradition": "Brass & silver artisan craft", "period": "Colonial era", "specialty": "Tin and silver decorative jewelry", "status": "Living tradition"},
            {"name": "Sana'a Old City - Silver Souq", "lat": 15.35, "lon": 44.21, "country": "Yemen", "tradition": "Yemeni Jewish & Arab silverwork", "period": "Ancient", "specialty": "Filigree amulets, bridal silver, coral & amber", "status": "Endangered"},
            {"name": "Shkoder - Albanian Filigree", "lat": 42.07, "lon": 19.51, "country": "Albania", "tradition": "Albanian filigree (telkari)", "period": "Ottoman era", "specialty": "Silver filigree buttons, brooches, xhubleta ornaments", "status": "Reviving"},
            {"name": "Toledo - Damascene", "lat": 39.86, "lon": -4.02, "country": "Spain", "tradition": "Damascening (damasquinado)", "period": "Moorish era", "specialty": "Gold inlay on blackened steel", "status": "Living tradition"},
            {"name": "Thrissur - Kerala Goldsmithing", "lat": 10.52, "lon": 76.21, "country": "India", "tradition": "Kerala temple jewelry", "period": "Ancient", "specialty": "Nagapadathali, Palakka mala, temple gold", "status": "Living tradition"},
            {"name": "Dongyang - Chinese Filigree", "lat": 29.27, "lon": 120.22, "country": "China", "tradition": "Hua Si (gold/silver filigree)", "period": "Han Dynasty onward", "specialty": "Micro-filigree, cloisonne, kingfisher feather inlay", "status": "Living tradition"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Smithing Centers", len(df))
        c2.metric("Countries", df["country"].nunique())
        living = len(df[df["status"] == "Living tradition"])
        c3.metric("Living Traditions", living)
        c4.metric("Traditions", df["tradition"].nunique())

        m = folium.Map(location=[25, 40], zoom_start=3, tiles="CartoDB dark_matter")
        status_colors = {"Living tradition": "gold", "Reviving": "lightgreen", "Endangered": "red"}
        for loc in locations:
            popup_html = f"""
            <div style='min-width:240px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>Country:</b> {html_module.escape(loc['country'])}<br>
            <b>Tradition:</b> {html_module.escape(loc['tradition'])}<br>
            <b>Period:</b> {html_module.escape(loc['period'])}<br>
            <b>Specialty:</b> {html_module.escape(loc['specialty'])}<br>
            <b>Status:</b> {html_module.escape(loc['status'])}
            </div>"""
            folium.Marker(
                [loc["lat"], loc["lon"]],
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=loc["name"],
                icon=folium.Icon(color="orange", icon="fire", prefix="fa"),
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "smithing_traditions.csv", "text/csv", key="dl_smithing")

    # ------------------------------------------------------------------ #
    #  7. Amber Trade Routes
    # ------------------------------------------------------------------ #
    elif mode == "Amber Trade Routes":
        locations = [
            {"name": "Kaliningrad (Konigsberg)", "lat": 54.71, "lon": 20.51, "country": "Russia", "role": "Major Source", "amber_type": "Baltic Succinite", "period": "Prehistoric to present", "notes": "90% of world's extractable amber reserves"},
            {"name": "Gdansk (Danzig)", "lat": 54.35, "lon": 18.65, "country": "Poland", "role": "Source & Trading Hub", "amber_type": "Baltic Succinite", "period": "Medieval to present", "notes": "Historic amber capital with world's largest museum"},
            {"name": "Palanga Amber Museum", "lat": 55.92, "lon": 21.07, "country": "Lithuania", "role": "Source & Museum", "amber_type": "Baltic Succinite", "period": "Prehistoric to present", "notes": "28,000-piece collection on Amber Coast"},
            {"name": "Jurmala - Latvian Amber Coast", "lat": 56.97, "lon": 23.77, "country": "Latvia", "role": "Source", "amber_type": "Baltic Succinite", "period": "Prehistoric to present", "notes": "Baltic amber washes ashore seasonally"},
            {"name": "Samland Peninsula Mines", "lat": 54.80, "lon": 19.95, "country": "Russia", "role": "Major Mining", "amber_type": "Baltic Succinite", "period": "1870s onward (industrial)", "notes": "World's largest amber mine at Yantarny"},
            {"name": "Aquileia", "lat": 45.77, "lon": 13.37, "country": "Italy", "role": "Roman Trading Hub", "amber_type": "Baltic (traded)", "period": "Roman era", "notes": "Southern terminus of ancient Amber Road"},
            {"name": "Carnuntum", "lat": 48.11, "lon": 16.86, "country": "Austria", "role": "Trade Route Station", "amber_type": "Baltic (traded)", "period": "Roman era", "notes": "Major Roman frontier town on Amber Road"},
            {"name": "Wroclaw (Breslau)", "lat": 51.11, "lon": 17.04, "country": "Poland", "role": "Trade Route Station", "amber_type": "Baltic (traded)", "period": "Medieval", "notes": "Key waypoint on medieval amber trade"},
            {"name": "Venice", "lat": 45.44, "lon": 12.34, "country": "Italy", "role": "Trading & Processing Hub", "amber_type": "Baltic (traded)", "period": "Medieval to Renaissance", "notes": "Major amber processing and rosary manufacturing"},
            {"name": "Bruges", "lat": 51.21, "lon": 3.22, "country": "Belgium", "role": "Trading Hub", "amber_type": "Baltic (traded)", "period": "Medieval", "notes": "Flemish amber trading and craft center"},
            {"name": "Lubeck", "lat": 53.87, "lon": 10.69, "country": "Germany", "role": "Hanseatic Trading Hub", "amber_type": "Baltic (traded)", "period": "Medieval", "notes": "Hanseatic League amber monopoly center"},
            {"name": "Chiapas Amber Region", "lat": 16.73, "lon": -92.64, "country": "Mexico", "role": "Source", "amber_type": "Mexican Amber (Chiapas)", "period": "Pre-Columbian to present", "notes": "Rare red and green amber from Simojovel"},
            {"name": "Dominican Republic Amber Mines", "lat": 19.58, "lon": -70.35, "country": "Dominican Republic", "role": "Source", "amber_type": "Dominican Blue Amber", "period": "Indigenous to present", "notes": "Rare blue fluorescent amber, famous inclusions"},
            {"name": "Myanmar (Kachin) Amber Mines", "lat": 26.33, "lon": 96.55, "country": "Myanmar", "role": "Source", "amber_type": "Burmite (Cretaceous)", "period": "Ancient to present", "notes": "99 million-year-old amber with dinosaur-era inclusions"},
            {"name": "Rivne Region", "lat": 50.62, "lon": 26.25, "country": "Ukraine", "role": "Source (illegal mining crisis)", "amber_type": "Baltic Succinite", "period": "Prehistoric to present", "notes": "Major illegal amber mining operations"},
            {"name": "Bitterfeld", "lat": 51.62, "lon": 12.33, "country": "Germany", "role": "Historical Source", "amber_type": "Bitterfeld Amber", "period": "Oligocene, mined 1975-1993", "notes": "Second largest European amber deposit"},
            {"name": "Sicily - Simetite", "lat": 37.50, "lon": 15.09, "country": "Italy", "role": "Historical Source", "amber_type": "Simetite (Sicilian)", "period": "Ancient", "notes": "Rare reddish amber from Simeto River"},
            {"name": "Borneo Amber Deposits", "lat": 5.30, "lon": 115.10, "country": "Malaysia", "role": "Source", "amber_type": "Borneo Amber", "period": "Miocene", "notes": "Tropical amber with unique inclusions"},
            {"name": "Saint Petersburg - Amber Room", "lat": 59.72, "lon": 30.40, "country": "Russia", "role": "Cultural Monument", "amber_type": "Baltic Succinite (crafted)", "period": "1701 (original), 2003 (reconstruction)", "notes": "Reconstructed Amber Room at Catherine Palace"},
            {"name": "Copenhagen Amber Museum", "lat": 55.68, "lon": 12.59, "country": "Denmark", "role": "Cultural Center", "amber_type": "Baltic (collected)", "period": "Viking age onward", "notes": "House of Amber with Viking-era collection"},
            {"name": "Sopot Amber Market", "lat": 54.44, "lon": 18.56, "country": "Poland", "role": "Modern Trading", "amber_type": "Baltic Succinite", "period": "Modern", "notes": "Major modern amber jewelry marketplace"},
            {"name": "Klaipeda Amber Quarter", "lat": 55.71, "lon": 21.13, "country": "Lithuania", "role": "Processing & Trading", "amber_type": "Baltic Succinite", "period": "Medieval to present", "notes": "Lithuanian amber jewelry artisan center"},
            {"name": "Vienna Natural History Museum", "lat": 48.21, "lon": 16.36, "country": "Austria", "role": "Museum Collection", "amber_type": "Various", "period": "Collection spans millennia", "notes": "Major scientific amber collection with rare inclusions"},
            {"name": "Sumatra Amber Deposits", "lat": 2.50, "lon": 99.00, "country": "Indonesia", "role": "Source", "amber_type": "Sumatran Amber (Miocene)", "period": "Recently discovered", "notes": "Tropical Miocene amber, entomological significance"},
            {"name": "New Jersey Amber Sites", "lat": 40.44, "lon": -74.23, "country": "USA", "role": "Historical/Scientific", "amber_type": "Cretaceous Amber", "period": "Cretaceous (90 Ma)", "notes": "Important Cretaceous amber with ancient insect fossils"},
            {"name": "Sarawak Amber (Merit-Pila)", "lat": 4.00, "lon": 114.00, "country": "Malaysia", "role": "Source", "amber_type": "Sarawak Amber (Miocene)", "period": "Miocene", "notes": "Rare tropical amber from Borneo with unique resin chemistry"},
            {"name": "Lebanese Amber Sites", "lat": 34.00, "lon": 35.75, "country": "Lebanon", "role": "Historical/Scientific", "amber_type": "Lebanese Amber (Cretaceous)", "period": "130 Ma (Early Cretaceous)", "notes": "Oldest amber with insect inclusions, extremely rare"},
            {"name": "Cedar Lake (Manitoba) Amber", "lat": 53.33, "lon": -99.95, "country": "Canada", "role": "Source", "amber_type": "Canadian Cretaceous Amber", "period": "Cretaceous (75 Ma)", "notes": "Significant Canadian amber deposit with fossil insects"},
            {"name": "Fushun Amber Mines", "lat": 41.87, "lon": 123.89, "country": "China", "role": "Source", "amber_type": "Fushun Amber (Eocene)", "period": "Eocene (50 Ma)", "notes": "Major Chinese amber source, coal-associated deposit"},
            {"name": "Oaxaca Amber Region", "lat": 17.07, "lon": -96.73, "country": "Mexico", "role": "Source", "amber_type": "Mexican Amber", "period": "Miocene", "notes": "Zapotec and Mixtec amber artifacts found in archaeological sites"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Amber Sites", len(df))
        c2.metric("Countries", df["country"].nunique())
        c3.metric("Amber Types", df["amber_type"].nunique())
        sources = len(df[df["role"].str.contains("Source")])
        c4.metric("Source Locations", sources)

        m = folium.Map(location=[48, 20], zoom_start=4, tiles="CartoDB dark_matter")
        role_colors = {"Major Source": "orange", "Source": "orange", "Source & Trading Hub": "red", "Source & Museum": "orange",
                       "Major Mining": "darkred", "Roman Trading Hub": "purple", "Trade Route Station": "blue",
                       "Trading & Processing Hub": "cadetblue", "Trading Hub": "blue", "Hanseatic Trading Hub": "blue",
                       "Source (illegal mining crisis)": "red", "Historical Source": "gray", "Cultural Monument": "pink",
                       "Cultural Center": "pink", "Modern Trading": "lightgreen", "Processing & Trading": "lightgreen",
                       "Museum Collection": "pink", "Historical/Scientific": "gray"}
        for loc in locations:
            popup_html = f"""
            <div style='min-width:240px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>Country:</b> {html_module.escape(loc['country'])}<br>
            <b>Role:</b> {html_module.escape(loc['role'])}<br>
            <b>Amber Type:</b> {html_module.escape(loc['amber_type'])}<br>
            <b>Period:</b> {html_module.escape(loc['period'])}<br>
            <b>Notes:</b> {html_module.escape(loc['notes'])}
            </div>"""
            folium.CircleMarker(
                [loc["lat"], loc["lon"]],
                radius=8,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=loc["name"],
                color="#FFA500",
                fill=True,
                fill_color="#FFD700",
                fill_opacity=0.7,
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "amber_trade_routes.csv", "text/csv", key="dl_amber")

    # ------------------------------------------------------------------ #
    #  8. Jade & Nephrite Sources
    # ------------------------------------------------------------------ #
    elif mode == "Jade & Nephrite Sources":
        locations = [
            {"name": "Hpakant (Jade Mines)", "lat": 25.98, "lon": 96.32, "country": "Myanmar", "jade_type": "Jadeite (Imperial)", "quality": "Supreme - Imperial Green", "annual_value": "$31 billion (est.)", "notes": "World's primary source of gem-quality jadeite"},
            {"name": "Kachin State Alluvial Fields", "lat": 25.50, "lon": 96.80, "country": "Myanmar", "jade_type": "Jadeite", "quality": "High - various colors", "annual_value": "Included above", "notes": "Alluvial jade boulders in river gravels"},
            {"name": "Hotan (Hetian) - White Jade", "lat": 37.11, "lon": 79.93, "country": "China", "jade_type": "Nephrite (Hetian)", "quality": "Supreme mutton-fat white", "annual_value": "$2+ billion", "notes": "Most prized nephrite source for 5,000+ years"},
            {"name": "Yurungkash & Karakash Rivers", "lat": 36.80, "lon": 79.30, "country": "China", "jade_type": "Nephrite (river pebbles)", "quality": "Highest for seed jade", "annual_value": "Premium prices", "notes": "River jade (zi liao) commands highest prices"},
            {"name": "Kunlun Mountains Deposits", "lat": 36.00, "lon": 80.00, "country": "China", "jade_type": "Nephrite (mountain)", "quality": "High - various", "annual_value": "Significant", "notes": "Mountain-mined nephrite, less valued than river jade"},
            {"name": "Xiuyan Jade Deposits", "lat": 40.28, "lon": 123.28, "country": "China", "jade_type": "Xiuyan Jade (serpentine)", "quality": "Commercial grade", "annual_value": "Moderate", "notes": "Large-scale serpentine jade production"},
            {"name": "Nanyang Jade Carving Center", "lat": 32.99, "lon": 112.53, "country": "China", "jade_type": "Processing center", "quality": "All grades processed", "annual_value": "Major industry", "notes": "Largest jade carving industry center in China"},
            {"name": "Guatemala - Motagua Valley", "lat": 15.00, "lon": -89.80, "country": "Guatemala", "jade_type": "Jadeite", "quality": "High - Olmec/Maya quality", "annual_value": "Limited production", "notes": "Only other significant jadeite source besides Myanmar"},
            {"name": "British Columbia - Cassiar", "lat": 59.28, "lon": -129.83, "country": "Canada", "jade_type": "Nephrite", "quality": "High - deep green", "annual_value": "$50+ million", "notes": "World's largest nephrite boulders found here"},
            {"name": "British Columbia - Fraser River", "lat": 49.25, "lon": -121.77, "country": "Canada", "jade_type": "Nephrite", "quality": "Good - green", "annual_value": "Included above", "notes": "Historic jade collecting along river"},
            {"name": "Cowell Jade Deposit", "lat": -33.68, "lon": 136.92, "country": "Australia", "jade_type": "Nephrite", "quality": "Good - dark green to black", "annual_value": "Moderate", "notes": "Southern Australia nephrite deposit"},
            {"name": "Westland - South Island", "lat": -42.45, "lon": 171.21, "country": "New Zealand", "jade_type": "Nephrite (Pounamu)", "quality": "Sacred cultural stone", "annual_value": "Cultural (restricted)", "notes": "Maori taonga (treasure), legally protected"},
            {"name": "Arahura River", "lat": -42.72, "lon": 171.08, "country": "New Zealand", "jade_type": "Nephrite (Pounamu)", "quality": "Supreme - inanga, kahurangi", "annual_value": "Cultural", "notes": "Most famous pounamu source for Maori"},
            {"name": "Sayan Mountains", "lat": 51.50, "lon": 100.00, "country": "Russia", "jade_type": "Nephrite", "quality": "Good - green, white", "annual_value": "$200+ million", "notes": "Major Russian nephrite exported to China"},
            {"name": "Vitim River Deposits", "lat": 56.43, "lon": 113.38, "country": "Russia", "jade_type": "Nephrite", "quality": "Good - spinach green", "annual_value": "Included above", "notes": "Siberian nephrite mining region"},
            {"name": "Polar Urals Deposits", "lat": 66.50, "lon": 65.50, "country": "Russia", "jade_type": "Nephrite", "quality": "Moderate to good", "annual_value": "Moderate", "notes": "Remote arctic nephrite deposits"},
            {"name": "Turkestan Range", "lat": 39.50, "lon": 68.00, "country": "Tajikistan", "jade_type": "Nephrite", "quality": "Moderate", "annual_value": "Small-scale", "notes": "Central Asian nephrite source"},
            {"name": "Chuncheon Jade Mines", "lat": 37.87, "lon": 127.73, "country": "South Korea", "jade_type": "Nephrite", "quality": "Moderate - green", "annual_value": "Small-scale", "notes": "Korean jade with cultural significance"},
            {"name": "Itoigawa - Japanese Jade", "lat": 37.04, "lon": 137.86, "country": "Japan", "jade_type": "Jadeite", "quality": "Historic - lavender & green", "annual_value": "Protected (no mining)", "notes": "Japan's national stone, UNESCO Geopark"},
            {"name": "Jordanow Slaski", "lat": 50.68, "lon": 16.53, "country": "Poland", "jade_type": "Nephrite", "quality": "Good - dark green", "annual_value": "Small-scale", "notes": "European nephrite source, Silesian deposits"},
            {"name": "Lushan Mountains", "lat": 29.56, "lon": 115.97, "country": "China", "jade_type": "Various jade-like stones", "quality": "Commercial", "annual_value": "Moderate", "notes": "Regional Chinese jade processing"},
            {"name": "Mandalay Jade Market", "lat": 21.97, "lon": 96.08, "country": "Myanmar", "jade_type": "Jadeite (trading)", "quality": "All grades", "annual_value": "Billions traded", "notes": "Massive jade trading market, much goes to China"},
            {"name": "Guangzhou Jade Market", "lat": 23.13, "lon": 113.26, "country": "China", "jade_type": "Trading center", "quality": "All grades", "annual_value": "Major", "notes": "Hualin jade market, southern China hub"},
            {"name": "Pingzhou Jade Street", "lat": 23.04, "lon": 113.10, "country": "China", "jade_type": "Jadeite processing", "quality": "All grades - cutting center", "annual_value": "Major", "notes": "China's main jadeite cutting and polishing center"},
            {"name": "Andes Jade Deposits", "lat": -33.00, "lon": -70.00, "country": "Chile", "jade_type": "Nephrite", "quality": "Moderate", "annual_value": "Small", "notes": "South American nephrite occurrences"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Jade Sites", len(df))
        c2.metric("Countries", df["country"].nunique())
        jadeite = len(df[df["jade_type"].str.contains("Jadeite", case=False)])
        nephrite = len(df[df["jade_type"].str.contains("Nephrite", case=False)])
        c3.metric("Jadeite Sources", jadeite)
        c4.metric("Nephrite Sources", nephrite)

        m = folium.Map(location=[30, 100], zoom_start=3, tiles="CartoDB dark_matter")
        for loc in locations:
            popup_html = f"""
            <div style='min-width:240px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>Country:</b> {html_module.escape(loc['country'])}<br>
            <b>Jade Type:</b> {html_module.escape(loc['jade_type'])}<br>
            <b>Quality:</b> {html_module.escape(loc['quality'])}<br>
            <b>Annual Value:</b> {html_module.escape(loc['annual_value'])}<br>
            <b>Notes:</b> {html_module.escape(loc['notes'])}
            </div>"""
            is_jadeite = "Jadeite" in loc["jade_type"]
            folium.CircleMarker(
                [loc["lat"], loc["lon"]],
                radius=9,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=loc["name"],
                color="#00FF00" if is_jadeite else "#228B22",
                fill=True,
                fill_color="#00FF00" if is_jadeite else "#228B22",
                fill_opacity=0.7,
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "jade_sources.csv", "text/csv", key="dl_jade")

    # ------------------------------------------------------------------ #
    #  9. Crown Jewels Collections
    # ------------------------------------------------------------------ #
    elif mode == "Crown Jewels Collections":
        locations = [
            {"name": "Tower of London - British Crown Jewels", "lat": 51.5081, "lon": -0.0759, "city": "London", "country": "UK", "pieces": "142 objects", "highlight": "Imperial State Crown, Koh-i-Noor, Cullinan I & II", "period": "1661 onward (post-Civil War)", "public_access": "Yes - 2.7M visitors/year"},
            {"name": "Topkapi Palace Treasury", "lat": 41.0115, "lon": 28.9833, "city": "Istanbul", "country": "Turkey", "pieces": "Thousands", "highlight": "Topkapi Dagger, Spoonmaker's Diamond (86 ct)", "period": "15th-19th century Ottoman", "public_access": "Yes"},
            {"name": "Iranian Crown Jewels - Central Bank", "lat": 35.6892, "lon": 51.3890, "city": "Tehran", "country": "Iran", "pieces": "Thousands (30+ kg gems)", "highlight": "Darya-ye Noor (182 ct pink diamond), Peacock Throne", "period": "Safavid to Pahlavi", "public_access": "Yes - Bank Markazi vault"},
            {"name": "Schatzkammer - Vienna Treasury", "lat": 48.2063, "lon": 16.3652, "city": "Vienna", "country": "Austria", "pieces": "163 objects", "highlight": "Imperial Crown of HRE, Holy Lance, emerald unguentarium", "period": "10th century onward", "public_access": "Yes"},
            {"name": "Kremlin Armoury - Diamond Fund", "lat": 55.7510, "lon": 37.6175, "city": "Moscow", "country": "Russia", "pieces": "250+ items in Diamond Fund", "highlight": "Orlov Diamond (190 ct), Great Imperial Crown", "period": "17th-19th century Romanov", "public_access": "Yes"},
            {"name": "Rosenborg Castle - Danish Crown Jewels", "lat": 55.6861, "lon": 12.5773, "city": "Copenhagen", "country": "Denmark", "pieces": "40+ objects", "highlight": "Christian IV's crown, Christian V's crown, regalia", "period": "1596 onward", "public_access": "Yes"},
            {"name": "Residenz Treasury - Munich", "lat": 48.1416, "lon": 11.5794, "city": "Munich", "country": "Germany", "pieces": "1,250 objects", "highlight": "Crown of Henry II, Bavarian Crown Jewels", "period": "Medieval to 19th century", "public_access": "Yes"},
            {"name": "Royal Palace - Swedish Regalia", "lat": 59.3268, "lon": 18.0717, "city": "Stockholm", "country": "Sweden", "pieces": "30+ objects", "highlight": "Erik XIV's crown (1561), Queen Christina's crown", "period": "16th century onward", "public_access": "Yes - Treasury vault"},
            {"name": "Nieuwe Kerk - Dutch Regalia Display", "lat": 52.3733, "lon": 4.8919, "city": "Amsterdam", "country": "Netherlands", "pieces": "12 objects", "highlight": "Crown of the Netherlands, Sword of State", "period": "1840 onward", "public_access": "During exhibitions"},
            {"name": "Aachen Cathedral Treasury", "lat": 50.7749, "lon": 6.0839, "city": "Aachen", "country": "Germany", "pieces": "100+ objects", "highlight": "Bust of Charlemagne, Lothar Cross", "period": "8th-15th century", "public_access": "Yes"},
            {"name": "Royal Palace - Norwegian Regalia", "lat": 59.9169, "lon": 10.7269, "city": "Oslo", "country": "Norway", "pieces": "15 objects", "highlight": "Crown of Norway (1818), Queen's crown", "period": "1818 onward", "public_access": "Limited"},
            {"name": "Nidaros Cathedral - Norwegian Crown Display", "lat": 63.4269, "lon": 10.3969, "city": "Trondheim", "country": "Norway", "pieces": "Regalia displayed", "highlight": "Norwegian Crown Regalia since 1988", "period": "1818-present", "public_access": "Yes"},
            {"name": "Budapest Parliament - Holy Crown", "lat": 47.5070, "lon": 19.0455, "city": "Budapest", "country": "Hungary", "pieces": "4 coronation objects", "highlight": "Holy Crown of Hungary (Szent Korona)", "period": "11th century onward", "public_access": "Yes"},
            {"name": "Wawel Cathedral Treasury", "lat": 50.0540, "lon": 19.9352, "city": "Krakow", "country": "Poland", "pieces": "100+ objects", "highlight": "Szczerbiec (coronation sword), reliquaries", "period": "13th century onward", "public_access": "Yes"},
            {"name": "Edinburgh Castle - Scottish Crown Jewels", "lat": 55.9486, "lon": -3.1999, "city": "Edinburgh", "country": "UK", "pieces": "Honours of Scotland + Stone of Destiny", "highlight": "Crown of Scotland (1540), Stone of Scone", "period": "15th century onward", "public_access": "Yes"},
            {"name": "Bangkok Grand Palace - Thai Regalia", "lat": 13.7500, "lon": 100.4913, "city": "Bangkok", "country": "Thailand", "pieces": "Royal regalia collection", "highlight": "Great Crown of Victory, golden niello objects", "period": "Rattanakosin era (1782+)", "public_access": "Partial"},
            {"name": "National Museum - Japanese Imperial Regalia", "lat": 34.68, "lon": 136.72, "city": "Ise", "country": "Japan", "pieces": "Three Imperial Regalia", "highlight": "Sacred Mirror, Sword, Jewel (Sanshu no Jingi)", "period": "Legendary / ancient", "public_access": "No - never publicly displayed"},
            {"name": "Smithsonian - National Gem Collection", "lat": 38.8913, "lon": -77.0261, "city": "Washington DC", "country": "USA", "pieces": "375,000+ specimens", "highlight": "Hope Diamond (45.52 ct), Star of Asia sapphire", "period": "Various", "public_access": "Yes - free admission"},
            {"name": "Louvre - French Crown Jewels", "lat": 48.8606, "lon": 2.3376, "city": "Paris", "country": "France", "pieces": "Remaining pieces after 1887 sale", "highlight": "Regent Diamond (140.64 ct), Hortensia Pink", "period": "17th-19th century Bourbon", "public_access": "Yes"},
            {"name": "Green Vault (Grunes Gewolbe)", "lat": 51.0529, "lon": 13.7369, "city": "Dresden", "country": "Germany", "pieces": "4,000+ objects", "highlight": "Dresden Green Diamond (41 ct), Moor with emeralds", "period": "16th-18th century Saxon", "public_access": "Yes (partially closed after 2019 heist)"},
            {"name": "National Palace Museum - Chinese Imperial", "lat": 25.1024, "lon": 121.5485, "city": "Taipei", "country": "Taiwan", "pieces": "700,000+ objects", "highlight": "Jadeite cabbage, Qing imperial jade seals", "period": "Sung to Qing dynasty", "public_access": "Yes"},
            {"name": "Tower of David - Ethiopian Imperial", "lat": 9.0105, "lon": 38.7468, "city": "Addis Ababa", "country": "Ethiopia", "pieces": "Royal collection", "highlight": "Crown of Emperor Haile Selassie, Aksumite gold", "period": "Solomonic dynasty", "public_access": "Limited - National Museum"},
            {"name": "Museu Imperial - Brazilian", "lat": -22.5066, "lon": -43.1794, "city": "Petropolis", "country": "Brazil", "pieces": "Imperial regalia", "highlight": "Imperial Crown of Brazil, Pedro II scepter", "period": "1822-1889", "public_access": "Yes"},
            {"name": "Palace Museum - Forbidden City", "lat": 39.9163, "lon": 116.3972, "city": "Beijing", "country": "China", "pieces": "1.8 million objects", "highlight": "Ming/Qing imperial gold & jade artifacts", "period": "Ming-Qing dynasty", "public_access": "Yes"},
            {"name": "Royal Collection - Moroccan Regalia", "lat": 34.0209, "lon": -6.8416, "city": "Rabat", "country": "Morocco", "pieces": "Royal treasures", "highlight": "Alaouite dynasty crowns, jeweled daggers", "period": "17th century onward", "public_access": "No - private royal collection"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Crown Jewel Collections", len(df))
        c2.metric("Countries", df["country"].nunique())
        public = len(df[df["public_access"].str.startswith("Yes")])
        c3.metric("Publicly Accessible", public)
        c4.metric("Cities", df["city"].nunique())

        m = folium.Map(location=[35, 20], zoom_start=3, tiles="CartoDB dark_matter")
        for loc in locations:
            popup_html = f"""
            <div style='min-width:260px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>City:</b> {html_module.escape(loc['city'])}, {html_module.escape(loc['country'])}<br>
            <b>Pieces:</b> {html_module.escape(loc['pieces'])}<br>
            <b>Highlight:</b> {html_module.escape(loc['highlight'])}<br>
            <b>Period:</b> {html_module.escape(loc['period'])}<br>
            <b>Public Access:</b> {html_module.escape(loc['public_access'])}
            </div>"""
            folium.Marker(
                [loc["lat"], loc["lon"]],
                popup=folium.Popup(popup_html, max_width=340),
                tooltip=loc["name"],
                icon=folium.Icon(color="red", icon="crown", prefix="fa"),
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "crown_jewels.csv", "text/csv", key="dl_crowns")

    # ------------------------------------------------------------------ #
    #  10. Gemstone Cutting Centers
    # ------------------------------------------------------------------ #
    elif mode == "Gemstone Cutting Centers":
        locations = [
            {"name": "Jaipur - Colored Gemstone Capital", "lat": 26.91, "lon": 75.79, "country": "India", "specialty": "Emerald, ruby, sapphire cutting & cabochons", "workforce": "500,000+", "global_share": "90% of world's colored stones", "notes": "World's largest gemstone cutting center"},
            {"name": "Surat - Diamond Cutting Hub", "lat": 21.17, "lon": 72.83, "country": "India", "specialty": "Diamond cutting & polishing", "workforce": "800,000+", "global_share": "90% of world's diamonds", "notes": "Cuts 14 out of every 15 diamonds in the world"},
            {"name": "Antwerp Diamond District", "lat": 51.22, "lon": 4.42, "country": "Belgium", "specialty": "Diamond trading, cutting, certification", "workforce": "30,000+", "global_share": "80% of rough diamonds traded", "notes": "World diamond capital since 15th century"},
            {"name": "Tel Aviv Diamond Exchange", "lat": 32.08, "lon": 34.80, "country": "Israel", "specialty": "Precision diamond cutting, fancy shapes", "workforce": "15,000+", "global_share": "Significant in high-end", "notes": "Known for innovative cuts and high technology"},
            {"name": "New York Diamond District", "lat": 40.7570, "lon": -73.9800, "country": "USA", "specialty": "Diamond trading, custom jewelry", "workforce": "25,000+", "global_share": "Major trading hub", "notes": "47th Street - $24 billion annual trade"},
            {"name": "Idar-Oberstein", "lat": 49.71, "lon": 7.31, "country": "Germany", "specialty": "Agate, colored stone cutting, engraving", "workforce": "5,000+", "global_share": "European cutting leader", "notes": "500-year tradition, famous gem-cutting school"},
            {"name": "Chanthaburi", "lat": 12.61, "lon": 102.10, "country": "Thailand", "specialty": "Ruby, sapphire heat treatment & cutting", "workforce": "100,000+", "global_share": "70% of world's rubies processed", "notes": "Global center for corundum enhancement"},
            {"name": "Bangkok Gem Quarter", "lat": 13.73, "lon": 100.52, "country": "Thailand", "specialty": "Colored stone cutting, trading", "workforce": "50,000+", "global_share": "Major Asian hub", "notes": "Silom and Mahesak gem trading streets"},
            {"name": "Guangzhou Panyu Gem District", "lat": 22.95, "lon": 113.38, "country": "China", "specialty": "Mass gem cutting, CZ, synthetic stones", "workforce": "200,000+", "global_share": "Largest volume producer", "notes": "Industrial-scale gem processing"},
            {"name": "Wuzhou - Synthetic Gem Capital", "lat": 23.47, "lon": 111.32, "country": "China", "specialty": "Synthetic gemstones, cubic zirconia", "workforce": "100,000+", "global_share": "80% of world's synthetic gems", "notes": "World capital of synthetic stone production"},
            {"name": "Shenzhen Gem Processing", "lat": 22.54, "lon": 114.06, "country": "China", "specialty": "Diamond cutting, jewelry manufacturing", "workforce": "50,000+", "global_share": "Growing diamond center", "notes": "Modern high-tech cutting facilities"},
            {"name": "Ratnapura Cutting Workshops", "lat": 6.68, "lon": 80.40, "country": "Sri Lanka", "specialty": "Sapphire, cat's eye cutting", "workforce": "30,000+", "global_share": "Notable in sapphires", "notes": "Traditional cutting alongside mining"},
            {"name": "Mogok Cutting Village", "lat": 22.92, "lon": 96.50, "country": "Myanmar", "specialty": "Ruby, sapphire, spinel cutting", "workforce": "10,000+", "global_share": "Local processing", "notes": "Artisan cutting near mine sources"},
            {"name": "Bogota Emerald Market", "lat": 4.60, "lon": -74.08, "country": "Colombia", "specialty": "Emerald cutting, oiling, trading", "workforce": "20,000+", "global_share": "Primary emerald processing", "notes": "Near mine sources, specialized emerald expertise"},
            {"name": "Dubai Multi Commodities Centre", "lat": 25.07, "lon": 55.14, "country": "UAE", "specialty": "Diamond trading, colored stones", "workforce": "20,000+", "global_share": "Growing regional hub", "notes": "Tax-free diamond and gem trading zone"},
            {"name": "Turnov", "lat": 50.59, "lon": 15.16, "country": "Czech Republic", "specialty": "Bohemian garnet, glass gems", "workforce": "2,000+", "global_share": "Bohemian garnet monopoly", "notes": "Traditional garnet cutting since 16th century"},
            {"name": "Nairobi Gem Dealers", "lat": -1.29, "lon": 36.82, "country": "Kenya", "specialty": "Tsavorite, tanzanite, ruby cutting", "workforce": "5,000+", "global_share": "East African hub", "notes": "Growing center for African gem processing"},
            {"name": "Arusha Tanzanite Center", "lat": -3.37, "lon": 36.68, "country": "Tanzania", "specialty": "Tanzanite cutting & grading", "workforce": "3,000+", "global_share": "Primary tanzanite processing", "notes": "Near Merelani mines, government-supported"},
            {"name": "Itaitinga Gem Center", "lat": -3.97, "lon": -38.53, "country": "Brazil", "specialty": "Tourmaline, aquamarine, topaz cutting", "workforce": "8,000+", "global_share": "Significant in Brazilian gems", "notes": "Brazilian colored stone processing"},
            {"name": "Teofilo Otoni", "lat": -17.86, "lon": -41.51, "country": "Brazil", "specialty": "All Brazilian colored stones", "workforce": "15,000+", "global_share": "Major Brazilian hub", "notes": "Gem trading capital of Brazil"},
            {"name": "Hong Kong Gem Centre", "lat": 22.28, "lon": 114.17, "country": "China", "specialty": "Jade, pearl, diamond trading", "workforce": "10,000+", "global_share": "Major Asian trade hub", "notes": "Free port for gem trading, major auctions"},
            {"name": "Moscow Diamond Cutting", "lat": 55.76, "lon": 37.62, "country": "Russia", "specialty": "Russian diamond cutting", "workforce": "5,000+", "global_share": "Domestic processing", "notes": "Kristall and Alrosa cutting facilities"},
            {"name": "Smolensk Diamond Plant", "lat": 54.78, "lon": 32.05, "country": "Russia", "specialty": "Large diamond polishing", "workforce": "3,000+", "global_share": "Premium Russian diamonds", "notes": "Specialized in large, high-value stones"},
            {"name": "Gaborone Diamond Hub", "lat": -24.65, "lon": 25.91, "country": "Botswana", "specialty": "Diamond sorting, cutting, valuation", "workforce": "5,000+", "global_share": "Growing African center", "notes": "De Beers Global Sightholder Sales moved here"},
            {"name": "Tucson Gem Shows", "lat": 32.22, "lon": -110.97, "country": "USA", "specialty": "Annual gem/mineral trading event", "workforce": "Seasonal (60,000 attendees)", "global_share": "World's largest gem show", "notes": "Annual February event, billions in trade"},
            {"name": "Hatton Garden", "lat": 51.5202, "lon": -0.1082, "country": "UK", "specialty": "Diamond and gemstone trading, bespoke jewelry", "workforce": "8,000+", "global_share": "UK's primary gem center", "notes": "London's historic jewelry quarter since medieval times"},
            {"name": "Nairobi Lapidary Centre", "lat": -1.27, "lon": 36.81, "country": "Kenya", "specialty": "Tanzanite, tsavorite, ruby cutting", "workforce": "2,000+", "global_share": "East African cutting hub", "notes": "Training artisan cutters for East African gems"},
            {"name": "Colombo Gem Market", "lat": 6.93, "lon": 79.85, "country": "Sri Lanka", "specialty": "Sapphire and multi-gem cutting & trading", "workforce": "20,000+", "global_share": "Notable in sapphires", "notes": "Sea Street gem district with hundreds of dealers"},
            {"name": "Mandalay Jade Cutting", "lat": 21.97, "lon": 96.08, "country": "Myanmar", "specialty": "Jadeite cutting, carving, cabochon", "workforce": "30,000+", "global_share": "Primary jadeite processing", "notes": "Jade boulders cut and shaped before export to China"},
            {"name": "Jequitinhonha Valley Workshops", "lat": -16.44, "lon": -41.01, "country": "Brazil", "specialty": "Aquamarine, tourmaline, topaz cutting", "workforce": "5,000+", "global_share": "Brazilian specialty", "notes": "Near Minas Gerais gem deposits, artisan cutting"},
            {"name": "Maputo Gem Processing", "lat": -25.97, "lon": 32.57, "country": "Mozambique", "specialty": "Ruby, garnet cutting", "workforce": "3,000+", "global_share": "Emerging African center", "notes": "Processing stones from Montepuez ruby mines"},
            {"name": "Beruwala Gem Traders", "lat": 6.47, "lon": 80.07, "country": "Sri Lanka", "specialty": "Multi-gem rough trading", "workforce": "5,000+", "global_share": "Notable in rough trading", "notes": "Moorish gem trading community since 8th century"},
        ]

        df = pd.DataFrame(locations)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cutting Centers", len(df))
        c2.metric("Countries", df["country"].nunique())
        india_workforce = sum(
            int(loc["workforce"].replace(",", "").replace("+", ""))
            for loc in locations
            if loc["country"] == "India"
        )
        c3.metric("India Workforce", f"{india_workforce:,}+")
        c4.metric("Specialties", df["specialty"].nunique())

        m = folium.Map(location=[20, 50], zoom_start=3, tiles="CartoDB dark_matter")
        for loc in locations:
            popup_html = f"""
            <div style='min-width:250px'>
            <b>{html_module.escape(loc['name'])}</b><br>
            <b>Country:</b> {html_module.escape(loc['country'])}<br>
            <b>Specialty:</b> {html_module.escape(loc['specialty'])}<br>
            <b>Workforce:</b> {html_module.escape(loc['workforce'])}<br>
            <b>Global Share:</b> {html_module.escape(loc['global_share'])}<br>
            <b>Notes:</b> {html_module.escape(loc['notes'])}
            </div>"""
            folium.Marker(
                [loc["lat"], loc["lon"]],
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=loc["name"],
                icon=folium.Icon(color="lightblue", icon="cut", prefix="fa"),
            ).add_to(m)
        st_html(m._repr_html_(), height=500)
        st.dataframe(df, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "cutting_centers.csv", "text/csv", key="dl_cutting")
