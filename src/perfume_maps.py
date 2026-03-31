# -*- coding: utf-8 -*-
"""
Perfume & Fragrance Maps module for TerraScout AI.
Explore the world of scents, perfume houses, aromatic plants, and fragrance history.
Provides 10 curated map modes with hardcoded data covering 180+ locations globally.
"""

import streamlit as st
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
from streamlit.components.v1 import html as st_html
import pandas as pd
import requests
import html as html_module


# ---------------------------------------------------------------------------
# Mode descriptions shown under the map title
# ---------------------------------------------------------------------------

MODE_DESCRIPTIONS = {
    "Historic Perfume Houses": (
        "Explore the world's most legendary perfume houses, from the 18th-century "
        "ateliers of London and Paris to modern niche powerhouses. Each marker "
        "represents a house that has shaped the art of perfumery through centuries "
        "of craftsmanship, innovation, and olfactory storytelling."
    ),
    "Grasse & French Perfume Capital": (
        "Grasse, nestled in the hills of Provence, has been the perfume capital of "
        "the world since the Renaissance. This mode maps the perfumeries, flower "
        "fields, museums, and workshops that make this small French town the "
        "beating heart of global fragrance production."
    ),
    "Aromatic Plant Regions": (
        "From the rose valleys of Bulgaria to the ylang-ylang groves of Madagascar, "
        "aromatic plants are cultivated in specific microclimates around the globe. "
        "This mode maps the key growing regions that supply the raw materials for "
        "the world's finest perfumes."
    ),
    "Incense & Resin Origins": (
        "Frankincense, myrrh, oud, sandalwood, and benzoin have been traded for "
        "millennia. This mode traces the geographic origins of the world's most "
        "precious aromatic resins and woods, from the Dhofar mountains of Oman to "
        "the agarwood forests of Southeast Asia."
    ),
    "Perfume Museums": (
        "Dedicated museums, historic pharmacies, and fragrance conservatories "
        "preserve thousands of years of perfumery heritage. Visit the Osmotheque "
        "in Versailles, the Farina Museum in Cologne, or the ancient Officina "
        "Profumo Farmaceutica di Santa Maria Novella in Florence."
    ),
    "Essential Oil Distilleries": (
        "Steam distillation, solvent extraction, and cold pressing transform raw "
        "plant material into the concentrated essences used by perfumers. This mode "
        "maps the major distillation and production centers for essential oils "
        "around the world."
    ),
    "Spice & Scent Routes": (
        "For millennia, spices and aromatics were among the most valuable trade "
        "goods on Earth. This mode traces the ancient and medieval trade routes "
        "that connected the cinnamon coasts of Ceylon, the pepper hills of Malabar, "
        "the saffron fields of Persia, and the spice bazaars of Constantinople."
    ),
    "Niche Perfumery Capitals": (
        "Beyond the mass market, a vibrant world of niche and artisanal perfumery "
        "thrives in select cities. From the oud souks of the Arabian Gulf to the "
        "attar distillers of Kannauj and the indie boutiques of New York and Berlin, "
        "these are the global capitals of bespoke scent."
    ),
    "Flower Markets & Gardens": (
        "Flower markets and botanical gardens have long been sources of inspiration "
        "and raw materials for perfumers. From the massive Aalsmeer auction to the "
        "Sunday stalls of Columbia Road and the floating Bloemenmarkt of Amsterdam, "
        "these are the world's most fragrant destinations."
    ),
    "Ancient Perfumery Sites": (
        "Perfumery is one of humanity's oldest arts. Archaeological sites from "
        "Bronze Age Cyprus to Pharaonic Egypt, from Minoan Crete to Roman Pompeii, "
        "reveal a world where scent was sacred, medicinal, and deeply woven into "
        "the fabric of daily life."
    ),
}


# ---------------------------------------------------------------------------
# Color palette for each mode
# ---------------------------------------------------------------------------

MODE_COLORS = {
    "Historic Perfume Houses": "#e91e90",
    "Grasse & French Perfume Capital": "#ff69b4",
    "Aromatic Plant Regions": "#22c55e",
    "Incense & Resin Origins": "#d4a017",
    "Perfume Museums": "#a855f7",
    "Essential Oil Distilleries": "#06b6d4",
    "Spice & Scent Routes": "#f97316",
    "Niche Perfumery Capitals": "#ec4899",
    "Flower Markets & Gardens": "#f43f5e",
    "Ancient Perfumery Sites": "#c4a35a",
}

MODE_ICONS = {
    "Historic Perfume Houses": "\U0001f3db\ufe0f",
    "Grasse & French Perfume Capital": "\U0001f33b",
    "Aromatic Plant Regions": "\U0001f33f",
    "Incense & Resin Origins": "\U0001f9f4",
    "Perfume Museums": "\U0001f3db\ufe0f",
    "Essential Oil Distilleries": "\U0001f52c",
    "Spice & Scent Routes": "\U0001f6e3\ufe0f",
    "Niche Perfumery Capitals": "\U0001f3ea",
    "Flower Markets & Gardens": "\U0001f490",
    "Ancient Perfumery Sites": "\U0001f3fa",
}


# ---------------------------------------------------------------------------
# Data helpers - 10 curated datasets
# ---------------------------------------------------------------------------

def _historic_perfume_houses():
    """Curated list of 22 historic and iconic perfume houses worldwide."""
    return [
        {"name": "Chanel", "city": "Paris", "country": "France",
         "lat": 48.8698, "lon": 2.3078, "founded": 1910,
         "famous_scent": "No. 5",
         "notes": "Founded by Coco Chanel; No. 5 is the best-selling perfume in history"},
        {"name": "Guerlain", "city": "Paris", "country": "France",
         "lat": 48.8672, "lon": 2.3280, "founded": 1828,
         "famous_scent": "Shalimar",
         "notes": "Oldest French perfume house still in operation"},
        {"name": "Dior Parfums", "city": "Grasse", "country": "France",
         "lat": 43.6580, "lon": 6.9230, "founded": 1947,
         "famous_scent": "Miss Dior",
         "notes": "Les Fontaines Parfumees estate in Grasse"},
        {"name": "Hermes Parfums", "city": "Paris", "country": "France",
         "lat": 48.8686, "lon": 2.3210, "founded": 1951,
         "famous_scent": "Terre d'Hermes",
         "notes": "Luxury house with dedicated in-house perfumer Jean-Claude Ellena"},
        {"name": "Creed", "city": "London", "country": "United Kingdom",
         "lat": 51.5074, "lon": -0.1410, "founded": 1760,
         "famous_scent": "Aventus",
         "notes": "Claims heritage dating to 1760; royal warrants"},
        {"name": "Tom Ford Beauty", "city": "New York", "country": "United States",
         "lat": 40.7648, "lon": -73.9730, "founded": 2006,
         "famous_scent": "Black Orchid",
         "notes": "Luxury niche-mainstream crossover brand"},
        {"name": "Amouage", "city": "Muscat", "country": "Oman",
         "lat": 23.5880, "lon": 58.3829, "founded": 1983,
         "famous_scent": "Interlude",
         "notes": "Founded by the Sultan of Oman; uses rare Arabian ingredients"},
        {"name": "Acqua di Parma", "city": "Parma", "country": "Italy",
         "lat": 44.8015, "lon": 10.3279, "founded": 1916,
         "famous_scent": "Colonia",
         "notes": "Iconic Italian citrus fragrance house"},
        {"name": "Penhaligon's", "city": "London", "country": "United Kingdom",
         "lat": 51.5110, "lon": -0.1350, "founded": 1870,
         "famous_scent": "Halfeti",
         "notes": "British perfumery with royal warrants since 1903"},
        {"name": "Floris London", "city": "London", "country": "United Kingdom",
         "lat": 51.5088, "lon": -0.1369, "founded": 1730,
         "famous_scent": "No. 89",
         "notes": "Oldest English retailer of perfume, royal warrant holder"},
        {"name": "Roger & Gallet", "city": "Paris", "country": "France",
         "lat": 48.8606, "lon": 2.3376, "founded": 1862,
         "famous_scent": "Jean Marie Farina",
         "notes": "Historic Parisian fragrance and soap house"},
        {"name": "Caron", "city": "Paris", "country": "France",
         "lat": 48.8738, "lon": 2.3042, "founded": 1904,
         "famous_scent": "Tabac Blond",
         "notes": "Known for its urns of powder and classic French perfumery"},
        {"name": "Jean Patou / Joy", "city": "Paris", "country": "France",
         "lat": 48.8680, "lon": 2.3090, "founded": 1925,
         "famous_scent": "Joy",
         "notes": "Joy was once called the costliest perfume in the world"},
        {"name": "Givenchy Parfums", "city": "Paris", "country": "France",
         "lat": 48.8660, "lon": 2.3100, "founded": 1957,
         "famous_scent": "L'Interdit",
         "notes": "First fragrance created exclusively for Audrey Hepburn"},
        {"name": "Gucci Parfums", "city": "Florence", "country": "Italy",
         "lat": 43.7696, "lon": 11.2558, "founded": 1974,
         "famous_scent": "Bloom",
         "notes": "Italian luxury house with Alberto Morillas as perfumer"},
        {"name": "Bulgari Parfums", "city": "Rome", "country": "Italy",
         "lat": 41.9050, "lon": 12.4800, "founded": 1992,
         "famous_scent": "Omnia",
         "notes": "Roman jeweler turned fragrance powerhouse"},
        {"name": "Serge Lutens", "city": "Marrakech", "country": "Morocco",
         "lat": 31.6295, "lon": -7.9811, "founded": 2000,
         "famous_scent": "Ambre Sultan",
         "notes": "Artistic niche house with a riad-boutique in Marrakech"},
        {"name": "Frederic Malle", "city": "Paris", "country": "France",
         "lat": 48.8575, "lon": 2.3514, "founded": 2000,
         "famous_scent": "Portrait of a Lady",
         "notes": "Editions de Parfums concept: perfumer as auteur"},
        {"name": "Byredo", "city": "Stockholm", "country": "Sweden",
         "lat": 59.3293, "lon": 18.0686, "founded": 2006,
         "famous_scent": "Gypsy Water",
         "notes": "Swedish minimalist niche house by Ben Gorham"},
        {"name": "Maison Francis Kurkdjian", "city": "Paris", "country": "France",
         "lat": 48.8640, "lon": 2.3310, "founded": 2009,
         "famous_scent": "Baccarat Rouge 540",
         "notes": "Founded by master perfumer Francis Kurkdjian"},
        {"name": "Xerjoff", "city": "Turin", "country": "Italy",
         "lat": 45.0703, "lon": 7.6869, "founded": 2003,
         "famous_scent": "Naxos",
         "notes": "Ultra-luxury Italian niche house with Murano glass bottles"},
        {"name": "Clive Christian", "city": "London", "country": "United Kingdom",
         "lat": 51.5130, "lon": -0.1500, "founded": 1999,
         "famous_scent": "No. 1",
         "notes": "No. 1 once held Guinness record for most expensive perfume"},
    ]


