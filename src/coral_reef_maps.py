"""
Coral Reef Explorer module for TerraScout AI.
Provides 10 curated map modes covering the world's major coral reef systems,
bleaching events, restoration projects, deep-sea corals, and species hotspots.
All data is preset (no external API key required).
"""

import io
import streamlit as st
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import requests
import html as html_module
from streamlit.components.v1 import html as st_html


# ═══════════════════════════════════════════
# MARKER COLOR PALETTE
# ═══════════════════════════════════════════
REEF_COLORS = {
    "healthy": "#10b981",
    "moderate": "#f59e0b",
    "degraded": "#ef4444",
    "bleached": "#f0f0f0",
    "restored": "#06b6d4",
    "deep": "#8b5cf6",
    "dive_site": "#3b82f6",
    "research": "#ec4899",
    "hotspot": "#f97316",
    "default": "#8b97b0",
}


# ═══════════════════════════════════════════
# PRESET DATA — 10 MAP MODES
# ═══════════════════════════════════════════

DATA_GREAT_BARRIER_REEF = [
    {"name": "Cairns Section", "lat": -16.9186, "lon": 145.7781, "type": "dive_site",
     "desc": "Popular gateway to the northern GBR; Agincourt Reef and Michaelmas Cay."},
    {"name": "Whitsunday Islands", "lat": -20.2797, "lon": 148.9536, "type": "dive_site",
     "desc": "Heart Reef, Hardy Reef, and stunning fringing reefs around 74 islands."},
    {"name": "Ribbon Reefs", "lat": -15.5000, "lon": 145.7800, "type": "healthy",
     "desc": "Chain of 10 narrow ribbon reefs along the continental shelf edge; Cod Hole dive site."},
    {"name": "Lizard Island Research Station", "lat": -14.6682, "lon": 145.4637, "type": "research",
     "desc": "Australian Museum research station; long-term reef monitoring since 1973."},
    {"name": "Heron Island Research Station", "lat": -23.4423, "lon": 151.9130, "type": "research",
     "desc": "University of Queensland station on the southern GBR; turtle nesting site."},
    {"name": "Osprey Reef", "lat": -13.8833, "lon": 146.5500, "type": "dive_site",
     "desc": "Isolated coral sea reef; 1,000 m vertical walls, pelagic sharks, and pristine coral."},
    {"name": "Moore Reef", "lat": -16.8500, "lon": 146.2000, "type": "dive_site",
     "desc": "Outer reef platform off Cairns; giant clam garden and snorkel trails."},
    {"name": "Lady Elliot Island", "lat": -24.1128, "lon": 152.7147, "type": "healthy",
     "desc": "Southernmost GBR coral cay; manta ray aggregation site, green zone."},
    {"name": "Cape Tribulation Fringing Reefs", "lat": -16.1700, "lon": 145.4600, "type": "moderate",
     "desc": "Where the Daintree Rainforest meets the reef; sediment run-off concerns."},
    {"name": "Raine Island", "lat": -11.5947, "lon": 144.0353, "type": "research",
     "desc": "World's largest green turtle nesting site; recovery project underway."},
    {"name": "Pompey Complex", "lat": -20.8000, "lon": 150.5000, "type": "healthy",
     "desc": "Massive reef complex in the central GBR; labyrinths of channels and bommies."},
    {"name": "Townsville — Magnetic Island Reefs", "lat": -19.1500, "lon": 146.8300, "type": "moderate",
     "desc": "Fringing reefs around Magnetic Island; AIMS research headquarters nearby."},
]

