"""
Smart Zoning & Land Use Recommendation module for TerraScout AI.
AI-powered optimal land use suggestion based on terrain, soil, climate,
and infrastructure.  Evaluates 8 land-use scenarios, ranks by suitability.
Data sources (free, no key): Open Topo Data, ISRIC SoilGrids v2.0,
Open-Meteo, Overpass API, USGS Earthquakes.
"""
import logging, math
from html import escape
import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

# ── API Endpoints ─────────────────────────────────────────────────────────────
OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"
SOILGRIDS_API = "https://rest.isric.org/soilgrids/v2.0/properties/query"
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
USGS_EQ_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
OVERPASS_API = "https://overpass-api.de/api/interpreter"

# ── Theme ─────────────────────────────────────────────────────────────────────
CLR_BG = "#1a1a2e";  CLR_SURFACE = "#16213e";  CLR_CARD = "#0f3460"
CLR_BORDER = "#1a4080";  CLR_TEXT = "#e8ecf4";  CLR_TEXT_SEC = "#8b97b0"
CLR_ACCENT = "#06b6d4"
CLR_EXCELLENT = "#22c55e";  CLR_GOOD = "#84cc16"
CLR_MODERATE = "#f59e0b";   CLR_POOR = "#ef4444";  CLR_UNSUITABLE = "#991b1b"

# ── Scenario Definitions ─────────────────────────────────────────────────────
SCENARIOS = {
    "residential": {
        "name": "Residential Development", "icon": "\U0001f3e0", "color": "#f59e0b",
        "description": "Housing requiring flat terrain, soil stability, services, water.",
        "factors": {"terrain_flatness": .20, "soil_stability": .15, "services_nearby": .20,
                    "water_access": .15, "climate_comfort": .10, "seismic_safety": .10,
                    "road_access": .10},
    },
    "agriculture": {
        "name": "Agricultural Use", "icon": "\U0001f33e", "color": "#10b981",
        "description": "Farming needing fertile soil (SOC, CEC, clay), water, moderate climate.",
        "factors": {"soil_fertility": .30, "water_access": .20, "climate_comfort": .15,
                    "terrain_flatness": .15, "precipitation": .10, "seismic_safety": .05,
                    "road_access": .05},
    },
    "industrial": {
        "name": "Industrial Zone", "icon": "\U0001f3ed", "color": "#ef4444",
        "description": "Manufacturing needing flat terrain, roads, distance from homes.",
        "factors": {"terrain_flatness": .25, "road_access": .25, "soil_stability": .15,
                    "distance_residential": .10, "seismic_safety": .10, "water_access": .10,
                    "climate_comfort": .05},
    },
    "conservation": {
        "name": "Conservation Area", "icon": "\U0001f333", "color": "#059669",
        "description": "Nature preservation: biodiversity, water, forest, low human impact.",
        "factors": {"biodiversity_potential": .25, "water_features": .20, "forest_cover": .20,
                    "low_human_impact": .15, "terrain_diversity": .10, "precipitation": .10},
    },
    "renewable_energy": {
        "name": "Renewable Energy", "icon": "\u2600\ufe0f", "color": "#3b82f6",
        "description": "Solar/wind production: clear skies, elevation, open flat terrain.",
        "factors": {"solar_potential": .25, "wind_potential": .20, "terrain_flatness": .15,
                    "road_access": .15, "low_human_impact": .10, "seismic_safety": .10,
                    "climate_comfort": .05},
    },
    "tourism": {
        "name": "Tourism & Recreation", "icon": "\U0001f3d6\ufe0f", "color": "#8b5cf6",
        "description": "Scenic tourism with amenities, pleasant weather, varied landscape.",
        "factors": {"scenic_value": .25, "amenities": .20, "climate_comfort": .20,
                    "water_features": .15, "road_access": .10, "terrain_diversity": .10},
    },
    "military": {
        "name": "Military / Strategic", "icon": "\U0001f6e1\ufe0f", "color": "#dc2626",
        "description": "Defence: elevation advantage, visibility, access control.",
        "factors": {"elevation_advantage": .25, "visibility": .20, "terrain_diversity": .15,
                    "road_access": .15, "distance_residential": .10, "water_access": .10,
                    "seismic_safety": .05},
    },
    "emergency_shelter": {
        "name": "Emergency Shelter", "icon": "\u26d1\ufe0f", "color": "#f97316",
        "description": "Disaster relief: flat, safe from hazards, water, supply routes.",
        "factors": {"terrain_flatness": .25, "seismic_safety": .20, "water_access": .15,
                    "road_access": .15, "climate_comfort": .10, "services_nearby": .10,
                    "flood_safety": .05},
    },
}

