"""
Livability Score AI -- Comprehensive quality-of-life assessment combining
climate comfort, air quality, healthcare, education, commercial services,
green spaces, transport and safety dimensions.

Uses: Open-Meteo, Open-Meteo Air Quality, Overpass API.
Part of TerraScout AI.
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

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LIVABILITY_DIMENSIONS = {
    "climate": {"name": "Climate Comfort", "color": "#f59e0b", "weight": 0.15,
                "icon": "🌡️", "desc": "Temperature averages, extremes and precipitation balance"},
    "air_quality": {"name": "Air Quality", "color": "#06b6d4", "weight": 0.10,
                    "icon": "🌬️", "desc": "PM2.5, PM10 and European AQI levels"},
    "healthcare": {"name": "Healthcare Access", "color": "#ef4444", "weight": 0.15,
                   "icon": "🏥", "desc": "Hospitals, clinics, pharmacies and doctors within 5 km"},
    "education": {"name": "Education Access", "color": "#8b5cf6", "weight": 0.10,
                  "icon": "🎓", "desc": "Schools, universities and libraries within 5 km"},
    "commercial": {"name": "Commercial & Services", "color": "#ec4899", "weight": 0.10,
                   "icon": "🛒", "desc": "Shops, restaurants, banks and supermarkets within 3 km"},
    "green_spaces": {"name": "Green Spaces & Recreation", "color": "#22c55e", "weight": 0.15,
                     "icon": "🌳", "desc": "Parks, gardens, sports facilities and playgrounds within 3 km"},
    "transport": {"name": "Transport & Connectivity", "color": "#3b82f6", "weight": 0.15,
                  "icon": "🚌", "desc": "Bus stops, train stations, roads and cycling paths within 3 km"},
    "safety": {"name": "Safety & Security", "color": "#10b981", "weight": 0.10,
               "icon": "🛡️", "desc": "Police, fire stations, street lights and surveillance within 3 km"},
}

RATING_BANDS = [
    (9.0, 10.0, "EXCELLENT", "#10b981"),
    (7.0, 8.99, "VERY GOOD", "#22c55e"),
    (5.0, 6.99, "GOOD", "#f59e0b"),
    (3.0, 4.99, "FAIR", "#f97316"),
    (0.0, 2.99, "POOR", "#ef4444"),
]

REFERENCE_CITIES = {
    "London": {"lat": 51.5074, "lon": -0.1278, "score": 7.5},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503, "score": 8.0},
    "New York": {"lat": 40.7128, "lon": -74.0060, "score": 7.2},
    "Zurich": {"lat": 47.3769, "lon": 8.5417, "score": 8.5},
    "Lagos": {"lat": 6.5244, "lon": 3.3792, "score": 4.0},
}

# ---------------------------------------------------------------------------
# Data-fetching helpers
# ---------------------------------------------------------------------------


@st.cache_data(ttl=900)
def _fetch_climate_data(lat: float, lon: float) -> dict:
    """Fetch 30-day climate data from Open-Meteo."""
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,sunshine_duration"
           f"&past_days=30&timezone=auto")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Climate data fetch error: %s", exc)
        return {}


@st.cache_data(ttl=900)
def _fetch_air_quality(lat: float, lon: float) -> dict:
    """Fetch current air-quality data from Open-Meteo AQ API."""
    url = (f"https://air-quality-api.open-meteo.com/v1/air-quality?"
           f"latitude={lat}&longitude={lon}&current=pm10,pm2_5,european_aqi")
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Air quality fetch error: %s", exc)
        return {}


@st.cache_data(ttl=900)
def _fetch_overpass(lat: float, lon: float, query_body: str) -> list:
    """Run an Overpass query and return elements list."""
    query = f"[out:json][timeout:25];\n(\n{query_body}\n);\nout body;"
    try:
        resp = requests.post("https://overpass-api.de/api/interpreter",
                             data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json().get("elements", [])
    except Exception as exc:
        logger.warning("Overpass fetch error: %s", exc)
        return []


@st.cache_data(ttl=900)
def _fetch_healthcare(lat: float, lon: float, radius: int = 5000) -> list:
    """Hospitals, clinics, pharmacies and doctors."""
    body = "\n".join([
        f'node["amenity"="hospital"](around:{radius},{lat},{lon});',
        f'node["amenity"="clinic"](around:{radius},{lat},{lon});',
        f'node["amenity"="pharmacy"](around:{radius},{lat},{lon});',
        f'node["amenity"="doctors"](around:{radius},{lat},{lon});',
        f'way["amenity"="hospital"](around:{radius},{lat},{lon});',
    ])
    return _fetch_overpass(lat, lon, body)


@st.cache_data(ttl=900)
def _fetch_education(lat: float, lon: float, radius: int = 5000) -> list:
    """Schools, universities and libraries."""
    body = "\n".join([
        f'node["amenity"="school"](around:{radius},{lat},{lon});',
        f'way["amenity"="school"](around:{radius},{lat},{lon});',
        f'node["amenity"="university"](around:{radius},{lat},{lon});',
        f'way["amenity"="university"](around:{radius},{lat},{lon});',
        f'node["amenity"="library"](around:{radius},{lat},{lon});',
    ])
    return _fetch_overpass(lat, lon, body)


@st.cache_data(ttl=900)
def _fetch_commercial(lat: float, lon: float, radius: int = 3000) -> list:
    """Shops, restaurants, banks and supermarkets."""
    body = "\n".join([
        f'node["shop"="supermarket"](around:{radius},{lat},{lon});',
        f'node["amenity"="restaurant"](around:{radius},{lat},{lon});',
        f'node["amenity"="bank"](around:{radius},{lat},{lon});',
        f'node["shop"="convenience"](around:{radius},{lat},{lon});',
        f'node["amenity"="cafe"](around:{radius},{lat},{lon});',
    ])
    return _fetch_overpass(lat, lon, body)


@st.cache_data(ttl=900)
def _fetch_green_spaces(lat: float, lon: float, radius: int = 3000) -> list:
    """Parks, gardens, sports and playgrounds."""
    body = "\n".join([
        f'way["leisure"="park"](around:{radius},{lat},{lon});',
        f'node["leisure"="garden"](around:{radius},{lat},{lon});',
        f'way["leisure"="garden"](around:{radius},{lat},{lon});',
        f'node["leisure"="sports_centre"](around:{radius},{lat},{lon});',
        f'node["leisure"="playground"](around:{radius},{lat},{lon});',
        f'way["leisure"="pitch"](around:{radius},{lat},{lon});',
    ])
    return _fetch_overpass(lat, lon, body)


@st.cache_data(ttl=900)
def _fetch_transport(lat: float, lon: float, radius: int = 3000) -> list:
    """Bus stops, train stations, roads, cycling."""
    body = "\n".join([
        f'node["highway"="bus_stop"](around:{radius},{lat},{lon});',
        f'node["railway"="station"](around:{radius},{lat},{lon});',
        f'node["railway"="halt"](around:{radius},{lat},{lon});',
        f'node["amenity"="bicycle_rental"](around:{radius},{lat},{lon});',
        f'way["highway"="cycleway"](around:{radius},{lat},{lon});',
        f'node["public_transport"="stop_position"](around:{radius},{lat},{lon});',
    ])
    return _fetch_overpass(lat, lon, body)


@st.cache_data(ttl=900)
def _fetch_safety(lat: float, lon: float, radius: int = 3000) -> list:
    """Police, fire stations, street lights, surveillance."""
    body = "\n".join([
        f'node["amenity"="police"](around:{radius},{lat},{lon});',
        f'node["amenity"="fire_station"](around:{radius},{lat},{lon});',
        f'node["highway"="street_lamp"](around:{radius},{lat},{lon});',
        f'node["man_made"="surveillance"](around:{radius},{lat},{lon});',
    ])
    return _fetch_overpass(lat, lon, body)


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _clamp(val: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return round(min(hi, max(lo, val)), 1)


def _score_climate(data: dict) -> tuple[float, dict]:
    """Score climate comfort 0-10. Ideal: 15-25 C mean, moderate rain."""
    if not data or "daily" not in data:
        return 5.0, {"note": "No climate data available"}
    daily = data["daily"]
    temps_max = daily.get("temperature_2m_max", [])
    temps_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    if not temps_max:
        return 5.0, {"note": "Empty climate response"}

    avg_max = sum(t for t in temps_max if t is not None) / max(len(temps_max), 1)
    avg_min = sum(t for t in temps_min if t is not None) / max(len(temps_min), 1)
    avg_temp = (avg_max + avg_min) / 2.0
    total_precip = sum(p for p in precip if p is not None)
    daily_precip = total_precip / max(len(precip), 1)

    details = {"avg_temp_c": round(avg_temp, 1), "avg_max_c": round(avg_max, 1),
               "avg_min_c": round(avg_min, 1), "total_precip_mm": round(total_precip, 1),
               "daily_precip_mm": round(daily_precip, 1)}

    temp_score = max(0.0, 10.0 - 0.04 * (avg_temp - 20.0) ** 2)
    if daily_precip < 0.5:
        precip_score = 5.0
    elif daily_precip <= 5.0:
        precip_score = 8.0 + 2.0 * (1.0 - abs(daily_precip - 3.0) / 3.0)
    elif daily_precip <= 15.0:
        precip_score = max(2.0, 8.0 - 0.6 * (daily_precip - 5.0))
    else:
        precip_score = 1.0

    extreme_days = (sum(1 for t in temps_max if t and t > 38)
                    + sum(1 for t in temps_min if t and t < -10))
    extreme_penalty = min(3.0, extreme_days * 0.5)
    details["extreme_days"] = extreme_days
    score = 0.5 * temp_score + 0.3 * precip_score + 0.2 * (10.0 - extreme_penalty)
    return _clamp(score), details


def _score_air_quality(data: dict) -> tuple[float, dict]:
    """Score air quality 0-10 from European AQI."""
    if not data or "current" not in data:
        return 5.0, {"note": "No air quality data available"}
    current = data["current"]
    pm25 = current.get("pm2_5")
    pm10 = current.get("pm10")
    eaqi = current.get("european_aqi")
    details = {"pm2_5": pm25, "pm10": pm10, "european_aqi": eaqi}
    if eaqi is None:
        return 5.0, details
    # European AQI bands: 0-20 Good, 20-40 Fair, 40-60 Moderate, 60-80 Poor, 80+ Very Poor
    if eaqi <= 20:
        score = 9.0 + (20 - eaqi) / 20.0
    elif eaqi <= 40:
        score = 7.0 + 2.0 * (40 - eaqi) / 20.0
    elif eaqi <= 60:
        score = 5.0 + 2.0 * (60 - eaqi) / 20.0
    elif eaqi <= 80:
        score = 3.0 + 2.0 * (80 - eaqi) / 20.0
    else:
        score = max(0.5, 3.0 - 3.0 * (eaqi - 80) / 100.0)
    return _clamp(score), details


def _score_from_count(count: int, thresholds: list) -> float:
    """Return a score interpolated from (count, score) breakpoints."""
    if count <= thresholds[0][0]:
        return thresholds[0][1]
    for i in range(1, len(thresholds)):
        if count <= thresholds[i][0]:
            lo_c, lo_s = thresholds[i - 1]
            hi_c, hi_s = thresholds[i]
            frac = (count - lo_c) / max(hi_c - lo_c, 1)
            return lo_s + frac * (hi_s - lo_s)
    return thresholds[-1][1]


def _count_tags(elements: list, tag_key: str, categories: dict) -> dict:
    """Count elements matching tag values in categories dict."""
    for el in elements:
        val = el.get("tags", {}).get(tag_key, "")
        if val in categories:
            categories[val] += 1
    categories["total"] = sum(v for k, v in categories.items() if k != "total")
    return categories


def _score_healthcare(elements: list) -> tuple[float, dict]:
    cats = _count_tags(elements, "amenity", {"hospital": 0, "clinic": 0, "pharmacy": 0, "doctors": 0})
    score = _score_from_count(cats["total"], [(0, 1.0), (3, 4.0), (10, 7.0), (25, 9.0), (50, 10.0)])
    diversity = sum(1 for k, v in cats.items() if k != "total" and v > 0)
    return _clamp(score + diversity * 0.3), cats


def _score_education(elements: list) -> tuple[float, dict]:
    cats = _count_tags(elements, "amenity", {"school": 0, "university": 0, "library": 0})
    score = _score_from_count(cats["total"], [(0, 1.0), (2, 3.5), (8, 6.5), (20, 8.5), (40, 10.0)])
    diversity = sum(1 for k, v in cats.items() if k != "total" and v > 0)
    return _clamp(score + diversity * 0.4), cats


def _score_commercial(elements: list) -> tuple[float, dict]:
    cats = {"supermarket": 0, "restaurant": 0, "bank": 0, "convenience": 0, "cafe": 0}
    for el in elements:
        tags = el.get("tags", {})
        amenity, shop = tags.get("amenity", ""), tags.get("shop", "")
        key = amenity if amenity in cats else (shop if shop in cats else "")
        if key:
            cats[key] += 1
    cats["total"] = sum(cats.values())
    score = _score_from_count(cats["total"], [(0, 0.5), (5, 3.0), (15, 5.5), (40, 8.0), (80, 10.0)])
    diversity = sum(1 for k, v in cats.items() if k != "total" and v > 0)
    return _clamp(score + diversity * 0.25), cats


def _score_green_spaces(elements: list) -> tuple[float, dict]:
    cats = _count_tags(elements, "leisure",
                       {"park": 0, "garden": 0, "sports_centre": 0, "playground": 0, "pitch": 0})
    score = _score_from_count(cats["total"], [(0, 0.5), (3, 3.5), (10, 6.0), (25, 8.5), (50, 10.0)])
    diversity = sum(1 for k, v in cats.items() if k != "total" and v > 0)
    return _clamp(score + diversity * 0.3), cats


def _score_transport(elements: list) -> tuple[float, dict]:
    cats = {"bus_stop": 0, "station": 0, "halt": 0,
            "bicycle_rental": 0, "cycleway": 0, "stop_position": 0}
    for el in elements:
        tags = el.get("tags", {})
        hw, rw = tags.get("highway", ""), tags.get("railway", "")
        amenity, pt = tags.get("amenity", ""), tags.get("public_transport", "")
        if hw == "bus_stop":      cats["bus_stop"] += 1
        elif hw == "cycleway":    cats["cycleway"] += 1
        elif rw in ("station", "halt"): cats[rw] += 1
        elif amenity == "bicycle_rental": cats["bicycle_rental"] += 1
        elif pt == "stop_position": cats["stop_position"] += 1
    cats["total"] = sum(v for k, v in cats.items() if k != "total")
    score = _score_from_count(cats["total"], [(0, 0.5), (5, 3.0), (20, 6.0), (60, 8.5), (120, 10.0)])
    has_rail = 1.0 if (cats["station"] + cats["halt"]) > 0 else 0.0
    return _clamp(score + has_rail), cats


def _score_safety(elements: list) -> tuple[float, dict]:
    cats = {"police": 0, "fire_station": 0, "street_lamp": 0, "surveillance": 0}
    for el in elements:
        tags = el.get("tags", {})
        amenity = tags.get("amenity", "")
        if amenity in ("police", "fire_station"):
            cats[amenity] += 1
        elif tags.get("highway", "") == "street_lamp":
            cats["street_lamp"] += 1
        elif tags.get("man_made", "") == "surveillance":
            cats["surveillance"] += 1
    cats["total"] = sum(cats.values())
    em_score = _score_from_count(cats["police"] + cats["fire_station"],
                                 [(0, 1.0), (1, 4.0), (3, 7.0), (6, 9.0), (10, 10.0)])
    light_score = _score_from_count(cats["street_lamp"],
                                    [(0, 2.0), (20, 5.0), (80, 8.0), (200, 10.0)])
    return _clamp(0.5 * em_score + 0.5 * light_score), cats


# ---------------------------------------------------------------------------
# Composite livability
# ---------------------------------------------------------------------------

def _compute_livability(scores: dict) -> float:
    """Weighted average across all dimensions."""
    total_w, weighted = 0.0, 0.0
    for key, dim in LIVABILITY_DIMENSIONS.items():
        w = dim["weight"]
        weighted += w * scores.get(key, 5.0)
        total_w += w
    return round(weighted / total_w, 1) if total_w else 5.0


def _get_rating(score: float) -> tuple:
    """Return (label, color) for a score."""
    for lo, hi, label, color in RATING_BANDS:
        if lo <= score <= hi:
            return label, color
    return "POOR", "#ef4444"


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------

def _render_score_gauge(score: float, label: str, color: str):
    """Big circular gauge for overall livability index."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number={"suffix": " / 10", "font": {"size": 38}},
        title={"text": f"Overall Livability: {label}", "font": {"size": 18}},
        gauge={"axis": {"range": [0, 10], "tickwidth": 1}, "bar": {"color": color},
               "steps": [{"range": [0, 3], "color": "#fef2f2"},
                         {"range": [3, 5], "color": "#fff7ed"},
                         {"range": [5, 7], "color": "#fefce8"},
                         {"range": [7, 9], "color": "#f0fdf4"},
                         {"range": [9, 10], "color": "#ecfdf5"}],
               "threshold": {"line": {"color": "#111827", "width": 3},
                             "thickness": 0.8, "value": score}}))
    fig.update_layout(height=280, margin=dict(t=60, b=20, l=40, r=40))
    st.plotly_chart(fig, use_container_width=True, key="livsco_pchart1")


