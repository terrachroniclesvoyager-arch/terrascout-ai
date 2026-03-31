# -*- coding: utf-8 -*-
"""
Pollution & Environmental Contamination Tracker module for TerraScout AI.
Analyzes pollution sources and environmental quality around any GPS coordinate
using 6 dimensions: Air Quality, Industrial Sources, Water Pollution Risk,
Noise Pollution, Waste Infrastructure, and Green Buffer Zones.
Uses Open-Meteo Air Quality API and Overpass API (all free, no API key).
"""

import math
import json
import logging

import streamlit as st
import requests
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit.components.v1 as components

try:
    import folium
except ImportError:
    folium = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OPEN_METEO_AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OPEN_METEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

EAQI_BANDS = [
    (0, 20, "Good", "#22c55e"), (21, 40, "Fair", "#84cc16"),
    (41, 60, "Moderate", "#f59e0b"), (61, 80, "Poor", "#f97316"),
    (81, 100, "Very Poor", "#ef4444"), (101, 999, "Extremely Poor", "#991b1b"),
]

WHO_LIMITS = {
    "pm2_5": 5.0, "pm10": 15.0, "nitrogen_dioxide": 10.0,
    "sulphur_dioxide": 40.0, "ozone": 100.0, "carbon_monoxide": 4000.0,
}

SCORE_COLORS = [
    (0, 2, "#ef4444"), (3, 4, "#f97316"), (5, 6, "#eab308"),
    (7, 8, "#84cc16"), (9, 10, "#22c55e"),
]

POLLUTANT_DISPLAY = {
    "pm2_5": ("PM2.5", "#06b6d4"), "pm10": ("PM10", "#38bdf8"),
    "nitrogen_dioxide": ("NO2", "#f59e0b"), "sulphur_dioxide": ("SO2", "#ef4444"),
    "ozone": ("O3", "#8b5cf6"), "carbon_monoxide": ("CO", "#10b981"),
}

DIMENSION_META = {
    "air_quality": {"label": "Air Quality", "icon": "wind"},
    "industrial": {"label": "Industrial Sources", "icon": "industry"},
    "water_pollution": {"label": "Water Pollution Risk", "icon": "tint"},
    "noise": {"label": "Noise Pollution", "icon": "volume-up"},
    "waste": {"label": "Waste Infrastructure", "icon": "trash"},
    "green_buffer": {"label": "Green Buffer Zones", "icon": "leaf"},
}

DIM_WEIGHTS = {
    "air_quality": 0.25, "industrial": 0.20, "water_pollution": 0.15,
    "noise": 0.15, "waste": 0.10, "green_buffer": 0.15,
}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------
def _score_color(score: float) -> str:
    s = int(round(score))
    for lo, hi, color in SCORE_COLORS:
        if lo <= s <= hi:
            return color
    return "#8b97b0"


def _eaqi_info(val: float) -> tuple:
    for lo, hi, label, color in EAQI_BANDS:
        if lo <= val <= hi:
            return label, color
    return "Unknown", "#8b97b0"


def _clamp(v: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, v))


def _health_label(score: float) -> str:
    if score >= 9: return "Excellent"
    if score >= 7: return "Good"
    if score >= 5: return "Moderate"
    if score >= 3: return "Poor"
    return "Hazardous"


def _count_elements(data: dict) -> int:
    if "error" in data or "elements" not in data:
        return 0
    return len(data.get("elements", []))


def _extract_coords(data: dict) -> list:
    out = []
    if "error" in data or "elements" not in data:
        return out
    for el in data["elements"]:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat and lon:
            out.append((lat, lon, el.get("tags", {})))
    return out


def _count_to_score(count: int, thresholds=None) -> float:
    """Convert a count into an inverted 0-10 score using threshold list."""
    if thresholds is None:
        thresholds = [(0, 10.0), (3, 8.0), (8, 6.0), (15, 4.0), (30, 2.0)]
    score = 0.5
    for limit, val in thresholds:
        if count <= limit:
            return val
    return score


