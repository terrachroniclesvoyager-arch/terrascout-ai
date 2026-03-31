# -*- coding: utf-8 -*-
"""
Submarines & Deep Sea Explorer module for TerraScout AI.
Curated database of submarine bases, deep ocean trenches, famous wrecks,
hydrothermal vents, underwater cables, canyons, research stations, and more.
All data is from public records and presented for EDUCATIONAL purposes.
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
# DATA: 10 MAP MODES WITH CURATED LOCATIONS
# ===================================================================

# ---------------------------------------------------------------
# 1. WORLD'S DEEPEST OCEAN TRENCHES (30 locations)
# ---------------------------------------------------------------
DEEPEST_OCEAN_TRENCHES = [
    {"name": "Mariana Trench - Challenger Deep", "lat": 11.3493, "lon": 142.1996,
     "country": "Pacific Ocean", "depth_m": 10994,
     "notes": "Deepest known point on Earth at 10,994 m. First reached by Jacques Piccard and Don Walsh in the bathyscaphe Trieste in 1960."},
    {"name": "Tonga Trench - Horizon Deep", "lat": -23.2500, "lon": -174.7200,
     "country": "Pacific Ocean", "depth_m": 10823,
     "notes": "Second deepest point on Earth at 10,823 m. Located in the South Pacific between Tonga and New Zealand."},
    {"name": "Philippine Trench - Galathea Deep", "lat": 7.0000, "lon": 126.5000,
     "country": "Pacific Ocean", "depth_m": 10540,
     "notes": "Third deepest ocean trench at 10,540 m. Named after the Danish research vessel Galathea which surveyed it in 1951."},
    {"name": "Kuril-Kamchatka Trench", "lat": 44.0000, "lon": 150.3400,
     "country": "Pacific Ocean", "depth_m": 10542,
     "notes": "Deep trench in the northwest Pacific, 10,542 m deep. Runs from Kamchatka Peninsula along the Kuril Islands to Hokkaido."},
    {"name": "Kermadec Trench", "lat": -30.0000, "lon": -176.5000,
     "country": "Pacific Ocean", "depth_m": 10047,
     "notes": "Over 10,047 m deep in the South Pacific. Extends from the Louisville Seamount Chain to the Hikurangi Plateau near New Zealand."},
    {"name": "Japan Trench", "lat": 36.0000, "lon": 142.7000,
     "country": "Pacific Ocean", "depth_m": 9810,
     "notes": "9,810 m deep trench east of Japan. The 2011 Tohoku earthquake (M9.1) was generated along this subduction zone."},
    {"name": "Izu-Bonin Trench", "lat": 29.3300, "lon": 142.2100,
     "country": "Pacific Ocean", "depth_m": 9780,
     "notes": "9,780 m deep trench extending south from Japan. Part of the Izu-Bonin-Mariana arc system stretching 2,800 km."},
    {"name": "Puerto Rico Trench - Brownson Deep", "lat": 19.7133, "lon": -67.2167,
     "country": "Atlantic Ocean", "depth_m": 8376,
     "notes": "Deepest point in the Atlantic Ocean at 8,376 m. Located at the boundary of the Caribbean and North American plates."},
    {"name": "South Sandwich Trench - Meteor Deep", "lat": -55.2500, "lon": -25.9167,
     "country": "Atlantic Ocean", "depth_m": 8264,
     "notes": "Deepest point in the South Atlantic at 8,264 m. Associated with the Scotia Arc and Antarctic tectonic plate boundary."},
    {"name": "Peru-Chile Trench - Atacama Trench", "lat": -23.3500, "lon": -71.3667,
     "country": "Pacific Ocean", "depth_m": 8065,
     "notes": "8,065 m deep trench running along the western coast of South America. Nearly 5,900 km long, one of the longest ocean trenches."},
    {"name": "Aleutian Trench", "lat": 51.0000, "lon": -177.0000,
     "country": "Pacific Ocean", "depth_m": 7679,
     "notes": "7,679 m deep trench stretching 3,400 km along the Aleutian Islands. Formed by the Pacific plate subducting under the North American plate."},
    {"name": "Java Trench - Sunda Trench", "lat": -10.3800, "lon": 109.9700,
     "country": "Indian Ocean", "depth_m": 7725,
     "notes": "Deepest point in the Indian Ocean at 7,725 m. Stretches 3,200 km from Myanmar to Sumba Island along the Indonesian archipelago."},
    {"name": "New Hebrides Trench", "lat": -20.0000, "lon": 168.6667,
     "country": "Pacific Ocean", "depth_m": 7628,
     "notes": "7,628 m deep trench in the southwestern Pacific near Vanuatu. Active subduction zone producing frequent seismic activity."},
    {"name": "Ryukyu Trench", "lat": 25.0000, "lon": 128.0000,
     "country": "Pacific Ocean", "depth_m": 7507,
     "notes": "7,507 m deep trench stretching from Japan to Taiwan along the Ryukyu Islands. Formed by the Philippine Sea plate subducting westward."},
    {"name": "Yap Trench", "lat": 8.5000, "lon": 138.5000,
     "country": "Pacific Ocean", "depth_m": 8527,
     "notes": "8,527 m deep trench between the Yap Islands and Palau. One of the deeper and less explored trenches in the western Pacific."},
    {"name": "Cayman Trough", "lat": 18.2000, "lon": -80.0000,
     "country": "Caribbean Sea", "depth_m": 7686,
     "notes": "Deepest point in the Caribbean Sea at 7,686 m. Contains the world's deepest known hydrothermal vents at the Beebe Vent Field."},
    {"name": "Diamantina Trench", "lat": -35.0000, "lon": 104.0000,
     "country": "Indian Ocean", "depth_m": 8047,
     "notes": "8,047 m deep fracture zone in the eastern Indian Ocean between Australia and Antarctica. Among the least explored deep sea features."},
    {"name": "Manila Trench", "lat": 16.0000, "lon": 118.0000,
     "country": "Pacific Ocean", "depth_m": 5400,
     "notes": "5,400 m deep trench in the South China Sea west of Luzon. Poses a significant tsunami hazard to the Philippines and surrounding nations."},
    {"name": "Romanche Trench", "lat": 0.2667, "lon": -18.4167,
     "country": "Atlantic Ocean", "depth_m": 7758,
     "notes": "7,758 m deep gap in the Mid-Atlantic Ridge near the equator. Allows deep cold water to flow between the western and eastern Atlantic basins."},
    {"name": "Hikurangi Trench", "lat": -40.0000, "lon": 178.5000,
     "country": "Pacific Ocean", "depth_m": 3000,
     "notes": "Subduction trench east of New Zealand's North Island reaching 3,000 m. Capable of producing M8+ earthquakes and tsunamis."},
    {"name": "Bougainville Trench", "lat": -6.0000, "lon": 155.0000,
     "country": "Pacific Ocean", "depth_m": 9140,
     "notes": "9,140 m deep trench north of the Solomon Islands. Part of the complex tectonic boundary between the Pacific and Australian plates."},
    {"name": "New Britain Trench", "lat": -6.3000, "lon": 152.5000,
     "country": "Pacific Ocean", "depth_m": 8320,
     "notes": "8,320 m deep trench near Papua New Guinea. One of the most seismically active regions on Earth with frequent deep earthquakes."},
    {"name": "Palau Trench", "lat": 7.8000, "lon": 134.8000,
     "country": "Pacific Ocean", "depth_m": 8054,
     "notes": "8,054 m deep trench east of Palau. Relatively short and narrow compared to other western Pacific trenches."},
    {"name": "Vityaz Deep (Tonga Trench)", "lat": -15.8500, "lon": -173.2000,
     "country": "Pacific Ocean", "depth_m": 10882,
     "notes": "10,882 m sounding recorded by the Soviet vessel Vityaz in 1957. Some measurements suggest depths rivaling the Challenger Deep."},
    {"name": "Middle America Trench", "lat": 14.0000, "lon": -93.0000,
     "country": "Pacific Ocean", "depth_m": 6669,
     "notes": "6,669 m deep trench off the Pacific coast of Central America. Source of many devastating earthquakes affecting Mexico and Central America."},
    {"name": "Hjort Trench", "lat": -56.0000, "lon": 163.0000,
     "country": "Pacific Ocean", "depth_m": 6300,
     "notes": "6,300 m deep trench south of New Zealand near the Macquarie Ridge. One of the southernmost deep ocean trenches in the Pacific."},
    {"name": "Weber Deep", "lat": -7.5000, "lon": 131.0000,
     "country": "Indian Ocean", "depth_m": 7440,
     "notes": "7,440 m deep basin within the Banda Sea, Indonesia. The deepest point in any marginal sea on Earth."},
    {"name": "Hellenic Trench", "lat": 36.0000, "lon": 22.0000,
     "country": "Mediterranean Sea", "depth_m": 5121,
     "notes": "5,121 m deep trench south of Greece. Deepest point in the Mediterranean Sea, associated with the African plate subducting under the Aegean."},
    {"name": "Cedros Trench", "lat": 28.0000, "lon": -115.5000,
     "country": "Pacific Ocean", "depth_m": 4800,
     "notes": "4,800 m deep trench off Baja California, Mexico. Remnant of a former subduction zone now largely replaced by the San Andreas transform boundary."},
    {"name": "Emden Deep (Philippine Trench)", "lat": 5.5000, "lon": 126.5800,
     "country": "Pacific Ocean", "depth_m": 10497,
     "notes": "10,497 m deep point in the Philippine Trench, named after the German cruiser SMS Emden. Among the deepest spots on the planet."},
]

# ---------------------------------------------------------------
# 2. SUBMARINE NAVAL BASES (30 locations)
# ---------------------------------------------------------------
SUBMARINE_NAVAL_BASES = [
    {"name": "Naval Submarine Base New London (Groton)", "lat": 41.3868, "lon": -72.0896,
     "country": "United States", "year": "1868",
     "notes": "Home of the Submarine Force and the oldest submarine base in the US. Known as the Submarine Capital of the World."},
    {"name": "Kings Bay Naval Submarine Base", "lat": 30.7966, "lon": -81.5645,
     "country": "United States", "year": "1979",
     "notes": "Home port for the Atlantic Fleet's Trident ballistic missile submarines (Ohio class SSBNs). Strategic nuclear deterrence base."},
    {"name": "Naval Base Kitsap - Bangor", "lat": 47.7175, "lon": -122.7136,
     "country": "United States", "year": "1977",
     "notes": "Pacific Fleet Trident submarine base on Hood Canal, Washington. Houses the largest single stockpile of nuclear warheads in the US."},
    {"name": "Pearl Harbor Naval Shipyard", "lat": 21.3546, "lon": -157.9602,
     "country": "United States", "year": "1908",
     "notes": "Major Pacific submarine maintenance facility. Home to several Los Angeles-class attack submarines and the Pacific submarine fleet."},
    {"name": "HMNB Clyde (Faslane)", "lat": 56.0675, "lon": -4.8194,
     "country": "United Kingdom", "year": "1966",
     "notes": "Home of the UK's Trident nuclear deterrent. Base for all Royal Navy submarines including Vanguard-class SSBNs on the Gare Loch."},
    {"name": "Ile Longue", "lat": 48.3022, "lon": -4.5061,
     "country": "France", "year": "1970",
     "notes": "French Navy base for the Force de dissuasion nucleaire on the Crozon Peninsula, Brittany. Home to Le Triomphant-class SSBNs."},
    {"name": "Gadzhiyevo (Sayda Bay)", "lat": 69.2500, "lon": 33.3167,
     "country": "Russia", "year": "1956",
     "notes": "Major Northern Fleet nuclear submarine base on the Kola Peninsula above the Arctic Circle. Home to Delta IV and Borei-class SSBNs."},
    {"name": "Vilyuchinsk", "lat": 52.9333, "lon": 158.4000,
     "country": "Russia", "year": "1938",
     "notes": "Pacific Fleet submarine base on the Kamchatka Peninsula. Houses both nuclear attack and ballistic missile submarines."},
    {"name": "Yulin Naval Base (Hainan)", "lat": 18.2167, "lon": 109.5500,
     "country": "China", "year": "2000",
     "notes": "Underground submarine base on Hainan Island with tunnels carved into coastal hills. Home to PLAN Jin-class SSBNs and Shang-class SSNs."},
    {"name": "Jianggezhuang Submarine Base", "lat": 36.1333, "lon": 120.6667,
     "country": "China", "year": "1960",
     "notes": "North Sea Fleet submarine base near Qingdao, Shandong Province. One of China's original nuclear submarine facilities."},
    {"name": "INS Visakhapatnam (Submarine Base)", "lat": 17.7000, "lon": 83.3000,
     "country": "India", "year": "1971",
     "notes": "Eastern Naval Command submarine base in Andhra Pradesh. Houses India's Kilo-class and Scorpene-class diesel-electric submarines."},
    {"name": "INS Kadamba (Karwar)", "lat": 14.8167, "lon": 74.1167,
     "country": "India", "year": "2005",
     "notes": "India's largest naval base on the western coast, Karnataka. Planned to host the Arihant-class nuclear ballistic missile submarines."},
    {"name": "Yokosuka Naval Base", "lat": 35.2833, "lon": 139.6500,
     "country": "Japan", "year": "1865",
     "notes": "Joint US-Japan naval facility in Tokyo Bay. Houses JMSDF Soryu and Taigei-class diesel-electric submarines alongside US Navy vessels."},
    {"name": "HMAS Stirling (Fleet Base West)", "lat": -32.2333, "lon": 115.6833,
     "country": "Australia", "year": "1978",
     "notes": "Principal base for the Royal Australian Navy's Collins-class submarines on Garden Island, Western Australia. Future AUKUS submarine base."},
    {"name": "Polyarny (Murmansk Oblast)", "lat": 69.2000, "lon": 33.4833,
     "country": "Russia", "year": "1933",
     "notes": "Historic Northern Fleet submarine base on the Kola Peninsula. Operational since WWII, key facility during the Cold War submarine arms race."},
    {"name": "Cam Ranh Bay (Naval Base)", "lat": 11.9000, "lon": 109.1500,
     "country": "Vietnam", "year": "1905",
     "notes": "Strategic deep-water port housing Vietnam's Kilo-class submarine fleet. Historically used by French, Japanese, American, and Soviet navies."},
    {"name": "Submarine Base Haakonsvern", "lat": 60.3167, "lon": 5.2000,
     "country": "Norway", "year": "1963",
     "notes": "Royal Norwegian Navy's main base near Bergen. Home to Ula-class and future Type 212CD submarines guarding the North Atlantic approaches."},
    {"name": "Naval Station Norfolk (Submarine Pier)", "lat": 36.9467, "lon": -76.3033,
     "country": "United States", "year": "1917",
     "notes": "World's largest naval station in Virginia. Hosts multiple Virginia-class fast attack submarines as part of Submarine Squadron 6."},
    {"name": "Severodvinsk Shipyard (Sevmash)", "lat": 64.5667, "lon": 39.8500,
     "country": "Russia", "year": "1936",
     "notes": "Russia's sole nuclear submarine construction facility on the White Sea. Built every Soviet/Russian nuclear submarine including Typhoon and Borei classes."},
    {"name": "Karlskrona Naval Base", "lat": 56.1617, "lon": 15.5833,
     "country": "Sweden", "year": "1680",
     "notes": "Swedish Navy submarine base and UNESCO World Heritage Site. Home to Gotland-class AIP submarines and the famous Whiskey on the Rocks incident site."},
    {"name": "Submarine Base La Spezia", "lat": 44.1000, "lon": 9.8167,
     "country": "Italy", "year": "1869",
     "notes": "Italian Navy submarine headquarters in Liguria. Base for Todaro-class (Type 212A) submarines and NATO submarine research center."},
    {"name": "Zhoushan Naval Base", "lat": 30.0000, "lon": 122.1000,
     "country": "China", "year": "1949",
     "notes": "East Sea Fleet submarine base in Zhejiang Province. Houses conventional submarines and supports operations in the East China Sea."},
    {"name": "Rota Naval Station", "lat": 36.6200, "lon": -6.3500,
     "country": "Spain", "year": "1955",
     "notes": "Joint US-Spanish naval base in Cadiz. Hosts US destroyer squadron and is a transit point for US and NATO submarines entering the Mediterranean."},
    {"name": "HMCS Esquimalt (CFB Esquimalt)", "lat": 48.4333, "lon": -123.4167,
     "country": "Canada", "year": "1865",
     "notes": "Royal Canadian Navy Pacific base near Victoria, BC. Home to Victoria-class (former Upholder) diesel-electric submarines."},
    {"name": "Jeju Naval Base", "lat": 33.2500, "lon": 126.5667,
     "country": "South Korea", "year": "2016",
     "notes": "Controversial new naval base on Jeju Island. Designed to host Son Won-il class (Type 214) and Dosan Ahn Changho class submarines."},
    {"name": "Submarine Base Devonport", "lat": 50.3833, "lon": -4.1833,
     "country": "United Kingdom", "year": "1691",
     "notes": "Royal Navy dockyard in Plymouth. Primary facility for nuclear submarine refitting and decommissioning, including Astute-class SSNs."},
    {"name": "Toulon Naval Base", "lat": 43.1167, "lon": 5.9333,
     "country": "France", "year": "1599",
     "notes": "French Mediterranean Fleet headquarters. Houses Rubis and Suffren-class nuclear attack submarines alongside the carrier Charles de Gaulle."},
    {"name": "Submarine Base Kure", "lat": 34.2333, "lon": 132.5667,
     "country": "Japan", "year": "1889",
     "notes": "JMSDF submarine repair and construction facility. Historic naval arsenal where the battleship Yamato was built during World War II."},
    {"name": "Submarine Base Mar del Plata", "lat": -38.0333, "lon": -57.5500,
     "country": "Argentina", "year": "1969",
     "notes": "Argentine Navy submarine base. Was home to ARA San Juan (S-42) which tragically sank in 2017 with 44 crew in the South Atlantic."},
    {"name": "Balaklava Submarine Base", "lat": 44.4983, "lon": 33.5964,
     "country": "Ukraine", "year": "1957",
     "notes": "Former secret Soviet underground submarine pen carved into a mountain in Crimea. Could shelter an entire submarine brigade from nuclear attack. Now a museum."},
]

# ---------------------------------------------------------------
# 3. FAMOUS SUBMARINE WRECKS (30 locations)
# ---------------------------------------------------------------
FAMOUS_SUBMARINE_WRECKS = [
    {"name": "RMS Titanic", "lat": 41.7325, "lon": -49.9469,
     "country": "Atlantic Ocean", "year": "1912",
     "notes": "Sank on maiden voyage after striking an iceberg. Found by Robert Ballard in 1985 at 3,784 m depth. Over 1,500 lives lost."},
    {"name": "USS Indianapolis (CA-35)", "lat": 12.0350, "lon": 134.8450,
     "country": "Pacific Ocean", "year": "1945",
     "notes": "Heavy cruiser torpedoed by I-58 after delivering atomic bomb components. 879 crew lost, many to shark attacks. Found in 2017 at 5,500 m."},
    {"name": "K-141 Kursk", "lat": 69.6167, "lon": 37.5833,
     "country": "Barents Sea", "year": "2000",
     "notes": "Oscar II-class nuclear submarine sank during naval exercises. Torpedo propellant explosion killed all 118 crew. Found at 107 m depth."},
    {"name": "USS Thresher (SSN-593)", "lat": 41.7500, "lon": -65.0167,
     "country": "Atlantic Ocean", "year": "1963",
     "notes": "First nuclear submarine lost at sea during deep-diving tests 350 km east of Cape Cod. All 129 crew lost at 2,560 m depth. Led to SUBSAFE program."},
    {"name": "USS Scorpion (SSN-589)", "lat": 32.9167, "lon": -33.1500,
     "country": "Atlantic Ocean", "year": "1968",
     "notes": "Skipjack-class nuclear submarine lost with 99 crew southwest of the Azores. Found at 3,050 m depth. Cause remains debated."},
    {"name": "K-129 (Soviet Golf II)", "lat": 40.1000, "lon": -179.9667,
     "country": "Pacific Ocean", "year": "1968",
     "notes": "Soviet ballistic missile submarine lost in the Pacific with 98 crew. Subject of the CIA's secret Project Azorian recovery attempt in 1974."},
    {"name": "ARA San Juan (S-42)", "lat": -46.4400, "lon": -59.7200,
     "country": "Atlantic Ocean", "year": "2017",
     "notes": "Argentine submarine lost with 44 crew in the South Atlantic. Found a year later at 907 m depth with implosion damage consistent with hull failure."},
    {"name": "HMS Thetis / Thunderbolt", "lat": 53.4333, "lon": -3.8667,
     "country": "Irish Sea", "year": "1939",
     "notes": "Sank during trials in Liverpool Bay killing 99. Raised, renamed HMS Thunderbolt, then sunk again by depth charges in 1943 off Sicily."},
    {"name": "U-869", "lat": 40.3167, "lon": -73.5667,
     "country": "Atlantic Ocean", "year": "1945",
     "notes": "German Type IXC/40 U-boat found off New Jersey in 1991 by divers John Chatterton and Richie Kohler. Subject of the book Shadow Divers."},
    {"name": "I-52 (Japanese Submarine)", "lat": 15.3167, "lon": -39.7833,
     "country": "Atlantic Ocean", "year": "1944",
     "notes": "Japanese cargo submarine sunk by US aircraft in the mid-Atlantic carrying gold and strategic materials. Found at 5,240 m in 1998."},
    {"name": "H.L. Hunley", "lat": 32.7200, "lon": -79.7700,
     "country": "Atlantic Ocean", "year": "1864",
     "notes": "Confederate submarine, first combat sub to sink an enemy vessel (USS Housatonic). Found in 1995 at 9 m depth off Charleston, SC. Now conserved."},
    {"name": "K-278 Komsomolets", "lat": 73.7167, "lon": 13.2667,
     "country": "Norwegian Sea", "year": "1989",
     "notes": "Soviet Mike-class nuclear submarine sank after fire. 42 of 69 crew died. Rests at 1,680 m with two nuclear torpedoes and a reactor."},
    {"name": "KRI Nanggala (402)", "lat": -7.3500, "lon": 115.3667,
     "country": "Bali Sea", "year": "2021",
     "notes": "Indonesian Type 209 submarine lost during torpedo drills with 53 crew. Found at 838 m depth broken into three sections."},
    {"name": "INS Dakar", "lat": 33.0000, "lon": 32.6667,
     "country": "Mediterranean Sea", "year": "1968",
     "notes": "Israeli submarine lost with 69 crew while transiting from UK to Haifa. Found in 1999 at 2,900 m depth between Crete and Cyprus."},
    {"name": "HMS Affray", "lat": 50.0667, "lon": -1.8333,
     "country": "English Channel", "year": "1951",
     "notes": "Last Royal Navy submarine lost at sea. Sank with 75 crew in the Hurd Deep. Found at 85 m depth with a broken snort mast."},
    {"name": "Surcouf (French Submarine)", "lat": 10.0000, "lon": -79.0000,
     "country": "Caribbean Sea", "year": "1942",
     "notes": "Largest submarine in the world at the time. Lost with 159 crew near the Panama Canal. Cause never determined, possibly rammed or bombed."},
    {"name": "USS Tang (SS-306)", "lat": 25.5000, "lon": 120.0000,
     "country": "Taiwan Strait", "year": "1944",
     "notes": "Most successful US submarine of WWII sunk by its own malfunctioning torpedo that circled back. 78 crew lost, 9 survived as POWs."},
    {"name": "U-505", "lat": 21.3000, "lon": -19.1833,
     "country": "Atlantic Ocean", "year": "1944",
     "notes": "German Type IXC U-boat captured by USS Guadalcanal task group off West Africa. Intelligence coup yielding Enigma materials. Now at Chicago museum."},
    {"name": "K-8 (Soviet November-class)", "lat": 48.3167, "lon": -20.2667,
     "country": "Bay of Biscay", "year": "1970",
     "notes": "Soviet nuclear submarine sank after fire during the Ocean-70 exercise. 52 of 125 crew lost. Rests at 4,680 m with two nuclear reactors."},
    {"name": "USS Wahoo (SS-238)", "lat": 43.5000, "lon": 141.5000,
     "country": "Sea of Japan", "year": "1943",
     "notes": "One of the top-scoring US submarines of WWII under Cmdr. Dudley 'Mush' Morton. Sunk by Japanese aircraft and surface vessels in La Perouse Strait."},
    {"name": "SMS UB-65 (Haunted U-boat)", "lat": 50.1000, "lon": -5.0000,
     "country": "Celtic Sea", "year": "1918",
     "notes": "German WWI U-boat infamous for alleged ghost sightings. Found capsized on the seafloor with no obvious cause of sinking."},
    {"name": "K-219 (Soviet Yankee-class)", "lat": 31.3000, "lon": -54.8000,
     "country": "Atlantic Ocean", "year": "1986",
     "notes": "Soviet SSBN suffered missile tube explosion east of Bermuda. 4 crew died. Scuttled and sank to 5,500 m with 16 nuclear missiles and 2 reactors."},
    {"name": "USS Squalus (SS-192)", "lat": 42.9167, "lon": -70.5333,
     "country": "Atlantic Ocean", "year": "1939",
     "notes": "Sank during test dive off New Hampshire when engine induction valve failed. 26 crew died. 33 survivors rescued by McCann Rescue Chamber."},
    {"name": "Minerve (S647)", "lat": 43.1333, "lon": 5.3667,
     "country": "Mediterranean Sea", "year": "1968",
     "notes": "French Daphne-class submarine lost off Toulon with 52 crew. Found in 2019 at 2,370 m depth after a 51-year search."},
    {"name": "ORP Orzel", "lat": 57.0000, "lon": 3.0000,
     "country": "North Sea", "year": "1940",
     "notes": "Polish submarine famed for its dramatic escape from internment in Estonia. Lost in the North Sea in June 1940 with 60 crew. Never found."},
    {"name": "U-47 (Gunther Prien)", "lat": 60.5000, "lon": -3.5000,
     "country": "North Atlantic", "year": "1941",
     "notes": "Famous German U-boat that penetrated Scapa Flow and sank HMS Royal Oak. Lost with 45 crew, likely depth charged by HMS Wolverine."},
    {"name": "K-159 (Soviet November-class)", "lat": 69.3833, "lon": 33.7333,
     "country": "Barents Sea", "year": "2003",
     "notes": "Decommissioned nuclear submarine sank while being towed to scrapping. 9 crew lost. Rests at 246 m with spent nuclear fuel still aboard."},
    {"name": "USS Grunion (SS-216)", "lat": 52.0000, "lon": -177.0000,
     "country": "Bering Sea", "year": "1942",
     "notes": "Gato-class submarine lost with 70 crew near Kiska Island in the Aleutians. Found in 2006 at 975 m depth by the sons of her commander."},
    {"name": "S-13 (Soviet Submarine)", "lat": 55.0700, "lon": 17.4167,
     "country": "Baltic Sea", "year": "1945",
     "notes": "Commanded by Alexander Marinesko, sank the Wilhelm Gustloff (9,000+ dead, worst maritime disaster) and the General von Steuben. Scrapped 1957."},
    {"name": "Dakar (ex-HMS Totem)", "lat": 33.0667, "lon": 32.5833,
     "country": "Mediterranean Sea", "year": "1968",
     "notes": "Former British T-class submarine transferred to Israel. Lost en route to Haifa in January 1968. Conning tower recovered, hull at 2,900 m."},
]

# ---------------------------------------------------------------
# 4. DEEP SEA EXPLORATION SITES (30 locations)
# ---------------------------------------------------------------
DEEP_SEA_EXPLORATION_SITES = [
    {"name": "Challenger Deep - Trieste Dive (1960)", "lat": 11.3493, "lon": 142.1996,
     "country": "Pacific Ocean", "year": "1960",
     "notes": "Jacques Piccard and Don Walsh reached the deepest point on Earth (10,916 m) in the bathyscaphe Trieste on January 23, 1960."},
    {"name": "Challenger Deep - Deepsea Challenger (2012)", "lat": 11.3493, "lon": 142.2000,
     "country": "Pacific Ocean", "year": "2012",
     "notes": "James Cameron made the first solo dive to the Challenger Deep reaching 10,908 m in the Deepsea Challenger submersible on March 26, 2012."},
    {"name": "Challenger Deep - Limiting Factor (2019)", "lat": 11.3493, "lon": 142.2000,
     "country": "Pacific Ocean", "year": "2019",
     "notes": "Victor Vescovo dove to 10,928 m in the DSV Limiting Factor, the deepest recorded dive in history. Part of the Five Deeps Expedition."},
    {"name": "RMS Titanic Discovery Site", "lat": 41.7260, "lon": -49.9470,
     "country": "Atlantic Ocean", "year": "1985",
     "notes": "Robert Ballard and Jean-Louis Michel discovered the Titanic wreck at 3,800 m using the Argo/ANGUS remote camera system on September 1, 1985."},
    {"name": "FAMOUS Mid-Atlantic Ridge", "lat": 36.8000, "lon": -33.2000,
     "country": "Atlantic Ocean", "year": "1974",
     "notes": "French-American Mid-Ocean Undersea Study. Alvin, Archimede, and Cyana made 44 dives exploring the rift valley of the Mid-Atlantic Ridge."},
    {"name": "Galapagos Rift Vent Discovery", "lat": 0.7933, "lon": -86.1367,
     "country": "Pacific Ocean", "year": "1977",
     "notes": "First hydrothermal vents discovered by the DSV Alvin in 1977. Revealed entirely new chemosynthetic ecosystems independent of sunlight."},
    {"name": "East Pacific Rise (21 deg N)", "lat": 21.0000, "lon": -109.1000,
     "country": "Pacific Ocean", "year": "1979",
     "notes": "First black smoker hydrothermal vents discovered. Water temperatures exceeding 350 deg C measured, rewriting understanding of ocean chemistry."},
    {"name": "Bismarck Wreck Site", "lat": 48.1700, "lon": -16.2000,
     "country": "Atlantic Ocean", "year": "1989",
     "notes": "Robert Ballard located the German battleship Bismarck at 4,791 m depth in the Atlantic, 960 km west of Brest, France."},
    {"name": "HMHS Britannic Wreck", "lat": 37.7283, "lon": 24.2850,
     "country": "Aegean Sea", "year": "1975",
     "notes": "Titanic's sister ship, sunk by mine or torpedo in 1916, explored by Jacques Cousteau in 1975. Largest ship on the seafloor at 120 m depth."},
    {"name": "USS Yorktown (CV-5) Discovery", "lat": 30.4667, "lon": -176.5667,
     "country": "Pacific Ocean", "year": "1998",
     "notes": "WWII carrier sunk at the Battle of Midway found by Robert Ballard at 5,000 m depth near Midway Atoll."},
    {"name": "Lost City Hydrothermal Field", "lat": 30.1242, "lon": -42.1188,
     "country": "Atlantic Ocean", "year": "2000",
     "notes": "Alkaline hydrothermal vent field discovered on the Atlantis Massif. Unique carbonate chimneys up to 60 m tall, some potentially billions of years old."},
    {"name": "Nereus Dive (Kermadec Trench)", "lat": -31.0000, "lon": -177.0000,
     "country": "Pacific Ocean", "year": "2009",
     "notes": "HROV Nereus reached 10,902 m in the Kermadec Trench, becoming the deepest-diving unmanned vehicle. Lost to implosion in 2014."},
    {"name": "Kaiko Dive (Challenger Deep)", "lat": 11.3492, "lon": 142.1992,
     "country": "Pacific Ocean", "year": "1995",
     "notes": "Japanese ROV Kaiko reached 10,911 m in the Challenger Deep, the first unmanned vehicle to reach the deepest point. Collected sediment samples."},
    {"name": "Deep Sea Drilling Project Site 504B", "lat": 1.2267, "lon": -83.7300,
     "country": "Pacific Ocean", "year": "1979",
     "notes": "Deepest ocean drill hole at the time, penetrating 2,111 m into ocean crust. Provided fundamental data on oceanic crustal structure."},
    {"name": "Ifremer Nautile - Mid-Atlantic Ridge", "lat": 23.3667, "lon": -44.9500,
     "country": "Atlantic Ocean", "year": "1985",
     "notes": "French submersible Nautile explored the Trans-Atlantic Geotraverse (TAG) hydrothermal mound, one of the largest known mineral deposits."},
    {"name": "Monterey Canyon Floor", "lat": 36.7000, "lon": -122.1833,
     "country": "Pacific Ocean", "year": "1992",
     "notes": "MBARI's ROV explorations since 1992 have documented thousands of new deep-sea species in this 3,600 m deep submarine canyon off California."},
    {"name": "Sirena Deep (Mariana Trench)", "lat": 11.3333, "lon": 142.5833,
     "country": "Pacific Ocean", "year": "2019",
     "notes": "Victor Vescovo dove to 10,714 m in the Sirena Deep, the second deepest point in the Mariana Trench, during the Five Deeps Expedition."},
    {"name": "Molloy Deep (Arctic Ocean)", "lat": 79.1500, "lon": 2.7833,
     "country": "Arctic Ocean", "year": "2019",
     "notes": "Victor Vescovo completed the deepest dive in the Arctic Ocean at 5,550 m in the Molloy Deep in the Fram Strait."},
    {"name": "Calypso Deep (Mediterranean)", "lat": 36.5000, "lon": 21.1167,
     "country": "Mediterranean Sea", "year": "2020",
     "notes": "Deepest point in the Mediterranean at 5,109 m southwest of Pylos, Greece. Named after Jacques Cousteau's research vessel."},
    {"name": "Puerto Rico Trench - Five Deeps", "lat": 19.7000, "lon": -67.2500,
     "country": "Atlantic Ocean", "year": "2019",
     "notes": "Vescovo dove to 8,376 m in the Brownson Deep, the deepest point in the Atlantic. Discovered plastic waste at the bottom."},
    {"name": "South Sandwich Trench - Five Deeps", "lat": -60.3833, "lon": -25.5667,
     "country": "Southern Ocean", "year": "2019",
     "notes": "Vescovo reached 7,433 m in the South Sandwich Trench, the deepest point in the Southern Ocean. First manned dive to this depth."},
    {"name": "Java Trench - Five Deeps", "lat": -10.1833, "lon": 110.0000,
     "country": "Indian Ocean", "year": "2019",
     "notes": "Deepest dive in the Indian Ocean at 7,192 m. Vescovo discovered the trench was deeper than previously measured by 400+ meters."},
    {"name": "Alvin Submersible 5000th Dive", "lat": 9.8333, "lon": -104.2667,
     "country": "Pacific Ocean", "year": "2018",
     "notes": "DSV Alvin, the world's most prolific research submersible, completed its 5,000th dive near the East Pacific Rise. Operating since 1964."},
    {"name": "Deepsea Challenger Sea Trials", "lat": -12.0000, "lon": 145.0000,
     "country": "Coral Sea", "year": "2012",
     "notes": "James Cameron's Deepsea Challenger conducted sea trials in the New Britain Trench near PNG, reaching 8,221 m before the Challenger Deep dive."},
    {"name": "HMS Erebus Discovery", "lat": 68.9167, "lon": -98.9333,
     "country": "Arctic Ocean", "year": "2014",
     "notes": "Sir John Franklin's lost expedition ship discovered in Nunavut waters at just 11 m depth. One of the greatest archaeological finds in maritime history."},
    {"name": "Mid-Cayman Rise Vents", "lat": 18.3750, "lon": -81.7333,
     "country": "Caribbean Sea", "year": "2010",
     "notes": "Deepest known hydrothermal vents at 4,960 m on an ultra-slow spreading ridge. Beebe Vent Field waters exceed 401 deg C, hottest recorded."},
    {"name": "Shinkai 6500 Deep Dive", "lat": 27.0000, "lon": 143.6333,
     "country": "Pacific Ocean", "year": "1989",
     "notes": "Japanese submersible Shinkai 6500 achieved its record depth of 6,527 m in the Japan Trench. Most capable crewed research sub for two decades."},
    {"name": "Jiaolong Deep Dive", "lat": 11.3500, "lon": 142.2000,
     "country": "Pacific Ocean", "year": "2012",
     "notes": "Chinese submersible Jiaolong reached 7,062 m in the Mariana Trench, making China the fifth nation to dive below 3,500 m with a crewed vessel."},
    {"name": "Fendouzhe Record Dive", "lat": 11.3493, "lon": 142.1996,
     "country": "Pacific Ocean", "year": "2020",
     "notes": "Chinese submersible Fendouzhe (Striver) reached 10,909 m in the Challenger Deep. Live-streamed on Chinese state television."},
    {"name": "OceanGate Titan Implosion Site", "lat": 41.7264, "lon": -49.9472,
     "country": "Atlantic Ocean", "year": "2023",
     "notes": "OceanGate's Titan submersible suffered catastrophic implosion at 3,800 m near the Titanic wreck. All 5 occupants lost. Raised safety regulation debates."},
]

# ---------------------------------------------------------------
# 5. HYDROTHERMAL VENT FIELDS (30 locations)
# ---------------------------------------------------------------
HYDROTHERMAL_VENT_FIELDS = [
    {"name": "Galapagos Rift Vents", "lat": 0.7933, "lon": -86.1367,
     "country": "Pacific Ocean", "year": "1977",
     "notes": "First hydrothermal vents ever discovered. Giant tube worms, clams, and unique chemosynthetic communities found thriving without sunlight."},
    {"name": "East Pacific Rise 21N Black Smokers", "lat": 21.0000, "lon": -109.1000,
     "country": "Pacific Ocean", "year": "1979",
     "notes": "First black smoker chimneys observed. Superheated water at 350+ deg C laden with metal sulfides creating mineral-rich deposits."},
    {"name": "Lost City Hydrothermal Field", "lat": 30.1242, "lon": -42.1188,
     "country": "Atlantic Ocean", "year": "2000",
     "notes": "Unique alkaline vent field on the Atlantis Massif. Carbonate chimneys up to 60 m tall. May represent conditions for the origin of life."},
    {"name": "TAG Hydrothermal Field", "lat": 26.1367, "lon": -44.8267,
     "country": "Atlantic Ocean", "year": "1985",
     "notes": "Trans-Atlantic Geotraverse mound on the Mid-Atlantic Ridge. One of the best-studied vent fields with massive sulfide deposits."},
    {"name": "Beebe Vent Field (Cayman Trough)", "lat": 18.3725, "lon": -81.7333,
     "country": "Caribbean Sea", "year": "2010",
     "notes": "Deepest known volcanic vents at 4,960 m on the Mid-Cayman Rise. Water temperatures reach 401 deg C, the hottest ever recorded."},
    {"name": "Kairei Field (Central Indian Ridge)", "lat": -25.3167, "lon": 70.0333,
     "country": "Indian Ocean", "year": "2000",
     "notes": "First hydrothermal vents discovered in the Indian Ocean on the Central Indian Ridge at 2,450 m depth. Unique vent fauna."},
    {"name": "Loki's Castle", "lat": 73.5633, "lon": 8.1583,
     "country": "Arctic Ocean", "year": "2008",
     "notes": "Northernmost black smoker field at 2,352 m on the Arctic Mid-Ocean Ridge. Named for its castle-like chimney structures."},
    {"name": "Rainbow Vent Field", "lat": 36.2267, "lon": -33.9017,
     "country": "Atlantic Ocean", "year": "1997",
     "notes": "Ultramafic-hosted vent field on the Mid-Atlantic Ridge at 2,300 m. Produces hydrogen-rich fluids and unusual mineral assemblages."},
    {"name": "Brothers Volcano Vents", "lat": -34.8617, "lon": -179.0617,
     "country": "Pacific Ocean", "year": "2003",
     "notes": "Hydrothermal vents inside an active submarine volcano on the Kermadec Arc. Unique dual vent systems on cone and caldera walls."},
    {"name": "East Manus Basin (PACMANUS)", "lat": -3.7167, "lon": 151.6667,
     "country": "Pacific Ocean", "year": "1991",
     "notes": "Felsic-hosted vent field in the Bismarck Sea near Papua New Guinea. Rich polymetallic sulfide deposits have attracted mining interest."},
    {"name": "Guaymas Basin", "lat": 27.0083, "lon": -111.4083,
     "country": "Pacific Ocean", "year": "1982",
     "notes": "Unique sediment-covered vents in the Gulf of California at 2,000 m. Organic-rich sediments create petroleum-like hydrocarbons at vent sites."},
    {"name": "Endeavour Segment Vents", "lat": 47.9500, "lon": -129.0833,
     "country": "Pacific Ocean", "year": "1984",
     "notes": "Major vent field on the Juan de Fuca Ridge with five active vent clusters. Designated a Marine Protected Area by Canada in 2003."},
    {"name": "Solwara 1", "lat": -3.7833, "lon": 152.1000,
     "country": "Pacific Ocean", "year": "2005",
     "notes": "First proposed deep-sea mining site for hydrothermal sulfide deposits off Papua New Guinea. Nautilus Minerals project was highly controversial."},
    {"name": "Snake Pit Vent Field", "lat": 23.3667, "lon": -44.9500,
     "country": "Atlantic Ocean", "year": "1985",
     "notes": "Named for its dense populations of vent-endemic snakefish. Located on the Mid-Atlantic Ridge at 3,460 m depth."},
    {"name": "Logatchev Vent Field", "lat": 14.7517, "lon": -44.9783,
     "country": "Atlantic Ocean", "year": "1993",
     "notes": "Ultramafic-hosted vent field on the Mid-Atlantic Ridge at 3,000 m. Produces high concentrations of hydrogen and methane."},
    {"name": "East Scotia Ridge E2/E9 Vents", "lat": -56.0833, "lon": -30.1667,
     "country": "Southern Ocean", "year": "2009",
     "notes": "First deep-sea vents discovered in the Southern Ocean. Harbors unique species found nowhere else, including the Hoff yeti crab."},
    {"name": "Longqi (Dragon Flag) Vent Field", "lat": -37.7833, "lon": 49.6500,
     "country": "Indian Ocean", "year": "2007",
     "notes": "Vent field on the Southwest Indian Ridge at 2,800 m. Approved as a Chinese deep-sea mining exploration area by the ISA."},
    {"name": "Menez Gwen Vent Field", "lat": 37.8417, "lon": -31.5167,
     "country": "Atlantic Ocean", "year": "1994",
     "notes": "Shallow vent field at 840 m on the Mid-Atlantic Ridge near the Azores. Unique due to its relatively shallow depth."},
    {"name": "Lucky Strike Vent Field", "lat": 37.2917, "lon": -32.2750,
     "country": "Atlantic Ocean", "year": "1993",
     "notes": "Large vent field on the Mid-Atlantic Ridge near the Azores at 1,700 m. Named by Portuguese scientists referencing a popular cigarette brand."},
    {"name": "Niua South Volcano Vents", "lat": -15.3667, "lon": -173.7500,
     "country": "Pacific Ocean", "year": "2008",
     "notes": "Hydrothermal vents on a submarine volcano in the Tonga Arc. Molten sulfur lakes and liquid CO2 pools observed at 1,177 m depth."},
    {"name": "Von Damm Vent Field", "lat": 18.3750, "lon": -81.8000,
     "country": "Caribbean Sea", "year": "2010",
     "notes": "Named after the late oceanographer Karen Von Damm. Located 20 km from the Beebe Vents on the Mid-Cayman Rise at 2,300 m depth."},
    {"name": "Ashadze Vent Field", "lat": 12.9733, "lon": -44.8633,
     "country": "Atlantic Ocean", "year": "2007",
     "notes": "Deepest known vents on the Mid-Atlantic Ridge at 4,080 m. Two distinct vent sites (Ashadze-1 and Ashadze-2) with unique fauna."},
    {"name": "Kermadec Arc White Island Vents", "lat": -37.5200, "lon": 177.1800,
     "country": "Pacific Ocean", "year": "1999",
     "notes": "Shallow hydrothermal vents associated with White Island (Whakaari) volcano. Active degassing and mineral deposition in coastal waters."},
    {"name": "Gorda Ridge Vents", "lat": 42.6833, "lon": -126.7833,
     "country": "Pacific Ocean", "year": "1996",
     "notes": "Sea Cliff Hydrothermal Field on the Gorda Ridge off northern California at 2,700 m. Eruptions monitored by NOAA's Vents program."},
    {"name": "Semenov Vent Field", "lat": 13.5133, "lon": -44.9617,
     "country": "Atlantic Ocean", "year": "2007",
     "notes": "Large vent field on the Mid-Atlantic Ridge at 2,700 m with both active and inactive sulfide mounds. Named after Russian geologist."},
    {"name": "Edmond Vent Field", "lat": -23.8833, "lon": 69.5833,
     "country": "Indian Ocean", "year": "2001",
     "notes": "Vent field on the Central Indian Ridge at 3,290 m depth. Named after MIT oceanographer John Edmond who pioneered hydrothermal chemistry."},
    {"name": "Aurora Vent Field", "lat": 82.9000, "lon": 6.2333,
     "country": "Arctic Ocean", "year": "2014",
     "notes": "Discovered on the ultraslow-spreading Gakkel Ridge beneath the Arctic ice at 3,900 m. One of the most remote vent fields known."},
    {"name": "Piccard Vent Field", "lat": 18.3333, "lon": -81.7167,
     "country": "Caribbean Sea", "year": "2010",
     "notes": "Alternative name for the Beebe Vent Field. Deepest known vents, located on the ultra-slow spreading Mid-Cayman Rise."},
    {"name": "Nibelungen Vent Field", "lat": 8.3000, "lon": -13.5167,
     "country": "Atlantic Ocean", "year": "2006",
     "notes": "Ultramafic-hosted vent site at 2,900 m on the southern Mid-Atlantic Ridge. Low-temperature venting with unique mineralogy."},
    {"name": "Mariner Vent Field (Lau Basin)", "lat": -22.1833, "lon": -176.6017,
     "country": "Pacific Ocean", "year": "2004",
     "notes": "Highly acidic vent fluids (pH 2) on the Valu Fa Ridge in the Lau back-arc basin at 1,910 m. Among the most corrosive vents known."},
]

# ---------------------------------------------------------------
# 6. UNDERWATER CABLE ROUTES (25 locations)
# ---------------------------------------------------------------
UNDERWATER_CABLE_ROUTES = [
    {"name": "TAT-14 Transatlantic Cable (US Landing)", "lat": 40.9500, "lon": -72.1667,
     "country": "United States", "year": "2001",
     "notes": "Fiber-optic cable connecting Tuckerton, NJ to UK/France/Germany/Denmark/Netherlands. 15,428 km total. Carried 3.2 Tbps capacity."},
    {"name": "TAT-14 Transatlantic (UK Landing)", "lat": 53.2000, "lon": 0.3167,
     "country": "United Kingdom", "year": "2001",
     "notes": "Bude, Cornwall landing point for TAT-14. Part of the backbone connecting North America to Europe since the first telegraph cable in 1858."},
    {"name": "MAREA Cable (US Landing)", "lat": 39.2833, "lon": -74.5667,
     "country": "United States", "year": "2018",
     "notes": "Microsoft and Facebook's 6,600 km transatlantic cable. Virginia Beach to Bilbao, Spain. 200 Tbps capacity, one of the highest-capacity cables."},
    {"name": "MAREA Cable (Spain Landing)", "lat": 43.2633, "lon": -2.9350,
     "country": "Spain", "year": "2018",
     "notes": "Bilbao landing point for the MAREA subsea cable. Laid at depths up to 5,182 m, among the deepest transatlantic cables."},
    {"name": "SEA-ME-WE 3 (Singapore Hub)", "lat": 1.2667, "lon": 103.8333,
     "country": "Singapore", "year": "1999",
     "notes": "One of the world's longest cables at 39,000 km connecting 33 countries. Runs from Germany through the Mediterranean, Red Sea, and Indian Ocean."},
    {"name": "SEA-ME-WE 3 (Suez Canal Crossing)", "lat": 30.0000, "lon": 32.5667,
     "country": "Egypt", "year": "1999",
     "notes": "Critical chokepoint where multiple cables transit the Suez area. Damage here can disrupt communications between Asia and Europe."},
    {"name": "FASTER Cable (US Landing)", "lat": 36.9667, "lon": -122.0333,
     "country": "United States", "year": "2016",
     "notes": "Google consortium cable connecting Oregon to Japan. 11,629 km with 60 Tbps capacity. One of the highest-capacity trans-Pacific cables."},
    {"name": "FASTER Cable (Japan Landing)", "lat": 34.6833, "lon": 135.1833,
     "country": "Japan", "year": "2016",
     "notes": "Shima, Mie Prefecture landing point. Cable connects to Taiwan via a branching unit in the Pacific. 6 fiber pairs."},
    {"name": "Southern Cross Cable (Sydney)", "lat": -33.7833, "lon": 151.2833,
     "country": "Australia", "year": "2000",
     "notes": "30,500 km cable connecting Australia to New Zealand, Fiji, and the US West Coast. Backbone of Australia's international connectivity."},
    {"name": "GRACE Hopper Cable (US Landing)", "lat": 39.2833, "lon": -74.5667,
     "country": "United States", "year": "2022",
     "notes": "Google's transatlantic cable from New York to UK and Spain. Named after computer pioneer Grace Hopper. 16 fiber pairs, 340 Tbps capacity."},
    {"name": "Atlantic Crossing 1 (AC-1) US End", "lat": 40.0167, "lon": -73.8500,
     "country": "United States", "year": "1998",
     "notes": "Early high-capacity transatlantic cable from Brookhaven, NY to multiple European destinations. 14,000 km with 80 Gbps per fiber pair."},
    {"name": "FLAG Atlantic (FA-1) Landing", "lat": 40.7167, "lon": -73.7667,
     "country": "United States", "year": "2001",
     "notes": "Fiber-optic Link Around the Globe (FLAG) Atlantic segment. Part of a 28,000 km cable system circling the globe."},
    {"name": "Africa Coast to Europe (ACE)", "lat": 5.3167, "lon": -4.0167,
     "country": "Ivory Coast", "year": "2012",
     "notes": "17,000 km submarine cable serving 24 countries along the west coast of Africa to France. Critical connectivity for West African nations."},
    {"name": "Asia-America Gateway (AAG)", "lat": 10.7833, "lon": 106.7000,
     "country": "Vietnam", "year": "2009",
     "notes": "20,000 km cable connecting Southeast Asia to the US via Malaysia, Singapore, Thailand, Brunei, Vietnam, Philippines, and Hong Kong."},
    {"name": "JUPITER Cable (Japan-US)", "lat": 35.0000, "lon": 136.8333,
     "country": "Japan", "year": "2020",
     "notes": "Google and Facebook's trans-Pacific cable. Connects Chikura and Shima, Japan to Los Angeles and Eureka, California. 60 Tbps capacity."},
    {"name": "Dunant Cable (France Landing)", "lat": 47.2667, "lon": -2.2167,
     "country": "France", "year": "2020",
     "notes": "Google's 6,400 km transatlantic cable named after Henry Dunant. Saint-Hilaire-de-Riez, France to Virginia Beach, US. 250 Tbps."},
    {"name": "EASSy Cable (Mombasa)", "lat": -4.0500, "lon": 39.6667,
     "country": "Kenya", "year": "2010",
     "notes": "Eastern Africa Submarine System cable connecting South Africa to Sudan along the east African coast. 10,000 km serving 10 countries."},
    {"name": "Pacific Crossing 1 (PC-1)", "lat": 35.2333, "lon": 139.8167,
     "country": "Japan", "year": "2000",
     "notes": "21,000 km trans-Pacific cable from Shima, Japan to Harbor Pointe, Washington and Grover Beach, California. Early broadband trans-Pacific link."},
    {"name": "AJC (Australia-Japan Cable)", "lat": -28.7833, "lon": 153.6167,
     "country": "Australia", "year": "2001",
     "notes": "12,700 km cable connecting Sydney, Australia to multiple Japanese landing points. Critical for Australia-Asia data traffic."},
    {"name": "Hibernia Atlantic (US Landing)", "lat": 41.1833, "lon": -72.1500,
     "country": "United States", "year": "2015",
     "notes": "Low-latency transatlantic cable used by financial traders. Connects Halifax, Canada to Brean, UK. Optimized for minimal signal delay."},
    {"name": "TGN-Atlantic (UK Landing)", "lat": 51.3500, "lon": 1.4333,
     "country": "United Kingdom", "year": "2001",
     "notes": "Telia Global Network Atlantic cable landing at Whitstable, Kent. Part of the global backbone connecting Americas, Europe, and Asia."},
    {"name": "WACS Cable (Cape Town)", "lat": -33.9167, "lon": 18.4167,
     "country": "South Africa", "year": "2012",
     "notes": "West Africa Cable System: 14,530 km connecting South Africa to the UK via 14 West African countries. 5.12 Tbps design capacity."},
    {"name": "2Africa Cable (Egypt Hub)", "lat": 31.2167, "lon": 29.9500,
     "country": "Egypt", "year": "2024",
     "notes": "Meta's 45,000 km cable circling Africa with extensions to Europe and Asia. One of the longest subsea cables ever deployed."},
    {"name": "Equiano Cable (Nigeria)", "lat": 6.4333, "lon": 3.4167,
     "country": "Nigeria", "year": "2022",
     "notes": "Google's cable from Portugal to South Africa via West Africa. Named after Olaudah Equiano. 12 fiber pairs, 144 Tbps capacity."},
    {"name": "EllaLink Cable (Brazil)", "lat": -3.7333, "lon": -38.5167,
     "country": "Brazil", "year": "2021",
     "notes": "6,000 km direct cable from Fortaleza, Brazil to Sines, Portugal. First direct high-capacity link between South America and Europe."},
]

# ---------------------------------------------------------------
# 7. SUBMARINE CANYON SYSTEMS (25 locations)
# ---------------------------------------------------------------
SUBMARINE_CANYON_SYSTEMS = [
    {"name": "Monterey Canyon", "lat": 36.7869, "lon": -121.9014,
     "country": "United States", "year": "1891",
     "notes": "Largest submarine canyon along the US Pacific coast, rivaling the Grand Canyon in scale. Reaches 3,600 m depth. MBARI research hub."},
    {"name": "Hudson Canyon", "lat": 39.0000, "lon": -72.5000,
     "country": "United States", "year": "1930",
     "notes": "Largest submarine canyon in the western Atlantic, extending 750 km from the Hudson River shelf edge. Reaches 4,500 m depth."},
    {"name": "Congo/Zaire Canyon", "lat": -6.0667, "lon": 12.0667,
     "country": "Atlantic Ocean", "year": "1886",
     "notes": "Largest submarine canyon in the world, extending 800+ km offshore. Turbidity currents travel 1,100 km to the deep sea fan."},
    {"name": "Nazare Canyon", "lat": 39.5833, "lon": -9.2667,
     "country": "Portugal", "year": "1898",
     "notes": "Europe's largest submarine canyon off the Portuguese coast, 230 km long and 5,000 m deep. Generates the world's largest surfable waves at Nazare."},
    {"name": "Bering Canyon", "lat": 54.4000, "lon": -169.0000,
     "country": "United States", "year": "1952",
     "notes": "One of the world's longest submarine canyons at 400 km. Located in the Bering Sea, carved during Pleistocene sea level lowstands."},
    {"name": "Cap Breton Canyon", "lat": 43.5667, "lon": -1.5667,
     "country": "France", "year": "1860",
     "notes": "Deep canyon in the Bay of Biscay cutting very close to shore at Capbreton. Only 250 m offshore, one of the closest canyons to land."},
    {"name": "Ganges-Brahmaputra Canyon", "lat": 21.0000, "lon": 89.5000,
     "country": "Indian Ocean", "year": "1936",
     "notes": "Extends from the Ganges-Brahmaputra delta into the Bay of Bengal, feeding the Bengal Fan, the world's largest submarine fan."},
    {"name": "Whittard Canyon", "lat": 48.5000, "lon": -10.5000,
     "country": "Atlantic Ocean", "year": "1907",
     "notes": "Complex canyon system on the Celtic margin south of Ireland. Four major branches with active sediment transport to 4,000+ m depth."},
    {"name": "Zhemchug Canyon", "lat": 56.2000, "lon": -175.2000,
     "country": "Bering Sea", "year": "1933",
     "notes": "Largest submarine canyon by volume in the world. Located in the Bering Sea with a total relief of 2,600 m. Larger than the Grand Canyon."},
    {"name": "Blanes Canyon", "lat": 41.6333, "lon": 2.8667,
     "country": "Spain", "year": "1890",
     "notes": "Northwestern Mediterranean canyon off the Costa Brava. Head is only 4 km from shore. Reaches 2,200 m depth at its axis."},
    {"name": "Perth Canyon", "lat": -32.0000, "lon": 115.0000,
     "country": "Australia", "year": "1947",
     "notes": "Deep canyon off Western Australia cutting through the continental shelf to 4,000 m. Hotspot for sperm whale and beaked whale feeding."},
    {"name": "De Soto Canyon", "lat": 29.5000, "lon": -87.0000,
     "country": "United States", "year": "1935",
     "notes": "Major canyon in the northeastern Gulf of Mexico between the Mississippi and Florida shelves. Important chemosynthetic community habitat."},
    {"name": "Norfolk Canyon", "lat": 37.0000, "lon": -74.5000,
     "country": "United States", "year": "1926",
     "notes": "Large canyon on the US mid-Atlantic margin off Virginia. Hosts diverse deep-sea coral communities and is part of a marine national monument."},
    {"name": "Indus Canyon", "lat": 23.5000, "lon": 67.0000,
     "country": "Indian Ocean", "year": "1934",
     "notes": "Extends from the Indus River delta into the Arabian Sea, feeding the Indus Fan. One of the largest submarine fans on Earth."},
    {"name": "Mississippi Canyon", "lat": 28.5000, "lon": -89.0000,
     "country": "United States", "year": "1937",
     "notes": "Major canyon in the Gulf of Mexico, head of the Mississippi submarine fan. Deepwater Horizon spill occurred near this canyon system."},
    {"name": "Cassidaigne Canyon", "lat": 43.1500, "lon": 5.4833,
     "country": "France", "year": "1870",
     "notes": "Short but deep canyon near Marseille. Historically used for industrial waste disposal from alumina factory. Now subject to restoration."},
    {"name": "La Jolla Canyon", "lat": 32.8500, "lon": -117.2667,
     "country": "United States", "year": "1913",
     "notes": "Submarine canyon extending from the Scripps pier area. Head is just 300 m offshore. Part of the Scripps Canyon system."},
    {"name": "Kaikoura Canyon", "lat": -42.4833, "lon": 173.6167,
     "country": "New Zealand", "year": "1920",
     "notes": "Deep canyon cutting close to the New Zealand coast near Kaikoura. Reaches 1,200 m depth. Important sperm whale feeding ground."},
    {"name": "Lacaze-Duthiers Canyon", "lat": 42.5000, "lon": 3.3667,
     "country": "France", "year": "1895",
     "notes": "Canyon in the Gulf of Lion, northwestern Mediterranean. Contains dense cold-water coral communities including Lophelia pertusa."},
    {"name": "Amazon Canyon", "lat": 2.5000, "lon": -47.0000,
     "country": "Brazil", "year": "1925",
     "notes": "Extends from the Amazon River mouth feeding the vast Amazon deep-sea fan. Carries enormous sediment loads to the Atlantic abyssal plain."},
    {"name": "Swatch of No Ground", "lat": 21.1000, "lon": 89.2000,
     "country": "Indian Ocean", "year": "1870",
     "notes": "Submarine canyon in the Bay of Bengal near Bangladesh. 14 km wide, reaching 1,340 m depth. Named for the abrupt loss of soundings."},
    {"name": "Great Bahama Canyon", "lat": 26.5000, "lon": -77.5000,
     "country": "Atlantic Ocean", "year": "1964",
     "notes": "System of canyons cutting through the Bahama Banks. The Tongue of the Ocean reaches 2,000 m and was used for US Navy submarine testing."},
    {"name": "Palomares Canyon", "lat": 37.2000, "lon": -1.8000,
     "country": "Spain", "year": "1966",
     "notes": "Canyon off Palomares, Spain. In 1966, a US hydrogen bomb was lost here after a B-52 collision, recovered from 869 m depth by DSV Alvin."},
    {"name": "Tokyo Canyon (Sagami Trough)", "lat": 35.0000, "lon": 139.0000,
     "country": "Japan", "year": "1930",
     "notes": "Complex canyon system in Sagami Bay south of Tokyo. Deep canyons cut by turbidity currents generated by earthquakes."},
    {"name": "Var Canyon", "lat": 43.6167, "lon": 7.2333,
     "country": "France", "year": "1979",
     "notes": "Canyon off Nice, France. In 1979, a landslide generated a tsunami that killed 11 people. Catastrophic failure of the new Nice airport runway extension."},
]

# ---------------------------------------------------------------
# 8. NUCLEAR SUBMARINE PORTS (25 locations)
# ---------------------------------------------------------------
NUCLEAR_SUBMARINE_PORTS = [
    {"name": "Naval Base Kitsap - Bangor (SSBN)", "lat": 47.7175, "lon": -122.7136,
     "country": "United States", "year": "1977",
     "notes": "Home to 8 Ohio-class SSBNs carrying Trident II D5 SLBMs. Largest concentration of deployed nuclear warheads in the US arsenal."},
    {"name": "Kings Bay (SSBN)", "lat": 30.7966, "lon": -81.5645,
     "country": "United States", "year": "1979",
     "notes": "Home to 6 Ohio-class SSBNs (Atlantic Fleet). Each submarine carries up to 20 Trident II missiles with multiple warheads."},
    {"name": "HMNB Clyde - Faslane (SSBN)", "lat": 56.0675, "lon": -4.8194,
     "country": "United Kingdom", "year": "1966",
     "notes": "Home to 4 Vanguard-class SSBNs carrying Trident II missiles. Britain's sole nuclear deterrent base. At least one boat always on patrol."},
    {"name": "Ile Longue (SSBN)", "lat": 48.3022, "lon": -4.5061,
     "country": "France", "year": "1972",
     "notes": "Home to 4 Le Triomphant-class SSBNs carrying M51 SLBMs. The Force oceanique strategique maintains continuous at-sea deterrence."},
    {"name": "Gadzhiyevo - Northern Fleet (SSBN)", "lat": 69.2500, "lon": 33.3167,
     "country": "Russia", "year": "1956",
     "notes": "Base for Russia's Delta IV and Borei-class SSBNs. Heart of the Northern Fleet's strategic nuclear submarine force on the Kola Peninsula."},
    {"name": "Vilyuchinsk - Pacific Fleet (SSBN)", "lat": 52.9333, "lon": 158.4000,
     "country": "Russia", "year": "1938",
     "notes": "Pacific Fleet SSBN base on Kamchatka. Houses Borei-class submarines carrying Bulava SLBMs. Protected by the Sea of Okhotsk bastion strategy."},
    {"name": "Yulin Underground Base (SSBN)", "lat": 18.2167, "lon": 109.5500,
     "country": "China", "year": "2000",
     "notes": "Underground pens on Hainan for PLAN's Jin-class (Type 094) SSBNs carrying JL-2/JL-3 SLBMs. Enables direct access to the South China Sea."},
    {"name": "INS Varsha (Planned SSBN Base)", "lat": 17.8333, "lon": 83.5000,
     "country": "India", "year": "2012",
     "notes": "Under-construction nuclear submarine base near Rambilli, Andhra Pradesh. Will house India's Arihant-class SSBNs carrying K-4 SLBMs."},
    {"name": "Groton (SSN Home Port)", "lat": 41.3868, "lon": -72.0896,
     "country": "United States", "year": "1954",
     "notes": "USS Nautilus (SSN-571), first nuclear submarine, was based here. Currently home to Virginia-class SSNs and the Submarine School."},
    {"name": "Norfolk (SSN Squadron)", "lat": 36.9467, "lon": -76.3033,
     "country": "United States", "year": "1960",
     "notes": "Submarine Squadron 6 and 8 home port. Multiple Virginia and Los Angeles-class SSNs stationed. Largest naval station in the world."},
    {"name": "Pearl Harbor (SSN Base)", "lat": 21.3546, "lon": -157.9602,
     "country": "United States", "year": "1960",
     "notes": "Submarine Squadron 1 and 7 home port in Hawaii. Forward-deployed SSNs for Pacific operations. Critical for Indo-Pacific strategy."},
    {"name": "Guam (SSN Forward Base)", "lat": 13.4443, "lon": 144.7937,
     "country": "United States", "year": "1964",
     "notes": "Naval Base Guam hosts forward-deployed Los Angeles and Virginia-class SSNs. Strategic Western Pacific presence and patrol base."},
    {"name": "HMAS Stirling (Future AUKUS SSN)", "lat": -32.2333, "lon": 115.6833,
     "country": "Australia", "year": "2027",
     "notes": "Under the AUKUS pact, will become home to Virginia-class SSNs and later SSN-AUKUS boats. Australia's future nuclear submarine base."},
    {"name": "Devonport (SSN Refit)", "lat": 50.3833, "lon": -4.1833,
     "country": "United Kingdom", "year": "1970",
     "notes": "Primary facility for Royal Navy nuclear submarine refitting. Services Astute and Trafalgar-class SSNs. Also decommissions old submarines."},
    {"name": "Toulon (SNA Barracuda)", "lat": 43.1167, "lon": 5.9333,
     "country": "France", "year": "1983",
     "notes": "Home to France's Suffren-class (Barracuda) nuclear attack submarines. Six boats planned to replace the Rubis class by 2030."},
    {"name": "Cherbourg (Submarine Construction)", "lat": 49.6333, "lon": -1.6167,
     "country": "France", "year": "1899",
     "notes": "Naval Group (formerly DCNS) shipyard where all French nuclear submarines are built. Current production: Suffren-class SSNs."},
    {"name": "Severodvinsk (Sevmash SSN/SSBN)", "lat": 64.5667, "lon": 39.8500,
     "country": "Russia", "year": "1939",
     "notes": "Russia's sole nuclear submarine shipyard on the White Sea. Currently building Yasen-M class SSGNs and Borei-A class SSBNs."},
    {"name": "Nerpichya (Zapadnaya Litsa)", "lat": 69.4167, "lon": 32.4500,
     "country": "Russia", "year": "1961",
     "notes": "Major Northern Fleet base for nuclear-powered attack submarines. Houses Akula, Sierra, and Yasen-class SSNs. Highly restricted access."},
    {"name": "Huludao Shipyard", "lat": 40.7167, "lon": 120.8500,
     "country": "China", "year": "1951",
     "notes": "Bohai Shipbuilding Heavy Industry shipyard where all Chinese nuclear submarines have been built since the 1960s."},
    {"name": "Wuchang Shipyard (SSN)", "lat": 30.5500, "lon": 114.3000,
     "country": "China", "year": "1934",
     "notes": "Major submarine construction facility in Wuhan, Hubei. Building conventional and reportedly some nuclear submarine sections."},
    {"name": "Vishakhapatnam (Arihant Class)", "lat": 17.6833, "lon": 83.2167,
     "country": "India", "year": "2009",
     "notes": "Ship Building Centre where INS Arihant, India's first indigenous nuclear ballistic missile submarine, was constructed and launched."},
    {"name": "Barrow-in-Furness (BAE Systems)", "lat": 54.1167, "lon": -3.2333,
     "country": "United Kingdom", "year": "1871",
     "notes": "BAE Systems Maritime shipyard building all Royal Navy submarines. Currently constructing Dreadnought-class SSBNs and Astute-class SSNs."},
    {"name": "General Dynamics Electric Boat", "lat": 41.3500, "lon": -72.0800,
     "country": "United States", "year": "1899",
     "notes": "Primary US nuclear submarine builder in Groton, Connecticut. Building Virginia-class SSNs and the new Columbia-class SSBNs."},
    {"name": "Newport News Shipbuilding", "lat": 36.9833, "lon": -76.4333,
     "country": "United States", "year": "1886",
     "notes": "Huntington Ingalls shipyard that co-produces Virginia-class submarines with Electric Boat. Also builds all US aircraft carriers."},
    {"name": "Nerpa Shipyard (Nuclear Sub Refit)", "lat": 69.1167, "lon": 33.4833,
     "country": "Russia", "year": "1950",
     "notes": "82nd Shipyard on the Kola Peninsula for nuclear submarine repair and refueling. Also handles decommissioning of retired nuclear boats."},
]

# ---------------------------------------------------------------
# 9. DEEP SEA MINING SITES (25 locations)
# ---------------------------------------------------------------
DEEP_SEA_MINING_SITES = [
    {"name": "Clarion-Clipperton Zone (CCZ) - DORD Area", "lat": 12.0000, "lon": -130.0000,
     "country": "Pacific Ocean", "year": "2001",
     "notes": "Japan's Deep Ocean Resources Development Co. holds ISA exploration license for polymetallic nodules. CCZ contains trillions of manganese nodules."},
    {"name": "CCZ - GSR (Belgium) Block", "lat": 13.5000, "lon": -125.0000,
     "country": "Pacific Ocean", "year": "2013",
     "notes": "Global Sea Mineral Resources (DEME Group, Belgium) holds ISA license. Estimated 300+ million tonnes of nodules in their 75,000 sq km block."},
    {"name": "CCZ - China Minmetals Block", "lat": 11.5000, "lon": -117.0000,
     "country": "Pacific Ocean", "year": "2017",
     "notes": "China Minmetals holds ISA exploration contract. Part of China's growing presence in deep-sea mineral exploration."},
    {"name": "CCZ - The Metals Company (NORI Area)", "lat": 14.0000, "lon": -127.0000,
     "country": "Pacific Ocean", "year": "2011",
     "notes": "The Metals Company (formerly DeepGreen) holds ISA contract via NORI. Plans to commence commercial nodule collection. Highly controversial."},
    {"name": "CCZ - BGR (Germany) Block", "lat": 11.8000, "lon": -118.0000,
     "country": "Pacific Ocean", "year": "2006",
     "notes": "German Federal Institute for Geosciences holds ISA license. Conducting environmental baseline studies alongside mineral assessment."},
    {"name": "CCZ - IOM (Interoceanmetal)", "lat": 12.0000, "lon": -120.0000,
     "country": "Pacific Ocean", "year": "2001",
     "notes": "Joint venture of Bulgaria, Cuba, Czech Republic, Poland, Russia, and Slovakia. One of the earliest ISA contractors for polymetallic nodules."},
    {"name": "Solwara 1 (Papua New Guinea)", "lat": -3.7833, "lon": 152.1000,
     "country": "Papua New Guinea", "year": "2011",
     "notes": "Nautilus Minerals planned the world's first deep-sea mining operation for seafloor massive sulfides at 1,600 m. Company went bankrupt in 2019."},
    {"name": "Cook Islands Exclusive Economic Zone", "lat": -15.0000, "lon": -160.0000,
     "country": "Cook Islands", "year": "2022",
     "notes": "Cook Islands seabed authority granted exploration licenses for polymetallic nodules in its 2 million sq km EEZ. Potentially 10+ billion tonnes."},
    {"name": "Mid-Atlantic Ridge ISA Area", "lat": 14.0000, "lon": -44.8667,
     "country": "Atlantic Ocean", "year": "2015",
     "notes": "Multiple ISA exploration contracts for polymetallic sulfides on the Mid-Atlantic Ridge. Russia, France, and Poland hold licenses."},
    {"name": "Central Indian Ocean Basin (India)", "lat": -12.0000, "lon": 76.0000,
     "country": "Indian Ocean", "year": "2002",
     "notes": "India holds ISA exploration license for 75,000 sq km of polymetallic nodule fields. Estimated 380 million tonnes of nodules."},
    {"name": "Southwest Indian Ridge (China)", "lat": -37.7833, "lon": 49.6500,
     "country": "Indian Ocean", "year": "2011",
     "notes": "China Ocean Mineral Resources R&D Association holds ISA license for polymetallic sulfides on the ultra-slow spreading ridge."},
    {"name": "Penrhyn Basin (Cook Islands)", "lat": -12.0000, "lon": -160.0000,
     "country": "Pacific Ocean", "year": "2020",
     "notes": "Rich manganese nodule field within the Cook Islands EEZ. Estimated to contain cobalt, nickel, and manganese worth hundreds of billions."},
    {"name": "Magellan Seamounts (Russia)", "lat": 16.5000, "lon": 152.0000,
     "country": "Pacific Ocean", "year": "2015",
     "notes": "Russia holds ISA exploration contract for cobalt-rich ferromanganese crusts on Pacific seamounts in the Magellan cluster."},
    {"name": "Rio Grande Rise (Brazil)", "lat": -30.0000, "lon": -35.5000,
     "country": "Atlantic Ocean", "year": "2014",
     "notes": "Brazil holds ISA exploration license for cobalt-rich crusts on this large oceanic plateau in the South Atlantic."},
    {"name": "Kermadec Arc (New Zealand EEZ)", "lat": -32.0000, "lon": -178.0000,
     "country": "New Zealand", "year": "2002",
     "notes": "Seafloor massive sulfide deposits associated with volcanic arc. New Zealand declared a moratorium on seabed mining in its waters."},
    {"name": "Bismarck Sea (PNG)", "lat": -3.7167, "lon": 151.6667,
     "country": "Papua New Guinea", "year": "2000",
     "notes": "Multiple seafloor massive sulfide deposits in the Manus back-arc basin. PACMANUS field contains gold, copper, zinc, and silver."},
    {"name": "Red Sea Brine Pools (Saudi-Sudan)", "lat": 21.3500, "lon": 38.0500,
     "country": "Red Sea", "year": "1965",
     "notes": "Metalliferous sediments in deep brine pools of the Atlantis II Deep. Contain zinc, copper, gold, and silver. Saudi-Sudanese joint mining proposed."},
    {"name": "CCZ - KIOST (South Korea) Block", "lat": 10.0000, "lon": -132.0000,
     "country": "Pacific Ocean", "year": "2012",
     "notes": "Korea Institute of Ocean Science and Technology holds ISA exploration license. Developing nodule collection technology."},
    {"name": "CCZ - COMRA (China) Block", "lat": 12.0000, "lon": -124.0000,
     "country": "Pacific Ocean", "year": "2001",
     "notes": "China Ocean Mineral Resources R&D Association pioneer investor area. 75,000 sq km license held since ISA's early operations."},
    {"name": "Northwest Pacific Seamounts (Japan)", "lat": 20.0000, "lon": 155.0000,
     "country": "Pacific Ocean", "year": "2013",
     "notes": "Japan holds ISA exploration license for cobalt-rich crusts. Japanese waters also contain rare earth element-rich muds."},
    {"name": "Tonga Offshore Mining Area", "lat": -21.0000, "lon": -175.5000,
     "country": "Tonga", "year": "2008",
     "notes": "Nautilus Minerals held exploration licenses for seafloor massive sulfides in Tonga's waters. Rights reverted after Nautilus bankruptcy."},
    {"name": "Chatham Rise (New Zealand)", "lat": -43.5000, "lon": -178.0000,
     "country": "New Zealand", "year": "2010",
     "notes": "Phosphorite nodule deposits on the continental shelf east of New Zealand. Trans-Tasman Resources proposed extraction but permit was declined."},
    {"name": "Sonne Field (Indian Ocean)", "lat": -25.3167, "lon": 70.0333,
     "country": "Indian Ocean", "year": "2016",
     "notes": "Hydrothermal sulfide deposits on the Central Indian Ridge. Germany conducted research surveys with the RV Sonne."},
    {"name": "JOGMEC Prime Crust Zone", "lat": 22.0000, "lon": 148.0000,
     "country": "Pacific Ocean", "year": "2013",
     "notes": "Japan Oil, Gas and Metals National Corporation holds ISA license for cobalt-rich crusts. Successfully tested small-scale collection in 2020."},
    {"name": "Nauru Ocean Resources (NORI-D)", "lat": 7.0000, "lon": -161.0000,
     "country": "Pacific Ocean", "year": "2011",
     "notes": "The Metals Company subsidiary NORI triggered the ISA two-year rule in 2021 by requesting exploitation license. Sparked global debate."},
]

# ---------------------------------------------------------------
# 10. UNDERWATER RESEARCH STATIONS (25 locations)
# ---------------------------------------------------------------
UNDERWATER_RESEARCH_STATIONS = [
    {"name": "Aquarius Reef Base", "lat": 24.9508, "lon": -80.4536,
     "country": "United States", "year": "1993",
     "notes": "World's only remaining undersea research laboratory at 19 m depth in the Florida Keys. NASA uses it for NEEMO astronaut training missions."},
    {"name": "SEALAB I", "lat": 32.6167, "lon": -64.9500,
     "country": "Bermuda", "year": "1964",
     "notes": "US Navy's first undersea habitat at 59 m off Bermuda. Four aquanauts lived 11 days proving humans could live and work underwater."},
    {"name": "SEALAB II", "lat": 33.4667, "lon": -117.5167,
     "country": "United States", "year": "1965",
     "notes": "Placed at 62 m off La Jolla, California. 28 aquanauts rotated in teams of 10. Scott Carpenter spent 30 continuous days submerged."},
    {"name": "SEALAB III", "lat": 33.4167, "lon": -117.5667,
     "country": "United States", "year": "1969",
     "notes": "Planned for 186 m depth off San Clemente Island. Project cancelled after the death of aquanaut Berry Cannon during helium gas mix issues."},
    {"name": "Conshelf I (Cousteau)", "lat": 43.2000, "lon": 5.3333,
     "country": "France", "year": "1962",
     "notes": "Jacques Cousteau's Continental Shelf Station One off Marseille at 10 m depth. Albert Falco and Claude Wesly lived 7 days underwater."},
    {"name": "Conshelf II (Cousteau)", "lat": 20.0833, "lon": 38.8333,
     "country": "Red Sea (Sudan)", "year": "1963",
     "notes": "Cousteau's ambitious Red Sea habitat complex with starfish-shaped main building at 10 m and deep cabin at 27 m. Five men lived a month."},
    {"name": "Conshelf III (Cousteau)", "lat": 43.1667, "lon": 6.7500,
     "country": "France", "year": "1965",
     "notes": "Six oceanauts lived 27 days at 100 m depth near Cap Ferrat. Proved humans could work effectively at saturation depth for extended periods."},
    {"name": "Tektite I Habitat", "lat": 18.3100, "lon": -64.7600,
     "country": "US Virgin Islands", "year": "1969",
     "notes": "Underwater habitat at 15 m in Lameshur Bay, St. John. Four aquanauts lived 58 days. Joint NASA-Navy-Interior Department program."},
    {"name": "Tektite II Habitat", "lat": 18.3100, "lon": -64.7600,
     "country": "US Virgin Islands", "year": "1970",
     "notes": "Continuation of Tektite, with 11 missions including the first all-female aquanaut team led by Sylvia Earle. Major marine science output."},
    {"name": "Helgoland Habitat", "lat": 54.1833, "lon": 7.8833,
     "country": "Germany", "year": "1969",
     "notes": "German underwater laboratory placed at 23 m near Helgoland Island in the North Sea. Used for marine biology and physiology research."},
    {"name": "La Chalupa Research Lab", "lat": 18.3000, "lon": -67.9167,
     "country": "Puerto Rico", "year": "1972",
     "notes": "Underwater habitat at 30 m off La Parguera. Scientists conducted marine biology research for NOAA. One of the last active US habitats."},
    {"name": "Jules' Undersea Lodge", "lat": 25.1167, "lon": -80.4000,
     "country": "United States", "year": "1986",
     "notes": "Former research habitat converted to the world's first and only underwater hotel in Key Largo, Florida at 6 m depth. Originally La Chalupa."},
    {"name": "PROTEUS Underwater Station (Planned)", "lat": 15.9333, "lon": -61.7167,
     "country": "Curacao", "year": "2026",
     "notes": "Fabien Cousteau's planned 370 sq m underwater research station off Curacao at 18 m depth. Would be the world's largest undersea habitat."},
    {"name": "Starfish House (Conshelf II Main)", "lat": 20.0833, "lon": 38.8333,
     "country": "Red Sea", "year": "1963",
     "notes": "The star-shaped main habitat of Conshelf II where 5 oceanauts lived at 10 m. Featured a garage for the submarine SP-350 Denise."},
    {"name": "MARS Underwater Observatory", "lat": 36.7133, "lon": -122.1867,
     "country": "United States", "year": "2008",
     "notes": "Monterey Accelerated Research System: cabled deep-sea observatory at 891 m in Monterey Bay. 24/7 real-time data and HD video from the abyss."},
    {"name": "NEPTUNE Observatory (Node)", "lat": 48.3167, "lon": -126.0500,
     "country": "Canada", "year": "2009",
     "notes": "North-East Pacific Time-series Undersea Networked Experiments. 800 km of fiber-optic cable with instruments from shore to 2,660 m depth."},
    {"name": "ALOHA Cabled Observatory", "lat": 22.7500, "lon": -158.0000,
     "country": "United States", "year": "2011",
     "notes": "Deep-sea observatory at 4,728 m depth north of Oahu, Hawaii. Continuous monitoring of deep Pacific water properties and biology."},
    {"name": "EMSO Azores (Lucky Strike)", "lat": 37.2917, "lon": -32.2750,
     "country": "Atlantic Ocean", "year": "2010",
     "notes": "European Multidisciplinary Seafloor and water-column Observatory at the Lucky Strike vent field on the Mid-Atlantic Ridge at 1,700 m."},
    {"name": "Deep-sea Station (S1) Japan", "lat": 41.1000, "lon": 144.4167,
     "country": "Japan", "year": "2006",
     "notes": "JAMSTEC deep-sea cabled observatory off Hokkaido at 2,500 m depth. Monitors seismicity, tsunamis, and deep-ocean conditions."},
    {"name": "Ocean Networks Canada (Cascadia Basin)", "lat": 47.7667, "lon": -127.7667,
     "country": "Canada", "year": "2009",
     "notes": "Deep-sea node of the NEPTUNE observatory at 2,660 m on the Juan de Fuca plate. Monitors earthquakes, gas hydrates, and deep currents."},
    {"name": "KM3NeT ORCA", "lat": 42.8000, "lon": 6.0333,
     "country": "France", "year": "2019",
     "notes": "Neutrino telescope array at 2,450 m depth off Toulon. Detects neutrinos using Cherenkov light in deep Mediterranean water."},
    {"name": "ANTARES Neutrino Telescope", "lat": 42.8000, "lon": 6.1667,
     "country": "France", "year": "2008",
     "notes": "Deep-sea neutrino detector at 2,475 m off Toulon. Predecessor to KM3NeT. Also serves as marine environmental monitoring platform."},
    {"name": "Baikal Deep Underwater Neutrino Telescope", "lat": 51.7667, "lon": 104.4000,
     "country": "Russia", "year": "2021",
     "notes": "Baikal-GVD neutrino telescope deployed at 1,366 m depth in Lake Baikal. Uses the world's deepest freshwater lake as a detection medium."},
    {"name": "DONET Observatory (Nankai Trough)", "lat": 33.1500, "lon": 136.7000,
     "country": "Japan", "year": "2011",
     "notes": "Dense Oceanfloor Network system for Earthquakes and Tsunamis in the Nankai Trough. 51 stations monitoring Japan's most dangerous fault."},
    {"name": "OOI Pioneer Array", "lat": 40.1333, "lon": -70.8833,
     "country": "United States", "year": "2013",
     "notes": "Ocean Observatories Initiative array south of Martha's Vineyard. Moorings, gliders, and AUVs monitoring the continental shelf to deep ocean."},
]

# ===================================================================
# MODE CONFIGURATION
# ===================================================================

MODE_CONFIG = {
    "World's Deepest Ocean Trenches": {
        "data": DEEPEST_OCEAN_TRENCHES,
        "color": "#06b6d4",
        "icon": "anchor",
        "desc": "The deepest points on Earth where tectonic plates collide and plunge into the mantle, creating abyssal chasms exceeding 10,000 meters.",
    },
    "Submarine Naval Bases": {
        "data": SUBMARINE_NAVAL_BASES,
        "color": "#8b5cf6",
        "icon": "ship",
        "desc": "Active and historic naval installations housing submarine fleets worldwide, from Cold War-era underground pens to modern Trident bases.",
    },
    "Famous Submarine Wrecks": {
        "data": FAMOUS_SUBMARINE_WRECKS,
        "color": "#ef4444",
        "icon": "exclamation-triangle",
        "desc": "Notable submarines and vessels lost at sea, from wartime casualties to peacetime tragedies, resting on the ocean floor.",
    },
    "Deep Sea Exploration Sites": {
        "data": DEEP_SEA_EXPLORATION_SITES,
        "color": "#10b981",
        "icon": "search",
        "desc": "Historic deep-sea dives and discoveries that expanded humanity's knowledge of the ocean depths and the limits of exploration.",
    },
    "Hydrothermal Vent Fields": {
        "data": HYDROTHERMAL_VENT_FIELDS,
        "color": "#f59e0b",
        "icon": "fire",
        "desc": "Volcanic vents on the seafloor where superheated mineral-laden water supports unique chemosynthetic ecosystems independent of sunlight.",
    },
    "Underwater Cable Routes": {
        "data": UNDERWATER_CABLE_ROUTES,
        "color": "#3b82f6",
        "icon": "plug",
        "desc": "Submarine fiber-optic cables carrying 97% of intercontinental data traffic. The hidden backbone of the global internet.",
    },
    "Submarine Canyon Systems": {
        "data": SUBMARINE_CANYON_SYSTEMS,
        "color": "#a855f7",
        "icon": "mountain",
        "desc": "Massive underwater valleys carved into continental shelves, some rivaling the Grand Canyon in scale and geological significance.",
    },
    "Nuclear Submarine Ports": {
        "data": NUCLEAR_SUBMARINE_PORTS,
        "color": "#dc2626",
        "icon": "radiation",
        "desc": "Bases and shipyards for nuclear-powered submarines, the most powerful warships ever built and keystones of strategic deterrence.",
    },
    "Deep Sea Mining Sites": {
        "data": DEEP_SEA_MINING_SITES,
        "color": "#f97316",
        "icon": "gem",
        "desc": "Locations where polymetallic nodules, sulfide deposits, and cobalt crusts are being explored for potential commercial mining on the seafloor.",
    },
    "Underwater Research Stations": {
        "data": UNDERWATER_RESEARCH_STATIONS,
        "color": "#14b8a6",
        "icon": "flask",
        "desc": "Undersea habitats, cabled observatories, and research platforms enabling long-term study of the ocean from within.",
    },
}


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================


def _compute_country_stats(locations):
    """Compute country frequency counts for a location list."""
    country_counts = {}
    for loc in locations:
        c = loc.get("country", "Unknown")
        country_counts[c] = country_counts.get(c, 0) + 1
    return dict(sorted(country_counts.items(), key=lambda x: -x[1]))


def _build_popup(loc, mode_color="#06b6d4"):
    """Build sanitized popup HTML for a folium CircleMarker."""
    name = html_module.escape(str(loc.get("name", "Unknown")))
    country = html_module.escape(str(loc.get("country", "")))
    notes = html_module.escape(str(loc.get("notes", ""))[:250])
    color = html_module.escape(str(mode_color))

    # Show depth if available, otherwise year
    extra_line = ""
    if "depth_m" in loc:
        depth = html_module.escape(str(loc["depth_m"]))
        extra_line = f'<div style="font-size:0.82rem; color:#06b6d4; font-weight:600;">Depth: {depth} m</div>'
    elif "year" in loc:
        year = html_module.escape(str(loc["year"]))
        extra_line = f'<div style="font-size:0.82rem; color:#e5e7eb;">Year: {year}</div>'

    return (
        f'<div style="max-width:300px; font-family:Segoe UI,sans-serif; '
        f'background:#0a0e1a; padding:10px 12px; border-radius:8px; '
        f'border:1px solid {color}40;">'
        f'<div style="font-size:0.95rem; font-weight:700; color:{color}; '
        f'margin-bottom:4px;">{name}</div>'
        f'<div style="font-size:0.82rem; color:#e5e7eb; margin-bottom:2px;">'
        f'{country}</div>'
        f'{extra_line}'
        f'<div style="font-size:0.75rem; color:#9ca3af; margin-top:6px; '
        f'line-height:1.4;">{notes}</div>'
        f'<div style="font-size:0.65rem; color:#5a6580; margin-top:4px;">'
        f'{loc.get("lat", 0):.4f}, {loc.get("lon", 0):.4f}</div>'
        f'</div>'
    )


def _build_map(locations, zoom=2, mode_color="#06b6d4"):
    """Build a dark-themed folium map with CircleMarkers for all locations."""
    if not locations:
        return folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    avg_lat = sum(loc["lat"] for loc in locations) / len(locations)
    avg_lon = sum(loc["lon"] for loc in locations) / len(locations)

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    for loc in locations:
        popup_html = _build_popup(loc, mode_color)
        tooltip_text = html_module.escape(str(loc.get("name", "")))

        # Size based on depth if available
        radius = 7
        if "depth_m" in loc:
            depth = loc["depth_m"]
            if depth > 10000:
                radius = 12
            elif depth > 8000:
                radius = 10
            elif depth > 6000:
                radius = 8
            else:
                radius = 6

        folium.CircleMarker(
            location=[loc["lat"], loc["lon"]],
            radius=radius,
            color=mode_color,
            fill=True,
            fill_color=mode_color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=tooltip_text,
        ).add_to(m)

    return m


def _build_dataframe(locations, mode_name=""):
    """Build a pandas DataFrame from a list of location dicts."""
    rows = []
    for loc in locations:
        row = {
            "Name": loc.get("name", ""),
            "Country / Region": loc.get("country", ""),
            "Latitude": loc.get("lat", 0.0),
            "Longitude": loc.get("lon", 0.0),
        }
        if "depth_m" in loc:
            row["Depth (m)"] = loc.get("depth_m", 0)
        if "year" in loc:
            row["Year"] = loc.get("year", "")
        row["Notes"] = loc.get("notes", "")
        rows.append(row)
    return pd.DataFrame(rows)


# ===================================================================
# INDIVIDUAL MODE RENDERER
# ===================================================================


def _render_mode(mode_name):
    """Render a complete section for one of the 10 map modes."""
    config = MODE_CONFIG.get(mode_name, {})
    locations = config.get("data", [])
    color = config.get("color", "#06b6d4")

    if not locations:
        st.warning(f"No data available for {html_module.escape(mode_name)}.")
        return

    # -- Mode Description --
    desc = html_module.escape(config.get("desc", ""))
    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem; margin-bottom:1rem;">'
        f'{desc}</p>',
        unsafe_allow_html=True,
    )

    # -- Stats Row using st.metric --
    countries = sorted(set(loc.get("country", "") for loc in locations))

    # Depth stats (for trench mode)
    depths = [loc["depth_m"] for loc in locations if "depth_m" in loc]

    # Year stats (for other modes)
    years_numeric = []
    for loc in locations:
        yr_str = str(loc.get("year", "")).strip()
        yr_clean = yr_str.rstrip("s").lstrip("~").replace("?", "")
        if yr_clean.lstrip("-").isdigit():
            years_numeric.append(int(yr_clean))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Locations", len(locations))
    c2.metric("Regions / Oceans", len(countries))

    if depths:
        c3.metric("Max Depth", f"{max(depths):,} m")
        c4.metric("Avg Depth", f"{sum(depths) // len(depths):,} m")
    elif years_numeric:
        c3.metric("Earliest Record", str(min(years_numeric)))
        c4.metric("Latest Record", str(max(years_numeric)))
    else:
        c3.metric("Data Points", len(locations))
        c4.metric("Fields per Entry", 5)

    # -- Country / Region Breakdown Metrics --
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
        f'<span style="color:{html_module.escape(color)}; font-size:0.85rem; font-weight:600;">'
        f'&#9679; {mode_esc}</span>'
        f' <span style="color:#5a6580; font-size:0.75rem;">'
        f'({len(locations)} locations)</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    m = _build_map(locations, zoom=2, mode_color=color)
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
                notes_esc = html_module.escape(str(loc.get("notes", ""))[:120])
                loc_color = html_module.escape(str(color))

                # Detail line differs by mode
                detail = ""
                if "depth_m" in loc:
                    detail = f"Depth: {loc['depth_m']:,} m"
                elif "year" in loc:
                    detail = f"Year: {html_module.escape(str(loc['year']))}"

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
                    f'{country_esc} &middot; {detail}</div>'
                    f'<div style="color:#5a6580; font-size:0.68rem; line-height:1.35;">'
                    f'{notes_esc}</div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # -- Data Table --
    df = _build_dataframe(locations, mode_name)
    st.markdown(
        f'<h4 style="color:#e8ecf4;">Data Table ({len(df)} locations)</h4>',
        unsafe_allow_html=True,
    )

    # Country / Region filter within mode
    all_regions = sorted(df["Country / Region"].unique().tolist())
    selected_regions = st.multiselect(
        "Filter by Region",
        options=all_regions,
        default=all_regions,
        key=f"filter_sub_{mode_name.replace(' ', '_').replace("'", '')}",
    )

    filtered_df = df[df["Country / Region"].isin(selected_regions)]
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # -- CSV Download --
    csv_buf = io.StringIO()
    filtered_df.to_csv(csv_buf, index=False)
    safe_name = mode_name.lower().replace(" ", "_").replace("'", "").replace("&", "and")
    st.download_button(
        label=f"Download {len(filtered_df)} {mode_name} locations as CSV",
        data=csv_buf.getvalue(),
        file_name=f"submarine_{safe_name}.csv",
        mime="text/csv",
        key=f"dl_sub_{safe_name}",
    )


# ===================================================================
# MAIN RENDER FUNCTION
# ===================================================================


def render_submarine_maps_tab():
    """Main render function for the Submarines & Deep Sea Explorer tab."""

    # ---- Tab Header ----
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>\U0001f531 Submarines & Deep Sea Explorer</h4>'
        '<p>Submarine bases, deep sea trenches, underwater exploration & naval heritage</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ---- Informational Notice ----
    st.markdown(
        '<div style="background:rgba(6,182,212,0.08); border:1px solid rgba(6,182,212,0.25); '
        'border-radius:8px; padding:0.75rem 1rem; margin-bottom:1rem;">'
        '<span style="color:#06b6d4; font-weight:600;">Deep Sea Data:</span> '
        '<span style="color:#8b97b0; font-size:0.85rem;">'
        'This module contains curated data on submarine bases, ocean trenches, famous wrecks, '
        'hydrothermal vents, undersea cables, research stations, and deep-sea mining sites. '
        'All locations are from publicly available records and scientific literature.</span></div>',
        unsafe_allow_html=True,
    )

    # ---- Map Mode Selector (10 modes) ----
    mode_options = list(MODE_CONFIG.keys())

    selected_mode = st.selectbox(
        "\U0001f531 Select Map Mode",
        mode_options,
        index=0,
        key="submarine_maps_mode",
        help="Choose from 10 categories covering submarines, ocean trenches, wrecks, vents, cables, and more.",
    )

    # ---- Category Quick-Access Badges (2 rows of 5) ----
    badge_icons = {
        "World's Deepest Ocean Trenches": "\U0001f30a",
        "Submarine Naval Bases": "\U0001f6a2",
        "Famous Submarine Wrecks": "\u2693",
        "Deep Sea Exploration Sites": "\U0001f52d",
        "Hydrothermal Vent Fields": "\U0001f525",
        "Underwater Cable Routes": "\U0001f50c",
        "Submarine Canyon Systems": "\U0001f3d4\ufe0f",
        "Nuclear Submarine Ports": "\u2622\ufe0f",
        "Deep Sea Mining Sites": "\u26cf\ufe0f",
        "Underwater Research Stations": "\U0001f52c",
    }

    row1 = mode_options[:5]
    row2 = mode_options[5:]

    cols1 = st.columns(5)
    for i, mode in enumerate(row1):
        cfg = MODE_CONFIG[mode]
        c = cfg["color"]
        icon = badge_icons.get(mode, "\U0001f30a")
        is_sel = mode == selected_mode
        bg = f"{c}22" if is_sel else "rgba(26,34,53,0.5)"
        border = c if is_sel else "#2a3550"
        short = mode.split("(")[0].strip()[:18]
        cols1[i].markdown(
            f'<div style="background:{bg}; border:1px solid {border}; '
            f'border-radius:6px; padding:4px 6px; text-align:center; '
            f'font-size:0.7rem; color:{c}; font-weight:600; '
            f'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">'
            f'{icon} {html_module.escape(short)}</div>',
            unsafe_allow_html=True,
        )

    cols2 = st.columns(5)
    for i, mode in enumerate(row2):
        cfg = MODE_CONFIG[mode]
        c = cfg["color"]
        icon = badge_icons.get(mode, "\U0001f30a")
        is_sel = mode == selected_mode
        bg = f"{c}22" if is_sel else "rgba(26,34,53,0.5)"
        border = c if is_sel else "#2a3550"
        short = mode.split("(")[0].strip()[:18]
        cols2[i].markdown(
            f'<div style="background:{bg}; border:1px solid {border}; '
            f'border-radius:6px; padding:4px 6px; text-align:center; '
            f'font-size:0.7rem; color:{c}; font-weight:600; '
            f'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">'
            f'{icon} {html_module.escape(short)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ---- Render Selected Mode ----
    _render_mode(selected_mode)