DATA_CORAL_TRIANGLE = [
    {"name": "Raja Ampat, Indonesia", "lat": -0.5500, "lon": 130.5000, "type": "hotspot",
     "desc": "Highest marine biodiversity on Earth; 600+ coral species, 1,700+ reef fish species."},
    {"name": "Tubbataha Reefs, Philippines", "lat": 8.9167, "lon": 119.9167, "type": "healthy",
     "desc": "UNESCO World Heritage; pristine coral atoll in the Sulu Sea, 600+ fish species."},
    {"name": "Bunaken National Park, Indonesia", "lat": 1.6167, "lon": 124.7667, "type": "dive_site",
     "desc": "Dramatic wall diving in North Sulawesi; 70% of all Indo-Western Pacific fish species."},
    {"name": "Wakatobi, Indonesia", "lat": -5.3167, "lon": 123.7500, "type": "dive_site",
     "desc": "Tukang Besi islands; 750+ coral species across massive reef flats and walls."},
    {"name": "Apo Reef, Philippines", "lat": 12.6667, "lon": 120.4333, "type": "healthy",
     "desc": "Second-largest contiguous reef in the world; pristine atoll in the Mindoro Strait."},
    {"name": "Kimbe Bay, Papua New Guinea", "lat": -5.4000, "lon": 150.2000, "type": "hotspot",
     "desc": "Over 860 reef fish species; seamounts, walls, and lush coral gardens."},
    {"name": "Milne Bay, Papua New Guinea", "lat": -10.3333, "lon": 150.6667, "type": "dive_site",
     "desc": "Extreme biodiversity; muck diving, coral reefs, and WWII wrecks."},
    {"name": "Solomon Islands — Marovo Lagoon", "lat": -8.4500, "lon": 158.0000, "type": "healthy",
     "desc": "Largest saltwater lagoon in the world; intact reef systems and mangroves."},
    {"name": "Derawan Islands, Indonesia", "lat": 2.2833, "lon": 118.2500, "type": "dive_site",
     "desc": "Jellyfish Lake, manta rays, and turtle nesting on pristine coral islands."},
    {"name": "Verde Island Passage, Philippines", "lat": 13.5600, "lon": 121.0000, "type": "hotspot",
     "desc": "Center of the center of marine biodiversity; densest concentration of species per unit area."},
    {"name": "Cenderawasih Bay, Indonesia", "lat": -2.7500, "lon": 134.5000, "type": "dive_site",
     "desc": "Whale shark aggregation and unique reef ecosystems in West Papua."},
    {"name": "Banda Sea, Indonesia", "lat": -4.5000, "lon": 129.9000, "type": "healthy",
     "desc": "Deep-water coral reefs with strong currents; hammerhead schooling sites."},
]

DATA_RED_SEA = [
    {"name": "Ras Mohammed, Egypt", "lat": 27.7269, "lon": 34.2553, "type": "dive_site",
     "desc": "Egypt's premier dive site; Shark Reef and Yolanda Reef with pristine hard corals."},
    {"name": "Elphinstone Reef, Egypt", "lat": 25.2833, "lon": 34.8500, "type": "dive_site",
     "desc": "Offshore reef famous for oceanic whitetip sharks and sheer coral walls."},
    {"name": "Brothers Islands, Egypt", "lat": 26.3167, "lon": 34.8500, "type": "dive_site",
     "desc": "Remote offshore reefs; stunning walls, pelagic sharks, and soft coral gardens."},
    {"name": "Dahab Blue Hole, Egypt", "lat": 28.5722, "lon": 34.5389, "type": "dive_site",
     "desc": "Famous 130 m sinkhole with vibrant reef rim; shore-accessible diving."},
    {"name": "Aqaba Marine Park, Jordan", "lat": 29.4300, "lon": 34.9700, "type": "healthy",
     "desc": "Jordan's only coastline reef; Japanese Garden, Cedar Pride wreck."},
    {"name": "Farasan Islands, Saudi Arabia", "lat": 16.7000, "lon": 41.9800, "type": "healthy",
     "desc": "Pristine archipelago in southern Red Sea; extensive coral cover and dugong habitat."},
    {"name": "NEOM Coral Gardens, Saudi Arabia", "lat": 27.9500, "lon": 35.3000, "type": "research",
     "desc": "Heat-tolerant coral populations; research into climate-resilient reef genetics."},
    {"name": "Sanganeb Atoll, Sudan", "lat": 19.7300, "lon": 37.4400, "type": "healthy",
     "desc": "UNESCO Biosphere Reserve; isolated atoll 30 km offshore with pristine coral."},
    {"name": "Dahlak Archipelago, Eritrea", "lat": 15.7500, "lon": 40.1500, "type": "moderate",
     "desc": "Over 200 islands with largely unexplored reef systems in the southern Red Sea."},
    {"name": "Djibouti — Moucha Island", "lat": 11.7200, "lon": 43.2200, "type": "moderate",
     "desc": "Gulf of Tadjoura reefs; whale shark seasonal aggregation point."},
    {"name": "Hurghada Reefs, Egypt", "lat": 27.2578, "lon": 33.8117, "type": "moderate",
     "desc": "Major resort area; Giftun Island marine park with protected reef zones."},
    {"name": "Tiran Strait, Egypt", "lat": 27.9500, "lon": 34.5700, "type": "dive_site",
     "desc": "Four famous reefs (Jackson, Woodhouse, Thomas, Gordon) at the mouth of the Gulf of Aqaba."},
]

