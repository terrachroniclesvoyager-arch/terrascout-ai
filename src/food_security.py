"""
Food Security AI module for TerraScout AI.
Provides comprehensive agricultural capacity and food system assessment
using multi-source free data:
  - ISRIC SoilGrids (soil fertility: SOC, nitrogen, pH, CEC, clay)
  - Open-Meteo (growing season, precipitation, temperature)
  - Overpass API (farmland, orchards, markets, food infrastructure)
  - iNaturalist (crop/plant species indicators)
  - Open Topo Data (arable terrain assessment)
All free, no API key required.
"""

import math
import logging

import numpy as np
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_biodiversity,
    fetch_elevation_grid,
)

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

DIMENSION_COLORS = {
    "Soil Fertility": "#10b981",
    "Growing Conditions": "#f59e0b",
    "Arable Land": "#8b5cf6",
    "Food Infrastructure": "#06b6d4",
    "Water for Agriculture": "#3b82f6",
    "Crop Diversity": "#ec4899",
}

MONTH_LABELS = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

# Overpass food-infrastructure tags used for scoring
FOOD_INFRA_TAGS = {
    "shop=supermarket": "Supermarket",
    "shop=convenience": "Convenience Store",
    "shop=greengrocer": "Greengrocer",
    "shop=bakery": "Bakery",
    "shop=butcher": "Butcher",
    "shop=farm": "Farm Shop",
    "amenity=marketplace": "Market",
    "amenity=restaurant": "Restaurant",
    "amenity=fast_food": "Fast Food",
    "building=farm": "Farm Building",
    "building=barn": "Barn",
    "building=silo": "Silo",
    "building=greenhouse": "Greenhouse",
    "man_made=silo": "Silo",
    "man_made=storage_tank": "Storage Tank",
    "landuse=farmland": "Farmland",
    "landuse=orchard": "Orchard",
    "landuse=vineyard": "Vineyard",
    "landuse=meadow": "Meadow/Pasture",
    "landuse=greenhouse_horticulture": "Greenhouse Hort.",
}


# =============================================================================
# HELPERS
# =============================================================================

def _clamp(v, lo=0.0, hi=100.0):
    """Clamp a numeric value between lo and hi."""
    return max(lo, min(hi, float(v)))


def _range_score(value, lo, hi):
    """Return 0-100 score for how well *value* fits inside [lo, hi]."""
    if value is None:
        return 50.0
    if lo <= value <= hi:
        return 100.0
    if value < lo:
        dist = lo - value
        span = hi - lo if hi > lo else 1
        return max(0.0, 100.0 - (dist / span) * 100.0)
    dist = value - hi
    span = hi - lo if hi > lo else 1
    return max(0.0, 100.0 - (dist / span) * 100.0)


def _extract_soil_value(soil_data, name, div=10):
    """Extract a soil property value from SoilGrids response, top layer."""
    props = (soil_data if isinstance(soil_data, dict) else {}).get("properties", {})
    layers = props.get("layers", [])
    for layer in (layers if isinstance(layers, list) else []):
        if isinstance(layer, dict) and layer.get("name") == name:
            depths = layer.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
    return None


def _extract_soil_profile(soil_data, name, div=10):
    """Extract all depth values for a soil property, returns list of (depth_label, value)."""
    props = (soil_data if isinstance(soil_data, dict) else {}).get("properties", {})
    layers = props.get("layers", [])
    result = []
    for layer in (layers if isinstance(layers, list) else []):
        if isinstance(layer, dict) and layer.get("name") == name:
            for depth_entry in layer.get("depths", []):
                label = depth_entry.get("label", "?")
                val_raw = depth_entry.get("values", {}).get("mean")
                val = val_raw / div if val_raw is not None else None
                result.append((label, val))
    return result


# =============================================================================
# FOOD INFRASTRUCTURE QUERY (Overpass)
# =============================================================================

@st.cache_data(ttl=1800)
def _fetch_food_infrastructure(lat: float, lon: float, radius: int = 5000) -> dict:
    """Fetch food-related infrastructure from Overpass API."""
    from src.overpass_client import query_overpass
    query = f"""[out:json][timeout:25];
(
  node["shop"~"supermarket|convenience|greengrocer|bakery|butcher|farm"](around:{radius},{lat},{lon});
  way["shop"~"supermarket|convenience|greengrocer|bakery|butcher|farm"](around:{radius},{lat},{lon});
  node["amenity"="marketplace"](around:{radius},{lat},{lon});
  way["amenity"="marketplace"](around:{radius},{lat},{lon});
  node["amenity"~"restaurant|fast_food"](around:{radius},{lat},{lon});
  way["amenity"~"restaurant|fast_food"](around:{radius},{lat},{lon});
  way["building"~"farm|barn|silo|greenhouse"](around:{radius},{lat},{lon});
  node["man_made"~"silo|storage_tank"](around:{radius},{lat},{lon});
  way["landuse"~"farmland|orchard|vineyard|meadow|greenhouse_horticulture"](around:{radius},{lat},{lon});
);
out center;"""
    result = query_overpass(query)
    if result is None or "_error" in result:
        return {"elements": []}
    return result


# =============================================================================
# SCORING FUNCTIONS
# =============================================================================

def _score_soil_fertility(soil_data):
    """
    Score soil fertility 0-100.
    SOC>20 g/kg = high, N>1 g/kg = good, pH 6-7 = ideal, CEC>20 = excellent.
    """
    soc = _extract_soil_value(soil_data, "soc", 10)
    nitrogen = _extract_soil_value(soil_data, "nitrogen", 100)
    ph = _extract_soil_value(soil_data, "phh2o", 10)
    cec = _extract_soil_value(soil_data, "cec", 10)
    clay = _extract_soil_value(soil_data, "clay", 10)

    soc_val = soc if soc is not None else 0
    nit_val = nitrogen if nitrogen is not None else 0
    ph_val = ph if ph is not None else 6.5
    cec_val = cec if cec is not None else 0
    clay_val = clay if clay is not None else 0

    # SOC subscore: >20 g/kg = 30 pts max
    soc_score = min(soc_val / 20.0, 1.0) * 30.0

    # Nitrogen subscore: >1 g/kg = 25 pts max
    nit_score = min(nit_val / 1.0, 1.0) * 25.0

    # pH subscore: 6-7 ideal = 25 pts max
    ph_score = _range_score(ph_val, 6.0, 7.0) * 0.25

    # CEC subscore: >20 cmol/kg = 20 pts max
    cec_score = min(cec_val / 20.0, 1.0) * 20.0

    score = _clamp(soc_score + nit_score + ph_score + cec_score)

    details = {
        "soc": round(soc_val, 1),
        "nitrogen": round(nit_val, 2),
        "ph": round(ph_val, 1),
        "cec": round(cec_val, 1),
        "clay": round(clay_val, 1),
        "soc_score": round(soc_score, 1),
        "nitrogen_score": round(nit_score, 1),
        "ph_score": round(ph_score, 1),
        "cec_score": round(cec_score, 1),
    }
    return round(score, 1), details