def _grasse_perfume_capital():
    """Grasse and surrounding French perfume capital - 16 locations."""
    return [
        {"name": "Fragonard Perfumery", "type": "Perfume House",
         "lat": 43.6590, "lon": 6.9227,
         "description": "Historic perfumery with factory tours and museum",
         "specialty": "Traditional Grassois perfumery"},
        {"name": "Galimard Perfumery", "type": "Perfume House",
         "lat": 43.6588, "lon": 6.9235,
         "description": "Founded 1747, one of the oldest perfumeries in Grasse",
         "specialty": "Bespoke fragrance workshops"},
        {"name": "Molinard Perfumery", "type": "Perfume House",
         "lat": 43.6583, "lon": 6.9220,
         "description": "Family perfumery since 1849 in Art Deco building",
         "specialty": "Tailor-made fragrances"},
        {"name": "Musee International de la Parfumerie", "type": "Museum",
         "lat": 43.6601, "lon": 6.9228,
         "description": "World-class museum covering 5000 years of perfume history",
         "specialty": "Historical artifacts and raw materials"},
        {"name": "Jardins du MIP", "type": "Garden",
         "lat": 43.6460, "lon": 6.9410,
         "description": "Botanical gardens of the perfumery museum with fragrant plants",
         "specialty": "Rose, jasmine, tuberose, lavender fields"},
        {"name": "Domaine de Manon", "type": "Flower Farm",
         "lat": 43.6520, "lon": 6.9350,
         "description": "Traditional rose and jasmine fields for perfumery",
         "specialty": "Rose de Mai and Jasmine grandiflorum"},
        {"name": "Robertet SA", "type": "Ingredient Supplier",
         "lat": 43.6575, "lon": 6.9260,
         "description": "Global leader in natural raw materials for perfumery",
         "specialty": "Natural essential oils and absolutes"},
        {"name": "Mougins Village", "type": "Historic Village",
         "lat": 43.6006, "lon": 6.9952,
         "description": "Medieval hilltop village near Grasse, artistic heritage",
         "specialty": "Gastronomy and art galleries"},
        {"name": "Plateau de Valensole", "type": "Lavender Field",
         "lat": 43.8374, "lon": 5.9826,
         "description": "Iconic lavender plateau of Provence",
         "specialty": "Lavandula angustifolia for perfumery"},
        {"name": "Champ de Centifolia Roses", "type": "Rose Field",
         "lat": 43.6550, "lon": 6.9300,
         "description": "Rose centifolia cultivation fields around Grasse",
         "specialty": "May rose harvest for absolute extraction"},
        {"name": "Art Parfum Grasse", "type": "Workshop",
         "lat": 43.6595, "lon": 6.9215,
         "description": "Boutique perfume creation workshop for visitors",
         "specialty": "Custom fragrance blending"},
        {"name": "Grasse Cathedral", "type": "Landmark",
         "lat": 43.6598, "lon": 6.9233,
         "description": "12th-century cathedral in the heart of old Grasse",
         "specialty": "Historic center of perfume capital"},
        {"name": "Usine Historique de Grasse", "type": "Historic Factory",
         "lat": 43.6570, "lon": 6.9250,
         "description": "19th-century perfume factory buildings in old town",
         "specialty": "Industrial perfumery heritage"},
        {"name": "Jasmine Fields of Pegomas", "type": "Flower Farm",
         "lat": 43.5970, "lon": 6.9320,
         "description": "Jasmine grandiflorum cultivation near Grasse",
         "specialty": "Night-harvested jasmine for absolutes"},
        {"name": "Parfumerie Aire de Grasse", "type": "Perfume House",
         "lat": 43.6560, "lon": 6.9200,
         "description": "Artisan perfumer using traditional Grasse techniques",
         "specialty": "Small-batch artisanal fragrances"},
        {"name": "Fete du Jasmin Site", "type": "Festival Ground",
         "lat": 43.6592, "lon": 6.9225,
         "description": "Annual jasmine festival held every August in Grasse",
         "specialty": "Celebrates jasmine harvest tradition"},
    ]


def _aromatic_plant_regions():
    """Major aromatic plant cultivation regions worldwide - 20 locations."""
    return [
        {"name": "Bulgarian Rose Valley (Kazanlak)", "plant": "Rosa damascena",
         "country": "Bulgaria", "lat": 42.6190, "lon": 25.3990,
         "use": "Rose absolute and otto",
         "notes": "Valley of Roses; produces 85% of world's rose oil"},
        {"name": "Moroccan Neroli (Khemisset)", "plant": "Citrus aurantium",
         "country": "Morocco", "lat": 33.8240, "lon": -6.0660,
         "use": "Neroli and orange blossom absolute",
         "notes": "Bitter orange groves for neroli distillation"},
        {"name": "Indian Jasmine (Madurai)", "plant": "Jasminum sambac",
         "country": "India", "lat": 9.9252, "lon": 78.1198,
         "use": "Jasmine absolute and concrete",
         "notes": "Tamil Nadu is the largest jasmine producer"},
        {"name": "Italian Bergamot (Calabria)", "plant": "Citrus bergamia",
         "country": "Italy", "lat": 38.1100, "lon": 15.6600,
         "use": "Bergamot essential oil",
         "notes": "Reggio Calabria produces 90% of the world's bergamot"},
        {"name": "Provence Lavender (Valensole)", "plant": "Lavandula angustifolia",
         "country": "France", "lat": 43.8374, "lon": 5.9826,
         "use": "Lavender essential oil",
         "notes": "AOC-protected haute-Provence lavender"},
        {"name": "Turkish Rose (Isparta)", "plant": "Rosa damascena",
         "country": "Turkey", "lat": 37.7640, "lon": 30.5520,
         "use": "Rose oil and rosewater",
         "notes": "Second largest rose oil producer after Bulgaria"},
        {"name": "Egyptian Jasmine (Gharbia)", "plant": "Jasminum grandiflorum",
         "country": "Egypt", "lat": 30.8700, "lon": 31.0300,
         "use": "Jasmine absolute",
         "notes": "Major supplier of jasmine grandiflorum absolute"},
        {"name": "Sri Lankan Cinnamon (Galle)", "plant": "Cinnamomum verum",
         "country": "Sri Lanka", "lat": 6.0535, "lon": 80.2210,
         "use": "Cinnamon bark oil",
         "notes": "True Ceylon cinnamon, prized in perfumery"},
        {"name": "Ylang-Ylang (Nosy Be, Madagascar)", "plant": "Cananga odorata",
         "country": "Madagascar", "lat": -13.3340, "lon": 48.2630,
         "use": "Ylang-ylang essential oil",
         "notes": "Perfume-grade ylang-ylang extra"},
        {"name": "Haitian Vetiver (Les Cayes)", "plant": "Chrysopogon zizanioides",
         "country": "Haiti", "lat": 18.1940, "lon": -73.7500,
         "use": "Vetiver essential oil",
         "notes": "Considered the finest vetiver for perfumery"},
        {"name": "Patchouli (Sulawesi, Indonesia)", "plant": "Pogostemon cablin",
         "country": "Indonesia", "lat": -1.4300, "lon": 121.4500,
         "use": "Patchouli essential oil",
         "notes": "Indonesia produces 90% of the world's patchouli"},
        {"name": "Iranian Damask Rose (Kashan)", "plant": "Rosa damascena",
         "country": "Iran", "lat": 33.9850, "lon": 51.4100,
         "use": "Rosewater and rose absolute",
         "notes": "Qamsar village famous for ancient rosewater distillation"},
        {"name": "Tunisian Neroli (Nabeul)", "plant": "Citrus aurantium",
         "country": "Tunisia", "lat": 36.4510, "lon": 10.7370,
         "use": "Neroli essential oil",
         "notes": "Cap Bon peninsula bigarade orange groves"},
        {"name": "Comoros Ylang-Ylang", "plant": "Cananga odorata",
         "country": "Comoros", "lat": -12.2360, "lon": 44.3370,
         "use": "Ylang-ylang essential oil",
         "notes": "Islands historically dominated ylang production"},
        {"name": "Chinese Osmanthus (Guilin)", "plant": "Osmanthus fragrans",
         "country": "China", "lat": 25.2740, "lon": 110.2900,
         "use": "Osmanthus absolute",
         "notes": "Guilin means Forest of Sweet Osmanthus"},
        {"name": "Sicilian Lemon (Syracuse)", "plant": "Citrus limon",
         "country": "Italy", "lat": 37.0755, "lon": 15.2866,
         "use": "Lemon essential oil",
         "notes": "Cold-pressed Sicilian lemon for top notes"},
        {"name": "Indian Sandalwood (Mysore)", "plant": "Santalum album",
         "country": "India", "lat": 12.2958, "lon": 76.6394,
         "use": "Sandalwood essential oil",
         "notes": "Mysore sandalwood is the gold standard"},
        {"name": "Australian Tea Tree (NSW)", "plant": "Melaleuca alternifolia",
         "country": "Australia", "lat": -29.0500, "lon": 153.0700,
         "use": "Tea tree essential oil",
         "notes": "Northern NSW major production region"},
        {"name": "Paraguayan Petitgrain", "plant": "Citrus aurantium",
         "country": "Paraguay", "lat": -25.2637, "lon": -57.5759,
         "use": "Petitgrain essential oil",
         "notes": "Paraguay is the top petitgrain producer"},
        {"name": "Reunion Island Geranium", "plant": "Pelargonium graveolens",
         "country": "Reunion (France)", "lat": -21.1151, "lon": 55.5364,
         "use": "Geranium bourbon essential oil",
         "notes": "Bourbon geranium prized for rosy sweetness"},
    ]


