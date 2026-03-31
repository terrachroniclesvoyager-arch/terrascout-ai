# -*- coding: utf-8 -*-
"""
Bread & Bakery Heritage Explorer module for TerraScout AI.
Provides 10 interactive map modes covering French boulangerie heritage,
German bread traditions, Italian bread & focaccia, sourdough heritage,
Middle Eastern flatbreads, Asian bread traditions, ancient bread history,
artisan bakeries worldwide, bread festivals & markets, and bread museums & schools.
All data is hardcoded -- no API keys required.
"""

import io
import html as html_module
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html

# ===================================================================
# COLOUR PALETTE (dark theme)
# ===================================================================
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_ACCENT = "#ec4899"
_MUTED = "#5a6580"

# ===================================================================
# MAP MODE LIST
# ===================================================================
MAP_MODES = [
    "French Boulangerie Heritage",
    "German Bread Traditions",
    "Italian Bread & Focaccia",
    "Sourdough Heritage",
    "Middle Eastern Flatbreads",
    "Asian Bread Traditions",
    "Ancient Bread History",
    "Artisan Bakeries Worldwide",
    "Bread Festivals & Markets",
    "Bread Museums & Schools",
]

# ===================================================================
# 1. FRENCH BOULANGERIE HERITAGE (28 entries)
# ===================================================================
FRENCH_BOULANGERIE = [
    {"name": "Poilane Bakery (rue du Cherche-Midi)", "lat": 48.8500, "lon": 2.3267, "country": "France", "style": "Pain Poilane / Miche", "founded": "1932", "notes": "Iconic Parisian sourdough; massive 1.9 kg miche baked in wood-fired ovens; globally renowned"},
    {"name": "Du Pain et des Idees", "lat": 48.8714, "lon": 2.3614, "country": "France", "style": "Pain des Amis / Escargots", "founded": "2002", "notes": "Christophe Vasseur's artisan bakery in 19th-century shop; best escargot pastries in Paris"},
    {"name": "Maison Kayser (Paris flagship)", "lat": 48.8462, "lon": 2.3455, "country": "France", "style": "Baguette / Pain de Campagne", "founded": "1996", "notes": "Eric Kayser pioneered liquid levain fermentation system; now 200+ bakeries in 25 countries"},
    {"name": "Boulangerie Julien (3 baguettes d'or)", "lat": 48.8553, "lon": 2.3700, "country": "France", "style": "Baguette de tradition", "founded": "1994", "notes": "Multiple Grand Prix de la Baguette de Tradition winner; classic Left Bank boulangerie"},
    {"name": "Le Grenier a Pain", "lat": 48.8844, "lon": 2.3378, "country": "France", "style": "Baguette tradition / Pain bio", "founded": "1995", "notes": "Michel Galloyer won Best Baguette in Paris (2010); organic flour specialist; Montmartre institution"},
    {"name": "Boulangerie Pichard", "lat": 48.8620, "lon": 2.2967, "country": "France", "style": "Croissant / Baguette", "founded": "1901", "notes": "Historic boulangerie near Trocadero; classic Parisian viennoiserie; butter croissants"},
    {"name": "La Maison Pichard", "lat": 48.8586, "lon": 2.2944, "country": "France", "style": "Pain au levain / Fougasse", "founded": "1956", "notes": "Traditional Parisian levain bread; long fermentation process; neighborhood institution"},
    {"name": "Moulin de la Vierge", "lat": 48.8413, "lon": 2.3192, "country": "France", "style": "Pain au levain / Baguette", "founded": "1995", "notes": "Stone-milled flour baked in wood-fired ovens; multiple locations; artisan levain tradition"},
    {"name": "Boulangerie Utopie", "lat": 48.8653, "lon": 2.3803, "country": "France", "style": "Pain au levain / Sourdough", "founded": "2017", "notes": "Erwan Blanche creates all-organic, all-sourdough breads in the 11th arrondissement"},
    {"name": "Boulangerie Ble Sucre", "lat": 48.8464, "lon": 2.3894, "country": "France", "style": "Croissant / Pain de mie", "founded": "2006", "notes": "Fabrice Le Bourdat's bakery near Gare de Lyon; acclaimed croissants and madeleine"},
    {"name": "Maison Landemaine", "lat": 48.8789, "lon": 2.3483, "country": "France", "style": "Baguette / Pain complet", "founded": "2007", "notes": "Rodolphe Landemaine's eco-bakery chain; organic flours; long fermentation philosophy"},
    {"name": "Boulangerie de Tradition (Lyon)", "lat": 45.7640, "lon": 4.8357, "country": "France", "style": "Pain de campagne / Couronne", "founded": "1985", "notes": "Lyon's artisan bread traditions; regional couronne lyonnaise shape; natural levain"},
    {"name": "Maison Becker (Strasbourg)", "lat": 48.5734, "lon": 7.7521, "country": "France", "style": "Pain d'Alsace / Kugelhopf", "founded": "1948", "notes": "Alsatian bread heritage; Kugelhopf is traditional ring-shaped enriched bread; Germanic influence"},
    {"name": "Boulangerie Xavier (Bordeaux)", "lat": 44.8378, "lon": -0.5792, "country": "France", "style": "Pain bordelais / Baguette", "founded": "1972", "notes": "Bordeaux regional bread styles; tourte bordelaise with ancient wheat varieties"},
    {"name": "Farine&O (Marseille)", "lat": 43.2965, "lon": 5.3698, "country": "France", "style": "Fougasse / Pain provencal", "founded": "2014", "notes": "Provencal bread specialist; fougasse with herbs; olive oil breads; Mediterranean tradition"},
    {"name": "Maison Puget (Aix-en-Provence)", "lat": 43.5263, "lon": 5.4474, "country": "France", "style": "Navette / Pain a l'olive", "founded": "1907", "notes": "Traditional Provencal bakery; navette biscuits and local bread specialties"},
    {"name": "Boulangerie Paul (Lille flagship)", "lat": 50.6292, "lon": 3.0573, "country": "France", "style": "Pain de campagne / Viennoiserie", "founded": "1889", "notes": "Founded in Lille; now 750+ locations worldwide; preserved traditional baking methods"},
    {"name": "Maison Collet (Rouen)", "lat": 49.4432, "lon": 1.0993, "country": "France", "style": "Pain normand / Brioche", "founded": "1920", "notes": "Norman bread and brioche traditions; butter-rich doughs reflecting Normandy dairy heritage"},
    {"name": "Pain Paillasse (Lozere)", "lat": 44.5167, "lon": 3.5000, "country": "France", "style": "Pain paillasse", "founded": "1990", "notes": "Revived ancient bread baked directly on stone; rustic open crumb; Massif Central tradition"},
    {"name": "Boulangerie Thierry Marx (Paris)", "lat": 48.8663, "lon": 2.3117, "country": "France", "style": "Pain artisanal / Gluten-free", "founded": "2017", "notes": "Chef Thierry Marx's bakery; innovative baking techniques; accessible artisanal bread"},
    {"name": "Maison Trottin (Nice)", "lat": 43.7102, "lon": 7.2620, "country": "France", "style": "Socca / Fougasse nicoise", "founded": "1945", "notes": "Nicois bread specialties; socca chickpea flatbread; pissaladiere; Riviera baking"},
    {"name": "Le Fournil de Pierre (Toulouse)", "lat": 43.6047, "lon": 1.4442, "country": "France", "style": "Pain de meture / Tourte", "founded": "1978", "notes": "Southwest France bread heritage; corn and wheat mixes; regional tourte traditions"},
    {"name": "Boulangerie Gosselin (Paris)", "lat": 48.8606, "lon": 2.2937, "country": "France", "style": "Baguette tradition", "founded": "1992", "notes": "Philippe Gosselin's baguette tradition; long cold fermentation; crispy golden crust"},
    {"name": "Au Levain du Marais (Paris)", "lat": 48.8572, "lon": 2.3589, "country": "France", "style": "Pain au levain / Rye", "founded": "1999", "notes": "Natural levain specialist in the Marais; dark rye and whole grain sourdoughs"},
    {"name": "Boulangerie Terroir d'Avenir (Paris)", "lat": 48.8636, "lon": 2.3508, "country": "France", "style": "Pain bio / Heritage wheat", "founded": "2012", "notes": "Farm-to-bakery concept; heritage wheat varieties; collaborates with local grain farmers"},
    {"name": "Boulangerie Bo (Paris)", "lat": 48.8702, "lon": 2.3811, "country": "France", "style": "Baguette / Croissant", "founded": "2015", "notes": "Thierry Breton's bakery-restaurant; rustic breads with long fermentation"},
    {"name": "Croissanterie de Montmartre", "lat": 48.8867, "lon": 2.3431, "country": "France", "style": "Croissant au beurre", "founded": "1960", "notes": "Classic Montmartre viennoiserie; laminated croissants with AOP Charentes butter"},
    {"name": "Breadmaking Museum (Bonnieux)", "lat": 43.8262, "lon": 5.3089, "country": "France", "style": "Pain provencal / Heritage", "founded": "1983", "notes": "Museum of traditional Provencal bread; historic ovens; displays of regional baking heritage"},
]

