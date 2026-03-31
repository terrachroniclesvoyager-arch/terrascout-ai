# -*- coding: utf-8 -*-
"""
Paranormal & UFO Maps module for TerraScout AI.
Hardcoded datasets of paranormal phenomena locations worldwide:
UFO sightings, haunted places, anomaly zones, crop circles, ley lines,
ghost ships, secret bases, ancient astronaut sites, strange events, and portals.
All data is embedded - no API key needed.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster, HeatMap
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ═══════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
ACCENT_COLOR = "#06b6d4"
MUTED_COLOR = "#5a6580"

# ═══════════════════════════════════════════════════════════════════
# MODE COLORS
# ═══════════════════════════════════════════════════════════════════
MODE_COLORS = {
    "UFO Sighting Hotspots": "#39ff14",
    "Haunted Places": "#8b5cf6",
    "Bermuda Triangle & Anomalies": "#ef4444",
    "Crop Circle Locations": "#f59e0b",
    "Ley Lines & Energy Vortices": "#ec4899",
    "Ghost Ship Sightings": "#38bdf8",
    "Secret Bases & Underground Facilities": "#dc2626",
    "Ancient Astronaut Sites": "#f97316",
    "Spontaneous Combustion & Strange Events": "#ff6b6b",
    "Portals & Dimensional Anomalies": "#a855f7",
}

# ═══════════════════════════════════════════════════════════════════
# DATA: UFO SIGHTING HOTSPOTS (~50 locations)
# ═══════════════════════════════════════════════════════════════════
UFO_SIGHTINGS = [
    {"name": "Roswell, New Mexico", "lat": 33.3943, "lon": -104.5230, "year": 1947, "type": "Crash/Recovery", "description": "Alleged UFO crash and debris recovery by US military"},
    {"name": "Area 51, Nevada", "lat": 37.2350, "lon": -115.8111, "year": 1955, "type": "Ongoing Activity", "description": "Classified USAF facility with persistent UFO reports"},
    {"name": "Rendlesham Forest, UK", "lat": 52.0833, "lon": 1.4333, "year": 1980, "type": "Landing/Encounter", "description": "Binary code encounter by USAF personnel near RAF Woodbridge"},
    {"name": "Phoenix, Arizona", "lat": 33.4484, "lon": -112.0740, "year": 1997, "type": "Mass Sighting", "description": "Phoenix Lights - V-shaped formation seen by thousands"},
    {"name": "Stephenville, Texas", "lat": 32.2207, "lon": -98.2023, "year": 2008, "type": "Mass Sighting", "description": "Multiple witnesses saw huge silent craft near Crawford Ranch"},
    {"name": "Gulf Breeze, Florida", "lat": 30.3574, "lon": -87.1639, "year": 1987, "type": "Repeated Sightings", "description": "Ed Walters photographic series of structured craft"},
    {"name": "Shag Harbour, Nova Scotia", "lat": 43.4605, "lon": -65.7233, "year": 1967, "type": "Crash/Water Entry", "description": "Official Canadian government documented USO incident"},
    {"name": "Kecksburg, Pennsylvania", "lat": 40.1848, "lon": -79.4612, "year": 1965, "type": "Crash/Recovery", "description": "Acorn-shaped object recovered by military from woods"},
    {"name": "Lubbock, Texas", "lat": 33.5779, "lon": -101.8552, "year": 1951, "type": "Mass Sighting", "description": "Lubbock Lights - V-formation of lights photographed by students"},
    {"name": "Washington D.C.", "lat": 38.9072, "lon": -77.0369, "year": 1952, "type": "Radar/Visual", "description": "UFOs over the Capitol - tracked on radar, jets scrambled"},
    {"name": "McMinnville, Oregon", "lat": 45.2101, "lon": -123.1987, "year": 1950, "type": "Photographic", "description": "Trent farm photos - among most analyzed UFO photographs"},
    {"name": "Colares, Brazil", "lat": -0.9367, "lon": -48.5161, "year": 1977, "type": "Mass Sighting/Injury", "description": "Operation Saucer - Brazilian Air Force investigated light beams"},
    {"name": "Varginha, Brazil", "lat": -21.5510, "lon": -45.4333, "year": 1996, "type": "Entity Encounter", "description": "Multiple witnesses reported alien being captured by military"},
    {"name": "Tehran, Iran", "lat": 35.6892, "lon": 51.3890, "year": 1976, "type": "Military Encounter", "description": "Iranian F-4 jets lost instruments chasing brilliant UFO"},
    {"name": "Belgium Wave", "lat": 50.8503, "lon": 4.3517, "year": 1989, "type": "Mass Sighting", "description": "Triangular craft wave documented by Belgian Air Force"},
    {"name": "Westall, Melbourne", "lat": -37.9251, "lon": 145.1046, "year": 1966, "type": "School Sighting", "description": "200+ students and teachers witnessed disc landing near school"},
    {"name": "Falcon Lake, Manitoba", "lat": 49.6956, "lon": -95.2584, "year": 1967, "type": "Close Encounter", "description": "Stefan Michalak burned by disc-shaped craft exhaust"},
    {"name": "Hessdalen Valley, Norway", "lat": 62.8100, "lon": 11.2000, "year": 1981, "type": "Recurring Lights", "description": "Unexplained lights studied by Project Hessdalen since 1984"},
    {"name": "Bonnybridge, Scotland", "lat": 56.0000, "lon": -3.8833, "year": 1992, "type": "Hotspot", "description": "Falkirk Triangle - 300+ annual sightings reported"},
    {"name": "Wycliffe Well, Australia", "lat": -20.7967, "lon": 134.1781, "year": 1960, "type": "Ongoing Hotspot", "description": "Self-proclaimed UFO capital of Australia"},
    {"name": "San Clemente, Chile", "lat": -35.5450, "lon": -71.4906, "year": 2008, "type": "Official UFO Trail", "description": "Government-designated UFO trail in Andes foothills"},
    {"name": "Broad Haven, Wales", "lat": 51.7673, "lon": -5.1871, "year": 1977, "type": "School Sighting", "description": "Broad Haven Triangle - school children drew identical craft"},
    {"name": "Canneto di Caronia, Sicily", "lat": 38.0167, "lon": 14.4500, "year": 2004, "type": "Anomalous Fires", "description": "Spontaneous fires and electrical anomalies linked to UFOs"},
    {"name": "Kapustin Yar, Russia", "lat": 48.5700, "lon": 45.7500, "year": 1948, "type": "Military Base", "description": "Russia's Roswell - rocket base with persistent UFO reports"},
    {"name": "Woomera, Australia", "lat": -31.1600, "lon": 136.8300, "year": 1950, "type": "Military/Test Range", "description": "Weapons testing range with numerous UFO sightings over decades"},
    {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332, "year": 1991, "type": "Mass Sighting", "description": "Eclipse UFO - thousands filmed silver disc during solar eclipse"},
    {"name": "Malmstrom AFB, Montana", "lat": 47.5052, "lon": -111.1830, "year": 1967, "type": "Nuclear/Military", "description": "UFO disabled 10 Minuteman nuclear missiles simultaneously"},
    {"name": "Levelland, Texas", "lat": 33.5873, "lon": -102.3780, "year": 1957, "type": "EM Effects", "description": "Egg-shaped craft caused vehicle electrical failures across town"},
    {"name": "Lakenheath-Bentwaters, UK", "lat": 52.4090, "lon": 0.5610, "year": 1956, "type": "Radar/Visual", "description": "Combined RAF/USAF radar tracking and visual confirmation"},
    {"name": "Cash-Landrum, Texas", "lat": 30.0750, "lon": -95.0200, "year": 1980, "type": "Close Encounter", "description": "Diamond-shaped craft caused radiation burns to three witnesses"},
    {"name": "Petrozavodsk, Russia", "lat": 61.7849, "lon": 34.3469, "year": 1977, "type": "Mass Sighting", "description": "Jellyfish-shaped luminous object over the city at dawn"},
    {"name": "Ariel School, Zimbabwe", "lat": -17.7900, "lon": 31.0500, "year": 1994, "type": "School Encounter", "description": "62 school children reported beings near landed craft"},
    {"name": "O'Hare Airport, Chicago", "lat": 41.9742, "lon": -87.9073, "year": 2006, "type": "Airport Sighting", "description": "Metallic disc hovered over Gate C17, punched hole in clouds"},
    {"name": "Tic Tac / USS Nimitz", "lat": 31.0000, "lon": -118.0000, "year": 2004, "type": "Military/Navy", "description": "Navy pilots recorded oblong UAP exhibiting impossible maneuvers"},
    {"name": "Gimbal / USS Theodore Roosevelt", "lat": 36.0000, "lon": -75.0000, "year": 2015, "type": "Military/Navy", "description": "Rotating UAP recorded by Navy fighter jet FLIR system"},
    {"name": "Aguadilla, Puerto Rico", "lat": 18.4938, "lon": -67.1300, "year": 2013, "type": "Transmedium", "description": "DHS thermal video of object entering and exiting ocean"},
    {"name": "Ruwa, Zimbabwe", "lat": -17.8500, "lon": 31.2333, "year": 1994, "type": "Entity Encounter", "description": "Ariel School contact case investigated by John Mack"},
    {"name": "Ely, Nevada", "lat": 39.2533, "lon": -114.8747, "year": 1952, "type": "Pilot Sighting", "description": "Multiple discs paced military transport aircraft"},
    {"name": "Ravenna, Ohio", "lat": 41.1576, "lon": -81.2421, "year": 1966, "type": "Police Chase", "description": "Portage County police chased glowing disc across state lines"},
    {"name": "Mariana, Montana", "lat": 47.5053, "lon": -111.2813, "year": 1950, "type": "Photographic", "description": "Nick Mariana filmed two bright objects over Great Falls"},
    {"name": "Crestview, Florida", "lat": 30.7541, "lon": -86.5706, "year": 1973, "type": "Multiple Witnesses", "description": "Triangular craft hovered over highway, multiple vehicle stops"},
    {"name": "Valensole, France", "lat": 43.8372, "lon": 5.9831, "year": 1965, "type": "Landing/Entity", "description": "Farmer encountered oval craft and small beings in lavender field"},
    {"name": "Voronezh, Russia", "lat": 51.6615, "lon": 39.2003, "year": 1989, "type": "Entity Encounter", "description": "Large beings and craft witnessed in park by many residents"},
    {"name": "Nuremberg, Germany", "lat": 49.4521, "lon": 11.0767, "year": 1561, "type": "Historical", "description": "1561 celestial event depicted in famous woodcut print"},
    {"name": "Basel, Switzerland", "lat": 47.5596, "lon": 7.5886, "year": 1566, "type": "Historical", "description": "Black spheres appeared in sky, documented in gazette"},
    {"name": "Aurora, Texas", "lat": 33.0607, "lon": -97.5103, "year": 1897, "type": "Crash/Historical", "description": "Airship allegedly crashed into windmill, pilot buried locally"},
    {"name": "Kaikoura, New Zealand", "lat": -42.4008, "lon": 173.6815, "year": 1978, "type": "Radar/Visual", "description": "Film crew captured lights confirmed on Wellington radar"},
    {"name": "São Paulo, Brazil", "lat": -23.5505, "lon": -46.6333, "year": 1986, "type": "Military Scramble", "description": "Brazilian Air Force scrambled jets after 20+ radar returns"},
    {"name": "Bonsall, UK", "lat": 53.0970, "lon": -1.5430, "year": 2000, "type": "Photographic", "description": "Disc photographed over Derbyshire village, widely analyzed"},
]

# ═══════════════════════════════════════════════════════════════════
# DATA: HAUNTED PLACES (~40 locations)
# ═══════════════════════════════════════════════════════════════════
HAUNTED_PLACES = [
    {"name": "Tower of London", "lat": 51.5081, "lon": -0.0759, "country": "UK", "type": "Castle/Prison", "ghost": "Anne Boleyn, Princes in the Tower", "description": "Headless queen and imprisoned princes haunt the ancient fortress"},
    {"name": "Eastern State Penitentiary", "lat": 39.9683, "lon": -75.1727, "country": "USA", "type": "Prison", "ghost": "Al Capone, cellblock spirits", "description": "Crumbling cellblocks echo with whispers and shadow figures"},
    {"name": "Poveglia Island", "lat": 45.3830, "lon": 12.3330, "country": "Italy", "type": "Island/Asylum", "ghost": "Plague victims, mad doctor", "description": "Island of death - plague dumping ground turned insane asylum"},
    {"name": "Aokigahara Forest", "lat": 35.4734, "lon": 138.6223, "country": "Japan", "type": "Forest", "ghost": "Yurei (restless spirits)", "description": "Sea of Trees at Mt Fuji base - compass anomalies and apparitions"},
    {"name": "Château de Brissac", "lat": 47.3536, "lon": -0.4506, "country": "France", "type": "Castle", "ghost": "La Dame Verte (Green Lady)", "description": "Murdered double-dealing wife roams as moaning green apparition"},
    {"name": "Monte Cristo Homestead", "lat": -34.7522, "lon": 148.7158, "country": "Australia", "type": "Mansion", "ghost": "Mrs. Crawley, various spirits", "description": "Australia's most haunted house - multiple tragic deaths on site"},
    {"name": "Edinburgh Castle", "lat": 55.9486, "lon": -3.1999, "country": "UK", "type": "Castle", "ghost": "Headless drummer, prisoners", "description": "Ancient fortress where a headless drummer warns of attacks"},
    {"name": "Bhangarh Fort", "lat": 27.0972, "lon": 76.2844, "country": "India", "type": "Fort/Ruins", "ghost": "Cursed princess and sorcerer", "description": "Government-declared haunted - entry banned after sunset"},
    {"name": "Gettysburg Battlefield", "lat": 39.8110, "lon": -77.2291, "country": "USA", "type": "Battlefield", "ghost": "Civil War soldiers", "description": "Phantom soldiers march and gunfire echoes across the fields"},
    {"name": "The Stanley Hotel", "lat": 40.3828, "lon": -105.5194, "country": "USA", "type": "Hotel", "ghost": "F.O. Stanley, Mrs. Wilson", "description": "Inspired The Shining - piano plays itself in the ballroom"},
    {"name": "Leap Castle", "lat": 52.9667, "lon": -7.8500, "country": "Ireland", "type": "Castle", "ghost": "Elemental being, Red Lady", "description": "Bloody Chapel and oubliette filled with skeletons"},
    {"name": "Borgvattnet Vicarage", "lat": 63.3000, "lon": 16.3833, "country": "Sweden", "type": "Vicarage", "ghost": "Grey ladies, screaming women", "description": "Haunted since 1927 - every vicar reported supernatural events"},
    {"name": "Myrtles Plantation", "lat": 30.5274, "lon": -91.3793, "country": "USA", "type": "Plantation", "ghost": "Chloe, murdered slave", "description": "Mirror captures ghostly figures and handprints appear on glass"},
    {"name": "Highgate Cemetery", "lat": 51.5676, "lon": -0.1473, "country": "UK", "type": "Cemetery", "ghost": "Highgate Vampire", "description": "Victorian cemetery where a vampire was allegedly spotted in 1970"},
    {"name": "Changi Hospital", "lat": 1.3839, "lon": 103.9800, "country": "Singapore", "type": "Hospital", "ghost": "WWII prisoners, patients", "description": "Abandoned WWII hospital with screams and ghostly apparitions"},
    {"name": "Island of the Dolls", "lat": 19.2828, "lon": -99.0931, "country": "Mexico", "type": "Island", "ghost": "Drowned girl", "description": "Thousands of decaying dolls hung by hermit to appease spirit"},
    {"name": "Ancient Ram Inn", "lat": 51.6845, "lon": -2.2087, "country": "UK", "type": "Inn", "ghost": "Incubus, child sacrifices", "description": "Built on pagan burial ground - demonic activity reported"},
    {"name": "Lawang Sewu", "lat": -6.9847, "lon": 110.4100, "country": "Indonesia", "type": "Colonial Building", "ghost": "Dutch soldiers, kuntilanak", "description": "Thousand Doors building - WWII execution site with headless ghosts"},
    {"name": "Waverly Hills Sanatorium", "lat": 38.1577, "lon": -85.8033, "country": "USA", "type": "Sanatorium", "ghost": "TB patients, shadow people", "description": "Body chute and death tunnel - 6,000+ tuberculosis deaths"},
    {"name": "Raynham Hall", "lat": 52.8003, "lon": 0.8045, "country": "UK", "type": "Manor", "ghost": "Brown Lady", "description": "Famous 1936 photograph of ghostly woman on staircase"},
    {"name": "Hoia Baciu Forest", "lat": 46.7700, "lon": 23.5400, "country": "Romania", "type": "Forest", "ghost": "UFOs, missing persons", "description": "World's most haunted forest - twisted trees and time loss"},
    {"name": "Chateau de Chateaubriant", "lat": 47.7186, "lon": -1.3759, "country": "France", "type": "Castle", "ghost": "Françoise de Foix", "description": "Murdered mistress of Francis I appears on October anniversaries"},
    {"name": "Catacombs of Paris", "lat": 48.8339, "lon": 2.3323, "country": "France", "type": "Catacombs", "ghost": "Philibert Aspairt, shadows", "description": "Miles of tunnels with 6 million bones and unexplained voices"},
    {"name": "Berry Pomeroy Castle", "lat": 50.4636, "lon": -3.6347, "country": "UK", "type": "Castle Ruins", "ghost": "White Lady, Blue Lady", "description": "Two spectral ladies - one lures, one wails in the dungeons"},
    {"name": "Banff Springs Hotel", "lat": 51.1674, "lon": -115.5642, "country": "Canada", "type": "Hotel", "ghost": "Bride, Sam the bellman", "description": "Ghost bride on staircase and helpful phantom bellman"},
    {"name": "Port Arthur", "lat": -43.1455, "lon": 147.8535, "country": "Australia", "type": "Prison Colony", "ghost": "Convict ghosts", "description": "Brutal penal colony - ghost tours document persistent activity"},
    {"name": "Forbidden City", "lat": 39.9163, "lon": 116.3972, "country": "China", "type": "Palace", "ghost": "Weeping concubines", "description": "Night guards report crying women and phantom processions"},
    {"name": "Rose Hall, Jamaica", "lat": 18.5117, "lon": -77.8653, "country": "Jamaica", "type": "Great House", "ghost": "Annie Palmer, White Witch", "description": "Voodoo-practicing mistress murdered three husbands"},
    {"name": "Akershus Fortress", "lat": 59.9075, "lon": 10.7361, "country": "Norway", "type": "Fortress", "ghost": "Malcanisen (demon dog)", "description": "Medieval fortress guarded by a hellhound phantom"},
    {"name": "Winchester Mystery House", "lat": 37.3184, "lon": -121.9511, "country": "USA", "type": "Mansion", "ghost": "Gun victims' spirits", "description": "160-room labyrinth built non-stop to appease rifle ghosts"},
    {"name": "Pluckley Village", "lat": 51.1726, "lon": 0.7475, "country": "UK", "type": "Village", "ghost": "12+ different ghosts", "description": "England's most haunted village - screaming man, red lady, colonel"},
    {"name": "Dragsholm Castle", "lat": 55.7453, "lon": 11.4900, "country": "Denmark", "type": "Castle", "ghost": "Grey Lady, White Lady, Earl", "description": "Three resident ghosts including a walled-up maiden"},
    {"name": "Houska Castle", "lat": 50.4900, "lon": 14.6300, "country": "Czech Republic", "type": "Castle", "ghost": "Demons from pit", "description": "Built over a gateway to Hell - no water, kitchen, or fortifications"},
    {"name": "Corvin Castle", "lat": 45.7489, "lon": 22.8875, "country": "Romania", "type": "Castle", "ghost": "Prisoners, Vlad Dracula", "description": "Vlad the Impaler was imprisoned here - moans from the dungeon"},
    {"name": "St. Augustine Lighthouse", "lat": 29.8855, "lon": -81.2886, "country": "USA", "type": "Lighthouse", "ghost": "Two drowned girls", "description": "Two girls who drowned during construction haunt the tower"},
    {"name": "Villisca Axe Murder House", "lat": 40.9295, "lon": -94.9730, "country": "USA", "type": "House", "ghost": "Moore family, children", "description": "Eight people axe-murdered in 1912 - voices and moving objects"},
    {"name": "Padre Pio Shrine", "lat": 41.7075, "lon": 15.9942, "country": "Italy", "type": "Shrine", "ghost": "Stigmata saint, lights", "description": "Pilgrims report healing lights and the saint's rose scent"},
    {"name": "Larnach Castle", "lat": -45.8537, "lon": 170.6267, "country": "New Zealand", "type": "Castle", "ghost": "Kate Larnach", "description": "Tragic wife's ghost languishes in the ballroom at night"},
    {"name": "Beechworth Lunatic Asylum", "lat": -36.3579, "lon": 146.6850, "country": "Australia", "type": "Asylum", "ghost": "Patients, Matron Sharpe", "description": "3,000 patients died here - shadow figures and cold spots"},
    {"name": "Hell Fire Club, Dublin", "lat": 53.2500, "lon": -6.3333, "country": "Ireland", "type": "Ruin", "ghost": "Demons, devil worshippers", "description": "Hilltop ruin where 18th century elite held black mass rituals"},
]

# ═══════════════════════════════════════════════════════════════════
# DATA: BERMUDA TRIANGLE & ANOMALY ZONES (~15)
# ═══════════════════════════════════════════════════════════════════
ANOMALY_ZONES = [
    {"name": "Bermuda Triangle", "lat": 25.0000, "lon": -71.0000, "radius_km": 1300, "type": "Maritime/Aviation", "incidents": 75, "description": "Devil's Triangle - hundreds of ships and planes vanished since 1945"},
    {"name": "Dragon's Triangle (Devil's Sea)", "lat": 29.0000, "lon": 140.0000, "radius_km": 1100, "type": "Maritime", "incidents": 40, "description": "Japan's Bermuda Triangle - ships vanish south of Tokyo"},
    {"name": "Michigan Triangle", "lat": 43.5000, "lon": -87.0000, "radius_km": 300, "type": "Maritime/Aviation", "incidents": 15, "description": "Lake Michigan anomaly zone - Flight 2501 and many ships lost"},
    {"name": "Sargasso Sea", "lat": 28.0000, "lon": -66.0000, "radius_km": 900, "type": "Maritime", "incidents": 30, "description": "Seaweed sea of no wind - ancient ships trapped, modern ones vanish"},
    {"name": "South Atlantic Anomaly", "lat": -25.0000, "lon": -50.0000, "radius_km": 2000, "type": "Magnetic/Space", "incidents": 20, "description": "Van Allen belt dip causes satellite malfunctions and radiation surges"},
    {"name": "Mapimí Silent Zone", "lat": 26.6900, "lon": -103.7400, "radius_km": 50, "type": "Electromagnetic", "incidents": 12, "description": "Mexican desert zone where radio signals allegedly cannot penetrate"},
    {"name": "Bass Strait Triangle", "lat": -39.5000, "lon": 145.5000, "radius_km": 250, "type": "Aviation", "incidents": 10, "description": "Frederick Valentich disappearance 1978 - plane and pilot never found"},
    {"name": "Bridgewater Triangle", "lat": 41.9000, "lon": -71.0800, "radius_km": 60, "type": "Multi-Phenomena", "incidents": 50, "description": "Bigfoot, UFOs, cattle mutilation, giant birds all reported here"},
    {"name": "Bennington Triangle", "lat": 43.0200, "lon": -73.0400, "radius_km": 40, "type": "Disappearances", "incidents": 8, "description": "Five people vanished without trace between 1945 and 1950"},
    {"name": "Alaska Triangle", "lat": 63.5000, "lon": -152.0000, "radius_km": 1500, "type": "Disappearances", "incidents": 60, "description": "Over 20,000 people have gone missing in this wilderness zone"},
    {"name": "Superstition Mountains", "lat": 33.4500, "lon": -111.1700, "radius_km": 30, "type": "Disappearances", "incidents": 15, "description": "Lost Dutchman's Gold Mine - searchers vanish, decapitated remains found"},
    {"name": "Vile Vortex - Algeria", "lat": 26.5700, "lon": 0.0000, "radius_km": 200, "type": "Vile Vortex", "incidents": 5, "description": "Ivan Sanderson's vile vortex point in the Sahara Desert"},
    {"name": "Vile Vortex - Afghanistan", "lat": 36.0000, "lon": 72.0000, "radius_km": 200, "type": "Vile Vortex", "incidents": 5, "description": "Mountain vortex point near Hindu Kush with anomalous compass readings"},
    {"name": "Wharton Basin Vortex", "lat": -25.0000, "lon": 100.0000, "radius_km": 500, "type": "Vile Vortex", "incidents": 8, "description": "Indian Ocean vortex - MH370 search area with magnetic anomalies"},
    {"name": "Point Nemo", "lat": -48.8767, "lon": -123.3933, "radius_km": 400, "type": "Oceanic Anomaly", "incidents": 3, "description": "Most remote ocean point - Bloop sound detected nearby in 1997"},
]

# ═══════════════════════════════════════════════════════════════════
# DATA: CROP CIRCLE LOCATIONS (~30)
# ═══════════════════════════════════════════════════════════════════
CROP_CIRCLES = [
    {"name": "Avebury, Wiltshire", "lat": 51.4286, "lon": -1.8544, "year": 1996, "pattern": "Julia Set", "description": "200ft fractal appeared in 45 minutes near stone circle"},
    {"name": "Barbury Castle, Wiltshire", "lat": 51.4847, "lon": -1.7800, "year": 1991, "pattern": "Triangle/Tetrahedron", "description": "Sacred geometry formation encoding mathematical constants"},
    {"name": "Chilbolton, Hampshire", "lat": 51.1450, "lon": -1.4372, "year": 2001, "pattern": "Face & Arecibo Reply", "description": "Response to 1974 Arecibo message appeared near radio telescope"},
    {"name": "Silbury Hill, Wiltshire", "lat": 51.4156, "lon": -1.8575, "year": 2009, "pattern": "Mayan Calendar", "description": "Complex Mayan-themed formation near Europe's largest man-made mound"},
    {"name": "Milk Hill, Wiltshire", "lat": 51.3572, "lon": -1.8500, "year": 2001, "pattern": "409-Circle Galaxy", "description": "Largest formation ever - 409 circles spanning 238m"},
    {"name": "Stonehenge, Wiltshire", "lat": 51.1789, "lon": -1.8262, "year": 1996, "pattern": "Julia Set Fractal", "description": "151-circle fractal appeared in broad daylight near monuments"},
    {"name": "Cley Hill, Wiltshire", "lat": 51.2106, "lon": -2.2250, "year": 2010, "pattern": "3D Cube", "description": "Impossible three-dimensional cube design in wheat field"},
    {"name": "West Kennett, Wiltshire", "lat": 51.4075, "lon": -1.8525, "year": 2011, "pattern": "Serpent", "description": "Undulating serpent formation near ancient long barrow"},
    {"name": "Windmill Hill, Wiltshire", "lat": 51.4400, "lon": -1.8781, "year": 1999, "pattern": "Magnetic Field Lines", "description": "Formation resembling Earth's magnetic field dipole"},
    {"name": "Hackpen Hill, Wiltshire", "lat": 51.4711, "lon": -1.7983, "year": 1999, "pattern": "Menorah", "description": "Sacred symbol pattern with seven branches in wheat"},
    {"name": "Alton Barnes, Wiltshire", "lat": 51.3564, "lon": -1.8639, "year": 1990, "pattern": "Pictogram", "description": "First major pictogram formation that sparked worldwide interest"},
    {"name": "Tully, Queensland", "lat": -17.9333, "lon": 145.9167, "year": 1966, "pattern": "Saucer Nest", "description": "Flattened reeds in lagoon after UFO sighting - first modern circle"},
    {"name": "Oliver's Castle, Wiltshire", "lat": 51.3217, "lon": -2.1217, "year": 1996, "pattern": "Snowflake", "description": "Controversial video allegedly showed lights creating formation"},
    {"name": "Crabwood, Hampshire", "lat": 51.0750, "lon": -1.3833, "year": 2002, "pattern": "Alien Face + Binary", "description": "Alien face with binary disc reading 'beware the bearers of false gifts'"},
    {"name": "Waylands Smithy, Oxfordshire", "lat": 51.5669, "lon": -1.5956, "year": 2006, "pattern": "Butterfly", "description": "Ornate butterfly formation near Neolithic burial chamber"},
    {"name": "Yatesbury, Wiltshire", "lat": 51.4350, "lon": -1.8914, "year": 2007, "pattern": "Magnetic Vortex", "description": "Spiral vortex pattern with stunning geometric precision"},
    {"name": "Saarbrücken, Germany", "lat": 49.2354, "lon": 6.9903, "year": 2014, "pattern": "Complex Mandala", "description": "One of the rare elaborate formations outside the UK"},
    {"name": "Robella, Piedmont, Italy", "lat": 45.1000, "lon": 8.1000, "year": 2013, "pattern": "Flower of Life", "description": "Sacred geometry pattern in Italian rice paddy field"},
    {"name": "Goes, Netherlands", "lat": 51.5042, "lon": 3.8892, "year": 2009, "pattern": "Butterfly Wings", "description": "Large butterfly design in Dutch farmland"},
    {"name": "Diessenhofen, Switzerland", "lat": 47.6900, "lon": 8.7500, "year": 2008, "pattern": "Star Mandala", "description": "Eight-pointed star formation appeared overnight near Rhine"},
    {"name": "Grasdorf, Germany", "lat": 52.1000, "lon": 9.7667, "year": 1991, "pattern": "Triple Formation", "description": "Three metal plates found buried beneath the formation"},
    {"name": "Ipuaçu, Brazil", "lat": -26.6375, "lon": -52.4553, "year": 2008, "pattern": "Sunflower Spiral", "description": "Fibonacci spiral in Brazilian soybean field"},
    {"name": "Conondale, Queensland", "lat": -26.7333, "lon": 152.6833, "year": 2006, "pattern": "Rings", "description": "Multiple ring formations in sugarcane near Glass House Mountains"},
    {"name": "Hoeven, Netherlands", "lat": 51.5889, "lon": 4.5694, "year": 2013, "pattern": "Complex Weave", "description": "Intricate woven pattern defying simple flattening techniques"},
    {"name": "Prudentópolis, Brazil", "lat": -25.2128, "lon": -50.9783, "year": 2012, "pattern": "Ring System", "description": "Concentric ring formation in Brazilian wheat field"},
    {"name": "Badbury Rings, Dorset", "lat": 50.8175, "lon": -2.0028, "year": 2014, "pattern": "Celtic Knot", "description": "Intricate knotwork formation near Iron Age hill fort"},
    {"name": "Etchilhampton, Wiltshire", "lat": 51.3311, "lon": -1.9333, "year": 2011, "pattern": "Cube Matrix", "description": "Three-dimensional matrix of cubes bending in perspective"},
    {"name": "Cherhill, Wiltshire", "lat": 51.4228, "lon": -1.9406, "year": 1999, "pattern": "Nine-pointed Star", "description": "Star within circles near the Cherhill White Horse"},
    {"name": "Stanton St Bernard", "lat": 51.3700, "lon": -1.8511, "year": 2012, "pattern": "DNA Helix", "description": "Double helix pattern representing DNA molecular structure"},
    {"name": "Ansty, Wiltshire", "lat": 51.0397, "lon": -2.0644, "year": 2016, "pattern": "Goddess Symbol", "description": "Triple Moon Goddess symbol with extraordinary precision"},
]

# ═══════════════════════════════════════════════════════════════════
# DATA: LEY LINES & ENERGY VORTICES (~30 nodes)
# ═══════════════════════════════════════════════════════════════════
LEY_LINES = [
    {"name": "Sedona Vortex - Airport Mesa", "lat": 34.8523, "lon": -111.7890, "type": "Energy Vortex", "energy": "Electromagnetic", "description": "Most accessible Sedona vortex - twisted juniper trees mark the spot"},
    {"name": "Sedona Vortex - Bell Rock", "lat": 34.8050, "lon": -111.7696, "type": "Energy Vortex", "energy": "Masculine/Electric", "description": "Bell-shaped butte radiating upward spiral energy"},
    {"name": "Sedona Vortex - Cathedral Rock", "lat": 34.8219, "lon": -111.7899, "type": "Energy Vortex", "energy": "Feminine/Magnetic", "description": "Red rock spires channeling powerful inward-flowing energy"},
    {"name": "Glastonbury Tor", "lat": 51.1442, "lon": -2.6986, "type": "Ley Node", "energy": "Michael Line", "description": "Intersection of St. Michael and Mary ley lines atop sacred hill"},
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "type": "Ley Node", "energy": "Solar Alignment", "description": "Major ley junction aligned to solstice sunrise and lunar cycles"},
    {"name": "Avebury Stone Circle", "lat": 51.4286, "lon": -1.8544, "type": "Ley Node", "energy": "Telluric", "description": "Largest stone circle in world sits on ley line intersection"},
    {"name": "Great Pyramid of Giza", "lat": 29.9792, "lon": 31.1342, "type": "Ley Node", "energy": "Piezoelectric", "description": "Center of Earth's landmass and major ley line hub"},
    {"name": "Nazca Lines", "lat": -14.7350, "lon": -75.1300, "type": "Ley Node", "energy": "Telluric", "description": "Desert geoglyphs aligned to astronomical and ley patterns"},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "type": "Energy Vortex", "energy": "Magnetic", "description": "Inca citadel built on convergence of multiple energy lines"},
    {"name": "Mount Shasta", "lat": 41.4092, "lon": -122.1949, "type": "Energy Vortex", "energy": "Root Chakra", "description": "Earth chakra point - home of Lemurian legends and light orbs"},
    {"name": "Easter Island (Rapa Nui)", "lat": -27.1127, "lon": -109.3497, "type": "Ley Node", "energy": "Pacific Grid", "description": "Moai statues placed along planetary energy grid lines"},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "type": "Ley Node", "energy": "Celestial Alignment", "description": "Temple complex mirrors Draco constellation on ley line"},
    {"name": "Newgrange", "lat": 53.6947, "lon": -6.4756, "type": "Ley Node", "energy": "Solar", "description": "5,000-year-old passage tomb aligned to winter solstice sunrise"},
    {"name": "Uluru (Ayers Rock)", "lat": -25.3444, "lon": 131.0369, "type": "Energy Vortex", "energy": "Solar Plexus Chakra", "description": "Sacred Aboriginal site radiating powerful Earth energy"},
    {"name": "Mount Kailash", "lat": 31.0672, "lon": 81.3119, "type": "Energy Vortex", "energy": "Crown Chakra", "description": "Sacred to four religions - alleged energy axis of the world"},
    {"name": "Chartres Cathedral", "lat": 48.4477, "lon": 1.4878, "type": "Ley Node", "energy": "Sacred Geometry", "description": "Gothic cathedral labyrinth built on druids' sacred well"},
    {"name": "Carnac Stones, Brittany", "lat": 47.5950, "lon": -3.0700, "type": "Ley Node", "energy": "Telluric", "description": "3,000+ standing stones aligned along magnetic ley paths"},
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8439, "type": "Ley Node", "energy": "Cosmic Alignment", "description": "Avenue of the Dead aligned to Orion with mica energy channels"},
    {"name": "Lake Titicaca, Bolivia", "lat": -15.8000, "lon": -69.3333, "type": "Energy Vortex", "energy": "Feminine/Sacral", "description": "Feminine Earth chakra point - gateway energy center"},
    {"name": "Externsteine, Germany", "lat": 51.8686, "lon": 8.9161, "type": "Ley Node", "energy": "Germanic", "description": "Natural rock pillars on ley line - Germanic sacred site"},
    {"name": "Delphi, Greece", "lat": 38.4824, "lon": 22.5012, "type": "Energy Vortex", "energy": "Oracle/Ethylene", "description": "Navel of the world - Oracle drew power from tectonic venting"},
    {"name": "Göbekli Tepe", "lat": 37.2231, "lon": 38.9225, "type": "Ley Node", "energy": "Ancient Grid", "description": "World's oldest temple (11,600 BP) on planetary energy grid"},
    {"name": "Haleakala Crater, Hawaii", "lat": 20.7097, "lon": -156.2533, "type": "Energy Vortex", "energy": "Volcanic/Magnetic", "description": "Hawaiian sacred site where Earth energy rises through volcano"},
    {"name": "Bosnian Pyramid of the Sun", "lat": 43.9769, "lon": 18.1761, "type": "Energy Vortex", "energy": "Ultrasonic Beam", "description": "Controversial pyramid hill with claimed energy beam emission"},
    {"name": "Rennes-le-Château", "lat": 42.9265, "lon": 2.2619, "type": "Ley Node", "energy": "Templar/Rose Line", "description": "Templar mysteries and alleged Rose Line meridian crossing"},
    {"name": "Skellig Michael", "lat": 51.7704, "lon": -10.5394, "type": "Ley Node", "energy": "Michael Line", "description": "Monastic island on St. Michael's ley line stretching to Mt. Carmel"},
    {"name": "Serpent Mound, Ohio", "lat": 39.0253, "lon": -83.4303, "type": "Ley Node", "energy": "Crypto-volcanic", "description": "1,348ft effigy mound on ancient impact crater with energy readings"},
    {"name": "Baalbek, Lebanon", "lat": 34.0069, "lon": 36.2036, "type": "Ley Node", "energy": "Megalithic", "description": "1,000+ ton stone blocks placed on ancient ley crossroads"},
    {"name": "Adam's Peak, Sri Lanka", "lat": 6.8096, "lon": 80.4994, "type": "Energy Vortex", "energy": "Pilgrimage", "description": "Sacred footprint summit on global energy meridian line"},
    {"name": "Glastonbury Abbey", "lat": 51.1465, "lon": -2.7144, "type": "Ley Node", "energy": "Grail Line", "description": "Legendary burial place of Arthur on Mary ley line"},
]

# ═══════════════════════════════════════════════════════════════════
# DATA: GHOST SHIP SIGHTINGS (~25)
# ═══════════════════════════════════════════════════════════════════
GHOST_SHIPS = [
    {"name": "Mary Celeste", "lat": 38.2000, "lon": -17.1500, "year": 1872, "ship_type": "Brigantine", "description": "Found adrift near Azores - crew vanished, cargo intact, food still warm"},
    {"name": "Flying Dutchman", "lat": -34.3500, "lon": 18.4700, "year": 1641, "ship_type": "Phantom Ship", "description": "Ghostly vessel doomed to sail Cape of Good Hope forever"},
    {"name": "SS Ourang Medan", "lat": 3.0000, "lon": 106.0000, "year": 1947, "ship_type": "Cargo Ship", "description": "Entire crew found dead with expressions of terror, then ship exploded"},
    {"name": "Carroll A. Deering", "lat": 35.1500, "lon": -75.5300, "year": 1921, "ship_type": "Schooner", "description": "Found grounded at Cape Hatteras - crew gone, meals prepared on stove"},
    {"name": "SS Baychimo", "lat": 71.0000, "lon": -155.0000, "year": 1931, "ship_type": "Cargo Steamer", "description": "Abandoned in Arctic ice, then spotted drifting for 38 years"},
    {"name": "HMS Eurydice", "lat": 50.6200, "lon": -1.1100, "year": 1878, "ship_type": "Training Ship", "description": "Ghost of capsized frigate seen sailing into Sandown Bay"},
    {"name": "Caleuche", "lat": -42.5000, "lon": -73.5000, "year": 1600, "ship_type": "Ghost Ship", "description": "Chilote mythology - glowing ship crewed by the drowned near Chiloé"},
    {"name": "SS Valencia", "lat": 48.4333, "lon": -124.8333, "year": 1906, "ship_type": "Passenger Ship", "description": "Phantom lifeboat with skeletons spotted decades after wreck"},
    {"name": "Lady Lovibond", "lat": 51.3500, "lon": 1.4667, "year": 1748, "ship_type": "Schooner", "description": "Appears every 50 years at Goodwin Sands where jealous first mate sank her"},
    {"name": "Palatine Light (Princess Augusta)", "lat": 41.1700, "lon": -71.5600, "year": 1738, "ship_type": "Ghost Light", "description": "Burning ship phantom appears off Block Island on winter nights"},
    {"name": "MV Joyita", "lat": -14.2833, "lon": -171.7500, "year": 1955, "ship_type": "Motor Vessel", "description": "Found partially submerged in South Pacific - all 25 people vanished"},
    {"name": "Octavius", "lat": 75.0000, "lon": -10.0000, "year": 1775, "ship_type": "Trading Ship", "description": "Found in Arctic with frozen crew - captain at desk, pen in hand"},
    {"name": "SS Iron Mountain", "lat": 32.3500, "lon": -90.8800, "year": 1872, "ship_type": "Steamboat", "description": "Vanished on Mississippi River with 55 passengers - never found"},
    {"name": "Ghost Ship of Northumberland", "lat": 46.2200, "lon": -62.8000, "year": 1786, "ship_type": "Phantom Ship", "description": "Burning three-masted ship appears in Northumberland Strait, PEI"},
    {"name": "Eliza Battle", "lat": 31.2700, "lon": -87.5200, "year": 1858, "ship_type": "Steamboat", "description": "Phantom burning steamer appears on Tombigbee River before storms"},
    {"name": "SS Zebrina", "lat": 50.2400, "lon": -2.5700, "year": 1917, "ship_type": "Barge", "description": "Found grounded at Cherbourg - crew of five vanished without trace"},
    {"name": "Jenny", "lat": -62.0000, "lon": -60.0000, "year": 1840, "ship_type": "Schooner", "description": "Found in Drake Passage with frozen crew 17 years after being trapped"},
    {"name": "SV Resolven", "lat": 42.3600, "lon": -71.0500, "year": 1884, "ship_type": "Sailing Vessel", "description": "Found adrift off Boston - only a dog alive, crew disappeared"},
    {"name": "Kaz II", "lat": -19.3700, "lon": 146.7000, "year": 2007, "ship_type": "Catamaran", "description": "Modern ghost ship found off Queensland - engine running, laptop open, no crew"},
    {"name": "High Aim 6", "lat": -23.0000, "lon": 151.0000, "year": 2003, "ship_type": "Fishing Vessel", "description": "Indonesian fishing boat found crewless off Australia, engine running"},
    {"name": "Tai Ching 21", "lat": 12.0000, "lon": 121.0000, "year": 2008, "ship_type": "Tanker", "description": "Ghost tanker found drifting in Philippine waters, all crew missing"},
    {"name": "Sam Ratulangi PB 1600", "lat": 9.0500, "lon": 125.5000, "year": 2018, "ship_type": "Cargo Ship", "description": "Massive freighter found drifting off Myanmar - completely abandoned"},
    {"name": "SS Cotopax", "lat": 24.8000, "lon": -79.5000, "year": 1925, "ship_type": "Tramp Steamer", "description": "Vanished in Bermuda Triangle with 32 crew - wreck found 2020"},
    {"name": "MV Lyubov Orlova", "lat": 51.0000, "lon": -30.0000, "year": 2013, "ship_type": "Cruise Ship", "description": "Rat-infested cruise ship broke free and drifted across Atlantic"},
    {"name": "HMS Resolute", "lat": 67.0000, "lon": -65.0000, "year": 1854, "ship_type": "Barque", "description": "Abandoned in Arctic, found 1,200 miles away sailing itself a year later"},
]

# ═══════════════════════════════════════════════════════════════════
# DATA: SECRET BASES & UNDERGROUND FACILITIES (~30)
# ═══════════════════════════════════════════════════════════════════
SECRET_BASES = [
    {"name": "Area 51 (Groom Lake)", "lat": 37.2350, "lon": -115.8111, "country": "USA", "type": "Air Force Base", "description": "Most famous secret base - alleged reverse-engineering of alien technology"},
    {"name": "Dulce Base", "lat": 36.9336, "lon": -106.9989, "country": "USA", "type": "Underground Base", "description": "Alleged joint human-alien underground facility beneath Archuleta Mesa"},
    {"name": "Pine Gap", "lat": -23.7990, "lon": 133.7370, "country": "Australia", "type": "Signals Intelligence", "description": "CIA/NSA joint facility - rumored underground levels and UFO connection"},
    {"name": "Mount Weather", "lat": 39.0634, "lon": -77.8898, "country": "USA", "type": "Continuity of Government", "description": "Shadow government bunker with underground city for 200+ officials"},
    {"name": "Raven Rock (Site R)", "lat": 39.7400, "lon": -77.4200, "country": "USA", "type": "Military Command", "description": "Underground Pentagon backup - 900 foot deep hollowed mountain"},
    {"name": "Cheyenne Mountain", "lat": 38.7442, "lon": -104.8461, "country": "USA", "type": "NORAD Command", "description": "NORAD command center built to survive nuclear strikes"},
    {"name": "Kapustin Yar", "lat": 48.5700, "lon": 45.7500, "country": "Russia", "type": "Rocket Base", "description": "Soviet Roswell - secret rocket base with alleged UFO recovery program"},
    {"name": "Zhitkur Underground", "lat": 49.5300, "lon": 46.7300, "country": "Russia", "type": "Underground Base", "description": "Rumored vast underground facility near Volgograd for secret research"},
    {"name": "Rudloe Manor", "lat": 51.4047, "lon": -2.2328, "country": "UK", "type": "RAF Underground", "description": "UK's secret UFO desk location - massive underground quarry complex"},
    {"name": "Porton Down", "lat": 51.1319, "lon": -1.7106, "country": "UK", "type": "Research Facility", "description": "Chemical/biological defense lab - rumored exotic material analysis"},
    {"name": "Yamantau Mountain", "lat": 54.2500, "lon": 58.1000, "country": "Russia", "type": "Bunker Complex", "description": "Massive secret Russian bunker - nuclear war survival city"},
    {"name": "Diego Garcia", "lat": -7.3133, "lon": 72.4111, "country": "UK/USA", "type": "Military Base", "description": "Remote Indian Ocean base - rendition site, space tracking, UFO rumors"},
    {"name": "Svalbard Global Seed Vault", "lat": 78.2355, "lon": 15.4941, "country": "Norway", "type": "Underground Vault", "description": "Doomsday seed vault - what else is stored in the mountain?"},
    {"name": "HAARP", "lat": 62.3900, "lon": -145.1500, "country": "USA", "type": "Research Station", "description": "Ionospheric research - alleged weather control and mind control weapon"},
    {"name": "Denver International Airport", "lat": 39.8561, "lon": -104.6737, "country": "USA", "type": "Alleged Underground", "description": "Murals of apocalypse, gargoyles, and rumored deep underground base"},
    {"name": "Montauk, Long Island", "lat": 41.0359, "lon": -71.9545, "country": "USA", "type": "Air Force Station", "description": "Montauk Project - alleged time travel and psychic experiments"},
    {"name": "Dugway Proving Ground", "lat": 40.1775, "lon": -112.9983, "country": "USA", "type": "Army Facility", "description": "Biological/chemical testing ground larger than Rhode Island"},
    {"name": "S-4 (Papoose Lake)", "lat": 37.1501, "lon": -115.8226, "country": "USA", "type": "Alleged Facility", "description": "Bob Lazar's claimed facility housing nine alien spacecraft"},
    {"name": "Wright-Patterson AFB", "lat": 39.8261, "lon": -84.0484, "country": "USA", "type": "Air Force Base", "description": "Hangar 18 - alleged storage of Roswell crash debris and bodies"},
    {"name": "White Sands Missile Range", "lat": 32.3893, "lon": -106.4786, "country": "USA", "type": "Missile Range", "description": "Trinity test site area with persistent UFO activity reports"},
    {"name": "Menwith Hill", "lat": 54.0019, "lon": -1.6883, "country": "UK", "type": "Signals Intelligence", "description": "NSA's largest overseas facility - giant golf ball radomes"},
    {"name": "Mount Yamantau", "lat": 54.2500, "lon": 58.1000, "country": "Russia", "type": "Dead Hand System", "description": "Alleged Perimeter automatic nuclear response system bunker"},
    {"name": "Dulce, New Mexico Tunnels", "lat": 36.9336, "lon": -106.9989, "country": "USA", "type": "Tunnel Network", "description": "Phil Schneider's alleged underground battle with grey aliens"},
    {"name": "Camp Hero, Montauk", "lat": 41.0712, "lon": -71.8645, "country": "USA", "type": "Radar Station", "description": "SAGE radar site - Philadelphia Experiment and time portal claims"},
    {"name": "Tonopah Test Range", "lat": 38.0606, "lon": -116.7808, "country": "USA", "type": "Test Facility", "description": "Where stealth fighters were secretly based - what else hides here?"},
    {"name": "Wewelsburg Castle", "lat": 51.6068, "lon": 8.6509, "country": "Germany", "type": "SS Occult HQ", "description": "Himmler's occult headquarters - Black Sun symbol and ritual chamber"},
    {"name": "Mezhgorye", "lat": 54.3333, "lon": 57.8000, "country": "Russia", "type": "Closed City", "description": "Closed Russian city - two battalions guard whatever is inside the mountain"},
    {"name": "Korvatunturi, Finland", "lat": 68.0736, "lon": 29.3119, "country": "Finland", "type": "Underground", "description": "Sacred Sami fell with alleged underground military facility"},
    {"name": "Los Alamos National Lab", "lat": 35.8800, "lon": -106.3060, "country": "USA", "type": "Nuclear Lab", "description": "Birthplace of atomic bomb - deep underground classified sections"},
    {"name": "Iron Mountain, Pennsylvania", "lat": 40.2700, "lon": -76.7400, "country": "USA", "type": "Underground Vault", "description": "Massive limestone mine storing government records and corporate data"},
]

# ═══════════════════════════════════════════════════════════════════
# DATA: ANCIENT ASTRONAUT SITES (~25)
# ═══════════════════════════════════════════════════════════════════
ANCIENT_ASTRONAUT_SITES = [
    {"name": "Great Pyramid of Giza", "lat": 29.9792, "lon": 31.1342, "era": "2560 BC", "civilization": "Egyptian", "description": "Precision construction with alleged alien engineering assistance"},
    {"name": "Nazca Lines", "lat": -14.7350, "lon": -75.1300, "era": "500 BC", "civilization": "Nazca", "description": "Giant geoglyphs theorized as alien landing strip markers"},
    {"name": "Puma Punku", "lat": -16.5617, "lon": -68.6806, "era": "536 AD", "civilization": "Tiwanaku", "description": "H-blocks with impossible precision - laser-cut stone theory"},
    {"name": "Sacsayhuamán", "lat": -13.5097, "lon": -71.9828, "era": "1100 AD", "civilization": "Inca/Pre-Inca", "description": "200-ton stones fit without mortar - vitrified surfaces suggest heat"},
    {"name": "Baalbek Megaliths", "lat": 34.0069, "lon": 36.2036, "era": "7000 BC", "civilization": "Unknown/Phoenician", "description": "1,650-ton Stone of the Pregnant Woman - no known construction method"},
    {"name": "Göbekli Tepe", "lat": 37.2231, "lon": 38.9225, "era": "9600 BC", "civilization": "Pre-agricultural", "description": "World's oldest temple predates agriculture - who built it?"},
    {"name": "Moai of Easter Island", "lat": -27.1127, "lon": -109.3497, "era": "1250 AD", "civilization": "Rapa Nui", "description": "887 monolithic statues - oral tradition says they 'walked' to position"},
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8439, "era": "200 BC", "civilization": "Unknown", "description": "Mica sheets in pyramid, mercury rivers, Orion belt alignment"},
    {"name": "Derinkuyu Underground City", "lat": 38.3735, "lon": 34.7347, "era": "800 BC", "civilization": "Phrygian", "description": "18-story underground city for 20,000 people - who dug this and why?"},
    {"name": "Pumapunku", "lat": -16.5617, "lon": -68.6806, "era": "536 AD", "civilization": "Tiwanaku", "description": "Interlocking stone blocks suggest advanced machining technology"},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670, "era": "1150 AD", "civilization": "Khmer", "description": "Temple mirrors Draco constellation - encoded astronomical knowledge"},
    {"name": "Carnac Stones", "lat": 47.5950, "lon": -3.0700, "era": "4500 BC", "civilization": "Neolithic", "description": "3,000 megaliths in precise rows - earthquake prediction system?"},
    {"name": "Dogon Country, Mali", "lat": 14.0000, "lon": -3.5000, "era": "Ancient", "civilization": "Dogon", "description": "Knew Sirius B existed before telescopes - claim star visitors taught them"},
    {"name": "Tassili n'Ajjer", "lat": 25.5000, "lon": 9.0000, "era": "8000 BC", "civilization": "Saharan", "description": "Cave paintings of suited beings and disc-shaped objects"},
    {"name": "Palenque Sarcophagus", "lat": 17.4838, "lon": -92.0462, "era": "683 AD", "civilization": "Maya", "description": "King Pakal's lid shows figure in what looks like a spacecraft cockpit"},
    {"name": "Vimana Temples of India", "lat": 13.0069, "lon": 77.5650, "era": "3000 BC", "civilization": "Vedic", "description": "Ancient texts describe flying craft (vimanas) with mercury engines"},
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "era": "3000 BC", "civilization": "Neolithic", "description": "Bluestones transported 150 miles - acoustic and astronomical wonder"},
    {"name": "Sumer (Eridu)", "lat": 30.8167, "lon": 45.9833, "era": "5400 BC", "civilization": "Sumerian", "description": "Anunnaki texts describe beings from Nibiru engineering humanity"},
    {"name": "Yonaguni Monument", "lat": 24.4348, "lon": 123.0104, "era": "10000 BC?", "civilization": "Unknown", "description": "Underwater stepped pyramid off Japan - natural or carved?"},
    {"name": "Longyou Caves, China", "lat": 28.9300, "lon": 119.1700, "era": "212 BC?", "civilization": "Unknown", "description": "Massive hand-carved caves removing 1M cubic meters - no historical record"},
    {"name": "Saqqara Bird", "lat": 29.8715, "lon": 31.2163, "era": "200 BC", "civilization": "Egyptian", "description": "Wooden artifact with aerodynamic properties resembling a glider"},
    {"name": "Antikythera Mechanism Site", "lat": 35.8614, "lon": 23.3000, "era": "100 BC", "civilization": "Greek", "description": "Ancient analog computer found in shipwreck - impossibly advanced"},
    {"name": "Sigiria Rock Fortress", "lat": 7.9570, "lon": 80.7603, "era": "477 AD", "civilization": "Sinhalese", "description": "Sky fortress on 200m rock pillar with advanced water engineering"},
    {"name": "Malta Temples (Ħaġar Qim)", "lat": 35.8275, "lon": 14.4419, "era": "3600 BC", "civilization": "Neolithic", "description": "Oldest freestanding structures predate pyramids by 1,000 years"},
    {"name": "Ollantaytambo", "lat": -13.2581, "lon": -72.2633, "era": "1400 AD", "civilization": "Inca", "description": "Perfectly fitted 50-ton stones hauled up mountain with unknown methods"},
]

# ═══════════════════════════════════════════════════════════════════
# DATA: SPONTANEOUS COMBUSTION & STRANGE EVENTS (~25)
# ═══════════════════════════════════════════════════════════════════
STRANGE_EVENTS = [
    {"name": "Mary Reeser, St. Petersburg FL", "lat": 27.7676, "lon": -82.6403, "year": 1951, "type": "Spontaneous Combustion", "description": "Reduced to ash in her chair - nearby objects unburned, slippered foot intact"},
    {"name": "Tunguska Event, Siberia", "lat": 60.8860, "lon": 101.8940, "year": 1908, "type": "Explosion", "description": "Airburst flattened 80M trees - no crater, cause still debated"},
    {"name": "Dyatlov Pass, Russia", "lat": 61.7545, "lon": 59.4620, "year": 1959, "type": "Mysterious Deaths", "description": "Nine hikers died in bizarre circumstances - torn tent, paradoxical undressing"},
    {"name": "Ball Lightning, Bath UK", "lat": 51.3811, "lon": -2.3590, "year": 1638, "type": "Ball Lightning", "description": "8-foot fireball entered church during service, killed 4 people"},
    {"name": "Jemison, Alabama SHC", "lat": 32.9584, "lon": -86.7442, "year": 1966, "type": "Spontaneous Combustion", "description": "Dr. J. Irving Bentley reduced to pile of ash, hole burned through floor"},
    {"name": "Raining Frogs, Ishikawa Japan", "lat": 36.5944, "lon": 136.6256, "year": 2009, "type": "Animal Rain", "description": "Tadpoles and small frogs rained down on city - no waterspout nearby"},
    {"name": "Kentucky Meat Shower", "lat": 38.2000, "lon": -83.9000, "year": 1876, "type": "Strange Rain", "description": "Chunks of meat fell from clear sky over 100x50 yard area"},
    {"name": "Blood Rain, Kerala India", "lat": 9.5916, "lon": 76.5222, "year": 2001, "type": "Strange Rain", "description": "Red rain fell for months - cells without DNA initially puzzled scientists"},
    {"name": "Oak Island Money Pit, Nova Scotia", "lat": 44.5130, "lon": -64.2939, "year": 1795, "type": "Mystery Construction", "description": "Engineered booby-trapped shaft - coconut fiber, stone tablet, flood tunnels"},
    {"name": "Dancing Plague, Strasbourg", "lat": 48.5734, "lon": 7.7521, "year": 1518, "type": "Mass Hysteria", "description": "400 people danced uncontrollably for days - several died from exhaustion"},
    {"name": "Lead Masks Case, Niterói Brazil", "lat": -22.8833, "lon": -43.1036, "year": 1966, "type": "Mysterious Deaths", "description": "Two men found dead wearing lead eye masks with notes about capsule ingestion"},
    {"name": "Hessdalen Lights, Norway", "lat": 62.8100, "lon": 11.2000, "year": 1981, "type": "Anomalous Lights", "description": "Persistent unexplained lights documented by Project Hessdalen since 1984"},
    {"name": "Taos Hum, New Mexico", "lat": 36.4072, "lon": -105.5730, "year": 1991, "type": "Anomalous Sound", "description": "Persistent low-frequency hum heard by 2% of population, source unknown"},
    {"name": "Overtoun Bridge Dog Deaths", "lat": 55.9372, "lon": -4.5531, "year": 1950, "type": "Animal Anomaly", "description": "Hundreds of dogs have jumped from this specific bridge spot since 1950s"},
    {"name": "Yellowstone Zone of Death", "lat": 44.2655, "lon": -111.1045, "year": 2005, "type": "Legal Anomaly", "description": "50 sq mile area where murder may be technically unprosecutable"},
    {"name": "Great Molasses Flood, Boston", "lat": 42.3656, "lon": -71.0545, "year": 1919, "type": "Disaster", "description": "2.3M gallons of molasses created 25ft wave killing 21 people"},
    {"name": "Tanganyika Laughter Epidemic", "lat": -2.4670, "lon": 32.9000, "year": 1962, "type": "Mass Hysteria", "description": "Laughing illness affected 1,000+ people across multiple villages"},
    {"name": "Bennington Triangle Disappearances", "lat": 43.0200, "lon": -73.0400, "year": 1945, "type": "Disappearances", "description": "Five people vanished without trace in five years in small Vermont area"},
    {"name": "Mothman, Point Pleasant WV", "lat": 38.8451, "lon": -82.1368, "year": 1966, "type": "Cryptid/Prophecy", "description": "Red-eyed winged creature sightings preceded Silver Bridge collapse"},
    {"name": "Flannan Isles Lighthouse", "lat": 58.2878, "lon": -7.5883, "year": 1900, "type": "Disappearance", "description": "Three lighthouse keepers vanished - clocks stopped, meal uneaten"},
    {"name": "Coventry Street Poltergeist", "lat": 52.4081, "lon": -1.5106, "year": 1963, "type": "Poltergeist", "description": "Stones materialized inside sealed rooms, objects flew in front of police"},
    {"name": "Roanoke Colony", "lat": 35.8493, "lon": -75.6546, "year": 1590, "type": "Disappearance", "description": "117 colonists vanished leaving only CROATOAN carved on post"},
    {"name": "Phaistos Disc, Crete", "lat": 35.0511, "lon": 24.8167, "year": -1700, "type": "Anomalous Artifact", "description": "3,700-year-old clay disc with undeciphered symbols - unique in world"},
    {"name": "Wow! Signal, Ohio", "lat": 40.3400, "lon": -83.0400, "year": 1977, "type": "Signal Anomaly", "description": "72-second narrowband radio signal from Sagittarius - never repeated"},
    {"name": "Bloop Sound, South Pacific", "lat": -50.0000, "lon": -100.0000, "year": 1997, "type": "Sound Anomaly", "description": "Ultra-low frequency ocean sound louder than blue whale - source unknown"},
]

# ═══════════════════════════════════════════════════════════════════
# DATA: PORTALS & DIMENSIONAL ANOMALIES (~25)
# ═══════════════════════════════════════════════════════════════════
PORTALS = [
    {"name": "Skinwalker Ranch, Utah", "lat": 40.2588, "lon": -109.8880, "type": "Multi-Phenomena Portal", "description": "Cattle mutilation, orbs, portals, shapeshifters - studied by NIDS and Pentagon"},
    {"name": "Stull Cemetery, Kansas", "lat": 38.9211, "lon": -95.4333, "type": "Gateway to Hell", "description": "Pope allegedly ordered his plane to avoid flying over this cemetery"},
    {"name": "Devil's Sea (Dragon's Triangle)", "lat": 29.0000, "lon": 140.0000, "type": "Dimensional Rift", "description": "Japanese Bermuda Triangle - ships and planes enter and never return"},
    {"name": "Plynlimon, Wales", "lat": 52.4667, "lon": -3.7500, "type": "Fairy Portal", "description": "Welsh mountains where people report entering fairy realm and losing time"},
    {"name": "Sedona Dimensional Vortex", "lat": 34.8697, "lon": -111.7610, "type": "Inter-dimensional", "description": "Red rock vortices allegedly thin the boundary between dimensions"},
    {"name": "Superstition Mountains Portal", "lat": 33.4500, "lon": -111.1700, "type": "Portal/Gateway", "description": "Apache legends of doorway to underworld inside the mountains"},
    {"name": "Mount Shasta Portal", "lat": 41.4092, "lon": -122.1949, "type": "Lemurian Gateway", "description": "Alleged entrance to underground Lemurian city Telos"},
    {"name": "Hoia Baciu Forest, Romania", "lat": 46.7700, "lon": 23.5400, "type": "Time Slip Zone", "description": "Missing time, apparitions, and a perfectly circular clearing with no growth"},
    {"name": "Markawasi, Peru", "lat": -11.7700, "lon": -76.5800, "type": "Stone Portal", "description": "Plateau with rock formations matching faces, animals - alleged portal"},
    {"name": "Ramayana Bridge (Adam's Bridge)", "lat": 9.1333, "lon": 79.4333, "type": "Ancient Gateway", "description": "Chain of shoals between India and Sri Lanka - natural or built?"},
    {"name": "Aramu Muru Doorway, Peru", "lat": -16.1758, "lon": -69.5336, "type": "Star Gate", "description": "T-shaped carved doorway in rock face - locals say priests disappeared into it"},
    {"name": "Loch Ness, Scotland", "lat": 57.3229, "lon": -4.4244, "type": "Water Portal", "description": "Aleister Crowley's Boleskine House and persistent creature sightings"},
    {"name": "Bigelow Ranch Portal", "lat": 40.2588, "lon": -109.8880, "type": "Studied Portal", "description": "AAWSAP/AATIP Pentagon program studied anomalous phenomena here"},
    {"name": "Devil's Gate Dam, Pasadena", "lat": 34.1808, "lon": -118.1755, "type": "Occult Gateway", "description": "Jack Parsons and L. Ron Hubbard performed Babalon Working rituals here"},
    {"name": "Stonehenge Portal", "lat": 51.1789, "lon": -1.8262, "type": "Dimensional Thin Spot", "description": "Acoustic properties create altered states - possible dimensional gateway"},
    {"name": "Lake Anjikuni, Canada", "lat": 62.1500, "lon": -97.7500, "type": "Mass Disappearance", "description": "Entire Inuit village allegedly vanished overnight in 1930"},
    {"name": "Erdstall Tunnels, Bavaria", "lat": 48.5000, "lon": 12.0000, "type": "Underground Portal", "description": "700+ narrow medieval tunnels with no known purpose - spirit passages?"},
    {"name": "Nan Madol, Micronesia", "lat": 6.8444, "lon": 158.3353, "type": "Ancient Portal", "description": "Venice of the Pacific - basalt city built on coral reef with spirit gateway"},
    {"name": "Cave of the Crystals, Mexico", "lat": 27.8500, "lon": -105.4833, "type": "Earth Portal", "description": "Giant selenite crystals 300m underground - extreme conditions, life found in crystals"},
    {"name": "Hockomock Swamp, MA", "lat": 41.9600, "lon": -71.0700, "type": "Bridgewater Triangle Core", "description": "Native American 'place where spirits dwell' - orbs, creatures, vanishings"},
    {"name": "Mount Rtanj, Serbia", "lat": 43.7667, "lon": 21.9333, "type": "Pyramid Portal", "description": "Natural pyramid-shaped mountain with alleged energy emissions and portal"},
    {"name": "Tiahuanaco Sun Gate", "lat": -16.5544, "lon": -68.6728, "type": "Star Gate", "description": "Carved doorway with calendar of impossible astronomical precision"},
    {"name": "Bell Witch Cave, Tennessee", "lat": 36.5500, "lon": -87.1000, "type": "Entity Portal", "description": "Cave where Bell Witch entity manifested - Andrew Jackson fled in terror"},
    {"name": "Agartha Entry - Mount Epomeo", "lat": 40.7333, "lon": 13.8833, "type": "Inner Earth Portal", "description": "Italian volcanic island alleged to contain passage to hollow Earth"},
    {"name": "Shambhala Gate - Altai Mountains", "lat": 49.8000, "lon": 86.5900, "type": "Mystical Gateway", "description": "Nicholas Roerich's expedition sought entrance to hidden kingdom"},
]


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _get_mode_data(mode: str) -> list:
    """Return the dataset for the selected mode."""
    mapping = {
        "UFO Sighting Hotspots": UFO_SIGHTINGS,
        "Haunted Places": HAUNTED_PLACES,
        "Bermuda Triangle & Anomalies": ANOMALY_ZONES,
        "Crop Circle Locations": CROP_CIRCLES,
        "Ley Lines & Energy Vortices": LEY_LINES,
        "Ghost Ship Sightings": GHOST_SHIPS,
        "Secret Bases & Underground Facilities": SECRET_BASES,
        "Ancient Astronaut Sites": ANCIENT_ASTRONAUT_SITES,
        "Spontaneous Combustion & Strange Events": STRANGE_EVENTS,
        "Portals & Dimensional Anomalies": PORTALS,
    }
    return mapping.get(mode, [])


def _get_mode_icon(mode: str) -> str:
    """Return a Folium-compatible icon name for the mode."""
    icons = {
        "UFO Sighting Hotspots": "star",
        "Haunted Places": "home",
        "Bermuda Triangle & Anomalies": "warning-sign",
        "Crop Circle Locations": "record",
        "Ley Lines & Energy Vortices": "flash",
        "Ghost Ship Sightings": "flag",
        "Secret Bases & Underground Facilities": "lock",
        "Ancient Astronaut Sites": "tower",
        "Spontaneous Combustion & Strange Events": "fire",
        "Portals & Dimensional Anomalies": "transfer",
    }
    return icons.get(mode, "info-sign")


def _get_mode_emoji(mode: str) -> str:
    """Return a descriptive label prefix for the mode."""
    labels = {
        "UFO Sighting Hotspots": "UFO",
        "Haunted Places": "Ghost",
        "Bermuda Triangle & Anomalies": "Anomaly",
        "Crop Circle Locations": "Circle",
        "Ley Lines & Energy Vortices": "Vortex",
        "Ghost Ship Sightings": "Ship",
        "Secret Bases & Underground Facilities": "Base",
        "Ancient Astronaut Sites": "Ancient",
        "Spontaneous Combustion & Strange Events": "Event",
        "Portals & Dimensional Anomalies": "Portal",
    }
    return labels.get(mode, "Item")


@st.cache_data(ttl=3600)
def _build_dataframe(mode: str) -> pd.DataFrame:
    """Build a pandas DataFrame from the hardcoded data for the given mode."""
    data = _get_mode_data(mode)
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    return df


def _build_popup_html(row: dict, mode: str) -> str:
    """Build safe HTML popup content for a map marker."""
    name = escape(str(row.get("name", "Unknown")))
    desc = escape(str(row.get("description", "")))
    color = MODE_COLORS.get(mode, ACCENT_COLOR)

    extra_lines = []
    for key in ["year", "type", "country", "era", "civilization", "pattern",
                 "energy", "ship_type", "ghost", "incidents", "radius_km"]:
        val = row.get(key)
        if val is not None:
            label = key.replace("_", " ").title()
            extra_lines.append(f"<b>{escape(label)}:</b> {escape(str(val))}")

    extras_html = "<br>".join(extra_lines)
    if extras_html:
        extras_html = f"<br>{extras_html}"

    html = (
        f'<div style="font-family:Inter,sans-serif;max-width:280px;'
        f'background:{SURFACE_COLOR};color:{TEXT_COLOR};padding:10px;'
        f'border-radius:8px;border:1px solid {color}40;">'
        f'<b style="color:{color};font-size:14px;">{name}</b>'
        f'{extras_html}'
        f'<br><span style="color:{MUTED_COLOR};font-size:12px;">{desc}</span>'
        f'</div>'
    )
    return html


def _create_folium_map(df: pd.DataFrame, mode: str, use_clustering: bool,
                       use_heatmap: bool) -> folium.Map:
    """Create a Folium map with markers for the given mode data."""
    color = MODE_COLORS.get(mode, ACCENT_COLOR)
    icon_name = _get_mode_icon(mode)

    # Calculate center
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=3,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Heatmap layer
    if use_heatmap:
        heat_data = df[["lat", "lon"]].values.tolist()
        HeatMap(
            heat_data,
            radius=25,
            blur=15,
            max_zoom=10,
            gradient={0.2: "#0a0e1a", 0.4: "#06b6d4", 0.6: "#f59e0b", 0.8: "#ef4444", 1.0: "#ff0000"},
        ).add_to(m)

    # Marker layer
    if use_clustering:
        marker_group = MarkerCluster(name="Locations")
    else:
        marker_group = folium.FeatureGroup(name="Locations")

    for _, row in df.iterrows():
        popup_html = _build_popup_html(row.to_dict(), mode)

        # For anomaly zones, draw circles
        if mode == "Bermuda Triangle & Anomalies" and "radius_km" in row and pd.notna(row.get("radius_km")):
            folium.Circle(
                location=[row["lat"], row["lon"]],
                radius=float(row["radius_km"]) * 1000,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.15,
                weight=2,
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(m)

        # For ley lines, draw connecting lines
        if mode == "Ley Lines & Energy Vortices":
            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=8,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=2,
                popup=folium.Popup(popup_html, max_width=300),
            ).add_to(marker_group)
        else:
            folium.Marker(
                location=[row["lat"], row["lon"]],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="red", icon=icon_name, prefix="glyphicon"),
            ).add_to(marker_group)

    marker_group.add_to(m)

    # For ley lines mode, draw lines between nearby points
    if mode == "Ley Lines & Energy Vortices" and len(df) > 1:
        ley_group = folium.FeatureGroup(name="Ley Lines")
        coords = df[["lat", "lon"]].values.tolist()
        # Connect points that are within 3000km of each other
        for i in range(len(coords)):
            for j in range(i + 1, len(coords)):
                dist = ((coords[i][0] - coords[j][0]) ** 2 +
                        (coords[i][1] - coords[j][1]) ** 2) ** 0.5
                if dist < 25:  # Roughly 2500km in degrees
                    folium.PolyLine(
                        [coords[i], coords[j]],
                        color="rgba(236,72,153,0.31)",
                        weight=1,
                        dash_array="5 10",
                    ).add_to(ley_group)
        ley_group.add_to(m)

    folium.LayerControl().add_to(m)
    return m


def _create_distribution_chart(df: pd.DataFrame, mode: str, group_col: str) -> plt.Figure:
    """Create a matplotlib bar chart showing distribution of a category column."""
    color = MODE_COLORS.get(mode, ACCENT_COLOR)

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    if group_col not in df.columns:
        ax.text(0.5, 0.5, "No grouping column available", ha="center", va="center",
                color=TEXT_COLOR, fontsize=14, transform=ax.transAxes)
        return fig

    counts = df[group_col].value_counts().head(15)

    bars = ax.barh(range(len(counts)), counts.values, color=color, alpha=0.8,
                   edgecolor=color, linewidth=0.5)
    ax.set_yticks(range(len(counts)))
    ax.set_yticklabels([str(label)[:30] for label in counts.index],
                       fontsize=9, color=TEXT_COLOR)
    ax.set_xlabel("Count", fontsize=11, color=TEXT_COLOR)
    ax.set_title(f"{mode} - Distribution by {group_col.replace('_', ' ').title()}",
                 fontsize=13, color=ACCENT_COLOR, pad=12)
    ax.tick_params(colors=TEXT_COLOR)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(MUTED_COLOR)
    ax.spines["left"].set_color(MUTED_COLOR)
    ax.invert_yaxis()

    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=9, color=TEXT_COLOR)

    plt.tight_layout()
    return fig


def _create_map_scatter(df: pd.DataFrame, mode: str) -> plt.Figure:
    """Create a matplotlib scatter plot showing geographic distribution."""
    color = MODE_COLORS.get(mode, ACCENT_COLOR)

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    ax.scatter(df["lon"], df["lat"], c=color, s=50, alpha=0.8,
              edgecolors="white", linewidths=0.5, zorder=5)

    # Draw simple world outline box
    ax.axhline(y=0, color=MUTED_COLOR, linewidth=0.3, alpha=0.5)
    ax.axvline(x=0, color=MUTED_COLOR, linewidth=0.3, alpha=0.5)

    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Longitude", fontsize=11, color=TEXT_COLOR)
    ax.set_ylabel("Latitude", fontsize=11, color=TEXT_COLOR)
    ax.set_title(f"{mode} - Global Distribution",
                 fontsize=13, color=ACCENT_COLOR, pad=12)
    ax.tick_params(colors=TEXT_COLOR)
    ax.spines["top"].set_color(MUTED_COLOR)
    ax.spines["right"].set_color(MUTED_COLOR)
    ax.spines["bottom"].set_color(MUTED_COLOR)
    ax.spines["left"].set_color(MUTED_COLOR)

    plt.tight_layout()
    return fig


def _create_timeline_chart(df: pd.DataFrame, mode: str) -> plt.Figure:
    """Create a timeline chart if the data has a year column."""
    color = MODE_COLORS.get(mode, ACCENT_COLOR)

    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    if "year" not in df.columns:
        ax.text(0.5, 0.5, "No year data available for timeline", ha="center",
                va="center", color=TEXT_COLOR, fontsize=14, transform=ax.transAxes)
        return fig

    years = df["year"].dropna().astype(int)
    if len(years) == 0:
        ax.text(0.5, 0.5, "No valid year data", ha="center", va="center",
                color=TEXT_COLOR, fontsize=14, transform=ax.transAxes)
        return fig

    # Bin by decade/century depending on range
    year_range = years.max() - years.min()
    if year_range > 500:
        bin_size = 100
        xlabel = "Century"
    elif year_range > 100:
        bin_size = 25
        xlabel = "Quarter Century"
    else:
        bin_size = 10
        xlabel = "Decade"

    bins = range(int(years.min() // bin_size * bin_size),
                 int(years.max() // bin_size * bin_size) + bin_size + 1,
                 bin_size)
    ax.hist(years, bins=list(bins), color=color, alpha=0.8,
            edgecolor=SURFACE_COLOR, linewidth=0.5)

    ax.set_xlabel(xlabel, fontsize=11, color=TEXT_COLOR)
    ax.set_ylabel("Count", fontsize=11, color=TEXT_COLOR)
    ax.set_title(f"{mode} - Timeline", fontsize=13, color=ACCENT_COLOR, pad=12)
    ax.tick_params(colors=TEXT_COLOR)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color(MUTED_COLOR)
    ax.spines["left"].set_color(MUTED_COLOR)

    plt.tight_layout()
    return fig


def _get_group_col(mode: str) -> str:
    """Return the best column to group by for each mode."""
    mapping = {
        "UFO Sighting Hotspots": "type",
        "Haunted Places": "type",
        "Bermuda Triangle & Anomalies": "type",
        "Crop Circle Locations": "pattern",
        "Ley Lines & Energy Vortices": "type",
        "Ghost Ship Sightings": "ship_type",
        "Secret Bases & Underground Facilities": "type",
        "Ancient Astronaut Sites": "civilization",
        "Spontaneous Combustion & Strange Events": "type",
        "Portals & Dimensional Anomalies": "type",
    }
    return mapping.get(mode, "type")


def _get_mode_description(mode: str) -> str:
    """Return a short description for each map mode."""
    descriptions = {
        "UFO Sighting Hotspots": "Major UFO and UAP sighting locations spanning from 1561 to present day. Includes crash sites, mass sightings, military encounters, and government-acknowledged incidents.",
        "Haunted Places": "The world's most haunted locations - castles, prisons, asylums, battlefields, and cursed sites where ghostly activity has been documented for centuries.",
        "Bermuda Triangle & Anomalies": "Anomaly zones around the world where ships, planes, and people mysteriously vanish. Includes vile vortex points and electromagnetic dead zones.",
        "Crop Circle Locations": "Major crop circle formation sites, primarily in Wiltshire UK but also worldwide. Includes the most complex and controversial formations.",
        "Ley Lines & Energy Vortices": "Ancient energy pathways connecting sacred sites, vortex points, and Earth chakra locations. Ley lines and power nodes mapped globally.",
        "Ghost Ship Sightings": "Maritime mysteries - ships found abandoned, phantom vessels, and crews that vanished without trace across the world's oceans.",
        "Secret Bases & Underground Facilities": "Classified military installations, underground bunker complexes, and alleged joint human-alien facilities around the world.",
        "Ancient Astronaut Sites": "Archaeological sites theorized to show evidence of extraterrestrial contact or advanced lost technology in the ancient world.",
        "Spontaneous Combustion & Strange Events": "Bizarre historical events including spontaneous human combustion, anomalous rains, mass hysteria, and unexplained phenomena.",
        "Portals & Dimensional Anomalies": "Alleged interdimensional gateways, time slip zones, and locations where the boundary between worlds is said to be thin.",
    }
    return descriptions.get(mode, "")


# ═══════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════

def render_paranormal_maps_tab():
    """Main render function for the Paranormal & UFO Maps tab."""

    # -- Header --
    st.markdown("""
    <div class="tab-header red">
        <h4>Paranormal & UFO Maps</h4>
        <p>Explore the world's most mysterious locations &mdash; UFO hotspots, haunted sites, anomaly zones, secret bases, ancient mysteries, and dimensional portals. All data curated from historical records and eyewitness accounts.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode Selection & Controls
    # ══════════════════════════════════════════
    st.markdown("#### Map Mode")

    mode_options = [
        "UFO Sighting Hotspots",
        "Haunted Places",
        "Bermuda Triangle & Anomalies",
        "Crop Circle Locations",
        "Ley Lines & Energy Vortices",
        "Ghost Ship Sightings",
        "Secret Bases & Underground Facilities",
        "Ancient Astronaut Sites",
        "Spontaneous Combustion & Strange Events",
        "Portals & Dimensional Anomalies",
    ]

    mode = st.selectbox(
        "Select Paranormal Category",
        mode_options,
        key="paranormal_mode",
        help="Choose a category of paranormal phenomena to explore on the map",
    )

    # Display mode description
    mode_desc = _get_mode_description(mode)
    mode_color = MODE_COLORS.get(mode, ACCENT_COLOR)
    st.markdown(
        f'<div style="background:{SURFACE_COLOR};border-left:3px solid {mode_color};'
        f'padding:10px 14px;border-radius:4px;margin:8px 0 16px 0;'
        f'color:{TEXT_COLOR};font-size:14px;">{escape(mode_desc)}</div>',
        unsafe_allow_html=True,
    )

    # Controls row
    col_cluster, col_heat, col_chart = st.columns(3)
    with col_cluster:
        use_clustering = st.checkbox("Cluster markers", value=True, key="paranormal_cluster",
                                     help="Group nearby markers into clusters")
    with col_heat:
        use_heatmap = st.checkbox("Show heatmap", value=False, key="paranormal_heat",
                                  help="Overlay a heatmap of location density")
    with col_chart:
        show_charts = st.checkbox("Show analytics", value=True, key="paranormal_charts",
                                  help="Display distribution charts and statistics")

    # Search / filter
    with st.expander("Filter & Search", expanded=False):
        search_text = st.text_input(
            "Search locations by name or description",
            key="paranormal_search",
            placeholder="e.g. Roswell, pyramid, triangle...",
        )

        fcol1, fcol2 = st.columns(2)
        with fcol1:
            lat_range = st.slider(
                "Latitude Range", -90.0, 90.0, (-90.0, 90.0),
                key="paranormal_lat_range",
            )
        with fcol2:
            lon_range = st.slider(
                "Longitude Range", -180.0, 180.0, (-180.0, 180.0),
                key="paranormal_lon_range",
            )

    # ══════════════════════════════════════════
    # SECTION 2: Build & Filter Data
    # ══════════════════════════════════════════
    df = _build_dataframe(mode)

    if df.empty:
        st.warning("No data available for this mode.")
        return

    # Apply filters
    filtered = df.copy()

    # Text search
    if search_text and search_text.strip():
        search_lower = search_text.strip().lower()
        mask = pd.Series(False, index=filtered.index)
        for col in filtered.columns:
            if filtered[col].dtype == object:
                mask = mask | filtered[col].astype(str).str.lower().str.contains(
                    search_lower, na=False
                )
        filtered = filtered[mask]

    # Geographic filter
    if lat_range != (-90.0, 90.0):
        filtered = filtered[
            (filtered["lat"] >= lat_range[0]) & (filtered["lat"] <= lat_range[1])
        ]
    if lon_range != (-180.0, 180.0):
        filtered = filtered[
            (filtered["lon"] >= lon_range[0]) & (filtered["lon"] <= lon_range[1])
        ]

    if filtered.empty:
        st.warning("No locations match your current filters. Try broadening your search.")
        return

    # ══════════════════════════════════════════
    # SECTION 3: Statistics Dashboard
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Statistics")

    total_locations = len(filtered)
    total_unfiltered = len(df)
    group_col = _get_group_col(mode)
    unique_types = filtered[group_col].nunique() if group_col in filtered.columns else 0

    # Hemisphere analysis
    northern = (filtered["lat"] > 0).sum()
    southern = (filtered["lat"] <= 0).sum()
    western = (filtered["lon"] < 0).sum()
    eastern = (filtered["lon"] >= 0).sum()

    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.metric("Locations Shown", f"{total_locations}", delta=None if total_locations == total_unfiltered else f"{total_locations - total_unfiltered}")
    with stat2:
        st.metric("Unique Categories", f"{unique_types}")
    with stat3:
        st.metric("Northern / Southern", f"{northern} / {southern}")
    with stat4:
        st.metric("Western / Eastern", f"{western} / {eastern}")

    # Extra stats row for modes with numeric data
    if "incidents" in filtered.columns:
        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.metric("Total Incidents", f"{int(filtered['incidents'].sum())}")
        with s2:
            st.metric("Max Incidents (Zone)", f"{int(filtered['incidents'].max())}")
        with s3:
            st.metric("Avg Incidents", f"{filtered['incidents'].mean():.1f}")
        with s4:
            st.metric("Avg Radius (km)", f"{filtered['radius_km'].mean():.0f}" if "radius_km" in filtered.columns else "N/A")

    if "year" in filtered.columns:
        years = filtered["year"].dropna()
        if len(years) > 0:
            y1, y2, y3, y4 = st.columns(4)
            with y1:
                st.metric("Earliest Year", f"{int(years.min())}")
            with y2:
                st.metric("Latest Year", f"{int(years.max())}")
            with y3:
                st.metric("Year Span", f"{int(years.max() - years.min())} years")
            with y4:
                median_year = int(years.median())
                st.metric("Median Year", f"{median_year}")

    # ══════════════════════════════════════════
    # SECTION 4: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Interactive Map")
    st.caption(f"Showing {total_locations} {_get_mode_emoji(mode).lower()} locations | Mode: {mode}")

    with st.spinner("Generating paranormal map..."):
        m = _create_folium_map(filtered, mode, use_clustering, use_heatmap)
        map_html = m._repr_html_()
        components.html(map_html, height=550)

    # ══════════════════════════════════════════
    # SECTION 5: Charts & Analytics
    # ══════════════════════════════════════════
    if show_charts:
        st.markdown("---")
        st.markdown("#### Analytics")

        chart_tab1, chart_tab2, chart_tab3 = st.tabs([
            "Distribution", "Geographic Scatter", "Timeline"
        ])

        with chart_tab1:
            fig_dist = _create_distribution_chart(filtered, mode, group_col)
            st.pyplot(fig_dist)
            plt.close(fig_dist)

        with chart_tab2:
            fig_scatter = _create_map_scatter(filtered, mode)
            st.pyplot(fig_scatter)
            plt.close(fig_scatter)

        with chart_tab3:
            fig_time = _create_timeline_chart(filtered, mode)
            st.pyplot(fig_time)
            plt.close(fig_time)

    # ══════════════════════════════════════════
    # SECTION 6: Data Table
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Location Data")

    # Column display order based on mode
    display_cols = ["name", "lat", "lon"]
    for optional in ["year", "type", "country", "era", "civilization", "pattern",
                     "energy", "ship_type", "ghost", "incidents", "radius_km",
                     "description"]:
        if optional in filtered.columns:
            display_cols.append(optional)

    display_df = filtered[display_cols].reset_index(drop=True)
    display_df.index = display_df.index + 1
    display_df.index.name = "#"

    st.dataframe(display_df, width="stretch")

    # ══════════════════════════════════════════
    # SECTION 7: CSV Download
    # ══════════════════════════════════════════
    csv_buffer = io.StringIO()
    display_df.to_csv(csv_buffer, index=True)
    csv_bytes = csv_buffer.getvalue().encode("utf-8")

    safe_name = mode.lower().replace(" ", "_").replace("&", "and").replace("/", "_")

    st.download_button(
        label=f"Download {mode} CSV ({total_locations} locations)",
        data=csv_bytes,
        file_name=f"terrascout_paranormal_{safe_name}.csv",
        mime="text/csv",
        key=f"paranormal_download_{safe_name}",
    )

    # ══════════════════════════════════════════
    # SECTION 8: Notable Highlights
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Notable Highlights")

    # Pick 5 random highlights (or first 5) for display
    highlights = filtered.sample(n=min(5, len(filtered)), random_state=42)

    for _, row in highlights.iterrows():
        name = escape(str(row.get("name", "Unknown")))
        desc = escape(str(row.get("description", "")))
        lat = row.get("lat", 0)
        lon = row.get("lon", 0)

        extra_bits = []
        for key in ["year", "type", "country", "era", "pattern", "energy",
                     "ship_type", "ghost", "civilization"]:
            val = row.get(key)
            if val is not None and str(val) != "nan":
                extra_bits.append(f"{key.replace('_', ' ').title()}: {escape(str(val))}")
        extra_line = " | ".join(extra_bits) if extra_bits else ""

        st.markdown(
            f'<div style="background:{SURFACE_COLOR};border-left:3px solid {mode_color};'
            f'padding:12px 16px;border-radius:6px;margin-bottom:10px;">'
            f'<b style="color:{mode_color};font-size:15px;">{name}</b>'
            f'<span style="color:{MUTED_COLOR};font-size:12px;margin-left:12px;">'
            f'{lat:.4f}, {lon:.4f}</span><br>'
            f'{f"<span style=color:{TEXT_COLOR};font-size:12px;>{extra_line}</span><br>" if extra_line else ""}'
            f'<span style="color:{TEXT_COLOR};font-size:13px;">{desc}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════
    # SECTION 9: Fun Facts / Disclaimer
    # ══════════════════════════════════════════
    st.markdown("---")

    fun_facts = {
        "UFO Sighting Hotspots": [
            "The US government officially acknowledged UAP (Unidentified Aerial Phenomena) investigations in 2017.",
            "The 1952 Washington D.C. UFO incident prompted the largest Pentagon press conference since WWII.",
            "AARO (All-domain Anomaly Resolution Office) was established in 2022 to investigate UAPs.",
            "The Nimitz Tic-Tac encounter in 2004 was confirmed authentic by the US Navy in 2020.",
        ],
        "Haunted Places": [
            "Eastern State Penitentiary housed Al Capone, who claimed to be haunted by a ghost he called 'Jimmy'.",
            "The Tower of London has over 900 years of ghost sightings documented in official records.",
            "Bhangarh Fort in India is legally declared haunted by the Archaeological Survey of India.",
            "The Brown Lady of Raynham Hall photograph from 1936 remains one of the most studied ghost images.",
        ],
        "Bermuda Triangle & Anomalies": [
            "The Bermuda Triangle was first named by Vincent Gaddis in a 1964 magazine article.",
            "Flight 19 - five TBM Avenger bombers vanished in the Triangle on December 5, 1945.",
            "The South Atlantic Anomaly causes more satellite failures than any other region on Earth.",
            "Ivan Sanderson identified 12 'vile vortex' points equally spaced around the globe.",
        ],
        "Crop Circle Locations": [
            "Over 10,000 crop circles have been reported worldwide, with 90% appearing in southern England.",
            "The largest crop circle ever recorded was the 2001 Milk Hill formation with 409 circles.",
            "Wiltshire county in England accounts for roughly half of all crop circles ever documented.",
            "The Chilbolton 'Arecibo Reply' formation appeared near a radio telescope in 2001.",
        ],
        "Ley Lines & Energy Vortices": [
            "Alfred Watkins coined the term 'ley line' in 1921 after noticing alignments on a map.",
            "The St. Michael ley line runs from Skellig Michael in Ireland to Mount Carmel in Israel.",
            "Sedona, Arizona has four officially recognized energy vortex sites.",
            "The Great Pyramid of Giza sits at the exact center of Earth's land mass.",
        ],
        "Ghost Ship Sightings": [
            "The Mary Celeste was found in perfect sailing condition with months of food and water aboard.",
            "The SS Baychimo was spotted drifting unmanned in the Arctic for 38 years after abandonment.",
            "The Flying Dutchman legend dates back to the 17th century Dutch Golden Age of sailing.",
            "The Kaz II catamaran was found in 2007 with its engine running, laptop open, and meals prepared.",
        ],
        "Secret Bases & Underground Facilities": [
            "Area 51 was not officially acknowledged by the US government until 2013.",
            "The Denver International Airport has 327,000 sq ft of underground tunnels and facilities.",
            "Cheyenne Mountain can withstand a 30-megaton nuclear blast detonated at the surface.",
            "Russia's Yamantau Mountain facility is estimated to be the size of the Washington D.C. metro area.",
        ],
        "Ancient Astronaut Sites": [
            "The Antikythera Mechanism is a 2,100-year-old analog computer that predicted eclipses.",
            "Puma Punku's H-blocks are cut with precision of 1/50th of an inch - before iron tools existed.",
            "Gobekli Tepe predates Stonehenge by 6,000 years and was deliberately buried 10,000 years ago.",
            "The Nazca Lines can only be fully appreciated from the air - yet were made 2,500 years ago.",
        ],
        "Spontaneous Combustion & Strange Events": [
            "The Tunguska Event of 1908 released energy equivalent to 10-15 megatons of TNT.",
            "The Dyatlov Pass incident was officially reclassified as an avalanche in 2020 - not everyone agrees.",
            "The 1518 Dancing Plague of Strasbourg lasted over a month and affected around 400 people.",
            "The Wow! Signal was exactly 72 seconds - the maximum a Big Ear telescope sweep could record.",
        ],
        "Portals & Dimensional Anomalies": [
            "Skinwalker Ranch was purchased by the Pentagon's AAWSAP program for $22 million in research.",
            "The Aramu Muru 'stargate' in Peru has a T-shaped niche that locals say opens on certain nights.",
            "Hoia Baciu Forest in Romania has a perfectly circular clearing where no vegetation grows.",
            "The US government's AATIP program spent $22M studying anomalous phenomena from 2007-2012.",
        ],
    }

    facts = fun_facts.get(mode, ["No additional facts available for this category."])

    st.markdown(
        f'<div style="background:{SURFACE_COLOR};padding:16px;border-radius:8px;'
        f'border:1px solid {mode_color}30;">'
        f'<b style="color:{mode_color};font-size:14px;">Did You Know?</b><br>'
        + "<br>".join(
            [f'<span style="color:{TEXT_COLOR};font-size:13px;line-height:1.8;">'
             f'&#8226; {escape(fact)}</span>' for fact in facts]
        )
        + '</div>',
        unsafe_allow_html=True,
    )

    # Disclaimer
    st.markdown(
        f'<div style="background:{BG_COLOR};padding:12px;border-radius:6px;'
        f'margin-top:16px;border:1px solid {MUTED_COLOR}40;">'
        f'<span style="color:{MUTED_COLOR};font-size:12px;">'
        f'<b>Disclaimer:</b> This module is for entertainment and educational purposes. '
        f'Locations and descriptions are compiled from historical reports, folklore, '
        f'and popular accounts. Inclusion on this map does not constitute verification '
        f'of any paranormal claims. Coordinates are approximate. Always respect private '
        f'property and local regulations when visiting any location.</span></div>',
        unsafe_allow_html=True,
    )
