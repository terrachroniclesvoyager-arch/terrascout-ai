"""
Fire Weather Index module for TerraScout AI.
Real-time and forecast fire danger assessment using weather, fuel load,
terrain analysis and suppression difficulty scoring.
Uses Open-Meteo, Open Topo Data, and Overpass (OSM) APIs -- all free, no keys.
"""

import math
import logging
from datetime import datetime, timedelta

import streamlit as st
import requests
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call
except ImportError:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────
FIRE_DANGER_LEVELS = [
    (0, 2, "LOW", "#22c55e"), (2, 4, "MODERATE", "#eab308"),
    (4, 6, "HIGH", "#f97316"), (6, 8, "VERY HIGH", "#ef4444"),
    (8, 10, "EXTREME", "#991b1b"),
]
OPEN_METEO = "https://api.open-meteo.com/v1/forecast"
OPEN_TOPO = "https://api.opentopodata.org/v1/srtm30m"
OVERPASS = "https://overpass-api.de/api/interpreter"
C_BG, C_CARD, C_BD, C_TX, C_MU = "#1a1a2e", "#16213e", "#2a3550", "#e8ecf4", "#8b97b0"


def _clamp(v, lo=0.0, hi=10.0):
    return max(lo, min(hi, v))


def _danger(score):
    """Return (label, color) for a fire danger score 0-10."""
    for lo, hi, lbl, clr in FIRE_DANGER_LEVELS:
        if lo <= score < hi:
            return lbl, clr
    return "EXTREME", "#991b1b"


def _badge(label, value, color="#38bdf8"):
    return (f'<span style="display:inline-block;background:{color}22;border:1px solid {color};'
            f'border-radius:6px;padding:3px 10px;margin:2px 4px;font-size:.88rem;">'
            f'<b style="color:{color};">{value}</b> '
            f'<span style="color:{C_MU};">{label}</span></span>')


def _card(title, body, bc=C_BD):
    st.markdown(
        f'<div style="background:{C_CARD};border:1px solid {bc};border-radius:10px;'
        f'padding:16px 20px;margin-bottom:14px;">'
        f'<div style="font-weight:700;font-size:1.05rem;color:{C_TX};margin-bottom:8px;">'
        f'{title}</div><div style="color:{C_MU};font-size:.92rem;line-height:1.5;">'
        f'{body}</div></div>', unsafe_allow_html=True)


def _haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ── API Functions (cached, timeout=10, try/except) ───────────────────────────

