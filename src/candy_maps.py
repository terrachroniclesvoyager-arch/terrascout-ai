"""
Candy & Sweet Traditions Explorer module for TerraScout AI.
Displays curated maps of world candy traditions, chocolate factories,
candy museums, licorice origins, gummy bear history, chewing gum,
marzipan & nougat, cotton candy fairgrounds, caramel & toffee, and lollipops.
All preset data — no external API key required.
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
import html as html_module

# ═══════════════════════════════════════════
# MARKER COLOR PALETTE
# ═══════════════════════════════════════════
CANDY_COLORS = {
    "traditions": "#ec4899",   # pink
    "chocolate": "#8b5cf6",    # violet
    "museum": "#06b6d4",       # cyan
    "licorice": "#1e293b",     # dark
    "gummy": "#10b981",        # emerald
    "gum": "#f59e0b",          # amber
    "marzipan": "#f97316",     # orange
    "cotton": "#e879f9",       # fuchsia
    "caramel": "#d97706",      # warm amber
    "lollipop": "#ef4444",     # red
}

# ═══════════════════════════════════════════
# MODE 1: WORLD CANDY & SWEET TRADITIONS
# ═══════════════════════════════════════════
CANDY_TRADITIONS = [
    {"name": "Turkish Delight (Lokum)", "lat": 41.0082, "lon": 28.9784,
     "desc": "Istanbul, Turkey — Lokum has been produced since the 15th century. Ali Muhiddin Haci Bekir, founded 1777, is the most famous maker."},
    {"name": "Japanese Wagashi", "lat": 35.0116, "lon": 135.7681,
     "desc": "Kyoto, Japan — Traditional Japanese confections made from mochi, anko (bean paste), and seasonal ingredients. Deeply tied to tea ceremony culture."},
    {"name": "French Dragees", "lat": 48.7734, "lon": 5.1600,
     "desc": "Verdun, France — Sugar-coated almonds have been made here since 1220. Maison Braquier continues the tradition."},
    {"name": "Mexican Dulces Tipicos", "lat": 19.4326, "lon": -99.1332,
     "desc": "Mexico City, Mexico — Rich tradition of tamarind candy, cajeta, alegrijas (amaranth bars), and chamoy-flavored sweets."},
    {"name": "Indian Mithai", "lat": 28.6139, "lon": 77.2090,
     "desc": "Delhi, India — Vast tradition of milk-based sweets: gulab jamun, barfi, rasgulla, jalebi, ladoo. Sweet shops (halwai) are cultural institutions."},
    {"name": "Persian Gaz & Sohan", "lat": 32.6546, "lon": 51.6680,
     "desc": "Isfahan, Iran — Gaz (Persian nougat) made with manna and rosewater. Sohan is a saffron and pistachio brittle from Qom."},
    {"name": "Italian Confetti di Sulmona", "lat": 42.0449, "lon": 13.9259,
     "desc": "Sulmona, Italy — Jordan almonds (confetti) have been crafted here since the 15th century. Pelino factory museum dates to 1783."},
    {"name": "Brazilian Brigadeiro", "lat": -23.5505, "lon": -46.6333,
     "desc": "Sao Paulo, Brazil — Chocolate truffle-like balls made from condensed milk and cocoa, invented in the 1940s. A national sweet icon."},
    {"name": "Australian Fairy Bread", "lat": -33.8688, "lon": 151.2093,
     "desc": "Sydney, Australia — White bread with butter and hundreds-and-thousands sprinkles. An iconic children's party treat since the 1920s."},
    {"name": "Swedish Godis (Pick & Mix)", "lat": 59.3293, "lon": 18.0686,
     "desc": "Stockholm, Sweden — Lordagsgodis (Saturday sweets) tradition. Sweden consumes the most candy per capita in the world."},
    {"name": "German Lebkuchen", "lat": 49.4521, "lon": 11.0767,
     "desc": "Nuremberg, Germany — Spiced honey cakes dating to medieval times. The Nuremberg Christkindlesmarkt is famous for them."},
    {"name": "Greek Loukoumi & Pasteli", "lat": 37.9715, "lon": 23.7267,
     "desc": "Athens, Greece — Loukoumi (Greek delight) and pasteli (sesame-honey bars) are ancient confections still enjoyed today."},
    {"name": "Filipino Ube Halaya & Pastillas", "lat": 14.5995, "lon": 120.9842,
     "desc": "Manila, Philippines — Purple yam (ube) sweets and pastillas de leche (milk candies from Bulacan) are beloved traditions."},
    {"name": "Moroccan Chebakia", "lat": 31.6295, "lon": -7.9811,
     "desc": "Marrakech, Morocco — Flower-shaped fried pastry coated in honey and sesame, traditionally served during Ramadan."},
    {"name": "South Korean Dalgona", "lat": 37.5665, "lon": 126.9780,
     "desc": "Seoul, South Korea — Sugar honeycomb candy made by street vendors. Became a global sensation through pop culture."},
]

# ═══════════════════════════════════════════
# MODE 2: CHOCOLATE FACTORY TOURS
# ═══════════════════════════════════════════
CHOCOLATE_FACTORIES = [
    {"name": "Hershey's Chocolate World", "lat": 40.2871, "lon": -76.6555,
     "desc": "Hershey, Pennsylvania, USA — Founded 1894. Free factory tour ride, chocolate tasting, and create-your-own candy bar experience."},
    {"name": "Cadbury World", "lat": 52.4298, "lon": -1.9327,
     "desc": "Bournville, Birmingham, UK — Cadbury factory visitor center. Learn about cocoa, watch chocolate being made, and enjoy free samples."},
    {"name": "Lindt Home of Chocolate", "lat": 47.3475, "lon": 8.5577,
     "desc": "Kilchberg, Zurich, Switzerland — World's largest Lindt chocolate museum with a 9-meter chocolate fountain. Opened 2020."},
    {"name": "Toblerone Factory (Bern)", "lat": 46.9480, "lon": 7.4474,
     "desc": "Bern, Switzerland — Toblerone was created here in 1908 by Theodor Tobler. Distinctive triangular bar inspired by the Matterhorn."},
    {"name": "Maison Cailler (Nestle)", "lat": 46.4706, "lon": 6.9131,
     "desc": "Broc, Switzerland — Switzerland's oldest chocolate brand (1819). Interactive tour through chocolate history and Swiss Alps setting."},
    {"name": "Ghirardelli Square", "lat": 37.8060, "lon": -122.4230,
     "desc": "San Francisco, California, USA — Historic chocolate factory turned marketplace. Ghirardelli has made chocolate here since 1852."},
    {"name": "Chocolate Museum (Museu de la Xocolata)", "lat": 41.3874, "lon": 2.1801,
     "desc": "Barcelona, Spain — Housed in a former convent. History of chocolate from Mesoamerica to Europe. Chocolate sculptures and tastings."},
    {"name": "Zotter Chocolate Factory", "lat": 47.1168, "lon": 15.9069,
     "desc": "Riegersburg, Austria — Bean-to-bar organic and fair-trade chocolate. Edible Zoo and Chocolate Theatre tours. Over 500 varieties."},
    {"name": "Valor Chocolate Factory", "lat": 38.6920, "lon": -0.4749,
     "desc": "Villajoyosa, Alicante, Spain — Family-run since 1881. Museum and factory tour in the colorful coastal town known as 'Chocolate City'."},
    {"name": "Theo Chocolate", "lat": 47.6587, "lon": -122.3475,
     "desc": "Seattle, Washington, USA — First organic and fair-trade bean-to-bar chocolate factory in North America. Public tours available."},
    {"name": "Cote d'Or / Callebaut (Barry Callebaut)", "lat": 51.1802, "lon": 4.0714,
     "desc": "Wieze, Belgium — One of the world's largest chocolate production facilities. Belgian chocolate heritage since 1850."},
    {"name": "Ritter Sport Chocolate Museum", "lat": 48.4916, "lon": 9.2146,
     "desc": "Waldenbuch, Germany — Colorful square chocolate maker. Factory outlet, museum, and make-your-own chocolate workshop."},
    {"name": "Meiji Chocolate Factory", "lat": 34.8177, "lon": 135.4285,
     "desc": "Takatsuki, Osaka, Japan — Tours of the facility where Meiji produces its iconic chocolate bars and snacks."},
    {"name": "Taza Chocolate", "lat": 42.3945, "lon": -71.0810,
     "desc": "Somerville, Massachusetts, USA — Stone-ground Mexican-style chocolate. Factory tours showcasing traditional grinding methods."},
    {"name": "Hachez Chocolade", "lat": 53.0793, "lon": 8.8017,
     "desc": "Bremen, Germany — Premium German chocolate since 1890. Known for its fine cocoa blends and elegant packaging."},
]

# ═══════════════════════════════════════════
# MODE 3: CANDY MUSEUMS
# ═══════════════════════════════════════════
CANDY_MUSEUMS = [
    {"name": "Museo del Dulce (Candy Museum)", "lat": 22.1506, "lon": -100.9761,
     "desc": "San Luis Potosi, Mexico — Displays traditional Mexican candy-making techniques, molds, and hundreds of regional sweet varieties."},
    {"name": "Sugarlandia (Museo del Azucar)", "lat": 10.3910, "lon": -75.5146,
     "desc": "Cartagena, Colombia — Museum dedicated to the history of sugar and candy in the Americas. Interactive exhibits."},
    {"name": "Haribo Museum & Store", "lat": 50.7374, "lon": 7.0982,
     "desc": "Bonn, Germany — Flagship store and exhibition at Haribo's birthplace. Giant pick-and-mix and gummy bear history."},
    {"name": "Bon Bon Land", "lat": 55.1968, "lon": 11.9889,
     "desc": "Holme-Olstrup, Denmark — Amusement park themed around Danish candy brand BonBon. Rides and candy factory tours."},
    {"name": "Candy Museum (Muzeum Cukiernictwa)", "lat": 54.3520, "lon": 18.6466,
     "desc": "Gdansk, Poland — Interactive museum in the historic old town. Learn about candy-making traditions of the Baltic region."},
    {"name": "Candytopia", "lat": 40.7484, "lon": -73.9857,
     "desc": "New York City, USA — Immersive, Instagram-worthy candy art installations and interactive rooms. Traveling pop-up exhibition."},
    {"name": "Sweet Pete's Candy", "lat": 30.3271, "lon": -81.6569,
     "desc": "Jacksonville, Florida, USA — Candy-making classes and factory tours in a restored historic building. Artisan sweets."},
    {"name": "Museum of Cocoa and Chocolate", "lat": 50.8432, "lon": 4.3530,
     "desc": "Brussels, Belgium — Choco-Story Brussels covers 2,600 years of chocolate history with live praline demonstrations."},
    {"name": "Imhoff Chocolate Museum", "lat": 50.9322, "lon": 6.9644,
     "desc": "Cologne, Germany — Major museum by Lindt on the Rhine. Tropical greenhouse, chocolate fountain, and production line viewing."},
    {"name": "Confectionery Museum at Pelino", "lat": 42.0449, "lon": 13.9259,
     "desc": "Sulmona, Italy — Inside the historic Pelino confetti factory (est. 1783). Displays antique tools and confetti art."},
    {"name": "Caramella Candy Museum", "lat": 45.0703, "lon": 7.6869,
     "desc": "Turin, Italy — Small museum dedicated to Italian candy traditions, gianduja, and Piedmontese confectionery history."},
    {"name": "Skansen Open-Air Museum (Candy Shop)", "lat": 59.3268, "lon": 18.1028,
     "desc": "Stockholm, Sweden — Historic candy shop within the world's oldest open-air museum. Traditional Swedish sweets made by hand."},
]

# ═══════════════════════════════════════════
# MODE 4: LICORICE ORIGINS
# ═══════════════════════════════════════════
LICORICE_ORIGINS = [
    {"name": "Amarelli Licorice Museum", "lat": 39.6569, "lon": 16.5204,
     "desc": "Rossano, Calabria, Italy — The Amarelli family has produced licorice since 1731. The museum is in a 15th-century palazzo."},
    {"name": "Pontefract (Liquorice Capital)", "lat": 53.6906, "lon": -1.3094,
     "desc": "Pontefract, West Yorkshire, UK — Pontefract cakes (licorice rounds) have been made here since the 17th century. Annual licorice festival."},
    {"name": "Harrogate (Farrah's Toffee & Licorice)", "lat": 53.9921, "lon": -1.5418,
     "desc": "Harrogate, UK — Home of Farrah's Original Harrogate Toffee and Yorkshire licorice confections since 1840."},
    {"name": "Brok, Netherlands (Drop Capital)", "lat": 52.3676, "lon": 4.9041,
     "desc": "Amsterdam, Netherlands — The Dutch consume more licorice (drop) per capita than anyone. Both sweet and salty varieties abound."},
    {"name": "Lakrids by Bulow", "lat": 55.6761, "lon": 12.5683,
     "desc": "Copenhagen, Denmark — Premium Danish licorice brand. Factory and flagship store. Known for chocolate-coated licorice."},
    {"name": "Fazer Licorice", "lat": 60.1699, "lon": 24.9384,
     "desc": "Helsinki, Finland — Fazer's salmiakki (salty licorice) is a Finnish institution. The Fazer Experience visitor center showcases it."},
    {"name": "Kolsvart Swedish Licorice", "lat": 57.7089, "lon": 11.9746,
     "desc": "Gothenburg, Sweden — Swedish lakrits ranges from sweet to intensely salty. Fish-shaped licorice (Malaco Djungelvraal) is iconic."},
    {"name": "Katjes Licorice", "lat": 51.3188, "lon": 6.5697,
     "desc": "Emmerich am Rhein, Germany — Katjes has produced licorice cats and other shapes since 1910. One of Germany's top candy makers."},
    {"name": "Glycyrrhiza Fields of Calabria", "lat": 39.3088, "lon": 16.3464,
     "desc": "Calabria, Italy — The Glycyrrhiza glabra plant grows wild here. Calabrian licorice root is prized worldwide for its sweetness."},
    {"name": "Uyghur Region Licorice Root", "lat": 39.4704, "lon": 75.9899,
     "desc": "Kashgar, Xinjiang, China — One of the world's major licorice root producing regions. Used in both confectionery and traditional medicine."},
    {"name": "Turkish Meyan Root", "lat": 37.0662, "lon": 37.3833,
     "desc": "Gaziantep, Turkey — Meyan serbeti (licorice root sherbet) is a traditional summer drink. Turkey is a major licorice root exporter."},
    {"name": "Panda Licorice", "lat": 63.0960, "lon": 21.6158,
     "desc": "Vaajakoski, Finland — Panda has made natural licorice from Finnish traditions since 1927. Exported worldwide."},
]

# ═══════════════════════════════════════════
# MODE 5: GUMMY BEAR & HARIBO
# ═══════════════════════════════════════════
GUMMY_BEAR_DATA = [
    {"name": "Haribo Headquarters", "lat": 50.7374, "lon": 7.0982,
     "desc": "Bonn, Germany — Hans Riegel founded Haribo here in 1920. The name is an acronym: HAns RIegel BOnn. Still the world's largest gummy maker."},
    {"name": "Haribo Factory Grafschaft", "lat": 50.5830, "lon": 7.0532,
     "desc": "Grafschaft, Germany — One of Haribo's major production facilities near Bonn. Produces millions of Goldbears daily."},
    {"name": "Haribo Factory Solingen", "lat": 51.1652, "lon": 7.0671,
     "desc": "Solingen, Germany — Another key Haribo production site in North Rhine-Westphalia. Licorice and fruit gummy production."},
    {"name": "Haribo Factory Uzès", "lat": 44.0125, "lon": 4.4197,
     "desc": "Uzes, Provence, France — Haribo's French production facility and museum. Includes the Musee du Bonbon Haribo."},
    {"name": "Haribo Factory Pontefract", "lat": 53.6906, "lon": -1.3094,
     "desc": "Pontefract, UK — Haribo's British factory. Produces Starmix, Tangfastics, and other gummy favorites for the UK market."},
    {"name": "Trolli Headquarters", "lat": 49.5981, "lon": 10.9575,
     "desc": "Furth, Germany — Trolli invented gummy worms in 1981. Known for creative, playful gummy candy shapes."},
    {"name": "Albanese Candy Factory", "lat": 41.5217, "lon": -87.3484,
     "desc": "Merrillville, Indiana, USA — Famous for high-quality gummy bears in 12 flavors. Factory store and viewing gallery."},
    {"name": "Black Forest Gummy (Ferrara)", "lat": 41.8781, "lon": -87.6298,
     "desc": "Chicago, Illinois, USA — Ferrara Candy Company produces Black Forest gummy bears and organic gummies. Major US gummy brand."},
    {"name": "Katjes (Vegetarian Gummies)", "lat": 51.3188, "lon": 6.5697,
     "desc": "Emmerich am Rhein, Germany — Pioneer of gelatin-free gummy candy. Uses plant-based alternatives since 2016."},
    {"name": "Gelatin Museum (GELITA)", "lat": 49.4875, "lon": 8.4660,
     "desc": "Eberbach, Germany — GELITA, a major gelatin producer. The science behind gummy candy's signature texture starts here."},
    {"name": "Sugarfina HQ", "lat": 34.0259, "lon": -118.3997,
     "desc": "Los Angeles, California, USA — Luxury gummy candy boutique brand. Famous for champagne bears and designer candy collections."},
    {"name": "Vidal Candies", "lat": 39.2145, "lon": -0.5242,
     "desc": "Murcia, Spain — Major European gummy and jelly candy manufacturer. Exports gummy sweets to over 90 countries."},
]

# ═══════════════════════════════════════════
# MODE 6: CHEWING GUM HISTORY
# ═══════════════════════════════════════════
CHEWING_GUM_DATA = [
    {"name": "Wrigley Building & HQ", "lat": 41.8892, "lon": -87.6245,
     "desc": "Chicago, Illinois, USA — William Wrigley Jr. founded his gum empire here. The iconic Wrigley Building (1924) still stands on Michigan Ave."},
    {"name": "Chicle Harvesting Region", "lat": 18.5036, "lon": -88.3055,
     "desc": "Quintana Roo, Mexico — The Yucatan Peninsula is where chicle (natural gum base from sapodilla trees) was first harvested by the Maya."},
    {"name": "Adams Gum Factory Site", "lat": 40.7128, "lon": -74.0060,
     "desc": "New York City, USA — Thomas Adams produced the first commercial chewing gum here in 1871 using Mexican chicle. Brand: Adams New York Gum."},
    {"name": "Dubble Bubble / Fleer HQ", "lat": 39.9526, "lon": -75.1652,
     "desc": "Philadelphia, Pennsylvania, USA — Walter Diemer invented bubble gum at Fleer Corporation in 1928. The original pink color was the only dye available."},
    {"name": "Cadbury/Trident Factory", "lat": 51.5225, "lon": -0.7130,
     "desc": "Maidenhead, UK — Mondelez (Cadbury) produces Trident and Stimorol gum for European markets. Long history of British gum manufacture."},
    {"name": "Lotte Chewing Gum HQ", "lat": 35.6762, "lon": 139.6503,
     "desc": "Tokyo, Japan — Lotte Corporation, founded 1948, is Asia's largest gum maker. Known for Xylitol gum and innovative flavors."},
    {"name": "Perfetti Van Melle (Mentos/Airwaves)", "lat": 44.8015, "lon": 10.3279,
     "desc": "Lainate/Parma, Italy — Italian-Dutch confectionery giant. Produces Mentos gum, Chupa Chups, Airheads, and more."},
    {"name": "Ancient Greek Mastic Gum", "lat": 38.3656, "lon": 25.9515,
     "desc": "Chios Island, Greece — Mastic resin from the mastic tree (Pistacia lentiscus) has been chewed for over 2,500 years. UNESCO protected."},
    {"name": "Spruce Gum Origin (Native American)", "lat": 44.2706, "lon": -71.3033,
     "desc": "New England, USA — Native Americans chewed spruce tree resin. John Curtis sold the first commercial spruce gum in 1848."},
    {"name": "Cloetta Jenkki Factory", "lat": 61.4978, "lon": 23.7610,
     "desc": "Tampere, Finland — Jenkki xylitol gum pioneered dental health gum. Finland led research proving xylitol prevents cavities."},
    {"name": "Beldent/Chiclets (Argentina)", "lat": -34.6037, "lon": -58.3816,
     "desc": "Buenos Aires, Argentina — Beldent gum is a cultural icon. Cadbury/Mondelez produces it for all of Latin America."},
    {"name": "Singapore Gum Ban Marker", "lat": 1.3521, "lon": 103.8198,
     "desc": "Singapore — Chewing gum has been banned from import/sale since 1992, except therapeutic gum. A unique chapter in gum history."},
]

# ═══════════════════════════════════════════
# MODE 7: MARZIPAN & NOUGAT
# ═══════════════════════════════════════════
MARZIPAN_NOUGAT_DATA = [
    {"name": "Niederegger Marzipan", "lat": 53.8655, "lon": 10.6866,
     "desc": "Lubeck, Germany — The world's most famous marzipan maker since 1806. Lubeck marzipan has Protected Geographical Indication status."},
    {"name": "Torrone di Cremona", "lat": 45.1333, "lon": 10.0244,
     "desc": "Cremona, Italy — Italian nougat (torrone) tradition dates to the 15th century. Annual Festa del Torrone celebrates the craft."},
    {"name": "Montelimar Nougat", "lat": 44.5580, "lon": 4.7510,
     "desc": "Montelimar, France — French nougat capital since the 17th century. Authentic Montelimar nougat requires almonds, honey, and egg whites."},
    {"name": "Toledo Mazapan", "lat": 39.8628, "lon": -4.0273,
     "desc": "Toledo, Spain — Spanish marzipan (mazapan) has been made by nuns in convents since the 12th century. Santo Tome is the most famous brand."},
    {"name": "Konigsberg Marzipan Origin", "lat": 54.7104, "lon": 20.4522,
     "desc": "Kaliningrad (former Konigsberg), Russia — One of the claimed birthplaces of marzipan in Europe, dating to medieval Hanseatic trade routes."},
    {"name": "Persian Toot (Mulberry Marzipan)", "lat": 32.6546, "lon": 51.6680,
     "desc": "Isfahan, Iran — Persian marzipan shaped like mulberries (toot) is a centuries-old tradition. Isfahan is the epicenter of Persian sweets."},
    {"name": "Torrone di Benevento", "lat": 41.1298, "lon": 14.7828,
     "desc": "Benevento, Italy — Claims to be the original home of Italian torrone. The name may derive from the Latin 'torreo' (to toast)."},
    {"name": "Turron de Jijona", "lat": 38.5422, "lon": -0.4880,
     "desc": "Jijona (Xixona), Alicante, Spain — Turron capital of Spain. Soft turron (Jijona) and hard turron (Alicante) made with Marcona almonds."},
    {"name": "Szaloncukor (Hungarian Fondant)", "lat": 47.4979, "lon": 19.0402,
     "desc": "Budapest, Hungary — Szaloncukor (parlor candy) is a Christmas tree decoration candy. Fondant, marzipan, and jelly varieties."},
    {"name": "Massepain of Saint-Leonard", "lat": 50.4953, "lon": 5.5734,
     "desc": "Saint-Leonard, Belgium — Belgian marzipan tradition. Speculoos-marzipan fusion and other Walloon confectionery specialties."},
    {"name": "Aleppo Nougat (Natef)", "lat": 36.2021, "lon": 37.1343,
     "desc": "Aleppo, Syria — Middle Eastern nougat traditions using natef (soapwort root foam), pistachios, and rosewater. Ancient confectionery heritage."},
    {"name": "Torrone Sardo", "lat": 40.1209, "lon": 9.0129,
     "desc": "Tonara, Sardinia, Italy — Sardinian nougat made with local honey and almonds. Tonara hosts an annual torrone festival."},
]

# ═══════════════════════════════════════════
# MODE 8: COTTON CANDY & FAIRGROUNDS
# ═══════════════════════════════════════════
COTTON_CANDY_DATA = [
    {"name": "Nashville (Cotton Candy Birthplace)", "lat": 36.1627, "lon": -86.7816,
     "desc": "Nashville, Tennessee, USA — Dentist William Morrison and confectioner John Wharton invented the first cotton candy machine in 1897."},
    {"name": "1904 St. Louis World's Fair", "lat": 38.6349, "lon": -90.2859,
     "desc": "St. Louis, Missouri, USA — Cotton candy was introduced to the masses at the 1904 World's Fair, selling 68,655 boxes at 25 cents each."},
    {"name": "Coney Island", "lat": 40.5749, "lon": -73.9859,
     "desc": "Brooklyn, New York, USA — Iconic American fairground where cotton candy became a boardwalk staple. Luna Park continues the tradition."},
    {"name": "Tivoli Gardens", "lat": 55.6736, "lon": 12.5681,
     "desc": "Copenhagen, Denmark — One of the world's oldest amusement parks (1843). Danish candyfloss (candy floss) is a beloved attraction treat."},
    {"name": "Oktoberfest Fairgrounds", "lat": 48.1319, "lon": 11.5497,
     "desc": "Munich, Germany — Zuckerwatte (cotton candy/sugar cotton) is a staple at the world's largest beer festival and folk fair since 1810."},
    {"name": "Blackpool Pleasure Beach", "lat": 53.7873, "lon": -3.0560,
     "desc": "Blackpool, UK — Iconic British seaside amusement park. Candy floss, toffee apples, and rock candy define the fairground experience."},
    {"name": "Prater Amusement Park", "lat": 48.2166, "lon": 16.3964,
     "desc": "Vienna, Austria — Historic Viennese amusement park (since 1766). Zuckerwatte and lebkuchen hearts are traditional fair sweets."},
    {"name": "Luna Park Melbourne", "lat": -37.8683, "lon": 144.9764,
     "desc": "Melbourne, Australia — Opened 1912, one of the world's oldest continually operating amusement parks. Fairy floss is the local name."},
    {"name": "Harajuku Cotton Candy", "lat": 35.6702, "lon": 139.7027,
     "desc": "Harajuku, Tokyo, Japan — Giant rainbow cotton candy (wataame) from Totti Candy Factory became a global social media sensation."},
    {"name": "Dussehra Mela Fairgrounds", "lat": 28.6328, "lon": 77.2197,
     "desc": "Delhi, India — Buddhi ke baal (old woman's hair) is the Hindi name for cotton candy sold at melas (fairs) across India."},
    {"name": "Hyde Park Winter Wonderland", "lat": 51.5073, "lon": -0.1657,
     "desc": "London, UK — Major seasonal fairground. Candy floss, toffee apples, and churros are the iconic sweet treats."},
    {"name": "Fete Foraine des Tuileries", "lat": 48.8634, "lon": 2.3275,
     "desc": "Paris, France — The Tuileries funfair features barbe a papa (daddy's beard — French cotton candy) as a beloved attraction."},
]

# ═══════════════════════════════════════════
# MODE 9: CARAMEL & TOFFEE
# ═══════════════════════════════════════════
CARAMEL_TOFFEE_DATA = [
    {"name": "Mackintosh's Toffee (Halifax)", "lat": 53.7246, "lon": -1.8580,
     "desc": "Halifax, West Yorkshire, UK — John Mackintosh invented modern toffee here in 1890 by combining English butterscotch with American caramel."},
    {"name": "Werther's Original (Storck)", "lat": 52.0302, "lon": 8.5325,
     "desc": "Halle (Westfalen), Germany — August Storck founded his candy company in 1903. Werther's Original caramel launched 1969, named after the town."},
    {"name": "Dulce de Leche Capital", "lat": -34.6037, "lon": -58.3816,
     "desc": "Buenos Aires, Argentina — Dulce de leche (caramelized milk) is Argentina's national sweet. Used in alfajores, ice cream, and cakes."},
    {"name": "Caramels d'Isigny", "lat": 49.3190, "lon": -1.1003,
     "desc": "Isigny-sur-Mer, Normandy, France — Famous for butter caramels made with Normandy's renowned AOP cream and butter since the 19th century."},
    {"name": "Callard & Bowser (London)", "lat": 51.5074, "lon": -0.1278,
     "desc": "London, UK — Callard & Bowser produced iconic British butterscotch and toffee since 1837. A Victorian-era confectionery legend."},
    {"name": "Havanna Alfajores", "lat": -38.0023, "lon": -57.5575,
     "desc": "Mar del Plata, Argentina — Havanna's dulce de leche alfajores (caramel sandwich cookies) are Argentina's most famous export candy."},
    {"name": "Thorntons Toffee", "lat": 52.9078, "lon": -1.3808,
     "desc": "Alfreton, Derbyshire, UK — Thorntons was founded in Sheffield in 1911. Special Toffee is their signature, still made to the original recipe."},
    {"name": "Breton Salted Caramel (Quiberon)", "lat": 47.4850, "lon": -3.1204,
     "desc": "Quiberon, Brittany, France — Henri Le Roux invented salted butter caramel (CBS) in 1977. Brittany's fleur de sel makes it unique."},
    {"name": "Confiteria del Molino", "lat": -34.6096, "lon": -58.3926,
     "desc": "Buenos Aires, Argentina — Iconic Art Nouveau confectionery (1916). Famous for caramel treats. Restored as national heritage landmark."},
    {"name": "Flodeboller & Karameller", "lat": 55.6761, "lon": 12.5683,
     "desc": "Copenhagen, Denmark — Danish karameller (soft caramels) by Toms, Anthon Berg, and others are a national confectionery tradition."},
    {"name": "Goetze's Caramel Creams", "lat": 39.2904, "lon": -76.6122,
     "desc": "Baltimore, Maryland, USA — Goetze's has made Caramel Creams and Cow Tales since 1895. A beloved American caramel candy."},
    {"name": "Cajeta de Celaya", "lat": 20.5235, "lon": -100.8157,
     "desc": "Celaya, Guanajuato, Mexico — Capital of cajeta (goat milk caramel). An essential Mexican confection with colonial-era origins."},
]

# ═══════════════════════════════════════════
# MODE 10: LOLLIPOP & ROCK CANDY
# ═══════════════════════════════════════════
LOLLIPOP_ROCK_DATA = [
    {"name": "Blackpool Rock", "lat": 53.8175, "lon": -3.0357,
     "desc": "Blackpool, Lancashire, UK — Seaside rock candy has been made here since 1887. Letters running through the stick are the hallmark."},
    {"name": "Chupa Chups Headquarters", "lat": 41.3874, "lon": 2.1686,
     "desc": "Barcelona, Spain — Enric Bernat invented Chupa Chups in 1958. Salvador Dali designed the famous daisy logo in 1969."},
    {"name": "Dum Dums (Spangler Candy)", "lat": 40.8756, "lon": -83.8888,
     "desc": "Bryan, Ohio, USA — Spangler Candy has produced Dum Dums lollipops since 1953. Over 2.5 billion produced per year."},
    {"name": "Tootsie Pop Factory", "lat": 41.8781, "lon": -87.6298,
     "desc": "Chicago, Illinois, USA — Tootsie Roll Industries has made Tootsie Pops since 1931. The mystery of 'how many licks' endures."},
    {"name": "See's Candies Lollipops", "lat": 37.7749, "lon": -122.4194,
     "desc": "San Francisco, California, USA — See's Candies, founded 1921, is known for chocolate lollipops and old-fashioned candy shop experience."},
    {"name": "Brighton Rock", "lat": 50.8225, "lon": -0.1372,
     "desc": "Brighton, UK — Immortalized in Graham Greene's 1938 novel 'Brighton Rock'. Traditional seaside rock candy sold along the pier."},
    {"name": "Edinburgh Rock", "lat": 55.9533, "lon": -3.1883,
     "desc": "Edinburgh, Scotland — Edinburgh rock is a crumbly, pastel-colored confection created by Alexander Ferguson in the 19th century."},
    {"name": "Nabat (Persian Rock Candy)", "lat": 35.6892, "lon": 51.3890,
     "desc": "Tehran, Iran — Nabat is saffron-infused rock candy on a stick. Traditionally served with Persian tea. Centuries-old tradition."},
    {"name": "Tanghulu (Chinese Candied Fruit)", "lat": 39.9042, "lon": 116.4074,
     "desc": "Beijing, China — Candied hawthorn berries on a stick, dating to the Song Dynasty. A beloved winter street treat across northern China."},
    {"name": "Kojak/Fiesta Lollipops", "lat": 40.4168, "lon": -3.7038,
     "desc": "Madrid, Spain — Fiesta brand lollipops and Kojak pops are Spanish candy icons. Distributed across Europe and Latin America."},
    {"name": "Candy Cane Origin (Cologne)", "lat": 50.9375, "lon": 6.9603,
     "desc": "Cologne, Germany — Legend says a choirmaster at Cologne Cathedral bent sugar sticks into canes in 1670 to quiet children during the nativity."},
    {"name": "Bob's Candies (Candy Cane)", "lat": 30.8327, "lon": -83.2785,
     "desc": "Albany, Georgia, USA — Bob McCormack perfected the candy cane in the 1920s. His brother-in-law invented the Keller Machine for automated production."},
]

# ═══════════════════════════════════════════
# MODE MAP (for selectbox label to data)
# ═══════════════════════════════════════════
MAP_MODES = {
    "World Candy & Sweet Traditions": {
        "data": CANDY_TRADITIONS,
        "color": CANDY_COLORS["traditions"],
        "icon_prefix": "Tradition",
        "zoom": 2,
        "center": [20.0, 0.0],
    },
    "Chocolate Factory Tours": {
        "data": CHOCOLATE_FACTORIES,
        "color": CANDY_COLORS["chocolate"],
        "icon_prefix": "Factory",
        "zoom": 2,
        "center": [30.0, 0.0],
    },
    "Candy Museums": {
        "data": CANDY_MUSEUMS,
        "color": CANDY_COLORS["museum"],
        "icon_prefix": "Museum",
        "zoom": 2,
        "center": [30.0, 0.0],
    },
    "Licorice Origins": {
        "data": LICORICE_ORIGINS,
        "color": CANDY_COLORS["licorice"],
        "icon_prefix": "Licorice",
        "zoom": 3,
        "center": [50.0, 15.0],
    },
    "Gummy Bear & Haribo": {
        "data": GUMMY_BEAR_DATA,
        "color": CANDY_COLORS["gummy"],
        "icon_prefix": "Gummy",
        "zoom": 3,
        "center": [48.0, 8.0],
    },
    "Chewing Gum History": {
        "data": CHEWING_GUM_DATA,
        "color": CANDY_COLORS["gum"],
        "icon_prefix": "Gum",
        "zoom": 2,
        "center": [30.0, 0.0],
    },
    "Marzipan & Nougat": {
        "data": MARZIPAN_NOUGAT_DATA,
        "color": CANDY_COLORS["marzipan"],
        "icon_prefix": "Nougat",
        "zoom": 3,
        "center": [45.0, 15.0],
    },
    "Cotton Candy & Fairgrounds": {
        "data": COTTON_CANDY_DATA,
        "color": CANDY_COLORS["cotton"],
        "icon_prefix": "Fair",
        "zoom": 2,
        "center": [35.0, 0.0],
    },
    "Caramel & Toffee": {
        "data": CARAMEL_TOFFEE_DATA,
        "color": CANDY_COLORS["caramel"],
        "icon_prefix": "Caramel",
        "zoom": 2,
        "center": [30.0, -10.0],
    },
    "Lollipop & Rock Candy": {
        "data": LOLLIPOP_ROCK_DATA,
        "color": CANDY_COLORS["lollipop"],
        "icon_prefix": "Lollipop",
        "zoom": 2,
        "center": [35.0, 0.0],
    },
}


# ═══════════════════════════════════════════
# HELPER: Build the folium map for a mode
# ═══════════════════════════════════════════
def _build_candy_map(mode_key: str) -> folium.Map:
    """Build a folium map with markers for the chosen candy mode."""
    cfg = MAP_MODES[mode_key]
    data = cfg["data"]
    color = cfg["color"]
    center = cfg["center"]
    zoom = cfg["zoom"]

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name=html_module.escape(mode_key)).add_to(m)

    for item in data:
        lat = item["lat"]
        lon = item["lon"]
        name = html_module.escape(item["name"])
        desc = html_module.escape(item["desc"])

        popup_html = (
            '<div style="max-width:260px;font-family:sans-serif;">'
            f'<strong style="color:{color};font-size:0.95rem;">{name}</strong><br/>'
            f'<span style="font-size:0.8rem;color:#ccc;">{desc}</span>'
            '</div>'
        )

        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=name,
        ).add_to(cluster)

    return m


# ═══════════════════════════════════════════
# HELPER: Build a DataFrame for a mode
# ═══════════════════════════════════════════
def _build_dataframe(mode_key: str) -> pd.DataFrame:
    """Build a pandas DataFrame for the chosen candy mode."""
    cfg = MAP_MODES[mode_key]
    rows = []
    for item in cfg["data"]:
        rows.append({
            "Name": item["name"],
            "Latitude": item["lat"],
            "Longitude": item["lon"],
            "Description": item["desc"],
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════
def render_candy_maps_tab():
    """Main render function for the Candy & Sweet Traditions Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header pink">
        <h4>Candy &amp; Sweet Traditions Explorer</h4>
        <p>Explore the world's candy heritage &mdash; chocolate factories, licorice origins, gummy bear history, fairground sweets, and more. All curated data, no API key required.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode selector ──
    mode = st.selectbox(
        "Choose a Candy Map",
        list(MAP_MODES.keys()),
        key="candy_mode_select",
    )

    st.markdown("---")

    cfg = MAP_MODES[mode]
    data = cfg["data"]
    color = cfg["color"]

    # ══════════════════════════════════════════
    # SECTION 1: Stats
    # ══════════════════════════════════════════
    total_locations = len(data)
    countries = set()
    for item in data:
        # Extract country from desc (last part after last comma or dash)
        desc = item["desc"]
        parts = desc.split(" — ")
        if len(parts) >= 1:
            location_part = parts[0]
            segments = location_part.split(", ")
            if len(segments) >= 2:
                countries.add(segments[-1].strip().rstrip("."))

    lats = [item["lat"] for item in data]
    lat_span = max(lats) - min(lats) if lats else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Locations", f"{total_locations}")
    with c2:
        st.metric("Countries/Regions", f"{len(countries)}")
    with c3:
        st.metric("Latitude Span", f"{lat_span:.1f}\u00b0")
    with c4:
        st.metric("Category", html_module.escape(mode))

    # ══════════════════════════════════════════
    # SECTION 2: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {html_module.escape(mode)} Map")

    # Color legend
    st.markdown(f"""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin-bottom:0.75rem;">
        <span style="color:{color}; font-size:0.8rem;">&#9679; {html_module.escape(mode)}</span>
        <span style="color:#8b97b0; font-size:0.8rem;">Click markers for details</span>
    </div>
    """, unsafe_allow_html=True)

    m = _build_candy_map(mode)
    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 3: Location Cards
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Location Details")

    for item in data:
        name = html_module.escape(item["name"])
        desc = html_module.escape(item["desc"])
        lat = item["lat"]
        lon = item["lon"]

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
            <div style="width:50px; height:50px; border-radius:50%; background:{color}20;
                        display:flex; align-items:center; justify-content:center;
                        margin-right:0.75rem; flex-shrink:0;">
                <span style="color:{color}; font-weight:800; font-size:1.1rem;">&#127852;</span>
            </div>
            <div style="flex:1;">
                <div style="color:#e8ecf4; font-weight:600; font-size:0.9rem;">{name}</div>
                <div style="color:#8b97b0; font-size:0.78rem;">{desc}</div>
                <div style="color:#5a6580; font-size:0.7rem;">Lat: {lat:.4f}, Lon: {lon:.4f}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 4: Data Table
    # ══════════════════════════════════════════
    st.markdown("---")
    df = _build_dataframe(mode)

    with st.expander(f"Full Data Table ({len(df)} locations)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 5: CSV Download
    # ══════════════════════════════════════════
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    safe_filename = mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        f"Download {len(df)} {html_module.escape(mode)} Locations (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"candy_{safe_filename}.csv",
        mime="text/csv",
        key="candy_csv_download",
    )
