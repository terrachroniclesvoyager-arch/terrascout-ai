# -*- coding: utf-8 -*-
"""
Urban Analytics module for TerraScout AI.
Provides 12 urban/city analysis map types using the Overpass API (free).
Covers green spaces, healthcare, education, religious buildings, sports,
shopping, tourism, emergency services, waste/recycling, parking,
street lighting, and building heights.
"""

import io
import json
import html
import math
import streamlit as st
import pandas as pd
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

# ═══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

CITY_PRESETS = {
    "Custom": None,
    "Rome": {"lat": 41.8967, "lon": 12.4822},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Paris": {"lat": 48.8566, "lon": 2.3522},
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "Berlin": {"lat": 52.5200, "lon": 13.4050},
    "Barcelona": {"lat": 41.3874, "lon": 2.1686},
    "Amsterdam": {"lat": 52.3676, "lon": 4.9041},
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
}

MAP_TYPES = [
    "City Green Spaces",
    "Hospital & Healthcare",
    "Schools & Universities",
    "Religious Buildings",
    "Sports Facilities",
    "Shopping & Markets",
    "Tourist Attractions",
    "Emergency Services",
    "Waste & Recycling",
    "Parking Analysis",
    "Street Lighting",
    "Building Heights",
]

# Color palette per map type
MAP_COLORS = {
    "City Green Spaces": {"primary": "#22c55e", "secondary": "#10b981", "accent": "#059669"},
    "Hospital & Healthcare": {"primary": "#ef4444", "secondary": "#f97316", "accent": "#ec4899"},
    "Schools & Universities": {"primary": "#3b82f6", "secondary": "#6366f1", "accent": "#8b5cf6"},
    "Religious Buildings": {"primary": "#f59e0b", "secondary": "#eab308", "accent": "#d97706"},
    "Sports Facilities": {"primary": "#06b6d4", "secondary": "#14b8a6", "accent": "#0891b2"},
    "Shopping & Markets": {"primary": "#ec4899", "secondary": "#f472b6", "accent": "#db2777"},
    "Tourist Attractions": {"primary": "#a855f7", "secondary": "#8b5cf6", "accent": "#7c3aed"},
    "Emergency Services": {"primary": "#dc2626", "secondary": "#f59e0b", "accent": "#2563eb"},
    "Waste & Recycling": {"primary": "#84cc16", "secondary": "#65a30d", "accent": "#4d7c0f"},
    "Parking Analysis": {"primary": "#64748b", "secondary": "#475569", "accent": "#94a3b8"},
    "Street Lighting": {"primary": "#fbbf24", "secondary": "#f59e0b", "accent": "#d97706"},
    "Building Heights": {"primary": "#06b6d4", "secondary": "#8b5cf6", "accent": "#ec4899"},
}


# ═══════════════════════════════════════════════════════════════════════
# OVERPASS QUERY BUILDERS (one per map type)
# ═══════════════════════════════════════════════════════════════════════

def _around_clause(lat: float, lon: float, radius_m: float) -> str:
    return f"around:{radius_m},{lat},{lon}"


