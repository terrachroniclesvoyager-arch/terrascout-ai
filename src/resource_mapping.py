"""
Natural Resource Mapping for TerraScout AI.
Comprehensive survey of all available natural resources near a point.
Covers 8 categories: Water, Timber, Agriculture, Minerals, Solar, Wind,
Building Materials, and Fisheries.
Uses: Overpass API, SoilGrids v2.0, Macrostrat, Open-Meteo.
All APIs are free and require no API keys.
"""

import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import requests
import streamlit as st
from streamlit.components.v1 import html as st_html

logger = logging.getLogger(__name__)

# ── Constants & Category Metadata ──────────────────────────────────────────

RESOURCE_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "Water Resources":   {"icon": "💧", "color": "#3b82f6", "desc": "Rivers, lakes, springs, wells, reservoirs"},
    "Timber & Forest":   {"icon": "🌲", "color": "#16a34a", "desc": "Forests, woodlands, tree cover area"},
    "Agricultural Land": {"icon": "🌾", "color": "#84cc16", "desc": "Farmland, orchards, vineyards + soil fertility"},
    "Mineral Potential":  {"icon": "⛏️", "color": "#a855f7", "desc": "Rock types, lithology, soil mineral content"},
    "Solar Energy":      {"icon": "☀️", "color": "#f59e0b", "desc": "Sunshine duration, latitude-based potential"},
    "Wind Energy":       {"icon": "💨", "color": "#06b6d4", "desc": "Wind speed patterns & consistency"},
    "Building Materials": {"icon": "🧱", "color": "#d97706", "desc": "Quarries, sand pits, gravel, stone deposits"},
    "Fisheries":         {"icon": "🐟", "color": "#0ea5e9", "desc": "Fish farms, fishing spots, aquaculture"},
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
MACROSTRAT_URL = "https://macrostrat.org/api/geologic_units/map"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

MINERAL_FAVORABLE = {
    "granite": 7.5, "basalt": 6.5, "gneiss": 7.0, "schist": 6.5,
    "quartzite": 6.0, "limestone": 5.5, "sandstone": 5.0,
    "serpentinite": 8.0, "pegmatite": 9.0, "kimberlite": 9.5,
    "dolomite": 5.5, "volcanic": 7.0, "metamorphic": 6.5,
    "igneous": 7.0, "sedimentary": 4.5, "marble": 5.0, "slate": 5.0,
    "shale": 4.0, "conglomerate": 4.0, "rhyolite": 6.0, "diorite": 6.5,
}

_FOLIUM_COLORS = {
    "Water Resources": "blue", "Timber & Forest": "green",
    "Agricultural Land": "lightgreen", "Mineral Potential": "purple",
    "Solar Energy": "orange", "Wind Energy": "lightblue",
    "Building Materials": "beige", "Fisheries": "cadetblue",
}

# ── Utility Helpers ────────────────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return distance in metres between two points."""
    R = 6_371_000
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _nearest_distance(lat: float, lon: float, elements: list) -> Optional[float]:
    """Find the nearest distance (m) from lat/lon to any element."""
    best = None
    for el in elements:
        elat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        elon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if elat is not None and elon is not None:
            d = _haversine(lat, lon, float(elat), float(elon))
            if best is None or d < best:
                best = d
    return best


def _fmt_dist(m: Optional[float]) -> str:
    if m is None:
        return "N/A"
    return f"{m:.0f} m" if m < 1000 else f"{m / 1000:.1f} km"


def _score_clamp(val: float) -> float:
    return max(0.0, min(10.0, val))


# ── Overpass Query Helper (cached) ─────────────────────────────────────────

@st.cache_data(ttl=900)
def _overpass_query(query_body: str) -> list:
    """Run an Overpass QL query and return elements list."""
    full_query = f"[out:json][timeout:10];({query_body});out center;"
    try:
        resp = requests.post(OVERPASS_URL, data={"data": full_query}, timeout=10)
        resp.raise_for_status()
        return resp.json().get("elements", [])
    except Exception as exc:
        logger.warning("Overpass query failed: %s", exc)
        return []


# ── Data-Fetching Functions (all cached with ttl=900) ──────────────────────

