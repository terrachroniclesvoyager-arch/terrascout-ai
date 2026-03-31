# -*- coding: utf-8 -*-
"""
Shipwrecks & Maritime Disasters module for TerraScout AI.
Curated databases of famous shipwrecks, treasure ships, war wrecks,
ancient vessels, ghost ships, submarine disasters, and more.
Uses Overpass API for OSM wreck data and rich curated datasets.
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

from src.overpass_client import query_overpass

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
    "Famous Shipwrecks",
    "Treasure Ships",
    "World War Wrecks",
    "Ancient Shipwrecks",
    "Ghost Ships",
    "Submarine Disasters",
    "Bermuda Triangle",
    "Maritime Disaster Zones",
    "Underwater Archaeology Sites",
    "Modern Maritime Disasters",
]

MODE_DESCRIPTIONS = {
    "Famous Shipwrecks": (
        "The most iconic shipwrecks in maritime history -- from the Titanic to the Mary Rose. "
        "Each vessel tells a story of ambition, tragedy, and the unforgiving sea."
    ),
    "Treasure Ships": (
        "Legendary treasure-laden vessels lost at sea, many still holding billions "
        "in gold, silver, and precious cargo on the ocean floor."
    ),
    "World War Wrecks": (
        "Naval combat wrecks from WWI and WWII -- battleships, carriers, submarines, "
        "and convoy vessels that became underwater war graves."
    ),
    "Ancient Shipwrecks": (
        "Archaeological marvels from antiquity -- Phoenician traders, Roman galleys, "
        "Greek merchant ships, and Bronze Age vessels discovered on the seabed."
    ),
    "Ghost Ships": (
        "Mysterious vessels found adrift or that vanished under inexplicable circumstances. "
        "Tales of crews that disappeared without a trace."
    ),
    "Submarine Disasters": (
        "Tragic losses of military and research submarines -- from Cold War incidents "
        "to modern accidents in the deep ocean."
    ),
    "Bermuda Triangle": (
        "Ships and aircraft that vanished in the infamous area between Miami, Bermuda, "
        "and Puerto Rico. Documented disappearances and prevailing theories."
    ),
    "Maritime Disaster Zones": (
        "The world's most dangerous waters -- graveyard coastlines, treacherous straits, "
        "and notorious ship-killing zones that have claimed hundreds of vessels."
    ),
    "Underwater Archaeology Sites": (
        "Protected wreck sites, underwater museums, marine parks, and premier "
        "diving destinations where history meets the ocean."
    ),
    "Modern Maritime Disasters": (
        "21st-century maritime tragedies -- cruise ship capsizings, cargo vessel losses, "
        "ferry disasters, and groundings that made global headlines."
    ),
}

MODE_COLORS = {
    "Famous Shipwrecks": "#06b6d4",
    "Treasure Ships": "#f59e0b",
    "World War Wrecks": "#ef4444",
    "Ancient Shipwrecks": "#a855f7",
    "Ghost Ships": "#8b97b0",
    "Submarine Disasters": "#3b82f6",
    "Bermuda Triangle": "#10b981",
    "Maritime Disaster Zones": "#f97316",
    "Underwater Archaeology Sites": "#ec4899",
    "Modern Maritime Disasters": "#dc2626",
}

# ═══════════════════════════════════════════════════════════════════════════════
# CURATED WRECK DATABASES
# ═══════════════════════════════════════════════════════════════════════════════

FAMOUS_SHIPWRECKS = [
    {"name": "RMS Titanic", "lat": 41.7260, "lon": -49.9469, "year": 1912,
     "type": "Ocean Liner", "flag": "UK", "depth_m": 3800,
     "cause": "Iceberg collision on maiden voyage",
     "details": "Most famous shipwreck in history. 1,517 lives lost. Discovered by Robert Ballard in 1985 at 3,800m depth."},
    {"name": "Bismarck", "lat": 48.1667, "lon": -16.2000, "year": 1941,
     "type": "Battleship", "flag": "Germany", "depth_m": 4791,
     "cause": "Scuttled after battle damage from Royal Navy",
     "details": "Germany's largest battleship. Sank HMS Hood before being hunted down. Found by Ballard in 1989."},
    {"name": "Mary Rose", "lat": 50.7636, "lon": -1.1050, "year": 1545,
     "type": "Warship (Carrack)", "flag": "England", "depth_m": 12,
     "cause": "Capsized in battle with French fleet",
     "details": "Henry VIII's flagship. Raised in 1982, now displayed in Portsmouth Historic Dockyard."},
    {"name": "Vasa", "lat": 59.3280, "lon": 18.0914, "year": 1628,
     "type": "Warship (Galleon)", "flag": "Sweden", "depth_m": 32,
     "cause": "Capsized on maiden voyage due to instability",
     "details": "Swedish warship that sank in Stockholm harbor. Salvaged in 1961, now in the Vasa Museum."},
    {"name": "SS Andrea Doria", "lat": 40.2967, "lon": -69.8517, "year": 1956,
     "type": "Ocean Liner", "flag": "Italy", "depth_m": 73,
     "cause": "Collision with MS Stockholm in fog",
     "details": "Italian luxury liner. 46 killed. Popular but dangerous dive site off Nantucket."},
    {"name": "RMS Lusitania", "lat": 51.2500, "lon": -8.5500, "year": 1915,
     "type": "Ocean Liner", "flag": "UK", "depth_m": 93,
     "cause": "Torpedoed by German U-boat U-20",
     "details": "1,198 lives lost including 128 Americans. Helped draw the US into WWI."},
    {"name": "HMHS Britannic", "lat": 37.4200, "lon": 24.2867, "year": 1916,
     "type": "Hospital Ship", "flag": "UK", "depth_m": 120,
     "cause": "Mine strike in the Kea Channel, Aegean Sea",
     "details": "Titanic's sister ship, serving as hospital ship in WWI. Largest ship lost in WWI. 30 killed."},
    {"name": "SS Edmund Fitzgerald", "lat": 46.9986, "lon": -85.1114, "year": 1975,
     "type": "Bulk Carrier", "flag": "USA", "depth_m": 162,
     "cause": "Storm on Lake Superior, structural failure",
     "details": "Largest ship to sink on the Great Lakes. All 29 crew lost. Immortalized in Gordon Lightfoot's song."},
    {"name": "RMS Empress of Ireland", "lat": 48.6283, "lon": -68.3850, "year": 1914,
     "type": "Ocean Liner", "flag": "UK/Canada", "depth_m": 40,
     "cause": "Collision with SS Storstad in fog, St. Lawrence River",
     "details": "1,012 lives lost in 14 minutes. Canada's worst maritime disaster."},
    {"name": "SS Thistlegorm", "lat": 27.8125, "lon": 33.9222, "year": 1941,
     "type": "Armed Freighter", "flag": "UK", "depth_m": 30,
     "cause": "Bombed by German aircraft in the Red Sea",
     "details": "One of the world's best dive wrecks. Cargo of vehicles, motorcycles, and munitions intact."},
    {"name": "MS Estonia", "lat": 59.3833, "lon": 21.6833, "year": 1994,
     "type": "Cruise Ferry", "flag": "Estonia", "depth_m": 74,
     "cause": "Bow visor failure in Baltic storm",
     "details": "852 lives lost. Worst peacetime maritime disaster in European waters since Titanic."},
    {"name": "MV Wilhelm Gustloff", "lat": 55.0700, "lon": 17.4167, "year": 1945,
     "type": "Passenger/Military", "flag": "Germany", "depth_m": 44,
     "cause": "Torpedoed by Soviet submarine S-13",
     "details": "~9,400 killed. Deadliest single-ship maritime disaster in history."},
    {"name": "RMS Carpathia", "lat": 49.5417, "lon": -10.5583, "year": 1918,
     "type": "Ocean Liner", "flag": "UK", "depth_m": 155,
     "cause": "Torpedoed by German U-boat U-55",
     "details": "Famous for rescuing Titanic survivors in 1912. Sunk by U-boat off Ireland in WWI."},
    {"name": "SS Waratah", "lat": -32.0000, "lon": 30.0000, "year": 1909,
     "type": "Passenger/Cargo", "flag": "UK", "depth_m": None,
     "cause": "Disappeared en route from Durban to Cape Town",
     "details": "211 passengers and crew lost. Wreck never found. Known as 'Titanic of the South'."},
    {"name": "HMS Victory (1744)", "lat": 49.4833, "lon": -4.7500, "year": 1744,
     "type": "Warship", "flag": "UK", "depth_m": 60,
     "cause": "Storm in the English Channel",
     "details": "Not Nelson's Victory but an earlier ship. Over 1,100 lives lost. Wreck found in 2008 with gold cargo."},
    {"name": "General Slocum", "lat": 40.7900, "lon": -73.9300, "year": 1904,
     "type": "Steamboat", "flag": "USA", "depth_m": 8,
     "cause": "Fire on the East River, New York",
     "details": "1,021 killed. Worst disaster in New York City until 9/11. Mostly German-American women and children."},
    {"name": "MV Dona Paz", "lat": 12.0500, "lon": 121.8833, "year": 1987,
     "type": "Passenger Ferry", "flag": "Philippines", "depth_m": 545,
     "cause": "Collision with oil tanker MT Vector",
     "details": "~4,386 killed. Worst peacetime maritime disaster. Ferry was severely overloaded."},
    {"name": "SS Eastland", "lat": 41.8867, "lon": -87.6317, "year": 1915,
     "type": "Passenger Steamer", "flag": "USA", "depth_m": 6,
     "cause": "Capsized at dock in Chicago River",
     "details": "844 passengers and crew killed while still tied to the dock. Worst Great Lakes disaster."},
]

TREASURE_SHIPS = [
    {"name": "Nuestra Senora de Atocha", "lat": 24.5142, "lon": -82.1850, "year": 1622,
     "type": "Spanish Galleon", "flag": "Spain", "depth_m": 16,
     "cargo": "$450 million in gold, silver, emeralds",
     "details": "Found by Mel Fisher in 1985 after 16-year search. Carried 40 tons of gold and silver."},
    {"name": "San Jose (Colombia)", "lat": 10.3000, "lon": -76.0333, "year": 1708,
     "type": "Spanish Galleon", "flag": "Spain", "depth_m": 600,
     "cargo": "$17 billion (estimated) in gold, silver, emeralds",
     "details": "The 'Holy Grail of Shipwrecks'. Sunk by British in War of Spanish Succession. Found 2015."},
    {"name": "Flor de la Mar", "lat": 2.4167, "lon": 104.2500, "year": 1511,
     "type": "Portuguese Carrack", "flag": "Portugal", "depth_m": None,
     "cargo": "$2.6 billion (estimated) in Malaccan treasure",
     "details": "Largest treasure ever lost at sea. Carried loot from the conquest of Malacca. Never found."},
    {"name": "SS Central America", "lat": 31.7500, "lon": -77.0833, "year": 1857,
     "type": "Sidewheel Steamer", "flag": "USA", "depth_m": 2200,
     "cargo": "$150 million in California Gold Rush gold",
     "details": "Sank in hurricane. 425 died. Recovery of 'Ship of Gold' started 1988 by Tommy Thompson."},
    {"name": "Nuestra Senora de las Mercedes", "lat": 36.2833, "lon": -6.8167, "year": 1804,
     "type": "Spanish Frigate", "flag": "Spain", "depth_m": 1100,
     "cargo": "$500 million in gold and silver coins",
     "details": "Sunk by British off Cape Santa Maria. Treasure recovered by Odyssey Marine, returned to Spain by court."},
    {"name": "SS Republic", "lat": 31.4167, "lon": -79.5833, "year": 1865,
     "type": "Steamship", "flag": "USA", "depth_m": 518,
     "cargo": "$180 million in gold and silver coins",
     "details": "Sank in hurricane off Georgia. Found 2003 by Odyssey Marine Exploration."},
    {"name": "Whydah Gally", "lat": 41.8808, "lon": -69.9483, "year": 1717,
     "type": "Slave Ship / Pirate Ship", "flag": "Pirate", "depth_m": 6,
     "cargo": "Pirate treasure, ivory, indigo, gold",
     "details": "Captain Black Sam Bellamy's flagship. First authenticated pirate wreck. Found by Barry Clifford 1984."},
    {"name": "SS Gairsoppa", "lat": 50.4167, "lon": -11.7500, "year": 1941,
     "type": "Cargo Ship", "flag": "UK", "depth_m": 4700,
     "cargo": "110 tons of silver ($210 million)",
     "details": "Torpedoed by U-101 off Ireland. Odyssey Marine recovered 48 tons of silver in 2012-2013."},
    {"name": "Concepcion (1641)", "lat": 20.3500, "lon": -69.0833, "year": 1641,
     "type": "Spanish Galleon", "flag": "Spain", "depth_m": 15,
     "cargo": "$14 million in treasure",
     "details": "Hit reef near Hispaniola. Treasure hunter William Phips recovered part of cargo in 1687."},
    {"name": "San Miguel (1551)", "lat": 27.5000, "lon": -80.2500, "year": 1551,
     "type": "Spanish Galleon", "flag": "Spain", "depth_m": 8,
     "cargo": "Gold, silver from New Spain",
     "details": "Part of the 1551 Tierra Firme Fleet lost in hurricane off Florida."},
    {"name": "Merchant Royal", "lat": 50.0000, "lon": -5.5000, "year": 1641,
     "type": "English Merchant Vessel", "flag": "England", "depth_m": None,
     "cargo": "$1.5 billion (estimated) in gold, silver, coins",
     "details": "Sank off Land's End, Cornwall. Carried enormous cargo from New World. Never found."},
    {"name": "Santa Margarita", "lat": 24.5300, "lon": -82.2100, "year": 1622,
     "type": "Spanish Galleon", "flag": "Spain", "depth_m": 16,
     "cargo": "$50 million in silver bars and coins",
     "details": "Sister ship to Atocha, part of same fleet. Found by Mel Fisher's team 1980."},
    {"name": "Le Chameau", "lat": 45.9400, "lon": -59.9200, "year": 1725,
     "type": "French Transport", "flag": "France", "depth_m": 27,
     "cargo": "Gold and silver coins, pay for French garrison",
     "details": "Sank in storm off Cape Breton, Nova Scotia. 316 lost. Partially salvaged in 1960s."},
    {"name": "SS Egypt", "lat": 48.1000, "lon": -5.6500, "year": 1922,
     "type": "P&O Liner", "flag": "UK", "depth_m": 122,
     "cargo": "$100 million in gold and silver",
     "details": "Rammed by Seine in fog off Ushant. Italian salvage team recovered most gold bars 1930-1935."},
    {"name": "Tek Sing", "lat": 2.0000, "lon": 106.5833, "year": 1822,
     "type": "Chinese Junk", "flag": "China", "depth_m": 30,
     "cargo": "350,000 pieces of fine Chinese porcelain",
     "details": "Titanic of the East. ~1,600 killed. Cargo of Qing dynasty porcelain recovered by Michael Hatcher."},
]

WORLD_WAR_WRECKS = [
    {"name": "USS Arizona (BB-39)", "lat": 21.3649, "lon": -157.9499, "year": 1941,
     "type": "Battleship", "flag": "USA", "depth_m": 12,
     "conflict": "WWII - Pearl Harbor",
     "details": "1,177 killed in Japanese attack on Pearl Harbor. Memorial built above the wreck. Still leaks oil."},
    {"name": "HMS Hood", "lat": 63.3333, "lon": -31.8500, "year": 1941,
     "type": "Battlecruiser", "flag": "UK", "depth_m": 2800,
     "conflict": "WWII - Battle of Denmark Strait",
     "details": "Pride of the Royal Navy, destroyed by Bismarck. 1,415 killed, only 3 survivors."},
    {"name": "IJN Yamato", "lat": 30.7200, "lon": 128.1167, "year": 1945,
     "type": "Battleship", "flag": "Japan", "depth_m": 340,
     "conflict": "WWII - Operation Ten-Go",
     "details": "Largest battleship ever built (72,000 tons). Sunk by massive US air attack. 3,055 killed."},
    {"name": "USS Indianapolis (CA-35)", "lat": 12.0300, "lon": 134.8000, "year": 1945,
     "type": "Heavy Cruiser", "flag": "USA", "depth_m": 5500,
     "conflict": "WWII - Pacific Theater",
     "details": "Torpedoed by I-58 after delivering A-bomb components. ~900 crew in water, ~300 killed by sharks."},
    {"name": "SMS Konig", "lat": 58.8833, "lon": -3.1500, "year": 1919,
     "type": "Battleship", "flag": "Germany", "depth_m": 40,
     "conflict": "WWI - Scapa Flow Scuttle",
     "details": "Scuttled with the German High Seas Fleet at Scapa Flow. Popular dive site in Orkney."},
    {"name": "HMS Royal Oak", "lat": 58.8833, "lon": -2.9833, "year": 1939,
     "type": "Battleship", "flag": "UK", "depth_m": 30,
     "conflict": "WWII - U-47 raid on Scapa Flow",
     "details": "Torpedoed at anchor by Gunther Prien's U-47. 835 killed. Protected war grave."},
    {"name": "USS Lexington (CV-2)", "lat": -15.3000, "lon": 155.5000, "year": 1942,
     "type": "Aircraft Carrier", "flag": "USA", "depth_m": 3000,
     "conflict": "WWII - Battle of Coral Sea",
     "details": "First carrier-vs-carrier battle. Found by Paul Allen's team in 2018 at 3,000m."},
    {"name": "IJN Akagi", "lat": 30.3000, "lon": -178.8500, "year": 1942,
     "type": "Aircraft Carrier", "flag": "Japan", "depth_m": 5400,
     "conflict": "WWII - Battle of Midway",
     "details": "Japanese flagship carrier at Midway. Sunk by SBD Dauntless dive bombers. Turning point of Pacific War."},
    {"name": "KMS Scharnhorst", "lat": 72.1600, "lon": 28.7100, "year": 1943,
     "type": "Battleship", "flag": "Germany", "depth_m": 290,
     "conflict": "WWII - Battle of North Cape",
     "details": "Sunk by HMS Duke of York off Norway. 1,932 killed, only 36 survivors."},
    {"name": "HMS Prince of Wales", "lat": 3.5500, "lon": 104.4833, "year": 1941,
     "type": "Battleship", "flag": "UK", "depth_m": 68,
     "conflict": "WWII - Sinking of Force Z",
     "details": "Sunk by Japanese aircraft with HMS Repulse off Malaya. Proved airpower could sink capital ships."},
    {"name": "HMS Repulse", "lat": 3.6167, "lon": 104.4167, "year": 1941,
     "type": "Battlecruiser", "flag": "UK", "depth_m": 56,
     "conflict": "WWII - Sinking of Force Z",
     "details": "Sunk alongside HMS Prince of Wales. 508 killed. Churchill called it 'the worst shock of the war'."},
    {"name": "USS Yorktown (CV-5)", "lat": 30.5000, "lon": -176.5667, "year": 1942,
     "type": "Aircraft Carrier", "flag": "USA", "depth_m": 5200,
     "conflict": "WWII - Battle of Midway",
     "details": "Damaged at Coral Sea, hastily repaired, then sunk at Midway by I-168. Found at 5,200m in 1998."},
    {"name": "U-869", "lat": 39.7167, "lon": -73.0167, "year": 1945,
     "type": "Submarine (Type IXC/40)", "flag": "Germany", "depth_m": 73,
     "conflict": "WWII - Atlantic U-boat",
     "details": "Lost off New Jersey, rediscovered by divers John Chatterton and Richie Kohler. Subject of 'Shadow Divers'."},
    {"name": "HMAS Sydney (II)", "lat": -26.1000, "lon": 111.0833, "year": 1941,
     "type": "Light Cruiser", "flag": "Australia", "depth_m": 2468,
     "conflict": "WWII - Indian Ocean",
     "details": "Sunk in mutual destruction with German raider Kormoran. 645 killed. Found 2008 after 66-year search."},
    {"name": "USS Oklahoma (BB-37)", "lat": 21.3644, "lon": -157.9519, "year": 1941,
     "type": "Battleship", "flag": "USA", "depth_m": 12,
     "conflict": "WWII - Pearl Harbor",
     "details": "Capsized at Pearl Harbor, 429 killed. Righted and refloated but sank under tow to scrapyard in 1947."},
    {"name": "AHS Centaur", "lat": -27.2833, "lon": 153.9833, "year": 1943,
     "type": "Hospital Ship", "flag": "Australia", "depth_m": 2059,
     "conflict": "WWII - Pacific Theater",
     "details": "Torpedoed by I-177 despite hospital markings. 268 killed. War crime. Found 2009."},
]

ANCIENT_SHIPWRECKS = [
    {"name": "Antikythera Wreck", "lat": 35.8767, "lon": 23.3100, "year": -60,
     "type": "Roman Cargo Ship", "flag": "Rome", "depth_m": 52,
     "period": "1st century BC",
     "details": "Found in 1900 off Antikythera, Greece. Contained the Antikythera Mechanism -- world's first analog computer."},
    {"name": "Uluburun Wreck", "lat": 36.1286, "lon": 29.6822, "year": -1300,
     "type": "Bronze Age Merchant", "flag": "Unknown", "depth_m": 52,
     "period": "Late Bronze Age (c. 1300 BC)",
     "details": "Oldest shipwreck ever excavated. Cargo from 7 cultures: copper, tin, glass, gold, ivory, ebony."},
    {"name": "Kyrenia Ship", "lat": 35.3422, "lon": 33.3183, "year": -300,
     "type": "Greek Merchant", "flag": "Greece", "depth_m": 30,
     "period": "4th century BC",
     "details": "Remarkably preserved Greek trading vessel. Carried almonds and wine amphorae. Hull on display in Kyrenia Castle."},
    {"name": "Madrague de Giens", "lat": 43.0356, "lon": 6.1389, "year": -70,
     "type": "Roman Wine Carrier", "flag": "Rome", "depth_m": 18,
     "period": "1st century BC",
     "details": "Massive Roman merchant ship carrying 6,000+ wine amphorae from Italy to Gaul. 40m long."},
    {"name": "Mahdia Wreck", "lat": 35.5000, "lon": 11.0667, "year": -80,
     "type": "Roman Art Transport", "flag": "Rome/Greece", "depth_m": 39,
     "period": "1st century BC",
     "details": "Carried Greek bronze and marble sculptures looted from Athens. Found off Tunisia in 1907."},
    {"name": "Skuldelev Ships", "lat": 55.7639, "lon": 12.0822, "year": 1070,
     "type": "Viking Ships (5 vessels)", "flag": "Denmark", "depth_m": 2,
     "period": "Viking Age (c. 1070 AD)",
     "details": "Five deliberately sunk Viking ships blocking Roskilde Fjord. Now in Viking Ship Museum."},
    {"name": "Ma'agan Mikhael Ship", "lat": 32.5539, "lon": 34.8667, "year": -400,
     "type": "Coastal Trader", "flag": "Phoenicia", "depth_m": 2,
     "period": "5th century BC",
     "details": "Ancient Phoenician merchantman found off Israel. Exceptionally well-preserved hull timbers."},
    {"name": "Marsala Punic Ship", "lat": 37.8000, "lon": 12.4333, "year": -241,
     "type": "Punic Warship", "flag": "Carthage", "depth_m": 3,
     "period": "3rd century BC (First Punic War)",
     "details": "Carthaginian warship from the Battle of the Aegates. Found off Marsala, Sicily in 1969."},
    {"name": "Dokos Wreck", "lat": 37.3167, "lon": 23.2833, "year": -2200,
     "type": "Early Bronze Age Vessel", "flag": "Unknown", "depth_m": 15,
     "period": "c. 2200 BC",
     "details": "One of the oldest known shipwrecks. Found near Hydra, Greece. Cargo of ceramic vessels."},
    {"name": "Nemi Ships", "lat": 41.7167, "lon": 12.7000, "year": 40,
     "type": "Roman Ceremonial Barges", "flag": "Rome", "depth_m": 0,
     "period": "1st century AD (Emperor Caligula)",
     "details": "Two enormous barges from Lake Nemi built for Caligula. Raised in 1930s, destroyed in WWII fire."},
    {"name": "Belem Wreck (Pepper Wreck)", "lat": 38.6892, "lon": -9.2100, "year": 1606,
     "type": "Portuguese Nau", "flag": "Portugal", "depth_m": 8,
     "period": "17th century",
     "details": "Nossa Senhora dos Martires. East Indiaman carrying pepper and spices. Found in Tagus River mouth."},
    {"name": "Cape Gelidonya Wreck", "lat": 36.2333, "lon": 30.4083, "year": -1200,
     "type": "Bronze Age Merchant", "flag": "Unknown", "depth_m": 27,
     "period": "Late Bronze Age (c. 1200 BC)",
     "details": "First ancient wreck excavated by divers (George Bass, 1960). Carried copper and tin ingots."},
    {"name": "Yassiada Byzantine Wreck", "lat": 36.9917, "lon": 27.1667, "year": 625,
     "type": "Byzantine Merchant", "flag": "Byzantine", "depth_m": 37,
     "period": "7th century AD",
     "details": "Excavated by George Bass. Carried 900 wine amphorae. Key site in underwater archaeology development."},
    {"name": "Sutton Hoo Ship", "lat": 52.0886, "lon": 1.3381, "year": 625,
     "type": "Anglo-Saxon Ship Burial", "flag": "Anglo-Saxon", "depth_m": 0,
     "period": "7th century AD",
     "details": "Royal burial ship found on land in Suffolk. Stunning treasure including helmet and gold. Not a wreck per se."},
]

GHOST_SHIPS = [
    {"name": "Mary Celeste", "lat": 38.7167, "lon": -17.3667, "year": 1872,
     "type": "Merchant Brigantine", "flag": "USA", "depth_m": None,
     "mystery": "Found sailing unmanned near the Azores",
     "details": "Crew of 10 vanished. Cargo intact, food on table. One of history's greatest maritime mysteries."},
    {"name": "Flying Dutchman (Legend)", "lat": -34.3568, "lon": 18.4740, "year": 1641,
     "type": "Phantom Ship", "flag": "Netherlands", "depth_m": None,
     "mystery": "Legendary ghost ship doomed to sail forever",
     "details": "Doomed to sail the seas forever. Sightings reported off Cape of Good Hope for centuries. Origin of many legends."},
    {"name": "Ourang Medan", "lat": 2.0000, "lon": 105.5000, "year": 1947,
     "type": "Cargo Ship", "flag": "Netherlands", "depth_m": None,
     "mystery": "Entire crew found dead with terrified expressions",
     "details": "SOS received: 'All officers dead... I die.' All crew dead with horrified faces. Ship exploded during rescue."},
    {"name": "Carroll A. Deering", "lat": 35.1522, "lon": -75.5283, "year": 1921,
     "type": "Five-masted Schooner", "flag": "USA", "depth_m": 5,
     "mystery": "Found grounded at Diamond Shoals, crew missing",
     "details": "All 11 crew vanished. Two lifeboats gone. Food prepared on stove. Navigation equipment missing."},
    {"name": "MV Joyita", "lat": -9.5000, "lon": -171.7500, "year": 1955,
     "type": "Merchant Vessel", "flag": "Tokelau", "depth_m": None,
     "mystery": "Found drifting, all 25 passengers and crew missing",
     "details": "Partially submerged but unsinkable (cork-lined). 25 people vanished without trace."},
    {"name": "Baychimo", "lat": 70.1000, "lon": -155.0000, "year": 1931,
     "type": "Cargo Steamer", "flag": "UK/Canada", "depth_m": None,
     "mystery": "Abandoned in Arctic ice, drifted unmanned for 38 years",
     "details": "Crew abandoned in ice off Alaska. Ship drifted crewless until last sighting in 1969. Never recovered."},
    {"name": "SS Zebrina", "lat": 50.7600, "lon": 0.9600, "year": 1917,
     "type": "Sailing Barge", "flag": "UK", "depth_m": 5,
     "mystery": "Found aground near Cherbourg with no crew",
     "details": "Coal cargo intact, no damage, lifeboats in place. All crew simply gone. Possible U-boat encounter."},
    {"name": "Caleuche (Legend)", "lat": -42.5000, "lon": -73.8000, "year": None,
     "type": "Ghost Ship (Mythology)", "flag": "Chile", "depth_m": None,
     "mystery": "Mythical ghost ship of Chiloe Island",
     "details": "Chilean/Chilote mythology. Appears as a beautiful white ship, then vanishes. Carries drowned sailors."},
    {"name": "Kaz II", "lat": -19.1833, "lon": 146.5000, "year": 2007,
     "type": "Catamaran", "flag": "Australia", "depth_m": None,
     "mystery": "Found drifting off Queensland, 3 men missing",
     "details": "Engine running, laptop on, food set out. Three experienced sailors vanished. No distress signal."},
    {"name": "High Aim 6", "lat": -17.0833, "lon": 122.2333, "year": 2003,
     "type": "Fishing Vessel", "flag": "Taiwan", "depth_m": None,
     "mystery": "Found drifting near Australia, crew missing",
     "details": "Indonesian fishing vessel found crewless off NW Australia. Captain and crew vanished. Possible mutiny."},
    {"name": "MV Lyubov Orlova", "lat": 52.0000, "lon": -30.0000, "year": 2013,
     "type": "Cruise Ship", "flag": "Russia", "depth_m": None,
     "mystery": "Derelict cruise ship drifting the Atlantic",
     "details": "Cut loose while being towed for scrap. Drifted the North Atlantic. Nicknamed 'cannibal rat ship'."},
    {"name": "SS Valencia", "lat": 48.6833, "lon": -124.7667, "year": 1906,
     "type": "Passenger Steamer", "flag": "USA", "depth_m": 10,
     "mystery": "Horrific wreck; lifeboat found 27 years later with skeletons",
     "details": "136 killed off Vancouver Island. Lifeboat found in 1933 with skeletal remains. Ghostly sightings since."},
]

SUBMARINE_DISASTERS = [
    {"name": "Kursk (K-141)", "lat": 69.6167, "lon": 37.5833, "year": 2000,
     "type": "Oscar-II Class SSGN", "flag": "Russia", "depth_m": 108,
     "cause": "Torpedo explosion / HTP fuel leak",
     "details": "118 killed. 23 survived initial blast, left notes. Failed rescue attempts. Raised in 2001."},
    {"name": "USS Thresher (SSN-593)", "lat": 41.7333, "lon": -64.9500, "year": 1963,
     "type": "Nuclear Attack Submarine", "flag": "USA", "depth_m": 2560,
     "cause": "Pipe joint failure during deep dive test",
     "details": "First nuclear submarine lost. 129 killed. Led to SUBSAFE quality program. Deepest US sub loss."},
    {"name": "USS Scorpion (SSN-589)", "lat": 32.9167, "lon": -33.1500, "year": 1968,
     "type": "Nuclear Attack Submarine", "flag": "USA", "depth_m": 3000,
     "cause": "Unknown -- torpedo malfunction or hull failure",
     "details": "99 killed. Lost in Atlantic SW of Azores. Cause still debated. Found in 3,000m of water."},
    {"name": "ARA San Juan (S-42)", "lat": -46.4400, "lon": -59.7700, "year": 2017,
     "type": "TR-1700 Class", "flag": "Argentina", "depth_m": 907,
     "cause": "Implosion at depth after battery failure",
     "details": "44 killed. Lost in South Atlantic. Found one year later at 907m by Ocean Infinity search vessel."},
    {"name": "INS Dakar", "lat": 33.3500, "lon": 28.9500, "year": 1968,
     "type": "T-class Submarine", "flag": "Israel", "depth_m": 3000,
     "cause": "Unknown, lost en route from UK to Israel",
     "details": "69 killed. Missing for 31 years until found in 1999 between Crete and Cyprus at 3,000m."},
    {"name": "HMS Thetis / Thunderbolt", "lat": 53.4500, "lon": -3.8333, "year": 1939,
     "type": "T-class Submarine", "flag": "UK", "depth_m": 49,
     "cause": "Torpedo tube door failure during trials",
     "details": "99 killed on trials in Liverpool Bay. Raised, renamed Thunderbolt, then sunk again in 1943 by depth charges."},
    {"name": "K-219", "lat": 31.2500, "lon": -54.7000, "year": 1986,
     "type": "Yankee-I Class SSBN", "flag": "Soviet Union", "depth_m": 5500,
     "cause": "Missile tube explosion and fire",
     "details": "4 killed. Sailor Sergei Preminin manually shut down reactor, sacrificing his life. Sank in 5,500m."},
    {"name": "K-129", "lat": 40.1000, "lon": -180.0000, "year": 1968,
     "type": "Golf-II Class SSB", "flag": "Soviet Union", "depth_m": 4900,
     "cause": "Unknown -- hydrogen explosion suspected",
     "details": "98 killed. CIA attempted secret recovery in Project Azorian using Hughes Glomar Explorer."},
    {"name": "Titan (OceanGate)", "lat": 41.7260, "lon": -49.9469, "year": 2023,
     "type": "Tourism Submersible", "flag": "USA", "depth_m": 3800,
     "cause": "Catastrophic implosion during Titanic dive",
     "details": "5 killed including CEO Stockton Rush. Carbon fiber hull failed at depth. Lost contact 1h45m into dive."},
    {"name": "HMSM Affray", "lat": 50.1083, "lon": -1.8167, "year": 1951,
     "type": "Amphion-class Submarine", "flag": "UK", "depth_m": 84,
     "cause": "Snort mast fracture, flooding",
     "details": "75 killed. Last Royal Navy submarine lost at sea. Found on seabed in English Channel."},
    {"name": "Minerve (S647)", "lat": 42.9833, "lon": 5.8500, "year": 1968,
     "type": "Daphne-class Submarine", "flag": "France", "depth_m": 2370,
     "cause": "Unknown, disappeared off Toulon",
     "details": "52 killed. Lost for 51 years. Found in 2019 at 2,370m in the Mediterranean by search team."},
    {"name": "KRI Nanggala (402)", "lat": -7.3333, "lon": 115.0167, "year": 2021,
     "type": "Type 209/1300", "flag": "Indonesia", "depth_m": 838,
     "cause": "Possible torpedo tube failure during exercise",
     "details": "53 killed. Lost during torpedo drill off Bali. Found in 3 pieces at 838m, well below crush depth."},
    {"name": "Komsomolets (K-278)", "lat": 73.7333, "lon": 13.2500, "year": 1989,
     "type": "Mike-class SSN", "flag": "Soviet Union", "depth_m": 1680,
     "cause": "Fire in aft compartment",
     "details": "42 killed. Held world depth record (1,027m). Fire broke out, crew abandoned. Lies with nuclear warheads."},
]

BERMUDA_TRIANGLE = [
    {"name": "Flight 19 (5 TBM Avengers)", "lat": 27.9500, "lon": -78.5000, "year": 1945,
     "type": "US Navy Torpedo Bombers (5 aircraft)", "flag": "USA", "depth_m": None,
     "mystery": "5 aircraft disappeared during training flight",
     "details": "14 airmen lost. Compass malfunction, disorientation. Rescue PBM Mariner also vanished (13 more crew)."},
    {"name": "USS Cyclops (AC-4)", "lat": 25.0000, "lon": -71.0000, "year": 1918,
     "type": "Proteus-class Collier", "flag": "USA", "depth_m": None,
     "mystery": "Largest non-combat loss of life in US Navy history",
     "details": "309 crew vanished en route from Barbados to Baltimore. No distress signal, no wreckage ever found."},
    {"name": "SS Marine Sulphur Queen", "lat": 25.2000, "lon": -83.0000, "year": 1963,
     "type": "T2 Tanker", "flag": "USA", "depth_m": None,
     "mystery": "Vanished with 39 crew in the Straits of Florida",
     "details": "Carried molten sulphur. Only debris and life jackets found. Coast Guard cited structural weaknesses."},
    {"name": "Star Tiger (BSAA)", "lat": 31.5000, "lon": -68.0000, "year": 1948,
     "type": "Avro Tudor IV Aircraft", "flag": "UK", "depth_m": None,
     "mystery": "Disappeared approaching Bermuda",
     "details": "31 passengers and crew lost. Last radio contact reported normal. No wreckage found."},
    {"name": "Star Ariel (BSAA)", "lat": 25.5000, "lon": -74.0000, "year": 1949,
     "type": "Avro Tudor IV Aircraft", "flag": "UK", "depth_m": None,
     "mystery": "Sister aircraft also disappeared in the Triangle",
     "details": "20 lost flying Bermuda to Jamaica. Two identical aircraft vanished a year apart. Tudor fleet grounded."},
    {"name": "SS Cotopaxi", "lat": 26.3000, "lon": -79.5000, "year": 1925,
     "type": "Cargo Steamship", "flag": "USA", "depth_m": None,
     "mystery": "Disappeared en route Charleston to Havana",
     "details": "32 crew lost. Featured in 'Close Encounters of the Third Kind'. Wreck possibly found in 2020."},
    {"name": "Douglas DC-3 (NC16002)", "lat": 26.0000, "lon": -80.5000, "year": 1948,
     "type": "Douglas DC-3 Aircraft", "flag": "USA", "depth_m": None,
     "mystery": "Disappeared on flight from San Juan to Miami",
     "details": "3 crew and 29 passengers vanished. Captain reported strong winds from the south. Never found."},
    {"name": "Witchcraft (cabin cruiser)", "lat": 25.7617, "lon": -80.4000, "year": 1967,
     "type": "Cabin Cruiser", "flag": "USA", "depth_m": None,
     "mystery": "Vanished one mile off Miami, Coast Guard found nothing",
     "details": "Owner called Coast Guard about a damaged propeller. 19 minutes later, boat and 2 people gone."},
    {"name": "Connemara IV", "lat": 28.0000, "lon": -73.0000, "year": 1955,
     "type": "Yacht", "flag": "UK", "depth_m": None,
     "mystery": "Found drifting with no crew aboard",
     "details": "Pleasure yacht found abandoned 400 miles SW of Bermuda. Three hurricanes had crossed the area."},
    {"name": "Ellen Austin Encounter", "lat": 29.0000, "lon": -69.0000, "year": 1881,
     "type": "Derelict Schooner", "flag": "Unknown", "depth_m": None,
     "mystery": "Abandoned ship, prize crew placed aboard also vanished",
     "details": "Ellen Austin found a derelict, put crew aboard. Ships separated in storm; when reunited, prize crew gone."},
    {"name": "USS Proteus (AC-9)", "lat": 25.0000, "lon": -69.0000, "year": 1941,
     "type": "Proteus-class Collier", "flag": "USA", "depth_m": None,
     "mystery": "Sister ship to Cyclops, also vanished",
     "details": "58 crew lost. Disappeared on same route as USS Cyclops. Possibly torpedoed by German U-boat."},
    {"name": "USS Nereus (AC-10)", "lat": 24.5000, "lon": -70.0000, "year": 1941,
     "type": "Proteus-class Collier", "flag": "USA", "depth_m": None,
     "mystery": "Third Proteus-class ship to vanish in the Triangle",
     "details": "61 crew lost. Like her sisters Cyclops and Proteus, she vanished without a trace."},
]

DISASTER_ZONES = [
    {"name": "Cape of Good Hope / Cape of Storms", "lat": -34.3568, "lon": 18.4740, "year": None,
     "type": "Disaster Zone", "flag": "South Africa", "depth_m": None,
     "ships_lost": "3,000+",
     "details": "Originally named Cape of Storms. Violent confluence of Atlantic and Indian oceans. Thousands of wrecks."},
    {"name": "Skeleton Coast", "lat": -19.0000, "lon": 12.5000, "year": None,
     "type": "Disaster Zone", "flag": "Namibia", "depth_m": None,
     "ships_lost": "1,000+",
     "details": "Cold Benguela current creates dense fog. Ships driven ashore on desolate desert coast. 'Gates of Hell'."},
    {"name": "Sable Island", "lat": 43.9333, "lon": -59.9167, "year": None,
     "type": "Disaster Zone", "flag": "Canada", "depth_m": None,
     "ships_lost": "350+",
     "details": "Graveyard of the Atlantic. Shifting sandbar 300km offshore of Nova Scotia. Over 350 recorded wrecks."},
    {"name": "Goodwin Sands", "lat": 51.2500, "lon": 1.5000, "year": None,
     "type": "Disaster Zone", "flag": "UK", "depth_m": None,
     "ships_lost": "2,000+",
     "details": "10-mile sandbank off Kent. 'Ship Swallower.' Shifting sands expose and re-bury wrecks constantly."},
    {"name": "Strait of Malacca", "lat": 2.5000, "lon": 101.5000, "year": None,
     "type": "Disaster Zone", "flag": "International", "depth_m": None,
     "ships_lost": "Hundreds",
     "details": "Busiest shipping lane in the world. Shallow, narrow, plagued by piracy. Hundreds of historical wrecks."},
    {"name": "Point Conception / Honda Point", "lat": 34.4920, "lon": -120.4790, "year": None,
     "type": "Disaster Zone", "flag": "USA", "depth_m": None,
     "ships_lost": "60+",
     "details": "California coast graveyard. In 1923, seven US destroyers ran aground simultaneously (Honda Point Disaster)."},
    {"name": "Scilly Isles", "lat": 49.9361, "lon": -6.3228, "year": None,
     "type": "Disaster Zone", "flag": "UK", "depth_m": None,
     "ships_lost": "800+",
     "details": "Rocky isles off Cornwall. Admiral Shovell's fleet wrecked here in 1707. Over 800 recorded wrecks."},
    {"name": "Diamond Shoals / Cape Hatteras", "lat": 35.2167, "lon": -75.5000, "year": None,
     "type": "Disaster Zone", "flag": "USA", "depth_m": None,
     "ships_lost": "600+",
     "details": "Graveyard of the Atlantic. Gulf Stream meets Labrador Current. Hundreds of wrecks from colonial era to WWII U-boats."},
    {"name": "Bass Strait", "lat": -39.5000, "lon": 145.5000, "year": None,
     "type": "Disaster Zone", "flag": "Australia", "depth_m": None,
     "ships_lost": "700+",
     "details": "Notoriously rough strait between Australia and Tasmania. Strong currents and storms. 700+ wrecks."},
    {"name": "Ushant / Ile d'Ouessant", "lat": 48.4500, "lon": -5.1000, "year": None,
     "type": "Disaster Zone", "flag": "France", "depth_m": None,
     "ships_lost": "300+",
     "details": "Rocky island off Brittany. Fierce tidal races and fog. Major shipping lane entrance to English Channel."},
    {"name": "Iron Bottom Sound", "lat": -9.1500, "lon": 159.9500, "year": 1942,
     "type": "Naval Graveyard", "flag": "International", "depth_m": 400,
     "ships_lost": "50+ warships",
     "details": "Guadalcanal, Solomon Islands. So many ships sunk in WWII naval battles the seabed is covered with wrecks."},
    {"name": "Truk Lagoon (Chuuk)", "lat": 7.4167, "lon": 151.8500, "year": 1944,
     "type": "Naval Graveyard", "flag": "Japan", "depth_m": 70,
     "ships_lost": "60+ ships and 275 aircraft",
     "details": "Japanese fleet destroyed by Operation Hailstone. Now the world's largest ship graveyard and top dive site."},
]

UNDERWATER_ARCHAEOLOGY = [
    {"name": "Alexandria / Cleopatra's Palace", "lat": 31.2100, "lon": 29.8850, "year": -30,
     "type": "Submerged City", "flag": "Egypt", "depth_m": 8,
     "status": "Active excavation, UNESCO candidate",
     "details": "Ancient royal quarters submerged by earthquakes. Franck Goddio's team found statues, sphinxes, temples."},
    {"name": "Pavlopetri", "lat": 36.5160, "lon": 22.5550, "year": -3000,
     "type": "Submerged City", "flag": "Greece", "depth_m": 4,
     "status": "UNESCO protected, oldest submerged city",
     "details": "5,000-year-old city off Laconia. Streets, buildings, tombs visible. Oldest known planned underwater town."},
    {"name": "Port Royal, Jamaica", "lat": 17.9353, "lon": -76.8412, "year": 1692,
     "type": "Submerged City", "flag": "Jamaica", "depth_m": 12,
     "status": "UNESCO World Heritage tentative list",
     "details": "Pirate capital destroyed by 1692 earthquake. Entire city slid into the sea. 'Sodom of the New World'."},
    {"name": "Scapa Flow Wrecks", "lat": 58.8833, "lon": -3.1500, "year": 1919,
     "type": "Naval Graveyard / Dive Site", "flag": "UK", "depth_m": 45,
     "status": "Scheduled Monument, premier dive site",
     "details": "German High Seas Fleet scuttled here. 52 ships sunk, 7 remain on seabed. World-class wreck diving."},
    {"name": "Bikini Atoll Wrecks", "lat": 11.5833, "lon": 165.3833, "year": 1946,
     "type": "Nuclear Test Target Fleet", "flag": "USA", "depth_m": 55,
     "status": "UNESCO World Heritage Site",
     "details": "Fleet of warships sunk by nuclear tests. Includes USS Saratoga and IJN Nagato. Radioactive dive site."},
    {"name": "Yonaguni Monument", "lat": 24.4350, "lon": 123.0108, "year": None,
     "type": "Underwater Structure", "flag": "Japan", "depth_m": 25,
     "status": "Debated -- natural vs man-made",
     "details": "Mysterious terraced structure off Yonaguni Island. Debated whether it is a natural formation or ancient ruin."},
    {"name": "Dwarka / Bet Dwarka", "lat": 22.2394, "lon": 68.9672, "year": -1500,
     "type": "Submerged Ancient City", "flag": "India", "depth_m": 12,
     "status": "ASI protected, ongoing research",
     "details": "Legendary city of Lord Krishna. Underwater structures and artifacts found. Mentioned in Mahabharata."},
    {"name": "Baia / Baiae", "lat": 40.8175, "lon": 14.0764, "year": 200,
     "type": "Submerged Roman Resort", "flag": "Italy", "depth_m": 6,
     "status": "Marine Protected Area, underwater museum",
     "details": "Luxury Roman resort submerged by volcanic bradyseism. Villas, mosaics, statues visible underwater."},
    {"name": "SS Thistlegorm", "lat": 27.8125, "lon": 33.9222, "year": 1941,
     "type": "Premier Dive Wreck", "flag": "Egypt/UK", "depth_m": 30,
     "status": "Most popular wreck dive in the world",
     "details": "WWII cargo ship in the Red Sea. Motorcycles, trucks, locomotives still visible in holds. Found by Cousteau."},
    {"name": "Museo Atlantico", "lat": 28.9183, "lon": -13.6583, "year": 2016,
     "type": "Underwater Sculpture Museum", "flag": "Spain", "depth_m": 14,
     "status": "Open to divers, first in Europe",
     "details": "Jason deCaires Taylor's underwater sculptures off Lanzarote. Over 300 life-size figures at 12-15m."},
    {"name": "Zenobia Wreck", "lat": 34.9167, "lon": 33.6500, "year": 1980,
     "type": "Premier Dive Wreck", "flag": "Cyprus", "depth_m": 42,
     "status": "Top 10 dive site worldwide",
     "details": "Swedish ro-ro ferry that capsized off Larnaca. 104 articulated trucks still chained in cargo holds."},
    {"name": "HMAS Brisbane Dive Wreck", "lat": -26.8500, "lon": 153.3833, "year": 2005,
     "type": "Artificial Reef / Dive Site", "flag": "Australia", "depth_m": 28,
     "status": "Purpose-sunk dive attraction",
     "details": "Perth-class destroyer deliberately scuttled to create artificial reef off Mooloolaba, Queensland."},
]

MODERN_DISASTERS = [
    {"name": "Costa Concordia", "lat": 42.3658, "lon": 10.9217, "year": 2012,
     "type": "Cruise Ship", "flag": "Italy", "depth_m": 20,
     "casualties": 32,
     "details": "Capsized off Giglio Island after hitting rocks. Captain Schettino abandoned ship. Largest parbuckling salvage ever."},
    {"name": "MV Sewol", "lat": 34.1681, "lon": 125.9419, "year": 2014,
     "type": "Passenger Ferry", "flag": "South Korea", "depth_m": 44,
     "casualties": 304,
     "details": "Capsized off Jindo. 304 killed, mostly high school students. Captain fled. National trauma in South Korea."},
    {"name": "SS El Faro", "lat": 23.2167, "lon": -73.8833, "year": 2015,
     "type": "Cargo Ship", "flag": "USA", "depth_m": 4572,
     "casualties": 33,
     "details": "Sank in Hurricane Joaquin near Bahamas. All 33 crew lost. Found at 4,572m. VDR recovered."},
    {"name": "MV Sewol", "lat": 34.1681, "lon": 125.9419, "year": 2014,
     "type": "Passenger Ferry", "flag": "South Korea", "depth_m": 44,
     "casualties": 304,
     "details": "Capsized en route to Jeju. 304 killed, mostly Danwon High students. Crew told passengers to stay put."},
    {"name": "Ever Given Grounding", "lat": 30.0167, "lon": 32.5800, "year": 2021,
     "type": "Ultra-Large Container Ship", "flag": "Panama", "depth_m": 0,
     "casualties": 0,
     "details": "Blocked the Suez Canal for 6 days. 400m long, 224,000 tons. $9.6 billion daily trade disrupted."},
    {"name": "MV Rena", "lat": -37.5542, "lon": 176.4347, "year": 2011,
     "type": "Container Ship", "flag": "Liberia", "depth_m": 22,
     "casualties": 0,
     "details": "Grounded on Astrolabe Reef, New Zealand. Broke in two. Worst environmental maritime disaster in NZ."},
    {"name": "MV Prestige", "lat": 42.1333, "lon": -12.0833, "year": 2002,
     "type": "Oil Tanker", "flag": "Bahamas", "depth_m": 3500,
     "casualties": 0,
     "details": "Broke apart off Galicia, Spain. 77,000 tons of oil spilled. Worst environmental disaster in Spanish history."},
    {"name": "MV Le Joola", "lat": 12.6000, "lon": -17.5000, "year": 2002,
     "type": "Government Ferry", "flag": "Senegal", "depth_m": 23,
     "casualties": 1863,
     "details": "Africa's worst maritime disaster. Capsized off The Gambia. Overcrowded: ~2,000 aboard, capacity 580."},
    {"name": "MV Princess of the Stars", "lat": 11.5833, "lon": 123.7667, "year": 2008,
     "type": "Passenger Ferry", "flag": "Philippines", "depth_m": 35,
     "casualties": 800,
     "details": "Capsized in Typhoon Frank in Sibuyan Sea. ~800 killed. Carried toxic pesticide cargo."},
    {"name": "Deepwater Horizon", "lat": 28.7367, "lon": -88.3867, "year": 2010,
     "type": "Oil Drilling Rig", "flag": "USA", "depth_m": 1500,
     "casualties": 11,
     "details": "Largest marine oil spill in history. 4.9 million barrels leaked. 11 killed. Ecological devastation of Gulf coast."},
    {"name": "MV Rocknes", "lat": 60.2833, "lon": 5.2000, "year": 2004,
     "type": "Cargo Ship", "flag": "Antigua", "depth_m": 24,
     "casualties": 18,
     "details": "Capsized in Vatlestraumen strait, Norway. 18 of 30 crew killed. Hit an underwater rock shelf."},
    {"name": "Norman Atlantic", "lat": 39.9167, "lon": 19.1000, "year": 2014,
     "type": "Passenger Ferry", "flag": "Italy", "depth_m": 0,
     "casualties": 31,
     "details": "Fire broke out on Adriatic crossing from Greece to Italy. 31 killed. Passengers stranded on burning ship."},
    {"name": "MV X-Press Pearl", "lat": 6.9500, "lon": 79.7833, "year": 2021,
     "type": "Container Ship", "flag": "Singapore", "depth_m": 21,
     "casualties": 0,
     "details": "Caught fire and sank off Colombo, Sri Lanka. Carried nitric acid and nurdles. Worst marine eco disaster in SL."},
]


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOOKUPS
# ═══════════════════════════════════════════════════════════════════════════════
_MODE_DATA = {
    "Famous Shipwrecks": FAMOUS_SHIPWRECKS,
    "Treasure Ships": TREASURE_SHIPS,
    "World War Wrecks": WORLD_WAR_WRECKS,
    "Ancient Shipwrecks": ANCIENT_SHIPWRECKS,
    "Ghost Ships": GHOST_SHIPS,
    "Submarine Disasters": SUBMARINE_DISASTERS,
    "Bermuda Triangle": BERMUDA_TRIANGLE,
    "Maritime Disaster Zones": DISASTER_ZONES,
    "Underwater Archaeology Sites": UNDERWATER_ARCHAEOLOGY,
    "Modern Maritime Disasters": MODERN_DISASTERS,
}


# ═══════════════════════════════════════════════════════════════════════════════
# OVERPASS API HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def search_osm_wrecks(lat: float, lon: float, radius_km: float = 50) -> list:
    """Search for shipwrecks in OpenStreetMap via Overpass API."""
    radius_m = int(radius_km * 1000)
    query = f"""