# ---------------------------------------------------------------------------
# API fetch functions (all cached, timeout=10, try/except)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_air_quality(lat: float, lon: float) -> dict:
    """Fetch current air quality from Open-Meteo Air Quality API."""
    try:
        resp = requests.get(OPEN_METEO_AQ_URL, params={
            "latitude": lat, "longitude": lon,
            "current": "pm10,pm2_5,nitrogen_dioxide,sulphur_dioxide,ozone,carbon_monoxide,european_aqi",
        }, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Air quality API error: %s", exc)
        return {"error": str(exc)}


@st.cache_data(ttl=900)
def _fetch_precipitation(lat: float, lon: float) -> dict:
    """Fetch 7-day precipitation from Open-Meteo weather API."""
    try:
        resp = requests.get(OPEN_METEO_WEATHER_URL, params={
            "latitude": lat, "longitude": lon,
            "current": "precipitation,rain",
            "daily": "precipitation_sum", "past_days": 7, "timezone": "auto",
        }, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Weather API error: %s", exc)
        return {"error": str(exc)}


@st.cache_data(ttl=900)
def _fetch_overpass(query: str) -> dict:
    """Execute an Overpass API query."""
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Overpass API error: %s", exc)
        return {"error": str(exc)}


def _overpass_around(tags_list: list, lat: float, lon: float, radius: int) -> dict:
    """Build and run an Overpass around query for a list of tag filters."""
    lines = []
    for tag_filter in tags_list:
        lines.append(f'  node[{tag_filter}](around:{radius},{lat},{lon});')
        lines.append(f'  way[{tag_filter}](around:{radius},{lat},{lon});')
    body = "\n".join(lines)
    query = f"[out:json][timeout:10];\n(\n{body}\n);\nout center body;"
    return _fetch_overpass(query)


@st.cache_data(ttl=900)
def _fetch_industrial_sources(lat: float, lon: float) -> dict:
    """Industrial landuse, factories, power plants, waste facilities in 10 km."""
    tags = ['"landuse"="industrial"', '"man_made"="works"', '"power"="plant"',
            '"industrial"', '"amenity"="waste_disposal"']
    return _overpass_around(tags, lat, lon, 10000)


@st.cache_data(ttl=900)
def _fetch_water_pollution_sources(lat: float, lon: float) -> dict:
    """Sewage plants, landfills, industrial sites near waterways in 10 km."""
    tags = ['"man_made"="wastewater_plant"', '"landuse"="landfill"',
            '"man_made"="sewage_treatment"', '"landuse"="industrial"',
            '"waterway"="drain"']
    return _overpass_around(tags, lat, lon, 10000)


@st.cache_data(ttl=900)
def _fetch_noise_sources(lat: float, lon: float) -> dict:
    """Highways, railways, airports, nightlife within 2 km."""
    tags = ['"highway"~"motorway|trunk|primary"', '"railway"="station"',
            '"railway"="rail"', '"aeroway"="aerodrome"', '"aeroway"="runway"',
            '"amenity"~"nightclub|bar|pub"']
    return _overpass_around(tags, lat, lon, 2000)


@st.cache_data(ttl=900)
def _fetch_waste_infrastructure(lat: float, lon: float) -> dict:
    """Recycling, waste disposal, landfills, composting in 10 km."""
    tags = ['"amenity"="recycling"', '"amenity"="waste_disposal"',
            '"landuse"="landfill"', '"amenity"="waste_transfer_station"',
            '"recycling_type"="centre"']
    return _overpass_around(tags, lat, lon, 10000)


@st.cache_data(ttl=900)
def _fetch_green_buffers(lat: float, lon: float) -> dict:
    """Parks, forests, nature reserves, green areas in 5 km."""
    lines = []
    for tag in ['"leisure"="park"', '"landuse"="forest"', '"leisure"="nature_reserve"',
                '"landuse"="grass"', '"leisure"="garden"', '"natural"="wood"']:
        lines.append(f'  way[{tag}](around:5000,{lat},{lon});')
    lines.append(f'  relation["leisure"="nature_reserve"](around:5000,{lat},{lon});')
    lines.append(f'  relation["boundary"="protected_area"](around:5000,{lat},{lon});')
    body = "\n".join(lines)
    return _fetch_overpass(f"[out:json][timeout:10];\n(\n{body}\n);\nout center body;")


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------
def _score_air_quality(data: dict) -> tuple:
    """Score air quality 0-10 (10 = excellent, 0 = hazardous)."""
    if "error" in data or "current" not in data:
        return 5.0, {"status": "unavailable"}
    cur = data["current"]
    eaqi = cur.get("european_aqi", 50)
    score = {20: 10.0, 40: 8.0, 60: 6.0, 80: 4.0, 100: 2.0}.get(
        next((t for t in [20, 40, 60, 80, 100] if eaqi <= t), None), 0.5)
    details = {"european_aqi": eaqi}
    for k in POLLUTANT_DISPLAY:
        details[k] = cur.get(k, 0)
    return _clamp(score), details


def _score_industrial(data: dict) -> tuple:
    count = _count_elements(data)
    score = _count_to_score(count)
    return _clamp(score), {"count": count, "elements": _extract_coords(data)[:50]}


def _score_water_pollution(osm_data: dict, precip_data: dict) -> tuple:
    count = _count_elements(osm_data)
    base = _count_to_score(count, [(0, 10.0), (3, 8.0), (8, 6.0), (15, 4.0), (25, 2.0)])
    rain_penalty, weekly = 0.0, 0.0
    if "error" not in precip_data and "daily" in precip_data:
        sums = precip_data["daily"].get("precipitation_sum", [])
        weekly = sum(v for v in sums if v is not None)
        rain_penalty = 2.0 if weekly > 50 else (1.0 if weekly > 20 else (0.5 if weekly > 10 else 0.0))
    return _clamp(base - rain_penalty), {
        "source_count": count, "weekly_precipitation_mm": round(weekly, 1),
        "rain_penalty": rain_penalty, "elements": _extract_coords(osm_data)[:50],
    }


def _score_noise(data: dict) -> tuple:
    elements = _extract_coords(data)
    cats = {"highways": 0, "railways": 0, "airports": 0, "nightlife": 0}
    for _, _, tags in elements:
        if "highway" in tags: cats["highways"] += 1
        elif "railway" in tags: cats["railways"] += 1
        elif "aeroway" in tags: cats["airports"] += 1
        elif tags.get("amenity") in ("nightclub", "bar", "pub"): cats["nightlife"] += 1
    weighted = cats["highways"] + cats["railways"] * 1.5 + cats["airports"] * 3.0 + cats["nightlife"] * 0.5
    score = _count_to_score(int(weighted))
    cats["total_sources"] = _count_elements(data)
    cats["weighted_score"] = round(weighted, 1)
    return _clamp(score), cats


def _score_waste(data: dict) -> tuple:
    elements = _extract_coords(data)
    recycling = landfills = disposal = other = 0
    for _, _, tags in elements:
        if tags.get("amenity") == "recycling" or tags.get("recycling_type") == "centre":
            recycling += 1
        elif tags.get("landuse") == "landfill": landfills += 1
        elif tags.get("amenity") in ("waste_disposal", "waste_transfer_station"): disposal += 1
        else: other += 1
    neg = landfills * 2.0 + disposal * 1.5 + other * 0.5
    pos = min(recycling * 0.3, 2.0)
    if neg == 0: score = 9.0 + pos * 0.5
    elif neg <= 3: score = 7.0 + pos * 0.3
    elif neg <= 8: score = 5.0
    elif neg <= 15: score = 3.0
    else: score = 1.0
    return _clamp(score), {
        "recycling_centers": recycling, "landfills": landfills,
        "disposal_sites": disposal, "other_waste": other,
        "total": len(elements), "elements": elements[:50],
    }


def _score_green_buffers(data: dict) -> tuple:
    elements = _extract_coords(data)
    parks = forests = reserves = other_g = 0
    for _, _, tags in elements:
        if tags.get("leisure") == "park": parks += 1
        elif tags.get("landuse") == "forest" or tags.get("natural") == "wood": forests += 1
        elif tags.get("leisure") == "nature_reserve" or tags.get("boundary") == "protected_area": reserves += 1
        else: other_g += 1
    w = parks + forests * 1.5 + reserves * 2.0 + other_g * 0.5
    score = _count_to_score(int(w), [(0, 1.0), (3, 3.0), (8, 5.0), (15, 7.0), (30, 8.5)])
    if w > 30: score = 10.0
    return _clamp(score), {
        "parks": parks, "forests": forests, "nature_reserves": reserves,
        "other_green": other_g, "total": _count_elements(data), "elements": elements[:50],
    }


def _overall_health_score(scores: dict) -> float:
    total = sum(scores.get(k, 5.0) * w for k, w in DIM_WEIGHTS.items())
    return round(total / sum(DIM_WEIGHTS.values()), 1)


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------
def _build_aqi_gauge(eaqi_val: float) -> go.Figure:
    label, color = _eaqi_info(eaqi_val)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=eaqi_val,
        title={"text": f"European AQI: {label}", "font": {"size": 16, "color": "#e8ecf4"}},
        number={"font": {"size": 42, "color": color}},
        gauge={
            "axis": {"range": [0, 150], "tickcolor": "#8b97b0"},
            "bar": {"color": color}, "bgcolor": "#1a1a2e", "bordercolor": "#1a4080",
            "steps": [
                {"range": [0, 20], "color": "rgba(34,197,94,0.2)"},
                {"range": [20, 40], "color": "rgba(132,204,22,0.2)"},
                {"range": [40, 60], "color": "rgba(245,158,11,0.2)"},
                {"range": [60, 80], "color": "rgba(249,115,22,0.2)"},
                {"range": [80, 100], "color": "rgba(239,68,68,0.2)"},
                {"range": [100, 150], "color": "rgba(153,27,27,0.2)"},
            ],
            "threshold": {"line": {"color": "#fff", "width": 2}, "thickness": 0.8, "value": eaqi_val},
        },
    ))
    fig.update_layout(height=260, margin=dict(t=50, b=10, l=30, r=30),
                      paper_bgcolor="#0f1117", font={"color": "#e8ecf4"})
    return fig