@st.cache_data(ttl=900)
def _fetch_water_resources(lat: float, lon: float, radius: int = 10000) -> Dict:
    """Fetch water features from Overpass API."""
    query = (
        f'node["natural"="water"](around:{radius},{lat},{lon});'
        f'way["natural"="water"](around:{radius},{lat},{lon});'
        f'node["natural"="spring"](around:{radius},{lat},{lon});'
        f'node["man_made"="water_well"](around:{radius},{lat},{lon});'
        f'node["man_made"="water_tower"](around:{radius},{lat},{lon});'
        f'way["water"~"river|lake|reservoir"](around:{radius},{lat},{lon});'
        f'way["waterway"~"river|stream|canal"](around:{radius},{lat},{lon});'
    )
    elements = _overpass_query(query)
    dist = _nearest_distance(lat, lon, elements)
    count = len(elements)
    score = min(count * 0.8, 7.0)
    if dist is not None and dist < 1000:
        score += 3.0
    elif dist is not None and dist < 5000:
        score += 1.5
    return {"elements": elements, "count": count, "nearest_m": dist, "score": _score_clamp(score)}


@st.cache_data(ttl=900)
def _fetch_timber_forest(lat: float, lon: float, radius: int = 10000) -> Dict:
    """Fetch forest and woodland features."""
    query = (
        f'way["natural"="wood"](around:{radius},{lat},{lon});'
        f'way["landuse"="forest"](around:{radius},{lat},{lon});'
        f'relation["landuse"="forest"](around:{radius},{lat},{lon});'
        f'relation["natural"="wood"](around:{radius},{lat},{lon});'
        f'node["natural"="tree"](around:{radius},{lat},{lon});'
    )
    elements = _overpass_query(query)
    dist = _nearest_distance(lat, lon, elements)
    count = len(elements)
    forest_ways = [e for e in elements if e.get("type") in ("way", "relation")]
    area_est_ha = len(forest_ways) * 5.0
    score = min(len(forest_ways) * 1.2 + count * 0.1, 8.0)
    if dist is not None and dist < 2000:
        score += 2.0
    return {
        "elements": elements, "count": count, "nearest_m": dist,
        "score": _score_clamp(score), "forest_ways": len(forest_ways),
        "area_est_ha": area_est_ha,
    }


