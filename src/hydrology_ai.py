"""
Hydrology Intelligence AI -- Water resources assessment combining surface water,
groundwater potential, precipitation, drainage quality, flood risk, drought
resilience & water infrastructure for any geographic location.

Uses FREE APIs only (no API key required):
  - Overpass API      (rivers, streams, lakes, springs, wells, dams, reservoirs,
                       wetlands, canals, water-works, pumping stations)
  - Open-Meteo        (precipitation current + 7-day forecast,
                       evapotranspiration estimate)
  - ISRIC SoilGrids   (clay / sand content -> drainage / aquifer proxy)
  - Open Topo Data    (elevation for watershed / slope analysis)
"""

import logging
import math
from html import escape

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
)

logger = logging.getLogger(__name__)

# =============================================================================
# THEME CONSTANTS
# =============================================================================

CLR_BG = "#1a1a2e"
CLR_SURFACE = "#16213e"
CLR_CARD = "#0f3460"
CLR_BORDER = "#1a4080"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"

CLR_EXCELLENT = "#22c55e"
CLR_GOOD = "#60a5fa"
CLR_FAIR = "#f59e0b"
CLR_POOR = "#ef4444"
CLR_HAZARDOUS = "#991b1b"

# =============================================================================
# HYDROLOGY COMPONENT DEFINITIONS
# =============================================================================

HYDRO_COMPONENTS = {
    "surface_water": {
        "name": "Surface Water",
        "color": "#3b82f6",
        "weight": 0.20,
        "description": "Rivers, streams, lakes and ponds density",
    },
    "groundwater": {
        "name": "Groundwater",
        "color": "#06b6d4",
        "weight": 0.15,
        "description": "Springs, wells and geological aquifer indicators",
    },
    "precipitation": {
        "name": "Precipitation",
        "color": "#8b5cf6",
        "weight": 0.15,
        "description": "Rainfall amount, distribution and reliability",
    },
    "drainage": {
        "name": "Drainage Quality",
        "color": "#22c55e",
        "weight": 0.10,
        "description": "Soil permeability from sand/clay ratio and slope",
    },
    "flood_risk": {
        "name": "Flood Risk",
        "color": "#ef4444",
        "weight": 0.15,
        "description": "Risk from low elevation, high water density, heavy rain",
    },
    "drought": {
        "name": "Drought Resilience",
        "color": "#f59e0b",
        "weight": 0.10,
        "description": "Water storage capacity and groundwater availability",
    },
    "infrastructure": {
        "name": "Water Infrastructure",
        "color": "#6366f1",
        "weight": 0.15,
        "description": "Dams, canals, water treatment and pumping stations",
    },
}

OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

# =============================================================================
# HELPERS
# =============================================================================


def _clamp(value, lo=0.0, hi=100.0):
    """Clamp a numeric value between lo and hi."""
    return max(lo, min(hi, float(value)))


def _safe_mean(values):
    """Return mean of non-None values, or 0.0 if empty."""
    cleaned = [v for v in (values or []) if v is not None]
    if not cleaned:
        return 0.0
    return sum(cleaned) / len(cleaned)


def _hydro_color(score):
    """Return hex colour for a 0-100 hydrology score."""
    if score > 80:
        return CLR_EXCELLENT
    if score > 60:
        return CLR_GOOD
    if score > 40:
        return CLR_FAIR
    if score > 20:
        return CLR_POOR
    return CLR_HAZARDOUS


def _classify_hydrology(score):
    """Return (label, colour) for a 0-100 hydrology index score."""
    if score > 80:
        return "Excellent", CLR_EXCELLENT
    if score > 60:
        return "Good", CLR_GOOD
    if score > 40:
        return "Moderate", CLR_FAIR
    if score > 20:
        return "Poor", CLR_POOR
    return "Critical", CLR_HAZARDOUS


# =============================================================================
# DATA FETCHERS
# =============================================================================


