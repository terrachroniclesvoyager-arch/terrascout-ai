"""
Construction Feasibility AI module for TerraScout AI.

Evaluates how suitable a location is for building construction projects
across seven critical dimensions:

  1. Foundation Soil     -- Clay, sand, bulk density, bearing capacity
  2. Terrain Flatness    -- Slope analysis and cut/fill estimation
  3. Seismic Zone        -- Earthquake frequency and magnitude
  4. Equipment Access    -- Road network quality and width
  5. Utility Availability-- Power lines, water, telecom, pipelines
  6. Weather Conditions  -- Working days, freeze-thaw cycles
  7. Existing Structures -- Building density, zoning context

APIs used (all free, no key required):
  - ISRIC SoilGrids v2.0
  - Open Topo Data (SRTM 90m)
  - USGS Earthquake Catalog
  - Overpass API (OpenStreetMap)
  - Open-Meteo Weather API

Overall Feasibility Scale:
  IDEAL (9-10) | GOOD (7-8) | FEASIBLE (5-6) | CHALLENGING (3-4) | UNSUITABLE (0-2)
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
import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

# ── Theme ────────────────────────────────────────────────────────────────────
CLR_BG, CLR_SURFACE, CLR_CARD = "#1a1a2e", "#16213e", "#0f3460"
CLR_BORDER, CLR_TEXT, CLR_TEXT_SEC = "#1a4080", "#e8ecf4", "#8b97b0"
CLR_ACCENT = "#f59e0b"
CLR_IDEAL, CLR_GOOD, CLR_FEASIBLE = "#10b981", "#22c55e", "#f59e0b"
CLR_CHALLENGING, CLR_UNSUITABLE = "#f97316", "#ef4444"

# ── Dimension definitions ────────────────────────────────────────────────────
DIMENSIONS = {
    "foundation_soil":      {"name": "Foundation Soil",      "color": "#a16207", "icon": "globe",      "weight": 0.18},
    "terrain_flatness":     {"name": "Terrain Flatness",     "color": "#6366f1", "icon": "area-chart", "weight": 0.15},
    "seismic_zone":         {"name": "Seismic Zone",         "color": "#ef4444", "icon": "bolt",       "weight": 0.12},
    "equipment_access":     {"name": "Equipment Access",     "color": "#3b82f6", "icon": "truck",      "weight": 0.15},
    "utility_availability": {"name": "Utility Availability", "color": "#8b5cf6", "icon": "plug",       "weight": 0.13},
    "weather_conditions":   {"name": "Weather Conditions",   "color": "#06b6d4", "icon": "cloud",      "weight": 0.12},
    "existing_structures":  {"name": "Existing Structures",  "color": "#ec4899", "icon": "building",   "weight": 0.15},
}
FEAS_LABELS = [(9, "IDEAL", CLR_IDEAL), (7, "GOOD", CLR_GOOD),
               (5, "FEASIBLE", CLR_FEASIBLE), (3, "CHALLENGING", CLR_CHALLENGING),
               (0, "UNSUITABLE", CLR_UNSUITABLE)]

# ── Helpers ──────────────────────────────────────────────────────────────────

def _clamp(v, lo=0.0, hi=10.0):
    """Clamp a numeric value to [lo, hi]. Returns lo if v is None."""
    return max(lo, min(hi, float(v))) if v is not None else lo


def _feas_color(s):
    """Return the hex colour for a feasibility score (0-10)."""
    for t, _, c in FEAS_LABELS:
        if s >= t:
            return c
    return CLR_UNSUITABLE


def _feas_label(s):
    """Return the text label for a feasibility score (0-10)."""
    for t, l, _ in FEAS_LABELS:
        if s >= t:
            return l
    return "UNSUITABLE"


def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ── Data fetching (all cached, all with timeout + try/except) ────────────────

@st.cache_data(ttl=900)
def _fetch_soilgrids(lat, lon):
    """Fetch SoilGrids v2.0 data for foundation analysis."""
    url = (f"https://rest.isric.org/soilgrids/v2.0/properties/query"
           f"?lon={lon}&lat={lat}&property=clay&property=sand&property=bdod"
           f"&property=soc&depth=0-5cm&value=mean")
    try:
        r = requests.get(url, timeout=10); r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("SoilGrids error: %s", e); return {}


@st.cache_data(ttl=900)
def _fetch_elevation(lat, lon):
    """Fetch a 5x5 elevation grid from Open Topo Data for slope analysis."""
    pts = "|".join(f"{lat+dy*0.003},{lon+dx*0.003}" for dy in range(-2,3) for dx in range(-2,3))
    try:
        r = requests.get("https://api.opentopodata.org/v1/srtm90m",
                         params={"locations": pts}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Elevation error: %s", e); return {}


@st.cache_data(ttl=900)
def _fetch_seismic(lat, lon):
    """Fetch recent earthquake data from USGS within 200 km."""
    url = (f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
           f"&latitude={lat}&longitude={lon}&maxradiuskm=200&limit=30")
    try:
        r = requests.get(url, timeout=10); r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("USGS error: %s", e); return {}


@st.cache_data(ttl=900)
def _fetch_access_roads(lat, lon, radius=2000):
    """Fetch road network data from Overpass API for access analysis."""
    q = f'[out:json][timeout:25];(way["highway"~"motorway|trunk|primary|secondary|tertiary|residential|service|unclassified"](around:{radius},{lat},{lon}););out body;'
    try:
        r = requests.post("https://overpass-api.de/api/interpreter",
                          data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Roads error: %s", e); return {"elements": []}


@st.cache_data(ttl=900)
def _fetch_utilities(lat, lon, radius=1500):
    """Fetch nearby utility infrastructure from Overpass API."""
    q = f"""[out:json][timeout:25];(
      way["power"~"line|minor_line|cable"](around:{radius},{lat},{lon});
      node["power"~"tower|pole|substation|transformer"](around:{radius},{lat},{lon});
      way["man_made"="pipeline"](around:{radius},{lat},{lon});
      node["man_made"~"water_well|water_tower|pumping_station"](around:{radius},{lat},{lon});
      way["waterway"="canal"](around:{radius},{lat},{lon});
      node["telecom"](around:{radius},{lat},{lon});way["telecom"](around:{radius},{lat},{lon});
      node["amenity"~"water_point|drinking_water"](around:{radius},{lat},{lon});
    );out body;"""
    try:
        r = requests.post("https://overpass-api.de/api/interpreter",
                          data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Utilities error: %s", e); return {"elements": []}


@st.cache_data(ttl=900)
def _fetch_weather(lat, lon):
    """Fetch 30-day weather history from Open-Meteo."""
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
           f"&past_days=30&timezone=auto")
    try:
        r = requests.get(url, timeout=10); r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Weather error: %s", e); return {}


@st.cache_data(ttl=900)
def _fetch_structures(lat, lon, radius=1500):
    """Fetch existing buildings and land-use from Overpass API."""
    q = f'[out:json][timeout:25];(way["building"](around:{radius},{lat},{lon});relation["building"](around:{radius},{lat},{lon});way["landuse"](around:{radius},{lat},{lon});relation["landuse"](around:{radius},{lat},{lon}););out body;'
    try:
        r = requests.post("https://overpass-api.de/api/interpreter",
                          data={"data": q}, timeout=10)
        r.raise_for_status(); return r.json()
    except Exception as e:
        logger.warning("Structures error: %s", e); return {"elements": []}

# ── Scoring functions ────────────────────────────────────────────────────────

def _score_foundation_soil(soil_data):
    """Score foundation soil quality 0-10 and return detail dict."""
    raw_props = (soil_data if isinstance(soil_data, dict) else {}).get("properties", {})
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
    clay, sand = _sv("clay"), _sv("sand")
    bdod, soc = _sv("bdod", div=100), _sv("soc")
    det = {"clay_pct": clay, "sand_pct": sand, "bulk_density": bdod, "organic_carbon": soc}
    score = 5.0
    if clay is not None and sand is not None:
        if clay > 40: score -= 2.5
        elif clay > 25: score -= 1.0
        elif clay < 5: score -= 0.5
        if sand > 70: score -= 1.0
        elif 20 < sand < 50: score += 1.0
    if bdod is not None:
        if bdod > 1.5: score += 2.0
        elif bdod > 1.2: score += 1.0
        elif bdod < 0.8: score -= 1.5
    if soc is not None:
        if soc > 5: score -= 2.0
        elif soc > 3: score -= 1.0
        elif soc < 1: score += 0.5
    bearing = 100.0
    if clay is not None: bearing += max(0, 30-clay)*2
    if bdod is not None: bearing += bdod*80
    if soc is not None: bearing -= soc*15
    det["bearing_capacity_kpa"] = round(max(20, bearing), 0)
    det["shrink_swell_risk"] = "High" if (clay or 0) > 35 else ("Moderate" if (clay or 0) > 20 else "Low")
    return _clamp(score), det


def _score_terrain(elev_data):
    """Score terrain flatness 0-10 from elevation grid. Flat = higher score."""
    results = (elev_data if isinstance(elev_data, dict) else {}).get("results", [])
    elevs = [float(r.get("elevation")) for r in (results if isinstance(results, list) else [])
             if isinstance(r, dict) and r.get("elevation") is not None]
    if len(elevs) < 3:
        return 5.0, {"slope_pct": None, "elev_range_m": None, "center_elev": None, "cut_fill": "Unknown"}
    center_elev, elev_range = elevs[len(elevs)//2], max(elevs)-min(elevs)
    slope_pct = (elev_range / max(0.003*111000*4, 1)) * 100
    det = {"slope_pct": round(slope_pct, 2), "elev_range_m": round(elev_range, 1),
           "center_elev": round(center_elev, 1)}
    if slope_pct < 2:    score, det["cut_fill"] = 9.5, "Minimal"
    elif slope_pct < 5:  score, det["cut_fill"] = 8.0, "Low"
    elif slope_pct < 10: score, det["cut_fill"] = 6.0, "Moderate"
    elif slope_pct < 20: score, det["cut_fill"] = 4.0, "Significant"
    elif slope_pct < 35: score, det["cut_fill"] = 2.5, "Major"
    else:                score, det["cut_fill"] = 1.0, "Extreme"
    return _clamp(score), det


def _score_seismic(seis_data):
    """Score seismic safety 0-10 (higher = safer for construction)."""
    features = (seis_data if isinstance(seis_data, dict) else {}).get("features", [])
    det = {"earthquake_count": len(features), "max_magnitude": 0, "avg_magnitude": 0, "seismic_zone": "Unknown"}
    if not features:
        det["seismic_zone"] = "Low"; return 9.0, det
    mags = [float(f.get("properties", {}).get("mag")) for f in features
            if isinstance(f, dict) and f.get("properties", {}).get("mag") is not None]
    if not mags:
        det["seismic_zone"] = "Low"; return 8.5, det
    det["max_magnitude"], det["avg_magnitude"] = round(max(mags), 1), round(sum(mags)/len(mags), 1)
    cp = min(4.0, len(mags)*0.15)
    mm = max(mags)
    if mm >= 6:   mp, det["seismic_zone"] = 4.0, "Very High"
    elif mm >= 5: mp, det["seismic_zone"] = 2.5, "High"
    elif mm >= 4: mp, det["seismic_zone"] = 1.5, "Moderate"
    elif mm >= 3: mp, det["seismic_zone"] = 0.5, "Low-Moderate"
    else:         mp, det["seismic_zone"] = 0.0, "Low"
    return _clamp(10.0-cp-mp), det


def _score_access(road_data):
    """Score equipment access quality 0-10 based on road type and width."""
    els = (road_data if isinstance(road_data, dict) else {}).get("elements", [])
    det = {"total_roads": 0, "major_roads": 0, "minor_roads": 0, "service_roads": 0, "access_quality": "None"}
    if not els: return 1.0, det
    major = minor = service = wide = 0
    for el in els:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        hw = tags.get("highway", "")
        if hw in ("motorway", "trunk", "primary"): major += 1
        elif hw in ("secondary", "tertiary"): minor += 1
        elif hw in ("service", "residential", "unclassified"): service += 1
        try:
            if float(str(tags.get("width", "")).replace("m", "").strip()) >= 6: wide += 1
        except (ValueError, TypeError): pass
    det.update(total_roads=len(els), major_roads=major, minor_roads=minor, service_roads=service)
    score = 2.0
    if major > 0: score += 3.0
    if minor > 0: score += 2.0
    if service > 3: score += 1.5
    elif service > 0: score += 1.0
    if wide > 2: score += 1.0
    for thr, lbl in [(8, "Excellent"), (6, "Good"), (4, "Moderate"), (2, "Limited")]:
        if score >= thr: det["access_quality"] = lbl; break
    else:
        det["access_quality"] = "Poor"
    return _clamp(score), det


def _score_utilities(util_data):
    """Score utility availability 0-10 based on nearby infrastructure."""
    els = (util_data if isinstance(util_data, dict) else {}).get("elements", [])
    pw_l = pw_n = water = tcom = pipes = 0
    for el in els:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        pw, mm, am, tc = tags.get("power",""), tags.get("man_made",""), tags.get("amenity",""), tags.get("telecom","")
        if pw in ("line","minor_line","cable"): pw_l += 1
        if pw in ("tower","pole","substation","transformer"): pw_n += 1
        if mm == "pipeline": pipes += 1
        if mm in ("water_well","water_tower","pumping_station"): water += 1
        if am in ("water_point","drinking_water"): water += 1
        if tc: tcom += 1
    det = {"power_lines": pw_l, "power_nodes": pw_n, "water_infra": water, "telecom": tcom, "pipelines": pipes}
    score = 1.0
    if pw_l > 0 or pw_n > 0: score += 3.0
    if water > 0: score += 2.5
    if tcom > 0: score += 1.5
    if pipes > 0: score += 1.5
    if pw_n > 3: score += 0.5
    return _clamp(score), det


def _score_weather(wx_data):
    """Score construction-friendly weather 0-10 based on working days."""
    daily = (wx_data if isinstance(wx_data, dict) else {}).get("daily", {})
    t_max, t_min, precip = daily.get("temperature_2m_max",[]), daily.get("temperature_2m_min",[]), daily.get("precipitation_sum",[])
    if not t_max or not precip:
        return 5.0, {"working_days": None, "avg_temp": None, "rain_days": None, "freeze_thaw_cycles": None}
    wd = rd = ft = 0; temps = []
    for i in range(len(t_max)):
        mx = t_max[i] if i < len(t_max) else None
        mn = t_min[i] if i < len(t_min) else None
        pr = precip[i] if i < len(precip) else None
        if mx is None or pr is None: continue
        temps.append((mx + (mn or mx)) / 2)
        ok = True
        if pr > 5: rd += 1; ok = False
        if mx > 40: ok = False
        if mn is not None and mn < -10: ok = False
        if ok: wd += 1
        if mn is not None and mn < 0 < mx: ft += 1
    total = max(len(t_max), 1); wpct = (wd/total)*100
    det = {"working_days": wd, "total_days": total, "working_pct": round(wpct, 1),
           "avg_temp": round(sum(temps)/len(temps), 1) if temps else None,
           "rain_days": rd, "freeze_thaw_cycles": ft}
    score = wpct / 10.0
    if ft > 10: score -= 1.5
    elif ft > 5: score -= 0.5
    return _clamp(score), det


def _score_structures(struct_data):
    """Score existing structures context 0-10. Moderate density is best."""
    els = (struct_data if isinstance(struct_data, dict) else {}).get("elements", [])
    bldgs, zones = [], []
    for el in els:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        if tags.get("building"): bldgs.append(tags)
        if tags.get("landuse"): zones.append(tags["landuse"])
    bc = len(bldgs)
    res_b = sum(1 for b in bldgs if b.get("building") in ("residential","apartments","house","yes"))
    com_b = sum(1 for b in bldgs if b.get("building") in ("commercial","retail","office"))
    ind_b = sum(1 for b in bldgs if b.get("building") in ("industrial","warehouse"))
    det = {"building_count": bc, "residential_buildings": res_b, "commercial_buildings": com_b,
           "industrial_buildings": ind_b, "has_residential_zone": "residential" in zones,
           "has_commercial_zone": "commercial" in zones, "has_industrial_zone": "industrial" in zones}
    if bc == 0:     score, det["density_class"] = 4.0, "Undeveloped"
    elif bc < 20:   score, det["density_class"] = 7.0, "Low"
    elif bc < 80:   score, det["density_class"] = 9.0, "Moderate"
    elif bc < 200:  score, det["density_class"] = 6.5, "High"
    else:           score, det["density_class"] = 3.5, "Very High"
    if det["has_residential_zone"] or det["has_commercial_zone"]: score += 0.5
    return _clamp(score), det


# ── Main assessment ──────────────────────────────────────────────────────────

@st.cache_data(ttl=900)
def _compute_construction_assessment(lat, lon):
    """Run the full 7-dimension construction feasibility assessment."""
    soil = _fetch_soilgrids(lat, lon)
    elev = _fetch_elevation(lat, lon)
    seis = _fetch_seismic(lat, lon)
    roads = _fetch_access_roads(lat, lon)
    utils = _fetch_utilities(lat, lon)
    wx = _fetch_weather(lat, lon)
    structs = _fetch_structures(lat, lon)
    scores, details = {}, {}
    scores["foundation_soil"], details["foundation_soil"] = _score_foundation_soil(soil)
    scores["terrain_flatness"], details["terrain_flatness"] = _score_terrain(elev)
    scores["seismic_zone"], details["seismic_zone"] = _score_seismic(seis)
    scores["equipment_access"], details["equipment_access"] = _score_access(roads)
    scores["utility_availability"], details["utility_availability"] = _score_utilities(utils)
    scores["weather_conditions"], details["weather_conditions"] = _score_weather(wx)
    scores["existing_structures"], details["existing_structures"] = _score_structures(structs)
    overall = round(_clamp(sum(scores[k]*DIMENSIONS[k]["weight"] for k in DIMENSIONS)), 1)
    recs = []
    if overall >= 7:
        recs = [("Heavy Construction", "Multi-story buildings, commercial complexes"),
                ("Medium Construction", "2-3 story residential, small commercial"),
                ("Light Construction", "Single-story, prefab, modular buildings")]
    elif overall >= 5:
        recs = [("Medium Construction", "2-3 story with reinforced foundation"),
                ("Light Construction", "Single-story, prefab, modular buildings")]
    elif overall >= 3:
        recs = [("Light Construction", "Single-story with special foundation design")]
    else:
        recs = [("Not Recommended", "Site requires major remediation before construction")]
    if overall >= 8:   cf, cl = 1.0, "Standard"
    elif overall >= 6: cf, cl = 1.3, "Moderate Premium"
    elif overall >= 4: cf, cl = 1.7, "Significant Premium"
    elif overall >= 2: cf, cl = 2.5, "High Premium"
    else:              cf, cl = 4.0, "Extreme Premium"
    return {"overall": overall, "label": _feas_label(overall), "scores": scores,
            "details": details, "recommendations": recs, "cost_factor": cf, "cost_label": cl}

# ── UI rendering ─────────────────────────────────────────────────────────────
def _render_gauge(overall, label):
    color = _feas_color(overall)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=overall,
        title={"text": f"<b>{label}</b>", "font": {"size": 22, "color": CLR_TEXT}},
        number={"font": {"size": 48, "color": color}, "suffix": "/10"},
        gauge={"axis": {"range": [0,10], "tickwidth": 2, "tickcolor": CLR_BORDER,
                        "dtick": 2, "tickfont": {"color": CLR_TEXT_SEC}},
               "bar": {"color": color, "thickness": 0.7},
               "bgcolor": CLR_SURFACE, "borderwidth": 2, "bordercolor": CLR_BORDER,
               "steps": [{"range": [0,3], "color": "rgba(239,68,68,0.15)"},
                         {"range": [3,5], "color": "rgba(249,115,22,0.15)"},
                         {"range": [5,7], "color": "rgba(245,158,11,0.15)"},
                         {"range": [7,9], "color": "rgba(34,197,94,0.15)"},
                         {"range": [9,10], "color": "rgba(16,185,129,0.15)"}],
               "threshold": {"line": {"color": "#fff", "width": 3}, "thickness": 0.8, "value": overall}}))
    fig.update_layout(height=280, margin=dict(t=60,b=20,l=40,r=40),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font={"color": CLR_TEXT})
    st.plotly_chart(fig, use_container_width=True, key="const_gauge")

def _card_html(dim, score):
    c = _feas_color(score)
    return f"""<div style="background:{CLR_CARD};border:1px solid {c}40;border-radius:12px;
    padding:16px;text-align:center;min-height:140px;">
    <div style="font-size:13px;color:{CLR_TEXT_SEC};margin-bottom:4px;">
    <i class="fa fa-{dim['icon']}"></i> {dim['name']}</div>
    <div style="font-size:32px;font-weight:700;color:{c};">{score:.1f}</div>
    <div style="font-size:11px;color:{CLR_TEXT_SEC};">{_feas_label(score)}</div>
    <div style="margin-top:6px;height:4px;background:{CLR_SURFACE};border-radius:2px;">
    <div style="width:{score*10}%;height:100%;background:{c};border-radius:2px;"></div>
    </div></div>"""

def _render_metric_cards(scores):
    dims = list(DIMENSIONS.items())
    for row_start in (0, 4):
        cols = st.columns(4)
        for i, (key, dim) in enumerate(dims[row_start:row_start+4]):
            with cols[i]:
                st.markdown(_card_html(dim, scores[key]), unsafe_allow_html=True)

def _render_radar_chart(scores):
    cats = [DIMENSIONS[k]["name"] for k in DIMENSIONS]
    vals = [scores[k] for k in DIMENSIONS]
    clrs = [DIMENSIONS[k]["color"] for k in DIMENSIONS]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals+[vals[0]], theta=cats+[cats[0]], fill="toself",
        fillcolor="rgba(245,158,11,0.15)", line=dict(color=CLR_ACCENT, width=2),
        marker=dict(size=8, color=clrs+[clrs[0]]), name="Feasibility"))
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)",
                   radialaxis=dict(visible=True, range=[0,10], showticklabels=True,
                                   tickfont=dict(size=10, color=CLR_TEXT_SEC), gridcolor=CLR_BORDER),
                   angularaxis=dict(tickfont=dict(size=11, color=CLR_TEXT), gridcolor=CLR_BORDER)),
        showlegend=False, height=420, margin=dict(t=40,b=40,l=60,r=60),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color=CLR_TEXT))
    st.plotly_chart(fig, use_container_width=True, key="const_radar")

def _render_detail_panels(details):
    with st.expander("Foundation Soil Details", expanded=False):
        fd = details.get("foundation_soil", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Clay %", fd.get("clay_pct", "N/A") if fd.get("clay_pct") is not None else "N/A")
        c2.metric("Sand %", fd.get("sand_pct", "N/A") if fd.get("sand_pct") is not None else "N/A")
        c3.metric("Bulk Density", fd.get("bulk_density", "N/A") if fd.get("bulk_density") is not None else "N/A")
        c4.metric("Bearing (kPa)", f"{fd.get('bearing_capacity_kpa', 'N/A')}")
        st.info(f"Shrink-Swell Risk: **{fd.get('shrink_swell_risk','Unknown')}** | Organic Carbon: {fd.get('organic_carbon','N/A')}")
    with st.expander("Terrain Flatness Details", expanded=False):
        td = details.get("terrain_flatness", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Slope %", f"{td.get('slope_pct','N/A')}")
        c2.metric("Elev Range", f"{td.get('elev_range_m','N/A')} m")
        c3.metric("Center Elev", f"{td.get('center_elev','N/A')} m")
        c4.metric("Cut/Fill", f"{td.get('cut_fill','N/A')}")
    with st.expander("Seismic Zone Details", expanded=False):
        sd = details.get("seismic_zone", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Earthquakes", f"{sd.get('earthquake_count',0)}")
        c2.metric("Max Magnitude", f"{sd.get('max_magnitude',0)}")
        c3.metric("Avg Magnitude", f"{sd.get('avg_magnitude',0)}")
        c4.metric("Seismic Zone", f"{sd.get('seismic_zone','Unknown')}")
    with st.expander("Equipment Access Details", expanded=False):
        ad = details.get("equipment_access", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Total Roads", f"{ad.get('total_roads',0)}")
        c2.metric("Major Roads", f"{ad.get('major_roads',0)}")
        c3.metric("Minor Roads", f"{ad.get('minor_roads',0)}")
        c4.metric("Access Quality", f"{ad.get('access_quality','Unknown')}")
    with st.expander("Utility Availability Details", expanded=False):
        ud = details.get("utility_availability", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Power Lines", f"{ud.get('power_lines',0)}")
        c2.metric("Power Nodes", f"{ud.get('power_nodes',0)}")
        c3.metric("Water Infra", f"{ud.get('water_infra',0)}")
        c4.metric("Telecom", f"{ud.get('telecom',0)}")
    with st.expander("Weather Conditions Details", expanded=False):
        wd = details.get("weather_conditions", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Working Days", f"{wd.get('working_days','N/A')}/{wd.get('total_days','N/A')}")
        c2.metric("Working %", f"{wd.get('working_pct','N/A')}%")
        c3.metric("Rain Days", f"{wd.get('rain_days','N/A')}")
        c4.metric("Freeze-Thaw", f"{wd.get('freeze_thaw_cycles','N/A')}")
        if wd.get("avg_temp") is not None:
            st.info(f"Average Temperature: **{wd['avg_temp']}C**")
    with st.expander("Existing Structures Details", expanded=False):
        ed = details.get("existing_structures", {})
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Buildings", f"{ed.get('building_count',0)}")
        c2.metric("Residential", f"{ed.get('residential_buildings',0)}")
        c3.metric("Commercial", f"{ed.get('commercial_buildings',0)}")
        c4.metric("Density", f"{ed.get('density_class','Unknown')}")
        zn = []
        if ed.get("has_residential_zone"): zn.append("Residential")
        if ed.get("has_commercial_zone"): zn.append("Commercial")
        if ed.get("has_industrial_zone"): zn.append("Industrial")
        st.info(f"Zoning detected: **{', '.join(zn) if zn else 'None identified'}**")

def _render_cost_difficulty(cost_factor, cost_label, overall):
    color = _feas_color(overall)
    bw = min(100, cost_factor/4.0*100)
    st.markdown(f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};border-radius:12px;padding:20px;margin:10px 0;">
    <div style="font-size:16px;font-weight:600;color:{CLR_TEXT};margin-bottom:10px;">Cost Difficulty Estimate</div>
    <div style="display:flex;align-items:center;gap:20px;">
    <div style="flex:1;"><div style="font-size:13px;color:{CLR_TEXT_SEC};margin-bottom:4px;">Multiplier</div>
    <div style="font-size:36px;font-weight:700;color:{color};">{cost_factor:.1f}x</div>
    <div style="font-size:12px;color:{CLR_TEXT_SEC};">{cost_label}</div></div>
    <div style="flex:2;"><div style="font-size:12px;color:{CLR_TEXT_SEC};margin-bottom:6px;">Relative Cost Scale</div>
    <div style="height:20px;background:{CLR_SURFACE};border-radius:10px;overflow:hidden;">
    <div style="width:{bw}%;height:100%;background:linear-gradient(90deg,{CLR_IDEAL},{color});border-radius:10px;"></div></div>
    <div style="display:flex;justify-content:space-between;margin-top:4px;">
    <span style="font-size:10px;color:{CLR_TEXT_SEC};">1.0x Standard</span>
    <span style="font-size:10px;color:{CLR_TEXT_SEC};">4.0x Extreme</span></div></div></div></div>""",
    unsafe_allow_html=True)

