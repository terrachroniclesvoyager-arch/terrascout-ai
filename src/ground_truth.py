"""
Ground Truth & Data Confidence module for TerraScout AI.
Assesses data reliability for any location by querying 8 independent sources
and scoring each: EXCELLENT, GOOD, MODERATE, SPARSE, NO DATA.
Overall Data Confidence Index = weighted average. All APIs free, no keys.
"""

import math
import logging
from datetime import datetime, timedelta

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Theme / constants
# ---------------------------------------------------------------------------
_CLR = {
    "bg": "#1a1a2e", "card": "rgba(26,26,46,0.85)", "border": "#2a3a5c",
    "text": "#e8ecf4", "muted": "#8b97b0", "green": "#22c55e",
    "yellow": "#eab308", "orange": "#f97316", "red": "#ef4444",
    "blue": "#3b82f6", "purple": "#8b5cf6", "cyan": "#06b6d4",
}

_TIERS = [
    ("EXCELLENT", _CLR["green"],  "dense, high-quality data"),
    ("GOOD",      _CLR["cyan"],   "adequate data coverage"),
    ("MODERATE",  _CLR["yellow"], "partial data, gaps likely"),
    ("SPARSE",    _CLR["orange"], "very limited data"),
    ("NO DATA",   _CLR["red"],    "no data returned"),
]

_SOURCE_META = [
    ("OSM Coverage",           "OSM",       1.5),
    ("Elevation Data Quality", "Elevation", 1.0),
    ("Soil Data Coverage",     "Soil",      1.2),
    ("Weather Station Data",   "Weather",   1.0),
    ("Seismic Monitoring",     "Seismic",   0.8),
    ("Geological Survey",      "Geology",   0.9),
    ("Biodiversity Records",   "Biodiv.",   0.8),
    ("Satellite Imagery",      "Satellite", 0.8),
]

_PRESETS = {
    "Custom": None, "London, UK": (51.5074, -0.1278),
    "Sahara Desert": (23.4162, 25.6628), "Amazon Rainforest": (-3.4653, -62.2159),
    "Tokyo, Japan": (35.6762, 139.6503), "McMurdo, Antarctica": (-77.85, 166.6667),
    "New York, USA": (40.7128, -74.006), "Rural Mongolia": (47.0, 105.0),
    "Nairobi, Kenya": (-1.2921, 36.8219), "Svalbard, Norway": (78.2232, 15.6267),
    "Sydney, Australia": (-33.8688, 151.2093),
}

