# -*- coding: utf-8 -*-
"""
Treasures & Lost Artifacts module for TerraScout AI.
Curated geographic data on lost treasures, famous archaeological finds,
sunken ships, crown jewels, museum masterpieces, art heists, ancient libraries,
gold rushes, pirate hideouts, and looted artifacts. 10 interactive map modes.
No API keys required -- all data is curated/embedded.
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

# ═══════════════════════════════════════════════════════════════════
# COLOR PALETTE  (matches TerraScout AI dark theme)
# ═══════════════════════════════════════════════════════════════════
BG_PRIMARY = "#0a0e1a"
BG_SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
ACCENT_CYAN = "#06b6d4"
ACCENT_AMBER = "#f59e0b"
ACCENT_VIOLET = "#8b5cf6"
ACCENT_EMERALD = "#10b981"
ACCENT_PINK = "#ec4899"
ACCENT_RED = "#ef4444"
ACCENT_ORANGE = "#f97316"
ACCENT_BLUE = "#3b82f6"
ACCENT_TEAL = "#14b8a6"
ACCENT_GOLD = "#eab308"

# ═══════════════════════════════════════════════════════════════════
# MAP MODE LABELS
# ═══════════════════════════════════════════════════════════════════
MAP_MODES = [
    "1. Lost Treasures",
    "2. Famous Archaeological Finds",
    "3. Sunken Treasure",
    "4. Crown Jewels & Royal Treasures",
    "5. Museum Masterpieces",
    "6. Famous Art Heists",
    "7. Ancient Libraries",
    "8. Gold Rushes",
    "9. Pirate Treasure Islands",
    "10. Looted Artifacts",
]

# ═══════════════════════════════════════════════════════════════════
# CURATED DATASETS  (each entry: name, lat, lon, description, extra fields)
# ═══════════════════════════════════════════════════════════════════

LOST_TREASURES = [
    {
        "name": "Amber Room",
        "lat": 59.7142, "lon": 30.3957,
        "location": "Catherine Palace, Pushkin, Russia",
        "era": "1701 (created); lost 1945",
        "estimated_value": "$500 million+",
        "status": "Lost / possibly destroyed",
        "description": "An ornate chamber made of amber panels backed with gold leaf and mirrors. "
                       "Created in 1701 for the King of Prussia, gifted to Peter the Great. "
                       "Dismantled by Nazi Germany in 1941 and shipped to Konigsberg. "
                       "Vanished in 1945 during Allied bombing. A reconstruction was completed in 2003.",
        "color": ACCENT_AMBER,
    },
    {
        "name": "Ark of the Covenant",
        "lat": 14.1208, "lon": 38.7468,
        "location": "Claimed: Axum, Ethiopia (Church of Our Lady Mary of Zion)",
        "era": "c. 1250 BCE (biblical)",
        "estimated_value": "Priceless / religious significance",
        "status": "Location debated",
        "description": "The sacred chest said to contain the stone tablets of the Ten Commandments. "
                       "According to Ethiopian tradition, it was brought to Axum by Menelik I. "
                       "Other theories place it in Jerusalem, Jordan, or southern Africa.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Holy Grail",
        "lat": 42.8486, "lon": -1.6076,
        "location": "Various claims: Valencia, Glastonbury, Rosslyn, Genoa",
        "era": "1st century CE (legendary)",
        "estimated_value": "Priceless / mythical",
        "status": "Legendary / never confirmed",
        "description": "The cup said to have been used by Jesus at the Last Supper. "
                       "Valencia Cathedral claims its Santo Caliz dates to the 1st century. "
                       "Legends connect it to the Knights Templar, King Arthur, and Rosslyn Chapel.",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Yamashita's Gold",
        "lat": 14.5995, "lon": 120.9842,
        "location": "Philippines (multiple alleged sites)",
        "era": "1942-1945 (WWII loot)",
        "estimated_value": "$100-300 billion (alleged)",
        "status": "Unconfirmed / treasure hunters active",
        "description": "Alleged treasure looted by Japanese forces across Southeast Asia during WWII, "
                       "reportedly hidden in caves and tunnels in the Philippines by General Yamashita. "
                       "Thousands of treasure hunters have searched for decades; some small finds reported.",
        "color": ACCENT_RED,
    },
    {
        "name": "Oak Island Money Pit",
        "lat": 44.5131, "lon": -64.2990,
        "location": "Oak Island, Nova Scotia, Canada",
        "era": "Discovered 1795",
        "estimated_value": "Unknown (speculation: millions to billions)",
        "status": "Active excavation (ongoing TV series)",
        "description": "A mysterious pit discovered in 1795 on a small island. Over 200 years of digging "
                       "have yielded flood tunnels, coconut fibers, a stone cipher, and various artifacts. "
                       "Theories attribute it to Captain Kidd, the Knights Templar, or Francis Bacon.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "El Dorado (Lake Guatavita)",
        "lat": 4.9741, "lon": -73.7747,
        "location": "Lake Guatavita, Colombia",
        "era": "Pre-Columbian / 16th century searches",
        "estimated_value": "Unknown (gold offerings in lake)",
        "status": "Partially recovered / protected site",
        "description": "The legendary city of gold actually originated from a Muisca chief who covered himself "
                       "in gold dust and made offerings in Lake Guatavita. Spanish conquistadors partially "
                       "drained the lake in the 1500s and found gold artifacts. The site is now protected.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Treasure of the Knights Templar",
        "lat": 48.8556, "lon": 2.3522,
        "location": "Paris (Temple), various European sites",
        "era": "Disbanded 1312",
        "estimated_value": "Immense (banking fortune of medieval Europe)",
        "status": "Lost / absorbed by crown & church",
        "description": "When King Philip IV of France arrested the Templars in 1307, their vast wealth "
                       "largely vanished. Theories place hidden vaults beneath the Paris Temple, "
                       "in Scotland, Portugal, or even the Americas.",
        "color": ACCENT_ORANGE,
    },
    {
        "name": "Flor de la Mar",
        "lat": 2.5000, "lon": 103.5000,
        "location": "Strait of Malacca, off Sumatra",
        "era": "Sank 1511",
        "estimated_value": "$2.6 billion+",
        "status": "Lost on seabed / disputed territory",
        "description": "A Portuguese carrack that sank in 1511 while carrying the treasure of the "
                       "Sultanate of Malacca -- gold, diamonds, rubies, and exotic goods. "
                       "It may be the richest shipwreck never found. Malaysia, Indonesia, and Portugal "
                       "all claim rights.",
        "color": ACCENT_TEAL,
    },
    {
        "name": "Menkaure's Basalt Sarcophagus",
        "lat": 29.9725, "lon": 31.1283,
        "location": "Lost at sea off Spain (was in Giza pyramid)",
        "era": "c. 2500 BCE; lost 1838",
        "estimated_value": "Priceless archaeological artifact",
        "status": "Lost at sea",
        "description": "The ornate basalt sarcophagus of Pharaoh Menkaure was found inside the Third Pyramid "
                       "at Giza. While being shipped to the British Museum in 1838, the cargo ship Beatrice "
                       "sank off the coast of Spain. It has never been recovered.",
        "color": ACCENT_BLUE,
    },
    {
        "name": "Treasure of Lima",
        "lat": 5.5500, "lon": -87.0500,
        "location": "Cocos Island, Costa Rica",
        "era": "Hidden 1820",
        "estimated_value": "$200-300 million",
        "status": "Never found",
        "description": "In 1820, as revolution swept Peru, Spanish officials entrusted the treasure of Lima "
                       "-- gold, silver, jeweled Virgin Marys -- to British Captain William Thompson. "
                       "He sailed away with it and allegedly buried it on Cocos Island. Over 300 expeditions "
                       "have searched; nothing substantial has been recovered.",
        "color": ACCENT_EMERALD,
    },
    {
        "name": "Faberge Eggs (Missing 8)",
        "lat": 59.9343, "lon": 30.3351,
        "location": "St. Petersburg origin; whereabouts unknown",
        "era": "1885-1917 (created)",
        "estimated_value": "$30-100 million (per egg)",
        "status": "8 of 50 Imperial eggs still missing",
        "description": "Of the 50 Imperial Faberge Eggs made for the Russian Tsars, 8 remain missing "
                       "after the 1917 Revolution. They were likely scattered during Bolshevik seizures. "
                       "In 2014, a scrap dealer almost melted one worth $33 million.",
        "color": ACCENT_PINK,
    },
    {
        "name": "Nazi Gold Train (Legend)",
        "lat": 50.8467, "lon": 16.2875,
        "location": "Walbrzych, Poland (Owl Mountains tunnels)",
        "era": "1945 (alleged)",
        "estimated_value": "Unknown (billions alleged)",
        "status": "Unconfirmed / searches found nothing definitive",
        "description": "Local legend holds that a Nazi armoured train carrying gold, gems, and weapons "
                       "was sealed inside a tunnel complex in Lower Silesia as WWII ended. "
                       "Despite ground-penetrating radar surveys and excavations in 2015-2016, no train "
                       "has been found, though the tunnel system (Project Riese) is real.",
        "color": ACCENT_RED,
    },
]

FAMOUS_ARCHAEOLOGICAL_FINDS = [
    {
        "name": "Tomb of Tutankhamun",
        "lat": 25.7402, "lon": 32.6014,
        "location": "Valley of the Kings, Luxor, Egypt",
        "year_discovered": 1922,
        "discoverer": "Howard Carter & Lord Carnarvon",
        "civilization": "Ancient Egypt (18th Dynasty)",
        "significance": "Nearly intact pharaoh's tomb with 5,398 items including the gold death mask",
        "description": "Discovered on November 4, 1922, this nearly intact royal tomb contained "
                       "the mummy of the boy-king and thousands of artifacts. The golden death mask "
                       "became the most iconic symbol of ancient Egypt.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Terracotta Army",
        "lat": 34.3848, "lon": 109.2734,
        "location": "Xi'an, Shaanxi, China",
        "year_discovered": 1974,
        "discoverer": "Local farmers digging a well",
        "civilization": "Qin Dynasty (c. 210 BCE)",
        "significance": "8,000+ life-sized clay soldiers guarding Emperor Qin Shi Huang's mausoleum",
        "description": "Accidentally discovered by farmers in 1974, the pits contain an estimated "
                       "8,000 soldiers, 130 chariots, 670 horses, and 150 cavalry figures. "
                       "Each soldier has unique facial features. Large areas remain unexcavated.",
        "color": ACCENT_ORANGE,
    },
    {
        "name": "Dead Sea Scrolls (Qumran)",
        "lat": 31.7414, "lon": 35.4593,
        "location": "Qumran Caves, West Bank",
        "year_discovered": 1947,
        "discoverer": "Bedouin shepherd Muhammad edh-Dhib",
        "civilization": "Second Temple Judaism (c. 250 BCE - 68 CE)",
        "significance": "Oldest known manuscripts of the Hebrew Bible and sectarian texts",
        "description": "A Bedouin shepherd found clay jars containing ancient scrolls in caves near "
                       "the Dead Sea. Over 900 manuscripts were recovered from 12 caves, including "
                       "the oldest known copies of every book of the Hebrew Bible (except Esther).",
        "color": ACCENT_AMBER,
    },
    {
        "name": "Rosetta Stone Discovery Site",
        "lat": 31.3960, "lon": 30.4171,
        "location": "Fort Julien, Rashid (Rosetta), Egypt",
        "year_discovered": 1799,
        "discoverer": "Captain Pierre-Francois Bouchard (Napoleon's army)",
        "civilization": "Ptolemaic Egypt (196 BCE)",
        "significance": "Key to deciphering Egyptian hieroglyphs -- trilingual decree",
        "description": "Found by a French soldier during Napoleon's Egyptian campaign. The stone "
                       "carries the same decree in hieroglyphic, Demotic, and Greek scripts. "
                       "Jean-Francois Champollion used it to crack the hieroglyphic code in 1822.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "Pompeii",
        "lat": 40.7509, "lon": 14.4869,
        "location": "Near Naples, Italy",
        "year_discovered": 1748,
        "discoverer": "Spanish engineer Rocque Joaquin de Alcubierre",
        "civilization": "Roman Empire (destroyed 79 CE)",
        "significance": "Complete Roman city preserved in volcanic ash with frescoes, mosaics, bodies",
        "description": "Buried by the eruption of Mount Vesuvius in 79 CE, Pompeii was rediscovered "
                       "in 1748. The ash preserved buildings, frescoes, everyday objects, and even "
                       "the shapes of victims. It remains the best window into daily Roman life.",
        "color": ACCENT_RED,
    },
    {
        "name": "Machu Picchu",
        "lat": -13.1631, "lon": -72.5450,
        "location": "Cusco Region, Peru",
        "year_discovered": 1911,
        "discoverer": "Hiram Bingham III (known to locals earlier)",
        "civilization": "Inca Empire (c. 1450 CE)",
        "significance": "Intact Inca citadel at 2,430m elevation -- royal estate of Pachacuti",
        "description": "Hiram Bingham was led to the mountain-top city by local farmers in 1911. "
                       "Built around 1450 as an estate for Inca emperor Pachacuti, it was abandoned "
                       "during the Spanish Conquest and remained unknown to outsiders for centuries.",
        "color": ACCENT_EMERALD,
    },
    {
        "name": "Troy (Hisarlik)",
        "lat": 39.9575, "lon": 26.2389,
        "location": "Canakkale, Turkey",
        "year_discovered": 1870,
        "discoverer": "Heinrich Schliemann",
        "civilization": "Bronze Age / Homeric Troy (c. 3000-1200 BCE)",
        "significance": "Proved Homer's Iliad had a historical basis -- 9 layers of ancient city",
        "description": "Heinrich Schliemann excavated the mound of Hisarlik beginning in 1870, "
                       "finding nine superimposed cities. He famously discovered 'Priam's Treasure' "
                       "(actually from an earlier layer). Modern archaeology confirms a destruction "
                       "layer consistent with the Trojan War era (~1200 BCE).",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Lascaux Cave Paintings",
        "lat": 45.0544, "lon": 1.1686,
        "location": "Dordogne, France",
        "year_discovered": 1940,
        "discoverer": "Four teenagers following their dog",
        "civilization": "Upper Paleolithic (c. 17,000 years ago)",
        "significance": "Stunning prehistoric cave art -- 600+ paintings of animals and symbols",
        "description": "Four teenagers stumbled into the cave in September 1940 while searching for "
                       "their dog. Inside they found over 600 paintings and 1,500 engravings of bulls, "
                       "horses, deer, and abstract signs -- some of the finest prehistoric art known.",
        "color": ACCENT_PINK,
    },
    {
        "name": "Gobekli Tepe",
        "lat": 37.2233, "lon": 38.9224,
        "location": "Sanliurfa Province, Turkey",
        "year_discovered": 1994,
        "discoverer": "Klaus Schmidt (German Archaeological Institute)",
        "civilization": "Pre-Pottery Neolithic (c. 9500 BCE)",
        "significance": "Oldest known monumental structure -- rewrote the timeline of civilization",
        "description": "Massive carved stone pillars arranged in circles, built by hunter-gatherers "
                       "around 9500 BCE -- 6,000 years before Stonehenge. The site challenged the belief "
                       "that agriculture preceded monumental architecture.",
        "color": ACCENT_TEAL,
    },
    {
        "name": "Sutton Hoo Ship Burial",
        "lat": 52.0889, "lon": 1.3375,
        "location": "Suffolk, England",
        "year_discovered": 1939,
        "discoverer": "Basil Brown (archaeologist) for landowner Edith Pretty",
        "civilization": "Anglo-Saxon (c. 625 CE)",
        "significance": "Richest Anglo-Saxon burial -- gold helmet, sword, Byzantine silver",
        "description": "A ship burial mound excavated in 1939 revealed an undisturbed chamber "
                       "containing a gold helmet, sword, shield, Byzantine silver, gold jewelry, "
                       "and coins. Likely the tomb of King Raedwald of East Anglia.",
        "color": ACCENT_BLUE,
    },
    {
        "name": "Staffordshire Hoard",
        "lat": 52.5860, "lon": -1.9190,
        "location": "Hammerwich, Staffordshire, England",
        "year_discovered": 2009,
        "discoverer": "Terry Herbert (metal detectorist)",
        "civilization": "Anglo-Saxon (7th-8th century CE)",
        "significance": "Largest hoard of Anglo-Saxon gold ever found -- 5.1 kg of gold",
        "description": "Found by a metal detectorist in a farmer's field, the hoard contained over "
                       "3,500 items of gold and silver, mostly military fittings -- sword pommels, "
                       "helmet crests, and cross-shaped fittings. Valued at 3.3 million GBP.",
        "color": ACCENT_AMBER,
    },
]

SUNKEN_TREASURE = [
    {
        "name": "Nuestra Senora de Atocha",
        "lat": 24.5147, "lon": -82.1862,
        "location": "Off Key West, Florida, USA",
        "year_sunk": 1622,
        "year_found": 1985,
        "cargo_value": "$450 million+",
        "finder": "Mel Fisher (after 16-year search)",
        "description": "A Spanish galleon that sank in a hurricane off Florida in 1622 carrying "
                       "gold, silver, emeralds, and indigo. Mel Fisher's famous 16-year search ended "
                       "in 1985 with the discovery of the 'mother lode' -- 40 tons of gold and silver.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "RMS Titanic Wreck Site",
        "lat": 41.7260, "lon": -49.9469,
        "location": "North Atlantic Ocean (3,800m depth)",
        "year_sunk": 1912,
        "year_found": 1985,
        "cargo_value": "Artifacts: priceless; gold disputed",
        "finder": "Robert Ballard & Jean-Louis Michel",
        "description": "The most famous shipwreck in history, found in 1985 at a depth of 3,800 meters. "
                       "Over 5,500 artifacts have been recovered. The wreck is legally protected "
                       "and is gradually being consumed by iron-eating bacteria.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "Antikythera Mechanism Wreck",
        "lat": 35.8825, "lon": 23.3108,
        "location": "Off Antikythera Island, Greece",
        "year_sunk": "c. 60 BCE",
        "year_found": 1901,
        "cargo_value": "Priceless (unique ancient computer + bronze statues)",
        "finder": "Greek sponge divers",
        "description": "A Roman-era shipwreck yielding the Antikythera Mechanism -- the world's oldest "
                       "known analog computer, used to predict eclipses and track the Olympics calendar. "
                       "Also contained stunning bronze and marble statues, glassware, and coins.",
        "color": ACCENT_TEAL,
    },
    {
        "name": "San Jose Galleon",
        "lat": 10.3910, "lon": -76.1860,
        "location": "Off Cartagena, Colombia",
        "year_sunk": 1708,
        "year_found": 2015,
        "cargo_value": "$4-17 billion (disputed)",
        "finder": "Colombian Navy / Woods Hole Oceanographic",
        "description": "A Spanish galleon sunk by the British in 1708, carrying gold, silver, and emeralds "
                       "from the New World. Found in 2015 at 600m depth. Colombia, Spain, and a US salvage "
                       "company all claim ownership. Possibly the most valuable shipwreck ever found.",
        "color": ACCENT_AMBER,
    },
    {
        "name": "SS Central America",
        "lat": 31.6167, "lon": -77.0833,
        "location": "Off South Carolina coast, USA",
        "year_sunk": 1857,
        "year_found": 1988,
        "cargo_value": "$100-150 million in gold",
        "finder": "Tommy Gregory Thompson",
        "description": "Known as the 'Ship of Gold,' she sank in a hurricane in 1857 carrying "
                       "21 tons of California Gold Rush gold. The sinking contributed to the "
                       "Panic of 1857 financial crisis. Recovered gold includes rare coins and ingots.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Vasa (Swedish Warship)",
        "lat": 59.3280, "lon": 18.0914,
        "location": "Stockholm Harbor, Sweden (now in Vasa Museum)",
        "year_sunk": 1628,
        "year_found": 1961,
        "cargo_value": "Priceless (intact 17th-century warship)",
        "finder": "Anders Franzen",
        "description": "The Vasa sank on its maiden voyage in 1628 after sailing just 1,300 meters. "
                       "Raised nearly intact in 1961 from Stockholm Harbor. Now displayed in the "
                       "Vasa Museum -- the world's best-preserved 17th-century ship.",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Flor de la Mar",
        "lat": 2.5000, "lon": 103.5000,
        "location": "Strait of Malacca, off Sumatra",
        "year_sunk": 1511,
        "year_found": "Not yet found",
        "cargo_value": "$2.6 billion+ (estimated)",
        "finder": "Still being searched for",
        "description": "The richest shipwreck never found. This Portuguese carrack was carrying "
                       "the entire treasury of the conquered Sultanate of Malacca when it sank "
                       "in a storm in the Strait of Malacca in 1511.",
        "color": ACCENT_RED,
    },
    {
        "name": "Mary Rose",
        "lat": 50.7634, "lon": -1.1118,
        "location": "The Solent, Hampshire, England (now in museum)",
        "year_sunk": 1545,
        "year_found": 1971,
        "cargo_value": "Priceless (19,000+ Tudor artifacts)",
        "finder": "Alexander McKee / Margaret Rule",
        "description": "Henry VIII's flagship sank during a battle with France in 1545. Raised in "
                       "1982 in a dramatic televised operation watched by 60 million viewers. "
                       "Over 19,000 artifacts provide an unmatched snapshot of Tudor England.",
        "color": ACCENT_EMERALD,
    },
    {
        "name": "Whydah Gally (Pirate Ship)",
        "lat": 41.8689, "lon": -69.9483,
        "location": "Off Cape Cod, Massachusetts, USA",
        "year_sunk": 1717,
        "year_found": 1984,
        "cargo_value": "$400 million+ in treasure",
        "finder": "Barry Clifford",
        "description": "The only verified pirate shipwreck ever found. Captained by 'Black Sam' Bellamy, "
                       "the Whydah carried loot from 53 captured ships when it sank in a storm. "
                       "The ship's bell, cannons, gold, and thousands of artifacts have been recovered.",
        "color": ACCENT_ORANGE,
    },
    {
        "name": "Merchant Royal",
        "lat": 50.0500, "lon": -5.6000,
        "location": "Off Land's End, Cornwall, England",
        "year_sunk": 1641,
        "year_found": "Not yet found",
        "cargo_value": "$1.5 billion+ (estimated)",
        "finder": "Still being searched for",
        "description": "An English merchant ship that sank in bad weather in 1641 while carrying "
                       "100,000 pounds of gold, 400 bars of Mexican silver, and nearly 500,000 "
                       "pieces of eight. Known as 'El Dorado of the Sea.'",
        "color": ACCENT_PINK,
    },
    {
        "name": "Nuestra Senora de las Mercedes",
        "lat": 36.3300, "lon": -6.8300,
        "location": "Off Cape Santa Maria, Portugal/Spain",
        "year_sunk": 1804,
        "year_found": 2007,
        "cargo_value": "$500 million (17 tons of silver coins)",
        "finder": "Odyssey Marine Exploration",
        "description": "A Spanish frigate sunk by British warships in 1804. Odyssey Marine recovered "
                       "17 tons of silver coins in 2007, but Spain sued successfully and the treasure "
                       "was returned. A landmark case in maritime salvage law.",
        "color": ACCENT_BLUE,
    },
]

CROWN_JEWELS = [
    {
        "name": "Crown Jewels of the United Kingdom",
        "lat": 51.5081, "lon": -0.0761,
        "location": "Tower of London, England",
        "highlight_item": "Imperial State Crown, Cullinan I (530ct diamond)",
        "estimated_value": "$4-6 billion",
        "pieces": "100+ objects, 23,578 gemstones",
        "description": "The British Crown Jewels include the Imperial State Crown (2,868 diamonds), "
                       "the Sovereign's Orb, and the Cullinan I diamond (530.2 carats). Guarded 24/7 "
                       "by the Yeomen Warders (Beefeaters) since 1303.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "Hope Diamond",
        "lat": 38.8913, "lon": -77.0260,
        "location": "Smithsonian National Museum of Natural History, Washington DC, USA",
        "highlight_item": "Hope Diamond (45.52ct deep blue diamond)",
        "estimated_value": "$200-350 million",
        "pieces": "Single stone (set in a pendant)",
        "description": "A 45.52-carat deep-blue diamond with a legendary curse. Possibly cut from the "
                       "French Blue diamond stolen during the French Revolution. Donated to the "
                       "Smithsonian in 1958 by Harry Winston, mailed via US Postal Service.",
        "color": ACCENT_BLUE,
    },
    {
        "name": "Koh-i-Noor Diamond",
        "lat": 51.5014, "lon": -0.1419,
        "location": "Tower of London (in Crown of Queen Mary), England",
        "highlight_item": "Koh-i-Noor (105.6ct diamond, 'Mountain of Light')",
        "estimated_value": "Priceless (claimed by India, Pakistan, Iran, Afghanistan)",
        "pieces": "Single stone, set in royal crown",
        "description": "One of the largest cut diamonds in history, with documented origins in India. "
                       "Passed through Mughal emperors, Persian conquerors, and Sikh rulers before "
                       "being taken by the British East India Company in 1849. Multiple countries "
                       "have formally requested its return.",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Imperial Crown of the Holy Roman Empire",
        "lat": 48.2039, "lon": 16.3812,
        "location": "Imperial Treasury (Schatzkammer), Hofburg Palace, Vienna, Austria",
        "highlight_item": "Imperial Crown (octagonal, gold, enamel, gems)",
        "estimated_value": "Priceless",
        "pieces": "Crown, orb, sceptre, Imperial Regalia",
        "description": "Created around 960 CE for Otto I, the octagonal gold crown is set with "
                       "144 gemstones and enamel panels depicting biblical kings. The Imperial Regalia "
                       "also includes the Holy Lance, said to contain a nail from the True Cross.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Iranian Crown Jewels",
        "lat": 35.6892, "lon": 51.3890,
        "location": "Central Bank of Iran Treasury, Tehran",
        "highlight_item": "Darya-ye Noor (186ct pink diamond), Naderi Throne",
        "estimated_value": "$12+ billion",
        "pieces": "Thousands -- thrones, crowns, tiaras, jeweled globes",
        "description": "One of the largest and most valuable jewel collections on Earth. Includes the "
                       "Darya-ye Noor (186ct pink diamond), Naderi Throne (26,733 gems), Kiani Crown, "
                       "and a jeweled globe made from 51,366 gems. Used as reserves backing Iran's currency.",
        "color": ACCENT_PINK,
    },
    {
        "name": "Russian Diamond Fund",
        "lat": 55.7520, "lon": 37.6175,
        "location": "Moscow Kremlin Armoury, Russia",
        "highlight_item": "Great Imperial Crown (4,936 diamonds), Orlov Diamond (189.62ct)",
        "estimated_value": "Priceless (state collection)",
        "pieces": "Crowns, scepters, the Orlov Diamond, Shah Diamond",
        "description": "The Diamond Fund contains Russia's most valuable gems. The Great Imperial Crown "
                       "(1762) holds 4,936 diamonds and a 398.72ct red spinel. The Orlov Diamond "
                       "(189.62ct) tops the Imperial Sceptre. Many pieces survived the Revolution "
                       "because the Bolsheviks recognized their financial value.",
        "color": ACCENT_RED,
    },
    {
        "name": "Bavarian Crown Jewels",
        "lat": 48.1413, "lon": 11.5788,
        "location": "Munich Residenz Treasury, Germany",
        "highlight_item": "Crown of Bavaria (1806), Wittelsbach Diamond",
        "estimated_value": "Several hundred million USD",
        "pieces": "Crown, orb, sceptre, sword of state, royal insignia",
        "description": "The Bavarian Crown Regalia were made in 1806 when Napoleon elevated Bavaria "
                       "to a kingdom. The Crown of Bavaria is set with diamonds, rubies, emeralds, "
                       "sapphires, and pearls. The original Wittelsbach Diamond (35.56ct, deep blue) "
                       "was sold and recut -- now called the Wittelsbach-Graff.",
        "color": ACCENT_AMBER,
    },
    {
        "name": "French Crown Jewels (Louvre)",
        "lat": 48.8611, "lon": 2.3364,
        "location": "Galerie d'Apollon, Louvre Museum, Paris, France",
        "highlight_item": "Regent Diamond (140.64ct), Louis XV Crown",
        "estimated_value": "Priceless (most sold in 1887 republican auctions)",
        "pieces": "Surviving pieces: Regent Diamond, some crowns, brooches",
        "description": "Most French Crown Jewels were sold in 1887 by the Third Republic. "
                       "The surviving pieces include the magnificent Regent Diamond (140.64ct), "
                       "considered the most perfect large white diamond, and several ceremonial crowns.",
        "color": ACCENT_EMERALD,
    },
    {
        "name": "Danish Crown Regalia",
        "lat": 55.6739, "lon": 12.5843,
        "location": "Rosenborg Castle, Copenhagen, Denmark",
        "highlight_item": "Christian IV's Crown (1596), Christian V's Crown (1670)",
        "estimated_value": "Priceless",
        "pieces": "Multiple crowns, orbs, swords, anointing vessels",
        "description": "Kept in the underground treasury of Rosenborg Castle since the 1830s. "
                       "Includes Christian IV's crown (1596) and the absolute monarchy crown of "
                       "Christian V (1670). The collection is one of the oldest intact European crown jewel sets.",
        "color": ACCENT_TEAL,
    },
    {
        "name": "Topkapi Palace Treasury",
        "lat": 41.0115, "lon": 28.9833,
        "location": "Topkapi Palace, Istanbul, Turkey",
        "highlight_item": "Topkapi Dagger, Spoonmaker's Diamond (86ct)",
        "estimated_value": "Priceless (Ottoman Empire collection)",
        "pieces": "Jeweled weapons, thrones, relics, robes, caftans",
        "description": "The Ottoman sultans' treasury holds the Topkapi Dagger (three enormous emeralds), "
                       "the Spoonmaker's Diamond (86ct pear-shaped), and holy relics including the "
                       "Prophet Muhammad's sword and cloak. The 1964 film 'Topkapi' is based on a "
                       "fictional heist of the dagger.",
        "color": ACCENT_ORANGE,
    },
]

MUSEUM_MASTERPIECES = [
    {
        "name": "Mona Lisa",
        "lat": 48.8606, "lon": 2.3376,
        "location": "Louvre Museum, Paris, France",
        "artist": "Leonardo da Vinci",
        "year_created": "c. 1503-1519",
        "origin": "Florence, Italy",
        "current_owner": "French Republic",
        "estimated_value": "$860 million+ (insured value in 1962: $100M, ~$1B today)",
        "description": "The world's most famous painting. Leonardo painted it over many years, "
                       "taking it to France where Francis I purchased it. Stolen in 1911 by an "
                       "Italian worker, recovered in 1913. Now behind bulletproof glass, "
                       "viewed by 10 million visitors annually.",
        "color": ACCENT_AMBER,
    },
    {
        "name": "Rosetta Stone",
        "lat": 51.5194, "lon": -0.1270,
        "location": "British Museum, London, England",
        "artist": "Egyptian priests / stone carvers",
        "year_created": "196 BCE",
        "origin": "Rashid (Rosetta), Egypt",
        "current_owner": "British Museum (contested by Egypt)",
        "estimated_value": "Priceless",
        "description": "Found by Napoleon's soldiers in 1799. The key to deciphering hieroglyphs. "
                       "Carried three scripts: hieroglyphic, Demotic, and Greek. "
                       "Egypt has repeatedly requested its return from the British Museum.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "Elgin (Parthenon) Marbles",
        "lat": 51.5194, "lon": -0.1270,
        "location": "British Museum, London, England",
        "artist": "Phidias and workshop",
        "year_created": "447-432 BCE",
        "origin": "Parthenon, Athens, Greece",
        "current_owner": "British Museum (contested by Greece)",
        "estimated_value": "Priceless",
        "description": "Lord Elgin removed roughly half the surviving sculptures of the Parthenon "
                       "between 1801-1812. Greece has demanded their return since independence in 1832. "
                       "The debate is the most famous repatriation case in the world.",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Bust of Nefertiti",
        "lat": 52.5211, "lon": 13.3969,
        "location": "Neues Museum, Berlin, Germany",
        "artist": "Thutmose (court sculptor)",
        "year_created": "c. 1345 BCE",
        "origin": "Amarna, Egypt",
        "current_owner": "Prussian Cultural Heritage Foundation (contested by Egypt)",
        "estimated_value": "Priceless",
        "description": "Found in 1912 by Ludwig Borchardt's expedition. One of the most copied works "
                       "of ancient art. Egypt has demanded its return, claiming it was taken through "
                       "a deceptive division of finds. Germany refuses, citing legal export.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Terracotta Army (Museum)",
        "lat": 34.3848, "lon": 109.2734,
        "location": "Emperor Qin Shi Huang's Mausoleum Museum, Xi'an, China",
        "artist": "Qin Dynasty imperial artisans",
        "year_created": "c. 210 BCE",
        "origin": "Xi'an, China (in situ museum)",
        "current_owner": "People's Republic of China",
        "estimated_value": "Priceless",
        "description": "Unlike most museum masterpieces, the Terracotta Army is displayed where it was "
                       "found. The on-site museum covers three excavation pits. Individual warriors "
                       "have toured museums worldwide, drawing record crowds.",
        "color": ACCENT_ORANGE,
    },
    {
        "name": "Venus de Milo",
        "lat": 48.8606, "lon": 2.3376,
        "location": "Louvre Museum, Paris, France",
        "artist": "Alexandros of Antioch (attributed)",
        "year_created": "c. 130-100 BCE",
        "origin": "Island of Milos, Greece",
        "current_owner": "French Republic",
        "estimated_value": "Priceless",
        "description": "Discovered on the island of Milos in 1820 by a Greek farmer. The French "
                       "purchased it and presented it to King Louis XVIII. The mystery of the "
                       "missing arms has inspired centuries of speculation.",
        "color": ACCENT_PINK,
    },
    {
        "name": "Tutankhamun's Death Mask",
        "lat": 30.0478, "lon": 31.2336,
        "location": "Grand Egyptian Museum, Giza, Egypt",
        "artist": "Ancient Egyptian goldsmiths (18th Dynasty)",
        "year_created": "c. 1323 BCE",
        "origin": "Valley of the Kings, Luxor, Egypt",
        "current_owner": "Arab Republic of Egypt",
        "estimated_value": "Priceless (gold alone worth ~$2 million)",
        "description": "The iconic 11 kg gold death mask is inlaid with lapis lazuli, obsidian, "
                       "quartz, and turquoise. It covered the head and shoulders of the mummy. "
                       "It is Egypt's most treasured artifact and a symbol of ancient Egypt worldwide.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "The Starry Night",
        "lat": 40.7614, "lon": -73.9776,
        "location": "Museum of Modern Art (MoMA), New York, USA",
        "artist": "Vincent van Gogh",
        "year_created": "1889",
        "origin": "Saint-Remy-de-Provence, France",
        "current_owner": "MoMA (acquired 1941)",
        "estimated_value": "$200+ million (estimated)",
        "description": "Painted in June 1889 from the window of Van Gogh's asylum room at "
                       "Saint-Paul-de-Mausole. The swirling night sky over the village has become "
                       "one of the most recognized images in Western culture.",
        "color": ACCENT_BLUE,
    },
    {
        "name": "Girl with a Pearl Earring",
        "lat": 52.0799, "lon": 4.3113,
        "location": "Mauritshuis, The Hague, Netherlands",
        "artist": "Johannes Vermeer",
        "year_created": "c. 1665",
        "origin": "Delft, Netherlands",
        "current_owner": "Royal Cabinet of Paintings, Mauritshuis",
        "estimated_value": "Priceless (national treasure)",
        "description": "Called the 'Mona Lisa of the North.' The identity of the girl is unknown. "
                       "The painting was bought at auction in 1881 for just 2 guilders (about $1). "
                       "It is now one of the Netherlands' most beloved works of art.",
        "color": ACCENT_EMERALD,
    },
    {
        "name": "Winged Victory of Samothrace",
        "lat": 48.8606, "lon": 2.3376,
        "location": "Louvre Museum, Paris, France (Daru staircase)",
        "artist": "Unknown (Rhodian sculptors, attributed)",
        "year_created": "c. 190 BCE",
        "origin": "Island of Samothrace, Greece",
        "current_owner": "French Republic",
        "estimated_value": "Priceless",
        "description": "A Hellenistic masterpiece depicting Nike, the goddess of victory, alighting on "
                       "the prow of a ship. Discovered in 1863 by Charles Champoiseau. Displayed at "
                       "the top of the Daru staircase in the Louvre, it is considered one of the "
                       "greatest sculptures ever created.",
        "color": ACCENT_TEAL,
    },
]

FAMOUS_ART_HEISTS = [
    {
        "name": "Isabella Stewart Gardner Museum Heist",
        "lat": 42.3382, "lon": -71.0990,
        "location": "Boston, Massachusetts, USA",
        "date": "March 18, 1990",
        "items_stolen": "13 works: Vermeer's 'The Concert', 3 Rembrandts, Manet, Degas, Flinck, Govaert",
        "estimated_value": "$500 million+",
        "status": "UNSOLVED -- $10 million reward still offered",
        "description": "Two men disguised as police officers talked their way into the museum at 1:24 AM. "
                       "In 81 minutes they stole 13 works including Vermeer's 'The Concert' (the most "
                       "valuable stolen painting in the world). Empty frames still hang as placeholders. "
                       "The FBI believes the Boston mob was involved, but no art has been recovered.",
        "color": ACCENT_RED,
    },
    {
        "name": "Mona Lisa Theft (1911)",
        "lat": 48.8606, "lon": 2.3376,
        "location": "Louvre Museum, Paris, France",
        "date": "August 21, 1911",
        "items_stolen": "Mona Lisa by Leonardo da Vinci",
        "estimated_value": "Priceless (estimated $1 billion+ today)",
        "status": "RECOVERED (1913) -- painting returned to Louvre",
        "description": "Italian handyman Vincenzo Peruggia hid in the Louvre overnight, lifted the "
                       "painting off the wall, hid it under his coat, and walked out. He kept it in "
                       "his apartment for 2 years. He was caught trying to sell it to a Florence dealer. "
                       "The theft actually made the Mona Lisa the world's most famous painting.",
        "color": ACCENT_AMBER,
    },
    {
        "name": "The Scream Thefts",
        "lat": 59.9139, "lon": 10.7522,
        "location": "National Gallery & Munch Museum, Oslo, Norway",
        "date": "1994 (National Gallery) & 2004 (Munch Museum)",
        "items_stolen": "Two versions of 'The Scream' by Edvard Munch",
        "estimated_value": "$120 million+ (each version)",
        "status": "BOTH RECOVERED",
        "description": "In 1994, thieves broke in through a window during the Winter Olympics opening "
                       "ceremony, leaving a note: 'Thanks for the poor security.' Recovered in 3 months. "
                       "In 2004, armed masked men took The Scream and Madonna from the Munch Museum "
                       "in broad daylight. Both recovered in 2006, slightly damaged.",
        "color": ACCENT_ORANGE,
    },
    {
        "name": "Kunsthal Rotterdam Heist",
        "lat": 51.9135, "lon": 4.4790,
        "location": "Kunsthal Museum, Rotterdam, Netherlands",
        "date": "October 16, 2012",
        "items_stolen": "7 paintings: Picasso, Monet, Matisse, Gauguin, Lucian Freud, Meyer de Haan",
        "estimated_value": "$100-200 million",
        "status": "DESTROYED -- suspect's mother burned them in her oven",
        "description": "Romanian thieves stole seven masterpieces in a late-night smash-and-grab. "
                       "When police closed in, suspect Radu Dogaru's mother Olga burned the paintings "
                       "in her wood-burning stove in rural Romania. Ash analysis confirmed traces "
                       "of paint pigments. One of art history's greatest tragedies.",
        "color": ACCENT_RED,
    },
    {
        "name": "Paris Museum of Modern Art Heist",
        "lat": 48.8638, "lon": 2.2982,
        "location": "Musee d'Art Moderne de la Ville de Paris, France",
        "date": "May 20, 2010",
        "items_stolen": "5 paintings: Picasso, Matisse, Braque, Modigliani, Leger",
        "estimated_value": "$123 million",
        "status": "UNSOLVED -- paintings never recovered (thief convicted)",
        "description": "A single masked thief broke a window, removed a padlock, and took five "
                       "masterpieces in a daring nighttime raid. He was identified as Vjeran Tomic, "
                       "a Serbian-born cat burglar. He claimed to have acted alone. The paintings "
                       "have never been recovered, and some believe they were destroyed or are in "
                       "a private collection.",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Saliera (Cellini Salt Cellar) Theft",
        "lat": 48.2039, "lon": 16.3812,
        "location": "Kunsthistorisches Museum, Vienna, Austria",
        "date": "May 11, 2003",
        "items_stolen": "Saliera by Benvenuto Cellini (gold salt cellar, 1543)",
        "estimated_value": "$60 million",
        "status": "RECOVERED (2006) -- buried in a forest",
        "description": "Robert Mang used scaffolding to climb into the museum and took the only "
                       "surviving gold work by Cellini. He tried to extort a ransom. Police found "
                       "the masterpiece buried in a lead box in a forest near the city. Mang "
                       "received 4 years in prison.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Van Gogh Museum Double Theft",
        "lat": 52.3584, "lon": 4.8810,
        "location": "Van Gogh Museum, Amsterdam, Netherlands",
        "date": "December 7, 2002",
        "items_stolen": "Two Van Gogh paintings: 'View of the Sea at Scheveningen' & 'Congregation Leaving the Reformed Church in Nuenen'",
        "estimated_value": "$30+ million",
        "status": "RECOVERED (2016) -- found by Italian anti-mafia police near Naples",
        "description": "Thieves broke in through the roof using a ladder. The two paintings "
                       "vanished for 14 years until Italian police found them during a raid on the "
                       "Camorra mafia near Naples. The paintings were hidden in a farmhouse, "
                       "wrapped in cotton, in remarkably good condition.",
        "color": ACCENT_EMERALD,
    },
    {
        "name": "Hatton Garden Safe Deposit Burglary",
        "lat": 51.5195, "lon": -0.1081,
        "location": "Hatton Garden Safe Deposit, London, England",
        "date": "April 2-5, 2015",
        "items_stolen": "Gold, diamonds, sapphires, jewelry from 73 safe deposit boxes",
        "estimated_value": "$200 million+ (estimate)",
        "status": "PARTIALLY RECOVERED -- elderly gang convicted",
        "description": "Over the Easter weekend, a gang of aging career criminals (average age 63) "
                       "drilled through a 50cm concrete vault wall using an industrial drill. They looted "
                       "73 boxes. Dubbed 'the diamond geezers,' most were caught. Two-thirds of the "
                       "loot was never recovered.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "Antwerp Diamond Heist",
        "lat": 51.2194, "lon": 4.4025,
        "location": "Antwerp Diamond Centre, Belgium",
        "date": "February 15-16, 2003",
        "items_stolen": "Diamonds, gold, jewelry, cash from 123 vault boxes",
        "estimated_value": "$100 million+",
        "status": "PARTIALLY RECOVERED -- Leonardo Notarbartolo convicted",
        "description": "Called the 'heist of the century.' Italian thief Leonardo Notarbartolo and his "
                       "team defeated 10 layers of security including infrared sensors, a 100-million "
                       "combination lock, seismic sensors, and a magnetic field. They were caught "
                       "through DNA on a half-eaten salami sandwich found at a highway rest stop.",
        "color": ACCENT_PINK,
    },
    {
        "name": "Stockholm National Museum Heist",
        "lat": 59.3283, "lon": 18.0783,
        "location": "Nationalmuseum, Stockholm, Sweden",
        "date": "December 22, 2000",
        "items_stolen": "Renoir's 'Conversation' and 'Young Parisian', Rembrandt's self-portrait",
        "estimated_value": "$36 million",
        "status": "RECOVERED -- all three paintings found",
        "description": "Three armed men held visitors at gunpoint while accomplices set off car bombs "
                       "and scattered road spikes to delay police. They escaped by speedboat. "
                       "The Renoirs were recovered in drug raids. The Rembrandt was found in 2005 "
                       "in a police sting at a Copenhagen hotel.",
        "color": ACCENT_BLUE,
    },
]

ANCIENT_LIBRARIES = [
    {
        "name": "Library of Alexandria",
        "lat": 31.2001, "lon": 29.9187,
        "location": "Alexandria, Egypt",
        "era": "c. 283 BCE - 48 BCE (major destruction) / final: 642 CE",
        "peak_holdings": "400,000-700,000 scrolls (estimated)",
        "fate": "Destroyed (multiple events: Caesar's fire 48 BCE, later destructions)",
        "surviving_texts": "None directly; some works known through later copies",
        "description": "The greatest library of antiquity, founded under Ptolemy I. It aimed to collect "
                       "all the world's knowledge. Julius Caesar accidentally burned part during the "
                       "siege of 48 BCE. Its final destruction may have occurred in 642 CE. "
                       "The Bibliotheca Alexandrina (2002) stands as a modern tribute.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Library of Pergamum",
        "lat": 39.1319, "lon": 27.1839,
        "location": "Pergamon (Bergama), Turkey",
        "era": "c. 197 BCE - 43 BCE",
        "peak_holdings": "200,000 scrolls (estimated)",
        "fate": "Contents allegedly given to Cleopatra by Mark Antony",
        "surviving_texts": "None directly; parchment ('pergamena') was invented here",
        "description": "Second only to Alexandria, the library of the Attalid kings rivaled Egypt's "
                       "collection. According to Plutarch, Mark Antony gave the entire library to "
                       "Cleopatra as a gift. Pergamum's contribution to civilization: parchment, "
                       "developed when Egypt restricted papyrus exports.",
        "color": ACCENT_AMBER,
    },
    {
        "name": "Nalanda University Library",
        "lat": 25.1358, "lon": 85.4432,
        "location": "Nalanda, Bihar, India",
        "era": "c. 427-1193 CE",
        "peak_holdings": "Millions of manuscripts (9 floors of library, 'Dharmaganja')",
        "fate": "Burned by Bakhtiyar Khilji's forces in 1193 CE",
        "surviving_texts": "Tibetan and Chinese translations preserve some texts",
        "description": "The world's first residential university, with a nine-story library called "
                       "Dharmaganja ('Mountain of Truth'). When burned in 1193, the library was said "
                       "to have smoldered for three months. It held texts on Buddhism, astronomy, "
                       "medicine, logic, and mathematics.",
        "color": ACCENT_ORANGE,
    },
    {
        "name": "House of Wisdom (Bayt al-Hikma)",
        "lat": 33.3152, "lon": 44.3661,
        "location": "Baghdad, Iraq",
        "era": "c. 830 - 1258 CE",
        "peak_holdings": "Hundreds of thousands of manuscripts",
        "fate": "Destroyed during the Mongol Siege of Baghdad (1258 CE)",
        "surviving_texts": "Many Arabic translations of Greek works survived elsewhere",
        "description": "The center of the Islamic Golden Age, where scholars translated Greek, "
                       "Persian, and Indian texts into Arabic, preserving works that would otherwise "
                       "be lost. The Mongol sack of Baghdad in 1258 reportedly turned the Tigris "
                       "black with ink from destroyed manuscripts.",
        "color": ACCENT_TEAL,
    },
    {
        "name": "Villa of the Papyri (Herculaneum)",
        "lat": 40.8060, "lon": 14.3478,
        "location": "Herculaneum, Italy (near Naples)",
        "era": "1st century BCE - 79 CE (buried by Vesuvius)",
        "peak_holdings": "1,800+ carbonized scrolls found",
        "fate": "Buried by Vesuvius eruption; scrolls survived carbonized",
        "surviving_texts": "AI/X-ray techniques are now reading the carbonized scrolls",
        "description": "The only surviving library from classical antiquity. Buried by Vesuvius in 79 CE, "
                       "the papyrus scrolls were carbonized but preserved. Modern AI and particle "
                       "accelerator scans are successfully reading them -- the Vesuvius Challenge "
                       "(2023) decoded passages of Philodemus on pleasure.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "Imperial Library of Constantinople",
        "lat": 41.0082, "lon": 28.9784,
        "location": "Constantinople (Istanbul), Turkey",
        "era": "c. 357 - 1453 CE",
        "peak_holdings": "120,000+ volumes at peak",
        "fate": "Partially destroyed multiple times; looted in 1204 (Crusaders) & 1453 (Ottomans)",
        "surviving_texts": "Many Byzantine manuscripts in Vatican, Venice, and European collections",
        "description": "Founded by Constantius II, it preserved Greek and Roman texts through the "
                       "medieval period. The Fourth Crusade (1204) saw Western crusaders looting "
                       "extensively. Many surviving manuscripts found their way to Italian Renaissance "
                       "scholars, helping spark the rebirth of classical learning.",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Library of Ashurbanipal",
        "lat": 36.3566, "lon": 43.1530,
        "location": "Nineveh (near Mosul), Iraq",
        "era": "c. 668-627 BCE",
        "peak_holdings": "30,000+ cuneiform tablets",
        "fate": "Buried when Nineveh fell in 612 BCE; tablets survived",
        "surviving_texts": "Most tablets in British Museum -- includes Epic of Gilgamesh",
        "description": "The Assyrian king's library is the oldest known systematically collected library. "
                       "When Nineveh was sacked in 612 BCE, the burning palace baked the clay tablets, "
                       "preserving them for 2,500 years. Contains the Epic of Gilgamesh -- the oldest "
                       "great work of literature.",
        "color": ACCENT_RED,
    },
    {
        "name": "Timbuktu Manuscripts",
        "lat": 16.7666, "lon": -3.0026,
        "location": "Timbuktu, Mali",
        "era": "13th-17th century CE (many still exist)",
        "peak_holdings": "700,000+ manuscripts in private collections",
        "fate": "Ongoing preservation -- many saved from Islamist destruction in 2012-2013",
        "surviving_texts": "Most survived thanks to heroic smuggling operation by local librarians",
        "description": "Timbuktu was a major center of Islamic learning from the 13th century. "
                       "Over 700,000 manuscripts on astronomy, medicine, law, and mathematics survive "
                       "in family collections. In 2012, when jihadists threatened to destroy them, "
                       "local librarians smuggled 350,000 manuscripts to safety in a heroic operation.",
        "color": ACCENT_EMERALD,
    },
    {
        "name": "Library of Celsus",
        "lat": 37.9395, "lon": 27.3417,
        "location": "Ephesus, Turkey",
        "era": "c. 117 CE - 262 CE",
        "peak_holdings": "12,000 scrolls",
        "fate": "Destroyed by Gothic invaders in 262 CE; facade survived earthquakes",
        "surviving_texts": "None directly; facade restored as archaeological monument",
        "description": "Built as a monumental tomb for the Roman senator Celsus, the library's "
                       "reconstructed two-story facade is one of the most photographed ancient ruins. "
                       "The architecture used optical illusions to make the building appear larger. "
                       "A secret tunnel connected it to a brothel across the street.",
        "color": ACCENT_PINK,
    },
    {
        "name": "Theological Library of Caesarea Maritima",
        "lat": 32.5000, "lon": 34.8900,
        "location": "Caesarea, Israel",
        "era": "c. 250-638 CE",
        "peak_holdings": "30,000+ texts (Origen's and Pamphilus' collections)",
        "fate": "Likely destroyed during Arab conquest (638 CE)",
        "surviving_texts": "Eusebius' works survive; he was the librarian",
        "description": "Founded by the scholar Origen and expanded by Pamphilus, this was the greatest "
                       "Christian library of late antiquity. The historian Eusebius used its resources "
                       "to write his foundational works on church history. Jerome also studied here.",
        "color": ACCENT_BLUE,
    },
]

GOLD_RUSHES = [
    {
        "name": "California Gold Rush",
        "lat": 38.7296, "lon": -120.8958,
        "location": "Sutter's Mill, Coloma, California, USA",
        "year_started": 1848,
        "peak_years": "1848-1855",
        "gold_produced": "750,000 lbs (est. $10+ billion today)",
        "prospectors": "~300,000 'Forty-Niners' arrived",
        "description": "James W. Marshall found gold at Sutter's Mill on January 24, 1848. "
                       "The resulting rush drew 300,000 people from around the world, grew San Francisco "
                       "from 200 to 36,000 residents, accelerated California statehood (1850), "
                       "and devastated the indigenous population.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Klondike Gold Rush",
        "lat": 63.8600, "lon": -138.8700,
        "location": "Dawson City, Yukon, Canada",
        "year_started": 1896,
        "peak_years": "1896-1899",
        "gold_produced": "Between 12-14 million troy ounces total",
        "prospectors": "~100,000 set out; ~30,000 arrived",
        "description": "Gold was discovered on Bonanza Creek in August 1896. The news reached the "
                       "outside world in 1897, triggering a stampede over the brutal Chilkoot Pass. "
                       "Of ~100,000 who set out, only ~30,000 reached Dawson City, and few struck it rich. "
                       "Jack London and Robert Service immortalized it in literature.",
        "color": ACCENT_AMBER,
    },
    {
        "name": "Witwatersrand Gold Rush",
        "lat": -26.1715, "lon": 28.0456,
        "location": "Johannesburg, South Africa",
        "year_started": 1886,
        "peak_years": "1886-present (still producing)",
        "gold_produced": "50,000+ tonnes -- 40% of all gold ever mined",
        "prospectors": "Transformed Johannesburg from nothing to a city",
        "description": "The world's largest gold deposit, discovered in 1886. The Witwatersrand Basin "
                       "has produced over 40% of all the gold ever mined on Earth. It created "
                       "Johannesburg, drove the Anglo-Boer Wars, and shaped South African history "
                       "including apartheid's economic foundations.",
        "color": ACCENT_ORANGE,
    },
    {
        "name": "Victorian Gold Rush (Ballarat)",
        "lat": -37.5622, "lon": 143.8503,
        "location": "Ballarat, Victoria, Australia",
        "year_started": 1851,
        "peak_years": "1851-1860s",
        "gold_produced": "Massive -- 'Welcome Stranger' nugget (2,316 troy oz) found 1869",
        "prospectors": "~500,000 immigrants arrived in Australia during the 1850s",
        "description": "The discovery of gold near Bathurst and Ballarat in 1851 tripled Australia's "
                       "population in a decade. The Eureka Stockade rebellion (1854) over mining licenses "
                       "became a defining moment in Australian democracy. The 'Welcome Stranger' "
                       "nugget (found 1869) remains the largest alluvial gold nugget ever found.",
        "color": ACCENT_EMERALD,
    },
    {
        "name": "Brazilian Gold Rush (Minas Gerais)",
        "lat": -20.3155, "lon": -43.8654,
        "location": "Ouro Preto, Minas Gerais, Brazil",
        "year_started": 1693,
        "peak_years": "1693-1785",
        "gold_produced": "1,000+ tonnes during colonial period",
        "prospectors": "400,000+ Portuguese settlers + enslaved Africans",
        "description": "The discovery of gold in Minas Gerais ('General Mines') in 1693 triggered "
                       "the first great gold rush of the modern era. Over 1,000 tonnes were extracted, "
                       "much by enslaved labor. The wealth created the baroque masterpiece city of "
                       "Ouro Preto ('Black Gold'). Portugal extracted enormous wealth through the 'Quinto' tax.",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Pike's Peak / Colorado Gold Rush",
        "lat": 39.7392, "lon": -104.9903,
        "location": "Denver / Central City area, Colorado, USA",
        "year_started": 1858,
        "peak_years": "1858-1861",
        "gold_produced": "Millions of ounces (led to major hard-rock mining)",
        "prospectors": "~100,000 'Fifty-Niners'",
        "description": "Gold discoveries along the South Platte River triggered the 'Pike's Peak or Bust' "
                       "rush. While placer gold ran out quickly, hard-rock mining at Central City and "
                       "Leadville became enormously productive. The rush founded Denver and led to "
                       "Colorado's statehood in 1876.",
        "color": ACCENT_RED,
    },
    {
        "name": "Otago Gold Rush",
        "lat": -45.0312, "lon": 169.1381,
        "location": "Gabriel's Gully, Central Otago, New Zealand",
        "year_started": 1861,
        "peak_years": "1861-1864",
        "gold_produced": "Significant -- transformed South Island economy",
        "prospectors": "~18,000 miners (mostly from Australian goldfields)",
        "description": "Gabriel Read found gold in a gully in Otago in 1861, sparking New Zealand's "
                       "largest gold rush. Dunedin briefly became New Zealand's largest and wealthiest "
                       "city. Chinese miners arrived in significant numbers, forming one of NZ's "
                       "first Asian communities.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "Cariboo Gold Rush",
        "lat": 52.9739, "lon": -122.4937,
        "location": "Barkerville, British Columbia, Canada",
        "year_started": 1861,
        "peak_years": "1861-1867",
        "gold_produced": "Over $50 million in 1860s dollars",
        "prospectors": "~30,000 miners traveled the Cariboo Wagon Road",
        "description": "Rich gold deposits drew miners north from the depleted Fraser River fields. "
                       "Barkerville became the largest city west of Chicago and north of San Francisco. "
                       "The rush prompted construction of the Cariboo Wagon Road and was a key factor "
                       "in British Columbia joining Canadian Confederation (1871).",
        "color": ACCENT_TEAL,
    },
    {
        "name": "Nome Gold Rush (Alaska)",
        "lat": 64.5011, "lon": -165.4064,
        "location": "Nome, Alaska, USA",
        "year_started": 1898,
        "peak_years": "1899-1909",
        "gold_produced": "$75+ million in early 1900s dollars",
        "prospectors": "~20,000 people -- tent city on the beach",
        "description": "Gold was discovered on the beaches of Nome in 1898. Remarkably, gold could be "
                       "scooped from the sand with no equipment. A tent city of 20,000 sprang up. "
                       "The 'Lucky Swedes' (Three Lucky Swedes) were among the first to stake claims "
                       "along Anvil Creek.",
        "color": ACCENT_BLUE,
    },
    {
        "name": "Kalgoorlie Gold Rush",
        "lat": -30.7490, "lon": 121.4660,
        "location": "Kalgoorlie-Boulder, Western Australia",
        "year_started": 1893,
        "peak_years": "1893-1900s (Super Pit still operates)",
        "gold_produced": "50+ million ounces total -- still producing",
        "prospectors": "Thousands; harsh desert conditions",
        "description": "Paddy Hannan found gold in 1893, sparking a rush into the arid Western "
                       "Australian desert. The Super Pit (Fimiston Open Pit) is still one of the "
                       "world's largest open-pit gold mines, visible from space. A water pipeline "
                       "from Perth (530 km) was built to sustain the goldfields.",
        "color": ACCENT_PINK,
    },
]

PIRATE_TREASURE_ISLANDS = [
    {
        "name": "Port Royal, Jamaica",
        "lat": 17.9350, "lon": -76.8410,
        "location": "Kingston Harbour, Jamaica",
        "era": "1650s-1692 (destroyed by earthquake)",
        "notable_pirates": "Henry Morgan, Calico Jack Rackham",
        "description": "Called 'the wickedest city on Earth,' Port Royal was the Caribbean pirate capital "
                       "in the 17th century. Captain Henry Morgan used it as a base for raiding Spanish "
                       "colonies. In 1692, a massive earthquake sank two-thirds of the city into the sea. "
                       "Underwater archaeology continues to reveal sunken taverns and warehouses.",
        "color": ACCENT_RED,
    },
    {
        "name": "Nassau, Bahamas (Republic of Pirates)",
        "lat": 25.0480, "lon": -77.3554,
        "location": "Nassau, New Providence, Bahamas",
        "era": "1706-1718 (pirate republic)",
        "notable_pirates": "Blackbeard, Charles Vane, Anne Bonny, Mary Read, Jack Rackham, Benjamin Hornigold",
        "description": "Nassau was a self-governing pirate republic from 1706-1718. The harbor could "
                       "hold hundreds of ships but was too shallow for warships. Blackbeard, Charles Vane, "
                       "and Anne Bonny all operated from here. Ended when Woodes Rogers became governor "
                       "in 1718 with orders to suppress piracy.",
        "color": ACCENT_AMBER,
    },
    {
        "name": "Tortuga (Ile de la Tortue)",
        "lat": 20.0500, "lon": -72.7833,
        "location": "Off northern Haiti",
        "era": "1630s-1680s",
        "notable_pirates": "Francois l'Olonnais, Pierre Le Grand, buccaneers",
        "description": "A mountainous island off Haiti that became the headquarters of the buccaneers -- "
                       "originally hunters who turned to piracy. The island's fortified harbor hosted "
                       "French, English, and Dutch pirates who raided Spanish shipping. "
                       "The name means 'turtle island' in French.",
        "color": ACCENT_EMERALD,
    },
    {
        "name": "Ile Sainte-Marie (Nosy Boraha), Madagascar",
        "lat": -16.8500, "lon": 49.9167,
        "location": "Off eastern coast of Madagascar",
        "era": "1690s-1720s",
        "notable_pirates": "Captain Kidd, Adam Baldridge, Thomas Tew, Abraham Samuel",
        "description": "The main pirate base in the Indian Ocean. Captain Kidd anchored here. "
                       "Adam Baldridge established a trading post that supplied pirates and bought "
                       "their loot. The pirates' cemetery still exists. Some pirates married "
                       "Malagasy women and founded mixed communities.",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Captain Kidd's Gardiner's Island Cache",
        "lat": 41.1000, "lon": -72.1000,
        "location": "Gardiner's Island, New York, USA",
        "era": "1699",
        "notable_pirates": "Captain William Kidd",
        "description": "Captain Kidd buried treasure on Gardiner's Island in 1699 -- one of the very few "
                       "documented cases of pirates actually burying treasure. He left it with John "
                       "Gardiner as a bargaining chip. The treasure was recovered by authorities and "
                       "used as evidence in Kidd's trial. He was hanged in 1701.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Blackbeard's Ocracoke Island Base",
        "lat": 35.1146, "lon": -75.9810,
        "location": "Ocracoke Island, North Carolina, USA",
        "era": "1717-1718",
        "notable_pirates": "Edward Teach (Blackbeard)",
        "description": "Blackbeard used the shallow inlets of Ocracoke Island as a base, where "
                       "larger naval vessels couldn't follow. He was killed here in a bloody battle "
                       "on November 22, 1718, when Lt. Robert Maynard's crew ambushed him. "
                       "Blackbeard received five pistol shots and twenty sword cuts before dying.",
        "color": ACCENT_ORANGE,
    },
    {
        "name": "Isla de la Juventud (Treasure Island)",
        "lat": 21.7050, "lon": -82.8220,
        "location": "South of Cuba",
        "era": "16th-18th century",
        "notable_pirates": "Francis Drake, Henry Morgan, various buccaneers",
        "description": "Long believed to be Robert Louis Stevenson's inspiration for 'Treasure Island.' "
                       "Its caves and hidden bays made it ideal for pirates hiding from Spanish patrols. "
                       "Dozens of documented visits by pirates including Sir Francis Drake. "
                       "Several treasure hunts have been conducted on the island.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "Cocos Island, Costa Rica",
        "lat": 5.5500, "lon": -87.0500,
        "location": "Pacific Ocean, 550 km off Costa Rica",
        "era": "17th-19th century",
        "notable_pirates": "Benito 'Bloody Sword' Bonito, Captain Thompson (Lima treasure)",
        "description": "The real-life 'Treasure Island' -- said to hold three separate pirate treasures "
                       "including the Treasure of Lima. Over 300 treasure-hunting expeditions have "
                       "searched the island. Now a UNESCO World Heritage Site and national park. "
                       "Said to have inspired both Stevenson and Michael Crichton (Jurassic Park).",
        "color": ACCENT_TEAL,
    },
    {
        "name": "Barataria Bay (Jean Lafitte's Base)",
        "lat": 29.3250, "lon": -89.9536,
        "location": "Louisiana, USA (south of New Orleans)",
        "era": "1805-1815",
        "notable_pirates": "Jean Lafitte & Pierre Lafitte",
        "description": "Jean Lafitte ran a smuggling and piracy operation from the swamps and barrier "
                       "islands of Barataria Bay. He commanded over 1,000 men and a fleet of ships. "
                       "Despite being a pirate, he aided Andrew Jackson at the Battle of New Orleans "
                       "(1815) and was pardoned by President Madison.",
        "color": ACCENT_PINK,
    },
    {
        "name": "Libertalia (Legendary Pirate Utopia)",
        "lat": -15.7167, "lon": 46.3167,
        "location": "Claimed: northern Madagascar (possibly Diego Suarez Bay)",
        "era": "Late 17th century (legendary)",
        "notable_pirates": "Captain Misson, Thomas Tew (possibly fictional)",
        "description": "A legendary pirate colony described in Captain Charles Johnson's 'General History "
                       "of the Pyrates' (1724). Supposedly founded by Captain Misson and a defrocked "
                       "Italian priest, it was said to be a democratic commune where freed slaves and "
                       "pirates lived as equals. Most historians believe it is fictional, but it "
                       "influenced later political thought.",
        "color": ACCENT_BLUE,
    },
]

LOOTED_ARTIFACTS = [
    {
        "name": "Benin Bronzes",
        "lat": 6.3350, "lon": 5.6270,
        "location": "Origin: Benin City, Nigeria; scattered in 160+ museums worldwide",
        "year_looted": 1897,
        "looted_by": "British Punitive Expedition",
        "current_holders": "British Museum, Ethnological Museum Berlin, Met, Pitt Rivers, many others",
        "items_count": "3,000-5,000+ brass/bronze plaques, heads, figures",
        "repatriation_status": "Active -- Germany returned 1,130 in 2022; UK museums returning pieces",
        "description": "British soldiers looted the Royal Palace of Benin in 1897 during a punitive "
                       "expedition. Thousands of intricate brass and bronze works were seized and sold "
                       "to museums worldwide. Nigeria has campaigned for decades for their return. "
                       "Germany returned 1,130 pieces in 2022; the Horniman Museum and others followed.",
        "color": ACCENT_AMBER,
    },
    {
        "name": "Parthenon (Elgin) Marbles",
        "lat": 37.9715, "lon": 23.7267,
        "location": "Origin: Parthenon, Athens; now: British Museum, London",
        "year_looted": "1801-1812",
        "looted_by": "Lord Elgin (British Ambassador to Ottoman Empire)",
        "current_holders": "British Museum (London), Acropolis Museum (Athens has the rest)",
        "items_count": "75 meters of frieze, 15 metopes, 17 pedimental figures",
        "repatriation_status": "Greece demands return since 1832; UK refuses; UNESCO mediates",
        "description": "Lord Elgin removed roughly half the surviving sculptures from the Parthenon "
                       "while Greece was under Ottoman rule. Greece has demanded their return since "
                       "independence. The British Museum argues they are legally acquired and better "
                       "preserved in London. The Acropolis Museum was built partly to house them.",
        "color": ACCENT_CYAN,
    },
    {
        "name": "Bust of Nefertiti",
        "lat": 27.6500, "lon": 30.8960,
        "location": "Origin: Amarna, Egypt; now: Neues Museum, Berlin",
        "year_looted": "1912 (disputed export)",
        "looted_by": "Ludwig Borchardt (German Archaeological Institute)",
        "current_holders": "Prussian Cultural Heritage Foundation, Berlin",
        "items_count": "1 painted limestone bust",
        "repatriation_status": "Egypt demands return; Germany refuses citing legal division of finds",
        "description": "Egypt claims Borchardt deliberately downplayed the bust's importance during the "
                       "division of finds with Egyptian authorities, possibly showing only a poor "
                       "photograph. Germany maintains the division was lawful. Zahi Hawass repeatedly "
                       "demanded its return. It remains one of Berlin's top attractions.",
        "color": ACCENT_GOLD,
    },
    {
        "name": "Ishtar Gate & Processional Way",
        "lat": 32.5422, "lon": 44.4211,
        "location": "Origin: Babylon, Iraq; now: Pergamon Museum, Berlin",
        "year_looted": "1902-1914 (excavation export)",
        "looted_by": "Robert Koldewey (German excavation)",
        "current_holders": "Pergamon Museum, Berlin",
        "items_count": "Reconstructed gate (15m tall) plus processional way panels",
        "repatriation_status": "Iraq has requested return; complicated by instability",
        "description": "German archaeologist Robert Koldewey excavated the Ishtar Gate of Nebuchadnezzar II "
                       "and shipped the glazed brick panels to Berlin, where the gate was reconstructed. "
                       "Iraq has requested its return, but political instability has complicated discussions. "
                       "A partial replica was built in Babylon.",
        "color": ACCENT_BLUE,
    },
    {
        "name": "Koh-i-Noor Diamond",
        "lat": 30.9010, "lon": 75.8573,
        "location": "Origin: India (Golconda mines); now: Tower of London",
        "year_looted": "1849 (Treaty of Lahore)",
        "looted_by": "British East India Company (from 10-year-old Maharaja Duleep Singh)",
        "current_holders": "British Crown (set in Crown of Queen Mary)",
        "items_count": "1 diamond (105.6 carats)",
        "repatriation_status": "Claimed by India, Pakistan, Iran, Afghanistan, and the Taliban",
        "description": "Taken from the young Maharaja Duleep Singh as a condition of the Treaty of "
                       "Lahore following the Anglo-Sikh Wars. India, Pakistan, Iran, and Afghanistan "
                       "have all formally demanded its return. The British government has refused, "
                       "calling it a 'gift.' It was last worn by Queen Elizabeth at the 1953 coronation.",
        "color": ACCENT_VIOLET,
    },
    {
        "name": "Rosetta Stone",
        "lat": 31.3960, "lon": 30.4171,
        "location": "Origin: Rosetta, Egypt; now: British Museum, London",
        "year_looted": "1801 (seized from France after Battle of Alexandria)",
        "looted_by": "British forces (originally found by Napoleon's army 1799)",
        "current_holders": "British Museum, London",
        "items_count": "1 granodiorite stele",
        "repatriation_status": "Egypt has demanded return; British Museum refuses",
        "description": "Found by French soldiers in 1799, seized by the British in 1801 under the "
                       "Treaty of Alexandria. The key to deciphering hieroglyphs, it has been in the "
                       "British Museum since 1802. Egypt's former antiquities minister Zahi Hawass "
                       "formally demanded its return. It is the museum's most visited object.",
        "color": ACCENT_TEAL,
    },
    {
        "name": "Ethiopian Tabots & Maqdala Treasures",
        "lat": 11.3470, "lon": 39.5340,
        "location": "Origin: Maqdala Fortress, Ethiopia; now: V&A, British Museum, others",
        "year_looted": 1868,
        "looted_by": "British Expedition to Abyssinia (Gen. Napier)",
        "current_holders": "Victoria & Albert Museum, British Museum, Royal Library Windsor, others",
        "items_count": "Hundreds -- manuscripts, crosses, tabots, crowns, religious items",
        "repatriation_status": "Ethiopia has requested returns since 1869; some items returned 2002",
        "description": "After defeating Emperor Tewodros II at the Battle of Maqdala in 1868, British "
                       "forces looted the fortress, carrying away treasures on 15 elephants and 200 mules. "
                       "Items included sacred tabots (replicas of the Ark), illuminated manuscripts, "
                       "gold crowns, and royal regalia. Some items were returned in 2002.",
        "color": ACCENT_ORANGE,
    },
    {
        "name": "Priam's Treasure",
        "lat": 39.9575, "lon": 26.2389,
        "location": "Origin: Troy (Hisarlik), Turkey; now: Pushkin Museum, Moscow",
        "year_looted": "1873 (excavation) / 1945 (Soviet seizure)",
        "looted_by": "Heinrich Schliemann (1873); Soviet Army from Berlin (1945)",
        "current_holders": "Pushkin Museum, Moscow (seized from Berlin Museum 1945)",
        "items_count": "Gold diadems, earrings, vessels, 8,750 gold pieces",
        "repatriation_status": "Claimed by Turkey, Germany, and Greece; Russia refuses return",
        "description": "Schliemann smuggled 'Priam's Treasure' from Troy to Berlin in 1873. Turkey has "
                       "demanded its return ever since. In 1945, Soviet troops seized it from a Berlin "
                       "bunker. Russia kept it secret until 1993. Turkey, Germany, and Greece all claim "
                       "it. Russia considers it war reparations.",
        "color": ACCENT_RED,
    },
    {
        "name": "Moai (Easter Island Heads) in Museums",
        "lat": -27.1127, "lon": -109.3497,
        "location": "Origin: Rapa Nui (Easter Island), Chile; dispersed to museums",
        "year_looted": "1868-1886 (various)",
        "looted_by": "British Navy (HMS Topaze), various expeditions",
        "current_holders": "British Museum (Hoa Hakananai'a), Smithsonian, Louvre, others",
        "items_count": "~12 moai in museums worldwide",
        "repatriation_status": "Rapa Nui community demands return; British Museum loaned replica",
        "description": "Several moai statues were taken from Easter Island by various expeditions. "
                       "The most famous, Hoa Hakananai'a ('Lost Friend'), was taken by the British "
                       "Navy in 1868. The Rapa Nui community has repeatedly requested its return, "
                       "saying it holds deep spiritual significance. The British Museum offered a replica.",
        "color": ACCENT_PINK,
    },
    {
        "name": "Lydian Hoard (Karun Treasure)",
        "lat": 38.5833, "lon": 28.5167,
        "location": "Origin: Usak, Turkey; was at Metropolitan Museum, New York",
        "year_looted": "1966 (grave robbers); purchased by Met 1966-1970",
        "looted_by": "Local tomb raiders; purchased by Metropolitan Museum",
        "current_holders": "Usak Museum, Turkey (returned 1993 after lawsuit)",
        "items_count": "363 Lydian artifacts: gold, silver, bronze, wall paintings",
        "repatriation_status": "RETURNED to Turkey in 1993 after landmark lawsuit",
        "description": "A major repatriation success story. Tomb robbers looted ancient Lydian "
                       "royal tombs in western Turkey in the 1960s. The Met purchased 363 artifacts. "
                       "Turkey sued in 1987, and the Met returned the hoard in 1993, admitting it knew "
                       "the objects were illicitly obtained. Set a precedent for future repatriation cases.",
        "color": ACCENT_EMERALD,
    },
]


# ═══════════════════════════════════════════════════════════════════
# HELPER: Build a Folium map from a list of entries
# ═══════════════════════════════════════════════════════════════════
def _build_folium_map(items: list, popup_fields: list[tuple[str, str]],
                      zoom_start: int = 2, center: tuple = (20.0, 0.0),
                      icon_name: str = "gem", icon_prefix: str = "fa") -> folium.Map:
    """
    Build a dark-themed Folium map with markers for each item.

    Parameters
    ----------
    items : list of dicts
        Each dict must have 'name', 'lat', 'lon', 'color', 'description'.
    popup_fields : list of (field_key, display_label) tuples for popup content.
    zoom_start : int
    center : tuple (lat, lon)
    icon_name : str   (FontAwesome icon name)
    icon_prefix : str ("fa" for FontAwesome)
    """
    m = folium.Map(
        location=center,
        zoom_start=zoom_start,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    for item in items:
        lat = item.get("lat")
        lon = item.get("lon")
        if lat is None or lon is None:
            continue

        color = item.get("color", ACCENT_CYAN)
        name = escape(str(item.get("name", "Unknown")))

        # Build popup HTML
        popup_lines = [
            f'<div style="min-width:260px;max-width:340px;font-family:sans-serif;">'
            f'<h4 style="margin:0 0 6px 0;color:{color};">{name}</h4>'
        ]
        for field_key, label in popup_fields:
            val = item.get(field_key, "")
            if val:
                popup_lines.append(
                    f'<b>{escape(label)}:</b> {escape(str(val))}<br>'
                )
        desc = item.get("description", "")
        if desc:
            popup_lines.append(
                f'<p style="margin:6px 0 0 0;font-size:12px;color:#ccc;">{escape(desc)}</p>'
            )
        popup_lines.append('</div>')

        popup_html = "".join(popup_lines)

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=360),
            tooltip=name,
            icon=folium.Icon(color="black", icon_color=color, icon=icon_name, prefix=icon_prefix),
        ).add_to(m)

    # Fit bounds if multiple items
    if len(items) > 1:
        coords = [(it["lat"], it["lon"]) for it in items if it.get("lat") and it.get("lon")]
        if coords:
            m.fit_bounds(coords, padding=(30, 30))

    return m


# ═══════════════════════════════════════════════════════════════════
# HELPER: Build a DataFrame from items
# ═══════════════════════════════════════════════════════════════════
def _build_dataframe(items: list, columns: list[tuple[str, str]]) -> pd.DataFrame:
    """
    Build a DataFrame from items.

    Parameters
    ----------
    items : list of dicts
    columns : list of (field_key, display_name) tuples
    """
    rows = []
    for item in items:
        row = {}
        for field_key, display_name in columns:
            row[display_name] = item.get(field_key, "")
        rows.append(row)
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════
# HELPER: CSV download button
# ═══════════════════════════════════════════════════════════════════
def _csv_download(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    """Offer a CSV download button."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        label=label,
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
    )


