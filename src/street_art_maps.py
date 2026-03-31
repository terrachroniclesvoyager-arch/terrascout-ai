# -*- coding: utf-8 -*-
"""
Street Art & Murals Explorer module for TerraScout AI.
Uses the Overpass API (tourism=artwork, artwork_type=mural/graffiti/sculpture)
and curated datasets to explore street art, murals, graffiti, and urban art
installations worldwide.

10 Map Modes:
 1. World Street Art Capitals
 2. Banksy Locations
 3. Mural Districts
 4. Political Murals
 5. 3D Street Art & Illusions
 6. Graffiti History
 7. Street Art Museums
 8. Sculpture & Installation Art
 9. Indigenous & Traditional Murals
10. Light Art & Projections
"""

import io
import html
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & CURATED DATA
# ══════════════════════════════════════════════════════════════════════════════

MODE_LABELS = [
    "World Street Art Capitals",
    "Banksy Locations",
    "Mural Districts",
    "Political Murals",
    "3D Street Art & Illusions",
    "Graffiti History",
    "Street Art Museums",
    "Sculpture & Installation Art",
    "Indigenous & Traditional Murals",
    "Light Art & Projections",
]

MODE_DESCRIPTIONS = {
    "World Street Art Capitals": (
        "Explore the world's most vibrant street art cities. From Berlin's "
        "raw warehouse murals to Melbourne's hidden laneways, these cities "
        "have become open-air galleries attracting artists and visitors from "
        "around the globe."
    ),
    "Banksy Locations": (
        "Trace the mysterious footprints of Banksy, the world's most famous "
        "anonymous street artist. This mode maps verified and attributed works "
        "across the UK, Europe, and beyond -- from the streets of Bristol to "
        "the separation wall in Bethlehem."
    ),
    "Mural Districts": (
        "Discover dedicated mural districts and street art precincts where "
        "entire neighbourhoods have been transformed into living canvases. "
        "From Wynwood Walls in Miami to the East Side Gallery in Berlin."
    ),
    "Political Murals": (
        "Street art has always been a vehicle for political expression. Explore "
        "murals born from conflict, resistance, and social movements -- Belfast "
        "peace walls, the Palestinian separation barrier, and protest art from "
        "Latin America to Southeast Asia."
    ),
    "3D Street Art & Illusions": (
        "Marvel at mind-bending 3D pavement art and trompe-l'oeil murals that "
        "trick the eye. This mode highlights famous optical-illusion street art "
        "and the artists who pioneered the craft."
    ),
    "Graffiti History": (
        "Journey through the birth and evolution of graffiti culture, from the "
        "subway tags of 1970s New York and Philadelphia to the European "
        "writers who shaped the movement into a global art form."
    ),
    "Street Art Museums": (
        "Explore the growing number of institutions dedicated to preserving "
        "street art. From the MOCO Museum in Amsterdam to Urban Nation in "
        "Berlin and the Straat Museum -- indoor and open-air galleries keeping "
        "the culture alive."
    ),
    "Sculpture & Installation Art": (
        "Public art goes beyond paint. Discover monumental sculptures, "
        "interactive installations, kinetic art, and avant-garde pieces placed "
        "in plazas, parks, and urban spaces around the world."
    ),
    "Indigenous & Traditional Murals": (
        "Celebrate the rich traditions of mural art rooted in Indigenous and "
        "folk cultures -- Aboriginal dot-painting walls in Australia, Mexican "
        "muralism from Rivera to Orozco, and vibrant African wall art traditions."
    ),
    "Light Art & Projections": (
        "When the sun goes down, cities light up. Discover permanent light "
        "installations, LED art, neon murals, and projection-mapping sites "
        "that transform buildings and public spaces after dark."
    ),
}

# ── Colour palette for map modes ──────────────────────────────────────────
MODE_COLORS = {
    "World Street Art Capitals": "#06b6d4",
    "Banksy Locations": "#f59e0b",
    "Mural Districts": "#ec4899",
    "Political Murals": "#ef4444",
    "3D Street Art & Illusions": "#a855f7",
    "Graffiti History": "#f97316",
    "Street Art Museums": "#8b5cf6",
    "Sculpture & Installation Art": "#10b981",
    "Indigenous & Traditional Murals": "#14b8a6",
    "Light Art & Projections": "#3b82f6",
}

# ══════════════════════════════════════════════════════════════════════════════
# MODE 1 -- World Street Art Capitals (curated)
# ══════════════════════════════════════════════════════════════════════════════

STREET_ART_CAPITALS = [
    {"city": "Berlin", "country": "Germany", "lat": 52.5015, "lon": 13.4105,
     "radius": 5, "highlight": "East Side Gallery, Urban Nation, RAW-Gelaende",
     "description": "Berlin's post-Wall rebirth made it a magnet for street artists. "
                    "Entire districts like Kreuzberg and Friedrichshain are open-air museums.",
     "notable_artists": "Blu, Os Gemeos, ROA, JR, El Bocho",
     "est_artworks": 5000},
    {"city": "Melbourne", "country": "Australia", "lat": -37.8136, "lon": 144.9631,
     "radius": 3, "highlight": "Hosier Lane, AC/DC Lane, Blender Studios",
     "description": "Melbourne's laneways are world-famous for ever-changing street art. "
                    "The city actively supports legal mural zones.",
     "notable_artists": "Rone, Lushsux, Adnate, Fintan Magee",
     "est_artworks": 3000},
    {"city": "Sao Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333,
     "radius": 6, "highlight": "Beco do Batman, Vila Madalena, Avenida Paulista",
     "description": "Sao Paulo has the largest concentration of street art in the "
                    "Americas, with pixacao and graffiti deeply embedded in the culture.",
     "notable_artists": "Os Gemeos, Nunca, Eduardo Kobra, Cranio",
     "est_artworks": 15000},
    {"city": "New York City", "country": "USA", "lat": 40.7214, "lon": -73.9951,
     "radius": 4, "highlight": "Bushwick Collective, Bowery Wall, Williamsburg",
     "description": "NYC is the birthplace of modern graffiti culture. From 1970s subway "
                    "tags to Bushwick's curated walls, the city remains an art mecca.",
     "notable_artists": "Keith Haring, Jean-Michel Basquiat, TAKI 183, Futura",
     "est_artworks": 8000},
    {"city": "London", "country": "UK", "lat": 51.5219, "lon": -0.0756,
     "radius": 3, "highlight": "Shoreditch, Brick Lane, Leake Street Tunnel",
     "description": "East London's Shoreditch is one of Europe's densest street art "
                    "zones. Banksy, Stik, and hundreds of artists paint these walls.",
     "notable_artists": "Banksy, Stik, D*Face, Ben Eine, Phlegm",
     "est_artworks": 4000},
    {"city": "Bristol", "country": "UK", "lat": 51.4545, "lon": -2.5879,
     "radius": 3, "highlight": "Nelson Street, Stokes Croft, Upfest festival",
     "description": "Banksy's hometown has embraced street art like no other UK city. "
                    "The annual Upfest is Europe's largest street art festival.",
     "notable_artists": "Banksy, Nick Walker, Inkie, Jody Thomas",
     "est_artworks": 2000},
    {"city": "Bogota", "country": "Colombia", "lat": 4.6097, "lon": -74.0817,
     "radius": 4, "highlight": "La Candelaria, Carrera 7, Chapinero",
     "description": "After a famous 2011 incident, Bogota decriminalized street art "
                    "and the city exploded with incredible murals and graffiti.",
     "notable_artists": "DJ Lu, Toxicomano, Bastardilla, Guache",
     "est_artworks": 6000},
    {"city": "Buenos Aires", "country": "Argentina", "lat": -34.6037, "lon": -58.3816,
     "radius": 4, "highlight": "Palermo, La Boca, Colegiales",
     "description": "BA's street art scene is one of the most dynamic in the world, "
                    "with artists given remarkable freedom on public walls.",
     "notable_artists": "Martin Ron, Jaz, Pastel, Poeta",
     "est_artworks": 4500},
    {"city": "Lisbon", "country": "Portugal", "lat": 38.7223, "lon": -9.1393,
     "radius": 3, "highlight": "Bairro Alto, Mouraria, LX Factory",
     "description": "Lisbon's crumbling facades are the perfect canvas. The city's "
                    "GAU programme actively commissions public murals.",
     "notable_artists": "Vhils, Bordalo II, Pantonio, Add Fuel",
     "est_artworks": 3500},
    {"city": "Mexico City", "country": "Mexico", "lat": 19.4326, "lon": -99.1332,
     "radius": 5, "highlight": "Roma, Coyoacan, Tepito",
     "description": "Mexico City blends the grand tradition of Mexican muralism with "
                    "contemporary street art, creating a layered visual landscape.",
     "notable_artists": "Saner, Smithe, Hilda Palafox, Paola Delfin",
     "est_artworks": 7000},
    {"city": "Athens", "country": "Greece", "lat": 37.9838, "lon": 23.7275,
     "radius": 3, "highlight": "Exarchia, Psyrri, Metaxourgeio",
     "description": "Greece's economic crisis fuelled an explosion of politically "
                    "charged street art, especially in the anarchist Exarchia district.",
     "notable_artists": "iNO, WD, Achilles, Same84",
     "est_artworks": 2500},
    {"city": "Valparaiso", "country": "Chile", "lat": -33.0472, "lon": -71.6127,
     "radius": 3, "highlight": "Cerro Alegre, Cerro Concepcion, open-air museum",
     "description": "Chile's bohemian port city is covered head to toe in murals. "
                    "The colourful hillside houses double as canvases.",
     "notable_artists": "Un Kolor Distinto, Inti, Cekis, Charquipunk",
     "est_artworks": 3000},
]

# ══════════════════════════════════════════════════════════════════════════════
# MODE 2 -- Banksy Locations (curated)
# ══════════════════════════════════════════════════════════════════════════════

