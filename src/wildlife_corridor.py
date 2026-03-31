# -*- coding: utf-8 -*-
"""
Wildlife Corridor AI module for TerraScout AI.
Habitat connectivity assessment using multi-source free geospatial data.
Analyzes 6 dimensions of corridor viability: habitat patches, barrier analysis,
water connectivity, species richness, terrain passability, and corridor integrity.

Data sources (all free, no API key required):
  - Overpass API (forests, water, parks, reserves, fences, roads)
  - iNaturalist (biodiversity / species)
  - GBIF (species occurrences)
  - Open Topo Data (terrain / elevation for movement analysis)
"""

import html as html_module
import logging
import math

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_species_breakdown,
    fetch_protected_areas,
)
from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# ==============================================================================
# CONSTANTS
# ==============================================================================

OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

DIMENSION_META = {
    "habitat_patches": {
        "name": "Habitat Patches",
        "color": "#10b981",
        "icon": "\U0001F333",
        "description": "Forest, park and reserve density & connectivity",
    },
    "barrier_analysis": {
        "name": "Barrier Analysis",
        "color": "#ef4444",
        "icon": "\U0001F6A7",
        "description": "Roads, fences and urban areas blocking wildlife movement",
    },
    "water_connectivity": {
        "name": "Water Connectivity",
        "color": "#3b82f6",
        "icon": "\U0001F30A",
        "description": "Rivers and streams as corridors or barriers",
    },
    "species_richness": {
        "name": "Species Richness",
        "color": "#8b5cf6",
        "icon": "\U0001F98B",
        "description": "Biodiversity indicating healthy corridors",
    },
    "terrain_passability": {
        "name": "Terrain Passability",
        "color": "#f59e0b",
        "icon": "\U000026F0\uFE0F",
        "description": "Slope and elevation barriers to movement",
    },
    "corridor_integrity": {
        "name": "Corridor Integrity",
        "color": "#06b6d4",
        "icon": "\U0001F517",
        "description": "Overall connectivity and corridor quality score",
    },
}

KINGDOM_COLORS = {
    "Plantae": "#10b981",
    "Aves": "#06b6d4",
    "Mammalia": "#8b5cf6",
    "Insecta": "#f59e0b",
    "Reptilia": "#ef4444",
    "Amphibia": "#ec4899",
    "Actinopterygii": "#3b82f6",
    "Fungi": "#a855f7",
    "Animalia": "#14b8a6",
    "Chromista": "#84cc16",
    "Other": "#8b97b0",
}

# Barrier weight by OSM highway type (higher = worse for wildlife)
ROAD_BARRIER_WEIGHTS = {
    "motorway": 10.0,
    "trunk": 8.0,
    "primary": 6.0,
    "secondary": 4.5,
    "tertiary": 3.0,
    "residential": 1.5,
    "service": 0.8,
    "track": 0.3,
    "footway": 0.1,
    "cycleway": 0.2,
    "path": 0.1,
}


# ==============================================================================
# DATA-FETCHING FUNCTIONS
# ==============================================================================

@st.cache_data(ttl=1800)
def fetch_corridor_habitat_patches(lat: float, lon: float, radius: int = 5000) -> dict:
    """Fetch forests, parks, nature reserves from Overpass API."""
    query = f"""[out:json][timeout:25];
(
  way["landuse"="forest"](around:{radius},{lat},{lon});
  way["natural"="wood"](around:{radius},{lat},{lon});
  way["leisure"="park"](around:{radius},{lat},{lon});
  way["leisure"="nature_reserve"](around:{radius},{lat},{lon});
  way["boundary"="protected_area"](around:{radius},{lat},{lon});
  relation["landuse"="forest"](around:{radius},{lat},{lon});
  relation["natural"="wood"](around:{radius},{lat},{lon});
  relation["leisure"="nature_reserve"](around:{radius},{lat},{lon});
  relation["boundary"="protected_area"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


@st.cache_data(ttl=1800)
def fetch_corridor_barriers(lat: float, lon: float, radius: int = 5000) -> dict:
    """Fetch roads, fences, railways, and urban landuse that block wildlife."""
    query = f"""[out:json][timeout:25];
