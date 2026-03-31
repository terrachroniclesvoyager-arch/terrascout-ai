# -*- coding: utf-8 -*-
"""
Fjords, Coasts & Shorelines module for TerraScout AI.
Explores fjords, sea cliffs, beaches, coral reefs, tidal phenomena,
coastal erosion, sea stacks, mangroves, bioluminescent bays, and
coastal megacities using curated datasets and free public APIs.
All data sources are free and require no API keys.
"""

import io
import logging
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

logger = logging.getLogger(__name__)

# ===================================================================
# MAP MODE DEFINITIONS
# ===================================================================
MAP_MODES = [
    "World's Greatest Fjords",
    "Dramatic Sea Cliffs",
    "World's Best Beaches",
    "Coral Reefs",
    "Tidal Phenomena",
    "Coastal Erosion Hotspots",
    "Sea Stacks & Arches",
    "Mangrove Forests",
    "Bioluminescent Bays",
    "Coastal Megacities",
]

MODE_DESCRIPTIONS = {
    "World's Greatest Fjords": (
        "Fjords are narrow, deep inlets carved by glaciers over millions of years. "
        "Norway alone has over 1,000 fjords, with Sognefjorden reaching 204 km in length "
        "and 1,308 m in depth. Other spectacular fjords are found in New Zealand, Chile, "
        "Greenland, Canada, and Alaska \u2014 each with towering cliffs and pristine waters."
    ),
    "Dramatic Sea Cliffs": (
        "Sea cliffs are vertical or near-vertical rock faces formed by wave erosion and "
        "weathering. The Cliffs of Moher in Ireland, Preikestolen in Norway, and the "
        "chalk cliffs of Etretat in France draw millions of visitors. Some cliffs exceed "
        "1,000 m in height, rivaling the world's tallest waterfalls."
    ),
    "World's Best Beaches": (
        "From the powder-white sands of Whitehaven Beach to the shipwreck cove of Navagio, "
        "the world's finest beaches are ranked by sand quality, water clarity, scenery, and "
        "visitor experience. Baia do Sancho in Brazil has been voted best beach on Earth "
        "multiple times by TripAdvisor Travellers' Choice."
    ),
    "Coral Reefs": (
        "Coral reefs cover less than 0.1% of the ocean floor but support 25% of all marine "
        "species. The Great Barrier Reef spans 2,300 km; the Mesoamerican Reef is the "
        "largest in the Atlantic. Climate change and ocean acidification threaten reef "
        "health globally, with 14% of reefs lost between 2009 and 2018."
    ),
    "Tidal Phenomena": (
        "Tides are driven by the gravitational pull of the Moon and Sun. The Bay of Fundy "
        "in Canada experiences the world's highest tides at over 16 m. Tidal bores \u2014 "
        "surging waves that travel up rivers \u2014 occur on the Severn, Amazon, and Qiantang. "
        "Mont Saint-Michel is famous for its dramatic tidal island effect."
    ),
    "Coastal Erosion Hotspots": (
        "Coastal erosion reshapes shorelines worldwide, threatening communities and "
        "ecosystems. The Holderness coast in England loses up to 2 m per year; Bangladesh's "
        "deltaic coast erodes even faster. Sea-level rise and stronger storms accelerate "
        "erosion, putting 40% of the global population at risk."
    ),
    "Sea Stacks & Arches": (
        "Sea stacks are isolated columns of rock left standing after coastal erosion removes "
        "softer surrounding material. Famous examples include the Twelve Apostles in Australia, "
        "the Old Man of Hoy in Scotland, and Malta's Azure Window (which collapsed in 2017). "
        "These formations are ephemeral \u2014 constantly shaped and destroyed by the sea."
    ),
    "Mangrove Forests": (
        "Mangroves are salt-tolerant trees that thrive in tropical and subtropical coastlines. "
        "The Sundarbans \u2014 shared between Bangladesh and India \u2014 is the world's largest mangrove "
        "forest at 10,000 sq km. Mangroves sequester 3-5x more carbon than terrestrial "
        "forests and protect coasts from storm surges and tsunamis."
    ),
    "Bioluminescent Bays": (
        "Bioluminescence in coastal waters is caused by dinoflagellates (Pyrodinium bahamense) "
        "and other microorganisms that emit light when disturbed. Mosquito Bay in Vieques, "
        "Puerto Rico, is the brightest bioluminescent bay on Earth. Other sites include "
        "Toyama Bay in Japan, Vaadhoo Island in the Maldives, and Luminous Lagoon in Jamaica."
    ),
    "Coastal Megacities": (
        "Over 800 million people live in coastal zones less than 10 m above sea level. "
        "Cities like Jakarta, Shanghai, Mumbai, and Miami face increasing flood risk from "
        "sea-level rise, land subsidence, and intensifying storms. Jakarta is sinking up to "
        "25 cm per year, prompting Indonesia to relocate its capital."
    ),
}

MODE_COLORS = {
    "World's Greatest Fjords": "#06b6d4",
    "Dramatic Sea Cliffs": "#ef4444",
    "World's Best Beaches": "#f59e0b",
    "Coral Reefs": "#ec4899",
    "Tidal Phenomena": "#3b82f6",
    "Coastal Erosion Hotspots": "#f97316",
    "Sea Stacks & Arches": "#a855f7",
    "Mangrove Forests": "#10b981",
    "Bioluminescent Bays": "#14b8a6",
    "Coastal Megacities": "#8b5cf6",
}

# ===================================================================
# CURATED DATASETS
# ===================================================================

GREATEST_FJORDS = [
    {"name": "Sognefjorden", "country": "Norway", "region": "Vestland",
     "length_km": 204, "depth_m": 1308, "lat": 61.100, "lon": 6.500,
     "notes": "Longest and deepest fjord in Norway, UNESCO branch Naeroyfjord"},
    {"name": "Hardangerfjorden", "country": "Norway", "region": "Vestland",
     "length_km": 179, "depth_m": 891, "lat": 60.230, "lon": 6.150,
     "notes": "Second longest in Norway, famous fruit orchards and waterfalls"},
    {"name": "Geirangerfjorden", "country": "Norway", "region": "More og Romsdal",
     "length_km": 15, "depth_m": 260, "lat": 62.100, "lon": 7.090,
     "notes": "UNESCO World Heritage Site, Seven Sisters waterfall"},
    {"name": "Naeroyfjord", "country": "Norway", "region": "Vestland",
     "length_km": 17, "depth_m": 500, "lat": 60.890, "lon": 6.870,
     "notes": "UNESCO site, narrowest point only 250 m wide"},
    {"name": "Lysefjorden", "country": "Norway", "region": "Rogaland",
     "length_km": 42, "depth_m": 497, "lat": 59.010, "lon": 6.230,
     "notes": "Home to Preikestolen (Pulpit Rock) and Kjeragbolten"},
    {"name": "Nordfjord", "country": "Norway", "region": "Vestland",
     "length_km": 106, "depth_m": 565, "lat": 61.900, "lon": 5.800,
     "notes": "Gateway to Jostedalsbreen glacier, scenic skiing"},
    {"name": "Trondheimsfjorden", "country": "Norway", "region": "Trondelag",
     "length_km": 126, "depth_m": 617, "lat": 63.600, "lon": 10.200,
     "notes": "Third longest Norwegian fjord, city of Trondheim at head"},
    {"name": "Milford Sound", "country": "New Zealand", "region": "Fiordland",
     "length_km": 15, "depth_m": 291, "lat": -44.640, "lon": 167.900,
     "notes": "Eighth wonder of the world, Mitre Peak rises 1,692 m"},
    {"name": "Doubtful Sound", "country": "New Zealand", "region": "Fiordland",
     "length_km": 40, "depth_m": 421, "lat": -45.300, "lon": 166.980,
     "notes": "Deepest NZ fjord, bottlenose dolphins, remote wilderness"},
    {"name": "Dusky Sound", "country": "New Zealand", "region": "Fiordland",
     "length_km": 44, "depth_m": 364, "lat": -45.750, "lon": 166.500,
     "notes": "Captain Cook's 1773 anchorage, pristine wilderness"},
    {"name": "Scoresby Sund", "country": "Greenland", "region": "East Greenland",
     "length_km": 350, "depth_m": 1450, "lat": 70.480, "lon": -25.000,
     "notes": "Longest fjord system in the world, massive icebergs"},
    {"name": "Ilulissat Icefjord", "country": "Greenland", "region": "West Greenland",
     "length_km": 55, "depth_m": 1000, "lat": 69.120, "lon": -51.100,
     "notes": "UNESCO site, Sermeq Kujalleq glacier calves huge bergs"},
    {"name": "Saguenay Fjord", "country": "Canada", "region": "Quebec",
     "length_km": 105, "depth_m": 275, "lat": 48.350, "lon": -70.000,
     "notes": "Only major fjord in eastern Canada, beluga whale habitat"},
    {"name": "Western Brook Pond", "country": "Canada", "region": "Newfoundland",
     "length_km": 16, "depth_m": 165, "lat": 49.780, "lon": -57.850,
     "notes": "Landlocked fjord in Gros Morne NP, UNESCO site"},
    {"name": "Kenai Fjords", "country": "USA", "region": "Alaska",
     "length_km": 35, "depth_m": 300, "lat": 59.850, "lon": -149.800,
     "notes": "Exit Glacier, humpback whales, tidewater glaciers"},
    {"name": "Tracy Arm Fjord", "country": "USA", "region": "Alaska",
     "length_km": 48, "depth_m": 370, "lat": 57.850, "lon": -133.600,
     "notes": "Twin Sawyer glaciers, popular cruise destination"},
    {"name": "Canal de las Montanas", "country": "Chile", "region": "Magallanes",
     "length_km": 60, "depth_m": 1288, "lat": -51.600, "lon": -74.000,
     "notes": "Deep Patagonian channel, remote glacial scenery"},
    {"name": "Ultima Esperanza", "country": "Chile", "region": "Magallanes",
     "length_km": 50, "depth_m": 400, "lat": -51.700, "lon": -72.500,
     "notes": "Last Hope Sound near Torres del Paine, Balmaceda glacier"},
    {"name": "Fiordo Pia", "country": "Chile", "region": "Tierra del Fuego",
     "length_km": 25, "depth_m": 350, "lat": -54.800, "lon": -69.600,
     "notes": "Stunning Pia glacier calving into the fjord, Beagle Channel"},
    {"name": "Kotor Bay", "country": "Montenegro", "region": "Boka Kotorska",
     "length_km": 28, "depth_m": 60, "lat": 42.430, "lon": 18.570,
     "notes": "Southernmost European fjord-like bay, UNESCO old town"},
    {"name": "Misty Fjords", "country": "USA", "region": "Alaska",
     "length_km": 35, "depth_m": 300, "lat": 56.100, "lon": -130.500,
     "notes": "Tongass National Forest, 900 m granite cliffs"},
    {"name": "Aurlandsfjorden", "country": "Norway", "region": "Vestland",
     "length_km": 29, "depth_m": 962, "lat": 60.900, "lon": 7.100,
     "notes": "Branch of Sognefjord, Stegastein viewpoint, Flam Railway"},
    {"name": "Romsdalsfjorden", "country": "Norway", "region": "More og Romsdal",
     "length_km": 88, "depth_m": 550, "lat": 62.550, "lon": 7.200,
     "notes": "Trollveggen (Troll Wall) nearby, dramatic alpine fjord"},
    {"name": "Prins Christian Sund", "country": "Greenland", "region": "South Greenland",
     "length_km": 100, "depth_m": 500, "lat": 60.050, "lon": -43.800,
     "notes": "Narrow passage through southern Greenland, icebergs"},
    {"name": "Howe Sound", "country": "Canada", "region": "British Columbia",
     "length_km": 42, "depth_m": 285, "lat": 49.460, "lon": -123.280,
     "notes": "Near Vancouver, Sea-to-Sky Highway, glass sponge reefs"},
    {"name": "Eyjafjordur", "country": "Iceland", "region": "Nordurland",
     "length_km": 60, "depth_m": 176, "lat": 65.900, "lon": -18.100,
     "notes": "Longest fjord in Iceland, Akureyri city, whale watching"},
    {"name": "Trollfjorden", "country": "Norway", "region": "Nordland",
     "length_km": 2, "depth_m": 60, "lat": 68.500, "lon": 15.400,
     "notes": "Iconic narrow Lofoten fjord, sheer 1,100 m walls"},
    {"name": "Lusterfjorden", "country": "Norway", "region": "Vestland",
     "length_km": 42, "depth_m": 684, "lat": 61.400, "lon": 7.300,
     "notes": "Innermost arm of Sognefjord, Urnes stave church UNESCO"},
    {"name": "Passage Canal", "country": "USA", "region": "Alaska",
     "length_km": 18, "depth_m": 250, "lat": 60.790, "lon": -148.680,
     "notes": "Gateway to Prince William Sound, Whittier access"},
    {"name": "Beagle Channel", "country": "Argentina/Chile", "region": "Tierra del Fuego",
     "length_km": 240, "depth_m": 300, "lat": -54.880, "lon": -68.300,
     "notes": "Named after Darwin's HMS Beagle, Ushuaia at southern end"},
]

