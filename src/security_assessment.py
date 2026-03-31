# -*- coding: utf-8 -*-
"""
Physical Security & Safety Assessment module for TerraScout AI.
Analyzes how secure and safe an area is based on infrastructure, visibility,
access control, emergency services, lighting, and community density.
Uses free APIs: Overpass (OpenStreetMap) and Open Topo Data (no keys required).
"""

import math
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
_BG, _SURFACE, _CARD = "#1a1a2e", "#16213e", "#0f3460"
_BORDER, _TEXT, _TEXT_SEC, _ACCENT = "#1a4080", "#e8ecf4", "#8b97b0", "#06b6d4"
_CLR_HIGH, _CLR_MEDIUM, _CLR_LOW, _CLR_CRITICAL = "#22c55e", "#f59e0b", "#f97316", "#ef4444"

# =============================================================================
# DIMENSION CONFIGURATION
# =============================================================================
DIMENSION_META = {
    "Surveillance Infrastructure": {"color": "#8b5cf6", "weight": 0.20},
    "Lighting Coverage":           {"color": "#fbbf24", "weight": 0.18},
    "Emergency Services":          {"color": "#ef4444", "weight": 0.20},
    "Access Control":              {"color": "#3b82f6", "weight": 0.15},
    "Visibility & Sightlines":     {"color": "#06b6d4", "weight": 0.12},
    "Community Density":           {"color": "#22c55e", "weight": 0.15},
}
DIMENSION_ORDER = list(DIMENSION_META.keys())

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# =============================================================================
# HELPERS
# =============================================================================
def _clamp(v, lo=0.0, hi=10.0):
    return max(lo, min(hi, float(v)))

def _security_level(score):
    if score >= 8.0:   return "HIGH", _CLR_HIGH
    if score >= 5.0:   return "MEDIUM", _CLR_MEDIUM
    if score >= 2.0:   return "LOW", _CLR_LOW
    return "CRITICAL", _CLR_CRITICAL

def _delta_label(score):
    if score >= 8.0:   return "Excellent"
    if score >= 6.0:   return "Good"
    if score >= 4.0:   return "Moderate"
    if score >= 2.0:   return "Poor"
    return "Critical"

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

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

def _safe_mean(vals):
    c = [v for v in (vals or []) if v is not None]
    return sum(c) / len(c) if c else 0.0

def _dim_card(name, score, detail, color):
    sc = _security_level(score)[1]
    return (
        f'<div style="background:{_CARD};border-radius:10px;padding:14px 12px;'
        f'border:1px solid {color}44;margin-bottom:8px;min-height:130px;">'
        f'<div style="font-size:12px;color:{color};font-weight:600;'
        f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">'
        f'{escape(name)}</div>'
        f'<div style="font-size:28px;font-weight:800;color:{sc};">{score:.1f}</div>'
        f'<div style="font-size:11px;color:{_TEXT_SEC};margin-top:4px;'
        f'line-height:1.35;">{escape(detail[:120])}</div></div>'
    )

def _security_badge(score):
    label, color = _security_level(score)
    return (
        f'<div style="display:inline-block;background:{color}22;border:2px solid {color};'
        f'border-radius:12px;padding:12px 28px;text-align:center;">'
        f'<div style="font-size:13px;color:{color};font-weight:600;'
        f'letter-spacing:1px;">SECURITY LEVEL</div>'
        f'<div style="font-size:36px;font-weight:900;color:{color};'
        f'margin:4px 0;">{label}</div>'
        f'<div style="font-size:22px;font-weight:700;color:{_TEXT};">'
        f'{score:.1f} / 10</div></div>'
    )