@st.cache_data(ttl=1800)
def fetch_hydrology_data(lat, lon, radius=5000):
    """Fetch comprehensive water-related features from the Overpass API.

    Categories returned via tags:
      - waterway=river/stream/canal/drain/ditch
      - natural=water (lakes, ponds)
      - natural=spring
      - man_made=water_well
      - natural=wetland
      - waterway=dam  (way + node)
      - landuse=reservoir
      - man_made=water_works
      - man_made=pumping_station
    """
    query = (
        f"[out:json][timeout:30];\n"
        f"(\n"
        f'  way["waterway"~"river|stream|canal|drain|ditch"]'
        f"(around:{radius},{lat},{lon});\n"
        f'  way["natural"="water"]'
        f"(around:{radius},{lat},{lon});\n"
        f'  node["natural"="spring"]'
        f"(around:{radius},{lat},{lon});\n"
        f'  node["man_made"="water_well"]'
        f"(around:{radius},{lat},{lon});\n"
        f'  way["natural"="wetland"]'
        f"(around:{radius},{lat},{lon});\n"
        f'  way["waterway"="dam"]'
        f"(around:{radius},{lat},{lon});\n"
        f'  node["waterway"="dam"]'
        f"(around:{radius},{lat},{lon});\n"
        f'  way["landuse"="reservoir"]'
        f"(around:{radius},{lat},{lon});\n"
        f'  node["man_made"="water_works"]'
        f"(around:{radius},{lat},{lon});\n"
        f'  node["man_made"="pumping_station"]'
        f"(around:{radius},{lat},{lon});\n"
        f");\n"
        f"out body;"
    )
    try:
        resp = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={"data": query},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Hydrology Overpass data error: %s", exc)
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_elevation_point(lat, lon):
    """Fetch elevation for a single point + small cross for slope estimate."""
    offset = 0.01  # ~1.1 km offset
    locations = (
        f"{lat},{lon}"
        f"|{lat + offset},{lon}"
        f"|{lat - offset},{lon}"
        f"|{lat},{lon + offset}"
        f"|{lat},{lon - offset}"
    )
    try:
        resp = requests.get(
            OPEN_TOPO_API,
            params={"locations": locations},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        elevations = []
        for r in results:
            e = r.get("elevation")
            elevations.append(float(e) if e is not None else 0.0)
        center = elevations[0] if elevations else 0.0
        return {
            "center": center,
            "min": min(elevations) if elevations else 0.0,
            "max": max(elevations) if elevations else 0.0,
            "slope_range": (max(elevations) - min(elevations)) if elevations else 0.0,
        }
    except Exception as exc:
        logger.warning("Elevation fetch error: %s", exc)
        return {"center": 0.0, "min": 0.0, "max": 0.0, "slope_range": 0.0}


# =============================================================================
# CLASSIFY OVERPASS ELEMENTS
# =============================================================================


def _classify_water_elements(elements):
    """Parse Overpass elements into hydrology categories.

    Returns a dict of counts and a list of typed dicts for details.
    """
    counts = {
        "rivers": 0,
        "streams": 0,
        "canals": 0,
        "drains": 0,
        "lakes": 0,
        "springs": 0,
        "wells": 0,
        "wetlands": 0,
        "dams": 0,
        "reservoirs": 0,
        "water_works": 0,
        "pumping_stations": 0,
    }
    typed = []

    for el in elements if isinstance(elements, list) else []:
        if not isinstance(el, dict):
            continue
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        if not isinstance(tags, dict):
            tags = {}

        waterway = tags.get("waterway", "")
        natural = tags.get("natural", "")
        man_made = tags.get("man_made", "")
        landuse = tags.get("landuse", "")
        name = tags.get("name", "")

        category = "other"

        if waterway == "river":
            counts["rivers"] += 1
            category = "river"
        elif waterway == "stream":
            counts["streams"] += 1
            category = "stream"
        elif waterway in ("canal", "drain", "ditch"):
            if waterway == "canal":
                counts["canals"] += 1
                category = "canal"
            else:
                counts["drains"] += 1
                category = "drain"
        elif waterway == "dam":
            counts["dams"] += 1
            category = "dam"
        elif natural == "water":
            counts["lakes"] += 1
            category = "lake"
        elif natural == "spring":
            counts["springs"] += 1
            category = "spring"
        elif natural == "wetland":
            counts["wetlands"] += 1
            category = "wetland"
        elif man_made == "water_well":
            counts["wells"] += 1
            category = "well"
        elif man_made == "water_works":
            counts["water_works"] += 1
            category = "water_works"
        elif man_made == "pumping_station":
            counts["pumping_stations"] += 1
            category = "pumping_station"
        elif landuse == "reservoir":
            counts["reservoirs"] += 1
            category = "reservoir"

        typed.append({"category": category, "name": name, "tags": tags})

    return counts, typed


# =============================================================================
# CORE: COMPUTE HYDROLOGY SCORES
# =============================================================================


@st.cache_data(ttl=1800)
def compute_hydrology(lat, lon):
    """Compute 7-dimension hydrology intelligence for a geographic point.

    Returns a dict with:
        overall_score       - 0-100 weighted index
        classification      - label string
        class_color         - hex colour
        dimension_scores    - dict of 7 component scores (0-100)
        counts              - water feature counts
        recommendations     - list of advisory strings
        daily_precip        - list of daily precipitation values
        daily_dates         - list of date strings for precip chart
        elevation           - elevation dict
        soil_summary        - dict with clay_pct, sand_pct
    """
    # ------------------------------------------------------------------
    # 1. Fetch all data sources
    # ------------------------------------------------------------------
    hydro_raw = fetch_hydrology_data(lat, lon)
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water_basic = fetch_water_features(lat, lon)
    elevation = fetch_elevation_point(lat, lon)

    # ------------------------------------------------------------------
    # 2. Parse Overpass elements (hydrology-specific query)
    # ------------------------------------------------------------------
    hydro_elements = (
        (hydro_raw if isinstance(hydro_raw, dict) else {}).get("elements", [])
    )
    counts, typed_features = _classify_water_elements(hydro_elements)

    # Also merge basic water features from deep_zone_analysis
    basic_elements = (
        (water_basic if isinstance(water_basic, dict) else {}).get("elements", [])
    )
    basic_counts, basic_typed = _classify_water_elements(basic_elements)

    # Merge (take max of each count to avoid double-counting)
    for key in counts:
        counts[key] = max(counts[key], basic_counts.get(key, 0))

    # ------------------------------------------------------------------
    # 3. Parse soil (layer_map pattern from SoilGrids)
    # ------------------------------------------------------------------
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {}
    for _l in _layers if isinstance(_layers, list) else []:
        _ln = _l.get("name", "") if isinstance(_l, dict) else ""
        if _ln:
            _layer_map[_ln] = _l

    def _sv(name, div=10):
        p = _layer_map.get(name, {})
        if isinstance(p, dict):
            depths = p.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay_pct = _sv("clay", 10)   # g/kg / 10 -> %
    sand_pct = _sv("sand", 10)
    soc_val = _sv("soc", 10)

    # ------------------------------------------------------------------
    # 4. Parse weather
    # ------------------------------------------------------------------
    current = (weather if isinstance(weather, dict) else {}).get("current", {})
    precip_now = current.get("precipitation", 0.0) or 0.0
    temp_c = current.get("temperature_2m", 15.0) or 15.0
    humidity = current.get("relative_humidity_2m", 50.0) or 50.0

    daily = (weather if isinstance(weather, dict) else {}).get("daily", {})
    daily_precip = daily.get("precipitation_sum", []) or []
    daily_dates = daily.get("time", []) or []
    daily_precip = [v if v is not None else 0.0 for v in daily_precip]

    avg_daily_precip = _safe_mean(daily_precip)
    total_7d_precip = sum(daily_precip)

    # Annualised rainfall estimate (mm/year) from 7-day average
    annual_precip_est = avg_daily_precip * 365.0

    # Precipitation reliability (lower std-dev relative to mean = more reliable)
    if daily_precip and avg_daily_precip > 0:
        precip_std = math.sqrt(
            sum((v - avg_daily_precip) ** 2 for v in daily_precip)
            / len(daily_precip)
        )
        precip_cv = precip_std / avg_daily_precip  # coefficient of variation
    else:
        precip_cv = 1.0  # unknown -> assume high variability

    # ------------------------------------------------------------------
    # 5. Parse elevation
    # ------------------------------------------------------------------
    center_elev = (
        elevation.get("center", 0.0)
        if isinstance(elevation, dict)
        else 0.0
    ) or 0.0
    slope_range = (
        elevation.get("slope_range", 0.0)
        if isinstance(elevation, dict)
        else 0.0
    ) or 0.0

    # ===================================================================
    # 6. SCORE ALL 7 DIMENSIONS (0-100)
    # ===================================================================
    dimension_scores = {}
    recommendations = []

    # ----- 6a. Surface Water ------------------------------------------
    #   rivers*10 + streams*5 + lakes*15 + canals*3
    sw_raw = (
        counts["rivers"] * 10
        + counts["streams"] * 5
        + counts["lakes"] * 15
        + counts["canals"] * 3
    )
    surface_water_score = _clamp(min(sw_raw, 100))
    dimension_scores["surface_water"] = round(surface_water_score, 1)

    if surface_water_score < 30:
        recommendations.append(
            "Very low surface water density detected. Consider rainwater "
            "harvesting and groundwater exploration for water supply."
        )

    # ----- 6b. Groundwater Potential ----------------------------------
    #   springs*20 + wells*15 + sand porosity proxy
    gw_feature_score = counts["springs"] * 20 + counts["wells"] * 15
    sand_porosity = 0.0
    if sand_pct is not None and sand_pct > 0:
        sand_porosity = min(30.0, sand_pct * 0.6)  # high sand = good aquifer
    groundwater_score = _clamp(gw_feature_score + sand_porosity)
    dimension_scores["groundwater"] = round(groundwater_score, 1)

    if groundwater_score < 30:
        recommendations.append(
            "Low groundwater potential estimated. Geological survey "
            "recommended before borehole drilling investments."
        )

    # ----- 6c. Precipitation ------------------------------------------
    #   500-1500 mm/year ideal -> score peaks at 1000mm
    #   Adjusted by reliability (low CV = bonus)
    if annual_precip_est <= 0:
        precip_score = 10.0  # desert-like
    elif annual_precip_est < 250:
        precip_score = 10.0 + (annual_precip_est / 250.0) * 15.0
    elif annual_precip_est < 500:
        precip_score = 25.0 + ((annual_precip_est - 250) / 250.0) * 25.0
    elif annual_precip_est <= 1500:
        precip_score = 50.0 + min(50.0, ((annual_precip_est - 500) / 500.0) * 30.0)
    elif annual_precip_est <= 2500:
        precip_score = 80.0 - ((annual_precip_est - 1500) / 1000.0) * 15.0
    else:
        precip_score = 65.0 - min(25.0, (annual_precip_est - 2500) / 500.0 * 10.0)

    # Reliability bonus/penalty
    if precip_cv < 0.5:
        precip_score += 10.0  # very consistent
    elif precip_cv > 2.0:
        precip_score -= 10.0  # highly erratic

    precip_score = _clamp(precip_score)
    dimension_scores["precipitation"] = round(precip_score, 1)

    if precip_score < 30:
        recommendations.append(
            "Precipitation levels are low or highly erratic. Water storage "
            "infrastructure (cisterns, reservoirs) is strongly recommended."
        )

    # ----- 6d. Drainage Quality ---------------------------------------
    #   High sand = good drainage = high score
    #   High clay = poor drainage = low score
    #   Slope adds drainage benefit (water runs off)
    drainage_score = 50.0  # neutral default
    if sand_pct is not None and clay_pct is not None:
        # sand-to-clay ratio drives permeability
        sand_ratio = sand_pct / max(sand_pct + clay_pct, 1.0)
        drainage_score = sand_ratio * 80.0
    elif sand_pct is not None:
        drainage_score = min(80.0, sand_pct * 1.2)
    elif clay_pct is not None:
        drainage_score = max(10.0, 80.0 - clay_pct * 1.5)

    # Slope contribution (moderate slope = good drainage, extreme = erosion)
    if slope_range > 0:
        if slope_range < 50:
            drainage_score += min(15.0, slope_range * 0.3)
        elif slope_range < 200:
            drainage_score += 10.0
        else:
            drainage_score -= 5.0  # extreme slope penalty

    drainage_score = _clamp(drainage_score)
    dimension_scores["drainage"] = round(drainage_score, 1)

    if drainage_score < 30:
        recommendations.append(
            "Poor soil drainage detected (high clay content). Consider "
            "drainage channels or raised-bed construction for development."
        )

    # ----- 6e. Flood Risk (INVERTED: lower risk = higher score) -------
    #   100 - (rivers*5 + low_elev_factor + high_rainfall*5 + wetlands*3)
    river_flood = min(25.0, (counts["rivers"] + counts["streams"]) * 5.0)
    low_elev_factor = 0.0
    if center_elev < 10:
        low_elev_factor = 30.0
    elif center_elev < 50:
        low_elev_factor = 20.0
    elif center_elev < 100:
        low_elev_factor = 10.0
    elif center_elev < 200:
        low_elev_factor = 5.0

    high_rain_factor = min(20.0, avg_daily_precip * 5.0)
    wetland_flood = min(15.0, counts["wetlands"] * 3.0)

    flood_penalty = river_flood + low_elev_factor + high_rain_factor + wetland_flood
    flood_risk_score = _clamp(100.0 - flood_penalty)
    dimension_scores["flood_risk"] = round(flood_risk_score, 1)

    if flood_risk_score < 40:
        recommendations.append(
            "FLOOD RISK WARNING: Low elevation combined with high water "
            "density and rainfall create significant flood exposure. "
            "Implement drainage, flood barriers, and early-warning systems."
        )

    # ----- 6f. Drought Resilience -------------------------------------
    #   reservoirs*25 + lakes*15 + groundwater_score*0.3
    storage_score = (
        counts["reservoirs"] * 25
        + counts["lakes"] * 15
        + counts["dams"] * 10
    )
    gw_contrib = groundwater_score * 0.3
    drought_score = _clamp(storage_score + gw_contrib)
    dimension_scores["drought"] = round(drought_score, 1)

    if drought_score < 30:
        recommendations.append(
            "Low drought resilience: insufficient water storage and limited "
            "groundwater. Develop reservoirs or underground water storage."
        )

    # ----- 6g. Water Infrastructure -----------------------------------
    #   dams*20 + water_works*15 + pumping_stations*10 + canals*5
    infra_raw = (
        counts["dams"] * 20
        + counts["water_works"] * 15
        + counts["pumping_stations"] * 10
        + counts["canals"] * 5
    )
    infra_score = _clamp(min(infra_raw, 100))
    dimension_scores["infrastructure"] = round(infra_score, 1)

    if infra_score < 20:
        recommendations.append(
            "Minimal water infrastructure detected. Investment in water "
            "treatment facilities and distribution networks is advised."
        )

    # ===================================================================
    # 7. OVERALL WEIGHTED SCORE
    # ===================================================================
    overall = 0.0
    for key, meta in HYDRO_COMPONENTS.items():
        overall += dimension_scores.get(key, 0.0) * meta["weight"]
    overall = round(overall, 1)

    classification, class_color = _classify_hydrology(overall)

    # General recommendation based on overall score
    if overall > 80:
        recommendations.insert(
            0,
            "Excellent water resource conditions. The area has strong "
            "hydrology fundamentals across multiple dimensions.",
        )
    elif overall > 60:
        recommendations.insert(
            0,
            "Good water resource profile. Some dimensions may benefit "
            "from targeted improvement; review individual scores.",
        )
    elif overall > 40:
        recommendations.insert(
            0,
            "Moderate water resources. Several constraints identified; "
            "prioritise the lowest-scoring dimensions for intervention.",
        )
    elif overall > 20:
        recommendations.insert(
            0,
            "Poor water resource conditions. Significant investment in "
            "water infrastructure and conservation is recommended.",
        )
    else:
        recommendations.insert(
            0,
            "CRITICAL: Severe water resource limitations across most "
            "dimensions. Emergency assessment and intervention required.",
        )

    # Water balance summary
    evap_estimate = max(0.0, temp_c * 0.15 + (100 - humidity) * 0.05)
    water_balance = avg_daily_precip - evap_estimate

    return {
        "overall_score": overall,
        "classification": classification,
        "class_color": class_color,
        "dimension_scores": dimension_scores,
        "counts": counts,
        "recommendations": recommendations,
        "daily_precip": daily_precip,
        "daily_dates": daily_dates,
        "elevation": elevation,
        "soil_summary": {
            "clay_pct": clay_pct,
            "sand_pct": sand_pct,
            "soc": soc_val,
        },
        "annual_precip_est": round(annual_precip_est, 0),
        "precip_cv": round(precip_cv, 2),
        "total_7d_precip": round(total_7d_precip, 1),
        "water_balance_daily": round(water_balance, 2),
        "typed_features": typed_features,
    }


# =============================================================================
# CHART BUILDERS
# =============================================================================


def _build_radar_chart(dimension_scores):
    """Build a radar chart for the 7 hydrology dimensions."""
    labels = []
    values = []
    colors = []
    for key, meta in HYDRO_COMPONENTS.items():
        labels.append(meta["name"])
        values.append(dimension_scores.get(key, 0))
        colors.append(meta["color"])

    # Close polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=labels_closed,
            fill="toself",
            fillcolor="rgba(59,130,246,0.15)",
            line={"color": "#60a5fa", "width": 2.5},
            marker={"color": colors + [colors[0]], "size": 8},
            name="Score",
            hovertemplate="%{theta}: %{r:.1f}/100<extra></extra>",
        )
    )
    fig.update_layout(
        polar={
            "bgcolor": CLR_SURFACE,
            "radialaxis": {
                "visible": True,
                "range": [0, 100],
                "tickfont": {"color": CLR_TEXT_SEC, "size": 10},
                "gridcolor": "#2a3550",
            },
            "angularaxis": {
                "tickfont": {"color": CLR_TEXT, "size": 11},
                "gridcolor": "#2a3550",
            },
        },
        showlegend=False,
        height=420,
        margin=dict(l=60, r=60, t=40, b=40),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        font={"color": CLR_TEXT},
    )
    return fig