# ===================================================================
# 2. GERMAN BREAD TRADITIONS (28 entries)
# ===================================================================
GERMAN_BREAD = [
    {"name": "Baeckerei Domberger (Berlin)", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "style": "Schwarzbrot / Vollkornbrot", "founded": "1878", "notes": "Traditional German whole-grain rye bakery; dense dark Pumpernickel and Vollkornbrot"},
    {"name": "Baeckerei Rischart (Munich)", "lat": 48.1351, "lon": 11.5820, "country": "Germany", "style": "Brezn / Semmeln / Roggenbrot", "founded": "1883", "notes": "Bavarian bakery institution; classic Brezn (pretzels) and Roggenmischbrot; 15 Munich locations"},
    {"name": "Baeckerei Hinkel (Dusseldorf)", "lat": 51.2277, "lon": 6.7735, "country": "Germany", "style": "Rheinisches Schwarzbrot", "founded": "1891", "notes": "Rhineland bread tradition; Schwarzbrot baked for 20+ hours in declining-heat ovens"},
    {"name": "Hofpfisterei (Munich)", "lat": 48.1374, "lon": 11.5755, "country": "Germany", "style": "Pfister Oko-Bauernbrot", "founded": "1331", "notes": "Munich's oldest bakery; organic Natursauerteig (natural sourdough); medieval origin"},
    {"name": "Baeckerei Junge (Lubeck)", "lat": 53.8655, "lon": 10.6866, "country": "Germany", "style": "Norddeutsches Brot / Feinbrot", "founded": "1897", "notes": "North German bread chain; rye-heavy loaves; marzipan bread for Lubeck tradition"},
    {"name": "Baeckerei Exner (Dresden)", "lat": 51.0504, "lon": 13.7373, "country": "Germany", "style": "Dresdner Stollen / Pumpernickel", "founded": "1954", "notes": "Saxon bread and Stollen tradition; Christstollen is UNESCO-worthy festive bread"},
    {"name": "Laugenbrezeln Tradition (Stuttgart)", "lat": 48.7758, "lon": 9.1829, "country": "Germany", "style": "Schwabische Laugenbrezel", "founded": "1477", "notes": "Swabian pretzel heartland; lye-dipped Brezeln with coarse salt; legend traces to Bad Urach 1477"},
    {"name": "Baeckerei Joest (Cologne)", "lat": 50.9375, "lon": 6.9603, "country": "Germany", "style": "Roggenmischbrot / Kolner Brot", "founded": "1932", "notes": "Cologne rye-wheat mix tradition; Roggenmischbrot is Germany's most popular bread type"},
    {"name": "Pumpernickel Bakery (Soest)", "lat": 51.5714, "lon": 8.1060, "country": "Germany", "style": "Westphalian Pumpernickel", "founded": "1570", "notes": "Pumpernickel originated in Westphalia; baked 16-24 hours at low temperature; dark and sweet"},
    {"name": "Baeckerei Wippler (Dresden)", "lat": 51.0534, "lon": 13.7500, "country": "Germany", "style": "Dresdner Eierschecke / Brot", "founded": "1896", "notes": "Saxon baking traditions; regional specialty breads alongside famous Eierschecke cake"},
    {"name": "Baeckerei Brotchen (Hamburg)", "lat": 53.5511, "lon": 9.9937, "country": "Germany", "style": "Hamburger Rundstuck / Brotchen", "founded": "1905", "notes": "Hamburg roll tradition; Rundstuck is the local breakfast roll; crusty wheat rolls"},
    {"name": "Weinheimer Brotmuseum", "lat": 49.5511, "lon": 8.6669, "country": "Germany", "style": "Heritage breads", "founded": "1978", "notes": "Bread museum in Weinheim; exhibits German bread culture spanning 6,000 years"},
    {"name": "Deutsches Brotinstitut (Berlin)", "lat": 52.5097, "lon": 13.3771, "country": "Germany", "style": "All German bread types", "founded": "1955", "notes": "German Bread Institute; registers over 3,200 recognized bread varieties in Germany"},
    {"name": "Baeckerei Hoefer (Nuremberg)", "lat": 49.4521, "lon": 11.0767, "country": "Germany", "style": "Frankisches Landbrot / Lebkuchen", "founded": "1879", "notes": "Franconian bread tradition; regional Landbrot with caraway; also Nuremberg Lebkuchen"},
    {"name": "Baeckerei Lichtenstein (Freiburg)", "lat": 47.9990, "lon": 7.8421, "country": "Germany", "style": "Schwarzwalder Brot / Bauernbrot", "founded": "1912", "notes": "Black Forest bread heritage; dark mixed rye with spelt; rustic Bauernbrot"},
    {"name": "Baeckerei Staib (Ulm)", "lat": 48.4011, "lon": 9.9876, "country": "Germany", "style": "Ulmer Brot / Schwabischer Seele", "founded": "1860", "notes": "Swabian Seele bread -- long, flat wheat roll with caraway and salt; Ulm specialty"},
    {"name": "Baeckerei Mantler (Mainz)", "lat": 49.9929, "lon": 8.2473, "country": "Germany", "style": "Rheinhessisches Brot / Weissbrot", "founded": "1925", "notes": "Rhineland-Hesse bread styles; wheat-rye blends; regional Mainzer Spundekase accompaniment"},
    {"name": "Kamps Bakery (Dusseldorf HQ)", "lat": 51.2330, "lon": 6.7845, "country": "Germany", "style": "Brotchen / Vollkornbrot", "founded": "1982", "notes": "Germany's largest bakery chain; over 400 locations; represents industrial German baking"},
    {"name": "Baeckerei Viehoff (Essen)", "lat": 51.4556, "lon": 7.0116, "country": "Germany", "style": "Ruhrgebiet Graubrot / Stuten", "founded": "1911", "notes": "Ruhr Valley bread culture; Stuten is sweet yeast bread; Graubrot grey bread tradition"},
    {"name": "Baeckerei Gilgen (Zurich influence)", "lat": 47.3769, "lon": 8.5417, "country": "Switzerland", "style": "Zopf / Ruchbrot", "founded": "1910", "notes": "Swiss-German bread tradition; Zopf braided bread for Sunday; Ruchbrot semi-white loaf"},
    {"name": "Wiener Brot Tradition (Vienna)", "lat": 48.2082, "lon": 16.3738, "country": "Austria", "style": "Kaisersemmel / Wachauer Laberl", "founded": "1850", "notes": "Austrian roll mastery; Kaisersemmel five-fold roll; Viennese baking influenced all of Central Europe"},
    {"name": "Baeckerei Heberer (Frankfurt)", "lat": 50.1109, "lon": 8.6821, "country": "Germany", "style": "Hessisches Bauernbrot", "founded": "1891", "notes": "Hessian farmhouse bread; caraway-studded rye loaves; Frankfurt's oldest bakery lineage"},
    {"name": "Baeckerei Gaues (Hamburg)", "lat": 53.5614, "lon": 10.0072, "country": "Germany", "style": "Norddeutsches Weizenbrot", "founded": "1998", "notes": "Award-winning Hamburg baker; stone oven baked wheat loaves; champion of artisanal methods"},
    {"name": "Baeckerei Lutz Geissler Style (Homebaker)", "lat": 50.9298, "lon": 11.5854, "country": "Germany", "style": "Artisan Sauerteig / Levain", "founded": "2009", "notes": "Influential German bread blogger/author; ploetzblog.de; revived home sourdough movement in Germany"},
    {"name": "Muehle & Bakery Drax (Bavaria)", "lat": 48.5656, "lon": 12.4231, "country": "Germany", "style": "Bayerisches Holzofenbrot", "founded": "1756", "notes": "Traditional Bavarian wood-oven bakery with attached mill; grain-to-loaf artisan process"},
    {"name": "Baeckerei Wiesheu (Augsburg)", "lat": 48.3705, "lon": 10.8978, "country": "Germany", "style": "Augsburger Brot / Kipferl", "founded": "1869", "notes": "Swabian-Bavarian crossover; Kipferl crescent rolls; traditional Augsburg baking heritage"},
    {"name": "Backhaus Salzwedel", "lat": 52.8529, "lon": 11.1549, "country": "Germany", "style": "Salzwedeler Baumkuchen / Brot", "founded": "1807", "notes": "Baumkuchen heritage bakery in Altmark region; tree cake and traditional Altmark breads"},
    {"name": "Baeckerei Alpenstuck (Berlin)", "lat": 52.5244, "lon": 13.4533, "country": "Germany", "style": "Alpine-style Sauerteigbrot", "founded": "2010", "notes": "Berlin's artisan sourdough revival; Alpine-inspired natural fermentation; crusty loaves"},
]

# ===================================================================
# 3. ITALIAN BREAD & FOCACCIA (28 entries)
# ===================================================================
ITALIAN_BREAD = [
    {"name": "Pane di Altamura (Altamura)", "lat": 40.8263, "lon": 16.5522, "country": "Italy", "style": "Pane di Altamura DOP", "founded": "Ancient", "notes": "First bread with EU DOP status; durum wheat semola rimacinata; baked in wood-fired ovens"},
    {"name": "Focaccia di Recco (Recco)", "lat": 44.3631, "lon": 9.1475, "country": "Italy", "style": "Focaccia col formaggio IGP", "founded": "1189", "notes": "Paper-thin focaccia filled with stracchino cheese; crusader-era origins; IGP protected"},
    {"name": "Antico Forno Roscioli (Rome)", "lat": 41.8935, "lon": 12.4751, "country": "Italy", "style": "Pizza bianca / Pane romano", "founded": "1824", "notes": "Roman bakery institution; legendary pizza bianca; crispy Roman-style bread with olive oil"},
    {"name": "Focacceria Ligure (Genoa)", "lat": 44.4056, "lon": 8.9463, "country": "Italy", "style": "Focaccia genovese", "founded": "1870", "notes": "Classic Genoese focaccia; dimpled, olive oil-soaked, salt-crusted; Ligurian tradition"},
    {"name": "Panificio Ferrara (Palermo)", "lat": 38.1157, "lon": 13.3615, "country": "Italy", "style": "Pane siciliano / Mafalda", "founded": "1925", "notes": "Sicilian sesame bread (Mafalda); durum wheat; S-shaped traditional loaves"},
    {"name": "Forno Campo de' Fiori (Rome)", "lat": 41.8956, "lon": 12.4722, "country": "Italy", "style": "Pizza bianca / Pane casareccio", "founded": "1945", "notes": "Iconic Roman bakery in Campo de' Fiori square; freshly baked pizza bianca all day"},
    {"name": "Panificio Davide Longoni (Milan)", "lat": 45.4625, "lon": 9.2039, "country": "Italy", "style": "Michetta / Pain de campagne", "founded": "2012", "notes": "Milan's artisanal bread renaissance; ancient grains; natural levain; Michetta hollow rolls"},
    {"name": "Forno Brisa (Bologna)", "lat": 44.4949, "lon": 11.3426, "country": "Italy", "style": "Pane bolognese / Crescentina", "founded": "2015", "notes": "New-wave Bolognese bakery; heritage grains; sourdough focaccia and tigelle/crescentina"},
    {"name": "Panificio Bonci (Rome)", "lat": 41.9070, "lon": 12.4540, "country": "Italy", "style": "Pizza al taglio / Focaccia", "founded": "2003", "notes": "Gabriele Bonci's legendary pizza al taglio near Vatican; high-hydration doughs"},
    {"name": "Pane di Matera (Matera)", "lat": 40.6654, "lon": 16.6043, "country": "Italy", "style": "Pane di Matera IGP", "founded": "Ancient", "notes": "Cave-city bread tradition; large horn-shaped loaves; durum wheat; stays fresh for days"},
    {"name": "Ciabatta Origin (Adria, Veneto)", "lat": 45.0550, "lon": 12.0564, "country": "Italy", "style": "Ciabatta", "founded": "1982", "notes": "Arnaldo Cavallari invented ciabatta in 1982 at his bakery near Adria; now globally ubiquitous"},
    {"name": "Schuttelbrot Bakery (South Tyrol)", "lat": 46.7103, "lon": 11.6538, "country": "Italy", "style": "Schuttelbrot / Vinschgauer", "founded": "Medieval", "notes": "South Tyrolean crisp rye flatbread; spiced with caraway and fennel; Alpine bread tradition"},
    {"name": "Panificio Perino Vesco (Turin)", "lat": 45.0703, "lon": 7.6869, "country": "Italy", "style": "Grissini torinesi / Rubata", "founded": "1890", "notes": "Turin is birthplace of grissini breadsticks (1675); hand-stretched rubata style"},
    {"name": "Forno Monteforte (Naples)", "lat": 40.8518, "lon": 14.2681, "country": "Italy", "style": "Pane cafone / Taralli", "founded": "1930", "notes": "Neapolitan pane cafone -- large rustic loaf with thick crust; served with everything"},
    {"name": "Panificio Di Gesaro (Castelvetrano)", "lat": 37.6781, "lon": 12.7922, "country": "Italy", "style": "Pane nero di Castelvetrano", "founded": "1870", "notes": "Unique black bread made with tumminìa ancient wheat; dark crumb; Slow Food presidia"},
    {"name": "Pane Carasau Bakery (Sardinia)", "lat": 40.3210, "lon": 9.3286, "country": "Italy", "style": "Pane carasau / Carta di musica", "founded": "Ancient", "notes": "Paper-thin Sardinian flatbread; twice-baked for shepherds; can last months; ancient recipe"},
    {"name": "Focaccia di Bari (Bari Vecchia)", "lat": 41.1256, "lon": 16.8684, "country": "Italy", "style": "Focaccia barese", "founded": "1600s", "notes": "Pugliese focaccia with tomatoes, olives, and semolina; baked in the old city ovens"},
    {"name": "Panetteria Fiore (Trani)", "lat": 41.2767, "lon": 16.4167, "country": "Italy", "style": "Pane di Trani / Pugliese", "founded": "1920", "notes": "Pugliese bread tradition; large loaves with crisp crust; durum wheat semola"},
    {"name": "Forno Pasticceria Rizzardini (Venice)", "lat": 45.4360, "lon": 12.3267, "country": "Italy", "style": "Baicoli / Pan del Doge", "founded": "1742", "notes": "Venice's oldest bakery; Baicoli thin oval biscuits; Venetian bread heritage since 18th century"},
    {"name": "Panificio Graziano (Lariano)", "lat": 41.7261, "lon": 12.8322, "country": "Italy", "style": "Pane di Lariano IGP", "founded": "1948", "notes": "Pane di Lariano: large wood-fired loaves south of Rome; chestnut and oak wood-fired ovens"},
    {"name": "Princi Bakery (Milan)", "lat": 45.4677, "lon": 9.1700, "country": "Italy", "style": "Focaccia / Ciabatta / Grissini", "founded": "1986", "notes": "Rocco Princi's designer bakery; open kitchen; artisan Italian breads; partnered with Starbucks"},
    {"name": "Eataly Bread Counter (Turin flagship)", "lat": 45.0473, "lon": 7.6766, "country": "Italy", "style": "Regional Italian breads", "founded": "2007", "notes": "Eataly showcases regional Italian breads; artisan bakers on site; educational bread displays"},
    {"name": "Panificio Perino (Ferrara)", "lat": 44.8381, "lon": 11.6199, "country": "Italy", "style": "Coppia ferrarese IGP", "founded": "1935", "notes": "Coppia ferrarese: twisted bread rolls with four horns; IGP protected; Este court origins"},
    {"name": "Bakery of Ferrara (Coppia tradition)", "lat": 44.8357, "lon": 11.6180, "country": "Italy", "style": "Coppia ferrarese", "founded": "1287", "notes": "Coppia bread documented since 1287; linked to Este dynasty court banquets; iconic shape"},
    {"name": "Il Fornaio di Gragnano", "lat": 40.6875, "lon": 14.5200, "country": "Italy", "style": "Pane di Gragnano / Taralli", "founded": "1880", "notes": "Gragnano is famous for pasta and bread; volcanic soil wheat; Campanian baking traditions"},
    {"name": "Panificio Manna (Lecce)", "lat": 40.3516, "lon": 18.1710, "country": "Italy", "style": "Puccia leccese / Frisella", "founded": "1950", "notes": "Salento bread traditions; puccia stuffed bread; frisella twice-baked barley rings"},
    {"name": "Forno della Soffitta (Florence)", "lat": 43.7696, "lon": 11.2558, "country": "Italy", "style": "Pane toscano (unsalted)", "founded": "1940", "notes": "Tuscan bread is famously unsalted; tradition dates to 12th-century salt tax; pairs with cured meats"},
    {"name": "Mulino Marino (Piemonte mill-bakery)", "lat": 44.8833, "lon": 7.8667, "country": "Italy", "style": "Stone-milled heritage flours", "founded": "1956", "notes": "Piedmont stone mill supplying Italy's best bakers; heritage grain revival; Tipo 1 and 2 flours"},
]