def _incense_resin_origins():
    """Origins of incense, resins, and precious aromatic woods - 20 locations."""
    return [
        {"name": "Frankincense Groves (Dhofar)", "material": "Frankincense (Boswellia sacra)",
         "country": "Oman", "lat": 17.0190, "lon": 54.0930,
         "trade_era": "3000+ years",
         "notes": "UNESCO World Heritage frankincense sites; finest Hojari grade"},
        {"name": "Myrrh Harvest (Sanaag)", "material": "Myrrh (Commiphora myrrha)",
         "country": "Somalia", "lat": 10.5000, "lon": 47.7600,
         "trade_era": "3000+ years",
         "notes": "Somali highlands are the primary myrrh source"},
        {"name": "Mysore Sandalwood Forests", "material": "Sandalwood (Santalum album)",
         "country": "India", "lat": 12.2958, "lon": 76.6394,
         "trade_era": "4000+ years",
         "notes": "Government-controlled; heartwood requires 30+ years to mature"},
        {"name": "Assam Oud Forests", "material": "Oud / Agarwood (Aquilaria malaccensis)",
         "country": "India", "lat": 26.1400, "lon": 91.7700,
         "trade_era": "2000+ years",
         "notes": "Northeast India produces prized Hindi oud"},
        {"name": "Cambodian Oud (Pursat)", "material": "Oud / Agarwood (Aquilaria crassna)",
         "country": "Cambodia", "lat": 12.5340, "lon": 103.9190,
         "trade_era": "1000+ years",
         "notes": "Pursat province known for distinctive sweet oud"},
        {"name": "Yemeni Frankincense (Hadramaut)", "material": "Frankincense (Boswellia sacra)",
         "country": "Yemen", "lat": 15.3500, "lon": 48.5000,
         "trade_era": "3000+ years",
         "notes": "Ancient Hadramaut kingdom was a frankincense trading center"},
        {"name": "Ethiopian Myrrh & Frankincense", "material": "Myrrh and Frankincense",
         "country": "Ethiopia", "lat": 9.1450, "lon": 40.4897,
         "trade_era": "2500+ years",
         "notes": "Ogaden and Tigray regions produce both resins"},
        {"name": "Vietnamese Oud (Khanh Hoa)", "material": "Oud / Agarwood (Aquilaria crassna)",
         "country": "Vietnam", "lat": 12.2585, "lon": 109.0526,
         "trade_era": "1500+ years",
         "notes": "Vietnam is a major oud oil producer and exporter"},
        {"name": "Indonesian Benzoin (Sumatra)", "material": "Benzoin resin (Styrax benzoin)",
         "country": "Indonesia", "lat": 2.5000, "lon": 99.0000,
         "trade_era": "1500+ years",
         "notes": "Sumatran benzoin (Siam type) with vanilla-like aroma"},
        {"name": "Socotra Dragon's Blood", "material": "Dragon's Blood (Dracaena cinnabari)",
         "country": "Yemen (Socotra)", "lat": 12.4634, "lon": 53.8237,
         "trade_era": "2000+ years",
         "notes": "Ancient resin from endemic dragon blood trees"},
        {"name": "Peruvian Balsam (El Salvador)", "material": "Balsam of Peru (Myroxylon balsamum)",
         "country": "El Salvador", "lat": 13.5450, "lon": -89.2000,
         "trade_era": "500+ years",
         "notes": "Despite the name, sourced primarily from El Salvador"},
        {"name": "Canadian Balsam Fir", "material": "Canada Balsam (Abies balsamea)",
         "country": "Canada", "lat": 47.5615, "lon": -72.7770,
         "trade_era": "400+ years",
         "notes": "Aromatic fir resin used in perfumery and incense"},
        {"name": "Japanese Hinoki (Kiso Valley)", "material": "Hinoki Cypress (Chamaecyparis obtusa)",
         "country": "Japan", "lat": 35.8400, "lon": 137.5600,
         "trade_era": "1000+ years",
         "notes": "Sacred wood used in temples; prized essential oil"},
        {"name": "Laotian Oud Forests", "material": "Oud / Agarwood (Aquilaria crassna)",
         "country": "Laos", "lat": 18.4960, "lon": 105.0000,
         "trade_era": "800+ years",
         "notes": "Wild agarwood from old-growth forests"},
        {"name": "Malaysian Oud (Pahang)", "material": "Oud / Agarwood (Aquilaria malaccensis)",
         "country": "Malaysia", "lat": 3.8126, "lon": 103.3256,
         "trade_era": "1000+ years",
         "notes": "Malaysian oud known for complex fruity-woody profile"},
        {"name": "Sudanese Olibanum", "material": "Frankincense (Boswellia papyrifera)",
         "country": "Sudan", "lat": 13.0000, "lon": 35.0000,
         "trade_era": "2000+ years",
         "notes": "Boswellia papyrifera in the western hills"},
        {"name": "Kenyan Frankincense (Turkana)", "material": "Frankincense (Boswellia neglecta)",
         "country": "Kenya", "lat": 3.3000, "lon": 36.0000,
         "trade_era": "1500+ years",
         "notes": "Northern Kenya produces neglecta species"},
        {"name": "Greek Mastic (Chios)", "material": "Mastic (Pistacia lentiscus)",
         "country": "Greece", "lat": 38.3680, "lon": 26.0400,
         "trade_era": "2500+ years",
         "notes": "Chios mastic is PDO-protected; tears of Chios"},
        {"name": "Australian Sandalwood (WA)", "material": "Sandalwood (Santalum spicatum)",
         "country": "Australia", "lat": -30.7500, "lon": 121.4700,
         "trade_era": "200+ years",
         "notes": "Sustainable plantation sandalwood alternative"},
        {"name": "Somaliland Frankincense (Erigavo)", "material": "Frankincense (Boswellia frereana)",
         "country": "Somaliland", "lat": 10.6170, "lon": 47.3640,
         "trade_era": "3000+ years",
         "notes": "Maydi frankincense, considered the king of frankincense"},
    ]


