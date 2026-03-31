"""
Masks & Ceremonial Art Explorer module for TerraScout AI.
Displays curated maps of mask traditions worldwide, from Venetian carnival masks
to African ceremonial masks, Japanese Noh theater, Day of the Dead, Native American
traditions, Asian temple masks, global carnivals, shamanic rituals, ancient death
masks, and major mask museum collections on interactive dark-theme Folium maps.
"""

import io
import streamlit as st
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import html as html_module
from streamlit.components.v1 import html as st_html


# ═══════════════════════════════════════════
# MODE DEFINITIONS
# ═══════════════════════════════════════════
MODE_OPTIONS = [
    "Venetian Masks",
    "African Masks",
    "Japanese Noh & Kabuki Masks",
    "Day of the Dead Masks",
    "Native American Masks",
    "Asian Temple Masks",
    "Carnival Masks Worldwide",
    "Shamanic & Ritual Masks",
    "Ancient Masks",
    "Mask Museums & Collections",
]

# ═══════════════════════════════════════════
# PRESET DATA PER MODE
# ═══════════════════════════════════════════

VENETIAN_MASKS = [
    {"name": "Ca' Macana Mask Workshop", "lat": 45.4338, "lon": 12.3260,
     "desc": "Renowned artisan mask workshop in Dorsoduro, crafting bauta, moretta, and volto masks since 1984.",
     "region": "Dorsoduro, Venice", "mask_type": "Bauta, Volto, Moretta", "color": "#8b5cf6"},
    {"name": "Tragicomica Mask Atelier", "lat": 45.4375, "lon": 12.3305,
     "desc": "Historic workshop near San Polo creating commedia dell'arte and carnival masks by hand.",
     "region": "San Polo, Venice", "mask_type": "Commedia dell'Arte", "color": "#a855f7"},
    {"name": "Piazza San Marco Carnival Stage", "lat": 45.4343, "lon": 12.3388,
     "desc": "Main stage for Venice Carnival's Flight of the Angel and Best Mask competition.",
     "region": "San Marco, Venice", "mask_type": "All Venetian Types", "color": "#f59e0b"},
    {"name": "Ca' del Sol Mask Studio", "lat": 45.4403, "lon": 12.3265,
     "desc": "Family-run mask studio specializing in papier-mache Plague Doctor and Pantalone masks.",
     "region": "Cannaregio, Venice", "mask_type": "Plague Doctor", "color": "#10b981"},
    {"name": "Museo del Merletto (Burano)", "lat": 45.4856, "lon": 12.4166,
     "desc": "Burano lace museum that also exhibits traditional carnival masks alongside lacework.",
     "region": "Burano, Venice", "mask_type": "Traditional Venetian", "color": "#06b6d4"},
    {"name": "Teatro La Fenice", "lat": 45.4338, "lon": 12.3336,
     "desc": "Historic opera house hosting masked balls and carnival performances since 1792.",
     "region": "San Marco, Venice", "mask_type": "Volto, Bauta", "color": "#ec4899"},
    {"name": "Atelier Marega", "lat": 45.4352, "lon": 12.3362,
     "desc": "Master craftsman workshop creating gold-leaf and Swarovski-encrusted Venetian masks.",
     "region": "San Marco, Venice", "mask_type": "Luxury Volto", "color": "#f97316"},
    {"name": "Fondazione Musei Civici - Ca' Rezzonico", "lat": 45.4333, "lon": 12.3269,
     "desc": "18th-century Venetian art museum with carnival-era paintings depicting masked revelers.",
     "region": "Dorsoduro, Venice", "mask_type": "Historical Bauta", "color": "#ef4444"},
    {"name": "Laboratorio Artigiano Maschere", "lat": 45.4371, "lon": 12.3397,
     "desc": "Traditional workshop near Rialto Bridge teaching visitors to craft their own Venetian masks.",
     "region": "Rialto, Venice", "mask_type": "Colombina, Zanni", "color": "#14b8a6"},
    {"name": "Carnival Parade Route - Via Garibaldi", "lat": 45.4308, "lon": 12.3513,
     "desc": "Traditional parade route in Castello district for Venice Carnival's grand water procession.",
     "region": "Castello, Venice", "mask_type": "Carnival Procession", "color": "#d946ef"},
    {"name": "Mondo Novo Maschere", "lat": 45.4335, "lon": 12.3278,
     "desc": "Art studio run by sculptor Guerrino Lovato, known for surrealist mask designs.",
     "region": "Dorsoduro, Venice", "mask_type": "Art Masks", "color": "#38bdf8"},
    {"name": "Mask Museum of Venice (Museo delle Maschere)", "lat": 45.4360, "lon": 12.3350,
     "desc": "Small museum dedicated to the history and craft of Venetian mask-making traditions.",
     "region": "San Polo, Venice", "mask_type": "All Types", "color": "#fbbf24"},
    {"name": "Papier Mache Workshop - Giudecca", "lat": 45.4264, "lon": 12.3285,
     "desc": "Island workshop producing large-scale papier-mache carnival masks and theatrical props.",
     "region": "Giudecca, Venice", "mask_type": "Theatrical Props", "color": "#3b82f6"},
    {"name": "Venice Carnival Opening Ceremony", "lat": 45.4295, "lon": 12.3202,
     "desc": "San Nicolo pier where the carnival officially opens with a masked water parade.",
     "region": "Lido, Venice", "mask_type": "Ceremonial", "color": "#22c55e"},
    {"name": "Museo Correr - Carnival Gallery", "lat": 45.4337, "lon": 12.3374,
     "desc": "Civic museum in Piazza San Marco with an extensive collection of 18th-century carnival artifacts.",
     "region": "San Marco, Venice", "mask_type": "Historical Collection", "color": "#64748b"},
    {"name": "Bottega dei Mascareri", "lat": 45.4367, "lon": 12.3360,
     "desc": "Traditional mask shop at the foot of Rialto Bridge, operated by the Boldrin brothers.",
     "region": "San Polo, Venice", "mask_type": "Bauta, Moretta", "color": "#e879f9"},
    {"name": "Commedia dell'Arte Square (Campo San Barnaba)", "lat": 45.4327, "lon": 12.3263,
     "desc": "Historic square associated with street performances of commedia dell'arte masked theater.",
     "region": "Dorsoduro, Venice", "mask_type": "Harlequin, Pantalone", "color": "#fb923c"},
    {"name": "Mascheranda Atelier", "lat": 45.4350, "lon": 12.3295,
     "desc": "Contemporary mask studio blending traditional techniques with modern art installations.",
     "region": "Dorsoduro, Venice", "mask_type": "Contemporary Art Masks", "color": "#c084fc"},
    {"name": "San Zaccaria Church Carnival Gathering", "lat": 45.4346, "lon": 12.3433,
     "desc": "Historic church square where nuns once held legendary masked carnival celebrations.",
     "region": "Castello, Venice", "mask_type": "Historical Venetian", "color": "#4ade80"},
    {"name": "Carnival Boat Parade - Grand Canal", "lat": 45.4377, "lon": 12.3321,
     "desc": "Grand Canal route for the annual masked boat parade during Venice Carnival's opening.",
     "region": "Grand Canal, Venice", "mask_type": "Water Procession", "color": "#facc15"},
    {"name": "Palazzo Pisani Moretta - Masked Ball", "lat": 45.4358, "lon": 12.3289,
     "desc": "15th-century Gothic palace hosting the legendary Ballo del Doge masked ball during carnival.",
     "region": "San Polo, Venice", "mask_type": "Gala Volto", "color": "#818cf8"},
    {"name": "Museo di Palazzo Mocenigo", "lat": 45.4381, "lon": 12.3268,
     "desc": "Textile and costume museum with historic carnival costume and mask exhibitions.",
     "region": "Santa Croce, Venice", "mask_type": "Costume & Mask History", "color": "#f472b6"},
    {"name": "Bauta Mask Heritage Walk - Cannaregio", "lat": 45.4434, "lon": 12.3312,
     "desc": "Walking route through Cannaregio showcasing historic bauta mask tradition locations.",
     "region": "Cannaregio, Venice", "mask_type": "Bauta Heritage", "color": "#34d399"},
    {"name": "Venetian Mask Restoration Lab", "lat": 45.4319, "lon": 12.3340,
     "desc": "Conservation laboratory specializing in restoring antique 18th-century Venetian masks.",
     "region": "San Marco, Venice", "mask_type": "Antique Restoration", "color": "#a78bfa"},
    {"name": "Arsenal of Venice - Carnival Fireworks", "lat": 45.4348, "lon": 12.3538,
     "desc": "Historic naval shipyard serving as the backdrop for Venice Carnival's spectacular finale fireworks.",
     "region": "Castello, Venice", "mask_type": "Carnival Finale", "color": "#fb7185"},
    {"name": "Moretta Mask Workshop - Murano", "lat": 45.4575, "lon": 12.3545,
     "desc": "Murano glass island workshop creating unique moretta masks with glass bead embellishments.",
     "region": "Murano, Venice", "mask_type": "Moretta with Glass", "color": "#2dd4bf"},
]