# ===================================================================
# 4. SOURDOUGH HERITAGE (28 entries)
# ===================================================================
SOURDOUGH_HERITAGE = [
    {"name": "Boudin Bakery (San Francisco)", "lat": 37.8080, "lon": -122.4177, "country": "USA", "style": "San Francisco Sourdough", "founded": "1849", "notes": "Gold Rush-era sourdough; unique Lactobacillus sanfranciscensis culture; bread bowl clam chowder icon"},
    {"name": "Tartine Bakery (San Francisco)", "lat": 37.7614, "lon": -122.4241, "country": "USA", "style": "Country Bread / Sourdough", "founded": "2002", "notes": "Chad Robertson's country loaf revolutionized modern sourdough; high-hydration open crumb; global influence"},
    {"name": "Acme Bread Company (Berkeley)", "lat": 37.8564, "lon": -122.2946, "country": "USA", "style": "Pain de campagne / Levain", "founded": "1983", "notes": "Steve Sullivan pioneered Bay Area artisan bread; trained at Chez Panisse; natural levain"},
    {"name": "Poilane (Paris)", "lat": 48.8502, "lon": 2.3265, "country": "France", "style": "Miche Poilane / Pain de campagne", "founded": "1932", "notes": "Apollonia Poilane continues the 2kg sourdough miche tradition; wood-fired; shipped worldwide"},
    {"name": "E5 Bakehouse (London)", "lat": 51.5340, "lon": -0.0556, "country": "UK", "style": "Sourdough / Heritage Grain", "founded": "2011", "notes": "London's sourdough pioneer; railway arch bakery in Hackney; heritage grain focus; community hub"},
    {"name": "Tartine Manufactory (San Francisco)", "lat": 37.7614, "lon": -122.4071, "country": "USA", "style": "Porridge Bread / Danish Rye", "founded": "2016", "notes": "Chad Robertson's expanded bakery; porridge breads; Danish-style rye; grain lab collaborations"},
    {"name": "Josey Baker Bread (San Francisco)", "lat": 37.7680, "lon": -122.4211, "country": "USA", "style": "Adventure Bread / Sourdough", "founded": "2010", "notes": "Whole grain sourdough specialist; Adventure Bread is 100% seeds and nuts; The Mill collaboration"},
    {"name": "Bourke Street Bakery (Sydney)", "lat": -33.8879, "lon": 151.2129, "country": "Australia", "style": "Sourdough Loaf / Rye", "founded": "2004", "notes": "Australian sourdough movement leader; Surry Hills original; multiple Sydney locations"},
    {"name": "Iggy's Bread of the World (Sydney)", "lat": -33.8688, "lon": 151.2093, "country": "Australia", "style": "Wood-fired Sourdough", "founded": "1995", "notes": "Igor Ivanovic's pioneering Australian sourdough; supplies top Sydney restaurants"},
    {"name": "Sonoma Bakery (Sydney)", "lat": -33.8903, "lon": 151.2050, "country": "Australia", "style": "Sourdough / Spelt / Rye", "founded": "2000", "notes": "Long-fermentation sourdough; stone-milled Australian grains; multiple cafe-bakeries"},
    {"name": "Jokinen Bakery (Helsinki)", "lat": 60.1695, "lon": 24.9354, "country": "Finland", "style": "Ruisleipa (Rye Sourdough)", "founded": "1907", "notes": "Finnish rye sourdough tradition; dark, dense ruisleipa is a dietary staple; centuries-old culture"},
    {"name": "Surdegsbageriet (Stockholm)", "lat": 59.3293, "lon": 18.0686, "country": "Sweden", "style": "Swedish Sourdough / Knackebrod", "founded": "2003", "notes": "Stockholm's sourdough specialist; Nordic rye traditions; Swedish knackebrod crispbread"},
    {"name": "Hart Bageri (Copenhagen)", "lat": 55.6761, "lon": 12.5683, "country": "Denmark", "style": "Danish Rye / Sourdough", "founded": "2018", "notes": "Richard Hart (ex-Tartine) in Copenhagen; Danish rugbrod rye sourdough; Nordic grain focus"},
    {"name": "Fabrique (Stockholm)", "lat": 59.3383, "lon": 18.0653, "country": "Sweden", "style": "Sourdough / Cardamom buns", "founded": "2008", "notes": "Swedish artisan chain; long-fermented sourdoughs; stone ovens; expanded to London and NYC"},
    {"name": "The Bread Station (Copenhagen)", "lat": 55.6867, "lon": 12.5399, "country": "Denmark", "style": "Organic Sourdough / Rugbrod", "founded": "2010", "notes": "Community bakery in Norrebro; 100% organic; Danish rugbrod tradition with wild yeast"},
    {"name": "Brickmaiden Breads (Point Reyes)", "lat": 38.0697, "lon": -122.8028, "country": "USA", "style": "Hearth Sourdough / Country", "founded": "2017", "notes": "Marin County artisan bakery; wood-fired sourdough; local grain collaborations"},
    {"name": "The Dusty Knuckle (London)", "lat": 51.5388, "lon": -0.0629, "country": "UK", "style": "Sourdough / Filled Focaccia", "founded": "2014", "notes": "Social enterprise bakery in Dalston; sourdough and focaccia; employs disadvantaged youth"},
    {"name": "Levain Bakery (New York)", "lat": 40.7803, "lon": -73.9809, "country": "USA", "style": "Sourdough / Walnut Raisin", "founded": "1995", "notes": "Upper West Side institution; famous for cookies but outstanding sourdough and walnut bread"},
    {"name": "Brot Bakehouse (Melbourne)", "lat": -37.8562, "lon": 145.0129, "country": "Australia", "style": "German-style Sourdough", "founded": "2015", "notes": "German-Australian sourdough fusion; whole rye and spelt loaves; Brunswick East bakery"},
    {"name": "Sullivan Street Bakery (New York)", "lat": 40.7589, "lon": -73.9899, "country": "USA", "style": "Pugliese / Italian Sourdough", "founded": "1994", "notes": "Jim Lahey invented no-knead bread method (2006); Italian-style high-hydration loaves"},
    {"name": "She Wolf Bakery (Brooklyn)", "lat": 40.6934, "lon": -73.9833, "country": "USA", "style": "Country Sourdough / Rye", "founded": "2015", "notes": "Brooklyn micro-bakery; stone-milled grains; supplies top NYC restaurants"},
    {"name": "Le Bricheton (Paris)", "lat": 48.8667, "lon": 2.3833, "country": "France", "style": "Pain au levain bio", "founded": "2018", "notes": "New-wave Parisian sourdough; 100% organic; heritage wheat varieties; long cold fermentation"},
    {"name": "Companion Bakery (St. Louis)", "lat": 38.6270, "lon": -90.1994, "country": "USA", "style": "Rustic Sourdough / Wheat", "founded": "1993", "notes": "Midwest artisan sourdough pioneer; supplies St. Louis restaurants; bakery-cafe model"},
    {"name": "Breadfarm (Bow, Washington)", "lat": 48.5606, "lon": -122.4301, "country": "USA", "style": "Sour Rye / Pain de Campagne", "founded": "2004", "notes": "Pacific Northwest sourdough artisan; Skagit Valley heritage grains; wood-fired deck oven"},
    {"name": "Panificio Bonci Sourdough (Rome)", "lat": 41.9073, "lon": 12.4545, "country": "Italy", "style": "Lievito madre / Sourdough Pizza", "founded": "2003", "notes": "Gabriele Bonci keeps a decades-old lievito madre (sourdough mother); pizza al taglio icon"},
    {"name": "Haga Bageri (Gothenburg)", "lat": 57.6991, "lon": 11.9528, "country": "Sweden", "style": "Swedish Levain / Kanelbulle", "founded": "1996", "notes": "Gothenburg's beloved bakery in Haga district; sourdough loaves and giant cinnamon buns"},
    {"name": "Mirabaud Bakery (Zurich)", "lat": 47.3769, "lon": 8.5417, "country": "Switzerland", "style": "Swiss Levain / Pain Paysan", "founded": "1952", "notes": "Swiss sourdough tradition; alpine grain varieties; hearth-baked pain paysan loaves"},
    {"name": "Loaflab (Cape Town)", "lat": -33.9249, "lon": 18.4241, "country": "South Africa", "style": "Sourdough / Heritage Grain", "founded": "2016", "notes": "South African artisan sourdough; local heritage grain exploration; Woodstock bakery"},
]

