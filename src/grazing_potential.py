"""
Grazing & Pastoral Potential AI -- Evaluates land suitability for livestock
grazing across 6 dimensions: pasture quality, water for livestock, terrain
accessibility, climate suitability, predator/hazard risk, and infrastructure.
Uses: SoilGrids v2.0, Overpass API, Open Topo Data, Open-Meteo, USGS.
All free, no API key required.
"""

import streamlit as st
import requests
import json
import math
import logging
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
from src.deep_zone_analysis import ANALYSIS_PRESETS

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================
DIMENSION_DEFS = {
    "pasture":        {"name": "Pasture Quality",      "color": "#22c55e", "weight": 0.22},
    "water":          {"name": "Water for Livestock",   "color": "#3b82f6", "weight": 0.20},
    "terrain":        {"name": "Terrain Accessibility", "color": "#f59e0b", "weight": 0.15},
    "climate":        {"name": "Climate Suitability",   "color": "#8b5cf6", "weight": 0.18},
    "hazard":         {"name": "Predator/Hazard Risk",  "color": "#ef4444", "weight": 0.10},
    "infrastructure": {"name": "Infrastructure",       "color": "#06b6d4", "weight": 0.15},
}
LIVESTOCK_PROFILES = {
    "Cattle": {"min_pasture": 40, "min_water": 50, "max_slope": 60, "min_climate": 35,
               "note": "Need ample water (50+ L/day), gentle terrain, quality pasture."},
    "Sheep":  {"min_pasture": 30, "min_water": 35, "max_slope": 70, "min_climate": 30,
               "note": "Hardy grazers, tolerate moderate slopes, lower water needs."},
    "Goats":  {"min_pasture": 20, "min_water": 25, "max_slope": 85, "min_climate": 25,
               "note": "Browse shrubs and rough terrain. Very adaptable climbers."},
    "Horses": {"min_pasture": 50, "min_water": 55, "max_slope": 55, "min_climate": 40,
               "note": "Require high-quality pasture, flat ground, reliable water."},
}

# =============================================================================
# HELPERS
# =============================================================================
def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))

def _range_score(value, lo, hi):
    if value is None: return 50.0
    if lo <= value <= hi: return 100.0
    dist = (lo - value) if value < lo else (value - hi)
    span = hi - lo if hi > lo else 1
    return max(0.0, 100.0 - (dist / span) * 100.0)

def _classify_grazing(score):
    if score >= 80: return "Excellent Grazing Land", "#10b981"
    if score >= 65: return "Good Grazing Potential", "#22c55e"
    if score >= 50: return "Moderate Potential", "#f59e0b"
    if score >= 35: return "Marginal Grazing", "#f97316"
    return "Poor / Unsuitable", "#ef4444"