def _perfume_museums():
    """Perfume museums and exhibitions worldwide - 16 locations."""
    return [
        {"name": "Musee International de la Parfumerie", "city": "Grasse",
         "country": "France", "lat": 43.6601, "lon": 6.9228,
         "type": "Dedicated Museum",
         "highlights": "5000-year perfume history, raw materials, antique bottles"},
        {"name": "Fragonard Musee du Parfum", "city": "Paris",
         "country": "France", "lat": 48.8724, "lon": 2.3320,
         "type": "Brand Museum",
         "highlights": "Free admission; antique perfume organs, distillation apparatus"},
        {"name": "Osmotheque", "city": "Versailles",
         "country": "France", "lat": 48.8049, "lon": 2.1345,
         "type": "Fragrance Conservatory",
         "highlights": "Archive of 4000+ historic fragrances including lost perfumes"},
        {"name": "Museo del Profumo", "city": "Milan",
         "country": "Italy", "lat": 45.4642, "lon": 9.1900,
         "type": "Dedicated Museum",
         "highlights": "Italian perfumery heritage, artistic flacons"},
        {"name": "Firmenich Perfumery School", "city": "Geneva",
         "country": "Switzerland", "lat": 46.1884, "lon": 6.1300,
         "type": "School / Archive",
         "highlights": "One of the world's top perfumer training schools"},
        {"name": "Santa Maria Novella", "city": "Florence",
         "country": "Italy", "lat": 43.7745, "lon": 11.2490,
         "type": "Historic Pharmacy",
         "highlights": "Oldest pharmacy in Europe (1221), still producing fragrances"},
        {"name": "Cologne Fragrance Museum (Farina)", "city": "Cologne",
         "country": "Germany", "lat": 50.9367, "lon": 6.9570,
         "type": "Brand Museum",
         "highlights": "Birthplace of Eau de Cologne; Farina house since 1709"},
        {"name": "4711 House of Eau de Cologne", "city": "Cologne",
         "country": "Germany", "lat": 50.9380, "lon": 6.9490,
         "type": "Brand Museum",
         "highlights": "Iconic 4711 brand, historic Glockengasse shop"},
        {"name": "Museo de la Perfumeria (Figueres)", "city": "Figueres",
         "country": "Spain", "lat": 42.2666, "lon": 2.9616,
         "type": "Dedicated Museum",
         "highlights": "Perfume bottles and artifacts from antiquity to modern era"},
        {"name": "Kannauj Perfume Museum", "city": "Kannauj",
         "country": "India", "lat": 27.0550, "lon": 79.9200,
         "type": "Heritage Museum",
         "highlights": "Traditional Indian attar distillation heritage"},
        {"name": "Museum of Scent (NYC)", "city": "New York",
         "country": "United States", "lat": 40.7230, "lon": -73.9930,
         "type": "Interactive Museum",
         "highlights": "Immersive scent experiences and olfactory art"},
        {"name": "Tianjin Perfume Museum", "city": "Tianjin",
         "country": "China", "lat": 39.1235, "lon": 117.2000,
         "type": "Dedicated Museum",
         "highlights": "Chinese fragrance culture and incense traditions"},
        {"name": "Parfumerie Fragonard (Grasse Factory)", "city": "Grasse",
         "country": "France", "lat": 43.6590, "lon": 6.9227,
         "type": "Factory Museum",
         "highlights": "Working perfume factory with guided tours"},
        {"name": "Le Grand Musee du Parfum", "city": "Paris",
         "country": "France", "lat": 48.8620, "lon": 2.3080,
         "type": "Sensory Museum",
         "highlights": "Interactive olfactory journey in Faubourg Saint-Honore"},
        {"name": "Museo del Perfume (Barcelona)", "city": "Barcelona",
         "country": "Spain", "lat": 41.3954, "lon": 2.1510,
         "type": "Dedicated Museum",
         "highlights": "5000+ perfume bottles spanning Egyptian to modern eras"},
        {"name": "Arabian Perfume Museum (Sharjah)", "city": "Sharjah",
         "country": "UAE", "lat": 25.3573, "lon": 55.3880,
         "type": "Cultural Museum",
         "highlights": "Arabian perfumery traditions, oud and bukhoor culture"},
    ]


def _essential_oil_distilleries():
    """Essential oil distilleries and production centers - 20 locations."""
    return [
        {"name": "Lavender Distilleries (Sault)", "product": "Lavender Oil",
         "country": "France", "lat": 44.0940, "lon": 5.4080,
         "method": "Steam distillation",
         "notes": "High-altitude lavender fields of Vaucluse"},
        {"name": "Ylang-Ylang Distillery (Ambanja)", "product": "Ylang-Ylang Oil",
         "country": "Madagascar", "lat": -13.6825, "lon": 48.4494,
         "method": "Fractional steam distillation",
         "notes": "Extra, I, II, III grades by distillation time"},
        {"name": "Tea Tree Plantations (Bungawalbin)", "product": "Tea Tree Oil",
         "country": "Australia", "lat": -29.0700, "lon": 153.3200,
         "method": "Steam distillation",
         "notes": "Northern NSW commercial tea tree production"},
        {"name": "Peppermint Distilleries (Willamette Valley)", "product": "Peppermint Oil",
         "country": "United States", "lat": 44.6365, "lon": -123.1059,
         "method": "Steam distillation",
         "notes": "Oregon produces premium peppermint and spearmint oils"},
        {"name": "Eucalyptus Plantations (Blue Mountains)", "product": "Eucalyptus Oil",
         "country": "Australia", "lat": -33.7200, "lon": 150.3100,
         "method": "Steam distillation",
         "notes": "Eucalyptus globulus and radiata species"},
        {"name": "Rosemary Distillery (Tunisia)", "product": "Rosemary Oil",
         "country": "Tunisia", "lat": 36.8065, "lon": 10.1815,
         "method": "Steam distillation",
         "notes": "Tunisia is a major rosemary oil exporter"},
        {"name": "Clove Distilleries (Zanzibar)", "product": "Clove Oil",
         "country": "Tanzania", "lat": -6.1659, "lon": 39.1989,
         "method": "Steam distillation",
         "notes": "Zanzibar was historically called the Spice Island"},
        {"name": "Citronella Plantations (Java)", "product": "Citronella Oil",
         "country": "Indonesia", "lat": -7.6145, "lon": 110.7122,
         "method": "Steam distillation",
         "notes": "Java type citronella is higher quality than Sri Lankan"},
        {"name": "Neroli Distillery (Nabeul)", "product": "Neroli Oil",
         "country": "Tunisia", "lat": 36.4510, "lon": 10.7370,
         "method": "Steam distillation",
         "notes": "Spring bigarade orange blossom harvest"},
        {"name": "Vetiver Distillery (Reunion)", "product": "Vetiver Oil",
         "country": "Reunion (France)", "lat": -21.1151, "lon": 55.5364,
         "method": "Steam distillation",
         "notes": "Bourbon vetiver has distinctive smoky quality"},
        {"name": "Geranium Distillery (Grasse)", "product": "Geranium Oil",
         "country": "France", "lat": 43.6580, "lon": 6.9230,
         "method": "Steam distillation",
         "notes": "Rose geranium absolute from Grasse region"},
        {"name": "Sandalwood Distillery (Kununurra)", "product": "Sandalwood Oil",
         "country": "Australia", "lat": -15.7742, "lon": 128.7385,
         "method": "Steam distillation",
         "notes": "Sustainable Santalum album plantation distillation"},
        {"name": "Lemongrass Distillery (Cochin)", "product": "Lemongrass Oil",
         "country": "India", "lat": 9.9312, "lon": 76.2673,
         "method": "Steam distillation",
         "notes": "Kerala produces both East and West Indian types"},
        {"name": "Rose Distillery (Kazanlak)", "product": "Rose Otto",
         "country": "Bulgaria", "lat": 42.6190, "lon": 25.3990,
         "method": "Steam and solvent extraction",
         "notes": "3500 kg of petals yield 1 kg of rose otto"},
        {"name": "Cedarwood Distillery (Atlas Mountains)", "product": "Cedarwood Oil",
         "country": "Morocco", "lat": 32.3600, "lon": -4.9800,
         "method": "Steam distillation",
         "notes": "Atlas cedarwood (Cedrus atlantica) for perfumery"},
        {"name": "Patchouli Distillery (Sulawesi)", "product": "Patchouli Oil",
         "country": "Indonesia", "lat": -1.4300, "lon": 121.4500,
         "method": "Steam distillation",
         "notes": "Leaves are dried and fermented before distillation"},
        {"name": "Basil Distillery (Comoros)", "product": "Basil Oil",
         "country": "Comoros", "lat": -12.2360, "lon": 44.3370,
         "method": "Steam distillation",
         "notes": "Exotic basil (methyl chavicol type) from the islands"},
        {"name": "Black Pepper Distillery (Malabar)", "product": "Black Pepper Oil",
         "country": "India", "lat": 11.2588, "lon": 75.7804,
         "method": "Steam distillation",
         "notes": "Malabar coast pepper has been traded for millennia"},
        {"name": "Turmeric Distillery (Erode)", "product": "Turmeric Oil",
         "country": "India", "lat": 11.3410, "lon": 77.7172,
         "method": "Steam distillation",
         "notes": "Erode is the turmeric capital of the world"},
        {"name": "Chamomile Distillery (Norfolk)", "product": "Roman Chamomile Oil",
         "country": "United Kingdom", "lat": 52.6140, "lon": 0.8864,
         "method": "Steam distillation",
         "notes": "English chamomile from Norfolk lavender region"},
    ]