# ═══════════════════════════════════════════════════════════════════
# HELPER: Render a single mode section
# ═══════════════════════════════════════════════════════════════════
def _render_mode(title: str, description: str, stats: dict,
                 items: list, popup_fields: list[tuple[str, str]],
                 table_columns: list[tuple[str, str]],
                 csv_filename: str, icon_name: str = "gem",
                 zoom_start: int = 2, center: tuple = (20.0, 0.0)):
    """
    Render a complete mode section: description, stats, map, table, download.
    """
    # Description
    st.markdown(f"**{escape(title)}**")
    st.markdown(description)

    # Stats row
    stat_cols = st.columns(len(stats))
    for i, (label, value) in enumerate(stats.items()):
        with stat_cols[i]:
            st.metric(label=label, value=value)

    # Map
    st.markdown("---")
    st.markdown(f"**Interactive Map** ({len(items)} locations)")
    m = _build_folium_map(
        items, popup_fields,
        zoom_start=zoom_start, center=center,
        icon_name=icon_name,
    )
    components.html(m._repr_html_(), height=500)

    # Data table
    st.markdown("---")
    st.markdown("**Data Table**")
    df = _build_dataframe(items, table_columns)
    st.dataframe(df, width="stretch")

    # Download
    _csv_download(df, csv_filename, label=f"Download {title} CSV")


