"""Expedition & Field Mission Planner -- TerraScout AI.
8-dimension planning: weather, terrain, water, shelter, emergency, comms,
supply, hazards.  Free APIs only (Open-Meteo, Open Topo Data, Overpass, USGS).
"""

import html as html_module
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

# -- Constants ----------------------------------------------------------------
CLR_BG, CLR_CARD, CLR_BORDER = "#1a1a2e", "#16213e", "#2a3550"
CLR_TEXT, CLR_TEXT_SEC, CLR_ACCENT = "#e8ecf4", "#8b97b0", "#f59e0b"
CLR_GREEN, CLR_YELLOW, CLR_ORANGE = "#22c55e", "#fbbf24", "#f97316"
CLR_RED, CLR_BLUE, CLR_PURPLE = "#ef4444", "#3b82f6", "#8b5cf6"
CLR_CYAN, CLR_PINK = "#06b6d4", "#ec4899"

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm + hail (L)", 99: "Thunderstorm + hail (H)",
}

MISSION_TYPES = [
    "Research Expedition", "Humanitarian Aid", "Military Recon",
    "Adventure/Trekking", "Wildlife Survey",
]

READINESS_BANDS = [
    (80, 101, "Mission GO", CLR_GREEN), (60, 80, "GO with Caution", CLR_YELLOW),
    (40, 60, "Marginal -- Extra Prep", CLR_ORANGE), (0, 40, "NO-GO -- Re-plan", CLR_RED),
]

SECTION_WEIGHTS = {
    "weather": 0.20, "terrain": 0.15, "water": 0.12, "shelter": 0.10,
    "emergency": 0.13, "comms": 0.10, "supply": 0.08, "hazard": 0.12,
}

# -- Helpers ------------------------------------------------------------------

def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _readiness_label(score):
    for lo, hi, label, color in READINESS_BANDS:
        if lo <= score < hi:
            return label, color
    return "NO-GO", CLR_RED

def _safe_mean(vals):
    cleaned = [v for v in (vals or []) if v is not None]
    return sum(cleaned) / len(cleaned) if cleaned else 0.0

def _count_elements(data):
    return len(data.get("elements", [])) if isinstance(data, dict) else 0

def _nearest_element(lat, lon, elements):
    """Return (distance_km, element) of the nearest Overpass element."""
    best_d, best_el = None, None
    for el in elements:
        elat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        elon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if elat is not None and elon is not None:
            d = _haversine(lat, lon, elat, elon)
            if best_d is None or d < best_d:
                best_d, best_el = d, el
    return best_d, best_el

def _metric_card(title, value, subtitle, color):
    st.markdown(
        f'<div style="background:{CLR_CARD};border-left:4px solid {color};'
        f'border-radius:8px;padding:14px 18px;margin-bottom:10px;">'
        f'<div style="color:{CLR_TEXT_SEC};font-size:12px;text-transform:uppercase;'
        f'letter-spacing:1px;">{title}</div>'
        f'<div style="color:{color};font-size:28px;font-weight:700;margin:4px 0;">'
        f'{value}</div>'
        f'<div style="color:{CLR_TEXT_SEC};font-size:12px;">{subtitle}</div></div>',
        unsafe_allow_html=True)

def _section_header(icon, title, score, color):
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;margin:18px 0 8px;">'
        f'<span style="font-size:22px;">{icon}</span>'
        f'<span style="color:{CLR_TEXT};font-size:17px;font-weight:600;">{title}</span>'
        f'<span style="background:{color}22;color:{color};padding:3px 10px;'
        f'border-radius:12px;font-size:13px;font-weight:600;margin-left:auto;">'
        f'{score:.0f}/100</span></div>', unsafe_allow_html=True)

# -- Data Fetchers (cached, timeout=10, try/except) ---------------------------