# =============================================================================
# DATA FETCHING  (all @st.cache_data, all timeout=10, all try/except)
# =============================================================================
@st.cache_data(ttl=900)
def _fetch_surveillance(lat, lon):
    """CCTV cameras, police stations, fire stations, military in 5 km."""
    query = f"""[out:json][timeout:25];(
      node["man_made"="surveillance"](around:5000,{lat},{lon});
      node["amenity"="police"](around:5000,{lat},{lon});
      way["amenity"="police"](around:5000,{lat},{lon});
      node["amenity"="fire_station"](around:5000,{lat},{lon});
      way["amenity"="fire_station"](around:5000,{lat},{lon});
      node["military"](around:5000,{lat},{lon});
      way["military"](around:5000,{lat},{lon});
    );out center body;"""
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Surveillance fetch error: %s", exc)
        return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_lighting(lat, lon):
    """Street lamps and lit roads in 2 km."""
    query = f"""[out:json][timeout:25];(
      node["highway"="street_lamp"](around:2000,{lat},{lon});
      way["lit"="yes"](around:2000,{lat},{lon});
    );out center body;"""
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Lighting fetch error: %s", exc)
        return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_emergency(lat, lon):
    """Hospitals, clinics, pharmacies, defibrillators in 5 km."""
    query = f"""[out:json][timeout:25];(
      node["amenity"="hospital"](around:5000,{lat},{lon});
      way["amenity"="hospital"](around:5000,{lat},{lon});
      node["amenity"="clinic"](around:5000,{lat},{lon});
      way["amenity"="clinic"](around:5000,{lat},{lon});
      node["amenity"="pharmacy"](around:5000,{lat},{lon});
      node["emergency"="defibrillator"](around:5000,{lat},{lon});
    );out center body;"""
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Emergency services fetch error: %s", exc)
        return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_access_control(lat, lon):
    """Barriers, bollards, gated areas, fences in 2 km."""
    query = f"""[out:json][timeout:25];(
      node["barrier"](around:2000,{lat},{lon});
      way["barrier"](around:2000,{lat},{lon});
      way["access"="private"](around:2000,{lat},{lon});
    );out center body;"""
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Access control fetch error: %s", exc)
        return {"elements": []}

