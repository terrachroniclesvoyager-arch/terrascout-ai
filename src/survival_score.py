"""
Survival Score AI -- Wilderness survival assessment combining water,
shelter, food, climate, navigation, hazards & resource availability.
Uses: Overpass, Open-Meteo, SoilGrids, iNaturalist.
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
    fetch_biodiversity,
    fetch_landuse_infrastructure,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SURVIVAL_COMPONENTS = {
    "water": {"name": "Water Availability", "color": "#3b82f6", "weight": 0.20},
    "shelter": {"name": "Shelter Potential", "color": "#f59e0b", "weight": 0.15},
    "food": {"name": "Food Sources", "color": "#22c55e", "weight": 0.15},
    "climate": {"name": "Climate Survivability", "color": "#ef4444", "weight": 0.15},
    "navigation": {"name": "Navigation & Rescue", "color": "#8b5cf6", "weight": 0.10},
    "hazards": {"name": "Natural Hazards", "color": "#ec4899", "weight": 0.10},
    "resources": {"name": "Resource Availability", "color": "#10b981", "weight": 0.15},
}

CLASSIFICATION_BANDS = [
    (85, 100, "Excellent Survival Zone", "#10b981"),
    (65, 84, "Good Survival Potential", "#22c55e"),
    (45, 64, "Moderate -- Prepared Only", "#f59e0b"),
    (25, 44, "Challenging -- Expert Only", "#f97316"),
    (0, 24, "Extreme -- Not Recommended", "#ef4444"),
]

# ---------------------------------------------------------------------------
# Data-fetching helpers
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def fetch_survival_features(lat, lon, radius=3000):
    """Fetch survival-relevant features from Overpass."""
    query = f"""
    [out:json][timeout:30];
    (
      node["natural"="spring"](around:{radius},{lat},{lon});
      node["natural"="cave_entrance"](around:{radius},{lat},{lon});
      way["natural"="wood"](around:{radius},{lat},{lon});
      way["landuse"="forest"](around:{radius},{lat},{lon});
      way["waterway"](around:{radius},{lat},{lon});
      node["natural"="peak"](around:{radius},{lat},{lon});
      way["natural"="wetland"](around:{radius},{lat},{lon});
      way["natural"="cliff"](around:{radius},{lat},{lon});
      node["natural"="rock"](around:{radius},{lat},{lon});
      way["natural"="water"](around:{radius},{lat},{lon});
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
        logger.warning(f"Survival features error: {e}")
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_roads_and_paths(lat, lon, radius=5000):
    """Fetch roads and paths for navigation/rescue scoring."""
    query = f"""
    [out:json][timeout:25];
    (
      way["highway"](around:{radius},{lat},{lon});
    );
    out body;
    """
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=25,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning(f"Roads fetch error: {e}")
        return {"elements": []}


# ---------------------------------------------------------------------------
# Feature-counting helpers
# ---------------------------------------------------------------------------


def _count_elements_by_tag(elements, tag_key, tag_value):
    """Count Overpass elements where tags[tag_key] == tag_value."""
    count = 0
    for el in elements:
        tags = el.get("tags", {})
        if tags.get(tag_key) == tag_value:
            count += 1
    return count


def _count_elements_with_tag(elements, tag_key):
    """Count Overpass elements that have a given tag key (any value)."""
    count = 0
    for el in elements:
        tags = el.get("tags", {})
        if tag_key in tags:
            count += 1
    return count


def _extract_soil_fertility(soil_data):
    """Return a 0-100 fertility score from SoilGrids data.

    Considers organic-carbon (soc), nitrogen, and CEC at 0-5 cm depth.
    Higher values mean more fertile soil.
    """
    layers = soil_data.get("properties", {}).get("layers", [])
    soc_val = None
    nitrogen_val = None
    cec_val = None
    for layer in layers:
        name = layer.get("name", "")
        for depth_entry in layer.get("depths", []):
            label = depth_entry.get("label", "")
            if "0-5" not in label:
                continue
            raw = depth_entry.get("values", {}).get("mean")
            if raw is None:
                continue
            if name == "soc":
                soc_val = raw / 10.0       # g/kg
            elif name == "nitrogen":
                nitrogen_val = raw / 100.0  # g/kg
            elif name == "cec":
                cec_val = raw / 10.0        # cmol/kg
    # Normalise each component to 0-33 range, sum for 0-99 max
    score = 0.0
    if soc_val is not None:
        score += min(soc_val / 60.0 * 33.0, 33.0)
    if nitrogen_val is not None:
        score += min(nitrogen_val / 5.0 * 33.0, 33.0)
    if cec_val is not None:
        score += min(cec_val / 40.0 * 33.0, 33.0)
    return min(round(score, 1), 100.0)


# ---------------------------------------------------------------------------
# Scoring functions -- one per dimension
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def score_water(lat, lon, radius=5000):
    """Water Availability score (0-100).

    springs*20 + streams*10 + rivers*15 + lakes*15 + rainfall_bonus.
    """
    water_data = fetch_water_features(lat, lon, radius=radius)
    weather_data = fetch_weather_data(lat, lon)
    survival_data = fetch_survival_features(lat, lon, radius=radius)

    water_els = water_data.get("elements", [])
    surv_els = survival_data.get("elements", [])

    springs = _count_elements_by_tag(water_els, "natural", "spring")
    springs += _count_elements_by_tag(surv_els, "natural", "spring")

    streams = 0
    rivers = 0
    for el in water_els + surv_els:
        tags = el.get("tags", {})
        ww = tags.get("waterway", "")
        if ww == "stream":
            streams += 1
        elif ww in ("river", "canal"):
            rivers += 1

    lakes = _count_elements_by_tag(water_els, "natural", "water")
    lakes += _count_elements_by_tag(surv_els, "natural", "water")

    # Rainfall bonus from current precipitation + humidity
    current = weather_data.get("current", {})
    precip = current.get("precipitation", 0) or 0
    humidity = current.get("relative_humidity_2m", 50) or 50
    rainfall_bonus = min(precip * 5.0, 15.0) + max(0, (humidity - 60) * 0.2)

    raw = springs * 20 + streams * 10 + rivers * 15 + lakes * 15 + rainfall_bonus
    score = min(round(raw, 1), 100.0)

    details = {
        "springs": springs,
        "streams": streams,
        "rivers": rivers,
        "lakes": lakes,
        "precipitation_mm": precip,
        "humidity_pct": humidity,
        "rainfall_bonus": round(rainfall_bonus, 1),
    }
    return max(score, 0.0), details


@st.cache_data(ttl=1800)
def score_shelter(lat, lon, radius=3000):
    """Shelter Potential score (0-100).

    caves*25 + forests*8 + rocks*5 + cliff_overhangs*10 + windbreak bonus.
    """
    surv_data = fetch_survival_features(lat, lon, radius=radius)
    els = surv_data.get("elements", [])

    caves = _count_elements_by_tag(els, "natural", "cave_entrance")
    forests = (_count_elements_by_tag(els, "natural", "wood")
               + _count_elements_by_tag(els, "landuse", "forest"))
    rocks = _count_elements_by_tag(els, "natural", "rock")
    cliffs = _count_elements_by_tag(els, "natural", "cliff")

    # Terrain variation proxy: peaks imply varied terrain = windbreak
    peaks = _count_elements_by_tag(els, "natural", "peak")
    windbreak_bonus = min(peaks * 5.0, 15.0)

    raw = caves * 25 + forests * 8 + rocks * 5 + cliffs * 10 + windbreak_bonus
    score = min(round(raw, 1), 100.0)

    details = {
        "caves": caves,
        "forests": forests,
        "rocks": rocks,
        "cliffs": cliffs,
        "peaks_windbreak": peaks,
        "windbreak_bonus": round(windbreak_bonus, 1),
    }
    return max(score, 0.0), details


@st.cache_data(ttl=1800)
def score_food(lat, lon, radius=5000):
    """Food Sources score (0-100).

    biodiversity_species*2 + soil_fertility_score + fishing_waters*10.
    """
    bio_data = fetch_biodiversity(lat, lon, radius_km=max(1, radius // 1000))
    soil_data = fetch_soil_data(lat, lon)
    water_data = fetch_water_features(lat, lon, radius=radius)

    species_total = bio_data.get("total_results", 0) or 0
    biodiversity_pts = min(species_total * 2.0, 40.0)

    fertility = _extract_soil_fertility(soil_data)
    fertility_pts = fertility * 0.3  # scale 0-30

    # Fishing waters: rivers + lakes
    water_els = water_data.get("elements", [])
    fishing = 0
    for el in water_els:
        tags = el.get("tags", {})
        if tags.get("waterway") in ("river", "stream", "canal"):
            fishing += 1
        if tags.get("natural") == "water":
            fishing += 1
    fishing_pts = min(fishing * 10.0, 30.0)

    raw = biodiversity_pts + fertility_pts + fishing_pts
    score = min(round(raw, 1), 100.0)

    details = {
        "species_observed": species_total,
        "biodiversity_pts": round(biodiversity_pts, 1),
        "soil_fertility": round(fertility, 1),
        "fertility_pts": round(fertility_pts, 1),
        "fishing_waters": fishing,
        "fishing_pts": round(fishing_pts, 1),
    }
    return max(score, 0.0), details


@st.cache_data(ttl=1800)
def score_climate(lat, lon):
    """Climate Survivability score (0-100).

    Penalise extremes.  Ideal 10-25 deg-C.
    score = max(0, 100 - abs(avg_temp-18)*4 - wind_penalty - humidity_penalty).
    """
    weather_data = fetch_weather_data(lat, lon)
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    temp_now = current.get("temperature_2m", 18) or 18
    daily_max = daily.get("temperature_2m_max", [])
    daily_min = daily.get("temperature_2m_min", [])
    valid_temps = [t for t in (daily_max + daily_min) if t is not None]
    avg_temp = sum(valid_temps) / len(valid_temps) if valid_temps else temp_now

    wind = current.get("wind_speed_10m", 0) or 0
    humidity = current.get("relative_humidity_2m", 50) or 50

    temp_penalty = abs(avg_temp - 18.0) * 4.0
    wind_penalty = max(0, (wind - 20) * 1.5)
    humidity_penalty = max(0, abs(humidity - 55) - 25) * 0.8

    raw = 100.0 - temp_penalty - wind_penalty - humidity_penalty
    score = min(max(round(raw, 1), 0.0), 100.0)

    # Growing season estimate (months with avg > 5 C)
    growing_months = 0
    if daily_max and daily_min:
        day_avgs = []
        for i in range(min(len(daily_max), len(daily_min))):
            hi = daily_max[i] if daily_max[i] is not None else 15
            lo = daily_min[i] if daily_min[i] is not None else 5
            day_avgs.append((hi + lo) / 2.0)
        above_5 = sum(1 for t in day_avgs if t > 5)
        growing_months = round(above_5 / max(len(day_avgs), 1) * 12, 1)

    details = {
        "avg_temp_c": round(avg_temp, 1),
        "wind_kmh": round(wind, 1),
        "humidity_pct": round(humidity, 1),
        "temp_penalty": round(temp_penalty, 1),
        "wind_penalty": round(wind_penalty, 1),
        "humidity_penalty": round(humidity_penalty, 1),
        "est_growing_months": growing_months,
    }
    return score, details


@st.cache_data(ttl=1800)
def score_navigation(lat, lon, radius=5000):
    """Navigation & Rescue score (0-100).

    nearby_roads*5 + peaks*10 (vantage points) + terrain_clarity.
    """
    road_data = fetch_roads_and_paths(lat, lon, radius=radius)
    surv_data = fetch_survival_features(lat, lon, radius=radius)

    road_els = road_data.get("elements", [])
    surv_els = surv_data.get("elements", [])

    # Count meaningful road types
    roads = 0
    for el in road_els:
        tags = el.get("tags", {})
        hw = tags.get("highway", "")
        if hw in ("motorway", "trunk", "primary", "secondary", "tertiary",
                   "unclassified", "residential", "service", "track", "path"):
            roads += 1

    peaks = _count_elements_by_tag(surv_els, "natural", "peak")

    # Terrain clarity: fewer dense forests means better visibility
    forests = (_count_elements_by_tag(surv_els, "natural", "wood")
               + _count_elements_by_tag(surv_els, "landuse", "forest"))
    terrain_clarity = max(0, 20 - forests * 2)

    raw = min(roads * 5.0, 50.0) + peaks * 10.0 + terrain_clarity
    score = min(round(raw, 1), 100.0)

    details = {
        "roads_paths": roads,
        "peaks_vantage": peaks,
        "forests_blocking": forests,
        "terrain_clarity_pts": round(terrain_clarity, 1),
    }
    return max(score, 0.0), details


@st.cache_data(ttl=1800)
def score_hazards(lat, lon, radius=3000):
    """Natural Hazards score (0-100, INVERTED: lower hazard = higher score).

    100 - (flood_risk + landslide_risk + steep_cliffs*5 + wetlands_as_hazard*3).
    """
    surv_data = fetch_survival_features(lat, lon, radius=radius)
    water_data = fetch_water_features(lat, lon, radius=radius)

    surv_els = surv_data.get("elements", [])
    water_els = water_data.get("elements", [])

    # Flood risk proxy: number of waterways and wetlands near target
    waterways = _count_elements_with_tag(water_els, "waterway")
    wetlands = _count_elements_by_tag(surv_els, "natural", "wetland")
    flood_risk = min(waterways * 3.0, 25.0)

    # Landslide risk proxy: cliffs + steep terrain
    cliffs = _count_elements_by_tag(surv_els, "natural", "cliff")
    peaks = _count_elements_by_tag(surv_els, "natural", "peak")
    landslide_risk = min((cliffs + peaks) * 4.0, 25.0)

    cliff_penalty = cliffs * 5.0
    wetland_penalty = wetlands * 3.0

    total_hazard = flood_risk + landslide_risk + cliff_penalty + wetland_penalty
    raw = 100.0 - total_hazard
    score = min(max(round(raw, 1), 0.0), 100.0)

    details = {
        "waterways": waterways,
        "wetlands": wetlands,
        "cliffs": cliffs,
        "peaks_steep": peaks,
        "flood_risk_pts": round(flood_risk, 1),
        "landslide_risk_pts": round(landslide_risk, 1),
        "cliff_penalty": round(cliff_penalty, 1),
        "wetland_penalty": round(wetland_penalty, 1),
        "total_hazard_deduction": round(total_hazard, 1),
    }
    return score, details


@st.cache_data(ttl=1800)
def score_resources(lat, lon, radius=3000):
    """Resource Availability score (0-100).

    forests*10 (firewood + building) + rocks*5 (tools) + biodiversity*2 (medicinal).
    """
    surv_data = fetch_survival_features(lat, lon, radius=radius)
    bio_data = fetch_biodiversity(lat, lon, radius_km=max(1, radius // 1000))

    surv_els = surv_data.get("elements", [])

    forests = (_count_elements_by_tag(surv_els, "natural", "wood")
               + _count_elements_by_tag(surv_els, "landuse", "forest"))
    rocks = _count_elements_by_tag(surv_els, "natural", "rock")

    species_total = bio_data.get("total_results", 0) or 0

    forest_pts = min(forests * 10.0, 50.0)
    rock_pts = min(rocks * 5.0, 25.0)
    medicinal_pts = min(species_total * 2.0, 25.0)

    raw = forest_pts + rock_pts + medicinal_pts
    score = min(round(raw, 1), 100.0)

    details = {
        "forests_firewood": forests,
        "rocks_tools": rocks,
        "species_medicinal_proxy": species_total,
        "forest_pts": round(forest_pts, 1),
        "rock_pts": round(rock_pts, 1),
        "medicinal_pts": round(medicinal_pts, 1),
    }
    return max(score, 0.0), details


# ---------------------------------------------------------------------------
# Composite score
# ---------------------------------------------------------------------------


def compute_all_scores(lat, lon, radius=3000):
    """Compute all 7 survival dimension scores and the weighted total."""
    water_score, water_detail = score_water(lat, lon, radius=radius)
    shelter_score, shelter_detail = score_shelter(lat, lon, radius=radius)
    food_score, food_detail = score_food(lat, lon, radius=radius)
    climate_score, climate_detail = score_climate(lat, lon)
    nav_score, nav_detail = score_navigation(lat, lon, radius=radius)
    hazard_score, hazard_detail = score_hazards(lat, lon, radius=radius)
    resource_score, resource_detail = score_resources(lat, lon, radius=radius)

    scores = {
        "water": {"score": water_score, "details": water_detail},
        "shelter": {"score": shelter_score, "details": shelter_detail},
        "food": {"score": food_score, "details": food_detail},
        "climate": {"score": climate_score, "details": climate_detail},
        "navigation": {"score": nav_score, "details": nav_detail},
        "hazards": {"score": hazard_score, "details": hazard_detail},
        "resources": {"score": resource_score, "details": resource_detail},
    }

    weighted_total = 0.0
    for key, meta in SURVIVAL_COMPONENTS.items():
        weighted_total += scores[key]["score"] * meta["weight"]

    return scores, round(weighted_total, 1)


def classify_score(total):
    """Return (label, color) classification for a total survival score."""
    for low, high, label, color in CLASSIFICATION_BANDS:
        if low <= total <= high:
            return label, color
    return "Extreme -- Not Recommended", "#ef4444"


# ---------------------------------------------------------------------------
# Visualisation helpers
# ---------------------------------------------------------------------------


def build_radar_chart(scores):
    """Build a Plotly radar chart of the 7 survival dimensions."""
    categories = []
    values = []
    colors_list = []
    for key in SURVIVAL_COMPONENTS:
        meta = SURVIVAL_COMPONENTS[key]
        categories.append(meta["name"])
        values.append(scores[key]["score"])
        colors_list.append(meta["color"])

    # Close the radar loop
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(6,182,212,0.18)",
        line=dict(color="#06b6d4", width=2),
        marker=dict(size=7, color="#06b6d4"),
        name="Survival Score",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(15,23,42,0.65)",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color="#5a6580", size=10),
                gridcolor="#2a3550",
            ),
            angularaxis=dict(
                tickfont=dict(color="#e8ecf4", size=11),
                gridcolor="#2a3550",
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=420,
    )
    return fig


def build_water_sources_pie(water_details):
    """Build a Plotly pie chart of water source types."""
    labels = []
    values = []
    source_map = {
        "Springs": water_details.get("springs", 0),
        "Streams": water_details.get("streams", 0),
        "Rivers": water_details.get("rivers", 0),
        "Lakes/Ponds": water_details.get("lakes", 0),
    }
    for lbl, val in source_map.items():
        if val > 0:
            labels.append(lbl)
            values.append(val)

    if not values:
        return None

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        marker=dict(colors=["#3b82f6", "#06b6d4", "#8b5cf6", "#10b981"]),
        textinfo="label+value",
        textfont=dict(color="#e8ecf4", size=12),
    )])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(font=dict(color="#8b97b0", size=11)),
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
    )
    return fig