# ===================================================================
# 5. MIDDLE EASTERN FLATBREADS (28 entries)
# ===================================================================
MIDDLE_EASTERN_FLATBREADS = [
    {"name": "Pita Bakery (Jerusalem Old City)", "lat": 31.7767, "lon": 35.2345, "country": "Israel/Palestine", "style": "Pita / Khubz", "founded": "Ancient", "notes": "Pita has been baked in Jerusalem for thousands of years; puffed pocket bread; taboon ovens"},
    {"name": "Abu Shukri Bakery (Jerusalem)", "lat": 31.7780, "lon": 35.2320, "country": "Israel/Palestine", "style": "Pita / Laffa", "founded": "1950", "notes": "Old City bakery; fresh pita for hummus; laffa large flatbread grilled on saj"},
    {"name": "Sangak Bakery (Tehran Grand Bazaar)", "lat": 35.6722, "lon": 51.4222, "country": "Iran", "style": "Sangak / Barbari", "founded": "Ancient", "notes": "Sangak baked on hot pebbles since Safavid era; long, dimpled flatbread; Iranian staple"},
    {"name": "Barbari Bakery (Isfahan)", "lat": 32.6546, "lon": 51.6680, "country": "Iran", "style": "Barbari / Nan-e Barbari", "founded": "Ancient", "notes": "Barbari is thick, golden, sesame-topped flatbread; baked in tandoor-style ovens; breakfast staple"},
    {"name": "Tannour Bakery (Baghdad)", "lat": 33.3128, "lon": 44.3615, "country": "Iraq", "style": "Khubz tannour / Samoon", "founded": "Ancient", "notes": "Iraqi tannour (clay oven) bread; samoon is diamond-shaped; Mesopotamian baking heritage"},
    {"name": "Manakish Bakery (Beirut)", "lat": 33.8938, "lon": 35.5018, "country": "Lebanon", "style": "Manakish / Man'oushe", "founded": "Traditional", "notes": "Za'atar-topped flatbread; Lebanese breakfast staple; baked on saj or in oven; street food icon"},
    {"name": "Furn al-Hara (Tripoli, Lebanon)", "lat": 34.4367, "lon": 35.8497, "country": "Lebanon", "style": "Markouk / Saj bread", "founded": "Traditional", "notes": "Markouk paper-thin bread cooked on convex saj; Tripoli has finest traditional bakeries"},
    {"name": "Naan Bakery (Lahore Old City)", "lat": 31.5820, "lon": 74.3292, "country": "Pakistan", "style": "Naan / Tandoori Roti", "founded": "Ancient", "notes": "Lahore's tandoor naan tradition; slapped onto clay oven walls; brushed with ghee; daily staple"},
    {"name": "Bukhara Naan (Bukhara)", "lat": 39.7683, "lon": 64.4219, "country": "Uzbekistan", "style": "Non / Obi-Non / Patyr", "founded": "Ancient", "notes": "Bukhara's ornamental bread (Non); stamped with patterns; baked in tandyr ovens; Silk Road heritage"},
    {"name": "Lavash Bakery (Yerevan)", "lat": 40.1792, "lon": 44.4991, "country": "Armenia", "style": "Lavash", "founded": "Ancient", "notes": "Armenian lavash is UNESCO Intangible Heritage; baked in tonir (underground oven); paper-thin"},
    {"name": "Lavash Village Bakery (Garni)", "lat": 40.1125, "lon": 44.7306, "country": "Armenia", "style": "Lavash / Matnakash", "founded": "Ancient", "notes": "Traditional village tonir ovens near Garni Temple; communal lavash baking by women"},
    {"name": "Tandoori Bread Market (Peshawar)", "lat": 34.0151, "lon": 71.5249, "country": "Pakistan", "style": "Chapli Naan / Roghni Naan", "founded": "Traditional", "notes": "Peshawar naan varieties; Roghni (buttery) naan; tandoor street bakeries line the bazaars"},
    {"name": "Fatayer Bakery (Damascus)", "lat": 33.5138, "lon": 36.2765, "country": "Syria", "style": "Khubz arabi / Fatayer", "founded": "Ancient", "notes": "Damascus flatbread tradition; Khubz arabi (Arabic bread); fatayer stuffed triangles"},
    {"name": "Taboon Bakery (Nazareth)", "lat": 32.6996, "lon": 35.3035, "country": "Israel/Palestine", "style": "Taboon bread / Musakhan", "founded": "Ancient", "notes": "Taboon clay oven bread; base for musakhan (sumac chicken); Palestinian culinary heritage"},
    {"name": "Taftoon Bakery (Shiraz)", "lat": 29.5918, "lon": 52.5836, "country": "Iran", "style": "Taftoon / Nan-e Taftoon", "founded": "Ancient", "notes": "Taftoon is soft, round Iranian flatbread; pebble-dimpled surface; baked on oven floor"},
    {"name": "Gozleme Workshop (Cappadocia)", "lat": 38.6431, "lon": 34.8287, "country": "Turkey", "style": "Gozleme / Yufka", "founded": "Traditional", "notes": "Turkish yufka flatbread rolled paper-thin; filled and griddled as gozleme; Anatolian tradition"},
    {"name": "Pide Bakery (Trabzon)", "lat": 41.0027, "lon": 39.7168, "country": "Turkey", "style": "Pide / Trabzon Pidesi", "founded": "Traditional", "notes": "Black Sea pide tradition; boat-shaped bread with toppings; Trabzon pidesi is egg-topped"},
    {"name": "Simit Street Bakery (Istanbul)", "lat": 41.0082, "lon": 28.9784, "country": "Turkey", "style": "Simit / Acma / Pogaca", "founded": "1525", "notes": "Simit sesame bread rings sold by street vendors since Ottoman era; Istanbul's iconic snack"},
    {"name": "Somun Bakery (Sarajevo Bascarsija)", "lat": 43.8590, "lon": 18.4314, "country": "Bosnia", "style": "Somun / Lepinja", "founded": "1462", "notes": "Ottoman-era flatbread tradition in Sarajevo's old bazaar; somun served with cevapi"},
    {"name": "Markook Bakery (Amman)", "lat": 31.9454, "lon": 35.9284, "country": "Jordan", "style": "Shrak / Markook", "founded": "Traditional", "notes": "Bedouin-style thin bread; cooked on domed saj over fire; Jordanian breakfast essential"},
    {"name": "Khachapuri Bakery (Tbilisi)", "lat": 41.7151, "lon": 44.8271, "country": "Georgia", "style": "Shotis Puri / Khachapuri", "founded": "Ancient", "notes": "Georgian shotis puri baked in tone (clay oven); canoe-shaped; khachapuri cheese bread"},
    {"name": "Puri Bakery (Tbilisi Old Town)", "lat": 41.6920, "lon": 44.8025, "country": "Georgia", "style": "Tone-baked Puri", "founded": "Ancient", "notes": "Underground tone ovens in Tbilisi; fresh puri bread pulled from oven walls; daily ritual"},
    {"name": "Chapati Corner (Delhi Old City)", "lat": 28.6562, "lon": 77.2410, "country": "India", "style": "Chapati / Roti / Paratha", "founded": "Traditional", "notes": "Delhi's roti and paratha traditions; whole wheat flatbreads on tawa; North Indian staple"},
    {"name": "Balady Bakery (Cairo)", "lat": 30.0444, "lon": 31.2357, "country": "Egypt", "style": "Aish Baladi / Shamsi", "founded": "Ancient", "notes": "Aish baladi (life bread); Egyptian pita from whole wheat; subsidized staple; ancient tradition"},
    {"name": "Moroccan Msemen Bakery (Fez)", "lat": 34.0181, "lon": -5.0078, "country": "Morocco", "style": "Msemen / Baghrir / Khobz", "founded": "Traditional", "notes": "Fez medina bread stalls; msemen layered griddle bread; baghrir spongy pancakes; khobz rounds"},
    {"name": "Yemeni Malooj Bakery (Sanaa)", "lat": 15.3694, "lon": 44.1910, "country": "Yemen", "style": "Malooj / Bint al-Sahn", "founded": "Traditional", "notes": "Yemeni honey bread (bint al-sahn); layered flaky bread drizzled with honey; festive dish"},
    {"name": "Tannour Bread (Erbil Citadel)", "lat": 36.1912, "lon": 44.0094, "country": "Iraq (Kurdistan)", "style": "Nan-e Tannour / Kurdish bread", "founded": "Ancient", "notes": "Kurdish tannour ovens in Erbil's ancient citadel; thin bread slapped on clay walls"},
    {"name": "Muhammara Bakery (Aleppo)", "lat": 36.2021, "lon": 37.1343, "country": "Syria", "style": "Khubz / Ka'ak", "founded": "Ancient", "notes": "Aleppo's ka'ak sesame bread rings; ancient Silk Road baking tradition; sold by street vendors"},
]

# ===================================================================
# 6. ASIAN BREAD TRADITIONS (27 entries)
# ===================================================================
ASIAN_BREAD = [
    {"name": "Shokupan Bakery (Ginza, Tokyo)", "lat": 35.6717, "lon": 139.7647, "country": "Japan", "style": "Shokupan / Milk Bread", "founded": "1888", "notes": "Japanese milk bread (shokupan) -- pillowy, tangzhong method; defines Japanese bread culture"},
    {"name": "Pelican Bakery (Asakusa, Tokyo)", "lat": 35.7089, "lon": 139.7932, "country": "Japan", "style": "Shokupan / Toast Bread", "founded": "1942", "notes": "Legendary Tokyo bakery; makes only two items -- shokupan and rolls; sells out daily by 10am"},
    {"name": "Centre the Bakery (Ginza)", "lat": 35.6725, "lon": 139.7626, "country": "Japan", "style": "Shokupan tasting", "founded": "2014", "notes": "Restaurant dedicated entirely to toast; serves three bakeries' shokupan for comparison tasting"},
    {"name": "Yamazaki Baking (Tokyo HQ)", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "style": "Anpan / Cream Pan", "founded": "1948", "notes": "Japan's largest bread company; invented modern anpan (red bean bread); melon pan pioneer"},
    {"name": "Korean Garlic Bread (Seoul Jongno)", "lat": 37.5729, "lon": 126.9794, "country": "South Korea", "style": "Garlic Cream Cheese Bread", "founded": "2010s", "notes": "Korean garlic bread went viral globally; cream cheese filled, garlic butter soaked; K-bread phenomenon"},
    {"name": "Paris Baguette (Seoul Flagship)", "lat": 37.5172, "lon": 127.0200, "country": "South Korea", "style": "Korean-style Baguette / Pastries", "founded": "1988", "notes": "Korea's largest bakery chain (4,000+ stores); blends French and Korean baking; global expansion"},
    {"name": "Tous les Jours (Seoul)", "lat": 37.5048, "lon": 127.0226, "country": "South Korea", "style": "Korean-French Bread / Patbingsu", "founded": "1997", "notes": "CJ Group bakery chain; French-inspired Korean baked goods; international presence"},
    {"name": "Mantou Street Kitchen (Shanghai Old City)", "lat": 31.2304, "lon": 121.4737, "country": "China", "style": "Mantou / Hua Juan", "founded": "Ancient", "notes": "Steamed mantou buns -- Chinese bread staple since 3rd century; plain or flower-rolled (hua juan)"},
    {"name": "Nanxiang Steamed Bun (Shanghai)", "lat": 31.2327, "lon": 121.4924, "country": "China", "style": "Xiaolongbao / Shengjianbao", "founded": "1900", "notes": "Shanghai soup dumplings and pan-fried bao; Nanxiang Mantou Dian is the original"},
    {"name": "Beijing Bun Street (Wangfujing)", "lat": 39.9133, "lon": 116.4103, "country": "China", "style": "Baozi / Jianbing", "founded": "Traditional", "notes": "Wangfujing street food; baozi stuffed steamed buns; jianbing crepe wraps; Northern Chinese tradition"},
    {"name": "Roti Canai Stall (George Town, Penang)", "lat": 5.4141, "lon": 100.3288, "country": "Malaysia", "style": "Roti Canai / Roti Telur", "founded": "Traditional", "notes": "Mamak roti canai -- flaky griddle bread from Indian-Muslim tradition; served with dhal curry"},
    {"name": "Roti Prata District (Singapore Little India)", "lat": 1.3066, "lon": 103.8518, "country": "Singapore", "style": "Roti Prata / Murtabak", "founded": "Traditional", "notes": "Singapore's roti prata culture; flipped and griddled flatbread; 24-hour prata shops"},
    {"name": "Bing Stall (Xi'an Muslim Quarter)", "lat": 34.2622, "lon": 108.9411, "country": "China", "style": "Roujiamo / Huoshao", "founded": "Ancient", "notes": "Xi'an roujiamo (Chinese hamburger); bread baked in clay oven; 2,000+ year street food heritage"},
    {"name": "Paratha Alley (Chandni Chowk, Delhi)", "lat": 28.6505, "lon": 77.2303, "country": "India", "style": "Paratha / Stuffed Flatbread", "founded": "1872", "notes": "Parathe Wali Gali -- 150+ year-old paratha street; stuffed flatbreads fried in ghee"},
    {"name": "Tandoori Naan (Amritsar Golden Temple)", "lat": 31.6200, "lon": 74.8765, "country": "India", "style": "Amritsari Kulcha / Naan", "founded": "Traditional", "notes": "Amritsari kulcha -- stuffed tandoor bread; crispy, buttery; served at langar free kitchen"},
    {"name": "Kerala Appam House (Kochi)", "lat": 9.9312, "lon": 76.2673, "country": "India", "style": "Appam / Hoppers", "founded": "Traditional", "notes": "Fermented rice batter bread; bowl-shaped with crispy edges and soft center; coconut milk stew"},
    {"name": "Vietnamese Banh Mi (Ho Chi Minh City)", "lat": 10.7769, "lon": 106.7009, "country": "Vietnam", "style": "Banh Mi / French-Vietnamese Baguette", "founded": "1950s", "notes": "French baguette adapted with rice flour; lighter, crispier; filled sandwich is global street food icon"},
    {"name": "Banh Mi Huynh Hoa (HCMC)", "lat": 10.7715, "lon": 106.6930, "country": "Vietnam", "style": "Banh Mi", "founded": "1980s", "notes": "Most famous banh mi shop in Vietnam; massive sandwiches; queues around the block daily"},
    {"name": "Milk Bread Bakery (Taipei)", "lat": 25.0330, "lon": 121.5654, "country": "Taiwan", "style": "Milk Bread / Pineapple Bun", "founded": "1962", "notes": "Taiwanese milk bread tradition influenced by Japan; pineapple bun (bo lo bao) from Hong Kong"},
    {"name": "Chapati Factory (Mumbai)", "lat": 19.0760, "lon": 72.8777, "country": "India", "style": "Chapati / Bhakri / Pav", "founded": "Traditional", "notes": "Mumbai pav bread for vada pav; Irani bakeries; chapati is India's universal daily bread"},
    {"name": "Thai Roti Stall (Bangkok Chinatown)", "lat": 13.7420, "lon": 100.5080, "country": "Thailand", "style": "Roti / Banana Roti", "founded": "Traditional", "notes": "Thai-Muslim roti tradition; crispy flaky bread with condensed milk and banana; street food staple"},
    {"name": "Uyghur Naan Bazaar (Kashgar)", "lat": 39.4694, "lon": 75.9895, "country": "China", "style": "Nang / Uyghur Naan", "founded": "Ancient", "notes": "Uyghur nang baked in tandoor ovens; stamped with patterns; sesame and onion varieties; Silk Road bread"},
    {"name": "Filipino Pandesal Bakery (Manila)", "lat": 14.5995, "lon": 120.9842, "country": "Philippines", "style": "Pandesal / Pan de Coco", "founded": "Spanish era", "notes": "Pandesal (bread of salt) -- fluffy rolls coated in breadcrumbs; Filipino breakfast essential"},
    {"name": "Sri Lankan Pol Roti Kitchen (Colombo)", "lat": 6.9271, "lon": 79.8612, "country": "Sri Lanka", "style": "Pol Roti / Coconut Flatbread", "founded": "Traditional", "notes": "Pol roti made with grated coconut, flour, onion; griddled flatbread; served with sambol"},
    {"name": "Tibetan Balep Kitchen (Lhasa)", "lat": 29.6500, "lon": 91.1000, "country": "China (Tibet)", "style": "Balep Korkun / Tingmo", "founded": "Ancient", "notes": "Tibetan balep korkun skillet bread; tingmo steamed bread; barley tsampa tradition"},
    {"name": "Indonesian Roti Bakery (Jogjakarta)", "lat": -7.7956, "lon": 110.3695, "country": "Indonesia", "style": "Roti Kukus / Roti Bakar", "founded": "Traditional", "notes": "Javanese steamed bread (roti kukus); roti bakar grilled bread; Dutch colonial bakery influence"},
    {"name": "Central Asian Lepyoshka (Samarkand)", "lat": 39.6542, "lon": 66.9597, "country": "Uzbekistan", "style": "Lepyoshka / Samarkand Non", "founded": "Ancient", "notes": "Samarkand non is Central Asia's most famous bread; ornately stamped; baked in tandyr; Silk Road"},
]