_RECS = {
    "OSM Coverage": "Area poorly mapped in OSM. Consider local mapping or commercial satellite providers.",
    "Elevation Data Quality": "SRTM data incomplete. Use LiDAR or local DEM surveys.",
    "Soil Data Coverage": "SoilGrids lacks data here. Ground-level soil sampling recommended.",
    "Weather Station Data": "Weather data incomplete. Deploy local monitoring or use ERA5 reanalysis.",
    "Seismic Monitoring": "Sparse seismic coverage. Consult regional geological surveys.",
    "Geological Survey": "No bedrock data. Commission a geotechnical survey.",
    "Biodiversity Records": "Few observations. Citizen science or professional field surveys recommended.",
    "Satellite Imagery": "Tile unavailable. Check commercial providers (Planet, Maxar).",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _tier(score: float):
    """Return (label, colour, desc) for a 0-100 confidence score."""
    if score >= 80: return _TIERS[0]
    if score >= 60: return _TIERS[1]
    if score >= 40: return _TIERS[2]
    if score >= 15: return _TIERS[3]
    return _TIERS[4]


def _tl(score: float) -> str:
    """Traffic-light coloured circle."""
    return f'<span style="color:{_tier(score)[1]};font-size:1.5em;">&#9679;</span>'


# ---------------------------------------------------------------------------
# 1. OSM Coverage (Overpass API)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_osm(lat: float, lon: float) -> dict:
    query = f"[out:json][timeout:10];node(around:3000,{lat},{lon});out count;"
    try:
        r = requests.post("https://overpass-api.de/api/interpreter",
                          data={"data": query}, timeout=10)
        r.raise_for_status()
        total = 0
        for el in r.json().get("elements", []):
            cnt = el.get("tags", {}).get("total", el.get("tags", {}).get("nodes", 0))
            try: total = int(cnt)
            except (ValueError, TypeError): total = 0
        return {"total_nodes": total, "error": None}
    except Exception as e:
        logger.warning("Overpass OSM fetch failed: %s", e)
        return {"total_nodes": 0, "error": str(e)}


def _score_osm(d: dict) -> tuple:
    if d.get("error"): return 0.0, f"API error: {d['error']}"
    n = d["total_nodes"]
    thresholds = [(5000, 95), (2000, 80), (500, 60), (100, 40), (1, 20)]
    score = next((s for t, s in thresholds if n >= t), 0.0)
    return float(score), f"{n:,} mapped features within 3 km"


# ---------------------------------------------------------------------------
# 2. Elevation Data Quality (Open Topo Data / SRTM)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_elev(lat: float, lon: float) -> dict:
    pts = [f"{lat},{lon}"] + [f"{round(lat+d, 6)},{round(lon+d, 6)}"
                               for d in (0.01, -0.01, 0.02, -0.02)]
    url = f"https://api.opentopodata.org/v1/srtm30m?locations={'|'.join(pts)}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        res = r.json().get("results", [])
        valid = [x["elevation"] for x in res if x.get("elevation") is not None]
        return {"total": len(res), "valid": len(valid), "elevs": valid, "error": None}
    except Exception as e:
        logger.warning("Open Topo Data fetch failed: %s", e)
        return {"total": 0, "valid": 0, "elevs": [], "error": str(e)}


def _score_elev(d: dict) -> tuple:
    if d.get("error"): return 0.0, f"API error: {d['error']}"
    if d["total"] == 0: return 0.0, "No elevation points returned"
    ratio = d["valid"] / d["total"]
    score = 90 if ratio >= 0.9 else 70 if ratio >= 0.7 else 45 if ratio >= 0.4 else 20 if ratio > 0 else 0
    detail = f"{d['valid']}/{d['total']} valid points ({ratio*100:.0f}%)"
    if d["elevs"]:
        detail += f", avg {sum(d['elevs'])/len(d['elevs']):.0f} m"
    return float(score), detail


# ---------------------------------------------------------------------------
# 3. Soil Data Coverage (ISRIC SoilGrids v2.0)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_soil(lat: float, lon: float) -> dict:
    url = ("https://rest.isric.org/soilgrids/v2.0/properties/query"
           f"?lon={lon}&lat={lat}"
           "&property=clay&property=sand&property=soc&depth=0-5cm&value=mean")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        layers = r.json().get("properties", {}).get("layers", [])
        props = {}
        for ly in (layers if isinstance(layers, list) else []):
            nm = ly.get("name", "?")
            depths = ly.get("depths", [])
            props[nm] = depths[0].get("values", {}).get("mean") if depths else None
        return {"properties": props, "error": None}
    except Exception as e:
        logger.warning("SoilGrids fetch failed: %s", e)
        return {"properties": {}, "error": str(e)}


def _score_soil(d: dict) -> tuple:
    if d.get("error"): return 0.0, f"API error: {d['error']}"
    props = d["properties"]
    if not props: return 0.0, "No soil properties returned"
    total, valid = len(props), sum(1 for v in props.values() if v is not None)
    ratio = valid / total
    score = 90 if ratio >= 0.9 else 65 if ratio >= 0.6 else 35 if ratio > 0 else 0
    info = ", ".join(f"{k}={'ok' if v is not None else 'null'}" for k, v in props.items())
    return float(score), f"{valid}/{total} valid ({info})"


# ---------------------------------------------------------------------------
# 4. Weather Station Data (Open-Meteo)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_weather(lat: float, lon: float) -> dict:
    url = ("https://api.open-meteo.com/v1/forecast"
           f"?latitude={lat}&longitude={lon}"
           "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
           "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
           "&past_days=7&forecast_days=1&timezone=auto")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        p = r.json()
        cur = p.get("current", {})
        daily = p.get("daily", {})
        cv = sum(1 for k in ("temperature_2m", "relative_humidity_2m", "wind_speed_10m")
                 if cur.get(k) is not None)
        dt = daily.get("temperature_2m_max", [])
        pv = sum(1 for x in daily.get("precipitation_sum", []) if x is not None)
        return {"cv": cv, "dt": len(dt),
                "dv": sum(1 for t in dt if t is not None),
                "pv": pv, "error": None}
    except Exception as e:
        logger.warning("Open-Meteo fetch failed: %s", e)
        return {"cv": 0, "dt": 0, "dv": 0, "pv": 0, "error": str(e)}


def _score_weather(d: dict) -> tuple:
    if d.get("error"): return 0.0, f"API error: {d['error']}"
    parts, score = [], 0.0
    if d["cv"] >= 3: score += 40; parts.append(f"{d['cv']}/3 current vars")
    elif d["cv"] >= 1: score += 20; parts.append(f"{d['cv']}/3 current vars")
    else: parts.append("no current data")
    if d["dt"]: score += 30 * (d["dv"] / d["dt"]); parts.append(f"{d['dv']}/{d['dt']} daily valid")
    if d["pv"]: score += min(30, d["pv"] * 5); parts.append(f"{d['pv']} precip records")
    return min(score, 100.0), "; ".join(parts)


# ---------------------------------------------------------------------------
# 5. Seismic Monitoring (USGS)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_seismic(lat: float, lon: float) -> dict:
    end = datetime.utcnow()
    start = end - timedelta(days=365)
    url = ("https://earthquake.usgs.gov/fdsnws/event/1/query"
           f"?format=geojson&latitude={lat}&longitude={lon}"
           f"&maxradiuskm=300&starttime={start:%Y-%m-%d}"
           f"&endtime={end:%Y-%m-%d}&limit=200")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        feats = r.json().get("features", [])
        mags = [f["properties"]["mag"] for f in feats
                if f.get("properties", {}).get("mag") is not None]
        return {"count": len(feats), "mags": mags, "error": None}
    except Exception as e:
        logger.warning("USGS seismic fetch failed: %s", e)
        return {"count": 0, "mags": [], "error": str(e)}


def _score_seismic(d: dict) -> tuple:
    if d.get("error"): return 0.0, f"API error: {d['error']}"
    n = d["count"]
    if n >= 50: score, detail = 95.0, f"{n} events/yr - dense monitoring"
    elif n >= 20: score, detail = 80.0, f"{n} events - good monitoring"
    elif n >= 5: score, detail = 60.0, f"{n} events - moderate monitoring"
    elif n >= 1: score, detail = 40.0, f"{n} events - sparse monitoring"
    else: score, detail = 50.0, "No events (stable or unmonitored)"
    if d["mags"]:
        detail += f", max M{max(d['mags']):.1f}, avg M{sum(d['mags'])/len(d['mags']):.1f}"
    return score, detail


# ---------------------------------------------------------------------------
# 6. Geological Survey (Macrostrat)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_geology(lat: float, lon: float) -> dict:
    url = f"https://macrostrat.org/api/geologic_units/map?lat={lat}&lng={lon}&format=geojson"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        feats = data.get("success", {}).get("data", {}).get("features", [])
        if not feats: feats = data.get("features", [])
        units = []
        for f in (feats if isinstance(feats, list) else []):
            p = f.get("properties", {}) if isinstance(f, dict) else {}
            units.append({"name": p.get("unit_name") or p.get("name", "Unknown"),
                          "lith": p.get("lith", p.get("lithology", "Unknown")),
                          "period": p.get("t_int_name", p.get("period", ""))})
        return {"units": units, "error": None}
    except Exception as e:
        logger.warning("Macrostrat fetch failed: %s", e)
        return {"units": [], "error": str(e)}


def _score_geology(d: dict) -> tuple:
    if d.get("error"): return 0.0, f"API error: {d['error']}"
    units = d["units"]
    if not units: return 5.0, "No geological unit data for this location"
    n = len(units)
    has_lith = sum(1 for u in units if u.get("lith") and u["lith"] != "Unknown")
    has_age = sum(1 for u in units if u.get("period"))
    comp = (has_lith + has_age) / (n * 2) if n else 0
    score = 90 if (n >= 3 and comp >= 0.7) else 70 if (n >= 2 and comp >= 0.5) else 50 if n >= 1 else 10
    return float(score), f"{n} unit(s): {', '.join(u['name'] for u in units[:3])} ({comp*100:.0f}% complete)"


# ---------------------------------------------------------------------------
# 7. Biodiversity Records (iNaturalist)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_biodiv(lat: float, lon: float) -> dict:
    url = f"https://api.inaturalist.org/v1/observations?lat={lat}&lng={lon}&radius=10&per_page=0"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return {"total": r.json().get("total_results", 0), "error": None}
    except Exception as e:
        logger.warning("iNaturalist fetch failed: %s", e)
        return {"total": 0, "error": str(e)}


def _score_biodiv(d: dict) -> tuple:
    if d.get("error"): return 0.0, f"API error: {d['error']}"
    n = d["total"]
    thresholds = [(10000, 95), (3000, 80), (500, 60), (50, 35), (1, 15)]
    score = next((s for t, s in thresholds if n >= t), 0.0)
    return float(score), f"{n:,} iNaturalist observations within 10 km"


# ---------------------------------------------------------------------------
# 8. Satellite Imagery (NASA GIBS)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_satellite(lat: float, lon: float) -> dict:
    zoom, n = 6, 2 ** 6
    x = max(0, min(int((lon + 180) / 360 * n), n - 1))
    lat_r = math.radians(lat)
    y = max(0, min(int((1 - math.asinh(math.tan(lat_r)) / math.pi) / 2 * n), n - 1))
    url = (f"https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/"
           f"MODIS_Terra_CorrectedReflectance_TrueColor/default/"
           f"2024-01-15/250m/{zoom}/{y}/{x}.jpg")
    try:
        r = requests.get(url, timeout=10)
        ok = r.status_code == 200 and len(r.content) > 1000
        return {"available": ok, "size": len(r.content), "error": None}
    except Exception as e:
        logger.warning("NASA GIBS fetch failed: %s", e)
        return {"available": False, "size": 0, "error": str(e)}


def _score_satellite(d: dict) -> tuple:
    if d.get("error"): return 0.0, f"API error: {d['error']}"
    if not d["available"]: return 15.0, "No satellite tile (may be ocean/polar)"
    sz = d["size"]
    if sz > 50000: return 95.0, f"Tile available ({sz:,} bytes, high detail)"
    if sz > 10000: return 80.0, f"Tile available ({sz:,} bytes)"
    return 65.0, f"Tile available ({sz:,} bytes, low detail)"


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
_FETCHERS = [_fetch_osm, _fetch_elev, _fetch_soil, _fetch_weather,
             _fetch_seismic, _fetch_geology, _fetch_biodiv, _fetch_satellite]
_SCORERS = [_score_osm, _score_elev, _score_soil, _score_weather,
            _score_seismic, _score_geology, _score_biodiv, _score_satellite]


def _compute_all(lat: float, lon: float) -> list:
    results = []
    for i, (name, label, weight) in enumerate(_SOURCE_META):
        raw = _FETCHERS[i](lat, lon)
        score, detail = _SCORERS[i](raw)
        tl, tc, td = _tier(score)
        results.append({"name": name, "label": label, "weight": weight,
                        "score": round(score, 1), "detail": detail,
                        "tier": tl, "tier_color": tc, "tier_desc": td, "raw": raw})
    return results


def _overall(results: list) -> float:
    tw = sum(r["weight"] for r in results)
    return round(sum(r["score"] * r["weight"] for r in results) / tw, 1) if tw else 0.0


# ---------------------------------------------------------------------------
# UI: Radar chart
# ---------------------------------------------------------------------------
def _radar_chart(results: list):
    labels = [r["label"] for r in results]
    scores = [r["score"] for r in results]
    lc, sc = labels + [labels[0]], scores + [scores[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=sc, theta=lc, fill="toself", fillcolor="rgba(34,197,94,0.15)",
        line=dict(color=_CLR["green"], width=2),
        marker=dict(size=6, color=[_tier(s)[1] for s in sc]), name="Confidence"))
    fig.add_trace(go.Scatterpolar(
        r=[60]*len(lc), theta=lc,
        line=dict(color=_CLR["muted"], width=1, dash="dash"), showlegend=False))
    fig.update_layout(
        polar=dict(bgcolor="rgba(26,26,46,0.6)",
                   radialaxis=dict(range=[0, 100], showticklabels=True,
                                   tickfont=dict(size=10, color=_CLR["muted"]),
                                   gridcolor="rgba(100,120,160,0.2)"),
                   angularaxis=dict(tickfont=dict(size=11, color=_CLR["text"]),
                                    gridcolor="rgba(100,120,160,0.2)")),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, margin=dict(l=60, r=60, t=30, b=30), height=400)
    return fig


# ---------------------------------------------------------------------------
# UI: Bar chart
# ---------------------------------------------------------------------------
def _bar_chart(results: list):
    sr = sorted(results, key=lambda x: x["score"])
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[r["name"] for r in sr], x=[r["score"] for r in sr], orientation="h",
        marker=dict(color=[r["tier_color"] for r in sr], line=dict(width=0)),
        text=[f"{r['score']:.0f}" for r in sr], textposition="outside",
        textfont=dict(color=_CLR["text"], size=11),
        hovertemplate="%{y}<br>Score: %{x:.1f}/100<extra></extra>"))
    for thr, lab in [(60, "GOOD"), (40, "MODERATE")]:
        fig.add_vline(x=thr, line=dict(color=_CLR["muted"], dash="dash", width=1),
                      annotation_text=lab, annotation_position="top",
                      annotation_font=dict(size=9, color=_CLR["muted"]))
    fig.update_layout(
        xaxis=dict(range=[0, 110], title="Confidence Score",
                   tickfont=dict(color=_CLR["muted"]), title_font=dict(color=_CLR["muted"]),
                   gridcolor="rgba(100,120,160,0.15)"),
        yaxis=dict(tickfont=dict(color=_CLR["text"], size=11)),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=160, r=40, t=20, b=40), height=340, showlegend=False)
    return fig


