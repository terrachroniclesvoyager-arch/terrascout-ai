"""
Terrain Mobility & Movement Analysis module for TerraScout AI.
Evaluates traversability across six movement modes: Infantry, Light Vehicle,
Heavy Vehicle, Tracked Vehicle, Bicycle/Motorcycle, and Helicopter/Aerial.
Uses: Open Topo Data (elevation), Overpass API (infrastructure), Open-Meteo (weather).
"""

import html as html_module
import json
import math
import logging

import streamlit as st
import requests
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS & MODE DEFINITIONS
# =============================================================================

MOBILITY_MODES = {
    "infantry": {"label": "Infantry / Foot", "icon": "\U0001F6B6", "color": "#22c55e",
                  "max_slope_pct": 60, "desc": "Dismounted movement on foot"},
    "light_vehicle": {"label": "Light Vehicle (4x4)", "icon": "\U0001F699", "color": "#3b82f6",
                       "max_slope_pct": 25, "desc": "4x4 / SUV on roads and moderate off-road"},
    "heavy_vehicle": {"label": "Heavy Vehicle / Truck", "icon": "\U0001F69A", "color": "#ef4444",
                       "max_slope_pct": 15, "desc": "Heavy truck on paved motorway/trunk roads"},
    "tracked": {"label": "Tracked Vehicle / APC", "icon": "\U0001F6E1\uFE0F", "color": "#f59e0b",
                 "max_slope_pct": 35, "desc": "Armored personnel carrier, cross-country"},
    "bicycle": {"label": "Bicycle / Motorcycle", "icon": "\U0001F6B2", "color": "#06b6d4",
                 "max_slope_pct": 18, "desc": "Two-wheeled on trails, cycleways, roads"},
    "helicopter": {"label": "Helicopter / Aerial", "icon": "\U0001F681", "color": "#8b5cf6",
                    "max_slope_pct": 100, "desc": "Rotary-wing aircraft operations"},
}

CLASS_THRESHOLDS = [
    (9.0, "EXCELLENT", "#15803d"), (7.0, "GOOD", "#22c55e"),
    (5.0, "MODERATE", "#f59e0b"), (3.0, "DIFFICULT", "#f97316"),
    (0.0, "IMPASSABLE", "#ef4444"),
]

RADIUS_M = 3000
GRID_SIZE = 0.025
GRID_STEPS = 5

# =============================================================================
# UTILITY HELPERS
# =============================================================================

def _clamp(val, lo=0.0, hi=10.0):
    return max(lo, min(hi, val))

def _safe_mean(values):
    clean = [v for v in values if v is not None]
    return sum(clean) / len(clean) if clean else 0.0

def _classify(score):
    for thr, label, color in CLASS_THRESHOLDS:
        if score >= thr:
            return label, color
    return "IMPASSABLE", "#ef4444"

def _compute_slopes(elevations, steps, size_deg):
    """Compute slope percentages from a flat elevation grid."""
    slopes, cell_m = [], size_deg / (steps - 1) * 111320.0
    for i in range(steps):
        for j in range(steps):
            idx = i * steps + j
            ec = elevations[idx] if idx < len(elevations) else None
            if ec is None:
                continue
            if j + 1 < steps:
                er = elevations[idx + 1] if (idx + 1) < len(elevations) else None
                if er is not None:
                    slopes.append(abs(er - ec) / cell_m * 100.0)
            if i + 1 < steps:
                eb_idx = (i + 1) * steps + j
                eb = elevations[eb_idx] if eb_idx < len(elevations) else None
                if eb is not None:
                    slopes.append(abs(eb - ec) / cell_m * 100.0)
    return slopes

# =============================================================================
# CACHED DATA FETCHING
# =============================================================================