# ===================================================================
# 7. ANCIENT BREAD HISTORY (28 entries)
# ===================================================================
ANCIENT_BREAD = [
    {"name": "Pompeii Bakery (Pistrinum of Modestus)", "lat": 40.7509, "lon": 14.4869, "country": "Italy", "style": "Panis Quadratus / Roman bread", "founded": "1st century", "notes": "Over 30 bakeries excavated in Pompeii; carbonized round loaves preserved by Vesuvius eruption (79 AD)"},
    {"name": "Pompeii Bakery of Popidius Priscus", "lat": 40.7495, "lon": 14.4856, "country": "Italy", "style": "Roman Milling & Bread", "founded": "1st century", "notes": "Complete Roman bakery with millstones, oven, and shop front; donkey-powered grain mills"},
    {"name": "Herculaneum Bakery", "lat": 40.8063, "lon": 14.3478, "country": "Italy", "style": "Panis Roman", "founded": "1st century", "notes": "Preserved bakery in Herculaneum; volcanic mud perfectly preserved ovens and bread molds"},
    {"name": "Giza Pyramid Workers' Bakery", "lat": 29.9773, "lon": 31.1325, "country": "Egypt", "style": "Ancient Egyptian Bread", "founded": "c. 2500 BCE", "notes": "Excavated bakeries fed pyramid builders; bell-shaped bedja ovens; emmer wheat bread daily rations"},
    {"name": "Deir el-Medina Bakery (Luxor)", "lat": 25.7281, "lon": 32.6018, "country": "Egypt", "style": "Egyptian Emmer Bread", "founded": "c. 1500 BCE", "notes": "Workers' village bakery; tomb painters received bread as wages; dozens of bread shapes found"},
    {"name": "Amarna Royal Bakery Site", "lat": 27.6483, "lon": 30.8978, "country": "Egypt", "style": "Royal Egyptian Bread", "founded": "c. 1350 BCE", "notes": "Akhenaten's capital had industrial bakeries; bread molds found; honey and date-enriched loaves"},
    {"name": "Ur Mesopotamian Ovens", "lat": 30.9628, "lon": 46.1028, "country": "Iraq", "style": "Sumerian Barley Bread", "founded": "c. 3000 BCE", "notes": "Ancient Ur had professional bakers; clay oven (tannour) tradition; barley was primary grain"},
    {"name": "Catalhoyuk Grain Site", "lat": 37.6663, "lon": 32.8280, "country": "Turkey", "style": "Neolithic Grain Processing", "founded": "c. 7500 BCE", "notes": "One of world's oldest settlements; evidence of grain grinding and possible early bread-like foods"},
    {"name": "Natufian Bread Site (Shubayqa)", "lat": 32.3833, "lon": 36.8000, "country": "Jordan", "style": "World's Oldest Bread", "founded": "c. 12000 BCE", "notes": "Oldest known bread (14,400 years old); charred flatbread remains; predates agriculture by 4,000 years"},
    {"name": "Abu Hureyra (Ancient Bakery)", "lat": 35.8667, "lon": 38.4000, "country": "Syria", "style": "Pre-agricultural Bread", "founded": "c. 11000 BCE", "notes": "Evidence of grain processing before farming; transition from foraging to cultivation"},
    {"name": "Ohalo II (Sea of Galilee)", "lat": 32.7233, "lon": 35.5672, "country": "Israel", "style": "Prehistoric Grain Processing", "founded": "c. 21000 BCE", "notes": "23,000-year-old campsite; earliest evidence of grain processing; grinding stones found"},
    {"name": "Gobekli Tepe", "lat": 37.2233, "lon": 38.9224, "country": "Turkey", "style": "Ritual Grain/Bread", "founded": "c. 9500 BCE", "notes": "World's oldest temple; grain processing linked to ritual feasting; beer and bread together"},
    {"name": "Roman Bakery at Ostia Antica", "lat": 41.7556, "lon": 12.2892, "country": "Italy", "style": "Roman Commercial Bakery", "founded": "2nd century", "notes": "Large-scale Roman bakery; grain mills, kneading machines, and ovens; supplied Rome's port city"},
    {"name": "Roman Forum Bread Stalls", "lat": 41.8925, "lon": 12.4853, "country": "Italy", "style": "Panis Civilis / Free Bread", "founded": "1st century BCE", "notes": "Roman grain dole (annona); free bread for citizens; Trajan's Market distributed grain and bread"},
    {"name": "Swiss Lake Dwelling Bread (Zurich)", "lat": 47.3667, "lon": 8.5500, "country": "Switzerland", "style": "Neolithic Flatbread", "founded": "c. 3700 BCE", "notes": "Charred bread remains from lake dwellings; earliest European bread evidence; emmer and barley"},
    {"name": "Vindolanda Roman Fort Bakery", "lat": 55.0000, "lon": -2.3600, "country": "UK", "style": "Roman Military Bread", "founded": "2nd century", "notes": "Roman garrison bakery on Hadrian's Wall; soldiers baked their own bread; grain mills excavated"},
    {"name": "Mohenjo-daro Grain Store", "lat": 27.3244, "lon": 68.1357, "country": "Pakistan", "style": "Indus Valley Bread", "founded": "c. 2500 BCE", "notes": "Great Granary of Mohenjo-daro; evidence of wheat and barley bread in Indus Valley civilization"},
    {"name": "Luxor Temple Bread Offerings", "lat": 25.6995, "lon": 32.6390, "country": "Egypt", "style": "Ritual Offering Bread", "founded": "c. 1400 BCE", "notes": "Bread offerings to Amun; temple reliefs show bread-making scenes; over 30 bread shapes depicted"},
    {"name": "Viking Bakery at Jorvik (York)", "lat": 53.9590, "lon": -1.0815, "country": "UK", "style": "Viking Rye/Barley Bread", "founded": "c. 900 CE", "notes": "Viking-age York; evidence of rye and barley bread baking; flat hearth breads and oat cakes"},
    {"name": "Maiden Castle Grain Storage", "lat": 50.6933, "lon": -2.4694, "country": "UK", "style": "Iron Age Bread", "founded": "c. 400 BCE", "notes": "Iron Age hill fort; large grain storage pits; evidence of communal bread-making in tribal Britain"},
    {"name": "Tomb of Ti Bakery Scene (Saqqara)", "lat": 29.8713, "lon": 31.2164, "country": "Egypt", "style": "Old Kingdom Bread", "founded": "c. 2400 BCE", "notes": "Mastaba tomb with detailed bread-making reliefs; shows kneading, shaping, and baking in molds"},
    {"name": "Ancient Jericho (Tell es-Sultan)", "lat": 31.8710, "lon": 35.4440, "country": "Palestine", "style": "Early Neolithic Grain", "founded": "c. 9000 BCE", "notes": "One of oldest cities; early grain cultivation and processing; transition to settled bread-making"},
    {"name": "Knossos Palace Granary (Crete)", "lat": 35.2978, "lon": 25.1631, "country": "Greece", "style": "Minoan Bread", "founded": "c. 2000 BCE", "notes": "Minoan palace stored grain in giant pithoi jars; bread was central to Minoan economy and ritual"},
    {"name": "Cerveteri Etruscan Tomb Bakery", "lat": 42.0000, "lon": 12.1000, "country": "Italy", "style": "Etruscan Bread", "founded": "c. 600 BCE", "notes": "Etruscan tombs depict bread-making and banqueting scenes; influenced Roman baking traditions"},
    {"name": "Ancient Athens Agora Bakeries", "lat": 37.9753, "lon": 23.7229, "country": "Greece", "style": "Greek Artos / Maza", "founded": "c. 500 BCE", "notes": "Athenian bakers (artopoios) in the Agora; wheat artos and barley maza; professional bakers' guild"},
    {"name": "Mehrgarh Grain Site", "lat": 29.3856, "lon": 67.6164, "country": "Pakistan", "style": "Early Neolithic Wheat", "founded": "c. 7000 BCE", "notes": "Earliest evidence of wheat and barley cultivation in South Asia; precursor to bread-making traditions"},
    {"name": "Cato's Roman Bread Recipes (Rome)", "lat": 41.9028, "lon": 12.4964, "country": "Italy", "style": "Libum / Placenta Cake-Bread", "founded": "c. 160 BCE", "notes": "Cato the Elder's De Agri Cultura records oldest surviving bread recipes; libum cheese bread"},
    {"name": "Pharaonic Brewery-Bakery (Abydos)", "lat": 26.1844, "lon": 31.9019, "country": "Egypt", "style": "Ancient Brewery-Bakery", "founded": "c. 3000 BCE", "notes": "Combined brewery-bakery; beer and bread production intertwined in ancient Egypt; emmer wheat base"},
]

