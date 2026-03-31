"""
Health Geography AI -- Health-related geographic assessment combining
healthcare access, disease vectors, air quality, water safety,
climate health, environmental toxins, and wellness scoring.
Uses: Overpass API, Open-Meteo, Open-Meteo Air Quality, ISRIC SoilGrids,
      Open Topo Data.
"""

import logging
import math
import requests
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
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

HEALTH_COMPONENTS = {
    "healthcare": {"name": "Healthcare Access", "color": "#ef4444", "weight": 0.20},
    "disease_vector": {"name": "Disease Vector Risk", "color": "#f59e0b", "weight": 0.15},
    "air_quality": {"name": "Air Quality Health", "color": "#6366f1", "weight": 0.15},
    "water_safety": {"name": "Water Safety", "color": "#3b82f6", "weight": 0.15},
    "climate_health": {"name": "Climate Health", "color": "#ec4899", "weight": 0.10},
    "env_toxins": {"name": "Environmental Toxins", "color": "#22c55e", "weight": 0.10},
    "wellness": {"name": "Wellness Score", "color": "#10b981", "weight": 0.15},
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING (ALL CACHED)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def fetch_healthcare_facilities(lat, lon, radius=5000):
    """Fetch healthcare and wellness facilities from Overpass."""
    query = f"""
    [out:json][timeout:30];
    (
      node["amenity"~"hospital|clinic|doctors|pharmacy|dentist|veterinary"](around:{radius},{lat},{lon});
      way["amenity"~"hospital|clinic"](around:{radius},{lat},{lon});
      node["leisure"~"park|garden|fitness_centre|swimming_pool"](around:{radius},{lat},{lon});
      way["leisure"~"park|garden|nature_reserve"](around:{radius},{lat},{lon});
      node["healthcare"](around:{radius},{lat},{lon});
    );
    out body;
    """
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Healthcare fetch error: {e}")
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_air_quality_health(lat, lon):
    """Fetch air quality data from Open-Meteo Air Quality API."""
    try:
        resp = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "pm10,pm2_5,nitrogen_dioxide,ozone,sulphur_dioxide,carbon_monoxide,us_aqi",
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Air quality error: {e}")
        return {}


@st.cache_data(ttl=1800)
def fetch_uv_index(lat, lon):
    """Fetch UV index from Open-Meteo forecast API."""
    try:
        resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": "uv_index_max",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"UV index error: {e}")
        return {}


@st.cache_data(ttl=1800)
def fetch_elevation_health(lat, lon):
    """Fetch elevation from Open Topo Data."""
    try:
        resp = requests.get(
            "https://api.opentopodata.org/v1/srtm30m",
            params={"locations": f"{lat},{lon}"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            elev = results[0].get("elevation")
            return float(elev) if elev is not None else 0.0
        return 0.0
    except Exception as e:
        logger.warning(f"Elevation fetch error: {e}")
        return 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING FUNCTIONS (ALL CACHED)
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def score_healthcare_access(lat, lon, radius=5000):
    """
    Healthcare Access score (0-100).
    Count hospitals, clinics, pharmacies, doctors in radius.
    Score = min(100, hospitals*20 + clinics*10 + pharmacies*5 + doctors*8).
    """
    data = fetch_healthcare_facilities(lat, lon, radius)
    elements = data.get("elements", [])

    hospitals = 0
    clinics = 0
    pharmacies = 0
    doctors = 0
    dentists = 0
    healthcare_other = 0

    for el in elements:
        tags = el.get("tags", {})
        amenity = tags.get("amenity", "")
        healthcare_tag = tags.get("healthcare", "")
        if amenity == "hospital" or healthcare_tag == "hospital":
            hospitals += 1
        elif amenity == "clinic" or healthcare_tag == "clinic":
            clinics += 1
        elif amenity == "pharmacy":
            pharmacies += 1
        elif amenity == "doctors" or healthcare_tag == "doctor":
            doctors += 1
        elif amenity == "dentist" or healthcare_tag == "dentist":
            dentists += 1
        elif healthcare_tag:
            healthcare_other += 1

    raw_score = hospitals * 20 + clinics * 10 + pharmacies * 5 + doctors * 8 + dentists * 4
    score = min(100, raw_score)

    details = {
        "hospitals": hospitals,
        "clinics": clinics,
        "pharmacies": pharmacies,
        "doctors": doctors,
        "dentists": dentists,
        "healthcare_other": healthcare_other,
        "total_facilities": hospitals + clinics + pharmacies + doctors + dentists + healthcare_other,
    }
    return score, details


@st.cache_data(ttl=1800)
def score_disease_vector_risk(lat, lon):
    """
    Disease Vector Risk score (0-100). INVERTED: higher = LOWER risk.
    Temp 20-30C + humidity >60% = high mosquito risk = LOW score.
    """
    weather = fetch_weather_data(lat, lon)
    current = weather.get("current", {})
    temp = current.get("temperature_2m", None)
    humidity = current.get("relative_humidity_2m", None)

    temp = (temp or 0)
    humidity = (humidity or 0)

    # Mosquito risk factor (0-50): peaks at 25C with high humidity
    if 20 <= temp <= 30 and humidity > 60:
        mosquito_factor = 40 + min(10, (humidity - 60) * 0.5)
    elif 15 <= temp <= 35 and humidity > 40:
        dist_from_ideal = min(abs(temp - 25), 10)
        mosquito_factor = max(0, 30 - dist_from_ideal * 3)
    else:
        mosquito_factor = 0

    # Tick risk factor (0-30): active in 5-30C with moderate humidity
    if 5 <= temp <= 30 and humidity > 40:
        tick_factor = 20 + min(10, max(0, humidity - 50) * 0.3)
    elif 0 <= temp <= 35:
        tick_factor = 8
    else:
        tick_factor = 0

    # Latitude-based tropical disease zone estimation
    abs_lat = abs(lat)
    if abs_lat < 23.5:
        tropical_penalty = 15  # tropics -- higher malaria/dengue risk
    elif abs_lat < 35:
        tropical_penalty = 8  # subtropical
    else:
        tropical_penalty = 0

    total_risk = mosquito_factor + tick_factor + tropical_penalty
    score = max(0, min(100, 100 - total_risk))

    details = {
        "temperature_c": round(temp, 1),
        "humidity_pct": round(humidity, 1),
        "mosquito_factor": round(mosquito_factor, 1),
        "tick_factor": round(tick_factor, 1),
        "tropical_penalty": tropical_penalty,
        "latitude_zone": "Tropical" if abs_lat < 23.5 else ("Subtropical" if abs_lat < 35 else "Temperate/Polar"),
    }
    return score, details


@st.cache_data(ttl=1800)
def score_air_quality_health(lat, lon):
    """
    Air Quality Health score (0-100). INVERTED: higher = better air.
    AQI 0-50=100, 51-100=75, 101-150=50, 151-200=25, >200=0.
    Also factors PM2.5 and ozone.
    """
    aq_data = fetch_air_quality_health(lat, lon)
    current = aq_data.get("current", {})

    aqi = current.get("us_aqi", None)
    pm25 = current.get("pm2_5", None)
    pm10 = current.get("pm10", None)
    ozone = current.get("ozone", None)
    no2 = current.get("nitrogen_dioxide", None)
    so2 = current.get("sulphur_dioxide", None)
    co = current.get("carbon_monoxide", None)

    aqi = (aqi or 0)

    # Base score from AQI
    if aqi <= 50:
        base_score = 100
    elif aqi <= 100:
        base_score = 75
    elif aqi <= 150:
        base_score = 50
    elif aqi <= 200:
        base_score = 25
    else:
        base_score = 0

    # PM2.5 penalty (WHO guideline: 15 ug/m3 annual, 45 ug/m3 24-hour)
    pm25_val = (pm25 or 0)
    if pm25_val > 55:
        pm25_penalty = 15
    elif pm25_val > 35:
        pm25_penalty = 10
    elif pm25_val > 15:
        pm25_penalty = 5
    else:
        pm25_penalty = 0

    # Ozone penalty (WHO guideline: 100 ug/m3)
    ozone_val = (ozone or 0)
    if ozone_val > 180:
        ozone_penalty = 15
    elif ozone_val > 120:
        ozone_penalty = 10
    elif ozone_val > 100:
        ozone_penalty = 5
    else:
        ozone_penalty = 0

    score = max(0, min(100, base_score - pm25_penalty - ozone_penalty))

    details = {
        "us_aqi": round(aqi, 1),
        "pm2_5": round(pm25_val, 1),
        "pm10": round((pm10 or 0), 1),
        "ozone": round(ozone_val, 1),
        "no2": round((no2 or 0), 1),
        "so2": round((so2 or 0), 1),
        "co": round((co or 0), 1),
        "aqi_category": (
            "Good" if aqi <= 50
            else "Moderate" if aqi <= 100
            else "Unhealthy (Sensitive)" if aqi <= 150
            else "Unhealthy" if aqi <= 200
            else "Very Unhealthy" if aqi <= 300
            else "Hazardous"
        ),
    }
    return score, details


@st.cache_data(ttl=1800)
def score_water_safety(lat, lon, radius=5000):
    """
    Water Safety score (0-100).
    Count water treatment works, springs, check water features health.
    """
    water_data = fetch_water_features(lat, lon, radius)
    elements = water_data.get("elements", [])

    springs = 0
    wells = 0
    waterways = 0
    water_bodies = 0
    treatment_works = 0

    for el in elements:
        tags = el.get("tags", {})
        natural = tags.get("natural", "")
        man_made = tags.get("man_made", "")
        waterway = tags.get("waterway", "")

        if natural == "spring":
            springs += 1
        elif man_made == "water_well":
            wells += 1
        elif man_made in ("water_works", "wastewater_plant"):
            treatment_works += 1
        elif waterway:
            waterways += 1
        elif natural == "water":
            water_bodies += 1

    # Also check landuse for water treatment and reservoirs
    landuse_data = fetch_landuse_infrastructure(lat, lon, radius)
    for el in landuse_data.get("elements", []):
        tags = el.get("tags", {})
        landuse = tags.get("landuse", "")
        if landuse == "reservoir" or tags.get("man_made", "") == "reservoir_covered":
            treatment_works += 1

    # Score: water treatment infrastructure + natural clean sources
    water_infra_score = min(40, treatment_works * 15 + wells * 8)
    natural_water_score = min(30, springs * 10 + water_bodies * 5)
    waterway_score = min(30, waterways * 5)

    score = min(100, water_infra_score + natural_water_score + waterway_score)

    details = {
        "springs": springs,
        "wells": wells,
        "treatment_works": treatment_works,
        "waterways": waterways,
        "water_bodies": water_bodies,
        "total_water_features": springs + wells + waterways + water_bodies + treatment_works,
    }
    return score, details


@st.cache_data(ttl=1800)
def score_climate_health(lat, lon):
    """
    Climate Health score (0-100).
    Penalize extremes: >35C heat stress, <-10C cold stress, high UV.
    """
    weather = fetch_weather_data(lat, lon)
    current = weather.get("current", {})
    temp = current.get("temperature_2m", None)
    humidity = current.get("relative_humidity_2m", None)
    temp = (temp or 15.0)
    humidity = (humidity or 50.0)

    # UV index
    uv_data = fetch_uv_index(lat, lon)
    daily = uv_data.get("daily", {})
    uv_max_list = daily.get("uv_index_max", [])
    uv_values = [x for x in uv_max_list if x is not None]
    uv_index = uv_values[0] if uv_values else 0.0

    # Elevation for altitude sickness consideration
    elevation = fetch_elevation_health(lat, lon)

    score = 100.0

    # Heat stress penalty (>35C severe, >40C extreme)
    if temp > 45:
        score -= 45
    elif temp > 40:
        score -= 35
    elif temp > 35:
        score -= 25
    elif temp > 32:
        score -= 15
    elif temp > 28:
        score -= 5

    # Heat index (combines temp + humidity)
    if temp > 27 and humidity > 40:
        heat_index_penalty = min(20, (temp - 27) * (humidity - 40) * 0.02)
        score -= heat_index_penalty

    # Cold stress penalty (<-10C severe, <-25C extreme)
    if temp < -25:
        score -= 40
    elif temp < -15:
        score -= 30
    elif temp < -10:
        score -= 20
    elif temp < -5:
        score -= 10
    elif temp < 0:
        score -= 5

    # UV exposure penalty
    if uv_index > 11:
        score -= 20  # extreme UV
    elif uv_index > 8:
        score -= 12  # very high UV
    elif uv_index > 6:
        score -= 6   # high UV
    elif uv_index > 3:
        score -= 2   # moderate UV

    # Altitude sickness risk (above 2500m)
    if elevation > 5000:
        score -= 25
    elif elevation > 4000:
        score -= 15
    elif elevation > 3000:
        score -= 8
    elif elevation > 2500:
        score -= 4

    score = max(0, min(100, score))

    uv_label = (
        "Low" if uv_index <= 2
        else "Moderate" if uv_index <= 5
        else "High" if uv_index <= 7
        else "Very High" if uv_index <= 10
        else "Extreme"
    )

    details = {
        "temperature_c": round(temp, 1),
        "humidity_pct": round(humidity, 1),
        "uv_index": round(uv_index, 1),
        "uv_category": uv_label,
        "elevation_m": round(elevation, 0),
        "heat_stress": "Severe" if temp > 40 else ("High" if temp > 35 else ("Moderate" if temp > 32 else "Low")),
        "cold_stress": "Severe" if temp < -15 else ("High" if temp < -10 else ("Moderate" if temp < -5 else "Low")),
    }
    return score, details


@st.cache_data(ttl=1800)
def score_environmental_toxins(lat, lon, radius=5000):
    """
    Environmental Toxins score (0-100). INVERTED: higher = SAFER.
    Count industrial zones, landfills, quarries. More industry = lower score.
    Also check soil contamination indicators from SoilGrids.
    """
    landuse_data = fetch_landuse_infrastructure(lat, lon, radius)
    elements = landuse_data.get("elements", [])

    industrial = 0
    construction = 0
    quarries = 0
    landfills = 0
    military = 0

    for el in elements:
        tags = el.get("tags", {})
        landuse = tags.get("landuse", "")
        if landuse == "industrial":
            industrial += 1
        elif landuse == "construction":
            construction += 1
        elif landuse == "quarry":
            quarries += 1
        elif landuse == "landfill":
            landfills += 1
        elif landuse == "military":
            military += 1

    # Soil contamination indicators from SoilGrids
    soil_data = fetch_soil_data(lat, lon)
    soil_properties = soil_data.get("properties", {})
    layers = soil_properties.get("layers", [])

    # Check pH for contamination (extreme pH indicates possible contamination)
    ph_values = []
    soc_values = []
    for layer in layers:
        prop_name = layer.get("name", "")
        depths = layer.get("depths", [])
        for depth_entry in depths:
            val = depth_entry.get("values", {}).get("mean")
            if val is not None:
                if prop_name == "phh2o":
                    ph_values.append(val / 10.0)  # SoilGrids returns pH * 10
                elif prop_name == "soc":
                    soc_values.append(val / 10.0)  # g/kg

    ph_clean = [x for x in ph_values if x is not None]
    avg_ph = sum(ph_clean) / len(ph_clean) if ph_clean else 7.0

    # pH contamination indicator: very acidic (<4.5) or very alkaline (>8.5)
    ph_penalty = 0
    if avg_ph < 4.0 or avg_ph > 9.0:
        ph_penalty = 15
    elif avg_ph < 4.5 or avg_ph > 8.5:
        ph_penalty = 8
    elif avg_ph < 5.0 or avg_ph > 8.0:
        ph_penalty = 3

    # Industrial proximity penalty
    industry_penalty = min(50, industrial * 10 + quarries * 8 + landfills * 15 + construction * 3 + military * 5)

    total_penalty = industry_penalty + ph_penalty
    score = max(0, min(100, 100 - total_penalty))

    details = {
        "industrial_zones": industrial,
        "construction_sites": construction,
        "quarries": quarries,
        "landfills": landfills,
        "military_areas": military,
        "avg_soil_ph": round(avg_ph, 1),
        "ph_contamination_risk": "High" if ph_penalty >= 10 else ("Moderate" if ph_penalty > 0 else "Low"),
        "total_hazardous_sites": industrial + quarries + landfills + military,
    }
    return score, details


@st.cache_data(ttl=1800)
def score_wellness(lat, lon, radius=5000):
    """
    Wellness Score (0-100).
    Green spaces (parks, gardens, nature reserves) + recreation facilities
    + clean air composite.
    """
    hc_data = fetch_healthcare_facilities(lat, lon, radius)
    elements = hc_data.get("elements", [])

    parks = 0
    gardens = 0
    nature_reserves = 0
    fitness_centres = 0
    swimming_pools = 0
    other_leisure = 0

    for el in elements:
        tags = el.get("tags", {})
        leisure = tags.get("leisure", "")
        if leisure == "park":
            parks += 1
        elif leisure == "garden":
            gardens += 1
        elif leisure == "nature_reserve":
            nature_reserves += 1
        elif leisure == "fitness_centre":
            fitness_centres += 1
        elif leisure == "swimming_pool":
            swimming_pools += 1
        elif leisure:
            other_leisure += 1

    # Green space component (0-40)
    green_score = min(40, parks * 6 + gardens * 4 + nature_reserves * 8)

    # Recreation component (0-30)
    recreation_score = min(30, fitness_centres * 8 + swimming_pools * 6 + other_leisure * 3)

    # Air quality composite (0-30): use air quality score scaled down
    aq_score, _ = score_air_quality_health(lat, lon)
    air_composite = round(aq_score * 0.30)

    score = min(100, green_score + recreation_score + air_composite)

    details = {
        "parks": parks,
        "gardens": gardens,
        "nature_reserves": nature_reserves,
        "fitness_centres": fitness_centres,
        "swimming_pools": swimming_pools,
        "other_leisure": other_leisure,
        "green_space_total": parks + gardens + nature_reserves,
        "recreation_total": fitness_centres + swimming_pools + other_leisure,
    }
    return score, details


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOSITE HEALTH INDEX
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_health_geography_index(lat, lon, radius=5000):
    """Compute all 7 health dimension scores and the overall weighted index."""
    hc_score, hc_details = score_healthcare_access(lat, lon, radius)
    dv_score, dv_details = score_disease_vector_risk(lat, lon)
    aq_score, aq_details = score_air_quality_health(lat, lon)
    ws_score, ws_details = score_water_safety(lat, lon, radius)
    ch_score, ch_details = score_climate_health(lat, lon)
    et_score, et_details = score_environmental_toxins(lat, lon, radius)
    wl_score, wl_details = score_wellness(lat, lon, radius)

    scores = {
        "healthcare": {"score": round(hc_score, 1), "details": hc_details},
        "disease_vector": {"score": round(dv_score, 1), "details": dv_details},
        "air_quality": {"score": round(aq_score, 1), "details": aq_details},
        "water_safety": {"score": round(ws_score, 1), "details": ws_details},
        "climate_health": {"score": round(ch_score, 1), "details": ch_details},
        "env_toxins": {"score": round(et_score, 1), "details": et_details},
        "wellness": {"score": round(wl_score, 1), "details": wl_details},
    }

    # Weighted overall score
    overall = 0.0
    for key, comp in HEALTH_COMPONENTS.items():
        overall += scores[key]["score"] * comp["weight"]

    overall = round(min(100, max(0, overall)), 1)

    if overall >= 70:
        label = "Healthy"
    elif overall >= 40:
        label = "Moderate"
    else:
        label = "Unhealthy"

    return overall, label, scores


# ═══════════════════════════════════════════════════════════════════════════════
# CHART BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════

def build_radar_chart(scores):
    """Build a Plotly radar chart for the 7 health dimensions."""
    categories = []
    values = []
    colors = []

    for key in HEALTH_COMPONENTS:
        comp = HEALTH_COMPONENTS[key]
        categories.append(comp["name"])
        values.append(scores[key]["score"])
        colors.append(comp["color"])

    # Close the polygon
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(6, 182, 212, 0.15)",
        line=dict(color="#06b6d4", width=2),
        marker=dict(size=6, color="#06b6d4"),
        name="Health Score",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color="#5a6580", size=10),
                gridcolor="#2a3550",
                linecolor="#2a3550",
            ),
            angularaxis=dict(
                tickfont=dict(color="#e8ecf4", size=11),
                gridcolor="#2a3550",
                linecolor="#2a3550",
            ),
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4"),
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=400,
    )

    return fig