BANKSY_WORKS = [
    {"title": "Girl with Balloon", "lat": 51.5076, "lon": -0.0994,
     "city": "London, UK", "year": 2002, "status": "Removed / iconic image",
     "description": "One of Banksy's most recognisable works -- a girl reaching for a red heart balloon. Originally appeared on Waterloo Bridge."},
    {"title": "Kissing Coppers", "lat": 50.8225, "lon": -0.1372,
     "city": "Brighton, UK", "year": 2004, "status": "Removed / sold",
     "description": "Two male police officers kissing, originally painted on the wall of the Prince Albert pub."},
    {"title": "Mild Mild West", "lat": 51.4598, "lon": -2.5967,
     "city": "Bristol, UK", "year": 1999, "status": "Extant",
     "description": "A teddy bear throwing a Molotov cocktail at riot police. One of the earliest and best-preserved Banksy murals."},
    {"title": "Well Hung Lover", "lat": 51.4538, "lon": -2.5952,
     "city": "Bristol, UK", "year": 2006, "status": "Extant",
     "description": "A naked man hangs from a window ledge while a woman and suited man look out."},
    {"title": "Flower Thrower", "lat": 31.7054, "lon": 35.2024,
     "city": "Bethlehem, Palestine", "year": 2003, "status": "Extant",
     "description": "An iconic masked protester hurling a bouquet of flowers. Painted on the separation wall."},
    {"title": "Armoured Dove", "lat": 31.7050, "lon": 35.2056,
     "city": "Bethlehem, Palestine", "year": 2007, "status": "Extant",
     "description": "A dove of peace wearing a bulletproof vest, targeted by crosshairs. On the separation wall."},
    {"title": "Shop Until You Drop", "lat": 51.5138, "lon": -0.0890,
     "city": "London, UK", "year": 2011, "status": "Removed",
     "description": "A woman falling with shopping bags, commentary on consumer culture."},
    {"title": "Slave Labour", "lat": 51.5309, "lon": -0.1478,
     "city": "London, UK", "year": 2012, "status": "Removed / controversy",
     "description": "A child sewing Union Jack bunting, critique of sweatshop labour during the Queen's Diamond Jubilee."},
    {"title": "Spy Booth", "lat": 51.8439, "lon": -2.2451,
     "city": "Cheltenham, UK", "year": 2014, "status": "Destroyed",
     "description": "Three spies in trenchcoats eavesdropping on a phone box, near GCHQ headquarters."},
    {"title": "Dismaland", "lat": 51.3410, "lon": -2.9783,
     "city": "Weston-super-Mare, UK", "year": 2015, "status": "Dismantled pop-up",
     "description": "A dystopian 'bemusement park', Banksy's largest-ever project featuring 58 artists."},
    {"title": "Girl with a Pierced Eardrum", "lat": 51.4497, "lon": -2.5960,
     "city": "Bristol, UK", "year": 2014, "status": "Extant",
     "description": "A parody of Vermeer's Girl with a Pearl Earring using a security alarm as the earring."},
    {"title": "Rage, Flower Thrower (Jerusalem)", "lat": 31.7758, "lon": 35.2292,
     "city": "Jerusalem, Israel/Palestine", "year": 2005, "status": "Extant (faded)",
     "description": "A variant of the flower thrower on a wall in the Old City area."},
    {"title": "Game Changer", "lat": 50.9205, "lon": -1.4049,
     "city": "Southampton, UK", "year": 2020, "status": "Donated to hospital",
     "description": "A boy plays with a nurse superhero doll; painted during COVID-19 for NHS workers."},
    {"title": "Aachoo!!", "lat": 51.4412, "lon": -2.5634,
     "city": "Bristol, UK", "year": 2020, "status": "Extant",
     "description": "An old woman sneezing so hard her dentures fly out, painted during the pandemic."},
    {"title": "Valentine's Day mural", "lat": 51.4472, "lon": -2.5267,
     "city": "Bristol, UK", "year": 2020, "status": "Damaged / protected",
     "description": "A girl firing a slingshot of flowers. Appeared on a house in Barton Hill."},
    {"title": "Migrant Child (Venice)", "lat": 45.4337, "lon": 12.3386,
     "city": "Venice, Italy", "year": 2019, "status": "Extant",
     "description": "A migrant child wearing a life jacket holds a neon flare, installed during the Venice Biennale."},
    {"title": "Steve Jobs mural (Calais)", "lat": 50.9581, "lon": 1.8627,
     "city": "Calais, France", "year": 2015, "status": "Destroyed with Jungle camp",
     "description": "Steve Jobs depicted as a refugee, reminding viewers he was the son of a Syrian migrant."},
    {"title": "Sweep It Under the Carpet", "lat": 51.5317, "lon": -0.1040,
     "city": "London, UK", "year": 2006, "status": "Painted over",
     "description": "A maid lifting a wall like a curtain and sweeping dirt underneath."},
    {"title": "Hammer Boy (Marble Arch)", "lat": 51.5133, "lon": -0.1590,
     "city": "London, UK", "year": 2013, "status": "Removed",
     "description": "Part of Banksy's month-long 'Better Out Than In' NYC-style residency in London."},
    {"title": "Season's Greetings", "lat": 51.6390, "lon": -3.8478,
     "city": "Port Talbot, Wales", "year": 2018, "status": "Relocated / preserved",
     "description": "A child catching snowflakes that are actually ash from a dumpster fire, commentary on pollution."},
]

# ══════════════════════════════════════════════════════════════════════════════
# MODE 3 -- Mural Districts (curated)
# ══════════════════════════════════════════════════════════════════════════════

MURAL_DISTRICTS = [
    {"name": "Wynwood Walls", "city": "Miami, USA", "lat": 25.8011, "lon": -80.1996,
     "radius": 1, "year_started": 2009,
     "description": "Tony Goldman transformed a warehouse district into the world's premier outdoor mural gallery. Over 80,000 sq ft of walls.",
     "notable_artists": "Shepard Fairey, Retna, Kenny Scharf, POSE, Maya Hayuk",
     "est_murals": 300},
    {"name": "East Side Gallery", "city": "Berlin, Germany", "lat": 52.5054, "lon": 13.4396,
     "radius": 1, "year_started": 1990,
     "description": "A 1.3 km stretch of the Berlin Wall painted by 118 artists from 21 countries. The longest open-air gallery in the world.",
     "notable_artists": "Dmitri Vrubel, Birgit Kinder, Thierry Noir, Kani Alavi",
     "est_murals": 105},
    {"name": "Hosier Lane", "city": "Melbourne, Australia", "lat": -37.8170, "lon": 144.9694,
     "radius": 0.5, "year_started": 2000,
     "description": "Melbourne's most famous street art laneway. Art changes daily as new layers cover old. A must-visit destination.",
     "notable_artists": "Rone, Adnate, Lushsux, Kaff-eine",
     "est_murals": 200},
    {"name": "Cerro Alegre & Concepcion", "city": "Valparaiso, Chile", "lat": -33.0420, "lon": -71.6250,
     "radius": 2, "year_started": 1990,
     "description": "Two hillside neighbourhoods in Valparaiso that function as a continuous open-air mural museum.",
     "notable_artists": "Un Kolor Distinto, Inti, Cekis",
     "est_murals": 500},
    {"name": "Bushwick Collective", "city": "Brooklyn, NYC, USA", "lat": 40.7044, "lon": -73.9213,
     "radius": 1, "year_started": 2011,
     "description": "Founded by Joe Ficalora, this Brooklyn collective has transformed industrial Bushwick into a world-class mural destination.",
     "notable_artists": "POSE, Meres One, Buff Monster, Blek le Rat",
     "est_murals": 250},
    {"name": "Beco do Batman", "city": "Sao Paulo, Brazil", "lat": -23.5560, "lon": -46.6878,
     "radius": 0.5, "year_started": 1980,
     "description": "An alleyway in Vila Madalena covered floor to ceiling in vibrant street art. Named after a Batman image painted in the 80s.",
     "notable_artists": "Various local and international artists",
     "est_murals": 150},
    {"name": "La Candelaria", "city": "Bogota, Colombia", "lat": 4.5964, "lon": -74.0739,
     "radius": 2, "year_started": 2011,
     "description": "After the decriminalisation of graffiti, Bogota's historic centre became an incredible street art gallery.",
     "notable_artists": "DJ Lu, Toxicomano, Bastardilla, Guache",
     "est_murals": 400},
    {"name": "Stokes Croft / Nelson Street", "city": "Bristol, UK", "lat": 51.4615, "lon": -2.5925,
     "radius": 1, "year_started": 2000,
     "description": "Bristol's creative quarter, known as 'the Banksy corridor'. The annual Upfest transforms it further each year.",
     "notable_artists": "Banksy, Jody Thomas, Cheo, Inkie",
     "est_murals": 200},
    {"name": "Kelburn Castle Graffiti Project", "city": "Largs, Scotland", "lat": 55.7813, "lon": -4.8692,
     "radius": 0.5, "year_started": 2007,
     "description": "A 13th-century Scottish castle covered in psychedelic Brazilian-style graffiti -- a unique fusion of history and street art.",
     "notable_artists": "Os Gemeos, Nina Pandolfo, Nunca",
     "est_murals": 1},
    {"name": "Shoreditch & Brick Lane", "city": "London, UK", "lat": 51.5230, "lon": -0.0720,
     "radius": 1, "year_started": 1990,
     "description": "East London's street art epicentre. Brick Lane and surrounding streets host a rotating gallery of world-class murals.",
     "notable_artists": "Stik, ROA, D*Face, Ben Eine, C215",
     "est_murals": 350},
    {"name": "Hamra Street", "city": "Beirut, Lebanon", "lat": 33.8980, "lon": 35.4880,
     "radius": 1, "year_started": 2012,
     "description": "Beirut's Hamra district features political and cultural murals reflecting Lebanon's complex history.",
     "notable_artists": "Yazan Halwani, Ashekman, Kabrit",
     "est_murals": 100},
    {"name": "Graffiti Alley (Toronto)", "city": "Toronto, Canada", "lat": 43.6487, "lon": -79.4011,
     "radius": 0.5, "year_started": 2010,
     "description": "Rush Lane, also known as Graffiti Alley, stretches through Queen West with colourful murals and tags.",
     "notable_artists": "Uber5000, Elicser, Birdo",
     "est_murals": 175},
]

# ══════════════════════════════════════════════════════════════════════════════
# MODE 4 -- Political Murals (curated)
# ══════════════════════════════════════════════════════════════════════════════

POLITICAL_MURALS = [
    {"name": "Falls Road Murals", "city": "Belfast, Northern Ireland", "lat": 54.5971, "lon": -5.9483,
     "side": "Republican / Nationalist", "period": "1970s-present",
     "description": "Over 300 murals line the Falls Road, depicting Irish Republican themes, hunger strikers, and calls for unity.",
     "est_murals": 150},
    {"name": "Shankill Road Murals", "city": "Belfast, Northern Ireland", "lat": 54.6029, "lon": -5.9512,
     "side": "Loyalist / Unionist", "period": "1970s-present",
     "description": "Loyalist murals featuring King William, UVF and UDA imagery, and commemoration of the Troubles.",
     "est_murals": 100},
    {"name": "Bethlehem Separation Wall", "city": "Bethlehem, Palestine", "lat": 31.7054, "lon": 35.2024,
     "side": "Pro-Palestinian / Peace", "period": "2003-present",
     "description": "The Israeli separation wall in Bethlehem has become one of the world's most political canvases, featuring works by Banksy and many others.",
     "est_murals": 200},
    {"name": "Orgosolo Murals", "city": "Orgosolo, Sardinia, Italy", "lat": 40.2043, "lon": 9.3525,
     "side": "Social justice / Anti-war", "period": "1969-present",
     "description": "Over 150 murals cover the village of Orgosolo, tackling themes from Italian politics to global injustice.",
     "est_murals": 150},
    {"name": "Chilean Protest Murals", "city": "Santiago, Chile", "lat": -33.4372, "lon": -70.6506,
     "side": "Anti-Pinochet / Social protest", "period": "1970s-present",
     "description": "From the Allende era through dictatorship to the 2019 estallido social, Santiago's walls tell Chile's political story.",
     "est_murals": 300},
    {"name": "Bogota Political Graffiti", "city": "Bogota, Colombia", "lat": 4.6097, "lon": -74.0817,
     "side": "Peace / Anti-violence", "period": "2011-present",
     "description": "After the shooting of a teenage graffiti artist by police, Bogota legalized street art. Political messages abound.",
     "est_murals": 250},
    {"name": "Exarchia Anarchist Murals", "city": "Athens, Greece", "lat": 37.9862, "lon": 23.7336,
     "side": "Anarchist / Anti-austerity", "period": "2008-present",
     "description": "Athens' Exarchia district is Europe's most politically charged street art zone, born from the 2008 crisis.",
     "est_murals": 200},
    {"name": "Derry / Bogside Murals", "city": "Derry, Northern Ireland", "lat": 54.9966, "lon": -7.3196,
     "side": "Nationalist / Civil rights", "period": "1990s-present",
     "description": "The 'People's Gallery' in the Bogside features 12 iconic murals depicting events from the Troubles, including Bloody Sunday.",
     "est_murals": 12},
    {"name": "Berlin Wall Murals (East Side Gallery)", "city": "Berlin, Germany", "lat": 52.5054, "lon": 13.4396,
     "side": "Peace / Anti-division", "period": "1990",
     "description": "Painted on the east side of the Wall after reunification, including 'My God, Help Me Survive This Deadly Love' (the Brezhnev-Honecker kiss).",
     "est_murals": 105},
    {"name": "Getsemani Murals", "city": "Cartagena, Colombia", "lat": 10.4218, "lon": -75.5500,
     "side": "Afro-Colombian heritage / Social justice", "period": "2000s-present",
     "description": "The Getsemani neighbourhood features murals celebrating Afro-Colombian culture and resistance against gentrification.",
     "est_murals": 80},
    {"name": "Zapatista Murals", "city": "San Cristobal de las Casas, Mexico", "lat": 16.7370, "lon": -92.6376,
     "side": "Indigenous rights / Zapatismo", "period": "1994-present",
     "description": "Murals depicting the Zapatista movement, indigenous rights, and anti-neoliberal themes in Chiapas.",
     "est_murals": 60},
    {"name": "Tahrir Square Graffiti", "city": "Cairo, Egypt", "lat": 30.0444, "lon": 31.2357,
     "side": "Pro-democracy / Arab Spring", "period": "2011-2013",
     "description": "The 2011 Egyptian revolution spawned powerful revolutionary graffiti around Tahrir Square, most later removed by authorities.",
     "est_murals": 50},
]