# ===================================================================
# 8. ARTISAN BAKERIES WORLDWIDE (28 entries)
# ===================================================================
ARTISAN_BAKERIES = [
    {"name": "Tartine Bakery (San Francisco)", "lat": 37.7614, "lon": -122.4241, "country": "USA", "style": "Country Loaf / Morning Bun", "founded": "2002", "notes": "Chad Robertson's legendary country loaf; 4-hour line is a San Francisco ritual; global influence"},
    {"name": "Poilane (Paris)", "lat": 48.8500, "lon": 2.3267, "country": "France", "style": "Miche / Pain de campagne", "founded": "1932", "notes": "The 2kg sourdough miche is shipped worldwide; three generations of baking mastery; wood-fired"},
    {"name": "E5 Bakehouse (London)", "lat": 51.5340, "lon": -0.0556, "country": "UK", "style": "Sourdough / Heritage Grain", "founded": "2011", "notes": "Hackney railway arch bakery; heritage grain focus; baking school; London sourdough movement leader"},
    {"name": "Boulangerie Julien (Paris)", "lat": 48.8553, "lon": 2.3700, "country": "France", "style": "Baguette tradition", "founded": "1994", "notes": "Multiple Grand Prix de la Baguette winner; exemplary French baking craft"},
    {"name": "Bread Ahead (London Borough Market)", "lat": 51.5055, "lon": -0.0910, "country": "UK", "style": "Sourdough / Doughnuts", "founded": "2013", "notes": "Matthew Jones's bakery at Borough Market; baking school; famous sourdough doughnuts"},
    {"name": "Sullivan Street Bakery (New York)", "lat": 40.7589, "lon": -73.9899, "country": "USA", "style": "No-Knead / Italian Bread", "founded": "1994", "notes": "Jim Lahey's no-knead bread revolution; Italian-inspired high-hydration loaves; pizza bianca"},
    {"name": "Maison Kayser (Paris)", "lat": 48.8462, "lon": 2.3455, "country": "France", "style": "Baguette / Pain de campagne", "founded": "1996", "notes": "Eric Kayser's liquid levain system; 200+ bakeries globally; artisan baguette standard-bearer"},
    {"name": "Gail's Bakery (London Flagship)", "lat": 51.5350, "lon": -0.1556, "country": "UK", "style": "Sourdough / Pastries", "founded": "2005", "notes": "London artisan chain; sourdough from slow fermentation; neighborhood bakery model"},
    {"name": "Ble Sucre (Paris)", "lat": 48.8464, "lon": 2.3894, "country": "France", "style": "Croissant / Pain de mie", "founded": "2006", "notes": "Fabrice Le Bourdat; best croissant in Paris contender; near Gare de Lyon"},
    {"name": "Bourke Street Bakery (Sydney)", "lat": -33.8879, "lon": 151.2129, "country": "Australia", "style": "Sourdough / Sausage Roll", "founded": "2004", "notes": "Sydney sourdough icon; ginger brulee tart; pork and fennel sausage roll; multiple locations"},
    {"name": "Du Pain et des Idees (Paris)", "lat": 48.8714, "lon": 2.3614, "country": "France", "style": "Pain des Amis / Escargot", "founded": "2002", "notes": "Christophe Vasseur in a gorgeous 19th-century shop; best escargot pastries; artisan pain des amis"},
    {"name": "Boulangerie BO (Paris)", "lat": 48.8702, "lon": 2.3811, "country": "France", "style": "Baguette / Croissant", "founded": "2015", "notes": "Thierry Breton's bakery; rustic sourdough baguettes; long fermentation; 20th arrondissement"},
    {"name": "Manufactum Brot & Butter (Munich)", "lat": 48.1419, "lon": 11.5751, "country": "Germany", "style": "Artisan German Breads", "founded": "2012", "notes": "Curated German artisan bread shop; sources from traditional small bakeries across Germany"},
    {"name": "Panificio Bonci (Rome)", "lat": 41.9070, "lon": 12.4540, "country": "Italy", "style": "Pizza al taglio / Focaccia", "founded": "2003", "notes": "Gabriele Bonci -- the Michelangelo of pizza; high-hydration sourdough; seasonal toppings"},
    {"name": "Tartine Manufactory (SF)", "lat": 37.7614, "lon": -122.4071, "country": "USA", "style": "Porridge Bread / Danish Rye", "founded": "2016", "notes": "Robertson's expanded grain lab; porridge breads; Danish rye; ice cream and coffee too"},
    {"name": "Josey Baker Bread (The Mill, SF)", "lat": 37.7680, "lon": -122.4211, "country": "USA", "style": "Adventure Bread / Whole Grain", "founded": "2010", "notes": "Whole grain specialist; Adventure Bread (seeds/nuts only); collaborates with Four Barrel Coffee"},
    {"name": "Brasserie Bread (Sydney)", "lat": -33.8768, "lon": 151.2151, "country": "Australia", "style": "French-style Sourdough", "founded": "2001", "notes": "Michael Klausen's French-trained Sydney bakery; supplies top restaurants; traditional wood-fired ovens"},
    {"name": "Baluard Barceloneta (Barcelona)", "lat": 41.3809, "lon": 2.1890, "country": "Spain", "style": "Pa de vidre / Coca", "founded": "2007", "notes": "Barcelona's best bread; pa de vidre (glass bread) with open crumb; Anna Bellsola's artisan mastery"},
    {"name": "Fabrique Bakery (Stockholm)", "lat": 59.3383, "lon": 18.0653, "country": "Sweden", "style": "Sourdough / Cardamom Bun", "founded": "2008", "notes": "Swedish artisan chain; stone-oven sourdough; beloved cardamom buns; expanded to London and NYC"},
    {"name": "Seven Seeds Bakery (Melbourne)", "lat": -37.8062, "lon": 144.9620, "country": "Australia", "style": "Sourdough / Rye", "founded": "2007", "notes": "Melbourne specialty coffee and bread; artisan sourdough focus; Carlton neighborhood institution"},
    {"name": "Signorino Bakery (Melbourne)", "lat": -37.7960, "lon": 144.9620, "country": "Australia", "style": "Italian-style Bread / Ciabatta", "founded": "1999", "notes": "Italian-Australian artisan bakery; traditional ciabatta and pane di casa; wholesale to top chefs"},
    {"name": "Pratik Bakery (Istanbul)", "lat": 41.0370, "lon": 28.9850, "country": "Turkey", "style": "Sourdough / Simit", "founded": "2016", "notes": "Istanbul's new-wave artisan bakery; natural fermentation; combines Turkish and European traditions"},
    {"name": "Hart Bageri (Copenhagen)", "lat": 55.6761, "lon": 12.5683, "country": "Denmark", "style": "Danish Rye / Sourdough", "founded": "2018", "notes": "Richard Hart (ex-Tartine head baker); Nordic grain sourcing; Danish rugbrod tradition"},
    {"name": "Johan Sorensen Bakery (Copenhagen)", "lat": 55.6850, "lon": 12.5700, "country": "Denmark", "style": "Rugbrod / Cardamom Bread", "founded": "2015", "notes": "Artisan bakery in Norrebro; traditional Danish rye alongside innovative pastries"},
    {"name": "La Brea Bakery (Los Angeles)", "lat": 34.0622, "lon": -118.3445, "country": "USA", "style": "Sourdough / Rustic Breads", "founded": "1989", "notes": "Nancy Silverton pioneered LA artisan bread; sourdough starter from grape must; now national brand"},
    {"name": "Hobbs House Bakery (Cotswolds)", "lat": 51.6167, "lon": -2.3500, "country": "UK", "style": "Sherston Loaf / Wild White", "founded": "1920", "notes": "Fifth-generation family bakery; Tom Herbert is ambassador for Real Bread Campaign; Cotswolds icon"},
    {"name": "Backerei Domberger (Berlin)", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "style": "Vollkornbrot / Sauerteig", "founded": "1878", "notes": "Traditional Berlin bakery; whole-grain sourdough mastery; Schwarzbrot and Landbrot specialists"},
    {"name": "Levain Bakery (New York)", "lat": 40.7803, "lon": -73.9809, "country": "USA", "style": "Sourdough / Walnut Raisin", "founded": "1995", "notes": "Upper West Side; famous 6-oz cookies and outstanding walnut raisin sourdough loaves"},
]

# ===================================================================
# 9. BREAD FESTIVALS & MARKETS (28 entries)
# ===================================================================
BREAD_FESTIVALS = [
    {"name": "Fete du Pain (Paris)", "lat": 48.8530, "lon": 2.3499, "country": "France", "style": "National Bread Festival", "founded": "1996", "notes": "Annual bread festival at Notre-Dame; artisan bakers demonstrate; free tastings; May celebration"},
    {"name": "Borough Market Bread Stalls (London)", "lat": 51.5055, "lon": -0.0910, "country": "UK", "style": "Artisan Bread Market", "founded": "1756", "notes": "London's finest food market; Bread Ahead, Olivier's, and artisan bakers; Saturday is peak"},
    {"name": "Brotmarkt (Ulm, Germany)", "lat": 48.3984, "lon": 9.9916, "country": "Germany", "style": "German Bread Market", "founded": "Medieval", "notes": "Annual bread market at Ulm Minster square; Germany's bread culture celebrated; regional varieties"},
    {"name": "Festa del Pane (Altamura, Italy)", "lat": 40.8263, "lon": 16.5522, "country": "Italy", "style": "Pane di Altamura Festival", "founded": "Traditional", "notes": "Annual celebration of Altamura's DOP bread; wood-fired community ovens; processions and tastings"},
    {"name": "Bread Festival of Matera", "lat": 40.6654, "lon": 16.6043, "country": "Italy", "style": "Heritage Bread Festival", "founded": "2010", "notes": "Matera celebrates its cave-baked bread tradition; ancient oven demonstrations; Sassi district"},
    {"name": "Real Bread Campaign Festival (London)", "lat": 51.5074, "lon": -0.1278, "country": "UK", "style": "Real Bread Week", "founded": "2009", "notes": "Sustain's annual Real Bread Week; promotes additive-free bread; bakery open days nationwide"},
    {"name": "Grain Gathering (Skagit Valley, WA)", "lat": 48.4510, "lon": -122.3375, "country": "USA", "style": "Grain & Bread Conference", "founded": "2014", "notes": "Annual gathering of grain farmers, millers, and bakers; heritage grain field tours; bread baking demos"},
    {"name": "Bread Days (Journees du Pain, France)", "lat": 48.8566, "lon": 2.3522, "country": "France", "style": "National Bread Days", "founded": "2000", "notes": "October celebration of French bread; bakeries nationwide open doors; baguette competitions"},
    {"name": "Bread Festival (Genzano di Roma)", "lat": 41.7078, "lon": 12.6906, "country": "Italy", "style": "Pane di Genzano IGP Festival", "founded": "Traditional", "notes": "Castelli Romani bread festival; Pane casareccio di Genzano IGP; wood-oven demonstrations"},
    {"name": "Christstollen Festival (Dresden)", "lat": 51.0504, "lon": 13.7373, "country": "Germany", "style": "Stollenfest", "founded": "1994", "notes": "Giant 3-ton Stollen paraded through Dresden; second Saturday of Advent; Christmas bread tradition"},
    {"name": "San Francisco Sourdough Festival", "lat": 37.8080, "lon": -122.4177, "country": "USA", "style": "Sourdough Festival", "founded": "2015", "notes": "Celebration of SF sourdough tradition; Boudin and artisan bakers; tastings at Fisherman's Wharf"},
    {"name": "Bread & Butter (Berlin Food Festival)", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "style": "Artisan Bread Expo", "founded": "2001", "notes": "Europe's largest lifestyle food expo; artisan bread showcases; sourdough workshops"},
    {"name": "Salon du Pain (Grand Palais, Paris)", "lat": 48.8662, "lon": 2.3126, "country": "France", "style": "Professional Bread Salon", "founded": "2005", "notes": "Annual professional boulangerie salon; artisan bakers, millers, equipment; Coupe du Monde de la Boulangerie"},
    {"name": "Kenyerunk Napja (Budapest)", "lat": 47.4979, "lon": 19.0402, "country": "Hungary", "style": "Hungarian Bread Day", "founded": "Traditional", "notes": "August 20 -- Hungarian Bread Day; celebrates new harvest; ceremonial bread baking; national holiday"},
    {"name": "Fiesta del Pan (Valleseco, Gran Canaria)", "lat": 28.0520, "lon": -15.5730, "country": "Spain", "style": "Canarian Bread Festival", "founded": "Traditional", "notes": "Canary Islands bread festival; traditional pan de papa (potato bread); community wood-oven baking"},
    {"name": "Naan Festival (Bukhara)", "lat": 39.7683, "lon": 64.4219, "country": "Uzbekistan", "style": "Central Asian Bread Festival", "founded": "Traditional", "notes": "Uzbek non (bread) celebrations; decorative bread competitions; tandyr oven demonstrations"},
    {"name": "World Bread Day Events (Global)", "lat": 48.2082, "lon": 16.3738, "country": "Austria (IUBG HQ)", "style": "World Bread Day", "founded": "2006", "notes": "October 16 -- World Bread Day; IUBG-organized; bakeries worldwide celebrate; baking workshops"},
    {"name": "Coupe du Monde de la Boulangerie (Paris)", "lat": 48.9538, "lon": 2.6358, "country": "France", "style": "World Cup of Baking", "founded": "1992", "notes": "Bakery World Cup at Europain expo; national teams compete in bread, viennoiserie, and artistic pieces"},
    {"name": "Bread & Roses Festival (London)", "lat": 51.4613, "lon": -0.1156, "country": "UK", "style": "Community Bread Festival", "founded": "2010", "notes": "Annual Clapham community festival; bread stalls, baking workshops, live music; charity fundraiser"},
    {"name": "Breadfest (Hay-on-Wye, Wales)", "lat": 52.0741, "lon": -3.1241, "country": "UK", "style": "Welsh Bread Festival", "founded": "2016", "notes": "Annual bread festival in Welsh border town; artisan bakers, sourdough workshops; heritage flour demos"},
    {"name": "Australian Bread Week", "lat": -33.8688, "lon": 151.2093, "country": "Australia", "style": "National Bread Week", "founded": "2012", "notes": "Australian sourdough celebration; bakery open days; bread-making classes; grain farm visits"},
    {"name": "Brot & Spiele (Trier, Germany)", "lat": 49.7490, "lon": 6.6371, "country": "Germany", "style": "Bread & Games Roman Festival", "founded": "2003", "notes": "Roman-themed bread festival at Trier amphitheater; ancient Roman bread recipes recreated"},
    {"name": "Festa della Focaccia (Recco)", "lat": 44.3631, "lon": 9.1475, "country": "Italy", "style": "Focaccia Festival", "founded": "Traditional", "notes": "Recco's annual focaccia col formaggio festival; street vendors; competitive focaccia judging"},
    {"name": "Kornmarkt (Lucerne Grain Market)", "lat": 47.0502, "lon": 8.3093, "country": "Switzerland", "style": "Heritage Grain/Bread Market", "founded": "Medieval", "notes": "Historic grain market square; modern artisan bread stalls; Swiss Ruchbrot and Zopf showcased"},
    {"name": "IBS Bread Summit (Various)", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "style": "International Bread Summit", "founded": "2018", "notes": "Annual professional summit for artisan bakers; grain sourcing, fermentation science, business"},
    {"name": "Tartine Block Party (San Francisco)", "lat": 37.7614, "lon": -122.4071, "country": "USA", "style": "Artisan Baker Gathering", "founded": "2017", "notes": "Annual gathering at Tartine Manufactory; guest bakers worldwide; grain tastings; community feast"},
    {"name": "Scottish Bakers Conference (Edinburgh)", "lat": 55.9533, "lon": -3.1883, "country": "UK", "style": "Scottish Bread Expo", "founded": "1891", "notes": "Scotland's oldest baking trade body; annual conference showcases Scottish morning rolls and breads"},
    {"name": "Bread Olympics (Iba Munich)", "lat": 48.1351, "lon": 11.5820, "country": "Germany", "style": "Iba Bread Olympics", "founded": "1949", "notes": "World's largest baking trade fair; bread olympics with teams from 40+ countries; held every 3 years"},
]