SEA_CLIFFS = [
    {"name": "Kalaupapa Cliffs", "country": "USA", "region": "Hawaii",
     "height_m": 1010, "lat": 21.190, "lon": -156.980,
     "notes": "Highest sea cliffs in the world, Molokai island"},
    {"name": "Hornelen", "country": "Norway", "region": "Vestland",
     "height_m": 860, "lat": 61.940, "lon": 5.170,
     "notes": "Highest sea cliff in Europe, Bremanger island"},
    {"name": "Cabo Girao", "country": "Portugal", "region": "Madeira",
     "height_m": 580, "lat": 32.650, "lon": -17.010,
     "notes": "One of highest in Europe, glass skywalk platform"},
    {"name": "Preikestolen", "country": "Norway", "region": "Rogaland",
     "height_m": 604, "lat": 58.986, "lon": 6.190,
     "notes": "Pulpit Rock over Lysefjorden, 300,000 visitors/year"},
    {"name": "Cliffs of Moher", "country": "Ireland", "region": "Clare",
     "height_m": 214, "lat": 52.970, "lon": -9.430,
     "notes": "Ireland's most-visited natural attraction, 1.5M visitors/yr"},
    {"name": "Etretat Cliffs", "country": "France", "region": "Normandy",
     "height_m": 90, "lat": 49.710, "lon": 0.200,
     "notes": "Iconic white chalk arches painted by Monet, needle rock"},
    {"name": "White Cliffs of Dover", "country": "UK", "region": "Kent",
     "height_m": 110, "lat": 51.130, "lon": 1.340,
     "notes": "Symbol of Britain, chalk cliffs facing the English Channel"},
    {"name": "Na Pali Coast", "country": "USA", "region": "Hawaii",
     "height_m": 1200, "lat": 22.170, "lon": -159.650,
     "notes": "Kauai's dramatic fluted ridges, accessible only by sea/air"},
    {"name": "Slieve League", "country": "Ireland", "region": "Donegal",
     "height_m": 601, "lat": 54.630, "lon": -8.680,
     "notes": "Among highest sea cliffs in Europe, pilgrim path on top"},
    {"name": "Los Gigantes", "country": "Spain", "region": "Tenerife",
     "height_m": 600, "lat": 28.240, "lon": -16.840,
     "notes": "Giant's Cliffs on Tenerife, whale watching below"},
    {"name": "Trango Towers", "country": "Pakistan", "region": "Gilgit-Baltistan",
     "height_m": 1340, "lat": 35.760, "lon": 76.090,
     "notes": "Near-vertical granite, tallest cliff faces on Earth"},
    {"name": "Mitre Peak", "country": "New Zealand", "region": "Fiordland",
     "height_m": 1692, "lat": -44.640, "lon": 167.870,
     "notes": "Rises directly from Milford Sound, iconic NZ peak"},
    {"name": "North Cape", "country": "Norway", "region": "Troms og Finnmark",
     "height_m": 307, "lat": 71.170, "lon": 25.780,
     "notes": "Northernmost point of mainland Europe, midnight sun"},
    {"name": "Cape Enniberg", "country": "Faroe Islands", "region": "Vidoy",
     "height_m": 754, "lat": 62.160, "lon": -6.580,
     "notes": "Highest sea cliff in the Faroes, seabird colonies"},
    {"name": "Croaghaun", "country": "Ireland", "region": "Achill Island",
     "height_m": 688, "lat": 53.970, "lon": -10.170,
     "notes": "Highest sea cliff in Ireland and insular Europe"},
    {"name": "Dingli Cliffs", "country": "Malta", "region": "Dingli",
     "height_m": 253, "lat": 35.850, "lon": 14.380,
     "notes": "Highest point in Malta, Mediterranean panorama"},
    {"name": "Cape Pillar", "country": "Australia", "region": "Tasmania",
     "height_m": 300, "lat": -43.210, "lon": 148.010,
     "notes": "Tallest dolerite sea cliffs in the Southern Hemisphere"},
    {"name": "Bempton Cliffs", "country": "UK", "region": "Yorkshire",
     "height_m": 120, "lat": 54.140, "lon": -0.170,
     "notes": "Biggest seabird colony in England, 500,000 birds"},
    {"name": "Latrabjarg", "country": "Iceland", "region": "Westfjords",
     "height_m": 441, "lat": 65.500, "lon": -24.080,
     "notes": "Largest bird cliff in Europe at 14 km, puffin colony"},
    {"name": "Bungle Bungles", "country": "Australia", "region": "Western Australia",
     "height_m": 250, "lat": -17.440, "lon": 128.370,
     "notes": "Beehive sandstone formations, Purnululu NP UNESCO"},
]

