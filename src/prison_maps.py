# -*- coding: utf-8 -*-
"""
Prisons, Justice & Incarceration Maps module for TerraScout AI.
Provides 10 interactive map modes covering famous prisons, Holocaust memorials,
Gulag camps, incarceration rates, historic dungeons, war-crimes tribunals,
great escapes, the death penalty, political prisoners, and justice systems.
All data is hardcoded -- no API keys required.
"""

import io
import html as _html
import streamlit as st
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ═══════════════════════════════════════════════════════════════════════
# COLOUR PALETTE  (dark theme)
# ═══════════════════════════════════════════════════════════════════════
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_ACCENT = "#06b6d4"
_MUTED = "#5a6580"

# ═══════════════════════════════════════════════════════════════════════
# MAP MODE LIST
# ═══════════════════════════════════════════════════════════════════════
MAP_MODES = [
    "World's Most Famous Prisons",
    "Holocaust Memorial Sites",
    "Gulag Archipelago",
    "Incarceration Rates by Country",
    "Historic Dungeons & Fortresses",
    "War Crimes Tribunals",
    "Great Escapes",
    "Death Penalty Map",
    "Political Prisoners",
    "Justice & Court Systems",
]

# ═══════════════════════════════════════════════════════════════════════
# 1. WORLD'S MOST FAMOUS PRISONS  (30 entries)
# ═══════════════════════════════════════════════════════════════════════
FAMOUS_PRISONS = [
    {"name": "Alcatraz Federal Penitentiary", "lat": 37.8267, "lon": -122.4233, "country": "USA", "years": "1934-1963", "notes": "Island prison in San Francisco Bay; housed Al Capone, 'Birdman' Robert Stroud"},
    {"name": "Tower of London", "lat": 51.5081, "lon": -0.0759, "country": "England", "years": "1100-1952", "notes": "Royal palace & fortress; held Anne Boleyn, Sir Walter Raleigh, Rudolf Hess"},
    {"name": "Bastille", "lat": 48.8532, "lon": -2.3692, "country": "France", "years": "1370-1789", "notes": "Symbol of royal tyranny; storming on 14 July 1789 sparked the French Revolution"},
    {"name": "Robben Island", "lat": -33.8060, "lon": 18.3664, "country": "South Africa", "years": "1961-1996", "notes": "Nelson Mandela imprisoned here 18 years; now UNESCO World Heritage Site"},
    {"name": "Chateau d'If", "lat": 43.2800, "lon": 5.3250, "country": "France", "years": "1540-1890", "notes": "Island fortress near Marseille; inspiration for The Count of Monte Cristo"},
    {"name": "Devil's Island", "lat": 5.2944, "lon": -52.5833, "country": "French Guiana", "years": "1852-1953", "notes": "Notorious penal colony; held Alfred Dreyfus; 80 % mortality rate"},
    {"name": "Eastern State Penitentiary", "lat": 39.9683, "lon": -75.1727, "country": "USA", "years": "1829-1970", "notes": "First true penitentiary; solitary-confinement model; held Al Capone"},
    {"name": "Sing Sing Correctional Facility", "lat": 41.1637, "lon": -73.8712, "country": "USA", "years": "1826-present", "notes": "On Hudson River; 614 executions; phrase 'sent up the river'"},
    {"name": "San Quentin State Prison", "lat": 37.9386, "lon": -122.4858, "country": "USA", "years": "1852-present", "notes": "California's oldest prison; largest death row in Western Hemisphere"},
    {"name": "Hoa Lo Prison (Hanoi Hilton)", "lat": 21.0254, "lon": 105.8467, "country": "Vietnam", "years": "1896-1993", "notes": "French colonial prison; held American POWs including John McCain"},
    {"name": "Lubyanka", "lat": 55.7601, "lon": 37.6276, "country": "Russia", "years": "1920-present", "notes": "KGB/FSB headquarters; notorious interrogation & execution centre"},
    {"name": "Spandau Prison", "lat": 52.5372, "lon": 13.2050, "country": "Germany", "years": "1876-1987", "notes": "Held Nazi war criminals; Rudolf Hess sole prisoner 1966-1987; demolished"},
    {"name": "Portlaoise Prison", "lat": 53.0344, "lon": -7.2989, "country": "Ireland", "years": "1830-present", "notes": "Ireland's most secure prison; held IRA, Real IRA, dissident republicans"},
    {"name": "Tadmor Prison", "lat": 34.5569, "lon": 38.2672, "country": "Syria", "years": "1930-2015", "notes": "Desert military prison; 1980 massacre killed ~1,000 inmates; destroyed by ISIS"},
    {"name": "Evin Prison", "lat": 35.8033, "lon": 51.3908, "country": "Iran", "years": "1972-present", "notes": "Tehran political prison; holds journalists, activists, dual nationals"},
    {"name": "Guantanamo Bay Detention Camp", "lat": 19.9023, "lon": -75.0967, "country": "Cuba (US-operated)", "years": "2002-present", "notes": "US military prison for 'enemy combatants'; controversial indefinite detention"},
    {"name": "ADX Florence", "lat": 38.3586, "lon": -105.0975, "country": "USA", "years": "1994-present", "notes": "'Alcatraz of the Rockies'; most secure federal prison; 23-hr solitary"},
    {"name": "Rikers Island", "lat": 40.7931, "lon": -73.8860, "country": "USA", "years": "1932-present", "notes": "NYC jail complex; 10 facilities; scheduled for closure by 2027"},
    {"name": "Bang Kwang Central Prison", "lat": 13.8858, "lon": 100.4922, "country": "Thailand", "years": "1931-present", "notes": "'Bangkok Hilton'; death-row inmates shackled; harsh conditions"},
    {"name": "La Sante Prison", "lat": 48.8339, "lon": 2.3378, "country": "France", "years": "1867-present", "notes": "Central Paris prison; high suicide rate; held Carlos the Jackal"},
    {"name": "Maze Prison (Long Kesh)", "lat": 54.4928, "lon": -6.0978, "country": "Northern Ireland", "years": "1971-2000", "notes": "H-Blocks; 1981 hunger strikes; Bobby Sands; mass escape 1983"},
    {"name": "Camp 22 (Hoeryong)", "lat": 42.1833, "lon": 129.7500, "country": "North Korea", "years": "1965-2012?", "notes": "Political labour camp; estimated 50,000 prisoners; alleged atrocities"},
    {"name": "Carandiru Penitentiary", "lat": -23.5158, "lon": -46.6267, "country": "Brazil", "years": "1920-2002", "notes": "1992 massacre: police killed 111 inmates; demolished 2002"},
    {"name": "Black Dolphin Prison", "lat": 51.2667, "lon": 56.0833, "country": "Russia", "years": "1773-present", "notes": "Houses Russia's worst criminals; no parole; 24-hr surveillance"},
    {"name": "Pollsmoor Prison", "lat": -34.0778, "lon": 18.4722, "country": "South Africa", "years": "1964-present", "notes": "Mandela transferred here from Robben Island; severe overcrowding"},
    {"name": "Mountjoy Prison", "lat": 53.3583, "lon": -6.2750, "country": "Ireland", "years": "1850-present", "notes": "Dublin's main prison; executions until 1954; 14 leaders buried here"},
    {"name": "Colditz Castle (Oflag IV-C)", "lat": 51.1308, "lon": 12.8139, "country": "Germany", "years": "1939-1945", "notes": "WWII POW camp for 'incorrigible' escapers; 30+ successful escapes"},
    {"name": "Kilmainham Gaol", "lat": 53.3419, "lon": -6.3100, "country": "Ireland", "years": "1796-1924", "notes": "Held leaders of 1916 Rising; executions in Stonebreakers' Yard"},
    {"name": "Port Arthur Convict Settlement", "lat": -43.1475, "lon": 147.8547, "country": "Australia", "years": "1833-1877", "notes": "Tasmanian penal colony; 'model prison' silent system; UNESCO site"},
    {"name": "Tuol Sleng (S-21)", "lat": 11.5494, "lon": 104.9172, "country": "Cambodia", "years": "1975-1979", "notes": "Khmer Rouge interrogation centre; ~17,000 prisoners; 12 known survivors"},
]