# ===================================================================
# 10. BREAD MUSEUMS & SCHOOLS (28 entries)
# ===================================================================
BREAD_MUSEUMS = [
    {"name": "Musee du Pain (Paris)", "lat": 48.8617, "lon": 2.3476, "country": "France", "style": "Bread Museum", "founded": "1978", "notes": "Museum of bread-making history; antique bakery equipment; French bread heritage exhibits"},
    {"name": "Panarium -- Bread Museum (Weinheim)", "lat": 49.5511, "lon": 8.6669, "country": "Germany", "style": "Bread Museum", "founded": "1978", "notes": "German bread museum; 6,000 years of bread history; over 3,200 German bread varieties documented"},
    {"name": "Museum of Bread Culture (Ulm)", "lat": 48.3984, "lon": 9.9916, "country": "Germany", "style": "Brotkultur Museum", "founded": "1955", "notes": "World's first bread museum; 18,000+ artifacts; art collection on bread themes; Eiselen Foundation"},
    {"name": "Deutsches Brotmuseum (Ulm)", "lat": 48.3979, "lon": 9.9923, "country": "Germany", "style": "German Bread Museum", "founded": "1955", "notes": "Comprehensive exhibits on German and global bread history; grain cultivation to final loaf"},
    {"name": "Museo del Pane (Altamura)", "lat": 40.8263, "lon": 16.5522, "country": "Italy", "style": "Bread Museum", "founded": "2005", "notes": "Museum dedicated to Pane di Altamura DOP; baking demonstrations; ancient oven displays"},
    {"name": "Le Cordon Bleu (Paris)", "lat": 48.8557, "lon": 2.2895, "country": "France", "style": "Baking School", "founded": "1895", "notes": "World's most prestigious culinary school; boulangerie and patisserie diploma programs"},
    {"name": "San Francisco Baking Institute", "lat": 37.6688, "lon": -122.0810, "country": "USA", "style": "Professional Baking School", "founded": "1996", "notes": "Michel Suas founded this artisan baking school; sourdough mastery courses; professional certification"},
    {"name": "King Arthur Baking School (Vermont)", "lat": 43.6489, "lon": -72.3274, "country": "USA", "style": "Community Baking School", "founded": "1992", "notes": "America's oldest flour company (1790); baking education center; sourdough and bread classes"},
    {"name": "Bread Ahead School (London)", "lat": 51.5055, "lon": -0.0910, "country": "UK", "style": "Artisan Baking School", "founded": "2013", "notes": "Borough Market baking school; sourdough masterclasses; doughnut workshops; hands-on learning"},
    {"name": "Ecole de Boulangerie et de Patisserie de Paris", "lat": 48.8396, "lon": 2.3755, "country": "France", "style": "Professional Boulangerie School", "founded": "2012", "notes": "Paris baking school; intensive baguette and viennoiserie programs; French baking arts diploma"},
    {"name": "Richemont Centre (Lucerne)", "lat": 47.0502, "lon": 8.3093, "country": "Switzerland", "style": "Swiss Baking School", "founded": "1945", "notes": "Swiss national baking training center; professional bread and pastry programs; international students"},
    {"name": "National Bakery School (London South Bank)", "lat": 51.4988, "lon": -0.1027, "country": "UK", "style": "Professional Baking College", "founded": "1894", "notes": "London South Bank University; UK's premier bakery science program; research into bread quality"},
    {"name": "Weinheim Baking Academy (Akademie Deutsches Baeckerhandwerk)", "lat": 49.5500, "lon": 8.6667, "country": "Germany", "style": "German Master Baker Academy", "founded": "1930", "notes": "Premier German baking academy; Meister (Master Baker) certification; international training"},
    {"name": "Museo del Pane di Sardegna (Borore)", "lat": 40.2239, "lon": 8.9978, "country": "Italy", "style": "Sardinian Bread Museum", "founded": "2006", "notes": "Museum of Sardinian bread traditions; pane carasau, pane frattau, pistoccu; ritual breads displayed"},
    {"name": "Bread Museum (Aghdash, Azerbaijan)", "lat": 40.6478, "lon": 47.4625, "country": "Azerbaijan", "style": "Bread Museum", "founded": "2010", "notes": "Museum of Azerbaijani bread and tandir oven culture; regional flatbread traditions"},
    {"name": "INBP -- Institut National de la Boulangerie Patisserie (Rouen)", "lat": 49.4432, "lon": 1.0993, "country": "France", "style": "National Baking Institute", "founded": "1974", "notes": "France's national baking institute; trains professional boulangers; research and innovation"},
    {"name": "Culinary Institute of America -- Bread Track (Hyde Park)", "lat": 41.7796, "lon": -73.9408, "country": "USA", "style": "Baking & Pastry Program", "founded": "1946", "notes": "CIA's baking and pastry arts program; artisan bread track; state-of-the-art bakery labs"},
    {"name": "Poilane Baking School (Paris)", "lat": 48.8502, "lon": 2.3265, "country": "France", "style": "Artisan Baking Atelier", "founded": "2002", "notes": "Apollonia Poilane offers bread-making workshops at the rue du Cherche-Midi bakery"},
    {"name": "Bread Museum (Plovdiv, Bulgaria)", "lat": 42.1354, "lon": 24.7453, "country": "Bulgaria", "style": "Bread Museum", "founded": "2015", "notes": "Bulgarian bread heritage museum; ritual breads for weddings, holidays; traditional oven displays"},
    {"name": "E5 Bakehouse Baking School (London)", "lat": 51.5340, "lon": -0.0556, "country": "UK", "style": "Community Baking School", "founded": "2011", "notes": "Hackney community baking classes; sourdough starters; heritage grain workshops; evening courses"},
    {"name": "Raimugido Bread Lab (Tokyo)", "lat": 35.6762, "lon": 139.6503, "country": "Japan", "style": "Bread Research & School", "founded": "2015", "notes": "Japanese bread research lab; shokupan perfection; fermentation science; professional training"},
    {"name": "Bread Lab (Washington State University)", "lat": 48.5428, "lon": -122.4443, "country": "USA", "style": "Grain Research Lab", "founded": "2011", "notes": "Dr. Stephen Jones's Bread Lab; heritage grain breeding; farmer-baker-brewer collaboration; Skagit Valley"},
    {"name": "Baking School of Ireland (Dublin)", "lat": 53.3498, "lon": -6.2603, "country": "Ireland", "style": "Professional Baking School", "founded": "2008", "notes": "Irish artisan baking courses; soda bread tradition; sourdough workshops; community classes"},
    {"name": "Pain et Partage Baking School (Lyon)", "lat": 45.7640, "lon": 4.8357, "country": "France", "style": "Community Baking School", "founded": "2016", "notes": "Lyon community baking school; social enterprise; teaches bread-making to refugees and locals"},
    {"name": "Museo del Pan (Mayorga, Spain)", "lat": 42.1667, "lon": -5.2500, "country": "Spain", "style": "Bread Museum", "founded": "2009", "notes": "Spanish bread museum in Tierra de Campos; Castilian bread heritage; traditional hornos (ovens)"},
    {"name": "Sourdough Library (Puratos, Belgium)", "lat": 50.7333, "lon": 4.2333, "country": "Belgium", "style": "Sourdough Starter Collection", "founded": "2013", "notes": "World's largest sourdough library; 130+ starters from 25 countries; scientific preservation center"},
    {"name": "Moulin de la Vierge School (Paris)", "lat": 48.8413, "lon": 2.3192, "country": "France", "style": "Artisan Baking Atelier", "founded": "2000", "notes": "Learn stone-milled bread baking in wood-fired ovens; classes at the Paris bakery"},
    {"name": "Breadmaking Museum (Bonnieux, Provence)", "lat": 43.8262, "lon": 5.3089, "country": "France", "style": "Provencal Bread Museum", "founded": "1983", "notes": "Museum in Luberon village; antique ovens and tools; Provencal bread traditions; flour-milling exhibits"},
]

# ===================================================================
# MODE CONFIGURATION MAP
# ===================================================================
_MODE_MAP = {
    "French Boulangerie Heritage": {
        "data": FRENCH_BOULANGERIE,
        "icon": "home",
        "color": "blue",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Bread Style", "Founded", "Notes"],
    },
    "German Bread Traditions": {
        "data": GERMAN_BREAD,
        "icon": "home",
        "color": "red",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Bread Style", "Founded", "Notes"],
    },
    "Italian Bread & Focaccia": {
        "data": ITALIAN_BREAD,
        "icon": "home",
        "color": "green",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Bread Style", "Founded", "Notes"],
    },
    "Sourdough Heritage": {
        "data": SOURDOUGH_HERITAGE,
        "icon": "grain",
        "color": "orange",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Bread Style", "Founded", "Notes"],
    },
    "Middle Eastern Flatbreads": {
        "data": MIDDLE_EASTERN_FLATBREADS,
        "icon": "record",
        "color": "darkred",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Bread Style", "Founded", "Notes"],
    },
    "Asian Bread Traditions": {
        "data": ASIAN_BREAD,
        "icon": "home",
        "color": "cadetblue",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Bread Style", "Founded", "Notes"],
    },
    "Ancient Bread History": {
        "data": ANCIENT_BREAD,
        "icon": "asterisk",
        "color": "beige",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Bread Type", "Period", "Notes"],
    },
    "Artisan Bakeries Worldwide": {
        "data": ARTISAN_BAKERIES,
        "icon": "star",
        "color": "pink",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Specialty", "Founded", "Notes"],
    },
    "Bread Festivals & Markets": {
        "data": BREAD_FESTIVALS,
        "icon": "calendar",
        "color": "purple",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Event Type", "Founded", "Notes"],
    },
    "Bread Museums & Schools": {
        "data": BREAD_MUSEUMS,
        "icon": "education",
        "color": "darkpurple",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Type", "Founded", "Notes"],
    },
}

# ===================================================================
# HELPERS
# ===================================================================

def _build_popup(entry: dict, fields: list, labels: list) -> str:
    """Build a rich HTML popup string with escaped content."""
    name = html_module.escape(str(entry.get("name", "")))
    rows = ""
    for field, label in zip(fields, labels):
        val = html_module.escape(str(entry.get(field, "N/A")))
        rows += (
            f'<tr>'
            f'<td style="padding:3px 8px;font-weight:600;color:{_ACCENT};'
            f'vertical-align:top;white-space:nowrap;">{label}</td>'
            f'<td style="padding:3px 8px;color:{_TEXT};">{val}</td>'
            f'</tr>'
        )
    return (
        f'<div style="font-family:Inter,sans-serif;min-width:260px;max-width:340px;'
        f'background:{_SURFACE};border:1px solid #2a3550;border-radius:8px;padding:10px;">'
        f'<h4 style="margin:0 0 8px;color:{_ACCENT};font-size:14px;">{name}</h4>'
        f'<table style="border-collapse:collapse;font-size:12px;">{rows}</table>'
        f'</div>'
    )


def _build_map(data: list, mode_cfg: dict, zoom: int = 2) -> folium.Map:
    """Create a folium map with markers for the given dataset."""
    if not data:
        return folium.Map(location=[20, 0], zoom_start=zoom, tiles="CartoDB dark_matter")

    avg_lat = sum(d["lat"] for d in data) / len(data)
    avg_lon = sum(d["lon"] for d in data) / len(data)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    for entry in data:
        popup_html = _build_popup(entry, mode_cfg["fields"], mode_cfg["labels"])
        folium.Marker(
            location=[entry["lat"], entry["lon"]],
            popup=folium.Popup(popup_html, max_width=360),
            tooltip=entry["name"],
            icon=folium.Icon(
                icon=mode_cfg["icon"],
                prefix="glyphicon",
                color=mode_cfg["color"],
            ),
        ).add_to(m)

    return m


def _get_country_stats(data: list) -> dict:
    """Count entries per country."""
    counts: dict = {}
    for d in data:
        c = d.get("country", "Unknown")
        counts[c] = counts.get(c, 0) + 1
    return counts


# ===================================================================
# MAIN RENDER FUNCTION
# ===================================================================