def _render_radar_chart(scores: dict):
    """Radar / spider chart of all 8 dimensions."""
    labels = [LIVABILITY_DIMENSIONS[k]["name"] for k in scores]
    values = [scores[k] for k in scores]
    labels.append(labels[0])
    values.append(values[0])
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=labels, fill="toself",
        fillcolor="rgba(59,130,246,0.15)", line=dict(color="#3b82f6", width=2),
        name="Your Location"))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=False, height=400, margin=dict(t=40, b=40, l=80, r=80))
    st.plotly_chart(fig, use_container_width=True, key="livsco_pchart2")


def _render_dimension_cards(scores: dict, details: dict):
    """Render cards with progress bars for each dimension."""
    cols = st.columns(2)
    for idx, (key, dim) in enumerate(LIVABILITY_DIMENSIONS.items()):
        col = cols[idx % 2]
        s = scores.get(key, 0.0)
        _, rating_color = _get_rating(s)
        det = details.get(key, {})
        with col:
            st.markdown(
                f"<div style='border:1px solid {dim['color']}33; border-radius:10px; "
                f"padding:14px; margin-bottom:10px; background:{dim['color']}08;'>"
                f"<div style='display:flex; justify-content:space-between; align-items:center;'>"
                f"<span style='font-size:1.1rem; font-weight:600;'>"
                f"{dim['icon']} {dim['name']}</span>"
                f"<span style='font-size:1.3rem; font-weight:700; color:{rating_color};'>"
                f"{s}/10</span></div>"
                f"<div style='background:#e5e7eb; border-radius:6px; height:8px; margin:8px 0;'>"
                f"<div style='background:{dim['color']}; width:{s * 10}%; "
                f"height:100%; border-radius:6px;'></div></div>"
                f"<div style='font-size:0.78rem; color:#6b7280;'>{dim['desc']}</div></div>",
                unsafe_allow_html=True)
            if det:
                with st.expander(f"Details: {dim['name']}", expanded=False):
                    for dk, dv in det.items():
                        if dk == "note":
                            st.info(dv)
                        else:
                            st.markdown(f"- **{dk.replace('_', ' ').title()}**: {dv}")