def _score_growing_conditions(weather_data):
    """
    Score growing conditions 0-100.
    Frost-free days from min temps, GDD from sum(max(0, temp-10)).
    """
    current = (weather_data if isinstance(weather_data, dict) else {}).get("current", {})
    daily = (weather_data if isinstance(weather_data, dict) else {}).get("daily", {})

    raw_max = daily.get("temperature_2m_max", [])
    raw_min = daily.get("temperature_2m_min", [])
    raw_precip = daily.get("precipitation_sum", [])

    daily_maxs = [v for v in raw_max if v is not None]
    daily_mins = [v for v in raw_min if v is not None]
    daily_precips = [v for v in raw_precip if v is not None]

    temp_now = current.get("temperature_2m") or 15.0
    avg_temp = (
        (sum(daily_maxs) + sum(daily_mins)) / (len(daily_maxs) + len(daily_mins))
        if (daily_maxs or daily_mins)
        else temp_now
    )
    max_temp = max(daily_maxs) if daily_maxs else (avg_temp + 5)
    min_temp = min(daily_mins) if daily_mins else (avg_temp - 5)

    precip_7d = sum(daily_precips) if daily_precips else 0.0
    annual_precip_est = precip_7d * (365.0 / 7.0) if precip_7d > 0 else 500.0

    # Frost-free days estimate: higher min temp = more frost-free days
    # Approximate: if min_temp > 0 => frost_free_pct ~ min_temp * 3 + 40
    if min_temp > 0:
        frost_free_pct = _clamp(min_temp * 3.0 + 40.0, 0, 100)
    elif min_temp > -5:
        frost_free_pct = _clamp(30.0 + min_temp * 4.0, 0, 100)
    else:
        frost_free_pct = _clamp(10.0 + max(0, min_temp + 10) * 2.0, 0, 100)

    frost_free_days_est = int(frost_free_pct / 100.0 * 365)

    # Growing Degree Days proxy: sum(max(0, daily_max - 10))
    if daily_maxs:
        gdd_7d = sum(max(0, t - 10.0) for t in daily_maxs)
        gdd_annual_est = gdd_7d * (365.0 / len(daily_maxs))
    else:
        gdd_annual_est = max(0, (avg_temp - 10.0)) * 365.0

    # Temperature range score: moderate range (10-25C avg) is ideal
    temp_range_score = _range_score(avg_temp, 10.0, 25.0)

    # Precipitation score: 400-1200mm is generally good for diverse agriculture
    precip_score = _range_score(annual_precip_est, 400.0, 1200.0)

    # Frost-free subscore (25 pts)
    frost_score = (frost_free_pct / 100.0) * 25.0

    # GDD subscore (25 pts): 2000+ GDD is excellent
    gdd_score = min(gdd_annual_est / 2000.0, 1.0) * 25.0

    # Temperature range subscore (25 pts)
    temp_sub = temp_range_score * 0.25

    # Precipitation subscore (25 pts)
    precip_sub = precip_score * 0.25

    score = _clamp(frost_score + gdd_score + temp_sub + precip_sub)

    details = {
        "avg_temp": round(avg_temp, 1),
        "min_temp": round(min_temp, 1),
        "max_temp": round(max_temp, 1),
        "frost_free_days": frost_free_days_est,
        "gdd_annual_est": round(gdd_annual_est, 0),
        "annual_precip_est": round(annual_precip_est, 0),
        "temp_now": round(temp_now, 1),
    }
    return round(score, 1), details


def _score_arable_land(elevation_data, landuse_data):
    """
    Score arable land potential 0-100.
    Flat terrain + farmland area from Overpass tags + elevation suitability.
    """
    center_elev = (elevation_data or {}).get("center_elevation", 0) or 0
    min_elev = (elevation_data or {}).get("min_elevation", 0) or 0
    max_elev = (elevation_data or {}).get("max_elevation", 0) or 0
    elev_range = max_elev - min_elev

    # Count farmland-related features
    farmland_count = 0
    orchard_count = 0
    vineyard_count = 0
    meadow_count = 0
    for el in (landuse_data or {}).get("elements", []):
        tags = el.get("tags", {})
        lu = tags.get("landuse", "")
        if lu == "farmland":
            farmland_count += 1
        elif lu == "orchard":
            orchard_count += 1
        elif lu == "vineyard":
            vineyard_count += 1
        elif lu in ("meadow", "grass"):
            meadow_count += 1

    total_agri = farmland_count + orchard_count + vineyard_count + meadow_count

    # Flatness subscore (40 pts): lower elevation range = flatter
    if elev_range < 10:
        flatness = 40.0
    elif elev_range < 50:
        flatness = 35.0
    elif elev_range < 100:
        flatness = 25.0
    elif elev_range < 300:
        flatness = 15.0
    else:
        flatness = max(2.0, 40.0 - elev_range / 20.0)

    # Existing farmland subscore (40 pts)
    farmland_score = min(total_agri / 15.0, 1.0) * 40.0

    # Elevation suitability (20 pts): 0-800m is ideal for most crops
    elev_score = _range_score(center_elev, 0, 800) * 0.20

    score = _clamp(flatness + farmland_score + elev_score)

    details = {
        "elevation": round(center_elev, 0),
        "elev_range": round(elev_range, 0),
        "farmland_areas": farmland_count,
        "orchards": orchard_count,
        "vineyards": vineyard_count,
        "meadows": meadow_count,
        "total_agricultural": total_agri,
    }
    return round(score, 1), details