(
  way["highway"](around:{radius},{lat},{lon});
  way["barrier"="fence"](around:{radius},{lat},{lon});
  way["barrier"="wall"](around:{radius},{lat},{lon});
  way["railway"](around:{radius},{lat},{lon});
  way["landuse"="industrial"](around:{radius},{lat},{lon});
  way["landuse"="commercial"](around:{radius},{lat},{lon});
  way["landuse"="residential"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


@st.cache_data(ttl=1800)
def fetch_terrain_elevation(lat: float, lon: float,
                            radius_deg: float = 0.04,
                            grid_size: int = 7) -> dict:
    """
    Fetch elevation grid from Open Topo Data for terrain passability analysis.
    Returns dict with elevations list, center_elevation, min/max, slope_estimate.
    """
    try:
        points = []
        half = grid_size // 2
        for i in range(-half, half + 1):
            for j in range(-half, half + 1):
                plat = lat + i * radius_deg / half if half > 0 else lat
                plon = lon + j * radius_deg / half if half > 0 else lon
                points.append(f"{plat:.5f},{plon:.5f}")

        locations_str = "|".join(points[:100])
        resp = requests.get(
            OPEN_TOPO_API,
            params={"locations": locations_str},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])

        elevations = []
        for r in results:
            e = r.get("elevation")
            elevations.append(float(e) if e is not None else 0.0)

        if not elevations:
            return {
                "elevations": [],
                "center_elevation": 0.0,
                "min_elevation": 0.0,
                "max_elevation": 0.0,
                "avg_elevation": 0.0,
                "elevation_range": 0.0,
                "slope_estimate": 0.0,
            }

        center_idx = len(elevations) // 2
        center_elev = elevations[center_idx]
        min_elev = min(elevations)
        max_elev = max(elevations)
        avg_elev = sum(elevations) / len(elevations)
        elev_range = max_elev - min_elev

        # Estimate average slope in degrees from elevation grid
        # Approximate horizontal distance between adjacent grid points
        lat_dist_m = radius_deg * 2 * 111320 / grid_size
        slopes = []
        for i in range(len(elevations) - 1):
            de = abs(elevations[i + 1] - elevations[i])
            if lat_dist_m > 0:
                slope_rad = math.atan2(de, lat_dist_m)
                slopes.append(math.degrees(slope_rad))
        avg_slope = sum(slopes) / len(slopes) if slopes else 0.0

        return {
            "elevations": elevations,
            "center_elevation": center_elev,
            "min_elevation": min_elev,
            "max_elevation": max_elev,
            "avg_elevation": avg_elev,
            "elevation_range": elev_range,
            "slope_estimate": avg_slope,
        }
    except Exception as exc:
        logger.warning("Terrain elevation fetch error: %s", exc)
        return {
            "elevations": [],
            "center_elevation": 0.0,
            "min_elevation": 0.0,
            "max_elevation": 0.0,
            "avg_elevation": 0.0,
            "elevation_range": 0.0,
            "slope_estimate": 0.0,
        }


# ==============================================================================
# SCORING FUNCTIONS
# ==============================================================================

@st.cache_data(ttl=1800)
def score_habitat_patches(lat: float, lon: float) -> dict:
    """
    Dimension 1: Habitat Patches -- density and connectivity of green areas.
    Returns dict with score (0-100), details.
    """
    patches = fetch_corridor_habitat_patches(lat, lon)
    protected = fetch_protected_areas(lat, lon)

    patch_elements = patches.get("elements", []) if isinstance(patches, dict) else []
    prot_elements = protected.get("elements", []) if isinstance(protected, dict) else []

    forests = [
        e for e in patch_elements
        if (e.get("tags", {}).get("landuse") == "forest"
            or e.get("tags", {}).get("natural") == "wood")
    ]
    parks = [
        e for e in patch_elements
        if e.get("tags", {}).get("leisure") in ("park", "nature_reserve")
    ]
    reserves = [
        e for e in patch_elements
        if e.get("tags", {}).get("boundary") == "protected_area"
    ]
    # Add protected areas from the dedicated fetch
    reserves_extra = [
        e for e in prot_elements
        if (e.get("tags", {}).get("boundary") == "protected_area"
            or e.get("tags", {}).get("leisure") == "nature_reserve")
    ]

    forest_count = len(forests)
    park_count = len(parks)
    reserve_count = len(reserves) + len(reserves_extra)
    total_patches = forest_count + park_count + reserve_count

    # Score: more patches = better connectivity, with diminishing returns
    density_score = min(100.0, (forest_count / 15.0) * 40.0
                        + (park_count / 8.0) * 25.0
                        + (reserve_count / 3.0) * 35.0)

    # Connectivity bonus: if we have all three types close by, corridors are
    # more likely continuous
    type_diversity = sum([
        1 for c in (forest_count, park_count, reserve_count) if c > 0
    ])
    diversity_bonus = type_diversity * 8.0

    score = min(100.0, max(0.0, density_score + diversity_bonus))

    return {
        "score": round(score, 1),
        "forest_count": forest_count,
        "park_count": park_count,
        "reserve_count": reserve_count,
        "total_patches": total_patches,
        "type_diversity": type_diversity,
    }


@st.cache_data(ttl=1800)
def score_barrier_analysis(lat: float, lon: float) -> dict:
    """
    Dimension 2: Barrier Analysis -- roads, fences, urban areas.
    Higher score = FEWER barriers (better for wildlife).
    """
    barriers = fetch_corridor_barriers(lat, lon)
    elements = barriers.get("elements", []) if isinstance(barriers, dict) else []

    road_count = 0
    road_severity = 0.0
    fence_count = 0
    railway_count = 0
    urban_count = 0

    for el in elements:
        tags = el.get("tags", {})
        highway = tags.get("highway", "")
        barrier = tags.get("barrier", "")
        railway = tags.get("railway", "")
        landuse = tags.get("landuse", "")

        if highway:
            road_count += 1
            road_severity += ROAD_BARRIER_WEIGHTS.get(highway, 1.0)
        if barrier in ("fence", "wall"):
            fence_count += 1
        if railway:
            railway_count += 1
        if landuse in ("industrial", "commercial", "residential"):
            urban_count += 1

    # Normalize road severity (0-100 scale, higher = worse)
    road_impact = min(100.0, road_severity / 5.0)
    fence_impact = min(30.0, fence_count * 5.0)
    railway_impact = min(20.0, railway_count * 4.0)
    urban_impact = min(40.0, urban_count * 2.0)

    raw_barrier = road_impact + fence_impact + railway_impact + urban_impact
    # Invert: higher score = fewer barriers = better corridor
    score = max(0.0, min(100.0, 100.0 - raw_barrier * 0.5))

    return {
        "score": round(score, 1),
        "road_count": road_count,
        "road_severity": round(road_severity, 1),
        "fence_count": fence_count,
        "railway_count": railway_count,
        "urban_count": urban_count,
        "barrier_impact": round(raw_barrier, 1),
    }


@st.cache_data(ttl=1800)
def score_water_connectivity(lat: float, lon: float) -> dict:
    """
    Dimension 3: Water Connectivity -- rivers/streams as corridors.
    Water bodies can serve as movement corridors or as barriers depending on type.
    """
    water = fetch_water_features(lat, lon)
    elements = water.get("elements", []) if isinstance(water, dict) else []

    waterways = []
    water_bodies = []
    springs = []
    wells = []

    for el in elements:
        tags = el.get("tags", {})
        waterway = tags.get("waterway", "")
        natural = tags.get("natural", "")
        man_made = tags.get("man_made", "")

        if waterway in ("river", "stream", "canal", "ditch", "drain"):
            waterways.append({"type": waterway, "name": tags.get("name", "")})
        if natural == "water" or waterway in ("riverbank",):
            water_bodies.append({"name": tags.get("name", "")})
        if natural == "spring":
            springs.append(el)
        if man_made == "water_well":
            wells.append(el)

    river_count = sum(1 for w in waterways if w["type"] == "river")
    stream_count = sum(1 for w in waterways if w["type"] == "stream")
    canal_count = sum(1 for w in waterways if w["type"] == "canal")
    water_body_count = len(water_bodies)
    spring_count = len(springs)

    # Streams and rivers are excellent corridors for many species
    corridor_value = (
        river_count * 12.0
        + stream_count * 8.0
        + spring_count * 5.0
        + water_body_count * 4.0
    )
    # Canals can be minor barriers (channelized)
    canal_penalty = canal_count * 2.0

    score = min(100.0, max(0.0, corridor_value - canal_penalty))

    return {
        "score": round(score, 1),
        "river_count": river_count,
        "stream_count": stream_count,
        "canal_count": canal_count,
        "water_body_count": water_body_count,
        "spring_count": spring_count,
        "total_water_features": len(elements),
    }


@st.cache_data(ttl=1800)
def score_species_richness(lat: float, lon: float) -> dict:
    """
    Dimension 4: Species Richness -- biodiversity indicating healthy corridors.
    """
    inat = fetch_biodiversity(lat, lon)
    gbif = fetch_gbif_occurrences(lat, lon)
    breakdown = compute_species_breakdown(inat, gbif)

    inat_total = (breakdown.get("inat_total") or 0)
    gbif_total = (breakdown.get("gbif_total") or 0)
    gbif_unique = (breakdown.get("gbif_unique_species") or 0)
    kingdom_counts = breakdown.get("kingdom_counts") or {}
    top_species = breakdown.get("top_species") or []

    num_kingdoms = len(kingdom_counts)
    total_obs = inat_total + gbif_total

    # Score based on observation density, species diversity, and kingdom spread
    obs_score = min(40.0, total_obs / 10.0)
    unique_score = min(30.0, gbif_unique / 3.0)
    kingdom_score = min(30.0, num_kingdoms * 5.0)

    score = min(100.0, max(0.0, obs_score + unique_score + kingdom_score))

    # Identify key wildlife groups for corridor relevance
    mammal_count = (kingdom_counts.get("Mammalia") or 0)
    bird_count = (kingdom_counts.get("Aves") or 0)
    reptile_count = (kingdom_counts.get("Reptilia") or 0)
    amphibian_count = (kingdom_counts.get("Amphibia") or 0)
    insect_count = (kingdom_counts.get("Insecta") or 0)
    plant_count = (kingdom_counts.get("Plantae") or 0)

    return {
        "score": round(score, 1),
        "inat_total": inat_total,
        "gbif_total": gbif_total,
        "gbif_unique_species": gbif_unique,
        "kingdom_counts": kingdom_counts,
        "top_species": top_species,
        "num_kingdoms": num_kingdoms,
        "mammal_count": mammal_count,
        "bird_count": bird_count,
        "reptile_count": reptile_count,
        "amphibian_count": amphibian_count,
        "insect_count": insect_count,
        "plant_count": plant_count,
    }


@st.cache_data(ttl=1800)
def score_terrain_passability(lat: float, lon: float) -> dict:
    """
    Dimension 5: Terrain Passability -- slope and elevation barriers.
    Flatter terrain with moderate elevation = easier wildlife movement.
    """
    terrain = fetch_terrain_elevation(lat, lon)

    center_elev = terrain.get("center_elevation", 0.0) or 0.0
    elev_range = terrain.get("elevation_range", 0.0) or 0.0
    avg_slope = terrain.get("slope_estimate", 0.0) or 0.0
    min_elev = terrain.get("min_elevation", 0.0) or 0.0
    max_elev = terrain.get("max_elevation", 0.0) or 0.0

    # Slope penalty: steep slopes reduce passability
    if avg_slope <= 5:
        slope_score = 100.0
    elif avg_slope <= 15:
        slope_score = 100.0 - (avg_slope - 5) * 5.0
    elif avg_slope <= 30:
        slope_score = 50.0 - (avg_slope - 15) * 2.5
    else:
        slope_score = max(0.0, 12.5 - (avg_slope - 30) * 0.5)

    # Elevation range penalty: extreme variation blocks movement
    if elev_range <= 50:
        range_score = 100.0
    elif elev_range <= 200:
        range_score = 100.0 - (elev_range - 50) * 0.4
    elif elev_range <= 500:
        range_score = 40.0 - (elev_range - 200) * 0.1
    else:
        range_score = max(0.0, 10.0 - (elev_range - 500) * 0.02)

    # Extreme altitude penalty (above treeline / alpine zone)
    altitude_factor = 1.0
    if center_elev > 3000:
        altitude_factor = max(0.3, 1.0 - (center_elev - 3000) / 3000)
    elif center_elev > 2000:
        altitude_factor = max(0.6, 1.0 - (center_elev - 2000) / 5000)

    score = (slope_score * 0.50 + range_score * 0.50) * altitude_factor
    score = min(100.0, max(0.0, score))

    return {
        "score": round(score, 1),
        "center_elevation": round(center_elev, 1),
        "min_elevation": round(min_elev, 1),
        "max_elevation": round(max_elev, 1),
        "elevation_range": round(elev_range, 1),
        "avg_slope_deg": round(avg_slope, 2),
        "slope_score": round(slope_score, 1),
        "range_score": round(range_score, 1),
    }


@st.cache_data(ttl=1800)
def compute_corridor_integrity(
    habitat_score: float,
    barrier_score: float,
    water_score: float,
    species_score: float,
    terrain_score: float,
) -> dict:
    """
    Dimension 6: Corridor Integrity -- weighted composite of all other dimensions.
    """
    weights = {
        "habitat_patches": 0.25,
        "barrier_analysis": 0.25,
        "water_connectivity": 0.15,
        "species_richness": 0.20,
        "terrain_passability": 0.15,
    }

    weighted = (
        (habitat_score or 0) * weights["habitat_patches"]
        + (barrier_score or 0) * weights["barrier_analysis"]
        + (water_score or 0) * weights["water_connectivity"]
        + (species_score or 0) * weights["species_richness"]
        + (terrain_score or 0) * weights["terrain_passability"]
    )

    # Bonus for balanced scores (no single dimension is catastrophically low)
    dim_scores = [
        (habitat_score or 0),
        (barrier_score or 0),
        (water_score or 0),
        (species_score or 0),
        (terrain_score or 0),
    ]
    min_dim = min(dim_scores) if dim_scores else 0
    balance_bonus = min(10.0, min_dim * 0.15)

    score = min(100.0, max(0.0, weighted + balance_bonus))

    # Generate corridor quality rating
    if score >= 80:
        rating = "Excellent"
        rating_color = "#10b981"
    elif score >= 60:
        rating = "Good"
        rating_color = "#06b6d4"
    elif score >= 40:
        rating = "Moderate"
        rating_color = "#f59e0b"
    elif score >= 20:
        rating = "Poor"
        rating_color = "#ef4444"
    else:
        rating = "Critical"
        rating_color = "#dc2626"

    # Generate recommendations
    recommendations = []
    if (habitat_score or 0) < 40:
        recommendations.append(
            "Increase habitat patch connectivity through reforestation or "
            "establishing stepping-stone habitats between isolated patches."
        )
    if (barrier_score or 0) < 40:
        recommendations.append(
            "Mitigate road and fence barriers with wildlife crossings, "
            "underpasses, or green bridges over major highways."
        )
    if (water_score or 0) < 30:
        recommendations.append(
            "Restore riparian corridors along streams and rivers to "
            "provide water-based movement pathways."
        )
    if (species_score or 0) < 35:
        recommendations.append(
            "Low species richness suggests degraded habitat; consider "
            "invasive species management and native planting programs."
        )
    if (terrain_score or 0) < 35:
        recommendations.append(
            "Steep terrain limits movement; focus corridor planning along "
            "valleys, ridgelines, or contour paths."
        )
    if not recommendations:
        recommendations.append(
            "Corridor conditions are favorable. Maintain current habitat "
            "quality and monitor for emerging threats."
        )

    return {
        "score": round(score, 1),
        "rating": rating,
        "rating_color": rating_color,
        "balance_bonus": round(balance_bonus, 1),
        "weighted_base": round(weighted, 1),
        "recommendations": recommendations,
    }


# ==============================================================================
# MASTER ANALYSIS
# ==============================================================================

@st.cache_data(ttl=1800)
def analyze_wildlife_corridor(lat: float, lon: float) -> dict:
    """Run all 6 corridor dimensions and return full results."""
    d1 = score_habitat_patches(lat, lon)
    d2 = score_barrier_analysis(lat, lon)
    d3 = score_water_connectivity(lat, lon)
    d4 = score_species_richness(lat, lon)
    d5 = score_terrain_passability(lat, lon)
    d6 = compute_corridor_integrity(
        d1["score"], d2["score"], d3["score"],
        d4["score"], d5["score"],
    )

    return {
        "habitat_patches": d1,
        "barrier_analysis": d2,
        "water_connectivity": d3,
        "species_richness": d4,
        "terrain_passability": d5,
        "corridor_integrity": d6,
        "scores": {
            "habitat_patches": d1["score"],
            "barrier_analysis": d2["score"],
            "water_connectivity": d3["score"],
            "species_richness": d4["score"],
            "terrain_passability": d5["score"],
            "corridor_integrity": d6["score"],
        },
    }


# ==============================================================================
# PLOTLY HELPERS
# ==============================================================================

def _dark_layout(fig, height=400, **kwargs):
    """Apply dark theme to a Plotly figure."""
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,26,46,0.6)",
        font=dict(color="#e8ecf4"),
        margin=dict(l=60, r=30, t=30, b=40),
        height=height,
        **kwargs,
    )
    return fig