# ═══════════════════════════════════════════════════════════════════
# MODE RENDERERS
# ═══════════════════════════════════════════════════════════════════

def _mode_lost_treasures():
    _render_mode(
        title="Lost Treasures of the World",
        description=(
            "Legendary treasures that have captivated treasure hunters for centuries. "
            "From the glittering Amber Room to the fabled gold of Yamashita, these are "
            "the most sought-after lost fortunes on Earth. Some may be myths, others are "
            "very real -- and still waiting to be found."
        ),
        stats={
            "Treasures Mapped": str(len(LOST_TREASURES)),
            "Total Est. Value": "$800B+ (alleged)",
            "Still Missing": str(sum(1 for t in LOST_TREASURES if "Lost" in t.get("status", "") or "Never" in t.get("status", "") or "Unconfirmed" in t.get("status", ""))),
            "Centuries Spanned": "15th - 20th",
        },
        items=LOST_TREASURES,
        popup_fields=[
            ("location", "Location"),
            ("era", "Era"),
            ("estimated_value", "Estimated Value"),
            ("status", "Status"),
        ],
        table_columns=[
            ("name", "Treasure"),
            ("location", "Location"),
            ("era", "Era"),
            ("estimated_value", "Estimated Value"),
            ("status", "Status"),
        ],
        csv_filename="lost_treasures.csv",
        icon_name="gem",
    )