def _score_food_infrastructure(food_infra_data):
    """
    Score food infrastructure 0-100.
    Shops, markets, restaurants, storage, farms from Overpass.
    """
    shops = 0
    markets = 0
    restaurants = 0
    storage = 0
    farms = 0
    greenhouses = 0

    for el in (food_infra_data or {}).get("elements", []):
        tags = el.get("tags", {})
        shop = tags.get("shop", "")
        amenity = tags.get("amenity", "")
        building = tags.get("building", "")
        man_made = tags.get("man_made", "")

        if shop in ("supermarket", "convenience", "greengrocer", "bakery", "butcher", "farm"):
            shops += 1
        if amenity == "marketplace":
            markets += 1
        if amenity in ("restaurant", "fast_food"):
            restaurants += 1
        if building in ("silo", "barn") or man_made in ("silo", "storage_tank"):
            storage += 1
        if building == "farm":
            farms += 1
        if building == "greenhouse":
            greenhouses += 1

    total = shops + markets + restaurants + storage + farms + greenhouses

    # Retail/shops subscore (25 pts)
    shop_score = min(shops / 10.0, 1.0) * 25.0

    # Markets subscore (20 pts)
    market_score = min(markets / 3.0, 1.0) * 20.0

    # Storage/processing subscore (20 pts)
    storage_score = min(storage / 5.0, 1.0) * 20.0

    # Production (farms/greenhouses) subscore (20 pts)
    production_score = min((farms + greenhouses) / 5.0, 1.0) * 20.0

    # Distribution (restaurants) subscore (15 pts)
    dist_score = min(restaurants / 15.0, 1.0) * 15.0

    score = _clamp(shop_score + market_score + storage_score + production_score + dist_score)

    details = {
        "shops": shops,
        "markets": markets,
        "restaurants": restaurants,
        "storage_facilities": storage,
        "farms": farms,
        "greenhouses": greenhouses,
        "total": total,
    }
    return round(score, 1), details


def _score_water_for_agriculture(water_data, weather_data):
    """
    Score water for agriculture 0-100.
    Irrigation sources, rivers, reservoirs, rainfall reliability.
    """
    water_elements = (water_data if isinstance(water_data, dict) else {}).get("elements", [])

    springs = 0
    wells = 0
    rivers = 0
    reservoirs = 0
    water_bodies = 0

    for el in water_elements:
        tags = el.get("tags", {})
        natural = tags.get("natural", "")
        man_made = tags.get("man_made", "")
        waterway = tags.get("waterway", "")
        water_type = tags.get("water", "")

        if natural == "spring":
            springs += 1
        if man_made == "water_well":
            wells += 1
        if waterway in ("river", "stream", "canal", "ditch", "drain"):
            rivers += 1
        if water_type == "reservoir" or man_made == "reservoir_covered":
            reservoirs += 1
        if natural == "water":
            water_bodies += 1

    # Precipitation from weather
    daily = (weather_data if isinstance(weather_data, dict) else {}).get("daily", {})
    raw_precip = daily.get("precipitation_sum", [])
    daily_precips = [v for v in raw_precip if v is not None]
    precip_7d = sum(daily_precips) if daily_precips else 0.0
    annual_precip_est = precip_7d * (365.0 / 7.0) if precip_7d > 0 else 500.0

    # Irrigation sources subscore (25 pts)
    irrigation_score = min((springs + wells) / 5.0, 1.0) * 25.0

    # Rivers/waterways subscore (25 pts)
    river_score = min(rivers / 8.0, 1.0) * 25.0

    # Reservoirs/water bodies subscore (20 pts)
    reservoir_score = min((reservoirs + water_bodies) / 5.0, 1.0) * 20.0

    # Rainfall reliability subscore (30 pts): >600mm annual = good
    if annual_precip_est >= 600:
        rain_score = 30.0
    elif annual_precip_est >= 400:
        rain_score = 20.0
    elif annual_precip_est >= 200:
        rain_score = 10.0
    else:
        rain_score = max(0.0, annual_precip_est / 200.0 * 10.0)

    score = _clamp(irrigation_score + river_score + reservoir_score + rain_score)

    details = {
        "springs": springs,
        "wells": wells,
        "rivers_streams": rivers,
        "reservoirs": reservoirs,
        "water_bodies": water_bodies,
        "annual_precip_est": round(annual_precip_est, 0),
        "total_water_features": len(water_elements),
    }
    return round(score, 1), details


def _score_crop_diversity(biodiversity_data, weather_data, soil_data):
    """
    Score crop diversity potential 0-100.
    Species variety, multi-cropping potential, climate-crop match.
    """
    results = (biodiversity_data if isinstance(biodiversity_data, dict) else {}).get("results", [])
    total_obs = (biodiversity_data if isinstance(biodiversity_data, dict) else {}).get("total_results", 0) or 0

    # Count plant species specifically
    plant_species = set()
    plant_obs = 0
    kingdom_set = set()
    for obs in results:
        taxon = obs.get("taxon")
        if not taxon:
            continue
        kingdom = taxon.get("iconic_taxon_name", "Other")
        kingdom_set.add(kingdom)
        if kingdom == "Plantae":
            sp = taxon.get("name", "")
            if sp:
                plant_species.add(sp)
                plant_obs += 1

    unique_plant_count = len(plant_species)

    # Climate-crop match: moderate climate supports more crop variety
    daily = (weather_data if isinstance(weather_data, dict) else {}).get("daily", {})
    raw_max = daily.get("temperature_2m_max", [])
    raw_min = daily.get("temperature_2m_min", [])
    daily_maxs = [v for v in raw_max if v is not None]
    daily_mins = [v for v in raw_min if v is not None]

    if daily_maxs and daily_mins:
        avg_temp = (sum(daily_maxs) + sum(daily_mins)) / (len(daily_maxs) + len(daily_mins))
        temp_range = max(daily_maxs) - min(daily_mins)
    else:
        current = (weather_data if isinstance(weather_data, dict) else {}).get("current", {})
        avg_temp = current.get("temperature_2m") or 15.0
        temp_range = 15.0

    # Soil pH diversity potential
    ph = _extract_soil_value(soil_data, "phh2o", 10)
    ph_val = ph if ph is not None else 6.5

    # Species variety subscore (30 pts)
    species_score = min(unique_plant_count / 20.0, 1.0) * 30.0

    # Kingdom diversity (10 pts)
    kingdom_score = min(len(kingdom_set) / 5.0, 1.0) * 10.0

    # Climate variety / multi-cropping (30 pts): moderate temp + wide range = multi-season
    climate_variety = _range_score(avg_temp, 10.0, 25.0) * 0.15
    multi_crop = min(temp_range / 20.0, 1.0) * 15.0

    # Soil pH in crop-friendly range (15 pts)
    ph_diversity = _range_score(ph_val, 5.5, 7.5) * 0.15

    # Overall biodiversity density (15 pts)
    bio_density = min(total_obs / 100.0, 1.0) * 15.0

    score = _clamp(species_score + kingdom_score + climate_variety + multi_crop + ph_diversity + bio_density)

    details = {
        "unique_plant_species": unique_plant_count,
        "plant_observations": plant_obs,
        "total_observations": total_obs,
        "kingdom_count": len(kingdom_set),
        "avg_temp": round(avg_temp, 1),
        "temp_range": round(temp_range, 1),
        "ph": round(ph_val, 1),
    }
    return round(score, 1), details


