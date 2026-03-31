# -*- coding: utf-8 -*-
"""
Cryptid & Monster Explorer module for TerraScout AI.
Curated geospatial datasets of cryptid sightings, legendary creatures,
and mysterious monster reports worldwide. Ten interactive map modes
covering lake monsters, bigfoot, sea serpents, and more.
All data is curated from historical records and folklore databases.
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

# ═══════════════════════════════════════════════════════
# CATEGORY COLORS
# ═══════════════════════════════════════════════════════
CATEGORY_COLORS = {
    "Lake Monsters": "#38bdf8",
    "Bigfoot & Yeti": "#8b5cf6",
    "Sea Serpents & Kraken": "#06b6d4",
    "Chupacabra & Blood Drinkers": "#ef4444",
    "Mothman & Winged Creatures": "#f59e0b",
    "Dragon Legends": "#dc2626",
    "Werewolf Legends": "#a855f7",
    "Mystery Cats & Big Cats": "#10b981",
    "Undiscovered Species": "#3b82f6",
    "Cryptid Hotspots": "#ec4899",
}

MARKER_ICONS = {
    "Lake Monsters": "tint",
    "Bigfoot & Yeti": "paw",
    "Sea Serpents & Kraken": "anchor",
    "Chupacabra & Blood Drinkers": "bolt",
    "Mothman & Winged Creatures": "plane",
    "Dragon Legends": "fire",
    "Werewolf Legends": "moon-o",
    "Mystery Cats & Big Cats": "paw",
    "Undiscovered Species": "search",
    "Cryptid Hotspots": "map-marker",
}

# ═══════════════════════════════════════════════════════
# MODE DESCRIPTIONS
# ═══════════════════════════════════════════════════════
MODE_DESCRIPTIONS = {
    "Lake Monsters": (
        "Explore legendary lake monsters from around the globe. From the iconic "
        "Loch Ness Monster in Scotland to Ogopogo in British Columbia, Champ in "
        "Lake Champlain, Nahuelito in Patagonia, and dozens more -- these aquatic "
        "cryptids have captivated human imagination for centuries. Each marker "
        "represents a lake or body of water with documented monster sightings "
        "or deep-rooted local legends."
    ),
    "Bigfoot & Yeti": (
        "Map the worldwide distribution of large bipedal cryptid sightings. "
        "Sasquatch dominates the Pacific Northwest, but similar creatures are "
        "reported on every inhabited continent: the Yeti in the Himalayas, "
        "Yowie in Australia, Orang Pendek in Sumatra, Almas in Central Asia, "
        "and the Yeren in China. This mode plots notable sighting clusters "
        "and areas of persistent reports."
    ),
    "Sea Serpents & Kraken": (
        "Chart historical sea monster encounters across the world's oceans. "
        "From ancient Norse Kraken legends to 19th-century naval encounters "
        "with enormous serpentine creatures, the deep ocean remains the last "
        "great frontier of cryptozoology. Includes giant squid encounter "
        "locations and famous sea serpent sighting coordinates."
    ),
    "Chupacabra & Blood Drinkers": (
        "Track sightings of the Chupacabra and similar blood-draining cryptids. "
        "First reported in Puerto Rico in 1995, the Chupacabra (goat-sucker) "
        "quickly spread across Latin America and the southern United States. "
        "This mode maps the most significant sighting clusters and livestock "
        "predation events attributed to unknown creatures."
    ),
    "Mothman & Winged Creatures": (
        "Investigate sightings of mysterious winged humanoids and aerial cryptids. "
        "The Mothman of Point Pleasant, West Virginia is the most famous, but "
        "similar creatures have been reported worldwide: the Jersey Devil of "
        "the Pine Barrens, Thunderbirds of the American Southwest, the Owlman "
        "of Cornwall, and winged humanoids reported over Chicago."
    ),
    "Dragon Legends": (
        "Explore the global geography of dragon mythology and alleged sightings. "
        "Nearly every culture on Earth has dragon legends, from European fire-breathers "
        "to Chinese lung dragons, Mesoamerican feathered serpents, and African "
        "Ninki Nanka. This mode maps locations where dragon myths originated "
        "and places where dragon-like creatures have allegedly been seen."
    ),
    "Werewolf Legends": (
        "Map the dark history of werewolf legends, trials, and modern sightings. "
        "From the Beast of Gevaudan that terrorized 18th-century France to "
        "the werewolf trials of medieval Europe, and modern reports of dogman "
        "creatures in Michigan and Wisconsin. Includes Skinwalker legends "
        "from the Navajo Nation."
    ),
    "Mystery Cats & Big Cats": (
        "Track sightings of out-of-place big cats and phantom felines worldwide. "
        "The Beast of Bodmin Moor, the Surrey Puma, the Blue Mountains panther -- "
        "large predatory cats are reported in places they should not exist. "
        "This mode maps confirmed and alleged sightings of mystery big cats, "
        "primarily in the UK and Australia where no native big cats exist."
    ),
    "Undiscovered Species": (
        "Celebrate cryptids that turned out to be real. The coelacanth was thought "
        "extinct for 65 million years until caught in 1938. The okapi was dismissed "
        "as fantasy until 1901. The giant squid was a myth until photographed alive "
        "in 2004. This mode maps discovery locations of formerly cryptid species "
        "and ongoing searches for creatures that may yet be proven real."
    ),
    "Cryptid Hotspots": (
        "Identify geographic regions with the highest concentration and diversity "
        "of cryptid reports. Some areas seem to attract far more sightings than "
        "others -- whether due to wilderness, folklore traditions, or something "
        "else entirely. This mode aggregates multi-category sighting data to "
        "reveal the world's most cryptid-active zones."
    ),
}

# ═══════════════════════════════════════════════════════
# CURATED DATASETS
# ═══════════════════════════════════════════════════════

def _lake_monsters_data():
    """Curated dataset of lake monster sightings and legends worldwide."""
    return pd.DataFrame([
        {"name": "Loch Ness Monster (Nessie)", "lat": 57.3229, "lon": -4.4244,
         "location": "Loch Ness, Scotland", "country": "United Kingdom",
         "first_reported": "565 AD", "description": "Long-necked aquatic creature, possibly plesiosaur-like. Over 1,000 recorded sightings.",
         "status": "Active legend", "evidence_level": "Photographs, sonar"},
        {"name": "Ogopogo (Naitaka)", "lat": 49.8610, "lon": -119.4960,
         "location": "Okanagan Lake, British Columbia", "country": "Canada",
         "first_reported": "1872", "description": "Multi-humped serpentine creature, 12-15m long. Indigenous Syilx people call it Naitaka.",
         "status": "Active legend", "evidence_level": "Video, photographs"},
        {"name": "Champ", "lat": 44.5333, "lon": -73.3333,
         "location": "Lake Champlain, Vermont/New York", "country": "USA",
         "first_reported": "1609", "description": "Large serpentine creature. Samuel de Champlain may have recorded first European sighting.",
         "status": "Active legend", "evidence_level": "Photographs, echolocation"},
        {"name": "Nahuelito", "lat": -41.0700, "lon": -71.3500,
         "location": "Nahuel Huapi Lake, Patagonia", "country": "Argentina",
         "first_reported": "1897", "description": "Large hump-backed creature in deep glacial lake. Similar to Nessie descriptions.",
         "status": "Active legend", "evidence_level": "Photographs"},
        {"name": "Lagarfljot Worm (Lagarfljotsormurinn)", "lat": 65.0833, "lon": -14.3833,
         "location": "Lagarfljot Lake, Eastern Iceland", "country": "Iceland",
         "first_reported": "1345", "description": "Giant worm or serpent in glacial lake. 2012 video went viral worldwide.",
         "status": "Active legend", "evidence_level": "Video"},
        {"name": "Mokele-mbembe", "lat": 1.6200, "lon": 16.0400,
         "location": "Lake Tele, Republic of Congo", "country": "Republic of Congo",
         "first_reported": "1776", "description": "Sauropod-like creature reported in Congo Basin swamps. Multiple expeditions mounted.",
         "status": "Active legend", "evidence_level": "Witness testimony"},
        {"name": "Storsjoodjuret", "lat": 63.1792, "lon": 14.6357,
         "location": "Lake Storsjon, Jamtland", "country": "Sweden",
         "first_reported": "1635", "description": "Serpentine lake monster, legally protected by Swedish authorities from 1986-2005.",
         "status": "Active legend", "evidence_level": "Multiple witnesses"},
        {"name": "Selma (Seljordsorm)", "lat": 59.4833, "lon": 9.1167,
         "location": "Lake Seljord, Telemark", "country": "Norway",
         "first_reported": "1750", "description": "Sea serpent-like creature in Norwegian lake. Sonar contacts recorded.",
         "status": "Active legend", "evidence_level": "Sonar, video"},
        {"name": "Morag", "lat": 56.8833, "lon": -5.6667,
         "location": "Loch Morar, Scotland", "country": "United Kingdom",
         "first_reported": "1887", "description": "Second most famous Scottish lake monster after Nessie. Loch Morar is the deepest UK lake.",
         "status": "Active legend", "evidence_level": "Witness testimony"},
        {"name": "Memphre", "lat": 45.0833, "lon": -72.1167,
         "location": "Lake Memphremagog, Quebec/Vermont", "country": "Canada/USA",
         "first_reported": "1816", "description": "Dark serpentine creature crossing the US-Canada border lake.",
         "status": "Active legend", "evidence_level": "Witness testimony"},
        {"name": "Issie", "lat": 31.2667, "lon": 130.5833,
         "location": "Lake Ikeda, Kagoshima", "country": "Japan",
         "first_reported": "1961", "description": "Japanese lake monster with humps. Statues and monuments at the lake honor the creature.",
         "status": "Cultural icon", "evidence_level": "Witness testimony"},
        {"name": "Trunko", "lat": -31.1000, "lon": 30.2333,
         "location": "Margate Beach, KwaZulu-Natal", "country": "South Africa",
         "first_reported": "1924", "description": "White-furred sea creature washed ashore. Fought two orcas. Possibly a globster.",
         "status": "Historical", "evidence_level": "Newspaper accounts"},
        {"name": "Bunyip", "lat": -36.7500, "lon": 145.7000,
         "location": "Murray River system, Victoria", "country": "Australia",
         "first_reported": "Pre-colonial", "description": "Aboriginal water spirit. Described as large, dark, with flippers. Multiple forms in legend.",
         "status": "Folklore", "evidence_level": "Indigenous oral history"},
        {"name": "Manipogo", "lat": 51.1167, "lon": -98.7833,
         "location": "Lake Manitoba, Manitoba", "country": "Canada",
         "first_reported": "1908", "description": "Named after Ogopogo. Serpentine creature up to 15m long reported by fishermen.",
         "status": "Active legend", "evidence_level": "Photographs"},
        {"name": "Cadborosaurus (Caddy)", "lat": 48.4284, "lon": -123.3656,
         "location": "Cadboro Bay, Victoria, BC", "country": "Canada",
         "first_reported": "1933", "description": "Horse-headed sea serpent seen in Pacific Northwest coastal waters. Also reported in San Francisco Bay.",
         "status": "Active legend", "evidence_level": "Photographs, carcass claims"},
        {"name": "Muc-sheilch (Loch Maree Monster)", "lat": 57.6833, "lon": -5.4333,
         "location": "Loch Maree, Scottish Highlands", "country": "United Kingdom",
         "first_reported": "1850", "description": "Multi-humped creature in a remote Highland loch surrounded by ancient Caledonian pine forest.",
         "status": "Active legend", "evidence_level": "Witness testimony"},
        {"name": "Tessie", "lat": 39.0968, "lon": -120.0324,
         "location": "Lake Tahoe, California/Nevada", "country": "USA",
         "first_reported": "1950s", "description": "Large serpentine creature in the deep alpine lake. Washoe and Paiute tribes have older legends.",
         "status": "Active legend", "evidence_level": "Witness testimony"},
        {"name": "Bear Lake Monster", "lat": 42.0333, "lon": -111.3333,
         "location": "Bear Lake, Utah/Idaho", "country": "USA",
         "first_reported": "1868", "description": "Multiple creature sightings in the turquoise border lake. Described as serpentine with legs.",
         "status": "Active legend", "evidence_level": "Historical accounts"},
        {"name": "Brosno Dragon", "lat": 57.0333, "lon": 32.4500,
         "location": "Lake Brosno, Tver Oblast", "country": "Russia",
         "first_reported": "13th century", "description": "Dragon-like creature allegedly swallowed a Tatar-Mongol army member. Still reported today.",
         "status": "Active legend", "evidence_level": "Sonar anomalies"},
        {"name": "Thetis Lake Monster", "lat": 48.4600, "lon": -123.4700,
         "location": "Thetis Lake, British Columbia", "country": "Canada",
         "first_reported": "1972", "description": "Silver-scaled humanoid creature emerging from the lake. One of few amphibious cryptid reports.",
         "status": "Historical", "evidence_level": "Police report filed"},
    ])


def _bigfoot_yeti_data():
    """Curated dataset of Bigfoot, Yeti, and similar bipedal cryptid sighting areas."""
    return pd.DataFrame([
        {"name": "Bluff Creek Bigfoot (Patterson-Gimlin film)", "lat": 41.4426, "lon": -123.8914,
         "location": "Bluff Creek, Northern California", "country": "USA",
         "first_reported": "1967", "creature_type": "Sasquatch",
         "description": "Site of the famous 1967 Patterson-Gimlin film, the most analyzed bigfoot footage ever recorded.",
         "status": "Iconic sighting", "evidence_level": "Film footage"},
        {"name": "Ape Canyon Incident", "lat": 46.1897, "lon": -122.1533,
         "location": "Mount St. Helens, Washington", "country": "USA",
         "first_reported": "1924", "creature_type": "Sasquatch",
         "description": "Miners claimed their cabin was attacked by a group of ape-like creatures. Canyon named after the incident.",
         "status": "Historical", "evidence_level": "Witness testimony"},
        {"name": "Skookum Meadows Cast", "lat": 46.2300, "lon": -121.7800,
         "location": "Gifford Pinchot National Forest, WA", "country": "USA",
         "first_reported": "2000", "creature_type": "Sasquatch",
         "description": "Body imprint found in mud by BFRO expedition. Analyzed by primate experts.",
         "status": "Investigated", "evidence_level": "Cast impression"},
        {"name": "Himalayan Yeti Zone", "lat": 27.9881, "lon": 86.9250,
         "location": "Everest Region, Nepal", "country": "Nepal",
         "first_reported": "1832", "creature_type": "Yeti",
         "description": "The Abominable Snowman. Sherpa culture includes extensive yeti lore. Footprints photographed by Shipton in 1951.",
         "status": "Active legend", "evidence_level": "Footprints, hair samples"},
        {"name": "Pangboche Yeti Scalp", "lat": 27.8550, "lon": 86.7900,
         "location": "Pangboche Monastery, Nepal", "country": "Nepal",
         "first_reported": "~1400s", "creature_type": "Yeti",
         "description": "Monastery held alleged yeti scalp and hand relic for centuries. Hand stolen 1991, DNA tested as human.",
         "status": "Cultural artifact", "evidence_level": "Physical artifacts"},
        {"name": "Yowie Sightings Cluster", "lat": -33.7000, "lon": 150.3000,
         "location": "Blue Mountains, New South Wales", "country": "Australia",
         "first_reported": "1795", "creature_type": "Yowie",
         "description": "Australian hairy hominid. Aboriginal rock art depicts large ape-like creatures. Concentrated sightings in Blue Mountains.",
         "status": "Active legend", "evidence_level": "Witness testimony, footprints"},
        {"name": "Orang Pendek Territory", "lat": -1.6950, "lon": 101.5325,
         "location": "Kerinci Seblat National Park, Sumatra", "country": "Indonesia",
         "first_reported": "1818", "creature_type": "Orang Pendek",
         "description": "Short bipedal ape. Most scientifically credible cryptid. Hair samples analyzed. Multiple expeditions.",
         "status": "Under investigation", "evidence_level": "Hair samples, footprint casts"},
        {"name": "Almas Region", "lat": 47.9200, "lon": 106.9200,
         "location": "Altai Mountains, Mongolia", "country": "Mongolia",
         "first_reported": "15th century", "creature_type": "Almas",
         "description": "Mongolian wild man. Described as more human-like than Bigfoot. May represent surviving Neanderthal population.",
         "status": "Folklore", "evidence_level": "Witness testimony"},
        {"name": "Yeren Sightings", "lat": 31.7500, "lon": 110.6700,
         "location": "Shennongjia, Hubei Province", "country": "China",
         "first_reported": "Pre-historic", "creature_type": "Yeren",
         "description": "Chinese wildman. Over 400 reported sightings. Government-sponsored expeditions in 1970s-80s. Hair samples collected.",
         "status": "Active investigation", "evidence_level": "Hair samples, government expeditions"},
        {"name": "Skunk Ape Territory", "lat": 25.7617, "lon": -80.8998,
         "location": "Everglades, Florida", "country": "USA",
         "first_reported": "1957", "creature_type": "Skunk Ape",
         "description": "Florida's bigfoot variant. Distinguished by terrible smell. Numerous photos and reports from swamp regions.",
         "status": "Active legend", "evidence_level": "Photographs"},
        {"name": "Boggy Creek Fouke Monster", "lat": 33.2676, "lon": -93.8907,
         "location": "Fouke, Arkansas", "country": "USA",
         "first_reported": "1946", "creature_type": "Sasquatch variant",
         "description": "Inspired 'The Legend of Boggy Creek' (1972). Multiple families reported encounters over decades.",
         "status": "Active legend", "evidence_level": "Witness testimony"},
        {"name": "Mapinguari Territory", "lat": -3.4653, "lon": -62.2159,
         "location": "Amazon Rainforest, Brazil", "country": "Brazil",
         "first_reported": "Pre-colonial", "creature_type": "Mapinguari",
         "description": "Possibly surviving giant ground sloth. Described as large, foul-smelling, with backward feet. Indigenous accounts.",
         "status": "Folklore", "evidence_level": "Indigenous oral history"},
        {"name": "Barmanou Zone", "lat": 35.0000, "lon": 71.5000,
         "location": "Chitral, Khyber Pakhtunkhwa", "country": "Pakistan",
         "first_reported": "Ancient", "creature_type": "Barmanou",
         "description": "Pakistani bigfoot equivalent found in remote northern mountains. Described as bipedal, covered in hair.",
         "status": "Folklore", "evidence_level": "Witness testimony"},
        {"name": "Sasquatch Provincial Park", "lat": 49.1000, "lon": -121.9500,
         "location": "Harrison Hot Springs, British Columbia", "country": "Canada",
         "first_reported": "1920s", "creature_type": "Sasquatch",
         "description": "Named for local First Nations legends. Annual Sasquatch Days festival. Numerous sightings nearby.",
         "status": "Cultural landmark", "evidence_level": "Ongoing reports"},
        {"name": "Ohio Grassman Region", "lat": 40.7990, "lon": -81.3784,
         "location": "Salt Fork State Park, Ohio", "country": "USA",
         "first_reported": "1978", "creature_type": "Grassman",
         "description": "Ohio's bigfoot variant. Annual Bigfoot Conference held here. Hundreds of reports from eastern Ohio.",
         "status": "Active legend", "evidence_level": "Footprint casts"},
        {"name": "Mogollon Monster Territory", "lat": 34.4200, "lon": -111.1700,
         "location": "Mogollon Rim, Arizona", "country": "USA",
         "first_reported": "1903", "creature_type": "Mogollon Monster",
         "description": "Arizona's bigfoot along the Mogollon Rim escarpment. Described as 7ft tall, foul-smelling, aggressive.",
         "status": "Active legend", "evidence_level": "Witness testimony"},
        {"name": "Batutut Zone", "lat": 14.0583, "lon": 108.2772,
         "location": "Vu Quang, Vietnam", "country": "Vietnam",
         "first_reported": "1947", "creature_type": "Batutut / Nguoi Rung",
         "description": "Vietnamese forest man. Region also yielded real discoveries: saola (1992) and giant muntjac (1994).",
         "status": "Under investigation", "evidence_level": "Witness testimony"},
        {"name": "Agogwe Territory", "lat": -8.0000, "lon": 32.9000,
         "location": "Western Tanzania", "country": "Tanzania",
         "first_reported": "1900", "creature_type": "Agogwe",
         "description": "Small bipedal hominid of East Africa. Described as 1.2-1.5m tall, reddish-brown fur. Possible unknown primate.",
         "status": "Folklore", "evidence_level": "Colonial-era accounts"},
    ])


def _sea_serpents_data():
    """Curated dataset of sea serpent and kraken sightings."""
    return pd.DataFrame([
        {"name": "HMS Daedalus Encounter", "lat": -24.5000, "lon": 9.3700,
         "location": "South Atlantic Ocean", "country": "At Sea",
         "year": "1848", "description": "British warship crew observed 20m serpentine creature for 20 minutes. Officially reported to the Admiralty.",
         "creature_type": "Sea Serpent", "evidence_level": "Naval report"},
        {"name": "Gloucester Sea Serpent", "lat": 42.6159, "lon": -70.6600,
         "location": "Cape Ann, Massachusetts", "country": "USA",
         "year": "1817", "description": "Multiple witnesses over several weeks. Linnaean Society sent investigators. Hundreds of depositions filed.",
         "creature_type": "Sea Serpent", "evidence_level": "Legal depositions"},
        {"name": "Cadborosaurus Carcass", "lat": 49.3700, "lon": -126.2700,
         "location": "Nootka Sound, Vancouver Island", "country": "Canada",
         "year": "1937", "description": "Intact creature found in sperm whale stomach at Naden Harbour whaling station. Photographed but lost.",
         "creature_type": "Cadborosaurus", "evidence_level": "Photograph of carcass"},
        {"name": "Kraken Origin - Maelstrom", "lat": 68.0500, "lon": 14.6500,
         "location": "Lofoten Islands, Norway", "country": "Norway",
         "year": "1180", "description": "Norse saga origin of the Kraken legend. Described as island-sized. Likely based on giant squid encounters.",
         "creature_type": "Kraken", "evidence_level": "Historical texts"},
        {"name": "Bishop Erik Pontoppidan Account", "lat": 60.3913, "lon": 5.3221,
         "location": "Bergen, Norway", "country": "Norway",
         "year": "1752", "description": "Published detailed natural history of Kraken. Described creature 2.4 km in circumference.",
         "creature_type": "Kraken", "evidence_level": "Published account"},
        {"name": "Giant Squid - Thimble Tickle", "lat": 49.3300, "lon": -53.9200,
         "location": "Thimble Tickle, Newfoundland", "country": "Canada",
         "year": "1878", "description": "Giant squid washed ashore, 16.5m total length. One of the largest specimens ever measured.",
         "creature_type": "Giant Squid (confirmed)", "evidence_level": "Physical specimen"},
        {"name": "Zuiyo Maru Carcass", "lat": -33.0000, "lon": 173.0000,
         "location": "Off Christchurch, New Zealand", "country": "New Zealand",
         "year": "1977", "description": "Japanese trawler hauled up 10m decomposed carcass. Photographed before discarded. Likely basking shark.",
         "creature_type": "Unidentified carcass", "evidence_level": "Photographs, tissue sample"},
        {"name": "Stinson Beach Monster", "lat": 37.9011, "lon": -122.6394,
         "location": "Stinson Beach, California", "country": "USA",
         "year": "1983", "description": "30m creature observed by highway workers from cliffs above the beach. Multiple witnesses.",
         "creature_type": "Sea Serpent", "evidence_level": "Witness testimony"},
        {"name": "Colossal Squid Discovery", "lat": -60.4000, "lon": 170.0000,
         "location": "Ross Sea, Antarctica", "country": "Antarctica",
         "year": "2003", "description": "Mesonychoteuthis hamiltoni. Larger than giant squid with rotating hooks on tentacles. Real creature.",
         "creature_type": "Colossal Squid (confirmed)", "evidence_level": "Physical specimen"},
        {"name": "Leviathan Biblical Region", "lat": 32.0000, "lon": 34.7500,
         "location": "Eastern Mediterranean", "country": "Mediterranean",
         "year": "~600 BC", "description": "Biblical sea monster described in Job, Psalms, Isaiah. May reflect ancient encounters with large marine life.",
         "creature_type": "Leviathan", "evidence_level": "Religious texts"},
        {"name": "Morgawr Sightings", "lat": 50.0833, "lon": -5.1167,
         "location": "Falmouth Bay, Cornwall", "country": "United Kingdom",
         "year": "1975", "description": "Long-necked sea creature photographed by 'Mary F.' Multiple witnesses over following decades.",
         "creature_type": "Sea Serpent", "evidence_level": "Photographs"},
        {"name": "Con Rit - Spiny Sea Serpent", "lat": 11.9500, "lon": 108.4500,
         "location": "Along Hau, Vietnam", "country": "Vietnam",
         "year": "1883", "description": "Armored, segmented sea creature. 18m carcass examined. Described as resembling giant centipede.",
         "creature_type": "Armored sea creature", "evidence_level": "Physical examination"},
        {"name": "Stronsay Beast", "lat": 59.1500, "lon": -2.6000,
         "location": "Stronsay, Orkney Islands", "country": "United Kingdom",
         "year": "1808", "description": "17m carcass washed ashore. Initially declared a new species. Later identified as basking shark.",
         "creature_type": "Globster", "evidence_level": "Physical remains"},
        {"name": "U-28 Sea Creature", "lat": 52.0000, "lon": -12.0000,
         "location": "Atlantic, off Ireland", "country": "At Sea",
         "year": "1915", "description": "German U-boat crew reported enormous creature hurled from water by torpedo explosion of SS Iberian.",
         "creature_type": "Unknown marine creature", "evidence_level": "Military account"},
        {"name": "Gambo Carcass", "lat": 13.4500, "lon": -16.5800,
         "location": "Bungalow Beach, Gambia", "country": "Gambia",
         "year": "1983", "description": "4.5m dolphin-like creature with beak. Owen Burnham documented measurements before locals buried it.",
         "creature_type": "Unknown cetacean", "evidence_level": "Detailed measurements"},
    ])


def _chupacabra_data():
    """Curated dataset of Chupacabra and blood-draining cryptid sightings."""
    return pd.DataFrame([
        {"name": "Moca Vampire (Original Chupacabra)", "lat": 18.3947, "lon": -67.1133,
         "location": "Moca, Puerto Rico", "country": "Puerto Rico",
         "year": "1975", "description": "The earliest chupacabra-type reports. Livestock found drained of blood. Called 'El Vampiro de Moca'.",
         "creature_type": "Proto-Chupacabra", "evidence_level": "Livestock deaths"},
        {"name": "Canovanas Chupacabra Wave", "lat": 18.3794, "lon": -65.9007,
         "location": "Canovanas, Puerto Rico", "country": "Puerto Rico",
         "year": "1995", "description": "Mayor organized armed patrols. Over 200 animals killed. Madelyne Tolentino's key eyewitness description.",
         "creature_type": "Chupacabra", "evidence_level": "Mass livestock deaths"},
        {"name": "Calama Attacks", "lat": -22.4560, "lon": -68.9293,
         "location": "Calama, Atacama Desert", "country": "Chile",
         "year": "2000", "description": "Major wave of livestock attacks in mining city. Hundreds of animals found bloodless. National news coverage.",
         "creature_type": "Chupacabra", "evidence_level": "Livestock deaths, media"},
        {"name": "Cuero TX Chupacabra", "lat": 29.0936, "lon": -97.2892,
         "location": "Cuero, Texas", "country": "USA",
         "year": "2007", "description": "Phylis Canion found strange carcass. DNA tested as coyote with mange. Sparked debate about chupacabra identity.",
         "creature_type": "Chupacabra (coyote/mange)", "evidence_level": "Physical carcass, DNA"},
        {"name": "Toluca Sightings", "lat": 19.2826, "lon": -99.6557,
         "location": "Toluca, State of Mexico", "country": "Mexico",
         "year": "1996", "description": "Wave of livestock attacks attributed to chupacabra. Reports spread through central Mexico.",
         "creature_type": "Chupacabra", "evidence_level": "Livestock deaths"},
        {"name": "Sao Paulo State Attacks", "lat": -23.5505, "lon": -46.6333,
         "location": "Sao Paulo state, Brazil", "country": "Brazil",
         "year": "1997", "description": "Multiple rural communities reported bloodless livestock. Called 'Chupa-cabra' in Brazilian Portuguese.",
         "creature_type": "Chupacabra", "evidence_level": "Livestock deaths"},
        {"name": "Nicaragua Wave", "lat": 12.1150, "lon": -86.2362,
         "location": "Managua region, Nicaragua", "country": "Nicaragua",
         "year": "2000", "description": "Farmers reported goats and chickens found drained. Multiple communities across the region affected.",
         "creature_type": "Chupacabra", "evidence_level": "Livestock deaths"},
        {"name": "Elmendorf Beast", "lat": 29.3500, "lon": -98.2000,
         "location": "Elmendorf, Texas", "country": "USA",
         "year": "2004", "description": "Rancher shot strange hairless animal. DNA showed coyote. Became one of the most famous 'chupacabra carcasses'.",
         "creature_type": "Chupacabra (coyote)", "evidence_level": "Physical carcass, DNA"},
        {"name": "Varginha ET/Chupacabra Link", "lat": -21.5513, "lon": -45.4363,
         "location": "Varginha, Minas Gerais", "country": "Brazil",
         "year": "1996", "description": "Strange creatures captured by military. Linked by some to chupacabra phenomenon. Major Brazilian case.",
         "creature_type": "Unknown creature", "evidence_level": "Witness testimony, military"},
        {"name": "Oaxaca Attacks", "lat": 17.0654, "lon": -96.7236,
         "location": "Oaxaca, Mexico", "country": "Mexico",
         "year": "1998", "description": "Rural communities lost dozens of goats. Puncture wounds consistent with chupacabra description.",
         "creature_type": "Chupacabra", "evidence_level": "Livestock deaths"},
        {"name": "Dominican Republic Wave", "lat": 18.4861, "lon": -69.9312,
         "location": "Santo Domingo region", "country": "Dominican Republic",
         "year": "1995", "description": "Concurrent with Puerto Rico wave. Hundreds of animals found with puncture wounds and drained of blood.",
         "creature_type": "Chupacabra", "evidence_level": "Livestock deaths"},
        {"name": "Penuelas Sightings", "lat": 18.0563, "lon": -66.7260,
         "location": "Penuelas, Puerto Rico", "country": "Puerto Rico",
         "year": "1995", "description": "Multiple witnesses described spiny-backed bipedal creature. Consistent with the 'classic' chupacabra form.",
         "creature_type": "Chupacabra", "evidence_level": "Multiple witnesses"},
        {"name": "San Antonio TX Capture", "lat": 29.4241, "lon": -98.4936,
         "location": "San Antonio, Texas", "country": "USA",
         "year": "2014", "description": "Couple captured live hairless animal. Identified as raccoon with severe mange. Media labeled it chupacabra.",
         "creature_type": "Chupacabra (raccoon)", "evidence_level": "Live capture, ID'd"},
        {"name": "Peruvian Attacks", "lat": -12.0464, "lon": -77.0428,
         "location": "Lima region, Peru", "country": "Peru",
         "year": "1999", "description": "Livestock deaths in rural areas around Lima attributed to chupacabra. Part of South American wave.",
         "creature_type": "Chupacabra", "evidence_level": "Livestock deaths"},
    ])


def _mothman_winged_data():
    """Curated dataset of Mothman and winged cryptid sightings."""
    return pd.DataFrame([
        {"name": "Mothman - TNT Area", "lat": 38.7321, "lon": -82.0242,
         "location": "Point Pleasant, West Virginia", "country": "USA",
         "year": "1966-1967", "creature_type": "Mothman",
         "description": "Over 100 sightings of red-eyed winged humanoid. Ended with Silver Bridge collapse killing 46 people.",
         "evidence_level": "Mass sightings, police reports"},
        {"name": "Jersey Devil Origin", "lat": 39.7853, "lon": -74.5700,
         "location": "Pine Barrens, New Jersey", "country": "USA",
         "year": "1735", "creature_type": "Jersey Devil",
         "description": "Legendary 13th child of Mother Leeds. 1909 wave had thousands of sightings across NJ and PA in one week.",
         "evidence_level": "Historical accounts, mass sightings"},
        {"name": "Owlman of Mawnan", "lat": 50.1000, "lon": -5.0833,
         "location": "Mawnan, Cornwall", "country": "United Kingdom",
         "year": "1976", "creature_type": "Owlman",
         "description": "Owl-like humanoid seen near Mawnan Old Church. Called Britain's Mothman. Multiple witnesses including tourists.",
         "evidence_level": "Witness testimony"},
        {"name": "Chicago Mothman Flap", "lat": 41.8781, "lon": -87.6298,
         "location": "Chicago, Illinois", "country": "USA",
         "year": "2017-2020", "creature_type": "Winged Humanoid",
         "description": "Over 55 sightings of large winged humanoid over Chicago. Investigated by MUFON and Singular Fortean Society.",
         "evidence_level": "Multiple witness reports"},
        {"name": "Thunderbird Sighting - Tombstone", "lat": 31.7129, "lon": -110.0676,
         "location": "Tombstone, Arizona", "country": "USA",
         "year": "1890", "creature_type": "Thunderbird",
         "description": "Tombstone Epitaph reported cowboys killed enormous bird with 10m wingspan. 'Missing thunderbird photo' became legend.",
         "evidence_level": "Newspaper account"},
        {"name": "Piasa Bird", "lat": 38.8800, "lon": -90.1300,
         "location": "Alton, Illinois", "country": "USA",
         "year": "1673", "creature_type": "Piasa",
         "description": "Giant bird painted on Mississippi River bluff by Illini people. Described by Father Marquette. Dragon-like creature.",
         "evidence_level": "Historical account, petroglyphs"},
        {"name": "Ahool Encounters", "lat": -7.2500, "lon": 106.2000,
         "location": "Java, Indonesia", "country": "Indonesia",
         "year": "1925", "creature_type": "Ahool",
         "description": "Giant bat with 3m wingspan in Javanese rainforest. Named for its call. Possibly a surviving giant bat species.",
         "evidence_level": "Explorer accounts"},
        {"name": "Kongamato Territory", "lat": -12.0000, "lon": 28.0000,
         "location": "Jiundu Swamps, Zambia", "country": "Zambia",
         "year": "1923", "creature_type": "Kongamato",
         "description": "Pterodactyl-like flying creature. Locals identified it when shown illustrations of pteranodons.",
         "evidence_level": "Explorer interviews"},
        {"name": "Ropen Sightings", "lat": -5.5000, "lon": 147.0000,
         "location": "Umboi Island, Papua New Guinea", "country": "Papua New Guinea",
         "year": "1994", "creature_type": "Ropen",
         "description": "Bioluminescent flying creature. Described as pterosaur-like by natives. Multiple expedition attempts.",
         "evidence_level": "Witness testimony, expedition reports"},
        {"name": "La Lechuza Territory", "lat": 26.2034, "lon": -98.2300,
         "location": "Rio Grande Valley, Texas", "country": "USA",
         "year": "Traditional", "creature_type": "La Lechuza",
         "description": "Giant owl-witch of Mexican-American folklore. Human-faced owl with 4.5m wingspan. Reports across South Texas.",
         "evidence_level": "Folklore, sighting reports"},
        {"name": "Batsquatch Sighting", "lat": 46.1912, "lon": -122.1944,
         "location": "Mount St. Helens, Washington", "country": "USA",
         "year": "1994", "creature_type": "Batsquatch",
         "description": "Blue-furred, bat-winged humanoid seen near Mount St. Helens. Yellow eyes, bird-like feet.",
         "evidence_level": "Single witness"},
        {"name": "Mothman Statue Location", "lat": 38.8423, "lon": -82.1371,
         "location": "Point Pleasant, WV (downtown)", "country": "USA",
         "year": "2003 (statue)", "creature_type": "Mothman (memorial)",
         "description": "12-foot stainless steel Mothman statue by Bob Roach. Annual Mothman Festival draws thousands.",
         "evidence_level": "Cultural landmark"},
        {"name": "Van Meter Visitor", "lat": 42.0192, "lon": -94.2322,
         "location": "Van Meter, Iowa", "country": "USA",
         "year": "1903", "creature_type": "Winged creature",
         "description": "Winged creature with horn-like light beam. Multiple prominent citizens witnessed it. Fired upon but unharmed.",
         "evidence_level": "Multiple witnesses, newspaper"},
        {"name": "Popobawa Territory", "lat": -6.1659, "lon": 39.2026,
         "location": "Zanzibar, Tanzania", "country": "Tanzania",
         "year": "1965", "creature_type": "Popobawa",
         "description": "Bat-winged cyclops creature. Major panic episodes in 1995 and 2001. Cultural phenomenon in Zanzibar.",
         "evidence_level": "Mass panic events"},
    ])


def _dragon_legends_data():
    """Curated dataset of dragon mythology and alleged sighting locations."""
    return pd.DataFrame([
        {"name": "Wawel Dragon (Smok Wawelski)", "lat": 50.0540, "lon": 19.9355,
         "location": "Krakow, Poland", "country": "Poland",
         "era": "Ancient legend", "dragon_type": "European fire-breather",
         "description": "Dragon lived in cave beneath Wawel Castle. Slain by cobbler Skuba using sulfur-stuffed sheep. Cave is a tourist site.",
         "evidence_level": "Folklore, Dragon's Den cave"},
        {"name": "St. George Dragon Site", "lat": 51.5074, "lon": -0.1278,
         "location": "London, England (patron saint)", "country": "United Kingdom",
         "era": "~300 AD", "dragon_type": "European dragon",
         "description": "St. George and the Dragon. Patron saint of England. Dragon-slaying tradition from Lydda (modern Israel).",
         "evidence_level": "Religious legend"},
        {"name": "Chinese Dragon (Long) Origin", "lat": 34.2658, "lon": 108.9541,
         "location": "Xi'an, China (ancient capital)", "country": "China",
         "era": "5000+ years", "dragon_type": "Chinese Lung Dragon",
         "description": "Benevolent water/rain deity. Dragon bones (fossils) collected for traditional medicine. Central to Chinese culture.",
         "evidence_level": "Continuous cultural tradition"},
        {"name": "Quetzalcoatl Temple", "lat": 19.6925, "lon": -98.8438,
         "location": "Teotihuacan, Mexico", "country": "Mexico",
         "era": "200 BC - 550 AD", "dragon_type": "Feathered Serpent",
         "description": "Quetzalcoatl - the feathered serpent god. Temple adorned with serpent heads. Pan-Mesoamerican dragon figure.",
         "evidence_level": "Archaeological site"},
        {"name": "Naga Kingdom", "lat": 13.7563, "lon": 100.5018,
         "location": "Bangkok/Mekong region", "country": "Thailand",
         "era": "Ancient", "dragon_type": "Naga (serpent dragon)",
         "description": "Multi-headed serpent dragons of Buddhist/Hindu mythology. Naga Fireballs seen rising from Mekong River annually.",
         "evidence_level": "Ongoing phenomenon (Naga Fireballs)"},
        {"name": "Fafnir's Lair", "lat": 61.0000, "lon": 10.0000,
         "location": "Gnitaheior (Norse legend)", "country": "Norway",
         "era": "13th century", "dragon_type": "Norse dwarf-turned-dragon",
         "description": "Dragon from Volsunga Saga. Slain by Sigurd/Siegfried. Guarded cursed gold. Basis for Tolkien's Smaug.",
         "evidence_level": "Norse sagas"},
        {"name": "Zmey Gorynych Legend", "lat": 55.7558, "lon": 37.6173,
         "location": "Moscow, Russia (Slavic culture center)", "country": "Russia",
         "era": "Medieval", "dragon_type": "Three-headed dragon",
         "description": "Slavic three-headed fire-breathing dragon. Slain by heroes Dobrynya Nikitich and Il'ya Muromets.",
         "evidence_level": "Slavic folklore"},
        {"name": "Wyvern of Mordiford", "lat": 52.0500, "lon": -2.5800,
         "location": "Mordiford, Herefordshire", "country": "United Kingdom",
         "era": "Medieval", "dragon_type": "Wyvern",
         "description": "Two-legged winged dragon terrorized village. Church painting depicted the wyvern until 1811 restoration.",
         "evidence_level": "Historical church records"},
        {"name": "Tatzelwurm Region", "lat": 47.3769, "lon": 11.5000,
         "location": "Bavarian/Austrian Alps", "country": "Austria/Germany",
         "era": "16th century+", "dragon_type": "Lindworm/Tatzelwurm",
         "description": "Cat-headed serpent of Alpine folklore. Reported even in 20th century. Possibly unknown large lizard species.",
         "evidence_level": "Persistent sightings"},
        {"name": "Ninki Nanka Territory", "lat": 13.4432, "lon": -15.3101,
         "location": "Gambia River region", "country": "Gambia",
         "era": "Traditional", "dragon_type": "West African dragon",
         "description": "Dragon-like creature of Gambian folklore. Described 30m long, scaly, with horse-like head. CFZ expedition 2006.",
         "evidence_level": "Expedition, oral tradition"},
        {"name": "Piasa Bird / Dragon Bluff", "lat": 38.8800, "lon": -90.1300,
         "location": "Alton, Illinois", "country": "USA",
         "era": "Pre-Columbian", "dragon_type": "Dragon-bird hybrid",
         "description": "Painted on Mississippi bluffs by Native Americans. Dragon with antlers, scales, wings, and long tail.",
         "evidence_level": "Rock art, historical accounts"},
        {"name": "Dragon Well (Longjing)", "lat": 30.2200, "lon": 120.1200,
         "location": "Hangzhou, Zhejiang", "country": "China",
         "era": "Ancient", "dragon_type": "Chinese Dragon",
         "description": "Dragon Well village -- dragon said to live in the well controlling rain. Famous tea named after the legend.",
         "evidence_level": "Folklore, cultural site"},
        {"name": "Lake Brosno Dragon", "lat": 57.0333, "lon": 32.4500,
         "location": "Lake Brosno, Tver Oblast", "country": "Russia",
         "era": "13th century", "dragon_type": "Aquatic dragon",
         "description": "Dragon swallowed Tatar-Mongol warrior. Still reported. Sonar expeditions found deep anomalies.",
         "evidence_level": "Sonar, ongoing sightings"},
        {"name": "Y Ddraig Goch (Red Dragon)", "lat": 52.0582, "lon": -3.2209,
         "location": "Dinas Emrys, Snowdonia", "country": "Wales, UK",
         "era": "5th century", "dragon_type": "Red Dragon",
         "description": "Welsh national symbol. Legend says red and white dragons fight beneath the hill. Revealed by young Merlin.",
         "evidence_level": "National mythology"},
        {"name": "Bakunawa (Moon-eating Dragon)", "lat": 10.3157, "lon": 123.8854,
         "location": "Cebu, Philippines", "country": "Philippines",
         "era": "Pre-colonial", "dragon_type": "Sea Dragon",
         "description": "Serpent dragon that swallows the moon during eclipses. People would make noise to scare it away.",
         "evidence_level": "Indigenous mythology"},
    ])


def _werewolf_data():
    """Curated dataset of werewolf legends, trials, and sighting locations."""
    return pd.DataFrame([
        {"name": "Beast of Gevaudan", "lat": 44.7247, "lon": 3.5200,
         "location": "Gevaudan (Lozere), France", "country": "France",
         "year": "1764-1767", "creature_type": "Wolf-beast",
         "description": "Killed 100+ people. Described as enormous wolf with reddish fur. King Louis XV sent hunters. Two large wolves killed.",
         "evidence_level": "Historical records, death toll"},
        {"name": "Peter Stumpp Trial", "lat": 50.9375, "lon": 7.4017,
         "location": "Bedburg, Germany", "country": "Germany",
         "year": "1589", "creature_type": "Werewolf (trial)",
         "description": "Most famous werewolf trial. Serial killer claimed belt that transformed him. Executed by breaking wheel.",
         "evidence_level": "Court records"},
        {"name": "Gilles Garnier Trial", "lat": 47.0925, "lon": 5.4922,
         "location": "Dole, France", "country": "France",
         "year": "1573", "creature_type": "Werewolf (trial)",
         "description": "Hermit confessed to killing and eating children while in wolf form. Burned alive by order of parliament.",
         "evidence_level": "Court records"},
        {"name": "Livonian Werewolf (Thiess)", "lat": 57.2578, "lon": 22.3000,
         "location": "Jurgenburg (Zaube), Latvia", "country": "Latvia",
         "year": "1692", "creature_type": "Werewolf (trial)",
         "description": "Old Thiess claimed werewolves fought witches for fertility of crops. Unique benevolent werewolf testimony.",
         "evidence_level": "Court transcript"},
        {"name": "Beast of Bray Road", "lat": 42.6336, "lon": -88.5426,
         "location": "Elkhorn, Wisconsin", "country": "USA",
         "year": "1989-present", "creature_type": "Dogman/Werewolf",
         "description": "Wolf-like bipedal creature reported by dozens of witnesses on rural road. Investigated by journalist Linda Godfrey.",
         "evidence_level": "Multiple witnesses, ongoing"},
        {"name": "Michigan Dogman", "lat": 44.2500, "lon": -85.4000,
         "location": "Manistee County, Michigan", "country": "USA",
         "year": "1887", "creature_type": "Dogman",
         "description": "Bipedal canine creature. 'The Legend' song (1987) by DJ Steve Cook prompted hundreds of people to report sightings.",
         "evidence_level": "Multiple witnesses"},
        {"name": "Skinwalker Ranch", "lat": 40.2588, "lon": -109.8883,
         "location": "Uintah County, Utah", "country": "USA",
         "year": "Traditional / 1994+", "creature_type": "Skinwalker",
         "description": "Navajo legend of shape-shifting witches. Ranch became famous for paranormal activity. Now government-studied.",
         "evidence_level": "Navajo oral tradition, AAWSAP"},
        {"name": "Werewolf of Ansbach", "lat": 49.3006, "lon": 10.5719,
         "location": "Ansbach, Bavaria", "country": "Germany",
         "year": "1685", "creature_type": "Werewolf (trial)",
         "description": "Wolf terrorized town. Killed and dressed in human clothes, paraded through streets as the 'werewolf mayor.'",
         "evidence_level": "Historical records"},
        {"name": "Loup-Garou Territory", "lat": 30.2241, "lon": -92.0198,
         "location": "Cajun Country, Louisiana", "country": "USA",
         "year": "Traditional", "creature_type": "Loup-Garou",
         "description": "French-Cajun werewolf legend. Those who break Lent 7 years become loup-garou. Central to Cajun folklore.",
         "evidence_level": "Folklore tradition"},
        {"name": "Morbach Monster", "lat": 49.8000, "lon": 6.9000,
         "location": "Morbach, Rhineland-Palatinate", "country": "Germany",
         "year": "1988", "creature_type": "Werewolf",
         "description": "Last werewolf of Germany legend. US Air Force personnel at Hahn AB reported sighting when shrine candle went out.",
         "evidence_level": "Military witness, folklore"},
        {"name": "Lycaon of Arcadia", "lat": 37.5000, "lon": 22.1000,
         "location": "Arcadia, Peloponnese", "country": "Greece",
         "year": "~700 BC", "creature_type": "Werewolf (mythological)",
         "description": "King Lycaon transformed by Zeus as punishment. Origin of the word 'lycanthropy'. Mount Lykaion ritual site.",
         "evidence_level": "Greek mythology, archaeological site"},
        {"name": "Hexenwolf Region (Vaud)", "lat": 46.5197, "lon": 6.6323,
         "location": "Canton of Vaud, Switzerland", "country": "Switzerland",
         "year": "1448-1610", "creature_type": "Werewolf (trials)",
         "description": "Region with highest concentration of werewolf trials in history. Hundreds accused during witch trial period.",
         "evidence_level": "Court records"},
        {"name": "Benandanti / Werewolf Zone", "lat": 46.0711, "lon": 13.2345,
         "location": "Friuli, Italy", "country": "Italy",
         "year": "1575-1675", "creature_type": "Benandanti-werewolf",
         "description": "Night battles between benandanti and witches. Inquisition records. Some transformed into wolves to fight evil.",
         "evidence_level": "Inquisition records"},
        {"name": "Vseslav of Polotsk Legend", "lat": 55.4855, "lon": 28.7645,
         "location": "Polotsk, Belarus", "country": "Belarus",
         "year": "11th century", "creature_type": "Werewolf prince",
         "description": "Prince Vseslav described in 'The Tale of Igor's Campaign' as a werewolf. Born with a caul (sign of shapeshifting).",
         "evidence_level": "Literary/historical source"},
    ])


def _mystery_cats_data():
    """Curated dataset of phantom cat and out-of-place big cat sightings."""
    return pd.DataFrame([
        {"name": "Beast of Bodmin Moor", "lat": 50.5500, "lon": -4.6000,
         "location": "Bodmin Moor, Cornwall", "country": "United Kingdom",
         "year": "1978-present", "cat_type": "Phantom big cat",
         "description": "Large black cat reported for decades on Bodmin Moor. Government investigation in 1995 was inconclusive.",
         "evidence_level": "Video, livestock kills, government report"},
        {"name": "Beast of Exmoor", "lat": 51.1333, "lon": -3.6333,
         "location": "Exmoor, Devon/Somerset", "country": "United Kingdom",
         "year": "1983-present", "cat_type": "Phantom big cat",
         "description": "Large cat killing sheep. Royal Marines deployed in 1983. Multiple clear sightings but never captured.",
         "evidence_level": "Military deployment, livestock kills"},
        {"name": "Surrey Puma", "lat": 51.2500, "lon": -0.4000,
         "location": "Surrey, England", "country": "United Kingdom",
         "year": "1959-present", "cat_type": "Puma/cougar",
         "description": "One of the longest-running UK big cat cases. A puma was actually captured in 1966 near Worplesdon.",
         "evidence_level": "Live capture (1966), ongoing sightings"},
        {"name": "Blue Mountains Panther", "lat": -33.7500, "lon": 150.4167,
         "location": "Blue Mountains, NSW", "country": "Australia",
         "first_reported": "1890s", "cat_type": "Phantom panther",
         "description": "Large black cat in Blue Mountains. Theories include escaped circus animals or wartime mascots.",
         "evidence_level": "Multiple witnesses, paw prints"},
        {"name": "Gippsland Phantom Cat", "lat": -38.0000, "lon": 146.0000,
         "location": "Gippsland, Victoria", "country": "Australia",
         "year": "1970s-present", "cat_type": "Feral big cat",
         "description": "Large cats reported across Gippsland. DNA analysis of scat in 2003 showed domestic cat. Debate continues.",
         "evidence_level": "DNA analysis, photographs"},
        {"name": "Scottish Big Cat Sightings", "lat": 56.8167, "lon": -5.1167,
         "location": "Scottish Highlands", "country": "United Kingdom",
         "year": "1930s-present", "cat_type": "Phantom big cat",
         "description": "Numerous sightings across the Highlands. Kellas cat (melanistic hybrid) confirmed in 1984 as new feline form.",
         "evidence_level": "Kellas cat specimens, ongoing sightings"},
        {"name": "Eastern Cougar Reports", "lat": 42.0000, "lon": -72.0000,
         "location": "New England, USA", "country": "USA",
         "year": "1938-present", "cat_type": "Eastern cougar (declared extinct)",
         "description": "Eastern cougar declared extinct in 2011, yet hundreds of sightings reported annually. Some confirmed as western cougars.",
         "evidence_level": "Trail cameras, DNA (confirmed dispersals)"},
        {"name": "Beast of Gevaudan (Cat Theory)", "lat": 44.7247, "lon": 3.5200,
         "location": "Gevaudan (Lozere), France", "country": "France",
         "year": "1764-1767", "cat_type": "Unknown large predator",
         "description": "Some researchers believe the Beast was a big cat (lion or hyena) rather than a wolf. Exotic animal theory.",
         "evidence_level": "Historical analysis"},
        {"name": "Alien Big Cats of Denmark", "lat": 56.0000, "lon": 10.0000,
         "location": "Jutland, Denmark", "country": "Denmark",
         "year": "2005-present", "cat_type": "Phantom big cat",
         "description": "Multiple sightings of large cat in Danish countryside. Paw prints found. No native big cats in Denmark.",
         "evidence_level": "Paw prints, trail camera images"},
        {"name": "Tantanoola Tiger", "lat": -37.7000, "lon": 140.4500,
         "location": "Tantanoola, South Australia", "country": "Australia",
         "year": "1893-1895", "cat_type": "Mystery cat",
         "description": "Livestock killed by unknown predator. Eventually an Assyrian wolf was shot. But big cat sightings continued.",
         "evidence_level": "Physical specimen (wolf), ongoing sightings"},
        {"name": "Wildman of the Navidad", "lat": 29.0000, "lon": -96.9000,
         "location": "Navidad River, Texas", "country": "USA",
         "year": "1837-1850s", "cat_type": "Unknown large cat/creature",
         "description": "Large cat-like creature terrorized settlers along the Navidad River. Described as African lion-sized.",
         "evidence_level": "Historical accounts"},
        {"name": "Mngwa (Strange One)", "lat": -6.7924, "lon": 39.2083,
         "location": "Dar es Salaam region, Tanzania", "country": "Tanzania",
         "year": "1900s", "cat_type": "Unknown big cat",
         "description": "Larger than a lion, brindled grey. British colonial officer Frank W. Lane investigated. Possibly unknown cat species.",
         "evidence_level": "Colonial records, native accounts"},
        {"name": "Fen Tiger", "lat": 52.4000, "lon": 0.2000,
         "location": "Cambridgeshire Fens, England", "country": "United Kingdom",
         "year": "1982-present", "cat_type": "Phantom big cat",
         "description": "Large cat in the flat fenlands. Multiple witnesses, some with photographs. Possible escaped exotic pet.",
         "evidence_level": "Photographs, witness testimony"},
        {"name": "Beast of Dartmoor", "lat": 50.5719, "lon": -3.9201,
         "location": "Dartmoor, Devon", "country": "United Kingdom",
         "year": "1988-present", "cat_type": "Phantom big cat",
         "description": "Large puma-like cat on Dartmoor. Livestock kills with big cat characteristics. Part of UK ABC phenomenon.",
         "evidence_level": "Livestock kills, photographs"},
    ])


def _undiscovered_species_data():
    """Curated dataset of former cryptids proven real and ongoing searches."""
    return pd.DataFrame([
        {"name": "Coelacanth Discovery", "lat": -32.9833, "lon": 27.8833,
         "location": "East London, South Africa", "country": "South Africa",
         "year_discovered": "1938", "original_status": "Extinct 65 million years",
         "description": "Living fossil caught by fisherman. Marjorie Courtenay-Latimer identified it. Previously known only from fossils.",
         "significance": "Most famous cryptid-to-real discovery"},
        {"name": "Okapi Discovery", "lat": 1.5000, "lon": 28.5000,
         "location": "Ituri Forest, DR Congo", "country": "DR Congo",
         "year_discovered": "1901", "original_status": "Dismissed as fantasy",
         "description": "African unicorn. Sir Harry Johnston obtained skin and skulls. Giraffe relative in dense rainforest.",
         "significance": "Validated indigenous knowledge"},
        {"name": "Giant Squid First Photograph", "lat": 27.0000, "lon": 142.0000,
         "location": "Ogasawara Islands, Japan", "country": "Japan",
         "year_discovered": "2004 (photo) / 2012 (video)", "original_status": "Mythological Kraken",
         "description": "Tsunemi Kubodera photographed live giant squid at 900m depth. Video followed in 2012.",
         "significance": "Kraken legend vindicated"},
        {"name": "Mountain Gorilla Discovery", "lat": -1.4500, "lon": 29.4600,
         "location": "Virunga Mountains, Rwanda/DRC", "country": "Rwanda",
         "year_discovered": "1902", "original_status": "Native legend",
         "description": "Robert von Beringe shot two specimens at 3,000m. Western science initially dismissed African reports of giant apes.",
         "significance": "Validated reports of giant ape"},
        {"name": "Komodo Dragon Discovery", "lat": -8.5500, "lon": 119.4400,
         "location": "Komodo Island, Indonesia", "country": "Indonesia",
         "year_discovered": "1910", "original_status": "Dragon legend",
         "description": "3m carnivorous lizard. Dutch colonial reports dismissed until specimens obtained. Literal living dragon.",
         "significance": "Real-life dragon discovery"},
        {"name": "Platypus First Specimen", "lat": -33.7500, "lon": 150.7000,
         "location": "Hawkesbury River, NSW", "country": "Australia",
         "year_discovered": "1799", "original_status": "Presumed hoax",
         "description": "Scientists thought specimen was a taxidermy fraud. Duck bill, beaver tail, venomous spur, lays eggs, has fur.",
         "significance": "So bizarre it was assumed fake"},
        {"name": "Saola Discovery", "lat": 18.0000, "lon": 105.5000,
         "location": "Vu Quang, Vietnam", "country": "Vietnam",
         "year_discovered": "1992", "original_status": "Unknown to science",
         "description": "Asian unicorn. Large forest bovid discovered from hunter trophies. One of rarest mammals on Earth. Possibly <100 remain.",
         "significance": "Last large land mammal discovered"},
        {"name": "Giant Panda Western Discovery", "lat": 30.7000, "lon": 103.0000,
         "location": "Sichuan Province, China", "country": "China",
         "year_discovered": "1869", "original_status": "Local legend to Westerners",
         "description": "Pere Armand David obtained specimen. Western scientists doubted Chinese reports of black-and-white bears.",
         "significance": "Iconic conservation species"},
        {"name": "Megamouth Shark Discovery", "lat": 21.3069, "lon": -157.8583,
         "location": "Off Oahu, Hawaii", "country": "USA",
         "year_discovered": "1976", "original_status": "Unknown",
         "description": "4.5m filter-feeding shark entangled in US Navy anchor. Entirely new family of sharks. Only ~270 specimens known.",
         "significance": "Major shark species unknown until modern era"},
        {"name": "King Cheetah Confirmed", "lat": -24.0000, "lon": 31.5000,
         "location": "Kruger region, South Africa", "country": "South Africa",
         "year_discovered": "1926 (first skin) / 1981 (confirmed)", "original_status": "Unknown species",
         "description": "Large blotched cheetah thought to be separate species. Confirmed as rare fur mutation of regular cheetah.",
         "significance": "Mystery cat resolved by genetics"},
        {"name": "Bondegezou Discovery", "lat": -4.0800, "lon": 137.1700,
         "location": "Moni, Papua (Indonesia)", "country": "Indonesia",
         "year_discovered": "1994", "original_status": "Sacred spirit animal",
         "description": "Black-and-white tree kangaroo known to locals but new to science. Dingiso in local language.",
         "significance": "Sacred creature proven real"},
        {"name": "Bili Ape Investigation", "lat": 4.3000, "lon": 24.4000,
         "location": "Bili Forest, DR Congo", "country": "DR Congo",
         "year_discovered": "2003 (studied)", "original_status": "Giant chimp legend",
         "description": "Unusually large chimpanzees that sleep on the ground and howl at the moon. Possibly unique chimp population.",
         "significance": "Giant ape reports partially validated"},
        {"name": "Hoan Kiem Turtle", "lat": 21.0285, "lon": 105.8542,
         "location": "Hoan Kiem Lake, Hanoi", "country": "Vietnam",
         "year_discovered": "1967 (described)", "original_status": "Sacred legend",
         "description": "Sacred turtle of the Returned Sword legend. Rafetus vietnamensis -- critically endangered. Last Hanoi turtle died 2016.",
         "significance": "Legend proved to contain real species"},
        {"name": "Chacoan Peccary Discovery", "lat": -22.0000, "lon": -60.0000,
         "location": "Gran Chaco, Paraguay", "country": "Paraguay",
         "year_discovered": "1975", "original_status": "Known only from fossils (extinct)",
         "description": "Catagonus wagneri thought extinct for 10,000 years. Found alive by Ralph Wetzel. Local people knew it all along.",
         "significance": "Lazarus taxon -- back from extinction"},
    ])


def _cryptid_hotspots_data():
    """Curated dataset of global cryptid hotspot regions."""
    return pd.DataFrame([
        {"name": "Pacific Northwest (USA/Canada)", "lat": 47.5000, "lon": -122.0000,
         "location": "Washington/Oregon/BC", "country": "USA/Canada",
         "cryptid_types": "Sasquatch, Sea Serpents, Thunderbirds",
         "num_species": 5, "total_sightings_est": 10000,
         "description": "Highest concentration of Bigfoot reports. Dense forests, sparse population. BFRO database hub.",
         "hotspot_rank": 1},
        {"name": "Scottish Highlands", "lat": 57.0000, "lon": -5.0000,
         "location": "Highlands, Scotland", "country": "United Kingdom",
         "cryptid_types": "Lake Monsters, Big Cats, Faerie Folk",
         "num_species": 4, "total_sightings_est": 5000,
         "description": "Nessie, Morag, and numerous other lake monsters. Also phantom cat sightings across the Highlands.",
         "hotspot_rank": 2},
        {"name": "Himalayas/Nepal-Tibet", "lat": 28.0000, "lon": 86.0000,
         "location": "Nepal/Tibet/Bhutan", "country": "Nepal/China/Bhutan",
         "cryptid_types": "Yeti, Migoi, Dzu-teh",
         "num_species": 3, "total_sightings_est": 3000,
         "description": "Yeti heartland. Multiple Sherpa cultural traditions, mountaineer reports, and government expeditions.",
         "hotspot_rank": 3},
        {"name": "Congo Basin", "lat": 0.0000, "lon": 18.0000,
         "location": "Republic of Congo/DRC/Cameroon", "country": "Central Africa",
         "cryptid_types": "Mokele-mbembe, Emela-ntouka, Mbielu-mbielu-mbielu",
         "num_species": 5, "total_sightings_est": 2000,
         "description": "Multiple alleged living dinosaurs in vast unexplored swamps. Numerous expeditions since 1776.",
         "hotspot_rank": 4},
        {"name": "Appalachian Mountains", "lat": 37.0000, "lon": -80.0000,
         "location": "West Virginia/Kentucky/Virginia", "country": "USA",
         "cryptid_types": "Mothman, Bigfoot, Flatwoods Monster, Grafton Monster",
         "num_species": 6, "total_sightings_est": 4000,
         "description": "Mothman capital plus dense Bigfoot reports. Flatwoods Monster (1952). Rich folklore tradition.",
         "hotspot_rank": 5},
        {"name": "Borneo/Sumatra Rainforest", "lat": -1.0000, "lon": 110.0000,
         "location": "Borneo/Sumatra, Indonesia/Malaysia", "country": "Indonesia/Malaysia",
         "cryptid_types": "Orang Pendek, Batutut, Ahool",
         "num_species": 4, "total_sightings_est": 1500,
         "description": "Orang Pendek most credible cryptid. Region also yielded real discoveries (saola, giant muntjac).",
         "hotspot_rank": 6},
        {"name": "Loch Ness / Great Glen", "lat": 57.3229, "lon": -4.4244,
         "location": "Great Glen, Scotland", "country": "United Kingdom",
         "cryptid_types": "Nessie, Kelpie, Water Horse",
         "num_species": 2, "total_sightings_est": 1100,
         "description": "Single most famous cryptid location on Earth. Over 1,000 Nessie sightings. Sonar, eDNA studies ongoing.",
         "hotspot_rank": 7},
        {"name": "Pine Barrens, New Jersey", "lat": 39.8000, "lon": -74.5000,
         "location": "Pine Barrens, NJ", "country": "USA",
         "cryptid_types": "Jersey Devil, Bigfoot, Ghost Lights",
         "num_species": 3, "total_sightings_est": 2500,
         "description": "Jersey Devil since 1735. 1909 mass sighting wave. 1.1 million acres of dense wilderness near NYC.",
         "hotspot_rank": 8},
        {"name": "Uintah Basin / Skinwalker", "lat": 40.2500, "lon": -109.9000,
         "location": "Uintah Basin, Utah", "country": "USA",
         "cryptid_types": "Skinwalker, UFOs, Bigfoot, Cattle mutilation",
         "num_species": 4, "total_sightings_est": 1500,
         "description": "Highest diversity of paranormal reports. Government-studied (AAWSAP/AATIP). Navajo skinwalker legends.",
         "hotspot_rank": 9},
        {"name": "Australian Outback / Blue Mountains", "lat": -33.0000, "lon": 148.0000,
         "location": "NSW/Victoria, Australia", "country": "Australia",
         "cryptid_types": "Yowie, Bunyip, Phantom Cats, Thylacine",
         "num_species": 5, "total_sightings_est": 3000,
         "description": "Yowie and bunyip from Aboriginal tradition. Phantom cats. Thylacine possibly surviving in Tasmania.",
         "hotspot_rank": 10},
        {"name": "Puerto Rico / Caribbean", "lat": 18.2208, "lon": -66.5901,
         "location": "Puerto Rico / Caribbean islands", "country": "Puerto Rico",
         "cryptid_types": "Chupacabra, UFOs, Sea Monsters",
         "num_species": 3, "total_sightings_est": 2000,
         "description": "Chupacabra epicenter. 1995 wave spread worldwide. Also frequent UFO and sea monster reports.",
         "hotspot_rank": 11},
        {"name": "Patagonia / Southern Andes", "lat": -43.0000, "lon": -71.0000,
         "location": "Argentina/Chile", "country": "Argentina/Chile",
         "cryptid_types": "Nahuelito, Patagonian Plesiosaur, Giant Ground Sloth",
         "num_species": 3, "total_sightings_est": 1000,
         "description": "Nahuelito lake monster, possible surviving mylodon (giant ground sloth). Fresh mylodon hide found in cave 1895.",
         "hotspot_rank": 12},
    ])


# ═══════════════════════════════════════════════════════
# MAP MODES REGISTRY
# ═══════════════════════════════════════════════════════
MAP_MODES = [
    "Lake Monsters",
    "Bigfoot & Yeti",
    "Sea Serpents & Kraken",
    "Chupacabra & Blood Drinkers",
    "Mothman & Winged Creatures",
    "Dragon Legends",
    "Werewolf Legends",
    "Mystery Cats & Big Cats",
    "Undiscovered Species",
    "Cryptid Hotspots",
]

DATA_LOADERS = {
    "Lake Monsters": _lake_monsters_data,
    "Bigfoot & Yeti": _bigfoot_yeti_data,
    "Sea Serpents & Kraken": _sea_serpents_data,
    "Chupacabra & Blood Drinkers": _chupacabra_data,
    "Mothman & Winged Creatures": _mothman_winged_data,
    "Dragon Legends": _dragon_legends_data,
    "Werewolf Legends": _werewolf_data,
    "Mystery Cats & Big Cats": _mystery_cats_data,
    "Undiscovered Species": _undiscovered_species_data,
    "Cryptid Hotspots": _cryptid_hotspots_data,
}


# ═══════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _load_mode_data(mode: str) -> pd.DataFrame:
    """Load curated data for a given map mode, with caching."""
    loader = DATA_LOADERS.get(mode)
    if loader is None:
        return pd.DataFrame()
    return loader()


def _get_popup_html(row: dict, mode: str) -> str:
    """Build safe HTML popup for folium markers using html.escape on all user data."""
    name = escape(str(row.get("name", "Unknown")))
    location = escape(str(row.get("location", "Unknown")))
    desc = escape(str(row.get("description", "")))
    evidence = escape(str(row.get("evidence_level", "N/A")))

    # Mode-specific fields
    extra = ""
    if mode == "Lake Monsters":
        first_rep = escape(str(row.get("first_reported", "Unknown")))
        status = escape(str(row.get("status", "Unknown")))
        extra = f"<br><b>First Reported:</b> {first_rep}<br><b>Status:</b> {status}"
    elif mode == "Bigfoot & Yeti":
        ctype = escape(str(row.get("creature_type", "Unknown")))
        status = escape(str(row.get("status", "Unknown")))
        extra = f"<br><b>Type:</b> {ctype}<br><b>Status:</b> {status}"
    elif mode == "Sea Serpents & Kraken":
        year = escape(str(row.get("year", "Unknown")))
        ctype = escape(str(row.get("creature_type", "Unknown")))
        extra = f"<br><b>Year:</b> {year}<br><b>Type:</b> {ctype}"
    elif mode == "Chupacabra & Blood Drinkers":
        year = escape(str(row.get("year", "Unknown")))
        ctype = escape(str(row.get("creature_type", "Unknown")))
        extra = f"<br><b>Year:</b> {year}<br><b>Type:</b> {ctype}"
    elif mode == "Mothman & Winged Creatures":
        year = escape(str(row.get("year", "Unknown")))
        ctype = escape(str(row.get("creature_type", "Unknown")))
        extra = f"<br><b>Year:</b> {year}<br><b>Type:</b> {ctype}"
    elif mode == "Dragon Legends":
        era = escape(str(row.get("era", "Unknown")))
        dtype = escape(str(row.get("dragon_type", "Unknown")))
        extra = f"<br><b>Era:</b> {era}<br><b>Dragon Type:</b> {dtype}"
    elif mode == "Werewolf Legends":
        year = escape(str(row.get("year", "Unknown")))
        ctype = escape(str(row.get("creature_type", "Unknown")))
        extra = f"<br><b>Year:</b> {year}<br><b>Type:</b> {ctype}"
    elif mode == "Mystery Cats & Big Cats":
        year = escape(str(row.get("year", row.get("first_reported", "Unknown"))))
        ctype = escape(str(row.get("cat_type", "Unknown")))
        extra = f"<br><b>Year:</b> {year}<br><b>Cat Type:</b> {ctype}"
    elif mode == "Undiscovered Species":
        yd = escape(str(row.get("year_discovered", "Unknown")))
        orig = escape(str(row.get("original_status", "Unknown")))
        sig = escape(str(row.get("significance", "")))
        extra = f"<br><b>Discovered:</b> {yd}<br><b>Was:</b> {orig}<br><b>Significance:</b> {sig}"
    elif mode == "Cryptid Hotspots":
        ctypes = escape(str(row.get("cryptid_types", "Unknown")))
        rank = escape(str(row.get("hotspot_rank", "N/A")))
        nsight = escape(str(row.get("total_sightings_est", "N/A")))
        extra = (f"<br><b>Cryptid Types:</b> {ctypes}"
                 f"<br><b>Rank:</b> #{rank}"
                 f"<br><b>Est. Sightings:</b> {nsight}")

    html = f"""
    <div style="font-family:Arial,sans-serif;min-width:240px;max-width:320px;">
        <h4 style="margin:0 0 6px 0;color:#e8ecf4;font-size:14px;">{name}</h4>
        <p style="margin:2px 0;color:#8b97b0;font-size:12px;">
            <b>Location:</b> {location}
        </p>
        <p style="margin:2px 0;color:#8b97b0;font-size:12px;">
            {desc}
            {extra}
        </p>
        <p style="margin:4px 0 0 0;color:#06b6d4;font-size:11px;">
            <b>Evidence:</b> {evidence}
        </p>
    </div>
    """
    return html


def _build_folium_map(df: pd.DataFrame, mode: str) -> folium.Map:
    """Build a folium map with markers for the given dataset and mode."""
    color = CATEGORY_COLORS.get(mode, "#06b6d4")
    icon_name = MARKER_ICONS.get(mode, "info-sign")

    # Calculate center
    center_lat = df["lat"].mean()
    center_lon = df["lon"].mean()

    # Determine zoom from data spread
    lat_range = df["lat"].max() - df["lat"].min()
    lon_range = df["lon"].max() - df["lon"].min()
    spread = max(lat_range, lon_range)
    if spread > 100:
        zoom = 2
    elif spread > 50:
        zoom = 3
    elif spread > 20:
        zoom = 4
    elif spread > 5:
        zoom = 6
    else:
        zoom = 8

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    for _, row in df.iterrows():
        popup_html = _get_popup_html(row.to_dict(), mode)

        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=escape(str(row.get("name", "Unknown"))),
            icon=folium.Icon(color=_folium_color(color), icon=icon_name, prefix="fa"),
        ).add_to(m)

    return m


def _folium_color(hex_color: str) -> str:
    """Map hex accent color to nearest folium built-in color."""
    color_map = {
        "#38bdf8": "blue",
        "#8b5cf6": "purple",
        "#06b6d4": "cadetblue",
        "#ef4444": "red",
        "#f59e0b": "orange",
        "#dc2626": "darkred",
        "#a855f7": "darkpurple",
        "#10b981": "green",
        "#3b82f6": "blue",
        "#ec4899": "pink",
    }
    return color_map.get(hex_color, "cadetblue")


def _build_distribution_chart(df: pd.DataFrame, mode: str, group_col: str, title: str):
    """Build a matplotlib bar chart with dark theme for distribution analysis."""
    if group_col not in df.columns:
        return None

    counts = df[group_col].value_counts().head(12)

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    color = CATEGORY_COLORS.get(mode, "#06b6d4")
    bars = ax.barh(range(len(counts)), counts.values, color=color, alpha=0.85, edgecolor="#2a3550")

    ax.set_yticks(range(len(counts)))
    ax.set_yticklabels([str(l)[:30] for l in counts.index], fontsize=9, color="#e8ecf4")
    ax.set_xlabel("Count", color="#8b97b0", fontsize=10)
    ax.set_title(title, color="#e8ecf4", fontsize=12, fontweight="bold", pad=10)

    ax.tick_params(axis="x", colors="#8b97b0")
    ax.tick_params(axis="y", colors="#e8ecf4")
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", color="#2a3550", alpha=0.3)

    # Value labels
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", color="#e8ecf4", fontsize=9)

    plt.tight_layout()
    return fig


def _get_mode_stats(df: pd.DataFrame, mode: str) -> dict:
    """Calculate summary statistics for each mode."""
    stats = {
        "total_entries": len(df),
    }

    if mode == "Lake Monsters":
        stats["countries"] = df["country"].nunique()
        stats["active_legends"] = len(df[df["status"] == "Active legend"])
        stats["with_evidence"] = len(df[df["evidence_level"].str.contains("Photo|Video|Sonar", case=False, na=False)])

    elif mode == "Bigfoot & Yeti":
        stats["creature_types"] = df["creature_type"].nunique()
        stats["countries"] = df["country"].nunique()
        stats["investigated"] = len(df[df["evidence_level"].str.contains("sample|cast|footage|Film|expedition", case=False, na=False)])

    elif mode == "Sea Serpents & Kraken":
        stats["creature_types"] = df["creature_type"].nunique()
        stats["confirmed_real"] = len(df[df["creature_type"].str.contains("confirmed", case=False, na=False)])
        stats["physical_evidence"] = len(df[df["evidence_level"].str.contains("specimen|carcass|Physical", case=False, na=False)])

    elif mode == "Chupacabra & Blood Drinkers":
        stats["countries"] = df["country"].nunique()
        stats["dna_tested"] = len(df[df["evidence_level"].str.contains("DNA", case=False, na=False)])
        stats["livestock_events"] = len(df[df["evidence_level"].str.contains("Livestock", case=False, na=False)])

    elif mode == "Mothman & Winged Creatures":
        stats["creature_types"] = df["creature_type"].nunique()
        stats["countries"] = df["country"].nunique()
        stats["mass_sightings"] = len(df[df["evidence_level"].str.contains("Multiple|Mass|mass", case=False, na=False)])

    elif mode == "Dragon Legends":
        stats["dragon_types"] = df["dragon_type"].nunique()
        stats["countries"] = df["country"].nunique()
        stats["physical_sites"] = len(df[df["evidence_level"].str.contains("site|cave|Rock art|phenomenon", case=False, na=False)])

    elif mode == "Werewolf Legends":
        stats["creature_types"] = df["creature_type"].nunique()
        stats["countries"] = df["country"].nunique()
        stats["court_records"] = len(df[df["evidence_level"].str.contains("Court|record|Inquisition|transcript", case=False, na=False)])

    elif mode == "Mystery Cats & Big Cats":
        stats["countries"] = df["country"].nunique()
        stats["cat_types"] = df["cat_type"].nunique()
        stats["physical_evidence"] = len(df[df["evidence_level"].str.contains("capture|DNA|specimen|camera|kill", case=False, na=False)])

    elif mode == "Undiscovered Species":
        stats["species_confirmed"] = len(df)
        stats["countries"] = df["country"].nunique()
        stats["lazarus_taxa"] = len(df[df["original_status"].str.contains("extinct|fossil", case=False, na=False)])

    elif mode == "Cryptid Hotspots":
        stats["regions"] = len(df)
        stats["total_est_sightings"] = int(df["total_sightings_est"].sum())
        stats["avg_species_per_zone"] = round(df["num_species"].mean(), 1)

    return stats


def _render_stats_row(stats: dict, mode: str):
    """Render statistics as a row of st.metric cards."""
    if mode == "Lake Monsters":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Lake Monsters", stats["total_entries"])
        c2.metric("Countries", stats["countries"])
        c3.metric("Active Legends", stats["active_legends"])
        c4.metric("With Photo/Video/Sonar", stats["with_evidence"])

    elif mode == "Bigfoot & Yeti":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sighting Areas", stats["total_entries"])
        c2.metric("Creature Types", stats["creature_types"])
        c3.metric("Countries", stats["countries"])
        c4.metric("Scientifically Investigated", stats["investigated"])

    elif mode == "Sea Serpents & Kraken":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Encounters", stats["total_entries"])
        c2.metric("Creature Types", stats["creature_types"])
        c3.metric("Confirmed Real", stats["confirmed_real"])
        c4.metric("Physical Evidence", stats["physical_evidence"])

    elif mode == "Chupacabra & Blood Drinkers":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sighting Locations", stats["total_entries"])
        c2.metric("Countries", stats["countries"])
        c3.metric("DNA Tested", stats["dna_tested"])
        c4.metric("Livestock Events", stats["livestock_events"])

    elif mode == "Mothman & Winged Creatures":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sighting Locations", stats["total_entries"])
        c2.metric("Creature Types", stats["creature_types"])
        c3.metric("Countries", stats["countries"])
        c4.metric("Mass Sighting Events", stats["mass_sightings"])

    elif mode == "Dragon Legends":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dragon Sites", stats["total_entries"])
        c2.metric("Dragon Types", stats["dragon_types"])
        c3.metric("Countries", stats["countries"])
        c4.metric("Physical Sites", stats["physical_sites"])

    elif mode == "Werewolf Legends":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations", stats["total_entries"])
        c2.metric("Creature Types", stats["creature_types"])
        c3.metric("Countries", stats["countries"])
        c4.metric("Court Records", stats["court_records"])

    elif mode == "Mystery Cats & Big Cats":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Sighting Areas", stats["total_entries"])
        c2.metric("Countries", stats["countries"])
        c3.metric("Cat Types", stats["cat_types"])
        c4.metric("Physical Evidence", stats["physical_evidence"])

    elif mode == "Undiscovered Species":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Species Confirmed", stats["species_confirmed"])
        c2.metric("Countries", stats["countries"])
        c3.metric("Lazarus Taxa", stats["lazarus_taxa"])
        c4.metric("Discovery Locations", stats["total_entries"])

    elif mode == "Cryptid Hotspots":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Hotspot Regions", stats["regions"])
        c2.metric("Est. Total Sightings", f"{stats['total_est_sightings']:,}")
        c3.metric("Avg Cryptid Species/Zone", stats["avg_species_per_zone"])
        c4.metric("Mapped Zones", stats["total_entries"])


def _get_group_column(mode: str) -> tuple:
    """Return the best column to group by and chart title for each mode."""
    group_map = {
        "Lake Monsters": ("country", "Lake Monsters by Country"),
        "Bigfoot & Yeti": ("creature_type", "Sightings by Creature Type"),
        "Sea Serpents & Kraken": ("creature_type", "Encounters by Creature Type"),
        "Chupacabra & Blood Drinkers": ("country", "Sightings by Country"),
        "Mothman & Winged Creatures": ("creature_type", "Sightings by Creature Type"),
        "Dragon Legends": ("dragon_type", "Dragons by Type"),
        "Werewolf Legends": ("country", "Werewolf Reports by Country"),
        "Mystery Cats & Big Cats": ("country", "Mystery Cat Sightings by Country"),
        "Undiscovered Species": ("country", "Discovery Locations by Country"),
        "Cryptid Hotspots": ("name", "Hotspot Regions by Estimated Sightings"),
    }
    return group_map.get(mode, ("country", "Distribution by Country"))


def _get_csv_data(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to CSV bytes for download."""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


# ═══════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════

def render_cryptid_maps_tab():
    """Main render function for the Cryptid & Monster Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header red">
        <h4>&#x1F43E; Cryptid &amp; Monster Explorer</h4>
        <p>Explore legendary creatures, mysterious monsters, and cryptid sightings from around the world &mdash;
        curated geospatial data covering lake monsters, bigfoot, sea serpents, dragons, and more.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode Selection
    # ══════════════════════════════════════════
    st.markdown("#### Select Map Mode")

    mode = st.selectbox(
        "Choose a cryptid category to explore",
        MAP_MODES,
        key="cryptid_mode_select",
        help="Each mode contains a curated dataset of cryptid sightings and legends.",
    )

    # Mode description
    desc = MODE_DESCRIPTIONS.get(mode, "")
    if desc:
        st.info(desc)

    # ══════════════════════════════════════════
    # SECTION 2: Load Data
    # ══════════════════════════════════════════
    with st.spinner(f"Loading {mode} data..."):
        df = _load_mode_data(mode)

    if df.empty:
        st.warning("No data available for this mode.")
        return

    # ══════════════════════════════════════════
    # SECTION 3: Filtering
    # ══════════════════════════════════════════
    with st.expander("Filter Data", expanded=False):
        # Country filter if applicable
        if "country" in df.columns:
            countries = ["All"] + sorted(df["country"].unique().tolist())
            sel_country = st.selectbox("Filter by Country/Region", countries, key="cryptid_country_filter")
            if sel_country != "All":
                df = df[df["country"] == sel_country]

        # Creature type filter if applicable
        type_cols = ["creature_type", "cat_type", "dragon_type"]
        for tc in type_cols:
            if tc in df.columns:
                types = ["All"] + sorted(df[tc].unique().tolist())
                sel_type = st.selectbox(f"Filter by {tc.replace('_', ' ').title()}", types, key=f"cryptid_{tc}_filter")
                if sel_type != "All":
                    df = df[df[tc] == sel_type]

        # Text search
        search_text = st.text_input("Search by name or description", key="cryptid_text_search",
                                    placeholder="e.g. Nessie, Yeti, Kraken...")
        if search_text:
            mask = (
                df["name"].str.contains(search_text, case=False, na=False) |
                df["description"].str.contains(search_text, case=False, na=False)
            )
            df = df[mask]

    if df.empty:
        st.warning("No entries match your filter criteria. Try adjusting the filters.")
        return

    # ══════════════════════════════════════════
    # SECTION 4: Statistics
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {mode} -- Overview")

    stats = _get_mode_stats(df, mode)
    _render_stats_row(stats, mode)

    # ══════════════════════════════════════════
    # SECTION 5: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {mode} -- Map")

    m = _build_folium_map(df, mode)
    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 6: Distribution Chart
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {mode} -- Distribution")

    group_col, chart_title = _get_group_column(mode)
    fig = _build_distribution_chart(df, mode, group_col, chart_title)
    if fig is not None:
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    else:
        st.info("No distribution chart available for current filter.")

    # ══════════════════════════════════════════
    # SECTION 7: Data Table
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {mode} -- Data Table")

    # Select display columns (exclude lat/lon for cleaner view)
    display_cols = [c for c in df.columns if c not in ("lat", "lon")]
    st.dataframe(df[display_cols], use_container_width=True)

    # Coordinate table (expandable)
    with st.expander("Show Coordinates", expanded=False):
        coord_cols = ["name", "lat", "lon"]
        if "location" in df.columns:
            coord_cols.insert(1, "location")
        st.dataframe(df[coord_cols], use_container_width=True)

    # ══════════════════════════════════════════
    # SECTION 8: CSV Download
    # ══════════════════════════════════════════
    st.markdown("---")

    csv_bytes = _get_csv_data(df)
    file_label = mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        label=f"Download {mode} Data (CSV)",
        data=csv_bytes,
        file_name=f"terrascout_cryptid_{file_label}.csv",
        mime="text/csv",
        key=f"cryptid_download_{file_label}",
    )

    # ══════════════════════════════════════════
    # SECTION 9: About / Methodology
    # ══════════════════════════════════════════
    with st.expander("About This Data", expanded=False):
        st.markdown("""
        **Data Sources & Methodology**

        This module uses curated coordinate datasets compiled from multiple sources:

        - **Historical Records**: Newspaper archives, naval logs, court documents, and expedition reports
        - **Folklore Databases**: Documented oral traditions from indigenous and local communities worldwide
        - **Cryptozoological Archives**: Peer-reviewed and documented investigations from organizations like BFRO, CFZ, and ISC
        - **Scientific Publications**: Descriptions of formerly cryptid species now recognized by science
        - **Cultural Heritage Sites**: UNESCO and national heritage databases for locations tied to creature legends

        **Coordinates** represent the primary location associated with each sighting, legend origin, or discovery site.
        For area-based phenomena (e.g., Bigfoot territory), the coordinate marks the most notable sighting cluster center.

        **Disclaimer**: This module presents cryptozoological data for educational and entertainment purposes.
        Inclusion of a location does not constitute endorsement of any cryptid's existence.
        Several entries (coelacanth, okapi, giant squid, etc.) represent creatures confirmed by mainstream science.
        """)

    # ══════════════════════════════════════════
    # SECTION 10: Fun Facts Sidebar
    # ══════════════════════════════════════════
    with st.expander("Cryptid Quick Facts", expanded=False):
        facts = {
            "Lake Monsters": [
                "Loch Ness has been searched by sonar, submarine, and eDNA -- no conclusive evidence found.",
                "Sweden legally protected the Storsjon Monster from 1986 to 2005.",
                "Lake Champlain's 'Champ' has its own legal protection in both Vermont and New York.",
            ],
            "Bigfoot & Yeti": [
                "The BFRO database contains over 10,000 Sasquatch sighting reports.",
                "The Patterson-Gimlin film (1967) has never been definitively debunked.",
                "Orang Pendek hair samples tested as 'unknown primate' by multiple labs.",
            ],
            "Sea Serpents & Kraken": [
                "The giant squid was not photographed alive until 2004 -- after millennia of Kraken legends.",
                "The colossal squid has rotating hooks on its tentacles and is larger than the giant squid.",
                "HMS Daedalus sea serpent report in 1848 was taken seriously by the British Admiralty.",
            ],
            "Chupacabra & Blood Drinkers": [
                "Most captured 'chupacabras' have been identified as coyotes or dogs with severe mange.",
                "The original 1995 description matches no known animal -- bipedal with spines and large eyes.",
                "Benjamin Radford traced the original description to the alien in the film 'Species' (1995).",
            ],
            "Mothman & Winged Creatures": [
                "The Silver Bridge collapsed 13 months after Mothman sightings began -- killing 46 people.",
                "Chicago's 2017-2020 winged humanoid flap produced over 55 documented sighting reports.",
                "The Jersey Devil has been New Jersey's official state demon since 1939.",
            ],
            "Dragon Legends": [
                "Dragon legends appear independently in cultures with no contact -- Europe, China, Americas, Africa.",
                "Dinosaur fossils may explain some dragon myths -- ancient Greeks found protoceratops skulls.",
                "Naga Fireballs rise from the Mekong River every year during the full moon of the 11th lunar month.",
            ],
            "Werewolf Legends": [
                "Between 1520-1630, there were over 30,000 werewolf trials in France alone.",
                "Old Thiess of Livonia (1692) claimed werewolves were servants of God fighting witches.",
                "Clinical lycanthropy is a real psychiatric condition where patients believe they are transforming.",
            ],
            "Mystery Cats & Big Cats": [
                "A real puma was captured in Surrey, England in 1966 -- validating some big cat reports.",
                "The 1976 Dangerous Wild Animals Act may have led to exotic cat releases in the UK.",
                "The Kellas cat (melanistic hybrid) was confirmed as a real new feline form in Scotland.",
            ],
            "Undiscovered Species": [
                "An estimated 80% of Earth's species remain undiscovered.",
                "The saola, discovered in 1992, is one of the rarest mammals -- possibly fewer than 100 remain.",
                "The megamouth shark was completely unknown to science until 1976.",
            ],
            "Cryptid Hotspots": [
                "The Pacific Northwest averages over 500 new Bigfoot reports per year.",
                "Skinwalker Ranch has been studied by the US government under the AAWSAP program.",
                "Loch Ness receives over 500,000 visitors per year -- largely due to the monster legend.",
            ],
        }

        mode_facts = facts.get(mode, [])
        for i, fact in enumerate(mode_facts, 1):
            st.markdown(f"**{i}.** {fact}")
