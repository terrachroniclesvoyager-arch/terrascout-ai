"""
Comprehensive Threat Assessment module for TerraScout AI.
Unified analysis of ALL threats (natural + man-made) at a location.
Combines seismic, weather, flood, landslide, industrial, wildfire,
air quality, and isolation threats into a single scored dashboard.
APIs: USGS, Open-Meteo, Open-Meteo AQ, Open Topo Data, Overpass (all free).
"""

import math
import logging
from datetime import datetime

import requests
import streamlit as st
import streamlit.components.v1 as components
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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------
USGS_API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
METEO_API = "https://api.open-meteo.com/v1/forecast"
TOPO_API = "https://api.opentopodata.org/v1/srtm30m"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
AQ_API = "https://air-quality-api.open-meteo.com/v1/air-quality"

# ---------------------------------------------------------------------------
# Threat category definitions (8 categories)
# ---------------------------------------------------------------------------
CATS = [
    {"id": "seismic",    "name": "Seismic Threat",     "icon": "\U0001f30d", "color": "#ef4444"},
    {"id": "weather",    "name": "Extreme Weather",    "icon": "\U0001f32a\ufe0f", "color": "#f97316"},
    {"id": "flood",      "name": "Flood Risk",         "icon": "\U0001f30a", "color": "#3b82f6"},
    {"id": "landslide",  "name": "Landslide Risk",     "icon": "\u26f0\ufe0f",  "color": "#a855f7"},
    {"id": "industrial", "name": "Industrial Hazard",  "icon": "\U0001f3ed", "color": "#6b7280"},
    {"id": "wildfire",   "name": "Wildfire Risk",      "icon": "\U0001f525", "color": "#dc2626"},
    {"id": "air",        "name": "Air Quality Threat", "icon": "\U0001f4a8", "color": "#0ea5e9"},
    {"id": "isolation",  "name": "Isolation Threat",   "icon": "\U0001f3e5", "color": "#14b8a6"},
]

# Severity thresholds: (lower bound, upper bound, label, colour)
SEV_LEVELS = [
    (0.0, 2.0,  "MINIMAL",  "#22c55e"),
    (2.0, 4.0,  "LOW",      "#84cc16"),
    (4.0, 6.0,  "MODERATE", "#f59e0b"),
    (6.0, 8.0,  "HIGH",     "#f97316"),
    (8.0, 10.1, "CRITICAL", "#ef4444"),
]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def _severity_label(score: float) -> tuple:
    """Return (label, colour) for a threat score on the 0-10 scale."""
    for lo, hi, lbl, col in SEV_LEVELS:
        if lo <= score < hi:
            return lbl, col
    return "CRITICAL", "#ef4444"


def _clamp(value: float, lo: float = 0.0, hi: float = 10.0) -> float:
    """Clamp a value between lo and hi."""
    return max(lo, min(hi, value))


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in km between two geographic points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _overpass_query(lat: float, lon: float, radius_m: int, tags: list) -> str:
    """Build an Overpass QL query for multiple tag filters around a point."""
    parts = []
    for t in tags:
        parts.append(f'  node{t}(around:{radius_m},{lat},{lon});')
        parts.append(f'  way{t}(around:{radius_m},{lat},{lon});')
    return "[out:json][timeout:10];\n(\n" + "\n".join(parts) + "\n);\nout center body;"


def _element_coords(el: dict, fallback_lat: float, fallback_lon: float) -> tuple:
    """Extract lat/lon from an Overpass element, falling back to given coords."""
    la = el.get("lat") or el.get("center", {}).get("lat", fallback_lat)
    lo = el.get("lon") or el.get("center", {}).get("lon", fallback_lon)
    return la, lo


def _daily_values(data: dict, key: str) -> list:
    """Extract non-None values from Open-Meteo daily response."""
    return [v for v in (data.get("daily", {}).get(key) or []) if v is not None]