# ---------------------------------------------------------------------------
# UI: Tier donut
# ---------------------------------------------------------------------------
def _tier_donut(results: list):
    tc, tcol = {}, {}
    for r in results:
        tc[r["tier"]] = tc.get(r["tier"], 0) + 1
        tcol[r["tier"]] = r["tier_color"]
    labs, vals = list(tc.keys()), list(tc.values())
    fig = go.Figure(data=[go.Pie(
        labels=labs, values=vals, hole=0.55,
        marker=dict(colors=[tcol[l] for l in labs],
                    line=dict(color=_CLR["bg"], width=2)),
        textinfo="label+value", textfont=dict(color=_CLR["text"], size=12),
        hovertemplate="%{label}: %{value} source(s)<extra></extra>")])
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False, margin=dict(l=20, r=20, t=10, b=10), height=280,
        annotations=[dict(text="Tier<br>Split", x=0.5, y=0.5,
                          font=dict(size=14, color=_CLR["muted"]), showarrow=False)])
    return fig


# ---------------------------------------------------------------------------
# UI: Coverage map
# ---------------------------------------------------------------------------
def _coverage_map(lat: float, lon: float, results: list):
    fig = go.Figure()
    angles = [i * 45 for i in range(8)]
    radii = [3, 1.5, 2, 5, 300, 50, 10, 100]
    for i, r in enumerate(results):
        a = math.radians(angles[i])
        olat = (radii[i] / 111.0) * 0.3 * math.cos(a)
        olon = (radii[i] / (111.0 * max(math.cos(math.radians(lat)), 0.01))) * 0.3 * math.sin(a)
        fig.add_trace(go.Scattermapbox(
            lat=[lat + olat], lon=[lon + olon], mode="markers+text",
            marker=dict(size=18, color=r["tier_color"], opacity=0.85),
            text=[r["label"]], textposition="top center",
            textfont=dict(size=10, color=_CLR["text"]), name=r["name"],
            hovertemplate=f"<b>{r['name']}</b><br>{r['score']}/100 - {r['tier']}<extra></extra>"))
    fig.add_trace(go.Scattermapbox(
        lat=[lat], lon=[lon], mode="markers",
        marker=dict(size=12, color=_CLR["blue"]), name="Target", showlegend=False))
    fig.update_layout(
        mapbox=dict(style="carto-darkmatter", center=dict(lat=lat, lon=lon), zoom=8),
        paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0, r=0, t=0, b=0),
        height=400, showlegend=False)
    return fig


