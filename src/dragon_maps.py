# -*- coding: utf-8 -*-
"""
Dragons & Mythical Beasts Explorer module for TerraScout AI.
Curated geospatial datasets of dragon legends, mythical creature sightings,
folklore traditions, and beast lore worldwide. Ten interactive map modes
covering European dragons, Asian dragons, sea monsters, unicorns, phoenixes,
werewolves, thunderbirds, yokai, Celtic/Norse beasts, and dragon museums.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import html as html_module
from streamlit.components.v1 import html as st_html

# ============================================================
# CATEGORY COLORS & ICONS
# ============================================================
CATEGORY_COLORS = {
    "European Dragon Legends": "#dc2626",
    "Chinese & Asian Dragons": "#f59e0b",
    "Sea Monster Sightings": "#06b6d4",
    "Unicorn & Griffin Lore": "#a855f7",
    "Phoenix & Firebird Myths": "#f97316",
    "Werewolf & Vampire Legends": "#7c3aed",
    "Thunderbird & Native Spirits": "#10b981",
    "Japanese Yokai & Demons": "#ec4899",
    "Celtic & Norse Beasts": "#3b82f6",
    "Dragon Museums & Festivals": "#eab308",
}

MARKER_ICONS = {
    "European Dragon Legends": "fire",
    "Chinese & Asian Dragons": "star",
    "Sea Monster Sightings": "anchor",
    "Unicorn & Griffin Lore": "certificate",
    "Phoenix & Firebird Myths": "fire",
    "Werewolf & Vampire Legends": "moon-o",
    "Thunderbird & Native Spirits": "bolt",
    "Japanese Yokai & Demons": "warning-sign",
    "Celtic & Norse Beasts": "tower",
    "Dragon Museums & Festivals": "flag",
}


# ============================================================
# DATASETS
# ============================================================

def _european_dragons():
    return pd.DataFrame([
        {"name": "Dragon of Wawel Hill", "lat": 50.0540, "lon": 19.9352, "location": "Krakow, Poland", "country": "Poland", "era": "Medieval", "description": "Smok Wawelski, the legendary dragon slain by Krakus. A fire-breathing statue stands at Wawel Castle.", "type": "Fire-breather", "status": "Cultural icon"},
        {"name": "Dragon of Brno", "lat": 49.1951, "lon": 16.6068, "location": "Brno, Czech Republic", "country": "Czech Republic", "era": "Medieval", "description": "A crocodile hanging in the Old Town Hall gateway, believed to be a dragon since the 1600s.", "type": "Lindworm", "status": "Museum artifact"},
        {"name": "Dragon of Ljubljana", "lat": 46.0514, "lon": 14.5060, "location": "Ljubljana, Slovenia", "country": "Slovenia", "era": "Ancient/Roman", "description": "Jason and the Argonauts allegedly slew a dragon here. The Dragon Bridge features four dragon statues.", "type": "Classical dragon", "status": "City symbol"},
        {"name": "Fafnir's Lair", "lat": 50.7374, "lon": 7.0982, "location": "Rhine Valley, Germany", "country": "Germany", "era": "Norse/Medieval", "description": "Fafnir the dwarf turned dragon, slain by Sigurd/Siegfried. The Nibelungenlied locates events along the Rhine.", "type": "Treasure-hoarder", "status": "Epic legend"},
        {"name": "Dragon of Silene", "lat": 36.8300, "lon": 12.4300, "location": "Silene, Libya (legend)", "country": "Libya", "era": "Medieval", "description": "St. George slew the dragon to save a princess. The most widespread European dragon-slayer legend.", "type": "Man-eater", "status": "Religious legend"},
        {"name": "Lambton Worm", "lat": 54.8400, "lon": -1.4700, "location": "County Durham, England", "country": "United Kingdom", "era": "Medieval", "description": "A giant worm pulled from the River Wear that grew into a monstrous dragon terrorizing the countryside.", "type": "Lindworm", "status": "Folklore"},
        {"name": "Dragon of Loschy Hill", "lat": 54.1100, "lon": -1.5200, "location": "North Yorkshire, England", "country": "United Kingdom", "era": "Medieval", "description": "Peter Loschy slew a venomous dragon by wearing armor studded with razor blades.", "type": "Venomous dragon", "status": "Folklore"},
        {"name": "Wyvern of Mordiford", "lat": 52.0700, "lon": -2.5800, "location": "Mordiford, Herefordshire", "country": "United Kingdom", "era": "Medieval", "description": "A wyvern raised from a baby by a girl, grew to terrorize the village until slain by a condemned criminal.", "type": "Wyvern", "status": "Folklore"},
        {"name": "Dragon of Bignor Hill", "lat": 50.8900, "lon": -0.6200, "location": "West Sussex, England", "country": "United Kingdom", "era": "Pre-medieval", "description": "A knucker dragon dwelling in a bottomless pool near Lyminster, slain by a wandering knight.", "type": "Knucker", "status": "Folklore"},
        {"name": "Tatzelwurm", "lat": 47.2692, "lon": 11.3933, "location": "Austrian/Swiss Alps", "country": "Austria", "era": "18th century+", "description": "A stubby-legged reptilian cryptid reported in the Alps. Described as a fat serpent with cat-like face.", "type": "Alpine cryptid", "status": "Cryptid legend"},
        {"name": "Lindworm of Klagenfurt", "lat": 46.6247, "lon": 14.3053, "location": "Klagenfurt, Austria", "country": "Austria", "era": "1335", "description": "A lindworm skull was found in 1335, inspiring the city's dragon fountain. Likely a woolly rhino skull.", "type": "Lindworm", "status": "City symbol"},
        {"name": "Cuelebre of Asturias", "lat": 43.3614, "lon": -5.8593, "location": "Asturias, Spain", "country": "Spain", "era": "Pre-Roman", "description": "A giant winged serpent guarding caves and treasures in Asturian mythology, warded off by bread offerings.", "type": "Winged serpent", "status": "Folklore"},
        {"name": "Coca Dragon", "lat": 40.9429, "lon": -8.5379, "location": "Mondsao, Portugal", "country": "Portugal", "era": "Medieval", "description": "The Coca is a female dragon fought during Corpus Christi festivals. St. George defeats it in annual pageants.", "type": "Festival dragon", "status": "Living tradition"},
        {"name": "Zilant of Kazan", "lat": 55.7963, "lon": 49.1082, "location": "Kazan, Russia", "country": "Russia", "era": "Medieval", "description": "A winged serpent on the coat of arms of Kazan. Legends say it terrorized the region before the city's founding.", "type": "Winged serpent", "status": "City symbol"},
        {"name": "Bolla / Kulshedra", "lat": 41.3275, "lon": 19.8187, "location": "Albania", "country": "Albania", "era": "Ancient", "description": "Albanian dragon that starts as Bolla (blind serpent) and transforms into Kulshedra, a multi-headed fire-breather.", "type": "Shapeshifter", "status": "Folklore"},
        {"name": "Smei Gorynych", "lat": 55.7558, "lon": 37.6173, "location": "Moscow region, Russia", "country": "Russia", "era": "Medieval", "description": "Three-headed dragon of Russian byliny epics. Slain by the bogatyr Dobrynya Nikitich.", "type": "Multi-headed", "status": "Epic legend"},
        {"name": "Wyvern of Bisternon", "lat": 50.7500, "lon": -1.8200, "location": "Bisterne, Hampshire", "country": "United Kingdom", "era": "Medieval", "description": "A fearsome wyvern that preyed on livestock and locals near the New Forest.", "type": "Wyvern", "status": "Folklore"},
        {"name": "Dragon of Monte Pilatus", "lat": 46.9790, "lon": 8.2566, "location": "Mount Pilatus, Switzerland", "country": "Switzerland", "era": "1649", "description": "Multiple dragon sightings recorded by Swiss naturalists. A flying dragon allegedly seen by Christoph Schorer.", "type": "Flying dragon", "status": "Historical account"},
        {"name": "Tarasque", "lat": 43.8069, "lon": 4.6589, "location": "Tarascon, France", "country": "France", "era": "1st century AD", "description": "A turtle-dragon hybrid tamed by St. Martha. The city of Tarascon is named after it. UNESCO-listed festival.", "type": "Hybrid beast", "status": "Festival tradition"},
        {"name": "Vouivre of Franche-Comte", "lat": 47.2400, "lon": 6.0200, "location": "Franche-Comte, France", "country": "France", "era": "Medieval", "description": "A female wyvern bearing a glowing carbuncle gem on her forehead, who bathed in rivers at night.", "type": "Wyvern", "status": "Folklore"},
        {"name": "Dragon of Gévaudan", "lat": 44.6500, "lon": 3.4500, "location": "Gevaudan, France", "country": "France", "era": "Pre-medieval", "description": "Before the famous Beast, the Gevaudan region had ancient dragon legends tied to volcanic landscapes.", "type": "Volcanic dragon", "status": "Folklore"},
        {"name": "Nidhogg's Root", "lat": 63.8258, "lon": -18.0353, "location": "Iceland (mythic)", "country": "Iceland", "era": "Norse", "description": "Nidhogg gnaws at the roots of Yggdrasil, the World Tree. Iceland's volcanic landscape inspired the myth.", "type": "World-serpent", "status": "Norse mythology"},
        {"name": "Hydra of Lerna", "lat": 37.5833, "lon": 22.7167, "location": "Lerna, Peloponnese, Greece", "country": "Greece", "era": "Ancient", "description": "Multi-headed water serpent slain by Heracles as his Second Labor. Cut one head, two grow back.", "type": "Multi-headed", "status": "Classical myth"},
        {"name": "Python of Delphi", "lat": 38.4824, "lon": 22.5010, "location": "Delphi, Greece", "country": "Greece", "era": "Ancient", "description": "A monstrous serpent-dragon guarding the Oracle, slain by Apollo who claimed the sanctuary.", "type": "Earth dragon", "status": "Classical myth"},
        {"name": "Jormungandr Origin", "lat": 64.1466, "lon": -21.9426, "location": "Reykjavik, Iceland (mythic)", "country": "Iceland", "era": "Norse", "description": "The Midgard Serpent encircling the world, child of Loki. Will fight Thor at Ragnarok.", "type": "World-serpent", "status": "Norse mythology"},
        {"name": "Dragon of Wantley", "lat": 53.4000, "lon": -1.6000, "location": "South Yorkshire, England", "country": "United Kingdom", "era": "16th century", "description": "A satirical dragon legend. More of Moor Hall slew it by kicking it. A humorous burlesque of chivalric tales.", "type": "Satirical", "status": "Folklore"},
        {"name": "Aitvaras", "lat": 54.6872, "lon": 25.2797, "location": "Lithuania", "country": "Lithuania", "era": "Pre-Christian", "description": "A household spirit appearing as a rooster indoors and a fiery dragon outdoors, bringing stolen wealth.", "type": "Fire spirit", "status": "Folklore"},
        {"name": "Zmeu", "lat": 44.4268, "lon": 26.1025, "location": "Romania", "country": "Romania", "era": "Medieval", "description": "A humanoid dragon of Romanian mythology that kidnaps maidens and hoards treasure. Slain by Fat-Frumos.", "type": "Humanoid dragon", "status": "Folklore"},
        {"name": "Wawel Dragon Statue", "lat": 50.0537, "lon": 19.9351, "location": "Wawel Castle, Krakow", "country": "Poland", "era": "Modern (1972)", "description": "The famous fire-breathing bronze dragon statue at the foot of Wawel Hill, breathes real fire every few minutes.", "type": "Monument", "status": "Tourist attraction"},
        {"name": "Dragon of Ragnar Lothbrok", "lat": 55.6761, "lon": 12.5683, "location": "Scandinavia (mythic)", "country": "Denmark", "era": "Viking Age", "description": "Ragnar wore hairy breeches to fight a giant serpent-dragon and win the hand of Thora.", "type": "Saga dragon", "status": "Viking saga"},
    ])


def _asian_dragons():
    return pd.DataFrame([
        {"name": "Dragon Wall, Forbidden City", "lat": 39.9163, "lon": 116.3972, "location": "Beijing, China", "country": "China", "era": "Ming Dynasty", "description": "The Nine-Dragon Wall (Jiulongbi) with nine glazed-tile dragons. Imperial dragons had five claws.", "type": "Lung (Imperial)", "status": "UNESCO site"},
        {"name": "Dragon Boat Festival Origin", "lat": 30.5728, "lon": 104.0668, "location": "Zigui County, Hubei", "country": "China", "era": "278 BC", "description": "Dragon boats honor poet Qu Yuan. Dragon worship merged with river festival traditions.", "type": "Water dragon", "status": "Living tradition"},
        {"name": "Dragon Gate, Yellow River", "lat": 35.5500, "lon": 110.3500, "location": "Longmen, Shaanxi/Shanxi", "country": "China", "era": "Ancient", "description": "Carp that leap the Dragon Gate become dragons. Origin of the proverb about perseverance and transformation.", "type": "Transformation myth", "status": "Folklore"},
        {"name": "Dragon King Temple, Datong", "lat": 40.0900, "lon": 113.2900, "location": "Datong, Shanxi", "country": "China", "era": "Song Dynasty", "description": "Temple to the Dragon King who controls rain. One of the oldest dragon deity temples in northern China.", "type": "Dragon King", "status": "Temple"},
        {"name": "Azure Dragon of the East", "lat": 34.2658, "lon": 108.9541, "location": "Xi'an, China (mythic)", "country": "China", "era": "Ancient", "description": "Qinglong, one of the Four Symbols of Chinese constellations, guardian of the East and spring.", "type": "Celestial dragon", "status": "Cosmological"},
        {"name": "Naga King Temple", "lat": 13.7563, "lon": 100.5018, "location": "Bangkok, Thailand", "country": "Thailand", "era": "Ancient", "description": "Naga serpent-dragons guard Buddhist temples across Thailand. Part dragon, part cobra deity.", "type": "Naga", "status": "Religious icon"},
        {"name": "Naga of the Mekong", "lat": 17.8725, "lon": 102.7413, "location": "Nong Khai, Thailand", "country": "Thailand", "era": "Ancient", "description": "Fireballs rise from the Mekong each October, attributed to the Naga. The Naga Fireball Festival celebrates this.", "type": "Naga", "status": "Living tradition"},
        {"name": "Yong (Korean Dragon)", "lat": 37.5665, "lon": 126.9780, "location": "Seoul, South Korea", "country": "South Korea", "era": "Three Kingdoms", "description": "Korean dragons (Yong) carry yeouiju orbs and are benevolent water deities associated with agriculture.", "type": "Yong", "status": "Cultural icon"},
        {"name": "Dragon Palace of Ryugu", "lat": 31.5969, "lon": 130.6571, "location": "Kagoshima, Japan", "country": "Japan", "era": "Ancient", "description": "Ryujin the dragon god lives in an underwater palace. Urashima Taro visited it in the famous folktale.", "type": "Ryujin", "status": "Folklore"},
        {"name": "Druk, Thunder Dragon", "lat": 27.4728, "lon": 89.6393, "location": "Thimphu, Bhutan", "country": "Bhutan", "era": "Ancient", "description": "Bhutan is the Land of the Thunder Dragon (Druk Yul). The Druk appears on the national flag.", "type": "Thunder dragon", "status": "National symbol"},
        {"name": "Bakunawa, Moon-Eater", "lat": 10.3157, "lon": 123.8854, "location": "Cebu, Philippines", "country": "Philippines", "era": "Pre-colonial", "description": "A giant sea serpent-dragon that causes eclipses by swallowing the moon. Villagers bang pots to scare it away.", "type": "Sea dragon", "status": "Folklore"},
        {"name": "Antaboga, World Serpent", "lat": -7.7956, "lon": 110.3695, "location": "Java, Indonesia", "country": "Indonesia", "era": "Hindu-Javanese", "description": "The primordial dragon of Javanese cosmology, meditating in the underworld, creating the world turtle and serpent.", "type": "Primordial dragon", "status": "Mythology"},
        {"name": "Long Ma, Dragon Horse", "lat": 34.7472, "lon": 113.6249, "location": "Yellow River, Henan", "country": "China", "era": "Ancient", "description": "A dragon-horse hybrid that emerged from the Yellow River carrying the He Tu diagram to Emperor Fu Xi.", "type": "Dragon-horse", "status": "Mythology"},
        {"name": "Makara Gate, Angkor", "lat": 13.4125, "lon": 103.8670, "location": "Angkor Wat, Cambodia", "country": "Cambodia", "era": "12th century", "description": "Makara dragon-crocodile hybrids guard temple entrances at Angkor. Sea-dragon motifs throughout Khmer art.", "type": "Makara", "status": "Temple art"},
        {"name": "Hai Riyo, Winged Dragon", "lat": 35.6762, "lon": 139.6503, "location": "Tokyo, Japan", "country": "Japan", "era": "Chinese influence", "description": "A dragon with bird wings, imported from Chinese mythology. Appears in Japanese temple art and tattoos.", "type": "Winged dragon", "status": "Art motif"},
        {"name": "Vietnamese Dragon, Hanoi", "lat": 21.0278, "lon": 105.8342, "location": "Hanoi, Vietnam", "country": "Vietnam", "era": "1010 AD", "description": "Emperor Ly Thai To saw a dragon ascending when founding Hanoi (Thang Long = Rising Dragon).", "type": "Rong (Vietnamese)", "status": "City origin myth"},
        {"name": "Ha Long Bay Dragons", "lat": 20.9101, "lon": 107.1839, "location": "Ha Long Bay, Vietnam", "country": "Vietnam", "era": "Ancient", "description": "Ha Long means Descending Dragon. A mother dragon and her children created the limestone pillars to repel invaders.", "type": "Rong", "status": "UNESCO site"},
        {"name": "Dragon Temple, Wat Samphran", "lat": 13.7400, "lon": 100.2600, "location": "Nakhon Pathom, Thailand", "country": "Thailand", "era": "Modern", "description": "A 17-story pink cylindrical temple wrapped by a giant green dragon sculpture. A surreal religious site.", "type": "Temple dragon", "status": "Temple"},
        {"name": "Dragon Pearl Legend", "lat": 23.1291, "lon": 113.2644, "location": "Guangzhou, China", "country": "China", "era": "Ancient", "description": "The Pearl River delta legends say dragons fought over a luminous pearl, creating the river systems.", "type": "Pearl dragon", "status": "Regional folklore"},
        {"name": "Naga of Angkor Thom", "lat": 13.4411, "lon": 103.8568, "location": "Angkor Thom, Cambodia", "country": "Cambodia", "era": "12th century", "description": "Giant naga balustrades line the causeway to Angkor Thom, depicting the Churning of the Ocean of Milk.", "type": "Naga", "status": "UNESCO site"},
        {"name": "Dragon Kiln, Jingdezhen", "lat": 29.2688, "lon": 117.1784, "location": "Jingdezhen, China", "country": "China", "era": "Song Dynasty", "description": "Dragon kilns (long yao) shaped like climbing dragons on hillsides, producing imperial porcelain.", "type": "Kiln tradition", "status": "Heritage site"},
        {"name": "Shenlong, Spirit Dragon", "lat": 36.0611, "lon": 103.8343, "location": "Lanzhou, Gansu", "country": "China", "era": "Ancient", "description": "Shenlong controls wind and rain. Blue-scaled dragon that farmers pray to for good harvests.", "type": "Shenlong", "status": "Agricultural deity"},
        {"name": "Tianlong, Celestial Dragon", "lat": 39.9042, "lon": 116.4074, "location": "Beijing, China", "country": "China", "era": "Ancient", "description": "Heavenly dragons that guard the palaces of the gods and pull divine chariots across the sky.", "type": "Tianlong", "status": "Mythology"},
        {"name": "Imugi, Proto-Dragon", "lat": 35.1796, "lon": 129.0756, "location": "Busan, South Korea", "country": "South Korea", "era": "Ancient", "description": "A giant serpent that must survive 1000 years to become a true dragon. Lives in water or caves.", "type": "Imugi", "status": "Folklore"},
        {"name": "Lao Dragon Boat Racing", "lat": 17.9757, "lon": 102.6331, "location": "Vientiane, Laos", "country": "Laos", "era": "Ancient", "description": "Naga dragon boat races on the Mekong during Boun Suang Heua festival, honoring river nagas.", "type": "Naga", "status": "Festival"},
    ])


def _sea_monsters():
    return pd.DataFrame([
        {"name": "Kraken Origin Waters", "lat": 63.0000, "lon": 5.0000, "location": "Norwegian Sea", "country": "Norway", "era": "1180 AD", "description": "First described in the Orvar-Odds saga. A creature so large it was mistaken for islands. Likely inspired by giant squid.", "type": "Kraken", "status": "Norse legend"},
        {"name": "Leviathan, Mediterranean", "lat": 33.0000, "lon": 35.0000, "location": "Eastern Mediterranean", "country": "Israel/Lebanon", "era": "Biblical", "description": "The great sea monster of Hebrew scripture, a chaos dragon representing primordial ocean forces.", "type": "Leviathan", "status": "Religious text"},
        {"name": "Scylla and Charybdis", "lat": 38.2400, "lon": 15.6300, "location": "Strait of Messina, Italy", "country": "Italy", "era": "Ancient Greek", "description": "Homer's Odyssey describes a six-headed sea monster (Scylla) and a whirlpool monster (Charybdis) flanking the strait.", "type": "Sea monster pair", "status": "Classical myth"},
        {"name": "HMS Daedalus Sighting", "lat": -24.5000, "lon": -9.0000, "location": "South Atlantic Ocean", "country": "International Waters", "era": "1848", "description": "Captain Peter M'Quhae and crew reported a 60-foot sea serpent for 20 minutes. Published in The Times.", "type": "Sea serpent", "status": "Naval report"},
        {"name": "Gloucester Sea Serpent", "lat": 42.6159, "lon": -70.6600, "location": "Cape Ann, Massachusetts", "country": "USA", "era": "1817", "description": "Hundreds of witnesses saw a 70-100 foot serpent over several weeks. A Linnaean Society investigation followed.", "type": "Sea serpent", "status": "Historical"},
        {"name": "Cadborosaurus Pacific", "lat": 48.5000, "lon": -124.0000, "location": "Strait of Juan de Fuca", "country": "USA/Canada", "era": "1930s+", "description": "Horse-headed sea serpent reported along the Pacific Northwest coast. A carcass was allegedly found in 1937.", "type": "Cadborosaurus", "status": "Cryptid"},
        {"name": "Morgawr of Falmouth", "lat": 50.1500, "lon": -5.0700, "location": "Falmouth Bay, Cornwall", "country": "United Kingdom", "era": "1975", "description": "A long-necked sea creature photographed off the Cornish coast. Multiple witnesses over decades.", "type": "Sea serpent", "status": "Cryptid"},
        {"name": "Trunko Beach Encounter", "lat": -30.8700, "lon": 30.3900, "location": "Margate, South Africa", "country": "South Africa", "era": "1924", "description": "A white-furred marine creature fought two whales before washing ashore. Dubbed Trunko for its trunk-like appendage.", "type": "Unknown marine", "status": "Historical"},
        {"name": "Lusca of the Blue Holes", "lat": 24.2500, "lon": -76.0000, "location": "Andros Island, Bahamas", "country": "Bahamas", "era": "Folklore", "description": "A giant octopus-shark hybrid lurking in the blue holes of Andros. Blamed for swimmers vanishing in tidal surges.", "type": "Lusca", "status": "Folklore"},
        {"name": "Cetus, Sea of Joppa", "lat": 32.0500, "lon": 34.7500, "location": "Jaffa (Joppa), Israel", "country": "Israel", "era": "Ancient Greek", "description": "The sea monster sent by Poseidon, from which Perseus rescued Andromeda. Chains allegedly visible on rocks.", "type": "Cetus", "status": "Classical myth"},
        {"name": "Aspidochelone", "lat": 35.0000, "lon": 25.0000, "location": "Mediterranean Sea", "country": "Greece", "era": "Medieval", "description": "A colossal sea turtle or whale mistaken for an island. Sailors would land on it and it would dive, drowning them.", "type": "Island-beast", "status": "Bestiary"},
        {"name": "Jormungandr, World Ocean", "lat": 66.0000, "lon": -18.0000, "location": "North Atlantic (mythic)", "country": "Iceland", "era": "Norse", "description": "The Midgard Serpent encircling the entire world ocean, so large it bites its own tail.", "type": "World serpent", "status": "Norse mythology"},
        {"name": "Umibozu, Pacific Japan", "lat": 33.0000, "lon": 135.0000, "location": "Kii Channel, Japan", "country": "Japan", "era": "Edo period", "description": "A giant black humanoid sea spirit that capsizes ships. Fishermen must not speak to it or look at it.", "type": "Sea spirit", "status": "Folklore"},
        {"name": "Qalupalik, Arctic Waters", "lat": 63.7500, "lon": -68.5000, "location": "Baffin Island, Canada", "country": "Canada", "era": "Inuit tradition", "description": "A green-skinned aquatic humanoid that lurks under ice, snatching children who wander too close to shore.", "type": "Aquatic humanoid", "status": "Indigenous legend"},
        {"name": "Charybdis Whirlpool", "lat": 38.2600, "lon": 15.6400, "location": "Messina Strait, Sicily", "country": "Italy", "era": "Ancient", "description": "The daughter of Poseidon, cursed by Zeus into a whirlpool monster that swallows the sea three times daily.", "type": "Whirlpool monster", "status": "Classical myth"},
        {"name": "Mokele-mbembe Lake", "lat": 1.6200, "lon": 16.0400, "location": "Lake Tele, Congo", "country": "Republic of Congo", "era": "1776+", "description": "A sauropod-like creature in Congo Basin swamps. Multiple expeditions mounted since the 19th century.", "type": "Lake monster", "status": "Cryptid"},
        {"name": "Giant Squid First Photo", "lat": 27.1900, "lon": 142.1800, "location": "Ogasawara Islands, Japan", "country": "Japan", "era": "2004", "description": "First live giant squid photographed at 900m depth. Validated centuries of Kraken-like legends.", "type": "Giant squid", "status": "Confirmed species"},
        {"name": "Colossal Squid Waters", "lat": -60.0000, "lon": 170.0000, "location": "Ross Sea, Antarctica", "country": "International Waters", "era": "2007", "description": "A 10m colossal squid caught by fishermen. Rotating hooks on tentacles. Largest invertebrate ever captured.", "type": "Colossal squid", "status": "Confirmed species"},
        {"name": "Loch Ness Classic", "lat": 57.3229, "lon": -4.4244, "location": "Loch Ness, Scotland", "country": "United Kingdom", "era": "565 AD+", "description": "The most famous lake monster worldwide. Over 1000 sightings. Multi-million pound tourism industry.", "type": "Plesiosaur-type", "status": "Active legend"},
        {"name": "Stoorworm of Orkney", "lat": 58.9800, "lon": -2.9600, "location": "Orkney Islands, Scotland", "country": "United Kingdom", "era": "Norse-Scottish", "description": "A world-sized sea serpent whose dying body formed Iceland, the Faroes, and Orkney. Its liver still burns as volcanoes.", "type": "World serpent", "status": "Mythology"},
        {"name": "Caspian Sea Dragon", "lat": 41.0000, "lon": 50.0000, "location": "Caspian Sea", "country": "Azerbaijan/Iran", "era": "Ancient", "description": "Persian legends describe water dragons (Azhi) in the Caspian. Azhi Dahaka was a three-headed storm dragon.", "type": "Azhi", "status": "Persian myth"},
        {"name": "Dobhar-chu", "lat": 54.2500, "lon": -8.2000, "location": "Glenade Lake, Ireland", "country": "Ireland", "era": "1722", "description": "The 'water hound' - a giant otter-like creature. A gravestone in Glenade depicts a woman killed by one.", "type": "Water hound", "status": "Folklore"},
        {"name": "Tiamat's Domain", "lat": 31.0000, "lon": 47.0000, "location": "Persian Gulf (mythic)", "country": "Iraq", "era": "Babylonian", "description": "Tiamat, the primordial sea dragon goddess of Babylonian creation myth, slain by Marduk to form the world.", "type": "Primordial dragon", "status": "Mythology"},
        {"name": "Isonade, Deep Pacific", "lat": 33.5000, "lon": 131.5000, "location": "Western Pacific, Japan", "country": "Japan", "era": "Edo period", "description": "A massive shark-like beast with hooked tail and barbed fins. Drags ships and whales to the depths.", "type": "Sea beast", "status": "Folklore"},
        {"name": "Coelacanth Discovery", "lat": -32.9700, "lon": 27.8700, "location": "East London, South Africa", "country": "South Africa", "era": "1938", "description": "A 'living fossil' fish thought extinct for 66 million years. Found alive, validating sea monster possibility.", "type": "Living fossil", "status": "Confirmed species"},
    ])


def _unicorn_griffin():
    return pd.DataFrame([
        {"name": "Unicorn Tapestries, Cluny", "lat": 48.8508, "lon": 2.3468, "location": "Musee de Cluny, Paris", "country": "France", "era": "1500", "description": "The Lady and the Unicorn tapestries, masterpieces of medieval art depicting the five senses plus 'a mon seul desir'.", "type": "Unicorn art", "status": "Museum"},
        {"name": "Unicorn Tapestries, Cloisters", "lat": 40.8649, "lon": -73.9319, "location": "The Cloisters, New York", "country": "USA", "era": "1495-1505", "description": "The Hunt of the Unicorn, seven tapestries depicting the pursuit and capture of a unicorn. South Netherlandish.", "type": "Unicorn art", "status": "Museum"},
        {"name": "Griffin Gate, Persepolis", "lat": 29.9353, "lon": 52.8914, "location": "Persepolis, Iran", "country": "Iran", "era": "500 BC", "description": "Griffin capitals and reliefs throughout the Achaemenid palace complex. Griffins symbolized divine power.", "type": "Griffin relief", "status": "UNESCO site"},
        {"name": "Unicorn of Scotland", "lat": 55.9486, "lon": -3.1999, "location": "Edinburgh, Scotland", "country": "United Kingdom", "era": "12th century+", "description": "The unicorn is Scotland's national animal. It appears on the Royal Coat of Arms, chained by English lions.", "type": "Heraldic unicorn", "status": "National symbol"},
        {"name": "Elasmotherium Habitat", "lat": 50.0000, "lon": 55.0000, "location": "Ural Steppes, Russia", "country": "Russia", "era": "Pleistocene", "description": "The 'Siberian Unicorn' - a real giant rhinoceros with a massive single horn. Survived until 29,000 years ago.", "type": "Real unicorn?", "status": "Extinct species"},
        {"name": "Griffin Vulture Colony", "lat": 37.9700, "lon": -5.8700, "location": "Andalusia, Spain", "country": "Spain", "era": "Ongoing", "description": "Griffon vultures with 2.8m wingspans. Their appearance likely inspired griffin legends in the ancient Mediterranean.", "type": "Real inspiration", "status": "Living species"},
        {"name": "Qilin Sighting, Zheng He", "lat": -1.2921, "lon": 36.8219, "location": "East Africa (Malindi)", "country": "Kenya", "era": "1414", "description": "Admiral Zheng He brought a giraffe to the Ming court. It was declared a Qilin (Chinese unicorn), an auspicious omen.", "type": "Qilin", "status": "Historical"},
        {"name": "Karkadann, Arabian Desert", "lat": 21.4225, "lon": 39.8262, "location": "Arabian Peninsula", "country": "Saudi Arabia", "era": "Medieval", "description": "A fierce unicorn-rhino of Persian and Arabic bestiaries. Only a virgin could tame it - echoing European legends.", "type": "Karkadann", "status": "Folklore"},
        {"name": "Unicorn Cave (Einhornhohle)", "lat": 51.7400, "lon": 10.2700, "location": "Harz Mountains, Germany", "country": "Germany", "era": "1541", "description": "Bones found here were long believed to be unicorn remains. Leibniz drew a unicorn skeleton from the finds in 1691.", "type": "Fossil site", "status": "Cave/museum"},
        {"name": "Griffin City of Genoa", "lat": 44.4056, "lon": 8.9463, "location": "Genoa, Italy", "country": "Italy", "era": "Medieval", "description": "The griffin is Genoa's heraldic symbol. Griffin statues guard churches and palaces across the city.", "type": "Heraldic griffin", "status": "City symbol"},
        {"name": "Indus Valley Unicorn Seal", "lat": 27.3257, "lon": 68.8472, "location": "Mohenjo-daro, Pakistan", "country": "Pakistan", "era": "2500 BC", "description": "Hundreds of seals depict a one-horned animal. The most common motif in Harappan civilization art.", "type": "Unicorn seal", "status": "Archaeological"},
        {"name": "Ctesias' Indian Unicorn", "lat": 26.9124, "lon": 75.7873, "location": "Rajasthan, India (attributed)", "country": "India", "era": "400 BC", "description": "Greek physician Ctesias described Indian wild asses with a single horn, possibly Indian rhinoceros.", "type": "Classical account", "status": "Historical text"},
        {"name": "Protoceratops Nests", "lat": 44.0000, "lon": 103.0000, "location": "Gobi Desert, Mongolia", "country": "Mongolia", "era": "Cretaceous/Discovery 1922", "description": "Protoceratops fossils with beaked skulls may have inspired Scythian griffin legends. Adrienne Mayor's hypothesis.", "type": "Griffin origin?", "status": "Paleontological"},
        {"name": "Re'em of the Bible", "lat": 31.7683, "lon": 35.2137, "location": "Jerusalem, Israel", "country": "Israel", "era": "Biblical", "description": "The Hebrew Re'em translated as 'unicorn' in the King James Bible. Likely an aurochs or wild ox.", "type": "Biblical unicorn", "status": "Religious text"},
        {"name": "Narwhal Horn Trade", "lat": 69.0000, "lon": -54.0000, "location": "Greenland Waters", "country": "Greenland/Denmark", "era": "Viking Age+", "description": "Viking traders sold narwhal tusks as unicorn horns (alicorn) for enormous sums. Believed to neutralize poison.", "type": "Narwhal/unicorn", "status": "Historical trade"},
        {"name": "Hippogriff of Ariosto", "lat": 44.4949, "lon": 11.3426, "location": "Bologna, Italy", "country": "Italy", "era": "1516", "description": "Ariosto's Orlando Furioso introduced the hippogriff (horse-griffin hybrid), offspring of a griffin and a mare.", "type": "Hippogriff", "status": "Literature"},
        {"name": "Shadhavar, Persian Unicorn", "lat": 32.6546, "lon": 51.6680, "location": "Isfahan, Iran", "country": "Iran", "era": "Medieval", "description": "A gazelle-like unicorn whose hollow horn produced enchanting music in the wind, luring prey.", "type": "Musical unicorn", "status": "Persian folklore"},
        {"name": "Griffin of St. Mark", "lat": 45.4408, "lon": 12.3155, "location": "Venice, Italy", "country": "Italy", "era": "Medieval", "description": "The Lion of St. Mark has griffin-like qualities. Griffin motifs appear in Venetian Gothic architecture.", "type": "Heraldic", "status": "City symbol"},
        {"name": "Alicorn Throne, Denmark", "lat": 55.6761, "lon": 12.5683, "location": "Rosenborg Castle, Copenhagen", "country": "Denmark", "era": "1662-1671", "description": "The Danish coronation throne is made of narwhal tusks, believed to be unicorn horns when crafted.", "type": "Unicorn artifact", "status": "Museum"},
        {"name": "Abath of Malay Peninsula", "lat": 3.1390, "lon": 101.6869, "location": "Malay Peninsula", "country": "Malaysia", "era": "16th century", "description": "A female unicorn-rhinoceros described by Portuguese traders. Its horn was prized as antidote to poison.", "type": "Abath", "status": "Colonial account"},
        {"name": "Unicorn District, North Korea", "lat": 39.0194, "lon": 125.7381, "location": "Pyongyang, North Korea", "country": "North Korea", "era": "2012 claim", "description": "North Korean archaeologists claimed to find the Kirin (unicorn) lair of King Tongmyong. Widely mocked internationally.", "type": "Kirin lair", "status": "Propaganda/folklore"},
        {"name": "Pegasus Spring, Corinth", "lat": 37.9062, "lon": 22.8800, "location": "Acrocorinth, Greece", "country": "Greece", "era": "Ancient", "description": "Pegasus struck the ground with his hoof creating the Hippocrene spring. Bellerophon tamed Pegasus at Corinth.", "type": "Pegasus", "status": "Classical myth"},
        {"name": "Simurgh Nest, Alborz", "lat": 35.9000, "lon": 51.6700, "location": "Alborz Mountains, Iran", "country": "Iran", "era": "Ancient", "description": "The Simurgh, a benevolent griffin-phoenix hybrid, nests atop the world tree in the Shahnameh epic.", "type": "Simurgh", "status": "Persian epic"},
        {"name": "Unicorn Fresco, Palazzo Farnese", "lat": 42.4566, "lon": 12.1060, "location": "Caprarola, Italy", "country": "Italy", "era": "1560s", "description": "Renaissance frescoes featuring unicorns in the Room of the Unicorn, symbolizing the Farnese family's purity.", "type": "Unicorn art", "status": "Palace art"},
        {"name": "Qilin Avenue, Ming Tombs", "lat": 40.2530, "lon": 116.2204, "location": "Ming Tombs, Beijing", "country": "China", "era": "Ming Dynasty", "description": "Stone Qilin statues line the Sacred Way to the Ming imperial tombs, alongside other mythical guardian beasts.", "type": "Qilin statue", "status": "UNESCO site"},
    ])


def _phoenix_firebird():
    return pd.DataFrame([
        {"name": "Bennu Bird, Heliopolis", "lat": 30.1310, "lon": 31.3133, "location": "Heliopolis (Ain Shams), Egypt", "country": "Egypt", "era": "Ancient Egyptian", "description": "The Bennu bird, Egyptian precursor of the phoenix. Associated with the sun god Ra and creation mythology.", "type": "Bennu", "status": "Mythology"},
        {"name": "Phoenix Temple, Phoenicia", "lat": 34.1184, "lon": 35.6551, "location": "Byblos, Lebanon", "country": "Lebanon", "era": "Ancient", "description": "Herodotus described the phoenix coming to Heliopolis from Arabia/Phoenicia. Byblos was a phoenix cult center.", "type": "Phoenix", "status": "Classical account"},
        {"name": "Fenghuang Palace, Beijing", "lat": 39.9163, "lon": 116.3972, "location": "Forbidden City, Beijing", "country": "China", "era": "Ming Dynasty", "description": "The Fenghuang (Chinese phoenix) adorns empress's quarters. It symbolizes virtue, grace, and the feminine yin.", "type": "Fenghuang", "status": "Imperial symbol"},
        {"name": "Firebird Palace, St. Petersburg", "lat": 59.9311, "lon": 30.3609, "location": "Mariinsky Theatre, St. Petersburg", "country": "Russia", "era": "1910", "description": "Stravinsky's The Firebird premiered here. The Slavic Zhar-Ptitsa (firebird) glows with golden feathers.", "type": "Zhar-Ptitsa", "status": "Folklore/ballet"},
        {"name": "Ho-Oo Shrine, Byodo-in", "lat": 34.8895, "lon": 135.8077, "location": "Uji, Kyoto, Japan", "country": "Japan", "era": "1053", "description": "The Phoenix Hall (Ho-o-do) of Byodo-in temple, topped with two golden Ho-Oo phoenix statues.", "type": "Ho-Oo", "status": "UNESCO site"},
        {"name": "Garuda Wisnu Kencana", "lat": -8.8103, "lon": 115.1675, "location": "Bali, Indonesia", "country": "Indonesia", "era": "2018", "description": "121m tall statue of Vishnu riding Garuda, the solar bird-deity. One of the tallest statues in the world.", "type": "Garuda", "status": "Monument"},
        {"name": "Simurgh Mountain", "lat": 36.4000, "lon": 52.0000, "location": "Alborz Mountains, Iran", "country": "Iran", "era": "Ancient", "description": "The Simurgh nests on Mount Qaf in Persian myth. It raised the hero Zal and gifted healing feathers.", "type": "Simurgh", "status": "Persian epic"},
        {"name": "Phoenix Park, Dublin", "lat": 53.3558, "lon": -6.3298, "location": "Phoenix Park, Dublin", "country": "Ireland", "era": "1662", "description": "Named from 'fionn uisce' (clear water), but a phoenix column stands at the center. Europe's largest enclosed city park.", "type": "Phoenix monument", "status": "Park"},
        {"name": "Vermilion Bird Tomb", "lat": 34.3900, "lon": 108.8800, "location": "Xi'an, China", "country": "China", "era": "Han Dynasty", "description": "Zhu Que, the Vermilion Bird of the South, painted in Han dynasty tombs as celestial guardian of the south.", "type": "Zhu Que", "status": "Tomb art"},
        {"name": "Phoenix, Arizona", "lat": 33.4484, "lon": -112.0740, "location": "Phoenix, Arizona", "country": "USA", "era": "1868", "description": "Named by settler Darrell Duppa who saw a city rising from Hohokam ruins like a phoenix from ashes.", "type": "City name", "status": "City origin"},
        {"name": "Thunderbird Totem, Vancouver", "lat": 49.2827, "lon": -123.1207, "location": "Stanley Park, Vancouver", "country": "Canada", "era": "Pre-colonial", "description": "Thunderbird atop totem poles. In Pacific Northwest mythology, thunderbirds create storms by flapping wings.", "type": "Thunderbird", "status": "Indigenous art"},
        {"name": "Phoenix Fountain, Piazza Pretoria", "lat": 38.1157, "lon": 13.3615, "location": "Palermo, Sicily", "country": "Italy", "era": "1554", "description": "Palermo's city symbol is a phoenix, representing rebirth from destruction. Statues throughout the historic center.", "type": "City phoenix", "status": "City symbol"},
        {"name": "Huma Bird, Persepolis", "lat": 29.9353, "lon": 52.8914, "location": "Persepolis, Iran", "country": "Iran", "era": "500 BC", "description": "The Huma bird never lands, living entirely airborne. Its shadow falling on a person makes them royalty.", "type": "Huma", "status": "Persian myth"},
        {"name": "Suzaku Gate, Nara", "lat": 34.6851, "lon": 135.8048, "location": "Nara, Japan", "country": "Japan", "era": "710 AD", "description": "The Vermilion Bird Gate (Suzakumon) was the main entrance to Heijo Palace, named after the celestial phoenix.", "type": "Suzaku", "status": "Heritage site"},
        {"name": "Adarna Bird, Philippines", "lat": 14.5995, "lon": 120.9842, "location": "Manila, Philippines", "country": "Philippines", "era": "Spanish colonial", "description": "The Ibong Adarna heals with its song and turns listeners to stone. A beloved Filipino epic poem.", "type": "Adarna", "status": "Literature"},
        {"name": "Anqa of Arabia", "lat": 21.3891, "lon": 39.8579, "location": "Mecca region, Saudi Arabia", "country": "Saudi Arabia", "era": "Pre-Islamic", "description": "A giant bird in Arabian mythology, similar to the Roc. Created perfect but became destructive and was destroyed by God.", "type": "Anqa", "status": "Islamic folklore"},
        {"name": "Firebird Lacquer, Palekh", "lat": 56.8000, "lon": 41.5200, "location": "Palekh, Russia", "country": "Russia", "era": "1924+", "description": "Palekh miniature lacquer art famously depicts the Firebird tale. UNESCO Intangible Cultural Heritage.", "type": "Firebird art", "status": "Art tradition"},
        {"name": "Feng Huang City", "lat": 27.9486, "lon": 109.5996, "location": "Fenghuang, Hunan, China", "country": "China", "era": "Ancient", "description": "The town of Fenghuang (Phoenix) with ancient stilted houses along the Tuo River. Named for phoenix sightings.", "type": "Phoenix town", "status": "Heritage town"},
        {"name": "Garuda National Emblem", "lat": -6.1751, "lon": 106.8650, "location": "Jakarta, Indonesia", "country": "Indonesia", "era": "1950", "description": "Garuda Pancasila is Indonesia's national emblem. The golden eagle-deity carries the national motto.", "type": "Garuda", "status": "National symbol"},
        {"name": "Phoenix Mosaic, Antioch", "lat": 36.2000, "lon": 36.1500, "location": "Antakya, Turkey", "country": "Turkey", "era": "2nd century AD", "description": "A stunning Roman-era mosaic of a phoenix with a halo, in the Hatay Archaeology Museum.", "type": "Phoenix art", "status": "Museum"},
        {"name": "Bennu Heron Colony", "lat": 30.1000, "lon": 31.2000, "location": "Nile Delta, Egypt", "country": "Egypt", "era": "Ongoing", "description": "The grey heron and goliath heron of the Nile likely inspired Bennu imagery. Living inspiration for the myth.", "type": "Real inspiration", "status": "Wildlife"},
        {"name": "San Francisco Phoenix", "lat": 37.7749, "lon": -122.4194, "location": "San Francisco, California", "country": "USA", "era": "1906", "description": "The city's flag features a phoenix rising from flames, commemorating its resurrection after the 1906 earthquake.", "type": "City phoenix", "status": "City symbol"},
        {"name": "Coventry Phoenix", "lat": 52.4068, "lon": -1.5197, "location": "Coventry, England", "country": "United Kingdom", "era": "Post-1940", "description": "Coventry adopted the phoenix after its devastation in WWII bombing. The city rose from ashes.", "type": "City phoenix", "status": "City symbol"},
        {"name": "Atlanta Phoenix", "lat": 33.7490, "lon": -84.3880, "location": "Atlanta, Georgia", "country": "USA", "era": "1865", "description": "Atlanta's symbol is a phoenix, representing its rebirth after being burned by Sherman's March in the Civil War.", "type": "City phoenix", "status": "City symbol"},
        {"name": "Kinnaree Temple Art", "lat": 13.7460, "lon": 100.4933, "location": "Grand Palace, Bangkok", "country": "Thailand", "era": "1782", "description": "Half-woman half-bird beings in Himmapan mythology, related to Garuda traditions. Exquisite temple sculptures.", "type": "Kinnaree", "status": "Temple art"},
    ])


def _werewolf_vampire():
    return pd.DataFrame([
        {"name": "Beast of Gevaudan", "lat": 44.6500, "lon": 3.4500, "location": "Gevaudan, Lozere, France", "country": "France", "era": "1764-1767", "description": "A wolf-like beast killed 100+ people over three years. The most documented beast attack in history. Possibly a large wolf or hyena.", "type": "Beast/Werewolf", "status": "Historical"},
        {"name": "Werewolf of Bedburg", "lat": 51.0000, "lon": 6.5700, "location": "Bedburg, Germany", "country": "Germany", "era": "1589", "description": "Peter Stumpp confessed (under torture) to being a werewolf who murdered 14 children. Executed publicly.", "type": "Werewolf trial", "status": "Historical"},
        {"name": "Bran Castle (Dracula's Castle)", "lat": 45.5150, "lon": 25.3672, "location": "Bran, Transylvania, Romania", "country": "Romania", "era": "1377/1897", "description": "Associated with Bram Stoker's Dracula. Vlad the Impaler may have visited. 500,000+ tourists annually.", "type": "Vampire castle", "status": "Tourist attraction"},
        {"name": "Vlad Dracula's Birthplace", "lat": 46.2181, "lon": 24.7914, "location": "Sighisoara, Romania", "country": "Romania", "era": "1431", "description": "Vlad III (the Impaler) was born here. His father was in the Order of the Dragon (Dracul). UNESCO World Heritage.", "type": "Historical Dracula", "status": "UNESCO site"},
        {"name": "Highgate Vampire", "lat": 51.5679, "lon": -0.1468, "location": "Highgate Cemetery, London", "country": "United Kingdom", "era": "1970", "description": "Mass vampire hysteria in the 1970s. Mobs armed with stakes hunted for vampires among the Victorian graves.", "type": "Vampire panic", "status": "Modern legend"},
        {"name": "Werewolves of Poligny", "lat": 46.8400, "lon": 5.7100, "location": "Poligny, Jura, France", "country": "France", "era": "1521", "description": "Pierre Burgot and Michel Verdun confessed to a demonic pact and werewolf transformations. Burned at the stake.", "type": "Werewolf trial", "status": "Historical"},
        {"name": "Strigoi Village", "lat": 44.8500, "lon": 24.8700, "location": "Curtea de Arges, Romania", "country": "Romania", "era": "Ongoing", "description": "Romanian villages still practice strigoi prevention: garlic on doors, stakes through suspected corpses.", "type": "Strigoi tradition", "status": "Living tradition"},
        {"name": "Mercy Brown Vampire", "lat": 41.5298, "lon": -71.6701, "location": "Exeter, Rhode Island", "country": "USA", "era": "1892", "description": "Mercy Brown's exhumed body showed blood in the heart. Her organs were burned and fed to her sick brother.", "type": "Vampire folklore", "status": "Historical"},
        {"name": "Dogman of Michigan", "lat": 44.3148, "lon": -85.6024, "location": "Wexford County, Michigan", "country": "USA", "era": "1887+", "description": "A bipedal canine creature reported across northern Michigan. Popularized by a 1987 radio DJ April Fools hoax turned real.", "type": "Dogman/Werewolf", "status": "Modern cryptid"},
        {"name": "Beast of Bray Road", "lat": 42.5700, "lon": -88.5400, "location": "Elkhorn, Wisconsin", "country": "USA", "era": "1989", "description": "A werewolf-like creature reported on Bray Road. Investigated by journalist Linda Godfrey. Multiple witnesses.", "type": "Werewolf cryptid", "status": "Modern cryptid"},
        {"name": "Varcolaci of Wallachia", "lat": 44.4268, "lon": 26.1025, "location": "Bucharest, Romania", "country": "Romania", "era": "Medieval", "description": "Ghostly wolf-vampires that devour the moon during eclipses. A unique Romanian blend of werewolf and vampire.", "type": "Wolf-vampire", "status": "Folklore"},
        {"name": "Skinwalker Ranch", "lat": 40.2586, "lon": -109.8883, "location": "Uintah County, Utah", "country": "USA", "era": "Navajo tradition", "description": "Navajo Skinwalkers (yee naaldlooshii) are witches who shapeshift into animals. The ranch is a paranormal hotspot.", "type": "Skinwalker", "status": "Indigenous/Modern"},
        {"name": "Nachzehrer, Silesia", "lat": 51.1079, "lon": 17.0385, "location": "Wroclaw, Poland/Silesia", "country": "Poland", "era": "Medieval", "description": "German vampire that chews its own shroud in the grave, killing relatives through sympathetic magic.", "type": "Nachzehrer", "status": "Folklore"},
        {"name": "Chiang Mai Phi Pop", "lat": 18.7883, "lon": 98.9853, "location": "Chiang Mai, Thailand", "country": "Thailand", "era": "Traditional", "description": "Phi Pop is a Thai vampire-spirit that possesses people and devours their entrails. Exorcisms still performed.", "type": "Phi Pop", "status": "Living tradition"},
        {"name": "Aswang Heartland", "lat": 11.5886, "lon": 122.7546, "location": "Capiz Province, Philippines", "country": "Philippines", "era": "Pre-colonial", "description": "Capiz is the aswang capital. Shapeshifting vampires that feed on fetuses and transform into dogs or pigs at night.", "type": "Aswang", "status": "Living tradition"},
        {"name": "Penanggalan of Malaya", "lat": 4.2105, "lon": 101.9758, "location": "Malay Peninsula", "country": "Malaysia", "era": "Traditional", "description": "A female vampire whose head detaches at night with dangling entrails to feed on pregnant women.", "type": "Penanggalan", "status": "Folklore"},
        {"name": "Sava Savanovic Mill", "lat": 44.1600, "lon": 19.5200, "location": "Zarožje, Serbia", "country": "Serbia", "era": "19th century", "description": "Serbia's most famous vampire haunted a watermill. When the mill collapsed in 2012, villagers put garlic on doors.", "type": "Vampire", "status": "Folklore/tourism"},
        {"name": "Vampire of Sozopol", "lat": 42.4172, "lon": 27.6953, "location": "Sozopol, Bulgaria", "country": "Bulgaria", "era": "2012 discovery", "description": "A medieval skeleton with an iron stake through its chest found by archaeologists. Anti-vampire burial practice.", "type": "Vampire burial", "status": "Archaeological"},
        {"name": "Werewolf of Dole", "lat": 47.0959, "lon": 5.4917, "location": "Dole, Jura, France", "country": "France", "era": "1573", "description": "Gilles Garnier, the Hermit of Dole, confessed to killing and eating children while in wolf form. Burned alive.", "type": "Werewolf trial", "status": "Historical"},
        {"name": "Chiang Rai Krasue", "lat": 19.9105, "lon": 99.8406, "location": "Chiang Rai, Thailand", "country": "Thailand", "era": "Traditional", "description": "The Krasue is a floating female head with glowing entrails, seeking blood and flesh at night. Thai horror icon.", "type": "Krasue", "status": "Folklore"},
        {"name": "Lycaon's Arcadia", "lat": 37.5000, "lon": 22.3000, "location": "Arcadia, Peloponnese, Greece", "country": "Greece", "era": "Ancient", "description": "King Lycaon served human flesh to Zeus and was transformed into a wolf. The origin of the word 'lycanthropy'.", "type": "Werewolf origin", "status": "Classical myth"},
        {"name": "Strigoi Prevention Museum", "lat": 45.7489, "lon": 21.2087, "location": "Timisoara, Romania", "country": "Romania", "era": "Various", "description": "Banat region traditions of anti-vampire practices documented extensively. Hearts removed and burned.", "type": "Vampire prevention", "status": "Ethnographic"},
        {"name": "Lobishomen, Sao Luis", "lat": -2.5307, "lon": -44.2826, "location": "Sao Luis, Maranhao, Brazil", "country": "Brazil", "era": "Colonial", "description": "Brazilian werewolf (Lobisomem), said to be the seventh consecutive son. Transforms at crossroads on Friday nights.", "type": "Lobisomem", "status": "Folklore"},
        {"name": "Berserker Graves", "lat": 61.0000, "lon": 8.0000, "location": "Western Norway", "country": "Norway", "era": "Viking Age", "description": "Norse berserkers wore wolf and bear skins, entering trance-like battle frenzy. Possible origin of werewolf warriors.", "type": "Berserker/Ulfhednar", "status": "Historical"},
        {"name": "Vrykolakas of Santorini", "lat": 36.3932, "lon": 25.4615, "location": "Santorini, Greece", "country": "Greece", "era": "17th century", "description": "Greek vampire-revenants. Santorini was notorious for vrykolakas outbreaks. Bodies were exhumed and burned.", "type": "Vrykolakas", "status": "Historical folklore"},
    ])


def _thunderbird_spirits():
    return pd.DataFrame([
        {"name": "Thunderbird Petroglyph", "lat": 45.4000, "lon": -75.7000, "location": "Ottawa Valley, Ontario", "country": "Canada", "era": "Pre-colonial", "description": "Algonquin petroglyphs depict Thunderbird (Animikii) as a supernatural bird that creates thunder with its wings.", "type": "Thunderbird", "status": "Indigenous art"},
        {"name": "Thunderbird Falls, Alaska", "lat": 61.3944, "lon": -149.4414, "location": "Chugach State Park, Alaska", "country": "USA", "era": "Tlingit tradition", "description": "Named for the Tlingit thunderbird legends. A powerful spirit bird controlling storms in Pacific Northwest culture.", "type": "Thunderbird", "status": "Geographic name"},
        {"name": "Piasa Bird Mural", "lat": 38.9200, "lon": -90.1500, "location": "Alton, Illinois", "country": "USA", "era": "1673 (recorded)", "description": "A winged dragon-like creature painted on Mississippi River bluffs. Marquette and Jolliet documented it. Recreated mural exists.", "type": "Piasa Bird", "status": "Historical/mural"},
        {"name": "Quetzalcoatl Temple", "lat": 19.6925, "lon": -98.8439, "location": "Teotihuacan, Mexico", "country": "Mexico", "era": "200 AD", "description": "Temple of the Feathered Serpent, dedicated to Quetzalcoatl. A deity combining bird (quetzal) and serpent (coatl).", "type": "Feathered Serpent", "status": "UNESCO site"},
        {"name": "Kukulkan Pyramid", "lat": 20.6843, "lon": -88.5678, "location": "Chichen Itza, Mexico", "country": "Mexico", "era": "600 AD", "description": "El Castillo pyramid with serpent shadow during equinox. Kukulkan is the Maya feathered serpent deity.", "type": "Feathered Serpent", "status": "UNESCO site"},
        {"name": "Wendigo Territory", "lat": 51.0000, "lon": -85.0000, "location": "Northern Ontario, Canada", "country": "Canada", "era": "Algonquian tradition", "description": "The Wendigo is a cannibalistic spirit of the frozen north. Starvation-induced psychosis was called Wendigo psychosis.", "type": "Wendigo", "status": "Indigenous legend"},
        {"name": "Skinwalker Mesa", "lat": 36.9000, "lon": -109.5000, "location": "Navajo Nation, Arizona", "country": "USA", "era": "Navajo tradition", "description": "Yee naaldlooshii (skinwalkers) are Navajo witches who transform into animals. Speaking of them is taboo.", "type": "Skinwalker", "status": "Indigenous belief"},
        {"name": "Coyote Trickster Origin", "lat": 46.8800, "lon": -110.3600, "location": "Montana (Great Plains)", "country": "USA", "era": "Pre-colonial", "description": "Coyote is the great trickster spirit across many Native American traditions. Both creator and fool.", "type": "Trickster spirit", "status": "Indigenous mythology"},
        {"name": "Uktena Serpent Mound", "lat": 39.0253, "lon": -83.4305, "location": "Serpent Mound, Ohio", "country": "USA", "era": "1000 BC", "description": "A 411m serpent effigy mound. Cherokee legends describe the Uktena, a horned serpent with a crystal forehead.", "type": "Horned Serpent", "status": "Heritage site"},
        {"name": "Underwater Panther, Lake Superior", "lat": 47.5000, "lon": -87.5000, "location": "Lake Superior", "country": "USA/Canada", "era": "Ojibwe tradition", "description": "Mishipeshu, the underwater panther/lynx with copper scales. Enemy of the Thunderbird in Ojibwe cosmology.", "type": "Water panther", "status": "Indigenous legend"},
        {"name": "Raven Creator, Haida Gwaii", "lat": 53.2500, "lon": -132.0700, "location": "Haida Gwaii, British Columbia", "country": "Canada", "era": "Pre-colonial", "description": "Raven discovered humans in a clamshell and released the sun from a box. The supreme trickster-creator of the Haida.", "type": "Raven", "status": "Indigenous mythology"},
        {"name": "Double-Headed Serpent, Aztec", "lat": 19.4326, "lon": -99.1332, "location": "Mexico City (Tenochtitlan)", "country": "Mexico", "era": "Aztec", "description": "The turquoise mosaic double-headed serpent in the British Museum, likely worn as a ceremonial pectoral.", "type": "Xiuhcoatl", "status": "Museum artifact"},
        {"name": "Sasquatch Territory", "lat": 49.0000, "lon": -121.7500, "location": "Harrison Hot Springs, BC", "country": "Canada", "era": "Sts'ailes tradition", "description": "Sasquatch derives from Halkomelem 'sasq'ets'. The Sts'ailes people have ancient traditions of wild forest giants.", "type": "Sasquatch", "status": "Indigenous/Cryptid"},
        {"name": "Avanyu Petroglyph", "lat": 35.8800, "lon": -106.1400, "location": "Bandelier, New Mexico", "country": "USA", "era": "Ancestral Puebloan", "description": "Avanyu the water serpent appears in Pueblo petroglyphs and pottery. A horned plumed serpent controlling storms.", "type": "Water serpent", "status": "Indigenous art"},
        {"name": "Tlingit Thunderbird Totem", "lat": 58.3005, "lon": -134.4197, "location": "Juneau, Alaska", "country": "USA", "era": "Pre-colonial", "description": "Tlingit totem poles feature Thunderbird prominently. It battles the killer whale in a cosmic struggle.", "type": "Thunderbird", "status": "Indigenous art"},
        {"name": "Pukwudgie Territory", "lat": 41.7600, "lon": -70.9500, "location": "Freetown-Fall River State Forest, MA", "country": "USA", "era": "Wampanoag tradition", "description": "Small troll-like beings that lure people off cliffs and use magic arrows. Increasingly reported in paranormal circles.", "type": "Pukwudgie", "status": "Indigenous legend"},
        {"name": "Kokopelli Rock Art", "lat": 36.8600, "lon": -111.5100, "location": "Glen Canyon, Utah", "country": "USA", "era": "Ancestral Puebloan", "description": "Humpbacked flute player petroglyph found across the Southwest. A fertility and trickster deity.", "type": "Kokopelli", "status": "Indigenous art"},
        {"name": "Thunderbird Park, Victoria", "lat": 48.4207, "lon": -123.3667, "location": "Royal BC Museum, Victoria", "country": "Canada", "era": "1941", "description": "Outdoor collection of First Nations totem poles and a carved Thunderbird House. Major cultural preservation site.", "type": "Thunderbird", "status": "Museum"},
        {"name": "Horned Serpent Effigy, Georgia", "lat": 34.3500, "lon": -84.8000, "location": "Etowah Mounds, Georgia", "country": "USA", "era": "1000-1550 AD", "description": "Mississippian culture shell gorgets depicting the horned serpent (Uktena). Part of the Southeastern Ceremonial Complex.", "type": "Horned Serpent", "status": "Archaeological"},
        {"name": "Spider Woman, Canyon de Chelly", "lat": 36.1300, "lon": -109.4700, "location": "Canyon de Chelly, Arizona", "country": "USA", "era": "Navajo tradition", "description": "Spider Rock where Spider Woman taught the Navajo to weave. A sacred pillar rising 230m from the canyon floor.", "type": "Spider Woman", "status": "Sacred site"},
        {"name": "Tezcatlipoca Jaguar Spirit", "lat": 19.0414, "lon": -98.2063, "location": "Cholula, Mexico", "country": "Mexico", "era": "Aztec/Toltec", "description": "Tezcatlipoca, the Smoking Mirror god who transforms into a jaguar. Rival of Quetzalcoatl.", "type": "Jaguar god", "status": "Mythology"},
        {"name": "Wampus Cat, Appalachia", "lat": 35.5951, "lon": -82.5515, "location": "Appalachian Mountains, NC", "country": "USA", "era": "Cherokee tradition", "description": "A six-legged cat-woman spirit. Cherokee legend says a woman disguised in a cat skin to spy on men's rituals was cursed.", "type": "Wampus Cat", "status": "Folklore"},
        {"name": "Deer Woman, Oklahoma", "lat": 35.4676, "lon": -97.5164, "location": "Oklahoma (Plains tribes)", "country": "USA", "era": "Pre-colonial", "description": "A beautiful woman with deer hooves who punishes unfaithful men. Common across Plains and Woodland tribes.", "type": "Deer Woman", "status": "Indigenous legend"},
        {"name": "Pamola, Mount Katahdin", "lat": 45.9044, "lon": -68.9213, "location": "Mount Katahdin, Maine", "country": "USA", "era": "Penobscot tradition", "description": "A moose-headed bird-spirit guarding Katahdin. Penobscot people warned against climbing the mountain.", "type": "Pamola", "status": "Indigenous legend"},
        {"name": "Xibalba Entrance, Cenotes", "lat": 20.6600, "lon": -88.5600, "location": "Yucatan Cenotes, Mexico", "country": "Mexico", "era": "Maya", "description": "Cenotes were entrances to Xibalba, the Maya underworld ruled by death lords and supernatural creatures.", "type": "Underworld entrance", "status": "Sacred site"},
    ])


def _japanese_yokai():
    return pd.DataFrame([
        {"name": "Yokai Street (Ichijo-dori)", "lat": 35.0270, "lon": 135.7400, "location": "Kyoto, Japan", "country": "Japan", "era": "Heian period+", "description": "Ichijo-dori street where the Hyakki Yagyo (Night Parade of 100 Demons) was said to occur. Yokai shops today.", "type": "Yokai parade", "status": "Cultural site"},
        {"name": "Kappa Bridge, Kamikochi", "lat": 36.2480, "lon": 137.6300, "location": "Kamikochi, Nagano", "country": "Japan", "era": "Traditional", "description": "Named for the kappa water imps said to inhabit the Azusa River. Kappa drag people underwater.", "type": "Kappa", "status": "Geographic name"},
        {"name": "Oni Museum, Fukuchiyama", "lat": 35.2917, "lon": 135.1253, "location": "Fukuchiyama, Kyoto", "country": "Japan", "era": "Modern museum", "description": "Japan's Oni (demon) museum. Shuten-doji, the king of oni, terrorized the area from Mount Oeyama.", "type": "Oni", "status": "Museum"},
        {"name": "Tengu Mountain, Kurama", "lat": 35.1200, "lon": 135.7700, "location": "Mount Kurama, Kyoto", "country": "Japan", "era": "Heian period", "description": "Sojobo, the king of tengu (crow-men), trained the warrior Minamoto no Yoshitsune in martial arts here.", "type": "Tengu", "status": "Sacred mountain"},
        {"name": "Tanuki Temple, Shikoku", "lat": 34.0700, "lon": 134.5500, "location": "Tokushima, Shikoku", "country": "Japan", "era": "Traditional", "description": "Tanuki (raccoon dog) statues everywhere in Shikoku. Shapeshifting tricksters that transform into humans and objects.", "type": "Tanuki", "status": "Cultural icon"},
        {"name": "Kitsune Shrine (Fushimi Inari)", "lat": 34.9671, "lon": 135.7727, "location": "Fushimi Inari, Kyoto", "country": "Japan", "era": "711 AD", "description": "Thousands of torii gates guarded by kitsune (fox) statues. Foxes are messengers of Inari, god of rice.", "type": "Kitsune", "status": "Shrine"},
        {"name": "Jorougumo Falls", "lat": 34.9800, "lon": 138.9800, "location": "Joren Falls, Shizuoka", "country": "Japan", "era": "Edo period", "description": "Jorougumo, a spider-woman yokai, lures men to their death at this waterfall. She plays a biwa lute.", "type": "Jorougumo", "status": "Folklore site"},
        {"name": "Gashadokuro Territory", "lat": 36.3900, "lon": 140.3800, "location": "Kanto Plain, Japan", "country": "Japan", "era": "Medieval", "description": "Giant skeletons (gashadokuro) formed from the bones of unburied war dead. They roam battlefields at night.", "type": "Gashadokuro", "status": "Folklore"},
        {"name": "Yuki-Onna Pass", "lat": 36.8500, "lon": 139.8800, "location": "Nikko Mountains, Tochigi", "country": "Japan", "era": "Edo period", "description": "The Snow Woman appears in blizzards, breathing frost to kill travelers. Lafcadio Hearn popularized the tale.", "type": "Yuki-Onna", "status": "Folklore"},
        {"name": "Nurarihyon Origin", "lat": 34.6937, "lon": 135.5023, "location": "Osaka, Japan", "country": "Japan", "era": "Edo period", "description": "The supreme commander of yokai, an old man with an enormous head who sneaks into houses and acts as master.", "type": "Nurarihyon", "status": "Folklore"},
        {"name": "Tsukumogami Quarter", "lat": 35.0116, "lon": 135.7681, "location": "Gion, Kyoto", "country": "Japan", "era": "Muromachi period", "description": "Objects that reach 100 years old become tsukumogami (living tools). Umbrellas, lanterns, sandals come alive.", "type": "Tsukumogami", "status": "Folklore"},
        {"name": "Nekomata Temple", "lat": 36.9500, "lon": 138.6000, "location": "Niigata, Japan", "country": "Japan", "era": "Traditional", "description": "Nekomata are supernatural cats whose tails split in two. They can raise the dead and control corpses.", "type": "Nekomata", "status": "Folklore"},
        {"name": "Aokigahara (Yokai Forest)", "lat": 35.4700, "lon": 138.6200, "location": "Mount Fuji base, Yamanashi", "country": "Japan", "era": "Ancient", "description": "The Sea of Trees is associated with yurei (ghosts) and yokai. Historically linked to ubasute (abandoning elderly).", "type": "Yurei/Yokai", "status": "Folklore site"},
        {"name": "Nure-Onna Coast", "lat": 33.2500, "lon": 131.6000, "location": "Oita Coast, Kyushu", "country": "Japan", "era": "Traditional", "description": "Nure-Onna, a snake-bodied woman who appears on beaches holding a baby bundle. If you take it, she devours you.", "type": "Nure-Onna", "status": "Folklore"},
        {"name": "Rokurokubi Quarter", "lat": 35.6762, "lon": 139.6503, "location": "Edo (Tokyo)", "country": "Japan", "era": "Edo period", "description": "Women whose necks stretch impossibly at night while they sleep. They fly around drinking lamp oil.", "type": "Rokurokubi", "status": "Folklore"},
        {"name": "Umi-Bozu Bay", "lat": 34.3963, "lon": 132.4596, "location": "Seto Inland Sea", "country": "Japan", "era": "Traditional", "description": "Umi-bozu are giant black humanoid sea spirits that appear in calm seas and demand a barrel (to sink your ship).", "type": "Umi-Bozu", "status": "Folklore"},
        {"name": "Yamata no Orochi Shrine", "lat": 35.3700, "lon": 132.6700, "location": "Izumo, Shimane", "country": "Japan", "era": "Mythological", "description": "The eight-headed serpent slain by Susanoo. He found the Kusanagi sword in its tail. Origin of Japan's imperial regalia.", "type": "Orochi", "status": "Mythology"},
        {"name": "Mizuki Shigeru Road", "lat": 35.4420, "lon": 133.3479, "location": "Sakaiminato, Tottori", "country": "Japan", "era": "Modern", "description": "800m street with 177 bronze yokai statues from manga artist Mizuki Shigeru's GeGeGe no Kitaro. A yokai theme town.", "type": "Yokai statues", "status": "Tourist attraction"},
        {"name": "Bakeneko Alley", "lat": 33.5904, "lon": 130.4017, "location": "Fukuoka, Kyushu", "country": "Japan", "era": "Edo period", "description": "Bakeneko (ghost cats) dance with napkins on their heads and shapeshift into humans. Nabeshima cat disturbance legends.", "type": "Bakeneko", "status": "Folklore"},
        {"name": "Raijin & Fujin Gate", "lat": 35.7115, "lon": 139.7966, "location": "Senso-ji, Tokyo", "country": "Japan", "era": "628 AD", "description": "The Kaminarimon gate features Raijin (thunder god) and Fujin (wind god), supernatural storm deities.", "type": "Storm gods", "status": "Temple"},
        {"name": "Dorotabo Rice Paddy", "lat": 35.1815, "lon": 136.9066, "location": "Nagoya area, Aichi", "country": "Japan", "era": "Traditional", "description": "A one-eyed muddy ghost rising from neglected rice paddies, wailing 'Give me back my field!' at lazy farmers.", "type": "Dorotabo", "status": "Folklore"},
        {"name": "Futakuchi-Onna Village", "lat": 39.7200, "lon": 140.1000, "location": "Akita Prefecture", "country": "Japan", "era": "Traditional", "description": "A woman with a second mouth on the back of her head, hidden under hair. It eats voraciously using hair-tentacles.", "type": "Futakuchi-Onna", "status": "Folklore"},
        {"name": "Namahage Festival", "lat": 39.8800, "lon": 139.8600, "location": "Oga Peninsula, Akita", "country": "Japan", "era": "Traditional", "description": "Namahage demons visit homes on New Year's Eve, frightening lazy children. UNESCO Intangible Cultural Heritage.", "type": "Namahage", "status": "Living tradition"},
        {"name": "Zashiki-Warashi Inn", "lat": 39.4800, "lon": 141.7500, "location": "Tono, Iwate", "country": "Japan", "era": "Traditional", "description": "Child ghosts that haunt old houses. If the zashiki-warashi leaves, the household falls to ruin. Lucky to have one.", "type": "Zashiki-Warashi", "status": "Folklore"},
        {"name": "Tofu Kozo Street", "lat": 35.6895, "lon": 139.6917, "location": "Shinjuku, Tokyo", "country": "Japan", "era": "Edo period", "description": "A childlike yokai carrying a tray of tofu. Harmless but persistent. If you eat the tofu, mold grows on your body.", "type": "Tofu Kozo", "status": "Folklore"},
    ])


def _celtic_norse():
    return pd.DataFrame([
        {"name": "Loch Ness Kelpie", "lat": 57.3229, "lon": -4.4244, "location": "Loch Ness, Scotland", "country": "United Kingdom", "era": "Celtic", "description": "Before Nessie, the loch was home to a kelpie - a shapeshifting water horse that drowns riders. Celtic water spirit.", "type": "Kelpie", "status": "Folklore"},
        {"name": "The Kelpies Sculpture", "lat": 56.0172, "lon": -3.7566, "location": "Falkirk, Scotland", "country": "United Kingdom", "era": "2013", "description": "Two 30m tall horse-head sculptures by Andy Scott, inspired by the kelpie mythology of Scottish waterways.", "type": "Kelpie art", "status": "Monument"},
        {"name": "Fenrir's Binding", "lat": 64.1466, "lon": -21.9426, "location": "Iceland (mythic)", "country": "Iceland", "era": "Norse", "description": "The monstrous wolf Fenrir, son of Loki, bound by the gods with Gleipnir. Breaks free at Ragnarok to devour Odin.", "type": "Fenrir", "status": "Norse mythology"},
        {"name": "Sleipnir's Birthplace", "lat": 65.6835, "lon": -18.0878, "location": "North Iceland (mythic)", "country": "Iceland", "era": "Norse", "description": "Odin's eight-legged horse, born when Loki shapeshifted into a mare. The fastest steed in all the Nine Worlds.", "type": "Sleipnir", "status": "Norse mythology"},
        {"name": "Cu Chulainn's Leap", "lat": 54.0500, "lon": -6.3300, "location": "Cooley Peninsula, Louth", "country": "Ireland", "era": "Iron Age", "description": "The Hound of Ulster fought the Tain war here. He battled single-handedly against Connacht's army for months.", "type": "Hero/beast", "status": "Irish mythology"},
        {"name": "Balor's Tower, Tory Island", "lat": 55.2700, "lon": -8.2300, "location": "Tory Island, Donegal", "country": "Ireland", "era": "Celtic", "description": "Balor of the Evil Eye, Fomorian giant whose gaze destroyed armies. Slain by his grandson Lugh at Moytura.", "type": "Fomorian", "status": "Irish mythology"},
        {"name": "Nuckelavee Shore, Orkney", "lat": 58.9800, "lon": -2.9600, "location": "Orkney Islands, Scotland", "country": "United Kingdom", "era": "Norse-Scottish", "description": "The most terrifying Scottish creature: a skinless horse-man hybrid from the sea. Its breath wilts crops.", "type": "Nuckelavee", "status": "Folklore"},
        {"name": "Each-Uisge, Loch Awe", "lat": 56.3500, "lon": -5.1000, "location": "Loch Awe, Scotland", "country": "United Kingdom", "era": "Celtic", "description": "A water horse deadlier than the kelpie. It lures riders then dives, leaving only the liver floating.", "type": "Each-Uisge", "status": "Folklore"},
        {"name": "Huginn & Muninn, Uppsala", "lat": 59.8586, "lon": 17.6389, "location": "Old Uppsala, Sweden", "country": "Sweden", "era": "Viking Age", "description": "Odin's ravens Thought and Memory fly across the world each day. The great temple at Uppsala honored Odin.", "type": "Divine ravens", "status": "Norse mythology"},
        {"name": "Ratatoskr, World Tree", "lat": 63.0000, "lon": 12.0000, "location": "Scandinavia (mythic)", "country": "Norway/Sweden", "era": "Norse", "description": "A squirrel that runs up and down Yggdrasil carrying insults between the eagle at the top and Nidhogg at the roots.", "type": "Cosmic squirrel", "status": "Norse mythology"},
        {"name": "Pooka Bridge, Wicklow", "lat": 53.0000, "lon": -6.3800, "location": "Wicklow Mountains, Ireland", "country": "Ireland", "era": "Celtic", "description": "The Pooka is a shapeshifting fairy that appears as a black horse, goat, or rabbit. It can give good or bad fortune.", "type": "Pooka", "status": "Folklore"},
        {"name": "Banshee Ford, Bunratty", "lat": 52.6977, "lon": -8.8050, "location": "Bunratty, Clare, Ireland", "country": "Ireland", "era": "Celtic", "description": "The Bean Sidhe (Banshee) wails to foretell death. Attached to old Irish families. Heard at fords and crossroads.", "type": "Banshee", "status": "Folklore"},
        {"name": "Selkie Shores, Shetland", "lat": 60.3913, "lon": -1.2816, "location": "Shetland Islands, Scotland", "country": "United Kingdom", "era": "Norse-Celtic", "description": "Selkies are seals that shed their skin to become human. If a man steals a selkie's skin, she must be his wife.", "type": "Selkie", "status": "Folklore"},
        {"name": "Nidhogg at Hvergelmir", "lat": 65.6260, "lon": -16.9000, "location": "East Iceland (Myvatn)", "country": "Iceland", "era": "Norse", "description": "Nidhogg the dragon gnaws Yggdrasil's roots at the spring Hvergelmir. Iceland's volcanic hot springs evoke the myth.", "type": "Nidhogg", "status": "Norse mythology"},
        {"name": "Fomorian Coast, Connemara", "lat": 53.4500, "lon": -10.0000, "location": "Connemara, Galway", "country": "Ireland", "era": "Celtic", "description": "The Fomorians were sea-giants, chaotic beings of the deep. They invaded Ireland before being defeated by the Tuatha De Danann.", "type": "Fomorian", "status": "Irish mythology"},
        {"name": "Draugr Burial, Birka", "lat": 59.3300, "lon": 17.5500, "location": "Birka, Sweden", "country": "Sweden", "era": "Viking Age", "description": "Draugar are undead Norse warriors guarding their burial mounds. Viking graves were sealed to prevent their escape.", "type": "Draugr", "status": "Norse mythology"},
        {"name": "Wild Hunt, Dartmoor", "lat": 50.5719, "lon": -3.9207, "location": "Dartmoor, Devon, England", "country": "United Kingdom", "era": "Celtic/Norse", "description": "The Wild Hunt sweeps across Dartmoor on stormy nights, led by Woden or Herne. Anyone caught outside is swept away.", "type": "Wild Hunt", "status": "Folklore"},
        {"name": "Cath Palug, Anglesey", "lat": 53.2300, "lon": -4.3000, "location": "Anglesey, Wales", "country": "United Kingdom", "era": "Arthurian", "description": "Cath Palug, a monstrous cat born from the sow Henwen. In Welsh and French Arthurian legend, it terrorized Anglesey.", "type": "Monster cat", "status": "Arthurian legend"},
        {"name": "Morrigan Battlefield, Moytura", "lat": 53.7000, "lon": -8.5000, "location": "Moytura, Galway", "country": "Ireland", "era": "Celtic", "description": "The Morrigan, a triple war-goddess who shapeshifts into a crow. She decided the outcome of the Battle of Moytura.", "type": "War goddess", "status": "Irish mythology"},
        {"name": "Jotunheim Mountains", "lat": 61.6000, "lon": 8.3000, "location": "Jotunheimen, Norway", "country": "Norway", "era": "Norse", "description": "The real mountain range named after the land of the frost giants (Jotnar). Galdhopiggen is Norway's highest peak.", "type": "Giant realm", "status": "Geographic name"},
        {"name": "Kraken Church, Bergen", "lat": 60.3913, "lon": 5.3221, "location": "Bergen, Norway", "country": "Norway", "era": "1180 AD", "description": "Erik Pontoppidan, Bishop of Bergen, wrote the definitive 1752 account of the Kraken in his Natural History of Norway.", "type": "Kraken", "status": "Historical account"},
        {"name": "Fairy Fort, Hill of Tara", "lat": 53.5793, "lon": -6.6117, "location": "Hill of Tara, Meath", "country": "Ireland", "era": "Neolithic/Celtic", "description": "The ancient seat of Irish High Kings, riddled with fairy forts (raths). The Tuatha De Danann retreated into the sidhe mounds.", "type": "Fairy realm", "status": "Heritage site"},
        {"name": "Glastonbury Tor Dragon", "lat": 51.1442, "lon": -2.6987, "location": "Glastonbury, Somerset", "country": "United Kingdom", "era": "Arthurian/Celtic", "description": "The terraced hill is said to be a sleeping dragon. Ley lines converge here. Associated with Avalon and the Holy Grail.", "type": "Earth dragon", "status": "Sacred site"},
        {"name": "Cwn Annwn, Cadair Idris", "lat": 52.6997, "lon": -3.9063, "location": "Cadair Idris, Wales", "country": "United Kingdom", "era": "Celtic", "description": "The Hounds of Annwn (Welsh underworld) hunt across the sky. Their howling grows quieter as they approach.", "type": "Spectral hounds", "status": "Welsh mythology"},
        {"name": "Fossegrim Falls, Hardanger", "lat": 60.4200, "lon": 6.7400, "location": "Hardangerfjord, Norway", "country": "Norway", "era": "Norse", "description": "The Fossegrim is a water spirit who plays the fiddle beneath waterfalls. He teaches musicians who offer a white goat.", "type": "Water spirit", "status": "Folklore"},
    ])


def _dragon_museums():
    return pd.DataFrame([
        {"name": "Dragon Museum, Furth im Wald", "lat": 49.3107, "lon": 12.8376, "location": "Furth im Wald, Bavaria", "country": "Germany", "era": "Annual since 1590", "description": "Home to the world's largest walking robot dragon (15m). The Drachenstich festival features a dragon-slaying play.", "type": "Festival/Museum", "status": "Annual festival"},
        {"name": "Dragon Festival, Krakow", "lat": 50.0540, "lon": 19.9352, "location": "Krakow, Poland", "country": "Poland", "era": "Annual June", "description": "The Grand Dragon Parade with giant puppets, fire shows, and the Wawel Dragon's birthday celebration.", "type": "Festival", "status": "Annual festival"},
        {"name": "Dragon Boat Festival HQ", "lat": 30.5728, "lon": 114.2679, "location": "Wuhan, Hubei, China", "country": "China", "era": "Annual", "description": "Duanwu Festival with dragon boat races honoring Qu Yuan. UNESCO Intangible Cultural Heritage since 2009.", "type": "Festival", "status": "UNESCO tradition"},
        {"name": "Dragon Museum, Ljubljana", "lat": 46.0514, "lon": 14.5060, "location": "Ljubljana, Slovenia", "country": "Slovenia", "era": "Ongoing", "description": "The House of Experiments and city tours focused on Ljubljana's dragon legend. Dragon Bridge is the city icon.", "type": "City museum", "status": "Tourism"},
        {"name": "St. George & Dragon, Stockholm", "lat": 59.3256, "lon": 18.0716, "location": "Storkyrkan, Stockholm", "country": "Sweden", "era": "1489", "description": "Bernt Notke's wooden sculpture of St. George slaying the dragon. One of the finest medieval sculptures in Northern Europe.", "type": "Sculpture", "status": "Church art"},
        {"name": "Dragon Procession, Mons", "lat": 50.4542, "lon": 3.9522, "location": "Mons, Belgium", "country": "Belgium", "era": "Annual since 1380", "description": "The Ducasse de Mons (Doudou) features the Lumecon: St. George battles a dragon in the Grand Place. UNESCO listed.", "type": "Festival", "status": "UNESCO tradition"},
        {"name": "Tarasque Festival, Tarascon", "lat": 43.8069, "lon": 4.6589, "location": "Tarascon, France", "country": "France", "era": "Annual since 1474", "description": "A giant Tarasque effigy parades through streets. Participants run from it. UNESCO Intangible Cultural Heritage.", "type": "Festival", "status": "UNESCO tradition"},
        {"name": "Potteries Dragon Museum", "lat": 53.0027, "lon": -2.1794, "location": "Stoke-on-Trent, England", "country": "United Kingdom", "era": "Ongoing", "description": "Dragon-themed ceramics spanning centuries at the Potteries Museum, including Chinese dragon porcelain collections.", "type": "Museum", "status": "Museum"},
        {"name": "Dragon Cave, Wawel", "lat": 50.0537, "lon": 19.9351, "location": "Wawel Hill, Krakow", "country": "Poland", "era": "Tourist attraction", "description": "The cave beneath Wawel Castle where Smok the dragon allegedly lived. Open to visitors in summer months.", "type": "Dragon cave", "status": "Tourist site"},
        {"name": "Chinese Dragon Museum, Tongling", "lat": 30.9500, "lon": 117.8100, "location": "Tongling, Anhui, China", "country": "China", "era": "Modern", "description": "Dedicated museum exploring Chinese dragon culture, art, and symbolism through 5,000 years of civilization.", "type": "Museum", "status": "Museum"},
        {"name": "Dragonalia, Ljublijana", "lat": 46.0500, "lon": 14.5000, "location": "Ljubljana Old Town", "country": "Slovenia", "era": "Modern", "description": "A dragon-themed interactive experience in Ljubljana's old town. Merges AR technology with the city's dragon legend.", "type": "Experience", "status": "Tourism"},
        {"name": "Dragon's Den, National Museum Wales", "lat": 51.4816, "lon": -3.1791, "location": "Cardiff, Wales", "country": "United Kingdom", "era": "Ongoing", "description": "The Welsh red dragon (Y Ddraig Goch) exhibitions. Wales is the only country with a dragon on its national flag.", "type": "Museum/National", "status": "National symbol"},
        {"name": "Komodo Dragon Reserve", "lat": -8.5500, "lon": 119.4400, "location": "Komodo Island, Indonesia", "country": "Indonesia", "era": "1980 (park)", "description": "Home to real dragons: Komodo monitors up to 3m long. UNESCO World Heritage Site and the closest thing to living dragons.", "type": "Real dragons", "status": "UNESCO site"},
        {"name": "Dragon Boat Museum, Hangzhou", "lat": 30.2741, "lon": 120.1551, "location": "Hangzhou, Zhejiang", "country": "China", "era": "Modern", "description": "Museum dedicated to dragon boat racing history and culture on the shores of West Lake.", "type": "Museum", "status": "Museum"},
        {"name": "Sant Jordi Festival, Barcelona", "lat": 41.3851, "lon": 2.1734, "location": "Barcelona, Spain", "country": "Spain", "era": "Annual April 23", "description": "La Diada de Sant Jordi: Barcelona celebrates St. George's dragon slaying with roses and books. The city's most romantic day.", "type": "Festival", "status": "Cultural tradition"},
        {"name": "Wyvern Inn, Hereford", "lat": 52.0565, "lon": -2.7160, "location": "Hereford, England", "country": "United Kingdom", "era": "Historic", "description": "A historic dragon-themed pub in the heart of wyvern country. Herefordshire has multiple dragon legends.", "type": "Dragon pub", "status": "Heritage"},
        {"name": "Dragon Festival, Klagenfurt", "lat": 46.6247, "lon": 14.3053, "location": "Klagenfurt, Austria", "country": "Austria", "era": "Annual", "description": "The Lindworm Fountain (Lindwurmbrunnen) is the city landmark. Annual festivals celebrate the dragon-slaying legend.", "type": "Festival", "status": "City tradition"},
        {"name": "Dragon King Temple, Pingyao", "lat": 37.2000, "lon": 112.1800, "location": "Pingyao, Shanxi, China", "country": "China", "era": "Yuan Dynasty", "description": "An ancient temple to the Dragon King deity who controls rainfall. Inside the UNESCO-listed walled city.", "type": "Temple", "status": "UNESCO area"},
        {"name": "Here Be Dragons Exhibition, British Library", "lat": 51.5299, "lon": -0.1277, "location": "British Library, London", "country": "United Kingdom", "era": "Ongoing/rotating", "description": "Medieval maps with 'Hic Sunt Dracones' and dragon marginalia. The Hereford Mappa Mundi features numerous beasts.", "type": "Library/Maps", "status": "Collection"},
        {"name": "Dragon Parade, Metz", "lat": 49.1193, "lon": 6.1757, "location": "Metz, France", "country": "France", "era": "Annual", "description": "The Graoully dragon parade commemorates St. Clement taming a dragon and leading it to the river to drown.", "type": "Festival", "status": "City tradition"},
        {"name": "Year of the Dragon Temple, Taipei", "lat": 25.0375, "lon": 121.4997, "location": "Longshan Temple, Taipei", "country": "Taiwan", "era": "1738", "description": "Spectacular dragon carvings and dragon pillar columns. Especially vibrant during Lunar New Year Dragon years.", "type": "Temple", "status": "Heritage site"},
        {"name": "Game of Thrones Dragon Skull", "lat": 44.4268, "lon": 26.1025, "location": "Various filming locations", "country": "Multiple", "era": "2011-2019", "description": "GoT filming sites (Dubrovnik, Seville, Iceland) with dragon iconography. Boosted dragon tourism worldwide.", "type": "Pop culture", "status": "Tourism"},
        {"name": "Naga Fireball Festival", "lat": 17.8725, "lon": 102.7413, "location": "Phon Phisai, Nong Khai", "country": "Thailand", "era": "Annual October", "description": "Mysterious fireballs rise from the Mekong. Locals attribute them to the Naga. Thousands gather each year.", "type": "Festival", "status": "Annual event"},
        {"name": "Dragon Boat Races, Penang", "lat": 5.4141, "lon": 100.3288, "location": "Penang, Malaysia", "country": "Malaysia", "era": "Annual", "description": "International dragon boat racing festival combining Chinese dragon culture with competitive sport.", "type": "Festival", "status": "Annual event"},
        {"name": "Snapdragon Festival, Norwich", "lat": 52.6309, "lon": 1.2974, "location": "Norwich, England", "country": "United Kingdom", "era": "Modern revival", "description": "Norwich's dragon Snap once paraded through medieval streets. Revival festivals celebrate the city's dragon heritage.", "type": "Festival", "status": "Cultural revival"},
    ])


# ============================================================
# POPUP BUILDER
# ============================================================

def _build_popup(row, color, mode):
    """Build a rich HTML popup for a map marker."""
    name = html_module.escape(str(row.get("name", "")))
    location = html_module.escape(str(row.get("location", "")))
    country = html_module.escape(str(row.get("country", "")))
    era = html_module.escape(str(row.get("era", "")))
    desc = html_module.escape(str(row.get("description", "")))
    rtype = html_module.escape(str(row.get("type", "")))
    status = html_module.escape(str(row.get("status", "")))

    popup_html = f"""
    <div style="font-family:Arial,sans-serif;width:320px;padding:10px;background:#1a1a2e;color:#e8ecf4;border-radius:8px;border:1px solid {color};">
        <h4 style="margin:0 0 6px 0;color:{color};font-size:14px;">{name}</h4>
        <div style="font-size:11px;color:#8b97b0;margin-bottom:6px;">{location} &bull; {country}</div>
        <div style="font-size:11px;margin-bottom:4px;"><b style="color:{color};">Era:</b> {era}</div>
        <div style="font-size:11px;margin-bottom:4px;"><b style="color:{color};">Type:</b> {rtype}</div>
        <div style="font-size:11px;margin-bottom:4px;"><b style="color:{color};">Status:</b> {status}</div>
        <p style="font-size:11px;color:#c0c8d8;margin:6px 0 0 0;line-height:1.4;">{desc}</p>
    </div>
    """
    return popup_html


# ============================================================
# MAP BUILDER
# ============================================================

def _build_map(df, mode):
    """Build a folium map for a given mode and DataFrame."""
    color = CATEGORY_COLORS.get(mode, "#dc2626")
    icon_name = MARKER_ICONS.get(mode, "fire")

    m = folium.Map(
        location=[df["lat"].mean(), df["lon"].mean()],
        zoom_start=3,
        tiles="CartoDB dark_matter",
    )

    for _, row in df.iterrows():
        popup_html = _build_popup(row, color, mode)
        folium.Marker(
            location=[row["lat"], row["lon"]],
            popup=folium.Popup(popup_html, max_width=340),
            tooltip=str(row["name"]),
            icon=folium.Icon(color="red", icon=icon_name, prefix="fa" if icon_name not in ("tower", "certificate", "warning-sign") else "glyphicon"),
        ).add_to(m)

    return m


# ============================================================
# MODE -> DATA FUNCTION MAP
# ============================================================

MODE_DATA_FUNCS = {
    "European Dragon Legends": _european_dragons,
    "Chinese & Asian Dragons": _asian_dragons,
    "Sea Monster Sightings": _sea_monsters,
    "Unicorn & Griffin Lore": _unicorn_griffin,
    "Phoenix & Firebird Myths": _phoenix_firebird,
    "Werewolf & Vampire Legends": _werewolf_vampire,
    "Thunderbird & Native Spirits": _thunderbird_spirits,
    "Japanese Yokai & Demons": _japanese_yokai,
    "Celtic & Norse Beasts": _celtic_norse,
    "Dragon Museums & Festivals": _dragon_museums,
}

MODE_DESCRIPTIONS = {
    "European Dragon Legends": "Explore fire-breathing dragons, lindworms, wyverns, and serpent legends across Europe from ancient Greece to medieval England.",
    "Chinese & Asian Dragons": "Discover the benevolent lung dragons of China, nagas of Southeast Asia, Korean yong, and dragon deities across the continent.",
    "Sea Monster Sightings": "Chart legendary sea creatures from the Kraken and Leviathan to modern cryptid encounters and confirmed giant species.",
    "Unicorn & Griffin Lore": "Trace unicorn legends from Indus Valley seals to medieval tapestries, and griffin mythology from Persepolis to the Gobi Desert.",
    "Phoenix & Firebird Myths": "Map the global geography of rebirth-birds: the Egyptian Bennu, Chinese Fenghuang, Slavic Firebird, and sacred Garuda.",
    "Werewolf & Vampire Legends": "Track werewolf trials, vampire panics, and shapeshifter legends from medieval France to modern cryptid sightings.",
    "Thunderbird & Native Spirits": "Explore Indigenous American mythology: thunderbirds, feathered serpents, skinwalkers, trickster spirits, and sacred sites.",
    "Japanese Yokai & Demons": "Navigate Japan's supernatural bestiary: kitsune, tengu, kappa, oni, and hundreds of yokai from folklore and pop culture.",
    "Celtic & Norse Beasts": "Encounter kelpies, selkies, Fenrir, Nidhogg, banshees, and the Wild Hunt across the Celtic and Norse mythological landscape.",
    "Dragon Museums & Festivals": "Visit dragon museums, festivals, parades, and cultural sites where dragon traditions are preserved and celebrated.",
}


# ============================================================
# MAIN RENDER FUNCTION
# ============================================================

def render_dragon_maps_tab():
    """Render the Dragons & Mythical Beasts Explorer tab."""
    st.markdown(
        '<div class="tab-header red"><h4>🐉 Dragons & Mythical Beasts Explorer</h4>'
        '<p>Dragon legends, mythical creature sightings, folklore traditions & beast lore worldwide</p></div>',
        unsafe_allow_html=True,
    )

    mode = st.selectbox(
        "🐉 Select Map Mode",
        list(MODE_DATA_FUNCS.keys()),
        key="dragon_maps_mode",
    )

    # Description
    st.markdown(
        f'<div style="background:rgba(15,23,42,0.65);border:1px solid #2a3550;border-radius:8px;padding:12px;margin-bottom:12px;">'
        f'<span style="color:#8b97b0;font-size:13px;">{MODE_DESCRIPTIONS.get(mode, "")}</span></div>',
        unsafe_allow_html=True,
    )

    # Load data
    data_func = MODE_DATA_FUNCS[mode]
    df = data_func()

    # --- Filters ---
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    filtered_df = df.copy()

    if "country" in df.columns:
        countries = sorted(df["country"].unique().tolist())
        selected_countries = filter_col1.multiselect(
            "Filter by Country",
            options=countries,
            default=[],
            key=f"dragon_country_filter_{mode}",
        )
        if selected_countries:
            filtered_df = filtered_df[filtered_df["country"].isin(selected_countries)]

    if "type" in df.columns:
        types = sorted(df["type"].unique().tolist())
        selected_types = filter_col2.multiselect(
            "Filter by Type",
            options=types,
            default=[],
            key=f"dragon_type_filter_{mode}",
        )
        if selected_types:
            filtered_df = filtered_df[filtered_df["type"].isin(selected_types)]

    if "status" in df.columns:
        statuses = sorted(df["status"].unique().tolist())
        selected_statuses = filter_col3.multiselect(
            "Filter by Status",
            options=statuses,
            default=[],
            key=f"dragon_status_filter_{mode}",
        )
        if selected_statuses:
            filtered_df = filtered_df[filtered_df["status"].isin(selected_statuses)]

    # --- Metrics ---
    color = CATEGORY_COLORS.get(mode, "#dc2626")
    cols = st.columns(4)
    cols[0].metric("Total Locations", len(filtered_df))
    if "country" in filtered_df.columns:
        cols[1].metric("Countries", filtered_df["country"].nunique())
    if "type" in filtered_df.columns:
        cols[2].metric("Creature Types", filtered_df["type"].nunique())
    if "status" in filtered_df.columns:
        cols[3].metric("Status Categories", filtered_df["status"].nunique())

    # --- Secondary Metrics Row ---
    if len(filtered_df) > 0:
        met_col1, met_col2, met_col3, met_col4 = st.columns(4)
        lat_range = filtered_df["lat"].max() - filtered_df["lat"].min()
        lon_range = filtered_df["lon"].max() - filtered_df["lon"].min()
        met_col1.metric("Latitude Range", f"{lat_range:.1f}°")
        met_col2.metric("Longitude Range", f"{lon_range:.1f}°")
        if "era" in filtered_df.columns:
            met_col3.metric("Era Periods", filtered_df["era"].nunique())
        if "type" in filtered_df.columns:
            most_common_type = filtered_df["type"].value_counts().index[0] if len(filtered_df) > 0 else "N/A"
            met_col4.metric("Most Common Type", most_common_type)

    # --- Map ---
    if len(filtered_df) > 0:
        m = _build_map(filtered_df, mode)
        st_html(m._repr_html_(), height=500)
    else:
        st.warning("No locations match the current filters. Adjust your selections above.")

    # --- Breakdown by Type ---
    if "type" in filtered_df.columns and len(filtered_df) > 0:
        st.markdown(f"#### 📊 {mode} - Breakdown by Type")
        type_counts = filtered_df["type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        breakdown_cols = st.columns(2)
        with breakdown_cols[0]:
            st.dataframe(type_counts, use_container_width=True)
        with breakdown_cols[1]:
            # Build a simple horizontal bar using markdown
            max_count = type_counts["Count"].max() if len(type_counts) > 0 else 1
            bar_html = '<div style="background:rgba(15,23,42,0.65);border:1px solid #2a3550;border-radius:8px;padding:12px;">'
            for _, trow in type_counts.iterrows():
                pct = int((trow["Count"] / max_count) * 100)
                bar_html += (
                    f'<div style="margin-bottom:6px;">'
                    f'<span style="color:#e8ecf4;font-size:12px;">{html_module.escape(str(trow["Type"]))}</span>'
                    f'<div style="background:#1e293b;border-radius:4px;height:18px;margin-top:2px;">'
                    f'<div style="background:{color};width:{pct}%;height:18px;border-radius:4px;'
                    f'display:flex;align-items:center;padding-left:6px;">'
                    f'<span style="color:#fff;font-size:10px;font-weight:bold;">{trow["Count"]}</span>'
                    f'</div></div></div>'
                )
            bar_html += '</div>'
            st.markdown(bar_html, unsafe_allow_html=True)

    # --- Breakdown by Country ---
    if "country" in filtered_df.columns and len(filtered_df) > 0:
        st.markdown(f"#### 🌍 {mode} - Breakdown by Country")
        country_counts = filtered_df["country"].value_counts().reset_index()
        country_counts.columns = ["Country", "Count"]
        country_cols = st.columns(2)
        with country_cols[0]:
            st.dataframe(country_counts, use_container_width=True)
        with country_cols[1]:
            max_cc = country_counts["Count"].max() if len(country_counts) > 0 else 1
            cc_html = '<div style="background:rgba(15,23,42,0.65);border:1px solid #2a3550;border-radius:8px;padding:12px;">'
            for _, crow in country_counts.iterrows():
                pct = int((crow["Count"] / max_cc) * 100)
                cc_html += (
                    f'<div style="margin-bottom:6px;">'
                    f'<span style="color:#e8ecf4;font-size:12px;">{html_module.escape(str(crow["Country"]))}</span>'
                    f'<div style="background:#1e293b;border-radius:4px;height:18px;margin-top:2px;">'
                    f'<div style="background:{color};width:{pct}%;height:18px;border-radius:4px;'
                    f'display:flex;align-items:center;padding-left:6px;">'
                    f'<span style="color:#fff;font-size:10px;font-weight:bold;">{crow["Count"]}</span>'
                    f'</div></div></div>'
                )
            cc_html += '</div>'
            st.markdown(cc_html, unsafe_allow_html=True)

    # --- Breakdown by Status ---
    if "status" in filtered_df.columns and len(filtered_df) > 0:
        st.markdown(f"#### 🏷️ {mode} - Breakdown by Status")
        status_counts = filtered_df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        st.dataframe(status_counts, use_container_width=True)

    # --- Breakdown by Era ---
    if "era" in filtered_df.columns and len(filtered_df) > 0:
        st.markdown(f"#### ⏳ {mode} - Breakdown by Era")
        era_counts = filtered_df["era"].value_counts().reset_index()
        era_counts.columns = ["Era", "Count"]
        st.dataframe(era_counts, use_container_width=True)

    # --- Location Details Expander ---
    if len(filtered_df) > 0:
        st.markdown(f"#### 🔍 {mode} - Location Details")
        for idx, row in filtered_df.iterrows():
            with st.expander(f"{row['name']} — {row.get('location', 'Unknown')}"):
                detail_cols = st.columns(3)
                detail_cols[0].markdown(f"**Country:** {row.get('country', 'N/A')}")
                detail_cols[1].markdown(f"**Type:** {row.get('type', 'N/A')}")
                detail_cols[2].markdown(f"**Era:** {row.get('era', 'N/A')}")
                st.markdown(f"**Status:** {row.get('status', 'N/A')}")
                st.markdown(f"**Coordinates:** {row['lat']:.4f}, {row['lon']:.4f}")
                st.markdown(f"**Description:** {row.get('description', 'N/A')}")

    # --- Full Data Table ---
    st.markdown(f"#### 📋 {mode} - Full Data Table")
    st.dataframe(filtered_df, use_container_width=True)

    # --- CSV Download ---
    csv_buffer = io.StringIO()
    filtered_df.to_csv(csv_buffer, index=False)
    st.download_button(
        label=f"📥 Download {mode} CSV",
        data=csv_buffer.getvalue(),
        file_name=f"dragon_maps_{mode.lower().replace(' ', '_').replace('&', 'and')}.csv",
        mime="text/csv",
        key=f"dragon_dl_{mode}",
    )

    # --- Cross-Mode Overview ---
    with st.expander("🐉 Cross-Mode Overview - All Categories Summary"):
        overview_rows = []
        for m_name, m_func in MODE_DATA_FUNCS.items():
            m_df = m_func()
            overview_rows.append({
                "Category": m_name,
                "Locations": len(m_df),
                "Countries": m_df["country"].nunique() if "country" in m_df.columns else 0,
                "Types": m_df["type"].nunique() if "type" in m_df.columns else 0,
                "Statuses": m_df["status"].nunique() if "status" in m_df.columns else 0,
            })
        overview_df = pd.DataFrame(overview_rows)
        st.dataframe(overview_df, use_container_width=True)

        total_locations = overview_df["Locations"].sum()
        total_countries = sum(
            m_func()["country"].nunique()
            for m_func in MODE_DATA_FUNCS.values()
            if "country" in m_func().columns
        )
        st.markdown(
            f'<div style="background:rgba(15,23,42,0.65);border:1px solid #dc2626;border-radius:8px;'
            f'padding:12px;text-align:center;">'
            f'<span style="color:#dc2626;font-size:16px;font-weight:bold;">'
            f'Total Database: {total_locations} Mythical Locations</span><br>'
            f'<span style="color:#8b97b0;font-size:12px;">'
            f'Across 10 categories spanning every inhabited continent</span></div>',
            unsafe_allow_html=True,
        )

    # --- Nearby Locations Finder ---
    with st.expander("📍 Find Nearby Mythical Locations"):
        near_cols = st.columns(2)
        search_lat = near_cols[0].number_input(
            "Latitude", value=48.8566, min_value=-90.0, max_value=90.0,
            step=0.1, key="dragon_near_lat",
        )
        search_lon = near_cols[1].number_input(
            "Longitude", value=2.3522, min_value=-180.0, max_value=180.0,
            step=0.1, key="dragon_near_lon",
        )
        search_radius = st.slider(
            "Search Radius (degrees)", min_value=1.0, max_value=50.0,
            value=10.0, step=1.0, key="dragon_near_radius",
        )

        if st.button("🔍 Search Nearby", key="dragon_near_btn"):
            nearby_results = []
            for m_name, m_func in MODE_DATA_FUNCS.items():
                m_df = m_func()
                for _, nrow in m_df.iterrows():
                    dist = ((nrow["lat"] - search_lat) ** 2 + (nrow["lon"] - search_lon) ** 2) ** 0.5
                    if dist <= search_radius:
                        nearby_results.append({
                            "Name": nrow["name"],
                            "Category": m_name,
                            "Location": nrow.get("location", ""),
                            "Country": nrow.get("country", ""),
                            "Distance (deg)": round(dist, 2),
                            "Lat": nrow["lat"],
                            "Lon": nrow["lon"],
                        })

            if nearby_results:
                nearby_df = pd.DataFrame(nearby_results).sort_values("Distance (deg)")
                st.metric("Nearby Locations Found", len(nearby_df))
                st.dataframe(nearby_df, use_container_width=True)
            else:
                st.info("No mythical locations found within the specified radius. Try increasing the search radius.")

    # --- Summary Footer ---
    st.markdown(
        f'<div style="background:rgba(15,23,42,0.65);border:1px solid {color};border-radius:8px;'
        f'padding:12px;margin-top:16px;text-align:center;">'
        f'<span style="color:{color};font-size:14px;font-weight:bold;">🐉 {mode}</span><br>'
        f'<span style="color:#8b97b0;font-size:12px;">'
        f'{len(filtered_df)} locations across {filtered_df["country"].nunique() if "country" in filtered_df.columns else "N/A"} countries'
        f' &bull; {filtered_df["type"].nunique() if "type" in filtered_df.columns else "N/A"} creature types'
        f' &bull; Data curated from historical records, folklore databases, and mythological texts</span></div>',
        unsafe_allow_html=True,
    )
