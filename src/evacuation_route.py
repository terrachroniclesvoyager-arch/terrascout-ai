"""
Evacuation Route Planning module for TerraScout AI.
Identifies escape routes, safe zones, and evacuation infrastructure across
7 dimensions: Road Network, Safe Zones, Bridges & Chokepoints, Terrain Escape,
Emergency Services, Transport Options, Hazard Zones.
Supports scenario selection: Flood, Earthquake, Wildfire, Industrial Accident.
Uses free APIs: Overpass, Open Topo Data, USGS, Open-Meteo (no keys required).
"""

import math
import logging
from html import escape

import streamlit as st
import requests
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
from streamlit.components.v1 import html as st_html

logger = logging.getLogger(__name__)

# =============================================================================
# THEME CONSTANTS
# =============================================================================
CLR_BG, CLR_CARD, CLR_SURFACE = "#1a1a2e", "#16213e", "#0f3460"
CLR_BORDER, CLR_TEXT, CLR_TEXT_SEC = "#2a3550", "#e8ecf4", "#8b97b0"
CLR_ACCENT = "#f59e0b"
CLR_GREEN, CLR_YELLOW, CLR_RED = "#22c55e", "#fbbf24", "#ef4444"
CLR_ORANGE, CLR_BLUE, CLR_PURPLE, CLR_CYAN = "#f97316", "#3b82f6", "#8b5cf6", "#06b6d4"

READINESS_LEVELS = {
    "Critical": ((0, 20), CLR_RED, "Immediate planning required"),
    "Poor": ((20, 40), CLR_ORANGE, "Significant gaps in evacuation readiness"),
    "Moderate": ((40, 60), CLR_YELLOW, "Partial coverage, improvements needed"),
    "Good": ((60, 80), CLR_BLUE, "Adequate evacuation infrastructure"),
    "Excellent": ((80, 101), CLR_GREEN, "Strong evacuation readiness"),
}

SCENARIO_WEIGHTS = {
    "Flood": {"Road Network": .18, "Safe Zones": .12, "Bridges & Chokepoints": .20,
              "Terrain Escape": .20, "Emergency Services": .10, "Transport Options": .08,
              "Hazard Zones": .12},
    "Earthquake": {"Road Network": .20, "Safe Zones": .18, "Bridges & Chokepoints": .15,
                   "Terrain Escape": .08, "Emergency Services": .15, "Transport Options": .10,
                   "Hazard Zones": .14},
    "Wildfire": {"Road Network": .22, "Safe Zones": .15, "Bridges & Chokepoints": .08,
                 "Terrain Escape": .15, "Emergency Services": .12, "Transport Options": .12,
                 "Hazard Zones": .16},
    "Industrial Accident": {"Road Network": .16, "Safe Zones": .14, "Bridges & Chokepoints": .10,
                            "Terrain Escape": .10, "Emergency Services": .20,
                            "Transport Options": .14, "Hazard Zones": .16},
}

DIMENSION_META = {
    "Road Network": "#6366f1", "Safe Zones": CLR_GREEN,
    "Bridges & Chokepoints": CLR_ORANGE, "Terrain Escape": "#a0785a",
    "Emergency Services": CLR_RED, "Transport Options": CLR_CYAN,
    "Hazard Zones": CLR_PURPLE,
}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# =============================================================================
# HELPERS
# =============================================================================
def _clamp(v, lo=0.0, hi=10.0):
    return max(lo, min(hi, float(v)))

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _el_pos(el):
    return (el.get("lat") or (el.get("center") or {}).get("lat"),
            el.get("lon") or (el.get("center") or {}).get("lon"))

def _nearest_dist(lat, lon, elements):
    best = None
    for el in (elements if isinstance(elements, list) else []):
        elat, elon = _el_pos(el)
        if elat is not None and elon is not None:
            d = _haversine(lat, lon, elat, elon)
            if best is None or d < best:
                best = d
    return best

def _classify_readiness(score):
    for name, (rng, color, desc) in READINESS_LEVELS.items():
        if rng[0] <= score < rng[1]:
            return name, color, desc
    return "Critical", CLR_RED, "Immediate planning required"

def _score_color(s):
    return CLR_GREEN if s >= 7 else CLR_YELLOW if s >= 4 else CLR_RED

def _dim_card_html(name, score, detail, color):
    sc = _score_color(score)
    return (f'<div style="background:{CLR_CARD};border-radius:10px;padding:14px 12px;'
            f'border:1px solid {color}44;margin-bottom:8px;min-height:130px;">'
            f'<div style="font-size:12px;color:{color};font-weight:600;'
            f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">'
            f'{escape(name)}</div>'
            f'<div style="font-size:28px;font-weight:800;color:{sc};">'
            f'{score:.1f}<span style="font-size:12px;color:{CLR_TEXT_SEC};">/10</span></div>'
            f'<div style="font-size:11px;color:{CLR_TEXT_SEC};margin-top:4px;'
            f'line-height:1.35;">{escape(detail[:120])}</div></div>')