def _render_comparison_table(overall: float):
    """Show comparison with reference cities."""
    st.markdown("### Comparison with Reference Cities")
    rows = sorted(REFERENCE_CITIES.items(), key=lambda x: x[1]["score"], reverse=True)
    header = "| City | Ref. Score | vs. Your Location |\n|---|---|---|\n"
    body = ""
    for city, info in rows:
        diff = overall - info["score"]
        diff_str = f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}"
        body += f"| {city} | {info['score']} | {diff_str} |\n"
    st.markdown(header + body)


def _render_map(lat: float, lon: float, all_elements: dict):
    """Render folium map with service locations."""
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.info("Install folium and streamlit-folium for interactive map.")
        return
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="CartoDB positron")
    folium.Marker([lat, lon], popup="Target Location",
                  icon=folium.Icon(color="red", icon="home", prefix="fa")).add_to(m)
    cat_colors = {"healthcare": "red", "education": "purple", "commercial": "pink",
                  "green_spaces": "green", "transport": "blue", "safety": "orange"}
    count = 0
    for cat_key, elements in all_elements.items():
        color = cat_colors.get(cat_key, "gray")
        for el in elements:
            if count >= 150:
                break
            el_lat, el_lon = el.get("lat"), el.get("lon")
            if el_lat is None or el_lon is None:
                center = el.get("center", {})
                el_lat, el_lon = center.get("lat"), center.get("lon")
            if el_lat is None or el_lon is None:
                continue
            tags = el.get("tags", {})
            name = tags.get("name", cat_key.replace("_", " ").title())
            amenity = tags.get("amenity", tags.get("leisure", tags.get("shop", "")))
            folium.CircleMarker([el_lat, el_lon], radius=4, color=color, fill=True,
                                fill_opacity=0.7, popup=f"{name} ({amenity})").add_to(m)
            count += 1
    folium.Circle([lat, lon], radius=3000, color="#3b82f6", fill=False,
                  dash_array="5", popup="3 km radius").add_to(m)
    folium.Circle([lat, lon], radius=5000, color="#8b5cf6", fill=False,
                  dash_array="10", popup="5 km radius").add_to(m)
    st_folium(m, width=None, height=480, key="livab_map")