def _build_feature_pie(counts):
    """Build a pie chart showing water feature type distribution."""
    labels = []
    values = []
    colors_list = [
        "#3b82f6", "#06b6d4", "#22c55e", "#8b5cf6",
        "#f59e0b", "#ef4444", "#6366f1", "#ec4899",
        "#14b8a6", "#f97316", "#a855f7", "#64748b",
    ]
    for i, (key, val) in enumerate(counts.items()):
        if val > 0:
            label = key.replace("_", " ").title()
            labels.append(label)
            values.append(val)

    if not values:
        labels = ["No features"]
        values = [1]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                marker={"colors": colors_list[: len(labels)]},
                textinfo="label+value",
                textfont={"color": CLR_TEXT, "size": 11},
                hole=0.4,
                hovertemplate="%{label}: %{value}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        showlegend=True,
        legend={"font": {"color": CLR_TEXT, "size": 11}},
        height=380,
        margin=dict(l=20, r=20, t=30, b=20),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        font={"color": CLR_TEXT},
    )
    return fig


def _build_precip_bar(dates, values):
    """Build a bar chart of daily precipitation."""
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=dates,
            y=values,
            marker_color="#8b5cf6",
            hovertemplate="Date: %{x}<br>Precipitation: %{y:.1f} mm<extra></extra>",
            name="Precipitation",
        )
    )
    fig.update_layout(
        xaxis={"title": "Date", "color": CLR_TEXT_SEC, "gridcolor": "#2a3550"},
        yaxis={
            "title": "Precipitation (mm)",
            "color": CLR_TEXT_SEC,
            "gridcolor": "#2a3550",
        },
        height=320,
        margin=dict(l=50, r=20, t=30, b=50),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_SURFACE,
        font={"color": CLR_TEXT},
        showlegend=False,
    )
    return fig


