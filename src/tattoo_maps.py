# -*- coding: utf-8 -*-
"""
Tattoo, Art & Body Culture Maps module for TerraScout AI.
Curated geographic data on tattoo traditions, street art, museums,
art movements, ancient art, sculpture parks, photography landmarks,
graffiti culture, art markets, and body modification traditions.
All data is embedded — no API keys required.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ═══════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════
BG_COLOR = "#0a0e1a"
SURFACE_COLOR = "#111827"
TEXT_COLOR = "#e8ecf4"
ACCENT_CYAN = "#06b6d4"
ACCENT_PINK = "#ec4899"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_AMBER = "#f59e0b"
ACCENT_EMERALD = "#10b981"
ACCENT_RED = "#ef4444"
ACCENT_BLUE = "#3b82f6"
ACCENT_ORANGE = "#f97316"

MAP_MODES = [
    "1. Traditional Tattoo Cultures",
    "2. Street Art Capitals",
    "3. World's Greatest Museums",
    "4. Art Movements Origins",
    "5. Ancient Art Sites",
    "6. Sculpture Parks",
    "7. Photography Landmarks",
    "8. Graffiti & Urban Art",
    "9. Art Markets & Auctions",
    "10. Body Modification Traditions",
]

# ═══════════════════════════════════════════════════════════════
# 1. TRADITIONAL TATTOO CULTURES
# ═══════════════════════════════════════════════════════════════
TATTOO_CULTURES = [
    {"name": "Polynesian Tatau — Samoa", "lat": -13.83, "lon": -171.76, "tradition": "Polynesian Tatau",
     "description": "Sacred pe'a (male) and malu (female) tattoos. Hand-tapped using au (comb tools) made from bone. Designs encode genealogy, rank, and spiritual protection. Unbroken tradition for 2000+ years.",
     "period": "2000+ years", "technique": "Hand-tapping (au comb)", "color": "#06b6d4"},
    {"name": "Polynesian Tatau — Tonga", "lat": -21.18, "lon": -175.20, "tradition": "Polynesian Tatau",
     "description": "Tongan tatatau tradition closely linked to Samoan practice. Geometric patterns representing social status, warrior prowess, and island identity.",
     "period": "2000+ years", "technique": "Hand-tapping", "color": "#06b6d4"},
    {"name": "Polynesian Tatau — Tahiti", "lat": -17.53, "lon": -149.57, "tradition": "Polynesian Tatau",
     "description": "The word 'tattoo' derives from Tahitian 'tatau'. Full-body designs documented by Captain Cook in 1769. Nearly lost under missionary pressure, now revived.",
     "period": "1500+ years", "technique": "Hand-tapping", "color": "#06b6d4"},
    {"name": "Polynesian Tatau — Hawaii", "lat": 19.90, "lon": -155.58, "tradition": "Polynesian Kakau",
     "description": "Hawaiian kakau tradition features bold black geometric patterns. Tattooing was banned in 1819 but revived in the late 20th century by practitioners like Keone Nunes.",
     "period": "1000+ years", "technique": "Hand-tapping (traditional), machine (modern revival)", "color": "#06b6d4"},
    {"name": "Maori Ta Moko — New Zealand", "lat": -38.14, "lon": 176.25, "tradition": "Ta Moko",
     "description": "Carved (not punctured) facial and body tattoos unique to Maori. Moko are chiseled into skin using uhi (chisels). Each moko is unique, encoding whakapapa (genealogy), iwi (tribe), and mana.",
     "period": "1000+ years", "technique": "Chiseling with uhi (bone chisel)", "color": "#10b981"},
    {"name": "Maori Ta Moko — Rotorua", "lat": -38.14, "lon": 176.25, "tradition": "Ta Moko",
     "description": "Rotorua's Te Puia cultural center preserves ta moko traditions. Women wear moko kauae (chin tattoos) signifying leadership and heritage.",
     "period": "1000+ years", "technique": "Uhi chisel and modern machine", "color": "#10b981"},
    {"name": "Japanese Irezumi — Tokyo", "lat": 35.68, "lon": 139.69, "tradition": "Irezumi",
     "description": "Full-body Japanese tattoo art featuring dragons, koi, chrysanthemums, and mythological scenes. Tebori (hand-poking) tradition dates to Edo period. Associated with yakuza but rooted in ukiyo-e aesthetics.",
     "period": "300+ years (Edo period)", "technique": "Tebori (hand-poke with nomi stick)", "color": "#ef4444"},
    {"name": "Japanese Irezumi — Osaka", "lat": 34.69, "lon": 135.50, "tradition": "Irezumi",
     "description": "Osaka's tattoo masters specialize in horimono (engraved things). Kuniyoshi's ukiyo-e prints of tattooed heroes popularized the art in the 1800s.",
     "period": "300+ years", "technique": "Tebori and machine", "color": "#ef4444"},
    {"name": "Japanese Irezumi — Yokohama", "lat": 35.44, "lon": 139.64, "tradition": "Irezumi",
     "description": "Yokohama port was where Western sailors first encountered Japanese tattoo art, sparking global fascination. Hori Chiyo tattooed visiting royalty in the 1880s.",
     "period": "300+ years", "technique": "Tebori", "color": "#ef4444"},
    {"name": "Celtic Tattoo Traditions — Ireland", "lat": 53.35, "lon": -6.26, "tradition": "Celtic",
     "description": "Ancient Celts used woad (blue dye) for body marking. Knotwork, spirals, and triskeles symbolize eternity and interconnection. Modern Celtic tattoos draw from Book of Kells illuminations.",
     "period": "2500+ years", "technique": "Woad staining (ancient), needle (modern)", "color": "#8b5cf6"},
    {"name": "Celtic Tattoo Traditions — Scotland", "lat": 57.48, "lon": -4.22, "tradition": "Pictish/Celtic",
     "description": "The Picts ('painted people') of Scotland were named for their body art. Pictish stones preserve mysterious symbols that inspired modern Celtic tattoo designs.",
     "period": "2000+ years", "technique": "Woad and needle", "color": "#8b5cf6"},
    {"name": "Celtic Tattoo Traditions — Wales", "lat": 52.13, "lon": -3.78, "tradition": "Celtic",
     "description": "Welsh Celtic traditions feature the Red Dragon, triple spiral, and daffodil motifs alongside classic knotwork patterns.",
     "period": "2000+ years", "technique": "Woad (ancient), machine (modern)", "color": "#8b5cf6"},
    {"name": "Thai Sak Yant — Bangkok", "lat": 13.76, "lon": 100.50, "tradition": "Sak Yant",
     "description": "Sacred geometric tattoos applied by Buddhist monks using a mai sak (long metal rod). Designs include the Hah Taew (five lines), Gao Yord (nine spires), and Paed Tidt (eight directions). Believed to grant protection and power.",
     "period": "700+ years (Khmer origin)", "technique": "Mai sak (metal rod hand-poke)", "color": "#f59e0b"},
    {"name": "Thai Sak Yant — Wat Bang Phra", "lat": 13.98, "lon": 100.22, "tradition": "Sak Yant",
     "description": "Famous temple west of Bangkok where monks administer Sak Yant tattoos. Annual Wai Khru festival sees devotees enter trance states, believed activated by tattoo magic.",
     "period": "700+ years", "technique": "Mai sak rod by monks", "color": "#f59e0b"},
    {"name": "Sak Yant — Chiang Mai", "lat": 18.79, "lon": 98.98, "tradition": "Sak Yant",
     "description": "Northern Thai ajarn (masters) practice a slightly different Lanna style of Sak Yant with distinctive yantra geometry and Khom script.",
     "period": "500+ years", "technique": "Mai sak and bamboo", "color": "#f59e0b"},
    {"name": "Berber Tattoos — Morocco", "lat": 31.63, "lon": -8.01, "tradition": "Berber/Amazigh",
     "description": "Amazigh women traditionally wore facial and hand tattoos. Motifs include diamonds, crosses, and palm fronds symbolizing fertility, protection against evil eye, and tribal identity.",
     "period": "3000+ years", "technique": "Needle and soot/indigo", "color": "#ec4899"},
    {"name": "Filipino Batok — Kalinga Province", "lat": 17.47, "lon": 121.37, "tradition": "Batok",
     "description": "Whang-Od Oggay, born 1917, is the last mambabatok (tattoo artist) of Kalinga. She uses a thorn from a pomelo tree and charcoal soot to create geometric warrior tattoos.",
     "period": "1000+ years", "technique": "Thorn hand-tapping (batok)", "color": "#f97316"},
    {"name": "Inuit Tattoos — Nunavut, Canada", "lat": 63.75, "lon": -68.52, "tradition": "Tunniit/Kakiniit",
     "description": "Inuit women's facial tattoos (tunniit) mark coming of age, spiritual milestones, and shamanic power. Applied by skin-stitching with caribou sinew and soot. Suppressed by colonizers, now revived.",
     "period": "3500+ years", "technique": "Skin-stitching with sinew and soot", "color": "#38bdf8"},
    {"name": "Mentawai Tattoos — Siberut Island, Indonesia", "lat": -1.55, "lon": 99.00, "tradition": "Titi",
     "description": "Mentawai people of Siberut have the oldest continuous tattoo tradition. Full-body tattoos represent the soul's journey, animal spirits, and harmony with nature.",
     "period": "4000+ years", "technique": "Thorn and soot hand-tapping", "color": "#a855f7"},
    {"name": "Ainu Tattoos — Hokkaido, Japan", "lat": 43.06, "lon": 141.35, "tradition": "Sinuye",
     "description": "Ainu women wore mouth tattoos (sinuye) begun in childhood and completed before marriage. The smile-like designs around the mouth were believed to ward off evil spirits.",
     "period": "1000+ years (banned 1871)", "technique": "Knife cuts with birch soot", "color": "#14b8a6"},
    {"name": "Dayak Tattoos — Borneo", "lat": 1.55, "lon": 110.35, "tradition": "Dayak Pantang",
     "description": "Iban and other Dayak peoples use hand-tapped tattoos to record headhunting victories, river journeys, and spiritual achievements. The bunga terung (eggplant flower) marks a young man's first journey.",
     "period": "2000+ years", "technique": "Hand-tapping with wooden mallet and needles", "color": "#d946ef"},
    {"name": "Egyptian Tattoo Tradition — Deir el-Medina", "lat": 25.73, "lon": 32.60, "tradition": "Ancient Egyptian",
     "description": "Female mummies from 2000 BCE show dot and line tattoos on the abdomen and thighs. Believed to protect during childbirth. Priestess Amunet bore diamond patterns. Tattooed figurines found at multiple sites.",
     "period": "4000+ years", "technique": "Bundle of bronze needles with soot", "color": "#fbbf24"},
    {"name": "Scythian Tattoo Tradition — Pazyryk, Altai", "lat": 50.43, "lon": 87.66, "tradition": "Scythian",
     "description": "Frozen Pazyryk burials (c. 500 BCE) preserved elaborate animal-style tattoos on chieftains. Griffins, deer, and mythical beasts cover arms, torsos, and legs.",
     "period": "2500 years", "technique": "Needle and soot", "color": "#fb923c"},
    {"name": "Samoan Tatau — American Samoa", "lat": -14.27, "lon": -170.70, "tradition": "Polynesian Tatau",
     "description": "The tufuga ta tatau (master tattooist) lineage continues unbroken. The pe'a takes weeks and covers from waist to knees. Stopping midway brings shame (pe'a mutu).",
     "period": "3000+ years", "technique": "Au (bone comb) hand-tapping", "color": "#06b6d4"},
    {"name": "Visayan Pintados — Cebu, Philippines", "lat": 10.31, "lon": 123.89, "tradition": "Pintados",
     "description": "Spanish colonizers called Visayan warriors 'Pintados' (painted ones) for their extensive tattoos. Designs depicted crocodiles, serpents, and centipedes — earned through bravery in battle.",
     "period": "1000+ years (pre-colonial)", "technique": "Thorn and soot", "color": "#f97316"},
]

# ═══════════════════════════════════════════════════════════════
# 2. STREET ART CAPITALS
# ═══════════════════════════════════════════════════════════════
STREET_ART_CITIES = [
    {"name": "Berlin, Germany", "lat": 52.50, "lon": 13.40, "highlights": "East Side Gallery (1.3km of Berlin Wall murals), RAW-Gelande, Kreuzberg, Urban Nation Museum",
     "notable_artists": "Blu, JR, Os Gemeos, ROA, ALIAS", "description": "Post-reunification explosion of street art. The East Side Gallery features 105 murals on the longest surviving section of the Berlin Wall. Kreuzberg is an open-air gallery.", "score": 98, "color": "#06b6d4"},
    {"name": "Melbourne, Australia", "lat": -37.81, "lon": 144.96, "highlights": "Hosier Lane, ACDC Lane, Duckboard Place, Blender Studios, Fitzroy",
     "notable_artists": "Rone, Lushsux, Adnate, Sofles, Fintan Magee", "description": "Melbourne's laneways form the world's most concentrated street art precinct. City council protects and encourages murals. Hosier Lane is repainted weekly.", "score": 97, "color": "#ec4899"},
    {"name": "Bristol, UK", "lat": 51.45, "lon": -2.58, "highlights": "Banksy trail, Nelson Street, Upfest festival, Stokes Croft, See No Evil",
     "notable_artists": "Banksy, Inkie, Nick Walker, 3Dom, Cheba", "description": "Birthplace of Banksy. The annual Upfest is Europe's largest street art festival. Nelson Street's See No Evil project transformed an entire street into murals.", "score": 95, "color": "#8b5cf6"},
    {"name": "Sao Paulo, Brazil", "lat": -23.55, "lon": -46.63, "highlights": "Vila Madalena (Beco do Batman), Avenida Paulista, MAAU open-air museum, Liberdade",
     "notable_artists": "Os Gemeos, Eduardo Kobra, Nina Pandolfo, Nunca, Cranio", "description": "Sao Paulo has the densest concentration of street art of any city. The pixacao (tag) tradition is unique to Brazil. Beco do Batman is a labyrinth of color.", "score": 96, "color": "#10b981"},
    {"name": "New York City, USA", "lat": 40.72, "lon": -73.99, "highlights": "Bushwick Collective, Bowery Wall, Williamsburg, L.I.S.A. Project, Hunts Point",
     "notable_artists": "Jean-Michel Basquiat, Keith Haring, Lady Pink, KAWS, Swoon", "description": "Birthplace of modern graffiti culture in the 1970s. The subway art era defined a global movement. Bushwick Collective is now a destination gallery.", "score": 97, "color": "#ef4444"},
    {"name": "Valparaiso, Chile", "lat": -33.05, "lon": -71.62, "highlights": "Cerro Alegre, Cerro Concepcion, Open Sky Museum (Museo a Cielo Abierto), Pasaje Gálvez",
     "notable_artists": "INTI, Charquipunk, Un Kolor Distinto, Cekis, Henruz", "description": "The hillside UNESCO city is painted in its entirety. The Museo a Cielo Abierto features 20 massive murals on retaining walls. Every surface is a canvas.", "score": 93, "color": "#f59e0b"},
    {"name": "Bogota, Colombia", "lat": 4.71, "lon": -74.07, "highlights": "La Candelaria, Carrera 7, Chapinero, Bogota Graffiti Tour route",
     "notable_artists": "DJ Lu, Stinkfish, Toxicomano, Guache, Lesivo", "description": "After police killed a teen graffiti artist in 2011, Bogota decriminalized street art. Now one of the world's most vibrant scenes with political and social themes.", "score": 94, "color": "#f97316"},
    {"name": "Penang, Malaysia (George Town)", "lat": 5.41, "lon": 100.34, "highlights": "Armenian Street murals, wire art installations, Hin Bus Depot, Campbell Street",
     "notable_artists": "Ernest Zacharevic, Louis Gan, Bibichun, ASA", "description": "Ernest Zacharevic's interactive murals (children on a bicycle, boy on a chair) turned George Town into Asia's street art capital. Wire sculptures complement painted walls.", "score": 90, "color": "#38bdf8"},
    {"name": "Lisbon, Portugal", "lat": 38.72, "lon": -9.14, "highlights": "LX Factory, Bairro Alto, Mouraria, Avenida Fontes Pereira de Melo, Quinta do Mocho",
     "notable_artists": "Vhils, Bordalo II, Pantonio, AkaCorleone, Tamara Alves", "description": "Vhils carves portraits into walls. Bordalo II creates animal sculptures from trash. Lisbon's Galeria de Arte Urbana program commissions massive facades.", "score": 92, "color": "#a855f7"},
    {"name": "Buenos Aires, Argentina", "lat": -34.61, "lon": -58.38, "highlights": "Palermo, La Boca, Barracas, Colegiales, BA Street Art tours",
     "notable_artists": "Milu Correch, Martin Ron, Poeta, Cabaio, Elian Chali", "description": "Building owners invite artists to paint facades. No permission needed on private walls (by custom). Massive photorealistic murals by Martin Ron span entire buildings.", "score": 93, "color": "#14b8a6"},
    {"name": "London, UK", "lat": 51.52, "lon": -0.07, "highlights": "Shoreditch, Brick Lane, Leake Street Tunnel, Camden, Dulwich Outdoor Gallery",
     "notable_artists": "Banksy, Stik, Ben Eine, Phlegm, Roa", "description": "Shoreditch and Brick Lane form London's graffiti heartland. Leake Street (Banksy Tunnel) is a legal painting space under Waterloo Station. Ben Eine's alphabet shutters are iconic.", "score": 95, "color": "#d946ef"},
    {"name": "Athens, Greece", "lat": 37.98, "lon": 23.73, "highlights": "Exarchia, Psyrri, Metaxourgeio, Gazi, Kerameikos",
     "notable_artists": "iNO, Achilles, Alexandros Vasmoulakis, WD, b.", "description": "Greece's economic crisis sparked an explosion of politically charged street art. Exarchia neighborhood is a anarchist-art epicenter with every surface covered.", "score": 91, "color": "#fbbf24"},
    {"name": "Mexico City, Mexico", "lat": 19.43, "lon": -99.13, "highlights": "Roma Norte, Coyoacan, Xochimilco, Ciudad Universitaria murals, Tepito",
     "notable_artists": "Saner, Smithe, Hilda Palafox (Poni), Paola Delfin, Revost", "description": "Mexico's muralism tradition (Rivera, Orozco, Siqueiros) lives on in contemporary street art. The UNAM campus murals are UNESCO listed. Roma Norte has world-class work.", "score": 94, "color": "#fb923c"},
    {"name": "Cape Town, South Africa", "lat": -33.93, "lon": 18.42, "highlights": "Woodstock, Salt River, District Six, Bo-Kaap edges, IPAF festival",
     "notable_artists": "Faith47, Freddy Sam, Ricky Lee Gordon, Jack Fox, DALeast", "description": "Woodstock and Salt River have been transformed into outdoor galleries. Themes of apartheid history, social justice, and African identity dominate. Annual IPAF festival draws international artists.", "score": 90, "color": "#f472b6"},
]

# ═══════════════════════════════════════════════════════════════
# 3. WORLD'S GREATEST MUSEUMS
# ═══════════════════════════════════════════════════════════════
MUSEUMS = [
    {"name": "Louvre Museum", "city": "Paris, France", "lat": 48.8606, "lon": 2.3376, "founded": 1793, "visitors_m": 8.9, "collection_size": "380,000+", "highlights": "Mona Lisa, Venus de Milo, Winged Victory, Code of Hammurabi", "type": "Universal", "color": "#06b6d4"},
    {"name": "British Museum", "city": "London, UK", "lat": 51.5194, "lon": -0.1270, "founded": 1753, "visitors_m": 5.8, "collection_size": "8,000,000+", "highlights": "Rosetta Stone, Elgin Marbles, Egyptian mummies, Sutton Hoo", "type": "Universal", "color": "#8b5cf6"},
    {"name": "Metropolitan Museum of Art", "city": "New York, USA", "lat": 40.7794, "lon": -73.9632, "founded": 1870, "visitors_m": 5.4, "collection_size": "1,500,000+", "highlights": "Temple of Dendur, Washington Crossing the Delaware, Arms & Armor", "type": "Universal", "color": "#ef4444"},
    {"name": "State Hermitage Museum", "city": "Saint Petersburg, Russia", "lat": 59.9398, "lon": 30.3146, "founded": 1764, "visitors_m": 3.9, "collection_size": "3,000,000+", "highlights": "Rembrandt, Matisse rooms, Scythian gold, Peacock Clock", "type": "Universal", "color": "#f59e0b"},
    {"name": "Museo del Prado", "city": "Madrid, Spain", "lat": 40.4138, "lon": -3.6921, "founded": 1819, "visitors_m": 3.5, "collection_size": "35,000+", "highlights": "Las Meninas (Velazquez), Garden of Earthly Delights (Bosch), Goya Black Paintings", "type": "Art", "color": "#10b981"},
    {"name": "Vatican Museums", "city": "Vatican City", "lat": 41.9065, "lon": 12.4536, "founded": 1506, "visitors_m": 6.9, "collection_size": "70,000+", "highlights": "Sistine Chapel ceiling, Raphael Rooms, Laocoon, Gallery of Maps", "type": "Art/Religious", "color": "#ec4899"},
    {"name": "Uffizi Gallery", "city": "Florence, Italy", "lat": 43.7677, "lon": 11.2553, "founded": 1581, "visitors_m": 4.4, "collection_size": "100,000+", "highlights": "Birth of Venus (Botticelli), Annunciation (da Vinci), Medusa (Caravaggio)", "type": "Art", "color": "#f97316"},
    {"name": "Rijksmuseum", "city": "Amsterdam, Netherlands", "lat": 52.3600, "lon": 4.8852, "founded": 1800, "visitors_m": 2.7, "collection_size": "1,000,000+", "highlights": "Night Watch (Rembrandt), The Milkmaid (Vermeer), Delftware collection", "type": "Art/History", "color": "#3b82f6"},
    {"name": "Musee d'Orsay", "city": "Paris, France", "lat": 48.8600, "lon": 2.3266, "founded": 1986, "visitors_m": 3.7, "collection_size": "100,000+", "highlights": "Starry Night Over the Rhone (Van Gogh), Bal du moulin de la Galette (Renoir)", "type": "Art (Impressionist)", "color": "#a855f7"},
    {"name": "National Gallery", "city": "London, UK", "lat": 51.5089, "lon": -0.1283, "founded": 1824, "visitors_m": 5.3, "collection_size": "2,300+", "highlights": "Sunflowers (Van Gogh), Arnolfini Portrait (van Eyck), The Fighting Temeraire (Turner)", "type": "Art", "color": "#14b8a6"},
    {"name": "Museum of Modern Art (MoMA)", "city": "New York, USA", "lat": 40.7614, "lon": -73.9776, "founded": 1929, "visitors_m": 2.8, "collection_size": "200,000+", "highlights": "Starry Night (Van Gogh), Persistence of Memory (Dali), Les Demoiselles d'Avignon (Picasso)", "type": "Modern Art", "color": "#06b6d4"},
    {"name": "Museo Nacional de Antropologia", "city": "Mexico City, Mexico", "lat": 19.4260, "lon": -99.1863, "founded": 1964, "visitors_m": 2.2, "collection_size": "600,000+", "highlights": "Aztec Sun Stone, Olmec colossal heads, Maya jade mask of Pakal", "type": "Anthropology", "color": "#f59e0b"},
    {"name": "Egyptian Museum", "city": "Cairo, Egypt", "lat": 30.0478, "lon": 31.2336, "founded": 1902, "visitors_m": 2.0, "collection_size": "120,000+", "highlights": "Tutankhamun's gold mask, Royal Mummy Room, Narmer Palette", "type": "Archaeological", "color": "#fbbf24"},
    {"name": "Acropolis Museum", "city": "Athens, Greece", "lat": 37.9684, "lon": 23.7284, "founded": 2009, "visitors_m": 1.8, "collection_size": "4,000+", "highlights": "Caryatids, Parthenon Gallery, Archaic Kore statues", "type": "Archaeological", "color": "#38bdf8"},
    {"name": "National Palace Museum", "city": "Taipei, Taiwan", "lat": 25.1024, "lon": 121.5485, "founded": 1925, "visitors_m": 3.8, "collection_size": "700,000+", "highlights": "Jadeite Cabbage, Meat-shaped Stone, Mao Gong Ding bronze", "type": "Chinese Art", "color": "#ef4444"},
    {"name": "Smithsonian National Museum", "city": "Washington DC, USA", "lat": 38.8913, "lon": -77.0260, "founded": 1846, "visitors_m": 7.1, "collection_size": "155,000,000+", "highlights": "Hope Diamond, Spirit of St. Louis, Star-Spangled Banner, First Ladies' gowns", "type": "Universal", "color": "#8b5cf6"},
    {"name": "Pergamon Museum", "city": "Berlin, Germany", "lat": 52.5212, "lon": 13.3966, "founded": 1930, "visitors_m": 2.3, "collection_size": "270,000+", "highlights": "Ishtar Gate, Pergamon Altar, Market Gate of Miletus", "type": "Archaeological", "color": "#10b981"},
    {"name": "Tokyo National Museum", "city": "Tokyo, Japan", "lat": 35.7189, "lon": 139.7766, "founded": 1872, "visitors_m": 2.1, "collection_size": "120,000+", "highlights": "National Treasure samurai armor, Heian scrolls, Jomon pottery, ukiyo-e prints", "type": "Art/History", "color": "#ec4899"},
    {"name": "Galleria Borghese", "city": "Rome, Italy", "lat": 41.9142, "lon": 12.4922, "founded": 1903, "visitors_m": 0.6, "collection_size": "780+", "highlights": "Apollo and Daphne (Bernini), Pauline Bonaparte (Canova), Boy with a Basket (Caravaggio)", "type": "Art", "color": "#f97316"},
    {"name": "Kunsthistorisches Museum", "city": "Vienna, Austria", "lat": 48.2034, "lon": 16.3616, "founded": 1891, "visitors_m": 1.8, "collection_size": "780,000+", "highlights": "Tower of Babel (Bruegel), Cellini Salt Cellar, Vermeer's Art of Painting", "type": "Art/History", "color": "#d946ef"},
    {"name": "State Tretyakov Gallery", "city": "Moscow, Russia", "lat": 55.7415, "lon": 37.6208, "founded": 1856, "visitors_m": 2.1, "collection_size": "180,000+", "highlights": "Trinity (Rublev), Bogatyrs (Vasnetsov), Ivan the Terrible (Repin)", "type": "Russian Art", "color": "#fb923c"},
    {"name": "National Museum of Korea", "city": "Seoul, South Korea", "lat": 37.5239, "lon": 126.9805, "founded": 1945, "visitors_m": 3.4, "collection_size": "420,000+", "highlights": "Silla gold crown, Goryeo celadon, Joseon white porcelain, Baekje incense burner", "type": "Art/History", "color": "#06b6d4"},
    {"name": "Art Institute of Chicago", "city": "Chicago, USA", "lat": 41.8796, "lon": -87.6237, "founded": 1879, "visitors_m": 1.7, "collection_size": "300,000+", "highlights": "American Gothic (Wood), A Sunday on La Grande Jatte (Seurat), Nighthawks (Hopper)", "type": "Art", "color": "#8b5cf6"},
    {"name": "Museu Nacional d'Art de Catalunya", "city": "Barcelona, Spain", "lat": 41.3685, "lon": 2.1527, "founded": 1990, "visitors_m": 0.9, "collection_size": "290,000+", "highlights": "Romanesque church murals, Gothic altarpieces, Gaudi furniture, Catalan modernisme", "type": "Art", "color": "#f59e0b"},
    {"name": "National Gallery of Victoria", "city": "Melbourne, Australia", "lat": -37.8226, "lon": 144.9689, "founded": 1861, "visitors_m": 3.3, "collection_size": "75,000+", "highlights": "Great Hall stained glass ceiling, Tiepolo, Banquet of Cleopatra, Australian art", "type": "Art", "color": "#10b981"},
    {"name": "Musee de l'Orangerie", "city": "Paris, France", "lat": 48.8638, "lon": 2.3225, "founded": 1927, "visitors_m": 1.0, "collection_size": "150+", "highlights": "Monet's Water Lilies (eight massive murals in oval rooms)", "type": "Art (Impressionist)", "color": "#ec4899"},
    {"name": "Mus. Egipcio de Turin (Museo Egizio)", "city": "Turin, Italy", "lat": 45.0688, "lon": 7.6842, "founded": 1824, "visitors_m": 0.9, "collection_size": "40,000+", "highlights": "Second largest Egyptian collection after Cairo. Tomb of Kha, Temple of Ellesiya, Book of the Dead papyri", "type": "Archaeological", "color": "#fbbf24"},
    {"name": "Museo Nacional Centro de Arte Reina Sofia", "city": "Madrid, Spain", "lat": 40.4085, "lon": -3.6943, "founded": 1992, "visitors_m": 4.4, "collection_size": "23,000+", "highlights": "Guernica (Picasso), The Great Masturbator (Dali), Woman in Blue (Picasso)", "type": "Modern Art", "color": "#ef4444"},
    {"name": "Tate Modern", "city": "London, UK", "lat": 51.5076, "lon": -0.0994, "founded": 2000, "visitors_m": 5.9, "collection_size": "70,000+", "highlights": "Turbine Hall installations, Rothko Room, Warhol, Picasso, Giacometti", "type": "Modern/Contemporary", "color": "#3b82f6"},
    {"name": "Centre Pompidou", "city": "Paris, France", "lat": 48.8607, "lon": 2.3524, "founded": 1977, "visitors_m": 3.3, "collection_size": "120,000+", "highlights": "Inside-out architecture, Matisse, Kandinsky, Duchamp, Frida Kahlo", "type": "Modern/Contemporary", "color": "#a855f7"},
]

# ═══════════════════════════════════════════════════════════════
# 4. ART MOVEMENTS ORIGINS
# ═══════════════════════════════════════════════════════════════
ART_MOVEMENTS = [
    {"name": "Renaissance", "city": "Florence, Italy", "lat": 43.77, "lon": 11.25, "period": "1400-1600",
     "key_artists": "Leonardo da Vinci, Michelangelo, Botticelli, Raphael, Donatello",
     "description": "Rebirth of classical learning and art. Linear perspective, anatomical accuracy, and humanism emerged under Medici patronage. The Duomo, Uffizi, and Accademia hold the core works.", "color": "#f59e0b"},
    {"name": "Baroque", "city": "Rome, Italy", "lat": 41.90, "lon": 12.50, "period": "1600-1750",
     "key_artists": "Caravaggio, Bernini, Borromini, Artemisia Gentileschi",
     "description": "Dramatic, emotional, grandiose art born of Counter-Reformation Rome. Caravaggio's chiaroscuro and Bernini's ecstatic sculptures defined the era. St. Peter's Basilica is the pinnacle.", "color": "#ef4444"},
    {"name": "Dutch Golden Age", "city": "Amsterdam, Netherlands", "lat": 52.37, "lon": 4.90, "period": "1588-1672",
     "key_artists": "Rembrandt, Vermeer, Frans Hals, Jan Steen, Pieter de Hooch",
     "description": "Trade wealth fueled an explosion of painting. Rembrandt's Night Watch and Vermeer's Girl with a Pearl Earring are icons. Genre scenes, still lifes, and landscapes flourished.", "color": "#06b6d4"},
    {"name": "Impressionism", "city": "Paris, France", "lat": 48.86, "lon": 2.34, "period": "1860-1890",
     "key_artists": "Monet, Renoir, Degas, Pissarro, Berthe Morisot, Cezanne",
     "description": "Painting light and movement en plein air. First exhibited at Nadar's studio in 1874. Name came from Monet's 'Impression, Sunrise'. Musee d'Orsay houses the definitive collection.", "color": "#ec4899"},
    {"name": "Post-Impressionism", "city": "Arles/Paris, France", "lat": 43.68, "lon": 4.63, "period": "1886-1905",
     "key_artists": "Van Gogh, Gauguin, Cezanne, Toulouse-Lautrec, Seurat",
     "description": "Beyond Impressionism: Van Gogh's emotional color in Arles, Gauguin's Tahitian primitivism, Seurat's pointillism, Cezanne's proto-Cubism in Aix-en-Provence.", "color": "#8b5cf6"},
    {"name": "Art Nouveau", "city": "Brussels, Belgium", "lat": 50.85, "lon": 4.35, "period": "1890-1910",
     "key_artists": "Victor Horta, Alphonse Mucha, Gustav Klimt, Gaudi, Hector Guimard",
     "description": "Organic, flowing forms inspired by nature. Horta's Tassel House in Brussels launched the movement. Paris Metro entrances, Klimt's The Kiss, and Gaudi's Barcelona are its monuments.", "color": "#10b981"},
    {"name": "Cubism", "city": "Paris, France (Montmartre)", "lat": 48.8867, "lon": 2.3431, "period": "1907-1920s",
     "key_artists": "Pablo Picasso, Georges Braque, Juan Gris, Fernand Leger",
     "description": "Fragmented reality into geometric planes. Picasso's Les Demoiselles d'Avignon (1907) shattered perspective. Developed at Bateau-Lavoir studio in Montmartre.", "color": "#f97316"},
    {"name": "Futurism", "city": "Milan, Italy", "lat": 45.46, "lon": 9.19, "period": "1909-1944",
     "key_artists": "Filippo Marinetti, Umberto Boccioni, Giacomo Balla, Luigi Russolo",
     "description": "Celebrated speed, machinery, and modernity. Marinetti published the Futurist Manifesto in 1909. Boccioni's Unique Forms of Continuity in Space is the movement's icon.", "color": "#3b82f6"},
    {"name": "Expressionism", "city": "Dresden/Munich, Germany", "lat": 51.05, "lon": 13.74, "period": "1905-1930s",
     "key_artists": "Ernst Ludwig Kirchner, Edvard Munch, Egon Schiele, Wassily Kandinsky",
     "description": "Raw emotion over realistic depiction. Die Brucke (Dresden) and Der Blaue Reiter (Munich) groups. Munch's The Scream embodies existential anxiety.", "color": "#ef4444"},
    {"name": "Dada", "city": "Zurich, Switzerland", "lat": 47.37, "lon": 8.54, "period": "1916-1924",
     "key_artists": "Marcel Duchamp, Hugo Ball, Tristan Tzara, Hannah Hoch, Man Ray",
     "description": "Anti-art born at Cabaret Voltaire during WWI. Duchamp's urinal ('Fountain') challenged every assumption about art. Collage, chance, and absurdity were its weapons.", "color": "#a855f7"},
    {"name": "Surrealism", "city": "Paris, France", "lat": 48.85, "lon": 2.35, "period": "1924-1960s",
     "key_artists": "Salvador Dali, Rene Magritte, Max Ernst, Frida Kahlo, Miro",
     "description": "Dreams, the unconscious, and the irrational. Andre Breton's 1924 Manifesto launched the movement. Dali's melting clocks and Magritte's paradoxes defined visual surrealism.", "color": "#ec4899"},
    {"name": "Bauhaus", "city": "Weimar/Dessau, Germany", "lat": 51.84, "lon": 11.28, "period": "1919-1933",
     "key_artists": "Walter Gropius, Paul Klee, Wassily Kandinsky, Laszlo Moholy-Nagy, Josef Albers",
     "description": "Form follows function. The Bauhaus school unified art, craft, and technology. Closed by Nazis in 1933, its ideas shaped modern design, architecture, and typography worldwide.", "color": "#06b6d4"},
    {"name": "Abstract Expressionism", "city": "New York, USA", "lat": 40.73, "lon": -74.00, "period": "1943-1965",
     "key_artists": "Jackson Pollock, Mark Rothko, Willem de Kooning, Franz Kline, Lee Krasner",
     "description": "First major American art movement. Pollock's drip paintings and Rothko's color fields emerged from Cedar Tavern and Tenth Street galleries. Shifted the art world's center from Paris to NYC.", "color": "#f59e0b"},
    {"name": "Pop Art", "city": "London/New York", "lat": 40.75, "lon": -73.99, "period": "1956-1970s",
     "key_artists": "Andy Warhol, Roy Lichtenstein, Richard Hamilton, Jasper Johns, Claes Oldenburg",
     "description": "Mass culture as high art. Hamilton's collage (1956) started it in London. Warhol's Factory in NYC made Campbell's Soup cans and Marilyn Monroe into icons.", "color": "#ef4444"},
    {"name": "Minimalism", "city": "New York, USA", "lat": 40.72, "lon": -74.01, "period": "1960s-1970s",
     "key_artists": "Donald Judd, Dan Flavin, Sol LeWitt, Agnes Martin, Frank Stella",
     "description": "Stripped art to essentials: geometry, industrial materials, repetition. Judd's Marfa installations in Texas are the ultimate expression. 'What you see is what you see.' (Stella)", "color": "#38bdf8"},
    {"name": "Ukiyo-e", "city": "Edo (Tokyo), Japan", "lat": 35.68, "lon": 139.77, "period": "1603-1868",
     "key_artists": "Hokusai, Hiroshige, Utamaro, Sharaku, Kuniyoshi",
     "description": "Woodblock prints of the 'floating world' — courtesans, kabuki actors, landscapes. Hokusai's Great Wave is the world's most recognized artwork. Profoundly influenced Impressionism.", "color": "#14b8a6"},
    {"name": "Mexican Muralism", "city": "Mexico City, Mexico", "lat": 19.43, "lon": -99.13, "period": "1920s-1970s",
     "key_artists": "Diego Rivera, David Alfaro Siqueiros, Jose Clemente Orozco, Frida Kahlo",
     "description": "Post-revolution public art celebrating indigenous identity and socialist ideals. Rivera's murals at the National Palace span Mexico's entire history. Influenced global public art.", "color": "#10b981"},
    {"name": "Land Art / Earthworks", "city": "Great Salt Lake, Utah, USA", "lat": 41.44, "lon": -112.67, "period": "1960s-present",
     "key_artists": "Robert Smithson, Michael Heizer, Walter De Maria, Nancy Holt, James Turrell",
     "description": "Art made from and in the landscape. Smithson's Spiral Jetty (1970) and Heizer's Double Negative redefined art's scale. Turrell's Roden Crater is art's most ambitious project.", "color": "#8b5cf6"},
]

# ═══════════════════════════════════════════════════════════════
# 5. ANCIENT ART SITES
# ═══════════════════════════════════════════════════════════════
ANCIENT_ART = [
    {"name": "Lascaux Cave", "location": "Dordogne, France", "lat": 45.0544, "lon": 1.1686, "age": "17,000 years",
     "description": "The 'Sistine Chapel of Prehistory'. Over 600 paintings of aurochs, horses, and deer. Discovered 1940 by teenagers. Original sealed since 1963; Lascaux IV replica open.", "type": "Cave Painting", "color": "#f59e0b"},
    {"name": "Altamira Cave", "location": "Cantabria, Spain", "lat": 43.3779, "lon": -4.1210, "age": "36,000 years",
     "description": "Polychrome bison ceiling paintings of extraordinary sophistication. First prehistoric cave art discovered (1879). Initially dismissed as forgery because quality was 'too good'.", "type": "Cave Painting", "color": "#ef4444"},
    {"name": "Chauvet Cave", "location": "Ardeche, France", "lat": 44.3885, "lon": 4.4175, "age": "36,000 years",
     "description": "Oldest known figurative art. Lions, rhinoceroses, and mammoths rendered with sophisticated shading and perspective. Werner Herzog filmed 'Cave of Forgotten Dreams' here.", "type": "Cave Painting", "color": "#06b6d4"},
    {"name": "Kakadu Rock Art", "location": "Northern Territory, Australia", "lat": -12.84, "lon": 132.87, "age": "20,000+ years",
     "description": "Aboriginal rock art spanning millennia. X-ray style paintings show internal anatomy of animals. Ubirr and Nourlangie sites contain thousands of artworks documenting 65,000 years of culture.", "type": "Rock Art", "color": "#10b981"},
    {"name": "Tassili n'Ajjer", "location": "Algeria (Sahara)", "lat": 25.50, "lon": 9.00, "age": "12,000 years",
     "description": "15,000+ petroglyphs and paintings on Saharan sandstone. Depicts a green Sahara with hippos, giraffes, and cattle herders. UNESCO World Heritage Site spanning 72,000 km2.", "type": "Rock Art/Petroglyphs", "color": "#ec4899"},
    {"name": "Bhimbetka Rock Shelters", "location": "Madhya Pradesh, India", "lat": 22.9376, "lon": 77.6119, "age": "30,000 years",
     "description": "Over 700 rock shelters with paintings spanning 30,000 years. Scenes of hunting, dancing, horse-riding, and honey collection. Stone Age to medieval period represented.", "type": "Rock Art", "color": "#8b5cf6"},
    {"name": "Gobustan Petroglyphs", "location": "Azerbaijan", "lat": 40.0865, "lon": 49.3741, "age": "40,000 years",
     "description": "6,000+ rock carvings depicting hunting, dancing, boats, and animals. Thor Heyerdahl believed reed-boat carvings linked to Scandinavia. UNESCO World Heritage since 2007.", "type": "Petroglyphs", "color": "#f97316"},
    {"name": "Drakensberg Cave Paintings", "location": "KwaZulu-Natal, South Africa", "lat": -29.40, "lon": 29.45, "age": "3,000 years",
     "description": "San (Bushmen) rock art — 35,000+ paintings in 500+ caves. Depicts trance dances, eland hunts, and therianthropes (human-animal hybrids). Game Pass Shelter's Rosetta Stone panel is key.", "type": "Rock Art", "color": "#38bdf8"},
    {"name": "Cueva de las Manos", "location": "Santa Cruz, Argentina", "lat": -47.15, "lon": -70.67, "age": "13,000 years",
     "description": "Cave of the Hands — hundreds of stenciled handprints in red, black, yellow, and white. Created by blowing pigment through bone tubes. Also depicts guanacos and hunting scenes.", "type": "Cave Art", "color": "#a855f7"},
    {"name": "Twyfelfontein", "location": "Kunene, Namibia", "lat": -20.59, "lon": 14.37, "age": "6,000 years",
     "description": "Over 2,500 San rock engravings (petroglyphs) depicting elephants, rhinos, giraffes, and human footprints. One of Africa's largest concentrations of petroglyphs. UNESCO listed.", "type": "Petroglyphs", "color": "#14b8a6"},
    {"name": "Ajanta Caves", "location": "Maharashtra, India", "lat": 20.5519, "lon": 75.7033, "age": "2,200 years",
     "description": "30 rock-cut Buddhist caves with exquisite frescoes depicting Jataka tales. Cave 1's Padmapani and Cave 2's ceiling paintings are masterpieces of ancient Indian art.", "type": "Cave Painting/Sculpture", "color": "#fbbf24"},
    {"name": "Mogao Caves (Dunhuang)", "location": "Gansu, China", "lat": 40.0359, "lon": 94.8093, "age": "1,600 years",
     "description": "492 grottoes with 45,000 sq meters of murals and 2,415 painted sculptures. Buddhist art spanning ten dynasties. The Diamond Sutra (868 CE), world's oldest printed book, was found here.", "type": "Cave Painting/Sculpture", "color": "#ef4444"},
    {"name": "Nazca Lines", "location": "Nazca, Peru", "lat": -14.72, "lon": -75.13, "age": "2,000 years",
     "description": "Giant geoglyphs (up to 370m long) depicting a hummingbird, spider, monkey, and condor. Only visible from air. Created by removing red pebbles to expose white ground beneath.", "type": "Geoglyphs", "color": "#06b6d4"},
    {"name": "Valcamonica Rock Art", "location": "Lombardy, Italy", "lat": 46.03, "lon": 10.35, "age": "13,000 years",
     "description": "300,000+ petroglyphs across 2,000+ rocks — the world's largest collection. Depicts deer, warriors, plowing scenes, maps, and the famous Camunian Rose. First Italian UNESCO site (1979).", "type": "Petroglyphs", "color": "#ec4899"},
    {"name": "Serra da Capivara", "location": "Piaui, Brazil", "lat": -8.83, "lon": -42.55, "age": "25,000 years",
     "description": "Over 30,000 rock paintings in 800+ sites. Depicts hunting, warfare, dancing, and sexuality. Some of the earliest evidence of human habitation in the Americas. UNESCO listed.", "type": "Rock Art", "color": "#10b981"},
    {"name": "Petroglyphs of Tamgaly", "location": "Almaty Region, Kazakhstan", "lat": 43.80, "lon": 75.53, "age": "3,000 years",
     "description": "5,000 petroglyphs in a dramatic gorge. Sun-headed deities, chariots, and animal scenes. Central hub of Bronze Age steppe culture. UNESCO World Heritage Site.", "type": "Petroglyphs", "color": "#8b5cf6"},
    {"name": "Laas Geel", "location": "Somaliland", "lat": 9.78, "lon": 44.47, "age": "5,000 years",
     "description": "Remarkably preserved cave paintings of cattle, wild animals, and humans in ceremonial garb. Discovered in 2002. Among Africa's best-preserved Neolithic rock art.", "type": "Cave Painting", "color": "#f97316"},
]

# ═══════════════════════════════════════════════════════════════
# 6. SCULPTURE PARKS
# ═══════════════════════════════════════════════════════════════
SCULPTURE_PARKS = [
    {"name": "Vigeland Sculpture Park", "city": "Oslo, Norway", "lat": 59.9269, "lon": 10.7003, "sculptures": 212,
     "artist": "Gustav Vigeland", "area_ha": 32, "description": "Single-artist park with 212 bronze and granite sculptures depicting the human life cycle. The Monolith (17m tall, 121 intertwined bodies) is its centerpiece. Free and open 24/7.", "color": "#06b6d4"},
    {"name": "Storm King Art Center", "city": "New Windsor, New York, USA", "lat": 41.4263, "lon": -74.0561, "sculptures": 100,
     "artist": "Multiple", "area_ha": 200, "description": "500 rolling acres in Hudson Valley. Maya Lin's Storm King Wavefield, Calder's The Arch, Goldsworthy's Stone Wall. America's premier outdoor sculpture museum.", "color": "#ef4444"},
    {"name": "Hakone Open-Air Museum", "city": "Hakone, Japan", "lat": 35.2356, "lon": 139.0543, "sculptures": 120,
     "artist": "Multiple", "area_ha": 7, "description": "Japan's first open-air museum (1969). Picasso Pavilion with 300+ works. Henry Moore, Niki de Saint Phalle. Mountain backdrop with hot spring foot bath.", "color": "#ec4899"},
    {"name": "Yorkshire Sculpture Park", "city": "West Bretton, UK", "lat": 53.6113, "lon": -1.5801, "sculptures": 80,
     "artist": "Multiple", "area_ha": 200, "description": "Henry Moore's birthplace county. Hepworth, Goldsworthy, Ai Weiwei, Jaume Plensa installations in 500 acres of 18th-century parkland. Underground gallery for large works.", "color": "#8b5cf6"},
    {"name": "Inhotim", "city": "Brumadinho, Minas Gerais, Brazil", "lat": -20.1214, "lon": -44.2206, "sculptures": 500,
     "artist": "Multiple", "area_ha": 140, "description": "World's largest open-air contemporary art museum set in botanical gardens. Yayoi Kusama's Narcissus Garden, Olafur Eliasson, Cildo Meireles, Adriana Varejao. Tropical setting.", "color": "#10b981"},
    {"name": "Gibbs Farm", "city": "Kaipara Harbour, New Zealand", "lat": -36.42, "lon": 174.41, "sculptures": 30,
     "artist": "Multiple", "area_ha": 400, "description": "Private 1000-acre sculpture park with monumental works. Anish Kapoor's Dismemberment, Richard Serra's Te Tuhirangi Contour, Leon van den Eijkel's Electrum. Open select days.", "color": "#f59e0b"},
    {"name": "Kroller-Muller Museum & Garden", "city": "Otterlo, Netherlands", "lat": 52.0958, "lon": 5.8164, "sculptures": 160,
     "artist": "Multiple", "area_ha": 25, "description": "Europe's largest sculpture garden in Hoge Veluwe National Park. Rodin, Dubuffet, Oldenburg. Also houses Van Gogh's second-largest collection. Explore by free white bicycle.", "color": "#3b82f6"},
    {"name": "Chianti Sculpture Park", "city": "Pievasciata, Tuscany, Italy", "lat": 43.3833, "lon": 11.3833, "sculptures": 30,
     "artist": "Multiple", "area_ha": 7, "description": "Site-specific works in Tuscan woodland. International artists respond to the Mediterranean landscape. Soundscapes, labyrinths, and reflective pools among olive groves and oaks.", "color": "#f97316"},
    {"name": "Jerash Sculpture Park", "city": "Jerash, Jordan", "lat": 32.2747, "lon": 35.8911, "sculptures": 20,
     "artist": "Multiple", "area_ha": 3, "description": "Contemporary sculptures among 2000-year-old Roman ruins. Dialogue between ancient and modern art in one of the best-preserved Roman provincial cities.", "color": "#a855f7"},
    {"name": "Changchun World Sculpture Park", "city": "Changchun, China", "lat": 43.8333, "lon": 125.3500, "sculptures": 450,
     "artist": "Multiple", "area_ha": 92, "description": "One of the world's largest sculpture parks with 450+ works from 200+ countries. Annual international sculpture symposium. Set around lakes and pine forests.", "color": "#14b8a6"},
    {"name": "Decordova Sculpture Park", "city": "Lincoln, Massachusetts, USA", "lat": 42.4375, "lon": -71.3042, "sculptures": 60,
     "artist": "Multiple", "area_ha": 12, "description": "New England's largest sculpture park on a hilltop overlooking Flint's Pond. Rotating exhibitions from emerging and mid-career artists. Free grounds access.", "color": "#38bdf8"},
    {"name": "Ekebergparken", "city": "Oslo, Norway", "lat": 59.9017, "lon": 10.7717, "sculptures": 40,
     "artist": "Multiple", "area_ha": 26, "description": "Sculpture park on the hillside above Oslo where Munch painted The Scream. Renoir, Rodin, Dali, Damien Hirst, Jenny Holzer. Spectacular fjord views.", "color": "#fbbf24"},
    {"name": "Jupiter Artland", "city": "Edinburgh, Scotland", "lat": 55.8903, "lon": -3.4517, "sculptures": 35,
     "artist": "Multiple", "area_ha": 40, "description": "Award-winning sculpture park in woodland near Edinburgh. Charles Jencks' Cells of Life landforms, Antony Gormley, Anish Kapoor, Cornelia Parker.", "color": "#d946ef"},
    {"name": "Benesse Art Site Naoshima", "city": "Naoshima Island, Japan", "lat": 34.4606, "lon": 133.9950, "sculptures": 20,
     "artist": "Multiple", "area_ha": 800, "description": "Entire island transformed into art destination. Yayoi Kusama's Yellow Pumpkin, Tadao Ando's museums, James Turrell's Backside of the Moon. Art embedded in landscape and architecture.", "color": "#ec4899"},
]

# ═══════════════════════════════════════════════════════════════
# 7. PHOTOGRAPHY LANDMARKS
# ═══════════════════════════════════════════════════════════════
PHOTO_LANDMARKS = [
    {"name": "Eiffel Tower", "city": "Paris, France", "lat": 48.8584, "lon": 2.2945, "photos_est": "500M+",
     "description": "Most photographed monument in the world. Nighttime light displays are copyrighted (since 2003). 7 million visitors annually, each averaging 50+ photos.", "category": "Monument", "color": "#f59e0b"},
    {"name": "Times Square", "city": "New York, USA", "lat": 40.7580, "lon": -73.9855, "photos_est": "400M+",
     "description": "50 million visitors/year in the 'Crossroads of the World'. Neon billboards create the world's most recognizable urban backdrop.", "category": "Urban", "color": "#ef4444"},
    {"name": "Taj Mahal", "city": "Agra, India", "lat": 27.1751, "lon": 78.0421, "photos_est": "300M+",
     "description": "Shah Jahan's marble mausoleum for Mumtaz Mahal. Dawn shots from across the Yamuna River are iconic. 8 million visitors annually.", "category": "Monument", "color": "#06b6d4"},
    {"name": "Machu Picchu", "city": "Cusco Region, Peru", "lat": -13.1631, "lon": -72.5450, "photos_est": "200M+",
     "description": "Inca citadel at 2,430m elevation. Misty sunrise shots from the Sun Gate are most coveted. Limited to 2,500 visitors/day.", "category": "Archaeological", "color": "#10b981"},
    {"name": "Santorini Caldera", "city": "Santorini, Greece", "lat": 36.4618, "lon": 25.3753, "photos_est": "250M+",
     "description": "White-washed villages and blue domes against the Aegean Sea. Oia sunset is the most photographed sunset on Earth. Instagram's most-posted island.", "category": "Landscape", "color": "#3b82f6"},
    {"name": "Grand Canyon", "city": "Arizona, USA", "lat": 36.1069, "lon": -112.1129, "photos_est": "200M+",
     "description": "277 miles of layered red rock. Mather Point and Toroweap Overlook provide the classic vistas. 6 million visitors annually.", "category": "Natural", "color": "#f97316"},
    {"name": "Colosseum", "city": "Rome, Italy", "lat": 41.8902, "lon": 12.4922, "photos_est": "300M+",
     "description": "Flavian Amphitheatre (80 CE) — the eternal icon of Rome. Night illumination shots and interior hypogeum views are most popular.", "category": "Monument", "color": "#ec4899"},
    {"name": "Great Wall of China — Badaling", "city": "Beijing, China", "lat": 40.3588, "lon": 116.0201, "photos_est": "350M+",
     "description": "Most-visited section of the 21,196 km wall. The serpentine wall disappearing into misty mountains is photography's most reproduced landscape.", "category": "Monument", "color": "#ef4444"},
    {"name": "Golden Gate Bridge", "city": "San Francisco, USA", "lat": 37.8199, "lon": -122.4783, "photos_est": "200M+",
     "description": "Art Deco international orange bridge in fog. Battery Spencer viewpoint provides the classic shot. Karl the Fog adds mystique.", "category": "Architecture", "color": "#f59e0b"},
    {"name": "Angkor Wat", "city": "Siem Reap, Cambodia", "lat": 13.4125, "lon": 103.8670, "photos_est": "150M+",
     "description": "World's largest religious monument. Sunrise reflected in the lotus pond is the definitive shot. Tree roots consuming Ta Prohm equally iconic.", "category": "Archaeological", "color": "#8b5cf6"},
    {"name": "Shibuya Crossing", "city": "Tokyo, Japan", "lat": 35.6595, "lon": 139.7004, "photos_est": "200M+",
     "description": "World's busiest pedestrian crossing. Up to 3,000 people cross simultaneously. Best shot from Starbucks above or the Magnet building rooftop.", "category": "Urban", "color": "#a855f7"},
    {"name": "Northern Lights — Tromso", "city": "Tromso, Norway", "lat": 69.6496, "lon": 18.9560, "photos_est": "100M+",
     "description": "Prime aurora borealis photography location. September-March viewing season. Long exposures capture green, purple, and red curtains of light.", "category": "Natural", "color": "#06b6d4"},
    {"name": "Petra — The Treasury", "city": "Petra, Jordan", "lat": 30.3285, "lon": 35.4414, "photos_est": "100M+",
     "description": "Rose-red Treasury (Al-Khazneh) revealed at the end of the Siq canyon. Night candlelight sessions create magical photos. One of the New Seven Wonders.", "category": "Archaeological", "color": "#14b8a6"},
    {"name": "Christ the Redeemer", "city": "Rio de Janeiro, Brazil", "lat": -22.9519, "lon": -43.2105, "photos_est": "150M+",
     "description": "30m Art Deco statue atop Corcovado mountain. Aerial drone shots and misty sunrise photos dominate social media. 2 million visitors/year.", "category": "Monument", "color": "#10b981"},
    {"name": "Victoria Peak", "city": "Hong Kong", "lat": 22.2759, "lon": 114.1455, "photos_est": "150M+",
     "description": "The quintessential Hong Kong skyline shot. Blue-hour photography of neon-lit skyscrapers and Victoria Harbour from the Peak is a rite of passage.", "category": "Urban", "color": "#38bdf8"},
    {"name": "Moraine Lake", "city": "Banff, Alberta, Canada", "lat": 51.3217, "lon": -116.1860, "photos_est": "50M+",
     "description": "The turquoise lake backed by ten peaks was featured on Canada's $20 bill. Rockpile trail viewpoint at sunrise. So popular access is now restricted.", "category": "Natural", "color": "#ec4899"},
]

# ═══════════════════════════════════════════════════════════════
# 8. GRAFFITI & URBAN ART
# ═══════════════════════════════════════════════════════════════
GRAFFITI_SITES = [
    {"name": "Wynwood Walls", "city": "Miami, USA", "lat": 25.8009, "lon": -80.1991,
     "description": "Tony Goldman transformed a warehouse district into the world's premier outdoor mural collection in 2009. 80,000 sq ft of walls by Shepard Fairey, Retna, Kenny Scharf, and others. Art Basel Miami anchor.", "type": "Legal Walls", "year": 2009, "color": "#ec4899"},
    {"name": "5Pointz (demolished)", "city": "Queens, New York, USA", "lat": 40.7425, "lon": -73.9293,
     "description": "The 'graffiti mecca' was a 200,000 sq ft factory covered in art by 1,500+ artists from 1993-2013. Whitewashed overnight in 2013; demolished 2014. Artists won $6.7M in court.", "type": "Historical", "year": 1993, "color": "#ef4444"},
    {"name": "Hosier Lane", "city": "Melbourne, Australia", "lat": -37.8166, "lon": 144.9691,
     "description": "Melbourne's most famous laneway. Council-protected graffiti zone since 2000s. Art changes daily — paste-ups, stencils, and spray paint from local and international artists.", "type": "Legal Lane", "year": 2003, "color": "#06b6d4"},
    {"name": "Banksy — Girl with Balloon (original site)", "city": "London, UK", "lat": 51.5063, "lon": -0.0951,
     "description": "Banksy's most iconic stencil first appeared on Waterloo Bridge in 2002. Voted UK's favorite artwork in 2017. The 2018 self-shredding at Sotheby's (now 'Love is in the Bin') sold for $25.4M.", "type": "Banksy", "year": 2002, "color": "#f59e0b"},
    {"name": "Banksy — Bethlehem Wall", "city": "Bethlehem, Palestine", "lat": 31.7054, "lon": 35.2024,
     "description": "Multiple Banksy works on the Israeli West Bank barrier wall. 'Flower Thrower', 'Armoured Dove of Peace', and the Walled Off Hotel (world's worst view). Powerful political statements.", "type": "Banksy", "year": 2005, "color": "#f59e0b"},
    {"name": "Banksy — Dismaland", "city": "Weston-super-Mare, UK", "lat": 51.3472, "lon": -2.9838,
     "description": "A 'bemusement park' — dystopian theme park installation in 2015. Cinderella's crashed pumpkin carriage, migrant boats, CCTV angels. 150,000 visitors in 5 weeks. Materials donated to Calais refugee camp.", "type": "Banksy", "year": 2015, "color": "#f59e0b"},
    {"name": "East Side Gallery", "city": "Berlin, Germany", "lat": 52.5052, "lon": 13.4397,
     "description": "1.3km of Berlin Wall painted by 118 artists from 21 countries in 1990. 'The Kiss' (Brezhnev-Honecker) and 'Test the Best' Trabant murals are most famous. World's largest open-air gallery.", "type": "Historical Wall", "year": 1990, "color": "#8b5cf6"},
    {"name": "Leake Street Tunnel (Banksy Tunnel)", "city": "London, UK", "lat": 51.5023, "lon": -0.1135,
     "description": "300m tunnel under Waterloo Station. Banksy organized the 'Cans Festival' here in 2008. Now a legal graffiti zone repainted constantly. Raw, layered, and always evolving.", "type": "Legal Tunnel", "year": 2008, "color": "#10b981"},
    {"name": "Favela Painting — Santa Marta", "city": "Rio de Janeiro, Brazil", "lat": -22.9434, "lon": -43.1873,
     "description": "Dutch artists Haas & Hahn painted entire favela hillsides in bold geometric patterns. Santa Marta and Vila Cruzeiro projects transformed communities and inspired worldwide favela art.", "type": "Community Art", "year": 2010, "color": "#3b82f6"},
    {"name": "Kelburn Castle Graffiti", "city": "Ayrshire, Scotland", "lat": 55.8558, "lon": -4.9078,
     "description": "A 13th-century castle painted in psychedelic Brazilian graffiti by Os Gemeos and Nina Pandolfo in 2007. The Earl of Glasgow commissioned it while awaiting renovation permits.", "type": "Castle Graffiti", "year": 2007, "color": "#a855f7"},
    {"name": "Ghetto Biennale", "city": "Port-au-Prince, Haiti", "lat": 18.5467, "lon": -72.3389,
     "description": "Biennial art festival in Grand Rue where Haitian sculptors create from recycled materials. Voodoo-inspired art meets international contemporary practice in the poorest urban quarter.", "type": "Festival", "year": 2009, "color": "#f97316"},
    {"name": "Teufelsberg Listening Station", "city": "Berlin, Germany", "lat": 52.4977, "lon": 13.2414,
     "description": "Abandoned Cold War NSA spy station on a man-made hill of WWII rubble. Now covered in world-class graffiti. Radomes (geodesic domes) create unique acoustics for art events.", "type": "Abandoned/Art", "year": 2010, "color": "#38bdf8"},
    {"name": "Comuna 13 — Medellin", "city": "Medellin, Colombia", "lat": 6.2456, "lon": -75.5989,
     "description": "Once the most dangerous neighborhood, now a vibrant street art destination. Outdoor escalators (2011) sparked a rebirth. Murals tell stories of violence, resilience, and hope. Guided graffiti tours.", "type": "Community Art", "year": 2012, "color": "#14b8a6"},
    {"name": "Hamra Street Murals", "city": "Beirut, Lebanon", "lat": 33.8938, "lon": 35.4868,
     "description": "Post-civil-war graffiti culture transformed Beirut. Yazan Halwani's Arabic calligraphy portraits and Ashekman's 'Peace' mural visible from space. Art as healing and resistance.", "type": "Political Art", "year": 2014, "color": "#ec4899"},
]

# ═══════════════════════════════════════════════════════════════
# 9. ART MARKETS & AUCTIONS
# ═══════════════════════════════════════════════════════════════
ART_MARKETS = [
    {"name": "Christie's — King Street", "city": "London, UK", "lat": 51.5079, "lon": -0.1375, "founded": 1766,
     "description": "World's oldest fine art auctioneer. Record sale: Leonardo's Salvator Mundi for $450.3M (2017). Annual sales exceed $7 billion. King Street headquarters since 1823.", "type": "Auction House", "color": "#ef4444"},
    {"name": "Sotheby's — New Bond Street", "city": "London, UK", "lat": 51.5113, "lon": -0.1430, "founded": 1744,
     "description": "The oldest auctioneer (originally books). Notable: Banksy's self-shredding 'Love is in the Bin' ($25.4M). York Avenue NYC gallery is equally iconic.", "type": "Auction House", "color": "#06b6d4"},
    {"name": "Sotheby's — York Avenue", "city": "New York, USA", "lat": 40.7620, "lon": -73.9607, "founded": 1744,
     "description": "American headquarters. Warhol's Shot Sage Blue Marilyn sold here for $195M (2022), the most expensive American artwork. Contemporary art market epicenter.", "type": "Auction House", "color": "#06b6d4"},
    {"name": "Art Basel — Basel", "city": "Basel, Switzerland", "lat": 47.5580, "lon": 7.5826, "founded": 1970,
     "description": "The world's premier art fair. 200+ galleries from 30+ countries. Messe Basel venue designed by Herzog & de Meuron. Annual attendance 90,000+. Defines market trends.", "type": "Art Fair", "color": "#8b5cf6"},
    {"name": "Art Basel — Miami Beach", "city": "Miami, USA", "lat": 25.7959, "lon": -80.1305, "founded": 2002,
     "description": "December fair anchoring Miami Art Week. 280+ galleries, 70,000+ visitors. Wynwood Walls, Design District, and satellite fairs create a citywide art festival.", "type": "Art Fair", "color": "#8b5cf6"},
    {"name": "Art Basel — Hong Kong", "city": "Hong Kong", "lat": 22.3030, "lon": 114.1601, "founded": 2013,
     "description": "Asia's premier contemporary art fair at the Hong Kong Convention Centre. Gateway for Asian collectors and galleries. 30,000+ visitors. Reflects Asia's booming art market.", "type": "Art Fair", "color": "#8b5cf6"},
    {"name": "Chelsea Gallery District", "city": "New York, USA", "lat": 40.7465, "lon": -74.0014, "founded": 1990,
     "description": "300+ galleries between 18th-28th Streets west of 10th Avenue. Gagosian, David Zwirner, Pace, Hauser & Wirth. Thursday openings are a weekly art event. Global market hub.", "type": "Gallery District", "color": "#ec4899"},
    {"name": "Marais Gallery District", "city": "Paris, France", "lat": 48.8583, "lon": 2.3594, "founded": 1970,
     "description": "100+ galleries in the historic Marais. Galerie Perrotin, Thaddaeus Ropac, Templon. Rue de Turenne and Rue Debelleyme are the main corridors. FIAC week peaks activity.", "type": "Gallery District", "color": "#f59e0b"},
    {"name": "Frieze London", "city": "London, UK", "lat": 51.5099, "lon": -0.1750, "founded": 2003,
     "description": "Regent's Park tent hosts 160+ galleries each October. Frieze Masters (historical) runs alongside. Sculpture Park in the gardens. 60,000+ visitors.", "type": "Art Fair", "color": "#10b981"},
    {"name": "Venice Biennale — Arsenale/Giardini", "city": "Venice, Italy", "lat": 45.4298, "lon": 12.3560, "founded": 1895,
     "description": "The Olympics of the art world. 90 national pavilions every two years (odd years). Arsenale and Giardini venues plus 100+ collateral exhibitions across the city. 800,000+ visitors.", "type": "Biennale", "color": "#f97316"},
    {"name": "Documenta", "city": "Kassel, Germany", "lat": 51.3127, "lon": 9.4797, "founded": 1955,
     "description": "Every 5 years (quinquennial), Kassel becomes contemporary art's think tank. 100 days, 1M+ visitors. More intellectual than commercial — 'museum of 100 days'. Documenta 15 (2022) was controversial.", "type": "Exhibition", "color": "#a855f7"},
    {"name": "Phillips — Berkeley Square", "city": "London, UK", "lat": 51.5096, "lon": -0.1474, "founded": 1796,
     "description": "Third-largest auction house. Specializes in 20th/21st-century art, design, watches, and jewelry. Record Basquiat and Richter sales. Growing Asian presence.", "type": "Auction House", "color": "#3b82f6"},
    {"name": "798 Art District", "city": "Beijing, China", "lat": 39.9847, "lon": 116.4946, "founded": 2002,
     "description": "Former military electronics factory transformed into China's contemporary art hub. UCCA, Pace Beijing, and 400+ studios/galleries. Bauhaus-style architecture. Center of Chinese art market.", "type": "Art District", "color": "#14b8a6"},
    {"name": "Al Quoz / Alserkal Avenue", "city": "Dubai, UAE", "lat": 25.1413, "lon": 55.2233, "founded": 2007,
     "description": "Middle East's premier gallery district in industrial Al Quoz. 70+ creative spaces. Art Dubai fair complements. $1B+ annual art transactions in the UAE.", "type": "Art District", "color": "#38bdf8"},
    {"name": "Sao Paulo Bienal — Ibirapuera", "city": "Sao Paulo, Brazil", "lat": -23.5874, "lon": -46.6576, "founded": 1951,
     "description": "Second-oldest biennale (after Venice). Oscar Niemeyer's Pavilion in Ibirapuera Park hosts 500,000+ visitors. Latin America's most important art event. Free admission.", "type": "Biennale", "color": "#ec4899"},
    {"name": "Sharjah Biennial", "city": "Sharjah, UAE", "lat": 25.3573, "lon": 55.3956, "founded": 1993,
     "description": "Most significant contemporary art event in the Arab world. Al Mureijah Art Spaces and heritage buildings as venues. Focus on artists from Africa, Asia, and the Middle East.", "type": "Biennale", "color": "#fbbf24"},
]

# ═══════════════════════════════════════════════════════════════
# 10. BODY MODIFICATION TRADITIONS
# ═══════════════════════════════════════════════════════════════
BODY_MODIFICATIONS = [
    {"name": "Kayan Neck Rings", "location": "Myanmar/Thailand border", "lat": 19.60, "lon": 97.50, "tradition": "Neck Elongation",
     "description": "Kayan (Padaung) women wear brass coils from age 5, adding rings over years. Coils push down clavicle and ribs rather than stretching the neck. Now primarily maintained for tourism and identity.", "origin": "Kayan people, Myanmar", "color": "#f59e0b"},
    {"name": "Mursi Lip Plates", "location": "Omo Valley, Ethiopia", "lat": 5.76, "lon": 36.47, "tradition": "Lip Plates (Dhebi a Tugoin)",
     "description": "Mursi and Suri women insert clay or wooden plates into lower lips. Larger plates indicate higher bride price. Teeth removed to accommodate. Practice declining among younger generation.", "origin": "Mursi/Suri peoples", "color": "#ef4444"},
    {"name": "Scarification — Nuba Mountains", "location": "South Kordofan, Sudan", "lat": 11.70, "lon": 30.50, "tradition": "Scarification",
     "description": "Nuba peoples create raised keloid patterns by cutting skin and introducing ash or plant matter. Designs mark tribal affiliation, coming of age, and beauty. Each group has distinctive patterns.", "origin": "Nuba peoples, Sudan", "color": "#ec4899"},
    {"name": "Scarification — Sepik River", "location": "Papua New Guinea", "lat": -4.20, "lon": 142.00, "tradition": "Crocodile Scarification",
     "description": "Young men undergo initiation in spirit houses (haus tambaran). Skin is cut hundreds of times and packed with clay to create raised scars resembling crocodile scales, honoring the creation ancestor.", "origin": "Sepik River peoples", "color": "#ec4899"},
    {"name": "Maori Ta Moko (Face Tattoo)", "location": "New Zealand", "lat": -41.29, "lon": 174.78, "tradition": "Ta Moko",
     "description": "Chiseled (not punctured) facial tattoos unique to Maori men and women. Each moko is unique, encoding whakapapa, iwi, and mana. Now experiencing powerful revival as cultural assertion.", "origin": "Maori, Aotearoa", "color": "#06b6d4"},
    {"name": "Chinese Foot Binding (Historical)", "location": "Southern China", "lat": 30.57, "lon": 114.27, "tradition": "Foot Binding",
     "description": "Girls' feet bound from age 4-9 to achieve 3-inch 'golden lotus'. Practiced for 1,000 years (10th-20th century). Symbol of beauty and status. Banned 1912. Last generation died in early 2000s.", "origin": "Song Dynasty China", "color": "#8b5cf6"},
    {"name": "Ear Stretching — Maasai", "location": "Serengeti, Tanzania/Kenya", "lat": -2.33, "lon": 34.83, "tradition": "Ear Stretching/Piercing",
     "description": "Maasai men and women stretch earlobes with progressively larger wooden or stone plugs. Beaded ear ornaments signify age, marital status, and social position. Both ears and cartilage are modified.", "origin": "Maasai people", "color": "#10b981"},
    {"name": "Nose Piercing — India", "location": "Rajasthan, India", "lat": 26.92, "lon": 75.79, "tradition": "Nath (Nose Ring)",
     "description": "Nose piercing (left nostril) has been practiced for 4,000+ years. The nath (large ornamental nose ring) is essential bridal jewelry. Connected to Ayurvedic belief about easing childbirth pain.", "origin": "South Asian subcontinent", "color": "#f97316"},
    {"name": "Teeth Filing — Bali", "location": "Bali, Indonesia", "lat": -8.65, "lon": 115.22, "tradition": "Metatah (Tooth Filing)",
     "description": "Balinese Hindu coming-of-age ceremony where upper canines and incisors are filed flat. Symbolizes controlling the six enemies (desire, greed, anger, confusion, jealousy, intoxication).", "origin": "Balinese Hindu tradition", "color": "#a855f7"},
    {"name": "Skull Shaping — Paracas", "location": "Paracas, Peru", "lat": -13.84, "lon": -76.25, "tradition": "Cranial Modification",
     "description": "Paracas culture (800 BCE-100 BCE) practiced cranial deformation by binding infants' heads. Elongated skulls found in cemeteries. Also practiced by Maya, Huns, and Toulouse in France.", "origin": "Paracas culture, Peru", "color": "#3b82f6"},
    {"name": "Lip Tattoo — Ainu", "location": "Hokkaido, Japan", "lat": 42.92, "lon": 141.35, "tradition": "Sinuye (Lip Tattoo)",
     "description": "Ainu women received gradual lip tattoos (sinuye) from childhood to marriage. Soot from birch bark was rubbed into knife cuts. The mouth designs resembled a permanent smile. Banned by Japan in 1871.", "origin": "Ainu people, Japan", "color": "#14b8a6"},
    {"name": "Henna/Mehndi Traditions", "location": "Rajasthan, India", "lat": 27.18, "lon": 75.79, "tradition": "Mehndi",
     "description": "Temporary body art using henna paste. Bridal mehndi is elaborate, covering hands to elbows. Tradition shared across South Asia, Middle East, and North Africa. 5,000+ year history.", "origin": "India/Middle East/North Africa", "color": "#fbbf24"},
    {"name": "Neck Stretching — Ndebele", "location": "Mpumalanga, South Africa", "lat": -25.55, "lon": 29.53, "tradition": "Idzila (Neck/Limb Rings)",
     "description": "Ndebele women wear idzila (copper/brass rings) on necks, arms, and legs. Given by husband after marriage. Rings signify wealth and faithfulness. Distinctive beadwork accompanies the rings.", "origin": "Ndebele people, South Africa", "color": "#d946ef"},
    {"name": "Tongue Splitting (Modern)", "location": "Austin, Texas, USA", "lat": 30.27, "lon": -97.74, "tradition": "Tongue Bifurcation",
     "description": "Modern body modification where the tongue is bisected. Popularized in the late 1990s by Erik Sprague ('The Lizardman'). Each half can be moved independently. Legal status varies.", "origin": "Modern body modification movement", "color": "#38bdf8"},
    {"name": "Subdermal Implants (Modern)", "location": "Los Angeles, USA", "lat": 34.05, "lon": -118.24, "tradition": "Subdermal Implants",
     "description": "Silicone shapes inserted under skin to create 3D effects — horns, ridges, stars. Steve Haworth pioneered the technique in the 1990s. Part of the transhumanist/body mod community.", "origin": "Modern body modification (1990s)", "color": "#fb923c"},
]


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def _build_folium_map(data, lat_key="lat", lon_key="lon", name_key="name",
                      color_key="color", popup_fields=None, zoom=2, center=None):
    """Build a dark-themed Folium map from a list of dicts."""
    if center is None:
        avg_lat = np.mean([d[lat_key] for d in data])
        avg_lon = np.mean([d[lon_key] for d in data])
        center = [avg_lat, avg_lon]

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    for item in data:
        popup_html = f"<div style='font-family:sans-serif;max-width:300px;'>"
        popup_html += f"<b style='font-size:14px;color:#0a0e1a;'>{escape(str(item.get(name_key, '')))}</b><br>"
        if popup_fields:
            for field_label, field_key in popup_fields:
                val = item.get(field_key, "")
                if val:
                    popup_html += f"<b>{escape(str(field_label))}:</b> {escape(str(val))}<br>"
        popup_html += "</div>"

        folium.CircleMarker(
            location=[item[lat_key], item[lon_key]],
            radius=8,
            color=item.get(color_key, ACCENT_CYAN),
            fill=True,
            fill_color=item.get(color_key, ACCENT_CYAN),
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=escape(str(item.get(name_key, ""))),
        ).add_to(m)

    return m


def _render_map(m, height=500):
    """Render a folium map in Streamlit."""
    components.html(m._repr_html_(), height=height)


def _make_download_button(df, filename, label="Download CSV"):
    """Create a CSV download button."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    st.download_button(label, buf.getvalue(), file_name=filename,
                       mime="text/csv", key=f"dl_{filename}")


