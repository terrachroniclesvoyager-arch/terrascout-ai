# -*- coding: utf-8 -*-
"""
Mystery & Conspiracy Maps module for TerraScout AI.
Curated database of locations associated with unexplained phenomena,
secret installations, ancient enigmas, and popular conspiracy theories.
All data is from public records and presented for EDUCATIONAL and
ENTERTAINMENT purposes only - exploring popular culture and folklore.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import html as html_module

# ===================================================================
# DATA: 10 MAP MODES WITH CURATED LOCATIONS (15-25 each)
# ===================================================================

# ---------------------------------------------------------------
# 1. SECRET MILITARY BASES (22 locations)
# ---------------------------------------------------------------
SECRET_MILITARY_BASES = [
    {"name": "Area 51 (Groom Lake)", "lat": 37.2350, "lon": -115.8111,
     "country": "United States", "year": "1955",
     "notes": "USAF facility in the Nevada Test and Training Range. Officially acknowledged by CIA in 2013. Associated with advanced aircraft testing and UFO lore."},
    {"name": "Pine Gap (Joint Defence Facility)", "lat": -23.7990, "lon": 133.7370,
     "country": "Australia", "year": "1970",
     "notes": "US-Australian satellite surveillance station near Alice Springs, Northern Territory. One of the largest ECHELON signal interception facilities."},
    {"name": "RAF Menwith Hill", "lat": 54.0009, "lon": -1.6884,
     "country": "United Kingdom", "year": "1954",
     "notes": "Royal Air Force station in North Yorkshire. NSA's largest overseas signals intelligence facility with distinctive golf-ball radomes."},
    {"name": "Diego Garcia", "lat": -7.3195, "lon": 72.4229,
     "country": "British Indian Ocean Territory", "year": "1971",
     "notes": "Joint US-UK military base on a remote atoll in the Indian Ocean. Indigenous Chagossians forcibly removed to make way for the base."},
    {"name": "Kapustin Yar", "lat": 48.5772, "lon": 46.3467,
     "country": "Russia", "year": "1946",
     "notes": "Soviet rocket launch and weapons development site in Astrakhan Oblast. Often called Russia's Area 51 due to numerous UFO reports."},
    {"name": "Tonopah Test Range", "lat": 38.0609, "lon": -116.7830,
     "country": "United States", "year": "1957",
     "notes": "USAF facility where the F-117 Nighthawk stealth fighter was secretly developed, tested, and operationally based for years."},
    {"name": "Dulce Base (alleged)", "lat": 36.9336, "lon": -106.9989,
     "country": "United States", "year": "1979",
     "notes": "Conspiracy theory alleges a secret underground base beneath Archuleta Mesa, New Mexico. No physical evidence has ever been found."},
    {"name": "Camp Peary (The Farm)", "lat": 37.4370, "lon": -76.7617,
     "country": "United States", "year": "1942",
     "notes": "CIA covert training facility near Williamsburg, Virginia. Officially designated the Armed Forces Experimental Training Activity."},
    {"name": "Mezhgorye (Mount Yamantau)", "lat": 54.2606, "lon": 58.1050,
     "country": "Russia", "year": "1979",
     "notes": "Closed town near Mount Yamantau in Bashkortostan. Suspected massive underground nuclear bunker complex. Access strictly prohibited."},
    {"name": "White Sands Missile Range", "lat": 32.3899, "lon": -106.4787,
     "country": "United States", "year": "1945",
     "notes": "Largest military installation in the US at 3,200 sq mi. Site of the first nuclear detonation (Trinity test, July 16, 1945)."},
    {"name": "Woomera Test Range", "lat": -31.1583, "lon": 136.8325,
     "country": "Australia", "year": "1947",
     "notes": "122,000 sq km restricted weapons testing area in South Australia. Largest weapons testing range in the Western world."},
    {"name": "Zhitkur Underground Facility", "lat": 48.7200, "lon": 45.5200,
     "country": "Russia", "year": "1950s",
     "notes": "Rumored underground facility near Kapustin Yar, Volgograd Oblast. Details remain classified by the Russian government."},
    {"name": "Jiuquan Satellite Launch Center", "lat": 40.9581, "lon": 100.2914,
     "country": "China", "year": "1958",
     "notes": "China's first and largest space launch facility in the Gobi Desert. Originally a top-secret military missile testing site."},
    {"name": "Rudloe Manor", "lat": 51.4050, "lon": -2.2308,
     "country": "United Kingdom", "year": "1940",
     "notes": "Former RAF station in Wiltshire. Long rumored to have been the UK's secret UFO investigation and reporting centre."},
    {"name": "Dugway Proving Ground", "lat": 40.1789, "lon": -112.9452,
     "country": "United States", "year": "1942",
     "notes": "US Army facility in Utah for testing chemical and biological defence systems. Multiple containment incidents have been documented."},
    {"name": "Porton Down", "lat": 51.1322, "lon": -1.7073,
     "country": "United Kingdom", "year": "1916",
     "notes": "UK government military science park in Wiltshire. Chemical and biological defence research since World War I. Controversial human testing history."},
    {"name": "Vandenberg Space Force Base", "lat": 34.7420, "lon": -120.5724,
     "country": "United States", "year": "1941",
     "notes": "Major military space launch facility on the California coast. Used for polar orbit satellite launches and ICBM testing."},
    {"name": "Baikonur Cosmodrome", "lat": 45.9650, "lon": 63.3050,
     "country": "Kazakhstan", "year": "1955",
     "notes": "World's first and largest space launch facility. Originally a top-secret Soviet military installation hidden from Western intelligence."},
    {"name": "Negev Nuclear Research Center (Dimona)", "lat": 31.0015, "lon": 35.1445,
     "country": "Israel", "year": "1958",
     "notes": "Israeli nuclear facility in the Negev desert. Israel maintains a policy of nuclear ambiguity regarding its weapons capabilities."},
    {"name": "Gakona HAARP Facility", "lat": 62.3933, "lon": -145.1500,
     "country": "United States", "year": "1993",
     "notes": "High-frequency Active Auroral Research Program in Alaska. Subject of numerous conspiracy theories about weather control and mind control."},
    {"name": "Kapustin Yar Cosmodrome", "lat": 48.5700, "lon": 46.2500,
     "country": "Russia", "year": "1947",
     "notes": "First Soviet rocket launch site. V-2 derivative launches began here. Still active for military satellite launches."},
    {"name": "Misawa Air Base (SIGINT)", "lat": 40.7032, "lon": 141.3686,
     "country": "Japan", "year": "1938",
     "notes": "USAF base in northern Honshu. Major signals intelligence collection site with the Security Hill SIGINT facility."},
]

# ---------------------------------------------------------------
# 2. BERMUDA TRIANGLE & ANOMALY ZONES (18 locations)
# ---------------------------------------------------------------
BERMUDA_TRIANGLE_ANOMALY_ZONES = [
    {"name": "Bermuda Triangle - Miami Vertex", "lat": 25.7617, "lon": -80.1918,
     "country": "United States", "year": "1964",
     "notes": "Southern vertex of the Bermuda Triangle. Named by Vincent Gaddis in his 1964 Argosy magazine article on mysterious disappearances."},
    {"name": "Bermuda Triangle - Bermuda Vertex", "lat": 32.3078, "lon": -64.7505,
     "country": "Bermuda", "year": "1964",
     "notes": "Northern vertex. The triangle encompasses approximately 500,000 square miles of the western Atlantic Ocean."},
    {"name": "Bermuda Triangle - San Juan Vertex", "lat": 18.4655, "lon": -66.1057,
     "country": "Puerto Rico", "year": "1964",
     "notes": "Eastern vertex. Region of Gulf Stream convergence and deep ocean trenches including the 8,376 m Puerto Rico Trench."},
    {"name": "Flight 19 Departure Point", "lat": 26.0712, "lon": -80.1528,
     "country": "United States", "year": "1945",
     "notes": "Five TBM Avenger torpedo bombers departed Fort Lauderdale NAS on Dec 5, 1945. All five aircraft and 14 airmen vanished without trace."},
    {"name": "USS Cyclops Last Known Position", "lat": 25.0000, "lon": -68.0000,
     "country": "Atlantic Ocean", "year": "1918",
     "notes": "US Navy collier with 306 crew vanished without distress signal. The largest non-combat loss of life in US Navy history."},
    {"name": "Dragon's Triangle (Devil's Sea)", "lat": 30.0000, "lon": 140.0000,
     "country": "Japan", "year": "1952",
     "notes": "Region south of Tokyo where the Japanese government declared a danger zone after mysterious vessel losses in the early 1950s."},
    {"name": "Michigan Triangle", "lat": 43.5000, "lon": -87.0000,
     "country": "United States", "year": "1950",
     "notes": "Region in Lake Michigan associated with aircraft and ship disappearances including Northwest Airlines Flight 2501 in 1950."},
    {"name": "Bridgewater Triangle", "lat": 41.9067, "lon": -71.0067,
     "country": "United States", "year": "1983",
     "notes": "200 sq mile area in southeastern Massachusetts. Named by cryptozoologist Loren Coleman. Reported paranormal activity since colonial era."},
    {"name": "Bass Strait Triangle", "lat": -39.5000, "lon": 145.5000,
     "country": "Australia", "year": "1978",
     "notes": "Waters between Australia and Tasmania. Site of the Frederick Valentich disappearance on October 21, 1978."},
    {"name": "Sargasso Sea Centre", "lat": 28.0000, "lon": -66.0000,
     "country": "Atlantic Ocean", "year": "Ancient",
     "notes": "Region of calm within the Bermuda Triangle. The only sea bounded by ocean currents rather than land. Feared by ancient sailors."},
    {"name": "Bennington Triangle", "lat": 42.8800, "lon": -73.1550,
     "country": "United States", "year": "1992",
     "notes": "Region of southwestern Vermont around Glastenbury Mountain. Multiple unexplained disappearances between 1945 and 1950."},
    {"name": "Mapimi Silent Zone", "lat": 26.6900, "lon": -103.7500,
     "country": "Mexico", "year": "1966",
     "notes": "Desert region in Durango where radio signals allegedly cannot be received. Now a UNESCO biosphere reserve."},
    {"name": "Vile Vortex - South Atlantic Anomaly", "lat": -26.0000, "lon": -37.0000,
     "country": "South Atlantic", "year": "1958",
     "notes": "Region where the Van Allen radiation belt dips closest to Earth's surface. Disrupts satellites and spacecraft electronics passing overhead."},
    {"name": "Vile Vortex - Algerian Megalith Zone", "lat": 26.5700, "lon": 1.6400,
     "country": "Algeria", "year": "1972",
     "notes": "One of twelve hypothesized anomaly zones mapped by researcher Ivan T. Sanderson in his global Vile Vortex theory."},
    {"name": "Vile Vortex - Hamakulia (Hawaii)", "lat": 19.5000, "lon": -155.5000,
     "country": "United States", "year": "1972",
     "notes": "Hawaiian anomaly zone in Sanderson's global grid pattern. Located near the active volcanic region of the Big Island."},
    {"name": "Lake Anjikuni Disappearance Site", "lat": 62.1700, "lon": -100.0500,
     "country": "Canada", "year": "1930",
     "notes": "Alleged mass disappearance of an entire Inuit village in Nunavut. Story is widely considered apocryphal by historians."},
    {"name": "Formosa Triangle (Pacific)", "lat": 22.0000, "lon": 125.0000,
     "country": "Pacific Ocean", "year": "1960s",
     "notes": "Region east of Taiwan where numerous aircraft and vessels have reportedly vanished. Less well-known cousin of the Bermuda Triangle."},
    {"name": "Superstition Mountains Anomaly", "lat": 33.4500, "lon": -111.4000,
     "country": "United States", "year": "1891",
     "notes": "Arizona mountain range associated with compass anomalies, the Lost Dutchman Gold Mine legend, and unexplained disappearances."},
]

# ---------------------------------------------------------------
# 3. ANCIENT ALIEN THEORY SITES (22 locations)
# ---------------------------------------------------------------
ANCIENT_ALIEN_THEORY_SITES = [
    {"name": "Nazca Lines", "lat": -14.7350, "lon": -75.1300,
     "country": "Peru", "year": "~500 BCE",
     "notes": "Massive geoglyphs in the Nazca Desert. Over 800 straight lines, 300 geometric figures, and 70 animal and plant biomorphs."},
    {"name": "Pumapunku (Tiwanaku)", "lat": -16.5616, "lon": -68.6797,
     "country": "Bolivia", "year": "~536 CE",
     "notes": "Pre-Columbian complex with precision-cut stone blocks. H-shaped interlocking blocks carved with sub-millimetre accuracy."},
    {"name": "Gobekli Tepe", "lat": 37.2232, "lon": 38.9224,
     "country": "Turkey", "year": "~9500 BCE",
     "notes": "Oldest known monumental structures on Earth. Predates agriculture, pottery, and the written word by thousands of years."},
    {"name": "Baalbek (Heliopolis)", "lat": 34.0069, "lon": 36.2039,
     "country": "Lebanon", "year": "~7000 BCE",
     "notes": "Temple complex with the Trilithon: three stones each weighing approximately 800 tonnes. The largest cut stones in all of antiquity."},
    {"name": "Easter Island (Rapa Nui)", "lat": -27.1127, "lon": -109.3497,
     "country": "Chile", "year": "~1250 CE",
     "notes": "887 monolithic Moai statues carved by the Rapa Nui people. Average weight 14 tonnes, tallest stands 10 metres high."},
    {"name": "Sacsayhuaman", "lat": -13.5086, "lon": -71.9822,
     "country": "Peru", "year": "~1100 CE",
     "notes": "Inca citadel above Cusco with walls of precisely fitted polygonal boulders, some weighing well over 100 tonnes."},
    {"name": "Great Pyramid of Giza", "lat": 29.9792, "lon": 31.1342,
     "country": "Egypt", "year": "~2560 BCE",
     "notes": "Last surviving Wonder of the Ancient World. Aligned to true north within 3/60th of a degree with 2.3 million stone blocks."},
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262,
     "country": "United Kingdom", "year": "~3000 BCE",
     "notes": "Neolithic stone circle on Salisbury Plain. Bluestones transported approximately 150 miles from the Preseli Hills in Wales."},
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8438,
     "country": "Mexico", "year": "~200 BCE",
     "notes": "Ancient Mesoamerican city whose builders remain unknown. The Avenue of the Dead aligns 15.5 degrees east of true north."},
    {"name": "Yonaguni Monument", "lat": 24.4353, "lon": 123.0101,
     "country": "Japan", "year": "~8000 BCE?",
     "notes": "Underwater rock formation off Yonaguni Island. Scientists continue to debate whether it is natural or an ancient man-made structure."},
    {"name": "Derinkuyu Underground City", "lat": 38.3744, "lon": 34.7347,
     "country": "Turkey", "year": "~800 BCE",
     "notes": "18-story underground city in Cappadocia capable of sheltering 20,000 people with livestock, food stores, and ventilation shafts."},
    {"name": "Nan Madol", "lat": 6.8438, "lon": 158.3350,
     "country": "Micronesia", "year": "~1180 CE",
     "notes": "Ruined city built on 92 artificial islets with basalt columns weighing up to 50 tonnes each. Called the Venice of the Pacific."},
    {"name": "Carnac Stones", "lat": 47.5950, "lon": -3.0717,
     "country": "France", "year": "~4500 BCE",
     "notes": "Over 3,000 prehistoric standing stones arranged in precise rows in Brittany. The largest megalithic site in the world."},
    {"name": "Gunung Padang", "lat": -6.9944, "lon": 107.0564,
     "country": "Indonesia", "year": "~25000 BCE?",
     "notes": "Megalithic site in West Java. Controversial claims of being the oldest pyramid structure on Earth based on ground-penetrating radar."},
    {"name": "Sigiriya (Lion Rock)", "lat": 7.9570, "lon": 80.7603,
     "country": "Sri Lanka", "year": "~477 CE",
     "notes": "Ancient rock fortress with advanced hydraulic water gardens and a polished mirror wall. UNESCO World Heritage Site."},
    {"name": "Antikythera Mechanism Site", "lat": 35.8600, "lon": 23.3000,
     "country": "Greece", "year": "~205 BCE",
     "notes": "Ancient Greek analog computer recovered from a shipwreck. Contains over 30 meshing bronze gears for astronomical calculations."},
    {"name": "Piri Reis Map Origin (Istanbul)", "lat": 41.0082, "lon": 28.9784,
     "country": "Turkey", "year": "1513",
     "notes": "Ottoman admiral's map showing coastlines of South America and allegedly Antarctica. Some claim it depicts an ice-free Antarctic coast."},
    {"name": "Tiahuanaco Sun Gate", "lat": -16.5546, "lon": -68.6733,
     "country": "Bolivia", "year": "~400 CE",
     "notes": "Monolithic stone archway carved from a single 10-tonne block of andesite. Intricate calendar carvings of debated significance."},
    {"name": "Ollantaytambo", "lat": -13.2581, "lon": -72.2636,
     "country": "Peru", "year": "~1400 CE",
     "notes": "Inca fortress with enormous precisely fitted stone blocks transported from quarries six kilometres across the Urubamba valley."},
    {"name": "Abu Simbel", "lat": 22.3360, "lon": 31.6256,
     "country": "Egypt", "year": "~1264 BCE",
     "notes": "Massive rock-cut temples of Ramesses II. Precisely aligned so that sunlight illuminates inner sanctum on two specific days per year."},
    {"name": "Gobekli Tepe Enclosure D", "lat": 37.2233, "lon": 38.9225,
     "country": "Turkey", "year": "~9000 BCE",
     "notes": "Largest and most elaborate enclosure with T-shaped pillars depicting animals. Deliberately and mysteriously buried after construction."},
    {"name": "Dogon Cliff Dwellings (Bandiagara)", "lat": 14.3500, "lon": -3.6100,
     "country": "Mali", "year": "~1490 CE",
     "notes": "Cliff settlements of the Dogon people who possessed surprising astronomical knowledge, including details about the Sirius star system."},
]

# ---------------------------------------------------------------
# 4. UNDERGROUND BUNKERS & TUNNELS (22 locations)
# ---------------------------------------------------------------
UNDERGROUND_BUNKERS_TUNNELS = [
    {"name": "NORAD Cheyenne Mountain Complex", "lat": 38.7446, "lon": -104.8463,
     "country": "United States", "year": "1966",
     "notes": "North American Aerospace Defense Command complex built 2,000 feet inside Cheyenne Mountain, Colorado Springs."},
    {"name": "Raven Rock Mountain Complex (Site R)", "lat": 39.7388, "lon": -77.4264,
     "country": "United States", "year": "1953",
     "notes": "Alternate Pentagon near Blue Ridge Summit, Pennsylvania. Underground command facility for the Department of Defense."},
    {"name": "Mount Weather Emergency Operations", "lat": 39.1624, "lon": -77.8900,
     "country": "United States", "year": "1959",
     "notes": "FEMA continuity-of-government facility in Bluemont, Virginia. Designed to house civilian government leadership during nuclear war."},
    {"name": "Burlington Bunker (Site 3)", "lat": 51.3464, "lon": -2.2305,
     "country": "United Kingdom", "year": "1956",
     "notes": "Cold War government relocation bunker beneath Corsham, Wiltshire. A 35-acre underground city capable of housing 4,000 people."},
    {"name": "Sonnenberg Tunnel Shelter", "lat": 47.0502, "lon": 8.3093,
     "country": "Switzerland", "year": "1976",
     "notes": "Largest civilian nuclear shelter in the world, built inside a highway tunnel in Lucerne. Designed for 20,000 people."},
    {"name": "Greenbrier Bunker", "lat": 37.7796, "lon": -80.3009,
     "country": "United States", "year": "1958",
     "notes": "Secret Congressional fallout shelter beneath The Greenbrier resort in White Sulphur Springs, West Virginia. Exposed by journalist in 1992."},
    {"name": "Kelvedon Hatch Nuclear Bunker", "lat": 51.6474, "lon": 0.2519,
     "country": "United Kingdom", "year": "1952",
     "notes": "Cold War regional government headquarters in Essex. Declassified and now open as a public museum."},
    {"name": "Kosvinsky Kamen (Ural Mountains)", "lat": 59.5000, "lon": 59.0667,
     "country": "Russia", "year": "1990s",
     "notes": "Deep underground command facility in the Ural Mountains. Believed to be a critical node in Russia's nuclear dead-hand system."},
    {"name": "Balaklava Submarine Base", "lat": 44.5000, "lon": 33.5969,
     "country": "Ukraine", "year": "1961",
     "notes": "Top-secret Soviet submarine base tunnelled into a mountain in Crimea. Could shelter 3,000 people from nuclear attack. Now a museum."},
    {"name": "Zeljava Air Base", "lat": 44.8647, "lon": 15.7669,
     "country": "Croatia/Bosnia", "year": "1968",
     "notes": "Largest underground air base in former Yugoslavia. Aircraft hangars and command centres tunnelled into Pljesevica mountain."},
    {"name": "Beijing Underground City", "lat": 39.8933, "lon": 116.3930,
     "country": "China", "year": "1969",
     "notes": "Network of tunnels beneath Beijing built during Sino-Soviet tensions under Mao's orders. Partially open for tours."},
    {"name": "Vivos xPoint", "lat": 43.4050, "lon": -103.5178,
     "country": "United States", "year": "1942",
     "notes": "575 former Army munitions bunkers in the Black Hills of South Dakota converted into a modern survival community."},
    {"name": "Kinmen Underground Hospital", "lat": 24.4360, "lon": 118.3622,
     "country": "Taiwan", "year": "1978",
     "notes": "Military hospital carved into solid granite during Taiwan Strait tensions. Now a tourist attraction on Kinmen Island."},
    {"name": "Hack Green Nuclear Bunker", "lat": 53.0210, "lon": -2.4757,
     "country": "United Kingdom", "year": "1940",
     "notes": "Former ROTOR radar and Cold War nuclear reporting station in Cheshire. Now a museum with preserved Cold War equipment."},
    {"name": "Swiss National Redoubt (Sargans)", "lat": 47.0446, "lon": 9.4434,
     "country": "Switzerland", "year": "1940",
     "notes": "Part of Switzerland's Alpine fortress system. Artillery positions hidden behind fake barn doors and rock faces."},
    {"name": "Sonneberg Air Defence Bunker", "lat": 50.3500, "lon": 11.1667,
     "country": "Germany", "year": "1979",
     "notes": "Former East German (NVA) underground air defence command centre in the forests of Thuringia."},
    {"name": "Wieliczka Salt Mine Tunnels", "lat": 49.9833, "lon": 20.0556,
     "country": "Poland", "year": "1290",
     "notes": "UNESCO World Heritage site with 287 km of tunnels, underground chapels carved from salt, 9 levels reaching 327 metres deep."},
    {"name": "Cu Chi Tunnels", "lat": 11.1414, "lon": 106.4635,
     "country": "Vietnam", "year": "1948",
     "notes": "250 km network used by Viet Cong during the Vietnam War. Three levels deep with hospitals, command centres, and weapons factories."},
    {"name": "Paris Catacombs", "lat": 48.8339, "lon": 2.3323,
     "country": "France", "year": "1786",
     "notes": "Ossuary holding the remains of over six million people in tunnels beneath Paris. Only a small section is open to the public."},
    {"name": "Odessa Catacombs", "lat": 46.4217, "lon": 30.7233,
     "country": "Ukraine", "year": "1830s",
     "notes": "Estimated 2,500 km of tunnels beneath Odessa. The largest catacomb system in the world. Mostly unmapped and extremely dangerous."},
    {"name": "DMZ Third Tunnel of Aggression", "lat": 37.9580, "lon": 126.6760,
     "country": "South Korea", "year": "1978",
     "notes": "North Korean invasion tunnel discovered under the Demilitarized Zone in 1978. Designed to move 30,000 troops per hour."},
    {"name": "Edinburgh Vaults (South Bridge)", "lat": 55.9494, "lon": -3.1878,
     "country": "United Kingdom", "year": "1788",
     "notes": "Hidden chambers beneath South Bridge arches. Sealed for nearly 200 years, rediscovered in 1985. Reported paranormal activity."},
]

# ---------------------------------------------------------------
# 5. CROP CIRCLE HOTSPOTS (17 locations)
# ---------------------------------------------------------------
CROP_CIRCLE_HOTSPOTS = [
    {"name": "Wiltshire Crop Circle Heartland", "lat": 51.3500, "lon": -1.8500,
     "country": "United Kingdom", "year": "1980s",
     "notes": "Wiltshire is the global epicentre of crop circle activity, with hundreds of increasingly complex formations appearing annually."},
    {"name": "Avebury Stone Circle Area", "lat": 51.4288, "lon": -1.8544,
     "country": "United Kingdom", "year": "1990s",
     "notes": "Neolithic henge monument surrounded by frequent crop circle appearances. The ancient stones are believed to attract formations."},
    {"name": "Silbury Hill", "lat": 51.4157, "lon": -1.8573,
     "country": "United Kingdom", "year": "1990s",
     "notes": "Largest prehistoric artificial mound in Europe at 40 metres tall. Crop circles frequently appear in surrounding farmland."},
    {"name": "Milk Hill (White Horse)", "lat": 51.3585, "lon": -1.8502,
     "country": "United Kingdom", "year": "2001",
     "notes": "Site of the largest crop circle ever recorded: a massive design of 409 circles spanning 238 metres, appeared on August 12, 2001."},
    {"name": "Stonehenge Environs", "lat": 51.1789, "lon": -1.8262,
     "country": "United Kingdom", "year": "1996",
     "notes": "Multiple formations appear near the ancient stone circle. The famous Julia Set fractal pattern appeared in 1996 by the A303 road."},
    {"name": "Alton Barnes (Vale of Pewsey)", "lat": 51.3520, "lon": -1.8400,
     "country": "United Kingdom", "year": "1990",
     "notes": "Famous pictogram formation of 1990 that brought worldwide media attention to crop circles and sparked the modern phenomenon."},
    {"name": "Chilbolton Radio Observatory", "lat": 51.1447, "lon": -1.4370,
     "country": "United Kingdom", "year": "2001",
     "notes": "Site of the 2001 Arecibo Reply and alien Face formations that appeared near a radio telescope. Among the most debated circles."},
    {"name": "Crabwood Farmhouse", "lat": 51.0700, "lon": -1.3900,
     "country": "United Kingdom", "year": "2002",
     "notes": "Location of the elaborate alien face and binary code disk formation in August 2002. The binary code contained an ASCII message."},
    {"name": "Barbury Castle Hillfort", "lat": 51.4850, "lon": -1.7823,
     "country": "United Kingdom", "year": "1991",
     "notes": "Iron Age hillfort near Swindon. Site of the famous 1991 triangular crop circle formation that appeared overnight."},
    {"name": "East Field (Alton Priors)", "lat": 51.3540, "lon": -1.8350,
     "country": "United Kingdom", "year": "1990s",
     "notes": "One of the most frequently targeted fields for crop circles. Dozens of major formations have been documented over three decades."},
    {"name": "Tully Saucer Nest (Queensland)", "lat": -18.0000, "lon": 145.9300,
     "country": "Australia", "year": "1966",
     "notes": "Circular depression found in a lagoon in January 1966. Considered one of the earliest modern reports resembling crop circle phenomena."},
    {"name": "Raisting Satellite Earth Station", "lat": 47.9000, "lon": 11.1200,
     "country": "Germany", "year": "2014",
     "notes": "Crop circle formations have appeared near this Bavarian satellite communications facility on multiple occasions."},
    {"name": "Robella (Piedmont)", "lat": 45.0800, "lon": 8.0800,
     "country": "Italy", "year": "2013",
     "notes": "Italian crop circle hotspot in the Piedmont region. Multiple intricate geometric formations documented in wheat fields."},
    {"name": "Chiseldon Formation Site", "lat": 51.5100, "lon": -1.7600,
     "country": "United Kingdom", "year": "2009",
     "notes": "Fields near Swindon, Wiltshire where multiple elaborate mathematical formations have appeared over several summers."},
    {"name": "Cley Hill (Warminster)", "lat": 51.2050, "lon": -2.2550,
     "country": "United Kingdom", "year": "2010",
     "notes": "Prominent hill near the town of Warminster, long associated with both crop circles and alleged UFO activity since the 1960s."},
    {"name": "Stadskanaal Formation Site", "lat": 52.9900, "lon": 6.9500,
     "country": "Netherlands", "year": "2009",
     "notes": "Dutch crop circle hotspot in Groningen province. Netherlands is the second most active country for crop formations after the UK."},
    {"name": "Hoeven Formation Site", "lat": 51.5800, "lon": 4.5600,
     "country": "Netherlands", "year": "2013",
     "notes": "North Brabant location where several notable Dutch crop formations have been documented and photographed from the air."},
]

# ---------------------------------------------------------------
# 6. FAMOUS UFO SIGHTING LOCATIONS (22 locations)
# ---------------------------------------------------------------
FAMOUS_UFO_SIGHTINGS = [
    {"name": "Roswell (Foster Ranch)", "lat": 33.9425, "lon": -105.0103,
     "country": "United States", "year": "1947",
     "notes": "Debris recovered June 1947. USAF initially announced a flying disc, then retracted to weather balloon. The most famous UFO case in history."},
    {"name": "Rendlesham Forest", "lat": 52.0835, "lon": 1.4355,
     "country": "United Kingdom", "year": "1980",
     "notes": "Series of reported sightings by USAF personnel near RAF Woodbridge, December 1980. Called Britain's Roswell."},
    {"name": "Phoenix Lights", "lat": 33.4484, "lon": -112.0740,
     "country": "United States", "year": "1997",
     "notes": "Massive V-shaped formation of lights observed by thousands of witnesses across Arizona on the evening of March 13, 1997."},
    {"name": "Belgian UFO Wave (Brussels)", "lat": 50.8503, "lon": 4.3517,
     "country": "Belgium", "year": "1989",
     "notes": "Triangular UFOs reported by thousands of witnesses from Nov 1989 to Apr 1990. The Belgian Air Force scrambled F-16 jets."},
    {"name": "Varginha UFO Incident", "lat": -21.5511, "lon": -45.4303,
     "country": "Brazil", "year": "1996",
     "notes": "Alleged UFO crash and creature capture in Minas Gerais, January 1996. Multiple civilian and military witnesses gave testimony."},
    {"name": "Tunguska Event Site", "lat": 60.8860, "lon": 101.8940,
     "country": "Russia", "year": "1908",
     "notes": "Massive explosion flattened 2,150 sq km of Siberian taiga forest on June 30, 1908. No impact crater has ever been found."},
    {"name": "Kecksburg Crash Site", "lat": 40.1848, "lon": -79.4612,
     "country": "United States", "year": "1965",
     "notes": "Fireball observed Dec 9, 1965 across six US states and Canada. An acorn-shaped object was reportedly recovered by the US Army."},
    {"name": "Hessdalen Lights Valley", "lat": 62.8200, "lon": 11.2000,
     "country": "Norway", "year": "1981",
     "notes": "Persistent unexplained luminous phenomena observed in Hessdalen valley since 1981. Studied by the academic Project Hessdalen."},
    {"name": "Shag Harbour Incident", "lat": 43.4606, "lon": -65.7206,
     "country": "Canada", "year": "1967",
     "notes": "Illuminated object observed crashing into the harbour on Oct 4, 1967. An official Canadian government investigation was conducted."},
    {"name": "Skinwalker Ranch", "lat": 40.2586, "lon": -109.8879,
     "country": "United States", "year": "1994",
     "notes": "512-acre ranch in the Uintah Basin, Utah. Studied by NIDS and later by the Pentagon's AAWSAP program under DIA contract."},
    {"name": "Dyatlov Pass Incident", "lat": 61.7543, "lon": 59.4567,
     "country": "Russia", "year": "1959",
     "notes": "Nine experienced hikers died under mysterious circumstances in the Ural Mountains in February 1959. The cause remains debated."},
    {"name": "Tehran UFO Incident", "lat": 35.6892, "lon": 51.3890,
     "country": "Iran", "year": "1976",
     "notes": "Iranian Air Force jets scrambled to intercept a bright UFO over Tehran on Sept 19, 1976. Aircraft instruments reportedly malfunctioned."},
    {"name": "Westall UFO Encounter", "lat": -37.9400, "lon": 145.1000,
     "country": "Australia", "year": "1966",
     "notes": "Over 200 students and teachers at Westall High School near Melbourne witnessed a UFO landing on April 6, 1966."},
    {"name": "Wycliffe Well (Stuart Highway)", "lat": -20.7950, "lon": 134.1933,
     "country": "Australia", "year": "1940s",
     "notes": "Self-proclaimed UFO capital of Australia along the Stuart Highway. Documented sightings since World War II."},
    {"name": "Aurora, Texas Crash Site", "lat": 33.0585, "lon": -97.5061,
     "country": "United States", "year": "1897",
     "notes": "Alleged airship crash on April 17, 1897, reported in the Dallas Morning News. Widely considered a newspaper hoax of the era."},
    {"name": "Stephenville, Texas Sightings", "lat": 32.2207, "lon": -98.2023,
     "country": "United States", "year": "2008",
     "notes": "Dozens of residents reported large silent objects with bright lights over Stephenville in January 2008. MUFON investigation followed."},
    {"name": "Colares UFO Flap (Operation Saucer)", "lat": -0.9300, "lon": -48.4900,
     "country": "Brazil", "year": "1977",
     "notes": "Intense wave of UFO sightings in Para state. Brazilian Air Force launched classified Operation Saucer to investigate."},
    {"name": "Ruwa Zimbabwe School Encounter", "lat": -17.8900, "lon": 31.1300,
     "country": "Zimbabwe", "year": "1994",
     "notes": "62 schoolchildren at Ariel School reported seeing a craft and beings. Independently investigated by Harvard's John Mack."},
    {"name": "Maury Island Incident", "lat": 47.3748, "lon": -122.4327,
     "country": "United States", "year": "1947",
     "notes": "Alleged UFO debris incident near Tacoma, Washington in June 1947, three days before the Roswell crash."},
    {"name": "Broad Haven Triangle (Wales)", "lat": 51.7700, "lon": -5.0700,
     "country": "United Kingdom", "year": "1977",
     "notes": "Series of UFO sightings in Pembrokeshire, Wales in 1977. Schoolchildren independently drew identical silver craft."},
    {"name": "Lubbock Lights", "lat": 33.5779, "lon": -101.8552,
     "country": "United States", "year": "1951",
     "notes": "V-shaped formation of lights observed by professors at Texas Tech University on multiple nights in August-September 1951."},
    {"name": "Washington D.C. UFO Incident", "lat": 38.8951, "lon": -77.0364,
     "country": "United States", "year": "1952",
     "notes": "UFOs tracked on radar over the US capital on consecutive weekends in July 1952. Fighter jets scrambled. National media sensation."},
]

# ---------------------------------------------------------------
# 7. SECRET SOCIETY HEADQUARTERS (18 locations)
# ---------------------------------------------------------------
SECRET_SOCIETY_HEADQUARTERS = [
    {"name": "United Grand Lodge of England", "lat": 51.5155, "lon": -0.1318,
     "country": "United Kingdom", "year": "1717",
     "notes": "Oldest Masonic Grand Lodge in the world. Freemasons Hall on Great Queen Street, London. Impressive Art Deco interior."},
    {"name": "Grand Orient de France", "lat": 48.8716, "lon": 2.3388,
     "country": "France", "year": "1773",
     "notes": "Major continental Masonic body on Rue Cadet, Paris. Founded during the Enlightenment era. Instrumental in French Revolution politics."},
    {"name": "House of the Temple (Scottish Rite)", "lat": 38.9076, "lon": -77.0300,
     "country": "United States", "year": "1915",
     "notes": "Headquarters of the Scottish Rite of Freemasonry (Southern Jurisdiction) in Washington DC. Modeled on the Mausoleum at Halicarnassus."},
    {"name": "Skull and Bones Tomb (Yale)", "lat": 41.3083, "lon": -72.9279,
     "country": "United States", "year": "1856",
     "notes": "Windowless sandstone hall on the Yale University campus, New Haven, CT. The Order was established in 1832 by William Huntington Russell."},
    {"name": "Bohemian Grove", "lat": 38.4690, "lon": -122.9715,
     "country": "United States", "year": "1878",
     "notes": "2,700-acre private redwood retreat in Monte Rio, California. Annual summer encampment of the Bohemian Club hosts world leaders."},
    {"name": "Bilderberg Hotel de Bilderberg", "lat": 52.0808, "lon": 5.8219,
     "country": "Netherlands", "year": "1954",
     "notes": "Hotel in Oosterbeek where the first Bilderberg Conference was held in May 1954. Annual invite-only meetings of global elites."},
    {"name": "Chatham House (RIIA)", "lat": 51.5074, "lon": -0.1382,
     "country": "United Kingdom", "year": "1920",
     "notes": "Royal Institute of International Affairs at St James's Square, London. Origin of the famous Chatham House Rule of confidentiality."},
    {"name": "Rosslyn Chapel", "lat": 55.8554, "lon": -3.1602,
     "country": "United Kingdom", "year": "1446",
     "notes": "Medieval chapel in Midlothian, Scotland. Extensively linked to Templar and Masonic legends. Featured in The Da Vinci Code."},
    {"name": "Palazzo Giustiniani", "lat": 41.8986, "lon": 12.4753,
     "country": "Italy", "year": "1805",
     "notes": "Historic seat of the Grand Orient of Italy in Rome. Now incorporated into the Italian Senate complex."},
    {"name": "Knights Templar Church (Temple Church)", "lat": 51.5133, "lon": -0.1105,
     "country": "United Kingdom", "year": "1185",
     "notes": "Built by the Knights Templar in London. Consecrated by Heraclius, Patriarch of Jerusalem. Circular nave after the Church of the Holy Sepulchre."},
    {"name": "Grand Lodge of Scotland", "lat": 55.9513, "lon": -3.1883,
     "country": "United Kingdom", "year": "1736",
     "notes": "Edinburgh headquarters on George Street. Oversees Scottish Freemasonry, one of the oldest Masonic jurisdictions in the world."},
    {"name": "Rosicrucian Park (AMORC)", "lat": 37.3352, "lon": -121.9127,
     "country": "United States", "year": "1927",
     "notes": "Ancient Mystical Order Rosae Crucis headquarters and Egyptian Museum campus in San Jose, California."},
    {"name": "Rennes-le-Chateau", "lat": 42.9256, "lon": 2.2617,
     "country": "France", "year": "1891",
     "notes": "Hilltop village in Languedoc. Centre of Priory of Sion legends, hidden treasure myths, and Holy Grail conspiracy theories."},
    {"name": "Villa of the Mysteries (Pompeii)", "lat": 40.7509, "lon": 14.4788,
     "country": "Italy", "year": "~60 BCE",
     "notes": "Pompeii villa with remarkably preserved frescoes depicting ancient mystery cult initiation rites."},
    {"name": "Freemasons Hall Dublin", "lat": 53.3380, "lon": -6.2630,
     "country": "Ireland", "year": "1869",
     "notes": "Grand Lodge of Ireland on Molesworth Street. One of the oldest Masonic jurisdictions in the world, founded in 1725."},
    {"name": "Council on Foreign Relations (NYC)", "lat": 40.7686, "lon": -73.9679,
     "country": "United States", "year": "1921",
     "notes": "Harold Pratt House on Park Avenue, New York City. One of the most influential foreign policy think tanks in the world."},
    {"name": "Trilateral Commission Office", "lat": 40.7614, "lon": -73.9776,
     "country": "United States", "year": "1973",
     "notes": "Founded by David Rockefeller and Zbigniew Brzezinski. Promotes cooperation between North America, Europe, and Japan."},
    {"name": "Odd Fellows Temple (Philadelphia)", "lat": 39.9535, "lon": -75.1629,
     "country": "United States", "year": "1847",
     "notes": "Historic headquarters of the Independent Order of Odd Fellows. One of the largest fraternal organizations in the 19th century."},
]

# ---------------------------------------------------------------
# 8. LEY LINES & ENERGY POINTS (18 locations)
# ---------------------------------------------------------------
LEY_LINES_ENERGY_POINTS = [
    {"name": "Stonehenge (St Michael Ley Line)", "lat": 51.1789, "lon": -1.8262,
     "country": "United Kingdom", "year": "~3000 BCE",
     "notes": "Major node on the St Michael ley line stretching from St Michael's Mount in Cornwall to Hopton-on-Sea in Norfolk."},
    {"name": "Avebury Henge", "lat": 51.4288, "lon": -1.8544,
     "country": "United Kingdom", "year": "~2850 BCE",
     "notes": "Largest stone circle in Europe encompassing an entire village. Key intersection point on multiple proposed ley line alignments."},
    {"name": "Glastonbury Tor", "lat": 51.1442, "lon": -2.6987,
     "country": "United Kingdom", "year": "Ancient",
     "notes": "Sacred terraced hill in Somerset on the St Michael ley line. Associated with Arthurian legend, the Holy Grail, and mystical energy."},
    {"name": "St Michael's Mount", "lat": 50.1178, "lon": -5.4776,
     "country": "United Kingdom", "year": "495 CE",
     "notes": "Tidal island in Mount's Bay, Cornwall. Western terminus of the St Michael ley line and the Apollo-St Michael alignment across Europe."},
    {"name": "Bury St Edmunds Abbey", "lat": 52.2429, "lon": 0.7143,
     "country": "United Kingdom", "year": "1020",
     "notes": "Medieval Benedictine abbey ruins in Suffolk positioned on the St Michael ley line. Eastern anchor point of the alignment."},
    {"name": "Great Pyramid Ley Intersection", "lat": 29.9792, "lon": 31.1342,
     "country": "Egypt", "year": "~2560 BCE",
     "notes": "Proposed intersection of multiple global ley lines. The pyramid sits precisely on the longest continuous land meridian on Earth."},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450,
     "country": "Peru", "year": "~1450 CE",
     "notes": "Inca citadel proposed as a major energy node on South American ley line networks connecting sacred sites along the Andes."},
    {"name": "Sedona Vortex Sites", "lat": 34.8697, "lon": -111.7610,
     "country": "United States", "year": "1980s",
     "notes": "Arizona desert town famous for alleged energy vortexes at Cathedral Rock, Bell Rock, Airport Mesa, and Boynton Canyon."},
    {"name": "Mount Shasta", "lat": 41.3099, "lon": -122.3106,
     "country": "United States", "year": "Ancient",
     "notes": "Dormant volcano in Northern California. New Age beliefs associate it with spiritual energy, Lemurian survivors, and underground cities."},
    {"name": "Externsteine", "lat": 51.8688, "lon": 8.9167,
     "country": "Germany", "year": "Ancient",
     "notes": "Sandstone rock formation in the Teutoburg Forest. Believed by ley line researchers to be an ancient sacred site and energy node."},
    {"name": "Carnac Alignments", "lat": 47.5950, "lon": -3.0717,
     "country": "France", "year": "~4500 BCE",
     "notes": "Over 3,000 menhirs arranged in precise rows in Brittany. Proposed by ley line theorists as a major megalithic alignment structure."},
    {"name": "Angkor Wat", "lat": 13.4125, "lon": 103.8670,
     "country": "Cambodia", "year": "~1150 CE",
     "notes": "Largest religious monument in the world. Proposed as a node on a global temple alignment network spanning multiple continents."},
    {"name": "Easter Island Ley Node", "lat": -27.1127, "lon": -109.3497,
     "country": "Chile", "year": "~1250 CE",
     "notes": "Remote Pacific island proposed as a global ley line node connecting ancient sites across the Pacific Ocean."},
    {"name": "Uluru (Ayers Rock)", "lat": -25.3444, "lon": 131.0369,
     "country": "Australia", "year": "Ancient",
     "notes": "Sacred Aboriginal monolith. Proposed as a major energy centre on both Australian songlines and global ley line maps."},
    {"name": "Chartres Cathedral", "lat": 48.4478, "lon": 1.4877,
     "country": "France", "year": "1194",
     "notes": "Gothic cathedral built on an ancient Druidic sacred site. Contains the famous labyrinth walked by pilgrims for spiritual transformation."},
    {"name": "Newgrange Passage Tomb", "lat": 53.6947, "lon": -6.4755,
     "country": "Ireland", "year": "~3200 BCE",
     "notes": "Prehistoric passage tomb older than Stonehenge or the pyramids. Winter solstice sunrise illuminates the inner chamber precisely."},
    {"name": "Delphi (Apollo Temple)", "lat": 38.4824, "lon": 22.5010,
     "country": "Greece", "year": "~800 BCE",
     "notes": "Ancient Greeks considered Delphi the navel (omphalos) of the world. On the Apollo-St Michael alignment stretching across Europe."},
    {"name": "Monte Sant'Angelo (Gargano)", "lat": 41.7067, "lon": 15.9556,
     "country": "Italy", "year": "490 CE",
     "notes": "Shrine of the Archangel Michael on the Gargano peninsula. Key point on the St Michael ley line running from Ireland to Israel."},
]

# ---------------------------------------------------------------
# 9. LOST CIVILIZATION SITES (17 locations)
# ---------------------------------------------------------------
LOST_CIVILIZATION_SITES = [
    {"name": "Santorini (Atlantis Candidate)", "lat": 36.3932, "lon": 25.4615,
     "country": "Greece", "year": "~1600 BCE",
     "notes": "Minoan eruption destroyed Thera. Leading archaeological candidate for the inspiration behind Plato's Atlantis allegory."},
    {"name": "Bimini Road", "lat": 25.7667, "lon": -79.2833,
     "country": "Bahamas", "year": "1968",
     "notes": "Underwater limestone formation discovered in 1968. Edgar Cayce had predicted Atlantis would be found near Bimini in 1938."},
    {"name": "Richat Structure (Eye of the Sahara)", "lat": 21.1244, "lon": -11.4015,
     "country": "Mauritania", "year": "Ancient",
     "notes": "50 km concentric geological formation in the Sahara matching some descriptions of Atlantis. Clearly visible from space."},
    {"name": "Doggerland (North Sea)", "lat": 55.0000, "lon": 2.5000,
     "country": "North Sea", "year": "~6000 BCE",
     "notes": "Submerged landmass that once connected Britain to continental Europe. Rich Mesolithic settlements drowned by post-glacial sea level rise."},
    {"name": "Sundaland (Southeast Asia)", "lat": 2.0000, "lon": 110.0000,
     "country": "Southeast Asia", "year": "~12000 BCE",
     "notes": "Vast submerged continental shelf connecting mainland Asia to Indonesia and Borneo. Drowned by post-Ice Age sea level rise."},
    {"name": "Yonaguni Monument (Mu Candidate)", "lat": 24.4353, "lon": 123.0101,
     "country": "Japan", "year": "~8000 BCE?",
     "notes": "Underwater formation cited by some researchers as evidence of the lost continent of Mu or Lemuria in the Pacific Ocean."},
    {"name": "Gulf of Cambay (Dwarka)", "lat": 22.2500, "lon": 69.0000,
     "country": "India", "year": "~7500 BCE?",
     "notes": "Side-scan sonar images reveal possible submerged city structures. Linked to the legendary city of Dwarka from Hindu scriptures."},
    {"name": "Nan Madol (Lemuria Link)", "lat": 6.8438, "lon": 158.3350,
     "country": "Micronesia", "year": "~1180 CE",
     "notes": "Ruined megalithic city on artificial islets in the Pacific. Some theorists link its mysterious origins to the lost continent of Lemuria."},
    {"name": "Gobekli Tepe (Pre-Flood Theory)", "lat": 37.2232, "lon": 38.9224,
     "country": "Turkey", "year": "~9500 BCE",
     "notes": "Some researchers propose this as evidence that an advanced pre-flood civilization existed before the Younger Dryas catastrophe."},
    {"name": "Guanahacabibes (Cuba Underwater City)", "lat": 21.8000, "lon": -84.5000,
     "country": "Cuba", "year": "2001",
     "notes": "Sonar readings off western Cuba showed geometric structures at 600-700 metres depth. Pauline Zalitzki's controversial 2001 discovery."},
    {"name": "Pavlopetri", "lat": 36.5189, "lon": 23.0472,
     "country": "Greece", "year": "~3000 BCE",
     "notes": "Oldest known submerged city in the world. A Bronze Age settlement off southern Laconia with visible streets and building foundations."},
    {"name": "Heracleion (Thonis)", "lat": 31.3000, "lon": 30.1000,
     "country": "Egypt", "year": "~800 BCE",
     "notes": "Ancient Egyptian port city rediscovered underwater in Abu Qir Bay by Franck Goddio in 2000. Sank after earthquakes and floods."},
    {"name": "Zealandia Continental Fragment", "lat": -42.0000, "lon": 172.0000,
     "country": "New Zealand", "year": "~85 Ma",
     "notes": "Nearly submerged continent in the southwestern Pacific. 94 percent underwater. Formally recognized as a continent in 2017."},
    {"name": "Tiahuanaco (Viracocha Legend)", "lat": -16.5546, "lon": -68.6733,
     "country": "Bolivia", "year": "~400 CE",
     "notes": "Ancient city near Lake Titicaca at 3,800 m altitude. Legend says the creator god Viracocha emerged from the lake to bring civilization."},
    {"name": "Piri Reis Map (Antarctic Connection)", "lat": -75.0000, "lon": 0.0000,
     "country": "Antarctica", "year": "1513",
     "notes": "The 1513 Ottoman map allegedly shows the ice-free Antarctic coastline, suggesting knowledge from a pre-ice-age mapping civilization."},
    {"name": "Dwarka Underwater Ruins", "lat": 22.2394, "lon": 68.9678,
     "country": "India", "year": "~1500 BCE",
     "notes": "Submerged structures discovered off the coast of modern Dwarka, Gujarat. Linked to the legendary city of Lord Krishna."},
    {"name": "Saharan Eye (Atlantis Theory)", "lat": 21.1244, "lon": -11.4015,
     "country": "Mauritania", "year": "Ancient",
     "notes": "The Richat Structure's concentric rings match Plato's description of Atlantis: alternating rings of water and land surrounding a central island."},
]

# ---------------------------------------------------------------
# 10. GOVERNMENT RESEARCH FACILITIES (22 locations)
# ---------------------------------------------------------------
GOVERNMENT_RESEARCH_FACILITIES = [
    {"name": "CERN (Large Hadron Collider)", "lat": 46.2044, "lon": 6.1432,
     "country": "Switzerland/France", "year": "1954",
     "notes": "European Organization for Nuclear Research. Houses the 27 km circumference Large Hadron Collider beneath the Franco-Swiss border."},
    {"name": "Los Alamos National Laboratory", "lat": 35.8819, "lon": -106.2989,
     "country": "United States", "year": "1943",
     "notes": "Birthplace of the atomic bomb under the Manhattan Project. Remains a premier nuclear weapons and national security research facility."},
    {"name": "Sandia National Laboratories", "lat": 35.0585, "lon": -106.5341,
     "country": "United States", "year": "1949",
     "notes": "Major nuclear weapons engineering and systems integration facility in Albuquerque, New Mexico."},
    {"name": "Porton Down (DSTL)", "lat": 51.1322, "lon": -1.7073,
     "country": "United Kingdom", "year": "1916",
     "notes": "Defence Science and Technology Laboratory. Chemical and biological weapons research since World War I. Controversial history of human testing."},
    {"name": "Biopreparat - Vozrozhdeniya Island", "lat": 44.9833, "lon": 59.2000,
     "country": "Uzbekistan/Kazakhstan", "year": "1954",
     "notes": "Former Soviet biological weapons open-air testing site on an island in the Aral Sea. Anthrax and smallpox spores buried here."},
    {"name": "Dugway Proving Ground", "lat": 40.1789, "lon": -112.9452,
     "country": "United States", "year": "1942",
     "notes": "US Army chemical and biological defense testing facility in the Utah desert. Multiple accidental releases have been documented."},
    {"name": "Plum Island Animal Disease Center", "lat": 41.1814, "lon": -72.1659,
     "country": "United States", "year": "1954",
     "notes": "USDA facility studying foreign animal diseases off Long Island, New York. Subject of Lyme disease origin conspiracy theories."},
    {"name": "Oak Ridge National Laboratory", "lat": 35.9313, "lon": -84.3107,
     "country": "United States", "year": "1943",
     "notes": "Manhattan Project site for uranium enrichment during WWII. Now the DOE's largest science and energy national laboratory."},
    {"name": "Lawrence Livermore National Lab", "lat": 37.6872, "lon": -121.7054,
     "country": "United States", "year": "1952",
     "notes": "Nuclear weapons design and national security research facility in Livermore, California. Houses the National Ignition Facility."},
    {"name": "Wuhan Institute of Virology", "lat": 30.5706, "lon": 114.3563,
     "country": "China", "year": "1956",
     "notes": "BSL-4 maximum containment virology laboratory. At the centre of worldwide debates about the origins of the COVID-19 pandemic."},
    {"name": "DARPA (Pentagon)", "lat": 38.8719, "lon": -77.0563,
     "country": "United States", "year": "1958",
     "notes": "Defense Advanced Research Projects Agency. Created ARPANET (the internet), GPS, stealth technology, and voice recognition."},
    {"name": "Ames Research Center (NASA)", "lat": 37.4100, "lon": -122.0644,
     "country": "United States", "year": "1939",
     "notes": "NASA facility in Silicon Valley. Research in astrobiology, autonomous systems, supercomputing, and air traffic management."},
    {"name": "Skunk Works (Lockheed Martin)", "lat": 34.6137, "lon": -118.0856,
     "country": "United States", "year": "1943",
     "notes": "Advanced Development Programs division in Palmdale, California. Developed U-2, SR-71 Blackbird, F-117, and classified aircraft."},
    {"name": "Novichok Development Site (Shikhany)", "lat": 52.1167, "lon": 47.2000,
     "country": "Russia", "year": "1970s",
     "notes": "State Research Institute of Organic Chemistry and Technology. Novichok-class nerve agents were developed and tested at this facility."},
    {"name": "Unit 731 Memorial Site (Harbin)", "lat": 45.6167, "lon": 126.6333,
     "country": "China", "year": "1937",
     "notes": "Former Imperial Japanese Army biological warfare research facility in Manchuria. Site of horrific wartime human experimentation."},
    {"name": "Montauk Air Force Station (Camp Hero)", "lat": 41.0716, "lon": -71.8599,
     "country": "United States", "year": "1942",
     "notes": "Decommissioned USAF radar station on Long Island. Centre of the Montauk Project conspiracy theories about time travel experiments."},
    {"name": "Pine Bluff Arsenal", "lat": 34.2585, "lon": -92.0071,
     "country": "United States", "year": "1941",
     "notes": "US Army chemical and biological weapons production and storage facility in Arkansas. Active in the US offensive BW program."},
    {"name": "Suffield Research Station (DRDC)", "lat": 50.2833, "lon": -111.1833,
     "country": "Canada", "year": "1941",
     "notes": "Defence Research Establishment Suffield in Alberta. Chemical and biological defense testing range on the Canadian prairies."},
    {"name": "Sverdlovsk-19 (Yekaterinburg)", "lat": 56.8431, "lon": 60.6454,
     "country": "Russia", "year": "1946",
     "notes": "Site of the 1979 anthrax leak that killed at least 66 people. Key facility in the Soviet biological weapons programme."},
    {"name": "Rocky Mountain Arsenal", "lat": 39.8083, "lon": -104.8583,
     "country": "United States", "year": "1942",
     "notes": "Former US chemical weapons manufacturing facility near Denver. Contaminated 27 sq miles of land. Now a National Wildlife Refuge."},
    {"name": "Brookhaven National Laboratory", "lat": 40.8681, "lon": -72.8789,
     "country": "United States", "year": "1947",
     "notes": "DOE research facility on Long Island. Houses the Relativistic Heavy Ion Collider. Subject of black hole creation conspiracy theories."},
    {"name": "Detrick (Fort Detrick)", "lat": 39.4353, "lon": -77.4389,
     "country": "United States", "year": "1943",
     "notes": "US Army biological weapons research centre in Maryland. Now home to USAMRIID and multiple biodefense programs."},
]


# ===================================================================
# MODE CONFIGURATION MAP
# ===================================================================

MODE_CONFIG = {
    "Secret Military Bases": {
        "data": SECRET_MILITARY_BASES,
        "color": "#ef4444",
        "fill_color": "#dc2626",
        "desc": "Classified or restricted military installations, test ranges, and covert facilities acknowledged or rumored worldwide.",
    },
    "Bermuda Triangle & Anomaly Zones": {
        "data": BERMUDA_TRIANGLE_ANOMALY_ZONES,
        "color": "#06b6d4",
        "fill_color": "#0891b2",
        "desc": "Geographical zones associated with reported anomalous disappearances, electromagnetic anomalies, and unexplained events.",
    },
    "Ancient Alien Theory Sites": {
        "data": ANCIENT_ALIEN_THEORY_SITES,
        "color": "#f59e0b",
        "fill_color": "#d97706",
        "desc": "Ancient structures and artifacts whose construction has been attributed to extraterrestrial influence in popular culture.",
    },
    "Underground Bunkers & Tunnels": {
        "data": UNDERGROUND_BUNKERS_TUNNELS,
        "color": "#64748b",
        "fill_color": "#475569",
        "desc": "Cold War bunkers, continuity-of-government shelters, secret tunnel networks, and subterranean military complexes.",
    },
    "Crop Circle Hotspots": {
        "data": CROP_CIRCLE_HOTSPOTS,
        "color": "#22c55e",
        "fill_color": "#16a34a",
        "desc": "Locations where elaborate crop formations have been documented, centered on Wiltshire, England and select global sites.",
    },
    "Famous UFO Sighting Locations": {
        "data": FAMOUS_UFO_SIGHTINGS,
        "color": "#a855f7",
        "fill_color": "#9333ea",
        "desc": "Documented locations of significant UFO/UAP sightings that generated government investigations or mass public interest.",
    },
    "Secret Society Headquarters": {
        "data": SECRET_SOCIETY_HEADQUARTERS,
        "color": "#8b5cf6",
        "fill_color": "#7c3aed",
        "desc": "Historically documented meeting halls, lodges, and headquarters of fraternal orders and influential private organizations.",
    },
    "Ley Lines & Energy Points": {
        "data": LEY_LINES_ENERGY_POINTS,
        "color": "#ec4899",
        "fill_color": "#db2777",
        "desc": "Sacred sites and ancient monuments proposed to align along ley lines or serve as spiritual energy nodes in New Age geography.",
    },
    "Lost Civilization Sites": {
        "data": LOST_CIVILIZATION_SITES,
        "color": "#f97316",
        "fill_color": "#ea580c",
        "desc": "Submerged cities, geological formations, and sites linked to legends of Atlantis, Lemuria, Mu, and other lost civilizations.",
    },
    "Government Research Facilities": {
        "data": GOVERNMENT_RESEARCH_FACILITIES,
        "color": "#10b981",
        "fill_color": "#059669",
        "desc": "Advanced government laboratories and research installations associated with weapons development and controversial experiments.",
    },
}


# ===================================================================
# CACHED DATA FETCH FUNCTIONS
# ===================================================================


@st.cache_data(ttl=3600)
def _fetch_mode_data(mode_name):
    """Fetch curated location data for a given mode. Cached for 1 hour."""
    config = MODE_CONFIG.get(mode_name, {})
    data = config.get("data", [])
    enriched = []
    for entry in data:
        loc = dict(entry)
        loc["mode"] = mode_name
        loc["color"] = config.get("color", "#8b97b0")
        loc["fill_color"] = config.get("fill_color", "#6b7280")
        enriched.append(loc)
    return enriched


@st.cache_data(ttl=3600)
def _fetch_all_mode_data():
    """Fetch all location data across all 10 modes. Cached for 1 hour."""
    all_locs = []
    for mode_name in MODE_CONFIG:
        all_locs.extend(_fetch_mode_data(mode_name))
    return all_locs


@st.cache_data(ttl=3600)
def _build_dataframe(locations):
    """Build a pandas DataFrame from a list of location dicts. Cached."""
    rows = []
    for loc in locations:
        rows.append({
            "Name": loc.get("name", ""),
            "Category": loc.get("mode", ""),
            "Country": loc.get("country", ""),
            "Year": loc.get("year", ""),
            "Latitude": loc.get("lat", 0.0),
            "Longitude": loc.get("lon", 0.0),
            "Notes": loc.get("notes", ""),
        })
    return pd.DataFrame(rows)


@st.cache_data(ttl=3600)
def _compute_country_stats(locations):
    """Compute country frequency counts for a location list. Cached."""
    country_counts = {}
    for loc in locations:
        c = loc.get("country", "Unknown")
        country_counts[c] = country_counts.get(c, 0) + 1
    return dict(sorted(country_counts.items(), key=lambda x: -x[1]))


# ===================================================================
# POPUP BUILDER (with html_module.escape for all user content)
# ===================================================================


def _build_popup(loc):
    """Build sanitized popup HTML for a folium CircleMarker."""
    name = html_module.escape(str(loc.get("name", "Unknown")))
    mode = html_module.escape(str(loc.get("mode", "")))
    country = html_module.escape(str(loc.get("country", "")))
    year = html_module.escape(str(loc.get("year", "")))
    notes = html_module.escape(str(loc.get("notes", ""))[:220])
    color = html_module.escape(str(loc.get("color", "#8b97b0")))

    return (
        f'<div style="max-width:280px; font-family:Segoe UI,sans-serif; '
        f'background:#1a1a2e; padding:10px 12px; border-radius:8px; '
        f'border:1px solid {color}40;">'
        f'<div style="font-size:0.95rem; font-weight:700; color:{color}; '
        f'margin-bottom:4px;">{name}</div>'
        f'<div style="font-size:0.72rem; color:#6b7280; '
        f'margin-bottom:6px; text-transform:uppercase; letter-spacing:0.5px;">{mode}</div>'
        f'<div style="font-size:0.82rem; color:#e5e7eb;">'
        f'{country} &middot; {year}</div>'
        f'<div style="font-size:0.75rem; color:#9ca3af; margin-top:6px; '
        f'line-height:1.4;">{notes}</div>'
        f'</div>'
    )


# ===================================================================
# FOLIUM MAP BUILDER
# ===================================================================


def _build_map(locations, zoom=2):
    """Build a dark-themed folium map with CircleMarkers for all locations."""
    if not locations:
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        return m

    avg_lat = sum(loc["lat"] for loc in locations) / len(locations)
    avg_lon = sum(loc["lon"] for loc in locations) / len(locations)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    for loc in locations:
        color = loc.get("color", "#8b97b0")
        fill_color = loc.get("fill_color", color)
        popup_html = _build_popup(loc)
        tooltip_text = html_module.escape(str(loc.get("name", "")))

        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=tooltip_text,
        ).add_to(m)

    return m


# ===================================================================
# INDIVIDUAL MODE RENDERER
# ===================================================================


def _render_mode(mode_name):
    """Render a complete section for one of the 10 map modes."""
    config = MODE_CONFIG.get(mode_name, {})
    locations = _fetch_mode_data(mode_name)

    if not locations:
        st.warning(f"No data available for {html_module.escape(mode_name)}.")
        return

    # -- Mode Description --
    desc = html_module.escape(config.get("desc", ""))
    color = html_module.escape(config.get("color", "#8b97b0"))
    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem; margin-bottom:1rem;">'
        f'{desc}</p>',
        unsafe_allow_html=True,
    )

    # -- Stats Row using st.metric --
    countries = sorted(set(loc.get("country", "") for loc in locations))
    years_numeric = []
    for loc in locations:
        yr_str = loc.get("year", "").lstrip("~").replace("?", "").strip()
        # Handle negative years (BCE) and "s" suffix (e.g., "1950s")
        yr_clean = yr_str.rstrip("s")
        if yr_clean.lstrip("-").isdigit():
            years_numeric.append(int(yr_clean))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Locations", len(locations))
    c2.metric("Countries / Regions", len(countries))
    if years_numeric:
        earliest = min(years_numeric)
        latest = max(years_numeric)
        c3.metric("Earliest Record", f"{earliest} {'BCE' if earliest < 0 else ''}")
        c4.metric("Latest Record", str(latest))
    else:
        c3.metric("Data Points", len(locations))
        c4.metric("Fields per Entry", 6)

    # -- Country Breakdown Metrics --
    country_counts = _compute_country_stats(locations)
    top_countries = list(country_counts.items())[:6]
    if top_countries:
        cols = st.columns(min(len(top_countries), 6))
        for i, (country, count) in enumerate(top_countries):
            cols[i].metric(country[:22], count)

    st.markdown("---")

    # -- Folium Map --
    mode_esc = html_module.escape(mode_name)
    st.markdown(
        f'<h4 style="color:#e8ecf4;">{mode_esc} Map</h4>',
        unsafe_allow_html=True,
    )

    # Color Legend
    st.markdown(
        f'<div style="margin-bottom:8px;">'
        f'<span style="color:{color}; font-size:0.85rem; font-weight:600;">'
        f'&#9679; {mode_esc}</span>'
        f' <span style="color:#5a6580; font-size:0.75rem;">'
        f'({len(locations)} locations)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    m = _build_map(locations, zoom=2)
    st_html(m._repr_html_(), height=500)

    st.markdown("---")

    # -- Notable Locations List --
    st.markdown(
        '<h4 style="color:#e8ecf4;">Notable Locations</h4>',
        unsafe_allow_html=True,
    )

    col_left, col_right = st.columns(2)
    half = len(locations) // 2

    for col, locs_slice in [(col_left, locations[:half]), (col_right, locations[half:])]:
        with col:
            for loc in locs_slice:
                name_esc = html_module.escape(str(loc.get("name", "")))
                country_esc = html_module.escape(str(loc.get("country", "")))
                year_esc = html_module.escape(str(loc.get("year", "")))
                notes_esc = html_module.escape(str(loc.get("notes", ""))[:120])
                loc_color = html_module.escape(str(loc.get("color", "#8b97b0")))

                st.markdown(
                    f'<div style="display:flex; align-items:flex-start; '
                    f'margin-bottom:0.6rem; padding:0.35rem 0;">'
                    f'<div style="width:5px; min-height:44px; border-radius:3px; '
                    f'background:{loc_color}; margin-right:0.65rem; flex-shrink:0;">'
                    f'</div>'
                    f'<div style="flex:1;">'
                    f'<div style="color:#e8ecf4; font-weight:600; font-size:0.82rem;">'
                    f'{name_esc}</div>'
                    f'<div style="color:#8b97b0; font-size:0.72rem;">'
                    f'{country_esc} &middot; {year_esc}</div>'
                    f'<div style="color:#5a6580; font-size:0.68rem; line-height:1.35;">'
                    f'{notes_esc}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # -- Data Table --
    df = _build_dataframe(locations)
    st.markdown(
        f'<h4 style="color:#e8ecf4;">Data Table ({len(df)} locations)</h4>',
        unsafe_allow_html=True,
    )

    # Country filter within mode
    all_countries_in_mode = sorted(df["Country"].unique().tolist())
    selected_countries = st.multiselect(
        "Filter by Country",
        options=all_countries_in_mode,
        default=all_countries_in_mode,
        key=f"filter_{mode_name.replace(' ', '_')}",
    )

    filtered_df = df[df["Country"].isin(selected_countries)]
    st.dataframe(filtered_df, width="stretch", hide_index=True)

    # -- CSV Download --
    csv_buf = io.StringIO()
    filtered_df.to_csv(csv_buf, index=False)
    safe_name = mode_name.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        label=f"Download {len(filtered_df)} {mode_name} Locations as CSV",
        data=csv_buf.getvalue(),
        file_name=f"conspiracy_{safe_name}.csv",
        mime="text/csv",
        key=f"dl_{safe_name}",
    )


# ===================================================================
# MAIN RENDER FUNCTION
# ===================================================================


def render_conspiracy_maps_tab():
    """Main render function for the Mystery & Conspiracy Maps tab."""

    # ---- Tab Header ----
    st.markdown(
        '<div class="tab-header red">'
        '<h4>\U0001f53a Mystery & Conspiracy Maps</h4>'
        '<p>Unexplained phenomena, secret bases, and mysterious locations</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Educational / Entertainment Disclaimer ----
    st.markdown(
        '<div style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25); '
        'border-radius:8px; padding:0.75rem 1rem; margin-bottom:1rem;">'
        '<span style="color:#ef4444; font-weight:600;">Educational / Entertainment Content:</span> '
        '<span style="color:#8b97b0; font-size:0.85rem;">'
        'This module explores locations associated with popular culture, folklore, and conspiracy theories. '
        'Inclusion does not imply endorsement of any conspiracy theory. '
        'Many listed claims have been debunked by mainstream scholarship. '
        'Always consult peer-reviewed sources for factual information.</span></div>',
        unsafe_allow_html=True,
    )

    # ---- Map Mode Selector (10 modes) ----
    mode_options = list(MODE_CONFIG.keys())

    selected_mode = st.selectbox(
        "Map Mode",
        mode_options,
        index=0,
        key="conspiracy_map_mode",
        help="Choose from 10 categories of mysterious and historically significant locations to explore.",
    )

    # ---- Category Quick-Access Badges (2 rows of 5) ----
    badge_cols = st.columns(5)
    for i, (mode_name, config) in enumerate(MODE_CONFIG.items()):
        col_idx = i % 5
        count = len(config.get("data", []))
        badge_color = html_module.escape(config.get("color", "#8b97b0"))
        mode_esc = html_module.escape(mode_name[:28])
        badge_cols[col_idx].markdown(
            f'<div style="background:rgba(26,34,53,0.8); '
            f'border:1px solid {badge_color}55; '
            f'border-radius:6px; padding:0.3rem 0.5rem; text-align:center; '
            f'margin-bottom:0.4rem;">'
            f'<span style="color:{badge_color}; font-size:0.72rem; font-weight:600;">'
            f'{mode_esc}</span><br/>'
            f'<span style="color:#5a6580; font-size:0.65rem;">{count} sites</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ---- Render the Selected Mode ----
    _render_mode(selected_mode)

    # ---- Global Database Summary Footer ----
    st.markdown("---")
    st.markdown(
        '<h4 style="color:#e8ecf4;">Global Database Summary</h4>',
        unsafe_allow_html=True,
    )

    all_locs = _fetch_all_mode_data()
    total_locations = len(all_locs)
    total_modes = len(MODE_CONFIG)
    total_countries = len(set(loc.get("country", "") for loc in all_locs))

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Total Locations (All Modes)", total_locations)
    g2.metric("Map Modes Available", total_modes)
    g3.metric("Countries / Regions", total_countries)
    g4.metric("Data Fields per Entry", 7)

    # ---- Mode Distribution Summary ----
    st.markdown(
        '<div style="margin-top:0.75rem; margin-bottom:0.75rem;">',
        unsafe_allow_html=True,
    )
    mode_summary_cols = st.columns(5)
    for i, (mode_name, config) in enumerate(MODE_CONFIG.items()):
        col_idx = i % 5
        mode_count = len(config.get("data", []))
        mc = html_module.escape(config.get("color", "#8b97b0"))
        mn = html_module.escape(mode_name[:25])
        mode_summary_cols[col_idx].markdown(
            f'<div style="text-align:center; margin-bottom:0.5rem;">'
            f'<span style="color:{mc}; font-size:1.1rem; font-weight:700;">'
            f'{mode_count}</span><br/>'
            f'<span style="color:#5a6580; font-size:0.65rem;">{mn}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Full Database CSV Download ----
    full_df = _build_dataframe(all_locs)
    csv_all = io.StringIO()
    full_df.to_csv(csv_all, index=False)
    st.download_button(
        label=f"Download Complete Database ({total_locations} Locations) as CSV",
        data=csv_all.getvalue(),
        file_name="conspiracy_maps_complete_database.csv",
        mime="text/csv",
        key="dl_conspiracy_all",
    )