def _score_color(score: float) -> str:
    """Return a color string based on a 0-100 score."""
    if score >= 70:
        return "#10b981"
    if score >= 40:
        return "#f59e0b"
    return "#ef4444"


# ==============================================================================
# RENDER FUNCTION
# ==============================================================================

def render_wildlife_corridor_tab():
    """Render the Wildlife Corridor AI tab."""

    # -- Header ----------------------------------------------------------------
    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);'
        "border:1px solid #2a3550;border-radius:12px;padding:18px 22px;"
        'margin-bottom:16px;">'
        '<h4 style="color:#10b981;margin:0 0 6px 0;">'
        "\U0001F43E Wildlife Corridor AI</h4>"
        '<p style="color:#8b97b0;margin:0;font-size:13px;">'
        "Assess habitat connectivity across 6 dimensions using Overpass, "
        "iNaturalist, GBIF, and Open Topo Data. Identifies barriers, corridor "
        "quality, and species richness for wildlife movement planning.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # -- Location selector -----------------------------------------------------
    c1, c2, c3 = st.columns([1.2, 1.0, 1.0])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="wcorr_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude",
            value=default_lat,
            format="%.5f",
            min_value=-90.0,
            max_value=90.0,
            key="wcorr_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude",
            value=default_lon,
            format="%.5f",
            min_value=-180.0,
            max_value=180.0,
            key="wcorr_lon",
        )

    run = st.button(
        "\U0001F43E Analyze Wildlife Corridor",
        type="primary",
        key="wcorr_run",
        use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Analyze Wildlife Corridor** to run "
            "the 6-dimension habitat connectivity assessment."
        )
        return

    # -- Run analysis ----------------------------------------------------------
    with st.spinner("Fetching corridor data from Overpass, iNaturalist, GBIF, Open Topo Data..."):
        result = analyze_wildlife_corridor(lat, lon)

    scores = result["scores"]
    d1 = result["habitat_patches"]
    d2 = result["barrier_analysis"]
    d3 = result["water_connectivity"]
    d4 = result["species_richness"]
    d5 = result["terrain_passability"]
    d6 = result["corridor_integrity"]

    st.markdown("---")

    # ==========================================================================
    # CORRIDOR INTEGRITY HEADER
    # ==========================================================================
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);'
        f"border:2px solid {d6['rating_color']};border-radius:14px;"
        f'padding:22px 28px;text-align:center;margin-bottom:18px;">'
        f'<span style="font-size:48px;">\U0001F43E</span><br/>'
        f'<h2 style="color:{d6["rating_color"]};margin:8px 0 4px 0;">'
        f'Corridor Integrity: {d6["rating"]}</h2>'
        f'<span style="color:#e8ecf4;font-size:26px;font-weight:bold;">'
        f'{d6["score"]:.0f}/100</span><br/>'
        f'<span style="color:#8b97b0;font-size:13px;">'
        f"Wildlife corridor assessment for {lat:.4f}, {lon:.4f}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # RADAR CHART -- All 6 Dimensions
    # ==========================================================================
    st.markdown("### Corridor Dimension Radar")

    dim_keys = list(DIMENSION_META.keys())
    radar_labels = [DIMENSION_META[k]["name"] for k in dim_keys]
    radar_values = [scores.get(k, 0) for k in dim_keys]
    radar_colors = [DIMENSION_META[k]["color"] for k in dim_keys]

    fig_radar = go.Figure()
    fig_radar.add_trace(
        go.Scatterpolar(
            r=radar_values + [radar_values[0]],
            theta=radar_labels + [radar_labels[0]],
            fill="toself",
            fillcolor="rgba(6,182,212,0.15)",
            line=dict(color="#06b6d4", width=2),
            marker=dict(size=7, color=radar_colors + [radar_colors[0]]),
            name="Score",
        )
    )
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(26,26,46,0.6)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#2a3550",
                tickfont=dict(color="#8b97b0", size=10),
            ),
            angularaxis=dict(
                gridcolor="#2a3550",
                tickfont=dict(color="#e8ecf4", size=11),
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=70, r=70, t=30, b=30),
        height=440,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="wilcor_pchart1")

    # ==========================================================================
    # DIMENSION SCORE CARDS (3 cols x 2 rows)
    # ==========================================================================
    st.markdown("### Dimension Scores")

    dim_list = list(DIMENSION_META.keys())
    for row in range(2):
        cols = st.columns(3)
        for ci in range(3):
            idx = row * 3 + ci
            if idx >= len(dim_list):
                break
            dkey = dim_list[idx]
            meta = DIMENSION_META[dkey]
            sc = scores.get(dkey, 0)
            bar_pct = min(sc, 100)
            bar_color = _score_color(sc)

            card_html = (
                f'<div style="background:rgba(26,26,46,0.85);'
                f"border:1px solid #2a3550;border-radius:10px;padding:14px;"
                f'text-align:center;min-height:160px;margin-bottom:8px;">'
                f'<span style="font-size:28px;">{meta["icon"]}</span><br/>'
                f'<span style="color:{meta["color"]};font-weight:bold;'
                f'font-size:13px;">{meta["name"]}</span><br/>'
                f'<span style="color:#e8ecf4;font-size:22px;font-weight:bold;">'
                f"{sc:.0f}/100</span><br/>"
                f'<div style="background:#1a2235;border-radius:6px;height:8px;'
                f'margin:8px 4px 0 4px;overflow:hidden;">'
                f'<div style="width:{bar_pct:.0f}%;background:{bar_color};'
                f'height:100%;border-radius:6px;"></div></div>'
                f'<p style="color:#8b97b0;font-size:11px;margin:6px 0 0 0;">'
                f"{meta['description']}</p>"
                f"</div>"
            )
            with cols[ci]:
                st.markdown(card_html, unsafe_allow_html=True)

    # ==========================================================================
    # BAR CHART -- Dimension Comparison
    # ==========================================================================
    st.markdown("### Dimension Comparison")

    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    bar_names = [DIMENSION_META[k]["name"] for k, _ in sorted_dims]
    bar_values = [v for _, v in sorted_dims]
    bar_colors_list = [DIMENSION_META[k]["color"] for k, _ in sorted_dims]

    fig_bar = go.Figure()
    fig_bar.add_trace(
        go.Bar(
            x=bar_values,
            y=bar_names,
            orientation="h",
            marker=dict(color=bar_colors_list),
            text=[f"{v:.0f}" for v in bar_values],
            textposition="auto",
            textfont=dict(color="#e8ecf4", size=12),
        )
    )
    fig_bar.update_layout(
        xaxis=dict(
            range=[0, 105],
            title="Score (0-100)",
            gridcolor="#2a3550",
            tickfont=dict(color="#8b97b0"),
            title_font=dict(color="#8b97b0"),
        ),
        yaxis=dict(
            tickfont=dict(color="#e8ecf4", size=12),
            autorange="reversed",
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,26,46,0.6)",
        margin=dict(l=160, r=30, t=20, b=40),
        height=320,
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="wilcor_pchart2")

    # ==========================================================================
    # DIMENSION 1: HABITAT PATCHES DETAIL
    # ==========================================================================
    st.markdown("### \U0001F333 Habitat Patches Detail")

    hp1, hp2, hp3, hp4 = st.columns(4)
    hp1.metric("Forests", d1.get("forest_count", 0))
    hp2.metric("Parks", d1.get("park_count", 0))
    hp3.metric("Reserves", d1.get("reserve_count", 0))
    hp4.metric("Patch Type Diversity", f"{d1.get('type_diversity', 0)}/3")

    # Patch composition donut
    patch_labels = ["Forests", "Parks", "Reserves"]
    patch_vals = [
        max(d1.get("forest_count", 0), 0),
        max(d1.get("park_count", 0), 0),
        max(d1.get("reserve_count", 0), 0),
    ]
    if sum(patch_vals) > 0:
        fig_patch = go.Figure()
        fig_patch.add_trace(
            go.Pie(
                labels=patch_labels,
                values=patch_vals,
                marker=dict(colors=["#10b981", "#22c55e", "#059669"]),
                hole=0.45,
                textinfo="label+value",
                textfont=dict(color="#e8ecf4", size=11),
            )
        )
        _dark_layout(fig_patch, height=300, showlegend=False,
                     margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_patch, use_container_width=True, key="wilcor_pchart3")
    else:
        st.warning("No habitat patches detected in the search radius.")

    # ==========================================================================
    # DIMENSION 2: BARRIER ANALYSIS DETAIL
    # ==========================================================================
    st.markdown("### \U0001F6A7 Barrier Analysis Detail")

    ba1, ba2, ba3, ba4 = st.columns(4)
    ba1.metric("Roads", d2.get("road_count", 0))
    ba2.metric("Fences/Walls", d2.get("fence_count", 0))
    ba3.metric("Railways", d2.get("railway_count", 0))
    ba4.metric("Urban Zones", d2.get("urban_count", 0))

    bm1, bm2 = st.columns(2)
    bm1.metric("Road Severity Index", f"{d2.get('road_severity', 0):.1f}")
    bm2.metric("Total Barrier Impact", f"{d2.get('barrier_impact', 0):.1f}")

    # Barrier breakdown bar chart
    barrier_cats = ["Roads", "Fences/Walls", "Railways", "Urban Zones"]
    barrier_vals = [
        d2.get("road_count", 0),
        d2.get("fence_count", 0),
        d2.get("railway_count", 0),
        d2.get("urban_count", 0),
    ]
    fig_barrier = go.Figure()
    fig_barrier.add_trace(
        go.Bar(
            x=barrier_cats,
            y=barrier_vals,
            marker=dict(color=["#ef4444", "#f97316", "#a855f7", "#64748b"]),
            text=[str(v) for v in barrier_vals],
            textposition="auto",
            textfont=dict(color="#e8ecf4", size=12),
        )
    )
    fig_barrier.update_layout(
        xaxis=dict(tickfont=dict(color="#e8ecf4")),
        yaxis=dict(
            title="Count",
            gridcolor="#2a3550",
            tickfont=dict(color="#8b97b0"),
            title_font=dict(color="#8b97b0"),
        ),
    )
    _dark_layout(fig_barrier, height=300)
    st.plotly_chart(fig_barrier, use_container_width=True, key="wilcor_pchart4")

    # ==========================================================================
    # DIMENSION 3: WATER CONNECTIVITY DETAIL
    # ==========================================================================
    st.markdown("### \U0001F30A Water Connectivity Detail")

    wc1, wc2, wc3 = st.columns(3)
    wc1.metric("Rivers", d3.get("river_count", 0))
    wc2.metric("Streams", d3.get("stream_count", 0))
    wc3.metric("Springs", d3.get("spring_count", 0))

    wc4, wc5, wc6 = st.columns(3)
    wc4.metric("Canals", d3.get("canal_count", 0))
    wc5.metric("Water Bodies", d3.get("water_body_count", 0))
    wc6.metric("Total Water Features", d3.get("total_water_features", 0))

    # Water feature donut
    wf_labels = ["Rivers", "Streams", "Springs", "Canals", "Water Bodies"]
    wf_vals = [
        max(d3.get("river_count", 0), 0),
        max(d3.get("stream_count", 0), 0),
        max(d3.get("spring_count", 0), 0),
        max(d3.get("canal_count", 0), 0),
        max(d3.get("water_body_count", 0), 0),
    ]
    if sum(wf_vals) > 0:
        fig_water = go.Figure()
        fig_water.add_trace(
            go.Pie(
                labels=wf_labels,
                values=wf_vals,
                marker=dict(colors=[
                    "#3b82f6", "#06b6d4", "#14b8a6", "#8b5cf6", "#60a5fa",
                ]),
                hole=0.45,
                textinfo="label+value",
                textfont=dict(color="#e8ecf4", size=11),
            )
        )
        _dark_layout(fig_water, height=300, showlegend=False,
                     margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_water, use_container_width=True, key="wilcor_pchart5")
    else:
        st.warning("No water features detected in the search radius.")

    # ==========================================================================
    # DIMENSION 4: SPECIES RICHNESS DETAIL
    # ==========================================================================
    st.markdown("### \U0001F98B Species Richness Detail")

    sr1, sr2, sr3 = st.columns(3)
    sr1.metric("iNaturalist Observations", d4.get("inat_total", 0))
    sr2.metric("GBIF Records", d4.get("gbif_total", 0))
    sr3.metric("GBIF Unique Species", d4.get("gbif_unique_species", 0))

    sr4, sr5, sr6 = st.columns(3)
    sr4.metric("Mammals", d4.get("mammal_count", 0))
    sr5.metric("Birds", d4.get("bird_count", 0))
    sr6.metric("Kingdoms Represented", d4.get("num_kingdoms", 0))

    # Wildlife group indicators row
    sw1, sw2, sw3, sw4 = st.columns(4)
    sw1.metric("Reptiles", d4.get("reptile_count", 0))
    sw2.metric("Amphibians", d4.get("amphibian_count", 0))
    sw3.metric("Insects", d4.get("insect_count", 0))
    sw4.metric("Plants", d4.get("plant_count", 0))

    # Kingdom distribution chart
    kc = d4.get("kingdom_counts") or {}
    if kc:
        bio_c1, bio_c2 = st.columns([1, 1])
        with bio_c1:
            k_names = list(kc.keys())
            k_values = [(kc[k] or 0) for k in k_names]
            k_colors = [KINGDOM_COLORS.get(k, "#8b97b0") for k in k_names]

            fig_kingdom = go.Figure()
            fig_kingdom.add_trace(
                go.Pie(
                    labels=k_names,
                    values=k_values,
                    marker=dict(colors=k_colors),
                    hole=0.45,
                    textinfo="label+percent",
                    textfont=dict(color="#e8ecf4", size=11),
                )
            )
            _dark_layout(fig_kingdom, height=300, showlegend=False,
                         margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_kingdom, use_container_width=True, key="wilcor_pchart6")

        with bio_c2:
            top_sp = d4.get("top_species") or []
            if top_sp:
                st.markdown(
                    '<div style="background:rgba(26,26,46,0.7);'
                    "border:1px solid #2a3550;border-radius:10px;padding:12px;"
                    '">'
                    '<h5 style="color:#e8ecf4;margin:0 0 8px 0;">'
                    "Top Species (Corridor Indicators)</h5>",
                    unsafe_allow_html=True,
                )
                for sci_name, count, common_name in top_sp[:12]:
                    display_name = common_name if common_name else sci_name
                    safe_display_name = html_module.escape(str(display_name))
                    obs_count = (count or 0)
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;'
                        f'padding:3px 0;border-bottom:1px solid #1a2235;">'
                        f'<span style="color:#e8ecf4;font-size:12px;">'
                        f"{safe_display_name}</span>"
                        f'<span style="color:#8b97b0;font-size:11px;'
                        f'font-style:italic;">{obs_count} obs</span></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.info("No top species data available for this location.")

    # ==========================================================================
    # DIMENSION 5: TERRAIN PASSABILITY DETAIL
    # ==========================================================================
    st.markdown("### \U000026F0\uFE0F Terrain Passability Detail")

    tp1, tp2, tp3, tp4 = st.columns(4)
    tp1.metric("Center Elevation", f"{d5.get('center_elevation', 0):.0f} m")
    tp2.metric("Elevation Range", f"{d5.get('elevation_range', 0):.0f} m")
    tp3.metric("Avg Slope", f"{d5.get('avg_slope_deg', 0):.1f}\u00b0")
    tp4.metric("Min Elevation", f"{d5.get('min_elevation', 0):.0f} m")

    tp5, tp6 = st.columns(2)
    tp5.metric("Slope Sub-score", f"{d5.get('slope_score', 0):.0f}/100")
    tp6.metric("Range Sub-score", f"{d5.get('range_score', 0):.0f}/100")

    # Terrain gauge chart
    fig_gauge = go.Figure()
    fig_gauge.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=d5.get("score", 0),
            title=dict(text="Terrain Passability", font=dict(color="#e8ecf4", size=16)),
            number=dict(font=dict(color="#e8ecf4", size=30)),
            gauge=dict(
                axis=dict(range=[0, 100], tickfont=dict(color="#8b97b0")),
                bar=dict(color="#f59e0b"),
                bgcolor="rgba(26,26,46,0.6)",
                borderwidth=1,
                bordercolor="#2a3550",
                steps=[
                    dict(range=[0, 30], color="rgba(239,68,68,0.25)"),
                    dict(range=[30, 60], color="rgba(245,158,11,0.25)"),
                    dict(range=[60, 100], color="rgba(16,185,129,0.25)"),
                ],
                threshold=dict(
                    line=dict(color="#e8ecf4", width=2),
                    thickness=0.8,
                    value=d5.get("score", 0),
                ),
            ),
        )
    )
    _dark_layout(fig_gauge, height=280, margin=dict(l=30, r=30, t=50, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True, key="wilcor_pchart7")

    # ==========================================================================
    # DIMENSION 6: CORRIDOR INTEGRITY DETAIL
    # ==========================================================================
    st.markdown("### \U0001F517 Corridor Integrity Summary")

    ci1, ci2, ci3 = st.columns(3)
    ci1.metric("Overall Score", f"{d6.get('score', 0):.0f}/100")
    ci2.metric("Rating", d6.get("rating", "N/A"))
    ci3.metric("Balance Bonus", f"+{d6.get('balance_bonus', 0):.1f}")

    # Integrity gauge
    fig_integrity = go.Figure()
    fig_integrity.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=d6.get("score", 0),
            title=dict(text="Corridor Integrity Index", font=dict(color="#e8ecf4", size=16)),
            number=dict(font=dict(color="#e8ecf4", size=36)),
            gauge=dict(
                axis=dict(range=[0, 100], tickfont=dict(color="#8b97b0")),
                bar=dict(color=d6.get("rating_color", "#06b6d4")),
                bgcolor="rgba(26,26,46,0.6)",
                borderwidth=1,
                bordercolor="#2a3550",
                steps=[
                    dict(range=[0, 20], color="rgba(220,38,38,0.2)"),
                    dict(range=[20, 40], color="rgba(239,68,68,0.2)"),
                    dict(range=[40, 60], color="rgba(245,158,11,0.2)"),
                    dict(range=[60, 80], color="rgba(6,182,212,0.2)"),
                    dict(range=[80, 100], color="rgba(16,185,129,0.2)"),
                ],
                threshold=dict(
                    line=dict(color="#e8ecf4", width=2),
                    thickness=0.8,
                    value=d6.get("score", 0),
                ),
            ),
        )
    )
    _dark_layout(fig_integrity, height=300, margin=dict(l=30, r=30, t=50, b=20))
    st.plotly_chart(fig_integrity, use_container_width=True, key="wilcor_pchart8")

    # ==========================================================================
    # RECOMMENDATIONS
    # ==========================================================================
    st.markdown("### Corridor Recommendations")

    recs = d6.get("recommendations", [])
    for i, rec in enumerate(recs):
        rec_color = "#10b981" if d6.get("score", 0) >= 60 else "#f59e0b"
        st.markdown(
            f'<div style="background:rgba(26,26,46,0.7);border-left:3px solid '
            f"{rec_color};border-radius:0 8px 8px 0;padding:10px 14px;"
            f'margin-bottom:8px;">'
            f'<span style="color:#e8ecf4;font-size:13px;">'
            f"{i + 1}. {rec}</span></div>",
            unsafe_allow_html=True,
        )

    # ==========================================================================
    # SCORING BREAKDOWN TABLE
    # ==========================================================================
    st.markdown("### Scoring Breakdown")

    table_rows = ""
    for dkey in DIMENSION_META:
        meta = DIMENSION_META[dkey]
        sc = scores.get(dkey, 0)
        sc_color = _score_color(sc)
        bar_pct = min(sc, 100)
        table_rows += (
            f"<tr>"
            f'<td style="padding:8px;color:{meta["color"]};font-weight:bold;'
            f'font-size:13px;">{meta["icon"]} {meta["name"]}</td>'
            f'<td style="padding:8px;text-align:center;">'
            f'<span style="color:{sc_color};font-weight:bold;font-size:15px;">'
            f"{sc:.0f}</span></td>"
            f'<td style="padding:8px;width:40%;">'
            f'<div style="background:#1a2235;border-radius:6px;height:10px;'
            f'overflow:hidden;">'
            f'<div style="width:{bar_pct:.0f}%;background:{sc_color};'
            f'height:100%;border-radius:6px;"></div></div></td>'
            f'<td style="padding:8px;color:#8b97b0;font-size:12px;">'
            f"{meta['description']}</td>"
            f"</tr>"
        )

    st.markdown(
        f'<div style="overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;'
        f'background:rgba(26,26,46,0.7);border-radius:10px;overflow:hidden;">'
        f"<thead><tr>"
        f'<th style="padding:10px;text-align:left;color:#8b97b0;'
        f'border-bottom:1px solid #2a3550;font-size:12px;">Dimension</th>'
        f'<th style="padding:10px;text-align:center;color:#8b97b0;'
        f'border-bottom:1px solid #2a3550;font-size:12px;">Score</th>'
        f'<th style="padding:10px;text-align:left;color:#8b97b0;'
        f'border-bottom:1px solid #2a3550;font-size:12px;">Progress</th>'
        f'<th style="padding:10px;text-align:left;color:#8b97b0;'
        f'border-bottom:1px solid #2a3550;font-size:12px;">Description</th>'
        f"</tr></thead>"
        f"<tbody>{table_rows}</tbody>"
        f"</table></div>",
        unsafe_allow_html=True,
    )

    # ==========================================================================
    # FOOTER
    # ==========================================================================
    st.markdown(
        '<div style="text-align:center;padding:12px;margin-top:16px;">'
        '<span style="color:#5a6580;font-size:11px;">'
        "Data: Overpass API / iNaturalist / GBIF / Open Topo Data | "
        "Wildlife Corridor AI | TerraScout AI</span></div>",
        unsafe_allow_html=True,
    )