def _plot_bar_chart(labels, values, title, xlabel, ylabel, color=ACCENT_CYAN, horizontal=False):
    """Create a styled bar chart."""
    fig, ax = plt.subplots(figsize=(10, max(4, len(labels) * 0.4) if horizontal else 5))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    if horizontal:
        bars = ax.barh(labels, values, color=color, edgecolor=color, alpha=0.8)
        ax.set_xlabel(xlabel, color=TEXT_COLOR, fontsize=11)
        ax.set_ylabel(ylabel, color=TEXT_COLOR, fontsize=11)
    else:
        bars = ax.bar(labels, values, color=color, edgecolor=color, alpha=0.8)
        ax.set_xlabel(xlabel, color=TEXT_COLOR, fontsize=11)
        ax.set_ylabel(ylabel, color=TEXT_COLOR, fontsize=11)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(title, color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(colors=TEXT_COLOR, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x" if horizontal else "y", alpha=0.15, color="#2a3550")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# INDIVIDUAL MODE RENDERERS
# ═══════════════════════════════════════════════════════════════

def _render_tattoo_cultures():
    """Mode 1: Traditional Tattoo Cultures."""
    st.markdown("### Traditional Tattoo Cultures Worldwide")
    st.markdown(
        "Explore the sacred and ancient tattoo traditions that have marked human "
        "bodies for millennia. From Polynesian tatau to Japanese irezumi, these "
        "living traditions connect people to ancestry, spirituality, and identity."
    )

    # Filter by tradition
    traditions = sorted(set(t["tradition"] for t in TATTOO_CULTURES))
    selected = st.multiselect("Filter by tradition", traditions, default=traditions,
                              key="tattoo_tradition_filter")
    filtered = [t for t in TATTOO_CULTURES if t["tradition"] in selected]

    if not filtered:
        st.warning("No traditions selected. Please choose at least one.")
        return

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Traditions", len(traditions))
    col2.metric("Sites Mapped", len(filtered))
    col3.metric("Oldest Tradition", "4000+ yrs")
    col4.metric("Continents", "6")

    # Map
    popup_fields = [
        ("Tradition", "tradition"),
        ("Period", "period"),
        ("Technique", "technique"),
        ("Details", "description"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=2)
    _render_map(m, height=520)

    # Chart — count by tradition
    trad_counts = {}
    for t in filtered:
        trad_counts[t["tradition"]] = trad_counts.get(t["tradition"], 0) + 1
    sorted_trads = sorted(trad_counts.items(), key=lambda x: x[1], reverse=True)
    _plot_bar_chart(
        [t[0] for t in sorted_trads], [t[1] for t in sorted_trads],
        "Sites per Tattoo Tradition", "Tradition", "Sites",
        color=ACCENT_CYAN, horizontal=True,
    )

    # Data table
    df = pd.DataFrame(filtered)
    display_cols = ["name", "tradition", "period", "technique", "description"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "tattoo_cultures.csv")


def _render_street_art():
    """Mode 2: Street Art Capitals."""
    st.markdown("### Street Art Capitals of the World")
    st.markdown(
        "The world's greatest cities for street art, murals, and urban creativity. "
        "From Berlin's East Side Gallery to Melbourne's ever-changing laneways, "
        "these cities have embraced the walls as canvas."
    )

    filtered = STREET_ART_CITIES

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Cities Mapped", len(filtered))
    col2.metric("Top Score", f"{max(c['score'] for c in filtered)}/100")
    col3.metric("Continents", "6")
    col4.metric("Avg Score", f"{np.mean([c['score'] for c in filtered]):.0f}/100")

    popup_fields = [
        ("Highlights", "highlights"),
        ("Notable Artists", "notable_artists"),
        ("Score", "score"),
        ("Details", "description"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=2)
    _render_map(m, height=520)

    # Chart — scores
    sorted_cities = sorted(filtered, key=lambda x: x["score"], reverse=True)
    _plot_bar_chart(
        [c["name"] for c in sorted_cities], [c["score"] for c in sorted_cities],
        "Street Art Capital Rankings", "City", "Score (/100)",
        color=ACCENT_PINK, horizontal=True,
    )

    df = pd.DataFrame(filtered)
    display_cols = ["name", "score", "highlights", "notable_artists", "description"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "street_art_capitals.csv")


def _render_museums():
    """Mode 3: World's Greatest Museums."""
    st.markdown("### World's Greatest Museums")
    st.markdown(
        "From the Louvre's 380,000 works to the Smithsonian's 155 million objects, "
        "these institutions preserve humanity's artistic and cultural heritage. "
        "Spanning six continents, they are temples of human creativity."
    )

    # Filter by type
    types = sorted(set(m["type"] for m in MUSEUMS))
    selected_types = st.multiselect("Filter by museum type", types, default=types,
                                    key="museum_type_filter")
    filtered = [m for m in MUSEUMS if m["type"] in selected_types]

    if not filtered:
        st.warning("No museum types selected.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Museums", len(filtered))
    col2.metric("Total Visitors/yr", f"{sum(m['visitors_m'] for m in filtered):.1f}M")
    col3.metric("Oldest", f"{min(m['founded'] for m in filtered)}")
    col4.metric("Countries", len(set(m["city"].split(", ")[-1] for m in filtered)))

    popup_fields = [
        ("City", "city"),
        ("Founded", "founded"),
        ("Annual Visitors", "visitors_m"),
        ("Collection", "collection_size"),
        ("Highlights", "highlights"),
        ("Type", "type"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=2)
    _render_map(m, height=520)

    # Chart — visitors
    sorted_mus = sorted(filtered, key=lambda x: x["visitors_m"], reverse=True)[:20]
    _plot_bar_chart(
        [m["name"] for m in sorted_mus], [m["visitors_m"] for m in sorted_mus],
        "Top Museums by Annual Visitors (millions)", "Museum", "Visitors (M)",
        color=ACCENT_VIOLET, horizontal=True,
    )

    df = pd.DataFrame(filtered)
    display_cols = ["name", "city", "founded", "visitors_m", "collection_size", "type", "highlights"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "world_museums.csv")


def _render_art_movements():
    """Mode 4: Art Movements Origins."""
    st.markdown("### Art Movements — Where They Were Born")
    st.markdown(
        "Every revolution in art started somewhere specific: a studio, a cafe, a city. "
        "This map traces the geographic origins of major art movements from the "
        "Renaissance to Land Art, revealing how places shaped artistic vision."
    )

    filtered = ART_MOVEMENTS

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Movements", len(filtered))
    col2.metric("Earliest", "1400 CE")
    col3.metric("Countries", len(set(m["city"].split(", ")[-1] for m in filtered)))
    col4.metric("Span", "600+ years")

    popup_fields = [
        ("City", "city"),
        ("Period", "period"),
        ("Key Artists", "key_artists"),
        ("Details", "description"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=3,
                          center=[45, 5])
    _render_map(m, height=520)

    # Timeline chart
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(BG_COLOR)
    ax.set_facecolor(SURFACE_COLOR)

    for i, mvt in enumerate(filtered):
        period = mvt["period"]
        try:
            parts = period.replace("s", "").split("-")
            start = int(parts[0])
            end = int(parts[1]) if len(parts) > 1 else start + 50
        except (ValueError, IndexError):
            start, end = 1900, 1950

        color = mvt.get("color", ACCENT_CYAN)
        ax.barh(i, end - start, left=start, height=0.6, color=color, alpha=0.8,
                edgecolor=color)
        ax.text(start - 5, i, escape(mvt["name"]), ha="right", va="center",
                color=TEXT_COLOR, fontsize=8, fontweight="bold")

    ax.set_xlabel("Year", color=TEXT_COLOR, fontsize=11)
    ax.set_title("Art Movements Timeline", color=TEXT_COLOR, fontsize=14,
                 fontweight="bold", pad=12)
    ax.set_yticks([])
    ax.tick_params(colors=TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", alpha=0.15, color="#2a3550")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame(filtered)
    display_cols = ["name", "city", "period", "key_artists", "description"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "art_movements.csv")


def _render_ancient_art():
    """Mode 5: Ancient Art Sites."""
    st.markdown("### Ancient Art Sites Worldwide")
    st.markdown(
        "From Lascaux's 17,000-year-old cave paintings to the Nazca Lines visible "
        "only from the sky, these sites prove that art is humanity's oldest language. "
        "Petroglyphs, cave paintings, and geoglyphs spanning 40,000 years."
    )

    # Filter by type
    art_types = sorted(set(a["type"] for a in ANCIENT_ART))
    selected_types = st.multiselect("Filter by art type", art_types, default=art_types,
                                    key="ancient_art_type_filter")
    filtered = [a for a in ANCIENT_ART if a["type"] in selected_types]

    if not filtered:
        st.warning("No art types selected.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sites", len(filtered))
    col2.metric("Oldest", "40,000 yrs")
    col3.metric("Art Types", len(art_types))
    col4.metric("Continents", "6")

    popup_fields = [
        ("Location", "location"),
        ("Age", "age"),
        ("Type", "type"),
        ("Details", "description"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=2)
    _render_map(m, height=520)

    # Chart by type
    type_counts = {}
    for a in filtered:
        type_counts[a["type"]] = type_counts.get(a["type"], 0) + 1
    sorted_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    _plot_bar_chart(
        [t[0] for t in sorted_types], [t[1] for t in sorted_types],
        "Ancient Art Sites by Type", "Type", "Sites",
        color=ACCENT_AMBER, horizontal=True,
    )

    df = pd.DataFrame(filtered)
    display_cols = ["name", "location", "age", "type", "description"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "ancient_art_sites.csv")


def _render_sculpture_parks():
    """Mode 6: Sculpture Parks."""
    st.markdown("### Sculpture Parks of the World")
    st.markdown(
        "Where art meets landscape. These outdoor museums place sculptures by the "
        "world's greatest artists in natural settings — from Norwegian fjords to "
        "Brazilian botanical gardens and Japanese islands."
    )

    filtered = SCULPTURE_PARKS

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Parks", len(filtered))
    col2.metric("Total Sculptures", f"{sum(p['sculptures'] for p in filtered):,}")
    col3.metric("Total Area", f"{sum(p['area_ha'] for p in filtered):,} ha")
    col4.metric("Countries", len(set(p["city"].split(", ")[-1] for p in filtered)))

    popup_fields = [
        ("City", "city"),
        ("Sculptures", "sculptures"),
        ("Area (ha)", "area_ha"),
        ("Artist(s)", "artist"),
        ("Details", "description"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=2)
    _render_map(m, height=520)

    # Chart — sculpture count
    sorted_parks = sorted(filtered, key=lambda x: x["sculptures"], reverse=True)
    _plot_bar_chart(
        [p["name"] for p in sorted_parks], [p["sculptures"] for p in sorted_parks],
        "Sculpture Parks by Number of Works", "Park", "Sculptures",
        color=ACCENT_EMERALD, horizontal=True,
    )

    df = pd.DataFrame(filtered)
    display_cols = ["name", "city", "sculptures", "area_ha", "artist", "description"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "sculpture_parks.csv")


def _render_photo_landmarks():
    """Mode 7: Photography Landmarks."""
    st.markdown("### Most Photographed Places on Earth")
    st.markdown(
        "From the Eiffel Tower's half-billion photos to Shibuya Crossing's chaotic "
        "beauty, these are the places that define the world's visual culture. "
        "Monuments, landscapes, and urban scenes that everyone wants to capture."
    )

    # Filter by category
    categories = sorted(set(p["category"] for p in PHOTO_LANDMARKS))
    selected_cats = st.multiselect("Filter by category", categories, default=categories,
                                   key="photo_cat_filter")
    filtered = [p for p in PHOTO_LANDMARKS if p["category"] in selected_cats]

    if not filtered:
        st.warning("No categories selected.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Landmarks", len(filtered))
    col2.metric("Categories", len(categories))
    col3.metric("Most Photographed", "Eiffel Tower")
    col4.metric("Continents", "6")

    popup_fields = [
        ("City", "city"),
        ("Est. Photos", "photos_est"),
        ("Category", "category"),
        ("Details", "description"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=2)
    _render_map(m, height=520)

    # Chart by category
    cat_counts = {}
    for p in filtered:
        cat_counts[p["category"]] = cat_counts.get(p["category"], 0) + 1
    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)
    _plot_bar_chart(
        [c[0] for c in sorted_cats], [c[1] for c in sorted_cats],
        "Photography Landmarks by Category", "Category", "Count",
        color=ACCENT_ORANGE, horizontal=True,
    )

    df = pd.DataFrame(filtered)
    display_cols = ["name", "city", "photos_est", "category", "description"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "photography_landmarks.csv")


def _render_graffiti():
    """Mode 8: Graffiti & Urban Art."""
    st.markdown("### Graffiti & Urban Art Landmarks")
    st.markdown(
        "From Banksy's provocations to Miami's Wynwood Walls, graffiti has evolved "
        "from vandalism to a billion-dollar art form. These sites mark where walls "
        "became canvases and spray cans became brushes."
    )

    # Filter by type
    types = sorted(set(g["type"] for g in GRAFFITI_SITES))
    selected_types = st.multiselect("Filter by type", types, default=types,
                                    key="graffiti_type_filter")
    filtered = [g for g in GRAFFITI_SITES if g["type"] in selected_types]

    if not filtered:
        st.warning("No types selected.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Sites", len(filtered))
    col2.metric("Types", len(types))
    col3.metric("Banksy Sites", len([g for g in GRAFFITI_SITES if "Banksy" in g["type"]]))
    col4.metric("Countries", len(set(g["city"].split(", ")[-1] for g in filtered)))

    popup_fields = [
        ("City", "city"),
        ("Type", "type"),
        ("Year", "year"),
        ("Details", "description"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=2)
    _render_map(m, height=520)

    # Chart — by year
    sorted_sites = sorted(filtered, key=lambda x: x.get("year", 2000))
    _plot_bar_chart(
        [g["name"][:25] for g in sorted_sites], [g.get("year", 2000) for g in sorted_sites],
        "Graffiti Sites by Year Established", "Site", "Year",
        color=ACCENT_RED, horizontal=True,
    )

    df = pd.DataFrame(filtered)
    display_cols = ["name", "city", "type", "year", "description"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "graffiti_urban_art.csv")


def _render_art_markets():
    """Mode 9: Art Markets & Auctions."""
    st.markdown("### Art Markets, Auctions & Fairs")
    st.markdown(
        "The global art market moves over $65 billion annually. From Christie's "
        "record-breaking auctions to Art Basel's trendsetting fairs and Venice's "
        "Biennale, these are the places where art meets commerce."
    )

    # Filter by type
    types = sorted(set(a["type"] for a in ART_MARKETS))
    selected_types = st.multiselect("Filter by venue type", types, default=types,
                                    key="art_market_type_filter")
    filtered = [a for a in ART_MARKETS if a["type"] in selected_types]

    if not filtered:
        st.warning("No venue types selected.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Venues", len(filtered))
    col2.metric("Types", len(types))
    col3.metric("Oldest", f"{min(a['founded'] for a in filtered)}")
    col4.metric("Countries", len(set(a["city"].split(", ")[-1] for a in filtered)))

    popup_fields = [
        ("City", "city"),
        ("Founded", "founded"),
        ("Type", "type"),
        ("Details", "description"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=2)
    _render_map(m, height=520)

    # Chart — by founding year
    sorted_markets = sorted(filtered, key=lambda x: x["founded"])
    _plot_bar_chart(
        [a["name"][:25] for a in sorted_markets], [a["founded"] for a in sorted_markets],
        "Art Market Venues by Year Founded", "Venue", "Year",
        color=ACCENT_BLUE, horizontal=True,
    )

    df = pd.DataFrame(filtered)
    display_cols = ["name", "city", "founded", "type", "description"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "art_markets_auctions.csv")


def _render_body_modifications():
    """Mode 10: Body Modification Traditions."""
    st.markdown("### Body Modification Traditions Worldwide")
    st.markdown(
        "Humans have reshaped their bodies for beauty, identity, and spirituality "
        "for millennia. From Kayan neck rings to Mursi lip plates, from Balinese "
        "tooth filing to modern subdermal implants, the body is the ultimate canvas."
    )

    # Filter by tradition type
    traditions = sorted(set(b["tradition"] for b in BODY_MODIFICATIONS))
    selected = st.multiselect("Filter by modification type", traditions, default=traditions,
                              key="body_mod_filter")
    filtered = [b for b in BODY_MODIFICATIONS if b["tradition"] in selected]

    if not filtered:
        st.warning("No modification types selected.")
        return

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Traditions", len(filtered))
    col2.metric("Unique Types", len(traditions))
    col3.metric("Continents", "6")
    col4.metric("Time Span", "5000+ years")

    popup_fields = [
        ("Location", "location"),
        ("Tradition", "tradition"),
        ("Origin", "origin"),
        ("Details", "description"),
    ]
    m = _build_folium_map(filtered, popup_fields=popup_fields, zoom=2)
    _render_map(m, height=520)

    # Chart — by tradition
    trad_counts = {}
    for b in filtered:
        trad_counts[b["tradition"]] = trad_counts.get(b["tradition"], 0) + 1
    sorted_trads = sorted(trad_counts.items(), key=lambda x: x[1], reverse=True)
    _plot_bar_chart(
        [t[0] for t in sorted_trads], [t[1] for t in sorted_trads],
        "Body Modification Sites by Type", "Tradition", "Sites",
        color=ACCENT_PINK, horizontal=True,
    )

    df = pd.DataFrame(filtered)
    display_cols = ["name", "location", "tradition", "origin", "description"]
    st.dataframe(df[display_cols], width="stretch")
    _make_download_button(df, "body_modifications.csv")


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════

def render_tattoo_maps_tab():
    """Main entry point for the Tattoo, Art & Body Culture Maps tab."""

    st.markdown(
        '<div class="tab-header pink">'
        '<h4>\U0001f3a8 Tattoo, Art & Body Culture Maps</h4>'
        '<p>Tattoo traditions, street art, body painting, art capitals & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Mode selector
    mode = st.selectbox(
        "Select map mode",
        MAP_MODES,
        key="tattoo_maps_mode",
        help="Choose from 10 curated cultural and art maps",
    )

    st.markdown("---")

    # Dispatch to the selected mode
    mode_idx = MAP_MODES.index(mode)

    if mode_idx == 0:
        _render_tattoo_cultures()
    elif mode_idx == 1:
        _render_street_art()
    elif mode_idx == 2:
        _render_museums()
    elif mode_idx == 3:
        _render_art_movements()
    elif mode_idx == 4:
        _render_ancient_art()
    elif mode_idx == 5:
        _render_sculpture_parks()
    elif mode_idx == 6:
        _render_photo_landmarks()
    elif mode_idx == 7:
        _render_graffiti()
    elif mode_idx == 8:
        _render_art_markets()
    elif mode_idx == 9:
        _render_body_modifications()
