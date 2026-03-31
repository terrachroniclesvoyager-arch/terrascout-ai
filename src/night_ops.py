# -*- coding: utf-8 -*-
"""
TerraScout AI - Night Operations & Darkness Assessment Module
Evaluates area suitability for night operations, astronomy, or dark-sky
activities across six dimensions: light pollution, urban proximity,
cloud cover forecast, moon phase, elevation advantage, and natural concealment.
Uses: Overpass API, Open-Meteo, Open Topo Data, algorithmic moon phase.
"""

import logging
import math
from datetime import datetime, timezone

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BORTLE_SCALE = {
    1: {"label": "Excellent dark sky", "color": "#0a0a2e",
        "desc": "Zodiacal light, gegenschein visible; Scorpius/Sagittarius dazzling"},
    2: {"label": "Typical dark sky", "color": "#111144",
        "desc": "Airglow visible; M33 easy naked-eye object"},
    3: {"label": "Rural sky", "color": "#1a1a5e",
        "desc": "Some light pollution on horizon; M33 with averted vision"},
    4: {"label": "Rural/suburban transition", "color": "#2a2a78",
        "desc": "Light-pollution domes visible; Milky Way faint"},
    5: {"label": "Suburban sky", "color": "#3b3b90",
        "desc": "Milky Way faint near horizon; clouds brighter than sky"},
    6: {"label": "Bright suburban", "color": "#5050a8",
        "desc": "Milky Way only near zenith; sky greyish above 35 deg"},
    7: {"label": "Suburban/urban transition", "color": "#6868b8",
        "desc": "Greyish-white sky; Milky Way invisible; M31 barely seen"},
    8: {"label": "City sky", "color": "#8888cc",
        "desc": "Sky glows white/orange; only bright constellations"},
    9: {"label": "Inner-city sky", "color": "#aaaadd",
        "desc": "Only Moon, planets & brightest stars visible"},
}

MOON_NAMES = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
              "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
MOON_ICONS = ["\U0001F311", "\U0001F312", "\U0001F313", "\U0001F314",
              "\U0001F315", "\U0001F316", "\U0001F317", "\U0001F318"]

DIM_WEIGHTS = {"light_pollution": 0.30, "urban_proximity": 0.15,
               "cloud_cover": 0.15, "moon_phase": 0.15,
               "elevation": 0.10, "concealment": 0.15}

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


# ---------------------------------------------------------------------------
# Data fetching (all cached, all with timeout + try/except)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def _fetch_light_pollution(lat: float, lon: float) -> dict:
    """Count street lamps, lit roads, commercial/industrial lighting in 5 km."""
    query = f"""[out:json][timeout:25];(
      node["highway"="street_lamp"](around:5000,{lat},{lon});
      way["lit"="yes"](around:5000,{lat},{lon});
      node["man_made"="mast"]["light:type"](around:5000,{lat},{lon});
      way["landuse"~"commercial|industrial|retail"](around:5000,{lat},{lon});
    );out count;"""
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        r.raise_for_status()
        total = int(r.json().get("elements", [{}])[0].get("tags", {}).get("total", 0) or 0)
        return {"count": total, "ok": True}
    except Exception as e:
        logger.warning("Light pollution error: %s", e)
        return {"count": 0, "ok": False}


@st.cache_data(ttl=900)
def _fetch_urban_proximity(lat: float, lon: float) -> dict:
    """Find nearest city/town within 50 km."""
    query = f"""[out:json][timeout:25];(
      node["place"~"city|town"](around:50000,{lat},{lon});
    );out body;"""
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        r.raise_for_status()
        elements = r.json().get("elements", [])
        if not elements:
            return {"distance_km": 50.0, "nearest": "None within 50 km", "ok": True}
        best_dist, best_name = float("inf"), "Unknown"
        for el in elements:
            d = _haversine(lat, lon, el.get("lat", lat), el.get("lon", lon))
            if d < best_dist:
                best_dist, best_name = d, el.get("tags", {}).get("name", "Unnamed")
        return {"distance_km": round(best_dist, 2), "nearest": best_name, "ok": True}
    except Exception as e:
        logger.warning("Urban proximity error: %s", e)
        return {"distance_km": 0, "nearest": "Error", "ok": False}