BEST_BEACHES = [
    {"name": "Baia do Sancho", "country": "Brazil", "region": "Fernando de Noronha",
     "rating": 9.8, "lat": -3.854, "lon": -32.444,
     "notes": "Multiple-time #1 beach globally, turquoise volcanic cove"},
    {"name": "Whitehaven Beach", "country": "Australia", "region": "Whitsundays",
     "rating": 9.7, "lat": -20.280, "lon": 149.040,
     "notes": "7 km of pure white silica sand, swirling Hill Inlet"},
    {"name": "Navagio Beach", "country": "Greece", "region": "Zakynthos",
     "rating": 9.6, "lat": 37.860, "lon": 20.625,
     "notes": "Shipwreck Beach, limestone cliffs, accessible only by boat"},
    {"name": "Anse Source d'Argent", "country": "Seychelles", "region": "La Digue",
     "rating": 9.6, "lat": -4.370, "lon": 55.830,
     "notes": "Iconic granite boulders, shallow turquoise water"},
    {"name": "Grace Bay Beach", "country": "Turks and Caicos", "region": "Providenciales",
     "rating": 9.5, "lat": 21.800, "lon": -72.230,
     "notes": "Pristine 5 km crescent of white sand, barrier reef"},
    {"name": "Playa Paraiso", "country": "Cuba", "region": "Cayo Largo",
     "rating": 9.4, "lat": 21.580, "lon": -81.560,
     "notes": "Untouched paradise beach, warm shallow waters"},
    {"name": "Matira Beach", "country": "French Polynesia", "region": "Bora Bora",
     "rating": 9.4, "lat": -16.540, "lon": -151.730,
     "notes": "Only public beach on Bora Bora, sunset views of Mt Otemanu"},
    {"name": "Pink Sands Beach", "country": "Bahamas", "region": "Harbour Island",
     "rating": 9.3, "lat": 25.510, "lon": -76.630,
     "notes": "Blush-pink sand from foraminifera, 5 km long"},
    {"name": "Trunk Bay", "country": "US Virgin Islands", "region": "St. John",
     "rating": 9.3, "lat": 18.350, "lon": -64.770,
     "notes": "Underwater snorkeling trail, crystal-clear water"},
    {"name": "Maya Bay", "country": "Thailand", "region": "Phi Phi Islands",
     "rating": 9.2, "lat": 7.678, "lon": 98.765,
     "notes": "The Beach movie location, closed 2018-2021 for recovery"},
    {"name": "Camps Bay", "country": "South Africa", "region": "Cape Town",
     "rating": 9.1, "lat": -33.950, "lon": 18.380,
     "notes": "Twelve Apostles mountain backdrop, Atlantic sunset"},
    {"name": "Seven Mile Beach", "country": "Cayman Islands", "region": "Grand Cayman",
     "rating": 9.1, "lat": 19.350, "lon": -81.380,
     "notes": "Coral sand crescent, calm Caribbean waters"},
    {"name": "Flamenco Beach", "country": "Puerto Rico", "region": "Culebra",
     "rating": 9.1, "lat": 18.330, "lon": -65.320,
     "notes": "Horseshoe bay with white sand, abandoned tank on beach"},
    {"name": "Copacabana", "country": "Brazil", "region": "Rio de Janeiro",
     "rating": 9.0, "lat": -22.970, "lon": -43.180,
     "notes": "Iconic 4 km urban crescent, mosaic promenade"},
    {"name": "Bondi Beach", "country": "Australia", "region": "Sydney",
     "rating": 9.0, "lat": -33.890, "lon": 151.270,
     "notes": "Australia's most famous beach, surf culture, coastal walk"},
    {"name": "Zlatni Rat", "country": "Croatia", "region": "Brac",
     "rating": 9.0, "lat": 43.255, "lon": 16.635,
     "notes": "Golden Horn spit that changes shape with wind and waves"},
    {"name": "Tulum Beach", "country": "Mexico", "region": "Quintana Roo",
     "rating": 8.9, "lat": 20.210, "lon": -87.430,
     "notes": "Mayan ruins above turquoise Caribbean, bohemian vibe"},
    {"name": "Lanikai Beach", "country": "USA", "region": "Hawaii",
     "rating": 8.9, "lat": 21.390, "lon": -157.710,
     "notes": "Mokulua twin islands, soft fine sand, calm lagoon"},
    {"name": "Elafonissi Beach", "country": "Greece", "region": "Crete",
     "rating": 8.9, "lat": 35.270, "lon": 23.540,
     "notes": "Pink-tinged sand, shallow lagoon, nature reserve"},
    {"name": "Rabbit Beach", "country": "Italy", "region": "Lampedusa",
     "rating": 8.8, "lat": 35.510, "lon": 12.550,
     "notes": "Isola dei Conigli, loggerhead turtle nesting site"},
    {"name": "Baia dos Porcos", "country": "Brazil", "region": "Fernando de Noronha",
     "rating": 8.8, "lat": -3.860, "lon": -32.430,
     "notes": "Natural rock pools, twin peaks view, volcanic setting"},
    {"name": "Praia da Marinha", "country": "Portugal", "region": "Algarve",
     "rating": 8.8, "lat": 37.090, "lon": -8.410,
     "notes": "Limestone arches and sea stacks, crystal water"},
    {"name": "Cable Beach", "country": "Australia", "region": "Broome",
     "rating": 8.7, "lat": -17.960, "lon": 122.210,
     "notes": "22 km of white sand, camel rides at sunset"},
    {"name": "Ipanema Beach", "country": "Brazil", "region": "Rio de Janeiro",
     "rating": 8.7, "lat": -22.980, "lon": -43.200,
     "notes": "Girl from Ipanema, Dois Irmaos peaks backdrop"},
    {"name": "Plage de Palombaggia", "country": "France", "region": "Corsica",
     "rating": 8.7, "lat": 41.560, "lon": 9.290,
     "notes": "Red porphyry rocks, Corsican pine trees, turquoise sea"},
    {"name": "Railay Beach", "country": "Thailand", "region": "Krabi",
     "rating": 8.7, "lat": 8.010, "lon": 98.840,
     "notes": "Limestone karst towers, rock climbing, boat access only"},
    {"name": "Praia de Benagil", "country": "Portugal", "region": "Algarve",
     "rating": 8.6, "lat": 37.090, "lon": -8.430,
     "notes": "Famous sea cave with skylight, kayak excursions"},
    {"name": "El Nido Beaches", "country": "Philippines", "region": "Palawan",
     "rating": 8.6, "lat": 11.180, "lon": 119.410,
     "notes": "Bacuit archipelago hidden lagoons, limestone cliffs"},
    {"name": "Anse Lazio", "country": "Seychelles", "region": "Praslin",
     "rating": 8.6, "lat": -4.290, "lon": 55.700,
     "notes": "Granite boulders, takamaka trees, top-rated Indian Ocean"},
    {"name": "Playa del Carmen", "country": "Mexico", "region": "Quintana Roo",
     "rating": 8.5, "lat": 20.630, "lon": -87.080,
     "notes": "Riviera Maya hub, 5th Avenue, Cozumel ferry"},
    {"name": "Myrtos Beach", "country": "Greece", "region": "Kefalonia",
     "rating": 8.5, "lat": 38.340, "lon": 20.530,
     "notes": "White pebble crescent, dramatic limestone backdrop"},
    {"name": "Clearwater Beach", "country": "USA", "region": "Florida",
     "rating": 8.5, "lat": 27.980, "lon": -82.830,
     "notes": "Consistent #1 US beach, gentle Gulf of Mexico waters"},
    {"name": "Anse Intendance", "country": "Seychelles", "region": "Mahe",
     "rating": 8.4, "lat": -4.770, "lon": 55.470,
     "notes": "Wild surf, sea turtles, palm-fringed granite bay"},
    {"name": "Praia do Espelho", "country": "Brazil", "region": "Bahia",
     "rating": 8.4, "lat": -16.810, "lon": -39.120,
     "notes": "Mirror Beach with reef pools and coloured cliffs"},
    {"name": "Siesta Key Beach", "country": "USA", "region": "Florida",
     "rating": 8.4, "lat": 27.270, "lon": -82.560,
     "notes": "99% pure quartz crystal sand, cool underfoot"},
    {"name": "Cala Goloritze", "country": "Italy", "region": "Sardinia",
     "rating": 8.4, "lat": 40.100, "lon": 9.660,
     "notes": "148 m limestone pinnacle, UNESCO natural monument"},
    {"name": "Long Beach", "country": "Canada", "region": "Tofino",
     "rating": 8.3, "lat": 49.020, "lon": -125.770,
     "notes": "Pacific Rim NP, storm watching, old-growth rainforest"},
    {"name": "Reynisfjara", "country": "Iceland", "region": "Vik",
     "rating": 8.3, "lat": 63.400, "lon": -19.050,
     "notes": "Black volcanic sand, basalt columns, powerful waves"},
    {"name": "Cayo de Agua", "country": "Venezuela", "region": "Los Roques",
     "rating": 8.3, "lat": 11.830, "lon": -66.830,
     "notes": "Sandbar connecting two islands, Caribbean national park"},
    {"name": "Radhanagar Beach", "country": "India", "region": "Havelock Island",
     "rating": 8.3, "lat": 11.980, "lon": 92.940,
     "notes": "Best beach in Asia multiple times, Andaman Islands"},
    {"name": "Turquoise Bay", "country": "Australia", "region": "Western Australia",
     "rating": 8.2, "lat": -23.130, "lon": 113.830,
     "notes": "Ningaloo Reef, drift snorkeling, whale sharks"},
    {"name": "Horseshoe Bay", "country": "Bermuda", "region": "Southampton",
     "rating": 8.2, "lat": 32.250, "lon": -64.840,
     "notes": "Pink sand crescent, limestone formations, snorkeling"},
    {"name": "Playa de Ses Illetes", "country": "Spain", "region": "Formentera",
     "rating": 8.2, "lat": 38.760, "lon": 1.440,
     "notes": "Crystal-clear Balearic waters, posidonia meadows"},
    {"name": "Bavaro Beach", "country": "Dominican Republic", "region": "Punta Cana",
     "rating": 8.1, "lat": 18.710, "lon": -68.420,
     "notes": "30 km of coconut palms, all-inclusive resorts"},
    {"name": "Wineglass Bay", "country": "Australia", "region": "Tasmania",
     "rating": 8.1, "lat": -42.130, "lon": 148.300,
     "notes": "Perfect crescent, Freycinet NP, granite peaks"},
    {"name": "Balos Beach", "country": "Greece", "region": "Crete",
     "rating": 8.1, "lat": 35.580, "lon": 23.590,
     "notes": "Lagoon with pink-white sand, Gramvousa fortress"},
    {"name": "Pansy Island", "country": "Mozambique", "region": "Bazaruto",
     "rating": 8.0, "lat": -21.610, "lon": 35.490,
     "notes": "Sandbank island, dugongs, Indian Ocean paradise"},
    {"name": "Playa Norte", "country": "Mexico", "region": "Isla Mujeres",
     "rating": 8.0, "lat": 21.250, "lon": -86.740,
     "notes": "Calm shallow water, sunset views, off Cancun coast"},
    {"name": "Ngapali Beach", "country": "Myanmar", "region": "Rakhine",
     "rating": 8.0, "lat": 18.380, "lon": 94.340,
     "notes": "Undeveloped Bay of Bengal gem, fishing village charm"},
    {"name": "Hyams Beach", "country": "Australia", "region": "New South Wales",
     "rating": 8.0, "lat": -35.100, "lon": 150.690,
     "notes": "Reputedly whitest sand in the world, Jervis Bay"},
]

CORAL_REEFS = [
    {"name": "Great Barrier Reef", "country": "Australia", "region": "Queensland",
     "area_km2": 344400, "health": "Threatened", "lat": -18.290, "lon": 147.700,
     "notes": "Largest reef system, 2,900 individual reefs, UNESCO"},
    {"name": "Mesoamerican Barrier Reef", "country": "Belize/Mexico/Honduras/Guatemala",
     "region": "Caribbean", "area_km2": 1000, "health": "Vulnerable",
     "lat": 17.000, "lon": -87.530,
     "notes": "Second largest barrier reef, Belize Blue Hole, 500+ fish species"},
    {"name": "Red Sea Coral Reef", "country": "Egypt/Saudi Arabia/Sudan",
     "region": "Red Sea", "area_km2": 17400, "health": "Good",
     "lat": 24.500, "lon": 36.000,
     "notes": "Heat-resistant corals, 300+ species, incredible visibility"},
    {"name": "New Caledonia Barrier Reef", "country": "France",
     "region": "New Caledonia", "area_km2": 24000, "health": "Moderate",
     "lat": -22.250, "lon": 166.500,
     "notes": "Second longest double barrier reef, UNESCO site"},
    {"name": "Maldives Coral Reefs", "country": "Maldives", "region": "Indian Ocean",
     "area_km2": 8920, "health": "Recovering", "lat": 3.200, "lon": 73.000,
     "notes": "26 atolls, 187 species of coral, mass bleaching events"},
    {"name": "Raja Ampat Reefs", "country": "Indonesia", "region": "West Papua",
     "area_km2": 40000, "health": "Good", "lat": -1.000, "lon": 130.500,
     "notes": "Highest marine biodiversity on Earth, 1,500+ fish species"},
    {"name": "Tubbataha Reefs", "country": "Philippines", "region": "Sulu Sea",
     "area_km2": 970, "health": "Good", "lat": 8.940, "lon": 119.920,
     "notes": "UNESCO site, pristine atoll, 600 fish species, nesting turtles"},
    {"name": "Apo Reef", "country": "Philippines", "region": "Mindoro",
     "area_km2": 34, "health": "Moderate", "lat": 12.660, "lon": 120.430,
     "notes": "Second largest contiguous reef in world, natural park"},
    {"name": "Andros Barrier Reef", "country": "Bahamas", "region": "Andros Island",
     "area_km2": 5600, "health": "Moderate", "lat": 24.200, "lon": -77.900,
     "notes": "Third largest barrier reef, blue holes, deep tongue of ocean"},
    {"name": "Ningaloo Reef", "country": "Australia", "region": "Western Australia",
     "area_km2": 5000, "health": "Good", "lat": -23.130, "lon": 113.830,
     "notes": "Largest fringing reef in world, whale sharks, 300 km long"},
    {"name": "Coral Triangle", "country": "Indonesia/Philippines/Malaysia",
     "region": "SE Asia", "area_km2": 5700000, "health": "Vulnerable",
     "lat": 0.000, "lon": 125.000,
     "notes": "Global center of marine biodiversity, 600 reef-building coral species"},
    {"name": "Aldabra Atoll", "country": "Seychelles", "region": "Indian Ocean",
     "area_km2": 155, "health": "Good", "lat": -9.420, "lon": 46.350,
     "notes": "UNESCO site, giant tortoises, pristine raised coral atoll"},
    {"name": "Chagos Archipelago", "country": "BIOT", "region": "Indian Ocean",
     "area_km2": 60000, "health": "Excellent", "lat": -6.500, "lon": 71.500,
     "notes": "Largest no-take marine reserve, pristine reefs"},
    {"name": "Hawaiian Coral Reefs", "country": "USA", "region": "Hawaii",
     "area_km2": 3400, "health": "Moderate", "lat": 21.300, "lon": -157.800,
     "notes": "25% endemic species, Papahanaumokuakea Marine Monument"},
    {"name": "Belize Barrier Reef", "country": "Belize", "region": "Caribbean",
     "area_km2": 960, "health": "Vulnerable", "lat": 17.330, "lon": -87.530,
     "notes": "Great Blue Hole, UNESCO site, 100 coral and 500 fish species"},
    {"name": "Florida Keys Reef", "country": "USA", "region": "Florida",
     "area_km2": 3800, "health": "Critical", "lat": 24.580, "lon": -81.800,
     "notes": "Only living barrier reef in continental US, severe bleaching"},
    {"name": "Scott Reef", "country": "Australia", "region": "Western Australia",
     "area_km2": 320, "health": "Recovering", "lat": -14.070, "lon": 121.800,
     "notes": "Isolated oceanic reef, 200+ coral species, remote"},
    {"name": "Palau Reef System", "country": "Palau", "region": "Micronesia",
     "area_km2": 1400, "health": "Good", "lat": 7.350, "lon": 134.470,
     "notes": "Rock Islands UNESCO, Jellyfish Lake, 700 coral species"},
    {"name": "Wakatobi Reefs", "country": "Indonesia", "region": "Sulawesi",
     "area_km2": 19000, "health": "Good", "lat": -5.480, "lon": 123.600,
     "notes": "National park, 750 coral species, dive paradise"},
    {"name": "Lighthouse Reef", "country": "Belize", "region": "Caribbean",
     "area_km2": 80, "health": "Moderate", "lat": 17.340, "lon": -87.480,
     "notes": "Home of the Great Blue Hole, Half Moon Caye"},
]