# ═══════════════════════════════════════════════════════════════════════
# 2. HOLOCAUST MEMORIAL SITES  (30 entries)
# ═══════════════════════════════════════════════════════════════════════
HOLOCAUST_SITES = [
    {"name": "Auschwitz-Birkenau", "lat": 50.0343, "lon": 19.1781, "country": "Poland", "type": "Death camp", "est_deaths": "1,100,000", "notes": "Largest Nazi extermination camp; UNESCO World Heritage Site"},
    {"name": "Treblinka", "lat": 52.6313, "lon": 22.0533, "country": "Poland", "type": "Death camp", "est_deaths": "870,000", "notes": "Second deadliest camp; Warsaw Ghetto deportees; revolt Aug 1943"},
    {"name": "Belzec", "lat": 50.3717, "lon": 23.4581, "country": "Poland", "type": "Death camp", "est_deaths": "600,000", "notes": "Operation Reinhard camp; only 7 known survivors"},
    {"name": "Sobibor", "lat": 51.4500, "lon": 23.6000, "country": "Poland", "type": "Death camp", "est_deaths": "250,000", "notes": "Uprising Oct 1943 led to camp closure; 58 survivors of revolt"},
    {"name": "Chelmno", "lat": 52.1533, "lon": 18.7317, "country": "Poland", "type": "Death camp", "est_deaths": "340,000", "notes": "First Nazi camp using gas vans; operated 1941-1945"},
    {"name": "Dachau", "lat": 48.2700, "lon": 11.4683, "country": "Germany", "type": "Concentration camp", "est_deaths": "41,500+", "notes": "First Nazi concentration camp (1933); model for all others"},
    {"name": "Buchenwald", "lat": 51.0214, "lon": 11.2486, "country": "Germany", "type": "Concentration camp", "est_deaths": "56,000", "notes": "Near Weimar; medical experiments; liberated by US Army April 1945"},
    {"name": "Bergen-Belsen", "lat": 52.7581, "lon": 9.9075, "country": "Germany", "type": "Concentration camp", "est_deaths": "70,000", "notes": "Anne Frank died here Feb 1945; British liberation filmed"},
    {"name": "Ravensbrueck", "lat": 53.1900, "lon": 13.1683, "country": "Germany", "type": "Concentration camp", "est_deaths": "30,000-50,000", "notes": "Largest women's camp; medical experiments; forced labor"},
    {"name": "Sachsenhausen", "lat": 52.7653, "lon": 13.2633, "country": "Germany", "type": "Concentration camp", "est_deaths": "30,000+", "notes": "Near Berlin; model for camp design; counterfeiting Operation Bernhard"},
    {"name": "Mauthausen", "lat": 48.2581, "lon": 14.5014, "country": "Austria", "type": "Concentration camp", "est_deaths": "90,000", "notes": "Category III (harshest); granite quarry; 'Stairs of Death'"},
    {"name": "Theresienstadt (Terezin)", "lat": 50.5131, "lon": 14.1500, "country": "Czech Republic", "type": "Ghetto/Transit camp", "est_deaths": "33,000", "notes": "Propaganda 'model ghetto'; Red Cross visit 1944; transit to Auschwitz"},
    {"name": "Majdanek", "lat": 51.2333, "lon": 22.6000, "country": "Poland", "type": "Death camp", "est_deaths": "78,000", "notes": "Only major camp not dismantled; gas chambers preserved intact"},
    {"name": "Stutthof", "lat": 54.3267, "lon": 19.1550, "country": "Poland", "type": "Concentration camp", "est_deaths": "65,000", "notes": "First camp outside Germany; death marches Jan 1945"},
    {"name": "Yad Vashem", "lat": 31.7741, "lon": 35.1753, "country": "Israel", "type": "Memorial/Museum", "est_deaths": "N/A", "notes": "World Holocaust Remembrance Center; Hall of Names; Children's Memorial"},
    {"name": "United States Holocaust Memorial Museum", "lat": 38.8867, "lon": -77.0328, "country": "USA", "type": "Memorial/Museum", "est_deaths": "N/A", "notes": "Opened 1993 in Washington DC; 40+ million visitors"},
    {"name": "Memorial to the Murdered Jews of Europe", "lat": 52.5139, "lon": 13.3789, "country": "Germany", "type": "Memorial", "est_deaths": "N/A", "notes": "2,711 concrete stelae in Berlin; designed by Peter Eisenman; opened 2005"},
    {"name": "Drancy Internment Camp", "lat": 48.9167, "lon": 2.4500, "country": "France", "type": "Transit camp", "est_deaths": "varies", "notes": "Main French transit camp to Auschwitz; 67,400 deported; memorial opened 2012"},
    {"name": "Westerbork Transit Camp", "lat": 52.9167, "lon": 6.6167, "country": "Netherlands", "type": "Transit camp", "est_deaths": "varies", "notes": "Anne Frank family deported from here; 107,000 people deported"},
    {"name": "Jasenovac", "lat": 45.2833, "lon": 16.9333, "country": "Croatia", "type": "Death camp", "est_deaths": "83,000-100,000", "notes": "Ustashe regime camp; Serbs, Jews, Roma; only Axis-run extermination camp"},
    {"name": "Fossoli Camp", "lat": 44.7333, "lon": 10.9167, "country": "Italy", "type": "Transit camp", "est_deaths": "varies", "notes": "Transit camp near Carpi; Primo Levi deported from here to Auschwitz"},
    {"name": "Neuengamme", "lat": 53.4267, "lon": 10.2333, "country": "Germany", "type": "Concentration camp", "est_deaths": "42,900", "notes": "Near Hamburg; brick works; largest camp in northwest Germany"},
    {"name": "Gross-Rosen", "lat": 50.9983, "lon": 16.2783, "country": "Poland", "type": "Concentration camp", "est_deaths": "40,000", "notes": "Granite quarry; 100+ sub-camps across Poland and Germany"},
    {"name": "Natzweiler-Struthof", "lat": 48.4522, "lon": 7.2531, "country": "France", "type": "Concentration camp", "est_deaths": "22,000", "notes": "Only camp on French soil; gas chamber preserved; medical experiments"},
    {"name": "Flossenburg", "lat": 49.7322, "lon": 12.3536, "country": "Germany", "type": "Concentration camp", "est_deaths": "30,000", "notes": "Near Czech border; Bonhoeffer & Canaris executed here April 1945"},
    {"name": "Mittelbau-Dora", "lat": 51.5311, "lon": 10.7458, "country": "Germany", "type": "Concentration camp", "est_deaths": "20,000", "notes": "Underground V-2 rocket factory; tunnel slave labor"},
    {"name": "Anne Frank House", "lat": 52.3752, "lon": 4.8840, "country": "Netherlands", "type": "Memorial/Museum", "est_deaths": "N/A", "notes": "Secret Annex at Prinsengracht 263; over 1 million visitors annually"},
    {"name": "Topography of Terror", "lat": 52.5067, "lon": 13.3833, "country": "Germany", "type": "Memorial/Museum", "est_deaths": "N/A", "notes": "Berlin museum on site of SS/Gestapo headquarters; free admission"},
    {"name": "Kazerne Dossin", "lat": 51.0253, "lon": 4.4833, "country": "Belgium", "type": "Transit camp/Museum", "est_deaths": "varies", "notes": "Mechelen transit camp; 25,274 Jews and 354 Roma deported to Auschwitz"},
    {"name": "Stolpersteine (Berlin)", "lat": 52.5200, "lon": 13.4050, "country": "Germany/Europe-wide", "type": "Memorial", "est_deaths": "N/A", "notes": "75,000+ brass 'stumbling stones' in sidewalks across Europe; by Gunter Demnig"},
]

# ═══════════════════════════════════════════════════════════════════════
# 3. GULAG ARCHIPELAGO  (30 entries)
# ═══════════════════════════════════════════════════════════════════════
GULAG_CAMPS = [
    {"name": "Kolyma (Sevvostlag)", "lat": 62.0, "lon": 150.0, "country": "Russia", "years": "1932-1957", "est_prisoners": "800,000+", "notes": "Deadliest Gulag region; gold mines; -60 C winters; Varlam Shalamov wrote about it"},
    {"name": "Vorkuta (Vorkutlag)", "lat": 67.5, "lon": 64.0, "country": "Russia", "years": "1932-1962", "est_prisoners": "73,000 at peak", "notes": "Coal mines above Arctic Circle; 1953 uprising after Stalin's death"},
    {"name": "Magadan", "lat": 59.5616, "lon": 150.8003, "country": "Russia", "years": "1932-1953", "est_prisoners": "varies", "notes": "Gateway city to Kolyma camps; 'Road of Bones'; Mask of Sorrow memorial"},
    {"name": "Norilsk (Norillag)", "lat": 69.3558, "lon": 88.1893, "country": "Russia", "years": "1935-1956", "est_prisoners": "70,000+", "notes": "Built Norilsk city and nickel mines; 1953 uprising; northernmost city"},
    {"name": "Solovetsky Islands (SLON)", "lat": 65.0333, "lon": 35.8333, "country": "Russia", "years": "1923-1939", "est_prisoners": "varies", "notes": "First major Gulag camp; former monastery; prototype for entire system"},
    {"name": "Perm-36", "lat": 58.2500, "lon": 57.3333, "country": "Russia", "years": "1946-1988", "est_prisoners": "varies", "notes": "Last political camp closed in USSR; now memorial museum (controversial)"},
    {"name": "Karaganda (Karlag)", "lat": 49.8, "lon": 73.1, "country": "Kazakhstan", "years": "1931-1959", "est_prisoners": "65,000 at peak", "notes": "One of largest camps; agricultural and mining; 100,000+ died"},
    {"name": "Dalstroi (Magadan region)", "lat": 60.0, "lon": 148.0, "country": "Russia", "years": "1931-1953", "est_prisoners": "varies", "notes": "Industrial complex spanning all NE Siberia; gold, tin, uranium mining"},
    {"name": "Kotlas (transit point)", "lat": 61.2542, "lon": 46.6328, "country": "Russia", "years": "1930s-1950s", "est_prisoners": "transit", "notes": "Major transit hub; rail junction sending prisoners north to camps"},
    {"name": "Inta (Minlag)", "lat": 66.0333, "lon": 60.1667, "country": "Russia", "years": "1942-1957", "est_prisoners": "25,000+", "notes": "Coal mining above Arctic Circle; built city of Inta"},
    {"name": "Ekibastuz", "lat": 51.7333, "lon": 75.3333, "country": "Kazakhstan", "years": "1948-1955", "est_prisoners": "varies", "notes": "Coal mines; Solzhenitsyn imprisoned here; described in One Day in the Life"},
    {"name": "Potma (Dubravlag)", "lat": 54.0, "lon": 43.5, "country": "Russia", "years": "1931-1990s", "est_prisoners": "varies", "notes": "Mordovia camp complex; held political prisoners through Soviet era"},
    {"name": "Pechorlag", "lat": 65.15, "lon": 57.25, "country": "Russia", "years": "1940-1959", "est_prisoners": "30,000+", "notes": "Built railway and coal mines in Pechora region; extreme conditions"},
    {"name": "Belbaltlag (White Sea Canal)", "lat": 63.0, "lon": 34.5, "country": "Russia", "years": "1931-1933", "est_prisoners": "126,000", "notes": "Built 227 km canal in 20 months; 12,000+ died; Stalin showcase project"},
    {"name": "Bamlag (BAM Railway)", "lat": 55.0, "lon": 120.0, "country": "Russia", "years": "1932-1953", "est_prisoners": "150,000+", "notes": "Built Baikal-Amur Mainline railway; vast camp spanning thousands of km"},
    {"name": "Steplag", "lat": 47.8, "lon": 67.5, "country": "Kazakhstan", "years": "1948-1956", "est_prisoners": "30,000", "notes": "Kazakh steppe camp; 1954 Kengir uprising one of largest in Gulag history"},
    {"name": "Taishet (Ozerlag)", "lat": 55.9333, "lon": 98.0000, "country": "Russia", "years": "1948-1958", "est_prisoners": "varies", "notes": "Eastern Siberia; built railway; starting point for BAM line"},
    {"name": "Ukhta (Ukhtpechlag)", "lat": 63.5667, "lon": 53.7000, "country": "Russia", "years": "1929-1955", "est_prisoners": "varies", "notes": "Oil and coal extraction; built infrastructure of Komi Republic"},
    {"name": "Sevzheldorlag", "lat": 62.0, "lon": 50.0, "country": "Russia", "years": "1938-1950", "est_prisoners": "80,000+", "notes": "Northern Railway camp; built Kotlas-Vorkuta railway line"},
    {"name": "Krasnoyarsk camps (Kraslag)", "lat": 56.0, "lon": 93.0, "country": "Russia", "years": "1938-1960", "est_prisoners": "varies", "notes": "Logging and construction in Krasnoyarsk region; vast network"},
    {"name": "Temirtau", "lat": 50.0667, "lon": 72.9667, "country": "Kazakhstan", "years": "1940s-1950s", "est_prisoners": "varies", "notes": "Steel mill construction using forced labor; now industrial city"},
    {"name": "Butugychag", "lat": 62.0, "lon": 149.0, "country": "Russia", "years": "1937-1956", "est_prisoners": "varies", "notes": "Uranium and tin mining in Kolyma; radioactive exposure; mass graves"},
    {"name": "Igarka", "lat": 67.4667, "lon": 86.5667, "country": "Russia", "years": "1930s-1950s", "est_prisoners": "varies", "notes": "Arctic port and lumber camps; part of 'Dead Road' railway project"},
    {"name": "Salekhard (Ob construction 501/503)", "lat": 66.5333, "lon": 66.6000, "country": "Russia", "years": "1947-1953", "est_prisoners": "100,000+", "notes": "Trans-polar railway ('Dead Road'); abandoned after Stalin's death"},
    {"name": "Medvezhyegorsk (BBK)", "lat": 62.9167, "lon": 34.4500, "country": "Russia", "years": "1930s", "est_prisoners": "varies", "notes": "White Sea-Baltic Canal HQ; Sandarmokh forest mass execution site"},
    {"name": "Viatlag", "lat": 59.3, "lon": 49.5, "country": "Russia", "years": "1938-1956", "est_prisoners": "30,000+", "notes": "Timber camps in Kirov region; harsh forestry labour"},
    {"name": "Elgen", "lat": 62.1, "lon": 147.0, "country": "Russia", "years": "1930s-1950s", "est_prisoners": "varies", "notes": "Women's camp in Kolyma; Yevgenia Ginzburg wrote of her time here"},
    {"name": "Sukhanovo Prison", "lat": 55.5833, "lon": 37.7167, "country": "Russia", "years": "1938-1952", "est_prisoners": "varies", "notes": "Secret NKVD prison near Moscow; special torture facility; Solzhenitsyn mentions"},
    {"name": "Akmolinsk camp for wives (ALZHIR)", "lat": 51.1, "lon": 71.4, "country": "Kazakhstan", "years": "1938-1953", "est_prisoners": "18,000 women", "notes": "Held wives and children of 'enemies of the people'; memorial museum"},
    {"name": "Zhezkazgan (Steplag centre)", "lat": 47.7833, "lon": 67.7667, "country": "Kazakhstan", "years": "1940s-1950s", "est_prisoners": "varies", "notes": "Copper mining centre; Kengir uprising 1954; 700+ prisoners killed"},
]

