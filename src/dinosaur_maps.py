"""
Dinosaur & Paleontology Explorer module for TerraScout AI.
Provides 10 curated map modes covering major dinosaur dig sites, fossil beaches,
museum halls, national parks, and mass extinction sites worldwide.
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
# COLOR PALETTE
# ═══════════════════════════════════════════
MODE_COLORS = {
    "Major Dinosaur Dig Sites": "#10b981",
    "T-Rex Discovery Sites": "#ef4444",
    "Sauropod Trackways": "#f59e0b",
    "Jurassic Coast & Fossil Beaches": "#06b6d4",
    "Natural History Dinosaur Halls": "#8b5cf6",
    "Dinosaur National Parks": "#22c55e",
    "Pterosaur Sites": "#ec4899",
    "Marine Reptile Sites": "#3b82f6",
    "Amber Fossil Sites": "#f97316",
    "Mass Extinction Sites": "#dc2626",
}

# ═══════════════════════════════════════════
# PRESET DATA FOR ALL 10 MODES
# ═══════════════════════════════════════════

MAJOR_DIG_SITES = [
    {"name": "Hell Creek Formation", "lat": 47.55, "lon": -106.50, "desc": "Montana, USA — One of the richest Late Cretaceous fossil beds. Source of T. rex, Triceratops, Edmontosaurus.", "period": "Late Cretaceous (68-66 Ma)"},
    {"name": "Gobi Desert — Flaming Cliffs", "lat": 44.15, "lon": 103.73, "desc": "Bayanzag, Mongolia — Roy Chapman Andrews' legendary site. First dinosaur eggs, Velociraptor, Protoceratops.", "period": "Late Cretaceous (75-71 Ma)"},
    {"name": "Patagonia — Plaza Huincul", "lat": -38.93, "lon": -69.32, "desc": "Neuquén, Argentina — Giganotosaurus, Argentinosaurus, one of the largest dinosaurs ever found.", "period": "Late Cretaceous (97-93 Ma)"},
    {"name": "Liaoning Province", "lat": 41.80, "lon": 120.70, "desc": "Yixian Formation, China — Feathered dinosaurs revolution: Sinosauropteryx, Microraptor, Confuciusornis.", "period": "Early Cretaceous (125-120 Ma)"},
    {"name": "Morrison Formation — Dinosaur Ridge", "lat": 39.67, "lon": -105.20, "desc": "Colorado, USA — Jurassic giant quarry: Apatosaurus, Stegosaurus, Allosaurus. First Bone Wars site.", "period": "Late Jurassic (155-148 Ma)"},
    {"name": "Tendaguru Formation", "lat": -9.68, "lon": 38.43, "desc": "Tanzania — Giraffatitan (Brachiosaurus) brancai, Kentrosaurus. Africa's greatest dinosaur quarry.", "period": "Late Jurassic (155-145 Ma)"},
    {"name": "Ischigualasto Formation", "lat": -30.16, "lon": -67.84, "desc": "San Juan, Argentina — Valley of the Moon. Earliest dinosaurs: Eoraptor, Herrerasaurus.", "period": "Late Triassic (231-225 Ma)"},
    {"name": "Ghost Ranch", "lat": 36.32, "lon": -106.48, "desc": "New Mexico, USA — Mass burial of Coelophysis. One of the oldest dinosaur bone beds in North America.", "period": "Late Triassic (228-208 Ma)"},
    {"name": "Solnhofen Limestone", "lat": 48.90, "lon": 10.97, "desc": "Bavaria, Germany — Archaeopteryx, the iconic feathered transitional fossil linking dinosaurs to birds.", "period": "Late Jurassic (150 Ma)"},
    {"name": "Dashanpu Formation", "lat": 29.39, "lon": 104.78, "desc": "Zigong, Sichuan, China — Middle Jurassic trove: Shunosaurus, Gasosaurus, Huayangosaurus.", "period": "Middle Jurassic (170-160 Ma)"},
    {"name": "Two Medicine Formation", "lat": 48.10, "lon": -112.40, "desc": "Montana, USA — Maiasaura nesting grounds, evidence of dinosaur parental care.", "period": "Late Cretaceous (80-74 Ma)"},
    {"name": "Nemegt Formation", "lat": 43.50, "lon": 101.00, "desc": "Gobi Desert, Mongolia — Tarbosaurus, Therizinosaurus, Deinocheirus. Rich Late Cretaceous ecosystem.", "period": "Late Cretaceous (72-66 Ma)"},
]

TREX_SITES = [
    {"name": "Sue — Field Museum Discovery", "lat": 45.47, "lon": -103.35, "desc": "Cheyenne River Reservation, SD — Sue Hendrickson found the most complete T. rex (FMNH PR 2081) in 1990.", "year": "1990"},
    {"name": "Scotty — Eastend, Saskatchewan", "lat": 49.13, "lon": -108.82, "desc": "Saskatchewan, Canada — Largest T. rex specimen found. Estimated 8,870 kg. Discovered 1991, excavated until 2014.", "year": "1991"},
    {"name": "Stan — Hell Creek, SD", "lat": 45.78, "lon": -103.37, "desc": "Harding County, SD — BHI 3033 found by Stan Sacrison. One of most studied T. rex specimens. Sold for $31.8M.", "year": "1987"},
    {"name": "Wankel Rex — Fort Peck", "lat": 47.94, "lon": -106.41, "desc": "Fort Peck Reservoir, MT — First substantially complete T. rex (MOR 555). Discovered by Kathy Wankel.", "year": "1988"},
    {"name": "Original T. rex — Hell Creek", "lat": 47.55, "lon": -106.95, "desc": "Montana — Barnum Brown discovered the T. rex holotype (AMNH 973) in 1902 for the American Museum.", "year": "1902"},
    {"name": "Trix — Dawson County, MT", "lat": 47.08, "lon": -104.95, "desc": "Montana, USA — Near-complete adult female T. rex, now at Naturalis Museum, Leiden, Netherlands.", "year": "2013"},
    {"name": "Dueling Dinosaurs Site", "lat": 47.50, "lon": -106.20, "desc": "Jordan, MT — T. rex and Triceratops locked in combat, preserved together. Acquired by NCSM in 2020.", "year": "2006"},
    {"name": "Bucky — Hill County, MT", "lat": 48.63, "lon": -109.40, "desc": "Montana — Juvenile T. rex specimen (TCM 2001.90.1), found by Bucky Derflinger in 1998.", "year": "1998"},
    {"name": "Jane — Ekalaka, MT", "lat": 45.89, "lon": -104.55, "desc": "Carter County, MT — Juvenile T. rex or Nanotyrannus? One of the most debated specimens (BMR P2002.4.1).", "year": "2001"},
    {"name": "Thomas — Thornburg Ranch, WY", "lat": 44.72, "lon": -105.50, "desc": "Wyoming — Well-preserved T. rex specimen discovered in the Lance Formation.", "year": "2003"},
]

SAUROPOD_TRACKWAYS = [
    {"name": "Cal Orcko — Sucre", "lat": -19.00, "lon": -65.24, "desc": "Bolivia — World's largest dinosaur trackway wall: 5,055 footprints, 462 trails on a near-vertical limestone cliff.", "track_count": "5,055+"},
    {"name": "Lark Quarry", "lat": -23.04, "lon": 142.42, "desc": "Winton, Queensland, Australia — Dinosaur stampede preserved in stone, over 3,300 footprints from 150+ dinosaurs.", "track_count": "3,300+"},
    {"name": "Plagne Trackway", "lat": 46.19, "lon": 5.67, "desc": "Ain, France — Longest sauropod trackway in the world at 155m. Left by a giant sauropod 150 Ma.", "track_count": "110 prints"},
    {"name": "Dinosaur Footprints Reservation", "lat": 42.34, "lon": -72.60, "desc": "Holyoke, Massachusetts — Eubrontes trackway on Connecticut River sandstone. Known since 1802.", "track_count": "800+"},
    {"name": "Münchehagen Dinosaur Park", "lat": 52.38, "lon": 9.22, "desc": "Lower Saxony, Germany — Over 250 sauropod footprints in a quarry. Well-preserved Early Cretaceous trackways.", "track_count": "250+"},
    {"name": "Fumanya", "lat": 42.17, "lon": 1.78, "desc": "Berguedà, Catalonia, Spain — Titanosaur trackway site with over 3,500 prints on a coal mine exposure.", "track_count": "3,500+"},
    {"name": "Paluxy River Trackway", "lat": 32.25, "lon": -97.81, "desc": "Glen Rose, Texas — Iconic sauropod and theropod trackways in Dinosaur Valley State Park.", "track_count": "Multiple trails"},
    {"name": "Torotoro National Park", "lat": -18.13, "lon": -65.77, "desc": "Potosí, Bolivia — Theropod and sauropod footprints in Cretaceous limestone, in a dramatic canyon landscape.", "track_count": "2,500+"},
    {"name": "Isle of Skye Trackways", "lat": 57.30, "lon": -6.32, "desc": "Scotland, UK — Middle Jurassic sauropod trackways discovered in tidal lagoon deposits. 170 Ma.", "track_count": "50+"},
    {"name": "Courtedoux Trackways", "lat": 47.39, "lon": 6.94, "desc": "Jura, Switzerland — Over 14,000 dinosaur footprints from the Late Jurassic, largest Swiss site.", "track_count": "14,000+"},
]

JURASSIC_COAST_SITES = [
    {"name": "Lyme Regis", "lat": 50.73, "lon": -2.93, "desc": "Dorset, UK — Mary Anning's legendary fossil hunting grounds. Ichthyosaur, plesiosaur, pterosaur discoveries.", "fossils": "Marine reptiles, ammonites"},
    {"name": "Charmouth Beach", "lat": 50.73, "lon": -2.90, "desc": "Dorset, UK — World-class ammonite and belemnite collecting. Jurassic Coast UNESCO World Heritage Site.", "fossils": "Ammonites, belemnites"},
    {"name": "Kimmeridge Bay", "lat": 50.61, "lon": -2.13, "desc": "Dorset, UK — Rich Kimmeridgian marine fossils in dark shales. Oil seeps and bituminous shale.", "fossils": "Marine invertebrates"},
    {"name": "Kem Kem Beds — Erfoud", "lat": 31.43, "lon": -4.43, "desc": "Morocco — Cretaceous river system fossils: Spinosaurus, Carcharodontosaurus, giant fish. World's most dangerous ecosystem.", "fossils": "Theropods, fish, crocodilians"},
    {"name": "Joggins Fossil Cliffs", "lat": 45.70, "lon": -64.44, "desc": "Nova Scotia, Canada — UNESCO site. Carboniferous 'Coal Age' forests, earliest known reptile (Hylonomus).", "fossils": "Carboniferous trees, reptiles"},
    {"name": "Dorset — Chesil Beach/Portland", "lat": 50.55, "lon": -2.44, "desc": "Dorset, UK — Portland limestone with titanosaur footprints and rich Jurassic invertebrate fossils.", "fossils": "Sauropod tracks, ammonites"},
    {"name": "Sidmouth to Beer", "lat": 50.68, "lon": -3.12, "desc": "Devon, UK — Triassic red beds transition to Jurassic limestones. 250 million year geological walk.", "fossils": "Triassic reptiles, Jurassic marine"},
    {"name": "Whitby — Yorkshire Coast", "lat": 54.49, "lon": -0.61, "desc": "North Yorkshire, UK — Jurassic ammonites and jet (fossilized wood). Cleveland Ironstone Formation.", "fossils": "Ammonites, jet, marine reptiles"},
    {"name": "Solnhofen Beach", "lat": 48.90, "lon": 10.97, "desc": "Bavaria, Germany — Lithographic limestone quarries: Archaeopteryx, pterosaurs, horseshoe crabs. Finest Lagerstätte.", "fossils": "Archaeopteryx, pterosaurs"},
    {"name": "Barton Cliffs", "lat": 50.73, "lon": -1.71, "desc": "Hampshire, UK — Eocene fossils: shark teeth (Otodus), tropical shells, and leaves. 40 million years old.", "fossils": "Shark teeth, shells"},
]

DINOSAUR_MUSEUMS = [
    {"name": "American Museum of Natural History", "lat": 40.7813, "lon": -73.9740, "desc": "New York, USA — Iconic T. rex (AMNH 5027), Apatosaurus, Barosaurus mount in the Great Hall.", "highlight": "T. rex, Barosaurus rearing mount"},
    {"name": "Field Museum of Natural History", "lat": 41.8663, "lon": -87.6170, "desc": "Chicago, USA — Home of Sue, the most complete T. rex. Evolved: Dino exhibition and Maximo the Titanosaur.", "highlight": "Sue the T. rex, Maximo titanosaur"},
    {"name": "Natural History Museum London", "lat": 51.4967, "lon": -0.1764, "desc": "London, UK — Dippy the Diplodocus (now touring), original Iguanodon teeth, Hintze Hall blue whale.", "highlight": "Dippy, Mantellisaurus, Stegosaurus"},
    {"name": "Royal Tyrrell Museum", "lat": 51.4798, "lon": -112.7878, "desc": "Drumheller, Alberta, Canada — World's premier dinosaur museum in the Badlands. 160,000+ specimens.", "highlight": "Borealopelta nodosaur mummy"},
    {"name": "Museum für Naturkunde", "lat": 52.5300, "lon": 13.3794, "desc": "Berlin, Germany — Houses Giraffatitan brancai, tallest mounted dinosaur skeleton in the world (13.27m).", "highlight": "Giraffatitan brancai, Archaeopteryx"},
    {"name": "Smithsonian National Museum of Natural History", "lat": 38.8913, "lon": -77.0261, "desc": "Washington D.C., USA — Nation's T. rex on display. Deep Time exhibition traces 3.7 billion years of life.", "highlight": "Nation's T. rex, Deep Time"},
    {"name": "Zigong Dinosaur Museum", "lat": 29.3920, "lon": 104.7750, "desc": "Zigong, Sichuan, China — Built over the Dashanpu Formation dig site. In-situ fossil hall unique worldwide.", "highlight": "In-situ Jurassic quarry floor"},
    {"name": "Fukui Prefectural Dinosaur Museum", "lat": 36.0588, "lon": 136.5428, "desc": "Katsuyama, Japan — One of the top 3 dinosaur museums worldwide. 44 complete dinosaur skeletons.", "highlight": "44 mounted skeletons, Fukuiraptor"},
    {"name": "Fernbank Museum of Natural History", "lat": 33.7742, "lon": -84.3280, "desc": "Atlanta, USA — Giganotosaurus and Argentinosaurus casts in Giants of the Mesozoic exhibition.", "highlight": "Giganotosaurus, Argentinosaurus"},
    {"name": "Museo Paleontológico Egidio Feruglio", "lat": -43.2933, "lon": -65.3028, "desc": "Trelew, Patagonia, Argentina — Patagotitan mayorum, the largest dinosaur ever found. World-class collection.", "highlight": "Patagotitan mayorum cast"},
    {"name": "Dinosaur Isle Museum", "lat": 50.6577, "lon": -1.1553, "desc": "Sandown, Isle of Wight, UK — Britain's first purpose-built dinosaur museum. Neovenator, Eotyrannus.", "highlight": "Neovenator, Isle of Wight dinosaurs"},
    {"name": "National Dinosaur Museum", "lat": -35.2140, "lon": 149.0550, "desc": "Canberra, Australia — Largest permanent display of dinosaur and prehistoric fossils in the Southern Hemisphere.", "highlight": "Muttaburrasaurus, Australian megafauna"},
]

DINOSAUR_PARKS = [
    {"name": "Dinosaur Provincial Park", "lat": 50.77, "lon": -111.53, "desc": "Alberta, Canada — UNESCO World Heritage Site. Over 40 dinosaur species from 75 million years ago. Badlands landscape.", "species_count": "40+"},
    {"name": "Dinosaur National Monument", "lat": 40.44, "lon": -109.31, "desc": "Utah/Colorado, USA — 1,500 dinosaur bones exposed on a quarry wall. Allosaurus, Camarasaurus, Stegosaurus.", "species_count": "Dozens"},
    {"name": "Badlands National Park", "lat": 43.75, "lon": -102.50, "desc": "South Dakota, USA — Oligocene mammal fossils. Dramatic eroded landscape revealing 75 million years of deposition.", "species_count": "Cenozoic mammals"},
    {"name": "Ischigualasto Provincial Park", "lat": -30.16, "lon": -67.84, "desc": "San Juan, Argentina — Valley of the Moon. Earliest dinosaurs (Triassic): Eoraptor, Herrerasaurus, Panphagia.", "species_count": "10+ Triassic"},
    {"name": "Dinosaur Valley State Park", "lat": 32.25, "lon": -97.81, "desc": "Glen Rose, Texas, USA — Sauropod and theropod trackways in the Paluxy River. Acrocanthosaurus tracks.", "species_count": "Track makers"},
    {"name": "Talampaya National Park", "lat": -29.76, "lon": -67.83, "desc": "La Rioja, Argentina — Triassic red sandstone canyons with some of the oldest dinosaur fossils in the world.", "species_count": "Triassic reptiles"},
    {"name": "Petrified Forest National Park", "lat": 34.82, "lon": -109.89, "desc": "Arizona, USA — Late Triassic ecosystem: Chinle Formation petrified wood, early dinosaurs, phytosaurs.", "species_count": "Triassic ecosystem"},
    {"name": "Dashanpu Dinosaur Quarry", "lat": 29.39, "lon": 104.78, "desc": "Zigong, Sichuan, China — Protected Middle Jurassic quarry site. Shunosaurus, Huayangosaurus in situ.", "species_count": "12+"},
    {"name": "Auca Mahuevo", "lat": -37.78, "lon": -68.92, "desc": "Neuquén, Argentina — Massive titanosaur nesting ground. Thousands of eggs with preserved embryonic skin.", "species_count": "Titanosaur eggs"},
    {"name": "Egg Mountain", "lat": 47.85, "lon": -112.45, "desc": "Montana, USA — Jack Horner's site: Maiasaura nesting colonies proving dinosaur parental care.", "species_count": "Maiasaura nests"},
]

PTEROSAUR_SITES = [
    {"name": "Santana Formation — Araripe Basin", "lat": -7.30, "lon": -39.30, "desc": "Ceará, Brazil — Finest pterosaur fossils: Anhanguera, Tupuxuara, Brasileodactylus. Exceptional 3D preservation.", "species": "Anhanguera, Tupuxuara"},
    {"name": "Solnhofen Limestone", "lat": 48.90, "lon": 10.97, "desc": "Bavaria, Germany — First pterosaur (Pterodactylus) described in 1784. Also Rhamphorhynchus, Anurognathus.", "species": "Pterodactylus, Rhamphorhynchus"},
    {"name": "Niobrara Formation", "lat": 39.10, "lon": -100.30, "desc": "Kansas, USA — Giant Pteranodon and Nyctosaurus from the Western Interior Seaway. Wingspans up to 6m.", "species": "Pteranodon, Nyctosaurus"},
    {"name": "Romualdo Formation", "lat": -7.45, "lon": -39.50, "desc": "Chapada do Araripe, Brazil — Giant azhdarchids and ornithocheirids. Complete skulls with soft tissue impressions.", "species": "Tropeognathus, Cearadactylus"},
    {"name": "Hatzeg Island — Transylvania", "lat": 45.62, "lon": 22.88, "desc": "Romania — Hatzegopteryx, one of the largest flying animals ever. 10-12m wingspan. Island dwarf dinosaurs.", "species": "Hatzegopteryx"},
    {"name": "Big Bend National Park", "lat": 29.25, "lon": -103.25, "desc": "Texas, USA — Quetzalcoatlus northropi, the largest flying animal ever known. 10-11m wingspan, Late Cretaceous.", "species": "Quetzalcoatlus"},
    {"name": "Cambridge Greensand", "lat": 52.20, "lon": 0.12, "desc": "Cambridgeshire, UK — Ornithostoma, early pterosaur finds from Cretaceous marine deposits.", "species": "Ornithostoma, Ornithocheirus"},
    {"name": "Yixian Formation — Pterosaur Beds", "lat": 41.60, "lon": 120.80, "desc": "Liaoning, China — Jeholopterus, Darwinopterus. Exceptional preservation with wing membranes and pycnofibers.", "species": "Darwinopterus, Jeholopterus"},
    {"name": "Crayssac Trackways", "lat": 44.47, "lon": 1.55, "desc": "Lot, France — Pterosaur footprints and landing traces from the Late Jurassic. Rare trackway evidence.", "species": "Pterosaur tracks (ichnofossils)"},
    {"name": "Alberta Badlands Pterosaur Sites", "lat": 51.50, "lon": -112.70, "desc": "Alberta, Canada — Cryodrakon boreas, a giant azhdarchid from Dinosaur Provincial Park. 10m wingspan.", "species": "Cryodrakon boreas"},
]

MARINE_REPTILE_SITES = [
    {"name": "Lyme Regis — Mary Anning Sites", "lat": 50.73, "lon": -2.93, "desc": "Dorset, UK — Mary Anning's ichthyosaur (1811) and plesiosaur (1823) discoveries that changed science.", "type": "Ichthyosaur, Plesiosaur"},
    {"name": "Holzmaden — Posidonia Shale", "lat": 48.63, "lon": 9.52, "desc": "Baden-Württemberg, Germany — Perfectly preserved ichthyosaurs with skin outlines and embryos. Early Jurassic.", "type": "Ichthyosaur"},
    {"name": "Svalbard — Pliosaurus Site", "lat": 78.20, "lon": 15.60, "desc": "Spitsbergen, Norway — 'Predator X' (Pliosaurus funkei), one of the largest marine predators. 12-13m long.", "type": "Pliosaurus"},
    {"name": "Smoky Hill Chalk — Kansas", "lat": 39.00, "lon": -100.50, "desc": "Kansas, USA — Mosasaurus, Tylosaurus, Elasmosaurus from the Western Interior Seaway. Niobrara Chalk.", "type": "Mosasaur, Plesiosaur"},
    {"name": "Maastricht Limestone", "lat": 50.85, "lon": 5.69, "desc": "Maastricht, Netherlands — Type locality of Mosasaurus hoffmannii (1764). Gave its name to the Maastrichtian age.", "type": "Mosasaur (type specimen)"},
    {"name": "Street — Somerset", "lat": 51.13, "lon": -2.74, "desc": "Somerset, UK — Early ichthyosaur discoveries, beautifully preserved Blue Lias specimens.", "type": "Ichthyosaur"},
    {"name": "Svalbard — Ophthalmosaurus Site", "lat": 78.00, "lon": 16.00, "desc": "Spitsbergen, Norway — Multiple marine reptile species in Arctic Jurassic sediments.", "type": "Ichthyosaur, Plesiosaur"},
    {"name": "Wadi Al-Hitan (Whale Valley)", "lat": 29.27, "lon": 30.04, "desc": "Fayoum, Egypt — UNESCO site. Eocene whale evolution: Basilosaurus, Dorudon. Not reptiles but key marine fossils.", "type": "Archaeoceti (early whales)"},
    {"name": "Quantou Formation", "lat": 44.80, "lon": 124.00, "desc": "Jilin, China — Manchurochelys and various Cretaceous marine/freshwater reptile fossils.", "type": "Aquatic reptiles, turtles"},
    {"name": "Aramberri Plesiosaur Site", "lat": 24.10, "lon": -99.82, "desc": "Nuevo León, Mexico — 'Monster of Aramberri', giant pliosaur estimated at 15m. Late Jurassic marine beds.", "type": "Pliosaurus"},
]

AMBER_SITES = [
    {"name": "Dominican Republic Amber Mines", "lat": 19.63, "lon": -70.35, "desc": "Cordillera Septentrional — Miocene amber (15-20 Ma) with superb insect inclusions, frogs, lizards.", "age": "15-20 Ma (Miocene)"},
    {"name": "Baltic Amber Coast — Kaliningrad", "lat": 54.72, "lon": 20.50, "desc": "Kaliningrad, Russia — World's largest amber deposit (Eocene, 44 Ma). Amber Museum, thousands of insect species.", "age": "44 Ma (Eocene)"},
    {"name": "Kachin Amber — Hukawng Valley", "lat": 26.40, "lon": 96.80, "desc": "Myanmar — Cretaceous amber (99 Ma) with dinosaur feathers, baby bird, spider attacking wasp, ticks on dino feathers.", "age": "99 Ma (Cretaceous)"},
    {"name": "New Jersey Amber — Sayreville", "lat": 40.46, "lon": -74.36, "desc": "New Jersey, USA — Cretaceous amber (90 Ma) from the Raritan Formation. Oldest ant and oldest mushroom.", "age": "90 Ma (Cretaceous)"},
    {"name": "Lebanese Amber — Byblos", "lat": 34.12, "lon": 35.65, "desc": "Mount Lebanon, Lebanon — Early Cretaceous amber (130 Ma) among the world's oldest. Exceptional insect preservation.", "age": "130 Ma (Early Cretaceous)"},
    {"name": "Gdańsk — Amber Capital", "lat": 54.35, "lon": 18.65, "desc": "Gdańsk, Poland — Historic amber trade center. Museum of Amber with spectacular Baltic amber inclusions.", "age": "44 Ma (Eocene)"},
    {"name": "Chiapas Amber — Simojovel", "lat": 17.14, "lon": -92.69, "desc": "Chiapas, Mexico — Miocene amber (23 Ma) with diverse tropical insect fauna. Important for paleobiogeography.", "age": "23 Ma (Miocene)"},
    {"name": "Canadian Amber — Grassy Lake", "lat": 49.73, "lon": -111.73, "desc": "Alberta, Canada — Late Cretaceous amber (78 Ma) with feathers, insects, and possible dinosaur-era parasites.", "age": "78 Ma (Late Cretaceous)"},
    {"name": "Fushun Amber", "lat": 41.85, "lon": 123.90, "desc": "Liaoning, China — Eocene amber (53 Ma) from coal deposits. Ants, beetles, and early tropical insects.", "age": "53 Ma (Eocene)"},
    {"name": "Ethiopian Amber", "lat": 11.60, "lon": 39.60, "desc": "Tigray, Ethiopia — Cretaceous amber (95 Ma) from Africa with diverse arthropods, unique biogeographic importance.", "age": "95 Ma (Cretaceous)"},
]

MASS_EXTINCTION_SITES = [
    {"name": "Chicxulub Crater", "lat": 21.40, "lon": -89.52, "desc": "Yucatán, Mexico — The impact crater from the asteroid that ended the Cretaceous. 180 km diameter, 66 Ma.", "event": "K-Pg Extinction (66 Ma)"},
    {"name": "Gubbio K-Pg Boundary", "lat": 43.35, "lon": 12.58, "desc": "Umbria, Italy — Where Alvarez discovered the iridium anomaly (1980), proving the asteroid impact hypothesis.", "event": "K-Pg Boundary (66 Ma)"},
    {"name": "Stevns Klint", "lat": 55.27, "lon": 12.44, "desc": "Denmark — UNESCO site. Dramatic K-Pg boundary exposure in chalk cliffs. Fish Clay layer with iridium spike.", "event": "K-Pg Boundary (66 Ma)"},
    {"name": "El Kef — Tunisia", "lat": 36.17, "lon": 8.71, "desc": "Tunisia — Global Stratotype Section (GSSP) for the K-Pg boundary. Reference point for the mass extinction.", "event": "K-Pg GSSP (66 Ma)"},
    {"name": "Hell Creek K-Pg Boundary", "lat": 47.55, "lon": -106.50, "desc": "Montana, USA — Last dinosaurs before the extinction. Boundary clay with shocked quartz and iridium.", "event": "K-Pg Boundary (66 Ma)"},
    {"name": "Meishan Section", "lat": 31.08, "lon": 119.71, "desc": "Zhejiang, China — GSSP for the Permian-Triassic boundary. The Great Dying: 96% of marine species lost.", "event": "Permian-Triassic (252 Ma)"},
    {"name": "Siberian Traps", "lat": 64.00, "lon": 93.00, "desc": "Siberia, Russia — Massive volcanic eruptions that triggered the Permian-Triassic extinction. 7 million km³ of basalt.", "event": "Permian-Triassic (252 Ma)"},
    {"name": "Deccan Traps", "lat": 18.52, "lon": 73.86, "desc": "Maharashtra, India — Massive volcanic province that contributed to K-Pg extinction stress. 500,000 km² of basalt.", "event": "K-Pg volcanism (68-60 Ma)"},
    {"name": "Dob's Linn", "lat": 55.44, "lon": -3.27, "desc": "Southern Uplands, Scotland — GSSP for the Ordovician-Silurian boundary. Late Ordovician mass extinction site.", "event": "Ordovician-Silurian (444 Ma)"},
    {"name": "Tanis — North Dakota", "lat": 46.39, "lon": -106.02, "desc": "North Dakota, USA — Extraordinary site preserving the hours after the Chicxulub impact: surge deposits, tektites, fish.", "event": "K-Pg impact day (66 Ma)"},
    {"name": "CAMP — Central Atlantic Magmatic Province", "lat": 33.00, "lon": -5.00, "desc": "Morocco — End-Triassic eruptions across four continents. Triggered the Triassic-Jurassic mass extinction.", "event": "Triassic-Jurassic (201 Ma)"},
    {"name": "Frasnian-Famennian Boundary — Coumiac", "lat": 43.50, "lon": 3.05, "desc": "Hérault, France — GSSP for the Late Devonian extinction. Reef collapse and marine biodiversity crash.", "event": "Late Devonian (372 Ma)"},
]


# ═══════════════════════════════════════════
# MAP MODE REGISTRY
# ═══════════════════════════════════════════
MAP_MODES = {
    "Major Dinosaur Dig Sites": MAJOR_DIG_SITES,
    "T-Rex Discovery Sites": TREX_SITES,
    "Sauropod Trackways": SAUROPOD_TRACKWAYS,
    "Jurassic Coast & Fossil Beaches": JURASSIC_COAST_SITES,
    "Natural History Dinosaur Halls": DINOSAUR_MUSEUMS,
    "Dinosaur National Parks": DINOSAUR_PARKS,
    "Pterosaur Sites": PTEROSAUR_SITES,
    "Marine Reptile Sites": MARINE_REPTILE_SITES,
    "Amber Fossil Sites": AMBER_SITES,
    "Mass Extinction Sites": MASS_EXTINCTION_SITES,
}

# Extra field labels per mode (for the detail column in the DataFrame)
MODE_EXTRA_FIELD = {
    "Major Dinosaur Dig Sites": ("period", "Period"),
    "T-Rex Discovery Sites": ("year", "Discovery Year"),
    "Sauropod Trackways": ("track_count", "Track Count"),
    "Jurassic Coast & Fossil Beaches": ("fossils", "Notable Fossils"),
    "Natural History Dinosaur Halls": ("highlight", "Highlight"),
    "Dinosaur National Parks": ("species_count", "Species / Notes"),
    "Pterosaur Sites": ("species", "Key Species"),
    "Marine Reptile Sites": ("type", "Reptile Type"),
    "Amber Fossil Sites": ("age", "Age"),
    "Mass Extinction Sites": ("event", "Extinction Event"),
}


# ═══════════════════════════════════════════
# OPTIONAL PBDB ENRICHMENT
# ═══════════════════════════════════════════
@st.cache_data(ttl=3600)
def _fetch_pbdb_nearby(lat: float, lon: float, radius_km: float = 50) -> list:
    """Optionally fetch nearby fossil occurrences from PBDB for enrichment."""
    try:
        resp = requests.get(
            "https://paleobiodb.org/data1.2/occs/list.json",
            params={
                "lngmin": lon - radius_km / 111,
                "lngmax": lon + radius_km / 111,
                "latmin": lat - radius_km / 111,
                "latmax": lat + radius_km / 111,
                "show": "coords,class",
                "limit": 100,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("records", [])
    except Exception:
        return []


# ═══════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════
def _build_popup(site: dict, mode: str) -> str:
    """Build HTML popup for a site marker."""
    name = html_module.escape(site.get("name", "Unknown"))
    desc = html_module.escape(site.get("desc", ""))
    extra_key, extra_label = MODE_EXTRA_FIELD.get(mode, ("", ""))
    extra_val = html_module.escape(str(site.get(extra_key, ""))) if extra_key else ""

    popup = (
        f'<div style="background:#1a2235;color:#e8ecf4;padding:10px;border-radius:8px;'
        f'min-width:200px;max-width:300px;font-family:sans-serif;">'
        f'<b style="color:{MODE_COLORS.get(mode, "#06b6d4")};font-size:0.95rem;">{name}</b><br>'
        f'<span style="color:#8b97b0;font-size:0.8rem;">{desc}</span>'
    )
    if extra_val:
        popup += (
            f'<br><span style="color:#f59e0b;font-size:0.78rem;margin-top:4px;display:inline-block;">'
            f'{html_module.escape(extra_label)}: {extra_val}</span>'
        )
    popup += '</div>'
    return popup


def _compute_zoom(sites: list) -> int:
    """Compute a reasonable zoom level based on site spread."""
    if not sites:
        return 2
    lats = [s["lat"] for s in sites]
    lons = [s["lon"] for s in sites]
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)
    spread = max(lat_range, lon_range)
    if spread > 100:
        return 2
    elif spread > 50:
        return 3
    elif spread > 20:
        return 4
    elif spread > 10:
        return 5
    elif spread > 5:
        return 6
    return 7


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════
def render_dinosaur_maps_tab():
    """Main render function for the Dinosaur & Paleontology Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header emerald">
        <h4>🦕 Dinosaur &amp; Paleontology Explorer</h4>
        <p>Explore the world's greatest dinosaur dig sites, fossil beaches, trackways, museums, and mass extinction locations &mdash; all on an interactive dark map.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode selector ──
    mode = st.selectbox(
        "Map Mode",
        list(MAP_MODES.keys()),
        key="dino_map_mode",
    )

    sites = MAP_MODES[mode]
    color = MODE_COLORS.get(mode, "#06b6d4")
    extra_key, extra_label = MODE_EXTRA_FIELD.get(mode, ("", ""))

    # ── Stats row ──
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Sites", len(sites))
    with c2:
        countries = set()
        for s in sites:
            desc = s.get("desc", "")
            # Extract rough country from description (text after last dash or comma)
            if " — " in desc:
                countries.add(desc.split(" — ")[0].strip().split(",")[-1].strip())
            elif ", " in desc:
                parts = desc.split(", ")
                if len(parts) >= 2:
                    countries.add(parts[1].split(" ")[0].strip().rstrip("."))
        st.metric("Regions", len(countries) if countries else "Global")
    with c3:
        lats = [s["lat"] for s in sites]
        lat_range = f"{min(lats):.1f} to {max(lats):.1f}"
        st.metric("Latitude Range", lat_range)
    with c4:
        lons = [s["lon"] for s in sites]
        lon_range = f"{min(lons):.1f} to {max(lons):.1f}"
        st.metric("Longitude Range", lon_range)

    st.markdown("---")

    # ── Build folium map ──
    center_lat = sum(s["lat"] for s in sites) / len(sites)
    center_lon = sum(s["lon"] for s in sites) / len(sites)
    zoom = _compute_zoom(sites)

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name=html_module.escape(mode)).add_to(m)

    for site in sites:
        popup_html = _build_popup(site, mode)

        folium.CircleMarker(
            location=[site["lat"], site["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            weight=2,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=html_module.escape(site["name"]),
        ).add_to(cluster)

    folium.LayerControl().add_to(m)

    # Render map
    st_html(m._repr_html_(), height=500)

    # ── Data table ──
    st.markdown("---")
    st.markdown(f"#### {html_module.escape(mode)} — Site Details")

    rows = []
    for site in sites:
        row = {
            "Name": site["name"],
            "Latitude": site["lat"],
            "Longitude": site["lon"],
            "Description": site["desc"],
        }
        if extra_key:
            row[extra_label] = site.get(extra_key, "")
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    # ── Site cards ──
    st.markdown("---")
    st.markdown("#### Site Highlights")

    for site in sites:
        s_name = html_module.escape(site["name"])
        s_desc = html_module.escape(site["desc"])
        s_extra = html_module.escape(str(site.get(extra_key, ""))) if extra_key else ""
        extra_html = ""
        if s_extra:
            extra_html = (
                f'<div style="color:#f59e0b;font-size:0.78rem;margin-top:2px;">'
                f'{html_module.escape(extra_label)}: {s_extra}</div>'
            )

        st.markdown(f"""
        <div class="bio-card" style="display:flex;align-items:center;margin-bottom:0.6rem;">
            <div style="width:8px;height:60px;border-radius:4px;background:{color};
                        margin-right:1rem;flex-shrink:0;"></div>
            <div style="flex:1;">
                <div style="color:#e8ecf4;font-weight:700;font-size:0.9rem;">{s_name}</div>
                <div style="color:#8b97b0;font-size:0.8rem;">{s_desc}</div>
                {extra_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── CSV download ──
    st.markdown("---")
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    safe_filename = mode.lower().replace(" ", "_").replace("&", "and").replace("'", "")
    st.download_button(
        f"Download {len(sites)} Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"dino_{safe_filename}.csv",
        mime="text/csv",
        key="dino_csv_download",
    )

    # ── Optional PBDB enrichment ──
    st.markdown("---")
    st.markdown("#### Enrich with Paleobiology Database")
    st.markdown(
        '<p style="color:#8b97b0;font-size:0.85rem;">'
        'Click on a site below to fetch nearby fossil occurrences from PBDB (free API, no key).</p>',
        unsafe_allow_html=True,
    )

    selected_site = st.selectbox(
        "Select site for PBDB lookup",
        [s["name"] for s in sites],
        key="dino_pbdb_site",
    )

    if st.button("Fetch Nearby Fossils from PBDB", key="dino_pbdb_btn", width="stretch"):
        site_data = next((s for s in sites if s["name"] == selected_site), None)
        if site_data:
            with st.spinner(f"Querying PBDB near {html_module.escape(selected_site)}..."):
                fossils = _fetch_pbdb_nearby(site_data["lat"], site_data["lon"], radius_km=50)

            if fossils:
                st.success(f"Found {len(fossils)} fossil occurrences near {html_module.escape(selected_site)}.")

                fc1, fc2 = st.columns(2)
                with fc1:
                    st.metric("Fossil Occurrences", len(fossils))
                with fc2:
                    taxa = set(f.get("tna", "") for f in fossils if f.get("tna"))
                    st.metric("Unique Taxa", len(taxa))

                fossil_rows = []
                for f in fossils[:200]:
                    fossil_rows.append({
                        "Taxon": f.get("tna", "Unknown"),
                        "Early Interval": f.get("oei", ""),
                        "Late Interval": f.get("oli", ""),
                        "Lat": f.get("lat"),
                        "Lon": f.get("lng"),
                    })
                df_fossils = pd.DataFrame(fossil_rows)
                st.dataframe(df_fossils, width="stretch", hide_index=True)

                # Fossil CSV download
                csv_fossil_buf = io.StringIO()
                df_fossils.to_csv(csv_fossil_buf, index=False)
                st.download_button(
                    f"Download {len(fossil_rows)} Fossils (CSV)",
                    data=csv_fossil_buf.getvalue(),
                    file_name=f"pbdb_near_{selected_site.replace(' ', '_')}.csv",
                    mime="text/csv",
                    key="dino_pbdb_csv_download",
                )
            else:
                st.warning(
                    f"No PBDB fossil records found within 50 km of {html_module.escape(selected_site)}. "
                    "PBDB coverage varies by region."
                )