TIDAL_PHENOMENA = [
    {"name": "Bay of Fundy", "country": "Canada",
     "region": "Nova Scotia/New Brunswick", "tidal_range_m": 16.3,
     "type": "Extreme Tide", "lat": 45.300, "lon": -64.900,
     "notes": "Highest tides on Earth, 160 billion tonnes of water per cycle"},
    {"name": "Mont Saint-Michel", "country": "France", "region": "Normandy",
     "tidal_range_m": 14.5, "type": "Tidal Island", "lat": 48.636, "lon": -1.511,
     "notes": "UNESCO island abbey, tide recedes 15 km, fastest tides in Europe"},
    {"name": "Severn Bore", "country": "UK", "region": "Gloucestershire",
     "tidal_range_m": 14.0, "type": "Tidal Bore", "lat": 51.740, "lon": -2.430,
     "notes": "One of highest bores in world, surfed for 12+ km, 2 m wave"},
    {"name": "Qiantang River Bore", "country": "China", "region": "Zhejiang",
     "tidal_range_m": 8.9, "type": "Tidal Bore", "lat": 30.350, "lon": 120.700,
     "notes": "Silver Dragon bore, up to 9 m high wall of water, annual festival"},
    {"name": "Pororoca", "country": "Brazil", "region": "Amazon",
     "tidal_range_m": 4.0, "type": "Tidal Bore", "lat": -0.500, "lon": -49.500,
     "notes": "Amazon tidal bore, waves up to 4 m, surfed for 37 minutes"},
    {"name": "Ungava Bay", "country": "Canada", "region": "Quebec",
     "tidal_range_m": 17.0, "type": "Extreme Tide", "lat": 59.500, "lon": -67.500,
     "notes": "Rivals Bay of Fundy for highest tides, remote Arctic bay"},
    {"name": "King Sound", "country": "Australia", "region": "Western Australia",
     "tidal_range_m": 11.8, "type": "Extreme Tide", "lat": -16.500, "lon": 123.600,
     "notes": "Highest tides in Australia, horizontal waterfall effect"},
    {"name": "Gulf of Khambhat", "country": "India", "region": "Gujarat",
     "tidal_range_m": 11.0, "type": "Extreme Tide", "lat": 21.500, "lon": 72.200,
     "notes": "Highest tides in Indian subcontinent, proposed tidal power"},
    {"name": "Anchorage", "country": "USA", "region": "Alaska",
     "tidal_range_m": 10.3, "type": "Extreme Tide", "lat": 61.200, "lon": -149.900,
     "notes": "Turnagain Arm bore, highest tides in US, mudflat danger"},
    {"name": "Bristol Channel", "country": "UK", "region": "Wales/England",
     "tidal_range_m": 14.5, "type": "Extreme Tide", "lat": 51.300, "lon": -3.500,
     "notes": "Second highest tides globally, proposed Severn Barrage"},
    {"name": "Normandy Coast", "country": "France", "region": "Normandy",
     "tidal_range_m": 13.5, "type": "Extreme Tide", "lat": 48.870, "lon": -1.600,
     "notes": "Critical factor in D-Day planning, oyster beds exposed"},
    {"name": "Horizontal Falls", "country": "Australia", "region": "Kimberley",
     "tidal_range_m": 11.0, "type": "Tidal Waterfall", "lat": -16.380, "lon": 124.450,
     "notes": "Horizontal waterfalls through narrow gorges, boat adventures"},
    {"name": "Morecambe Bay", "country": "UK", "region": "Lancashire",
     "tidal_range_m": 10.5, "type": "Tidal Flats", "lat": 54.150, "lon": -2.850,
     "notes": "Largest intertidal area in UK, guided quicksand walks"},
    {"name": "Chandipur Beach", "country": "India", "region": "Odisha",
     "tidal_range_m": 5.0, "type": "Vanishing Sea", "lat": 21.460, "lon": 87.020,
     "notes": "Sea recedes 5 km during low tide, walk on seabed"},
    {"name": "Maelstrom of Saltstraumen", "country": "Norway", "region": "Nordland",
     "tidal_range_m": 3.0, "type": "Tidal Whirlpool", "lat": 67.230, "lon": 14.620,
     "notes": "Strongest tidal current in world, 400M cubic m per tide"},
    {"name": "Old Sow Whirlpool", "country": "Canada/USA",
     "region": "New Brunswick/Maine", "tidal_range_m": 7.0,
     "type": "Tidal Whirlpool", "lat": 44.960, "lon": -66.920,
     "notes": "Largest whirlpool in Western Hemisphere, 75 m diameter"},
    {"name": "Corryvreckan", "country": "UK", "region": "Scotland",
     "tidal_range_m": 4.5, "type": "Tidal Whirlpool", "lat": 56.150, "lon": -5.720,
     "notes": "Third largest whirlpool on Earth, roar heard 16 km away"},
    {"name": "Ganges Delta Tides", "country": "Bangladesh/India",
     "region": "Sundarbans", "tidal_range_m": 6.0, "type": "Tidal Forest",
     "lat": 21.950, "lon": 89.180,
     "notes": "Largest tidal mangrove forest, daily flooding of 10,000 km2"},
    {"name": "Naruto Whirlpools", "country": "Japan", "region": "Tokushima",
     "tidal_range_m": 1.5, "type": "Tidal Whirlpool", "lat": 34.230, "lon": 134.650,
     "notes": "Up to 20 m diameter vortices in Naruto Strait, bridge viewing"},
    {"name": "Pentland Firth", "country": "UK", "region": "Scotland",
     "tidal_range_m": 5.0, "type": "Tidal Current", "lat": 58.680, "lon": -3.100,
     "notes": "Strongest tidal race in British Isles, tidal energy potential"},
]

COASTAL_EROSION = [
    {"name": "Holderness Coast", "country": "UK", "region": "Yorkshire",
     "erosion_rate_m_yr": 2.0, "lat": 53.800, "lon": 0.100,
     "notes": "Fastest eroding coast in Europe, villages lost to sea"},
    {"name": "Norfolk Cliffs", "country": "UK", "region": "Norfolk",
     "erosion_rate_m_yr": 1.5, "lat": 52.900, "lon": 1.300,
     "notes": "Happisburgh village falling into sea, soft glacial till"},
    {"name": "Ganges-Brahmaputra Delta", "country": "Bangladesh",
     "region": "Sundarbans", "erosion_rate_m_yr": 5.0,
     "lat": 22.000, "lon": 89.500,
     "notes": "Up to 200 m/year in places, millions displaced, rising seas"},
    {"name": "Chatham Islands", "country": "USA", "region": "Massachusetts",
     "erosion_rate_m_yr": 1.5, "lat": 41.670, "lon": -69.960,
     "notes": "Barrier beach breakthroughs, lighthouse relocated"},
    {"name": "Vashon Island Bluffs", "country": "USA", "region": "Washington",
     "erosion_rate_m_yr": 0.3, "lat": 47.400, "lon": -122.470,
     "notes": "Puget Sound bluff recession, landslide hazard"},
    {"name": "Waikiki Beach", "country": "USA", "region": "Hawaii",
     "erosion_rate_m_yr": 0.3, "lat": 21.280, "lon": -157.830,
     "notes": "Chronic erosion managed by sand replenishment, tourism threat"},
    {"name": "Benin Coastline", "country": "Benin", "region": "Gulf of Guinea",
     "erosion_rate_m_yr": 4.0, "lat": 6.350, "lon": 2.430,
     "notes": "Rapid retreat from sand mining and dam impacts upstream"},
    {"name": "Shishmaref", "country": "USA", "region": "Alaska",
     "erosion_rate_m_yr": 3.0, "lat": 66.250, "lon": -166.070,
     "notes": "Inuit village voted to relocate, permafrost thaw, storm surge"},
    {"name": "Isle de Jean Charles", "country": "USA", "region": "Louisiana",
     "erosion_rate_m_yr": 4.5, "lat": 29.370, "lon": -90.610,
     "notes": "First US climate refugees, 98% of land lost since 1955"},
    {"name": "Sagar Island", "country": "India", "region": "West Bengal",
     "erosion_rate_m_yr": 3.5, "lat": 21.650, "lon": 88.060,
     "notes": "Ganges delta island losing 5 km2/year, 200,000+ affected"},
    {"name": "Medmerry", "country": "UK", "region": "West Sussex",
     "erosion_rate_m_yr": 1.0, "lat": 50.740, "lon": -0.820,
     "notes": "Managed realignment site, largest in Europe, 2013 breach"},
    {"name": "Dakhla Peninsula", "country": "Morocco", "region": "Western Sahara",
     "erosion_rate_m_yr": 1.5, "lat": 23.720, "lon": -15.930,
     "notes": "Desert peninsula narrowing, Atlantic wave action"},
    {"name": "Tuvalu", "country": "Tuvalu", "region": "Pacific Ocean",
     "erosion_rate_m_yr": 0.5, "lat": -8.520, "lon": 179.200,
     "notes": "Entire nation at risk of submersion, max elevation 4.6 m"},
    {"name": "Pacifica Cliffs", "country": "USA", "region": "California",
     "erosion_rate_m_yr": 0.5, "lat": 37.630, "lon": -122.490,
     "notes": "Apartments condemned and demolished, cliff collapse"},
    {"name": "Hemsby Dunes", "country": "UK", "region": "Norfolk",
     "erosion_rate_m_yr": 2.5, "lat": 52.700, "lon": 1.700,
     "notes": "Homes falling off sand dunes, 2018 storms destroyed houses"},
    {"name": "Kiribati", "country": "Kiribati", "region": "Pacific Ocean",
     "erosion_rate_m_yr": 0.8, "lat": 1.870, "lon": -157.360,
     "notes": "Atolls disappearing, government bought land in Fiji"},
    {"name": "Portsea Back Beach", "country": "Australia", "region": "Victoria",
     "erosion_rate_m_yr": 0.4, "lat": -38.330, "lon": 144.720,
     "notes": "Cliff collapses, beach narrowing, infrastructure at risk"},
    {"name": "Cotonou Coast", "country": "Benin", "region": "Atlantique",
     "erosion_rate_m_yr": 6.0, "lat": 6.370, "lon": 2.400,
     "notes": "Fastest urban coastal erosion in West Africa, 40 m/yr spots"},
    {"name": "Mekong Delta", "country": "Vietnam", "region": "Southern Vietnam",
     "erosion_rate_m_yr": 3.0, "lat": 9.800, "lon": 106.400,
     "notes": "500 hectares lost per year, sand mining and dam impacts"},
    {"name": "Jakarta Coastline", "country": "Indonesia", "region": "Java",
     "erosion_rate_m_yr": 2.0, "lat": -6.100, "lon": 106.850,
     "notes": "Sinking 25 cm/year from groundwater extraction, sea wall projects"},
]