# =============================================================================
# RENDER - MAIN ENTRY POINT
# =============================================================================


def render_hydrology_ai_tab():
    """Render the Hydrology Intelligence AI tab in the Streamlit UI."""

    # -- Header --------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},#1e3a5f);
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">
                Hydrology Intelligence AI
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Comprehensive water resources assessment combining surface water,
                groundwater, precipitation, drainage, flood risk, drought resilience
                &amp; water infrastructure analysis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Location selector ---------------------------------------------
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="hydro_preset",
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
            key="hydro_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude",
            value=default_lon,
            format="%.5f",
            min_value=-180.0,
            max_value=180.0,
            key="hydro_lon",
        )

    run_btn = st.button(
        "Analyse Hydrology",
        type="primary",
        key="hydro_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info(
            "Select a location and click **Analyse Hydrology** to begin "
            "the water resources assessment."
        )
        return

    # -- Run analysis --------------------------------------------------
    with st.spinner(
        "Fetching hydrology, soil, weather and elevation data..."
    ):
        result = compute_hydrology(lat, lon)

    overall = result["overall_score"]
    classification = result["classification"]
    class_color = result["class_color"]
    dim_scores = result["dimension_scores"]
    counts = result["counts"]
    recs = result["recommendations"]
    daily_precip = result["daily_precip"]
    daily_dates = result["daily_dates"]
    elevation = result["elevation"]
    soil_summary = result["soil_summary"]
    annual_precip_est = result["annual_precip_est"]
    water_balance = result["water_balance_daily"]

    # -- Overall score header ------------------------------------------
    total_features = sum(counts.values())
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{class_color}22,{CLR_BG});
                    padding:20px 24px;border-radius:12px;
                    border:1px solid {class_color}66;margin:10px 0 20px;">
            <div style="display:flex;align-items:center;justify-content:space-between;
                        flex-wrap:wrap;">
                <div>
                    <span style="font-size:14px;color:{CLR_TEXT_SEC};
                                 text-transform:uppercase;letter-spacing:1px;">
                        Hydrology Intelligence Index
                    </span>
                    <h1 style="margin:4px 0;color:{class_color};font-size:48px;">
                        {overall}/100
                    </h1>
                    <span style="font-size:18px;color:{class_color};font-weight:600;">
                        {escape(classification)}
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:13px;color:{CLR_TEXT_SEC};">
                        Location: {lat:.4f}, {lon:.4f}<br>
                        Elevation: {elevation.get('center', 0.0):.0f} m<br>
                        Water Features: {total_features} detected<br>
                        Dimensions: 7 assessed
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- 7 Dimension Metric Cards --------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Hydrology Dimension Scores
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    dim_keys = list(HYDRO_COMPONENTS.keys())
    # Row 1: first 4, Row 2: remaining 3 (+ empty col for balance)
    row1_keys = dim_keys[:4]
    row2_keys = dim_keys[4:]

    for row_keys in (row1_keys, row2_keys):
        cols = st.columns(4)
        for idx, col in enumerate(cols):
            if idx >= len(row_keys):
                break
            key = row_keys[idx]
            meta = HYDRO_COMPONENTS[key]
            score_val = dim_scores.get(key, 0)
            s_color = _hydro_color(score_val)
            bar_width = max(5, score_val)

            # Build detail line based on dimension
            detail = ""
            if key == "surface_water":
                detail = (
                    f"Rivers: {counts['rivers']} | "
                    f"Streams: {counts['streams']} | "
                    f"Lakes: {counts['lakes']}"
                )
            elif key == "groundwater":
                detail = (
                    f"Springs: {counts['springs']} | "
                    f"Wells: {counts['wells']}"
                )
                if soil_summary.get("sand_pct") is not None:
                    detail += f" | Sand: {soil_summary['sand_pct']:.0f}%"
            elif key == "precipitation":
                detail = (
                    f"Est. annual: {annual_precip_est:.0f} mm | "
                    f"CV: {result['precip_cv']:.2f}"
                )
            elif key == "drainage":
                clay_str = (
                    f"{soil_summary['clay_pct']:.0f}%"
                    if soil_summary.get("clay_pct") is not None
                    else "N/A"
                )
                sand_str = (
                    f"{soil_summary['sand_pct']:.0f}%"
                    if soil_summary.get("sand_pct") is not None
                    else "N/A"
                )
                detail = (
                    f"Clay: {clay_str} | "
                    f"Sand: {sand_str} | "
                    f"Slope: {elevation.get('slope_range', 0):.0f} m"
                )
            elif key == "flood_risk":
                detail = (
                    f"Elev: {elevation.get('center', 0):.0f} m | "
                    f"Wetlands: {counts['wetlands']}"
                )
            elif key == "drought":
                detail = (
                    f"Reservoirs: {counts['reservoirs']} | "
                    f"Lakes: {counts['lakes']} | "
                    f"Dams: {counts['dams']}"
                )
            elif key == "infrastructure":
                detail = (
                    f"Dams: {counts['dams']} | "
                    f"Works: {counts['water_works']} | "
                    f"Pumps: {counts['pumping_stations']}"
                )

            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE};
                                border:1px solid {meta['color']}44;
                                border-radius:10px;padding:16px;
                                text-align:center;min-height:210px;">
                        <div style="font-size:13px;color:{CLR_TEXT_SEC};
                                    margin-bottom:4px;">
                            {escape(meta['name'])}
                        </div>
                        <div style="font-size:34px;font-weight:700;
                                    color:{s_color};">
                            {score_val}
                        </div>
                        <div style="background:{CLR_BG};border-radius:4px;
                                    height:6px;margin:10px 0 6px;">
                            <div style="background:{s_color};
                                        width:{bar_width}%;height:6px;
                                        border-radius:4px;"></div>
                        </div>
                        <div style="font-size:10px;color:{CLR_TEXT_SEC};
                                    line-height:1.3;margin-bottom:6px;">
                            {escape(meta['description'])}
                        </div>
                        <div style="font-size:10px;color:{meta['color']};
                                    line-height:1.3;">
                            {escape(detail)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- Radar Chart ---------------------------------------------------
    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Hydrology Profile Radar
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    radar_fig = _build_radar_chart(dim_scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="hydro_radar")

    # -- Water Feature Pie Chart + Precipitation Bar Chart side-by-side -
    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown(
            f"""
            <div style="background:{CLR_SURFACE};padding:16px 20px;
                        border-radius:10px;
                        border:1px solid {CLR_BORDER};margin:16px 0 8px;">
                <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                    Water Feature Distribution
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        pie_fig = _build_feature_pie(counts)
        st.plotly_chart(pie_fig, use_container_width=True, key="hydro_pie")

    with right_col:
        st.markdown(
            f"""
            <div style="background:{CLR_SURFACE};padding:16px 20px;
                        border-radius:10px;
                        border:1px solid {CLR_BORDER};margin:16px 0 8px;">
                <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                    7-Day Precipitation
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if daily_dates and daily_precip:
            precip_fig = _build_precip_bar(daily_dates, daily_precip)
            st.plotly_chart(
                precip_fig, use_container_width=True, key="hydro_precip"
            )
        else:
            st.info("No precipitation forecast data available.")

    # -- Water Balance Summary -----------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Water Balance Summary
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    bal_cols = st.columns(4)
    balance_items = [
        (
            "Est. Annual Rainfall",
            f"{annual_precip_est:.0f} mm/yr",
            "#8b5cf6",
        ),
        (
            "7-Day Total Precip",
            f"{result['total_7d_precip']:.1f} mm",
            "#3b82f6",
        ),
        (
            "Daily Water Balance",
            f"{water_balance:+.2f} mm/day",
            CLR_EXCELLENT if water_balance >= 0 else CLR_POOR,
        ),
        (
            "Elevation",
            f"{elevation.get('center', 0):.0f} m (range {elevation.get('slope_range', 0):.0f} m)",
            "#06b6d4",
        ),
    ]

    for col, (label, value_str, color) in zip(bal_cols, balance_items):
        with col:
            st.markdown(
                f"""
                <div style="background:{CLR_BG};border:1px solid {color}44;
                            border-radius:10px;padding:16px;text-align:center;">
                    <div style="font-size:12px;color:{CLR_TEXT_SEC};">
                        {escape(label)}
                    </div>
                    <div style="font-size:22px;font-weight:700;color:{color};
                                margin:6px 0;">
                        {escape(value_str)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -- Soil Drainage Profile -----------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Soil Drainage Profile
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    soil_cols = st.columns(3)
    soil_items = [
        (
            "Clay Content",
            f"{soil_summary['clay_pct']:.1f}%"
            if soil_summary.get("clay_pct") is not None
            else "N/A",
            "#f59e0b",
            "High clay = poor drainage",
        ),
        (
            "Sand Content",
            f"{soil_summary['sand_pct']:.1f}%"
            if soil_summary.get("sand_pct") is not None
            else "N/A",
            "#ef4444",
            "High sand = good drainage / aquifer",
        ),
        (
            "Organic Carbon",
            f"{soil_summary['soc']:.1f} g/kg"
            if soil_summary.get("soc") is not None
            else "N/A",
            "#10b981",
            "Affects water retention capacity",
        ),
    ]

    for col, (label, value_str, color, desc) in zip(soil_cols, soil_items):
        with col:
            st.markdown(
                f"""
                <div style="background:{CLR_BG};border:1px solid {color}44;
                            border-radius:10px;padding:16px;text-align:center;">
                    <div style="font-size:12px;color:{CLR_TEXT_SEC};">
                        {escape(label)}
                    </div>
                    <div style="font-size:28px;font-weight:700;color:{color};
                                margin:6px 0;">
                        {escape(value_str)}
                    </div>
                    <div style="font-size:10px;color:{CLR_TEXT_SEC};">
                        {escape(desc)}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -- Recommendations -----------------------------------------------
    if recs:
        st.markdown(
            f"""
            <div style="background:{CLR_SURFACE};padding:16px 20px;
                        border-radius:10px;
                        border:1px solid {CLR_BORDER};margin:20px 0 8px;">
                <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                    Recommendations
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for rec in recs:
            is_alert = "WARNING" in rec or "CRITICAL" in rec
            card_border = CLR_POOR if is_alert else CLR_BORDER
            icon_color = CLR_POOR if is_alert else "#60a5fa"
            left_border = CLR_POOR if is_alert else "#60a5fa"

            st.markdown(
                f"""
                <div style="background:{CLR_BG};border:1px solid {card_border};
                            border-left:4px solid {left_border};
                            border-radius:8px;padding:12px 16px;margin:6px 0;">
                    <span style="color:{icon_color};font-size:13px;">
                        {escape(rec)}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