def _render_weight_breakdown(scores: dict):
    """Horizontal bar chart showing weighted contribution of each dimension."""
    names, contributions, colors = [], [], []
    for key, dim in LIVABILITY_DIMENSIONS.items():
        names.append(dim["name"])
        contributions.append(round(scores.get(key, 0.0) * dim["weight"], 2))
        colors.append(dim["color"])
    fig = go.Figure(go.Bar(
        x=contributions, y=names, orientation="h", marker_color=colors,
        text=[f"{c:.2f}" for c in contributions], textposition="outside"))
    fig.update_layout(title="Weighted Contribution to Overall Score",
                      xaxis_title="Contribution", yaxis_title="", height=340,
                      margin=dict(l=160, r=40, t=50, b=40),
                      yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True, key="livsco_pchart3")


def _render_summary_insights(scores: dict, overall: float):
    """Generate textual insights from scores."""
    label, color = _get_rating(overall)
    st.markdown(
        f"<div style='background:{color}18; border-left:4px solid {color}; "
        f"padding:16px; border-radius:8px; margin-bottom:16px;'>"
        f"<h3 style='margin:0 0 8px 0; color:{color};'>Livability Rating: {label}</h3>"
        f"<p style='margin:0; color:#374151;'>Overall Index: <b>{overall}/10</b></p></div>",
        unsafe_allow_html=True)
    # Strengths and weaknesses
    sorted_dims = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    strengths = [(k, v) for k, v in sorted_dims if v >= 7.0]
    weaknesses = [(k, v) for k, v in sorted_dims if v < 5.0]
    col_s, col_w = st.columns(2)
    with col_s:
        st.markdown("**Strengths**")
        if strengths:
            for k, v in strengths[:3]:
                dim = LIVABILITY_DIMENSIONS[k]
                st.markdown(f"- {dim['icon']} {dim['name']}: **{v}/10**")
        else:
            st.markdown("_No strong dimensions detected._")
    with col_w:
        st.markdown("**Areas for Improvement**")
        if weaknesses:
            for k, v in weaknesses[:3]:
                dim = LIVABILITY_DIMENSIONS[k]
                st.markdown(f"- {dim['icon']} {dim['name']}: **{v}/10**")
        else:
            st.markdown("_No weak dimensions detected._")
    # Recommendations
    st.markdown("---")
    st.markdown("**Recommendations**")
    rec_map = {
        "climate": "Climate comfort is low. Consider seasonal timing or climate-adapted housing.",
        "air_quality": "Air quality is a concern. Indoor air filtration and avoiding outdoor peak-hours is advised.",
        "healthcare": "Healthcare access is limited. Verify emergency response times and keep a first-aid kit.",
        "education": "Educational facilities are sparse. Online or remote learning options may supplement.",
        "commercial": "Commercial services are limited. Plan for bulk shopping or delivery services.",
        "green_spaces": "Recreational areas are scarce. Consider proximity to nature reserves outside the scanned radius.",
        "transport": "Public transport is weak. Personal vehicle or ride-sharing may be necessary.",
        "safety": "Safety infrastructure is lacking. Check local crime statistics and community networks.",
    }
    recs = [msg for key, msg in rec_map.items() if scores.get(key, 10) < 5]
    if recs:
        for r in recs:
            st.markdown(f"- {r}")
    else:
        st.success("This location scores well across all dimensions. No critical recommendations.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_livability_score_tab():
    """Render the Livability Score AI module."""
    st.markdown("## Livability Score AI")
    st.caption("Comprehensive quality-of-life assessment for any location")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9028, format="%.4f", key="livab_lat")
    lon = c2.number_input("Longitude", value=12.4964, format="%.4f", key="livab_lon")

    if st.button("Calculate Livability", key="livab_btn"):
        scores: dict = {}
        details: dict = {}
        all_elements: dict = {}

        with st.spinner("Fetching climate and air quality data..."):
            climate_data = _fetch_climate_data(lat, lon)
            aq_data = _fetch_air_quality(lat, lon)
        scores["climate"], details["climate"] = _score_climate(climate_data)
        scores["air_quality"], details["air_quality"] = _score_air_quality(aq_data)

        fetch_configs = [
            ("healthcare", "Scanning healthcare facilities (5 km)...", _fetch_healthcare, _score_healthcare),
            ("education", "Scanning education facilities (5 km)...", _fetch_education, _score_education),
            ("commercial", "Scanning commercial services (3 km)...", _fetch_commercial, _score_commercial),
            ("green_spaces", "Scanning green spaces (3 km)...", _fetch_green_spaces, _score_green_spaces),
            ("transport", "Scanning transport infrastructure (3 km)...", _fetch_transport, _score_transport),
            ("safety", "Scanning safety infrastructure (3 km)...", _fetch_safety, _score_safety),
        ]
        for dim_key, msg, fetch_fn, score_fn in fetch_configs:
            with st.spinner(msg):
                elems = fetch_fn(lat, lon)
                all_elements[dim_key] = elems
                scores[dim_key], details[dim_key] = score_fn(elems)

        overall = _compute_livability(scores)
        label, color = _get_rating(overall)

        st.markdown("---")
        _render_score_gauge(overall, label, color)
        _render_summary_insights(scores, overall)

        st.markdown("---")
        st.markdown("### Dimension Scores")
        _render_dimension_cards(scores, details)

        st.markdown("---")
        rc, wc = st.columns(2)
        with rc:
            st.markdown("### Radar Profile")
            _render_radar_chart(scores)
        with wc:
            st.markdown("### Weight Breakdown")
            _render_weight_breakdown(scores)

        st.markdown("---")
        st.markdown("### Service Locations Map")
        _render_map(lat, lon, all_elements)

        st.markdown("---")
        _render_comparison_table(overall)

        with st.expander("Raw Score Data", expanded=False):
            st.json({
                "location": {"latitude": lat, "longitude": lon},
                "overall_score": overall, "rating": label,
                "dimensions": {
                    k: {"score": scores[k], "weight": LIVABILITY_DIMENSIONS[k]["weight"],
                        "weighted": round(scores[k] * LIVABILITY_DIMENSIONS[k]["weight"], 3),
                        "details": details.get(k, {})}
                    for k in LIVABILITY_DIMENSIONS},
                "reference_cities": {c: i["score"] for c, i in REFERENCE_CITIES.items()},
            })