AFRICAN_MASKS = [
    {"name": "Dogon Cliff Villages - Bandiagara", "lat": 14.3475, "lon": -3.5840,
     "desc": "UNESCO site where Kanaga and Sirige masks are used in sacred Dama funerary ceremonies.",
     "region": "Bandiagara, Mali", "tradition": "Dogon Dama", "color": "#f59e0b"},
    {"name": "Fang Mask Tradition - Libreville", "lat": 0.3924, "lon": 9.4536,
     "desc": "Fang people's ngil masks used by secret society judges in spiritual ceremonies.",
     "region": "Libreville, Gabon", "tradition": "Fang Ngil", "color": "#8b5cf6"},
    {"name": "Dan Mask Workshops - Man", "lat": 7.4013, "lon": -7.5500,
     "desc": "Dan people's gle masks used in initiation, entertainment, and judgment ceremonies.",
     "region": "Man, Ivory Coast", "tradition": "Dan Gle", "color": "#10b981"},
    {"name": "Punu White Mask Center - Mouila", "lat": -1.8667, "lon": 11.0500,
     "desc": "Punu people's iconic white Okuyi masks representing idealized female ancestors.",
     "region": "Mouila, Gabon", "tradition": "Punu Okuyi", "color": "#ef4444"},
    {"name": "Chokwe Mask Heritage - Saurimo", "lat": -9.6605, "lon": 20.3928,
     "desc": "Chokwe chieftaincy masks including the powerful Mwana Pwo and Cihongo masks.",
     "region": "Saurimo, Angola", "tradition": "Chokwe Royal", "color": "#ec4899"},
    {"name": "Makonde Mask Carvers - Mueda", "lat": -11.6667, "lon": 39.5167,
     "desc": "Makonde sculptors creating mapiko helmet masks for initiation dances.",
     "region": "Mueda, Mozambique", "tradition": "Makonde Mapiko", "color": "#06b6d4"},
    {"name": "FESTIMA Mask Festival - Dedougou", "lat": 12.4600, "lon": -3.4600,
     "desc": "International Festival of Masks and Arts bringing together mask traditions from across Africa.",
     "region": "Dedougou, Burkina Faso", "tradition": "Pan-African Festival", "color": "#a855f7"},
    {"name": "Bamana Mask Society - Bamako", "lat": 12.6392, "lon": -8.0029,
     "desc": "Bamana people's Chi Wara antelope headdresses used in agricultural ceremonies.",
     "region": "Bamako, Mali", "tradition": "Bamana Chi Wara", "color": "#f97316"},
    {"name": "Kuba Kingdom Masks - Mushenge", "lat": -4.3333, "lon": 21.5167,
     "desc": "Elaborate Kuba royal masks including Bwoom, Ngady Mwaash, and Mwaash a Mboy.",
     "region": "Mushenge, DR Congo", "tradition": "Kuba Royal", "color": "#d946ef"},
    {"name": "Yoruba Gelede Masks - Ile-Ife", "lat": 7.4820, "lon": 4.5624,
     "desc": "UNESCO-recognized Gelede masquerade honoring the spiritual power of women.",
     "region": "Ile-Ife, Nigeria", "tradition": "Yoruba Gelede", "color": "#14b8a6"},
    {"name": "Gule Wamkulu - Lilongwe", "lat": -13.9626, "lon": 33.7741,
     "desc": "Chewa people's Great Dance ritual with masks representing spirits of the dead.",
     "region": "Lilongwe, Malawi", "tradition": "Chewa Nyau", "color": "#38bdf8"},
    {"name": "Bamileke Elephant Masks - Dschang", "lat": 5.4500, "lon": 10.0500,
     "desc": "Royal elephant masks of the Bamileke kingdom used in ceremonial dances.",
     "region": "Dschang, Cameroon", "tradition": "Bamileke Royal", "color": "#fbbf24"},
    {"name": "Senufo Mask Workshops - Korhogo", "lat": 9.4540, "lon": -5.6337,
     "desc": "Senufo Poro society masks used in initiation and funeral ceremonies.",
     "region": "Korhogo, Ivory Coast", "tradition": "Senufo Poro", "color": "#22c55e"},
    {"name": "Luba Kifwebe Masks - Lubumbashi", "lat": -11.6604, "lon": 27.4794,
     "desc": "Striking striped Kifwebe masks of the Luba people used by the Bwadi bwa Kifwebe society.",
     "region": "Lubumbashi, DR Congo", "tradition": "Luba Kifwebe", "color": "#e879f9"},
    {"name": "Igbo Maiden Spirit Masks - Enugu", "lat": 6.4584, "lon": 7.5464,
     "desc": "Igbo agbogho mmuo masks depicting idealized maiden spirits in masquerade performances.",
     "region": "Enugu, Nigeria", "tradition": "Igbo Agbogho Mmuo", "color": "#fb923c"},
    {"name": "Bobo Mask Ceremonies - Bobo-Dioulasso", "lat": 11.1771, "lon": -4.2979,
     "desc": "Bobo people's leaf and fiber masks representing spirits of nature and the bush.",
     "region": "Bobo-Dioulasso, Burkina Faso", "tradition": "Bobo Nature Spirits", "color": "#c084fc"},
    {"name": "Lega Bwami Society - Kindu", "lat": -2.9500, "lon": 25.9167,
     "desc": "Small ivory and wood masks used as insignia in the Lega Bwami initiation society.",
     "region": "Kindu, DR Congo", "tradition": "Lega Bwami", "color": "#4ade80"},
    {"name": "Egungun Masquerade - Oyo", "lat": 7.8504, "lon": 3.9342,
     "desc": "Yoruba ancestral spirit masquerade with elaborate layered cloth masks and costumes.",
     "region": "Oyo, Nigeria", "tradition": "Yoruba Egungun", "color": "#facc15"},
    {"name": "Bembe Mask Rituals - Fizi", "lat": -4.3167, "lon": 28.9333,
     "desc": "Bembe people's alunga masks used in rituals for social harmony and conflict resolution.",
     "region": "Fizi, DR Congo", "tradition": "Bembe Alunga", "color": "#818cf8"},
    {"name": "National Museum of African Art - Nairobi", "lat": -1.2921, "lon": 36.8219,
     "desc": "Major East African museum with collections of masks from across the continent.",
     "region": "Nairobi, Kenya", "tradition": "Pan-African Collection", "color": "#f472b6"},
    {"name": "Zulu Beaded Masks - Durban", "lat": -29.8587, "lon": 31.0218,
     "desc": "Zulu artisans creating intricate beaded masks reflecting clan identity and spiritual beliefs.",
     "region": "Durban, South Africa", "tradition": "Zulu Beadwork", "color": "#34d399"},
    {"name": "Baule Portrait Masks - Bouake", "lat": 7.6900, "lon": -5.0300,
     "desc": "Refined portrait masks representing spirit spouses (blolo bla/bian) in Baule tradition.",
     "region": "Bouake, Ivory Coast", "tradition": "Baule Portrait", "color": "#a78bfa"},
    {"name": "Kongo Nkisi Power Figures - Matadi", "lat": -5.8263, "lon": 13.4533,
     "desc": "Nail-studded power figures and masks used by Kongo ritual specialists.",
     "region": "Matadi, DR Congo", "tradition": "Kongo Nkisi", "color": "#fb7185"},
    {"name": "Maasai Ceremonial Adornment - Arusha", "lat": -3.3869, "lon": 36.6830,
     "desc": "Maasai warrior and ceremonial face painting and beaded head ornaments for rituals.",
     "region": "Arusha, Tanzania", "tradition": "Maasai Adornment", "color": "#2dd4bf"},
    {"name": "Pende Mbuya Masks - Gungu", "lat": -5.2500, "lon": 19.2833,
     "desc": "Pende people's mbuya masks representing village characters in masked theater.",
     "region": "Gungu, DR Congo", "tradition": "Pende Mbuya", "color": "#64748b"},
    {"name": "Tiv Kwagh-hir Puppet Masks - Makurdi", "lat": 7.7411, "lon": 8.5122,
     "desc": "Tiv people's puppet theater with carved masks telling stories of spirits and animals.",
     "region": "Makurdi, Nigeria", "tradition": "Tiv Kwagh-hir", "color": "#84cc16"},
]

JAPANESE_NOH_KABUKI = [
    {"name": "Kanze Noh Theater - Kyoto", "lat": 35.0054, "lon": 135.7717,
     "desc": "One of the five Kanze school Noh stages where Ko-omote and Hannya masks are performed.",
     "region": "Kyoto, Japan", "mask_type": "Ko-omote, Hannya", "color": "#ef4444"},
    {"name": "National Noh Theatre - Tokyo", "lat": 35.6857, "lon": 139.7143,
     "desc": "Japan's premier Noh theater in Shibuya, showcasing all five schools of Noh mask performance.",
     "region": "Sendagaya, Tokyo", "mask_type": "All Noh Types", "color": "#8b5cf6"},
    {"name": "Kongou Noh Stage - Kyoto", "lat": 35.0173, "lon": 135.7579,
     "desc": "Historic Kongou school theater founded in 1848 with an ancient hinoki cypress stage.",
     "region": "Kyoto, Japan", "mask_type": "Okina, Tengu", "color": "#06b6d4"},
    {"name": "Kabuki-za Theatre - Tokyo", "lat": 35.6695, "lon": 139.7678,
     "desc": "Iconic Ginza kabuki theater where kumadori face painting and demon masks are showcased.",
     "region": "Ginza, Tokyo", "mask_type": "Kumadori, Oni", "color": "#f59e0b"},
    {"name": "Noh Mask Museum - Kamakura", "lat": 35.3192, "lon": 139.5466,
     "desc": "Private museum displaying over 200 antique Noh masks from the Muromachi period onward.",
     "region": "Kamakura, Japan", "mask_type": "Antique Collection", "color": "#ec4899"},
    {"name": "Itsukushima Noh Stage - Miyajima", "lat": 34.2955, "lon": 132.3196,
     "desc": "UNESCO floating Noh stage at Itsukushima Shrine, performing on water during high tide.",
     "region": "Miyajima, Hiroshima", "mask_type": "Sacred Noh", "color": "#10b981"},
    {"name": "Osaka Noh Hall (Otsuki Noh)", "lat": 34.6937, "lon": 135.5023,
     "desc": "Major Noh performance hall in Osaka featuring regular performances of masked drama.",
     "region": "Osaka, Japan", "mask_type": "Noh Performance", "color": "#f97316"},
    {"name": "Noh Mask Carver Studio - Nara", "lat": 34.6851, "lon": 135.8048,
     "desc": "Traditional mask carver (menzuchi) workshop preserving centuries-old carving techniques.",
     "region": "Nara, Japan", "mask_type": "Handcarved Noh", "color": "#a855f7"},
    {"name": "Minamiza Kabuki Theatre - Kyoto", "lat": 35.0038, "lon": 135.7709,
     "desc": "Oldest kabuki theater in Japan, dating back to 1610, in the Shijo Gion district.",
     "region": "Gion, Kyoto", "mask_type": "Kabuki Performance", "color": "#d946ef"},
    {"name": "Chusonji Temple Noh Stage - Hiraizumi", "lat": 38.9880, "lon": 141.1030,
     "desc": "UNESCO World Heritage temple with outdoor Noh stage surrounded by ancient cedars.",
     "region": "Hiraizumi, Iwate", "mask_type": "Temple Noh", "color": "#14b8a6"},
    {"name": "Yokohama Noh Theater", "lat": 35.4437, "lon": 139.6380,
     "desc": "Modern Noh theater with educational programs on mask-making and performance traditions.",
     "region": "Yokohama, Japan", "mask_type": "Educational Noh", "color": "#38bdf8"},
    {"name": "Tengu Shrine - Mount Takao", "lat": 35.6252, "lon": 139.2436,
     "desc": "Mountain shrine dedicated to Tengu spirits with large Tengu mask displayed at the gate.",
     "region": "Hachioji, Tokyo", "mask_type": "Tengu", "color": "#fbbf24"},
    {"name": "Kagura Mask Performance - Izumo", "lat": 35.3569, "lon": 132.7595,
     "desc": "Sacred Kagura dance performances using Shinto deity masks at Izumo Grand Shrine.",
     "region": "Izumo, Shimane", "mask_type": "Kagura Sacred", "color": "#22c55e"},
    {"name": "Nagoya Noh Theater", "lat": 35.1815, "lon": 136.9066,
     "desc": "City-run Noh theater offering regular performances and mask exhibition galleries.",
     "region": "Nagoya, Aichi", "mask_type": "Noh Gallery", "color": "#e879f9"},
    {"name": "Hyottoko & Okame Festival - Nobeoka", "lat": 32.5834, "lon": 131.6625,
     "desc": "Annual festival where thousands wear comic Hyottoko and Okame folk masks in a grand parade.",
     "region": "Nobeoka, Miyazaki", "mask_type": "Hyottoko, Okame", "color": "#fb923c"},
    {"name": "Bugaku Mask Court Dance - Imperial Palace", "lat": 35.6852, "lon": 139.7528,
     "desc": "Ancient court dance tradition with elaborate masks performed at the Imperial Palace.",
     "region": "Chiyoda, Tokyo", "mask_type": "Bugaku Court", "color": "#c084fc"},
    {"name": "Awaji Puppet Theater", "lat": 34.2789, "lon": 134.8908,
     "desc": "Traditional Awaji ningyo joruri puppet theater with carved puppet head masks.",
     "region": "Awaji Island, Hyogo", "mask_type": "Puppet Masks", "color": "#4ade80"},
    {"name": "Menuma Shodenzan Kangi-in Temple", "lat": 36.2333, "lon": 139.3833,
     "desc": "Temple famous for its collection of ornate Noh and Bugaku masks as cultural treasures.",
     "region": "Kumagaya, Saitama", "mask_type": "Temple Collection", "color": "#facc15"},
    {"name": "Kita Noh School - Tokyo", "lat": 35.7049, "lon": 139.7242,
     "desc": "Intimate Noh theater of the Kita school known for dynamic performance style.",
     "region": "Meguro, Tokyo", "mask_type": "Kita School Noh", "color": "#818cf8"},
    {"name": "Namahage Mask Festival - Oga Peninsula", "lat": 39.9387, "lon": 139.8474,
     "desc": "UNESCO intangible heritage where demon-masked figures visit homes on New Year's Eve.",
     "region": "Oga, Akita", "mask_type": "Namahage Oni", "color": "#f472b6"},
    {"name": "Noh & Kyogen Museum - Kanazawa", "lat": 36.5613, "lon": 136.6562,
     "desc": "Museum in Kanazawa dedicated to Noh and comic Kyogen mask traditions of Kaga domain.",
     "region": "Kanazawa, Ishikawa", "mask_type": "Noh & Kyogen", "color": "#34d399"},
    {"name": "Toshogu Shrine Mask Dance - Nikko", "lat": 36.7580, "lon": 139.5994,
     "desc": "Spring and autumn festivals at Toshogu Shrine featuring sacred mask dances and processions.",
     "region": "Nikko, Tochigi", "mask_type": "Shrine Festival", "color": "#a78bfa"},
    {"name": "Oni Museum - Fukuchiyama", "lat": 35.2960, "lon": 135.1266,
     "desc": "Japan's only museum dedicated to oni (demon) masks and folklore from across the country.",
     "region": "Fukuchiyama, Kyoto", "mask_type": "Oni Demon", "color": "#fb7185"},
    {"name": "Shimokitazawa Mask Shop District", "lat": 35.6612, "lon": 139.6682,
     "desc": "Bohemian neighborhood with specialty shops selling vintage Noh and festival masks.",
     "region": "Setagaya, Tokyo", "mask_type": "Vintage Masks", "color": "#2dd4bf"},
    {"name": "Kasuga Grand Shrine - Nara", "lat": 34.6810, "lon": 135.8499,
     "desc": "Ancient Shinto shrine hosting on-no-matsuri festival with Bugaku masked dance performances.",
     "region": "Nara, Japan", "mask_type": "Bugaku Festival", "color": "#64748b"},
    {"name": "Chichibu Night Festival", "lat": 35.9914, "lon": 139.0858,
     "desc": "UNESCO night festival with illuminated floats and masked performers in Saitama Prefecture.",
     "region": "Chichibu, Saitama", "mask_type": "Festival Float Masks", "color": "#84cc16"},
]