def _mode_archaeological_finds():
    _render_mode(
        title="Famous Archaeological Finds",
        description=(
            "The greatest archaeological discoveries in history -- moments that rewrote "
            "our understanding of the ancient world. From the golden mask of Tutankhamun "
            "to the enigmatic circles of Gobekli Tepe, each find opened a window into "
            "civilizations long gone."
        ),
        stats={
            "Discoveries Mapped": str(len(FAMOUS_ARCHAEOLOGICAL_FINDS)),
            "Oldest Find": "c. 9500 BCE (Gobekli Tepe)",
            "Most Recent": "2009 (Staffordshire Hoard)",
            "Civilizations Represented": "11+",
        },
        items=FAMOUS_ARCHAEOLOGICAL_FINDS,
        popup_fields=[
            ("location", "Location"),
            ("year_discovered", "Year Discovered"),
            ("discoverer", "Discoverer"),
            ("civilization", "Civilization"),
            ("significance", "Significance"),
        ],
        table_columns=[
            ("name", "Discovery"),
            ("location", "Location"),
            ("year_discovered", "Year"),
            ("discoverer", "Discoverer"),
            ("civilization", "Civilization"),
            ("significance", "Significance"),
        ],
        csv_filename="archaeological_finds.csv",
        icon_name="university",
    )


