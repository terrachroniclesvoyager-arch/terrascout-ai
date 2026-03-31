"""
Cheese & Dairy Explorer module for TerraScout AI.
Displays curated maps of world cheese regions, DOP/AOC designations,
dairy traditions, cheese museums, and festivals with preset coordinate
data and interactive Folium maps.
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
import html as html_module
from streamlit.components.v1 import html as st_html


# ═══════════════════════════════════════════
# MODE DEFINITIONS
# ═══════════════════════════════════════════
MODE_OPTIONS = [
    "French Cheese AOC Regions",
    "Italian Cheese DOP",
    "Swiss Cheese Traditions",
    "British Cheese Heritage",
    "Dutch & Belgian Cheese",
    "Spanish & Portuguese Cheese",
    "Greek & Mediterranean Cheese",
    "American Artisan Cheese",
    "Ancient Cheese History",
    "Cheese Museums & Festivals",
]

MODE_ICONS = {
    "French Cheese AOC Regions": "\U0001f9c0",
    "Italian Cheese DOP": "\U0001f1ee\U0001f1f9",
    "Swiss Cheese Traditions": "\U0001f1e8\U0001f1ed",
    "British Cheese Heritage": "\U0001f1ec\U0001f1e7",
    "Dutch & Belgian Cheese": "\U0001f1f3\U0001f1f1",
    "Spanish & Portuguese Cheese": "\U0001f1ea\U0001f1f8",
    "Greek & Mediterranean Cheese": "\U0001f1ec\U0001f1f7",
    "American Artisan Cheese": "\U0001f1fa\U0001f1f8",
    "Ancient Cheese History": "\U0001f3db\ufe0f",
    "Cheese Museums & Festivals": "\U0001f3aa",
}

MODE_DESCRIPTIONS = {
    "French Cheese AOC Regions": "Explore France's prestigious AOC/AOP cheese regions from Normandy to the Pyrenees.",
    "Italian Cheese DOP": "Discover Italy's DOP-protected cheeses across every region, from Parmigiano to Pecorino.",
    "Swiss Cheese Traditions": "The alpine dairy heritage of Switzerland, from Emmental valleys to mountain chalets.",
    "British Cheese Heritage": "Centuries of British cheesemaking from Cheddar Gorge to Stilton country.",
    "Dutch & Belgian Cheese": "Gouda markets, Edam traditions, and Trappist monastery cheeses of the Low Countries.",
    "Spanish & Portuguese Cheese": "Iberian cheese culture from Manchego plains to Serra da Estrela highlands.",
    "Greek & Mediterranean Cheese": "Feta, Halloumi, and the sun-drenched dairy traditions of the Mediterranean basin.",
    "American Artisan Cheese": "The craft cheese revolution across Vermont, Wisconsin, California, and beyond.",
    "Ancient Cheese History": "Archaeological cheese finds from Neolithic pots to Roman recipes and Mongol aaruul.",
    "Cheese Museums & Festivals": "Cheese rolling, market days, museums, and dairy festivals around the globe.",
}

# ═══════════════════════════════════════════
# PRESET DATA PER MODE
# ═══════════════════════════════════════════

FRENCH_AOC = [
    {"name": "Roquefort-sur-Soulzon", "lat": 43.9783, "lon": 2.9811,
     "desc": "Home of Roquefort, the King of Cheeses, aged in natural Combalou caves since antiquity.",
     "country": "France", "cheese": "Roquefort", "milk": "Sheep", "color": "#06b6d4"},
    {"name": "Camembert, Normandy", "lat": 48.8789, "lon": 0.1692,
     "desc": "Birthplace of Camembert, created by Marie Harel in 1791 in this tiny Norman village.",
     "country": "France", "cheese": "Camembert de Normandie", "milk": "Cow", "color": "#f59e0b"},
    {"name": "Meaux, Ile-de-France", "lat": 48.9604, "lon": 2.8788,
     "desc": "Center of Brie de Meaux production, the 'Queen of Cheeses' since Charlemagne.",
     "country": "France", "cheese": "Brie de Meaux", "milk": "Cow", "color": "#8b5cf6"},
    {"name": "Poligny, Jura", "lat": 46.8367, "lon": 5.7086,
     "desc": "Capital of Comte cheese in the Jura mountains, with 160+ fruitieres.",
     "country": "France", "cheese": "Comte", "milk": "Cow", "color": "#10b981"},
    {"name": "Thones, Haute-Savoie", "lat": 45.8800, "lon": 6.3247,
     "desc": "Alpine village at the heart of Reblochon production in the Aravis mountains.",
     "country": "France", "cheese": "Reblochon", "milk": "Cow", "color": "#ec4899"},
    {"name": "Munster, Alsace", "lat": 48.0400, "lon": 7.1372,
     "desc": "Vosgian town giving its name to the pungent washed-rind Munster cheese.",
     "country": "France", "cheese": "Munster", "milk": "Cow", "color": "#ef4444"},
    {"name": "Beaufort, Savoie", "lat": 45.7167, "lon": 6.5736,
     "desc": "Alpine pastures producing the 'Prince of Gruyeres' since the Roman era.",
     "country": "France", "cheese": "Beaufort", "milk": "Cow", "color": "#f97316"},
    {"name": "Saint-Nectaire, Auvergne", "lat": 45.5833, "lon": 2.9333,
     "desc": "Volcanic terroir of the Auvergne producing this creamy semi-soft cheese.",
     "country": "France", "cheese": "Saint-Nectaire", "milk": "Cow", "color": "#a855f7"},
    {"name": "Epoisses, Burgundy", "lat": 47.5072, "lon": 4.1728,
     "desc": "Village producing the notoriously pungent Epoisses, washed in Marc de Bourgogne.",
     "country": "France", "cheese": "Epoisses", "milk": "Cow", "color": "#d946ef"},
    {"name": "Maroilles, Nord", "lat": 50.0833, "lon": 3.7500,
     "desc": "Named after the abbey where monks created this strong washed-rind cheese in 962 AD.",
     "country": "France", "cheese": "Maroilles", "milk": "Cow", "color": "#14b8a6"},
    {"name": "Cantal, Auvergne", "lat": 45.0297, "lon": 2.6808,
     "desc": "One of France's oldest cheeses, produced in the volcanic Cantal mountains for 2000 years.",
     "country": "France", "cheese": "Cantal", "milk": "Cow", "color": "#fbbf24"},
    {"name": "Rocamadour, Lot", "lat": 44.7994, "lon": 1.6186,
     "desc": "Tiny goat cheese from the pilgrimage town perched on limestone cliffs.",
     "country": "France", "cheese": "Rocamadour", "milk": "Goat", "color": "#38bdf8"},
    {"name": "Ossau-Iraty, Pyrenees", "lat": 43.0633, "lon": -0.6150,
     "desc": "Ancient Basque-Bearnaise sheep cheese from the western Pyrenees.",
     "country": "France", "cheese": "Ossau-Iraty", "milk": "Sheep", "color": "#fb923c"},
    {"name": "Langres, Champagne", "lat": 47.8625, "lon": 5.3333,
     "desc": "Concave-topped washed rind cheese traditionally filled with Champagne.",
     "country": "France", "cheese": "Langres", "milk": "Cow", "color": "#c084fc"},
    {"name": "Livarot, Normandy", "lat": 49.0000, "lon": 0.1500,
     "desc": "Called 'The Colonel' for its five raffia bands, one of Normandy's oldest cheeses.",
     "country": "France", "cheese": "Livarot", "milk": "Cow", "color": "#4ade80"},
    {"name": "Pont-l'Eveque, Normandy", "lat": 49.2833, "lon": 0.1833,
     "desc": "Possibly France's oldest cheese, documented since the 12th century.",
     "country": "France", "cheese": "Pont-l'Eveque", "milk": "Cow", "color": "#22d3ee"},
    {"name": "Valencay, Berry", "lat": 47.1567, "lon": 1.5667,
     "desc": "Pyramid-shaped goat cheese from the Loire Valley, legend says truncated by Napoleon.",
     "country": "France", "cheese": "Valencay", "milk": "Goat", "color": "#e879f9"},
    {"name": "Salers, Cantal", "lat": 45.1372, "lon": 2.4939,
     "desc": "Made only in summer from raw Salers cow milk on high volcanic pastures.",
     "country": "France", "cheese": "Salers", "milk": "Cow", "color": "#34d399"},
    {"name": "Morbier, Jura", "lat": 46.5333, "lon": 6.0167,
     "desc": "Distinctive ash line cheese created by Jura farmers using morning and evening milk.",
     "country": "France", "cheese": "Morbier", "milk": "Cow", "color": "#818cf8"},
    {"name": "Fourme d'Ambert, Auvergne", "lat": 45.5497, "lon": 3.7414,
     "desc": "One of France's oldest blue cheeses, milder and creamier than Roquefort.",
     "country": "France", "cheese": "Fourme d'Ambert", "milk": "Cow", "color": "#f472b6"},
    {"name": "Bleu d'Auvergne, Auvergne", "lat": 45.2833, "lon": 3.0833,
     "desc": "Created in the 1850s by Antoine Roussel using bread mold techniques.",
     "country": "France", "cheese": "Bleu d'Auvergne", "milk": "Cow", "color": "#2dd4bf"},
    {"name": "Chaource, Champagne", "lat": 48.0583, "lon": 4.1333,
     "desc": "Double-cream cheese from the village on the Champagne-Burgundy border.",
     "country": "France", "cheese": "Chaource", "milk": "Cow", "color": "#facc15"},
    {"name": "Selles-sur-Cher, Loire", "lat": 47.2764, "lon": 1.5528,
     "desc": "Ash-coated goat cheese from the chalky soils of the Loire Valley.",
     "country": "France", "cheese": "Selles-sur-Cher", "milk": "Goat", "color": "#fb7185"},
    {"name": "Picodon, Drome-Ardeche", "lat": 44.5000, "lon": 4.7500,
     "desc": "Small peppery goat cheese from the rocky Ardeche and Drome hillsides.",
     "country": "France", "cheese": "Picodon", "milk": "Goat", "color": "#a78bfa"},
    {"name": "Banon, Provence", "lat": 44.0333, "lon": 5.6333,
     "desc": "Goat cheese wrapped in chestnut leaves and tied with raffia, a Provencal tradition.",
     "country": "France", "cheese": "Banon", "milk": "Goat", "color": "#60a5fa"},
    {"name": "Abondance, Haute-Savoie", "lat": 46.2833, "lon": 6.7167,
     "desc": "Semi-hard alpine cheese from the Chablais valley, served at medieval papal conclaves.",
     "country": "France", "cheese": "Abondance", "milk": "Cow", "color": "#c4b5fd"},
]

ITALIAN_DOP = [
    {"name": "Parma, Emilia-Romagna", "lat": 44.8015, "lon": 10.3279,
     "desc": "Home of Parmigiano-Reggiano, the 'King of Italian Cheeses', aged 12-36 months.",
     "country": "Italy", "cheese": "Parmigiano-Reggiano", "milk": "Cow", "color": "#f59e0b"},
    {"name": "Caserta, Campania", "lat": 41.0742, "lon": 14.3328,
     "desc": "Heart of Mozzarella di Bufala Campana DOP production from water buffalo milk.",
     "country": "Italy", "cheese": "Mozzarella di Bufala", "milk": "Buffalo", "color": "#06b6d4"},
    {"name": "Novara, Piedmont", "lat": 45.4500, "lon": 8.6200,
     "desc": "Gorgonzola originated here in the 9th century, now Italy's premier blue cheese.",
     "country": "Italy", "cheese": "Gorgonzola", "milk": "Cow", "color": "#8b5cf6"},
    {"name": "Pienza, Tuscany", "lat": 43.0763, "lon": 11.6789,
     "desc": "Capital of Pecorino Toscano, made from sheep grazing on Val d'Orcia pastures.",
     "country": "Italy", "cheese": "Pecorino Toscano", "milk": "Sheep", "color": "#10b981"},
    {"name": "Bergamo, Lombardy", "lat": 45.6983, "lon": 9.6773,
     "desc": "Center of Taleggio production, a washed-rind cheese named after Val Taleggio.",
     "country": "Italy", "cheese": "Taleggio", "milk": "Cow", "color": "#ef4444"},
    {"name": "Asiago, Veneto", "lat": 45.8758, "lon": 11.5100,
     "desc": "High plateau town producing Asiago d'Allevo and Asiago Pressato since the year 1000.",
     "country": "Italy", "cheese": "Asiago", "milk": "Cow", "color": "#ec4899"},
    {"name": "Cremona, Lombardy", "lat": 45.1333, "lon": 10.0167,
     "desc": "Provolone Valpadana territory, where this pasta filata cheese is shaped and aged.",
     "country": "Italy", "cheese": "Provolone Valpadana", "milk": "Cow", "color": "#f97316"},
    {"name": "Locana, Piedmont", "lat": 45.0281, "lon": 7.4214,
     "desc": "Alpine pastures of the Orco Valley where Toma Piemontese has been made for centuries.",
     "country": "Italy", "cheese": "Toma Piemontese", "milk": "Cow", "color": "#a855f7"},
    {"name": "Fonni, Sardinia", "lat": 40.1208, "lon": 9.2500,
     "desc": "Heart of Pecorino Sardo production on the Gennargentu highlands of Sardinia.",
     "country": "Italy", "cheese": "Pecorino Sardo", "milk": "Sheep", "color": "#14b8a6"},
    {"name": "Ragusa, Sicily", "lat": 36.9269, "lon": 14.7253,
     "desc": "Home of Ragusano DOP, a rectangular stretched-curd cheese from Iblea plateau.",
     "country": "Italy", "cheese": "Ragusano", "milk": "Cow", "color": "#d946ef"},
    {"name": "Castelmagno, Piedmont", "lat": 44.3833, "lon": 7.1833,
     "desc": "Rare blue-veined cheese from a tiny alpine village, once used to pay rent to lords.",
     "country": "Italy", "cheese": "Castelmagno", "milk": "Cow", "color": "#38bdf8"},
    {"name": "Norcia, Umbria", "lat": 42.7933, "lon": 13.0922,
     "desc": "Pecorino di Norcia from the Sibillini mountains, flavored with black truffle.",
     "country": "Italy", "cheese": "Pecorino di Norcia", "milk": "Sheep", "color": "#fbbf24"},
    {"name": "Bra, Piedmont", "lat": 44.6986, "lon": 7.8533,
     "desc": "Namesake of Bra DOP cheese and host city of Slow Food's Cheese biennial festival.",
     "country": "Italy", "cheese": "Bra", "milk": "Cow", "color": "#fb923c"},
    {"name": "Matera, Basilicata", "lat": 40.6664, "lon": 16.6043,
     "desc": "Canestrato di Moliterno, aged in caves of Basilicata's ancient Sassi district.",
     "country": "Italy", "cheese": "Canestrato di Moliterno", "milk": "Sheep/Goat", "color": "#c084fc"},
    {"name": "Piave Valley, Veneto", "lat": 46.0833, "lon": 12.0833,
     "desc": "Piave DOP cheese from the Dolomite foothills, aged from 2 to over 18 months.",
     "country": "Italy", "cheese": "Piave", "milk": "Cow", "color": "#4ade80"},
    {"name": "Sondrio, Lombardy", "lat": 46.1699, "lon": 9.8789,
     "desc": "Bitto Storico from Valtellina, one of the world's longest-aged cheeses (10+ years).",
     "country": "Italy", "cheese": "Bitto", "milk": "Cow/Goat", "color": "#22d3ee"},
    {"name": "Aosta, Valle d'Aosta", "lat": 45.7370, "lon": 7.3150,
     "desc": "Fontina DOP from the Alps, essential for fonduta and beloved since the 12th century.",
     "country": "Italy", "cheese": "Fontina", "milk": "Cow", "color": "#e879f9"},
    {"name": "Modena, Emilia-Romagna", "lat": 44.6471, "lon": 10.9252,
     "desc": "Part of the Parmigiano-Reggiano zone, also home to traditional balsamic vinegar.",
     "country": "Italy", "cheese": "Parmigiano-Reggiano (Modena)", "milk": "Cow", "color": "#34d399"},
    {"name": "Grotta di Castelcivita, Campania", "lat": 40.4911, "lon": 15.2283,
     "desc": "Cave-aged Caciocavallo Silano DOP, a gourd-shaped stretched-curd southern cheese.",
     "country": "Italy", "cheese": "Caciocavallo Silano", "milk": "Cow", "color": "#818cf8"},
    {"name": "Valsesia, Piedmont", "lat": 45.8000, "lon": 8.2000,
     "desc": "Mountain pastures producing Maccagno, a rare alpine cheese from Biella province.",
     "country": "Italy", "cheese": "Maccagno", "milk": "Cow", "color": "#f472b6"},
    {"name": "Montasio, Friuli", "lat": 46.3900, "lon": 13.4300,
     "desc": "Montasio DOP from the Julian Alps, used in the famous frico dish of Friuli.",
     "country": "Italy", "cheese": "Montasio", "milk": "Cow", "color": "#2dd4bf"},
    {"name": "Crotone, Calabria", "lat": 39.0839, "lon": 17.1278,
     "desc": "Pecorino Crotonese from southern Calabria, a staple of the ancient Greek colony.",
     "country": "Italy", "cheese": "Pecorino Crotonese", "milk": "Sheep", "color": "#facc15"},
    {"name": "Cortina d'Ampezzo, Veneto", "lat": 46.5369, "lon": 12.1358,
     "desc": "Schiz cheese from the Dolomites, traditionally cooked on a hot plate with butter.",
     "country": "Italy", "cheese": "Schiz", "milk": "Cow", "color": "#fb7185"},
    {"name": "Nebrodi Mountains, Sicily", "lat": 37.9333, "lon": 14.7667,
     "desc": "Provola dei Nebrodi, a rare smoked stretched-curd cheese from wild highland pastures.",
     "country": "Italy", "cheese": "Provola dei Nebrodi", "milk": "Cow", "color": "#a78bfa"},
    {"name": "Agerola, Campania", "lat": 40.6333, "lon": 14.5333,
     "desc": "Fior di Latte from the Lattari Mountains, the cow-milk cousin of buffalo mozzarella.",
     "country": "Italy", "cheese": "Fior di Latte", "milk": "Cow", "color": "#60a5fa"},
    {"name": "Nuoro, Sardinia", "lat": 40.3210, "lon": 9.3300,
     "desc": "Fiore Sardo DOP, a smoked Sardinian pecorino made by shepherd families since antiquity.",
     "country": "Italy", "cheese": "Fiore Sardo", "milk": "Sheep", "color": "#c4b5fd"},
]

SWISS_CHEESE = [
    {"name": "Emmental, Bern", "lat": 46.9500, "lon": 7.7333,
     "desc": "The Emme valley where the iconic 'Swiss cheese' with large holes has been made since 1293.",
     "country": "Switzerland", "cheese": "Emmentaler AOC", "milk": "Cow", "color": "#f59e0b"},
    {"name": "Gruyeres, Fribourg", "lat": 46.5833, "lon": 7.0833,
     "desc": "Medieval walled town and birthplace of Gruyere AOP, Switzerland's most popular cheese.",
     "country": "Switzerland", "cheese": "Gruyere AOP", "milk": "Cow", "color": "#06b6d4"},
    {"name": "Appenzell, AI", "lat": 47.3333, "lon": 9.4167,
     "desc": "Home of Appenzeller, whose herbal brine recipe is a closely guarded secret since 700 years.",
     "country": "Switzerland", "cheese": "Appenzeller", "milk": "Cow", "color": "#8b5cf6"},
    {"name": "Valais Region", "lat": 46.2333, "lon": 7.3667,
     "desc": "Raclette du Valais AOP, traditionally melted by the fire and scraped onto plates.",
     "country": "Switzerland", "cheese": "Raclette du Valais", "milk": "Cow", "color": "#ef4444"},
    {"name": "Bellelay, Jura bernois", "lat": 47.2667, "lon": 7.1667,
     "desc": "Tete de Moine AOP, invented by monks at Bellelay Abbey, served as rosettes with a girolle.",
     "country": "Switzerland", "cheese": "Tete de Moine", "milk": "Cow", "color": "#ec4899"},
    {"name": "Tilsit, Thurgau", "lat": 47.5500, "lon": 9.1000,
     "desc": "Swiss Tilsiter, adapted from the East Prussian original by Swiss cheesemakers.",
     "country": "Switzerland", "cheese": "Tilsiter", "milk": "Cow", "color": "#10b981"},
    {"name": "Urnaesch, Appenzell", "lat": 47.3167, "lon": 9.2833,
     "desc": "Alpine dairy producing traditional Appenzeller in copper vats over wood fire.",
     "country": "Switzerland", "cheese": "Appenzeller Alpkaese", "milk": "Cow", "color": "#f97316"},
    {"name": "Etivaz, Vaud", "lat": 46.3500, "lon": 7.1500,
     "desc": "L'Etivaz AOP, made only in summer chalets over wood fires in the Pays-d'Enhaut.",
     "country": "Switzerland", "cheese": "L'Etivaz", "milk": "Cow", "color": "#a855f7"},
    {"name": "Sbrinz, Obwalden", "lat": 46.8833, "lon": 8.2500,
     "desc": "Sbrinz AOP, one of Europe's oldest hard cheeses, possibly the ancestor of Parmesan.",
     "country": "Switzerland", "cheese": "Sbrinz", "milk": "Cow", "color": "#14b8a6"},
    {"name": "Vacherin Mont-d'Or, Vaud", "lat": 46.7167, "lon": 6.3667,
     "desc": "Seasonal spruce-bark wrapped cheese made only from October to March.",
     "country": "Switzerland", "cheese": "Vacherin Mont-d'Or", "milk": "Cow", "color": "#d946ef"},
    {"name": "Schabziger, Glarus", "lat": 47.0500, "lon": 9.0667,
     "desc": "The green cone-shaped cheese flavored with blue fenugreek, made since the 15th century.",
     "country": "Switzerland", "cheese": "Schabziger (Sap Sago)", "milk": "Cow", "color": "#38bdf8"},
    {"name": "Brig, Valais", "lat": 46.3167, "lon": 7.9833,
     "desc": "Simplon and Gomser cheese from the upper Valais alpine pastures.",
     "country": "Switzerland", "cheese": "Gomser", "milk": "Cow", "color": "#fbbf24"},
    {"name": "Chateau-d'Oex, Vaud", "lat": 46.4833, "lon": 7.1333,
     "desc": "Alpine cheese village in the Pays-d'Enhaut, center of summer alpage cheesemaking.",
     "country": "Switzerland", "cheese": "Alpage Gruyere", "milk": "Cow", "color": "#fb923c"},
    {"name": "Engelberg, Obwalden", "lat": 46.8200, "lon": 8.4000,
     "desc": "Benedictine monastery producing cheese since the 12th century in central Switzerland.",
     "country": "Switzerland", "cheese": "Engelberger Klosterkase", "milk": "Cow", "color": "#c084fc"},
    {"name": "Saanen, Bern", "lat": 46.4833, "lon": 7.2500,
     "desc": "High-altitude pastures producing Saanen Hobelkaese, a hard cheese shaved into curls.",
     "country": "Switzerland", "cheese": "Hobelkaese", "milk": "Cow", "color": "#4ade80"},
    {"name": "Ticino Region", "lat": 46.2000, "lon": 8.9500,
     "desc": "Formaggini Ticinesi, small fresh goat cheeses from the Italian-speaking canton.",
     "country": "Switzerland", "cheese": "Formaggini", "milk": "Goat", "color": "#22d3ee"},
    {"name": "Jura Region, Neuchatel", "lat": 47.0000, "lon": 6.9500,
     "desc": "Gruyere and Tete de Moine production in the rolling Jura hills and valleys.",
     "country": "Switzerland", "cheese": "Jura Gruyere", "milk": "Cow", "color": "#e879f9"},
    {"name": "Alpstein, AI", "lat": 47.2833, "lon": 9.4000,
     "desc": "Summer alpage cheeses from one of Switzerland's most dramatic mountain settings.",
     "country": "Switzerland", "cheese": "Alpstein Bergkaese", "milk": "Cow", "color": "#34d399"},
    {"name": "Fribourg City", "lat": 46.8065, "lon": 7.1620,
     "desc": "Capital of the canton synonymous with Vacherin Fribourgeois, essential for fondue moitie-moitie.",
     "country": "Switzerland", "cheese": "Vacherin Fribourgeois", "milk": "Cow", "color": "#818cf8"},
    {"name": "Justistal, Bern", "lat": 46.7333, "lon": 7.7500,
     "desc": "Annual Chasteilet cheese-sharing festival in the Justis valley above Lake Thun.",
     "country": "Switzerland", "cheese": "Justistal Alpkaese", "milk": "Cow", "color": "#f472b6"},
    {"name": "Schwyz, Schwyz", "lat": 47.0167, "lon": 8.6500,
     "desc": "Traditional hard cheese production in the founding canton of Switzerland.",
     "country": "Switzerland", "cheese": "Schwyzer Milchsuppe Kaese", "milk": "Cow", "color": "#2dd4bf"},
    {"name": "Luzern Region", "lat": 47.0500, "lon": 8.3000,
     "desc": "Central Switzerland's dairy heartland with numerous small artisan fromageries.",
     "country": "Switzerland", "cheese": "Luzerner Rahmkaese", "milk": "Cow", "color": "#facc15"},
    {"name": "Zweisimmen, Bern", "lat": 46.5500, "lon": 7.3833,
     "desc": "Simmental valley cheese from the famous dairy cattle breed region.",
     "country": "Switzerland", "cheese": "Simmentaler Kaese", "milk": "Cow", "color": "#fb7185"},
    {"name": "Davos, Graubunden", "lat": 46.8027, "lon": 9.8360,
     "desc": "Alpine cheese dairies in the highest town in Europe, serving skiers and hikers.",
     "country": "Switzerland", "cheese": "Davoser Bergkaese", "milk": "Cow", "color": "#a78bfa"},
    {"name": "Adelboden, Bern", "lat": 46.4917, "lon": 7.5583,
     "desc": "Traditional Bernese Oberland cheesemaking with summer alpage tradition.",
     "country": "Switzerland", "cheese": "Adelbodner Alpkaese", "milk": "Cow", "color": "#60a5fa"},
]

BRITISH_CHEESE = [
    {"name": "Cheddar Gorge, Somerset", "lat": 51.2833, "lon": -2.7667,
     "desc": "The limestone caves of Cheddar Gorge where the world's most popular cheese was first aged.",
     "country": "United Kingdom", "cheese": "Cheddar", "milk": "Cow", "color": "#f59e0b"},
    {"name": "Stilton, Cambridgeshire", "lat": 52.4833, "lon": -0.4833,
     "desc": "The village that gave its name to England's 'King of Cheeses', a protected blue cheese.",
     "country": "United Kingdom", "cheese": "Stilton", "milk": "Cow", "color": "#8b5cf6"},
    {"name": "Melton Mowbray, Leicestershire", "lat": 52.7631, "lon": -0.8864,
     "desc": "Home of Red Leicester cheese and Stilton production since the 18th century.",
     "country": "United Kingdom", "cheese": "Red Leicester", "milk": "Cow", "color": "#ef4444"},
    {"name": "Hawes, Wensleydale", "lat": 54.3033, "lon": -2.1947,
     "desc": "Wensleydale Creamery in the Yorkshire Dales, producing crumbly cheese since 1150 AD.",
     "country": "United Kingdom", "cheese": "Wensleydale", "milk": "Cow", "color": "#06b6d4"},
    {"name": "Lynher Dairies, Cornwall", "lat": 50.4167, "lon": -4.8667,
     "desc": "Cornish Yarg wrapped in nettle leaves, a modern classic revived from a historical recipe.",
     "country": "United Kingdom", "cheese": "Cornish Yarg", "milk": "Cow", "color": "#10b981"},
    {"name": "Colston Bassett, Nottinghamshire", "lat": 52.8667, "lon": -1.0000,
     "desc": "Colston Bassett Stilton, handmade with traditional methods since 1913.",
     "country": "United Kingdom", "cheese": "Colston Bassett Stilton", "milk": "Cow", "color": "#ec4899"},
    {"name": "Appleby, Cumbria", "lat": 54.5833, "lon": -2.4833,
     "desc": "Appleby's Cheshire, one of Britain's oldest cheeses, crumbly and tangy.",
     "country": "United Kingdom", "cheese": "Cheshire", "milk": "Cow", "color": "#f97316"},
    {"name": "Stinking Bishop, Gloucestershire", "lat": 51.8167, "lon": -2.4500,
     "desc": "Charles Martell's famous pungent washed-rind cheese named after a local pear variety.",
     "country": "United Kingdom", "cheese": "Stinking Bishop", "milk": "Cow", "color": "#a855f7"},
    {"name": "Sparkenhoe, Leicestershire", "lat": 52.5667, "lon": -1.3833,
     "desc": "The only traditional raw-milk Red Leicester, revived on the historic Sparkenhoe farm.",
     "country": "United Kingdom", "cheese": "Sparkenhoe Red Leicester", "milk": "Cow", "color": "#d946ef"},
    {"name": "Stichelton Dairy, Nottinghamshire", "lat": 53.0833, "lon": -1.0000,
     "desc": "Raw-milk 'Stilton-style' blue cheese, using traditional rennet and methods.",
     "country": "United Kingdom", "cheese": "Stichelton", "milk": "Cow", "color": "#14b8a6"},
    {"name": "Montgomery, Somerset", "lat": 51.0167, "lon": -2.7667,
     "desc": "Montgomery's Cheddar, widely regarded as the finest traditional clothbound Cheddar.",
     "country": "United Kingdom", "cheese": "Montgomery's Cheddar", "milk": "Cow", "color": "#fbbf24"},
    {"name": "Caerphilly, Wales", "lat": 51.5731, "lon": -3.2186,
     "desc": "Welsh mining town cheese, a moist crumbly variety originally made for coal miners.",
     "country": "United Kingdom", "cheese": "Caerphilly", "milk": "Cow", "color": "#38bdf8"},
    {"name": "Lanark, Scotland", "lat": 55.6744, "lon": -3.7778,
     "desc": "Lanark Blue, Scotland's answer to Roquefort, made from Lacaune sheep milk.",
     "country": "United Kingdom", "cheese": "Lanark Blue", "milk": "Sheep", "color": "#fb923c"},
    {"name": "Isle of Mull, Scotland", "lat": 56.4500, "lon": -5.9167,
     "desc": "Isle of Mull Cheddar, made with raw milk from Tobermory-fed cows on the island.",
     "country": "United Kingdom", "cheese": "Isle of Mull Cheddar", "milk": "Cow", "color": "#c084fc"},
    {"name": "Dorstone, Herefordshire", "lat": 52.0333, "lon": -3.0500,
     "desc": "Neal's Yard's Dorstone, an award-winning ash-coated goat cheese.",
     "country": "United Kingdom", "cheese": "Dorstone", "milk": "Goat", "color": "#4ade80"},
    {"name": "Sharpham, Devon", "lat": 50.4167, "lon": -3.6333,
     "desc": "Sharpham Brie, made with Jersey cow milk on a Dart Valley vineyard estate.",
     "country": "United Kingdom", "cheese": "Sharpham Brie", "milk": "Cow", "color": "#22d3ee"},
    {"name": "Berwick Edge, Northumberland", "lat": 55.7667, "lon": -2.0000,
     "desc": "Northumberland cheese, a semi-hard cheese from the English-Scottish border country.",
     "country": "United Kingdom", "cheese": "Northumberland", "milk": "Cow", "color": "#e879f9"},
    {"name": "Wigmore, Berkshire", "lat": 51.4500, "lon": -1.4000,
     "desc": "Village Maid Cheese's Wigmore, a washed-curd sheep cheese from the Thames Valley.",
     "country": "United Kingdom", "cheese": "Wigmore", "milk": "Sheep", "color": "#34d399"},
    {"name": "Tunworth, Hampshire", "lat": 51.2333, "lon": -1.1667,
     "desc": "Tunworth, an award-winning English Camembert-style cheese from Hampshire Cheeses.",
     "country": "United Kingdom", "cheese": "Tunworth", "milk": "Cow", "color": "#818cf8"},
    {"name": "Baron Bigod, Suffolk", "lat": 52.4333, "lon": 1.5167,
     "desc": "England's only raw-milk Brie-style farmstead cheese from Fen Farm Dairy.",
     "country": "United Kingdom", "cheese": "Baron Bigod", "milk": "Cow", "color": "#f472b6"},
    {"name": "Kirkham, Lancashire", "lat": 53.7833, "lon": -2.8667,
     "desc": "Mrs Kirkham's Lancashire, a buttery crumbly cheese made by the same family since 1978.",
     "country": "United Kingdom", "cheese": "Kirkham's Lancashire", "milk": "Cow", "color": "#2dd4bf"},
    {"name": "Gorwydd, Carmarthenshire", "lat": 51.8500, "lon": -4.3000,
     "desc": "Gorwydd Caerphilly, a traditionally made Welsh cave-aged territorial cheese.",
     "country": "United Kingdom", "cheese": "Gorwydd Caerphilly", "milk": "Cow", "color": "#facc15"},
    {"name": "Cropwell Bishop, Nottinghamshire", "lat": 52.9500, "lon": -1.0167,
     "desc": "Cropwell Bishop Stilton, hand-ladled and traditionally aged in the cheese cellars.",
     "country": "United Kingdom", "cheese": "Cropwell Bishop Stilton", "milk": "Cow", "color": "#fb7185"},
    {"name": "Quicke's, Devon", "lat": 50.7667, "lon": -3.5167,
     "desc": "Quicke's clothbound Cheddar, made on the same Devon farm for over 450 years.",
     "country": "United Kingdom", "cheese": "Quicke's Cheddar", "milk": "Cow", "color": "#a78bfa"},
    {"name": "Orkney, Scotland", "lat": 58.9667, "lon": -3.0000,
     "desc": "Orkney Cheddar and Grimbister Farm Cheese from the windswept northern isles.",
     "country": "United Kingdom", "cheese": "Orkney Cheddar", "milk": "Cow", "color": "#60a5fa"},
    {"name": "Anster, Fife", "lat": 56.2167, "lon": -2.7000,
     "desc": "Anster cheese from St Andrews Farmstead, Scotland's first registered farmhouse cheese.",
     "country": "United Kingdom", "cheese": "Anster", "milk": "Cow", "color": "#c4b5fd"},
]

DUTCH_BELGIAN = [
    {"name": "Gouda, South Holland", "lat": 52.0115, "lon": 4.7104,
     "desc": "Historic cheese market town since 1395; Gouda accounts for 50-60% of world Dutch cheese.",
     "country": "Netherlands", "cheese": "Gouda", "milk": "Cow", "color": "#f59e0b"},
    {"name": "Edam, North Holland", "lat": 52.5133, "lon": 5.0467,
     "desc": "Edam cheese in its iconic red wax coating, exported worldwide since the 14th century.",
     "country": "Netherlands", "cheese": "Edam", "milk": "Cow", "color": "#ef4444"},
    {"name": "Alkmaar, North Holland", "lat": 52.6324, "lon": 4.7534,
     "desc": "Famous Friday cheese market dating to 1593, a living tradition with cheese carriers.",
     "country": "Netherlands", "cheese": "Alkmaar Market Cheese", "milk": "Cow", "color": "#06b6d4"},
    {"name": "Limburg, Netherlands", "lat": 50.8514, "lon": 5.6910,
     "desc": "Birthplace of Limburger, the notoriously pungent washed-rind cheese.",
     "country": "Netherlands", "cheese": "Limburger", "milk": "Cow", "color": "#8b5cf6"},
    {"name": "Leiden, South Holland", "lat": 52.1601, "lon": 4.4970,
     "desc": "Leidse Kaas, cumin-spiced cheese pressed with the city's coat of arms.",
     "country": "Netherlands", "cheese": "Leiden (Leidse Kaas)", "milk": "Cow", "color": "#10b981"},
    {"name": "Texel Island, North Holland", "lat": 53.0667, "lon": 4.8000,
     "desc": "Texelse Schapenkaas, sheep cheese from the salt-marsh meadows of Texel island.",
     "country": "Netherlands", "cheese": "Texel Sheep Cheese", "milk": "Sheep", "color": "#ec4899"},
    {"name": "Beemster Polder, North Holland", "lat": 52.5500, "lon": 4.9167,
     "desc": "Beemster cheese from the UNESCO-listed polder, known for extra-aged Gouda.",
     "country": "Netherlands", "cheese": "Beemster", "milk": "Cow", "color": "#f97316"},
    {"name": "Maasdam, South Holland", "lat": 51.7833, "lon": 4.5500,
     "desc": "Maasdam cheese, the Dutch 'Swiss-style' cheese with large sweet holes.",
     "country": "Netherlands", "cheese": "Maasdam", "milk": "Cow", "color": "#a855f7"},
    {"name": "Woerden, South Holland", "lat": 52.0833, "lon": 4.8833,
     "desc": "Last authentic cheese market in the Netherlands, held on Saturday mornings.",
     "country": "Netherlands", "cheese": "Boerenkaas (Farmhouse)", "milk": "Cow", "color": "#14b8a6"},
    {"name": "Friesland Region", "lat": 53.1500, "lon": 5.8000,
     "desc": "Friese Nagelkaas, clove-and-cumin spiced cheese from the Frisian dairy region.",
     "country": "Netherlands", "cheese": "Friese Nagelkaas", "milk": "Cow", "color": "#d946ef"},
    {"name": "Chimay, Hainaut", "lat": 50.0500, "lon": 4.3167,
     "desc": "Chimay Trappist cheese, made by monks alongside the famous Chimay beer.",
     "country": "Belgium", "cheese": "Chimay", "milk": "Cow", "color": "#38bdf8"},
    {"name": "Herve, Liege", "lat": 50.6400, "lon": 5.7936,
     "desc": "Herve AOP, Belgium's only AOP cheese, a pungent washed-rind from the Pays de Herve.",
     "country": "Belgium", "cheese": "Herve", "milk": "Cow", "color": "#fbbf24"},
    {"name": "Orval, Luxembourg Province", "lat": 49.6375, "lon": 5.3469,
     "desc": "Orval monastery cheese, another Trappist cheese tradition from the Gaume region.",
     "country": "Belgium", "cheese": "Orval", "milk": "Cow", "color": "#fb923c"},
    {"name": "Passendale, West Flanders", "lat": 50.9000, "lon": 2.9833,
     "desc": "Passendale cheese, a semi-soft bread-shaped cheese from the WWI memorial village.",
     "country": "Belgium", "cheese": "Passendale", "milk": "Cow", "color": "#c084fc"},
    {"name": "Bruges, West Flanders", "lat": 51.2093, "lon": 3.2247,
     "desc": "Brugge Blomme and Old Bruges cheeses, sold in the medieval cheese shops of the city.",
     "country": "Belgium", "cheese": "Brugge Blomme", "milk": "Cow", "color": "#4ade80"},
    {"name": "Maredsous Abbey, Namur", "lat": 50.2833, "lon": 4.7667,
     "desc": "Maredsous, a Benedictine monastery cheese, Belgium's best-known abbey cheese.",
     "country": "Belgium", "cheese": "Maredsous", "milk": "Cow", "color": "#22d3ee"},
    {"name": "Postel Abbey, Antwerp", "lat": 51.3167, "lon": 5.2167,
     "desc": "Postel Norbertine abbey cheese, a semi-hard washed-rind from the Kempen region.",
     "country": "Belgium", "cheese": "Postel", "milk": "Cow", "color": "#e879f9"},
    {"name": "Westmalle, Antwerp", "lat": 51.2833, "lon": 4.6667,
     "desc": "Trappist cheese from Westmalle Abbey, paired with their legendary dubbel and tripel.",
     "country": "Belgium", "cheese": "Westmalle", "milk": "Cow", "color": "#34d399"},
    {"name": "Rochefort, Namur", "lat": 50.1597, "lon": 5.2219,
     "desc": "Rochefort Trappist cheese, made in small batches at the Notre-Dame de Saint-Remy abbey.",
     "country": "Belgium", "cheese": "Rochefort", "milk": "Cow", "color": "#818cf8"},
    {"name": "Bouillon, Luxembourg Province", "lat": 49.7958, "lon": 5.0672,
     "desc": "Bouillon cheese, an artisan washed-rind from the forested Ardennes region.",
     "country": "Belgium", "cheese": "Bouillon", "milk": "Cow", "color": "#f472b6"},
    {"name": "Giethoorn, Overijssel", "lat": 52.7200, "lon": 6.0800,
     "desc": "Farmhouse Gouda from the 'Venice of the Netherlands', made in canal-side dairies.",
     "country": "Netherlands", "cheese": "Giethoorn Boerenkaas", "milk": "Cow", "color": "#2dd4bf"},
    {"name": "Zaandam, North Holland", "lat": 52.4400, "lon": 4.8267,
     "desc": "Windmill-powered cheese factories of the Zaan region, a historic cheese-making center.",
     "country": "Netherlands", "cheese": "Zaandam Gouda", "milk": "Cow", "color": "#facc15"},
    {"name": "Schoorl, North Holland", "lat": 52.7000, "lon": 4.6667,
     "desc": "Organic artisan cheese farms in the North Holland dune landscape.",
     "country": "Netherlands", "cheese": "Schoorl Bio Kaas", "milk": "Cow", "color": "#fb7185"},
    {"name": "Reypenaer, Amsterdam", "lat": 52.3676, "lon": 4.9041,
     "desc": "Reypenaer Cheese Tasting Room, showcasing aged Gouda in Amsterdam's historic center.",
     "country": "Netherlands", "cheese": "Reypenaer VSOP", "milk": "Cow", "color": "#a78bfa"},
    {"name": "Rotterdam, South Holland", "lat": 51.9225, "lon": 4.4792,
     "desc": "Fenix Food Factory and artisan cheese producers reviving farmstead traditions.",
     "country": "Netherlands", "cheese": "Rotterdam Artisan", "milk": "Cow", "color": "#60a5fa"},
]

SPANISH_PORTUGUESE = [
    {"name": "La Mancha, Castilla", "lat": 39.4000, "lon": -3.0000,
     "desc": "Manchego DOP, Spain's most famous cheese, from Manchega sheep on the central plateau.",
     "country": "Spain", "cheese": "Manchego", "milk": "Sheep", "color": "#f59e0b"},
    {"name": "Idiazabal, Basque Country", "lat": 42.9833, "lon": -2.2333,
     "desc": "Smoked Idiazabal DOP from Latxa sheep, a Basque pastoral tradition for millennia.",
     "country": "Spain", "cheese": "Idiazabal", "milk": "Sheep", "color": "#06b6d4"},
    {"name": "Serra da Estrela, Portugal", "lat": 40.3210, "lon": -7.6114,
     "desc": "Serra da Estrela DOP, Portugal's most prized cheese, curdled with thistle flower rennet.",
     "country": "Portugal", "cheese": "Serra da Estrela", "milk": "Sheep", "color": "#8b5cf6"},
    {"name": "Cabrales, Asturias", "lat": 43.3167, "lon": -4.8500,
     "desc": "Cabrales DOP, a powerful blue cheese aged in natural limestone caves of the Picos de Europa.",
     "country": "Spain", "cheese": "Cabrales", "milk": "Cow/Sheep/Goat", "color": "#ef4444"},
    {"name": "Mahon, Menorca", "lat": 39.8858, "lon": 4.2625,
     "desc": "Mahon-Menorca DOP, a pressed cheese with a distinctive orange rind from Balearic Islands.",
     "country": "Spain", "cheese": "Mahon-Menorca", "milk": "Cow", "color": "#ec4899"},
    {"name": "Roncal Valley, Navarra", "lat": 42.8000, "lon": -0.9333,
     "desc": "Roncal DOP, Spain's first DOP cheese, from Latxa and Rasa sheep of the Pyrenean valley.",
     "country": "Spain", "cheese": "Roncal", "milk": "Sheep", "color": "#10b981"},
    {"name": "Tetilla, Galicia", "lat": 42.8800, "lon": -8.5448,
     "desc": "Tetilla DOP, the breast-shaped cheese of Galicia, mild and creamy.",
     "country": "Spain", "cheese": "Tetilla", "milk": "Cow", "color": "#f97316"},
    {"name": "Azeitao, Setubal", "lat": 38.5228, "lon": -9.0119,
     "desc": "Queijo de Azeitao DOP, a small soft thistle-rennet cheese from the Arrabida hills.",
     "country": "Portugal", "cheese": "Azeitao", "milk": "Sheep", "color": "#a855f7"},
    {"name": "Sao Jorge, Azores", "lat": 38.6500, "lon": -28.0333,
     "desc": "Queijo Sao Jorge DOP, a Cheddar-like cheese brought to the Azores by Flemish settlers.",
     "country": "Portugal", "cheese": "Sao Jorge", "milk": "Cow", "color": "#14b8a6"},
    {"name": "Torta del Casar, Extremadura", "lat": 39.2667, "lon": -6.3833,
     "desc": "Torta del Casar DOP, a runny thistle-rennet cheese eaten by slicing the top open.",
     "country": "Spain", "cheese": "Torta del Casar", "milk": "Sheep", "color": "#d946ef"},
    {"name": "Picon Bejes-Tresviso, Cantabria", "lat": 43.2167, "lon": -4.6333,
     "desc": "Blue cheese wrapped in sycamore leaves, aged in Cantabrian mountain caves.",
     "country": "Spain", "cheese": "Picon Bejes-Tresviso", "milk": "Cow/Sheep/Goat", "color": "#38bdf8"},
    {"name": "Arzua-Ulloa, Galicia", "lat": 42.9333, "lon": -8.1667,
     "desc": "Arzua-Ulloa DOP, Galicia's most-produced cheese, creamy with a natural rind.",
     "country": "Spain", "cheese": "Arzua-Ulloa", "milk": "Cow", "color": "#fbbf24"},
    {"name": "Nisa, Alentejo", "lat": 39.5167, "lon": -7.6500,
     "desc": "Queijo de Nisa DOP, a semi-hard thistle-curdled cheese from the hot Alentejo plain.",
     "country": "Portugal", "cheese": "Nisa", "milk": "Sheep", "color": "#fb923c"},
    {"name": "Majorero, Fuerteventura", "lat": 28.3587, "lon": -14.0538,
     "desc": "Majorero DOP, goat cheese rubbed with oil, paprika, or gofio from the Canary Islands.",
     "country": "Spain", "cheese": "Majorero", "milk": "Goat", "color": "#c084fc"},
    {"name": "Zamorano, Castilla y Leon", "lat": 41.5033, "lon": -5.7455,
     "desc": "Zamorano DOP, a hard sheep cheese from the Churra and Castellana breeds of Zamora.",
     "country": "Spain", "cheese": "Zamorano", "milk": "Sheep", "color": "#4ade80"},
    {"name": "Palmero, La Palma", "lat": 28.7086, "lon": -17.8550,
     "desc": "Queso Palmero DOP, artisan smoked goat cheese from the volcanic island of La Palma.",
     "country": "Spain", "cheese": "Palmero", "milk": "Goat", "color": "#22d3ee"},
    {"name": "Castelo Branco, Portugal", "lat": 39.8222, "lon": -7.4917,
     "desc": "Queijo de Castelo Branco DOP, thistle-rennet cheese from the Beira Baixa region.",
     "country": "Portugal", "cheese": "Castelo Branco", "milk": "Sheep/Goat", "color": "#e879f9"},
    {"name": "Herrera del Duque, Extremadura", "lat": 38.9833, "lon": -5.0333,
     "desc": "La Serena DOP, a runny Merino sheep cheese from Extremadura's dehesa pastures.",
     "country": "Spain", "cheese": "La Serena", "milk": "Sheep", "color": "#34d399"},
    {"name": "Rabaçal, Coimbra", "lat": 39.9833, "lon": -8.4500,
     "desc": "Queijo Rabacal DOP, a small pressed cheese from the Serra de Sicó limestone hills.",
     "country": "Portugal", "cheese": "Rabacal", "milk": "Sheep/Goat", "color": "#818cf8"},
    {"name": "Gamoneu, Asturias", "lat": 43.2500, "lon": -5.0000,
     "desc": "Gamoneu DOP, a lightly smoked and naturally blued cheese from remote Picos de Europa.",
     "country": "Spain", "cheese": "Gamoneu", "milk": "Cow/Sheep/Goat", "color": "#f472b6"},
    {"name": "San Simon da Costa, Lugo", "lat": 43.3500, "lon": -7.6000,
     "desc": "San Simon da Costa DOP, a pear-shaped smoked cheese from Galician birch-wood fires.",
     "country": "Spain", "cheese": "San Simon da Costa", "milk": "Cow", "color": "#2dd4bf"},
    {"name": "Evora, Alentejo", "lat": 38.5714, "lon": -7.9094,
     "desc": "Queijo de Evora DOP, a small hard sheep cheese from the cork oak plains of Alentejo.",
     "country": "Portugal", "cheese": "Evora", "milk": "Sheep", "color": "#facc15"},
    {"name": "Flor de Guia, Gran Canaria", "lat": 28.1333, "lon": -15.6333,
     "desc": "Queso de Flor de Guia DOP, made with a mix of milks and thistle-flower rennet.",
     "country": "Spain", "cheese": "Flor de Guia", "milk": "Sheep/Cow", "color": "#fb7185"},
    {"name": "Cebreiro, Lugo", "lat": 42.7000, "lon": -7.0500,
     "desc": "Queso de Cebreiro, a mushroom-shaped fresh cheese from the Camino de Santiago route.",
     "country": "Spain", "cheese": "Cebreiro", "milk": "Cow", "color": "#a78bfa"},
    {"name": "Amanteigado, Beira Baixa", "lat": 40.0000, "lon": -7.3000,
     "desc": "Queijo Amanteigado, a butter-soft thistle-rennet cheese from central Portugal.",
     "country": "Portugal", "cheese": "Amanteigado", "milk": "Sheep", "color": "#60a5fa"},
]

GREEK_MEDITERRANEAN = [
    {"name": "Epirus, Greece", "lat": 39.6500, "lon": 20.8500,
     "desc": "Heartland of Feta PDO production, Greece's most famous cheese, brined in barrels.",
     "country": "Greece", "cheese": "Feta", "milk": "Sheep/Goat", "color": "#06b6d4"},
    {"name": "Larnaca, Cyprus", "lat": 34.9167, "lon": 33.6333,
     "desc": "Halloumi, the squeaky grilling cheese of Cyprus, made from sheep and goat milk.",
     "country": "Cyprus", "cheese": "Halloumi", "milk": "Sheep/Goat", "color": "#f59e0b"},
    {"name": "Plovdiv, Bulgaria", "lat": 42.1500, "lon": 24.7500,
     "desc": "Kashkaval Vitosha, the stretched-curd yellow cheese beloved across the Balkans.",
     "country": "Bulgaria", "cheese": "Kashkaval", "milk": "Sheep/Cow", "color": "#8b5cf6"},
    {"name": "Balikesir, Turkey", "lat": 39.6500, "lon": 27.8833,
     "desc": "Beyaz Peynir, Turkey's white brined cheese, a breakfast staple for centuries.",
     "country": "Turkey", "cheese": "Beyaz Peynir", "milk": "Sheep/Cow", "color": "#ef4444"},
    {"name": "Thessaly, Greece", "lat": 39.6000, "lon": 22.4167,
     "desc": "Major Feta production region with protected mountain pastures in central Greece.",
     "country": "Greece", "cheese": "Thessaly Feta", "milk": "Sheep/Goat", "color": "#ec4899"},
    {"name": "Metsovo, Epirus", "lat": 39.7700, "lon": 21.1833,
     "desc": "Metsovone, a smoked pasta-filata cheese from the Vlach mountain town of Metsovo.",
     "country": "Greece", "cheese": "Metsovone", "milk": "Cow", "color": "#10b981"},
    {"name": "Mytilene, Lesbos", "lat": 39.1000, "lon": 26.5500,
     "desc": "Ladotyri Mytilinis PDO, a hard cheese aged in olive oil on the island of Lesbos.",
     "country": "Greece", "cheese": "Ladotyri", "milk": "Sheep/Goat", "color": "#f97316"},
    {"name": "Arachova, Boeotia", "lat": 38.4792, "lon": 22.5883,
     "desc": "Formaella Arachovas PDO, a small hard cheese from the slopes of Mount Parnassus.",
     "country": "Greece", "cheese": "Formaella Arachovas", "milk": "Sheep/Goat", "color": "#a855f7"},
    {"name": "Naxos, Cyclades", "lat": 37.1000, "lon": 25.3833,
     "desc": "Graviera Naxou PDO, a sweet hard cheese from the largest Cycladic island.",
     "country": "Greece", "cheese": "Graviera Naxou", "milk": "Cow/Sheep", "color": "#14b8a6"},
    {"name": "Crete, Greece", "lat": 35.2400, "lon": 24.4700,
     "desc": "Graviera Kritis PDO, the most popular table cheese of Crete, nutty and sweet.",
     "country": "Greece", "cheese": "Graviera Kritis", "milk": "Sheep", "color": "#d946ef"},
    {"name": "Sfakia, Crete", "lat": 35.2000, "lon": 24.1333,
     "desc": "Sfakian pies filled with mizithra, a fresh whey cheese from the White Mountains.",
     "country": "Greece", "cheese": "Mizithra", "milk": "Sheep/Goat", "color": "#38bdf8"},
    {"name": "Kars, Turkey", "lat": 40.6167, "lon": 43.1000,
     "desc": "Kars Gravyer, a Swiss-influenced cheese brought by Caucasian settlers to eastern Turkey.",
     "country": "Turkey", "cheese": "Kars Gravyer", "milk": "Cow", "color": "#fbbf24"},
    {"name": "Van, Turkey", "lat": 38.5000, "lon": 43.3833,
     "desc": "Otlu Peynir, a brined cheese with wild mountain herbs from the Van region.",
     "country": "Turkey", "cheese": "Otlu Peynir", "milk": "Sheep", "color": "#fb923c"},
    {"name": "Izmir, Turkey", "lat": 38.4189, "lon": 27.1287,
     "desc": "Tulum Peynir, a strong goat cheese aged in goatskin bags, an Aegean tradition.",
     "country": "Turkey", "cheese": "Tulum Peynir", "milk": "Goat", "color": "#c084fc"},
    {"name": "Split, Croatia", "lat": 43.5081, "lon": 16.4402,
     "desc": "Paski Sir, a hard sheep cheese from the island of Pag, Croatia's most famous cheese.",
     "country": "Croatia", "cheese": "Paski Sir (Pag Cheese)", "milk": "Sheep", "color": "#4ade80"},
    {"name": "Beirut, Lebanon", "lat": 33.8938, "lon": 35.5018,
     "desc": "Akkawi cheese, a mild brined white cheese essential in Lebanese cuisine and manakish.",
     "country": "Lebanon", "cheese": "Akkawi", "milk": "Cow", "color": "#22d3ee"},
    {"name": "Nablus, Palestine", "lat": 32.2211, "lon": 35.2544,
     "desc": "Nabulsi cheese, a brined white cheese boiled with mastic and mahleb, used in knafeh.",
     "country": "Palestine", "cheese": "Nabulsi", "milk": "Sheep/Goat", "color": "#e879f9"},
    {"name": "Cairo, Egypt", "lat": 30.0444, "lon": 31.2357,
     "desc": "Domiati cheese, Egypt's most popular white cheese, salted before curdling.",
     "country": "Egypt", "cheese": "Domiati", "milk": "Buffalo/Cow", "color": "#34d399"},
    {"name": "Podgorica, Montenegro", "lat": 42.4304, "lon": 19.2594,
     "desc": "Njeguski Sir, a semi-hard smoked cheese from the village of Njegos near Cetinje.",
     "country": "Montenegro", "cheese": "Njeguski Sir", "milk": "Sheep/Goat", "color": "#818cf8"},
    {"name": "Kotor, Montenegro", "lat": 42.4247, "lon": 18.7712,
     "desc": "Fresh cheese traditions along the Bay of Kotor, influenced by Venetian and Slavic cuisine.",
     "country": "Montenegro", "cheese": "Kotor Fresh Cheese", "milk": "Goat", "color": "#f472b6"},
    {"name": "Tunis, Tunisia", "lat": 36.8065, "lon": 10.1815,
     "desc": "Testouri, a fresh ball-shaped cheese from North Africa, made from sheep or goat milk.",
     "country": "Tunisia", "cheese": "Testouri", "milk": "Sheep/Goat", "color": "#2dd4bf"},
    {"name": "Tripoli, Libya", "lat": 32.9022, "lon": 13.1800,
     "desc": "Jibna Bayda, white brined cheese made throughout North Africa for generations.",
     "country": "Libya", "cheese": "Jibna Bayda", "milk": "Goat/Sheep", "color": "#facc15"},
    {"name": "Syros, Cyclades", "lat": 37.4333, "lon": 24.9333,
     "desc": "San Michali PDO, a hard grating cheese from Syros, influenced by Venetian cheesemaking.",
     "country": "Greece", "cheese": "San Michali", "milk": "Cow", "color": "#fb7185"},
    {"name": "Kalathaki, Limnos", "lat": 39.9167, "lon": 25.2500,
     "desc": "Kalathaki Limnou PDO, a soft basket-shaped cheese from the Aegean island of Limnos.",
     "country": "Greece", "cheese": "Kalathaki Limnou", "milk": "Sheep/Goat", "color": "#a78bfa"},
    {"name": "Tel Aviv, Israel", "lat": 32.0853, "lon": 34.7818,
     "desc": "Tzfat (Safed) cheese, a semi-hard brined cheese central to Israeli cuisine.",
     "country": "Israel", "cheese": "Tzfat Cheese", "milk": "Sheep", "color": "#60a5fa"},
]

AMERICAN_ARTISAN = [
    {"name": "Jasper Hill Farm, Vermont", "lat": 44.5250, "lon": -72.2167,
     "desc": "Cellars at Jasper Hill, home of Harbison, Bayley Hazen Blue, and cave-aged cheeses.",
     "country": "USA", "cheese": "Harbison / Bayley Hazen Blue", "milk": "Cow", "color": "#06b6d4"},
    {"name": "Cabot, Vermont", "lat": 44.3939, "lon": -72.3060,
     "desc": "Cabot Creamery cooperative, making award-winning Vermont Cheddar since 1919.",
     "country": "USA", "cheese": "Cabot Cheddar", "milk": "Cow", "color": "#f59e0b"},
    {"name": "Plymouth, Vermont", "lat": 43.5167, "lon": -72.7333,
     "desc": "Plymouth Artisan Cheese, reviving the heritage Plymouth cheese from Calvin Coolidge's era.",
     "country": "USA", "cheese": "Plymouth Heritage", "milk": "Cow", "color": "#8b5cf6"},
    {"name": "Monroe, Wisconsin", "lat": 42.6011, "lon": -89.6384,
     "desc": "Swiss Colony town and home of Limburger at Chalet Cheese Co-op, the last in America.",
     "country": "USA", "cheese": "American Limburger", "milk": "Cow", "color": "#ef4444"},
    {"name": "Mineral Point, Wisconsin", "lat": 42.8603, "lon": -90.1793,
     "desc": "Uplands Cheese, maker of Pleasant Ridge Reserve, the most-awarded American cheese.",
     "country": "USA", "cheese": "Pleasant Ridge Reserve", "milk": "Cow", "color": "#10b981"},
    {"name": "Spring Green, Wisconsin", "lat": 43.1775, "lon": -90.0579,
     "desc": "Carr Valley Cheese, producing over 100 varieties from cow, sheep, and goat milk.",
     "country": "USA", "cheese": "Carr Valley Mixed Milk", "milk": "Mixed", "color": "#ec4899"},
    {"name": "Point Reyes, California", "lat": 38.0697, "lon": -122.8064,
     "desc": "Point Reyes Farmstead, making Original Blue and Toma from their own Holstein herd.",
     "country": "USA", "cheese": "Point Reyes Blue", "milk": "Cow", "color": "#f97316"},
    {"name": "Petaluma, California", "lat": 38.2324, "lon": -122.6367,
     "desc": "Marin French Cheese, America's oldest continuously operating cheese company since 1865.",
     "country": "USA", "cheese": "Marin French Triple Cream", "milk": "Cow", "color": "#a855f7"},
    {"name": "Sonoma, California", "lat": 38.2919, "lon": -122.4580,
     "desc": "Vella Cheese Company, making Dry Jack since 1931 in the heart of wine country.",
     "country": "USA", "cheese": "Vella Dry Jack", "milk": "Cow", "color": "#14b8a6"},
    {"name": "Central Point, Oregon", "lat": 42.3779, "lon": -122.9023,
     "desc": "Rogue Creamery, maker of Rogue River Blue wrapped in grape leaves soaked in pear brandy.",
     "country": "USA", "cheese": "Rogue River Blue", "milk": "Cow", "color": "#d946ef"},
    {"name": "Tillamook, Oregon", "lat": 45.4562, "lon": -123.8426,
     "desc": "Tillamook County Creamery, cooperative of dairy families making cheese since 1909.",
     "country": "USA", "cheese": "Tillamook Cheddar", "milk": "Cow", "color": "#38bdf8"},
    {"name": "Greensboro, Vermont", "lat": 44.5286, "lon": -72.2858,
     "desc": "Jasper Hill's Cellars at Jasper Hill, aging facility for Northeast artisan cheeses.",
     "country": "USA", "cheese": "Cabot Clothbound Cheddar", "milk": "Cow", "color": "#fbbf24"},
    {"name": "Cato Corner Farm, Connecticut", "lat": 41.5000, "lon": -72.4167,
     "desc": "Bloomsday and Dutch Farmstead raw-milk cheeses from a small New England farm.",
     "country": "USA", "cheese": "Bloomsday", "milk": "Cow", "color": "#fb923c"},
    {"name": "Consider Bardwell Farm, Vermont", "lat": 43.1000, "lon": -73.2667,
     "desc": "Pawlet and Dorset cheeses from Vermont's oldest cheesemaking operation (est. 1864).",
     "country": "USA", "cheese": "Pawlet / Dorset", "milk": "Cow/Goat", "color": "#c084fc"},
    {"name": "Cypress Grove, Humboldt, CA", "lat": 40.7833, "lon": -124.1500,
     "desc": "Humboldt Fog, the iconic American goat cheese with a line of vegetable ash.",
     "country": "USA", "cheese": "Humboldt Fog", "milk": "Goat", "color": "#4ade80"},
    {"name": "Sweet Grass Dairy, Georgia", "lat": 30.8333, "lon": -83.2833,
     "desc": "Southern artisan cheeses including Green Hill, a double-cream Camembert-style.",
     "country": "USA", "cheese": "Green Hill", "milk": "Cow", "color": "#22d3ee"},
    {"name": "Beecher's, Seattle, WA", "lat": 47.6097, "lon": -122.3406,
     "desc": "Beecher's Handmade Cheese at Pike Place Market, making Flagship in view of visitors.",
     "country": "USA", "cheese": "Beecher's Flagship", "milk": "Cow", "color": "#e879f9"},
    {"name": "Murray's Cheese, NYC", "lat": 40.7308, "lon": -74.0019,
     "desc": "Murray's Cheese Caves in Greenwich Village, aging cheeses under Bleecker Street.",
     "country": "USA", "cheese": "Murray's Cave Aged", "milk": "Various", "color": "#34d399"},
    {"name": "Cowgirl Creamery, Point Reyes, CA", "lat": 38.0725, "lon": -122.7978,
     "desc": "Organic Mt Tam triple cream and Red Hawk washed-rind from the Point Reyes coast.",
     "country": "USA", "cheese": "Mt Tam / Red Hawk", "milk": "Cow", "color": "#818cf8"},
    {"name": "Fiscalini Farmstead, Modesto, CA", "lat": 37.6391, "lon": -120.9969,
     "desc": "Bandage-wrapped Cheddar aged 18+ months from a third-generation California dairy.",
     "country": "USA", "cheese": "Fiscalini Cheddar", "milk": "Cow", "color": "#f472b6"},
    {"name": "Roth Cheese, Monroe, WI", "lat": 42.6042, "lon": -89.6385,
     "desc": "Grand Cru Gruyere and alpine-style cheeses from Wisconsin's Swiss heritage region.",
     "country": "USA", "cheese": "Roth Grand Cru", "milk": "Cow", "color": "#2dd4bf"},
    {"name": "Grafton Village Cheese, VT", "lat": 43.1750, "lon": -72.6083,
     "desc": "Raw-milk Cheddar aged in caves, a Vermont cheesemaking tradition since 1892.",
     "country": "USA", "cheese": "Grafton Village Cheddar", "milk": "Cow", "color": "#facc15"},
    {"name": "Meadow Creek Dairy, Virginia", "lat": 36.7333, "lon": -81.3833,
     "desc": "Grayson, an Appalachian washed-rind inspired by Taleggio, from the Blue Ridge Mountains.",
     "country": "USA", "cheese": "Grayson", "milk": "Cow", "color": "#fb7185"},
    {"name": "Bleu Mont Dairy, Wisconsin", "lat": 42.9833, "lon": -89.8833,
     "desc": "Earth-sheltered cave-aged Cheddar and blue cheeses from Willi Lehner's hillside dairy.",
     "country": "USA", "cheese": "Bleu Mont Bandaged Cheddar", "milk": "Cow", "color": "#a78bfa"},
    {"name": "Shelburne Farms, Vermont", "lat": 44.3833, "lon": -73.2500,
     "desc": "1400-acre farm on Lake Champlain making award-winning two-year Cheddar.",
     "country": "USA", "cheese": "Shelburne Farms Cheddar", "milk": "Cow", "color": "#60a5fa"},
    {"name": "Beehive Cheese, Utah", "lat": 41.7333, "lon": -111.8333,
     "desc": "Promontory and Barely Buzzed espresso-rubbed cheeses from Cache Valley, Utah.",
     "country": "USA", "cheese": "Barely Buzzed", "milk": "Cow", "color": "#c4b5fd"},
]

ANCIENT_CHEESE = [
    {"name": "Taklamakan Desert, Xinjiang", "lat": 38.9500, "lon": 82.8000,
     "desc": "Oldest cheese ever found (1615 BC), preserved on Bronze Age Xiaohe mummies in desert tombs.",
     "country": "China", "cheese": "Xiaohe Kefir Cheese", "milk": "Cow/Goat", "color": "#f59e0b"},
    {"name": "Saqqara, Egypt", "lat": 29.8700, "lon": 31.2164,
     "desc": "3200-year-old cheese found in the tomb of Ptahmes, mayor of Memphis, made from sheep/goat milk.",
     "country": "Egypt", "cheese": "Ancient Egyptian Cheese", "milk": "Sheep/Goat", "color": "#06b6d4"},
    {"name": "Dalmatia, Croatia", "lat": 43.5000, "lon": 16.5000,
     "desc": "Neolithic pottery with cheese residue (5200 BC) found at Dalmatian sites, earliest Mediterranean evidence.",
     "country": "Croatia", "cheese": "Neolithic Curd Cheese", "milk": "Sheep/Goat", "color": "#8b5cf6"},
    {"name": "Kuyavia, Poland", "lat": 52.5000, "lon": 18.5000,
     "desc": "Perforated pottery strainers (5000 BC) with milk fat residue, among earliest cheese-making tools.",
     "country": "Poland", "cheese": "Neolithic Strained Cheese", "milk": "Cow", "color": "#ef4444"},
    {"name": "Ur, Mesopotamia (Iraq)", "lat": 30.9628, "lon": 46.1031,
     "desc": "Sumerian dairy scenes on the Ur frieze (2500 BC) showing cheese-making from cow milk.",
     "country": "Iraq", "cheese": "Sumerian Curd", "milk": "Cow", "color": "#ec4899"},
    {"name": "Rome, Italy", "lat": 41.9028, "lon": 12.4964,
     "desc": "Columella's De Re Rustica (65 AD) describes cheese recipes still recognizable today.",
     "country": "Italy", "cheese": "Roman Cheese (Caseus)", "milk": "Sheep/Goat", "color": "#10b981"},
    {"name": "Herculaneum, Italy", "lat": 40.8058, "lon": 14.3478,
     "desc": "Carbonized cheese found in shops buried by Vesuvius in 79 AD, preserved by volcanic ash.",
     "country": "Italy", "cheese": "Herculaneum Cheese", "milk": "Sheep", "color": "#f97316"},
    {"name": "Mongolia Steppe", "lat": 47.9200, "lon": 106.9100,
     "desc": "Mongol aaruul (dried curd) tradition, portable protein carried by Genghis Khan's cavalry.",
     "country": "Mongolia", "cheese": "Aaruul (Dried Curd)", "milk": "Yak/Mare/Cow", "color": "#a855f7"},
    {"name": "Tibet Plateau", "lat": 29.6500, "lon": 91.1000,
     "desc": "Chhurpi, a traditional Himalayan yak cheese dried into hard chews, consumed for millennia.",
     "country": "China/Tibet", "cheese": "Chhurpi (Yak Cheese)", "milk": "Yak", "color": "#14b8a6"},
    {"name": "Anatolia, Turkey", "lat": 39.9208, "lon": 32.8541,
     "desc": "Earliest evidence of dairying in western Turkey (6500 BC), at Catalhoyuk settlement.",
     "country": "Turkey", "cheese": "Neolithic Anatolian Dairy", "milk": "Sheep/Goat", "color": "#d946ef"},
    {"name": "Sahara Desert, Libya", "lat": 26.3351, "lon": 17.2283,
     "desc": "Rock art at Tassili n'Ajjer (5000 BC) showing milking scenes in a green Sahara.",
     "country": "Libya/Algeria", "cheese": "Saharan Pastoral Dairy", "milk": "Cow", "color": "#38bdf8"},
    {"name": "Swiss Lake Dwellings", "lat": 47.3769, "lon": 8.5417,
     "desc": "Neolithic Swiss lakeside settlements (3000 BC) with ceramic strainers for cheese-making.",
     "country": "Switzerland", "cheese": "Lake Dwelling Cheese", "milk": "Cow/Goat", "color": "#fbbf24"},
    {"name": "Vindolanda, Hadrian's Wall", "lat": 54.9900, "lon": -2.3600,
     "desc": "Roman fort tablets referencing cheese rations for soldiers guarding Britannia's frontier.",
     "country": "United Kingdom", "cheese": "Roman Military Cheese", "milk": "Cow/Sheep", "color": "#fb923c"},
    {"name": "Homer's Cave, Greece", "lat": 38.3667, "lon": 20.7167,
     "desc": "Cyclops Polyphemus making sheep cheese in Homer's Odyssey (8th century BC).",
     "country": "Greece", "cheese": "Homeric Sheep Cheese", "milk": "Sheep", "color": "#c084fc"},
    {"name": "Mount Ararat Region, Armenia", "lat": 39.7000, "lon": 44.3000,
     "desc": "Areni-1 cave with 5000-year-old residue evidence of dairying and winemaking.",
     "country": "Armenia", "cheese": "Ancient Armenian Dairy", "milk": "Sheep/Goat", "color": "#4ade80"},
    {"name": "Pliny the Elder's Rome", "lat": 41.8902, "lon": 12.4922,
     "desc": "Pliny's Natural History (77 AD) ranks cheeses from across the Roman Empire.",
     "country": "Italy", "cheese": "Pliny's Cheese Rankings", "milk": "Various", "color": "#22d3ee"},
    {"name": "Cluny Abbey, Burgundy", "lat": 46.4342, "lon": 4.6592,
     "desc": "Medieval monastic cheesemaking tradition, Benedictine monks systematized aging techniques.",
     "country": "France", "cheese": "Monastic Cheese Tradition", "milk": "Cow", "color": "#e879f9"},
    {"name": "Parma, Medieval Italy", "lat": 44.8015, "lon": 10.3280,
     "desc": "First documented Parmesan-type cheese in 1254, Boccaccio described it in 1348.",
     "country": "Italy", "cheese": "Medieval Parmesan", "milk": "Cow", "color": "#34d399"},
    {"name": "Roquefort Caves, Medieval France", "lat": 43.9780, "lon": 2.9815,
     "desc": "Charlemagne tasted Roquefort in 774 AD; it received a royal charter from Charles VI in 1411.",
     "country": "France", "cheese": "Medieval Roquefort", "milk": "Sheep", "color": "#818cf8"},
    {"name": "Fertile Crescent, Levant", "lat": 33.5138, "lon": 36.2765,
     "desc": "The origin region of animal domestication and the dawn of dairying (8000 BC).",
     "country": "Syria/Iraq", "cheese": "Proto-Cheese (Curd)", "milk": "Sheep/Goat", "color": "#f472b6"},
    {"name": "Maasai Lands, East Africa", "lat": -2.8333, "lon": 36.8333,
     "desc": "Traditional cattle-herding cultures making fermented milk products for thousands of years.",
     "country": "Kenya/Tanzania", "cheese": "Maasai Fermented Milk", "milk": "Cow", "color": "#2dd4bf"},
    {"name": "Cheshire, Roman Britain", "lat": 53.1933, "lon": -2.8931,
     "desc": "Roman-era salt mines enabling cheese preservation; Cheshire may be England's oldest cheese.",
     "country": "United Kingdom", "cheese": "Roman-Era Cheshire", "milk": "Cow", "color": "#facc15"},
    {"name": "Jericho, Palestine", "lat": 31.8667, "lon": 35.4500,
     "desc": "One of the world's oldest cities with evidence of goat husbandry and dairy processing.",
     "country": "Palestine", "cheese": "Ancient Levantine Dairy", "milk": "Goat", "color": "#fb7185"},
    {"name": "Lascaux, France", "lat": 45.0542, "lon": 1.1686,
     "desc": "Paleolithic cave paintings showing aurochs; the ancestors of dairy cattle roamed here.",
     "country": "France", "cheese": "Pre-Dairy Aurochs", "milk": "N/A", "color": "#a78bfa"},
    {"name": "Indus Valley, Pakistan", "lat": 27.3228, "lon": 68.1389,
     "desc": "Mohenjo-daro and Harappan sites with dairy residue in pottery (2600 BC).",
     "country": "Pakistan", "cheese": "Indus Valley Dairy", "milk": "Cow/Buffalo", "color": "#60a5fa"},
    {"name": "Viking York, England", "lat": 53.9600, "lon": -1.0873,
     "desc": "Viking-era cheese molds found at Jorvik (York), evidence of Norse dairy skills in Britain.",
     "country": "United Kingdom", "cheese": "Viking Skyr/Cheese", "milk": "Cow/Sheep", "color": "#c4b5fd"},
]

CHEESE_MUSEUMS_FESTIVALS = [
    {"name": "Cooper's Hill, Gloucestershire", "lat": 51.8443, "lon": -2.1561,
     "desc": "Annual Cheese Rolling event: competitors chase a 9-lb Double Gloucester down a steep hill.",
     "country": "United Kingdom", "event": "Cheese Rolling", "color": "#f59e0b"},
    {"name": "Alkmaar Cheese Market", "lat": 52.6324, "lon": 4.7534,
     "desc": "Traditional Friday cheese market since 1593 with porters in white and colored hats.",
     "country": "Netherlands", "event": "Cheese Market", "color": "#06b6d4"},
    {"name": "Maison du Gruyere, Gruyeres", "lat": 46.5833, "lon": 7.0833,
     "desc": "Interactive museum and cheese dairy where visitors watch Gruyere being made daily.",
     "country": "Switzerland", "event": "Cheese Museum/Dairy", "color": "#8b5cf6"},
    {"name": "Emmental Show Dairy, Affoltern", "lat": 46.8833, "lon": 7.7333,
     "desc": "Working show dairy demonstrating Emmentaler production with tastings.",
     "country": "Switzerland", "event": "Show Dairy", "color": "#ef4444"},
    {"name": "Bra Cheese Festival, Piedmont", "lat": 44.6986, "lon": 7.8533,
     "desc": "Slow Food's biennial 'Cheese' fair, the world's largest artisan cheese event.",
     "country": "Italy", "event": "Cheese Festival (Biennial)", "color": "#ec4899"},
    {"name": "Gouda Cheese Market", "lat": 52.0115, "lon": 4.7104,
     "desc": "Historic Thursday morning cheese market on the Markt square, active since the Middle Ages.",
     "country": "Netherlands", "event": "Cheese Market", "color": "#10b981"},
    {"name": "Cheddar Gorge Cheese Company", "lat": 51.2839, "lon": -2.7614,
     "desc": "Only Cheddar maker still in Cheddar, producing in the traditional cave-aged method.",
     "country": "United Kingdom", "event": "Working Cheese Dairy", "color": "#f97316"},
    {"name": "Maison du Camembert, Normandy", "lat": 48.8789, "lon": 0.1692,
     "desc": "Museum dedicated to Camembert history, from Marie Harel to modern AOP production.",
     "country": "France", "event": "Cheese Museum", "color": "#a855f7"},
    {"name": "Wisconsin Cheese Museum, Monroe", "lat": 42.6011, "lon": -89.6384,
     "desc": "Historic Cheesemaking Center documenting Swiss immigrant cheese traditions in America.",
     "country": "USA", "event": "Cheese Museum", "color": "#14b8a6"},
    {"name": "Stresa Convention Site, Italy", "lat": 45.8842, "lon": 8.5336,
     "desc": "Location of the 1951 Stresa Convention that established international cheese naming rules.",
     "country": "Italy", "event": "Cheese Legislation History", "color": "#d946ef"},
    {"name": "Appenzeller Schaukaeserei", "lat": 47.3256, "lon": 9.4097,
     "desc": "Show dairy in Stein AR where visitors see Appenzeller made with its secret herbal brine.",
     "country": "Switzerland", "event": "Show Dairy", "color": "#38bdf8"},
    {"name": "Roquefort Caves Visit Center", "lat": 43.9783, "lon": 2.9811,
     "desc": "Tours of the natural Combalou caves where Roquefort has been aged for centuries.",
     "country": "France", "event": "Cave Tours", "color": "#fbbf24"},
    {"name": "Amsterdam Cheese Museum", "lat": 52.3760, "lon": 4.8840,
     "desc": "Free cheese museum on the Prinsengracht canal with tastings and cheese history.",
     "country": "Netherlands", "event": "Cheese Museum", "color": "#fb923c"},
    {"name": "Fete du Fromage, Rocamadour", "lat": 44.7994, "lon": 1.6186,
     "desc": "Annual Whitsun cheese festival celebrating Rocamadour goat cheese in the Lot valley.",
     "country": "France", "event": "Cheese Festival", "color": "#c084fc"},
    {"name": "Great British Cheese Festival, Cardiff", "lat": 51.4816, "lon": -3.1791,
     "desc": "Annual celebration of British and international artisan cheeses in Cardiff Castle.",
     "country": "United Kingdom", "event": "Cheese Festival", "color": "#4ade80"},
    {"name": "Vermont Cheesemakers Festival", "lat": 44.2500, "lon": -72.5667,
     "desc": "Annual festival showcasing 40+ Vermont artisan cheesemakers with tastings and pairings.",
     "country": "USA", "event": "Cheese Festival", "color": "#22d3ee"},
    {"name": "Kaesiade, Hopfgarten, Austria", "lat": 47.4500, "lon": 12.1667,
     "desc": "Biennial alpine cheese olympiad judging 500+ mountain cheeses from across the Alps.",
     "country": "Austria", "event": "Cheese Competition", "color": "#e879f9"},
    {"name": "Salon du Fromage, Paris", "lat": 48.8566, "lon": 2.3522,
     "desc": "Professional cheese salon at the Paris agricultural show, with MOF cheese competitions.",
     "country": "France", "event": "Cheese Salon", "color": "#34d399"},
    {"name": "World Championship Cheese Contest, Madison", "lat": 43.0731, "lon": -89.4012,
     "desc": "Biennial contest judging 3000+ cheeses, the world's largest technical cheese competition.",
     "country": "USA", "event": "Cheese Competition", "color": "#818cf8"},
    {"name": "Chaesteilet, Justistal", "lat": 46.7333, "lon": 7.7500,
     "desc": "Ancient cheese-dividing festival in the Bernese Oberland, distributing alpine cheese.",
     "country": "Switzerland", "event": "Cheese Division Festival", "color": "#f472b6"},
    {"name": "Feria del Queso, Trujillo, Spain", "lat": 39.4583, "lon": -5.8808,
     "desc": "Spain's national cheese fair held each May in the medieval plaza of Trujillo.",
     "country": "Spain", "event": "Cheese Fair", "color": "#2dd4bf"},
    {"name": "Canadian Cheese Museum, Ingersoll", "lat": 43.0381, "lon": -80.8834,
     "desc": "Museum celebrating Canada's cheese heritage, including the famous 7000-lb mammoth cheese.",
     "country": "Canada", "event": "Cheese Museum", "color": "#facc15"},
    {"name": "Edam Museum, North Holland", "lat": 52.5133, "lon": 5.0467,
     "desc": "Edams Museum in a 1530 merchant house, documenting the cheese trade history of Edam.",
     "country": "Netherlands", "event": "Cheese Museum", "color": "#fb7185"},
    {"name": "Wensleydale Creamery Visitor Centre", "lat": 54.3033, "lon": -2.1947,
     "desc": "Museum and viewing gallery in Hawes, Yorkshire Dales, with cheese-making demonstrations.",
     "country": "United Kingdom", "event": "Visitor Centre", "color": "#a78bfa"},
    {"name": "Parmigiano-Reggiano Museum, Soragna", "lat": 44.9250, "lon": 10.1250,
     "desc": "Museum of Parmigiano-Reggiano in the Rocca Meli Lupi castle, documenting 900 years of production.",
     "country": "Italy", "event": "Cheese Museum", "color": "#60a5fa"},
    {"name": "Fromagerie Hamel, Montreal", "lat": 45.5017, "lon": -73.5673,
     "desc": "Iconic Montreal fromagerie hosting tastings and Quebec artisan cheese events.",
     "country": "Canada", "event": "Cheese Shop/Events", "color": "#c4b5fd"},
]

# ═══════════════════════════════════════════
# MODE -> DATA MAP
# ═══════════════════════════════════════════
MODE_DATA = {
    "French Cheese AOC Regions": FRENCH_AOC,
    "Italian Cheese DOP": ITALIAN_DOP,
    "Swiss Cheese Traditions": SWISS_CHEESE,
    "British Cheese Heritage": BRITISH_CHEESE,
    "Dutch & Belgian Cheese": DUTCH_BELGIAN,
    "Spanish & Portuguese Cheese": SPANISH_PORTUGUESE,
    "Greek & Mediterranean Cheese": GREEK_MEDITERRANEAN,
    "American Artisan Cheese": AMERICAN_ARTISAN,
    "Ancient Cheese History": ANCIENT_CHEESE,
    "Cheese Museums & Festivals": CHEESE_MUSEUMS_FESTIVALS,
}


# ═══════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════

def _build_map(items: list, mode: str) -> folium.Map:
    """Build a Folium dark-theme map with clustered markers."""
    avg_lat = sum(it["lat"] for it in items) / len(items)
    avg_lon = sum(it["lon"] for it in items) / len(items)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=5,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name="Cheese Locations").add_to(m)

    for item in items:
        name_safe = html_module.escape(item["name"])
        desc_safe = html_module.escape(item["desc"])
        color = item.get("color", "#06b6d4")

        extra_lines = ""
        if "country" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Country: {html_module.escape(item["country"])}</span>'
        if "cheese" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Cheese: {html_module.escape(item["cheese"])}</span>'
        if "milk" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Milk: {html_module.escape(item["milk"])}</span>'
        if "event" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Event: {html_module.escape(item["event"])}</span>'

        popup_html = f"""
        <div style="max-width:240px;">
            <strong style="color:{color};">{name_safe}</strong>
            {extra_lines}
            <br/><span style="font-size:0.78rem; color:#555;">{desc_safe}</span>
            <br/><span style="font-size:0.72rem; color:#888;">{item['lat']:.4f}, {item['lon']:.4f}</span>
        </div>
        """

        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=name_safe,
        ).add_to(cluster)

    return m


def _build_dataframe(items: list, mode: str) -> pd.DataFrame:
    """Build a display DataFrame from item list."""
    rows = []
    for item in items:
        row = {
            "Name": item["name"],
            "Latitude": item["lat"],
            "Longitude": item["lon"],
            "Description": item["desc"],
        }
        if "country" in item:
            row["Country"] = item["country"]
        if "cheese" in item:
            row["Cheese"] = item["cheese"]
        if "milk" in item:
            row["Milk Type"] = item["milk"]
        if "event" in item:
            row["Event"] = item["event"]
        rows.append(row)
    return pd.DataFrame(rows)


def _get_csv(df: pd.DataFrame) -> str:
    """Convert DataFrame to CSV string."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════