DAY_OF_THE_DEAD = [
    {"name": "Oaxaca City - Day of the Dead Capital", "lat": 17.0732, "lon": -96.7266,
     "desc": "Mexico's spiritual center for Dia de los Muertos with elaborate cemetery vigils, comparsas, and calavera masks.",
     "region": "Oaxaca, Mexico", "tradition": "Oaxacan Calavera", "color": "#ec4899"},
    {"name": "Mixquic Cemetery Vigil", "lat": 19.2369, "lon": -99.0078,
     "desc": "Ancient island village where families hold all-night vigils with candlelit graves and skull masks.",
     "region": "Tlahuac, Mexico City", "tradition": "Cemetery Vigil", "color": "#f59e0b"},
    {"name": "Patzcuaro - Janitzio Island", "lat": 19.5689, "lon": -101.6094,
     "desc": "Purepecha indigenous community performing butterfly net fishermen ceremonies and masked dances.",
     "region": "Patzcuaro, Michoacan", "tradition": "Purepecha Ritual", "color": "#8b5cf6"},
    {"name": "Mexico City - Mega Desfile de Muertos", "lat": 19.4326, "lon": -99.1332,
     "desc": "Massive Day of the Dead parade along Paseo de la Reforma with giant calavera floats.",
     "region": "Mexico City, Mexico", "tradition": "Mega Parade", "color": "#a855f7"},
    {"name": "San Andres Mixquic Altar Tradition", "lat": 19.2392, "lon": -99.0100,
     "desc": "Village famous for community ofrendas (altars) and paper-mache skeleton masks.",
     "region": "Mixquic, Mexico", "tradition": "Ofrenda Altars", "color": "#ef4444"},
    {"name": "Aguascalientes Calavera Festival", "lat": 21.8818, "lon": -102.2916,
     "desc": "Festival honoring Jose Guadalupe Posada, creator of the iconic La Catrina skull image.",
     "region": "Aguascalientes, Mexico", "tradition": "Catrina Festival", "color": "#06b6d4"},
    {"name": "San Miguel de Allende - La Calaca Festival", "lat": 20.9142, "lon": -100.7447,
     "desc": "Colonial town celebration with skull painting workshops and masked processions.",
     "region": "Guanajuato, Mexico", "tradition": "Calaca Parade", "color": "#10b981"},
    {"name": "Pomuch Bone Cleaning Ritual", "lat": 20.1167, "lon": -90.1167,
     "desc": "Unique Mayan tradition where families clean the bones of deceased relatives and decorate them.",
     "region": "Pomuch, Campeche", "tradition": "Mayan Bone Ritual", "color": "#d946ef"},
    {"name": "Xantolo Festival - Huasteca Region", "lat": 21.1438, "lon": -98.4150,
     "desc": "Huastec Nahua celebration with old man masks (viejitos) and ceremonial dances for the dead.",
     "region": "Huasteca, San Luis Potosi", "tradition": "Xantolo Viejitos", "color": "#f97316"},
    {"name": "Tzintzuntzan Cemetery - Lake Patzcuaro", "lat": 19.6278, "lon": -101.5750,
     "desc": "Ancient Purepecha capital with atmospheric cemetery vigils overlooking the lake.",
     "region": "Tzintzuntzan, Michoacan", "tradition": "Purepecha Vigil", "color": "#14b8a6"},
    {"name": "Museo Nacional de la Muerte", "lat": 21.8824, "lon": -102.2952,
     "desc": "National Museum of Death with extensive collection of death masks and funeral art.",
     "region": "Aguascalientes, Mexico", "tradition": "Museum Collection", "color": "#38bdf8"},
    {"name": "Hollywood Forever Cemetery - LA", "lat": 34.0899, "lon": -118.3191,
     "desc": "Largest US Day of the Dead celebration with tens of thousands of masked attendees.",
     "region": "Los Angeles, USA", "tradition": "US Dia de Muertos", "color": "#fbbf24"},
    {"name": "Tlaquepaque Artisan Mask Workshops", "lat": 20.6413, "lon": -103.3132,
     "desc": "Artisan village near Guadalajara famous for handcrafted calaca and calavera masks.",
     "region": "Tlaquepaque, Jalisco", "tradition": "Artisan Calaveras", "color": "#22c55e"},
    {"name": "Chiapa de Corzo - Parachicos Festival", "lat": 16.7078, "lon": -93.0153,
     "desc": "UNESCO festival with carved wooden masks and colorful costumes honoring the town's patroness.",
     "region": "Chiapas, Mexico", "tradition": "Parachicos", "color": "#e879f9"},
    {"name": "San Juan Chamula Mask Ceremonies", "lat": 16.7894, "lon": -92.6897,
     "desc": "Tzotzil Maya community with syncretic mask ceremonies blending indigenous and Catholic traditions.",
     "region": "Chiapas, Mexico", "tradition": "Tzotzil Maya", "color": "#fb923c"},
    {"name": "Morelia Catrina Festival", "lat": 19.7060, "lon": -101.1950,
     "desc": "Colonial city celebration with monumental Catrina installations and face painting.",
     "region": "Morelia, Michoacan", "tradition": "Catrina Art", "color": "#c084fc"},
    {"name": "Puebla Cemetery Celebrations", "lat": 19.0414, "lon": -98.2063,
     "desc": "Elaborate cemetery celebrations with marigold paths, music, and decorated sugar skulls.",
     "region": "Puebla, Mexico", "tradition": "Sugar Skull", "color": "#4ade80"},
    {"name": "Museo Dolores Olmedo - Xochimilco", "lat": 19.2586, "lon": -99.1053,
     "desc": "Museum hosting spectacular Day of the Dead ofrenda installations and mask exhibitions.",
     "region": "Xochimilco, Mexico City", "tradition": "Museum Ofrenda", "color": "#facc15"},
    {"name": "Mictlan Underworld Experience - Queretaro", "lat": 20.5888, "lon": -100.3899,
     "desc": "Immersive Aztec underworld experience with authentic replica death masks and rituals.",
     "region": "Queretaro, Mexico", "tradition": "Aztec Mictlan", "color": "#818cf8"},
    {"name": "Noche de Muertos - Uruapan", "lat": 19.4173, "lon": -102.0531,
     "desc": "Purepecha Night of the Dead celebrations with tirekua masked dance performances.",
     "region": "Uruapan, Michoacan", "tradition": "Purepecha Dance", "color": "#f472b6"},
    {"name": "Lecumberri Cemetery Vigil", "lat": 19.4464, "lon": -99.1245,
     "desc": "Historic Mexico City cemetery with elaborate community vigils and traditional mask processions.",
     "region": "Mexico City, Mexico", "tradition": "Urban Vigil", "color": "#34d399"},
    {"name": "Xcaret Day of the Dead Festival", "lat": 20.5793, "lon": -87.1180,
     "desc": "Eco-park hosting Mexico's largest cultural Day of the Dead festival with mask workshops.",
     "region": "Playa del Carmen, Quintana Roo", "tradition": "Cultural Festival", "color": "#a78bfa"},
    {"name": "Teotitlan del Valle Mask Weavers", "lat": 17.0310, "lon": -96.5228,
     "desc": "Zapotec weaving village creating distinctive textile skull masks and ceremonial pieces.",
     "region": "Oaxaca Valley, Mexico", "tradition": "Zapotec Textile", "color": "#fb7185"},
    {"name": "Zinacantan Mask Festival", "lat": 16.7592, "lon": -92.7219,
     "desc": "Tzotzil Maya flower-growing community with unique jaguar and monkey mask dances.",
     "region": "Chiapas, Mexico", "tradition": "Maya Jaguar Dance", "color": "#2dd4bf"},
    {"name": "Museo de Arte Popular - Mexico City", "lat": 19.4336, "lon": -99.1451,
     "desc": "Museum of Popular Art with extensive permanent collection of Mexican ceremonial masks.",
     "region": "Mexico City, Mexico", "tradition": "Folk Art Collection", "color": "#64748b"},
    {"name": "Guerrero Tiger Mask Dances", "lat": 17.5521, "lon": -99.5075,
     "desc": "Nahua communities performing tecuani (jaguar/tiger) mask dances for agricultural rites.",
     "region": "Guerrero, Mexico", "tradition": "Tecuani Tiger Dance", "color": "#84cc16"},
]