@st.cache_data(ttl=900)
def _fetch_soilgrids(lat: float, lon: float) -> Dict:
    """Fetch soil properties from SoilGrids v2.0."""
    params = {
        "lat": lat, "lon": lon,
        "property": ["soc", "nitrogen", "phh2o", "clay", "sand", "silt", "cec", "ocd"],
        "depth": "0-5cm", "value": "mean",
    }
    try:
        resp = requests.get(SOILGRIDS_URL, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("SoilGrids request failed: %s", exc)
        return {}


def _parse_soilgrids(soil: dict) -> Dict[str, Optional[float]]:
    """Parse SoilGrids v2.0 response using correct layer structure."""
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {}
    for _l in (_layers if isinstance(_layers, list) else []):
        _ln = _l.get("name", "") if isinstance(_l, dict) else ""
        if _ln:
            _layer_map[_ln] = _l

    def _sv(name: str, div: float = 10) -> Optional[float]:
        p = _layer_map.get(name, {})
        if isinstance(p, dict):
            depths = p.get("depths", [])
            if depths:
                return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    return {
        "soc": _sv("soc", 10), "nitrogen": _sv("nitrogen", 100),
        "ph": _sv("phh2o", 10), "clay": _sv("clay", 10),
        "sand": _sv("sand", 10), "silt": _sv("silt", 10),
        "cec": _sv("cec", 10), "ocd": _sv("ocd", 10),
    }


@st.cache_data(ttl=900)
def _fetch_agricultural(lat: float, lon: float, radius: int = 10000) -> Dict:
    """Fetch agricultural land from Overpass + soil fertility from SoilGrids."""
    query = (
        f'way["landuse"="farmland"](around:{radius},{lat},{lon});'
        f'way["landuse"="orchard"](around:{radius},{lat},{lon});'
        f'way["landuse"="vineyard"](around:{radius},{lat},{lon});'
        f'way["landuse"="meadow"](around:{radius},{lat},{lon});'
        f'node["landuse"="allotments"](around:{radius},{lat},{lon});'
        f'way["landuse"="allotments"](around:{radius},{lat},{lon});'
    )
    elements = _overpass_query(query)
    soil_raw = _fetch_soilgrids(lat, lon)
    soil = _parse_soilgrids(soil_raw)
    dist = _nearest_distance(lat, lon, elements)
    count = len(elements)
    # Fertility sub-score from soil (0-5)
    fertility = 0.0
    soc, ph, n, cec_val = soil.get("soc"), soil.get("ph"), soil.get("nitrogen"), soil.get("cec")
    if soc is not None and soc > 10:
        fertility += 1.5
    elif soc is not None and soc > 5:
        fertility += 0.8
    if ph is not None and 5.5 <= ph <= 7.5:
        fertility += 1.2
    if n is not None and n > 0.5:
        fertility += 1.0
    if cec_val is not None and cec_val > 10:
        fertility += 1.3
    score = min(count * 0.6, 5.0) + fertility
    if dist is not None and dist < 2000:
        score += 1.0
    return {
        "elements": elements, "count": count, "nearest_m": dist,
        "score": _score_clamp(score), "soil": soil, "fertility": round(fertility, 1),
    }


@st.cache_data(ttl=900)
def _fetch_macrostrat(lat: float, lon: float) -> Dict:
    """Fetch geologic units from Macrostrat."""
    url = f"{MACROSTRAT_URL}?lat={lat}&lng={lon}&format=geojson"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Macrostrat request failed: %s", exc)
        return {}


@st.cache_data(ttl=900)
def _fetch_mineral_potential(lat: float, lon: float) -> Dict:
    """Evaluate mineral potential via Macrostrat + SoilGrids."""
    macro = _fetch_macrostrat(lat, lon)
    soil_raw = _fetch_soilgrids(lat, lon)
    soil = _parse_soilgrids(soil_raw)
    features, rock_types = [], []
    if isinstance(macro, dict):
        feats = macro.get("features", [])
        if isinstance(feats, list):
            features = feats
            for f in feats:
                props = f.get("properties", {}) if isinstance(f, dict) else {}
                rock_types.append(str(props.get("lith", "")).lower())
    geo_score, matched_rocks = 0.0, []
    for rt in rock_types:
        for key, val in MINERAL_FAVORABLE.items():
            if key in rt:
                geo_score = max(geo_score, val)
                matched_rocks.append(key)
    soil_mineral_bonus = 0.0
    if (soil.get("cec") or 0) > 15:
        soil_mineral_bonus += 1.0
    if (soil.get("clay") or 0) > 30:
        soil_mineral_bonus += 0.5
    score = _score_clamp(geo_score * 0.8 + soil_mineral_bonus + len(features) * 0.3)
    return {
        "features": features, "rock_types": rock_types,
        "matched_rocks": list(set(matched_rocks)), "score": score,
        "soil": soil, "geo_units": len(features),
    }


@st.cache_data(ttl=900)
def _fetch_solar_energy(lat: float, lon: float) -> Dict:
    """Evaluate solar energy potential using Open-Meteo sunshine data."""
    url = (f"{OPEN_METEO_URL}?latitude={lat}&longitude={lon}"
           f"&daily=sunshine_duration&past_days=30&timezone=auto")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Open-Meteo solar request failed: %s", exc)
        data = {}
    daily = data.get("daily", {})
    sunshine_secs = daily.get("sunshine_duration", [])
    sunshine_hrs = [s / 3600.0 for s in sunshine_secs if s is not None] if sunshine_secs else []
    avg_sun = sum(sunshine_hrs) / len(sunshine_hrs) if sunshine_hrs else 0
    lat_factor = max(0, 1.0 - abs(lat) / 90.0) * 3.0
    clear_days = sum(1 for h in sunshine_hrs if h > 8) if sunshine_hrs else 0
    clear_pct = (clear_days / len(sunshine_hrs) * 100) if sunshine_hrs else 0
    score = _score_clamp(avg_sun * 0.6 + lat_factor + clear_pct * 0.02)
    return {
        "avg_sunshine_hrs": round(avg_sun, 1), "clear_sky_days_30d": clear_days,
        "clear_pct": round(clear_pct, 1), "lat_factor": round(lat_factor, 2),
        "score": score, "daily_sunshine_hrs": [round(h, 1) for h in sunshine_hrs],
    }


@st.cache_data(ttl=900)
def _fetch_wind_energy(lat: float, lon: float) -> Dict:
    """Evaluate wind energy potential using Open-Meteo wind data."""
    url = (f"{OPEN_METEO_URL}?latitude={lat}&longitude={lon}"
           f"&daily=wind_speed_10m_max&past_days=30&timezone=auto")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Open-Meteo wind request failed: %s", exc)
        data = {}
    daily = data.get("daily", {})
    winds = daily.get("wind_speed_10m_max", [])
    wind_vals = [w for w in (winds or []) if w is not None]
    avg_wind = sum(wind_vals) / len(wind_vals) if wind_vals else 0
    max_wind = max(wind_vals) if wind_vals else 0
    if len(wind_vals) > 1 and avg_wind > 0:
        variance = sum((w - avg_wind) ** 2 for w in wind_vals) / len(wind_vals)
        consistency = max(0, 1.0 - math.sqrt(variance) / avg_wind) * 2.0
    else:
        consistency = 0.0
    if avg_wind >= 25:     power_class = 7
    elif avg_wind >= 20:   power_class = 6
    elif avg_wind >= 15:   power_class = 5
    elif avg_wind >= 12:   power_class = 4
    elif avg_wind >= 9:    power_class = 3
    elif avg_wind >= 6:    power_class = 2
    else:                  power_class = 1
    score = _score_clamp(avg_wind * 0.35 + consistency + power_class * 0.3)
    return {
        "avg_wind_kmh": round(avg_wind, 1), "max_wind_kmh": round(max_wind, 1),
        "power_class": power_class, "consistency": round(consistency, 2),
        "score": score, "daily_winds": [round(w, 1) for w in wind_vals],
    }


@st.cache_data(ttl=900)
def _fetch_building_materials(lat: float, lon: float, radius: int = 10000) -> Dict:
    """Find quarries, sand pits, and gravel deposits."""
    query = (
        f'node["man_made"~"quarry|mineshaft"](around:{radius},{lat},{lon});'
        f'way["landuse"="quarry"](around:{radius},{lat},{lon});'
        f'node["natural"~"sand|shingle"](around:{radius},{lat},{lon});'
        f'way["natural"~"sand|shingle"](around:{radius},{lat},{lon});'
        f'node["resource"="gravel"](around:{radius},{lat},{lon});'
        f'way["resource"="gravel"](around:{radius},{lat},{lon});'
    )
    elements = _overpass_query(query)
    macro = _fetch_macrostrat(lat, lon)
    stone_types = []
    if isinstance(macro, dict):
        for f in macro.get("features", []):
            if isinstance(f, dict):
                lith = str((f.get("properties", {}) or {}).get("lith", "")).lower()
                if any(k in lith for k in ("limestone", "granite", "marble",
                                           "sandstone", "basalt", "slate")):
                    stone_types.append(lith)
    dist = _nearest_distance(lat, lon, elements)
    count = len(elements)
    score = min(count * 1.5, 6.0) + len(stone_types) * 1.0
    if dist is not None and dist < 3000:
        score += 2.0
    return {
        "elements": elements, "count": count, "nearest_m": dist,
        "score": _score_clamp(score), "stone_types": list(set(stone_types)),
    }


@st.cache_data(ttl=900)
def _fetch_fisheries(lat: float, lon: float, radius: int = 10000) -> Dict:
    """Find fishing and aquaculture features."""
    query = (
        f'node["leisure"="fishing"](around:{radius},{lat},{lon});'
        f'way["leisure"="fishing"](around:{radius},{lat},{lon});'
        f'node["landuse"="aquaculture"](around:{radius},{lat},{lon});'
        f'way["landuse"="aquaculture"](around:{radius},{lat},{lon});'
        f'node["man_made"="fish_pass"](around:{radius},{lat},{lon});'
        f'way["man_made"="fish_pass"](around:{radius},{lat},{lon});'
        f'node["shop"="seafood"](around:{radius},{lat},{lon});'
        f'way["industrial"="fish_farm"](around:{radius},{lat},{lon});'
    )
    elements = _overpass_query(query)
    dist = _nearest_distance(lat, lon, elements)
    count = len(elements)
    water_q = (
        f'way["natural"="water"](around:{radius},{lat},{lon});'
        f'way["waterway"~"river|stream"](around:{radius},{lat},{lon});'
    )
    water_els = _overpass_query(water_q)
    water_bonus = min(len(water_els) * 0.5, 3.0)
    score = min(count * 2.0, 5.0) + water_bonus
    if dist is not None and dist < 2000:
        score += 2.0
    return {
        "elements": elements, "count": count, "nearest_m": dist,
        "score": _score_clamp(score), "water_bodies_nearby": len(water_els),
    }


# ── Aggregate Survey ──────────────────────────────────────────────────────

@st.cache_data(ttl=900)
def survey_all_resources(lat: float, lon: float) -> Dict[str, Dict]:
    """Run all 8 resource surveys and return combined results."""
    return {
        "Water Resources":   _fetch_water_resources(lat, lon),
        "Timber & Forest":   _fetch_timber_forest(lat, lon),
        "Agricultural Land": _fetch_agricultural(lat, lon),
        "Mineral Potential":  _fetch_mineral_potential(lat, lon),
        "Solar Energy":      _fetch_solar_energy(lat, lon),
        "Wind Energy":       _fetch_wind_energy(lat, lon),
        "Building Materials": _fetch_building_materials(lat, lon),
        "Fisheries":         _fetch_fisheries(lat, lon),
    }


def _compute_richness_index(results: Dict[str, Dict]) -> float:
    """Compute overall Resource Richness Index (0-100)."""
    scores = [r.get("score", 0) for r in results.values()]
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    diversity = sum(1 for s in scores if s >= 3.0) / len(scores)
    return round(avg * 8.0 + diversity * 20.0, 1)


# ── UI: Resource Cards ────────────────────────────────────────────────────

def _render_resource_card(name: str, meta: Dict, data: Dict):
    """Render a single resource card with icon, score bar, and stats."""
    icon, color = meta.get("icon", "📦"), meta.get("color", "#6b7280")
    score = data.get("score", 0)
    pct = score / 10.0 * 100
    st.markdown(
        f"""<div style="border:1px solid {color}33; border-radius:10px; padding:14px;
                    background:linear-gradient(135deg, {color}08, {color}15);
                    margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.15em; font-weight:600;">{icon} {name}</span>
                <span style="font-size:1.3em; font-weight:700; color:{color};">{score:.1f}/10</span>
            </div>
            <div style="background:#e5e7eb; border-radius:6px; height:10px; margin:8px 0;">
                <div style="background:{color}; width:{pct:.0f}%; height:10px;
                            border-radius:6px;"></div>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:0.82em;
                        color:#6b7280;">
                <span>Features: {data.get('count', 0)}</span>
                <span>Nearest: {_fmt_dist(data.get('nearest_m'))}</span>
            </div>
        </div>""", unsafe_allow_html=True,
    )


def _render_all_cards(results: Dict[str, Dict]):
    """Render 8 resource cards in a 2-column grid."""
    names = list(results.keys())
    for i in range(0, len(names), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(names):
                name = names[idx]
                meta = RESOURCE_CATEGORIES.get(name, {"icon": "📦", "color": "#6b7280"})
                with col:
                    _render_resource_card(name, meta, results[name])


# ── UI: Charts ─────────────────────────────────────────────────────────────

def _render_bar_chart(results: Dict[str, Dict]):
    """Horizontal bar chart ranking resources by availability score."""
    sorted_items = sorted(results.items(), key=lambda x: x[1].get("score", 0))
    names = [k for k, _ in sorted_items]
    scores = [v.get("score", 0) for _, v in sorted_items]
    colors = [RESOURCE_CATEGORIES.get(n, {}).get("color", "#6b7280") for n in names]
    labels = [f"{RESOURCE_CATEGORIES.get(n, {}).get('icon', '')} {n}" for n in names]
    fig = go.Figure(go.Bar(
        x=scores, y=labels, orientation="h", marker_color=colors,
        text=[f"{s:.1f}" for s in scores], textposition="outside",
    ))
    fig.update_layout(
        title="Resource Availability Ranking",
        xaxis_title="Score (0-10)", yaxis_title="",
        height=380, margin=dict(l=10, r=30, t=40, b=30),
        xaxis=dict(range=[0, 11]),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, key="resmap_bar_chart")


def _render_pie_chart(results: Dict[str, Dict]):
    """Pie chart showing resource mix proportions."""
    names = list(results.keys())
    scores = [results[n].get("score", 0) for n in names]
    colors = [RESOURCE_CATEGORIES.get(n, {}).get("color", "#6b7280") for n in names]
    labels = [f"{RESOURCE_CATEGORIES.get(n, {}).get('icon', '')} {n}" for n in names]
    fig = go.Figure(go.Pie(
        labels=labels, values=scores, marker_colors=colors,
        textinfo="label+percent", textposition="outside", hole=0.35,
        hovertemplate="%{label}: %{value:.1f}/10<extra></extra>",
    ))
    fig.update_layout(
        title="Resource Mix", height=400, margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True, key="resmap_pie_chart")


# ── UI: Detail Expanders ──────────────────────────────────────────────────

def _render_detail_expanders(results: Dict[str, Dict]):
    """Render per-category detail expanders with extra info."""
    for name, data in results.items():
        meta = RESOURCE_CATEGORIES.get(name, {})
        icon, score = meta.get("icon", "📦"), data.get("score", 0)
        with st.expander(f"{icon} {name} — Score: {score:.1f}/10"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Score", f"{score:.1f}/10")
            c2.metric("Features Found", data.get("count", "N/A"))
            c3.metric("Nearest", _fmt_dist(data.get("nearest_m")))
            if name == "Water Resources":
                st.info("Water features scanned: rivers, lakes, springs, wells, "
                        "reservoirs, water towers within 10 km.")
            elif name == "Timber & Forest":
                st.info(f"Forest polygons: {data.get('forest_ways', 0)} | "
                        f"Estimated area: ~{data.get('area_est_ha', 0):.0f} ha")
            elif name == "Agricultural Land":
                soil = data.get("soil", {})
                st.info(f"Fertility sub-score: {data.get('fertility', 0)}/5")
                if soil:
                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.metric("SOC (g/kg)", f"{soil.get('soc') or 'N/A'}")
                    sc2.metric("pH", f"{soil.get('ph') or 'N/A'}")
                    sc3.metric("Nitrogen (g/kg)", f"{soil.get('nitrogen') or 'N/A'}")
                    sc4.metric("CEC (cmol/kg)", f"{soil.get('cec') or 'N/A'}")
            elif name == "Mineral Potential":
                matched = data.get("matched_rocks", [])
                if matched:
                    st.success(f"Favorable rock types: {', '.join(matched)}")
                else:
                    st.warning("No notably favorable rock types detected.")
                st.info(f"Geological units found: {data.get('geo_units', 0)}")
                soil = data.get("soil", {})
                if soil:
                    sc1, sc2 = st.columns(2)
                    sc1.metric("Clay %", f"{soil.get('clay') or 'N/A'}")
                    sc2.metric("CEC", f"{soil.get('cec') or 'N/A'}")
            elif name == "Solar Energy":
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Avg Sunshine", f"{data.get('avg_sunshine_hrs', 0)} h/day")
                sc2.metric("Clear Days (30d)", data.get("clear_sky_days_30d", 0))
                sc3.metric("Clear %", f"{data.get('clear_pct', 0)}%")
                daily = data.get("daily_sunshine_hrs", [])
                if daily:
                    fig = go.Figure(go.Scatter(
                        y=daily, mode="lines+markers",
                        line=dict(color="#f59e0b", width=2), marker=dict(size=4),
                    ))
                    fig.update_layout(
                        height=180, margin=dict(l=10, r=10, t=10, b=10),
                        xaxis_title="Day", yaxis_title="Sunshine (h)",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True, key="resmap_solar_spark")
            elif name == "Wind Energy":
                sc1, sc2, sc3 = st.columns(3)
                sc1.metric("Avg Wind", f"{data.get('avg_wind_kmh', 0)} km/h")
                sc2.metric("Max Wind", f"{data.get('max_wind_kmh', 0)} km/h")
                sc3.metric("Power Class", data.get("power_class", 1))
                daily = data.get("daily_winds", [])
                if daily:
                    fig = go.Figure(go.Bar(y=daily, marker_color="#06b6d4"))
                    fig.update_layout(
                        height=180, margin=dict(l=10, r=10, t=10, b=10),
                        xaxis_title="Day", yaxis_title="Max Wind (km/h)",
                        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig, use_container_width=True, key="resmap_wind_spark")
            elif name == "Building Materials":
                stone = data.get("stone_types", [])
                if stone:
                    st.success(f"Available stone types: {', '.join(stone)}")
                else:
                    st.info("No specific stone types identified in geology.")
            elif name == "Fisheries":
                st.info(f"Water bodies nearby: {data.get('water_bodies_nearby', 0)} | "
                        f"Fishing/aquaculture features: {data.get('count', 0)}")


# ── UI: Folium Map ─────────────────────────────────────────────────────────

def _render_resource_map(lat: float, lon: float, results: Dict[str, Dict]):
    """Render folium map with color-coded markers for each resource type."""
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB positron")
    folium.Marker(
        [lat, lon], popup="Survey Center",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(m)
    MAX_MARKERS = 25
    for cat_name, data in results.items():
        elements = data.get("elements", [])
        if not elements:
            continue
        fc = _FOLIUM_COLORS.get(cat_name, "gray")
        fg = folium.FeatureGroup(name=cat_name)
        count = 0
        for el in elements:
            elat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
            elon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
            if elat is None or elon is None:
                continue
            label = (el.get("tags", {}) or {}).get("name", cat_name)
            folium.CircleMarker(
                [float(elat), float(elon)], radius=5, color=fc,
                fill=True, fill_opacity=0.6,
                popup=f"<b>{cat_name}</b><br>{label}",
            ).add_to(fg)
            count += 1
            if count >= MAX_MARKERS:
                break
        fg.add_to(m)
    folium.Circle(
        [lat, lon], radius=10000, color="#ef4444",
        fill=False, weight=1, dash_array="5", popup="10 km survey radius",
    ).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    st_html(m._repr_html_(), height=520)


# ── UI: Richness Index Header ─────────────────────────────────────────────

def _render_richness_header(richness: float, results: Dict[str, Dict]):
    """Display overall Resource Richness Index as a prominent gauge."""
    if richness >= 70:     grade, grade_col = "Excellent", "#16a34a"
    elif richness >= 50:   grade, grade_col = "Good", "#84cc16"
    elif richness >= 30:   grade, grade_col = "Moderate", "#f59e0b"
    else:                  grade, grade_col = "Low", "#ef4444"
    top = max(results.items(), key=lambda x: x[1].get("score", 0))
    top_name, top_icon = top[0], RESOURCE_CATEGORIES.get(top[0], {}).get("icon", "")
    top_score = top[1].get("score", 0)
    st.markdown(
        f"""<div style="background:linear-gradient(135deg,#1e293b,#334155);
                    border-radius:14px; padding:22px; margin-bottom:18px;
                    color:#f1f5f9; text-align:center;">
            <div style="font-size:0.9em; opacity:0.8; margin-bottom:4px;">
                RESOURCE RICHNESS INDEX</div>
            <div style="font-size:3em; font-weight:800; color:{grade_col};">
                {richness:.0f}<span style="font-size:0.4em">/100</span></div>
            <div style="font-size:1.1em; font-weight:600; color:{grade_col};">{grade}</div>
            <div style="font-size:0.85em; opacity:0.7; margin-top:8px;">
                Top resource: {top_icon} {top_name} ({top_score:.1f}/10)</div>
        </div>""", unsafe_allow_html=True,
    )


# ── UI: Summary Table ─────────────────────────────────────────────────────

def _render_summary_table(results: Dict[str, Dict]):
    """Compact summary table of all resource categories."""
    rows = []
    for name, data in results.items():
        icon = RESOURCE_CATEGORIES.get(name, {}).get("icon", "")
        rows.append({
            "Resource": f"{icon} {name}", "Score": f"{data.get('score', 0):.1f}",
            "Features": data.get("count", "—"), "Nearest": _fmt_dist(data.get("nearest_m")),
        })
    header = "| Resource | Score | Features | Nearest |\n|---|---|---|---|\n"
    body = "\n".join(
        f"| {r['Resource']} | {r['Score']} | {r['Features']} | {r['Nearest']} |"
        for r in rows
    )
    st.markdown(header + body)


# ── UI: Recommendations ───────────────────────────────────────────────────

def _render_recommendations(results: Dict[str, Dict]):
    """Generate actionable recommendations based on resource survey."""
    recs = []
    sorted_res = sorted(results.items(), key=lambda x: x[1].get("score", 0), reverse=True)
    for name, data in sorted_res[:3]:
        score = data.get("score", 0)
        icon = RESOURCE_CATEGORIES.get(name, {}).get("icon", "")
        if score >= 7:
            recs.append(f"**{icon} {name}** — Highly abundant ({score:.1f}/10). "
                        f"Strong potential for commercial exploitation.")
        elif score >= 4:
            recs.append(f"**{icon} {name}** — Moderately available ({score:.1f}/10). "
                        f"Worth investigating for sustainable use.")
    weak = [n for n, d in sorted_res if d.get("score", 0) < 2.0]
    if weak:
        recs.append(f"**Limited resources:** {', '.join(weak)} — scored below 2.0. "
                    f"These are scarce in this area.")
    water_s = results.get("Water Resources", {}).get("score", 0)
    agri_s = results.get("Agricultural Land", {}).get("score", 0)
    if water_s >= 5 and agri_s >= 5:
        recs.append("**Synergy:** Strong water + agriculture scores suggest "
                    "excellent irrigated farming potential.")
    solar_s = results.get("Solar Energy", {}).get("score", 0)
    wind_s = results.get("Wind Energy", {}).get("score", 0)
    if solar_s >= 5 and wind_s >= 5:
        recs.append("**Energy hub:** Both solar and wind show good potential — "
                    "ideal for hybrid renewable energy installations.")
    if recs:
        st.markdown("### Recommendations")
        for r in recs:
            st.markdown(f"- {r}")


# ── Main Entry Point ──────────────────────────────────────────────────────

def render_resource_mapping_tab():
    """Single entry point for the Natural Resource Mapping module."""
    st.markdown("## 💎 Natural Resource Mapping")
    st.caption("Comprehensive survey of water, timber, minerals, energy & materials")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f", key="resmap_lat")
    lon = c2.number_input("Longitude", value=12.5, format="%.4f", key="resmap_lon")
    radius_opt = st.selectbox(
        "Survey radius", options=["5 km", "10 km", "15 km", "20 km"],
        index=1, key="resmap_radius",
    )

    if st.button("💎 Survey Resources", key="resmap_btn", type="primary"):
        with st.spinner("Surveying 8 resource categories..."):
            results = survey_all_resources(lat, lon)
        if not results:
            st.error("No resource data could be retrieved. Please try again.")
            return

        # Richness Index
        richness = _compute_richness_index(results)
        _render_richness_header(richness, results)

        # Quick metrics row
        m_cols = st.columns(4)
        scores = sorted(results.items(), key=lambda x: x[1].get("score", 0), reverse=True)
        total_features = sum(d.get("count", 0) for d in results.values())
        above_5 = sum(1 for d in results.values() if d.get("score", 0) >= 5)
        m_cols[0].metric("Categories Surveyed", len(results))
        m_cols[1].metric("Total Features", total_features)
        m_cols[2].metric("Scores >= 5", f"{above_5}/8")
        m_cols[3].metric("Top Score", f"{scores[0][1].get('score', 0):.1f}/10")
        st.markdown("---")

        # Resource Cards
        st.markdown("### Resource Availability")
        _render_all_cards(results)
        st.markdown("---")

        # Charts side by side
        st.markdown("### Resource Analysis")
        chart_c1, chart_c2 = st.columns(2)
        with chart_c1:
            _render_bar_chart(results)
        with chart_c2:
            _render_pie_chart(results)
        st.markdown("---")

        # Map
        st.markdown("### Resource Map")
        st.caption("Color-coded markers for each resource type within survey radius")
        _render_resource_map(lat, lon, results)
        st.markdown("---")

        # Summary Table
        st.markdown("### Summary")
        _render_summary_table(results)
        st.markdown("---")

        # Detailed Breakdowns
        st.markdown("### Detailed Breakdowns")
        _render_detail_expanders(results)
        st.markdown("---")

        # Recommendations
        _render_recommendations(results)
        st.markdown("---")
        st.caption("Data sources: OpenStreetMap (Overpass), ISRIC SoilGrids v2.0, "
                   "Macrostrat, Open-Meteo. All free, no API keys required.")