def _render_recommendations(recommendations):
    html = f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};border-radius:12px;padding:20px;margin:10px 0;">
    <div style="font-size:16px;font-weight:600;color:{CLR_TEXT};margin-bottom:12px;">Construction Type Recommendations</div>"""
    for rtype, rdesc in recommendations:
        if "Heavy" in rtype: ic, ico = CLR_IDEAL, "building"
        elif "Medium" in rtype: ic, ico = CLR_GOOD, "home"
        elif "Light" in rtype: ic, ico = CLR_FEASIBLE, "cube"
        else: ic, ico = CLR_UNSUITABLE, "times-circle"
        html += f"""<div style="display:flex;align-items:center;gap:12px;padding:8px 0;border-bottom:1px solid {CLR_BORDER}40;">
        <div style="width:36px;height:36px;border-radius:50%;background:{ic}20;display:flex;align-items:center;justify-content:center;">
        <i class="fa fa-{ico}" style="color:{ic};font-size:16px;"></i></div>
        <div><div style="font-size:14px;font-weight:600;color:{CLR_TEXT};">{rtype}</div>
        <div style="font-size:12px;color:{CLR_TEXT_SEC};">{rdesc}</div></div></div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

def _render_bar_chart(scores):
    """Render horizontal bar chart comparing all 7 dimension scores."""
    names = [DIMENSIONS[k]["name"] for k in DIMENSIONS]
    vals = [scores[k] for k in DIMENSIONS]
    colors = [_feas_color(v) for v in vals]

    fig = go.Figure(go.Bar(
        x=vals,
        y=names,
        orientation="h",
        marker=dict(color=colors, line=dict(color=CLR_BORDER, width=1)),
        text=[f"{v:.1f}" for v in vals],
        textposition="outside",
        textfont=dict(color=CLR_TEXT, size=12),
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 11], title="Score", title_font=dict(color=CLR_TEXT_SEC),
                   tickfont=dict(color=CLR_TEXT_SEC), gridcolor=CLR_BORDER),
        yaxis=dict(tickfont=dict(color=CLR_TEXT, size=12), autorange="reversed"),
        height=320,
        margin=dict(t=20, b=40, l=150, r=40),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=CLR_TEXT),
    )
    st.plotly_chart(fig, use_container_width=True, key="const_bar")