@st.cache_data(ttl=900)
def _fetch_cloud_cover(lat: float, lon: float) -> dict:
    """7-day hourly cloud-cover forecast from Open-Meteo."""
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&hourly=cloud_cover&timezone=auto&forecast_hours=168")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        h = r.json().get("hourly", {})
        times, covers = h.get("time", []), h.get("cloud_cover", [])
        if not covers:
            return {"avg": 50, "hours": [], "values": [], "ok": False}
        return {"avg": round(sum(covers) / len(covers), 1),
                "hours": times, "values": covers, "ok": True}
    except Exception as e:
        logger.warning("Cloud cover error: %s", e)
        return {"avg": 50, "hours": [], "values": [], "ok": False}


@st.cache_data(ttl=900)
def _fetch_elevation(lat: float, lon: float) -> dict:
    """Elevation in metres from Open Topo Data SRTM 30 m."""
    try:
        r = requests.get(f"https://api.opentopodata.org/v1/srtm30m?locations={lat},{lon}",
                         timeout=10)
        r.raise_for_status()
        res = r.json().get("results", [])
        elev = res[0].get("elevation", 0) if res else 0
        return {"elevation_m": round(elev or 0, 1), "ok": True}
    except Exception as e:
        logger.warning("Elevation error: %s", e)
        return {"elevation_m": 0, "ok": False}


@st.cache_data(ttl=900)
def _fetch_natural_concealment(lat: float, lon: float) -> dict:
    """Forest/scrub cover count within 3 km."""
    query = f"""[out:json][timeout:25];(
      way["natural"~"wood|scrub"](around:3000,{lat},{lon});
      way["landuse"="forest"](around:3000,{lat},{lon});
      relation["landuse"="forest"](around:3000,{lat},{lon});
      relation["natural"="wood"](around:3000,{lat},{lon});
    );out count;"""
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        r.raise_for_status()
        total = int(r.json().get("elements", [{}])[0].get("tags", {}).get("total", 0) or 0)
        return {"features": total, "ok": True}
    except Exception as e:
        logger.warning("Concealment error: %s", e)
        return {"features": 0, "ok": False}


# ---------------------------------------------------------------------------
# Algorithmic helpers
# ---------------------------------------------------------------------------

def _haversine(lat1, lon1, lat2, lon2):
    """Great-circle distance in km."""
    R = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _compute_moon_phase() -> dict:
    """Current moon phase via Julian-day calculation."""
    now = datetime.now(timezone.utc)
    y, mo = now.year, now.month
    day = now.day + now.hour / 24.0
    if mo <= 2:
        y -= 1; mo += 12
    A = int(y / 100)
    JD = int(365.25 * (y + 4716)) + int(30.6001 * (mo + 1)) + day + 2 - A + int(A / 4) - 1524.5
    synodic = 29.53059
    age = (JD - 2451550.26) % synodic  # ref: 2000-01-06 new moon
    illum = (1 - math.cos(2 * math.pi * age / synodic)) / 2 * 100
    idx = int((age / synodic) * 8 + 0.5) % 8
    return {"age_days": round(age, 2), "illumination": round(illum, 1),
            "phase_name": MOON_NAMES[idx], "phase_idx": idx, "icon": MOON_ICONS[idx]}


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def _score_light(count):
    if count <= 0: return 100.0
    return round(max(0, 100 - 25 * math.log10(1 + count) ** 1.5), 1)

def _score_urban(dist_km):
    if dist_km >= 50: return 100.0
    return round(min(100, (dist_km / 50) * 100), 1)

def _score_cloud(avg_pct):
    return round(max(0, 100 - avg_pct), 1)

def _score_moon(illum):
    return round(max(0, 100 - illum), 1)

def _score_elev(elev_m):
    if elev_m <= 0: return 10.0
    return round(min(100, 10 + 30 * math.log10(1 + elev_m)), 1)

def _score_conceal(features):
    if features <= 0: return 5.0
    return round(min(100, 40 * math.log10(1 + features)), 1)