NATIVE_AMERICAN_MASKS = [
    {"name": "Haida Heritage Centre - Skidegate", "lat": 53.2526, "lon": -131.9990,
     "desc": "Museum showcasing Haida transformation masks, frontlets, and totem pole traditions.",
     "region": "Haida Gwaii, BC", "tradition": "Haida Transformation", "color": "#10b981"},
    {"name": "U'mista Cultural Centre - Alert Bay", "lat": 50.5862, "lon": -126.9311,
     "desc": "Repatriated Kwakwaka'wakw potlatch regalia including iconic Sisiutl and Thunderbird masks.",
     "region": "Alert Bay, BC", "tradition": "Kwakwaka'wakw Potlatch", "color": "#8b5cf6"},
    {"name": "Museum of Anthropology - UBC", "lat": 49.2696, "lon": -123.2594,
     "desc": "World-class collection of Northwest Coast transformation masks and ceremonial regalia.",
     "region": "Vancouver, BC", "tradition": "Northwest Coast", "color": "#f59e0b"},
    {"name": "Hopi Cultural Center - Second Mesa", "lat": 35.8246, "lon": -110.5174,
     "desc": "Cultural center preserving Hopi kachina doll and mask traditions, sacred to Hopi people.",
     "region": "Second Mesa, Arizona", "tradition": "Hopi Kachina", "color": "#ef4444"},
    {"name": "Iroquois Indian Museum - Howes Cave", "lat": 42.6959, "lon": -74.3915,
     "desc": "Museum dedicated to Haudenosaunee art including False Face medicine masks.",
     "region": "Howes Cave, New York", "tradition": "Iroquois False Face", "color": "#ec4899"},
    {"name": "Tlingit Heritage Center - Sitka", "lat": 57.0531, "lon": -135.3300,
     "desc": "Sitka National Historical Park with Tlingit totem poles and clan crest masks.",
     "region": "Sitka, Alaska", "tradition": "Tlingit Clan Crest", "color": "#06b6d4"},
    {"name": "Squamish Lil'wat Cultural Centre", "lat": 50.0900, "lon": -122.9450,
     "desc": "Cultural center in Whistler presenting Squamish and Lil'wat mask and ceremonial traditions.",
     "region": "Whistler, BC", "tradition": "Squamish & Lil'wat", "color": "#a855f7"},
    {"name": "Makah Cultural & Research Center", "lat": 48.3654, "lon": -124.6251,
     "desc": "Museum at Neah Bay with 500-year-old masks and artifacts from the Ozette archaeological site.",
     "region": "Neah Bay, Washington", "tradition": "Makah Ozette", "color": "#f97316"},
    {"name": "Heard Museum - Phoenix", "lat": 33.4734, "lon": -112.0722,
     "desc": "Premier museum of American Indian art with extensive kachina and ceremonial mask collections.",
     "region": "Phoenix, Arizona", "tradition": "Southwest Nations", "color": "#d946ef"},
    {"name": "National Museum of the American Indian - DC", "lat": 38.8882, "lon": -77.0164,
     "desc": "Smithsonian museum with masks from tribes across North America, from Arctic to Southwest.",
     "region": "Washington, DC", "tradition": "Pan-Native American", "color": "#14b8a6"},
    {"name": "Totem Heritage Center - Ketchikan", "lat": 55.3405, "lon": -131.6330,
     "desc": "World's largest collection of unrestored 19th-century totem poles and clan masks.",
     "region": "Ketchikan, Alaska", "tradition": "Tlingit & Haida", "color": "#38bdf8"},
    {"name": "Nuu-chah-nulth Mask Carvers - Tofino", "lat": 49.1530, "lon": -125.9066,
     "desc": "First Nations artists continuing the tradition of wild man and wolf transformation masks.",
     "region": "Tofino, BC", "tradition": "Nuu-chah-nulth", "color": "#fbbf24"},
    {"name": "Seneca-Iroquois National Museum", "lat": 42.0794, "lon": -78.7625,
     "desc": "Seneca Nation museum with False Face masks and Husk Face society artifacts.",
     "region": "Salamanca, New York", "tradition": "Seneca False Face", "color": "#22c55e"},
    {"name": "Alaska Native Heritage Center", "lat": 61.2325, "lon": -149.7854,
     "desc": "Living cultural center showcasing Yup'ik, Inupiaq, and Alutiiq mask-making traditions.",
     "region": "Anchorage, Alaska", "tradition": "Alaska Native", "color": "#e879f9"},
    {"name": "Pueblo Cultural Center - Albuquerque", "lat": 35.1050, "lon": -106.6159,
     "desc": "Cultural center representing 19 Pueblo nations with ceremonial mask and dance traditions.",
     "region": "Albuquerque, New Mexico", "tradition": "Pueblo Nations", "color": "#fb923c"},
    {"name": "Royal BC Museum - Victoria", "lat": 48.4197, "lon": -123.3677,
     "desc": "Provincial museum with extensive First Nations gallery including transformation masks.",
     "region": "Victoria, BC", "tradition": "BC First Nations", "color": "#c084fc"},
    {"name": "Zuni Pueblo", "lat": 35.0700, "lon": -108.8520,
     "desc": "Zuni community known for Shalako ceremonial masked dancers and kachina traditions.",
     "region": "Zuni, New Mexico", "tradition": "Zuni Shalako", "color": "#4ade80"},
    {"name": "Kwakiutl Museum - Cape Mudge", "lat": 50.0269, "lon": -125.3616,
     "desc": "Repatriated potlatch collection including Dzunukwa (wild woman) and Raven masks.",
     "region": "Quadra Island, BC", "tradition": "Kwakiutl Potlatch", "color": "#facc15"},
    {"name": "Cherokee National Museum - Tahlequah", "lat": 35.9131, "lon": -94.9696,
     "desc": "Museum preserving Cherokee Booger Dance mask tradition and ceremonial heritage.",
     "region": "Tahlequah, Oklahoma", "tradition": "Cherokee Booger", "color": "#818cf8"},
    {"name": "Museum of Northern Arizona - Flagstaff", "lat": 35.2258, "lon": -111.6607,
     "desc": "Museum with significant collection of Hopi, Navajo, and Pueblo ceremonial objects.",
     "region": "Flagstaff, Arizona", "tradition": "Northern Arizona Nations", "color": "#f472b6"},
    {"name": "Yup'ik Mask Tradition - Bethel", "lat": 60.7922, "lon": -161.7558,
     "desc": "Center of Yup'ik mask-making with elaborate spirit masks used in midwinter ceremonies.",
     "region": "Bethel, Alaska", "tradition": "Yup'ik Spirit Masks", "color": "#34d399"},
    {"name": "Burke Museum - Seattle", "lat": 47.6604, "lon": -122.3106,
     "desc": "University of Washington museum with major Pacific Northwest Coast mask collection.",
     "region": "Seattle, Washington", "tradition": "Pacific NW Collection", "color": "#a78bfa"},
    {"name": "Tsimshian Mask Heritage - Prince Rupert", "lat": 54.3150, "lon": -130.3208,
     "desc": "Tsimshian Nation's mask-carving heritage center preserving transformation mask traditions.",
     "region": "Prince Rupert, BC", "tradition": "Tsimshian", "color": "#fb7185"},
    {"name": "Six Nations of the Grand River", "lat": 43.0607, "lon": -80.1123,
     "desc": "Haudenosaunee territory preserving False Face and Husk Face medicine society traditions.",
     "region": "Ohsweken, Ontario", "tradition": "Haudenosaunee", "color": "#2dd4bf"},
    {"name": "Wheelwright Museum - Santa Fe", "lat": 35.6696, "lon": -105.9382,
     "desc": "Museum of the American Indian with Navajo Yei and Pueblo ceremonial mask displays.",
     "region": "Santa Fe, New Mexico", "tradition": "Navajo & Pueblo", "color": "#64748b"},
    {"name": "Taos Pueblo", "lat": 36.4386, "lon": -105.5445,
     "desc": "UNESCO World Heritage adobe pueblo with over 1,000 years of ceremonial mask traditions.",
     "region": "Taos, New Mexico", "tradition": "Taos Pueblo", "color": "#84cc16"},
]

ASIAN_TEMPLE_MASKS = [
    {"name": "Barong Dance - Batubulan, Bali", "lat": -8.5404, "lon": 115.2958,
     "desc": "Sacred Barong lion mask battles demon queen Rangda in Balinese Hindu dance-drama.",
     "region": "Batubulan, Bali", "tradition": "Balinese Barong", "color": "#f59e0b"},
    {"name": "Khon Mask Workshop - Bangkok", "lat": 13.7449, "lon": 100.4930,
     "desc": "Traditional Khon masked dance workshop preserving Thai Ramakien epic mask traditions.",
     "region": "Bangkok, Thailand", "tradition": "Thai Khon", "color": "#8b5cf6"},
    {"name": "Hahoe Mask Dance Village - Andong", "lat": 36.5404, "lon": 128.5183,
     "desc": "UNESCO village preserving Korean Hahoe Byeolsin gut shaman masks and talchum dance.",
     "region": "Andong, South Korea", "tradition": "Korean Hahoe Tal", "color": "#06b6d4"},
    {"name": "Sri Lankan Kolam Dance - Ambalangoda", "lat": 6.2350, "lon": 80.0531,
     "desc": "Mask museum and workshops for traditional Kolam, Sanni Yakuma healing, and Raksha masks.",
     "region": "Ambalangoda, Sri Lanka", "tradition": "Sinhalese Kolam", "color": "#ef4444"},
    {"name": "Topeng Mask Dance - Ubud, Bali", "lat": -8.5069, "lon": 115.2625,
     "desc": "Sacred Topeng masked dance theater telling stories of Balinese kings and deities.",
     "region": "Ubud, Bali", "tradition": "Balinese Topeng", "color": "#ec4899"},
    {"name": "Bhutan Tsechu Festival - Thimphu", "lat": 27.4728, "lon": 89.6393,
     "desc": "Annual Buddhist festival with elaborate Cham mask dances at Thimphu Dzong.",
     "region": "Thimphu, Bhutan", "tradition": "Bhutanese Cham", "color": "#10b981"},
    {"name": "Tibetan Cham Dance - Hemis Monastery", "lat": 33.9078, "lon": 77.7070,
     "desc": "Annual Hemis Tsechu with colorful deity and demon Cham mask dances in Ladakh.",
     "region": "Hemis, Ladakh", "tradition": "Tibetan Cham", "color": "#a855f7"},
    {"name": "Wayang Wong Temple Performance - Java", "lat": -7.5928, "lon": 110.8277,
     "desc": "Sacred Javanese court dance-drama with Ramayana mask performances at Prambanan Temple.",
     "region": "Prambanan, Java", "tradition": "Javanese Wayang Wong", "color": "#f97316"},
    {"name": "Kathakali Mask Theater - Kochi", "lat": 9.9312, "lon": 76.2673,
     "desc": "Kerala's elaborate Kathakali dance-drama with painted face masks depicting Mahabharata stories.",
     "region": "Kochi, Kerala", "tradition": "Kathakali", "color": "#d946ef"},
    {"name": "Chinese Opera Masks - Beijing Opera", "lat": 39.9042, "lon": 116.4074,
     "desc": "Jingju (Beijing Opera) face painting traditions with color-coded character masks.",
     "region": "Beijing, China", "tradition": "Jingju Opera", "color": "#14b8a6"},
    {"name": "Sichuan Opera Face-Changing - Chengdu", "lat": 30.5728, "lon": 104.0668,
     "desc": "Legendary bian lian face-changing technique where masks switch in split seconds.",
     "region": "Chengdu, Sichuan", "tradition": "Sichuan Bian Lian", "color": "#38bdf8"},
    {"name": "Theyyam Ritual Masks - Kannur", "lat": 11.8745, "lon": 75.3704,
     "desc": "Spectacular North Kerala temple ritual with elaborate mask-like face painting and headdresses.",
     "region": "Kannur, Kerala", "tradition": "Theyyam", "color": "#fbbf24"},
    {"name": "Mask Museum - Ambalangoda", "lat": 6.2380, "lon": 80.0536,
     "desc": "Dedicated mask museum displaying 100+ traditional Sinhalese masks used in exorcism and dance.",
     "region": "Ambalangoda, Sri Lanka", "tradition": "Sinhalese Collection", "color": "#22c55e"},
    {"name": "Rangda Mask Temple - Gianyar, Bali", "lat": -8.5415, "lon": 115.3275,
     "desc": "Temple storing sacred Rangda witch-queen masks used in Calon Arang exorcism dance.",
     "region": "Gianyar, Bali", "tradition": "Rangda Exorcism", "color": "#e879f9"},
    {"name": "Thai National Museum - Khon Collection", "lat": 13.7584, "lon": 100.4923,
     "desc": "National museum with extensive royal Khon mask collection from Ramakien performances.",
     "region": "Bangkok, Thailand", "tradition": "Royal Khon", "color": "#fb923c"},
    {"name": "Nepali Indra Jatra Festival - Kathmandu", "lat": 27.7044, "lon": 85.3076,
     "desc": "Kathmandu's biggest festival with Lakhe demon mask dances honoring Lord Indra.",
     "region": "Kathmandu, Nepal", "tradition": "Nepali Lakhe", "color": "#c084fc"},
    {"name": "Cham Dance at Rumtek Monastery", "lat": 27.2875, "lon": 88.5656,
     "desc": "Major Kagyu Buddhist monastery in Sikkim hosting annual Cham mask dance festivals.",
     "region": "Gangtok, Sikkim", "tradition": "Sikkimese Cham", "color": "#4ade80"},
    {"name": "Phi Ta Khon Ghost Festival - Loei", "lat": 17.4860, "lon": 101.7223,
     "desc": "Thai ghost festival where villagers wear colorful oversized spirit masks and dance.",
     "region": "Dan Sai, Loei", "tradition": "Phi Ta Khon", "color": "#facc15"},
    {"name": "Vietnamese Water Puppet Masks - Hanoi", "lat": 21.0285, "lon": 105.8542,
     "desc": "Traditional water puppet theater at Thang Long with carved lacquered puppet masks.",
     "region": "Hanoi, Vietnam", "tradition": "Mua Roi Nuoc", "color": "#818cf8"},
    {"name": "Bhairab Mask Temple - Bhaktapur", "lat": 27.6720, "lon": 85.4298,
     "desc": "Ancient Newar temple with enormous Bhairab deity mask displayed during Bisket Jatra festival.",
     "region": "Bhaktapur, Nepal", "tradition": "Newar Bhairab", "color": "#f472b6"},
    {"name": "Tamshing Phala Chhoepa - Bumthang", "lat": 27.5882, "lon": 90.7310,
     "desc": "Bhutanese naked dance festival with unique Cham masks at Tamshing Monastery.",
     "region": "Bumthang, Bhutan", "tradition": "Bhutanese Tamshing", "color": "#34d399"},
    {"name": "Yakshagana Mask Theater - Udupi", "lat": 13.3389, "lon": 74.7451,
     "desc": "Karnataka's traditional dance-drama with elaborate painted headdress masks and costumes.",
     "region": "Udupi, Karnataka", "tradition": "Yakshagana", "color": "#a78bfa"},
    {"name": "Angkor Wat Apsara Dance - Siem Reap", "lat": 13.4125, "lon": 103.8670,
     "desc": "Khmer classical dance with crown masks and deity character performances near Angkor Wat.",
     "region": "Siem Reap, Cambodia", "tradition": "Khmer Apsara", "color": "#fb7185"},
    {"name": "Mani Rimdu Festival - Tengboche", "lat": 27.8364, "lon": 86.7639,
     "desc": "Sherpa Buddhist festival with Cham mask dances at Tengboche Monastery below Everest.",
     "region": "Tengboche, Nepal", "tradition": "Sherpa Cham", "color": "#2dd4bf"},
    {"name": "Chinese Nuo Opera Masks - Guizhou", "lat": 26.6470, "lon": 106.6302,
     "desc": "Ancient Nuo exorcism masks and opera traditions preserved in Guizhou's mountain villages.",
     "region": "Guiyang, Guizhou", "tradition": "Nuo Opera", "color": "#64748b"},
    {"name": "Sandae Mask Dance - Seoul", "lat": 37.5800, "lon": 126.9850,
     "desc": "Korean talchum mask dance satirizing social hierarchy performed at festivals and events.",
     "region": "Seoul, South Korea", "tradition": "Korean Sandae", "color": "#84cc16"},
]

