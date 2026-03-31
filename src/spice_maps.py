# -*- coding: utf-8 -*-
"""
Spice Routes & Heritage Explorer module for TerraScout AI.
Curated databases of spice islands, historic trade ports, saffron regions,
vanilla heritage, cinnamon trails, pepper empires, chili heat maps,
spice museums, and ancient spice routes with interactive Folium maps.
No API keys required -- all data is curated/embedded.
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
from streamlit.components.v1 import html as st_html
import html as html_module

# ===============================================================================
# THEME CONSTANTS (TerraScout AI dark theme)
# ===============================================================================
_BG = "#0a0e1a"
_SURFACE = "#111827"
_CARD = "#1a2235"
_BORDER = "#2a3550"
_TEXT = "#e8ecf4"
_TEXT2 = "#8b97b0"
_MUTED = "#5a6580"
_ACCENT = "#06b6d4"
_AMBER = "#f59e0b"
_VIOLET = "#8b5cf6"
_EMERALD = "#10b981"
_RED = "#ef4444"
_PINK = "#ec4899"
_ORANGE = "#f97316"
_BLUE = "#3b82f6"
_GOLD = "#eab308"
_TEAL = "#14b8a6"
_CYAN = "#06b6d4"

# ===============================================================================
# MODE OPTIONS
# ===============================================================================
MODE_OPTIONS = [
    "Spice Islands of Indonesia",
    "Indian Spice Markets",
    "Historic Spice Trade Ports",
    "Saffron Growing Regions",
    "Vanilla Heritage",
    "Cinnamon & Cassia",
    "Pepper Empire",
    "Chili Heat Map",
    "Spice Museums & Experiences",
    "Ancient Spice Routes",
]

# ===============================================================================
# MODE DESCRIPTIONS
# ===============================================================================
MODE_DESCRIPTIONS = {
    "Spice Islands of Indonesia": (
        "The legendary Moluccas -- Banda Islands, Ternate, Tidore, and surrounding "
        "isles -- where nutmeg, clove, and mace grew nowhere else on Earth, sparking "
        "centuries of exploration, conquest, and colonial wars."
    ),
    "Indian Spice Markets": (
        "From Kerala's black pepper vines to Kashmir's saffron fields, Rajasthan's "
        "chili bazaars, and Tamil Nadu's cardamom hills, India has been the spice "
        "heartland of the world for over 3,000 years."
    ),
    "Historic Spice Trade Ports": (
        "The great entrepots of the global spice trade: Calicut, Malacca, Aden, "
        "Venice, Lisbon, Amsterdam, and others that grew wealthy channeling the "
        "aromatic treasures of the East to hungry Western markets."
    ),
    "Saffron Growing Regions": (
        "The world's most expensive spice by weight, saffron (Crocus sativus) "
        "thrives in only a handful of arid, high-altitude regions: Kashmir, Iran, "
        "La Mancha, Morocco's Taliouine, and Greek Kozani."
    ),
    "Vanilla Heritage": (
        "From the Totonac people of Papantla, Mexico, who first cultivated vanilla, "
        "to Madagascar's Bourbon vanilla, Tahitian orchids, and Reunion Island -- "
        "the world's second most expensive spice after saffron."
    ),
    "Cinnamon & Cassia": (
        "True Ceylon cinnamon from Sri Lanka versus Chinese cassia, Vietnamese "
        "Saigon cinnamon, and Indonesian Korintje -- the bark that launched the "
        "spice trade and drove European colonialism in South Asia."
    ),
    "Pepper Empire": (
        "Black pepper, once worth its weight in gold, drove the entire Age of "
        "Exploration. From Kerala's Malabar Coast to Sarawak, Kampot, Lampung, "
        "and Brazilian Bahia, pepper remains the king of spices."
    ),
    "Chili Heat Map": (
        "From Capsicum's origins in Mesoamerica to Sichuan's numbing heat, "
        "Assam's Bhut Jolokia ghost peppers, and the Carolina Reaper -- tracing "
        "the global spread of chili peppers and extreme heat culture."
    ),
    "Spice Museums & Experiences": (
        "Museums, spice trails, plantation tours, and sensory experiences "
        "dedicated to the world of spices: Hamburg's Spice Museum, Kerala's "
        "Spice Trail, Zanzibar's spice tours, and more."
    ),
    "Ancient Spice Routes": (
        "The great trade arteries that carried spices across continents for "
        "millennia: the Incense Route, the Maritime Silk Road's spice leg, "
        "the Amber Road, and overland caravan trails through Arabia and Persia."
    ),
}

# ===============================================================================
# MODE ICONS
# ===============================================================================
MODE_ICONS = {
    "Spice Islands of Indonesia": "🏝️",
    "Indian Spice Markets": "🇮🇳",
    "Historic Spice Trade Ports": "⚓",
    "Saffron Growing Regions": "🌸",
    "Vanilla Heritage": "🌿",
    "Cinnamon & Cassia": "🪵",
    "Pepper Empire": "⚫",
    "Chili Heat Map": "🌶️",
    "Spice Museums & Experiences": "🏛️",
    "Ancient Spice Routes": "🐪",
}

# ===============================================================================
# MODE INSIGHTS -- contextual blurbs shown below the download
# ===============================================================================
MODE_INSIGHTS = {
    "Spice Islands of Indonesia": (
        "The Banda Islands were so valuable that the Dutch massacred nearly the "
        "entire indigenous Bandanese population in 1621 to seize control of nutmeg. "
        "Cloves were once worth more than gold by weight in European markets. The "
        "English traded their claim to Pulau Run for Manhattan -- one of history's "
        "most lopsided trades, driven entirely by the value of nutmeg."
    ),
    "Indian Spice Markets": (
        "India produces 75% of the world's spices and consumes 90% of its own output. "
        "The country has been the epicenter of the global spice trade for over 3,000 "
        "years, with ancient Roman coins found in Kerala attesting to the pepper "
        "trade described in the 1st century Periplus of the Erythraean Sea."
    ),
    "Historic Spice Trade Ports": (
        "The spice trade was the original engine of globalization. Venice's wealth was "
        "built on its monopoly of Eastern spices entering Europe. When the Portuguese "
        "found the sea route to India in 1498, they broke that monopoly and shifted "
        "global power from the Mediterranean to the Atlantic seaboard."
    ),
    "Saffron Growing Regions": (
        "It takes 150,000 hand-picked crocus flowers to produce a single kilogram of "
        "saffron, making it the world's most expensive spice at $3,000-$10,000/kg. "
        "Iran dominates production with over 90% of global output. Medieval "
        "Nuremberg burned saffron adulterators at the stake."
    ),
    "Vanilla Heritage": (
        "Vanilla was a Mesoamerican secret for centuries. European attempts to grow it "
        "failed until 1841, when 12-year-old Edmond Albius, enslaved on Reunion Island, "
        "discovered the hand-pollination technique still used today. Madagascar now "
        "produces 80% of the world's vanilla, and a price crash-and-boom cycle "
        "regularly disrupts global markets."
    ),
    "Cinnamon & Cassia": (
        "True Ceylon cinnamon (Cinnamomum verum) and its coarser cousins -- Chinese "
        "cassia, Vietnamese Saigon cinnamon, and Indonesian Korintje -- are distinct "
        "species often sold interchangeably. Ceylon cinnamon is delicate and papery; "
        "cassia is bold and contains coumarin, a compound restricted in the EU."
    ),
    "Pepper Empire": (
        "Black pepper was so valuable in medieval Europe that it was counted out "
        "peppercorn by peppercorn and used as currency. The term 'peppercorn rent' "
        "survives in English law. Alaric the Visigoth demanded 3,000 pounds of "
        "pepper as part of Rome's ransom in 410 CE."
    ),
    "Chili Heat Map": (
        "All chili peppers (Capsicum spp.) originate from the Americas. Columbus "
        "brought them to Europe in 1493 calling them 'peppers' because of their "
        "pungency. Within 50 years, Portuguese traders had spread chilies to Africa, "
        "India, and Southeast Asia. The Carolina Reaper (2.2 million SHU) is the "
        "current world record holder for heat."
    ),
    "Spice Museums & Experiences": (
        "Spice tourism is a growing sector combining gastronomy, history, and "
        "agriculture. Kerala, Zanzibar, and Grenada offer plantation walks where "
        "visitors can smell, touch, and taste spices growing on the vine. Museums "
        "like Hamburg's Spicy's preserve the industrial and colonial heritage of "
        "the global spice trade."
    ),
    "Ancient Spice Routes": (
        "The ancient spice trade connected China to Rome across 8,000 miles. The "
        "Incense Route carried frankincense from Oman to Gaza. The Maritime Silk Road "
        "shipped pepper and cinnamon from India through the Red Sea to Alexandria. "
        "These routes shaped empires, funded wars, and connected civilizations "
        "thousands of years before the word 'globalization' was coined."
    ),
}

# ===============================================================================
# CURATED DATASETS -- 10 modes, 25+ entries each
# ===============================================================================

SPICE_ISLANDS = [
    {"name": "Banda Neira", "lat": -4.5250, "lon": 129.8950, "country": "Indonesia", "spice": "Nutmeg, Mace", "desc": "Heart of the Banda Islands and historic center of the global nutmeg trade. The Dutch East India Company massacred the Bandanese to control nutmeg production.", "color": _AMBER},
    {"name": "Banda Besar (Lontar)", "lat": -4.5400, "lon": 129.8800, "country": "Indonesia", "spice": "Nutmeg", "desc": "Largest of the Banda Islands, covered in nutmeg plantations since the 15th century. Dutch perkeniers (plantation owners) built colonial estates here.", "color": _AMBER},
    {"name": "Pulau Ai", "lat": -4.5200, "lon": 129.7700, "country": "Indonesia", "spice": "Nutmeg", "desc": "Tiny island fought over by Dutch and English for its nutmeg groves. The English traded it for Manhattan in 1667.", "color": _AMBER},
    {"name": "Pulau Run", "lat": -4.5250, "lon": 129.7300, "country": "Indonesia", "spice": "Nutmeg", "desc": "The English-held nutmeg island swapped for New Amsterdam (Manhattan) in the Treaty of Breda, 1667.", "color": _GOLD},
    {"name": "Ternate", "lat": 0.7900, "lon": 127.3700, "country": "Indonesia", "spice": "Clove", "desc": "Volcanic island and historic sultanate, one of the original sources of cloves. Portuguese built Fort Oranje here in 1522.", "color": _RED},
    {"name": "Tidore", "lat": 0.6800, "lon": 127.4000, "country": "Indonesia", "spice": "Clove", "desc": "Rival sultanate to Ternate, allied with the Spanish. Magellan's expedition reached Tidore in 1521.", "color": _RED},
    {"name": "Makian Island", "lat": 0.3200, "lon": 127.4000, "country": "Indonesia", "spice": "Clove", "desc": "Volcanic clove-producing island in the North Maluku chain, south of Ternate and Tidore.", "color": _ORANGE},
    {"name": "Bacan Island", "lat": -0.6700, "lon": 127.5000, "country": "Indonesia", "spice": "Clove, Nutmeg", "desc": "Large island in the Maluku chain where Alfred Russel Wallace collected specimens and studied spice cultivation.", "color": _ORANGE},
    {"name": "Ambon (Amboina)", "lat": -3.6954, "lon": 128.1814, "country": "Indonesia", "spice": "Clove", "desc": "Dutch colonial capital of the Spice Islands. Site of the 1623 Amboyna massacre of English traders by the VOC.", "color": _VIOLET},
    {"name": "Seram Island", "lat": -3.1300, "lon": 129.4800, "country": "Indonesia", "spice": "Clove, Nutmeg", "desc": "Largest island in the central Maluku group, with wild nutmeg and clove forests in the interior mountains.", "color": _VIOLET},
    {"name": "Halmahera", "lat": 0.9800, "lon": 127.8000, "country": "Indonesia", "spice": "Clove", "desc": "Largest island in the North Maluku chain, with extensive clove plantations and volcanic soils ideal for spice cultivation.", "color": _TEAL},
    {"name": "Sanana (Sula Islands)", "lat": -2.0700, "lon": 125.9700, "country": "Indonesia", "spice": "Clove", "desc": "Southern Maluku island group with clove production dating to pre-colonial trading networks.", "color": _TEAL},
    {"name": "Pulau Mandioli", "lat": -0.8200, "lon": 127.4200, "country": "Indonesia", "spice": "Nutmeg", "desc": "Small island near Bacan known for nutmeg groves and traditional spice drying methods.", "color": _EMERALD},
    {"name": "Gorontalo (Sulawesi)", "lat": 0.5435, "lon": 123.0568, "country": "Indonesia", "spice": "Clove", "desc": "Major clove-growing region on northern Sulawesi, now Indonesia's largest clove-producing area.", "color": _EMERALD},
    {"name": "Minahasa (Sulawesi)", "lat": 1.2921, "lon": 124.8413, "country": "Indonesia", "spice": "Clove, Nutmeg", "desc": "Highland region of North Sulawesi with colonial-era spice plantations introduced by the Dutch.", "color": _BLUE},
    {"name": "Tobelo (Halmahera)", "lat": 1.7264, "lon": 128.0011, "country": "Indonesia", "spice": "Clove", "desc": "Northern Halmahera trading town and gateway to the historic clove-producing regions of Jailolo.", "color": _BLUE},
    {"name": "Jailolo (Halmahera)", "lat": 1.0800, "lon": 127.5100, "country": "Indonesia", "spice": "Clove", "desc": "One of the four original Maluku sultanates alongside Ternate, Tidore, and Bacan.", "color": _PINK},
    {"name": "Banda Api (Volcano)", "lat": -4.5250, "lon": 129.8710, "country": "Indonesia", "spice": "Nutmeg", "desc": "Active volcanic cone in the Banda Sea whose eruptions fertilized the soils that produce the finest nutmeg.", "color": _PINK},
    {"name": "Kei Islands", "lat": -5.6300, "lon": 132.7500, "country": "Indonesia", "spice": "Nutmeg", "desc": "Southeastern Maluku islands with nutmeg cultivation and traditional Kei boat-building heritage.", "color": _CYAN},
    {"name": "Tanimbar Islands", "lat": -7.5000, "lon": 131.6000, "country": "Indonesia", "spice": "Clove", "desc": "Remote southeastern Maluku islands integrated into the spice trade via Makassar middlemen.", "color": _CYAN},
    {"name": "Aru Islands", "lat": -6.1000, "lon": 134.4000, "country": "Indonesia", "spice": "Nutmeg", "desc": "Eastern Maluku islands visited by Wallace, with scattered nutmeg groves and pearl diving traditions.", "color": _GOLD},
    {"name": "Buru Island", "lat": -3.4000, "lon": 126.6500, "country": "Indonesia", "spice": "Cajuput Oil", "desc": "Western Maluku island known for cajuput (melaleuca) oil distillation and spice-adjacent trading.", "color": _GOLD},
    {"name": "Kayoa Island", "lat": 0.3200, "lon": 127.5100, "country": "Indonesia", "spice": "Clove", "desc": "Small volcanic island between Makian and Bacan with clove gardens dating to the sultanate era.", "color": _ACCENT},
    {"name": "Manado (Sulawesi)", "lat": 1.4748, "lon": 124.8421, "country": "Indonesia", "spice": "Clove, Nutmeg", "desc": "Port city and VOC trading post; gateway to the clove and nutmeg gardens of North Sulawesi.", "color": _ACCENT},
    {"name": "Obi Islands", "lat": -1.5400, "lon": 127.7000, "country": "Indonesia", "spice": "Clove", "desc": "South of Bacan, these islands were part of the Bacan sultanate's clove-producing territory.", "color": _EMERALD},
    {"name": "Weda (Halmahera)", "lat": 0.3800, "lon": 127.8500, "country": "Indonesia", "spice": "Clove", "desc": "Eastern Halmahera settlement with traditional clove-drying platforms and pre-colonial trade links.", "color": _AMBER},
]

INDIAN_SPICE_MARKETS = [
    {"name": "Khari Baoli, Old Delhi", "lat": 28.6562, "lon": 77.2167, "country": "India", "spice": "Mixed Spices", "desc": "Asia's largest wholesale spice market, operating since the 17th century Mughal era. Overflowing with turmeric, cumin, cardamom, and chili.", "color": _AMBER},
    {"name": "Mattancherry Spice Market, Kochi", "lat": 9.9577, "lon": 76.2590, "country": "India", "spice": "Pepper, Cardamom", "desc": "Historic spice trading quarter in Fort Kochi where pepper has been traded for over 2,000 years.", "color": _EMERALD},
    {"name": "Wayanad Pepper Plantations", "lat": 11.6854, "lon": 76.1320, "country": "India", "spice": "Black Pepper", "desc": "Kerala highlands where Malabar pepper vines climb tropical trees; one of the oldest pepper-growing regions.", "color": _EMERALD},
    {"name": "Idukki Cardamom Hills", "lat": 9.8494, "lon": 76.9720, "country": "India", "spice": "Cardamom", "desc": "The Cardamom Hills of Kerala and Tamil Nadu, producing India's famous green cardamom (Elettaria).", "color": _TEAL},
    {"name": "Thekkady Spice Plantations", "lat": 9.6000, "lon": 77.1640, "country": "India", "spice": "Cardamom, Pepper, Vanilla", "desc": "Periyar region spice gardens offering walking tours through cardamom, pepper, vanilla, and coffee plantations.", "color": _TEAL},
    {"name": "Pampore Saffron Fields, Kashmir", "lat": 33.9700, "lon": 74.9300, "country": "India", "spice": "Saffron", "desc": "The saffron karewas (plateaus) of Pampore, where Kashmiri saffron has been cultivated since antiquity. Harvest in October-November.", "color": _VIOLET},
    {"name": "Jodhpur Spice Bazaar", "lat": 26.2389, "lon": 73.0243, "country": "India", "spice": "Chili, Cumin", "desc": "Rajasthani spice market in the Blue City, famous for Mathania red chili and cumin from Barmer.", "color": _RED},
    {"name": "Mathania Chili Fields, Rajasthan", "lat": 26.3500, "lon": 72.6700, "country": "India", "spice": "Red Chili", "desc": "Village near Jodhpur famous for its deep red Mathania chili, prized for color and moderate heat.", "color": _RED},
    {"name": "Guntur Chili Market, Andhra Pradesh", "lat": 16.3067, "lon": 80.4365, "country": "India", "spice": "Red Chili", "desc": "India's largest chili trading hub, handling millions of tonnes annually. The Guntur Sannam variety is exported worldwide.", "color": _ORANGE},
    {"name": "Kumily Spice Town, Kerala", "lat": 9.5974, "lon": 77.1670, "country": "India", "spice": "Pepper, Cardamom", "desc": "Gateway to the Periyar Tiger Reserve and surrounded by spice plantations offering organic spice tours.", "color": _EMERALD},
    {"name": "Coonoor Tea & Spice Hills", "lat": 11.3530, "lon": 76.7959, "country": "India", "spice": "Clove, Cinnamon", "desc": "Nilgiri Hills station where clove and cinnamon grow alongside world-famous tea estates.", "color": _BLUE},
    {"name": "Coorg (Kodagu) Coffee & Spice", "lat": 12.3375, "lon": 75.8069, "country": "India", "spice": "Pepper, Cardamom", "desc": "Karnataka highlands producing pepper and cardamom alongside India's finest coffee. Known as the 'Scotland of India'.", "color": _BLUE},
    {"name": "Devaraja Market, Mysuru", "lat": 12.3119, "lon": 76.6568, "country": "India", "spice": "Mixed Spices", "desc": "120-year-old market in Mysore selling turmeric, sandalwood, incense, and mixed masala powders.", "color": _GOLD},
    {"name": "Unjha APMC Cumin Market, Gujarat", "lat": 23.8000, "lon": 72.4000, "country": "India", "spice": "Cumin", "desc": "World's largest single-commodity cumin market. Gujarat produces 70% of India's cumin output.", "color": _GOLD},
    {"name": "Haldi (Turmeric) Market, Sangli", "lat": 16.8524, "lon": 74.5815, "country": "India", "spice": "Turmeric", "desc": "Maharashtra's principal turmeric trading center, one of the largest in Asia. Turmeric is called 'Indian gold'.", "color": _AMBER},
    {"name": "Ernakulam Spice District", "lat": 9.9816, "lon": 76.2999, "country": "India", "spice": "Mixed Spices", "desc": "Commercial hub adjacent to Kochi handling exports of pepper, cardamom, and clove through the Cochin port.", "color": _TEAL},
    {"name": "Munnar Tea & Spice Estates", "lat": 10.0889, "lon": 77.0595, "country": "India", "spice": "Cardamom, Vanilla", "desc": "Hill station in the Western Ghats where cardamom and vanilla grow in the shade of tea bushes at 1,600 meters.", "color": _EMERALD},
    {"name": "Kollam (Quilon) Pepper Port", "lat": 8.8932, "lon": 76.6141, "country": "India", "spice": "Black Pepper", "desc": "Ancient port known to Romans as Quilon; a major pepper export hub since the 1st century CE Periplus trade.", "color": _VIOLET},
    {"name": "Chikmagalur Spice Hills", "lat": 13.3161, "lon": 75.7720, "country": "India", "spice": "Pepper, Cardamom", "desc": "Karnataka's coffee capital also grows premium pepper and cardamom on shaded hillside plantations.", "color": _BLUE},
    {"name": "Thodupuzha Spice Market", "lat": 9.9000, "lon": 76.7200, "country": "India", "spice": "Cardamom, Pepper", "desc": "Central Kerala trading town serving as collection hub for cardamom from Idukki district plantations.", "color": _CYAN},
    {"name": "Kozhikode (Calicut) Market", "lat": 11.2588, "lon": 75.7804, "country": "India", "spice": "Pepper, Ginger", "desc": "Where Vasco da Gama landed in 1498 seeking the pepper trade. The Zamorin's port had traded spices for millennia.", "color": _PINK},
    {"name": "Yercaud Spice Garden, Tamil Nadu", "lat": 11.7750, "lon": 78.2080, "country": "India", "spice": "Pepper, Clove", "desc": "Salem district hill station with colonial-era spice gardens growing pepper, clove, and cinnamon.", "color": _ORANGE},
    {"name": "Sirsi Spice Hub, Karnataka", "lat": 14.6200, "lon": 74.8340, "country": "India", "spice": "Pepper, Areca Nut", "desc": "Western Ghats town in Uttara Kannada known for arecanut and pepper cultivation in humid forests.", "color": _ACCENT},
    {"name": "Thanjavur Market, Tamil Nadu", "lat": 10.7870, "lon": 79.1378, "country": "India", "spice": "Turmeric, Coriander", "desc": "Ancient Chola capital where turmeric and coriander are traded in the shadow of the Brihadeeswarar Temple.", "color": _GOLD},
    {"name": "Bodi Spice Bazaar, Tamil Nadu", "lat": 10.0100, "lon": 77.3500, "country": "India", "spice": "Cardamom", "desc": "Theni district trading center at the foot of the Western Ghats, handling cardamom from hill plantations.", "color": _TEAL},
    {"name": "Rameswaram Spice & Salt", "lat": 9.2876, "lon": 79.3129, "country": "India", "spice": "Dried Chili, Sea Salt", "desc": "Island temple town where dried chili, turmeric, and sea salt are traded at the southern tip of India.", "color": _RED},
]

HISTORIC_TRADE_PORTS = [
    {"name": "Calicut (Kozhikode), India", "lat": 11.2588, "lon": 75.7804, "country": "India", "era": "1st century BCE", "desc": "The Zamorin's port and Vasco da Gama's destination in 1498. Calicut was the pepper capital of the world for centuries.", "color": _AMBER},
    {"name": "Malacca (Melaka), Malaysia", "lat": 2.1896, "lon": 102.2501, "country": "Malaysia", "era": "15th century", "desc": "Strategic strait city controlling the spice route between India and China. Conquered by Portuguese (1511), Dutch, and British.", "color": _RED},
    {"name": "Aden, Yemen", "lat": 12.7855, "lon": 45.0187, "country": "Yemen", "era": "1st century CE", "desc": "Ancient Arabian port at the mouth of the Red Sea, transshipping spices from India to the Mediterranean world.", "color": _ORANGE},
    {"name": "Venice, Italy", "lat": 45.4408, "lon": 12.3155, "country": "Italy", "era": "10th century", "desc": "Queen of the Adriatic and Europe's spice gateway. Venetian merchants monopolized the Eastern spice trade for centuries.", "color": _VIOLET},
    {"name": "Lisbon, Portugal", "lat": 38.7223, "lon": -9.1393, "country": "Portugal", "era": "15th century", "desc": "Launch point for the Portuguese spice empire. Vasco da Gama sailed from here in 1497 to break Venice's monopoly.", "color": _EMERALD},
    {"name": "Amsterdam, Netherlands", "lat": 52.3676, "lon": 4.9041, "country": "Netherlands", "era": "17th century", "desc": "VOC headquarters and the world's spice trading capital in the Dutch Golden Age. The Amsterdam Exchange set global spice prices.", "color": _BLUE},
    {"name": "Goa, India", "lat": 15.4989, "lon": 73.8278, "country": "India", "era": "16th century", "desc": "Portuguese colonial capital in India (1510-1961). Hub for exporting pepper, cinnamon, and ginger to Europe.", "color": _PINK},
    {"name": "Hormuz, Iran", "lat": 27.0583, "lon": 56.4611, "country": "Iran", "era": "13th century", "desc": "Island fortress controlling the Persian Gulf entrance. All spice ships from India passed through Hormuz.", "color": _GOLD},
    {"name": "Mocha, Yemen", "lat": 13.3164, "lon": 43.2489, "country": "Yemen", "era": "15th century", "desc": "Red Sea port famous for coffee but also a major spice transshipment point from the Indian Ocean.", "color": _ORANGE},
    {"name": "Zanzibar (Stone Town), Tanzania", "lat": -6.1622, "lon": 39.1921, "country": "Tanzania", "era": "10th century", "desc": "The Spice Island of East Africa, center of the clove trade under Omani sultans. Clove plantations still thrive.", "color": _TEAL},
    {"name": "Genoa, Italy", "lat": 44.4056, "lon": 8.9463, "country": "Italy", "era": "12th century", "desc": "Venice's great rival in the spice trade. Genoese merchants controlled Black Sea and Eastern Mediterranean routes.", "color": _VIOLET},
    {"name": "Alexandria, Egypt", "lat": 31.2001, "lon": 29.9187, "country": "Egypt", "era": "3rd century BCE", "desc": "Ptolemaic and Roman spice entrepot linking the Red Sea trade to the Mediterranean via the Nile and overland routes.", "color": _GOLD},
    {"name": "Bantam (Banten), Java", "lat": -6.0500, "lon": 106.1500, "country": "Indonesia", "era": "16th century", "desc": "Javanese pepper port where Dutch, English, and Chinese competed for the pepper and spice trade.", "color": _RED},
    {"name": "Cochin (Kochi), India", "lat": 9.9312, "lon": 76.2673, "country": "India", "era": "14th century", "desc": "Natural harbor on the Malabar Coast. The Raja of Cochin allied with the Portuguese to trade pepper.", "color": _EMERALD},
    {"name": "Muscat, Oman", "lat": 23.5880, "lon": 58.3829, "country": "Oman", "era": "6th century", "desc": "Strategic Arabian Sea port connecting Indian spices to the Persian Gulf and African coast via dhow trading.", "color": _AMBER},
    {"name": "Guangzhou (Canton), China", "lat": 23.1291, "lon": 113.2644, "country": "China", "era": "3rd century BCE", "desc": "Southern Chinese port and terminus of the Maritime Silk Road. Star anise, cassia, and ginger were exported from here.", "color": _CYAN},
    {"name": "Aceh (Banda Aceh), Sumatra", "lat": 5.5483, "lon": 95.3238, "country": "Indonesia", "era": "13th century", "desc": "Sultanate of Aceh controlled the western entrance to the Strait of Malacca and the pepper trade of Sumatra.", "color": _RED},
    {"name": "Quilon (Kollam), India", "lat": 8.8932, "lon": 76.6141, "country": "India", "era": "1st century CE", "desc": "Ancient port mentioned in the Periplus, trading pepper with Rome. Chinese and Arab merchants maintained factories.", "color": _PINK},
    {"name": "Constantinople (Istanbul)", "lat": 41.0082, "lon": 28.9784, "country": "Turkey", "era": "4th century CE", "desc": "Byzantine capital and crossroads where overland and maritime spice routes converged at the Bosphorus.", "color": _GOLD},
    {"name": "Bruges, Belgium", "lat": 51.2093, "lon": 3.2247, "country": "Belgium", "era": "13th century", "desc": "Medieval Flemish trading city where Italian merchants sold Eastern spices to Northern European buyers.", "color": _BLUE},
    {"name": "Antwerp, Belgium", "lat": 51.2194, "lon": 4.4025, "country": "Belgium", "era": "16th century", "desc": "Succeeded Bruges as Europe's commercial capital. Portuguese spice cargoes were auctioned at the Antwerp Bourse.", "color": _BLUE},
    {"name": "Seville, Spain", "lat": 37.3891, "lon": -5.9845, "country": "Spain", "era": "16th century", "desc": "Casa de Contratacion controlled all Spanish trade with the Americas, including New World chili and vanilla imports.", "color": _ORANGE},
    {"name": "Basra, Iraq", "lat": 30.5085, "lon": 47.7804, "country": "Iraq", "era": "7th century", "desc": "Gateway port of the Abbasid Caliphate at the head of the Persian Gulf. Sinbad's legendary sailing port.", "color": _AMBER},
    {"name": "Mangalore, India", "lat": 12.9141, "lon": 74.8560, "country": "India", "era": "6th century", "desc": "Karnataka's main port exporting pepper, cardamom, and arecanut from the Western Ghats hinterland.", "color": _TEAL},
    {"name": "Makassar (Ujung Pandang), Sulawesi", "lat": -5.1477, "lon": 119.4327, "country": "Indonesia", "era": "14th century", "desc": "Bugis and Makassarese port that served as middleman between the Spice Islands and global trade networks.", "color": _PINK},
    {"name": "Palembang, Sumatra", "lat": -2.9761, "lon": 104.7754, "country": "Indonesia", "era": "7th century", "desc": "Capital of the Srivijaya maritime empire controlling the Strait of Malacca and spice transshipment.", "color": _VIOLET},
]

SAFFRON_REGIONS = [
    {"name": "Pampore, Kashmir, India", "lat": 33.9700, "lon": 74.9300, "country": "India", "variety": "Kashmiri (Mongra)", "desc": "The saffron karewas of Pampore produce India's prized GI-tagged Kashmiri saffron, among the world's finest.", "color": _VIOLET},
    {"name": "Kishtwar, Jammu & Kashmir", "lat": 33.3100, "lon": 75.7700, "country": "India", "variety": "Kashmiri", "desc": "High-altitude saffron fields in the Kishtwar valley, supplementing the more famous Pampore production.", "color": _VIOLET},
    {"name": "Qaen, South Khorasan, Iran", "lat": 33.7260, "lon": 59.1840, "country": "Iran", "variety": "Iranian Sargol", "desc": "Iran produces 90% of the world's saffron. Qaen and Birjand are the heartland of production.", "color": _RED},
    {"name": "Torbat-e Heydarieh, Iran", "lat": 35.2740, "lon": 59.2194, "country": "Iran", "variety": "Iranian Super Negin", "desc": "Premium Iranian saffron region producing Super Negin grade, the highest quality threads.", "color": _RED},
    {"name": "Gonabad, Iran", "lat": 34.3529, "lon": 58.6836, "country": "Iran", "variety": "Iranian Pushal", "desc": "Khorasan province saffron town with ancient qanat irrigation systems supporting crocus cultivation.", "color": _ORANGE},
    {"name": "Birjand, Iran", "lat": 32.8663, "lon": 59.2211, "country": "Iran", "variety": "Iranian Sargol", "desc": "Capital of South Khorasan province and a major saffron processing and export center.", "color": _ORANGE},
    {"name": "La Mancha, Consuegra, Spain", "lat": 39.4600, "lon": -3.6100, "country": "Spain", "variety": "Spanish Mancha", "desc": "Spain's DO-protected saffron region in Castilla-La Mancha. Spanish saffron was once the European standard.", "color": _AMBER},
    {"name": "La Mancha, Madridejos, Spain", "lat": 39.4700, "lon": -3.5300, "country": "Spain", "variety": "Spanish Mancha", "desc": "Traditional saffron harvest festival (Rosa del Azafran) held each October in this La Mancha village.", "color": _AMBER},
    {"name": "Taliouine, Morocco", "lat": 30.5300, "lon": -7.9300, "country": "Morocco", "variety": "Moroccan", "desc": "The saffron capital of Morocco in the Anti-Atlas mountains. Berber women hand-harvest crocus flowers at dawn.", "color": _GOLD},
    {"name": "Kozani, Greece", "lat": 40.3014, "lon": 21.7889, "country": "Greece", "variety": "Greek Red (Krokos Kozanis)", "desc": "PDO-protected Greek saffron from the Kozani plateau in Macedonia. Cultivated here since the 17th century.", "color": _BLUE},
    {"name": "Navelli, Abruzzo, Italy", "lat": 42.2300, "lon": 13.7300, "country": "Italy", "variety": "L'Aquila Saffron", "desc": "Italy's finest saffron from the Navelli plateau, DOP-protected. Used in risotto alla Milanese since medieval times.", "color": _EMERALD},
    {"name": "San Gimignano, Tuscany, Italy", "lat": 43.4677, "lon": 11.0430, "country": "Italy", "variety": "Tuscan Saffron", "desc": "Medieval town that traded saffron as currency. The San Gimignano saffron tradition has been revived.", "color": _EMERALD},
    {"name": "Mund, Valais, Switzerland", "lat": 46.3200, "lon": 7.9400, "country": "Switzerland", "variety": "Swiss Alpine", "desc": "Europe's highest saffron fields at 1,200m. The tiny village of Mund has grown saffron since the 14th century.", "color": _TEAL},
    {"name": "Herat, Afghanistan", "lat": 34.3529, "lon": 62.2043, "country": "Afghanistan", "variety": "Afghan", "desc": "Afghanistan's rapidly growing saffron industry, promoted as an alternative to opium poppy cultivation.", "color": _PINK},
    {"name": "Safranbolu, Turkey", "lat": 41.2547, "lon": 32.6901, "country": "Turkey", "variety": "Turkish", "desc": "UNESCO World Heritage town named after saffron (safran). Historic Ottoman saffron trading center.", "color": _ORANGE},
    {"name": "Kashmir Valley (Pulwama)", "lat": 33.8700, "lon": 74.9000, "country": "India", "variety": "Kashmiri Lacha", "desc": "Pulwama district's saffron fields, where the crop is called 'red gold' and requires manual harvesting.", "color": _VIOLET},
    {"name": "Krokos Village, Greece", "lat": 40.2800, "lon": 21.7600, "country": "Greece", "variety": "Krokos Kozanis PDO", "desc": "The village that gave its name to crocus. Greek saffron cooperative processes and exports from here.", "color": _BLUE},
    {"name": "Ghain, Iran", "lat": 33.7100, "lon": 59.1700, "country": "Iran", "variety": "Iranian Negin", "desc": "Historic center of Iranian saffron production with ancient knowledge of crocus cultivation techniques.", "color": _RED},
    {"name": "Chiniot, Punjab, Pakistan", "lat": 31.7167, "lon": 72.9833, "country": "Pakistan", "variety": "Pakistani", "desc": "Emerging saffron cultivation area in Pakistan, adapting techniques from neighboring Kashmir and Iran.", "color": _TEAL},
    {"name": "Consuegra Windmills Plateau, Spain", "lat": 39.4580, "lon": -3.6040, "country": "Spain", "variety": "La Mancha DOP", "desc": "Don Quixote's windmill country is also the heart of Spanish saffron. Annual Fiesta de la Rosa del Azafran.", "color": _AMBER},
    {"name": "Saffron Walden, England", "lat": 52.0220, "lon": 0.2430, "country": "United Kingdom", "variety": "English (historic)", "desc": "Essex town named for its medieval saffron trade. English saffron cultivation peaked in the 14th-16th centuries.", "color": _CYAN},
    {"name": "Nuremberg, Germany", "lat": 49.4521, "lon": 11.0767, "country": "Germany", "variety": "Trade hub", "desc": "Medieval saffron trading city where Safranschou (saffron inspectors) tested quality. Adulterators were burned at the stake.", "color": _GOLD},
    {"name": "Boyaca, Colombia", "lat": 5.5353, "lon": -73.3622, "country": "Colombia", "variety": "Colombian (experimental)", "desc": "High Andes experimental saffron cultivation at 2,500m, adapting Iranian and Spanish crocus varieties.", "color": _PINK},
    {"name": "Tasmania, Australia", "lat": -42.0000, "lon": 147.0000, "country": "Australia", "variety": "Tasmanian", "desc": "Southern hemisphere saffron production in Tasmania's cool climate, harvested in May-June.", "color": _ACCENT},
    {"name": "Khorasan Razavi (Mashhad area)", "lat": 36.2972, "lon": 59.6060, "country": "Iran", "variety": "Iranian Premium", "desc": "Greater Khorasan is the world's saffron superpower, producing over 300 tonnes annually.", "color": _RED},
]

VANILLA_HERITAGE = [
    {"name": "Papantla, Veracruz, Mexico", "lat": 20.4491, "lon": -97.3203, "country": "Mexico", "variety": "Mexican Vanilla", "desc": "Birthplace of vanilla cultivation. The Totonac people first domesticated Vanilla planifolia here over 1,000 years ago.", "color": _AMBER},
    {"name": "SAVA Region, Madagascar", "lat": -14.2800, "lon": 50.0200, "country": "Madagascar", "variety": "Bourbon Vanilla", "desc": "Madagascar produces 80% of the world's vanilla. The SAVA northeast coast is the global capital of Bourbon vanilla.", "color": _EMERALD},
    {"name": "Antalaha, Madagascar", "lat": -14.8990, "lon": 50.2780, "country": "Madagascar", "variety": "Bourbon Vanilla", "desc": "Self-proclaimed 'Vanilla Capital of the World.' Annual vanilla festival celebrates harvest season.", "color": _EMERALD},
    {"name": "Sambava, Madagascar", "lat": -14.2667, "lon": 50.1667, "country": "Madagascar", "variety": "Bourbon Vanilla", "desc": "Major vanilla market town in the SAVA region. Vanilla beans are sun-dried on rooftops throughout the town.", "color": _TEAL},
    {"name": "Vohemar, Madagascar", "lat": -13.3500, "lon": 50.0000, "country": "Madagascar", "variety": "Bourbon Vanilla", "desc": "Northern vanilla-producing area of Madagascar contributing to the SAVA region's dominance.", "color": _TEAL},
    {"name": "Tahaa, French Polynesia", "lat": -16.6200, "lon": -151.4900, "country": "French Polynesia", "variety": "Tahitian Vanilla", "desc": "The 'Vanilla Island' of Tahaa is the center of Tahitian vanilla (V. tahitensis) with its unique floral, cherry-like flavor.", "color": _VIOLET},
    {"name": "Raiatea, French Polynesia", "lat": -16.8300, "lon": -151.4600, "country": "French Polynesia", "variety": "Tahitian Vanilla", "desc": "Sister island to Tahaa and co-producer of Tahitian vanilla, prized by French pastry chefs.", "color": _VIOLET},
    {"name": "Huahine, French Polynesia", "lat": -16.7500, "lon": -151.0000, "country": "French Polynesia", "variety": "Tahitian Vanilla", "desc": "Traditional vanilla gardens on this 'Garden of Eden' island supplement Tahaa production.", "color": _PINK},
    {"name": "Saint-Andre, Reunion Island", "lat": -20.9600, "lon": 55.6500, "country": "Reunion (France)", "variety": "Bourbon Vanilla", "desc": "Where Edmond Albius, an enslaved 12-year-old, invented hand-pollination of vanilla in 1841, revolutionizing production.", "color": _GOLD},
    {"name": "Sainte-Suzanne, Reunion Island", "lat": -20.9100, "lon": 55.6100, "country": "Reunion (France)", "variety": "Bourbon Vanilla", "desc": "Vanilla cooperative producing traditional Bourbon vanilla with slow curing methods on Reunion Island.", "color": _GOLD},
    {"name": "Tonga, Pacific Islands", "lat": -21.2000, "lon": -175.2000, "country": "Tonga", "variety": "Tongan Vanilla", "desc": "Pacific Island vanilla production adapting Bourbon and Tahitian varieties to Tongan growing conditions.", "color": _CYAN},
    {"name": "Jujutla, El Salvador", "lat": 13.5600, "lon": -89.8500, "country": "El Salvador", "variety": "Central American", "desc": "Small-scale artisanal vanilla cultivation in El Salvador, near the wild origin range of the vanilla orchid.", "color": _ORANGE},
    {"name": "Misantla, Veracruz, Mexico", "lat": 19.9300, "lon": -96.8500, "country": "Mexico", "variety": "Mexican Vanilla", "desc": "Historic vanilla region near Papantla; together they form the original vanilla homeland of Mesoamerica.", "color": _AMBER},
    {"name": "Uxpanapa, Veracruz, Mexico", "lat": 17.2800, "lon": -94.5500, "country": "Mexico", "variety": "Mexican Vanilla", "desc": "Southern Veracruz vanilla-growing zone in the tropical lowlands near Oaxaca border.", "color": _RED},
    {"name": "Comoros Islands (Anjouan)", "lat": -12.2167, "lon": 44.2500, "country": "Comoros", "variety": "Bourbon-type", "desc": "Indian Ocean archipelago producing Bourbon-type vanilla, historically a major exporter.", "color": _BLUE},
    {"name": "Bali, Indonesia", "lat": -8.3405, "lon": 115.0920, "country": "Indonesia", "variety": "Indonesian Vanilla", "desc": "Indonesian vanilla from Bali and Java; Indonesia is the second-largest vanilla producer globally.", "color": _ORANGE},
    {"name": "Sulawesi, Indonesia", "lat": -1.4300, "lon": 121.4500, "country": "Indonesia", "variety": "Indonesian Vanilla", "desc": "Central Sulawesi vanilla plantations contributing to Indonesia's growing share of the world market.", "color": _ORANGE},
    {"name": "Papua New Guinea Highlands", "lat": -5.5000, "lon": 145.0000, "country": "Papua New Guinea", "variety": "PNG Vanilla", "desc": "Smallholder vanilla cultivation in the PNG Highlands, producing a unique terroir-driven flavor.", "color": _TEAL},
    {"name": "Taveuni, Fiji", "lat": -16.8700, "lon": -179.9000, "country": "Fiji", "variety": "Fijian Vanilla", "desc": "The 'Garden Island' of Fiji is developing vanilla cultivation as a premium agricultural export.", "color": _PINK},
    {"name": "Uganda (Mukono District)", "lat": 0.3500, "lon": 32.7700, "country": "Uganda", "variety": "African Bourbon", "desc": "East African vanilla production growing rapidly. Ugandan Bourbon vanilla is gaining international recognition.", "color": _EMERALD},
    {"name": "Kerala, India", "lat": 9.6000, "lon": 77.1640, "country": "India", "variety": "Indian Vanilla", "desc": "Indian vanilla cultivation in Kerala and Karnataka, growing alongside pepper and cardamom in spice gardens.", "color": _GOLD},
    {"name": "Guadalajara (Jalisco), Mexico", "lat": 20.6597, "lon": -103.3496, "country": "Mexico", "variety": "Mexican Vanilla", "desc": "Processing hub for Mexican vanilla extract. Beware of coumarin-containing tonka bean imitations sold as 'vanilla'.", "color": _RED},
    {"name": "Oaxaca, Mexico", "lat": 17.0732, "lon": -96.7266, "country": "Mexico", "variety": "Mexican Vanilla", "desc": "Southern Mexican vanilla region; Oaxaca's indigenous communities maintain traditional vanilla curing knowledge.", "color": _AMBER},
    {"name": "Maroantsetra, Madagascar", "lat": -15.4400, "lon": 49.7400, "country": "Madagascar", "variety": "Bourbon Vanilla", "desc": "Remote northeastern port town and vanilla collection center at the edge of the Masoala rainforest.", "color": _EMERALD},
    {"name": "Vava'u, Tonga", "lat": -18.6500, "lon": -174.0000, "country": "Tonga", "variety": "Tongan Vanilla", "desc": "Northern Tonga island group with organic vanilla projects supporting local farming communities.", "color": _CYAN},
]

CINNAMON_CASSIA = [
    {"name": "Galle, Sri Lanka", "lat": 6.0535, "lon": 80.2210, "country": "Sri Lanka", "variety": "Ceylon Cinnamon (C. verum)", "desc": "The southern coast of Sri Lanka is the birthplace of true Ceylon cinnamon, the world's finest and most delicate.", "color": _AMBER},
    {"name": "Matara, Sri Lanka", "lat": 5.9485, "lon": 80.5353, "country": "Sri Lanka", "variety": "Ceylon Cinnamon", "desc": "Major cinnamon processing district. Sri Lankan peelers use a unique hand-rolling technique perfected over centuries.", "color": _AMBER},
    {"name": "Koggala, Sri Lanka", "lat": 5.9900, "lon": 80.3200, "country": "Sri Lanka", "variety": "Ceylon Cinnamon", "desc": "Cinnamon gardens along the southern coast where Martin Wickramasinghe documented traditional peeling culture.", "color": _GOLD},
    {"name": "Balapitiya, Sri Lanka", "lat": 6.2700, "lon": 80.1600, "country": "Sri Lanka", "variety": "Ceylon Cinnamon", "desc": "Cinnamon growing area in Galle district with boat tours through cinnamon-lined riverside plantations.", "color": _GOLD},
    {"name": "Negombo, Sri Lanka", "lat": 7.2083, "lon": 79.8358, "country": "Sri Lanka", "variety": "Ceylon Cinnamon", "desc": "Historic port near Colombo once known as the 'Cinnamon City'. The Dutch fought the Portuguese for control.", "color": _AMBER},
    {"name": "Ambalangoda, Sri Lanka", "lat": 6.2400, "lon": 80.0500, "country": "Sri Lanka", "variety": "Ceylon Cinnamon", "desc": "Coastal town in the cinnamon belt where traditional mask-making and cinnamon peeling are living crafts.", "color": _EMERALD},
    {"name": "Guangxi Province, China", "lat": 23.7260, "lon": 108.3200, "country": "China", "variety": "Chinese Cassia (C. cassia)", "desc": "China's largest cassia-producing province. Chinese cassia is thicker, darker, and more pungent than Ceylon cinnamon.", "color": _RED},
    {"name": "Guangdong Province, China", "lat": 23.3790, "lon": 113.7633, "country": "China", "variety": "Chinese Cassia", "desc": "Southern Chinese cassia region. Cassia bark has been used in Chinese medicine for over 4,000 years.", "color": _RED},
    {"name": "Fujian Province, China", "lat": 26.0745, "lon": 119.2965, "country": "China", "variety": "Chinese Cassia", "desc": "Eastern Chinese cassia production area, supplying bark for five-spice powder and traditional remedies.", "color": _ORANGE},
    {"name": "Yen Bai, Vietnam", "lat": 21.7168, "lon": 104.8985, "country": "Vietnam", "variety": "Saigon Cinnamon (C. loureiroi)", "desc": "Vietnamese cinnamon (Saigon cinnamon) has the highest cinnamaldehyde content, making it the strongest variety.", "color": _PINK},
    {"name": "Quang Nam, Vietnam", "lat": 15.5394, "lon": 108.0191, "country": "Vietnam", "variety": "Saigon Cinnamon", "desc": "Central Vietnam cinnamon forests where bark is harvested from C. loureiroi trees grown on steep hillsides.", "color": _PINK},
    {"name": "Lao Cai, Vietnam", "lat": 22.4860, "lon": 103.9707, "country": "Vietnam", "variety": "Vietnamese Cassia", "desc": "Northwest Vietnam cinnamon region near the Chinese border; cinnamon bark is a major smallholder crop.", "color": _VIOLET},
    {"name": "Thanh Hoa, Vietnam", "lat": 19.8067, "lon": 105.7852, "country": "Vietnam", "variety": "Vietnamese Cassia", "desc": "Central Vietnamese province with cassia forests supporting rural livelihoods.", "color": _VIOLET},
    {"name": "Jambi, Sumatra, Indonesia", "lat": -1.5900, "lon": 103.6131, "country": "Indonesia", "variety": "Korintje Cassia (C. burmannii)", "desc": "Sumatran Korintje (Kerinci) cassia is the most commonly sold 'cinnamon' in American supermarkets.", "color": _TEAL},
    {"name": "Kerinci Valley, Sumatra", "lat": -1.7500, "lon": 101.2650, "country": "Indonesia", "variety": "Korintje Cassia", "desc": "Highland valley near Mount Kerinci producing Indonesia's finest cassia, graded A, B, and C by oil content.", "color": _TEAL},
    {"name": "West Sumatra (Padang area)", "lat": -0.9471, "lon": 100.4172, "country": "Indonesia", "variety": "Korintje Cassia", "desc": "Minangkabau region cassia production, exported through the port of Padang.", "color": _BLUE},
    {"name": "Kerala (Idukki), India", "lat": 9.8494, "lon": 76.9720, "country": "India", "variety": "Indian Cassia (C. tamala)", "desc": "Indian cinnamon (tej pat/bay leaf) and cassia grown alongside cardamom in the Western Ghats.", "color": _EMERALD},
    {"name": "Assam, India", "lat": 26.2006, "lon": 92.9376, "country": "India", "variety": "Indian Cassia", "desc": "Northeast Indian cassia cultivation in the Himalayan foothills of Assam.", "color": _CYAN},
    {"name": "Zanzibar, Tanzania", "lat": -6.1622, "lon": 39.1921, "country": "Tanzania", "variety": "East African Cinnamon", "desc": "Introduced cinnamon on the Spice Island, grown alongside clove, nutmeg, and pepper on plantation tours.", "color": _GOLD},
    {"name": "Seychelles", "lat": -4.6796, "lon": 55.4920, "country": "Seychelles", "variety": "Seychellois Cinnamon", "desc": "Cinnamon plantations introduced during French colonial rule now cover the hillsides of Mahe Island.", "color": _PINK},
    {"name": "Grenada", "lat": 12.1165, "lon": -61.6790, "country": "Grenada", "variety": "Caribbean Cinnamon", "desc": "The 'Spice Island' of the Caribbean grows cinnamon alongside nutmeg, its signature spice.", "color": _ORANGE},
    {"name": "Saigon (Ho Chi Minh City)", "lat": 10.8231, "lon": 106.6297, "country": "Vietnam", "variety": "Saigon Cinnamon (trade hub)", "desc": "Historic export hub for Vietnamese cinnamon and cassia, giving 'Saigon cinnamon' its trade name.", "color": _PINK},
    {"name": "Colombo, Sri Lanka", "lat": 6.9271, "lon": 79.8612, "country": "Sri Lanka", "variety": "Ceylon Cinnamon (export hub)", "desc": "Sri Lanka's capital and primary cinnamon export port. The very name 'Ceylon' is synonymous with true cinnamon.", "color": _AMBER},
    {"name": "Batticaloa, Sri Lanka", "lat": 7.7310, "lon": 81.6747, "country": "Sri Lanka", "variety": "Ceylon Cinnamon", "desc": "Eastern Sri Lankan cinnamon-growing area contributing to the island's 90% share of true cinnamon exports.", "color": _GOLD},
    {"name": "Hainan Island, China", "lat": 19.2000, "lon": 109.7200, "country": "China", "variety": "Chinese Cassia", "desc": "Tropical southern Chinese island with cassia production dating to imperial trade networks.", "color": _RED},
    {"name": "Meghalaya, India", "lat": 25.4670, "lon": 91.3662, "country": "India", "variety": "Indian Cassia", "desc": "Northeast Indian hill state with wild cassia trees (C. tamala) harvested by local Khasi communities.", "color": _CYAN},
]

PEPPER_EMPIRE = [
    {"name": "Tellicherry (Thalassery), Kerala", "lat": 11.7480, "lon": 75.4904, "country": "India", "variety": "Tellicherry Pepper", "desc": "The gold standard of black pepper. Tellicherry peppercorns are the largest and most flavorful Malabar grade.", "color": _AMBER},
    {"name": "Wayanad, Kerala", "lat": 11.6854, "lon": 76.1320, "country": "India", "variety": "Malabar Pepper", "desc": "Kerala highland pepper gardens where vines climb areca palms and wild trees in mixed agroforestry systems.", "color": _AMBER},
    {"name": "Idukki, Kerala", "lat": 9.8494, "lon": 76.9720, "country": "India", "variety": "Malabar Pepper", "desc": "Mountain district producing premium Malabar pepper and cardamom in the Western Ghats.", "color": _EMERALD},
    {"name": "Kannur, Kerala", "lat": 11.8745, "lon": 75.3704, "country": "India", "variety": "Malabar Pepper", "desc": "Traditionally the main export hub for Malabar pepper, traded with Arabs, Chinese, and Romans.", "color": _EMERALD},
    {"name": "Kampot, Cambodia", "lat": 10.5940, "lon": 104.1620, "country": "Cambodia", "variety": "Kampot Pepper (GI)", "desc": "World-famous Kampot pepper with PGI status. Known for floral complexity and lingering heat. Nearly lost under the Khmer Rouge.", "color": _VIOLET},
    {"name": "Kep, Cambodia", "lat": 10.4830, "lon": 104.3140, "country": "Cambodia", "variety": "Kampot Pepper", "desc": "Coastal region adjacent to Kampot sharing the same terroir for premium pepper cultivation.", "color": _VIOLET},
    {"name": "Sarawak, Malaysia (Kuching)", "lat": 1.5497, "lon": 110.3634, "country": "Malaysia", "variety": "Sarawak Pepper", "desc": "World's largest pepper exporter. Sarawak white pepper is the industry benchmark, grown by Iban and Chinese farmers.", "color": _RED},
    {"name": "Johor, Malaysia", "lat": 1.4854, "lon": 103.7618, "country": "Malaysia", "variety": "Malaysian Pepper", "desc": "Southern Malaysian pepper cultivation supplementing Sarawak's dominant production.", "color": _RED},
    {"name": "Lampung, Sumatra, Indonesia", "lat": -5.4500, "lon": 105.2667, "country": "Indonesia", "variety": "Lampung Black Pepper", "desc": "Indonesia's primary pepper-producing province. Lampung pepper is one of the most traded grades globally.", "color": _ORANGE},
    {"name": "Bangka Island, Indonesia", "lat": -2.1333, "lon": 106.1167, "country": "Indonesia", "variety": "Muntok White Pepper", "desc": "Famous for Muntok white pepper, considered the world's finest white pepper variety.", "color": _ORANGE},
    {"name": "Belitung Island, Indonesia", "lat": -2.7500, "lon": 107.6500, "country": "Indonesia", "variety": "Indonesian Pepper", "desc": "Pepper-producing island adjacent to Bangka with a long history of Muntok-style white pepper.", "color": _GOLD},
    {"name": "Phu Quoc, Vietnam", "lat": 10.2270, "lon": 103.9640, "country": "Vietnam", "variety": "Phu Quoc Pepper", "desc": "Vietnamese island famous for premium black pepper and fish sauce, with terroir-driven pepper farms.", "color": _PINK},
    {"name": "Gia Lai, Central Highlands, Vietnam", "lat": 13.9831, "lon": 108.0000, "country": "Vietnam", "variety": "Vietnamese Pepper", "desc": "Vietnam is the world's largest pepper producer. Central Highlands produce 60% of the national crop.", "color": _PINK},
    {"name": "Binh Phuoc, Vietnam", "lat": 11.7500, "lon": 106.9000, "country": "Vietnam", "variety": "Vietnamese Black Pepper", "desc": "Southern Vietnamese province contributing significantly to Vietnam's global pepper dominance.", "color": _TEAL},
    {"name": "Bahia, Brazil (Ilheus)", "lat": -14.7886, "lon": -39.0493, "country": "Brazil", "variety": "Brazilian Black Pepper", "desc": "Brazilian pepper production centered in Bahia and Para states. Brazil is a top-5 global producer.", "color": _BLUE},
    {"name": "Para, Brazil (Belem)", "lat": -1.4558, "lon": -48.5024, "country": "Brazil", "variety": "Brazilian Pepper", "desc": "Amazonian state and major Brazilian pepper-producing region, introduced by Japanese immigrants in the 1930s.", "color": _BLUE},
    {"name": "Espiritu Santo, Brazil", "lat": -20.3155, "lon": -40.3128, "country": "Brazil", "variety": "Brazilian Pepper", "desc": "Southeastern Brazilian pepper cultivation adding to Brazil's growing export volumes.", "color": _CYAN},
    {"name": "Penja, Cameroon", "lat": 4.6333, "lon": 9.6667, "country": "Cameroon", "variety": "Penja White Pepper (GI)", "desc": "Africa's first GI-registered pepper. Penja white pepper is prized by European chefs for its unique terroir.", "color": _GOLD},
    {"name": "Zanzibar, Tanzania", "lat": -6.1622, "lon": 39.1921, "country": "Tanzania", "variety": "Zanzibar Pepper", "desc": "The Spice Island grows pepper alongside cloves, with guided spice plantation tours.", "color": _ACCENT},
    {"name": "Kottayam, Kerala", "lat": 9.5916, "lon": 76.5222, "country": "India", "variety": "Malabar Pepper", "desc": "Inland Kerala spice trading center handling pepper from the Cardamom Hills.", "color": _EMERALD},
    {"name": "Trivandrum (Thiruvananthapuram)", "lat": 8.5241, "lon": 76.9366, "country": "India", "variety": "Malabar Pepper", "desc": "Kerala's capital and spice research hub. The Indian Institute of Spices Research has headquarters nearby.", "color": _TEAL},
    {"name": "Dak Lak, Vietnam", "lat": 12.7100, "lon": 108.2378, "country": "Vietnam", "variety": "Vietnamese Pepper", "desc": "Central Highlands province known for both coffee and pepper cultivation on volcanic soils.", "color": _PINK},
    {"name": "Kuching Market, Sarawak", "lat": 1.5575, "lon": 110.3441, "country": "Malaysia", "variety": "Sarawak Pepper", "desc": "Sarawak's capital city hosts pepper trading markets and the Sarawak Pepper Board headquarters.", "color": _RED},
    {"name": "Sri Lanka (Matale)", "lat": 7.4675, "lon": 80.6234, "country": "Sri Lanka", "variety": "Sri Lankan Pepper", "desc": "Central Sri Lankan pepper cultivation, historically overshadowed by cinnamon but still significant.", "color": _AMBER},
    {"name": "Goa (Ponda), India", "lat": 15.4000, "lon": 74.0100, "country": "India", "variety": "Goan Pepper", "desc": "Ponda taluka spice plantations where pepper vines are intercropped with cashew, areca nut, and coconut.", "color": _VIOLET},
]

CHILI_HEAT_MAP = [
    {"name": "Tehuacan Valley, Puebla, Mexico", "lat": 18.4500, "lon": -97.4000, "country": "Mexico", "origin": "Capsicum Origin", "desc": "Archaeological site with the oldest known chili seeds (7000 BCE). The birthplace of cultivated Capsicum annuum.", "color": _RED},
    {"name": "Oaxaca Valley, Mexico", "lat": 17.0732, "lon": -96.7266, "country": "Mexico", "origin": "Capsicum Origin", "desc": "Mesoamerican center of chili diversity. Pasilla, chilhuacle, and other rare landraces grow in the valley.", "color": _RED},
    {"name": "Yucatan, Mexico", "lat": 20.7100, "lon": -89.0943, "country": "Mexico", "origin": "Habanero", "desc": "Home of the habanero (DOP). The Yucatan habanero was once the world's hottest pepper (350,000 SHU).", "color": _ORANGE},
    {"name": "Hatch Valley, New Mexico, USA", "lat": 32.6700, "lon": -107.1600, "country": "USA", "origin": "Hatch Chile", "desc": "America's chili capital. Hatch green and red chile are roasted at roadside stands every September.", "color": _EMERALD},
    {"name": "Chimayo, New Mexico, USA", "lat": 35.9930, "lon": -105.9360, "country": "USA", "origin": "Chimayo Chile", "desc": "Heirloom chili grown in the high desert. Chimayo chile has a unique smoky sweetness from the terroir.", "color": _ORANGE},
    {"name": "Sichuan Province, China (Chengdu)", "lat": 30.5728, "lon": 104.0668, "country": "China", "origin": "Sichuan Chili", "desc": "Home of mala (numbing-hot) cuisine. Sichuan uses facing-heaven chilies and Sichuan peppercorn together.", "color": _PINK},
    {"name": "Hunan Province, China (Changsha)", "lat": 28.2282, "lon": 112.9388, "country": "China", "origin": "Hunan Chili", "desc": "Hunan cuisine rivals Sichuan for heat, using chopped fresh chilies, smoked chilies, and chili oil.", "color": _PINK},
    {"name": "Guizhou Province, China", "lat": 26.6470, "lon": 106.6302, "country": "China", "origin": "Guizhou Sour-Spicy", "desc": "Chinese province known for sour-and-spicy chili preparations. The locals say 'not afraid of hot'.", "color": _VIOLET},
    {"name": "Tezpur, Assam, India (Bhut Jolokia)", "lat": 26.6338, "lon": 92.7837, "country": "India", "origin": "Ghost Pepper (Bhut Jolokia)", "desc": "Home of the Bhut Jolokia ghost pepper (1,041,427 SHU), the first chili to break 1 million Scoville.", "color": _RED},
    {"name": "Nagaland, India", "lat": 25.6700, "lon": 94.1100, "country": "India", "origin": "Naga King Chili", "desc": "The Naga King Chili (Raja Mircha) is revered by Naga tribes and closely related to the Bhut Jolokia.", "color": _RED},
    {"name": "Manipur, India", "lat": 24.8170, "lon": 93.9368, "country": "India", "origin": "Umorok (Ghost Pepper)", "desc": "Northeastern Indian state where the ghost pepper is called umorok and used in fiery chutneys.", "color": _ORANGE},
    {"name": "Guntur, Andhra Pradesh, India", "lat": 16.3067, "lon": 80.4365, "country": "India", "origin": "Guntur Sannam", "desc": "India's chili trading capital. Millions of tonnes pass through Guntur's cold storage yards annually.", "color": _AMBER},
    {"name": "Espelette, Basque Country, France", "lat": 43.3444, "lon": -1.4370, "country": "France", "origin": "Piment d'Espelette (AOP)", "desc": "French Basque village famous for its mild, sweet AOP chili, dried on whitewashed house facades.", "color": _EMERALD},
    {"name": "Calabria, Italy (Tropea)", "lat": 38.6750, "lon": 15.9000, "country": "Italy", "origin": "Calabrian Peperoncino", "desc": "Italy's spiciest region. Calabrian peperoncino (chili) is essential in 'Nduja salami and southern cooking.", "color": _GOLD},
    {"name": "Fort Mill, South Carolina, USA", "lat": 35.0074, "lon": -80.9451, "country": "USA", "origin": "Carolina Reaper", "desc": "Birthplace of the Carolina Reaper (2,200,000 SHU), bred by Ed Currie. Current Guinness record holder.", "color": _RED},
    {"name": "Siling Labuyo, Philippines", "lat": 14.5995, "lon": 120.9842, "country": "Philippines", "origin": "Siling Labuyo (Bird's Eye)", "desc": "The fiery Filipino bird's eye chili, essential in adobo, sinigang, and sawsawan dipping sauces.", "color": _TEAL},
    {"name": "Sriracha, Chonburi, Thailand", "lat": 13.1674, "lon": 100.9269, "country": "Thailand", "origin": "Sriracha Sauce Origin", "desc": "Thai coastal town that inspired the world-famous sriracha sauce. Prik khee noo (bird chili) dominates Thai cuisine.", "color": _EMERALD},
    {"name": "Aci Biber Region, Turkey (Urfa)", "lat": 37.1674, "lon": 38.7955, "country": "Turkey", "origin": "Urfa Biber / Aleppo Pepper", "desc": "Southeastern Turkey produces Urfa biber (sun-dried, oily, smoky) and Aleppo-style pepper flakes.", "color": _GOLD},
    {"name": "Szegedi Paprika Region, Hungary", "lat": 46.2530, "lon": 20.1414, "country": "Hungary", "origin": "Hungarian Paprika", "desc": "Szeged is the paprika capital of Hungary and Europe. Hungarian paprika ranges from sweet (edes) to hot (eros).", "color": _AMBER},
    {"name": "Kalocsa, Hungary", "lat": 46.5300, "lon": 18.9800, "country": "Hungary", "origin": "Hungarian Paprika", "desc": "The other great Hungarian paprika town, with a Paprika Museum and annual paprika harvest festival.", "color": _AMBER},
    {"name": "Kashmiri Chili, India", "lat": 34.0837, "lon": 74.7973, "country": "India", "origin": "Kashmiri Mirch", "desc": "Mild, deep red Kashmiri chili prized for color rather than heat. Essential in rogan josh and tandoori.", "color": _VIOLET},
    {"name": "Scotch Bonnet, Jamaica (Kingston)", "lat": 18.1096, "lon": -77.2975, "country": "Jamaica", "origin": "Scotch Bonnet", "desc": "Iconic Caribbean chili used in jerk seasoning. Scotch bonnets (C. chinense) reach 350,000 SHU.", "color": _CYAN},
    {"name": "Aji Amarillo, Peru (Lima)", "lat": -12.0464, "lon": -77.0428, "country": "Peru", "origin": "Aji Amarillo", "desc": "Peru's beloved yellow pepper used in ceviche, aji de gallina, and causa. Part of Peru's Capsicum heritage.", "color": _GOLD},
    {"name": "Malagueta, Bahia, Brazil", "lat": -12.9714, "lon": -38.5124, "country": "Brazil", "origin": "Malagueta Pepper", "desc": "Brazil's signature hot pepper, essential in Bahian cuisine, moqueca, and pimenta sauce.", "color": _BLUE},
    {"name": "Peri-Peri, Mozambique", "lat": -25.9692, "lon": 32.5732, "country": "Mozambique", "origin": "Peri-Peri (Piri-Piri)", "desc": "African bird's eye chili brought by Portuguese traders. Peri-peri chicken is Mozambique's global gift.", "color": _PINK},
    {"name": "Byadgi, Karnataka, India", "lat": 14.6725, "lon": 75.4897, "country": "India", "origin": "Byadgi Chili", "desc": "Famous for its deep red color and mild heat, Byadgi chili is India's premier color chili for curries.", "color": _ORANGE},
]

SPICE_MUSEUMS = [
    {"name": "Spice Museum (Spicy's), Hamburg", "lat": 53.5449, "lon": 9.9883, "country": "Germany", "type": "Museum", "desc": "World's largest spice museum in Hamburg's Speicherstadt warehouse district. Over 900 exhibits spanning 5,000 years of spice history.", "color": _AMBER},
    {"name": "Kerala Spice Trail, Thekkady", "lat": 9.6000, "lon": 77.1640, "country": "India", "type": "Trail/Tour", "desc": "Multi-day walking trail through Kerala's spice plantations: pepper, cardamom, vanilla, clove, and cinnamon.", "color": _EMERALD},
    {"name": "Zanzibar Spice Tour, Stone Town", "lat": -6.1622, "lon": 39.1921, "country": "Tanzania", "type": "Tour", "desc": "Iconic guided tours of Zanzibar's spice farms: clove, nutmeg, cinnamon, pepper, and vanilla growing side by side.", "color": _TEAL},
    {"name": "Kew Gardens Spice Collection, London", "lat": 51.4787, "lon": -0.2955, "country": "United Kingdom", "type": "Botanical Garden", "desc": "Royal Botanic Gardens with historical spice plant collections in the Princess of Wales Conservatory.", "color": _VIOLET},
    {"name": "Penang Spice Garden, Malaysia", "lat": 5.4610, "lon": 100.2100, "country": "Malaysia", "type": "Botanical Garden", "desc": "Tropical spice and herb garden in Georgetown showcasing Southeast Asian culinary plants.", "color": _PINK},
    {"name": "Jardin des Epices, Mahajanga, Madagascar", "lat": -15.7167, "lon": 46.3167, "country": "Madagascar", "type": "Garden/Tour", "desc": "Malagasy spice garden growing vanilla, clove, ylang-ylang, and pepper. Demonstrates traditional curing.", "color": _GOLD},
    {"name": "Spice Bazaar (Misir Carsisi), Istanbul", "lat": 41.0166, "lon": 28.9700, "country": "Turkey", "type": "Historic Market", "desc": "17th-century Ottoman spice market near the Golden Horn. Vendors sell sumac, saffron, Turkish pepper, and baharat.", "color": _ORANGE},
    {"name": "Gewurzmuseum (Spice Museum), Nuremberg", "lat": 49.4521, "lon": 11.0767, "country": "Germany", "type": "Museum", "desc": "Historic city where medieval Safranschou (saffron inspectors) enforced quality. Museum covers Franconian spice trade.", "color": _GOLD},
    {"name": "Mattancherry Spice Warehouses, Kochi", "lat": 9.9577, "lon": 76.2590, "country": "India", "type": "Heritage Warehouse", "desc": "Colonial-era spice warehouses in Fort Kochi's Jew Town where pepper, cardamom, and ginger are still traded.", "color": _EMERALD},
    {"name": "Dutch East India Company Museum, Amsterdam", "lat": 52.3738, "lon": 4.9153, "country": "Netherlands", "type": "Museum", "desc": "Amsterdam's Scheepvaartmuseum tells the story of the VOC and its violent quest to monopolize the spice trade.", "color": _BLUE},
    {"name": "Musee de la Vanille, Reunion Island", "lat": -20.9100, "lon": 55.6100, "country": "Reunion (France)", "type": "Museum", "desc": "Vanilla museum honoring Edmond Albius's 1841 hand-pollination discovery that transformed the vanilla industry.", "color": _GOLD},
    {"name": "Spice Market (Souk al-Attarine), Fez", "lat": 34.0631, "lon": -4.9729, "country": "Morocco", "type": "Historic Market", "desc": "Medieval medina spice souk selling cumin, turmeric, saffron, ras el hanout, and traditional remedies since the 13th century.", "color": _AMBER},
    {"name": "Laura Plantation Spice Tour, Vacherie, LA", "lat": 30.0100, "lon": -90.7700, "country": "USA", "type": "Heritage Plantation", "desc": "Louisiana Creole plantation with historic spice and herb gardens showcasing New World-Old World spice fusion.", "color": _PINK},
    {"name": "Cinnamon Citadel Experience, Galle", "lat": 6.0535, "lon": 80.2210, "country": "Sri Lanka", "type": "Heritage Experience", "desc": "Interactive cinnamon heritage experience showing traditional bark peeling, quilling, and grading in southern Sri Lanka.", "color": _AMBER},
    {"name": "Museum der Kulturen, Basel", "lat": 47.5561, "lon": 7.5886, "country": "Switzerland", "type": "Museum", "desc": "Ethnographic museum with exhibits on global spice trade routes and their cultural impacts.", "color": _CYAN},
    {"name": "Indian Spice Box Gallery, Delhi", "lat": 28.6562, "lon": 77.2167, "country": "India", "type": "Gallery/Museum", "desc": "Cultural gallery near Khari Baoli market documenting India's spice heritage through artifacts and sensory exhibits.", "color": _ORANGE},
    {"name": "Grenada Nutmeg Museum, Gouyave", "lat": 12.1648, "lon": -61.7287, "country": "Grenada", "type": "Museum/Factory", "desc": "Working nutmeg processing station in the 'Nutmeg Isle.' See sorting, grading, and oil extraction of Grenadian nutmeg.", "color": _TEAL},
    {"name": "Hortus Botanicus, Leiden", "lat": 52.1583, "lon": 4.4862, "country": "Netherlands", "type": "Botanical Garden", "desc": "One of Europe's oldest botanical gardens (1590), founded partly to study spice plants from VOC expeditions.", "color": _BLUE},
    {"name": "Pepper Trail, Goa", "lat": 15.4000, "lon": 74.0100, "country": "India", "type": "Trail/Tour", "desc": "Walking tour through Goan spice plantations in Ponda taluka, with cooking demonstrations and Feni tasting.", "color": _EMERALD},
    {"name": "Museu do Oriente, Lisbon", "lat": 38.7007, "lon": -9.1844, "country": "Portugal", "type": "Museum", "desc": "Museum of the Orient documenting Portugal's spice trade empire from Goa to Macau to the Moluccas.", "color": _VIOLET},
    {"name": "Spice Souk, Dubai", "lat": 25.2676, "lon": 55.2973, "country": "UAE", "type": "Market", "desc": "Historic Dubai Creek spice market where frankincense, saffron, cardamom, and dried limes fill the air.", "color": _GOLD},
    {"name": "Tropical Spice Plantation, Goa", "lat": 15.3500, "lon": 74.0500, "country": "India", "type": "Plantation Tour", "desc": "Award-winning Goan organic spice plantation with elephant rides, spice walks, and traditional Goan lunch.", "color": _EMERALD},
    {"name": "Kidichi Persian Baths & Spice Walk, Zanzibar", "lat": -6.1200, "lon": 39.3000, "country": "Tanzania", "type": "Heritage/Tour", "desc": "19th-century Persian baths combined with guided walks through Zanzibar's clove and spice plantations.", "color": _TEAL},
    {"name": "National Pepper Exchange Museum, Kochi", "lat": 9.9700, "lon": 76.2800, "country": "India", "type": "Museum", "desc": "Historic commodity exchange where global pepper prices were set for centuries. Now a heritage museum.", "color": _AMBER},
    {"name": "Saffron Museum, Consuegra, Spain", "lat": 39.4600, "lon": -3.6100, "country": "Spain", "type": "Museum", "desc": "Museum dedicated to La Mancha saffron culture, harvesting traditions, and the annual Rosa del Azafran festival.", "color": _VIOLET},
]

ANCIENT_SPICE_ROUTES = [
    {"name": "Incense Route - Dhofar, Oman", "lat": 17.0151, "lon": 54.0924, "country": "Oman", "route": "Incense Route", "desc": "Southern Arabian source of frankincense. Caravans departed Dhofar carrying incense to the Mediterranean.", "color": _AMBER},
    {"name": "Incense Route - Shabwa, Yemen", "lat": 15.3700, "lon": 47.0200, "country": "Yemen", "route": "Incense Route", "desc": "Capital of the ancient Hadhramaut kingdom and major incense caravan staging point.", "color": _AMBER},
    {"name": "Incense Route - Petra, Jordan", "lat": 30.3285, "lon": 35.4444, "country": "Jordan", "route": "Incense Route", "desc": "Nabataean capital controlling the northern section of the incense route. UNESCO World Heritage Site.", "color": _GOLD},
    {"name": "Incense Route - Gaza, Palestine", "lat": 31.5000, "lon": 34.4667, "country": "Palestine", "route": "Incense Route", "desc": "Mediterranean terminus of the Incense Route where frankincense and myrrh were loaded onto ships for Rome.", "color": _GOLD},
    {"name": "Incense Route - Avdat, Negev", "lat": 30.7930, "lon": 34.7630, "country": "Israel", "route": "Incense Route", "desc": "UNESCO-listed Nabataean way station in the Negev desert on the overland incense and spice route.", "color": _ORANGE},
    {"name": "Maritime Silk Road - Quanzhou, China", "lat": 24.8741, "lon": 118.6757, "country": "China", "route": "Maritime Silk Road (Spice Leg)", "desc": "Song and Yuan dynasty maritime hub exporting Chinese goods and importing Southeast Asian spices.", "color": _CYAN},
    {"name": "Maritime Silk Road - Palembang, Sumatra", "lat": -2.9761, "lon": 104.7754, "country": "Indonesia", "route": "Maritime Silk Road (Spice Leg)", "desc": "Srivijaya capital controlling the Strait of Malacca and spice transshipment from the Moluccas westward.", "color": _TEAL},
    {"name": "Maritime Silk Road - Calicut, India", "lat": 11.2588, "lon": 75.7804, "country": "India", "route": "Maritime Silk Road (Spice Leg)", "desc": "Malabar pepper port linking the Maritime Silk Road to the Indian Ocean spice trade.", "color": _EMERALD},
    {"name": "Maritime Silk Road - Aden, Yemen", "lat": 12.7855, "lon": 45.0187, "country": "Yemen", "route": "Maritime Silk Road (Spice Leg)", "desc": "Red Sea transshipment point where Indian Ocean spice ships met Mediterranean-bound vessels.", "color": _ORANGE},
    {"name": "Maritime Silk Road - Berenike, Egypt", "lat": 23.9083, "lon": 35.4750, "country": "Egypt", "route": "Maritime Silk Road (Spice Leg)", "desc": "Roman Red Sea port importing pepper and cinnamon from India. Archaeological finds include peppercorns.", "color": _RED},
    {"name": "Maritime Silk Road - Muziris (Pattanam), India", "lat": 10.1567, "lon": 76.2100, "country": "India", "route": "Maritime Silk Road (Spice Leg)", "desc": "Lost Roman-era port rediscovered in Kerala. Roman coins and amphorae confirm the pepper trade with Rome.", "color": _EMERALD},
    {"name": "Amber Road - Aquileia, Italy", "lat": 45.7694, "lon": 13.3692, "country": "Italy", "route": "Amber Road", "desc": "Roman city at the southern terminus of the Amber Road, which also carried Baltic and Eastern spices south.", "color": _VIOLET},
    {"name": "Amber Road - Carnuntum, Austria", "lat": 48.1200, "lon": 16.8600, "country": "Austria", "route": "Amber Road", "desc": "Roman legionary camp and trading post on the Danube along the Amber Road corridor.", "color": _VIOLET},
    {"name": "Amber Road - Gdansk, Poland", "lat": 54.3520, "lon": 18.6466, "country": "Poland", "route": "Amber Road", "desc": "Baltic terminus of the ancient Amber Road connecting the Baltic Sea to the Mediterranean via spice trade.", "color": _BLUE},
    {"name": "Silk Road - Samarkand, Uzbekistan", "lat": 39.6542, "lon": 66.9597, "country": "Uzbekistan", "route": "Overland Silk/Spice Road", "desc": "Timur's capital and key Silk Road oasis. Spice caravans stopped here en route from China to Persia.", "color": _PINK},
    {"name": "Silk Road - Bukhara, Uzbekistan", "lat": 39.7747, "lon": 64.4286, "country": "Uzbekistan", "route": "Overland Silk/Spice Road", "desc": "Medieval trading city where spice, silk, and precious stone caravans converged.", "color": _PINK},
    {"name": "Silk Road - Merv, Turkmenistan", "lat": 37.6600, "lon": 62.1600, "country": "Turkmenistan", "route": "Overland Silk/Spice Road", "desc": "Ancient oasis city at the crossroads of the Silk Road. One of the world's largest cities by the 12th century.", "color": _GOLD},
    {"name": "Silk Road - Kashgar, China", "lat": 39.4700, "lon": 75.9900, "country": "China", "route": "Overland Silk/Spice Road", "desc": "Western Chinese oasis city where the northern and southern Silk Road branches reunited. Major spice bazaar.", "color": _CYAN},
    {"name": "Trans-Saharan Route - Timbuktu, Mali", "lat": 16.7735, "lon": -3.0074, "country": "Mali", "route": "Trans-Saharan Spice Route", "desc": "Legendary desert trading city where salt, gold, and North African spices were exchanged.", "color": _AMBER},
    {"name": "Trans-Saharan Route - Sijilmasa, Morocco", "lat": 31.2800, "lon": -4.2800, "country": "Morocco", "route": "Trans-Saharan Spice Route", "desc": "Medieval Moroccan gateway city at the northern edge of the Sahara for the trans-desert caravan trade.", "color": _AMBER},
    {"name": "Spice Route - Muziris to Rome via Myos Hormos", "lat": 26.1800, "lon": 34.2200, "country": "Egypt", "route": "Roman Spice Route", "desc": "Roman Red Sea port of Myos Hormos (Quseir al-Qadim) where Indian spice ships unloaded for overland transport to the Nile.", "color": _RED},
    {"name": "Spice Route - Ostia, Roman Port", "lat": 41.7558, "lon": 12.2912, "country": "Italy", "route": "Roman Spice Route", "desc": "Port of Rome where Alexandrian grain and spice ships docked. Roman pepper warehouses (horrea piperataria) stood nearby.", "color": _RED},
    {"name": "Persian Royal Road - Susa, Iran", "lat": 32.1900, "lon": 48.2600, "country": "Iran", "route": "Persian Royal Road", "desc": "Achaemenid capital and eastern anchor of the Royal Road. Indian spices reached the Mediterranean via this route.", "color": _GOLD},
    {"name": "Persian Royal Road - Sardis, Turkey", "lat": 38.4900, "lon": 28.0400, "country": "Turkey", "route": "Persian Royal Road", "desc": "Lydian capital and western terminus of the Persian Royal Road connecting Persia to the Aegean.", "color": _ORANGE},
    {"name": "Cinnamon Route - Rhapta, Tanzania", "lat": -7.0000, "lon": 39.5000, "country": "Tanzania", "route": "Cinnamon/Cassia Route", "desc": "Ancient East African port mentioned in the Periplus, possibly trading cinnamon bark from Southeast Asia.", "color": _TEAL},
    {"name": "Cinnamon Route - Adulis, Eritrea", "lat": 15.2300, "lon": 39.6500, "country": "Eritrea", "route": "Cinnamon/Cassia Route", "desc": "Aksumite Red Sea port where cinnamon from the East was transshipped toward Egypt and Rome.", "color": _TEAL},
]

# ===============================================================================
# MAP DATA REGISTRY
# ===============================================================================
MODE_DATA = {
    "Spice Islands of Indonesia": SPICE_ISLANDS,
    "Indian Spice Markets": INDIAN_SPICE_MARKETS,
    "Historic Spice Trade Ports": HISTORIC_TRADE_PORTS,
    "Saffron Growing Regions": SAFFRON_REGIONS,
    "Vanilla Heritage": VANILLA_HERITAGE,
    "Cinnamon & Cassia": CINNAMON_CASSIA,
    "Pepper Empire": PEPPER_EMPIRE,
    "Chili Heat Map": CHILI_HEAT_MAP,
    "Spice Museums & Experiences": SPICE_MUSEUMS,
    "Ancient Spice Routes": ANCIENT_SPICE_ROUTES,
}

# Extra column keys per mode for dataframe building
MODE_EXTRA_KEYS = {
    "Spice Islands of Indonesia": ["spice"],
    "Indian Spice Markets": ["spice"],
    "Historic Spice Trade Ports": ["era"],
    "Saffron Growing Regions": ["variety"],
    "Vanilla Heritage": ["variety"],
    "Cinnamon & Cassia": ["variety"],
    "Pepper Empire": ["variety"],
    "Chili Heat Map": ["origin"],
    "Spice Museums & Experiences": ["type"],
    "Ancient Spice Routes": ["route"],
}

# ===============================================================================
# HELPER: BUILD FOLIUM MAP
# ===============================================================================

def _build_map(items: list, mode: str) -> folium.Map:
    """Build a Folium dark-theme map with MarkerCluster for the given items."""
    if not items:
        return folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    avg_lat = sum(it["lat"] for it in items) / len(items)
    avg_lon = sum(it["lon"] for it in items) / len(items)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=3,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name="Spice Locations").add_to(m)

    for item in items:
        name_safe = html_module.escape(item["name"])
        desc_safe = html_module.escape(item["desc"])
        color = item.get("color", _ACCENT)

        extra_lines = ""
        if "country" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Country: {html_module.escape(item["country"])}</span>'
        if "spice" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Spice: {html_module.escape(item["spice"])}</span>'
        if "variety" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Variety: {html_module.escape(item["variety"])}</span>'
        if "era" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Era: {html_module.escape(item["era"])}</span>'
        if "origin" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Origin: {html_module.escape(item["origin"])}</span>'
        if "route" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Route: {html_module.escape(item["route"])}</span>'
        if "type" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Type: {html_module.escape(item["type"])}</span>'

        popup_html = f"""
        <div style="max-width:260px;">
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
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=name_safe,
        ).add_to(cluster)

    return m