def _build_radar_chart(scores: dict) -> go.Figure:
    cats = [DIMENSION_META[k]["label"] for k in DIMENSION_META]
    vals = [scores.get(k, 5.0) for k in DIMENSION_META]
    cats.append(cats[0]); vals.append(vals[0])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals, theta=cats, fill="toself", fillcolor="rgba(34,197,94,0.15)",
        line=dict(color="#22c55e", width=2), name="Env. Health",
        marker=dict(size=8, color="#22c55e"),
    ))
    fig.add_trace(go.Scatterpolar(
        r=[5.0] * len(cats), theta=cats,
        line=dict(color="#f59e0b", width=1, dash="dash"), name="Moderate",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(visible=True, range=[0, 10], tickvals=[2, 4, 6, 8, 10],
                            gridcolor="#1a4080", tickfont=dict(color="#8b97b0", size=10)),
            angularaxis=dict(gridcolor="#1a4080", tickfont=dict(color="#e8ecf4", size=11)),
        ),
        showlegend=True, legend=dict(font=dict(color="#e8ecf4"), bgcolor="rgba(0,0,0,0)"),
        height=400, margin=dict(t=30, b=30, l=50, r=50),
        paper_bgcolor="#0f1117", font=dict(color="#e8ecf4"),
    )
    return fig