# ═══════════════════════════════════════════════════════════════════════
# 4. INCARCERATION RATES  (50 countries, per 100k, 2024 estimates)
# ═══════════════════════════════════════════════════════════════════════
INCARCERATION_DATA = [
    {"country": "United States", "rate": 531, "total": 1_767_200, "lat": 39.8, "lon": -98.5, "notes": "Highest total incarcerated population; declining since 2009 peak"},
    {"country": "El Salvador", "rate": 605, "total": 39_000, "lat": 13.7, "lon": -88.9, "notes": "Surged after 2022 gang crackdown; mega-prison CECOT opened 2023"},
    {"country": "Rwanda", "rate": 580, "total": 76_000, "lat": -1.9, "lon": 29.9, "notes": "Post-genocide detentions drove rate very high; community courts (Gacaca)"},
    {"country": "Turkmenistan", "rate": 552, "total": 35_000, "lat": 39.0, "lon": 59.5, "notes": "Opaque system; forced labour camps; no independent monitoring"},
    {"country": "Cuba", "rate": 510, "total": 57_000, "lat": 21.5, "lon": -80.0, "notes": "Political prisoners included; limited transparency"},
    {"country": "Thailand", "rate": 411, "total": 286_000, "lat": 15.0, "lon": 100.0, "notes": "Severe overcrowding; lese-majeste laws; drug offences drive numbers"},
    {"country": "Brazil", "rate": 381, "total": 811_700, "lat": -14.2, "lon": -51.9, "notes": "Third largest prison population; 70 % overcrowding; gang control inside"},
    {"country": "Russia", "rate": 300, "total": 433_000, "lat": 61.5, "lon": 105.3, "notes": "Declining from Soviet-era highs; penal colonies ('zona') system"},
    {"country": "Turkey", "rate": 390, "total": 336_000, "lat": 39.0, "lon": 35.0, "notes": "Post-2016 coup purge; massive prison building programme"},
    {"country": "Iran", "rate": 282, "total": 240_000, "lat": 32.4, "lon": 53.7, "notes": "Political prisoners; high execution rate; overcrowded"},
    {"country": "China", "rate": 119, "total": 1_690_000, "lat": 35.9, "lon": 104.2, "notes": "Second largest total; excludes pre-trial & Xinjiang detention centres"},
    {"country": "India", "rate": 51, "total": 573_220, "lat": 20.6, "lon": 79.0, "notes": "Low rate but huge total; 76 % are undertrials (pre-conviction)"},
    {"country": "United Kingdom", "rate": 130, "total": 87_700, "lat": 55.4, "lon": -3.4, "notes": "Highest rate in Western Europe; overcrowding crisis"},
    {"country": "France", "rate": 105, "total": 73_600, "lat": 46.2, "lon": 2.2, "notes": "Chronic overcrowding; European Court of Human Rights rulings"},
    {"country": "Germany", "rate": 64, "total": 54_400, "lat": 51.2, "lon": 10.4, "notes": "Declining trend; focus on rehabilitation; open prisons"},
    {"country": "Japan", "rate": 36, "total": 44_800, "lat": 36.2, "lon": 138.3, "notes": "Very low rate; aging prison population; 99 % conviction rate"},
    {"country": "Canada", "rate": 104, "total": 40_400, "lat": 56.1, "lon": -106.3, "notes": "Indigenous over-representation; federal vs provincial split"},
    {"country": "Australia", "rate": 160, "total": 42_000, "lat": -25.3, "lon": 133.8, "notes": "Indigenous Australians 29 % of prisoners (3 % of population)"},
    {"country": "Mexico", "rate": 168, "total": 220_000, "lat": 23.6, "lon": -102.5, "notes": "Cartel-related violence; overcrowding; pre-trial detention high"},
    {"country": "South Africa", "rate": 234, "total": 142_000, "lat": -30.6, "lon": 22.9, "notes": "Overcrowded; gang culture inside prisons; Pollsmoor, Drakenstein"},
    {"country": "Indonesia", "rate": 89, "total": 248_000, "lat": -0.8, "lon": 113.9, "notes": "Drug offences main driver; overcrowding; Bali's Kerobokan prison"},
    {"country": "Philippines", "rate": 179, "total": 215_000, "lat": 12.9, "lon": 121.8, "notes": "Extreme overcrowding (400-500 %); drug war crackdown"},
    {"country": "Nigeria", "rate": 39, "total": 80_000, "lat": 9.1, "lon": 8.7, "notes": "72 % are awaiting trial; colonial-era facilities; severe overcrowding"},
    {"country": "Egypt", "rate": 111, "total": 120_000, "lat": 26.8, "lon": 30.8, "notes": "Political prisoners; post-2013 crackdown; new mega-prisons"},
    {"country": "Colombia", "rate": 230, "total": 118_000, "lat": 4.6, "lon": -74.3, "notes": "Drug-related offences; FARC peace process changed dynamics"},
    {"country": "Poland", "rate": 186, "total": 71_600, "lat": 51.9, "lon": 19.1, "notes": "Higher than EU average; electronic monitoring expanding"},
    {"country": "Italy", "rate": 98, "total": 58_700, "lat": 41.9, "lon": 12.6, "notes": "Overcrowded; mafia inmates in 41-bis solitary regime"},
    {"country": "Spain", "rate": 117, "total": 55_800, "lat": 40.5, "lon": -3.7, "notes": "Declining trend; Basque political prisoners controversy ended"},
    {"country": "Argentina", "rate": 238, "total": 110_000, "lat": -38.4, "lon": -63.6, "notes": "Rising rate; overcrowding; Buenos Aires province worst"},
    {"country": "South Korea", "rate": 90, "total": 47_000, "lat": 35.9, "lon": 127.8, "notes": "Relatively low; former presidents imprisoned for corruption"},
    {"country": "Saudi Arabia", "rate": 197, "total": 70_000, "lat": 24.0, "lon": 45.0, "notes": "Opaque system; political detentions; anti-terrorism laws"},
    {"country": "Pakistan", "rate": 36, "total": 82_000, "lat": 30.4, "lon": 69.3, "notes": "Low rate but severe overcrowding (200 %); blasphemy detentions"},
    {"country": "Bangladesh", "rate": 43, "total": 72_000, "lat": 23.7, "lon": 90.4, "notes": "Overcrowded (300 %); many pre-trial detainees; colonial-era jails"},
    {"country": "Vietnam", "rate": 123, "total": 126_000, "lat": 14.1, "lon": 108.3, "notes": "Political prisoners; drug offences; limited transparency"},
    {"country": "Ethiopia", "rate": 99, "total": 118_000, "lat": 9.1, "lon": 40.5, "notes": "Political detentions; Maekelawi detention centre closed 2018"},
    {"country": "Norway", "rate": 54, "total": 3_000, "lat": 60.5, "lon": 8.5, "notes": "Rehabilitation focus; open prisons; Halden prison model"},
    {"country": "Sweden", "rate": 60, "total": 6_300, "lat": 60.1, "lon": 18.6, "notes": "Low rate; rehabilitation over punishment; open institutions"},
    {"country": "Finland", "rate": 50, "total": 2_800, "lat": 61.9, "lon": 25.7, "notes": "Among lowest in Europe; open prisons; strong social safety net"},
    {"country": "Denmark", "rate": 63, "total": 3_700, "lat": 56.3, "lon": 9.5, "notes": "Liberal system; electronic monitoring; open prisons"},
    {"country": "Netherlands", "rate": 59, "total": 10_300, "lat": 52.1, "lon": 5.3, "notes": "Closing prisons due to low crime; imports prisoners from Belgium/Norway"},
    {"country": "Iceland", "rate": 33, "total": 130, "lat": 64.1, "lon": -21.9, "notes": "Smallest prison population in Europe; open prison at Kviabryggia"},
    {"country": "Venezuela", "rate": 178, "total": 50_000, "lat": 6.4, "lon": -66.6, "notes": "Chaotic prison system; gangs control facilities; 'pranes' (prison bosses)"},
    {"country": "Peru", "rate": 310, "total": 103_000, "lat": -9.2, "lon": -75.0, "notes": "Rising rapidly; overcrowded; Lurigancho housed 10,000+ inmates"},
    {"country": "Kenya", "rate": 130, "total": 70_000, "lat": -0.0, "lon": 37.9, "notes": "Colonial-era facilities; overcrowding; petty offenders fill prisons"},
    {"country": "Morocco", "rate": 220, "total": 83_000, "lat": 31.8, "lon": -7.1, "notes": "High for Africa; drug offences; new prisons being built"},
    {"country": "Israel", "rate": 163, "total": 16_500, "lat": 31.0, "lon": 34.9, "notes": "Excludes Palestinian detainees in military system; security prisoners"},
    {"country": "Singapore", "rate": 181, "total": 10_500, "lat": 1.4, "lon": 103.8, "notes": "Mandatory death penalty for drug trafficking; caning still used"},
    {"country": "New Zealand", "rate": 148, "total": 7_700, "lat": -40.9, "lon": 174.9, "notes": "Maori 53 % of prisoners (16 % of population); reform efforts"},
    {"country": "Switzerland", "rate": 67, "total": 5_900, "lat": 46.8, "lon": 8.2, "notes": "Low rate; cantonal system; focus on resocialisation"},
    {"country": "Myanmar", "rate": 166, "total": 90_000, "lat": 21.9, "lon": 95.9, "notes": "Surge after 2021 coup; Insein Prison notorious; political detentions"},
]