def _spice_scent_routes():
    """Historic spice and scent trade route locations - 20 locations."""
    return [
        {"name": "Cinnamon Coast (Galle)", "spice": "True Cinnamon",
         "country": "Sri Lanka", "lat": 6.0535, "lon": 80.2210,
         "era": "Ancient-Present",
         "notes": "Ceylon cinnamon, the original spice that drove trade"},
        {"name": "Vanilla Plantations (SAVA)", "spice": "Vanilla",
         "country": "Madagascar", "lat": -14.2700, "lon": 50.1700,
         "era": "19th century-Present",
         "notes": "Madagascar produces 80% of the world's vanilla"},
        {"name": "Saffron Fields (Khorasan)", "spice": "Saffron",
         "country": "Iran", "lat": 34.3000, "lon": 58.8000,
         "era": "3000+ years",
         "notes": "Iran produces 90% of the world's saffron"},
        {"name": "Zanzibar Spice Markets", "spice": "Cloves, Nutmeg, Pepper",
         "country": "Tanzania", "lat": -6.1659, "lon": 39.1989,
         "era": "Medieval-Present",
         "notes": "Historic Spice Island trading center"},
        {"name": "Banda Islands (Nutmeg)", "spice": "Nutmeg & Mace",
         "country": "Indonesia", "lat": -4.5250, "lon": 129.9000,
         "era": "Ancient-Present",
         "notes": "Original and only source of nutmeg for centuries"},
        {"name": "Pepper Coast (Malabar)", "spice": "Black Pepper",
         "country": "India", "lat": 11.2588, "lon": 75.7804,
         "era": "3000+ years",
         "notes": "Malabar pepper was once worth its weight in gold"},
        {"name": "Cardamom Hills (Idukki)", "spice": "Green Cardamom",
         "country": "India", "lat": 9.8500, "lon": 77.0000,
         "era": "Ancient-Present",
         "notes": "Queen of Spices from the Western Ghats"},
        {"name": "Star Anise Forests (Lang Son)", "spice": "Star Anise",
         "country": "Vietnam", "lat": 21.8500, "lon": 106.7500,
         "era": "Ancient-Present",
         "notes": "Vietnamese and Chinese highlands primary source"},
        {"name": "Petra (Incense Route)", "spice": "Frankincense, Myrrh",
         "country": "Jordan", "lat": 30.3285, "lon": 35.4444,
         "era": "300 BC - 200 AD",
         "notes": "Nabataean caravan city on the Incense Route"},
        {"name": "Alexandria (Spice Port)", "spice": "All Eastern Spices",
         "country": "Egypt", "lat": 31.2001, "lon": 29.9187,
         "era": "300 BC - Medieval",
         "notes": "Major Mediterranean spice trading port"},
        {"name": "Venice (Spice Republic)", "spice": "All Eastern Spices",
         "country": "Italy", "lat": 45.4408, "lon": 12.3155,
         "era": "Medieval",
         "notes": "Venice monopolized European spice trade for centuries"},
        {"name": "Malacca (Spice Strait)", "spice": "All Southeast Asian Spices",
         "country": "Malaysia", "lat": 2.1896, "lon": 102.2501,
         "era": "15th-17th century",
         "notes": "Strategic strait controlling spice trade routes"},
        {"name": "Hormuz (Persian Gulf)", "spice": "Frankincense, Oud, Spices",
         "country": "Iran", "lat": 27.0586, "lon": 56.4600,
         "era": "Ancient-Medieval",
         "notes": "Gateway between Arabian and Asian spice trade"},
        {"name": "Samarkand (Silk Road)", "spice": "All Central Asian Aromatics",
         "country": "Uzbekistan", "lat": 39.6270, "lon": 66.9750,
         "era": "Ancient-Medieval",
         "notes": "Key Silk Road hub for spice and fragrance trade"},
        {"name": "Aden (Incense Port)", "spice": "Frankincense, Myrrh",
         "country": "Yemen", "lat": 12.7855, "lon": 45.0187,
         "era": "Ancient-Medieval",
         "notes": "Southern Arabian port for incense export"},
        {"name": "Calicut (Spice Capital)", "spice": "Pepper, Cardamom, Ginger",
         "country": "India", "lat": 11.2588, "lon": 75.7804,
         "era": "Ancient-Medieval",
         "notes": "Vasco da Gama landed here seeking the spice trade"},
        {"name": "Mogadishu (Incense Trade)", "spice": "Frankincense, Myrrh",
         "country": "Somalia", "lat": 2.0469, "lon": 45.3182,
         "era": "Ancient-Medieval",
         "notes": "Horn of Africa incense trading port"},
        {"name": "Goa (Portuguese Spice Colony)", "spice": "Pepper, Cinnamon, Cloves",
         "country": "India", "lat": 15.4989, "lon": 73.8278,
         "era": "16th-18th century",
         "notes": "Portuguese colonial spice trading capital"},
        {"name": "Constantinople (Spice Bazaar)", "spice": "All Spices and Aromatics",
         "country": "Turkey", "lat": 41.0166, "lon": 28.9706,
         "era": "Medieval-Ottoman",
         "notes": "Egyptian Bazaar (Misir Carsisi) still sells spices today"},
        {"name": "Guangzhou (Canton)", "spice": "Chinese Aromatics, Camphor",
         "country": "China", "lat": 23.1291, "lon": 113.2644,
         "era": "Ancient-Present",
         "notes": "Major port on the Maritime Silk Road for aromatics"},
    ]


def _niche_perfumery_capitals():
    """Global capitals of niche and artisanal perfumery - 15 locations."""
    return [
        {"name": "Abu Dhabi Oud Souks", "city": "Abu Dhabi",
         "country": "UAE", "lat": 24.4539, "lon": 54.3773,
         "specialty": "Oud, Bukhoor, Bakhoor",
         "notes": "Arabian oud markets with premium Hindi and Cambodi oud"},
        {"name": "Kannauj Attar District", "city": "Kannauj",
         "country": "India", "lat": 27.0550, "lon": 79.9200,
         "specialty": "Traditional Attars",
         "notes": "India's perfume capital; 5000-year tradition of attar distillation"},
        {"name": "Grasse Artisan Quarter", "city": "Grasse",
         "country": "France", "lat": 43.6590, "lon": 6.9227,
         "specialty": "French Haute Parfumerie",
         "notes": "UNESCO Intangible Cultural Heritage of perfume-making"},
        {"name": "NYC Niche Perfume Scene", "city": "New York",
         "country": "United States", "lat": 40.7230, "lon": -73.9930,
         "specialty": "Indie & Niche Brands",
         "notes": "Luckyscent, MiN New York, Le Labo flagship, and dozens of niche boutiques"},
        {"name": "London Perfume Quarter", "city": "London",
         "country": "United Kingdom", "lat": 51.5074, "lon": -0.1350,
         "specialty": "British Niche Houses",
         "notes": "Penhaligon's, Jo Malone, Floris, Miller Harris, and more"},
        {"name": "Fez Medina Perfumers", "city": "Fez",
         "country": "Morocco", "lat": 34.0346, "lon": -5.0083,
         "specialty": "Moroccan Aromatics",
         "notes": "Traditional souks with rosewater, musk, and amber vendors"},
        {"name": "Dubai Perfume Souk", "city": "Dubai",
         "country": "UAE", "lat": 25.2680, "lon": 55.3002,
         "specialty": "Oud & Arabian Perfumery",
         "notes": "Gold and Spice Souks area with premium oud sellers"},
        {"name": "Florence Artisan Perfumeries", "city": "Florence",
         "country": "Italy", "lat": 43.7745, "lon": 11.2490,
         "specialty": "Renaissance Perfumery",
         "notes": "Santa Maria Novella, Aquaflor, Lorenzo Villoresi"},
        {"name": "Tokyo Niche Scene", "city": "Tokyo",
         "country": "Japan", "lat": 35.6762, "lon": 139.6503,
         "specialty": "Japanese Niche & Incense",
         "notes": "Nose Shop, Shoyeido incense, Japanese minimalist brands"},
        {"name": "Berlin Underground Perfumery", "city": "Berlin",
         "country": "Germany", "lat": 52.5200, "lon": 13.4050,
         "specialty": "Avant-Garde Niche",
         "notes": "Frau Tonis, J.F. Schwarzlose, concept perfume stores"},
        {"name": "Jeddah Oud Market", "city": "Jeddah",
         "country": "Saudi Arabia", "lat": 21.4858, "lon": 39.1925,
         "specialty": "Arabian Oud & Bukhoor",
         "notes": "Al-Balad historic district with centuries-old oud traders"},
        {"name": "Barcelona Perfume Boulevard", "city": "Barcelona",
         "country": "Spain", "lat": 41.3954, "lon": 2.1510,
         "specialty": "Spanish Niche",
         "notes": "Carner Barcelona, Loewe, and independent perfumers"},
        {"name": "Amsterdam Scent District", "city": "Amsterdam",
         "country": "Netherlands", "lat": 52.3676, "lon": 4.9041,
         "specialty": "Dutch Niche",
         "notes": "Skins Cosmetics, independent perfumers, and concept stores"},
        {"name": "Istanbul Spice Bazaar Perfumers", "city": "Istanbul",
         "country": "Turkey", "lat": 41.0166, "lon": 28.9706,
         "specialty": "Turkish Aromatics",
         "notes": "Misir Carsisi with rose, musk, and amber artisans"},
        {"name": "Los Angeles Indie Scene", "city": "Los Angeles",
         "country": "United States", "lat": 34.0522, "lon": -118.2437,
         "specialty": "California Niche",
         "notes": "DS & Durga pop-ups, Luckyscent, indie West Coast brands"},
    ]