def _build_pollution_map(lat: float, lon: float, all_details: dict) -> str:
    if folium is None:
        return "<p style='color:#8b97b0;'>Install <code>folium</code> for map visualisation.</p>"
    m = folium.Map(location=[lat, lon], zoom_start=12, tiles="CartoDB dark_matter")
    folium.Marker([lat, lon], popup="<b>Analysis Center</b>",
                  icon=folium.Icon(color="blue", icon="crosshairs", prefix="fa")).add_to(m)
    for r, c, lbl in [(2000, "#8b97b0", "2 km"), (5000, "#6b7280", "5 km"), (10000, "#4b5563", "10 km")]:
        folium.Circle([lat, lon], radius=r, color=c, fill=False, dash_array="5", popup=lbl).add_to(m)
    layer_cfg = {
        "industrial": ("red", "Industrial Sources"),
        "water_pollution": ("orange", "Water Pollution"),
        "noise": ("purple", "Noise Sources"),
        "waste": ("darkred", "Waste Sites"),
        "green_buffer": ("green", "Green Buffers"),
    }
    for dim_key, (clr, lbl) in layer_cfg.items():
        elements = all_details.get(dim_key, {}).get("elements", [])
        fg = folium.FeatureGroup(name=lbl)
        for elat, elon, tags in elements[:40]:
            name = tags.get("name", tags.get("amenity", tags.get("landuse", dim_key)))
            folium.CircleMarker(
                [elat, elon], radius=5, color=clr, fill=True,
                fill_color=clr, fill_opacity=0.7,
                popup=f"<b>{name}</b><br>{dim_key.replace('_', ' ').title()}",
            ).add_to(fg)
        fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m._repr_html_()