CARNIVAL_MASKS_WORLDWIDE = [
    {"name": "Rio Carnival - Sambodromo", "lat": -22.9122, "lon": -43.1967,
     "desc": "World's largest carnival with samba schools competing in elaborate mask and costume parades.",
     "region": "Rio de Janeiro, Brazil", "tradition": "Samba Carnival", "color": "#f59e0b"},
    {"name": "Mardi Gras - New Orleans", "lat": 29.9511, "lon": -90.0715,
     "desc": "Iconic celebration with krewe masks, elaborate floats, and bead-throwing traditions.",
     "region": "New Orleans, USA", "tradition": "Mardi Gras", "color": "#a855f7"},
    {"name": "Basel Fasnacht", "lat": 47.5596, "lon": 7.5886,
     "desc": "Switzerland's largest carnival with Morgestraich lantern procession and larve masks.",
     "region": "Basel, Switzerland", "tradition": "Basel Larven", "color": "#10b981"},
    {"name": "Trinidad Carnival", "lat": 10.6918, "lon": -61.2225,
     "desc": "Caribbean mas (masquerade) tradition with elaborate wire-bending and feathered headpieces.",
     "region": "Port of Spain, Trinidad", "tradition": "Caribbean Mas", "color": "#ec4899"},
    {"name": "Cologne Carnival (Kolner Karneval)", "lat": 50.9375, "lon": 6.9603,
     "desc": "Germany's largest carnival with Nubbel burning, clown masks, and Rose Monday parade.",
     "region": "Cologne, Germany", "tradition": "Rhineland Karneval", "color": "#ef4444"},
    {"name": "Binche Carnival - Gilles", "lat": 50.4114, "lon": 4.1672,
     "desc": "UNESCO heritage carnival with Gilles dancers wearing wax masks and ostrich-feather hats.",
     "region": "Binche, Belgium", "tradition": "Gilles de Binche", "color": "#06b6d4"},
    {"name": "Oruro Carnival - La Diablada", "lat": -17.9647, "lon": -67.1140,
     "desc": "UNESCO Masterpiece with La Diablada devil masks and Morenada dance costumes.",
     "region": "Oruro, Bolivia", "tradition": "Bolivian Diablada", "color": "#8b5cf6"},
    {"name": "Santa Cruz de Tenerife Carnival", "lat": 28.4636, "lon": -16.2518,
     "desc": "Second-largest carnival worldwide with drag queen gala and elaborate mask competitions.",
     "region": "Tenerife, Spain", "tradition": "Canary Islands", "color": "#f97316"},
    {"name": "Viareggio Carnival", "lat": 43.8714, "lon": 10.2503,
     "desc": "Famous for gigantic satirical papier-mache masks on elaborate floats along the seafront.",
     "region": "Viareggio, Italy", "tradition": "Papier-Mache Satire", "color": "#d946ef"},
    {"name": "Nice Carnival", "lat": 43.6961, "lon": 7.2660,
     "desc": "Battle of Flowers and Parade of Lights with colossal masked figures on the Riviera.",
     "region": "Nice, France", "tradition": "Nice Carnival", "color": "#14b8a6"},
    {"name": "Barranquilla Carnival", "lat": 10.9685, "lon": -74.7813,
     "desc": "UNESCO-recognized Colombian carnival with marimonda masks and Congo dance traditions.",
     "region": "Barranquilla, Colombia", "tradition": "Colombian Carnival", "color": "#38bdf8"},
    {"name": "Notting Hill Carnival - London", "lat": 51.5170, "lon": -0.2048,
     "desc": "Europe's largest street festival celebrating Caribbean culture with masquerade bands.",
     "region": "London, UK", "tradition": "Caribbean Mas", "color": "#fbbf24"},
    {"name": "Ivrea Orange Battle Carnival", "lat": 45.4659, "lon": 7.8771,
     "desc": "Medieval carnival with symbolic orange battle and traditional Tuchini rebel masks.",
     "region": "Ivrea, Italy", "tradition": "Medieval Rebel", "color": "#22c55e"},
    {"name": "Cadiz Carnival", "lat": 36.5271, "lon": -6.2886,
     "desc": "Famous for satirical chirigotas (musical groups) performing in elaborate costumes and masks.",
     "region": "Cadiz, Spain", "tradition": "Chirigota Satire", "color": "#e879f9"},
    {"name": "Lucerne Fasnacht", "lat": 47.0502, "lon": 8.3093,
     "desc": "Central Swiss carnival with Greth Schell masks and Fritschivater figures.",
     "region": "Lucerne, Switzerland", "tradition": "Swiss Fasnacht", "color": "#fb923c"},
    {"name": "Maastricht Carnival", "lat": 50.8514, "lon": 5.6910,
     "desc": "Dutch southern carnival where the city transforms into Mestreech with festive masks.",
     "region": "Maastricht, Netherlands", "tradition": "Dutch Carnival", "color": "#c084fc"},
    {"name": "Aalborg Carnival", "lat": 57.0488, "lon": 9.9217,
     "desc": "Northern Europe's largest carnival parade with 100,000+ masked participants.",
     "region": "Aalborg, Denmark", "tradition": "Scandinavian", "color": "#4ade80"},
    {"name": "Mazatlan Carnival", "lat": 23.2494, "lon": -106.4111,
     "desc": "Third-largest carnival in the world with elaborate masks and seaside parade.",
     "region": "Mazatlan, Mexico", "tradition": "Mexican Carnival", "color": "#facc15"},
    {"name": "Mohacs Busojaras", "lat": 46.0093, "lon": 18.6791,
     "desc": "Hungarian carnival with fearsome wooden Buso masks to scare away winter.",
     "region": "Mohacs, Hungary", "tradition": "Buso Masks", "color": "#818cf8"},
    {"name": "Mindelo Carnival - Cape Verde", "lat": 16.8908, "lon": -24.9808,
     "desc": "African island carnival inspired by Brazilian and Portuguese traditions with elaborate masks.",
     "region": "Mindelo, Cape Verde", "tradition": "Cape Verdean", "color": "#f472b6"},
    {"name": "Goa Carnival", "lat": 15.2993, "lon": 74.1240,
     "desc": "Three-day Portuguese-influenced festival with King Momo masks and float parades.",
     "region": "Goa, India", "tradition": "Indo-Portuguese", "color": "#34d399"},
    {"name": "Recife Carnival - Galo da Madrugada", "lat": -8.0476, "lon": -34.8770,
     "desc": "World-record carnival bloc with giant rooster float and frevo dance masks.",
     "region": "Recife, Brazil", "tradition": "Frevo Dance", "color": "#a78bfa"},
    {"name": "Montevideo Carnival - Llamadas", "lat": -34.9011, "lon": -56.1645,
     "desc": "World's longest carnival season with candombe drum processions and masked comparsas.",
     "region": "Montevideo, Uruguay", "tradition": "Candombe", "color": "#fb7185"},
    {"name": "Dunkirk Carnival", "lat": 51.0343, "lon": 2.3768,
     "desc": "Raucous northern French carnival with the Bande de la Citadelle masked parade.",
     "region": "Dunkirk, France", "tradition": "French Bande", "color": "#2dd4bf"},
    {"name": "Sitges Carnival", "lat": 41.2354, "lon": 1.8058,
     "desc": "Catalonia's most extravagant carnival known for elaborate costumes and mask competitions.",
     "region": "Sitges, Spain", "tradition": "Catalan Carnival", "color": "#64748b"},
    {"name": "Patras Carnival - Greece", "lat": 38.2466, "lon": 21.7346,
     "desc": "Largest Greek carnival with masked treasure hunt and spectacular float parade.",
     "region": "Patras, Greece", "tradition": "Greek Apokries", "color": "#84cc16"},
]

