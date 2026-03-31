"""
Shelter & Habitability Analysis module for TerraScout AI.
Assesses how suitable an area is for establishing shelter, camps, or
temporary settlements across 7 dimensions: terrain suitability, ground
stability, water access, weather exposure, natural cover, supply access,
and hazard exposure.
Uses free APIs: Open Topo Data, ISRIC SoilGrids v2.0, Overpass,
Open-Meteo, USGS (no API keys required).
"""

import json
import math
import datetime
import logging
from html import escape

import streamlit as st
import requests
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

# =============================================================================
# THEME CONSTANTS
# =============================================================================
CLR_BG, CLR_SURFACE, CLR_CARD = "#1a1a2e", "#16213e", "#0f3460"
CLR_BORDER, CLR_TEXT, CLR_TEXT_SEC = "#1a4080", "#e8ecf4", "#8b97b0"
CLR_ACCENT = "#f59e0b"
CLR_SUITABLE, CLR_MARGINAL, CLR_UNSUITABLE = "#22c55e", "#f59e0b", "#ef4444"

DIMENSION_META = {
    "Terrain Suitability":  {"color": "#c9a66b", "weight": 0.18},
    "Ground Stability":     {"color": "#a0785a", "weight": 0.14},
    "Water Access":         {"color": "#3b82f6", "weight": 0.16},
    "Weather Exposure":     {"color": "#f59e0b", "weight": 0.14},
    "Natural Cover":        {"color": "#22c55e", "weight": 0.12},
    "Supply Access":        {"color": "#8b5cf6", "weight": 0.12},
    "Hazard Exposure":      {"color": "#ef4444", "weight": 0.14},
}
DIMENSION_ORDER = list(DIMENSION_META.keys())

# =============================================================================
# HELPERS
# =============================================================================
def _clamp(v, lo=0.0, hi=10.0):
    return max(lo, min(hi, float(v)))

def _verdict_color(s):
    return CLR_SUITABLE if s >= 7 else CLR_MARGINAL if s >= 4 else CLR_UNSUITABLE

def _verdict_label(s):
    return "SUITABLE" if s >= 7 else "MARGINAL" if s >= 4 else "UNSUITABLE"

def _verdict_badge(s):
    return "GO" if s >= 7 else "CAUTION" if s >= 4 else "NO-GO"

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _safe_mean(vals):
    c = [v for v in (vals or []) if v is not None]
    return sum(c) / len(c) if c else 0.0

def _nearest_dist(lat, lon, elements):
    best = None
    for el in (elements if isinstance(elements, list) else []):
        elat = el.get("lat") or (el.get("center") or {}).get("lat")
        elon = el.get("lon") or (el.get("center") or {}).get("lon")
        if elat is not None and elon is not None:
            d = _haversine(lat, lon, elat, elon)
            if best is None or d < best:
                best = d
    return best

def _dim_card(name, score, detail, color):
    sc = _verdict_color(score)
    return (
        f'<div style="background:{CLR_CARD};border-radius:10px;padding:14px 12px;'
        f'border:1px solid {color}44;margin-bottom:8px;min-height:130px;">'
        f'<div style="font-size:12px;color:{color};font-weight:600;'
        f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">'
        f'{escape(name)}</div>'
        f'<div style="font-size:28px;font-weight:800;color:{sc};">{score}</div>'
        f'<div style="font-size:11px;color:{CLR_TEXT_SEC};margin-top:4px;'
        f'line-height:1.35;">{escape(detail[:90])}</div></div>'
    )