DATA_CARIBBEAN = [
    {"name": "Belize Barrier Reef", "lat": 17.3200, "lon": -87.5300, "type": "healthy",
     "desc": "Second-largest barrier reef in the world; UNESCO World Heritage Site since 1996."},
    {"name": "Great Blue Hole, Belize", "lat": 17.3156, "lon": -87.5347, "type": "dive_site",
     "desc": "Giant marine sinkhole 300 m across and 124 m deep; stalactites and reef sharks."},
    {"name": "Bonaire Marine Park", "lat": 12.1443, "lon": -68.2655, "type": "healthy",
     "desc": "Self-guided shore diving paradise; one of the best-managed reef parks globally."},
    {"name": "Cayman Islands — Bloody Bay Wall", "lat": 19.7000, "lon": -80.0500, "type": "dive_site",
     "desc": "Dramatic wall dive starting at 6 m and plunging to 1,800 m; pristine sponges and corals."},
    {"name": "Jardines de la Reina, Cuba", "lat": 21.3000, "lon": -79.0000, "type": "healthy",
     "desc": "Cuba's marine crown jewel; no-take marine reserve with Caribbean's healthiest reefs."},
    {"name": "Saba Marine Park, Netherlands Antilles", "lat": 17.6300, "lon": -63.2400, "type": "healthy",
     "desc": "Volcanic island reefs with pinnacles; pioneering marine park established 1987."},
    {"name": "Roatan, Honduras", "lat": 16.3200, "lon": -86.5300, "type": "dive_site",
     "desc": "Part of the Mesoamerican Reef; steep walls and rich macro life at affordable prices."},
    {"name": "Turks and Caicos — Wall Diving", "lat": 21.7900, "lon": -72.1600, "type": "dive_site",
     "desc": "Columbus Passage wall starting at 12 m; eagle rays, humpback whale migration."},
    {"name": "Buck Island Reef, USVI", "lat": 17.7883, "lon": -64.6200, "type": "research",
     "desc": "National monument with underwater snorkel trail; elkhorn coral restoration site."},
    {"name": "Flower Garden Banks, Gulf of Mexico", "lat": 27.8833, "lon": -93.8167, "type": "healthy",
     "desc": "Northernmost coral reefs in the continental US; 50%+ living coral cover."},
    {"name": "Los Roques, Venezuela", "lat": 11.8500, "lon": -66.7500, "type": "moderate",
     "desc": "Archipelago national park with extensive reef flats and seagrass beds."},
    {"name": "Curacao Reefs", "lat": 12.1696, "lon": -68.9900, "type": "dive_site",
     "desc": "Shore-accessible reef diving; healthy deep reefs below 30 m with unique sponge assemblages."},
]

DATA_MALDIVES = [
    {"name": "North Male Atoll — Banana Reef", "lat": 4.2700, "lon": 73.5300, "type": "dive_site",
     "desc": "The Maldives' first dive site; overhangs, caves, and dense fish schools."},
    {"name": "South Ari Atoll — Whale Shark Point", "lat": 3.5400, "lon": 72.8600, "type": "dive_site",
     "desc": "Year-round whale shark encounters along the atoll's outer edge."},
    {"name": "Baa Atoll — Hanifaru Bay", "lat": 5.1700, "lon": 73.0000, "type": "healthy",
     "desc": "UNESCO Biosphere Reserve; mass manta ray and whale shark feeding aggregation."},
    {"name": "Vaavu Atoll — Fotteyo Kandu", "lat": 3.3700, "lon": 73.4200, "type": "dive_site",
     "desc": "World-class channel dive; grey reef sharks, eagle rays, and overhangs at 30 m."},
    {"name": "Addu Atoll", "lat": -0.6300, "lon": 73.1600, "type": "moderate",
     "desc": "Southernmost atoll straddling the equator; WWII wrecks and house reef biodiversity."},
    {"name": "Rasdhoo Atoll", "lat": 4.2600, "lon": 72.9800, "type": "dive_site",
     "desc": "Hammerhead Point for early-morning hammerhead shark encounters."},
    {"name": "Lhaviyani Atoll — Fushifaru Thila", "lat": 5.3700, "lon": 73.5100, "type": "healthy",
     "desc": "Protected thila covered in soft corals; macro critters and reef fish galore."},
    {"name": "North Nilandhe Atoll", "lat": 3.0200, "lon": 72.9300, "type": "healthy",
     "desc": "Less-visited atoll with pristine house reefs and mantas in channels."},
    {"name": "Maldives Marine Research Institute", "lat": 4.1700, "lon": 73.5100, "type": "research",
     "desc": "Male-based institute coordinating national coral monitoring and reef restoration."},
    {"name": "Huvadhoo Atoll", "lat": 0.5000, "lon": 73.3000, "type": "healthy",
     "desc": "One of the deepest atolls globally; diverse channnel ecosystems and remote reefs."},
    {"name": "Raa Atoll — Manta Point", "lat": 5.5500, "lon": 72.9000, "type": "dive_site",
     "desc": "Cleaning station for resident manta rays; soft coral gardens on the reef slope."},
    {"name": "Laamu Atoll", "lat": 1.8500, "lon": 73.4500, "type": "moderate",
     "desc": "Reef systems with climate monitoring buoys; coral garden restoration in progress."},
]