SHAMANIC_RITUAL_MASKS = [
    {"name": "Siberian Shaman Masks - Kyzyl (Tuva)", "lat": 51.7191, "lon": 94.4378,
     "desc": "Tuvan shamans using drum masks and headdresses in kamlanie spirit journey ceremonies.",
     "region": "Kyzyl, Tuva Republic", "tradition": "Tuvan Shamanism", "color": "#8b5cf6"},
    {"name": "Himalayan Shaman Masks - Kathmandu Valley", "lat": 27.7044, "lon": 85.3076,
     "desc": "Dhami-jhankri shamans using carved wooden masks for healing and exorcism rituals.",
     "region": "Kathmandu, Nepal", "tradition": "Nepali Dhami-Jhankri", "color": "#f59e0b"},
    {"name": "Amazonian Shaman Masks - Iquitos", "lat": -3.7491, "lon": -73.2538,
     "desc": "Indigenous Amazonian shamans using bark cloth and feather masks in ayahuasca ceremonies.",
     "region": "Iquitos, Peru", "tradition": "Amazonian Ayahuasca", "color": "#10b981"},
    {"name": "Aboriginal Ceremony Grounds - Arnhem Land", "lat": -12.4634, "lon": 136.4171,
     "desc": "Aboriginal people's sacred body painting and bark masks used in Dreamtime ceremonies.",
     "region": "Arnhem Land, NT Australia", "tradition": "Aboriginal Dreaming", "color": "#ef4444"},
    {"name": "Korean Mudang Gut Ritual - Ganghwa", "lat": 37.7463, "lon": 126.4878,
     "desc": "Korean mudang shamans performing gut rituals with deity and spirit masks on Ganghwa Island.",
     "region": "Ganghwa, South Korea", "tradition": "Korean Gut Shamanism", "color": "#ec4899"},
    {"name": "Siberian Evenki Shaman Center - Yakutsk", "lat": 62.0355, "lon": 129.6755,
     "desc": "Evenki shamanic heritage with spirit-world bird masks and reindeer antler headdresses.",
     "region": "Yakutsk, Sakha Republic", "tradition": "Evenki Shamanism", "color": "#06b6d4"},
    {"name": "Bon Ritual Masks - Upper Mustang", "lat": 29.1800, "lon": 83.9600,
     "desc": "Pre-Buddhist Bon religion masks used in Tiji festival at the ancient walled city of Lo Manthang.",
     "region": "Lo Manthang, Nepal", "tradition": "Tibetan Bon", "color": "#a855f7"},
    {"name": "Mapuche Machi Ceremony - Temuco", "lat": -38.7359, "lon": -72.5904,
     "desc": "Mapuche machi (shaman) ceremonies with carved rewe masks and ritualistic drumming.",
     "region": "Temuco, Chile", "tradition": "Mapuche Machi", "color": "#f97316"},
    {"name": "Sami Noaidi Drum Masks - Kautokeino", "lat": 69.0125, "lon": 23.0403,
     "desc": "Sami shamanic tradition with painted drum figures and spirit-journey mask rituals.",
     "region": "Kautokeino, Norway", "tradition": "Sami Noaidi", "color": "#d946ef"},
    {"name": "Papua New Guinea Spirit Masks - Sepik", "lat": -3.8616, "lon": 141.8505,
     "desc": "Haus Tambaran spirit houses containing sacred ancestor masks along the Sepik River.",
     "region": "Sepik River, PNG", "tradition": "Sepik Ancestor", "color": "#14b8a6"},
    {"name": "Aztec Priest Masks - Tenochtitlan (Mexico City)", "lat": 19.4352, "lon": -99.1312,
     "desc": "Templo Mayor museum with turquoise mosaic masks used by Aztec priests in ceremonies.",
     "region": "Mexico City, Mexico", "tradition": "Aztec Ritual", "color": "#38bdf8"},
    {"name": "Vodou Masks & Altars - Port-au-Prince", "lat": 18.5944, "lon": -72.3074,
     "desc": "Haitian Vodou traditions with Gede spirit masks, sequined flags, and ceremony altars.",
     "region": "Port-au-Prince, Haiti", "tradition": "Haitian Vodou", "color": "#fbbf24"},
    {"name": "Mongolian Tsam Dance Masks - Ulaanbaatar", "lat": 47.9184, "lon": 106.9177,
     "desc": "Buddhist Tsam masked dance tradition with elaborate deity masks at Gandantegchinlen Monastery.",
     "region": "Ulaanbaatar, Mongolia", "tradition": "Mongolian Tsam", "color": "#22c55e"},
    {"name": "Asmat Ancestor Masks - Agats", "lat": -5.5333, "lon": 138.1167,
     "desc": "Asmat people's ancestor spirit masks (jipae) used in headhunting and initiation rituals.",
     "region": "Agats, Papua", "tradition": "Asmat Jipae", "color": "#e879f9"},
    {"name": "Torres Strait Islander Masks - Thursday Island", "lat": -10.5833, "lon": 142.2167,
     "desc": "Elaborate turtle-shell masks (dari) used in ceremonial dances of the Torres Strait Islanders.",
     "region": "Thursday Island, QLD", "tradition": "Torres Strait Dari", "color": "#fb923c"},
    {"name": "Inuit Transformation Masks - Iqaluit", "lat": 63.7467, "lon": -68.5170,
     "desc": "Inuit shamanic masks depicting animal-human transformation used in midwinter ceremonies.",
     "region": "Iqaluit, Nunavut", "tradition": "Inuit Angakkuq", "color": "#c084fc"},
    {"name": "Santeria Masks & Orishas - Havana", "lat": 23.1136, "lon": -82.3666,
     "desc": "Afro-Cuban Santeria tradition with orisha deity masks and Abakua secret society costumes.",
     "region": "Havana, Cuba", "tradition": "Cuban Santeria", "color": "#4ade80"},
    {"name": "Candomble Masks - Salvador", "lat": -12.9714, "lon": -38.5124,
     "desc": "Afro-Brazilian Candomble ceremonies with orixas masks and elaborate ritual costumes.",
     "region": "Salvador, Bahia", "tradition": "Brazilian Candomble", "color": "#facc15"},
    {"name": "Taino Ceremonial Masks - San Juan", "lat": 18.4655, "lon": -66.1057,
     "desc": "Indigenous Taino people's guanin and cohoba masks used in cemis spirit ceremonies.",
     "region": "San Juan, Puerto Rico", "tradition": "Taino Cemis", "color": "#818cf8"},
    {"name": "Dogon Mask Society - Sangha", "lat": 14.4410, "lon": -3.3170,
     "desc": "Dogon Awa society's sacred masks performed during Sigui ceremonies every 60 years.",
     "region": "Sangha, Mali", "tradition": "Dogon Awa Sigui", "color": "#f472b6"},
    {"name": "Maori Haka Face Carving - Rotorua", "lat": -38.1368, "lon": 176.2497,
     "desc": "Ta moko facial tattooing and carved meeting house masks at Te Puia cultural center.",
     "region": "Rotorua, New Zealand", "tradition": "Maori Ta Moko", "color": "#34d399"},
    {"name": "Altai Shaman Masks - Gorno-Altaysk", "lat": 51.9581, "lon": 85.9603,
     "desc": "Altai shamanic tradition with leather spirit masks and eeren guardian figures.",
     "region": "Gorno-Altaysk, Russia", "tradition": "Altai Shamanism", "color": "#a78bfa"},
    {"name": "Buryat Shaman Masks - Ulan-Ude", "lat": 51.8340, "lon": 107.5841,
     "desc": "Buryat shamanic tradition with ongon spirit masks and ceremonial drumming rituals.",
     "region": "Ulan-Ude, Buryatia", "tradition": "Buryat Shamanism", "color": "#fb7185"},
    {"name": "Maya Shaman Masks - Tikal", "lat": 17.2220, "lon": -89.6237,
     "desc": "Ancient Maya ritual jade and obsidian masks used by shamans in temple ceremonies at Tikal.",
     "region": "Tikal, Guatemala", "tradition": "Maya Shamanic", "color": "#2dd4bf"},
    {"name": "Koryak Shaman Masks - Palana", "lat": 59.0833, "lon": 159.9500,
     "desc": "Koryak people's raven spirit masks and whale-hunting ceremony masks in Kamchatka.",
     "region": "Palana, Kamchatka", "tradition": "Koryak Spirit", "color": "#64748b"},
    {"name": "San Bushman Trance Dance - Tsodilo Hills", "lat": -18.7500, "lon": 21.7333,
     "desc": "San healing trance dances near the sacred rock art site of Tsodilo Hills in Botswana.",
     "region": "Tsodilo Hills, Botswana", "tradition": "San Trance Dance", "color": "#84cc16"},
]