def _mode_sunken_treasure():
    _render_mode(
        title="Sunken Treasure Ships",
        description=(
            "The ocean floor holds more treasure than all the world's museums combined. "
            "From Spanish galleons laden with New World gold to the Titanic's opulent "
            "artifacts, these shipwrecks have drawn salvors, archaeologists, and dreamers "
            "for centuries. Some remain the subject of multi-billion dollar legal battles."
        ),
        stats={
            "Wrecks Mapped": str(len(SUNKEN_TREASURE)),
            "Total Est. Value": "$25+ billion",
            "Still Unfound": str(sum(1 for s in SUNKEN_TREASURE if "Not yet" in str(s.get("year_found", "")) or "Still" in str(s.get("finder", "")))),
            "Deepest Wreck": "3,800m (Titanic)",
        },
        items=SUNKEN_TREASURE,
        popup_fields=[
            ("location", "Location"),
            ("year_sunk", "Year Sunk"),
            ("year_found", "Year Found"),
            ("cargo_value", "Cargo Value"),
            ("finder", "Found By"),
        ],
        table_columns=[
            ("name", "Shipwreck"),
            ("location", "Location"),
            ("year_sunk", "Year Sunk"),
            ("year_found", "Year Found"),
            ("cargo_value", "Value"),
            ("finder", "Found By"),
        ],
        csv_filename="sunken_treasure.csv",
        icon_name="anchor",
    )


