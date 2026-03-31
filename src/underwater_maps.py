# -*- coding: utf-8 -*-
"""
Underwater World Explorer module for TerraScout AI.
Curated databases of dive sites, ocean trenches, coral reefs, underwater caves,
hydrothermal vents, submarine volcanoes, kelp forests, deep sea features,
marine protected areas, and famous underwater discoveries.
All data sources are free, no API key required.
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

# ═══════════════════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_TEXT2 = "#8b97b0"
_MUTED = "#5a6580"
_BORDER = "#2a3550"
_ACCENT = "#06b6d4"

# ═══════════════════════════════════════════════════════════════════════════════
# MAP MODE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════
MAP_MODES = [
    "World's Best Dive Sites",
    "Deep Ocean Trenches",
    "Coral Reefs",
    "Underwater Caves & Cenotes",
    "Hydrothermal Vents",
    "Submarine Volcanoes",
    "Kelp Forests & Seagrass",
    "Deep Sea Features",
    "Marine Protected Areas",
    "Famous Underwater Discoveries",
]

MODE_DESCRIPTIONS = {
    "World's Best Dive Sites": (
        "The most spectacular diving destinations on Earth -- from the Great Blue Hole "
        "of Belize to the crystal waters of Sipadan. These sites attract divers worldwide "
        "for their extraordinary visibility, marine life, and underwater topography. "
        "Each location offers unique experiences from wall dives to drift dives, "
        "manta ray encounters, and underwater cathedrals of coral."
    ),
    "Deep Ocean Trenches": (
        "The deepest scars on Earth's surface, formed by tectonic subduction zones. "
        "The Mariana Trench plunges to 10,994 m at Challenger Deep -- the deepest known "
        "point in the ocean. These trenches host extremophile life forms thriving under "
        "crushing pressures exceeding 1,000 atmospheres, in total darkness and near-freezing "
        "temperatures. Only a handful of manned descents have reached the hadal zone."
    ),
    "Coral Reefs": (
        "The rainforests of the sea -- coral reef ecosystems cover less than 1% of the "
        "ocean floor but support over 25% of all marine species. The Great Barrier Reef "
        "stretches over 2,300 km and is visible from space. These living structures are "
        "built over millennia by tiny coral polyps and face existential threats from "
        "warming oceans, acidification, and human activity."
    ),
    "Underwater Caves & Cenotes": (
        "Submerged cave systems and cenotes represent some of the most challenging and "
        "beautiful diving environments on Earth. The Yucatan Peninsula alone holds over "
        "6,000 cenotes connected by the world's longest underwater cave system (Sistema "
        "Sac Actun at 376 km). Blue holes, flooded mines, and submarine caves harbor "
        "unique ecosystems and pristine geological formations."
    ),
    "Hydrothermal Vents": (
        "Deep-sea hydrothermal vents are fissures on the ocean floor that discharge "
        "superheated, mineral-rich water at temperatures up to 400 degrees C. Black smokers "
        "emit dark plumes of sulfide minerals, while white smokers release lighter barium "
        "and silicon compounds. First discovered in 1977 near the Galapagos, these vents "
        "support chemosynthetic ecosystems independent of sunlight, redefining our "
        "understanding of life's possibilities."
    ),
    "Submarine Volcanoes": (
        "An estimated 1 million submarine volcanoes dot the ocean floor, with roughly "
        "75% of all volcanic activity on Earth occurring underwater. Seamounts, guyots, "
        "and active submarine eruptions shape the seabed and occasionally breach the "
        "surface to create new islands. Kavachi in the Solomon Islands erupts so "
        "frequently it has been dubbed 'Sharkano' for the sharks living in its crater."
    ),
    "Kelp Forests & Seagrass": (
        "Underwater forests of giant kelp and vast seagrass meadows are among the most "
        "productive ecosystems on Earth. Kelp can grow up to 60 cm per day, forming "
        "dense canopies reaching 45 m tall. Seagrass meadows sequester carbon 35 times "
        "faster than tropical rainforests per hectare and provide critical nursery habitat "
        "for commercially important fish species, sea turtles, and dugongs."
    ),
    "Deep Sea Features": (
        "The deep ocean floor is far from flat -- it is sculpted by mid-ocean ridges "
        "stretching 65,000 km around the globe, abyssal plains covering 50% of Earth's "
        "surface, fracture zones, submarine canyons deeper than the Grand Canyon, and "
        "mysterious abyssal hills. These features record the tectonic history of our "
        "planet and host unique ecosystems adapted to extreme conditions."
    ),
    "Marine Protected Areas": (
        "Marine Protected Areas (MPAs) safeguard critical ocean habitats, biodiversity "
        "hotspots, and cultural heritage sites. Currently about 8% of the global ocean "
        "is designated as protected, with targets set for 30% by 2030. From the vast "
        "Papahanaumokuakea Marine National Monument to small no-take reserves, MPAs "
        "have proven to increase fish biomass, restore ecosystems, and boost resilience "
        "to climate change."
    ),
    "Famous Underwater Discoveries": (
        "From the RMS Titanic resting at 3,800 m to ancient sunken cities and underwater "
        "museums, humanity has made extraordinary discoveries beneath the waves. Modern "
        "technology -- ROVs, side-scan sonar, and deep submersibles -- continues to reveal "
        "lost ships, submerged harbors, and artifacts that rewrite history. The ocean "
        "floor remains the planet's greatest museum, with millions of wrecks yet to be found."
    ),
}

MODE_COLORS = {
    "World's Best Dive Sites": "#06b6d4",
    "Deep Ocean Trenches": "#3b82f6",
    "Coral Reefs": "#10b981",
    "Underwater Caves & Cenotes": "#8b5cf6",
    "Hydrothermal Vents": "#ef4444",
    "Submarine Volcanoes": "#f97316",
    "Kelp Forests & Seagrass": "#22c55e",
    "Deep Sea Features": "#6366f1",
    "Marine Protected Areas": "#14b8a6",
    "Famous Underwater Discoveries": "#f59e0b",
}

MODE_ICONS = {
    "World's Best Dive Sites": "&#127754;",
    "Deep Ocean Trenches": "&#11015;",
    "Coral Reefs": "&#129680;",
    "Underwater Caves & Cenotes": "&#128371;",
    "Hydrothermal Vents": "&#127755;",
    "Submarine Volcanoes": "&#127755;",
    "Kelp Forests & Seagrass": "&#127793;",
    "Deep Sea Features": "&#127758;",
    "Marine Protected Areas": "&#128154;",
    "Famous Underwater Discoveries": "&#128269;",
}

# ═══════════════════════════════════════════════════════════════════════════════
# CURATED DATABASES
# ═══════════════════════════════════════════════════════════════════════════════

BEST_DIVE_SITES = [
    {"name": "Great Blue Hole", "lat": 17.3155, "lon": -87.5347,
     "country": "Belize", "depth_m": 124, "visibility_m": 30,
     "type": "Sinkhole / Wall Dive",
     "highlights": "Giant stalactites, reef sharks, bull sharks, groupers",
     "details": "A massive marine sinkhole 300 m across and 124 m deep. UNESCO World Heritage Site. "
                "Formed as a limestone cave during the last Ice Age, then flooded as sea levels rose. "
                "Jacques Cousteau declared it one of the top 10 dive sites in the world."},
    {"name": "Sipadan Island", "lat": 4.1150, "lon": 118.6286,
     "country": "Malaysia", "depth_m": 600, "visibility_m": 40,
     "type": "Oceanic Island / Wall Dive",
     "highlights": "Barracuda tornado, turtle tomb cave, sea turtle parades, white-tip reef sharks",
     "details": "Rising 600 m from the seabed, Sipadan is Malaysia's only oceanic island. "
                "Home to over 3,000 fish species and hundreds of coral species. Limited to 120 dive "
                "permits per day to protect the ecosystem. Famous for its swirling barracuda vortex."},
    {"name": "SS Thistlegorm", "lat": 27.8129, "lon": 33.9221,
     "country": "Egypt (Red Sea)", "depth_m": 30, "visibility_m": 25,
     "type": "Wreck Dive",
     "highlights": "WWII cargo ship, motorcycles, trucks, locomotives, anti-aircraft guns",
     "details": "British cargo ship sunk by German bombers in 1941. Resting at 30 m in the Red Sea, "
                "she carries a time capsule of WWII military supplies. Discovered by Cousteau in 1955."},
    {"name": "Maldives - South Ari Atoll", "lat": 3.5500, "lon": 72.8500,
     "country": "Maldives", "depth_m": 40, "visibility_m": 35,
     "type": "Atoll / Channel Dive",
     "highlights": "Whale sharks, manta rays, hammerhead sharks, coral gardens",
     "details": "The Maldives offers some of the best pelagic diving on Earth. South Ari Atoll is "
                "one of the few places where whale sharks can be seen year-round. Crystal-clear waters "
                "with 30+ m visibility and thriving coral reefs despite warming pressures."},
    {"name": "Galapagos - Gordon Rocks", "lat": -0.5231, "lon": -90.2797,
     "country": "Ecuador", "depth_m": 35, "visibility_m": 15,
     "type": "Pinnacle / Drift Dive",
     "highlights": "Hammerhead sharks, sea lions, marine iguanas, mola mola, whale sharks",
     "details": "Known as the 'washing machine' for its strong currents, Gordon Rocks is the premier "
                "hammerhead shark dive in the Galapagos. Schools of hundreds of scalloped hammerheads "
                "cruise past divers clinging to rocky walls in nutrient-rich waters."},
    {"name": "Raja Ampat - Misool", "lat": -1.8500, "lon": 130.0667,
     "country": "Indonesia", "depth_m": 30, "visibility_m": 25,
     "type": "Reef / Macro Dive",
     "highlights": "Highest marine biodiversity on Earth, manta rays, wobbegong sharks, pygmy seahorses",
     "details": "Raja Ampat holds the world record for marine biodiversity: 1,508 fish species and "
                "537 coral species in a single survey area. Misool's protected waters have seen fish "
                "biomass increase 250% since 2005 thanks to community-managed no-take zones."},
    {"name": "Palau - Blue Corner", "lat": 7.1383, "lon": 134.2188,
     "country": "Palau", "depth_m": 30, "visibility_m": 30,
     "type": "Wall / Drift Dive",
     "highlights": "Grey reef sharks, Napoleon wrasse, eagle rays, giant trevally, barracuda",
     "details": "Consistently ranked among the top 5 dive sites worldwide. A submerged reef plateau "
                "where powerful currents attract vast schools of pelagic fish. Divers hook into the "
                "wall and watch the marine parade drift past."},
    {"name": "Cenote Dos Ojos", "lat": 20.3253, "lon": -87.3881,
     "country": "Mexico", "depth_m": 35, "visibility_m": 60,
     "type": "Cave / Cenote Dive",
     "highlights": "Crystal-clear water, stalactites, halocline layers, bat cave, light effects",
     "details": "Part of the longest explored underwater cave system in the world (Sistema Sac Actun). "
                "Two main sinkholes ('eyes') connected by 400+ km of surveyed passages. Visibility "
                "can exceed 60 m in gin-clear freshwater above the halocline."},
    {"name": "Richelieu Rock", "lat": 9.3550, "lon": 98.0214,
     "country": "Thailand", "depth_m": 35, "visibility_m": 20,
     "type": "Pinnacle / Macro Dive",
     "highlights": "Whale sharks (Feb-May), seahorses, ghost pipefish, frogfish, soft corals",
     "details": "A horseshoe-shaped pinnacle rising from the Andaman Sea seabed. Thailand's premier "
                "dive site and one of the best macro diving locations in the world. Purple and orange "
                "soft corals blanket every surface during peak season."},
    {"name": "Silfra Fissure", "lat": 64.2559, "lon": -21.1167,
     "country": "Iceland", "depth_m": 18, "visibility_m": 100,
     "type": "Fissure / Drift Dive",
     "highlights": "100 m visibility, tectonic plate boundary, glacial water, cathedral formations",
     "details": "Dive between the North American and Eurasian tectonic plates in water filtered "
                "through lava rock for 30-100 years. Visibility exceeds 100 m, making it the clearest "
                "dive water on Earth. Temperature is a constant 2-4 degrees C year-round."},
    {"name": "Cocos Island", "lat": 5.5319, "lon": -87.0614,
     "country": "Costa Rica", "depth_m": 40, "visibility_m": 20,
     "type": "Oceanic Island / Pelagic Dive",
     "highlights": "Scalloped hammerhead schools, whale sharks, tiger sharks, dolphins, mantas",
     "details": "Remote uninhabited island 550 km off Costa Rica's Pacific coast. Scalloped "
                "hammerhead sharks gather in schools of hundreds at cleaning stations. UNESCO World "
                "Heritage Site with some of the best big-animal diving on the planet."},
    {"name": "Tubbataha Reef", "lat": 8.9167, "lon": 119.8167,
     "country": "Philippines", "depth_m": 40, "visibility_m": 35,
     "type": "Atoll / Wall Dive",
     "highlights": "Pristine walls, hammerhead sharks, manta rays, whale sharks, tiger sharks",
     "details": "A remote atoll in the Sulu Sea accessible only by liveaboard during the March-June "
                "season. UNESCO World Heritage Site protecting 97,030 hectares of marine wilderness. "
                "Vertical walls drop to over 100 m with pristine hard coral cover."},
    {"name": "Ras Mohammed", "lat": 27.7300, "lon": 34.2530,
     "country": "Egypt (Red Sea)", "depth_m": 25, "visibility_m": 30,
     "type": "Reef / Wall Dive",
     "highlights": "Shark Reef, Yolanda Reef, jackfish tornado, Napoleon wrasse, coral gardens",
     "details": "The jewel of the Red Sea at the southern tip of the Sinai Peninsula. Shark and "
                "Yolanda Reefs form an underwater amphitheater where currents bring pelagic action. "
                "The wreck of the Yolanda cargo ship spills toilets and bathtubs across the reef."},
    {"name": "Cozumel - Palancar Reef", "lat": 20.3597, "lon": -87.0128,
     "country": "Mexico", "depth_m": 30, "visibility_m": 40,
     "type": "Reef / Drift Dive",
     "highlights": "Towering coral pinnacles, splendid toadfish (endemic), eagle rays, turtles",
     "details": "One of the largest barrier reefs in the Western Hemisphere. Palancar's dramatic "
                "coral formations include tunnels, swimthroughs, and towering pillars. Home to the "
                "splendid toadfish, found nowhere else on Earth."},
    {"name": "Shark Point (Hin Musang)", "lat": 7.6167, "lon": 98.6833,
     "country": "Thailand", "depth_m": 24, "visibility_m": 15,
     "type": "Pinnacle / Reef Dive",
     "highlights": "Leopard sharks, soft corals, seahorses, ornate ghost pipefish",
     "details": "Three submerged pinnacles southeast of Phuket draped in vibrant pink and purple "
                "soft corals. Leopard sharks rest on sandy patches between the pinnacles. One of "
                "Thailand's marine protected dive sites."},
]

DEEP_OCEAN_TRENCHES = [
    {"name": "Mariana Trench - Challenger Deep", "lat": 11.3493, "lon": 142.1996,
     "ocean": "Pacific", "depth_m": 10994, "length_km": 2550,
     "tectonic": "Pacific Plate subducting under Mariana Plate",
     "details": "The deepest known point on Earth. First reached by Jacques Piccard and Don Walsh "
                "in 1960 aboard the bathyscaphe Trieste. James Cameron made a solo descent in 2012. "
                "Victor Vescovo reached the very bottom in 2019 and found plastic waste."},
    {"name": "Tonga Trench", "lat": -22.9167, "lon": -174.7167,
     "ocean": "Pacific", "depth_m": 10882, "length_km": 860,
     "tectonic": "Pacific Plate subducting under Tonga Plate",
     "details": "Second deepest trench on Earth. Horizon Deep reaches 10,882 m. Located in one of "
                "the most seismically active regions, producing massive earthquakes and tsunamis. "
                "Victor Vescovo reached the bottom in 2019 during the Five Deeps Expedition."},
    {"name": "Philippine Trench", "lat": 10.0000, "lon": 127.0000,
     "ocean": "Pacific", "depth_m": 10540, "length_km": 1320,
     "tectonic": "Philippine Sea Plate subducting under Eurasian Plate",
     "details": "Third deepest ocean trench. Emden Deep reaches 10,540 m. Extends from Luzon to "
                "Halmahera. Home to unique hadal zone organisms including amphipods, snailfish, "
                "and holothurians adapted to extreme pressure."},
    {"name": "Puerto Rico Trench", "lat": 19.7167, "lon": -66.5000,
     "ocean": "Atlantic", "depth_m": 8376, "length_km": 800,
     "tectonic": "North American Plate subducting under Caribbean Plate",
     "details": "Deepest point in the Atlantic Ocean. Milwaukee Deep reaches 8,376 m. A complex "
                "tectonic boundary where the North American plate slides under the Caribbean plate, "
                "generating significant earthquake and tsunami hazard for the Caribbean islands."},
    {"name": "Java Trench (Sunda Trench)", "lat": -10.3833, "lon": 109.9833,
     "ocean": "Indian", "depth_m": 7290, "length_km": 3200,
     "tectonic": "Indo-Australian Plate subducting under Eurasian Plate",
     "details": "Deepest point in the Indian Ocean at 7,290 m. Stretches 3,200 km from Myanmar to "
                "Australia, making it one of the longest trenches. The 2004 Boxing Day tsunami was "
                "generated along this subduction zone."},
    {"name": "Kermadec Trench", "lat": -30.0000, "lon": -177.0000,
     "ocean": "Pacific", "depth_m": 10047, "length_km": 1000,
     "tectonic": "Pacific Plate subducting under Indo-Australian Plate",
     "details": "Extends north of New Zealand to the Tonga Trench. Reaches 10,047 m at Scholl Deep. "
                "In 2011 a living snailfish was filmed at 7,966 m, setting a then-record for the "
                "deepest fish ever observed. The trench is entirely within New Zealand's EEZ."},
    {"name": "Japan Trench", "lat": 36.0000, "lon": 143.0000,
     "ocean": "Pacific", "depth_m": 8412, "length_km": 800,
     "tectonic": "Pacific Plate subducting under Okhotsk Plate",
     "details": "Source of the devastating 2011 Tohoku earthquake (M9.1) and tsunami that caused "
                "the Fukushima nuclear disaster. Reaches 8,412 m deep. Research submersibles have "
                "observed rapid seafloor changes caused by the massive tectonic displacement."},
    {"name": "Kuril-Kamchatka Trench", "lat": 44.0000, "lon": 150.5000,
     "ocean": "Pacific", "depth_m": 10542, "length_km": 2200,
     "tectonic": "Pacific Plate subducting under Okhotsk Plate",
     "details": "One of the deepest trenches in the Pacific, reaching 10,542 m. Extends from "
                "Kamchatka to Hokkaido along the Kuril Islands volcanic arc. Extremely seismically "
                "active with frequent large earthquakes."},
    {"name": "Peru-Chile Trench (Atacama Trench)", "lat": -23.3500, "lon": -71.3500,
     "ocean": "Pacific", "depth_m": 8065, "length_km": 5900,
     "tectonic": "Nazca Plate subducting under South American Plate",
     "details": "The longest ocean trench on Earth at 5,900 km, running the full length of western "
                "South America. Richards Deep reaches 8,065 m. Drives the uplift of the Andes "
                "mountains and generates frequent devastating earthquakes."},
    {"name": "South Sandwich Trench", "lat": -56.5000, "lon": -25.0000,
     "ocean": "Atlantic", "depth_m": 8266, "length_km": 965,
     "tectonic": "South American Plate subducting under Scotia Plate",
     "details": "The deepest trench in the Southern Atlantic, reaching 8,266 m at Meteor Deep. "
                "Located in one of the most remote and inhospitable regions on Earth near Antarctica. "
                "Associated with the South Sandwich volcanic island arc."},
    {"name": "Aleutian Trench", "lat": 51.0000, "lon": -177.0000,
     "ocean": "Pacific", "depth_m": 7679, "length_km": 3400,
     "tectonic": "Pacific Plate subducting under North American Plate",
     "details": "Stretches 3,400 km along the Aleutian Islands from Alaska. Reaches 7,679 m deep. "
                "Generated the 1946 and 1957 Aleutian tsunamis that devastated Hawaii. The subduction "
                "zone feeds the Aleutian volcanic arc with over 40 active volcanoes."},
    {"name": "Middle America Trench", "lat": 14.0000, "lon": -93.0000,
     "ocean": "Pacific", "depth_m": 6662, "length_km": 2750,
     "tectonic": "Cocos & Rivera Plates subducting under Caribbean & North American Plates",
     "details": "Runs from central Mexico to Costa Rica. Generates devastating earthquakes "
                "including the 1985 Mexico City earthquake (M8.0) that killed over 10,000 people. "
                "The subduction zone is complex with multiple plate interactions."},
]

CORAL_REEFS = [
    {"name": "Great Barrier Reef", "lat": -18.2871, "lon": 147.6992,
     "country": "Australia", "area_km2": 344400, "status": "Threatened",
     "reef_type": "Barrier Reef",
     "highlights": "2,900+ individual reefs, 900 islands, 1,500 fish species, 400 coral species",
     "details": "The largest coral reef system on Earth, visible from space. UNESCO World Heritage "
                "Site stretching over 2,300 km along the Queensland coast. Has suffered multiple "
                "mass bleaching events in 2016, 2017, 2020, and 2022 due to ocean warming."},
    {"name": "Mesoamerican Barrier Reef", "lat": 17.5000, "lon": -87.5000,
     "country": "Belize/Mexico/Guatemala/Honduras", "area_km2": 96300,
     "status": "Vulnerable", "reef_type": "Barrier Reef",
     "highlights": "Largest reef in Western Hemisphere, whale sharks, manatees, sea turtles",
     "details": "Stretches over 1,000 km from the Yucatan to Honduras. Second largest barrier "
                "reef system globally. Includes the Belize Barrier Reef UNESCO World Heritage Site. "
                "Supports fisheries for 2 million people across four nations."},
    {"name": "Raja Ampat Coral Triangle", "lat": -0.5000, "lon": 130.5000,
     "country": "Indonesia", "area_km2": 40000, "status": "Protected",
     "reef_type": "Fringing & Patch Reefs",
     "highlights": "Highest marine biodiversity on Earth, 600+ coral species, 1,700+ fish species",
     "details": "The epicenter of the Coral Triangle, which contains 76% of all known coral species. "
                "Raja Ampat alone has more coral species than the entire Caribbean. Community-managed "
                "marine protected areas have led to dramatic recovery of fish populations."},
    {"name": "Red Sea Coral Reefs", "lat": 22.0000, "lon": 38.0000,
     "country": "Egypt/Saudi Arabia/Sudan", "area_km2": 17640,
     "status": "Relatively Healthy", "reef_type": "Fringing Reef",
     "highlights": "Heat-resistant corals, 300+ coral species, 1,200 fish species, pristine walls",
     "details": "Red Sea corals are among the most heat-tolerant on Earth, having adapted to "
                "naturally warm waters. The northern Red Sea may serve as a climate refuge for "
                "corals as other reefs decline. Exceptionally clear water with 30+ m visibility."},
    {"name": "New Caledonia Barrier Reef", "lat": -21.5000, "lon": 165.5000,
     "country": "New Caledonia (France)", "area_km2": 24000,
     "status": "UNESCO Protected", "reef_type": "Barrier Reef",
     "highlights": "Second longest barrier reef, dugongs, nautilus, endemic species",
     "details": "The world's second longest double barrier reef (1,500 km). UNESCO World Heritage "
                "Site with one of the most diverse reef ecosystems in the Pacific. Home to the "
                "endangered nautilus and significant dugong populations."},
    {"name": "Andros Barrier Reef", "lat": 24.4000, "lon": -77.9500,
     "country": "Bahamas", "area_km2": 5800, "status": "Vulnerable",
     "reef_type": "Barrier Reef",
     "highlights": "Third largest barrier reef, blue holes, wall diving, shark aggregations",
     "details": "The third largest barrier reef in the world, stretching 225 km along the east "
                "coast of Andros Island. Features dramatic wall dives dropping to 1,800 m into "
                "the Tongue of the Ocean. Numerous blue holes dot the reef platform."},
    {"name": "Tubbataha Reef", "lat": 8.9167, "lon": 119.8167,
     "country": "Philippines", "area_km2": 97030, "status": "Well Protected",
     "reef_type": "Atoll Reef",
     "highlights": "Pristine coral cover, 600+ fish species, manta rays, sea turtles, sharks",
     "details": "One of the Philippines' premier reef systems and a UNESCO World Heritage Site. "
                "Strict protection since 1988 has resulted in exceptional coral health. Accessible "
                "only by liveaboard during the March-June season, limiting human impact."},
    {"name": "Aldabra Atoll", "lat": -9.4167, "lon": 46.3333,
     "country": "Seychelles", "area_km2": 15500, "status": "Well Protected",
     "reef_type": "Atoll Reef",
     "highlights": "Giant tortoises, pristine reefs, manta rays, dugongs, green turtles",
     "details": "One of the most remote and pristine atolls on Earth. UNESCO World Heritage Site "
                "home to 100,000 giant Aldabra tortoises. The lagoon covers 224 km2 and the reef "
                "system has remained largely untouched by human development."},
    {"name": "Apo Reef", "lat": 12.6667, "lon": 120.4500,
     "country": "Philippines", "area_km2": 34, "status": "Protected",
     "reef_type": "Atoll-like Reef",
     "highlights": "Second largest contiguous reef in the Philippines, sharks, manta rays",
     "details": "Triangular-shaped atoll-like reef in the Mindoro Strait. The second largest "
                "contiguous reef in the Philippines after Tubbataha. A Natural Park with diverse "
                "coral and pelagic life including white-tip and black-tip reef sharks."},
    {"name": "Ningaloo Reef", "lat": -22.6000, "lon": 113.6667,
     "country": "Australia", "area_km2": 5000, "status": "UNESCO Protected",
     "reef_type": "Fringing Reef",
     "highlights": "Whale shark aggregations (Mar-Jul), manta rays, humpback whales, turtle nesting",
     "details": "Australia's other great reef -- a 300 km fringing reef on Western Australia's "
                "coast. UNESCO World Heritage Site. The world's best whale shark aggregation site "
                "with predictable encounters from March to July. Accessible directly from shore."},
    {"name": "Wakatobi Reefs", "lat": -5.4000, "lon": 123.7500,
     "country": "Indonesia", "area_km2": 13900, "status": "National Park",
     "reef_type": "Fringing & Barrier Reefs",
     "highlights": "750+ coral species, 942 fish species, pristine house reef diving",
     "details": "Wakatobi (Wangi-Wangi, Kaledupa, Tomia, Binongko) is one of the most species-rich "
                "reef systems in the Coral Triangle. Some of the highest coral species counts ever "
                "recorded in a single dive. Excellent macro diving with pygmy seahorses."},
    {"name": "Maldives Atolls", "lat": 3.2028, "lon": 73.2207,
     "country": "Maldives", "area_km2": 21000, "status": "Threatened",
     "reef_type": "Atoll Reefs",
     "highlights": "26 atolls, 1,190 islands, manta rays, whale sharks, bioluminescent beaches",
     "details": "A chain of 26 atolls in the Indian Ocean, each a ring of coral reef enclosing "
                "a lagoon. The lowest country on Earth (average 1.5 m above sea level) faces "
                "existential threat from sea level rise. Despite bleaching events, recovery has "
                "been documented in well-managed areas."},
]

UNDERWATER_CAVES = [
    {"name": "Sistema Sac Actun", "lat": 20.2460, "lon": -87.4660,
     "country": "Mexico", "type": "Cenote Cave System",
     "length_km": 376, "depth_m": 119,
     "highlights": "Longest underwater cave system on Earth, Mayan artifacts, fossils",
     "details": "The world's longest underwater cave system at 376+ km of surveyed passages. "
                "Formed in Yucatan limestone, connecting hundreds of cenotes. Contains human "
                "remains dating back 13,000 years and Pleistocene megafauna fossils."},
    {"name": "Sistema Ox Bel Ha", "lat": 20.2133, "lon": -87.4194,
     "country": "Mexico", "type": "Cenote Cave System",
     "length_km": 270, "depth_m": 55,
     "highlights": "Second longest underwater cave, halocline layers, pristine formations",
     "details": "The world's second longest underwater cave system. Ox Bel Ha means 'Three Paths "
                "of Water' in Mayan. Features spectacular halocline effects where fresh and salt "
                "water meet, creating visual distortions like an underwater river."},
    {"name": "Great Blue Hole", "lat": 17.3155, "lon": -87.5347,
     "country": "Belize", "type": "Blue Hole",
     "length_km": 0.3, "depth_m": 124,
     "highlights": "Giant stalactites, sharks, 300 m diameter vertical cave",
     "details": "A giant marine sinkhole 300 m across and 124 m deep. Massive stalactites at "
                "40 m depth prove this was a dry cave during the Ice Age. Below 90 m the water "
                "becomes anoxic with a hydrogen sulfide layer."},
    {"name": "Dean's Blue Hole", "lat": 23.1083, "lon": -75.0261,
     "country": "Bahamas", "type": "Blue Hole",
     "length_km": 0.035, "depth_m": 202,
     "highlights": "Deepest known blue hole, freediving competitions, vertical walls",
     "details": "The world's deepest known blue hole at 202 m. Located on Long Island, Bahamas. "
                "Site of the annual Vertical Blue freediving competition where world records are "
                "regularly set. The circular opening is 25-35 m in diameter."},
    {"name": "Cenote Angelita", "lat": 20.2847, "lon": -87.3975,
     "country": "Mexico", "type": "Cenote",
     "length_km": 0.06, "depth_m": 60,
     "highlights": "Underwater river, hydrogen sulfide cloud, surreal landscapes",
     "details": "Famous for its 'underwater river' -- a dense hydrogen sulfide cloud at 30 m "
                "depth that resembles a flowing river with trees. The eerie layer separates "
                "fresh water above from salt water below, creating otherworldly diving."},
    {"name": "Orda Cave", "lat": 56.8833, "lon": 56.8167,
     "country": "Russia", "type": "Gypsum Cave",
     "length_km": 4.6, "depth_m": 22,
     "highlights": "Longest underwater cave in Russia, crystal-clear gypsum, white passages",
     "details": "The longest underwater cave in Russia and the largest underwater gypsum cave "
                "in the world. White gypsum walls create an ethereal moonscape. Water temperature "
                "is 4-5 degrees C year-round with visibility up to 46 m."},
    {"name": "Nullarbor Caves", "lat": -31.7500, "lon": 129.0000,
     "country": "Australia", "type": "Limestone Cave System",
     "length_km": 6.5, "depth_m": 100,
     "highlights": "Cocklebiddy Cave, Pannikin Plains, deep lake chambers",
     "details": "Beneath the Nullarbor Plain lies one of the largest underwater cave systems "
                "in the Southern Hemisphere. Cocklebiddy Cave contains the longest underwater "
                "cave passage in Australia at 6.4 km. Extremely remote and challenging access."},
    {"name": "Caves of Kilsby Sinkhole", "lat": -37.0500, "lon": 140.5500,
     "country": "Australia", "type": "Sinkhole",
     "length_km": 0.1, "depth_m": 40,
     "highlights": "Crystal-clear water, limestone formations, freshwater diving",
     "details": "A stunning sinkhole in South Australia's limestone coast with exceptional "
                "visibility. The water is so clear it creates an illusion of floating in air. "
                "The sinkhole opens into a wide underwater chamber with dramatic light beams."},
    {"name": "Cenote Dos Ojos", "lat": 20.3253, "lon": -87.3881,
     "country": "Mexico", "type": "Cenote Cave System",
     "length_km": 82, "depth_m": 119,
     "highlights": "Two connected sinkholes, The Pit (120 m deep), Barbie Line passage",
     "details": "Connected to Sistema Sac Actun, Dos Ojos ('Two Eyes') features two main "
                "entrances leading to a vast cave network. 'The Pit' is a 119 m deep cenote "
                "within the system. Crystal-clear visibility often exceeds 60 m."},
    {"name": "Tulum Cenotes (Gran Cenote)", "lat": 20.2453, "lon": -87.4661,
     "country": "Mexico", "type": "Cenote",
     "length_km": 1.5, "depth_m": 15,
     "highlights": "Stalactites, turtles, cavern zone light effects, easy access",
     "details": "One of the most accessible and photogenic cenotes near Tulum. A semicircular "
                "pool opens into a cavern with spectacular stalactite formations and light beams. "
                "Sea turtles and fish inhabit the crystal-clear freshwater."},
    {"name": "Pozzo del Merro", "lat": 42.1167, "lon": 12.7167,
     "country": "Italy", "type": "Sinkhole",
     "length_km": 0.01, "depth_m": 392,
     "highlights": "Deepest known sinkhole in the world, still not fully explored",
     "details": "The deepest known water-filled sinkhole in the world at 392 m. Located near "
                "Rome, its full depth remains unknown. An ROV explored to 392 m in 2002 without "
                "finding the bottom, suggesting it may be even deeper."},
    {"name": "Weeki Wachee Spring", "lat": 28.5167, "lon": -82.5722,
     "country": "USA (Florida)", "type": "Spring Cave",
     "length_km": 1.2, "depth_m": 76,
     "highlights": "First magnitude spring, underwater theater, mermaid shows since 1947",
     "details": "One of Florida's deepest and most voluminous springs, pumping 643 million "
                "liters per day. Home to the famous Weeki Wachee Mermaids underwater theater "
                "since 1947. The spring cave extends to at least 76 m depth."},
]

HYDROTHERMAL_VENTS = [
    {"name": "East Pacific Rise - 9N", "lat": 9.8333, "lon": -104.2917,
     "ocean": "Pacific", "depth_m": 2500, "vent_type": "Black Smoker",
     "temperature_c": 380, "discovery_year": 1991,
     "highlights": "Tube worm colonies, chimney towers, rapid regrowth after eruptions",
     "details": "One of the most studied vent fields on Earth. In 1991 an eruption destroyed "
                "the vent community; researchers documented complete recolonization within years. "
                "Giant tube worms (Riftia pachyptila) grow up to 2 m long here."},
    {"name": "Galapagos Rift Vents", "lat": 0.7930, "lon": -86.1340,
     "ocean": "Pacific", "depth_m": 2450, "vent_type": "White Smoker",
     "temperature_c": 350, "discovery_year": 1977,
     "highlights": "First hydrothermal vents ever discovered, chemosynthetic ecosystem",
     "details": "The 1977 discovery of these vents by the Alvin submersible revolutionized "
                "biology. Scientists found thriving ecosystems sustained by chemosynthesis, "
                "not photosynthesis. Giant clams, tube worms, and blind shrimp in total darkness."},
    {"name": "Lost City", "lat": 30.1250, "lon": -42.1167,
     "ocean": "Atlantic", "depth_m": 750, "vent_type": "Alkaline Vent",
     "temperature_c": 90, "discovery_year": 2000,
     "highlights": "Carbonate chimneys 60 m tall, possible origin-of-life conditions",
     "details": "Unlike typical black smokers, Lost City produces alkaline fluids (pH 9-11) "
                "at relatively low temperatures. Towering white carbonate chimneys up to 60 m "
                "tall (the tallest known). A leading candidate for the origin of life on Earth."},
    {"name": "Mid-Atlantic Ridge - TAG", "lat": 26.1370, "lon": -44.8260,
     "ocean": "Atlantic", "depth_m": 3650, "vent_type": "Black Smoker",
     "temperature_c": 360, "discovery_year": 1985,
     "highlights": "Trans-Atlantic Geotraverse, massive sulfide deposits, shrimp swarms",
     "details": "The Trans-Atlantic Geotraverse (TAG) is one of the largest known seafloor "
                "massive sulfide deposits. The active mound is 200 m in diameter and 50 m tall. "
                "Dense swarms of vent shrimp (Rimicaris exoculata) carpet the chimneys."},
    {"name": "Kairei Vent Field", "lat": -25.3167, "lon": 70.0333,
     "ocean": "Indian", "depth_m": 2415, "vent_type": "Black Smoker",
     "temperature_c": 360, "discovery_year": 2000,
     "highlights": "First Indian Ocean vents discovered, unique fauna, scaly-foot snail",
     "details": "Located on the Central Indian Ridge, these were the first hydrothermal vents "
                "discovered in the Indian Ocean. Home to the scaly-foot snail (Chrysomallon "
                "squamiferum) which builds its shell from iron sulfide -- the only animal known "
                "to incorporate metal into its skeleton."},
    {"name": "Loki's Castle", "lat": 73.5667, "lon": 8.1667,
     "ocean": "Arctic", "depth_m": 2352, "vent_type": "Black Smoker",
     "temperature_c": 320, "discovery_year": 2008,
     "highlights": "Northernmost known vents, unique Arctic vent fauna",
     "details": "The northernmost black smoker vents known, located on the Mid-Atlantic Ridge "
                "between Norway and Greenland. Named after the Norse god of mischief. Home to "
                "unique organisms including a new genus of snail and vent-endemic polychaetes."},
    {"name": "Longqi (Dragon Flag)", "lat": -37.7833, "lon": 49.6500,
     "ocean": "Indian", "depth_m": 2800, "vent_type": "Black Smoker",
     "temperature_c": 370, "discovery_year": 2007,
     "highlights": "Commercially valuable sulfide deposits, scaly-foot snail habitat",
     "details": "Discovered on the Southwest Indian Ridge, Longqi hosts commercially significant "
                "polymetallic sulfide deposits. China has been granted exploration rights. The "
                "vent field is also habitat for the endangered scaly-foot snail."},
    {"name": "Brothers Volcano Vents", "lat": -34.8750, "lon": -179.0750,
     "ocean": "Pacific", "depth_m": 1580, "vent_type": "Volcanic Vent",
     "temperature_c": 300, "discovery_year": 1998,
     "highlights": "Submarine volcanic caldera, acid vents, unique chemistries",
     "details": "Hydrothermal vents within an active submarine volcanic caldera in the Kermadec "
                "Arc. Features both high-temperature black smokers and low-pH acid-sulfate vents. "
                "Research has revealed distinct biological communities on different sides of the caldera."},
    {"name": "Guaymas Basin", "lat": 27.0167, "lon": -111.4083,
     "ocean": "Pacific (Gulf of California)", "depth_m": 2000,
     "vent_type": "Sediment-Hosted Vent", "temperature_c": 315, "discovery_year": 1980,
     "highlights": "Oil-rich sediment vents, Beggiatoa mats, unique chemistry",
     "details": "Unique vent system where hot fluids percolate through 400 m of organic-rich "
                "sediment, creating petroleum-like compounds. Massive white Beggiatoa bacterial "
                "mats carpet the seafloor. A natural laboratory for studying oil formation."},
    {"name": "Champagne Vent (NW Eifuku)", "lat": 21.4889, "lon": 144.0439,
     "ocean": "Pacific", "depth_m": 1604, "vent_type": "CO2 Vent",
     "temperature_c": 103, "discovery_year": 2004,
     "highlights": "Liquid CO2 bubbles, acidic environment, extremophile life",
     "details": "Named for the streams of liquid CO2 droplets that rise like champagne bubbles. "
                "One of the few places on Earth where liquid CO2 has been observed on the seafloor. "
                "The extremely acidic environment (pH as low as 1.6) supports extremophile microbes."},
    {"name": "Snake Pit", "lat": 23.3667, "lon": -44.9500,
     "ocean": "Atlantic", "depth_m": 3460, "vent_type": "Black Smoker",
     "temperature_c": 350, "discovery_year": 1985,
     "highlights": "Dense vent shrimp populations, tall chimneys, massive sulfide deposits",
     "details": "Named for the sinuous, snake-like tubeworms found here. One of the major "
                "vent sites on the Mid-Atlantic Ridge. Dense swarms of Rimicaris shrimp "
                "cluster around superheated fluid outflows. Active copper and gold-rich deposits."},
]

SUBMARINE_VOLCANOES = [
    {"name": "Kavachi", "lat": -8.9910, "lon": 157.9720,
     "country": "Solomon Islands", "depth_m": 20, "status": "Very Active",
     "last_eruption": "2022",
     "highlights": "Sharks living in volcanic crater, frequent eruptions breach surface",
     "details": "One of the most active submarine volcanoes in the Pacific. Nicknamed 'Sharkano' "
                "after researchers discovered hammerhead and silky sharks living inside its active "
                "volcanic crater. Erupts frequently enough to occasionally form temporary islands."},
    {"name": "Axial Seamount", "lat": 45.9500, "lon": -130.0167,
     "ocean": "Pacific (Juan de Fuca)", "depth_m": 1410, "status": "Active",
     "last_eruption": "2015",
     "highlights": "Cabled observatory, most studied submarine volcano, eruption prediction",
     "details": "The most intensively studied submarine volcano on Earth, connected to shore by "
                "the Ocean Observatories Initiative cable. Scientists successfully predicted its "
                "2015 eruption -- the first submarine eruption forecast. Rich hydrothermal vent communities."},
    {"name": "Monowai Seamount", "lat": -25.8870, "lon": -177.1880,
     "ocean": "Pacific (Kermadec)", "depth_m": 100, "status": "Very Active",
     "last_eruption": "2023",
     "highlights": "One of the most active submarine volcanoes, rapid growth and collapse",
     "details": "In 2011, scientists documented the summit collapsing by 18.8 m in a single day "
                "then rebuilding. One of the most active submarine volcanoes in the world, erupting "
                "almost continuously. Located in the Kermadec volcanic arc."},
    {"name": "Havre Seamount", "lat": -31.1000, "lon": -179.0333,
     "ocean": "Pacific (Kermadec)", "depth_m": 650, "status": "Recently Active",
     "last_eruption": "2012",
     "highlights": "Largest deep-ocean eruption ever recorded, pumice raft visible from space",
     "details": "Produced the largest deep-ocean silicic eruption ever documented in 2012. "
                "Generated a pumice raft 400 km long visible from space. Giant lava flows and "
                "a 240 m tall lava dome were discovered on the summit by ROV exploration."},
    {"name": "Kick 'em Jenny", "lat": 12.3000, "lon": -61.6333,
     "ocean": "Caribbean", "depth_m": 185, "status": "Active",
     "last_eruption": "2017",
     "highlights": "Most active submarine volcano in the Caribbean, exclusion zone enforced",
     "details": "The most active submarine volcano in the Lesser Antilles, with 14 confirmed "
                "eruptions since 1939. A 5 km exclusion zone is enforced around the summit. "
                "Could potentially generate a tsunami if a major flank collapse occurred."},
    {"name": "Marsili Seamount", "lat": 39.2500, "lon": 14.3667,
     "ocean": "Tyrrhenian Sea", "depth_m": 450, "status": "Potentially Active",
     "last_eruption": "Unknown (recent hydrothermal activity)",
     "highlights": "Largest European submarine volcano, potential tsunami risk to Italy",
     "details": "Europe's largest submarine volcano, 70 km long and 30 km wide, rising 3,000 m "
                "from the seafloor. Located just 150 km from Naples. Concerns about potential "
                "flank collapse generating a tsunami affecting the Italian coastline."},
    {"name": "Hunga Tonga-Hunga Ha'apai", "lat": -20.5450, "lon": -175.3900,
     "ocean": "Pacific", "depth_m": 0, "status": "Very Active",
     "last_eruption": "2022",
     "highlights": "Massive 2022 eruption, atmospheric shockwave circled Earth multiple times",
     "details": "The January 2022 eruption was the most powerful volcanic explosion in the "
                "satellite era. The plume reached 57 km altitude, the pressure wave circled Earth "
                "4+ times, and it generated tsunamis across the Pacific. Previously submarine, "
                "the 2014-15 eruption had created a new island connecting two older remnants."},
    {"name": "West Mata", "lat": -15.1000, "lon": -173.7500,
     "ocean": "Pacific", "depth_m": 1174, "status": "Active",
     "last_eruption": "2009",
     "highlights": "First deep-ocean eruption filmed in real-time, Brimstone Pit lava lake",
     "details": "In 2009, ROV Jason captured the first-ever video of a deep-ocean volcanic eruption "
                "in progress. Molten lava, explosive bursts, and a lava lake named Brimstone Pit "
                "were observed at 1,174 m depth. A landmark moment in ocean science."},
    {"name": "NW Rota-1", "lat": 14.6000, "lon": 144.7750,
     "ocean": "Pacific (Mariana Arc)", "depth_m": 517, "status": "Active",
     "last_eruption": "2010",
     "highlights": "Continuous eruption observed, 'Brimstone Pit' vent, shrimp in volcanic plume",
     "details": "An actively erupting submarine volcano in the Mariana Arc. Scientists observed "
                "continuous Strombolian eruptions from the 'Brimstone Pit' vent. Remarkably, "
                "swarms of volcanic vent shrimp were found thriving in the acidic volcanic plume."},
    {"name": "Loihi Seamount", "lat": 18.9200, "lon": -155.2700,
     "ocean": "Pacific", "depth_m": 969, "status": "Active",
     "last_eruption": "1996",
     "highlights": "Future Hawaiian island, Pele's Pit collapse crater, active hydrothermal vents",
     "details": "The newest volcano in the Hawaiian chain, rising 3,000 m from the seafloor. "
                "In approximately 10,000-100,000 years, Loihi will breach the surface to become "
                "Hawaii's newest island. A 1996 earthquake swarm collapsed the summit into "
                "'Pele's Pit,' a 300 m deep crater."},
    {"name": "Kolumbo", "lat": 36.5117, "lon": 25.4917,
     "ocean": "Aegean Sea", "depth_m": 18, "status": "Active",
     "last_eruption": "1650 (submarine)",
     "highlights": "Near Santorini, active CO2 vents, gold-rich deposits, tsunami risk",
     "details": "A submarine volcano just 7 km NE of Santorini. Its 1650 eruption generated a "
                "tsunami and toxic gas that killed 70 people on Santorini. Active hydrothermal "
                "vents on the crater floor deposit gold and silver. Closely monitored for "
                "future eruption potential."},
]

KELP_FORESTS = [
    {"name": "California Kelp Forests", "lat": 33.4500, "lon": -118.5000,
     "country": "USA", "type": "Giant Kelp",
     "area_km2": 320, "species": "Macrocystis pyrifera",
     "highlights": "Sea otters, garibaldi fish, horn sharks, giant sea bass",
     "details": "The iconic giant kelp forests of California can grow up to 60 cm per day, "
                "reaching heights of 45 m. Sea otters are keystone species -- without them, "
                "sea urchins devastate kelp. The forests support over 800 species and are vital "
                "nurseries for commercially important fish."},
    {"name": "South African Kelp Forest", "lat": -34.3500, "lon": 18.4700,
     "country": "South Africa", "type": "Sea Bamboo Kelp",
     "area_km2": 400, "species": "Ecklonia maxima",
     "highlights": "Cape fur seals, broadnose sevengill sharks, My Octopus Teacher filming location",
     "details": "The Great African Sea Forest extends along the Cape coast. Made famous by the "
                "documentary 'My Octopus Teacher.' These cold-water kelp forests support unique "
                "biodiversity including broadnose sevengill sharks and pajama catsharks."},
    {"name": "Patagonian Kelp Forests", "lat": -53.0000, "lon": -70.0000,
     "country": "Argentina/Chile", "type": "Giant Kelp",
     "area_km2": 600, "species": "Macrocystis pyrifera",
     "highlights": "Sea lions, penguins, kelp geese, pristine cold-water ecosystems",
     "details": "Some of the most pristine kelp forests remaining on Earth. The cold, nutrient-rich "
                "waters of Tierra del Fuego support dense kelp canopies that shelter Magellanic "
                "penguins, sea lions, and diverse invertebrate communities."},
    {"name": "Norwegian Kelp Forests", "lat": 65.0000, "lon": 12.0000,
     "country": "Norway", "type": "Laminaria Kelp",
     "area_km2": 5500, "species": "Laminaria hyperborea",
     "highlights": "Europe's largest kelp forests, sea urchin barrens recovery, cod nursery",
     "details": "Norway's coastline hosts Europe's most extensive kelp forests. Decades of sea "
                "urchin overgrazing created vast 'urchin barrens,' but recent warming has helped "
                "kelp recover in northern areas. These forests are critical nurseries for Atlantic "
                "cod and other commercial fish species."},
    {"name": "Tasmanian Giant Kelp", "lat": -43.0000, "lon": 147.0000,
     "country": "Australia", "type": "Giant Kelp",
     "area_km2": 50, "species": "Macrocystis pyrifera",
     "highlights": "Critically declining, weedy seadragon, handfish, climate change indicator",
     "details": "Tasmania's giant kelp forests have declined by over 95% since the 1940s due to "
                "warming East Australian Current extension. Now listed as a critically endangered "
                "ecological community. Home to the endemic spotted handfish."},
    {"name": "Posidonia Meadows (Mediterranean)", "lat": 38.9000, "lon": 1.4000,
     "country": "Spain (Ibiza/Formentera)", "type": "Seagrass",
     "area_km2": 76, "species": "Posidonia oceanica",
     "highlights": "UNESCO World Heritage, 100,000-year-old clonal organism, crystal-clear water",
     "details": "Posidonia oceanica seagrass meadows are the foundation of Mediterranean marine "
                "ecosystems. The meadow between Ibiza and Formentera is UNESCO-listed and contains "
                "organisms estimated at 100,000 years old. Seagrass captures carbon 15x faster "
                "than tropical forests per hectare."},
    {"name": "Shark Bay Seagrass", "lat": -25.5000, "lon": 113.5000,
     "country": "Australia", "type": "Seagrass",
     "area_km2": 4800, "species": "Amphibolis antarctica / Posidonia australis",
     "highlights": "Largest seagrass meadow on Earth, dugongs, dolphins, sea turtles, stromatolites",
     "details": "The world's largest seagrass ecosystem. UNESCO World Heritage Site supporting "
                "10% of the world's dugong population (about 10,000). A 2022 study found a single "
                "seagrass clone spanning 180 km -- the largest known plant on Earth at 4,500 years old."},
    {"name": "Florida Seagrass", "lat": 24.7000, "lon": -81.0000,
     "country": "USA (Florida)", "type": "Seagrass",
     "area_km2": 11000, "species": "Thalassia testudinum (turtle grass)",
     "highlights": "Manatees, green sea turtles, sport fish nursery, Florida Bay ecosystem",
     "details": "Florida contains the most extensive seagrass beds in the continental US. "
                "These meadows are critical habitat for the endangered Florida manatee and serve "
                "as nurseries for economically important species like snapper, grouper, and lobster. "
                "Indian River Lagoon suffered massive seagrass die-off from algal blooms."},
    {"name": "Alaskan Kelp Forests", "lat": 57.0000, "lon": -135.5000,
     "country": "USA (Alaska)", "type": "Bull Kelp",
     "area_km2": 500, "species": "Nereocystis luetkeana",
     "highlights": "Sea otters, Steller sea lions, kelp highway hypothesis, marine carbon sink",
     "details": "Alaska's cold, nutrient-rich waters support extensive bull kelp forests. The "
                "'kelp highway hypothesis' suggests early humans migrated from Asia to the Americas "
                "along a coastal kelp forest corridor. These forests are expanding as sea otters "
                "return to control urchin populations."},
    {"name": "Great Southern Reef (Australia)", "lat": -35.0000, "lon": 137.0000,
     "country": "Australia", "type": "Mixed Kelp",
     "area_km2": 71000, "species": "Ecklonia radiata (common kelp)",
     "highlights": "Newly recognized reef system, 30% endemic species, temperate biodiversity hotspot",
     "details": "Spanning 8,000 km along southern Australia's coastline, the Great Southern Reef "
                "was formally recognized as a significant reef system in 2016. Contains over 30% "
                "endemic species found nowhere else. Produces more kelp biomass than anywhere "
                "else in the Southern Hemisphere."},
]

DEEP_SEA_FEATURES = [
    {"name": "Mid-Atlantic Ridge", "lat": 28.0000, "lon": -30.0000,
     "ocean": "Atlantic", "type": "Mid-Ocean Ridge",
     "length_km": 16000, "depth_m": 2500,
     "highlights": "Longest mountain range on Earth, tectonic plate boundary, Iceland sits atop it",
     "details": "The longest mountain range on Earth at 16,000 km, running from the Arctic to "
                "the Antarctic. Marks the boundary where the American plates diverge from the "
                "Eurasian and African plates. Iceland is the most prominent above-water section. "
                "The ridge produces new oceanic crust at 2.5 cm per year."},
    {"name": "East Pacific Rise", "lat": 0.0000, "lon": -104.0000,
     "ocean": "Pacific", "type": "Mid-Ocean Ridge",
     "length_km": 9000, "depth_m": 2000,
     "highlights": "Fastest spreading ridge, hydrothermal vents, new crust formation",
     "details": "The fastest spreading mid-ocean ridge on Earth, producing new crust at up to "
                "15 cm per year. Site of some of the most spectacular hydrothermal vent fields. "
                "The rapid spreading creates a smoother ridge profile than the Mid-Atlantic Ridge."},
    {"name": "Abyssal Plain - Sohm", "lat": 32.0000, "lon": -60.0000,
     "ocean": "Atlantic", "type": "Abyssal Plain",
     "length_km": 900, "depth_m": 5400,
     "highlights": "One of the flattest surfaces on Earth, marine snow, abyssal life",
     "details": "Abyssal plains are the flattest areas on Earth's surface, covered in fine "
                "sediment from 'marine snow' -- a constant drizzle of organic particles from above. "
                "The Sohm Plain covers 900,000 km2 in the western Atlantic. Despite appearing "
                "barren, the plains support unique communities of brittle stars and sea cucumbers."},
    {"name": "Monterey Canyon", "lat": 36.7900, "lon": -121.9000,
     "ocean": "Pacific", "type": "Submarine Canyon",
     "length_km": 153, "depth_m": 3600,
     "highlights": "Deeper than Grand Canyon, MBARI research, deep-sea species discoveries",
     "details": "One of the largest submarine canyons on Earth, comparable in size to the Grand "
                "Canyon. Extends 153 km from Moss Landing to the abyssal plain at 3,600 m depth. "
                "Home to MBARI (Monterey Bay Aquarium Research Institute), which has used ROVs to "
                "discover hundreds of new deep-sea species."},
    {"name": "Romanche Fracture Zone", "lat": -0.2500, "lon": -18.5000,
     "ocean": "Atlantic", "type": "Fracture Zone",
     "length_km": 300, "depth_m": 7758,
     "highlights": "Deepest point in the Atlantic seabed, connects deep ocean basins",
     "details": "A transform fault offsetting the Mid-Atlantic Ridge near the equator. Contains "
                "the Romanche Trench at 7,758 m -- the deepest point in the Atlantic seabed. "
                "Acts as a gateway for deep Antarctic Bottom Water to flow between ocean basins."},
    {"name": "Challenger Plateau", "lat": -40.0000, "lon": 170.0000,
     "ocean": "Pacific", "type": "Submarine Plateau",
     "length_km": 800, "depth_m": 1000,
     "highlights": "Zealandia fragment, continental crust remnant, unique deep-sea fauna",
     "details": "Part of the submerged continent Zealandia (which sank about 23 million years "
                "ago). The plateau is a shallow submarine feature of continental crust. In 2017, "
                "Zealandia was recognized as Earth's eighth continent -- 94% of it is underwater."},
    {"name": "Hawaiian-Emperor Seamount Chain", "lat": 32.0000, "lon": -172.0000,
     "ocean": "Pacific", "type": "Seamount Chain",
     "length_km": 6000, "depth_m": 1000,
     "highlights": "Hotspot track, guyots (flat-topped seamounts), 80+ million year record",
     "details": "A chain of over 80 submarine volcanoes and seamounts stretching 6,000 km across "
                "the Pacific. Records 80+ million years of Pacific Plate movement over the Hawaii "
                "hotspot. Many older seamounts have flat tops (guyots) from wave erosion when they "
                "were islands, before subsiding below sea level."},
    {"name": "Charlie-Gibbs Fracture Zone", "lat": 52.5000, "lon": -31.0000,
     "ocean": "Atlantic", "type": "Fracture Zone",
     "length_km": 2000, "depth_m": 4500,
     "highlights": "Major oceanographic boundary, deep-water crossover, biodiversity hotspot",
     "details": "A major transform fault in the North Atlantic that offsets the Mid-Atlantic Ridge "
                "by 350 km. Acts as a critical oceanographic boundary separating cold northern and "
                "warmer southern deep waters. The fracture zone supports distinct biological "
                "communities on either side of the boundary."},
    {"name": "Congo Submarine Canyon", "lat": -6.0667, "lon": 12.2000,
     "ocean": "Atlantic", "type": "Submarine Canyon",
     "length_km": 760, "depth_m": 1200,
     "highlights": "Longest submarine canyon in the world, powerful turbidity currents, cable breaks",
     "details": "The world's longest submarine canyon at 760 km, extending from the Congo River "
                "mouth into the deep Atlantic. Generates some of the most powerful turbidity "
                "currents on Earth -- underwater avalanches of sediment traveling at 8 m/s that "
                "have snapped undersea telecommunications cables."},
    {"name": "Zealandia (Te Riu-a-Maui)", "lat": -42.0000, "lon": 173.0000,
     "ocean": "Pacific", "type": "Submerged Continent",
     "length_km": 4900, "depth_m": 1100,
     "highlights": "Earth's 8th continent, 94% submerged, 4.9 million km2",
     "details": "Recognized as Earth's eighth continent in 2017. At 4.9 million km2, it is the "
                "world's smallest continent but 94% is submerged. Only New Zealand and New "
                "Caledonia remain above water. Zealandia rifted from Antarctica and Australia "
                "60-85 million years ago and gradually sank."},
    {"name": "Mariana Forearc (Serpentinite Mud Volcanoes)", "lat": 18.1000, "lon": 147.0000,
     "ocean": "Pacific", "type": "Mud Volcano Field",
     "length_km": 100, "depth_m": 1500,
     "highlights": "Largest mud volcanoes on Earth, serpentinite flows, deep-Earth fluid samples",
     "details": "A field of enormous serpentinite mud volcanoes on the Mariana forearc. The largest, "
                "South Chamorro Seamount, rises 2 km from the seafloor and is 30 km wide. These "
                "volcanoes bring up material and fluids from the subducting Pacific Plate, providing "
                "windows into processes 30+ km below the seafloor."},
]

MARINE_PROTECTED_AREAS = [
    {"name": "Papahanaumokuakea", "lat": 25.0000, "lon": -170.0000,
     "country": "USA (Hawaii)", "area_km2": 1510000,
     "designation": "Marine National Monument",
     "established": 2006, "status": "Fully Protected",
     "highlights": "One of the largest MPAs on Earth, Hawaiian monk seals, laysan albatross",
     "details": "One of the largest fully protected conservation areas on Earth. Encompasses "
                "the remote Northwestern Hawaiian Islands with 1.5 million km2 of ocean. "
                "A UNESCO World Heritage Site protecting over 7,000 marine species, including "
                "the critically endangered Hawaiian monk seal."},
    {"name": "Ross Sea Marine Protected Area", "lat": -72.0000, "lon": 177.0000,
     "country": "International (Antarctica)", "area_km2": 1550000,
     "designation": "Marine Protected Area",
     "established": 2016, "status": "Mixed (72% no-take)",
     "highlights": "Last pristine ocean, Adelie penguins, Weddell seals, Antarctic toothfish",
     "details": "The world's largest marine protected area at 1.55 million km2. Often called "
                "the 'Last Ocean' because it remains the most pristine marine ecosystem on Earth. "
                "Agreed by 24 nations and the EU through CCAMLR in 2016."},
    {"name": "British Indian Ocean Territory MPA", "lat": -6.0000, "lon": 71.5000,
     "country": "UK (Chagos Archipelago)", "area_km2": 640000,
     "designation": "Marine Protected Area",
     "established": 2010, "status": "No-Take (contested)",
     "highlights": "Cleanest ocean water measured, pristine coral reefs, mega-fauna haven",
     "details": "The world's largest no-take marine reserve at 640,000 km2 around the Chagos "
                "Archipelago. Contains some of the healthiest and most diverse coral reefs in "
                "the Indian Ocean. Sovereignty is contested between the UK and Mauritius."},
    {"name": "Great Barrier Reef Marine Park", "lat": -18.2871, "lon": 147.6992,
     "country": "Australia", "area_km2": 344400,
     "designation": "Marine Park",
     "established": 1975, "status": "Zoned (33% no-take)",
     "highlights": "Largest coral reef system, 2,900 reefs, 900 islands, 1,500 fish species",
     "details": "Established in 1975 to protect the world's largest coral reef system. A landmark "
                "2004 rezoning increased no-take zones from 4.5% to 33%, resulting in measurable "
                "increases in fish size and abundance. Faces ongoing threats from climate change."},
    {"name": "Galapagos Marine Reserve", "lat": -0.5000, "lon": -90.5000,
     "country": "Ecuador", "area_km2": 133000,
     "designation": "Marine Reserve",
     "established": 1998, "status": "Zoned Protection",
     "highlights": "Marine iguanas, hammerhead sharks, whale sharks, unique endemic species",
     "details": "Protects one of the most unique marine ecosystems on Earth where cold and warm "
                "ocean currents converge. Home to the world's only marine iguana and an extraordinary "
                "concentration of sharks. In 2022, Ecuador expanded the reserve by 60,000 km2."},
    {"name": "Phoenix Islands Protected Area", "lat": -3.8000, "lon": -171.7000,
     "country": "Kiribati", "area_km2": 408250,
     "designation": "Marine Protected Area",
     "established": 2008, "status": "Fully Protected",
     "highlights": "Remote Pacific reefs, deep seamounts, pelagic species, pristine ecosystems",
     "details": "One of the largest and deepest UNESCO World Heritage Sites. Protects eight atolls "
                "and submerged reef systems in the central Pacific. The extreme remoteness has "
                "preserved near-pristine ecosystems rarely found elsewhere."},
    {"name": "Papahanaaumokuakea / Marianas Trench MNM", "lat": 11.3493, "lon": 142.1996,
     "country": "USA (Mariana Islands)", "area_km2": 250487,
     "designation": "Marine National Monument",
     "established": 2009, "status": "Fully Protected",
     "highlights": "Deepest point on Earth, unique hadal life, submarine volcanoes",
     "details": "Protects the waters around the Mariana Trench, the Mariana volcanic arc, and "
                "surrounding seamounts. Includes the deepest point on Earth (Challenger Deep) "
                "and unique chemosynthetic communities. Established by President George W. Bush."},
    {"name": "Coral Sea Marine Park", "lat": -18.0000, "lon": 155.0000,
     "country": "Australia", "area_km2": 989842,
     "designation": "Marine Park",
     "established": 2012, "status": "Zoned Protection",
     "highlights": "Pristine coral reefs, pelagic sharks, sea turtles, deep-sea features",
     "details": "One of the world's largest marine parks, extending east from the Great Barrier "
                "Reef into the Coral Sea. Protects important coral reef systems, seamounts, and "
                "deep-sea habitats. Includes Osprey Reef, famous for its shark diving."},
    {"name": "Pitcairn Islands Marine Reserve", "lat": -24.3750, "lon": -128.3150,
     "country": "UK (Pitcairn Islands)", "area_km2": 834000,
     "designation": "Marine Protected Area",
     "established": 2016, "status": "Fully Protected",
     "highlights": "One of the most remote MPAs, pristine deep-water corals, endemic species",
     "details": "One of the largest fully protected marine reserves in the world, surrounding "
                "the remote Pitcairn Islands in the South Pacific. The islands are home to fewer "
                "than 50 people. Surveys have documented some of the deepest known healthy coral "
                "reefs at over 100 m depth."},
    {"name": "Marae Moana", "lat": -18.0000, "lon": -161.0000,
     "country": "Cook Islands", "area_km2": 1976000,
     "designation": "Marine Park",
     "established": 2017, "status": "Multi-Use Protected",
     "highlights": "Largest marine park in the world (by single nation), whales, tuna, seamounts",
     "details": "The Cook Islands' entire 1.976 million km2 exclusive economic zone was declared "
                "a marine park in 2017, making it one of the largest marine protected areas "
                "established by a single nation. Protects critical habitat for migratory species "
                "including humpback whales and tuna."},
    {"name": "Coral Triangle Initiative", "lat": -2.0000, "lon": 128.0000,
     "country": "6 nations (Indonesia, Philippines, etc.)", "area_km2": 5700000,
     "designation": "Multi-National Initiative",
     "established": 2009, "status": "Coordinated Network",
     "highlights": "76% of all coral species, 37% of reef fish species, epicenter of marine life",
     "details": "A multilateral partnership protecting the Coral Triangle -- the global epicenter "
                "of marine biodiversity spanning Indonesia, Malaysia, Philippines, Papua New Guinea, "
                "Solomon Islands, and Timor-Leste. Contains 76% of all known coral species and "
                "supports the livelihoods of 120 million coastal people."},
]

FAMOUS_DISCOVERIES = [
    {"name": "RMS Titanic", "lat": 41.7260, "lon": -49.9469,
     "country": "International Waters (Atlantic)", "year_discovered": 1985,
     "depth_m": 3800, "type": "Shipwreck",
     "discoverer": "Robert Ballard / Jean-Louis Michel",
     "highlights": "Most famous underwater discovery, 1,517 lives lost, broke in two on sinking",
     "details": "Discovered on September 1, 1985 by a joint US-French expedition using the "
                "ROV Argo's camera sled. Resting at 3,800 m in two main sections 600 m apart. "
                "Over 5,500 artifacts recovered. The wreck is deteriorating and may collapse "
                "completely by 2030 due to rust-eating bacteria."},
    {"name": "Bismarck", "lat": 48.1667, "lon": -16.2000,
     "country": "International Waters (Atlantic)", "year_discovered": 1989,
     "depth_m": 4791, "type": "Warship Wreck",
     "discoverer": "Robert Ballard",
     "highlights": "Germany's largest battleship, sank HMS Hood, scuttled after battle damage",
     "details": "Found by Robert Ballard in 1989 at 4,791 m depth using the same technology "
                "that located the Titanic. The wreck is remarkably intact, standing upright on "
                "the seabed. Analysis suggests the crew scuttled the ship rather than letting it "
                "be captured by the Royal Navy."},
    {"name": "Antikythera Mechanism Site", "lat": 35.8750, "lon": 23.3167,
     "country": "Greece", "year_discovered": 1901,
     "depth_m": 45, "type": "Ancient Wreck & Artifact",
     "discoverer": "Greek sponge divers",
     "highlights": "World's oldest analog computer (c. 100 BC), ancient Greek astronomy device",
     "details": "A Roman-era shipwreck yielded the Antikythera Mechanism -- a 2,000-year-old "
                "analog computer that predicted astronomical positions, eclipses, and Olympiad dates. "
                "Its technological sophistication was not matched for over 1,000 years. CT scanning "
                "has revealed 37 interlocking bronze gears."},
    {"name": "MUSA Underwater Museum", "lat": 21.2014, "lon": -86.7494,
     "country": "Mexico (Cancun)", "year_discovered": 2009,
     "depth_m": 8, "type": "Underwater Museum",
     "discoverer": "Jason deCaires Taylor (artist)",
     "highlights": "500+ life-size sculptures, artificial reef, art meets conservation",
     "details": "The Museo Subacuatico de Arte features over 500 permanent life-size sculptures "
                "on the seabed near Cancun and Isla Mujeres. Created by Jason deCaires Taylor to "
                "divert tourists from natural reefs and create artificial reef habitat. The "
                "sculptures are colonized by coral, sponges, and marine life."},
    {"name": "Heracleion (Thonis)", "lat": 31.3000, "lon": 30.1000,
     "country": "Egypt", "year_discovered": 2000,
     "depth_m": 10, "type": "Sunken City",
     "discoverer": "Franck Goddio",
     "highlights": "Lost Egyptian port city, massive temple ruins, 64 ancient ships",
     "details": "A legendary Egyptian city lost for over 1,000 years, discovered submerged in "
                "Abu Qir Bay. Once Egypt's main port before Alexandria was founded. Franck Goddio's "
                "team found colossal statues, 64 ancient ships, gold coins, and the intact temple "
                "of Amun-Gereb beneath the sediment."},
    {"name": "Pavlopetri", "lat": 36.5192, "lon": 22.9619,
     "country": "Greece", "year_discovered": 1967,
     "depth_m": 4, "type": "Sunken City",
     "discoverer": "Nicholas Flemming",
     "highlights": "Oldest known submerged city (5,000 years), Mycenaean-era streets and buildings",
     "details": "The oldest known submerged city in the world, dating to at least 2800 BC. "
                "Located just off the coast of southern Laconia, Greece, in only 3-4 m of water. "
                "Streets, buildings, and tombs from the Mycenaean period are clearly visible. "
                "The city sank due to tectonic subsidence around 1000 BC."},
    {"name": "Dwarka (Bet Dwarka)", "lat": 22.4600, "lon": 69.0800,
     "country": "India", "year_discovered": 2001,
     "depth_m": 12, "type": "Submerged Archaeological Site",
     "discoverer": "Marine Archaeology Centre, India",
     "highlights": "Ancient Krishna's city, submerged structures, 9,500-year-old pottery",
     "details": "Underwater ruins off the coast of Gujarat, India, believed by some to be the "
                "legendary city of Dwarka mentioned in the Mahabharata. Sonar surveys revealed "
                "geometric structures at 12 m depth. Artifacts include anchors, pottery, and "
                "construction materials dating to various periods."},
    {"name": "HMS Erebus & Terror", "lat": 68.9250, "lon": -98.9450,
     "country": "Canada (Arctic)", "year_discovered": 2014,
     "depth_m": 11, "type": "Exploration Ship Wreck",
     "discoverer": "Parks Canada / Inuit knowledge",
     "highlights": "Lost Franklin Expedition ships, Arctic mystery solved, Inuit oral history confirmed",
     "details": "Sir John Franklin's lost expedition ships, missing since 1845, were found using "
                "Inuit oral history that had been dismissed for 170 years. HMS Erebus was found in "
                "2014 and HMS Terror in 2016 in remarkably preserved condition in the frigid Arctic "
                "waters. The discoveries confirmed cannibalism and solved one of exploration's "
                "greatest mysteries."},
    {"name": "Yonaguni Monument", "lat": 24.4350, "lon": 123.0100,
     "country": "Japan", "year_discovered": 1987,
     "depth_m": 25, "type": "Submerged Formation (Debated)",
     "discoverer": "Kihachiro Aratake",
     "highlights": "Controversial terraced structure, natural or man-made debate, 10,000+ years old",
     "details": "A massive underwater terraced structure off Yonaguni Island, Japan. The formation "
                "features flat surfaces, right angles, and stepped terraces that resemble a pyramid. "
                "Debate continues whether it is a natural sandstone formation or a 10,000-year-old "
                "man-made structure from when sea levels were lower."},
    {"name": "Port Royal", "lat": 17.9342, "lon": -76.8411,
     "country": "Jamaica", "year_discovered": 1959,
     "depth_m": 12, "type": "Sunken City",
     "discoverer": "Edwin Link (systematic excavation)",
     "highlights": "The 'Wickedest City on Earth,' destroyed by 1692 earthquake, pirate haven",
     "details": "Once called 'the wickedest city on Earth,' Port Royal was a notorious pirate haven "
                "that sank into Kingston Harbour during a catastrophic earthquake on June 7, 1692. "
                "Two-thirds of the city slid underwater. Excavations have recovered thousands of "
                "artifacts from the preserved 17th-century streets."},
    {"name": "Uluburun Shipwreck", "lat": 36.1333, "lon": 29.6833,
     "country": "Turkey", "year_discovered": 1982,
     "depth_m": 52, "type": "Bronze Age Wreck",
     "discoverer": "Mehmet Cakir (sponge diver)",
     "highlights": "3,300-year-old cargo, oldest known intact ship, gold, copper, tin, amber",
     "details": "A Late Bronze Age merchant vessel from around 1300 BC, discovered by a sponge "
                "diver off southwestern Turkey. Carried 10 tons of copper ingots, 1 ton of tin, "
                "gold artifacts, ebony, ivory, and the oldest known intact book (a wooden diptych). "
                "One of the most important underwater archaeological discoveries ever made."},
    {"name": "Endurance (Shackleton's Ship)", "lat": -68.7333, "lon": -52.3833,
     "country": "International Waters (Antarctica)", "year_discovered": 2022,
     "depth_m": 3008, "type": "Exploration Ship Wreck",
     "discoverer": "Endurance22 Expedition (Mensun Bound)",
     "highlights": "Best-preserved wooden wreck ever found, 107 years under Antarctic ice",
     "details": "Ernest Shackleton's Endurance, crushed by Antarctic ice in 1915, was found in "
                "2022 at 3,008 m depth in the Weddell Sea. Described as the finest wooden shipwreck "
                "ever found -- remarkably intact with the ship's name clearly visible on the stern. "
                "Protected under the Antarctic Treaty as a Historic Site."},
]

# ═══════════════════════════════════════════════════════════════════════════════
# DATA MAPPING
# ═══════════════════════════════════════════════════════════════════════════════
_MODE_DATA = {
    "World's Best Dive Sites": BEST_DIVE_SITES,
    "Deep Ocean Trenches": DEEP_OCEAN_TRENCHES,
    "Coral Reefs": CORAL_REEFS,
    "Underwater Caves & Cenotes": UNDERWATER_CAVES,
    "Hydrothermal Vents": HYDROTHERMAL_VENTS,
    "Submarine Volcanoes": SUBMARINE_VOLCANOES,
    "Kelp Forests & Seagrass": KELP_FORESTS,
    "Deep Sea Features": DEEP_SEA_FEATURES,
    "Marine Protected Areas": MARINE_PROTECTED_AREAS,
    "Famous Underwater Discoveries": FAMOUS_DISCOVERIES,
}


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: STATS RENDERING
# ═══════════════════════════════════════════════════════════════════════════════
def _render_stats(entries: list, mode: str, color: str):
    """Render overview statistics row for the current mode."""
    n = len(entries)

    if mode == "World's Best Dive Sites":
        countries = set(e.get("country", "Unknown") for e in entries)
        avg_depth = sum(e.get("depth_m", 0) for e in entries) / max(n, 1)
        avg_vis = sum(e.get("visibility_m", 0) for e in entries) / max(n, 1)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dive Sites", n)
        c2.metric("Countries", len(countries))
        c3.metric("Avg Depth", f"{avg_depth:.0f} m")
        c4.metric("Avg Visibility", f"{avg_vis:.0f} m")

    elif mode == "Deep Ocean Trenches":
        deepest = max((e.get("depth_m", 0) for e in entries), default=0)
        total_len = sum(e.get("length_km", 0) for e in entries)
        oceans = set(e.get("ocean", "Unknown") for e in entries)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Trenches", n)
        c2.metric("Deepest", f"{deepest:,} m")
        c3.metric("Total Length", f"{total_len:,} km")
        c4.metric("Oceans", len(oceans))

    elif mode == "Coral Reefs":
        total_area = sum(e.get("area_km2", 0) for e in entries)
        protected = sum(1 for e in entries if "Protected" in e.get("status", ""))
        countries = set(e.get("country", "Unknown") for e in entries)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Reef Systems", n)
        c2.metric("Total Area", f"{total_area:,} km2")
        c3.metric("Well Protected", protected)
        c4.metric("Regions", len(countries))

    elif mode == "Underwater Caves & Cenotes":
        total_len = sum(e.get("length_km", 0) for e in entries)
        deepest = max((e.get("depth_m", 0) for e in entries), default=0)
        types = set(e.get("type", "Unknown") for e in entries)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Cave Sites", n)
        c2.metric("Total Passage", f"{total_len:,.0f} km")
        c3.metric("Deepest", f"{deepest:,} m")
        c4.metric("Types", len(types))

    elif mode == "Hydrothermal Vents":
        avg_depth = sum(e.get("depth_m", 0) for e in entries) / max(n, 1)
        hottest = max((e.get("temperature_c", 0) for e in entries), default=0)
        oceans = set(e.get("ocean", "Unknown") for e in entries)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Vent Fields", n)
        c2.metric("Avg Depth", f"{avg_depth:,.0f} m")
        c3.metric("Hottest", f"{hottest} C")
        c4.metric("Oceans", len(oceans))

    elif mode == "Submarine Volcanoes":
        active = sum(1 for e in entries if "Active" in e.get("status", ""))
        shallowest = min((e.get("depth_m", 9999) for e in entries), default=0)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Volcanoes", n)
        c2.metric("Active", active)
        c3.metric("Shallowest", f"{shallowest} m")
        c4.metric("Locations", n)

    elif mode == "Kelp Forests & Seagrass":
        total_area = sum(e.get("area_km2", 0) for e in entries)
        countries = set(e.get("country", "Unknown") for e in entries)
        types = set(e.get("type", "Unknown") for e in entries)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ecosystems", n)
        c2.metric("Total Area", f"{total_area:,} km2")
        c3.metric("Countries", len(countries))
        c4.metric("Types", len(types))

    elif mode == "Deep Sea Features":
        total_len = sum(e.get("length_km", 0) for e in entries)
        deepest = max((e.get("depth_m", 0) for e in entries), default=0)
        types = set(e.get("type", "Unknown") for e in entries)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Features", n)
        c2.metric("Total Extent", f"{total_len:,} km")
        c3.metric("Deepest", f"{deepest:,} m")
        c4.metric("Feature Types", len(types))

    elif mode == "Marine Protected Areas":
        total_area = sum(e.get("area_km2", 0) for e in entries)
        no_take = sum(1 for e in entries if "Fully" in e.get("status", ""))
        countries = set(e.get("country", "Unknown") for e in entries)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("MPAs", n)
        c2.metric("Total Area", f"{total_area:,.0f} km2")
        c3.metric("Fully Protected", no_take)
        c4.metric("Countries/Regions", len(countries))

    elif mode == "Famous Underwater Discoveries":
        avg_depth = sum(e.get("depth_m", 0) for e in entries) / max(n, 1)
        types = set(e.get("type", "Unknown") for e in entries)
        countries = set(e.get("country", "Unknown") for e in entries)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Discoveries", n)
        c2.metric("Avg Depth", f"{avg_depth:,.0f} m")
        c3.metric("Discovery Types", len(types))
        c4.metric("Locations", len(countries))

    else:
        c1, c2 = st.columns(2)
        c1.metric("Entries", n)
        c2.metric("Mode", escape(mode))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: MATPLOTLIB CHART
# ═══════════════════════════════════════════════════════════════════════════════
def _make_depth_chart(entries: list, color: str, title: str):
    """Create a horizontal bar chart of depths."""
    items = [(e.get("name", "?"), e.get("depth_m", 0)) for e in entries if e.get("depth_m")]
    if not items:
        return None
    items.sort(key=lambda x: x[1], reverse=True)
    names = [i[0] for i in items[:20]]
    depths = [i[1] for i in items[:20]]

    fig, ax = plt.subplots(figsize=(10, max(4, len(names) * 0.4)))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)
    ax.barh(range(len(names)), depths, color=color, alpha=0.8, edgecolor=color, linewidth=0.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8, color=_TEXT)
    ax.invert_yaxis()
    ax.set_xlabel("Depth (m)", color=_TEXT2, fontsize=9)
    ax.set_title(title, color=_TEXT, fontsize=11, fontweight="bold", pad=12)
    ax.tick_params(axis="x", colors=_TEXT2, labelsize=8)
    ax.tick_params(axis="y", colors=_TEXT)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    ax.grid(axis="x", alpha=0.15, color=_TEXT2)
    fig.tight_layout()
    return fig


def _make_area_chart(entries: list, color: str, title: str):
    """Create a horizontal bar chart of areas."""
    items = [(e.get("name", "?"), e.get("area_km2", 0)) for e in entries if e.get("area_km2")]
    if not items:
        return None
    items.sort(key=lambda x: x[1], reverse=True)
    names = [i[0] for i in items[:20]]
    areas = [i[1] for i in items[:20]]

    fig, ax = plt.subplots(figsize=(10, max(4, len(names) * 0.4)))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)
    ax.barh(range(len(names)), areas, color=color, alpha=0.8, edgecolor=color, linewidth=0.5)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=8, color=_TEXT)
    ax.invert_yaxis()
    ax.set_xlabel("Area (km2)", color=_TEXT2, fontsize=9)
    ax.set_title(title, color=_TEXT, fontsize=11, fontweight="bold", pad=12)
    ax.tick_params(axis="x", colors=_TEXT2, labelsize=8)
    ax.tick_params(axis="y", colors=_TEXT)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    ax.grid(axis="x", alpha=0.15, color=_TEXT2)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: BUILD FOLIUM MAP
# ═══════════════════════════════════════════════════════════════════════════════
def _build_map(entries: list, color: str, mode: str,
               center: list = None, zoom: int = 2) -> folium.Map:
    """Build a folium map with markers for all entries in this mode."""
    if center is None:
        if entries:
            avg_lat = sum(e.get("lat", 0) for e in entries) / len(entries)
            avg_lon = sum(e.get("lon", 0) for e in entries) / len(entries)
            center = [avg_lat, avg_lon]
        else:
            center = [20.0, 0.0]

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    for e in entries:
        lat = e.get("lat")
        lon = e.get("lon")
        if lat is None or lon is None:
            continue

        name = escape(str(e.get("name", "Unknown")))
        details = escape(str(e.get("details", "")))

        # Build popup content based on available fields
        popup_parts = [f"<b style='color:{color};font-size:13px;'>{name}</b><br>"]

        for key in ["country", "ocean", "type", "reef_type", "vent_type",
                     "designation", "discoverer", "status"]:
            val = e.get(key)
            if val:
                label = key.replace("_", " ").title()
                popup_parts.append(f"<b>{escape(label)}:</b> {escape(str(val))}<br>")

        for key in ["depth_m", "length_km", "area_km2", "visibility_m",
                     "temperature_c", "year_discovered", "established"]:
            val = e.get(key)
            if val is not None:
                label = key.replace("_", " ").title()
                popup_parts.append(f"<b>{escape(label)}:</b> {escape(str(val))}<br>")

        if e.get("highlights"):
            popup_parts.append(
                f"<b>Highlights:</b> {escape(str(e['highlights']))}<br>"
            )

        popup_parts.append(
            f"<div style='margin-top:6px;font-size:11px;color:#8b97b0;'>"
            f"{details[:300]}{'...' if len(details) > 300 else ''}</div>"
        )

        popup_html = (
            f"<div style='min-width:260px;max-width:340px;font-family:sans-serif;"
            f"font-size:12px;color:#e8ecf4;background:#111827;padding:10px;"
            f"border-radius:6px;border:1px solid #2a3550;'>"
            f"{''.join(popup_parts)}</div>"
        )

        # Determine marker radius from depth or area
        depth = e.get("depth_m", 0)
        area = e.get("area_km2", 0)
        if area and area > 100000:
            radius = 10
        elif area and area > 10000:
            radius = 8
        elif depth and depth > 5000:
            radius = 9
        elif depth and depth > 1000:
            radius = 7
        else:
            radius = 5

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=1.5,
            popup=folium.Popup(popup_html, max_width=360),
            tooltip=name,
        ).add_to(m)

    return m


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: CONVERT TO DATAFRAME
# ═══════════════════════════════════════════════════════════════════════════════
def _entries_to_dataframe(entries: list) -> pd.DataFrame:
    """Convert entry list to a clean DataFrame."""
    if not entries:
        return pd.DataFrame()

    rows = []
    for e in entries:
        row = {}
        for k, v in e.items():
            col_name = k.replace("_", " ").title()
            row[col_name] = v
        rows.append(row)

    df = pd.DataFrame(rows)

    # Reorder so Name/Lat/Lon are first if present
    priority = ["Name", "Lat", "Lon"]
    cols = [c for c in priority if c in df.columns]
    cols += [c for c in df.columns if c not in cols]
    return df[cols]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: DETAIL CARDS
# ═══════════════════════════════════════════════════════════════════════════════
def _render_detail_cards(entries: list, color: str, max_cards: int = 12):
    """Render styled detail cards for entries."""
    for i, e in enumerate(entries[:max_cards]):
        name = escape(str(e.get("name", "Unknown")))
        details = escape(str(e.get("details", "")))
        highlights = escape(str(e.get("highlights", "")))

        # Gather metadata lines
        meta_parts = []
        for key in ["country", "ocean", "type", "reef_type", "vent_type",
                     "designation", "discoverer", "status", "species",
                     "tectonic", "last_eruption", "cause"]:
            val = e.get(key)
            if val:
                label = key.replace("_", " ").title()
                meta_parts.append(
                    f"<span style='color:{_MUTED};'>{escape(label)}:</span> "
                    f"<span style='color:{_TEXT2};'>{escape(str(val))}</span>"
                )
        for key in ["depth_m", "length_km", "area_km2", "visibility_m",
                     "temperature_c", "year_discovered", "established",
                     "discovery_year"]:
            val = e.get(key)
            if val is not None:
                label = key.replace("_", " ").title()
                meta_parts.append(
                    f"<span style='color:{_MUTED};'>{escape(label)}:</span> "
                    f"<span style='color:{_TEXT2};'>{escape(str(val))}</span>"
                )

        meta_html = " &middot; ".join(meta_parts)

        st.markdown(f"""
        <div style="background:rgba(17,24,39,0.65); border:1px solid {_BORDER};
                    border-left:4px solid {color}; border-radius:8px;
                    padding:0.9rem 1.1rem; margin-bottom:0.75rem;">
            <div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.4rem;">
                <span style="color:{color}; font-size:1.05rem; font-weight:700;">{name}</span>
                <span style="color:{_MUTED}; font-size:0.75rem; margin-left:auto;">
                    {escape(str(e.get('lat', '')))}N, {escape(str(e.get('lon', '')))}E
                </span>
            </div>
            <div style="font-size:0.78rem; line-height:1.6; margin-bottom:0.4rem;">
                {meta_html}
            </div>
            <div style="color:#f59e0b; font-size:0.8rem; margin-bottom:0.3rem;">
                {highlights}
            </div>
            <div style="color:{_TEXT2}; font-size:0.8rem; line-height:1.5;">
                {details}
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: MODE INTRO PANEL
# ═══════════════════════════════════════════════════════════════════════════════
def _render_mode_intro(mode: str, color: str, entries: list):
    """Render the introductory panel for a mode."""
    icon = MODE_ICONS.get(mode, "&#127754;")
    desc = MODE_DESCRIPTIONS.get(mode, "")
    safe_desc = escape(desc)

    st.markdown(f"""
    <div style="background:rgba(17,24,39,0.65); border:1px solid {_BORDER};
                border-left:4px solid {color}; border-radius:8px;
                padding:1rem 1.2rem; margin-bottom:1rem;">
        <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.5rem;">
            <span style="font-size:1.5rem; color:{color};">{icon}</span>
            <span style="color:{_TEXT}; font-size:1.1rem; font-weight:700;">
                {escape(mode)}
            </span>
            <span style="color:{_MUTED}; font-size:0.8rem; margin-left:auto;">
                {len(entries)} entries
            </span>
        </div>
        <div style="color:{_TEXT2}; font-size:0.85rem; line-height:1.5;">
            {safe_desc}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════
def render_underwater_maps_tab():
    """Main render function for the Underwater World Explorer tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header cyan">'
        '<h4>&#127754; Underwater World Explorer</h4>'
        '<p>Dive sites, ocean trenches, coral reefs, underwater caves & 10 ocean maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # MODE SELECTOR
    # ══════════════════════════════════════════
    st.markdown("#### Select Map Mode")

    mode = st.selectbox(
        "Choose an underwater category to explore",
        MAP_MODES,
        key="underwater_mode",
        help="Each mode features a curated dataset with interactive map, statistics, and downloadable data.",
    )

    color = MODE_COLORS.get(mode, _ACCENT)
    entries = _MODE_DATA.get(mode, [])

    # Remove any accidental duplicates (based on name)
    seen_names = set()
    unique_entries = []
    for e in entries:
        name = e.get("name", "")
        if name not in seen_names:
            seen_names.add(name)
            unique_entries.append(e)
    entries = unique_entries

    # ══════════════════════════════════════════
    # MODE INTRODUCTION
    # ══════════════════════════════════════════
    _render_mode_intro(mode, color, entries)

    # ══════════════════════════════════════════
    # STATS OVERVIEW
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Overview & Statistics")
    _render_stats(entries, mode, color)

    # ══════════════════════════════════════════
    # CHART
    # ══════════════════════════════════════════
    chart_modes_depth = [
        "World's Best Dive Sites", "Deep Ocean Trenches", "Underwater Caves & Cenotes",
        "Hydrothermal Vents", "Submarine Volcanoes", "Deep Sea Features",
        "Famous Underwater Discoveries",
    ]
    chart_modes_area = [
        "Coral Reefs", "Kelp Forests & Seagrass", "Marine Protected Areas",
    ]

    if mode in chart_modes_depth:
        with st.expander("Depth Comparison Chart", expanded=False):
            fig = _make_depth_chart(entries, color, f"{mode} -- Depth Comparison")
            if fig:
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("No depth data available for charting.")

    elif mode in chart_modes_area:
        with st.expander("Area Comparison Chart", expanded=False):
            fig = _make_area_chart(entries, color, f"{mode} -- Area Comparison")
            if fig:
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("No area data available for charting.")

    # ══════════════════════════════════════════
    # INTERACTIVE MAP
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Interactive Map")

    # Legend
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:0.5rem; '
        f'margin-bottom:0.5rem;">'
        f'<span style="font-size:1.2rem; color:{color};">&#127754;</span>'
        f'<span style="color:{_TEXT2}; font-size:0.85rem;">'
        f'{escape(mode)} &mdash; {len(entries)} locations mapped</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Determine optimal zoom and center based on mode
    zoom_overrides = {
        "Kelp Forests & Seagrass": (10.0, 0.0, 2),
        "Marine Protected Areas": (0.0, 0.0, 2),
        "Deep Sea Features": (15.0, -20.0, 2),
        "Deep Ocean Trenches": (10.0, 150.0, 2),
    }

    if mode in zoom_overrides:
        c_lat, c_lon, zoom = zoom_overrides[mode]
        m = _build_map(entries, color, mode, center=[c_lat, c_lon], zoom=zoom)
    else:
        m = _build_map(entries, color, mode)

    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # DETAIL CARDS
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Detailed Entries")

    show_all = st.checkbox("Show all entries", value=False, key="underwater_show_all")
    max_display = len(entries) if show_all else min(12, len(entries))

    _render_detail_cards(entries, color, max_cards=max_display)

    if not show_all and len(entries) > 12:
        st.caption(
            f"Showing 12 of {len(entries)} entries. "
            f"Check 'Show all entries' to see everything."
        )

    # ══════════════════════════════════════════
    # DATA TABLE & DOWNLOAD
    # ══════════════════════════════════════════
    st.markdown("---")
    df = _entries_to_dataframe(entries)

    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, use_container_width=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} {mode} Entries (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"underwater_{mode.lower().replace(' ', '_').replace('&', 'and')}.csv",
        mime="text/csv",
        key="underwater_csv_download",
    )

    # ══════════════════════════════════════════
    # FOOTER INFO
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(
        f'<div style="color:{_MUTED}; font-size:0.75rem; line-height:1.5; '
        f'padding:0.5rem 0;">'
        f'<b>Data Sources:</b> Curated scientific records, NOAA Ocean Explorer, '
        f'GEBCO bathymetry, UNESCO World Heritage Centre, IUCN Marine Protected Areas, '
        f'Reef Check, Global Coral Reef Monitoring Network, InterRidge Vent Database, '
        f'Smithsonian Global Volcanism Program, OBIS (Ocean Biodiversity Information System).'
        f'<br><b>Note:</b> Coordinates are approximate centers for large features. '
        f'Depth and area values are from the most recent published surveys.'
        f'</div>',
        unsafe_allow_html=True,
    )