# ── Helpers ───────────────────────────────────────────────────────────────────
def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))

def _score_color(s):
    if s >= 80: return CLR_EXCELLENT
    if s >= 60: return CLR_GOOD
    if s >= 40: return CLR_MODERATE
    if s >= 20: return CLR_POOR
    return CLR_UNSUITABLE

def _score_label(s):
    if s >= 80: return "Excellent"
    if s >= 60: return "Good"
    if s >= 40: return "Moderate"
    if s >= 20: return "Poor"
    return "Unsuitable"

def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ── Cached Data Fetching ─────────────────────────────────────────────────────
@st.cache_data(ttl=900)
def _fetch_elevation(lat: float, lon: float) -> dict:
    """Fetch elevation for a 5x5 grid around the target point."""
    try:
        pts, lats_l, lons_l = [], [], []
        half, step = 2, 0.01
        for i in range(-half, half + 1):
            for j in range(-half, half + 1):
                plat, plon = lat + i * step, lon + j * step
                pts.append(f"{plat:.5f},{plon:.5f}")
                lats_l.append(plat); lons_l.append(plon)
        resp = requests.get(OPEN_TOPO_API, params={"locations": "|".join(pts)}, timeout=10)
        resp.raise_for_status()
        elevs = [float(r.get("elevation") or 0) for r in resp.json().get("results", [])]
        if not elevs:
            return {"center": 0, "min": 0, "max": 0, "avg": 0, "std": 0,
                    "slope_deg": 0, "elevations": []}
        avg_e = sum(elevs) / len(elevs)
        std_e = math.sqrt(sum((e - avg_e) ** 2 for e in elevs) / len(elevs))
        span_m = _haversine_km(lat - half * step, lon, lat + half * step, lon) * 1000
        slope_deg = math.degrees(math.atan2(max(elevs) - min(elevs), span_m)) if span_m else 0
        return {"center": elevs[len(elevs) // 2], "min": min(elevs), "max": max(elevs),
                "avg": avg_e, "std": std_e, "slope_deg": slope_deg, "elevations": elevs}
    except Exception as exc:
        logger.warning("Elevation fetch error: %s", exc)
        return {"center": 0, "min": 0, "max": 0, "avg": 0, "std": 0,
                "slope_deg": 0, "elevations": []}

@st.cache_data(ttl=900)
def _fetch_soil(lat: float, lon: float) -> dict:
    """Fetch soil composition from ISRIC SoilGrids v2.0."""
    try:
        resp = requests.get(SOILGRIDS_API, params={
            "lon": lon, "lat": lat,
            "property": ["clay", "sand", "silt", "soc", "phh2o", "nitrogen", "cec"],
            "depth": ["0-5cm", "5-15cm", "15-30cm", "30-60cm", "60-100cm"],
            "value": "mean"}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("SoilGrids error: %s", exc)
        return {}

@st.cache_data(ttl=900)
def _fetch_weather(lat: float, lon: float) -> dict:
    """Fetch current + 7-day forecast from Open-Meteo."""
    try:
        resp = requests.get(OPEN_METEO_API, params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,precipitation,"
                       "wind_speed_10m,surface_pressure,cloud_cover",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                     "wind_speed_10m_max,sunshine_duration",
            "timezone": "auto", "forecast_days": 7}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Open-Meteo error: %s", exc)
        return {}

@st.cache_data(ttl=900)
def _fetch_infrastructure(lat: float, lon: float, radius: int = 3000) -> dict:
    """Fetch infrastructure from Overpass API."""
    query = f"""[out:json][timeout:25];
(
  way["highway"~"motorway|trunk|primary|secondary|tertiary"](around:{radius},{lat},{lon});
  way["building"](around:{radius},{lat},{lon});
  node["amenity"~"school|hospital|clinic|pharmacy|fire_station|police"](around:{radius},{lat},{lon});
  node["shop"](around:{radius},{lat},{lon});
  way["landuse"~"residential|industrial|commercial|farmland|forest|meadow"](around:{radius},{lat},{lon});
  way["natural"="water"](around:{radius},{lat},{lon});
  way["waterway"](around:{radius},{lat},{lon});
  way["leisure"~"park|nature_reserve"](around:{radius},{lat},{lon});
  node["public_transport"="stop_position"](around:{radius},{lat},{lon});
  node["tourism"~"hotel|museum|attraction|viewpoint"](around:{radius},{lat},{lon});
);
out center;"""
    try:
        resp = requests.post(OVERPASS_API, data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Overpass error: %s", exc)
        return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_earthquakes(lat: float, lon: float, radius_km: int = 150) -> dict:
    """Fetch seismic events from USGS (last 2 years)."""
    try:
        from datetime import datetime, timedelta
        end = datetime.utcnow(); start = end - timedelta(days=730)
        resp = requests.get(USGS_EQ_API, params={
            "format": "geojson", "starttime": start.strftime("%Y-%m-%d"),
            "endtime": end.strftime("%Y-%m-%d"), "latitude": lat,
            "longitude": lon, "maxradiuskm": radius_km,
            "minmagnitude": 2.0, "limit": 500}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("USGS earthquake error: %s", exc)
        return {"features": []}

# ── Soil Parsing (SoilGrids v2.0 correct structure) ──────────────────────────
def _parse_soil(soil: dict) -> dict:
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
    return {"clay": _sv("clay", 10), "sand": _sv("sand", 10), "silt": _sv("silt", 10),
            "soc": _sv("soc", 10), "ph": _sv("phh2o", 10),
            "nitrogen": _sv("nitrogen", 100), "cec": _sv("cec", 10)}

# ── Infrastructure Analysis ──────────────────────────────────────────────────
def _analyse_infrastructure(infra: dict) -> dict:
    elements = infra.get("elements", []) if isinstance(infra, dict) else []
    c = {"roads": 0, "buildings": 0, "amenities": 0, "shops": 0,
         "residential_zones": 0, "industrial_zones": 0, "commercial_zones": 0,
         "farmland": 0, "forest": 0, "water_bodies": 0, "waterways": 0,
         "parks": 0, "transport_stops": 0, "tourism_sites": 0}
    for el in elements:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        if not isinstance(tags, dict):
            continue
        hw = tags.get("highway", "")
        if hw in ("motorway", "trunk", "primary", "secondary", "tertiary"):
            c["roads"] += 1
        if tags.get("building"): c["buildings"] += 1
        am = tags.get("amenity", "")
        if am in ("school", "hospital", "clinic", "pharmacy", "fire_station", "police"):
            c["amenities"] += 1
        if tags.get("shop"): c["shops"] += 1
        lu = tags.get("landuse", "")
        if lu == "residential":   c["residential_zones"] += 1
        elif lu == "industrial":  c["industrial_zones"] += 1
        elif lu == "commercial":  c["commercial_zones"] += 1
        elif lu == "farmland":    c["farmland"] += 1
        elif lu == "forest":      c["forest"] += 1
        if tags.get("natural") == "water": c["water_bodies"] += 1
        if tags.get("waterway"): c["waterways"] += 1
        if tags.get("leisure", "") in ("park", "nature_reserve"): c["parks"] += 1
        if tags.get("public_transport") == "stop_position": c["transport_stops"] += 1
        if tags.get("tourism"): c["tourism_sites"] += 1
    return c

# ── Factor Scoring Functions (each returns 0-100) ────────────────────────────
def _score_terrain_flatness(elev):
    s = elev.get("slope_deg", 0)
    if s <= 1: return 95.0
    if s <= 3: return 85.0
    if s <= 5: return 70.0
    if s <= 10: return 50.0
    if s <= 15: return 30.0
    return max(5.0, 25.0 - s)

def _score_soil_fertility(p):
    sc = 50.0
    soc, cec, clay, ph = p.get("soc"), p.get("cec"), p.get("clay"), p.get("ph")
    if soc is not None: sc += _clamp(soc * 3, 0, 20)
    if cec is not None: sc += _clamp(cec * 1.5, 0, 15)
    if clay is not None:
        sc += 10 if 15 <= clay <= 35 else (5 if clay < 15 else -5)
    if ph is not None:
        sc += 5 if 5.5 <= ph <= 7.5 else -5
    return _clamp(sc)

def _score_soil_stability(p):
    sc = 60.0
    clay, sand = p.get("clay"), p.get("sand")
    if clay is not None:
        sc += 15 if clay < 20 else (5 if clay < 35 else -15)
    if sand is not None:
        sc += 10 if sand > 40 else (5 if sand > 20 else 0)
    return _clamp(sc)

def _score_water_access(ic):
    t = ic.get("water_bodies", 0) + ic.get("waterways", 0)
    if t >= 5: return 95.0
    if t >= 3: return 80.0
    if t >= 1: return 60.0
    return 20.0

def _score_water_features(ic):
    return _clamp(30 + ic.get("water_bodies", 0) * 10 + ic.get("waterways", 0) * 8)

def _score_services_nearby(ic):
    t = ic.get("amenities", 0) + ic.get("shops", 0) + ic.get("transport_stops", 0)
    if t >= 20: return 95.0
    if t >= 10: return 80.0
    if t >= 5: return 65.0
    if t >= 1: return 40.0
    return 15.0

def _score_road_access(ic):
    r = ic.get("roads", 0)
    if r >= 15: return 95.0
    if r >= 8: return 80.0
    if r >= 3: return 60.0
    if r >= 1: return 40.0
    return 15.0

def _score_climate_comfort(w):
    cur = w.get("current", {})
    if not cur: return 50.0
    temp, hum, wind = cur.get("temperature_2m"), cur.get("relative_humidity_2m"), cur.get("wind_speed_10m")
    sc = 60.0
    if temp is not None:
        if 15 <= temp <= 25: sc += 15
        elif 10 <= temp <= 30: sc += 5
        elif temp < 0 or temp > 40: sc -= 20
        else: sc -= 5
    if hum is not None:
        sc += 10 if 30 <= hum <= 70 else -5
    if wind is not None:
        if wind < 15: sc += 10
        elif wind > 30: sc -= 15
    return _clamp(sc)

def _score_precipitation(w):
    precip = w.get("daily", {}).get("precipitation_sum", [])
    if not precip: return 50.0
    avg = sum(p for p in precip if p is not None) / max(len(precip), 1)
    if 2 <= avg <= 8: return 90.0
    if 1 <= avg <= 15: return 70.0
    return 35.0 if avg < 1 else 40.0

def _score_seismic_safety(eq):
    feats = eq.get("features", [])
    if not feats: return 95.0
    max_mag = max((f.get("properties", {}).get("mag", 0) or 0) for f in feats)
    return _clamp(95 - min(len(feats) * 2, 40) - min(max_mag * 8, 40))

def _score_flood_safety(elev, ic):
    sc = 70.0
    ctr = elev.get("center", 0)
    water = ic.get("water_bodies", 0) + ic.get("waterways", 0)
    if ctr > 200: sc += 15
    elif ctr > 50: sc += 5
    else: sc -= 10
    if water == 0: sc += 10
    elif water > 3: sc -= 10
    return _clamp(sc)

def _score_distance_residential(ic):
    r = ic.get("residential_zones", 0)
    if r == 0: return 95.0
    if r <= 2: return 70.0
    if r <= 5: return 50.0
    return max(10, 40 - r * 3)

def _score_biodiversity_potential(ic, w):
    base = 30.0 + ic.get("forest", 0) * 8 + ic.get("parks", 0) * 6
    base += (ic.get("water_bodies", 0) + ic.get("waterways", 0)) * 5
    precip = w.get("daily", {}).get("precipitation_sum", [])
    if precip:
        avg = sum(p for p in precip if p is not None) / max(len(precip), 1)
        if avg > 2: base += 10
    return _clamp(base)

def _score_forest_cover(ic):
    f = ic.get("forest", 0)
    if f >= 5: return 95.0
    if f >= 3: return 75.0
    if f >= 1: return 50.0
    return 15.0

def _score_low_human_impact(ic):
    t = ic.get("buildings", 0) + ic.get("industrial_zones", 0) * 10 + ic.get("residential_zones", 0) * 5
    if t == 0: return 95.0
    if t <= 10: return 75.0
    if t <= 50: return 50.0
    if t <= 200: return 30.0
    return 10.0

def _score_terrain_diversity(elev):
    s = elev.get("std", 0)
    if s >= 100: return 90.0
    if s >= 50: return 75.0
    if s >= 20: return 60.0
    if s >= 5: return 40.0
    return 20.0

def _score_solar_potential(w):
    cur = w.get("current", {})
    cloud = cur.get("cloud_cover", 50) if cur else 50
    sunshine = w.get("daily", {}).get("sunshine_duration", [])
    sc = 50.0
    if cloud is not None: sc += _clamp((100 - cloud) * 0.3, 0, 30)
    if sunshine:
        avg_s = sum(s for s in sunshine if s is not None) / max(len(sunshine), 1)
        hrs = avg_s / 3600 if avg_s > 100 else avg_s
        sc += _clamp(hrs * 3, 0, 25)
    return _clamp(sc)

def _score_wind_potential(w, elev):
    cur = w.get("current", {})
    wind = cur.get("wind_speed_10m", 0) if cur else 0
    sc = 30.0
    if wind is not None:
        if wind >= 20: sc += 35
        elif wind >= 10: sc += 25
        elif wind >= 5: sc += 15
    ctr = elev.get("center", 0)
    if ctr > 500: sc += 15
    elif ctr > 200: sc += 10
    return _clamp(sc)

def _score_scenic_value(elev, ic):
    return _clamp(30.0 + elev.get("std", 0) * 0.3
                  + (ic.get("water_bodies", 0) + ic.get("waterways", 0)) * 6
                  + ic.get("parks", 0) * 5 + ic.get("tourism_sites", 0) * 8)

def _score_amenities(ic):
    return _clamp(20.0 + ic.get("tourism_sites", 0) * 10
                  + ic.get("shops", 0) * 2 + ic.get("transport_stops", 0) * 3)

def _score_elevation_advantage(elev):
    c = elev.get("center", 0)
    if c >= 1000: return 95.0
    if c >= 500: return 80.0
    if c >= 200: return 65.0
    if c >= 50: return 45.0
    return 20.0

def _score_visibility(elev):
    d = elev.get("center", 0) - elev.get("avg", 0)
    if d >= 50: return 90.0
    if d >= 20: return 75.0
    if d >= 5: return 60.0
    if d >= 0: return 45.0
    return 25.0

# ── Factor Dispatcher ────────────────────────────────────────────────────────
def _compute_factor(name, elev, ps, w, ic, eq):
    _d = {
        "terrain_flatness": lambda: _score_terrain_flatness(elev),
        "soil_fertility": lambda: _score_soil_fertility(ps),
        "soil_stability": lambda: _score_soil_stability(ps),
        "water_access": lambda: _score_water_access(ic),
        "water_features": lambda: _score_water_features(ic),
        "services_nearby": lambda: _score_services_nearby(ic),
        "road_access": lambda: _score_road_access(ic),
        "climate_comfort": lambda: _score_climate_comfort(w),
        "precipitation": lambda: _score_precipitation(w),
        "seismic_safety": lambda: _score_seismic_safety(eq),
        "flood_safety": lambda: _score_flood_safety(elev, ic),
        "distance_residential": lambda: _score_distance_residential(ic),
        "biodiversity_potential": lambda: _score_biodiversity_potential(ic, w),
        "forest_cover": lambda: _score_forest_cover(ic),
        "low_human_impact": lambda: _score_low_human_impact(ic),
        "terrain_diversity": lambda: _score_terrain_diversity(elev),
        "solar_potential": lambda: _score_solar_potential(w),
        "wind_potential": lambda: _score_wind_potential(w, elev),
        "scenic_value": lambda: _score_scenic_value(elev, ic),
        "amenities": lambda: _score_amenities(ic),
        "elevation_advantage": lambda: _score_elevation_advantage(elev),
        "visibility": lambda: _score_visibility(elev),
    }
    fn = _d.get(name)
    return round(fn(), 1) if fn else 50.0

# ── Scoring Engine ───────────────────────────────────────────────────────────
def _score_all_scenarios(elev, soil, weather, infra, eq_data):
    ps = _parse_soil(soil)
    ic = _analyse_infrastructure(infra)
    results = []
    for key, sc in SCENARIOS.items():
        details, wsum = [], 0.0
        for fn, wt in sc["factors"].items():
            raw = _compute_factor(fn, elev, ps, weather, ic, eq_data)
            wsum += raw * wt
            details.append({"name": fn.replace("_", " ").title(), "score": raw,
                            "weight": wt, "weighted": round(raw * wt, 1)})
        comp = round(_clamp(wsum), 1)
        results.append({"key": key, "name": sc["name"], "icon": sc["icon"],
                        "color": sc["color"], "description": sc["description"],
                        "score": comp, "label": _score_label(comp),
                        "factors": sorted(details, key=lambda d: d["weighted"], reverse=True)})
    results.sort(key=lambda r: r["score"], reverse=True)
    return results

# ── UI Rendering ─────────────────────────────────────────────────────────────
def _render_badge(r):
    col = _score_color(r["score"])
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,{CLR_CARD},{CLR_SURFACE});
                border:2px solid {col};border-radius:12px;padding:24px;
                text-align:center;margin-bottom:16px;">
        <div style="font-size:48px;">{escape(r['icon'])}</div>
        <div style="font-size:28px;font-weight:700;color:{col};margin-top:8px;">
            {escape(r['name'])}</div>
        <div style="font-size:42px;font-weight:800;color:{col};margin-top:4px;">
            {r['score']}/100</div>
        <div style="font-size:16px;color:{CLR_TEXT_SEC};margin-top:8px;">
            Suitability: <b style="color:{col}">{escape(r['label'])}</b></div>
        <div style="font-size:13px;color:{CLR_TEXT_SEC};margin-top:12px;
                    max-width:500px;margin-left:auto;margin-right:auto;">
            {escape(r['description'])}</div>
    </div>""", unsafe_allow_html=True)

def _render_bar_chart(results):
    names = [r["name"] for r in results]
    scores = [r["score"] for r in results]
    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h",
        marker_color=[_score_color(s) for s in scores],
        text=[f"{s}" for s in scores], textposition="outside",
        textfont=dict(color=CLR_TEXT, size=13)))
    fig.update_layout(
        title=dict(text="Land Use Suitability Ranking", font=dict(color=CLR_TEXT, size=18)),
        xaxis=dict(title="Score (0-100)", range=[0, 110], gridcolor=CLR_BORDER, color=CLR_TEXT_SEC),
        yaxis=dict(autorange="reversed", color=CLR_TEXT),
        plot_bgcolor=CLR_SURFACE, paper_bgcolor=CLR_BG,
        height=380, margin=dict(l=180, r=60, t=50, b=40))
    st.plotly_chart(fig, use_container_width=True, key="szone_bar_chart")

def _render_factor_breakdown(result, idx):
    label = f'{result["icon"]} {result["name"]}  --  {result["score"]}/100 ({result["label"]})'
    with st.expander(label, expanded=(idx == 0)):
        st.markdown(f'<div style="color:{CLR_TEXT_SEC};font-size:13px;margin-bottom:12px;">'
                    f'{escape(result["description"])}</div>', unsafe_allow_html=True)
        f_names = [f["name"] for f in result["factors"]]
        f_scores = [f["score"] for f in result["factors"]]
        f_wts = [f"{f['weight']*100:.0f}%" for f in result["factors"]]
        fig = go.Figure(go.Bar(
            x=f_scores, y=[f"{n} ({w})" for n, w in zip(f_names, f_wts)],
            orientation="h", marker_color=[_score_color(s) for s in f_scores],
            text=[f"{s}" for s in f_scores], textposition="outside",
            textfont=dict(color=CLR_TEXT, size=11)))
        fig.update_layout(
            xaxis=dict(range=[0, 110], gridcolor=CLR_BORDER, color=CLR_TEXT_SEC, title="Factor Score"),
            yaxis=dict(autorange="reversed", color=CLR_TEXT),
            plot_bgcolor=CLR_SURFACE, paper_bgcolor=CLR_BG,
            height=max(200, len(f_names) * 38 + 60), margin=dict(l=200, r=50, t=10, b=30))
        st.plotly_chart(fig, use_container_width=True,
                        key=f"szone_factor_{result['key']}_{idx}")

def _render_summary_table(results):
    st.markdown("### Summary Table")
    hdr = "| Rank | Scenario | Score | Rating |\n|---:|:---|---:|:---|\n"
    rows = "".join(f"| {i} | {r['icon']} {r['name']} | {r['score']} | {r['label']} |\n"
                   for i, r in enumerate(results, 1))
    st.markdown(hdr + rows)

def _render_map(lat, lon, results):
    try:
        import folium
        from streamlit.components.v1 import html as st_html
        m = folium.Map(location=[lat, lon], zoom_start=13, tiles="OpenStreetMap")
        top = results[0] if results else None
        popup = (f"<b>{top['icon']} {top['name']}</b><br>Score: {top['score']}/100<br>"
                 f"Rating: {top['label']}") if top else "Analysis point"
        folium.Marker([lat, lon], popup=folium.Popup(popup, max_width=250),
                      tooltip="Analysis Centre",
                      icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
        folium.Circle([lat, lon], radius=3000, color=CLR_ACCENT, fill=True,
                      fill_opacity=0.08, popup="3 km analysis radius").add_to(m)
        for i, r in enumerate(results[:3]):
            folium.Circle([lat, lon], radius=[2200, 1500, 800][i], color=r["color"],
                          fill=False, weight=2, dash_array="5 5",
                          popup=f"#{i+1}: {r['name']} ({r['score']})").add_to(m)
        st_html(f'<div style="border:1px solid {CLR_BORDER};border-radius:8px;'
                f'overflow:hidden;">{m._repr_html_()}</div>', height=450)
    except ImportError:
        st.info("Install `folium` for map visualisation.")
    except Exception as exc:
        logger.warning("Map render error: %s", exc)
        st.warning("Could not render map.")

def _render_data_overview(elev, soil, weather, ic, eq_count):
    ps = _parse_soil(soil)
    cur = weather.get("current", {}) if isinstance(weather, dict) else {}
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Elevation", f"{elev.get('center', 0):.0f} m")
        st.metric("Slope", f"{elev.get('slope_deg', 0):.1f} deg")
    with c2:
        t = cur.get("temperature_2m", "N/A"); w = cur.get("wind_speed_10m", "N/A")
        st.metric("Temperature", f"{t} C" if t != "N/A" else "N/A")
        st.metric("Wind", f"{w} km/h" if w != "N/A" else "N/A")
    with c3:
        cl = ps.get("clay"); so = ps.get("soc")
        st.metric("Clay", f"{cl:.1f} %" if cl is not None else "N/A")
        st.metric("Organic C", f"{so:.1f} g/kg" if so is not None else "N/A")
    with c4:
        st.metric("Buildings", f"{ic.get('buildings', 0)}")
        st.metric("Earthquakes (2yr)", f"{eq_count}")

def _render_radar_chart(results):
    if len(results) < 2:
        return
    dims = ["Terrain Flatness", "Water Access", "Road Access",
            "Climate Comfort", "Seismic Safety"]
    fig = go.Figure()
    for r in results[:4]:
        fm = {f["name"]: f["score"] for f in r["factors"]}
        vals = [fm.get(d, 50) for d in dims]
        vals.append(vals[0])
        fig.add_trace(go.Scatterpolar(
            r=vals, theta=dims + [dims[0]], fill="toself",
            name=f"{r['icon']} {r['name']} ({r['score']})",
            line=dict(color=r["color"]), opacity=0.6))
    fig.update_layout(
        polar=dict(bgcolor=CLR_SURFACE,
                   radialaxis=dict(visible=True, range=[0, 100],
                                   gridcolor=CLR_BORDER, color=CLR_TEXT_SEC),
                   angularaxis=dict(color=CLR_TEXT)),
        paper_bgcolor=CLR_BG,
        title=dict(text="Scenario Comparison (Key Dimensions)",
                   font=dict(color=CLR_TEXT, size=16)),
        legend=dict(font=dict(color=CLR_TEXT, size=11)),
        height=420, margin=dict(l=60, r=60, t=50, b=40))
    st.plotly_chart(fig, use_container_width=True, key="szone_radar")

# ── Main Entry Point ─────────────────────────────────────────────────────────
def render_smart_zoning_tab():
    """Single entry point for the Smart Zoning & Land Use AI tab."""
    st.markdown("## \U0001f3d7\ufe0f Smart Zoning & Land Use AI")
    st.caption("AI-powered optimal land use recommendation based on terrain, "
               "soil, climate, and infrastructure analysis")
    st.markdown(f"""<style>
        div[data-testid="stExpander"] {{
            background-color: {CLR_SURFACE}; border: 1px solid {CLR_BORDER};
            border-radius: 8px; margin-bottom: 8px;
        }}
    </style>""", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f",
                          key="szone_lat", min_value=-90.0, max_value=90.0)
    lon = c2.number_input("Longitude", value=12.5, format="%.4f",
                          key="szone_lon", min_value=-180.0, max_value=180.0)
    col_r, _ = st.columns([1, 2])
    radius = col_r.slider("Analysis radius (m)", 1000, 10000, 3000, 500,
                           key="szone_radius")

    if st.button("\U0001f3d7\ufe0f Analyse Zoning", key="szone_btn",
                 use_container_width=True):
        with st.spinner("Gathering geospatial data and scoring land-use scenarios..."):
            prog = st.progress(0, text="Fetching elevation data...")
            elev = _fetch_elevation(lat, lon)
            prog.progress(20, text="Fetching soil composition...")
            soil = _fetch_soil(lat, lon)
            prog.progress(40, text="Fetching weather data...")
            weather = _fetch_weather(lat, lon)
            prog.progress(60, text="Fetching infrastructure...")
            infra = _fetch_infrastructure(lat, lon, radius=radius)
            prog.progress(80, text="Fetching seismic data...")
            eq_data = _fetch_earthquakes(lat, lon)
            prog.progress(90, text="Computing suitability scores...")
            results = _score_all_scenarios(elev, soil, weather, infra, eq_data)
            infra_counts = _analyse_infrastructure(infra)
            eq_count = len(eq_data.get("features", []))
            prog.progress(100, text="Analysis complete!")
            prog.empty()

        # ── Display Results ──────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Top Recommendation")
        if results:
            _render_badge(results[0])

        st.markdown("### Location Data Overview")
        _render_data_overview(elev, soil, weather, infra_counts, eq_count)
        st.markdown("---")

        st.markdown("### Suitability Ranking")
        _render_bar_chart(results)

        st.markdown("### Multi-Scenario Comparison")
        _render_radar_chart(results)
        st.markdown("---")

        st.markdown("### Factor Breakdown by Scenario")
        for idx, r in enumerate(results):
            _render_factor_breakdown(r, idx)
        st.markdown("---")

        st.markdown("### Zoning Map")
        _render_map(lat, lon, results)
        st.markdown("---")

        _render_summary_table(results)

        st.markdown(f"""
        <div style="background:{CLR_SURFACE};border:1px solid {CLR_BORDER};
                    border-radius:8px;padding:16px;margin-top:16px;">
            <div style="color:{CLR_TEXT};font-weight:600;margin-bottom:8px;">
                How to read these results</div>
            <div style="color:{CLR_TEXT_SEC};font-size:13px;line-height:1.6;">
                Each scenario is scored 0-100 based on weighted environmental
                factors. Above 80 = <b>excellent</b>, 60-80 = <b>good</b>,
                40-60 = <b>moderate</b>, below 40 = <b>poorly suited</b>.
                Analysis uses a {radius} m radius. All data from free,
                open-access geospatial APIs; not professional planning advice.
            </div>
        </div>""", unsafe_allow_html=True)