def _estimate_bortle(light_s, urban_s, elev_s):
    """Bortle class 1-9 from light / urban / elevation scores."""
    c = light_s * 0.55 + urban_s * 0.30 + elev_s * 0.15
    thresholds = [(92, 1), (82, 2), (72, 3), (60, 4), (48, 5), (36, 6), (24, 7), (12, 8)]
    for t, b in thresholds:
        if c >= t:
            return b
    return 9


def _composite(scores):
    return round(sum(scores.get(k, 0) * w for k, w in DIM_WEIGHTS.items()), 1)


def _star_visibility(bortle, cloud_avg, moon_illum):
    """Predict naked-eye limiting magnitude and star count."""
    nelm_map = {1: 7.6, 2: 7.1, 3: 6.6, 4: 6.2, 5: 5.6, 6: 5.1, 7: 4.6, 8: 4.0, 9: 3.5}
    base = nelm_map.get(bortle, 5.0)
    eff = max(1.0, base - (cloud_avg / 100) * 3.0 - (moon_illum / 100) * 1.5)
    stars = int(10 ** (0.6 * eff - 1))
    mw = eff >= 5.5
    rating = ("Excellent" if eff >= 6.5 else "Good" if eff >= 5.5
              else "Fair" if eff >= 4.5 else "Poor" if eff >= 3.5 else "Very Poor")
    return {"nelm": round(eff, 1), "visible_stars": stars,
            "milky_way": mw, "deep_sky": eff >= 5.0, "rating": rating}


# ---------------------------------------------------------------------------
# Plotly charts
# ---------------------------------------------------------------------------

def _bortle_gauge(bortle):
    info = BORTLE_SCALE[bortle]
    steps = [{"range": [i, i + 1], "color": BORTLE_SCALE[i]["color"]} for i in range(1, 9)]
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=bortle,
        number={"font": {"size": 52, "color": "#e0e0ff"}},
        title={"text": f"Bortle Class: {info['label']}",
               "font": {"size": 16, "color": "#c0c0e0"}},
        gauge={"axis": {"range": [1, 9], "dtick": 1,
                        "tickfont": {"color": "#9999bb"}, "tickcolor": "#555588"},
               "bar": {"color": info["color"], "thickness": 0.35},
               "bgcolor": "#12122a", "borderwidth": 2, "bordercolor": "#333366",
               "steps": steps,
               "threshold": {"line": {"color": "#ffdd44", "width": 3},
                             "thickness": 0.8, "value": bortle}}))
    fig.update_layout(height=280, margin=dict(t=60, b=20, l=30, r=30),
                      paper_bgcolor="#0b0b1e", font={"color": "#c0c0e0"})
    return fig


def _cloud_chart(hours, values):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours, y=values, fill="tozeroy",
        fillcolor="rgba(100,120,200,0.25)",
        line=dict(color="#7788dd", width=1.5), name="Cloud Cover %",
        hovertemplate="%{x}<br>Cloud: %{y}%<extra></extra>"))
    fig.add_hline(y=30, line_dash="dash", line_color="#44cc88",
                  annotation_text="Good threshold (30%)",
                  annotation_font_color="#44cc88")
    fig.update_layout(
        title=dict(text="7-Day Cloud Cover Forecast",
                   font=dict(size=14, color="#c0c0e0")),
        xaxis=dict(title="Time", showgrid=False, color="#888"),
        yaxis=dict(title="Cloud Cover (%)", range=[0, 105],
                   gridcolor="#222244", color="#888"),
        height=300, margin=dict(t=50, b=40, l=50, r=20),
        paper_bgcolor="#0b0b1e", plot_bgcolor="#0e0e24",
        font=dict(color="#c0c0e0"))
    return fig