# =============================================================================
# MAIN COMPUTATION (cached)
# =============================================================================

@st.cache_data(ttl=1800)
def compute_food_security_index(lat: float, lon: float) -> dict:
    """
    Fetch all data sources and compute 6-dimension food security scores.
    Returns a dict with dimension scores, details, overall index, and recommendations.
    """
    # ---- fetch data --------------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    landuse = fetch_landuse_infrastructure(lat, lon)
    biodiversity = fetch_biodiversity(lat, lon, radius_km=10)
    elevation = fetch_elevation_grid(lat, lon)
    food_infra = _fetch_food_infrastructure(lat, lon)

    # ---- score each dimension -----------------------------------------------
    soil_score, soil_details = _score_soil_fertility(soil)
    growing_score, growing_details = _score_growing_conditions(weather)
    arable_score, arable_details = _score_arable_land(elevation, landuse)
    infra_score, infra_details = _score_food_infrastructure(food_infra)
    water_score, water_details = _score_water_for_agriculture(water, weather)
    diversity_score, diversity_details = _score_crop_diversity(biodiversity, weather, soil)

    dimension_scores = {
        "Soil Fertility": soil_score,
        "Growing Conditions": growing_score,
        "Arable Land": arable_score,
        "Food Infrastructure": infra_score,
        "Water for Agriculture": water_score,
        "Crop Diversity": diversity_score,
    }

    # Food Security Index = weighted average
    weights = {
        "Soil Fertility": 0.20,
        "Growing Conditions": 0.20,
        "Arable Land": 0.18,
        "Food Infrastructure": 0.15,
        "Water for Agriculture": 0.15,
        "Crop Diversity": 0.12,
    }
    food_security_index = sum(
        dimension_scores[dim] * weights[dim] for dim in dimension_scores
    )
    food_security_index = round(_clamp(food_security_index), 1)

    # ---- soil profile for breakdown chart -----------------------------------
    soil_profile = {}
    for prop_name, div in [("soc", 10), ("nitrogen", 100), ("phh2o", 10), ("cec", 10), ("clay", 10)]:
        soil_profile[prop_name] = _extract_soil_profile(soil, prop_name, div)

    # ---- growing season calendar estimate -----------------------------------
    monthly_temps = []
    monthly_precip = []
    daily_data = (weather if isinstance(weather, dict) else {}).get("daily", {})
    raw_max = daily_data.get("temperature_2m_max", [])
    raw_min = daily_data.get("temperature_2m_min", [])

    daily_maxs = [v for v in raw_max if v is not None]
    daily_mins = [v for v in raw_min if v is not None]
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    temp_now = current.get("temperature_2m") or 15.0

    if daily_maxs and daily_mins:
        avg_temp = (sum(daily_maxs) + sum(daily_mins)) / (len(daily_maxs) + len(daily_mins))
    else:
        avg_temp = temp_now

    # Synthesize rough monthly variation with seasonal offset
    for m in range(12):
        # Simple seasonal model: warmest at month 6-7 (NH), coldest at 0-1
        if lat >= 0:
            seasonal_offset = 8.0 * math.cos(2 * math.pi * (m - 6.5) / 12.0)
        else:
            seasonal_offset = 8.0 * math.cos(2 * math.pi * (m - 0.5) / 12.0)
        monthly_temps.append(round(avg_temp + seasonal_offset, 1))

    annual_precip = growing_details.get("annual_precip_est", 500)
    for m in range(12):
        # Simple distribution: wetter months mid-year (adjust by hemisphere)
        if lat >= 0:
            seasonal_factor = 1.0 + 0.5 * math.cos(2 * math.pi * (m - 5.5) / 12.0)
        else:
            seasonal_factor = 1.0 + 0.5 * math.cos(2 * math.pi * (m - 11.5) / 12.0)
        monthly_precip.append(round(annual_precip / 12.0 * seasonal_factor, 1))

    growing_months = []
    for m in range(12):
        if monthly_temps[m] >= 5.0 and monthly_precip[m] >= 15.0:
            growing_months.append(MONTH_LABELS[m])

    # ---- crop suitability summary -------------------------------------------
    crop_categories = []
    if growing_details.get("avg_temp", 15) >= 15 and growing_details.get("avg_temp", 15) <= 30:
        crop_categories.append(("Cereals (wheat, barley, corn)", "High"))
    elif growing_details.get("avg_temp", 15) >= 10:
        crop_categories.append(("Cool-season cereals (wheat, barley)", "Moderate"))
    else:
        crop_categories.append(("Cold-hardy grains (rye, oats)", "Low"))

    if soil_details.get("ph", 6.5) >= 5.5 and soil_details.get("ph", 6.5) <= 7.5:
        crop_categories.append(("Root vegetables (potatoes, carrots)", "High"))
    else:
        crop_categories.append(("Root vegetables (potatoes, carrots)", "Low"))

    if growing_details.get("annual_precip_est", 500) >= 800:
        crop_categories.append(("Rice / paddy crops", "High"))
    elif growing_details.get("annual_precip_est", 500) >= 500:
        crop_categories.append(("Rice / paddy crops", "Moderate"))
    else:
        crop_categories.append(("Rice / paddy crops", "Low"))

    if growing_details.get("avg_temp", 15) >= 15 and growing_details.get("avg_temp", 15) <= 30:
        crop_categories.append(("Legumes (beans, lentils)", "High"))
    else:
        crop_categories.append(("Legumes (beans, lentils)", "Moderate"))

    if growing_details.get("avg_temp", 15) >= 15 and growing_details.get("annual_precip_est", 500) >= 400:
        crop_categories.append(("Fruits & orchards", "High"))
    else:
        crop_categories.append(("Fruits & orchards", "Moderate"))

    if growing_details.get("avg_temp", 15) >= 10 and growing_details.get("annual_precip_est", 500) >= 300:
        crop_categories.append(("Vegetables", "High"))
    else:
        crop_categories.append(("Vegetables", "Moderate"))

    # ---- recommendations ----------------------------------------------------
    recommendations = []
    if soil_score < 40:
        recommendations.append(
            "Soil fertility is low. Consider organic amendments, composting, "
            "or nitrogen-fixing cover crops to improve soil organic carbon and nutrient levels."
        )
    if growing_score < 35:
        recommendations.append(
            "Growing conditions are challenging. Greenhouses, polytunnels, or "
            "selection of cold-hardy/drought-resistant crop varieties is recommended."
        )
    if arable_score < 30:
        recommendations.append(
            "Limited arable land detected. Terracing, raised beds, or vertical farming "
            "techniques may help increase productive agricultural area."
        )
    if infra_score < 30:
        recommendations.append(
            "Food infrastructure is sparse. Investment in local markets, storage "
            "facilities, and food distribution networks would improve food security."
        )
    if water_score < 35:
        recommendations.append(
            "Water for agriculture is limited. Rainwater harvesting, drip irrigation, "
            "or borehole development could significantly improve water availability."
        )
    if diversity_score < 30:
        recommendations.append(
            "Low crop diversity detected. Introducing varied crop species and "
            "implementing crop rotation would build resilience against climate shocks."
        )
    if food_security_index >= 60 and not recommendations:
        recommendations.append(
            "Overall food security conditions appear favorable. Maintaining "
            "soil health and diversifying crop production will sustain food security."
        )
    if not recommendations:
        recommendations.append(
            "Moderate food security potential. Focus on improving the lowest-scoring "
            "dimensions to build a more resilient food system."
        )

    return {
        "food_security_index": food_security_index,
        "dimension_scores": dimension_scores,
        "soil_details": soil_details,
        "growing_details": growing_details,
        "arable_details": arable_details,
        "infra_details": infra_details,
        "water_details": water_details,
        "diversity_details": diversity_details,
        "soil_profile": soil_profile,
        "monthly_temps": monthly_temps,
        "monthly_precip": monthly_precip,
        "growing_months": growing_months,
        "crop_suitability": crop_categories,
        "recommendations": recommendations,
    }