def _render_summary_table(scores, details):
    """Render an HTML summary table with key metrics per dimension."""
    rows_html = ""
    summary_data = [
        ("Foundation Soil", scores["foundation_soil"],
         f"Bearing: {details['foundation_soil'].get('bearing_capacity_kpa', 'N/A')} kPa"),
        ("Terrain Flatness", scores["terrain_flatness"],
         f"Slope: {details['terrain_flatness'].get('slope_pct', 'N/A')}%"),
        ("Seismic Zone", scores["seismic_zone"],
         f"Zone: {details['seismic_zone'].get('seismic_zone', 'N/A')}"),
        ("Equipment Access", scores["equipment_access"],
         f"Quality: {details['equipment_access'].get('access_quality', 'N/A')}"),
        ("Utility Availability", scores["utility_availability"],
         f"Power: {details['utility_availability'].get('power_lines', 0)} lines"),
        ("Weather Conditions", scores["weather_conditions"],
         f"Working: {details['weather_conditions'].get('working_pct', 'N/A')}%"),
        ("Existing Structures", scores["existing_structures"],
         f"Density: {details['existing_structures'].get('density_class', 'N/A')}"),
    ]
    for name, score, key_metric in summary_data:
        c = _feas_color(score)
        lbl = _feas_label(score)
        rows_html += f"""<tr>
            <td style="padding:8px 12px;border-bottom:1px solid {CLR_BORDER}40;color:{CLR_TEXT};">{name}</td>
            <td style="padding:8px 12px;border-bottom:1px solid {CLR_BORDER}40;color:{c};font-weight:700;text-align:center;">{score:.1f}</td>
            <td style="padding:8px 12px;border-bottom:1px solid {CLR_BORDER}40;color:{c};text-align:center;">{lbl}</td>
            <td style="padding:8px 12px;border-bottom:1px solid {CLR_BORDER}40;color:{CLR_TEXT_SEC};font-size:12px;">{key_metric}</td>
        </tr>"""
    st.markdown(f"""
    <div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};border-radius:12px;padding:16px;margin:10px 0;overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;">
            <thead>
                <tr>
                    <th style="padding:8px 12px;text-align:left;color:{CLR_TEXT_SEC};font-size:12px;border-bottom:2px solid {CLR_BORDER};">Dimension</th>
                    <th style="padding:8px 12px;text-align:center;color:{CLR_TEXT_SEC};font-size:12px;border-bottom:2px solid {CLR_BORDER};">Score</th>
                    <th style="padding:8px 12px;text-align:center;color:{CLR_TEXT_SEC};font-size:12px;border-bottom:2px solid {CLR_BORDER};">Rating</th>
                    <th style="padding:8px 12px;text-align:left;color:{CLR_TEXT_SEC};font-size:12px;border-bottom:2px solid {CLR_BORDER};">Key Metric</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>""", unsafe_allow_html=True)