@st.cache_data(ttl=900)
def _fetch_elevation_grid(lat, lon):
    """Fetch 5x5 elevation grid from Open Topo Data for terrain roughness."""
    try:
        pts = [f"{lat + (i - 2) * 0.004:.5f},{lon + (j - 2) * 0.004:.5f}"
               for i in range(5) for j in range(5)]
        resp = requests.get("https://api.opentopodata.org/v1/srtm30m",
                            params={"locations": "|".join(pts)}, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        return {"elevations": [float(r.get("elevation") or 0) for r in results]}
    except Exception as exc:
        logger.warning("Elevation grid fetch error: %s", exc)
        return {"elevations": []}

@st.cache_data(ttl=900)
def _fetch_community(lat, lon):
    """Residential buildings, schools, community centres in 3 km."""
    query = f"""[out:json][timeout:25];(
      way["building"="residential"](around:3000,{lat},{lon});
      node["building"="residential"](around:3000,{lat},{lon});
      node["amenity"="school"](around:3000,{lat},{lon});
      way["amenity"="school"](around:3000,{lat},{lon});
      node["amenity"="community_centre"](around:3000,{lat},{lon});
      way["amenity"="community_centre"](around:3000,{lat},{lon});
    );out center body;"""
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Community density fetch error: %s", exc)
        return {"elements": []}

# =============================================================================
# SCORING HELPERS
# =============================================================================
def _count_by_tag(elements, tag_key, tag_value):
    return sum(1 for el in (elements if isinstance(elements, list) else [])
               if isinstance(el.get("tags"), dict) and el["tags"].get(tag_key) == tag_value)

def _count_by_tag_key(elements, tag_key):
    return sum(1 for el in (elements if isinstance(elements, list) else [])
               if isinstance(el.get("tags"), dict) and tag_key in el["tags"])

def _categorize_elements(elements, tag_key, tag_values):
    return [el for el in (elements if isinstance(elements, list) else [])
            if isinstance(el.get("tags"), dict) and el["tags"].get(tag_key) in tag_values]

# =============================================================================
# SCORING ENGINE
# =============================================================================
@st.cache_data(ttl=900)
def _compute_security_scores(lat, lon):
    """Compute all 6 security dimension scores (each 0-10)."""
    surv_data  = _fetch_surveillance(lat, lon)
    light_data = _fetch_lighting(lat, lon)
    emerg_data = _fetch_emergency(lat, lon)
    access_data = _fetch_access_control(lat, lon)
    elev_data  = _fetch_elevation_grid(lat, lon)
    comm_data  = _fetch_community(lat, lon)

    scores, details, raw_counts = {}, {}, {}

    # --- DIM 1: Surveillance Infrastructure ---
    s_el = surv_data.get("elements", [])
    s_el = s_el if isinstance(s_el, list) else []
    n_cctv = _count_by_tag(s_el, "man_made", "surveillance")
    n_police = _count_by_tag(s_el, "amenity", "police")
    n_fire = _count_by_tag(s_el, "amenity", "fire_station")
    n_military = _count_by_tag_key(s_el, "military")
    raw_counts["surveillance"] = {"cctv": n_cctv, "police": n_police,
                                   "fire_station": n_fire, "military": n_military}
    total_surv = n_cctv + n_police * 5 + n_fire * 3 + n_military * 4
    if   total_surv >= 50: ss = 9.5
    elif total_surv >= 30: ss = 8.0
    elif total_surv >= 15: ss = 6.5
    elif total_surv >= 5:  ss = 5.0
    elif total_surv >= 1:  ss = 3.0
    else:                  ss = 1.0
    nearest_police = _nearest_dist(lat, lon, _categorize_elements(s_el, "amenity", {"police"}))
    if nearest_police is not None and nearest_police < 1.0:
        ss = _clamp(ss + 1.0)
    elif nearest_police is not None and nearest_police > 4.0:
        ss = _clamp(ss - 0.5)
    sd = f"{n_cctv} cameras, {n_police} police, {n_fire} fire stations, {n_military} military in 5 km"
    if nearest_police is not None:
        sd += f"; nearest police {nearest_police:.1f} km"
    scores["Surveillance Infrastructure"] = round(_clamp(ss), 1)
    details["Surveillance Infrastructure"] = sd

    # --- DIM 2: Lighting Coverage ---
    l_el = light_data.get("elements", [])
    l_el = l_el if isinstance(l_el, list) else []
    n_lamps = _count_by_tag(l_el, "highway", "street_lamp")
    n_lit = sum(1 for e in l_el if e.get("tags", {}).get("lit") == "yes")
    raw_counts["lighting"] = {"street_lamps": n_lamps, "lit_roads": n_lit}
    density = n_lamps / 12.57  # lamps per km2 in 2 km radius
    if   density >= 40: ls = 9.5
    elif density >= 20: ls = 8.0
    elif density >= 10: ls = 6.5
    elif density >= 4:  ls = 5.0
    elif density >= 1:  ls = 3.5
    else:               ls = 1.5
    if n_lit >= 20:   ls = _clamp(ls + 1.0)
    elif n_lit >= 5:  ls = _clamp(ls + 0.5)
    scores["Lighting Coverage"] = round(_clamp(ls), 1)
    details["Lighting Coverage"] = f"{n_lamps} street lamps ({density:.1f}/km2), {n_lit} lit roads in 2 km"

    # --- DIM 3: Emergency Services ---
    e_el = emerg_data.get("elements", [])
    e_el = e_el if isinstance(e_el, list) else []
    n_hosp = _count_by_tag(e_el, "amenity", "hospital")
    n_clin = _count_by_tag(e_el, "amenity", "clinic")
    n_phar = _count_by_tag(e_el, "amenity", "pharmacy")
    n_aed  = _count_by_tag(e_el, "emergency", "defibrillator")
    raw_counts["emergency"] = {"hospitals": n_hosp, "clinics": n_clin,
                                "pharmacies": n_phar, "defibrillators": n_aed}
    total_em = n_hosp * 10 + n_clin * 5 + n_phar * 2 + n_aed * 3
    if   total_em >= 60: es = 9.5
    elif total_em >= 30: es = 8.0
    elif total_em >= 15: es = 6.5
    elif total_em >= 5:  es = 4.5
    elif total_em >= 1:  es = 3.0
    else:                es = 1.0
    nearest_hosp = _nearest_dist(lat, lon, _categorize_elements(e_el, "amenity", {"hospital"}))
    if nearest_hosp is not None and nearest_hosp < 1.0:
        es = _clamp(es + 1.0)
    elif nearest_hosp is not None and nearest_hosp > 4.0:
        es = _clamp(es - 1.0)
    ed = f"{n_hosp} hospitals, {n_clin} clinics, {n_phar} pharmacies, {n_aed} AEDs in 5 km"
    if nearest_hosp is not None:
        ed += f"; nearest hospital {nearest_hosp:.1f} km"
    scores["Emergency Services"] = round(_clamp(es), 1)
    details["Emergency Services"] = ed

    # --- DIM 4: Access Control ---
    a_el = access_data.get("elements", [])
    a_el = a_el if isinstance(a_el, list) else []
    n_barriers = _count_by_tag_key(a_el, "barrier")
    n_private = sum(1 for e in a_el if e.get("tags", {}).get("access") == "private")
    raw_counts["access"] = {"barriers": n_barriers, "private_areas": n_private}
    total_ac = n_barriers + n_private * 2
    if   total_ac >= 80: acs = 9.0
    elif total_ac >= 40: acs = 7.5
    elif total_ac >= 20: acs = 6.0
    elif total_ac >= 8:  acs = 4.5
    elif total_ac >= 2:  acs = 3.0
    else:                acs = 1.5
    scores["Access Control"] = round(_clamp(acs), 1)
    details["Access Control"] = f"{n_barriers} barriers/bollards, {n_private} private-access areas in 2 km"

    # --- DIM 5: Visibility & Sightlines ---
    elevations = elev_data.get("elevations", [])
    if len(elevations) >= 9:
        diffs = [abs(elevations[i + 1] - elevations[i]) for i in range(len(elevations) - 1)]
        mean_diff = _safe_mean(diffs)
        max_diff = max(diffs) if diffs else 0.0
        if   mean_diff < 2:  vs, vd = 9.0, f"Very flat (avg {mean_diff:.1f}m), excellent visibility"
        elif mean_diff < 5:  vs, vd = 7.5, f"Gentle terrain ({mean_diff:.1f}m avg), good sightlines"
        elif mean_diff < 15: vs, vd = 5.5, f"Moderate variation ({mean_diff:.1f}m), partial obstruction"
        elif mean_diff < 30: vs, vd = 3.5, f"Hilly ({mean_diff:.1f}m avg), limited visibility"
        else:                vs, vd = 2.0, f"Rugged ({mean_diff:.1f}m avg), severely obstructed"
        if max_diff > 50:
            vs = _clamp(vs - 1.0); vd += f"; steep features ({max_diff:.0f}m max)"
    else:
        vs, vd = 5.0, "Elevation data limited; approximate visibility estimate"
    scores["Visibility & Sightlines"] = round(_clamp(vs), 1)
    details["Visibility & Sightlines"] = vd

    # --- DIM 6: Community Density ---
    c_el = comm_data.get("elements", [])
    c_el = c_el if isinstance(c_el, list) else []
    n_resid = sum(1 for e in c_el if e.get("tags", {}).get("building") == "residential")
    n_schools = _count_by_tag(c_el, "amenity", "school")
    n_comm = _count_by_tag(c_el, "amenity", "community_centre")
    raw_counts["community"] = {"residential": n_resid, "schools": n_schools,
                                "community_centres": n_comm}
    craw = n_resid + n_schools * 10 + n_comm * 8
    if   craw >= 200: cs = 9.5
    elif craw >= 100: cs = 8.0
    elif craw >= 50:  cs = 6.5
    elif craw >= 20:  cs = 5.0
    elif craw >= 5:   cs = 3.5
    else:             cs = 1.5
    scores["Community Density"] = round(_clamp(cs), 1)
    details["Community Density"] = (f"{n_resid} residential bldgs, {n_schools} schools, "
                                     f"{n_comm} community centres in 3 km")

    # --- Overall weighted index ---
    overall = round(_clamp(sum(scores[d] * DIMENSION_META[d]["weight"]
                                for d in DIMENSION_ORDER)), 1)
    return {"scores": scores, "details": details, "overall": overall,
            "raw_counts": raw_counts,
            "raw_data": {"surveillance": surv_data, "lighting": light_data,
                         "emergency": emerg_data, "access": access_data,
                         "elevation": elev_data, "community": comm_data}}

# =============================================================================
# RADAR CHART
# =============================================================================
def _build_radar_chart(scores):
    cats = list(DIMENSION_ORDER)
    vals = [scores.get(d, 0) for d in cats]
    cats_c, vals_c = cats + [cats[0]], vals + [vals[0]]
    colors = [DIMENSION_META[d]["color"] for d in cats]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals_c, theta=cats_c, fill="toself",
        fillcolor="rgba(6,182,212,0.15)",
        line=dict(color=_ACCENT, width=2.5),
        marker=dict(size=8, color=colors + [colors[0]]),
        name="Security Score",
        hovertemplate="%{theta}: %{r:.1f}/10<extra></extra>"))
    fig.update_layout(
        polar=dict(bgcolor=_SURFACE,
                   radialaxis=dict(visible=True, range=[0, 10],
                                   tickfont=dict(size=10, color=_TEXT_SEC),
                                   gridcolor=_BORDER),
                   angularaxis=dict(tickfont=dict(size=11, color=_TEXT),
                                    gridcolor=_BORDER)),
        showlegend=False, paper_bgcolor=_BG, font=dict(color=_TEXT),
        margin=dict(l=60, r=60, t=40, b=40), height=420)
    return fig

