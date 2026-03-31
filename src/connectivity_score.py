"""
Connectivity & Digital Infrastructure AI -- comprehensive connectivity
assessment combining mobile coverage, internet infrastructure, signal
propagation, digital services & connectivity resilience.

Uses: Overpass API, Open Topo Data, Open-Meteo.
Part of TerraScout AI (271+ modules).
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
    fetch_weather_data,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

CONNECTIVITY_COMPONENTS = {
    "mobile_coverage": {
        "name": "Mobile Coverage",
        "color": "#3b82f6",
        "weight": 0.25,
    },
    "internet_infra": {
        "name": "Internet Infrastructure",
        "color": "#8b5cf6",
        "weight": 0.25,
    },
    "signal_propagation": {
        "name": "Signal Propagation",
        "color": "#06b6d4",
        "weight": 0.15,
    },
    "digital_services": {
        "name": "Digital Services",
        "color": "#f59e0b",
        "weight": 0.15,
    },
    "connectivity_resilience": {
        "name": "Connectivity Resilience",
        "color": "#10b981",
        "weight": 0.20,
    },
}

CLASSIFICATION_BANDS = [
    (85, 100, "Excellent Connectivity", "#10b981"),
    (70, 84, "Strong Connectivity", "#22c55e"),
    (50, 69, "Moderate Connectivity", "#f59e0b"),
    (30, 49, "Weak Connectivity", "#f97316"),
    (0, 29, "Poor / No Connectivity", "#ef4444"),
]

# ---------------------------------------------------------------------------
# Data-fetching helpers
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def fetch_connectivity_data(lat, lon, radius=5000):
    """Fetch telecom and digital infrastructure features from Overpass."""
    query = f"""
    [out:json][timeout:30];
    (
      node["man_made"="tower"]["tower:type"="communication"](around:{radius},{lat},{lon});
      node["man_made"="mast"](around:{radius},{lat},{lon});
      node["telecom"](around:{radius},{lat},{lon});
      way["telecom"](around:{radius},{lat},{lon});
      node["man_made"="data_center"](around:{radius},{lat},{lon});
      node["amenity"="internet_cafe"](around:{radius},{lat},{lon});
      node["office"="telecommunication"](around:{radius},{lat},{lon});
      way["utility"="fibre_optic_cable"](around:{radius},{lat},{lon});
      node["power"~"substation|transformer"](around:{radius},{lat},{lon});
      node["shop"="electronics"](around:{radius},{lat},{lon});
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
        logger.warning(f"Connectivity data fetch error: {e}")
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_elevation_data(lat, lon):
    """Fetch elevation for a single point from Open Topo Data."""
    try:
        params = {"locations": f"{lat},{lon}"}
        resp = requests.get(OPEN_TOPO_API, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "OK" and len(data.get("results", [])) > 0:
            elev = data["results"][0].get("elevation")
            if elev is not None:
                try:
                    return float(elev)
                except (TypeError, ValueError):
                    return None
        return None
    except Exception as e:
        logger.warning(f"Elevation API error for ({lat}, {lon}): {e}")
        return None


@st.cache_data(ttl=1800)
def fetch_elevation_grid(lat, lon, radius_km=5, samples=9):
    """Fetch a grid of elevation samples around the target point.

    Returns a list of dicts with lat, lon, elevation keys.
    Used to assess terrain variability for signal propagation.
    """
    results = []
    step = radius_km / 3.0
    offsets = [-step, 0, step]
    locations = []
    for dlat_km in offsets:
        for dlon_km in offsets:
            slat = lat + (dlat_km / 111.0)
            slon = lon + (dlon_km / (111.0 * max(math.cos(math.radians(lat)), 0.01)))
            locations.append((slat, slon))

    loc_str = "|".join(f"{la},{lo}" for la, lo in locations)
    try:
        params = {"locations": loc_str}
        resp = requests.get(OPEN_TOPO_API, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") == "OK":
            for r in data.get("results", []):
                elev = r.get("elevation")
                loc = r.get("location", {})
                if elev is not None:
                    results.append({
                        "lat": loc.get("lat", 0),
                        "lon": loc.get("lng", 0),
                        "elevation": float(elev),
                    })
    except Exception as e:
        logger.warning(f"Elevation grid error: {e}")
    return results


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


def _count_elements_by_tag_regex(elements, tag_key, values):
    """Count Overpass elements where tags[tag_key] is in values set."""
    count = 0
    for el in elements:
        tags = el.get("tags", {})
        if tags.get(tag_key) in values:
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


def _extract_tower_positions(elements):
    """Extract lat/lon for communication towers and masts."""
    positions = []
    for el in elements:
        tags = el.get("tags", {})
        is_tower = (
            (tags.get("man_made") == "tower"
             and tags.get("tower:type") == "communication")
            or tags.get("man_made") == "mast"
        )
        if is_tower:
            lat = el.get("lat")
            lon = el.get("lon")
            if lat is not None and lon is not None:
                positions.append({"lat": lat, "lon": lon, "tags": tags})
    return positions


def _haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Scoring functions -- one per dimension
# ---------------------------------------------------------------------------


@st.cache_data(ttl=1800)
def score_mobile_coverage(lat, lon, radius=5000):
    """Mobile Coverage score (0-100).

    Evaluates cell/telecom tower density, distribution uniformity,
    and proximity of nearest tower.
    """
    conn_data = fetch_connectivity_data(lat, lon, radius=radius)
    elements = conn_data.get("elements", [])

    towers = _extract_tower_positions(elements)
    tower_count = len(towers)

    # Density score: more towers = better coverage
    # 10+ towers in radius is excellent
    density_pts = min(tower_count * 8.0, 40.0)

    # Proximity of nearest tower
    nearest_dist_km = None
    if towers:
        distances = [
            _haversine_km(lat, lon, t["lat"], t["lon"]) for t in towers
        ]
        nearest_dist_km = min(distances)

    # Proximity bonus: < 0.5 km = 30, < 1 km = 25, < 2 km = 15, etc.
    if nearest_dist_km is not None:
        if nearest_dist_km < 0.5:
            proximity_pts = 30.0
        elif nearest_dist_km < 1.0:
            proximity_pts = 25.0
        elif nearest_dist_km < 2.0:
            proximity_pts = 18.0
        elif nearest_dist_km < 3.0:
            proximity_pts = 10.0
        else:
            proximity_pts = max(0, 8.0 - nearest_dist_km)
    else:
        proximity_pts = 0.0

    # Distribution: check angular coverage (how many quadrants have towers)
    quadrants_covered = set()
    for t in towers:
        dlat = t["lat"] - lat
        dlon = t["lon"] - lon
        if dlat >= 0 and dlon >= 0:
            quadrants_covered.add("NE")
        elif dlat >= 0 and dlon < 0:
            quadrants_covered.add("NW")
        elif dlat < 0 and dlon >= 0:
            quadrants_covered.add("SE")
        else:
            quadrants_covered.add("SW")
    distribution_pts = len(quadrants_covered) * 7.5  # max 30

    raw = density_pts + proximity_pts + distribution_pts
    score = min(max(round(raw, 1), 0.0), 100.0)

    details = {
        "tower_count": tower_count,
        "nearest_tower_km": round(nearest_dist_km, 2) if nearest_dist_km is not None else None,
        "quadrants_covered": len(quadrants_covered),
        "density_pts": round(density_pts, 1),
        "proximity_pts": round(proximity_pts, 1),
        "distribution_pts": round(distribution_pts, 1),
    }
    return score, details


@st.cache_data(ttl=1800)
def score_internet_infrastructure(lat, lon, radius=5000):
    """Internet Infrastructure score (0-100).

    Evaluates fiber optic cables, data centers, ISP offices,
    and telecom facilities.
    """
    conn_data = fetch_connectivity_data(lat, lon, radius=radius)
    elements = conn_data.get("elements", [])

    fiber_cables = _count_elements_by_tag(elements, "utility", "fibre_optic_cable")
    data_centers = _count_elements_by_tag(elements, "man_made", "data_center")
    telecom_offices = _count_elements_by_tag(elements, "office", "telecommunication")
    telecom_nodes = _count_elements_with_tag(elements, "telecom")

    # Fiber presence is a strong indicator
    fiber_pts = min(fiber_cables * 15.0, 35.0)

    # Data centers indicate major infrastructure
    datacenter_pts = min(data_centers * 20.0, 30.0)

    # Telecom offices & facilities
    office_pts = min(telecom_offices * 10.0, 15.0)

    # General telecom tagged nodes/ways
    telecom_pts = min(telecom_nodes * 5.0, 20.0)

    raw = fiber_pts + datacenter_pts + office_pts + telecom_pts
    score = min(max(round(raw, 1), 0.0), 100.0)

    details = {
        "fiber_cables": fiber_cables,
        "data_centers": data_centers,
        "telecom_offices": telecom_offices,
        "telecom_nodes": telecom_nodes,
        "fiber_pts": round(fiber_pts, 1),
        "datacenter_pts": round(datacenter_pts, 1),
        "office_pts": round(office_pts, 1),
        "telecom_pts": round(telecom_pts, 1),
    }
    return score, details


@st.cache_data(ttl=1800)
def score_signal_propagation(lat, lon, radius=5000):
    """Signal Propagation score (0-100).

    Evaluates terrain favorability for wireless signal propagation:
    - Flat terrain = good (fewer obstructions)
    - Valleys = poor (signal blocked)
    - Elevated position = advantage (line of sight)
    Uses Open Topo Data elevation grid.
    """
    center_elev = fetch_elevation_data(lat, lon)
    grid = fetch_elevation_grid(lat, lon, radius_km=max(1, radius // 1000))

    if center_elev is None:
        center_elev = 0.0

    elevations = [p["elevation"] for p in grid if p.get("elevation") is not None]

    if not elevations:
        # No elevation data available; return neutral score
        return 50.0, {
            "center_elevation_m": round(center_elev, 1),
            "terrain_variability_m": 0.0,
            "elevation_advantage_m": 0.0,
            "flatness_pts": 25.0,
            "elevation_advantage_pts": 15.0,
            "valley_penalty": 0.0,
            "note": "Limited elevation data available",
        }

    avg_elev = sum(elevations) / len(elevations)
    max_elev = max(elevations)
    min_elev = min(elevations)
    terrain_range = max_elev - min_elev
    elevation_advantage = center_elev - avg_elev

    # Flatness score: low variability is good for propagation
    # < 20 m range = very flat (40 pts), > 200 m = very rough (5 pts)
    if terrain_range < 20:
        flatness_pts = 40.0
    elif terrain_range < 50:
        flatness_pts = 32.0
    elif terrain_range < 100:
        flatness_pts = 22.0
    elif terrain_range < 200:
        flatness_pts = 12.0
    else:
        flatness_pts = 5.0

    # Elevation advantage: being higher than surroundings improves LOS
    # > 50 m above average = 35 pts, at average = 15 pts, below = 5 pts
    if elevation_advantage > 50:
        elev_adv_pts = 35.0
    elif elevation_advantage > 20:
        elev_adv_pts = 28.0
    elif elevation_advantage > 5:
        elev_adv_pts = 20.0
    elif elevation_advantage > -5:
        elev_adv_pts = 15.0
    elif elevation_advantage > -20:
        elev_adv_pts = 10.0
    else:
        elev_adv_pts = 5.0

    # Valley penalty: if center is significantly lower than surroundings
    valley_penalty = 0.0
    if elevation_advantage < -30:
        valley_penalty = min(abs(elevation_advantage) * 0.3, 25.0)

    # High altitude bonus for clear air propagation (above 1500 m)
    altitude_bonus = 0.0
    if center_elev > 1500:
        altitude_bonus = min((center_elev - 1500) * 0.01, 10.0)

    raw = flatness_pts + elev_adv_pts - valley_penalty + altitude_bonus
    score = min(max(round(raw, 1), 0.0), 100.0)

    details = {
        "center_elevation_m": round(center_elev, 1),
        "avg_surrounding_m": round(avg_elev, 1),
        "terrain_range_m": round(terrain_range, 1),
        "elevation_advantage_m": round(elevation_advantage, 1),
        "flatness_pts": round(flatness_pts, 1),
        "elevation_advantage_pts": round(elev_adv_pts, 1),
        "valley_penalty": round(valley_penalty, 1),
        "altitude_bonus": round(altitude_bonus, 1),
    }
    return score, details


@st.cache_data(ttl=1800)
def score_digital_services(lat, lon, radius=5000):
    """Digital Services score (0-100).

    Evaluates internet cafes, coworking spaces, electronics shops,
    and other digital service points.
    """
    conn_data = fetch_connectivity_data(lat, lon, radius=radius)
    elements = conn_data.get("elements", [])

    internet_cafes = _count_elements_by_tag(elements, "amenity", "internet_cafe")
    electronics_shops = _count_elements_by_tag(elements, "shop", "electronics")
    telecom_offices = _count_elements_by_tag(elements, "office", "telecommunication")

    # Internet cafes are direct access points
    cafe_pts = min(internet_cafes * 20.0, 40.0)

    # Electronics shops indicate digital ecosystem
    shop_pts = min(electronics_shops * 10.0, 25.0)

    # Telecom offices for service & support
    office_pts = min(telecom_offices * 15.0, 20.0)

    # Base urban digital score: if any services exist, area has some baseline
    baseline_pts = 0.0
    total_services = internet_cafes + electronics_shops + telecom_offices
    if total_services >= 5:
        baseline_pts = 15.0
    elif total_services >= 2:
        baseline_pts = 10.0
    elif total_services >= 1:
        baseline_pts = 5.0

    raw = cafe_pts + shop_pts + office_pts + baseline_pts
    score = min(max(round(raw, 1), 0.0), 100.0)

    details = {
        "internet_cafes": internet_cafes,
        "electronics_shops": electronics_shops,
        "telecom_offices": telecom_offices,
        "total_services": total_services,
        "cafe_pts": round(cafe_pts, 1),
        "shop_pts": round(shop_pts, 1),
        "office_pts": round(office_pts, 1),
        "baseline_pts": round(baseline_pts, 1),
    }
    return score, details


@st.cache_data(ttl=1800)
def score_connectivity_resilience(lat, lon, radius=5000):
    """Connectivity Resilience score (0-100).

    Evaluates redundancy (multiple towers from different directions),
    weather impact on signal quality, and power infrastructure.
    """
    conn_data = fetch_connectivity_data(lat, lon, radius=radius)
    weather_data = fetch_weather_data(lat, lon)
    elements = conn_data.get("elements", [])

    towers = _extract_tower_positions(elements)
    tower_count = len(towers)

    # Redundancy: multiple towers mean failover capability
    # 5+ towers = excellent redundancy
    if tower_count >= 5:
        redundancy_pts = 35.0
    elif tower_count >= 3:
        redundancy_pts = 25.0
    elif tower_count >= 2:
        redundancy_pts = 18.0
    elif tower_count >= 1:
        redundancy_pts = 10.0
    else:
        redundancy_pts = 0.0

    # Power infrastructure: substations and transformers
    power_nodes = _count_elements_by_tag_regex(
        elements, "power", {"substation", "transformer"}
    )
    power_pts = min(power_nodes * 8.0, 25.0)

    # Weather impact on signal: heavy rain, high wind, dense clouds degrade signal
    current = weather_data.get("current", {})
    precip = current.get("precipitation", 0) or 0
    wind = current.get("wind_speed_10m", 0) or 0
    cloud_cover = current.get("cloud_cover", 0) or 0

    # Weather penalty: heavier weather = worse signal
    rain_penalty = 0.0
    if precip > 10:
        rain_penalty = 15.0
    elif precip > 5:
        rain_penalty = 10.0
    elif precip > 2:
        rain_penalty = 5.0

    wind_penalty = 0.0
    if wind > 60:
        wind_penalty = 12.0
    elif wind > 40:
        wind_penalty = 8.0
    elif wind > 25:
        wind_penalty = 4.0

    cloud_penalty = 0.0
    if cloud_cover > 90:
        cloud_penalty = 5.0
    elif cloud_cover > 70:
        cloud_penalty = 3.0

    total_weather_penalty = rain_penalty + wind_penalty + cloud_penalty

    # Weather resilience: less penalty = higher score
    weather_resilience_pts = max(0.0, 25.0 - total_weather_penalty)

    # Diversity bonus: having both towers and power infra
    diversity_bonus = 0.0
    if tower_count >= 1 and power_nodes >= 1:
        diversity_bonus = 15.0
    elif tower_count >= 1 or power_nodes >= 1:
        diversity_bonus = 8.0

    raw = redundancy_pts + power_pts + weather_resilience_pts + diversity_bonus
    score = min(max(round(raw, 1), 0.0), 100.0)

    details = {
        "tower_redundancy": tower_count,
        "power_nodes": power_nodes,
        "precipitation_mm": round(precip, 1),
        "wind_kmh": round(wind, 1),
        "cloud_cover_pct": round(cloud_cover, 1),
        "redundancy_pts": round(redundancy_pts, 1),
        "power_pts": round(power_pts, 1),
        "weather_penalty": round(total_weather_penalty, 1),
        "weather_resilience_pts": round(weather_resilience_pts, 1),
        "diversity_bonus": round(diversity_bonus, 1),
    }
    return score, details


# ---------------------------------------------------------------------------
# Composite score
# ---------------------------------------------------------------------------


def compute_all_scores(lat, lon, radius=5000):
    """Compute all 5 connectivity dimension scores and the weighted total."""
    mobile_score, mobile_detail = score_mobile_coverage(lat, lon, radius=radius)
    infra_score, infra_detail = score_internet_infrastructure(lat, lon, radius=radius)
    signal_score, signal_detail = score_signal_propagation(lat, lon, radius=radius)
    digital_score, digital_detail = score_digital_services(lat, lon, radius=radius)
    resilience_score, resilience_detail = score_connectivity_resilience(
        lat, lon, radius=radius
    )

    scores = {
        "mobile_coverage": {"score": mobile_score, "details": mobile_detail},
        "internet_infra": {"score": infra_score, "details": infra_detail},
        "signal_propagation": {"score": signal_score, "details": signal_detail},
        "digital_services": {"score": digital_score, "details": digital_detail},
        "connectivity_resilience": {
            "score": resilience_score,
            "details": resilience_detail,
        },
    }

    weighted_total = 0.0
    for key, meta in CONNECTIVITY_COMPONENTS.items():
        weighted_total += scores[key]["score"] * meta["weight"]

    return scores, round(weighted_total, 1)


def classify_score(total):
    """Return (label, color) classification for a connectivity score."""
    for low, high, label, color in CLASSIFICATION_BANDS:
        if low <= total <= high:
            return label, color
    return "Poor / No Connectivity", "#ef4444"


# ---------------------------------------------------------------------------
# Visualisation helpers
# ---------------------------------------------------------------------------


def build_radar_chart(scores):
    """Build a Plotly radar chart of the 5 connectivity dimensions."""
    categories = []
    values = []
    for key in CONNECTIVITY_COMPONENTS:
        meta = CONNECTIVITY_COMPONENTS[key]
        categories.append(meta["name"])
        values.append(scores[key]["score"])

    # Close the radar loop
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(59,130,246,0.18)",
        line=dict(color="#3b82f6", width=2),
        marker=dict(size=7, color="#3b82f6"),
        name="Connectivity Score",
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


def build_connectivity_gauge(total):
    """Build a Plotly gauge chart for the overall connectivity score."""
    _, color = classify_score(total)

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total,
        number=dict(font=dict(size=48, color=color), suffix="/100"),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#2a3550"),
            bar=dict(color=color),
            bgcolor="rgba(15,23,42,0.65)",
            borderwidth=2,
            bordercolor="#2a3550",
            steps=[
                dict(range=[0, 29], color="rgba(239,68,68,0.15)"),
                dict(range=[30, 49], color="rgba(249,115,22,0.15)"),
                dict(range=[50, 69], color="rgba(245,158,11,0.15)"),
                dict(range=[70, 84], color="rgba(34,197,94,0.15)"),
                dict(range=[85, 100], color="rgba(16,185,129,0.15)"),
            ],
            threshold=dict(
                line=dict(color="#e8ecf4", width=3),
                thickness=0.8,
                value=total,
            ),
        ),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=50, b=20),
        height=280,
    )
    return fig


def build_tower_density_chart(tower_details):
    """Build a Plotly chart showing tower quadrant distribution."""
    labels = ["NE Quadrant", "NW Quadrant", "SE Quadrant", "SW Quadrant"]
    quadrants_covered = tower_details.get("quadrants_covered", 0)

    # Create a simple filled/unfilled representation
    values = []
    colors = []
    for i in range(4):
        if i < quadrants_covered:
            values.append(1)
            colors.append("#3b82f6")
        else:
            values.append(1)
            colors.append("rgba(42,53,80,0.5)")

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker=dict(colors=colors),
        textinfo="label",
        textfont=dict(color="#e8ecf4", size=11),
        hoverinfo="label",
    )])

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
        height=280,
        annotations=[dict(
            text=f"{quadrants_covered}/4",
            x=0.5, y=0.5,
            font=dict(size=28, color="#3b82f6"),
            showarrow=False,
        )],
    )
    return fig