def _mode_crown_jewels():
    _render_mode(
        title="Crown Jewels & Royal Treasures",
        description=(
            "The most dazzling collections of gemstones, gold, and regalia assembled by "
            "monarchies across the globe. These treasures represent centuries of power, "
            "conquest, and artistic mastery. Several contain individual stones that are "
            "the subjects of intense international repatriation debates."
        ),
        stats={
            "Collections Mapped": str(len(CROWN_JEWELS)),
            "Total Est. Value": "$20+ billion",
            "Largest Collection": "Iranian Crown Jewels ($12B+)",
            "Most Contested Gem": "Koh-i-Noor (4 countries claim)",
        },
        items=CROWN_JEWELS,
        popup_fields=[
            ("location", "Location"),
            ("highlight_item", "Highlight Item"),
            ("estimated_value", "Estimated Value"),
            ("pieces", "Collection Size"),
        ],
        table_columns=[
            ("name", "Collection"),
            ("location", "Location"),
            ("highlight_item", "Highlight"),
            ("estimated_value", "Value"),
            ("pieces", "Pieces"),
        ],
        csv_filename="crown_jewels.csv",
        icon_name="crown",
    )


def _mode_museum_masterpieces():
    _render_mode(
        title="Museum Masterpieces: Where Are They Now?",
        description=(
            "The world's most famous artworks and artifacts -- and the museums that house them. "
            "Many of these masterpieces have complex origin stories: looted during wars, "
            "purchased under questionable circumstances, or carried away during colonial "
            "expeditions. This map shows where they are today."
        ),
        stats={
            "Masterpieces Mapped": str(len(MUSEUM_MASTERPIECES)),
            "Countries of Origin": "8+",
            "Contested by Origin Country": str(sum(1 for m in MUSEUM_MASTERPIECES if "contested" in m.get("current_owner", "").lower())),
            "Most Visited": "Mona Lisa (10M/yr)",
        },
        items=MUSEUM_MASTERPIECES,
        popup_fields=[
            ("location", "Current Location"),
            ("artist", "Artist/Creator"),
            ("year_created", "Year Created"),
            ("origin", "Origin"),
            ("current_owner", "Current Owner"),
            ("estimated_value", "Estimated Value"),
        ],
        table_columns=[
            ("name", "Masterpiece"),
            ("location", "Current Location"),
            ("artist", "Artist"),
            ("year_created", "Created"),
            ("origin", "Origin"),
            ("current_owner", "Owner"),
        ],
        csv_filename="museum_masterpieces.csv",
        icon_name="image",
        zoom_start=2,
    )