DATA_PACIFIC_ISLANDS = [
    {"name": "Rangiroa, French Polynesia", "lat": -15.1167, "lon": -147.6500, "type": "dive_site",
     "desc": "Second-largest atoll on Earth; Tiputa Pass with dolphins, sharks, and mantas."},
    {"name": "Fakarava, French Polynesia", "lat": -16.0500, "lon": -145.6500, "type": "healthy",
     "desc": "UNESCO Biosphere Reserve; south pass has the famous Wall of Sharks — 700+ grey reef sharks."},
    {"name": "Great Astrolabe Reef, Fiji", "lat": -18.8000, "lon": 178.5000, "type": "healthy",
     "desc": "Fourth-largest barrier reef in the world; rich soft coral diversity."},
    {"name": "Rainbow Reef, Fiji", "lat": -16.8200, "lon": -179.9000, "type": "dive_site",
     "desc": "Soft coral capital of the world; Great White Wall dive site in Somosomo Strait."},
    {"name": "Palau — Rock Islands", "lat": 7.1600, "lon": 134.3800, "type": "hotspot",
     "desc": "UNESCO World Heritage; Jellyfish Lake, Blue Corner, and 700+ coral species."},
    {"name": "Palau — German Channel", "lat": 7.1000, "lon": 134.2200, "type": "dive_site",
     "desc": "Manta ray cleaning station and coral gardens on a man-made channel through the reef."},
    {"name": "Chuuk Lagoon, Micronesia", "lat": 7.4167, "lon": 151.7833, "type": "dive_site",
     "desc": "WWII Japanese fleet wreck graveyard; coral-encrusted ships in a protected lagoon."},
    {"name": "Yap, Micronesia", "lat": 9.5100, "lon": 138.1300, "type": "dive_site",
     "desc": "Resident manta ray population; traditional conservation practices protect reefs."},
    {"name": "Apo Island, Philippines", "lat": 9.0700, "lon": 123.2700, "type": "restored",
     "desc": "Community-managed marine sanctuary; textbook case of reef recovery after protection."},
    {"name": "Moorea, French Polynesia", "lat": -17.5400, "lon": -149.8300, "type": "research",
     "desc": "CRIOBE research station; long-term coral reef monitoring since 1971."},
    {"name": "Bikini Atoll, Marshall Islands", "lat": 11.5833, "lon": 165.3833, "type": "healthy",
     "desc": "Nuclear testing site with remarkable coral recovery; thriving shark populations."},
    {"name": "Cocos Island, Costa Rica", "lat": 5.5300, "lon": -87.0600, "type": "healthy",
     "desc": "Remote oceanic island; massive hammerhead schools and deep coral communities."},
]

DATA_BLEACHING_EVENTS = [
    {"name": "2016 GBR Mass Bleaching — Lizard Island", "lat": -14.6682, "lon": 145.4637, "type": "bleached",
     "desc": "2016: Worst bleaching on record; 67% of shallow-water corals died in northern GBR."},
    {"name": "2017 GBR Bleaching — Central Section", "lat": -18.3000, "lon": 147.5000, "type": "bleached",
     "desc": "2017: Unprecedented back-to-back event; central GBR severely impacted."},
    {"name": "2020 GBR Third Mass Bleaching", "lat": -20.0000, "lon": 149.0000, "type": "bleached",
     "desc": "2020: Third mass bleaching in 5 years; most widespread event across the entire reef."},
    {"name": "1998 Global Bleaching — Maldives", "lat": 4.1753, "lon": 73.5093, "type": "bleached",
     "desc": "1998 El Nino: Up to 90% coral mortality in Maldivian reef flats."},
    {"name": "1998 Global Bleaching — Seychelles", "lat": -4.6796, "lon": 55.4920, "type": "bleached",
     "desc": "1998: Seychelles lost over 90% of live coral; slow ongoing recovery."},
    {"name": "2005 Caribbean Bleaching — USVI", "lat": 18.3358, "lon": -64.8963, "type": "bleached",
     "desc": "2005: Hottest Caribbean sea temps on record; 80% bleaching across the region."},
    {"name": "2010 Southeast Asia Bleaching", "lat": 1.3521, "lon": 103.8198, "type": "bleached",
     "desc": "2010: Severe bleaching in Singapore, Malaysia, and Thailand; 80% bleaching."},
    {"name": "2014-2017 Global Bleaching Event — Hawaii", "lat": 19.8968, "lon": -155.5828, "type": "bleached",
     "desc": "Third global bleaching event; Hawaii reefs bleached in 2014 and 2015 back-to-back."},
    {"name": "2016 Kiribati Bleaching", "lat": 1.8700, "lon": -157.3600, "type": "bleached",
     "desc": "2016: Extreme bleaching in Kiribati; some reefs lost nearly all live coral."},
    {"name": "2024 Fourth Global Bleaching Event", "lat": -3.3731, "lon": 29.9189, "type": "bleached",
     "desc": "2024: NOAA confirmed fourth global mass bleaching event; record ocean temperatures."},
    {"name": "2016 Okinawa Bleaching, Japan", "lat": 26.3344, "lon": 127.8056, "type": "bleached",
     "desc": "2016: 70% of coral around Okinawa bleached; major die-off on Sekisei Lagoon reefs."},
    {"name": "2019 French Polynesia Bleaching", "lat": -17.6797, "lon": -149.4068, "type": "bleached",
     "desc": "2019: Moderate-to-severe bleaching across Society Islands despite relative resilience."},
]

