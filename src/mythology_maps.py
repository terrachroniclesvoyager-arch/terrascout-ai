# -*- coding: utf-8 -*-
"""
Mythology & Legends Maps - TerraScout AI Module
Explore mythological sites, sacred places, and legendary locations worldwide.
"""

import streamlit as st
import streamlit.components.v1 as components
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import html
import io
from datetime import datetime

matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Color palette (dark theme)
# ---------------------------------------------------------------------------
BG = "#0a0e1a"
SURFACE = "#111827"
TEXT = "#e8ecf4"
ACCENT = "#06b6d4"
AMBER = "#f59e0b"
EMERALD = "#10b981"
VIOLET = "#8b5cf6"
PINK = "#ec4899"
RED = "#ef4444"

# ---------------------------------------------------------------------------
# Hardcoded datasets
# ---------------------------------------------------------------------------

GREEK_SITES = [
    {"name": "Mount Olympus", "lat": 40.0859, "lon": 22.3583, "myth": "Home of the twelve Olympian gods", "deity": "Zeus / All Olympians", "type": "Sacred Mountain", "era": "Bronze Age"},
    {"name": "Delphi", "lat": 38.4824, "lon": 22.5010, "myth": "Oracle of Apollo, navel of the world", "deity": "Apollo", "type": "Oracle / Temple", "era": "8th c. BCE"},
    {"name": "Troy (Hisarlik)", "lat": 39.9575, "lon": 26.2388, "myth": "Site of the Trojan War (Iliad)", "deity": "Athena / Aphrodite", "type": "Legendary City", "era": "Bronze Age"},
    {"name": "Ithaca", "lat": 38.3654, "lon": 20.7181, "myth": "Homeland of Odysseus", "deity": "Odysseus", "type": "Legendary Island", "era": "Bronze Age"},
    {"name": "Knossos, Crete", "lat": 35.2979, "lon": 25.1631, "myth": "Labyrinth of the Minotaur, King Minos", "deity": "Minotaur / Ariadne", "type": "Labyrinth / Palace", "era": "Minoan"},
    {"name": "Colchis (Kutaisi)", "lat": 42.2679, "lon": 42.6946, "myth": "Golden Fleece sought by Jason", "deity": "Medea / Aeetes", "type": "Legendary Kingdom", "era": "Bronze Age"},
    {"name": "Athens - Acropolis", "lat": 37.9715, "lon": 23.7267, "myth": "Contest between Athena and Poseidon", "deity": "Athena", "type": "Temple Complex", "era": "5th c. BCE"},
    {"name": "Eleusis", "lat": 38.0417, "lon": 23.5361, "myth": "Eleusinian Mysteries, Demeter & Persephone", "deity": "Demeter / Persephone", "type": "Mystery Cult Site", "era": "Mycenaean"},
    {"name": "Epidaurus", "lat": 37.5963, "lon": 23.0792, "myth": "Healing sanctuary of Asclepius", "deity": "Asclepius", "type": "Healing Temple", "era": "6th c. BCE"},
    {"name": "Delos", "lat": 37.3966, "lon": 25.2688, "myth": "Birthplace of Apollo and Artemis", "deity": "Apollo / Artemis", "type": "Sacred Island", "era": "Archaic"},
    {"name": "Olympia", "lat": 37.6386, "lon": 21.6300, "myth": "Origin of the Olympic Games for Zeus", "deity": "Zeus", "type": "Athletic Sanctuary", "era": "776 BCE"},
    {"name": "Dodona", "lat": 39.5463, "lon": 20.7867, "myth": "Oldest Greek oracle, sacred oak of Zeus", "deity": "Zeus / Dione", "type": "Oracle", "era": "2nd mill. BCE"},
    {"name": "Mycenae", "lat": 37.7306, "lon": 22.7563, "myth": "Kingdom of Agamemnon, Curse of Atreus", "deity": "Agamemnon", "type": "Citadel", "era": "Bronze Age"},
    {"name": "Thebes (Greece)", "lat": 38.3190, "lon": 23.3178, "myth": "Birthplace of Dionysus, Oedipus tragedy", "deity": "Dionysus / Oedipus", "type": "Legendary City", "era": "Mycenaean"},
    {"name": "Sparta", "lat": 37.0755, "lon": 22.4303, "myth": "Home of Menelaus and Helen", "deity": "Helen / Menelaus", "type": "City-State", "era": "Bronze Age"},
    {"name": "Lerna", "lat": 37.5500, "lon": 22.7167, "myth": "Lair of the Lernaean Hydra", "deity": "Heracles", "type": "Monster Lair", "era": "Mythological"},
    {"name": "Nemea", "lat": 37.8078, "lon": 22.7136, "myth": "Heracles slew the Nemean Lion", "deity": "Heracles", "type": "Labour Site", "era": "Mythological"},
    {"name": "Cape Sounion", "lat": 37.6503, "lon": 24.0246, "myth": "Temple of Poseidon, Aegeus leapt into the sea", "deity": "Poseidon / Aegeus", "type": "Temple / Cliff", "era": "5th c. BCE"},
    {"name": "Samothrace", "lat": 40.4722, "lon": 25.5250, "myth": "Sanctuary of the Great Gods, Cabiri mysteries", "deity": "Cabiri", "type": "Mystery Cult Site", "era": "7th c. BCE"},
    {"name": "Naxos", "lat": 37.1036, "lon": 25.3763, "myth": "Ariadne abandoned by Theseus, found by Dionysus", "deity": "Dionysus / Ariadne", "type": "Sacred Island", "era": "Mythological"},
    {"name": "Corinth", "lat": 37.9060, "lon": 22.8795, "myth": "Sisyphus condemned to roll boulder eternally", "deity": "Sisyphus", "type": "City / Underworld link", "era": "Archaic"},
    {"name": "Mount Etna, Sicily", "lat": 37.7510, "lon": 14.9934, "myth": "Forge of Hephaestus, Typhon imprisoned beneath", "deity": "Hephaestus / Typhon", "type": "Volcanic Forge", "era": "Mythological"},
    {"name": "Stymphalos", "lat": 37.8583, "lon": 22.4667, "myth": "Heracles drove away the Stymphalian Birds", "deity": "Heracles", "type": "Labour Site", "era": "Mythological"},
    {"name": "Argos", "lat": 37.6310, "lon": 22.7196, "myth": "Kingdom of Diomedes, hundred-eyed Argus", "deity": "Hera / Argus Panoptes", "type": "Ancient City", "era": "Mycenaean"},
    {"name": "Tiryns", "lat": 37.5992, "lon": 22.7997, "myth": "Birthplace of Heracles, Cyclopean walls", "deity": "Heracles", "type": "Citadel", "era": "Bronze Age"},
    {"name": "Phaistos, Crete", "lat": 35.0514, "lon": 24.8147, "myth": "Minoan palace, Phaistos Disc mysteries", "deity": "Minos", "type": "Palace", "era": "Minoan"},
    {"name": "Mount Ida, Crete", "lat": 35.2276, "lon": 24.7690, "myth": "Cave where infant Zeus was hidden from Kronos", "deity": "Zeus / Kronos", "type": "Sacred Cave", "era": "Mythological"},
    {"name": "Thermopylae", "lat": 38.7961, "lon": 22.5359, "myth": "Gates of Fire; Heracles linked to hot springs", "deity": "Heracles", "type": "Legendary Pass", "era": "480 BCE"},
    {"name": "Aulis", "lat": 38.4008, "lon": 23.6000, "myth": "Agamemnon sacrificed Iphigenia for fair winds", "deity": "Artemis / Iphigenia", "type": "Sacrifice Site", "era": "Mythological"},
    {"name": "Seriphos", "lat": 37.1500, "lon": 24.4833, "myth": "Perseus grew up here, turned Polydectes to stone", "deity": "Perseus", "type": "Island", "era": "Mythological"},
    {"name": "Lemnos", "lat": 39.9167, "lon": 25.2333, "myth": "Hephaestus fell here when cast from Olympus", "deity": "Hephaestus", "type": "Island", "era": "Mythological"},
    {"name": "Paphos, Cyprus", "lat": 34.7553, "lon": 32.4069, "myth": "Aphrodite born from the sea foam", "deity": "Aphrodite", "type": "Birth Site", "era": "Mythological"},
    {"name": "Cythera", "lat": 36.2833, "lon": 22.9833, "myth": "Alternate birthplace of Aphrodite", "deity": "Aphrodite", "type": "Sacred Island", "era": "Mythological"},
    {"name": "Cumae, Italy", "lat": 40.8481, "lon": 14.0539, "myth": "Cave of the Cumaean Sibyl, gate to the Underworld", "deity": "Apollo / Sibyl", "type": "Oracle Cave", "era": "8th c. BCE"},
    {"name": "Mount Parnassus", "lat": 38.5337, "lon": 22.6211, "myth": "Home of the Muses, above Delphi", "deity": "Muses / Apollo", "type": "Sacred Mountain", "era": "Mythological"},
    {"name": "Cape Tenaron", "lat": 36.3883, "lon": 22.4825, "myth": "Entrance to the Underworld, Heracles dragged Cerberus out", "deity": "Hades / Heracles", "type": "Underworld Gate", "era": "Mythological"},
    {"name": "River Styx (Mavroneri)", "lat": 38.0000, "lon": 22.2333, "myth": "Waterfall said to be the real River Styx", "deity": "Styx", "type": "Underworld River", "era": "Mythological"},
    {"name": "Pella", "lat": 40.7617, "lon": 22.5247, "myth": "Birthplace of Alexander, who claimed descent from Heracles", "deity": "Heracles / Alexander", "type": "Royal City", "era": "4th c. BCE"},
    {"name": "Iolcos (Volos)", "lat": 39.3600, "lon": 22.9444, "myth": "Port of the Argonauts, Jason's departure", "deity": "Jason / Argonauts", "type": "Port City", "era": "Mythological"},
    {"name": "Calydon", "lat": 38.3722, "lon": 21.5328, "myth": "Calydonian Boar Hunt by Meleager and Atalanta", "deity": "Artemis / Meleager", "type": "Hunting Ground", "era": "Mythological"},
]