# ═══════════════════════════════════════════════════════════════════════
# 5. HISTORIC DUNGEONS & FORTRESSES  (25 entries)
# ═══════════════════════════════════════════════════════════════════════
HISTORIC_DUNGEONS = [
    {"name": "Chateau d'If", "lat": 43.2800, "lon": 5.3250, "country": "France", "years": "1540-1890", "notes": "Island fortress off Marseille; made famous by Alexandre Dumas' novel"},
    {"name": "Spandau Citadel", "lat": 52.5397, "lon": 13.2111, "country": "Germany", "years": "12th century-present", "notes": "Renaissance fortress; held French prisoners in Napoleonic Wars; Rudolf Hess post-WWII"},
    {"name": "Devil's Island", "lat": 5.2944, "lon": -52.5833, "country": "French Guiana", "years": "1852-1953", "notes": "Dreyfus imprisoned 1895-1899; Henri Charriere (Papillon) escaped 1944"},
    {"name": "Hoa Lo Prison", "lat": 21.0254, "lon": 105.8467, "country": "Vietnam", "years": "1896-1993", "notes": "French colonial 'Maison Centrale'; American POWs called it Hanoi Hilton"},
    {"name": "Castel Sant'Angelo", "lat": 41.9031, "lon": 12.4663, "country": "Italy", "years": "139 AD-present", "notes": "Hadrian's mausoleum; papal fortress & prison; Benvenuto Cellini escaped"},
    {"name": "Chateau de Vincennes", "lat": 48.8428, "lon": 2.4353, "country": "France", "years": "1370-1784", "notes": "Held Marquis de Sade, Diderot, Mirabeau; 52m high donjon tower"},
    {"name": "Forte di San Leo", "lat": 43.8964, "lon": 12.3439, "country": "Italy", "years": "15th century-1906", "notes": "Hilltop fortress; Count Cagliostro died here 1795; impregnable location"},
    {"name": "Edinburgh Castle", "lat": 55.9486, "lon": -3.1999, "country": "Scotland", "years": "12th century+", "notes": "Held prisoners of war; vaults used as prison; Mary Queen of Scots"},
    {"name": "Doge's Palace (Piombi & Pozzi)", "lat": 45.4337, "lon": 12.3408, "country": "Italy", "years": "14th century+", "notes": "Lead-roofed Piombi cells and ground-level Pozzi dungeons; Casanova escaped 1756"},
    {"name": "Conciergerie", "lat": 48.8564, "lon": 2.3456, "country": "France", "years": "1370-1914", "notes": "Paris prison during Revolution; Marie Antoinette held here before execution"},
    {"name": "Fortress of Peter and Paul", "lat": 59.9500, "lon": 30.3167, "country": "Russia", "years": "1720-1921", "notes": "St Petersburg fortress; held Dostoevsky, Gorky, Trotsky; Trubetskoy Bastion"},
    {"name": "Spielberg Fortress", "lat": 49.1944, "lon": 16.5997, "country": "Czech Republic", "years": "1783-1855", "notes": "Brno fortress prison; Habsburg political prisoners; Silvio Pellico wrote 'Le Mie Prigioni'"},
    {"name": "Fort Boyard", "lat": 45.9997, "lon": -1.2139, "country": "France", "years": "1857-present", "notes": "Sea fortress; briefly used as prison; famous from TV game show"},
    {"name": "Castle of the Counts (Gravensteen)", "lat": 51.0575, "lon": 3.7206, "country": "Belgium", "years": "12th century+", "notes": "Ghent castle; used as prison and courthouse; torture instruments displayed"},
    {"name": "Carlsten Fortress", "lat": 57.8764, "lon": 11.4522, "country": "Sweden", "years": "1658-present", "notes": "Marstrand island; held political prisoners; last used as prison 1882"},
    {"name": "Wartburg Castle", "lat": 50.9667, "lon": 10.3069, "country": "Germany", "years": "1067-present", "notes": "Martin Luther 'imprisoned' here 1521-22 translating Bible; UNESCO site"},
    {"name": "Castell de Bellver", "lat": 39.5636, "lon": 2.6194, "country": "Spain", "years": "14th century+", "notes": "Circular castle in Mallorca; used as prison; held French POWs in 1800s"},
    {"name": "Rumeli Hisari", "lat": 41.0847, "lon": 29.0569, "country": "Turkey", "years": "1452-present", "notes": "Bosphorus fortress; built by Mehmed II; dungeon for prisoners of war"},
    {"name": "Yedikule Fortress", "lat": 41.0017, "lon": 28.9228, "country": "Turkey", "years": "1457-1831", "notes": "Istanbul fortress; held ambassadors and sultans; Tower of Inscriptions"},
    {"name": "Elmina Castle", "lat": 5.0833, "lon": -1.3500, "country": "Ghana", "years": "1482-present", "notes": "Portuguese slave castle; dungeons held enslaved Africans; UNESCO site"},
    {"name": "Cape Coast Castle", "lat": 5.1036, "lon": -1.2389, "country": "Ghana", "years": "1665-present", "notes": "British slave fort; 'Door of No Return'; now museum and UNESCO site"},
    {"name": "Goree Island", "lat": 14.6667, "lon": -17.4000, "country": "Senegal", "years": "17th century+", "notes": "Slave trading post; 'House of Slaves' museum; UNESCO site"},
    {"name": "Fort Santiago", "lat": 14.5953, "lon": 120.9706, "country": "Philippines", "years": "1571-1945", "notes": "Intramuros citadel; Jose Rizal imprisoned before execution; WWII atrocities"},
    {"name": "Cellular Jail", "lat": 11.6925, "lon": 92.7381, "country": "India", "years": "1906-1945", "notes": "Andaman Islands; British colonial prison for Indian independence activists"},
    {"name": "Old Melbourne Gaol", "lat": -37.8078, "lon": 144.9653, "country": "Australia", "years": "1842-1929", "notes": "Ned Kelly hanged here 1880; death masks collection; now museum"},
]

# ═══════════════════════════════════════════════════════════════════════
# 6. WAR CRIMES TRIBUNALS  (20 entries)
# ═══════════════════════════════════════════════════════════════════════
WAR_CRIMES_TRIBUNALS = [
    {"name": "Nuremberg Trials (Palace of Justice)", "lat": 49.4522, "lon": 11.0472, "country": "Germany", "years": "1945-1946", "type": "IMT", "notes": "Tried 24 major Nazi war criminals; established 'crimes against humanity'; Courtroom 600"},
    {"name": "International Criminal Court (ICC)", "lat": 52.0931, "lon": 4.3631, "country": "Netherlands", "years": "2002-present", "type": "Permanent court", "notes": "The Hague; permanent tribunal for genocide, war crimes, crimes against humanity"},
    {"name": "International Court of Justice (ICJ)", "lat": 52.0864, "lon": 4.2925, "country": "Netherlands", "years": "1945-present", "type": "UN principal organ", "notes": "Peace Palace, The Hague; settles disputes between states; advisory opinions"},
    {"name": "Tokyo War Crimes Tribunal (IMTFE)", "lat": 35.6938, "lon": 139.7461, "country": "Japan", "years": "1946-1948", "type": "Military tribunal", "notes": "Tried 28 Class A Japanese war criminals; General Tojo convicted; Ichigaya"},
    {"name": "ICTY (Yugoslavia Tribunal)", "lat": 52.0931, "lon": 4.3500, "country": "Netherlands", "years": "1993-2017", "type": "Ad hoc tribunal", "notes": "The Hague; tried Balkan war criminals; Milosevic, Karadzic, Mladic convicted"},
    {"name": "ICTR (Rwanda Tribunal)", "lat": -3.3731, "lon": 29.3644, "country": "Tanzania", "years": "1994-2015", "type": "Ad hoc tribunal", "notes": "Arusha; tried Rwandan genocide perpetrators; first conviction for genocide in int'l law"},
    {"name": "Extraordinary Chambers in the Courts of Cambodia (ECCC)", "lat": 11.5353, "lon": 104.8167, "country": "Cambodia", "years": "2006-2022", "type": "Hybrid tribunal", "notes": "Phnom Penh; tried senior Khmer Rouge leaders; Duch, Nuon Chea, Khieu Samphan"},
    {"name": "Special Court for Sierra Leone", "lat": 8.4844, "lon": -13.2344, "country": "Sierra Leone", "years": "2002-2013", "type": "Hybrid tribunal", "notes": "Freetown; Charles Taylor (Liberia) convicted; child soldiers accountability"},
    {"name": "Special Tribunal for Lebanon", "lat": 52.0708, "lon": 4.3569, "country": "Netherlands", "years": "2009-2023", "type": "Hybrid tribunal", "notes": "Leidschendam; Hariri assassination trial; first int'l tribunal for terrorism"},
    {"name": "Iraqi High Tribunal", "lat": 33.3152, "lon": 44.3661, "country": "Iraq", "years": "2004-2006", "type": "National tribunal", "notes": "Baghdad; tried Saddam Hussein for crimes against humanity; executed Dec 2006"},
    {"name": "International Residual Mechanism (IRMCT)", "lat": 52.0931, "lon": 4.3550, "country": "Netherlands/Tanzania", "years": "2010-present", "type": "UN mechanism", "notes": "Successor to ICTY/ICTR; handles residual functions, fugitive tracking"},
    {"name": "Kigali Gacaca Courts", "lat": -1.9536, "lon": 30.0606, "country": "Rwanda", "years": "2005-2012", "type": "Community courts", "notes": "12,000 community courts tried 1.9 million genocide suspects; transitional justice"},
    {"name": "East Timor Special Panels", "lat": -8.5569, "lon": 125.5603, "country": "East Timor", "years": "2000-2006", "type": "Hybrid tribunal", "notes": "Dili District Court; tried crimes from 1999 independence violence"},
    {"name": "Bangladesh International Crimes Tribunal", "lat": 23.7104, "lon": 90.4074, "country": "Bangladesh", "years": "2010-present", "type": "National tribunal", "notes": "Dhaka; trying 1971 Liberation War crimes; controversial death sentences"},
    {"name": "African Court on Human and Peoples' Rights", "lat": -3.3869, "lon": 36.6828, "country": "Tanzania", "years": "2006-present", "type": "Regional court", "notes": "Arusha; African Union court; handles human rights violations across Africa"},
    {"name": "European Court of Human Rights", "lat": 48.5964, "lon": 7.7706, "country": "France", "years": "1959-present", "type": "Regional court", "notes": "Strasbourg; Council of Europe; binding judgments on 46 member states"},
    {"name": "Inter-American Court of Human Rights", "lat": 9.9356, "lon": -84.0483, "country": "Costa Rica", "years": "1979-present", "type": "Regional court", "notes": "San Jose; OAS court; landmark rulings on forced disappearances, indigenous rights"},
    {"name": "Nuremberg Subsequent Trials", "lat": 49.4522, "lon": 11.0472, "country": "Germany", "years": "1946-1949", "type": "US military tribunals", "notes": "12 subsequent trials: Doctors' Trial, Judges' Trial, IG Farben, Einsatzgruppen etc."},
    {"name": "Dachau War Crimes Trials", "lat": 48.2700, "lon": 11.4683, "country": "Germany", "years": "1945-1947", "type": "US military tribunal", "notes": "Tried staff of Buchenwald, Mauthausen, Flossenburg, Dachau; 1,672 tried, 297 executed"},
    {"name": "Kosovo Specialist Chambers", "lat": 52.0931, "lon": 4.3600, "country": "Netherlands", "years": "2017-present", "type": "Hybrid tribunal", "notes": "The Hague; trying KLA leaders for war crimes; Thaci indicted"},
]