DATA_RESTORATION_PROJECTS = [
    {"name": "Coral Gardening — Bonaire", "lat": 12.1443, "lon": -68.2655, "type": "restored",
     "desc": "Fragment-based coral nurseries growing staghorn and elkhorn corals for outplanting."},
    {"name": "Mars Coral Reef Restoration — Sulawesi", "lat": -5.2500, "lon": 119.3000, "type": "restored",
     "desc": "Mars Inc. program using Reef Stars — hexagonal steel structures seeded with coral fragments."},
    {"name": "Mote Marine Lab — Florida Keys", "lat": 24.6617, "lon": -81.4539, "type": "restored",
     "desc": "Micro-fragmentation and assisted gene flow to produce heat-resistant corals."},
    {"name": "Reef Design Lab — Melbourne", "lat": -37.8136, "lon": 144.9631, "type": "research",
     "desc": "3D-printed reef structures deployed in Australia and the Middle East."},
    {"name": "Coral Triangle Initiative HQ — Jakarta", "lat": -6.2088, "lon": 106.8456, "type": "research",
     "desc": "Six-nation partnership protecting reefs across Indonesia, Philippines, Malaysia, PNG, Solomons, Timor-Leste."},
    {"name": "CRF — Coral Restoration Foundation, Key Largo", "lat": 25.0865, "lon": -80.4473, "type": "restored",
     "desc": "World's largest coral reef restoration program; coral tree nurseries growing 40,000+ corals."},
    {"name": "Biorock Reef — Pemuteran, Bali", "lat": -8.1500, "lon": 114.6400, "type": "restored",
     "desc": "Low-voltage electrical current accelerates coral growth on steel frames by 3-5x."},
    {"name": "Great Barrier Reef Foundation — Cairns", "lat": -16.9186, "lon": 145.7781, "type": "research",
     "desc": "AU$443 million program for GBR resilience; coral IVF and larval reseeding trials."},
    {"name": "Secore International — Curacao", "lat": 12.1696, "lon": -68.9900, "type": "restored",
     "desc": "Coral sexual reproduction and larval seeding technology for genetic diversity."},
    {"name": "Reef Check — Los Angeles HQ", "lat": 33.9416, "lon": -118.4085, "type": "research",
     "desc": "Global citizen science reef health monitoring in 90+ countries since 1996."},
    {"name": "Nature Seychelles — Reef Rescuers", "lat": -4.6167, "lon": 55.4500, "type": "restored",
     "desc": "Largest reef restoration project in the Indian Ocean; 50,000+ coral fragments transplanted."},
    {"name": "Saudi Arabia Red Sea Coral Nursery", "lat": 22.3000, "lon": 39.1000, "type": "restored",
     "desc": "KAUST-led nurseries growing heat-tolerant Red Sea corals for regional restoration."},
]