def _flower_markets_gardens():
    """Famous flower markets and fragrance gardens worldwide - 15 locations."""
    return [
        {"name": "Aalsmeer Flower Auction", "city": "Aalsmeer",
         "country": "Netherlands", "lat": 52.2614, "lon": 4.7580,
         "type": "Auction / Market",
         "notes": "Largest flower auction in the world; 12 billion flowers annually"},
        {"name": "Columbia Road Flower Market", "city": "London",
         "country": "United Kingdom", "lat": 51.5295, "lon": -0.0720,
         "type": "Street Market",
         "notes": "Iconic Sunday flower market in East London"},
        {"name": "Kunming Flower Market (Dounan)", "city": "Kunming",
         "country": "China", "lat": 24.8960, "lon": 102.7500,
         "type": "Wholesale Market",
         "notes": "Asia's largest flower market; Yunnan is China's flower capital"},
        {"name": "Keukenhof Gardens", "city": "Lisse",
         "country": "Netherlands", "lat": 52.2697, "lon": 4.5462,
         "type": "Botanical Garden",
         "notes": "Garden of Europe: 7 million bulbs, world's largest flower garden"},
        {"name": "Marche aux Fleurs (Ile de la Cite)", "city": "Paris",
         "country": "France", "lat": 48.8562, "lon": 2.3467,
         "type": "Historic Market",
         "notes": "Parisian flower market since 1808 on Ile de la Cite"},
        {"name": "Kew Royal Botanic Gardens", "city": "London",
         "country": "United Kingdom", "lat": 51.4787, "lon": -0.2955,
         "type": "Botanical Garden",
         "notes": "UNESCO site with extensive fragrant plant collections"},
        {"name": "Jardin Majorelle", "city": "Marrakech",
         "country": "Morocco", "lat": 31.6418, "lon": -8.0032,
         "type": "Artist's Garden",
         "notes": "Yves Saint Laurent's garden with aromatic plants"},
        {"name": "Bangalore Flower Market (KR)", "city": "Bangalore",
         "country": "India", "lat": 12.9620, "lon": 77.5750,
         "type": "Wholesale Market",
         "notes": "Largest flower market in Asia; jasmine, roses, marigolds"},
        {"name": "Floating Flower Market (Bloemenmarkt)", "city": "Amsterdam",
         "country": "Netherlands", "lat": 52.3660, "lon": 4.8914,
         "type": "Floating Market",
         "notes": "World's only floating flower market on Singel canal"},
        {"name": "Mercado Jamaica", "city": "Mexico City",
         "country": "Mexico", "lat": 19.3722, "lon": -99.1396,
         "type": "Market",
         "notes": "Vibrant flower and plant market in Mexico City"},
        {"name": "Dalat Flower Gardens", "city": "Dalat",
         "country": "Vietnam", "lat": 11.9420, "lon": 108.4550,
         "type": "Flower Garden",
         "notes": "City of Flowers in the Vietnamese highlands"},
        {"name": "Namdaemun Flower Market", "city": "Seoul",
         "country": "South Korea", "lat": 37.5590, "lon": 126.9776,
         "type": "Wholesale Market",
         "notes": "Korea's largest flower market in historic Namdaemun area"},
        {"name": "Giardino di Boboli", "city": "Florence",
         "country": "Italy", "lat": 43.7628, "lon": 11.2480,
         "type": "Historic Garden",
         "notes": "Renaissance garden with aromatic herb sections"},
        {"name": "Butchart Gardens", "city": "Victoria",
         "country": "Canada", "lat": 48.5636, "lon": -123.4707,
         "type": "Display Garden",
         "notes": "100+ year-old gardens with fragrant rose garden section"},
        {"name": "Chelsea Physic Garden", "city": "London",
         "country": "United Kingdom", "lat": 51.4844, "lon": -0.1634,
         "type": "Botanical Garden",
         "notes": "London's oldest botanical garden (1673); perfumery plants section"},
    ]


def _ancient_perfumery_sites():
    """Archaeological sites related to ancient perfumery - 16 locations."""
    return [
        {"name": "Kyphi Temple Workshop (Edfu)", "civilization": "Ancient Egyptian",
         "country": "Egypt", "lat": 24.9779, "lon": 32.8734,
         "era": "300 BC",
         "notes": "Temple of Horus with kyphi incense recipe carved on walls"},
        {"name": "Perfume Workshop of Pompeii", "civilization": "Roman",
         "country": "Italy", "lat": 40.7509, "lon": 14.4869,
         "era": "79 AD (destroyed)",
         "notes": "Roman perfume shops (unguentarii) preserved by Vesuvius"},
        {"name": "Pyrgos Perfume Distillery (Cyprus)", "civilization": "Bronze Age",
         "country": "Cyprus", "lat": 34.7460, "lon": 33.2470,
         "era": "2000 BC",
         "notes": "Oldest known perfume factory; discovered 2004-2005"},
        {"name": "Hatshepsut Temple (Deir el-Bahari)", "civilization": "Ancient Egyptian",
         "country": "Egypt", "lat": 25.7381, "lon": 32.6075,
         "era": "1470 BC",
         "notes": "Reliefs depicting expedition to Land of Punt for myrrh trees"},
        {"name": "Delos Perfume Quarter", "civilization": "Ancient Greek",
         "country": "Greece", "lat": 37.3965, "lon": 25.2680,
         "era": "3rd century BC",
         "notes": "Island trade center with perfume workshops and storage"},
        {"name": "Ur Royal Tombs (Incense)", "civilization": "Sumerian",
         "country": "Iraq", "lat": 30.9627, "lon": 46.1031,
         "era": "2600 BC",
         "notes": "Gold incense containers and aromatic resins in royal tombs"},
        {"name": "Mohenjo-daro (Perfume Vessels)", "civilization": "Indus Valley",
         "country": "Pakistan", "lat": 27.3240, "lon": 68.1386,
         "era": "2500 BC",
         "notes": "Terracotta perfume vessels and distillation apparatus found"},
        {"name": "Karnak Temple (Incense Offerings)", "civilization": "Ancient Egyptian",
         "country": "Egypt", "lat": 25.7188, "lon": 32.6573,
         "era": "2000-300 BC",
         "notes": "Massive temple complex with daily incense burning rituals"},
        {"name": "Taxila (Gandhara Perfumery)", "civilization": "Gandhara",
         "country": "Pakistan", "lat": 33.7460, "lon": 72.7956,
         "era": "600 BC - 500 AD",
         "notes": "Ancient university city with perfumery trade connections"},
        {"name": "Knossos Palace (Fragrant Oils)", "civilization": "Minoan",
         "country": "Greece", "lat": 35.2979, "lon": 25.1630,
         "era": "1700 BC",
         "notes": "Linear B tablets record perfume recipes and trade"},
        {"name": "En Gedi (Ein Gedi) Balsam Works", "civilization": "Ancient Israelite",
         "country": "Israel", "lat": 31.4504, "lon": 35.3930,
         "era": "600 BC",
         "notes": "Biblical oasis known for opobalsam (Balm of Gilead) production"},
        {"name": "Capua Perfumers Quarter", "civilization": "Roman",
         "country": "Italy", "lat": 41.1063, "lon": 14.2121,
         "era": "2nd century BC",
         "notes": "Major Roman perfume manufacturing center, rival to Pompeii"},
        {"name": "Dhofar Frankincense Sites", "civilization": "Arabian",
         "country": "Oman", "lat": 17.0190, "lon": 54.0930,
         "era": "3000+ BC",
         "notes": "UNESCO-listed Land of Frankincense archaeological sites"},
        {"name": "Antioch Spice Markets", "civilization": "Hellenistic/Roman",
         "country": "Turkey", "lat": 36.2000, "lon": 36.1600,
         "era": "300 BC - 600 AD",
         "notes": "Major spice and perfume trading center of the ancient world"},
        {"name": "Medinet Habu (Ramesses III Temple)", "civilization": "Ancient Egyptian",
         "country": "Egypt", "lat": 25.7195, "lon": 32.6013,
         "era": "1150 BC",
         "notes": "Temple records of vast incense offerings and aromatic stores"},
        {"name": "Mycenae (Perfumed Oil Trade)", "civilization": "Mycenaean",
         "country": "Greece", "lat": 37.7306, "lon": 22.7563,
         "era": "1600-1100 BC",
         "notes": "Linear B tablets listing perfume ingredients and oil trade"},
    ]