# ---------------------------------------------------------------------------
# UI: Metric card HTML
# ---------------------------------------------------------------------------
def _card(r: dict) -> str:
    light = _tl(r["score"])
    bw = max(r["score"], 2)
    return (
        f'<div style="background:{_CLR["card"]};border:1px solid {_CLR["border"]};'
        f'border-left:4px solid {r["tier_color"]};border-radius:10px;'
        f'padding:14px 16px;margin-bottom:10px;">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;">'
        f'<span style="font-size:0.8em;color:{_CLR["muted"]};text-transform:uppercase;'
        f'letter-spacing:1px;">{r["name"]}</span>'
        f'<div style="display:flex;align-items:center;gap:8px;">{light}'
        f'<span style="font-size:1.3em;font-weight:700;color:{r["tier_color"]};">'
        f'{r["score"]}</span></div></div>'
        f'<div style="margin:8px 0 4px;background:rgba(100,120,160,0.15);'
        f'border-radius:4px;height:6px;overflow:hidden;">'
        f'<div style="width:{bw}%;height:100%;background:{r["tier_color"]};'
        f'border-radius:4px;"></div></div>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-top:6px;">'
        f'<span style="font-size:0.78em;color:{_CLR["text"]};max-width:75%;">{r["detail"]}</span>'
        f'<span style="font-size:0.75em;font-weight:600;color:{r["tier_color"]};'
        f'letter-spacing:1px;">{r["tier"]}</span></div></div>'
    )