DATA_DEEP_SEA_CORAL = [
    {"name": "Lophelia Reef — Norway", "lat": 64.1000, "lon": 8.0000, "type": "deep",
     "desc": "World's largest known deep cold-water coral reef complex; Lophelia pertusa at 200-400 m."},
    {"name": "Darwin Mounds — NE Atlantic", "lat": 59.8200, "lon": -7.3900, "type": "deep",
     "desc": "Deep-water coral mounds at 1,000 m; first area protected from bottom trawling in EU waters."},
    {"name": "Strait of Sicily Deep Reefs", "lat": 37.0000, "lon": 13.5000, "type": "deep",
     "desc": "Mediterranean deep coral communities; white coral (Madrepora oculata) below 200 m."},
    {"name": "Blake Plateau, SE USA", "lat": 31.0000, "lon": -78.5000, "type": "deep",
     "desc": "Massive deep coral province at 500-900 m; one of the largest in the Atlantic."},
    {"name": "Aleutian Islands Deep Coral", "lat": 52.0000, "lon": -175.0000, "type": "deep",
     "desc": "Gorgonian and bamboo coral gardens in cold North Pacific waters; extremely biodiverse."},
    {"name": "Porcupine Seabight, Ireland", "lat": 51.5000, "lon": -13.0000, "type": "deep",
     "desc": "Carbonate mound province hosting Lophelia and Madrepora at 600-1,000 m depth."},
    {"name": "Tasman Fracture Zone, Australia", "lat": -44.0000, "lon": 147.0000, "type": "deep",
     "desc": "Deep seamount corals at 700-1,400 m in a marine reserve south of Tasmania."},
    {"name": "Charleston Bump, SE USA", "lat": 32.0000, "lon": -78.0000, "type": "deep",
     "desc": "Deep reef oasis on a geological feature deflecting the Gulf Stream; rich coral and sponge."},
    {"name": "Mauritanian Cold-Water Coral Mounds", "lat": 19.0000, "lon": -17.0000, "type": "deep",
     "desc": "Fossil and living coral mounds off West Africa; rare sub-tropical deep coral habitat."},
    {"name": "Kermadec Ridge, New Zealand", "lat": -30.0000, "lon": -178.5000, "type": "deep",
     "desc": "Volcanic seamount chain with deep gorgonians and stony corals at 200-1,500 m."},
    {"name": "Campos Basin, Brazil", "lat": -22.5000, "lon": -40.0000, "type": "deep",
     "desc": "Deep-water coral communities in 500-1,200 m; discovered during oil exploration surveys."},
    {"name": "Gulf of Mexico Deep Reefs", "lat": 28.0000, "lon": -88.5000, "type": "deep",
     "desc": "Lophelia colonies on hardground at 400-800 m; chemosynthetic communities nearby."},
]

DATA_SPECIES_HOTSPOTS = [
    {"name": "Coral Triangle Apex — Raja Ampat", "lat": -0.5500, "lon": 130.5000, "type": "hotspot",
     "desc": "600+ hard coral species; global peak of coral diversity and endemism."},
    {"name": "Central Indo-Pacific — Philippines", "lat": 10.3157, "lon": 123.8854, "type": "hotspot",
     "desc": "500+ hard coral species; Verde Island Passage is the densest marine area on Earth."},
    {"name": "Western Indian Ocean — Mozambique", "lat": -12.3000, "lon": 40.5000, "type": "hotspot",
     "desc": "Quirimbas Archipelago; 300+ coral species and endemic species along the East African coast."},
    {"name": "Red Sea Endemism Center", "lat": 22.0000, "lon": 38.5000, "type": "hotspot",
     "desc": "8-10% coral species endemic to the Red Sea; heat-adapted species found nowhere else."},
    {"name": "New Caledonia Lagoon", "lat": -22.2735, "lon": 166.4580, "type": "hotspot",
     "desc": "UNESCO World Heritage; 1,600 km barrier reef with 350+ coral species and endemic fish."},
    {"name": "Chagos Archipelago", "lat": -6.0000, "lon": 72.0000, "type": "healthy",
     "desc": "Largest no-take marine reserve; 300+ coral species and benchmark for pristine reef state."},
    {"name": "Southern Japan — Amami-Oshima", "lat": 28.3800, "lon": 129.5000, "type": "hotspot",
     "desc": "Northern range limit for many coral species; unique temperate-tropical overlap zone."},
    {"name": "Ningaloo Reef, Western Australia", "lat": -22.7000, "lon": 113.6800, "type": "healthy",
     "desc": "300+ coral species on the world's largest fringing reef; whale shark aggregation."},
    {"name": "Andaman Sea — Similan Islands", "lat": 8.6500, "lon": 97.6400, "type": "dive_site",
     "desc": "350+ coral species; unique mix of Indian Ocean and Pacific species on granite boulders."},
    {"name": "Great Barrier Reef Species Center", "lat": -18.0000, "lon": 147.0000, "type": "hotspot",
     "desc": "450+ hard coral species across 2,300 km; largest living structure visible from space."},
    {"name": "Socotra Island, Yemen", "lat": 12.4634, "lon": 53.8237, "type": "hotspot",
     "desc": "Galapagos of the Indian Ocean; unique coral assemblages with high endemism."},
    {"name": "Lord Howe Island, Australia", "lat": -31.5500, "lon": 159.0800, "type": "hotspot",
     "desc": "World's southernmost true coral reef; unique mix of tropical and temperate species."},
]