def _overpass(query):
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Overpass fetch error: %s", exc)
        return {"elements": []}

def _els(data):
    els = (data or {}).get("elements", [])
    return els if isinstance(els, list) else []

def _by_tag(elements, key, values):
    if isinstance(values, str):
        values = (values,)
    return [e for e in elements if (e.get("tags") or {}).get(key) in values]


# =============================================================================
# DATA FETCHING -- @st.cache_data(ttl=900), timeout=10, try/except
# =============================================================================
@st.cache_data(ttl=900)
def _fetch_road_network(lat, lon, radius=8000):
    return _overpass(f"""[out:json][timeout:25];(
      way["highway"="motorway"](around:{radius},{lat},{lon});
      way["highway"="trunk"](around:{radius},{lat},{lon});
      way["highway"="primary"](around:{radius},{lat},{lon});
      way["highway"="secondary"](around:{radius},{lat},{lon});
      way["highway"="tertiary"](around:{radius},{lat},{lon});
    );out center body;""")

@st.cache_data(ttl=900)
def _fetch_safe_zones(lat, lon, radius=10000):
    return _overpass(f"""[out:json][timeout:25];(
      way["leisure"="park"](around:{radius},{lat},{lon});
      way["leisure"="sports_centre"](around:{radius},{lat},{lon});
      way["leisure"="pitch"](around:{radius},{lat},{lon});
      way["leisure"="stadium"](around:{radius},{lat},{lon});
      node["amenity"="school"](around:{radius},{lat},{lon});
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      node["amenity"="place_of_worship"](around:{radius},{lat},{lon});
      way["landuse"="recreation_ground"](around:{radius},{lat},{lon});
      way["landuse"="grass"](around:{radius},{lat},{lon});
      node["amenity"="community_centre"](around:{radius},{lat},{lon});
    );out center body;""")

@st.cache_data(ttl=900)
def _fetch_bridges_chokepoints(lat, lon, radius=8000):
    return _overpass(f"""[out:json][timeout:25];(
      way["bridge"="yes"](around:{radius},{lat},{lon});
      way["tunnel"="yes"](around:{radius},{lat},{lon});
      node["barrier"](around:{radius},{lat},{lon});
      way["highway"="ford"](around:{radius},{lat},{lon});
      node["ford"="yes"](around:{radius},{lat},{lon});
    );out center body;""")