# ---------------------------------------------------------------------------
# Cached data fetching
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def _fetch_mode_data(mode: str) -> list[dict]:
    """Return the curated dataset for the selected map mode."""
    dispatch = {
        "Historic Perfume Houses": _historic_perfume_houses,
        "Grasse & French Perfume Capital": _grasse_perfume_capital,
        "Aromatic Plant Regions": _aromatic_plant_regions,
        "Incense & Resin Origins": _incense_resin_origins,
        "Perfume Museums": _perfume_museums,
        "Essential Oil Distilleries": _essential_oil_distilleries,
        "Spice & Scent Routes": _spice_scent_routes,
        "Niche Perfumery Capitals": _niche_perfumery_capitals,
        "Flower Markets & Gardens": _flower_markets_gardens,
        "Ancient Perfumery Sites": _ancient_perfumery_sites,
    }
    fn = dispatch.get(mode)
    if fn is None:
        return []
    return fn()


# ---------------------------------------------------------------------------
# Popup builder
# ---------------------------------------------------------------------------

def _build_popup_html(row: dict, mode: str, color: str) -> str:
    """
    Build a styled HTML popup for a folium CircleMarker.
    All user content is escaped with html_module.escape() to prevent XSS.
    """
    safe = {
        k: html_module.escape(str(v))
        for k, v in row.items()
        if k not in ("lat", "lon")
    }

    title = safe.get("name", "Unknown")

    detail_lines: list[str] = []

    if mode == "Historic Perfume Houses":
        detail_lines.append(f"<b>City:</b> {safe.get('city', '')} &middot; <b>Country:</b> {safe.get('country', '')}")
        detail_lines.append(f"<b>Founded:</b> {safe.get('founded', '')}")
        detail_lines.append(f"<b>Famous Scent:</b> {safe.get('famous_scent', '')}")
        detail_lines.append(f"<b>Notes:</b> {safe.get('notes', '')}")

    elif mode == "Grasse & French Perfume Capital":
        detail_lines.append(f"<b>Type:</b> {safe.get('type', '')}")
        detail_lines.append(f"<b>Description:</b> {safe.get('description', '')}")
        detail_lines.append(f"<b>Specialty:</b> {safe.get('specialty', '')}")

    elif mode == "Aromatic Plant Regions":
        detail_lines.append(f"<b>Plant:</b> <i>{safe.get('plant', '')}</i>")
        detail_lines.append(f"<b>Country:</b> {safe.get('country', '')}")
        detail_lines.append(f"<b>Use:</b> {safe.get('use', '')}")
        detail_lines.append(f"<b>Notes:</b> {safe.get('notes', '')}")

    elif mode == "Incense & Resin Origins":
        detail_lines.append(f"<b>Material:</b> {safe.get('material', '')}")
        detail_lines.append(f"<b>Country:</b> {safe.get('country', '')}")
        detail_lines.append(f"<b>Trade Era:</b> {safe.get('trade_era', '')}")
        detail_lines.append(f"<b>Notes:</b> {safe.get('notes', '')}")

    elif mode == "Perfume Museums":
        detail_lines.append(f"<b>City:</b> {safe.get('city', '')} &middot; <b>Country:</b> {safe.get('country', '')}")
        detail_lines.append(f"<b>Type:</b> {safe.get('type', '')}")
        detail_lines.append(f"<b>Highlights:</b> {safe.get('highlights', '')}")

    elif mode == "Essential Oil Distilleries":
        detail_lines.append(f"<b>Product:</b> {safe.get('product', '')}")
        detail_lines.append(f"<b>Country:</b> {safe.get('country', '')}")
        detail_lines.append(f"<b>Method:</b> {safe.get('method', '')}")
        detail_lines.append(f"<b>Notes:</b> {safe.get('notes', '')}")

    elif mode == "Spice & Scent Routes":
        detail_lines.append(f"<b>Spice:</b> {safe.get('spice', '')}")
        detail_lines.append(f"<b>Country:</b> {safe.get('country', '')}")
        detail_lines.append(f"<b>Era:</b> {safe.get('era', '')}")
        detail_lines.append(f"<b>Notes:</b> {safe.get('notes', '')}")

    elif mode == "Niche Perfumery Capitals":
        detail_lines.append(f"<b>City:</b> {safe.get('city', '')} &middot; <b>Country:</b> {safe.get('country', '')}")
        detail_lines.append(f"<b>Specialty:</b> {safe.get('specialty', '')}")
        detail_lines.append(f"<b>Notes:</b> {safe.get('notes', '')}")

    elif mode == "Flower Markets & Gardens":
        detail_lines.append(f"<b>City:</b> {safe.get('city', '')} &middot; <b>Country:</b> {safe.get('country', '')}")
        detail_lines.append(f"<b>Type:</b> {safe.get('type', '')}")
        detail_lines.append(f"<b>Notes:</b> {safe.get('notes', '')}")

    elif mode == "Ancient Perfumery Sites":
        detail_lines.append(f"<b>Civilization:</b> {safe.get('civilization', '')}")
        detail_lines.append(f"<b>Country:</b> {safe.get('country', '')}")
        detail_lines.append(f"<b>Era:</b> {safe.get('era', '')}")
        detail_lines.append(f"<b>Notes:</b> {safe.get('notes', '')}")

    else:
        # Fallback: show all fields
        for k, v in safe.items():
            if k != "name":
                label = k.replace("_", " ").title()
                detail_lines.append(f"<b>{label}:</b> {v}")

    details_html = "<br>".join(detail_lines)

    popup = (
        '<div style="'
        "font-family:Inter,Arial,sans-serif;"
        "min-width:220px;max-width:320px;"
        "background:#1a2235;color:#e8ecf4;"
        "border-radius:10px;padding:12px 14px;"
        f'border:1px solid {color}55;">'
        '<div style="'
        "font-size:14px;font-weight:700;"
        f'color:{color};margin-bottom:6px;">'
        f"{title}</div>"
        '<div style="'
        "font-size:11.5px;line-height:1.55;"
        'color:#8b97b0;">'
        f"{details_html}</div></div>"
    )
    return popup


# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------

def _build_map(data: list[dict], mode: str, color: str) -> folium.Map:
    """
    Build a folium dark-themed map with CircleMarkers for each location.
    Uses CartoDB dark_matter tiles for the TerraScout AI dark theme.
    """
    if not data:
        return folium.Map(
            location=[20, 0],
            zoom_start=2,
            tiles="CartoDB dark_matter",
        )

    lats = [d["lat"] for d in data]
    lons = [d["lon"] for d in data]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    # Determine appropriate zoom level from geographic spread
    lat_range = max(lats) - min(lats)
    lon_range = max(lons) - min(lons)
    span = max(lat_range, lon_range)

    if span < 1:
        zoom = 11
    elif span < 2:
        zoom = 10
    elif span < 5:
        zoom = 7
    elif span < 10:
        zoom = 6
    elif span < 20:
        zoom = 5
    elif span < 40:
        zoom = 4
    elif span < 100:
        zoom = 3
    else:
        zoom = 2

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom,
        tiles="CartoDB dark_matter",
    )

    for row in data:
        popup_html = _build_popup_html(row, mode, color)
        tooltip_text = html_module.escape(row.get("name", ""))

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=2,
            popup=folium.Popup(popup_html, max_width=340),
            tooltip=tooltip_text,
        ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Stats computation
# ---------------------------------------------------------------------------