# ═══════════════════════════════════════════
# MODE CONFIGURATION
# ═══════════════════════════════════════════
MAP_MODES = {
    "Great Barrier Reef": {
        "data": DATA_GREAT_BARRIER_REEF,
        "center": [-18.0, 147.0],
        "zoom": 6,
        "desc": "Australia's iconic 2,300 km reef system — sections, dive sites, and research stations.",
    },
    "Coral Triangle": {
        "data": DATA_CORAL_TRIANGLE,
        "center": [0.0, 130.0],
        "zoom": 5,
        "desc": "The global epicenter of marine biodiversity spanning six nations.",
    },
    "Red Sea Coral Reefs": {
        "data": DATA_RED_SEA,
        "center": [22.0, 38.0],
        "zoom": 5,
        "desc": "Heat-tolerant reefs from Egypt to Djibouti — world-class diving and endemic species.",
    },
    "Caribbean Coral Reefs": {
        "data": DATA_CARIBBEAN,
        "center": [18.0, -75.0],
        "zoom": 5,
        "desc": "From the Belize Barrier Reef to Bonaire — Caribbean reef highlights.",
    },
    "Maldives Atolls": {
        "data": DATA_MALDIVES,
        "center": [3.0, 73.2],
        "zoom": 6,
        "desc": "Maldivian reef systems — atolls, house reefs, and marine protected areas.",
    },
    "Pacific Island Reefs": {
        "data": DATA_PACIFIC_ISLANDS,
        "center": [0.0, -170.0],
        "zoom": 3,
        "desc": "Reefs of French Polynesia, Fiji, Palau, Micronesia, and beyond.",
    },
    "Coral Bleaching Events": {
        "data": DATA_BLEACHING_EVENTS,
        "center": [0.0, 120.0],
        "zoom": 2,
        "desc": "Major coral bleaching events from 1998 to 2024 — locations and impacts.",
    },
    "Coral Restoration Projects": {
        "data": DATA_RESTORATION_PROJECTS,
        "center": [10.0, 40.0],
        "zoom": 2,
        "desc": "Active reef restoration initiatives worldwide — nurseries, 3D printing, larval reseeding.",
    },
    "Deep Sea Coral": {
        "data": DATA_DEEP_SEA_CORAL,
        "center": [30.0, -20.0],
        "zoom": 2,
        "desc": "Cold-water coral locations, deep reef habitats, and coral mound provinces.",
    },
    "Coral Species Hotspots": {
        "data": DATA_SPECIES_HOTSPOTS,
        "center": [0.0, 120.0],
        "zoom": 3,
        "desc": "Global biodiversity centers and endemic coral species concentrations.",
    },
}

# ═══════════════════════════════════════════
# REEF HEALTH API (NOAA Coral Reef Watch)
# ═══════════════════════════════════════════
@st.cache_data(ttl=3600)
def fetch_reef_watch_alerts() -> list:
    """Fetch current NOAA Coral Reef Watch bleaching alert area data (GeoJSON)."""
    url = "https://coralreefwatch.noaa.gov/product/vs/data/all_vs_data.json"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else data.get("features", [])
    except Exception:
        return []


# ═══════════════════════════════════════════
# HELPER: Build popup HTML
# ═══════════════════════════════════════════
def _popup_html(name: str, desc: str, site_type: str) -> str:
    """Create styled popup HTML with escaped text."""
    safe_name = html_module.escape(name)
    safe_desc = html_module.escape(desc)
    safe_type = html_module.escape(site_type)
    color = REEF_COLORS.get(site_type, REEF_COLORS["default"])
    return (
        f'<div style="background:#1a2235;color:#e8ecf4;padding:10px;border-radius:8px;'
        f'min-width:180px;max-width:260px;font-family:sans-serif;">'
        f'<b style="color:{color};font-size:0.95rem;">{safe_name}</b><br>'
        f'<span style="color:#8b97b0;font-size:0.75rem;text-transform:uppercase;">{safe_type}</span><br>'
        f'<span style="color:#c0c8d8;font-size:0.82rem;line-height:1.4;">{safe_desc}</span>'
        f'</div>'
    )