def build_aqi_gauge(aqi_value):
    """Build a Plotly AQI gauge indicator with color zones."""
    aqi_value = (aqi_value or 0)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=aqi_value,
        number=dict(font=dict(color="#e8ecf4", size=40)),
        title=dict(text="US Air Quality Index", font=dict(color="#8b97b0", size=14)),
        gauge=dict(
            axis=dict(
                range=[0, 500],
                tickwidth=1,
                tickcolor="#5a6580",
                tickfont=dict(color="#5a6580"),
            ),
            bar=dict(color="#06b6d4"),
            bgcolor="#1a1a2e",
            borderwidth=0,
            steps=[
                dict(range=[0, 50], color="#22c55e"),
                dict(range=[50, 100], color="#f59e0b"),
                dict(range=[100, 150], color="#f97316"),
                dict(range=[150, 200], color="#ef4444"),
                dict(range=[200, 300], color="#a855f7"),
                dict(range=[300, 500], color="#7f1d1d"),
            ],
            threshold=dict(
                line=dict(color="#ffffff", width=3),
                thickness=0.8,
                value=aqi_value,
            ),
        ),
    ))

    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4"),
        height=280,
        margin=dict(l=30, r=30, t=50, b=20),
    )

    return fig


def build_facilities_bar_chart(details):
    """Build a Plotly bar chart of healthcare facilities by type."""
    facility_types = {
        "Hospitals": details.get("hospitals", 0),
        "Clinics": details.get("clinics", 0),
        "Pharmacies": details.get("pharmacies", 0),
        "Doctors": details.get("doctors", 0),
        "Dentists": details.get("dentists", 0),
        "Other HC": details.get("healthcare_other", 0),
    }

    # Filter to non-zero
    filtered = {k: v for k, v in facility_types.items() if v > 0}
    if not filtered:
        filtered = facility_types  # Show all even if zero

    colors = ["#ef4444", "#f59e0b", "#3b82f6", "#10b981", "#8b5cf6", "#ec4899"]

    fig = go.Figure(go.Bar(
        x=list(filtered.keys()),
        y=list(filtered.values()),
        marker_color=colors[:len(filtered)],
        text=list(filtered.values()),
        textposition="auto",
        textfont=dict(color="#e8ecf4"),
    ))

    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4"),
        xaxis=dict(
            gridcolor="#2a3550",
            tickfont=dict(color="#8b97b0"),
        ),
        yaxis=dict(
            gridcolor="#2a3550",
            tickfont=dict(color="#8b97b0"),
            title="Count",
        ),
        height=300,
        margin=dict(l=40, r=20, t=20, b=40),
        bargap=0.3,
    )

    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# UI HELPER: METRIC CARD