def _radar_chart(scores):
    labels = ["Light Pollution", "Urban Distance", "Clear Sky",
              "Moon Darkness", "Elevation", "Concealment"]
    vals = [scores.get(k, 0) for k in DIM_WEIGHTS]
    vals.append(vals[0]); labels = labels + [labels[0]]
    fig = go.Figure(go.Scatterpolar(
        r=vals, theta=labels, fill="toself",
        fillcolor="rgba(80,120,220,0.25)",
        line=dict(color="#6688ee", width=2)))
    fig.update_layout(
        polar=dict(bgcolor="#0e0e24",
                   radialaxis=dict(range=[0, 100], gridcolor="#222244",
                                   tickfont=dict(size=9, color="#888")),
                   angularaxis=dict(gridcolor="#222244",
                                    tickfont=dict(size=10, color="#aab"))),
        height=340, margin=dict(t=40, b=30, l=60, r=60),
        paper_bgcolor="#0b0b1e", showlegend=False, font=dict(color="#c0c0e0"))
    return fig


# ---------------------------------------------------------------------------
# Folium map builder
# ---------------------------------------------------------------------------

def _night_map(lat, lon, bortle, scores):
    import folium
    m = folium.Map(location=[lat, lon], zoom_start=11,
                   tiles="CartoDB dark_matter", attr="CartoDB")
    info = BORTLE_SCALE[bortle]
    comp = _composite(scores)
    popup = (f'<div style="font-family:monospace;font-size:12px;min-width:200px;'
             f'background:#111;color:#ddd;padding:8px;border-radius:6px;">'
             f'<b style="color:#7799ff;">Night Ops Assessment</b><hr style="border-color:#333;margin:4px 0;">'
             f'Bortle: <b style="color:#ffcc44;">{bortle}</b> - {info["label"]}<br>'
             f'Darkness: <b style="color:#44ddff;">{comp}/100</b><hr style="border-color:#333;margin:4px 0;">'
             f'Light: {scores.get("light_pollution",0)}/100 | Urban: {scores.get("urban_proximity",0)}/100<br>'
             f'Sky: {scores.get("cloud_cover",0)}/100 | Moon: {scores.get("moon_phase",0)}/100<br>'
             f'Elev: {scores.get("elevation",0)}/100 | Cover: {scores.get("concealment",0)}/100</div>')
    folium.Marker([lat, lon], popup=folium.Popup(popup, max_width=280),
                  icon=folium.Icon(color="darkblue", icon="star", prefix="fa"),
                  tooltip=f"Bortle {bortle} | Darkness {comp}/100").add_to(m)
    folium.Circle([lat, lon], radius=5000, color="#4466aa",
                  fill=True, fill_opacity=0.08,
                  popup="5 km light-pollution radius").add_to(m)
    folium.Circle([lat, lon], radius=3000, color="#226644",
                  fill=True, fill_opacity=0.06, dash_array="5,5",
                  popup="3 km concealment radius").add_to(m)
    return m._repr_html_()


# ---------------------------------------------------------------------------
# Night-time clear-sky window estimator
# ---------------------------------------------------------------------------

def _night_windows(cloud_vals, cloud_hrs):
    """Find clear-sky windows during night hours (20:00-05:00)."""
    if not cloud_hrs or not cloud_vals:
        return []
    windows, cur = [], None
    for h_str, cov in zip(cloud_hrs, cloud_vals):
        try:
            h = datetime.fromisoformat(h_str).hour
        except (ValueError, TypeError):
            continue
        if (h >= 20 or h <= 5) and cov < 40:
            if cur is None:
                cur = {"start": h_str, "end": h_str, "c": [cov]}
            else:
                cur["end"] = h_str; cur["c"].append(cov)
        else:
            if cur and len(cur["c"]) >= 2:
                windows.append({"start": cur["start"], "end": cur["end"],
                                "duration_h": len(cur["c"]),
                                "avg_cloud": round(sum(cur["c"]) / len(cur["c"]), 1)})
            cur = None
    if cur and len(cur["c"]) >= 2:
        windows.append({"start": cur["start"], "end": cur["end"],
                        "duration_h": len(cur["c"]),
                        "avg_cloud": round(sum(cur["c"]) / len(cur["c"]), 1)})
    return windows[:10]


# ---------------------------------------------------------------------------
# Operations suitability assessor
# ---------------------------------------------------------------------------