def build_infrastructure_bar(scores):
    """Build a horizontal bar chart of all 5 dimension scores."""
    names = []
    vals = []
    colors = []
    for key in CONNECTIVITY_COMPONENTS:
        meta = CONNECTIVITY_COMPONENTS[key]
        names.append(meta["name"])
        vals.append(scores[key]["score"])
        colors.append(meta["color"])

    fig = go.Figure(go.Bar(
        y=names,
        x=vals,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.0f}" for v in vals],
        textposition="auto",
        textfont=dict(color="#e8ecf4", size=12),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            range=[0, 105],
            gridcolor="#2a3550",
            tickfont=dict(color="#5a6580"),
            title=dict(text="Score", font=dict(color="#8b97b0")),
        ),
        yaxis=dict(
            tickfont=dict(color="#e8ecf4", size=12),
            autorange="reversed",
        ),
        margin=dict(l=10, r=30, t=20, b=40),
        height=300,
    )
    return fig


# ---------------------------------------------------------------------------
# Summary generators
# ---------------------------------------------------------------------------


def generate_digital_readiness_summary(scores, total):
    """Return a list of insight strings based on dimension scores."""
    insights = []

    mobile_s = scores["mobile_coverage"]["score"]
    infra_s = scores["internet_infra"]["score"]
    signal_s = scores["signal_propagation"]["score"]
    digital_s = scores["digital_services"]["score"]
    resilience_s = scores["connectivity_resilience"]["score"]

    # Mobile coverage insights
    if mobile_s >= 70:
        insights.append(
            "Strong mobile coverage detected with multiple cell towers "
            "providing good signal distribution across the area."
        )
    elif mobile_s >= 40:
        insights.append(
            "Moderate mobile coverage. Some cell towers are present but "
            "coverage gaps may exist, especially in certain directions."
        )
    else:
        insights.append(
            "WEAK: Limited or no cell tower infrastructure detected. "
            "Mobile connectivity is likely unreliable or unavailable. "
            "Consider satellite communication as backup."
        )

    # Internet infrastructure insights
    if infra_s >= 70:
        insights.append(
            "Well-developed internet backbone with fiber optic and/or "
            "data center presence, indicating high-speed connectivity options."
        )
    elif infra_s >= 40:
        insights.append(
            "Some internet infrastructure exists. Wired broadband may be "
            "available but speeds could vary significantly."
        )
    else:
        insights.append(
            "WEAK: Minimal fixed internet infrastructure. Broadband access "
            "is likely limited to mobile data or satellite only."
        )

    # Signal propagation insights
    if signal_s >= 70:
        insights.append(
            "Terrain is favorable for wireless signal propagation with "
            "good line-of-sight potential and minimal obstructions."
        )
    elif signal_s < 40:
        insights.append(
            "CHALLENGING: Terrain significantly impacts signal quality. "
            "Valleys, hills, or dense elevation changes create dead zones."
        )

    # Digital services insights
    if digital_s >= 50:
        insights.append(
            "Digital service ecosystem is present with internet cafes, "
            "electronics shops, or telecom offices nearby."
        )
    elif digital_s < 20:
        insights.append(
            "No digital service points detected. Bring your own equipment "
            "and ensure devices are fully charged before visiting."
        )

    # Resilience insights
    if resilience_s >= 70:
        insights.append(
            "Good connectivity resilience with redundant towers and "
            "stable power infrastructure supporting consistent service."
        )
    elif resilience_s < 40:
        insights.append(
            "LOW RESILIENCE: Limited redundancy in connectivity "
            "infrastructure. Service disruptions are likely during "
            "adverse weather or equipment failures."
        )

    # Overall digital readiness
    if total >= 70:
        insights.append(
            "DIGITAL READINESS: This location supports remote work, "
            "video calls, and cloud-based operations with high confidence."
        )
    elif total >= 45:
        insights.append(
            "DIGITAL READINESS: Basic connectivity tasks (email, messaging) "
            "are likely feasible. Bandwidth-intensive tasks may be unreliable."
        )
    else:
        insights.append(
            "DIGITAL READINESS: This area is poorly connected. Plan for "
            "offline operation and consider portable connectivity solutions "
            "(satellite hotspot, mesh radio)."
        )

    return insights