# ══════════════════════════════════════════════════════════════════════════════
# MODE 5 -- 3D Street Art & Illusions (curated)
# ══════════════════════════════════════════════════════════════════════════════

THREE_D_ART = [
    {"title": "Crevasse (Dun Laoghaire)", "artist": "Edgar Mueller", "lat": 53.2946, "lon": -6.1339,
     "city": "Dun Laoghaire, Ireland", "year": 2008, "type": "3D pavement art",
     "description": "A massive 3D pavement painting of a crevasse splitting open a street, one of the most famous 3D works ever created."},
    {"title": "The Lava Burst", "artist": "Edgar Mueller", "lat": 50.0782, "lon": 8.2398,
     "city": "Geldern, Germany", "year": 2008, "type": "3D pavement art",
     "description": "A spectacular pavement art piece showing molten lava erupting through a city street."},
    {"title": "Waterfall (Quebec)", "artist": "Francois Abelanet", "lat": 46.8139, "lon": -71.2074,
     "city": "Quebec City, Canada", "year": 2012, "type": "Anamorphic installation",
     "description": "An anamorphic installation that appears as a giant waterfall when viewed from the correct angle."},
    {"title": "Odeith's Anamorphic Insects", "artist": "Odeith", "lat": 38.6600, "lon": -9.2033,
     "city": "Lisbon, Portugal", "year": 2015, "type": "Anamorphic mural",
     "description": "Hyper-realistic anamorphic insects that appear to crawl off walls, pioneered by Portuguese artist Odeith."},
    {"title": "Julian Beever Pavement Works", "artist": "Julian Beever", "lat": 51.5074, "lon": -0.1278,
     "city": "London, UK (various)", "year": 2000, "type": "Chalk pavement art",
     "description": "Julian Beever is the godfather of 3D pavement art, creating chalk masterpieces worldwide since the 1990s."},
    {"title": "Tromp-l'oeil facades (Lyon)", "artist": "CiteCrea", "lat": 45.7640, "lon": 4.8357,
     "city": "Lyon, France", "year": 1987, "type": "Trompe-l'oeil building",
     "description": "Lyon is the European capital of trompe-l'oeil, with over 100 painted building facades deceiving the eye."},
    {"title": "The Ground Illusion (Seoul)", "artist": "Various", "lat": 37.5665, "lon": 126.9780,
     "city": "Seoul, South Korea", "year": 2013, "type": "3D pavement art",
     "description": "Seoul hosts a permanent 3D Trick Eye Museum and numerous street-level illusion artworks."},
    {"title": "Manfred Stader 3D Works", "artist": "Manfred Stader", "lat": 50.1109, "lon": 8.6821,
     "city": "Frankfurt, Germany", "year": 2010, "type": "3D street painting",
     "description": "Manfred Stader creates large-scale 3D street paintings for brands and cities across Europe."},
    {"title": "ZAG (Milan)", "artist": "Truly Design", "lat": 45.4798, "lon": 9.2321,
     "city": "Milan, Italy", "year": 2016, "type": "Anamorphic room",
     "description": "Truly Design created an anamorphic room painting in Milan that only reveals its 3D form from one viewpoint."},
    {"title": "The Swimming Pool (Toronto)", "artist": "David Zinn", "lat": 43.6532, "lon": -79.3832,
     "city": "Toronto, Canada", "year": 2018, "type": "Chalk street art",
     "description": "David Zinn's whimsical chalk creatures that appear to interact with urban infrastructure."},
    {"title": "JR Inside Out (Paris)", "artist": "JR", "lat": 48.8606, "lon": 2.3376,
     "city": "Paris, France", "year": 2011, "type": "Large-scale optical",
     "description": "JR's paste-up portraits create massive optical illusions on buildings, making faces emerge from architecture."},
    {"title": "Pokras Lampas Calligraphy (St. Petersburg)", "artist": "Pokras Lampas", "lat": 59.9343, "lon": 30.3351,
     "city": "St. Petersburg, Russia", "year": 2019, "type": "Rooftop calligrafuturism",
     "description": "The world's largest calligraphy artwork on a rooftop, visible from above, blending street art with typography."},
]

# ══════════════════════════════════════════════════════════════════════════════
# MODE 6 -- Graffiti History (curated)
# ══════════════════════════════════════════════════════════════════════════════

GRAFFITI_HISTORY = [
    {"title": "TAKI 183 Origin", "lat": 40.8484, "lon": -73.9346,
     "city": "Washington Heights, NYC", "year": 1971, "era": "Birth of graffiti",
     "description": "TAKI 183, a Greek-American teen, became the first graffiti celebrity when the NY Times covered his tags across the city. He inspired thousands.",
     "significance": "Considered the spark that ignited the NYC graffiti movement"},
    {"title": "CORNBREAD (Philadelphia)", "lat": 39.9526, "lon": -75.1652,
     "city": "Philadelphia, USA", "year": 1967, "era": "Proto-graffiti",
     "description": "Darryl McCray, aka CORNBREAD, is widely considered the first modern graffiti writer. He tagged walls across Philly to impress a girl.",
     "significance": "Widely credited as the first modern graffiti writer"},
    {"title": "5 Pointz (Queens)", "lat": 40.7425, "lon": -73.9311,
     "city": "Long Island City, NYC", "year": 1993, "era": "Golden age institution",
     "description": "5 Pointz was the 'Institute of Higher Burnin', a mecca for graffiti writers worldwide. Controversially whitewashed in 2013.",
     "significance": "The world's most famous legal graffiti space, demolished 2014"},
    {"title": "Writers Bench (149th St Grand Concourse)", "lat": 40.8209, "lon": -73.9271,
     "city": "South Bronx, NYC", "year": 1972, "era": "Subway era",
     "description": "The legendary bench at the 149th Street station where writers gathered to watch their pieces roll by on trains.",
     "significance": "Social hub of the early subway graffiti movement"},
    {"title": "Wild Style Film Location", "lat": 40.8176, "lon": -73.9209,
     "city": "South Bronx, NYC", "year": 1983, "era": "Graffiti film",
     "description": "Locations from 'Wild Style', the first hip-hop film, featuring real graffiti artists Lee Quinones and Lady Pink.",
     "significance": "The film that introduced graffiti culture to the world"},
    {"title": "Blek le Rat Origins (Paris)", "lat": 48.8566, "lon": 2.3522,
     "city": "Paris, France", "year": 1981, "era": "European pioneers",
     "description": "Xavier Prou, aka Blek le Rat, pioneered stencil graffiti in Paris. He is considered the 'father of stencil graffiti art'.",
     "significance": "Invented stencil graffiti, directly influenced Banksy"},
    {"title": "Harald Naegeli (Zurich)", "lat": 47.3769, "lon": 8.5417,
     "city": "Zurich, Switzerland", "year": 1977, "era": "European pioneers",
     "description": "The 'Sprayer of Zurich' created minimalist stick figures across the city, was arrested and became a cause celebre.",
     "significance": "One of Europe's first graffiti artists, sparked legal debate"},
    {"title": "Amsterdam Graffiti Hall of Fame", "lat": 52.3602, "lon": 4.9292,
     "city": "Amsterdam, Netherlands", "year": 1983, "era": "European expansion",
     "description": "The NDSM wharf and surrounding areas became Amsterdam's graffiti epicentre in the 1980s.",
     "significance": "Key node in spreading American graffiti culture to Europe"},
    {"title": "Fab 5 Freddy / Subway Art Era", "lat": 40.6868, "lon": -73.9776,
     "city": "Brooklyn, NYC", "year": 1984, "era": "Documentation",
     "description": "Martha Cooper and Henry Chalfant's book 'Subway Art' (1984) documented the golden age and became the graffiti bible.",
     "significance": "The book that codified and spread subway graffiti worldwide"},
    {"title": "Keith Haring Subway Drawings", "lat": 40.7580, "lon": -73.9855,
     "city": "Midtown Manhattan, NYC", "year": 1980, "era": "Street-to-gallery",
     "description": "Keith Haring drew with chalk on blank subway advertising panels, creating iconic pop-art figures seen by millions daily.",
     "significance": "Bridged the gap between street art and fine art"},
    {"title": "Jean-Michel Basquiat / SAMO", "lat": 40.7242, "lon": -73.9963,
     "city": "SoHo / Lower East Side, NYC", "year": 1977, "era": "Street-to-gallery",
     "description": "Before becoming a gallery star, Basquiat and Al Diaz wrote cryptic 'SAMO' messages across downtown Manhattan.",
     "significance": "Proto-street-art that became fine art legend"},
    {"title": "Berlin Wall Graffiti", "lat": 52.5070, "lon": 13.3383,
     "city": "Berlin, Germany", "year": 1984, "era": "Political expression",
     "description": "The western side of the Berlin Wall became the world's longest graffiti canvas, a symbol of freedom and resistance.",
     "significance": "Graffiti as a symbol of freedom against division"},
]

# ══════════════════════════════════════════════════════════════════════════════
# MODE 7 -- Street Art Museums (curated)
# ══════════════════════════════════════════════════════════════════════════════

STREET_ART_MUSEUMS = [
    {"name": "MOCO Museum", "city": "Amsterdam, Netherlands", "lat": 52.3580, "lon": 4.8813,
     "type": "Indoor gallery", "year_opened": 2016,
     "description": "Modern Contemporary museum featuring Banksy, KAWS, and other street art icons alongside contemporary art.",
     "collection": "Banksy, KAWS, Keith Haring, Basquiat"},
    {"name": "Urban Nation Museum", "city": "Berlin, Germany", "lat": 52.4970, "lon": 13.3537,
     "type": "Museum + outdoor gallery", "year_opened": 2017,
     "description": "The world's first museum dedicated to urban contemporary art. Building facade and interior are both art.",
     "collection": "Shepard Fairey, Swoon, Vhils, D*Face"},
    {"name": "Straat Museum", "city": "Amsterdam, Netherlands", "lat": 52.4015, "lon": 4.8945,
     "type": "Indoor museum", "year_opened": 2020,
     "description": "Europe's largest street art museum, housed in a massive NDSM wharf warehouse with 150+ works.",
     "collection": "ROA, Faith47, Tymon de Laat, DOES"},
    {"name": "Museum of Graffiti", "city": "Miami, USA", "lat": 25.7990, "lon": -80.1992,
     "type": "Museum + outdoor walls", "year_opened": 2019,
     "description": "The first museum in the world dedicated to graffiti, in the heart of Wynwood.",
     "collection": "CRASH, Futura, Lady Pink, Lee Quinones"},
    {"name": "Leake Street Arches (Banksy Tunnel)", "city": "London, UK", "lat": 51.5019, "lon": -0.1143,
     "type": "Legal graffiti tunnel", "year_opened": 2008,
     "description": "A 300m tunnel beneath Waterloo station. Banksy's 'Cans Festival' opened it; now a permanent legal graffiti space.",
     "collection": "Rotating artists, open to all"},
    {"name": "Museo a Cielo Abierto", "city": "Valparaiso, Chile", "lat": -33.0500, "lon": -71.6210,
     "type": "Open-air museum", "year_opened": 1992,
     "description": "An open-air mural museum in the Bellavista neighbourhood, featuring 20 original murals on resident walls.",
     "collection": "Roberto Matta, Nemesio Antunez, Mario Toral"},
    {"name": "Citylights Gallery", "city": "Paris, France", "lat": 48.8653, "lon": 2.3616,
     "type": "Gallery", "year_opened": 2010,
     "description": "A pioneering Parisian gallery dedicated to street art, bringing outdoor artists into the gallery world.",
     "collection": "Invader, Ludo, C215, Seth"},
    {"name": "Beyond the Streets", "city": "Los Angeles / NYC, USA", "lat": 34.0522, "lon": -118.2437,
     "type": "Travelling exhibition", "year_opened": 2018,
     "description": "The largest graffiti and street art exhibition ever, featuring 100+ artists in massive warehouse spaces.",
     "collection": "Basquiat, Haring, Banksy, Futura, Swoon"},
    {"name": "Nuart Festival & Gallery", "city": "Stavanger, Norway", "lat": 58.9700, "lon": 5.7331,
     "type": "Festival + permanent gallery", "year_opened": 2001,
     "description": "One of Europe's leading street art festivals, transforming Stavanger annually with world-class murals.",
     "collection": "Ernest Zacharevic, Martin Whatson, Fintan Magee"},
    {"name": "The Haus (Pop-up)", "city": "Berlin, Germany", "lat": 52.5076, "lon": 13.3341,
     "type": "Pop-up museum", "year_opened": 2017,
     "description": "165 artists transformed a doomed bank building into a massive pop-up street art museum before demolition.",
     "collection": "165 international street artists"},
    {"name": "St+Art India Foundation", "city": "New Delhi, India", "lat": 28.6139, "lon": 77.2090,
     "type": "Urban art foundation + district", "year_opened": 2014,
     "description": "Transformed the Lodhi Colony into India's first public art district with massive murals on government buildings.",
     "collection": "Nevercrew, Amitabh Kumar, Hanif Kureshi"},
    {"name": "Upfest Gallery", "city": "Bristol, UK", "lat": 51.4430, "lon": -2.5880,
     "type": "Gallery + annual festival", "year_opened": 2008,
     "description": "Europe's largest street art festival, with a year-round gallery showcasing Bristol's vibrant scene.",
     "collection": "Banksy, Stik, Jody Thomas, various"},
]