def _render_folium_map(lat, lon, result):
    try:
        import folium
    except ImportError:
        st.warning("Folium not installed. Map view unavailable."); return
    overall, label = result["overall"], result["label"]
    color = _feas_color(overall)
    mc = "green" if overall >= 7 else ("orange" if overall >= 5 else ("red" if overall >= 3 else "darkred"))
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="OpenStreetMap")
    popup_html = f"""<div style="font-family:Arial;min-width:200px;">
    <h4 style="margin:0 0 8px 0;color:#333;">Construction Feasibility</h4>
    <table style="width:100%;font-size:12px;">
    <tr><td><b>Overall</b></td><td style="text-align:right;">{overall}/10 ({label})</td></tr>
    <tr><td><b>Cost</b></td><td style="text-align:right;">{result['cost_factor']:.1f}x</td></tr>
    <tr><td><b>Coords</b></td><td style="text-align:right;">{lat:.4f}, {lon:.4f}</td></tr></table>
    <hr style="margin:6px 0;"><table style="width:100%;font-size:11px;">"""
    for key, dim in DIMENSIONS.items():
        s = result["scores"][key]
        popup_html += f"<tr><td>{dim['name']}</td><td style='text-align:right;'>{s:.1f}/10</td></tr>"
    popup_html += "</table></div>"
    folium.Marker(location=[lat, lon], popup=folium.Popup(popup_html, max_width=300),
                  tooltip=f"Feasibility: {overall}/10 ({label})",
                  icon=folium.Icon(color=mc, icon="wrench", prefix="fa")).add_to(m)
    folium.Circle(location=[lat, lon], radius=1500, color=color, weight=2,
                  fill=True, fill_opacity=0.08, tooltip="Assessment radius (1.5 km)").add_to(m)
    offsets = [(0.005,0),(0.0035,0.0035),(0,0.005),(-0.0035,0.0035),
              (-0.005,0),(-0.0035,-0.0035),(0,-0.005)]
    for idx, (key, dim) in enumerate(DIMENSIONS.items()):
        s = result["scores"][key]; c = _feas_color(s); dlat, dlon = offsets[idx]
        folium.CircleMarker(location=[lat+dlat, lon+dlon], radius=12, color=c,
                            fill=True, fill_color=c, fill_opacity=0.6, weight=2,
                            tooltip=f"{dim['name']}: {s:.1f}/10").add_to(m)
    components.html(m._repr_html_(), height=500, scrolling=True)