[out:json][timeout:60];
(
  node["historic"="wreck"](around:{radius_m},{lat},{lon});
  way["historic"="wreck"](around:{radius_m},{lat},{lon});
  node["seamark:type"="wreck"](around:{radius_m},{lat},{lon});
  way["seamark:type"="wreck"](around:{radius_m},{lat},{lon});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return []

    elements = result.get("elements", [])
    node_lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            node_lookup[el["id"]] = (el["lat"], el["lon"])

    wrecks = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue

        lat_w, lon_w = None, None
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lat_w, lon_w = el["lat"], el["lon"]
        elif el.get("type") == "way":
            nodes = el.get("nodes", [])
            coords = [node_lookup[n] for n in nodes if n in node_lookup]
            if coords:
                lat_w = sum(c[0] for c in coords) / len(coords)
                lon_w = sum(c[1] for c in coords) / len(coords)

        if lat_w is None or lon_w is None:
            continue

        name = tags.get("name", tags.get("seamark:name",
               tags.get("name:en", "Unknown Wreck")))
        wrecks.append({
            "name": name,
            "lat": lat_w,
            "lon": lon_w,
            "year": tags.get("year", tags.get("start_date", "")),
            "type": tags.get("seamark:type", tags.get("historic", "wreck")),
            "details": tags.get("description", tags.get("note", "")),
            "wikipedia": tags.get("wikipedia", ""),
            "wikidata": tags.get("wikidata", ""),
            "osm_id": el.get("id"),
        })

    return wrecks


# ═══════════════════════════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _make_bar_chart(labels: list, values: list, colors: list, title: str,
                    xlabel: str = "Count"):
    """Create a horizontal bar chart with dark theme."""
    fig, ax = plt.subplots(figsize=(7, max(3, len(labels) * 0.45)))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)

    bars = ax.barh(range(len(labels)), values, color=colors, alpha=0.85,
                   edgecolor=_BORDER, linewidth=0.5)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, color=_TEXT2, fontsize=9)
    ax.set_xlabel(xlabel, color=_TEXT2, fontsize=10)
    ax.set_title(title, color=_TEXT, fontsize=12, fontweight="bold", pad=10)
    ax.tick_params(axis="x", colors=_TEXT2, labelsize=9)
    ax.grid(True, axis="x", color=_BORDER, linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    ax.invert_yaxis()

    # Value labels on bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.02, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", color=_TEXT, fontsize=8)

    fig.tight_layout()
    return fig


def _make_pie_chart(labels: list, values: list, colors: list, title: str):
    """Create a pie chart with dark theme."""
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_BG)

    wedges, texts, autotexts = ax.pie(
        values, labels=None, colors=colors, autopct="%1.0f%%",
        startangle=140, pctdistance=0.8,
        wedgeprops={"edgecolor": _BORDER, "linewidth": 0.5},
    )
    for t in autotexts:
        t.set_color(_TEXT)
        t.set_fontsize(8)

    ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5),
              fontsize=8, facecolor=_SURFACE, edgecolor=_BORDER,
              labelcolor=_TEXT2)
    ax.set_title(title, color=_TEXT, fontsize=12, fontweight="bold", pad=10)
    fig.tight_layout()
    return fig