# ═══════════════════════════════════════════════════════════════════════
# 7. GREAT ESCAPES  (20 entries)
# ═══════════════════════════════════════════════════════════════════════
GREAT_ESCAPES = [
    {"name": "Alcatraz 1962 (Anglin brothers & Morris)", "lat": 37.8267, "lon": -122.4233, "year": 1962, "prison": "Alcatraz", "notes": "Dug through walls with spoons; raft from raincoats; presumed drowned but bodies never found"},
    {"name": "Colditz Glider Escape Plan", "lat": 51.1308, "lon": 12.8139, "year": 1945, "prison": "Colditz Castle", "notes": "British POWs built glider in attic from bedsheets and floorboards; war ended before launch"},
    {"name": "The Great Escape (Stalag Luft III)", "lat": 51.5883, "lon": 15.1672, "year": 1944, "prison": "Stalag Luft III", "notes": "76 escaped through tunnel 'Harry'; 73 recaptured; 50 executed by Gestapo; 3 reached freedom"},
    {"name": "Maze Prison Mass Escape", "lat": 54.4928, "lon": -6.0978, "year": 1983, "prison": "Maze (Long Kesh)", "notes": "38 IRA prisoners escaped in food delivery truck; largest UK prison escape; 1 guard killed"},
    {"name": "Papillon (Henri Charriere)", "lat": 5.2944, "lon": -52.5833, "year": 1944, "prison": "Devil's Island", "notes": "Escaped on coconut-sack raft; reached Venezuela after multiple attempts; bestselling memoir"},
    {"name": "Casanova's Escape from the Piombi", "lat": 45.4337, "lon": 12.3408, "year": 1756, "prison": "Doge's Palace", "notes": "Broke through lead roof with iron spike; crossed rooftops; walked out main door at dawn"},
    {"name": "John Dillinger's Wooden Gun Escape", "lat": 41.4647, "lon": -87.3500, "year": 1934, "prison": "Crown Point Jail", "notes": "Bluffed guards with hand-carved wooden gun blackened with shoe polish; stole sheriff's car"},
    {"name": "Libby Prison Tunnel Escape", "lat": 37.5314, "lon": -77.4367, "year": 1864, "prison": "Libby Prison", "notes": "109 Union officers tunneled out of Confederate prison in Richmond; 59 reached Union lines"},
    {"name": "Pascal Payet Helicopter Escapes", "lat": 43.2965, "lon": 5.3698, "year": 2001, "prison": "Luynes Prison", "notes": "Escaped by helicopter three times (2001, 2003, 2007) from French prisons; eventually recaptured"},
    {"name": "El Chapo Tunnel Escape", "lat": 20.5083, "lon": -103.3833, "year": 2015, "prison": "Altiplano Prison", "notes": "Escaped through 1.5 km tunnel from shower to construction site; motorcycle on rails; recaptured 2016"},
    {"name": "Roger Bushell (Big X) Stalag Luft III", "lat": 51.5883, "lon": 15.1672, "year": 1944, "prison": "Stalag Luft III", "notes": "Mastermind of The Great Escape; organised 600 men; executed by Gestapo after recapture"},
    {"name": "Jack Sheppard's Four Escapes", "lat": 51.5155, "lon": -0.1005, "year": 1724, "prison": "Newgate Prison", "notes": "Escaped Newgate four times; folk hero of 18th-century London; eventually hanged at Tyburn"},
    {"name": "Billy Hayes (Midnight Express)", "lat": 40.9833, "lon": 28.8167, "year": 1975, "prison": "Imrali Island Prison", "notes": "American smuggler escaped Turkish prison; swam to fishing boat; memoir became famous film"},
    {"name": "Texas Seven Prison Break", "lat": 31.0833, "lon": -97.2500, "year": 2000, "prison": "Connally Unit", "notes": "7 inmates overpowered guards; stole weapons; 6 weeks on run; all captured; 4 executed"},
    {"name": "Dannemora Prison Escape (2015)", "lat": 44.7211, "lon": -73.7228, "year": 2015, "prison": "Clinton Correctional", "notes": "Richard Matt & David Sweat cut through steel and tunneled out; prison employee smuggled tools"},
    {"name": "Dieter Dengler Vietnam Escape", "lat": 19.8, "lon": 102.2, "year": 1966, "prison": "Pathet Lao camp", "notes": "US Navy pilot escaped Laotian POW camp; survived 23 days in jungle; rescued by helicopter"},
    {"name": "Airey Neave Colditz Escape", "lat": 51.1308, "lon": 12.8139, "year": 1942, "prison": "Colditz Castle", "notes": "First British officer to escape Colditz and reach home; through theatre trapdoor in German uniform"},
    {"name": "Berlin Wall Tunnel 57", "lat": 52.5350, "lon": 13.3950, "year": 1964, "prison": "East Berlin", "notes": "Students dug 145m tunnel; 57 East Germans escaped to West in two nights; largest tunnel escape"},
    {"name": "Bastille Break-In Reverse", "lat": 48.8532, "lon": 2.3692, "year": 1789, "prison": "Bastille", "notes": "Not an escape but a mass break-in; storming freed 7 prisoners; sparked French Revolution"},
    {"name": "Frank Abagnale Jr.", "lat": 40.6413, "lon": -73.7781, "year": 1971, "prison": "Federal Detention Center", "notes": "Con artist escaped federal custody twice; posed as pilot, doctor, lawyer; inspiration for Catch Me If You Can"},
]