NORSE_SITES = [
    {"name": "Uppsala, Sweden", "lat": 59.8586, "lon": 17.6389, "myth": "Temple of the Norse gods, sacrificial grove", "deity": "Odin / Thor / Freyr", "type": "Temple Complex", "saga": "Adam of Bremen"},
    {"name": "Gamla Uppsala", "lat": 59.8981, "lon": 17.6303, "myth": "Royal burial mounds, seat of Yngling kings", "deity": "Freyr / Yngvi", "type": "Royal Burial Mounds", "saga": "Ynglinga Saga"},
    {"name": "Jelling, Denmark", "lat": 55.7564, "lon": 9.4192, "myth": "Viking royal monuments, runic stones", "deity": "Thor / Christ transition", "type": "Royal Monument", "saga": "Historical"},
    {"name": "Thingvellir, Iceland", "lat": 64.2559, "lon": -21.1290, "myth": "Site of the Althing; rift between tectonic plates (Ginnungagap echo)", "deity": "Lawspeaker / All-gods", "type": "Assembly Site", "saga": "Islendingabok"},
    {"name": "Birka, Sweden", "lat": 59.3300, "lon": 17.5500, "myth": "Major Viking trade hub, warrior graves", "deity": "Odin (warrior cult)", "type": "Viking Town", "saga": "Historical"},
    {"name": "Lindisfarne, England", "lat": 55.6697, "lon": -1.8011, "myth": "First Viking raid 793 CE, dawn of the Viking Age", "deity": "Odin / War", "type": "Raid Site", "saga": "Anglo-Saxon Chronicle"},
    {"name": "Roskilde, Denmark", "lat": 55.6415, "lon": 12.0803, "myth": "Viking ship burials discovered in fjord", "deity": "Njord (sea god)", "type": "Ship Burial", "saga": "Historical"},
    {"name": "Oseberg, Norway", "lat": 59.3064, "lon": 10.2297, "myth": "Ornate Viking ship burial of a volva (seeress)", "deity": "Freyja (seeress link)", "type": "Ship Burial", "saga": "Archaeological"},
    {"name": "Gokstad, Norway", "lat": 59.1533, "lon": 10.2167, "myth": "Great Viking burial ship, warrior king", "deity": "Odin", "type": "Ship Burial", "saga": "Archaeological"},
    {"name": "Trondheim (Nidaros), Norway", "lat": 63.4305, "lon": 10.3951, "myth": "Founded by Olav Tryggvason, conversion of Norse to Christianity", "deity": "Olav / Thor conflict", "type": "Viking Capital", "saga": "Heimskringla"},
    {"name": "Hedeby, Germany", "lat": 54.4900, "lon": 9.5650, "myth": "Great Viking trading emporium", "deity": "Mercantile gods", "type": "Viking Town", "saga": "Historical"},
    {"name": "L'Anse aux Meadows, Canada", "lat": 51.5882, "lon": -55.5336, "myth": "Norse settlement in Vinland (North America)", "deity": "Leif Erikson", "type": "Norse Settlement", "saga": "Vinland Sagas"},
    {"name": "Borg, Lofoten, Norway", "lat": 68.2494, "lon": 14.4372, "myth": "Largest Viking longhouse ever found, chieftain's hall", "deity": "Odin (chieftain cult)", "type": "Chieftain Hall", "saga": "Archaeological"},
    {"name": "Sigtuna, Sweden", "lat": 59.6167, "lon": 17.7167, "myth": "Sweden's first town, runic inscriptions", "deity": "Various", "type": "Viking Town", "saga": "Historical"},
    {"name": "Gotland, Sweden", "lat": 57.4667, "lon": 18.4833, "myth": "Island of picture stones depicting Odin and Valhalla", "deity": "Odin / Valkyries", "type": "Picture Stone Island", "saga": "Archaeological"},
    {"name": "Hekla Volcano, Iceland", "lat": 63.9833, "lon": -19.6667, "myth": "Believed to be a gateway to Hel (underworld)", "deity": "Hel", "type": "Underworld Gate", "saga": "Medieval lore"},
    {"name": "Dettifoss, Iceland", "lat": 65.8147, "lon": -16.3845, "myth": "Thundering waterfall linked to Thor's power", "deity": "Thor", "type": "Sacred Waterfall", "saga": "Folk belief"},
    {"name": "Snorri's Hot Pool, Reykholt", "lat": 64.6653, "lon": -21.2958, "myth": "Home of Snorri Sturluson, author of the Prose Edda", "deity": "All Norse gods (literary)", "type": "Author's Home", "saga": "Prose Edda"},
    {"name": "Borre, Norway", "lat": 59.3833, "lon": 10.4333, "myth": "Borre mound cemetery, Yngling dynasty", "deity": "Freyr / Yngvi", "type": "Royal Burial Mounds", "saga": "Ynglinga Saga"},
    {"name": "Anundshog, Sweden", "lat": 59.6167, "lon": 16.5500, "myth": "Largest tumulus in Sweden, ship setting stones", "deity": "Ancestral spirits", "type": "Burial Mound", "saga": "Archaeological"},
    {"name": "Ales Stenar, Sweden", "lat": 55.3833, "lon": 14.0528, "myth": "Stone ship monument, solar calendar alignment", "deity": "Sun / Time gods", "type": "Stone Ship", "saga": "Archaeological"},
    {"name": "Trolltunga, Norway", "lat": 60.1241, "lon": 6.7400, "myth": "Troll's Tongue rock formation from Norse troll legends", "deity": "Trolls", "type": "Troll Legend Site", "saga": "Folk belief"},
    {"name": "Jostedalsbreen, Norway", "lat": 61.6750, "lon": 6.9167, "myth": "Largest glacier in Europe, home of frost giants in legend", "deity": "Frost Giants / Ymir", "type": "Jotunheim echo", "saga": "Prose Edda"},
    {"name": "Visby, Gotland", "lat": 57.6389, "lon": 18.2942, "myth": "Walled Viking Age town, site of many saga events", "deity": "Various", "type": "Medieval Viking Town", "saga": "Gutasaga"},
    {"name": "Kaupang, Norway", "lat": 59.0472, "lon": 10.0481, "myth": "Norway's first urban Viking settlement", "deity": "Various", "type": "Viking Trade Town", "saga": "Historical"},
    {"name": "Tune Ship Mound, Norway", "lat": 59.2833, "lon": 11.1333, "myth": "Early Viking ship burial", "deity": "Ancestral spirits", "type": "Ship Burial", "saga": "Archaeological"},
    {"name": "Fyrkat, Denmark", "lat": 56.6267, "lon": 9.7736, "myth": "Viking ring fortress, volva grave found", "deity": "Freyja / Seidr", "type": "Ring Fortress", "saga": "Archaeological"},
    {"name": "Trelleborg, Denmark", "lat": 55.4000, "lon": 11.2667, "myth": "Viking ring fortress of Harald Bluetooth", "deity": "Odin / War", "type": "Ring Fortress", "saga": "Historical"},
    {"name": "Saaremaa, Estonia", "lat": 58.4167, "lon": 22.5000, "myth": "Kaali meteorite crater linked to Norse sky-fire legends", "deity": "Thor (sky fire)", "type": "Meteor Crater", "saga": "Kalevala / Norse overlap"},
    {"name": "Broskov, Denmark", "lat": 55.2333, "lon": 11.9167, "myth": "Sacrificial bog deposits to Norse gods", "deity": "Various", "type": "Bog Sacrifice Site", "saga": "Archaeological"},
]

EGYPTIAN_SITES = [
    {"name": "Great Pyramids of Giza", "lat": 29.9792, "lon": 31.1342, "myth": "Tombs of Khufu, Khafre, Menkaure; aligned to Orion", "deity": "Osiris / Ra", "type": "Pyramid Complex", "dynasty": "4th Dynasty"},
    {"name": "Great Sphinx of Giza", "lat": 29.9753, "lon": 31.1376, "myth": "Guardian of the Giza plateau, face of Khafre", "deity": "Hor-em-akhet", "type": "Monument", "dynasty": "4th Dynasty"},
    {"name": "Valley of the Kings", "lat": 25.7402, "lon": 32.6014, "myth": "Royal tombs with Duat (underworld) passages", "deity": "Osiris / Anubis", "type": "Royal Necropolis", "dynasty": "18th-20th Dynasty"},
    {"name": "Karnak Temple, Luxor", "lat": 25.7188, "lon": 32.6573, "myth": "Largest ancient religious complex, Amun-Ra's domain", "deity": "Amun-Ra", "type": "Temple Complex", "dynasty": "Middle-New Kingdom"},
    {"name": "Luxor Temple", "lat": 25.6995, "lon": 32.6390, "myth": "Opet Festival, divine birth of pharaoh", "deity": "Amun / Mut / Khonsu", "type": "Temple", "dynasty": "18th Dynasty"},
    {"name": "Abu Simbel", "lat": 22.3360, "lon": 31.6256, "myth": "Ramesses II's colossal temple, solar alignment", "deity": "Ra / Ptah / Amun", "type": "Rock Temple", "dynasty": "19th Dynasty"},
    {"name": "Dendera Temple", "lat": 26.1422, "lon": 32.6700, "myth": "Zodiac ceiling, Hathor's sacred temple", "deity": "Hathor", "type": "Temple", "dynasty": "Ptolemaic"},
    {"name": "Abydos", "lat": 26.1850, "lon": 31.9194, "myth": "Burial place of Osiris, gateway to afterlife", "deity": "Osiris", "type": "Sacred City", "dynasty": "All dynasties"},
    {"name": "Philae Temple (Agilkia)", "lat": 24.0236, "lon": 32.8842, "myth": "Isis temple, last active Egyptian temple", "deity": "Isis", "type": "Temple Island", "dynasty": "Ptolemaic"},
    {"name": "Edfu Temple", "lat": 24.9781, "lon": 32.8736, "myth": "Horus's temple, battle with Set depicted", "deity": "Horus", "type": "Temple", "dynasty": "Ptolemaic"},
    {"name": "Kom Ombo Temple", "lat": 24.4525, "lon": 32.9283, "myth": "Double temple to Sobek (crocodile) and Horus", "deity": "Sobek / Horus", "type": "Double Temple", "dynasty": "Ptolemaic"},
    {"name": "Saqqara (Step Pyramid)", "lat": 29.8713, "lon": 31.2164, "myth": "Imhotep's masterwork, first monumental stone building", "deity": "Imhotep / Djoser", "type": "Pyramid", "dynasty": "3rd Dynasty"},
    {"name": "Memphis", "lat": 29.8481, "lon": 31.2547, "myth": "First capital of unified Egypt, Ptah's city", "deity": "Ptah", "type": "Ancient Capital", "dynasty": "1st Dynasty"},
    {"name": "Heliopolis (Ain Shams)", "lat": 30.1311, "lon": 31.3133, "myth": "Center of sun worship, the Ennead creation myth", "deity": "Ra / Atum", "type": "Solar Temple City", "dynasty": "Old Kingdom"},
    {"name": "Hermopolis (El Ashmunein)", "lat": 27.7814, "lon": 30.7983, "myth": "Thoth's city, Ogdoad creation myth", "deity": "Thoth", "type": "Sacred City", "dynasty": "Old Kingdom"},
    {"name": "Thebes (Luxor area)", "lat": 25.7000, "lon": 32.6500, "myth": "City of Amun, capital during New Kingdom", "deity": "Amun", "type": "Capital City", "dynasty": "New Kingdom"},
    {"name": "Deir el-Bahari", "lat": 25.7381, "lon": 32.6069, "myth": "Hatshepsut's mortuary temple, divine birth scenes", "deity": "Amun / Hatshepsut", "type": "Mortuary Temple", "dynasty": "18th Dynasty"},
    {"name": "Medinet Habu", "lat": 25.7197, "lon": 32.6006, "myth": "Ramesses III's temple, Sea Peoples battle scenes", "deity": "Amun-Ra", "type": "Mortuary Temple", "dynasty": "20th Dynasty"},
    {"name": "Colossi of Memnon", "lat": 25.7205, "lon": 32.6103, "myth": "Singing statues at dawn (Memnon = Ethiopian hero)", "deity": "Amenhotep III", "type": "Colossal Statues", "dynasty": "18th Dynasty"},
    {"name": "Dahshur (Bent Pyramid)", "lat": 29.7903, "lon": 31.2094, "myth": "Sneferu's experimental pyramids", "deity": "Sneferu", "type": "Pyramid", "dynasty": "4th Dynasty"},
    {"name": "Amarna (Akhetaten)", "lat": 27.6486, "lon": 30.8964, "myth": "Akhenaten's sun city, monotheistic revolution", "deity": "Aten", "type": "Capital City", "dynasty": "18th Dynasty"},
    {"name": "Siwa Oasis", "lat": 29.2032, "lon": 25.5195, "myth": "Oracle of Amun, Alexander declared son of Zeus-Ammon", "deity": "Amun / Zeus-Ammon", "type": "Oracle Oasis", "dynasty": "26th Dynasty / Greek"},
    {"name": "Elephantine Island", "lat": 24.0850, "lon": 32.8867, "myth": "Khnum's workshop where he molded humans on a potter's wheel", "deity": "Khnum", "type": "Sacred Island", "dynasty": "Old Kingdom"},
    {"name": "Esna Temple", "lat": 25.2919, "lon": 32.5544, "myth": "Khnum creation hymns on ceiling", "deity": "Khnum / Neith", "type": "Temple", "dynasty": "Ptolemaic-Roman"},
    {"name": "Bubastis (Tell Basta)", "lat": 30.5750, "lon": 31.5150, "myth": "Center of cat-goddess Bastet worship, festivals", "deity": "Bastet", "type": "Sacred City", "dynasty": "22nd Dynasty"},
    {"name": "Crocodilopolis (Faiyum)", "lat": 29.3083, "lon": 30.8417, "myth": "Sacred crocodiles of Sobek worshipped here", "deity": "Sobek", "type": "Sacred City", "dynasty": "12th Dynasty"},
    {"name": "Deir el-Medina", "lat": 25.7278, "lon": 32.6017, "myth": "Workers' village, personal devotion to Meretseger", "deity": "Meretseger / Hathor", "type": "Workers' Village", "dynasty": "New Kingdom"},
    {"name": "Serabit el-Khadim, Sinai", "lat": 29.0389, "lon": 33.4556, "myth": "Hathor turquoise mines, proto-Sinaitic script", "deity": "Hathor", "type": "Mining Temple", "dynasty": "12th Dynasty"},
    {"name": "Gebel Barkal, Sudan", "lat": 18.5347, "lon": 31.8269, "myth": "Amun's sacred mountain in Nubia, southern holy place", "deity": "Amun", "type": "Sacred Mountain", "dynasty": "18th Dynasty / Kushite"},
    {"name": "Tanis (San el-Hagar)", "lat": 30.9764, "lon": 31.8800, "myth": "Delta capital, royal tombs rivalling Valley of Kings", "deity": "Amun / Seth", "type": "Capital / Necropolis", "dynasty": "21st Dynasty"},
    {"name": "Coptos (Qift)", "lat": 25.9975, "lon": 32.8156, "myth": "Gateway to Eastern Desert, Min fertility god center", "deity": "Min", "type": "Trade City", "dynasty": "Predynastic"},
    {"name": "Beni Hasan", "lat": 27.9333, "lon": 30.8833, "myth": "Middle Kingdom tombs with wrestling and daily life scenes", "deity": "Various", "type": "Rock Tombs", "dynasty": "11th-12th Dynasty"},
    {"name": "Hierakonpolis", "lat": 25.0986, "lon": 32.7639, "myth": "City of the Falcon, Narmer Palette origin", "deity": "Horus", "type": "Predynastic Capital", "dynasty": "Predynastic"},
    {"name": "Nubian Temples of Kalabsha", "lat": 23.9667, "lon": 32.8667, "myth": "Relocated Nubian temple, Mandulis solar cult", "deity": "Mandulis / Isis", "type": "Nubian Temple", "dynasty": "Roman period"},
    {"name": "Medamud", "lat": 25.7333, "lon": 32.7167, "myth": "War-god Montu's bull cult temple", "deity": "Montu", "type": "Temple", "dynasty": "Middle Kingdom"},
]

