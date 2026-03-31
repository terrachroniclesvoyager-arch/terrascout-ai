"""
Transportation & Logistics Intelligence AI module for TerraScout AI.
Analyzes transport infrastructure quality around any GPS coordinate by
querying the Overpass API across six dimensions: road network density,
public transit coverage, airport proximity, port/maritime access,
cycling infrastructure, and pedestrian accessibility.
All APIs are free and require no API keys.
"""

import math
import logging
from html import escape

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

OVERPASS_API = "https://overpass-api.de/api/interpreter"
OPEN_ELEVATION_API = "https://api.open-elevation.com/api/v1/lookup"

# Theme colours
CLR_BG = "#1a1a2e"
CLR_SURFACE = "#16213e"
CLR_CARD = "#0f3460"
CLR_BORDER = "#1a4080"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"
CLR_ACCENT = "#06b6d4"

CLR_EXCELLENT = "#22c55e"
CLR_GOOD = "#84cc16"
CLR_MODERATE = "#f59e0b"
CLR_POOR = "#ef4444"
CLR_MINIMAL = "#991b1b"

# Dimension definitions
DIMENSIONS = {
    "Road Network Density": {
        "color": "#3b82f6",
        "icon": "road",
        "desc": "Motorways, trunks, primary, secondary, and tertiary roads within 5 km.",
    },
    "Public Transit Coverage": {
        "color": "#8b5cf6",
        "icon": "bus",
        "desc": "Bus stops, train stations, tram stops, and subway stations within 3 km.",
    },
    "Airport Proximity": {
        "color": "#06b6d4",
        "icon": "plane",
        "desc": "Distance to nearest airports and aerodromes.",
    },
    "Port & Maritime Access": {
        "color": "#0ea5e9",
        "icon": "anchor",
        "desc": "Harbors, piers, and ferry terminals within 20 km.",
    },
    "Cycling Infrastructure": {
        "color": "#10b981",
        "icon": "bicycle",
        "desc": "Cycleways, bicycle parking, and bike-sharing within 3 km.",
    },
    "Pedestrian Accessibility": {
        "color": "#f59e0b",
        "icon": "walking",
        "desc": "Footways, pedestrian zones, crossings, and sidewalks within 2 km.",
    },
}

DIMENSION_WEIGHTS = {
    "Road Network Density": 0.25,
    "Public Transit Coverage": 0.20,
    "Airport Proximity": 0.15,
    "Port & Maritime Access": 0.10,
    "Cycling Infrastructure": 0.15,
    "Pedestrian Accessibility": 0.15,
}

# =============================================================================
# HELPERS
# =============================================================================


def _clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    """Clamp a value to the given range."""
    return max(lo, min(hi, value))


def _score_color(score: float) -> str:
    """Return a hex colour for a 0-10 transport score."""
    if score >= 8:
        return CLR_EXCELLENT
    if score >= 6:
        return CLR_GOOD
    if score >= 3:
        return CLR_MODERATE
    if score >= 1:
        return CLR_POOR
    return CLR_MINIMAL


