# -*- coding: utf-8 -*-
"""
Deep Mythology Explorer module for TerraScout AI.
Ten curated mythology map modes with preset data, folium dark-theme maps,
stats rows, DataFrames, and CSV downloads.
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

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from streamlit.components.v1 import html as st_html

# ═══════════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════════
_BG = "#0a0e1a"
_SURFACE = "#111827"
_TEXT = "#e8ecf4"
_TEXT2 = "#8b97b0"
_MUTED = "#5a6580"
_GRID = "#2a3550"
_ACCENT = "#06b6d4"

# ═══════════════════════════════════════════════════════════════════════
# MODE COLORS
# ═══════════════════════════════════════════════════════════════════════
MODE_COLORS = {
    "Greek Mythology Sites": "#06b6d4",
    "Norse Mythology Lands": "#8b5cf6",
    "Egyptian Mythology Sites": "#f59e0b",
    "Celtic Mythology Places": "#10b981",
    "Hindu Epic Locations": "#ec4899",
    "Japanese Yokai & Kami": "#ef4444",
    "Mesoamerican Gods": "#f97316",
    "Chinese Mythology": "#e11d48",
    "African Mythology": "#a855f7",
    "Arthurian Legend Map": "#3b82f6",
}

# ═══════════════════════════════════════════════════════════════════════
# MODE 1: GREEK MYTHOLOGY SITES
# ═══════════════════════════════════════════════════════════════════════
GREEK_SITES = [
    {"name": "Mount Olympus", "lat": 40.0859, "lon": 22.3583,
     "desc": "Home of the twelve Olympian gods, highest peak in Greece at 2,917m.",
     "deity": "Zeus / All Olympians", "type": "Sacred Mountain", "era": "Bronze Age"},
    {"name": "Delphi - Oracle of Apollo", "lat": 38.4824, "lon": 22.5010,
     "desc": "Navel of the world, the Pythia delivered prophecies from Apollo.",
     "deity": "Apollo", "type": "Oracle / Temple", "era": "8th c. BCE"},
    {"name": "Troy (Hisarlik)", "lat": 39.9575, "lon": 26.2388,
     "desc": "Site of the Trojan War narrated in Homer's Iliad.",
     "deity": "Athena / Aphrodite", "type": "Legendary City", "era": "Bronze Age"},
    {"name": "Knossos - Labyrinth of Crete", "lat": 35.2979, "lon": 25.1631,
     "desc": "Palace of King Minos, Labyrinth of the Minotaur built by Daedalus.",
     "deity": "Minotaur / Ariadne / Theseus", "type": "Labyrinth / Palace", "era": "Minoan"},
    {"name": "Athens - Acropolis", "lat": 37.9715, "lon": 23.7267,
     "desc": "Contest between Athena and Poseidon for patronage of the city.",
     "deity": "Athena / Poseidon", "type": "Temple Complex", "era": "5th c. BCE"},
    {"name": "Ithaca", "lat": 38.3654, "lon": 20.7181,
     "desc": "Homeland of Odysseus, hero of Homer's Odyssey.",
     "deity": "Odysseus / Penelope", "type": "Legendary Island", "era": "Bronze Age"},
    {"name": "Delos", "lat": 37.3966, "lon": 25.2688,
     "desc": "Birthplace of Apollo and Artemis, sacred island.",
     "deity": "Apollo / Artemis", "type": "Sacred Island", "era": "Archaic"},
    {"name": "Eleusis", "lat": 38.0417, "lon": 23.5361,
     "desc": "Site of the Eleusinian Mysteries, rites of Demeter and Persephone.",
     "deity": "Demeter / Persephone", "type": "Mystery Cult Site", "era": "Mycenaean"},
    {"name": "Epidaurus", "lat": 37.5963, "lon": 23.0792,
     "desc": "Healing sanctuary of Asclepius, god of medicine.",
     "deity": "Asclepius", "type": "Healing Temple", "era": "6th c. BCE"},
    {"name": "Olympia", "lat": 37.6386, "lon": 21.6300,
     "desc": "Origin of the Olympic Games held in honour of Zeus.",
     "deity": "Zeus", "type": "Athletic Sanctuary", "era": "776 BCE"},
    {"name": "Mycenae", "lat": 37.7306, "lon": 22.7563,
     "desc": "Kingdom of Agamemnon, Lion Gate citadel.",
     "deity": "Agamemnon / Clytemnestra", "type": "Citadel", "era": "Bronze Age"},
    {"name": "Dodona", "lat": 39.5463, "lon": 20.7867,
     "desc": "Oldest Greek oracle, sacred oak tree of Zeus.",
     "deity": "Zeus / Dione", "type": "Oracle", "era": "2nd mill. BCE"},
    {"name": "Colchis (Kutaisi)", "lat": 42.2679, "lon": 42.6946,
     "desc": "Golden Fleece sought by Jason and the Argonauts.",
     "deity": "Medea / Aeetes", "type": "Legendary Kingdom", "era": "Bronze Age"},
    {"name": "Cape Sounion", "lat": 37.6503, "lon": 24.0246,
     "desc": "Temple of Poseidon, where Aegeus leapt into the sea.",
     "deity": "Poseidon / Aegeus", "type": "Temple / Cliff", "era": "5th c. BCE"},
    {"name": "Thebes (Greece)", "lat": 38.3190, "lon": 23.3178,
     "desc": "Birthplace of Dionysus, setting of the Oedipus tragedy.",
     "deity": "Dionysus / Oedipus", "type": "Legendary City", "era": "Mycenaean"},
    {"name": "Sparta", "lat": 37.0755, "lon": 22.4303,
     "desc": "Home of Menelaus and Helen of Troy.",
     "deity": "Helen / Menelaus", "type": "City-State", "era": "Bronze Age"},
    {"name": "Nemea", "lat": 37.8078, "lon": 22.7136,
     "desc": "Heracles slew the Nemean Lion as his first labour.",
     "deity": "Heracles", "type": "Labour Site", "era": "Mythological"},
    {"name": "Lerna", "lat": 37.5500, "lon": 22.7167,
     "desc": "Lair of the Lernaean Hydra, Heracles' second labour.",
     "deity": "Heracles", "type": "Monster Lair", "era": "Mythological"},
    {"name": "Samothrace", "lat": 40.4722, "lon": 25.5250,
     "desc": "Sanctuary of the Great Gods, Cabiri mystery cult.",
     "deity": "Cabiri", "type": "Mystery Cult Site", "era": "7th c. BCE"},
    {"name": "Paphos, Cyprus", "lat": 34.7553, "lon": 32.4069,
     "desc": "Aphrodite born from the sea foam near this shore.",
     "deity": "Aphrodite", "type": "Birth Site", "era": "Mythological"},
    {"name": "Mount Etna, Sicily", "lat": 37.7510, "lon": 14.9934,
     "desc": "Forge of Hephaestus, Typhon imprisoned beneath the volcano.",
     "deity": "Hephaestus / Typhon", "type": "Volcanic Forge", "era": "Mythological"},
    {"name": "Cumae, Italy", "lat": 40.8481, "lon": 14.0539,
     "desc": "Cave of the Cumaean Sibyl, legendary gate to the Underworld.",
     "deity": "Apollo / Sibyl", "type": "Oracle Cave", "era": "8th c. BCE"},
    {"name": "Cape Tenaron", "lat": 36.3883, "lon": 22.4825,
     "desc": "Entrance to the Underworld, Heracles dragged Cerberus out.",
     "deity": "Hades / Heracles", "type": "Underworld Gate", "era": "Mythological"},
    {"name": "Naxos", "lat": 37.1036, "lon": 25.3763,
     "desc": "Ariadne abandoned by Theseus, discovered by Dionysus.",
     "deity": "Dionysus / Ariadne", "type": "Sacred Island", "era": "Mythological"},
    {"name": "Corinth", "lat": 37.9060, "lon": 22.8795,
     "desc": "Sisyphus condemned to roll a boulder for eternity.",
     "deity": "Sisyphus", "type": "City / Underworld link", "era": "Archaic"},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 2: NORSE MYTHOLOGY LANDS
# ═══════════════════════════════════════════════════════════════════════
NORSE_SITES = [
    {"name": "Uppsala Temple", "lat": 59.8586, "lon": 17.6389,
     "desc": "Temple of the Norse gods with sacrificial grove at Gamla Uppsala.",
     "deity": "Odin / Thor / Freyr", "type": "Temple Complex", "saga": "Adam of Bremen"},
    {"name": "Jelling Monuments", "lat": 55.7564, "lon": 9.4192,
     "desc": "Royal rune stones marking the transition from Norse paganism to Christianity.",
     "deity": "Thor / Christ transition", "type": "Royal Monument", "saga": "Historical"},
    {"name": "Lindisfarne", "lat": 55.6697, "lon": -1.8011,
     "desc": "First Viking raid 793 CE, dawn of the Viking Age.",
     "deity": "Odin / War", "type": "Raid Site", "saga": "Anglo-Saxon Chronicle"},
    {"name": "Roskilde", "lat": 55.6415, "lon": 12.0803,
     "desc": "Viking ship burials discovered in the fjord.",
     "deity": "Njord (sea god)", "type": "Ship Burial", "saga": "Historical"},
    {"name": "Thingvellir, Iceland", "lat": 64.2559, "lon": -21.1290,
     "desc": "Site of the Althing parliament; rift between tectonic plates echoes Ginnungagap.",
     "deity": "Lawspeaker / All-gods", "type": "Assembly Site", "saga": "Islendingabok"},
    {"name": "Snorri's Reykholt", "lat": 64.6653, "lon": -21.2958,
     "desc": "Home of Snorri Sturluson, author of the Prose Edda.",
     "deity": "All Norse gods (literary)", "type": "Author's Home", "saga": "Prose Edda"},
    {"name": "Hekla Volcano, Iceland", "lat": 63.9833, "lon": -19.6667,
     "desc": "Believed to be a gateway to Hel (the Norse underworld).",
     "deity": "Hel", "type": "Underworld Gate", "saga": "Medieval lore"},
    {"name": "Oseberg Ship Burial", "lat": 59.3064, "lon": 10.2297,
     "desc": "Ornate Viking ship burial of a volva (seeress).",
     "deity": "Freyja (seeress link)", "type": "Ship Burial", "saga": "Archaeological"},
    {"name": "Gokstad Ship Burial", "lat": 59.1533, "lon": 10.2167,
     "desc": "Great Viking burial ship with warrior king remains.",
     "deity": "Odin", "type": "Ship Burial", "saga": "Archaeological"},
    {"name": "Birka", "lat": 59.3300, "lon": 17.5500,
     "desc": "Major Viking trade hub with warrior graves.",
     "deity": "Odin (warrior cult)", "type": "Viking Town", "saga": "Historical"},
    {"name": "L'Anse aux Meadows", "lat": 51.5882, "lon": -55.5336,
     "desc": "Norse settlement in Vinland (North America), Leif Erikson's landing.",
     "deity": "Leif Erikson", "type": "Norse Settlement", "saga": "Vinland Sagas"},
    {"name": "Trondheim (Nidaros)", "lat": 63.4305, "lon": 10.3951,
     "desc": "Founded by Olav Tryggvason, conversion site of Norse paganism.",
     "deity": "Olav / Thor conflict", "type": "Viking Capital", "saga": "Heimskringla"},
    {"name": "Hedeby", "lat": 54.4900, "lon": 9.5650,
     "desc": "Great Viking trading emporium at the Danish-German border.",
     "deity": "Mercantile gods", "type": "Viking Town", "saga": "Historical"},
    {"name": "Gotland", "lat": 57.4667, "lon": 18.4833,
     "desc": "Island of picture stones depicting Odin riding to Valhalla.",
     "deity": "Odin / Valkyries", "type": "Picture Stone Island", "saga": "Archaeological"},
    {"name": "Borg, Lofoten", "lat": 68.2494, "lon": 14.4372,
     "desc": "Largest Viking longhouse ever found, chieftain's mead hall.",
     "deity": "Odin (chieftain cult)", "type": "Chieftain Hall", "saga": "Archaeological"},
    {"name": "Fyrkat Ring Fortress", "lat": 56.6267, "lon": 9.7736,
     "desc": "Viking ring fortress with volva grave discovered inside.",
     "deity": "Freyja / Seidr", "type": "Ring Fortress", "saga": "Archaeological"},
    {"name": "Trelleborg Ring Fortress", "lat": 55.4000, "lon": 11.2667,
     "desc": "Viking ring fortress built by Harald Bluetooth.",
     "deity": "Odin / War", "type": "Ring Fortress", "saga": "Historical"},
    {"name": "Trolltunga, Norway", "lat": 60.1241, "lon": 6.7400,
     "desc": "Troll's Tongue rock formation from Norse troll legends.",
     "deity": "Trolls", "type": "Troll Legend Site", "saga": "Folk belief"},
    {"name": "Jostedalsbreen Glacier", "lat": 61.6750, "lon": 6.9167,
     "desc": "Largest glacier in Europe, home of frost giants in legend.",
     "deity": "Frost Giants / Ymir", "type": "Jotunheim echo", "saga": "Prose Edda"},
    {"name": "Dettifoss, Iceland", "lat": 65.8147, "lon": -16.3845,
     "desc": "Thundering waterfall linked to Thor's elemental power.",
     "deity": "Thor", "type": "Sacred Waterfall", "saga": "Folk belief"},
    {"name": "Gamla Uppsala Mounds", "lat": 59.8981, "lon": 17.6303,
     "desc": "Royal burial mounds of the Yngling kings linked to god Freyr.",
     "deity": "Freyr / Yngvi", "type": "Royal Burial Mounds", "saga": "Ynglinga Saga"},
    {"name": "Ales Stenar", "lat": 55.3833, "lon": 14.0528,
     "desc": "Ship-shaped stone monument aligned to the solar calendar.",
     "deity": "Sun / Time gods", "type": "Stone Ship", "saga": "Archaeological"},
    {"name": "Saaremaa Meteor Crater", "lat": 58.4167, "lon": 22.5000,
     "desc": "Kaali meteorite crater linked to Norse sky-fire and Thor legends.",
     "deity": "Thor (sky fire)", "type": "Meteor Crater", "saga": "Norse overlap"},
    {"name": "Kaupang, Norway", "lat": 59.0472, "lon": 10.0481,
     "desc": "Norway's first urban Viking settlement and trade center.",
     "deity": "Various", "type": "Viking Trade Town", "saga": "Historical"},
    {"name": "Visby, Gotland", "lat": 57.6389, "lon": 18.2942,
     "desc": "Walled Viking-age town, site of many saga events.",
     "deity": "Various", "type": "Medieval Viking Town", "saga": "Gutasaga"},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 3: EGYPTIAN MYTHOLOGY SITES
# ═══════════════════════════════════════════════════════════════════════
EGYPTIAN_SITES = [
    {"name": "Valley of the Kings", "lat": 25.7402, "lon": 32.6014,
     "desc": "Royal tombs with passages depicting the Duat (underworld).",
     "deity": "Osiris / Anubis", "type": "Royal Necropolis", "dynasty": "18th-20th"},
    {"name": "Karnak Temple, Luxor", "lat": 25.7188, "lon": 32.6573,
     "desc": "Largest ancient religious complex, domain of Amun-Ra.",
     "deity": "Amun-Ra", "type": "Temple Complex", "dynasty": "Middle-New Kingdom"},
    {"name": "Abu Simbel", "lat": 22.3360, "lon": 31.6256,
     "desc": "Colossal rock temple of Ramesses II with solar alignment.",
     "deity": "Ra / Ptah / Amun", "type": "Rock Temple", "dynasty": "19th Dynasty"},
    {"name": "Luxor Temple", "lat": 25.6995, "lon": 32.6390,
     "desc": "Opet Festival temple, divine birth of the pharaoh.",
     "deity": "Amun / Mut / Khonsu", "type": "Temple", "dynasty": "18th Dynasty"},
    {"name": "Great Pyramids of Giza", "lat": 29.9792, "lon": 31.1342,
     "desc": "Tombs of Khufu, Khafre, Menkaure aligned to Orion's belt.",
     "deity": "Osiris / Ra", "type": "Pyramid Complex", "dynasty": "4th Dynasty"},
    {"name": "Great Sphinx of Giza", "lat": 29.9753, "lon": 31.1376,
     "desc": "Guardian of the Giza plateau with the face of Khafre.",
     "deity": "Hor-em-akhet", "type": "Monument", "dynasty": "4th Dynasty"},
    {"name": "Dendera Temple", "lat": 26.1422, "lon": 32.6700,
     "desc": "Hathor's sacred temple with famous zodiac ceiling.",
     "deity": "Hathor", "type": "Temple", "dynasty": "Ptolemaic"},
    {"name": "Abydos", "lat": 26.1850, "lon": 31.9194,
     "desc": "Burial place of Osiris, gateway to the afterlife.",
     "deity": "Osiris", "type": "Sacred City", "dynasty": "All dynasties"},
    {"name": "Philae Temple (Agilkia)", "lat": 24.0236, "lon": 32.8842,
     "desc": "Last active Egyptian temple, dedicated to Isis.",
     "deity": "Isis", "type": "Temple Island", "dynasty": "Ptolemaic"},
    {"name": "Edfu Temple", "lat": 24.9781, "lon": 32.8736,
     "desc": "Temple of Horus depicting his battle with Set.",
     "deity": "Horus", "type": "Temple", "dynasty": "Ptolemaic"},
    {"name": "Kom Ombo Temple", "lat": 24.4525, "lon": 32.9283,
     "desc": "Double temple to crocodile god Sobek and falcon Horus.",
     "deity": "Sobek / Horus", "type": "Double Temple", "dynasty": "Ptolemaic"},
    {"name": "Saqqara Step Pyramid", "lat": 29.8713, "lon": 31.2164,
     "desc": "First monumental stone building, designed by Imhotep.",
     "deity": "Imhotep / Djoser", "type": "Pyramid", "dynasty": "3rd Dynasty"},
    {"name": "Memphis", "lat": 29.8481, "lon": 31.2547,
     "desc": "First capital of unified Egypt, city of creator god Ptah.",
     "deity": "Ptah", "type": "Ancient Capital", "dynasty": "1st Dynasty"},
    {"name": "Heliopolis (Ain Shams)", "lat": 30.1311, "lon": 31.3133,
     "desc": "Center of sun worship, the Ennead creation myth.",
     "deity": "Ra / Atum", "type": "Solar Temple City", "dynasty": "Old Kingdom"},
    {"name": "Deir el-Bahari", "lat": 25.7381, "lon": 32.6069,
     "desc": "Hatshepsut's mortuary temple with divine birth scenes.",
     "deity": "Amun / Hatshepsut", "type": "Mortuary Temple", "dynasty": "18th Dynasty"},
    {"name": "Medinet Habu", "lat": 25.7197, "lon": 32.6006,
     "desc": "Ramesses III temple depicting the Sea Peoples battle.",
     "deity": "Amun-Ra", "type": "Mortuary Temple", "dynasty": "20th Dynasty"},
    {"name": "Colossi of Memnon", "lat": 25.7205, "lon": 32.6103,
     "desc": "Singing statues at dawn named after Ethiopian hero Memnon.",
     "deity": "Amenhotep III", "type": "Colossal Statues", "dynasty": "18th Dynasty"},
    {"name": "Amarna (Akhetaten)", "lat": 27.6486, "lon": 30.8964,
     "desc": "Akhenaten's sun city, monotheistic revolution capital.",
     "deity": "Aten", "type": "Capital City", "dynasty": "18th Dynasty"},
    {"name": "Siwa Oasis", "lat": 29.2032, "lon": 25.5195,
     "desc": "Oracle of Amun where Alexander was declared son of Zeus-Ammon.",
     "deity": "Amun / Zeus-Ammon", "type": "Oracle Oasis", "dynasty": "26th / Greek"},
    {"name": "Elephantine Island", "lat": 24.0850, "lon": 32.8867,
     "desc": "Khnum's workshop where he molded humans on a potter's wheel.",
     "deity": "Khnum", "type": "Sacred Island", "dynasty": "Old Kingdom"},
    {"name": "Bubastis (Tell Basta)", "lat": 30.5750, "lon": 31.5150,
     "desc": "Center of cat-goddess Bastet worship and grand festivals.",
     "deity": "Bastet", "type": "Sacred City", "dynasty": "22nd Dynasty"},
    {"name": "Hermopolis", "lat": 27.7814, "lon": 30.7983,
     "desc": "City of Thoth, site of the Ogdoad creation myth.",
     "deity": "Thoth", "type": "Sacred City", "dynasty": "Old Kingdom"},
    {"name": "Gebel Barkal, Sudan", "lat": 18.5347, "lon": 31.8269,
     "desc": "Amun's sacred mountain in Nubia, southern holy place.",
     "deity": "Amun", "type": "Sacred Mountain", "dynasty": "18th / Kushite"},
    {"name": "Dahshur Bent Pyramid", "lat": 29.7903, "lon": 31.2094,
     "desc": "Sneferu's experimental bent pyramid, transition in design.",
     "deity": "Sneferu", "type": "Pyramid", "dynasty": "4th Dynasty"},
    {"name": "Crocodilopolis (Faiyum)", "lat": 29.3083, "lon": 30.8417,
     "desc": "City where sacred crocodiles of Sobek were worshipped.",
     "deity": "Sobek", "type": "Sacred City", "dynasty": "12th Dynasty"},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 4: CELTIC MYTHOLOGY PLACES
# ═══════════════════════════════════════════════════════════════════════
CELTIC_SITES = [
    {"name": "Glastonbury Tor", "lat": 51.1442, "lon": -2.6983,
     "desc": "Isle of Avalon, legendary burial place of King Arthur.",
     "deity": "Arthur / Morgan le Fay", "type": "Sacred Hill", "tradition": "Arthurian"},
    {"name": "Newgrange", "lat": 53.6947, "lon": -6.4756,
     "desc": "Passage tomb older than the pyramids, dwelling of the Dagda.",
     "deity": "Dagda / Aengus", "type": "Passage Tomb", "tradition": "Irish mythology"},
    {"name": "Hill of Tara", "lat": 53.5789, "lon": -6.6117,
     "desc": "Seat of the High Kings of Ireland, Lia Fail coronation stone.",
     "deity": "Lugh / High Kings", "type": "Royal Seat", "tradition": "Irish mythology"},
    {"name": "Isle of Man", "lat": 54.2361, "lon": -4.5481,
     "desc": "Named after sea god Manannan mac Lir, Celtic crossroads.",
     "deity": "Manannan mac Lir", "type": "Sacred Island", "tradition": "Celtic / Manx"},
    {"name": "Emain Macha (Navan Fort)", "lat": 54.3481, "lon": -6.6969,
     "desc": "Capital of Ulster, court of Cu Chulainn.",
     "deity": "Cu Chulainn / Conchobar", "type": "Royal Fort", "tradition": "Ulster Cycle"},
    {"name": "Giant's Causeway", "lat": 55.2408, "lon": -6.5117,
     "desc": "Built by Fionn mac Cumhaill to fight a Scottish giant.",
     "deity": "Fionn mac Cumhaill", "type": "Geological Wonder", "tradition": "Fenian Cycle"},
    {"name": "Cruachan (Rathcroghan)", "lat": 53.8000, "lon": -8.3000,
     "desc": "Capital of Connacht, entrance to the Otherworld.",
     "deity": "Medb / Ailill", "type": "Royal Site / Otherworld Gate", "tradition": "Ulster Cycle"},
    {"name": "Knowth (Brugh na Boinne)", "lat": 53.7014, "lon": -6.4908,
     "desc": "Passage tomb complex in the Boyne Valley, home of the Tuatha De Danann.",
     "deity": "Tuatha De Danann", "type": "Passage Tomb", "tradition": "Irish mythology"},
    {"name": "Dinas Emrys, Wales", "lat": 53.0133, "lon": -4.0772,
     "desc": "Two dragons fought beneath the hill: the red and the white.",
     "deity": "Merlin / Vortigern", "type": "Hillfort", "tradition": "Welsh mythology"},
    {"name": "Anglesey (Ynys Mon)", "lat": 53.2500, "lon": -4.3333,
     "desc": "Last stronghold of the Druids, destroyed by Romans.",
     "deity": "Druidic priesthood", "type": "Druid Island", "tradition": "Druidic"},
    {"name": "Callanish Stones, Scotland", "lat": 58.1972, "lon": -6.7456,
     "desc": "Stone circle aligned with the lunar cycle, petrified giants legend.",
     "deity": "Ancient spirits", "type": "Stone Circle", "tradition": "Scottish / Gaelic"},
    {"name": "Ben Bulben, Ireland", "lat": 54.3539, "lon": -8.4486,
     "desc": "Where Diarmuid was killed by an enchanted boar.",
     "deity": "Diarmuid / Grainne", "type": "Sacred Mountain", "tradition": "Fenian Cycle"},
    {"name": "Skellig Michael", "lat": 51.7700, "lon": -10.5392,
     "desc": "Remote monastic island, spiritual warrior retreat.",
     "deity": "Michael / Lugh", "type": "Island Monastery", "tradition": "Celtic Christian"},
    {"name": "Bath (Aquae Sulis)", "lat": 51.3811, "lon": -2.3590,
     "desc": "Sacred hot springs of goddess Sulis Minerva.",
     "deity": "Sulis / Minerva", "type": "Sacred Springs", "tradition": "Romano-Celtic"},
    {"name": "Broceliande (Paimpont)", "lat": 48.0000, "lon": -2.1667,
     "desc": "Enchanted forest of Merlin, imprisoned by Viviane.",
     "deity": "Merlin / Viviane", "type": "Enchanted Forest", "tradition": "Arthurian"},
    {"name": "Mont-Saint-Michel", "lat": 48.6361, "lon": -1.5114,
     "desc": "Archangel Michael appeared on this Celtic sacred tidal isle.",
     "deity": "Michael / Celtic sea gods", "type": "Tidal Island", "tradition": "Celtic Christian"},
    {"name": "Ring of Brodgar, Orkney", "lat": 59.0017, "lon": -3.2297,
     "desc": "Neolithic henge, gateway to the spirit world.",
     "deity": "Ancestral spirits", "type": "Stone Circle", "tradition": "Orcadian"},
    {"name": "Loughcrew, Ireland", "lat": 53.7444, "lon": -7.1167,
     "desc": "Passage tombs created by the Cailleach (divine hag).",
     "deity": "Cailleach", "type": "Passage Tomb", "tradition": "Irish mythology"},
    {"name": "Edinburgh - Arthur's Seat", "lat": 55.9444, "lon": -3.1617,
     "desc": "Volcanic hill linked to King Arthur in Scottish tradition.",
     "deity": "Arthur", "type": "Sacred Hill", "tradition": "Arthurian (Scottish)"},
    {"name": "Poulnabrone Dolmen", "lat": 53.0488, "lon": -9.1398,
     "desc": "Portal tomb in the Burren with remains of 33 individuals.",
     "deity": "Ancestral spirits", "type": "Portal Tomb", "tradition": "Irish Neolithic"},
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262,
     "desc": "Merlin transported stones from Ireland by magic.",
     "deity": "Merlin", "type": "Stone Circle", "tradition": "Arthurian / Druidic"},
    {"name": "Clonmacnoise, Ireland", "lat": 53.3264, "lon": -7.9867,
     "desc": "Monastic site where pagan and Christian worlds merged.",
     "deity": "Ciaran / Saint", "type": "Monastery", "tradition": "Celtic Christian"},
    {"name": "Bardsey Island, Wales", "lat": 52.7550, "lon": -4.7950,
     "desc": "Island of 20,000 saints, Merlin's glass house.",
     "deity": "Merlin", "type": "Sacred Island", "tradition": "Arthurian / Welsh"},
    {"name": "Carnac Stones, Brittany", "lat": 47.5847, "lon": -3.0772,
     "desc": "Over 3,000 stones, said to be Roman soldiers petrified by Merlin.",
     "deity": "Merlin", "type": "Megalithic Rows", "tradition": "Breton / Arthurian"},
    {"name": "Lough Derg, Ireland", "lat": 52.9167, "lon": -8.4500,
     "desc": "Saint Patrick's Purgatory, gate to the Otherworld.",
     "deity": "Saint Patrick", "type": "Sacred Lake", "tradition": "Celtic Christian"},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 5: HINDU EPIC LOCATIONS
# ═══════════════════════════════════════════════════════════════════════
HINDU_SITES = [
    {"name": "Ayodhya", "lat": 26.7922, "lon": 82.1998,
     "desc": "Birthplace of Lord Rama, capital of the Kosala kingdom.",
     "deity": "Rama", "epic": "Ramayana", "type": "Sacred City"},
    {"name": "Kurukshetra", "lat": 29.9695, "lon": 76.8783,
     "desc": "Battlefield of the Mahabharata, where the Bhagavad Gita was spoken.",
     "deity": "Krishna / Arjuna", "epic": "Mahabharata", "type": "Battlefield"},
    {"name": "Varanasi (Kashi)", "lat": 25.3176, "lon": 82.9739,
     "desc": "City of Shiva, oldest living city, moksha gateway.",
     "deity": "Shiva", "epic": "Puranas", "type": "Holy City"},
    {"name": "Lanka (Sri Lanka)", "lat": 7.8731, "lon": 80.7718,
     "desc": "Kingdom of Ravana, where Sita was held captive.",
     "deity": "Ravana / Rama", "epic": "Ramayana", "type": "Demon Kingdom"},
    {"name": "Dwarka", "lat": 22.2442, "lon": 68.9685,
     "desc": "Submerged city of Lord Krishna.",
     "deity": "Krishna", "epic": "Mahabharata", "type": "Sacred City (submerged)"},
    {"name": "Mathura", "lat": 27.4924, "lon": 77.6737,
     "desc": "Birthplace of Lord Krishna.",
     "deity": "Krishna", "epic": "Bhagavata Purana", "type": "Sacred City"},
    {"name": "Vrindavan", "lat": 27.5810, "lon": 77.6960,
     "desc": "Krishna's childhood playground, Rasa Lila dances.",
     "deity": "Krishna / Radha", "epic": "Bhagavata Purana", "type": "Sacred Forest"},
    {"name": "Hastinapura", "lat": 29.1627, "lon": 78.0178,
     "desc": "Capital of the Kuru dynasty, Pandavas and Kauravas.",
     "deity": "Pandavas", "epic": "Mahabharata", "type": "Ancient Capital"},
    {"name": "Kishkindha (Hampi)", "lat": 15.3350, "lon": 76.4600,
     "desc": "Kingdom of monkey king Sugriva, Rama's ally.",
     "deity": "Hanuman / Sugriva", "epic": "Ramayana", "type": "Monkey Kingdom"},
    {"name": "Rameshwaram", "lat": 9.2881, "lon": 79.3129,
     "desc": "Rama worshipped Shiva here before crossing to Lanka.",
     "deity": "Rama / Shiva", "epic": "Ramayana", "type": "Temple Island"},
    {"name": "Mount Kailash", "lat": 31.0672, "lon": 81.3128,
     "desc": "Abode of Lord Shiva and Parvati.",
     "deity": "Shiva / Parvati", "epic": "Puranas", "type": "Sacred Mountain"},
    {"name": "Badrinath", "lat": 30.7433, "lon": 79.4938,
     "desc": "Where Vishnu meditated under a badri tree.",
     "deity": "Vishnu", "epic": "Puranas", "type": "Char Dham Temple"},
    {"name": "Kedarnath", "lat": 30.7352, "lon": 79.0669,
     "desc": "One of 12 Jyotirlingas, Shiva hid from the Pandavas here.",
     "deity": "Shiva", "epic": "Mahabharata", "type": "Jyotirlinga Temple"},
    {"name": "Adam's Bridge (Ram Setu)", "lat": 9.1333, "lon": 79.4167,
     "desc": "Bridge built by Rama's monkey army to reach Lanka.",
     "deity": "Rama / Hanuman", "epic": "Ramayana", "type": "Mythical Bridge"},
    {"name": "Panchavati (Nashik)", "lat": 19.9975, "lon": 73.7898,
     "desc": "Where Rama, Sita, and Lakshmana lived in exile.",
     "deity": "Rama / Sita", "epic": "Ramayana", "type": "Forest Exile"},
    {"name": "Chitrakoot", "lat": 25.2018, "lon": 80.8994,
     "desc": "Rama's hermitage during exile, Bharata's visit.",
     "deity": "Rama", "epic": "Ramayana", "type": "Sacred Hill"},
    {"name": "Indraprastha (Delhi)", "lat": 28.6139, "lon": 77.2090,
     "desc": "City built by the Pandavas after dividing the kingdom.",
     "deity": "Pandavas / Indra", "epic": "Mahabharata", "type": "Legendary City"},
    {"name": "Tirupati (Tirumala)", "lat": 13.6288, "lon": 79.4192,
     "desc": "Vishnu descended to earth as Venkateswara.",
     "deity": "Venkateswara / Vishnu", "epic": "Puranas", "type": "Hill Temple"},
    {"name": "Ujjain", "lat": 23.1765, "lon": 75.7885,
     "desc": "City of Mahakaleshwar, one of 12 Jyotirlingas.",
     "deity": "Shiva (Mahakal)", "epic": "Puranas", "type": "Sacred City"},
    {"name": "Somnath", "lat": 20.8880, "lon": 70.4016,
     "desc": "First of the 12 Jyotirlingas, moon god's curse lifted.",
     "deity": "Shiva / Chandra", "epic": "Puranas", "type": "Jyotirlinga Temple"},
    {"name": "Haridwar", "lat": 29.9457, "lon": 78.1642,
     "desc": "Where Ganga enters the plains, Kumbh Mela site.",
     "deity": "Ganga", "epic": "Puranas", "type": "Holy City"},
    {"name": "Allahabad (Prayagraj)", "lat": 25.4358, "lon": 81.8463,
     "desc": "Triveni Sangam confluence of Ganga, Yamuna, Saraswati.",
     "deity": "Brahma / Rivers", "epic": "Puranas", "type": "Sacred Confluence"},
    {"name": "Lepakshi", "lat": 15.4833, "lon": 77.6070,
     "desc": "Jatayu fell here after Ravana cut his wings.",
     "deity": "Jatayu / Rama", "epic": "Ramayana", "type": "Eagle Fall Site"},
    {"name": "Ganges Source (Gaumukh)", "lat": 30.9267, "lon": 79.0833,
     "desc": "Ganga descended from heaven through Shiva's locks.",
     "deity": "Ganga / Shiva", "epic": "Puranas", "type": "Sacred Source"},
    {"name": "Pushkar", "lat": 26.4899, "lon": 74.5542,
     "desc": "Only Brahma temple in the world, lotus petal lake.",
     "deity": "Brahma", "epic": "Puranas", "type": "Creator's Temple"},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 6: JAPANESE YOKAI & KAMI
# ═══════════════════════════════════════════════════════════════════════
JAPANESE_SITES = [
    {"name": "Fushimi Inari Taisha, Kyoto", "lat": 34.9671, "lon": 135.7727,
     "desc": "Thousands of torii gates, kitsune (fox spirit) messengers of Inari.",
     "deity": "Inari / Kitsune", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Ise Grand Shrine", "lat": 34.4551, "lon": 136.7256,
     "desc": "Most sacred Shinto shrine, houses Amaterasu's mirror.",
     "deity": "Amaterasu", "type": "Grand Shrine", "tradition": "Shinto"},
    {"name": "Izumo Taisha", "lat": 35.4019, "lon": 132.6856,
     "desc": "Where all kami gather in October (Kamiarizuki).",
     "deity": "Okuninushi", "type": "Grand Shrine", "tradition": "Shinto"},
    {"name": "Mount Fuji", "lat": 35.3606, "lon": 138.7274,
     "desc": "Sacred mountain, dwelling of Konohanasakuya-hime.",
     "deity": "Konohanasakuya-hime", "type": "Sacred Mountain", "tradition": "Shinto"},
    {"name": "Aokigahara (Sea of Trees)", "lat": 35.4733, "lon": 138.6225,
     "desc": "Haunted forest at base of Fuji, yurei (ghost) legends.",
     "deity": "Yurei (ghosts)", "type": "Haunted Forest", "tradition": "Folklore"},
    {"name": "Mount Osore (Osorezan)", "lat": 41.3328, "lon": 141.0883,
     "desc": "Gateway to the afterlife, itako spirit mediums summon the dead.",
     "deity": "Jizo Bosatsu", "type": "Underworld Gate", "tradition": "Buddhist / Folk"},
    {"name": "Takachiho Gorge", "lat": 32.7133, "lon": 131.3072,
     "desc": "Amaterasu hid in a cave, plunging the world into darkness.",
     "deity": "Amaterasu / Ame-no-Uzume", "type": "Sacred Gorge", "tradition": "Shinto"},
    {"name": "Itsukushima Shrine, Miyajima", "lat": 34.2961, "lon": 132.3197,
     "desc": "Floating torii gate, three Munakata sea goddesses.",
     "deity": "Munakata goddesses", "type": "Floating Shrine", "tradition": "Shinto"},
    {"name": "Nachi Falls", "lat": 33.6675, "lon": 135.8892,
     "desc": "Tallest waterfall in Japan, abode of the dragon god.",
     "deity": "Dragon God / Nachi", "type": "Sacred Waterfall", "tradition": "Shinto"},
    {"name": "Mizuki Shigeru Road, Sakaiminato", "lat": 35.3864, "lon": 133.2328,
     "desc": "Yokai street with 177 bronze statues of yokai creatures.",
     "deity": "Various Yokai", "type": "Yokai Street", "tradition": "Folklore"},
    {"name": "Enoshima Shrine", "lat": 35.2994, "lon": 139.4797,
     "desc": "Island rose from the sea, dragon and Benzaiten love story.",
     "deity": "Benzaiten / Dragon", "type": "Island Shrine", "tradition": "Shinto"},
    {"name": "Kirishima Shrine", "lat": 31.8658, "lon": 130.8703,
     "desc": "Where Ninigi-no-Mikoto descended from heaven to earth.",
     "deity": "Ninigi-no-Mikoto", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Ama-no-Iwato Shrine", "lat": 32.7550, "lon": 131.3508,
     "desc": "The heavenly rock cave where Amaterasu hid.",
     "deity": "Amaterasu", "type": "Cave Shrine", "tradition": "Shinto"},
    {"name": "Kasuga Taisha, Nara", "lat": 34.6810, "lon": 135.8497,
     "desc": "Deity arrived on a white deer, 3,000 stone lanterns.",
     "deity": "Takemikazuchi", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Okunoin Cemetery, Koyasan", "lat": 34.2133, "lon": 135.6036,
     "desc": "200,000 graves; Kobo Daishi awaits Maitreya's coming.",
     "deity": "Kobo Daishi", "type": "Cemetery", "tradition": "Shingon Buddhism"},
    {"name": "Dewa Sanzan", "lat": 38.6969, "lon": 139.9772,
     "desc": "Three sacred mountains of yamabushi mountain ascetics.",
     "deity": "Haguro / Gassan / Yudono", "type": "Sacred Mountains", "tradition": "Shugendo"},
    {"name": "Nikko Toshogu", "lat": 36.7581, "lon": 139.5994,
     "desc": "Deified Tokugawa Ieyasu, home of the three wise monkeys.",
     "deity": "Tokugawa Ieyasu", "type": "Shrine / Mausoleum", "tradition": "Shinto"},
    {"name": "Tono City (Tono Monogatari)", "lat": 39.3278, "lon": 141.5339,
     "desc": "Birthplace of Kunio Yanagita's folklore tales, kappa river spirits.",
     "deity": "Kappa / Zashiki-warashi", "type": "Folklore Town", "tradition": "Folklore"},
    {"name": "Suwa Taisha", "lat": 36.0744, "lon": 138.0983,
     "desc": "One of oldest shrines, Onbashira log festival, dragon lake.",
     "deity": "Takeminakata", "type": "Grand Shrine", "tradition": "Shinto"},
    {"name": "Omiwa Shrine, Nara", "lat": 34.5267, "lon": 135.8556,
     "desc": "Mountain itself is the shintai (god-body), no main hall.",
     "deity": "Omononushi", "type": "Mountain Shrine", "tradition": "Shinto"},
    {"name": "Sefa Utaki, Okinawa", "lat": 26.1731, "lon": 127.8267,
     "desc": "Most sacred Ryukyuan site, creation goddess descended here.",
     "deity": "Amamikiyo", "type": "Sacred Grove", "tradition": "Ryukyuan"},
    {"name": "Zeniarai Benten, Kamakura", "lat": 35.3236, "lon": 139.5422,
     "desc": "Washing money in spring water multiplies wealth.",
     "deity": "Benzaiten", "type": "Money-Washing Shrine", "tradition": "Shinto"},
    {"name": "Meiji Shrine, Tokyo", "lat": 35.6764, "lon": 139.6993,
     "desc": "Dedicated to divine spirits of Emperor Meiji and Empress Shoken.",
     "deity": "Emperor Meiji", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Mount Koya (Koyasan)", "lat": 34.2130, "lon": 135.5800,
     "desc": "Kukai (Kobo Daishi) meditates eternally in his mausoleum.",
     "deity": "Kobo Daishi", "type": "Sacred Mountain", "tradition": "Shingon Buddhism"},
    {"name": "Konpira Shrine, Shikoku", "lat": 34.1767, "lon": 133.8186,
     "desc": "Sea god's shrine, 1,368 stone steps to the main hall.",
     "deity": "Omono-nushi (sea)", "type": "Shrine", "tradition": "Shinto"},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 7: MESOAMERICAN GODS
# ═══════════════════════════════════════════════════════════════════════
MESOAMERICAN_SITES = [
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8438,
     "desc": "Where the gods sacrificed themselves to create the fifth sun.",
     "deity": "Quetzalcoatl / Tlaloc", "culture": "Teotihuacan", "type": "Pyramid City"},
    {"name": "Chichen Itza", "lat": 20.6843, "lon": -88.5678,
     "desc": "Feathered serpent shadow descends pyramid at equinox.",
     "deity": "Kukulkan", "culture": "Maya / Toltec", "type": "Temple Complex"},
    {"name": "Palenque", "lat": 17.4838, "lon": -92.0461,
     "desc": "Tomb of K'inich Janaab Pakal, the astronaut-like sarcophagus lid.",
     "deity": "K'inich Janaab Pakal", "culture": "Maya", "type": "Temple / Tomb"},
    {"name": "Monte Alban", "lat": 17.0439, "lon": -96.7678,
     "desc": "Zapotec capital, observatory, and Danzantes relief carvings.",
     "deity": "Cocijo (rain god)", "culture": "Zapotec", "type": "Ceremonial Center"},
    {"name": "Tikal", "lat": 17.2220, "lon": -89.6237,
     "desc": "Great Maya city where kings communed with gods.",
     "deity": "Itzamna / Chaak", "culture": "Maya", "type": "Temple City"},
    {"name": "Templo Mayor, Mexico City", "lat": 19.4350, "lon": -99.1313,
     "desc": "Aztec twin pyramid for Huitzilopochtli and Tlaloc.",
     "deity": "Huitzilopochtli / Tlaloc", "culture": "Aztec", "type": "Twin Pyramid"},
    {"name": "Uxmal", "lat": 20.3594, "lon": -89.7714,
     "desc": "Pyramid of the Magician, built by a dwarf in one night.",
     "deity": "Chaak", "culture": "Maya", "type": "Pyramid City"},
    {"name": "Copan", "lat": 14.8400, "lon": -89.1408,
     "desc": "City of sculptors, Hieroglyphic Stairway with 2,200 glyphs.",
     "deity": "K'inich Yax K'uk' Mo'", "culture": "Maya", "type": "Temple City"},
    {"name": "Tula", "lat": 20.0646, "lon": -99.3403,
     "desc": "Toltec capital, Atlantean warrior statues atop pyramid.",
     "deity": "Quetzalcoatl / Tezcatlipoca", "culture": "Toltec", "type": "Capital City"},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450,
     "desc": "Inca citadel, sacred Intihuatana stone hitching post of the sun.",
     "deity": "Inti (Sun God)", "culture": "Inca", "type": "Citadel"},
    {"name": "Nazca Lines", "lat": -14.7350, "lon": -75.1300,
     "desc": "Giant geoglyphs visible from the sky, offerings to sky gods.",
     "deity": "Sky deities", "culture": "Nazca", "type": "Geoglyphs"},
    {"name": "Tiwanaku", "lat": -16.5546, "lon": -68.6733,
     "desc": "Pre-Inca site, Gateway of the Sun with Viracocha carving.",
     "deity": "Viracocha", "culture": "Tiwanaku", "type": "Ceremonial Center"},
    {"name": "Calakmul", "lat": 18.1053, "lon": -89.8107,
     "desc": "Rival Maya superpower of Tikal, deep in the jungle.",
     "deity": "Itzamna", "culture": "Maya", "type": "Temple City"},
    {"name": "El Tajin", "lat": 20.4483, "lon": -97.3783,
     "desc": "Pyramid of the Niches with 365 windows, Totonac culture.",
     "deity": "Tajin (thunder god)", "culture": "Totonac", "type": "Pyramid"},
    {"name": "La Venta", "lat": 18.1033, "lon": -94.0417,
     "desc": "Olmec colossal heads, earliest Mesoamerican civilization.",
     "deity": "Were-jaguar", "culture": "Olmec", "type": "Ceremonial Center"},
    {"name": "Sacsayhuaman", "lat": -13.5094, "lon": -71.9822,
     "desc": "Inca fortress with massive megalithic walls, solar festival site.",
     "deity": "Inti", "culture": "Inca", "type": "Fortress / Temple"},
    {"name": "Ollantaytambo", "lat": -13.2588, "lon": -72.2631,
     "desc": "Inca sacred valley fortress, Temple of the Sun on the hilltop.",
     "deity": "Inti / Viracocha", "culture": "Inca", "type": "Temple Fortress"},
    {"name": "Mitla", "lat": 16.9244, "lon": -96.3592,
     "desc": "Zapotec City of the Dead, gateway to the underworld.",
     "deity": "Pitao Bezelao (death)", "culture": "Zapotec / Mixtec", "type": "Necropolis"},
    {"name": "Bonampak", "lat": 16.7042, "lon": -91.0647,
     "desc": "Famous Maya murals depicting war, sacrifice, and divine ritual.",
     "deity": "Maya deities", "culture": "Maya", "type": "Temple / Murals"},
    {"name": "Isla del Sol, Lake Titicaca", "lat": -16.0175, "lon": -69.1744,
     "desc": "Birthplace of the Inca sun god Inti and first Incas.",
     "deity": "Inti / Manco Capac", "culture": "Inca", "type": "Sacred Island"},
    {"name": "Tenochtitlan (Mexico City)", "lat": 19.4326, "lon": -99.1332,
     "desc": "Aztec capital founded where an eagle ate a snake on a cactus.",
     "deity": "Huitzilopochtli", "culture": "Aztec", "type": "Capital City"},
    {"name": "Cholula Great Pyramid", "lat": 19.0578, "lon": -98.3022,
     "desc": "Largest pyramid by volume in the world, dedicated to Quetzalcoatl.",
     "deity": "Quetzalcoatl", "culture": "Multi-culture", "type": "Great Pyramid"},
    {"name": "Chavin de Huantar", "lat": -9.5944, "lon": -77.1778,
     "desc": "Pre-Inca oracle site with Lanzon stone idol in underground gallery.",
     "deity": "Staff God", "culture": "Chavin", "type": "Oracle / Temple"},
    {"name": "Yaxchilan", "lat": 16.9000, "lon": -90.9667,
     "desc": "Maya city on the Usumacinta river, bloodletting vision rituals.",
     "deity": "Vision Serpent", "culture": "Maya", "type": "Temple City"},
    {"name": "Chan Chan", "lat": -8.1064, "lon": -79.0747,
     "desc": "Largest adobe city in the Americas, Chimu kingdom capital.",
     "deity": "Si (Moon goddess)", "culture": "Chimu", "type": "Adobe Capital"},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 8: CHINESE MYTHOLOGY
# ═══════════════════════════════════════════════════════════════════════
CHINESE_SITES = [
    {"name": "Mount Tai (Taishan)", "lat": 36.2500, "lon": 117.1000,
     "desc": "Foremost of the Five Great Mountains, where emperors communed with Heaven.",
     "deity": "Jade Emperor / Dongyue", "type": "Sacred Mountain", "tradition": "Taoist"},
    {"name": "Kunlun Mountains", "lat": 36.0000, "lon": 84.0000,
     "desc": "Mythical home of the Queen Mother of the West (Xiwangmu).",
     "deity": "Xiwangmu", "type": "Mythical Mountain", "tradition": "Taoist"},
    {"name": "Huaguo Mountain (Lianyungang)", "lat": 34.6000, "lon": 119.2000,
     "desc": "Flower Fruit Mountain, birthplace of Sun Wukong (Monkey King).",
     "deity": "Sun Wukong", "type": "Monkey King Site", "tradition": "Journey to the West"},
    {"name": "Flaming Mountains, Turpan", "lat": 42.9500, "lon": 89.1800,
     "desc": "Fiery mountains from Journey to the West, cooled by Princess Iron Fan.",
     "deity": "Sun Wukong / Princess Iron Fan", "type": "Legendary Mountain", "tradition": "Journey to the West"},
    {"name": "Mount Wudang", "lat": 32.4000, "lon": 111.0000,
     "desc": "Birthplace of Taoist martial arts, Zhang Sanfeng's retreat.",
     "deity": "Zhenwu / Zhang Sanfeng", "type": "Sacred Mountain", "tradition": "Taoist"},
    {"name": "West Lake, Hangzhou", "lat": 30.2500, "lon": 120.1500,
     "desc": "Legend of the White Snake, Leifeng Pagoda imprisoned Lady Bai.",
     "deity": "Bai Suzhen (White Snake)", "type": "Legendary Lake", "tradition": "Folklore"},
    {"name": "Dragon King Temple, Beijing", "lat": 39.9042, "lon": 116.3974,
     "desc": "Temple to the Dragon King (Longwang) who controls water and rain.",
     "deity": "Dragon King (Longwang)", "type": "Dragon King Temple", "tradition": "Folk religion"},
    {"name": "Jade Emperor Temple, Kunming", "lat": 25.0389, "lon": 102.7183,
     "desc": "Temple dedicated to the supreme Jade Emperor of Taoist heaven.",
     "deity": "Jade Emperor", "type": "Jade Emperor Temple", "tradition": "Taoist"},
    {"name": "Mount Emei", "lat": 29.5500, "lon": 103.3333,
     "desc": "One of four sacred Buddhist mountains, home of Samantabhadra Bodhisattva.",
     "deity": "Samantabhadra", "type": "Sacred Mountain", "tradition": "Buddhist"},
    {"name": "Mount Hua (Huashan)", "lat": 34.4750, "lon": 110.0875,
     "desc": "One of Five Great Mountains, Chen Tuan achieved immortality here.",
     "deity": "Chen Tuan / Laojun", "type": "Sacred Mountain", "tradition": "Taoist"},
    {"name": "Longmen Grottoes, Luoyang", "lat": 34.5678, "lon": 112.4706,
     "desc": "Thousands of Buddha statues carved from limestone, dragon gate legend.",
     "deity": "Buddha / Dragon Gate", "type": "Buddhist Grottoes", "tradition": "Buddhist"},
    {"name": "Mount Putuo", "lat": 30.0000, "lon": 122.3833,
     "desc": "Sacred island of Guanyin, Bodhisattva of Compassion.",
     "deity": "Guanyin", "type": "Sacred Island", "tradition": "Buddhist"},
    {"name": "White Horse Temple, Luoyang", "lat": 34.7333, "lon": 112.5600,
     "desc": "First Buddhist temple in China, scriptures arrived by white horse.",
     "deity": "Buddha", "type": "Temple", "tradition": "Buddhist"},
    {"name": "Mount Wutai", "lat": 39.0833, "lon": 113.5667,
     "desc": "Sacred mountain of Manjusri (Wenshu), Bodhisattva of Wisdom.",
     "deity": "Manjusri", "type": "Sacred Mountain", "tradition": "Buddhist"},
    {"name": "Mount Jiuhua", "lat": 30.4833, "lon": 117.8000,
     "desc": "Sacred mountain of Ksitigarbha (Dizang), Bodhisattva of the Underworld.",
     "deity": "Ksitigarbha", "type": "Sacred Mountain", "tradition": "Buddhist"},
    {"name": "Nuwa Temple, Hebei", "lat": 36.4417, "lon": 114.1583,
     "desc": "Temple to goddess Nuwa who repaired the sky and created humans.",
     "deity": "Nuwa", "type": "Temple", "tradition": "Mythology"},
    {"name": "Yellow Emperor's Mausoleum", "lat": 35.5911, "lon": 109.2614,
     "desc": "Tomb of Huangdi, mythical ancestor of all Chinese people.",
     "deity": "Yellow Emperor (Huangdi)", "type": "Mausoleum", "tradition": "Ancestral"},
    {"name": "Qufu - Confucius Temple", "lat": 35.5967, "lon": 116.9892,
     "desc": "Birthplace and temple of Confucius, greatest sage.",
     "deity": "Confucius", "type": "Temple / Birthplace", "tradition": "Confucian"},
    {"name": "Wuyi Mountains", "lat": 27.6667, "lon": 117.9500,
     "desc": "Where Penglai immortals roamed, origin of Wuyi rock tea.",
     "deity": "Immortals (Xian)", "type": "Immortal Mountains", "tradition": "Taoist"},
    {"name": "Dunhuang Mogao Caves", "lat": 40.0422, "lon": 94.8019,
     "desc": "Thousand Buddha Grottoes, silk road spiritual oasis.",
     "deity": "Buddha / Bodhisattvas", "type": "Cave Temples", "tradition": "Buddhist"},
    {"name": "Mazu Temple, Meizhou Island", "lat": 25.0900, "lon": 118.9800,
     "desc": "Temple to Mazu, goddess of the sea who protects sailors.",
     "deity": "Mazu (Tianhou)", "type": "Sea Goddess Temple", "tradition": "Folk religion"},
    {"name": "City God Temple, Shanghai", "lat": 31.2265, "lon": 121.4922,
     "desc": "Temple to Chenghuang, the divine magistrate of the city.",
     "deity": "Chenghuang (City God)", "type": "City God Temple", "tradition": "Folk religion"},
    {"name": "Fengdu Ghost City", "lat": 29.8633, "lon": 107.7500,
     "desc": "City of Ghosts on the Yangtze, Diyu (underworld) replica.",
     "deity": "King Yanluo (Yama)", "type": "Ghost City", "tradition": "Buddhist / Taoist"},
    {"name": "Zhangjiajie Pillars", "lat": 29.3167, "lon": 110.4333,
     "desc": "Avatar-like sandstone pillars, home of heavenly spirits.",
     "deity": "Mountain spirits", "type": "Celestial Pillars", "tradition": "Folk belief"},
    {"name": "Dragon King Temple, Datong", "lat": 40.0900, "lon": 113.2900,
     "desc": "Temple where Dragon King controls the rains of northern China.",
     "deity": "Dragon King (Longwang)", "type": "Dragon King Temple", "tradition": "Folk religion"},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 9: AFRICAN MYTHOLOGY
# ═══════════════════════════════════════════════════════════════════════
AFRICAN_SITES = [
    {"name": "Ile-Ife, Nigeria", "lat": 7.4833, "lon": 4.5667,
     "desc": "Sacred city of the Yoruba, where Oduduwa descended and created dry land.",
     "deity": "Oduduwa / Orishas", "type": "Creation City", "tradition": "Yoruba"},
    {"name": "Osogbo Sacred Grove", "lat": 7.7667, "lon": 4.5500,
     "desc": "UNESCO shrine forest of the river goddess Oshun.",
     "deity": "Oshun", "type": "Sacred Grove", "tradition": "Yoruba"},
    {"name": "Oyo (Old Oyo), Nigeria", "lat": 8.8000, "lon": 3.9333,
     "desc": "Capital of the Oyo Empire, home of Shango's lightning cult.",
     "deity": "Shango", "type": "Royal Capital", "tradition": "Yoruba"},
    {"name": "Nok, Nigeria", "lat": 9.5000, "lon": 8.0167,
     "desc": "Ancient terracotta culture, earliest sub-Saharan figurative sculpture.",
     "deity": "Ancestral spirits", "type": "Archaeological / Mythological", "tradition": "Nok"},
    {"name": "Great Zimbabwe", "lat": -20.2675, "lon": 30.9330,
     "desc": "Stone city of the Shona, associated with Mwari creator god.",
     "deity": "Mwari", "type": "Stone City", "tradition": "Shona"},
    {"name": "Lake Fundudzi, South Africa", "lat": -22.9167, "lon": 30.3333,
     "desc": "Sacred lake of the Venda people, home of the python god.",
     "deity": "Python God", "type": "Sacred Lake", "tradition": "Venda"},
    {"name": "uKhahlamba-Drakensberg", "lat": -29.0000, "lon": 29.2500,
     "desc": "San rock art depicting trance dances and therianthropes.",
     "deity": "Mantis (/Kaggen)", "type": "Rock Art", "tradition": "San / Bushman"},
    {"name": "Tsodilo Hills, Botswana", "lat": -18.7500, "lon": 21.7333,
     "desc": "Mountains of the Gods, 4,500+ San rock paintings.",
     "deity": "Creator spirits", "type": "Sacred Hills / Rock Art", "tradition": "San"},
    {"name": "Bandiagara Escarpment (Dogon)", "lat": 14.3500, "lon": -3.5833,
     "desc": "Dogon cliff dwellings, astronomical knowledge of Sirius B.",
     "deity": "Amma / Nommo", "type": "Cliff Dwellings", "tradition": "Dogon"},
    {"name": "Mount Kilimanjaro", "lat": -3.0674, "lon": 37.3556,
     "desc": "Chagga legend: Ruwa (creator) placed humans on the mountain.",
     "deity": "Ruwa", "type": "Sacred Mountain", "tradition": "Chagga"},
    {"name": "Lake Bosumtwi, Ghana", "lat": 6.5042, "lon": -1.4125,
     "desc": "Meteorite crater lake, souls of the dead come here to bid farewell to god Twi.",
     "deity": "Twi", "type": "Sacred Lake", "tradition": "Ashanti"},
    {"name": "Lalibela, Ethiopia", "lat": 12.0319, "lon": 39.0472,
     "desc": "Rock-hewn churches carved by angels according to legend.",
     "deity": "Angels / Lalibela", "type": "Rock-Hewn Churches", "tradition": "Ethiopian Christian"},
    {"name": "Timbuktu, Mali", "lat": 16.7735, "lon": -3.0074,
     "desc": "Center of Islamic scholarship and Mande griots' oral mythology.",
     "deity": "Faro (water spirit)", "type": "Scholarly City", "tradition": "Mande / Islamic"},
    {"name": "Mapungubwe, South Africa", "lat": -22.1919, "lon": 29.2550,
     "desc": "Predecessor kingdom to Great Zimbabwe, golden rhinoceros artifact.",
     "deity": "Rain-making spirits", "type": "Royal Hill", "tradition": "Ancestral"},
    {"name": "Senegambian Stone Circles", "lat": 13.6917, "lon": -15.5250,
     "desc": "Over 1,000 megaliths, largest concentration of stone circles on Earth.",
     "deity": "Ancestral spirits", "type": "Megaliths", "tradition": "West African"},
    {"name": "Ngorongoro Crater, Tanzania", "lat": -3.2000, "lon": 35.5833,
     "desc": "Maasai legend: cattle descended from the sky into this crater.",
     "deity": "Enkai", "type": "Volcanic Crater", "tradition": "Maasai"},
    {"name": "Mount Kenya", "lat": -0.1521, "lon": 37.3083,
     "desc": "Throne of Ngai (Kikuyu creator god), all prayers face this mountain.",
     "deity": "Ngai", "type": "Sacred Mountain", "tradition": "Kikuyu"},
    {"name": "Victoria Falls (Mosi-oa-Tunya)", "lat": -17.9243, "lon": 25.8572,
     "desc": "The Smoke that Thunders, home of river spirit Nyami Nyami.",
     "deity": "Nyami Nyami", "type": "Sacred Waterfall", "tradition": "Tonga / Lozi"},
    {"name": "Djenne Great Mosque, Mali", "lat": 13.9054, "lon": -4.5556,
     "desc": "Largest adobe building in the world, blending Islam and animism.",
     "deity": "Ancestral spirits / Allah", "type": "Mosque / Sacred Site", "tradition": "Mande / Islamic"},
    {"name": "Robben Island, South Africa", "lat": -33.8064, "lon": 18.3667,
     "desc": "Khoisan legend of the sea spirit Adamastor guarding the cape.",
     "deity": "Adamastor", "type": "Island", "tradition": "Khoisan / Portuguese"},
    {"name": "Olduvai Gorge, Tanzania", "lat": -2.9953, "lon": 35.3497,
     "desc": "Cradle of mankind; Maasai creation stories center on this rift valley.",
     "deity": "Enkai", "type": "Gorge / Origin Site", "tradition": "Maasai"},
    {"name": "Lake Malawi", "lat": -12.0000, "lon": 34.5000,
     "desc": "Chewa legend: the lake was formed by the tears of a goddess.",
     "deity": "Water spirits", "type": "Sacred Lake", "tradition": "Chewa"},
    {"name": "Axum Obelisks, Ethiopia", "lat": 14.1289, "lon": 38.7197,
     "desc": "Ancient stelae, said to mark where the Ark of the Covenant rests.",
     "deity": "Ark of the Covenant", "type": "Obelisks", "tradition": "Ethiopian Orthodox"},
    {"name": "Blyde River Canyon, S. Africa", "lat": -24.5833, "lon": 30.8167,
     "desc": "Swazi legend: the canyon was carved by a great serpent.",
     "deity": "Great Serpent", "type": "Canyon", "tradition": "Swazi"},
    {"name": "Mount Cameroon", "lat": 4.2030, "lon": 9.1700,
     "desc": "Active volcano, Bakweri legend says it is home of the god Epasa Moto.",
     "deity": "Epasa Moto", "type": "Sacred Volcano", "tradition": "Bakweri"},
]

# ═══════════════════════════════════════════════════════════════════════
# MODE 10: ARTHURIAN LEGEND MAP
# ═══════════════════════════════════════════════════════════════════════
ARTHURIAN_SITES = [
    {"name": "Tintagel Castle", "lat": 50.6687, "lon": -4.7587,
     "desc": "Birthplace of King Arthur according to Geoffrey of Monmouth.",
     "tradition": "Arthurian", "type": "Castle / Birth Site", "source": "Geoffrey of Monmouth"},
    {"name": "Cadbury Castle (Camelot?)", "lat": 51.0247, "lon": -2.5328,
     "desc": "Most credible candidate for Camelot, Iron Age hillfort refortified in 5th c.",
     "tradition": "Arthurian", "type": "Camelot Candidate", "source": "John Leland / archaeology"},
    {"name": "Glastonbury Tor (Avalon?)", "lat": 51.1442, "lon": -2.6983,
     "desc": "Legendary Isle of Avalon where Arthur was taken after his final battle.",
     "tradition": "Arthurian", "type": "Avalon Candidate", "source": "Gerald of Wales"},
    {"name": "Glastonbury Abbey", "lat": 51.1473, "lon": -2.7139,
     "desc": "Monks claimed to discover Arthur and Guinevere's graves in 1191.",
     "tradition": "Arthurian", "type": "Burial Site", "source": "Gerald of Wales"},
    {"name": "Dozmary Pool (Excalibur)", "lat": 50.5292, "lon": -4.6042,
     "desc": "Lake where the Lady of the Lake received Excalibur back.",
     "tradition": "Arthurian", "type": "Excalibur Site", "source": "Sir Thomas Malory"},
    {"name": "Llyn Llydaw, Snowdonia (Excalibur)", "lat": 53.0694, "lon": -4.0536,
     "desc": "Welsh candidate for the lake where Excalibur was cast.",
     "tradition": "Arthurian", "type": "Excalibur Site", "source": "Welsh tradition"},
    {"name": "Caerleon (Round Table?)", "lat": 51.6117, "lon": -2.9522,
     "desc": "Roman amphitheatre identified as Arthur's Round Table by Geoffrey.",
     "tradition": "Arthurian", "type": "Round Table Candidate", "source": "Geoffrey of Monmouth"},
    {"name": "Winchester Round Table", "lat": 51.0607, "lon": -1.3200,
     "desc": "Great Hall houses a painted round table dating to c.1290.",
     "tradition": "Arthurian", "type": "Round Table Artifact", "source": "Edward I era"},
    {"name": "Badon Hill (Bath area)", "lat": 51.3811, "lon": -2.3590,
     "desc": "Decisive victory of Arthur over the Saxons (~500 CE).",
     "tradition": "Arthurian", "type": "Battle Site", "source": "Gildas / Nennius"},
    {"name": "Camlann (possible: Camelford)", "lat": 50.6211, "lon": -4.6811,
     "desc": "Arthur's final battle where he was mortally wounded.",
     "tradition": "Arthurian", "type": "Battle Site", "source": "Annales Cambriae"},
    {"name": "Camlann (possible: Birdoswald)", "lat": 54.9900, "lon": -2.6100,
     "desc": "Hadrian's Wall fort Camboglanna, alternative Camlann site.",
     "tradition": "Arthurian", "type": "Battle Site", "source": "Historical linguistics"},
    {"name": "Broceliande Forest (Paimpont)", "lat": 48.0000, "lon": -2.1667,
     "desc": "Enchanted forest where Merlin was imprisoned by Viviane.",
     "tradition": "Arthurian", "type": "Enchanted Forest", "source": "Chretien de Troyes"},
    {"name": "Dinas Emrys", "lat": 53.0133, "lon": -4.0772,
     "desc": "Merlin prophesied fighting dragons to Vortigern here.",
     "tradition": "Arthurian", "type": "Merlin Site", "source": "Historia Brittonum"},
    {"name": "Bardsey Island (Merlin's prison)", "lat": 52.7550, "lon": -4.7950,
     "desc": "Island of 20,000 saints, Merlin's glass tower prison.",
     "tradition": "Arthurian", "type": "Merlin Site", "source": "Welsh tradition"},
    {"name": "Edinburgh - Arthur's Seat", "lat": 55.9444, "lon": -3.1617,
     "desc": "Volcanic hill named after Arthur, Gododdin territory.",
     "tradition": "Arthurian", "type": "Arthur Toponym", "source": "Scottish tradition"},
    {"name": "Bamburgh Castle (Joyous Garde?)", "lat": 55.6089, "lon": -1.7103,
     "desc": "Candidate for Lancelot's castle Joyous Garde.",
     "tradition": "Arthurian", "type": "Joyous Garde Candidate", "source": "Malory"},
    {"name": "Corbenic (Dinas Bran?)", "lat": 52.9778, "lon": -3.2400,
     "desc": "Hilltop castle ruin, possible Grail Castle (Corbenic).",
     "tradition": "Arthurian", "type": "Grail Castle Candidate", "source": "Vulgate Cycle"},
    {"name": "Stirling Castle (Round Table)", "lat": 56.1238, "lon": -3.9468,
     "desc": "King's Knot earthwork below castle linked to Arthur's Round Table.",
     "tradition": "Arthurian", "type": "Round Table Candidate", "source": "Scottish lore"},
    {"name": "Slaughterbridge (Camlann?)", "lat": 50.6400, "lon": -4.7100,
     "desc": "Stone inscribed 'Latini ic iacit', linked to Arthur's death.",
     "tradition": "Arthurian", "type": "Death Site Candidate", "source": "Local tradition"},
    {"name": "Kelliwic (Kelly Rounds)", "lat": 50.5278, "lon": -4.8722,
     "desc": "Cornish hillfort identified as Arthur's court Kelliwic in Welsh triads.",
     "tradition": "Arthurian", "type": "Court Site", "source": "Trioedd Ynys Prydein"},
    {"name": "Carlisle", "lat": 54.8951, "lon": -2.9382,
     "desc": "Identified as Arthur's court in several French romances.",
     "tradition": "Arthurian", "type": "Court Site", "source": "Chretien de Troyes"},
    {"name": "Carmarthen (Merlin's birthplace)", "lat": 51.8568, "lon": -4.3121,
     "desc": "Town named Caerfyrddin (Merlin's fort), his legendary birthplace.",
     "tradition": "Arthurian", "type": "Merlin Birthplace", "source": "Geoffrey of Monmouth"},
    {"name": "Loch Lomond (Arthur?)", "lat": 56.0833, "lon": -4.5833,
     "desc": "Mentioned in early sources as site of Arthur's battles.",
     "tradition": "Arthurian", "type": "Battle Site", "source": "Nennius"},
    {"name": "Cadbury Congresbury", "lat": 51.3833, "lon": -2.8667,
     "desc": "Dark Age refortified hillfort, another Camelot candidate.",
     "tradition": "Arthurian", "type": "Camelot Candidate", "source": "Archaeology"},
    {"name": "Mont Saint-Michel", "lat": 48.6361, "lon": -1.5114,
     "desc": "Arthur killed a giant here according to Geoffrey of Monmouth.",
     "tradition": "Arthurian", "type": "Giant-Slaying Site", "source": "Geoffrey of Monmouth"},
]


# ═══════════════════════════════════════════════════════════════════════
# DATASET REGISTRY
# ═══════════════════════════════════════════════════════════════════════
MODE_DATA = {
    "Greek Mythology Sites": GREEK_SITES,
    "Norse Mythology Lands": NORSE_SITES,
    "Egyptian Mythology Sites": EGYPTIAN_SITES,
    "Celtic Mythology Places": CELTIC_SITES,
    "Hindu Epic Locations": HINDU_SITES,
    "Japanese Yokai & Kami": JAPANESE_SITES,
    "Mesoamerican Gods": MESOAMERICAN_SITES,
    "Chinese Mythology": CHINESE_SITES,
    "African Mythology": AFRICAN_SITES,
    "Arthurian Legend Map": ARTHURIAN_SITES,
}

MODE_LIST = list(MODE_DATA.keys())

# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _build_dataframe(sites: list) -> pd.DataFrame:
    """Convert a site list to a DataFrame for display and download."""
    rows = []
    for s in sites:
        rows.append({
            "Name": s.get("name", ""),
            "Latitude": s.get("lat", 0),
            "Longitude": s.get("lon", 0),
            "Description": s.get("desc", ""),
            "Type": s.get("type", ""),
            "Deity / Figure": s.get("deity", s.get("tradition", s.get("source", ""))),
        })
    return pd.DataFrame(rows)


def _build_map(sites: list, color: str, zoom: int = 3) -> folium.Map:
    """Build a folium dark-theme map with MarkerCluster."""
    if not sites:
        return folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    avg_lat = sum(s["lat"] for s in sites) / len(sites)
    avg_lon = sum(s["lon"] for s in sites) / len(sites)
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=zoom, tiles="CartoDB dark_matter")

    cluster = MarkerCluster(name="Sites").add_to(m)

    for s in sites:
        safe_name = html_module.escape(str(s.get("name", "Unknown")))
        safe_desc = html_module.escape(str(s.get("desc", ""))[:250])
        safe_type = html_module.escape(str(s.get("type", "")))
        safe_deity = html_module.escape(str(
            s.get("deity", s.get("tradition", s.get("source", "")))
        ))

        popup_html = (
            f'<div style="max-width:260px; font-family:sans-serif;">'
            f'<strong style="font-size:0.9rem;">{safe_name}</strong><br/>'
            f'<span style="color:{color}; font-size:0.78rem;">{safe_type}</span>'
        )
        if safe_deity:
            popup_html += f' &mdash; <span style="color:#8b97b0; font-size:0.78rem;">{safe_deity}</span>'
        popup_html += f'<br/><span style="font-size:0.75rem;">{safe_desc}</span></div>'

        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=7,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=safe_name,
        ).add_to(cluster)

    # Fit bounds
    lats = [s["lat"] for s in sites]
    lons = [s["lon"] for s in sites]
    m.fit_bounds([[min(lats) - 1, min(lons) - 1], [max(lats) + 1, max(lons) + 1]])

    return m


def _show_stats(sites: list, mode_label: str):
    """Display a metrics row."""
    if not sites:
        st.info("No data to display.")
        return

    types = set(s.get("type", "") for s in sites if s.get("type"))
    deities = set()
    for s in sites:
        d = s.get("deity", s.get("tradition", s.get("source", "")))
        if d:
            deities.add(d)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Sites", len(sites))
    c2.metric("Unique Types", len(types))
    c3.metric("Deities / Figures", len(deities))
    lats = [s["lat"] for s in sites]
    c4.metric("Lat Range", f"{min(lats):.1f} to {max(lats):.1f}")


def _type_chart(sites: list, color: str, mode_label: str):
    """Horizontal bar chart of site types."""
    if not sites:
        return
    counts: dict[str, int] = {}
    for s in sites:
        t = s.get("type", "Unknown")
        counts[t] = counts.get(t, 0) + 1
    if not counts:
        return

    sorted_items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:12]
    labels = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    fig, ax = plt.subplots(figsize=(7, max(3, len(labels) * 0.38)))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_SURFACE)
    ax.barh(range(len(labels)), values, color=color, alpha=0.85)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, color=_TEXT2, fontsize=9)
    ax.set_xlabel("Count", color=_TEXT2, fontsize=10)
    ax.set_title(f"Site Types - {mode_label}", color=_TEXT, fontsize=11, pad=8)
    ax.tick_params(axis="x", colors=_TEXT2, labelsize=9)
    ax.grid(True, axis="x", color=_GRID, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(_GRID)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _csv_download(df: pd.DataFrame, mode_label: str, key_prefix: str):
    """Provide CSV download button."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    filename = mode_label.lower().replace(" ", "_").replace("&", "and") + "_deep.csv"
    st.download_button(
        label=f"Download {len(df)} {mode_label} Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
        key=f"{key_prefix}_dl",
    )


# ═══════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def render_mythology_deep_maps_tab():
    """Render the Deep Mythology Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header violet">
        <h4>Deep Mythology Explorer</h4>
        <p>Explore mythological sites, sacred places, and legendary locations across ten world traditions.
        Curated databases with 25 sites per category, dark-theme maps, stats, charts, and CSV export.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode selector ──
    mode = st.selectbox(
        "Select Mythology Tradition",
        options=MODE_LIST,
        index=0,
        key="myth_deep_mode",
    )

    sites = MODE_DATA.get(mode, [])
    color = MODE_COLORS.get(mode, _ACCENT)

    if not sites:
        st.warning("No data available for this mode.")
        return

    # ── Description panel ──
    descriptions = {
        "Greek Mythology Sites": (
            "The Greek myths form the foundation of Western storytelling. From the thunder-wielding "
            "Zeus atop Mount Olympus to Odysseus's decade-long journey home, these tales are rooted "
            "in real landscapes across the Mediterranean."
        ),
        "Norse Mythology Lands": (
            "The Norse cosmos stretched from Asgard to Hel, but its earthly echoes lie scattered "
            "across Scandinavia, Iceland, and the Viking diaspora. Great halls, ship burials, and "
            "ring fortresses mark the places where skalds sang of Odin, Thor, and the twilight of the gods."
        ),
        "Egyptian Mythology Sites": (
            "For over three millennia, the Nile corridor was the stage for one of humanity's richest "
            "mythologies. Pyramids rose as stairways to the stars, temples housed living gods, and "
            "the boundary between the living and the dead was thin as the desert's edge."
        ),
        "Celtic Mythology Places": (
            "Mist-shrouded islands, enchanted forests, and ancient stone circles form the landscape "
            "of Celtic myth. The tales interweave with older Irish and Welsh legends of the Tuatha De "
            "Danann, Cu Chulainn, and the Fenian warriors."
        ),
        "Hindu Epic Locations": (
            "The Indian subcontinent is a living map of the great epics. The Ramayana traces Rama's "
            "path from Ayodhya to Lanka; the Mahabharata stages its cosmic battle at Kurukshetra."
        ),
        "Japanese Yokai & Kami": (
            "Shinto and Buddhist traditions have sanctified nearly every peak, waterfall, and grove "
            "in Japan. The sun goddess Amaterasu hid in a cave, fox spirits guard rice fields, and "
            "mountain ascetics seek enlightenment on volcanic slopes."
        ),
        "Mesoamerican Gods": (
            "The great civilizations of the Americas built pyramids to touch the sky and carved "
            "calendars into stone. The Maya, Aztec, Inca, and Olmec each created worlds where "
            "gods demanded blood, serpents wore feathers, and the sun was born from divine sacrifice."
        ),
        "Chinese Mythology": (
            "China's mythological landscape spans from the Kunlun Mountains, home of immortals, "
            "to the Five Great Mountains that anchor the empire. The Monkey King, the White Snake, "
            "and the Dragon Kings are among dozens of legends tied to real places."
        ),
        "African Mythology": (
            "Africa's mythologies are vast and diverse: Yoruba Orishas govern nature and human "
            "affairs, San rock art preserves trance visions spanning millennia, Dogon astronomy "
            "encodes deep celestial knowledge, and creation stories root themselves in mountains, "
            "lakes, and sacred groves across the continent."
        ),
        "Arthurian Legend Map": (
            "The Arthurian legend spans Britain and Brittany: Camelot candidates from Cadbury to "
            "Carlisle, Excalibur lakes in Cornwall and Snowdonia, Tintagel's birth story, "
            "Glastonbury's claim to Avalon, and the enchanted forest of Broceliande."
        ),
    }

    desc_text = descriptions.get(mode, "Explore legendary sites on the map below.")
    st.markdown(
        f"""<div style="background:{_SURFACE};border-left:3px solid {color};
            padding:12px 16px;border-radius:0 8px 8px 0;margin:8px 0;
            color:{_TEXT};font-size:13px;line-height:1.6;">
            {html_module.escape(desc_text)}
        </div>""",
        unsafe_allow_html=True,
    )

    # ── Stats row ──
    st.markdown("---")
    _show_stats(sites, mode)

    # ── Map ──
    st.markdown("---")
    st.markdown(f"#### {html_module.escape(mode)} Map")

    zoom_defaults = {
        "Greek Mythology Sites": 5,
        "Norse Mythology Lands": 4,
        "Egyptian Mythology Sites": 6,
        "Celtic Mythology Places": 5,
        "Hindu Epic Locations": 5,
        "Japanese Yokai & Kami": 5,
        "Mesoamerican Gods": 3,
        "Chinese Mythology": 4,
        "African Mythology": 3,
        "Arthurian Legend Map": 6,
    }
    zoom = zoom_defaults.get(mode, 3)
    m = _build_map(sites, color, zoom)
    st_html(m._repr_html_(), height=500)

    # ── Site type chart ──
    st.markdown("---")
    col_chart, col_list = st.columns([1, 1])

    with col_chart:
        with st.expander("Site Type Distribution", expanded=True):
            _type_chart(sites, color, mode)

    with col_list:
        st.markdown("#### Notable Sites")
        for s in sites[:15]:
            safe_name = html_module.escape(str(s.get("name", "")))
            safe_type = html_module.escape(str(s.get("type", "")))
            safe_desc = html_module.escape(str(s.get("desc", ""))[:120])
            st.markdown(
                f"""<div style="display:flex; align-items:center; margin-bottom:0.5rem;">
                    <div style="width:8px; height:50px; border-radius:4px; background:{color};
                                margin-right:0.75rem; flex-shrink:0;"></div>
                    <div>
                        <div style="color:{_TEXT}; font-weight:600; font-size:0.85rem;">{safe_name}</div>
                        <div style="color:{color}; font-size:0.75rem;">{safe_type}</div>
                        <div style="color:{_MUTED}; font-size:0.7rem;">{safe_desc}</div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    # ── Data Table ──
    st.markdown("---")
    df = _build_dataframe(sites)
    st.markdown(f"#### {html_module.escape(mode)} Data Table ({len(df)} sites)")
    st.dataframe(df, width="stretch", hide_index=True)

    # ── CSV Download ──
    st.markdown("---")
    _csv_download(df, mode, f"myth_deep_{MODE_LIST.index(mode)}")

    # ── About ──
    st.markdown("---")
    with st.expander("About Deep Mythology Explorer"):
        st.markdown(
            f"""
**Deep Mythology Explorer** provides curated geospatial data for ten world
mythology traditions.

**Current mode:** {html_module.escape(mode)}
**Sites in this dataset:** {len(sites)}

All coordinates are approximate and correspond to real-world locations
associated with each myth or legend. Data is curated from scholarly and
popular sources and does not require any external API.

**Available categories:**
1. **Greek Mythology Sites** -- {len(GREEK_SITES)} sites
2. **Norse Mythology Lands** -- {len(NORSE_SITES)} sites
3. **Egyptian Mythology Sites** -- {len(EGYPTIAN_SITES)} sites
4. **Celtic Mythology Places** -- {len(CELTIC_SITES)} sites
5. **Hindu Epic Locations** -- {len(HINDU_SITES)} sites
6. **Japanese Yokai & Kami** -- {len(JAPANESE_SITES)} sites
7. **Mesoamerican Gods** -- {len(MESOAMERICAN_SITES)} sites
8. **Chinese Mythology** -- {len(CHINESE_SITES)} sites
9. **African Mythology** -- {len(AFRICAN_SITES)} sites
10. **Arthurian Legend Map** -- {len(ARTHURIAN_SITES)} sites

*Part of the TerraScout AI geospatial platform.*
            """,
        )
