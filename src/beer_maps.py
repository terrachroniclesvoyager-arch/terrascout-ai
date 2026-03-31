# -*- coding: utf-8 -*-
"""
Beer & Brewing Heritage Explorer module for TerraScout AI.
Provides 10 interactive map modes covering Trappist abbeys, German beer heritage,
Czech pilsner history, British pub culture, American craft beer, Japanese craft beer,
ancient brewing, hop growing regions, beer festivals, and brewery museums/tours.
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
_ACCENT = "#06b6d4"
_MUTED = "#5a6580"

# ===================================================================
# MAP MODE LIST
# ===================================================================
MAP_MODES = [
    "Belgian Abbey & Trappist Breweries",
    "German Beer Heritage",
    "Czech & Pilsner Heritage",
    "British Pub & Ale Heritage",
    "American Craft Beer Revolution",
    "Japanese Craft Beer",
    "Ancient Brewing History",
    "Hop Growing Regions",
    "Oktoberfest & Beer Festivals",
    "Beer Museums & Brewery Tours",
]

# ===================================================================
# 1. BELGIAN ABBEY & TRAPPIST BREWERIES (28 entries)
# ===================================================================
BELGIAN_TRAPPIST = [
    {"name": "Westvleteren Brewery (Sint-Sixtus)", "lat": 50.8933, "lon": 2.7228, "country": "Belgium", "style": "Trappist Quad/Blonde/8", "founded": "1838", "notes": "Consistently rated world's best beer; limited sales at monastery gate only; Westvleteren 12 is legendary"},
    {"name": "Chimay Brewery (Scourmont Abbey)", "lat": 50.0494, "lon": 4.3178, "country": "Belgium", "style": "Trappist Red/Blue/White", "founded": "1862", "notes": "Largest Trappist brewery; Chimay Blue is a world-class strong dark ale; also produces cheese"},
    {"name": "Orval Brewery (Abbaye d'Orval)", "lat": 49.6369, "lon": 5.3478, "country": "Belgium", "style": "Trappist Pale Ale", "founded": "1931", "notes": "Only one beer; dry-hopped with Brettanomyces; unique among Trappist ales; iconic skittle-shaped glass"},
    {"name": "Rochefort Brewery (Saint-Remy Abbey)", "lat": 50.1600, "lon": 5.2219, "country": "Belgium", "style": "Trappist 6/8/10", "founded": "1595", "notes": "Rochefort 10 is among world's finest dark strong ales; brewed since late 16th century"},
    {"name": "Westmalle Brewery (Abbey of Westmalle)", "lat": 51.2853, "lon": 4.6633, "country": "Belgium", "style": "Trappist Dubbel/Tripel", "founded": "1836", "notes": "Defined the modern Dubbel and Tripel styles; Westmalle Tripel is the benchmark for the style"},
    {"name": "Achel Brewery (Achelse Kluis)", "lat": 51.3978, "lon": 5.4819, "country": "Belgium", "style": "Trappist Blonde/Bruin", "founded": "1648", "notes": "Lost Trappist status in 2021 due to lack of monks; still brews on monastery grounds"},
    {"name": "La Trappe Brewery (Koningshoeven)", "lat": 51.5431, "lon": 5.0900, "country": "Netherlands", "style": "Trappist Dubbel/Tripel/Quad", "founded": "1884", "notes": "Only Dutch Trappist brewery; wide range includes Isid'or, Bockbier, and oak-aged Quad"},
    {"name": "Stift Engelszell Brewery", "lat": 48.5028, "lon": 13.7347, "country": "Austria", "style": "Trappist Gregorius/Benno", "founded": "2012", "notes": "Only Austrian Trappist; Gregorius uses local honey; small-batch artisanal production"},
    {"name": "Zundert Brewery (Maria Toevlucht)", "lat": 51.4672, "lon": 4.6531, "country": "Netherlands", "style": "Trappist 10", "founded": "2013", "notes": "Newest Dutch Trappist; single amber-copper beer with fruity Belgian yeast character"},
    {"name": "Tre Fontane Brewery", "lat": 41.8347, "lon": 12.4761, "country": "Italy", "style": "Trappist Tripel", "founded": "2015", "notes": "Only Italian Trappist; brewed with eucalyptus grown on monastery grounds; unique flavor"},
    {"name": "Tynt Meadow (Mount Saint Bernard)", "lat": 52.7311, "lon": -1.3053, "country": "England", "style": "Trappist English Dark Ale", "founded": "2018", "notes": "Only English Trappist; mahogany dark ale with chocolate and pepper notes; very limited output"},
    {"name": "Spencer Brewery (St. Joseph's Abbey)", "lat": 42.2428, "lon": -72.0103, "country": "USA", "style": "Trappist Ale (ceased 2022)", "founded": "2013", "notes": "First American Trappist; closed in 2022 due to pandemic economic pressures"},
    {"name": "Cantillon Brewery", "lat": 50.8433, "lon": 4.3331, "country": "Belgium", "style": "Lambic/Gueuze/Kriek", "founded": "1900", "notes": "Iconic spontaneously fermented lambic brewery in Brussels; open-air coolship; museum on site"},
    {"name": "Brasserie Dupont", "lat": 50.5019, "lon": 3.6033, "country": "Belgium", "style": "Saison Dupont", "founded": "1844", "notes": "Saison Dupont is the definitive farmhouse ale; originally brewed for seasonal farm workers"},
    {"name": "Brasserie d'Achouffe", "lat": 50.1244, "lon": 5.7844, "country": "Belgium", "style": "La Chouffe Golden Ale", "founded": "1982", "notes": "Iconic gnome-branded Belgian strong golden ale; Ardennes forest setting; major craft pioneer"},
    {"name": "Duvel Moortgat Brewery", "lat": 51.0811, "lon": 4.4656, "country": "Belgium", "style": "Duvel Strong Golden Ale", "founded": "1871", "notes": "Duvel (meaning 'devil') is the quintessential Belgian strong golden ale; secondary bottle fermentation"},
    {"name": "Brouwerij Rodenbach", "lat": 50.9500, "lon": 3.1228, "country": "Belgium", "style": "Flemish Red-Brown Ale", "founded": "1821", "notes": "Grand Cru aged in massive oak foeders; Flemish sour ale tradition; cathedral of wood aging"},
    {"name": "Brasserie de la Senne", "lat": 50.8497, "lon": 4.3361, "country": "Belgium", "style": "Taras Boulba/Brusseleir", "founded": "2006", "notes": "New-wave Brussels brewery reviving hoppy, dry Belgian ales; counter to sweet Belgian tradition"},
    {"name": "Brouwerij De Ranke", "lat": 50.7547, "lon": 2.7803, "country": "Belgium", "style": "XX Bitter/Guldenberg", "founded": "1994", "notes": "Pioneered aggressively hopped Belgian ales; XX Bitter combines American hops with Belgian yeast"},
    {"name": "Brouwerij St. Bernardus", "lat": 50.9139, "lon": 2.6936, "country": "Belgium", "style": "Abt 12/Prior 8/Wit", "founded": "1946", "notes": "Originally brewed under Westvleteren license; Abt 12 rivals St. Sixtus in quality"},
    {"name": "Brasserie de Rochefort (Val-Dieu)", "lat": 50.6564, "lon": 5.8292, "country": "Belgium", "style": "Abbey Blonde/Brune/Triple", "founded": "1216", "notes": "Cistercian abbey brewery in Herve; modern revival of 800-year abbey brewing tradition"},
    {"name": "Het Anker Brewery", "lat": 51.0294, "lon": 4.4847, "country": "Belgium", "style": "Gouden Carolus Classic/Tripel", "founded": "1471", "notes": "One of Belgium's oldest breweries; Gouden Carolus named for coins of Emperor Charles V"},
    {"name": "Brouwerij Verhaeghe", "lat": 50.8503, "lon": 3.2622, "country": "Belgium", "style": "Duchesse de Bourgogne", "founded": "1885", "notes": "Flemish red-brown sour ale blended from young and 18-month oak-aged beer; sweet-sour masterpiece"},
    {"name": "Brouwerij Huyghe", "lat": 51.0000, "lon": 3.7906, "country": "Belgium", "style": "Delirium Tremens", "founded": "1654", "notes": "Delirium Tremens in its pink elephant bottle is globally recognized; strong blonde ale icon"},
    {"name": "Brouwerij Lindemans", "lat": 50.7628, "lon": 4.2097, "country": "Belgium", "style": "Lambic/Gueuze/Framboise", "founded": "1822", "notes": "Pajottenland lambic producer; fruit lambics introduced sour beer to mainstream audiences"},
    {"name": "Brasserie Fantome", "lat": 50.0422, "lon": 5.7019, "country": "Belgium", "style": "Fantome Saison", "founded": "1988", "notes": "One-man farmhouse brewery; every batch unique; cult following among beer connoisseurs"},
    {"name": "Brouwerij 3 Fonteinen", "lat": 50.7694, "lon": 4.1819, "country": "Belgium", "style": "Oude Gueuze/Kriek", "founded": "1887", "notes": "Premier gueuze blender in Pajottenland; Oude Gueuze is benchmark for the style; traditional methods"},
    {"name": "Brouwerij De Dolle Brouwers", "lat": 51.0711, "lon": 2.9456, "country": "Belgium", "style": "Oerbier/Arabier", "founded": "1980", "notes": "Mad Brewers of Esen; eccentric, bold ales with wild yeast character; weekend-only brewery"},
]

# ===================================================================
# 2. GERMAN BEER HERITAGE (28 entries)
# ===================================================================
GERMAN_HERITAGE = [
    {"name": "Hofbrauhaus Munich", "lat": 48.1378, "lon": 11.5799, "country": "Germany", "style": "Helles/Dunkel/Weizen", "founded": "1589", "notes": "World's most famous beer hall; founded by Duke Wilhelm V; seats 3,000+; center of Bavarian beer culture"},
    {"name": "Augustiner-Brau Munich", "lat": 48.1392, "lon": 11.5671, "country": "Germany", "style": "Augustiner Helles", "founded": "1328", "notes": "Munich's oldest brewery; beloved Helles served from wooden casks; Stammhaus beer hall is iconic"},
    {"name": "Weihenstephan Brewery (Freising)", "lat": 48.3947, "lon": 11.7286, "country": "Germany", "style": "Hefeweizen/Helles/Vitus", "founded": "1040", "notes": "World's oldest continuously operating brewery; Benedictine monks started in 1040; attached to TU Munich"},
    {"name": "Schlenkerla Rauchbier (Bamberg)", "lat": 49.8917, "lon": 10.8844, "country": "Germany", "style": "Rauchbier (Smoked Beer)", "founded": "1405", "notes": "Legendary smoked beer tavern; malt smoked over beechwood fires; Bamberg's signature style since medieval era"},
    {"name": "Spezial Keller (Bamberg)", "lat": 49.8947, "lon": 10.8853, "country": "Germany", "style": "Rauchbier Lager/Marzen", "founded": "1536", "notes": "Second great Bamberg rauchbier brewery; smokes its own malt; subtler smoke than Schlenkerla"},
    {"name": "Kolsch Beer Tradition (Fruh am Dom)", "lat": 50.9406, "lon": 6.9578, "country": "Germany", "style": "Kolsch", "founded": "1904", "notes": "Kolsch is legally protected to Cologne; light, crisp top-fermented ale served in 200ml Stangen glasses"},
    {"name": "Gaffel Kolsch Brewery", "lat": 50.9361, "lon": 6.9553, "country": "Germany", "style": "Kolsch", "founded": "1302", "notes": "One of oldest Kolsch breweries; Gaffel means fork, guild symbol; quintessential Cologne beer experience"},
    {"name": "Paulaner Brewery Munich", "lat": 48.1197, "lon": 11.5861, "country": "Germany", "style": "Helles/Salvator Doppelbock", "founded": "1634", "notes": "Paulaner monks invented Doppelbock (Salvator) for Lenten fasting; now major Oktoberfest brewery"},
    {"name": "Schneider Weisse (Kelheim)", "lat": 48.9133, "lon": 11.8750, "country": "Germany", "style": "Weizenbock/Hefeweizen", "founded": "1872", "notes": "Schneider Aventinus is the definitive Weizenbock; Georg Schneider saved wheat beer from extinction"},
    {"name": "Andechs Monastery Brewery", "lat": 47.9739, "lon": 11.1833, "country": "Germany", "style": "Doppelbock/Helles/Dunkel", "founded": "1455", "notes": "Benedictine hilltop monastery above Ammersee; pilgrimage destination for beer lovers; stunning views"},
    {"name": "Ayinger Brewery", "lat": 47.9667, "lon": 11.7833, "country": "Germany", "style": "Celebrator Doppelbock", "founded": "1878", "notes": "Village brewery south of Munich; Celebrator Doppelbock is a world classic with twin goat pendant"},
    {"name": "Einbecker Brauhaus", "lat": 51.8178, "lon": 9.8667, "country": "Germany", "style": "Bock Beer", "founded": "1378", "notes": "Birthplace of Bock beer; Einbeck brewers brought strong beer to Munich; name corrupted to Bock"},
    {"name": "Mahrs Brau (Bamberg)", "lat": 49.8878, "lon": 10.9008, "country": "Germany", "style": "Ungespundet Kellerbier", "founded": "1670", "notes": "Classic Franconian brewery; Ungespundet (unbunged) lager naturally carbonated; local favorite"},
    {"name": "Brauerei Heller-Trum (Schlenkerla)", "lat": 49.8908, "lon": 10.8836, "country": "Germany", "style": "Rauchbier Urbock/Weizen", "founded": "1678", "notes": "Historic tavern in half-timbered building; rauchbier tapped directly from oak casks in cellar"},
    {"name": "Klosterbrauerei Weltenburg", "lat": 48.8978, "lon": 11.8186, "country": "Germany", "style": "Barock Dunkel", "founded": "1050", "notes": "World's oldest monastic brewery; dramatic Danube Gorge setting; Barock Dunkel is superb dark lager"},
    {"name": "Bitburger Brewery", "lat": 49.9747, "lon": 6.5264, "country": "Germany", "style": "German Pilsner", "founded": "1817", "notes": "Germany's best-selling draft beer; pioneered German-style pilsner; Bitte ein Bit slogan is iconic"},
    {"name": "Jever Brewery", "lat": 53.5736, "lon": 7.9003, "country": "Germany", "style": "Jever Pilsener", "founded": "1848", "notes": "Extremely bitter, dry North German pilsner; Frisian heritage; cult following for its hoppy intensity"},
    {"name": "Aecht Schlenkerla Brewery Cellar", "lat": 49.8914, "lon": 10.8839, "country": "Germany", "style": "Rauchbier Marzen/Urbock", "founded": "1405", "notes": "Underground cellars beneath Bamberg; gravity-dispensed smoked lager; medieval atmosphere"},
    {"name": "Brauhaus Riegele (Augsburg)", "lat": 48.3625, "lon": 10.8842, "country": "Germany", "style": "Augsburger Herren Pils", "founded": "1386", "notes": "Swabian brewery with 600+ year heritage; family-owned for seven generations; innovative spirit"},
    {"name": "Rothaus Brewery (Black Forest)", "lat": 47.8219, "lon": 8.1647, "country": "Germany", "style": "Tannenzapfle Pilsner", "founded": "1791", "notes": "Black Forest state brewery; Tannenzapfle (Little Fir Cone) is a beloved regional pilsner"},
    {"name": "Spaten-Franziskaner Brewery", "lat": 48.1319, "lon": 11.5556, "country": "Germany", "style": "Spaten Helles/Oktoberfestbier", "founded": "1397", "notes": "Gabriel Sedlmayr II pioneered modern lager brewing and refrigeration; Oktoberfest original brewery"},
    {"name": "Hacker-Pschorr Brewery", "lat": 48.1353, "lon": 11.5739, "country": "Germany", "style": "Munich Helles/Dunkel", "founded": "1417", "notes": "Historic Munich brewery; Himmel der Bayern (Heaven of Bavarians) motto; classic Munich lagers"},
    {"name": "Lowenbrau Brewery", "lat": 48.1442, "lon": 11.5486, "country": "Germany", "style": "Munich Helles/Oktoberfest", "founded": "1383", "notes": "Lion brand is globally recognized; Lowenbraukeller beer hall; major Oktoberfest tent brewery"},
    {"name": "Erdinger Weissbrau", "lat": 48.3064, "lon": 11.9069, "country": "Germany", "style": "Weissbier/Dunkel Weizen", "founded": "1886", "notes": "World's largest wheat beer brewery; Erdinger Weissbier is Bavaria's wheat beer ambassador"},
    {"name": "Bamberg Brewery District", "lat": 49.8919, "lon": 10.8869, "country": "Germany", "style": "Rauchbier/Kellerbier/Lager", "founded": "1122", "notes": "UNESCO World Heritage city with 11 breweries; highest brewery density per capita in the world"},
    {"name": "Astra Brauerei (Hamburg)", "lat": 53.5511, "lon": 9.9625, "country": "Germany", "style": "Astra Urtyp Pilsner", "founded": "1909", "notes": "Hamburg's cult beer; heart-anchor logo; St. Pauli Reeperbahn culture; cheeky marketing"},
    {"name": "Becks Brewery (Bremen)", "lat": 53.0731, "lon": 8.8114, "country": "Germany", "style": "Beck's Pilsner", "founded": "1873", "notes": "Germany's most exported beer; Bremen ship key logo; major international brand since 19th century"},
    {"name": "Warsteiner Brewery", "lat": 51.4403, "lon": 8.3500, "country": "Germany", "style": "Premium Verum Pilsner", "founded": "1753", "notes": "Germany's largest privately owned brewery; Kaiserquelle spring water source; 270+ year heritage"},
]

# ===================================================================
# 3. CZECH & PILSNER HERITAGE (27 entries)
# ===================================================================
CZECH_PILSNER = [
    {"name": "Pilsner Urquell Brewery (Plzen)", "lat": 49.7486, "lon": 13.3867, "country": "Czech Republic", "style": "Original Pilsner Lager", "founded": "1842", "notes": "Birthplace of pilsner; Josef Groll brewed first golden lager here; changed world beer forever"},
    {"name": "Budejovicky Budvar (Ceske Budejovice)", "lat": 48.9706, "lon": 14.4642, "country": "Czech Republic", "style": "Czech Lager/Budvar", "founded": "1895", "notes": "Original Budweiser city; state-owned Czech lager; century-long trademark battle with Anheuser-Busch"},
    {"name": "U Fleku Brewpub (Prague)", "lat": 50.0789, "lon": 14.4175, "country": "Czech Republic", "style": "Dark Lager (Flekovske Tmave)", "founded": "1499", "notes": "Prague's oldest brewpub; single dark 13-degree lager served for 500+ years; cabaret shows"},
    {"name": "Strahov Monastery Brewery (Prague)", "lat": 50.0864, "lon": 14.3886, "country": "Czech Republic", "style": "St. Norbert Ales/Lagers", "founded": "1628", "notes": "Monastery brewery overlooking Prague Castle; revived in 2000; historic Premonstratensian order"},
    {"name": "Brevnov Monastery Brewery (Prague)", "lat": 50.0856, "lon": 14.3592, "country": "Czech Republic", "style": "Benedict Lager", "founded": "993", "notes": "Oldest monastery in Bohemia; Benedictine brewing tradition; modern craft revival"},
    {"name": "Pivovarsky Dum (Prague)", "lat": 50.0753, "lon": 14.4261, "country": "Czech Republic", "style": "Experimental Lagers", "founded": "1998", "notes": "Innovative Prague brewpub; banana beer, coffee lager, nettle beer; Czech craft pioneer"},
    {"name": "Zatec Hop Museum", "lat": 50.3272, "lon": 13.5461, "country": "Czech Republic", "style": "Saaz Hops Heritage", "founded": "2012", "notes": "Saaz (Zatec) hops are world's finest noble hops; museum in historic hop warehouse; UNESCO candidate"},
    {"name": "Kozel Brewery (Velke Popovice)", "lat": 49.9256, "lon": 14.5600, "country": "Czech Republic", "style": "Velkopopovicky Kozel", "founded": "1874", "notes": "Goat-branded Czech lager; live goat mascot at brewery; smooth, malty Czech dark and pale lagers"},
    {"name": "Staropramen Brewery (Prague)", "lat": 50.0706, "lon": 14.4028, "country": "Czech Republic", "style": "Czech Premium Lager", "founded": "1869", "notes": "Second largest Czech brewery; Smichov district landmark; classic Czech pale lager"},
    {"name": "Gambrinus Brewery (Plzen)", "lat": 49.7508, "lon": 13.3881, "country": "Czech Republic", "style": "Czech Lager", "founded": "1869", "notes": "Named for patron saint of beer; Czech Republic's best-selling beer; shares site with Pilsner Urquell"},
    {"name": "Bernard Brewery (Humpolec)", "lat": 49.5403, "lon": 15.3597, "country": "Czech Republic", "style": "Unpasteurized Czech Lager", "founded": "1597", "notes": "Premium unpasteurized lager; family-owned revival story; considered among Czech Republic's finest"},
    {"name": "Matuska Brewery (Broumy)", "lat": 49.8817, "lon": 13.8633, "country": "Czech Republic", "style": "IPA/Pale Ale/Imperial Stout", "founded": "2009", "notes": "Czech craft beer revolution leader; American-influenced IPAs meet Czech brewing precision"},
    {"name": "Pivovar Clock (Prague)", "lat": 50.0847, "lon": 14.4200, "country": "Czech Republic", "style": "Czech Pale Lager", "founded": "2015", "notes": "Modern Prague microbrewery; precise lager brewing in small batches; craft lager focus"},
    {"name": "Zlaty Bazant Brewery (Hurbanovo)", "lat": 47.8728, "lon": 18.1953, "country": "Slovakia", "style": "Slovak Golden Pheasant Lager", "founded": "1969", "notes": "Slovakia's most famous brewery; Golden Pheasant lager; shared Czech-Slovak brewing tradition"},
    {"name": "Krusovice Royal Brewery", "lat": 50.1800, "lon": 13.7714, "country": "Czech Republic", "style": "Czech Royal Lager", "founded": "1581", "notes": "Owned by Emperor Rudolf II in 1583; imperial brewing license; classic Bohemian lager"},
    {"name": "Lobkowicz Brewery (Vysocany)", "lat": 50.1103, "lon": 14.4881, "country": "Czech Republic", "style": "Czech Premium Lager", "founded": "1466", "notes": "Aristocratic Lobkowicz family brewery; historical Czech nobility brewing tradition"},
    {"name": "Svijansky Rychtarz Brewery", "lat": 50.6278, "lon": 15.1711, "country": "Czech Republic", "style": "Svijany Lager", "founded": "1564", "notes": "Popular Bohemian lager; unfiltered versions available; strong regional following in northern Bohemia"},
    {"name": "Cerna Hora Brewery", "lat": 49.4117, "lon": 16.5489, "country": "Czech Republic", "style": "Moravian Lager", "founded": "1298", "notes": "One of Czech Republic's oldest breweries; Moravian brewing tradition; 700+ year heritage"},
    {"name": "U Medvidku (Prague)", "lat": 50.0822, "lon": 14.4194, "country": "Czech Republic", "style": "X-Beer 33 (strongest Czech)", "founded": "1466", "notes": "Historic Prague beer hall; X-Beer 33 is world's strongest lager (12.6% ABV); Budvar on tap"},
    {"name": "Pivovar Falkon (Zatec)", "lat": 50.3267, "lon": 13.5450, "country": "Czech Republic", "style": "Hop-forward Czech Lager", "founded": "2014", "notes": "Craft brewery in hop capital Zatec; wet-hopped lagers using local Saaz hops; terroir focus"},
    {"name": "Pivovar Raven (Plzen)", "lat": 49.7478, "lon": 13.3800, "country": "Czech Republic", "style": "Czech-American Hybrid Ales", "founded": "2012", "notes": "Plzen craft brewery combining Czech lager tradition with American craft influences"},
    {"name": "Pivovar Nomad (Prague)", "lat": 50.0761, "lon": 14.4319, "country": "Czech Republic", "style": "IPA/Sour/Stout", "founded": "2016", "notes": "Gypsy brewery embodying new Czech craft wave; boundary-pushing styles from nomadic brewers"},
    {"name": "Regent Brewery (Trebon)", "lat": 49.0028, "lon": 14.7700, "country": "Czech Republic", "style": "Bohemia Regent Lager", "founded": "1379", "notes": "One of oldest Czech breweries; Renaissance brewery building; South Bohemian fish pond region"},
    {"name": "Jihlava Brewery", "lat": 49.3961, "lon": 15.5900, "country": "Czech Republic", "style": "Jezek Lager", "founded": "1860", "notes": "Moravian Highlands brewery; Jezek (Hedgehog) brand; traditional Czech-Moravian brewing"},
    {"name": "Opat Brewery (Broumov)", "lat": 50.5856, "lon": 16.3325, "country": "Czech Republic", "style": "Monastery-style Czech Lager", "founded": "2010", "notes": "Revived Benedictine brewing tradition; Broumov monastery setting; spiritual brewing heritage"},
    {"name": "Uhersky Brod Brewery", "lat": 49.0272, "lon": 17.6472, "country": "Czech Republic", "style": "Comenius Lager", "founded": "1895", "notes": "Moravian brewery named for famous scholar; traditional Moravian lager; southeastern Czech tradition"},
    {"name": "Nachod Brewery", "lat": 50.4158, "lon": 16.1628, "country": "Czech Republic", "style": "Primator Czech Lager", "founded": "1872", "notes": "Premium Czech lager with strong export presence; double bock and weizen variants; Eastern Bohemia gem"},
]

# ===================================================================
# 4. BRITISH PUB & ALE HERITAGE (28 entries)
# ===================================================================
BRITISH_PUB = [
    {"name": "Ye Olde Trip to Jerusalem (Nottingham)", "lat": 52.9489, "lon": -1.1556, "country": "England", "style": "Cask Bitter/Mild", "founded": "1189", "notes": "Claims to be England's oldest pub; carved into caves beneath Nottingham Castle; Crusader heritage"},
    {"name": "The Eagle and Child (Oxford)", "lat": 51.7547, "lon": -1.2611, "country": "England", "style": "Cask Ales", "founded": "1650", "notes": "Where Tolkien and C.S. Lewis met as The Inklings; literary pub history; classic Oxford experience"},
    {"name": "Ye Olde Cheshire Cheese (London)", "lat": 51.5147, "lon": -0.1069, "country": "England", "style": "Cask Ales/Porter", "founded": "1538", "notes": "Fleet Street literary pub; Dickens, Twain, Conan Doyle drank here; rebuilt after Great Fire of 1666"},
    {"name": "The Lamb and Flag (London)", "lat": 51.5122, "lon": -0.1264, "country": "England", "style": "Fuller's Cask Ales", "founded": "1623", "notes": "Covent Garden's oldest pub; John Dryden beaten outside in 1679; 'Bucket of Blood' nickname"},
    {"name": "Timothy Taylor's Brewery (Keighley)", "lat": 53.8681, "lon": -1.9117, "country": "England", "style": "Landlord Pale Ale", "founded": "1858", "notes": "Timothy Taylor's Landlord is the most-awarded cask ale; Madonna's reported favorite; Yorkshire gem"},
    {"name": "Fuller's Griffin Brewery (Chiswick)", "lat": 51.4858, "lon": -0.2594, "country": "England", "style": "London Pride/ESB", "founded": "1845", "notes": "London's last major traditional brewery; ESB defined the Extra Special Bitter style worldwide"},
    {"name": "Harvey's Brewery (Lewes)", "lat": 50.8722, "lon": 0.0106, "country": "England", "style": "Harvey's Sussex Best Bitter", "founded": "1790", "notes": "Iconic Sussex family brewery; Best Bitter is the benchmark English bitter; Victorian tower brewery"},
    {"name": "Samuel Smith Brewery (Tadcaster)", "lat": 53.8842, "lon": -1.2644, "country": "England", "style": "Old Brewery Bitter/Oatmeal Stout", "founded": "1758", "notes": "Yorkshire's oldest brewery; slate Yorkshire squares; horse-drawn deliveries; fiercely independent"},
    {"name": "Marston's Brewery (Burton upon Trent)", "lat": 52.8072, "lon": -1.6228, "country": "England", "style": "Pedigree/Burton Union System", "founded": "1834", "notes": "Last brewery using Burton Union fermentation system; Burton-on-Trent is the capital of British brewing"},
    {"name": "CAMRA Headquarters (St Albans)", "lat": 51.7500, "lon": -0.3361, "country": "England", "style": "Campaign for Real Ale", "founded": "1971", "notes": "Birthplace of the real ale movement; CAMRA saved cask ale from extinction; 170,000+ members"},
    {"name": "The Bow Bar (Edinburgh)", "lat": 55.9489, "lon": -3.1928, "country": "Scotland", "style": "Scottish Cask Ales", "founded": "1860", "notes": "Legendary Edinburgh cask ale pub; rotating Scottish and English real ales; multiple CAMRA awards"},
    {"name": "The Wenlock Arms (London)", "lat": 51.5333, "lon": -0.0908, "country": "England", "style": "Cask Ales/Real Cider", "founded": "1836", "notes": "Saved from demolition by community campaign; East London real ale institution; 10+ cask lines"},
    {"name": "Thornbridge Brewery (Bakewell)", "lat": 53.2150, "lon": -1.6778, "country": "England", "style": "Jaipur IPA/Lord Marples", "founded": "2005", "notes": "UK craft beer pioneer; Jaipur IPA redefined British IPA; stately home brewery in Peak District"},
    {"name": "The Olde Gate Inn (Brassington)", "lat": 53.0839, "lon": -1.6364, "country": "England", "style": "Cask Ales", "founded": "1616", "notes": "Timeless Derbyshire pub; no jukebox, no TV, no food after 2pm; pure traditional pub experience"},
    {"name": "Theakston Brewery (Masham)", "lat": 54.2231, "lon": -1.6556, "country": "England", "style": "Old Peculier", "founded": "1827", "notes": "Old Peculier is a legendary Yorkshire old ale; name from ecclesiastical peculier of Masham"},
    {"name": "The Cask Pub & Kitchen (London)", "lat": 51.5261, "lon": -0.1147, "country": "England", "style": "Rotating Craft/Cask", "founded": "2009", "notes": "London's pioneering craft beer bar; early champion of both cask and keg craft; Pimlico location"},
    {"name": "The Sheffield Tap", "lat": 53.3783, "lon": -1.4622, "country": "England", "style": "Craft Cask/Keg", "founded": "2009", "notes": "Restored Edwardian refreshment room in Sheffield station; Thornbridge showcase; architectural beauty"},
    {"name": "Hook Norton Brewery", "lat": 52.0094, "lon": -1.4878, "country": "England", "style": "Old Hooky/Hooky Bitter", "founded": "1849", "notes": "Victorian tower brewery still using steam engine; horse-drawn deliveries; Cotswolds gem"},
    {"name": "St Austell Brewery", "lat": 50.3400, "lon": -4.7892, "country": "England", "style": "Tribute Pale Ale/Proper Job IPA", "founded": "1851", "notes": "Cornwall's family brewery; Tribute is the West Country's favorite; Proper Job IPA is award-winning"},
    {"name": "Adnams Brewery (Southwold)", "lat": 52.3272, "lon": 1.6786, "country": "England", "style": "Broadside/Ghost Ship", "founded": "1872", "notes": "Suffolk coastal brewery; Broadside named for Battle of Sole Bay 1672; eco-conscious pioneer"},
    {"name": "The Kirkstall Bridge Inn (Leeds)", "lat": 53.8117, "lon": -1.5969, "country": "England", "style": "Cask Ales", "founded": "1867", "notes": "CAMRA Leeds POTY multiple times; 14 hand pumps of rotating cask ales; real fire; canalside"},
    {"name": "The Fat Cat (Norwich)", "lat": 52.6353, "lon": 1.2761, "country": "England", "style": "Cask Ales/Real Cider", "founded": "1991", "notes": "Multi-award-winning Norwich free house; 12+ cask ales; own Fat Cat Brewery; city's best pub"},
    {"name": "Batham's Brewery (Brierley Hill)", "lat": 52.4778, "lon": -2.1253, "country": "England", "style": "Batham's Best Bitter", "founded": "1877", "notes": "Black Country family brewery; Best Bitter is a West Midlands legend; The Vine pub is the tap house"},
    {"name": "The Marble Arch Inn (Manchester)", "lat": 53.4889, "lon": -2.2322, "country": "England", "style": "Manchester Bitter/Lagonda IPA", "founded": "1888", "notes": "Magnificent tiled Victorian pub; own Marble brewery; northern craft beer trailblazer"},
    {"name": "Greene King Brewery (Bury St Edmunds)", "lat": 52.2456, "lon": 0.7178, "country": "England", "style": "Abbot Ale/IPA", "founded": "1799", "notes": "Major British brewer; Old 5X strong ale aged in wooden vats; Westgate brewery is historic"},
    {"name": "Batemans Brewery (Wainfleet)", "lat": 53.1078, "lon": 0.2353, "country": "England", "style": "XXXB/Gold", "founded": "1874", "notes": "Good Honest Ales motto; family fought hostile takeover in 1986; Lincolnshire windmill logo"},
    {"name": "The Harp (London)", "lat": 51.5097, "lon": -0.1267, "country": "England", "style": "Cask Ales", "founded": "1850", "notes": "CAMRA National Pub of the Year 2010; Covent Garden narrow pub; 10 perfectly kept cask lines"},
    {"name": "Sharp's Brewery (Rock, Cornwall)", "lat": 50.5456, "lon": -4.9233, "country": "England", "style": "Doom Bar Amber Ale", "founded": "1994", "notes": "Doom Bar is UK's best-selling cask ale; named after Camel Estuary sandbar; Cornish surf culture"},
]

# ===================================================================
# 5. AMERICAN CRAFT BEER REVOLUTION (28 entries)
# ===================================================================
AMERICAN_CRAFT = [
    {"name": "Sierra Nevada Brewing (Chico)", "lat": 39.7242, "lon": -121.8153, "country": "USA", "style": "Pale Ale/Torpedo IPA", "founded": "1980", "notes": "Sierra Nevada Pale Ale started the American craft beer revolution; Ken Grossman's homebrew dream"},
    {"name": "Russian River Brewing (Santa Rosa)", "lat": 38.4408, "lon": -122.7089, "country": "USA", "style": "Pliny the Elder DIPA", "founded": "1997", "notes": "Pliny the Elder is the gold standard Double IPA; Pliny the Younger release causes annual frenzy"},
    {"name": "Hill Farmstead Brewery (Greensboro Bend)", "lat": 44.5872, "lon": -72.2978, "country": "USA", "style": "Abner DIPA/Edward Pale Ale", "founded": "2010", "notes": "Multiple times RateBeer's Best Brewery in World; remote Vermont hilltop farm setting; transcendent IPAs"},
    {"name": "Alchemist Brewery (Stowe)", "lat": 44.4656, "lon": -72.6869, "country": "USA", "style": "Heady Topper DIPA", "founded": "2003", "notes": "Heady Topper pioneered hazy IPA revolution; drink from the can instruction; Vermont cult classic"},
    {"name": "Tree House Brewing (Charlton)", "lat": 42.1361, "lon": -71.9897, "country": "USA", "style": "Julius/Haze NE IPA", "founded": "2011", "notes": "Epicenter of New England IPA movement; Julius is the haze benchmark; massive on-site-only lines"},
    {"name": "Other Half Brewing (Brooklyn)", "lat": 40.6735, "lon": -73.9986, "country": "USA", "style": "All Green Everything DIPA", "founded": "2014", "notes": "Brooklyn haze factory; DDH everything; Saturday can releases create block-long queues"},
    {"name": "Deschutes Brewery (Bend)", "lat": 44.0517, "lon": -121.3142, "country": "USA", "style": "Mirror Pond/Black Butte Porter", "founded": "1988", "notes": "Oregon craft pioneer; Mirror Pond is a perfect pale ale; Bend is America's beer town"},
    {"name": "Great Notion Brewing (Portland)", "lat": 45.5586, "lon": -122.6439, "country": "USA", "style": "Hazy IPA/Fruit Sours", "founded": "2016", "notes": "Portland haze and sour masters; smoothie-style fruited sours; James Beard nominated brewpub"},
    {"name": "Dogfish Head Brewery (Milton)", "lat": 38.7811, "lon": -75.3219, "country": "USA", "style": "60/90/120 Minute IPA", "founded": "1995", "notes": "Off-centered ales for off-centered people; continuous hopping invention; ancient ales revival"},
    {"name": "Bell's Brewery (Comstock)", "lat": 42.2694, "lon": -85.5081, "country": "USA", "style": "Two Hearted Ale", "founded": "1985", "notes": "Two Hearted Ale repeatedly voted America's best beer; Centennial single-hop masterpiece"},
    {"name": "Founders Brewing (Grand Rapids)", "lat": 42.9586, "lon": -85.6744, "country": "USA", "style": "KBS/All Day IPA/Breakfast Stout", "founded": "1997", "notes": "KBS (Kentucky Breakfast Stout) is legendary imperial stout; Grand Rapids is Beer City USA"},
    {"name": "Stone Brewing (Escondido)", "lat": 33.1156, "lon": -117.1206, "country": "USA", "style": "Arrogant Bastard/IPA", "founded": "1996", "notes": "Aggressive, bold West Coast IPAs; gargoyle logo; You're Not Worthy marketing; San Diego pioneer"},
    {"name": "Anchor Brewing (San Francisco)", "lat": 37.7669, "lon": -122.4003, "country": "USA", "style": "Anchor Steam/Liberty Ale", "founded": "1896", "notes": "Fritz Maytag saved it in 1965; Liberty Ale was first modern American IPA; sadly closed in 2023"},
    {"name": "New Belgium Brewing (Fort Collins)", "lat": 40.5936, "lon": -105.0681, "country": "USA", "style": "Fat Tire/Voodoo Ranger IPA", "founded": "1991", "notes": "Employee-owned B Corp; Fat Tire was inspired by cycling in Belgium; Tour de Fat festival"},
    {"name": "Wicked Weed Brewing (Asheville)", "lat": 35.5926, "lon": -82.5522, "country": "USA", "style": "Pernicious IPA/Sour Program", "founded": "2012", "notes": "Asheville craft scene leader; massive sour/wild program in Funkatorium; Southern craft capital"},
    {"name": "Burial Beer Co (Asheville)", "lat": 35.5814, "lon": -82.5511, "country": "USA", "style": "Skillet Donut Stout/IPAs", "founded": "2013", "notes": "Dark, artistic Asheville brewery; death-themed branding; pastry stouts and hazy IPAs"},
    {"name": "Trillium Brewing (Boston)", "lat": 42.3481, "lon": -71.0400, "country": "USA", "style": "Congress Street IPA", "founded": "2013", "notes": "Boston's NE IPA flagship; Congress Street is a haze standard; Fort Point waterfront location"},
    {"name": "Firestone Walker (Paso Robles)", "lat": 35.6264, "lon": -120.6819, "country": "USA", "style": "Union Jack IPA/Parabola", "founded": "1996", "notes": "Wine country brewery; British-American hybrid approach; barrel-aged program is world-class"},
    {"name": "The Bruery (Placentia)", "lat": 33.8814, "lon": -117.8531, "country": "USA", "style": "Black Tuesday Imperial Stout", "founded": "2008", "notes": "Belgian-inspired barrel-aged specialists; Black Tuesday annual release is a beer event"},
    {"name": "AleSmith Brewing (San Diego)", "lat": 32.8333, "lon": -117.1133, "country": "USA", "style": "Speedway Stout", "founded": "1995", "notes": "Speedway Stout (Vietnamese coffee) is an imperial stout legend; San Diego craft cornerstone"},
    {"name": "Side Project Brewing (Maplewood)", "lat": 38.6119, "lon": -90.3256, "country": "USA", "style": "Derivation Series", "founded": "2014", "notes": "Ultra-premium barrel-aged stouts and wilds; Derivation series trades for hundreds of dollars"},
    {"name": "Toppling Goliath (Decorah)", "lat": 43.3022, "lon": -91.7897, "country": "USA", "style": "King Sue/PseudoSue", "founded": "2009", "notes": "Small Iowa brewery with massive reputation; King Sue DIPA is liquid gold; Mornin' Delight stout"},
    {"name": "Cigar City Brewing (Tampa)", "lat": 27.9597, "lon": -82.5081, "country": "USA", "style": "Jai Alai IPA/Hunahpu", "founded": "2009", "notes": "Tampa's craft flagship; Jai Alai IPA is Florida's beer; Hunahpu's Day imperial stout festival"},
    {"name": "Bissell Brothers Brewing (Portland ME)", "lat": 43.6692, "lon": -70.2567, "country": "USA", "style": "Substance Ale/Lux", "founded": "2013", "notes": "Maine NE IPA scene leaders; Substance is the daily haze driver; Industrial Way beer district"},
    {"name": "Modern Times Beer (San Diego)", "lat": 32.7372, "lon": -117.1639, "country": "USA", "style": "Fortunate Islands/Black House", "founded": "2013", "notes": "Utopian-socialist themed brewery; in-house coffee roasting and fermentation; employee-owned"},
    {"name": "Odell Brewing (Fort Collins)", "lat": 40.5894, "lon": -105.0631, "country": "USA", "style": "IPA/90 Shilling", "founded": "1989", "notes": "Colorado craft pioneer; employee-owned ESOP; beautiful taproom with mountain views"},
    {"name": "Half Acre Beer (Chicago)", "lat": 41.9681, "lon": -87.6831, "country": "USA", "style": "Daisy Cutter Pale Ale", "founded": "2006", "notes": "Chicago craft stalwart; Daisy Cutter is a West Coast pale ale icon in the Midwest; Balmoral taproom"},
    {"name": "Monkish Brewing (Torrance)", "lat": 33.8361, "lon": -118.3267, "country": "USA", "style": "Foggy Window DIPA", "founded": "2012", "notes": "SoCal haze kings; Belgian-meets-NE IPA approach; can releases sell out in minutes online"},
]

# ===================================================================
# 6. JAPANESE CRAFT BEER (27 entries)
# ===================================================================
JAPANESE_CRAFT = [
    {"name": "Yebisu Beer Museum (Tokyo)", "lat": 35.6428, "lon": 139.7133, "country": "Japan", "style": "Yebisu Premium Lager", "founded": "1890", "notes": "Historic Tokyo beer district named after the brand; museum traces Japanese brewing from Meiji era"},
    {"name": "Hitachino Nest (Kiuchi Brewery, Naka)", "lat": 36.4572, "lon": 140.4811, "country": "Japan", "style": "White Ale/Red Rice Ale", "founded": "1823", "notes": "Originally a sake brewery since 1823; owl logo; White Ale is Japan's most recognized craft export"},
    {"name": "Baird Brewing (Shuzenji)", "lat": 34.9750, "lon": 138.9278, "country": "Japan", "style": "Rising Sun Pale Ale", "founded": "2000", "notes": "American-Japanese craft pioneer; Bryan Baird's taproom empire; Izu Peninsula craft destination"},
    {"name": "Yo-Ho Brewing (Karuizawa)", "lat": 36.3478, "lon": 138.5972, "country": "Japan", "style": "Yona Yona Ale/Indo no Aooni", "founded": "1997", "notes": "Japan's craft beer leader by volume; Yona Yona Ale introduced American Pale Ale to Japan"},
    {"name": "Spring Valley Brewery (Yokohama)", "lat": 35.4478, "lon": 139.6453, "country": "Japan", "style": "496/Copeland", "founded": "1870", "notes": "Japan's first brewery; William Copeland founded it for Yokohama's foreign community; revived by Kirin"},
    {"name": "Coedo Brewery (Kawagoe)", "lat": 35.9244, "lon": 139.4856, "country": "Japan", "style": "Beniaka Sweet Potato Lager", "founded": "1996", "notes": "Uses local Kawagoe sweet potatoes; Beniaka is a unique amber lager; Little Edo historic town"},
    {"name": "Minoh Beer (Osaka)", "lat": 34.8367, "lon": 135.4703, "country": "Japan", "style": "W-IPA/Stout/Weizen", "founded": "1997", "notes": "Sisters brewery; W-IPA is a double IPA pioneer in Japan; Minoh waterfall area; multiple gold medals"},
    {"name": "Shiga Kogen Beer (Nagano)", "lat": 36.7950, "lon": 138.5228, "country": "Japan", "style": "Miyama Blonde/IPA/House IPA", "founded": "2004", "notes": "Ski resort brewery at high altitude; uses local rice and hops; fresh mountain water source"},
    {"name": "Isekadoya Brewery (Ise)", "lat": 34.4861, "lon": 136.7083, "country": "Japan", "style": "Pale Ale/Stout/Hime White", "founded": "1997", "notes": "Near Ise Grand Shrine; traditional Japanese aesthetics meet craft beer; popular with pilgrims"},
    {"name": "Sankt Gallen Brewery (Atsugi)", "lat": 35.4328, "lon": 139.3647, "country": "Japan", "style": "Sweet Vanilla Stout/Yokohama XPA", "founded": "1997", "notes": "Named after Swiss monastery; first legal Japanese microbrewery after 1994 deregulation"},
    {"name": "Ise Kadoya Beer Hall (Tokyo)", "lat": 35.6631, "lon": 139.7322, "country": "Japan", "style": "Pale Ale/Dark Lager", "founded": "2007", "notes": "Tokyo outpost of Ise brewery; Shinjuku location; craft beer izakaya concept; Ise shrine theme"},
    {"name": "TY Harbor Brewery (Tokyo)", "lat": 35.6233, "lon": 139.7472, "country": "Japan", "style": "American-style Craft Ales", "founded": "1997", "notes": "Waterfront Tokyo brewpub in Tennoz Isle; American craft approach in converted warehouse"},
    {"name": "Kyoto Brewing Co.", "lat": 35.0050, "lon": 135.7400, "country": "Japan", "style": "Ichigo Ichie Saison/Belgian-Japanese", "founded": "2015", "notes": "Belgian-American-Japanese trio founded Kyoto's first craft brewery; Belgian-inspired Japanese ales"},
    {"name": "Brimmer Brewing (Kawasaki)", "lat": 35.5228, "lon": 139.6989, "country": "Japan", "style": "Pale Ale/Porter/IPA", "founded": "2012", "notes": "American expat Scott Brimmer's brewery; bridge between US and Japanese craft scenes"},
    {"name": "Doppo Beer (Okayama)", "lat": 34.6614, "lon": 133.9175, "country": "Japan", "style": "Muscat Ale/Peach Lager", "founded": "1995", "notes": "Uses local Okayama fruit (white peach, muscat grape); German lager techniques with Japanese fruit"},
    {"name": "Otaru Beer (Hokkaido)", "lat": 43.1908, "lon": 140.9944, "country": "Japan", "style": "German-style Pilsner/Dunkel", "founded": "1995", "notes": "German brewmaster in Hokkaido; authentic German lagers with pristine Hokkaido water; canal district"},
    {"name": "Echigo Beer (Niigata)", "lat": 37.9161, "lon": 139.0364, "country": "Japan", "style": "Koshihikari Rice Lager", "founded": "1994", "notes": "Japan's first post-deregulation brewpub; uses premium Koshihikari rice; sake-country brewing"},
    {"name": "Fujizakura Heights Beer", "lat": 35.4733, "lon": 138.7956, "country": "Japan", "style": "Weizen/Rauch/Pilsner", "founded": "1998", "notes": "Brewed at foot of Mount Fuji; German-style lagers with Fuji spring water; scenic brewery"},
    {"name": "Swan Lake Beer (Niigata)", "lat": 37.7833, "lon": 139.1833, "country": "Japan", "style": "Amber Ale/Porter", "founded": "1997", "notes": "World Beer Cup gold winners; Agano area near swan migration lakes; quality-focused family brewery"},
    {"name": "Thrash Zone (Yokohama)", "lat": 35.4444, "lon": 139.6319, "country": "Japan", "style": "Hazy IPA/Pale Ale", "founded": "2015", "notes": "Heavy metal themed Yokohama nanobrewery; American-influenced hop-forward beers; cult following"},
    {"name": "DevilCraft (Tokyo)", "lat": 35.6967, "lon": 139.7744, "country": "Japan", "style": "Chicago Deep Dish & Craft Beer", "founded": "2011", "notes": "American-run Tokyo craft beer bar; rotating Japanese and imported craft taps; Kanda location"},
    {"name": "Ushitora Brewery (Tokyo)", "lat": 35.7489, "lon": 139.8128, "country": "Japan", "style": "Hoppy English Bitter/Saison", "founded": "2015", "notes": "Shimokitazawa brewery blending English cask traditions with Japanese precision; tiny batch focus"},
    {"name": "Nara Brewing Co.", "lat": 34.6817, "lon": 135.8050, "country": "Japan", "style": "Shika IPA/Sake Yeast Pale", "founded": "2018", "notes": "Brewing near ancient temples; deer (shika) branding; experiments with sake yeast in beer"},
    {"name": "North Island Beer (Sapporo)", "lat": 43.0639, "lon": 141.3544, "country": "Japan", "style": "Pilsner/IPA/Stout", "founded": "2003", "notes": "Hokkaido craft pioneer; classic European and American styles with Hokkaido ingredients"},
    {"name": "Hideji Beer (Miyazaki)", "lat": 31.9111, "lon": 131.4239, "country": "Japan", "style": "Sun & Moon Lager/Pale Ale", "founded": "1996", "notes": "Kyushu tropical-climate brewery; unique southern Japanese craft identity; mango and citrus beers"},
    {"name": "Iwate Kura Beer (Ichinoseki)", "lat": 38.9344, "lon": 141.1267, "country": "Japan", "style": "Oyster Stout/Red Ale", "founded": "1995", "notes": "Tohoku brewery using local oysters in stout; traditional kura (storehouse) building; regional pride"},
    {"name": "Helios Craft Beer (Okinawa)", "lat": 26.3344, "lon": 127.7539, "country": "Japan", "style": "Goya Dry/Shisa IPA", "founded": "1996", "notes": "Okinawan craft brewery; uses bitter melon (goya); tropical island brewing; unique subtropical terroir"},
]

# ===================================================================
# 7. ANCIENT BREWING HISTORY (26 entries)
# ===================================================================
ANCIENT_BREWING = [
    {"name": "Godin Tepe (Zagros Mountains)", "lat": 34.4500, "lon": 48.0667, "country": "Iran", "style": "Earliest Barley Beer Evidence", "founded": "c. 3500 BCE", "notes": "Chemical residue of barley beer found in pottery; among earliest direct evidence of beer brewing"},
    {"name": "Raqefet Cave (Mount Carmel)", "lat": 32.6833, "lon": 35.0333, "country": "Israel", "style": "Natufian Wheat-Barley Beer", "founded": "c. 11000 BCE", "notes": "Oldest known beer production site; Natufian people brewed before agriculture; ritual funeral feasts"},
    {"name": "Jiahu (Henan Province)", "lat": 33.6167, "lon": 113.6667, "country": "China", "style": "Rice-Honey-Fruit Ferment", "founded": "c. 7000 BCE", "notes": "Residue analysis shows fermented rice, honey, hawthorn fruit; among world's oldest fermented beverages"},
    {"name": "Temple of Ninkasi (Ur/Nasiriyah)", "lat": 30.9625, "lon": 46.1028, "country": "Iraq", "style": "Sumerian Beer (Kas)", "founded": "c. 3900 BCE", "notes": "Hymn to Ninkasi is oldest beer recipe; Sumerian goddess of beer; beer was daily bread of Mesopotamia"},
    {"name": "Hierakonpolis (Nekhen)", "lat": 25.0975, "lon": 32.7783, "country": "Egypt", "style": "Egyptian Emmer Wheat Beer", "founded": "c. 3500 BCE", "notes": "Large-scale predynastic Egyptian brewery; beer was essential worker payment; 300 gallons/day capacity"},
    {"name": "Workers Village at Giza Pyramids", "lat": 29.9753, "lon": 31.1325, "country": "Egypt", "style": "Pyramid Builder's Beer", "founded": "c. 2560 BCE", "notes": "Brewery fed pyramid builders; workers received 4-5 liters daily; beer was nutritional staple"},
    {"name": "Tall Bazi (Euphrates Valley)", "lat": 35.8833, "lon": 38.5667, "country": "Syria", "style": "Bronze Age Barley Beer", "founded": "c. 1400 BCE", "notes": "3400-year-old beer jugs with barley residue; Mesopotamian brewing technology spread along Euphrates"},
    {"name": "Ebla (Tell Mardikh)", "lat": 35.7983, "lon": 36.7950, "country": "Syria", "style": "Palace Brewery Beer", "founded": "c. 2400 BCE", "notes": "Cuneiform tablets describe palace brewery producing multiple beer styles; city consumed vast quantities"},
    {"name": "Abydos Royal Brewery", "lat": 26.1850, "lon": 31.9197, "country": "Egypt", "style": "Ritual/Funerary Beer", "founded": "c. 3000 BCE", "notes": "World's oldest known large-scale brewery; produced beer for royal rituals honoring early pharaohs"},
    {"name": "Teotihuacan Pulque Brewing", "lat": 19.6925, "lon": -98.8439, "country": "Mexico", "style": "Pulque (Agave Beer)", "founded": "c. 200 CE", "notes": "Mesoamerican fermented agave sap; Aztec goddess Mayahuel; pre-Columbian beer equivalent"},
    {"name": "Chavin de Huantar Chicha Brewery", "lat": -9.5931, "lon": -77.1769, "country": "Peru", "style": "Chicha de Jora (Corn Beer)", "founded": "c. 1000 BCE", "notes": "Andean corn beer brewed for ritual feasts; women chewed corn to start fermentation; 3000+ year tradition"},
    {"name": "Cerro Baul Wari Brewery", "lat": -17.0794, "lon": -70.8539, "country": "Peru", "style": "Chicha/Molle Berry Beer", "founded": "c. 600 CE", "notes": "Wari Empire hilltop brewery; molle berry chicha for elite feasts; brewery burned in farewell ritual"},
    {"name": "Great Zimbabwe Brewing Complex", "lat": -20.2675, "lon": 30.9339, "country": "Zimbabwe", "style": "Sorghum/Millet Beer", "founded": "c. 1100 CE", "notes": "Large-scale sorghum beer production for the Shona kingdom; communal brewing pits; ritual importance"},
    {"name": "Skara Brae (Orkney)", "lat": 59.0489, "lon": -3.3417, "country": "Scotland", "style": "Neolithic Heather Ale", "founded": "c. 3100 BCE", "notes": "Evidence of fermented beverages at Neolithic village; possible heather ale or mead-beer hybrid"},
    {"name": "Egtved Girl Burial (Jutland)", "lat": 55.6167, "lon": 9.3000, "country": "Denmark", "style": "Nordic Bronze Age Grog", "founded": "c. 1370 BCE", "notes": "Birch bark bucket with wheat beer, honey, bog myrtle, cranberry; Nordic grog recipe preserved in burial"},
    {"name": "Hochdorf Chieftain's Grave", "lat": 48.8494, "lon": 9.0111, "country": "Germany", "style": "Celtic Mead-Beer", "founded": "c. 530 BCE", "notes": "500L bronze cauldron with mead residue; Iron Age Celtic drinking culture; elite warrior burial feast"},
    {"name": "Vindolanda Roman Fort", "lat": 55.0094, "lon": -2.3606, "country": "England", "style": "Roman Cervesa", "founded": "c. 85 CE", "notes": "Vindolanda tablets mention beer (cervesa) supplies for Roman garrison; soldiers drank beer on Hadrian's Wall"},
    {"name": "Bryggen Wharf (Bergen)", "lat": 60.3975, "lon": 5.3242, "country": "Norway", "style": "Viking/Hanseatic Ale", "founded": "c. 1070 CE", "notes": "Medieval Hanseatic trading wharf; beer was primary Viking and medieval Norwegian beverage"},
    {"name": "Birka Viking Settlement", "lat": 59.3331, "lon": 17.5458, "country": "Sweden", "style": "Viking Mead-Ale", "founded": "c. 750 CE", "notes": "Major Viking trading post; imported hops and malt; brewing equipment found in excavations"},
    {"name": "Karakorum (Mongol Capital)", "lat": 47.1972, "lon": 102.8217, "country": "Mongolia", "style": "Airag/Kumis (Mare's Milk Beer)", "founded": "c. 1220 CE", "notes": "Mongol capital had a silver fountain dispensing fermented mare's milk; William of Rubruck's account"},
    {"name": "Dogon Cliff Breweries (Bandiagara)", "lat": 14.3500, "lon": -3.6167, "country": "Mali", "style": "Dolo (Millet Beer)", "founded": "c. 1400 CE", "notes": "Dogon people brew dolo millet beer in cliff villages; communal brewing by women; ritual significance"},
    {"name": "Amarna Royal Brewery", "lat": 27.6472, "lon": 30.8986, "country": "Egypt", "style": "Pharaonic Wheat-Barley Beer", "founded": "c. 1350 BCE", "notes": "Akhenaten's capital brewery; industrial-scale production for royal court; dated bread-beer loaves found"},
    {"name": "Uruk (Warka) Brewery District", "lat": 31.3228, "lon": 45.6369, "country": "Iraq", "style": "Sumerian Temple Beer", "founded": "c. 4000 BCE", "notes": "World's first city had temple breweries; beer ration tablets; Inanna temple offerings included beer"},
    {"name": "Deir el-Medina Workers Village", "lat": 25.7278, "lon": 32.6017, "country": "Egypt", "style": "Workers' Daily Beer Ration", "founded": "c. 1500 BCE", "notes": "New Kingdom tomb builders received daily beer rations; household brewing documented on ostraca"},
    {"name": "Qiaotou (Zhejiang Province)", "lat": 29.0333, "lon": 120.9000, "country": "China", "style": "Neolithic Rice Beer", "founded": "c. 7000 BCE", "notes": "Rice-based fermented beverage residue found in painted pottery; early Yangtze Delta brewing culture"},
    {"name": "Kvass Tradition Origin (Kyiv)", "lat": 50.4501, "lon": 30.5234, "country": "Ukraine", "style": "Slavic Bread Beer (Kvass)", "founded": "c. 996 CE", "notes": "Prince Vladimir I distributed kvass at baptism feast; Slavic bread-fermented low-alcohol beer tradition"},
]

# ===================================================================
# 8. HOP GROWING REGIONS (26 entries)
# ===================================================================
HOP_REGIONS = [
    {"name": "Hallertau (Bavaria)", "lat": 48.5833, "lon": 11.7500, "country": "Germany", "style": "Hallertauer Mittelfruh/Tradition", "founded": "c. 736 CE", "notes": "World's largest hop growing region; noble Hallertauer hops define German lager character; 2,400+ farms"},
    {"name": "Yakima Valley (Washington)", "lat": 46.6021, "lon": -120.5059, "country": "USA", "style": "Cascade/Citra/Simcoe/Mosaic", "founded": "1868", "notes": "Produces 75% of US hops; birthplace of Cascade hop; arid irrigated valley; American craft revolution fuel"},
    {"name": "Zatec / Saaz (Bohemia)", "lat": 50.3272, "lon": 13.5461, "country": "Czech Republic", "style": "Saaz Noble Hops", "founded": "c. 1004 CE", "notes": "Saaz hops are the soul of pilsner; noble hop with spicy, herbal, earthy character; UNESCO candidate"},
    {"name": "East Kent (Canterbury/Faversham)", "lat": 51.3178, "lon": 0.8919, "country": "England", "style": "East Kent Goldings", "founded": "c. 1520", "notes": "East Kent Goldings are England's finest hops; gentle floral, honey, spice character; cask ale essential"},
    {"name": "Nelson/Tasman Region", "lat": -41.2706, "lon": 173.2840, "country": "New Zealand", "style": "Nelson Sauvin/Motueka/Riwaka", "founded": "1842", "notes": "Nelson Sauvin revolutionized NZ hops with Sauvignon Blanc-like character; Pacific hop frontier"},
    {"name": "Tettnang (Lake Constance)", "lat": 47.6694, "lon": 9.5931, "country": "Germany", "style": "Tettnanger Noble Hops", "founded": "c. 1150 CE", "notes": "Noble hop variety from Lake Constance region; delicate spicy-herbal aroma; premium lager hops"},
    {"name": "Spalt (Franconia)", "lat": 49.1750, "lon": 10.9250, "country": "Germany", "style": "Spalter Noble Hops", "founded": "c. 1341 CE", "notes": "Fourth German noble hop; Franconian specialty; subtle, refined aroma; certified geographic origin"},
    {"name": "Willamette Valley (Oregon)", "lat": 44.7833, "lon": -123.0833, "country": "USA", "style": "Willamette/Crystal/Sterling", "founded": "1880s", "notes": "Oregon's hop heartland; Willamette hop is a Fuggle descendant; fertile valley floor; sustainable farming"},
    {"name": "Herefordshire/Worcestershire", "lat": 52.0567, "lon": -2.7167, "country": "England", "style": "Fuggle/First Gold/Bramling Cross", "founded": "c. 1600", "notes": "West Midlands hop country; Fuggle hop bred here in 1875; rolling green hop gardens; oast houses"},
    {"name": "Tasmania (Bushy Park)", "lat": -42.7000, "lon": 146.9000, "country": "Australia", "style": "Galaxy/Enigma/Vic Secret", "founded": "1822", "notes": "Galaxy hop transformed Aussie/American craft; tropical passionfruit character; cool-climate terroir"},
    {"name": "Elbe-Saale Region (Saxony-Anhalt)", "lat": 51.5833, "lon": 11.9667, "country": "Germany", "style": "Magnum/Northern Brewer", "founded": "c. 1200 CE", "notes": "Former East German hop region revived post-reunification; continental climate; historic trade routes"},
    {"name": "Styria / Savinjska Valley", "lat": 46.2333, "lon": 14.8333, "country": "Slovenia", "style": "Styrian Goldings (Aurora/Celeia)", "founded": "c. 1876", "notes": "Styrian Goldings are actually Fuggle cuttings transplanted from England; earthy, spicy Continental character"},
    {"name": "Alsace (Bas-Rhin)", "lat": 48.7167, "lon": 7.3500, "country": "France", "style": "Strisselspalt/Aramis", "founded": "c. 1500", "notes": "France's main hop region; Strisselspalt is a noble-like hop with delicate floral aroma; brasserie culture"},
    {"name": "Poperinge (West Flanders)", "lat": 50.8553, "lon": 2.7261, "country": "Belgium", "style": "Belgian Hops/Tradition", "founded": "c. 1100 CE", "notes": "Belgium's hop capital; annual Hop Festival; hop museum; hops for abbey ales and lambics"},
    {"name": "Galena County (Idaho)", "lat": 43.8667, "lon": -114.2333, "country": "USA", "style": "Galena/Idaho 7", "founded": "1900s", "notes": "Idaho hop production growing rapidly; Idaho 7 hop is a new-wave American variety; mountain terroir"},
    {"name": "South Africa (George/Outeniqua)", "lat": -33.9667, "lon": 22.4500, "country": "South Africa", "style": "Southern Promise/African Queen", "founded": "1980s", "notes": "Only hop growing region in Africa; African Queen hop has unique tropical-stone fruit character"},
    {"name": "Lublin Region (Poland)", "lat": 51.2500, "lon": 22.5667, "country": "Poland", "style": "Lublin/Lubelski Hops", "founded": "c. 1600", "notes": "Polish noble-type hop; lavender and magnolia notes; used in Polish and Czech-style lagers"},
    {"name": "Xinhui (Guangdong Province)", "lat": 22.4586, "lon": 113.0322, "country": "China", "style": "Chinese Hops (Qingdao/Marco Polo)", "founded": "1900s", "notes": "China is world's second-largest hop grower; Gansu and Xinjiang provinces are primary regions"},
    {"name": "Waikato/Bay of Plenty (North Island)", "lat": -37.7833, "lon": 175.2833, "country": "New Zealand", "style": "Pacific Jade/Rakau", "founded": "1900s", "notes": "North Island hop growing complements Nelson; subtropical varieties; Pacific Jade is distinctive"},
    {"name": "Ribnica/Petrina (Dolenjska)", "lat": 45.7333, "lon": 14.7333, "country": "Slovenia", "style": "Bobek/Dana", "founded": "c. 1900", "notes": "Lower Carniola hop district; complements Styrian production; continental Slovenian hop heritage"},
    {"name": "Tochigi Prefecture", "lat": 36.5667, "lon": 139.8833, "country": "Japan", "style": "Sorachi Ace/Shinshuwase", "founded": "1870s", "notes": "Sorachi Ace hop created by Sapporo brewery; lemongrass and dill character; cult craft hop worldwide"},
    {"name": "Zhangye (Gansu Province)", "lat": 38.9333, "lon": 100.4500, "country": "China", "style": "Chinese Hops (bulk varieties)", "founded": "1960s", "notes": "Gansu Province is China's largest hop region; continental climate; primarily alpha-acid varieties"},
    {"name": "Smarhon (Grodno Region)", "lat": 54.4833, "lon": 26.4000, "country": "Belarus", "style": "Eastern European Traditional Hops", "founded": "c. 1800", "notes": "Historic Eastern European hop region; supplied Soviet-era breweries; traditional varieties"},
    {"name": "West Coast Tasmania (Scottsdale)", "lat": -41.1500, "lon": 147.5167, "country": "Australia", "style": "Ella/Topaz/Summer", "founded": "1990s", "notes": "Tasmanian hop breeding produces world-class varieties; Ella hop has floral star anise character"},
    {"name": "Michigan Hop Country (Grand Traverse)", "lat": 44.7631, "lon": -85.6206, "country": "USA", "style": "Revival Heritage Hops", "founded": "1840s", "notes": "Michigan was once America's top hop state before Prohibition; revival movement growing heritage varieties"},
    {"name": "Aroostook County (Maine)", "lat": 46.8500, "lon": -68.0167, "country": "USA", "style": "Northeast Heritage Hops", "founded": "2010s", "notes": "New England hop farming renaissance; local-sourced fresh hop beers; cold-climate hop varieties"},
]

# ===================================================================
# 9. OKTOBERFEST & BEER FESTIVALS (27 entries)
# ===================================================================
BEER_FESTIVALS = [
    {"name": "Munich Oktoberfest (Theresienwiese)", "lat": 48.1313, "lon": 11.5497, "country": "Germany", "style": "Oktoberfest Marzen/Festbier", "founded": "1810", "notes": "World's largest beer festival; 6 million visitors; 14 tents; only 6 Munich breweries served; lederhosen required attitude"},
    {"name": "Great American Beer Festival (Denver)", "lat": 39.7422, "lon": -104.9875, "country": "USA", "style": "All American Craft Styles", "founded": "1982", "notes": "GABF is American craft beer's Olympics; 2,000+ breweries compete; 4,000+ beers poured over 3 days"},
    {"name": "Great British Beer Festival (London)", "lat": 51.4975, "lon": -0.1357, "country": "England", "style": "Cask Ales/Real Cider", "founded": "1977", "notes": "CAMRA's flagship event at Olympia; 900+ real ales; Champion Beer of Britain awards; cask ale paradise"},
    {"name": "Belgian Beer Weekend (Brussels)", "lat": 50.8467, "lon": 4.3525, "country": "Belgium", "style": "All Belgian Styles", "founded": "1998", "notes": "Grand Place transformed into beer paradise; 50+ Belgian breweries; UNESCO Intangible Heritage backdrop"},
    {"name": "Pilsner Fest (Plzen)", "lat": 49.7478, "lon": 13.3786, "country": "Czech Republic", "style": "Czech Pilsner/Lagers", "founded": "1992", "notes": "Annual celebration of pilsner's birthplace; Pilsner Urquell brewery courtyard; traditional brass bands"},
    {"name": "Stockholm Beer & Whisky Festival", "lat": 59.3250, "lon": 18.0714, "country": "Sweden", "style": "Nordic Craft/International", "founded": "1992", "notes": "Scandinavia's largest beer festival; 100+ exhibitors; Nordic craft beer showcase at Nacka Strand"},
    {"name": "Mondial de la Biere (Montreal)", "lat": 45.5017, "lon": -73.5673, "country": "Canada", "style": "International Craft", "founded": "1994", "notes": "Major North American beer festival; 600+ beers from 20+ countries; Old Montreal setting"},
    {"name": "Oregon Brewers Festival (Portland)", "lat": 45.5106, "lon": -122.6708, "country": "USA", "style": "Pacific Northwest Craft", "founded": "1988", "notes": "One of America's largest outdoor festivals; Tom McCall Waterfront Park; 80+ craft breweries; free entry"},
    {"name": "Cannstatter Volksfest (Stuttgart)", "lat": 48.7917, "lon": 9.2122, "country": "Germany", "style": "Swabian Festbier", "founded": "1818", "notes": "Stuttgart's answer to Oktoberfest; almost as large; fruit column tradition; Swabian beer culture"},
    {"name": "Zythos Beer Festival (Belgium)", "lat": 51.0500, "lon": 3.7250, "country": "Belgium", "style": "All Belgian Craft Styles", "founded": "2004", "notes": "Belgian beer consumer organization's festival; 100+ craft breweries; less touristy than Brussels events"},
    {"name": "Copenhagen Beer Celebration", "lat": 55.6761, "lon": 12.5683, "country": "Denmark", "style": "Nordic/International Craft", "founded": "2014", "notes": "Mikkeller-founded festival; invite-only top-tier breweries; Scandinavian craft elite gathering"},
    {"name": "Barcelona Beer Festival", "lat": 41.3851, "lon": 2.1734, "country": "Spain", "style": "Mediterranean/International Craft", "founded": "2012", "notes": "Spain's largest craft beer festival; 400+ beers; La Farga venue; Mediterranean craft beer boom showcase"},
    {"name": "Beervana (Wellington)", "lat": -41.2865, "lon": 174.7762, "country": "New Zealand", "style": "NZ/Australian Craft", "founded": "2009", "notes": "New Zealand's premier craft beer festival; Westpac Stadium; 50+ breweries; Kiwi hop showcase"},
    {"name": "Qingdao International Beer Festival", "lat": 36.0671, "lon": 120.3826, "country": "China", "style": "Tsingtao/International Lagers", "founded": "1991", "notes": "Asia's largest beer festival; Tsingtao Brewery heritage; German colonial brewing history; 2 weeks"},
    {"name": "Blumenau Oktoberfest (Brazil)", "lat": -26.9194, "lon": -49.0661, "country": "Brazil", "style": "German-Brazilian Lagers", "founded": "1984", "notes": "World's second-largest Oktoberfest; German immigrant heritage in Santa Catarina; 600,000+ visitors"},
    {"name": "Helsinki Beer Festival", "lat": 60.1699, "lon": 24.9384, "country": "Finland", "style": "Finnish/Nordic Craft", "founded": "2006", "notes": "Finnish craft beer showcase; sahti traditional ale featured; Railway Square venue; Nordic flavors"},
    {"name": "Beavertown Extravaganza (London)", "lat": 51.5650, "lon": -0.0467, "country": "England", "style": "UK/International Craft", "founded": "2014", "notes": "Beavertown's annual skull-themed party; live music; 50+ guest breweries; London craft community event"},
    {"name": "Festival of Barrel-Aged Beers (Chicago)", "lat": 41.8781, "lon": -87.6298, "country": "USA", "style": "Barrel-Aged Stouts/Sours", "founded": "2003", "notes": "FoBAB is America's premier barrel-aged beer festival; blind judging; stout and sour paradise"},
    {"name": "Berliner Bierfestival (Berlin)", "lat": 52.5200, "lon": 13.4050, "country": "Germany", "style": "International/German Craft", "founded": "1997", "notes": "Karl-Marx-Allee becomes 2.2km beer mile; 2,400+ beers from 90+ countries; world's longest beer garden"},
    {"name": "Bruges Beer Festival", "lat": 51.2094, "lon": 3.2247, "country": "Belgium", "style": "Belgian/Flemish Ales", "founded": "2008", "notes": "Medieval city setting; 80+ Belgian breweries; Markt square venue; free entry with glass purchase"},
    {"name": "Craft Beer Rising (London)", "lat": 51.5242, "lon": -0.0775, "country": "England", "style": "UK/International Craft", "founded": "2013", "notes": "Old Truman Brewery, Brick Lane; UK's hippest beer festival; street food; live music; 200+ beers"},
    {"name": "Mikkeller Beer Celebration (Copenhagen)", "lat": 55.6828, "lon": 12.6031, "country": "Denmark", "style": "World-Class Craft", "founded": "2014", "notes": "Mikkeller curated elite event; 70+ handpicked international breweries; Refshaleoen island venue"},
    {"name": "Salon du Brasseur (Colmar)", "lat": 48.0794, "lon": 7.3558, "country": "France", "style": "French/Alsatian Craft", "founded": "2017", "notes": "France's growing craft beer scene; Alsatian brewing heritage; brasserie culture meets craft innovation"},
    {"name": "South African Craft Beer Festival", "lat": -33.9249, "lon": 18.4241, "country": "South Africa", "style": "South African Craft", "founded": "2010", "notes": "Cape Town craft showcase; 40+ South African breweries; craft beer revolution in the Rainbow Nation"},
    {"name": "India Craft Beer Week (Multiple Cities)", "lat": 12.9716, "lon": 77.5946, "country": "India", "style": "Indian Craft/Craft Lagers", "founded": "2018", "notes": "Bengaluru-centered craft festival; India's booming craft scene; 100+ Indian microbreweries represented"},
    {"name": "Tallinn Craft Beer Weekend", "lat": 59.4370, "lon": 24.7536, "country": "Estonia", "style": "Baltic/Nordic Craft", "founded": "2015", "notes": "Baltic craft beer hub; Estonian/Latvian/Lithuanian breweries; Telliskivi Creative City venue"},
    {"name": "Prague Beer Museum Festival", "lat": 50.0875, "lon": 14.4213, "country": "Czech Republic", "style": "Czech Craft/Lager", "founded": "2013", "notes": "Prague's celebration of Czech craft beer revolution; 30+ taps; modern Czech ales alongside traditional lagers"},
]

# ===================================================================
# 10. BEER MUSEUMS & BREWERY TOURS (27 entries)
# ===================================================================
BEER_MUSEUMS = [
    {"name": "Guinness Storehouse (Dublin)", "lat": 53.3418, "lon": -6.2868, "country": "Ireland", "style": "Guinness Stout", "founded": "2000", "notes": "Ireland's #1 tourist attraction; 7-story experience in 1904 fermentation building; Gravity Bar rooftop views"},
    {"name": "Heineken Experience (Amsterdam)", "lat": 52.3578, "lon": 4.8914, "country": "Netherlands", "style": "Heineken Lager", "founded": "2001", "notes": "Former brewery turned interactive museum; beer tasting; holographic experiences; canal-side location"},
    {"name": "Pilsner Urquell Brewery Tour (Plzen)", "lat": 49.7486, "lon": 13.3867, "country": "Czech Republic", "style": "Pilsner Urquell", "founded": "1842", "notes": "Tour the birthplace of pilsner; underground cellars with unfiltered tank beer; copper brewhouse"},
    {"name": "Cantillon Brewery & Museum (Brussels)", "lat": 50.8433, "lon": 4.3331, "country": "Belgium", "style": "Lambic/Gueuze", "founded": "1900", "notes": "Working lambic brewery museum; open coolship; cobwebbed barrels; self-guided tour with tastings"},
    {"name": "Brewery Museum (Bruges)", "lat": 51.2083, "lon": 3.2264, "country": "Belgium", "style": "Belgian Ales History", "founded": "1981", "notes": "11th-century building tracing Bruges' brewing history; copper kettles; malting floor; historic artifacts"},
    {"name": "Sapporo Beer Museum (Sapporo)", "lat": 43.0703, "lon": 141.3550, "country": "Japan", "style": "Sapporo Lager", "founded": "1987", "notes": "Red brick Meiji-era building; traces Japanese beer from 1876; tasting hall; Hokkaido beer garden"},
    {"name": "Carlsberg Museum (Copenhagen)", "lat": 55.6622, "lon": 12.5303, "country": "Denmark", "style": "Carlsberg Pilsner", "founded": "2008", "notes": "Visit Carlsberg Brewery; Jacobsen brewhouse; world's largest bottle collection; yeast laboratory history"},
    {"name": "Smithwick's Experience (Kilkenny)", "lat": 52.6542, "lon": -7.2542, "country": "Ireland", "style": "Smithwick's Red Ale", "founded": "2014", "notes": "300-year brewing history at St. Francis Abbey site; medieval monastic brewing; interactive tour"},
    {"name": "National Brewery Museum (Potosi)", "lat": 42.6839, "lon": -90.7921, "country": "USA", "style": "American Brewing History", "founded": "2008", "notes": "Restored 1850s brewery; American brewing history from colonial era; largest collection of breweriana"},
    {"name": "Stiegl Brauwelt (Salzburg)", "lat": 47.7811, "lon": 13.0200, "country": "Austria", "style": "Stiegl Goldbrau", "founded": "2002", "notes": "Austria's largest private brewery museum; interactive brewing process; beer sommelier tastings"},
    {"name": "Spaten Museum (Munich)", "lat": 48.1319, "lon": 11.5556, "country": "Germany", "style": "Spaten Helles/Oktoberfest", "founded": "1397", "notes": "Historic Munich brewery; Gabriel Sedlmayr's lager revolution; refrigeration pioneer; brewery tours"},
    {"name": "Bass Museum (Burton upon Trent)", "lat": 52.8064, "lon": -1.6283, "country": "England", "style": "British Pale Ale History", "founded": "1977", "notes": "National Brewery Centre; tells story of Burton brewing capital; iconic red triangle trademark museum"},
    {"name": "De Halve Maan Brewery (Bruges)", "lat": 51.2044, "lon": 3.2258, "country": "Belgium", "style": "Brugse Zot/Straffe Hendrik", "founded": "1856", "notes": "Only active brewery in Bruges old town; rooftop views; underground beer pipeline to bottling plant"},
    {"name": "Sierra Nevada Mills River Tour (NC)", "lat": 35.3906, "lon": -82.5578, "country": "USA", "style": "Sierra Nevada Ales", "founded": "2014", "notes": "East Coast Sierra Nevada facility; sustainability showcase; Taproom and Restaurant; Blue Ridge setting"},
    {"name": "Brooklyn Brewery Tour (NYC)", "lat": 40.7217, "lon": -73.9572, "country": "USA", "style": "Brooklyn Lager/Ales", "founded": "1988", "notes": "Williamsburg brewery tours; Brooklyn Lager revived pre-Prohibition recipes; NYC craft pioneer"},
    {"name": "Museum of Beer and Brewing (Milwaukee)", "lat": 43.0389, "lon": -87.9065, "country": "USA", "style": "American Lager Heritage", "founded": "1990", "notes": "Former Pabst complex; Milwaukee's beer baron history; Schlitz, Blatz, Pabst, Miller heritage"},
    {"name": "Asahi Beer Museum (Suita)", "lat": 34.7606, "lon": 135.5322, "country": "Japan", "style": "Asahi Super Dry", "founded": "2003", "notes": "Tour Asahi's flagship brewery; see Super Dry production; tasting at end; Osaka industrial heritage"},
    {"name": "Weihenstephan Brewery Tour", "lat": 48.3947, "lon": 11.7286, "country": "Germany", "style": "World's Oldest Brewery", "founded": "1040", "notes": "Tour the world's oldest active brewery; Benedictine monastic brewing history; TU Munich campus"},
    {"name": "Steam Whistle Brewery (Toronto)", "lat": 43.6405, "lon": -79.3856, "country": "Canada", "style": "Premium Pilsner", "founded": "2000", "notes": "Historic John Street Roundhouse; single-beer philosophy; Toronto landmark; excellent brewery tour"},
    {"name": "Brewery Hops Museum (Poperinge)", "lat": 50.8556, "lon": 2.7244, "country": "Belgium", "style": "Hop Heritage", "founded": "2002", "notes": "Belgian hop capital museum; entire hop cycle from field to brewery; restored 19th-century hop warehouse"},
    {"name": "Samuel Adams Boston Brewery", "lat": 42.3142, "lon": -71.1044, "country": "USA", "style": "Boston Lager", "founded": "1988", "notes": "Jim Koch's brewery that reignited American craft; free tours and tastings; Boston Beer Company flagship"},
    {"name": "DAB Brewery Museum (Dortmund)", "lat": 51.5136, "lon": 7.4653, "country": "Germany", "style": "Dortmunder Export", "founded": "1868", "notes": "Dortmund was once Europe's largest brewing city; industrial beer heritage; Export lager birthplace"},
    {"name": "Trappistes Rochefort Visitor Center", "lat": 50.1600, "lon": 5.2219, "country": "Belgium", "style": "Rochefort 6/8/10", "founded": "2019", "notes": "Rare Trappist visitor center; abbey grounds tour; learn about monastic brewing life; tasting room"},
    {"name": "Kirin Beer Village (Yokohama)", "lat": 35.4906, "lon": 139.6586, "country": "Japan", "style": "Kirin Ichiban", "founded": "1991", "notes": "Kirin's showcase brewery; trace Japanese beer from 1870s; one-pour master tastings; free tours"},
    {"name": "Staropramen Visitor Centre (Prague)", "lat": 50.0706, "lon": 14.4028, "country": "Czech Republic", "style": "Staropramen Lager", "founded": "2012", "notes": "Smichov brewery interactive tour; Czech brewing techniques; tank beer tasting; multimedia exhibits"},
    {"name": "Bitburger Erlebniswelt", "lat": 49.9747, "lon": 6.5264, "country": "Germany", "style": "Bitburger Pilsner", "founded": "2017", "notes": "Bitburger Experience World; German pilsner journey; sensory tastings; Eifel region heritage"},
    {"name": "Anchor Brewing Museum (SF)", "lat": 37.7669, "lon": -122.4003, "country": "USA", "style": "Anchor Steam", "founded": "1896", "notes": "Historic Potrero Hill brewery; Fritz Maytag's craft revolution; California Common style origin; closed 2023"},
]

# ===================================================================
# MODE CONFIGURATION MAP
# ===================================================================
_MODE_MAP = {
    "Belgian Abbey & Trappist Breweries": {
        "data": BELGIAN_TRAPPIST,
        "icon": "star",
        "color": "orange",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Style", "Founded", "Notes"],
    },
    "German Beer Heritage": {
        "data": GERMAN_HERITAGE,
        "icon": "glass",
        "color": "red",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Style", "Founded", "Notes"],
    },
    "Czech & Pilsner Heritage": {
        "data": CZECH_PILSNER,
        "icon": "glass",
        "color": "darkblue",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Style", "Founded", "Notes"],
    },
    "British Pub & Ale Heritage": {
        "data": BRITISH_PUB,
        "icon": "home",
        "color": "darkred",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Style", "Founded", "Notes"],
    },
    "American Craft Beer Revolution": {
        "data": AMERICAN_CRAFT,
        "icon": "flag",
        "color": "blue",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Style", "Founded", "Notes"],
    },
    "Japanese Craft Beer": {
        "data": JAPANESE_CRAFT,
        "icon": "flag",
        "color": "cadetblue",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Style", "Founded", "Notes"],
    },
    "Ancient Brewing History": {
        "data": ANCIENT_BREWING,
        "icon": "info-sign",
        "color": "darkgreen",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Style", "Founded", "Notes"],
    },
    "Hop Growing Regions": {
        "data": HOP_REGIONS,
        "icon": "leaf",
        "color": "green",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Variety/Style", "Founded", "Notes"],
    },
    "Oktoberfest & Beer Festivals": {
        "data": BEER_FESTIVALS,
        "icon": "calendar",
        "color": "purple",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Style", "Founded", "Notes"],
    },
    "Beer Museums & Brewery Tours": {
        "data": BEER_MUSEUMS,
        "icon": "home",
        "color": "darkpurple",
        "fields": ["country", "style", "founded", "notes"],
        "labels": ["Country", "Style", "Founded", "Notes"],
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

def render_beer_maps_tab():
    """Render the Beer & Brewing Heritage Explorer tab."""

    # ---- Header ----
    st.markdown(
        '<div class="tab-header amber">'
        "<h4>Beer & Brewing Heritage Explorer</h4>"
        "<p>Trappist abbeys, historic breweries, ancient brewing sites, hop regions & beer festivals worldwide</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        key="beer_maps_mode",
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
        "Belgian Abbey & Trappist Breweries": (
            "Explore the hallowed Trappist monasteries and iconic Belgian abbey "
            "breweries where monks have perfected brewing for centuries. From the "
            "mythical Westvleteren 12 to Cantillon's wild lambics, Belgium is the "
            "spiritual home of artisanal brewing."
        ),
        "German Beer Heritage": (
            "From the world's oldest brewery at Weihenstephan to the smoke-filled "
            "taverns of Bamberg and the grand beer halls of Munich, Germany's "
            "brewing heritage spans a millennium of lager perfection and the sacred "
            "Reinheitsgebot purity law of 1516."
        ),
        "Czech & Pilsner Heritage": (
            "In 1842, Josef Groll brewed the first golden pilsner in Plzen and "
            "changed beer forever. The Czech Republic remains the world's highest "
            "per-capita beer consuming nation, with a lager culture stretching back "
            "over 700 years."
        ),
        "British Pub & Ale Heritage": (
            "The British pub is a living institution -- from medieval coaching inns "
            "to CAMRA's cask ale revolution. Yorkshire bitters, London porters, and "
            "the art of the perfectly pulled pint define a beer culture unlike any "
            "other in the world."
        ),
        "American Craft Beer Revolution": (
            "From Sierra Nevada's garage in 1980 to the hazy IPA explosion of the "
            "2010s, American craft brewing transformed global beer culture. Portland, "
            "San Diego, Vermont, and Asheville lead a movement of fearless "
            "experimentation and bold flavor."
        ),
        "Japanese Craft Beer": (
            "After the 1994 deregulation allowed microbrewing, Japan's craft scene "
            "exploded with precision-engineered ales and lagers. From Hitachino Nest's "
            "White Ale to Yo-Ho's Yona Yona, Japanese craft combines meticulous "
            "technique with creative flair."
        ),
        "Ancient Brewing History": (
            "Beer is older than civilization itself. From 11,000-year-old Natufian "
            "brewing at Raqefet Cave to the Hymn to Ninkasi in Sumer, the Pyramid "
            "builders' daily rations in Egypt, and Viking mead-ales, brewing is "
            "woven into the fabric of human history."
        ),
        "Hop Growing Regions": (
            "Noble hops from Hallertau and Saaz defined lager for centuries. Today, "
            "Yakima Valley's Citra and Mosaic, New Zealand's Nelson Sauvin, and "
            "Australia's Galaxy are driving the craft revolution. Every great beer "
            "starts in the hop field."
        ),
        "Oktoberfest & Beer Festivals": (
            "From Munich's legendary Oktoberfest with its 6 million visitors to the "
            "Great American Beer Festival's 4,000 craft beers, beer festivals are "
            "where cultures celebrate brewing heritage. Raise a stein, sample the "
            "world, and join the global toast."
        ),
        "Beer Museums & Brewery Tours": (
            "Step inside the Guinness Storehouse's seven stories, descend into "
            "Pilsner Urquell's medieval cellars, or wander Cantillon's cobwebbed "
            "barrel rooms. Beer museums and brewery tours bring centuries of "
            "brewing history and craft to life."
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
    zoom = 5 if mode in ("German Beer Heritage", "Czech & Pilsner Heritage", "British Pub & Ale Heritage") else 3
    if mode == "Japanese Craft Beer":
        zoom = 5
    elif mode == "Belgian Abbey & Trappist Breweries":
        zoom = 4
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
        file_name=f"beer_heritage_{mode.lower().replace(' ', '_').replace('&', 'and')}.csv",
        mime="text/csv",
        key=f"dl_beer_{mode}",
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

    # ---- Style / Founded analysis ----
    st.markdown("#### Founding Era Analysis")
    era_buckets: dict = {
        "Ancient / Medieval (before 1500)": 0,
        "Early Modern (1500-1799)": 0,
        "Industrial Age (1800-1949)": 0,
        "Modern Craft (1950-1999)": 0,
        "21st Century (2000+)": 0,
        "Prehistoric / Approximate": 0,
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
            era_buckets["Prehistoric / Approximate"] += 1
        elif year < 0:
            era_buckets["Ancient / Medieval (before 1500)"] += 1
        elif year < 1500:
            era_buckets["Ancient / Medieval (before 1500)"] += 1
        elif year < 1800:
            era_buckets["Early Modern (1500-1799)"] += 1
        elif year < 1950:
            era_buckets["Industrial Age (1800-1949)"] += 1
        elif year < 2000:
            era_buckets["Modern Craft (1950-1999)"] += 1
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
        "Belgian Abbey & Trappist Breweries": [
            "Only 14 breweries worldwide hold authentic Trappist designation (ITA seal).",
            "Westvleteren 12 has been repeatedly rated the best beer in the world.",
            "Lambic is the only major beer style fermented entirely by wild yeast.",
            "Belgium has over 1,500 unique beer brands for a population of 11 million.",
        ],
        "German Beer Heritage": [
            "The Reinheitsgebot (1516) is the world's oldest food safety regulation still referenced.",
            "Germany has over 1,300 breweries, many family-owned for generations.",
            "Weihenstephan (1040) holds the Guinness record as the oldest active brewery.",
            "Bamberg has the highest brewery-to-population ratio of any city.",
        ],
        "Czech & Pilsner Heritage": [
            "Czechs drink more beer per capita than any other nation (~140 liters/year).",
            "The pilsner style invented in 1842 now accounts for over 90% of global beer.",
            "Saaz hops from Zatec are considered among the world's finest noble hops.",
            "Czech beer culture is on the UNESCO Intangible Cultural Heritage list.",
        ],
        "British Pub & Ale Heritage": [
            "CAMRA (founded 1971) saved cask-conditioned ale from near extinction.",
            "The UK has over 47,000 pubs, though numbers have been declining since 2000.",
            "Burton-on-Trent's gypsum-rich water made it the historic capital of British brewing.",
            "Cask ale is served by gravity or handpump and is naturally carbonated in the cask.",
        ],
        "American Craft Beer Revolution": [
            "The US went from 89 breweries in 1978 to over 9,500 in 2023.",
            "Sierra Nevada Pale Ale (1980) is considered the spark of the craft revolution.",
            "New England/Hazy IPA is the most influential style of the 2010s.",
            "Homebrewing was illegal in the US until Jimmy Carter legalized it in 1978.",
        ],
        "Japanese Craft Beer": [
            "Japan's 1994 tax law revision reduced the minimum production volume and enabled microbrewing.",
            "Hitachino Nest White Ale is Japan's most internationally recognized craft beer.",
            "Japan's big four (Asahi, Kirin, Sapporo, Suntory) control 95% of the domestic market.",
            "Sake breweries have been experimenting with beer since the Meiji era (1868).",
        ],
        "Ancient Brewing History": [
            "The oldest known beer recipe is the 3,900-year-old Hymn to Ninkasi from Sumer.",
            "Egyptian pyramid builders received a daily ration of about 4 liters of beer.",
            "Beer may have been the incentive for humans to adopt agriculture.",
            "Ancient beer was often consumed through straws to filter out grain solids.",
        ],
        "Hop Growing Regions": [
            "Hops were not widely used in beer until the 9th-13th centuries in Europe.",
            "Before hops, beer was flavored with gruit (a mix of herbs and spices).",
            "The Yakima Valley produces about 75% of all US hops.",
            "Germany's Hallertau region alone produces about a third of the world's hops.",
        ],
        "Oktoberfest & Beer Festivals": [
            "Munich Oktoberfest visitors consume roughly 7.7 million liters of beer annually.",
            "Only six Munich breweries may serve beer at the official Oktoberfest.",
            "The Great American Beer Festival judges over 10,000 entries in 100+ categories.",
            "The original 1810 Oktoberfest was a wedding celebration for Crown Prince Ludwig.",
        ],
        "Beer Museums & Brewery Tours": [
            "The Guinness Storehouse welcomes over 1.7 million visitors annually.",
            "Pilsner Urquell's cellars extend 9 km under Plzen with unfiltered tank beer.",
            "Cantillon's cobwebbed barrels contain wild yeast essential for spontaneous fermentation.",
            "The Heineken Experience is built in the original 1867 Amsterdam brewery.",
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
        "Data is curated from historical records, brewery publications, beer guides, "
        "and enthusiast databases. Locations are approximate. Brewery status and visiting "
        "hours may change -- check official sources before visiting."
    )