# ══════════════════════════════════════════════════════════════════════════════
# MODE 8 -- Sculpture & Installation Art (curated)
# ══════════════════════════════════════════════════════════════════════════════

SCULPTURE_INSTALLATIONS = [
    {"name": "Cloud Gate (The Bean)", "artist": "Anish Kapoor", "lat": 41.8827, "lon": -87.6233,
     "city": "Chicago, USA", "year": 2006, "type": "Sculpture",
     "description": "The iconic reflective bean-shaped sculpture in Millennium Park. One of the most photographed public artworks on Earth."},
    {"name": "The Angel of the North", "artist": "Antony Gormley", "lat": 54.9141, "lon": -1.5894,
     "city": "Gateshead, UK", "year": 1998, "type": "Sculpture",
     "description": "A massive 20m steel angel with a 54m wingspan overlooking the A1 motorway. Seen by 90,000 drivers daily."},
    {"name": "Charging Bull", "artist": "Arturo Di Modica", "lat": 40.7056, "lon": -74.0134,
     "city": "New York City, USA", "year": 1989, "type": "Sculpture",
     "description": "The iconic bronze bull in Lower Manhattan, originally a guerrilla art installation that became a symbol of Wall Street."},
    {"name": "Vessel (Hudson Yards)", "artist": "Thomas Heatherwick", "lat": 40.7536, "lon": -74.0022,
     "city": "New York City, USA", "year": 2019, "type": "Interactive structure",
     "description": "A 16-story honeycomb-like structure of interconnected staircases. An architectural sculpture visitors can climb."},
    {"name": "Floralis Generica", "artist": "Eduardo Catalano", "lat": -34.5737, "lon": -58.4016,
     "city": "Buenos Aires, Argentina", "year": 2002, "type": "Kinetic sculpture",
     "description": "A giant metal flower that opens and closes with the sun. 23 metres tall, made of stainless steel and aluminium."},
    {"name": "Manneken Pis", "artist": "Hieronymus Duquesnoy the Elder", "lat": 50.8450, "lon": 4.3499,
     "city": "Brussels, Belgium", "year": 1619, "type": "Sculpture / fountain",
     "description": "The famously cheeky bronze fountain statue of a little boy urinating. An icon of Brussels since the 17th century."},
    {"name": "Knotted Gun (Non-Violence)", "artist": "Carl Fredrik Reutersward", "lat": 40.7489, "lon": -73.9680,
     "city": "New York City (UN), USA", "year": 1988, "type": "Sculpture",
     "description": "A bronze revolver with a knotted barrel, placed outside the United Nations. A symbol of peace and non-violence."},
    {"name": "Spoonbridge and Cherry", "artist": "Claes Oldenburg & Coosje van Bruggen",
     "lat": 44.9692, "lon": -93.2889,
     "city": "Minneapolis, USA", "year": 1988, "type": "Sculpture",
     "description": "A massive spoon with a cherry at the Minneapolis Sculpture Garden. Pop art becomes monumental public sculpture."},
    {"name": "Puppy", "artist": "Jeff Koons", "lat": 43.2684, "lon": -2.9340,
     "city": "Bilbao, Spain", "year": 1997, "type": "Living sculpture",
     "description": "A 12m topiary puppy covered in flowers outside the Guggenheim Bilbao. Reimagined annually with fresh plantings."},
    {"name": "Expansion", "artist": "Paige Bradley", "lat": 40.7580, "lon": -73.9855,
     "city": "New York City, USA", "year": 2004, "type": "Bronze / light sculpture",
     "description": "A cracked bronze figure with light shining through, symbolising the human spirit breaking free."},
    {"name": "The Kelpies", "artist": "Andy Scott", "lat": 56.0176, "lon": -3.7558,
     "city": "Falkirk, Scotland", "year": 2013, "type": "Sculpture",
     "description": "Two 30m steel horse-head sculptures inspired by shape-shifting water spirits of Celtic mythology."},
    {"name": "Rain Room", "artist": "Random International", "lat": 24.5333, "lon": 54.3975,
     "city": "Sharjah, UAE", "year": 2012, "type": "Interactive installation",
     "description": "Walk through a rainstorm without getting wet. Sensors pause the rain where you walk. Permanently at Sharjah Art Foundation."},
]

# ══════════════════════════════════════════════════════════════════════════════
# MODE 9 -- Indigenous & Traditional Murals (curated)
# ══════════════════════════════════════════════════════════════════════════════

INDIGENOUS_MURALS = [
    {"name": "Aboriginal Dot-Painting Walls", "city": "Alice Springs, Australia", "lat": -23.6980, "lon": 133.8807,
     "tradition": "Aboriginal Australian", "period": "Contemporary (1970s-present)",
     "description": "The Araluen Arts Centre and surrounding areas feature contemporary Aboriginal dot-painting murals translating ancient dreamtime stories to walls.",
     "significance": "Bridge between 40,000-year-old traditions and contemporary urban art"},
    {"name": "Diego Rivera's Detroit Industry Murals", "city": "Detroit, USA", "lat": 42.3593, "lon": -83.0645,
     "tradition": "Mexican Muralism", "period": "1932-1933",
     "description": "27 fresco panels at the Detroit Institute of Arts depicting the city's industry. Rivera's masterwork in the USA.",
     "significance": "Considered among the finest examples of Mexican muralism"},
    {"name": "Palacio de Bellas Artes Murals", "city": "Mexico City, Mexico", "lat": 19.4353, "lon": -99.1413,
     "tradition": "Mexican Muralism", "period": "1934-present",
     "description": "Home to murals by Rivera, Siqueiros, Orozco, and Tamayo. The epicentre of the Mexican muralist movement.",
     "significance": "The birthplace of the Mexican muralism movement"},
    {"name": "Bonampak Mural Reproductions", "city": "Mexico City (UNAM), Mexico", "lat": 19.3262, "lon": -99.1764,
     "tradition": "Ancient Maya", "period": "AD 790 (originals)",
     "description": "Reproductions of the ancient Maya murals of Bonampak, depicting battle, ritual, and courtly life in vivid colour.",
     "significance": "Among the finest surviving pre-Columbian murals"},
    {"name": "Ndebele House Paintings", "city": "Mpumalanga, South Africa", "lat": -25.3500, "lon": 29.0167,
     "tradition": "Ndebele", "period": "Traditional (centuries old, ongoing)",
     "description": "The Ndebele people paint their houses in bold geometric patterns. Esther Mahlangu brought this tradition to global fame.",
     "significance": "Living tradition of geometric wall art, UNESCO interest"},
    {"name": "Ethiopian Church Murals", "city": "Lalibela, Ethiopia", "lat": 12.0314, "lon": 39.0472,
     "tradition": "Ethiopian Orthodox", "period": "12th century-present",
     "description": "The rock-hewn churches of Lalibela contain ancient frescoes depicting biblical scenes in a uniquely Ethiopian style.",
     "significance": "UNESCO World Heritage Site, among Africa's oldest mural traditions"},
    {"name": "Warli Art Walls", "city": "Dahanu, Maharashtra, India", "lat": 19.9830, "lon": 72.7406,
     "tradition": "Warli tribal", "period": "Traditional (2000+ years)",
     "description": "The Warli people of Maharashtra paint white stick-figure murals on mud walls depicting daily life, rituals, and nature.",
     "significance": "One of the oldest forms of Indian folk art, still practised"},
    {"name": "Orozco's Hospicio Cabanas Murals", "city": "Guadalajara, Mexico", "lat": 20.6760, "lon": -103.3361,
     "tradition": "Mexican Muralism", "period": "1938-1939",
     "description": "Jose Clemente Orozco's monumental murals in the Hospicio Cabanas chapel, including 'Man of Fire' on the dome ceiling.",
     "significance": "UNESCO World Heritage Site, Orozco's masterpiece"},
    {"name": "Haida Totem Poles & Murals", "city": "Haida Gwaii, BC, Canada", "lat": 53.2527, "lon": -131.9954,
     "tradition": "Haida (First Nations)", "period": "Traditional (centuries, revived)",
     "description": "Haida longhouses and community buildings feature elaborate painted designs depicting clan crests and stories.",
     "significance": "Living First Nations mural tradition on the Pacific Northwest"},
    {"name": "Maori Meeting House Carvings & Murals", "city": "Rotorua, New Zealand", "lat": -38.1368, "lon": 176.2497,
     "tradition": "Maori (Aotearoa)", "period": "Traditional (ongoing)",
     "description": "Maori wharenui (meeting houses) feature elaborate painted panels (tukutuku and kowhaiwhai) with deep cultural significance.",
     "significance": "Living Polynesian mural tradition, UNESCO cultural heritage"},
    {"name": "Siqueiros' Polyforum Cultural", "city": "Mexico City, Mexico", "lat": 19.3714, "lon": -99.1769,
     "tradition": "Mexican Muralism", "period": "1966-1971",
     "description": "The world's largest mural, 'March of Humanity', wrapping an entire building interior and exterior in 8,700 sq ft of art.",
     "significance": "The largest mural in the world by a single artist"},
    {"name": "Aboriginal Street Art (Newtown)", "city": "Sydney, Australia", "lat": -33.8974, "lon": 151.1789,
     "tradition": "Contemporary Aboriginal", "period": "2010s-present",
     "description": "Sydney's Newtown area features collaborations between Indigenous Australian artists and street art culture.",
     "significance": "Fusion of ancient Indigenous visual language with urban art"},
]

# ══════════════════════════════════════════════════════════════════════════════
# MODE 10 -- Light Art & Projections (curated)
# ══════════════════════════════════════════════════════════════════════════════