SEA_STACKS = [
    {"name": "Twelve Apostles", "country": "Australia", "region": "Victoria",
     "height_m": 45, "status": "Active Erosion", "lat": -38.665, "lon": 143.104,
     "notes": "Only 8 remain, limestone, Great Ocean Road"},
    {"name": "Old Man of Hoy", "country": "UK", "region": "Orkney",
     "height_m": 137, "status": "Stable", "lat": 58.880, "lon": -3.430,
     "notes": "Red sandstone sea stack, first climbed 1966 on live TV"},
    {"name": "Azure Window (Collapsed)", "country": "Malta", "region": "Gozo",
     "height_m": 0, "status": "Collapsed 2017", "lat": 36.053, "lon": 14.190,
     "notes": "Iconic limestone arch collapsed 8 March 2017, GoT filming"},
    {"name": "Kicker Rock", "country": "Ecuador", "region": "Galapagos",
     "height_m": 148, "status": "Stable", "lat": -0.770, "lon": -89.520,
     "notes": "Leon Dormido, split volcanic tuff, hammerhead sharks"},
    {"name": "Durdle Door", "country": "UK", "region": "Dorset",
     "height_m": 30, "status": "Active Erosion", "lat": 50.620, "lon": -2.270,
     "notes": "Natural limestone arch, Jurassic Coast UNESCO"},
    {"name": "Risin og Kellingin", "country": "Faroe Islands", "region": "Eidi",
     "height_m": 71, "status": "Active Erosion", "lat": 62.130, "lon": -6.980,
     "notes": "Giant and the Witch, basalt sea stacks, petrified trolls legend"},
    {"name": "Ball's Pyramid", "country": "Australia", "region": "Lord Howe",
     "height_m": 562, "status": "Stable", "lat": -31.750, "lon": 159.250,
     "notes": "Tallest volcanic sea stack in the world, Lord Howe stick insect"},
    {"name": "Ko Tapu", "country": "Thailand", "region": "Phang Nga Bay",
     "height_m": 20, "status": "Active Erosion", "lat": 8.275, "lon": 98.500,
     "notes": "James Bond Island, limestone needle, Man with the Golden Gun"},
    {"name": "Langdranan", "country": "Sweden", "region": "Gotland",
     "height_m": 12, "status": "Stable", "lat": 57.500, "lon": 18.500,
     "notes": "Limestone raukar formations, over 100 sea stacks on Faro"},
    {"name": "Dun Briste", "country": "Ireland", "region": "Mayo",
     "height_m": 45, "status": "Stable", "lat": 54.320, "lon": -9.410,
     "notes": "Detached from Downpatrick Head in 1393, ruined buildings on top"},
    {"name": "Perce Rock", "country": "Canada", "region": "Quebec",
     "height_m": 88, "status": "Active Erosion", "lat": 48.523, "lon": -64.213,
     "notes": "Iconic pierced limestone arch, gannet colony nearby"},
    {"name": "Cathedral Cove Arch", "country": "New Zealand", "region": "Coromandel",
     "height_m": 20, "status": "Active Erosion", "lat": -36.830, "lon": 175.790,
     "notes": "Natural arch between two beaches, Narnia filming location"},
    {"name": "Porte d'Aval", "country": "France", "region": "Etretat",
     "height_m": 70, "status": "Stable", "lat": 49.710, "lon": 0.195,
     "notes": "Chalk arch with Needle rock, painted by Monet and Courbet"},
    {"name": "Hvitserkur", "country": "Iceland", "region": "Hunaping",
     "height_m": 15, "status": "Reinforced", "lat": 65.610, "lon": -20.640,
     "notes": "Basalt stack resembling a dragon, concrete reinforced base"},
    {"name": "Manneporte", "country": "France", "region": "Etretat",
     "height_m": 90, "status": "Stable", "lat": 49.710, "lon": 0.210,
     "notes": "Largest of Etretat's three arches, Grande Manneporte"},
    {"name": "London Bridge", "country": "Australia", "region": "Victoria",
     "height_m": 25, "status": "Partially Collapsed", "lat": -38.630, "lon": 143.080,
     "notes": "Double arch collapsed 1990 stranding tourists, now single stack"},
    {"name": "Green Bridge of Wales", "country": "UK", "region": "Pembrokeshire",
     "height_m": 24, "status": "Active Erosion", "lat": 51.630, "lon": -5.030,
     "notes": "Natural limestone arch on Castlemartin coast, MOD range"},
    {"name": "Bako Sea Stacks", "country": "Malaysia", "region": "Sarawak",
     "height_m": 30, "status": "Active Erosion", "lat": 1.720, "lon": 110.470,
     "notes": "Sandstone stacks in Bako National Park, proboscis monkeys"},
    {"name": "The Needles", "country": "UK", "region": "Isle of Wight",
     "height_m": 30, "status": "Active Erosion", "lat": 50.660, "lon": -1.590,
     "notes": "Three chalk stacks with lighthouse, colored sand cliffs"},
    {"name": "Haystack Rock", "country": "USA", "region": "Oregon",
     "height_m": 72, "status": "Stable", "lat": 45.880, "lon": -123.970,
     "notes": "Cannon Beach icon, tufted puffins, tidepool marine garden"},
]

MANGROVE_FORESTS = [
    {"name": "Sundarbans", "country": "Bangladesh/India", "region": "Bengal Delta",
     "area_km2": 10000, "lat": 21.950, "lon": 89.180,
     "notes": "Largest mangrove forest, Bengal tigers, UNESCO site"},
    {"name": "Everglades Mangroves", "country": "USA", "region": "Florida",
     "area_km2": 6000, "lat": 25.350, "lon": -81.000,
     "notes": "Largest mangrove wilderness in Western Hemisphere, manatees"},
    {"name": "Matang Mangroves", "country": "Malaysia", "region": "Perak",
     "area_km2": 404, "lat": 4.850, "lon": 100.550,
     "notes": "Best managed mangrove in world, 100+ years sustainable forestry"},
    {"name": "Pichavaram Mangroves", "country": "India", "region": "Tamil Nadu",
     "area_km2": 11, "lat": 11.430, "lon": 79.780,
     "notes": "Second largest mangrove in India, kayak ecotourism"},
    {"name": "Can Gio Mangroves", "country": "Vietnam", "region": "Ho Chi Minh",
     "area_km2": 758, "lat": 10.410, "lon": 106.890,
     "notes": "UNESCO biosphere, replanted after Agent Orange defoliation"},
    {"name": "Rufiji Delta", "country": "Tanzania", "region": "Pwani",
     "area_km2": 530, "lat": -7.800, "lon": 39.400,
     "notes": "Largest mangrove in East Africa, hippos, marine turtles"},
    {"name": "Gulf of Carpentaria", "country": "Australia", "region": "Queensland/NT",
     "area_km2": 3500, "lat": -14.500, "lon": 139.000,
     "notes": "Largest mangrove extent in Australia, saltwater crocodiles"},
    {"name": "Galapagos Mangroves", "country": "Ecuador", "region": "Galapagos",
     "area_km2": 15, "lat": -0.750, "lon": -90.300,
     "notes": "Critical habitat for Galapagos penguins and marine iguanas"},
    {"name": "Niger Delta Mangroves", "country": "Nigeria", "region": "Niger Delta",
     "area_km2": 10000, "lat": 5.000, "lon": 6.000,
     "notes": "Largest in Africa, severely impacted by oil spills"},
    {"name": "Baja California Mangroves", "country": "Mexico",
     "region": "Baja California Sur", "area_km2": 250,
     "lat": 24.750, "lon": -110.350,
     "notes": "Northernmost mangroves in eastern Pacific, whale nursery"},
    {"name": "Cayos Cochinos", "country": "Honduras", "region": "Bay Islands",
     "area_km2": 489, "lat": 15.950, "lon": -86.470,
     "notes": "Marine biological reserve, Garifuna communities, reef protection"},
    {"name": "Mangrove Bay", "country": "Bermuda", "region": "Sandys",
     "area_km2": 0.5, "lat": 32.310, "lon": -64.870,
     "notes": "Most northerly mangrove in the Atlantic, protected site"},
    {"name": "Andaman Mangroves", "country": "India", "region": "Andaman Islands",
     "area_km2": 966, "lat": 12.000, "lon": 92.800,
     "notes": "Rich biodiversity, saltwater crocodiles, dugongs"},
    {"name": "Cienaga Grande", "country": "Colombia", "region": "Magdalena",
     "area_km2": 4280, "lat": 10.700, "lon": -74.500,
     "notes": "Largest lagoon-mangrove system in Colombia, Ramsar site"},
    {"name": "Bhitarkanika Mangroves", "country": "India", "region": "Odisha",
     "area_km2": 650, "lat": 20.700, "lon": 87.000,
     "notes": "Second largest in India, largest saltwater crocodile population"},
    {"name": "Lamu Archipelago", "country": "Kenya", "region": "Coast",
     "area_km2": 320, "lat": -2.200, "lon": 40.900,
     "notes": "UNESCO World Heritage, dense mangrove channels, dhow culture"},
    {"name": "Moreton Bay", "country": "Australia", "region": "Queensland",
     "area_km2": 185, "lat": -27.300, "lon": 153.200,
     "notes": "Ramsar wetland near Brisbane, dugongs, migratory shorebirds"},
    {"name": "Mekong Delta Mangroves", "country": "Vietnam", "region": "Mekong Delta",
     "area_km2": 550, "lat": 9.500, "lon": 106.200,
     "notes": "Vital flood buffer, aquaculture-mangrove systems"},
    {"name": "Mangroves of Zanzibar", "country": "Tanzania", "region": "Zanzibar",
     "area_km2": 180, "lat": -6.200, "lon": 39.300,
     "notes": "Jozani Forest surroundings, red colobus monkey habitat"},
    {"name": "Sine-Saloum Delta", "country": "Senegal", "region": "Fatick",
     "area_km2": 1800, "lat": 13.800, "lon": -16.500,
     "notes": "UNESCO biosphere, shell mounds, 200+ bird species"},
]