def _score_label(score: float) -> str:
    """Return a human-readable label for a 0-10 score."""
    if score >= 8:
        return "Excellent"
    if score >= 6:
        return "Good"
    if score >= 3:
        return "Moderate"
    if score >= 1:
        return "Poor"
    return "Minimal"


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance in kilometres between two points
    on Earth using the Haversine formula.
    """
    R = 6371.0  # Earth radius in km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# =============================================================================
# OVERPASS QUERY HELPER
# =============================================================================


@st.cache_data(ttl=900)
def _overpass_query(query: str) -> list:
    """
    Execute an Overpass API query and return the elements list.
    Returns an empty list on any failure.
    """
    try:
        resp = requests.post(
            OVERPASS_API,
            data={"data": query},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("elements", [])
    except Exception as exc:
        logger.warning("Overpass query failed: %s", exc)
        return []


# =============================================================================
# ELEVATION FETCH
# =============================================================================


@st.cache_data(ttl=900)
def fetch_elevation_data(lat: float, lon: float) -> dict:
    """
    Fetch elevation for the centre point and a surrounding grid.
    Returns dict with:
        center_elevation  (float)
        grid_elevations   (list of floats)
    """
    offsets_km = [-2, -1, 0, 1, 2]
    locations = []
    for dlat_km in offsets_km:
        for dlon_km in offsets_km:
            slat = lat + (dlat_km / 111.0)
            slon = lon + (dlon_km / (111.0 * max(math.cos(math.radians(lat)), 0.01)))
            locations.append({"latitude": slat, "longitude": slon})

    center_elevation = 0.0
    grid_elevations = []

    try:
        resp = requests.post(
            OPEN_ELEVATION_API,
            json={"locations": locations},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        for r in results:
            elev = r.get("elevation")
            if elev is not None:
                grid_elevations.append(float(elev))
        # Centre point is the middle of the grid (index 12 in a 5x5 grid)
        if len(grid_elevations) > 12:
            center_elevation = grid_elevations[12]
        elif grid_elevations:
            center_elevation = grid_elevations[0]
    except Exception as exc:
        logger.warning("Elevation API error: %s", exc)

    return {
        "center_elevation": center_elevation,
        "grid_elevations": grid_elevations,
    }


# =============================================================================
# DIMENSION 1: ROAD NETWORK DENSITY
# =============================================================================


@st.cache_data(ttl=900)
def fetch_road_network(lat: float, lon: float) -> dict:
    """
    Count roads by type (motorway, trunk, primary, secondary, tertiary)
    within 5 km using the Overpass API.
    """
    query = f"""
    [out:json][timeout:10];
    (
      way["highway"~"motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link"](around:5000,{lat},{lon});
    );
    out body;
    """
    elements = _overpass_query(query)

    counts = {
        "motorway": 0,
        "trunk": 0,
        "primary": 0,
        "secondary": 0,
        "tertiary": 0,
    }
    for el in elements:
        hw = el.get("tags", {}).get("highway", "")
        if hw in ("motorway", "motorway_link"):
            counts["motorway"] += 1
        elif hw in ("trunk", "trunk_link"):
            counts["trunk"] += 1
        elif hw in ("primary", "primary_link"):
            counts["primary"] += 1
        elif hw in ("secondary", "secondary_link"):
            counts["secondary"] += 1
        elif hw in ("tertiary", "tertiary_link"):
            counts["tertiary"] += 1

    total = sum(counts.values())
    # Scoring: weighted by road importance
    weighted = (
        counts["motorway"] * 5
        + counts["trunk"] * 4
        + counts["primary"] * 3
        + counts["secondary"] * 2
        + counts["tertiary"] * 1
    )
    score = _clamp(min(10.0, weighted / 40.0))

    return {"counts": counts, "total": total, "score": round(score, 1)}


# =============================================================================
# DIMENSION 2: PUBLIC TRANSIT COVERAGE
# =============================================================================


@st.cache_data(ttl=900)
def fetch_public_transit(lat: float, lon: float) -> dict:
    """
    Count bus stops, train stations, tram stops, and subway stations
    within 3 km using the Overpass API.
    """
    query = f"""
    [out:json][timeout:10];
    (
      node["highway"="bus_stop"](around:3000,{lat},{lon});
      node["public_transport"="stop_position"](around:3000,{lat},{lon});
      node["railway"="station"](around:3000,{lat},{lon});
      node["railway"="halt"](around:3000,{lat},{lon});
      node["railway"="tram_stop"](around:3000,{lat},{lon});
      node["station"="subway"](around:3000,{lat},{lon});
      node["railway"="subway_entrance"](around:3000,{lat},{lon});
    );
    out body;
    """
    elements = _overpass_query(query)

    counts = {
        "bus_stops": 0,
        "train_stations": 0,
        "tram_stops": 0,
        "subway_stations": 0,
    }
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("highway") == "bus_stop" or tags.get("public_transport") == "stop_position":
            counts["bus_stops"] += 1
        elif tags.get("railway") == "station" or tags.get("railway") == "halt":
            counts["train_stations"] += 1
        elif tags.get("railway") == "tram_stop":
            counts["tram_stops"] += 1
        elif tags.get("station") == "subway" or tags.get("railway") == "subway_entrance":
            counts["subway_stations"] += 1

    total = sum(counts.values())
    # Scoring: higher weight for rail-based transit
    weighted = (
        counts["bus_stops"] * 1
        + counts["train_stations"] * 5
        + counts["tram_stops"] * 3
        + counts["subway_stations"] * 4
    )
    score = _clamp(min(10.0, weighted / 25.0))

    return {"counts": counts, "total": total, "score": round(score, 1)}


# =============================================================================
# DIMENSION 3: AIRPORT PROXIMITY
# =============================================================================


@st.cache_data(ttl=900)
def fetch_airport_proximity(lat: float, lon: float) -> dict:
    """
    Find nearest airports and aerodromes within 50 km.
    Score is based on proximity of the nearest one.
    """
    query = f"""
    [out:json][timeout:10];
    (
      node["aeroway"="aerodrome"](around:50000,{lat},{lon});
      way["aeroway"="aerodrome"](around:50000,{lat},{lon});
      relation["aeroway"="aerodrome"](around:50000,{lat},{lon});
    );
    out center;
    """
    elements = _overpass_query(query)

    airports = []
    for el in elements:
        name = el.get("tags", {}).get("name", "Unknown Airport")
        iata = el.get("tags", {}).get("iata", "")
        atype = el.get("tags", {}).get("aerodrome:type", "unknown")

        # Get coordinates (nodes have lat/lon directly; ways/relations use center)
        a_lat = el.get("lat") or el.get("center", {}).get("lat")
        a_lon = el.get("lon") or el.get("center", {}).get("lon")

        if a_lat is not None and a_lon is not None:
            dist = haversine_distance(lat, lon, float(a_lat), float(a_lon))
            airports.append({
                "name": name,
                "iata": iata,
                "type": atype,
                "lat": float(a_lat),
                "lon": float(a_lon),
                "distance_km": round(dist, 1),
            })

    airports.sort(key=lambda a: a["distance_km"])
    nearest_dist = airports[0]["distance_km"] if airports else 999.0

    # Scoring: closer is better, max score if within 5 km
    if nearest_dist <= 5:
        score = 10.0
    elif nearest_dist <= 15:
        score = 8.0
    elif nearest_dist <= 30:
        score = 6.0
    elif nearest_dist <= 50:
        score = 4.0
    else:
        score = 1.0

    return {
        "airports": airports[:5],
        "nearest_distance_km": nearest_dist,
        "count": len(airports),
        "score": round(score, 1),
    }


# =============================================================================
# DIMENSION 4: PORT & MARITIME ACCESS
# =============================================================================


@st.cache_data(ttl=900)
def fetch_port_access(lat: float, lon: float) -> dict:
    """
    Find harbors, piers, and ferry terminals within 20 km.
    """
    query = f"""
    [out:json][timeout:10];
    (
      node["harbour"="yes"](around:20000,{lat},{lon});
      way["harbour"="yes"](around:20000,{lat},{lon});
      node["man_made"="pier"](around:20000,{lat},{lon});
      way["man_made"="pier"](around:20000,{lat},{lon});
      node["amenity"="ferry_terminal"](around:20000,{lat},{lon});
      way["amenity"="ferry_terminal"](around:20000,{lat},{lon});
      node["landuse"="harbour"](around:20000,{lat},{lon});
      way["landuse"="harbour"](around:20000,{lat},{lon});
      node["industrial"="port"](around:20000,{lat},{lon});
      way["industrial"="port"](around:20000,{lat},{lon});
    );
    out center;
    """
    elements = _overpass_query(query)

    counts = {
        "harbors": 0,
        "piers": 0,
        "ferry_terminals": 0,
        "ports": 0,
    }
    facilities = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "Unnamed")
        f_lat = el.get("lat") or el.get("center", {}).get("lat")
        f_lon = el.get("lon") or el.get("center", {}).get("lon")
        dist = 0.0
        if f_lat is not None and f_lon is not None:
            dist = haversine_distance(lat, lon, float(f_lat), float(f_lon))

        ftype = "port"
        if tags.get("harbour") == "yes" or tags.get("landuse") == "harbour":
            counts["harbors"] += 1
            ftype = "harbor"
        elif tags.get("man_made") == "pier":
            counts["piers"] += 1
            ftype = "pier"
        elif tags.get("amenity") == "ferry_terminal":
            counts["ferry_terminals"] += 1
            ftype = "ferry_terminal"
        elif tags.get("industrial") == "port":
            counts["ports"] += 1
            ftype = "port"

        facilities.append({
            "name": name,
            "type": ftype,
            "distance_km": round(dist, 1),
        })

    facilities.sort(key=lambda f: f["distance_km"])
    total = sum(counts.values())

    # Scoring: presence-based with distance weighting
    if total == 0:
        score = 0.0
    else:
        base = min(6.0, total * 1.5)
        nearest = facilities[0]["distance_km"] if facilities else 20.0
        proximity_bonus = max(0, (20.0 - nearest) / 20.0) * 4.0
        score = _clamp(base + proximity_bonus)

    return {
        "counts": counts,
        "total": total,
        "facilities": facilities[:8],
        "score": round(score, 1),
    }


# =============================================================================
# DIMENSION 5: CYCLING INFRASTRUCTURE
# =============================================================================


@st.cache_data(ttl=900)
def fetch_cycling_infra(lat: float, lon: float) -> dict:
    """
    Count cycleways, bicycle parking, and bike-sharing stations within 3 km.
    """
    query = f"""
    [out:json][timeout:10];
    (
      way["highway"="cycleway"](around:3000,{lat},{lon});
      node["amenity"="bicycle_parking"](around:3000,{lat},{lon});
      node["amenity"="bicycle_rental"](around:3000,{lat},{lon});
      way["cycleway"~"lane|track|shared_lane"](around:3000,{lat},{lon});
    );
    out body;
    """
    elements = _overpass_query(query)

    counts = {
        "cycleways": 0,
        "bicycle_parking": 0,
        "bike_sharing": 0,
        "cycle_lanes": 0,
    }
    for el in elements:
        tags = el.get("tags", {})
        if tags.get("highway") == "cycleway":
            counts["cycleways"] += 1
        elif tags.get("amenity") == "bicycle_parking":
            counts["bicycle_parking"] += 1
        elif tags.get("amenity") == "bicycle_rental":
            counts["bike_sharing"] += 1
        elif tags.get("cycleway") in ("lane", "track", "shared_lane"):
            counts["cycle_lanes"] += 1

    total = sum(counts.values())
    weighted = (
        counts["cycleways"] * 2
        + counts["bicycle_parking"] * 1
        + counts["bike_sharing"] * 3
        + counts["cycle_lanes"] * 2
    )
    score = _clamp(min(10.0, weighted / 20.0))

    return {"counts": counts, "total": total, "score": round(score, 1)}


# =============================================================================
# DIMENSION 6: PEDESTRIAN ACCESSIBILITY
# =============================================================================


@st.cache_data(ttl=900)
def fetch_pedestrian_access(lat: float, lon: float) -> dict:
    """
    Count footways, pedestrian zones, crossings, and sidewalks within 2 km.
    """
    query = f"""
    [out:json][timeout:10];
    (
      way["highway"="footway"](around:2000,{lat},{lon});
      way["highway"="pedestrian"](around:2000,{lat},{lon});
      node["highway"="crossing"](around:2000,{lat},{lon});
      way["footway"="sidewalk"](around:2000,{lat},{lon});
      way["highway"="steps"](around:2000,{lat},{lon});
    );
    out body;
    """
    elements = _overpass_query(query)

    counts = {
        "footways": 0,
        "pedestrian_zones": 0,
        "crossings": 0,
        "sidewalks": 0,
        "steps": 0,
    }
    for el in elements:
        tags = el.get("tags", {})
        hw = tags.get("highway", "")
        if hw == "footway" and tags.get("footway") != "sidewalk":
            counts["footways"] += 1
        elif hw == "pedestrian":
            counts["pedestrian_zones"] += 1
        elif hw == "crossing":
            counts["crossings"] += 1
        elif tags.get("footway") == "sidewalk":
            counts["sidewalks"] += 1
        elif hw == "steps":
            counts["steps"] += 1

    total = sum(counts.values())
    weighted = (
        counts["footways"] * 1
        + counts["pedestrian_zones"] * 3
        + counts["crossings"] * 2
        + counts["sidewalks"] * 1
        + counts["steps"] * 1
    )
    score = _clamp(min(10.0, weighted / 30.0))

    return {"counts": counts, "total": total, "score": round(score, 1)}


# =============================================================================
# CORE INTELLIGENCE COMPUTATION
# =============================================================================


@st.cache_data(ttl=900)
def compute_transport_intelligence(lat: float, lon: float) -> dict:
    """
    Orchestrate all six transport dimension analyses, compute scores,
    terrain context, and generate recommendations.

    Returns a comprehensive result dictionary.
    """
    # Fetch all six dimensions
    road_data = fetch_road_network(lat, lon)
    transit_data = fetch_public_transit(lat, lon)
    airport_data = fetch_airport_proximity(lat, lon)
    port_data = fetch_port_access(lat, lon)
    cycling_data = fetch_cycling_infra(lat, lon)
    pedestrian_data = fetch_pedestrian_access(lat, lon)

    # Fetch elevation context
    elevation_data = fetch_elevation_data(lat, lon)
    center_elevation = elevation_data.get("center_elevation", 0.0)
    grid_elevations = elevation_data.get("grid_elevations", [])
    valid_elevs = [e for e in grid_elevations if e is not None]
    elev_range = (max(valid_elevs) - min(valid_elevs)) if valid_elevs else 0.0
    elev_mean = (sum(valid_elevs) / len(valid_elevs)) if valid_elevs else 0.0

    # Dimension scores
    scores = {
        "Road Network Density": road_data["score"],
        "Public Transit Coverage": transit_data["score"],
        "Airport Proximity": airport_data["score"],
        "Port & Maritime Access": port_data["score"],
        "Cycling Infrastructure": cycling_data["score"],
        "Pedestrian Accessibility": pedestrian_data["score"],
    }

    # Weighted overall score
    overall = sum(
        scores[dim] * DIMENSION_WEIGHTS[dim] for dim in scores
    )
    overall = round(_clamp(overall), 1)

    # Terrain impact assessment
    terrain_notes = []
    if elev_range > 200:
        terrain_notes.append(
            f"Significant elevation variation ({elev_range:.0f} m) may impede road construction."
        )
    if center_elevation > 1500:
        terrain_notes.append(
            f"High elevation ({center_elevation:.0f} m) limits accessible transport modes."
        )
    if center_elevation < 5:
        terrain_notes.append(
            "Low-lying area -- maritime/port infrastructure may be feasible."
        )

    # Generate recommendations
    recommendations = []
    if road_data["score"] < 4:
        recommendations.append(
            "Road network is sparse. Investment in primary/secondary roads "
            "would significantly improve logistics connectivity."
        )
    if transit_data["score"] < 3:
        recommendations.append(
            "Public transit coverage is minimal. Consider bus route expansion "
            "or demand-responsive transit services."
        )
    if airport_data["score"] < 4:
        recommendations.append(
            "No airports nearby. Air freight requires long ground transfer distances."
        )
    if port_data["score"] < 2 and center_elevation < 50:
        recommendations.append(
            "Low-lying location without port access. Explore potential for "
            "inland waterway or river port development."
        )
    if cycling_data["score"] >= 6:
        recommendations.append(
            "Strong cycling infrastructure supports last-mile delivery "
            "and sustainable urban logistics."
        )
    if pedestrian_data["score"] >= 7:
        recommendations.append(
            "Excellent pedestrian infrastructure indicates dense urban fabric "
            "suitable for micro-logistics hubs."
        )
    if overall >= 7:
        recommendations.append(
            "Outstanding multimodal transport connectivity. Location is well-suited "
            "for logistics and distribution operations."
        )
    elif overall < 3:
        recommendations.append(
            "Transport infrastructure is severely limited. This location faces "
            "major logistics challenges for commercial operations."
        )

    if not recommendations:
        recommendations.append(
            "Transport infrastructure is adequate. Targeted improvements in weaker "
            "dimensions would enhance overall logistics performance."
        )

    return {
        "scores": scores,
        "overall_score": overall,
        "overall_label": _score_label(overall),
        "road": road_data,
        "transit": transit_data,
        "airport": airport_data,
        "port": port_data,
        "cycling": cycling_data,
        "pedestrian": pedestrian_data,
        "elevation": {
            "center_elevation": center_elevation,
            "grid_elevations": grid_elevations,
            "mean": round(elev_mean, 1),
            "range": round(elev_range, 1),
        },
        "terrain_notes": terrain_notes,
        "recommendations": recommendations,
    }


# =============================================================================
# PLOTLY CHARTS
# =============================================================================


def _build_radar_chart(scores: dict) -> go.Figure:
    """Build a Plotly radar chart for the six transport dimensions."""
    labels = list(scores.keys())
    values = [scores[k] for k in labels]

    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(6, 182, 212, 0.18)",
        line=dict(color=CLR_ACCENT, width=2.5),
        marker=dict(size=6, color=CLR_ACCENT),
        name="Transport Score",
    ))

    fig.update_layout(
        polar=dict(
            bgcolor=CLR_BG,
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                gridcolor="#2a2a3e",
                tickfont=dict(color=CLR_TEXT_SEC, size=10),
                dtick=2,
            ),
            angularaxis=dict(
                gridcolor="#2a2a3e",
                tickfont=dict(color=CLR_TEXT, size=11),
            ),
        ),
        paper_bgcolor="#0e0e1a",
        plot_bgcolor=CLR_BG,
        font=dict(color=CLR_TEXT),
        showlegend=False,
        height=450,
        margin=dict(t=40, b=40, l=80, r=80),
        title=dict(
            text="Transport Dimension Profile",
            font=dict(color=CLR_TEXT, size=16),
            x=0.5,
        ),
    )
    return fig


def _build_gauge_chart(score: float, label: str) -> go.Figure:
    """Build a Plotly gauge chart for the overall transport score."""
    color = _score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        number=dict(suffix="/10", font=dict(size=36, color=color)),
        title=dict(text=label, font=dict(size=16, color=CLR_TEXT)),
        gauge=dict(
            axis=dict(range=[0, 10], tickwidth=1, tickcolor=CLR_TEXT_SEC,
                      dtick=2, tickfont=dict(color=CLR_TEXT_SEC)),
            bar=dict(color=color, thickness=0.3),
            bgcolor=CLR_SURFACE,
            borderwidth=2,
            bordercolor=CLR_BORDER,
            steps=[
                dict(range=[0, 3], color="rgba(153,27,27,0.2)"),
                dict(range=[3, 6], color="rgba(245,158,11,0.13)"),
                dict(range=[6, 8], color="rgba(132,204,22,0.13)"),
                dict(range=[8, 10], color="rgba(34,197,94,0.13)"),
            ],
        ),
    ))
    fig.update_layout(
        paper_bgcolor="#0e0e1a",
        plot_bgcolor=CLR_BG,
        font=dict(color=CLR_TEXT),
        height=280,
        margin=dict(t=60, b=20, l=40, r=40),
    )
    return fig


def _build_infrastructure_bar_chart(result: dict) -> go.Figure:
    """Build a horizontal bar chart summarising infrastructure counts."""
    categories = []
    values = []
    colors = []

    # Road counts
    for road_type, count in result["road"]["counts"].items():
        categories.append(f"Road: {road_type.title()}")
        values.append(count)
        colors.append(DIMENSIONS["Road Network Density"]["color"])

    # Transit counts
    for t_type, count in result["transit"]["counts"].items():
        label = t_type.replace("_", " ").title()
        categories.append(f"Transit: {label}")
        values.append(count)
        colors.append(DIMENSIONS["Public Transit Coverage"]["color"])

    # Cycling counts
    for c_type, count in result["cycling"]["counts"].items():
        label = c_type.replace("_", " ").title()
        categories.append(f"Cycling: {label}")
        values.append(count)
        colors.append(DIMENSIONS["Cycling Infrastructure"]["color"])

    # Pedestrian counts
    for p_type, count in result["pedestrian"]["counts"].items():
        label = p_type.replace("_", " ").title()
        categories.append(f"Pedestrian: {label}")
        values.append(count)
        colors.append(DIMENSIONS["Pedestrian Accessibility"]["color"])

    fig = go.Figure(go.Bar(
        y=categories,
        x=values,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=values,
        textposition="auto",
        textfont=dict(color=CLR_TEXT, size=11),
    ))
    fig.update_layout(
        paper_bgcolor="#0e0e1a",
        plot_bgcolor=CLR_BG,
        font=dict(color=CLR_TEXT),
        xaxis=dict(
            gridcolor="#2a2a3e",
            title="Count",
            title_font=dict(color=CLR_TEXT_SEC),
            tickfont=dict(color=CLR_TEXT_SEC),
        ),
        yaxis=dict(
            tickfont=dict(color=CLR_TEXT, size=11),
            autorange="reversed",
        ),
        height=max(350, len(categories) * 28),
        margin=dict(t=30, b=40, l=180, r=30),
        title=dict(
            text="Infrastructure Element Counts",
            font=dict(color=CLR_TEXT, size=15),
            x=0.5,
        ),
    )
    return fig


# =============================================================================
# MAP BUILDER
# =============================================================================


def _build_transport_map(lat: float, lon: float, result: dict) -> object:
    """
    Build a Folium map with markers for airports, ports, and transit stops.
    Returns None if folium is not available.
    """
    try:
        import folium
        from folium.plugins import MarkerCluster
    except ImportError:
        logger.warning("Folium not available -- skipping map.")
        return None

    m = folium.Map(location=[lat, lon], zoom_start=11, tiles="CartoDB dark_matter")

    # Centre marker
    folium.Marker(
        location=[lat, lon],
        popup="Analysis Centre",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(m)

    # Airport markers
    for ap in result["airport"].get("airports", []):
        if ap.get("lat") and ap.get("lon"):
            label = f"{ap['name']}"
            if ap.get("iata"):
                label += f" ({ap['iata']})"
            label += f" - {ap['distance_km']} km"
            folium.Marker(
                location=[ap["lat"], ap["lon"]],
                popup=label,
                icon=folium.Icon(color="blue", icon="plane", prefix="fa"),
            ).add_to(m)

    # Port/maritime markers
    for fac in result["port"].get("facilities", []):
        # Port facilities may not have coordinates in our simplified model;
        # skip those that lack lat/lon
        pass

    # Radius circles for analysis extents
    folium.Circle(
        location=[lat, lon],
        radius=5000,
        color=DIMENSIONS["Road Network Density"]["color"],
        fill=False,
        weight=1.5,
        dash_array="5,5",
        popup="Road Network (5 km)",
    ).add_to(m)

    folium.Circle(
        location=[lat, lon],
        radius=3000,
        color=DIMENSIONS["Public Transit Coverage"]["color"],
        fill=False,
        weight=1.5,
        dash_array="5,5",
        popup="Transit Coverage (3 km)",
    ).add_to(m)

    folium.Circle(
        location=[lat, lon],
        radius=2000,
        color=DIMENSIONS["Pedestrian Accessibility"]["color"],
        fill=False,
        weight=1.5,
        dash_array="5,5",
        popup="Pedestrian Zone (2 km)",
    ).add_to(m)

    return m


# =============================================================================
# RENDER TAB
# =============================================================================


def render_transportation_ai_tab():
    """Render the Transportation & Logistics Intelligence tab in the Streamlit UI."""

    # -- Header ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_ACCENT};font-size:26px;">
                Transportation &amp; Logistics Intelligence
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Comprehensive transport infrastructure analysis across roads,
                transit, aviation, maritime, cycling, and pedestrian networks.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Location inputs -------------------------------------------------------
    c1, c2 = st.columns(2)
    lat = c1.number_input(
        "Latitude", value=41.9028, format="%.4f",
        min_value=-90.0, max_value=90.0, key="transport_lat",
    )
    lon = c2.number_input(
        "Longitude", value=12.4964, format="%.4f",
        min_value=-180.0, max_value=180.0, key="transport_lon",
    )

    run_btn = st.button(
        "Analyze Transport Infrastructure",
        type="primary",
        key="transport_btn",
        use_container_width=True,
    )

    if not run_btn:
        st.info(
            "Enter coordinates and click **Analyze Transport Infrastructure** "
            "to generate a full multimodal transport report."
        )
        return

    # -- Run analysis ----------------------------------------------------------
    with st.spinner("Analyzing transportation infrastructure across 6 dimensions..."):
        result = compute_transport_intelligence(lat, lon)

    scores = result["scores"]
    overall = result["overall_score"]
    overall_label = result["overall_label"]
    overall_color = _score_color(overall)

    # -- Overall score header --------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{overall_color}22,{CLR_BG});
                    padding:20px 24px;border-radius:12px;
                    border:1px solid {overall_color}66;margin:10px 0 20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;
                        flex-wrap:wrap;">
                <div>
                    <span style="font-size:14px;color:{CLR_TEXT_SEC};
                                 text-transform:uppercase;letter-spacing:1px;">
                        Overall Transport Score
                    </span>
                    <h1 style="margin:4px 0;color:{overall_color};font-size:42px;">
                        {overall}/10
                    </h1>
                    <span style="font-size:18px;color:{overall_color};font-weight:600;">
                        {escape(overall_label)}
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:13px;color:{CLR_TEXT_SEC};">
                        Location: {lat:.4f}, {lon:.4f}<br>
                        Elevation: {result['elevation']['center_elevation']:.0f} m<br>
                        Terrain range: {result['elevation']['range']:.0f} m
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Gauge chart -----------------------------------------------------------
    gauge_fig = _build_gauge_chart(overall, "Overall Transport Score")
    st.plotly_chart(gauge_fig, use_container_width=True, key="transport_gauge")

    # -- Dimension score cards -------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Transport Dimension Scores
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    dim_keys = list(scores.keys())
    row1 = dim_keys[:3]
    row2 = dim_keys[3:]

    for row_keys in (row1, row2):
        cols = st.columns(len(row_keys))
        for col, dim_name in zip(cols, row_keys):
            s = scores[dim_name]
            s_color = _score_color(s)
            s_label = _score_label(s)
            meta = DIMENSIONS.get(dim_name, {"desc": "", "color": CLR_ACCENT})
            bar_pct = max(5, s / 10 * 100)
            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE};border:1px solid {s_color}44;
                                border-radius:10px;padding:16px;text-align:center;
                                min-height:185px;">
                        <div style="font-size:13px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
                            {escape(dim_name)}
                        </div>
                        <div style="font-size:34px;font-weight:700;color:{s_color};">
                            {s}
                        </div>
                        <div style="font-size:12px;color:{s_color};font-weight:600;
                                    margin-bottom:8px;">
                            {escape(s_label)}
                        </div>
                        <div style="background:{CLR_BG};border-radius:4px;height:6px;
                                    margin:8px 0;">
                            <div style="background:{s_color};width:{bar_pct}%;
                                        height:6px;border-radius:4px;"></div>
                        </div>
                        <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-top:6px;">
                            {escape(meta['desc'])}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- Radar chart -----------------------------------------------------------
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    radar_fig = _build_radar_chart(scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="transport_radar")

    # -- Detailed breakdown tabs -----------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Detailed Infrastructure Breakdown
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_road, tab_transit, tab_airport, tab_port, tab_cycling, tab_ped = st.tabs([
        "Roads", "Transit", "Airports", "Ports", "Cycling", "Pedestrian",
    ])

    # -- Road tab --------------------------------------------------------------
    with tab_road:
        rd = result["road"]
        st.metric("Total Road Segments (5 km)", rd["total"])
        rcols = st.columns(5)
        for i, (rtype, rcount) in enumerate(rd["counts"].items()):
            with rcols[i]:
                st.metric(rtype.title(), rcount)
        st.markdown(
            f"<p style='color:{CLR_TEXT_SEC};font-size:13px;'>"
            f"Score is weighted by road class: motorways (x5), trunks (x4), "
            f"primary (x3), secondary (x2), tertiary (x1).</p>",
            unsafe_allow_html=True,
        )

    # -- Transit tab -----------------------------------------------------------
    with tab_transit:
        tr = result["transit"]
        st.metric("Total Transit Stops (3 km)", tr["total"])
        tcols = st.columns(4)
        labels = ["Bus Stops", "Train Stations", "Tram Stops", "Subway Stations"]
        for i, (ttype, tcount) in enumerate(tr["counts"].items()):
            with tcols[i]:
                st.metric(labels[i], tcount)

    # -- Airport tab -----------------------------------------------------------
    with tab_airport:
        ap = result["airport"]
        st.metric("Airports Found (50 km)", ap["count"])
        if ap["airports"]:
            st.metric("Nearest Airport Distance", f"{ap['nearest_distance_km']} km")
            for airport in ap["airports"]:
                iata_str = f" ({airport['iata']})" if airport.get("iata") else ""
                st.markdown(
                    f"<div style='background:{CLR_BG};padding:10px 14px;"
                    f"border-radius:8px;margin:6px 0;"
                    f"border-left:3px solid {DIMENSIONS['Airport Proximity']['color']};'>"
                    f"<span style='color:{CLR_TEXT};font-weight:600;'>"
                    f"{escape(airport['name'])}{escape(iata_str)}</span>"
                    f"<span style='color:{CLR_TEXT_SEC};margin-left:12px;'>"
                    f"{airport['distance_km']} km</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("No airports found within 50 km.")

    # -- Port tab --------------------------------------------------------------
    with tab_port:
        pt = result["port"]
        st.metric("Maritime Facilities (20 km)", pt["total"])
        pcols = st.columns(4)
        port_labels = ["Harbors", "Piers", "Ferry Terminals", "Ports"]
        for i, (ptype, pcount) in enumerate(pt["counts"].items()):
            with pcols[i]:
                st.metric(port_labels[i], pcount)
        if pt["facilities"]:
            for fac in pt["facilities"]:
                st.markdown(
                    f"<div style='background:{CLR_BG};padding:10px 14px;"
                    f"border-radius:8px;margin:6px 0;"
                    f"border-left:3px solid {DIMENSIONS['Port & Maritime Access']['color']};'>"
                    f"<span style='color:{CLR_TEXT};font-weight:600;'>"
                    f"{escape(fac['name'])}</span>"
                    f"<span style='color:{CLR_TEXT_SEC};margin-left:12px;'>"
                    f"{escape(fac['type'])} - {fac['distance_km']} km</span></div>",
                    unsafe_allow_html=True,
                )

    # -- Cycling tab -----------------------------------------------------------
    with tab_cycling:
        cy = result["cycling"]
        st.metric("Cycling Features (3 km)", cy["total"])
        ccols = st.columns(4)
        cycle_labels = ["Cycleways", "Bicycle Parking", "Bike Sharing", "Cycle Lanes"]
        for i, (ctype, ccount) in enumerate(cy["counts"].items()):
            with ccols[i]:
                st.metric(cycle_labels[i], ccount)

    # -- Pedestrian tab --------------------------------------------------------
    with tab_ped:
        pe = result["pedestrian"]
        st.metric("Pedestrian Features (2 km)", pe["total"])
        pecols = st.columns(5)
        ped_labels = ["Footways", "Pedestrian Zones", "Crossings", "Sidewalks", "Steps"]
        for i, (ptype, pcount) in enumerate(pe["counts"].items()):
            with pecols[i]:
                st.metric(ped_labels[i], pcount)

    # -- Infrastructure bar chart ----------------------------------------------
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    bar_fig = _build_infrastructure_bar_chart(result)
    st.plotly_chart(bar_fig, use_container_width=True, key="transport_bar")

    # -- Map -------------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Transport Infrastructure Map
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    transport_map = _build_transport_map(lat, lon, result)
    if transport_map is not None:
        try:
            from streamlit_folium import st_folium
            st_folium(transport_map, width=None, height=500, key="transport_map")
        except ImportError:
            import streamlit.components.v1 as components
            map_html = transport_map._repr_html_()
            components.html(map_html, height=500, scrolling=True)
    else:
        st.warning("Map visualisation requires the `folium` package.")

    # -- Terrain notes ---------------------------------------------------------
    if result["terrain_notes"]:
        st.markdown(
            f"""
            <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                        border:1px solid {CLR_BORDER};margin:20px 0 8px;">
                <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                    Terrain Impact Notes
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for note in result["terrain_notes"]:
            st.markdown(
                f"<div style='background:{CLR_BG};padding:12px 16px;"
                f"border-radius:8px;margin:6px 0;"
                f"border-left:3px solid {CLR_MODERATE};'>"
                f"<p style='color:{CLR_TEXT};margin:0;'>{escape(note)}</p></div>",
                unsafe_allow_html=True,
            )

    # -- Recommendations -------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Recommendations
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for rec in result["recommendations"]:
        st.markdown(
            f"<div style='background:{CLR_BG};padding:12px 16px;"
            f"border-radius:8px;margin:6px 0;"
            f"border-left:3px solid {CLR_ACCENT};'>"
            f"<p style='color:{CLR_TEXT};margin:0;'>{escape(rec)}</p></div>",
            unsafe_allow_html=True,
        )

    # -- Elevation context -----------------------------------------------------
    elev_data = result["elevation"]
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Elevation Context
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    elev_cols = st.columns(3)
    with elev_cols[0]:
        st.metric("Centre Elevation", f"{elev_data['center_elevation']:.0f} m")
    with elev_cols[1]:
        st.metric("Mean Elevation", f"{elev_data['mean']:.0f} m")
    with elev_cols[2]:
        st.metric("Elevation Range", f"{elev_data['range']:.0f} m")

    # Elevation profile mini chart
    if elev_data["grid_elevations"]:
        elev_fig = go.Figure()
        elev_fig.add_trace(go.Scatter(
            y=elev_data["grid_elevations"],
            mode="lines+markers",
            line=dict(color=CLR_ACCENT, width=2),
            marker=dict(size=5, color=CLR_ACCENT),
            fill="tozeroy",
            fillcolor="rgba(6,182,212,0.15)",
            name="Elevation",
        ))
        elev_fig.update_layout(
            paper_bgcolor="#0e0e1a",
            plot_bgcolor=CLR_BG,
            font=dict(color=CLR_TEXT),
            xaxis=dict(
                title="Grid Point",
                gridcolor="#2a2a3e",
                tickfont=dict(color=CLR_TEXT_SEC),
            ),
            yaxis=dict(
                title="Elevation (m)",
                gridcolor="#2a2a3e",
                tickfont=dict(color=CLR_TEXT_SEC),
            ),
            height=250,
            margin=dict(t=20, b=40, l=60, r=20),
            showlegend=False,
        )
        st.plotly_chart(elev_fig, use_container_width=True, key="transport_elev")

    # -- Footer ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_BG};padding:12px 16px;border-radius:8px;
                    margin-top:24px;text-align:center;">
            <span style="color:{CLR_TEXT_SEC};font-size:12px;">
                Data sources: Overpass API (OpenStreetMap) | Open-Elevation API |
                Analysis radius: 2-50 km depending on dimension |
                Cache TTL: 15 minutes
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )
