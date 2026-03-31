# -*- coding: utf-8 -*-
"""
Pirates & Maritime History Explorer module for TerraScout AI.
Curated databases of pirate havens, famous shipwrecks, naval battles,
treasure legends, Viking routes, Barbary pirates, East Asian pirates,
privateers, maritime museums, and smuggling routes.
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
from streamlit.components.v1 import html as st_html
import html as html_module

# ═══════════════════════════════════════════════════════════════════════════════
# THEME CONSTANTS (TerraScout AI dark theme)
# ═══════════════════════════════════════════════════════════════════════════════
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

# ═══════════════════════════════════════════════════════════════════════════════
# MODE DESCRIPTIONS
# ═══════════════════════════════════════════════════════════════════════════════
MODE_DESCRIPTIONS = {
    "Golden Age Pirate Havens": (
        "The Golden Age of Piracy (c. 1650-1730) saw Caribbean ports, remote islands, "
        "and lawless harbors transformed into pirate republics. From Port Royal's debauchery "
        "to Nassau's pirate democracy, these havens shaped the era's most infamous careers."
    ),
    "Famous Shipwrecks": (
        "Legendary vessels lost to storms, reefs, and battle -- from Blackbeard's Queen Anne's "
        "Revenge to the treasure-laden Nuestra Senora de Atocha. Each wreck tells a story of "
        "ambition, tragedy, and the unforgiving sea."
    ),
    "Naval Battle Sites": (
        "The great sea battles that decided the fates of empires: Trafalgar, Midway, Salamis, "
        "Lepanto, and dozens more. From ancient triremes to WWII aircraft carriers, naval warfare "
        "has shaped civilization for three millennia."
    ),
    "Treasure Map Legends": (
        "Buried pirate gold, coded cryptograms, cursed islands, and treasure hunts that have "
        "consumed generations of seekers. From Oak Island's Money Pit to the unfound fortune "
        "of La Buse, these legends endure."
    ),
    "Viking Sea Routes": (
        "Norse raiders, traders, and explorers who sailed from Scandinavia to Byzantium, "
        "Baghdad, and North America between 793-1066 AD. The Vikings built a maritime "
        "network spanning half the globe."
    ),
    "Barbary Coast Pirates": (
        "The Barbarossa brothers, Dragut, and the corsair states that terrorized the "
        "Mediterranean for over 300 years. Ottoman-backed piracy that enslaved over a "
        "million Europeans and provoked wars with America."
    ),
    "East Asian Pirates": (
        "From the fearsome Japanese Wako raiders to Ching Shih's 80,000-strong pirate "
        "armada, East Asian piracy was vast in scale. The Zheng family empire and Moro "
        "raiders dominated Asian seas for centuries."
    ),
    "Privateers & Corsairs": (
        "Government-sanctioned sea raiders operating with letters of marque. Drake, Jean "
        "Bart, the Sea Beggars, and American Revolution privateers -- legal pirates who "
        "blurred the line between patriotism and piracy."
    ),
    "Maritime Museums": (
        "The finest collections of maritime history worldwide: pirate artifacts, preserved "
        "warships, treasure salvage, and underwater archaeology from the Vasa Museum to "
        "the Mel Fisher Maritime Heritage Museum."
    ),
    "Smuggling Routes & Hideouts": (
        "Secret coves, moonless Channel crossings, Prohibition rum runners, and the illicit "
        "trade networks that defied empires for centuries. From Cornish brandy caves to "
        "Prohibition-era Rum Row."
    ),
}

# ═══════════════════════════════════════════════════════════════════════════════
# CURATED DATASETS
# ═══════════════════════════════════════════════════════════════════════════════

GOLDEN_AGE_HAVENS = [
    {"name": "Port Royal", "lat": 17.9362, "lon": -76.8412, "country": "Jamaica", "era": "1650-1692", "famous_pirates": "Henry Morgan, Calico Jack", "desc": "The 'Wickedest City on Earth' -- hub of buccaneering in the Caribbean until a devastating earthquake sank much of the city in 1692.", "color": _AMBER},
    {"name": "Nassau (New Providence)", "lat": 25.0480, "lon": -77.3554, "country": "Bahamas", "era": "1706-1718", "famous_pirates": "Blackbeard, Charles Vane, Anne Bonny", "desc": "Republic of Pirates. Governed by pirate captains for over a decade until Woodes Rogers restored British authority in 1718.", "color": _AMBER},
    {"name": "Tortuga", "lat": 20.0554, "lon": -72.7863, "country": "Haiti", "era": "1630-1680", "famous_pirates": "Francois l'Olonnais, Pierre le Grand", "desc": "Notorious buccaneering stronghold off the coast of Hispaniola. French and English pirates used it as a base to raid Spanish ships.", "color": _AMBER},
    {"name": "Saint-Malo", "lat": 48.6493, "lon": -2.0007, "country": "France", "era": "1500-1700", "famous_pirates": "Robert Surcouf, Rene Duguay-Trouin", "desc": "Walled port city famed for corsairs who held royal commissions. Known as the 'City of Privateers' along the Brittany coast.", "color": _AMBER},
    {"name": "Ile Sainte-Marie (Nosy Boraha)", "lat": -16.8500, "lon": 49.9167, "country": "Madagascar", "era": "1690-1730", "famous_pirates": "Adam Baldridge, William Kidd", "desc": "Remote island haven off eastern Madagascar. Pirates established a fortified trading post and launched raids on Indian Ocean shipping.", "color": _AMBER},
    {"name": "Libertatia (Libertalia)", "lat": -15.7167, "lon": 46.3167, "country": "Madagascar (legendary)", "era": "c. 1690s", "famous_pirates": "Captain James Misson (legendary)", "desc": "Possibly mythical pirate utopia said to have been founded on Madagascar. Described in Captain Charles Johnson's General History of the Pyrates.", "color": _VIOLET},
    {"name": "Barataria Bay", "lat": 29.4250, "lon": -89.9550, "country": "USA (Louisiana)", "era": "1805-1815", "famous_pirates": "Jean Lafitte, Pierre Lafitte", "desc": "Marshy bayou stronghold south of New Orleans. Jean Lafitte ran a smuggling and privateering empire from this remote base.", "color": _AMBER},
    {"name": "Ocracoke Island", "lat": 35.1146, "lon": -75.9810, "country": "USA (North Carolina)", "era": "1710-1718", "famous_pirates": "Blackbeard (Edward Teach)", "desc": "Blackbeard's favorite anchorage in the Outer Banks. He was killed here in a fierce battle with Lt. Robert Maynard's forces in 1718.", "color": _RED},
    {"name": "Salé", "lat": 34.0389, "lon": -6.8036, "country": "Morocco", "era": "1600-1800", "famous_pirates": "Salé Rovers, Jan Janszoon", "desc": "Independent pirate republic on the Moroccan coast. The Salé Rovers terrorized Atlantic shipping and even raided Iceland and Ireland.", "color": _AMBER},
    {"name": "Tunis", "lat": 36.8065, "lon": 10.1815, "country": "Tunisia", "era": "1500-1830", "famous_pirates": "Hayreddin Barbarossa, Dragut", "desc": "Major base for Barbary corsairs who controlled much of the western Mediterranean. Ottoman-backed piracy lasted for centuries.", "color": _AMBER},
    {"name": "Algiers", "lat": 36.7538, "lon": 3.0588, "country": "Algeria", "era": "1500-1830", "famous_pirates": "Aruj Barbarossa, Uluj Ali", "desc": "Capital of the Barbary Coast pirate state. European nations paid enormous tributes to avoid having their ships seized.", "color": _AMBER},
    {"name": "Tripoli", "lat": 32.9022, "lon": 13.1800, "country": "Libya", "era": "1550-1835", "famous_pirates": "Murad Reis, Turgut Reis", "desc": "Eastern Barbary Coast stronghold. The First Barbary War (1801-1805) was fought to end Tripolitan piracy against American shipping.", "color": _AMBER},
    {"name": "Petit Goave", "lat": 18.4311, "lon": -72.8669, "country": "Haiti", "era": "1660-1700", "famous_pirates": "Laurens de Graaf, Michel de Grammont", "desc": "French buccaneer base on the southern coast of Saint-Domingue. Hub for raids against Spanish colonial settlements.", "color": _AMBER},
    {"name": "Charles Town (Charleston)", "lat": 32.7765, "lon": -79.9311, "country": "USA (South Carolina)", "era": "1670-1720", "famous_pirates": "Blackbeard, Stede Bonnet", "desc": "Wealthy colonial port that Blackbeard famously blockaded in 1718, holding the city hostage for medicine. Stede Bonnet was hanged here.", "color": _RED},
    {"name": "Madagascar (Diego Suarez)", "lat": -12.2765, "lon": 49.2917, "country": "Madagascar", "era": "1690-1730", "famous_pirates": "Thomas Tew, Henry Every", "desc": "Northern Madagascar served as a staging point for pirates raiding the rich Mughal treasure fleets in the Indian Ocean.", "color": _AMBER},
    {"name": "Tortola", "lat": 18.4317, "lon": -64.6400, "country": "British Virgin Islands", "era": "1650-1720", "famous_pirates": "Various buccaneers", "desc": "Sheltered harbors of the Virgin Islands provided perfect hiding spots for pirates preying on the busy Caribbean trade routes.", "color": _AMBER},
    {"name": "New Providence (Harbour Island)", "lat": 25.5000, "lon": -76.6333, "country": "Bahamas", "era": "1700-1718", "famous_pirates": "Benjamin Hornigold", "desc": "Secondary pirate anchorage near Nassau. Hornigold mentored both Blackbeard and Sam Bellamy from these waters.", "color": _AMBER},
    {"name": "Zanzibar", "lat": -6.1659, "lon": 39.2026, "country": "Tanzania", "era": "1650-1800", "famous_pirates": "Captain Kidd, various", "desc": "East African trading hub used by pirates operating in the Indian Ocean. Also a major center for the slave trade.", "color": _AMBER},
    {"name": "Galveston Island", "lat": 29.3013, "lon": -94.7977, "country": "USA (Texas)", "era": "1817-1821", "famous_pirates": "Jean Lafitte", "desc": "Lafitte established a pirate colony called Campeche on Galveston after leaving Barataria. Abandoned in 1821 under US pressure.", "color": _AMBER},
    {"name": "Providence Island", "lat": 13.3500, "lon": -81.3667, "country": "Colombia", "era": "1629-1641", "famous_pirates": "Henry Morgan (later)", "desc": "English Puritan colony that turned to privateering. Strategically located to intercept Spanish treasure fleets.", "color": _AMBER},
    {"name": "Hispaniola (Cow Island)", "lat": 18.6347, "lon": -74.2639, "country": "Haiti", "era": "1620-1680", "famous_pirates": "Buccaneers (boucaniers)", "desc": "Original buccaneers were wild cattle hunters on Hispaniola who turned to piracy. The word 'buccaneer' comes from their boucan smokehouses.", "color": _AMBER},
    {"name": "Port-de-Paix", "lat": 19.9397, "lon": -72.8303, "country": "Haiti", "era": "1680-1700", "famous_pirates": "Henry Morgan's fleet", "desc": "Northern Hispaniola port used by French and English pirates to coordinate large-scale raids on Spanish colonial cities.", "color": _AMBER},
    {"name": "Campeche", "lat": 19.8301, "lon": -90.5349, "country": "Mexico", "era": "1560-1700", "famous_pirates": "Lorencillo, various", "desc": "Spanish colonial port repeatedly sacked by pirates. Its logwood trade attracted raiders from across the Caribbean.", "color": _AMBER},
    {"name": "Maracaibo", "lat": 10.6544, "lon": -71.6292, "country": "Venezuela", "era": "1660-1680", "famous_pirates": "Henry Morgan, l'Olonnais", "desc": "Wealthy Venezuelan port sacked multiple times by buccaneers. Morgan's 1669 raid was one of his most famous exploits.", "color": _AMBER},
    {"name": "Portobelo", "lat": 9.5500, "lon": -79.6531, "country": "Panama", "era": "1600-1740", "famous_pirates": "Henry Morgan, Francis Drake", "desc": "Spanish treasure port on the Isthmus of Panama. Key transshipment point for Peruvian silver, making it an irresistible pirate target.", "color": _GOLD},
]

FAMOUS_SHIPWRECKS = [
    {"name": "Queen Anne's Revenge", "lat": 34.6929, "lon": -76.6704, "year": 1718, "captain": "Blackbeard", "desc": "Blackbeard's flagship, originally a French slave ship La Concorde. Ran aground at Beaufort Inlet, North Carolina. Discovered in 1996.", "color": _RED},
    {"name": "Whydah Gally", "lat": 41.6740, "lon": -69.9578, "year": 1717, "captain": "Black Sam Bellamy", "desc": "Only authenticated pirate shipwreck ever discovered. Sank in a nor'easter off Cape Cod carrying over 4.5 tons of treasure.", "color": _GOLD},
    {"name": "Adventure Galley", "lat": -12.2833, "lon": 49.2917, "year": 1698, "captain": "Captain William Kidd", "desc": "Kidd's rotting ship was scuttled in Madagascar after his ill-fated privateering voyage. He was later hanged for piracy in London.", "color": _AMBER},
    {"name": "San Martin (1588)", "lat": 56.5000, "lon": -9.0000, "year": 1588, "captain": "Spanish Armada", "desc": "Flagship of the Spanish Armada's squadron. Many Armada ships wrecked on Scottish and Irish coasts during the disastrous retreat.", "color": _RED},
    {"name": "Nuestra Senora de Atocha", "lat": 24.5242, "lon": -82.2219, "year": 1622, "captain": "Spanish Treasure Fleet", "desc": "Sank in a hurricane off the Florida Keys carrying 40 tons of gold and silver. Mel Fisher found her in 1985 after a 16-year search.", "color": _GOLD},
    {"name": "San Jose (1708)", "lat": 10.3700, "lon": -76.0200, "year": 1708, "captain": "Spanish Treasure Fleet", "desc": "Sunk by the British near Cartagena, Colombia. Called the 'Holy Grail of Shipwrecks' with an estimated $17 billion in treasure.", "color": _GOLD},
    {"name": "The Golden Hind (replica site)", "lat": 51.5074, "lon": -0.0880, "year": 1580, "captain": "Sir Francis Drake", "desc": "Drake's famous vessel that circumnavigated the globe (1577-1580). The original was broken up; a replica sits in London.", "color": _EMERALD},
    {"name": "HMS Victory (1744)", "lat": 49.4800, "lon": -4.9500, "year": 1744, "captain": "Admiral Sir John Balchin", "desc": "Not Nelson's flagship -- an earlier warship lost with all 1,100 crew in the English Channel. Found in 2008 with possible gold cargo.", "color": _BLUE},
    {"name": "Le Griffon", "lat": 45.7833, "lon": -85.5333, "year": 1679, "captain": "Rene-Robert Cavelier de La Salle", "desc": "First full-size sailing ship on the Great Lakes. Vanished on Lake Michigan on her maiden return voyage -- America's oldest shipwreck mystery.", "color": _VIOLET},
    {"name": "Santa Maria", "lat": 19.9000, "lon": -72.2000, "year": 1492, "captain": "Christopher Columbus", "desc": "Columbus's flagship ran aground on a reef off Hispaniola on Christmas Day, 1492. Her timbers were used to build Fort La Navidad.", "color": _RED},
    {"name": "Flor de la Mar", "lat": 2.5000, "lon": 103.5000, "year": 1511, "captain": "Afonso de Albuquerque", "desc": "Portuguese carrack loaded with the plundered treasure of Malacca. Sank in the Strait of Malacca; never found. Possibly richest wreck ever.", "color": _GOLD},
    {"name": "Vasa", "lat": 59.3280, "lon": 18.0914, "year": 1628, "captain": "Captain Sofring Hansson", "desc": "Swedish warship that sank on her maiden voyage in Stockholm harbor. Salvaged nearly intact in 1961 and now a famous museum.", "color": _EMERALD},
    {"name": "Batavia", "lat": -28.4900, "lon": 113.7900, "year": 1629, "captain": "Dutch East India Company", "desc": "Wrecked on the Abrolhos Islands, Western Australia. Survivors endured a horrific mutiny and massacre before rescue arrived.", "color": _RED},
    {"name": "HMS Endeavour", "lat": 41.5037, "lon": -71.3894, "year": 1778, "captain": "Originally James Cook", "desc": "Cook's famous exploration ship was later scuttled in Newport Harbor during the American Revolution. Wreck identified in 2022.", "color": _BLUE},
    {"name": "La Belle", "lat": 28.5950, "lon": -96.3028, "year": 1686, "captain": "Rene-Robert Cavelier de La Salle", "desc": "French exploration vessel wrecked in Matagorda Bay, Texas. Excavated from the seabed in a remarkable archaeological dig in the 1990s.", "color": _VIOLET},
    {"name": "Quedagh Merchant", "lat": 19.2000, "lon": -69.9000, "year": 1699, "captain": "Captured by Captain Kidd", "desc": "Armenian merchant ship captured by Kidd, sparking the piracy charges that led to his execution. Found off the Dominican Republic in 2007.", "color": _AMBER},
    {"name": "Concepcion", "lat": 20.9500, "lon": -68.6000, "year": 1641, "captain": "Spanish Treasure Fleet", "desc": "Nuestra Senora de la Pura y Limpia Concepcion sank on Silver Shoals. William Phips salvaged a fortune from her in 1687.", "color": _GOLD},
    {"name": "Bonhomme Richard", "lat": 55.6900, "lon": -1.8000, "year": 1779, "captain": "John Paul Jones", "desc": "Jones's flagship sank after his legendary victory over HMS Serapis. He declared 'I have not yet begun to fight!' during the battle.", "color": _BLUE},
    {"name": "Mary Rose", "lat": 50.7833, "lon": -1.1000, "year": 1545, "captain": "Vice Admiral Sir George Carew", "desc": "Henry VIII's favorite warship sank in the Solent during a battle with France. Raised in 1982 and preserved in Portsmouth.", "color": _EMERALD},
    {"name": "San Pedro de Alcantara", "lat": 37.2300, "lon": -7.0000, "year": 1786, "captain": "Spanish Navy", "desc": "Spanish frigate carrying a fortune in Peruvian silver. Wrecked near Peniche, Portugal. Salvage attempts have recovered millions.", "color": _GOLD},
    {"name": "Fancy (Henry Every)", "lat": 25.0343, "lon": -77.3963, "year": 1696, "captain": "Henry Every", "desc": "Every's ship after his legendary capture of the Mughal treasure ship Ganj-i-Sawai. He disappeared and was never seen again.", "color": _VIOLET},
    {"name": "Royal Fortune", "lat": 5.6037, "lon": -0.1870, "year": 1722, "captain": "Bartholomew Roberts", "desc": "Black Bart Roberts' last ship. He was killed in battle off Cape Lopez, Gabon, ending the career of history's most successful pirate.", "color": _RED},
    {"name": "Speaker", "lat": -19.8833, "lon": 57.7833, "year": 1702, "captain": "John Bowen", "desc": "Pirate ship wrecked on a reef near Mauritius. Bowen and crew salvaged what they could and continued pirating on captured vessels.", "color": _AMBER},
    {"name": "Satisfaction", "lat": 18.2300, "lon": -87.8300, "year": 1669, "captain": "Henry Morgan (fleet)", "desc": "One of Morgan's fleet ships lost during his expedition. Believed to lie in the waters off the coast of Belize.", "color": _AMBER},
    {"name": "Henrietta Marie", "lat": 24.5500, "lon": -82.0500, "year": 1700, "captain": "Slave trade vessel", "desc": "English slave ship wrecked in the Florida Keys. One of the most significant underwater archaeological finds related to the slave trade.", "color": _RED},
    {"name": "Ganj-i-Sawai (capture site)", "lat": 17.0000, "lon": 71.0000, "year": 1695, "captain": "Captured by Henry Every", "desc": "Grand Mughal treasure ship captured in history's most lucrative pirate raid. Each crew member received a fortune worth millions today.", "color": _GOLD},
    {"name": "HMS Fowey", "lat": 25.0200, "lon": -80.3000, "year": 1748, "captain": "Captain Francis William Drake", "desc": "British warship wrecked on a reef off Biscayne Bay, Florida. Discovered in 1939 and designated a protected archaeological site.", "color": _BLUE},
    {"name": "Pirate Ship (Black Sam - Marianne)", "lat": 41.9100, "lon": -69.9500, "year": 1717, "captain": "Paulsgrave Williams (Bellamy's consort)", "desc": "Consort ship of the Whydah fleet. The Marianne wrecked near the Whydah in the same storm off Cape Cod.", "color": _AMBER},
]

NAVAL_BATTLES = [
    {"name": "Battle of Trafalgar", "lat": 36.1800, "lon": -6.2400, "year": 1805, "forces": "Britain vs France & Spain", "desc": "Nelson's greatest victory and death. Established British naval supremacy for a century. 27 British ships defeated 33 Franco-Spanish.", "color": _BLUE},
    {"name": "Battle of Lepanto", "lat": 38.2950, "lon": 21.0900, "year": 1571, "forces": "Holy League vs Ottoman Empire", "desc": "Last great galley battle. A coalition of Christian states destroyed the Ottoman fleet, halting Ottoman expansion in the Mediterranean.", "color": _RED},
    {"name": "Battle of the Nile (Aboukir Bay)", "lat": 31.3200, "lon": 30.0700, "year": 1798, "forces": "Britain vs France", "desc": "Nelson destroyed Napoleon's fleet at anchor in Egypt. The French flagship L'Orient exploded in one of the most famous events in naval history.", "color": _BLUE},
    {"name": "Battle of Gravelines (Spanish Armada)", "lat": 51.0136, "lon": 2.1281, "year": 1588, "forces": "England vs Spain", "desc": "Fire ships scattered the Spanish Armada. Combined with storms, this ended Philip II's invasion plan and shifted the balance of sea power.", "color": _RED},
    {"name": "Battle of Midway", "lat": 28.2000, "lon": -177.3700, "year": 1942, "forces": "USA vs Japan", "desc": "Turning point of the Pacific War. American aircraft sank four Japanese carriers in a decisive victory that reversed Japanese expansion.", "color": _BLUE},
    {"name": "Battle of Salamis", "lat": 37.9500, "lon": 23.5833, "year": -480, "forces": "Greek city-states vs Persia", "desc": "Themistocles lured Xerxes' fleet into the narrow strait. The Greek victory saved Western civilization from Persian conquest.", "color": _EMERALD},
    {"name": "Battle of Actium", "lat": 38.9500, "lon": 20.7167, "year": -31, "forces": "Octavian vs Antony & Cleopatra", "desc": "Octavian's fleet defeated Antony and Cleopatra, leading to the fall of the Roman Republic and the birth of the Roman Empire.", "color": _VIOLET},
    {"name": "Battle of Tsushima", "lat": 34.5000, "lon": 129.5000, "year": 1905, "forces": "Japan vs Russia", "desc": "Japanese fleet annihilated the Russian Baltic Fleet after its 18,000-mile voyage. First modern naval battle decided by battleships.", "color": _RED},
    {"name": "Battle of Jutland", "lat": 57.0500, "lon": 6.0500, "year": 1916, "forces": "Britain vs Germany", "desc": "Largest naval battle of WWI. Though tactically inconclusive, the German High Seas Fleet never again challenged British dominance.", "color": _BLUE},
    {"name": "Siege of Yorktown (Naval)", "lat": 37.2388, "lon": -76.5097, "year": 1781, "forces": "France vs Britain", "desc": "French Admiral de Grasse defeated the British fleet at the Battle of the Chesapeake, trapping Cornwallis and winning American independence.", "color": _EMERALD},
    {"name": "Battle of the Coral Sea", "lat": -15.0000, "lon": 152.0000, "year": 1942, "forces": "USA & Australia vs Japan", "desc": "First naval battle where opposing ships never sighted each other -- fought entirely by carrier aircraft. Strategic Allied victory.", "color": _BLUE},
    {"name": "Battle of Leyte Gulf", "lat": 11.0000, "lon": 126.5000, "year": 1944, "forces": "USA & Australia vs Japan", "desc": "Largest naval battle in history by number of ships. Japanese fleet was effectively destroyed, ending their naval power in WWII.", "color": _BLUE},
    {"name": "Battle of the Chesapeake", "lat": 36.9600, "lon": -75.8700, "year": 1781, "forces": "France vs Britain", "desc": "De Grasse's French fleet prevented British reinforcement of Yorktown. Often called the most important naval battle in American history.", "color": _EMERALD},
    {"name": "Battle of Cape Finisterre", "lat": 42.7700, "lon": -9.3000, "year": 1747, "forces": "Britain vs France", "desc": "Anson's decisive victory over the French fleet. Captured treasure worth millions and secured British control of the Atlantic.", "color": _BLUE},
    {"name": "Battle of the Saintes", "lat": 15.8667, "lon": -61.5833, "year": 1782, "forces": "Britain vs France", "desc": "Rodney's fleet broke the French line of battle in the Caribbean. Saved Jamaica from French invasion and restored British prestige.", "color": _BLUE},
    {"name": "Battle of Copenhagen", "lat": 55.6761, "lon": 12.5683, "year": 1801, "forces": "Britain vs Denmark-Norway", "desc": "Nelson famously put his telescope to his blind eye to ignore the signal to withdraw. Destroyed the Danish fleet at anchor.", "color": _BLUE},
    {"name": "Battle of the Atlantic", "lat": 50.0000, "lon": -30.0000, "year": 1939, "forces": "Allies vs Germany (U-boats)", "desc": "The longest continuous military campaign of WWII. German U-boats sank over 3,500 Allied ships before being defeated by convoy tactics.", "color": _RED},
    {"name": "Battle of Quiberon Bay", "lat": 47.4500, "lon": -3.1000, "year": 1759, "forces": "Britain vs France", "desc": "Hawke pursued the French fleet into a dangerous bay during a gale. Brilliant victory that ended French invasion plans for Britain.", "color": _BLUE},
    {"name": "Battle of the Virginia Capes", "lat": 37.0000, "lon": -75.5000, "year": 1781, "forces": "France vs Britain", "desc": "French tactical victory that contributed to the British defeat at Yorktown. De Grasse held the bay against Graves' relief force.", "color": _EMERALD},
    {"name": "Battle of Hampton Roads", "lat": 36.9800, "lon": -76.3300, "year": 1862, "forces": "USS Monitor vs CSS Virginia", "desc": "First battle between ironclad warships. Revolutionized naval warfare overnight, making wooden warships obsolete.", "color": _VIOLET},
    {"name": "Raid on the Medway", "lat": 51.3967, "lon": 0.5917, "year": 1667, "forces": "Dutch Republic vs England", "desc": "Dutch fleet sailed up the Thames and Medway, burning English warships. One of England's worst military defeats; they towed away the flagship.", "color": _RED},
    {"name": "Battle of Myeongnyang", "lat": 34.5675, "lon": 126.3086, "year": 1597, "forces": "Korea vs Japan", "desc": "Admiral Yi Sun-sin defeated 133 Japanese warships with only 13 Korean ships using the Myeongnyang Strait's dangerous currents.", "color": _EMERALD},
    {"name": "Battle of Manila Bay", "lat": 14.5500, "lon": 120.9000, "year": 1898, "forces": "USA vs Spain", "desc": "Dewey's Asiatic Squadron destroyed the Spanish Pacific fleet without losing a single man. Marked America's emergence as a global naval power.", "color": _BLUE},
    {"name": "Battle of the Falklands", "lat": -51.7500, "lon": -59.0000, "year": 1914, "forces": "Britain vs Germany", "desc": "British battlecruisers avenged the defeat at Coronel by sinking von Spee's armored cruiser squadron near the Falkland Islands.", "color": _BLUE},
    {"name": "Battle of Diu", "lat": 20.7144, "lon": 70.9875, "year": 1509, "forces": "Portugal vs Mamluk-Gujarat alliance", "desc": "Portuguese victory established their dominance of the Indian Ocean spice trade for over a century. Beginning of European colonial naval power.", "color": _VIOLET},
    {"name": "Battle of Sluys", "lat": 51.3500, "lon": 3.3833, "year": 1340, "forces": "England vs France", "desc": "Edward III's fleet destroyed the French fleet in a harbor battle. First major engagement of the Hundred Years' War gave England naval control.", "color": _RED},
    {"name": "Battle of the Nile (Lake Trasimene context)", "lat": 31.3000, "lon": 30.0500, "year": 1798, "forces": "Britain vs France", "desc": "Nelson's decisive destruction of Napoleon's Egyptian fleet stranded the French army and made Napoleon's eastern ambitions impossible.", "color": _BLUE},
]

TREASURE_LEGENDS = [
    {"name": "Oak Island Money Pit", "lat": 44.5130, "lon": -64.2988, "legend": "Buried treasure of unknown origin", "era": "Discovered 1795", "desc": "A mysterious pit on Oak Island, Nova Scotia, has driven treasure hunters for over 200 years. Theories attribute it to Captain Kidd, the Knights Templar, or Francis Bacon.", "color": _GOLD},
    {"name": "Treasure of Lima", "lat": 5.5500, "lon": -87.0333, "legend": "Looted Lima cathedral treasure", "era": "1820", "desc": "Spanish officials entrusted the treasure of Lima's churches to Captain William Thompson. He murdered the guards and sailed to Cocos Island. Never recovered.", "color": _GOLD},
    {"name": "Blackbeard's Treasure", "lat": 35.1146, "lon": -75.9810, "legend": "Blackbeard's hidden loot", "era": "c. 1718", "desc": "Blackbeard reportedly said his treasure was hidden 'where none but Satan and myself can find it.' Numerous sites across the Outer Banks have been searched.", "color": _AMBER},
    {"name": "Captain Kidd's Treasure", "lat": 41.0772, "lon": -72.1803, "legend": "Kidd's buried pirate gold", "era": "1699", "desc": "Kidd buried some treasure on Gardiner's Island, NY, which was recovered. But legends persist of far greater caches hidden along the American coast.", "color": _AMBER},
    {"name": "Treasure of the Knights Templar", "lat": 48.8032, "lon": 2.4014, "legend": "Lost Templar fortune", "era": "1307", "desc": "When Philip IV dissolved the Templars, their vast treasure vanished overnight. Theories place it in Scotland, Nova Scotia, or beneath the Temple of Solomon.", "color": _VIOLET},
    {"name": "El Dorado (Lake Guatavita)", "lat": 4.9778, "lon": -73.7764, "legend": "City of Gold", "era": "1500s-1700s", "desc": "The Muisca ceremony of gilding their chief fueled legends of a city of gold. Countless expeditions failed to find it; the lake was partially drained multiple times.", "color": _GOLD},
    {"name": "Treasure of Rennes-le-Chateau", "lat": 42.9260, "lon": 2.2614, "legend": "Abbe Sauniere's mysterious wealth", "era": "1890s", "desc": "A poor parish priest suddenly became wealthy after allegedly finding something in his church. Linked to Templar treasure, Cathar gold, or royal secrets.", "color": _VIOLET},
    {"name": "Lost Dutchman's Mine", "lat": 33.3942, "lon": -111.3194, "legend": "Lost gold mine in the Superstition Mountains", "era": "1840s", "desc": "German immigrant Jacob Waltz allegedly found a fabulously rich gold mine in Arizona's Superstition Mountains. Many have died searching for it.", "color": _GOLD},
    {"name": "Pirate Treasure of Palmyra Atoll", "lat": 5.8833, "lon": -162.0833, "legend": "Buried pirate gold", "era": "1816", "desc": "The Spanish pirate ship Esperanza allegedly buried treasure on this remote Pacific atoll. The island has a reputation for misfortune and mysterious deaths.", "color": _AMBER},
    {"name": "Treasure of Forrest Fenn", "lat": 36.0000, "lon": -105.5000, "legend": "Hidden chest of gold and gems", "era": "2010 (hidden), 2020 (found)", "desc": "Art dealer Forrest Fenn hid a bronze chest containing gold, gems, and artifacts in the Rocky Mountains. Found in 2020 after a decade-long search.", "color": _EMERALD},
    {"name": "Flor de la Mar Treasure", "lat": 2.5000, "lon": 103.5000, "legend": "Plundered treasure of Malacca", "era": "1511", "desc": "The richest ship ever to sail, loaded with the treasure of the Malaccan sultanate. Sank in the Strait of Malacca and has never been found.", "color": _GOLD},
    {"name": "Jean Lafitte's Contraband", "lat": 29.4250, "lon": -89.9550, "legend": "Lafitte's hidden smuggling fortune", "era": "1810s", "desc": "The pirate-privateer Jean Lafitte is said to have buried treasure throughout the Louisiana bayous and along the Gulf Coast. None confirmed.", "color": _AMBER},
    {"name": "Dead Man's Chest (island)", "lat": 18.3800, "lon": -64.4750, "legend": "Blackbeard marooned 15 men here", "era": "c. 1717", "desc": "The tiny island is supposedly where Blackbeard marooned 15 mutinous crew with nothing but a bottle of rum -- inspiring the famous pirate song.", "color": _RED},
    {"name": "Ilha da Queimada Grande (Treasure legend)", "lat": -24.4875, "lon": -46.6753, "legend": "Brazilian pirate gold", "era": "1800s", "desc": "Legends say pirates buried treasure on this Brazilian island. Now home to thousands of deadly golden lancehead vipers -- the most dangerous island on Earth.", "color": _RED},
    {"name": "Mahé (Pirate Cemetery)", "lat": -4.6833, "lon": 55.5000, "legend": "Treasure of La Buse", "era": "1730", "desc": "Olivier Levasseur ('La Buse') reportedly threw a coded cryptogram to the crowd at his execution, saying 'Find my treasure, he who can!' Still unsolved.", "color": _VIOLET},
    {"name": "Isla de Mona", "lat": 18.0850, "lon": -67.8940, "legend": "Pirate treasure caves", "era": "1600s-1700s", "desc": "Remote island between Puerto Rico and Hispaniola riddled with caves. Pirates including Captain Kidd allegedly used it as a treasure cache.", "color": _AMBER},
    {"name": "Norman Island", "lat": 18.3200, "lon": -64.6200, "legend": "Inspiration for Treasure Island", "era": "1750s", "desc": "Said to have inspired Robert Louis Stevenson's Treasure Island. Spanish treasure from a wrecked Nuestra Senora was allegedly hidden in its caves.", "color": _GOLD},
    {"name": "Skeleton Island (Heard Island)", "lat": -53.1000, "lon": 73.5167, "legend": "Remote Southern Ocean treasure", "era": "1800s", "desc": "One of the most remote islands on Earth. Persistent legends of sealers and pirates burying treasure on this volcanic, glacier-covered island.", "color": _VIOLET},
    {"name": "Guadalcanal Gold", "lat": -9.4438, "lon": 160.0356, "legend": "WWII Japanese war gold", "era": "1942", "desc": "Rumors persist that Japanese forces buried looted treasure on Guadalcanal during WWII before the American invasion. Part of the 'Yamashita's Gold' legend.", "color": _GOLD},
    {"name": "Treasure Fleet of 1715", "lat": 27.5800, "lon": -80.3600, "year": 1715, "legend": "Spanish Plate Fleet", "desc": "Eleven Spanish ships sank in a hurricane off Florida's Treasure Coast. Worth billions, coins still wash up on beaches. Major salvage operations continue.", "color": _GOLD},
    {"name": "Nuestra Senora de las Mercedes", "lat": 36.1833, "lon": -6.6833, "legend": "Spanish frigate treasure", "era": "1804", "desc": "Spanish frigate carrying 17 tons of coins sunk by the British at the Battle of Cape Santa Maria. Odyssey Marine found it in 2007; Spain won a legal battle for the treasure.", "color": _GOLD},
    {"name": "Pirate Gold of Amelia Island", "lat": 30.6694, "lon": -81.4439, "legend": "Multiple pirate caches", "era": "1700s-1800s", "desc": "Amelia Island, Florida, changed hands 8 times between nations and was a haven for pirates, smugglers, and freebooters. Treasure legends abound.", "color": _AMBER},
    {"name": "Robinson Crusoe Island Treasure", "lat": -33.6367, "lon": -78.8300, "legend": "Spanish colonial treasure", "era": "1715", "desc": "A treasure of 800 barrels of gold allegedly buried by Spanish navigator Juan Esteban Ubilla. A 2005 expedition claimed to locate it using a robot.", "color": _GOLD},
    {"name": "Treasure of the San Miguel", "lat": 27.3800, "lon": -80.2500, "legend": "1715 Fleet flagship treasure", "era": "1715", "desc": "The capitana of the 1715 Treasure Fleet. Carried the bulk of the fleet's registered treasure. Salvagers continue to find gold coins along the Florida coast.", "color": _GOLD},
    {"name": "John Rackham's Loot", "lat": 18.1096, "lon": -77.2975, "legend": "Calico Jack's hidden treasure", "era": "1720", "desc": "Calico Jack Rackham, famous for sailing with Anne Bonny and Mary Read, is said to have hidden treasure in Jamaica before his capture and execution.", "color": _AMBER},
]

VIKING_SEA_ROUTES = [
    {"name": "Lindisfarne (Viking raid)", "lat": 55.6689, "lon": -1.8019, "year": 793, "desc": "First major Viking raid. Norse warriors attacked the Holy Island monastery, shocking all of Christendom and beginning the Viking Age.", "color": _RED},
    {"name": "Hedeby (Haithabu)", "lat": 54.4908, "lon": 9.5629, "year": 800, "desc": "Major Viking trading town at the base of the Jutland peninsula. Hub connecting Baltic and North Sea trade networks.", "color": _TEAL},
    {"name": "Birka", "lat": 59.3333, "lon": 17.5500, "year": 790, "desc": "Sweden's first urban center and a crucial Viking trading post on Lake Malaren. UNESCO World Heritage Site.", "color": _TEAL},
    {"name": "Jorvik (York)", "lat": 53.9600, "lon": -1.0873, "year": 866, "desc": "Captured by the Great Heathen Army. Became capital of the Viking kingdom of Jorvik and one of the most important trading cities in Britain.", "color": _AMBER},
    {"name": "Dublin (Dubh Linn)", "lat": 53.3498, "lon": -6.2603, "year": 841, "desc": "Founded as a Viking longphort (ship fortress). Became one of the most important Viking settlements outside Scandinavia.", "color": _AMBER},
    {"name": "L'Anse aux Meadows", "lat": 51.5882, "lon": -55.5320, "year": 1000, "desc": "Only confirmed Norse settlement in North America. Leif Erikson's Vinland. UNESCO World Heritage Site proving Vikings reached America 500 years before Columbus.", "color": _EMERALD},
    {"name": "Reykjavik", "lat": 64.1466, "lon": -21.9426, "year": 874, "desc": "Founded by Ingolfur Arnarson. Iceland became a stepping stone for Viking expansion westward to Greenland and North America.", "color": _TEAL},
    {"name": "Brattahlid (Qassiarsuk)", "lat": 61.1500, "lon": -45.5167, "year": 985, "desc": "Erik the Red's settlement in Greenland. Center of the Norse Greenland colony that lasted nearly 500 years.", "color": _EMERALD},
    {"name": "Novgorod", "lat": 58.5225, "lon": 31.2753, "year": 859, "desc": "Major Viking (Varangian) trading city in Russia. The Rus' Vikings established trade routes from the Baltic to Constantinople.", "color": _TEAL},
    {"name": "Constantinople (Viking Varangian Guard)", "lat": 41.0082, "lon": 28.9784, "year": 860, "desc": "Vikings besieged Constantinople in 860. Later, Norse warriors served as the elite Varangian Guard protecting Byzantine emperors.", "color": _VIOLET},
    {"name": "Kaupang", "lat": 59.0500, "lon": 10.0500, "year": 800, "desc": "Norway's first known trading town. Archaeological finds show trade connections from Ireland to the Middle East.", "color": _TEAL},
    {"name": "Roskilde", "lat": 55.6415, "lon": 12.0803, "year": 980, "desc": "Danish royal seat and home of the Viking Ship Museum. Five 11th-century Viking ships were scuttled here to block the fjord.", "color": _TEAL},
    {"name": "Trondheim (Nidaros)", "lat": 63.4305, "lon": 10.3951, "year": 997, "desc": "Founded by Viking king Olav Tryggvason. Became Norway's first capital and the most important city in medieval Norway.", "color": _TEAL},
    {"name": "Staraya Ladoga", "lat": 59.9978, "lon": 32.2942, "year": 750, "desc": "One of the oldest Varangian settlements in Russia. Key waypoint on the trade route from Scandinavia to Byzantium.", "color": _TEAL},
    {"name": "Waterford", "lat": 52.2593, "lon": -7.1101, "year": 914, "desc": "Founded by Vikings as Vedrafjordr. Ireland's oldest city and an important Norse trading port.", "color": _AMBER},
    {"name": "Vinland (approximate)", "lat": 47.0000, "lon": -56.0000, "year": 1000, "desc": "The Norse name for the coast of North America south of L'Anse aux Meadows. Described in the Icelandic sagas as rich in grapes and timber.", "color": _EMERALD},
    {"name": "Danelaw Boundary (Watling Street)", "lat": 52.6300, "lon": -1.1300, "year": 886, "desc": "The treaty boundary between Anglo-Saxon England and the Viking Danelaw, roughly following the old Roman road of Watling Street.", "color": _AMBER},
    {"name": "Gokstad Ship Burial", "lat": 59.1372, "lon": 10.1839, "year": 900, "desc": "One of the finest Viking ship burials ever found. The Gokstad ship could carry 70 warriors and represents the pinnacle of Norse shipbuilding.", "color": _TEAL},
    {"name": "Oseberg Ship Burial", "lat": 59.3058, "lon": 10.2217, "year": 834, "desc": "Lavishly decorated Viking ship burial of two high-status women. Contains the finest collection of Viking Age artifacts ever discovered.", "color": _TEAL},
    {"name": "Jelling", "lat": 55.7567, "lon": 9.4200, "year": 958, "desc": "Royal seat of the Danish Viking kings. The Jelling Stones are Denmark's 'birth certificate' -- runestones erected by Gorm the Old and Harald Bluetooth.", "color": _TEAL},
    {"name": "Lofoten (Borg Viking longhouse)", "lat": 68.2500, "lon": 14.6667, "year": 800, "desc": "The largest Viking longhouse ever found (83m). Chieftain's residence in the Lofoten Islands showing the wealth of northern Norse society.", "color": _TEAL},
    {"name": "Skuldelev (Roskilde Fjord)", "lat": 55.7500, "lon": 11.9833, "year": 1070, "desc": "Five Viking ships deliberately sunk to block the fjord from enemy attack. Recovered and now displayed in the Viking Ship Museum.", "color": _TEAL},
    {"name": "Stamford Bridge", "lat": 53.9900, "lon": -0.9133, "year": 1066, "desc": "Harold Godwinson defeated Harald Hardrada's Viking invasion force. Often considered the end of the Viking Age, three weeks before Hastings.", "color": _RED},
    {"name": "Clontarf", "lat": 53.3631, "lon": -6.2089, "year": 1014, "desc": "Brian Boru defeated the Dublin Norse and their allies, breaking Viking power in Ireland. Brian was killed in his tent after the battle.", "color": _RED},
    {"name": "Baghdad (Viking trade route)", "lat": 33.3152, "lon": 44.3661, "year": 850, "desc": "Viking (Varangian) traders reached Baghdad via Russian rivers. Arab chronicler Ibn Fadlan described meeting the Rus' Vikings on the Volga in 921.", "color": _VIOLET},
]

BARBARY_COAST = [
    {"name": "Algiers", "lat": 36.7538, "lon": 3.0588, "era": "1500-1830", "famous_pirates": "Aruj & Hayreddin Barbarossa", "desc": "Capital of the most powerful Barbary state. The Barbarossa brothers made it the base of their corsair empire under Ottoman protection.", "color": _AMBER},
    {"name": "Tunis", "lat": 36.8065, "lon": 10.1815, "era": "1534-1830", "famous_pirates": "Hayreddin Barbarossa, Dragut", "desc": "Barbarossa captured Tunis for the Ottomans in 1534. Major corsair base that launched raids as far as Iceland.", "color": _AMBER},
    {"name": "Tripoli", "lat": 32.9022, "lon": 13.1800, "era": "1551-1835", "famous_pirates": "Turgut Reis (Dragut)", "desc": "Dragut's stronghold after 1551. The US fought the First Barbary War to end Tripolitan attacks on American shipping.", "color": _AMBER},
    {"name": "Salé", "lat": 34.0389, "lon": -6.8036, "era": "1627-1668", "famous_pirates": "Jan Janszoon (Murad Reis)", "desc": "Independent pirate republic of the Salé Rovers. A Dutch renegade named Jan Janszoon became their admiral and even raided Iceland in 1627.", "color": _RED},
    {"name": "Djerba", "lat": 33.8076, "lon": 10.8451, "era": "1510-1560", "famous_pirates": "Dragut, Barbarossa", "desc": "Island base used by Barbary corsairs. Site of the disastrous Battle of Djerba (1560) where the Ottomans destroyed a Christian fleet.", "color": _RED},
    {"name": "Bougie (Bejaia)", "lat": 36.7528, "lon": 5.0842, "era": "1510-1555", "famous_pirates": "Aruj Barbarossa", "desc": "Aruj Barbarossa captured Bougie and used it as a corsair base before moving to Algiers. He lost his arm fighting the Spanish here.", "color": _AMBER},
    {"name": "Cherchell", "lat": 36.6106, "lon": 2.1922, "era": "1500-1600", "famous_pirates": "Various Barbary corsairs", "desc": "Ancient port city west of Algiers used as a corsair haven. Once the capital of the Roman province of Mauretania.", "color": _AMBER},
    {"name": "Annaba (Bone)", "lat": 36.9000, "lon": 7.7667, "era": "1500-1700", "famous_pirates": "Barbary corsairs", "desc": "Eastern Algerian port used by corsairs. Raided frequently by Spanish and Italian counter-pirates.", "color": _AMBER},
    {"name": "Istanbul (Ottoman HQ)", "lat": 41.0082, "lon": 28.9784, "era": "1500-1800", "famous_pirates": "Hayreddin Barbarossa (Grand Admiral)", "desc": "Hayreddin Barbarossa became Grand Admiral (Kapudan Pasha) of the Ottoman fleet. The Sultan backed corsair operations throughout the Mediterranean.", "color": _VIOLET},
    {"name": "Preveza", "lat": 38.9500, "lon": 20.7500, "era": "1538", "famous_pirates": "Hayreddin Barbarossa", "desc": "Barbarossa's greatest naval victory. He defeated the combined fleets of the Holy League, securing Ottoman dominance of the Mediterranean.", "color": _RED},
    {"name": "Lesbos (Mytilene)", "lat": 39.1000, "lon": 26.5500, "era": "1462-born", "famous_pirates": "Aruj & Hayreddin Barbarossa", "desc": "Birthplace of the Barbarossa brothers on the island of Lesbos. Their father was a retired Ottoman soldier turned potter.", "color": _TEAL},
    {"name": "Malta", "lat": 35.8989, "lon": 14.5146, "era": "1530-1798", "famous_pirates": "Knights of Malta (Christian corsairs)", "desc": "The Knights Hospitaller ran their own Christian corsair operations against Muslim shipping from Malta, mirroring the Barbary pirates.", "color": _BLUE},
    {"name": "Rabat", "lat": 34.0209, "lon": -6.8416, "era": "1627-1700", "famous_pirates": "Moriscos, Salé Rovers", "desc": "Partnered with Salé across the river. Expelled Moriscos from Spain became formidable corsairs here, seeking revenge on Christendom.", "color": _AMBER},
    {"name": "Tunis - La Goulette", "lat": 36.8186, "lon": 10.3050, "era": "1535-1574", "famous_pirates": "Dragut, Uluj Ali", "desc": "Fortress guarding the entrance to Tunis. Changed hands multiple times between Spain and the Ottomans during the corsair wars.", "color": _RED},
    {"name": "Bizerte", "lat": 37.2744, "lon": 9.8739, "era": "1500-1700", "famous_pirates": "Various corsairs", "desc": "Northernmost port in Africa, used as a corsair staging point for raids into the western Mediterranean.", "color": _AMBER},
    {"name": "Mogador (Essaouira)", "lat": 31.5125, "lon": -9.7700, "era": "1600-1800", "famous_pirates": "Barbary corsairs", "desc": "Atlantic Moroccan port used by corsairs preying on European shipping heading to and from West Africa.", "color": _AMBER},
    {"name": "Palermo (Barbary raids)", "lat": 38.1157, "lon": 13.3615, "era": "1500-1700", "famous_pirates": "Raided by Barbarossa", "desc": "Wealthy Sicilian port repeatedly raided by Barbary corsairs. Barbarossa carried off thousands of captives in his raids on Italian coasts.", "color": _RED},
    {"name": "Naples (Barbary raids)", "lat": 40.8518, "lon": 14.2681, "era": "1500-1600", "famous_pirates": "Hayreddin Barbarossa", "desc": "Barbarossa terrorized the Bay of Naples in 1544, capturing thousands of inhabitants from the town of Ischia and nearby settlements.", "color": _RED},
    {"name": "Vestmannaeyjar (Iceland raid)", "lat": 63.4417, "lon": -20.2694, "era": "1627", "famous_pirates": "Murat Reis (Jan Janszoon)", "desc": "Barbary pirates from Salé raided Iceland in 1627, capturing 400+ people and selling them into slavery in North Africa. Called the Turkish Abductions.", "color": _RED},
    {"name": "Baltimore, Ireland (Sack of Baltimore)", "lat": 51.4831, "lon": -9.3694, "era": "1631", "famous_pirates": "Murat Reis (Jan Janszoon)", "desc": "Barbary pirates raided the Irish village of Baltimore, carrying off over 100 villagers to slavery in Algiers. Only 2 ever returned.", "color": _RED},
    {"name": "Vieste, Italy", "lat": 41.8819, "lon": 16.1767, "era": "1554", "famous_pirates": "Dragut (Turgut Reis)", "desc": "Dragut sacked Vieste on the Gargano peninsula, massacring inhabitants and enslaving thousands. The bloodstained rock (Chianca Amara) still stands.", "color": _RED},
    {"name": "Decatur at Tripoli", "lat": 32.9022, "lon": 13.1800, "era": "1804", "famous_pirates": "Stephen Decatur (US Navy)", "desc": "Lt. Decatur led a daring raid to burn the captured USS Philadelphia in Tripoli harbor. Nelson called it 'the most bold and daring act of the age.'", "color": _BLUE},
    {"name": "Bombardment of Algiers", "lat": 36.7538, "lon": 3.0588, "era": "1816", "famous_pirates": "Anglo-Dutch fleet vs Algiers", "desc": "A combined British-Dutch fleet bombarded Algiers, freeing over 3,000 Christian slaves and forcing the Dey to end Christian slavery.", "color": _BLUE},
    {"name": "French conquest of Algiers", "lat": 36.7538, "lon": 3.0588, "era": "1830", "famous_pirates": "End of Barbary piracy", "desc": "France invaded and conquered Algiers in 1830, permanently ending over 300 years of Barbary corsair operations in the Mediterranean.", "color": _BLUE},
    {"name": "Mahon, Menorca", "lat": 39.8885, "lon": 4.2658, "era": "1535", "famous_pirates": "Hayreddin Barbarossa", "desc": "Barbarossa raided Mahon in 1535, carrying off the entire population of the old town. One of the most devastating Barbary raids on Spanish territory.", "color": _RED},
]

EAST_ASIAN_PIRATES = [
    {"name": "Kowloon (Cheung Po Tsai Cave)", "lat": 22.2149, "lon": 114.0100, "era": "1783-1822", "famous_pirates": "Cheung Po Tsai", "desc": "Adopted son and successor of Ching Shih. Commanded 600 ships before accepting an amnesty and becoming a colonel in the Qing navy.", "color": _AMBER},
    {"name": "Guangzhou (Canton)", "lat": 23.1291, "lon": 113.2644, "era": "1800-1810", "famous_pirates": "Ching Shih (Madame Ching)", "desc": "Ching Shih commanded the Red Flag Fleet of 1,800 vessels and 80,000 pirates -- the largest pirate armada in history. She retired rich and respected.", "color": _RED},
    {"name": "Hakata Bay", "lat": 33.5902, "lon": 130.4017, "era": "1274-1281", "famous_pirates": "Wako (Japanese pirates)", "desc": "Target of Mongol invasions that were destroyed by typhoons (kamikaze). Wako pirates later terrorized Chinese and Korean coasts for centuries.", "color": _AMBER},
    {"name": "Hirado Island", "lat": 33.3644, "lon": 129.5467, "era": "1500-1600", "famous_pirates": "Wako pirates, Matsuura clan", "desc": "Base for wako pirates who raided the Chinese coast during the Ming dynasty. Later became one of Japan's first international trading ports.", "color": _AMBER},
    {"name": "Kinmen (Quemoy)", "lat": 24.4500, "lon": 118.3833, "era": "1620-1662", "famous_pirates": "Zheng Zhilong, Koxinga", "desc": "Base of the Zheng family maritime empire. Zheng Zhilong was the richest pirate in Chinese history; his son Koxinga conquered Taiwan.", "color": _RED},
    {"name": "Tainan (Fort Zeelandia)", "lat": 23.0000, "lon": 120.2269, "era": "1624-1662", "famous_pirates": "Koxinga (Zheng Chenggong)", "desc": "Koxinga expelled the Dutch from Taiwan in 1662 and established a Chinese kingdom. Son of pirate lord Zheng Zhilong.", "color": _RED},
    {"name": "Sulu Archipelago", "lat": 6.0000, "lon": 121.0000, "era": "1600-1900", "famous_pirates": "Moro pirates", "desc": "The Sulu pirates dominated Southeast Asian waters for centuries, raiding as far as the Philippines, Borneo, and the Malay Peninsula.", "color": _AMBER},
    {"name": "Riau Islands", "lat": 0.9000, "lon": 104.4500, "era": "1300-1800", "famous_pirates": "Orang Laut (Sea People)", "desc": "Malay sea nomads who served as naval forces for various sultanates and engaged in piracy throughout the Strait of Malacca.", "color": _AMBER},
    {"name": "Hai Phong", "lat": 20.8449, "lon": 106.6881, "era": "1790-1810", "famous_pirates": "Tay Son pirates, Ching Shih", "desc": "Vietnamese pirates allied with the Tay Son rebellion. Ching Shih's fleet operated extensively in the Gulf of Tonkin.", "color": _RED},
    {"name": "Zhoushan Islands", "lat": 30.0000, "lon": 122.1000, "era": "1500-1600", "famous_pirates": "Wang Zhi, Xu Hai", "desc": "Major wako pirate base during the Ming dynasty. Wang Zhi commanded a fleet of hundreds of ships and traded with Japan.", "color": _AMBER},
    {"name": "Palawan", "lat": 9.8349, "lon": 118.7384, "era": "1600-1800", "famous_pirates": "Moro raiders", "desc": "Strategic island used by Moro pirates for raiding Spanish colonial shipping between Manila and the Spice Islands.", "color": _AMBER},
    {"name": "Macau", "lat": 22.1987, "lon": 113.5439, "era": "1550-1810", "famous_pirates": "Various Chinese pirates", "desc": "Portuguese trading port constantly threatened by Chinese pirate fleets. Major target for Ching Shih's Red Flag Fleet.", "color": _AMBER},
    {"name": "Hong Kong (Lantau Island)", "lat": 22.2600, "lon": 113.9400, "era": "1800-1810", "famous_pirates": "Ching Shih, Cheung Po Tsai", "desc": "The islands around Hong Kong were prime pirate territory. Caves on Lantau and Cheung Chau served as hideouts for pirate fleets.", "color": _AMBER},
    {"name": "Strait of Malacca", "lat": 2.5000, "lon": 101.5000, "era": "1400-present", "famous_pirates": "Various", "desc": "One of the world's busiest and most pirate-infested waterways. Piracy here has continued from ancient times to the modern era.", "color": _RED},
    {"name": "Manila Bay", "lat": 14.5500, "lon": 120.7500, "era": "1570-1800", "famous_pirates": "Limahong, various", "desc": "Chinese pirate Limahong attacked Manila in 1574 with 62 ships. The Philippines were repeatedly raided by Chinese, Japanese, and Moro pirates.", "color": _RED},
    {"name": "Nagasaki", "lat": 32.7503, "lon": 129.8779, "era": "1500-1600", "famous_pirates": "Wako pirates", "desc": "Wako pirates operated from harbors around Nagasaki. The city later became Japan's main port for foreign trade.", "color": _AMBER},
    {"name": "Hainan Island", "lat": 19.2000, "lon": 109.7000, "era": "1780-1810", "famous_pirates": "Red Flag Fleet", "desc": "Ching Shih's pirates dominated the waters around Hainan, extracting protection money from fishing villages and merchant ships.", "color": _RED},
    {"name": "Xiamen (Amoy)", "lat": 24.4798, "lon": 118.0894, "era": "1620-1680", "famous_pirates": "Zheng Zhilong, Koxinga", "desc": "Key port of the Zheng family maritime empire. From here they controlled much of the China Sea trade.", "color": _RED},
    {"name": "Brunei", "lat": 4.9431, "lon": 114.9425, "era": "1500-1800", "famous_pirates": "Illanun pirates", "desc": "The Illanun pirates of Borneo were feared throughout Southeast Asia. They raided for slaves and goods across a vast maritime territory.", "color": _AMBER},
    {"name": "Tsushima Island", "lat": 34.4167, "lon": 129.3333, "era": "1350-1500", "famous_pirates": "Wako pirates", "desc": "Strategic island between Japan and Korea used as a wako pirate base. The Joseon dynasty launched punitive expeditions against them.", "color": _AMBER},
    {"name": "Bias Bay (Daya Bay)", "lat": 22.6000, "lon": 114.5500, "era": "1920-1930", "famous_pirates": "Lai Choi San", "desc": "Notorious 20th-century pirate queen who commanded a fleet of junks. She was documented by Finnish adventurer Aleko Lilius in the 1920s.", "color": _RED},
    {"name": "Mekong Delta", "lat": 10.0000, "lon": 106.0000, "era": "1700-1800", "famous_pirates": "Vietnamese river pirates", "desc": "The labyrinthine waterways of the Mekong Delta provided perfect cover for river pirates preying on trade between Cambodia and the sea.", "color": _AMBER},
    {"name": "Takao (Kaohsiung)", "lat": 22.6273, "lon": 120.3014, "era": "1620-1680", "famous_pirates": "Koxinga", "desc": "Port used by Koxinga during his campaign to expel the Dutch from Taiwan. His pirate-descended dynasty ruled Taiwan for 23 years.", "color": _RED},
    {"name": "Vladivostok (Manchurian pirates)", "lat": 43.1332, "lon": 131.9113, "era": "1850-1900", "famous_pirates": "Manchurian & Korean pirates", "desc": "Northern Pacific piracy targeted Russian and Japanese shipping in the Sea of Japan during the late 19th century.", "color": _AMBER},
    {"name": "Singapore Strait", "lat": 1.2500, "lon": 103.8500, "era": "1300-present", "famous_pirates": "Various", "desc": "Narrow strait between Singapore and Indonesia's Riau Islands. Piracy hotspot from ancient times through the modern era.", "color": _RED},
]

PRIVATEERS_CORSAIRS = [
    {"name": "Plymouth, England", "lat": 50.3755, "lon": -4.1427, "era": "1570-1596", "famous_pirates": "Sir Francis Drake", "desc": "Home port of Drake, England's most famous privateer. He circumnavigated the globe and plundered Spanish treasure worth billions in today's money.", "color": _BLUE},
    {"name": "Brest, France", "lat": 48.3904, "lon": -4.4861, "era": "1690-1715", "famous_pirates": "Jean Bart, Duguay-Trouin", "desc": "Home port of France's greatest corsairs during the wars of Louis XIV. Jean Bart was so successful he was ennobled by the king.", "color": _BLUE},
    {"name": "Flushing (Vlissingen)", "lat": 51.4427, "lon": 3.5709, "era": "1568-1648", "famous_pirates": "Sea Beggars (Watergeuzen)", "desc": "Base of the Sea Beggars, Dutch Protestant privateers who fought against Spanish rule. Their capture of Brielle in 1572 sparked the Dutch Revolt.", "color": _EMERALD},
    {"name": "Dunkirk", "lat": 51.0383, "lon": 2.3775, "era": "1580-1715", "famous_pirates": "Dunkirk Privateers, Jean Bart", "desc": "Feared privateering base that preyed on English and Dutch shipping. Jean Bart captured the entire Dutch grain fleet in 1694.", "color": _BLUE},
    {"name": "Salem, Massachusetts", "lat": 42.5195, "lon": -70.8967, "era": "1775-1815", "famous_pirates": "American privateers", "desc": "Salem sent out more privateers than any other American port during the Revolution and War of 1812. Some captains became fabulously wealthy.", "color": _BLUE},
    {"name": "Nombre de Dios (Drake's raid)", "lat": 9.5750, "lon": -79.4753, "era": "1572", "famous_pirates": "Sir Francis Drake", "desc": "Drake's audacious raid on the Spanish treasure port. He captured a mule train carrying Peruvian silver across the Isthmus of Panama.", "color": _GOLD},
    {"name": "Cartagena de Indias", "lat": 10.3910, "lon": -75.5144, "era": "1586", "famous_pirates": "Sir Francis Drake", "desc": "Drake sacked Spain's wealthiest New World city with a fleet of 23 ships. He held the city for ransom, demanding 107,000 ducats.", "color": _GOLD},
    {"name": "Baltimore, Maryland", "lat": 39.2904, "lon": -76.6122, "era": "1812-1815", "famous_pirates": "Thomas Boyle", "desc": "Boyle's Chasseur was the most successful privateer of the War of 1812. He audaciously proclaimed a blockade of the entire British Isles.", "color": _BLUE},
    {"name": "Cadiz, Spain (Drake's raid)", "lat": 36.5271, "lon": -6.2886, "era": "1587", "famous_pirates": "Sir Francis Drake", "desc": "Drake 'singed the King of Spain's beard' by destroying over 30 ships in Cadiz harbor, delaying the Spanish Armada by a year.", "color": _GOLD},
    {"name": "Buenos Aires", "lat": -34.6037, "lon": -58.3816, "era": "1810-1830", "famous_pirates": "Hipolito Bouchard", "desc": "Argentine privateer who circumnavigated the globe raiding Spanish shipping. He even attacked the coast of California in 1818.", "color": _BLUE},
    {"name": "Newport, Rhode Island", "lat": 41.4901, "lon": -71.3128, "era": "1690-1725", "famous_pirates": "Thomas Tew", "desc": "Newport privateer Thomas Tew pioneered the 'Pirate Round' -- sailing from America to the Indian Ocean to prey on Mughal treasure ships.", "color": _AMBER},
    {"name": "La Rochelle", "lat": 46.1591, "lon": -1.1520, "era": "1550-1630", "famous_pirates": "Huguenot privateers", "desc": "French Protestant stronghold whose privateers raided Catholic shipping. The famous siege of 1627-28 ended their maritime independence.", "color": _BLUE},
    {"name": "Livorno (Leghorn)", "lat": 43.5485, "lon": 10.3106, "era": "1600-1700", "famous_pirates": "Knights of St. Stephen", "desc": "Tuscany's corsair order preyed on Ottoman and Barbary shipping from Livorno. Authorized piracy under the banner of Christian warfare.", "color": _BLUE},
    {"name": "Valetta, Malta", "lat": 35.8989, "lon": 14.5146, "era": "1530-1798", "famous_pirates": "Knights of Malta (Hospitaller)", "desc": "The Knights Hospitaller were the most organized Christian corsairs. Their corso operations against Muslim shipping were highly profitable.", "color": _BLUE},
    {"name": "Rio de Janeiro (corsair port)", "lat": -22.9068, "lon": -43.1729, "era": "1710-1712", "famous_pirates": "Rene Duguay-Trouin", "desc": "Duguay-Trouin captured Rio de Janeiro with a fleet of corsair ships in 1711, holding the city for ransom. One of the greatest corsair feats.", "color": _GOLD},
    {"name": "Port of Bordeaux", "lat": 44.8378, "lon": -0.5792, "era": "1700-1815", "famous_pirates": "French corsairs", "desc": "Important corsair port in southwestern France. Bordeaux privateers preyed on British merchant shipping during multiple wars.", "color": _BLUE},
    {"name": "Guayaquil", "lat": -2.1710, "lon": -79.9224, "era": "1687", "famous_pirates": "Woodes Rogers, William Dampier", "desc": "Rogers and Dampier sacked this wealthy South American port during their privateering voyage around the world (1708-1711).", "color": _GOLD},
    {"name": "Manila Galleon Route (Acapulco)", "lat": 16.8531, "lon": -99.8237, "era": "1587", "famous_pirates": "Thomas Cavendish", "desc": "Cavendish captured the Manila Galleon Santa Ana off Baja California -- one of the richest prizes ever taken by an English privateer.", "color": _GOLD},
    {"name": "Saint-Nazaire (corsair base)", "lat": 47.2736, "lon": -2.2137, "era": "1690-1815", "famous_pirates": "French corsairs", "desc": "Atlantic corsair port that launched raids on British commerce during the wars of the 17th and 18th centuries.", "color": _BLUE},
    {"name": "Ushant (Channel patrol)", "lat": 48.4500, "lon": -5.1000, "era": "1700-1815", "famous_pirates": "Various privateers", "desc": "Key patrol area in the western English Channel. Privateers from both sides lurked near Ushant waiting for merchantmen.", "color": _BLUE},
    {"name": "Havana (Drake's approach)", "lat": 23.1136, "lon": -82.3666, "era": "1590-1620", "famous_pirates": "Drake, Piet Hein", "desc": "Spain's most fortified Caribbean port. Dutch privateer Piet Hein captured the entire Spanish Silver Fleet off Havana in 1628.", "color": _GOLD},
    {"name": "Isle of Man", "lat": 54.2361, "lon": -4.5481, "era": "1600-1700", "famous_pirates": "Manx privateers", "desc": "The Isle of Man's independent status made it a convenient base for privateering and smuggling operations in the Irish Sea.", "color": _BLUE},
    {"name": "Vera Cruz (San Juan de Ulua)", "lat": 19.2000, "lon": -96.1500, "era": "1568", "famous_pirates": "John Hawkins, Francis Drake", "desc": "Spanish betrayal at San Juan de Ulua in 1568 sparked England's war of privateering against Spain. Young Drake swore vengeance.", "color": _RED},
    {"name": "Aden (Red Sea route)", "lat": 12.7855, "lon": 45.0187, "era": "1690-1700", "famous_pirates": "Thomas Tew, Henry Every", "desc": "Mouth of the Red Sea where English pirates from America intercepted Mughal pilgrim and treasure ships heading to Mecca.", "color": _AMBER},
    {"name": "Martinique (Fort-de-France)", "lat": 14.6167, "lon": -61.0500, "era": "1650-1815", "famous_pirates": "French corsairs", "desc": "Caribbean base for French privateers who raided English and Spanish shipping. Letters of marque were freely distributed during wartime.", "color": _BLUE},
]

MARITIME_MUSEUMS = [
    {"name": "National Maritime Museum", "lat": 51.4810, "lon": -0.0054, "city": "Greenwich, London", "highlights": "Nelson's uniform, maritime art, navigation instruments", "desc": "World's largest maritime museum. Houses Nelson's blood-stained uniform from Trafalgar and an unparalleled collection of maritime art.", "color": _EMERALD},
    {"name": "Vasa Museum", "lat": 59.3280, "lon": 18.0914, "city": "Stockholm, Sweden", "highlights": "Intact 17th-century warship Vasa", "desc": "Home to the almost perfectly intact Vasa warship, which sank on its maiden voyage in 1628 and was raised in 1961.", "color": _EMERALD},
    {"name": "Whydah Pirate Museum", "lat": 41.6555, "lon": -70.1704, "city": "West Yarmouth, Massachusetts", "highlights": "Only authenticated pirate shipwreck artifacts", "desc": "Displays artifacts from Black Sam Bellamy's Whydah Gally -- the only verified pirate shipwreck. Thousands of artifacts including the ship's bell.", "color": _RED},
    {"name": "Pirates of Nassau Museum", "lat": 25.0780, "lon": -77.3440, "city": "Nassau, Bahamas", "highlights": "Golden Age pirate history, replica ship", "desc": "Interactive museum in the former pirate capital. Features a full-size replica pirate ship and recreations of 18th-century Nassau.", "color": _AMBER},
    {"name": "St. Augustine Pirate & Treasure Museum", "lat": 29.8921, "lon": -81.3114, "city": "St. Augustine, Florida", "highlights": "One of only two Jolly Roger flags in existence", "desc": "Houses one of the world's only authentic pirate flags and the oldest wanted poster for a pirate. Over 800 artifacts.", "color": _AMBER},
    {"name": "Viking Ship Museum (Roskilde)", "lat": 55.6506, "lon": 12.0808, "city": "Roskilde, Denmark", "highlights": "Five original Viking ships", "desc": "Five Viking ships recovered from Roskilde Fjord where they were deliberately sunk around 1070. Active boatbuilding yard.", "color": _TEAL},
    {"name": "Viking Ship Museum (Oslo)", "lat": 59.9048, "lon": 10.6844, "city": "Oslo, Norway", "highlights": "Oseberg and Gokstad ships", "desc": "Home to the world's best-preserved Viking ships -- the ornate Oseberg ship and the seagoing Gokstad ship.", "color": _TEAL},
    {"name": "Museo Naval", "lat": 40.4151, "lon": -3.6930, "city": "Madrid, Spain", "highlights": "Spanish Armada, colonial navigation", "desc": "Spain's national naval museum. Contains the first map to show the Americas and extensive collections from the Age of Exploration.", "color": _EMERALD},
    {"name": "Musee de la Marine", "lat": 48.8625, "lon": 2.2876, "city": "Paris, France", "highlights": "French naval history, ship models", "desc": "One of the oldest maritime museums in the world. Exceptional collection of ship models, navigational instruments, and naval art.", "color": _EMERALD},
    {"name": "Mary Rose Museum", "lat": 50.8009, "lon": -1.1098, "city": "Portsmouth, England", "highlights": "Henry VIII's warship Mary Rose", "desc": "Purpose-built museum housing the hull of the Mary Rose (sunk 1545, raised 1982) and 19,000 Tudor-era artifacts.", "color": _EMERALD},
    {"name": "National Museum of the Royal Navy", "lat": 50.7989, "lon": -1.1083, "city": "Portsmouth, England", "highlights": "HMS Victory, HMS Warrior", "desc": "Home to Nelson's flagship HMS Victory and the world's first iron-hulled warship HMS Warrior. Located in Portsmouth Historic Dockyard.", "color": _BLUE},
    {"name": "Mystic Seaport Museum", "lat": 41.3615, "lon": -71.9662, "city": "Mystic, Connecticut", "highlights": "Charles W. Morgan whaling ship, maritime village", "desc": "America's leading maritime museum. Home to the Charles W. Morgan (1841), the last surviving wooden whaling ship.", "color": _EMERALD},
    {"name": "Maritime Museum of Barcelona", "lat": 41.3755, "lon": 2.1746, "city": "Barcelona, Spain", "highlights": "Full-size replica of Don Juan of Austria's galley", "desc": "Housed in the medieval Royal Shipyards (Drassanes). Features a full-scale replica of the galley that fought at Lepanto.", "color": _EMERALD},
    {"name": "Scheepvaartmuseum", "lat": 52.3717, "lon": 4.9153, "city": "Amsterdam, Netherlands", "highlights": "VOC ship replica, Dutch Golden Age maritime", "desc": "National Maritime Museum in a former naval storehouse. Full-size replica of the VOC ship Amsterdam and 500,000+ artifacts.", "color": _EMERALD},
    {"name": "San Diego Maritime Museum", "lat": 32.7208, "lon": -117.1751, "city": "San Diego, California", "highlights": "Star of India (1863), HMS Surprise replica", "desc": "Fleet of historic ships including the Star of India, the world's oldest active sailing ship, and the HMS Surprise from Master and Commander.", "color": _EMERALD},
    {"name": "Australian National Maritime Museum", "lat": -33.8694, "lon": 151.1988, "city": "Sydney, Australia", "highlights": "HMB Endeavour replica, Vampire destroyer", "desc": "Waterfront museum with a replica of Cook's Endeavour, HMAS Vampire destroyer, and extensive Indigenous maritime heritage collection.", "color": _EMERALD},
    {"name": "Batavia Shipwreck Gallery", "lat": -28.7757, "lon": 114.6150, "city": "Geraldton, Western Australia", "highlights": "Batavia wreck artifacts, reconstructed stern", "desc": "Houses the reconstructed stern section of the VOC ship Batavia (wrecked 1629) and artifacts from one of history's most horrific mutinies.", "color": _RED},
    {"name": "KonTiki Museum", "lat": 59.9042, "lon": 10.6986, "city": "Oslo, Norway", "highlights": "Thor Heyerdahl's Kon-Tiki and Ra II rafts", "desc": "Houses Thor Heyerdahl's original Kon-Tiki balsa raft and the papyrus boat Ra II, proving ancient maritime contacts were possible.", "color": _EMERALD},
    {"name": "Cutty Sark", "lat": 51.4826, "lon": -0.0116, "city": "Greenwich, London", "highlights": "Last surviving tea clipper", "desc": "The world's sole surviving tea clipper, built in 1869. Beautifully restored and displayed in a glass 'dry dock' at Greenwich.", "color": _EMERALD},
    {"name": "USS Constitution Museum", "lat": 42.3725, "lon": -71.0567, "city": "Boston, Massachusetts", "highlights": "Old Ironsides, oldest commissioned warship afloat", "desc": "America's Ship of State -- launched in 1797, she famously defeated five British warships in the War of 1812. Still commissioned.", "color": _BLUE},
    {"name": "Deutsches Schifffahrtsmuseum", "lat": 53.5400, "lon": 8.5800, "city": "Bremerhaven, Germany", "highlights": "Hanseatic cog from 1380, U-boat", "desc": "German Maritime Museum with a medieval Hanseatic cog excavated from the Weser River and a Type XXI U-boat.", "color": _EMERALD},
    {"name": "Museo Storico Navale", "lat": 45.4337, "lon": 12.3472, "city": "Venice, Italy", "highlights": "Venetian galley models, Bucentaur model", "desc": "Venice's naval museum in the Arsenale. Models of the legendary Venetian war galleys and the Doge's ceremonial barge.", "color": _EMERALD},
    {"name": "Port Royal Heritage Site", "lat": 17.9362, "lon": -76.8412, "city": "Port Royal, Jamaica", "highlights": "Sunken pirate city archaeological site", "desc": "The submerged remains of the 'Wickedest City on Earth.' Ongoing underwater archaeology reveals the pirate capital destroyed by earthquake in 1692.", "color": _AMBER},
    {"name": "Queen Anne's Revenge Shipwreck Lab", "lat": 34.7212, "lon": -76.6705, "city": "Beaufort, North Carolina", "highlights": "Blackbeard's flagship artifacts", "desc": "Conservation lab where artifacts from Blackbeard's Queen Anne's Revenge are preserved. Cannons, anchors, gold dust, and medical instruments.", "color": _RED},
    {"name": "Mel Fisher Maritime Museum", "lat": 24.5615, "lon": -81.8073, "city": "Key West, Florida", "highlights": "Nuestra Senora de Atocha treasure", "desc": "Displays treasure from the Atocha and Santa Margarita -- emeralds, gold bars, silver coins, and a 77-carat emerald.", "color": _GOLD},
    {"name": "Jangsaengpo Whale Museum", "lat": 35.4907, "lon": 129.3833, "city": "Ulsan, South Korea", "highlights": "Asian maritime & whaling heritage", "desc": "Korea's unique maritime museum focused on the ancient whaling traditions of the region, with Bangudae Petroglyphs connections.", "color": _EMERALD},
]

SMUGGLING_ROUTES = [
    {"name": "Smugglers' Cove (Lulworth)", "lat": 50.6167, "lon": -2.2333, "era": "1700-1850", "goods": "Brandy, silk, tea", "desc": "Hidden cove on the Dorset coast used extensively by English smugglers. Secret tunnels connected the beach to clifftop inns.", "color": _VIOLET},
    {"name": "Hawkhurst Gang Territory", "lat": 51.0500, "lon": 0.5333, "era": "1735-1749", "goods": "Tea, brandy, tobacco", "desc": "The Hawkhurst Gang was England's most violent smuggling gang, controlling the Sussex and Kent coast. They murdered rivals and informers openly.", "color": _RED},
    {"name": "Polperro, Cornwall", "lat": 50.3333, "lon": -4.5167, "era": "1700-1850", "goods": "Brandy, gin, tobacco", "desc": "Quintessential Cornish smuggling village. The entire community participated -- from fishermen to the local parson. A smuggling museum exists today.", "color": _VIOLET},
    {"name": "Jamaica Inn (Bodmin Moor)", "lat": 50.5614, "lon": -4.5831, "era": "1750-1850", "goods": "Brandy, silk, tobacco", "desc": "Coaching inn on Bodmin Moor made famous by Daphne du Maurier's novel. Served as a staging post for smuggled goods moving inland.", "color": _VIOLET},
    {"name": "Deal, Kent", "lat": 51.2242, "lon": 1.4006, "era": "1700-1800", "goods": "Brandy, lace, tea", "desc": "Notorious smuggling port where goods were landed by 'hovellers' and carried through tunnels under the town to secret warehouses.", "color": _VIOLET},
    {"name": "Caves of Matala, Crete", "lat": 34.9936, "lon": 24.7500, "era": "Ancient-1800s", "goods": "Various contraband", "desc": "Ancient Roman-era caves on the Cretan coast later used by pirates and smugglers for centuries. Now a tourist attraction.", "color": _VIOLET},
    {"name": "Bahia de Cochinos (Bay of Pigs)", "lat": 22.0833, "lon": -81.1500, "era": "1700-1900", "goods": "Rum, slaves, tobacco", "desc": "Remote Cuban bay used by smugglers and pirates long before the famous 1961 invasion. Its isolation made it ideal for illicit trade.", "color": _VIOLET},
    {"name": "Strait of Messina", "lat": 38.2000, "lon": 15.6000, "era": "Ancient-1800s", "goods": "Various contraband", "desc": "Narrow strait between Sicily and mainland Italy. Smugglers exploited the treacherous currents that also inspired the myths of Scylla and Charybdis.", "color": _VIOLET},
    {"name": "Clovelly, Devon", "lat": 50.9989, "lon": -4.4003, "era": "1700-1850", "goods": "Brandy, tobacco, silk", "desc": "Steep cobbled fishing village on the Devon coast. Its inaccessibility made it perfect for landing contraband away from revenue officers.", "color": _VIOLET},
    {"name": "Beer, Devon", "lat": 50.6956, "lon": -3.0922, "era": "1700-1850", "goods": "Brandy, lace, spirits", "desc": "Jack Rattenbury, the 'Rob Roy of the West,' led smuggling operations from Beer's caves and beach for decades.", "color": _VIOLET},
    {"name": "Isle of Wight (The Needles)", "lat": 50.6625, "lon": -1.5883, "era": "1700-1800", "goods": "Brandy, silk, tobacco", "desc": "Chalk stacks at the western tip of the Isle of Wight. Smugglers used hidden caves and coves nearby to land French contraband.", "color": _VIOLET},
    {"name": "Roscoff, Brittany", "lat": 48.7267, "lon": -3.9867, "era": "1700-1850", "goods": "Brandy, wine, onions", "desc": "French port that was the main source of smuggled goods heading to Cornwall and Devon. The 'Johnnies' (onion sellers) were a cover story.", "color": _VIOLET},
    {"name": "Guernsey & Jersey", "lat": 49.4542, "lon": -2.5367, "era": "1700-1850", "goods": "Brandy, tobacco, tea", "desc": "Channel Islands served as a massive tax-free warehouse for contraband destined for England. Smuggling was the islands' main industry.", "color": _VIOLET},
    {"name": "Gibraltar", "lat": 36.1408, "lon": -5.3536, "era": "1713-present", "goods": "Tobacco, alcohol, various", "desc": "Strategic rock controlling the Mediterranean entrance. Its tax-free status has made it a smuggling hub for over 300 years.", "color": _VIOLET},
    {"name": "Tangier", "lat": 35.7595, "lon": -5.8340, "era": "1700-1960", "goods": "Hashish, guns, people", "desc": "International zone city across from Gibraltar. Its lawless reputation made it a center for smuggling of every kind.", "color": _RED},
    {"name": "Rum Row (New York)", "lat": 40.4800, "lon": -73.6000, "era": "1920-1933", "goods": "Alcohol (Prohibition)", "desc": "During Prohibition, ships anchored just outside US territorial waters selling liquor to speedboat 'rum runners' who dashed for shore.", "color": _AMBER},
    {"name": "Bimini, Bahamas", "lat": 25.7264, "lon": -79.2706, "era": "1920-1933", "goods": "Rum, whiskey (Prohibition)", "desc": "Closest Bahamian island to the US mainland. Major staging point for Prohibition rum-runners. Ernest Hemingway was a frequent visitor.", "color": _AMBER},
    {"name": "St. Pierre and Miquelon", "lat": 46.7787, "lon": -56.1733, "era": "1920-1933", "goods": "Canadian whiskey, French wines", "desc": "French islands off Newfoundland became a massive Prohibition-era liquor warehouse. Al Capone allegedly visited to arrange shipments.", "color": _AMBER},
    {"name": "Dunhuang (Silk Road smuggling)", "lat": 40.1421, "lon": 94.6619, "era": "Ancient-1900s", "goods": "Silk, jade, manuscripts", "desc": "Silk Road oasis city where contraband and untaxed goods flowed for millennia. Aurel Stein 'acquired' priceless manuscripts from its caves.", "color": _GOLD},
    {"name": "Opium Trail (Calcutta)", "lat": 22.5726, "lon": 88.3639, "era": "1770-1910", "goods": "Opium", "desc": "British East India Company shipped opium from Bengal to China, sparking the Opium Wars. Calcutta was the starting point of the trade.", "color": _RED},
    {"name": "Canton (Opium trade)", "lat": 23.1291, "lon": 113.2644, "era": "1800-1860", "goods": "Opium", "desc": "Receiving end of the opium trade. Chinese attempts to stop smuggling led to the Opium Wars and the ceding of Hong Kong to Britain.", "color": _RED},
    {"name": "Tortola (smuggling haven)", "lat": 18.4317, "lon": -64.6400, "era": "1700-1900", "goods": "Slaves, rum, sugar", "desc": "The intricate channels of the British Virgin Islands made them ideal for avoiding customs. Smuggling was an accepted way of life.", "color": _VIOLET},
    {"name": "Ile de Re (salt smuggling)", "lat": 46.2022, "lon": -1.3736, "era": "1300-1789", "goods": "Salt", "desc": "Salt smuggling (faux-saunage) was big business in France, where the gabelle tax made salt ruinously expensive. Thousands were imprisoned for it.", "color": _VIOLET},
    {"name": "Monte Carlo (post-WWII)", "lat": 43.7384, "lon": 7.4246, "era": "1945-1970", "goods": "Cigarettes, gold, currency", "desc": "Monaco's tax-free status made it a hub for post-war smuggling of American cigarettes, gold, and currency into France and Italy.", "color": _VIOLET},
    {"name": "Naxos, Greece", "lat": 37.1036, "lon": 25.3761, "era": "1700-1900", "goods": "Emery, contraband", "desc": "Greek island whose remote coves were used by smugglers avoiding Ottoman customs. Also a pirate hideout in earlier centuries.", "color": _VIOLET},
    {"name": "Cherbourg", "lat": 49.6337, "lon": -1.6222, "era": "1700-1850", "goods": "Brandy, silk, lace", "desc": "Norman port across the Channel from southern England. Smuggling boats made the crossing on dark nights, evading revenue cutters.", "color": _VIOLET},
]

# ═══════════════════════════════════════════════════════════════════════════════
# POPUP BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def _popup(title, fields, desc, color):
    """Build an HTML popup for folium markers."""
    esc = html_module.escape
    rows = "".join(
        f"<tr><td style='padding:3px 8px;color:#8b97b0;font-size:12px;'>{esc(str(k))}</td>"
        f"<td style='padding:3px 8px;color:#e8ecf4;font-size:12px;'>{esc(str(v))}</td></tr>"
        for k, v in fields.items() if v
    )
    return f"""
    <div style="font-family:Inter,Arial,sans-serif;max-width:320px;background:#111827;
                border:1px solid {color};border-radius:10px;padding:12px;">
        <h4 style="margin:0 0 8px;color:{color};font-size:14px;">{esc(title)}</h4>
        <table style="width:100%;border-collapse:collapse;">{rows}</table>
        <p style="margin:8px 0 0;color:#8b97b0;font-size:11px;line-height:1.4;">{esc(desc)}</p>
    </div>
    """

# ═══════════════════════════════════════════════════════════════════════════════
# MAP BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def _build_map(data, field_keys, center=None, zoom=3):
    """Build a folium map with markers for the given data."""
    if not data:
        return None
    if center is None:
        lats = [d["lat"] for d in data]
        lons = [d["lon"] for d in data]
        center = [sum(lats) / len(lats), sum(lons) / len(lons)]
    m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB dark_matter",
                   width="100%", height="100%")
    for item in data:
        fields = {k: item.get(k, "") for k in field_keys}
        popup_html = _popup(item["name"], fields, item.get("desc", ""), item.get("color", _ACCENT))
        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=7,
            color=item.get("color", _ACCENT),
            fill=True,
            fill_color=item.get("color", _ACCENT),
            fill_opacity=0.7,
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=item["name"],
        ).add_to(m)
    return m


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def render_pirate_maps_tab():
    """Render the Pirates & Maritime History Explorer tab."""

    st.markdown(
        '<div class="tab-header amber">'
        '<h4>Pirates & Maritime History Explorer</h4>'
        '<p>Pirate havens, famous shipwrecks, naval battles & maritime legends</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox("Select Map Mode", [
        "Golden Age Pirate Havens",
        "Famous Shipwrecks",
        "Naval Battle Sites",
        "Treasure Map Legends",
        "Viking Sea Routes",
        "Barbary Coast Pirates",
        "East Asian Pirates",
        "Privateers & Corsairs",
        "Maritime Museums",
        "Smuggling Routes & Hideouts",
    ], key="pirate_maps_mode")

    # Show mode description
    desc = MODE_DESCRIPTIONS.get(mode, "")
    if desc:
        st.info(desc)

    st.markdown("---")

    # ── Golden Age Pirate Havens ──────────────────────────────────────────────
    if mode == "Golden Age Pirate Havens":
        data = GOLDEN_AGE_HAVENS
        st.markdown("#### Golden Age Pirate Havens (c. 1650-1730)")
        st.caption("Ports, islands, and hideouts of the buccaneers and pirates who terrorized the seas during piracy's Golden Age.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Pirate Havens", len(data))
        caribbean = sum(1 for d in data if d["lon"] < -60 and d["lat"] > 10 and d["lat"] < 30)
        c2.metric("Caribbean Bases", caribbean)
        african = sum(1 for d in data if d["lon"] > 30 and d["lat"] < 0)
        c3.metric("African / Indian Ocean", african)
        c4.metric("Countries Covered", len(set(d["country"] for d in data)))
        m = _build_map(data, ["country", "era", "famous_pirates"], center=[15, -40], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Country": d["country"], "Era": d["era"],
            "Famous Pirates": d["famous_pirates"], "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "pirate_havens.csv", "text/csv", key="dl_havens")
        with st.expander("Historical Context: The Golden Age of Piracy"):
            st.markdown(
                "The Golden Age of Piracy (c. 1650-1730) was fueled by the collapse of "
                "Spanish naval power, the end of the War of the Spanish Succession, and "
                "the vast wealth flowing through Caribbean trade routes. Thousands of "
                "unemployed sailors turned to piracy, creating de facto pirate republics "
                "in places like Nassau, Bahamas. The era ended when colonial governors "
                "like Woodes Rogers offered pardons and aggressively hunted holdouts."
            )

    # ── Famous Shipwrecks ─────────────────────────────────────────────────────
    elif mode == "Famous Shipwrecks":
        data = FAMOUS_SHIPWRECKS
        st.markdown("#### Famous Pirate & Maritime Shipwrecks")
        st.caption("Legendary vessels lost to storms, battles, and reefs -- from Blackbeard's flagship to Spanish treasure galleons.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Shipwrecks", len(data))
        pirate_wrecks = sum(1 for d in data if "pirate" in d.get("desc", "").lower() or "captain" in d.get("captain", "").lower())
        c2.metric("Pirate Vessels", pirate_wrecks)
        treasure_wrecks = sum(1 for d in data if d.get("color") == _GOLD)
        c3.metric("Treasure Ships", treasure_wrecks)
        years = [d["year"] for d in data if "year" in d]
        c4.metric("Oldest Wreck", f"{min(years)}" if years else "N/A")
        m = _build_map(data, ["year", "captain"], center=[20, -40], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Year": d.get("year", ""), "Captain/Fleet": d.get("captain", ""),
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "pirate_shipwrecks.csv", "text/csv", key="dl_wrecks")
        with st.expander("Historical Context: Pirate Ship Archaeology"):
            st.markdown(
                "Underwater archaeology has revolutionized our understanding of piracy. "
                "The discovery of the Whydah Gally in 1984 was the first authenticated "
                "pirate shipwreck, proving that pirates really did carry enormous treasure. "
                "Modern technology including side-scan sonar, ROVs, and DNA analysis "
                "continues to reveal new wrecks and rewrite maritime history."
            )

    # ── Naval Battle Sites ────────────────────────────────────────────────────
    elif mode == "Naval Battle Sites":
        data = NAVAL_BATTLES
        st.markdown("#### Great Naval Battles of History")
        st.caption("From ancient Salamis to WWII Midway -- the sea battles that shaped empires and changed the course of history.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Battles Mapped", len(data))
        ancient = sum(1 for d in data if d["year"] < 1500)
        c2.metric("Ancient / Medieval", ancient)
        modern = sum(1 for d in data if d["year"] >= 1800)
        c3.metric("Modern Era (1800+)", modern)
        british = sum(1 for d in data if "britain" in d.get("forces", "").lower() or "england" in d.get("forces", "").lower())
        c4.metric("British Involvement", british)
        m = _build_map(data, ["year", "forces"], center=[30, 0], zoom=2)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Battle": d["name"], "Year": d["year"], "Forces": d.get("forces", ""),
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "naval_battles.csv", "text/csv", key="dl_battles")
        with st.expander("Historical Context: Naval Warfare Through the Ages"):
            st.markdown(
                "Naval warfare evolved from ancient ramming tactics at Salamis (480 BC) "
                "through the age of sail's broadside cannons at Trafalgar (1805) to the "
                "carrier-based air power that decided Midway (1942). Each revolution in "
                "naval technology -- from galleys to galleons, ironclads to aircraft "
                "carriers -- reshaped geopolitics and global trade."
            )

    # ── Treasure Map Legends ──────────────────────────────────────────────────
    elif mode == "Treasure Map Legends":
        data = TREASURE_LEGENDS
        st.markdown("#### Treasure Map Legends & Lost Loot")
        st.caption("Buried gold, coded cryptograms, cursed islands, and treasure hunts that have consumed generations of seekers.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Treasure Legends", len(data))
        confirmed = sum(1 for d in data if d.get("color") == _EMERALD)
        c2.metric("Found / Confirmed", confirmed)
        gold_legends = sum(1 for d in data if d.get("color") == _GOLD)
        c3.metric("Still Undiscovered", gold_legends)
        pirate_treasures = sum(1 for d in data if "pirate" in d.get("desc", "").lower())
        c4.metric("Pirate-Related", pirate_treasures)
        m = _build_map(data, ["legend", "era"], center=[20, -40], zoom=2)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Legend": d.get("legend", ""), "Era": d.get("era", d.get("year", "")),
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "treasure_legends.csv", "text/csv", key="dl_treasure")
        with st.expander("Historical Context: The Allure of Pirate Treasure"):
            st.markdown(
                "The reality of pirate treasure is both more and less romantic than legend "
                "suggests. Most pirates spent their loot quickly on drink and gambling in "
                "port towns. However, some caches were genuinely buried or hidden -- "
                "Captain Kidd's Gardiner's Island treasure was real, and the 1715 Treasure "
                "Fleet still yields gold coins on Florida beaches. The coded cryptogram "
                "of La Buse remains unsolved after nearly 300 years."
            )

    # ── Viking Sea Routes ─────────────────────────────────────────────────────
    elif mode == "Viking Sea Routes":
        data = VIKING_SEA_ROUTES
        st.markdown("#### Viking Sea Routes & Settlements (793-1066)")
        st.caption("Norse raiders, traders, and explorers who sailed from Scandinavia to Byzantium, Baghdad, and North America.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Viking Sites", len(data))
        raids = sum(1 for d in data if d.get("color") == _RED)
        c2.metric("Raids / Battles", raids)
        trade = sum(1 for d in data if d.get("color") == _TEAL)
        c3.metric("Trading Posts", trade)
        settlements = sum(1 for d in data if d.get("color") == _EMERALD)
        c4.metric("Key Settlements", settlements)
        m = _build_map(data, ["year"], center=[55, 5], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Year": d["year"], "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "viking_routes.csv", "text/csv", key="dl_viking")
        with st.expander("Historical Context: The Viking Age"):
            st.markdown(
                "The Viking Age (793-1066) saw Norse seafarers reach every corner of the "
                "known world and beyond. Their longships -- shallow-drafted, fast, and "
                "seaworthy -- could cross oceans and navigate rivers. Vikings established "
                "trade routes from Scandinavia to Baghdad, founded the Kievan Rus state, "
                "settled Iceland, Greenland, and Vinland (North America), and served as "
                "the elite Varangian Guard of Byzantine emperors."
            )

    # ── Barbary Coast Pirates ─────────────────────────────────────────────────
    elif mode == "Barbary Coast Pirates":
        data = BARBARY_COAST
        st.markdown("#### Barbary Coast Pirates & Corsairs (1500-1830)")
        st.caption("The Barbarossa brothers, Dragut, and the corsair states that terrorized the Mediterranean for over 300 years.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations", len(data))
        bases = sum(1 for d in data if d.get("color") == _AMBER)
        c2.metric("Corsair Bases", bases)
        raids = sum(1 for d in data if d.get("color") == _RED)
        c3.metric("Raids / Battles", raids)
        counter = sum(1 for d in data if d.get("color") == _BLUE)
        c4.metric("Counter-Piracy", counter)
        m = _build_map(data, ["era", "famous_pirates"], center=[38, 10], zoom=4)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Era": d.get("era", ""), "Famous Pirates": d.get("famous_pirates", ""),
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "barbary_pirates.csv", "text/csv", key="dl_barbary")
        with st.expander("Historical Context: The Barbary Corsairs"):
            st.markdown(
                "The Barbary States (Algiers, Tunis, Tripoli, and Morocco) conducted "
                "state-sponsored piracy for over 300 years. Backed by the Ottoman Empire, "
                "corsairs enslaved an estimated 1-1.25 million Europeans. European nations "
                "paid enormous tribute to avoid attack. The United States fought two Barbary "
                "Wars (1801-1805, 1815) to end attacks on American shipping, giving rise "
                "to the Marine Corps hymn line 'to the shores of Tripoli.'"
            )

    # ── East Asian Pirates ────────────────────────────────────────────────────
    elif mode == "East Asian Pirates":
        data = EAST_ASIAN_PIRATES
        st.markdown("#### East Asian Pirates -- Wako, Wokou & South China Sea")
        st.caption("From the fearsome Wako raiders to Ching Shih's 80,000-strong pirate armada -- the greatest pirates of the East.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations", len(data))
        chinese = sum(1 for d in data if d.get("color") == _RED)
        c2.metric("Major Pirate Bases", chinese)
        japanese = sum(1 for d in data if "wako" in d.get("desc", "").lower() or "wako" in d.get("famous_pirates", "").lower())
        c3.metric("Wako-Related", japanese)
        se_asian = sum(1 for d in data if d["lat"] < 10)
        c4.metric("SE Asian Sites", se_asian)
        m = _build_map(data, ["era", "famous_pirates"], center=[20, 115], zoom=4)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Era": d.get("era", ""), "Famous Pirates": d.get("famous_pirates", ""),
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "east_asian_pirates.csv", "text/csv", key="dl_eastasia")
        with st.expander("Historical Context: East Asian Piracy"):
            st.markdown(
                "East Asian piracy dwarfed its Caribbean counterpart in scale. Ching Shih "
                "(Madame Ching) commanded 1,800 vessels and 80,000 pirates in the early "
                "1800s -- the largest pirate fleet in history. Japanese wako pirates raided "
                "Chinese and Korean coasts for centuries. The Zheng family built a maritime "
                "empire rivaling European colonial companies, and Koxinga's pirate-descended "
                "dynasty ruled Taiwan for 23 years after expelling the Dutch."
            )

    # ── Privateers & Corsairs ─────────────────────────────────────────────────
    elif mode == "Privateers & Corsairs":
        data = PRIVATEERS_CORSAIRS
        st.markdown("#### Privateers & Corsairs -- Licensed Pirates")
        st.caption("Government-sanctioned sea raiders: Drake, Jean Bart, the Sea Beggars, and other legal pirates with letters of marque.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations", len(data))
        english = sum(1 for d in data if "drake" in d.get("famous_pirates", "").lower() or "england" in d.get("desc", "").lower())
        c2.metric("English Privateers", english)
        french = sum(1 for d in data if "france" in d.get("desc", "").lower() or "french" in d.get("desc", "").lower())
        c3.metric("French Corsairs", french)
        sacked = sum(1 for d in data if d.get("color") == _GOLD)
        c4.metric("Raids / Sackings", sacked)
        m = _build_map(data, ["era", "famous_pirates"], center=[30, -20], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Era": d.get("era", ""), "Famous Figures": d.get("famous_pirates", ""),
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "privateers_corsairs.csv", "text/csv", key="dl_privateers")
        with st.expander("Historical Context: Privateering"):
            st.markdown(
                "Privateering was government-licensed piracy. Nations issued 'letters of "
                "marque' authorizing private captains to attack enemy shipping and keep a "
                "share of the spoils. Drake's circumnavigation alone returned a 4,700% "
                "profit to Queen Elizabeth's investors. During the American Revolution, "
                "privateers captured over 600 British ships. Privateering was not "
                "abolished internationally until the Declaration of Paris in 1856."
            )

    # ── Maritime Museums ──────────────────────────────────────────────────────
    elif mode == "Maritime Museums":
        data = MARITIME_MUSEUMS
        st.markdown("#### Maritime Museums of the World")
        st.caption("The finest collections of maritime history, pirate artifacts, historic ships, and underwater archaeology.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Museums", len(data))
        pirate_museums = sum(1 for d in data if "pirate" in d.get("desc", "").lower() or "pirate" in d.get("highlights", "").lower())
        c2.metric("Pirate-Focused", pirate_museums)
        ship_museums = sum(1 for d in data if "ship" in d.get("highlights", "").lower())
        c3.metric("With Historic Ships", ship_museums)
        countries = len(set(d.get("city", "").split(",")[-1].strip() for d in data))
        c4.metric("Countries", countries)
        m = _build_map(data, ["city", "highlights"], center=[35, 0], zoom=2)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Museum": d["name"], "City": d.get("city", ""), "Highlights": d.get("highlights", ""),
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "maritime_museums.csv", "text/csv", key="pirm_dl_museums")
        with st.expander("Visitor Tips: Maritime Museums"):
            st.markdown(
                "Many of these museums feature actual historic vessels that can be boarded. "
                "The Vasa Museum in Stockholm is the world's most visited maritime museum, "
                "housing a nearly intact 17th-century warship. Portsmouth Historic Dockyard "
                "offers HMS Victory, HMS Warrior, and the Mary Rose all in one location. "
                "The Whydah Pirate Museum in Cape Cod is the only museum dedicated to an "
                "authenticated pirate shipwreck."
            )

    # ── Smuggling Routes & Hideouts ───────────────────────────────────────────
    elif mode == "Smuggling Routes & Hideouts":
        data = SMUGGLING_ROUTES
        st.markdown("#### Smuggling Routes, Hideouts & Contraband")
        st.caption("Secret coves, moonless crossings, rum runners, and the illicit trade networks that defied empires for centuries.")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Locations", len(data))
        english = sum(1 for d in data if d["lat"] > 50 and d["lat"] < 52 and d["lon"] < 2)
        c2.metric("English Coast", english)
        prohibition = sum(1 for d in data if "prohibition" in d.get("desc", "").lower() or "1920" in d.get("era", ""))
        c3.metric("Prohibition Era", prohibition)
        goods_set = set()
        for d in data:
            for g in d.get("goods", "").split(","):
                g = g.strip()
                if g:
                    goods_set.add(g)
        c4.metric("Contraband Types", len(goods_set))
        m = _build_map(data, ["era", "goods"], center=[45, -5], zoom=3)
        if m:
            st_html(m._repr_html_(), height=500)
        df = pd.DataFrame([{
            "Name": d["name"], "Era": d.get("era", ""), "Goods": d.get("goods", ""),
            "Lat": d["lat"], "Lon": d["lon"],
        } for d in data])
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "smuggling_routes.csv", "text/csv", key="dl_smuggling")
        with st.expander("Historical Context: The Economics of Smuggling"):
            st.markdown(
                "Smuggling thrived wherever governments imposed high taxes or trade "
                "restrictions. In 18th-century England, tea was taxed at 119%, making "
                "smuggling enormously profitable -- an estimated half of all tea consumed "
                "in Britain was smuggled. During American Prohibition (1920-1933), rum "
                "running became a billion-dollar industry. The Channel Islands served as "
                "a vast tax-free warehouse, and entire coastal communities depended on "
                "the 'free trade' for their livelihood."
            )