# ═══════════════════════════════════════════
# HELPER: Build map for a mode
# ═══════════════════════════════════════════
def _build_map(sites: list, center: list, zoom: int) -> folium.Map:
    """Create a dark-theme folium map with MarkerCluster for given sites."""
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name="Coral Sites").add_to(m)

    for site in sites:
        lat = site["lat"]
        lon = site["lon"]
        name = site["name"]
        desc = site.get("desc", "")
        site_type = site.get("type", "default")
        color = REEF_COLORS.get(site_type, REEF_COLORS["default"])

        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(_popup_html(name, desc, site_type), max_width=280),
            tooltip=html_module.escape(name),
        ).add_to(cluster)

    return m


# ═══════════════════════════════════════════
# HELPER: Build dataframe and stats
# ═══════════════════════════════════════════
def _build_dataframe(sites: list) -> pd.DataFrame:
    """Convert site list to a DataFrame."""
    rows = []
    for s in sites:
        rows.append({
            "Name": s["name"],
            "Latitude": s["lat"],
            "Longitude": s["lon"],
            "Type": s.get("type", ""),
            "Description": s.get("desc", ""),
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════
def render_coral_reef_maps_tab():
    """Main render function for the Coral Reef Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header emerald">
        <h4>\U0001fab8 Coral Reef Explorer</h4>
        <p>Explore the world's coral reefs &mdash; from the Great Barrier Reef to deep-sea corals, bleaching events, restoration projects, and species hotspots.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode selector ──
    mode_name = st.selectbox(
        "Map Mode",
        list(MAP_MODES.keys()),
        key="coral_mode_select",
    )

    mode = MAP_MODES[mode_name]
    sites = mode["data"]
    center = mode["center"]
    zoom = mode["zoom"]
    mode_desc = mode["desc"]

    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem;">{html_module.escape(mode_desc)}</p>',
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Stats row ──
    df = _build_dataframe(sites)
    type_counts = df["Type"].value_counts().to_dict()

    total_sites = len(sites)
    unique_types = len(type_counts)

    # Pick the two most common types for display
    top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    primary_type = top_types[0] if top_types else ("", 0)
    secondary_type = top_types[1] if len(top_types) > 1 else ("", 0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Sites", f"{total_sites}")
    with c2:
        st.metric("Site Types", f"{unique_types}")
    with c3:
        st.metric(
            html_module.escape(primary_type[0].replace("_", " ").title()) if primary_type[0] else "Primary",
            f"{primary_type[1]}",
        )
    with c4:
        st.metric(
            html_module.escape(secondary_type[0].replace("_", " ").title()) if secondary_type[0] else "Secondary",
            f"{secondary_type[1]}",
        )

    # ── Color legend ──
    active_types = sorted(set(s.get("type", "default") for s in sites))
    legend_items = " ".join(
        f'<span style="color:{REEF_COLORS.get(t, REEF_COLORS["default"])};font-size:0.8rem;">'
        f'\u25cf {html_module.escape(t.replace("_", " ").title())}</span>'
        for t in active_types
    )
    st.markdown(
        f'<div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:0.75rem;">{legend_items}</div>',
        unsafe_allow_html=True,
    )

    # ── Map ──
    m = _build_map(sites, center, zoom)
    st_html(m._repr_html_(), height=500)

    # ── Data table ──
    st.markdown("---")
    st.markdown("#### Site Details")
    st.dataframe(df, width="stretch", hide_index=True)

    # ── Site cards ──
    st.markdown("#### Site Overview")
    for site in sites:
        stype = site.get("type", "default")
        color = REEF_COLORS.get(stype, REEF_COLORS["default"])
        safe_name = html_module.escape(site["name"])
        safe_desc = html_module.escape(site.get("desc", ""))
        safe_type = html_module.escape(stype.replace("_", " ").title())
        st.markdown(f"""
        <div class="bio-card" style="display:flex;align-items:center;margin-bottom:0.5rem;">
            <div style="width:8px;height:56px;border-radius:4px;background:{color};
                        margin-right:1rem;flex-shrink:0;"></div>
            <div style="flex:1;">
                <div style="color:#e8ecf4;font-weight:600;font-size:0.9rem;">{safe_name}</div>
                <div style="color:{color};font-size:0.75rem;text-transform:uppercase;">{safe_type}</div>
                <div style="color:#8b97b0;font-size:0.8rem;">{safe_desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── CSV Download ──
    st.markdown("---")
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    safe_filename = mode_name.lower().replace(" ", "_").replace("—", "").replace("-", "_")
    st.download_button(
        f"Download {len(sites)} Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"coral_reef_{safe_filename}.csv",
        mime="text/csv",
        key="coral_csv_download",
    )
