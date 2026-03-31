"""
Archaeological Potential AI -- Assesses archaeological potential combining
known sites, terrain analysis, geological context, and preservation conditions.
Uses: Overpass, Macrostrat, Open Topo Data, Open-Meteo, SoilGrids.
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
    fetch_elevation_grid,
    fetch_geology,
    haversine_distance,
)

logger = logging.getLogger(__name__)

# ==============================================================================
# THEME CONSTANTS
# ==============================================================================

CLR_BG = "#1a1a2e"
CLR_SURFACE = "#16213e"
CLR_CARD = "#0f3460"
CLR_BORDER = "#1a4080"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"

CLR_HIGH = "#22c55e"
CLR_MODERATE = "#f59e0b"
CLR_LOW = "#ef4444"

# ==============================================================================
# ARCHAEOLOGICAL ANALYSIS COMPONENTS
# ==============================================================================

ARCH_COMPONENTS = {
    "known_sites": {"name": "Known Sites", "color": "#f59e0b", "weight": 0.25},
    "terrain": {"name": "Terrain Suitability", "color": "#22c55e", "weight": 0.20},
    "geological": {"name": "Geological Context", "color": "#8b5cf6", "weight": 0.15},
    "settlement": {"name": "Settlement Pattern", "color": "#3b82f6", "weight": 0.15},
    "preservation": {"name": "Preservation Conditions", "color": "#ec4899", "weight": 0.15},
    "discovery": {"name": "Discovery Probability", "color": "#ef4444", "weight": 0.10},
}


# ==============================================================================
# HELPERS
# ==============================================================================

def _clamp(value, lo=0.0, hi=100.0):
    """Clamp a numeric value between lo and hi."""
    return max(lo, min(hi, float(value or 0)))


def _class_label(score):
    """Return High / Moderate / Low classification."""
    if score >= 65:
        return "High"
    if score >= 35:
        return "Moderate"
    return "Low"


def _class_color(score):
    """Return colour for classification."""
    if score >= 65:
        return CLR_HIGH
    if score >= 35:
        return CLR_MODERATE
    return CLR_LOW


# ==============================================================================
# DATA FETCHERS
# ==============================================================================

@st.cache_data(ttl=1800)
def fetch_archaeological_sites(lat, lon, radius=5000):
    """Fetch archaeological and historic features from Overpass API."""
    query = f"""
    [out:json][timeout:30];
    (
      node["historic"](around:{radius},{lat},{lon});
      way["historic"](around:{radius},{lat},{lon});
      node["archaeological_site"](around:{radius},{lat},{lon});
      way["archaeological_site"](around:{radius},{lat},{lon});
      node["historic"="castle"](around:{radius},{lat},{lon});
      way["historic"="castle"](around:{radius},{lat},{lon});
      node["historic"="ruins"](around:{radius},{lat},{lon});
      way["historic"="ruins"](around:{radius},{lat},{lon});
      node["tourism"="museum"](around:{radius},{lat},{lon});
      node["heritage"](around:{radius},{lat},{lon});
    );
    out body center;
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
        logger.warning(f"Overpass archaeological error: {e}")
        return {"elements": []}


@st.cache_data(ttl=1800)
def fetch_macrostrat_geology(lat, lon):
    """Fetch geological context from Macrostrat for archaeological analysis."""
    return fetch_geology(lat, lon)


# ==============================================================================
# SCORING FUNCTIONS
# ==============================================================================

def _parse_site_list(arch_data, lat, lon):
    """Parse Overpass archaeological data into a structured list of sites."""
    elements = (arch_data if isinstance(arch_data, dict) else {}).get("elements", [])
    if not isinstance(elements, list):
        elements = []
    sites = []
    for el in elements:
        tags = el.get("tags", {}) or {}
        name = tags.get("name", tags.get("historic", tags.get("tourism", "Unknown site")))
        site_type = (
            tags.get("historic")
            or tags.get("archaeological_site")
            or tags.get("tourism")
            or tags.get("heritage")
            or "unknown"
        )
        # Get coordinates -- nodes have lat/lon directly; ways may have center
        s_lat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        s_lon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        dist = None
        if s_lat is not None and s_lon is not None:
            dist = haversine_distance(lat, lon, float(s_lat), float(s_lon))
        sites.append({
            "name": str(name),
            "type": str(site_type),
            "distance_km": dist,
            "lat": s_lat,
            "lon": s_lon,
        })
    # Sort by distance (None at end)
    sites.sort(key=lambda s: s.get("distance_km") if s.get("distance_km") is not None else 9999)
    return sites