def _mode_art_heists():
    _render_mode(
        title="Famous Art Heists",
        description=(
            "The most daring, dramatic, and sometimes tragic thefts in art history. "
            "From the unsolved Isabella Stewart Gardner heist (the FBI's top art crime case) "
            "to the Mona Lisa theft that made the painting world-famous, these crimes have "
            "captivated the public imagination. Some masterpieces were recovered; others are "
            "gone forever."
        ),
        stats={
            "Heists Mapped": str(len(FAMOUS_ART_HEISTS)),
            "Total Stolen Value": "$1.5+ billion",
            "Still Unsolved": str(sum(1 for h in FAMOUS_ART_HEISTS if "UNSOLVED" in h.get("status", ""))),
            "Works Destroyed": "7 (Kunsthal Rotterdam)",
        },
        items=FAMOUS_ART_HEISTS,
        popup_fields=[
            ("location", "Location"),
            ("date", "Date"),
            ("items_stolen", "Items Stolen"),
            ("estimated_value", "Estimated Value"),
            ("status", "Status"),
        ],
        table_columns=[
            ("name", "Heist"),
            ("location", "Location"),
            ("date", "Date"),
            ("estimated_value", "Value"),
            ("status", "Status"),
        ],
        csv_filename="art_heists.csv",
        icon_name="mask",
    )