# ---------------------------------------------------------------------------
# Survival tips generator
# ---------------------------------------------------------------------------


def generate_survival_tips(scores, total):
    """Return a list of survival tips based on dimension scores."""
    tips = []

    water_s = scores["water"]["score"]
    shelter_s = scores["shelter"]["score"]
    food_s = scores["food"]["score"]
    climate_s = scores["climate"]["score"]
    nav_s = scores["navigation"]["score"]
    hazard_s = scores["hazards"]["score"]
    resource_s = scores["resources"]["score"]

    if water_s < 30:
        tips.append(
            "CRITICAL: Water sources are extremely scarce. "
            "Carry at least 3 litres per person per day and bring "
            "purification supplies."
        )
    elif water_s < 60:
        tips.append(
            "Water is limited. Locate the nearest stream or spring "
            "immediately upon arrival and purify before drinking."
        )
    else:
        tips.append(
            "Multiple water sources detected. Boil or filter all "
            "natural water to avoid pathogens."
        )

    if shelter_s < 30:
        tips.append(
            "CRITICAL: Very few natural shelters. Bring a tent "
            "or tarp. Exposure risk is high."
        )
    elif shelter_s < 60:
        tips.append(
            "Some shelter options exist (forest canopy or rock "
            "formations). Scout for windbreaks early."
        )
    else:
        tips.append(
            "Good shelter potential with caves, dense forest, "
            "or rock overhangs. Inspect caves for animal inhabitants."
        )

    if food_s < 30:
        tips.append(
            "CRITICAL: Food sources are very limited. Pack "
            "high-calorie rations for the entire stay."
        )
    elif food_s < 60:
        tips.append(
            "Moderate food potential. Supplement packed rations "
            "with foraging, but never eat unidentified plants."
        )

    if climate_s < 30:
        tips.append(
            "Extreme climate conditions detected. Bring layered "
            "clothing, sun/cold protection, and monitor weather."
        )
    elif climate_s < 60:
        tips.append(
            "Moderate climate risks. Temperature swings are "
            "possible -- pack for both warm and cold conditions."
        )

    if nav_s < 30:
        tips.append(
            "Navigation is very difficult. Carry a GPS device, "
            "compass, and detailed topographic maps."
        )

    if hazard_s < 50:
        tips.append(
            "Elevated natural hazards detected (flooding, "
            "landslides, steep terrain). Camp on high, stable ground."
        )

    if resource_s < 30:
        tips.append(
            "Limited natural resources for fire and construction. "
            "Bring fire-starting gear and cordage."
        )

    if total < 25:
        tips.append(
            "OVERALL: This area is EXTREMELY challenging for "
            "survival. Professional-grade equipment and expert "
            "wilderness skills are mandatory."
        )
    elif total < 45:
        tips.append(
            "OVERALL: Expert-level preparedness required. "
            "Do not enter alone. File a trip plan with authorities."
        )

    return tips


