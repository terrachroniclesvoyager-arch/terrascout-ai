"""
Ice Cream & Gelato Explorer module for TerraScout AI.
Curated maps of the world's best ice cream, gelato, sorbet, and frozen dessert
destinations across 10 themed modes. All data is preset (no external API needed).
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
import requests
import html as html_module
from streamlit.components.v1 import html as st_html


# ═══════════════════════════════════════════
# COLOR PALETTE
# ═══════════════════════════════════════════
MODE_COLORS = {
    "Italian Gelato Heritage": "#f59e0b",
    "Japanese Soft Serve & Mochi": "#ec4899",
    "Turkish Dondurma": "#ef4444",
    "American Ice Cream Trail": "#3b82f6",
    "French Sorbet & Glacier": "#8b5cf6",
    "Belgian Waffle & Ice Cream": "#f97316",
    "Artisan Ice Cream Makers": "#10b981",
    "Ice Cream Museums": "#06b6d4",
    "Historic Ice Cream Origins": "#a855f7",
    "Street Ice Cream Vendors": "#14b8a6",
}


# ═══════════════════════════════════════════
# PRESET DATA — 10 MODES
# ═══════════════════════════════════════════

ITALIAN_GELATO = [
    {"name": "Gelateria dei Neri", "lat": 43.7696, "lon": 11.2610, "city": "Florence", "desc": "Legendary Florentine gelateria known for ricotta & fig and crema fiorentina flavors."},
    {"name": "Giolitti", "lat": 41.8997, "lon": 12.4778, "city": "Rome", "desc": "Historic Roman gelateria since 1890, served gelato to kings and popes."},
    {"name": "Gelateria La Carraia", "lat": 43.7696, "lon": 11.2466, "city": "Florence", "desc": "Beloved spot on the Arno with huge portions and classic Tuscan flavors."},
    {"name": "Il Gelato di San Crispino", "lat": 41.9024, "lon": 12.4839, "city": "Rome", "desc": "Near the Trevi Fountain; famous for pure natural ingredients, no artificial colors."},
    {"name": "Gelateria Dondoli", "lat": 43.4676, "lon": 11.0462, "city": "San Gimignano", "desc": "World Gelato Champion Sergio Dondoli, known for Vernaccia sorbet and saffron cream."},
    {"name": "Suso Gelatoteca", "lat": 45.4350, "lon": 12.3374, "city": "Venice", "desc": "Venice's tiny gem near Piazza San Marco with creative seasonal flavors."},
    {"name": "Gelato Museum Carpigiani", "lat": 44.5234, "lon": 11.2809, "city": "Bologna (Anzola Emilia)", "desc": "The world's only museum dedicated to the history and art of gelato."},
    {"name": "Gelateria Alberto Marchetti", "lat": 45.0703, "lon": 7.6869, "city": "Turin", "desc": "Slow-food philosophy gelato using Piedmontese hazelnuts and local dairy."},
    {"name": "I Tre Scalini", "lat": 41.8987, "lon": 12.4726, "city": "Rome", "desc": "Piazza Navona institution famous for its tartufo — chocolate gelato truffle since 1946."},
    {"name": "Gelateria Gianni", "lat": 44.4940, "lon": 11.3464, "city": "Bologna", "desc": "Beloved Bologna gelateria known for pistachio and stracciatella since 1957."},
    {"name": "La Sorbetteria Castiglione", "lat": 44.4882, "lon": 11.3533, "city": "Bologna", "desc": "Artisan sorbets and gelato using organic Sicilian almonds and pistachios."},
    {"name": "Ciacco Gelato", "lat": 43.7697, "lon": 11.2557, "city": "Florence", "desc": "Experimental flavors from a chemistry-trained gelatiere — rosemary, blue cheese, wasabi."},
    {"name": "Gelateria Pepino", "lat": 45.0649, "lon": 7.6819, "city": "Turin", "desc": "Inventor of the Pinguino — the first chocolate-covered gelato on a stick (1939)."},
    {"name": "Gelateria Cesare", "lat": 38.1090, "lon": 13.3616, "city": "Palermo", "desc": "Sicilian gelato with jasmine, mulberry, and ricotta-pistachio brioche."},
    {"name": "Bar Ercole", "lat": 37.5178, "lon": 15.0861, "city": "Catania", "desc": "Famous for granita with brioche — the Catanese breakfast tradition."},
]

JAPANESE_ICE_CREAM = [
    {"name": "Cremia (Daimaru Tokyo)", "lat": 35.6812, "lon": 139.7671, "city": "Tokyo", "desc": "Ultra-premium soft serve with Hokkaido milk and langues de chat cone."},
    {"name": "Tsujiri Gion", "lat": 35.0036, "lon": 135.7747, "city": "Kyoto", "desc": "Historic matcha house since 1860 serving rich matcha soft serve and parfaits."},
    {"name": "Nanaya Aoyama", "lat": 35.6647, "lon": 139.7142, "city": "Tokyo", "desc": "World's richest matcha gelato with 7 levels of matcha intensity."},
    {"name": "Daily Chiko (Nishiki Market)", "lat": 35.0054, "lon": 135.7639, "city": "Kyoto", "desc": "Towering soft serve stacks in soy sauce, sesame, matcha, and seasonal flavors."},
    {"name": "Mochi Ice Cream Yukimi Daifuku (Lotte HQ)", "lat": 35.6285, "lon": 139.7402, "city": "Tokyo", "desc": "Birthplace of Yukimi Daifuku — mochi-wrapped ice cream since 1981."},
    {"name": "Funawacha", "lat": 35.6622, "lon": 139.7010, "city": "Tokyo (Jiyugaoka)", "desc": "Sweet potato and hojicha soft serve — traditional Japanese wagashi meets ice cream."},
    {"name": "Suzukien Asakusa", "lat": 35.7148, "lon": 139.7968, "city": "Tokyo", "desc": "Claims world's strongest matcha gelato, 7-level intensity scale."},
    {"name": "Nana's Green Tea", "lat": 34.6937, "lon": 135.5023, "city": "Osaka", "desc": "Chain famous for matcha soft serve floats and houjicha lattes."},
    {"name": "Yubari Melon Soft Serve", "lat": 43.0618, "lon": 141.3545, "city": "Sapporo", "desc": "Hokkaido's famous Yubari melon soft serve, available at melon farms."},
    {"name": "Blue Seal Ice Cream", "lat": 26.3344, "lon": 127.7600, "city": "Okinawa", "desc": "American-Okinawan hybrid brand with beni-imo (purple sweet potato) and sugarcane."},
    {"name": "Taiyaki Ice Cream (Kurikoan)", "lat": 35.6595, "lon": 139.7006, "city": "Tokyo (Shibuya)", "desc": "Soft serve stuffed inside a hot fish-shaped taiyaki waffle."},
    {"name": "Otaru LeTAO", "lat": 43.1907, "lon": 140.9947, "city": "Otaru", "desc": "Double fromage soft serve — layered cheesecake-flavored ice cream in Hokkaido."},
]

TURKISH_DONDURMA = [
    {"name": "Kahramanmaras Dondurma Bazaar", "lat": 37.5847, "lon": 36.9228, "city": "Kahramanmaras", "desc": "The birthplace of stretchy Turkish ice cream, made with mastic and salep orchid root."},
    {"name": "Mado", "lat": 41.0082, "lon": 28.9784, "city": "Istanbul (Sultanahmet)", "desc": "Famous chain from Maras serving authentic dondurma with theatrical stretching."},
    {"name": "Yasar Usta Dondurma", "lat": 37.5858, "lon": 36.9237, "city": "Kahramanmaras", "desc": "Multi-generational master dondurma maker, considered the finest in the city."},
    {"name": "Mini Dondurma", "lat": 41.0370, "lon": 28.9850, "city": "Istanbul (Beyoglu)", "desc": "Istiklal Avenue institution — watch vendors perform dondurma tricks."},
    {"name": "Dondurma Dunyasi", "lat": 36.8841, "lon": 30.7056, "city": "Antalya", "desc": "Popular Antalya dondurma spot with pomegranate and fig flavors."},
    {"name": "Mevlana Dondurma", "lat": 37.8715, "lon": 32.5037, "city": "Konya", "desc": "Near Mevlana Museum; traditional Konya-style frozen desserts."},
    {"name": "Hafiz Mustafa 1864", "lat": 41.0105, "lon": 28.9753, "city": "Istanbul (Eminonu)", "desc": "Historic Ottoman confectioner since 1864, now famed for dondurma and baklava."},
    {"name": "Baylan Pastanesi", "lat": 40.9900, "lon": 29.0255, "city": "Istanbul (Kadikoy)", "desc": "Iconic 1920s patisserie on the Asian side — famous for kup griye ice cream."},
    {"name": "Saray Muhallebicisi", "lat": 41.0340, "lon": 28.9770, "city": "Istanbul (Beyoglu)", "desc": "Ottoman-era milk pudding house, also serving traditional kazandibi ice cream."},
    {"name": "Ali Usta Dondurma", "lat": 38.7312, "lon": 35.4827, "city": "Kayseri", "desc": "Central Anatolian dondurma master known for dense, chewy texture."},
]

AMERICAN_ICE_CREAM = [
    {"name": "Ben & Jerry's Factory", "lat": 44.3534, "lon": -72.8696, "city": "Waterbury, VT", "desc": "Iconic Vermont factory tour — birthplace of Cherry Garcia and Chunky Monkey."},
    {"name": "Jeni's Splendid Ice Creams", "lat": 39.9860, "lon": -83.0036, "city": "Columbus, OH", "desc": "Pioneering artisan brand famous for Salty Caramel and Brambleberry Crisp."},
    {"name": "Salt & Straw", "lat": 45.5231, "lon": -122.6765, "city": "Portland, OR", "desc": "Creative Portland-born brand with honey lavender, pear & blue cheese."},
    {"name": "Bi-Rite Creamery", "lat": 37.7615, "lon": -122.4264, "city": "San Francisco, CA", "desc": "Mission District legend with salted caramel, balsamic strawberry."},
    {"name": "Van Leeuwen", "lat": 40.7128, "lon": -74.0060, "city": "New York, NY", "desc": "Brooklyn-born vegan & classic ice cream truck turned empire."},
    {"name": "Graeter's Ice Cream", "lat": 39.1399, "lon": -84.4979, "city": "Cincinnati, OH", "desc": "French Pot process since 1870 — massive chocolate chips in Black Raspberry Chocolate Chip."},
    {"name": "McConnell's Fine Ice Creams", "lat": 34.4208, "lon": -119.6982, "city": "Santa Barbara, CA", "desc": "Central Coast creamery since 1949 using local dairy and eureka lemons."},
    {"name": "Leopold's Ice Cream", "lat": 32.0809, "lon": -81.0912, "city": "Savannah, GA", "desc": "Southern institution since 1919 — Tutti Frutti recipe unchanged for a century."},
    {"name": "Bassett's Ice Cream", "lat": 39.9536, "lon": -75.1592, "city": "Philadelphia, PA", "desc": "America's oldest ice cream company, at Reading Terminal Market since 1861."},
    {"name": "Ted Drewes Frozen Custard", "lat": 38.5891, "lon": -90.3015, "city": "St. Louis, MO", "desc": "Route 66 frozen custard stand since 1929 — concretes so thick they're served upside down."},
    {"name": "Ample Hills Creamery", "lat": 40.6782, "lon": -73.9442, "city": "Brooklyn, NY", "desc": "Prospect Heights favorite with Ooey Gooey Butter Cake and Snap Crackle Pop."},
    {"name": "Toscanini's", "lat": 42.3650, "lon": -71.1036, "city": "Cambridge, MA", "desc": "MIT-area gelateria dubbed 'the best ice cream in the world' by the New York Times."},
    {"name": "Amy's Ice Creams", "lat": 30.2672, "lon": -97.7431, "city": "Austin, TX", "desc": "Austin original with Mexican vanilla and crush'n mix-ins since 1984."},
    {"name": "Handel's Homemade Ice Cream", "lat": 41.0997, "lon": -80.6495, "city": "Youngstown, OH", "desc": "Small-batch Ohio creamery since 1945 with over 100 rotating flavors."},
]

FRENCH_SORBET = [
    {"name": "Berthillon", "lat": 48.8516, "lon": 2.3565, "city": "Paris (Ile Saint-Louis)", "desc": "Paris's most legendary glacier since 1954 — wild strawberry, caramel au beurre sale."},
    {"name": "Une Glace a Paris", "lat": 48.8600, "lon": 2.3522, "city": "Paris (Marais)", "desc": "MOF (Meilleur Ouvrier de France) glacier with inventive seasonal sorbets."},
    {"name": "Glacier Amorino", "lat": 48.8534, "lon": 2.3488, "city": "Paris (Saint-Germain)", "desc": "Italian-French flower-shaped gelato cones with organic ingredients."},
    {"name": "Maison Pillon", "lat": 43.6961, "lon": 7.2719, "city": "Nice", "desc": "Provencal glacier with lavender, olive oil, and fig sorbets."},
    {"name": "Fenocchio", "lat": 43.6977, "lon": 7.2761, "city": "Nice (Vieux Nice)", "desc": "Over 100 flavors including thyme, tomato-basil, and black olive."},
    {"name": "La Fabrique Givree", "lat": 48.8672, "lon": 2.3638, "city": "Paris (Canal Saint-Martin)", "desc": "Organic craft glacier using seasonal French fruits and raw milk."},
    {"name": "Glacier Vilfeu", "lat": 43.2965, "lon": 5.3698, "city": "Marseille", "desc": "Marseillais glacier known for pastis sorbet and calisson ice cream."},
    {"name": "Maison Weiss", "lat": 45.4327, "lon": 4.3872, "city": "Saint-Etienne", "desc": "Chocolatier-glacier with grand cru chocolate sorbets since 1882."},
    {"name": "Raimo Glacier", "lat": 48.8476, "lon": 2.3935, "city": "Paris (12e)", "desc": "Italian-French house since 1947, famous for marron glace and nougat."},
    {"name": "Le Bac a Glaces", "lat": 48.8566, "lon": 2.3255, "city": "Paris (7e)", "desc": "Neighborhood glacier near the Eiffel Tower with seasonal French fruit sorbets."},
]

BELGIAN_WAFFLE_ICE = [
    {"name": "Chez Albert", "lat": 50.6460, "lon": 5.5733, "city": "Liege", "desc": "The quintessential Liege waffle with pearl sugar, topped with house-made ice cream."},
    {"name": "Maison Dandoy", "lat": 50.8485, "lon": 4.3528, "city": "Brussels (Grand Place)", "desc": "Brussels waffle dynasty since 1829 — crispy rectangles with speculoos ice cream."},
    {"name": "Glacier Zizi", "lat": 50.8466, "lon": 4.3514, "city": "Brussels", "desc": "Near Grand Place; Belgian chocolate ice cream on warm waffles."},
    {"name": "Otomat Waffle & Ice", "lat": 51.0543, "lon": 3.7174, "city": "Ghent", "desc": "Ghent hotspot combining Belgian waffles with artisan gelato."},
    {"name": "Glacier Capoue", "lat": 50.6428, "lon": 5.5684, "city": "Liege", "desc": "Artisan glacier with Belgian chocolate, speculoos, and seasonal fruit sorbets."},
    {"name": "Het Moment", "lat": 51.2194, "lon": 4.4025, "city": "Antwerp", "desc": "Antwerp ice cream bar with waffle sandwiches and local craft flavors."},
    {"name": "De Gouden Saep", "lat": 51.0490, "lon": 3.7249, "city": "Ghent", "desc": "Traditional Belgian ice salon in the heart of medieval Ghent."},
    {"name": "Cremerie De Linkebeek", "lat": 50.7679, "lon": 4.3312, "city": "Linkebeek (Brussels area)", "desc": "Suburban Brussels creamery famous for farm-fresh dairy ice cream."},
    {"name": "Lizzyco Ice Cream Parlour", "lat": 51.2093, "lon": 3.2247, "city": "Bruges", "desc": "Bruges canal-side parlour with Belgian praline and white chocolate ice cream."},
    {"name": "Ijssalon Verdonck", "lat": 51.0559, "lon": 3.7193, "city": "Ghent", "desc": "Ghent's oldest ice cream salon — classic Flemish flavors since 1948."},
]

ARTISAN_MAKERS = [
    {"name": "Gelato Messina", "lat": -33.8830, "lon": 151.2171, "city": "Sydney, Australia", "desc": "Australia's gelato phenomenon with rotating weekly specials and lab-style innovation."},
    {"name": "Gelupo", "lat": 51.5116, "lon": -0.1363, "city": "London, UK", "desc": "Soho gelateria from the team behind Bocca di Lupo — ricotta & sour cherry."},
    {"name": "Heladeria Cadore", "lat": -34.6037, "lon": -58.4116, "city": "Buenos Aires, Argentina", "desc": "Legendary Buenos Aires heladeria — dulce de leche granizado since 1957."},
    {"name": "Murphy's Ice Cream", "lat": 52.1406, "lon": -10.2686, "city": "Dingle, Ireland", "desc": "Wild Atlantic Way creamery using Kerry cow milk and Dingle sea salt."},
    {"name": "Perche No!", "lat": 43.7706, "lon": 11.2540, "city": "Florence, Italy", "desc": "Creative Florentine gelateria with black sesame and Sicilian almond."},
    {"name": "Eismanufaktur", "lat": 52.5200, "lon": 13.4050, "city": "Berlin, Germany", "desc": "Berlin's craft ice cream maker with liquid nitrogen techniques and local herbs."},
    {"name": "Rocambolesc", "lat": 41.9794, "lon": 2.8214, "city": "Girona, Spain", "desc": "From the Roca brothers (El Celler de Can Roca) — Michelin-star ice cream."},
    {"name": "Lucciano's", "lat": -34.6126, "lon": -58.3642, "city": "Buenos Aires, Argentina", "desc": "Natural gelato with edible art — each scoop printed with chocolate imagery."},
    {"name": "Giapo", "lat": -36.8485, "lon": 174.7633, "city": "Auckland, New Zealand", "desc": "Boundary-pushing ice cream sculptures and avant-garde frozen desserts."},
    {"name": "Anita Gelato", "lat": 32.0853, "lon": 34.7818, "city": "Tel Aviv, Israel", "desc": "Massive portions of halva, tahini, and Middle Eastern-inspired gelato."},
    {"name": "Chin Chin Labs", "lat": 51.5402, "lon": -0.1432, "city": "London (Camden)", "desc": "Liquid nitrogen ice cream made to order — the UK's first nitrogen parlour."},
    {"name": "Messina (Darlinghurst)", "lat": -33.8775, "lon": 151.2208, "city": "Sydney, Australia", "desc": "Original flagship of Gelato Messina with queues down the block nightly."},
]

ICE_CREAM_MUSEUMS = [
    {"name": "Gelato Museum Carpigiani", "lat": 44.5234, "lon": 11.2809, "city": "Bologna, Italy", "desc": "World's only museum dedicated to gelato history, science, and culture."},
    {"name": "Museum of Ice Cream (NYC)", "lat": 40.7223, "lon": -73.9928, "city": "New York, USA", "desc": "Immersive pop-culture ice cream experience with sprinkle pool and tastings."},
    {"name": "Museum of Ice Cream (Singapore)", "lat": 1.2846, "lon": 103.8607, "city": "Singapore", "desc": "Dempsey Hill location with 14 multi-sensory installations."},
    {"name": "Museum of Ice Cream (Chicago)", "lat": 41.8884, "lon": -87.6355, "city": "Chicago, USA", "desc": "Michigan Avenue experience with ice cream-themed art and unlimited tastings."},
    {"name": "Ice Cream Farm (Cheshire)", "lat": 53.1175, "lon": -2.6953, "city": "Tattenhall, UK", "desc": "UK's largest ice cream attraction — farm, parlour, and adventure play."},
    {"name": "Walls Ice Cream Museum", "lat": 51.5074, "lon": -0.1278, "city": "London, UK", "desc": "Pop-up exhibitions celebrating over 100 years of Walls ice cream history."},
    {"name": "Haagen-Dazs Experience (Bronx)", "lat": 40.8448, "lon": -73.8648, "city": "Bronx, NY", "desc": "Brand experience center near the original factory location."},
    {"name": "Sweet Museum", "lat": 48.8606, "lon": 2.3376, "city": "Paris, France", "desc": "Dessert and ice cream focused interactive museum near the Louvre."},
    {"name": "Sweets Museum", "lat": 35.6595, "lon": 139.7006, "city": "Tokyo (Shibuya)", "desc": "Japanese kawaii dessert museum with ice cream art installations."},
    {"name": "Dessert Museum Manila", "lat": 14.5547, "lon": 121.0244, "city": "Manila, Philippines", "desc": "8 themed rooms including the Cotton Candy Room and Ice Cream Room."},
]

HISTORIC_ORIGINS = [
    {"name": "Persepolis (Persian faloodeh origin)", "lat": 29.9343, "lon": 52.8914, "city": "Shiraz, Iran", "desc": "Ancient Persia invented faloodeh — frozen rosewater vermicelli — over 2,500 years ago."},
    {"name": "Tang Dynasty Ice Cream (Xi'an)", "lat": 34.2658, "lon": 108.9541, "city": "Xi'an, China", "desc": "Tang Dynasty nobles froze buffalo milk with camphor — among earliest ice cream records (618-907 AD)."},
    {"name": "Arab Sharbat Heritage (Damascus)", "lat": 33.5138, "lon": 36.2765, "city": "Damascus, Syria", "desc": "Arabic sharbat (sherbet) tradition — chilled fruit drinks that evolved into sorbet."},
    {"name": "Marco Polo's Venice", "lat": 45.4408, "lon": 12.3155, "city": "Venice, Italy", "desc": "Legend says Marco Polo brought frozen dessert recipes from China to Italy (c. 1295)."},
    {"name": "Catherine de Medici's Florence", "lat": 43.7696, "lon": 11.2558, "city": "Florence, Italy", "desc": "When Catherine de Medici married into French royalty (1533), she brought Italian sorbetto to France."},
    {"name": "Procopio Cafe (Cafe Procope)", "lat": 48.8530, "lon": 2.3397, "city": "Paris, France", "desc": "Sicilian Francesco Procopio opened the first cafe serving gelato to the public in 1686."},
    {"name": "Dolley Madison's White House", "lat": 38.8977, "lon": -77.0365, "city": "Washington, DC", "desc": "First Lady Dolley Madison served strawberry ice cream at the 1813 Inaugural Ball."},
    {"name": "Jacob Fussell's Factory", "lat": 39.2904, "lon": -76.6122, "city": "Baltimore, MD", "desc": "Jacob Fussell opened the first commercial ice cream factory in 1851."},
    {"name": "Augustus Jackson's Philadelphia", "lat": 39.9526, "lon": -75.1652, "city": "Philadelphia, PA", "desc": "Augustus Jackson, 'Father of Ice Cream,' improved recipes and distribution in the 1830s."},
    {"name": "Italo Marchioni (Ice Cream Cone)", "lat": 40.7128, "lon": -74.0060, "city": "New York, NY", "desc": "Italian immigrant Italo Marchioni patented the ice cream cone mold in 1903."},
    {"name": "1904 St. Louis World's Fair", "lat": 38.6353, "lon": -90.2845, "city": "St. Louis, MO", "desc": "The waffle cone legend — a waffle vendor rolled his waffles for an ice cream seller who ran out of cups."},
    {"name": "Mughal Kulfi (Delhi)", "lat": 28.6139, "lon": 77.2090, "city": "Delhi, India", "desc": "Mughal emperors enjoyed kulfi — dense frozen milk with saffron and cardamom — from the 16th century."},
]

STREET_VENDORS = [
    {"name": "Kulfi Carts, Chandni Chowk", "lat": 28.6506, "lon": 77.2301, "city": "Delhi, India", "desc": "Old Delhi's iconic matka kulfi carts — dense cardamom-pistachio kulfi from clay pots."},
    {"name": "Kulfi Faluda, Mohammed Ali Road", "lat": 18.9570, "lon": 72.8318, "city": "Mumbai, India", "desc": "Famous Mumbai street kulfi-falooda with vermicelli, rose syrup, and saffron."},
    {"name": "Helado de Paila, Ibarra", "lat": 0.3392, "lon": -78.1225, "city": "Ibarra, Ecuador", "desc": "Traditional Ecuadorian ice cream hand-churned in copper pails over straw and ice."},
    {"name": "Nieves de Garrafa, Oaxaca", "lat": 17.0732, "lon": -96.7266, "city": "Oaxaca, Mexico", "desc": "Hand-churned wooden barrel sorbets — mezcal, tuna (prickly pear), leche quemada."},
    {"name": "Ais Kacang, Penang", "lat": 5.4164, "lon": 100.3327, "city": "Penang, Malaysia", "desc": "Shaved ice mountain with red beans, sweet corn, grass jelly, and condensed milk."},
    {"name": "Halo-Halo, Quiapo Manila", "lat": 14.5988, "lon": 120.9836, "city": "Manila, Philippines", "desc": "Filipino crushed ice with ube, leche flan, sweet beans, and macapuno."},
    {"name": "Es Campur Carts, Yogyakarta", "lat": -7.7956, "lon": 110.3695, "city": "Yogyakarta, Indonesia", "desc": "Mixed ice dessert with coconut, avocado, jackfruit, and condensed milk."},
    {"name": "Paleta Carts, Mexico City", "lat": 19.4326, "lon": -99.1332, "city": "Mexico City, Mexico", "desc": "Paleteros pushing carts of fresh fruit paletas — mango-chili, tamarindo, coconut."},
    {"name": "Dondurma Street Vendors, Taksim", "lat": 41.0370, "lon": 28.9850, "city": "Istanbul, Turkey", "desc": "Theatrical Turkish ice cream vendors who tease customers with stretchy dondurma tricks."},
    {"name": "Bingsu Street, Myeongdong", "lat": 37.5636, "lon": 126.9869, "city": "Seoul, South Korea", "desc": "Korean shaved ice (bingsu) with red bean, mochi, and injeolmi powder."},
    {"name": "Cendol Stalls, Melaka", "lat": 2.1896, "lon": 102.2501, "city": "Melaka, Malaysia", "desc": "Green pandan jelly noodles in coconut milk and gula melaka over shaved ice."},
    {"name": "Raspados, Guadalajara", "lat": 20.6597, "lon": -103.3496, "city": "Guadalajara, Mexico", "desc": "Mexican shaved ice with chamoy, tamarind, mango, and lime juice."},
    {"name": "Chendol Street Cart, Singapore", "lat": 1.2814, "lon": 103.8450, "city": "Singapore", "desc": "Hawker-style chendol with pandan noodles, red beans, and palm sugar."},
    {"name": "Booza Carts, Beirut", "lat": 33.8938, "lon": 35.5018, "city": "Beirut, Lebanon", "desc": "Lebanese stretchy ice cream (booza) pounded with mastic, served from street carts."},
]


# ═══════════════════════════════════════════
# MAP MODE REGISTRY
# ═══════════════════════════════════════════
MAP_MODES = {
    "Italian Gelato Heritage": {
        "data": ITALIAN_GELATO,
        "center": [42.5, 12.5],
        "zoom": 6,
        "desc": "Famous gelato shops in Italy, gelato museums, and the birthplaces of legendary flavors.",
        "color": "#f59e0b",
    },
    "Japanese Soft Serve & Mochi": {
        "data": JAPANESE_ICE_CREAM,
        "center": [36.2, 138.2],
        "zoom": 6,
        "desc": "Unique Japanese ice cream flavors, matcha masters, mochi ice cream, and taiyaki cones.",
        "color": "#ec4899",
    },
    "Turkish Dondurma": {
        "data": TURKISH_DONDURMA,
        "center": [39.0, 32.0],
        "zoom": 6,
        "desc": "Stretchy Turkish dondurma from Kahramanmaras to Istanbul, made with mastic and salep.",
        "color": "#ef4444",
    },
    "American Ice Cream Trail": {
        "data": AMERICAN_ICE_CREAM,
        "center": [39.5, -98.0],
        "zoom": 4,
        "desc": "Ben & Jerry's, historic creameries, artisan scoops, and frozen custard stands across the USA.",
        "color": "#3b82f6",
    },
    "French Sorbet & Glacier": {
        "data": FRENCH_SORBET,
        "center": [46.6, 2.2],
        "zoom": 6,
        "desc": "Berthillon, Parisian glaciers, Provencal sorbets, and MOF-certified ice cream artisans.",
        "color": "#8b5cf6",
    },
    "Belgian Waffle & Ice Cream": {
        "data": BELGIAN_WAFFLE_ICE,
        "center": [50.8, 4.4],
        "zoom": 8,
        "desc": "Belgian waffle houses with artisan ice cream, from Brussels to Bruges to Liege.",
        "color": "#f97316",
    },
    "Artisan Ice Cream Makers": {
        "data": ARTISAN_MAKERS,
        "center": [20.0, 0.0],
        "zoom": 2,
        "desc": "World-class craft ice cream factories and gelaterias from Sydney to Buenos Aires.",
        "color": "#10b981",
    },
    "Ice Cream Museums": {
        "data": ICE_CREAM_MUSEUMS,
        "center": [30.0, -20.0],
        "zoom": 2,
        "desc": "Ice cream and dessert museums worldwide — immersive, interactive, and delicious.",
        "color": "#06b6d4",
    },
    "Historic Ice Cream Origins": {
        "data": HISTORIC_ORIGINS,
        "center": [35.0, 30.0],
        "zoom": 3,
        "desc": "Where ice cream was invented: Persian faloodeh, Tang Dynasty milk ice, Marco Polo legend, and more.",
        "color": "#a855f7",
    },
    "Street Ice Cream Vendors": {
        "data": STREET_VENDORS,
        "center": [15.0, 80.0],
        "zoom": 3,
        "desc": "Kulfi carts in India, helado in Mexico, ais kacang in SE Asia, bingsu in Korea.",
        "color": "#14b8a6",
    },
}


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════
def render_ice_cream_maps_tab():
    """Main render function for the Ice Cream & Gelato Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header pink">
        <h4>Ice Cream & Gelato Explorer</h4>
        <p>Discover the world's finest frozen desserts &mdash; from Italian gelato heritage to Japanese soft serve, Turkish dondurma, street kulfi carts, and ice cream museums.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode Selector ──
    mode = st.selectbox(
        "Choose a Map Mode",
        list(MAP_MODES.keys()),
        key="icecream_mode",
    )

    mode_info = MAP_MODES[mode]
    data = mode_info["data"]
    center = mode_info["center"]
    zoom = mode_info["zoom"]
    accent = mode_info["color"]

    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem;">{html_module.escape(mode_info["desc"])}</p>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ══════════════════════════════════════════
    # STATS ROW
    # ══════════════════════════════════════════
    cities = set(item["city"] for item in data)
    countries = set()
    for item in data:
        city = item["city"]
        # Extract country hint from city string (after last comma)
        parts = city.split(",")
        if len(parts) > 1:
            countries.add(parts[-1].strip())
        else:
            countries.add(city)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Locations", len(data))
    with c2:
        st.metric("Cities", len(cities))
    with c3:
        st.metric("Regions", len(countries))

    st.markdown("---")

    # ══════════════════════════════════════════
    # FOLIUM MAP
    # ══════════════════════════════════════════
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name="Ice Cream Locations").add_to(m)

    for item in data:
        safe_name = html_module.escape(item["name"])
        safe_city = html_module.escape(item["city"])
        safe_desc = html_module.escape(item["desc"])

        popup_html = (
            f'<div style="max-width:240px; background:#1a2235; color:#e8ecf4; '
            f'padding:10px; border-radius:8px; border-left:4px solid {accent};">'
            f'<b style="color:{accent}; font-size:0.9rem;">{safe_name}</b><br/>'
            f'<span style="color:#8b97b0; font-size:0.8rem;">{safe_city}</span><br/>'
            f'<span style="color:#e8ecf4; font-size:0.78rem;">{safe_desc}</span>'
            f'</div>'
        )

        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=accent,
            fill=True,
            fill_color=accent,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=safe_name,
        ).add_to(cluster)

    folium.LayerControl().add_to(m)
    st_html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # LOCATION CARDS
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Featured Locations")

    for item in data:
        safe_name = html_module.escape(item["name"])
        safe_city = html_module.escape(item["city"])
        safe_desc = html_module.escape(item["desc"])

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
            <div style="width:8px; height:56px; border-radius:4px; background:{accent};
                        margin-right:0.75rem; flex-shrink:0;"></div>
            <div style="flex:1;">
                <div style="color:#e8ecf4; font-weight:600; font-size:0.88rem;">{safe_name}</div>
                <div style="color:{accent}; font-size:0.78rem;">{safe_city}</div>
                <div style="color:#8b97b0; font-size:0.75rem;">{safe_desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # DATA TABLE
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Data Table")

    rows = []
    for item in data:
        rows.append({
            "Name": item["name"],
            "City": item["city"],
            "Latitude": item["lat"],
            "Longitude": item["lon"],
            "Description": item["desc"],
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    # ══════════════════════════════════════════
    # CSV DOWNLOAD
    # ══════════════════════════════════════════
    st.markdown("---")
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)

    safe_mode_filename = mode.lower().replace(" ", "_").replace("&", "and").replace("'", "")
    st.download_button(
        f"Download {len(data)} Locations (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"ice_cream_{safe_mode_filename}.csv",
        mime="text/csv",
        key="icecream_download",
    )
