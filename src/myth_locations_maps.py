# -*- coding: utf-8 -*-
"""
Myth & Legend Locations Explorer module for TerraScout AI.
Presents 10 curated map modes showcasing real-world locations tied to
myths, legends, and folklore traditions from around the globe.
All data is embedded (no external API required for the curated sites).
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

# ═══════════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════════
BG_DARK = "#0a0e1a"
SURFACE = "#111827"
TEXT_PRIMARY = "#e8ecf4"
TEXT_SECONDARY = "#8b97b0"
TEXT_MUTED = "#5a6580"
ACCENT_CYAN = "#06b6d4"
BORDER = "#2a3550"

# ═══════════════════════════════════════════════════════════════════════
# MAP MODE DEFINITIONS  (10 modes, each with curated site data)
# ═══════════════════════════════════════════════════════════════════════

MAP_MODES = {
    "Olympus & Greek Sacred Sites": {
        "description": (
            "Explore the legendary landscapes of ancient Greece -- from the "
            "throne of the gods atop Mount Olympus to the Oracle at Delphi, "
            "the birthplace of Apollo on Delos, the epic walls of Troy, and "
            "the labyrinth of the Minotaur beneath Knossos."
        ),
        "icon": "Greek",
        "color": "#06b6d4",
        "center": [38.5, 24.0],
        "zoom": 6,
        "sites": [
            {"name": "Mount Olympus", "lat": 40.0859, "lon": 22.3583,
             "myth": "Home of the twelve Olympian gods ruled by Zeus",
             "era": "Bronze Age", "type": "Sacred Mountain",
             "notes": "Highest peak in Greece at 2,917 m; pilgrims left offerings at the summit."},
            {"name": "Delphi", "lat": 38.4824, "lon": 22.5010,
             "myth": "Seat of the Pythia, the Oracle of Apollo",
             "era": "8th c. BCE onward", "type": "Oracle / Temple",
             "notes": "Considered the navel (omphalos) of the world by the ancient Greeks."},
            {"name": "Delos", "lat": 37.3964, "lon": 25.2687,
             "myth": "Birthplace of Apollo and Artemis",
             "era": "3rd millennium BCE", "type": "Sacred Island",
             "notes": "Tiny Cycladic island; once the holiest sanctuary in the Aegean."},
            {"name": "Troy (Hisarlik)", "lat": 39.9575, "lon": 26.2389,
             "myth": "Site of the Trojan War described in Homer's Iliad",
             "era": "c. 3000-500 BCE", "type": "Legendary City",
             "notes": "Excavated by Schliemann in the 1870s; nine settlement layers."},
            {"name": "Knossos", "lat": 35.2980, "lon": 25.1631,
             "myth": "Palace of King Minos and the Labyrinth of the Minotaur",
             "era": "c. 2000-1400 BCE", "type": "Minoan Palace",
             "notes": "Largest Bronze Age archaeological site on Crete."},
            {"name": "Olympia", "lat": 37.6388, "lon": 21.6301,
             "myth": "Site of the original Olympic Games held in honor of Zeus",
             "era": "776 BCE onward", "type": "Sanctuary / Games",
             "notes": "Temple of Zeus once housed one of the Seven Wonders of the Ancient World."},
            {"name": "Eleusis", "lat": 38.0418, "lon": 23.5364,
             "myth": "Center of the Eleusinian Mysteries honoring Demeter and Persephone",
             "era": "c. 1500 BCE onward", "type": "Mystery Cult Site",
             "notes": "Annual initiation rites that were among the most secret in antiquity."},
            {"name": "Mycenae", "lat": 37.7306, "lon": 22.7563,
             "myth": "Kingdom of Agamemnon; Lion Gate and Treasury of Atreus",
             "era": "c. 1600-1100 BCE", "type": "Citadel",
             "notes": "Schliemann found the golden 'Mask of Agamemnon' here in 1876."},
            {"name": "Epidaurus", "lat": 37.5963, "lon": 23.0792,
             "myth": "Sanctuary of Asklepios, god of medicine and healing",
             "era": "6th c. BCE onward", "type": "Healing Sanctuary",
             "notes": "Famous for its acoustically perfect ancient theater (14,000 seats)."},
            {"name": "Cape Sounion", "lat": 37.6503, "lon": 24.0246,
             "myth": "Temple of Poseidon where Aegeus watched for Theseus's return",
             "era": "5th c. BCE", "type": "Temple Promontory",
             "notes": "Aegeus leapt to his death here, giving the Aegean Sea its name."},
            {"name": "Dodona", "lat": 39.5463, "lon": 20.7867,
             "myth": "Oldest Hellenic oracle; sacred oak of Zeus",
             "era": "2nd millennium BCE", "type": "Oracle",
             "notes": "Priests interpreted the rustling of oak leaves as the voice of Zeus."},
            {"name": "Mount Ida (Crete)", "lat": 35.2278, "lon": 24.7700,
             "myth": "Cave where the infant Zeus was hidden from Kronos",
             "era": "Mythological", "type": "Sacred Cave / Mountain",
             "notes": "The Idaean Cave on the summit was a major cult site."},
        ],
    },

    "Norse Mythology Sites": {
        "description": (
            "Journey through the Viking world and Norse cosmology -- the great "
            "temple at Uppsala, Jelling's rune stones, the Althing at "
            "Thingvellir, and other sacred sites linked to Odin, Thor, and "
            "the World Tree Yggdrasil."
        ),
        "icon": "Norse",
        "color": "#8b5cf6",
        "center": [60.0, 14.0],
        "zoom": 5,
        "sites": [
            {"name": "Old Uppsala", "lat": 59.8979, "lon": 17.6336,
             "myth": "Great pagan temple and royal burial mounds dedicated to Odin, Thor, and Freyr",
             "era": "3rd-11th c. CE", "type": "Temple / Royal Burial",
             "notes": "Adam of Bremen described lavish sacrifices held here every nine years."},
            {"name": "Jelling", "lat": 55.7565, "lon": 9.4193,
             "myth": "Royal seat of the Viking kings; rune stones mark Denmark's conversion",
             "era": "10th c. CE", "type": "Royal Monument",
             "notes": "UNESCO World Heritage; the 'birth certificate of Denmark.'"},
            {"name": "Thingvellir", "lat": 64.2559, "lon": -21.1300,
             "myth": "Site of the Althing, the oldest parliament, in a rift valley between tectonic plates",
             "era": "930 CE onward", "type": "Assembly / Sacred Landscape",
             "notes": "Where Icelandic chieftains convened; also tied to Norse cosmological symbolism."},
            {"name": "Gamla Uppsala Mounds", "lat": 59.8982, "lon": 17.6308,
             "myth": "Burial mounds of legendary Swedish kings Aun, Egil, and Adils",
             "era": "5th-6th c. CE", "type": "Royal Burial Mounds",
             "notes": "Three large mounds dominate the landscape; linked to the Ynglinga saga."},
            {"name": "Lindholm Hoje", "lat": 57.0780, "lon": 9.9268,
             "myth": "Viking and Iron Age cemetery with ship-shaped stone settings",
             "era": "5th-11th c. CE", "type": "Burial Ground",
             "notes": "Nearly 700 graves; ship outlines represent vessels for the afterlife voyage."},
            {"name": "Borg (Lofoten)", "lat": 68.2510, "lon": 14.3704,
             "myth": "Largest known Viking longhouse; seat of a powerful chieftain",
             "era": "6th-9th c. CE", "type": "Chieftain's Hall",
             "notes": "83 m long; gold-foil figures suggest ritual use and Odin-worship."},
            {"name": "Roskilde", "lat": 55.6426, "lon": 12.0803,
             "myth": "Harbor where five Viking warships were scuttled as a blockade",
             "era": "11th c. CE", "type": "Ship Burial / Harbor",
             "notes": "Ships raised in 1962 now displayed in the Viking Ship Museum."},
            {"name": "Birka", "lat": 59.3360, "lon": 17.5466,
             "myth": "First major Viking trading town; missionary Ansgar preached here",
             "era": "8th-10th c. CE", "type": "Trading Settlement",
             "notes": "UNESCO site on Bjorko island; rich warrior burials."},
            {"name": "Oseberg (Vestfold)", "lat": 59.3063, "lon": 10.2273,
             "myth": "Elaborately carved ship burial of a high-status woman",
             "era": "834 CE", "type": "Ship Burial",
             "notes": "Oseberg ship is the best-preserved Viking vessel ever found."},
            {"name": "Trelleborg (Sealand)", "lat": 55.3989, "lon": 11.2634,
             "myth": "Perfectly geometric ring fortress built by Harald Bluetooth",
             "era": "c. 980 CE", "type": "Ring Fortress",
             "notes": "Military precision; one of several Trelleborg-type forts in Denmark."},
            {"name": "Gosforth Cross", "lat": 54.4212, "lon": -3.4282,
             "myth": "Stone cross depicting Ragnarok scenes alongside Christian imagery",
             "era": "10th c. CE", "type": "Monument / Cross",
             "notes": "Rare merging of Norse apocalypse myth with Christian theology."},
            {"name": "Brattahlid (Qassiarsuk)", "lat": 61.1550, "lon": -45.5170,
             "myth": "Erik the Red's settlement in Greenland, gateway to Vinland",
             "era": "985 CE", "type": "Norse Settlement",
             "notes": "Ruins of Erik's farm and the first Christian church in the New World."},
        ],
    },

    "Egyptian Sacred Places": {
        "description": (
            "Discover the monumental landscapes of ancient Egypt -- from the "
            "pyramids at Giza and the Valley of the Kings to the temple "
            "complexes of Karnak, Luxor, Abu Simbel, and other sites sacred "
            "to the pharaohs and the gods of the Nile."
        ),
        "icon": "Egyptian",
        "color": "#f59e0b",
        "center": [26.0, 32.0],
        "zoom": 6,
        "sites": [
            {"name": "Great Pyramids of Giza", "lat": 29.9792, "lon": 31.1342,
             "myth": "Tombs of pharaohs Khufu, Khafre, and Menkaure; linked to stellar alignments",
             "era": "c. 2580-2510 BCE", "type": "Royal Tomb / Pyramid",
             "notes": "Last surviving Wonder of the Ancient World; Great Pyramid is 146 m tall."},
            {"name": "Valley of the Kings", "lat": 25.7402, "lon": 32.6014,
             "myth": "Royal necropolis where pharaohs were buried with spells from the Book of the Dead",
             "era": "16th-11th c. BCE", "type": "Royal Necropolis",
             "notes": "63 tombs discovered, including Tutankhamun's intact burial (1922)."},
            {"name": "Karnak Temple Complex", "lat": 25.7188, "lon": 32.6573,
             "myth": "Largest religious complex ever built; principal seat of Amun-Ra",
             "era": "c. 2055 BCE - 100 CE", "type": "Temple Complex",
             "notes": "Hypostyle Hall has 134 massive columns; 2,000 years of construction."},
            {"name": "Abu Simbel", "lat": 22.3360, "lon": 31.6256,
             "myth": "Colossal rock-cut temple of Ramesses II aligned so sunlight illuminates inner sanctuary",
             "era": "13th c. BCE", "type": "Rock-Cut Temple",
             "notes": "Relocated in 1968 to save it from Lake Nasser; UNESCO feat of engineering."},
            {"name": "Luxor Temple", "lat": 25.6995, "lon": 32.6392,
             "myth": "Dedicated to the rejuvenation of kingship; connected to Karnak by sphinx avenue",
             "era": "c. 1400 BCE", "type": "Temple",
             "notes": "Avenue of Sphinxes (2.7 km) recently restored and reopened."},
            {"name": "Temple of Hatshepsut (Deir el-Bahari)", "lat": 25.7381, "lon": 32.6069,
             "myth": "Mortuary temple of the female pharaoh who claimed divine birth from Amun",
             "era": "15th c. BCE", "type": "Mortuary Temple",
             "notes": "Terraced into the cliffs; one of Egypt's most elegant monuments."},
            {"name": "Dendera Temple Complex", "lat": 26.1416, "lon": 32.6700,
             "myth": "Temple of Hathor, goddess of love and music; contains famous zodiac ceiling",
             "era": "c. 2250 BCE onward", "type": "Temple",
             "notes": "Zodiac ceiling (now in the Louvre) shows ancient astronomical knowledge."},
            {"name": "Edfu Temple (Temple of Horus)", "lat": 24.9779, "lon": 32.8734,
             "myth": "Best-preserved Egyptian temple; dedicated to Horus, the falcon god",
             "era": "237-57 BCE", "type": "Temple",
             "notes": "Walls record the mythical battle between Horus and Set."},
            {"name": "Philae Temple (Agilkia Island)", "lat": 24.0243, "lon": 32.8842,
             "myth": "Temple of Isis; last outpost of ancient Egyptian religion",
             "era": "c. 690 BCE - 550 CE", "type": "Temple",
             "notes": "Pagan worship continued here until Justinian closed it in 550 CE."},
            {"name": "Saqqara (Step Pyramid)", "lat": 29.8713, "lon": 31.2165,
             "myth": "First pyramid ever built; designed by Imhotep, later deified as god of medicine",
             "era": "c. 2670 BCE", "type": "Pyramid / Necropolis",
             "notes": "Imhotep's Step Pyramid is the oldest monumental stone structure on Earth."},
            {"name": "Abydos", "lat": 26.1853, "lon": 31.9190,
             "myth": "Cult center of Osiris; pharaohs built cenotaphs to be near the god of the afterlife",
             "era": "c. 3100 BCE onward", "type": "Sacred City / Temple",
             "notes": "Seti I's temple contains the famous Abydos King List."},
            {"name": "Amarna (Akhetaten)", "lat": 27.6454, "lon": 30.8975,
             "myth": "Capital built by Akhenaten for the sole worship of the sun-disk Aten",
             "era": "c. 1346-1332 BCE", "type": "Capital City",
             "notes": "Abandoned after Akhenaten's death; revolutionary monotheistic experiment."},
        ],
    },

    "Celtic Sacred Landscapes": {
        "description": (
            "Walk the enchanted terrains of the Celtic world -- Glastonbury "
            "Tor (legendary Avalon), the Hill of Tara in Ireland, the passage "
            "tomb of Newgrange aligned to the winter solstice, Stonehenge, "
            "and other sites steeped in Druidic and Arthurian lore."
        ),
        "icon": "Celtic",
        "color": "#10b981",
        "center": [52.5, -4.0],
        "zoom": 6,
        "sites": [
            {"name": "Glastonbury Tor", "lat": 51.1442, "lon": -2.6985,
             "myth": "Identified with Avalon, the isle where King Arthur was taken after his last battle",
             "era": "Neolithic onward", "type": "Sacred Hill / Tor",
             "notes": "Tower of St Michael on top; terraces may be a ritual labyrinth."},
            {"name": "Stonehenge", "lat": 51.1789, "lon": -1.8262,
             "myth": "Legendary stone circle attributed to Merlin's magic by Geoffrey of Monmouth",
             "era": "c. 3000-2000 BCE", "type": "Stone Circle / Henge",
             "notes": "Aligned to midsummer sunrise and midwinter sunset."},
            {"name": "Hill of Tara", "lat": 53.5793, "lon": -6.6117,
             "myth": "Seat of the High Kings of Ireland; Stone of Destiny (Lia Fail) cried out for true kings",
             "era": "c. 3400 BCE onward", "type": "Royal Hill / Inauguration Site",
             "notes": "Contains passage tombs, ring forts, and the Mound of the Hostages."},
            {"name": "Newgrange", "lat": 53.6947, "lon": -6.4755,
             "myth": "Passage tomb where sunlight enters the chamber at winter solstice; linked to the Tuatha De Danann",
             "era": "c. 3200 BCE", "type": "Passage Tomb",
             "notes": "Older than the Great Pyramid; UNESCO World Heritage site."},
            {"name": "Avebury", "lat": 51.4288, "lon": -1.8544,
             "myth": "Largest stone circle in Europe; part of a vast ritual landscape",
             "era": "c. 2850 BCE", "type": "Stone Circle / Henge",
             "notes": "Village sits inside the circle; connected to West Kennet Long Barrow."},
            {"name": "Callanish Stones", "lat": 58.1976, "lon": -6.7458,
             "myth": "Stone circle on Lewis associated with Celtic sky-god worship and lunar alignments",
             "era": "c. 2900-2600 BCE", "type": "Stone Circle",
             "notes": "Cross-shaped avenue of stones; remote and atmospheric."},
            {"name": "Bryn Celli Ddu", "lat": 53.2072, "lon": -4.2361,
             "myth": "Passage tomb on Anglesey aligned to summer solstice; Druid island tradition",
             "era": "c. 3000 BCE", "type": "Passage Tomb",
             "notes": "Built over a destroyed henge; carved 'Pattern Stone' found inside."},
            {"name": "Ring of Brodgar", "lat": 59.0016, "lon": -3.2298,
             "myth": "Neolithic stone circle in Orkney; part of Heart of Neolithic Orkney UNESCO site",
             "era": "c. 2500-2000 BCE", "type": "Stone Circle",
             "notes": "Originally 60 stones; 27 survive; surrounded by a rock-cut ditch."},
            {"name": "Loughcrew (Sliabh na Caillighe)", "lat": 53.7433, "lon": -7.1165,
             "myth": "Hilltop cairns said to be created when a giant hag dropped stones from her apron",
             "era": "c. 3500-3300 BCE", "type": "Passage Tomb Complex",
             "notes": "Equinox sunrise illuminates the carvings inside Cairn T."},
            {"name": "Emain Macha (Navan Fort)", "lat": 54.3488, "lon": -6.6968,
             "myth": "Capital of the Ulaid in the Ulster Cycle; seat of King Conchobar mac Nessa",
             "era": "c. 95 BCE ritual structure", "type": "Royal Enclosure",
             "notes": "Massive timber structure was deliberately burned in a ritual act."},
            {"name": "The Giants Causeway", "lat": 55.2408, "lon": -6.5116,
             "myth": "40,000 basalt columns said to be built by the giant Finn McCool to fight a Scottish rival",
             "era": "c. 60 million years old", "type": "Natural / Mythic Landmark",
             "notes": "UNESCO World Heritage; columns formed by cooling lava."},
            {"name": "Dun Aonghasa (Inis Mor)", "lat": 53.1255, "lon": -9.7669,
             "myth": "Cliffside stone fort named after Aonghus of the Fir Bolg, legendary pre-Celtic people",
             "era": "c. 1100 BCE", "type": "Stone Fort",
             "notes": "Perched on 100 m cliffs; chevaux-de-frise stone defenses."},
        ],
    },

    "Japanese Shinto Sacred Sites": {
        "description": (
            "Discover the sacred geography of Shinto Japan -- the Grand Shrine "
            "at Ise, the vermillion torii gates of Fushimi Inari, the ancient "
            "Kumano pilgrimage, and sacred mountains revered as dwelling "
            "places of the kami (divine spirits)."
        ),
        "icon": "Shinto",
        "color": "#ef4444",
        "center": [35.5, 136.0],
        "zoom": 6,
        "sites": [
            {"name": "Ise Grand Shrine (Ise Jingu)", "lat": 34.4551, "lon": 136.7256,
             "myth": "Most sacred Shinto shrine; enshrines Amaterasu, the sun goddess",
             "era": "c. 4 BCE (traditional)", "type": "Grand Shrine",
             "notes": "Rebuilt every 20 years in ritual renewal (shikinen sengu); last rebuilt 2013."},
            {"name": "Fushimi Inari Taisha", "lat": 34.9671, "lon": 135.7727,
             "myth": "Head shrine of Inari, kami of rice, commerce, and foxes (kitsune)",
             "era": "711 CE", "type": "Shrine",
             "notes": "Famous for thousands of vermillion torii gates winding up Mount Inari."},
            {"name": "Kumano Nachi Taisha", "lat": 33.6713, "lon": 135.8900,
             "myth": "One of the three Kumano shrines on the ancient pilgrimage route (Kumano Kodo)",
             "era": "4th c. CE", "type": "Shrine / Pilgrimage",
             "notes": "Adjacent to Nachi Falls (133 m), itself worshipped as a kami."},
            {"name": "Mount Fuji", "lat": 35.3606, "lon": 138.7274,
             "myth": "Sacred mountain; dwelling of the goddess Konohanasakuya-hime",
             "era": "Prehistoric worship", "type": "Sacred Mountain",
             "notes": "UNESCO World Heritage; 3,776 m; iconic symbol of Japan."},
            {"name": "Mount Koya (Koyasan)", "lat": 34.2130, "lon": 135.5834,
             "myth": "Founded by Kobo Daishi (Kukai); believed to still be in eternal meditation",
             "era": "816 CE", "type": "Sacred Mountain / Monastery",
             "notes": "Over 100 temples; Okunoin cemetery with 200,000+ graves."},
            {"name": "Izumo Taisha", "lat": 35.4017, "lon": 132.6855,
             "myth": "One of the oldest shrines; dedicated to Okuninushi, god of nation-building and marriage",
             "era": "Legendary / ancient", "type": "Grand Shrine",
             "notes": "In October (Kannazuki) all kami gather here; giant shimenawa rope."},
            {"name": "Itsukushima Shrine (Miyajima)", "lat": 34.2960, "lon": 132.3198,
             "myth": "Floating torii gate; island so sacred that births and deaths were forbidden on it",
             "era": "593 CE", "type": "Shrine / Sacred Island",
             "notes": "UNESCO site; torii appears to float at high tide."},
            {"name": "Mount Haguro (Dewa Sanzan)", "lat": 38.7018, "lon": 139.9811,
             "myth": "One of three sacred mountains of Dewa; center of Shugendo mountain asceticism",
             "era": "593 CE (traditional)", "type": "Sacred Mountain",
             "notes": "2,446 stone steps through ancient cedar forest to summit shrine."},
            {"name": "Kasuga Taisha (Nara)", "lat": 34.6810, "lon": 135.8498,
             "myth": "Shrine where the deity arrived riding a white deer; sacred deer roam freely",
             "era": "768 CE", "type": "Shrine",
             "notes": "3,000 stone and bronze lanterns; primeval forest behind."},
            {"name": "Meiji Jingu (Tokyo)", "lat": 35.6764, "lon": 139.6993,
             "myth": "Shrine dedicated to the deified spirits of Emperor Meiji and Empress Shoken",
             "era": "1920 CE", "type": "Shrine",
             "notes": "100,000-tree forest planted in the heart of Tokyo."},
            {"name": "Okinoshima", "lat": 34.2430, "lon": 130.1040,
             "myth": "Forbidden island where the goddess Tagori-hime dwells; women traditionally barred",
             "era": "4th-9th c. CE", "type": "Sacred Island",
             "notes": "UNESCO site; 80,000 ritual artifacts found; visitors must ritually purify."},
            {"name": "Nachi Falls", "lat": 33.6704, "lon": 135.8873,
             "myth": "Japan's tallest waterfall (133 m); worshipped as a kami in its own right",
             "era": "Prehistoric worship", "type": "Sacred Waterfall",
             "notes": "The waterfall itself is the object of worship, not merely a scenic backdrop."},
        ],
    },

    "Arthurian Legend Locations": {
        "description": (
            "Trace the geography of King Arthur -- Tintagel Castle on the "
            "Cornish cliffs, Glastonbury's claimed grave, Camelot candidates "
            "from Cadbury to Winchester, the lakes tied to Excalibur, and "
            "other sites woven into the Matter of Britain."
        ),
        "icon": "Arthurian",
        "color": "#8b5cf6",
        "center": [51.5, -3.0],
        "zoom": 7,
        "sites": [
            {"name": "Tintagel Castle", "lat": 50.6685, "lon": -4.7588,
             "myth": "Geoffrey of Monmouth's birthplace of King Arthur; castle on dramatic headland",
             "era": "13th c. CE (castle); earlier settlement", "type": "Castle / Legendary Birthplace",
             "notes": "New footbridge (2019) reconnects headland; Dark Age pottery found."},
            {"name": "Glastonbury Abbey", "lat": 51.1468, "lon": -2.7144,
             "myth": "Monks claimed to discover Arthur and Guinevere's graves here in 1191",
             "era": "7th c. CE onward", "type": "Abbey / Legendary Burial",
             "notes": "Also linked to Joseph of Arimathea and the Holy Grail."},
            {"name": "Cadbury Castle (South Cadbury)", "lat": 51.0224, "lon": -2.5306,
             "myth": "Leading candidate for Camelot; Iron Age hillfort refortified in Arthurian era",
             "era": "c. 500 CE refortification", "type": "Hillfort / Camelot Candidate",
             "notes": "John Leland (1542) first identified it as Camelot; excavations found a great hall."},
            {"name": "Winchester Great Hall", "lat": 51.0610, "lon": -1.3206,
             "myth": "Hangs the Winchester Round Table, painted for Edward I as an Arthurian claim",
             "era": "13th c. CE (table)", "type": "Great Hall / Arthurian Symbol",
             "notes": "The Round Table was dendro-dated to c. 1270; repainted for Henry VIII."},
            {"name": "Dozmary Pool", "lat": 50.5336, "lon": -4.5803,
             "myth": "Claimed to be the lake where Sir Bedivere returned Excalibur to the Lady of the Lake",
             "era": "Legendary", "type": "Lake / Excalibur Legend",
             "notes": "Remote moorland pool on Bodmin Moor; other lakes also claim the legend."},
            {"name": "Llyn Llydaw (Snowdonia)", "lat": 53.0690, "lon": -4.0551,
             "myth": "Welsh candidate for the lake of Excalibur and Arthur's final battle",
             "era": "Legendary", "type": "Lake / Arthurian Legend",
             "notes": "Below Snowdon's summit; early Welsh sources place Arthur in Snowdonia."},
            {"name": "Bamburgh Castle", "lat": 55.6089, "lon": -1.7101,
             "myth": "Identified by some scholars as Joyous Garde, Lancelot's castle",
             "era": "Anglo-Saxon onward", "type": "Castle / Arthurian Link",
             "notes": "Seat of the kings of Northumbria; Sir Thomas Malory placed Joyous Garde here."},
            {"name": "Caerleon", "lat": 51.6121, "lon": -2.9521,
             "myth": "Geoffrey of Monmouth placed Arthur's court here; Roman amphitheater as 'Round Table'",
             "era": "Roman (75 CE onward)", "type": "Roman Fortress / Arthurian Court",
             "notes": "Roman amphitheater, baths, and barracks; resonates with Arthurian feasting."},
            {"name": "Slaughterbridge (Camlann)", "lat": 50.6282, "lon": -4.6959,
             "myth": "Traditional site of the Battle of Camlann, Arthur's last battle",
             "era": "Legendary / Dark Age", "type": "Battlefield Site",
             "notes": "Inscribed stone by the River Camel was once wrongly called 'Arthur's Tomb.'"},
            {"name": "Castle Dore", "lat": 50.3706, "lon": -4.6470,
             "myth": "Iron Age fort linked to King Mark of Cornwall in the Tristan and Iseult legend",
             "era": "Iron Age; 6th c. CE", "type": "Hillfort / Tristan Legend",
             "notes": "The Tristan Stone stands nearby with a 6th c. inscription."},
            {"name": "Merlin's Cave (Tintagel)", "lat": 50.6660, "lon": -4.7600,
             "myth": "Sea cave beneath Tintagel Castle associated with Merlin the wizard",
             "era": "Legendary", "type": "Sea Cave / Legend",
             "notes": "Accessible at low tide; eerie atmosphere fuels the Merlin connection."},
            {"name": "Birdoswald Roman Fort (Camboglanna)", "lat": 54.9907, "lon": -2.6008,
             "myth": "Hadrian's Wall fort whose Roman name Camboglanna may derive from Camlann",
             "era": "Roman / Post-Roman", "type": "Roman Fort / Battlefield Candidate",
             "notes": "Some historians place Arthur's last battle here on the Wall."},
        ],
    },

    "Robin Hood & Medieval Legends": {
        "description": (
            "Explore the real landscapes of Robin Hood and other medieval "
            "English outlaw legends -- Sherwood Forest, Nottingham Castle, "
            "the Major Oak, Barnsdale, the churches and abbeys linked to "
            "Friar Tuck, Maid Marian, and the Merry Men."
        ),
        "icon": "Medieval",
        "color": "#10b981",
        "center": [53.2, -1.2],
        "zoom": 8,
        "sites": [
            {"name": "Major Oak (Sherwood Forest)", "lat": 53.2044, "lon": -1.0724,
             "myth": "800-year-old oak said to have sheltered Robin Hood and his Merry Men",
             "era": "Medieval legend", "type": "Legendary Tree",
             "notes": "Trunk circumference 10 m; supported by scaffolding; SSSI protected."},
            {"name": "Nottingham Castle", "lat": 52.9518, "lon": -1.1556,
             "myth": "Stronghold of the Sheriff of Nottingham, Robin Hood's arch-enemy",
             "era": "1067 CE onward", "type": "Castle",
             "notes": "Rebuilt many times; now a museum with Robin Hood exhibition."},
            {"name": "Sherwood Forest (Visitors Centre)", "lat": 53.2037, "lon": -1.0699,
             "myth": "The vast royal forest where Robin Hood lived as an outlaw",
             "era": "Medieval", "type": "Royal Forest",
             "notes": "Once covered 100,000 acres; remnant ancient oaks survive."},
            {"name": "St Mary's Church, Edwinstowe", "lat": 53.1928, "lon": -1.0685,
             "myth": "Traditional site where Robin Hood married Maid Marian",
             "era": "12th c. CE", "type": "Church",
             "notes": "The legend is recorded in later ballad traditions."},
            {"name": "Barnsdale (Robin Hood's Well)", "lat": 53.5859, "lon": -1.2202,
             "myth": "Earliest ballads locate Robin Hood in Barnsdale, not Sherwood",
             "era": "14th c. ballads", "type": "Well / Landmark",
             "notes": "A Gest of Robyn Hode (c. 1450) repeatedly references Barnsdale."},
            {"name": "Kirklees Priory (gatehouse)", "lat": 53.6837, "lon": -1.7549,
             "myth": "Where Robin Hood was bled to death by the treacherous Prioress",
             "era": "c. 1155 CE (priory)", "type": "Priory / Legendary Death Site",
             "notes": "'Robin Hood's Grave' headstone in the grounds; private land."},
            {"name": "Fountains Abbey", "lat": 54.1084, "lon": -1.5838,
             "myth": "Greatest Cistercian ruin; linked to Friar Tuck traditions of roving monks",
             "era": "1132 CE", "type": "Abbey Ruins",
             "notes": "UNESCO World Heritage; largest monastic ruin in England."},
            {"name": "Loxley, Sheffield", "lat": 53.4050, "lon": -1.5510,
             "myth": "Robin Hood sometimes called 'Robin of Loxley'; claimed birthplace",
             "era": "Legendary", "type": "Village / Legendary Origin",
             "notes": "Mentioned in later Robin Hood literature; south Yorkshire location."},
            {"name": "Lincoln Cathedral", "lat": 53.2344, "lon": -0.5353,
             "myth": "Robin Hood and Little John legendarily competed in an archery contest here",
             "era": "1088 CE onward", "type": "Cathedral",
             "notes": "Was the tallest building in the world (1311-1548) at 160 m."},
            {"name": "Papplewick (St James Church)", "lat": 53.0535, "lon": -1.1780,
             "myth": "Church associated with Alan-a-Dale's wedding rescued by Robin Hood",
             "era": "12th c. CE", "type": "Church / Ballad Location",
             "notes": "Norman doorway survives; near Sherwood Forest edge."},
            {"name": "Ye Olde Trip to Jerusalem", "lat": 52.9494, "lon": -1.1555,
             "myth": "Claims to be England's oldest inn (1189 CE); Crusader and outlaw connections",
             "era": "Claimed 1189 CE", "type": "Historic Inn",
             "notes": "Built into caves beneath Nottingham Castle; a Robin Hood tourism staple."},
            {"name": "Creswell Crags", "lat": 53.2624, "lon": -1.1907,
             "myth": "Limestone gorge with caves containing Britain's only Ice Age cave art; local witch-mark legends",
             "era": "c. 13,000 years BP", "type": "Cave / Folklore Site",
             "notes": "Hundreds of apotropaic witch marks found carved in the caves."},
        ],
    },

    "Vampire & Gothic Locations": {
        "description": (
            "Enter the world of vampires and Gothic horror -- Bran Castle "
            "(Dracula's Castle) in Transylvania, Whitby Abbey where Stoker "
            "was inspired, Highgate Cemetery, and other eerie sites woven "
            "into the vampire myth across Europe."
        ),
        "icon": "Gothic",
        "color": "#dc2626",
        "center": [47.0, 20.0],
        "zoom": 5,
        "sites": [
            {"name": "Bran Castle", "lat": 45.5150, "lon": 25.3673,
             "myth": "Marketed as 'Dracula's Castle'; Vlad Tepes may have been imprisoned here",
             "era": "1388 CE", "type": "Castle / Dracula Legend",
             "notes": "Perched on a cliff; Romanian national landmark and top tourist site."},
            {"name": "Poenari Fortress", "lat": 45.3540, "lon": 24.6353,
             "myth": "The real fortress of Vlad the Impaler (Vlad Tepes / Dracula)",
             "era": "13th c. CE, expanded by Vlad", "type": "Fortress / Historical Dracula",
             "notes": "1,480 steps to reach it; Vlad's wife legendarily leapt from the tower."},
            {"name": "Whitby Abbey", "lat": 54.4882, "lon": -0.6076,
             "myth": "Bram Stoker stayed in Whitby in 1890; Dracula arrives in England here as a wolf",
             "era": "657 CE (abbey)", "type": "Abbey / Literary Inspiration",
             "notes": "199 steps up the cliff; the ruined Gothic arches are iconic."},
            {"name": "Sighisoara (Vlad's Birthplace)", "lat": 46.2197, "lon": 24.7919,
             "myth": "Vlad III (Dracula) was born in this medieval citadel in 1431",
             "era": "12th c. CE", "type": "Medieval Citadel / Birthplace",
             "notes": "UNESCO World Heritage; Clock Tower and house of Vlad's birth survive."},
            {"name": "Highgate Cemetery", "lat": 51.5676, "lon": -0.1466,
             "myth": "Victorian cemetery at center of the 1970s 'Highgate Vampire' panic",
             "era": "1839 CE", "type": "Cemetery / Vampire Legend",
             "notes": "Egyptian Avenue and catacombs; Karl Marx also buried here."},
            {"name": "Snagov Monastery", "lat": 44.6856, "lon": 26.1586,
             "myth": "Island monastery where Vlad the Impaler is traditionally said to be buried",
             "era": "14th c. CE", "type": "Monastery / Legendary Tomb",
             "notes": "Excavations found a headless skeleton under the altar; identity debated."},
            {"name": "Borgo Pass", "lat": 47.2520, "lon": 25.0539,
             "myth": "The mountain pass through which Jonathan Harker traveled to Castle Dracula in the novel",
             "era": "Stoker's novel (1897)", "type": "Mountain Pass / Literary Site",
             "notes": "Hotel Castel Dracula built here in 1983 for vampire tourism."},
            {"name": "Curtea de Arges Monastery", "lat": 45.1416, "lon": 24.6816,
             "myth": "Legend of Master Manole who walled his wife alive to complete the monastery",
             "era": "1517 CE", "type": "Monastery / Legend",
             "notes": "One of Romania's most beautiful churches; Manole legend is a masterwork of folklore."},
            {"name": "Corvin Castle (Hunedoara)", "lat": 45.7489, "lon": 22.8874,
             "myth": "Gothic fortress where Vlad Tepes was allegedly held prisoner for 7 years",
             "era": "1446 CE", "type": "Gothic Castle",
             "notes": "One of Europe's largest Gothic castles; dramatic bridge entrance."},
            {"name": "Orava Castle (Slovakia)", "lat": 49.2615, "lon": 19.3603,
             "myth": "Filming location for the classic vampire film Nosferatu (1922)",
             "era": "1267 CE", "type": "Castle / Film Location",
             "notes": "Perched high on a cliff; one of Slovakia's most dramatic castles."},
            {"name": "Slains Castle (Scotland)", "lat": 57.4164, "lon": -1.8329,
             "myth": "Bram Stoker visited and may have drawn inspiration for Castle Dracula from it",
             "era": "16th c. CE (new castle)", "type": "Castle Ruin / Literary Inspiration",
             "notes": "Clifftop ruin overlooking the North Sea; now roofless."},
            {"name": "Pere Lachaise Cemetery (Paris)", "lat": 48.8614, "lon": 2.3934,
             "myth": "Largest cemetery in Paris; vampire folklore, Allan Kardec spiritism",
             "era": "1804 CE", "type": "Cemetery / Gothic Culture",
             "notes": "Jim Morrison, Oscar Wilde, Chopin buried here; a Gothic pilgrimage site."},
        ],
    },

    "Native American Sacred Sites": {
        "description": (
            "Honor the sacred landscapes of Indigenous North America -- the "
            "great mound city of Cahokia, Chaco Canyon's astronomical "
            "alignments, Bear Butte, Devils Tower, and other places of "
            "deep spiritual significance to Native peoples."
        ),
        "icon": "Indigenous",
        "color": "#f97316",
        "center": [40.0, -100.0],
        "zoom": 4,
        "sites": [
            {"name": "Cahokia Mounds", "lat": 38.6556, "lon": -90.0621,
             "myth": "Largest pre-Columbian settlement north of Mexico; Monks Mound is 30 m high",
             "era": "c. 600-1400 CE", "type": "Mound City / Ceremonial Center",
             "notes": "Population may have reached 20,000; Woodhenge solar calendar."},
            {"name": "Chaco Canyon", "lat": 36.0604, "lon": -107.9614,
             "myth": "Ancestral Puebloan great houses aligned to solar and lunar cycles",
             "era": "c. 850-1250 CE", "type": "Ceremonial Complex",
             "notes": "Pueblo Bonito had over 600 rooms; roads radiate across the desert."},
            {"name": "Bear Butte (Mato Paha)", "lat": 44.4753, "lon": -103.4311,
             "myth": "Sacred to the Lakota and Cheyenne; where Sweet Medicine received sacred laws",
             "era": "Thousands of years", "type": "Sacred Mountain",
             "notes": "Prayer cloths tied to trees; still an active vision quest site."},
            {"name": "Devils Tower (Bear Lodge)", "lat": 44.5902, "lon": -104.7146,
             "myth": "Lakota legend tells of girls saved from a giant bear; its claws scored the rock",
             "era": "Geological / ancient spiritual", "type": "Sacred Monolith",
             "notes": "First US National Monument (1906); voluntary June climbing ban honors tribes."},
            {"name": "Mesa Verde", "lat": 37.1838, "lon": -108.4887,
             "myth": "Ancestral Puebloan cliff dwellings; people eventually migrated south per oral traditions",
             "era": "c. 600-1300 CE", "type": "Cliff Dwellings",
             "notes": "Cliff Palace has 150 rooms; UNESCO World Heritage site."},
            {"name": "Serpent Mound", "lat": 39.0253, "lon": -83.4305,
             "myth": "1,348-foot effigy mound in the shape of a serpent swallowing an egg",
             "era": "c. 321 BCE (debated)", "type": "Effigy Mound",
             "notes": "Aligned to summer solstice sunset; built on a crypto-explosion structure."},
            {"name": "Taos Pueblo", "lat": 36.4386, "lon": -105.5447,
             "myth": "Multi-story adobe pueblo continuously inhabited for over 1,000 years",
             "era": "c. 1000-1450 CE", "type": "Living Pueblo",
             "notes": "UNESCO site; Blue Lake returned to the pueblo in 1970 after decades of activism."},
            {"name": "Bighorn Medicine Wheel", "lat": 44.8263, "lon": -107.9220,
             "myth": "Stone circle with 28 spokes aligned to summer solstice sunrise and star risings",
             "era": "c. 1200-1700 CE", "type": "Medicine Wheel / Observatory",
             "notes": "At 9,642 feet elevation; used by many tribes for ceremony and vision quests."},
            {"name": "Poverty Point", "lat": 32.6344, "lon": -91.4087,
             "myth": "Monumental earthwork complex built by hunter-gatherers; enormous C-shaped ridges",
             "era": "c. 1700-1100 BCE", "type": "Earthwork Complex",
             "notes": "UNESCO World Heritage; one of the oldest mound sites in North America."},
            {"name": "Pipestone (Catlinite Quarry)", "lat": 44.0136, "lon": -96.3255,
             "myth": "Sacred red pipestone quarried for ceremonial pipes; neutral ground for all tribes",
             "era": "3,000+ years", "type": "Sacred Quarry",
             "notes": "National Monument; only enrolled Native Americans may quarry the stone."},
            {"name": "Canyon de Chelly", "lat": 36.1311, "lon": -109.4698,
             "myth": "Sacred canyon of the Navajo; Spider Rock is home of Spider Woman who taught weaving",
             "era": "c. 2500 BCE onward", "type": "Canyon / Sacred Landscape",
             "notes": "Spider Rock spire rises 230 m; still home to Navajo families."},
            {"name": "Ocmulgee Mounds", "lat": 32.8375, "lon": -83.6063,
             "myth": "Creek/Muscogee origin place; Earth Lodge contains a 1,000-year-old clay floor",
             "era": "c. 900-1100 CE", "type": "Mound / Ceremonial Center",
             "notes": "Recently expanded as Ocmulgee Mounds National Historical Park."},
        ],
    },

    "Hindu Mythology Sites": {
        "description": (
            "Journey through the sacred geography of Hinduism -- Ayodhya "
            "(birthplace of Lord Rama), Lanka, the battlefield of "
            "Kurukshetra from the Mahabharata, submerged Dwarka, holy "
            "Varanasi on the Ganges, and other tirthas (pilgrimage sites)."
        ),
        "icon": "Hindu",
        "color": "#ec4899",
        "center": [22.0, 78.0],
        "zoom": 5,
        "sites": [
            {"name": "Ayodhya", "lat": 26.7922, "lon": 82.1998,
             "myth": "Birthplace of Lord Rama; setting for much of the Ramayana epic",
             "era": "Ancient / mythological", "type": "Holy City / Epic Setting",
             "notes": "Ram Mandir temple inaugurated January 2024 at the claimed birthplace."},
            {"name": "Kurukshetra", "lat": 29.9695, "lon": 76.8783,
             "myth": "Battlefield of the Mahabharata war; where Krishna delivered the Bhagavad Gita",
             "era": "c. 3100 BCE (traditional)", "type": "Battlefield / Sacred City",
             "notes": "Brahma Sarovar tank; solar eclipse pilgrimage attracts millions."},
            {"name": "Dwarka", "lat": 22.2394, "lon": 68.9678,
             "myth": "Kingdom of Lord Krishna; said to have been submerged by the sea after his death",
             "era": "Ancient / mythological", "type": "Submerged City / Temple",
             "notes": "Dwarkadhish Temple on shore; marine archaeology has found underwater structures."},
            {"name": "Varanasi (Kashi)", "lat": 25.3176, "lon": 83.0068,
             "myth": "City of Lord Shiva; oldest continuously inhabited city; liberation (moksha) from rebirth",
             "era": "c. 11th c. BCE onward", "type": "Holy City",
             "notes": "Ganga Aarti on the ghats; cremation at Manikarnika Ghat since antiquity."},
            {"name": "Rameshwaram", "lat": 9.2885, "lon": 79.3129,
             "myth": "Where Rama built the bridge (Rama Setu / Adam's Bridge) to Lanka",
             "era": "Ancient / mythological", "type": "Temple / Bridge Legend",
             "notes": "Chain of limestone shoals visible from satellite; Ramanathaswamy Temple."},
            {"name": "Lanka (Sigiriya, Sri Lanka)", "lat": 7.9570, "lon": 80.7603,
             "myth": "Candidates for Ravana's Lanka; Sigiriya rock fortress linked to the demon king",
             "era": "5th c. CE (Sigiriya)", "type": "Rock Fortress / Epic Setting",
             "notes": "UNESCO site; frescoes, lion gate, and mirror wall."},
            {"name": "Kedarnath", "lat": 30.7352, "lon": 79.0669,
             "myth": "One of 12 Jyotirlinga shrines; Shiva hid here as a bull and sank into the ground",
             "era": "8th c. CE (temple)", "type": "Himalayan Temple",
             "notes": "At 3,583 m; devastated by 2013 floods but temple survived."},
            {"name": "Tirupati (Tirumala)", "lat": 13.6833, "lon": 79.3474,
             "myth": "Hill shrine of Venkateswara (Vishnu); wealthiest pilgrimage site on Earth",
             "era": "c. 300 CE onward", "type": "Temple / Pilgrimage",
             "notes": "50,000-100,000 pilgrims daily; annual revenue rivals major corporations."},
            {"name": "Haridwar", "lat": 29.9457, "lon": 78.1642,
             "myth": "Gateway to the gods; where the Ganges exits the Himalayas onto the plains",
             "era": "Ancient", "type": "Holy City / Ghat",
             "notes": "Kumbh Mela held here every 12 years; millions bathe at Har Ki Pauri ghat."},
            {"name": "Ujjain (Mahakaleshwar)", "lat": 23.1828, "lon": 75.7682,
             "myth": "One of 12 Jyotirlinga; also where the prime meridian of ancient Indian astronomy ran",
             "era": "Ancient", "type": "Temple / Sacred City",
             "notes": "Bhasma Aarti performed with sacred ash at dawn; Simhastha Kumbh site."},
            {"name": "Hampi (Kishkindha)", "lat": 15.3350, "lon": 76.4600,
             "myth": "Identified with Kishkindha, the monkey kingdom of Sugriva and Hanuman in the Ramayana",
             "era": "1336-1565 CE (Vijayanagara)", "type": "Ruined City / Epic Setting",
             "notes": "UNESCO site; hundreds of temples, the Stone Chariot, and giant boulders."},
            {"name": "Puri (Jagannath Temple)", "lat": 19.8050, "lon": 85.8180,
             "myth": "Lord Jagannath (Krishna) in unfinished wooden form; annual Rath Yatra chariot festival",
             "era": "12th c. CE (temple)", "type": "Temple / Festival",
             "notes": "English word 'juggernaut' derives from the enormous chariot procession."},
        ],
    },
}

# ═══════════════════════════════════════════════════════════════════════
# COLOR PALETTE for map markers by mode
# ═══════════════════════════════════════════════════════════════════════
MODE_MARKER_COLORS = {
    "Olympus & Greek Sacred Sites": "#06b6d4",
    "Norse Mythology Sites": "#8b5cf6",
    "Egyptian Sacred Places": "#f59e0b",
    "Celtic Sacred Landscapes": "#10b981",
    "Japanese Shinto Sacred Sites": "#ef4444",
    "Arthurian Legend Locations": "#8b5cf6",
    "Robin Hood & Medieval Legends": "#10b981",
    "Vampire & Gothic Locations": "#dc2626",
    "Native American Sacred Sites": "#f97316",
    "Hindu Mythology Sites": "#ec4899",
}

# Type-based sub-colors for diverse markers within a mode
TYPE_COLORS = {
    "Sacred Mountain": "#06b6d4",
    "Oracle / Temple": "#f59e0b",
    "Oracle": "#f59e0b",
    "Sacred Island": "#3b82f6",
    "Legendary City": "#ef4444",
    "Minoan Palace": "#ec4899",
    "Sanctuary / Games": "#10b981",
    "Mystery Cult Site": "#8b5cf6",
    "Citadel": "#f97316",
    "Healing Sanctuary": "#14b8a6",
    "Temple Promontory": "#38bdf8",
    "Sacred Cave / Mountain": "#a855f7",
    "Temple / Royal Burial": "#8b5cf6",
    "Royal Monument": "#f59e0b",
    "Assembly / Sacred Landscape": "#06b6d4",
    "Royal Burial Mounds": "#a855f7",
    "Burial Ground": "#64748b",
    "Chieftain's Hall": "#f97316",
    "Ship Burial / Harbor": "#3b82f6",
    "Trading Settlement": "#10b981",
    "Ship Burial": "#3b82f6",
    "Ring Fortress": "#ef4444",
    "Monument / Cross": "#8b97b0",
    "Norse Settlement": "#14b8a6",
    "Royal Tomb / Pyramid": "#f59e0b",
    "Royal Necropolis": "#dc2626",
    "Temple Complex": "#f59e0b",
    "Rock-Cut Temple": "#f97316",
    "Temple": "#f59e0b",
    "Mortuary Temple": "#dc2626",
    "Pyramid / Necropolis": "#a855f7",
    "Sacred City / Temple": "#ec4899",
    "Capital City": "#ef4444",
    "Sacred Hill / Tor": "#10b981",
    "Stone Circle / Henge": "#06b6d4",
    "Royal Hill / Inauguration Site": "#f59e0b",
    "Passage Tomb": "#8b5cf6",
    "Stone Circle": "#06b6d4",
    "Passage Tomb Complex": "#a855f7",
    "Royal Enclosure": "#f97316",
    "Natural / Mythic Landmark": "#10b981",
    "Stone Fort": "#64748b",
    "Grand Shrine": "#ef4444",
    "Shrine": "#dc2626",
    "Shrine / Pilgrimage": "#ec4899",
    "Sacred Mountain / Monastery": "#8b5cf6",
    "Shrine / Sacred Island": "#3b82f6",
    "Sacred Waterfall": "#06b6d4",
    "Castle / Legendary Birthplace": "#8b5cf6",
    "Abbey / Legendary Burial": "#a855f7",
    "Hillfort / Camelot Candidate": "#f59e0b",
    "Great Hall / Arthurian Symbol": "#f97316",
    "Lake / Excalibur Legend": "#3b82f6",
    "Lake / Arthurian Legend": "#3b82f6",
    "Castle / Arthurian Link": "#8b5cf6",
    "Roman Fortress / Arthurian Court": "#f59e0b",
    "Battlefield Site": "#ef4444",
    "Hillfort / Tristan Legend": "#ec4899",
    "Sea Cave / Legend": "#06b6d4",
    "Roman Fort / Battlefield Candidate": "#64748b",
    "Legendary Tree": "#10b981",
    "Castle": "#8b5cf6",
    "Royal Forest": "#10b981",
    "Church": "#f59e0b",
    "Well / Landmark": "#06b6d4",
    "Priory / Legendary Death Site": "#dc2626",
    "Abbey Ruins": "#a855f7",
    "Village / Legendary Origin": "#8b97b0",
    "Cathedral": "#f59e0b",
    "Church / Ballad Location": "#f59e0b",
    "Historic Inn": "#f97316",
    "Cave / Folklore Site": "#64748b",
    "Castle / Dracula Legend": "#dc2626",
    "Fortress / Historical Dracula": "#ef4444",
    "Abbey / Literary Inspiration": "#a855f7",
    "Medieval Citadel / Birthplace": "#f59e0b",
    "Cemetery / Vampire Legend": "#64748b",
    "Monastery / Legendary Tomb": "#8b5cf6",
    "Mountain Pass / Literary Site": "#06b6d4",
    "Monastery / Legend": "#ec4899",
    "Gothic Castle": "#dc2626",
    "Castle / Film Location": "#f97316",
    "Castle Ruin / Literary Inspiration": "#8b97b0",
    "Cemetery / Gothic Culture": "#64748b",
    "Mound City / Ceremonial Center": "#f59e0b",
    "Ceremonial Complex": "#f97316",
    "Sacred Monolith": "#ef4444",
    "Cliff Dwellings": "#a855f7",
    "Effigy Mound": "#10b981",
    "Living Pueblo": "#ec4899",
    "Medicine Wheel / Observatory": "#06b6d4",
    "Earthwork Complex": "#8b5cf6",
    "Sacred Quarry": "#f97316",
    "Canyon / Sacred Landscape": "#dc2626",
    "Mound / Ceremonial Center": "#f59e0b",
    "Holy City / Epic Setting": "#ef4444",
    "Battlefield / Sacred City": "#dc2626",
    "Submerged City / Temple": "#3b82f6",
    "Holy City": "#f59e0b",
    "Temple / Bridge Legend": "#06b6d4",
    "Rock Fortress / Epic Setting": "#f97316",
    "Himalayan Temple": "#8b5cf6",
    "Temple / Pilgrimage": "#ec4899",
    "Holy City / Ghat": "#06b6d4",
    "Temple / Sacred City": "#a855f7",
    "Ruined City / Epic Setting": "#f97316",
    "Temple / Festival": "#ef4444",
}


# ═══════════════════════════════════════════════════════════════════════
# HELPER: build dataframe from site list
# ═══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def _build_dataframe(mode_name: str) -> pd.DataFrame:
    """Build a pandas DataFrame for the selected map mode's curated sites."""
    mode = MAP_MODES[mode_name]
    rows = []
    for s in mode["sites"]:
        rows.append({
            "Name": s["name"],
            "Latitude": s["lat"],
            "Longitude": s["lon"],
            "Type": s["type"],
            "Era": s["era"],
            "Myth / Legend": s["myth"],
            "Notes": s["notes"],
        })
    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════