# ═══════════════════════════════════════════════════════════════════════
# 8. DEATH PENALTY MAP  (60 countries)
# ═══════════════════════════════════════════════════════════════════════
DEATH_PENALTY_DATA = [
    {"country": "China", "lat": 35.9, "lon": 104.2, "status": "Retentionist", "method": "Lethal injection / shooting", "notes": "Estimated 1,000+ executions/year; exact figures state secret"},
    {"country": "Iran", "lat": 32.4, "lon": 53.7, "status": "Retentionist", "method": "Hanging", "notes": "Second highest executions globally; drug offences, political crimes"},
    {"country": "Saudi Arabia", "lat": 24.0, "lon": 45.0, "status": "Retentionist", "method": "Beheading", "notes": "Public executions; drug trafficking, murder, apostasy, sorcery"},
    {"country": "Egypt", "lat": 26.8, "lon": 30.8, "status": "Retentionist", "method": "Hanging", "notes": "Mass death sentences post-2013; political cases"},
    {"country": "Iraq", "lat": 33.2, "lon": 43.7, "status": "Retentionist", "method": "Hanging", "notes": "Terrorism-related executions; Saddam Hussein hanged 2006"},
    {"country": "United States", "lat": 39.8, "lon": -98.5, "status": "Retentionist", "method": "Lethal injection / various", "notes": "27 states retain; federal moratorium 2021; 1,600+ executions since 1976"},
    {"country": "Pakistan", "lat": 30.4, "lon": 69.3, "status": "Retentionist", "method": "Hanging", "notes": "Resumed 2014 after Peshawar school massacre; blasphemy cases"},
    {"country": "Vietnam", "lat": 14.1, "lon": 108.3, "status": "Retentionist", "method": "Lethal injection", "notes": "Drug trafficking main offence; switched from firing squad 2011"},
    {"country": "Japan", "lat": 36.2, "lon": 138.3, "status": "Retentionist", "method": "Hanging", "notes": "Inmates not told execution date until morning; strong public support"},
    {"country": "India", "lat": 20.6, "lon": 79.0, "status": "Retentionist", "method": "Hanging", "notes": "'Rarest of rare' doctrine; few executions; last in 2020"},
    {"country": "Singapore", "lat": 1.4, "lon": 103.8, "status": "Retentionist", "method": "Hanging", "notes": "Mandatory death for drug trafficking; controversial executions of foreigners"},
    {"country": "North Korea", "lat": 40.3, "lon": 127.5, "status": "Retentionist", "method": "Firing squad / hanging", "notes": "Public executions; anti-aircraft guns reported; political crimes"},
    {"country": "Belarus", "lat": 53.7, "lon": 27.9, "status": "Retentionist", "method": "Shooting", "notes": "Last country in Europe with death penalty; shot in back of head"},
    {"country": "Somalia", "lat": 5.2, "lon": 46.2, "status": "Retentionist", "method": "Firing squad", "notes": "Al-Shabaab also carries out executions; limited rule of law"},
    {"country": "South Sudan", "lat": 6.9, "lon": 31.3, "status": "Retentionist", "method": "Hanging / shooting", "notes": "Armed conflict; limited judicial system; military executions"},
    {"country": "Syria", "lat": 35.0, "lon": 38.5, "status": "Retentionist", "method": "Hanging", "notes": "Mass executions at Saydnaya prison; Amnesty documented thousands"},
    {"country": "Yemen", "lat": 15.6, "lon": 48.5, "status": "Retentionist", "method": "Shooting / stoning", "notes": "Active conflict; Houthi authorities also execute"},
    {"country": "Thailand", "lat": 15.0, "lon": 100.0, "status": "Retentionist", "method": "Lethal injection", "notes": "Rare use; last execution 2018 after 9-year hiatus"},
    {"country": "Nigeria", "lat": 9.1, "lon": 8.7, "status": "Retentionist", "method": "Hanging / shooting", "notes": "Sharia courts in north; large death row; few executions"},
    {"country": "Bangladesh", "lat": 23.7, "lon": 90.4, "status": "Retentionist", "method": "Hanging", "notes": "War crimes executions; drug trafficking; political killings"},
    {"country": "Germany", "lat": 51.2, "lon": 10.4, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 1949 (West) / 1987 (East); constitutional prohibition"},
    {"country": "France", "lat": 46.2, "lon": 2.2, "status": "Abolitionist", "method": "N/A", "notes": "Last execution 1977 (guillotine); abolished 1981 by Mitterrand"},
    {"country": "United Kingdom", "lat": 55.4, "lon": -3.4, "status": "Abolitionist", "method": "N/A", "notes": "Abolished for murder 1969; completely 1998; last hanging 1964"},
    {"country": "Canada", "lat": 56.1, "lon": -106.3, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 1976; last execution 1962; constitutional prohibition"},
    {"country": "Australia", "lat": -25.3, "lon": 133.8, "status": "Abolitionist", "method": "N/A", "notes": "Last execution 1967 (Ronald Ryan); federal abolition 1973; all states by 1985"},
    {"country": "Brazil", "lat": -14.2, "lon": -51.9, "status": "Abolitionist", "method": "N/A", "notes": "Abolished for ordinary crimes 1979; peacetime since 1876; last execution 1876"},
    {"country": "South Africa", "lat": -30.6, "lon": 22.9, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 1995 by Constitutional Court; apartheid-era executions high"},
    {"country": "Mexico", "lat": 23.6, "lon": -102.5, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 2005; constitutional amendment; last execution 1961"},
    {"country": "Italy", "lat": 41.9, "lon": 12.6, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 1948 (civilian); 1994 (military); European Convention signatory"},
    {"country": "Spain", "lat": 40.5, "lon": -3.7, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 1978; last execution by garrote 1974; democratic constitution"},
    {"country": "Poland", "lat": 51.9, "lon": 19.1, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 1997; last execution 1988; EU accession requirement"},
    {"country": "Russia", "lat": 61.5, "lon": 105.3, "status": "Moratorium", "method": "Shooting (suspended)", "notes": "Moratorium since 1996; Constitutional Court extended; last execution 1996"},
    {"country": "South Korea", "lat": 35.9, "lon": 127.8, "status": "Moratorium", "method": "Hanging (suspended)", "notes": "De facto abolitionist since 1997; death row exists but no executions"},
    {"country": "Kenya", "lat": -0.0, "lon": 37.9, "status": "Moratorium", "method": "Hanging (suspended)", "notes": "Last execution 1987; courts still sentence but not carried out"},
    {"country": "Tanzania", "lat": -6.4, "lon": 34.9, "status": "Moratorium", "method": "Hanging (suspended)", "notes": "Last execution 1994; large death row; commutations common"},
    {"country": "Algeria", "lat": 28.0, "lon": 1.7, "status": "Moratorium", "method": "N/A (suspended)", "notes": "Last execution 1993; de facto abolitionist; courts still sentence"},
    {"country": "Morocco", "lat": 31.8, "lon": -7.1, "status": "Moratorium", "method": "N/A (suspended)", "notes": "Last execution 1993; death sentences still issued; no executions"},
    {"country": "Myanmar", "lat": 21.9, "lon": 95.9, "status": "Retentionist", "method": "Hanging", "notes": "Resumed executions 2022 after 30+ years; political activists executed"},
    {"country": "Malaysia", "lat": 4.2, "lon": 101.9, "status": "Abolitionist", "method": "N/A", "notes": "Abolished mandatory death penalty 2023; replaced with discretionary sentencing"},
    {"country": "Indonesia", "lat": -0.8, "lon": 113.9, "status": "Retentionist", "method": "Firing squad", "notes": "Drug trafficking executions of foreigners controversial; Bali Nine case"},
    {"country": "Norway", "lat": 60.5, "lon": 8.5, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 1979; last execution 1948 (war crimes); 21-year max sentence"},
    {"country": "Sweden", "lat": 60.1, "lon": 18.6, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 1921 (peacetime); 1973 (all); last execution 1910"},
    {"country": "Netherlands", "lat": 52.1, "lon": 5.3, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 1870 (civilian); 1983 (all); last execution 1952 (war crimes)"},
    {"country": "Cuba", "lat": 21.5, "lon": -80.0, "status": "Retentionist", "method": "Firing squad / lethal injection", "notes": "Last known execution 2003; de facto moratorium since then"},
    {"country": "Afghanistan", "lat": 33.9, "lon": 67.7, "status": "Retentionist", "method": "Shooting / hanging / stoning", "notes": "Taliban resumed public executions; sharia law; no due process"},
    {"country": "Jordan", "lat": 30.6, "lon": 36.2, "status": "Retentionist", "method": "Hanging", "notes": "Resumed 2014 after 8-year moratorium; terrorism-related cases"},
    {"country": "Taiwan", "lat": 23.7, "lon": 121.0, "status": "Retentionist", "method": "Shooting / lethal injection", "notes": "Few executions per year; public debate on abolition ongoing"},
    {"country": "Philippines", "lat": 12.9, "lon": 121.8, "status": "Abolitionist", "method": "N/A", "notes": "Abolished 2006; reinstated then abolished again; Duterte pushed for revival"},
    {"country": "Ethiopia", "lat": 9.1, "lon": 40.5, "status": "Retentionist", "method": "Hanging", "notes": "Rare use; political dimensions; Derg-era mass executions"},
    {"country": "Libya", "lat": 26.3, "lon": 17.2, "status": "Retentionist", "method": "Firing squad / hanging", "notes": "Chaotic judicial system; militia executions; limited rule of law"},
]

# ═══════════════════════════════════════════════════════════════════════
# 9. POLITICAL PRISONERS  (25 entries)
# ═══════════════════════════════════════════════════════════════════════
POLITICAL_PRISONERS = [
    {"name": "Nelson Mandela", "lat": -33.8060, "lon": 18.3664, "country": "South Africa", "years": "1962-1990", "notes": "27 years imprisoned; Robben Island & Pollsmoor; Nobel Peace Prize 1993; became president"},
    {"name": "Aung San Suu Kyi", "lat": 16.8409, "lon": 96.1735, "country": "Myanmar", "years": "1989-2010 (intermittent)", "notes": "15 years house arrest; Nobel Peace Prize 1991; later controversial as leader; imprisoned again 2021"},
    {"name": "Liu Xiaobo", "lat": 41.8, "lon": 123.4, "country": "China", "years": "2008-2017", "notes": "Charter 08 democracy manifesto; Nobel Peace Prize 2010 (empty chair); died in custody of liver cancer"},
    {"name": "Vaclav Havel", "lat": 50.0755, "lon": 14.4378, "country": "Czechoslovakia", "years": "1977-1989 (intermittent)", "notes": "Dissident playwright; Charter 77; 5 years total in prison; became president after Velvet Revolution"},
    {"name": "Alexei Navalny", "lat": 67.5, "lon": 64.0, "country": "Russia", "years": "2021-2024", "notes": "Opposition leader; poisoned with Novichok 2020; died in Arctic penal colony IK-3 Feb 2024"},
    {"name": "Andrei Sakharov", "lat": 56.3287, "lon": 44.0, "country": "Soviet Union", "years": "1980-1986", "notes": "Nuclear physicist; internal exile in Gorky; Nobel Peace Prize 1975; father of Soviet H-bomb"},
    {"name": "Mahatma Gandhi", "lat": 18.9220, "lon": 72.8347, "country": "India", "years": "1922-1944 (intermittent)", "notes": "Multiple imprisonments by British; total ~6 years; Aga Khan Palace, Yeravda Jail"},
    {"name": "Martin Luther King Jr.", "lat": 33.5207, "lon": -86.8025, "country": "USA", "years": "1963", "notes": "Birmingham Jail; wrote 'Letter from Birmingham Jail'; arrested 30+ times for civil rights"},
    {"name": "Lech Walesa", "lat": 54.3520, "lon": 18.6466, "country": "Poland", "years": "1981-1982", "notes": "Solidarity leader; interned under martial law; Nobel Peace Prize 1983; became president"},
    {"name": "Wole Soyinka", "lat": 7.3775, "lon": 3.9470, "country": "Nigeria", "years": "1967-1969", "notes": "Nigerian playwright; 22 months solitary confinement during Biafra war; Nobel Literature 1986"},
    {"name": "Natan Sharansky", "lat": 55.7558, "lon": 37.6173, "country": "Soviet Union", "years": "1977-1986", "notes": "Jewish dissident; charged with spying for US; 9 years in Gulag; released in prisoner swap"},
    {"name": "Jacobo Timerman", "lat": -34.6037, "lon": -58.3816, "country": "Argentina", "years": "1977-1979", "notes": "Newspaper editor; imprisoned and tortured during Dirty War; wrote 'Prisoner Without a Name'"},
    {"name": "Kim Dae-jung", "lat": 37.5665, "lon": 126.9780, "country": "South Korea", "years": "1980-1982", "notes": "Death sentence commuted; exiled; Nobel Peace Prize 2000; became president; Gwangju connection"},
    {"name": "Leyla Yunus", "lat": 40.4093, "lon": 49.8671, "country": "Azerbaijan", "years": "2014-2015", "notes": "Human rights defender; charged with treason; released after international pressure"},
    {"name": "Nasrin Sotoudeh", "lat": 35.6892, "lon": 51.3890, "country": "Iran", "years": "2010-2013, 2018-present", "notes": "Human rights lawyer; defended women removing hijab; 38-year sentence + 148 lashes"},
    {"name": "Ales Bialiatski", "lat": 53.9045, "lon": 27.5615, "country": "Belarus", "years": "2021-present", "notes": "Human rights activist; Nobel Peace Prize 2022 (while in prison); Viasna centre founder"},
    {"name": "Antonio Gramsci", "lat": 41.9028, "lon": 12.4964, "country": "Italy", "years": "1926-1937", "notes": "Communist philosopher; imprisoned by Mussolini; wrote Prison Notebooks; died shortly after release"},
    {"name": "Oscar Wilde", "lat": 51.5400, "lon": -0.1831, "country": "England", "years": "1895-1897", "notes": "Imprisoned for 'gross indecency'; Reading Gaol; wrote De Profundis and Ballad of Reading Gaol"},
    {"name": "Dietrich Bonhoeffer", "lat": 49.7322, "lon": 12.3536, "country": "Germany", "years": "1943-1945", "notes": "Lutheran pastor; anti-Nazi conspirator; hanged at Flossenburg weeks before liberation"},
    {"name": "Alfred Dreyfus", "lat": 5.2944, "lon": -52.5833, "country": "France", "years": "1894-1899", "notes": "French Army officer; wrongly convicted of treason; Devil's Island; Dreyfus Affair divided France"},
    {"name": "Bobby Sands", "lat": 54.4928, "lon": -6.0978, "country": "Northern Ireland", "years": "1977-1981", "notes": "IRA member; elected MP while in Maze Prison; died on hunger strike after 66 days"},
    {"name": "Fyodor Dostoevsky", "lat": 55.1, "lon": 73.4, "country": "Russia", "years": "1849-1854", "notes": "Mock execution; 4 years hard labour in Omsk; transformed his writing; wrote Notes from a Dead House"},
    {"name": "Ngugi wa Thiong'o", "lat": -1.2864, "lon": 36.8172, "country": "Kenya", "years": "1977-1978", "notes": "Kenyan writer; detained without trial; wrote novel on toilet paper in prison; Devil on the Cross"},
    {"name": "Primo Levi", "lat": 50.0343, "lon": 19.1781, "country": "Italy/Poland", "years": "1944-1945", "notes": "Italian chemist; survived Auschwitz; wrote If This Is a Man; testimony against dehumanisation"},
    {"name": "Ai Weiwei", "lat": 39.9042, "lon": 116.4074, "country": "China", "years": "2011 (81 days)", "notes": "Artist and activist; detained without charge; passport confiscated until 2015; now in exile"},
]

# ═══════════════════════════════════════════════════════════════════════
# 10. JUSTICE & COURT SYSTEMS  (30 entries)
# ═══════════════════════════════════════════════════════════════════════
JUSTICE_COURTS = [
    {"name": "US Supreme Court", "lat": 38.8907, "lon": -77.0046, "country": "USA", "tradition": "Common law", "notes": "9 justices; judicial review since Marbury v Madison 1803; 1 First Street NE"},
    {"name": "Royal Courts of Justice", "lat": 51.5137, "lon": -0.1134, "country": "England", "tradition": "Common law", "notes": "Strand, London; High Court & Court of Appeal; Gothic Revival; opened 1882"},
    {"name": "Supreme Court of India", "lat": 28.6225, "lon": 77.2400, "country": "India", "tradition": "Common law / Hindu law", "notes": "31 justices; world's most powerful judiciary; Public Interest Litigation"},
    {"name": "Palais de Justice (Paris)", "lat": 48.8556, "lon": 2.3450, "country": "France", "tradition": "Civil law (Napoleonic)", "notes": "Ile de la Cite; Cour de Cassation; 700+ years of French justice; adjacent Conciergerie"},
    {"name": "Federal Constitutional Court (Karlsruhe)", "lat": 49.0122, "lon": 8.4017, "country": "Germany", "tradition": "Civil law", "notes": "Guardian of Basic Law; two senates of 8 judges each; powerful constitutional review"},
    {"name": "International Court of Justice", "lat": 52.0864, "lon": 4.2925, "country": "Netherlands", "tradition": "International law", "notes": "Peace Palace, The Hague; 15 judges; settles state disputes; advisory opinions for UN"},
    {"name": "Supreme Court of Canada", "lat": 45.4215, "lon": -75.7100, "country": "Canada", "tradition": "Common law / Civil law (Quebec)", "notes": "Ottawa; 9 justices; bijural system; Charter of Rights decisions"},
    {"name": "High Court of Australia", "lat": -35.2997, "lon": 149.1383, "country": "Australia", "tradition": "Common law", "notes": "Canberra; 7 justices; Mabo decision 1992 recognised native title"},
    {"name": "Constitutional Court of South Africa", "lat": -26.1917, "lon": 28.0436, "country": "South Africa", "tradition": "Mixed (Roman-Dutch / Common)", "notes": "Johannesburg; on site of Old Fort Prison; abolished death penalty 1995"},
    {"name": "Supreme Court of Japan", "lat": 35.6814, "lon": 139.7467, "country": "Japan", "tradition": "Civil law (German-influenced)", "notes": "Tokyo; 15 justices; 99.9 % conviction rate; rare judicial review"},
    {"name": "Supreme People's Court of China", "lat": 39.9154, "lon": 116.4081, "country": "China", "tradition": "Socialist civil law", "notes": "Beijing; final appellate court; reviews all death sentences since 2007"},
    {"name": "Federal Supreme Court of Brazil", "lat": -15.7989, "lon": -47.8622, "country": "Brazil", "tradition": "Civil law", "notes": "Brasilia; 11 ministers; Niemeyer building; live-streamed sessions"},
    {"name": "Supreme Court of Israel", "lat": 31.7808, "lon": 35.2025, "country": "Israel", "tradition": "Mixed (common/civil/religious)", "notes": "Jerusalem; landmark human rights rulings; architectural pyramid design"},
    {"name": "Constitutional Court of Italy", "lat": 41.8969, "lon": 12.4828, "country": "Italy", "tradition": "Civil law", "notes": "Palazzo della Consulta, Rome; 15 judges; reviews constitutionality of laws"},
    {"name": "Supreme Court of the United Kingdom", "lat": 51.5014, "lon": -0.1307, "country": "UK", "tradition": "Common law", "notes": "Middlesex Guildhall; established 2009 replacing Law Lords; 12 justices"},
    {"name": "Cour de Cassation", "lat": 48.8556, "lon": 2.3450, "country": "France", "tradition": "Civil law", "notes": "Highest court of ordinary jurisdiction; Palais de Justice; ~150 judges"},
    {"name": "Spanish Constitutional Court", "lat": 40.4168, "lon": -3.7038, "country": "Spain", "tradition": "Civil law", "notes": "Madrid; 12 members; Catalan independence crisis rulings; Pedro Sanchez reforms"},
    {"name": "Supreme Court of Nigeria", "lat": 9.0579, "lon": 7.4951, "country": "Nigeria", "tradition": "Common law / Sharia / Customary", "notes": "Abuja; dual system: secular and sharia courts in northern states"},
    {"name": "Supreme Court of Mexico", "lat": 19.4326, "lon": -99.1332, "country": "Mexico", "tradition": "Civil law", "notes": "Mexico City; 11 ministers; murals by Orozco; amparo (protection) writs"},
    {"name": "Federal Court of Switzerland", "lat": 46.5197, "lon": 6.6323, "country": "Switzerland", "tradition": "Civil law", "notes": "Lausanne; 38 judges; four official languages; limited constitutional review"},
    {"name": "Supreme Court of Norway", "lat": 59.9139, "lon": 10.7522, "country": "Norway", "tradition": "Civil law (Nordic)", "notes": "Oslo; 20 justices; Breivik trial 2012; maximum 21-year sentence"},
    {"name": "Supreme Administrative Court of Egypt", "lat": 30.0444, "lon": 31.2357, "country": "Egypt", "tradition": "Civil law (French-influenced)", "notes": "Cairo; Conseil d'Etat model; administrative justice since 1946"},
    {"name": "Supreme Court of South Korea", "lat": 37.4695, "lon": 127.0139, "country": "South Korea", "tradition": "Civil law (German/Japanese)", "notes": "Seoul; 14 justices; Constitutional Court separate; presidential impeachment 2017"},
    {"name": "Supreme Federal Court of Germany", "lat": 49.0069, "lon": 8.4037, "country": "Germany", "tradition": "Civil law", "notes": "Bundesgerichtshof, Karlsruhe; highest court for civil and criminal cases"},
    {"name": "Court of Final Appeal (Hong Kong)", "lat": 22.2808, "lon": 114.1603, "country": "Hong Kong", "tradition": "Common law", "notes": "Former Legislative Council building; British legal tradition; foreign judges sit"},
    {"name": "Supreme Court of Indonesia", "lat": -6.1753, "lon": 106.8272, "country": "Indonesia", "tradition": "Civil law / Adat / Sharia", "notes": "Jakarta; pluralistic legal system; religious courts for Muslim family law"},
    {"name": "Federal Supreme Court of Ethiopia", "lat": 9.0192, "lon": 38.7525, "country": "Ethiopia", "tradition": "Civil law", "notes": "Addis Ababa; federal and regional courts; customary and religious tribunals"},
    {"name": "Supreme Court of Argentina", "lat": -34.6037, "lon": -58.3816, "country": "Argentina", "tradition": "Civil law", "notes": "Buenos Aires; 5 members; Dirty War trials; constitutional review powers"},
    {"name": "Supreme Court of the Philippines", "lat": 14.5946, "lon": 121.0042, "country": "Philippines", "tradition": "Mixed (civil/common)", "notes": "Manila; 15 justices; influenced by US and Spanish legal traditions"},
    {"name": "Supreme Court of Kenya", "lat": -1.2821, "lon": 36.8219, "country": "Kenya", "tradition": "Common law / Customary", "notes": "Nairobi; 2010 constitution; nullified presidential election 2017 -- African first"},
]


# ═══════════════════════════════════════════════════════════════════════
# HELPER: safe HTML for popups
# ═══════════════════════════════════════════════════════════════════════
def _esc(text):
    """Escape user-provided strings for safe HTML embedding."""
    return _html.escape(str(text))


# ═══════════════════════════════════════════════════════════════════════
# HELPER: render folium map in Streamlit
# ═══════════════════════════════════════════════════════════════════════
def _show_map(m, height=500):
    components.html(m._repr_html_(), height=height)


# ═══════════════════════════════════════════════════════════════════════
# HELPER: CSV download button
# ═══════════════════════════════════════════════════════════════════════
def _csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, buf.getvalue(), file_name=filename, mime="text/csv")


# ═══════════════════════════════════════════════════════════════════════
# HELPER: matplotlib dark defaults
# ═══════════════════════════════════════════════════════════════════════
def _dark_fig(rows=1, cols=1, figsize=(10, 5)):
    fig, axes = plt.subplots(rows, cols, figsize=figsize)
    fig.patch.set_facecolor(_BG)
    if rows * cols == 1:
        axes = [axes]
    for ax in (axes if isinstance(axes, list) else axes.flat):
        ax.set_facecolor(_SURFACE)
        ax.tick_params(colors=_TEXT, labelsize=8)
        ax.xaxis.label.set_color(_TEXT)
        ax.yaxis.label.set_color(_TEXT)
        ax.title.set_color(_TEXT)
        for spine in ax.spines.values():
            spine.set_color(_MUTED)
    return fig, axes if rows * cols > 1 else axes[0]


# ═══════════════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════════════

def _render_famous_prisons():
    st.markdown("#### World's Most Famous Prisons")
    st.info(
        "From Alcatraz to Tuol Sleng -- a curated tour of 30 of the world's most "
        "notorious, historic, and significant prisons across six continents."
    )
    df = pd.DataFrame(FAMOUS_PRISONS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Prisons mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Still operating", sum(1 for r in FAMOUS_PRISONS if "present" in r["years"]))

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    cluster = MarkerCluster(name="Famous Prisons").add_to(m)
    for r in FAMOUS_PRISONS:
        popup = (
            f"<b>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['years'])}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
            icon=folium.Icon(color="red", icon="lock", prefix="fa"),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["name", "country", "years", "notes"]], width="stretch")
    _csv_download(df, "famous_prisons.csv")


def _render_holocaust():
    st.markdown("#### Holocaust Memorial Sites")
    st.info(
        "Concentration camps, extermination camps, transit camps, and memorials -- "
        "30 sites commemorating the Holocaust and its estimated 6 million Jewish victims."
    )
    df = pd.DataFrame(HOLOCAUST_SITES)
    types = df["type"].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.metric("Sites mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Site types", len(types))

    # Chart: sites by type
    fig, ax = _dark_fig(figsize=(8, 4))
    colors = ["#dc2626", "#f97316", "#eab308", "#22c55e", "#06b6d4", "#8b5cf6"]
    types.plot.barh(ax=ax, color=colors[:len(types)])
    ax.set_title("Holocaust Sites by Type")
    ax.set_xlabel("Count")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    _type_colors = {
        "Death camp": "red",
        "Concentration camp": "darkred",
        "Transit camp": "orange",
        "Ghetto/Transit camp": "orange",
        "Memorial/Museum": "blue",
        "Memorial": "purple",
        "Transit camp/Museum": "cadetblue",
    }
    m = folium.Map(location=[50, 15], zoom_start=4, tiles="CartoDB dark_matter")
    for r in HOLOCAUST_SITES:
        clr = _type_colors.get(r["type"], "gray")
        popup = (
            f"<b>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['type'])}<br>"
            f"Est. deaths: {_esc(r['est_deaths'])}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(popup, max_width=320),
            tooltip=_esc(r["name"]),
            icon=folium.Icon(color=clr, icon="star-of-david", prefix="fa"),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "type", "est_deaths", "notes"]], width="stretch")
    _csv_download(df, "holocaust_sites.csv")


def _render_gulag():
    st.markdown("#### Gulag Archipelago")
    st.info(
        "The Soviet forced-labour camp system imprisoned an estimated 18 million people "
        "between 1930 and 1953. This map plots 30 major camp locations from Solovetsky to Kolyma."
    )
    df = pd.DataFrame(GULAG_CAMPS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Camps mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Estimated total Gulag deaths", "1.5-1.8 million")

    m = folium.Map(location=[60, 80], zoom_start=3, tiles="CartoDB dark_matter")
    for r in GULAG_CAMPS:
        popup = (
            f"<b>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['years'])}<br>"
            f"Prisoners: {_esc(r['est_prisoners'])}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=8,
            color="#dc2626",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=320),
            tooltip=_esc(r["name"]),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "years", "est_prisoners", "notes"]], width="stretch")
    _csv_download(df, "gulag_camps.csv")


def _render_incarceration():
    st.markdown("#### Incarceration Rates by Country")
    st.info(
        "Prison population rates per 100,000 inhabitants and total numbers for 50 countries. "
        "Data compiled from World Prison Brief and national statistics (2024 estimates)."
    )
    df = pd.DataFrame(INCARCERATION_DATA)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", len(df))
    c2.metric("Highest rate", f"{df['rate'].max()} per 100k")
    c3.metric("Lowest rate", f"{df['rate'].min()} per 100k")
    c4.metric("Total prisoners", f"{df['total'].sum():,.0f}")

    # Top 15 bar chart
    top = df.nlargest(15, "rate")
    fig, ax = _dark_fig(figsize=(10, 5))
    bars = ax.barh(top["country"][::-1], top["rate"][::-1], color="#ef4444")
    ax.set_xlabel("Prisoners per 100,000 population")
    ax.set_title("Top 15 Incarceration Rates")
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 5, bar.get_y() + bar.get_height() / 2, f"{w:.0f}",
                va="center", color=_TEXT, fontsize=8)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # Map
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    max_rate = df["rate"].max()
    for r in INCARCERATION_DATA:
        ratio = r["rate"] / max_rate
        if ratio > 0.6:
            clr = "#dc2626"
        elif ratio > 0.3:
            clr = "#f97316"
        else:
            clr = "#22c55e"
        radius = max(5, ratio * 25)
        popup = (
            f"<b>{_esc(r['country'])}</b><br>"
            f"Rate: {_esc(r['rate'])} per 100k<br>"
            f"Total: {r['total']:,}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=radius,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.65,
            popup=folium.Popup(popup, max_width=300),
            tooltip=f"{_esc(r['country'])}: {r['rate']}/100k",
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["country", "rate", "total", "notes"]], width="stretch")
    _csv_download(df, "incarceration_rates.csv")


def _render_dungeons():
    st.markdown("#### Historic Dungeons & Fortresses")
    st.info(
        "25 legendary fortresses, castles, and dungeons that served as prisons throughout "
        "history -- from medieval keeps to colonial slave forts."
    )
    df = pd.DataFrame(HISTORIC_DUNGEONS)
    c1, c2 = st.columns(2)
    c1.metric("Sites mapped", len(df))
    c2.metric("Countries", df["country"].nunique())

    m = folium.Map(location=[30, 10], zoom_start=3, tiles="CartoDB dark_matter")
    cluster = MarkerCluster(name="Dungeons & Fortresses").add_to(m)
    for r in HISTORIC_DUNGEONS:
        popup = (
            f"<b>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['years'])}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(popup, max_width=300),
            tooltip=_esc(r["name"]),
            icon=folium.Icon(color="darkred", icon="dungeon", prefix="fa"),
        ).add_to(cluster)
    _show_map(m)

    st.dataframe(df[["name", "country", "years", "notes"]], width="stretch")
    _csv_download(df, "historic_dungeons.csv")


def _render_tribunals():
    st.markdown("#### War Crimes Tribunals")
    st.info(
        "From Nuremberg to the ICC -- 20 international and hybrid courts and tribunals that "
        "have prosecuted genocide, crimes against humanity, and war crimes."
    )
    df = pd.DataFrame(WAR_CRIMES_TRIBUNALS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Tribunals / Courts", len(df))
    c2.metric("Countries hosting", df["country"].nunique())
    c3.metric("Tribunal types", df["type"].nunique())

    # Chart: types
    type_counts = df["type"].value_counts()
    fig, ax = _dark_fig(figsize=(8, 4))
    type_counts.plot.barh(ax=ax, color="#06b6d4")
    ax.set_title("Tribunals by Type")
    ax.set_xlabel("Count")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    m = folium.Map(location=[30, 10], zoom_start=2, tiles="CartoDB dark_matter")
    for r in WAR_CRIMES_TRIBUNALS:
        popup = (
            f"<b>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['years'])}<br>"
            f"Type: {_esc(r['type'])}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(popup, max_width=320),
            tooltip=_esc(r["name"]),
            icon=folium.Icon(color="blue", icon="gavel", prefix="fa"),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "years", "type", "notes"]], width="stretch")
    _csv_download(df, "war_crimes_tribunals.csv")


def _render_escapes():
    st.markdown("#### Great Escapes")
    st.info(
        "20 of the most daring, ingenious, and legendary prison escapes in history -- "
        "from Casanova's rooftop break to El Chapo's motorcycle tunnel."
    )
    df = pd.DataFrame(GREAT_ESCAPES)
    c1, c2, c3 = st.columns(3)
    c1.metric("Escapes mapped", len(df))
    c2.metric("Earliest", df["year"].min())
    c3.metric("Most recent", df["year"].max())

    # Timeline scatter
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.scatter(df["year"], range(len(df)), color="#f97316", s=60, zorder=5)
    for i, r in df.iterrows():
        ax.annotate(r["name"][:30], (r["year"], i), fontsize=6, color=_TEXT,
                     xytext=(8, 0), textcoords="offset points", va="center")
    ax.set_xlabel("Year")
    ax.set_title("Great Escapes Timeline")
    ax.set_yticks([])
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    m = folium.Map(location=[30, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for r in GREAT_ESCAPES:
        popup = (
            f"<b>{_esc(r['name'])}</b><br>"
            f"Year: {_esc(r['year'])} &middot; Prison: {_esc(r['prison'])}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(popup, max_width=320),
            tooltip=_esc(r["name"]),
            icon=folium.Icon(color="orange", icon="running", prefix="fa"),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "year", "prison", "notes"]], width="stretch")
    _csv_download(df, "great_escapes.csv")


def _render_death_penalty():
    st.markdown("#### Death Penalty Map")
    st.info(
        "Global overview of capital punishment: retentionist, abolitionist, and moratorium "
        "countries. 50 countries mapped with methods and notes."
    )
    df = pd.DataFrame(DEATH_PENALTY_DATA)

    status_counts = df["status"].value_counts()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries mapped", len(df))
    c2.metric("Retentionist", status_counts.get("Retentionist", 0))
    c3.metric("Abolitionist", status_counts.get("Abolitionist", 0))
    c4.metric("Moratorium", status_counts.get("Moratorium", 0))

    # Pie chart
    fig, ax = _dark_fig(figsize=(6, 4))
    clrs = {"Retentionist": "#dc2626", "Abolitionist": "#22c55e", "Moratorium": "#eab308"}
    ax.pie(
        status_counts.values,
        labels=status_counts.index,
        colors=[clrs.get(s, "#888") for s in status_counts.index],
        autopct="%1.0f%%",
        textprops={"color": _TEXT, "fontsize": 9},
        startangle=140,
    )
    ax.set_title("Death Penalty Status (sampled countries)")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    _status_colors = {
        "Retentionist": "red",
        "Abolitionist": "green",
        "Moratorium": "orange",
    }
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for r in DEATH_PENALTY_DATA:
        clr = _status_colors.get(r["status"], "gray")
        popup = (
            f"<b>{_esc(r['country'])}</b><br>"
            f"Status: {_esc(r['status'])}<br>"
            f"Method: {_esc(r['method'])}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.CircleMarker(
            [r["lat"], r["lon"]],
            radius=8,
            color=clr,
            fill=True,
            fill_color=clr,
            fill_opacity=0.7,
            popup=folium.Popup(popup, max_width=300),
            tooltip=f"{_esc(r['country'])}: {_esc(r['status'])}",
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["country", "status", "method", "notes"]], width="stretch")
    _csv_download(df, "death_penalty.csv")


def _render_political_prisoners():
    st.markdown("#### Political Prisoners")
    st.info(
        "25 prominent political prisoners, prisoners of conscience, and Nobel laureates "
        "who were imprisoned for their beliefs, writings, or activism."
    )
    df = pd.DataFrame(POLITICAL_PRISONERS)
    c1, c2, c3 = st.columns(3)
    c1.metric("Prisoners profiled", len(df))
    c2.metric("Countries", df["country"].nunique())
    nobel_count = sum(1 for r in POLITICAL_PRISONERS if "Nobel" in r["notes"])
    c3.metric("Nobel laureates", nobel_count)

    m = folium.Map(location=[25, 20], zoom_start=2, tiles="CartoDB dark_matter")
    for r in POLITICAL_PRISONERS:
        is_nobel = "Nobel" in r["notes"]
        clr = "purple" if is_nobel else "cadetblue"
        icon_name = "award" if is_nobel else "fist-raised"
        popup = (
            f"<b>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i> &middot; {_esc(r['years'])}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(popup, max_width=320),
            tooltip=_esc(r["name"]),
            icon=folium.Icon(color=clr, icon=icon_name, prefix="fa"),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "years", "notes"]], width="stretch")
    _csv_download(df, "political_prisoners.csv")