@st.cache_data(ttl=900)
def _fetch_elevation_grid(lat, lon):
    try:
        pts = [f"{lat + (i - 3) * .005:.5f},{lon + (j - 3) * .005:.5f}"
               for i in range(7) for j in range(7)]
        resp = requests.get("https://api.opentopodata.org/v1/srtm30m",
                            params={"locations": "|".join(pts)}, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        elevs = [float(r.get("elevation") or 0) for r in results]
        mid = len(elevs) // 2
        return {"center": elevs[mid] if elevs else 0.0, "grid": elevs}
    except Exception as exc:
        logger.warning("Elevation fetch error: %s", exc)
        return {"center": 0.0, "grid": []}

@st.cache_data(ttl=900)
def _fetch_emergency_services(lat, lon, radius=10000):
    return _overpass(f"""[out:json][timeout:25];(
      node["amenity"="fire_station"](around:{radius},{lat},{lon});
      way["amenity"="fire_station"](around:{radius},{lat},{lon});
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      way["amenity"="hospital"](around:{radius},{lat},{lon});
      node["amenity"="police"](around:{radius},{lat},{lon});
      way["amenity"="police"](around:{radius},{lat},{lon});
      node["amenity"="clinic"](around:{radius},{lat},{lon});
      node["emergency"="ambulance_station"](around:{radius},{lat},{lon});
    );out center body;""")

@st.cache_data(ttl=900)
def _fetch_transport_options(lat, lon, radius=10000):
    return _overpass(f"""[out:json][timeout:25];(
      node["highway"="bus_stop"](around:{radius},{lat},{lon});
      node["railway"="station"](around:{radius},{lat},{lon});
      node["railway"="halt"](around:{radius},{lat},{lon});
      node["aeroway"="helipad"](around:{radius},{lat},{lon});
      way["aeroway"="aerodrome"](around:{radius},{lat},{lon});
      node["aeroway"="aerodrome"](around:{radius},{lat},{lon});
      node["amenity"="ferry_terminal"](around:{radius},{lat},{lon});
    );out center body;""")

@st.cache_data(ttl=900)
def _fetch_earthquakes(lat, lon, radius_km=150):
    try:
        resp = requests.get("https://earthquake.usgs.gov/fdsnws/event/1/query",
                            params={"format": "geojson", "latitude": lat, "longitude": lon,
                                    "maxradiuskm": radius_km, "limit": 20}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("USGS earthquake fetch error: %s", exc)
        return {"features": []}

@st.cache_data(ttl=900)
def _fetch_weather(lat, lon):
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,precipitation",
            "daily": "precipitation_sum,wind_speed_10m_max",
            "timezone": "auto"}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Weather fetch error: %s", exc)
        return {}

@st.cache_data(ttl=900)
def _fetch_industrial_hazards(lat, lon, radius=10000):
    return _overpass(f"""[out:json][timeout:25];(
      way["landuse"="industrial"](around:{radius},{lat},{lon});
      node["man_made"="storage_tank"](around:{radius},{lat},{lon});
      way["man_made"="works"](around:{radius},{lat},{lon});
      node["industrial"="chemical"](around:{radius},{lat},{lon});
      way["power"="plant"](around:{radius},{lat},{lon});
    );out center body;""")

@st.cache_data(ttl=900)
def _fetch_water_features(lat, lon, radius=8000):
    return _overpass(f"""[out:json][timeout:25];(
      way["waterway"="river"](around:{radius},{lat},{lon});
      way["waterway"="stream"](around:{radius},{lat},{lon});
      way["natural"="water"](around:{radius},{lat},{lon});
      relation["natural"="water"](around:{radius},{lat},{lon});
    );out center body;""")

# =============================================================================
# SCORING ENGINE
# =============================================================================
@st.cache_data(ttl=900)
def _compute_evacuation_scores(lat, lon, scenario):
    """Compute all 7 evacuation dimension scores (each 0-10)."""
    roads = _els(_fetch_road_network(lat, lon))
    safe_zones = _els(_fetch_safe_zones(lat, lon))
    bridge_raw = _els(_fetch_bridges_chokepoints(lat, lon))
    elev_data = _fetch_elevation_grid(lat, lon)
    emergency = _els(_fetch_emergency_services(lat, lon))
    transport = _els(_fetch_transport_options(lat, lon))
    q_feats = (_fetch_earthquakes(lat, lon) or {}).get("features", [])
    q_list = q_feats if isinstance(q_feats, list) else []
    weather = _fetch_weather(lat, lon) or {}
    industrial = _els(_fetch_industrial_hazards(lat, lon))
    water = _els(_fetch_water_features(lat, lon))

    scores, details, raw = {}, {}, {}

    # -- DIM 1: Road Network ---------------------------------------------------
    motorways = _by_tag(roads, "highway", "motorway")
    trunks = _by_tag(roads, "highway", "trunk")
    primaries = _by_tag(roads, "highway", "primary")
    secondaries = _by_tag(roads, "highway", "secondary")
    if not roads:
        rs, rd = 1.0, "No major roads within 8 km; evacuation very difficult"
    else:
        rs = min(6.0, 1.5 + len(roads) * 0.08)
        rs = _clamp(rs + (len(motorways) > 0) * 1.5 + (len(trunks) > 0) * 1.2
                    + (len(primaries) > 0) * 1.0 + (len(secondaries) > 0) * 0.5)
        parts = [(n, l) for n, l in [("motorways", motorways), ("trunk", trunks),
                  ("primary", primaries), ("secondary", secondaries)] if l]
        rd = ", ".join(f"{len(l)} {n}" for n, l in parts) + f" ({len(roads)} total)"
    if scenario == "Earthquake":
        rs, rd = _clamp(rs - 1.0), rd + "; road damage risk"
    scores["Road Network"] = round(_clamp(rs), 1)
    details["Road Network"] = rd
    raw["roads"] = roads

    # -- DIM 2: Safe Zones -----------------------------------------------------
    parks = _by_tag(safe_zones, "leisure", ("park", "sports_centre", "pitch", "stadium"))
    schools = _by_tag(safe_zones, "amenity", "school")
    hosp_sz = _by_tag(safe_zones, "amenity", "hospital")
    churches = _by_tag(safe_zones, "amenity", "place_of_worship")
    community = _by_tag(safe_zones, "amenity", "community_centre")
    open_land = _by_tag(safe_zones, "landuse", ("recreation_ground", "grass"))
    nearest_sz = _nearest_dist(lat, lon, safe_zones)
    if not safe_zones:
        szs, szd = 1.5, "No designated safe zones within 10 km"
    else:
        szs = min(6.5, 2.0 + len(safe_zones) * 0.15)
        szs = _clamp(szs + sum(1 for g in [parks, schools, hosp_sz, churches,
                                            community, open_land] if g) * 0.5)
        if nearest_sz and nearest_sz < 1.0: szs = _clamp(szs + 1.5)
        elif nearest_sz and nearest_sz < 3.0: szs = _clamp(szs + 0.8)
        cats = [(n, l) for n, l in [("parks/fields", parks), ("schools", schools),
                 ("hospitals", hosp_sz), ("worship", churches), ("community", community),
                 ("open land", open_land)] if l]
        szd = ", ".join(f"{len(l)} {n}" for n, l in cats)
        if nearest_sz: szd += f"; nearest {nearest_sz:.1f} km"
    if scenario == "Wildfire" and parks:
        szs, szd = _clamp(szs - 0.5), szd + "; green areas risky in wildfire"
    scores["Safe Zones"] = round(_clamp(szs), 1)
    details["Safe Zones"] = szd
    raw["safe_zones"] = safe_zones

    # -- DIM 3: Bridges & Chokepoints ------------------------------------------
    bridges = _by_tag(bridge_raw, "bridge", "yes")
    tunnels = _by_tag(bridge_raw, "tunnel", "yes")
    fords = [e for e in bridge_raw if (e.get("tags") or {}).get("ford") == "yes"
             or (e.get("tags") or {}).get("highway") == "ford"]
    barriers = [e for e in bridge_raw if "barrier" in (e.get("tags") or {})]
    bc = len(bridges)
    if bc == 0 and not tunnels:
        bs, bd = 8.0, "No bridges/tunnels (no chokepoint failure risk)"
    else:
        bs = _clamp(7.0 - bc * 0.3 - len(tunnels) * 0.4)
        parts = []
        if bridges: parts.append(f"{bc} bridges")
        if tunnels: parts.append(f"{len(tunnels)} tunnels")
        if fords: parts.append(f"{len(fords)} fords")
        if barriers: parts.append(f"{len(barriers)} barriers")
        bd = "; ".join(parts)
    if scenario == "Flood":
        bs, bd = _clamp(bs - bc * 0.5), bd + "; bridges high-risk in flood"
    elif scenario == "Earthquake":
        bs = _clamp(bs - bc * 0.6 - len(tunnels) * 0.5)
        bd += "; structural collapse risk"
    scores["Bridges & Chokepoints"] = round(_clamp(bs), 1)
    details["Bridges & Chokepoints"] = bd
    raw["bridges"], raw["tunnels"] = bridges, tunnels

    # -- DIM 4: Terrain Escape -------------------------------------------------
    grid_elevs = elev_data.get("grid", [])
    center_elev = elev_data.get("center", 0.0)
    valid = [e for e in grid_elevs if e is not None and e > -500]
    if len(valid) >= 4:
        elev_range = max(valid) - min(valid)
        uphill = sum(1 for e in valid if e > center_elev + 5)
        flat = sum(1 for e in valid if abs(e - center_elev) <= 5)
        if scenario == "Flood":
            if center_elev < 5: ts, td = 2.0, f"Very low ({center_elev:.0f}m), severe flood risk"
            elif center_elev < 20: ts, td = 4.0, f"Low ({center_elev:.0f}m), flood-prone"
            elif center_elev < 100: ts, td = 7.0, f"Moderate ({center_elev:.0f}m), some safety"
            else: ts, td = 9.0, f"High ground ({center_elev:.0f}m), good flood escape"
            if uphill > 5: ts, td = _clamp(ts + 1), td + f"; {uphill} uphill routes"
        else:
            if flat > len(valid) * 0.6: ts, td = 8.0, f"Flat ({center_elev:.0f}m), easy corridors"
            elif elev_range < 50: ts, td = 7.0, f"Gentle (range {elev_range:.0f}m), good mobility"
            elif elev_range < 200: ts, td = 5.0, f"Hilly ({elev_range:.0f}m range), limited"
            else: ts, td = 3.0, f"Mountainous ({elev_range:.0f}m), difficult"
    else:
        ts, td, elev_range, uphill, flat = 5.0, "Elevation data limited", 0, 0, 0
    scores["Terrain Escape"] = round(_clamp(ts), 1)
    details["Terrain Escape"] = td
    raw["elevation"] = {"center": center_elev, "range": elev_range}

    # -- DIM 5: Emergency Services ---------------------------------------------
    fire = _by_tag(emergency, "amenity", "fire_station")
    hosp = _by_tag(emergency, "amenity", "hospital")
    police = _by_tag(emergency, "amenity", "police")
    clinics = _by_tag(emergency, "amenity", "clinic")
    ambul = [e for e in emergency if (e.get("tags") or {}).get("emergency") == "ambulance_station"]
    nearest_em = _nearest_dist(lat, lon, emergency)
    if not emergency:
        es, ed = 1.0, "No emergency services within 10 km"
    else:
        es = min(6.0, 2.0 + len(emergency) * 0.4)
        es = _clamp(es + sum(1 for g in [fire, hosp, police, clinics, ambul] if g) * 0.8)
        if nearest_em and nearest_em < 2.0: es = _clamp(es + 1.5)
        elif nearest_em and nearest_em < 5.0: es = _clamp(es + 0.8)
        cats = [(n, l) for n, l in [("fire stations", fire), ("hospitals", hosp),
                 ("police", police), ("clinics", clinics), ("ambulance", ambul)] if l]
        ed = ", ".join(f"{len(l)} {n}" for n, l in cats)
        if nearest_em: ed += f"; nearest {nearest_em:.1f} km"
    scores["Emergency Services"] = round(_clamp(es), 1)
    details["Emergency Services"] = ed
    raw["emergency"] = emergency

    # -- DIM 6: Transport Options ----------------------------------------------
    buses = _by_tag(transport, "highway", "bus_stop")
    trains = _by_tag(transport, "railway", ("station", "halt"))
    heli = _by_tag(transport, "aeroway", "helipad")
    air = _by_tag(transport, "aeroway", "aerodrome")
    ferry = _by_tag(transport, "amenity", "ferry_terminal")
    nearest_tr = _nearest_dist(lat, lon, transport)
    if not transport:
        trs, trd = 1.5, "No mass transport within 10 km"
    else:
        trs = min(5.5, 1.5 + len(transport) * 0.08)
        trs = _clamp(trs + (len(trains) > 0) * 1.5 + (len(air) > 0) * 2.0
                     + (len(heli) > 0) * 1.5 + (len(buses) > 0) * 0.8
                     + (len(ferry) > 0) * 1.0)
        if nearest_tr and nearest_tr < 1.0: trs = _clamp(trs + 1.0)
        cats = [(n, l) for n, l in [("bus stops", buses), ("train stations", trains),
                 ("helipads", heli), ("airports", air), ("ferries", ferry)] if l]
        trd = ", ".join(f"{len(l)} {n}" for n, l in cats)
        if nearest_tr: trd += f"; nearest {nearest_tr:.1f} km"
    if scenario == "Flood" and ferry:
        trs, trd = _clamp(trs - 0.5), trd + "; ferries unreliable in flood"
    scores["Transport Options"] = round(_clamp(trs), 1)
    details["Transport Options"] = trd
    raw["transport"] = transport

    # -- DIM 7: Hazard Zones (USGS + Open-Meteo + Overpass) --------------------
    mags = [float((f.get("properties") or {}).get("mag", 0))
            for f in q_list if (f.get("properties") or {}).get("mag") is not None]
    max_mag = max(mags) if mags else 0.0
    daily = weather.get("daily", {})
    tot_prec = sum(v for v in (daily.get("precipitation_sum") or []) if v is not None)
    wind_vals = [v for v in (daily.get("wind_speed_10m_max") or []) if v is not None]
    max_wind = max(wind_vals) if wind_vals else 0
    nearest_ind = _nearest_dist(lat, lon, industrial)
    nearest_wat = _nearest_dist(lat, lon, water)

    hz, hp = 8.0, []
    if max_mag >= 5.0: hz -= 3.0; hp.append(f"seismic M{max_mag:.1f}")
    elif max_mag >= 3.0: hz -= 1.5; hp.append(f"seismic M{max_mag:.1f}")
    elif q_list: hz -= 0.5; hp.append(f"{len(q_list)} minor quakes")
    if nearest_wat and nearest_wat < 1.0 and center_elev < 20:
        hz -= 2.0; hp.append(f"flood plain ({nearest_wat:.1f}km to water, {center_elev:.0f}m)")
    elif nearest_wat and nearest_wat < 2.0 and center_elev < 50:
        hz -= 1.0; hp.append(f"near water ({nearest_wat:.1f}km)")
    if nearest_ind and nearest_ind < 2.0: hz -= 2.0; hp.append(f"industrial {nearest_ind:.1f}km")
    elif nearest_ind and nearest_ind < 5.0: hz -= 1.0; hp.append(f"industrial {nearest_ind:.1f}km")
    if tot_prec > 80: hz -= 1.0; hp.append(f"heavy rain {tot_prec:.0f}mm/7d")
    if max_wind > 50: hz -= 1.0; hp.append(f"wind {max_wind:.0f}km/h")
    if scenario == "Industrial Accident" and industrial:
        hz -= 1.5; hp.append(f"{len(industrial)} industrial sites nearby")
    scores["Hazard Zones"] = round(_clamp(hz), 1)
    details["Hazard Zones"] = "; ".join(hp) if hp else "No significant hazards detected"
    raw["hazards"] = {"quakes": len(q_list), "max_mag": max_mag,
                      "industrial": len(industrial), "water": len(water)}
    # -- Overall --
    w = SCENARIO_WEIGHTS.get(scenario, SCENARIO_WEIGHTS["Flood"])
    overall = _clamp(sum(scores[d] * w.get(d, .1) for d in scores) * 10, 0, 100)
    return {"scores": scores, "details": details, "raw": raw,
            "overall": round(overall, 1), "scenario": scenario, "lat": lat, "lon": lon}

# =============================================================================
# MAP BUILDER
# =============================================================================
def _build_evacuation_map(results):
    lat, lon, raw, scenario = results["lat"], results["lon"], results["raw"], results["scenario"]
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB positron")
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satellite", overlay=False).add_to(m)
    folium.Marker([lat, lon], popup=f"<b>Origin</b><br>{lat:.4f}, {lon:.4f}",
                  tooltip="Your Location",
                  icon=folium.Icon(color="red", icon="home", prefix="fa")).add_to(m)

    # Safe Zone markers
    sz_grp = folium.FeatureGroup(name="Safe Zones")
    for el in raw.get("safe_zones", [])[:30]:
        elat, elon = _el_pos(el)
        if elat is not None and elon is not None:
            nm = (el.get("tags") or {}).get("name", "Safe Zone")
            d = _haversine(lat, lon, elat, elon)
            folium.CircleMarker([elat, elon], radius=7, color=CLR_GREEN, fill=True,
                                fill_color=CLR_GREEN, fill_opacity=0.7,
                                popup=f"<b>{escape(str(nm))}</b><br>{d:.1f} km",
                                tooltip=f"Safe: {escape(str(nm))}").add_to(sz_grp)
    sz_grp.add_to(m)

    # Emergency Services markers
    em_grp = folium.FeatureGroup(name="Emergency Services")
    ic_map = {"fire_station": "fire-extinguisher", "hospital": "hospital",
              "police": "shield", "clinic": "medkit"}
    for el in raw.get("emergency", [])[:20]:
        elat, elon = _el_pos(el)
        if elat is not None and elon is not None:
            tags = el.get("tags") or {}
            am = tags.get("amenity", tags.get("emergency", "service"))
            nm = tags.get("name", am)
            folium.Marker([elat, elon], popup=f"<b>{escape(str(nm))}</b><br>{am}",
                          tooltip=f"Emergency: {escape(str(nm))}",
                          icon=folium.Icon(color="blue", icon=ic_map.get(am, "plus"),
                                           prefix="fa")).add_to(em_grp)
    em_grp.add_to(m)

    # Transport markers
    tr_grp = folium.FeatureGroup(name="Transport")
    for el in raw.get("transport", [])[:25]:
        elat, elon = _el_pos(el)
        if elat is not None and elon is not None:
            nm = (el.get("tags") or {}).get("name", "Transport")
            folium.CircleMarker([elat, elon], radius=5, color=CLR_CYAN, fill=True,
                                fill_color=CLR_CYAN, fill_opacity=0.6,
                                tooltip=f"Transport: {escape(str(nm))}").add_to(tr_grp)
    tr_grp.add_to(m)

    # Evacuation route lines (origin to nearest safe zones)
    sorted_sz = sorted(
        [(d, elat, elon) for el in raw.get("safe_zones", [])
         for elat, elon in [_el_pos(el)] if elat is not None and elon is not None
         for d in [_haversine(lat, lon, elat, elon)]],
        key=lambda x: x[0])
    rt_grp = folium.FeatureGroup(name="Evacuation Routes")
    for idx, (d, elat, elon) in enumerate(sorted_sz[:5]):
        clr = CLR_GREEN if idx == 0 else CLR_YELLOW if idx < 3 else CLR_ORANGE
        lbl = "Primary" if idx == 0 else "Secondary" if idx < 3 else "Tertiary"
        folium.PolyLine([[lat, lon], [elat, elon]], color=clr, weight=4, opacity=0.8,
                        dash_array="10 5" if idx > 0 else None,
                        tooltip=f"{lbl} Route ({d:.1f} km)").add_to(rt_grp)
    rt_grp.add_to(m)

    # Chokepoint markers
    ch_grp = folium.FeatureGroup(name="Chokepoints")
    for el in raw.get("bridges", [])[:15]:
        elat, elon = _el_pos(el)
        if elat is not None and elon is not None:
            risk = "HIGH" if scenario in ("Flood", "Earthquake") else "MODERATE"
            folium.CircleMarker([elat, elon], radius=6, color=CLR_ORANGE, fill=True,
                                fill_color=CLR_ORANGE, fill_opacity=0.7,
                                tooltip=f"Bridge ({risk} risk)").add_to(ch_grp)
    for el in raw.get("tunnels", [])[:10]:
        elat, elon = _el_pos(el)
        if elat is not None and elon is not None:
            folium.CircleMarker([elat, elon], radius=6, color=CLR_RED, fill=True,
                                fill_color=CLR_RED, fill_opacity=0.6,
                                tooltip="Tunnel (blockage risk)").add_to(ch_grp)
    ch_grp.add_to(m)

    # Hazard overlay circle
    if scenario == "Industrial Accident":
        folium.Circle([lat, lon], radius=3000, color=CLR_RED, fill=True,
                      fill_color=CLR_RED, fill_opacity=0.08,
                      tooltip="3 km hazard zone").add_to(m)
    elif scenario == "Flood":
        folium.Circle([lat, lon], radius=5000, color=CLR_BLUE, fill=True,
                      fill_color=CLR_BLUE, fill_opacity=0.06,
                      tooltip="5 km flood zone").add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# =============================================================================
# MAIN RENDER
# =============================================================================
def render_evacuation_route_tab():
    """Entry point: render the Evacuation Route Planning tab."""
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{CLR_CARD},{CLR_SURFACE});'
        f'border-radius:12px;padding:18px 22px;margin-bottom:16px;'
        f'border:1px solid {CLR_BORDER};">'
        f'<h4 style="margin:0;color:{CLR_GREEN};">Evacuation Route Planning</h4>'
        f'<p style="margin:4px 0 0;color:{CLR_TEXT_SEC};font-size:13px;">'
        f'Identify escape routes, safe zones, and evacuation infrastructure. '
        f'Evaluate readiness across 7 dimensions for multiple disaster scenarios.</p>'
        f'</div>', unsafe_allow_html=True)

    # -- Controls --
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        evac_lat = st.number_input("Latitude", -90.0, 90.0, 41.9028, step=0.01,
                                   format="%.4f", key="evac_lat")
    with c2:
        evac_lon = st.number_input("Longitude", -180.0, 180.0, 12.4964, step=0.01,
                                   format="%.4f", key="evac_lon")
    with c3:
        evac_scenario = st.selectbox("Disaster Scenario",
                                     list(SCENARIO_WEIGHTS.keys()), key="evac_scenario")

    if st.button("Analyze Evacuation Readiness", type="primary",
                 use_container_width=True, key="evac_run"):
        with st.spinner("Analyzing evacuation routes and safe zones..."):
            st.session_state["evac_results"] = _compute_evacuation_scores(
                evac_lat, evac_lon, evac_scenario)

    if "evac_results" not in st.session_state:
        st.info("Enter coordinates and select a disaster scenario, then click Analyze.")
        return

    res = st.session_state["evac_results"]
    scores, details, overall = res["scores"], res["details"], res["overall"]
    scenario, raw = res["scenario"], res["raw"]

    # -- Readiness Score Header --
    label, color, desc = _classify_readiness(overall)
    st.markdown(
        f'<div style="background:{CLR_CARD};border-radius:12px;padding:20px;'
        f'text-align:center;border:2px solid {color};margin-bottom:16px;">'
        f'<div style="font-size:14px;color:{CLR_TEXT_SEC};text-transform:uppercase;'
        f'letter-spacing:1px;">Evacuation Readiness ({scenario})</div>'
        f'<div style="font-size:52px;font-weight:900;color:{color};margin:8px 0;">'
        f'{overall:.0f}<span style="font-size:20px;color:{CLR_TEXT_SEC};">/100</span></div>'
        f'<div style="font-size:16px;color:{color};font-weight:700;">{label}</div>'
        f'<div style="font-size:12px;color:{CLR_TEXT_SEC};margin-top:4px;">{desc}</div>'
        f'</div>', unsafe_allow_html=True)

    # -- Key Metrics --
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Road Segments", len(raw.get("roads", [])))
    with m2: st.metric("Safe Zones", len(raw.get("safe_zones", [])))
    with m3: st.metric("Emergency Services", len(raw.get("emergency", [])))
    with m4: st.metric("Transport Nodes", len(raw.get("transport", [])))
    st.markdown("---")

    # -- Radar Chart + Weights --
    col_r, col_w = st.columns([3, 2])
    with col_r:
        st.markdown(f"#### Dimension Radar -- {scenario}")
        dims = list(scores.keys())
        vals = [scores[d] for d in dims] + [scores[dims[0]]]
        fig = go.Figure(go.Scatterpolar(
            r=vals, theta=dims + [dims[0]], fill="toself",
            fillcolor="rgba(34,197,94,0.15)", line=dict(color=CLR_GREEN, width=2)))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10], gridcolor="#334155"),
                       angularaxis=dict(gridcolor="#334155"), bgcolor=CLR_BG),
            showlegend=False, height=380, margin=dict(l=60, r=60, t=30, b=30),
            paper_bgcolor=CLR_BG, font=dict(color=CLR_TEXT))
        st.plotly_chart(fig, use_container_width=True, key="evac_radar")
    with col_w:
        st.markdown(f"#### Scenario Weights -- {scenario}")
        sw = SCENARIO_WEIGHTS[scenario]
        for dim, sc in scores.items():
            bc = _score_color(sc)
            st.markdown(
                f'<div style="margin-bottom:6px;">'
                f'<span style="color:{CLR_TEXT};font-size:12px;">{dim}</span>'
                f'<span style="float:right;color:{bc};font-weight:700;">{sc:.1f}/10</span>'
                f'<div style="background:{CLR_BORDER};border-radius:4px;height:8px;'
                f'margin-top:2px;"><div style="background:{bc};width:{sc*10:.0f}%;'
                f'height:100%;border-radius:4px;"></div></div>'
                f'<span style="color:{CLR_TEXT_SEC};font-size:10px;">'
                f'Weight: {sw.get(dim,0)*100:.0f}%</span></div>', unsafe_allow_html=True)
    st.markdown("---")

    # -- Dimension Cards --
    st.markdown("#### Dimension Analysis")
    dim_list = list(DIMENSION_META.keys())
    for row_dims in [dim_list[:4], dim_list[4:]]:
        cols = st.columns(len(row_dims))
        for i, d in enumerate(row_dims):
            with cols[i]:
                st.markdown(_dim_card_html(d, scores.get(d, 0), details.get(d, ""),
                                           DIMENSION_META[d]), unsafe_allow_html=True)
    st.markdown("---")

    # -- Evacuation Map --
    st.markdown("#### Evacuation Route Map")
    st.caption("Green = primary | Yellow = secondary | Orange = tertiary | "
               "Markers: safe zones, services, transport")
    st_html(_build_evacuation_map(res)._repr_html_(), height=520)
    st.markdown("---")

    # -- Distance Metrics --
    st.markdown("#### Distance to Safe Zones")
    rows = []
    for el in raw.get("safe_zones", [])[:8]:
        elat, elon = _el_pos(el)
        if elat is not None and elon is not None:
            tags = el.get("tags") or {}
            nm = tags.get("name", tags.get("amenity", tags.get("leisure", "Zone")))
            d = _haversine(res["lat"], res["lon"], elat, elon)
            tp = tags.get("amenity", tags.get("leisure", "open"))
            rows.append({"Name": str(nm)[:35],
                         "Type": str(tp).replace("_", " ").title(),
                         "Distance (km)": round(d, 2),
                         "Walk (min)": round(d / 4.5 * 60),
                         "Drive (min)": round(d / 40 * 60, 1),
                         "Suitability": "High" if d < 3 else "Medium" if d < 6 else "Low"})
    if rows:
        rows.sort(key=lambda x: x["Distance (km)"])
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.warning("No safe zone distance data available.")
    st.markdown("---")

    # -- Scenario Comparison --
    st.markdown("#### Scenario Comparison")
    if st.button("Compare All Scenarios", key="evac_compare"):
        with st.spinner("Computing scenario comparisons..."):
            st.session_state["evac_comparison"] = {
                sc: _compute_evacuation_scores(res["lat"], res["lon"], sc)
                for sc in SCENARIO_WEIGHTS}
    if "evac_comparison" in st.session_state:
        comp = st.session_state["evac_comparison"]
        sc_cols = st.columns(len(comp))
        for i, (sn, sr) in enumerate(comp.items()):
            with sc_cols[i]:
                sl, sc_c, _ = _classify_readiness(sr["overall"])
                st.markdown(
                    f'<div style="background:{CLR_CARD};border-radius:10px;padding:14px;'
                    f'text-align:center;border:1px solid {sc_c}44;">'
                    f'<div style="font-size:12px;color:{CLR_TEXT_SEC};'
                    f'text-transform:uppercase;">{escape(sn)}</div>'
                    f'<div style="font-size:32px;font-weight:800;color:{sc_c};">'
                    f'{sr["overall"]:.0f}</div>'
                    f'<div style="font-size:11px;color:{sc_c};">{sl}</div></div>',
                    unsafe_allow_html=True)
        # Grouped bar
        fig_c = go.Figure()
        sc_colors = {"Flood": CLR_BLUE, "Earthquake": CLR_RED,
                     "Wildfire": CLR_ORANGE, "Industrial Accident": CLR_PURPLE}
        for sn, sr in comp.items():
            fig_c.add_trace(go.Bar(name=sn, x=dim_list,
                                   y=[sr["scores"].get(d, 0) for d in dim_list],
                                   marker_color=sc_colors.get(sn, CLR_CYAN)))
        fig_c.update_layout(barmode="group", height=380, margin=dict(t=30, b=80, l=50, r=20),
                            yaxis=dict(range=[0, 10], title="Score", gridcolor="#334155"),
                            xaxis=dict(tickangle=-30), paper_bgcolor=CLR_BG,
                            plot_bgcolor=CLR_BG, font=dict(color=CLR_TEXT, size=11),
                            legend=dict(orientation="h", y=1.12))
        st.plotly_chart(fig_c, use_container_width=True, key="evac_comp_chart")
    st.markdown("---")

    # -- Recommendations --
    st.markdown("#### Evacuation Recommendations")
    rec_map = {
        "Road Network": "Identify alternative unpaved roads or footpaths for evacuation.",
        "Safe Zones": "Map elevated open areas and sturdy buildings as ad-hoc shelters.",
        "Bridges & Chokepoints": "Plan bypass routes that avoid bridges and tunnels.",
        "Terrain Escape": "Pre-identify high ground routes and mark them clearly.",
        "Emergency Services": "Coordinate with nearest services; set up local first-aid posts.",
        "Transport Options": "Arrange vehicle pools or request mobile evacuation units.",
        "Hazard Zones": "Establish hazard perimeters and continuous monitoring protocols.",
    }
    recs = [rec_map[d] for d, s in sorted(scores.items(), key=lambda x: x[1])[:3] if s < 5]
    if not recs:
        recs = ["Overall readiness is adequate. Maintain regular evacuation drills."]
    for idx, rec in enumerate(recs, 1):
        st.markdown(
            f'<div style="background:{CLR_CARD};border-radius:8px;padding:10px 14px;'
            f'margin-bottom:6px;border-left:3px solid {CLR_ACCENT};">'
            f'<span style="color:{CLR_ACCENT};font-weight:700;">#{idx}</span> '
            f'<span style="color:{CLR_TEXT};font-size:13px;">{escape(rec)}</span></div>',
            unsafe_allow_html=True)
