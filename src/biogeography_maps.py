"""
Biogeography & Species Distribution Maps module for TerraScout AI.
Composite maps showing animal/plant distribution across the world using
hardcoded scientific data with folium visualizations.
All data is embedded — no external API calls required.
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

# ═══════════════════════════════════════════════════════════════
# COLOR PALETTES
# ═══════════════════════════════════════════════════════════════
MARSUPIAL_COLORS = {
    "Australasia": "#10b981",
    "Americas (Opossums)": "#f59e0b",
}

BIG_CAT_COLORS = {
    "Lion": "#f59e0b",
    "Tiger": "#f97316",
    "Leopard": "#eab308",
    "Jaguar": "#84cc16",
    "Cheetah": "#06b6d4",
    "Snow Leopard": "#a78bfa",
    "Cougar": "#ef4444",
}

PRIMATE_COLORS = {
    "Gorilla": "#8b5cf6",
    "Chimpanzee": "#10b981",
    "Orangutan": "#f97316",
    "Bonobo": "#ec4899",
    "New World Monkeys": "#06b6d4",
    "Old World Monkeys": "#f59e0b",
}

MARINE_COLORS = {
    "Blue Whale": "#3b82f6",
    "Humpback Whale": "#06b6d4",
    "Gray Whale": "#8b97b0",
    "Great White Shark": "#ef4444",
    "Dolphin Hotspot": "#10b981",
    "Sea Turtle Nesting": "#f59e0b",
}

REALM_COLORS = {
    "Nearctic": "#3b82f6",
    "Neotropical": "#10b981",
    "Palearctic": "#8b5cf6",
    "Afrotropic": "#f59e0b",
    "Indomalayan": "#f97316",
    "Australasia": "#ef4444",
    "Oceanian": "#06b6d4",
    "Antarctic": "#e2e8f0",
}

CORAL_COLORS = {
    "Great Barrier Reef": "#ef4444",
    "Coral Triangle": "#f97316",
    "Mesoamerican Reef": "#10b981",
    "Red Sea Coral": "#f59e0b",
    "Caribbean Reefs": "#06b6d4",
    "Maldives Reefs": "#8b5cf6",
    "Hawaiian Reefs": "#ec4899",
}

RAINFOREST_COLORS = {
    "Amazon": "#10b981",
    "Congo Basin": "#22c55e",
    "SE Asian (Borneo)": "#84cc16",
    "SE Asian (Sumatra)": "#a3e635",
    "SE Asian (Papua)": "#4ade80",
    "Daintree": "#14b8a6",
    "Atlantic Forest": "#34d399",
}

FLYWAY_COLORS = {
    "Atlantic Americas": "#3b82f6",
    "Pacific Americas": "#06b6d4",
    "Mississippi": "#8b5cf6",
    "East Atlantic": "#10b981",
    "Black Sea / Mediterranean": "#f59e0b",
    "Central Asian": "#f97316",
    "East Asian-Australasian": "#ef4444",
    "West Pacific": "#ec4899",
}

VENOM_COLORS = {
    "Venomous Snakes": "#ef4444",
    "Scorpions": "#f59e0b",
    "Spiders": "#8b5cf6",
    "Box Jellyfish": "#06b6d4",
    "Cone Snails": "#ec4899",
}


# ═══════════════════════════════════════════════════════════════
# POPUP BUILDER
# ═══════════════════════════════════════════════════════════════
def _popup_html(title: str, rows: dict, color: str = "#06b6d4") -> str:
    """Build a styled HTML popup for folium markers/polygons."""
    body = "".join(
        f"<tr><td style='color:#8b97b0;padding:2px 8px 2px 0;'>{escape(str(k))}</td>"
        f"<td style='color:#e8ecf4;padding:2px 0;'>{escape(str(v))}</td></tr>"
        for k, v in rows.items()
    )
    return (
        f"<div style='min-width:220px;max-width:320px;font-family:Inter,sans-serif;"
        f"background:#1a2235;border:1px solid #2a3550;border-radius:8px;padding:12px;"
        f"color:#e8ecf4;'>"
        f"<div style='font-size:14px;font-weight:600;color:{color};margin-bottom:8px;"
        f"border-bottom:1px solid #2a3550;padding-bottom:6px;'>{escape(str(title))}</div>"
        f"<table style='font-size:12px;'>{body}</table></div>"
    )


# ═══════════════════════════════════════════════════════════════
# MAP 1 — MARSUPIAL DISTRIBUTION
# ═══════════════════════════════════════════════════════════════
def _build_marsupial_map() -> tuple:
    """Marsupial distribution: Australasia + Americas opossums + Wallace Line."""
    m = folium.Map(location=[-10, 140], zoom_start=3, tiles="CartoDB dark_matter")

    # Australasian marsupial zone (simplified polygon)
    australasia_coords = [
        (-10, 110), (-8, 118), (-5, 120), (-2, 130), (-2, 140),
        (-5, 150), (-10, 155), (-20, 155), (-35, 152), (-40, 148),
        (-44, 147), (-44, 142), (-38, 137), (-35, 130), (-30, 115),
        (-20, 112), (-12, 110), (-10, 110),
    ]
    folium.Polygon(
        locations=australasia_coords,
        color=MARSUPIAL_COLORS["Australasia"],
        fill=True, fill_color=MARSUPIAL_COLORS["Australasia"],
        fill_opacity=0.25, opacity=0.7, weight=2,
        popup=folium.Popup(_popup_html("Australasian Marsupials", {
            "Region": "Australia, New Guinea, nearby islands",
            "Species count": "~250 marsupial species",
            "Key species": "Kangaroo, Koala, Wombat, Platypus-adjacent",
            "Unique feature": "Evolved in isolation after Gondwana breakup",
            "Conservation": "Many species vulnerable due to habitat loss",
        }, MARSUPIAL_COLORS["Australasia"]), max_width=340),
    ).add_to(m)

    # New Guinea highlands pocket
    new_guinea = [
        (-2, 132), (-1, 138), (-2, 143), (-5, 147), (-8, 147),
        (-9, 143), (-7, 137), (-5, 132), (-2, 132),
    ]
    folium.Polygon(
        locations=new_guinea,
        color=MARSUPIAL_COLORS["Australasia"],
        fill=True, fill_color=MARSUPIAL_COLORS["Australasia"],
        fill_opacity=0.2, opacity=0.5, weight=1,
        popup=folium.Popup(_popup_html("New Guinea Marsupials", {
            "Region": "Papua New Guinea & West Papua",
            "Species count": "~80 marsupial species",
            "Key species": "Tree kangaroos, cuscus, bandicoots",
            "Habitat": "Tropical montane and lowland forests",
        }, MARSUPIAL_COLORS["Australasia"]), max_width=340),
    ).add_to(m)

    # Americas opossums zone
    americas_coords = [
        (45, -100), (40, -85), (30, -80), (20, -95), (15, -90),
        (10, -80), (5, -75), (0, -70), (-10, -65), (-20, -55),
        (-35, -60), (-40, -65), (-35, -70), (-20, -70), (-10, -75),
        (0, -80), (10, -85), (20, -100), (30, -105), (40, -110),
        (45, -100),
    ]
    folium.Polygon(
        locations=americas_coords,
        color=MARSUPIAL_COLORS["Americas (Opossums)"],
        fill=True, fill_color=MARSUPIAL_COLORS["Americas (Opossums)"],
        fill_opacity=0.2, opacity=0.7, weight=2,
        popup=folium.Popup(_popup_html("Americas Marsupials", {
            "Region": "North, Central & South America",
            "Species count": "~100+ opossum species",
            "Key species": "Virginia opossum, water opossum, mouse opossums",
            "Unique feature": "Only marsupials outside Australasia",
            "Fun fact": "Virginia opossum immune to most snake venom",
        }, MARSUPIAL_COLORS["Americas (Opossums)"]), max_width=340),
    ).add_to(m)

    # Wallace Line
    wallace_line = [
        (20, 119.5), (5, 119.5), (0, 118), (-2, 117), (-5, 116),
        (-8, 116), (-9, 117), (-10, 120),
    ]
    folium.PolyLine(
        locations=wallace_line, color="#ef4444", weight=3,
        dash_array="10 6",
        popup=folium.Popup(_popup_html("Wallace Line", {
            "Named after": "Alfred Russel Wallace (1859)",
            "Significance": "Biogeographic boundary between Asian & Australasian fauna",
            "West side": "Asian fauna — primates, elephants, tigers",
            "East side": "Australasian fauna — marsupials, birds of paradise",
            "Geological cause": "Deep ocean trench prevented land bridges",
        }, "#ef4444"), max_width=340),
    ).add_to(m)

    # Key species markers
    species_markers = [
        (-33.87, 151.21, "Red Kangaroo", "Macropus rufus", "Largest living marsupial, up to 2m tall", "Least Concern"),
        (-33.71, 150.31, "Koala", "Phascolarctos cinereus", "Arboreal herbivore, sleeps 20+ hours/day", "Vulnerable"),
        (-31.95, 149.85, "Wombat", "Vombatus ursinus", "Burrowing marsupial with cube-shaped scat", "Least Concern"),
        (-42.88, 147.33, "Tasmanian Devil", "Sarcophilus harrisii", "Largest living carnivorous marsupial", "Endangered"),
        (-6.0, 145.0, "Tree Kangaroo", "Dendrolagus sp.", "Arboreal kangaroo of New Guinea rainforests", "Endangered"),
        (38.9, -77.0, "Virginia Opossum", "Didelphis virginiana", "Only marsupial in North America", "Least Concern"),
        (-15.0, -47.0, "Water Opossum", "Chironectes minimus", "Only aquatic marsupial, webbed hind feet", "Least Concern"),
    ]
    for lat, lng, name, sci, desc, status in species_markers:
        color = MARSUPIAL_COLORS["Australasia"] if lng > 100 else MARSUPIAL_COLORS["Americas (Opossums)"]
        folium.CircleMarker(
            location=[lat, lng], radius=7, color=color,
            fill=True, fill_color=color, fill_opacity=0.8,
            popup=folium.Popup(_popup_html(name, {
                "Scientific name": sci,
                "Description": desc,
                "Conservation status": status,
            }, color), max_width=340),
        ).add_to(m)

    # Stats
    stats = {"Total marsupial species": "~380", "Australasia species": "~250",
             "Americas species": "~100+", "Families": "19"}
    df = pd.DataFrame(species_markers, columns=["Lat", "Lon", "Species", "Scientific Name", "Description", "Status"])
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# MAP 2 — BIG CAT TERRITORIES
# ═══════════════════════════════════════════════════════════════
def _build_big_cat_map() -> tuple:
    """Big cat territory ranges worldwide."""
    m = folium.Map(location=[20, 50], zoom_start=3, tiles="CartoDB dark_matter")

    cat_ranges = {
        "Lion": {
            "color": BIG_CAT_COLORS["Lion"],
            "polygons": [
                # Sub-Saharan Africa
                [(15, -15), (15, 5), (10, 15), (5, 20), (0, 30), (-5, 35),
                 (-15, 35), (-25, 32), (-30, 28), (-25, 18), (-15, 12),
                 (-5, 5), (0, -5), (5, -15), (15, -15)],
                # Gir Forest, India
                [(21, 70), (22, 70), (22, 71.5), (21, 71.5), (21, 70)],
            ],
            "info": {
                "Scientific name": "Panthera leo",
                "Population": "~25,000 wild",
                "Habitat": "Savanna, grasslands, open woodlands",
                "Conservation status": "Vulnerable (IUCN)",
                "Top speed": "80 km/h",
                "Social": "Only social big cat (prides of 10-15)",
            },
        },
        "Tiger": {
            "color": BIG_CAT_COLORS["Tiger"],
            "polygons": [
                # India / South Asia
                [(8, 73), (12, 75), (20, 78), (28, 80), (30, 85),
                 (28, 90), (22, 90), (15, 82), (8, 78), (8, 73)],
                # Southeast Asia
                [(0, 98), (5, 100), (10, 105), (15, 108), (20, 105),
                 (18, 100), (10, 98), (5, 98), (0, 98)],
                # Siberian / Amur tiger
                [(42, 130), (45, 132), (48, 135), (50, 138),
                 (48, 140), (45, 138), (42, 135), (42, 130)],
            ],
            "info": {
                "Scientific name": "Panthera tigris",
                "Population": "~4,500 wild",
                "Habitat": "Tropical forests, mangroves, taiga",
                "Conservation status": "Endangered (IUCN)",
                "Top speed": "65 km/h",
                "Subspecies": "6 living (Bengal, Indochinese, Malayan, Siberian, South China, Sumatran)",
            },
        },
        "Leopard": {
            "color": BIG_CAT_COLORS["Leopard"],
            "polygons": [
                # Africa
                [(15, -15), (15, 10), (10, 25), (5, 35), (-5, 38),
                 (-20, 35), (-30, 30), (-35, 25), (-25, 15), (-10, 8),
                 (0, -5), (10, -15), (15, -15)],
                # South / Central Asia
                [(10, 65), (15, 70), (25, 75), (35, 80), (40, 75),
                 (35, 68), (28, 60), (20, 55), (10, 65)],
            ],
            "info": {
                "Scientific name": "Panthera pardus",
                "Population": "~250,000 (most abundant big cat)",
                "Habitat": "Forests, grasslands, mountains, deserts",
                "Conservation status": "Vulnerable (IUCN)",
                "Top speed": "58 km/h",
                "Unique trait": "Most adaptable big cat, found in widest range of habitats",
            },
        },
        "Jaguar": {
            "color": BIG_CAT_COLORS["Jaguar"],
            "polygons": [
                [(25, -105), (20, -95), (15, -88), (10, -80), (5, -75),
                 (0, -70), (-5, -65), (-15, -55), (-25, -55), (-30, -58),
                 (-25, -65), (-15, -72), (-5, -78), (5, -80), (15, -92),
                 (20, -100), (25, -105)],
            ],
            "info": {
                "Scientific name": "Panthera onca",
                "Population": "~170,000 wild",
                "Habitat": "Tropical rainforest, wetlands, savanna",
                "Conservation status": "Near Threatened (IUCN)",
                "Top speed": "80 km/h",
                "Unique trait": "Strongest bite force relative to size of all big cats",
            },
        },
        "Cheetah": {
            "color": BIG_CAT_COLORS["Cheetah"],
            "polygons": [
                # East and Southern Africa
                [(10, 30), (5, 35), (0, 38), (-5, 38), (-15, 35),
                 (-25, 30), (-30, 25), (-25, 20), (-15, 25), (-5, 30),
                 (5, 32), (10, 30)],
                # Small Iranian population
                [(32, 52), (34, 52), (35, 55), (34, 58), (32, 58),
                 (31, 55), (32, 52)],
            ],
            "info": {
                "Scientific name": "Acinonyx jubatus",
                "Population": "~7,100 wild",
                "Habitat": "Open grasslands, savanna, semi-desert",
                "Conservation status": "Vulnerable (IUCN)",
                "Top speed": "120 km/h (fastest land animal)",
                "Unique trait": "Cannot roar; only big cat that purrs",
            },
        },
        "Snow Leopard": {
            "color": BIG_CAT_COLORS["Snow Leopard"],
            "polygons": [
                [(28, 68), (30, 72), (35, 75), (40, 80), (45, 85),
                 (48, 90), (45, 95), (40, 98), (35, 95), (30, 88),
                 (28, 82), (27, 75), (28, 68)],
            ],
            "info": {
                "Scientific name": "Panthera uncia",
                "Population": "~4,000-6,500 wild",
                "Habitat": "Alpine/subalpine zones, 3,000-5,500m elevation",
                "Conservation status": "Vulnerable (IUCN)",
                "Range countries": "12 (China, Mongolia, India, Nepal, Pakistan, etc.)",
                "Unique trait": "Cannot roar; tail nearly as long as body for balance",
            },
        },
        "Cougar": {
            "color": BIG_CAT_COLORS["Cougar"],
            "polygons": [
                [(55, -130), (50, -120), (45, -110), (40, -105),
                 (35, -110), (30, -115), (25, -105), (15, -95),
                 (10, -80), (0, -75), (-10, -70), (-25, -65),
                 (-40, -70), (-45, -72), (-40, -75), (-25, -70),
                 (-10, -78), (5, -80), (20, -100), (35, -115),
                 (45, -120), (55, -130)],
            ],
            "info": {
                "Scientific name": "Puma concolor",
                "Population": "~50,000 wild",
                "Habitat": "Mountains, forests, deserts — widest range of any New World cat",
                "Conservation status": "Least Concern (IUCN)",
                "Top speed": "72 km/h",
                "Unique trait": "Largest purring cat; also called mountain lion, puma, panther",
            },
        },
    }

    for cat_name, data in cat_ranges.items():
        for poly in data["polygons"]:
            folium.Polygon(
                locations=poly, color=data["color"],
                fill=True, fill_color=data["color"],
                fill_opacity=0.25, opacity=0.7, weight=2,
                popup=folium.Popup(_popup_html(cat_name, data["info"], data["color"]), max_width=340),
            ).add_to(m)

    stats = {"Big cat species": "7", "Total wild population": "~510,000",
             "Most endangered": "Cheetah (~7,100)", "Fastest": "Cheetah (120 km/h)"}
    rows = []
    for cat_name, data in cat_ranges.items():
        rows.append({
            "Species": cat_name,
            "Scientific Name": data["info"]["Scientific name"],
            "Population": data["info"]["Population"],
            "Status": data["info"]["Conservation status"],
        })
    df = pd.DataFrame(rows)
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# MAP 3 — PRIMATE DISTRIBUTION
# ═══════════════════════════════════════════════════════════════
def _build_primate_map() -> tuple:
    """Primate distribution: great apes + monkey regions."""
    m = folium.Map(location=[5, 30], zoom_start=3, tiles="CartoDB dark_matter")

    primate_data = {
        "Gorilla": {
            "color": PRIMATE_COLORS["Gorilla"],
            "polygons": [
                # Central Africa — eastern and western gorilla
                [(-4, 20), (-2, 22), (0, 25), (2, 28), (3, 30),
                 (2, 32), (0, 30), (-2, 28), (-4, 25), (-4, 20)],
            ],
            "info": {
                "Scientific name": "Gorilla gorilla / Gorilla beringei",
                "Population": "~360,000 (western) / ~1,000 (mountain)",
                "Habitat": "Tropical montane and lowland forests",
                "Conservation status": "Critically Endangered (IUCN)",
                "Subspecies": "4 (Western lowland, Cross River, Mountain, Eastern lowland)",
                "Unique trait": "Largest living primate, up to 200 kg",
            },
        },
        "Chimpanzee": {
            "color": PRIMATE_COLORS["Chimpanzee"],
            "polygons": [
                # West and Central Africa
                [(-5, 10), (-2, 8), (2, 5), (5, 2), (8, -5),
                 (10, -12), (8, -15), (5, -10), (2, -5), (0, 5),
                 (-2, 12), (-5, 15), (-6, 18), (-5, 22), (-3, 25),
                 (0, 28), (2, 30), (2, 32), (0, 30), (-3, 28),
                 (-5, 25), (-7, 20), (-7, 15), (-5, 10)],
            ],
            "info": {
                "Scientific name": "Pan troglodytes",
                "Population": "~170,000-300,000 wild",
                "Habitat": "Tropical rainforest, savanna-woodland mosaic",
                "Conservation status": "Endangered (IUCN)",
                "Subspecies": "4 (Central, Western, Nigeria-Cameroon, Eastern)",
                "Unique trait": "Closest relative to humans (98.7% DNA shared)",
            },
        },
        "Orangutan": {
            "color": PRIMATE_COLORS["Orangutan"],
            "polygons": [
                # Borneo
                [(-3, 108), (-1, 109), (2, 110), (4, 112),
                 (5, 115), (4, 117), (2, 118), (0, 117),
                 (-2, 115), (-3, 112), (-3, 108)],
                # Sumatra
                [(-2, 98), (0, 99), (2, 100), (4, 101),
                 (5, 99), (3, 97), (1, 97), (-1, 97), (-2, 98)],
            ],
            "info": {
                "Scientific name": "Pongo pygmaeus / Pongo abelii / Pongo tapanuliensis",
                "Population": "~105,000 (Bornean) / ~14,000 (Sumatran) / ~800 (Tapanuli)",
                "Habitat": "Tropical and subtropical moist broadleaf forests",
                "Conservation status": "Critically Endangered (IUCN)",
                "Species": "3 (Bornean, Sumatran, Tapanuli)",
                "Unique trait": "Most arboreal great ape; solitary lifestyle",
            },
        },
        "Bonobo": {
            "color": PRIMATE_COLORS["Bonobo"],
            "polygons": [
                # Congo Basin south of Congo River
                [(-5, 18), (-3, 20), (-1, 22), (0, 25),
                 (-1, 27), (-3, 28), (-5, 26), (-6, 23), (-5, 18)],
            ],
            "info": {
                "Scientific name": "Pan paniscus",
                "Population": "~15,000-20,000 wild",
                "Habitat": "Lowland tropical rainforest (Congo Basin only)",
                "Conservation status": "Endangered (IUCN)",
                "Range": "Democratic Republic of Congo only",
                "Unique trait": "Matriarchal society; resolves conflicts peacefully",
            },
        },
        "New World Monkeys": {
            "color": PRIMATE_COLORS["New World Monkeys"],
            "polygons": [
                [(20, -100), (15, -90), (10, -80), (5, -75),
                 (0, -70), (-5, -65), (-15, -55), (-25, -55),
                 (-30, -58), (-25, -65), (-15, -70), (-5, -78),
                 (5, -80), (15, -92), (20, -100)],
            ],
            "info": {
                "Scientific name": "Platyrrhini (infraorder)",
                "Species count": "~200 species in 5 families",
                "Key families": "Callitrichidae (marmosets), Cebidae (capuchins), Atelidae (howlers)",
                "Habitat": "Tropical and subtropical forests",
                "Conservation status": "Varies; many endangered",
                "Unique trait": "Prehensile tails (some species); flat noses",
            },
        },
        "Old World Monkeys": {
            "color": PRIMATE_COLORS["Old World Monkeys"],
            "polygons": [
                # Africa
                [(15, -15), (10, 0), (5, 15), (0, 30), (-5, 35),
                 (-15, 35), (-25, 30), (-20, 15), (-5, 5), (5, -10), (15, -15)],
                # Asia
                [(5, 70), (10, 80), (20, 90), (30, 100), (35, 110),
                 (30, 120), (20, 115), (10, 105), (5, 95), (0, 85), (5, 70)],
            ],
            "info": {
                "Scientific name": "Cercopithecidae (family)",
                "Species count": "~160 species",
                "Key genera": "Macaca (macaques), Papio (baboons), Colobus, Langur",
                "Habitat": "Forests, savannas, mountains — very diverse",
                "Conservation status": "Varies; many threatened",
                "Unique trait": "Non-prehensile tails; closer nose arrangement than New World",
            },
        },
    }

    for name, data in primate_data.items():
        for poly in data["polygons"]:
            folium.Polygon(
                locations=poly, color=data["color"],
                fill=True, fill_color=data["color"],
                fill_opacity=0.25, opacity=0.7, weight=2,
                popup=folium.Popup(_popup_html(name, data["info"], data["color"]), max_width=340),
            ).add_to(m)

    stats = {"Great ape species": "4 genera, 7 species", "Monkey families": "~5 NW + 1 OW",
             "Most endangered": "Tapanuli Orangutan (~800)", "Closest to humans": "Chimpanzee (98.7%)"}
    rows = []
    for name, data in primate_data.items():
        rows.append({
            "Group": name,
            "Scientific Name": data["info"].get("Scientific name", ""),
            "Status": data["info"].get("Conservation status", ""),
        })
    df = pd.DataFrame(rows)
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# MAP 4 — MARINE MEGAFAUNA
# ═══════════════════════════════════════════════════════════════
def _build_marine_map() -> tuple:
    """Marine megafauna: whale migration routes, shark zones, turtle nesting."""
    m = folium.Map(location=[10, -30], zoom_start=2, tiles="CartoDB dark_matter")

    # Whale migration routes (polylines)
    whale_routes = {
        "Blue Whale — Eastern Pacific": {
            "color": MARINE_COLORS["Blue Whale"],
            "path": [(55, -140), (45, -130), (35, -125), (25, -115),
                     (15, -105), (10, -100), (5, -95)],
            "info": {
                "Scientific name": "Balaenoptera musculus",
                "Population": "~10,000-25,000",
                "Max length": "30 m (largest animal ever)",
                "Migration": "Alaska to Costa Rica (~10,000 km)",
                "Conservation status": "Endangered (IUCN)",
                "Diet": "Krill (up to 3,600 kg/day)",
            },
        },
        "Blue Whale — Southern Ocean": {
            "color": MARINE_COLORS["Blue Whale"],
            "path": [(-60, -30), (-55, 0), (-50, 30), (-45, 60),
                     (-50, 90), (-55, 120), (-60, 150)],
            "info": {
                "Scientific name": "Balaenoptera musculus intermedia",
                "Population": "~5,000 (Antarctic subspecies)",
                "Migration": "Antarctic feeding to tropical breeding",
                "Conservation status": "Critically Endangered",
                "Region": "Southern Ocean circumpolar",
            },
        },
        "Humpback Whale — North Atlantic": {
            "color": MARINE_COLORS["Humpback Whale"],
            "path": [(65, -20), (55, -25), (45, -30), (35, -40),
                     (25, -50), (20, -60), (18, -65)],
            "info": {
                "Scientific name": "Megaptera novaeangliae",
                "Population": "~80,000 worldwide",
                "Max length": "16 m",
                "Migration": "Norway/Iceland to Caribbean (~8,000 km)",
                "Conservation status": "Least Concern (IUCN)",
                "Famous for": "Complex songs lasting up to 30 minutes",
            },
        },
        "Humpback Whale — South Pacific": {
            "color": MARINE_COLORS["Humpback Whale"],
            "path": [(-65, 170), (-55, 175), (-45, -175), (-35, -170),
                     (-25, -165), (-18, -155), (-15, -150)],
            "info": {
                "Scientific name": "Megaptera novaeangliae",
                "Migration": "Antarctic to Tonga / French Polynesia",
                "Conservation status": "Least Concern (IUCN)",
                "Unique behavior": "Bubble-net feeding in groups",
            },
        },
        "Gray Whale — Eastern Pacific": {
            "color": MARINE_COLORS["Gray Whale"],
            "path": [(65, -170), (58, -160), (50, -140), (42, -130),
                     (35, -122), (28, -116), (22, -110)],
            "info": {
                "Scientific name": "Eschrichtius robustus",
                "Population": "~27,000",
                "Max length": "15 m",
                "Migration": "Alaska to Baja California (~20,000 km round trip)",
                "Conservation status": "Least Concern (IUCN)",
                "Unique trait": "Longest migration of any mammal",
            },
        },
    }

    for route_name, data in whale_routes.items():
        folium.PolyLine(
            locations=data["path"], color=data["color"],
            weight=3, opacity=0.8, dash_array="8 4",
            popup=folium.Popup(_popup_html(route_name, data["info"], data["color"]), max_width=340),
        ).add_to(m)

    # Great White Shark zones
    shark_zones = [
        (-34, 18, "Great White — South Africa", "Seal Island, False Bay — iconic cage diving spot"),
        (-34, 152, "Great White — SE Australia", "Neptune Islands, SA — seasonal aggregation"),
        (37, -122, "Great White — California", "Farallon Islands — elephant seal predation"),
        (22, -160, "Great White — Hawaii", "Seasonal transits between mainland & Hawaii"),
        (-42, 175, "Great White — New Zealand", "Stewart Island — year-round population"),
    ]
    for lat, lon, name, desc in shark_zones:
        folium.CircleMarker(
            location=[lat, lon], radius=10,
            color=MARINE_COLORS["Great White Shark"],
            fill=True, fill_color=MARINE_COLORS["Great White Shark"],
            fill_opacity=0.7,
            popup=folium.Popup(_popup_html(name, {
                "Scientific name": "Carcharodon carcharias",
                "Description": desc,
                "Population": "~3,500 worldwide",
                "Max length": "6 m",
                "Conservation status": "Vulnerable (IUCN)",
            }, MARINE_COLORS["Great White Shark"]), max_width=340),
        ).add_to(m)

    # Dolphin hotspots
    dolphin_spots = [
        (25, -80, "Dolphin — Florida Keys", "Bottlenose dolphins, year-round"),
        (-8, 115, "Dolphin — Bali", "Spinner dolphins, dawn pods"),
        (28, 34, "Dolphin — Red Sea", "Spinner & bottlenose near reef"),
        (-26, 33, "Dolphin — Mozambique", "Indo-Pacific bottlenose, sardine run"),
        (43, 5, "Dolphin — Mediterranean", "Striped & common dolphins"),
    ]
    for lat, lon, name, desc in dolphin_spots:
        folium.CircleMarker(
            location=[lat, lon], radius=7,
            color=MARINE_COLORS["Dolphin Hotspot"],
            fill=True, fill_color=MARINE_COLORS["Dolphin Hotspot"],
            fill_opacity=0.7,
            popup=folium.Popup(_popup_html(name, {
                "Description": desc,
                "Dolphin species": "~90 species worldwide",
                "Conservation": "Varies by species",
            }, MARINE_COLORS["Dolphin Hotspot"]), max_width=340),
        ).add_to(m)

    # Sea turtle nesting beaches
    turtle_nests = [
        (27, -80, "Loggerhead — Florida", "Major nesting beach; >100,000 nests/yr"),
        (-3, 40, "Green Turtle — Kenya", "Watamu Marine Park nesting"),
        (24, 36, "Hawksbill — Red Sea", "Ras Mohammed, important nesting site"),
        (-23, 152, "Flatback — Queensland", "Endemic to Australian continental shelf"),
        (9, 100, "Leatherback — Thailand", "Phuket nesting sites, critically reduced"),
        (20, -87, "Hawksbill — Yucatan", "Mexican Caribbean nesting beaches"),
        (-20, 63, "Green Turtle — Mauritius", "Historically important nesting colony"),
    ]
    for lat, lon, name, desc in turtle_nests:
        folium.CircleMarker(
            location=[lat, lon], radius=6,
            color=MARINE_COLORS["Sea Turtle Nesting"],
            fill=True, fill_color=MARINE_COLORS["Sea Turtle Nesting"],
            fill_opacity=0.8,
            popup=folium.Popup(_popup_html(name, {
                "Description": desc,
                "Sea turtle species": "7 worldwide",
                "Threats": "Plastic, light pollution, bycatch, poaching",
                "Conservation": "6 of 7 species threatened",
            }, MARINE_COLORS["Sea Turtle Nesting"]), max_width=340),
        ).add_to(m)

    stats = {"Whale species mapped": "3", "Migration max distance": "20,000 km (Gray Whale)",
             "Shark zones": "5", "Turtle nesting sites": str(len(turtle_nests))}
    rows = []
    for name, data in whale_routes.items():
        rows.append({"Type": "Whale Route", "Name": name, "Status": data["info"].get("Conservation status", "")})
    for lat, lon, name, desc in shark_zones:
        rows.append({"Type": "Shark Zone", "Name": name, "Status": "Vulnerable (IUCN)"})
    for lat, lon, name, desc in turtle_nests:
        rows.append({"Type": "Turtle Nesting", "Name": name, "Status": "Threatened"})
    df = pd.DataFrame(rows)
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# MAP 5 — WALLACE LINE & BIOGEOGRAPHIC REALMS
# ═══════════════════════════════════════════════════════════════
def _build_realms_map() -> tuple:
    """Wallace Line, Weber Line, Lydekker Line and 8 biogeographic realms."""
    m = folium.Map(location=[10, 50], zoom_start=2, tiles="CartoDB dark_matter")

    # 8 Biogeographic Realms (simplified polygons)
    realms = {
        "Nearctic": {
            "color": REALM_COLORS["Nearctic"],
            "polygon": [(70, -170), (70, -55), (50, -55), (35, -80),
                        (25, -100), (20, -105), (30, -118), (48, -130),
                        (60, -145), (65, -170), (70, -170)],
            "info": {
                "Area": "~22.9 million km2",
                "Region": "North America, Greenland, northern Mexico",
                "Key endemic fauna": "Pronghorn, prairie dog, bison, turkey vulture",
                "Biomes": "Tundra, boreal forest, temperate deciduous, grasslands, deserts",
                "Unique feature": "Connected to Palearctic via Beringia during ice ages",
            },
        },
        "Neotropical": {
            "color": REALM_COLORS["Neotropical"],
            "polygon": [(20, -105), (25, -100), (20, -80), (15, -75),
                        (10, -75), (5, -70), (0, -65), (-10, -55),
                        (-25, -55), (-40, -60), (-55, -70), (-45, -75),
                        (-25, -70), (-10, -78), (0, -82), (10, -85),
                        (15, -90), (20, -105)],
            "info": {
                "Area": "~19.0 million km2",
                "Region": "Central America, South America, Caribbean",
                "Key endemic fauna": "Sloth, toucan, anaconda, jaguar, piranha",
                "Biomes": "Tropical rainforest, cerrado, pampas, Andes alpine",
                "Unique feature": "Highest biodiversity of any realm (Amazon)",
            },
        },
        "Palearctic": {
            "color": REALM_COLORS["Palearctic"],
            "polygon": [(70, -25), (75, 0), (75, 60), (75, 120),
                        (70, 170), (55, 170), (45, 140), (40, 120),
                        (30, 100), (25, 70), (30, 50), (30, 35),
                        (35, 25), (40, 10), (45, -10), (55, -25), (70, -25)],
            "info": {
                "Area": "~54.1 million km2 (largest realm)",
                "Region": "Europe, northern Africa, northern/central Asia",
                "Key endemic fauna": "Brown bear, red fox, Eurasian lynx, giant panda",
                "Biomes": "Tundra, taiga, temperate forest, steppe, desert",
                "Unique feature": "Largest biogeographic realm by area",
            },
        },
        "Afrotropic": {
            "color": REALM_COLORS["Afrotropic"],
            "polygon": [(15, -18), (20, 0), (20, 25), (15, 40),
                        (10, 45), (5, 42), (0, 40), (-10, 42),
                        (-25, 35), (-35, 25), (-35, 18), (-25, 15),
                        (-10, 10), (0, 0), (10, -15), (15, -18)],
            "info": {
                "Area": "~22.1 million km2",
                "Region": "Sub-Saharan Africa, Madagascar, southern Arabian Peninsula",
                "Key endemic fauna": "Elephant, giraffe, hippo, lemur (Madagascar), gorilla",
                "Biomes": "Tropical forest, savanna, Sahel, fynbos, deserts",
                "Unique feature": "Origin of hominins; highest large mammal diversity",
            },
        },
        "Indomalayan": {
            "color": REALM_COLORS["Indomalayan"],
            "polygon": [(30, 65), (35, 80), (30, 100), (25, 105),
                        (20, 108), (10, 105), (5, 100), (0, 95),
                        (-5, 100), (-8, 110), (-5, 115), (5, 120),
                        (5, 115), (10, 105), (15, 80), (25, 70), (30, 65)],
            "info": {
                "Area": "~7.5 million km2",
                "Region": "Indian subcontinent, Southeast Asia, southern China",
                "Key endemic fauna": "Tiger, Asian elephant, orangutan, Komodo dragon",
                "Biomes": "Tropical rainforest, monsoon forest, mangroves",
                "Unique feature": "Bounded by Wallace Line to the east",
            },
        },
        "Australasia": {
            "color": REALM_COLORS["Australasia"],
            "polygon": [(-10, 120), (-5, 130), (-2, 140), (-5, 150),
                        (-15, 155), (-25, 153), (-38, 148), (-44, 147),
                        (-44, 135), (-35, 125), (-25, 115), (-15, 115),
                        (-10, 120)],
            "info": {
                "Area": "~7.7 million km2",
                "Region": "Australia, New Guinea, New Zealand, eastern Indonesia",
                "Key endemic fauna": "Kangaroo, koala, platypus, kiwi, echidna",
                "Biomes": "Desert, tropical forest, temperate forest, alpine",
                "Unique feature": "Dominated by marsupials and monotremes",
            },
        },
        "Oceanian": {
            "color": REALM_COLORS["Oceanian"],
            "polygon": [(20, 160), (25, -175), (20, -150), (10, -140),
                        (0, -150), (-10, -160), (-20, -175), (-25, 175),
                        (-20, 165), (-10, 160), (0, 155), (10, 155),
                        (20, 160)],
            "info": {
                "Area": "~1.0 million km2 (land only)",
                "Region": "Pacific Islands — Polynesia, Micronesia, Melanesia, Hawaii",
                "Key endemic fauna": "Honeycreepers (Hawaii), fruit bats, unique seabirds",
                "Biomes": "Tropical moist forest, coral atolls",
                "Unique feature": "Extreme endemism due to island isolation; high extinction rates",
            },
        },
        "Antarctic": {
            "color": REALM_COLORS["Antarctic"],
            "polygon": [(-60, -180), (-60, -90), (-60, 0), (-60, 90),
                        (-60, 180), (-75, 180), (-80, 90), (-80, 0),
                        (-80, -90), (-75, -180), (-60, -180)],
            "info": {
                "Area": "~14.2 million km2",
                "Region": "Antarctica, Southern Ocean islands",
                "Key endemic fauna": "Emperor penguin, leopard seal, Antarctic krill",
                "Biomes": "Ice sheet, tundra, Southern Ocean",
                "Unique feature": "Most extreme environment; nearly all fauna marine-dependent",
            },
        },
    }

    for realm_name, data in realms.items():
        folium.Polygon(
            locations=data["polygon"], color=data["color"],
            fill=True, fill_color=data["color"],
            fill_opacity=0.2, opacity=0.7, weight=2,
            popup=folium.Popup(_popup_html(realm_name, data["info"], data["color"]), max_width=340),
        ).add_to(m)

    # Wallace Line
    wallace_line = [(20, 119.5), (5, 119.5), (0, 118), (-2, 117),
                    (-5, 116), (-8, 116), (-10, 120)]
    folium.PolyLine(
        locations=wallace_line, color="#ef4444", weight=3, dash_array="10 6",
        popup=folium.Popup(_popup_html("Wallace Line", {
            "Year proposed": "1859 by Alfred Russel Wallace",
            "Separates": "Indomalayan from Australasian fauna",
            "West": "Placental mammals (primates, elephants)",
            "East": "Marsupials, monotremes, birds of paradise",
        }, "#ef4444"), max_width=340),
    ).add_to(m)

    # Weber Line
    weber_line = [(5, 125), (0, 126), (-3, 127), (-5, 128),
                  (-8, 130), (-10, 132)]
    folium.PolyLine(
        locations=weber_line, color="#f59e0b", weight=3, dash_array="10 6",
        popup=folium.Popup(_popup_html("Weber Line", {
            "Year proposed": "1902 by Max Weber",
            "Description": "Line of faunal balance between Asian & Australian fauna",
            "Location": "Between Wallace Line and Lydekker Line",
            "Significance": "50/50 balance point of fauna from each realm",
        }, "#f59e0b"), max_width=340),
    ).add_to(m)

    # Lydekker Line
    lydekker_line = [(0, 130), (-2, 132), (-4, 134), (-6, 135),
                     (-8, 136), (-10, 138), (-12, 140)]
    folium.PolyLine(
        locations=lydekker_line, color="#10b981", weight=3, dash_array="10 6",
        popup=folium.Popup(_popup_html("Lydekker Line", {
            "Year proposed": "1896 by Richard Lydekker",
            "Description": "Edge of the Australian continental shelf",
            "East of line": "True Australasian fauna (marsupials dominant)",
            "Significance": "Marks boundary of Sahul (ancient Australian continent)",
        }, "#10b981"), max_width=340),
    ).add_to(m)

    stats = {"Realms mapped": "8", "Largest realm": "Palearctic (54.1M km2)",
             "Most biodiverse": "Neotropical", "Boundary lines": "3 (Wallace, Weber, Lydekker)"}
    rows = []
    for name, data in realms.items():
        rows.append({
            "Realm": name, "Area": data["info"]["Area"],
            "Key Fauna": data["info"]["Key endemic fauna"][:60],
        })
    df = pd.DataFrame(rows)
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# MAP 6 — CORAL REEF DISTRIBUTION
# ═══════════════════════════════════════════════════════════════
def _build_coral_map() -> tuple:
    """Major coral reef systems of the world."""
    m = folium.Map(location=[5, 80], zoom_start=2, tiles="CartoDB dark_matter")

    reef_data = {
        "Great Barrier Reef": {
            "color": CORAL_COLORS["Great Barrier Reef"],
            "polygon": [(-10, 143), (-12, 144), (-15, 146), (-18, 147),
                        (-20, 149), (-23, 152), (-24, 152), (-23, 150),
                        (-20, 148), (-17, 146), (-14, 144), (-11, 143),
                        (-10, 143)],
            "info": {
                "Length": "2,300 km (largest reef system)",
                "Area": "~344,400 km2",
                "Species": "1,500 fish, 400 coral, 4,000 mollusk",
                "UNESCO": "World Heritage Site since 1981",
                "Threat level": "High — bleaching events 2016-2020",
                "Conservation": "Great Barrier Reef Marine Park Authority",
            },
        },
        "Coral Triangle": {
            "color": CORAL_COLORS["Coral Triangle"],
            "polygon": [(5, 115), (8, 120), (10, 125), (8, 130),
                        (5, 135), (0, 140), (-5, 140), (-8, 135),
                        (-10, 130), (-8, 125), (-5, 120), (0, 115),
                        (5, 115)],
            "info": {
                "Countries": "Indonesia, Philippines, Malaysia, PNG, Timor-Leste, Solomon Islands",
                "Area": "~6 million km2",
                "Species": "600 coral species (76% of all known)",
                "Nickname": "Amazon of the Seas",
                "Threat level": "Very High — fishing, climate change",
                "Unique": "Global epicenter of marine biodiversity",
            },
        },
        "Mesoamerican Reef": {
            "color": CORAL_COLORS["Mesoamerican Reef"],
            "polygon": [(21, -87), (20, -87), (18, -88), (16, -88),
                        (15, -87), (16, -86), (18, -86), (20, -86),
                        (21, -87)],
            "info": {
                "Length": "1,000 km (2nd largest barrier reef)",
                "Countries": "Mexico, Belize, Guatemala, Honduras",
                "Species": "65 coral species, 500 fish species",
                "Key site": "Belize Barrier Reef (UNESCO)",
                "Threat level": "High — coastal development, agriculture runoff",
                "Conservation": "MAR Fund regional coordination",
            },
        },
        "Red Sea Coral": {
            "color": CORAL_COLORS["Red Sea Coral"],
            "polygon": [(28, 33), (27, 34), (24, 36), (20, 38),
                        (15, 42), (13, 43), (13, 42), (16, 40),
                        (20, 37), (24, 35), (27, 33), (28, 33)],
            "info": {
                "Length": "~2,000 km fringing reef",
                "Area": "~4,250 km2",
                "Species": "300 coral species, 1,200 fish species",
                "Unique": "Heat-resistant corals (naturally adapted to 32C+)",
                "Threat level": "Moderate — naturally more resilient",
                "Research": "Model for climate-adapted corals",
            },
        },
        "Caribbean Reefs": {
            "color": CORAL_COLORS["Caribbean Reefs"],
            "polygon": [(25, -80), (23, -75), (20, -70), (15, -65),
                        (12, -62), (10, -63), (12, -68), (15, -72),
                        (18, -78), (20, -82), (22, -83), (25, -80)],
            "info": {
                "Area": "~26,000 km2 of reefs",
                "Countries": "30+ nations and territories",
                "Species": "65 coral species, 1,500 fish species",
                "Decline": "80% of Caribbean reefs lost since 1970s",
                "Threat level": "Critical — disease, bleaching, overfishing",
                "Key cause": "Diadema sea urchin die-off (1983)",
            },
        },
        "Maldives Reefs": {
            "color": CORAL_COLORS["Maldives Reefs"],
            "polygon": [(7, 72), (6, 73), (4, 73.5), (2, 73.5),
                        (0, 73), (-1, 73), (0, 72.5), (2, 72),
                        (4, 72), (6, 72), (7, 72)],
            "info": {
                "Structure": "26 atolls, ~1,200 islands",
                "Area": "~8,920 km2 of reef",
                "Species": "250 coral species, 1,100 fish species",
                "Elevation": "Avg 1.5m above sea level",
                "Threat level": "Very High — sea level rise, bleaching",
                "Bleaching": "1998 event killed 60% of shallow corals",
            },
        },
        "Hawaiian Reefs": {
            "color": CORAL_COLORS["Hawaiian Reefs"],
            "polygon": [(22, -161), (21, -160), (20, -157), (19, -155),
                        (19, -156), (20, -159), (21, -161), (22, -161)],
            "info": {
                "Length": "~2,100 km (Northwestern Hawaiian Islands)",
                "Area": "~3,600 km2",
                "Species": "57 coral species, 680 fish species",
                "Endemism": "25% of marine species found nowhere else",
                "Monument": "Papahanaumokuakea Marine National Monument",
                "Threat level": "High — warming, invasive algae, sediment",
            },
        },
    }

    for reef_name, data in reef_data.items():
        folium.Polygon(
            locations=data["polygon"], color=data["color"],
            fill=True, fill_color=data["color"],
            fill_opacity=0.35, opacity=0.7, weight=2,
            popup=folium.Popup(_popup_html(reef_name, data["info"], data["color"]), max_width=340),
        ).add_to(m)

    stats = {"Reef systems": "7 major", "Global coral reef area": "~284,300 km2",
             "Coral species": "~800 worldwide", "Reefs at risk": ">75% threatened"}
    rows = []
    for name, data in reef_data.items():
        rows.append({
            "Reef System": name,
            "Threat Level": data["info"].get("Threat level", ""),
            "Key Stat": list(data["info"].values())[0],
        })
    df = pd.DataFrame(rows)
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# MAP 7 — RAINFOREST COVERAGE
# ═══════════════════════════════════════════════════════════════
def _build_rainforest_map() -> tuple:
    """Major rainforests of the world with deforestation data."""
    m = folium.Map(location=[0, 20], zoom_start=2, tiles="CartoDB dark_matter")

    rainforest_data = {
        "Amazon": {
            "color": RAINFOREST_COLORS["Amazon"],
            "polygon": [(5, -75), (3, -70), (0, -60), (-3, -52),
                        (-8, -48), (-12, -50), (-15, -55), (-18, -60),
                        (-15, -65), (-12, -70), (-8, -75), (-3, -78),
                        (0, -78), (3, -77), (5, -75)],
            "info": {
                "Area": "5.5 million km2 (original), ~4.7M km2 remaining",
                "Countries": "Brazil (60%), Peru, Colombia, Ecuador, Bolivia + 4 more",
                "Biodiversity": "10% of all species on Earth",
                "Key species": "Jaguar, harpy eagle, poison dart frog, anaconda",
                "Deforestation": "~17% lost since 1970",
                "Carbon storage": "150-200 billion tonnes of CO2",
                "Rainfall": "Generates 50% of its own rainfall",
            },
        },
        "Congo Basin": {
            "color": RAINFOREST_COLORS["Congo Basin"],
            "polygon": [(5, 10), (5, 15), (4, 22), (3, 28),
                        (2, 30), (0, 30), (-3, 28), (-5, 25),
                        (-5, 20), (-4, 15), (-2, 12), (0, 10),
                        (3, 10), (5, 10)],
            "info": {
                "Area": "2.0 million km2 (2nd largest rainforest)",
                "Countries": "DRC (60%), Republic of Congo, Cameroon, Gabon, CAR",
                "Biodiversity": "10,000 plant species, 1,000 bird species",
                "Key species": "Gorilla, bonobo, okapi, forest elephant",
                "Deforestation": "~10% lost since 1970",
                "Carbon storage": "60 billion tonnes of CO2",
                "Peatlands": "World's largest tropical peatland (145,500 km2)",
            },
        },
        "SE Asian (Borneo)": {
            "color": RAINFOREST_COLORS["SE Asian (Borneo)"],
            "polygon": [(-3, 108), (-1, 109), (2, 111), (5, 114),
                        (6, 117), (4, 118), (2, 118), (0, 117),
                        (-2, 115), (-3, 112), (-3, 108)],
            "info": {
                "Area": "~280,000 km2 remaining (of 743,000 km2 island)",
                "Countries": "Malaysia (Sabah, Sarawak), Indonesia (Kalimantan), Brunei",
                "Biodiversity": "15,000 plant species, 380 bird species",
                "Key species": "Bornean orangutan, pygmy elephant, proboscis monkey",
                "Deforestation": "~50% lost since 1970 (palm oil)",
                "Threat": "Palm oil plantations, logging, fires",
            },
        },
        "SE Asian (Sumatra)": {
            "color": RAINFOREST_COLORS["SE Asian (Sumatra)"],
            "polygon": [(-5, 100), (-3, 101), (0, 101), (3, 102),
                        (5, 100), (4, 98), (2, 97), (0, 97),
                        (-2, 98), (-4, 99), (-5, 100)],
            "info": {
                "Area": "~120,000 km2 remaining (of ~250,000 km2)",
                "Country": "Indonesia",
                "Biodiversity": "10,000 plant species",
                "Key species": "Sumatran orangutan, Sumatran tiger, Sumatran rhino",
                "Deforestation": "~50% lost since 1985",
                "UNESCO": "Tropical Rainforest Heritage of Sumatra",
            },
        },
        "SE Asian (Papua)": {
            "color": RAINFOREST_COLORS["SE Asian (Papua)"],
            "polygon": [(-1, 131), (0, 135), (-1, 140), (-3, 145),
                        (-6, 148), (-8, 147), (-8, 143), (-6, 138),
                        (-4, 134), (-2, 131), (-1, 131)],
            "info": {
                "Area": "~300,000 km2 (3rd largest tropical forest island)",
                "Countries": "Indonesia (West Papua), Papua New Guinea",
                "Biodiversity": "20,000 plant species, 760 bird species",
                "Key species": "Birds of paradise, tree kangaroos, echidnas",
                "Deforestation": "~10% lost (accelerating)",
                "Unique": "One of the least explored forests on Earth",
            },
        },
        "Daintree": {
            "color": RAINFOREST_COLORS["Daintree"],
            "polygon": [(-15.5, 145.0), (-15.8, 145.2), (-16.2, 145.4),
                        (-16.5, 145.5), (-16.8, 145.4), (-16.8, 145.2),
                        (-16.5, 145.0), (-16.2, 144.9), (-15.8, 144.9),
                        (-15.5, 145.0)],
            "info": {
                "Area": "~1,200 km2",
                "Country": "Australia (Queensland)",
                "Age": "180 million years (oldest rainforest on Earth)",
                "Biodiversity": "30% of frog species, 65% of bat species in Australia",
                "Key species": "Cassowary, musky rat-kangaroo, Boyd's forest dragon",
                "UNESCO": "Wet Tropics World Heritage Area",
            },
        },
        "Atlantic Forest": {
            "color": RAINFOREST_COLORS["Atlantic Forest"],
            "polygon": [(-5, -35), (-8, -36), (-12, -38), (-15, -40),
                        (-20, -42), (-25, -47), (-28, -50), (-27, -49),
                        (-22, -44), (-18, -41), (-13, -39), (-8, -37),
                        (-5, -35)],
            "info": {
                "Original area": "1.3 million km2",
                "Remaining": "~100,000 km2 (only 7-8%!)",
                "Country": "Brazil (primarily), Paraguay, Argentina",
                "Biodiversity": "20,000 plant species, 950 bird species",
                "Key species": "Golden lion tamarin, muriqui, jaguar",
                "Deforestation": "~93% lost — most devastated major rainforest",
                "Status": "Biodiversity Hotspot (Conservation International)",
            },
        },
    }

    for name, data in rainforest_data.items():
        folium.Polygon(
            locations=data["polygon"], color=data["color"],
            fill=True, fill_color=data["color"],
            fill_opacity=0.3, opacity=0.7, weight=2,
            popup=folium.Popup(_popup_html(name, data["info"], data["color"]), max_width=340),
        ).add_to(m)

    stats = {"Rainforests mapped": "7", "Total area": "~8.5M km2 remaining",
             "Most devastated": "Atlantic Forest (93% lost)", "Oldest": "Daintree (180M yrs)"}
    rows = []
    for name, data in rainforest_data.items():
        rows.append({
            "Rainforest": name,
            "Area": data["info"].get("Area", data["info"].get("Remaining", "")),
            "Deforestation": data["info"].get("Deforestation", "N/A"),
        })
    df = pd.DataFrame(rows)
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# MAP 8 — MIGRATORY BIRD FLYWAYS
# ═══════════════════════════════════════════════════════════════
def _build_flyway_map() -> tuple:
    """8 major migratory bird flyways of the world."""
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    flyways = {
        "Atlantic Americas": {
            "color": FLYWAY_COLORS["Atlantic Americas"],
            "path": [(70, -60), (60, -62), (50, -65), (40, -72),
                     (30, -78), (20, -75), (10, -65), (0, -55),
                     (-10, -48), (-20, -42), (-35, -52), (-50, -60)],
            "info": {
                "Region": "Eastern Americas (Atlantic coast)",
                "Distance": "Up to 15,000 km",
                "Key species": "Red knot, semipalmated sandpiper, snow goose",
                "Stopover sites": "Delaware Bay, Caribbean coast, Patagonia",
                "Threats": "Habitat loss, hunting, horseshoe crab decline",
                "Birds using flyway": "~500 species",
            },
        },
        "Pacific Americas": {
            "color": FLYWAY_COLORS["Pacific Americas"],
            "path": [(70, -160), (60, -150), (50, -135), (40, -125),
                     (30, -118), (20, -110), (10, -100), (0, -85),
                     (-10, -78), (-20, -72), (-35, -72), (-50, -72)],
            "info": {
                "Region": "Western Americas (Pacific coast)",
                "Distance": "Up to 20,000 km",
                "Key species": "Bar-tailed godwit, western sandpiper, osprey",
                "Stopover sites": "Copper River Delta, San Francisco Bay, Gulf of California",
                "Threats": "Wetland drainage, pollution, wind farms",
                "Birds using flyway": "~400 species",
            },
        },
        "Mississippi": {
            "color": FLYWAY_COLORS["Mississippi"],
            "path": [(65, -95), (55, -92), (45, -90), (38, -90),
                     (30, -90), (25, -90), (20, -88), (15, -85),
                     (10, -80), (5, -75), (-5, -60)],
            "info": {
                "Region": "Central Americas (Mississippi River corridor)",
                "Distance": "Up to 12,000 km",
                "Key species": "Whooping crane, Mississippi kite, prothonotary warbler",
                "Stopover sites": "Great Lakes, Gulf Coast, Mississippi Delta",
                "Threats": "Wetland loss, light pollution, pesticides",
                "Birds using flyway": "~350 species",
            },
        },
        "East Atlantic": {
            "color": FLYWAY_COLORS["East Atlantic"],
            "path": [(75, 20), (65, 5), (55, -5), (45, -8),
                     (35, -10), (25, -15), (15, -15), (5, -5),
                     (-5, 10), (-15, 12), (-25, 15), (-35, 18)],
            "info": {
                "Region": "Western Europe to West Africa",
                "Distance": "Up to 12,000 km",
                "Key species": "Bar-tailed godwit, dunlin, knot, spoonbill",
                "Stopover sites": "Wadden Sea (UNESCO), Banc d'Arguin, Bijagos",
                "Threats": "Tidal flat reclamation, oil spills, hunting",
                "Birds using flyway": "~400 species",
            },
        },
        "Black Sea / Mediterranean": {
            "color": FLYWAY_COLORS["Black Sea / Mediterranean"],
            "path": [(55, 25), (48, 30), (42, 30), (38, 32),
                     (35, 34), (30, 33), (25, 33), (20, 35),
                     (15, 38), (10, 40), (5, 38), (0, 35), (-5, 35)],
            "info": {
                "Region": "Eastern Europe, Middle East, East Africa",
                "Distance": "Up to 10,000 km",
                "Key species": "White stork, lesser spotted eagle, Eurasian crane",
                "Stopover sites": "Bosphorus, Hula Valley, Rift Valley lakes",
                "Bottlenecks": "Gibraltar, Bosphorus, Suez (raptor funnels)",
                "Birds using flyway": "~300 species",
            },
        },
        "Central Asian": {
            "color": FLYWAY_COLORS["Central Asian"],
            "path": [(70, 70), (60, 65), (50, 60), (42, 55),
                     (35, 55), (30, 60), (25, 65), (20, 70),
                     (15, 72), (10, 75), (5, 78), (0, 80)],
            "info": {
                "Region": "Central Asia to Indian subcontinent",
                "Distance": "Up to 8,000 km",
                "Key species": "Siberian crane, bar-headed goose, demoiselle crane",
                "Stopover sites": "Aral Sea region, Indus Delta, Chilika Lake",
                "Famous crossing": "Bar-headed goose over Himalayas at 8,800 m",
                "Birds using flyway": "~250 species",
            },
        },
        "East Asian-Australasian": {
            "color": FLYWAY_COLORS["East Asian-Australasian"],
            "path": [(70, 170), (60, 150), (50, 135), (40, 125),
                     (30, 120), (20, 115), (10, 110), (0, 108),
                     (-10, 115), (-20, 130), (-30, 140), (-40, 145)],
            "info": {
                "Region": "East Asia to Australia/New Zealand",
                "Distance": "Up to 13,000 km",
                "Key species": "Spoon-billed sandpiper, great knot, bar-tailed godwit",
                "Stopover sites": "Yellow Sea mudflats (critical!), Ariake Bay",
                "Threats": "Massive tidal flat loss in Yellow Sea (65% lost)",
                "Birds using flyway": "~500 species (50M+ waterbirds)",
            },
        },
        "West Pacific": {
            "color": FLYWAY_COLORS["West Pacific"],
            "path": [(60, -175), (50, -170), (40, -165), (30, -160),
                     (20, -158), (10, -155), (0, -160), (-10, -170),
                     (-20, -175), (-30, 175), (-40, 170)],
            "info": {
                "Region": "Pacific Islands, Alaska to New Zealand",
                "Distance": "Up to 12,000 km",
                "Key species": "Bristle-thighed curlew, golden plover, wandering tattler",
                "Stopover sites": "Hawaiian Islands, Marshall Islands, Fiji",
                "Threats": "Sea level rise, invasive predators on islands",
                "Birds using flyway": "~200 species",
            },
        },
    }

    for name, data in flyways.items():
        folium.PolyLine(
            locations=data["path"], color=data["color"],
            weight=4, opacity=0.8,
            popup=folium.Popup(_popup_html(name + " Flyway", data["info"], data["color"]), max_width=340),
        ).add_to(m)
        # Add arrow markers at midpoint
        mid_idx = len(data["path"]) // 2
        lat, lon = data["path"][mid_idx]
        folium.CircleMarker(
            location=[lat, lon], radius=5, color=data["color"],
            fill=True, fill_color=data["color"], fill_opacity=0.9,
        ).add_to(m)

    stats = {"Flyways mapped": "8", "Total migratory species": "~4,000+",
             "Longest migration": "Bar-tailed godwit (11,000 km non-stop)", "Highest flight": "Bar-headed goose (8,800 m)"}
    rows = []
    for name, data in flyways.items():
        rows.append({
            "Flyway": name,
            "Region": data["info"]["Region"],
            "Distance": data["info"]["Distance"],
            "Key Species": data["info"]["Key species"][:50],
        })
    df = pd.DataFrame(rows)
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# MAP 9 — VENOMOUS ANIMALS HOTSPOTS
# ═══════════════════════════════════════════════════════════════
def _build_venomous_map() -> tuple:
    """Venomous animal hotspots worldwide."""
    m = folium.Map(location=[15, 50], zoom_start=2, tiles="CartoDB dark_matter")

    # Venomous snakes hotspots
    snake_zones = [
        (-25, 134, 18, "Australia — Inland Taipan & Eastern Brown",
         "Most venomous land snakes on Earth; 100+ venomous species",
         "Extreme — 21 of 25 most venomous snakes"),
        (22, 80, 15, "India — King Cobra & Saw-scaled Viper",
         "Big Four: Cobra, Krait, Russell's Viper, Saw-scaled Viper; ~50,000 deaths/yr",
         "Extreme — highest snakebite mortality worldwide"),
        (5, 25, 14, "Sub-Saharan Africa — Black Mamba & Puff Adder",
         "Black mamba (fastest snake), puff adder (most bites in Africa), Gaboon viper",
         "Very High — 30,000+ deaths/yr across continent"),
        (12, 105, 12, "SE Asia — King Cobra & Malayan Pit Viper",
         "Dense snake populations in tropical forests; many elapids and vipers",
         "Very High — high envenomation rates"),
        (-15, -55, 12, "Brazil — Bushmaster & Fer-de-lance",
         "Bothrops genus responsible for most bites; bushmaster is largest pit viper",
         "High — dense populations in rainforest"),
        (33, -110, 8, "SW United States — Rattlesnakes",
         "Western diamondback, Mojave rattlesnake; ~8,000 bites/yr in US",
         "Moderate — good medical access"),
    ]
    for lat, lon, radius, name, desc, danger in snake_zones:
        folium.CircleMarker(
            location=[lat, lon], radius=radius,
            color=VENOM_COLORS["Venomous Snakes"],
            fill=True, fill_color=VENOM_COLORS["Venomous Snakes"],
            fill_opacity=0.4, opacity=0.7,
            popup=folium.Popup(_popup_html(name, {
                "Type": "Venomous Snakes",
                "Description": desc,
                "Danger rating": danger,
                "Global deaths": "~81,000-138,000/yr from snakebite",
            }, VENOM_COLORS["Venomous Snakes"]), max_width=340),
        ).add_to(m)

    # Scorpion hotspots
    scorpion_zones = [
        (25, 5, 14, "Sahara / North Africa — Deathstalker Scorpion",
         "Androctonus, Leiurus quinquestriatus; extremely potent neurotoxin",
         "Extreme — most dangerous scorpion region"),
        (30, 45, 10, "Middle East — Fat-tailed Scorpion",
         "Androctonus crassicauda; 5,000+ stings/yr in Saudi Arabia",
         "Very High — arid habitat favors scorpions"),
        (32, -112, 8, "SW US / Mexico — Arizona Bark Scorpion",
         "Centruroides sculpturatus; only lethal US scorpion",
         "Moderate — effective antivenom available"),
        (22, 78, 8, "India — Red Scorpion",
         "Hottentotta tamulus; significant rural health burden",
         "High — rural areas lack antivenom access"),
    ]
    for lat, lon, radius, name, desc, danger in scorpion_zones:
        folium.CircleMarker(
            location=[lat, lon], radius=radius,
            color=VENOM_COLORS["Scorpions"],
            fill=True, fill_color=VENOM_COLORS["Scorpions"],
            fill_opacity=0.4, opacity=0.7,
            popup=folium.Popup(_popup_html(name, {
                "Type": "Scorpions",
                "Description": desc,
                "Danger rating": danger,
                "Global deaths": "~3,250/yr from scorpion stings",
            }, VENOM_COLORS["Scorpions"]), max_width=340),
        ).add_to(m)

    # Spider hotspots
    spider_zones = [
        (-33, 151, 10, "Australia — Sydney Funnel-web Spider",
         "Atrax robustus; one of most dangerous spiders. Also redback spider continent-wide",
         "High — antivenom has prevented deaths since 1981"),
        (-15, -47, 10, "Brazil — Brazilian Wandering Spider",
         "Phoneutria; most venomous spider (Guinness). Also brown recluse (Loxosceles)",
         "High — spider enters homes; painful envenomation"),
        (35, -90, 6, "Southern US — Brown Recluse & Black Widow",
         "Loxosceles reclusa & Latrodectus mactans; common in homes",
         "Moderate — rarely fatal with treatment"),
    ]
    for lat, lon, radius, name, desc, danger in spider_zones:
        folium.CircleMarker(
            location=[lat, lon], radius=radius,
            color=VENOM_COLORS["Spiders"],
            fill=True, fill_color=VENOM_COLORS["Spiders"],
            fill_opacity=0.4, opacity=0.7,
            popup=folium.Popup(_popup_html(name, {
                "Type": "Spiders",
                "Description": desc,
                "Danger rating": danger,
                "Note": "Very few spider species dangerous to humans",
            }, VENOM_COLORS["Spiders"]), max_width=340),
        ).add_to(m)

    # Box jellyfish
    jellyfish_zones = [
        (-16, 146, 10, "Box Jellyfish — NE Australia",
         "Chironex fleckeri; most venomous marine animal. ~80 deaths since 1883 in Australia",
         "Extreme — can kill in 2-5 minutes"),
        (10, 115, 8, "Box Jellyfish — Philippines / SE Asia",
         "Chiropsalmus & Chironex; underreported deaths in developing nations",
         "Very High — many unreported fatalities"),
        (7, 80, 6, "Box Jellyfish — Indian Ocean / Sri Lanka",
         "Seasonal blooms; increasing encounters with warming oceans",
         "High — increasing risk with climate change"),
    ]
    for lat, lon, radius, name, desc, danger in jellyfish_zones:
        folium.CircleMarker(
            location=[lat, lon], radius=radius,
            color=VENOM_COLORS["Box Jellyfish"],
            fill=True, fill_color=VENOM_COLORS["Box Jellyfish"],
            fill_opacity=0.4, opacity=0.7,
            popup=folium.Popup(_popup_html(name, {
                "Type": "Box Jellyfish",
                "Description": desc,
                "Danger rating": danger,
                "Season": "Primarily October-May (tropical wet season)",
            }, VENOM_COLORS["Box Jellyfish"]), max_width=340),
        ).add_to(m)

    # Cone snails
    cone_zones = [
        (-10, 145, 6, "Cone Snails — Indo-Pacific / Great Barrier Reef",
         "Conus geographus; geography cone can kill humans. ~30 recorded deaths",
         "High — no antivenom exists"),
        (0, 120, 5, "Cone Snails — Coral Triangle",
         "High diversity of venomous Conus species in reef habitats",
         "Moderate — rare human encounters"),
        (20, -87, 4, "Cone Snails — Caribbean",
         "Lower diversity but still dangerous Conus species present",
         "Low-Moderate — fewer dangerous species"),
    ]
    for lat, lon, radius, name, desc, danger in cone_zones:
        folium.CircleMarker(
            location=[lat, lon], radius=radius,
            color=VENOM_COLORS["Cone Snails"],
            fill=True, fill_color=VENOM_COLORS["Cone Snails"],
            fill_opacity=0.4, opacity=0.7,
            popup=folium.Popup(_popup_html(name, {
                "Type": "Cone Snails",
                "Description": desc,
                "Danger rating": danger,
                "Medical use": "Cone snail venom used in pain medication (Ziconotide)",
            }, VENOM_COLORS["Cone Snails"]), max_width=340),
        ).add_to(m)

    stats = {"Hotspot zones": str(len(snake_zones) + len(scorpion_zones) + len(spider_zones) + len(jellyfish_zones) + len(cone_zones)),
             "Snakebite deaths/yr": "~81,000-138,000",
             "Most venomous land": "Inland Taipan (Australia)",
             "Most venomous marine": "Box Jellyfish"}
    rows = []
    for zones, vtype in [(snake_zones, "Snake"), (scorpion_zones, "Scorpion"),
                         (spider_zones, "Spider"), (jellyfish_zones, "Box Jellyfish"),
                         (cone_zones, "Cone Snail")]:
        for lat, lon, radius, name, desc, danger in zones:
            rows.append({"Type": vtype, "Name": name, "Danger Rating": danger, "Lat": lat, "Lon": lon})
    df = pd.DataFrame(rows)
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# MAP 10 — BIODIVERSITY HOTSPOTS
# ═══════════════════════════════════════════════════════════════
def _build_biodiversity_hotspots_map() -> tuple:
    """36 Conservation International biodiversity hotspots."""
    m = folium.Map(location=[15, 20], zoom_start=2, tiles="CartoDB dark_matter")

    # Color palette for 36 hotspots (cycle through)
    hotspot_palette = [
        "#ef4444", "#f97316", "#f59e0b", "#eab308", "#84cc16",
        "#22c55e", "#10b981", "#14b8a6", "#06b6d4", "#0ea5e9",
        "#3b82f6", "#6366f1", "#8b5cf6", "#a855f7", "#d946ef",
        "#ec4899", "#f43f5e", "#fb923c", "#fbbf24", "#a3e635",
        "#4ade80", "#2dd4bf", "#22d3ee", "#38bdf8", "#818cf8",
        "#c084fc", "#e879f9", "#f472b6", "#fb7185", "#fdba74",
        "#fcd34d", "#bef264", "#86efac", "#5eead4", "#67e8f9",
        "#93c5fd",
    ]

    hotspots = [
        {"name": "Tropical Andes", "lat": -5, "lon": -75,
         "polygon": [(-8, -79), (-2, -78), (5, -76), (10, -74), (8, -72), (2, -73), (-5, -76), (-8, -79)],
         "species": 30000, "endemic": 50, "area_remaining": 25, "threat": "High",
         "desc": "Richest hotspot on Earth; cloud forests, paramo, high Andean lakes"},
        {"name": "Mesoamerica", "lat": 14, "lon": -87,
         "polygon": [(8, -83), (10, -80), (15, -88), (18, -92), (20, -97), (18, -100), (14, -92), (8, -83)],
         "species": 17000, "endemic": 33, "area_remaining": 20, "threat": "Very High",
         "desc": "Biodiversity bridge between North and South America"},
        {"name": "Caribbean Islands", "lat": 19, "lon": -72,
         "polygon": [(15, -78), (18, -80), (22, -78), (23, -73), (20, -65), (17, -63), (15, -68), (15, -78)],
         "species": 13000, "endemic": 50, "area_remaining": 11, "threat": "Critical",
         "desc": "Highly endemic island biodiversity; massive habitat loss"},
        {"name": "Atlantic Forest", "lat": -15, "lon": -42,
         "polygon": [(-5, -35), (-10, -37), (-15, -40), (-20, -43), (-25, -48), (-28, -50), (-25, -46), (-18, -41), (-10, -36), (-5, -35)],
         "species": 20000, "endemic": 40, "area_remaining": 8, "threat": "Critical",
         "desc": "One of most threatened; only ~8% remaining of original forest"},
        {"name": "Cerrado", "lat": -14, "lon": -48,
         "polygon": [(-5, -50), (-8, -45), (-12, -42), (-18, -45), (-22, -50), (-18, -55), (-10, -52), (-5, -50)],
         "species": 12000, "endemic": 35, "area_remaining": 20, "threat": "Very High",
         "desc": "World's most biodiverse savanna; soy expansion major threat"},
        {"name": "Chilean Valdivian Forests", "lat": -40, "lon": -72,
         "polygon": [(-35, -72), (-38, -73), (-42, -73), (-45, -74), (-45, -72), (-42, -71), (-38, -71), (-35, -72)],
         "species": 3900, "endemic": 50, "area_remaining": 30, "threat": "High",
         "desc": "Temperate rainforests with ancient araucaria trees"},
        {"name": "Mediterranean Basin", "lat": 38, "lon": 15,
         "polygon": [(30, -5), (35, 0), (40, 5), (42, 15), (40, 25), (35, 30), (30, 30), (30, 20), (32, 10), (30, -5)],
         "species": 22500, "endemic": 52, "area_remaining": 5, "threat": "Critical",
         "desc": "Olive groves, maquis, cork oak; 5,000+ years of human impact"},
        {"name": "Caucasus", "lat": 42, "lon": 44,
         "polygon": [(40, 38), (42, 40), (44, 44), (43, 48), (41, 48), (40, 44), (39, 40), (40, 38)],
         "species": 6300, "endemic": 25, "area_remaining": 10, "threat": "Very High",
         "desc": "Mountain biodiversity corridor between Europe and Asia"},
        {"name": "Guinean Forests of West Africa", "lat": 6, "lon": -5,
         "polygon": [(3, -12), (5, -8), (8, -4), (8, 2), (6, 5), (4, 5), (3, 0), (3, -5), (3, -12)],
         "species": 9000, "endemic": 27, "area_remaining": 15, "threat": "Very High",
         "desc": "Upper and Lower Guinea forests; chimpanzee, pygmy hippo habitat"},
        {"name": "Succulent Karoo", "lat": -30, "lon": 19,
         "polygon": [(-28, 17), (-29, 18), (-31, 19), (-33, 19), (-33, 18), (-31, 17), (-29, 16), (-28, 17)],
         "species": 6356, "endemic": 40, "area_remaining": 29, "threat": "High",
         "desc": "World's richest succulent flora; unique fog-driven ecosystem"},
        {"name": "Cape Floristic Region", "lat": -34, "lon": 19,
         "polygon": [(-32, 18), (-33, 18), (-34, 19), (-35, 20), (-34, 22), (-33, 21), (-32, 20), (-32, 18)],
         "species": 9000, "endemic": 69, "area_remaining": 18, "threat": "High",
         "desc": "Fynbos biome; smallest and richest floral kingdom on Earth"},
        {"name": "Coastal Forests of Eastern Africa", "lat": -6, "lon": 38,
         "polygon": [(-1, 39), (-3, 40), (-7, 39), (-10, 38), (-10, 37), (-7, 37), (-3, 38), (-1, 39)],
         "species": 4000, "endemic": 25, "area_remaining": 10, "threat": "Very High",
         "desc": "Fragments of ancient forest along East African coast"},
        {"name": "Eastern Afromontane", "lat": 0, "lon": 35,
         "polygon": [(10, 38), (5, 36), (0, 33), (-5, 32), (-10, 34), (-5, 36), (0, 37), (5, 38), (10, 38)],
         "species": 7600, "endemic": 32, "area_remaining": 11, "threat": "Very High",
         "desc": "Mountain chain from Ethiopia to Mozambique; Ethiopian wolf habitat"},
        {"name": "Horn of Africa", "lat": 8, "lon": 46,
         "polygon": [(5, 42), (8, 45), (12, 48), (14, 50), (12, 50), (8, 48), (5, 45), (5, 42)],
         "species": 5000, "endemic": 29, "area_remaining": 5, "threat": "Critical",
         "desc": "Driest hotspot; Socotra Island endemics, frankincense trees"},
        {"name": "Madagascar & Indian Ocean", "lat": -18, "lon": 47,
         "polygon": [(-12, 49), (-14, 50), (-18, 50), (-22, 48), (-25, 47), (-25, 44), (-22, 44), (-18, 44), (-14, 46), (-12, 49)],
         "species": 12000, "endemic": 89, "area_remaining": 10, "threat": "Critical",
         "desc": "Extreme endemism (89%!); lemurs, chameleons, baobabs"},
        {"name": "Maputaland-Pondoland-Albany", "lat": -30, "lon": 30,
         "polygon": [(-25, 30), (-28, 32), (-32, 30), (-34, 28), (-32, 27), (-28, 28), (-25, 30)],
         "species": 8100, "endemic": 23, "area_remaining": 18, "threat": "High",
         "desc": "Coastal forests and grasslands of southern Africa"},
        {"name": "Mountains of Central Asia", "lat": 40, "lon": 70,
         "polygon": [(35, 65), (38, 68), (42, 72), (42, 78), (40, 78), (37, 74), (35, 70), (35, 65)],
         "species": 5500, "endemic": 29, "area_remaining": 15, "threat": "High",
         "desc": "Snow leopard, argali sheep; ancient walnut-fruit forests"},
        {"name": "Western Ghats & Sri Lanka", "lat": 12, "lon": 76,
         "polygon": [(8, 75), (10, 76), (14, 76), (18, 74), (20, 73), (18, 73), (14, 74), (10, 75), (8, 75)],
         "species": 5916, "endemic": 52, "area_remaining": 7, "threat": "Critical",
         "desc": "Ancient mountain chain; lion-tailed macaque, Nilgiri tahr"},
        {"name": "Indo-Burma", "lat": 18, "lon": 100,
         "polygon": [(10, 92), (15, 95), (22, 100), (25, 105), (22, 108), (15, 106), (10, 100), (10, 92)],
         "species": 13500, "endemic": 52, "area_remaining": 5, "threat": "Critical",
         "desc": "SE Asian mainland forests; saola, Tonkin snub-nosed monkey"},
        {"name": "Sundaland", "lat": 0, "lon": 110,
         "polygon": [(-5, 100), (-2, 105), (2, 110), (5, 115), (5, 118), (2, 118), (-2, 115), (-5, 108), (-5, 100)],
         "species": 25000, "endemic": 60, "area_remaining": 8, "threat": "Critical",
         "desc": "Borneo, Sumatra, Java, Malay Peninsula; orangutan, Sumatran rhino"},
        {"name": "Wallacea", "lat": -3, "lon": 125,
         "polygon": [(-1, 118), (0, 122), (-1, 127), (-4, 130), (-7, 130), (-8, 127), (-5, 123), (-3, 118), (-1, 118)],
         "species": 10000, "endemic": 50, "area_remaining": 15, "threat": "Very High",
         "desc": "Sulawesi, Moluccas, Lesser Sundas; between Wallace and Lydekker lines"},
        {"name": "Philippines", "lat": 12, "lon": 122,
         "polygon": [(5, 118), (8, 120), (12, 122), (15, 121), (18, 122), (18, 124), (14, 125), (10, 124), (6, 122), (5, 118)],
         "species": 9253, "endemic": 50, "area_remaining": 7, "threat": "Critical",
         "desc": "7,107 islands with extreme endemism; Philippine eagle"},
        {"name": "Southwest Australia", "lat": -33, "lon": 118,
         "polygon": [(-28, 114), (-30, 116), (-34, 118), (-35, 120), (-35, 118), (-33, 115), (-30, 114), (-28, 114)],
         "species": 5571, "endemic": 49, "area_remaining": 11, "threat": "Very High",
         "desc": "Kwongan heathlands; world-class plant diversity in ancient soils"},
        {"name": "New Zealand", "lat": -42, "lon": 172,
         "polygon": [(-35, 173), (-38, 175), (-42, 174), (-46, 168), (-46, 166), (-43, 170), (-38, 173), (-35, 173)],
         "species": 2300, "endemic": 70, "area_remaining": 22, "threat": "High",
         "desc": "Kiwi, tuatara, kakapo; devastated by introduced mammals"},
        {"name": "Polynesia-Micronesia", "lat": -10, "lon": -170,
         "polygon": [(-5, -175), (-8, -172), (-15, -168), (-18, -170), (-15, -175), (-10, -178), (-5, -175)],
         "species": 5330, "endemic": 63, "area_remaining": 21, "threat": "Very High",
         "desc": "Scattered Pacific islands; highest bird extinction rate on Earth"},
        {"name": "East Melanesian Islands", "lat": -8, "lon": 160,
         "polygon": [(-5, 155), (-6, 158), (-9, 162), (-12, 165), (-12, 162), (-9, 158), (-6, 155), (-5, 155)],
         "species": 8000, "endemic": 20, "area_remaining": 30, "threat": "High",
         "desc": "Solomon Islands, Vanuatu, Bismarck; bird and plant endemism"},
        {"name": "New Caledonia", "lat": -21, "lon": 165,
         "polygon": [(-19, 164), (-20, 165), (-22, 167), (-23, 167), (-22, 165), (-20, 164), (-19, 164)],
         "species": 3270, "endemic": 74, "area_remaining": 28, "threat": "High",
         "desc": "Ancient Gondwanan relict; 74% plant endemism; mining threat"},
        {"name": "Japan", "lat": 35, "lon": 136,
         "polygon": [(30, 130), (33, 132), (36, 136), (40, 140), (42, 142), (40, 144), (36, 140), (33, 136), (30, 130)],
         "species": 5600, "endemic": 40, "area_remaining": 25, "threat": "High",
         "desc": "Temperate forests with high endemism; Japanese macaque, giant salamander"},
        {"name": "Mountains of SW China", "lat": 28, "lon": 100,
         "polygon": [(24, 96), (26, 98), (30, 100), (32, 104), (30, 104), (26, 102), (24, 100), (24, 96)],
         "species": 12000, "endemic": 29, "area_remaining": 8, "threat": "Critical",
         "desc": "Hengduan Mountains; giant panda, red panda, golden snub-nosed monkey"},
        {"name": "Himalaya", "lat": 28, "lon": 84,
         "polygon": [(26, 72), (28, 78), (29, 84), (28, 90), (27, 95), (26, 92), (27, 86), (27, 80), (26, 72)],
         "species": 10000, "endemic": 32, "area_remaining": 25, "threat": "High",
         "desc": "Highest mountains; snow leopard, red panda, Himalayan monal"},
        {"name": "Irano-Anatolian", "lat": 37, "lon": 45,
         "polygon": [(33, 38), (36, 42), (38, 48), (40, 52), (38, 56), (35, 52), (33, 46), (33, 38)],
         "species": 6000, "endemic": 25, "area_remaining": 15, "threat": "High",
         "desc": "Origin center for wheat and fruit trees; Persian leopard habitat"},
        {"name": "Forests of East Australia", "lat": -30, "lon": 152,
         "polygon": [(-20, 148), (-24, 150), (-28, 152), (-33, 152), (-36, 150), (-33, 150), (-28, 150), (-24, 148), (-20, 148)],
         "species": 8257, "endemic": 30, "area_remaining": 18, "threat": "High",
         "desc": "Subtropical to temperate rainforests; koala, platypus, lyrebird"},
        {"name": "Horn of Africa (Coastal)", "lat": 2, "lon": 42,
         "polygon": [(-2, 40), (0, 42), (3, 44), (5, 46), (3, 46), (0, 44), (-2, 42), (-2, 40)],
         "species": 2750, "endemic": 25, "area_remaining": 10, "threat": "Very High",
         "desc": "Coastal Kenya/Tanzania; coral reefs and coastal forests"},
        {"name": "California Floristic Province", "lat": 37, "lon": -120,
         "polygon": [(32, -122), (34, -120), (37, -122), (40, -124), (42, -124), (40, -122), (37, -120), (34, -118), (32, -122)],
         "species": 3488, "endemic": 61, "area_remaining": 25, "threat": "High",
         "desc": "Chaparral, redwood forests, serpentine endemics; condor habitat"},
        {"name": "Madrean Pine-Oak Woodlands", "lat": 25, "lon": -105,
         "polygon": [(20, -108), (23, -106), (28, -105), (30, -108), (28, -110), (25, -108), (22, -108), (20, -108)],
         "species": 5300, "endemic": 31, "area_remaining": 20, "threat": "High",
         "desc": "Mexican highlands; world's highest pine and oak diversity"},
        {"name": "Tumbes-Choco-Magdalena", "lat": 3, "lon": -78,
         "polygon": [(8, -77), (5, -78), (2, -79), (-2, -80), (-5, -80), (-3, -78), (0, -77), (3, -76), (8, -77)],
         "species": 11000, "endemic": 25, "area_remaining": 24, "threat": "High",
         "desc": "Pacific coast from Panama to Peru; Choco rainforest, incredible rainfall"},
    ]

    for i, hs in enumerate(hotspots):
        color = hotspot_palette[i % len(hotspot_palette)]
        folium.Polygon(
            locations=hs["polygon"], color=color,
            fill=True, fill_color=color,
            fill_opacity=0.3, opacity=0.7, weight=2,
            popup=folium.Popup(_popup_html(hs["name"], {
                "Plant species": f"~{hs['species']:,}",
                "Endemic species": f"{hs['endemic']}%",
                "Original habitat remaining": f"{hs['area_remaining']}%",
                "Threat level": hs["threat"],
                "Description": hs["desc"],
            }, color), max_width=340),
        ).add_to(m)

    stats = {"Hotspots mapped": str(len(hotspots)),
             "Total plant species": f"{sum(h['species'] for h in hotspots):,}",
             "Highest endemism": "Madagascar (89%)",
             "Most threatened": "Horn of Africa (5% remaining)"}
    rows = []
    for hs in hotspots:
        rows.append({
            "Hotspot": hs["name"],
            "Species": f"~{hs['species']:,}",
            "Endemic %": f"{hs['endemic']}%",
            "Remaining %": f"{hs['area_remaining']}%",
            "Threat": hs["threat"],
        })
    df = pd.DataFrame(rows)
    return m, stats, df


# ═══════════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════════
def _make_bar_chart(labels: list, values: list, title: str, color: str = "#06b6d4",
                    ylabel: str = "Count") -> plt.Figure:
    """Create a dark-themed horizontal bar chart."""
    fig, ax = plt.subplots(figsize=(8, max(3, len(labels) * 0.4)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    bars = ax.barh(labels, values, color=color, alpha=0.8, edgecolor="#2a3550")
    ax.set_xlabel(ylabel, color="#8b97b0", fontsize=10)
    ax.set_title(title, color="#e8ecf4", fontsize=13, fontweight="bold", pad=12)
    ax.tick_params(colors="#8b97b0", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#2a3550")
    ax.spines["left"].set_color("#2a3550")
    ax.invert_yaxis()

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:,}" if isinstance(val, int) else str(val),
                va="center", ha="left", color="#e8ecf4", fontsize=9)

    fig.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════
MAP_OPTIONS = [
    "Marsupial Distribution",
    "Big Cat Territories",
    "Primate Distribution",
    "Marine Megafauna",
    "Wallace Line & Biogeographic Realms",
    "Coral Reef Distribution",
    "Rainforest Coverage",
    "Migratory Bird Flyways",
    "Venomous Animals Hotspots",
    "Biodiversity Hotspots",
]

MAP_DESCRIPTIONS = {
    "Marsupial Distribution": "Australasian marsupials and Americas opossums with the Wallace Line boundary.",
    "Big Cat Territories": "Global ranges of lions, tigers, leopards, jaguars, cheetahs, snow leopards, and cougars.",
    "Primate Distribution": "Great apes (gorilla, chimpanzee, orangutan, bonobo) and monkey regions worldwide.",
    "Marine Megafauna": "Whale migration routes, great white shark zones, dolphin hotspots, and sea turtle nesting.",
    "Wallace Line & Biogeographic Realms": "Eight biogeographic realms and the Wallace, Weber, and Lydekker lines.",
    "Coral Reef Distribution": "Major coral reef systems from the Great Barrier Reef to the Caribbean.",
    "Rainforest Coverage": "Major tropical and temperate rainforests with deforestation statistics.",
    "Migratory Bird Flyways": "Eight major flyways connecting breeding and wintering grounds worldwide.",
    "Venomous Animals Hotspots": "Dangerous zones for venomous snakes, scorpions, spiders, jellyfish, and cone snails.",
    "Biodiversity Hotspots": "36 Conservation International biodiversity hotspots with species and threat data.",
}

MAP_BUILDERS = {
    "Marsupial Distribution": _build_marsupial_map,
    "Big Cat Territories": _build_big_cat_map,
    "Primate Distribution": _build_primate_map,
    "Marine Megafauna": _build_marine_map,
    "Wallace Line & Biogeographic Realms": _build_realms_map,
    "Coral Reef Distribution": _build_coral_map,
    "Rainforest Coverage": _build_rainforest_map,
    "Migratory Bird Flyways": _build_flyway_map,
    "Venomous Animals Hotspots": _build_venomous_map,
    "Biodiversity Hotspots": _build_biodiversity_hotspots_map,
}


def render_biogeography_maps_tab():
    """Render the Biogeography & Species Distribution Maps tab."""
    st.markdown(
        '<div class="tab-header emerald">'
        "<h4>Biogeography &amp; Species Maps</h4>"
        "<p>Animal distribution, migration routes, and biodiversity hotspots</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Map selection
    col_sel, col_desc = st.columns([1, 2])
    with col_sel:
        selected_map = st.selectbox(
            "Select map type",
            options=MAP_OPTIONS,
            index=0,
            key="biogeography_map_select",
        )
    with col_desc:
        st.info(MAP_DESCRIPTIONS.get(selected_map, ""))

    st.markdown("---")

    # Build the selected map
    with st.spinner(f"Building {selected_map} map..."):
        builder = MAP_BUILDERS[selected_map]
        folium_map, stats, df = builder()

    # Stats row
    stat_cols = st.columns(len(stats))
    for col, (label, value) in zip(stat_cols, stats.items()):
        col.metric(label=label, value=value)

    st.markdown("")

    # Render the folium map
    components.html(folium_map._repr_html_(), height=600)

    # Chart section (contextual per map)
    st.markdown("### Data Summary")

    if selected_map == "Biodiversity Hotspots" and not df.empty:
        # Sort by endemic %
        chart_df = df.copy()
        chart_df["Endemic_val"] = chart_df["Endemic %"].str.replace("%", "").astype(int)
        chart_df = chart_df.sort_values("Endemic_val", ascending=False).head(15)
        fig = _make_bar_chart(
            chart_df["Hotspot"].tolist(),
            chart_df["Endemic_val"].tolist(),
            "Top 15 Biodiversity Hotspots by Endemism",
            color="#10b981",
            ylabel="Endemic Species %",
        )
        st.pyplot(fig)
        plt.close(fig)
    elif selected_map == "Big Cat Territories" and not df.empty:
        fig = _make_bar_chart(
            df["Species"].tolist(),
            [
                int("".join(c for c in p.split("~")[-1].split()[0].replace(",", "") if c.isdigit()) or 0)
                for p in df["Population"].tolist()
            ],
            "Big Cat Wild Populations (estimated)",
            color="#f59e0b",
            ylabel="Estimated Population",
        )
        st.pyplot(fig)
        plt.close(fig)
    elif selected_map == "Rainforest Coverage" and not df.empty:
        labels = df["Rainforest"].tolist()
        deforest_vals = []
        for d in df["Deforestation"].tolist():
            try:
                val = int("".join(c for c in d.split("~")[-1].split("%")[0] if c.isdigit()))
            except (ValueError, IndexError):
                val = 0
            deforest_vals.append(val)
        fig = _make_bar_chart(
            labels, deforest_vals,
            "Rainforest Deforestation Since 1970",
            color="#ef4444",
            ylabel="% Lost",
        )
        st.pyplot(fig)
        plt.close(fig)
    elif selected_map == "Coral Reef Distribution" and not df.empty:
        threat_map = {"Low": 1, "Moderate": 2, "High": 3, "Very High": 4, "Critical": 5}
        labels = df["Reef System"].tolist()
        threat_vals = []
        for t in df["Threat Level"].tolist():
            for key in ["Critical", "Very High", "High", "Moderate", "Low"]:
                if key.lower() in t.lower():
                    threat_vals.append(threat_map[key])
                    break
            else:
                threat_vals.append(0)
        fig = _make_bar_chart(
            labels, threat_vals,
            "Coral Reef Threat Levels (1=Low, 5=Critical)",
            color="#ef4444",
            ylabel="Threat Level",
        )
        st.pyplot(fig)
        plt.close(fig)

    # Data table
    st.markdown("### Detailed Data")
    st.dataframe(df, width="stretch")

    # Download CSV
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="Download CSV",
        data=csv_buffer.getvalue(),
        file_name=f"biogeography_{selected_map.lower().replace(' ', '_')}.csv",
        mime="text/csv",
        key="biogeography_csv_download",
    )