# =============================================================================
# FOLIUM MAP
# =============================================================================
def _build_security_map(lat, lon, raw_data):
    try:
        import folium
    except ImportError:
        return None

    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="CartoDB dark_matter")
    folium.Marker([lat, lon], popup="Analysis Center",
                  icon=folium.Icon(color="white", icon="crosshairs", prefix="fa")).add_to(m)

    for radius, color, label in [(2000, "#fbbf24", "2 km"),
                                  (3000, "#22c55e", "3 km"),
                                  (5000, "#8b5cf6", "5 km")]:
        folium.Circle([lat, lon], radius=radius, color=color, fill=False,
                      weight=1.5, opacity=0.5, dash_array="5,5",
                      tooltip=f"{label} radius").add_to(m)

    marker_cfg = {
        "surveillance":     ("purple",     "eye",                "fa", "CCTV Camera"),
        "police":           ("darkblue",   "shield",             "fa", "Police Station"),
        "fire_station":     ("red",        "fire-extinguisher",  "fa", "Fire Station"),
        "military":         ("darkred",    "star",               "fa", "Military"),
        "street_lamp":      ("orange",     "lightbulb",          "fa", "Street Lamp"),
        "hospital":         ("red",        "plus",               "fa", "Hospital"),
        "clinic":           ("pink",       "stethoscope",        "fa", "Clinic"),
        "pharmacy":         ("green",      "prescription-bottle","fa", "Pharmacy"),
        "defibrillator":    ("cadetblue",  "heartbeat",          "fa", "AED"),
        "barrier":          ("blue",       "lock",               "fa", "Barrier"),
        "school":           ("darkgreen",  "graduation-cap",     "fa", "School"),
        "community_centre": ("lightgreen", "users",              "fa", "Community Centre"),
    }

    def _detect_type(tags):
        if tags.get("man_made") == "surveillance":   return "surveillance"
        if tags.get("amenity") == "police":          return "police"
        if tags.get("amenity") == "fire_station":    return "fire_station"
        if tags.get("military"):                     return "military"
        if tags.get("highway") == "street_lamp":     return "street_lamp"
        if tags.get("amenity") == "hospital":        return "hospital"
        if tags.get("amenity") == "clinic":          return "clinic"
        if tags.get("amenity") == "pharmacy":        return "pharmacy"
        if tags.get("emergency") == "defibrillator": return "defibrillator"
        if tags.get("barrier"):                      return "barrier"
        if tags.get("amenity") == "school":          return "school"
        if tags.get("amenity") == "community_centre":return "community_centre"
        return None

    marker_count, max_markers, lamp_count = 0, 300, 0
    for src in ("surveillance", "lighting", "emergency", "access", "community"):
        for el in (raw_data.get(src, {}).get("elements") or []):
            if marker_count >= max_markers:
                break
            elat = el.get("lat") or (el.get("center") or {}).get("lat")
            elon = el.get("lon") or (el.get("center") or {}).get("lon")
            tags = el.get("tags", {})
            if elat is None or elon is None or not isinstance(tags, dict):
                continue
            ft = _detect_type(tags)
            if ft is None:
                continue
            if ft == "street_lamp":
                lamp_count += 1
                if lamp_count > 120:
                    continue
            cfg = marker_cfg.get(ft, ("gray", "info", "fa", ft))
            name = tags.get("name") or cfg[3]
            dist = _haversine(lat, lon, elat, elon)
            popup = (f"<b>{escape(name)}</b><br>Type: {ft.replace('_',' ').title()}"
                     f"<br>Distance: {dist:.2f} km")
            folium.Marker(
                [elat, elon], popup=folium.Popup(popup, max_width=250),
                icon=folium.Icon(color=cfg[0], icon=cfg[1], prefix=cfg[2])).add_to(m)
            marker_count += 1
    return m

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def render_security_assessment_tab():
    """Render the Physical Security & Safety Assessment tab."""
    st.markdown(
        f'<div style="background:linear-gradient(135deg,{_SURFACE},{_CARD});">'
        f'<h2 style="color:{_TEXT};margin:0;padding:18px 0 4px 0;">'
        f'&#128737; Physical Security Assessment</h2>'
        f'<p style="color:{_TEXT_SEC};font-size:14px;margin:0 0 14px 0;">'
        f'Area security analysis: surveillance, lighting, emergency services, '
        f'access control, terrain visibility &amp; community density</p></div>',
        unsafe_allow_html=True)

    # --- Inputs ---------------------------------------------------------------
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, format="%.4f",
                          min_value=-90.0, max_value=90.0, key="secass_lat")
    lon = c2.number_input("Longitude", value=12.4964, format="%.4f",
                          min_value=-180.0, max_value=180.0, key="secass_lon")

    pc, bc = st.columns([2, 1])
    preset = pc.selectbox("Quick location presets", key="secass_preset",
        options=["Custom", "Rome, Italy", "London, UK", "Paris, France",
                 "New York, USA", "Tokyo, Japan", "Berlin, Germany",
                 "Sydney, Australia", "Mumbai, India", "Dubai, UAE",
                 "Singapore", "Sao Paulo, Brazil", "Nairobi, Kenya"])
    presets = {
        "Rome, Italy": (41.9028, 12.4964), "London, UK": (51.5074, -0.1278),
        "Paris, France": (48.8566, 2.3522), "New York, USA": (40.7128, -74.006),
        "Tokyo, Japan": (35.6762, 139.6503), "Berlin, Germany": (52.52, 13.405),
        "Sydney, Australia": (-33.8688, 151.2093), "Mumbai, India": (19.076, 72.8777),
        "Dubai, UAE": (25.2048, 55.2708), "Singapore": (1.3521, 103.8198),
        "Sao Paulo, Brazil": (-23.5505, -46.6333), "Nairobi, Kenya": (-1.2921, 36.8219),
    }
    if preset != "Custom" and preset in presets:
        lat, lon = presets[preset]

    if not bc.button("Assess Security", key="secass_btn", use_container_width=True):
        st.info("Configure coordinates and click **Assess Security** to begin.")
        return

    # --- Analysis -------------------------------------------------------------
    with st.spinner("Analyzing security infrastructure across 6 dimensions..."):
        result = _compute_security_scores(lat, lon)
    if not result or not result.get("scores"):
        st.error("Analysis failed. Please try again later.")
        return

    scores = result["scores"]
    det = result["details"]
    overall = result["overall"]
    raw_counts = result["raw_counts"]
    raw_data = result["raw_data"]

    # --- Badge + Radar --------------------------------------------------------
    st.markdown("<br>", unsafe_allow_html=True)
    badge_col, radar_col = st.columns([1, 2])
    with badge_col:
        st.markdown(f'<div style="text-align:center;padding:20px 0;">'
                    f'{_security_badge(overall)}</div>', unsafe_allow_html=True)
        wt_html = (f'<div style="background:{_CARD};border-radius:10px;padding:14px;'
                   f'border:1px solid {_BORDER};margin-top:16px;">'
                   f'<div style="font-size:12px;color:{_TEXT_SEC};font-weight:600;'
                   f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;">'
                   f'Weight Distribution</div>')
        for dim in DIMENSION_ORDER:
            meta = DIMENSION_META[dim]
            sv = scores[dim]
            wt_html += (f'<div style="display:flex;justify-content:space-between;'
                        f'align-items:center;margin-bottom:6px;">'
                        f'<span style="font-size:11px;color:{meta["color"]};">{dim}</span>'
                        f'<span style="font-size:11px;color:{_security_level(sv)[1]};'
                        f'font-weight:700;">{sv:.1f} ({int(meta["weight"]*100)}%)</span></div>')
        st.markdown(wt_html + "</div>", unsafe_allow_html=True)
    with radar_col:
        st.plotly_chart(_build_radar_chart(scores, key="secass_pchart1"), use_container_width=True, key="secass_radar")

    # --- Dimension Cards ------------------------------------------------------
    st.markdown(f'<div style="font-size:16px;font-weight:700;color:{_TEXT};'
                f'margin:24px 0 12px 0;">Dimension Scores</div>', unsafe_allow_html=True)
    r1 = st.columns(3)
    r2 = st.columns(3)
    for idx, dim in enumerate(DIMENSION_ORDER):
        with (r1 + r2)[idx]:
            st.markdown(_dim_card(dim, scores[dim], det[dim],
                                  DIMENSION_META[dim]["color"]), unsafe_allow_html=True)
            dv = scores[dim] - 5.0
            st.metric(label=dim, value=f"{scores[dim]:.1f}",
                      delta=f"{_delta_label(scores[dim])} ({dv:+.1f})",
                      delta_color="normal" if dv >= 0 else "inverse",
                      label_visibility="collapsed")

    # --- Infrastructure Counts ------------------------------------------------
    st.markdown(f'<div style="font-size:16px;font-weight:700;color:{_TEXT};'
                f'margin:24px 0 12px 0;">Infrastructure Counts</div>', unsafe_allow_html=True)
    sc = raw_counts.get("surveillance", {})
    lc = raw_counts.get("lighting", {})
    ec = raw_counts.get("emergency", {})
    ac = raw_counts.get("access", {})
    cc = raw_counts.get("community", {})
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("CCTV Cameras", sc.get("cctv", 0), key="secass_m_cctv")
    m1.metric("Police Stations", sc.get("police", 0), key="secass_m_police")
    m2.metric("Fire Stations", sc.get("fire_station", 0), key="secass_m_fire")
    m2.metric("Street Lamps", lc.get("street_lamps", 0), key="secass_m_lamps")
    m3.metric("Hospitals", ec.get("hospitals", 0), key="secass_m_hosp")
    m3.metric("Pharmacies", ec.get("pharmacies", 0), key="secass_m_pharm")
    m4.metric("Schools", cc.get("schools", 0), key="secass_m_school")
    m4.metric("Barriers", ac.get("barriers", 0), key="secass_m_barrier")

    # --- Bar Chart ------------------------------------------------------------
    st.markdown(f'<div style="font-size:16px;font-weight:700;color:{_TEXT};'
                f'margin:24px 0 12px 0;">Score Comparison</div>', unsafe_allow_html=True)
    bar_fig = go.Figure()
    for dim in DIMENSION_ORDER:
        bar_fig.add_trace(go.Bar(
            x=[dim], y=[scores[dim]], marker_color=DIMENSION_META[dim]["color"],
            text=[f"{scores[dim]:.1f}"], textposition="outside",
            textfont=dict(color=_TEXT, size=12),
            hovertemplate=f"{dim}: %{{y:.1f}}/10<extra></extra>", showlegend=False))
    bar_fig.add_hline(y=overall, line_dash="dash", line_color=_ACCENT, line_width=2,
                      annotation_text=f"Overall: {overall:.1f}",
                      annotation_font_color=_ACCENT)
    bar_fig.update_layout(
        paper_bgcolor=_BG, plot_bgcolor=_SURFACE, font=dict(color=_TEXT),
        xaxis=dict(tickangle=-25, tickfont=dict(size=10, color=_TEXT_SEC), gridcolor=_BORDER),
        yaxis=dict(range=[0, 11], title="Score (0-10)", gridcolor=_BORDER,
                   tickfont=dict(size=10, color=_TEXT_SEC)),
        margin=dict(l=50, r=20, t=30, b=90), height=350)
    st.plotly_chart(bar_fig, use_container_width=True, key="secass_bar")

    # --- Folium Map -----------------------------------------------------------
    st.markdown(f'<div style="font-size:16px;font-weight:700;color:{_TEXT};'
                f'margin:24px 0 12px 0;">Security Infrastructure Map</div>',
                unsafe_allow_html=True)
    sec_map = _build_security_map(lat, lon, raw_data)
    if sec_map is not None:
        try:
            import streamlit.components.v1 as components
            components.html(sec_map._repr_html_(), height=520, scrolling=True)
        except Exception as exc:
            logger.warning("Map rendering error: %s", exc)
            st.warning("Map rendering failed. Ensure folium is installed.")
    else:
        st.warning("Map could not be generated. Ensure folium is installed.")

    # --- Legend ---------------------------------------------------------------
    legend_items = [
        ("#8b5cf6", "CCTV"), ("#1e3a8a", "Police"), ("#dc2626", "Fire Station"),
        ("#f97316", "Street Lamp"), ("#ef4444", "Hospital"), ("#ec4899", "Clinic"),
        ("#22c55e", "Pharmacy"), ("#0ea5e9", "AED"), ("#3b82f6", "Barrier"),
        ("#166534", "School"), ("#84cc16", "Community Centre"),
    ]
    legend_spans = "".join(f'<span style="color:{c};">&#9679; {n}</span>' for c, n in legend_items)
    st.markdown(
        f'<div style="background:{_CARD};border-radius:10px;padding:14px;'
        f'border:1px solid {_BORDER};margin-top:12px;">'
        f'<div style="font-size:12px;color:{_TEXT_SEC};font-weight:600;'
        f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:10px;">'
        f'Map Legend</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:12px;">{legend_spans}</div></div>',
        unsafe_allow_html=True)

    # --- Interpretation Guide -------------------------------------------------
    st.markdown(f'<div style="font-size:16px;font-weight:700;color:{_TEXT};'
                f'margin:24px 0 12px 0;">Interpretation Guide</div>', unsafe_allow_html=True)
    levels = [("HIGH", _CLR_HIGH, "8.0 - 10.0", "Well-secured area with strong infrastructure"),
              ("MEDIUM", _CLR_MEDIUM, "5.0 - 7.9", "Adequate security, some gaps identified"),
              ("LOW", _CLR_LOW, "2.0 - 4.9", "Limited security infrastructure present"),
              ("CRITICAL", _CLR_CRITICAL, "0.0 - 1.9", "Minimal or no security coverage detected")]
    level_cards = ""
    for lbl, clr, rng, desc in levels:
        level_cards += (
            f'<div style="text-align:center;padding:10px;border-radius:8px;'
            f'background:{clr}15;border:1px solid {clr}44;">'
            f'<div style="font-size:20px;font-weight:800;color:{clr};">{lbl}</div>'
            f'<div style="font-size:11px;color:{_TEXT_SEC};">{rng}</div>'
            f'<div style="font-size:10px;color:{_TEXT_SEC};margin-top:4px;">{desc}</div></div>')
    st.markdown(
        f'<div style="background:{_CARD};border-radius:10px;padding:16px;'
        f'border:1px solid {_BORDER};">'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">'
        f'{level_cards}</div>'
        f'<div style="margin-top:14px;padding:10px;background:{_SURFACE};'
        f'border-radius:8px;border:1px solid {_BORDER};">'
        f'<div style="font-size:11px;color:{_TEXT_SEC};font-weight:600;'
        f'margin-bottom:4px;">Methodology</div>'
        f'<div style="font-size:10px;color:{_TEXT_SEC};line-height:1.5;">'
        f'Scores are computed from OpenStreetMap infrastructure data (Overpass API) '
        f'and terrain elevation data (Open Topo Data). Each dimension is scored 0-10 '
        f'and weighted to produce the overall Security Index. Surveillance and Emergency '
        f'Services carry the highest weight (20% each). Results depend on OSM data '
        f'completeness for the area.</div></div></div>', unsafe_allow_html=True)

    # --- Raw Data Expander ----------------------------------------------------
    with st.expander("Raw API Response Data", expanded=False):
        st.json({"coordinates": {"latitude": lat, "longitude": lon},
                 "overall_security_index": overall,
                 "security_level": _security_level(overall)[0],
                 "dimension_scores": scores,
                 "dimension_details": det,
                 "infrastructure_counts": raw_counts})