def _render_justice_courts():
    st.markdown("#### Justice & Court Systems")
    st.info(
        "30 supreme courts, constitutional courts, and landmark judicial institutions "
        "around the world -- spanning common law, civil law, and mixed traditions."
    )
    df = pd.DataFrame(JUSTICE_COURTS)
    tradition_counts = df["tradition"].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.metric("Courts mapped", len(df))
    c2.metric("Countries", df["country"].nunique())
    c3.metric("Legal traditions", len(tradition_counts))

    # Legal traditions bar chart
    fig, ax = _dark_fig(figsize=(9, 4))
    tradition_counts.plot.barh(ax=ax, color="#8b5cf6")
    ax.set_title("Courts by Legal Tradition")
    ax.set_xlabel("Count")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    _tradition_colors = {
        "Common law": "blue",
        "Civil law": "green",
        "Civil law (Napoleonic)": "green",
        "Civil law (German-influenced)": "green",
        "Civil law (French-influenced)": "green",
        "Civil law (Nordic)": "lightgreen",
        "Civil law (German/Japanese)": "green",
        "Socialist civil law": "red",
        "International law": "purple",
        "Common law / Hindu law": "cadetblue",
        "Common law / Civil law (Quebec)": "cadetblue",
        "Mixed (Roman-Dutch / Common)": "orange",
        "Mixed (common/civil/religious)": "orange",
        "Common law / Sharia / Customary": "orange",
        "Mixed (civil/common)": "orange",
        "Common law / Customary": "cadetblue",
        "Civil law / Adat / Sharia": "orange",
    }
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
    for r in JUSTICE_COURTS:
        clr = _tradition_colors.get(r["tradition"], "gray")
        popup = (
            f"<b>{_esc(r['name'])}</b><br>"
            f"<i>{_esc(r['country'])}</i><br>"
            f"Tradition: {_esc(r['tradition'])}<br>"
            f"{_esc(r['notes'])}"
        )
        folium.Marker(
            [r["lat"], r["lon"]],
            popup=folium.Popup(popup, max_width=320),
            tooltip=_esc(r["name"]),
            icon=folium.Icon(color=clr, icon="landmark", prefix="fa"),
        ).add_to(m)
    _show_map(m)

    st.dataframe(df[["name", "country", "tradition", "notes"]], width="stretch")
    _csv_download(df, "justice_courts.csv")