@st.cache_data(ttl=3600)
def fetch_green_spaces(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch parks, gardens, forests, nature reserves."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  way["leisure"="park"]({ac});
  way["leisure"="garden"]({ac});
  way["landuse"="forest"]({ac});
  way["leisure"="nature_reserve"]({ac});
  way["landuse"="grass"]({ac});
  way["landuse"="recreation_ground"]({ac});
  relation["leisure"="park"]({ac});
  relation["landuse"="forest"]({ac});
  node["leisure"="park"]({ac});
  node["leisure"="garden"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_healthcare(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch hospitals, clinics, pharmacies, doctors."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  node["amenity"="hospital"]({ac});
  way["amenity"="hospital"]({ac});
  node["amenity"="clinic"]({ac});
  way["amenity"="clinic"]({ac});
  node["amenity"="pharmacy"]({ac});
  node["amenity"="doctors"]({ac});
  node["amenity"="dentist"]({ac});
  node["healthcare"="centre"]({ac});
  way["healthcare"="centre"]({ac});
  node["amenity"="veterinary"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_schools(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch schools, universities, colleges, kindergartens."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  node["amenity"="school"]({ac});
  way["amenity"="school"]({ac});
  node["amenity"="university"]({ac});
  way["amenity"="university"]({ac});
  node["amenity"="college"]({ac});
  way["amenity"="college"]({ac});
  node["amenity"="kindergarten"]({ac});
  way["amenity"="kindergarten"]({ac});
  node["amenity"="library"]({ac});
  way["amenity"="library"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_religious(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch places of worship by religion."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  node["amenity"="place_of_worship"]({ac});
  way["amenity"="place_of_worship"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_sports(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch stadiums, pitches, swimming pools, gyms, sports centres."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  node["leisure"="sports_centre"]({ac});
  way["leisure"="sports_centre"]({ac});
  node["leisure"="stadium"]({ac});
  way["leisure"="stadium"]({ac});
  node["leisure"="swimming_pool"]({ac});
  way["leisure"="swimming_pool"]({ac});
  node["leisure"="pitch"]({ac});
  way["leisure"="pitch"]({ac});
  node["leisure"="fitness_centre"]({ac});
  way["leisure"="fitness_centre"]({ac});
  node["leisure"="track"]({ac});
  way["leisure"="track"]({ac});
  node["leisure"="golf_course"]({ac});
  way["leisure"="golf_course"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_shopping(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch shopping centers, supermarkets, marketplaces."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  node["shop"="supermarket"]({ac});
  way["shop"="supermarket"]({ac});
  node["shop"="mall"]({ac});
  way["shop"="mall"]({ac});
  node["shop"="department_store"]({ac});
  way["shop"="department_store"]({ac});
  node["amenity"="marketplace"]({ac});
  way["amenity"="marketplace"]({ac});
  node["shop"="convenience"]({ac});
  way["shop"="convenience"]({ac});
  node["shop"="wholesale"]({ac});
  way["shop"="wholesale"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_tourist(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch museums, viewpoints, monuments, attractions, artwork."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  node["tourism"="museum"]({ac});
  way["tourism"="museum"]({ac});
  node["tourism"="attraction"]({ac});
  way["tourism"="attraction"]({ac});
  node["tourism"="viewpoint"]({ac});
  node["tourism"="artwork"]({ac});
  node["historic"="monument"]({ac});
  way["historic"="monument"]({ac});
  node["historic"="memorial"]({ac});
  node["tourism"="gallery"]({ac});
  way["tourism"="gallery"]({ac});
  node["tourism"="information"]["information"="guidepost"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_emergency(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch fire stations, police stations, ambulance stations."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  node["amenity"="fire_station"]({ac});
  way["amenity"="fire_station"]({ac});
  node["amenity"="police"]({ac});
  way["amenity"="police"]({ac});
  node["emergency"="ambulance_station"]({ac});
  way["emergency"="ambulance_station"]({ac});
  node["amenity"="hospital"]["emergency"="yes"]({ac});
  way["amenity"="hospital"]["emergency"="yes"]({ac});
  node["emergency"="defibrillator"]({ac});
  node["emergency"="fire_hydrant"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_waste(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch waste facilities, recycling centres, waste baskets."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  node["amenity"="recycling"]({ac});
  way["amenity"="recycling"]({ac});
  node["amenity"="waste_disposal"]({ac});
  way["amenity"="waste_disposal"]({ac});
  node["amenity"="waste_basket"]({ac});
  node["amenity"="waste_transfer_station"]({ac});
  way["amenity"="waste_transfer_station"]({ac});
  node["landuse"="landfill"]({ac});
  way["landuse"="landfill"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_parking(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch parking facilities (surface, underground, multi-storey)."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  node["amenity"="parking"]({ac});
  way["amenity"="parking"]({ac});
  node["amenity"="bicycle_parking"]({ac});
  way["amenity"="bicycle_parking"]({ac});
  node["amenity"="parking_entrance"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_street_lighting(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch streets with lighting information."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  way["highway"]["lit"="yes"]({ac});
  way["highway"]["lit"="no"]({ac});
  node["highway"="street_lamp"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


@st.cache_data(ttl=3600)
def fetch_building_heights(lat: float, lon: float, radius_km: float) -> dict:
    """Fetch buildings with height or building:levels tags."""
    r = radius_km * 1000
    ac = _around_clause(lat, lon, r)
    query = f"""
[out:json][timeout:90];
(
  way["building"]["height"]({ac});
  way["building"]["building:levels"]({ac});
);
out body;
>;
out skel qt;
"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": [], "_error": result.get("_error", "Unknown") if result else "No response"}
    return result


# ═══════════════════════════════════════════════════════════════════════
# ELEMENT EXTRACTION HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _build_node_lookup(elements: list) -> dict:
    """Build a dict mapping node id -> (lat, lon)."""
    lookup = {}
    for el in elements:
        if el.get("type") == "node" and "lat" in el and "lon" in el:
            lookup[el["id"]] = (el["lat"], el["lon"])
    return lookup


def _resolve_coords(el: dict, node_lookup: dict):
    """Return (lat, lon, coords_list) for a node or way element."""
    if el.get("type") == "node" and "lat" in el and "lon" in el:
        return el["lat"], el["lon"], []
    elif el.get("type") == "way":
        nodes = el.get("nodes", [])
        coords = [(node_lookup[n][0], node_lookup[n][1])
                   for n in nodes if n in node_lookup]
        if coords:
            lat = sum(c[0] for c in coords) / len(coords)
            lon = sum(c[1] for c in coords) / len(coords)
            return lat, lon, coords
    return None, None, []


def _extract_generic(data: dict, classify_fn) -> list:
    """
    Generic extractor. classify_fn(tags) should return
    (category_str, color_str) or (None, None) to skip.
    """
    elements = data.get("elements", [])
    node_lookup = _build_node_lookup(elements)
    features = []
    seen = set()
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        eid = (el.get("type"), el.get("id"))
        if eid in seen:
            continue
        seen.add(eid)

        lat, lon, coords = _resolve_coords(el, node_lookup)
        if lat is None:
            continue

        cat, color = classify_fn(tags)
        if cat is None:
            continue

        name = tags.get("name", tags.get("name:en", ""))
        features.append({
            "name": name if name else cat,
            "category": cat,
            "color": color,
            "lat": lat,
            "lon": lon,
            "coords": coords,
            "tags": tags,
            "osm_id": el.get("id"),
            "osm_type": el.get("type"),
        })
    return features


# ═══════════════════════════════════════════════════════════════════════
# CLASSIFIERS (one per map type)
# ═══════════════════════════════════════════════════════════════════════

def _classify_green(tags: dict):
    if tags.get("leisure") == "park":
        return "Park", "#22c55e"
    if tags.get("leisure") == "garden":
        return "Garden", "#10b981"
    if tags.get("landuse") == "forest":
        return "Forest", "#059669"
    if tags.get("leisure") == "nature_reserve":
        return "Nature Reserve", "#16a34a"
    if tags.get("landuse") == "grass":
        return "Grass Area", "#84cc16"
    if tags.get("landuse") == "recreation_ground":
        return "Recreation Ground", "#65a30d"
    return None, None


def _classify_healthcare(tags: dict):
    if tags.get("amenity") == "hospital":
        return "Hospital", "#ef4444"
    if tags.get("amenity") == "clinic":
        return "Clinic", "#f97316"
    if tags.get("amenity") == "pharmacy":
        return "Pharmacy", "#22c55e"
    if tags.get("amenity") == "doctors":
        return "Doctor", "#3b82f6"
    if tags.get("amenity") == "dentist":
        return "Dentist", "#8b5cf6"
    if tags.get("healthcare") == "centre":
        return "Health Centre", "#ec4899"
    if tags.get("amenity") == "veterinary":
        return "Veterinary", "#f59e0b"
    return None, None


def _classify_schools(tags: dict):
    if tags.get("amenity") == "university":
        return "University", "#8b5cf6"
    if tags.get("amenity") == "college":
        return "College", "#6366f1"
    if tags.get("amenity") == "school":
        return "School", "#3b82f6"
    if tags.get("amenity") == "kindergarten":
        return "Kindergarten", "#f59e0b"
    if tags.get("amenity") == "library":
        return "Library", "#10b981"
    return None, None


def _classify_religious(tags: dict):
    if tags.get("amenity") != "place_of_worship":
        return None, None
    religion = tags.get("religion", "other").lower()
    religion_colors = {
        "christian": ("#3b82f6", "Christian"),
        "muslim": ("#22c55e", "Muslim"),
        "jewish": ("#f59e0b", "Jewish"),
        "buddhist": ("#f97316", "Buddhist"),
        "hindu": ("#ef4444", "Hindu"),
        "shinto": ("#ec4899", "Shinto"),
        "sikh": ("#8b5cf6", "Sikh"),
        "taoist": ("#06b6d4", "Taoist"),
    }
    if religion in religion_colors:
        color, label = religion_colors[religion]
        return label, color
    return "Other", "#64748b"


def _classify_sports(tags: dict):
    l = tags.get("leisure", "")
    if l == "stadium":
        return "Stadium", "#ef4444"
    if l == "sports_centre":
        return "Sports Centre", "#3b82f6"
    if l == "swimming_pool":
        return "Swimming Pool", "#06b6d4"
    if l == "pitch":
        sport = tags.get("sport", "unknown")
        return f"Pitch ({sport})", "#22c55e"
    if l == "fitness_centre":
        return "Gym/Fitness", "#f59e0b"
    if l == "track":
        return "Track", "#8b5cf6"
    if l == "golf_course":
        return "Golf Course", "#10b981"
    return None, None


def _classify_shopping(tags: dict):
    shop = tags.get("shop", "")
    amenity = tags.get("amenity", "")
    if shop == "supermarket":
        return "Supermarket", "#22c55e"
    if shop == "mall":
        return "Shopping Mall", "#ec4899"
    if shop == "department_store":
        return "Department Store", "#8b5cf6"
    if amenity == "marketplace":
        return "Marketplace", "#f59e0b"
    if shop == "convenience":
        return "Convenience Store", "#06b6d4"
    if shop == "wholesale":
        return "Wholesale", "#64748b"
    return None, None


def _classify_tourist(tags: dict):
    tourism = tags.get("tourism", "")
    historic = tags.get("historic", "")
    if tourism == "museum":
        return "Museum", "#a855f7"
    if tourism == "attraction":
        return "Attraction", "#ec4899"
    if tourism == "viewpoint":
        return "Viewpoint", "#06b6d4"
    if tourism == "artwork":
        return "Artwork", "#f59e0b"
    if historic == "monument":
        return "Monument", "#ef4444"
    if historic == "memorial":
        return "Memorial", "#64748b"
    if tourism == "gallery":
        return "Gallery", "#8b5cf6"
    if tourism == "information":
        return "Info/Guidepost", "#10b981"
    return None, None


def _classify_emergency(tags: dict):
    amenity = tags.get("amenity", "")
    emergency = tags.get("emergency", "")
    if amenity == "fire_station":
        return "Fire Station", "#ef4444"
    if amenity == "police":
        return "Police Station", "#3b82f6"
    if emergency == "ambulance_station":
        return "Ambulance Station", "#f59e0b"
    if amenity == "hospital" and tags.get("emergency") == "yes":
        return "Emergency Hospital", "#dc2626"
    if emergency == "defibrillator":
        return "Defibrillator (AED)", "#22c55e"
    if emergency == "fire_hydrant":
        return "Fire Hydrant", "#f97316"
    return None, None


def _classify_waste(tags: dict):
    amenity = tags.get("amenity", "")
    landuse = tags.get("landuse", "")
    if amenity == "recycling":
        rtype = tags.get("recycling_type", "")
        if rtype == "centre":
            return "Recycling Centre", "#22c55e"
        return "Recycling Point", "#84cc16"
    if amenity == "waste_disposal":
        return "Waste Disposal", "#f59e0b"
    if amenity == "waste_basket":
        return "Waste Basket", "#64748b"
    if amenity == "waste_transfer_station":
        return "Transfer Station", "#f97316"
    if landuse == "landfill":
        return "Landfill", "#ef4444"
    return None, None


def _classify_parking(tags: dict):
    amenity = tags.get("amenity", "")
    if amenity == "parking":
        ptype = tags.get("parking", "surface")
        ptype_map = {
            "surface": ("Surface Parking", "#64748b"),
            "multi-storey": ("Multi-Storey", "#3b82f6"),
            "underground": ("Underground", "#8b5cf6"),
            "rooftop": ("Rooftop Parking", "#06b6d4"),
            "lane": ("On-Street", "#f59e0b"),
            "street_side": ("Street-Side", "#f97316"),
        }
        return ptype_map.get(ptype, ("Parking (other)", "#94a3b8"))
    if amenity == "bicycle_parking":
        return "Bicycle Parking", "#22c55e"
    if amenity == "parking_entrance":
        return "Parking Entrance", "#ec4899"
    return None, None


def _classify_lighting(tags: dict):
    highway = tags.get("highway", "")
    lit = tags.get("lit", "")
    if highway == "street_lamp":
        return "Street Lamp", "#fbbf24"
    if lit == "yes" and highway:
        return "Lit Street", "#22c55e"
    if lit == "no" and highway:
        return "Unlit Street", "#ef4444"
    return None, None


def _classify_building_height(tags: dict):
    if "building" not in tags:
        return None, None
    height_str = tags.get("height", "")
    levels_str = tags.get("building:levels", "")
    height_m = 0.0
    if height_str:
        try:
            height_m = float(height_str.replace("m", "").replace(" ", "").strip())
        except (ValueError, TypeError):
            height_m = 0.0
    if height_m == 0.0 and levels_str:
        try:
            height_m = float(levels_str) * 3.2
        except (ValueError, TypeError):
            height_m = 0.0
    if height_m <= 0:
        return None, None
    # Color by height bracket
    if height_m < 10:
        return f"Low ({height_m:.0f}m)", "#22c55e"
    elif height_m < 25:
        return f"Medium ({height_m:.0f}m)", "#f59e0b"
    elif height_m < 50:
        return f"Tall ({height_m:.0f}m)", "#f97316"
    elif height_m < 100:
        return f"High-rise ({height_m:.0f}m)", "#ef4444"
    else:
        return f"Skyscraper ({height_m:.0f}m)", "#dc2626"


# Map type -> (fetch_fn, classify_fn)
_DISPATCH = {
    "City Green Spaces":      (fetch_green_spaces,    _classify_green),
    "Hospital & Healthcare":  (fetch_healthcare,       _classify_healthcare),
    "Schools & Universities": (fetch_schools,          _classify_schools),
    "Religious Buildings":    (fetch_religious,         _classify_religious),
    "Sports Facilities":      (fetch_sports,           _classify_sports),
    "Shopping & Markets":     (fetch_shopping,          _classify_shopping),
    "Tourist Attractions":    (fetch_tourist,           _classify_tourist),
    "Emergency Services":     (fetch_emergency,         _classify_emergency),
    "Waste & Recycling":      (fetch_waste,            _classify_waste),
    "Parking Analysis":       (fetch_parking,           _classify_parking),
    "Street Lighting":        (fetch_street_lighting,   _classify_lighting),
    "Building Heights":       (fetch_building_heights,  _classify_building_height),
}


# ═══════════════════════════════════════════════════════════════════════
# FOLIUM MAP BUILDER
# ═══════════════════════════════════════════════════════════════════════

def _build_folium_map(features: list, center_lat: float, center_lon: float,
                      radius_km: float, map_type: str) -> folium.Map:
    """Build a folium map with markers for the given features."""
    m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles=None)

    # CartoDB dark_matter base
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False,
    ).add_to(m)

    # Search radius
    folium.Circle(
        location=[center_lat, center_lon],
        radius=radius_km * 1000,
        color="#06b6d4",
        fill=True,
        fill_opacity=0.03,
        weight=1,
        dash_array="5",
    ).add_to(m)

    # Special rendering for Street Lighting (polylines) and Building Heights (polygons)
    if map_type == "Street Lighting":
        _add_lighting_layers(m, features)
    elif map_type == "Building Heights":
        _add_building_layers(m, features)
    else:
        _add_marker_layers(m, features)

    folium.LayerControl().add_to(m)
    return m


def _add_marker_layers(m: folium.Map, features: list):
    """Standard circle markers for point features."""
    for f in features:
        safe_name = html.escape(f["name"][:80])
        safe_cat = html.escape(f["category"])
        extra_info = ""
        tags = f.get("tags", {})
        if tags.get("phone"):
            extra_info += f"<br/>Phone: {html.escape(tags['phone'])}"
        if tags.get("website"):
            safe_url = html.escape(tags["website"][:120])
            extra_info += f'<br/><a href="{safe_url}" target="_blank" style="font-size:0.7rem;">Website</a>'
        if tags.get("opening_hours"):
            extra_info += f"<br/>Hours: {html.escape(tags['opening_hours'][:60])}"

        popup_html = f"""
        <div style="max-width:220px; font-family:sans-serif;">
            <strong style="font-size:0.85rem;">{safe_name}</strong><br/>
            <span style="font-size:0.75rem; color:#888;">{safe_cat}</span>
            {extra_info}
            <br/><span style="font-size:0.65rem; color:#666;">{f['lat']:.5f}, {f['lon']:.5f}</span>
        </div>
        """

        # For way features with coords, draw polygon outline
        if f.get("coords") and len(f["coords"]) > 2:
            folium.Polygon(
                locations=f["coords"],
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=0.15,
                weight=1,
                popup=folium.Popup(popup_html, max_width=250),
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[f["lat"], f["lon"]],
                radius=6,
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=0.7,
                weight=2,
                popup=folium.Popup(popup_html, max_width=250),
            ).add_to(m)


def _add_lighting_layers(m: folium.Map, features: list):
    """Polylines for lit/unlit streets, markers for lamps."""
    for f in features:
        safe_name = html.escape(f["name"][:80])
        safe_cat = html.escape(f["category"])
        popup_html = f"""
        <div style="max-width:200px; font-family:sans-serif;">
            <strong>{safe_name}</strong><br/>
            <span style="font-size:0.75rem; color:#888;">{safe_cat}</span>
        </div>
        """
        if f.get("coords") and len(f["coords"]) >= 2:
            folium.PolyLine(
                locations=f["coords"],
                color=f["color"],
                weight=3 if f["category"] != "Unlit Street" else 2,
                opacity=0.8 if f["category"] == "Lit Street" else 0.5,
                dash_array="4" if f["category"] == "Unlit Street" else None,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[f["lat"], f["lon"]],
                radius=3,
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=0.9,
                weight=1,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)


def _add_building_layers(m: folium.Map, features: list):
    """Colored polygons for buildings by height."""
    for f in features:
        safe_name = html.escape(f["name"][:80])
        safe_cat = html.escape(f["category"])
        tags = f.get("tags", {})
        height_str = tags.get("height", "")
        levels_str = tags.get("building:levels", "")
        extra = ""
        if height_str:
            extra += f"<br/>Height: {html.escape(str(height_str))}"
        if levels_str:
            extra += f"<br/>Levels: {html.escape(str(levels_str))}"
        btype = tags.get("building", "")
        if btype and btype != "yes":
            extra += f"<br/>Type: {html.escape(btype)}"

        popup_html = f"""
        <div style="max-width:220px; font-family:sans-serif;">
            <strong>{safe_name}</strong><br/>
            <span style="font-size:0.75rem; color:#888;">{safe_cat}</span>
            {extra}
        </div>
        """

        # Compute opacity from height for 3D-style effect
        height_m = 0.0
        if height_str:
            try:
                height_m = float(height_str.replace("m", "").replace(" ", "").strip())
            except (ValueError, TypeError):
                pass
        if height_m == 0.0 and levels_str:
            try:
                height_m = float(levels_str) * 3.2
            except (ValueError, TypeError):
                pass
        opacity = min(0.15 + (height_m / 200.0) * 0.55, 0.7)

        if f.get("coords") and len(f["coords"]) > 2:
            folium.Polygon(
                locations=f["coords"],
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=opacity,
                weight=1,
                popup=folium.Popup(popup_html, max_width=250),
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[f["lat"], f["lon"]],
                radius=max(4, min(12, height_m / 10)),
                color=f["color"],
                fill=True,
                fill_color=f["color"],
                fill_opacity=opacity,
                weight=2,
                popup=folium.Popup(popup_html, max_width=250),
            ).add_to(m)


# ═══════════════════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _render_category_chart(cat_counts: dict, title: str = "Category Breakdown"):
    """Horizontal bar chart of category counts, dark themed."""
    if not cat_counts:
        return
    fig, ax = plt.subplots(figsize=(6, max(3, len(cat_counts) * 0.45)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    cats = list(cat_counts.keys())
    counts = list(cat_counts.values())
    # Use unique colors per bar
    palette = ["#06b6d4", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6",
               "#ec4899", "#3b82f6", "#f97316", "#14b8a6", "#a855f7",
               "#dc2626", "#84cc16", "#64748b", "#fbbf24"]
    colors = [palette[i % len(palette)] for i in range(len(cats))]

    bars = ax.barh(range(len(cats)), counts, color=colors, alpha=0.85, edgecolor="#2a3550")
    ax.set_yticks(range(len(cats)))
    ax.set_yticklabels([c[:30] for c in cats], color="#8b97b0", fontsize=9)
    ax.set_xlabel("Count", color="#8b97b0", fontsize=10)
    ax.tick_params(axis="x", colors="#8b97b0", labelsize=9)
    ax.grid(True, axis="x", color="#2a3550", linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.invert_yaxis()

    # Value labels on bars
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.02, bar.get_y() + bar.get_height() / 2,
                str(count), va="center", color="#e8ecf4", fontsize=8)

    ax.set_title(title, color="#e8ecf4", fontsize=11, fontweight="bold", pad=10)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_density_heatmap(features: list, center_lat: float, center_lon: float,
                            radius_km: float, map_type: str):
    """Render a density scatter plot of feature locations."""
    if len(features) < 5:
        return
    fig, ax = plt.subplots(figsize=(6, 5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    lats = [f["lat"] for f in features]
    lons = [f["lon"] for f in features]

    primary_color = MAP_COLORS.get(map_type, {}).get("primary", "#06b6d4")

    ax.scatter(lons, lats, c=primary_color, alpha=0.5, s=12, edgecolors="none")
    ax.scatter([center_lon], [center_lat], c="#ef4444", s=60, marker="x", linewidths=2, zorder=10)

    ax.set_xlabel("Longitude", color="#8b97b0", fontsize=9)
    ax.set_ylabel("Latitude", color="#8b97b0", fontsize=9)
    ax.tick_params(colors="#5a6580", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.set_title(f"{map_type} Density", color="#e8ecf4", fontsize=11, fontweight="bold", pad=10)
    ax.grid(True, color="#2a3550", linewidth=0.4, alpha=0.5)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_pie_chart(cat_counts: dict, title: str = "Distribution"):
    """Pie chart for category distribution."""
    if not cat_counts or len(cat_counts) < 2:
        return
    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")

    labels = list(cat_counts.keys())
    sizes = list(cat_counts.values())
    palette = ["#06b6d4", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6",
               "#ec4899", "#3b82f6", "#f97316", "#14b8a6", "#a855f7",
               "#dc2626", "#84cc16", "#64748b", "#fbbf24"]
    colors = [palette[i % len(palette)] for i in range(len(labels))]

    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, autopct="%1.0f%%", startangle=90,
        colors=colors, pctdistance=0.8,
        wedgeprops={"edgecolor": "#1a2235", "linewidth": 1.5},
    )
    for t in autotexts:
        t.set_color("#e8ecf4")
        t.set_fontsize(8)
    ax.legend(
        [f"{l} ({s})" for l, s in zip(labels, sizes)],
        loc="center left", bbox_to_anchor=(1.0, 0.5),
        fontsize=7, frameon=False, labelcolor="#8b97b0",
    )
    ax.set_title(title, color="#e8ecf4", fontsize=11, fontweight="bold", pad=10)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════
# EXTRA ANALYSIS HELPERS PER MAP TYPE
# ═══════════════════════════════════════════════════════════════════════

def _compute_area_km2(radius_km: float) -> float:
    """Approximate search area in km2."""
    return math.pi * radius_km ** 2


def _healthcare_analysis(features: list, radius_km: float):
    """Extra stats for healthcare."""
    area = _compute_area_km2(radius_km)
    hospitals = sum(1 for f in features if f["category"] == "Hospital")
    pharmacies = sum(1 for f in features if f["category"] == "Pharmacy")
    c1, c2, c3 = st.columns(3)
    c1.metric("Hospitals", hospitals)
    c2.metric("Pharmacies", pharmacies)
    density = len(features) / area if area > 0 else 0
    c3.metric("Facilities/km\u00b2", f"{density:.1f}")


def _education_analysis(features: list, radius_km: float):
    """Extra stats for education."""
    area = _compute_area_km2(radius_km)
    unis = sum(1 for f in features if f["category"] == "University")
    schools = sum(1 for f in features if f["category"] == "School")
    libs = sum(1 for f in features if f["category"] == "Library")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Universities", unis)
    c2.metric("Schools", schools)
    c3.metric("Libraries", libs)
    density = len(features) / area if area > 0 else 0
    c4.metric("Density/km\u00b2", f"{density:.1f}")


def _parking_analysis(features: list, radius_km: float):
    """Extra stats for parking: surface vs structured."""
    surface = sum(1 for f in features if "Surface" in f["category"])
    structured = sum(1 for f in features if any(kw in f["category"]
                     for kw in ["Multi-Storey", "Underground", "Rooftop"]))
    bicycle = sum(1 for f in features if "Bicycle" in f["category"])
    other = len(features) - surface - structured - bicycle
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Surface Lots", surface)
    c2.metric("Structured", structured)
    c3.metric("Bicycle", bicycle)
    c4.metric("Other/On-Street", other)


def _lighting_analysis(features: list, radius_km: float):
    """Extra stats for street lighting coverage."""
    lit = sum(1 for f in features if f["category"] == "Lit Street")
    unlit = sum(1 for f in features if f["category"] == "Unlit Street")
    lamps = sum(1 for f in features if f["category"] == "Street Lamp")
    total_streets = lit + unlit
    coverage = (lit / total_streets * 100) if total_streets > 0 else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lit Streets", lit)
    c2.metric("Unlit Streets", unlit)
    c3.metric("Street Lamps", lamps)
    c4.metric("Coverage", f"{coverage:.0f}%")


def _building_height_analysis(features: list, radius_km: float):
    """Extra stats for building heights."""
    heights = []
    for f in features:
        tags = f.get("tags", {})
        h = 0.0
        h_str = tags.get("height", "")
        l_str = tags.get("building:levels", "")
        if h_str:
            try:
                h = float(h_str.replace("m", "").replace(" ", "").strip())
            except (ValueError, TypeError):
                h = 0.0
        if h == 0.0 and l_str:
            try:
                h = float(l_str) * 3.2
            except (ValueError, TypeError):
                h = 0.0
        if h > 0:
            heights.append(h)

    if not heights:
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Buildings", len(heights))
    c2.metric("Max Height", f"{max(heights):.0f}m")
    c3.metric("Avg Height", f"{sum(heights)/len(heights):.1f}m")
    c4.metric("Median", f"{sorted(heights)[len(heights)//2]:.0f}m")

    # Height distribution histogram
    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.hist(heights, bins=min(30, max(5, len(heights) // 3)),
            color="#06b6d4", alpha=0.8, edgecolor="#1a2235")
    ax.set_xlabel("Height (m)", color="#8b97b0", fontsize=9)
    ax.set_ylabel("Count", color="#8b97b0", fontsize=9)
    ax.set_title("Building Height Distribution", color="#e8ecf4", fontsize=10, fontweight="bold")
    ax.tick_params(colors="#5a6580", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(True, axis="y", color="#2a3550", linewidth=0.4, alpha=0.5)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _emergency_coverage_analysis(features: list, center_lat: float, center_lon: float,
                                 radius_km: float):
    """Extra analysis: distance-based coverage rings for emergency services."""
    fire = sum(1 for f in features if "Fire" in f["category"] and "Hydrant" not in f["category"])
    police = sum(1 for f in features if "Police" in f["category"])
    ambulance = sum(1 for f in features if "Ambulance" in f["category"])
    aed = sum(1 for f in features if "Defibrillator" in f["category"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Fire Stations", fire)
    c2.metric("Police Stations", police)
    c3.metric("Ambulance Stations", ambulance)
    c4.metric("AEDs", aed)


def _green_space_analysis(features: list, radius_km: float):
    """Extra analysis for green spaces: area coverage estimate."""
    area = _compute_area_km2(radius_km)
    parks = sum(1 for f in features if f["category"] == "Park")
    forests = sum(1 for f in features if f["category"] == "Forest")
    gardens = sum(1 for f in features if f["category"] == "Garden")
    density = len(features) / area if area > 0 else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Parks", parks)
    c2.metric("Forests", forests)
    c3.metric("Gardens", gardens)
    c4.metric("Green/km\u00b2", f"{density:.1f}")


# ═══════════════════════════════════════════════════════════════════════
# GEOJSON EXPORT
# ═══════════════════════════════════════════════════════════════════════

def _features_to_geojson(features: list) -> str:
    """Convert feature list to GeoJSON FeatureCollection string."""
    geojson_features = []
    for f in features:
        props = {
            "name": f["name"],
            "category": f["category"],
            "osm_id": f.get("osm_id"),
        }
        # Add select tags
        for key in ("phone", "website", "opening_hours", "religion",
                    "sport", "height", "building:levels", "parking",
                    "lit", "recycling_type", "emergency"):
            val = f.get("tags", {}).get(key)
            if val:
                props[key] = val

        geojson_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [f["lon"], f["lat"]],
            },
            "properties": props,
        })
    return json.dumps({
        "type": "FeatureCollection",
        "features": geojson_features,
    }, indent=2)


# ═══════════════════════════════════════════════════════════════════════
# DATA TABLE BUILDER
# ═══════════════════════════════════════════════════════════════════════

def _build_dataframe(features: list, map_type: str) -> pd.DataFrame:
    """Build a DataFrame from features with columns relevant to the map type."""
    rows = []
    for f in features:
        tags = f.get("tags", {})
        row = {
            "name": f["name"],
            "category": f["category"],
            "latitude": round(f["lat"], 6),
            "longitude": round(f["lon"], 6),
        }
        # Type-specific columns
        if map_type == "Hospital & Healthcare":
            row["phone"] = tags.get("phone", "")
            row["website"] = tags.get("website", "")
            row["opening_hours"] = tags.get("opening_hours", "")
            row["emergency"] = tags.get("emergency", "")
        elif map_type == "Schools & Universities":
            row["operator"] = tags.get("operator", "")
            row["website"] = tags.get("website", "")
            row["isced_level"] = tags.get("isced:level", "")
        elif map_type == "Religious Buildings":
            row["religion"] = tags.get("religion", "")
            row["denomination"] = tags.get("denomination", "")
        elif map_type == "Sports Facilities":
            row["sport"] = tags.get("sport", "")
            row["surface"] = tags.get("surface", "")
        elif map_type == "Shopping & Markets":
            row["shop"] = tags.get("shop", "")
            row["opening_hours"] = tags.get("opening_hours", "")
            row["brand"] = tags.get("brand", "")
        elif map_type == "Tourist Attractions":
            row["wikipedia"] = tags.get("wikipedia", "")
            row["wikidata"] = tags.get("wikidata", "")
            row["tourism"] = tags.get("tourism", "")
        elif map_type == "Emergency Services":
            row["phone"] = tags.get("phone", "")
            row["emergency"] = tags.get("emergency", "")
            row["operator"] = tags.get("operator", "")
        elif map_type == "Waste & Recycling":
            row["recycling_type"] = tags.get("recycling_type", "")
            row["operator"] = tags.get("operator", "")
        elif map_type == "Parking Analysis":
            row["parking"] = tags.get("parking", "")
            row["capacity"] = tags.get("capacity", "")
            row["fee"] = tags.get("fee", "")
            row["access"] = tags.get("access", "")
        elif map_type == "Street Lighting":
            row["highway"] = tags.get("highway", "")
            row["lit"] = tags.get("lit", "")
            row["surface"] = tags.get("surface", "")
        elif map_type == "Building Heights":
            row["height"] = tags.get("height", "")
            row["building_levels"] = tags.get("building:levels", "")
            row["building_type"] = tags.get("building", "")
            row["roof_shape"] = tags.get("roof:shape", "")
        else:
            row["website"] = tags.get("website", "")

        row["osm_id"] = f.get("osm_id", "")
        rows.append(row)

    return pd.DataFrame(rows)


# ═══════════════════════════════════════════════════════════════════════
# MAP TYPE DESCRIPTIONS (for the info box)
# ═══════════════════════════════════════════════════════════════════════

_MAP_DESCRIPTIONS = {
    "City Green Spaces":
        "Explore parks, gardens, forests, and nature reserves within urban areas. "
        "Green spaces are essential for urban well-being, air quality, and biodiversity.",
    "Hospital & Healthcare":
        "Map hospitals, clinics, pharmacies, doctors, dentists, and health centres. "
        "Analyze healthcare facility density and distribution across the city.",
    "Schools & Universities":
        "Find schools, universities, colleges, kindergartens, and libraries. "
        "Understand the educational infrastructure landscape of any city.",
    "Religious Buildings":
        "Discover places of worship categorized by religion: Christian, Muslim, "
        "Jewish, Buddhist, Hindu, Shinto, Sikh, and more.",
    "Sports Facilities":
        "Locate stadiums, sports centres, swimming pools, pitches, gyms, tracks, "
        "and golf courses. Analyze sports infrastructure by type.",
    "Shopping & Markets":
        "Map supermarkets, shopping malls, department stores, marketplaces, "
        "convenience stores, and wholesale outlets.",
    "Tourist Attractions":
        "Find museums, attractions, viewpoints, monuments, memorials, galleries, "
        "and artwork installations for tourism analysis.",
    "Emergency Services":
        "Map fire stations, police stations, ambulance stations, emergency hospitals, "
        "AEDs, and fire hydrants for safety coverage analysis.",
    "Waste & Recycling":
        "Locate recycling points, recycling centres, waste disposal facilities, "
        "waste baskets, transfer stations, and landfills.",
    "Parking Analysis":
        "Analyze parking infrastructure: surface lots vs multi-storey garages vs "
        "underground parking. Includes bicycle parking and capacity data.",
    "Street Lighting":
        "Visualize streets tagged with lighting information. Compare lit vs unlit "
        "streets and individual street lamp locations for safety analysis.",
    "Building Heights":
        "3D-style visualization of buildings with height or floor-level data. "
        "Color-coded from low-rise to skyscrapers for urban density analysis.",
}


# ═══════════════════════════════════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════════════════════════════════

def render_urban_analytics_tab():
    """Main render function for the Urban Analytics tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header pink">
        <h4>Urban Analytics</h4>
        <p>12 specialized city analysis maps powered by OpenStreetMap. Explore green spaces,
        healthcare, education, religion, sports, shopping, tourism, emergency services,
        waste management, parking, street lighting, and building heights.</p>
    </div>
    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════
    # SECTION 1: Map Type Selection
    # ══════════════════════════════════════════
    st.markdown("#### Select Analysis Type")

    selected_map = st.radio(
        "Choose an urban analysis map",
        MAP_TYPES,
        index=0,
        key="urban_map_type",
        horizontal=True,
    )

    # Description
    desc = _MAP_DESCRIPTIONS.get(selected_map, "")
    if desc:
        st.info(desc)

    # ══════════════════════════════════════════
    # SECTION 2: Location Controls
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Location & Search")

    col_preset, col_radius = st.columns([2, 1])
    with col_preset:
        preset = st.selectbox(
            "City Preset",
            list(CITY_PRESETS.keys()),
            key="urban_preset",
        )
    with col_radius:
        radius_km = st.slider("Radius (km)", 1, 30, 3, key="urban_radius",
                               help="Search radius around the center point")

    if preset != "Custom" and CITY_PRESETS.get(preset):
        p = CITY_PRESETS[preset]
        default_lat = p["lat"]
        default_lon = p["lon"]
    else:
        default_lat = 41.8967
        default_lon = 12.4822

    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.4f",
            min_value=-90.0, max_value=90.0, key="urban_lat",
        )
    with col_lon:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.4f",
            min_value=-180.0, max_value=180.0, key="urban_lon",
        )

    # Override with preset values if a preset is chosen
    if preset != "Custom" and CITY_PRESETS.get(preset):
        lat = CITY_PRESETS[preset]["lat"]
        lon = CITY_PRESETS[preset]["lon"]

    # Search button
    if st.button(
        f"Analyze {selected_map}",
        key="urban_search_btn",
        type="primary",
        width="stretch",
    ):
        st.session_state.urban_params = {
            "lat": lat,
            "lon": lon,
            "radius_km": radius_km,
            "map_type": selected_map,
        }

    if "urban_params" not in st.session_state:
        st.info("Select a city and analysis type, then click the Analyze button to begin.")
        return

    params = st.session_state.urban_params

    # ══════════════════════════════════════════
    # SECTION 3: Data Fetching & Processing
    # ══════════════════════════════════════════
    fetch_fn, classify_fn = _DISPATCH.get(params["map_type"], (None, None))
    if fetch_fn is None:
        st.error(f"Unknown map type: {params['map_type']}")
        return

    with st.spinner(f"Fetching {params['map_type']} data from OpenStreetMap..."):
        raw_data = fetch_fn(params["lat"], params["lon"], params["radius_km"])

    if "_error" in raw_data:
        st.error(f"Overpass API error: {raw_data['_error']}. Try a smaller radius or retry later.")
        return

    features = _extract_generic(raw_data, classify_fn)

    if not features:
        st.warning(f"No {params['map_type']} features found in this area. "
                   "Try a larger radius or a different city.")
        return

    # ══════════════════════════════════════════
    # SECTION 4: Statistics Overview
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown(f"#### {params['map_type']} \u2014 Results")

    # Category counts
    cat_counts = {}
    for f in features:
        cat = f["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Primary metrics row
    area_km2 = _compute_area_km2(params["radius_km"])
    n_cats = len(cat_counts)
    density = len(features) / area_km2 if area_km2 > 0 else 0

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Total Features", f"{len(features):,}")
    mc2.metric("Categories", n_cats)
    mc3.metric("Search Area", f"{area_km2:.1f} km\u00b2")
    mc4.metric("Density/km\u00b2", f"{density:.1f}")

    # Type-specific extra analysis
    mt = params["map_type"]
    if mt == "City Green Spaces":
        _green_space_analysis(features, params["radius_km"])
    elif mt == "Hospital & Healthcare":
        _healthcare_analysis(features, params["radius_km"])
    elif mt == "Schools & Universities":
        _education_analysis(features, params["radius_km"])
    elif mt == "Parking Analysis":
        _parking_analysis(features, params["radius_km"])
    elif mt == "Street Lighting":
        _lighting_analysis(features, params["radius_km"])
    elif mt == "Building Heights":
        _building_height_analysis(features, params["radius_km"])
    elif mt == "Emergency Services":
        _emergency_coverage_analysis(features, params["lat"], params["lon"],
                                     params["radius_km"])

    # ══════════════════════════════════════════
    # SECTION 5: Folium Map
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Interactive Map")

    # Legend
    unique_cats = {}
    for f in features:
        if f["category"] not in unique_cats:
            unique_cats[f["category"]] = f["color"]

    legend_items = " ".join([
        f'<span style="color:{color}; font-size:0.8rem;">\u25cf {html.escape(cat)}</span>'
        for cat, color in unique_cats.items()
    ])
    st.markdown(
        f'<div style="display:flex; gap:0.75rem; flex-wrap:wrap; margin-bottom:0.5rem;">'
        f'{legend_items}</div>',
        unsafe_allow_html=True,
    )

    fmap = _build_folium_map(
        features, params["lat"], params["lon"],
        params["radius_km"], params["map_type"],
    )
    components.html(fmap._repr_html_(), height=550)

    # ══════════════════════════════════════════
    # SECTION 6: Charts
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Analysis Charts")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        _render_category_chart(cat_counts, f"{params['map_type']} by Category")

    with chart_col2:
        if len(cat_counts) >= 2:
            _render_pie_chart(cat_counts, f"{params['map_type']} Distribution")
        else:
            _render_density_heatmap(features, params["lat"], params["lon"],
                                    params["radius_km"], params["map_type"])

    # Density scatter (always show if enough features)
    if len(features) >= 10:
        _render_density_heatmap(features, params["lat"], params["lon"],
                                params["radius_km"], params["map_type"])

    # ══════════════════════════════════════════
    # SECTION 7: Notable Features List
    # ══════════════════════════════════════════
    st.markdown("---")
    st.markdown("#### Notable Features")

    # Show top named features sorted by tag richness
    named = [f for f in features if f["name"] != f["category"]]
    sorted_features = sorted(named, key=lambda x: len(x.get("tags", {})), reverse=True)

    display_count = min(25, len(sorted_features))
    if display_count > 0:
        for f in sorted_features[:display_count]:
            safe_name = html.escape(f["name"][:60])
            safe_cat = html.escape(f["category"])
            extra_badges = ""
            tags = f.get("tags", {})
            if tags.get("wikipedia"):
                extra_badges += ' <span style="color:#3b82f6; font-size:0.65rem;">WIKI</span>'
            if tags.get("website"):
                extra_badges += ' <span style="color:#06b6d4; font-size:0.65rem;">WEB</span>'
            if tags.get("phone"):
                extra_badges += ' <span style="color:#22c55e; font-size:0.65rem;">TEL</span>'

            st.markdown(f"""
            <div style="display:flex; align-items:center; margin-bottom:0.4rem;
                        padding:0.4rem 0.6rem; background:rgba(26,34,53,0.5);
                        border-radius:6px; border-left:3px solid {f['color']};">
                <div>
                    <div style="color:#e8ecf4; font-weight:600; font-size:0.82rem;">
                        {safe_name}{extra_badges}
                    </div>
                    <div style="color:#8b97b0; font-size:0.72rem;">{safe_cat}</div>
                    <div style="color:#5a6580; font-size:0.65rem;">
                        {f['lat']:.5f}, {f['lon']:.5f}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No named features to display. All features are visible on the map above.")

    # ══════════════════════════════════════════
    # SECTION 8: Data Table
    # ══════════════════════════════════════════
    st.markdown("---")
    df = _build_dataframe(features, params["map_type"])

    with st.expander(f"Full Data Table ({len(df):,} features)", expanded=False):
        st.dataframe(df, width="stretch", hide_index=True)

    # ══════════════════════════════════════════
    # SECTION 9: Downloads
    # ══════════════════════════════════════════
    st.markdown("#### Download Data")

    dl_col1, dl_col2 = st.columns(2)

    with dl_col1:
        csv_buf = io.StringIO()
        df.to_csv(csv_buf, index=False)
        safe_filename = params["map_type"].lower().replace(" ", "_").replace("&", "and")
        st.download_button(
            f"Download CSV ({len(df):,} rows)",
            data=csv_buf.getvalue(),
            file_name=f"urban_{safe_filename}.csv",
            mime="text/csv",
            key="urban_dl_csv",
        )

    with dl_col2:
        geojson_str = _features_to_geojson(features)
        st.download_button(
            f"Download GeoJSON ({len(features):,} features)",
            data=geojson_str,
            file_name=f"urban_{safe_filename}.geojson",
            mime="application/geo+json",
            key="urban_dl_geojson",
        )

    # ══════════════════════════════════════════
    # SECTION 10: Methodology Note
    # ══════════════════════════════════════════
    with st.expander("Methodology & Data Sources"):
        st.markdown(f"""
        **Data Source:** [OpenStreetMap](https://www.openstreetmap.org) via the
        [Overpass API](https://overpass-api.de/).

        **Analysis Type:** {html.escape(params['map_type'])}

        **Search Parameters:**
        - Center: {params['lat']:.4f}, {params['lon']:.4f}
        - Radius: {params['radius_km']} km
        - Search area: {area_km2:.1f} km\u00b2

        **Notes:**
        - Data completeness depends on OSM contributor activity in the area.
        - Some features may lack names or detailed tags.
        - Building height data is only available where contributors have tagged it.
        - Street lighting data coverage varies significantly by city.
        - Results are cached for 1 hour to reduce API load.
        """)