LIGHT_ART = [
    {"name": "Vivid Sydney", "city": "Sydney, Australia", "lat": -33.8568, "lon": 151.2153,
     "type": "Annual projection festival", "permanent": False, "year_started": 2009,
     "description": "The world's largest festival of light, music, and ideas. The Opera House and Harbour Bridge become giant canvases."},
    {"name": "Fete des Lumieres", "city": "Lyon, France", "lat": 45.7640, "lon": 4.8357,
     "type": "Annual light festival", "permanent": False, "year_started": 1852,
     "description": "Lyon's Festival of Lights transforms the city every December with over 70 light installations across major buildings."},
    {"name": "TeamLab Borderless", "city": "Tokyo, Japan", "lat": 35.6253, "lon": 139.7739,
     "type": "Permanent digital art museum", "permanent": True, "year_started": 2018,
     "description": "An immersive digital art museum where projections flow between rooms, creating a borderless art experience."},
    {"name": "Amsterdam Light Festival", "city": "Amsterdam, Netherlands", "lat": 52.3676, "lon": 4.9041,
     "type": "Annual light festival", "permanent": False, "year_started": 2012,
     "description": "Light artworks and installations along the canals of Amsterdam, best experienced by boat during winter."},
    {"name": "Lumiere London", "city": "London, UK", "lat": 51.5074, "lon": -0.1278,
     "type": "Biennial light festival", "permanent": False, "year_started": 2016,
     "description": "London's largest outdoor art commission, with installations from Piccadilly to King's Cross."},
    {"name": "The Bay Lights", "city": "San Francisco, USA", "lat": 37.7983, "lon": -122.3778,
     "type": "Permanent LED installation", "permanent": True, "year_started": 2013,
     "description": "25,000 LEDs on the San Francisco Bay Bridge's suspension cables, creating the world's largest LED sculpture."},
    {"name": "Neon Museum", "city": "Las Vegas, USA", "lat": 36.1768, "lon": -115.1353,
     "type": "Museum / outdoor gallery", "permanent": True, "year_started": 1996,
     "description": "A museum dedicated to preserving Las Vegas's iconic neon signs, with an outdoor 'Neon Boneyard' of rescued signs."},
    {"name": "Luminale (Light & Building)", "city": "Frankfurt, Germany", "lat": 50.1109, "lon": 8.6821,
     "type": "Biennial light festival", "permanent": False, "year_started": 2002,
     "description": "Frankfurt's biennial light and urban design event, transforming the city's skyline with projections and LED art."},
    {"name": "Northern Lights Cathedral", "city": "Alta, Norway", "lat": 69.9689, "lon": 23.2716,
     "type": "Permanent architectural light", "permanent": True, "year_started": 2013,
     "description": "A spiral titanium cathedral designed to capture and reflect the Northern Lights, itself a light sculpture."},
    {"name": "KANAAL Light Art Collection", "city": "Mechelen, Belgium", "lat": 51.0259, "lon": 4.4777,
     "type": "Permanent gallery", "permanent": True, "year_started": 2019,
     "description": "Axel Vervoordt's permanent collection includes major light-art installations by James Turrell and Anish Kapoor."},
    {"name": "i Light Singapore", "city": "Singapore", "lat": 1.2834, "lon": 103.8607,
     "type": "Annual light festival", "permanent": False, "year_started": 2010,
     "description": "Asia's leading sustainable light art festival at Marina Bay, using eco-friendly materials and energy-efficient lighting."},
    {"name": "Seoul Lantern Festival", "city": "Seoul, South Korea", "lat": 37.5690, "lon": 126.9882,
     "type": "Annual lantern festival", "permanent": False, "year_started": 2009,
     "description": "Thousands of lanterns float along the Cheonggyecheon Stream, combining traditional Korean craft with contemporary light art."},
]


# ══════════════════════════════════════════════════════════════════════════════
# OVERPASS API QUERIES
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _fetch_artwork_overpass(lat: float, lon: float, radius_km: float,
                            artwork_types: list | None = None) -> list:
    """
    Query the Overpass API for tourism=artwork features near a point.
    Optionally filter by artwork_type (mural, sculpture, graffiti, etc.).
    Returns a list of feature dicts with lat, lon, name, tags.
    """
    radius_m = int(radius_km * 1000)

    if artwork_types:
        type_clauses = []
        for atype in artwork_types:
            type_clauses.append(
                f'node["tourism"="artwork"]["artwork_type"="{atype}"]'
                f'(around:{radius_m},{lat},{lon});'
            )
            type_clauses.append(
                f'way["tourism"="artwork"]["artwork_type"="{atype}"]'
                f'(around:{radius_m},{lat},{lon});'
            )
        body = "\n  ".join(type_clauses)
    else:
        body = (
            f'node["tourism"="artwork"](around:{radius_m},{lat},{lon});\n'
            f'  way["tourism"="artwork"](around:{radius_m},{lat},{lon});'
        )

    query = f"""
[out:json][timeout:90];
(
  {body}
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []

    elements = result.get("elements", [])

    # Build node lookup for ways
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        lat_f, lon_f = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat_f, lon_f = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [node_lookup[n] for n in nodes if n in node_lookup]
            if coords:
                lat_f = sum(c[0] for c in coords) / len(coords)
                lon_f = sum(c[1] for c in coords) / len(coords)

        if lat_f is None or lon_f is None:
            continue

        features.append({
            "name": tags.get("name", tags.get("name:en", "Unnamed artwork")),
            "artwork_type": tags.get("artwork_type", "unknown"),
            "artist": tags.get("artist_name", tags.get("artist", "")),
            "material": tags.get("material", ""),
            "year": tags.get("start_date", tags.get("year", "")),
            "description": tags.get("description", tags.get("description:en", "")),
            "wikipedia": tags.get("wikipedia", ""),
            "wikidata": tags.get("wikidata", ""),
            "website": tags.get("website", tags.get("url", "")),
            "lat": lat_f,
            "lon": lon_f,
            "osm_id": el.get("id"),
        })

    return features


@st.cache_data(ttl=3600)
def _fetch_sculptures_overpass(lat: float, lon: float, radius_km: float) -> list:
    """Fetch public sculptures and art installations from Overpass."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:90];