@st.cache_data(ttl=900)
def _fetch_elevation(lat, lon):
    """Fetch 5x5 elevation grid from Open Topo Data SRTM30m."""
    pts = []
    for i in range(GRID_STEPS):
        for j in range(GRID_STEPS):
            plat = lat - GRID_SIZE / 2 + (GRID_SIZE * i / (GRID_STEPS - 1))
            plon = lon - GRID_SIZE / 2 + (GRID_SIZE * j / (GRID_STEPS - 1))
            pts.append(f"{plat:.5f},{plon:.5f}")
    try:
        resp = requests.get("https://api.opentopodata.org/v1/srtm30m",
                            params={"locations": "|".join(pts)}, timeout=10)
        resp.raise_for_status()
        elevs = [r.get("elevation") for r in resp.json().get("results", [])]
        valid = [e for e in elevs if e is not None]
        return {"elevations": elevs,
                "center": elevs[len(elevs) // 2] if elevs else None,
                "mean": _safe_mean(valid),
                "elev_range": (max(valid) - min(valid)) if valid else 0}
    except Exception as exc:
        logger.warning("Elevation fetch error: %s", exc)
        return {"elevations": [], "center": None, "mean": 0, "elev_range": 0}


@st.cache_data(ttl=900)
def _fetch_overpass(lat, lon):
    """Fetch roads, bridges, water, forests, settlements, helipads from Overpass."""
    query = f"""[out:json][timeout:25];(
      way["highway"](around:{RADIUS_M},{lat},{lon});
      way["bridge"="yes"](around:{RADIUS_M},{lat},{lon});
      way["natural"="water"](around:{RADIUS_M},{lat},{lon});
      way["waterway"](around:{RADIUS_M},{lat},{lon});
      way["natural"="wood"](around:{RADIUS_M},{lat},{lon});
      way["landuse"="forest"](around:{RADIUS_M},{lat},{lon});
      way["natural"="wetland"](around:{RADIUS_M},{lat},{lon});
      node["place"](around:{RADIUS_M},{lat},{lon});
      node["aeroway"="helipad"](around:{RADIUS_M},{lat},{lon});
      way["aeroway"="helipad"](around:{RADIUS_M},{lat},{lon});
      node["aeroway"="aerodrome"](around:{RADIUS_M},{lat},{lon});
      way["surface"](around:{RADIUS_M},{lat},{lon});
    );out center;"""
    try:
        resp = requests.post("https://overpass-api.de/api/interpreter",
                             data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Overpass fetch error: %s", exc)
        return {"elements": []}


@st.cache_data(ttl=900)
def _fetch_weather(lat, lon):
    """Fetch current weather from Open-Meteo."""
    try:
        resp = requests.get("https://api.open-meteo.com/v1/forecast", params={
            "latitude": lat, "longitude": lon, "current_weather": "true",
            "hourly": "precipitation,windspeed_10m,visibility", "forecast_days": 1,
        }, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        cur = data.get("current_weather", {})
        h = data.get("hourly", {})
        return {"temperature": cur.get("temperature", 20),
                "windspeed": cur.get("windspeed", 0),
                "avg_precip": _safe_mean(h.get("precipitation", [])[:6]),
                "max_wind": max(h.get("windspeed_10m", [0])[:6]),
                "avg_vis": _safe_mean(h.get("visibility", [20000])[:6])}
    except Exception as exc:
        logger.warning("Weather fetch error: %s", exc)
        return {"temperature": 20, "windspeed": 0, "avg_precip": 0,
                "max_wind": 0, "avg_vis": 20000}

# =============================================================================
# FEATURE EXTRACTION
# =============================================================================

_PAVED = {"asphalt", "concrete", "paved", "cobblestone", "sett"}
_UNPAVED = {"gravel", "dirt", "ground", "mud", "sand", "grass", "earth", "unpaved"}

def _extract_features(overpass_data):
    """Classify roads by type and count all infrastructure features.

    Iterates all Overpass elements once, tallying:
      - Road counts by highway classification
      - Surface quality (paved vs unpaved)
      - Bridges, water crossings, forests, wetlands
      - Settlements, helipads / aerodromes
    """
    road_types = ("motorway", "trunk", "primary", "secondary", "tertiary",
                  "residential", "unclassified", "track", "path",
                  "footway", "cycleway", "service")
    rc = {rt: 0 for rt in road_types}
    rc["other"] = 0
    bridge = water = forest = wetland = settlement = helipad = paved = unpaved = 0

    for el in overpass_data.get("elements", []):
        tags = el.get("tags", {})

        # Road classification
        hw = tags.get("highway", "")
        if hw:
            if hw in rc:
                rc[hw] += 1
            else:
                rc["other"] += 1

        # Surface quality assessment
        surf = tags.get("surface", "").lower()
        if surf in _PAVED:
            paved += 1
        elif surf in _UNPAVED:
            unpaved += 1

        # Bridge detection
        if tags.get("bridge") == "yes":
            bridge += 1

        # Water features (rivers, lakes, streams)
        if tags.get("natural") == "water" or tags.get("waterway"):
            water += 1

        # Vegetation cover (forest / woodland)
        if tags.get("natural") == "wood" or tags.get("landuse") == "forest":
            forest += 1

        # Wetland areas (bogs, marshes)
        if tags.get("natural") == "wetland":
            wetland += 1

        # Populated settlements
        if tags.get("place") in ("city", "town", "village", "hamlet", "suburb"):
            settlement += 1

        # Aviation landing sites
        if tags.get("aeroway") in ("helipad", "aerodrome"):
            helipad += 1

    major = rc["motorway"] + rc["trunk"] + rc["primary"]
    minor = rc["secondary"] + rc["tertiary"] + rc["residential"]
    trails = rc["track"] + rc["path"] + rc["footway"]
    total = sum(rc.values())

    return {"total_roads": total, "major_roads": major, "minor_roads": minor,
            "trails": trails, "cycleways": rc["cycleway"], "bridge": bridge,
            "water": water, "forest": forest, "wetland": wetland,
            "settlement": settlement, "helipad": helipad,
            "paved": paved, "unpaved": unpaved}

# =============================================================================
# SCORING FUNCTIONS (each returns 0-10)
# =============================================================================

def _score_infantry(slopes, f, w):
    avg = _safe_mean(slopes) if slopes else 0
    slope_s = 3.0 if avg <= 10 else (2.5 if avg <= 25 else (1.5 if avg <= 40 else max(0, 3 - avg / 20)))
    trail_s = min(2.5, f["trails"] * 0.25)
    water_p = min(1.5, f["water"] * 0.15)
    if f["bridge"] > 0:
        water_p *= max(0.3, 1 - f["bridge"] * 0.2)
    veg_s = min(1.5, f["forest"] * 0.15)
    weather_p = min(1.0, w.get("avg_precip", 0) * 0.1)
    settle_s = min(0.5, f["settlement"] * 0.15)
    return round(_clamp(2.0 + slope_s + trail_s + veg_s + settle_s - water_p - weather_p), 1)


def _score_light_vehicle(slopes, f, w):
    avg = _safe_mean(slopes) if slopes else 0
    mx = max(slopes) if slopes else 0
    slope_s = 2.5 if avg <= 8 else (2.0 if avg <= 15 else (1.0 if avg <= 25 else 0))
    steep_p = min(2.0, (mx - 25) / 10) if mx > 25 else 0
    road_s = min(3.0, (f["total_roads"] + f["trails"]) * 0.15)
    bridge_s = min(1.5, f["bridge"] * 0.5)
    ts = f["paved"] + f["unpaved"]
    surf_s = (0.5 + f["paved"] / ts * 0.5) if ts > 0 else 0.3
    w_p = min(1.5, w.get("avg_precip", 0) * 0.15)
    wet_p = min(1.0, f["wetland"] * 0.3)
    return round(_clamp(1.5 + slope_s + road_s + bridge_s + surf_s - steep_p - w_p - wet_p), 1)


def _score_heavy_vehicle(slopes, f, w):
    avg = _safe_mean(slopes) if slopes else 0
    mx = max(slopes) if slopes else 0
    slope_s = 2.0 if avg <= 5 else (1.5 if avg <= 10 else (0.5 if avg <= 15 else 0))
    steep_p = min(3.0, (mx - 15) / 5) if mx > 15 else 0
    road_s = min(2.5, f["major_roads"] * 0.5) + min(1.0, f["minor_roads"] * 0.1)
    bridge_s = min(1.5, f["bridge"] * 0.5)
    settle_s = min(1.0, f["settlement"] * 0.25)
    surf_s = min(1.0, f["paved"] * 0.15) if f["paved"] > 0 else 0
    w_p = min(1.0, w.get("avg_precip", 0) * 0.1)
    return round(_clamp(1.0 + slope_s + road_s + bridge_s + settle_s + surf_s - steep_p - w_p), 1)


def _score_tracked(slopes, f, w):
    avg = _safe_mean(slopes) if slopes else 0
    mx = max(slopes) if slopes else 0
    slope_s = 2.5 if avg <= 15 else (2.0 if avg <= 25 else (1.0 if avg <= 35 else 0))
    steep_p = min(2.5, (mx - 35) / 8) if mx > 35 else 0
    forest_p = min(1.5, f["forest"] * 0.12)
    rough_s = 2.0 if avg <= 20 else (1.5 if avg <= 30 else 0.5)
    water_s = 1.0 if f["water"] <= 2 else (0.5 if f["water"] <= 5 else 0)
    wet_p = min(1.5, f["wetland"] * 0.4)
    road_b = min(1.0, f["total_roads"] * 0.05)
    w_p = min(0.5, w.get("avg_precip", 0) * 0.05)
    return round(_clamp(2.0 + slope_s + rough_s + water_s + road_b
                        - steep_p - forest_p - wet_p - w_p), 1)


def _score_bicycle(slopes, f, w):
    avg = _safe_mean(slopes) if slopes else 0
    mx = max(slopes) if slopes else 0
    slope_s = 2.5 if avg <= 3 else (2.0 if avg <= 8 else (1.0 if avg <= 15 else 0))
    steep_p = min(2.0, (mx - 18) / 8) if mx > 18 else 0
    cycle_s = min(2.5, (f["cycleways"] + f["trails"]) * 0.25)
    road_s = min(1.5, f["total_roads"] * 0.08)
    ts = f["paved"] + f["unpaved"]
    surf_s = (f["paved"] / ts) if ts > 0 else 0.3
    settle_s = min(0.5, f["settlement"] * 0.15)
    w_p = min(1.5, w.get("avg_precip", 0) * 0.15 + w.get("max_wind", 0) * 0.02)
    return round(_clamp(1.5 + slope_s + cycle_s + road_s + surf_s + settle_s - steep_p - w_p), 1)


def _score_helicopter(slopes, f, w, elev):
    flat = sum(1 for s in slopes if s < 5) if slopes else 0
    total = len(slopes) if slopes else 1
    lz_s = (flat / total) * 3.0
    obs_p = min(2.0, f["forest"] * 0.15)
    heli_s = min(2.0, f["helipad"] * 1.0)
    me = elev.get("mean", 0) or 0
    elev_p = 0 if me <= 1500 else (min(1.0, (me - 1500) / 3000))
    wind = w.get("max_wind", 0)
    wind_p = min(1.5, (wind - 50) / 30) if wind > 50 else ((wind - 30) / 40 if wind > 30 else 0)
    vis = w.get("avg_vis", 20000)
    vis_p = min(1.5, (5000 - vis) / 3000) if vis < 5000 else 0
    prec_p = min(0.5, w.get("avg_precip", 0) * 0.05)
    open_b = 1.0 if f["forest"] < 3 else (0.5 if f["forest"] < 8 else 0)
    return round(_clamp(3.0 + lz_s + heli_s + open_b - obs_p - elev_p
                        - wind_p - vis_p - prec_p), 1)

# =============================================================================
# AGGREGATE ANALYSIS
# =============================================================================

def _run_analysis(lat, lon):
    elev = _fetch_elevation(lat, lon)
    ovp = _fetch_overpass(lat, lon)
    weather = _fetch_weather(lat, lon)
    feat = _extract_features(ovp)
    slopes = _compute_slopes(elev["elevations"], GRID_STEPS, GRID_SIZE)
    avg_s = _safe_mean(slopes) if slopes else 0
    max_s = max(slopes) if slopes else 0

    scores = {
        "infantry": _score_infantry(slopes, feat, weather),
        "light_vehicle": _score_light_vehicle(slopes, feat, weather),
        "heavy_vehicle": _score_heavy_vehicle(slopes, feat, weather),
        "tracked": _score_tracked(slopes, feat, weather),
        "bicycle": _score_bicycle(slopes, feat, weather),
        "helicopter": _score_helicopter(slopes, feat, weather, elev),
    }
    tsumm = {"avg_slope": round(avg_s, 1), "max_slope": round(max_s, 1),
             "elev_range": round(elev.get("elev_range", 0), 1),
             "center_elev": round(elev.get("center", 0) or 0, 1),
             "mean_elev": round(elev.get("mean", 0), 1)}
    return {"scores": scores, "features": feat, "weather": weather,
            "terrain": tsumm, "elev": elev, "overpass": ovp}

# =============================================================================
# UI HELPERS
# =============================================================================

def _mode_card(mk, score, best_mk):
    m = MOBILITY_MODES[mk]
    lbl, clr = _classify(score)
    is_best = mk == best_mk
    border = f"3px solid {m['color']}" if is_best else "1px solid #444"
    bg = "#1a2a1a" if is_best else "#1a1a2e"
    badge = ' <span style="color:#ffd700;font-weight:bold;">[BEST]</span>' if is_best else ""
    st.markdown(f"""<div style="border:{border};border-radius:10px;padding:15px;
        background:{bg};margin-bottom:8px;">
        <div style="font-size:1.3em;font-weight:bold;">{m['icon']} {m['label']}{badge}</div>
        <div style="font-size:2em;font-weight:bold;color:{clr};margin:5px 0;">{score}/10</div>
        <div style="display:inline-block;padding:3px 10px;border-radius:12px;
            background:{clr}22;color:{clr};font-weight:bold;font-size:0.85em;">{lbl}</div>
        <div style="color:#aaa;font-size:0.8em;margin-top:6px;">{m['desc']}</div>
        <div style="color:#888;font-size:0.75em;margin-top:4px;">Max slope: {m['max_slope_pct']}%</div>
    </div>""", unsafe_allow_html=True)


def _radar_chart(scores):
    labels = [MOBILITY_MODES[k]["label"] for k in scores]
    colors = [MOBILITY_MODES[k]["color"] for k in scores]
    vals = list(scores.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=labels + [labels[0]], fill="toself",
        fillcolor="rgba(59,130,246,0.15)", line=dict(color="#3b82f6", width=2),
        marker=dict(size=8, color=colors + [colors[0]]),
        hovertemplate="%{theta}: %{r}/10<extra></extra>"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10],
                   tickvals=[2, 4, 6, 8, 10], gridcolor="#333"),
                   angularaxis=dict(gridcolor="#333"), bgcolor="rgba(0,0,0,0)"),
        showlegend=False, height=420, margin=dict(l=60, r=60, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"))
    return fig


def _bar_chart(scores):
    sm = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    labels = [MOBILITY_MODES[k]["label"] for k, _ in sm]
    vals = [v for _, v in sm]
    colors = [MOBILITY_MODES[k]["color"] for k, _ in sm]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=vals, y=labels, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v}/10" for v in vals], textposition="auto",
        textfont=dict(color="white", size=13),
        hovertemplate="%{y}: %{x}/10<extra></extra>"))
    fig.update_layout(
        xaxis=dict(range=[0, 10.5], title="Mobility Score", gridcolor="#333",
                   tickvals=[0, 2, 4, 6, 8, 10]),
        yaxis=dict(autorange="reversed"), height=320,
        margin=dict(l=10, r=20, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"))
    for x0, x1, c in [(0, 2, "rgba(239,68,68,0.08)"), (2, 4, "rgba(249,115,22,0.08)"),
                       (4, 6, "rgba(245,158,11,0.08)"), (6, 8, "rgba(34,197,94,0.08)"),
                       (8, 10, "rgba(21,128,61,0.08)")]:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=c, line_width=0)
    return fig


def _road_map(lat, lon, ovp_data, scores):
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.warning("Install folium and streamlit-folium for map visualization.")
        return
    best = max(scores, key=scores.get)
    bi = MOBILITY_MODES[best]
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB dark_matter")
    folium.Marker([lat, lon],
        popup=f"Center | Best: {bi['icon']} {bi['label']}",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(m)
    folium.Circle([lat, lon], radius=RADIUS_M, color="#3b82f6",
        fill=False, weight=1, dash_array="5").add_to(m)

    hw_colors = {"motorway": "#ef4444", "trunk": "#f97316", "primary": "#f59e0b",
        "secondary": "#eab308", "tertiary": "#a3e635", "residential": "#86efac",
        "track": "#a78bfa", "path": "#c084fc", "footway": "#e879f9",
        "cycleway": "#22d3ee", "service": "#94a3b8"}

    for el in ovp_data.get("elements", []):
        tags = el.get("tags", {})
        if el.get("type") == "way":
            c = el.get("center", {})
            elat, elon = c.get("lat"), c.get("lon")
            if not elat or not elon:
                continue
            hw = tags.get("highway", "")
            if hw in hw_colors:
                folium.CircleMarker([elat, elon], radius=3, color=hw_colors[hw],
                    fill=True, fillOpacity=0.7, popup=f"{hw.title()}").add_to(m)
            if tags.get("bridge") == "yes":
                folium.Marker([elat, elon], icon=folium.Icon(color="blue",
                    icon="road", prefix="fa"), popup="Bridge").add_to(m)
            if tags.get("natural") == "water" or tags.get("waterway"):
                folium.CircleMarker([elat, elon], radius=4, color="#0ea5e9",
                    fill=True, fillOpacity=0.5, popup="Water").add_to(m)
            if tags.get("aeroway") in ("helipad", "aerodrome"):
                folium.Marker([elat, elon], icon=folium.Icon(color="purple",
                    icon="helicopter", prefix="fa"), popup="Helipad").add_to(m)
        elif el.get("type") == "node":
            if tags.get("place") in ("city", "town", "village", "hamlet"):
                folium.Marker([el.get("lat", 0), el.get("lon", 0)],
                    icon=folium.Icon(color="green", icon="home", prefix="fa"),
                    popup=f"{html_module.escape(tags.get('name', 'Settlement'))}").add_to(m)
    st_folium(m, width=700, height=450, key="tmob_folium_map")


def _mode_factors(mk, f, t):
    avg, mx = t["avg_slope"], t["max_slope"]
    mt = MOBILITY_MODES[mk]["max_slope_pct"]
    si = "+" if avg <= mt * 0.5 else ("-" if avg > mt else "~")
    base = [("Avg Slope", f"{avg}% (tol: {mt}%)", si),
            ("Max Slope", f"{mx}%", "+" if mx <= mt else "-")]
    extras = {
        "infantry": [("Trails", str(f["trails"]), "+" if f["trails"] > 3 else "~"),
                     ("Water", str(f["water"]), "-" if f["water"] > 5 else "~"),
                     ("Forest", str(f["forest"]), "+" if f["forest"] > 2 else "~")],
        "light_vehicle": [("Roads", str(f["total_roads"]), "+" if f["total_roads"] > 10 else "-"),
                          ("Bridges", str(f["bridge"]), "+" if f["bridge"] > 0 else "-"),
                          ("Paved", str(f["paved"]), "+" if f["paved"] > 5 else "~")],
        "heavy_vehicle": [("Major Roads", str(f["major_roads"]), "+" if f["major_roads"] > 2 else "-"),
                          ("Bridges", str(f["bridge"]), "+" if f["bridge"] > 0 else "-"),
                          ("Settlements", str(f["settlement"]), "+" if f["settlement"] > 0 else "~")],
        "tracked": [("Open Terrain", f"Forest:{f['forest']}", "+" if f["forest"] < 5 else "-"),
                    ("Wetlands", str(f["wetland"]), "-" if f["wetland"] > 2 else "+"),
                    ("Water", str(f["water"]), "~")],
        "bicycle": [("Cycleways", str(f["cycleways"]), "+" if f["cycleways"] > 0 else "-"),
                    ("Trails", str(f["trails"]), "+" if f["trails"] > 3 else "~"),
                    ("Paved", str(f["paved"]), "+" if f["paved"] > 5 else "-")],
        "helicopter": [("Helipads", str(f["helipad"]), "+" if f["helipad"] > 0 else "~"),
                       ("Forest Obs.", str(f["forest"]), "-" if f["forest"] > 5 else "+"),
                       ("Elevation", f"{t['mean_elev']}m", "-" if t["mean_elev"] > 2000 else "+")],
    }
    return base + extras.get(mk, [])

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def render_terrain_mobility_tab():
    """Main entry point for the Terrain Mobility & Movement Analysis tab."""
    st.markdown("## \U0001F681 Terrain Mobility & Movement Analysis")
    st.caption("Multi-mode terrain traversability for foot, vehicle, "
               "tracked & aerial movement within a 3 km radius.")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f", key="tmob_lat",
                          min_value=-90.0, max_value=90.0)
    lon = c2.number_input("Longitude", value=12.5, format="%.4f", key="tmob_lon",
                          min_value=-180.0, max_value=180.0)
    st.markdown("---")

    if st.button("\U0001F681 Analyze Mobility", key="tmob_btn", type="primary"):
        with st.spinner("Fetching elevation, infrastructure, and weather data..."):
            res = _run_analysis(lat, lon)

        scores = res["scores"]
        feat = res["features"]
        weather = res["weather"]
        tsumm = res["terrain"]

        if not scores:
            st.error("Analysis failed. Could not retrieve required data.")
            return

        # Best mode
        best_mk = max(scores, key=scores.get)
        bi = MOBILITY_MODES[best_mk]
        bl, bc = _classify(scores[best_mk])
        st.success(f"Analysis complete for ({lat:.4f}, {lon:.4f}). "
                   f"Best: {bi['icon']} **{bi['label']}** ({scores[best_mk]}/10 - {bl})")

        # Mode cards (3x2 grid)
        st.markdown("### Mobility Scores by Mode")
        keys = list(MOBILITY_MODES.keys())
        for row_keys in [keys[:3], keys[3:]]:
            cols = st.columns(3)
            for i, mk in enumerate(row_keys):
                with cols[i]:
                    _mode_card(mk, scores[mk], best_mk)

        # Charts
        st.markdown("### Comparative Analysis")
        cl, cr = st.columns(2)
        with cl:
            st.markdown("#### Mobility Radar")
            st.plotly_chart(_radar_chart(scores, key="termob_pchart1"), use_container_width=True, key="tmob_radar")
        with cr:
            st.markdown("#### Mode Ranking")
            st.plotly_chart(_bar_chart(scores, key="termob_pchart2"), use_container_width=True, key="tmob_bar")

        # Legend
        st.markdown("#### Classification Scale")
        lcols = st.columns(5)
        for i, (cl_l, cl_r, cl_c) in enumerate([
            ("EXCELLENT", "9-10", "#15803d"), ("GOOD", "7-8", "#22c55e"),
            ("MODERATE", "5-6", "#f59e0b"), ("DIFFICULT", "3-4", "#f97316"),
            ("IMPASSABLE", "0-2", "#ef4444")]):
            lcols[i].markdown(f"<span style='color:{cl_c};font-weight:bold;'>"
                              f"{cl_l}</span> ({cl_r})", unsafe_allow_html=True)

        st.markdown("---")

        # Terrain summary metrics
        st.markdown("### Terrain & Infrastructure Summary")
        for row_metrics in [
            [("Avg Slope", f"{tsumm['avg_slope']}%"),
             ("Max Slope", f"{tsumm['max_slope']}%"),
             ("Elev. Range", f"{tsumm['elev_range']} m"),
             ("Center Elev.", f"{tsumm['center_elev']} m")],
            [("Total Roads", feat["total_roads"]),
             ("Bridges", feat["bridge"]),
             ("Water Crossings", feat["water"]),
             ("Settlements", feat["settlement"])],
            [("Trails/Paths", feat["trails"]),
             ("Forests", feat["forest"]),
             ("Wetlands", feat["wetland"]),
             ("Helipads", feat["helipad"])]]:
            cols = st.columns(4)
            for i, (label, val) in enumerate(row_metrics):
                cols[i].metric(label, val)

        st.markdown("#### Current Weather Conditions")
        wc = st.columns(4)
        wc[0].metric("Temperature", f"{weather.get('temperature', '?')} C")
        wc[1].metric("Wind Speed", f"{weather.get('windspeed', '?')} km/h")
        wc[2].metric("Avg Precip.", f"{weather.get('avg_precip', 0):.1f} mm")
        wc[3].metric("Visibility", f"{weather.get('avg_vis', 0):.0f} m")

        st.markdown("---")

        # Road map
        st.markdown("### Road Network & Infrastructure Map")
        _road_map(lat, lon, res["overpass"], scores)

        st.markdown("---")

        # Detailed breakdown
        st.markdown("### Detailed Mode Breakdown")
        for mk, sc in scores.items():
            m = MOBILITY_MODES[mk]
            lbl, clr = _classify(sc)
            with st.expander(f"{m['icon']} {m['label']} -- {sc}/10 ({lbl})"):
                for fn, fv, fi in _mode_factors(mk, feat, tsumm):
                    ic = "#22c55e" if fi == "+" else ("#ef4444" if fi == "-" else "#f59e0b")
                    st.markdown(f"- **{fn}**: {fv} "
                                f"<span style='color:{ic}'>[{fi}]</span>",
                                unsafe_allow_html=True)

        st.markdown("---")

        # Recommendation
        st.markdown("### Movement Recommendation")
        sm = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        best_k, best_s = sm[0]
        worst_k, worst_s = sm[-1]
        bm, wm = MOBILITY_MODES[best_k], MOBILITY_MODES[worst_k]
        avg_sc = _safe_mean(list(scores.values()))
        lines = [
            f"**Best mode**: {bm['icon']} **{bm['label']}** ({best_s}/10)",
            f"**Least suitable**: {wm['icon']} **{wm['label']}** ({worst_s}/10)",
            f"**Average mobility index**: {avg_sc:.1f}/10", ""]
        if tsumm["avg_slope"] > 25:
            lines.append("- **Terrain Warning**: High slopes restrict wheeled vehicles. "
                         "Consider infantry or tracked movement.")
        elif tsumm["avg_slope"] > 15:
            lines.append("- **Terrain Note**: Moderate slopes challenge heavy vehicles. "
                         "Light 4x4 and tracked vehicles recommended.")
        else:
            lines.append("- **Terrain**: Favorable slopes for most movement types.")
        if weather.get("avg_precip", 0) > 5:
            lines.append("- **Weather Alert**: Precipitation degrades unpaved surfaces.")
        if weather.get("max_wind", 0) > 40:
            lines.append("- **Wind Advisory**: High winds may restrict helicopter ops.")
        st.markdown("\n".join(lines))

        st.markdown("---")

        # Raw data export
        with st.expander("Raw Data (JSON)", expanded=False):
            export = {
                "coordinates": {"lat": lat, "lon": lon}, "scores": scores,
                "terrain": tsumm,
                "infrastructure": {k: feat[k] for k in feat},
                "weather": weather,
                "classifications": {k: _classify(v)[0] for k, v in scores.items()}}
            st.json(export)
            st.download_button("Download JSON Report",
                data=json.dumps(export, indent=2),
                file_name=f"mobility_report_{lat}_{lon}.json",
                mime="application/json", key="tmob_download_json")