CELTIC_SITES = [
    {"name": "Glastonbury Tor", "lat": 51.1442, "lon": -2.6983, "myth": "Isle of Avalon, burial of King Arthur", "deity": "Arthur / Morgan le Fay", "type": "Sacred Hill", "tradition": "Arthurian"},
    {"name": "Tintagel Castle", "lat": 50.6687, "lon": -4.7587, "myth": "Birthplace of King Arthur", "deity": "Arthur / Uther", "type": "Castle Ruin", "tradition": "Arthurian"},
    {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262, "myth": "Merlin transported stones from Ireland by magic", "deity": "Merlin", "type": "Stone Circle", "tradition": "Arthurian / Druidic"},
    {"name": "Avebury", "lat": 51.4288, "lon": -1.8544, "myth": "Largest stone circle in Europe, druidic rites", "deity": "Earth Mother", "type": "Stone Circle", "tradition": "Druidic"},
    {"name": "Brocéliande (Paimpont)", "lat": 48.0000, "lon": -2.1667, "myth": "Enchanted forest of Merlin, imprisoned by Viviane", "deity": "Merlin / Viviane", "type": "Enchanted Forest", "tradition": "Arthurian"},
    {"name": "Hill of Tara", "lat": 53.5789, "lon": -6.6117, "myth": "Seat of the High Kings of Ireland, Lia Fail stone", "deity": "Lugh / High Kings", "type": "Royal Seat", "tradition": "Irish mythology"},
    {"name": "Newgrange", "lat": 53.6947, "lon": -6.4756, "myth": "Otherworld dwelling of Dagda and Aengus", "deity": "Dagda / Aengus", "type": "Passage Tomb", "tradition": "Irish mythology"},
    {"name": "Brugh na Boinne (Knowth)", "lat": 53.7014, "lon": -6.4908, "myth": "Passage tomb complex in the Boyne Valley", "deity": "Tuatha De Danann", "type": "Passage Tomb", "tradition": "Irish mythology"},
    {"name": "Emain Macha (Navan Fort)", "lat": 54.3481, "lon": -6.6969, "myth": "Capital of Ulster, Cu Chulainn's court", "deity": "Cu Chulainn / Conchobar", "type": "Royal Fort", "tradition": "Ulster Cycle"},
    {"name": "Cruachan (Rathcroghan)", "lat": 53.8000, "lon": -8.3000, "myth": "Capital of Connacht, entrance to the Otherworld", "deity": "Medb / Ailill", "type": "Royal Site / Otherworld Gate", "tradition": "Ulster Cycle"},
    {"name": "Cadbury Castle", "lat": 51.0247, "lon": -2.5328, "myth": "Possible site of Camelot", "deity": "Arthur", "type": "Hillfort", "tradition": "Arthurian"},
    {"name": "Dozmary Pool", "lat": 50.5292, "lon": -4.6042, "myth": "Lady of the Lake returned Excalibur here", "deity": "Arthur / Lady of the Lake", "type": "Lake", "tradition": "Arthurian"},
    {"name": "Llyn Llydaw, Snowdonia", "lat": 53.0694, "lon": -4.0536, "myth": "Welsh candidate for where Excalibur was cast", "deity": "Arthur", "type": "Lake", "tradition": "Arthurian (Welsh)"},
    {"name": "Caerleon", "lat": 51.6117, "lon": -2.9522, "myth": "One of Arthur's courts in Geoffrey of Monmouth", "deity": "Arthur", "type": "Roman-Arthurian City", "tradition": "Arthurian"},
    {"name": "Callanish Stones, Scotland", "lat": 58.1972, "lon": -6.7456, "myth": "Petrified giants turned to stone", "deity": "Ancient spirits", "type": "Stone Circle", "tradition": "Scottish / Gaelic"},
    {"name": "Ring of Brodgar, Orkney", "lat": 59.0017, "lon": -3.2297, "myth": "Neolithic henge, gateway to the spirit world", "deity": "Ancestral spirits", "type": "Stone Circle", "tradition": "Orcadian"},
    {"name": "Clonmacnoise, Ireland", "lat": 53.3264, "lon": -7.9867, "myth": "Monastic site where pagan and Christian worlds merged", "deity": "Ciaran / Saint", "type": "Monastery", "tradition": "Early Christian / Celtic"},
    {"name": "Skellig Michael, Ireland", "lat": 51.7700, "lon": -10.5392, "myth": "Remote monastic island, spiritual warrior retreat", "deity": "Michael / Lugh", "type": "Island Monastery", "tradition": "Celtic Christian"},
    {"name": "Giant's Causeway", "lat": 55.2408, "lon": -6.5117, "myth": "Built by Fionn mac Cumhaill to fight Scottish giant", "deity": "Fionn mac Cumhaill", "type": "Geological Wonder", "tradition": "Fenian Cycle"},
    {"name": "Ben Bulben, Ireland", "lat": 54.3539, "lon": -8.4486, "myth": "Diarmuid killed by enchanted boar on this mountain", "deity": "Diarmuid / Grainne", "type": "Sacred Mountain", "tradition": "Fenian Cycle"},
    {"name": "Lough Derg, Ireland", "lat": 52.9167, "lon": -8.4500, "myth": "Saint Patrick's Purgatory, gate to the Otherworld", "deity": "Saint Patrick", "type": "Sacred Lake", "tradition": "Celtic Christian"},
    {"name": "Edinburgh - Arthur's Seat", "lat": 55.9444, "lon": -3.1617, "myth": "Volcanic hill linked to King Arthur", "deity": "Arthur", "type": "Sacred Hill", "tradition": "Arthurian (Scottish)"},
    {"name": "Bardsey Island, Wales", "lat": 52.7550, "lon": -4.7950, "myth": "Island of 20,000 saints, Merlin's glass house", "deity": "Merlin", "type": "Sacred Island", "tradition": "Arthurian / Welsh"},
    {"name": "Dinas Emrys, Wales", "lat": 53.0133, "lon": -4.0772, "myth": "Two dragons fought beneath the hill (red & white)", "deity": "Merlin / Vortigern", "type": "Hillfort", "tradition": "Welsh mythology"},
    {"name": "Loughcrew, Ireland", "lat": 53.7444, "lon": -7.1167, "myth": "Passage tombs created by the Cailleach (divine hag)", "deity": "Cailleach", "type": "Passage Tomb", "tradition": "Irish mythology"},
    {"name": "Anglesey (Ynys Mon)", "lat": 53.2500, "lon": -4.3333, "myth": "Last stronghold of the Druids, destroyed by Romans", "deity": "Druidic priesthood", "type": "Druid Island", "tradition": "Druidic"},
    {"name": "Carnac Stones, France", "lat": 47.5847, "lon": -3.0772, "myth": "Petrified Roman soldiers turned to stone by Merlin", "deity": "Merlin", "type": "Megalithic Rows", "tradition": "Breton / Arthurian"},
    {"name": "Mont-Saint-Michel, France", "lat": 48.6361, "lon": -1.5114, "myth": "Archangel Michael appeared, Celtic sacred tidal isle", "deity": "Michael / Celtic sea gods", "type": "Tidal Island", "tradition": "Celtic Christian"},
    {"name": "Clava Cairns, Scotland", "lat": 57.4728, "lon": -4.0736, "myth": "Bronze Age burial cairns aligned to midwinter sunset", "deity": "Ancestral spirits", "type": "Cairns", "tradition": "Scottish"},
    {"name": "Bath (Aquae Sulis)", "lat": 51.3811, "lon": -2.3590, "myth": "Sacred hot springs of goddess Sulis Minerva", "deity": "Sulis / Minerva", "type": "Sacred Springs", "tradition": "Romano-Celtic"},
]

HINDU_SITES = [
    {"name": "Ayodhya", "lat": 26.7922, "lon": 82.1998, "myth": "Birthplace of Lord Rama, capital of Kosala", "deity": "Rama", "epic": "Ramayana", "type": "Sacred City"},
    {"name": "Lanka (Sri Lanka)", "lat": 7.8731, "lon": 80.7718, "myth": "Kingdom of Ravana, where Sita was held captive", "deity": "Ravana / Rama", "epic": "Ramayana", "type": "Demon Kingdom"},
    {"name": "Kurukshetra", "lat": 29.9695, "lon": 76.8783, "myth": "Battlefield of the Mahabharata, Bhagavad Gita spoken here", "deity": "Krishna / Arjuna", "epic": "Mahabharata", "type": "Battlefield"},
    {"name": "Dwarka", "lat": 22.2442, "lon": 68.9685, "myth": "Submerged city of Lord Krishna", "deity": "Krishna", "epic": "Mahabharata", "type": "Sacred City (submerged)"},
    {"name": "Varanasi (Kashi)", "lat": 25.3176, "lon": 82.9739, "myth": "City of Shiva, oldest living city, moksha gateway", "deity": "Shiva", "epic": "Puranas", "type": "Holy City"},
    {"name": "Mathura", "lat": 27.4924, "lon": 77.6737, "myth": "Birthplace of Lord Krishna", "deity": "Krishna", "epic": "Bhagavata Purana", "type": "Sacred City"},
    {"name": "Vrindavan", "lat": 27.5810, "lon": 77.6960, "myth": "Krishna's childhood playground, Rasa Lila dances", "deity": "Krishna / Radha", "epic": "Bhagavata Purana", "type": "Sacred Forest"},
    {"name": "Hastinapura", "lat": 29.1627, "lon": 78.0178, "myth": "Capital of the Kuru dynasty, Pandavas and Kauravas", "deity": "Pandavas", "epic": "Mahabharata", "type": "Ancient Capital"},
    {"name": "Indraprastha (Delhi)", "lat": 28.6139, "lon": 77.2090, "myth": "City built by the Pandavas after dividing kingdom", "deity": "Pandavas / Indra", "epic": "Mahabharata", "type": "Legendary City"},
    {"name": "Rameshwaram", "lat": 9.2881, "lon": 79.3129, "myth": "Rama worshipped Shiva here before crossing to Lanka", "deity": "Rama / Shiva", "epic": "Ramayana", "type": "Temple Island"},
    {"name": "Kishkindha (Hampi)", "lat": 15.3350, "lon": 76.4600, "myth": "Kingdom of monkey king Sugriva, Rama's ally", "deity": "Hanuman / Sugriva", "epic": "Ramayana", "type": "Monkey Kingdom"},
    {"name": "Panchavati (Nashik)", "lat": 19.9975, "lon": 73.7898, "myth": "Where Rama, Sita, and Lakshmana lived in exile", "deity": "Rama / Sita", "epic": "Ramayana", "type": "Forest Exile"},
    {"name": "Chitrakoot", "lat": 25.2018, "lon": 80.8994, "myth": "Rama's hermitage during exile, Bharata's visit", "deity": "Rama", "epic": "Ramayana", "type": "Sacred Hill"},
    {"name": "Mount Kailash", "lat": 31.0672, "lon": 81.3128, "myth": "Abode of Lord Shiva and Parvati", "deity": "Shiva / Parvati", "epic": "Puranas", "type": "Sacred Mountain"},
    {"name": "Badrinath", "lat": 30.7433, "lon": 79.4938, "myth": "Where Vishnu meditated under a badri tree", "deity": "Vishnu", "epic": "Puranas", "type": "Char Dham Temple"},
    {"name": "Kedarnath", "lat": 30.7352, "lon": 79.0669, "myth": "One of 12 Jyotirlingas, Shiva hid from Pandavas", "deity": "Shiva", "epic": "Mahabharata", "type": "Jyotirlinga Temple"},
    {"name": "Puri (Jagannath)", "lat": 19.8135, "lon": 85.8312, "myth": "Lord Jagannath (Krishna) with unfinished idol legend", "deity": "Jagannath / Krishna", "epic": "Puranas", "type": "Char Dham Temple"},
    {"name": "Ujjain", "lat": 23.1765, "lon": 75.7885, "myth": "City of Mahakaleshwar, one of 12 Jyotirlingas", "deity": "Shiva (Mahakal)", "epic": "Puranas", "type": "Sacred City"},
    {"name": "Somnath", "lat": 20.8880, "lon": 70.4016, "myth": "First of the 12 Jyotirlingas, moon god's curse lifted", "deity": "Shiva / Chandra", "epic": "Puranas", "type": "Jyotirlinga Temple"},
    {"name": "Tirupati (Tirumala)", "lat": 13.6288, "lon": 79.4192, "myth": "Vishnu descended to earth as Venkateswara for his consort", "deity": "Venkateswara / Vishnu", "epic": "Puranas", "type": "Hill Temple"},
    {"name": "Gaya", "lat": 24.7914, "lon": 85.0002, "myth": "Vishnu's footprint, ancestors gain salvation (pind daan)", "deity": "Vishnu", "epic": "Puranas", "type": "Ancestral Rites City"},
    {"name": "Allahabad (Prayagraj)", "lat": 25.4358, "lon": 81.8463, "myth": "Triveni Sangam - confluence of Ganga, Yamuna, Saraswati", "deity": "Brahma / Rivers", "epic": "Puranas", "type": "Sacred Confluence"},
    {"name": "Haridwar", "lat": 29.9457, "lon": 78.1642, "myth": "Where Ganga enters the plains, Kumbh Mela site", "deity": "Ganga", "epic": "Puranas", "type": "Holy City"},
    {"name": "Rishikesh", "lat": 30.0869, "lon": 78.2676, "myth": "Where Vishnu appeared to Raibhya rishi", "deity": "Vishnu", "epic": "Puranas", "type": "Yoga Capital"},
    {"name": "Lepakshi", "lat": 15.4833, "lon": 77.6070, "myth": "Jatayu fell here after Ravana cut his wings", "deity": "Jatayu / Rama", "epic": "Ramayana", "type": "Eagle Fall Site"},
    {"name": "Adam's Bridge (Ram Setu)", "lat": 9.1333, "lon": 79.4167, "myth": "Bridge built by Rama's monkey army to Lanka", "deity": "Rama / Hanuman", "epic": "Ramayana", "type": "Mythical Bridge"},
    {"name": "Gokarna", "lat": 14.5479, "lon": 74.3188, "myth": "Atmalinga of Shiva, tricked from Ravana by Ganesha", "deity": "Shiva / Ganesha", "epic": "Puranas", "type": "Shiva Temple"},
    {"name": "Omkareshwar", "lat": 22.2453, "lon": 76.1511, "myth": "Om-shaped island, one of 12 Jyotirlingas", "deity": "Shiva", "epic": "Puranas", "type": "Jyotirlinga Island"},
    {"name": "Madhurai (Meenakshi Temple)", "lat": 9.9195, "lon": 78.1193, "myth": "Shiva married Meenakshi (Parvati) here", "deity": "Shiva / Meenakshi", "epic": "Puranas", "type": "Marriage Temple"},
    {"name": "Ganges Source (Gaumukh)", "lat": 30.9267, "lon": 79.0833, "myth": "Ganga descended from heaven through Shiva's locks", "deity": "Ganga / Shiva", "epic": "Puranas", "type": "Sacred Source"},
    {"name": "Amarkantak", "lat": 22.6733, "lon": 81.7530, "myth": "Source of the Narmada river, Shiva's sweat drops", "deity": "Shiva / Narmada", "epic": "Puranas", "type": "River Source"},
    {"name": "Dwaraka (underwater ruins)", "lat": 22.2300, "lon": 68.9500, "myth": "Marine archaeological ruins off Gujarat coast", "deity": "Krishna", "epic": "Mahabharata", "type": "Underwater City"},
    {"name": "Muktinath, Nepal", "lat": 28.8167, "lon": 83.8667, "myth": "Sacred to both Hindus (Vishnu) and Buddhists", "deity": "Vishnu / Muktinath", "epic": "Puranas", "type": "Mountain Temple"},
    {"name": "Pushkar", "lat": 26.4899, "lon": 74.5542, "myth": "Only Brahma temple in the world, lotus petal lake", "deity": "Brahma", "epic": "Puranas", "type": "Creator's Temple"},
    {"name": "Palitana, Gujarat", "lat": 21.5289, "lon": 71.8234, "myth": "Mountain of Jain temples, Adinath's moksha", "deity": "Adinath / Jain Tirthankaras", "epic": "Jain tradition", "type": "Temple Mountain"},
]