BIOLUMINESCENT_BAYS = [
    {"name": "Mosquito Bay", "country": "Puerto Rico", "region": "Vieques",
     "brightness": "Extreme", "organism": "Pyrodinium bahamense",
     "lat": 18.095, "lon": -65.450,
     "notes": "Brightest bioluminescent bay on Earth, Guinness record"},
    {"name": "Laguna Grande", "country": "Puerto Rico", "region": "Fajardo",
     "brightness": "High", "organism": "Pyrodinium bahamense",
     "lat": 18.370, "lon": -65.640,
     "notes": "Kayak tours through mangrove channels, accessible from San Juan"},
    {"name": "La Parguera", "country": "Puerto Rico", "region": "Lajas",
     "brightness": "Moderate", "organism": "Pyrodinium bahamense",
     "lat": 17.960, "lon": -67.050,
     "notes": "Phosphorescent Bay, diminished by light pollution but visible"},
    {"name": "Luminous Lagoon", "country": "Jamaica", "region": "Falmouth",
     "brightness": "High", "organism": "Pyrodinium bahamense",
     "lat": 18.470, "lon": -77.640,
     "notes": "Glistening Waters, swim and glow, freshwater-saltwater interface"},
    {"name": "Toyama Bay", "country": "Japan", "region": "Toyama",
     "brightness": "Seasonal", "organism": "Watasenia scintillans",
     "lat": 36.800, "lon": 137.200,
     "notes": "Firefly squid blue glow March-June, rise from deep water"},
    {"name": "Vaadhoo Island", "country": "Maldives", "region": "Raa Atoll",
     "brightness": "High", "organism": "Dinoflagellates",
     "lat": 5.640, "lon": 72.970,
     "notes": "Sea of Stars, bioluminescent phytoplankton wash ashore"},
    {"name": "Halong Bay", "country": "Vietnam", "region": "Quang Ninh",
     "brightness": "Low", "organism": "Noctiluca scintillans",
     "lat": 20.900, "lon": 107.100,
     "notes": "Occasional bioluminescence around limestone karsts"},
    {"name": "Jervis Bay", "country": "Australia", "region": "New South Wales",
     "brightness": "Moderate", "organism": "Noctiluca scintillans",
     "lat": -35.050, "lon": 150.750,
     "notes": "Blue glow events May-August, phosphorescence on Hyams Beach"},
    {"name": "Sam Mun Tsai", "country": "China", "region": "Hong Kong",
     "brightness": "Low", "organism": "Noctiluca scintillans",
     "lat": 22.450, "lon": 114.210,
     "notes": "Blue tears phenomenon, related to red tide organisms"},
    {"name": "Matsu Islands", "country": "Taiwan", "region": "Lienchiang",
     "brightness": "High", "organism": "Noctiluca scintillans",
     "lat": 26.160, "lon": 119.950,
     "notes": "Blue Tears phenomenon April-September, sea sparkle"},
    {"name": "Mudhdhoo Island", "country": "Maldives", "region": "Baa Atoll",
     "brightness": "Moderate", "organism": "Dinoflagellates",
     "lat": 5.250, "lon": 73.000,
     "notes": "Baa Atoll UNESCO biosphere, glowing plankton in lagoons"},
    {"name": "Holbox Island", "country": "Mexico", "region": "Quintana Roo",
     "brightness": "Moderate", "organism": "Dinoflagellates",
     "lat": 21.520, "lon": -87.380,
     "notes": "Summer bioluminescence, whale shark aggregation, car-free"},
    {"name": "Krabi", "country": "Thailand", "region": "Krabi",
     "brightness": "Low", "organism": "Dinoflagellates",
     "lat": 8.090, "lon": 98.900,
     "notes": "Occasional glow on Railay and Ao Nang beaches"},
    {"name": "Aberavon Beach", "country": "UK", "region": "Wales",
     "brightness": "Rare", "organism": "Noctiluca scintillans",
     "lat": 51.600, "lon": -3.830,
     "notes": "Rare bioluminescence events, cold-water plankton, documented 2020"},
    {"name": "Torrey Pines Beach", "country": "USA", "region": "California",
     "brightness": "Seasonal", "organism": "Lingulodinium polyedra",
     "lat": 32.920, "lon": -117.260,
     "notes": "Red tide by day, blue glow by night, spring events"},
    {"name": "Manasquan Beach", "country": "USA", "region": "New Jersey",
     "brightness": "Rare", "organism": "Noctiluca scintillans",
     "lat": 40.100, "lon": -74.040,
     "notes": "Occasional summer bioluminescence, warm Gulf Stream intrusions"},
    {"name": "Gippsland Lakes", "country": "Australia", "region": "Victoria",
     "brightness": "Seasonal", "organism": "Noctiluca scintillans",
     "lat": -37.860, "lon": 147.800,
     "notes": "2008 and 2012 spectacular blooms, blue glow in inland waterway"},
    {"name": "Ton Sai Bay", "country": "Thailand", "region": "Phi Phi",
     "brightness": "Low", "organism": "Dinoflagellates",
     "lat": 7.740, "lon": 98.770,
     "notes": "Occasional plankton glow, best during new moon"},
    {"name": "Navarre Beach", "country": "USA", "region": "Florida",
     "brightness": "Rare", "organism": "Pyrodinium bahamense",
     "lat": 30.380, "lon": -86.860,
     "notes": "Gulf Coast bioluminescence, comb jellies also contribute glow"},
    {"name": "Nosy Iranja", "country": "Madagascar", "region": "Nosy Be",
     "brightness": "Low", "organism": "Dinoflagellates",
     "lat": -13.780, "lon": 47.680,
     "notes": "Remote island bioluminescence, undeveloped, sea turtle nesting"},
]

COASTAL_MEGACITIES = [
    {"name": "Jakarta", "country": "Indonesia", "population_m": 34.0,
     "elevation_m": -2.0, "subsidence_cm_yr": 25.0, "flood_risk": "Extreme",
     "lat": -6.200, "lon": 106.850,
     "notes": "Sinking fastest city, capital relocating to Nusantara, 40% below sea level"},
    {"name": "Shanghai", "country": "China", "population_m": 29.0,
     "elevation_m": 4.0, "subsidence_cm_yr": 1.5, "flood_risk": "Very High",
     "lat": 31.230, "lon": 121.470,
     "notes": "Yangtze Delta, typhoon risk, massive sea wall and sponge city projects"},
    {"name": "Mumbai", "country": "India", "population_m": 21.7,
     "elevation_m": 8.0, "subsidence_cm_yr": 2.0, "flood_risk": "Very High",
     "lat": 19.080, "lon": 72.880,
     "notes": "Monsoon flooding annual, 2005 deluge killed 1,000+, coastal reclamation"},
    {"name": "New York City", "country": "USA", "population_m": 20.1,
     "elevation_m": 10.0, "subsidence_cm_yr": 0.2, "flood_risk": "High",
     "lat": 40.710, "lon": -74.010,
     "notes": "Hurricane Sandy 2012, $19B damage, sea level rising 3.4 mm/yr"},
    {"name": "Miami", "country": "USA", "population_m": 6.2,
     "elevation_m": 2.0, "subsidence_cm_yr": 0.3, "flood_risk": "Extreme",
     "lat": 25.760, "lon": -80.190,
     "notes": "Porous limestone base, king tide flooding, $3.5T property at risk"},
    {"name": "Bangkok", "country": "Thailand", "population_m": 17.0,
     "elevation_m": 1.5, "subsidence_cm_yr": 2.0, "flood_risk": "Extreme",
     "lat": 13.760, "lon": 100.500,
     "notes": "2011 floods cost $45B, built on soft clay, groundwater extraction"},
    {"name": "Tokyo", "country": "Japan", "population_m": 37.4,
     "elevation_m": 5.0, "subsidence_cm_yr": 0.1, "flood_risk": "High",
     "lat": 35.680, "lon": 139.770,
     "notes": "Underground cathedral flood tunnels, typhoon and tsunami risk"},
    {"name": "Dhaka", "country": "Bangladesh", "population_m": 23.0,
     "elevation_m": 4.0, "subsidence_cm_yr": 1.4, "flood_risk": "Extreme",
     "lat": 23.810, "lon": 90.410,
     "notes": "Two-thirds of Bangladesh below 5m, cyclone and monsoon flooding"},
    {"name": "Ho Chi Minh City", "country": "Vietnam", "population_m": 13.0,
     "elevation_m": 0.5, "subsidence_cm_yr": 8.0, "flood_risk": "Extreme",
     "lat": 10.820, "lon": 106.630,
     "notes": "Mekong Delta sinking rapidly, chronic urban flooding"},
    {"name": "Manila", "country": "Philippines", "population_m": 14.0,
     "elevation_m": 1.0, "subsidence_cm_yr": 10.0, "flood_risk": "Extreme",
     "lat": 14.600, "lon": 120.980,
     "notes": "Typhoon Ondoy 2009 80% flooded, severe groundwater-driven subsidence"},
    {"name": "Lagos", "country": "Nigeria", "population_m": 16.0,
     "elevation_m": 2.0, "subsidence_cm_yr": 3.0, "flood_risk": "Very High",
     "lat": 6.450, "lon": 3.400,
     "notes": "Eko Atlantic reclamation, 70% at flood risk, growing 3% per year"},
    {"name": "Kolkata", "country": "India", "population_m": 15.1,
     "elevation_m": 9.0, "subsidence_cm_yr": 1.0, "flood_risk": "High",
     "lat": 22.570, "lon": 88.360,
     "notes": "Hooghly River flooding, Cyclone Amphan 2020 $13B damage"},
    {"name": "Alexandria", "country": "Egypt", "population_m": 5.4,
     "elevation_m": 1.0, "subsidence_cm_yr": 0.5, "flood_risk": "Very High",
     "lat": 31.200, "lon": 29.920,
     "notes": "Nile Delta subsidence, 2 million could be displaced by 2050"},
    {"name": "Guangzhou", "country": "China", "population_m": 14.0,
     "elevation_m": 7.0, "subsidence_cm_yr": 1.0, "flood_risk": "Very High",
     "lat": 23.130, "lon": 113.260,
     "notes": "Pearl River Delta, typhoons, $1.3T assets exposed to flooding"},
    {"name": "Osaka", "country": "Japan", "population_m": 19.3,
     "elevation_m": 3.0, "subsidence_cm_yr": 0.1, "flood_risk": "High",
     "lat": 34.690, "lon": 135.500,
     "notes": "Typhoon Jebi 2018 flooded Kansai Airport, major river delta"},
    {"name": "Houston", "country": "USA", "population_m": 7.1,
     "elevation_m": 15.0, "subsidence_cm_yr": 2.0, "flood_risk": "High",
     "lat": 29.760, "lon": -95.370,
     "notes": "Hurricane Harvey 2017 $125B damage, 60 inches rain in 4 days"},
    {"name": "New Orleans", "country": "USA", "population_m": 1.3,
     "elevation_m": -2.0, "subsidence_cm_yr": 2.5, "flood_risk": "Extreme",
     "lat": 29.950, "lon": -90.070,
     "notes": "Hurricane Katrina 2005, 80% flooded, $14.5B levee system rebuilt"},
    {"name": "London", "country": "UK", "population_m": 9.5,
     "elevation_m": 5.0, "subsidence_cm_yr": 0.1, "flood_risk": "Moderate",
     "lat": 51.510, "lon": -0.120,
     "notes": "Thames Barrier protects 1.4M people, considering TE2100 successor"},
    {"name": "Venice", "country": "Italy", "population_m": 0.3,
     "elevation_m": 1.0, "subsidence_cm_yr": 0.2, "flood_risk": "Extreme",
     "lat": 45.440, "lon": 12.340,
     "notes": "MOSE barrier system, acqua alta flooding, UNESCO threatened"},
    {"name": "Tianjin", "country": "China", "population_m": 14.0,
     "elevation_m": 3.0, "subsidence_cm_yr": 5.0, "flood_risk": "Very High",
     "lat": 39.130, "lon": 117.200,
     "notes": "Bohai Sea coast, rapid subsidence from groundwater extraction"},
]

