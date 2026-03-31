"""
Satellite Intelligence module for TerraScout AI.

Fetches NDVI, land cover, and vegetation data from free satellite and
geospatial APIs (MODIS, Overpass/OSM, Open-Meteo).  No API keys required.
"""

import math
import logging
import requests
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODIS_NDVI_URL = (
    "https://modis.ornl.gov/rst/api/v1/MOD13Q1/subset"
    "?latitude={lat}&longitude={lon}&kmAboveBelow=0&kmLeftRight=0"
)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OPEN_METEO_CLIMATE_URL = (
    "https://climate-api.open-meteo.com/v1/climate"
    "?latitude={lat}&longitude={lon}"
    "&models=EC_Earth3P_HR"
    "&monthly=precipitation_sum,temperature_2m_mean"
    "&start_date=2024-01-01&end_date=2024-12-31"
)

NDVI_THRESHOLDS = {
    "dense":    0.6,
    "moderate": 0.3,
    "sparse":   0.1,
}

HEALTH_THRESHOLDS = {
    "excellent": 0.7,
    "good":      0.5,
    "fair":      0.3,
    "poor":      0.15,
}

LAND_USE_MAP = {
    "forest":       "Forest",
    "wood":         "Forest",
    "orchard":      "Forest",
    "farmland":     "Agricultural",
    "farm":         "Agricultural",
    "agriculture":  "Agricultural",
    "vineyard":     "Agricultural",
    "allotments":   "Agricultural",
    "residential":  "Urban/Built",
    "commercial":   "Urban/Built",
    "industrial":   "Urban/Built",
    "retail":       "Urban/Built",
    "construction": "Urban/Built",
    "grass":        "Grassland",
    "meadow":       "Grassland",
    "heath":        "Grassland",
    "scrub":        "Grassland",
    "water":        "Water/Wetland",
    "wetland":      "Water/Wetland",
    "reservoir":    "Water/Wetland",
    "marsh":        "Water/Wetland",
    "sand":         "Barren",
    "rock":         "Barren",
    "scree":        "Barren",
    "bare_rock":    "Barren",
}

# ---------------------------------------------------------------------------
# 1. NDVI Data
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def _fetch_modis_ndvi(lat: float, lon: float):
    """Attempt to fetch real MODIS NDVI from ORNL DAAC REST API."""
    try:
        url = MODIS_NDVI_URL.format(lat=lat, lon=lon)
        resp = requests.get(url, timeout=12, headers={"Accept": "application/json"})
        resp.raise_for_status()
        data = resp.json()
        subset = data.get("subset", [])
        if not subset:
            return None
        # MODIS NDVI values are scaled by 10000
        values = []
        for entry in subset:
            raw = entry.get("data", [])
            for v in raw:
                if isinstance(v, (int, float)) and v > -2000:
                    values.append(v / 10000.0)
        if values:
            return values
    except Exception as exc:
        logger.debug("MODIS NDVI fetch failed: %s", exc)
    return None