def _assess_ops(bortle, comp, star_vis, moon, conceal, elev):
    cs = _score_conceal(conceal["features"])
    moon_ok = moon["illumination"] < 30
    assessments = []

    # Stargazing / Astrophotography
    if bortle <= 3 and star_vis["milky_way"]:   suit, col = "Excellent", "#44cc88"
    elif bortle <= 5:                            suit, col = "Good", "#88bb44"
    elif bortle <= 7:                            suit, col = "Fair", "#ffaa33"
    else:                                        suit, col = "Poor", "#ee4444"
    assessments.append({"activity": "Stargazing / Astrophotography", "icon": "\u2B50",
        "suitability": suit, "color": col,
        "note": f"Bortle {bortle}, NELM {star_vis['nelm']} mag, "
                f"{'Milky Way visible' if star_vis['milky_way'] else 'Milky Way not visible'}"})

    # Covert Night Movement
    if comp >= 65 and cs >= 50 and moon_ok:      suit, col = "Excellent", "#44cc88"
    elif comp >= 45 and cs >= 30:                 suit, col = "Good", "#88bb44"
    elif comp >= 30:                              suit, col = "Fair", "#ffaa33"
    else:                                         suit, col = "Poor", "#ee4444"
    assessments.append({"activity": "Covert Night Movement", "icon": "\U0001F977",
        "suitability": suit, "color": col,
        "note": f"Darkness {comp}/100, concealment {cs}/100, moon {moon['illumination']}%"})

    # Night Navigation Training
    if 30 <= comp <= 70 and moon["illumination"] >= 20: suit, col = "Good", "#88bb44"
    elif comp > 70:                                      suit, col = "Fair (very dark)", "#ffaa33"
    elif comp < 30:                                      suit, col = "Easy (bright)", "#ffaa33"
    else:                                                suit, col = "Fair", "#ffaa33"
    assessments.append({"activity": "Night Navigation Training", "icon": "\U0001F9ED",
        "suitability": suit, "color": col,
        "note": f"Darkness {comp}/100, moon {moon['illumination']}% illuminated"})

    # Drone / UAV Night Ops
    em = elev["elevation_m"]
    if comp >= 50 and em < 2000:  suit, col = "Good", "#88bb44"
    elif comp >= 30:              suit, col = "Fair", "#ffaa33"
    else:                         suit, col = "Poor", "#ee4444"
    assessments.append({"activity": "Drone / UAV Night Operations", "icon": "\U0001F681",
        "suitability": suit, "color": col,
        "note": f"Elevation {em}m, darkness {comp}/100"})

    # Nocturnal Wildlife Observation
    if comp >= 55 and cs >= 40:  suit, col = "Excellent", "#44cc88"
    elif comp >= 35:             suit, col = "Good", "#88bb44"
    else:                        suit, col = "Fair", "#ffaa33"
    assessments.append({"activity": "Nocturnal Wildlife Observation", "icon": "\U0001F989",
        "suitability": suit, "color": col,
        "note": f"Concealment {cs}/100, darkness {comp}/100"})

    # Dark Sky Preservation
    if bortle <= 2:    suit, col = "Pristine", "#44cc88"
    elif bortle <= 4:  suit, col = "Good", "#88bb44"
    elif bortle <= 6:  suit, col = "Moderate", "#ffaa33"
    else:              suit, col = "Threatened", "#ee4444"
    assessments.append({"activity": "Dark Sky Preservation Status", "icon": "\U0001F30C",
        "suitability": suit, "color": col,
        "note": f"Bortle {bortle} - {BORTLE_SCALE[bortle]['desc']}"})

    return assessments


# ---------------------------------------------------------------------------
# Main render function -- single entry point
# ---------------------------------------------------------------------------