# =============================================================================
# RENDER TAB
# =============================================================================

def render_food_security_tab():
    """Render the Food Security AI tab in Streamlit."""

    st.markdown(
        '<div class="tab-header" style="border-left:4px solid #10b981;'
        'background:rgba(16,185,129,0.08);padding:12px 18px;border-radius:8px;'
        'margin-bottom:16px;">'
        "<h4 style='margin:0;color:#e8ecf4;'>Food Security AI</h4>"
        "<p style='margin:4px 0 0;color:#8b97b0;font-size:13px;'>"
        "Agricultural capacity &amp; food system assessment &mdash; "
        "soil fertility, growing conditions, infrastructure, water &amp; crop diversity</p></div>",
        unsafe_allow_html=True,
    )

    # ---- location selector -------------------------------------------------
    col_preset, col_lat, col_lon = st.columns([1.4, 1, 1])
    with col_preset:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="food_sec_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50
    with col_lat:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="food_sec_lat",
        )
    with col_lon:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="food_sec_lon",
        )

    run = st.button(
        "Analyze Food Security",
        type="primary",
        use_container_width=True,
        key="food_sec_run",
    )

    if not run:
        st.info(
            "Select a location and click **Analyze Food Security** "
            "to generate a comprehensive food system assessment."
        )
        return

    # ---- compute -----------------------------------------------------------
    with st.spinner("Fetching soil, weather, water, infrastructure and biodiversity data..."):
        result = compute_food_security_index(lat, lon)

    fsi = result["food_security_index"]
    dims = result["dimension_scores"]
    soil_d = result["soil_details"]
    growing_d = result["growing_details"]
    arable_d = result["arable_details"]
    infra_d = result["infra_details"]
    water_d = result["water_details"]
    diversity_d = result["diversity_details"]
    soil_profile = result["soil_profile"]
    monthly_temps = result["monthly_temps"]
    monthly_precip = result["monthly_precip"]
    growing_months = result["growing_months"]
    crop_suit = result["crop_suitability"]
    recommendations = result["recommendations"]

    st.markdown("---")

    # ====================================================================
    # HEADER: FOOD SECURITY INDEX
    # ====================================================================
    if fsi >= 70:
        fsi_color = "#10b981"
        fsi_label = "HIGH"
    elif fsi >= 45:
        fsi_color = "#f59e0b"
        fsi_label = "MODERATE"
    elif fsi >= 25:
        fsi_color = "#f97316"
        fsi_label = "LOW"
    else:
        fsi_color = "#ef4444"
        fsi_label = "CRITICAL"

    st.markdown(
        f'<div style="background:rgba(26,26,46,0.85);border:2px solid {fsi_color};'
        f'border-radius:16px;padding:24px;text-align:center;margin-bottom:16px;">'
        f'<div style="color:#8b97b0;font-size:13px;text-transform:uppercase;'
        f'letter-spacing:2px;">Food Security Index</div>'
        f'<div style="color:{fsi_color};font-size:56px;font-weight:bold;'
        f'margin:8px 0;">{fsi}</div>'
        f'<div style="color:{fsi_color};font-size:18px;font-weight:bold;">'
        f'{fsi_label}</div>'
        f'<div style="color:#5a6580;font-size:12px;margin-top:6px;">'
        f'Composite score across 6 dimensions (0-100 scale)</div></div>',
        unsafe_allow_html=True,
    )

    # ====================================================================
    # DIMENSION METRIC CARDS
    # ====================================================================
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    dim_list = list(dims.items())
    cols = [m1, m2, m3, m4, m5, m6]
    for col, (dim_name, dim_val) in zip(cols, dim_list):
        color = DIMENSION_COLORS.get(dim_name, "#8b97b0")
        level = "High" if dim_val >= 65 else ("Moderate" if dim_val >= 40 else "Low")
        col.markdown(
            f'<div style="background:rgba(26,26,46,0.85);border:1px solid {color};'
            f'border-radius:10px;padding:10px;text-align:center;">'
            f'<div style="color:#8b97b0;font-size:10px;line-height:1.2;'
            f'min-height:24px;">{dim_name}</div>'
            f'<div style="color:{color};font-size:24px;font-weight:bold;'
            f'margin:4px 0;">{dim_val}</div>'
            f'<div style="color:#5a6580;font-size:10px;">{level}</div></div>',
            unsafe_allow_html=True,
        )

    st.markdown("")

    # ====================================================================
    # RADAR CHART: 6 DIMENSIONS
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "Food Security Dimensions</h5>",
        unsafe_allow_html=True,
    )

    dim_names = list(dims.keys())
    dim_values = list(dims.values())
    radar_values = dim_values + [dim_values[0]]
    radar_names = dim_names + [dim_names[0]]
    radar_colors = [DIMENSION_COLORS.get(n, "#06b6d4") for n in dim_names]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values,
        theta=radar_names,
        fill="toself",
        fillcolor="rgba(16,185,129,0.15)",
        line=dict(color="#10b981", width=2),
        marker=dict(size=7, color="#10b981"),
        name="Score",
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(26,26,46,0.6)",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#2a3550", tickfont=dict(color="#5a6580", size=10),
            ),
            angularaxis=dict(
                gridcolor="#2a3550",
                tickfont=dict(color="#e8ecf4", size=11),
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=70, r=70, t=30, b=30),
        height=400,
        showlegend=False,
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="foosec_pchart1")

    # ====================================================================
    # 1. SOIL FERTILITY BREAKDOWN
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "1. Soil Fertility Breakdown</h5>",
        unsafe_allow_html=True,
    )

    sf1, sf2 = st.columns([1.2, 1])
    with sf1:
        # Sub-scores bar chart
        sub_labels = ["SOC", "Nitrogen", "pH", "CEC"]
        sub_values = [
            soil_d.get("soc_score", 0),
            soil_d.get("nitrogen_score", 0),
            soil_d.get("ph_score", 0),
            soil_d.get("cec_score", 0),
        ]
        sub_colors = ["#10b981", "#14b8a6", "#06b6d4", "#f97316"]

        fig_soil = go.Figure()
        fig_soil.add_trace(go.Bar(
            x=sub_labels,
            y=sub_values,
            marker=dict(color=sub_colors),
            text=[f"{v:.0f}" for v in sub_values],
            textposition="outside",
            textfont=dict(color="#e8ecf4", size=11),
        ))
        fig_soil.update_layout(
            yaxis=dict(
                range=[0, 35], title="Sub-score",
                gridcolor="#2a3550", tickfont=dict(color="#8b97b0"),
                title_font=dict(color="#8b97b0"),
            ),
            xaxis=dict(tickfont=dict(color="#e8ecf4", size=12)),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(26,26,46,0.4)",
            margin=dict(l=50, r=20, t=10, b=30),
            height=280,
            showlegend=False,
        )
        st.plotly_chart(fig_soil, use_container_width=True, key="foosec_pchart2")

    with sf2:
        sm1, sm2 = st.columns(2)
        sm1.metric("SOC", f"{soil_d.get('soc', 0)} g/kg")
        sm2.metric("Nitrogen", f"{soil_d.get('nitrogen', 0)} g/kg")
        sm3, sm4 = st.columns(2)
        sm3.metric("pH", f"{soil_d.get('ph', 0)}")
        sm4.metric("CEC", f"{soil_d.get('cec', 0)} cmol/kg")
        st.metric("Clay Content", f"{soil_d.get('clay', 0)}%")

        # Soil profile depth chart
        soc_profile = soil_profile.get("soc", [])
        if soc_profile:
            depth_labels = [p[0] for p in soc_profile]
            soc_vals = [(p[1] or 0) for p in soc_profile]
            fig_depth = go.Figure()
            fig_depth.add_trace(go.Bar(
                y=depth_labels,
                x=soc_vals,
                orientation="h",
                marker=dict(color="#10b981"),
                name="SOC (g/kg)",
            ))
            fig_depth.update_layout(
                xaxis=dict(title="SOC (g/kg)", gridcolor="#2a3550",
                           tickfont=dict(color="#8b97b0"),
                           title_font=dict(color="#8b97b0")),
                yaxis=dict(tickfont=dict(color="#e8ecf4", size=10),
                           autorange="reversed"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(26,26,46,0.4)",
                margin=dict(l=80, r=20, t=10, b=30),
                height=200,
                showlegend=False,
            )
            st.plotly_chart(fig_depth, use_container_width=True, key="foosec_pchart3")

    # ====================================================================
    # 2. GROWING CONDITIONS
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "2. Growing Conditions</h5>",
        unsafe_allow_html=True,
    )

    gc1, gc2 = st.columns([1.2, 1])
    with gc1:
        gm1, gm2, gm3 = st.columns(3)
        gm1.metric("Avg Temp", f"{growing_d.get('avg_temp', 0)} C")
        gm2.metric("Min Temp", f"{growing_d.get('min_temp', 0)} C")
        gm3.metric("Max Temp", f"{growing_d.get('max_temp', 0)} C")

        gm4, gm5, gm6 = st.columns(3)
        gm4.metric("Frost-Free Days", f"{growing_d.get('frost_free_days', 0)}")
        gm5.metric("GDD (annual est.)", f"{growing_d.get('gdd_annual_est', 0):.0f}")
        gm6.metric("Annual Precip.", f"{growing_d.get('annual_precip_est', 0):.0f} mm")

    with gc2:
        # Growing season calendar
        st.markdown(
            "<div style='color:#8b97b0;font-size:12px;margin-bottom:4px;'>"
            "Growing Season Calendar (estimated)</div>",
            unsafe_allow_html=True,
        )
        cal_html = '<div style="display:flex;gap:2px;flex-wrap:wrap;">'
        for m in range(12):
            is_growing = MONTH_LABELS[m] in growing_months
            bg = "#10b981" if is_growing else "#1a2235"
            txt_color = "#0a0e1a" if is_growing else "#5a6580"
            cal_html += (
                f'<div style="background:{bg};color:{txt_color};'
                f'padding:6px 4px;border-radius:6px;text-align:center;'
                f'font-size:10px;font-weight:bold;width:42px;">'
                f'{MONTH_LABELS[m]}</div>'
            )
        cal_html += '</div>'
        st.markdown(cal_html, unsafe_allow_html=True)

        st.markdown(
            f"<div style='color:#8b97b0;font-size:11px;margin-top:6px;'>"
            f"Growing months: {len(growing_months)}/12 "
            f"({', '.join(growing_months) if growing_months else 'None'})</div>",
            unsafe_allow_html=True,
        )

    # Temperature & precipitation monthly chart
    fig_climate = go.Figure()
    fig_climate.add_trace(go.Scatter(
        x=MONTH_LABELS,
        y=monthly_temps,
        mode="lines+markers",
        name="Temp (C)",
        line=dict(color="#ef4444", width=2),
        marker=dict(size=6, color="#ef4444"),
        yaxis="y",
    ))
    fig_climate.add_trace(go.Bar(
        x=MONTH_LABELS,
        y=monthly_precip,
        name="Precip (mm)",
        marker=dict(color="rgba(59,130,246,0.5)"),
        yaxis="y2",
    ))
    fig_climate.update_layout(
        yaxis=dict(
            title="Temperature (C)", side="left",
            gridcolor="#2a3550", tickfont=dict(color="#ef4444"),
            title_font=dict(color="#ef4444"),
        ),
        yaxis2=dict(
            title="Precipitation (mm)", side="right",
            overlaying="y", gridcolor="#2a3550",
            tickfont=dict(color="#3b82f6"),
            title_font=dict(color="#3b82f6"),
        ),
        xaxis=dict(tickfont=dict(color="#e8ecf4", size=11)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,26,46,0.4)",
        margin=dict(l=50, r=60, t=10, b=30),
        height=280,
        legend=dict(font=dict(color="#8b97b0"), x=0.01, y=0.99),
        barmode="overlay",
    )
    st.plotly_chart(fig_climate, use_container_width=True, key="foosec_pchart4")

    # ====================================================================
    # 3. ARABLE LAND
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "3. Arable Land Assessment</h5>",
        unsafe_allow_html=True,
    )

    al1, al2 = st.columns([1, 1])
    with al1:
        am1, am2 = st.columns(2)
        am1.metric("Elevation", f"{arable_d.get('elevation', 0):.0f} m")
        am2.metric("Elevation Range", f"{arable_d.get('elev_range', 0):.0f} m")
        am3, am4 = st.columns(2)
        am3.metric("Farmland Areas", f"{arable_d.get('farmland_areas', 0)}")
        am4.metric("Orchards", f"{arable_d.get('orchards', 0)}")
        am5, am6 = st.columns(2)
        am5.metric("Vineyards", f"{arable_d.get('vineyards', 0)}")
        am6.metric("Meadows", f"{arable_d.get('meadows', 0)}")

    with al2:
        agri_data = {
            "Farmland": arable_d.get("farmland_areas", 0),
            "Orchards": arable_d.get("orchards", 0),
            "Vineyards": arable_d.get("vineyards", 0),
            "Meadows": arable_d.get("meadows", 0),
        }
        agri_data = {k: v for k, v in agri_data.items() if v > 0}
        if agri_data:
            fig_agri = go.Figure()
            fig_agri.add_trace(go.Pie(
                labels=list(agri_data.keys()),
                values=list(agri_data.values()),
                marker=dict(colors=["#10b981", "#16a34a", "#a855f7", "#84cc16"]),
                textfont=dict(color="#e8ecf4"),
                hole=0.4,
            ))
            fig_agri.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=250,
                legend=dict(font=dict(color="#8b97b0", size=11)),
            )
            st.plotly_chart(fig_agri, use_container_width=True, key="foosec_pchart5")
        else:
            st.info("No agricultural land use features detected in the search area.")

    # ====================================================================
    # 4. FOOD INFRASTRUCTURE
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "4. Food Infrastructure</h5>",
        unsafe_allow_html=True,
    )

    fi1, fi2 = st.columns([1, 1.2])
    with fi1:
        fm1, fm2, fm3 = st.columns(3)
        fm1.metric("Shops", f"{infra_d.get('shops', 0)}")
        fm2.metric("Markets", f"{infra_d.get('markets', 0)}")
        fm3.metric("Restaurants", f"{infra_d.get('restaurants', 0)}")
        fm4, fm5, fm6 = st.columns(3)
        fm4.metric("Storage", f"{infra_d.get('storage_facilities', 0)}")
        fm5.metric("Farms", f"{infra_d.get('farms', 0)}")
        fm6.metric("Greenhouses", f"{infra_d.get('greenhouses', 0)}")

    with fi2:
        infra_bars = {
            "Food Shops": infra_d.get("shops", 0),
            "Markets": infra_d.get("markets", 0),
            "Restaurants": infra_d.get("restaurants", 0),
            "Storage": infra_d.get("storage_facilities", 0),
            "Farms": infra_d.get("farms", 0),
            "Greenhouses": infra_d.get("greenhouses", 0),
        }
        infra_bars = {k: v for k, v in infra_bars.items() if v > 0}
        if infra_bars:
            sorted_infra = sorted(infra_bars.items(), key=lambda x: x[1])
            fig_infra = go.Figure()
            fig_infra.add_trace(go.Bar(
                y=[i[0] for i in sorted_infra],
                x=[i[1] for i in sorted_infra],
                orientation="h",
                marker=dict(color=["#06b6d4", "#10b981", "#f59e0b",
                                   "#8b5cf6", "#ec4899", "#3b82f6"][:len(sorted_infra)]),
                text=[str(i[1]) for i in sorted_infra],
                textposition="outside",
                textfont=dict(color="#e8ecf4", size=11),
            ))
            fig_infra.update_layout(
                xaxis=dict(title="Count", gridcolor="#2a3550",
                           tickfont=dict(color="#8b97b0"),
                           title_font=dict(color="#8b97b0")),
                yaxis=dict(tickfont=dict(color="#e8ecf4", size=11)),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(26,26,46,0.4)",
                margin=dict(l=100, r=40, t=10, b=30),
                height=250,
                showlegend=False,
            )
            st.plotly_chart(fig_infra, use_container_width=True, key="foosec_pchart6")
        else:
            st.info("No food infrastructure features detected in the search area.")

    # ====================================================================
    # 5. WATER FOR AGRICULTURE
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "5. Water for Agriculture</h5>",
        unsafe_allow_html=True,
    )

    wa1, wa2 = st.columns([1, 1])
    with wa1:
        wm1, wm2 = st.columns(2)
        wm1.metric("Springs", f"{water_d.get('springs', 0)}")
        wm2.metric("Wells", f"{water_d.get('wells', 0)}")
        wm3, wm4 = st.columns(2)
        wm3.metric("Rivers/Streams", f"{water_d.get('rivers_streams', 0)}")
        wm4.metric("Reservoirs", f"{water_d.get('reservoirs', 0)}")
        wm5, wm6 = st.columns(2)
        wm5.metric("Water Bodies", f"{water_d.get('water_bodies', 0)}")
        wm6.metric("Annual Precip.", f"{water_d.get('annual_precip_est', 0):.0f} mm")

    with wa2:
        water_cats = {
            "Springs": water_d.get("springs", 0),
            "Wells": water_d.get("wells", 0),
            "Rivers": water_d.get("rivers_streams", 0),
            "Reservoirs": water_d.get("reservoirs", 0),
            "Water Bodies": water_d.get("water_bodies", 0),
        }
        water_cats = {k: v for k, v in water_cats.items() if v > 0}
        if water_cats:
            fig_water = go.Figure()
            fig_water.add_trace(go.Pie(
                labels=list(water_cats.keys()),
                values=list(water_cats.values()),
                marker=dict(colors=["#06b6d4", "#3b82f6", "#10b981",
                                    "#8b5cf6", "#14b8a6"]),
                textfont=dict(color="#e8ecf4"),
                hole=0.4,
            ))
            fig_water.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=10, r=10, t=10, b=10),
                height=250,
                legend=dict(font=dict(color="#8b97b0", size=11)),
            )
            st.plotly_chart(fig_water, use_container_width=True, key="foosec_pchart7")
        else:
            st.info("No water features detected in the search area.")

    # ====================================================================
    # 6. CROP DIVERSITY
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-bottom:4px;'>"
        "6. Crop Diversity Potential</h5>",
        unsafe_allow_html=True,
    )

    cd1, cd2 = st.columns([1, 1])
    with cd1:
        dm1, dm2 = st.columns(2)
        dm1.metric("Plant Species", f"{diversity_d.get('unique_plant_species', 0)}")
        dm2.metric("Plant Observations", f"{diversity_d.get('plant_observations', 0)}")
        dm3, dm4 = st.columns(2)
        dm3.metric("Total Bio. Obs.", f"{diversity_d.get('total_observations', 0)}")
        dm4.metric("Kingdom Count", f"{diversity_d.get('kingdom_count', 0)}")
        dm5, dm6 = st.columns(2)
        dm5.metric("Avg Temp", f"{diversity_d.get('avg_temp', 0)} C")
        dm6.metric("Temp Range", f"{diversity_d.get('temp_range', 0)} C")

    with cd2:
        # Crop suitability summary table
        st.markdown(
            "<div style='color:#8b97b0;font-size:12px;margin-bottom:6px;'>"
            "Crop Suitability Summary</div>",
            unsafe_allow_html=True,
        )
        for crop_name, suitability in crop_suit:
            if suitability == "High":
                suit_color = "#10b981"
                suit_icon = "+"
            elif suitability == "Moderate":
                suit_color = "#f59e0b"
                suit_icon = "~"
            else:
                suit_color = "#ef4444"
                suit_icon = "-"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;'
                f'margin-bottom:4px;padding:6px 10px;'
                f'background:rgba(26,26,46,0.6);border-radius:6px;'
                f'border-left:3px solid {suit_color};">'
                f'<span style="color:{suit_color};font-weight:bold;'
                f'font-size:14px;width:16px;">{suit_icon}</span>'
                f'<span style="color:#e8ecf4;font-size:12px;flex:1;">'
                f'{crop_name}</span>'
                f'<span style="color:{suit_color};font-size:11px;'
                f'font-weight:bold;">{suitability}</span></div>',
                unsafe_allow_html=True,
            )

    # ====================================================================
    # DIMENSION COMPARISON BAR CHART
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-top:16px;margin-bottom:4px;'>"
        "Dimension Comparison</h5>",
        unsafe_allow_html=True,
    )

    sorted_dims = sorted(dims.items(), key=lambda x: x[1])
    fig_dims = go.Figure()
    fig_dims.add_trace(go.Bar(
        y=[d[0] for d in sorted_dims],
        x=[d[1] for d in sorted_dims],
        orientation="h",
        marker=dict(color=[DIMENSION_COLORS.get(d[0], "#06b6d4") for d in sorted_dims]),
        text=[f"{d[1]}" for d in sorted_dims],
        textposition="outside",
        textfont=dict(color="#e8ecf4", size=12),
    ))
    fig_dims.update_layout(
        xaxis=dict(
            range=[0, 110], title="Score (0-100)",
            gridcolor="#2a3550", tickfont=dict(color="#8b97b0"),
            title_font=dict(color="#8b97b0"),
        ),
        yaxis=dict(tickfont=dict(color="#e8ecf4", size=12)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(26,26,46,0.4)",
        margin=dict(l=180, r=50, t=10, b=30),
        height=300,
        showlegend=False,
    )
    st.plotly_chart(fig_dims, use_container_width=True, key="foosec_pchart8")

    # ====================================================================
    # RECOMMENDATIONS
    # ====================================================================
    st.markdown(
        "<h5 style='color:#e8ecf4;margin-top:12px;margin-bottom:4px;'>"
        "Recommendations</h5>",
        unsafe_allow_html=True,
    )
    for rec in recommendations:
        st.markdown(
            f'<div style="background:rgba(16,185,129,0.07);'
            f"border-left:3px solid #10b981;padding:10px 14px;"
            f'border-radius:0 8px 8px 0;margin-bottom:6px;'
            f'color:#c8d0dc;font-size:13px;">'
            f"{rec}</div>",
            unsafe_allow_html=True,
        )
