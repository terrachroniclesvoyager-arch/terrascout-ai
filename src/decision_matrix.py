"""
Decision Matrix AI module for TerraScout AI.
Multi-criteria decision support system that evaluates geographic locations
against 8 common decision scenarios and recommends the best course of action.

Uses real data from SoilGrids, Open-Meteo, Overpass, USGS, iNaturalist, GBIF
and Open-Elevation to produce GO / CAUTION / NO-GO recommendations.
"""

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_species_breakdown,
    fetch_earthquakes,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Decision Scenario Definitions
# ---------------------------------------------------------------------------

DECISION_SCENARIOS: Dict[str, dict] = {
    "residence": {
        "name": "Buy Land for Residence",
        "icon": "\U0001f3e0",
        "criteria": {
            "safety": {"weight": 0.25, "source": "hazards", "label": "Safety from Hazards"},
            "amenities": {"weight": 0.20, "source": "infrastructure", "label": "Amenities & Infrastructure"},
            "climate": {"weight": 0.15, "source": "weather", "label": "Climate Comfort"},
            "water": {"weight": 0.15, "source": "water", "label": "Water Availability"},
            "terrain": {"weight": 0.10, "source": "elevation", "label": "Terrain Suitability"},
            "environment": {"weight": 0.15, "source": "ecology", "label": "Environmental Quality"},
        },
    },
    "agriculture": {
        "name": "Agricultural Investment",
        "icon": "\U0001f33e",
        "criteria": {
            "soil_quality": {"weight": 0.30, "source": "soil", "label": "Soil Quality"},
            "water_availability": {"weight": 0.25, "source": "water", "label": "Water Availability"},
            "climate_suitability": {"weight": 0.20, "source": "weather", "label": "Climate Suitability"},
            "terrain_slope": {"weight": 0.15, "source": "elevation", "label": "Terrain & Slope"},
            "market_access": {"weight": 0.10, "source": "infrastructure", "label": "Market Access"},
        },
    },
    "commercial": {
        "name": "Commercial Development",
        "icon": "\U0001f3e2",
        "criteria": {
            "infrastructure": {"weight": 0.30, "source": "infrastructure", "label": "Infrastructure Density"},
            "accessibility": {"weight": 0.25, "source": "infrastructure_roads", "label": "Transport & Roads"},
            "terrain_flat": {"weight": 0.15, "source": "elevation", "label": "Flat Buildable Terrain"},
            "hazard_safety": {"weight": 0.15, "source": "hazards", "label": "Hazard Safety"},
            "environment_compliance": {"weight": 0.15, "source": "ecology", "label": "Environmental Compliance"},
        },
    },
    "conservation": {
        "name": "Conservation / Protection",
        "icon": "\U0001f33f",
        "criteria": {
            "biodiversity": {"weight": 0.30, "source": "biodiversity", "label": "Biodiversity Richness"},
            "protected_status": {"weight": 0.25, "source": "protected", "label": "Existing Protection"},
            "ecosystem_health": {"weight": 0.20, "source": "ecology", "label": "Ecosystem Health"},
            "threat_level": {"weight": 0.15, "source": "threats", "label": "Threat Level (inverse)"},
            "water_ecology": {"weight": 0.10, "source": "water", "label": "Aquatic Ecosystem"},
        },
    },
    "tourism": {
        "name": "Tourism Development",
        "icon": "\U0001f3d6\ufe0f",
        "criteria": {
            "scenic_value": {"weight": 0.25, "source": "elevation", "label": "Scenic / Terrain Value"},
            "climate_appeal": {"weight": 0.20, "source": "weather", "label": "Climate Appeal"},
            "amenities_nearby": {"weight": 0.20, "source": "infrastructure", "label": "Amenities Nearby"},
            "accessibility": {"weight": 0.15, "source": "infrastructure_roads", "label": "Accessibility"},
            "nature_culture": {"weight": 0.20, "source": "biodiversity", "label": "Nature & Cultural Sites"},
        },
    },
    "renewable_energy": {
        "name": "Renewable Energy",
        "icon": "\u2600\ufe0f",
        "criteria": {
            "solar_potential": {"weight": 0.25, "source": "weather_solar", "label": "Solar Radiation Potential"},
            "wind_potential": {"weight": 0.20, "source": "weather_wind", "label": "Wind Energy Potential"},
            "grid_access": {"weight": 0.20, "source": "infrastructure", "label": "Grid / Infrastructure Access"},
            "terrain_install": {"weight": 0.15, "source": "elevation", "label": "Terrain for Installation"},
            "env_impact": {"weight": 0.20, "source": "ecology", "label": "Low Environmental Impact"},
        },
    },
    "emergency_shelter": {
        "name": "Emergency Shelter",
        "icon": "\u26d1\ufe0f",
        "criteria": {
            "hazard_safety": {"weight": 0.30, "source": "hazards", "label": "Safety from Hazards"},
            "water_access": {"weight": 0.25, "source": "water", "label": "Water Access"},
            "terrain_stable": {"weight": 0.15, "source": "elevation", "label": "Stable Terrain"},
            "access_routes": {"weight": 0.15, "source": "infrastructure_roads", "label": "Access Routes"},
            "building_materials": {"weight": 0.15, "source": "infrastructure", "label": "Building Materials Nearby"},
        },
    },
    "scientific_research": {
        "name": "Scientific Research",
        "icon": "\U0001f52c",
        "criteria": {
            "biodiversity_interest": {"weight": 0.30, "source": "biodiversity", "label": "Biodiversity Interest"},
            "geological_interest": {"weight": 0.25, "source": "elevation", "label": "Geological Interest"},
            "accessibility": {"weight": 0.15, "source": "infrastructure_roads", "label": "Accessibility"},
            "existing_data": {"weight": 0.15, "source": "biodiversity_data", "label": "Existing Study Data"},
            "environment_pristine": {"weight": 0.15, "source": "ecology", "label": "Pristine Environment"},
        },
    },
}