def _score_known_sites(sites):
    """Score 0-100 based on proximity and density of known archaeological sites."""
    if not sites:
        return 15.0, "No known archaeological or historic sites within search radius"

    count = len(sites)
    distances = [s.get("distance_km") for s in sites if s.get("distance_km") is not None]
    min_dist = min(distances) if distances else 99

    # Density component (max 50 points)
    if count >= 20:
        density_score = 50.0
    elif count >= 10:
        density_score = 40.0
    elif count >= 5:
        density_score = 30.0
    elif count >= 2:
        density_score = 20.0
    else:
        density_score = 10.0

    # Proximity component (max 50 points)
    if min_dist < 0.5:
        proximity_score = 50.0
    elif min_dist < 1.0:
        proximity_score = 40.0
    elif min_dist < 2.0:
        proximity_score = 30.0
    elif min_dist < 3.0:
        proximity_score = 20.0
    else:
        proximity_score = 10.0

    score = _clamp(density_score + proximity_score)
    detail = f"{count} historic/archaeological features found"
    if distances:
        detail += f"; nearest {min_dist:.1f} km away"
    return score, detail


def _score_terrain(elev_data):
    """Score 0-100 for terrain suitability for ancient settlements."""
    raw_elevations = (elev_data if isinstance(elev_data, dict) else {}).get(
        "grid_elevations", []
    )
    elevations = [e for e in (raw_elevations if isinstance(raw_elevations, list) else [])
                  if e is not None]
    center_elev = (elev_data if isinstance(elev_data, dict) else {}).get(
        "center_elevation", 0.0
    ) or 0.0
    elev_min = min(elevations) if elevations else 0.0
    elev_max = max(elevations) if elevations else 0.0
    elev_range = elev_max - elev_min

    score = 50.0
    details = []

    # Ideal elevation for ancient settlements: 50-500m (not too high, not coastal flood-prone)
    if 50 <= center_elev <= 500:
        score += 20.0
        details.append(f"Ideal elevation ({center_elev:.0f}m)")
    elif 20 <= center_elev <= 1000:
        score += 10.0
        details.append(f"Acceptable elevation ({center_elev:.0f}m)")
    elif center_elev < 5:
        score -= 10.0
        details.append(f"Very low elevation ({center_elev:.0f}m), coastal/flood-prone")
    elif center_elev > 2000:
        score -= 15.0
        details.append(f"High altitude ({center_elev:.0f}m), harsh conditions")
    else:
        details.append(f"Elevation {center_elev:.0f}m")

    # Gentle slopes preferred (hills with defensible positions)
    if 10 <= elev_range <= 50:
        score += 20.0
        details.append("Gentle slopes -- ideal defensive position")
    elif 5 <= elev_range <= 100:
        score += 10.0
        details.append("Moderate terrain variation")
    elif elev_range < 5:
        score += 5.0
        details.append("Very flat terrain")
    else:
        score -= 5.0
        details.append(f"Steep terrain ({elev_range:.0f}m range)")

    # Hilltop bonus (center higher than surroundings)
    avg_elev = sum(elevations) / len(elevations) if elevations else center_elev
    if center_elev > avg_elev + 5:
        score += 10.0
        details.append("Hilltop position -- defensible")

    return _clamp(score), "; ".join(details)