# HELPER: build folium map
# ═══════════════════════════════════════════════════════════════════════
def _build_map(mode_name: str) -> folium.Map:
    """Create a Folium map for the given mode with all curated sites."""
    mode = MAP_MODES[mode_name]
    m = folium.Map(
        location=mode["center"],
        zoom_start=mode["zoom"],
        tiles="CartoDB dark_matter",
    )

    for s in mode["sites"]:
        color = TYPE_COLORS.get(s["type"], mode["color"])

        popup_html = (
            '<div style="max-width:260px; font-family:sans-serif;">'
            '<strong style="font-size:0.95rem;">{name}</strong><br/>'
            '<span style="color:#888; font-size:0.8rem;">{type} &middot; {era}</span><br/>'
            '<span style="font-size:0.82rem;">{myth}</span><br/>'
            '<span style="color:#aaa; font-size:0.75rem;">{notes}</span>'
            '</div>'
        ).format(
            name=escape(s["name"]),
            type=escape(s["type"]),
            era=escape(s["era"]),
            myth=escape(s["myth"]),
            notes=escape(s["notes"]),
        )

        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=2,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=escape(s["name"]),
        ).add_to(m)

    return m


# ═══════════════════════════════════════════════════════════════════════
# HELPER: build matplotlib chart of site types
# ═══════════════════════════════════════════════════════════════════════
def _build_type_chart(df: pd.DataFrame, mode_color: str):
    """Create a horizontal bar chart of site types."""
    type_counts = df["Type"].value_counts()
    fig, ax = plt.subplots(figsize=(6, max(3, len(type_counts) * 0.4)))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)

    colors = [TYPE_COLORS.get(t, mode_color) for t in type_counts.index]
    ax.barh(range(len(type_counts)), type_counts.values, color=colors, alpha=0.85)
    ax.set_yticks(range(len(type_counts)))
    ax.set_yticklabels(
        [t[:35] for t in type_counts.index],
        color=TEXT_SECONDARY, fontsize=9,
    )
    ax.set_xlabel("Count", color=TEXT_SECONDARY, fontsize=10)
    ax.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=9)
    ax.grid(True, axis="x", color=BORDER, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.invert_yaxis()
    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════
# HELPER: compute stats for a mode
# ═══════════════════════════════════════════════════════════════════════
def _compute_stats(df: pd.DataFrame) -> dict:
    """Compute summary statistics for the dashboard metrics row."""
    total_sites = len(df)
    unique_types = df["Type"].nunique()
    lat_range = df["Latitude"].max() - df["Latitude"].min()
    lon_range = df["Longitude"].max() - df["Longitude"].min()
    avg_lat = df["Latitude"].mean()
    avg_lon = df["Longitude"].mean()
    return {
        "total_sites": total_sites,
        "unique_types": unique_types,
        "lat_range": f"{lat_range:.2f}",
        "lon_range": f"{lon_range:.2f}",
        "centroid": f"{avg_lat:.2f}, {avg_lon:.2f}",
    }


# ═══════════════════════════════════════════════════════════════════════
# HELPER: render a single mode panel
# ═══════════════════════════════════════════════════════════════════════
def _render_mode(mode_name: str):
    """Render description, stats, map, chart, table, and download for one mode."""
    mode = MAP_MODES[mode_name]

    # ── Description ──────────────────────────────────────────────────
    st.markdown(
        f'<div style="background:{SURFACE}; border:1px solid {BORDER}; '
        f'border-radius:8px; padding:1rem; margin-bottom:1rem;">'
        f'<span style="color:{mode["color"]}; font-weight:700; font-size:1rem;">'
        f'{mode["icon"]} Mythology</span>'
        f'<p style="color:{TEXT_SECONDARY}; margin:0.4rem 0 0 0; font-size:0.9rem;">'
        f'{escape(mode["description"])}</p></div>',
        unsafe_allow_html=True,
    )

    # ── Build data ───────────────────────────────────────────────────
    df = _build_dataframe(mode_name)
    stats = _compute_stats(df)

    # ── Stats row ────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Sites", stats["total_sites"])
    c2.metric("Site Types", stats["unique_types"])
    c3.metric("Lat Range", f"{stats['lat_range']}deg")
    c4.metric("Lon Range", f"{stats['lon_range']}deg")
    c5.metric("Centroid", stats["centroid"])

    # ── Folium Map ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Interactive Map")

    legend_html = " ".join(
        f'<span style="color:{TYPE_COLORS.get(t, mode["color"])}; '
        f'font-size:0.8rem;">&#9679; {escape(t)}</span>'
        for t in df["Type"].unique()
    )
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'{legend_html}</div>',
        unsafe_allow_html=True,
    )

    m = _build_map(mode_name)
    components.html(m._repr_html_(), height=500)

    # ── Chart & Notable Sites ────────────────────────────────────────
    st.markdown("---")
    col_sites, col_chart = st.columns([1, 1])

    with col_sites:
        st.markdown("#### Notable Sites")
        for _, row in df.iterrows():
            color = TYPE_COLORS.get(row["Type"], mode["color"])
            st.markdown(
                f'<div style="display:flex; align-items:center; margin-bottom:0.5rem;">'
                f'<div style="width:10px; height:54px; border-radius:5px; background:{color};'
                f' margin-right:0.75rem; flex-shrink:0;"></div>'
                f'<div>'
                f'<div style="color:{TEXT_PRIMARY}; font-weight:600; font-size:0.85rem;">'
                f'{escape(str(row["Name"]))}</div>'
                f'<div style="color:{TEXT_SECONDARY}; font-size:0.75rem;">'
                f'{escape(str(row["Type"]))} &middot; {escape(str(row["Era"]))}</div>'
                f'<div style="color:{TEXT_MUTED}; font-size:0.7rem;">'
                f'{row["Latitude"]:.4f}, {row["Longitude"]:.4f}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    with col_chart:
        st.markdown("#### Site Type Breakdown")
        fig = _build_type_chart(df, mode["color"])
        st.pyplot(fig)
        plt.close(fig)

    # ── Data Table ───────────────────────────────────────────────────
    st.markdown("---")
    with st.expander(f"Full Data Table ({len(df)} sites)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── CSV Download ─────────────────────────────────────────────────
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    safe_filename = mode_name.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        f"Download {len(df)} {mode_name} Sites (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"myth_{safe_filename}.csv",
        mime="text/csv",
        key=f"myth_dl_{safe_filename}",
    )


# ═══════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════
def render_myth_locations_maps_tab():
    """Main entry point -- renders the Myth & Legend Locations Explorer tab."""

    # ── Tab Header ───────────────────────────────────────────────────
    st.markdown(
        '<div class="tab-header violet">'
        '<h4>Myth & Legend Locations Explorer</h4>'
        '<p>Explore real-world sites tied to myths, legends, and folklore '
        'traditions from ten civilizations across the globe. Each map mode '
        'presents curated locations with coordinates, historical context, '
        'and the stories that made them legendary.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Mode Selector ────────────────────────────────────────────────
    st.markdown("#### Select a Map Mode")

    mode_labels = list(MAP_MODES.keys())
    selected_mode = st.selectbox(
        "Mythology / Legend Tradition",
        mode_labels,
        index=0,
        key="mythloc_mode_select",
        help="Choose a mythological tradition to explore its associated real-world sites.",
    )

    # ── Quick Overview Across All Modes ──────────────────────────────
    with st.expander("All 10 Map Modes at a Glance", expanded=False):
        overview_rows = []
        for name, mode in MAP_MODES.items():
            overview_rows.append({
                "Mode": name,
                "Sites": len(mode["sites"]),
                "Region Center": f"{mode['center'][0]:.1f}, {mode['center'][1]:.1f}",
                "Description": mode["description"][:90] + "...",
            })
        overview_df = pd.DataFrame(overview_rows)
        st.dataframe(overview_df, use_container_width=True, hide_index=True)

        # Summary stats
        total_all = sum(len(m["sites"]) for m in MAP_MODES.values())
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Total Map Modes", len(MAP_MODES))
        sc2.metric("Total Curated Sites", total_all)
        sc3.metric("Avg Sites / Mode", f"{total_all / len(MAP_MODES):.1f}")

    # ── Render Selected Mode ─────────────────────────────────────────
    st.markdown("---")
    _render_mode(selected_mode)

    # ── Global Mega-Map (all modes combined) ─────────────────────────
    st.markdown("---")
    st.markdown("#### Global Myth & Legend Map (All Modes)")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY}; font-size:0.85rem;">'
        "All curated sites from every mythology tradition plotted together. "
        "Marker colors correspond to their tradition.</p>",
        unsafe_allow_html=True,
    )

    global_map = folium.Map(
        location=[25.0, 30.0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )

    all_rows = []
    for mname, mode in MAP_MODES.items():
        color = MODE_MARKER_COLORS.get(mname, "#8b97b0")
        for s in mode["sites"]:
            popup_html = (
                '<div style="max-width:240px; font-family:sans-serif;">'
                '<strong>{name}</strong><br/>'
                '<span style="color:#888; font-size:0.78rem;">{mode}</span><br/>'
                '<span style="font-size:0.8rem;">{myth}</span>'
                '</div>'
            ).format(
                name=escape(s["name"]),
                mode=escape(mname),
                myth=escape(s["myth"]),
            )

            folium.CircleMarker(
                location=[s["lat"], s["lon"]],
                radius=6,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=1.5,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=escape(s["name"]),
            ).add_to(global_map)

            all_rows.append({
                "Tradition": mname,
                "Name": s["name"],
                "Latitude": s["lat"],
                "Longitude": s["lon"],
                "Type": s["type"],
                "Era": s["era"],
                "Myth / Legend": s["myth"],
            })

    # Legend for global map
    global_legend = " ".join(
        f'<span style="color:{c}; font-size:0.8rem;">&#9679; {escape(n)}</span>'
        for n, c in MODE_MARKER_COLORS.items()
    )
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'{global_legend}</div>',
        unsafe_allow_html=True,
    )

    components.html(global_map._repr_html_(), height=500)

    # ── Global data table & download ─────────────────────────────────
    all_df = pd.DataFrame(all_rows)

    with st.expander(f"Combined Data Table ({len(all_df)} sites across all traditions)", expanded=False):
        st.dataframe(all_df, use_container_width=True, hide_index=True)

    csv_all = io.StringIO()
    all_df.to_csv(csv_all, index=False)
    st.download_button(
        f"Download All {len(all_df)} Myth Sites (CSV)",
        data=csv_all.getvalue(),
        file_name="myth_all_sites_combined.csv",
        mime="text/csv",
        key="myth_dl_all_combined",
    )

    # ── Traditions Comparison Chart ──────────────────────────────────
    st.markdown("---")
    st.markdown("#### Traditions Comparison")

    trad_counts = {n: len(m["sites"]) for n, m in MAP_MODES.items()}
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BG_DARK)
    ax.set_facecolor(SURFACE)

    names = list(trad_counts.keys())
    counts = list(trad_counts.values())
    colors = [MODE_MARKER_COLORS.get(n, "#8b97b0") for n in names]

    ax.barh(range(len(names)), counts, color=colors, alpha=0.85)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(
        [n[:30] for n in names],
        color=TEXT_SECONDARY, fontsize=9,
    )
    ax.set_xlabel("Number of Curated Sites", color=TEXT_SECONDARY, fontsize=10)
    ax.set_title(
        "Sites per Mythology Tradition",
        color=TEXT_PRIMARY, fontsize=12, pad=10,
    )
    ax.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=9)
    ax.grid(True, axis="x", color=BORDER, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color(BORDER)
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── Geographic Spread Analysis ───────────────────────────────────
    st.markdown("---")
    st.markdown("#### Geographic Spread Analysis")
    st.markdown(
        f'<p style="color:{TEXT_SECONDARY}; font-size:0.85rem;">'
        "Latitude and longitude distributions of curated sites across all "
        "mythology traditions, illustrating the global reach of legendary "
        "landscapes.</p>",
        unsafe_allow_html=True,
    )

    spread_col1, spread_col2 = st.columns(2)

    with spread_col1:
        # Latitude distribution scatter
        fig_lat, ax_lat = plt.subplots(figsize=(6, 4))
        fig_lat.patch.set_facecolor(BG_DARK)
        ax_lat.set_facecolor(SURFACE)

        for mname, mode in MAP_MODES.items():
            lats = [s["lat"] for s in mode["sites"]]
            color = MODE_MARKER_COLORS.get(mname, "#8b97b0")
            ax_lat.scatter(
                [mname[:12]] * len(lats), lats,
                color=color, alpha=0.8, s=40, edgecolors="white",
                linewidths=0.3, zorder=3,
            )

        ax_lat.set_ylabel("Latitude", color=TEXT_SECONDARY, fontsize=10)
        ax_lat.set_title("Latitude by Tradition", color=TEXT_PRIMARY, fontsize=11, pad=8)
        ax_lat.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=7, rotation=45)
        ax_lat.tick_params(axis="y", colors=TEXT_SECONDARY, labelsize=9)
        ax_lat.grid(True, axis="y", color=BORDER, linewidth=0.5, alpha=0.5)
        ax_lat.set_axisbelow(True)
        for spine in ax_lat.spines.values():
            spine.set_color(BORDER)
        fig_lat.tight_layout()
        st.pyplot(fig_lat)
        plt.close(fig_lat)

    with spread_col2:
        # Longitude distribution scatter
        fig_lon, ax_lon = plt.subplots(figsize=(6, 4))
        fig_lon.patch.set_facecolor(BG_DARK)
        ax_lon.set_facecolor(SURFACE)

        for mname, mode in MAP_MODES.items():
            lons = [s["lon"] for s in mode["sites"]]
            color = MODE_MARKER_COLORS.get(mname, "#8b97b0")
            ax_lon.scatter(
                [mname[:12]] * len(lons), lons,
                color=color, alpha=0.8, s=40, edgecolors="white",
                linewidths=0.3, zorder=3,
            )

        ax_lon.set_ylabel("Longitude", color=TEXT_SECONDARY, fontsize=10)
        ax_lon.set_title("Longitude by Tradition", color=TEXT_PRIMARY, fontsize=11, pad=8)
        ax_lon.tick_params(axis="x", colors=TEXT_SECONDARY, labelsize=7, rotation=45)
        ax_lon.tick_params(axis="y", colors=TEXT_SECONDARY, labelsize=9)
        ax_lon.grid(True, axis="y", color=BORDER, linewidth=0.5, alpha=0.5)
        ax_lon.set_axisbelow(True)
        for spine in ax_lon.spines.values():
            spine.set_color(BORDER)
        fig_lon.tight_layout()
        st.pyplot(fig_lon)
        plt.close(fig_lon)