def _overpass_post(query):
    try:
        r = requests.post("https://overpass-api.de/api/interpreter",
                          data={"data": query}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Overpass error: %s", e)
        return {"elements": []}

# =============================================================================
# DATA FETCHING (ALL CACHED, ttl=900, timeout=10)
# =============================================================================
@st.cache_data(ttl=900)
def _fetch_soil_graze(lat, lon):
    try:
        r = requests.get("https://rest.isric.org/soilgrids/v2.0/properties/query",
                         params={"lat": lat, "lon": lon,
                                 "property": "soc,nitrogen,phh2o,clay,sand,cec",
                                 "depth": "0-5cm,5-15cm", "value": "mean"}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("SoilGrids error: %s", e); return {}

@st.cache_data(ttl=900)
def _fetch_pasture_features(lat, lon, radius=5000):
    q = f"""[out:json][timeout:25];(
      way["landuse"="meadow"](around:{radius},{lat},{lon});
      way["landuse"="grass"](around:{radius},{lat},{lon});
      way["natural"="grassland"](around:{radius},{lat},{lon});
      way["landuse"="farmland"]["crop"="grass"](around:{radius},{lat},{lon});
      way["landuse"="farmyard"](around:{radius},{lat},{lon});
      relation["landuse"="meadow"](around:{radius},{lat},{lon});
      relation["natural"="grassland"](around:{radius},{lat},{lon});
    );out center;"""
    return _overpass_post(q)

@st.cache_data(ttl=900)
def _fetch_water_livestock(lat, lon, radius=5000):
    q = f"""[out:json][timeout:25];(
      way["waterway"~"river|stream|canal"](around:{radius},{lat},{lon});
      node["natural"="spring"](around:{radius},{lat},{lon});
      node["man_made"="water_well"](around:{radius},{lat},{lon});
      way["natural"="water"](around:{radius},{lat},{lon});
      node["natural"="water"](around:{radius},{lat},{lon});
      node["man_made"="water_trough"](around:{radius},{lat},{lon});
      node["amenity"="watering_place"](around:{radius},{lat},{lon});
      way["landuse"="reservoir"](around:{radius},{lat},{lon});
    );out center;"""
    return _overpass_post(q)

@st.cache_data(ttl=900)
def _fetch_elevation_grid(lat, lon):
    pts = "|".join(f"{lat+dy*0.004},{lon+dx*0.004}" for dy in range(-3,4) for dx in range(-3,4))
    try:
        r = requests.get("https://api.opentopodata.org/v1/srtm90m",
                         params={"locations": pts}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Elevation error: %s", e); return {"results": []}

@st.cache_data(ttl=900)
def _fetch_weather_graze(lat, lon):
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast",
                         params={"latitude": lat, "longitude": lon,
                                 "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
                                 "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                                 "timezone": "auto", "forecast_days": 7}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Open-Meteo error: %s", e); return {}

@st.cache_data(ttl=900)
def _fetch_hazard_features(lat, lon, radius=5000):
    q = f"""[out:json][timeout:25];(
      way["landuse"="forest"](around:{radius},{lat},{lon});
      way["natural"="wood"](around:{radius},{lat},{lon});
      way["highway"~"primary|secondary|trunk|motorway"](around:{radius},{lat},{lon});
    );out center;"""
    return _overpass_post(q)

@st.cache_data(ttl=900)
def _fetch_earthquake_risk(lat, lon):
    try:
        r = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/count",
                         params={"format": "geojson", "latitude": lat, "longitude": lon,
                                 "maxradiuskm": 100, "starttime": "2020-01-01",
                                 "minmagnitude": 3}, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("count", 0) if isinstance(data, dict) else 0
    except Exception:
        return 0

@st.cache_data(ttl=900)
def _fetch_infra_livestock(lat, lon, radius=5000):
    q = f"""[out:json][timeout:25];(
      way["barrier"~"fence|hedge"](around:{radius},{lat},{lon});
      node["barrier"="gate"](around:{radius},{lat},{lon});
      way["building"~"barn|stable|farm_auxiliary|cowshed|sty"](around:{radius},{lat},{lon});
      node["amenity"="veterinary"](around:{radius},{lat},{lon});
      node["shop"="farm"](around:{radius},{lat},{lon});
      way["shop"="farm"](around:{radius},{lat},{lon});
      node["amenity"="animal_shelter"](around:{radius},{lat},{lon});
    );out center;"""
    return _overpass_post(q)

# =============================================================================
# SCORING FUNCTIONS
# =============================================================================
def _score_pasture_quality(soil, pasture_data):
    # SoilGrids v2.0 CORRECT parsing
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {}
    for _l in (_layers if isinstance(_layers, list) else []):
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

    soc = _sv("soc", 10) or 0
    nitrogen = _sv("nitrogen", 100) or 0
    ph = _sv("phh2o", 10) or 6.5
    clay = _sv("clay", 10) or 20
    cec = _sv("cec", 10) or 10
    soc_s = min(soc / 15.0, 1.0) * 30.0
    nit_s = min(nitrogen / 1.0, 1.0) * 20.0
    ph_s = _range_score(ph, 5.5, 7.5) * 0.15
    elements = (pasture_data if isinstance(pasture_data, dict) else {}).get("elements", [])
    meadow_c = sum(1 for el in elements if isinstance(el, dict)
                   and (el.get("tags", {}) or {}).get("landuse", "") in ("meadow", "grass"))
    grass_c = sum(1 for el in elements if isinstance(el, dict)
                  and (el.get("tags", {}) or {}).get("natural", "") == "grassland")
    total_grass = meadow_c + grass_c
    grass_s = min(total_grass / 10.0, 1.0) * 35.0
    score = _clamp(soc_s + nit_s + ph_s + grass_s)
    return round(score, 1), {"soc": round(soc, 1), "nitrogen": round(nitrogen, 2),
        "ph": round(ph, 1), "clay": round(clay, 1), "cec": round(cec, 1),
        "meadows": meadow_c, "grasslands": grass_c, "total_pasture_features": total_grass}

def _score_water_livestock(water_data):
    elements = (water_data if isinstance(water_data, dict) else {}).get("elements", [])
    counts = {"river": 0, "stream": 0, "canal": 0, "spring": 0,
              "water_well": 0, "water": 0, "water_trough": 0,
              "watering_place": 0, "reservoir": 0}
    water_coords = []
    for el in (elements if isinstance(elements, list) else []):
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        for tag_key, tag_field in [("waterway", "waterway"), ("natural", "natural"),
                                   ("man_made", "man_made"), ("amenity", "amenity"),
                                   ("landuse", "landuse")]:
            val = tags.get(tag_field, "")
            if val in counts:
                counts[val] += 1
        c_lat = el.get("lat")
        if c_lat is None:
            c_lat = (el.get("center") or {}).get("lat")
        c_lon = el.get("lon")
        if c_lon is None:
            c_lon = (el.get("center") or {}).get("lon")
        if c_lat is not None and c_lon is not None:
            wt = tags.get("waterway", "") or tags.get("natural", "") or tags.get("man_made", "")
            water_coords.append({"lat": c_lat, "lon": c_lon, "type": wt or "water"})
    rivers_streams = counts["river"] + counts["stream"]
    wells_springs = counts["spring"] + counts["water_well"]
    ponds_res = counts["water"] + counts["reservoir"]
    troughs = counts["water_trough"] + counts["watering_place"] + counts["canal"]
    total = rivers_streams + wells_springs + ponds_res + troughs
    score = _clamp(min(rivers_streams / 6.0, 1.0) * 30
                   + min(wells_springs / 4.0, 1.0) * 25
                   + min(ponds_res / 4.0, 1.0) * 25
                   + min(troughs / 3.0, 1.0) * 20)
    return round(score, 1), {"rivers": counts["river"], "streams": counts["stream"],
        "springs": counts["spring"], "wells": counts["water_well"],
        "ponds": counts["water"], "troughs": counts["water_trough"],
        "canals": counts["canal"], "reservoirs": counts["reservoir"],
        "total": total, "coords": water_coords[:50]}

def _score_terrain(elevation_data):
    results = (elevation_data if isinstance(elevation_data, dict) else {}).get("results", [])
    elevations = [float(r.get("elevation")) for r in (results if isinstance(results, list) else [])
                  if isinstance(r, dict) and r.get("elevation") is not None]
    if not elevations:
        return 50.0, {"slope_deg": 0, "elevation": 0, "elev_range": 0}
    center_elev = elevations[len(elevations) // 2]
    elev_range = max(elevations) - min(elevations)
    slope_deg = math.degrees(math.atan(elev_range / 3000.0))
    if slope_deg < 3: slope_s = 95.0
    elif slope_deg < 8: slope_s = 80.0
    elif slope_deg < 15: slope_s = 55.0
    elif slope_deg < 25: slope_s = 30.0
    else: slope_s = max(5.0, 100 - slope_deg * 3)
    score = _clamp(slope_s * 0.70 + _range_score(center_elev, 100, 2000) * 0.30)
    return round(score, 1), {"slope_deg": round(slope_deg, 1),
        "elevation": round(center_elev, 0), "min_elevation": round(min(elevations), 0),
        "max_elevation": round(max(elevations), 0), "elev_range": round(elev_range, 0)}

def _score_climate(weather_data):
    current = (weather_data if isinstance(weather_data, dict) else {}).get("current", {})
    daily = (weather_data if isinstance(weather_data, dict) else {}).get("daily", {})
    daily_maxs = [v for v in daily.get("temperature_2m_max", []) if v is not None]
    daily_mins = [v for v in daily.get("temperature_2m_min", []) if v is not None]
    daily_precips = [v for v in daily.get("precipitation_sum", []) if v is not None]
    temp_now = current.get("temperature_2m") or 15.0
    humidity = current.get("relative_humidity_2m") or 50.0
    wind = current.get("wind_speed_10m") or 10.0
    avg_temp = ((sum(daily_maxs) + sum(daily_mins)) / (len(daily_maxs) + len(daily_mins))
                if (daily_maxs or daily_mins) else temp_now)
    max_temp = max(daily_maxs) if daily_maxs else (avg_temp + 5)
    min_temp = min(daily_mins) if daily_mins else (avg_temp - 5)
    precip_7d = sum(daily_precips) if daily_precips else 0.0
    annual_precip = precip_7d * (365.0 / 7.0) if precip_7d > 0 else 500.0
    if min_temp > 0: ff_pct = _clamp(min_temp * 3.0 + 40.0, 0, 100)
    elif min_temp > -5: ff_pct = _clamp(30.0 + min_temp * 4.0, 0, 100)
    else: ff_pct = _clamp(10.0 + max(0, min_temp + 10) * 2.0, 0, 100)
    growing_days = int(ff_pct / 100.0 * 365)
    score = _clamp(_range_score(avg_temp, 5.0, 28.0) * 0.30
                   + _range_score(annual_precip, 400, 1200) * 0.30
                   + min(growing_days / 250.0, 1.0) * 25.0
                   + _range_score(wind, 0, 25) * 0.15)
    return round(score, 1), {"avg_temp": round(avg_temp, 1), "min_temp": round(min_temp, 1),
        "max_temp": round(max_temp, 1), "humidity": round(humidity, 1),
        "wind_speed": round(wind, 1), "annual_precip_est": round(annual_precip, 0),
        "growing_season_days": growing_days}

def _score_hazard(hazard_data, quake_count):
    elements = (hazard_data if isinstance(hazard_data, dict) else {}).get("elements", [])
    forest_c = road_c = 0
    for el in (elements if isinstance(elements, list) else []):
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        if tags.get("landuse") == "forest" or tags.get("natural") == "wood": forest_c += 1
        if tags.get("highway", "") in ("primary", "secondary", "trunk", "motorway"): road_c += 1
    raw_risk = (min(forest_c / 15.0, 1.0) * 40.0
                + min(road_c / 10.0, 1.0) * 30.0
                + min(quake_count / 20.0, 1.0) * 30.0)
    score = _clamp(100.0 - raw_risk)
    return round(score, 1), {"forest_patches": forest_c, "major_roads": road_c,
                             "earthquake_events": quake_count}

def _score_infrastructure(infra_data):
    elements = (infra_data if isinstance(infra_data, dict) else {}).get("elements", [])
    fences = barns = stables = shelters = vets = farm_shops = gates = hedges = 0
    for el in (elements if isinstance(elements, list) else []):
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        b = tags.get("barrier", ""); bld = tags.get("building", "")
        am = tags.get("amenity", ""); sh = tags.get("shop", "")
        if b == "fence": fences += 1
        elif b == "hedge": hedges += 1
        elif b == "gate": gates += 1
        if bld == "barn": barns += 1
        elif bld in ("stable", "cowshed", "sty"): stables += 1
        elif bld == "farm_auxiliary": shelters += 1
        if am == "veterinary": vets += 1
        if am == "animal_shelter": shelters += 1
        if sh == "farm": farm_shops += 1
    score = _clamp(min((fences + hedges + gates) / 15.0, 1.0) * 30.0
                   + min((barns + stables + shelters) / 5.0, 1.0) * 30.0
                   + min(vets / 2.0, 1.0) * 20.0
                   + min(farm_shops / 3.0, 1.0) * 20.0)
    return round(score, 1), {"fences": fences, "hedges": hedges, "gates": gates,
        "barns": barns, "stables": stables, "shelters": shelters,
        "veterinary_clinics": vets, "farm_shops": farm_shops,
        "total": fences + hedges + gates + barns + stables + shelters + vets + farm_shops}

# =============================================================================
# CARRYING CAPACITY
# =============================================================================
def _estimate_carrying_capacity(overall, climate_details, pasture_details):
    precip = climate_details.get("annual_precip_est", 500)
    soc = pasture_details.get("soc", 5)
    if precip >= 800: base = 1.5
    elif precip >= 600: base = 1.0
    elif precip >= 400: base = 0.6
    elif precip >= 250: base = 0.3
    else: base = 0.1
    cap = round(base * min(soc / 10.0, 1.5) * (overall / 60.0), 2)
    return max(0.01, min(cap, 5.0))

# =============================================================================
# MAIN COMPUTATION (CACHED)
# =============================================================================
@st.cache_data(ttl=900)
def compute_grazing_potential(lat, lon):
    soil = _fetch_soil_graze(lat, lon)
    pasture = _fetch_pasture_features(lat, lon, radius=5000)
    water = _fetch_water_livestock(lat, lon, radius=5000)
    elevation = _fetch_elevation_grid(lat, lon)
    weather = _fetch_weather_graze(lat, lon)
    hazard_raw = _fetch_hazard_features(lat, lon, radius=5000)
    quake_count = _fetch_earthquake_risk(lat, lon)
    infra = _fetch_infra_livestock(lat, lon, radius=5000)

    p_sc, p_dt = _score_pasture_quality(soil, pasture)
    w_sc, w_dt = _score_water_livestock(water)
    t_sc, t_dt = _score_terrain(elevation)
    c_sc, c_dt = _score_climate(weather)
    h_sc, h_dt = _score_hazard(hazard_raw, quake_count)
    i_sc, i_dt = _score_infrastructure(infra)

    scores = {"pasture": p_sc, "water": w_sc, "terrain": t_sc,
              "climate": c_sc, "hazard": h_sc, "infrastructure": i_sc}
    overall = round(_clamp(sum(scores[k] * DIMENSION_DEFS[k]["weight"] for k in DIMENSION_DEFS)), 1)
    capacity = _estimate_carrying_capacity(overall, c_dt, p_dt)

    # Livestock suitability
    recommended = []
    for name, prof in LIVESTOCK_PROFILES.items():
        fit = (min(scores["pasture"] / max(prof["min_pasture"], 1), 1.0) * 30
               + min(scores["water"] / max(prof["min_water"], 1), 1.0) * 25
               + min(scores["terrain"] / max(100 - prof["max_slope"] + 50, 1), 1.0) * 20
               + min(scores["climate"] / max(prof["min_climate"], 1), 1.0) * 25)
        recommended.append({"name": name, "fit_score": round(min(fit, 100), 1), "note": prof["note"]})
    recommended.sort(key=lambda x: x["fit_score"], reverse=True)

    recs = []
    if p_sc < 40: recs.append("Low pasture quality. Consider reseeding with improved grass varieties or applying fertiliser.")
    if w_sc < 35: recs.append("Insufficient water sources. Install troughs, bore wells, or pipe water from nearby sources.")
    if t_sc < 40: recs.append("Steep terrain limits livestock movement. Goats may be better suited than cattle here.")
    if c_sc < 35: recs.append("Climate conditions are challenging. Provide shelters and supplementary feed during extreme seasons.")
    if h_sc < 40: recs.append("Elevated predator or traffic risk. Strengthen fencing and consider guardian animals or patrols.")
    if i_sc < 30: recs.append("Limited livestock infrastructure. Invest in fencing, shelters, and veterinary access.")
    if overall >= 65: recs.append("Good overall grazing potential. Regular rotational grazing will maximise pasture longevity.")
    if not recs: recs.append("Moderate conditions for grazing. Match livestock type to local conditions for best results.")

    return {"scores": scores, "overall": overall, "capacity_au_ha": capacity,
            "recommended_livestock": recommended,
            "details": {"pasture": p_dt, "water": w_dt, "terrain": t_dt,
                        "climate": c_dt, "hazard": h_dt, "infrastructure": i_dt},
            "recommendations": recs}

# =============================================================================
# UI HELPERS
# =============================================================================
_CARD_TPL = ('<div style="background:rgba(26,26,46,0.85);border:1px solid {border};'
             'border-radius:10px;padding:14px;text-align:center;margin-bottom:8px;">'
             '<div style="color:#8b97b0;font-size:11px;text-transform:uppercase;'
             'letter-spacing:0.5px;">{title}</div>'
             '<div style="color:{sc_color};font-size:32px;font-weight:bold;'
             'margin:6px 0;">{value}</div>'
             '<div style="color:#5a6580;font-size:11px;">{desc}</div>'
             '<div style="background:#1a2235;border-radius:6px;height:8px;'
             'margin-top:8px;overflow:hidden;">'
             '<div style="width:{pct}%;background:{border};height:100%;'
             'border-radius:6px;"></div></div></div>')

def _sc_color(sc):
    return "#10b981" if sc >= 70 else ("#f59e0b" if sc >= 45 else "#ef4444")

def _dim_desc(key, details):
    d = details.get(key, {})
    m = {"pasture": f"SOC: {d.get('soc',0)} g/kg | Meadows: {d.get('meadows',0)} | Grasslands: {d.get('grasslands',0)}",
         "water": f"Rivers: {d.get('rivers',0)} | Wells: {d.get('wells',0)} | Ponds: {d.get('ponds',0)} | Troughs: {d.get('troughs',0)}",
         "terrain": f"Slope: {d.get('slope_deg',0)} deg | Elev: {d.get('elevation',0)} m",
         "climate": f"Temp: {d.get('avg_temp',0)} C | Precip: {d.get('annual_precip_est',0)} mm/yr | Growing: {d.get('growing_season_days',0)} d",
         "hazard": f"Forest: {d.get('forest_patches',0)} | Roads: {d.get('major_roads',0)} | Quakes: {d.get('earthquake_events',0)}",
         "infrastructure": f"Fences: {d.get('fences',0)} | Barns: {d.get('barns',0)} | Vets: {d.get('veterinary_clinics',0)}"}
    return m.get(key, "")

# =============================================================================
# RENDER TAB
# =============================================================================
def render_grazing_potential_tab():
    st.markdown("## Grazing & Pastoral Potential")
    st.caption("Livestock suitability: pasture, water, terrain, climate & infrastructure")

    # Location selector
    col_p, col_la, col_lo = st.columns([1.4, 1, 1])
    with col_p:
        preset = st.selectbox("Location Preset", list(ANALYSIS_PRESETS.keys()), key="graze_preset")
    p = ANALYSIS_PRESETS.get(preset)
    d_lat = p.get("lat", 41.90) if p else 41.90
    d_lon = p.get("lon", 12.50) if p else 12.50
    with col_la:
        lat = st.number_input("Latitude", value=d_lat, format="%.5f",
                              min_value=-90.0, max_value=90.0, key="graze_lat")
    with col_lo:
        lon = st.number_input("Longitude", value=d_lon, format="%.5f",
                              min_value=-180.0, max_value=180.0, key="graze_lon")

    if not st.button("Analyze Grazing Potential", type="primary",
                     use_container_width=True, key="graze_run"):
        st.info("Select a location and click **Analyze Grazing Potential** to evaluate "
                "pasture, water, terrain, climate and infrastructure.")
        return

    with st.spinner("Fetching soil, pasture, water, weather and infrastructure data..."):
        result = compute_grazing_potential(lat, lon)

    scores = result["scores"]; overall = result["overall"]
    capacity = result["capacity_au_ha"]; recommended = result["recommended_livestock"]
    details = result["details"]; recs = result["recommendations"]
    classification, class_color = _classify_grazing(overall)
    st.markdown("---")

    # 1. Overall Grazing Index
    st.markdown(
        f'<div style="background:rgba(26,26,46,0.85);border:1px solid {class_color};'
        f'border-radius:14px;padding:24px;text-align:center;margin-bottom:16px;">'
        f'<div style="color:#8b97b0;font-size:13px;text-transform:uppercase;'
        f'letter-spacing:1px;">Overall Grazing Index</div>'
        f'<div style="color:{class_color};font-size:52px;font-weight:bold;margin:8px 0;">{overall}</div>'
        f'<div style="color:{class_color};font-size:18px;font-weight:600;">{classification}</div>'
        f'<div style="color:#5a6580;font-size:12px;margin-top:6px;">'
        f'Carrying capacity estimate: <b>{capacity}</b> AU/ha (animal units per hectare)</div></div>',
        unsafe_allow_html=True)

    # 2. Radar Chart
    st.markdown("<h5 style='color:#e8ecf4;margin-bottom:4px;'>Grazing Dimensions Radar</h5>",
                unsafe_allow_html=True)
    dim_keys = list(DIMENSION_DEFS.keys())
    r_names = [DIMENSION_DEFS[k]["name"] for k in dim_keys]
    r_vals = [scores[k] for k in dim_keys]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=r_vals + [r_vals[0]], theta=r_names + [r_names[0]],
        fill="toself", fillcolor="rgba(34,197,94,0.15)",
        line=dict(color="#22c55e", width=2), marker=dict(size=6, color="#22c55e"), name="Score"))
    fig.update_layout(
        polar=dict(bgcolor="rgba(26,26,46,0.6)",
                   radialaxis=dict(visible=True, range=[0, 100], gridcolor="#2a3550",
                                   tickfont=dict(color="#5a6580", size=10)),
                   angularaxis=dict(gridcolor="#2a3550", tickfont=dict(color="#e8ecf4", size=11))),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=30, b=30), height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key="graze_radar_chart")

    # 3. Six Metric Cards (3x2)
    st.markdown("<h5 style='color:#e8ecf4;margin-bottom:4px;'>Dimension Scores</h5>",
                unsafe_allow_html=True)
    dim_items = list(DIMENSION_DEFS.items())
    for row_slice in [dim_items[:3], dim_items[3:]]:
        cols = st.columns(3)
        for idx, (key, meta) in enumerate(row_slice):
            with cols[idx]:
                sc = scores[key]
                st.markdown(_CARD_TPL.format(
                    border=meta["color"], title=meta["name"], sc_color=_sc_color(sc),
                    value=sc, desc=_dim_desc(key, details), pct=sc), unsafe_allow_html=True)

    # 4. Recommended Livestock
    st.markdown("<h5 style='color:#e8ecf4;margin-bottom:4px;'>Recommended Livestock</h5>",
                unsafe_allow_html=True)
    lv_cols = st.columns(len(recommended))
    for idx, lv in enumerate(recommended):
        with lv_cols[idx]:
            fit = lv["fit_score"]; fc = _sc_color(fit)
            st.markdown(
                f'<div style="background:rgba(26,26,46,0.85);border:1px solid {fc};'
                f'border-radius:10px;padding:14px;text-align:center;margin-bottom:8px;">'
                f'<div style="color:#e8ecf4;font-size:16px;font-weight:600;">{lv["name"]}</div>'
                f'<div style="color:{fc};font-size:28px;font-weight:bold;margin:6px 0;">{fit}</div>'
                f'<div style="color:#5a6580;font-size:10px;">Fit Score</div>'
                f'<div style="color:#8b97b0;font-size:10px;margin-top:6px;">{lv["note"]}</div></div>',
                unsafe_allow_html=True)

    # 5. Folium Map
    st.markdown("<h5 style='color:#e8ecf4;margin-bottom:4px;'>Water Sources & Grassland Map</h5>",
                unsafe_allow_html=True)
    try:
        import folium
        from streamlit_folium import st_folium
        m = folium.Map(location=[lat, lon], zoom_start=13, tiles="OpenStreetMap")
        folium.Marker([lat, lon], popup="Analysis Center",
                      icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(m)
        for wc in details.get("water", {}).get("coords", [])[:40]:
            wla, wlo = wc.get("lat"), wc.get("lon")
            if wla is not None and wlo is not None:
                folium.CircleMarker([wla, wlo], radius=5, color="#3b82f6",
                                    fill=True, fill_opacity=0.7,
                                    popup=f"Water: {wc.get('type','water')}").add_to(m)
        folium.Circle([lat, lon], radius=5000, color="#22c55e", fill=False,
                      weight=2, dash_array="5", popup="5 km analysis radius").add_to(m)
        st_folium(m, width=700, height=450, key="graze_folium_map")
    except ImportError:
        st.warning("Install `folium` and `streamlit-folium` for the interactive map: "
                   "`pip install folium streamlit-folium`")

    # 6. Recommendations
    st.markdown("<h5 style='color:#e8ecf4;margin-bottom:4px;'>Recommendations</h5>",
                unsafe_allow_html=True)
    for rec in recs:
        st.markdown(f'<div style="background:rgba(26,26,46,0.7);border-left:3px solid #22c55e;'
                    f'padding:10px 14px;border-radius:6px;margin-bottom:8px;'
                    f'color:#c5cdd8;font-size:13px;">{rec}</div>', unsafe_allow_html=True)

    # 7. Raw Data
    with st.expander("Raw Analysis Data", expanded=False):
        st.json({"coordinates": {"lat": lat, "lon": lon},
                 "overall_grazing_index": overall, "classification": classification,
                 "carrying_capacity_au_ha": capacity,
                 "dimension_scores": {DIMENSION_DEFS[k]["name"]: scores[k] for k in scores},
                 "recommended_livestock": recommended,
                 "details": {k: {kk: vv for kk, vv in v.items() if kk != "coords"}
                             for k, v in details.items()},
                 "recommendations": recs})