def render_night_ops_tab():
    """Render the Night Operations & Darkness Assessment tab."""
    st.markdown("## \U0001F319 Night Operations & Darkness Assessment")
    st.caption("Night-sky quality, concealment, visibility & darkness analysis")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f", key="nops_lat")
    lon = c2.number_input("Longitude", value=12.5, format="%.4f", key="nops_lon")

    if not st.button("\U0001F319 Assess Night Conditions", key="nops_btn"):
        st.info("Enter coordinates and click the button to analyse night conditions.")
        return

    # -- Fetch all data --
    with st.spinner("Scanning darkness dimensions ..."):
        light_d = _fetch_light_pollution(lat, lon)
        urban_d = _fetch_urban_proximity(lat, lon)
        cloud_d = _fetch_cloud_cover(lat, lon)
        moon_d = _compute_moon_phase()
        elev_d = _fetch_elevation(lat, lon)
        conceal_d = _fetch_natural_concealment(lat, lon)

    # -- Compute scores --
    scores = {
        "light_pollution": _score_light(light_d["count"]),
        "urban_proximity": _score_urban(urban_d["distance_km"]),
        "cloud_cover": _score_cloud(cloud_d["avg"]),
        "moon_phase": _score_moon(moon_d["illumination"]),
        "elevation": _score_elev(elev_d["elevation_m"]),
        "concealment": _score_conceal(conceal_d["features"]),
    }
    bortle = _estimate_bortle(scores["light_pollution"],
                              scores["urban_proximity"], scores["elevation"])
    comp = _composite(scores)
    sv = _star_visibility(bortle, cloud_d["avg"], moon_d["illumination"])

    # -----------------------------------------------------------------------
    # UI LAYOUT
    # -----------------------------------------------------------------------

    # -- Top metrics --
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Darkness Score", f"{comp}/100",
              delta="Dark" if comp >= 60 else "Bright",
              delta_color="normal" if comp >= 60 else "inverse")
    m2.metric("Bortle Class", str(bortle), delta=BORTLE_SCALE[bortle]["label"])
    m3.metric(f"Moon {moon_d['icon']}", moon_d["phase_name"],
              delta=f"{moon_d['illumination']}% illuminated")
    m4.metric("Star Visibility", sv["rating"], delta=f"NELM {sv['nelm']} mag")

    st.divider()

    # -- Bortle gauge + Moon phase card --
    col_g, col_m = st.columns([3, 2])
    with col_g:
        st.plotly_chart(_bortle_gauge(bortle, key="nigops_pchart1"), use_container_width=True,
                        key="nops_bortle_gauge")
    with col_m:
        moon_advice = ("Excellent for dark-sky ops" if moon_d["illumination"] < 15
                       else "Good darkness" if moon_d["illumination"] < 40
                       else "Moderate moonlight" if moon_d["illumination"] < 65
                       else "Significant moonlight -- plan accordingly")
        adv_col = "44cc88" if moon_d["illumination"] < 30 else "ff8844"
        st.markdown(
            f'<div style="background:#0e0e24;border:1px solid #333366;border-radius:10px;'
            f'padding:20px;text-align:center;">'
            f'<div style="font-size:72px;line-height:1;">{moon_d["icon"]}</div>'
            f'<div style="color:#c0c0e0;font-size:18px;margin-top:8px;font-weight:bold;">'
            f'{moon_d["phase_name"]}</div>'
            f'<div style="color:#888;font-size:13px;margin-top:4px;">'
            f'Age: {moon_d["age_days"]} days | Illumination: {moon_d["illumination"]}%</div>'
            f'<div style="color:#{adv_col};font-size:13px;margin-top:6px;">'
            f'{moon_advice}</div></div>', unsafe_allow_html=True)

    st.divider()

    # -- Cloud forecast --
    if cloud_d["ok"] and cloud_d["hours"]:
        st.plotly_chart(_cloud_chart(cloud_d["hours"], cloud_d["values"], key="nigops_pchart2"),
                        use_container_width=True, key="nops_cloud_chart")
        windows = _night_windows(cloud_d["values"], cloud_d["hours"])
        if windows:
            st.markdown("#### Clear Night-Sky Windows (< 40% cloud, 20:00-05:00)")
            for i, w in enumerate(windows):
                st.markdown(f"- **Window {i+1}**: {w['start'].replace('T',' ')} to "
                            f"{w['end'].replace('T',' ')} ({w['duration_h']}h, "
                            f"avg cloud {w['avg_cloud']}%)")
        else:
            st.warning("No clear nighttime windows found in the 7-day forecast.")
    else:
        st.warning("Cloud cover data unavailable.")

    st.divider()

    # -- Dimension scores + radar --
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### Dimension Scores")
        dim_info = [("Light Pollution (darkness)", "light_pollution"),
                    ("Urban Distance", "urban_proximity"),
                    ("Clear Sky", "cloud_cover"),
                    ("Moon Darkness", "moon_phase"),
                    ("Elevation Advantage", "elevation"),
                    ("Natural Concealment", "concealment")]
        for label, key in dim_info:
            val = scores[key]
            bc = "#44cc88" if val >= 60 else "#ffaa33" if val >= 35 else "#ee4444"
            st.markdown(
                f'<div style="margin-bottom:8px;">'
                f'<span style="color:#c0c0e0;font-size:13px;">{label}</span>'
                f'<span style="color:{bc};font-weight:bold;float:right;">{val}/100</span>'
                f'<div style="background:#1a1a3a;border-radius:4px;height:10px;margin-top:3px;">'
                f'<div style="background:{bc};width:{val}%;height:10px;border-radius:4px;">'
                f'</div></div></div>', unsafe_allow_html=True)
    with col_b:
        st.plotly_chart(_radar_chart(scores, key="nigops_pchart3"), use_container_width=True, key="nops_radar")

    st.divider()

    # -- Raw data expander --
    with st.expander("Raw Data Details", expanded=False):
        r1, r2, r3 = st.columns(3)
        r1.markdown("**Light Pollution**"); r1.write(f"Lit features: {light_d['count']}")
        r2.markdown("**Urban Proximity**"); r2.write(f"Nearest: {urban_d['nearest']} ({urban_d['distance_km']} km)")
        r3.markdown("**Elevation**"); r3.write(f"{elev_d['elevation_m']} m")
        r4, r5 = st.columns(2)
        r4.markdown("**Concealment**"); r4.write(f"Forest/scrub features: {conceal_d['features']}")
        r5.markdown("**Cloud Cover**"); r5.write(f"7-day average: {cloud_d['avg']}%")

    st.divider()

    # -- Star visibility --
    st.markdown("#### Star Visibility Prediction")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Limiting Magnitude", f"{sv['nelm']} mag")
    s2.metric("Approx. Visible Stars", f"{sv['visible_stars']:,}")
    s3.metric("Milky Way", "Visible" if sv["milky_way"] else "Not visible")
    s4.metric("Deep-Sky Objects", "Possible" if sv["deep_sky"] else "Unlikely")

    st.divider()

    # -- Night ops suitability --
    st.markdown("#### Night Operations Suitability")
    for ops in _assess_ops(bortle, comp, sv, moon_d, conceal_d, elev_d):
        st.markdown(
            f'<div style="background:#0e0e24;border-left:4px solid {ops["color"]};'
            f'padding:10px 14px;margin-bottom:8px;border-radius:0 6px 6px 0;">'
            f'<span style="font-size:16px;">{ops["icon"]}</span>'
            f'<b style="color:#c0c0e0;margin-left:6px;">{ops["activity"]}</b>'
            f'<span style="color:{ops["color"]};float:right;font-weight:bold;">'
            f'{ops["suitability"]}</span>'
            f'<div style="color:#888;font-size:12px;margin-top:4px;">{ops["note"]}</div>'
            f'</div>', unsafe_allow_html=True)

    st.divider()

    # -- Folium dark-themed map --
    st.markdown("#### Assessment Map")
    st.components.v1.html(_night_map(lat, lon, bortle, scores), height=460, scrolling=False)

    # -- Bortle scale reference --
    with st.expander("Bortle Scale Reference", expanded=False):
        for b in range(1, 10):
            info = BORTLE_SCALE[b]
            tag = " << YOUR LOCATION" if b == bortle else ""
            st.markdown(
                f'<div style="background:{info["color"]};color:#eee;padding:6px 12px;'
                f'margin-bottom:2px;border-radius:4px;font-size:13px;">'
                f'<b>Bortle {b}</b> - {info["label"]}{tag}'
                f'<span style="float:right;font-size:11px;color:#ccc;">'
                f'{info["desc"]}</span></div>', unsafe_allow_html=True)