def _score_geological(geo_data):
    """Score 0-100 for geological context (sedimentary layers = preservation)."""
    units = (geo_data if isinstance(geo_data, dict) else {}).get("success", {})
    if isinstance(units, dict):
        data_list = units.get("data", [])
    else:
        data_list = []
    if not isinstance(data_list, list):
        data_list = []

    if not data_list:
        return 40.0, "No geological unit data available"

    score = 40.0
    details = []

    for item in data_list:
        lith = str(item.get("lith", "") or "").lower()
        strat_name = item.get("strat_name_long") or item.get("strat_name") or item.get("name") or "Unknown"
        period = item.get("t_int_name", "Unknown") or "Unknown"
        age = item.get("t_age")

        # Sedimentary rocks are best for preservation
        sedimentary_keywords = [
            "sandstone", "limestone", "shale", "mudstone", "siltstone",
            "chalk", "marl", "conglomerate", "clay", "sedimentary",
            "carbonate", "dolomite", "travertine",
        ]
        igneous_keywords = [
            "basalt", "granite", "volcanic", "lava", "ignite",
            "andesite", "rhyolite", "pumice", "tuff",
        ]
        metamorphic_keywords = [
            "marble", "slate", "schist", "gneiss", "quartzite", "metamorphic",
        ]

        if any(kw in lith for kw in sedimentary_keywords):
            score += 15.0
            details.append(f"Sedimentary ({strat_name}) -- excellent preservation potential")
        elif any(kw in lith for kw in igneous_keywords):
            score += 5.0
            details.append(f"Igneous ({strat_name}) -- may contain volcanic context")
        elif any(kw in lith for kw in metamorphic_keywords):
            score += 8.0
            details.append(f"Metamorphic ({strat_name}) -- moderate preservation")
        else:
            score += 5.0
            details.append(f"{strat_name} ({period})")

        # Age bonus -- older geological periods more likely to have ancient finds
        if age is not None:
            try:
                age_val = float(age)
                if age_val < 66:
                    score += 5.0  # Cenozoic -- recent enough for human artefacts
            except (ValueError, TypeError):
                pass

        # Process only first few units
        if len(details) >= 3:
            break

    return _clamp(score), "; ".join(details) if details else "Geological context analysed"


def _score_settlement_pattern(elev_data, water_data, sites):
    """Score 0-100 for ancient settlement pattern indicators."""
    score = 30.0
    details = []

    # Water proximity -- ancient settlements needed water
    water_elements = (water_data if isinstance(water_data, dict) else {}).get("elements", [])
    if not isinstance(water_elements, list):
        water_elements = []

    rivers = [e for e in water_elements
              if (e.get("tags", {}) or {}).get("waterway") in ("river", "stream", "canal")]
    springs = [e for e in water_elements
               if (e.get("tags", {}) or {}).get("natural") == "spring"]
    lakes = [e for e in water_elements
             if (e.get("tags", {}) or {}).get("natural") == "water"]
    water_total = len(rivers) + len(springs) + len(lakes)

    if water_total >= 5:
        score += 25.0
        details.append(f"Abundant water ({len(rivers)} rivers, {len(springs)} springs)")
    elif water_total >= 2:
        score += 15.0
        details.append(f"Water accessible ({water_total} features)")
    elif water_total >= 1:
        score += 8.0
        details.append("Limited water supply nearby")
    else:
        details.append("No water features detected -- unusual for settlements")

    # Defensible position -- elevation advantage
    center_elev = (elev_data if isinstance(elev_data, dict) else {}).get(
        "center_elevation", 0.0
    ) or 0.0
    raw_elevations = (elev_data if isinstance(elev_data, dict) else {}).get(
        "grid_elevations", []
    )
    elevations = [e for e in (raw_elevations if isinstance(raw_elevations, list) else [])
                  if e is not None]
    avg_elev = sum(elevations) / len(elevations) if elevations else center_elev

    if center_elev > avg_elev + 10:
        score += 15.0
        details.append("Elevated defensive position")
    elif center_elev > avg_elev + 3:
        score += 8.0
        details.append("Slightly elevated position")

    # Trade route indicator -- intersecting roads / paths suggest historic routes
    road_features = [e for e in water_elements
                     if (e.get("tags", {}) or {}).get("highway")]
    # Also check proximity to known sites as clustering indicator
    if sites and len(sites) >= 3:
        score += 10.0
        details.append("Multiple historic sites suggest settlement corridor")
    elif sites and len(sites) >= 1:
        score += 5.0
        details.append("Some historic presence in the area")

    # River confluence bonus (junction of rivers = trade hub)
    if len(rivers) >= 2:
        score += 10.0
        details.append("Multiple waterways -- potential trade junction")

    return _clamp(score), "; ".join(details) if details else "Settlement pattern analysis complete"