# Verdict thresholds
VERDICT_GO = 65
VERDICT_CAUTION = 40

VERDICT_COLORS = {
    "GO": "#22c55e",
    "CAUTION": "#f59e0b",
    "NO-GO": "#ef4444",
}


# ---------------------------------------------------------------------------
# Cached data collection
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def _collect_location_data(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch all data sources for a location and return as a dict."""
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elevation = fetch_elevation_grid(lat, lon)
    infrastructure = fetch_landuse_infrastructure(lat, lon)
    protected = fetch_protected_areas(lat, lon)
    inat = fetch_biodiversity(lat, lon)
    gbif = fetch_gbif_occurrences(lat, lon)
    species = compute_species_breakdown(inat, gbif)
    earthquakes = fetch_earthquakes(lat, lon)
    return {
        "soil": soil,
        "weather": weather,
        "water": water,
        "elevation": elevation,
        "infrastructure": infrastructure,
        "protected": protected,
        "inat": inat,
        "gbif": gbif,
        "species": species,
        "earthquakes": earthquakes,
    }


# ---------------------------------------------------------------------------
# SoilGrids helper -- safe value extraction
# ---------------------------------------------------------------------------

def _build_soil_layer_map(soil: Any) -> dict:
    """Return {layer_name: layer_dict} from raw SoilGrids response."""
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map: dict = {}
    for _l in (_layers if isinstance(_layers, list) else []):
        _ln = _l.get("name", "") if isinstance(_l, dict) else ""
        if _ln:
            _layer_map[_ln] = _l
    return _layer_map


def _soil_value(layer_map: dict, name: str, div: float = 10) -> Optional[float]:
    """Extract top-depth mean value from soil layer map."""
    p = layer_map.get(name, {})
    if isinstance(p, dict):
        depths = p.get("depths", [])
        if depths:
            raw = (depths[0].get("values", {}) if isinstance(depths[0], dict) else {}).get("mean")
            if raw is not None:
                return raw / div
    return None


# ---------------------------------------------------------------------------
# Individual criterion scorers  (each returns 0-100)
# ---------------------------------------------------------------------------

def _clamp(val: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, val))


# -- Hazard / safety score ------------------------------------------------

@st.cache_data(ttl=1800)
def _score_hazards(earthquakes: dict, water: dict, elevation: dict, infrastructure: dict) -> Tuple[float, List[str], List[str]]:
    """Return (score 0-100, risks, advantages). Higher = safer."""
    risks: List[str] = []
    advantages: List[str] = []

    # Seismic
    eq_features = (earthquakes if isinstance(earthquakes, dict) else {}).get("features", [])
    mags = [
        (f.get("properties", {}) if isinstance(f, dict) else {}).get("mag", 0) or 0
        for f in (eq_features if isinstance(eq_features, list) else [])
    ]
    max_mag = max(mags) if mags else 0
    eq_count = len(mags)
    seismic_penalty = min(50, (max_mag / 9.0) * 30 + min(eq_count / 50.0, 1.0) * 20)

    if max_mag >= 5:
        risks.append(f"Significant seismic activity (max M{max_mag:.1f}, {eq_count} events)")
    elif eq_count == 0:
        advantages.append("No recorded seismic events in the area")

    # Flood proxy
    water_els = (water if isinstance(water, dict) else {}).get("elements", [])
    center_elev = (elevation if isinstance(elevation, dict) else {}).get("center_elevation", 100) or 100
    flood_penalty = min(20, len(water_els) / 30.0 * 10 + max(0, (50 - center_elev) / 50.0) * 10)
    if center_elev < 10:
        risks.append(f"Very low elevation ({center_elev:.0f} m) -- flood risk")
    elif center_elev > 200:
        advantages.append(f"Elevated position ({center_elev:.0f} m) reduces flood risk")

    # Landslide proxy
    elev_range = ((elevation if isinstance(elevation, dict) else {}).get("max_elevation", 0) or 0) - (
        (elevation if isinstance(elevation, dict) else {}).get("min_elevation", 0) or 0
    )
    landslide_penalty = min(15, elev_range / 500.0 * 15)
    if elev_range > 300:
        risks.append(f"Steep terrain (elevation range {elev_range:.0f} m) -- landslide risk")

    # Pollution proxy from infrastructure
    infra_els = (infrastructure if isinstance(infrastructure, dict) else {}).get("elements", [])
    industrial_count = sum(
        1 for el in infra_els
        if (el.get("tags", {}) if isinstance(el, dict) else {}).get("landuse") in ("industrial", "construction")
    )
    pollution_penalty = min(15, industrial_count / 10.0 * 15)
    if industrial_count > 5:
        risks.append(f"{industrial_count} industrial/construction zones nearby")
    elif industrial_count == 0:
        advantages.append("No industrial zones detected nearby")

    total_penalty = seismic_penalty + flood_penalty + landslide_penalty + pollution_penalty
    score = _clamp(100 - total_penalty)
    return score, risks, advantages


# -- Infrastructure / amenities -------------------------------------------

@st.cache_data(ttl=1800)
def _score_infrastructure(infrastructure: dict) -> Tuple[float, List[str], List[str]]:
    """Score infrastructure density (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    elements = (infrastructure if isinstance(infrastructure, dict) else {}).get("elements", [])
    building_count = 0
    road_count = 0
    park_count = 0
    for el in elements:
        tags = (el.get("tags", {}) if isinstance(el, dict) else {})
        if "building" in tags:
            building_count += 1
        if "highway" in tags:
            road_count += 1
        if tags.get("leisure") == "park":
            park_count += 1

    building_score = min(40, building_count / 50.0 * 40)
    road_score = min(35, road_count / 30.0 * 35)
    park_score = min(25, park_count / 3.0 * 25)
    score = _clamp(building_score + road_score + park_score)

    if building_count > 30:
        advantages.append(f"{building_count} buildings nearby -- good urban coverage")
    elif building_count < 5:
        risks.append("Very few buildings -- limited amenities")
    if road_count > 20:
        advantages.append(f"{road_count} road segments -- well connected")
    elif road_count < 3:
        risks.append("Very few roads -- poor connectivity")
    if park_count > 0:
        advantages.append(f"{park_count} parks / leisure areas nearby")
    return score, risks, advantages


# -- Road accessibility sub-score -----------------------------------------

@st.cache_data(ttl=1800)
def _score_roads(infrastructure: dict) -> Tuple[float, List[str], List[str]]:
    """Score road / transport accessibility (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    elements = (infrastructure if isinstance(infrastructure, dict) else {}).get("elements", [])
    road_count = 0
    major_road = 0
    for el in elements:
        tags = (el.get("tags", {}) if isinstance(el, dict) else {})
        hw = tags.get("highway", "")
        if hw:
            road_count += 1
            if hw in ("motorway", "trunk", "primary", "secondary"):
                major_road += 1

    score = _clamp(min(60, road_count / 25.0 * 60) + min(40, major_road / 3.0 * 40))
    if major_road > 0:
        advantages.append(f"{major_road} major road(s) nearby")
    else:
        risks.append("No major roads detected in the area")
    if road_count < 3:
        risks.append("Very limited road network")
    elif road_count > 15:
        advantages.append("Dense road network")
    return score, risks, advantages


# -- Weather / climate comfort --------------------------------------------

@st.cache_data(ttl=1800)
def _score_weather(weather: dict) -> Tuple[float, List[str], List[str]]:
    """Score climate comfort (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    temp = (current.get("temperature_2m") if isinstance(current, dict) else None) or 15.0
    humidity = (current.get("relative_humidity_2m") if isinstance(current, dict) else None) or 50.0
    wind = (current.get("wind_speed_10m") if isinstance(current, dict) else None) or 10.0
    precip = (current.get("precipitation") if isinstance(current, dict) else None) or 0.0

    # Temperature comfort: ideal 15-25 C
    if 15 <= temp <= 25:
        temp_score = 100
        advantages.append(f"Comfortable temperature ({temp:.1f} C)")
    elif 5 <= temp < 15 or 25 < temp <= 35:
        temp_score = 60
    elif temp < -10 or temp > 42:
        temp_score = 10
        risks.append(f"Extreme temperature ({temp:.1f} C)")
    else:
        temp_score = 30

    # Humidity: ideal 30-60
    if 30 <= humidity <= 60:
        hum_score = 100
    elif humidity > 85:
        hum_score = 30
        risks.append(f"Very high humidity ({humidity:.0f}%)")
    else:
        hum_score = 60

    # Wind: lower is better for comfort
    wind_score = _clamp(100 - wind * 2)
    if wind > 30:
        risks.append(f"Strong winds ({wind:.0f} km/h)")
    elif wind < 10:
        advantages.append("Calm wind conditions")

    score = _clamp(temp_score * 0.45 + hum_score * 0.25 + wind_score * 0.30)
    return score, risks, advantages


# -- Solar potential sub-score ---------------------------------------------

@st.cache_data(ttl=1800)
def _score_solar(weather: dict, lat: float) -> Tuple[float, List[str], List[str]]:
    """Score solar energy potential (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    cloud = (current.get("cloud_cover") if isinstance(current, dict) else None)
    cloud = cloud if cloud is not None else 50.0

    # Lower latitude -> more solar, lower cloud -> more solar
    lat_factor = _clamp(100 - abs(lat) * 1.2)
    cloud_factor = _clamp(100 - cloud)
    score = _clamp(lat_factor * 0.55 + cloud_factor * 0.45)

    if cloud < 30:
        advantages.append(f"Low cloud cover ({cloud:.0f}%) -- good solar potential")
    elif cloud > 70:
        risks.append(f"High cloud cover ({cloud:.0f}%) -- reduced solar")
    if abs(lat) < 35:
        advantages.append(f"Favorable latitude ({lat:.1f}) for solar")
    elif abs(lat) > 55:
        risks.append(f"High latitude ({lat:.1f}) -- reduced annual solar hours")
    return score, risks, advantages


# -- Wind potential sub-score ----------------------------------------------

@st.cache_data(ttl=1800)
def _score_wind(weather: dict) -> Tuple[float, List[str], List[str]]:
    """Score wind energy potential (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    wind = (current.get("wind_speed_10m") if isinstance(current, dict) else None) or 0.0

    # Wind turbines need 12-25 km/h ideally
    if 12 <= wind <= 25:
        score = 95.0
        advantages.append(f"Ideal wind speed ({wind:.0f} km/h) for turbines")
    elif 8 <= wind < 12 or 25 < wind <= 40:
        score = 65.0
        advantages.append(f"Moderate wind ({wind:.0f} km/h)")
    elif wind > 40:
        score = 40.0
        risks.append(f"Excessive wind ({wind:.0f} km/h) -- structural risk")
    elif wind >= 5:
        score = 35.0
        risks.append(f"Low wind ({wind:.0f} km/h) -- marginal for energy")
    else:
        score = 15.0
        risks.append(f"Very low wind ({wind:.0f} km/h) -- not viable")
    return score, risks, advantages


# -- Water availability ---------------------------------------------------

@st.cache_data(ttl=1800)
def _score_water(water: dict) -> Tuple[float, List[str], List[str]]:
    """Score water availability (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    elements = (water if isinstance(water, dict) else {}).get("elements", [])
    springs = 0
    wells = 0
    waterways = 0
    water_bodies = 0
    for el in (elements if isinstance(elements, list) else []):
        tags = (el.get("tags", {}) if isinstance(el, dict) else {})
        if tags.get("natural") == "spring":
            springs += 1
        elif tags.get("man_made") == "water_well":
            wells += 1
        elif tags.get("waterway"):
            waterways += 1
        elif tags.get("natural") == "water":
            water_bodies += 1

    total = springs + wells + waterways + water_bodies
    score = _clamp(min(40, springs * 15 + wells * 12) + min(35, waterways * 8) + min(25, water_bodies * 10))
    if total == 0:
        score = 10.0
        risks.append("No water features detected nearby")
    else:
        advantages.append(f"Water sources: {springs} springs, {wells} wells, {waterways} waterways, {water_bodies} bodies")
    if springs > 0:
        advantages.append("Natural spring(s) present")
    return score, risks, advantages


# -- Elevation / terrain --------------------------------------------------

@st.cache_data(ttl=1800)
def _score_terrain(elevation: dict) -> Tuple[float, List[str], List[str]]:
    """Score terrain for buildability (flatter = better). 0-100."""
    risks: List[str] = []
    advantages: List[str] = []
    center_elev = (elevation if isinstance(elevation, dict) else {}).get("center_elevation", 0) or 0
    min_elev = (elevation if isinstance(elevation, dict) else {}).get("min_elevation", 0) or 0
    max_elev = (elevation if isinstance(elevation, dict) else {}).get("max_elevation", 0) or 0
    elev_range = max_elev - min_elev

    flatness = _clamp(100 - elev_range * 0.5)
    altitude_penalty = 0.0
    if center_elev > 3000:
        altitude_penalty = 30
        risks.append(f"Very high altitude ({center_elev:.0f} m)")
    elif center_elev > 2000:
        altitude_penalty = 15
    elif center_elev < 0:
        altitude_penalty = 20
        risks.append(f"Below sea level ({center_elev:.0f} m)")

    score = _clamp(flatness - altitude_penalty)
    if elev_range < 20:
        advantages.append(f"Very flat terrain (range {elev_range:.0f} m)")
    elif elev_range > 200:
        risks.append(f"Rugged terrain (elevation range {elev_range:.0f} m)")
    return score, risks, advantages


# -- Scenic / geological interest (higher range = more interesting) -------

@st.cache_data(ttl=1800)
def _score_scenic(elevation: dict) -> Tuple[float, List[str], List[str]]:
    """Score scenic and geological interest (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    center_elev = (elevation if isinstance(elevation, dict) else {}).get("center_elevation", 0) or 0
    min_elev = (elevation if isinstance(elevation, dict) else {}).get("min_elevation", 0) or 0
    max_elev = (elevation if isinstance(elevation, dict) else {}).get("max_elevation", 0) or 0
    elev_range = max_elev - min_elev

    variety = _clamp(elev_range * 0.35)
    altitude_bonus = _clamp(center_elev / 40.0)
    score = _clamp(variety * 0.7 + altitude_bonus * 0.3 + 15)

    if elev_range > 200:
        advantages.append(f"Dramatic terrain variation ({elev_range:.0f} m range)")
    elif elev_range < 10:
        risks.append("Very flat -- limited scenic variety")
    if center_elev > 1000:
        advantages.append(f"Mountain views (elevation {center_elev:.0f} m)")
    return score, risks, advantages


# -- Soil quality ---------------------------------------------------------

@st.cache_data(ttl=1800)
def _score_soil(soil: dict) -> Tuple[float, List[str], List[str]]:
    """Score soil quality for agriculture (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    lm = _build_soil_layer_map(soil)

    clay = _soil_value(lm, "clay", 10)
    sand = _soil_value(lm, "sand", 10)
    silt = _soil_value(lm, "silt", 10)
    soc = _soil_value(lm, "soc", 10)
    ph = _soil_value(lm, "phh2o", 10)
    nitrogen = _soil_value(lm, "nitrogen", 100)
    cec = _soil_value(lm, "cec", 10)

    if clay is None and sand is None:
        return 50.0, ["No soil data available for this location"], []

    # Texture score -- loamy soil is ideal (balanced clay/sand/silt)
    clay_v = clay or 0
    sand_v = sand or 0
    silt_v = silt or 0
    total_tex = clay_v + sand_v + silt_v
    if total_tex > 0:
        balance = 100 - (abs(clay_v - 25) + abs(sand_v - 40) + abs(silt_v - 35)) * 0.8
        texture_score = _clamp(balance)
    else:
        texture_score = 50.0

    # Organic carbon -- higher is better (up to ~50 g/kg)
    soc_v = soc or 0
    oc_score = _clamp(soc_v / 40.0 * 100)
    if soc_v > 25:
        advantages.append(f"Rich organic carbon ({soc_v:.1f} g/kg)")
    elif soc_v < 5:
        risks.append(f"Low organic carbon ({soc_v:.1f} g/kg)")

    # pH -- ideal 6.0-7.5
    ph_v = ph or 7.0
    if 6.0 <= ph_v <= 7.5:
        ph_score = 100.0
        advantages.append(f"Ideal soil pH ({ph_v:.1f})")
    elif 5.0 <= ph_v < 6.0 or 7.5 < ph_v <= 8.5:
        ph_score = 60.0
    else:
        ph_score = 25.0
        risks.append(f"Extreme soil pH ({ph_v:.1f})")

    # Nitrogen
    n_v = nitrogen or 0
    n_score = _clamp(n_v / 3.0 * 100)
    if n_v > 2.0:
        advantages.append(f"Good nitrogen content ({n_v:.2f} g/kg)")
    elif n_v < 0.5:
        risks.append(f"Low nitrogen ({n_v:.2f} g/kg)")

    # CEC -- higher is better (up to ~40)
    cec_v = cec or 0
    cec_score = _clamp(cec_v / 35.0 * 100)

    score = _clamp(
        texture_score * 0.25 + oc_score * 0.25 + ph_score * 0.20 + n_score * 0.15 + cec_score * 0.15
    )
    return score, risks, advantages


# -- Ecology / environment quality ----------------------------------------

@st.cache_data(ttl=1800)
def _score_ecology(infrastructure: dict, species: dict, protected: dict) -> Tuple[float, List[str], List[str]]:
    """Score environmental quality (0-100). Low infrastructure + high biodiversity = high."""
    risks: List[str] = []
    advantages: List[str] = []
    infra_els = (infrastructure if isinstance(infrastructure, dict) else {}).get("elements", [])
    industrial_count = sum(
        1 for el in infra_els
        if (el.get("tags", {}) if isinstance(el, dict) else {}).get("landuse") in ("industrial", "construction", "quarry")
    )

    # Biodiversity richness
    inat_total = (species if isinstance(species, dict) else {}).get("inat_total", 0) or 0
    gbif_unique = (species if isinstance(species, dict) else {}).get("gbif_unique_species", 0) or 0
    bio_score = _clamp((inat_total / 100.0) * 30 + (gbif_unique / 50.0) * 30)

    # Low pollution
    pollution_score = _clamp(100 - industrial_count * 12)

    # Protected areas bonus
    prot_els = (protected if isinstance(protected, dict) else {}).get("elements", [])
    prot_bonus = min(30, len(prot_els) * 10)

    score = _clamp(bio_score * 0.4 + pollution_score * 0.35 + prot_bonus * 0.25 + 10)
    if inat_total > 50:
        advantages.append(f"Rich biodiversity ({inat_total} iNaturalist observations)")
    if gbif_unique > 20:
        advantages.append(f"{gbif_unique} unique GBIF species recorded")
    if len(prot_els) > 0:
        advantages.append(f"{len(prot_els)} protected area(s) nearby")
    if industrial_count > 3:
        risks.append(f"{industrial_count} industrial zones -- potential pollution")
    elif industrial_count == 0:
        advantages.append("No industrial pollution sources detected")
    return score, risks, advantages


# -- Biodiversity richness (for conservation / research) ------------------

@st.cache_data(ttl=1800)
def _score_biodiversity(species: dict) -> Tuple[float, List[str], List[str]]:
    """Score biodiversity richness specifically (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    inat_total = (species if isinstance(species, dict) else {}).get("inat_total", 0) or 0
    gbif_unique = (species if isinstance(species, dict) else {}).get("gbif_unique_species", 0) or 0
    kingdom_counts = (species if isinstance(species, dict) else {}).get("kingdom_counts", {})
    kingdom_counts = kingdom_counts if isinstance(kingdom_counts, dict) else {}
    num_kingdoms = len([k for k, v in kingdom_counts.items() if (v or 0) > 0])

    obs_score = _clamp(inat_total / 150.0 * 50)
    species_score = _clamp(gbif_unique / 80.0 * 30)
    diversity_score = _clamp(num_kingdoms / 6.0 * 20)
    score = _clamp(obs_score + species_score + diversity_score)

    if inat_total > 100:
        advantages.append(f"High observation count ({inat_total})")
    elif inat_total < 10:
        risks.append(f"Very few observations ({inat_total}) -- limited data or low biodiversity")
    if gbif_unique > 50:
        advantages.append(f"High species diversity ({gbif_unique} unique)")
    if num_kingdoms >= 4:
        advantages.append(f"Diverse taxonomic coverage ({num_kingdoms} kingdoms)")
    return score, risks, advantages


# -- Existing study data (for research) -----------------------------------

@st.cache_data(ttl=1800)
def _score_existing_data(species: dict, protected: dict) -> Tuple[float, List[str], List[str]]:
    """Score how much existing scientific data is available (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    inat_total = (species if isinstance(species, dict) else {}).get("inat_total", 0) or 0
    gbif_total = (species if isinstance(species, dict) else {}).get("gbif_total", 0) or 0
    prot_els = (protected if isinstance(protected, dict) else {}).get("elements", [])

    data_score = _clamp((inat_total / 100.0) * 35 + (gbif_total / 200.0) * 35 + len(prot_els) * 10)
    if inat_total + gbif_total > 200:
        advantages.append("Extensive existing observation data")
    elif inat_total + gbif_total < 10:
        risks.append("Very limited prior studies -- frontier area")
    if len(prot_els) > 0:
        advantages.append("Protected area status may provide research infrastructure")
    return data_score, risks, advantages


# -- Protected status (for conservation) ----------------------------------

@st.cache_data(ttl=1800)
def _score_protected(protected: dict) -> Tuple[float, List[str], List[str]]:
    """Score existing protection level (0-100)."""
    risks: List[str] = []
    advantages: List[str] = []
    prot_els = (protected if isinstance(protected, dict) else {}).get("elements", [])
    count = len(prot_els)

    score = _clamp(count * 25 + 10) if count > 0 else 15.0
    if count >= 3:
        advantages.append(f"Strong protection: {count} protected areas/reserves")
    elif count == 0:
        risks.append("No existing protection -- area may be vulnerable")
    else:
        advantages.append(f"{count} protected area(s) present")
    return score, risks, advantages


# -- Threat level (for conservation -- inverse: low threat = high score) ---

@st.cache_data(ttl=1800)
def _score_threats(earthquakes: dict, infrastructure: dict) -> Tuple[float, List[str], List[str]]:
    """Score threat level inversely (0-100): low anthropogenic threat = high score."""
    risks: List[str] = []
    advantages: List[str] = []
    infra_els = (infrastructure if isinstance(infrastructure, dict) else {}).get("elements", [])
    building_count = sum(
        1 for el in infra_els if "building" in (el.get("tags", {}) if isinstance(el, dict) else {})
    )
    road_count = sum(
        1 for el in infra_els if "highway" in (el.get("tags", {}) if isinstance(el, dict) else {})
    )

    anthropogenic_pressure = _clamp(building_count / 80.0 * 50 + road_count / 40.0 * 50)
    score = _clamp(100 - anthropogenic_pressure)

    if building_count > 50:
        risks.append(f"High urban pressure ({building_count} buildings)")
    elif building_count < 5:
        advantages.append("Low anthropogenic footprint")
    if road_count > 20:
        risks.append(f"Dense road network fragments habitat ({road_count} segments)")
    return score, risks, advantages


# ---------------------------------------------------------------------------
# Master scorer -- routes criterion to scorer
# ---------------------------------------------------------------------------

def _evaluate_criterion(
    source: str,
    data: Dict[str, Any],
    lat: float,
    lon: float,
) -> Tuple[float, List[str], List[str]]:
    """Route a criterion source tag to its scorer function. Returns (score, risks, advantages)."""
    if source == "hazards":
        return _score_hazards(data["earthquakes"], data["water"], data["elevation"], data["infrastructure"])
    elif source == "infrastructure":
        return _score_infrastructure(data["infrastructure"])
    elif source == "infrastructure_roads":
        return _score_roads(data["infrastructure"])
    elif source == "weather":
        return _score_weather(data["weather"])
    elif source == "weather_solar":
        return _score_solar(data["weather"], lat)
    elif source == "weather_wind":
        return _score_wind(data["weather"])
    elif source == "water":
        return _score_water(data["water"])
    elif source == "elevation":
        return _score_terrain(data["elevation"])
    elif source == "soil":
        return _score_soil(data["soil"])
    elif source == "ecology":
        return _score_ecology(data["infrastructure"], data["species"], data["protected"])
    elif source == "biodiversity":
        return _score_biodiversity(data["species"])
    elif source == "biodiversity_data":
        return _score_existing_data(data["species"], data["protected"])
    elif source == "protected":
        return _score_protected(data["protected"])
    elif source == "threats":
        return _score_threats(data["earthquakes"], data["infrastructure"])
    else:
        return 50.0, [], []


# ---------------------------------------------------------------------------
# Evaluate a full scenario
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def _evaluate_scenario(
    scenario_key: str,
    lat: float,
    lon: float,
    data_soil: dict,
    data_weather: dict,
    data_water: dict,
    data_elevation: dict,
    data_infrastructure: dict,
    data_protected: dict,
    data_species: dict,
    data_earthquakes: dict,
) -> Dict[str, Any]:
    """Evaluate a single scenario and return results dict."""
    scenario = DECISION_SCENARIOS[scenario_key]
    data_bundle: Dict[str, Any] = {
        "soil": data_soil,
        "weather": data_weather,
        "water": data_water,
        "elevation": data_elevation,
        "infrastructure": data_infrastructure,
        "protected": data_protected,
        "species": data_species,
        "earthquakes": data_earthquakes,
    }

    criteria_results: Dict[str, dict] = {}
    weighted_total = 0.0
    all_risks: List[str] = []
    all_advantages: List[str] = []

    for crit_key, crit_def in scenario["criteria"].items():
        score, risks, advantages = _evaluate_criterion(crit_def["source"], data_bundle, lat, lon)
        weight = crit_def["weight"]
        weighted_total += score * weight
        criteria_results[crit_key] = {
            "label": crit_def.get("label", crit_key),
            "score": round(score, 1),
            "weight": weight,
            "weighted": round(score * weight, 1),
            "risks": risks,
            "advantages": advantages,
        }
        all_risks.extend(risks)
        all_advantages.extend(advantages)

    overall = round(_clamp(weighted_total), 1)
    if overall >= VERDICT_GO:
        verdict = "GO"
    elif overall >= VERDICT_CAUTION:
        verdict = "CAUTION"
    else:
        verdict = "NO-GO"

    # De-duplicate
    seen_r: set = set()
    unique_risks = [r for r in all_risks if not (r in seen_r or seen_r.add(r))]  # type: ignore[func-returns-value]
    seen_a: set = set()
    unique_adv = [a for a in all_advantages if not (a in seen_a or seen_a.add(a))]  # type: ignore[func-returns-value]

    return {
        "scenario_key": scenario_key,
        "name": scenario["name"],
        "icon": scenario.get("icon", ""),
        "overall_score": overall,
        "verdict": verdict,
        "criteria": criteria_results,
        "risks": unique_risks[:8],
        "advantages": unique_adv[:8],
    }


# ---------------------------------------------------------------------------
# Plotly charts
# ---------------------------------------------------------------------------

def _build_criteria_bar(result: dict) -> go.Figure:
    """Build a horizontal bar chart for criteria breakdown."""
    labels = []
    scores = []
    colors = []
    for crit in result["criteria"].values():
        labels.append(crit["label"])
        s = crit["score"]
        scores.append(s)
        if s >= VERDICT_GO:
            colors.append("#22c55e")
        elif s >= VERDICT_CAUTION:
            colors.append("#f59e0b")
        else:
            colors.append("#ef4444")

    fig = go.Figure(go.Bar(
        x=scores,
        y=labels,
        orientation="h",
        marker_color=colors,
        text=[f"{s:.0f}" for s in scores],
        textposition="auto",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 100], title="Score"),
        yaxis=dict(autorange="reversed"),
        height=max(200, len(labels) * 45),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def _build_radar_chart(results: List[dict]) -> go.Figure:
    """Build a comparative radar chart overlaying multiple scenarios."""
    fig = go.Figure()
    palette = ["#22c55e", "#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316"]
    for idx, result in enumerate(results):
        criteria = result["criteria"]
        labels = [c["label"] for c in criteria.values()]
        values = [c["score"] for c in criteria.values()]
        # Close the polygon
        labels_closed = labels + [labels[0]]
        values_closed = values + [values[0]]
        color = palette[idx % len(palette)]
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=labels_closed,
            fill="toself",
            name=result["name"],
            line_color=color,
            fillcolor=color.replace(")", ",0.15)").replace("rgb", "rgba") if color.startswith("rgb") else color + "26",
            opacity=0.8,
        ))

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100]),
        ),
        showlegend=True,
        height=500,
        margin=dict(l=40, r=40, t=30, b=30),
    )
    return fig


def _build_comparison_bar(results: List[dict]) -> go.Figure:
    """Build grouped bar chart comparing overall scores."""
    names = [r["name"] for r in results]
    scores = [r["overall_score"] for r in results]
    colors = [VERDICT_COLORS[r["verdict"]] for r in results]

    fig = go.Figure(go.Bar(
        x=names,
        y=scores,
        marker_color=colors,
        text=[f"{s:.0f}" for s in scores],
        textposition="auto",
    ))
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(range=[0, 100], title="Overall Score"),
        height=350,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


# ---------------------------------------------------------------------------
# Gauge widget (HTML/CSS)
# ---------------------------------------------------------------------------

def _render_gauge_html(score: float, verdict: str) -> str:
    """Return HTML for a circular gauge showing overall score."""
    color = VERDICT_COLORS.get(verdict, "#64748b")
    pct = score / 100.0
    dash = 283 * pct
    gap = 283 - dash
    return f"""
    <div style="display:flex;align-items:center;gap:18px;">
      <svg width="110" height="110" viewBox="0 0 110 110">
        <circle cx="55" cy="55" r="45" fill="none" stroke="#334155" stroke-width="10"/>
        <circle cx="55" cy="55" r="45" fill="none" stroke="{color}" stroke-width="10"
                stroke-dasharray="{dash:.1f} {gap:.1f}"
                stroke-linecap="round" transform="rotate(-90 55 55)"/>
        <text x="55" y="55" text-anchor="middle" dominant-baseline="central"
              fill="{color}" font-size="22" font-weight="bold">{score:.0f}</text>
      </svg>
      <div>
        <span style="font-size:28px;font-weight:bold;color:{color};">{verdict}</span><br/>
        <span style="color:#94a3b8;font-size:14px;">Overall Suitability</span>
      </div>
    </div>
    """


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_decision_matrix_tab() -> None:
    """Render the Decision Matrix AI tab in Streamlit."""
    st.markdown(
        "<h2 style='text-align:center;'>Decision Matrix AI</h2>"
        "<p style='text-align:center;color:#94a3b8;'>"
        "Multi-criteria decision support -- evaluate any location for residence, "
        "agriculture, commercial, conservation, tourism, energy, shelter, or research.</p>",
        unsafe_allow_html=True,
    )

    # ── Location selector ──────────────────────────────────────────────
    col_loc1, col_loc2, col_loc3 = st.columns([2, 1, 1])
    with col_loc1:
        preset_name = st.selectbox(
            "Location preset",
            list(ANALYSIS_PRESETS.keys()),
            key="dm_preset",
        )
    p = ANALYSIS_PRESETS.get(preset_name)
    with col_loc2:
        lat = st.number_input(
            "Latitude",
            value=p.get("lat", 41.90) if p else 41.90,
            format="%.4f",
            key="dm_lat",
        )
    with col_loc3:
        lon = st.number_input(
            "Longitude",
            value=p.get("lon", 12.50) if p else 12.50,
            format="%.4f",
            key="dm_lon",
        )

    st.markdown("---")

    # ── Scenario multi-select ──────────────────────────────────────────
    st.subheader("Select Decision Scenarios")
    scenario_cols = st.columns(4)
    selected_scenarios: List[str] = []
    scenario_keys = list(DECISION_SCENARIOS.keys())
    for idx, key in enumerate(scenario_keys):
        sc = DECISION_SCENARIOS[key]
        with scenario_cols[idx % 4]:
            if st.checkbox(
                f"{sc.get('icon', '')} {sc['name']}",
                key=f"dm_sc_{key}",
            ):
                selected_scenarios.append(key)

    if not selected_scenarios:
        st.info("Select one or more scenarios above, then click **Evaluate Decision**.")

    st.markdown("---")

    # ── Evaluate button ────────────────────────────────────────────────
    if st.button("Evaluate Decision", type="primary", disabled=len(selected_scenarios) == 0, key="dm_eval_btn"):
        with st.spinner("Collecting location data from 10+ sources..."):
            raw_data = _collect_location_data(lat, lon)

        results: List[dict] = []
        progress = st.progress(0, text="Evaluating scenarios...")
        for i, sc_key in enumerate(selected_scenarios):
            progress.progress(
                (i + 1) / len(selected_scenarios),
                text=f"Evaluating: {DECISION_SCENARIOS[sc_key]['name']}...",
            )
            result = _evaluate_scenario(
                sc_key,
                lat,
                lon,
                raw_data["soil"],
                raw_data["weather"],
                raw_data["water"],
                raw_data["elevation"],
                raw_data["infrastructure"],
                raw_data["protected"],
                raw_data["species"],
                raw_data["earthquakes"],
            )
            results.append(result)

        progress.empty()

        # ── Render results ─────────────────────────────────────────────
        st.markdown(
            f"<h3 style='text-align:center;'>Results for ({lat:.4f}, {lon:.4f})</h3>",
            unsafe_allow_html=True,
        )

        # Comparison bar if multiple
        if len(results) > 1:
            st.markdown("#### Scenario Comparison")
            st.plotly_chart(_build_comparison_bar(results, key="decmat_pchart1"), width="stretch")
            st.plotly_chart(_build_radar_chart(results, key="decmat_pchart2"), width="stretch")

        # Individual scenario details
        for result in results:
            verdict = result["verdict"]
            v_color = VERDICT_COLORS[verdict]
            icon = result.get("icon", "")

            st.markdown(
                f"<div style='border-left:4px solid {v_color};padding:8px 16px;"
                f"margin:16px 0 8px 0;background:rgba(0,0,0,0.2);border-radius:6px;'>"
                f"<h3 style='margin:0;'>{icon} {result['name']}</h3></div>",
                unsafe_allow_html=True,
            )

            col_gauge, col_detail = st.columns([1, 2])
            with col_gauge:
                st.markdown(_render_gauge_html(result["overall_score"], verdict), unsafe_allow_html=True)

            with col_detail:
                # Criteria breakdown table
                header = "| Criterion | Score | Weight | Weighted |"
                sep = "|---|---|---|---|"
                rows_md = [header, sep]
                for crit in result["criteria"].values():
                    s = crit["score"]
                    if s >= VERDICT_GO:
                        dot = "\U0001f7e2"
                    elif s >= VERDICT_CAUTION:
                        dot = "\U0001f7e1"
                    else:
                        dot = "\U0001f534"
                    rows_md.append(
                        f"| {dot} {crit['label']} | {s:.0f} | {crit['weight']:.0%} | {crit['weighted']:.1f} |"
                    )
                st.markdown("\n".join(rows_md), unsafe_allow_html=True)

            # Criteria bar chart
            st.plotly_chart(_build_criteria_bar(result, key="decmat_pchart3"), width="stretch")

            # Risks & advantages
            col_risk, col_adv = st.columns(2)
            with col_risk:
                st.markdown(
                    "<div style='background:rgba(239,68,68,0.08);padding:10px;border-radius:8px;'>"
                    "<strong style='color:#ef4444;'>Key Risks</strong></div>",
                    unsafe_allow_html=True,
                )
                if result["risks"]:
                    for r in result["risks"]:
                        st.markdown(f"- {r}")
                else:
                    st.markdown("_No significant risks identified._")

            with col_adv:
                st.markdown(
                    "<div style='background:rgba(34,197,94,0.08);padding:10px;border-radius:8px;'>"
                    "<strong style='color:#22c55e;'>Key Advantages</strong></div>",
                    unsafe_allow_html=True,
                )
                if result["advantages"]:
                    for a in result["advantages"]:
                        st.markdown(f"- {a}")
                else:
                    st.markdown("_No notable advantages detected._")

            st.markdown("---")

        # ── Final recommendation summary ───────────────────────────────
        st.markdown(
            "<h3 style='text-align:center;'>Final Recommendation Summary</h3>",
            unsafe_allow_html=True,
        )
        summary_cols = st.columns(min(len(results), 4))
        for idx, result in enumerate(results):
            v = result["verdict"]
            c = VERDICT_COLORS[v]
            with summary_cols[idx % min(len(results), 4)]:
                st.markdown(
                    f"<div style='text-align:center;padding:16px;border:2px solid {c};"
                    f"border-radius:12px;margin:4px;'>"
                    f"<div style='font-size:32px;'>{result.get('icon', '')}</div>"
                    f"<div style='font-size:14px;color:#94a3b8;'>{result['name']}</div>"
                    f"<div style='font-size:36px;font-weight:bold;color:{c};'>{result['overall_score']:.0f}</div>"
                    f"<div style='font-size:18px;font-weight:bold;color:{c};'>{v}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

        # Best use recommendation
        if results:
            best = max(results, key=lambda r: r["overall_score"])
            worst = min(results, key=lambda r: r["overall_score"])
            st.markdown(
                f"<div style='text-align:center;margin-top:16px;padding:14px;"
                f"background:rgba(34,197,94,0.06);border-radius:10px;'>"
                f"<strong>Best use:</strong> {best.get('icon', '')} {best['name']} "
                f"(score {best['overall_score']:.0f})",
                unsafe_allow_html=True,
            )
            if len(results) > 1 and worst["overall_score"] < VERDICT_CAUTION:
                st.markdown(
                    f"<div style='text-align:center;padding:10px;"
                    f"background:rgba(239,68,68,0.06);border-radius:10px;'>"
                    f"<strong>Least suitable:</strong> {worst.get('icon', '')} {worst['name']} "
                    f"(score {worst['overall_score']:.0f})</div>",
                    unsafe_allow_html=True,
                )