# ═══════════════════════════════════════════════════════════════════════════════

def _render_score_card(name, score, color, details_html=""):
    """Render a styled score card in HTML."""
    if score >= 70:
        grade = "Good"
        grade_color = "#22c55e"
    elif score >= 40:
        grade = "Fair"
        grade_color = "#f59e0b"
    else:
        grade = "Poor"
        grade_color = "#ef4444"

    bar_width = max(0, min(100, score))

    return f"""
    <div style="background:rgba(26,26,46,0.85);border:1px solid #2a3550;
                border-radius:12px;padding:16px;backdrop-filter:blur(16px);
                border-left:4px solid {color};height:100%;">
        <div style="display:flex;justify-content:space-between;align-items:center;
                    margin-bottom:8px;">
            <span style="color:#e8ecf4;font-size:14px;font-weight:600;">{name}</span>
            <span style="color:{grade_color};font-size:13px;font-weight:bold;">
                {grade}
            </span>
        </div>
        <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:8px;">
            <span style="color:{color};font-size:28px;font-weight:bold;">
                {score:.0f}
            </span>
            <span style="color:#5a6580;font-size:13px;">/100</span>
        </div>
        <div style="background:#0f172a;border-radius:6px;height:8px;
                    margin-bottom:10px;overflow:hidden;">
            <div style="width:{bar_width:.0f}%;background:{color};height:100%;
                        border-radius:6px;transition:width 0.5s;"></div>
        </div>
        <div style="color:#8b97b0;font-size:11px;line-height:1.5;">
            {details_html}
        </div>
    </div>
    """


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def render_health_geography_tab():
    """Render the Health Geography AI tab UI."""

    # ── Tab Header ──
    st.markdown(
        '<div style="background:linear-gradient(135deg,rgba(239,68,68,0.15),'
        'rgba(236,72,153,0.10));border:1px solid rgba(239,68,68,0.25);'
        'border-radius:12px;padding:18px 24px;margin-bottom:20px;">'
        '<h4 style="color:#ef4444;margin:0 0 4px 0;">Health Geography AI</h4>'
        '<p style="color:#8b97b0;margin:0;font-size:13px;">'
        'Assess health-related geographic factors: healthcare access, disease '
        'vectors, air quality, water safety, climate health, environmental '
        'toxins &amp; wellness</p></div>',
        unsafe_allow_html=True,
    )

    # ── Location Selector ──
    loc_c1, loc_c2, loc_c3 = st.columns([1.4, 1, 1])
    with loc_c1:
        preset = st.selectbox(
            "Location Preset",
            list(ANALYSIS_PRESETS.keys()),
            key="hg_preset",
        )
    with loc_c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="hg_lat",
        )
    with loc_c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="hg_lon",
        )

    radius_col, _ = st.columns([1, 2])
    with radius_col:
        radius_km = st.slider(
            "Analysis Radius (km)", 1, 20, 5, key="hg_radius",
        )
    radius_m = radius_km * 1000

    run_btn = st.button(
        "Analyze Health Geography",
        type="primary",
        key="hg_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info(
            "Select a location and click **Analyze Health Geography** to "
            "generate a comprehensive health assessment for the area."
        )
        return

    # ══════════════════════════════════════════════════════════════════════════
    # RUN ANALYSIS
    # ══════════════════════════════════════════════════════════════════════════

    progress = st.progress(0, text="Starting health geography analysis...")

    progress.progress(10, text="Scoring healthcare access...")
    hc_score, hc_details = score_healthcare_access(lat, lon, radius_m)

    progress.progress(25, text="Assessing disease vector risk...")
    dv_score, dv_details = score_disease_vector_risk(lat, lon)

    progress.progress(40, text="Analyzing air quality health impact...")
    aq_score, aq_details = score_air_quality_health(lat, lon)

    progress.progress(50, text="Evaluating water safety...")
    ws_score, ws_details = score_water_safety(lat, lon, radius_m)

    progress.progress(60, text="Assessing climate health factors...")
    ch_score, ch_details = score_climate_health(lat, lon)

    progress.progress(75, text="Checking environmental toxins...")
    et_score, et_details = score_environmental_toxins(lat, lon, radius_m)

    progress.progress(85, text="Computing wellness score...")
    wl_score, wl_details = score_wellness(lat, lon, radius_m)

    progress.progress(95, text="Computing overall index...")

    # Build scores dict for charts
    scores = {
        "healthcare": {"score": round(hc_score, 1), "details": hc_details},
        "disease_vector": {"score": round(dv_score, 1), "details": dv_details},
        "air_quality": {"score": round(aq_score, 1), "details": aq_details},
        "water_safety": {"score": round(ws_score, 1), "details": ws_details},
        "climate_health": {"score": round(ch_score, 1), "details": ch_details},
        "env_toxins": {"score": round(et_score, 1), "details": et_details},
        "wellness": {"score": round(wl_score, 1), "details": wl_details},
    }

    # Weighted overall
    overall = 0.0
    for key, comp in HEALTH_COMPONENTS.items():
        overall += scores[key]["score"] * comp["weight"]
    overall = round(min(100, max(0, overall)), 1)

    if overall >= 70:
        label = "Healthy"
        label_color = "#22c55e"
    elif overall >= 40:
        label = "Moderate"
        label_color = "#f59e0b"
    else:
        label = "Unhealthy"
        label_color = "#ef4444"

    progress.progress(100, text="Analysis complete!")

    # ══════════════════════════════════════════════════════════════════════════
    # 1. HEADER CARD -- Overall Health Geography Index
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown("---")

    st.markdown(
        f'<div style="background:linear-gradient(135deg,rgba(26,26,46,0.95),'
        f'rgba(26,26,46,0.80));border:1px solid #2a3550;border-radius:16px;'
        f'padding:28px 32px;text-align:center;margin-bottom:24px;'
        f'backdrop-filter:blur(16px);">'
        f'<p style="color:#8b97b0;font-size:13px;margin:0 0 4px 0;'
        f'text-transform:uppercase;letter-spacing:1px;">Health Geography Index</p>'
        f'<span style="color:{label_color};font-size:56px;font-weight:bold;'
        f'line-height:1.1;">{overall}</span>'
        f'<span style="color:#5a6580;font-size:20px;"> / 100</span><br/>'
        f'<span style="color:{label_color};font-size:22px;font-weight:600;'
        f'margin-top:6px;display:inline-block;">{label}</span><br/>'
        f'<span style="color:#5a6580;font-size:12px;margin-top:8px;'
        f'display:inline-block;">'
        f'{lat:.4f}, {lon:.4f} &mdash; radius {radius_km} km</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # 2. RADAR CHART
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown("### Health Dimensions Radar")
    radar_fig = build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="heageo_pchart1")

    # ══════════════════════════════════════════════════════════════════════════
    # 3. METRIC CARDS -- 4+3 layout
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown("### Dimension Scores")

    # Row 1: 4 cards
    r1c1, r1c2, r1c3, r1c4 = st.columns(4)

    with r1c1:
        st.markdown(
            _render_score_card(
                "Healthcare Access",
                scores["healthcare"]["score"],
                HEALTH_COMPONENTS["healthcare"]["color"],
                f"Hospitals: {hc_details.get('hospitals', 0)} | "
                f"Clinics: {hc_details.get('clinics', 0)}<br/>"
                f"Pharmacies: {hc_details.get('pharmacies', 0)} | "
                f"Doctors: {hc_details.get('doctors', 0)}<br/>"
                f"Total: {hc_details.get('total_facilities', 0)} facilities",
            ),
            unsafe_allow_html=True,
        )

    with r1c2:
        st.markdown(
            _render_score_card(
                "Disease Vector Risk",
                scores["disease_vector"]["score"],
                HEALTH_COMPONENTS["disease_vector"]["color"],
                f"Mosquito factor: {dv_details.get('mosquito_factor', 0)}<br/>"
                f"Tick factor: {dv_details.get('tick_factor', 0)}<br/>"
                f"Zone: {dv_details.get('latitude_zone', 'N/A')}<br/>"
                f"Temp: {dv_details.get('temperature_c', 0)}&deg;C | "
                f"Humidity: {dv_details.get('humidity_pct', 0)}%",
            ),
            unsafe_allow_html=True,
        )

    with r1c3:
        st.markdown(
            _render_score_card(
                "Air Quality Health",
                scores["air_quality"]["score"],
                HEALTH_COMPONENTS["air_quality"]["color"],
                f"AQI: {aq_details.get('us_aqi', 0)} "
                f"({aq_details.get('aqi_category', 'N/A')})<br/>"
                f"PM2.5: {aq_details.get('pm2_5', 0)} &mu;g/m&sup3;<br/>"
                f"PM10: {aq_details.get('pm10', 0)} &mu;g/m&sup3;<br/>"
                f"Ozone: {aq_details.get('ozone', 0)} &mu;g/m&sup3;",
            ),
            unsafe_allow_html=True,
        )

    with r1c4:
        st.markdown(
            _render_score_card(
                "Water Safety",
                scores["water_safety"]["score"],
                HEALTH_COMPONENTS["water_safety"]["color"],
                f"Treatment works: {ws_details.get('treatment_works', 0)}<br/>"
                f"Springs: {ws_details.get('springs', 0)} | "
                f"Wells: {ws_details.get('wells', 0)}<br/>"
                f"Waterways: {ws_details.get('waterways', 0)} | "
                f"Water bodies: {ws_details.get('water_bodies', 0)}",
            ),
            unsafe_allow_html=True,
        )

    # Row 2: 3 cards
    r2c1, r2c2, r2c3 = st.columns(3)

    with r2c1:
        st.markdown(
            _render_score_card(
                "Climate Health",
                scores["climate_health"]["score"],
                HEALTH_COMPONENTS["climate_health"]["color"],
                f"Temp: {ch_details.get('temperature_c', 0)}&deg;C<br/>"
                f"UV: {ch_details.get('uv_index', 0)} "
                f"({ch_details.get('uv_category', 'N/A')})<br/>"
                f"Heat stress: {ch_details.get('heat_stress', 'Low')}<br/>"
                f"Cold stress: {ch_details.get('cold_stress', 'Low')}<br/>"
                f"Elevation: {ch_details.get('elevation_m', 0):.0f} m",
            ),
            unsafe_allow_html=True,
        )

    with r2c2:
        st.markdown(
            _render_score_card(
                "Environmental Toxins",
                scores["env_toxins"]["score"],
                HEALTH_COMPONENTS["env_toxins"]["color"],
                f"Industrial: {et_details.get('industrial_zones', 0)} | "
                f"Quarries: {et_details.get('quarries', 0)}<br/>"
                f"Landfills: {et_details.get('landfills', 0)} | "
                f"Military: {et_details.get('military_areas', 0)}<br/>"
                f"Soil pH: {et_details.get('avg_soil_ph', 7.0)} "
                f"(risk: {et_details.get('ph_contamination_risk', 'Low')})",
            ),
            unsafe_allow_html=True,
        )

    with r2c3:
        st.markdown(
            _render_score_card(
                "Wellness Score",
                scores["wellness"]["score"],
                HEALTH_COMPONENTS["wellness"]["color"],
                f"Parks: {wl_details.get('parks', 0)} | "
                f"Gardens: {wl_details.get('gardens', 0)}<br/>"
                f"Nature reserves: {wl_details.get('nature_reserves', 0)}<br/>"
                f"Fitness: {wl_details.get('fitness_centres', 0)} | "
                f"Pools: {wl_details.get('swimming_pools', 0)}<br/>"
                f"Green spaces: {wl_details.get('green_space_total', 0)} total",
            ),
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 4. AQI GAUGE CHART
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown("### Air Quality Index Gauge")
    gauge_c1, gauge_c2 = st.columns([1.2, 1])

    with gauge_c1:
        aqi_gauge = build_aqi_gauge(aq_details.get("us_aqi", 0))
        st.plotly_chart(aqi_gauge, use_container_width=True, key="heageo_pchart2")

    with gauge_c2:
        st.markdown(
            f'<div style="background:rgba(26,26,46,0.85);border:1px solid #2a3550;'
            f'border-radius:12px;padding:16px;">'
            f'<h5 style="color:#e8ecf4;margin:0 0 12px 0;">Pollutant Breakdown</h5>'
            f'<table style="width:100%;color:#8b97b0;font-size:12px;">'
            f'<tr><td>PM2.5</td><td style="text-align:right;color:#e8ecf4;">'
            f'{aq_details.get("pm2_5", 0)} &mu;g/m&sup3;</td></tr>'
            f'<tr><td>PM10</td><td style="text-align:right;color:#e8ecf4;">'
            f'{aq_details.get("pm10", 0)} &mu;g/m&sup3;</td></tr>'
            f'<tr><td>Ozone (O&sub3;)</td><td style="text-align:right;color:#e8ecf4;">'
            f'{aq_details.get("ozone", 0)} &mu;g/m&sup3;</td></tr>'
            f'<tr><td>NO&sub2;</td><td style="text-align:right;color:#e8ecf4;">'
            f'{aq_details.get("no2", 0)} &mu;g/m&sup3;</td></tr>'
            f'<tr><td>SO&sub2;</td><td style="text-align:right;color:#e8ecf4;">'
            f'{aq_details.get("so2", 0)} &mu;g/m&sup3;</td></tr>'
            f'<tr><td>CO</td><td style="text-align:right;color:#e8ecf4;">'
            f'{aq_details.get("co", 0)} &mu;g/m&sup3;</td></tr>'
            f'</table></div>',
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # 5. HEALTHCARE FACILITIES BAR CHART
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown("### Healthcare Facilities by Type")
    fac_chart = build_facilities_bar_chart(hc_details)
    st.plotly_chart(fac_chart, use_container_width=True, key="heageo_pchart3")

    # ══════════════════════════════════════════════════════════════════════════
    # 6. HEALTH RISK SUMMARY -- Key Findings
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown("### Health Risk Summary")

    findings = []

    # Healthcare access finding
    if hc_score < 30:
        findings.append(
            ("Critical", "#ef4444",
             "Very limited healthcare access. "
             f"Only {hc_details.get('total_facilities', 0)} facility(ies) found "
             f"within {radius_km} km.")
        )
    elif hc_score < 60:
        findings.append(
            ("Warning", "#f59e0b",
             "Moderate healthcare coverage. Consider proximity to larger medical centers. "
             f"{hc_details.get('hospitals', 0)} hospital(s) available.")
        )
    else:
        findings.append(
            ("Good", "#22c55e",
             f"Strong healthcare infrastructure with {hc_details.get('total_facilities', 0)} "
             f"facilities including {hc_details.get('hospitals', 0)} hospital(s).")
        )

    # Disease vector finding
    if dv_score < 40:
        findings.append(
            ("Warning", "#f59e0b",
             f"High disease vector risk. {dv_details.get('latitude_zone', 'N/A')} zone "
             f"with temp {dv_details.get('temperature_c', 0):.0f}C and "
             f"humidity {dv_details.get('humidity_pct', 0):.0f}%. "
             "Mosquito and tick-borne diseases may be prevalent.")
        )
    elif dv_score >= 80:
        findings.append(
            ("Good", "#22c55e",
             "Low disease vector risk. Climate conditions are unfavorable for "
             "common disease-carrying arthropods.")
        )

    # Air quality finding
    aqi_val = aq_details.get("us_aqi", 0)
    if aqi_val > 150:
        findings.append(
            ("Critical", "#ef4444",
             f"Unhealthy air quality (AQI {aqi_val:.0f}). "
             f"PM2.5: {aq_details.get('pm2_5', 0)} ug/m3. "
             "Respiratory risk for sensitive groups.")
        )
    elif aqi_val > 100:
        findings.append(
            ("Warning", "#f59e0b",
             f"Moderate air quality concern (AQI {aqi_val:.0f}). "
             "Sensitive individuals should limit prolonged outdoor exertion.")
        )
    elif aq_score >= 75:
        findings.append(
            ("Good", "#22c55e",
             f"Good air quality (AQI {aqi_val:.0f}). Safe for outdoor activities.")
        )

    # Water safety finding
    if ws_score < 30:
        findings.append(
            ("Warning", "#f59e0b",
             "Limited water infrastructure detected. "
             f"Only {ws_details.get('total_water_features', 0)} water features found. "
             "Water quality verification recommended.")
        )

    # Climate health finding
    temp_val = ch_details.get("temperature_c", 0)
    if temp_val > 35:
        findings.append(
            ("Critical", "#ef4444",
             f"Heat stress risk: {temp_val:.1f}C. "
             "Hydration and shade are critical. Limit outdoor exposure.")
        )
    elif temp_val < -10:
        findings.append(
            ("Warning", "#f59e0b",
             f"Cold stress risk: {temp_val:.1f}C. "
             "Hypothermia risk -- adequate insulation required.")
        )

    uv_val = ch_details.get("uv_index", 0)
    if uv_val > 8:
        findings.append(
            ("Warning", "#f59e0b",
             f"Very high UV index ({uv_val:.1f}). "
             "Sun protection essential -- risk of skin damage within minutes.")
        )

    # Environmental toxins finding
    hazardous = et_details.get("total_hazardous_sites", 0)
    if hazardous > 5:
        findings.append(
            ("Warning", "#f59e0b",
             f"{hazardous} potentially hazardous sites (industrial, quarries, "
             "landfills) detected within the analysis area.")
        )
    elif hazardous == 0 and et_score >= 80:
        findings.append(
            ("Good", "#22c55e",
             "No industrial or hazardous sites detected. "
             "Low environmental contamination risk.")
        )

    # Wellness finding
    green_total = wl_details.get("green_space_total", 0)
    if green_total > 5:
        findings.append(
            ("Good", "#22c55e",
             f"Abundant green spaces ({green_total} parks/gardens/reserves). "
             "Beneficial for mental and physical health.")
        )
    elif green_total == 0:
        findings.append(
            ("Info", "#6366f1",
             "No green spaces detected in the area. "
             "Limited access to nature for wellness.")
        )

    # Render findings
    if not findings:
        findings.append(
            ("Info", "#6366f1", "Analysis complete. No significant health risks identified.")
        )

    for severity, color, text in findings:
        icon = (
            "!!" if severity == "Critical"
            else "!" if severity == "Warning"
            else "i" if severity == "Info"
            else "+"
        )
        st.markdown(
            f'<div style="background:rgba(26,26,46,0.85);border-left:4px solid {color};'
            f'border-radius:0 8px 8px 0;padding:12px 16px;margin:6px 0;'
            f'backdrop-filter:blur(16px);">'
            f'<span style="color:{color};font-weight:bold;font-size:12px;'
            f'margin-right:8px;">[{severity}]</span>'
            f'<span style="color:#e8ecf4;font-size:13px;">{text}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # FOOTER -- Score Breakdown Table
    # ══════════════════════════════════════════════════════════════════════════

    st.markdown("### Score Breakdown")

    breakdown_rows = ""
    for key in HEALTH_COMPONENTS:
        comp = HEALTH_COMPONENTS[key]
        s = scores[key]["score"]
        w = comp["weight"]
        weighted = round(s * w, 1)
        bar_w = max(0, min(100, s))
        grade_color = "#22c55e" if s >= 70 else ("#f59e0b" if s >= 40 else "#ef4444")
        breakdown_rows += (
            f'<tr>'
            f'<td style="padding:8px;color:#e8ecf4;font-size:13px;">'
            f'<span style="display:inline-block;width:10px;height:10px;'
            f'border-radius:50%;background:{comp["color"]};margin-right:8px;'
            f'vertical-align:middle;"></span>{comp["name"]}</td>'
            f'<td style="padding:8px;text-align:center;">'
            f'<span style="color:{grade_color};font-weight:bold;">{s:.0f}</span></td>'
            f'<td style="padding:8px;text-align:center;color:#5a6580;">'
            f'{w:.0%}</td>'
            f'<td style="padding:8px;text-align:center;color:#e8ecf4;">'
            f'{weighted:.1f}</td>'
            f'<td style="padding:8px;width:120px;">'
            f'<div style="background:#0f172a;border-radius:4px;height:8px;">'
            f'<div style="width:{bar_w:.0f}%;background:{comp["color"]};'
            f'height:100%;border-radius:4px;"></div></div></td>'
            f'</tr>'
        )

    st.markdown(
        f'<div style="background:rgba(26,26,46,0.85);border:1px solid #2a3550;'
        f'border-radius:12px;padding:16px;overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr>'
        f'<th style="padding:8px;color:#8b97b0;font-size:12px;text-align:left;'
        f'border-bottom:1px solid #2a3550;">Dimension</th>'
        f'<th style="padding:8px;color:#8b97b0;font-size:12px;text-align:center;'
        f'border-bottom:1px solid #2a3550;">Score</th>'
        f'<th style="padding:8px;color:#8b97b0;font-size:12px;text-align:center;'
        f'border-bottom:1px solid #2a3550;">Weight</th>'
        f'<th style="padding:8px;color:#8b97b0;font-size:12px;text-align:center;'
        f'border-bottom:1px solid #2a3550;">Weighted</th>'
        f'<th style="padding:8px;color:#8b97b0;font-size:12px;text-align:left;'
        f'border-bottom:1px solid #2a3550;">Bar</th>'
        f'</tr></thead>'
        f'<tbody>{breakdown_rows}</tbody>'
        f'<tfoot><tr style="border-top:2px solid #2a3550;">'
        f'<td style="padding:10px;color:#e8ecf4;font-weight:bold;">Overall Index</td>'
        f'<td style="padding:10px;text-align:center;color:{label_color};'
        f'font-weight:bold;font-size:16px;">{overall}</td>'
        f'<td colspan="3" style="padding:10px;text-align:center;color:{label_color};'
        f'font-weight:bold;font-size:14px;">{label}</td>'
        f'</tr></tfoot>'
        f'</table></div>',
        unsafe_allow_html=True,
    )