def _compute_stats(
    data: list[dict],
    mode: str,
) -> list[tuple[str, str, str]]:
    """
    Return a list of (label, value, delta_or_help) tuples for st.metric.
    Each mode produces 2-4 relevant statistics about its dataset.
    """
    n = len(data)
    stats: list[tuple[str, str, str]] = [
        ("Locations", str(n), "on map"),
    ]

    if mode == "Historic Perfume Houses":
        countries = len({d.get("country") for d in data})
        oldest = min(
            (d.get("founded", 9999) for d in data),
            default=0,
        )
        newest = max(
            (d.get("founded", 0) for d in data),
            default=0,
        )
        stats.append(("Countries", str(countries), "represented"))
        stats.append(("Oldest Founded", str(oldest), "year"))
        stats.append(("Newest Founded", str(newest), "year"))

    elif mode == "Grasse & French Perfume Capital":
        types = len({d.get("type") for d in data})
        perfume_houses = sum(
            1 for d in data if d.get("type") == "Perfume House"
        )
        farms = sum(
            1 for d in data if "Farm" in d.get("type", "") or "Field" in d.get("type", "")
        )
        stats.append(("Location Types", str(types), "categories"))
        stats.append(("Perfume Houses", str(perfume_houses), "in Grasse"))
        stats.append(("Flower Fields/Farms", str(farms), "active"))

    elif mode == "Aromatic Plant Regions":
        countries = len({d.get("country") for d in data})
        plants = len({d.get("plant") for d in data})
        continents = _count_continents(data)
        stats.append(("Countries", str(countries), "worldwide"))
        stats.append(("Plant Species", str(plants), "catalogued"))
        stats.append(("Continents", str(continents), "covered"))

    elif mode == "Incense & Resin Origins":
        materials = len({d.get("material") for d in data})
        countries = len({d.get("country") for d in data})
        oud_count = sum(
            1 for d in data if "Oud" in d.get("material", "") or "Agarwood" in d.get("material", "")
        )
        stats.append(("Materials", str(materials), "types"))
        stats.append(("Source Countries", str(countries), "worldwide"))
        stats.append(("Oud Sources", str(oud_count), "forests"))

    elif mode == "Perfume Museums":
        countries = len({d.get("country") for d in data})
        types = len({d.get("type") for d in data})
        france_count = sum(
            1 for d in data if d.get("country") == "France"
        )
        stats.append(("Countries", str(countries), "worldwide"))
        stats.append(("Museum Types", str(types), "categories"))
        stats.append(("In France", str(france_count), "museums"))

    elif mode == "Essential Oil Distilleries":
        products = len({d.get("product") for d in data})
        countries = len({d.get("country") for d in data})
        steam_count = sum(
            1 for d in data if "Steam" in d.get("method", "")
        )
        stats.append(("Products", str(products), "oils"))
        stats.append(("Countries", str(countries), "worldwide"))
        stats.append(("Steam Distilled", str(steam_count), "sites"))

    elif mode == "Spice & Scent Routes":
        spices = len({d.get("spice") for d in data})
        countries = len({d.get("country") for d in data})
        ancient_count = sum(
            1 for d in data if "Ancient" in d.get("era", "")
        )
        stats.append(("Spice Types", str(spices), "traded"))
        stats.append(("Countries", str(countries), "on routes"))
        stats.append(("Ancient Sites", str(ancient_count), "pre-medieval"))

    elif mode == "Niche Perfumery Capitals":
        countries = len({d.get("country") for d in data})
        specialties = len({d.get("specialty") for d in data})
        stats.append(("Countries", str(countries), "worldwide"))
        stats.append(("Specialties", str(specialties), "types"))

    elif mode == "Flower Markets & Gardens":
        types = len({d.get("type") for d in data})
        countries = len({d.get("country") for d in data})
        gardens = sum(
            1 for d in data if "Garden" in d.get("type", "")
        )
        stats.append(("Venue Types", str(types), "categories"))
        stats.append(("Countries", str(countries), "worldwide"))
        stats.append(("Gardens", str(gardens), "botanical"))

    elif mode == "Ancient Perfumery Sites":
        civilizations = len({d.get("civilization") for d in data})
        countries = len({d.get("country") for d in data})
        egyptian = sum(
            1 for d in data if "Egyptian" in d.get("civilization", "")
        )
        stats.append(("Civilizations", str(civilizations), "represented"))
        stats.append(("Countries", str(countries), "worldwide"))
        stats.append(("Egyptian Sites", str(egyptian), "pharaonic"))

    return stats


def _count_continents(data: list[dict]) -> int:
    """Rough continent count based on country names for stats display."""
    _EU = {"France", "Italy", "Bulgaria", "Turkey", "Greece", "Spain",
           "United Kingdom", "Germany", "Sweden", "Netherlands",
           "Switzerland", "Cyprus"}
    _AS = {"India", "China", "Japan", "Vietnam", "Indonesia", "Cambodia",
           "Malaysia", "Laos", "Sri Lanka", "Iran", "Oman", "Yemen",
           "UAE", "Saudi Arabia", "Iraq", "Israel", "Jordan", "Pakistan",
           "Uzbekistan", "South Korea"}
    _AF = {"Morocco", "Tunisia", "Egypt", "Somalia", "Somaliland",
           "Ethiopia", "Kenya", "Sudan", "Tanzania", "Madagascar",
           "Comoros", "Reunion (France)", "Yemen (Socotra)"}
    _NA = {"United States", "Canada", "Mexico", "Haiti", "El Salvador"}
    _SA = {"Paraguay"}
    _OC = {"Australia"}
    continents = set()
    for d in data:
        c = d.get("country", "")
        if c in _EU:   continents.add("EU")
        elif c in _AS: continents.add("AS")
        elif c in _AF: continents.add("AF")
        elif c in _NA: continents.add("NA")
        elif c in _SA: continents.add("SA")
        elif c in _OC: continents.add("OC")
        else:          continents.add("Other")
    return len(continents)


# ---------------------------------------------------------------------------
# Country breakdown helper
# ---------------------------------------------------------------------------

def _country_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """Return a DataFrame of country counts for sidebar/expander display."""
    if "country" not in df.columns:
        return pd.DataFrame()
    counts = (
        df["country"]
        .value_counts()
        .reset_index()
    )
    counts.columns = ["Country", "Count"]
    return counts


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_perfume_maps_tab():
    """Render the Perfume & Fragrance Maps tab for TerraScout AI."""

    # ---- Tab header ----
    st.markdown(
        '<div class="tab-header pink">'
        "<h4>\U0001f338 Perfume & Fragrance Maps</h4>"
        "<p>World of scents, perfume houses, and aromatic plants</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Mode selector ----
    modes = [
        "Historic Perfume Houses",
        "Grasse & French Perfume Capital",
        "Aromatic Plant Regions",
        "Incense & Resin Origins",
        "Perfume Museums",
        "Essential Oil Distilleries",
        "Spice & Scent Routes",
        "Niche Perfumery Capitals",
        "Flower Markets & Gardens",
        "Ancient Perfumery Sites",
    ]

    mode = st.selectbox("Map Mode", modes, index=0)

    color = MODE_COLORS.get(mode, "#e91e90")
    icon = MODE_ICONS.get(mode, "\U0001f338")

    # ---- Mode description ----
    description = MODE_DESCRIPTIONS.get(mode, "")
    if description:
        st.markdown(
            f'<div style="background:rgba(15,23,42,0.5);border-left:3px solid {color};'
            f'padding:10px 14px;border-radius:6px;margin-bottom:12px;'
            f'color:#8b97b0;font-size:13px;">'
            f"{html_module.escape(description)}</div>",
            unsafe_allow_html=True,
        )

    # ---- Fetch data ----
    data = _fetch_mode_data(mode)
    if not data:
        st.warning("No data available for this mode.")
        return

    df = pd.DataFrame(data)

    # ---- Search filter ----
    search_term = st.text_input(
        "Filter locations",
        placeholder="Type to search by name, country, or keyword...",
        key="perfume_maps_search",
    )

    if search_term and search_term.strip():
        term_lower = search_term.strip().lower()
        mask = df.apply(
            lambda row: any(
                term_lower in str(v).lower() for v in row.values
            ),
            axis=1,
        )
        df = df[mask]
        data = df.to_dict("records")

    if len(data) == 0:
        st.info("No locations match the current filter. Try a different search term.")
        return

    # ---- Stats row ----
    stats = _compute_stats(data, mode)
    stat_cols = st.columns(len(stats))
    for col, (label, value, delta) in zip(stat_cols, stats):
        col.metric(label=label, value=value, delta=delta)

    # ---- Map ----
    st.markdown(
        f"**{icon} {mode}** \u2014 {len(data)} locations",
    )
    m = _build_map(data, mode, color)
    st_html(m._repr_html_(), height=500)

    # ---- Country breakdown (expandable) ----
    country_df = _country_breakdown(df)
    if not country_df.empty:
        with st.expander("Country Breakdown", expanded=False):
            st.dataframe(
                country_df,
                use_container_width=True,
                hide_index=True,
            )

    # ---- Data Table ----
    st.markdown("### Data Table")
    display_cols = [c for c in df.columns if c not in ("lat", "lon")]
    st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
    )

    # ---- Coordinate table (expandable) ----
    with st.expander("Show Coordinates", expanded=False):
        coord_cols = ["name", "lat", "lon"]
        available = [c for c in coord_cols if c in df.columns]
        if available:
            st.dataframe(
                df[available],
                use_container_width=True,
                hide_index=True,
            )

    # ---- CSV Download ----
    csv_data = df.to_csv(index=False).encode("utf-8")
    safe_mode_name = (
        mode.lower()
        .replace(" ", "_")
        .replace("&", "and")
    )
    st.download_button(
        label=f"Download {mode} CSV",
        data=csv_data,
        file_name=f"perfume_maps_{safe_mode_name}.csv",
        mime="text/csv",
    )