# ── Main entry point ─────────────────────────────────────────────────────────
def render_construction_ai_tab():
    """Render the Construction Feasibility AI tab."""
    st.markdown("## Construction Feasibility AI")
    st.caption("Site assessment for building construction: soil, terrain, seismic, access & utilities")
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f", key="const_lat")
    lon = c2.number_input("Longitude", value=12.5, format="%.4f", key="const_lon")
    if st.button("Assess Construction Site", key="const_btn"):
        with st.spinner("Fetching data from 7 sources and computing feasibility..."):
            result = _compute_construction_assessment(lat, lon)
        if not result:
            st.error("Assessment failed. Please try again."); return
        overall, label = result["overall"], result["label"]
        scores, details = result["scores"], result["details"]
        _render_gauge(overall, label)
        st.markdown("---")
        st.markdown("### Dimension Scores")
        _render_metric_cards(scores)
        st.markdown("---")
        col_r, col_i = st.columns([3, 2])
        with col_r:
            st.markdown("### Feasibility Radar")
            _render_radar_chart(scores)
        with col_i:
            st.markdown("### Cost & Recommendations")
            _render_cost_difficulty(result["cost_factor"], result["cost_label"], overall)
            _render_recommendations(result["recommendations"])
        st.markdown("---")

        # -- Summary table + bar chart ----------------------------------------
        st.markdown("### Score Summary")
        _render_summary_table(scores, details)

        col_bar, col_empty = st.columns([3, 1])
        with col_bar:
            st.markdown("### Dimension Comparison")
            _render_bar_chart(scores)

        st.markdown("---")

        # -- Detail panels ----------------------------------------------------
        st.markdown("### Detailed Analysis")
        _render_detail_panels(details)

        st.markdown("---")

        # -- Folium map -------------------------------------------------------
        st.markdown("### Site Map")
        _render_folium_map(lat, lon, result)
        st.markdown(f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};border-radius:12px;
        padding:20px;margin-top:20px;text-align:center;">
        <div style="font-size:14px;color:{CLR_TEXT_SEC};margin-bottom:6px;">Construction Feasibility Assessment Complete</div>
        <div style="font-size:24px;font-weight:700;color:{_feas_color(overall)};">{overall}/10 &mdash; {label}</div>
        <div style="font-size:12px;color:{CLR_TEXT_SEC};margin-top:6px;">
        Location: {lat:.4f}, {lon:.4f} | Cost Factor: {result['cost_factor']:.1f}x ({result['cost_label']})</div>
        <div style="font-size:11px;color:{CLR_TEXT_SEC};margin-top:10px;">
        Data sources: ISRIC SoilGrids v2.0, Open Topo Data, USGS Earthquake,
        Overpass API (OSM), Open-Meteo | All free, no API keys required</div></div>""",
        unsafe_allow_html=True)