def _pollutant_bar_html(name: str, value: float, who_limit: float, color: str) -> str:
    ratio = min(value / who_limit, 3.0) if who_limit > 0 else 0
    pct = min(ratio * 33.33, 100.0)
    sc = "#22c55e" if ratio <= 1 else ("#f59e0b" if ratio <= 2 else "#ef4444")
    ex = f" ({ratio:.1f}x WHO)" if ratio > 1 else ""
    return (f'<div style="margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;font-size:13px;color:#e8ecf4;">'
            f'<span>{name}</span><span style="color:{sc};">{value:.1f} ug/m3{ex}</span></div>'
            f'<div style="background:#1a1a2e;border-radius:4px;height:8px;margin-top:2px;">'
            f'<div style="background:{color};width:{pct:.0f}%;height:100%;border-radius:4px;"></div>'
            f'</div></div>')


def _metric_card(label: str, score: float, detail: str, icon: str) -> str:
    c = _score_color(score)
    return (f'<div style="background:#16213e;border:1px solid #1a4080;border-radius:10px;'
            f'padding:14px;margin-bottom:10px;border-left:4px solid {c};">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;"><div>'
            f'<span style="color:#8b97b0;font-size:12px;text-transform:uppercase;">{label}</span>'
            f'<div style="color:{c};font-size:28px;font-weight:700;">{score:.1f}'
            f'<span style="font-size:14px;color:#8b97b0;">/10</span></div></div>'
            f'<div style="font-size:28px;color:{c};opacity:0.6;">'
            f'<i class="fa fa-{icon}"></i></div></div>'
            f'<div style="color:#8b97b0;font-size:11px;margin-top:6px;">{detail}</div></div>')