# ---------------------------------------------------------------------------
# UI: Gap analysis
# ---------------------------------------------------------------------------
def _gap_analysis(results: list):
    gaps = [r for r in results if r["score"] < 40]
    moderate = [r for r in results if 40 <= r["score"] < 60]
    strong = [r for r in results if r["score"] >= 60]
    if gaps:
        st.markdown("#### Data Gaps Identified")
        for g in gaps:
            rec = _RECS.get(g["name"], "Ground verification recommended.")
            st.markdown(
                f'<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.3);'
                f'border-radius:8px;padding:12px;margin-bottom:8px;">'
                f'<div style="color:{_CLR["red"]};font-weight:600;">'
                f'{g["name"]} &mdash; {g["tier"]} ({g["score"]})</div>'
                f'<div style="color:{_CLR["text"]};font-size:0.85em;margin-top:4px;">'
                f'{g["detail"]}</div>'
                f'<div style="color:{_CLR["yellow"]};font-size:0.82em;margin-top:6px;">'
                f'Recommendation: {rec}</div></div>', unsafe_allow_html=True)
    if moderate:
        st.markdown("#### Moderate Coverage Areas")
        for m in moderate:
            rec = _RECS.get(m["name"], "Ground verification recommended.")
            st.markdown(
                f'<div style="background:rgba(234,179,8,0.06);border:1px solid rgba(234,179,8,0.25);'
                f'border-radius:8px;padding:10px;margin-bottom:6px;">'
                f'<div style="color:{_CLR["yellow"]};font-weight:600;">'
                f'{m["name"]} &mdash; {m["tier"]} ({m["score"]})</div>'
                f'<div style="color:{_CLR["muted"]};font-size:0.82em;margin-top:4px;">'
                f'{m["detail"]} &mdash; {rec}</div></div>', unsafe_allow_html=True)
    if strong:
        st.markdown("#### Well-Covered Sources")
        st.markdown("Strong data from: " +
                    ", ".join(f"**{s['name']}** ({s['score']})" for s in strong))


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def render_ground_truth_tab():
    """Render the Ground Truth & Data Confidence analysis tab."""

    st.markdown("## Ground Truth & Data Confidence")
    st.caption("Assesses data availability across 8 independent sources. "
               "Sparse data = low confidence in any analysis.")

    # -- Location inputs --
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, format="%.4f",
                          key="gtruth_lat", min_value=-90.0, max_value=90.0)
    lon = c2.number_input("Longitude", value=12.4964, format="%.4f",
                          key="gtruth_lon", min_value=-180.0, max_value=180.0)

    preset = st.selectbox("Preset locations", list(_PRESETS.keys()), key="gtruth_preset")
    if preset != "Custom" and _PRESETS[preset]:
        lat, lon = _PRESETS[preset]

    if not st.button("Assess Data Confidence", key="gtruth_btn", type="primary"):
        st.info("Enter coordinates and click **Assess Data Confidence** to begin.")
        return

    # -- Fetch & score all sources --
    with st.spinner("Querying 8 data sources for coverage assessment..."):
        results = _compute_all(lat, lon)

    ov = _overall(results)
    ov_tier, ov_color, ov_desc = _tier(ov)

    # -- Overall banner --
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{_CLR["card"]},rgba(26,26,46,0.95));'
        f'border:2px solid {ov_color};border-radius:14px;padding:24px;'
        f'text-align:center;margin:16px 0;">'
        f'<div style="font-size:0.85em;color:{_CLR["muted"]};letter-spacing:3px;'
        f'text-transform:uppercase;">Data Confidence Index</div>'
        f'<div style="font-size:3.2em;font-weight:800;color:{ov_color};margin:8px 0;">{ov}</div>'
        f'<div style="font-size:1.3em;font-weight:700;color:{ov_color};'
        f'letter-spacing:3px;">{ov_tier}</div>'
        f'<div style="font-size:0.82em;color:{_CLR["text"]};margin-top:10px;">'
        f'{lat:.4f}, {lon:.4f} &mdash; {ov_desc}</div>'
        f'<div style="font-size:0.75em;color:{_CLR["muted"]};margin-top:4px;">'
        f'8 sources checked &middot; weighted average</div></div>',
        unsafe_allow_html=True)

    # -- Quick metrics row --
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Excellent", sum(1 for r in results if r["tier"] == "EXCELLENT"))
    mc2.metric("Good", sum(1 for r in results if r["tier"] == "GOOD"))
    mc3.metric("Data Gaps", sum(1 for r in results if r["score"] < 40))
    mc4.metric("Avg Score", f"{ov:.0f}/100")

    st.divider()

    # -- Source detail cards --
    st.markdown("### Source-by-Source Assessment")
    ca, cb = st.columns(2)
    for i, r in enumerate(results):
        (ca if i % 2 == 0 else cb).markdown(_card(r), unsafe_allow_html=True)

    st.divider()

    # -- Visualisations --
    st.markdown("### Confidence Visualisations")
    t1, t2, t3, t4 = st.tabs(["Radar Chart", "Bar Chart", "Tier Distribution", "Coverage Map"])
    with t1:
        st.plotly_chart(_radar_chart(results, key="grotru_pchart1"), use_container_width=True, key="gtruth_radar")
    with t2:
        st.plotly_chart(_bar_chart(results, key="grotru_pchart2"), use_container_width=True, key="gtruth_bar")
    with t3:
        st.plotly_chart(_tier_donut(results, key="grotru_pchart3"), use_container_width=True, key="gtruth_donut")
    with t4:
        st.plotly_chart(_coverage_map(lat, lon, results, key="grotru_pchart4"), use_container_width=True,
                        key="gtruth_map")

    st.divider()

    # -- Gap analysis --
    st.markdown("### Data Gap Analysis & Recommendations")
    _gap_analysis(results)

    st.divider()

    # -- Detailed expandable per source --
    st.markdown("### Detailed Source Breakdowns")
    for r in results:
        with st.expander(f"{r['name']} ({r['tier']} - {r['score']}/100)"):
            st.markdown(f"**Score:** {r['score']}/100 &mdash; **{r['tier']}**")
            st.markdown(f"**Detail:** {r['detail']}")
            st.markdown(f"**Weight:** {r['weight']}  |  **Tier:** {r['tier_desc']}")
            if r["score"] < 60:
                st.warning(_RECS.get(r["name"], "Ground verification recommended."))
            raw = r.get("raw", {})
            if isinstance(raw, dict):
                show = {k: v for k, v in raw.items()
                        if k != "error" and not isinstance(v, bytes)}
                if show:
                    st.json(show)

    st.divider()

    # -- Methodology --
    st.markdown("### Methodology")
    st.markdown("""
The Data Confidence Index aggregates coverage from **8 independent sources**, each weighted:

| Source | Radius | Weight | Checks |
|--------|--------|--------|--------|
| OSM Coverage | 3 km | 1.5 | Mapped feature count (Overpass) |
| Elevation Quality | Point+4 | 1.0 | SRTM valid returns |
| Soil Data | Point | 1.2 | SoilGrids property coverage |
| Weather Station | Point | 1.0 | Current + 7-day completeness |
| Seismic Monitoring | 300 km | 0.8 | USGS event catalog density |
| Geological Survey | Point | 0.9 | Macrostrat bedrock data |
| Biodiversity Records | 10 km | 0.8 | iNaturalist observation count |
| Satellite Imagery | Tile | 0.8 | NASA GIBS MODIS tile check |

**Tiers:** EXCELLENT (>=80) | GOOD (>=60) | MODERATE (>=40) | SPARSE (>=15) | NO DATA (<15)

Overall index = **weighted average** across all sources.
    """)