# =============================================================================
# DATA FETCHING  (all cached, all with timeout=10, all try/except)
# =============================================================================
@st.cache_data(ttl=900)
def _fetch_elevation(lat, lon):
    """Fetch center elevation + 5x5 grid from Open Topo Data."""
    try:
        pts = []
        for i in range(5):
            for j in range(5):
                pts.append(f"{lat + (i - 2) * 0.004:.5f},{lon + (j - 2) * 0.004:.5f}")
        resp = requests.get(
            "https://api.opentopodata.org/v1/srtm30m",
            params={"locations": "|".join(pts)}, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        elevs = [float(r.get("elevation") or 0) for r in results]
        mid = len(elevs) // 2
        return {"center_elevation": elevs[mid] if elevs else 0.0,
                "grid_elevations": elevs}
    except Exception as exc:
        logger.warning("Elevation fetch error: %s", exc)
        return {"center_elevation": 0.0, "grid_elevations": []}

@st.cache_data(ttl=900)
def _fetch_soil(lat, lon):
    """Fetch soil data from ISRIC SoilGrids v2.0."""
    try:
        resp = requests.get(
            "https://rest.isric.org/soilgrids/v2.0/properties/query",
            params={"lon": lon, "lat": lat,
                     "property": ["clay", "sand", "soc"],
                     "depth": "0-5cm", "value": "mean"},
            timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("SoilGrids fetch error: %s", exc)
        return {}

@st.cache_data(ttl=900)
def _fetch_water_sources(lat, lon, radius=5000):
    """Fetch water sources from Overpass API."""
    query = f"""[out:json][timeout:25];(
      node["natural"="spring"](around:{radius},{lat},{lon});
      node["natural"="water"](around:{radius},{lat},{lon});
      way["waterway"="river"](around:{radius},{lat},{lon});
      way["waterway"="stream"](around:{radius},{lat},{lon});
      node["man_made"="water_well"](around:{radius},{lat},{lon});
      node["amenity"="drinking_water"](around:{radius},{lat},{lon});
      way["natural"="water"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        resp = requests.post("https://overpass-api.de/api/interpreter",
                             data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Water sources fetch error: %s", exc)
        return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_weather(lat, lon):
    """Fetch current + daily forecast from Open-Meteo."""
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,precipitation,relative_humidity_2m",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
            "timezone": "auto"}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Weather fetch error: %s", exc)
        return {}

@st.cache_data(ttl=900)
def _fetch_natural_cover(lat, lon, radius=3000):
    """Fetch forests, trees, hedges from Overpass API."""
    query = f"""[out:json][timeout:25];(
      way["natural"="wood"](around:{radius},{lat},{lon});
      way["landuse"="forest"](around:{radius},{lat},{lon});
      node["natural"="tree"](around:{radius},{lat},{lon});
      way["natural"="scrub"](around:{radius},{lat},{lon});
      way["natural"="hedge"](around:{radius},{lat},{lon});
      way["natural"="tree_row"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        resp = requests.post("https://overpass-api.de/api/interpreter",
                             data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Natural cover fetch error: %s", exc)
        return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_supply_points(lat, lon, radius=5000):
    """Fetch shops, fuel, hardware stores from Overpass API."""
    query = f"""[out:json][timeout:25];(
      node["shop"](around:{radius},{lat},{lon});
      node["amenity"="fuel"](around:{radius},{lat},{lon});
      node["shop"="hardware"](around:{radius},{lat},{lon});
      node["shop"="doityourself"](around:{radius},{lat},{lon});
      node["shop"="convenience"](around:{radius},{lat},{lon});
      node["shop"="supermarket"](around:{radius},{lat},{lon});
      node["amenity"="marketplace"](around:{radius},{lat},{lon});
    );out center body;"""
    try:
        resp = requests.post("https://overpass-api.de/api/interpreter",
                             data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Supply points fetch error: %s", exc)
        return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_earthquakes(lat, lon):
    """Fetch recent earthquakes within 100 km from USGS."""
    try:
        resp = requests.get(
            "https://earthquake.usgs.gov/fdsnws/event/1/query",
            params={"format": "geojson", "latitude": lat, "longitude": lon,
                     "maxradiuskm": 100, "limit": 10},
            timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("USGS earthquake fetch error: %s", exc)
        return {"features": []}

# =============================================================================
# SCORING ENGINE
# =============================================================================
@st.cache_data(ttl=900)
def _compute_shelter_scores(lat, lon):
    """Compute all 7 shelter/habitability dimension scores (each 0-10)."""

    elev = _fetch_elevation(lat, lon)
    soil = _fetch_soil(lat, lon)
    water = _fetch_water_sources(lat, lon)
    weather = _fetch_weather(lat, lon)
    cover = _fetch_natural_cover(lat, lon)
    supply = _fetch_supply_points(lat, lon)
    quakes = _fetch_earthquakes(lat, lon)

    scores, details = {}, {}

    # === DIM 1: Terrain Suitability ==========================================
    grid_elevations = elev.get("grid_elevations", [])
    center_elevation = elev.get("center_elevation", 0.0)
    if len(grid_elevations) >= 4:
        slopes = []
        spacing_m = 440.0
        for i in range(len(grid_elevations) - 1):
            slopes.append(abs(grid_elevations[i + 1] - grid_elevations[i]) / spacing_m * 100)
        avg_slope = _safe_mean(slopes)
        if avg_slope < 2:
            ts, td = 9.5, f"Very flat (slope {avg_slope:.1f}%), ideal for camps"
        elif avg_slope < 5:
            ts, td = 8.0, f"Gentle slope ({avg_slope:.1f}%), suitable"
        elif avg_slope < 10:
            ts, td = 6.5, f"Moderate slope ({avg_slope:.1f}%), needs leveling"
        elif avg_slope < 20:
            ts, td = 4.0, f"Steep ({avg_slope:.1f}%), difficult for camps"
        else:
            ts, td = 2.0, f"Very steep ({avg_slope:.1f}%), unsuitable"
        if center_elevation < 3:
            ts = _clamp(ts - 3); td += "; flood-prone"
        elif center_elevation < 10:
            ts = _clamp(ts - 1.5); td += "; low elevation"
        if center_elevation > 3000:
            ts = _clamp(ts - 2); td += "; high altitude"
    else:
        ts, td = 5.0, "Elevation data limited; approximate assessment"
    scores["Terrain Suitability"] = round(_clamp(ts), 1)
    details["Terrain Suitability"] = td

    # === DIM 2: Ground Stability (SoilGrids v2.0) ===========================
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

    clay_pct, sand_pct, soc_val = _sv("clay", 10), _sv("sand", 10), _sv("soc", 10)
    if clay_pct is not None:
        if clay_pct < 15:
            gs, gd = 9.0, f"Low clay ({clay_pct:.1f}%), stable"
        elif clay_pct < 25:
            gs, gd = 7.5, f"Moderate clay ({clay_pct:.1f}%), stable"
        elif clay_pct < 40:
            gs, gd = 5.0, f"High clay ({clay_pct:.1f}%), swelling risk"
        else:
            gs, gd = 3.0, f"Very high clay ({clay_pct:.1f}%), poor stability"
        if sand_pct is not None and sand_pct > 50:
            gs = _clamp(gs + 1); gd += f"; good drainage (sand {sand_pct:.0f}%)"
        elif sand_pct is not None and sand_pct > 30:
            gs = _clamp(gs + 0.5); gd += f"; moderate drainage (sand {sand_pct:.0f}%)"
        if soc_val is not None and soc_val > 50:
            gs = _clamp(gs - 1); gd += "; high organic, soft ground"
    else:
        gs, gd = 5.0, "Soil data unavailable; on-site testing recommended"
    scores["Ground Stability"] = round(_clamp(gs), 1)
    details["Ground Stability"] = gd

    # === DIM 3: Water Access =================================================
    w_el = (water if isinstance(water, dict) else {}).get("elements", [])
    w_list = w_el if isinstance(w_el, list) else []
    springs = [e for e in w_list if e.get("tags", {}).get("natural") == "spring"]
    rivers = [e for e in w_list if e.get("tags", {}).get("waterway") in ("river", "stream")]
    wells = [e for e in w_list if e.get("tags", {}).get("man_made") == "water_well"]
    drinking = [e for e in w_list if e.get("tags", {}).get("amenity") == "drinking_water"]
    lakes = [e for e in w_list if e.get("tags", {}).get("natural") == "water"]
    nearest_water = _nearest_dist(lat, lon, w_list)
    if not w_list:
        ws, wd = 1.0, "No water sources within 5 km"
    else:
        ws = min(7.0, 2.0 + len(w_list) * 0.5)
        types_n = sum(1 for g in [springs, rivers, wells, drinking, lakes] if g)
        ws = _clamp(ws + types_n * 0.5)
        if nearest_water and nearest_water < 0.5: ws = _clamp(ws + 1.5)
        elif nearest_water and nearest_water < 1.0: ws = _clamp(ws + 1.0)
        elif nearest_water and nearest_water < 2.0: ws = _clamp(ws + 0.5)
        parts = []
        for lbl, lst in [("springs", springs), ("rivers/streams", rivers),
                          ("wells", wells), ("drinking water", drinking),
                          ("water bodies", lakes)]:
            if lst: parts.append(f"{len(lst)} {lbl}")
        wd = ", ".join(parts) + (f", nearest {nearest_water:.1f} km" if nearest_water else "")
    scores["Water Access"] = round(_clamp(ws), 1)
    details["Water Access"] = wd

    # === DIM 4: Weather Exposure =============================================
    cur = (weather if isinstance(weather, dict) else {}).get("current", {})
    daily = (weather if isinstance(weather, dict) else {}).get("daily", {})
    temp_c = cur.get("temperature_2m", 20.0) or 20.0
    wind_spd = cur.get("wind_speed_10m", 0.0) or 0.0
    humidity = cur.get("relative_humidity_2m", 50.0) or 50.0
    d_tmax = daily.get("temperature_2m_max", [])
    d_tmin = daily.get("temperature_2m_min", [])
    d_prec = daily.get("precipitation_sum", [])
    d_wind = daily.get("wind_speed_10m_max", [])
    max_t7 = max((v for v in d_tmax if v is not None), default=temp_c)
    min_t7 = min((v for v in d_tmin if v is not None), default=temp_c)
    tot_p7 = sum(v for v in d_prec if v is not None)
    max_w7 = max((v for v in d_wind if v is not None), default=wind_spd)
    tc = 3.5 if 10 <= temp_c <= 28 else 2.5 if 5 <= temp_c <= 35 else 1.5 if 0 <= temp_c <= 40 else 0.5
    wc = 3.0 if max_w7 < 15 else 2.0 if max_w7 < 30 else 1.0 if max_w7 < 50 else 0.3
    rc = 3.5 if tot_p7 < 10 else 2.5 if tot_p7 < 30 else 1.5 if tot_p7 < 80 else 0.5
    wxs = _clamp(tc + wc + rc)
    wxd = (f"Temp {temp_c:.1f}C ({min_t7:.0f}-{max_t7:.0f}C), "
           f"wind max {max_w7:.0f} km/h, 7d precip {tot_p7:.1f} mm")
    scores["Weather Exposure"] = round(wxs, 1)
    details["Weather Exposure"] = wxd

    # === DIM 5: Natural Cover ================================================
    cov_el = (cover if isinstance(cover, dict) else {}).get("elements", [])
    cov_list = cov_el if isinstance(cov_el, list) else []
    forests = [e for e in cov_list if e.get("tags", {}).get("landuse") == "forest"
               or e.get("tags", {}).get("natural") == "wood"]
    trees = [e for e in cov_list if e.get("tags", {}).get("natural") == "tree"]
    scrub = [e for e in cov_list if e.get("tags", {}).get("natural") == "scrub"]
    hedges = [e for e in cov_list if e.get("tags", {}).get("natural") in ("hedge", "tree_row")]
    nearest_cov = _nearest_dist(lat, lon, cov_list)
    if not cov_list:
        cs, cd = 2.0, "No natural cover within 3 km; exposed area"
    else:
        cs = min(7.0, 2.0 + len(cov_list) * 0.3)
        if forests: cs = _clamp(cs + min(2.0, len(forests) * 0.5))
        if hedges: cs = _clamp(cs + min(1.0, len(hedges) * 0.3))
        if nearest_cov and nearest_cov < 0.5: cs = _clamp(cs + 0.5)
        parts = []
        for lbl, lst in [("forests", forests), ("trees", trees),
                          ("scrubland", scrub), ("hedges/rows", hedges)]:
            if lst: parts.append(f"{len(lst)} {lbl}")
        cd = ", ".join(parts) + (f"; nearest {nearest_cov:.1f} km" if nearest_cov else "")
    scores["Natural Cover"] = round(_clamp(cs), 1)
    details["Natural Cover"] = cd

    # === DIM 6: Supply Access ================================================
    sup_el = (supply if isinstance(supply, dict) else {}).get("elements", [])
    sup_list = sup_el if isinstance(sup_el, list) else []
    fuel = [e for e in sup_list if e.get("tags", {}).get("amenity") == "fuel"]
    hw = [e for e in sup_list if e.get("tags", {}).get("shop") in ("hardware", "doityourself")]
    food = [e for e in sup_list if e.get("tags", {}).get("shop") in
            ("supermarket", "convenience", "grocery") or
            e.get("tags", {}).get("amenity") == "marketplace"]
    nearest_sup = _nearest_dist(lat, lon, sup_list)
    if not sup_list:
        ss, sd = 1.0, "No supply points within 5 km; remote area"
    else:
        ss = min(6.0, 1.5 + len(sup_list) * 0.15)
        ss = _clamp(ss + sum(1 for g in [food, fuel, hw] if g) * 1.0)
        if nearest_sup and nearest_sup < 1.0: ss = _clamp(ss + 1.5)
        elif nearest_sup and nearest_sup < 3.0: ss = _clamp(ss + 0.8)
        parts = []
        if food: parts.append(f"{len(food)} food shops")
        if fuel: parts.append(f"{len(fuel)} fuel stations")
        if hw: parts.append(f"{len(hw)} hardware stores")
        other = len(sup_list) - len(food) - len(fuel) - len(hw)
        if other > 0: parts.append(f"{other} other shops")
        sd = ", ".join(parts) + (f"; nearest {nearest_sup:.1f} km" if nearest_sup else "")
    scores["Supply Access"] = round(_clamp(ss), 1)
    details["Supply Access"] = sd

    # === DIM 7: Hazard Exposure (seismic + weather) ==========================
    feats = (quakes if isinstance(quakes, dict) else {}).get("features", [])
    eq_list = feats if isinstance(feats, list) else []
    mags = [float((f.get("properties") or {}).get("mag")) for f in eq_list
            if (f.get("properties") or {}).get("mag") is not None]
    max_mag = max(mags) if mags else 0.0
    if not eq_list: sc_s = 5.0
    elif max_mag < 2.5: sc_s = 4.0
    elif max_mag < 4.0: sc_s = 3.0
    elif max_mag < 5.5: sc_s = 1.5
    else: sc_s = 0.5
    wx_c = (5.0 if max_w7 < 20 and tot_p7 < 30 else
            3.5 if max_w7 < 40 and tot_p7 < 60 else
            2.0 if max_w7 < 60 and tot_p7 < 120 else 1.0)
    hs = _clamp(sc_s + wx_c)
    hp = []
    if eq_list: hp.append(f"{len(eq_list)} quakes (max M{max_mag:.1f})")
    else: hp.append("No recent seismic activity")
    if max_w7 > 40: hp.append(f"high wind {max_w7:.0f} km/h")
    if tot_p7 > 60: hp.append(f"heavy rain {tot_p7:.0f} mm/7d")
    scores["Hazard Exposure"] = round(_clamp(hs), 1)
    details["Hazard Exposure"] = "; ".join(hp)

    # === OVERALL (weighted) ==================================================
    wsum = sum(scores[d] * DIMENSION_META[d]["weight"] for d in DIMENSION_ORDER)
    wtot = sum(DIMENSION_META[d]["weight"] for d in DIMENSION_ORDER)
    overall = round(wsum / wtot if wtot else 5.0, 1)

    advantages = [f"{d}: {details[d]}" for d in DIMENSION_ORDER if scores[d] >= 7.5]
    challenges = [f"{d}: {details[d]}" for d in DIMENSION_ORDER if scores[d] < 4.0]
    recs = []
    if scores["Terrain Suitability"] < 5: recs.append("Site needs grading/leveling before camp setup.")
    if scores["Ground Stability"] < 5: recs.append("Use geotextile ground cover or elevated platforms.")
    if scores["Water Access"] < 4: recs.append("Bring portable water supply; plan delivery logistics.")
    if scores["Weather Exposure"] < 4: recs.append("Reinforce shelters against wind/rain; insulate for extremes.")
    if scores["Natural Cover"] < 4: recs.append("Deploy windbreaks or shade structures; no natural cover.")
    if scores["Supply Access"] < 4: recs.append("Pre-stage supplies; nearest resupply is distant.")
    if scores["Hazard Exposure"] < 4: recs.append("Establish evacuation plan; notable hazard risk.")
    if not recs: recs.append("Location is generally favorable for shelter establishment.")

    return {
        "scores": scores, "details": details, "overall": overall,
        "verdict": _verdict_label(overall), "verdict_badge": _verdict_badge(overall),
        "advantages": advantages, "challenges": challenges, "recommendations": recs,
        "raw": {
            "weather_current": cur, "weather_daily": daily,
            "water_elements": w_list, "supply_elements": sup_list,
            "cover_elements": cov_list, "earthquakes": eq_list,
            "soil_clay": clay_pct, "soil_sand": sand_pct,
            "center_elevation": center_elevation,
            "max_wind_7d": max_w7, "min_temp_7d": min_t7,
            "max_temp_7d": max_t7, "total_precip_7d": tot_p7,
            "nearest_water_km": nearest_water, "nearest_supply_km": nearest_sup,
        },
    }

# =============================================================================
# PLOTLY RADAR CHART
# =============================================================================
def _build_radar(scores):
    cats = DIMENSION_ORDER + [DIMENSION_ORDER[0]]
    vals = [scores[d] for d in DIMENSION_ORDER] + [scores[DIMENSION_ORDER[0]]]
    cols = [DIMENSION_META[d]["color"] for d in DIMENSION_ORDER]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=cats, fill="toself",
        fillcolor="rgba(245,158,11,0.15)",
        line=dict(color=CLR_ACCENT, width=2.5),
        marker=dict(size=7, color=cols + [cols[0]]),
        hovertemplate="%{theta}: %{r:.1f}/10<extra></extra>"))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 10],
                            tickvals=[2, 4, 6, 8, 10],
                            gridcolor="rgba(255,255,255,0.1)",
                            tickfont=dict(size=10, color=CLR_TEXT_SEC)),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.1)",
                             tickfont=dict(size=11, color=CLR_TEXT))),
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=30, b=30), height=400)
    return fig