def _score_preservation(weather_data, soil_data):
    """Score 0-100 for preservation conditions (climate + soil)."""
    score = 40.0
    details = []

    # Climate analysis -- dry and cold climates preserve better
    current = (weather_data if isinstance(weather_data, dict) else {}).get("current", {})
    if not isinstance(current, dict):
        current = {}
    temp_c = current.get("temperature_2m", 20.0) or 20.0
    humidity = current.get("relative_humidity_2m", 50.0) or 50.0
    precip = current.get("precipitation", 0.0) or 0.0

    daily = (weather_data if isinstance(weather_data, dict) else {}).get("daily", {})
    if not isinstance(daily, dict):
        daily = {}
    daily_precip = daily.get("precipitation_sum", [])
    if not isinstance(daily_precip, list):
        daily_precip = []
    total_precip_7d = sum(v for v in daily_precip if v is not None)

    # Dry climates preserve better
    if humidity < 40:
        score += 15.0
        details.append(f"Low humidity ({humidity:.0f}%) -- excellent for preservation")
    elif humidity < 55:
        score += 10.0
        details.append(f"Moderate humidity ({humidity:.0f}%)")
    elif humidity > 80:
        score -= 10.0
        details.append(f"High humidity ({humidity:.0f}%) -- accelerates decay")
    else:
        details.append(f"Humidity {humidity:.0f}%")

    # Temperature
    if temp_c < 5:
        score += 10.0
        details.append(f"Cold conditions ({temp_c:.1f}C) -- slows decomposition")
    elif temp_c < 15:
        score += 5.0
        details.append(f"Cool conditions ({temp_c:.1f}C)")
    elif temp_c > 35:
        score += 8.0
        details.append(f"Hot/arid conditions ({temp_c:.1f}C) -- desiccation preserves")
    else:
        details.append(f"Temperature {temp_c:.1f}C")

    # Rainfall
    if total_precip_7d < 5:
        score += 10.0
        details.append("Very low rainfall -- dry preservation")
    elif total_precip_7d < 20:
        score += 5.0
    elif total_precip_7d > 80:
        score -= 10.0
        details.append("Heavy rainfall -- erosion risk")

    # Soil pH -- neutral to slightly alkaline preserves bone/organic material
    raw_props = (soil_data if isinstance(soil_data, dict) else {}).get("properties", {})
    if not isinstance(raw_props, dict):
        raw_props = {}
    _layers = raw_props.get("layers", [])
    _layer_map = {}
    for _l in (_layers if isinstance(_layers, list) else []):
        _ln = _l.get("name", "") if isinstance(_l, dict) else ""
        if _ln:
            _layer_map[_ln] = _l
    ph_data = _layer_map.get("phh2o", {})
    if isinstance(ph_data, dict):
        depths = ph_data.get("depths", [])
        if isinstance(depths, list) and depths:
            ph_mean = (depths[0].get("values", {}) or {}).get("mean")
            if ph_mean is not None:
                ph_val = (ph_mean or 0) / 10.0
                if 6.5 <= ph_val <= 8.0:
                    score += 10.0
                    details.append(f"Soil pH {ph_val:.1f} -- ideal for bone/organic preservation")
                elif 5.5 <= ph_val <= 8.5:
                    score += 5.0
                    details.append(f"Soil pH {ph_val:.1f} -- acceptable")
                else:
                    score -= 5.0
                    details.append(f"Soil pH {ph_val:.1f} -- acidic soils degrade organic material")

    # Calcium carbonate / clay content affects preservation
    clay_data = _layer_map.get("clay", {})
    if isinstance(clay_data, dict):
        clay_depths = clay_data.get("depths", [])
        if isinstance(clay_depths, list) and clay_depths:
            clay_mean = (clay_depths[0].get("values", {}) or {}).get("mean")
            if clay_mean is not None:
                clay_pct = (clay_mean or 0) / 10.0
                if 15 <= clay_pct <= 35:
                    score += 5.0
                    details.append(f"Clay {clay_pct:.0f}% -- seals artefacts from water")

    return _clamp(score), "; ".join(details) if details else "Preservation conditions analysed"