def _make_timeline_chart(wrecks: list, color: str, title: str):
    """Create a timeline scatter plot of wrecks by year."""
    dated = [w for w in wrecks if w.get("year") and w["year"] is not None]
    if not dated:
        return None

    years = []
    names = []
    for w in dated:
        try:
            y = int(w["year"])
            years.append(y)
            names.append(w["name"][:25])
        except (ValueError, TypeError):
            continue

    if not years:
        return None

    fig, ax = plt.subplots(figsize=(10, max(3, len(years) * 0.35)))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)

    sorted_pairs = sorted(zip(years, names))
    years_s = [p[0] for p in sorted_pairs]
    names_s = [p[1] for p in sorted_pairs]

    ax.scatter(years_s, range(len(years_s)), color=color, s=60, alpha=0.85,
               edgecolors=_TEXT, linewidth=0.3, zorder=5)

    for i, (yr, nm) in enumerate(zip(years_s, names_s)):
        ax.text(yr + (max(years_s) - min(years_s)) * 0.02, i,
                f"{nm} ({yr})", va="center", color=_TEXT2, fontsize=7.5)

    ax.set_yticks([])
    ax.set_xlabel("Year", color=_TEXT2, fontsize=10)
    ax.set_title(title, color=_TEXT, fontsize=12, fontweight="bold", pad=10)
    ax.tick_params(axis="x", colors=_TEXT2, labelsize=9)
    ax.grid(True, axis="x", color=_BORDER, linewidth=0.5, alpha=0.5)
    for spine in ax.spines.values():
        spine.set_color(_BORDER)
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# MAP BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
def _build_wreck_map(wrecks: list, color: str, mode: str,
                     center: list = None, zoom: int = 3) -> folium.Map:
    """Build a Folium map of wreck locations with ship icon markers."""
    valid = [w for w in wrecks if w.get("lat") is not None and w.get("lon") is not None]

    if not valid:
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        return m

    if center is None:
        avg_lat = sum(w["lat"] for w in valid) / len(valid)
        avg_lon = sum(w["lon"] for w in valid) / len(valid)
        center = [avg_lat, avg_lon]

    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter")

    for w in valid:
        safe_name = escape(str(w.get("name", "Unknown")))
        safe_type = escape(str(w.get("type", "")))
        safe_details = escape(str(w.get("details", ""))[:300])
        year_str = str(w.get("year", "Unknown")) if w.get("year") else "Unknown"
        safe_year = escape(year_str)
        depth_str = f"{w['depth_m']}m" if w.get("depth_m") else "Unknown"
        safe_depth = escape(depth_str)

        # Extra fields based on mode
        extra_html = ""
        if "cargo" in w and w["cargo"]:
            safe_cargo = escape(str(w["cargo"]))
            extra_html += f'<br/><b>Cargo:</b> {safe_cargo}'
        if "conflict" in w and w["conflict"]:
            safe_conflict = escape(str(w["conflict"]))
            extra_html += f'<br/><b>Conflict:</b> {safe_conflict}'
        if "mystery" in w and w["mystery"]:
            safe_mystery = escape(str(w["mystery"]))
            extra_html += f'<br/><b>Mystery:</b> {safe_mystery}'
        if "cause" in w and w["cause"]:
            safe_cause = escape(str(w["cause"]))
            extra_html += f'<br/><b>Cause:</b> {safe_cause}'
        if "ships_lost" in w and w["ships_lost"]:
            safe_lost = escape(str(w["ships_lost"]))
            extra_html += f'<br/><b>Ships lost:</b> {safe_lost}'
        if "casualties" in w and w.get("casualties") is not None:
            extra_html += f'<br/><b>Casualties:</b> {escape(str(w["casualties"]))}'
        if "status" in w and w["status"]:
            safe_status = escape(str(w["status"]))
            extra_html += f'<br/><b>Status:</b> {safe_status}'
        if "period" in w and w["period"]:
            safe_period = escape(str(w["period"]))
            extra_html += f'<br/><b>Period:</b> {safe_period}'

        popup_html = f"""
        <div style="max-width:280px; font-family:sans-serif; font-size:12px;">
            <div style="font-weight:700; font-size:13px; margin-bottom:4px;
                        color:#111; border-bottom:2px solid {color}; padding-bottom:3px;">
                {safe_name}
            </div>
            <b>Type:</b> {safe_type}<br/>
            <b>Year:</b> {safe_year}<br/>
            <b>Depth:</b> {safe_depth}
            {extra_html}
            <div style="margin-top:6px; color:#444; font-size:11px;">
                {safe_details}
            </div>
            <div style="margin-top:4px; color:#888; font-size:10px;">
                {escape(f"{w['lat']:.4f}")}, {escape(f"{w['lon']:.4f}")}
            </div>
        </div>
        """

        # Use ship icon via DivIcon for a distinctive marker
        icon_html = f"""
        <div style="font-size:18px; color:{color}; text-shadow:0 0 6px {color}40,
                     0 1px 3px rgba(0,0,0,0.5); text-align:center; line-height:1;">
            &#9875;
        </div>
        """

        folium.Marker(
            location=[w["lat"], w["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=safe_name,
            icon=folium.DivIcon(
                html=icon_html,
                icon_size=(24, 24),
                icon_anchor=(12, 12),
                class_name="shipwreck-icon",
            ),
        ).add_to(m)

    return m


# ═══════════════════════════════════════════════════════════════════════════════
# DATAFRAME BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
def _wrecks_to_dataframe(wrecks: list) -> pd.DataFrame:
    """Convert wreck list to a clean DataFrame."""
    rows = []
    for w in wrecks:
        row = {
            "Name": w.get("name", "Unknown"),
            "Latitude": w.get("lat"),
            "Longitude": w.get("lon"),
            "Year": w.get("year"),
            "Type": w.get("type", ""),
            "Flag/Nation": w.get("flag", ""),
            "Depth (m)": w.get("depth_m"),
        }
        # Optional columns
        for key in ("cargo", "conflict", "mystery", "cause", "ships_lost",
                    "casualties", "status", "period", "details"):
            if key in w and w[key]:
                col_name = key.replace("_", " ").title()
                row[col_name] = w[key]
        rows.append(row)
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════════════
# STATS PANEL BUILDER
# ═══════════════════════════════════════════════════════════════════════════════
def _render_stats(wrecks: list, mode: str, color: str):
    """Render summary stats for the current mode."""
    total = len(wrecks)
    dated = [w for w in wrecks if w.get("year") is not None]
    with_depth = [w for w in wrecks if w.get("depth_m") is not None]

    cols = st.columns(4)
    cols[0].metric("Total Entries", total)

    if dated:
        try:
            years = [int(w["year"]) for w in dated]
            cols[1].metric("Earliest", min(years))
            cols[2].metric("Latest", max(years))
        except (ValueError, TypeError):
            cols[1].metric("Dated Entries", len(dated))
            cols[2].metric("Undated", total - len(dated))
    else:
        cols[1].metric("Dated Entries", 0)
        cols[2].metric("Undated", total)

    if with_depth:
        max_d = max(w["depth_m"] for w in with_depth)
        cols[3].metric("Deepest (m)", f"{max_d:,}")
    else:
        cols[3].metric("With Depth Data", 0)

    # Type breakdown
    type_counts = {}
    for w in wrecks:
        t = w.get("type", "Unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    if len(type_counts) > 1:
        sorted_types = sorted(type_counts.items(), key=lambda x: -x[1])[:10]
        labels = [t[0][:35] for t in sorted_types]
        values = [t[1] for t in sorted_types]
        colors = [color] * len(labels)
        fig = _make_bar_chart(labels, values, colors,
                              f"{mode} -- by Type", "Count")
        st.pyplot(fig)
        plt.close(fig)

    # Country/flag breakdown
    flag_counts = {}
    for w in wrecks:
        f = w.get("flag", "Unknown")
        if f:
            flag_counts[f] = flag_counts.get(f, 0) + 1

    if len(flag_counts) > 1:
        sorted_flags = sorted(flag_counts.items(), key=lambda x: -x[1])[:8]
        labels = [f[0] for f in sorted_flags]
        values = [f[1] for f in sorted_flags]
        palette = ["#06b6d4", "#f59e0b", "#ef4444", "#8b5cf6",
                    "#10b981", "#ec4899", "#3b82f6", "#f97316"]
        colors = palette[:len(labels)]
        fig = _make_pie_chart(labels, values, colors,
                              f"{mode} -- by Nation/Flag")
        st.pyplot(fig)
        plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
# WRECK DETAIL CARDS
# ═══════════════════════════════════════════════════════════════════════════════
def _render_wreck_cards(wrecks: list, color: str, max_cards: int = 15):
    """Render detailed cards for each wreck."""
    for i, w in enumerate(wrecks[:max_cards]):
        safe_name = escape(str(w.get("name", "Unknown")))
        safe_type = escape(str(w.get("type", "")))
        safe_details = escape(str(w.get("details", "")))
        year_str = str(w.get("year", "")) if w.get("year") else "Unknown"
        depth_str = f"{w['depth_m']:,}m" if w.get("depth_m") else "Unknown"
        flag_str = escape(str(w.get("flag", "")))

        # Build extra info line
        extra_parts = []
        if w.get("cargo"):
            extra_parts.append(f"<b>Cargo:</b> {escape(str(w['cargo']))}")
        if w.get("conflict"):
            extra_parts.append(f"<b>Conflict:</b> {escape(str(w['conflict']))}")
        if w.get("mystery"):
            extra_parts.append(f"<b>Mystery:</b> {escape(str(w['mystery']))}")
        if w.get("cause"):
            extra_parts.append(f"<b>Cause:</b> {escape(str(w['cause']))}")
        if w.get("ships_lost"):
            extra_parts.append(f"<b>Ships lost:</b> {escape(str(w['ships_lost']))}")
        if w.get("casualties") is not None:
            extra_parts.append(f"<b>Casualties:</b> {escape(str(w['casualties']))}")
        if w.get("status"):
            extra_parts.append(f"<b>Status:</b> {escape(str(w['status']))}")
        if w.get("period"):
            extra_parts.append(f"<b>Period:</b> {escape(str(w['period']))}")

        extra_html = "<br/>".join(extra_parts)
        if extra_html:
            extra_html = f'<div style="margin-top:4px; font-size:0.78rem; color:{_TEXT2};">{extra_html}</div>'

        lat_str = f"{w['lat']:.4f}" if w.get("lat") is not None else "?"
        lon_str = f"{w['lon']:.4f}" if w.get("lon") is not None else "?"

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:flex-start; margin-bottom:0.6rem;
                    padding:0.6rem 0.8rem; border-left:3px solid {color};
                    background:rgba(17,24,39,0.5); border-radius:6px;">
            <div style="font-size:1.4rem; margin-right:0.7rem; color:{color};
                        line-height:1; padding-top:2px;">&#9875;</div>
            <div style="flex:1;">
                <div style="color:{_TEXT}; font-weight:700; font-size:0.9rem;">
                    {safe_name}
                    <span style="color:{_MUTED}; font-weight:400; font-size:0.75rem; margin-left:6px;">
                        {escape(year_str)} &middot; {flag_str}
                    </span>
                </div>
                <div style="color:{_TEXT2}; font-size:0.8rem; margin-top:2px;">
                    {safe_type} &middot; Depth: {escape(depth_str)} &middot;
                    <span style="color:{_MUTED};">{escape(lat_str)}, {escape(lon_str)}</span>
                </div>
                {extra_html}
                <div style="color:{_MUTED}; font-size:0.75rem; margin-top:4px; line-height:1.4;">
                    {safe_details}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# OSM WRECK SEARCH PANEL
# ═══════════════════════════════════════════════════════════════════════════════
def _render_osm_search():
    """Render a panel for searching OSM wrecks near a location."""
    st.markdown("---")
    st.markdown("#### Search OpenStreetMap Wrecks")
    st.markdown(
        f'<div style="color:{_TEXT2}; font-size:0.85rem; margin-bottom:0.5rem;">'
        'Search for shipwrecks tagged in OpenStreetMap near any coordinates. '
        'Uses <code>historic=wreck</code> and <code>seamark:type=wreck</code> tags.'
        '</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        osm_lat = st.number_input("Latitude", value=51.25, format="%.4f",
                                  min_value=-90.0, max_value=90.0,
                                  key="wreck_osm_lat")
    with c2:
        osm_lon = st.number_input("Longitude", value=-8.55, format="%.4f",
                                  min_value=-180.0, max_value=180.0,
                                  key="wreck_osm_lon")
    with c3:
        osm_radius = st.slider("Radius (km)", 5, 200, 50,
                                key="wreck_osm_radius",
                                help="Search radius around center point")

    # Preset areas for OSM search
    osm_presets = {
        "Custom": None,
        "Old Head of Kinsale (Lusitania)": {"lat": 51.60, "lon": -8.54, "r": 30},
        "Scapa Flow, Orkney": {"lat": 58.88, "lon": -3.15, "r": 20},
        "English Channel": {"lat": 50.50, "lon": -1.00, "r": 100},
        "Outer Banks, NC": {"lat": 35.22, "lon": -75.50, "r": 50},
        "Red Sea Wrecks": {"lat": 27.80, "lon": 33.90, "r": 100},
        "Mediterranean": {"lat": 36.00, "lon": 15.00, "r": 200},
        "Truk Lagoon": {"lat": 7.42, "lon": 151.85, "r": 30},
        "Great Lakes": {"lat": 44.00, "lon": -83.00, "r": 200},
    }

    osm_preset = st.selectbox("Preset Areas", list(osm_presets.keys()),
                               key="wreck_osm_preset")
    if osm_preset != "Custom" and osm_presets.get(osm_preset):
        p = osm_presets[osm_preset]
        osm_lat = p["lat"]
        osm_lon = p["lon"]
        osm_radius = p["r"]

    if st.button("Search OSM Wrecks", key="wreck_osm_search", type="primary"):
        with st.spinner("Querying OpenStreetMap for wrecks..."):
            results = search_osm_wrecks(osm_lat, osm_lon, osm_radius)

        if not results:
            st.warning("No wrecks found in this area via OSM. "
                       "Try a larger radius or different location.")
            return

        st.success(f"Found {len(results)} wreck(s) in OpenStreetMap")

        # Map of OSM results
        osm_map = folium.Map(
            location=[osm_lat, osm_lon], zoom_start=9,
            tiles="CartoDB dark_matter",
        )

        folium.Circle(
            location=[osm_lat, osm_lon],
            radius=osm_radius * 1000,
            color=_ACCENT, fill=True, fill_opacity=0.03, weight=1,
        ).add_to(osm_map)

        for w in results:
            safe_name = escape(str(w.get("name", "Unknown Wreck")))
            safe_detail = escape(str(w.get("details", ""))[:200])
            year_str = escape(str(w.get("year", "Unknown")))
            wiki_link = ""
            if w.get("wikipedia"):
                parts = w["wikipedia"].split(":", 1)
                if len(parts) == 2:
                    lang, title = parts
                else:
                    lang, title = "en", parts[0]
                wiki_link = (f'<br/><a href="https://{escape(lang)}.wikipedia.org/wiki/'
                             f'{escape(title)}" target="_blank" '
                             f'style="font-size:0.75rem;">Wikipedia</a>')

            popup = f"""
            <div style="max-width:240px; font-size:12px;">
                <strong>{safe_name}</strong><br/>
                <b>Year:</b> {year_str}<br/>
                {safe_detail}
                {wiki_link}
            </div>
            """
            icon_html = f"""
            <div style="font-size:16px; color:{_ACCENT};
                        text-shadow:0 0 5px {_ACCENT}40;">&#9875;</div>
            """
            folium.Marker(
                location=[w["lat"], w["lon"]],
                popup=folium.Popup(popup, max_width=260),
                tooltip=safe_name,
                icon=folium.DivIcon(
                    html=icon_html, icon_size=(20, 20),
                    icon_anchor=(10, 10), class_name="osm-wreck-icon",
                ),
            ).add_to(osm_map)

        components.html(osm_map._repr_html_(), height=500)

        # Table of OSM results
        osm_rows = []
        for w in results:
            osm_rows.append({
                "Name": w.get("name", "Unknown"),
                "Latitude": round(w["lat"], 5),
                "Longitude": round(w["lon"], 5),
                "Year": w.get("year", ""),
                "Type": w.get("type", ""),
                "Wikipedia": w.get("wikipedia", ""),
                "OSM ID": w.get("osm_id", ""),
            })

        osm_df = pd.DataFrame(osm_rows)
        with st.expander(f"OSM Wreck Data ({len(osm_df)} wrecks)", expanded=False):
            st.dataframe(osm_df, width="stretch", hide_index=True)

        csv_buf = io.StringIO()
        osm_df.to_csv(csv_buf, index=False)
        st.download_button(
            f"Download {len(osm_rows)} OSM Wrecks (CSV)",
            data=csv_buf.getvalue(),
            file_name="osm_shipwrecks.csv",
            mime="text/csv",
            key="wreck_osm_download",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MODE-SPECIFIC INTRO PANELS
# ═══════════════════════════════════════════════════════════════════════════════
_MODE_ICONS = {
    "Famous Shipwrecks": "&#9875;",
    "Treasure Ships": "&#128176;",
    "World War Wrecks": "&#9876;",
    "Ancient Shipwrecks": "&#127963;",
    "Ghost Ships": "&#128123;",
    "Submarine Disasters": "&#9978;",
    "Bermuda Triangle": "&#9650;",
    "Maritime Disaster Zones": "&#9888;",
    "Underwater Archaeology Sites": "&#127959;",
    "Modern Maritime Disasters": "&#128674;",
}


def _render_mode_intro(mode: str, color: str, wrecks: list):
    """Render the introductory panel for a mode."""
    icon = _MODE_ICONS.get(mode, "&#9875;")
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
                {len(wrecks)} entries
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
def render_shipwreck_maps_tab():
    """Main render function for the Shipwrecks & Maritime Disasters tab."""

    # ── Header ──
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>&#9875; Shipwrecks & Maritime Disasters</h4>'
        '<p>Famous wrecks, treasure ships, submarine graves & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # MODE SELECTOR
    # ══════════════════════════════════════════
    st.markdown("#### Select Map Mode")

    mode = st.selectbox(
        "Choose a shipwreck category to explore",
        MAP_MODES,
        key="wreck_mode",
        help="Each mode features a curated dataset with interactive map, statistics, and downloadable data.",
    )

    color = MODE_COLORS.get(mode, _ACCENT)
    wrecks = _MODE_DATA.get(mode, [])

    # Remove any accidental duplicates (based on name)
    seen_names = set()
    unique_wrecks = []
    for w in wrecks:
        name = w.get("name", "")
        if name not in seen_names:
            seen_names.add(name)
            unique_wrecks.append(w)
    wrecks = unique_wrecks

    # ══════════════════════════════════════════
    # MODE INTRODUCTION
    # ══════════════════════════════════════════
    _render_mode_intro(mode, color, wrecks)

    # ══════════════════════════════════════════
    # STATS OVERVIEW
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Overview & Statistics")
    _render_stats(wrecks, mode, color)

    # ══════════════════════════════════════════
    # TIMELINE
    # ══════════════════════════════════════════
    with st.expander("Timeline", expanded=False):
        fig = _make_timeline_chart(wrecks, color, f"{mode} -- Timeline")
        if fig:
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("No dated entries available for a timeline in this mode.")

    # ══════════════════════════════════════════
    # INTERACTIVE MAP
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Interactive Map")

    # Legend
    st.markdown(
        f'<div style="display:flex; align-items:center; gap:0.5rem; '
        f'margin-bottom:0.5rem;">'
        f'<span style="font-size:1.2rem; color:{color};">&#9875;</span>'
        f'<span style="color:{_TEXT2}; font-size:0.85rem;">'
        f'{escape(mode)} &mdash; {len(wrecks)} locations mapped</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Determine optimal zoom and center based on mode
    zoom_overrides = {
        "Bermuda Triangle": (26.0, -72.0, 5),
        "Maritime Disaster Zones": (20.0, 0.0, 2),
        "Underwater Archaeology Sites": (25.0, 30.0, 2),
        "Modern Maritime Disasters": (20.0, 30.0, 2),
    }

    if mode in zoom_overrides:
        c_lat, c_lon, zoom = zoom_overrides[mode]
        m = _build_wreck_map(wrecks, color, mode, center=[c_lat, c_lon], zoom=zoom)
    else:
        m = _build_wreck_map(wrecks, color, mode)

    components.html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # WRECK DETAIL CARDS
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Detailed Entries")

    show_all = st.checkbox("Show all entries", value=False, key="wreck_show_all")
    max_display = len(wrecks) if show_all else min(12, len(wrecks))

    _render_wreck_cards(wrecks, color, max_cards=max_display)

    if not show_all and len(wrecks) > 12:
        st.caption(f"Showing 12 of {len(wrecks)} entries. Check 'Show all entries' to see everything.")

    # ══════════════════════════════════════════
    # DATA TABLE & DOWNLOAD
    # ══════════════════════════════════════════
    st.markdown("---")
    df = _wrecks_to_dataframe(wrecks)

    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(df)} {mode} Entries (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"shipwrecks_{mode.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="wreck_csv_download",
    )

    # ══════════════════════════════════════════
    # OSM WRECK SEARCH
    # ══════════════════════════════════════════
    _render_osm_search()

    # ══════════════════════════════════════════
    # FOOTER INFO
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(
        f'<div style="color:{_MUTED}; font-size:0.75rem; line-height:1.5; '
        f'padding:0.5rem 0;">'
        f'<b>Data Sources:</b> Curated historical records, OpenStreetMap '
        f'(<code>historic=wreck</code>, <code>seamark:type=wreck</code>), '
        f'public maritime archives.<br/>'
        f'<b>Note:</b> Coordinates are approximate for deep-ocean wrecks. '
        f'Depths may vary by source. Some wrecks have never been located '
        f'and positions shown are last known or estimated.<br/>'
        f'<b>Disclaimer:</b> Many wreck sites are protected war graves. '
        f'Diving on protected wrecks without authorization may be illegal.'
        f'</div>',
        unsafe_allow_html=True,
    )