# ═══════════════════════════════════════════════════════════════════════
# DISPATCHER MAP
# ═══════════════════════════════════════════════════════════════════════
_RENDERERS = {
    MAP_MODES[0]: _render_famous_prisons,
    MAP_MODES[1]: _render_holocaust,
    MAP_MODES[2]: _render_gulag,
    MAP_MODES[3]: _render_incarceration,
    MAP_MODES[4]: _render_dungeons,
    MAP_MODES[5]: _render_tribunals,
    MAP_MODES[6]: _render_escapes,
    MAP_MODES[7]: _render_death_penalty,
    MAP_MODES[8]: _render_political_prisoners,
    MAP_MODES[9]: _render_justice_courts,
}


# ═══════════════════════════════════════════════════════════════════════
# PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
def render_prison_maps_tab():
    """Main entry point -- called from app.py inside a tab context."""
    st.markdown(
        '<div class="tab-header red"><h4>\U0001f512 Prisons, Justice & Incarceration Maps</h4>'
        "<p>Famous prisons, concentration camps, justice systems & 10 maps</p></div>",
        unsafe_allow_html=True,
    )

    mode = st.selectbox("Select map mode", MAP_MODES, key="prison_maps_mode")
    st.markdown("---")
    renderer = _RENDERERS.get(mode)
    if renderer:
        renderer()
    else:
        st.warning("Map mode not found.")