# ===================================================================
# HELPER - MAP BUILDER (ranked)
# ===================================================================

def _build_ranked_map(data, lat_key, lon_key, label_key,
                      rank_key, popup_fields, color,
                      center=None, zoom=3):
    """Build a folium map with rank-scaled circle markers."""
    if center is None:
        if data:
            center = (
                sum(d[lat_key] for d in data) / len(data),
                sum(d[lon_key] for d in data) / len(data),
            )
        else:
            center = (20, 0)

    m = folium.Map(location=list(center), zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    if data:
        max_val = max(abs(d.get(rank_key, 1)) for d in data) or 1
    else:
        max_val = 1

    for i, item in enumerate(data):
        val = abs(item.get(rank_key, 0))
        radius = max(5, int(4 + 14 * (val / max_val)))

        popup_lines = [f"<b>Rank:</b> #{i + 1}"]
        for label, key in popup_fields.items():
            v = item.get(key, "")
            if v not in (None, "", 0, "0"):
                popup_lines.append(
                    f"<b>{escape(str(label))}:</b> {escape(str(v))}"
                )
        popup_html = (
            '<div style="max-width:260px; font-size:0.85rem;">'
            f'<strong>{escape(str(item.get(label_key, "Unknown")))}</strong>'
            '<br/>' + "<br/>".join(popup_lines) + "</div>"
        )
        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=radius,
            color=color, fill=True, fill_color=color,
            fill_opacity=0.65, weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"#{i+1} {escape(str(item.get(label_key, '')))}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


# ===================================================================
# HELPER - MAP BUILDER (categorical)
# ===================================================================

def _build_categorical_map(data, lat_key, lon_key, label_key,
                           cat_key, popup_fields, color_map,
                           default_color="#06b6d4", center=None, zoom=3):
    """Build map with category-colored markers."""
    if center is None:
        if data:
            center = (
                sum(d[lat_key] for d in data) / len(data),
                sum(d[lon_key] for d in data) / len(data),
            )
        else:
            center = (20, 0)

    m = folium.Map(location=list(center), zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    for i, item in enumerate(data):
        cat = str(item.get(cat_key, ""))
        c = color_map.get(cat, default_color)

        popup_lines = []
        for label, key in popup_fields.items():
            v = item.get(key, "")
            if v not in (None, "", 0, "0"):
                popup_lines.append(
                    f"<b>{escape(str(label))}:</b> {escape(str(v))}"
                )
        popup_html = (
            '<div style="max-width:260px; font-size:0.85rem;">'
            f'<strong>{escape(str(item.get(label_key, "Unknown")))}</strong>'
            '<br/>' + "<br/>".join(popup_lines) + "</div>"
        )
        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=8, color=c, fill=True, fill_color=c,
            fill_opacity=0.65, weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(str(item.get(label_key, ""))),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


# ===================================================================
# HELPER - STATS ROW
# ===================================================================

def _show_stats(metrics):
    """Display metric cards in columns. metrics = [(label, value), ...]"""
    cols = st.columns(min(len(metrics), 5))
    for i, (label, value) in enumerate(metrics):
        cols[i % len(cols)].metric(label, value)


# ===================================================================
# HELPER - CHART (horizontal bar)
# ===================================================================

def _bar_chart(labels, values, color, xlabel, title=""):
    """Draw a dark-themed horizontal bar chart."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, max(3, 0.35 * len(labels))))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    y_pos = range(len(labels))
    ax.barh(y_pos, values, color=color, alpha=0.85,
            edgecolor=color, linewidth=0.5)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels([str(lb)[:30] for lb in labels],
                       color="#e8ecf4", fontsize=9)
    ax.set_xlabel(xlabel, color="#e8ecf4", fontsize=10)
    if title:
        ax.set_title(title, color="#e8ecf4", fontsize=11, pad=8)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ===================================================================
# HELPER - DOWNLOAD
# ===================================================================

def _download_section(df, filename, label, key):
    """Expander with dataframe and CSV download."""
    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label, data=csv_buf.getvalue(),
        file_name=filename, mime="text/csv", key=key,
    )


# ===================================================================
# MODE RENDERERS
# ===================================================================

def _render_fjords():
    """Mode 1: World's Greatest Fjords."""
    data = sorted(GREATEST_FJORDS, key=lambda x: x["depth_m"], reverse=True)
    _show_stats([
        ("Fjords Listed", len(data)),
        ("Deepest", f"{data[0]['depth_m']:,} m"),
        ("Longest", f"{max(d['length_km'] for d in data)} km"),
        ("Countries", len(set(d["country"] for d in data))),
    ])
    st.markdown("---")
    st.markdown("#### World Fjords Map")
    m = _build_ranked_map(
        data, "lat", "lon", "name", "depth_m",
        popup_fields={"Depth": "depth_m", "Length": "length_km",
                       "Country": "country", "Region": "region",
                       "Notes": "notes"},
        color="#06b6d4", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top], [d["depth_m"] for d in top],
        "#06b6d4", "Maximum Depth (m)", "Deepest Fjords in the World",
    )
    df = pd.DataFrame(data)[
        ["name", "country", "region", "length_km", "depth_m",
         "lat", "lon", "notes"]
    ]
    df = df.sort_values("depth_m", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "greatest_fjords.csv",
                      f"Download {len(df)} Fjords (CSV)", "dl_fjords")


def _render_sea_cliffs():
    """Mode 2: Dramatic Sea Cliffs."""
    data = sorted(SEA_CLIFFS, key=lambda x: x["height_m"], reverse=True)
    _show_stats([
        ("Cliffs Listed", len(data)),
        ("Tallest", f"{data[0]['height_m']:,} m"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Avg Height", f"{sum(d['height_m'] for d in data) // len(data)} m"),
    ])
    st.markdown("---")
    st.markdown("#### Dramatic Sea Cliffs Map")
    m = _build_ranked_map(
        data, "lat", "lon", "name", "height_m",
        popup_fields={"Height": "height_m", "Country": "country",
                       "Region": "region", "Notes": "notes"},
        color="#ef4444", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top], [d["height_m"] for d in top],
        "#ef4444", "Height (meters)", "Tallest Sea Cliffs",
    )
    df = pd.DataFrame(data)[
        ["name", "country", "region", "height_m", "lat", "lon", "notes"]
    ]
    df = df.sort_values("height_m", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "sea_cliffs.csv",
                      f"Download {len(df)} Sea Cliffs (CSV)", "dl_cliffs")


def _render_beaches():
    """Mode 3: World's Best Beaches."""
    data = sorted(BEST_BEACHES, key=lambda x: x["rating"], reverse=True)
    _show_stats([
        ("Beaches Listed", len(data)),
        ("Top Rated", data[0]["name"]),
        ("Countries", len(set(d["country"] for d in data))),
        ("Avg Rating", f"{sum(d['rating'] for d in data)/len(data):.1f}/10"),
    ])
    st.markdown("---")
    st.markdown("#### World's Best Beaches Map")
    m = _build_ranked_map(
        data, "lat", "lon", "name", "rating",
        popup_fields={"Rating": "rating", "Country": "country",
                       "Region": "region", "Notes": "notes"},
        color="#f59e0b", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    top = data[:20]
    _bar_chart(
        [d["name"] for d in top], [d["rating"] for d in top],
        "#f59e0b", "Rating (/10)", "Top 20 Beaches by Rating",
    )
    df = pd.DataFrame(data)[
        ["name", "country", "region", "rating", "lat", "lon", "notes"]
    ]
    df = df.sort_values("rating", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "best_beaches.csv",
                      f"Download {len(df)} Beaches (CSV)", "dl_beaches")


def _render_coral_reefs():
    """Mode 4: Coral Reefs."""
    data = sorted(CORAL_REEFS, key=lambda x: x["area_km2"], reverse=True)
    health_counts = {}
    for d in data:
        h = d["health"]
        health_counts[h] = health_counts.get(h, 0) + 1
    _show_stats([
        ("Reef Systems", len(data)),
        ("Largest", f"{data[0]['area_km2']:,} km2"),
        ("Good Health", health_counts.get("Good", 0)
         + health_counts.get("Excellent", 0)),
        ("Threatened", health_counts.get("Critical", 0)
         + health_counts.get("Vulnerable", 0)
         + health_counts.get("Threatened", 0)),
    ])
    st.markdown("---")
    st.markdown("#### Coral Reefs World Map")
    health_colors = {
        "Excellent": "#10b981", "Good": "#06b6d4",
        "Moderate": "#f59e0b", "Recovering": "#3b82f6",
        "Vulnerable": "#f97316", "Threatened": "#ef4444",
        "Critical": "#dc2626",
    }
    m = _build_categorical_map(
        data, "lat", "lon", "name", "health",
        popup_fields={"Area": "area_km2", "Health": "health",
                       "Country": "country", "Region": "region",
                       "Notes": "notes"},
        color_map=health_colors, default_color="#ec4899", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top], [d["area_km2"] for d in top],
        "#ec4899", "Area (km2)", "Largest Coral Reef Systems",
    )
    df = pd.DataFrame(data)[
        ["name", "country", "region", "area_km2", "health",
         "lat", "lon", "notes"]
    ]
    df = df.sort_values("area_km2", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "coral_reefs.csv",
                      f"Download {len(df)} Coral Reefs (CSV)", "dl_reefs")


def _render_tidal_phenomena():
    """Mode 5: Tidal Phenomena."""
    data = sorted(TIDAL_PHENOMENA,
                  key=lambda x: x["tidal_range_m"], reverse=True)
    type_counts = {}
    for d in data:
        t = d["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    _show_stats([
        ("Sites Listed", len(data)),
        ("Highest Tide", f"{data[0]['tidal_range_m']} m"),
        ("Tidal Bores", type_counts.get("Tidal Bore", 0)),
        ("Whirlpools", type_counts.get("Tidal Whirlpool", 0)),
    ])
    st.markdown("---")
    st.markdown("#### Tidal Phenomena World Map")
    type_colors = {
        "Extreme Tide": "#3b82f6", "Tidal Bore": "#f59e0b",
        "Tidal Whirlpool": "#ef4444", "Tidal Island": "#a855f7",
        "Tidal Waterfall": "#14b8a6", "Tidal Flats": "#06b6d4",
        "Vanishing Sea": "#ec4899", "Tidal Forest": "#10b981",
        "Tidal Current": "#8b5cf6",
    }
    m = _build_categorical_map(
        data, "lat", "lon", "name", "type",
        popup_fields={"Tidal Range": "tidal_range_m", "Type": "type",
                       "Country": "country", "Region": "region",
                       "Notes": "notes"},
        color_map=type_colors, default_color="#3b82f6", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top], [d["tidal_range_m"] for d in top],
        "#3b82f6", "Tidal Range (meters)", "Highest Tidal Ranges",
    )
    df = pd.DataFrame(data)[
        ["name", "country", "region", "tidal_range_m", "type",
         "lat", "lon", "notes"]
    ]
    df = df.sort_values("tidal_range_m", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "tidal_phenomena.csv",
                      f"Download {len(df)} Tidal Sites (CSV)", "dl_tidal")