ANCIENT_MASKS = [
    {"name": "Tutankhamun's Gold Mask - Egyptian Museum", "lat": 30.0478, "lon": 31.2336,
     "desc": "The iconic 11kg gold death mask of Pharaoh Tutankhamun, the world's most famous mask.",
     "region": "Cairo, Egypt", "mask_type": "Egyptian Gold Death Mask", "color": "#f59e0b"},
    {"name": "Mask of Agamemnon - Athens", "lat": 37.9895, "lon": 23.7321,
     "desc": "Gold funeral mask discovered by Schliemann at Mycenae, now in the National Archaeological Museum.",
     "region": "Athens, Greece", "mask_type": "Mycenaean Gold Mask", "color": "#8b5cf6"},
    {"name": "Roman Theater Masks - Pompeii", "lat": 40.7509, "lon": 14.4869,
     "desc": "Excavated comedy and tragedy theater masks from the buried Roman city of Pompeii.",
     "region": "Pompeii, Italy", "mask_type": "Roman Theater", "color": "#ef4444"},
    {"name": "Teotihuacan Jade Masks", "lat": 19.6925, "lon": -98.8438,
     "desc": "Jade and obsidian funerary masks from the Pyramid of the Sun at Teotihuacan.",
     "region": "Teotihuacan, Mexico", "mask_type": "Mesoamerican Jade", "color": "#10b981"},
    {"name": "Pakal's Jade Death Mask - Palenque", "lat": 17.4838, "lon": -92.0462,
     "desc": "Magnificent jade mosaic mask of King K'inich Janaab Pakal from his tomb at Palenque.",
     "region": "Palenque, Mexico", "mask_type": "Maya Jade Mask", "color": "#ec4899"},
    {"name": "Greek Theater of Epidaurus", "lat": 37.5963, "lon": 23.0792,
     "desc": "Best-preserved ancient theater where actors wore terracotta masks for comedy and tragedy.",
     "region": "Epidaurus, Greece", "mask_type": "Greek Theater", "color": "#06b6d4"},
    {"name": "Phoenician Masks - Carthage", "lat": 36.8526, "lon": 10.3233,
     "desc": "Phoenician terracotta grotesque masks from the Tophet sanctuary of ancient Carthage.",
     "region": "Carthage, Tunisia", "mask_type": "Phoenician Terracotta", "color": "#a855f7"},
    {"name": "Sanxingdui Bronze Masks - Guanghan", "lat": 31.0000, "lon": 104.2833,
     "desc": "Mysterious 3,000-year-old giant bronze masks with protruding eyes from Sanxingdui culture.",
     "region": "Guanghan, Sichuan", "mask_type": "Sanxingdui Bronze", "color": "#f97316"},
    {"name": "Etruscan Tomb Masks - Cerveteri", "lat": 42.0000, "lon": 12.1000,
     "desc": "Terracotta funerary masks and sarcophagus portraits from the Etruscan necropolis of Banditaccia.",
     "region": "Cerveteri, Italy", "mask_type": "Etruscan Funerary", "color": "#d946ef"},
    {"name": "Luzira Head - Kampala", "lat": 0.3136, "lon": 32.6174,
     "desc": "Enigmatic ceramic head/mask from 1,000-year-old Iron Age site near Lake Victoria.",
     "region": "Kampala, Uganda", "mask_type": "African Iron Age", "color": "#14b8a6"},
    {"name": "Roman Cavalry Masks - Kalkriese", "lat": 52.4089, "lon": 8.1264,
     "desc": "Iron face masks worn by Roman cavalry, found at the Varus Battle site in Germany.",
     "region": "Kalkriese, Germany", "mask_type": "Roman Cavalry", "color": "#38bdf8"},
    {"name": "Moche Portrait Vessels - Trujillo", "lat": -8.1116, "lon": -79.0289,
     "desc": "Incredibly realistic ceramic portrait masks/vessels from the Moche civilization of Peru.",
     "region": "Trujillo, Peru", "mask_type": "Moche Ceramic Portrait", "color": "#fbbf24"},
    {"name": "Hattian Gold Masks - Museum of Anatolian Civilizations", "lat": 39.9334, "lon": 32.8597,
     "desc": "Pre-Hittite gold funeral masks from royal tombs of Alacahoyuk, dating to 2500 BCE.",
     "region": "Ankara, Turkey", "mask_type": "Hattian Gold", "color": "#22c55e"},
    {"name": "Minoan Bull-Leaping Masks - Heraklion", "lat": 35.3387, "lon": 25.1442,
     "desc": "Minoan ceremonial masks and rhytons from the Palace of Knossos in the Heraklion Museum.",
     "region": "Heraklion, Crete", "mask_type": "Minoan Ceremonial", "color": "#e879f9"},
    {"name": "Sipan Lord's Gold Mask - Lambayeque", "lat": -6.7011, "lon": -79.9084,
     "desc": "Magnificent gold mask of the Lord of Sipan, a Moche warrior-priest buried with treasures.",
     "region": "Lambayeque, Peru", "mask_type": "Moche Gold", "color": "#fb923c"},
    {"name": "Chinese Bronze Ritual Masks - Anyang", "lat": 36.0972, "lon": 114.3525,
     "desc": "Shang Dynasty bronze masks and taotie motif vessels from the ruins of Yin at Anyang.",
     "region": "Anyang, Henan", "mask_type": "Shang Bronze", "color": "#c084fc"},
    {"name": "Lydenburg Heads - Pretoria", "lat": -25.7479, "lon": 28.2293,
     "desc": "Earliest known African iron age sculpture masks from 500 CE in South Africa.",
     "region": "Pretoria, South Africa", "mask_type": "Lydenburg Iron Age", "color": "#4ade80"},
    {"name": "Roman Funeral Masks - Museo Nazionale Romano", "lat": 41.9014, "lon": 12.4984,
     "desc": "Wax imagines (ancestor masks) and marble portrait masks of Roman patrician families.",
     "region": "Rome, Italy", "mask_type": "Roman Imagines", "color": "#facc15"},
    {"name": "Ife Bronze Masks - Lagos", "lat": 6.5244, "lon": 3.3792,
     "desc": "Naturalistic bronze and terracotta masks of Ife kings, 12th-14th century Nigerian art.",
     "region": "Lagos, Nigeria", "mask_type": "Ife Bronze", "color": "#818cf8"},
    {"name": "Babylonian Demon Masks - Baghdad", "lat": 33.3128, "lon": 44.3615,
     "desc": "Mesopotamian Pazuzu and Humbaba demon masks from ancient Babylonian protective rituals.",
     "region": "Baghdad, Iraq", "mask_type": "Babylonian Demon", "color": "#f472b6"},
    {"name": "Chimu Gold Masks - Chan Chan", "lat": -8.1049, "lon": -79.0747,
     "desc": "Pre-Inca gold funerary masks from the largest pre-Columbian adobe city in the Americas.",
     "region": "Trujillo, Peru", "mask_type": "Chimu Gold", "color": "#34d399"},
    {"name": "Thracian Gold Masks - Sofia", "lat": 42.6977, "lon": 23.3219,
     "desc": "Spectacular Thracian gold masks from royal tombs, displayed in Sofia's National Museum.",
     "region": "Sofia, Bulgaria", "mask_type": "Thracian Gold", "color": "#a78bfa"},
    {"name": "Olmec Jade Masks - Villahermosa", "lat": 17.9895, "lon": -92.9475,
     "desc": "Ancient Olmec jade masks and figurines from La Venta, in the Parque Museo La Venta.",
     "region": "Villahermosa, Mexico", "mask_type": "Olmec Jade", "color": "#fb7185"},
    {"name": "Anglo-Saxon Sutton Hoo Helmet-Mask", "lat": 52.0890, "lon": 1.3359,
     "desc": "Iconic Anglo-Saxon helmet with face mask from the Sutton Hoo royal ship burial.",
     "region": "Sutton Hoo, England", "mask_type": "Anglo-Saxon Helmet", "color": "#2dd4bf"},
    {"name": "Nubian Gold Masks - Khartoum", "lat": 15.5007, "lon": 32.5599,
     "desc": "Kushite royal gold death masks from pyramids of Meroe displayed at the Sudan National Museum.",
     "region": "Khartoum, Sudan", "mask_type": "Nubian Kushite Gold", "color": "#64748b"},
    {"name": "Peruvian Nazca Masks - Ica", "lat": -14.0755, "lon": -75.7343,
     "desc": "Nazca culture ceremonial masks with trophy head imagery at the Ica Regional Museum.",
     "region": "Ica, Peru", "mask_type": "Nazca Ceremonial", "color": "#84cc16"},
]

MASK_MUSEUMS = [
    {"name": "Metropolitan Museum of Art - NYC", "lat": 40.7794, "lon": -73.9632,
     "desc": "World-class collection spanning African, Oceanic, and Asian masks in the Michael C. Rockefeller Wing.",
     "region": "New York, USA", "specialty": "Global Collection", "color": "#f59e0b"},
    {"name": "Musee du Quai Branly - Paris", "lat": 48.8611, "lon": 2.2977,
     "desc": "France's premier museum of non-European arts with 3,500+ masks from Africa, Asia, and Oceania.",
     "region": "Paris, France", "specialty": "African & Oceanic", "color": "#8b5cf6"},
    {"name": "British Museum - London", "lat": 51.5194, "lon": -0.1270,
     "desc": "Extensive mask collection from ancient Egypt, Africa, Mesoamerica, and the Pacific.",
     "region": "London, UK", "specialty": "Ancient & World Masks", "color": "#10b981"},
    {"name": "National Museum of Ethnology - Leiden", "lat": 52.1571, "lon": 4.4856,
     "desc": "Major Dutch collection of masks from Indonesia, Africa, and the Americas.",
     "region": "Leiden, Netherlands", "specialty": "Indonesian & African", "color": "#ef4444"},
    {"name": "Pitt Rivers Museum - Oxford", "lat": 51.7586, "lon": -1.2557,
     "desc": "Iconic anthropological museum with dense displays of masks from worldwide cultures.",
     "region": "Oxford, UK", "specialty": "Anthropological", "color": "#ec4899"},
    {"name": "Ethnological Museum - Berlin (Humboldt Forum)", "lat": 52.5167, "lon": 13.4005,
     "desc": "Major collection of masks from Africa, Pacific, and the Americas at the Humboldt Forum.",
     "region": "Berlin, Germany", "specialty": "Pacific & Americas", "color": "#06b6d4"},
    {"name": "Museo Internazionale della Maschera - Venice", "lat": 45.4360, "lon": 12.3350,
     "desc": "Dedicated mask museum in Venice with Venetian, commedia dell'arte, and world mask collections.",
     "region": "Venice, Italy", "specialty": "Venetian Masks", "color": "#a855f7"},
    {"name": "Museo Nacional de Antropologia - Mexico City", "lat": 19.4260, "lon": -99.1861,
     "desc": "Mexico's greatest museum with extensive Aztec, Maya, and Olmec mask collections.",
     "region": "Mexico City, Mexico", "specialty": "Mesoamerican", "color": "#f97316"},
    {"name": "Tokyo National Museum", "lat": 35.7189, "lon": 139.7766,
     "desc": "Japan's oldest museum with outstanding Noh, Bugaku, and Gigaku mask collections.",
     "region": "Tokyo, Japan", "specialty": "Japanese Noh & Bugaku", "color": "#d946ef"},
    {"name": "Rietberg Museum - Zurich", "lat": 47.3542, "lon": 8.5281,
     "desc": "Swiss museum of non-European art with significant African and Asian mask collections.",
     "region": "Zurich, Switzerland", "specialty": "African & Asian", "color": "#14b8a6"},
    {"name": "National Museum of Korea - Seoul", "lat": 37.5230, "lon": 126.9804,
     "desc": "Major museum with Korean talchum masks, Buddhist sculpture masks, and shamanic artifacts.",
     "region": "Seoul, South Korea", "specialty": "Korean Masks", "color": "#38bdf8"},
    {"name": "Fowler Museum - UCLA", "lat": 34.0728, "lon": -118.4420,
     "desc": "University museum with exceptional collection of African and Oceanic masks.",
     "region": "Los Angeles, USA", "specialty": "African & Oceanic", "color": "#fbbf24"},
    {"name": "Museum of Archaeology & Anthropology - Cambridge", "lat": 52.2012, "lon": 0.1207,
     "desc": "Cambridge University museum with Torres Strait, Pacific, and Native American mask collections.",
     "region": "Cambridge, UK", "specialty": "Pacific & Native American", "color": "#22c55e"},
    {"name": "Royal Museum for Central Africa - Tervuren", "lat": 50.8306, "lon": 4.5194,
     "desc": "Extraordinary collection of 120,000+ Central African objects including rare masks from the Congo.",
     "region": "Tervuren, Belgium", "specialty": "Central African", "color": "#e879f9"},
    {"name": "Museum of World Cultures - Gothenburg", "lat": 57.7000, "lon": 11.9658,
     "desc": "Swedish museum with African, Asian, and South American mask and art collections.",
     "region": "Gothenburg, Sweden", "specialty": "World Cultures", "color": "#fb923c"},
    {"name": "Museo de Arte Popular - Mexico City", "lat": 19.4336, "lon": -99.1451,
     "desc": "Museum celebrating Mexican folk art including elaborate ceremonial and dance masks.",
     "region": "Mexico City, Mexico", "specialty": "Mexican Folk Masks", "color": "#c084fc"},
    {"name": "Australian Museum - Sydney", "lat": -33.8744, "lon": 151.2082,
     "desc": "Australia's oldest museum with Aboriginal and Torres Strait Islander mask collections.",
     "region": "Sydney, Australia", "specialty": "Aboriginal & Pacific", "color": "#4ade80"},
    {"name": "National Museum of African Art - Smithsonian", "lat": 38.8883, "lon": -77.0230,
     "desc": "Smithsonian museum with significant collection of West and Central African masks.",
     "region": "Washington, DC", "specialty": "African Collection", "color": "#facc15"},
    {"name": "Musee Barbier-Mueller - Geneva", "lat": 46.2017, "lon": 6.1467,
     "desc": "Private museum with one of the world's finest collections of tribal and ancient masks.",
     "region": "Geneva, Switzerland", "specialty": "Tribal & Ancient", "color": "#818cf8"},
    {"name": "Museum der Kulturen - Basel", "lat": 47.5533, "lon": 7.5919,
     "desc": "Major Swiss ethnographic museum with masks from Oceania, Africa, and the Americas.",
     "region": "Basel, Switzerland", "specialty": "Oceanic & African", "color": "#f472b6"},
    {"name": "Museo de las Americas - Madrid", "lat": 40.4388, "lon": -3.7200,
     "desc": "Spanish museum with pre-Columbian masks from across Central and South America.",
     "region": "Madrid, Spain", "specialty": "Pre-Columbian", "color": "#34d399"},
    {"name": "Peabody Museum - Harvard", "lat": 42.3783, "lon": -71.1142,
     "desc": "Harvard's archaeology museum with significant Native American and Mesoamerican mask collections.",
     "region": "Cambridge, MA", "specialty": "Native American & Mesoamerican", "color": "#a78bfa"},
    {"name": "National Museum of World Cultures - Osaka", "lat": 34.6548, "lon": 135.4223,
     "desc": "Japanese museum of ethnology with masks from Africa, Oceania, the Americas, and Asia.",
     "region": "Osaka, Japan", "specialty": "World Masks", "color": "#fb7185"},
    {"name": "Tropenmuseum - Amsterdam", "lat": 52.3627, "lon": 4.9223,
     "desc": "Museum of the tropics with Indonesian, African, and Surinamese mask collections.",
     "region": "Amsterdam, Netherlands", "specialty": "Indonesian & African", "color": "#2dd4bf"},
    {"name": "Museu Nacional de Etnologia - Lisbon", "lat": 38.6931, "lon": -9.2100,
     "desc": "Portuguese ethnology museum with masks from former colonies including Mozambique and Brazil.",
     "region": "Lisbon, Portugal", "specialty": "Lusophone World", "color": "#64748b"},
    {"name": "Field Museum of Natural History - Chicago", "lat": 41.8663, "lon": -87.6170,
     "desc": "Major natural history museum with extensive Pacific, African, and Native American mask holdings.",
     "region": "Chicago, USA", "specialty": "Pacific & Native American", "color": "#84cc16"},
]