# ---------------------------------------------------------------------------
# Entry-point UI renderer
# ---------------------------------------------------------------------------


def render_connectivity_score_tab():
    """Render the Connectivity & Digital Infrastructure AI tab UI."""

    # -- Tab header --
    st.markdown(
        '<div class="tab-header blue">'
        "<h4>Connectivity & Digital Infrastructure AI</h4>"
        "<p>AI-powered assessment of mobile coverage, internet infrastructure, "
        "signal propagation, digital services &amp; connectivity resilience</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # -- Location selector --
    c1, c2, c3 = st.columns([1.2, 1.2, 0.8])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="conn_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50

    with c2:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="conn_lat",
        )
    with c3:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="conn_lon",
        )

    radius = st.slider(
        "Search radius (m)", 1000, 15000, 5000,
        step=500, key="conn_radius",
    )

    run = st.button(
        "Analyse Connectivity",
        type="primary",
        key="conn_run",
        use_container_width=True,
    )

    if not run:
        st.info(
            "Set coordinates and click **Analyse Connectivity** "
            "to assess digital infrastructure and signal quality."
        )
        return

    # ==================================================================
    # Compute all scores
    # ==================================================================
    progress = st.progress(0, text="Initialising connectivity analysis...")

    progress.progress(10, text="Fetching telecom infrastructure...")
    scores, total = compute_all_scores(lat, lon, radius=radius)

    progress.progress(85, text="Building visualisations...")

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
        f'Weighted composite of 5 connectivity dimensions at '
        f'{lat:.4f}, {lon:.4f}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ==================================================================
    # 2. Connectivity gauge
    # ==================================================================
    st.markdown("### Overall Connectivity Gauge")
    gauge_fig = build_connectivity_gauge(total)
    st.plotly_chart(gauge_fig, use_container_width=True, key="consco_pchart1")

    # ==================================================================
    # 3. Radar chart
    # ==================================================================
    st.markdown("### Connectivity Dimensions Radar")
    radar_fig = build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="consco_pchart2")

    # ==================================================================
    # 4. Infrastructure bar chart
    # ==================================================================
    st.markdown("### Dimension Comparison")
    bar_fig = build_infrastructure_bar(scores)
    st.plotly_chart(bar_fig, use_container_width=True, key="consco_pchart3")

    # ==================================================================
    # 5. Five metric cards
    # ==================================================================
    st.markdown("### Dimension Breakdown")

    for key in CONNECTIVITY_COMPONENTS:
        meta = CONNECTIVITY_COMPONENTS[key]
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
            filtered = {
                k: v for k, v in dim_details.items() if v is not None
            }
            if filtered:
                detail_cols = st.columns(min(len(filtered), 4))
                for idx, (dk, dv) in enumerate(filtered.items()):
                    col = detail_cols[idx % len(detail_cols)]
                    display_key = dk.replace("_", " ").title()
                    col.metric(display_key, f"{dv}")
            else:
                st.caption("No detail data available.")

    # ==================================================================
    # 6. Tower density map concept
    # ==================================================================
    st.markdown("### Tower Coverage Distribution")
    mobile_details = scores["mobile_coverage"]["details"]
    tower_chart = build_tower_density_chart(mobile_details)
    st.plotly_chart(tower_chart, use_container_width=True, key="consco_pchart4")

    tc = mobile_details.get("tower_count", 0)
    nearest = mobile_details.get("nearest_tower_km")
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.metric("Towers Detected", tc)
    col_t2.metric(
        "Nearest Tower",
        f"{nearest:.2f} km" if nearest is not None else "N/A",
    )
    col_t3.metric(
        "Quadrant Coverage",
        f"{mobile_details.get('quadrants_covered', 0)}/4",
    )

    # ==================================================================
    # 7. Connectivity priorities (ranked list)
    # ==================================================================
    st.markdown("### Connectivity Priorities (Weakest First)")

    ranked = sorted(
        CONNECTIVITY_COMPONENTS.keys(),
        key=lambda k: scores[k]["score"],
    )
    for rank, key in enumerate(ranked, 1):
        meta = CONNECTIVITY_COMPONENTS[key]
        s = scores[key]["score"]
        _, sc = classify_score(s)
        urgency = ("CRITICAL" if s < 30 else
                   ("WEAK" if s < 50 else
                    ("MODERATE" if s < 70 else "STRONG")))
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
    # 8. Digital readiness summary
    # ==================================================================
    st.markdown("### Digital Readiness Summary")
    insights = generate_digital_readiness_summary(scores, total)
    for insight in insights:
        is_weak = "WEAK" in insight or "LOW" in insight or "CHALLENGING" in insight
        border_color = "#ef4444" if is_weak else "#2a3550"
        st.markdown(
            f'<div style="background:rgba(15,23,42,0.65);border:1px solid '
            f'{border_color};border-radius:10px;padding:12px 16px;'
            f'margin:6px 0;color:#e8ecf4;font-size:13px;">'
            f'{insight}</div>',
            unsafe_allow_html=True,
        )