def render_bread_maps_tab():
    """Render the Bread & Bakery Heritage Explorer tab."""

    # ---- Header ----
    st.markdown(
        '<div class="tab-header pink">'
        "<h4>Bread & Bakery Heritage Explorer</h4>"
        "<p>French boulangeries, German Schwarzbrot, Italian focaccia, sourdough traditions, ancient bakeries & bread festivals worldwide</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        key="bread_maps_mode",
    )

    cfg = _MODE_MAP[mode]
    data = cfg["data"]

    # ---- Stats row ----
    country_stats = _get_country_stats(data)
    top_country = max(country_stats, key=country_stats.get) if country_stats else "N/A"
    top_count = country_stats.get(top_country, 0)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Locations", len(data))
    c2.metric("Countries / Regions", len(country_stats))
    c3.metric("Top Country", top_country)
    c4.metric("Locations in Top", top_count)

    # ---- Description blurbs ----
    _DESCRIPTIONS = {
        "French Boulangerie Heritage": (
            "France is the spiritual home of bread. From the crispy baguette de "
            "tradition -- protected by law since 1993 -- to the massive sourdough "
            "miche of Poilane, the rustic pain de campagne, and the flaky croissant, "
            "French boulangeries represent centuries of baking artistry. The Grand "
            "Prix de la Baguette is Paris's most coveted bakery prize."
        ),
        "German Bread Traditions": (
            "Germany registers over 3,200 distinct bread varieties -- more than any "
            "nation on earth. From the dark, 24-hour Pumpernickel of Westphalia to "
            "the lye-dipped Brezeln of Swabia, the rye Schwarzbrot of the north, and "
            "the Vollkornbrot whole-grain tradition, German bread culture was inscribed "
            "on the UNESCO Intangible Cultural Heritage list in 2014."
        ),
        "Italian Bread & Focaccia": (
            "Italy's bread landscape is as diverse as its regions. Pane di Altamura "
            "holds the EU's first DOP for bread. Ciabatta was invented in 1982 in "
            "Veneto. Focaccia di Recco has been made since the Crusades. Sardinia's "
            "pane carasau (carta di musica) is paper-thin. Tuscan bread is famously "
            "unsalted. Each region tells a story through its dough."
        ),
        "Sourdough Heritage": (
            "Sourdough is humanity's oldest leavening method, dating back at least "
            "5,000 years. San Francisco's fog-nurtured Lactobacillus sanfranciscensis "
            "creates a unique tang. Finland's ruisleipa rye sourdough is a daily "
            "staple. Nordic bakers ferment with wild cultures. Today, Tartine's "
            "country loaf and Poilane's miche inspire a global artisan renaissance."
        ),
        "Middle Eastern Flatbreads": (
            "The cradle of civilization is also the cradle of bread. Pita has been "
            "baked in taboon clay ovens for millennia. Armenian lavash is UNESCO "
            "Intangible Heritage. Iranian sangak is baked on hot pebbles. Turkish "
            "simit dates to the Ottoman era. Georgian shotis puri emerges from "
            "underground tone ovens. These flatbreads connect us to 12,000 years "
            "of baking history."
        ),
        "Asian Bread Traditions": (
            "From Japan's pillowy shokupan milk bread to China's steamed mantou "
            "buns, India's tandoori naan, Vietnam's rice-flour banh mi baguettes, "
            "and Korea's viral garlic cream cheese bread, Asia's bread traditions "
            "span ancient clay-oven techniques and modern innovation. Roti canai, "
            "paratha, and Uyghur nang reflect Silk Road connections."
        ),
        "Ancient Bread History": (
            "The world's oldest known bread is 14,400 years old, found at Shubayqa "
            "in Jordan -- predating agriculture by 4,000 years. Pompeii's eruption "
            "in 79 AD preserved over 30 bakeries with carbonized loaves. Egyptian "
            "pyramid builders received daily bread rations. The Hymn to Ninkasi from "
            "Sumer is the oldest bread-and-beer recipe. Bread is the foundation of "
            "civilization itself."
        ),
        "Artisan Bakeries Worldwide": (
            "The global artisan bread renaissance is led by visionary bakers: Chad "
            "Robertson at Tartine (San Francisco), Apollonia Poilane in Paris, Jim "
            "Lahey's no-knead revolution in New York, the E5 Bakehouse in London's "
            "railway arches, and Gabriele Bonci's pizza al taglio in Rome. These "
            "bakers prioritize slow fermentation, heritage grains, and craft over "
            "industrial speed."
        ),
        "Bread Festivals & Markets": (
            "From the Fete du Pain at Notre-Dame to Dresden's giant Stollen parade, "
            "London's Borough Market bread stalls, and the Bakery World Cup "
            "(Coupe du Monde de la Boulangerie), bread festivals celebrate the art "
            "and heritage of baking. Community ovens fire up, ancient recipes are "
            "recreated, and bakers from around the world share their craft."
        ),
        "Bread Museums & Schools": (
            "The Museum of Bread Culture in Ulm (1955) was the world's first bread "
            "museum. The Puratos Sourdough Library in Belgium preserves 130+ starters "
            "from 25 countries. Le Cordon Bleu trains bakers since 1895. The WSU "
            "Bread Lab breeds heritage grains. From the San Francisco Baking "
            "Institute to King Arthur's Vermont school, bread education keeps "
            "ancient traditions alive."
        ),
    }

    st.markdown(
        f'<div style="background:{_SURFACE};border:1px solid #2a3550;border-radius:8px;'
        f'padding:14px 18px;margin:8px 0 12px;color:{_TEXT};font-size:14px;line-height:1.5;">'
        f'{_DESCRIPTIONS.get(mode, "")}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ---- Map ----
    zoom = 5 if mode in ("French Boulangerie Heritage", "German Bread Traditions", "Italian Bread & Focaccia") else 3
    if mode == "Middle Eastern Flatbreads":
        zoom = 4
    elif mode == "Asian Bread Traditions":
        zoom = 3
    elif mode == "Ancient Bread History":
        zoom = 3
    elif mode == "Sourdough Heritage":
        zoom = 3
    m = _build_map(data, cfg, zoom=zoom)
    st_html(m._repr_html_(), height=500)

    # ---- Dataframe ----
    st.markdown(
        f"#### Data Table: {mode}",
    )

    # Build a clean dataframe from the dataset
    df_records = []
    for entry in data:
        row = {"Name": entry["name"], "Latitude": entry["lat"], "Longitude": entry["lon"]}
        for field, label in zip(cfg["fields"], cfg["labels"]):
            row[label] = entry.get(field, "N/A")
        df_records.append(row)

    df = pd.DataFrame(df_records)
    st.dataframe(df, use_container_width=True)

    # ---- CSV Download ----
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    st.download_button(
        label=f"Download {mode} CSV",
        data=csv_bytes,
        file_name=f"bread_heritage_{mode.lower().replace(' ', '_').replace('&', 'and')}.csv",
        mime="text/csv",
        key=f"dl_bread_{mode}",
    )

    # ---- Country breakdown ----
    st.markdown("#### Country / Region Breakdown")
    breakdown_df = (
        pd.DataFrame(
            [(k, v) for k, v in sorted(country_stats.items(), key=lambda x: -x[1])]
        )
        .rename(columns={0: "Country", 1: "Count"})
    )
    st.dataframe(breakdown_df, use_container_width=True)

    # ---- Founding Era Analysis ----
    st.markdown("#### Founding Era Analysis")
    era_buckets: dict = {
        "Ancient / Prehistoric": 0,
        "Medieval (before 1500)": 0,
        "Early Modern (1500-1799)": 0,
        "Industrial Age (1800-1949)": 0,
        "Modern Artisan (1950-1999)": 0,
        "21st Century (2000+)": 0,
        "Traditional / Approximate": 0,
    }

    for entry in data:
        founded = str(entry.get("founded", ""))
        # Try to extract a numeric year
        year = None
        for token in founded.replace("c.", "").replace("~", "").split():
            cleaned = token.strip("().,;")
            if cleaned.lstrip("-").isdigit():
                year = int(cleaned)
                break
            elif cleaned.endswith("BCE") or cleaned.endswith("BC"):
                num_part = cleaned.replace("BCE", "").replace("BC", "").strip()
                if num_part.isdigit():
                    year = -int(num_part)
                    break

        if year is None:
            era_buckets["Traditional / Approximate"] += 1
        elif year < 0:
            era_buckets["Ancient / Prehistoric"] += 1
        elif year < 1500:
            era_buckets["Medieval (before 1500)"] += 1
        elif year < 1800:
            era_buckets["Early Modern (1500-1799)"] += 1
        elif year < 1950:
            era_buckets["Industrial Age (1800-1949)"] += 1
        elif year < 2000:
            era_buckets["Modern Artisan (1950-1999)"] += 1
        else:
            era_buckets["21st Century (2000+)"] += 1

    # Filter out zero-count eras for cleaner display
    era_data = [(k, v) for k, v in era_buckets.items() if v > 0]
    if era_data:
        era_df = pd.DataFrame(era_data, columns=["Era", "Count"])
        st.dataframe(era_df, use_container_width=True)

    # ---- Quick facts per mode ----
    st.markdown("#### Quick Facts")
    _QUICK_FACTS = {
        "French Boulangerie Heritage": [
            "The French baguette was added to UNESCO Intangible Cultural Heritage in 2022.",
            "A 1993 French law (Decret Pain) defines what constitutes a baguette de tradition.",
            "Paris holds an annual Grand Prix de la Baguette -- the winner supplies the Elysee Palace.",
            "France has approximately 35,000 boulangeries, roughly one per 1,800 inhabitants.",
        ],
        "German Bread Traditions": [
            "German bread culture (Brotkultur) was inscribed on the UNESCO Intangible Heritage list in 2014.",
            "Germany has over 3,200 officially registered bread varieties -- the most in the world.",
            "Pumpernickel from Westphalia is baked for 16-24 hours at declining temperatures.",
            "The average German consumes about 55 kg of bread per year, among the highest globally.",
        ],
        "Italian Bread & Focaccia": [
            "Pane di Altamura was the first bread in Europe to receive DOP (Protected Designation of Origin) status.",
            "Ciabatta was invented in 1982 by Arnaldo Cavallari as Italy's answer to the French baguette.",
            "Tuscan pane sciocco (unsalted bread) dates to a 12th-century salt tax dispute with Pisa.",
            "Sardinian pane carasau (carta di musica) can last months and was food for shepherds.",
        ],
        "Sourdough Heritage": [
            "The unique tang of San Francisco sourdough comes from Lactobacillus sanfranciscensis and wild yeast.",
            "Sourdough fermentation has been traced back at least 5,000 years to ancient Egypt.",
            "Chad Robertson's Tartine Country Loaf recipe has been called the most influential bread of the 21st century.",
            "The Puratos Sourdough Library in Belgium preserves over 130 sourdough starters from around the world.",
        ],
        "Middle Eastern Flatbreads": [
            "Armenian lavash was inscribed on the UNESCO Intangible Cultural Heritage list in 2014.",
            "Egyptian aish baladi means 'bread of life' -- it is the most subsidized food in Egypt.",
            "Georgian bread-making (shotis puri in tone ovens) is a living UNESCO heritage tradition.",
            "The oldest known bread (14,400 years old) was found at Shubayqa 1 in northeastern Jordan.",
        ],
        "Asian Bread Traditions": [
            "Japanese shokupan (milk bread) uses the tangzhong/yudane method for extreme softness.",
            "Vietnamese banh mi combines French baguette technique with rice flour for a lighter, crispier crust.",
            "Korean garlic cream cheese bread became a global viral sensation starting in the early 2020s.",
            "Chinese mantou (steamed buns) have been a staple since at least the 3rd century.",
        ],
        "Ancient Bread History": [
            "The oldest bread ever found (14,400 years old) predates agriculture by 4,000 years.",
            "Over 30 commercial bakeries have been excavated in Pompeii, preserved by Vesuvius in 79 AD.",
            "Egyptian pyramid builders received daily rations of bread and beer as their primary wages.",
            "The Hymn to Ninkasi (c. 1800 BCE) from Sumer is the world's oldest recorded bread-and-beer recipe.",
        ],
        "Artisan Bakeries Worldwide": [
            "Jim Lahey's no-knead bread recipe (published in NYT, 2006) democratized home bread-baking.",
            "Tartine Bakery's country loaf requires a 4+ hour queue and sells out every day.",
            "The Real Bread Campaign in the UK advocates for additive-free bread with transparent ingredients.",
            "Gabriele Bonci is called the Michelangelo of Pizza for his high-hydration sourdough focaccia.",
        ],
        "Bread Festivals & Markets": [
            "Munich's Oktoberfest started as a royal wedding in 1810 and always featured ceremonial bread.",
            "The Coupe du Monde de la Boulangerie (Bakery World Cup) has been held since 1992.",
            "Dresden's Stollenfest features a 3-ton Christstollen paraded through the city on the second Advent Saturday.",
            "Borough Market in London has operated as a food market since at least 1756.",
        ],
        "Bread Museums & Schools": [
            "The Museum of Bread Culture in Ulm, founded in 1955, was the world's first bread museum.",
            "The Puratos Sourdough Library preserves active sourdough starters from over 25 countries.",
            "King Arthur Flour, founded in 1790, is the oldest flour company in the United States.",
            "The WSU Bread Lab breeds heritage grain varieties specifically for flavor and nutrition, not just yield.",
        ],
    }

    facts = _QUICK_FACTS.get(mode, [])
    for fact in facts:
        st.markdown(
            f'<div style="background:{_SURFACE};border-left:3px solid {_ACCENT};'
            f'padding:8px 14px;margin:4px 0;color:{_TEXT};font-size:13px;'
            f'border-radius:0 6px 6px 0;">'
            f'{html_module.escape(fact)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ---- Footer ----
    st.markdown("---")
    st.caption(
        "Data is curated from historical records, bakery publications, bread heritage guides, "
        "and culinary databases. Locations are approximate. Bakery hours and availability "
        "may change -- check official sources before visiting."
    )