# ═══════════════════════════════════════════
# MODE -> DATA MAP
# ═══════════════════════════════════════════
MODE_DATA = {
    "Venetian Masks": VENETIAN_MASKS,
    "African Masks": AFRICAN_MASKS,
    "Japanese Noh & Kabuki Masks": JAPANESE_NOH_KABUKI,
    "Day of the Dead Masks": DAY_OF_THE_DEAD,
    "Native American Masks": NATIVE_AMERICAN_MASKS,
    "Asian Temple Masks": ASIAN_TEMPLE_MASKS,
    "Carnival Masks Worldwide": CARNIVAL_MASKS_WORLDWIDE,
    "Shamanic & Ritual Masks": SHAMANIC_RITUAL_MASKS,
    "Ancient Masks": ANCIENT_MASKS,
    "Mask Museums & Collections": MASK_MUSEUMS,
}

MODE_DESCRIPTIONS = {
    "Venetian Masks": "Venice's legendary mask-making workshops, carnival stages, and masked ball venues from the bauta to the moretta.",
    "African Masks": "Sacred ceremonial masks of Africa from Dogon Kanaga to Fang Ngil, Yoruba Gelede, and Kuba royal masks.",
    "Japanese Noh & Kabuki Masks": "Traditional Japanese Noh theaters, kabuki stages, mask carvers, and sacred Kagura performances.",
    "Day of the Dead Masks": "Mexico's Dia de los Muertos calavera masks, cemetery vigils, ofrenda altars, and Catrina traditions.",
    "Native American Masks": "Pacific Northwest transformation masks, Hopi kachina, Iroquois False Face, and Tlingit clan crests.",
    "Asian Temple Masks": "Balinese Barong, Thai Khon, Korean Hahoe, Sri Lankan Kolam, Himalayan Cham, and Kathakali traditions.",
    "Carnival Masks Worldwide": "From Rio to Mardi Gras, Basel Fasnacht, Trinidad Mas, Oruro Diablada, and Viareggio's papier-mache giants.",
    "Shamanic & Ritual Masks": "Siberian shamans, Himalayan healers, Amazonian ayahuasca masks, Aboriginal Dreamtime, and Vodou traditions.",
    "Ancient Masks": "Tutankhamun's gold mask, Mycenaean funeral masks, Roman theater masks, Mesoamerican jade, and Sanxingdui bronze.",
    "Mask Museums & Collections": "World-class mask collections at the Met, Quai Branly, British Museum, Tokyo National Museum, and beyond.",
}

MODE_COLORS = {
    "Venetian Masks": "#8b5cf6",
    "African Masks": "#f59e0b",
    "Japanese Noh & Kabuki Masks": "#ef4444",
    "Day of the Dead Masks": "#ec4899",
    "Native American Masks": "#10b981",
    "Asian Temple Masks": "#06b6d4",
    "Carnival Masks Worldwide": "#a855f7",
    "Shamanic & Ritual Masks": "#d946ef",
    "Ancient Masks": "#f97316",
    "Mask Museums & Collections": "#14b8a6",
}


# ═══════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════

def _build_map(items: list, mode: str) -> folium.Map:
    """Build a Folium dark-theme map with MarkerCluster for the given items."""
    if not items:
        return folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    avg_lat = sum(it["lat"] for it in items) / len(items)
    avg_lon = sum(it["lon"] for it in items) / len(items)

    # Venetian masks are all in Venice, zoom in more
    zoom = 13 if mode == "Venetian Masks" else 3

    m = folium.Map(
        location=[avg_lat, avg_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    cluster = MarkerCluster(name=mode).add_to(m)

    for item in items:
        name_safe = html_module.escape(item["name"])
        desc_safe = html_module.escape(item["desc"])
        color = item.get("color", "#06b6d4")

        extra_lines = ""
        if "region" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Region: {html_module.escape(item["region"])}</span>'
        if "mask_type" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Mask Type: {html_module.escape(item["mask_type"])}</span>'
        if "tradition" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Tradition: {html_module.escape(item["tradition"])}</span>'
        if "specialty" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Specialty: {html_module.escape(item["specialty"])}</span>'
        if "country" in item:
            extra_lines += f'<br/><span style="font-size:0.8rem;">Country: {html_module.escape(item["country"])}</span>'

        popup_html = f"""
        <div style="max-width:240px;">
            <strong style="color:{color};">{name_safe}</strong>
            {extra_lines}
            <br/><span style="font-size:0.78rem; color:#555;">{desc_safe}</span>
            <br/><span style="font-size:0.72rem; color:#888;">{item['lat']:.4f}, {item['lon']:.4f}</span>
        </div>
        """

        folium.CircleMarker(
            location=[item["lat"], item["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=name_safe,
        ).add_to(cluster)

    return m


def _build_dataframe(items: list, mode: str) -> pd.DataFrame:
    """Build a display DataFrame from item list."""
    rows = []
    for item in items:
        row = {
            "Name": item["name"],
            "Latitude": item["lat"],
            "Longitude": item["lon"],
            "Description": item["desc"],
        }
        if "region" in item:
            row["Region"] = item["region"]
        if "mask_type" in item:
            row["Mask Type"] = item["mask_type"]
        if "tradition" in item:
            row["Tradition"] = item["tradition"]
        if "specialty" in item:
            row["Specialty"] = item["specialty"]
        if "country" in item:
            row["Country"] = item["country"]
        rows.append(row)
    return pd.DataFrame(rows)


def _get_csv(df: pd.DataFrame) -> str:
    """Convert DataFrame to CSV string."""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════

def render_mask_maps_tab():
    """Main render function for the Masks & Ceremonial Art Explorer tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header violet">
        <h4>Masks & Ceremonial Art Explorer</h4>
        <p>Discover the world's mask traditions &mdash; from Venetian carnival to African ceremonial masks, Japanese Noh theater, Day of the Dead, shamanic rituals, ancient death masks, and the greatest museum collections.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Mode Selection
    # ══════════════════════════════════════════
    mode = st.selectbox(
        "Mask Map Mode",
        MODE_OPTIONS,
        key="mask_maps_mode",
        help="Choose a mask tradition category to explore on the map.",
    )

    mode_desc = MODE_DESCRIPTIONS.get(mode, "")
    mode_color = MODE_COLORS.get(mode, "#06b6d4")
    st.markdown(
        f'<p style="color:#8b97b0; font-size:0.85rem;"><span style="color:{mode_color};">&#9673;</span> {html_module.escape(mode_desc)}</p>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════
    # SECTION 2: Load Data
    # ══════════════════════════════════════════
    items = MODE_DATA.get(mode, [])

    if not items:
        st.warning("No data available for this mode.")
        return

    # ══════════════════════════════════════════
    # SECTION 3: Stats Row
    # ══════════════════════════════════════════
    st.markdown("---")

    regions = set(it.get("region", "") for it in items if it.get("region"))
    traditions = set(it.get("tradition", it.get("mask_type", it.get("specialty", ""))) for it in items)
    traditions.discard("")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Locations", len(items))
    with c2:
        st.metric("Regions", len(regions))
    with c3:
        st.metric("Distinct Traditions", len(traditions))
    with c4:
        lat_range = max(it["lat"] for it in items) - min(it["lat"] for it in items)
        st.metric("Lat Spread", f"{lat_range:.1f}\u00b0")

    # ══════════════════════════════════════════
    # SECTION 4: Interactive Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {html_module.escape(mode)} Map")

    # Legend
    legend_items = " ".join(
        f'<span style="color:{it["color"]}; font-size:0.8rem;">\u25cf {html_module.escape(it["name"][:30])}</span>'
        for it in items[:12]
    )
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">{legend_items}</div>',
        unsafe_allow_html=True,
    )

    m = _build_map(items, mode)
    st_html(m._repr_html_(), height=500)

    # ══════════════════════════════════════════
    # SECTION 5: Data Table
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Location Data")

    df = _build_dataframe(items, mode)

    with st.expander(f"Full Data Table ({len(df)} entries)", expanded=False):
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 6: Notable Entries Cards
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Highlights")

    for item in items[:10]:
        name_safe = html_module.escape(item["name"])
        desc_safe = html_module.escape(item["desc"])
        color = item.get("color", "#06b6d4")

        sub_info = ""
        if "region" in item:
            sub_info += html_module.escape(item["region"])
        if "mask_type" in item:
            sub_info += f" &mdash; {html_module.escape(item['mask_type'])}"
        if "tradition" in item:
            sub_info += f" &mdash; {html_module.escape(item['tradition'])}"
        if "specialty" in item:
            sub_info += f" &mdash; {html_module.escape(item['specialty'])}"

        st.markdown(f"""
        <div class="bio-card" style="display:flex; align-items:center; margin-bottom:0.5rem;">
            <div style="width:10px; height:56px; border-radius:5px; background:{color};
                        margin-right:0.75rem; flex-shrink:0;"></div>
            <div>
                <div style="color:#e8ecf4; font-weight:600; font-size:0.85rem;">{name_safe}</div>
                <div style="color:#8b97b0; font-size:0.75rem;">{sub_info}</div>
                <div style="color:#5a6580; font-size:0.7rem;">{desc_safe[:140]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 7: CSV Download
    # ══════════════════════════════════════════
    st.markdown("---")

    csv_data = _get_csv(df)
    filename = mode.lower().replace(" ", "_").replace("&", "and")
    st.download_button(
        f"Download {len(df)} {mode} Locations (CSV)",
        data=csv_data,
        file_name=f"mask_maps_{filename}.csv",
        mime="text/csv",
        key="mask_maps_download",
    )