JAPANESE_SITES = [
    {"name": "Ise Grand Shrine", "lat": 34.4551, "lon": 136.7256, "myth": "Most sacred Shinto shrine, houses Amaterasu's mirror", "deity": "Amaterasu", "type": "Grand Shrine", "tradition": "Shinto"},
    {"name": "Izumo Taisha", "lat": 35.4019, "lon": 132.6856, "myth": "Where all gods gather in October, Okuninushi's shrine", "deity": "Okuninushi", "type": "Grand Shrine", "tradition": "Shinto"},
    {"name": "Mount Fuji", "lat": 35.3606, "lon": 138.7274, "myth": "Sacred mountain, dwelling of goddess Konohanasakuya-hime", "deity": "Konohanasakuya-hime", "type": "Sacred Mountain", "tradition": "Shinto / Buddhist"},
    {"name": "Mount Koya (Koyasan)", "lat": 34.2130, "lon": 135.5800, "myth": "Kukai (Kobo Daishi) meditates eternally here", "deity": "Kobo Daishi", "type": "Sacred Mountain", "tradition": "Shingon Buddhism"},
    {"name": "Kumano Sanzan", "lat": 33.8406, "lon": 135.7739, "myth": "Three grand shrines, entrance to the Pure Land", "deity": "Kumano deities", "type": "Shrine Complex", "tradition": "Shinto / Buddhist"},
    {"name": "Fushimi Inari Taisha, Kyoto", "lat": 34.9671, "lon": 135.7727, "myth": "Thousands of torii gates, fox spirits (kitsune)", "deity": "Inari", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Itsukushima Shrine, Miyajima", "lat": 34.2961, "lon": 132.3197, "myth": "Floating torii gate, three sea goddesses", "deity": "Munakata goddesses", "type": "Floating Shrine", "tradition": "Shinto"},
    {"name": "Nikko Toshogu", "lat": 36.7581, "lon": 139.5994, "myth": "Deified Tokugawa Ieyasu, three wise monkeys", "deity": "Tokugawa Ieyasu", "type": "Shrine / Mausoleum", "tradition": "Shinto / Buddhist"},
    {"name": "Aokigahara (Sea of Trees)", "lat": 35.4733, "lon": 138.6225, "myth": "Haunted forest at base of Fuji, yurei legends", "deity": "Yurei (ghosts)", "type": "Haunted Forest", "tradition": "Folklore"},
    {"name": "Takachiho Gorge", "lat": 32.7133, "lon": 131.3072, "myth": "Where Amaterasu hid in a cave, plunging world into darkness", "deity": "Amaterasu / Ame-no-Uzume", "type": "Sacred Gorge", "tradition": "Shinto"},
    {"name": "Mount Osore (Osorezan)", "lat": 41.3328, "lon": 141.0883, "myth": "Gateway to the afterlife, itako spirit mediums", "deity": "Jizo Bosatsu", "type": "Underworld Gate", "tradition": "Buddhist / Folk"},
    {"name": "Nara - Todaiji", "lat": 34.6889, "lon": 135.8397, "myth": "Great Buddha hall, deer are divine messengers", "deity": "Vairocana Buddha", "type": "Temple", "tradition": "Buddhism"},
    {"name": "Dewa Sanzan", "lat": 38.6969, "lon": 139.9772, "myth": "Three sacred mountains of yamabushi mountain ascetics", "deity": "Haguro / Gassan / Yudono", "type": "Sacred Mountains", "tradition": "Shugendo"},
    {"name": "Sefa Utaki, Okinawa", "lat": 26.1731, "lon": 127.8267, "myth": "Most sacred Ryukyuan site, creation goddess descended", "deity": "Amamikiyo", "type": "Sacred Grove", "tradition": "Ryukyuan"},
    {"name": "Hashiman Shrine, Kamakura", "lat": 35.3258, "lon": 139.5564, "myth": "God of war (Hachiman), samurai patron deity", "deity": "Hachiman", "type": "War Shrine", "tradition": "Shinto"},
    {"name": "Okunoin Cemetery, Koyasan", "lat": 34.2133, "lon": 135.6036, "myth": "200,000 graves, Kobo Daishi awaits Maitreya's coming", "deity": "Kobo Daishi", "type": "Cemetery", "tradition": "Shingon Buddhism"},
    {"name": "Meiji Shrine, Tokyo", "lat": 35.6764, "lon": 139.6993, "myth": "Dedicated to Emperor Meiji, divine spirits of the emperor", "deity": "Emperor Meiji", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Nachi Falls", "lat": 33.6675, "lon": 135.8892, "myth": "Tallest waterfall in Japan, abode of dragon god", "deity": "Dragon God / Nachi", "type": "Sacred Waterfall", "tradition": "Shinto / Buddhist"},
    {"name": "Himuro Shrine, Nara", "lat": 34.6828, "lon": 135.8331, "myth": "Where ice was offered to the emperor, icehouse god", "deity": "Ice deity", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Omiwa Shrine, Nara", "lat": 34.5267, "lon": 135.8556, "myth": "Mountain itself is the shintai (god-body), no main hall", "deity": "Omononushi", "type": "Mountain Shrine", "tradition": "Shinto"},
    {"name": "Kasuga Taisha, Nara", "lat": 34.6810, "lon": 135.8497, "myth": "Deity arrived on a white deer, 3,000 lanterns", "deity": "Takemikazuchi", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Mount Haguro", "lat": 38.7000, "lon": 139.9833, "myth": "Five-story pagoda in ancient cedar forest, birth mountain", "deity": "Haguro Gongen", "type": "Sacred Mountain", "tradition": "Shugendo"},
    {"name": "Kirishima Shrine", "lat": 31.8658, "lon": 130.8703, "myth": "Where Ninigi-no-Mikoto descended from heaven", "deity": "Ninigi-no-Mikoto", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Ama-no-Iwato Shrine", "lat": 32.7550, "lon": 131.3508, "myth": "Cave where Amaterasu hid, the heavenly rock cave", "deity": "Amaterasu", "type": "Cave Shrine", "tradition": "Shinto"},
    {"name": "Enoshima Shrine", "lat": 35.2994, "lon": 139.4797, "myth": "Island rose from the sea, dragon and goddess love story", "deity": "Benzaiten / Dragon", "type": "Island Shrine", "tradition": "Shinto / Buddhist"},
    {"name": "Zeniarai Benten, Kamakura", "lat": 35.3236, "lon": 139.5422, "myth": "Washing money in spring water multiplies wealth", "deity": "Benzaiten", "type": "Money-Washing Shrine", "tradition": "Shinto"},
    {"name": "Mount Yoshino", "lat": 34.3667, "lon": 135.8667, "myth": "Thousands of cherry trees, En no Gyoja's mountain asceticism", "deity": "Zao Gongen", "type": "Sacred Mountain", "tradition": "Shugendo"},
    {"name": "Konpira Shrine, Shikoku", "lat": 34.1767, "lon": 133.8186, "myth": "Sea god's shrine, 1,368 stone steps to the main hall", "deity": "Omono-nushi (sea)", "type": "Shrine", "tradition": "Shinto"},
    {"name": "Tsubaki Grand Shrine", "lat": 34.8917, "lon": 136.4683, "myth": "Sarutahiko (earthly kami guide) shrine, oldest shrine in Japan", "deity": "Sarutahiko", "type": "Grand Shrine", "tradition": "Shinto"},
    {"name": "Suwa Taisha", "lat": 36.0744, "lon": 138.0983, "myth": "One of oldest shrines, Onbashira log festival, dragon lake", "deity": "Takeminakata", "type": "Grand Shrine", "tradition": "Shinto"},
]

MESOAMERICAN_SITES = [
    {"name": "Teotihuacan", "lat": 19.6925, "lon": -98.8438, "myth": "Where the gods sacrificed themselves to create the fifth sun", "deity": "Quetzalcoatl / Tlaloc", "culture": "Teotihuacan", "type": "Pyramid City"},
    {"name": "Chichen Itza", "lat": 20.6843, "lon": -88.5678, "myth": "Feathered serpent descends pyramid at equinox", "deity": "Kukulkan", "culture": "Maya / Toltec", "type": "Temple Complex"},
    {"name": "Machu Picchu", "lat": -13.1631, "lon": -72.5450, "myth": "Royal estate of Pachacuti, sacred Intihuatana stone", "deity": "Inti (Sun God)", "culture": "Inca", "type": "Citadel"},
    {"name": "Tikal", "lat": 17.2220, "lon": -89.6237, "myth": "Great Maya city where kings communed with gods", "deity": "Itzamna / Chaak", "culture": "Maya", "type": "Temple City"},
    {"name": "Nazca Lines", "lat": -14.7350, "lon": -75.1300, "myth": "Giant geoglyphs visible from the sky, offerings to sky gods", "deity": "Sky deities", "culture": "Nazca", "type": "Geoglyphs"},
    {"name": "Templo Mayor, Mexico City", "lat": 19.4352, "lon": -99.1317, "myth": "Twin temples to Huitzilopochtli and Tlaloc, heart of Aztec cosmos", "deity": "Huitzilopochtli / Tlaloc", "culture": "Aztec", "type": "Twin Pyramid"},
    {"name": "Palenque", "lat": 17.4838, "lon": -92.0462, "myth": "Tomb of Pakal the Great, sarcophagus lid cosmos scene", "deity": "K'inich Janaab Pakal", "culture": "Maya", "type": "Temple / Tomb"},
    {"name": "Monte Alban", "lat": 17.0436, "lon": -96.7681, "myth": "Zapotec cloud people's mountaintop capital", "deity": "Cocijo (lightning)", "culture": "Zapotec", "type": "Mountaintop City"},
    {"name": "Uxmal", "lat": 20.3594, "lon": -89.7714, "myth": "Magician's Pyramid built in one night by a dwarf", "deity": "Chaak", "culture": "Maya", "type": "Pyramid Complex"},
    {"name": "Tulum", "lat": 20.2144, "lon": -87.4292, "myth": "Walled coastal city, lighthouse for Maya traders", "deity": "Ek Chuaj (trade god)", "culture": "Maya", "type": "Coastal Temple"},
    {"name": "Copan", "lat": 14.8400, "lon": -89.1400, "myth": "Great Maya city of astronomers, Hieroglyphic Stairway", "deity": "K'inich Yax K'uk' Mo'", "culture": "Maya", "type": "Temple City"},
    {"name": "Tula (Tollan)", "lat": 20.0651, "lon": -99.3406, "myth": "Toltec capital, Quetzalcoatl exiled by Tezcatlipoca", "deity": "Quetzalcoatl / Tezcatlipoca", "culture": "Toltec", "type": "Legendary Capital"},
    {"name": "Cholula Great Pyramid", "lat": 19.0578, "lon": -98.3017, "myth": "Largest pyramid by volume, built for Quetzalcoatl", "deity": "Quetzalcoatl", "culture": "Olmec-Aztec", "type": "Great Pyramid"},
    {"name": "Calakmul", "lat": 18.1056, "lon": -89.8108, "myth": "Snake Kingdom, rival of Tikal in Maya superpower wars", "deity": "Kaan dynasty", "culture": "Maya", "type": "Temple City"},
    {"name": "Sacsayhuaman, Cusco", "lat": -13.5094, "lon": -71.9822, "myth": "Inca fortress of precisely fitted megaliths", "deity": "Inti / Viracocha", "culture": "Inca", "type": "Megalithic Fortress"},
    {"name": "Ollantaytambo", "lat": -13.2581, "lon": -72.2625, "myth": "Inca temple-fortress, Temple of the Sun", "deity": "Inti", "culture": "Inca", "type": "Temple Fortress"},
    {"name": "Lake Titicaca - Isla del Sol", "lat": -16.0167, "lon": -69.1667, "myth": "Birthplace of the Inca sun god and first Inca rulers", "deity": "Inti / Manco Capac", "culture": "Inca / Tiwanaku", "type": "Sacred Island"},
    {"name": "Tiwanaku", "lat": -16.5553, "lon": -68.6731, "myth": "Viracocha created humanity here, Gate of the Sun", "deity": "Viracocha", "culture": "Tiwanaku", "type": "Temple City"},
    {"name": "El Tajin", "lat": 20.4483, "lon": -97.3783, "myth": "Pyramid of the Niches (365 niches, one per day)", "deity": "Tajin (thunder)", "culture": "Totonac", "type": "Pyramid"},
    {"name": "La Venta", "lat": 18.1031, "lon": -94.0425, "myth": "Olmec ceremonial center, colossal head sculptures", "deity": "Jaguar deity", "culture": "Olmec", "type": "Ceremonial Center"},
    {"name": "San Lorenzo Tenochtitlan", "lat": 17.7539, "lon": -94.7611, "myth": "Oldest Olmec center, mother culture of Mesoamerica", "deity": "Were-Jaguar", "culture": "Olmec", "type": "Ceremonial Center"},
    {"name": "Mitla", "lat": 16.9244, "lon": -96.3597, "myth": "Place of the Dead, Zapotec entrance to the underworld", "deity": "Death deities", "culture": "Zapotec / Mixtec", "type": "Underworld Gate"},
    {"name": "Bonampak", "lat": 16.7042, "lon": -91.0650, "myth": "Vivid murals depicting Maya warfare and ritual", "deity": "War deities", "culture": "Maya", "type": "Mural Temple"},
    {"name": "Yaxchilan", "lat": 16.8997, "lon": -90.9667, "myth": "Maya city of blood-letting rituals to summon Vision Serpent", "deity": "Vision Serpent", "culture": "Maya", "type": "Ritual City"},
    {"name": "Moray, Peru", "lat": -13.3294, "lon": -72.1972, "myth": "Inca agricultural terraces, sacred crop laboratory", "deity": "Pachamama", "culture": "Inca", "type": "Agricultural Temple"},
    {"name": "Chavin de Huantar", "lat": -9.5950, "lon": -77.1772, "myth": "Oracle temple with psychedelic rituals, Lanzon idol", "deity": "Staff God", "culture": "Chavin", "type": "Oracle Temple"},
    {"name": "Caral", "lat": -10.8928, "lon": -77.5203, "myth": "Oldest city in the Americas (~3000 BCE), sacred pyramids", "deity": "Unknown deities", "culture": "Norte Chico", "type": "Ancient City"},
    {"name": "Huaca de la Luna", "lat": -8.1147, "lon": -78.9750, "myth": "Moche temple with Ai Apaec (Decapitator God) murals", "deity": "Ai Apaec", "culture": "Moche", "type": "Temple"},
    {"name": "Xochicalco", "lat": 18.8042, "lon": -99.2958, "myth": "Feathered Serpent reliefs, astronomical observatory", "deity": "Quetzalcoatl", "culture": "Epiclassic", "type": "Hilltop Temple"},
    {"name": "Chan Chan", "lat": -8.1056, "lon": -79.0750, "myth": "Largest adobe city, Chimu moon-worshipping capital", "deity": "Si (Moon Goddess)", "culture": "Chimu", "type": "Adobe Capital"},
]

BIBLICAL_SITES = [
    {"name": "Jerusalem - Temple Mount", "lat": 31.7781, "lon": 35.2354, "myth": "Solomon's Temple, Dome of the Rock, Muhammad's ascent", "tradition": "Judaism / Islam / Christianity", "type": "Temple / Mosque", "era": "Multi-era"},
    {"name": "Bethlehem", "lat": 31.7054, "lon": 35.2024, "myth": "Birthplace of Jesus Christ", "tradition": "Christianity", "type": "Birth Site", "era": "1st c. CE"},
    {"name": "Mount Sinai (Jebel Musa)", "lat": 28.5394, "lon": 33.9753, "myth": "Moses received the Ten Commandments", "tradition": "Judaism / Christianity / Islam", "type": "Sacred Mountain", "era": "~1300 BCE"},
    {"name": "Dead Sea", "lat": 31.5000, "lon": 35.5000, "myth": "Sodom and Gomorrah destroyed nearby, Lot's wife pillar", "tradition": "Judaism / Christianity / Islam", "type": "Salt Sea", "era": "Patriarchal"},
    {"name": "Nazareth", "lat": 32.7019, "lon": 35.2978, "myth": "Childhood home of Jesus, Annunciation", "tradition": "Christianity", "type": "Holy Town", "era": "1st c. CE"},
    {"name": "Sea of Galilee", "lat": 32.8233, "lon": 35.5811, "myth": "Jesus walked on water, calmed the storm", "tradition": "Christianity", "type": "Sacred Lake", "era": "1st c. CE"},
    {"name": "Mount Ararat", "lat": 39.7019, "lon": 44.2983, "myth": "Noah's Ark came to rest here after the Great Flood", "tradition": "Judaism / Christianity / Islam", "type": "Mountain", "era": "Antediluvian"},
    {"name": "Jericho", "lat": 31.8611, "lon": 35.4428, "myth": "Walls fell when Joshua's trumpets sounded", "tradition": "Judaism / Christianity", "type": "Ancient City", "era": "~1400 BCE"},
    {"name": "Hebron - Cave of Machpelah", "lat": 31.5244, "lon": 35.1108, "myth": "Tomb of Abraham, Sarah, Isaac, Rebecca, Jacob, Leah", "tradition": "Judaism / Christianity / Islam", "type": "Patriarchal Tomb", "era": "Patriarchal"},
    {"name": "Church of the Holy Sepulchre", "lat": 31.7785, "lon": 35.2296, "myth": "Site of Jesus's crucifixion and resurrection", "tradition": "Christianity", "type": "Church", "era": "1st c. CE"},
    {"name": "Mount of Olives", "lat": 31.7781, "lon": 35.2476, "myth": "Jesus's ascension to heaven, Garden of Gethsemane", "tradition": "Christianity", "type": "Sacred Mountain", "era": "1st c. CE"},
    {"name": "Jordan River - Bethabara", "lat": 31.8369, "lon": 35.5503, "myth": "Baptism of Jesus by John the Baptist", "tradition": "Christianity", "type": "River / Baptism Site", "era": "1st c. CE"},
    {"name": "Capernaum", "lat": 32.8808, "lon": 35.5753, "myth": "Jesus's base of ministry, Peter's house, miracles", "tradition": "Christianity", "type": "Town Ruins", "era": "1st c. CE"},
    {"name": "Mount Tabor", "lat": 32.6869, "lon": 35.3903, "myth": "Transfiguration of Jesus", "tradition": "Christianity", "type": "Sacred Mountain", "era": "1st c. CE"},
    {"name": "Cana (Kafr Kanna)", "lat": 32.7500, "lon": 35.3394, "myth": "Jesus turned water into wine (first miracle)", "tradition": "Christianity", "type": "Miracle Site", "era": "1st c. CE"},
    {"name": "Damascus", "lat": 33.5138, "lon": 36.2765, "myth": "Paul's conversion on the road to Damascus", "tradition": "Christianity / Islam", "type": "Ancient City", "era": "1st c. CE"},
    {"name": "Mecca - Kaaba", "lat": 21.4225, "lon": 39.8262, "myth": "House built by Abraham and Ishmael, holiest Islamic site", "tradition": "Islam", "type": "Sacred Shrine", "era": "Abrahamic"},
    {"name": "Medina - Al-Masjid an-Nabawi", "lat": 24.4672, "lon": 39.6112, "myth": "Prophet Muhammad's mosque and burial place", "tradition": "Islam", "type": "Mosque / Tomb", "era": "7th c. CE"},
    {"name": "Bethany (Al-Eizariya)", "lat": 31.7667, "lon": 35.2583, "myth": "Jesus raised Lazarus from the dead", "tradition": "Christianity", "type": "Miracle Site", "era": "1st c. CE"},
    {"name": "Mount Nebo", "lat": 31.7672, "lon": 35.7256, "myth": "Moses viewed the Promised Land before dying", "tradition": "Judaism / Christianity", "type": "Sacred Mountain", "era": "~1200 BCE"},
    {"name": "Qumran", "lat": 31.7414, "lon": 35.4586, "myth": "Dead Sea Scrolls discovered, Essene community", "tradition": "Judaism", "type": "Scroll Caves", "era": "2nd c. BCE - 1st c. CE"},
    {"name": "Ur of the Chaldees (Tell el-Muqayyar)", "lat": 30.9628, "lon": 46.1031, "myth": "Abraham's birthplace, ziggurat of Nanna", "tradition": "Judaism / Christianity / Islam", "type": "Ancient City", "era": "~2000 BCE"},
    {"name": "Babylon (Hillah)", "lat": 32.5422, "lon": 44.4211, "myth": "Tower of Babel, Babylonian exile of Jews", "tradition": "Judaism / Christianity", "type": "Ancient City", "era": "6th c. BCE"},
    {"name": "Nineveh (Mosul)", "lat": 36.3594, "lon": 43.1531, "myth": "Jonah preached here after the whale", "tradition": "Judaism / Christianity / Islam", "type": "Ancient City", "era": "8th c. BCE"},
    {"name": "Antioch (Antakya)", "lat": 36.2025, "lon": 36.1594, "myth": "Followers first called Christians here", "tradition": "Christianity", "type": "Ancient City", "era": "1st c. CE"},
    {"name": "Ephesus", "lat": 37.9411, "lon": 27.3417, "myth": "Paul's epistles, Temple of Artemis, possible home of Mary", "tradition": "Christianity", "type": "Ancient City / Temple", "era": "1st c. CE"},
    {"name": "Patmos", "lat": 37.3100, "lon": 26.5500, "myth": "John wrote the Book of Revelation here", "tradition": "Christianity", "type": "Sacred Island", "era": "1st c. CE"},
    {"name": "Mount Carmel", "lat": 32.7357, "lon": 35.0475, "myth": "Elijah challenged the prophets of Baal with fire from heaven", "tradition": "Judaism / Christianity", "type": "Sacred Mountain", "era": "9th c. BCE"},
    {"name": "Beer-Sheba", "lat": 31.2518, "lon": 34.7913, "myth": "Abraham dug a well, swore an oath with Abimelech", "tradition": "Judaism", "type": "Patriarchal Site", "era": "Patriarchal"},
    {"name": "Bethel (Beitin)", "lat": 31.9311, "lon": 35.2306, "myth": "Jacob's Ladder dream, stairway to heaven", "tradition": "Judaism / Christianity", "type": "Dream Site", "era": "Patriarchal"},
    {"name": "Sodom (Bab edh-Dhra)", "lat": 31.2517, "lon": 35.5244, "myth": "City destroyed by God for wickedness, fire and brimstone", "tradition": "Judaism / Christianity / Islam", "type": "Destroyed City", "era": "Patriarchal"},
    {"name": "Tabgha", "lat": 32.8722, "lon": 35.5469, "myth": "Miracle of loaves and fishes (feeding the 5,000)", "tradition": "Christianity", "type": "Miracle Site", "era": "1st c. CE"},
    {"name": "Samaria (Sebastia)", "lat": 32.2750, "lon": 35.1903, "myth": "Capital of northern Israel, Elijah and the prophets", "tradition": "Judaism / Christianity", "type": "Ancient Capital", "era": "Iron Age"},
    {"name": "Sidon", "lat": 33.5606, "lon": 35.3714, "myth": "Phoenician city, Jesus visited and healed", "tradition": "Christianity", "type": "Ancient Port", "era": "Multi-era"},
    {"name": "Tyre", "lat": 33.2706, "lon": 35.1969, "myth": "Phoenician city, prophesied destruction by Ezekiel", "tradition": "Judaism / Christianity", "type": "Ancient Port", "era": "Multi-era"},
    {"name": "Garden of Eden (traditional: Qurnah)", "lat": 31.0117, "lon": 47.4333, "myth": "Where Tigris and Euphrates meet, traditional Eden site", "tradition": "Judaism / Christianity / Islam", "type": "Paradise", "era": "Creation"},
    {"name": "Haran (Harran)", "lat": 36.8642, "lon": 39.0314, "myth": "Abraham stayed here, Jacob fled to Laban", "tradition": "Judaism / Christianity / Islam", "type": "Patriarchal City", "era": "Patriarchal"},
    {"name": "Masada", "lat": 31.3156, "lon": 35.3536, "myth": "Last stand of Jewish zealots against Rome (73 CE)", "tradition": "Judaism", "type": "Fortress", "era": "1st c. CE"},
    {"name": "Ein Gedi", "lat": 31.4500, "lon": 35.3833, "myth": "David hid from Saul in these caves", "tradition": "Judaism", "type": "Oasis / Cave", "era": "~1000 BCE"},
    {"name": "Megiddo (Armageddon)", "lat": 32.5847, "lon": 35.1847, "myth": "Site of the prophesied final battle (Revelation)", "tradition": "Christianity", "type": "Ancient Fortress", "era": "Apocalyptic"},
]

CHINESE_SITES = [
    {"name": "Kunlun Mountains", "lat": 35.5000, "lon": 80.0000, "myth": "Jade palace of the Queen Mother of the West (Xi Wangmu)", "deity": "Xi Wangmu", "type": "Mythical Mountain", "tradition": "Daoism"},
    {"name": "Mount Tai (Taishan)", "lat": 36.2563, "lon": 117.1008, "myth": "Most sacred of the Five Great Mountains, emperors' heavenly mandate", "deity": "Jade Emperor", "type": "Sacred Mountain", "tradition": "Daoism / Confucianism"},
    {"name": "Shaolin Temple", "lat": 34.5078, "lon": 112.9372, "myth": "Bodhidharma meditated 9 years facing a wall, origin of kung fu", "deity": "Bodhidharma", "type": "Martial Temple", "tradition": "Chan Buddhism"},
    {"name": "Wudang Mountains", "lat": 32.4000, "lon": 111.0000, "myth": "Birthplace of tai chi, Zhang Sanfeng's immortal arts", "deity": "Zhenwu / Zhang Sanfeng", "type": "Sacred Mountain", "tradition": "Daoism"},
    {"name": "Mount Hua (Huashan)", "lat": 34.4756, "lon": 110.0894, "myth": "Western Great Mountain, Chen Tuan's sleeping immortal cave", "deity": "White Emperor", "type": "Sacred Mountain", "tradition": "Daoism"},
    {"name": "Mount Emei", "lat": 29.5200, "lon": 103.3322, "myth": "Bodhisattva Samantabhadra's sacred peak", "deity": "Samantabhadra", "type": "Buddhist Mountain", "tradition": "Buddhism"},
    {"name": "Mount Wutai", "lat": 39.0833, "lon": 113.5833, "myth": "Bodhisattva Manjushri's wisdom peak", "deity": "Manjushri", "type": "Buddhist Mountain", "tradition": "Buddhism"},
    {"name": "Mount Putuo", "lat": 30.0000, "lon": 122.3833, "myth": "Bodhisattva Guanyin's island sanctuary", "deity": "Guanyin", "type": "Buddhist Island", "tradition": "Buddhism"},
    {"name": "Mount Jiuhua", "lat": 30.4833, "lon": 117.8000, "myth": "Bodhisattva Ksitigarbha's sacred peak, Dizang's domain", "deity": "Dizang / Ksitigarbha", "type": "Buddhist Mountain", "tradition": "Buddhism"},
    {"name": "Longmen Grottoes", "lat": 34.5653, "lon": 112.4706, "myth": "Dragon Gate where carp leap to become dragons", "deity": "Dragon King", "type": "Grotto Temples", "tradition": "Buddhism"},
    {"name": "Mount Song (Songshan)", "lat": 34.4842, "lon": 112.9569, "myth": "Central Great Mountain, axis of the world", "deity": "Central Emperor", "type": "Sacred Mountain", "tradition": "Daoism / Buddhism"},
    {"name": "Mount Heng (Hengshan North)", "lat": 39.6833, "lon": 113.7333, "myth": "Northern Great Mountain, Hanging Temple defies gravity", "deity": "Black Emperor", "type": "Sacred Mountain", "tradition": "Daoism"},
    {"name": "Mount Heng (Hengshan South)", "lat": 27.2542, "lon": 112.7083, "myth": "Southern Great Mountain, Fire Emperor's domain", "deity": "Red Emperor", "type": "Sacred Mountain", "tradition": "Daoism"},
    {"name": "West Lake (Xi Hu), Hangzhou", "lat": 30.2500, "lon": 120.1500, "myth": "Legend of the White Snake, Lady White meets Xu Xian", "deity": "White Snake / Xu Xian", "type": "Legendary Lake", "tradition": "Folk legend"},
    {"name": "Leifeng Pagoda, Hangzhou", "lat": 30.2319, "lon": 120.1489, "myth": "White Snake spirit trapped beneath by monk Fahai", "deity": "White Snake / Fahai", "type": "Pagoda", "tradition": "Folk legend"},
    {"name": "Flaming Mountains, Turpan", "lat": 42.9500, "lon": 89.5833, "myth": "Sun Wukong (Monkey King) knocked over Laozi's furnace here", "deity": "Sun Wukong", "type": "Legendary Landmark", "tradition": "Journey to the West"},
    {"name": "Flower Fruit Mountain (Lianyungang)", "lat": 34.6147, "lon": 119.1978, "myth": "Birthplace of the Monkey King (Sun Wukong)", "deity": "Sun Wukong", "type": "Mythical Mountain", "tradition": "Journey to the West"},
    {"name": "Qingcheng Mountain", "lat": 30.8983, "lon": 103.5686, "myth": "Birthplace of Daoism, Zhang Daoling founded Tianshi sect", "deity": "Zhang Daoling", "type": "Daoist Mountain", "tradition": "Daoism"},
    {"name": "Maoshan", "lat": 31.8000, "lon": 119.1500, "myth": "Center of Shangqing Daoism, exorcism traditions", "deity": "Mao brothers", "type": "Daoist Mountain", "tradition": "Daoism"},
    {"name": "Qufu - Temple of Confucius", "lat": 35.6017, "lon": 116.9867, "myth": "Birthplace and temple of Confucius, sage of all ages", "deity": "Confucius", "type": "Temple", "tradition": "Confucianism"},
    {"name": "Yellow River Source (Gyaring Lake)", "lat": 34.8833, "lon": 97.7333, "myth": "Dragon's blood river, Yu the Great tamed the floods", "deity": "Yu the Great / Dragon", "type": "River Source", "tradition": "Myth / History"},
    {"name": "Dongting Lake", "lat": 29.3333, "lon": 112.8333, "myth": "Dragon King of Dongting, Qu Yuan drowned here (Dragon Boat origin)", "deity": "Dragon King / Qu Yuan", "type": "Sacred Lake", "tradition": "Folk / Historical"},
    {"name": "Penglai", "lat": 37.8000, "lon": 120.7500, "myth": "Legendary island of the Eight Immortals", "deity": "Eight Immortals", "type": "Mythical Island / Pavilion", "tradition": "Daoism"},
    {"name": "Tiger Leaping Gorge", "lat": 27.1833, "lon": 100.1667, "myth": "Tiger leapt across the Yangtze on a boulder", "deity": "Tiger spirit", "type": "Sacred Gorge", "tradition": "Naxi / Folk"},
    {"name": "Fengdu Ghost City", "lat": 29.8667, "lon": 107.7000, "myth": "City of the dead, depicts the underworld courts of Diyu", "deity": "Yanluo Wang (Yama)", "type": "Underworld City", "tradition": "Buddhism / Daoism"},
    {"name": "Mogao Caves, Dunhuang", "lat": 40.0361, "lon": 94.8019, "myth": "1,000 Buddha caves, Silk Road spiritual gateway", "deity": "Buddhist pantheon", "type": "Grotto Temples", "tradition": "Buddhism"},
    {"name": "Labrang Monastery", "lat": 35.1939, "lon": 102.5117, "myth": "One of six great Gelug monasteries, living Buddha tradition", "deity": "Tsongkhapa", "type": "Tibetan Monastery", "tradition": "Tibetan Buddhism"},
    {"name": "Potala Palace, Lhasa", "lat": 29.6575, "lon": 91.1169, "myth": "Winter palace of the Dalai Lama, Avalokiteshvara's earthly abode", "deity": "Avalokiteshvara / Dalai Lama", "type": "Palace / Temple", "tradition": "Tibetan Buddhism"},
    {"name": "Jokhang Temple, Lhasa", "lat": 29.6525, "lon": 91.1328, "myth": "Built over a lake-demoness's heart to pin her down", "deity": "Jowo Shakyamuni", "type": "Temple", "tradition": "Tibetan Buddhism"},
    {"name": "Nuwa's Temple, She Huang", "lat": 36.5500, "lon": 114.0833, "myth": "Goddess Nuwa repaired the sky and created humanity", "deity": "Nuwa", "type": "Creation Temple", "tradition": "Chinese mythology"},
]

CRYPTID_SITES = [
    {"name": "Loch Ness, Scotland", "lat": 57.3229, "lon": -4.4244, "myth": "Nessie the Loch Ness Monster sighted since 565 CE", "creature": "Loch Ness Monster", "type": "Lake Monster", "first_sighting": "565 CE"},
    {"name": "Bluff Creek, California", "lat": 41.1500, "lon": -123.6000, "myth": "Patterson-Gimlin film of Bigfoot (1967)", "creature": "Bigfoot / Sasquatch", "type": "Primate Cryptid", "first_sighting": "1958"},
    {"name": "Mount Everest Base Camp", "lat": 28.0025, "lon": 86.8528, "myth": "Yeti tracks found by Shipton expedition (1951)", "creature": "Yeti / Abominable Snowman", "type": "Primate Cryptid", "first_sighting": "1832"},
    {"name": "Canovanas, Puerto Rico", "lat": 18.3797, "lon": -65.9014, "myth": "First reported Chupacabra attacks on livestock (1995)", "creature": "Chupacabra", "type": "Vampiric Cryptid", "first_sighting": "1995"},
    {"name": "Point Pleasant, West Virginia", "lat": 38.8451, "lon": -82.1371, "myth": "Mothman sightings before Silver Bridge collapse (1966-67)", "creature": "Mothman", "type": "Winged Humanoid", "first_sighting": "1966"},
    {"name": "Flatwoods, West Virginia", "lat": 38.7223, "lon": -80.6518, "myth": "Flatwoods Monster encounter (1952)", "creature": "Flatwoods Monster", "type": "Alien Entity", "first_sighting": "1952"},
    {"name": "Lake Champlain, Vermont", "lat": 44.5333, "lon": -73.3333, "myth": "Champ sightings, America's Loch Ness Monster", "creature": "Champ", "type": "Lake Monster", "first_sighting": "1609"},
    {"name": "Dover, Massachusetts", "lat": 42.2350, "lon": -71.2831, "myth": "Dover Demon sighted by teenagers (1977)", "creature": "Dover Demon", "type": "Unknown Entity", "first_sighting": "1977"},
    {"name": "Fouke, Arkansas", "lat": 33.2676, "lon": -94.0307, "myth": "Fouke Monster (Boggy Creek creature) reports since 1946", "creature": "Fouke Monster", "type": "Primate Cryptid", "first_sighting": "1946"},
    {"name": "Pine Barrens, New Jersey", "lat": 39.8000, "lon": -74.5000, "myth": "Jersey Devil, 13th child of Mother Leeds", "creature": "Jersey Devil", "type": "Winged Cryptid", "first_sighting": "1735"},
    {"name": "Lake Okanagan, BC, Canada", "lat": 49.9167, "lon": -119.5000, "myth": "Ogopogo lake monster sightings", "creature": "Ogopogo", "type": "Lake Monster", "first_sighting": "1872"},
    {"name": "Nahuel Huapi Lake, Argentina", "lat": -40.9833, "lon": -71.5000, "myth": "Nahuelito lake monster in Patagonia", "creature": "Nahuelito", "type": "Lake Monster", "first_sighting": "1922"},
    {"name": "Himalayas - Pangboche, Nepal", "lat": 27.8500, "lon": 86.7833, "myth": "Pangboche Hand and Yeti scalp relics in monastery", "creature": "Yeti", "type": "Primate Cryptid", "first_sighting": "Ancient"},
    {"name": "Congo River Basin", "lat": 1.5000, "lon": 18.0000, "myth": "Mokele-mbembe, living dinosaur in the swamps", "creature": "Mokele-mbembe", "type": "Sauropod Cryptid", "first_sighting": "1776"},
    {"name": "Skunk Ape Trail, Florida", "lat": 25.7617, "lon": -80.9467, "myth": "Florida's Bigfoot, foul-smelling ape-like creature", "creature": "Skunk Ape", "type": "Primate Cryptid", "first_sighting": "1957"},
    {"name": "Enfield, Illinois", "lat": 38.0767, "lon": -88.3464, "myth": "Enfield Horror, three-legged creature attacked a boy (1973)", "creature": "Enfield Horror", "type": "Unknown Entity", "first_sighting": "1973"},
    {"name": "Loch Morar, Scotland", "lat": 56.9500, "lon": -5.7500, "myth": "Morag, Scotland's other lake monster", "creature": "Morag", "type": "Lake Monster", "first_sighting": "1887"},
    {"name": "Lake Tianchi, China", "lat": 42.0042, "lon": 128.0600, "myth": "Tianchi Monster in Heaven Lake, giant serpentine creature", "creature": "Tianchi Monster", "type": "Lake Monster", "first_sighting": "1903"},
    {"name": "Mapinguari Territory, Amazon", "lat": -3.0000, "lon": -60.0000, "myth": "Giant ground sloth cryptid in the Amazon rainforest", "creature": "Mapinguari", "type": "Ground Sloth Cryptid", "first_sighting": "Pre-colonial"},
    {"name": "Loveland, Ohio", "lat": 39.2689, "lon": -84.2633, "myth": "Loveland Frogman, bipedal frog-like creature (1955)", "creature": "Loveland Frogman", "type": "Amphibian Humanoid", "first_sighting": "1955"},
    {"name": "Mount Shasta, California", "lat": 41.4092, "lon": -122.1949, "myth": "Lemurians living inside the mountain, strange lights", "creature": "Lemurians", "type": "Lost Civilization", "first_sighting": "1880s"},
    {"name": "Skinwalker Ranch, Utah", "lat": 40.2589, "lon": -109.8878, "myth": "Shapeshifters, UFOs, cattle mutilations, paranormal hotspot", "creature": "Skinwalker", "type": "Shapeshifter", "first_sighting": "Navajo tradition"},
    {"name": "Lake Storsjön, Sweden", "lat": 63.1167, "lon": 14.3667, "myth": "Storsjöodjuret, Scandinavian lake monster", "creature": "Storsjöodjuret", "type": "Lake Monster", "first_sighting": "1635"},
    {"name": "Lusca Blue Hole, Bahamas", "lat": 24.1167, "lon": -77.8333, "myth": "Lusca, giant octopus-shark hybrid in blue holes", "creature": "Lusca", "type": "Sea Monster", "first_sighting": "Folk tradition"},
    {"name": "Canvey Island, England", "lat": 51.5167, "lon": 0.5833, "myth": "Canvey Island Monster, strange carcasses washed ashore (1953-54)", "creature": "Canvey Island Monster", "type": "Sea Creature", "first_sighting": "1953"},
    {"name": "Hopkinsville, Kentucky", "lat": 36.8656, "lon": -87.4886, "myth": "Kelly-Hopkinsville encounter, goblin-like aliens (1955)", "creature": "Hopkinsville Goblins", "type": "Alien Entity", "first_sighting": "1955"},
    {"name": "Roswell, New Mexico", "lat": 33.3943, "lon": -104.5230, "myth": "1947 UFO crash, alleged alien bodies recovered", "creature": "Grey Aliens", "type": "Alien Entity", "first_sighting": "1947"},
    {"name": "Beast of Gevaudan territory, France", "lat": 44.6833, "lon": 3.5000, "myth": "Monstrous wolf-like beast killed over 100 people (1764-67)", "creature": "Beast of Gevaudan", "type": "Wolf Cryptid", "first_sighting": "1764"},
    {"name": "Zanzibar Channel, Tanzania", "lat": -6.1667, "lon": 39.3333, "myth": "Popobawa, shape-shifting bat creature terrorizing villages", "creature": "Popobawa", "type": "Shapeshifter", "first_sighting": "1965"},
    {"name": "Lake Ikeda, Japan", "lat": 31.2333, "lon": 130.5667, "myth": "Issie, Japan's lake monster resembling a plesiosaur", "creature": "Issie", "type": "Lake Monster", "first_sighting": "1961"},
]

# ---------------------------------------------------------------------------
# Marker color & icon mapping per mode
# ---------------------------------------------------------------------------
MODE_THEMES = {
    "Greek Mythology Sites": {"color": "#f59e0b", "icon": "bolt", "prefix": "fa", "marker_color": "orange"},
    "Norse Mythology Locations": {"color": "#60a5fa", "icon": "shield", "prefix": "fa", "marker_color": "blue"},
    "Egyptian Sacred Sites": {"color": "#fbbf24", "icon": "sun-o", "prefix": "fa", "marker_color": "beige"},
    "Celtic & Arthurian Legends": {"color": "#34d399", "icon": "pagelines", "prefix": "fa", "marker_color": "green"},
    "Hindu Epic Geography": {"color": "#fb923c", "icon": "fire", "prefix": "fa", "marker_color": "orange"},
    "Japanese Mythology": {"color": "#f472b6", "icon": "star", "prefix": "fa", "marker_color": "pink"},
    "Mesoamerican Sacred Sites": {"color": "#a78bfa", "icon": "pyramid", "prefix": "fa", "marker_color": "purple"},
    "Biblical & Holy Land": {"color": "#fde68a", "icon": "book", "prefix": "fa", "marker_color": "beige"},
    "Chinese Mythology Sites": {"color": "#ef4444", "icon": "yin-yang", "prefix": "fa", "marker_color": "red"},
    "Cryptid & Monster Sightings": {"color": "#22d3ee", "icon": "eye", "prefix": "fa", "marker_color": "darkgreen"},
}

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _get_data_for_mode(mode: str) -> list[dict]:
    """Return the hardcoded dataset for the selected map mode."""
    mapping = {
        "Greek Mythology Sites": GREEK_SITES,
        "Norse Mythology Locations": NORSE_SITES,
        "Egyptian Sacred Sites": EGYPTIAN_SITES,
        "Celtic & Arthurian Legends": CELTIC_SITES,
        "Hindu Epic Geography": HINDU_SITES,
        "Japanese Mythology": JAPANESE_SITES,
        "Mesoamerican Sacred Sites": MESOAMERICAN_SITES,
        "Biblical & Holy Land": BIBLICAL_SITES,
        "Chinese Mythology Sites": CHINESE_SITES,
        "Cryptid & Monster Sightings": CRYPTID_SITES,
    }
    return mapping.get(mode, [])


def _build_popup_html(site: dict, mode: str) -> str:
    """Build a dark-themed HTML popup for a map marker."""
    name = html.escape(str(site.get("name", "")))
    myth = html.escape(str(site.get("myth", "")))
    stype = html.escape(str(site.get("type", "")))

    # Mode-specific secondary field
    if mode == "Greek Mythology Sites":
        secondary_label = "Deity / Hero"
        secondary_val = html.escape(str(site.get("deity", "")))
        tertiary_label = "Era"
        tertiary_val = html.escape(str(site.get("era", "")))
    elif mode == "Norse Mythology Locations":
        secondary_label = "Deity / Figure"
        secondary_val = html.escape(str(site.get("deity", "")))
        tertiary_label = "Saga Source"
        tertiary_val = html.escape(str(site.get("saga", "")))
    elif mode == "Egyptian Sacred Sites":
        secondary_label = "Deity"
        secondary_val = html.escape(str(site.get("deity", "")))
        tertiary_label = "Dynasty"
        tertiary_val = html.escape(str(site.get("dynasty", "")))
    elif mode == "Celtic & Arthurian Legends":
        secondary_label = "Figure"
        secondary_val = html.escape(str(site.get("deity", "")))
        tertiary_label = "Tradition"
        tertiary_val = html.escape(str(site.get("tradition", "")))
    elif mode == "Hindu Epic Geography":
        secondary_label = "Deity"
        secondary_val = html.escape(str(site.get("deity", "")))
        tertiary_label = "Epic"
        tertiary_val = html.escape(str(site.get("epic", "")))
    elif mode == "Japanese Mythology":
        secondary_label = "Deity / Spirit"
        secondary_val = html.escape(str(site.get("deity", "")))
        tertiary_label = "Tradition"
        tertiary_val = html.escape(str(site.get("tradition", "")))
    elif mode == "Mesoamerican Sacred Sites":
        secondary_label = "Deity / Figure"
        secondary_val = html.escape(str(site.get("deity", "")))
        tertiary_label = "Culture"
        tertiary_val = html.escape(str(site.get("culture", "")))
    elif mode == "Biblical & Holy Land":
        secondary_label = "Tradition"
        secondary_val = html.escape(str(site.get("tradition", "")))
        tertiary_label = "Era"
        tertiary_val = html.escape(str(site.get("era", "")))
    elif mode == "Chinese Mythology Sites":
        secondary_label = "Deity / Figure"
        secondary_val = html.escape(str(site.get("deity", "")))
        tertiary_label = "Tradition"
        tertiary_val = html.escape(str(site.get("tradition", "")))
    elif mode == "Cryptid & Monster Sightings":
        secondary_label = "Creature"
        secondary_val = html.escape(str(site.get("creature", "")))
        tertiary_label = "First Sighting"
        tertiary_val = html.escape(str(site.get("first_sighting", "")))
    else:
        secondary_label = "Detail"
        secondary_val = ""
        tertiary_label = "Info"
        tertiary_val = ""

    return f"""
    <div style="font-family:'Segoe UI',sans-serif;background:{SURFACE};color:{TEXT};
                padding:12px;border-radius:8px;min-width:240px;max-width:320px;
                border:1px solid #2a3550;">
        <h4 style="margin:0 0 6px 0;color:{ACCENT};font-size:14px;">{name}</h4>
        <p style="margin:0 0 4px;font-size:12px;color:#8b97b0;">{stype}</p>
        <p style="margin:0 0 8px;font-size:12px;">{myth}</p>
        <table style="width:100%;font-size:11px;color:#8b97b0;">
            <tr><td><b>{secondary_label}:</b></td><td style="color:{TEXT}">{secondary_val}</td></tr>
            <tr><td><b>{tertiary_label}:</b></td><td style="color:{TEXT}">{tertiary_val}</td></tr>
            <tr><td><b>Coordinates:</b></td><td style="color:{TEXT}">{site.get('lat', 0):.4f}, {site.get('lon', 0):.4f}</td></tr>
        </table>
    </div>
    """


@st.cache_data(ttl=3600)
def _build_dataframe(data: list[dict], mode: str) -> pd.DataFrame:
    """Convert site list to a DataFrame with mode-appropriate columns."""
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.rename(columns={"lat": "Latitude", "lon": "Longitude", "name": "Name",
                            "myth": "Myth / Legend", "type": "Type"})
    col_renames = {
        "deity": "Deity / Figure",
        "era": "Era",
        "saga": "Saga Source",
        "dynasty": "Dynasty",
        "tradition": "Tradition",
        "epic": "Epic",
        "culture": "Culture",
        "creature": "Creature",
        "first_sighting": "First Sighting",
    }
    for old, new in col_renames.items():
        if old in df.columns:
            df = df.rename(columns={old: new})
    return df


def _create_folium_map(data: list[dict], mode: str, selected_types: list[str]) -> folium.Map:
    """Create a themed Folium map with markers for all sites."""
    theme = MODE_THEMES.get(mode, {"color": ACCENT, "icon": "info-sign", "prefix": "glyphicon", "marker_color": "blue"})

    if not data:
        m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
        return m

    # Filter by type
    filtered = [s for s in data if s.get("type", "") in selected_types] if selected_types else data
    if not filtered:
        filtered = data

    lats = [s["lat"] for s in filtered]
    lons = [s["lon"] for s in filtered]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    m = folium.Map(location=[center_lat, center_lon], zoom_start=4, tiles="CartoDB dark_matter")

    for site in filtered:
        popup_html = _build_popup_html(site, mode)
        popup = folium.Popup(popup_html, max_width=340)
        try:
            folium.Marker(
                location=[site["lat"], site["lon"]],
                popup=popup,
                tooltip=site.get("name", "Unknown"),
                icon=folium.Icon(
                    color=theme["marker_color"],
                    icon=theme["icon"],
                    prefix=theme["prefix"],
                ),
            ).add_to(m)
        except Exception:
            folium.Marker(
                location=[site["lat"], site["lon"]],
                popup=popup,
                tooltip=site.get("name", "Unknown"),
                icon=folium.Icon(color=theme["marker_color"], icon="info-sign"),
            ).add_to(m)

    m.fit_bounds([[min(lats) - 1, min(lons) - 1], [max(lats) + 1, max(lons) + 1]])
    return m


def _render_stats(df: pd.DataFrame, mode: str, theme_color: str):
    """Render summary statistics as metric cards."""
    total = len(df)
    if "Type" in df.columns:
        unique_types = df["Type"].nunique()
    else:
        unique_types = 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sites", total)
    with col2:
        st.metric("Unique Types", unique_types)
    with col3:
        if "Deity / Figure" in df.columns:
            st.metric("Deities / Figures", df["Deity / Figure"].nunique())
        elif "Creature" in df.columns:
            st.metric("Creatures", df["Creature"].nunique())
        elif "Tradition" in df.columns:
            st.metric("Traditions", df["Tradition"].nunique())
        else:
            st.metric("Categories", unique_types)
    with col4:
        if "Latitude" in df.columns:
            lat_range = f"{df['Latitude'].min():.1f} to {df['Latitude'].max():.1f}"
            st.metric("Lat Range", lat_range)
        else:
            st.metric("Dataset", mode.split()[0])


def _render_type_chart(df: pd.DataFrame, mode: str, theme_color: str):
    """Render a matplotlib bar chart of site types."""
    if "Type" not in df.columns or df.empty:
        return

    type_counts = df["Type"].value_counts().head(12)
    if type_counts.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)

    bars = ax.barh(type_counts.index[::-1], type_counts.values[::-1], color=theme_color, alpha=0.85)
    ax.set_xlabel("Number of Sites", color=TEXT, fontsize=10)
    ax.set_title(f"Site Types - {mode}", color=TEXT, fontsize=12, pad=10)
    ax.tick_params(colors=TEXT, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.xaxis.label.set_color(TEXT)

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.2, bar.get_y() + bar.get_height() / 2,
                f"{int(width)}", va="center", color=TEXT, fontsize=9)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_csv_download(df: pd.DataFrame, mode: str):
    """Provide a CSV download button."""
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    filename = mode.lower().replace(" ", "_").replace("&", "and") + "_sites.csv"
    st.download_button(
        label=f"Download {mode} CSV",
        data=csv_buf.getvalue(),
        file_name=filename,
        mime="text/csv",
    )


def _render_geographic_scatter(df: pd.DataFrame, mode: str, theme_color: str):
    """Render a matplotlib scatter plot of site locations (lat/lon)."""
    if df.empty or "Latitude" not in df.columns or "Longitude" not in df.columns:
        return

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)

    # Color by type if available
    if "Type" in df.columns:
        types = df["Type"].unique()
        cmap = plt.cm.get_cmap("Set2", len(types))
        for idx, t in enumerate(types):
            subset = df[df["Type"] == t]
            ax.scatter(
                subset["Longitude"], subset["Latitude"],
                c=[cmap(idx)], label=t if len(types) <= 10 else None,
                s=50, alpha=0.85, edgecolors="#2a3550", linewidths=0.5,
            )
        if len(types) <= 10:
            legend = ax.legend(
                fontsize=7, loc="lower left",
                facecolor=SURFACE, edgecolor="#2a3550",
                labelcolor=TEXT, framealpha=0.9,
            )
    else:
        ax.scatter(
            df["Longitude"], df["Latitude"],
            c=theme_color, s=50, alpha=0.85,
            edgecolors="#2a3550", linewidths=0.5,
        )

    ax.set_xlabel("Longitude", color=TEXT, fontsize=10)
    ax.set_ylabel("Latitude", color=TEXT, fontsize=10)
    ax.set_title(f"Geographic Distribution - {mode}", color=TEXT, fontsize=12, pad=10)
    ax.tick_params(colors=TEXT, labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(True, alpha=0.15, color="#5a6580")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_search_panel(df: pd.DataFrame, mode: str):
    """Render a search box to find specific sites by name or keyword."""
    search_query = st.text_input(
        "Search sites by name or keyword",
        placeholder="e.g. Zeus, pyramid, dragon...",
        key="myth_search_input",
    )
    if search_query and not df.empty:
        query_lower = search_query.lower()
        mask = df.apply(
            lambda row: any(query_lower in str(v).lower() for v in row.values),
            axis=1,
        )
        results = df[mask]
        if results.empty:
            st.info(f"No sites found matching '{search_query}' in {mode}.")
        else:
            st.success(f"Found {len(results)} site(s) matching '{search_query}'.")
            st.dataframe(results, width="stretch", hide_index=True)
    elif search_query:
        st.info("No data available.")


def _render_site_detail_card(site: dict, mode: str, theme_color: str):
    """Render a detailed information card for a single selected site."""
    name = html.escape(str(site.get("name", site.get("Name", ""))))
    myth = html.escape(str(site.get("myth", site.get("Myth / Legend", ""))))
    stype = html.escape(str(site.get("type", site.get("Type", ""))))
    lat = site.get("lat", site.get("Latitude", 0))
    lon = site.get("lon", site.get("Longitude", 0))

    detail_rows = ""
    skip_keys = {"name", "Name", "myth", "Myth / Legend", "type", "Type",
                 "lat", "Latitude", "lon", "Longitude"}
    for k, v in site.items():
        if k not in skip_keys and v:
            label = html.escape(str(k).replace("_", " ").title())
            val = html.escape(str(v))
            detail_rows += f"""
            <tr>
                <td style="padding:3px 8px;color:#8b97b0;font-size:12px;"><b>{label}</b></td>
                <td style="padding:3px 8px;color:{TEXT};font-size:12px;">{val}</td>
            </tr>"""

    card_html = f"""
    <div style="background:{SURFACE};border:1px solid #2a3550;border-radius:10px;
                padding:16px;margin:8px 0;">
        <h3 style="color:{theme_color};margin:0 0 4px 0;font-size:16px;">{name}</h3>
        <span style="background:{theme_color}22;color:{theme_color};padding:2px 8px;
                     border-radius:4px;font-size:11px;">{stype}</span>
        <p style="color:{TEXT};margin:10px 0 8px;font-size:13px;line-height:1.5;">{myth}</p>
        <table style="width:100%;">
            {detail_rows}
            <tr>
                <td style="padding:3px 8px;color:#8b97b0;font-size:12px;"><b>Coordinates</b></td>
                <td style="padding:3px 8px;color:{TEXT};font-size:12px;">{lat:.4f}, {lon:.4f}</td>
            </tr>
        </table>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


def _render_legend_panel(mode: str, theme_color: str):
    """Show a brief narrative introduction for each mythology category."""
    descriptions = {
        "Greek Mythology Sites": (
            "The Greek myths form the foundation of Western storytelling. From the thunder-wielding "
            "Zeus atop Mount Olympus to Odysseus's decade-long journey home, these tales are rooted "
            "in real landscapes across the Mediterranean. Temples, oracles, and monster lairs dot the "
            "Greek mainland, its islands, and far-flung colonies."
        ),
        "Norse Mythology Locations": (
            "The Norse cosmos stretched from Asgard to Hel, but its earthly echoes lie scattered "
            "across Scandinavia, Iceland, and the Viking diaspora. Great halls, ship burials, ring "
            "fortresses, and assembly sites mark the places where skalds sang of Odin, Thor, and "
            "the twilight of the gods."
        ),
        "Egyptian Sacred Sites": (
            "For over three millennia, the Nile corridor was the stage for one of humanity's richest "
            "mythologies. Pyramids rose as stairways to the stars, temples housed living gods, and "
            "the boundary between the living and the dead was as thin as the desert's edge. From "
            "Heliopolis to Abu Simbel, every stone tells a divine story."
        ),
        "Celtic & Arthurian Legends": (
            "Mist-shrouded islands, enchanted forests, and ancient stone circles form the landscape "
            "of Celtic myth. The tales of King Arthur, Merlin, and the Knights of the Round Table "
            "interweave with older Irish and Welsh legends of the Tuatha De Danann, Cu Chulainn, "
            "and the Fenian warriors."
        ),
        "Hindu Epic Geography": (
            "The Indian subcontinent is a living map of the great epics. The Ramayana traces Rama's "
            "path from Ayodhya to Lanka; the Mahabharata stages its cosmic battle at Kurukshetra. "
            "Sacred rivers, temple cities, and mountain abodes of the gods connect myth to geography "
            "in an unbroken tradition spanning thousands of years."
        ),
        "Japanese Mythology": (
            "Shinto and Buddhist traditions have sanctified nearly every peak, waterfall, and grove "
            "in Japan. The sun goddess Amaterasu hid in a cave, fox spirits guard rice fields, and "
            "mountain ascetics seek enlightenment on volcanic slopes. From Ise's pristine shrines "
            "to Aokigahara's haunted forest, the sacred is everywhere."
        ),
        "Mesoamerican Sacred Sites": (
            "The great civilizations of the Americas built pyramids to touch the sky and carved "
            "calendars into stone. The Maya, Aztec, Inca, and Olmec each created worlds where "
            "gods demanded blood, serpents wore feathers, and the sun itself was born from "
            "divine sacrifice."
        ),
        "Biblical & Holy Land": (
            "The Holy Land sits at the crossroads of three Abrahamic faiths. Mountains where "
            "prophets heard God's voice, seas that parted, cities whose walls fell to trumpet "
            "blasts -- these sites have shaped the spiritual geography of billions. From Eden's "
            "traditional location to Armageddon's prophesied battlefield, the landscape is layered "
            "with millennia of sacred meaning."
        ),
        "Chinese Mythology Sites": (
            "China's mythological landscape spans from the Kunlun Mountains -- home of immortals -- "
            "to the Five Great Mountains that anchor the empire. The Monkey King's Flower Fruit "
            "Mountain, the White Snake's West Lake, and Confucius's Qufu are among dozens of "
            "places where myth, history, and living tradition converge."
        ),
        "Cryptid & Monster Sightings": (
            "From the murky depths of Loch Ness to the dense forests of the Pacific Northwest, "
            "reports of unidentified creatures persist worldwide. Lake monsters, forest apes, "
            "winged humanoids, and shape-shifters have been reported for centuries. Whether "
            "folklore, misidentification, or something stranger, these locations draw investigators "
            "and the curious alike."
        ),
    }
    desc = descriptions.get(mode, "Explore legendary and mythological sites across the globe.")
    st.markdown(
        f"""<div style="background:{SURFACE};border-left:3px solid {theme_color};
            padding:12px 16px;border-radius:0 8px 8px 0;margin:8px 0;
            color:{TEXT};font-size:13px;line-height:1.6;">
            {html.escape(desc)}
        </div>""",
        unsafe_allow_html=True,
    )


def _render_deity_frequency_chart(df: pd.DataFrame, mode: str, theme_color: str):
    """Render a horizontal bar chart of most frequently mentioned deities/figures."""
    # Determine which column to use
    col = None
    for candidate in ["Deity / Figure", "Creature", "Tradition"]:
        if candidate in df.columns:
            col = candidate
            break
    if col is None or df.empty:
        return

    counts = df[col].value_counts().head(15)
    if counts.empty:
        return

    fig, ax = plt.subplots(figsize=(10, 4.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(SURFACE)

    bars = ax.barh(counts.index[::-1], counts.values[::-1], color=theme_color, alpha=0.8)
    ax.set_xlabel("Number of Sites", color=TEXT, fontsize=10)
    chart_label = col if col != "Deity / Figure" else "Deities / Figures"
    ax.set_title(f"Top {chart_label} - {mode}", color=TEXT, fontsize=12, pad=10)
    ax.tick_params(colors=TEXT, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")

    for bar in bars:
        width = bar.get_width()
        ax.text(width + 0.15, bar.get_y() + bar.get_height() / 2,
                f"{int(width)}", va="center", color=TEXT, fontsize=8)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_mythology_maps_tab():
    """Render the Mythology & Legends Maps tab."""

    # Tab header
    st.markdown(
        """<div class="tab-header amber">
            <h4>Mythology &amp; Legends Maps</h4>
            <p>Explore mythological sites, sacred places, legendary locations, and cryptid sightings across the globe.
            Ten curated datasets spanning Greek, Norse, Egyptian, Celtic, Hindu, Japanese, Mesoamerican,
            Biblical, Chinese mythology, and Cryptid &amp; Monster lore.</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------------------------
    # Controls
    # -----------------------------------------------------------------------
    ctrl_col1, ctrl_col2 = st.columns([1, 1])

    with ctrl_col1:
        mode = st.selectbox(
            "Select Mythology / Legend Category",
            options=[
                "Greek Mythology Sites",
                "Norse Mythology Locations",
                "Egyptian Sacred Sites",
                "Celtic & Arthurian Legends",
                "Hindu Epic Geography",
                "Japanese Mythology",
                "Mesoamerican Sacred Sites",
                "Biblical & Holy Land",
                "Chinese Mythology Sites",
                "Cryptid & Monster Sightings",
            ],
            index=0,
            key="myth_mode_select",
        )

    data = _get_data_for_mode(mode)
    df = _build_dataframe(data, mode)

    # Type filter
    if "Type" in df.columns:
        all_types = sorted(df["Type"].unique().tolist())
    else:
        all_types = []

    with ctrl_col2:
        selected_types = st.multiselect(
            "Filter by Site Type",
            options=all_types,
            default=all_types,
            key="myth_type_filter",
        )

    # Apply filter to dataframe
    if selected_types and "Type" in df.columns:
        df_filtered = df[df["Type"].isin(selected_types)]
    else:
        df_filtered = df

    theme = MODE_THEMES.get(mode, {"color": ACCENT})
    theme_color = theme["color"]

    # -----------------------------------------------------------------------
    # Legend description panel
    # -----------------------------------------------------------------------
    _render_legend_panel(mode, theme_color)

    # -----------------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------------
    st.markdown("---")
    _render_stats(df_filtered, mode, theme_color)

    # -----------------------------------------------------------------------
    # Map
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.subheader(f"{mode} Map")

    m = _create_folium_map(data, mode, selected_types)
    map_html = m._repr_html_()
    components.html(map_html, height=550)

    # -----------------------------------------------------------------------
    # Charts (two-column layout)
    # -----------------------------------------------------------------------
    st.markdown("---")
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        with st.expander("Site Type Distribution", expanded=True):
            _render_type_chart(df_filtered, mode, theme_color)
    with chart_col2:
        with st.expander("Top Figures / Entities", expanded=True):
            _render_deity_frequency_chart(df_filtered, mode, theme_color)

    # -----------------------------------------------------------------------
    # Geographic scatter plot
    # -----------------------------------------------------------------------
    st.markdown("---")
    with st.expander("Geographic Scatter Plot", expanded=False):
        _render_geographic_scatter(df_filtered, mode, theme_color)

    # -----------------------------------------------------------------------
    # Search panel
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Search Sites")
    _render_search_panel(df_filtered, mode)

    # -----------------------------------------------------------------------
    # Site detail viewer
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Site Detail Viewer")
    if not df_filtered.empty and "Name" in df_filtered.columns:
        site_names = df_filtered["Name"].tolist()
        selected_site_name = st.selectbox(
            "Select a site to view details",
            options=site_names,
            index=0,
            key="myth_site_detail_select",
        )
        # Find the matching raw dict from data for full field access
        selected_raw = None
        for s in data:
            if s.get("name") == selected_site_name:
                selected_raw = s
                break
        if selected_raw:
            _render_site_detail_card(selected_raw, mode, theme_color)
    else:
        st.info("No sites available for the current filter selection.")

    # -----------------------------------------------------------------------
    # Data table
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.subheader(f"{mode} Data Table ({len(df_filtered)} sites)")
    st.dataframe(df_filtered, width="stretch", hide_index=True)

    # -----------------------------------------------------------------------
    # Download
    # -----------------------------------------------------------------------
    st.markdown("---")
    _render_csv_download(df_filtered, mode)

    # -----------------------------------------------------------------------
    # About / Footer
    # -----------------------------------------------------------------------
    st.markdown("---")
    with st.expander("About this module"):
        st.markdown(
            f"""
            **Mythology & Legends Maps** provides curated geospatial data for ten mythological
            and legendary traditions around the world.

            **Current mode:** {mode}
            **Total sites in this dataset:** {len(data)}

            All coordinates are approximate and correspond to real-world locations associated
            with each myth, legend, or sighting. Data is hardcoded from scholarly and popular
            sources and does not require any external API.

            **Available categories:**
            1. **Greek Mythology Sites** - ~{len(GREEK_SITES)} sites across Greece, the Mediterranean, and beyond
            2. **Norse Mythology Locations** - ~{len(NORSE_SITES)} sites across Scandinavia, Iceland, and the Viking world
            3. **Egyptian Sacred Sites** - ~{len(EGYPTIAN_SITES)} sites along the Nile and beyond
            4. **Celtic & Arthurian Legends** - ~{len(CELTIC_SITES)} sites across Britain, Ireland, and France
            5. **Hindu Epic Geography** - ~{len(HINDU_SITES)} sites from the Ramayana, Mahabharata, and Puranas
            6. **Japanese Mythology** - ~{len(JAPANESE_SITES)} shrines, temples, and sacred mountains
            7. **Mesoamerican Sacred Sites** - ~{len(MESOAMERICAN_SITES)} sites from Maya, Aztec, Inca, and other cultures
            8. **Biblical & Holy Land** - ~{len(BIBLICAL_SITES)} sites from Judaism, Christianity, and Islam
            9. **Chinese Mythology Sites** - ~{len(CHINESE_SITES)} mountains, temples, and legendary places
            10. **Cryptid & Monster Sightings** - ~{len(CRYPTID_SITES)} locations of reported creature encounters

            *Part of the TerraScout AI geospatial platform.*
            """,
            unsafe_allow_html=True,
        )