# =============================================================================
# FOLIUM MAP
# =============================================================================
def _build_map(lat, lon, raw):
    try:
        import folium
    except ImportError:
        return None
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="OpenStreetMap")
    folium.Marker(
        [lat, lon],
        popup=folium.Popup(
            f"<b>Target Site</b><br/>Lat: {lat:.5f}<br/>Lon: {lon:.5f}<br/>"
            f"Elev: {raw.get('center_elevation', 0):.0f} m", max_width=220),
        icon=folium.Icon(color="red", icon="home", prefix="fa")).add_to(m)

    layer_cfgs = [
        ("water_elements", "#3b82f6", "Water", 5),
        ("supply_elements", "#8b5cf6", "Supply", 4),
        ("cover_elements", "#22c55e", "Cover", 4),
    ]
    for key, color, label, radius in layer_cfgs:
        for el in raw.get(key, []):
            elat = el.get("lat") or (el.get("center") or {}).get("lat")
            elon = el.get("lon") or (el.get("center") or {}).get("lon")
            if elat and elon:
                tags = el.get("tags", {})
                name = tags.get("name", tags.get("shop", tags.get("natural",
                       tags.get("waterway", tags.get("amenity", label)))))
                folium.CircleMarker(
                    [elat, elon], radius=radius, color=color,
                    fill=True, fill_color=color, fill_opacity=0.7,
                    popup=f"{label}: {escape(str(name))}").add_to(m)

    for eq in raw.get("earthquakes", []):
        coords = eq.get("geometry", {}).get("coordinates", [])
        if len(coords) >= 2:
            props = eq.get("properties", {})
            folium.CircleMarker(
                [coords[1], coords[0]], radius=6, color="#ef4444",
                fill=True, fill_color="#ef4444", fill_opacity=0.6,
                popup=f"M{props.get('mag','?')} - {escape(str(props.get('place','')))}").add_to(m)

    folium.Circle([lat, lon], radius=5000, color=CLR_ACCENT,
                  fill=False, weight=1.5, dash_array="5 5").add_to(m)
    return m

# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================
def render_shelter_analysis_tab():
    """Single entry point for the Shelter & Habitability Analysis module."""

    st.markdown(
        f'<div style="background:linear-gradient(135deg,{CLR_BG},{CLR_SURFACE});'
        f'padding:24px 28px;border-radius:12px;border:1px solid {CLR_BORDER};'
        f'margin-bottom:20px;">'
        f'<h2 style="margin:0;color:{CLR_TEXT};font-size:26px;">'
        f'Shelter &amp; Habitability Analysis</h2>'
        f'<p style="margin:6px 0 0;color:{CLR_TEXT_SEC};font-size:14px;">'
        f'Assess terrain suitability for shelter, camps &amp; temporary '
        f'settlements across 7 habitability dimensions.</p></div>',
        unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f",
                          min_value=-90.0, max_value=90.0, key="shelter_lat")
    lon = c2.number_input("Longitude", value=12.5, format="%.4f",
                          min_value=-180.0, max_value=180.0, key="shelter_lon")

    if not st.button("Analyze Shelter Potential", type="primary",
                     key="shelter_btn", use_container_width=True):
        st.info("Enter coordinates and click **Analyze Shelter Potential** "
                "to evaluate the area for shelter establishment.")
        return

    with st.spinner("Assessing habitability across 7 dimensions..."):
        result = _compute_shelter_scores(lat, lon)

    scores = result["scores"]
    det = result["details"]
    overall = result["overall"]
    verdict = result["verdict"]
    badge = result["verdict_badge"]
    raw = result["raw"]
    vc = _verdict_color(overall)

    # -- Verdict banner -------------------------------------------------------
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{vc}22,{CLR_BG});'
        f'padding:24px 28px;border-radius:12px;border:2px solid {vc}88;'
        f'margin:10px 0 24px;text-align:center;">'
        f'<span style="font-size:13px;color:{CLR_TEXT_SEC};text-transform:uppercase;'
        f'letter-spacing:2px;">Overall Habitability Index</span>'
        f'<h1 style="margin:8px 0 4px;color:{vc};font-size:52px;font-weight:800;">'
        f'{overall} / 10</h1>'
        f'<div style="display:inline-block;padding:6px 24px;border-radius:20px;'
        f'background:{vc}33;border:1px solid {vc}66;">'
        f'<span style="font-size:20px;font-weight:700;color:{vc};letter-spacing:2px;">'
        f'{escape(badge)} &mdash; {escape(verdict)}</span></div>'
        f'<p style="margin:10px 0 0;color:{CLR_TEXT_SEC};font-size:13px;">'
        f'Location: {lat:.4f}, {lon:.4f}</p></div>',
        unsafe_allow_html=True)

    # -- Dimension score cards ------------------------------------------------
    st.markdown(f"<h3 style='color:{CLR_TEXT};margin-bottom:12px;'>"
                f"Dimension Scores</h3>", unsafe_allow_html=True)

    for row_dims, ncols in [(DIMENSION_ORDER[:4], 4), (DIMENSION_ORDER[4:], 3)]:
        cols = st.columns(ncols)
        for idx, dim in enumerate(row_dims):
            with cols[idx]:
                st.markdown(_dim_card(dim, scores[dim], det[dim],
                            DIMENSION_META[dim]["color"]), unsafe_allow_html=True)

    # -- Radar chart + key metrics --------------------------------------------
    st.markdown("---")
    ch_col, info_col = st.columns([3, 2])
    with ch_col:
        st.markdown(f"<h4 style='color:{CLR_TEXT};'>Habitability Profile</h4>",
                    unsafe_allow_html=True)
        st.plotly_chart(_build_radar(scores, key="sheana_pchart1"), use_container_width=True,
                        key="shelter_radar")
    with info_col:
        st.markdown(f"<h4 style='color:{CLR_TEXT};'>Key Metrics</h4>",
                    unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        m1.metric("Elevation", f"{raw.get('center_elevation', 0):.0f} m")
        m2.metric("Temperature", f"{raw.get('weather_current',{}).get('temperature_2m','N/A')} C")
        m3, m4 = st.columns(2)
        m3.metric("Wind (max 7d)", f"{raw.get('max_wind_7d', 0):.0f} km/h")
        m4.metric("Precip (7d)", f"{raw.get('total_precip_7d', 0):.1f} mm")
        m5, m6 = st.columns(2)
        nw, ns = raw.get("nearest_water_km"), raw.get("nearest_supply_km")
        m5.metric("Nearest Water", f"{nw:.1f} km" if nw else "N/A")
        m6.metric("Nearest Supply", f"{ns:.1f} km" if ns else "N/A")
        m7, m8 = st.columns(2)
        m7.metric("Clay", f"{raw['soil_clay']:.1f}%" if raw.get("soil_clay") is not None else "N/A")
        m8.metric("Sand", f"{raw['soil_sand']:.1f}%" if raw.get("soil_sand") is not None else "N/A")

    # -- Advantages & Challenges ----------------------------------------------
    st.markdown("---")
    a_col, c_col = st.columns(2)
    for col, items, title, clr in [
        (a_col, result["advantages"], "Advantages", CLR_SUITABLE),
        (c_col, result["challenges"], "Challenges", CLR_UNSUITABLE),
    ]:
        with col:
            st.markdown(f"<h4 style='color:{clr};'>{title}</h4>",
                        unsafe_allow_html=True)
            if items:
                for item in items:
                    st.markdown(
                        f"<div style='background:{clr}15;padding:8px 12px;"
                        f"border-radius:6px;border-left:3px solid {clr};"
                        f"margin-bottom:6px;color:{CLR_TEXT};font-size:13px;'>"
                        f"{escape(item)}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='color:{CLR_TEXT_SEC};font-size:13px;'>"
                            f"None identified.</div>", unsafe_allow_html=True)

    # -- Recommendations ------------------------------------------------------
    st.markdown("---")
    st.markdown(f"<h4 style='color:{CLR_TEXT};'>Recommendations</h4>",
                unsafe_allow_html=True)
    for rec in result["recommendations"]:
        st.markdown(
            f"<div style='background:{CLR_CARD};padding:10px 14px;"
            f"border-radius:8px;border:1px solid {CLR_BORDER};"
            f"margin-bottom:8px;color:{CLR_TEXT};font-size:13px;'>"
            f"&#8226; {escape(rec)}</div>", unsafe_allow_html=True)

    # -- Map ------------------------------------------------------------------
    st.markdown("---")
    st.markdown(f"<h4 style='color:{CLR_TEXT};'>Shelter Area Map</h4>",
                unsafe_allow_html=True)
    st.caption("Blue = water | Purple = supply | Green = cover | Red = earthquakes")
    shelter_map = _build_map(lat, lon, raw)
    if shelter_map is not None:
        try:
            from streamlit_folium import st_folium
            st_folium(shelter_map, width=None, height=500, key="shelter_map")
        except ImportError:
            try:
                from streamlit.components.v1 import html as st_html
                st_html(shelter_map._repr_html_(), height=500)
            except Exception:
                st.info("Install folium and streamlit-folium for map display.")
    else:
        st.info("Install `folium` for map visualization: `pip install folium`")

    # -- Detailed breakdown expander ------------------------------------------
    st.markdown("---")
    with st.expander("Detailed Dimension Breakdown", expanded=False):
        for dim in DIMENSION_ORDER:
            s, d = scores[dim], det[dim]
            c = DIMENSION_META[dim]["color"]
            sc = _verdict_color(s)
            w = DIMENSION_META[dim]["weight"]
            st.markdown(
                f'<div style="background:{CLR_SURFACE};padding:12px 16px;'
                f'border-radius:8px;border:1px solid {c}33;margin-bottom:8px;">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;flex-wrap:wrap;">'
                f'<div><span style="font-weight:700;color:{c};font-size:14px;">'
                f'{escape(dim)}</span>'
                f'<span style="color:{CLR_TEXT_SEC};font-size:12px;margin-left:8px;">'
                f'Weight: {w:.0%}</span></div>'
                f'<div><span style="font-size:22px;font-weight:800;color:{sc};">'
                f'{s}/10</span>'
                f'<span style="color:{CLR_TEXT_SEC};font-size:12px;margin-left:8px;">'
                f'Contrib: {s * w:.2f}</span></div></div>'
                f'<div style="margin-top:6px;color:{CLR_TEXT};font-size:13px;">'
                f'{escape(d)}</div>'
                f'<div style="margin-top:8px;background:{CLR_BG};border-radius:4px;'
                f'height:8px;overflow:hidden;">'
                f'<div style="width:{s * 10:.0f}%;height:100%;'
                f'background:linear-gradient(90deg,{c},{sc});border-radius:4px;">'
                f'</div></div></div>', unsafe_allow_html=True)

    # -- 7-day weather forecast expander --------------------------------------
    with st.expander("7-Day Weather Forecast", expanded=False):
        dd = raw.get("weather_daily", {})
        dm, dn = dd.get("temperature_2m_max", []), dd.get("temperature_2m_min", [])
        dp, dw = dd.get("precipitation_sum", []), dd.get("wind_speed_10m_max", [])
        if dm:
            days = list(range(1, len(dm) + 1))
            fig = go.Figure()
            fig.add_trace(go.Bar(x=days, y=[p or 0 for p in dp],
                                 name="Precip (mm)", marker_color="#3b82f6",
                                 opacity=0.6, yaxis="y2"))
            fig.add_trace(go.Scatter(x=days, y=dm, name="Max Temp",
                                     line=dict(color="#ef4444", width=2), mode="lines+markers"))
            fig.add_trace(go.Scatter(x=days, y=dn, name="Min Temp",
                                     line=dict(color="#3b82f6", width=2), mode="lines+markers"))
            fig.add_trace(go.Scatter(x=days, y=[w or 0 for w in dw], name="Wind (km/h)",
                                     line=dict(color="#f59e0b", width=2, dash="dot"),
                                     mode="lines+markers", yaxis="y3"))
            fig.update_layout(
                xaxis=dict(title="Day", tickvals=days, ticktext=[f"D{d}" for d in days]),
                yaxis=dict(title="Temp (C)", gridcolor="rgba(255,255,255,0.05)"),
                yaxis2=dict(title="Precip", overlaying="y", side="right", showgrid=False),
                yaxis3=dict(title="Wind", overlaying="y", side="right",
                            position=0.95, showgrid=False),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=CLR_TEXT), legend=dict(orientation="h", y=-0.2),
                height=350, margin=dict(l=50, r=80, t=20, b=60))
            st.plotly_chart(fig, use_container_width=True, key="shelter_wx_chart")
        else:
            st.info("Daily forecast data not available.")

    # -- Seismic activity expander --------------------------------------------
    with st.expander("Recent Seismic Activity (100 km)", expanded=False):
        eq_list = raw.get("earthquakes", [])
        if eq_list:
            for eq in eq_list:
                props = eq.get("properties", {})
                try:
                    ts = datetime.datetime.utcfromtimestamp(props.get("time", 0) / 1000)
                    tstr = ts.strftime("%Y-%m-%d %H:%M UTC")
                except Exception:
                    tstr = "Unknown"
                st.markdown(
                    f"<div style='background:{CLR_SURFACE};padding:8px 12px;"
                    f"border-radius:6px;border-left:3px solid #ef4444;"
                    f"margin-bottom:6px;color:{CLR_TEXT};font-size:13px;'>"
                    f"<b>M{props.get('mag','?')}</b> &mdash; "
                    f"{escape(str(props.get('place','Unknown')))} "
                    f"<span style='color:{CLR_TEXT_SEC};'>({tstr})</span></div>",
                    unsafe_allow_html=True)
        else:
            st.success("No earthquakes within 100 km in recent history.")

    # -- Raw JSON export ------------------------------------------------------
    with st.expander("Raw Analysis Data (JSON)", expanded=False):
        st.code(json.dumps({
            "location": {"latitude": lat, "longitude": lon},
            "overall_score": overall, "verdict": verdict, "badge": badge,
            "dimension_scores": dict(scores), "dimension_details": dict(det),
            "advantages": result["advantages"],
            "challenges": result["challenges"],
            "recommendations": result["recommendations"],
        }, indent=2, ensure_ascii=False), language="json")