def _risk_assessment_html(scores: dict, details: dict) -> str:
    overall = _overall_health_score(scores)
    risks = []
    aq = details.get("air_quality", {})
    for key, label in [("pm2_5", "PM2.5"), ("nitrogen_dioxide", "NO2")]:
        val = aq.get(key, 0) or 0
        if val > WHO_LIMITS[key]:
            risks.append(f"{label} is {val / WHO_LIMITS[key]:.1f}x above WHO guideline")
    ind_c = details.get("industrial", {}).get("count", 0)
    if ind_c > 10:
        risks.append(f"High industrial density: {ind_c} sources within 10 km")
    wp = details.get("water_pollution", {})
    if wp.get("source_count", 0) > 5 and wp.get("weekly_precipitation_mm", 0) > 20:
        risks.append(f"Elevated runoff risk: {wp['source_count']} sources + {wp['weekly_precipitation_mm']:.0f} mm rain")
    ns = details.get("noise", {})
    if ns.get("airports", 0) > 0:
        risks.append("Airport proximity - significant noise exposure")
    if ns.get("highways", 0) > 5:
        risks.append(f"Dense highway network ({ns['highways']} major roads within 2 km)")
    if details.get("waste", {}).get("landfills", 0) > 2:
        risks.append(f"Multiple landfills ({details['waste']['landfills']}) - groundwater risk")
    if details.get("green_buffer", {}).get("total", 0) < 3:
        risks.append("Limited green buffer zones - reduced natural pollution filtering")

    oc = _score_color(overall)
    ol = _health_label(overall)
    if risks:
        items = "".join(f'<li style="margin-bottom:6px;color:#e8ecf4;">{r}</li>' for r in risks)
        rhtml = f'<ul style="margin:0;padding-left:18px;">{items}</ul>'
    else:
        rhtml = '<div style="color:#22c55e;padding:8px;">No significant risks identified.</div>'
    return (f'<div style="background:#16213e;border:1px solid #1a4080;border-radius:10px;padding:16px;">'
            f'<h4 style="color:#e8ecf4;margin-top:0;">Risk Assessment</h4>'
            f'<div style="display:flex;align-items:center;margin-bottom:12px;">'
            f'<div style="font-size:36px;font-weight:800;color:{oc};margin-right:12px;">{overall:.1f}</div>'
            f'<div><div style="color:{oc};font-size:16px;font-weight:600;">{ol}</div>'
            f'<div style="color:#8b97b0;font-size:12px;">Overall Environmental Health</div></div></div>'
            f'<div style="border-top:1px solid #1a4080;padding-top:10px;">'
            f'<div style="color:#8b97b0;font-size:12px;margin-bottom:6px;text-transform:uppercase;">'
            f'Identified Concerns</div>{rhtml}</div></div>')


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def render_pollution_tracker_tab():
    """Single entry point for the Pollution & Contamination Tracker tab."""
    st.markdown("## Pollution & Contamination Tracker")
    st.caption("Environmental pollution analysis & source identification across 6 dimensions")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, format="%.4f", key="poltrack_lat")
    lon = c2.number_input("Longitude", value=12.4964, format="%.4f", key="poltrack_lon")

    if not st.button("Track Pollution", key="poltrack_btn"):
        st.info("Enter coordinates and click **Track Pollution** to begin environmental analysis.")
        return

    # Fetch all 6 dimensions
    with st.spinner("Scanning pollution sources across 6 dimensions..."):
        aq_data = _fetch_air_quality(lat, lon)
        precip_data = _fetch_precipitation(lat, lon)
        industrial_data = _fetch_industrial_sources(lat, lon)
        water_data = _fetch_water_pollution_sources(lat, lon)
        noise_data = _fetch_noise_sources(lat, lon)
        waste_data = _fetch_waste_infrastructure(lat, lon)
        green_data = _fetch_green_buffers(lat, lon)

    # Compute scores
    aq_score, aq_det = _score_air_quality(aq_data)
    ind_score, ind_det = _score_industrial(industrial_data)
    wp_score, wp_det = _score_water_pollution(water_data, precip_data)
    ns_score, ns_det = _score_noise(noise_data)
    ws_score, ws_det = _score_waste(waste_data)
    gb_score, gb_det = _score_green_buffers(green_data)

    scores = {"air_quality": aq_score, "industrial": ind_score, "water_pollution": wp_score,
              "noise": ns_score, "waste": ws_score, "green_buffer": gb_score}
    all_det = {"air_quality": aq_det, "industrial": ind_det, "water_pollution": wp_det,
               "noise": ns_det, "waste": ws_det, "green_buffer": gb_det}

    overall = _overall_health_score(scores)
    oc = _score_color(overall)
    ol = _health_label(overall)

    # Overall score header
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#16213e,#0f3460);border:1px solid #1a4080;'
        f'border-radius:12px;padding:20px;text-align:center;margin-bottom:16px;">'
        f'<div style="color:#8b97b0;font-size:13px;text-transform:uppercase;letter-spacing:1px;">'
        f'Overall Environmental Health</div>'
        f'<div style="font-size:56px;font-weight:800;color:{oc};line-height:1.1;">'
        f'{overall:.1f}<span style="font-size:20px;color:#8b97b0;">/10</span></div>'
        f'<div style="color:{oc};font-size:18px;font-weight:600;">{ol}</div>'
        f'<div style="color:#8b97b0;font-size:12px;margin-top:4px;">{lat:.4f}N, {lon:.4f}E</div></div>',
        unsafe_allow_html=True,
    )

    # AQI gauge and pollutant bars
    if "status" not in aq_det:
        st.plotly_chart(_build_aqi_gauge(aq_det.get("european_aqi", 50, key="poltra_pchart1")), use_container_width=True, key="poltrack_aqi_gauge")
        st.markdown("#### Pollutant Concentrations vs WHO Guidelines")
        bars = ""
        for pkey, (pname, pcolor) in POLLUTANT_DISPLAY.items():
            val = aq_det.get(pkey, 0) or 0
            bars += _pollutant_bar_html(pname, val, WHO_LIMITS.get(pkey, 100), pcolor)
        st.markdown(f'<div style="background:#16213e;border:1px solid #1a4080;'
                    f'border-radius:10px;padding:16px;">{bars}</div>', unsafe_allow_html=True)
    else:
        st.warning("Air quality data unavailable for this location.")

    st.markdown("---")

    # Dimension score cards
    st.markdown("#### Dimension Scores")
    col_a, col_b = st.columns(2)
    dim_texts = {
        "air_quality": f"AQI: {aq_det.get('european_aqi', 'N/A')} | PM2.5: {aq_det.get('pm2_5', 'N/A')} ug/m3",
        "industrial": f"{ind_det.get('count', 0)} industrial sources in 10 km",
        "water_pollution": f"{wp_det.get('source_count', 0)} sources | {wp_det.get('weekly_precipitation_mm', 0)} mm rain/wk",
        "noise": f"Hwy: {ns_det.get('highways', 0)} | Rail: {ns_det.get('railways', 0)} | "
                 f"Air: {ns_det.get('airports', 0)} | Night: {ns_det.get('nightlife', 0)}",
        "waste": f"Recycle: {ws_det.get('recycling_centers', 0)} | Landfill: {ws_det.get('landfills', 0)} | "
                 f"Disposal: {ws_det.get('disposal_sites', 0)}",
        "green_buffer": f"Parks: {gb_det.get('parks', 0)} | Forest: {gb_det.get('forests', 0)} | "
                        f"Reserves: {gb_det.get('nature_reserves', 0)}",
    }
    for i, key in enumerate(DIMENSION_META):
        meta = DIMENSION_META[key]
        card = _metric_card(meta["label"], scores[key], dim_texts.get(key, ""), meta["icon"])
        (col_a if i % 2 == 0 else col_b).markdown(card, unsafe_allow_html=True)

    st.markdown("---")

    # Radar chart
    st.markdown("#### Environmental Health Radar")
    st.plotly_chart(_build_radar_chart(scores, key="poltra_pchart2"), use_container_width=True, key="poltrack_radar")

    st.markdown("---")

    # Risk assessment
    st.markdown(_risk_assessment_html(scores, all_det), unsafe_allow_html=True)

    st.markdown("---")

    # Pollution map
    st.markdown("#### Pollution Source Map")
    st.caption("Toggle layers to view different pollution source categories")
    components.html(_build_pollution_map(lat, lon, all_det), height=520, scrolling=False)

    # Raw data expander
    with st.expander("Raw Data Summary", expanded=False):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.markdown("**Air Quality**")
            if "status" not in aq_det:
                for pk in POLLUTANT_DISPLAY:
                    st.text(f"  {pk}: {aq_det.get(pk, 'N/A')}")
            else:
                st.text("  Unavailable")
            st.markdown("**Industrial**")
            st.text(f"  Count: {ind_det.get('count', 0)}")
        with sc2:
            st.markdown("**Water Pollution**")
            st.text(f"  Sources: {wp_det.get('source_count', 0)}")
            st.text(f"  Rain 7d: {wp_det.get('weekly_precipitation_mm', 0)} mm")
            st.markdown("**Noise**")
            for nk in ["highways", "railways", "airports", "nightlife"]:
                st.text(f"  {nk}: {ns_det.get(nk, 0)}")
        with sc3:
            st.markdown("**Waste**")
            for wk in ["recycling_centers", "landfills", "disposal_sites"]:
                st.text(f"  {wk}: {ws_det.get(wk, 0)}")
            st.markdown("**Green Buffers**")
            for gk in ["parks", "forests", "nature_reserves", "total"]:
                st.text(f"  {gk}: {gb_det.get(gk, 0)}")

    # Methodology expander
    with st.expander("Scoring Methodology", expanded=False):
        st.markdown(
            "**Environmental Health Score** is computed across 6 dimensions, "
            "each rated 0-10 where 10 = healthiest:\n\n"
            "| Dimension | Weight | Source | Radius |\n"
            "|---|---|---|---|\n"
            "| Air Quality | 25% | Open-Meteo AQ API | Point |\n"
            "| Industrial Sources | 20% | Overpass API | 10 km |\n"
            "| Water Pollution | 15% | Overpass + Weather | 10 km |\n"
            "| Noise Pollution | 15% | Overpass API | 2 km |\n"
            "| Waste Infrastructure | 10% | Overpass API | 10 km |\n"
            "| Green Buffers | 15% | Overpass API | 5 km |\n\n"
            "**Color coding:** 0-2 Red (hazardous), 3-4 Orange (poor), "
            "5-6 Yellow (moderate), 7-8 Light green (good), 9-10 Green (excellent).\n\n"
            "Pollution dimensions use inverted scoring (more pollution = lower score). "
            "Green buffers use direct scoring. WHO exceedances are flagged in Risk Assessment."
        )