@st.cache_data(ttl=900)
def _fetch_current(lat: float, lon: float) -> dict:
    """Fetch current weather conditions from Open-Meteo."""
    try:
        r = requests.get(OPEN_METEO, params={
            "latitude": lat, "longitude": lon, "timezone": "auto",
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,wind_gusts_10m,precipitation",
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Current weather failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_forecast(lat: float, lon: float) -> dict:
    """Fetch 7-day daily forecast from Open-Meteo."""
    try:
        r = requests.get(OPEN_METEO, params={
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 7,
            "daily": "temperature_2m_max,relative_humidity_2m_min,wind_speed_10m_max,precipitation_sum",
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Forecast failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_drought(lat: float, lon: float) -> dict:
    """Fetch 30-day past precipitation and temperature for drought code."""
    try:
        r = requests.get(OPEN_METEO, params={
            "latitude": lat, "longitude": lon, "timezone": "auto",
            "daily": "precipitation_sum,temperature_2m_max", "past_days": 30, "forecast_days": 0,
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Drought data failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_vegetation(lat: float, lon: float) -> dict:
    """Fetch vegetation / fuel load features from Overpass API (5 km radius)."""
    q = (f'[out:json][timeout:10];(way["natural"~"wood|scrub|heath|grassland"]'
         f'(around:5000,{lat},{lon});way["landuse"="forest"](around:5000,{lat},{lon}););'
         f'out count;out body qt 200;')
    try:
        r = requests.post(OVERPASS, data={"data": q}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Vegetation failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_terrain(lat: float, lon: float) -> dict:
    """Fetch 5-point elevation for slope/aspect computation."""
    off = 0.005
    pts = [(lat, lon), (lat + off, lon), (lat - off, lon), (lat, lon + off), (lat, lon - off)]
    locs = "|".join(f"{p[0]},{p[1]}" for p in pts)
    try:
        r = requests.get(OPEN_TOPO, params={"locations": locs}, timeout=10)
        r.raise_for_status()
        d = r.json()
        return {"results": d["results"]} if d.get("status") == "OK" else {"error": "non-OK"}
    except Exception as e:
        logger.warning("Terrain failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_suppression(lat: float, lon: float) -> dict:
    """Fetch fire stations, water sources, road access near location."""
    q = (f'[out:json][timeout:10];('
         f'node["amenity"="fire_station"](around:15000,{lat},{lon});'
         f'way["amenity"="fire_station"](around:15000,{lat},{lon});'
         f'node["natural"="water"](around:5000,{lat},{lon});'
         f'way["natural"="water"](around:5000,{lat},{lon});'
         f'node["water"~"lake|pond|reservoir"](around:5000,{lat},{lon});'
         f'way["water"~"lake|pond|reservoir"](around:5000,{lat},{lon});'
         f'way["waterway"~"river|stream|canal"](around:3000,{lat},{lon});'
         f'way["highway"~"primary|secondary|tertiary|track"](around:2000,{lat},{lon});'
         f');out center qt 300;')
    try:
        r = requests.post(OVERPASS, data={"data": q}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Suppression failed: %s", e)
        return {"error": str(e)}


# ── Compute Helpers ──────────────────────────────────────────────────────────

def _calc_fwi(temp, humidity, wind, precip):
    """Compute simplified Fire Weather Index from conditions (0-10)."""
    # Temperature factor 0-3
    if temp >= 40:      tf = 3.0
    elif temp >= 30:    tf = 1.5 + 1.5 * (temp - 30) / 10
    elif temp >= 20:    tf = 0.5 + (temp - 20) / 10
    else:               tf = max(0, temp / 40)
    # Dryness factor 0-3
    df = 3.0 * (100 - humidity) / 100
    # Wind factor 0-2.5
    if wind >= 60:      wf = 2.5
    elif wind >= 30:    wf = 1.5 + (wind - 30) / 30
    else:               wf = wind / 20
    # Precipitation dampening
    pd = 0.2 if precip > 5 else 0.5 if precip > 1 else 0.8 if precip > 0 else 1.0
    return _clamp((tf + df + wf) * pd * 10 / 8.5)


def _daily_fwi(t, rh, w, p):
    """Compute daily FWI from daily aggregates."""
    t, rh, w, p = t or 20, rh or 50, w or 10, p or 0
    tf = min(3.0, max(0, (t - 10) / 10))
    df = 3.0 * (100 - rh) / 100
    wf = min(2.5, w / 24)
    dr = 1.0 if p < 0.5 else max(0.15, 1.0 - p / 20)
    return _clamp((tf + df + wf) * dr * 10 / 8.5)


def _calc_drought(daily: dict) -> dict:
    """Compute drought severity from 30-day precipitation history."""
    prec = daily.get("precipitation_sum", [])
    tmps = daily.get("temperature_2m_max", [])
    total = sum(p for p in prec if p is not None)
    avg_t = sum(t for t in tmps if t is not None) / max(1, len(tmps)) if tmps else 20
    days = len(prec)
    expected = days * 2.5
    deficit = max(0, expected - total)
    dpct = min(100, deficit / max(1, expected) * 100)
    score = _clamp(dpct / 10)
    if avg_t > 30:      score = _clamp(score * 1.3)
    elif avg_t > 25:    score = _clamp(score * 1.15)
    dry_d = sum(1 for p in prec if p is not None and p < 0.5)
    return {"score": round(score, 1), "total_mm": round(total, 1),
            "expected_mm": round(expected, 1), "deficit_mm": round(deficit, 1),
            "deficit_pct": round(dpct, 1), "avg_temp": round(avg_t, 1),
            "dry_days": dry_d, "total_days": days}


def _calc_slope(terrain: dict) -> dict:
    """Compute slope and aspect from 5-point elevation samples."""
    res = terrain.get("results", [])
    if len(res) < 5:
        return {"slope_deg": 0, "aspect": "Flat", "elev_m": 0, "risk_score": 0}
    e = [r.get("elevation", 0) or 0 for r in res]
    center, north, south, east, west = e
    dz_ns, dz_ew = north - south, east - west
    slope = math.degrees(math.atan(math.sqrt(dz_ns**2 + dz_ew**2) / 1000))
    if dz_ns == 0 and dz_ew == 0:
        aspect = "Flat"
    else:
        ad = (math.degrees(math.atan2(dz_ew, dz_ns)) + 360) % 360
        aspect = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((ad + 22.5) / 45) % 8]
    sf = min(4.0, slope / 10)
    ab = 1.5 if aspect in ("S", "SE", "SW") else 0.5 if aspect in ("E", "W") else 0
    risk = _clamp(sf + ab + center / 2000)
    return {"slope_deg": round(slope, 1), "aspect": aspect,
            "elev_m": round(center, 0), "risk_score": round(risk, 1)}


def _calc_vegetation(data: dict) -> dict:
    """Analyze vegetation fuel load from Overpass response."""
    if "error" in data:
        return {"score": 0, "total": 0, "forest": 0, "scrub": 0, "grass": 0}
    els = data.get("elements", [])
    f = s = g = o = 0
    for el in els:
        tags = el.get("tags", {})
        nat, lu = tags.get("natural", ""), tags.get("landuse", "")
        if lu == "forest" or nat == "wood":  f += 1
        elif nat in ("scrub", "heath"):      s += 1
        elif nat == "grassland":             g += 1
        else:                                o += 1
    tot = f + s + g + o
    sc = 1.0 if tot == 0 else _clamp(
        (f * 2.0 + s * 2.5 + g * 1.2 + o * 0.8) / max(1, tot) * min(3, tot / 10 + 1))
    return {"score": round(sc, 1), "total": tot, "forest": f, "scrub": s, "grass": g}


def _calc_suppression(data: dict, lat: float, lon: float) -> dict:
    """Analyze suppression resources and compute difficulty score."""
    empty = {"score": 8.0, "stations": 0, "water_sources": 0, "roads": 0,
             "nearest_km": None, "stn_coords": [], "wat_coords": []}
    if "error" in data:
        return empty
    stns, wats, roads = [], [], 0
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        elat = el.get("lat") or (el.get("center") or {}).get("lat")
        elon = el.get("lon") or (el.get("center") or {}).get("lon")
        if tags.get("amenity") == "fire_station" and elat is not None and elon is not None:
            stns.append({"lat": elat, "lon": elon,
                         "dist_km": _haversine(lat, lon, elat, elon),
                         "name": tags.get("name", "Fire Station")})
        elif (tags.get("natural") == "water" or tags.get("water") or tags.get("waterway")) and elat is not None and elon is not None:
            wats.append({"lat": elat, "lon": elon})
        elif tags.get("highway"):
            roads += 1
    stns.sort(key=lambda s: s["dist_km"])
    nk = stns[0]["dist_km"] if stns else None
    sf = 4.0 if not stns else min(4.0, nk / 5)
    wf = 3.0 if not wats else max(0.5, 3.0 - len(wats) * 0.3)
    rf = 3.0 if roads == 0 else max(0.5, 3.0 - roads * 0.05)
    return {"score": round(_clamp(sf + wf + rf), 1), "stations": len(stns),
            "water_sources": len(wats), "roads": roads,
            "nearest_km": round(nk, 1) if nk else None,
            "stn_coords": stns[:10], "wat_coords": wats[:30]}


# ── Rendering ────────────────────────────────────────────────────────────────

def _render_gauge(score):
    lbl, clr = _danger(score)
    pct = score / 10 * 100
    st.markdown(
        f'<div style="background:{C_CARD};border:1px solid {C_BD};border-radius:12px;'
        f'padding:18px 22px;margin-bottom:16px;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;'
        f'margin-bottom:10px;"><span style="font-size:1.1rem;font-weight:700;color:{C_TX};">'
        f'Overall Fire Danger</span><span style="font-size:1.4rem;font-weight:800;color:{clr};'
        f'text-shadow:0 0 8px {clr}66;">{lbl}</span></div>'
        f'<div style="position:relative;height:22px;border-radius:11px;'
        f'background:linear-gradient(to right,#22c55e,#eab308,#f97316,#ef4444,#991b1b);'
        f'overflow:hidden;"><div style="position:absolute;left:{pct}%;top:-2px;width:4px;'
        f'height:26px;background:white;border-radius:2px;'
        f'box-shadow:0 0 6px rgba(255,255,255,.8);"></div></div>'
        f'<div style="display:flex;justify-content:space-between;margin-top:4px;'
        f'font-size:.75rem;color:{C_MU};"><span>LOW</span><span>MODERATE</span>'
        f'<span>HIGH</span><span>VERY HIGH</span><span>EXTREME</span></div>'
        f'<div style="text-align:center;margin-top:6px;font-size:1.6rem;'
        f'font-weight:800;color:{clr};">{score:.1f} / 10</div></div>',
        unsafe_allow_html=True)


def _render_forecast(fdata):
    daily = fdata.get("daily", {})
    dates = daily.get("time", [])
    if not dates:
        st.info("No forecast data available.")
        return
    temps = daily.get("temperature_2m_max", [])
    rhs = daily.get("relative_humidity_2m_min", [])
    winds = daily.get("wind_speed_10m_max", [])
    precs = daily.get("precipitation_sum", [])
    n = len(dates)
    scores, colors, labels = [], [], []
    for i in range(n):
        sc = _daily_fwi(temps[i] if i < len(temps) else None, rhs[i] if i < len(rhs) else None,
                        winds[i] if i < len(winds) else None, precs[i] if i < len(precs) else None)
        scores.append(sc)
        _, c = _danger(sc)
        colors.append(c)
        labels.append(dates[i][5:] if dates[i] else "?")

    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor(C_BG)
    ax.set_facecolor(C_BG)
    bands = ["rgba(34,197,94,0.13)", "rgba(234,179,8,0.13)", "rgba(249,115,22,0.13)", "rgba(239,68,68,0.13)", "rgba(153,27,27,0.13)"]
    for idx, (lo, hi, _, _) in enumerate(FIRE_DANGER_LEVELS):
        ax.axhspan(lo, hi, color=bands[idx], zorder=0)
    bars = ax.bar(labels, scores, color=colors, edgecolor="rgba(255,255,255,0.2)", linewidth=.8, zorder=2, width=.65)
    for bar, sc in zip(bars, scores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + .15,
                f"{sc:.1f}", ha="center", va="bottom", fontsize=8, color=C_TX, fontweight="bold")
    ax.set_ylim(0, 10.5)
    ax.set_ylabel("FWI Score", color=C_MU, fontsize=9)
    ax.tick_params(colors=C_MU, labelsize=8)
    for sp in ax.spines.values():
        sp.set_color(C_BD)
    ax.set_title("7-Day Fire Weather Index Forecast", color=C_TX, fontsize=11, fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def _render_drought(dr):
    sc = dr["score"]
    _, clr = _danger(sc)
    badges = (_badge("Rain (30d)", f'{dr["total_mm"]} mm', "#38bdf8")
              + _badge("Expected", f'{dr["expected_mm"]} mm', "#8b97b0")
              + _badge("Deficit", f'{dr["deficit_mm"]} mm', "#ef4444")
              + _badge("Dry days", f'{dr["dry_days"]}/{dr["total_days"]}', "#f59e0b")
              + _badge("Avg Temp", f'{dr["avg_temp"]} C', "#f97316"))
    st.markdown(
        f'<div style="background:{C_CARD};border:1px solid {C_BD};border-radius:10px;'
        f'padding:16px 20px;margin-bottom:14px;">'
        f'<div style="font-weight:700;color:{C_TX};margin-bottom:8px;">'
        f'Drought Severity: <span style="color:{clr};">{sc}/10</span></div>'
        f'<div style="height:14px;background:#1e293b;border-radius:7px;overflow:hidden;">'
        f'<div style="width:{sc / 10 * 100}%;height:100%;'
        f'background:linear-gradient(to right,#eab308,#ef4444,#991b1b);'
        f'border-radius:7px;"></div></div>'
        f'<div style="margin-top:10px;">{badges}</div></div>', unsafe_allow_html=True)


def _render_fuel(veg):
    sc = veg["score"]
    _, clr = _danger(sc)
    segs = ""
    for lbl, cnt, c in [("Forest/Wood", veg["forest"], "#22c55e"),
                         ("Scrub/Heath", veg["scrub"], "#f97316"),
                         ("Grassland", veg["grass"], "#eab308")]:
        segs += (f'<div style="display:flex;justify-content:space-between;margin:3px 0;'
                 f'font-size:.88rem;"><span style="color:{c};">{lbl}</span>'
                 f'<span style="color:{C_TX};font-weight:600;">{cnt} features</span></div>')
    _card(f"Vegetation Fuel Load: <span style='color:{clr};'>{sc}/10</span>",
          f"{_badge('Total (5 km)', str(veg['total']), clr)}<div style='margin-top:8px;'>"
          f"{segs}</div><div style='margin-top:6px;font-size:.82rem;color:{C_MU};'>"
          f"Dense scrub = highest ignition risk. Forest canopy = sustained crown fire.</div>", bc=clr)


def _render_terrain(tr):
    sc = tr["risk_score"]
    _, clr = _danger(sc)
    warn = ""
    if tr["slope_deg"] > 15 and tr["aspect"] in ("S", "SE", "SW"):
        warn = (f'<div style="margin-top:6px;padding:6px 10px;background:#991b1b22;'
                f'border:1px solid #991b1b;border-radius:6px;font-size:.85rem;color:#ef4444;">'
                f'Steep south-facing slope -- extreme fire spread risk. '
                f'Fire doubles speed every 10 deg of slope.</div>')
    _card(f"Terrain Fire Spread Risk: <span style='color:{clr};'>{sc}/10</span>",
          _badge("Slope", f'{tr["slope_deg"]} deg', "#38bdf8")
          + _badge("Aspect", tr["aspect"], "#8b5cf6")
          + _badge("Elevation", f'{int(tr["elev_m"])} m', "#10b981") + warn, bc=clr)


def _render_suppression(supp, lat, lon):
    sc = supp["score"]
    _, clr = _danger(sc)
    nk = f'{supp["nearest_km"]} km' if supp["nearest_km"] else "None found"
    _card(f"Suppression Difficulty: <span style='color:{clr};'>{sc}/10</span>",
          _badge("Stations (15 km)", str(supp["stations"]), "#ef4444")
          + _badge("Nearest", nk, "#f97316")
          + _badge("Water (5 km)", str(supp["water_sources"]), "#38bdf8")
          + _badge("Roads (2 km)", str(supp["roads"]), "#8b97b0")
          + f'<div style="margin-top:6px;font-size:.82rem;color:{C_MU};">'
          f'Higher score = harder suppression. Factors: station distance, water, roads.</div>',
          bc=clr)
    # Folium map with stations and water sources
    if supp["stn_coords"] or supp["wat_coords"]:
        m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB dark_matter")
        folium.Marker([lat, lon], popup="Analysis Point",
                      icon=folium.Icon(color="red", icon="fire", prefix="fa")).add_to(m)
        for s in supp["stn_coords"]:
            folium.Marker([s["lat"], s["lon"]], popup=f'{s["name"]} ({s["dist_km"]:.1f} km)',
                          icon=folium.Icon(color="orange", icon="building", prefix="fa")).add_to(m)
        for w in supp["wat_coords"][:20]:
            folium.CircleMarker([w["lat"], w["lon"]], radius=4, color="#38bdf8",
                                fill=True, fill_opacity=.7, popup="Water source").add_to(m)
        components.html(m._repr_html_(), height=380)


# ── Main Entry Point ─────────────────────────────────────────────────────────

def render_fire_weather_tab():
    """Render the Fire Weather Index tab -- single entry point."""
    st.markdown("## Fire Weather Index")
    st.caption("Real-time & forecast fire danger with fuel, terrain & suppression analysis")

    # Location input
    c1, c2, c3 = st.columns([2, 2, 1])
    with c1:
        lat = st.number_input("Latitude", value=42.35, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="fwi_lat")
    with c2:
        lon = st.number_input("Longitude", value=13.40, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="fwi_lon")
    with c3:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        run = st.button("Analyze Fire Danger", key="fwi_run",
                        type="primary", use_container_width=True)
    if not run:
        st.info("Enter coordinates and click **Analyze Fire Danger** to start.")
        return

    # Fetch all data
    with st.spinner("Fetching weather, terrain, fuel & suppression data..."):
        cur_raw = _fetch_current(lat, lon)
        fcast = _fetch_forecast(lat, lon)
        dro_raw = _fetch_drought(lat, lon)
        veg_raw = _fetch_vegetation(lat, lon)
        ter_raw = _fetch_terrain(lat, lon)
        sup_raw = _fetch_suppression(lat, lon)

    # Compute metrics
    cur = cur_raw.get("current", {}) if "error" not in cur_raw else {}
    cur_fwi = _calc_fwi(cur.get("temperature_2m", 20), cur.get("relative_humidity_2m", 50),
                        cur.get("wind_speed_10m", 10), cur.get("precipitation", 0))
    drought = _calc_drought(dro_raw.get("daily", {}) if "error" not in dro_raw else {})
    veg = _calc_vegetation(veg_raw)
    terrain = _calc_slope(ter_raw) if "error" not in ter_raw else {
        "slope_deg": 0, "aspect": "N/A", "elev_m": 0, "risk_score": 0}
    supp = _calc_suppression(sup_raw, lat, lon)

    # Overall composite score
    overall = _clamp(cur_fwi * 0.35 + drought["score"] * 0.20 + veg["score"] * 0.15
                     + terrain["risk_score"] * 0.15 + supp["score"] * 0.15)

    # ── Section 0: Danger Gauge ──────────────────────────────────────────────
    _render_gauge(overall)

    # ── Section 1: Current Fire Weather ──────────────────────────────────────
    st.markdown("### 1 -- Current Fire Weather Conditions")
    if "error" in cur_raw:
        st.error(f"Weather fetch failed: {cur_raw['error']}")
    else:
        t, rh = cur.get("temperature_2m", "N/A"), cur.get("relative_humidity_2m", "N/A")
        w, g = cur.get("wind_speed_10m", "N/A"), cur.get("wind_gusts_10m", "N/A")
        p = cur.get("precipitation", "N/A")
        cols = st.columns(5)
        cols[0].metric("Temperature", f"{t} C" if t != "N/A" else "N/A")
        cols[1].metric("Humidity", f"{rh}%" if rh != "N/A" else "N/A")
        cols[2].metric("Wind", f"{w} km/h" if w != "N/A" else "N/A")
        cols[3].metric("Gusts", f"{g} km/h" if g != "N/A" else "N/A")
        cols[4].metric("Precipitation", f"{p} mm" if p != "N/A" else "N/A")
        conds = []
        if isinstance(t, (int, float)) and t > 30: conds.append("High temperature")
        if isinstance(rh, (int, float)) and rh < 30: conds.append("Very low humidity")
        if isinstance(w, (int, float)) and w > 30: conds.append("Strong winds")
        if isinstance(p, (int, float)) and p < 0.5: conds.append("No rain")
        _, fc = _danger(cur_fwi)
        note = " + ".join(conds) if conds else "Normal parameters"
        alert = "Elevated fire weather detected." if cur_fwi > 5 else "Within normal range."
        _card(f"Current FWI: <span style='color:{fc};'>{cur_fwi:.1f}/10</span>",
              f"Conditions: {note}<br>{alert}", bc=fc)

    # ── Section 2: 7-Day Forecast ────────────────────────────────────────────
    st.markdown("### 2 -- 7-Day Fire Danger Forecast")
    if "error" in fcast:
        st.error(f"Forecast failed: {fcast['error']}")
    else:
        _render_forecast(fcast)
        with st.expander("Daily breakdown", expanded=False):
            d = fcast.get("daily", {})
            for i, dt in enumerate(d.get("time", [])):
                sc = _daily_fwi(
                    d.get("temperature_2m_max", [None])[i] if i < len(d.get("temperature_2m_max", [])) else None,
                    d.get("relative_humidity_2m_min", [None])[i] if i < len(d.get("relative_humidity_2m_min", [])) else None,
                    d.get("wind_speed_10m_max", [None])[i] if i < len(d.get("wind_speed_10m_max", [])) else None,
                    d.get("precipitation_sum", [None])[i] if i < len(d.get("precipitation_sum", [])) else None)
                lb, cl = _danger(sc)
                st.markdown(f"**{dt}** -- FWI **{sc:.1f}** "
                            f"<span style='color:{cl};font-weight:700;'>[{lb}]</span>",
                            unsafe_allow_html=True)

    # ── Section 3: Drought Code ──────────────────────────────────────────────
    st.markdown("### 3 -- Drought Code (30-Day)")
    if "error" in dro_raw:
        st.error(f"Drought data failed: {dro_raw['error']}")
    else:
        _render_drought(drought)

    # ── Section 4: Vegetation Fuel Load ──────────────────────────────────────
    st.markdown("### 4 -- Vegetation Fuel Load")
    _render_fuel(veg)

    # ── Section 5: Terrain Fire Spread Risk ──────────────────────────────────
    st.markdown("### 5 -- Terrain Fire Spread Risk")
    _render_terrain(terrain)

    # ── Section 6: Suppression Difficulty ────────────────────────────────────
    st.markdown("### 6 -- Suppression Difficulty")
    _render_suppression(supp, lat, lon)

    # ── Composite Summary Table ──────────────────────────────────────────────
    st.markdown("### Composite Score Breakdown")
    rows = ""
    for name, sc, wt in [("Current Fire Weather", cur_fwi, 0.35),
                          ("Drought Code", drought["score"], 0.20),
                          ("Vegetation Fuel Load", veg["score"], 0.15),
                          ("Terrain Spread Risk", terrain["risk_score"], 0.15),
                          ("Suppression Difficulty", supp["score"], 0.15)]:
        _, cl = _danger(sc)
        rows += (f'<tr style="border-bottom:1px solid {C_BD};">'
                 f'<td style="padding:8px 12px;color:{C_TX};">{name}</td>'
                 f'<td style="padding:8px 12px;text-align:center;">'
                 f'<span style="color:{cl};font-weight:700;">{sc:.1f}</span></td>'
                 f'<td style="padding:8px 12px;text-align:center;color:{C_MU};">{wt:.0%}</td>'
                 f'<td style="padding:8px 12px;text-align:center;color:{cl};'
                 f'font-weight:600;">{sc * wt:.2f}</td></tr>')
    _, oc = _danger(overall)
    st.markdown(
        f'<div style="background:{C_CARD};border:1px solid {C_BD};border-radius:10px;'
        f'overflow:hidden;margin-bottom:16px;"><table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:{C_BG};">'
        f'<th style="padding:10px 12px;text-align:left;color:{C_MU};font-size:.85rem;">Component</th>'
        f'<th style="padding:10px 12px;text-align:center;color:{C_MU};font-size:.85rem;">Score</th>'
        f'<th style="padding:10px 12px;text-align:center;color:{C_MU};font-size:.85rem;">Weight</th>'
        f'<th style="padding:10px 12px;text-align:center;color:{C_MU};font-size:.85rem;">Weighted</th>'
        f'</tr></thead><tbody>{rows}'
        f'<tr style="background:{C_BG};"><td style="padding:10px 12px;color:{C_TX};'
        f'font-weight:700;" colspan="3">OVERALL FIRE DANGER</td>'
        f'<td style="padding:10px 12px;text-align:center;font-size:1.2rem;'
        f'font-weight:800;color:{oc};">{overall:.1f}</td></tr>'
        f'</tbody></table></div>', unsafe_allow_html=True)

    # Final advisory
    lbl, clr = _danger(overall)
    advisories = {8: "EXTREME fire danger. All outdoor burning prohibited. "
                     "Evacuations may be ordered. Pre-position suppression resources.",
                  6: "VERY HIGH fire danger. Avoid all ignition sources. "
                     "Fire services on heightened alert. Monitor closely.",
                  4: "HIGH fire danger. Outdoor burning discouraged. "
                     "Maintain fire breaks. Have evacuation plans ready.",
                  2: "MODERATE fire danger. Exercise caution with open flames. "
                     "Standard fire safety protocols in effect.",
                  0: "LOW fire danger. Conditions favorable. "
                     "Normal activities may proceed with standard precautions."}
    adv = next(v for k, v in sorted(advisories.items(), reverse=True) if overall >= k)
    st.markdown(
        f'<div style="background:{clr}15;border:2px solid {clr};border-radius:10px;'
        f'padding:16px 20px;margin-top:8px;">'
        f'<div style="font-weight:700;font-size:1.1rem;color:{clr};margin-bottom:6px;">'
        f'Advisory: {lbl}</div>'
        f'<div style="color:{C_TX};font-size:.95rem;">{adv}</div></div>',
        unsafe_allow_html=True)