def _render_coastal_erosion():
    """Mode 6: Coastal Erosion Hotspots."""
    data = sorted(COASTAL_EROSION,
                  key=lambda x: x["erosion_rate_m_yr"], reverse=True)
    _show_stats([
        ("Sites Listed", len(data)),
        ("Fastest Erosion", f"{data[0]['erosion_rate_m_yr']} m/yr"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Avg Rate",
         f"{sum(d['erosion_rate_m_yr'] for d in data)/len(data):.1f} m/yr"),
    ])
    st.markdown("---")
    st.markdown("#### Coastal Erosion Hotspots Map")
    m = _build_ranked_map(
        data, "lat", "lon", "name", "erosion_rate_m_yr",
        popup_fields={"Erosion Rate": "erosion_rate_m_yr",
                       "Country": "country", "Region": "region",
                       "Notes": "notes"},
        color="#f97316", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top], [d["erosion_rate_m_yr"] for d in top],
        "#f97316", "Erosion Rate (m/year)", "Fastest Eroding Coastlines",
    )
    df = pd.DataFrame(data)[
        ["name", "country", "region", "erosion_rate_m_yr",
         "lat", "lon", "notes"]
    ]
    df = df.sort_values("erosion_rate_m_yr", ascending=False
                        ).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "coastal_erosion.csv",
                      f"Download {len(df)} Erosion Sites (CSV)", "dl_erosion")


def _render_sea_stacks():
    """Mode 7: Sea Stacks & Arches."""
    data = sorted(SEA_STACKS, key=lambda x: x["height_m"], reverse=True)
    status_counts = {}
    for d in data:
        s = d["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    _show_stats([
        ("Features Listed", len(data)),
        ("Tallest", f"{data[0]['height_m']} m"),
        ("Active Erosion", status_counts.get("Active Erosion", 0)),
        ("Collapsed", status_counts.get("Collapsed 2017", 0)
         + status_counts.get("Partially Collapsed", 0)),
    ])
    st.markdown("---")
    st.markdown("#### Sea Stacks & Arches Map")
    status_colors = {
        "Stable": "#10b981", "Active Erosion": "#f59e0b",
        "Collapsed 2017": "#ef4444", "Partially Collapsed": "#f97316",
        "Reinforced": "#3b82f6",
    }
    m = _build_categorical_map(
        data, "lat", "lon", "name", "status",
        popup_fields={"Height": "height_m", "Status": "status",
                       "Country": "country", "Region": "region",
                       "Notes": "notes"},
        color_map=status_colors, default_color="#a855f7", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    active = [d for d in data if d["height_m"] > 0][:15]
    _bar_chart(
        [d["name"] for d in active], [d["height_m"] for d in active],
        "#a855f7", "Height (meters)", "Tallest Sea Stacks & Arches",
    )
    df = pd.DataFrame(data)[
        ["name", "country", "region", "height_m", "status",
         "lat", "lon", "notes"]
    ]
    df = df.sort_values("height_m", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "sea_stacks.csv",
                      f"Download {len(df)} Sea Stacks (CSV)", "dl_stacks")


def _render_mangroves():
    """Mode 8: Mangrove Forests."""
    data = sorted(MANGROVE_FORESTS,
                  key=lambda x: x["area_km2"], reverse=True)
    total_area = sum(d["area_km2"] for d in data)
    _show_stats([
        ("Sites Listed", len(data)),
        ("Largest", f"{data[0]['area_km2']:,} km2"),
        ("Countries", len(set(d["country"] for d in data))),
        ("Total Area", f"{total_area:,.0f} km2"),
    ])
    st.markdown("---")
    st.markdown("#### Mangrove Forests World Map")
    m = _build_ranked_map(
        data, "lat", "lon", "name", "area_km2",
        popup_fields={"Area": "area_km2", "Country": "country",
                       "Region": "region", "Notes": "notes"},
        color="#10b981", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top], [d["area_km2"] for d in top],
        "#10b981", "Area (km2)", "Largest Mangrove Forests",
    )
    df = pd.DataFrame(data)[
        ["name", "country", "region", "area_km2", "lat", "lon", "notes"]
    ]
    df = df.sort_values("area_km2", ascending=False).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "mangrove_forests.csv",
                      f"Download {len(df)} Mangroves (CSV)", "dl_mangroves")


def _render_bioluminescent():
    """Mode 9: Bioluminescent Bays."""
    brightness_order = {
        "Extreme": 5, "High": 4, "Moderate": 3,
        "Seasonal": 2, "Low": 1, "Rare": 0,
    }
    data = sorted(BIOLUMINESCENT_BAYS,
                  key=lambda x: brightness_order.get(x["brightness"], 0),
                  reverse=True)
    brightness_counts = {}
    for d in data:
        b = d["brightness"]
        brightness_counts[b] = brightness_counts.get(b, 0) + 1
    _show_stats([
        ("Sites Listed", len(data)),
        ("Brightest", data[0]["name"]),
        ("Extreme/High", brightness_counts.get("Extreme", 0)
         + brightness_counts.get("High", 0)),
        ("Countries", len(set(d["country"] for d in data))),
    ])
    st.markdown("---")
    st.markdown("#### Bioluminescent Bays & Shores Map")
    bright_colors = {
        "Extreme": "#06b6d4", "High": "#14b8a6",
        "Moderate": "#3b82f6", "Seasonal": "#8b5cf6",
        "Low": "#6366f1", "Rare": "#475569",
    }
    m = _build_categorical_map(
        data, "lat", "lon", "name", "brightness",
        popup_fields={"Brightness": "brightness", "Organism": "organism",
                       "Country": "country", "Region": "region",
                       "Notes": "notes"},
        color_map=bright_colors, default_color="#14b8a6", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    st.markdown("##### Brightness Levels")
    bright_labels = ["Extreme", "High", "Moderate", "Seasonal", "Low", "Rare"]
    bright_vals = [brightness_counts.get(b, 0) for b in bright_labels]
    _bar_chart(bright_labels, bright_vals, "#14b8a6",
               "Number of Sites", "Bioluminescent Sites by Brightness")
    df = pd.DataFrame(data)[
        ["name", "country", "region", "brightness", "organism",
         "lat", "lon", "notes"]
    ]
    df.index = range(1, len(df) + 1)
    df.index.name = "Rank"
    _download_section(df.reset_index(), "bioluminescent_bays.csv",
                      f"Download {len(df)} Bioluminescent Sites (CSV)",
                      "dl_biolum")


def _render_coastal_megacities():
    """Mode 10: Coastal Megacities."""
    data = sorted(COASTAL_MEGACITIES,
                  key=lambda x: x["subsidence_cm_yr"], reverse=True)
    extreme_count = sum(1 for d in data if d["flood_risk"] == "Extreme")
    total_pop = sum(d["population_m"] for d in data)
    _show_stats([
        ("Cities Listed", len(data)),
        ("Total Population", f"{total_pop:.0f}M"),
        ("Extreme Risk", extreme_count),
        ("Fastest Sinking", f"{data[0]['subsidence_cm_yr']} cm/yr"),
    ])
    st.markdown("---")
    st.markdown("#### Coastal Megacities Flood Risk Map")
    risk_colors = {
        "Extreme": "#ef4444", "Very High": "#f97316",
        "High": "#f59e0b", "Moderate": "#3b82f6",
    }
    m = _build_categorical_map(
        data, "lat", "lon", "name", "flood_risk",
        popup_fields={"Population": "population_m",
                       "Elevation": "elevation_m",
                       "Subsidence": "subsidence_cm_yr",
                       "Flood Risk": "flood_risk",
                       "Country": "country", "Notes": "notes"},
        color_map=risk_colors, default_color="#8b5cf6", zoom=2,
    )
    components.html(m._repr_html_(), height=500)
    st.markdown("---")
    top = data[:15]
    _bar_chart(
        [d["name"] for d in top], [d["subsidence_cm_yr"] for d in top],
        "#8b5cf6", "Land Subsidence (cm/year)",
        "Fastest Sinking Coastal Cities",
    )
    df = pd.DataFrame(data)[
        ["name", "country", "population_m", "elevation_m",
         "subsidence_cm_yr", "flood_risk", "lat", "lon", "notes"]
    ]
    df = df.sort_values("subsidence_cm_yr", ascending=False
                        ).reset_index(drop=True)
    df.index = df.index + 1
    df.index.name = "Rank"
    _download_section(df.reset_index(), "coastal_megacities.csv",
                      f"Download {len(df)} Coastal Cities (CSV)",
                      "dl_megacities")


# ===================================================================
# MODE DISPATCH
# ===================================================================

_MODE_RENDERERS = {
    "World's Greatest Fjords": _render_fjords,
    "Dramatic Sea Cliffs": _render_sea_cliffs,
    "World's Best Beaches": _render_beaches,
    "Coral Reefs": _render_coral_reefs,
    "Tidal Phenomena": _render_tidal_phenomena,
    "Coastal Erosion Hotspots": _render_coastal_erosion,
    "Sea Stacks & Arches": _render_sea_stacks,
    "Mangrove Forests": _render_mangroves,
    "Bioluminescent Bays": _render_bioluminescent,
    "Coastal Megacities": _render_coastal_megacities,
}


# ===================================================================
# MAIN ENTRY POINT
# ===================================================================

def render_fjord_maps_tab():
    """Render the Fjords, Coasts & Shorelines tab."""
    st.markdown(
        '<div class="tab-header cyan">'
        '<h4>\U0001F3D6\uFE0F Fjords, Coasts & Shorelines</h4>'
        '<p>Fjords, cliffs, beaches, coastal erosion, tidal zones '
        '& 10 maps</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "Select Coastal Map Mode",
        MAP_MODES,
        key="fjord_maps_mode",
    )

    desc = MODE_DESCRIPTIONS.get(mode, "")
    if desc:
        color = MODE_COLORS.get(mode, "#06b6d4")
        st.markdown(
            f'<div style="background:rgba(15,23,42,0.65);'
            f'border-left:3px solid {color};'
            f'padding:12px 16px;border-radius:6px;margin:8px 0 16px 0;'
            f'color:#8b97b0;font-size:0.92rem;">'
            f'{escape(desc)}</div>',
            unsafe_allow_html=True,
        )

    renderer = _MODE_RENDERERS.get(mode)
    if renderer:
        renderer()
    else:
        st.warning(f"Mode '{mode}' is not yet implemented.")