# ---------------------------------------------------------------------------
# Cached API calls (all use ttl=900 and timeout=10)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_seismic(lat: float, lon: float) -> dict:
    """Fetch recent earthquakes from USGS within 200 km."""
    try:
        r = requests.get(USGS_API, params={
            "format": "geojson", "latitude": lat, "longitude": lon,
            "maxradiuskm": 200, "limit": 50,
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("USGS earthquake fetch failed: %s", exc)
        return {"features": []}


@st.cache_data(ttl=900)
def _fetch_weather(lat: float, lon: float) -> dict:
    """Fetch 16-day weather forecast from Open-Meteo."""
    try:
        r = requests.get(METEO_API, params={
            "latitude": lat, "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,wind_speed_10m_max,precipitation_sum",
            "timezone": "auto", "forecast_days": 16,
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("Open-Meteo forecast fetch failed: %s", exc)
        return {}


@st.cache_data(ttl=900)
def _fetch_elevation(lat: float, lon: float) -> float:
    """Fetch elevation in metres from Open Topo Data SRTM dataset."""
    try:
        r = requests.get(TOPO_API, params={"locations": f"{lat},{lon}"}, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        if results and results[0].get("elevation") is not None:
            return float(results[0]["elevation"])
    except Exception as exc:
        logger.warning("Elevation fetch failed: %s", exc)
    return -9999.0


@st.cache_data(ttl=900)
def _fetch_elevation_neighbours(lat: float, lon: float) -> list:
    """Fetch elevation at 4 cardinal points ~500 m from centre for slope calc."""
    off = 0.005
    pts = [(lat + off, lon), (lat - off, lon), (lat, lon + off), (lat, lon - off)]
    locs = "|".join(f"{p[0]},{p[1]}" for p in pts)
    try:
        r = requests.get(TOPO_API, params={"locations": locs}, timeout=10)
        r.raise_for_status()
        return [x.get("elevation", 0) or 0 for x in r.json().get("results", [])]
    except Exception as exc:
        logger.warning("Elevation neighbours fetch failed: %s", exc)
        return [0, 0, 0, 0]


@st.cache_data(ttl=900)
def _fetch_overpass(query: str) -> list:
    """Execute an Overpass API query and return elements."""
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        r.raise_for_status()
        return r.json().get("elements", [])
    except Exception as exc:
        logger.warning("Overpass query failed: %s", exc)
        return []


@st.cache_data(ttl=900)
def _fetch_air_quality(lat: float, lon: float) -> dict:
    """Fetch current air quality from Open-Meteo Air Quality API."""
    try:
        r = requests.get(AQ_API, params={
            "latitude": lat, "longitude": lon,
            "current": "pm10,pm2_5,european_aqi",
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        logger.warning("Air quality fetch failed: %s", exc)
        return {}


# ---------------------------------------------------------------------------
# Threat scoring functions — each returns (score: float, detail: dict)
# ---------------------------------------------------------------------------
def _score_seismic(lat: float, lon: float) -> tuple:
    """Score 0-10 for seismic threat based on earthquake frequency and magnitude."""
    feats = _fetch_seismic(lat, lon).get("features", [])
    if not feats:
        return 0.0, {"count": 0, "max_mag": 0, "avg_depth": 0, "events": []}
    mags, depths, events = [], [], []
    for f in feats:
        p = f.get("properties", {})
        co = f.get("geometry", {}).get("coordinates", [0, 0, 0])
        mag = p.get("mag") or 0
        dep = co[2] if len(co) > 2 else 0
        mags.append(mag)
        depths.append(dep)
        events.append({"mag": mag, "place": p.get("place", "Unknown"),
                       "time": p.get("time", 0), "depth": dep,
                       "lat": co[1] if len(co) > 1 else lat,
                       "lon": co[0] if co else lon})
    mx = max(mags)
    ad = sum(depths) / len(depths)
    freq_sc = min(len(feats) / 10.0, 5.0)
    mag_sc = min(mx / 2.0, 5.0)
    depth_pen = max(0, 1.0 - ad / 100.0)  # shallow quakes are worse
    score = _clamp(freq_sc + mag_sc + depth_pen)
    detail = {"count": len(feats), "max_mag": round(mx, 1), "avg_depth": round(ad, 1),
              "events": sorted(events, key=lambda e: -e["mag"])[:10]}
    return round(score, 1), detail


def _score_weather(lat: float, lon: float) -> tuple:
    """Score 0-10 for extreme weather threat based on 16-day forecast."""
    data = _fetch_weather(lat, lon)
    if not data.get("daily"):
        return 0.0, {"max_temp": "N/A", "min_temp": "N/A",
                     "max_wind": "N/A", "max_precip": "N/A"}
    tmx = _daily_values(data, "temperature_2m_max")
    tmn = _daily_values(data, "temperature_2m_min")
    wnd = _daily_values(data, "wind_speed_10m_max")
    prc = _daily_values(data, "precipitation_sum")
    mt = max(tmx) if tmx else 20
    mn = min(tmn) if tmn else 10
    mw = max(wnd) if wnd else 0
    mp = max(prc) if prc else 0
    # Temperature extremes
    ts = (min((mt - 35) / 3.0, 3.0) if mt > 35 else 0) + \
         (min((-10 - mn) / 5.0, 3.0) if mn < -10 else 0)
    ws = min(max(mw - 30, 0) / 15.0, 3.0)   # wind > 30 km/h
    ps = min(max(mp - 10, 0) / 20.0, 3.0)   # precipitation > 10 mm
    score = _clamp(ts + ws + ps + 0.5)
    detail = {"max_temp": f"{mt:.1f} C", "min_temp": f"{mn:.1f} C",
              "max_wind": f"{mw:.1f} km/h", "max_precip": f"{mp:.1f} mm",
              "forecast_days": len(tmx)}
    return round(score, 1), detail


def _score_flood(lat: float, lon: float) -> tuple:
    """Score 0-10 for flood risk from elevation and water body proximity."""
    elev = _fetch_elevation(lat, lon)
    wq = _overpass_query(lat, lon, 5000, [
        '["natural"="water"]', '["waterway"="river"]',
        '["waterway"="stream"]', '["waterway"="canal"]',
    ])
    welems = _fetch_overpass(wq)
    wc = len(welems)
    # Low elevation = higher flood risk
    es = 0.0
    if elev != -9999.0:
        if elev < 5:     es = 5.0
        elif elev < 20:  es = 3.0
        elif elev < 50:  es = 1.5
        elif elev < 100: es = 0.5
    ws = min(wc / 5.0, 4.0)  # water proximity
    # Precipitation factor
    prc = _daily_values(_fetch_weather(lat, lon), "precipitation_sum")
    ap = sum(prc) / len(prc) if prc else 0
    pf = min(ap / 15.0, 2.0)
    # Collect water features for map
    water_features = []
    for el in welems[:15]:
        tg = el.get("tags", {})
        nm = tg.get("name", tg.get("waterway", tg.get("natural", "Water")))
        la, lo2 = _element_coords(el, lat, lon)
        water_features.append({"name": nm, "lat": la, "lon": lo2})
    detail = {"elevation_m": round(elev, 1) if elev != -9999 else "N/A",
              "water_bodies_nearby": wc, "avg_precip_mm": round(ap, 1),
              "water_features": water_features}
    return round(_clamp(es + ws + pf), 1), detail


def _score_landslide(lat: float, lon: float) -> tuple:
    """Score 0-10 for landslide risk from slope steepness and precipitation."""
    ce = _fetch_elevation(lat, lon)
    ne = _fetch_elevation_neighbours(lat, lon)
    if ce == -9999.0:
        return 0.0, {"slope_deg": "N/A", "elevation_m": "N/A"}
    diffs = [abs(ce - e) for e in ne if e != 0]
    md = max(diffs) if diffs else 0
    slope = math.degrees(math.atan2(md, 500))
    # Slope scoring
    ss = 5.0 if slope > 35 else 3.5 if slope > 25 else 2.0 if slope > 15 \
        else 1.0 if slope > 8 else 0
    # Precipitation and elevation factors
    prc = _daily_values(_fetch_weather(lat, lon), "precipitation_sum")
    mp = max(prc) if prc else 0
    pf = min(mp / 20.0, 3.0)
    ef = min(max(ce - 200, 0) / 500.0, 2.0)
    detail = {"slope_deg": round(slope, 1), "elevation_m": round(ce, 1),
              "max_precip_mm": round(mp, 1),
              "neighbour_elevations": [round(e, 1) for e in ne]}
    return round(_clamp(ss + pf + ef), 1), detail


def _score_industrial(lat: float, lon: float) -> tuple:
    """Score 0-10 for industrial hazard from nearby factories and plants."""
    q = _overpass_query(lat, lon, 5000, [
        '["man_made"="works"]', '["industrial"]', '["power"="plant"]',
        '["power"="generator"]', '["amenity"="fuel"]', '["hazard"]',
        '["landuse"="industrial"]',
    ])
    elems = _fetch_overpass(q)
    cnt = len(elems)
    hazards = []
    high_risk = 0
    for el in elems:
        tg = el.get("tags", {})
        nm = tg.get("name", "Unnamed facility")
        ht = "industrial"
        if tg.get("power"):
            ht = "power_plant"; high_risk += 1
        elif tg.get("hazard") or "chemical" in str(tg).lower():
            ht = "chemical"; high_risk += 2
        elif tg.get("amenity") == "fuel":
            ht = "fuel_station"
        elif "industrial" in str(tg.get("landuse", "")):
            ht = "industrial_zone"
        la, lo2 = _element_coords(el, lat, lon)
        dist = _haversine(lat, lon, la, lo2)
        hazards.append({"name": nm, "type": ht, "lat": la, "lon": lo2,
                        "distance_km": round(dist, 2)})
    hazards.sort(key=lambda h: h["distance_km"])
    score = _clamp(min(cnt / 8.0, 5.0) + min(high_risk * 1.5, 5.0))
    detail = {"total_facilities": cnt, "high_risk_count": high_risk,
              "hazards": hazards[:15]}
    return round(score, 1), detail


def _score_wildfire(lat: float, lon: float) -> tuple:
    """Score 0-10 for wildfire risk from temperature, dryness, and vegetation."""
    data = _fetch_weather(lat, lon)
    tmx = _daily_values(data, "temperature_2m_max")
    prc = _daily_values(data, "precipitation_sum")
    mt = max(tmx) if tmx else 20
    ap = sum(prc) / len(prc) if prc else 5
    # Vegetation density from Overpass
    vq = _overpass_query(lat, lon, 5000, [
        '["natural"="wood"]', '["landuse"="forest"]',
        '["natural"="scrub"]', '["natural"="grassland"]',
    ])
    vc = len(_fetch_overpass(vq))
    # Temperature scoring
    ts = 4.0 if mt > 40 else 3.0 if mt > 35 else 1.5 if mt > 30 \
        else 0.5 if mt > 25 else 0
    # Dryness scoring (low precipitation = high risk)
    ds = 3.0 if ap < 1 else 2.0 if ap < 3 else 1.0 if ap < 5 else 0
    vs = min(vc / 5.0, 3.0)  # vegetation density factor
    detail = {"max_temp_c": round(mt, 1), "avg_precip_mm": round(ap, 1),
              "vegetation_features": vc}
    return round(_clamp(ts + ds + vs), 1), detail


def _aqi_label(aqi: float) -> str:
    """Return human-readable European AQI label."""
    if aqi <= 20:  return "Good"
    if aqi <= 40:  return "Fair"
    if aqi <= 60:  return "Moderate"
    if aqi <= 80:  return "Poor"
    if aqi <= 100: return "Very Poor"
    return "Extremely Poor"


def _score_air(lat: float, lon: float) -> tuple:
    """Score 0-10 for air quality threat from PM2.5, PM10, European AQI."""
    cur = _fetch_air_quality(lat, lon).get("current", {})
    p25 = cur.get("pm2_5", 0) or 0
    p10 = cur.get("pm10", 0) or 0
    aqi = cur.get("european_aqi", 0) or 0
    aq = 5 if aqi > 100 else 4 if aqi > 80 else 3 if aqi > 60 \
        else 2 if aqi > 40 else 1 if aqi > 20 else 0
    score = _clamp(aq + min(p25 / 20.0, 3.0) + min(p10 / 30.0, 2.0))
    detail = {"pm2_5": round(p25, 1), "pm10": round(p10, 1),
              "european_aqi": round(aqi, 1), "aqi_label": _aqi_label(aqi)}
    return round(score, 1), detail


def _score_isolation(lat: float, lon: float) -> tuple:
    """Score 0-10 for isolation threat from distance to emergency services."""
    hosp = _fetch_overpass(_overpass_query(lat, lon, 10000, ['["amenity"="hospital"]']))
    fire = _fetch_overpass(_overpass_query(lat, lon, 10000, ['["amenity"="fire_station"]']))
    poli = _fetch_overpass(_overpass_query(lat, lon, 10000, ['["amenity"="police"]']))
    road = _fetch_overpass(_overpass_query(lat, lon, 3000, [
        '["highway"="primary"]', '["highway"="secondary"]',
        '["highway"="trunk"]', '["highway"="motorway"]',
    ]))
    hc, fc, pc, rc = len(hosp), len(fire), len(poli), len(road)
    # Fewer services = higher isolation
    hs = max(3.0 - hc, 0)
    fs = max(2.0 - fc * 0.8, 0)
    ps = max(2.0 - pc * 0.8, 0)
    rs = max(3.0 - rc * 0.3, 0)
    # Collect nearest services for the map display
    svcs = []
    for h in hosp[:5]:
        la, lo2 = _element_coords(h, lat, lon)
        svcs.append({"name": h.get("tags", {}).get("name", "Hospital"),
                     "type": "hospital", "lat": la, "lon": lo2,
                     "distance_km": round(_haversine(lat, lon, la, lo2), 2)})
    for f in fire[:5]:
        la, lo2 = _element_coords(f, lat, lon)
        svcs.append({"name": f.get("tags", {}).get("name", "Fire Station"),
                     "type": "fire_station", "lat": la, "lon": lo2,
                     "distance_km": round(_haversine(lat, lon, la, lo2), 2)})
    svcs.sort(key=lambda s: s["distance_km"])
    detail = {"hospitals": hc, "fire_stations": fc, "police_stations": pc,
              "major_roads": rc, "nearest_services": svcs[:10]}
    return round(_clamp(hs + fs + ps + rs), 1), detail


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
_SKIP_DETAIL_KEYS = frozenset({
    "events", "hazards", "water_features", "nearest_services", "neighbour_elevations",
})


def _card_html(cat: dict, score: float, detail: dict) -> str:
    """Generate a styled HTML card for a single threat category."""
    lbl, col = _severity_label(score)
    pct = min(score * 10, 100)
    lines = ""
    for k, v in detail.items():
        if k in _SKIP_DETAIL_KEYS:
            continue
        nice = k.replace("_", " ").title()
        lines += (f"<div style='display:flex;justify-content:space-between'>"
                  f"<span style='color:#9ca3af;font-size:.82rem'>{nice}</span>"
                  f"<span style='color:#e5e7eb;font-size:.82rem;font-weight:600'>{v}</span>"
                  f"</div>")
    return (
        f"<div style='background:linear-gradient(135deg,#1e1e2e,#2a2a3e);"
        f"border-left:4px solid {col};border-radius:10px;padding:16px;margin-bottom:12px'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;"
        f"margin-bottom:8px'>"
        f"<span style='font-size:1.1rem;font-weight:700;color:#f1f5f9'>"
        f"{cat['icon']} {cat['name']}</span>"
        f"<span style='background:{col};color:#fff;padding:3px 10px;border-radius:12px;"
        f"font-size:.78rem;font-weight:700'>{lbl} ({score}/10)</span></div>"
        f"<div style='background:#374151;border-radius:6px;height:8px;margin-bottom:10px'>"
        f"<div style='background:{col};width:{pct}%;height:100%;border-radius:6px'></div>"
        f"</div>{lines}</div>"
    )


def _banner_html(avg: float) -> str:
    """Render the overall threat level banner as styled HTML."""
    lbl, col = _severity_label(avg)
    return (
        f"<div style='background:linear-gradient(135deg,#0f0f1a,#1a1a2e);"
        f"border:2px solid {col};border-radius:14px;padding:24px;text-align:center;"
        f"margin-bottom:20px'>"
        f"<div style='font-size:.85rem;color:#9ca3af;text-transform:uppercase;"
        f"letter-spacing:2px;margin-bottom:6px'>Overall Threat Level</div>"
        f"<div style='font-size:2.6rem;font-weight:800;color:{col};"
        f"margin-bottom:4px'>{lbl}</div>"
        f"<div style='font-size:1.3rem;color:#e5e7eb'>Composite Score: "
        f"<strong style='color:{col}'>{avg:.1f}</strong> / 10</div></div>"
    )


def _build_radar(scores: dict) -> go.Figure:
    """Build a Plotly polar/radar chart of all 8 threat scores."""
    cats = list(scores.keys())
    vals = list(scores.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=cats + [cats[0]],
        fill="toself", fillcolor="rgba(239,68,68,0.15)",
        line=dict(color="#ef4444", width=2),
        marker=dict(size=7, color="#ef4444"),
        name="Threat Score",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(15,15,26,0.9)",
            radialaxis=dict(visible=True, range=[0, 10],
                            tickfont=dict(size=10, color="#9ca3af"),
                            gridcolor="rgba(75,85,99,0.3)"),
            angularaxis=dict(tickfont=dict(size=11, color="#e5e7eb"),
                             gridcolor="rgba(75,85,99,0.3)"),
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=30, b=30),
        height=420,
    )
    return fig


def _build_threat_map(lat: float, lon: float, res: dict) -> folium.Map:
    """Build a folium map with threat-source markers and radius circles."""
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB dark_matter")

    # Centre marker
    folium.Marker([lat, lon], popup="<b>Assessment Location</b>",
                  icon=folium.Icon(color="red", icon="exclamation-triangle",
                                   prefix="fa")).add_to(m)
    # Assessment radii
    folium.Circle([lat, lon], radius=5000, color="#ef4444", fill=True,
                  fill_opacity=0.05, weight=1, dash_array="5",
                  popup="5 km assessment radius").add_to(m)
    folium.Circle([lat, lon], radius=10000, color="#f59e0b", fill=False,
                  weight=1, dash_array="8",
                  popup="10 km extended radius").add_to(m)

    # Seismic events
    for ev in res.get("seismic", {}).get("detail", {}).get("events", [])[:8]:
        mg = ev.get("mag", 0)
        c = "#ef4444" if mg >= 5 else "#f59e0b" if mg >= 3 else "#22c55e"
        folium.CircleMarker([ev["lat"], ev["lon"]], radius=max(mg * 3, 4),
                            color=c, fill=True, fill_opacity=0.6,
                            popup=f"<b>M{mg}</b><br>{ev.get('place', '')}").add_to(m)

    # Water features (flood)
    for wf in res.get("flood", {}).get("detail", {}).get("water_features", [])[:10]:
        folium.CircleMarker([wf["lat"], wf["lon"]], radius=5, color="#3b82f6",
                            fill=True, fill_opacity=0.5,
                            popup=f"<b>{wf['name']}</b> (water)").add_to(m)

    # Industrial hazards
    _ic = {"power_plant": ("bolt", "orange"), "chemical": ("flask", "darkred"),
           "fuel_station": ("gas-pump", "gray"),
           "industrial_zone": ("industry", "darkblue"),
           "industrial": ("industry", "cadetblue")}
    for hz in res.get("industrial", {}).get("detail", {}).get("hazards", [])[:10]:
        icn, icc = _ic.get(hz["type"], ("industry", "cadetblue"))
        folium.Marker([hz["lat"], hz["lon"]],
                      popup=f"<b>{hz['name']}</b><br>{hz['type']} ({hz['distance_km']} km)",
                      icon=folium.Icon(color=icc, icon=icn, prefix="fa")).add_to(m)

    # Emergency services (isolation)
    _sc = {"hospital": ("hospital-o", "green"),
           "fire_station": ("fire-extinguisher", "red")}
    for sv in res.get("isolation", {}).get("detail", {}).get("nearest_services", [])[:8]:
        icn, icc = _sc.get(sv["type"], ("info", "blue"))
        folium.Marker([sv["lat"], sv["lon"]],
                      popup=f"<b>{sv['name']}</b><br>{sv['distance_km']} km",
                      icon=folium.Icon(color=icc, icon=icn, prefix="fa")).add_to(m)
    return m


def _key_factor(cid: str, d: dict) -> str:
    """Extract a concise key-factor string for the score-breakdown table."""
    if cid == "seismic":
        return f"{d.get('count', 0)} events, max M{d.get('max_mag', 0)}"
    if cid == "weather":
        return f"Max {d.get('max_temp', 'N/A')}, wind {d.get('max_wind', 'N/A')}"
    if cid == "flood":
        return (f"Elev {d.get('elevation_m', 'N/A')}m, "
                f"{d.get('water_bodies_nearby', 0)} water bodies")
    if cid == "landslide":
        return (f"Slope {d.get('slope_deg', 'N/A')} deg, "
                f"elev {d.get('elevation_m', 'N/A')}m")
    if cid == "industrial":
        return (f"{d.get('total_facilities', 0)} facilities, "
                f"{d.get('high_risk_count', 0)} high-risk")
    if cid == "wildfire":
        return (f"Max {d.get('max_temp_c', 0)} C, "
                f"{d.get('vegetation_features', 0)} veg areas")
    if cid == "air":
        return (f"AQI {d.get('european_aqi', 0)} ({d.get('aqi_label', 'N/A')}), "
                f"PM2.5 {d.get('pm2_5', 0)}")
    if cid == "isolation":
        return (f"{d.get('hospitals', 0)} hospitals, "
                f"{d.get('fire_stations', 0)} fire stations in 10 km")
    return "N/A"


# ---------------------------------------------------------------------------
# Recommendation definitions (table-driven to keep code compact)
# ---------------------------------------------------------------------------
_REC_DEFS = [
    ("seismic", 6, "\U0001f30d", "Seismic Preparedness Required",
     "Significant seismic activity detected. Ensure structures meet earthquake resistance "
     "standards. Prepare emergency kits and evacuation routes. Consider seismic retrofitting."),
    ("seismic", 3, "\U0001f30d", "Seismic Awareness",
     "Moderate seismic activity present. Basic earthquake preparedness is advised. "
     "Review building codes and ensure structural integrity."),
    ("weather", 6, "\U0001f32a\ufe0f", "Extreme Weather Alert",
     "Severe weather conditions forecast. Plan for temperature extremes, high winds, "
     "or heavy precipitation. Secure outdoor structures and ensure adequate shelter."),
    ("weather", 3, "\U0001f32a\ufe0f", "Weather Monitoring Advised",
     "Notable weather variability expected. Monitor forecasts regularly and prepare "
     "for moderate temperature or wind events."),
    ("flood", 6, "\U0001f30a", "High Flood Risk",
     "Significant flood exposure due to low elevation and water proximity. Implement "
     "flood barriers, ensure proper drainage, and develop flood evacuation plans."),
    ("flood", 3, "\U0001f30a", "Moderate Flood Awareness",
     "Some flood risk present. Review drainage systems, check flood insurance coverage, "
     "and be aware of seasonal water level changes."),
    ("landslide", 5, "\u26f0\ufe0f", "Landslide Risk Present",
     "Terrain slope and conditions suggest landslide vulnerability. Avoid construction "
     "on steep slopes, implement retaining walls, and monitor soil moisture after rains."),
    ("industrial", 5, "\U0001f3ed", "Industrial Hazard Proximity",
     "Multiple industrial facilities nearby. Verify emergency response plans, understand "
     "wind patterns for chemical dispersal, and maintain awareness of incident protocols."),
    ("wildfire", 5, "\U0001f525", "Wildfire Conditions Present",
     "Conditions favour wildfire ignition and spread. Clear vegetation within defensible "
     "space perimeter, prepare fire suppression equipment, identify evacuation routes."),
    ("air", 5, "\U0001f4a8", "Poor Air Quality",
     "Air quality is degraded. Limit outdoor exposure for sensitive groups, use air "
     "filtration indoors, and monitor AQI readings regularly."),
    ("isolation", 5, "\U0001f3e5", "Limited Emergency Services",
     "Location is relatively isolated from emergency services. Maintain comprehensive "
     "first-aid supplies and establish reliable communication protocols."),
]


def _build_recommendations(results: dict) -> list:
    """Generate actionable recommendations based on individual threat scores."""
    recs = []
    seen = set()
    for cid, thresh, icon, title, text in _REC_DEFS:
        if cid in seen:
            continue
        sc = results.get(cid, {}).get("score", 0)
        if sc >= thresh:
            recs.append({"icon": icon, "title": title, "severity": sc, "text": text})
            seen.add(cid)
    if not recs:
        recs.append({
            "icon": "\u2705", "title": "Low Overall Threat Profile", "severity": 1.0,
            "text": "No individual threat category scored high enough to trigger specific "
                    "recommendations. Standard preparedness measures are sufficient.",
        })
    recs.sort(key=lambda r: -r["severity"])
    return recs


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def render_threat_assessment_tab():
    """Single entry point for the Comprehensive Threat Assessment tab."""
    st.markdown("## Comprehensive Threat Assessment")
    st.caption("Unified natural & man-made threat analysis across 8 categories")

    # Coordinate inputs
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, min_value=-90.0,
                          max_value=90.0, format="%.4f", key="threat_lat")
    lon = c2.number_input("Longitude", value=12.4964, min_value=-180.0,
                          max_value=180.0, format="%.4f", key="threat_lon")
    st.markdown("---")

    if not st.button("Assess All Threats", key="threat_btn", type="primary",
                     use_container_width=True):
        st.info(
            "Enter coordinates and click **Assess All Threats** to begin the comprehensive "
            "analysis. The assessment covers seismic activity, extreme weather, flood risk, "
            "landslides, industrial hazards, wildfire potential, air quality, and isolation."
        )
        return

    # ── Run all 8 threat assessments with progress bar ──
    results = {}
    progress = st.progress(0, text="Initialising threat assessment...")
    funcs = [
        ("seismic", _score_seismic), ("weather", _score_weather),
        ("flood", _score_flood), ("landslide", _score_landslide),
        ("industrial", _score_industrial), ("wildfire", _score_wildfire),
        ("air", _score_air), ("isolation", _score_isolation),
    ]
    for idx, (cid, fn) in enumerate(funcs):
        cat = next(c for c in CATS if c["id"] == cid)
        progress.progress((idx + 1) / len(funcs),
                          text=f"Assessing {cat['icon']} {cat['name']}...")
        sc, det = fn(lat, lon)
        results[cid] = {"score": sc, "detail": det}
    progress.empty()

    # Compute aggregate score
    scores_list = [results[c["id"]]["score"] for c in CATS]
    avg_score = round(sum(scores_list) / len(scores_list), 1)

    # ── Overall threat-level banner ──
    st.markdown(_banner_html(avg_score), unsafe_allow_html=True)

    # ── Key metrics row ──
    sd = results.get("seismic", {}).get("detail", {})
    wd = results.get("weather", {}).get("detail", {})
    ad = results.get("air", {}).get("detail", {})
    fd = results.get("flood", {}).get("detail", {})
    metrics = [
        ("Earthquakes", sd.get("count", 0), "in 200 km"),
        ("Max Magnitude", sd.get("max_mag", 0), "Richter"),
        ("Max Temperature", wd.get("max_temp", "N/A"), "forecast"),
        ("Max Wind", wd.get("max_wind", "N/A"), "forecast"),
        ("PM 2.5", ad.get("pm2_5", 0), "ug/m3"),
        ("Elevation", fd.get("elevation_m", "N/A"), "meters"),
    ]
    mcols = st.columns(len(metrics))
    for i, (lbl, val, unit) in enumerate(metrics):
        with mcols[i]:
            st.metric(label=lbl, value=str(val), delta=unit, delta_color="off")
    st.markdown("---")

    # ── Radar chart + Priority ranking side by side ──
    rcol, pcol = st.columns([1, 1])
    with rcol:
        st.markdown("#### Threat Radar Profile")
        score_map = {c["name"]: results[c["id"]]["score"] for c in CATS}
        st.plotly_chart(_build_radar(score_map, key="thrass_pchart1"), use_container_width=True,
                        key="threat_radar_chart")
    with pcol:
        st.markdown("#### Threat Priority Ranking")
        ranked = sorted(CATS, key=lambda c: -results[c["id"]]["score"])
        for rk, cat in enumerate(ranked, 1):
            sc = results[cat["id"]]["score"]
            lbl, col = _severity_label(sc)
            pct = min(sc * 10, 100)
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:10px;padding:6px 0;"
                f"border-bottom:1px solid rgba(75,85,99,0.3)'>"
                f"<span style='font-size:1.1rem;font-weight:700;color:{col};"
                f"width:24px'>#{rk}</span>"
                f"<span style='flex:1;color:#e5e7eb;font-size:.92rem'>"
                f"{cat['icon']} {cat['name']}</span>"
                f"<div style='width:100px;background:#374151;border-radius:4px;height:6px'>"
                f"<div style='width:{pct}%;background:{col};height:100%;"
                f"border-radius:4px'></div></div>"
                f"<span style='color:{col};font-weight:700;font-size:.9rem;width:45px;"
                f"text-align:right'>{sc}/10</span></div>",
                unsafe_allow_html=True,
            )
    st.markdown("---")

    # ── Detailed threat cards in 2 columns ──
    st.markdown("#### Detailed Threat Analysis")
    lcol, rcol2 = st.columns(2)
    for i, cat in enumerate(CATS):
        entry = results[cat["id"]]
        html = _card_html(cat, entry["score"], entry["detail"])
        with (lcol if i % 2 == 0 else rcol2):
            st.markdown(html, unsafe_allow_html=True)
    st.markdown("---")

    # ── Folium threat-source map ──
    st.markdown("#### Threat Source Map")
    st.caption("Earthquake epicentres, water bodies, industrial hazards, and emergency services")
    threat_map = _build_threat_map(lat, lon, results)
    components.html(threat_map._repr_html_(), height=520, scrolling=False)
    st.markdown("---")

    # ── Score breakdown table ──
    st.markdown("#### Score Breakdown")
    hcols = st.columns([2, 1, 1, 3])
    hcols[0].markdown("**Category**")
    hcols[1].markdown("**Score**")
    hcols[2].markdown("**Level**")
    hcols[3].markdown("**Key Factor**")
    for cat in CATS:
        cid = cat["id"]
        sc = results[cid]["score"]
        det = results[cid]["detail"]
        lbl, col = _severity_label(sc)
        kf = _key_factor(cid, det)
        row = st.columns([2, 1, 1, 3])
        row[0].markdown(f"{cat['icon']} {cat['name']}")
        row[1].markdown(f"<span style='color:{col};font-weight:700'>{sc}/10</span>",
                        unsafe_allow_html=True)
        row[2].markdown(f"<span style='background:{col};color:#fff;padding:2px 8px;"
                        f"border-radius:8px;font-size:.75rem'>{lbl}</span>",
                        unsafe_allow_html=True)
        row[3].markdown(f"<span style='color:#9ca3af;font-size:.85rem'>{kf}</span>",
                        unsafe_allow_html=True)
    st.markdown("---")

    # ── Threat mitigation recommendations ──
    st.markdown("#### Threat Mitigation Recommendations")
    for rec in _build_recommendations(results):
        _, rc = _severity_label(rec["severity"])
        st.markdown(
            f"<div style='background:rgba(30,30,46,0.8);border-left:3px solid {rc};"
            f"padding:10px 14px;border-radius:6px;margin-bottom:8px'>"
            f"<span style='color:{rc};font-weight:700'>{rec['icon']} {rec['title']}</span>"
            f"<br/><span style='color:#d1d5db;font-size:.88rem'>{rec['text']}</span></div>",
            unsafe_allow_html=True,
        )

    # ── Footer ──
    st.caption(
        f"Assessment completed at {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} "
        f"| Coordinates: {lat:.4f}, {lon:.4f} | "
        f"Data: USGS, Open-Meteo, OpenTopoData, Overpass"
    )