(
  node["tourism"="artwork"]["artwork_type"="sculpture"](around:{radius_m},{lat},{lon});
  way["tourism"="artwork"]["artwork_type"="sculpture"](around:{radius_m},{lat},{lon});
  node["tourism"="artwork"]["artwork_type"="installation"](around:{radius_m},{lat},{lon});
  way["tourism"="artwork"]["artwork_type"="installation"](around:{radius_m},{lat},{lon});
  node["tourism"="artwork"]["artwork_type"="statue"](around:{radius_m},{lat},{lon});
  way["tourism"="artwork"]["artwork_type"="statue"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []

    elements = result.get("elements", [])
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        lat_f, lon_f = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat_f, lon_f = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [node_lookup[n] for n in nodes if n in node_lookup]
            if coords:
                lat_f = sum(c[0] for c in coords) / len(coords)
                lon_f = sum(c[1] for c in coords) / len(coords)
        if lat_f is None or lon_f is None:
            continue
        features.append({
            "name": tags.get("name", tags.get("name:en", "Unnamed sculpture")),
            "artwork_type": tags.get("artwork_type", "sculpture"),
            "artist": tags.get("artist_name", tags.get("artist", "")),
            "material": tags.get("material", ""),
            "year": tags.get("start_date", tags.get("year", "")),
            "description": tags.get("description", ""),
            "lat": lat_f,
            "lon": lon_f,
            "osm_id": el.get("id"),
        })
    return features


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: Build a dark folium map
# ══════════════════════════════════════════════════════════════════════════════

def _make_dark_map(center_lat: float, center_lon: float, zoom: int = 4) -> folium.Map:
    """Create a Folium map with CartoDB dark_matter tiles."""
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )
    return m


def _safe(text: str) -> str:
    """html.escape wrapper for popup safety."""
    return html.escape(str(text)) if text else ""


def _popup_html(lines: list[tuple[str, str]], max_width: int = 260) -> folium.Popup:
    """Build a dark-themed HTML popup from key-value pairs."""
    rows = ""
    for label, value in lines:
        if value:
            safe_val = _safe(value)
            rows += (
                f'<tr><td style="color:#8b97b0;font-size:0.7rem;padding:1px 6px 1px 0;">'
                f'{_safe(label)}</td>'
                f'<td style="color:#e8ecf4;font-size:0.75rem;padding:1px 0;">'
                f'{safe_val}</td></tr>'
            )
    inner = f"""
    <div style="background:#111827;border-radius:6px;padding:8px;max-width:{max_width}px;">
        <table style="border-collapse:collapse;">{rows}</table>
    </div>
    """
    return folium.Popup(inner, max_width=max_width + 20)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: Stats row
# ══════════════════════════════════════════════════════════════════════════════

def _stats_row(metrics: list[tuple[str, str | int]]):
    """Render a row of st.metric cards."""
    cols = st.columns(min(len(metrics), 6))
    for i, (label, value) in enumerate(metrics):
        cols[i % len(cols)].metric(label, value)


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: DataFrame display + CSV download
# ══════════════════════════════════════════════════════════════════════════════

def _show_table_and_download(df: pd.DataFrame, label: str, key_suffix: str):
    """Display dataframe + CSV download button."""
    with st.expander(f"Data Table ({len(df)} records)", expanded=False):
        st.dataframe(df, use_container_width=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} {label} (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"street_art_{key_suffix}.csv",
        mime="text/csv",
        key=f"sa_dl_{key_suffix}",
    )


# ══════════════════════════════════════════════════════════════════════════════
# HELPER: matplotlib bar chart (dark theme)
# ══════════════════════════════════════════════════════════════════════════════

def _dark_bar_chart(labels: list, values: list, colors: list | str,
                    xlabel: str = "Count", title: str = ""):
    """Horizontal bar chart with the TerraScout dark palette."""
    fig, ax = plt.subplots(figsize=(6, max(2.5, len(labels) * 0.45)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    if isinstance(colors, str):
        colors = [colors] * len(labels)

    ax.barh(range(len(labels)), values, color=colors, alpha=0.85)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels([str(l)[:30] for l in labels], color="#e8ecf4", fontsize=9)
    ax.set_xlabel(xlabel, color="#8b97b0", fontsize=10)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    if title:
        ax.set_title(title, color="#e8ecf4", fontsize=11, pad=10)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# MODE RENDER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _render_mode_1_street_art_capitals():
    """Mode 1: World Street Art Capitals."""
    st.markdown("##### World Street Art Capitals")
    st.caption(MODE_DESCRIPTIONS["World Street Art Capitals"])

    # ── City selector ──
    city_names = [c["city"] for c in STREET_ART_CAPITALS]
    selected_city = st.selectbox(
        "Select a city to explore (or view all on map)",
        ["All Cities"] + city_names,
        key="sa_m1_city",
    )

    # ── Stats ──
    total_artworks = sum(c["est_artworks"] for c in STREET_ART_CAPITALS)
    total_cities = len(STREET_ART_CAPITALS)
    top_city = max(STREET_ART_CAPITALS, key=lambda c: c["est_artworks"])
    _stats_row([
        ("Cities Mapped", total_cities),
        ("Est. Total Artworks", f"{total_artworks:,}"),
        ("Top City", top_city["city"]),
        ("Top City Artworks", f"{top_city['est_artworks']:,}"),
    ])

    # ── Map ──
    st.markdown("---")
    if selected_city == "All Cities":
        m = _make_dark_map(20.0, 0.0, zoom=2)
        cities_to_show = STREET_ART_CAPITALS
    else:
        city_data = next(c for c in STREET_ART_CAPITALS if c["city"] == selected_city)
        m = _make_dark_map(city_data["lat"], city_data["lon"], zoom=12)
        cities_to_show = [city_data]

    for c in cities_to_show:
        popup = _popup_html([
            ("City", c["city"]),
            ("Country", c["country"]),
            ("Highlights", c["highlight"]),
            ("Notable Artists", c["notable_artists"]),
            ("Est. Artworks", str(c["est_artworks"])),
        ])
        folium.CircleMarker(
            location=[c["lat"], c["lon"]],
            radius=max(6, min(14, c["est_artworks"] // 1000 + 6)),
            color="#06b6d4",
            fill=True,
            fill_color="#06b6d4",
            fill_opacity=0.7,
            weight=2,
            popup=popup,
            tooltip=_safe(c["city"]),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # ── Fetch OSM artwork data for selected city ──
    if selected_city != "All Cities":
        city_data = next(c for c in STREET_ART_CAPITALS if c["city"] == selected_city)
        with st.spinner(f"Searching street art in {selected_city} via Overpass API..."):
            osm_features = _fetch_artwork_overpass(
                city_data["lat"], city_data["lon"], city_data["radius"],
                artwork_types=["mural", "graffiti", "street_art"],
            )
        if osm_features:
            st.success(f"Found {len(osm_features)} artworks from OpenStreetMap in {selected_city}")
            m2 = _make_dark_map(city_data["lat"], city_data["lon"], zoom=13)
            for f in osm_features:
                popup = _popup_html([
                    ("Name", f["name"]),
                    ("Type", f["artwork_type"]),
                    ("Artist", f["artist"]),
                    ("Year", f["year"]),
                ])
                folium.CircleMarker(
                    location=[f["lat"], f["lon"]],
                    radius=5,
                    color="#ec4899",
                    fill=True,
                    fill_color="#ec4899",
                    fill_opacity=0.7,
                    weight=1,
                    popup=popup,
                    tooltip=_safe(f["name"]),
                ).add_to(m2)
            components.html(m2._repr_html_(), height=500)

            osm_df = pd.DataFrame(osm_features)
            _show_table_and_download(osm_df, "artworks", f"capitals_{selected_city}")
        else:
            st.info(f"No OSM artwork data found for {selected_city}. Showing curated data only.")

    # ── City info & chart ──
    st.markdown("---")
    col_info, col_chart = st.columns([1, 1])
    with col_info:
        st.markdown("##### City Profiles")
        for c in STREET_ART_CAPITALS:
            st.markdown(
                f'<div style="border-left:3px solid #06b6d4;padding:6px 12px;margin-bottom:8px;">'
                f'<strong style="color:#e8ecf4;">{_safe(c["city"])}, {_safe(c["country"])}</strong><br/>'
                f'<span style="color:#8b97b0;font-size:0.8rem;">{_safe(c["description"])}</span><br/>'
                f'<span style="color:#06b6d4;font-size:0.75rem;">Artists: {_safe(c["notable_artists"])}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_chart:
        st.markdown("##### Estimated Artwork Count by City")
        _dark_bar_chart(
            labels=[c["city"] for c in sorted(STREET_ART_CAPITALS, key=lambda x: x["est_artworks"])],
            values=[c["est_artworks"] for c in sorted(STREET_ART_CAPITALS, key=lambda x: x["est_artworks"])],
            colors="#06b6d4",
            xlabel="Estimated Artworks",
        )

    # ── Full curated table download ──
    curated_df = pd.DataFrame(STREET_ART_CAPITALS)
    _show_table_and_download(curated_df, "street art capitals", "capitals_all")


def _render_mode_2_banksy():
    """Mode 2: Banksy Locations."""
    st.markdown("##### Banksy Locations")
    st.caption(MODE_DESCRIPTIONS["Banksy Locations"])

    # ── Stats ──
    extant = sum(1 for b in BANKSY_WORKS if "Extant" in b["status"])
    removed = sum(1 for b in BANKSY_WORKS if "Removed" in b["status"] or "Destroyed" in b["status"])
    countries = len(set(b["city"].split(", ")[-1] for b in BANKSY_WORKS))
    years = [b["year"] for b in BANKSY_WORKS]
    _stats_row([
        ("Total Works Mapped", len(BANKSY_WORKS)),
        ("Still Extant", extant),
        ("Removed/Destroyed", removed),
        ("Countries", countries),
        ("Year Range", f"{min(years)}-{max(years)}"),
    ])

    # ── Filter ──
    status_filter = st.multiselect(
        "Filter by status",
        ["Extant", "Removed", "Destroyed", "All"],
        default=["All"],
        key="sa_m2_status",
    )

    filtered = BANKSY_WORKS
    if "All" not in status_filter:
        filtered = [b for b in BANKSY_WORKS
                     if any(s.lower() in b["status"].lower() for s in status_filter)]

    # ── Map ──
    st.markdown("---")
    m = _make_dark_map(51.5, -1.0, zoom=5)
    for b in filtered:
        color = "#10b981" if "Extant" in b["status"] else "#ef4444"
        popup = _popup_html([
            ("Title", b["title"]),
            ("City", b["city"]),
            ("Year", str(b["year"])),
            ("Status", b["status"]),
            ("Description", b["description"][:150]),
        ])
        folium.CircleMarker(
            location=[b["lat"], b["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            weight=2,
            popup=popup,
            tooltip=_safe(b["title"]),
        ).add_to(m)

    # Legend
    st.markdown(
        '<span style="color:#10b981;font-size:0.8rem;">&#9679; Extant</span> &nbsp; '
        '<span style="color:#ef4444;font-size:0.8rem;">&#9679; Removed/Destroyed</span>',
        unsafe_allow_html=True,
    )
    components.html(m._repr_html_(), height=500)

    # ── Timeline chart ──
    st.markdown("---")
    col_list, col_chart = st.columns([1, 1])
    with col_list:
        st.markdown("##### Works List")
        for b in sorted(filtered, key=lambda x: x["year"], reverse=True):
            status_color = "#10b981" if "Extant" in b["status"] else "#ef4444"
            st.markdown(
                f'<div style="border-left:3px solid {status_color};padding:4px 10px;margin-bottom:6px;">'
                f'<strong style="color:#e8ecf4;">{_safe(b["title"])}</strong> '
                f'<span style="color:#8b97b0;font-size:0.8rem;">({b["year"]})</span><br/>'
                f'<span style="color:#8b97b0;font-size:0.75rem;">{_safe(b["city"])} -- {_safe(b["status"])}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_chart:
        st.markdown("##### Works by Year")
        year_counts = {}
        for b in BANKSY_WORKS:
            year_counts[b["year"]] = year_counts.get(b["year"], 0) + 1
        sorted_years = sorted(year_counts.keys())

        fig, ax = plt.subplots(figsize=(6, 4))
        fig.patch.set_facecolor("#0a0e1a")
        ax.set_facecolor("#111827")
        ax.bar(sorted_years, [year_counts[y] for y in sorted_years], color="#f59e0b", alpha=0.85)
        ax.set_xlabel("Year", color="#8b97b0", fontsize=10)
        ax.set_ylabel("Works", color="#8b97b0", fontsize=10)
        ax.tick_params(axis="both", colors="#8b97b0", labelsize=8)
        ax.grid(True, axis="y", color="#2a3550", linewidth=0.5, alpha=0.7)
        for spine in ax.spines.values():
            spine.set_color("#2a3550")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # ── Table & download ──
    df = pd.DataFrame(filtered)
    _show_table_and_download(df, "Banksy works", "banksy")


def _render_mode_3_mural_districts():
    """Mode 3: Mural Districts."""
    st.markdown("##### Mural Districts & Street Art Precincts")
    st.caption(MODE_DESCRIPTIONS["Mural Districts"])

    # ── Stats ──
    total_murals = sum(d["est_murals"] for d in MURAL_DISTRICTS)
    top_district = max(MURAL_DISTRICTS, key=lambda d: d["est_murals"])
    _stats_row([
        ("Districts Mapped", len(MURAL_DISTRICTS)),
        ("Est. Total Murals", f"{total_murals:,}"),
        ("Largest District", top_district["name"]),
        ("Oldest", min(MURAL_DISTRICTS, key=lambda d: d["year_started"])["name"]),
    ])

    # ── District selector for API lookup ──
    district_names = [d["name"] for d in MURAL_DISTRICTS]
    selected = st.selectbox("Select a district for detailed map", ["All Districts"] + district_names, key="sa_m3_sel")

    # ── Map ──
    st.markdown("---")
    if selected == "All Districts":
        m = _make_dark_map(20.0, 0.0, zoom=2)
        districts_to_show = MURAL_DISTRICTS
    else:
        dd = next(d for d in MURAL_DISTRICTS if d["name"] == selected)
        m = _make_dark_map(dd["lat"], dd["lon"], zoom=14)
        districts_to_show = [dd]

    for d in districts_to_show:
        popup = _popup_html([
            ("Name", d["name"]),
            ("City", d["city"]),
            ("Since", str(d["year_started"])),
            ("Est. Murals", str(d["est_murals"])),
            ("Artists", d["notable_artists"]),
        ])
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=max(6, min(14, d["est_murals"] // 50 + 6)),
            color="#ec4899",
            fill=True,
            fill_color="#ec4899",
            fill_opacity=0.7,
            weight=2,
            popup=popup,
            tooltip=_safe(d["name"]),
        ).add_to(m)

        if selected != "All Districts":
            folium.Circle(
                location=[d["lat"], d["lon"]],
                radius=d["radius"] * 1000,
                color="#ec4899",
                fill=True,
                fill_opacity=0.05,
                weight=1,
            ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # ── OSM artworks for selected district ──
    if selected != "All Districts":
        dd = next(d for d in MURAL_DISTRICTS if d["name"] == selected)
        with st.spinner(f"Searching artworks in {selected} via Overpass API..."):
            osm_art = _fetch_artwork_overpass(dd["lat"], dd["lon"], dd["radius"])
        if osm_art:
            st.success(f"Found {len(osm_art)} artworks in {selected} from OpenStreetMap")
            m2 = _make_dark_map(dd["lat"], dd["lon"], zoom=15)
            for f in osm_art:
                popup = _popup_html([
                    ("Name", f["name"]),
                    ("Type", f["artwork_type"]),
                    ("Artist", f["artist"]),
                ])
                folium.CircleMarker(
                    location=[f["lat"], f["lon"]],
                    radius=5,
                    color="#a855f7",
                    fill=True,
                    fill_color="#a855f7",
                    fill_opacity=0.7,
                    weight=1,
                    popup=popup,
                    tooltip=_safe(f["name"]),
                ).add_to(m2)
            components.html(m2._repr_html_(), height=500)
            osm_df = pd.DataFrame(osm_art)
            _show_table_and_download(osm_df, "artworks", f"district_{selected.replace(' ', '_')}")

    # ── Chart ──
    st.markdown("---")
    st.markdown("##### Murals by District")
    sorted_d = sorted(MURAL_DISTRICTS, key=lambda x: x["est_murals"])
    _dark_bar_chart(
        labels=[d["name"] for d in sorted_d],
        values=[d["est_murals"] for d in sorted_d],
        colors="#ec4899",
        xlabel="Estimated Murals",
    )

    # ── Table & download ──
    df = pd.DataFrame(MURAL_DISTRICTS)
    _show_table_and_download(df, "mural districts", "mural_districts")


def _render_mode_4_political_murals():
    """Mode 4: Political Murals."""
    st.markdown("##### Political Murals & Protest Art")
    st.caption(MODE_DESCRIPTIONS["Political Murals"])

    # ── Stats ──
    total_murals = sum(p["est_murals"] for p in POLITICAL_MURALS)
    countries = len(set(p["city"].split(", ")[-1] for p in POLITICAL_MURALS))
    _stats_row([
        ("Sites Mapped", len(POLITICAL_MURALS)),
        ("Est. Total Murals", f"{total_murals:,}"),
        ("Countries", countries),
        ("Most Murals", max(POLITICAL_MURALS, key=lambda p: p["est_murals"])["name"][:25]),
    ])

    # ── Map ──
    st.markdown("---")
    m = _make_dark_map(30.0, 0.0, zoom=2)
    for p in POLITICAL_MURALS:
        popup = _popup_html([
            ("Name", p["name"]),
            ("City", p["city"]),
            ("Perspective", p["side"]),
            ("Period", p["period"]),
            ("Est. Murals", str(p["est_murals"])),
            ("Description", p["description"][:150]),
        ])
        folium.CircleMarker(
            location=[p["lat"], p["lon"]],
            radius=max(5, min(12, p["est_murals"] // 30 + 5)),
            color="#ef4444",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.7,
            weight=2,
            popup=popup,
            tooltip=_safe(p["name"]),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # ── Detailed list ──
    st.markdown("---")
    st.markdown("##### Site Details")
    for p in POLITICAL_MURALS:
        st.markdown(
            f'<div style="border-left:3px solid #ef4444;padding:6px 12px;margin-bottom:8px;">'
            f'<strong style="color:#e8ecf4;">{_safe(p["name"])}</strong> '
            f'<span style="color:#8b97b0;font-size:0.8rem;">({_safe(p["city"])})</span><br/>'
            f'<span style="color:#5a6580;font-size:0.75rem;">{_safe(p["side"])} | {_safe(p["period"])}</span><br/>'
            f'<span style="color:#8b97b0;font-size:0.8rem;">{_safe(p["description"])}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Chart ──
    st.markdown("---")
    st.markdown("##### Murals by Site")
    sorted_p = sorted(POLITICAL_MURALS, key=lambda x: x["est_murals"])
    _dark_bar_chart(
        labels=[p["name"][:25] for p in sorted_p],
        values=[p["est_murals"] for p in sorted_p],
        colors="#ef4444",
        xlabel="Estimated Murals",
    )

    # ── Table & download ──
    df = pd.DataFrame(POLITICAL_MURALS)
    _show_table_and_download(df, "political mural sites", "political_murals")


def _render_mode_5_3d_art():
    """Mode 5: 3D Street Art & Illusions."""
    st.markdown("##### 3D Street Art & Optical Illusions")
    st.caption(MODE_DESCRIPTIONS["3D Street Art & Illusions"])

    # ── Stats ──
    art_types = {}
    for a in THREE_D_ART:
        art_types[a["type"]] = art_types.get(a["type"], 0) + 1
    countries = len(set(a["city"].split(", ")[-1] for a in THREE_D_ART))
    artists = len(set(a["artist"] for a in THREE_D_ART))
    _stats_row([
        ("Works Mapped", len(THREE_D_ART)),
        ("Unique Artists", artists),
        ("Countries", countries),
        ("Art Types", len(art_types)),
    ])

    # ── Map ──
    st.markdown("---")
    m = _make_dark_map(30.0, 10.0, zoom=3)
    for a in THREE_D_ART:
        popup = _popup_html([
            ("Title", a["title"]),
            ("Artist", a["artist"]),
            ("City", a["city"]),
            ("Year", str(a["year"])),
            ("Type", a["type"]),
            ("Description", a["description"][:150]),
        ])
        folium.CircleMarker(
            location=[a["lat"], a["lon"]],
            radius=7,
            color="#a855f7",
            fill=True,
            fill_color="#a855f7",
            fill_opacity=0.7,
            weight=2,
            popup=popup,
            tooltip=_safe(a["title"]),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # ── Detail cards ──
    st.markdown("---")
    col_cards, col_chart = st.columns([1, 1])
    with col_cards:
        st.markdown("##### Artworks")
        for a in THREE_D_ART:
            st.markdown(
                f'<div style="border-left:3px solid #a855f7;padding:4px 10px;margin-bottom:6px;">'
                f'<strong style="color:#e8ecf4;">{_safe(a["title"])}</strong><br/>'
                f'<span style="color:#a855f7;font-size:0.8rem;">{_safe(a["artist"])}</span> '
                f'<span style="color:#5a6580;font-size:0.75rem;">| {_safe(a["city"])} ({a["year"]})</span><br/>'
                f'<span style="color:#8b97b0;font-size:0.75rem;">{_safe(a["description"][:120])}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with col_chart:
        st.markdown("##### Art Types Breakdown")
        _dark_bar_chart(
            labels=list(art_types.keys()),
            values=list(art_types.values()),
            colors="#a855f7",
            xlabel="Count",
        )

    # ── Table & download ──
    df = pd.DataFrame(THREE_D_ART)
    _show_table_and_download(df, "3D artworks", "3d_art")


def _render_mode_6_graffiti_history():
    """Mode 6: Graffiti History."""
    st.markdown("##### Graffiti History -- Birth & Evolution")
    st.caption(MODE_DESCRIPTIONS["Graffiti History"])

    # ── Stats ──
    eras = {}
    for g in GRAFFITI_HISTORY:
        eras[g["era"]] = eras.get(g["era"], 0) + 1
    years = [g["year"] for g in GRAFFITI_HISTORY]
    _stats_row([
        ("Landmarks Mapped", len(GRAFFITI_HISTORY)),
        ("Era Span", f"{min(years)}-{max(years)}"),
        ("Eras Covered", len(eras)),
        ("Cities", len(set(g["city"] for g in GRAFFITI_HISTORY))),
    ])

    # ── Era filter ──
    era_filter = st.multiselect(
        "Filter by era",
        list(eras.keys()),
        default=list(eras.keys()),
        key="sa_m6_era",
    )
    filtered = [g for g in GRAFFITI_HISTORY if g["era"] in era_filter]

    # ── Map ──
    st.markdown("---")
    m = _make_dark_map(42.0, -20.0, zoom=3)
    era_colors = {
        "Proto-graffiti": "#f97316",
        "Birth of graffiti": "#ef4444",
        "Subway era": "#ec4899",
        "Golden age institution": "#a855f7",
        "Graffiti film": "#8b5cf6",
        "Documentation": "#06b6d4",
        "European pioneers": "#10b981",
        "European expansion": "#14b8a6",
        "Street-to-gallery": "#f59e0b",
        "Political expression": "#3b82f6",
    }
    for g in filtered:
        color = era_colors.get(g["era"], "#8b97b0")
        popup = _popup_html([
            ("Title", g["title"]),
            ("City", g["city"]),
            ("Year", str(g["year"])),
            ("Era", g["era"]),
            ("Significance", g["significance"]),
        ])
        folium.CircleMarker(
            location=[g["lat"], g["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            weight=2,
            popup=popup,
            tooltip=_safe(g["title"]),
        ).add_to(m)

    # Legend
    legend_html = " &nbsp; ".join(
        f'<span style="color:{c};font-size:0.75rem;">&#9679; {_safe(e)}</span>'
        for e, c in era_colors.items() if e in era_filter
    )
    st.markdown(legend_html, unsafe_allow_html=True)
    components.html(m._repr_html_(), height=500)

    # ── Timeline ──
    st.markdown("---")
    st.markdown("##### Timeline")
    for g in sorted(filtered, key=lambda x: x["year"]):
        color = era_colors.get(g["era"], "#8b97b0")
        st.markdown(
            f'<div style="border-left:3px solid {color};padding:4px 10px;margin-bottom:6px;">'
            f'<strong style="color:#e8ecf4;">{g["year"]} -- {_safe(g["title"])}</strong><br/>'
            f'<span style="color:{color};font-size:0.8rem;">{_safe(g["era"])}</span> '
            f'<span style="color:#5a6580;font-size:0.75rem;">| {_safe(g["city"])}</span><br/>'
            f'<span style="color:#8b97b0;font-size:0.75rem;">{_safe(g["description"][:150])}</span><br/>'
            f'<span style="color:#06b6d4;font-size:0.7rem;font-style:italic;">{_safe(g["significance"])}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Chart ──
    st.markdown("---")
    st.markdown("##### Landmarks by Era")
    _dark_bar_chart(
        labels=list(eras.keys()),
        values=list(eras.values()),
        colors=[era_colors.get(e, "#8b97b0") for e in eras.keys()],
        xlabel="Landmarks",
    )

    # ── Table & download ──
    df = pd.DataFrame(filtered)
    _show_table_and_download(df, "graffiti landmarks", "graffiti_history")


def _render_mode_7_museums():
    """Mode 7: Street Art Museums."""
    st.markdown("##### Street Art Museums & Galleries")
    st.caption(MODE_DESCRIPTIONS["Street Art Museums"])

    # ── Stats ──
    museum_types = {}
    for mu in STREET_ART_MUSEUMS:
        museum_types[mu["type"]] = museum_types.get(mu["type"], 0) + 1
    countries = len(set(mu["city"].split(", ")[-1] for mu in STREET_ART_MUSEUMS))
    oldest = min(STREET_ART_MUSEUMS, key=lambda mu: mu["year_opened"])
    _stats_row([
        ("Museums Mapped", len(STREET_ART_MUSEUMS)),
        ("Types", len(museum_types)),
        ("Countries", countries),
        ("Oldest", f"{oldest['name'][:20]} ({oldest['year_opened']})"),
    ])

    # ── Map ──
    st.markdown("---")
    m = _make_dark_map(35.0, 0.0, zoom=2)
    for mu in STREET_ART_MUSEUMS:
        popup = _popup_html([
            ("Name", mu["name"]),
            ("City", mu["city"]),
            ("Type", mu["type"]),
            ("Opened", str(mu["year_opened"])),
            ("Collection", mu["collection"]),
        ])
        folium.CircleMarker(
            location=[mu["lat"], mu["lon"]],
            radius=8,
            color="#8b5cf6",
            fill=True,
            fill_color="#8b5cf6",
            fill_opacity=0.7,
            weight=2,
            popup=popup,
            tooltip=_safe(mu["name"]),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # ── Detail cards ──
    st.markdown("---")
    st.markdown("##### Museum Profiles")
    for mu in STREET_ART_MUSEUMS:
        st.markdown(
            f'<div style="border-left:3px solid #8b5cf6;padding:6px 12px;margin-bottom:8px;">'
            f'<strong style="color:#e8ecf4;">{_safe(mu["name"])}</strong> '
            f'<span style="color:#5a6580;font-size:0.8rem;">({_safe(mu["city"])})</span><br/>'
            f'<span style="color:#8b5cf6;font-size:0.75rem;">{_safe(mu["type"])} | Est. {mu["year_opened"]}</span><br/>'
            f'<span style="color:#8b97b0;font-size:0.8rem;">{_safe(mu["description"])}</span><br/>'
            f'<span style="color:#06b6d4;font-size:0.75rem;">Collection: {_safe(mu["collection"])}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Chart ──
    st.markdown("---")
    st.markdown("##### Museums by Type")
    _dark_bar_chart(
        labels=list(museum_types.keys()),
        values=list(museum_types.values()),
        colors="#8b5cf6",
        xlabel="Count",
    )

    # ── Table & download ──
    df = pd.DataFrame(STREET_ART_MUSEUMS)
    _show_table_and_download(df, "street art museums", "museums")


def _render_mode_8_sculpture():
    """Mode 8: Sculpture & Installation Art."""
    st.markdown("##### Public Sculpture & Installation Art")
    st.caption(MODE_DESCRIPTIONS["Sculpture & Installation Art"])

    # ── Stats ──
    art_types = {}
    for s in SCULPTURE_INSTALLATIONS:
        art_types[s["type"]] = art_types.get(s["type"], 0) + 1
    artists = len(set(s["artist"] for s in SCULPTURE_INSTALLATIONS))
    _stats_row([
        ("Sculptures Mapped", len(SCULPTURE_INSTALLATIONS)),
        ("Unique Artists", artists),
        ("Art Types", len(art_types)),
        ("Oldest", str(min(s["year"] for s in SCULPTURE_INSTALLATIONS))),
    ])

    # ── City search for Overpass data ──
    st.markdown("---")
    st.markdown("##### Search OSM for Sculptures Near a Location")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        sc_lat = st.number_input("Latitude", value=40.7580, format="%.4f", key="sa_m8_lat")
    with col2:
        sc_lon = st.number_input("Longitude", value=-73.9855, format="%.4f", key="sa_m8_lon")
    with col3:
        sc_radius = st.slider("Radius (km)", 1, 20, 5, key="sa_m8_rad")

    if st.button("Search Sculptures", key="sa_m8_search"):
        with st.spinner("Searching sculptures via Overpass API..."):
            osm_sculpts = _fetch_sculptures_overpass(sc_lat, sc_lon, sc_radius)
        if osm_sculpts:
            st.success(f"Found {len(osm_sculpts)} sculptures/installations from OpenStreetMap")
            m_osm = _make_dark_map(sc_lat, sc_lon, zoom=13)
            for f in osm_sculpts:
                popup = _popup_html([
                    ("Name", f["name"]),
                    ("Type", f["artwork_type"]),
                    ("Artist", f["artist"]),
                    ("Material", f["material"]),
                    ("Year", f["year"]),
                ])
                folium.CircleMarker(
                    location=[f["lat"], f["lon"]],
                    radius=6,
                    color="#10b981",
                    fill=True,
                    fill_color="#10b981",
                    fill_opacity=0.7,
                    weight=1,
                    popup=popup,
                    tooltip=_safe(f["name"]),
                ).add_to(m_osm)
            components.html(m_osm._repr_html_(), height=500)
            osm_df = pd.DataFrame(osm_sculpts)
            _show_table_and_download(osm_df, "sculptures", "sculptures_osm")
        else:
            st.info("No sculptures found in this area. Try a larger radius or different location.")

    # ── Curated map ──
    st.markdown("---")
    st.markdown("##### Iconic Public Sculptures Worldwide")
    m = _make_dark_map(30.0, 0.0, zoom=2)
    for s in SCULPTURE_INSTALLATIONS:
        popup = _popup_html([
            ("Name", s["name"]),
            ("Artist", s["artist"]),
            ("City", s["city"]),
            ("Year", str(s["year"])),
            ("Type", s["type"]),
            ("Description", s["description"][:150]),
        ])
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color="#10b981",
            fill=True,
            fill_color="#10b981",
            fill_opacity=0.7,
            weight=2,
            popup=popup,
            tooltip=_safe(s["name"]),
        ).add_to(m)

    components.html(m._repr_html_(), height=500)

    # ── Detail cards ──
    st.markdown("---")
    col_list, col_chart = st.columns([1, 1])
    with col_list:
        st.markdown("##### Artwork Profiles")
        for s in SCULPTURE_INSTALLATIONS:
            st.markdown(
                f'<div style="border-left:3px solid #10b981;padding:4px 10px;margin-bottom:6px;">'
                f'<strong style="color:#e8ecf4;">{_safe(s["name"])}</strong><br/>'
                f'<span style="color:#10b981;font-size:0.8rem;">{_safe(s["artist"])}</span> '
                f'<span style="color:#5a6580;font-size:0.75rem;">| {_safe(s["city"])} ({s["year"]})</span><br/>'
                f'<span style="color:#8b97b0;font-size:0.75rem;">{_safe(s["description"][:120])}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with col_chart:
        st.markdown("##### By Type")
        _dark_bar_chart(
            labels=list(art_types.keys()),
            values=list(art_types.values()),
            colors="#10b981",
            xlabel="Count",
        )

    # ── Table & download ──
    df = pd.DataFrame(SCULPTURE_INSTALLATIONS)
    _show_table_and_download(df, "sculptures", "sculpture_curated")


def _render_mode_9_indigenous():
    """Mode 9: Indigenous & Traditional Murals."""
    st.markdown("##### Indigenous & Traditional Mural Art")
    st.caption(MODE_DESCRIPTIONS["Indigenous & Traditional Murals"])

    # ── Stats ──
    traditions = {}
    for ig in INDIGENOUS_MURALS:
        traditions[ig["tradition"]] = traditions.get(ig["tradition"], 0) + 1
    countries = len(set(ig["city"].split(", ")[-1] for ig in INDIGENOUS_MURALS))
    _stats_row([
        ("Sites Mapped", len(INDIGENOUS_MURALS)),
        ("Traditions", len(traditions)),
        ("Countries", countries),
        ("Heritage Sites", sum(1 for ig in INDIGENOUS_MURALS if "UNESCO" in ig["significance"])),
    ])

    # ── Map ──
    st.markdown("---")
    m = _make_dark_map(10.0, 0.0, zoom=2)
    tradition_colors = {
        "Aboriginal Australian": "#f59e0b",
        "Mexican Muralism": "#ef4444",
        "Ancient Maya": "#a855f7",
        "Ndebele": "#ec4899",
        "Ethiopian Orthodox": "#10b981",
        "Warli tribal": "#f97316",
        "Haida (First Nations)": "#06b6d4",
        "Maori (Aotearoa)": "#3b82f6",
        "Contemporary Aboriginal": "#14b8a6",
    }
    for ig in INDIGENOUS_MURALS:
        color = tradition_colors.get(ig["tradition"], "#14b8a6")
        popup = _popup_html([
            ("Name", ig["name"]),
            ("City", ig["city"]),
            ("Tradition", ig["tradition"]),
            ("Period", ig["period"]),
            ("Significance", ig["significance"]),
        ])
        folium.CircleMarker(
            location=[ig["lat"], ig["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=popup,
            tooltip=_safe(ig["name"]),
        ).add_to(m)

    # Legend
    legend_html = " &nbsp; ".join(
        f'<span style="color:{c};font-size:0.75rem;">&#9679; {_safe(t)}</span>'
        for t, c in tradition_colors.items()
    )
    st.markdown(legend_html, unsafe_allow_html=True)
    components.html(m._repr_html_(), height=500)

    # ── Detail cards ──
    st.markdown("---")
    st.markdown("##### Sites & Traditions")
    for ig in INDIGENOUS_MURALS:
        color = tradition_colors.get(ig["tradition"], "#14b8a6")
        unesco = ""
        if "UNESCO" in ig["significance"]:
            unesco = ' <span style="color:#f59e0b;font-size:0.7rem;">UNESCO</span>'
        st.markdown(
            f'<div style="border-left:3px solid {color};padding:6px 12px;margin-bottom:8px;">'
            f'<strong style="color:#e8ecf4;">{_safe(ig["name"])}</strong>{unesco}<br/>'
            f'<span style="color:{color};font-size:0.8rem;">{_safe(ig["tradition"])}</span> '
            f'<span style="color:#5a6580;font-size:0.75rem;">| {_safe(ig["city"])} | {_safe(ig["period"])}</span><br/>'
            f'<span style="color:#8b97b0;font-size:0.8rem;">{_safe(ig["description"])}</span><br/>'
            f'<span style="color:#06b6d4;font-size:0.75rem;font-style:italic;">{_safe(ig["significance"])}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Chart ──
    st.markdown("---")
    st.markdown("##### Sites by Tradition")
    _dark_bar_chart(
        labels=list(traditions.keys()),
        values=list(traditions.values()),
        colors=[tradition_colors.get(t, "#14b8a6") for t in traditions.keys()],
        xlabel="Sites",
    )

    # ── Table & download ──
    df = pd.DataFrame(INDIGENOUS_MURALS)
    _show_table_and_download(df, "indigenous mural sites", "indigenous_murals")


def _render_mode_10_light_art():
    """Mode 10: Light Art & Projections."""
    st.markdown("##### Light Art & Projection Mapping")
    st.caption(MODE_DESCRIPTIONS["Light Art & Projections"])

    # ── Stats ──
    permanent_count = sum(1 for la in LIGHT_ART if la["permanent"])
    festival_count = sum(1 for la in LIGHT_ART if not la["permanent"])
    countries = len(set(la["city"].split(", ")[-1] for la in LIGHT_ART))
    oldest = min(LIGHT_ART, key=lambda la: la["year_started"])
    _stats_row([
        ("Sites Mapped", len(LIGHT_ART)),
        ("Permanent", permanent_count),
        ("Festivals", festival_count),
        ("Countries", countries),
        ("Oldest", f"{oldest['name'][:18]} ({oldest['year_started']})"),
    ])

    # ── Filter ──
    perm_filter = st.radio(
        "Show",
        ["All", "Permanent Only", "Festivals Only"],
        horizontal=True,
        key="sa_m10_filter",
    )
    if perm_filter == "Permanent Only":
        filtered = [la for la in LIGHT_ART if la["permanent"]]
    elif perm_filter == "Festivals Only":
        filtered = [la for la in LIGHT_ART if not la["permanent"]]
    else:
        filtered = LIGHT_ART

    # ── Map ──
    st.markdown("---")
    m = _make_dark_map(30.0, 10.0, zoom=2)
    for la in filtered:
        color = "#3b82f6" if la["permanent"] else "#f59e0b"
        popup = _popup_html([
            ("Name", la["name"]),
            ("City", la["city"]),
            ("Type", la["type"]),
            ("Permanent", "Yes" if la["permanent"] else "No (Festival)"),
            ("Since", str(la["year_started"])),
            ("Description", la["description"][:150]),
        ])
        folium.CircleMarker(
            location=[la["lat"], la["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=popup,
            tooltip=_safe(la["name"]),
        ).add_to(m)

    st.markdown(
        '<span style="color:#3b82f6;font-size:0.8rem;">&#9679; Permanent</span> &nbsp; '
        '<span style="color:#f59e0b;font-size:0.8rem;">&#9679; Festival</span>',
        unsafe_allow_html=True,
    )
    components.html(m._repr_html_(), height=500)

    # ── Detail cards ──
    st.markdown("---")
    col_cards, col_chart = st.columns([1, 1])
    with col_cards:
        st.markdown("##### Light Art Profiles")
        for la in filtered:
            color = "#3b82f6" if la["permanent"] else "#f59e0b"
            badge = "PERMANENT" if la["permanent"] else "FESTIVAL"
            st.markdown(
                f'<div style="border-left:3px solid {color};padding:4px 10px;margin-bottom:6px;">'
                f'<strong style="color:#e8ecf4;">{_safe(la["name"])}</strong> '
                f'<span style="color:{color};font-size:0.7rem;">{badge}</span><br/>'
                f'<span style="color:#5a6580;font-size:0.75rem;">{_safe(la["city"])} | Since {la["year_started"]}</span><br/>'
                f'<span style="color:#8b97b0;font-size:0.75rem;">{_safe(la["description"][:120])}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with col_chart:
        st.markdown("##### Light Art Types")
        type_counts = {}
        for la in LIGHT_ART:
            type_counts[la["type"]] = type_counts.get(la["type"], 0) + 1
        _dark_bar_chart(
            labels=list(type_counts.keys()),
            values=list(type_counts.values()),
            colors="#3b82f6",
            xlabel="Count",
        )

    # ── Table & download ──
    df = pd.DataFrame(filtered)
    _show_table_and_download(df, "light art sites", "light_art")


# ══════════════════════════════════════════════════════════════════════════════
# MODE DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════

_MODE_RENDERERS = {
    "World Street Art Capitals": _render_mode_1_street_art_capitals,
    "Banksy Locations": _render_mode_2_banksy,
    "Mural Districts": _render_mode_3_mural_districts,
    "Political Murals": _render_mode_4_political_murals,
    "3D Street Art & Illusions": _render_mode_5_3d_art,
    "Graffiti History": _render_mode_6_graffiti_history,
    "Street Art Museums": _render_mode_7_museums,
    "Sculpture & Installation Art": _render_mode_8_sculpture,
    "Indigenous & Traditional Murals": _render_mode_9_indigenous,
    "Light Art & Projections": _render_mode_10_light_art,
}


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def render_street_art_maps_tab():
    """Main render function for the Street Art & Murals Explorer tab."""

    # ── Tab header ──
    st.markdown(
        '<div class="tab-header pink">'
        '<h4>Street Art &amp; Murals Explorer</h4>'
        '<p>Discover street art, murals, graffiti, and urban art installations '
        'worldwide. Explore curated collections and live OpenStreetMap data '
        'across 10 thematic map modes.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode selector ──
    selected_mode = st.selectbox(
        "Map Mode",
        MODE_LABELS,
        key="sa_mode_select",
        help="Choose one of 10 street art exploration modes",
    )

    # ── Mode description ──
    mode_color = MODE_COLORS.get(selected_mode, "#ec4899")
    st.markdown(
        f'<div style="border-left:3px solid {mode_color};padding:6px 12px;margin-bottom:12px;">'
        f'<span style="color:#e8ecf4;font-size:0.85rem;">'
        f'{_safe(MODE_DESCRIPTIONS.get(selected_mode, ""))}'
        f'</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Dispatch to mode renderer ──
    renderer = _MODE_RENDERERS.get(selected_mode)
    if renderer:
        renderer()
    else:
        st.error(f"Unknown mode: {selected_mode}")