# ===============================================================================
# HELPER: BUILD DATAFRAME
# ===============================================================================

def _build_dataframe(items: list, mode: str) -> pd.DataFrame:
    """Build a display DataFrame from item list."""
    extra_keys = MODE_EXTRA_KEYS.get(mode, [])
    rows = []
    for item in items:
        row = {
            "Name": item["name"],
            "Country": item.get("country", ""),
            "Latitude": item["lat"],
            "Longitude": item["lon"],
            "Description": item["desc"],
        }
        for key in extra_keys:
            col_name = key.replace("_", " ").title()
            row[col_name] = item.get(key, "")
        rows.append(row)
    return pd.DataFrame(rows)


# ===============================================================================
# HELPER: CSV EXPORT
# ===============================================================================

def _get_csv(df: pd.DataFrame) -> str:
    """Convert DataFrame to CSV string."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# ===============================================================================
# MAIN RENDER FUNCTION
# ===============================================================================

def render_spice_maps_tab():
    """Main render function for the Spice Routes & Heritage Explorer tab."""

    # ── Glass Tab Header ──
    st.markdown("""
    <div class="tab-header amber">
        <h4>Spice Routes &amp; Heritage Explorer</h4>
        <p>Explore the spice islands, historic trade ports, saffron fields, pepper empires, chili origins, vanilla heritage, and ancient caravan routes that shaped world history.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode Selection
    # ══════════════════════════════════════════
    mode = st.selectbox(
        "Spice Map Mode",
        MODE_OPTIONS,
        key="spice_maps_mode",
        help="Choose a spice category or trade route to explore on the map.",
    )

    icon = MODE_ICONS.get(mode, "🌿")
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
    extra_keys = MODE_EXTRA_KEYS.get(mode, [])

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Locations", len(items))
    with c2:
        st.metric("Countries / Areas", len(countries))
    with c3:
        if extra_keys:
            distinct_vals = set(it.get(extra_keys[0], "") for it in items if it.get(extra_keys[0]))
            st.metric(f"Distinct {extra_keys[0].title()}s", len(distinct_vals))
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

    # Legend row
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
    st.markdown("#### Spice Data")

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
        color = item.get("color", _ACCENT)

        sub_info = ""
        if "country" in item:
            sub_info += html_module.escape(item["country"])
        if "spice" in item:
            sub_info += f" &mdash; {html_module.escape(item['spice'])}"
        if "variety" in item:
            sub_info += f" &mdash; {html_module.escape(item['variety'])}"
        if "era" in item:
            sub_info += f" &mdash; {html_module.escape(item['era'])}"
        if "origin" in item:
            sub_info += f" &mdash; {html_module.escape(item['origin'])}"
        if "route" in item:
            sub_info += f" &mdash; {html_module.escape(item['route'])}"
        if "type" in item:
            sub_info += f" &mdash; {html_module.escape(item['type'])}"

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
            <div style="width:10px; height:56px; border-radius:5px; background:{color};
                        margin-right:0.75rem; flex-shrink:0;"></div>
            <div>
                <div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{name_safe}</div>
                <div style="color:#8b97b0; font-size:0.75rem;">{sub_info}</div>
                <div style="color:#5a6580; font-size:0.7rem;">{desc_safe[:140]}</div>
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
        file_name=f"spice_{filename}.csv",
        mime="text/csv",
        key="spice_download",
    )

    # ══════════════════════════════════════════
    # SECTION 8: Mode-Specific Insights
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Insights & Context")

    _insight = MODE_INSIGHTS.get(mode, "")
    if _insight:
        st.markdown(
            f'<div style="background:{_CARD}; border:1px solid {_BORDER}; border-radius:8px; '
            f'padding:1rem; color:{_TEXT2}; font-size:0.85rem; line-height:1.6;">'
            f'{html_module.escape(_insight)}</div>',
            unsafe_allow_html=True,
        )