@st.cache_data(ttl=900)
def _fetch_weather_forecast(lat, lon):
    """16-day weather forecast from Open-Meteo."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "precipitation_probability_max,wind_speed_10m_max,weathercode"
        "&timezone=auto&forecast_days=16"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Weather fetch error: %s", e)
        return None

@st.cache_data(ttl=900)
def _fetch_elevation(lat, lon):
    """Single-point elevation from Open Topo Data."""
    url = f"https://api.opentopodata.org/v1/srtm90m?locations={lat},{lon}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])
        return results[0].get("elevation") if results else None
    except Exception as e:
        logger.warning("Elevation fetch error: %s", e)
        return None

@st.cache_data(ttl=900)
def _fetch_elevation_profile(lat, lon, points=5):
    """Fetch a small elevation grid around the location for slope analysis."""
    offset = 0.03
    locations = []
    for i in range(points):
        for j in range(points):
            plat = lat - offset + (2 * offset * i / (points - 1))
            plon = lon - offset + (2 * offset * j / (points - 1))
            locations.append(f"{plat:.5f},{plon:.5f}")
    url = f"https://api.opentopodata.org/v1/srtm90m?locations={'|'.join(locations)}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return [res.get("elevation") for res in r.json().get("results", [])]
    except Exception as e:
        logger.warning("Elevation profile error: %s", e)
        return []

@st.cache_data(ttl=900)
def _fetch_overpass(query_body, label="Overpass"):
    """Generic Overpass API query helper."""
    query = f"[out:json][timeout:25];\n(\n{query_body}\n);\nout center body;"
    try:
        r = requests.post("https://overpass-api.de/api/interpreter",
                          data={"data": query}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("%s fetch error: %s", label, e)
        return {"elements": []}

def _build_ovp(tags, lat, lon, radius):
    """Build Overpass query string from list of (type, key=value) pairs."""
    return "".join(f'{t}[{kv}](around:{radius},{lat},{lon});' for t, kv in tags)

@st.cache_data(ttl=900)
def _fetch_water_sources(lat, lon, radius=10000):
    tags = [("node", '"natural"="spring"'), ("node", '"natural"="water"'),
            ("way", '"natural"="water"'), ("node", '"amenity"="drinking_water"'),
            ("way", '"waterway"="stream"'), ("way", '"waterway"="river"'),
            ("node", '"man_made"="water_well"')]
    return _fetch_overpass(_build_ovp(tags, lat, lon, radius), "Water sources")

@st.cache_data(ttl=900)
def _fetch_shelters(lat, lon, radius=10000):
    tags = [("node", '"tourism"="alpine_hut"'), ("node", '"tourism"="wilderness_hut"'),
            ("node", '"tourism"="camp_site"'), ("node", '"amenity"="shelter"'),
            ("way", '"building"="hut"'), ("way", '"building"="cabin"'),
            ("node", '"tourism"="hotel"'), ("node", '"tourism"="hostel"'),
            ("way", '"tourism"="camp_site"')]
    return _fetch_overpass(_build_ovp(tags, lat, lon, radius), "Shelters")

@st.cache_data(ttl=900)
def _fetch_emergency_services(lat, lon, radius=20000):
    tags = [("node", '"amenity"="hospital"'), ("way", '"amenity"="hospital"'),
            ("node", '"amenity"="fire_station"'), ("node", '"amenity"="police"'),
            ("node", '"emergency"="phone"'), ("node", '"amenity"="mountain_rescue"'),
            ("node", '"emergency"="defibrillator"'), ("node", '"amenity"="clinic"')]
    return _fetch_overpass(_build_ovp(tags, lat, lon, radius), "Emergency services")

@st.cache_data(ttl=900)
def _fetch_comms(lat, lon, radius=10000):
    tags = [("node", '"man_made"="mast"'),
            ("node", '"man_made"="tower"]["tower:type"="communication"'),
            ("node", '"telecom"="exchange"'), ("node", '"man_made"="antenna"'),
            ("way", '"man_made"="mast"')]
    return _fetch_overpass(_build_ovp(tags, lat, lon, radius), "Communications")

@st.cache_data(ttl=900)
def _fetch_supply_points(lat, lon, radius=10000):
    tags = [("node", '"shop"="supermarket"'), ("node", '"shop"="convenience"'),
            ("node", '"amenity"="fuel"'), ("node", '"shop"="hardware"'),
            ("node", '"shop"="outdoor"'), ("node", '"shop"="general"'),
            ("way", '"shop"="supermarket"')]
    return _fetch_overpass(_build_ovp(tags, lat, lon, radius), "Supply points")

@st.cache_data(ttl=900)
def _fetch_earthquakes(lat, lon, radius_km=100, days=365):
    """Recent earthquakes from USGS within radius."""
    end = datetime.utcnow()
    start = end - timedelta(days=days)
    url = (
        "https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
        f"&starttime={start.strftime('%Y-%m-%d')}&endtime={end.strftime('%Y-%m-%d')}"
        f"&latitude={lat}&longitude={lon}&maxradiuskm={radius_km}"
        "&minmagnitude=2.5&limit=100&orderby=magnitude"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Earthquake fetch error: %s", e)
        return {"features": []}

# -- Scoring ------------------------------------------------------------------

def _score_weather(weather_data):
    """Score weather conditions (0-100) and identify best departure window."""
    if not weather_data or "daily" not in weather_data:
        return 50.0, None, []
    daily = weather_data["daily"]
    dates = daily.get("time", [])
    t_max = daily.get("temperature_2m_max", [])
    t_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    precip_prob = daily.get("precipitation_probability_max", [])
    wind = daily.get("wind_speed_10m_max", [])
    codes = daily.get("weathercode", [])
    if not dates:
        return 50.0, None, []

    day_scores = []
    for i in range(len(dates)):
        s = 100.0
        tmax_i = t_max[i] if i < len(t_max) and t_max[i] is not None else 20
        tmin_i = t_min[i] if i < len(t_min) and t_min[i] is not None else 10
        tavg = (tmax_i + tmin_i) / 2.0
        if tavg < 5:
            s -= min(30, (5 - tavg) * 4)
        elif tavg > 35:
            s -= min(30, (tavg - 35) * 4)
        pp = precip[i] if i < len(precip) and precip[i] is not None else 0
        s -= min(30, pp * 3)
        prob = precip_prob[i] if i < len(precip_prob) and precip_prob[i] is not None else 0
        s -= prob * 0.15
        w = wind[i] if i < len(wind) and wind[i] is not None else 10
        if w > 20:
            s -= min(25, (w - 20) * 1.5)
        c = codes[i] if i < len(codes) and codes[i] is not None else 0
        if c >= 95:
            s -= 30
        elif c >= 80:
            s -= 15
        elif c >= 61:
            s -= 10
        day_scores.append({"date": dates[i], "score": _clamp(s), "idx": i})

    best_start, best_avg = 0, 0
    for start in range(len(day_scores) - 2):
        avg = sum(day_scores[start + k]["score"] for k in range(3)) / 3.0
        if avg > best_avg:
            best_avg, best_start = avg, start
    overall = _safe_mean([d["score"] for d in day_scores])
    best_date = day_scores[best_start]["date"] if day_scores else None
    return overall, best_date, day_scores

def _score_terrain(elevation, profile):
    """Score terrain difficulty (0-100, higher = easier / better)."""
    if elevation is None:
        return 50.0, "Unknown", 0.0
    alt_score = 100.0
    if elevation > 4000:
        alt_score -= min(40, (elevation - 4000) * 0.02)
    elif elevation > 2500:
        alt_score -= (elevation - 2500) * 0.015
    elif elevation < 0:
        alt_score -= 20
    max_slope = 0.0
    if profile and len(profile) > 1:
        valid = [e for e in profile if e is not None]
        if len(valid) > 1:
            spread = max(valid) - min(valid)
            max_slope = spread / (6.0 * 1000) * 100
            if max_slope > 30:
                alt_score -= 25
            elif max_slope > 15:
                alt_score -= 15
            elif max_slope > 8:
                alt_score -= 8
    if elevation > 3500:
        terrain_type = "Alpine / High Mountain"
    elif elevation > 2000:
        terrain_type = "Mountain"
    elif elevation > 800:
        terrain_type = "Highland / Plateau"
    elif elevation > 200:
        terrain_type = "Hilly Terrain"
    elif elevation > 0:
        terrain_type = "Lowland / Plain"
    else:
        terrain_type = "Below Sea Level / Coastal"
    return _clamp(alt_score), terrain_type, max_slope

def _score_overpass_resource(data, lat, lon, ideal_count=5, max_dist_km=5.0):
    """Generic resource scoring from Overpass data."""
    elements = data.get("elements", []) if isinstance(data, dict) else []
    count = len(elements)
    if count == 0:
        return 10.0, 0, None
    dist, _ = _nearest_element(lat, lon, elements)
    count_score = min(50, count / ideal_count * 50)
    dist_score = 50.0
    if dist is not None:
        if dist > max_dist_km * 2:
            dist_score = 10
        elif dist > max_dist_km:
            dist_score = 30
    return _clamp(count_score + dist_score), count, dist

def _score_hazards(earthquake_data, weather_data, elevation):
    """Hazard assessment score (0-100, higher = safer)."""
    score, hazards = 100.0, []
    quakes = earthquake_data.get("features", []) if isinstance(earthquake_data, dict) else []
    if quakes:
        max_mag = max((f["properties"].get("mag", 0) or 0) for f in quakes)
        q_count = len(quakes)
        if max_mag >= 5.0:
            score -= 25
            hazards.append(f"Seismic: M{max_mag:.1f} recorded ({q_count} events)")
        elif max_mag >= 3.5:
            score -= 12
            hazards.append(f"Moderate seismic: M{max_mag:.1f} ({q_count} events)")
        elif q_count > 10:
            score -= 8
            hazards.append(f"Minor seismic activity ({q_count} events)")
    if weather_data and "daily" in weather_data:
        daily = weather_data["daily"]
        codes = daily.get("weathercode", [])
        wind = daily.get("wind_speed_10m_max", [])
        precip = daily.get("precipitation_sum", [])
        severe_days = sum(1 for c in codes if c is not None and c >= 95)
        if severe_days > 0:
            score -= severe_days * 8
            hazards.append(f"Severe weather: {severe_days} thunderstorm day(s)")
        max_wind = max((w for w in wind if w is not None), default=0)
        if max_wind > 60:
            score -= 15
            hazards.append(f"Extreme wind: {max_wind:.0f} km/h")
        elif max_wind > 40:
            score -= 8
            hazards.append(f"High wind: {max_wind:.0f} km/h")
        heavy_rain_days = sum(1 for p in precip if p is not None and p > 20)
        if heavy_rain_days > 3:
            score -= 10
            hazards.append(f"Heavy rain: {heavy_rain_days} day(s) >20mm")
    if elevation is not None:
        if elevation > 4000:
            score -= 15
            hazards.append(f"Extreme altitude: {elevation:.0f}m (AMS risk)")
        elif elevation > 3000:
            score -= 8
            hazards.append(f"High altitude: {elevation:.0f}m")
    if not hazards:
        hazards.append("No significant hazards identified")
    return _clamp(score), hazards

# -- Equipment Checklist -------------------------------------------------------

def _generate_equipment(mission_type, terrain_type, weather_data, elevation):
    """Auto-generate equipment checklist based on conditions."""
    items = [
        ("Navigation", ["Topographic map", "Compass", "GPS device", "Backup batteries"]),
        ("Communication", ["Satellite phone / PLB", "Two-way radios", "Whistle"]),
        ("First Aid", ["First-aid kit", "Emergency blanket", "Sunscreen SPF50+"]),
        ("Water", ["Water bottles (3L min)", "Purification tablets", "Portable filter"]),
        ("Shelter", ["Tent / bivvy", "Sleeping bag", "Ground mat"]),
    ]
    wx = []
    if weather_data and "daily" in weather_data:
        daily = weather_data["daily"]
        t_min_v = [v for v in daily.get("temperature_2m_min", []) if v is not None]
        t_max_v = [v for v in daily.get("temperature_2m_max", []) if v is not None]
        min_t, max_t = (min(t_min_v) if t_min_v else 10), (max(t_max_v) if t_max_v else 25)
        total_rain = sum(p for p in daily.get("precipitation_sum", []) if p is not None)
        if min_t < 0:
            wx.extend(["Insulated jacket", "Thermal base layers", "Hand warmers", "Balaclava"])
        elif min_t < 10:
            wx.extend(["Fleece layer", "Warm hat", "Gloves"])
        if max_t > 35:
            wx.extend(["Sun hat", "Electrolyte sachets", "Cooling towel"])
        if total_rain > 30:
            wx.extend(["Waterproof jacket", "Rain pants", "Dry bags", "Gaiters"])
        else:
            wx.append("Light rain jacket")
    if wx:
        items.append(("Weather Gear", wx))
    tx = []
    if "Alpine" in terrain_type or "Mountain" in terrain_type:
        tx.extend(["Trekking poles", "Crampons", "Rope (30m)", "Carabiners", "Helmet"])
    if "Highland" in terrain_type or "Hilly" in terrain_type:
        tx.extend(["Trekking poles", "Ankle-support boots"])
    if elevation is not None and elevation > 3000:
        tx.extend(["Altitude sickness medication (Diamox)", "Pulse oximeter"])
    if tx:
        items.append(("Terrain Gear", tx))
    mission_map = {
        "Research Expedition": ["Field notebook", "Sample containers", "Camera + extra SD",
                                "Laptop / tablet", "Solar charger"],
        "Humanitarian Aid": ["MRE / ration packs", "Water purification (bulk)",
                             "Tarps (large)", "Medical supplies extended"],
        "Military Recon": ["Camouflage net", "Night vision aid", "Range finder",
                           "Encrypted comms", "MREs (7-day)"],
        "Adventure/Trekking": ["Trekking poles", "Trail snacks", "Headlamp + spare",
                               "Multi-tool", "Paracord (15m)"],
        "Wildlife Survey": ["Binoculars", "Camera with telephoto lens", "Field guide",
                            "Insect repellent", "Data logging sheets"],
    }
    mx = mission_map.get(mission_type, [])
    if mx:
        items.append(("Mission-Specific", mx))
    return items

# -- Charts -------------------------------------------------------------------

def _build_weather_chart(day_scores, weather_data):
    """Plotly chart showing 16-day forecast with score overlay."""
    if not day_scores or not weather_data or "daily" not in weather_data:
        return None
    daily = weather_data["daily"]
    dates = [d["date"] for d in day_scores]
    scores = [d["score"] for d in day_scores]
    t_max = daily.get("temperature_2m_max", [])
    t_min = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=precip[:len(dates)], name="Precipitation (mm)",
                         marker_color="rgba(59,130,246,0.5)", yaxis="y2"))
    fig.add_trace(go.Scatter(x=dates, y=t_max[:len(dates)], name="Temp Max",
                             mode="lines+markers", line=dict(color=CLR_RED, width=2),
                             marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=dates, y=t_min[:len(dates)], name="Temp Min",
                             mode="lines+markers", line=dict(color=CLR_BLUE, width=2),
                             marker=dict(size=5)))
    fig.add_trace(go.Scatter(x=dates, y=scores, name="Day Score", mode="lines+markers",
                             line=dict(color=CLR_GREEN, width=3, dash="dot"),
                             marker=dict(size=7, symbol="diamond"), yaxis="y3"))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=CLR_BG, plot_bgcolor=CLR_CARD,
        height=370, margin=dict(l=50, r=50, t=40, b=40),
        title=dict(text="16-Day Weather Window", font=dict(size=14)),
        legend=dict(orientation="h", y=-0.15, font=dict(size=10)),
        xaxis=dict(title="Date", gridcolor=CLR_BORDER),
        yaxis=dict(title="Temperature (C)", side="left", gridcolor=CLR_BORDER),
        yaxis2=dict(title="Precipitation (mm)", overlaying="y", side="right", showgrid=False),
        yaxis3=dict(overlaying="y", side="right", position=0.95, range=[0, 100],
                    showgrid=False, visible=False),
    )
    return fig

def _build_readiness_gauge(score):
    """Plotly gauge chart for mission readiness."""
    label, color = _readiness_label(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=score,
        title=dict(text="Mission Readiness", font=dict(size=16, color=CLR_TEXT)),
        number=dict(suffix="/100", font=dict(size=30, color=color)),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=CLR_TEXT_SEC),
            bar=dict(color=color), bgcolor=CLR_CARD, bordercolor=CLR_BORDER,
            steps=[dict(range=[0, 40], color="rgba(239,68,68,0.13)"),
                   dict(range=[40, 60], color="rgba(249,115,22,0.13)"),
                   dict(range=[60, 80], color="rgba(251,191,36,0.13)"),
                   dict(range=[80, 100], color="rgba(34,197,94,0.13)")],
            threshold=dict(line=dict(color="white", width=2), thickness=0.8, value=score),
        ),
    ))
    fig.update_layout(paper_bgcolor=CLR_BG, plot_bgcolor=CLR_CARD,
                      height=260, margin=dict(l=30, r=30, t=50, b=20))
    return fig

def _build_radar_chart(section_scores):
    """Radar chart of all 8 planning dimensions."""
    labels = list(section_scores.keys())
    vals = list(section_scores.values())
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=labels + [labels[0]],
        fill="toself", fillcolor="rgba(59,130,246,0.15)",
        line=dict(color=CLR_BLUE, width=2), marker=dict(size=6), name="Score"))
    fig.update_layout(
        polar=dict(bgcolor=CLR_CARD,
                   radialaxis=dict(visible=True, range=[0, 100], gridcolor=CLR_BORDER,
                                   tickfont=dict(size=9)),
                   angularaxis=dict(gridcolor=CLR_BORDER,
                                    tickfont=dict(size=10, color=CLR_TEXT))),
        paper_bgcolor=CLR_BG, showlegend=False, height=370,
        margin=dict(l=60, r=60, t=40, b=40),
        title=dict(text="Planning Dimensions", font=dict(size=14, color=CLR_TEXT)))
    return fig

def _build_terrain_profile_chart(elevations):
    """Simple elevation profile chart."""
    if not elevations:
        return None
    valid = [e if e is not None else 0 for e in elevations]
    x_labels = [f"P{i + 1}" for i in range(len(valid))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_labels, y=valid, mode="lines+markers", fill="tozeroy",
        fillcolor="rgba(201,166,107,0.2)", line=dict(color="#c9a66b", width=2),
        marker=dict(size=6, color="#c9a66b"), name="Elevation"))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor=CLR_BG, plot_bgcolor=CLR_CARD,
        height=260, margin=dict(l=50, r=30, t=40, b=30),
        title=dict(text="Elevation Profile (sample grid)", font=dict(size=13)),
        xaxis=dict(title="Sample Point", gridcolor=CLR_BORDER),
        yaxis=dict(title="Elevation (m)", gridcolor=CLR_BORDER))
    return fig

# -- Folium Map ---------------------------------------------------------------

def _build_expedition_map(lat, lon, water_data, shelter_data, emergency_data,
                          comms_data, supply_data, earthquake_data):
    """Build a folium map with all waypoints and hazard markers."""
    try:
        import folium
        from folium.plugins import MarkerCluster
    except ImportError:
        return None

    m = folium.Map(location=[lat, lon], zoom_start=12,
                   tiles="OpenStreetMap", control_scale=True)
    folium.Marker([lat, lon], popup="<b>Mission Base</b>", tooltip="Base Camp",
                  icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(m)

    def _add_layer(data, layer_name, icon_name, icon_color):
        elements = data.get("elements", []) if isinstance(data, dict) else []
        if not elements:
            return
        fg = folium.FeatureGroup(name=layer_name)
        cluster = MarkerCluster().add_to(fg)
        for el in elements[:60]:
            elat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
            elon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
            if elat is None or elon is None:
                continue
            name = html_module.escape(el.get("tags", {}).get("name", layer_name))
            tip = f"{layer_name}: {name}"
            folium.Marker([elat, elon], popup=tip, tooltip=tip[:40],
                          icon=folium.Icon(color=icon_color, icon=icon_name,
                                           prefix="fa")).add_to(cluster)
        fg.add_to(m)

    _add_layer(water_data, "Water Sources", "tint", "blue")
    _add_layer(shelter_data, "Shelters", "home", "orange")
    _add_layer(emergency_data, "Emergency", "plus-square", "red")
    _add_layer(comms_data, "Communications", "signal", "purple")
    _add_layer(supply_data, "Supply Points", "shopping-cart", "green")

    quakes = earthquake_data.get("features", []) if isinstance(earthquake_data, dict) else []
    if quakes:
        fg_eq = folium.FeatureGroup(name="Earthquakes (1yr)")
        for f in quakes[:30]:
            props = f.get("properties", {})
            coords = f.get("geometry", {}).get("coordinates", [])
            if len(coords) >= 2:
                mag = props.get("mag", 0) or 0
                folium.CircleMarker(
                    [coords[1], coords[0]], radius=max(3, mag * 3),
                    color=CLR_RED, fill=True, fill_color=CLR_RED, fill_opacity=0.4,
                    popup=f"M{mag:.1f} - {html_module.escape(props.get('place', 'Unknown'))}",
                    tooltip=f"M{mag:.1f}").add_to(fg_eq)
        fg_eq.add_to(m)

    folium.Circle([lat, lon], radius=10000, color=CLR_BLUE, fill=False,
                  weight=1, dash_array="5", tooltip="10 km radius").add_to(m)
    folium.Circle([lat, lon], radius=20000, color=CLR_PURPLE, fill=False,
                  weight=1, dash_array="8", tooltip="20 km radius").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m

# -- Risk Briefing ------------------------------------------------------------

def _build_risk_briefing(hazards, weather_score, terrain_score, emergency_score,
                         comms_score, mission_type):
    """Generate a risk briefing text."""
    lines = [f"**Mission Type:** {mission_type}",
             f"**Assessment Date:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ""]
    critical = []
    if weather_score < 40:
        critical.append("Adverse weather conditions across forecast window")
    if terrain_score < 40:
        critical.append("Difficult terrain requiring specialized equipment")
    if emergency_score < 30:
        critical.append("Very limited emergency service access")
    if comms_score < 30:
        critical.append("Poor communication coverage -- satellite comms mandatory")
    if critical:
        lines.append("**CRITICAL RISKS:**")
        lines.extend(f"- {c}" for c in critical)
        lines.append("")
    lines.append("**HAZARD SUMMARY:**")
    lines.extend(f"- {h}" for h in hazards)
    lines.append("")
    lines.append("**RECOMMENDATIONS:**")
    if weather_score < 60:
        lines.append("- Monitor weather closely; consider postponement")
    if emergency_score < 50:
        lines.append("- Carry extended first-aid kit and PLB")
    if comms_score < 50:
        lines.append("- Satellite communication device required")
    if terrain_score < 50:
        lines.append("- Technical climbing or scrambling gear recommended")
    lines.append("- File expedition plan with local authorities")
    lines.append("- Establish check-in schedule (every 12h minimum)")
    return "\n".join(lines)

# -- Main Render --------------------------------------------------------------

def render_expedition_planner_tab():
    """Entry point: Expedition & Field Mission Planner tab."""
    st.markdown("## Expedition & Field Mission Planner")
    st.caption("Comprehensive mission planning: weather, terrain, resources & hazards")

    # -- Input Controls -------------------------------------------------------
    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f", key="exped_lat")
    lon = c2.number_input("Longitude", value=12.5, format="%.4f", key="exped_lon")
    c3, c4 = st.columns(2)
    mission_type = c3.selectbox("Mission Type", MISSION_TYPES, key="exped_type")
    scan_radius = c4.selectbox("Scan Radius", ["5 km", "10 km", "15 km", "20 km"],
                               index=1, key="exped_radius")
    radius_m = int(scan_radius.replace(" km", "")) * 1000

    if not st.button("Plan Expedition", key="exped_btn"):
        st.info("Configure coordinates and mission type, then click **Plan Expedition**.")
        return

    # -- Data Collection ------------------------------------------------------
    prog = st.progress(0, text="Collecting mission intelligence ...")
    weather_data = _fetch_weather_forecast(lat, lon);          prog.progress(12)
    elevation = _fetch_elevation(lat, lon);                    prog.progress(20)
    elev_profile = _fetch_elevation_profile(lat, lon);         prog.progress(28)
    water_data = _fetch_water_sources(lat, lon, radius_m);     prog.progress(38)
    shelter_data = _fetch_shelters(lat, lon, radius_m);        prog.progress(48)
    emergency_data = _fetch_emergency_services(lat, lon, min(radius_m * 2, 30000))
    prog.progress(58)
    comms_data = _fetch_comms(lat, lon, radius_m);             prog.progress(68)
    supply_data = _fetch_supply_points(lat, lon, radius_m);    prog.progress(78)
    earthquake_data = _fetch_earthquakes(lat, lon, radius_km=max(100, radius_m // 500))
    prog.progress(88)

    # -- Scoring --------------------------------------------------------------
    weather_score, best_date, day_scores = _score_weather(weather_data)
    terrain_score, terrain_type, max_slope = _score_terrain(elevation, elev_profile)
    water_score, water_count, water_dist = _score_overpass_resource(
        water_data, lat, lon, ideal_count=8, max_dist_km=3.0)
    shelter_score, shelter_count, shelter_dist = _score_overpass_resource(
        shelter_data, lat, lon, ideal_count=4, max_dist_km=5.0)
    emergency_score, emerg_count, emerg_dist = _score_overpass_resource(
        emergency_data, lat, lon, ideal_count=3, max_dist_km=10.0)
    comms_score, comms_count, comms_dist = _score_overpass_resource(
        comms_data, lat, lon, ideal_count=3, max_dist_km=5.0)
    supply_score, supply_count, supply_dist = _score_overpass_resource(
        supply_data, lat, lon, ideal_count=4, max_dist_km=5.0)
    hazard_score, hazards = _score_hazards(earthquake_data, weather_data, elevation)

    section_scores = {
        "Weather": weather_score, "Terrain": terrain_score,
        "Water": water_score, "Shelter": shelter_score,
        "Emergency": emergency_score, "Comms": comms_score,
        "Supply": supply_score, "Hazards": hazard_score,
    }
    weights_ordered = [SECTION_WEIGHTS[k] for k in
                       ["weather", "terrain", "water", "shelter",
                        "emergency", "comms", "supply", "hazard"]]
    overall_score = _clamp(sum(s * w for s, w in
                               zip(section_scores.values(), weights_ordered)))
    label, label_color = _readiness_label(overall_score)
    prog.progress(100, text="Mission planning complete!")

    # -- Mission Briefing Card ------------------------------------------------
    st.markdown("---")
    st.markdown(
        f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};'
        f'border-radius:12px;padding:20px 28px;margin-bottom:18px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;">'
        f'<div><div style="color:{CLR_TEXT};font-size:20px;font-weight:700;">'
        f'Mission Briefing: {mission_type}</div>'
        f'<div style="color:{CLR_TEXT_SEC};font-size:13px;margin-top:4px;">'
        f'Location: {lat:.4f}, {lon:.4f} | Elevation: {elevation or "N/A"} m | '
        f'Terrain: {terrain_type} | Scan: {scan_radius}</div></div>'
        f'<div style="text-align:center;">'
        f'<div style="background:{label_color}22;color:{label_color};'
        f'padding:8px 20px;border-radius:20px;font-weight:700;font-size:18px;'
        f'border:1px solid {label_color}44;">'
        f'{label} ({overall_score:.0f}/100)</div></div></div>'
        f'<div style="color:{CLR_TEXT_SEC};font-size:12px;margin-top:10px;">'
        f'Best departure window: <b style="color:{CLR_GREEN};">{best_date or "N/A"}</b>'
        f' | Assessment: {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}'
        f'</div></div>', unsafe_allow_html=True)

    # -- Readiness Gauge + Radar ----------------------------------------------
    gc1, gc2 = st.columns(2)
    with gc1:
        st.plotly_chart(_build_readiness_gauge(overall_score, key="exppla_pchart1"),
                        use_container_width=True, key="exped_gauge")
    with gc2:
        st.plotly_chart(_build_radar_chart(section_scores, key="exppla_pchart2"),
                        use_container_width=True, key="exped_radar")

    # -- S1: Weather Window ---------------------------------------------------
    _section_header("1.", "Weather Window (16-Day)", weather_score, CLR_BLUE)
    weather_fig = _build_weather_chart(day_scores, weather_data)
    if weather_fig:
        st.plotly_chart(weather_fig, use_container_width=True, key="exped_weather_chart")
    if day_scores:
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            _metric_card("Best Date", best_date or "N/A", "Optimal departure", CLR_GREEN)
        with mc2:
            _metric_card("Best Day Score", f"{max(d['score'] for d in day_scores):.0f}",
                         "Peak forecast day", CLR_BLUE)
        with mc3:
            if weather_data and "daily" in weather_data:
                t_vals = [v for v in weather_data["daily"].get("temperature_2m_max", [])
                          if v is not None]
                _metric_card("Avg High", f"{_safe_mean(t_vals):.1f} C",
                             "16-day average", CLR_ORANGE)
        with mc4:
            if weather_data and "daily" in weather_data:
                tp = sum(p for p in weather_data["daily"].get("precipitation_sum", [])
                         if p is not None)
                _metric_card("Total Precip", f"{tp:.1f}mm", "16-day cumulative", CLR_CYAN)

    # -- S2: Terrain Difficulty -----------------------------------------------
    _section_header("2.", "Terrain Difficulty", terrain_score, "#c9a66b")
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        _metric_card("Elevation", f"{elevation or 0:.0f} m", terrain_type, "#c9a66b")
    with tc2:
        _metric_card("Max Slope", f"{max_slope:.1f}%", "Across sample grid", CLR_ORANGE)
    with tc3:
        dl = "Easy" if terrain_score > 75 else "Moderate" if terrain_score > 50 else "Hard"
        _metric_card("Difficulty", dl, f"Score: {terrain_score:.0f}/100", CLR_RED)
    profile_fig = _build_terrain_profile_chart(elev_profile)
    if profile_fig:
        st.plotly_chart(profile_fig, use_container_width=True, key="exped_terrain_chart")

    # -- S3-S7: Resource Sections (water, shelter, emergency, comms, supply) ---
    _resource_sections = [
        ("3.", "Water Sources", water_score, CLR_BLUE,
         "Sources Found", water_count, scan_radius, CLR_BLUE,
         "Nearest Water", water_dist, "Distance to closest", CLR_CYAN,
         "Adequate" if water_count > 5 else "Limited" if water_count > 0 else "None",
         "Resupply", "Water availability", CLR_GREEN),
        ("4.", "Shelter Options", shelter_score, CLR_ORANGE,
         "Shelters Found", shelter_count, scan_radius, CLR_ORANGE,
         "Nearest Shelter", shelter_dist, "Distance", CLR_YELLOW,
         "Good" if shelter_count > 3 else "Fair" if shelter_count > 0 else "None",
         "Coverage", "Shelter availability", CLR_GREEN),
        ("5.", "Emergency Services", emergency_score, CLR_RED,
         "Services", emerg_count, "20 km", CLR_RED,
         "Nearest Hospital", emerg_dist, "Distance", CLR_PINK,
         "Good" if emergency_score > 60 else "Limited" if emergency_score > 30 else "Remote",
         "Response", "Emergency access", CLR_ORANGE),
        ("6.", "Communication Coverage", comms_score, CLR_PURPLE,
         "Towers/Masts", comms_count, scan_radius, CLR_PURPLE,
         "Nearest Tower", comms_dist, "Distance", CLR_BLUE,
         "Strong" if comms_score > 70 else "Weak" if comms_score > 30 else "None",
         "Signal", "Estimated coverage", CLR_CYAN),
        ("7.", "Supply Points", supply_score, CLR_GREEN,
         "Supply Points", supply_count, scan_radius, CLR_GREEN,
         "Nearest Supply", supply_dist, "Distance", CLR_YELLOW,
         "Self-sufficient" if supply_score > 60 else "Carry extra" if supply_score > 30 else "Full resupply needed",
         "Logistics", "Supply strategy", CLR_ORANGE),
    ]
    for (num, title, score, clr, c1t, cnt, rng, c1c,
         c2t, dist, c2s, c2c, c3v, c3t, c3s, c3c) in _resource_sections:
        _section_header(num, title, score, clr)
        r1, r2, r3 = st.columns(3)
        with r1:
            _metric_card(c1t, str(cnt), f"Within {rng}", c1c)
        with r2:
            _metric_card(c2t, f"{dist:.1f} km" if dist is not None else "N/A", c2s, c2c)
        with r3:
            _metric_card(c3t, c3v, c3s, c3c)

    # -- S8: Hazard Assessment ------------------------------------------------
    _section_header("8.", "Hazard Assessment", hazard_score, CLR_RED)
    hz1, hz2 = st.columns([2, 1])
    with hz1:
        for h in hazards:
            sc = (CLR_RED if "Seismic" in h or "Extreme" in h
                  else CLR_ORANGE if "Severe" in h or "High" in h or "Heavy" in h
                  else CLR_YELLOW)
            st.markdown(
                f'<div style="background:{CLR_CARD};border-left:3px solid {sc};'
                f'padding:8px 14px;margin-bottom:6px;border-radius:4px;'
                f'color:{CLR_TEXT};font-size:13px;">{h}</div>', unsafe_allow_html=True)
    with hz2:
        thr = "LOW" if hazard_score > 70 else "MODERATE" if hazard_score > 45 else "HIGH"
        tc = CLR_GREEN if hazard_score > 70 else CLR_ORANGE if hazard_score > 45 else CLR_RED
        _metric_card("Threat Level", thr, f"Score: {hazard_score:.0f}/100", tc)

    # -- Risk Briefing --------------------------------------------------------
    st.markdown("---")
    st.markdown("### Risk Briefing")
    briefing = _build_risk_briefing(hazards, weather_score, terrain_score,
                                    emergency_score, comms_score, mission_type)
    st.markdown(
        f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};'
        f'border-radius:8px;padding:18px 22px;font-size:13px;color:{CLR_TEXT};'
        f'white-space:pre-wrap;">{briefing}</div>', unsafe_allow_html=True)

    # -- Equipment Checklist --------------------------------------------------
    st.markdown("---")
    st.markdown("### Equipment Checklist")
    st.caption("Auto-generated based on weather, terrain, and mission type")
    equipment = _generate_equipment(mission_type, terrain_type, weather_data, elevation)
    eq_cols = st.columns(min(len(equipment), 3))
    for idx, (category, eq_items) in enumerate(equipment):
        with eq_cols[idx % len(eq_cols)]:
            items_html = "".join(
                f'<div style="padding:3px 0;color:{CLR_TEXT};font-size:12px;">'
                f'&#9744; {item}</div>' for item in eq_items)
            st.markdown(
                f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};'
                f'border-radius:8px;padding:12px 16px;margin-bottom:10px;">'
                f'<div style="color:{CLR_ACCENT};font-size:13px;font-weight:600;'
                f'margin-bottom:6px;">{category}</div>{items_html}</div>',
                unsafe_allow_html=True)

    # -- Folium Map -----------------------------------------------------------
    st.markdown("---")
    st.markdown("### Expedition Map -- Key Waypoints")
    exp_map = _build_expedition_map(lat, lon, water_data, shelter_data,
                                    emergency_data, comms_data, supply_data,
                                    earthquake_data)
    if exp_map is not None:
        try:
            from streamlit_folium import st_folium
            st_folium(exp_map, width=None, height=520, key="exped_folium_map")
        except ImportError:
            st.components.v1.html(exp_map._repr_html_(), height=520, scrolling=True)
    else:
        st.warning("Folium is not installed. Install with: `pip install folium`")

    # -- Summary Table --------------------------------------------------------
    st.markdown("---")
    st.markdown("### Score Summary")
    icons_map = {"Weather": ("1", CLR_BLUE), "Terrain": ("2", "#c9a66b"),
                 "Water": ("3", CLR_BLUE), "Shelter": ("4", CLR_ORANGE),
                 "Emergency": ("5", CLR_RED), "Comms": ("6", CLR_PURPLE),
                 "Supply": ("7", CLR_GREEN), "Hazards": ("8", CLR_RED)}
    rows = ""
    for name, sv in section_scores.items():
        num, clr = icons_map.get(name, ("?", CLR_TEXT))
        bc = CLR_GREEN if sv > 70 else CLR_YELLOW if sv > 45 else CLR_RED
        rows += (f'<tr><td style="padding:6px 10px;color:{clr};font-weight:600;">{num}. {name}</td>'
                 f'<td style="padding:6px 10px;color:{CLR_TEXT};text-align:right;">{sv:.0f}/100</td>'
                 f'<td style="padding:6px 10px;width:40%;"><div style="background:{CLR_BORDER};'
                 f'border-radius:4px;height:14px;overflow:hidden;"><div style="width:{max(2, sv)}%;'
                 f'background:{bc};height:100%;border-radius:4px;"></div></div></td></tr>')
    th = f'<th style="padding:8px 10px;color:{CLR_TEXT_SEC};font-size:12px;'
    st.markdown(
        f'<table style="width:100%;border-collapse:collapse;background:{CLR_CARD};'
        f'border-radius:8px;overflow:hidden;"><thead><tr style="border-bottom:1px solid '
        f'{CLR_BORDER};">{th}text-align:left;">Section</th>{th}text-align:right;">Score</th>'
        f'{th}text-align:left;">Rating</th></tr></thead><tbody>{rows}'
        f'<tr style="border-top:2px solid {CLR_BORDER};">'
        f'<td style="padding:8px 10px;color:{label_color};font-weight:700;">OVERALL</td>'
        f'<td style="padding:8px 10px;color:{label_color};font-weight:700;text-align:right;">'
        f'{overall_score:.0f}/100</td><td style="padding:8px 10px;color:{label_color};'
        f'font-weight:700;">{label}</td></tr></tbody></table>', unsafe_allow_html=True)

    st.caption("Scores reflect data availability and real-time conditions. "
               "Always validate with local intelligence before deployment.")