# ---------------------------------------------------------------------------
# Entry-point UI renderer
# ---------------------------------------------------------------------------


def render_survival_score_tab():
    """Render the Wilderness Survival Score tab UI."""

    # -- Tab header --
    st.markdown(
        '<div class="tab-header violet">'
        "<h4>Wilderness Survival Score</h4>"
        "<p>AI-powered wilderness survival assessment &mdash; "
        "water, shelter, food, climate, navigation, hazards &amp; resources</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # -- Location selector --
    c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="surv_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50

    with c2:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="surv_lat",
        )
    with c3:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="surv_lon",
        )

    radius = st.slider(
        "Search radius (m)", 1000, 10000, 3000,
        step=500, key="surv_radius",
    )

    run = st.button(
        "Compute Survival Score",
        type="primary",
        key="surv_run",
        use_container_width=True,
    )

    if not run:
        st.info(
            "Set coordinates and click **Compute Survival Score** "
            "to analyse wilderness survival potential."
        )
        return

    # ==================================================================
    # Compute all scores
    # ==================================================================
    progress = st.progress(0, text="Initialising survival analysis...")

    progress.progress(10, text="Scoring water availability...")
    # Trigger computation (cached after first call)
    scores, total = compute_all_scores(lat, lon, radius=radius)

    progress.progress(90, text="Building visualisations...")

    classification_label, classification_color = classify_score(total)

    progress.progress(100, text="Analysis complete!")

    # ==================================================================
    # 1. Header: classification banner
    # ==================================================================
    st.markdown("---")
    st.markdown(
        f'<div style="background:rgba(15,23,42,0.8);border:2px solid '
        f'{classification_color};border-radius:16px;padding:24px;'
        f'text-align:center;margin-bottom:18px;">'
        f'<span style="font-size:48px;font-weight:bold;color:'
        f'{classification_color};">{total}</span>'
        f'<span style="font-size:20px;color:#8b97b0;">/100</span><br/>'
        f'<span style="font-size:18px;color:{classification_color};'
        f'font-weight:600;">{classification_label}</span><br/>'
        f'<span style="font-size:12px;color:#5a6580;">'
        f'Weighted composite of 7 survival dimensions at '
        f'{lat:.4f}, {lon:.4f}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ==================================================================
    # 2. Radar chart
    # ==================================================================
    st.markdown("### Survival Dimensions Radar")
    radar_fig = build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="sursco_pchart1")

    # ==================================================================
    # 3. Seven metric cards
    # ==================================================================
    st.markdown("### Dimension Breakdown")

    for key in SURVIVAL_COMPONENTS:
        meta = SURVIVAL_COMPONENTS[key]
        dim_score = scores[key]["score"]
        dim_details = scores[key]["details"]
        dim_label, dim_color = classify_score(dim_score)

        st.markdown(
            f'<div style="background:rgba(15,23,42,0.65);border-left:4px solid '
            f'{meta["color"]};border-radius:0 12px 12px 0;padding:14px 18px;'
            f'margin:8px 0;backdrop-filter:blur(16px);">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;">'
            f'<span style="color:#e8ecf4;font-size:15px;font-weight:bold;">'
            f'{meta["name"]}</span>'
            f'<span style="color:{dim_color};font-size:22px;font-weight:bold;">'
            f'{dim_score}</span></div>'
            f'<div style="background:#1a2235;border-radius:6px;height:10px;'
            f'margin:8px 0;">'
            f'<div style="width:{min(dim_score, 100):.0f}%;'
            f'background:{meta["color"]};height:100%;border-radius:6px;">'
            f'</div></div>'
            f'<span style="color:#5a6580;font-size:11px;">'
            f'{dim_label} &mdash; weight: {meta["weight"]*100:.0f}%</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Expandable details
        with st.expander(f"Details: {meta['name']}"):
            detail_cols = st.columns(min(len(dim_details), 4))
            for idx, (dk, dv) in enumerate(dim_details.items()):
                col = detail_cols[idx % len(detail_cols)]
                display_key = dk.replace("_", " ").title()
                col.metric(display_key, f"{dv}")

    # ==================================================================
    # 4. Survival priorities (ranked list)
    # ==================================================================
    st.markdown("### Survival Priorities (Most Critical First)")

    ranked = sorted(
        SURVIVAL_COMPONENTS.keys(),
        key=lambda k: scores[k]["score"],
    )
    for rank, key in enumerate(ranked, 1):
        meta = SURVIVAL_COMPONENTS[key]
        s = scores[key]["score"]
        _, sc = classify_score(s)
        urgency = "CRITICAL" if s < 25 else ("HIGH" if s < 45 else
                  ("MODERATE" if s < 65 else "LOW"))
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:12px;'
            f'padding:6px 12px;margin:4px 0;background:rgba(15,23,42,0.5);'
            f'border-radius:8px;">'
            f'<span style="color:{sc};font-size:18px;font-weight:bold;'
            f'min-width:28px;">{rank}</span>'
            f'<span style="color:#e8ecf4;flex:1;">{meta["name"]}</span>'
            f'<span style="color:{sc};font-weight:600;font-size:13px;">'
            f'{urgency}</span>'
            f'<span style="color:{meta["color"]};font-weight:bold;">'
            f'{s}/100</span></div>',
            unsafe_allow_html=True,
        )

    # ==================================================================
    # 5. Water sources pie chart
    # ==================================================================
    st.markdown("### Water Sources Distribution")
    water_pie = build_water_sources_pie(scores["water"]["details"])
    if water_pie is not None:
        st.plotly_chart(water_pie, use_container_width=True, key="sursco_pchart2")
    else:
        st.info("No water sources detected within the search radius.")

    # ==================================================================
    # 6. Survival tips
    # ==================================================================
    st.markdown("### Key Survival Tips")
    tips = generate_survival_tips(scores, total)
    for tip in tips:
        is_critical = tip.startswith("CRITICAL") or tip.startswith("OVERALL")
        icon = "warning" if is_critical else "info"
        border_color = "#ef4444" if is_critical else "#2a3550"
        st.markdown(
            f'<div style="background:rgba(15,23,42,0.65);border:1px solid '
            f'{border_color};border-radius:10px;padding:12px 16px;'
            f'margin:6px 0;color:#e8ecf4;font-size:13px;">'
            f'{tip}</div>',
            unsafe_allow_html=True,
        )