def render_cheese_maps_tab():
    """Main render function for the Cheese & Dairy Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header pink">
        <h4>Cheese & Dairy Explorer</h4>
        <p>Discover world cheese regions, AOC/DOP designations, ancient dairy history, artisan creameries, cheese museums, and festivals on an interactive dark-theme map.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode Selection
    # ══════════════════════════════════════════
    mode = st.selectbox(
        "Cheese Map Mode",
        MODE_OPTIONS,
        key="cheese_mode",
        help="Choose a cheese category to explore on the map.",
    )

    icon = MODE_ICONS.get(mode, "\U0001f9c0")
    mode_desc = MODE_DESCRIPTIONS.get(mode, "")
    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem;">{icon} {html_module.escape(mode_desc)}</p>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # SECTION 2: Load Data
    # ══════════════════════════════════════════
    items = MODE_DATA.get(mode, [])

    if not items:
        st.warning("No data available for this mode.")
        return

    # ══════════════════════════════════════════
    # SECTION 3: Stats Row
    # ══════════════════════════════════════════
    st.markdown("---")

    countries = set(it.get("country", "") for it in items)
    cheeses = set(it.get("cheese", "") for it in items if it.get("cheese"))
    milks = set(it.get("milk", "") for it in items if it.get("milk"))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Locations", len(items))
    with c2:
        st.metric("Countries / Areas", len(countries))
    with c3:
        if cheeses:
            st.metric("Distinct Cheeses", len(cheeses))
        elif milks:
            st.metric("Milk Types", len(milks))
        else:
            st.metric("Category", mode.split(" ")[0])
    with c4:
        lat_range = max(it["lat"] for it in items) - min(it["lat"] for it in items)
        st.metric("Lat Spread", f"{lat_range:.1f}\u00b0")

    # ══════════════════════════════════════════
    # SECTION 4: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {icon} {html_module.escape(mode)} Map")

    # Legend
    legend_items = " ".join(
        f'<span style="color:{it["color"]}; font-size:0.8rem;">\u25cf {html_module.escape(it["name"][:30])}</span>'
        for it in items[:12]
    )
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
        unsafe_allow_html=True,
    )

    m = _build_map(items, mode)
    st_html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 5: Data Table
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Cheese Data")

    df = _build_dataframe(items, mode)

    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 6: Notable Entries Cards
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Highlights")

    for item in items[:8]:
        name_safe = html_module.escape(item["name"])
        desc_safe = html_module.escape(item["desc"])
        color = item.get("color", "#06b6d4")

        sub_info = ""
        if "country" in item:
            sub_info += html_module.escape(item["country"])
        if "cheese" in item:
            sub_info += f" &mdash; {html_module.escape(item['cheese'])}"
        if "milk" in item:
            sub_info += f" &mdash; {html_module.escape(item['milk'])} milk"
        if "event" in item:
            sub_info += f" &mdash; {html_module.escape(item['event'])}"

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
            <div style="width:10px; height:56px; border-radius:5px; background:{color};
                        margin-right:0.75rem; flex-shrink:0;"></div>
            <div>
                <div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{name_safe}</div>
                <div style="color:#8b97b0; font-size:0.75rem;">{sub_info}</div>
                <div style="color:#5a6580; font-size:0.7rem;">{desc_safe[:120]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 7: CSV Download
    # ══════════════════════════════════════════
    st.markdown("---")

    csv_data = _get_csv(df)
    filename = mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        f"Download {len(df)} {mode} Locations (CSV)",
        data=csv_data,
        file_name=f"cheese_{filename}.csv",
        mime="text/csv",
        key="cheese_download",
    )