def _score_discovery_probability(known_score, terrain_score, geological_score,
                                 settlement_score, preservation_score):
    """Composite score estimating undiscovered site likelihood."""
    details = []

    # High known-site density suggests area is archaeologically rich
    # but might also mean it's been well-surveyed
    if known_score >= 70:
        site_factor = 0.7  # already well-explored
        details.append("Well-surveyed area -- many known sites")
    elif known_score >= 40:
        site_factor = 1.0  # moderate exploration
        details.append("Partially explored -- undiscovered sites likely")
    else:
        # Low known sites + good terrain = high discovery potential
        site_factor = 1.2
        details.append("Under-explored area -- high discovery potential")

    # Average of supporting factors
    support_avg = (terrain_score + geological_score + settlement_score + preservation_score) / 4.0

    # Good supporting conditions but few known sites = best discovery potential
    raw_score = support_avg * site_factor

    # Bonus for unexplored areas with good settlement patterns
    if known_score < 40 and settlement_score >= 50:
        raw_score += 10
        details.append("Good settlement conditions with few known sites")

    # Bonus for good preservation in under-surveyed areas
    if known_score < 50 and preservation_score >= 60:
        raw_score += 5
        details.append("Good preservation may hide undiscovered artefacts")

    score = _clamp(raw_score)
    return score, "; ".join(details) if details else "Discovery probability estimated"


# ==============================================================================
# MAIN ANALYSIS FUNCTION
# ==============================================================================

@st.cache_data(ttl=1800)
def compute_archaeological_potential(lat, lon):
    """
    Evaluate archaeological potential for the given location.

    Returns a dict with:
        overall            - weighted average score (0-100)
        classification     - High / Moderate / Low
        class_color        - hex colour for classification
        component_scores   - dict of 6 component scores (0-100)
        component_details  - dict of explanation per component
        sites              - list of nearby known sites
        site_types         - dict of site type counts
        key_findings       - list of finding strings
        geo_units          - list of geological unit info
    """
    # Fetch all data sources
    arch_data = fetch_archaeological_sites(lat, lon)
    elev_data = fetch_elevation_grid(lat, lon, radius_deg=0.05, grid_size=9)
    geo_data = fetch_macrostrat_geology(lat, lon)
    weather_data = fetch_weather_data(lat, lon)
    water_data = fetch_water_features(lat, lon)
    soil_data = fetch_soil_data(lat, lon)

    # Parse sites
    sites = _parse_site_list(arch_data, lat, lon)

    # Compute all 6 dimension scores
    known_score, known_detail = _score_known_sites(sites)
    terrain_score, terrain_detail = _score_terrain(elev_data)
    geological_score, geological_detail = _score_geological(geo_data)
    settlement_score, settlement_detail = _score_settlement_pattern(elev_data, water_data, sites)
    preservation_score, preservation_detail = _score_preservation(weather_data, soil_data)
    discovery_score, discovery_detail = _score_discovery_probability(
        known_score, terrain_score, geological_score, settlement_score, preservation_score
    )

    component_scores = {
        "known_sites": round(known_score, 1),
        "terrain": round(terrain_score, 1),
        "geological": round(geological_score, 1),
        "settlement": round(settlement_score, 1),
        "preservation": round(preservation_score, 1),
        "discovery": round(discovery_score, 1),
    }
    component_details = {
        "known_sites": known_detail,
        "terrain": terrain_detail,
        "geological": geological_detail,
        "settlement": settlement_detail,
        "preservation": preservation_detail,
        "discovery": discovery_detail,
    }

    # Weighted overall score
    overall = 0.0
    for key, meta in ARCH_COMPONENTS.items():
        overall += component_scores.get(key, 0) * meta["weight"]
    overall = round(_clamp(overall), 1)

    classification = _class_label(overall)
    class_color = _class_color(overall)

    # Site type breakdown
    site_types = {}
    for s in sites:
        t = s.get("type", "unknown")
        site_types[t] = site_types.get(t, 0) + 1

    # Key findings
    key_findings = []
    if known_score >= 60:
        key_findings.append(
            f"Rich archaeological landscape with {len(sites)} known historic features nearby."
        )
    elif known_score >= 30:
        key_findings.append(
            f"Moderate archaeological record with {len(sites)} known features."
        )
    else:
        key_findings.append("Limited known archaeological features in this area.")

    if terrain_score >= 60:
        key_findings.append(
            "Terrain is highly suitable for ancient settlement (elevation, slope, defensibility)."
        )
    if settlement_score >= 60:
        key_findings.append(
            "Strong settlement pattern indicators (water access, defensible position, clustering)."
        )
    if preservation_score >= 60:
        key_findings.append(
            "Environmental conditions favour artefact preservation (climate, soil pH)."
        )
    if discovery_score >= 60:
        key_findings.append(
            "High probability of undiscovered archaeological material in this area."
        )
    if geological_score >= 60:
        key_findings.append(
            "Geological context (sedimentary layers) supports preservation and excavation potential."
        )

    if not key_findings:
        key_findings.append("This location shows limited overall archaeological potential.")

    # Geological units for display
    geo_units = []
    geo_success = (geo_data if isinstance(geo_data, dict) else {}).get("success", {})
    if isinstance(geo_success, dict):
        geo_list = geo_success.get("data", [])
        if isinstance(geo_list, list):
            for item in geo_list[:5]:
                geo_units.append({
                    "name": item.get("strat_name_long") or item.get("strat_name") or item.get("name") or "Unknown",
                    "period": item.get("t_int_name", "Unknown") or "Unknown",
                    "age": item.get("t_age", "?"),
                    "lithology": item.get("lith", "Unknown") or "Unknown",
                    "color": item.get("color", "#8b97b0"),
                })

    return {
        "overall": overall,
        "classification": classification,
        "class_color": class_color,
        "component_scores": component_scores,
        "component_details": component_details,
        "sites": sites,
        "site_types": site_types,
        "key_findings": key_findings,
        "geo_units": geo_units,
    }