@st.cache_data(ttl=1800)
def _fetch_climate_proxy(lat: float, lon: float):
    """Fetch monthly precipitation and temperature from Open-Meteo Climate API."""
    try:
        url = OPEN_METEO_CLIMATE_URL.format(lat=lat, lon=lon)
        resp = requests.get(url, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        monthly = data.get("monthly", {})
        precip = monthly.get("precipitation_sum", [])
        temp = monthly.get("temperature_2m_mean", [])
        annual_precip = sum(p for p in precip if p is not None) if precip else None
        avg_temp = (
            sum(t for t in temp if t is not None) / max(len([t for t in temp if t is not None]), 1)
            if temp else None
        )
        return {"annual_precip_mm": annual_precip, "avg_temp_c": avg_temp}
    except Exception as exc:
        logger.debug("Climate proxy fetch failed: %s", exc)
    return {"annual_precip_mm": None, "avg_temp_c": None}


def _estimate_ndvi(lat: float, lon: float, climate: dict) -> float:
    """Estimate NDVI from latitude, and climate data when satellite is unavailable."""
    abs_lat = abs(lat)
    precip = climate.get("annual_precip_mm")
    avg_temp = climate.get("avg_temp_c")

    # Start with latitude-based baseline
    if abs_lat > 70:
        base = 0.08
    elif abs_lat > 60:
        base = 0.20
    elif abs_lat > 50:
        base = 0.40
    elif abs_lat > 23:
        base = 0.45
    else:
        base = 0.60  # tropical

    # Adjust for precipitation
    if precip is not None:
        if precip < 100:
            base *= 0.25
        elif precip < 250:
            base *= 0.50
        elif precip < 500:
            base *= 0.75
        elif precip > 1500:
            base = min(base * 1.15, 0.85)

    # Adjust for temperature
    if avg_temp is not None:
        if avg_temp < -5:
            base *= 0.5
        elif avg_temp < 5:
            base *= 0.7
        elif avg_temp > 25 and (precip is None or precip > 600):
            base = min(base * 1.10, 0.85)

    return round(max(0.0, min(1.0, base)), 3)


def _classify_ndvi(ndvi: float) -> str:
    if ndvi >= NDVI_THRESHOLDS["dense"]:
        return "Dense Vegetation"
    if ndvi >= NDVI_THRESHOLDS["moderate"]:
        return "Moderate Vegetation"
    if ndvi >= NDVI_THRESHOLDS["sparse"]:
        return "Sparse Vegetation"
    return "Barren/Water"


def _assess_health(ndvi: float) -> str:
    if ndvi >= HEALTH_THRESHOLDS["excellent"]:
        return "Excellent"
    if ndvi >= HEALTH_THRESHOLDS["good"]:
        return "Good"
    if ndvi >= HEALTH_THRESHOLDS["fair"]:
        return "Fair"
    if ndvi >= HEALTH_THRESHOLDS["poor"]:
        return "Poor"
    return "Critical"


def _seasonal_variation(ndvi_values: list) -> str:
    """Determine seasonal variation from a time-series of NDVI values."""
    if not ndvi_values or len(ndvi_values) < 3:
        return "LOW"
    ndvi_range = max(ndvi_values) - min(ndvi_values)
    if ndvi_range > 0.35:
        return "HIGH"
    if ndvi_range > 0.15:
        return "MODERATE"
    return "LOW"


@st.cache_data(ttl=1800)
def fetch_ndvi_data(lat: float, lon: float) -> dict:
    """
    Fetch or estimate NDVI for a given location.

    Tries MODIS satellite data first; falls back to climate-based estimation.
    Returns a dict with ndvi_current, classification, health, etc.
    """
    estimated = True
    seasonal = "LOW"

    # Try real satellite data
    modis_values = _fetch_modis_ndvi(lat, lon)
    climate = _fetch_climate_proxy(lat, lon)

    if modis_values and len(modis_values) >= 1:
        ndvi_current = round(modis_values[-1], 3)
        ndvi_current = max(0.0, min(1.0, ndvi_current))
        estimated = False
        seasonal = _seasonal_variation(modis_values)
    else:
        ndvi_current = _estimate_ndvi(lat, lon, climate)
        # Estimate seasonal variation from latitude
        abs_lat = abs(lat)
        if 23 < abs_lat < 55:
            seasonal = "HIGH"
        elif 10 < abs_lat <= 23 or 55 <= abs_lat < 66:
            seasonal = "MODERATE"
        else:
            seasonal = "LOW"

    classification = _classify_ndvi(ndvi_current)
    health = _assess_health(ndvi_current)
    green_cover_pct = round(min(ndvi_current * 120, 100.0), 1)

    return {
        "ndvi_current": ndvi_current,
        "ndvi_classification": classification,
        "vegetation_health": health,
        "estimated": estimated,
        "green_cover_pct": green_cover_pct,
        "seasonal_variation": seasonal,
    }


# ---------------------------------------------------------------------------
# 2. Land Cover
# ---------------------------------------------------------------------------


def _shannon_diversity(distribution: dict) -> float:
    """Compute Shannon diversity index from a percentage distribution."""
    total = sum(distribution.values())
    if total <= 0:
        return 0.0
    H = 0.0
    for count in distribution.values():
        if count > 0:
            p = count / total
            H -= p * math.log(p)
    # Normalise by ln(number of categories) so result is in [0, 1]
    n = len(distribution)
    if n <= 1:
        return 0.0
    return round(H / math.log(n), 3)


@st.cache_data(ttl=1800)
def fetch_land_cover(lat: float, lon: float) -> dict:
    """
    Determine dominant land cover around a location using OSM via Overpass API.

    Queries for landuse and natural tags within 1 km, then classifies.
    """
    query = (
        f'[out:json][timeout:10];'
        f'(way["landuse"](around:1000,{lat},{lon});'
        f'way["natural"](around:1000,{lat},{lon}););'
        f'out tags;'
    )

    category_counts: dict[str, int] = {}

    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        elements = data.get("elements", [])

        for elem in elements:
            tags = elem.get("tags", {})
            raw_landuse = tags.get("landuse", "")
            raw_natural = tags.get("natural", "")
            raw_key = raw_landuse or raw_natural
            if not raw_key:
                continue
            category = LAND_USE_MAP.get(raw_key.lower(), "Other")
            category_counts[category] = category_counts.get(category, 0) + 1

    except Exception as exc:
        logger.warning("Land cover Overpass query failed: %s", exc)

    # Build distribution as percentages
    total = sum(category_counts.values()) if category_counts else 0
    if total > 0:
        cover_distribution = {k: round(v / total * 100, 1) for k, v in category_counts.items()}
    else:
        cover_distribution = {"Unknown": 100.0}

    dominant = max(cover_distribution, key=cover_distribution.get)

    # Urbanisation level
    urban_pct = cover_distribution.get("Urban/Built", 0.0)
    if urban_pct >= 60:
        urbanization = "HIGH"
    elif urban_pct >= 25:
        urbanization = "MODERATE"
    elif urban_pct > 0:
        urbanization = "LOW"
    else:
        urbanization = "NONE"

    # Natural percentage (Forest + Grassland + Water/Wetland)
    natural_pct = sum(
        cover_distribution.get(c, 0.0)
        for c in ("Forest", "Grassland", "Water/Wetland")
    )
    natural_pct = round(min(natural_pct, 100.0), 1)

    diversity = _shannon_diversity(category_counts) if category_counts else 0.0

    return {
        "dominant_cover": dominant,
        "cover_distribution": cover_distribution,
        "urbanization_level": urbanization,
        "natural_pct": natural_pct,
        "land_use_diversity": diversity,
    }


# ---------------------------------------------------------------------------
# 3. Surface Water
# ---------------------------------------------------------------------------

WATER_TYPE_MAP = {
    "river":      "River",
    "stream":     "Stream",
    "canal":      "Canal",
    "drain":      "Drain",
    "ditch":      "Ditch",
    "lake":       "Lake",
    "reservoir":  "Reservoir",
    "pond":       "Pond",
    "basin":      "Basin",
    "lagoon":     "Lagoon",
    "oxbow":      "Oxbow",
    "wastewater": "Wastewater",
}


@st.cache_data(ttl=1800)
def fetch_surface_water(lat: float, lon: float) -> dict:
    """
    Detect surface water features within 5 km of the location via Overpass API.

    Returns count, types, proximity classification, and diversity.
    """
    query = (
        f'[out:json][timeout:10];'
        f'(way["water"](around:5000,{lat},{lon});'
        f'way["waterway"](around:5000,{lat},{lon});'
        f'relation["water"](around:5000,{lat},{lon}););'
        f'out tags;'
    )

    water_types_found: list[str] = []
    water_bodies_count = 0

    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        elements = data.get("elements", [])
        water_bodies_count = len(elements)

        for elem in elements:
            tags = elem.get("tags", {})
            raw_water = tags.get("water", "")
            raw_waterway = tags.get("waterway", "")
            raw_key = raw_water or raw_waterway
            if raw_key:
                mapped = WATER_TYPE_MAP.get(raw_key.lower(), raw_key.capitalize())
                if mapped not in water_types_found:
                    water_types_found.append(mapped)

    except Exception as exc:
        logger.warning("Surface water Overpass query failed: %s", exc)

    # Proximity heuristic: more features nearby implies closer proximity
    if water_bodies_count == 0:
        proximity = "NONE"
    elif water_bodies_count >= 10:
        proximity = "ADJACENT"
    elif water_bodies_count >= 5:
        proximity = "NEAR"
    elif water_bodies_count >= 2:
        proximity = "MODERATE"
    else:
        proximity = "DISTANT"

    nearest_type = water_types_found[0] if water_types_found else "None"

    # Water diversity (normalised Shannon)
    type_counts: dict[str, int] = {}
    for wt in water_types_found:
        type_counts[wt] = type_counts.get(wt, 0) + 1
    water_diversity = _shannon_diversity(type_counts) if len(type_counts) > 1 else 0.0

    return {
        "water_bodies_count": water_bodies_count,
        "water_types": water_types_found,
        "nearest_water_type": nearest_type,
        "surface_water_proximity": proximity,
        "water_diversity": water_diversity,
    }


# ---------------------------------------------------------------------------
# 4. Composite Vegetation / Land Quality Score
# ---------------------------------------------------------------------------


def compute_vegetation_index_score(
    ndvi: dict,
    land_cover: dict,
    surface_water: dict,
) -> dict:
    """
    Compute a composite vegetation / land quality score (0-100).

    Factors:
        - NDVI value (40 pts)
        - Green cover percentage (20 pts)
        - Natural area percentage (20 pts)
        - Water diversity (10 pts)
        - Land use diversity (10 pts)
        - Penalties for high urbanisation or barren cover
    """
    ndvi_val = ndvi.get("ndvi_current", 0.0)
    green_pct = ndvi.get("green_cover_pct", 0.0)
    natural_pct = land_cover.get("natural_pct", 0.0)
    water_div = surface_water.get("water_diversity", 0.0)
    land_div = land_cover.get("land_use_diversity", 0.0)
    urban_level = land_cover.get("urbanization_level", "NONE")
    dominant = land_cover.get("dominant_cover", "Unknown")

    factors: list[dict] = []

    # NDVI contribution: up to 40
    ndvi_contrib = round(ndvi_val * 40, 1)
    factors.append({"name": "NDVI Value", "contribution": ndvi_contrib})

    # Green cover: up to 20
    green_contrib = round(green_pct * 0.2, 1)
    factors.append({"name": "Green Cover", "contribution": green_contrib})

    # Natural percentage: up to 20
    natural_contrib = round(natural_pct * 0.2, 1)
    factors.append({"name": "Natural Area", "contribution": natural_contrib})

    # Water diversity: up to 10
    water_contrib = round(water_div * 10, 1)
    factors.append({"name": "Water Diversity", "contribution": water_contrib})

    # Land use diversity: up to 10
    land_contrib = round(land_div * 10, 1)
    factors.append({"name": "Land Use Diversity", "contribution": land_contrib})

    raw_score = ndvi_contrib + green_contrib + natural_contrib + water_contrib + land_contrib

    # Penalties
    penalty = 0.0
    if urban_level == "HIGH":
        penalty += 10.0
        factors.append({"name": "High Urbanisation Penalty", "contribution": -10.0})
    if dominant == "Barren":
        penalty += 15.0
        factors.append({"name": "Barren Cover Penalty", "contribution": -15.0})

    score = round(max(0.0, min(100.0, raw_score - penalty)), 1)

    # Grade
    if score >= 80:
        grade = "A"
    elif score >= 65:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"

    # Summary
    health = ndvi.get("vegetation_health", "Unknown")
    summary = (
        f"This location scores {score}/100 (Grade {grade}) for vegetation and land quality. "
        f"Vegetation health is {health} with {green_pct}% estimated green cover and "
        f"a dominant land cover of {dominant}."
    )

    return {
        "vegetation_score": score,
        "grade": grade,
        "factors": factors,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# 5. Complete Satellite Profile
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def fetch_complete_satellite_profile(lat: float, lon: float) -> dict:
    """
    Master function that assembles the full satellite intelligence profile.

    Calls all sub-functions and returns a unified result dict.
    """
    ndvi_data = fetch_ndvi_data(lat, lon)
    land_cover_data = fetch_land_cover(lat, lon)
    surface_water_data = fetch_surface_water(lat, lon)
    score_result = compute_vegetation_index_score(
        ndvi_data, land_cover_data, surface_water_data
    )

    return {
        "ndvi": ndvi_data,
        "land_cover": land_cover_data,
        "surface_water": surface_water_data,
        "vegetation_score": score_result,
    }


# ---------------------------------------------------------------------------
# Streamlit Rendering Entry Point
# ---------------------------------------------------------------------------


def render_satellite_intelligence_tab():
    """Render the Satellite Intelligence module inside a Streamlit tab."""
    st.header("Satellite Intelligence")
    st.caption(
        "NDVI, land cover classification, and surface water detection "
        "powered by MODIS, Open-Meteo, and OpenStreetMap."
    )

    col1, col2 = st.columns(2)
    with col1:
        lat = st.number_input(
            "Latitude", value=41.9028, format="%.4f", key="satint_lat"
        )
    with col2:
        lon = st.number_input(
            "Longitude", value=12.4964, format="%.4f", key="satint_lon"
        )

    if st.button("Analyse Location", key="satint_run"):
        with st.spinner("Fetching satellite intelligence..."):
            profile = fetch_complete_satellite_profile(lat, lon)

        # --- NDVI -----------------------------------------------------------
        st.subheader("Vegetation Index (NDVI)")
        ndvi = profile["ndvi"]
        source_label = "Estimated" if ndvi["estimated"] else "MODIS Satellite"
        c1, c2, c3 = st.columns(3)
        c1.metric("NDVI", f'{ndvi["ndvi_current"]:.3f}', help=f"Source: {source_label}")
        c2.metric("Classification", ndvi["ndvi_classification"])
        c3.metric("Health", ndvi["vegetation_health"])

        c4, c5, c6 = st.columns(3)
        c4.metric("Green Cover", f'{ndvi["green_cover_pct"]:.1f}%')
        c5.metric("Seasonal Variation", ndvi["seasonal_variation"])
        c6.metric("Data Source", source_label)

        # --- Land Cover ------------------------------------------------------
        st.subheader("Land Cover")
        lc = profile["land_cover"]
        lc1, lc2, lc3 = st.columns(3)
        lc1.metric("Dominant Cover", lc["dominant_cover"])
        lc2.metric("Urbanisation", lc["urbanization_level"])
        lc3.metric("Natural Area", f'{lc["natural_pct"]:.1f}%')

        if lc["cover_distribution"] and "Unknown" not in lc["cover_distribution"]:
            st.markdown("**Cover Distribution**")
            for cover_type, pct in sorted(
                lc["cover_distribution"].items(), key=lambda x: x[1], reverse=True
            ):
                st.progress(min(pct / 100, 1.0), text=f"{cover_type}: {pct:.1f}%")

        # --- Surface Water ---------------------------------------------------
        st.subheader("Surface Water")
        sw = profile["surface_water"]
        sw1, sw2, sw3 = st.columns(3)
        sw1.metric("Water Bodies", sw["water_bodies_count"])
        sw2.metric("Proximity", sw["surface_water_proximity"])
        sw3.metric("Nearest Type", sw["nearest_water_type"])

        if sw["water_types"]:
            st.markdown(
                "**Types detected:** " + ", ".join(sw["water_types"])
            )

        # --- Composite Score -------------------------------------------------
        st.subheader("Vegetation Quality Score")
        vs = profile["vegetation_score"]
        grade_colors = {"A": "green", "B": "blue", "C": "orange", "D": "red", "F": "red"}
        grade_color = grade_colors.get(vs["grade"], "gray")

        st.markdown(
            f'### Score: **{vs["vegetation_score"]:.1f}** / 100 '
            f'&mdash; Grade: :{grade_color}[**{vs["grade"]}**]'
        )
        st.info(vs["summary"])

        st.markdown("**Factor Breakdown**")
        for factor in vs["factors"]:
            sign = "+" if factor["contribution"] >= 0 else ""
            st.text(f'  {factor["name"]}: {sign}{factor["contribution"]:.1f}')