def _mode_ancient_libraries():
    _render_mode(
        title="Ancient Libraries of the World",
        description=(
            "The great libraries of antiquity preserved humanity's knowledge through "
            "millennia. Their destruction -- by fire, conquest, and neglect -- represents "
            "incalculable losses. Yet some survived: Timbuktu's manuscripts were saved by "
            "heroic librarians, and AI is now reading Herculaneum's carbonized scrolls. "
            "Knowledge endures."
        ),
        stats={
            "Libraries Mapped": str(len(ANCIENT_LIBRARIES)),
            "Oldest": "668 BCE (Ashurbanipal)",
            "Largest": "700,000+ scrolls (Alexandria)",
            "Still Readable": "Villa of Papyri (AI), Timbuktu, Ashurbanipal tablets",
        },
        items=ANCIENT_LIBRARIES,
        popup_fields=[
            ("location", "Location"),
            ("era", "Era"),
            ("peak_holdings", "Peak Holdings"),
            ("fate", "Fate"),
            ("surviving_texts", "Surviving Texts"),
        ],
        table_columns=[
            ("name", "Library"),
            ("location", "Location"),
            ("era", "Era"),
            ("peak_holdings", "Holdings"),
            ("fate", "Fate"),
            ("surviving_texts", "Surviving Texts"),
        ],
        csv_filename="ancient_libraries.csv",
        icon_name="book",
    )


def _mode_gold_rushes():
    _render_mode(
        title="Gold Rushes of the World",
        description=(
            "The discovery of gold has reshaped continents, built cities overnight, and "
            "driven some of history's largest mass migrations. From the forty-niners of "
            "California to the frozen trails of the Klondike, these gold rushes transformed "
            "landscapes, economies, and societies -- often at enormous human cost."
        ),
        stats={
            "Gold Rushes Mapped": str(len(GOLD_RUSHES)),
            "Earliest": "1693 (Brazil)",
            "Most Gold": "Witwatersrand (40% of all gold ever mined)",
            "Largest Migration": "300,000 (California 1849)",
        },
        items=GOLD_RUSHES,
        popup_fields=[
            ("location", "Location"),
            ("year_started", "Year Started"),
            ("peak_years", "Peak Years"),
            ("gold_produced", "Gold Produced"),
            ("prospectors", "Prospectors"),
        ],
        table_columns=[
            ("name", "Gold Rush"),
            ("location", "Location"),
            ("year_started", "Started"),
            ("peak_years", "Peak Years"),
            ("gold_produced", "Gold Produced"),
            ("prospectors", "Prospectors"),
        ],
        csv_filename="gold_rushes.csv",
        icon_name="coins",
    )


def _mode_pirate_islands():
    _render_mode(
        title="Pirate Treasure Islands & Hideouts",
        description=(
            "The real pirate bases that inspired centuries of legend. Forget X marks the spot -- "
            "these were functioning communities of outlaws, with harbors, taverns, and even "
            "democratic councils. From the 'wickedest city on Earth' (Port Royal) to the "
            "self-governing Republic of Pirates in Nassau, these places shaped maritime history."
        ),
        stats={
            "Locations Mapped": str(len(PIRATE_TREASURE_ISLANDS)),
            "Peak Era": "1650-1730 (Golden Age of Piracy)",
            "Most Famous Pirate": "Blackbeard (Edward Teach)",
            "Real Buried Treasure": "Gardiner's Island (Captain Kidd)",
        },
        items=PIRATE_TREASURE_ISLANDS,
        popup_fields=[
            ("location", "Location"),
            ("era", "Era"),
            ("notable_pirates", "Notable Pirates"),
        ],
        table_columns=[
            ("name", "Location"),
            ("location", "Region"),
            ("era", "Era"),
            ("notable_pirates", "Notable Pirates"),
        ],
        csv_filename="pirate_islands.csv",
        icon_name="flag",
        center=(15.0, -40.0),
        zoom_start=3,
    )


def _mode_looted_artifacts():
    _render_mode(
        title="Looted Artifacts & Repatriation Debates",
        description=(
            "Many of the world's most famous museum objects were taken during colonial "
            "expeditions, wartime looting, or dubious excavation deals. The global "
            "repatriation movement is gaining momentum: Germany returned the Benin Bronzes "
            "in 2022, the Met returned the Lydian Hoard in 1993, and Greece continues to "
            "press for the Parthenon Marbles. This map tracks the origins and current locations "
            "of contested artifacts."
        ),
        stats={
            "Cases Mapped": str(len(LOOTED_ARTIFACTS)),
            "Successfully Returned": str(sum(1 for a in LOOTED_ARTIFACTS if "RETURNED" in a.get("repatriation_status", "").upper() or "returned" in a.get("repatriation_status", "").lower())),
            "Countries Claiming": "15+",
            "Most Contested Holder": "British Museum",
        },
        items=LOOTED_ARTIFACTS,
        popup_fields=[
            ("location", "Origin / Current Location"),
            ("year_looted", "Year Taken"),
            ("looted_by", "Taken By"),
            ("current_holders", "Current Holder(s)"),
            ("items_count", "Items"),
            ("repatriation_status", "Repatriation Status"),
        ],
        table_columns=[
            ("name", "Artifact"),
            ("location", "Origin"),
            ("year_looted", "Year Taken"),
            ("current_holders", "Current Holder"),
            ("repatriation_status", "Status"),
        ],
        csv_filename="looted_artifacts.csv",
        icon_name="balance-scale",
    )


# ═══════════════════════════════════════════════════════════════════
# MAP MODE DISPATCHER
# ═══════════════════════════════════════════════════════════════════
MODE_RENDERERS = {
    MAP_MODES[0]: _mode_lost_treasures,
    MAP_MODES[1]: _mode_archaeological_finds,
    MAP_MODES[2]: _mode_sunken_treasure,
    MAP_MODES[3]: _mode_crown_jewels,
    MAP_MODES[4]: _mode_museum_masterpieces,
    MAP_MODES[5]: _mode_art_heists,
    MAP_MODES[6]: _mode_ancient_libraries,
    MAP_MODES[7]: _mode_gold_rushes,
    MAP_MODES[8]: _mode_pirate_islands,
    MAP_MODES[9]: _mode_looted_artifacts,
}


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
def render_treasure_maps_tab():
    """Render the Treasures & Lost Artifacts tab in TerraScout AI."""

    # Tab header
    st.markdown(
        '<div class="tab-header amber">'
        '<h4>💎 Treasures & Lost Artifacts</h4>'
        '<p>Hidden treasures, lost artifacts, museum collections, famous heists & 10 maps</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Mode selector
    selected_mode = st.selectbox(
        "Select Map Mode",
        MAP_MODES,
        index=0,
        help="Choose from 10 curated treasure & artifact map modes.",
    )

    st.markdown("---")

    # Render selected mode
    renderer = MODE_RENDERERS.get(selected_mode)
    if renderer:
        renderer()
    else:
        st.warning("Unknown map mode selected.")