# ==============================================================================
# VISUALISATION HELPERS
# ==============================================================================

def _build_radar_chart(component_scores):
    """Build a Plotly radar chart of the 6 archaeological dimensions."""
    labels = [ARCH_COMPONENTS[k]["name"] for k in component_scores]
    values = list(component_scores.values())
    colors = [ARCH_COMPONENTS[k]["color"] for k in component_scores]

    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(245,158,11,0.15)",
        line={"color": "#f59e0b", "width": 2.5},
        marker={"size": 6, "color": "#f59e0b"},
        name="Archaeological Score",
        hovertemplate="%{theta}: %{r:.1f}/100<extra></extra>",
    ))
    fig.update_layout(
        polar={
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
            "bgcolor": CLR_BG,
        },
        title={
            "text": "Archaeological Potential Profile",
            "font": {"color": CLR_TEXT, "size": 16},
        },
        height=440,
        margin=dict(l=70, r=70, t=60, b=40),
        paper_bgcolor=CLR_BG,
        showlegend=False,
    )
    return fig


def _build_site_type_pie(site_types):
    """Build a Plotly pie chart of site type distribution."""
    if not site_types:
        return None

    labels = list(site_types.keys())
    values = list(site_types.values())

    type_colors = {
        "ruins": "#ef4444",
        "castle": "#8b5cf6",
        "monument": "#3b82f6",
        "memorial": "#06b6d4",
        "archaeological_site": "#f59e0b",
        "museum": "#ec4899",
        "tomb": "#a855f7",
        "church": "#14b8a6",
        "fort": "#f97316",
        "tower": "#64748b",
        "city_gate": "#84cc16",
        "battlefield": "#dc2626",
        "building": "#22c55e",
        "heritage": "#10b981",
    }
    colors = [type_colors.get(lbl, "#8b97b0") for lbl in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.45,
        marker={"colors": colors, "line": {"color": CLR_BG, "width": 2}},
        textfont={"color": CLR_TEXT, "size": 12},
        hovertemplate="%{label}: %{value} sites (%{percent})<extra></extra>",
    )])
    fig.update_layout(
        title={"text": "Site Type Distribution", "font": {"color": CLR_TEXT, "size": 16}},
        height=380,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor=CLR_BG,
        plot_bgcolor=CLR_BG,
        legend={"font": {"color": CLR_TEXT, "size": 11}},
        showlegend=True,
    )
    return fig


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render_archaeological_ai_tab():
    """Render the Archaeological Potential AI tab in the Streamlit UI."""

    # -- Header ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});
                    padding:24px 28px;border-radius:12px;
                    border:1px solid {CLR_BORDER};margin-bottom:20px;">
            <h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">
                Archaeological Potential AI
            </h2>
            <p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">
                Assess archaeological potential and historical significance combining
                known sites, terrain analysis, geological context, settlement patterns,
                and preservation conditions.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Location selector -----------------------------------------------------
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="archai_preset",
        )
    with c2:
        p = ANALYSIS_PRESETS.get(preset)
        default_lat = p.get("lat", 41.90) if p else 41.90
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="archai_lat",
        )
    with c3:
        default_lon = p.get("lon", 12.50) if p else 12.50
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="archai_lon",
        )

    run_btn = st.button(
        "Assess Archaeological Potential",
        type="primary",
        key="archai_run",
        use_container_width=True,
    )

    if not run_btn:
        st.info("Select a location and click **Assess Archaeological Potential** to begin.")
        return

    # -- Run analysis ----------------------------------------------------------
    with st.spinner("Fetching archaeological data and analysing potential..."):
        result = compute_archaeological_potential(lat, lon)

    overall = result["overall"]
    classification = result["classification"]
    class_color = result["class_color"]
    component_scores = result["component_scores"]
    component_details = result["component_details"]
    sites = result["sites"]
    site_types = result["site_types"]
    key_findings = result["key_findings"]
    geo_units = result["geo_units"]

    # -- Overall score header --------------------------------------------------
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
                        Archaeological Potential Index
                    </span>
                    <h1 style="margin:4px 0;color:{class_color};font-size:42px;">
                        {overall}/100
                    </h1>
                    <span style="font-size:18px;color:{class_color};font-weight:600;">
                        {escape(classification)} Potential
                    </span>
                </div>
                <div style="text-align:right;">
                    <span style="font-size:13px;color:{CLR_TEXT_SEC};">
                        Location: {lat:.4f}, {lon:.4f}
                    </span><br/>
                    <span style="font-size:12px;color:{CLR_TEXT_SEC};">
                        {len(sites)} known site(s) detected
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -- Radar chart -----------------------------------------------------------
    radar_fig = _build_radar_chart(component_scores)
    st.plotly_chart(radar_fig, use_container_width=True, key="archai_radar")

    # -- Component metric cards (3x2 grid) -------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:16px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Dimension Breakdown
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    comp_keys = list(component_scores.keys())
    row1_keys = comp_keys[:3]
    row2_keys = comp_keys[3:]

    for row_keys in [row1_keys, row2_keys]:
        cols = st.columns(len(row_keys))
        for col, key in zip(cols, row_keys):
            meta = ARCH_COMPONENTS.get(key, {})
            score_val = component_scores.get(key, 0)
            s_color = _class_color(score_val)
            s_label = _class_label(score_val)
            f_color = meta.get("color", "#f59e0b")
            f_name = meta.get("name", key)
            bar_width = max(5, score_val)
            detail_text = escape(component_details.get(key, ""))
            weight_pct = int(meta.get("weight", 0) * 100)

            with col:
                st.markdown(
                    f"""
                    <div style="background:{CLR_SURFACE};border:1px solid {f_color}44;
                                border-radius:10px;padding:16px;text-align:center;
                                min-height:210px;">
                        <div style="font-size:12px;color:{f_color};margin-bottom:4px;
                                    font-weight:600;">
                            {escape(f_name)}
                        </div>
                        <div style="font-size:10px;color:{CLR_TEXT_SEC};margin-bottom:6px;">
                            Weight: {weight_pct}%
                        </div>
                        <div style="font-size:32px;font-weight:700;color:{s_color};">
                            {score_val:.0f}
                        </div>
                        <div style="font-size:12px;color:{s_color};font-weight:600;
                                    margin-bottom:8px;">
                            {escape(s_label)}
                        </div>
                        <div style="background:{CLR_BG};border-radius:4px;height:6px;
                                    margin:8px 0;">
                            <div style="background:{s_color};width:{bar_width}%;
                                        height:6px;border-radius:4px;"></div>
                        </div>
                        <div style="font-size:10px;color:{CLR_TEXT_SEC};margin-top:6px;
                                    line-height:1.4;">
                            {detail_text}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- Known Sites Table -----------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Known Archaeological / Historic Sites
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if sites:
        # Build table rows
        table_rows = ""
        for idx, site in enumerate(sites[:30]):
            s_name = escape(str(site.get("name", "Unknown")))
            s_type = escape(str(site.get("type", "unknown")))
            s_dist = site.get("distance_km")
            dist_str = f"{s_dist:.2f} km" if s_dist is not None else "N/A"
            bg = CLR_BG if idx % 2 == 0 else CLR_SURFACE
            table_rows += (
                f'<tr style="background:{bg};">'
                f'<td style="padding:8px 12px;color:{CLR_TEXT};font-size:13px;">{s_name}</td>'
                f'<td style="padding:8px 12px;color:{CLR_TEXT_SEC};font-size:13px;">{s_type}</td>'
                f'<td style="padding:8px 12px;color:{CLR_TEXT_SEC};font-size:13px;">{dist_str}</td>'
                f'</tr>'
            )
        st.markdown(
            f"""
            <div style="overflow-x:auto;border-radius:8px;border:1px solid {CLR_BORDER};">
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="background:{CLR_CARD};">
                            <th style="padding:10px 12px;color:{CLR_TEXT};font-size:13px;
                                       text-align:left;font-weight:600;">Name</th>
                            <th style="padding:10px 12px;color:{CLR_TEXT};font-size:13px;
                                       text-align:left;font-weight:600;">Type</th>
                            <th style="padding:10px 12px;color:{CLR_TEXT};font-size:13px;
                                       text-align:left;font-weight:600;">Distance</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if len(sites) > 30:
            st.caption(f"Showing 30 of {len(sites)} sites.")
    else:
        st.info("No known archaeological or historic sites found within the search radius.")

    # -- Site Type Pie Chart ---------------------------------------------------
    if site_types:
        pie_col, info_col = st.columns([1.2, 1])
        with pie_col:
            pie_fig = _build_site_type_pie(site_types)
            if pie_fig is not None:
                st.plotly_chart(pie_fig, use_container_width=True, key="archai_pie")
        with info_col:
            st.markdown(
                f"""
                <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                            border:1px solid {CLR_BORDER};margin-top:10px;">
                    <h4 style="margin:0 0 10px;color:{CLR_TEXT};font-size:15px;">
                        Site Type Summary
                    </h4>
                </div>
                """,
                unsafe_allow_html=True,
            )
            for stype, scount in sorted(site_types.items(), key=lambda x: -x[1]):
                st.markdown(
                    f"""
                    <div style="display:flex;justify-content:space-between;
                                padding:6px 12px;margin:2px 0;
                                background:{CLR_BG};border-radius:6px;">
                        <span style="color:{CLR_TEXT};font-size:13px;">
                            {escape(str(stype))}
                        </span>
                        <span style="color:#f59e0b;font-weight:600;font-size:13px;">
                            {scount}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # -- Key Findings Summary --------------------------------------------------
    st.markdown(
        f"""
        <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                    border:1px solid {CLR_BORDER};margin:20px 0 8px;">
            <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                Key Findings
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    for finding in key_findings:
        st.markdown(
            f"""
            <div style="background:{CLR_BG};border:1px solid {class_color}44;
                        border-left:4px solid {class_color};
                        border-radius:8px;padding:12px 16px;margin:6px 0;">
                <span style="color:{CLR_TEXT};font-size:13px;line-height:1.5;">
                    {escape(finding)}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -- Geological Context (if available) -------------------------------------
    if geo_units:
        st.markdown(
            f"""
            <div style="background:{CLR_SURFACE};padding:16px 20px;border-radius:10px;
                        border:1px solid {CLR_BORDER};margin:20px 0 8px;">
                <h3 style="margin:0;color:{CLR_TEXT};font-size:18px;">
                    Geological Context (Macrostrat)
                </h3>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for unit in geo_units:
            u_color = unit.get("color", "#2a3550")
            u_name = escape(str(unit.get("name", "Unknown")))
            u_period = escape(str(unit.get("period", "Unknown")))
            u_age = escape(str(unit.get("age", "?")))
            u_lith = escape(str(unit.get("lithology", "Unknown")))
            st.markdown(
                f"""
                <div style="background:rgba(15,23,42,0.65);border-left:4px solid {u_color};
                            padding:10px 14px;margin:6px 0;border-radius:0 8px 8px 0;
                            backdrop-filter:blur(16px);">
                    <span style="color:{CLR_TEXT};font-weight:bold;font-size:14px;">
                        {u_name}
                    </span><br/>
                    <span style="color:{CLR_TEXT_SEC};font-size:12px;">
                        Period: {u_period} | Age: {u_age} Ma
                    </span><br/>
                    <span style="color:#06b6d4;font-size:12px;">
                        Lithology: {u_lith}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # -- Footer ----------------------------------------------------------------
    st.markdown(
        f"""
        <div style="text-align:center;padding:16px;margin-top:20px;
                    color:{CLR_TEXT_SEC};font-size:12px;">
            Archaeological Potential AI powered by OpenStreetMap Overpass,
            Macrostrat, Open Topo Data, Open-Meteo, and ISRIC SoilGrids.
            Scores are indicative and should complement professional archaeological surveys.
        </div>
        """,
        unsafe_allow_html=True,
    )
