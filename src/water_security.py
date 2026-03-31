"""
Water Security & Access AI module for TerraScout AI.
Comprehensive water availability, quality risk, and access assessment
using 7 scoring dimensions across multiple free APIs:
  - Overpass API (OSM water features, infrastructure, contamination sources)
  - ISRIC SoilGrids v2.0 (soil permeability via sand content)
  - Open-Meteo (precipitation, evapotranspiration, temperature)
  - Open Topo Data (elevation / slope for drainage)
All free, no API key required.
"""

import io, json, math
import streamlit as st
import requests
import pandas as pd
from html import escape
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
import numpy as np

# ═══════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
SOILGRIDS_API = "https://rest.isric.org/soilgrids/v2.0/properties/query"
OPEN_METEO_API = "https://api.open-meteo.com/v1/forecast"
OPEN_TOPO_API = "https://api.opentopodata.org/v1/srtm30m"

CLR_BG, CLR_CARD, CLR_BORDER = "#0a0e1a", "#1a2235", "#2a3550"
CLR_TEXT, CLR_TEXT_SEC = "#e8ecf4", "#8b97b0"
CLR_ACCENT, CLR_WATER = "#06b6d4", "#3b82f6"
CLR_SAFE, CLR_WARN, CLR_DANGER = "#22c55e", "#f59e0b", "#ef4444"
CLR_PRECIP, CLR_EVAP = "#8b5cf6", "#f97316"

WATER_PRESETS = {
    "Custom": None,
    "Lake Garda, Italy": {"lat": 45.60, "lon": 10.65},
    "Sahara - Southern Algeria": {"lat": 27.0, "lon": 2.0},
    "Amazon Basin, Brazil": {"lat": -3.12, "lon": -60.02},
    "Maldives - Male": {"lat": 4.17, "lon": 73.51},
    "Nile Delta, Egypt": {"lat": 30.9, "lon": 31.2},
    "Cape Town, South Africa": {"lat": -33.93, "lon": 18.42},
    "Rajasthan, India": {"lat": 26.9, "lon": 70.9},
    "Amsterdam, Netherlands": {"lat": 52.37, "lon": 4.90},
    "Atacama Desert, Chile": {"lat": -24.5, "lon": -69.25},
    "Swiss Alps - Interlaken": {"lat": 46.69, "lon": 7.86},
    "Australian Outback": {"lat": -25.0, "lon": 134.0},
    "Venice Lagoon, Italy": {"lat": 45.44, "lon": 12.33},
}

DIM_NAMES = ["Surface Water", "Groundwater", "Precip Balance",
             "Infrastructure", "Contamination", "Drought Vuln.", "Flood Drainage"]
DIM_LABELS = [
    "1. Surface Water Access", "2. Groundwater Indicators",
    "3. Precipitation Balance", "4. Water Infrastructure",
    "5. Contamination Risk", "6. Drought Vulnerability", "7. Flood Drainage",
]
DIM_WEIGHTS = [0.20, 0.15, 0.20, 0.15, 0.10, 0.10, 0.10]


def _classify(score):
    if score >= 8: return "SECURE", CLR_SAFE, "Abundant water resources with strong infrastructure"
    if score >= 6: return "ADEQUATE", "#4ade80", "Sufficient water access with minor concerns"
    if score >= 4: return "STRESSED", CLR_WARN, "Water availability under pressure, risks present"
    if score >= 2: return "SCARCE", "#f97316", "Limited water resources, significant vulnerability"
    return "CRITICAL", CLR_DANGER, "Severe water scarcity, urgent risk"


def _clamp(v, lo=0, hi=10):
    return max(lo, min(hi, v))


def _bbox_str(lat, lon, radius_m):
    d = radius_m / 111320.0
    return f"{lat - d},{lon - d},{lat + d},{lon + d}"


def _haversine(lat1, lon1, lat2, lon2):
    R, p = 6371000, math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2 +
         math.cos(lat1 * p) * math.cos(lat2 * p) *
         math.sin((lon2 - lon1) * p / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))


def _element_coords(el):
    if "lat" in el and "lon" in el:
        return el["lat"], el["lon"]
    c = el.get("center", {})
    return (c.get("lat"), c.get("lon")) if c else (None, None)


def _parse_soil(soil):
    """Parse SoilGrids v2.0 response with correct nested structure."""
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
    return _sv


# ═══════════════════════════════════════════
# DATA FETCHING (all cached, all with timeout)
# ═══════════════════════════════════════════
@st.cache_data(ttl=900)
def _fetch_overpass(query_body: str) -> dict:
    full = f"[out:json][timeout:15];{query_body}out center;"
    try:
        r = requests.post(OVERPASS_URL, data={"data": full}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "elements": []}


@st.cache_data(ttl=900)
def _fetch_surface_water(lat: float, lon: float, radius: int = 5000) -> dict:
    bb = _bbox_str(lat, lon, radius)
    q = (f'(way["waterway"~"river|stream"]({bb});way["natural"="water"]({bb});'
         f'relation["natural"="water"]({bb});way["water"~"reservoir|pond|lake"]({bb});'
         f'node["natural"="spring"]({bb}););')
    return _fetch_overpass(q)


@st.cache_data(ttl=900)
def _fetch_groundwater(lat: float, lon: float, radius: int = 5000) -> dict:
    bb = _bbox_str(lat, lon, radius)
    q = (f'(node["man_made"="water_well"]({bb});node["natural"="spring"]({bb});'
         f'node["man_made"="borehole"]({bb});'
         f'node["man_made"="monitoring_station"]["monitoring:groundwater"="yes"]({bb}););')
    return _fetch_overpass(q)


@st.cache_data(ttl=900)
def _fetch_infrastructure(lat: float, lon: float, radius: int = 5000) -> dict:
    bb = _bbox_str(lat, lon, radius)
    q = (f'(node["man_made"="water_tower"]({bb});way["man_made"="water_tower"]({bb});'
         f'node["man_made"="water_works"]({bb});way["man_made"="water_works"]({bb});'
         f'node["amenity"="drinking_water"]({bb});node["man_made"="water_tap"]({bb});'
         f'way["man_made"="pipeline"]["substance"="water"]({bb}););')
    return _fetch_overpass(q)


@st.cache_data(ttl=900)
def _fetch_contamination(lat: float, lon: float, radius: int = 5000) -> dict:
    bb = _bbox_str(lat, lon, radius)
    q = (f'(node["landuse"="industrial"]({bb});way["landuse"="industrial"]({bb});'
         f'node["landuse"="landfill"]({bb});way["landuse"="landfill"]({bb});'
         f'node["man_made"="wastewater_plant"]({bb});way["man_made"="wastewater_plant"]({bb});'
         f'node["man_made"="sewage"]({bb});way["industrial"~"chemical|oil|refinery"]({bb}););')
    return _fetch_overpass(q)


@st.cache_data(ttl=900)
def _fetch_soilgrids(lat: float, lon: float) -> dict:
    try:
        r = requests.get(SOILGRIDS_API, params={
            "lon": lon, "lat": lat, "property": ["sand", "clay", "silt"],
            "depth": ["0-5cm", "5-15cm", "15-30cm"], "value": "mean"}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_weather(lat: float, lon: float) -> dict:
    url = (f"{OPEN_METEO_API}?latitude={lat}&longitude={lon}"
           f"&daily=precipitation_sum,et0_fao_evapotranspiration,temperature_2m_max"
           f"&past_days=30&timezone=auto")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_elevation(lat: float, lon: float) -> dict:
    offsets = [(0, 0), (0.001, 0), (-0.001, 0), (0, 0.001), (0, -0.001)]
    locs = "|".join(f"{lat+dy},{lon+dx}" for dy, dx in offsets)
    try:
        r = requests.get(f"{OPEN_TOPO_API}?locations={locs}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════
# DIMENSION SCORING (each returns 0-10 + details dict)
# ═══════════════════════════════════════════
def _score_surface_water(data, lat, lon):
    elements = data.get("elements", [])
    count = len(elements)
    if count == 0:
        return 0.0, {"count": 0, "nearest_m": None}
    nearest = float("inf")
    for el in elements:
        elat, elon = _element_coords(el)
        if elat is not None:
            nearest = min(nearest, _haversine(lat, lon, elat, elon))
    prox = _clamp(10 - (nearest / 500), 0, 5)
    abund = _clamp(count / 4, 0, 5)
    return _clamp(prox + abund), {"count": count, "nearest_m": round(nearest, 0)}


def _score_groundwater(gw_data, soil_sv, lat, lon):
    elements = gw_data.get("elements", [])
    well_count = len(elements)
    well_sc = _clamp(well_count * 1.5, 0, 5)
    sand = soil_sv("sand") if soil_sv else None
    perm_sc = _clamp(sand / 15, 0, 5) if sand is not None else 2.5
    return _clamp(well_sc + perm_sc), {"wells": well_count,
                                        "sand_pct": round(sand, 1) if sand else None}


def _score_precip_balance(weather):
    daily = weather.get("daily", {})
    precip_list = daily.get("precipitation_sum", [])
    et_list = daily.get("et0_fao_evapotranspiration", [])
    if not precip_list:
        return 5.0, {"total_precip_mm": None, "total_et_mm": None, "balance_mm": None}
    total_p = sum(v for v in precip_list if v is not None)
    total_et = sum(v for v in et_list if v is not None) if et_list else 0
    balance = total_p - total_et
    ratio = total_p / total_et if total_et > 0 else 2.0
    return _clamp(ratio * 5, 0, 10), {
        "total_precip_mm": round(total_p, 1), "total_et_mm": round(total_et, 1),
        "balance_mm": round(balance, 1), "ratio": round(ratio, 2),
        "daily_precip": precip_list, "daily_et": et_list,
        "dates": daily.get("time", []),
    }


def _score_infrastructure(data):
    elements = data.get("elements", [])
    count = len(elements)
    towers = sum(1 for e in elements if "water_tower" in str(e.get("tags", {})))
    works = sum(1 for e in elements if "water_works" in str(e.get("tags", {})))
    drinking = sum(1 for e in elements
                   if e.get("tags", {}).get("amenity") == "drinking_water"
                   or "water_tap" in str(e.get("tags", {})))
    sc = _clamp(towers * 2 + works * 3 + drinking * 0.5 + count * 0.3, 0, 10)
    return sc, {"total": count, "towers": towers, "works": works,
                "drinking_points": drinking}


def _score_contamination(data):
    elements = data.get("elements", [])
    count = len(elements)
    industrial = sum(1 for e in elements
                     if e.get("tags", {}).get("landuse") == "industrial"
                     or "chemical" in str(e.get("tags", {}))
                     or "refinery" in str(e.get("tags", {})))
    landfills = sum(1 for e in elements if e.get("tags", {}).get("landuse") == "landfill")
    sewage = sum(1 for e in elements
                 if "wastewater" in str(e.get("tags", {}))
                 or "sewage" in str(e.get("tags", {})))
    risk = industrial * 2 + landfills * 3 + sewage * 1.5
    return _clamp(10 - risk, 0, 10), {"total_sources": count, "industrial": industrial,
                                       "landfills": landfills, "sewage": sewage}


def _score_drought(weather, soil_sv):
    daily = weather.get("daily", {})
    precip_list = daily.get("precipitation_sum", [])
    temp_list = daily.get("temperature_2m_max", [])
    total_p = sum(v for v in precip_list if v is not None) if precip_list else 0
    valid_temps = [v for v in (temp_list or []) if v is not None]
    avg_temp = sum(valid_temps) / max(len(valid_temps), 1) if valid_temps else 20
    sand = soil_sv("sand") if soil_sv else None
    sand_val = sand if sand is not None else 30
    dry = max(0, 1 - total_p / 60)
    heat = max(0, (avg_temp - 20) / 25)
    perm = max(0, sand_val / 100)
    drought_risk = (dry * 0.5 + heat * 0.3 + perm * 0.2) * 10
    return _clamp(10 - drought_risk, 0, 10), {
        "30d_precip_mm": round(total_p, 1), "avg_max_temp_c": round(avg_temp, 1),
        "sand_pct": round(sand_val, 1), "drought_risk_raw": round(drought_risk, 1)}


def _score_flood_drainage(elev_data, soil_sv):
    results = elev_data.get("results", [])
    slope_deg, center_elev = 0, None
    if len(results) >= 5:
        elevs = [r.get("elevation") for r in results if r.get("elevation") is not None]
        if len(elevs) >= 3:
            center_elev = elevs[0]
            avg_diff = sum(abs(e - center_elev) for e in elevs[1:]) / len(elevs[1:])
            slope_deg = math.degrees(math.atan2(avg_diff, 111))
    slope_sc = _clamp(slope_deg / 3, 0, 5)
    sand = soil_sv("sand") if soil_sv else None
    sand_val = sand if sand is not None else 30
    perm_sc = _clamp(sand_val / 20, 0, 5)
    return _clamp(slope_sc + perm_sc), {
        "slope_deg": round(slope_deg, 2),
        "elevation_m": round(center_elev, 1) if center_elev else None,
        "sand_pct": round(sand_val, 1)}


# ═══════════════════════════════════════════
# VISUALIZATION HELPERS
# ═══════════════════════════════════════════
def _render_gauge(score, label, width=220):
    cls_name, cls_clr, cls_desc = _classify(score)
    pct = score / 10 * 100
    dash = 2 * math.pi * 54
    filled = dash * pct / 100
    return f"""<div style="text-align:center;padding:10px">
      <svg width="{width}" height="{width}" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r="54" fill="none" stroke="#2a3550" stroke-width="8"/>
        <circle cx="60" cy="60" r="54" fill="none" stroke="{cls_clr}" stroke-width="8"
          stroke-dasharray="{filled:.1f} {dash:.1f}"
          stroke-linecap="round" transform="rotate(-90 60 60)"/>
        <text x="60" y="55" text-anchor="middle" fill="{cls_clr}"
          font-size="24" font-weight="bold">{score:.1f}</text>
        <text x="60" y="72" text-anchor="middle" fill="{CLR_TEXT_SEC}"
          font-size="9">{cls_name}</text>
      </svg>
      <div style="color:{CLR_TEXT};font-size:13px;font-weight:600">{label}</div>
      <div style="color:{CLR_TEXT_SEC};font-size:11px;margin-top:2px">{cls_desc}</div>
    </div>"""


def _render_metric_card(title, score, details):
    _, clr, _ = _classify(score)
    bar_w = score / 10 * 100
    det = "".join(f"<div style='color:{CLR_TEXT_SEC};font-size:11px'>"
                  f"<b>{escape(str(k))}:</b> {escape(str(v))}</div>"
                  for k, v in details.items()
                  if v is not None and not isinstance(v, list))
    return f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};
         border-radius:10px;padding:14px;margin:6px 0">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="color:{CLR_TEXT};font-size:13px;font-weight:600">{escape(title)}</div>
        <div style="color:{clr};font-size:18px;font-weight:700">{score:.1f}</div>
      </div>
      <div style="background:#1e293b;border-radius:4px;height:6px;margin:8px 0">
        <div style="background:{clr};width:{bar_w:.0f}%;height:100%;border-radius:4px"></div>
      </div>{det}</div>"""


def _render_radar_chart(scores, labels):
    N = len(labels)
    angles = [n / float(N) * 2 * math.pi for n in range(N)] + [0]
    values = list(scores) + [scores[0]]
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor(CLR_BG)
    ax.set_facecolor(CLR_BG)
    ax.plot(angles, values, 'o-', linewidth=2, color=CLR_ACCENT)
    ax.fill(angles, values, alpha=0.2, color=CLR_ACCENT)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=8, color=CLR_TEXT)
    ax.set_ylim(0, 10)
    ax.set_yticks([2, 4, 6, 8, 10])
    ax.set_yticklabels(["2", "4", "6", "8", "10"], size=7, color=CLR_TEXT_SEC)
    ax.spines['polar'].set_color(CLR_BORDER)
    ax.tick_params(colors=CLR_TEXT_SEC)
    ax.grid(color=CLR_BORDER, alpha=0.4)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _render_water_balance_chart(details):
    dates = details.get("dates", [])
    precip = details.get("daily_precip", [])
    et = details.get("daily_et", [])
    if not dates or not precip:
        return None
    n = min(len(dates), len(precip))
    precip_v = [v if v is not None else 0 for v in precip[:n]]
    et_v = [v if v is not None else 0 for v in et[:n]] if et else [0] * n
    fig, ax = plt.subplots(figsize=(8, 3.5))
    fig.patch.set_facecolor(CLR_BG)
    ax.set_facecolor(CLR_BG)
    x = np.arange(n)
    w = 0.38
    ax.bar(x - w/2, precip_v, w, color=CLR_PRECIP, alpha=0.85, label="Precipitation")
    ax.bar(x + w/2, et_v, w, color=CLR_EVAP, alpha=0.85, label="ET\u2080 (evapotranspiration)")
    step = max(1, n // 10)
    short_d = [d[5:] if len(d) > 5 else d for d in dates[:n]]
    ax.set_xticks(x[::step])
    ax.set_xticklabels(short_d[::step], rotation=45, ha="right", fontsize=7, color=CLR_TEXT_SEC)
    ax.set_ylabel("mm", fontsize=9, color=CLR_TEXT_SEC)
    ax.tick_params(colors=CLR_TEXT_SEC)
    for sp in ax.spines.values():
        sp.set_color(CLR_BORDER)
    ax.legend(fontsize=8, facecolor=CLR_CARD, edgecolor=CLR_BORDER, labelcolor=CLR_TEXT)
    ax.set_title("30-Day Water Balance", fontsize=11, color=CLR_TEXT, pad=10)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


def _add_layer(m, name, data, color, prefix=""):
    fg = folium.FeatureGroup(name=name, show=True)
    for el in data.get("elements", []):
        elat, elon = _element_coords(el)
        if elat is None:
            continue
        tags = el.get("tags", {})
        lbl = tags.get("name", tags.get("man_made", tags.get("waterway",
              tags.get("natural", tags.get("landuse", "feature")))))
        folium.CircleMarker(
            [elat, elon], radius=4, color=color, fill=True,
            fill_opacity=0.75, popup=f"{prefix}{escape(str(lbl))}",
        ).add_to(fg)
    fg.add_to(m)
    return fg


def _build_map(lat, lon, surface, gw, infra, contam):
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB dark_matter")
    folium.Marker([lat, lon], popup="Analysis Centre",
                  icon=folium.Icon(color="blue", icon="crosshairs", prefix="fa")).add_to(m)
    folium.Circle([lat, lon], radius=5000, color=CLR_WATER, fill=False,
                  weight=1, dash_array="5", popup="5 km radius").add_to(m)
    _add_layer(m, "Surface Water", surface, CLR_WATER)
    _add_layer(m, "Groundwater", gw, CLR_ACCENT, "GW: ")
    _add_layer(m, "Infrastructure", infra, CLR_SAFE, "Infra: ")
    # Contamination gets risk zone overlay circles
    contam_fg = folium.FeatureGroup(name="Contamination Risk", show=True)
    for el in contam.get("elements", []):
        elat, elon = _element_coords(el)
        if elat is None:
            continue
        tags = el.get("tags", {})
        lbl = tags.get("name", tags.get("landuse", tags.get("man_made", "risk")))
        folium.Circle([elat, elon], radius=300, color=CLR_DANGER, fill=True,
                      fill_opacity=0.15, weight=1, popup=f"Risk: {escape(str(lbl))}").add_to(contam_fg)
        folium.CircleMarker([elat, elon], radius=4, color=CLR_DANGER, fill=True,
                            fill_opacity=0.8).add_to(contam_fg)
    contam_fg.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def _generate_recommendations(scores, details):
    recs = []
    s1, s2, s3, s4, s5, s6, s7 = scores
    _, _, d3, _, d5, _, _ = details
    if s1 < 4:
        recs.append("**Surface water is scarce.** Consider rainwater harvesting "
                     "or alternative supply sources.")
    elif s1 >= 8:
        recs.append("**Abundant surface water.** Maintain riparian buffers "
                     "to protect quality.")
    if s2 < 4:
        recs.append("**Limited groundwater access.** Geological surveys recommended "
                     "before well drilling.")
    if s3 < 4:
        bal = d3.get("balance_mm", 0)
        recs.append(f"**Water deficit ({bal:.0f} mm / 30 days).** Implement conservation "
                     "measures and evaluate storage capacity.")
    elif s3 >= 8:
        recs.append("**Strong precipitation surplus.** Ensure adequate drainage "
                     "to prevent waterlogging.")
    if s4 < 4:
        recs.append("**Minimal water infrastructure.** Priority investment needed in "
                     "treatment facilities and distribution.")
    if s5 < 4:
        recs.append(f"**High contamination risk ({d5.get('total_sources', 0)} sources).** "
                     "Water quality testing strongly recommended.")
    if s6 < 4:
        recs.append("**High drought vulnerability.** Develop contingency plans, "
                     "improve storage, consider drought-resistant crops.")
    if s7 < 4:
        recs.append("**Poor flood drainage.** Flat terrain with low permeability "
                     "increases flood risk. Consider drainage improvements.")
    elif s7 >= 8:
        recs.append("**Good drainage capacity.** Terrain and soil support "
                     "effective runoff management.")
    if not recs:
        recs.append("**Overall water security is adequate.** Continue monitoring "
                     "and maintain existing infrastructure.")
    return recs


# ═══════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════
def render_water_security_tab():
    """Render the Water Security & Access AI tab."""
    st.markdown("## \U0001F4A7 Water Security & Access AI")
    st.caption("Water availability, quality, infrastructure & drought vulnerability")

    # ── Input controls ──
    st.markdown("---")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        preset = st.selectbox("Location preset", list(WATER_PRESETS.keys()),
                               key="watersec_preset")
    p = WATER_PRESETS.get(preset)
    dlat = p["lat"] if p else 45.60
    dlon = p["lon"] if p else 10.65
    with c2:
        lat = st.number_input("Latitude", value=dlat, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="watersec_lat")
    with c3:
        lon = st.number_input("Longitude", value=dlon, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="watersec_lon")

    radius = st.slider("Analysis radius (m)", 1000, 15000, 5000, 500,
                        key="watersec_radius")
    run = st.button("\U0001F4A7 Analyze Water Security", key="watersec_run",
                    use_container_width=True, type="primary")
    if not run:
        st.info("Select a location and click **Analyze Water Security** to begin.")
        return

    # ── Fetch data ──
    with st.spinner("Fetching surface water data..."):
        surface_data = _fetch_surface_water(lat, lon, radius)
    with st.spinner("Fetching groundwater data..."):
        gw_data = _fetch_groundwater(lat, lon, radius)
    with st.spinner("Fetching soil data..."):
        soil_raw = _fetch_soilgrids(lat, lon)
    with st.spinner("Fetching weather data..."):
        weather = _fetch_weather(lat, lon)
    with st.spinner("Fetching infrastructure data..."):
        infra_data = _fetch_infrastructure(lat, lon, radius)
    with st.spinner("Fetching contamination sources..."):
        contam_data = _fetch_contamination(lat, lon, radius)
    with st.spinner("Fetching elevation data..."):
        elev_data = _fetch_elevation(lat, lon)

    soil_sv = _parse_soil(soil_raw)

    # ── Score all 7 dimensions ──
    s1, d1 = _score_surface_water(surface_data, lat, lon)
    s2, d2 = _score_groundwater(gw_data, soil_sv, lat, lon)
    s3, d3 = _score_precip_balance(weather)
    s4, d4 = _score_infrastructure(infra_data)
    s5, d5 = _score_contamination(contam_data)
    s6, d6 = _score_drought(weather, soil_sv)
    s7, d7 = _score_flood_drainage(elev_data, soil_sv)
    scores = [s1, s2, s3, s4, s5, s6, s7]
    details_all = [d1, d2, d3, d4, d5, d6, d7]

    overall = _clamp(sum(s * w for s, w in zip(scores, DIM_WEIGHTS)))

    # ── Overall gauge ──
    st.markdown("---")
    gc, ic = st.columns([1, 2])
    with gc:
        st.markdown(_render_gauge(overall, "Water Security Index", 240),
                    unsafe_allow_html=True)
    cls_name, cls_clr, cls_desc = _classify(overall)
    with ic:
        st.markdown(f"""<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};
             border-radius:12px;padding:20px;margin:10px 0">
          <div style="font-size:14px;color:{CLR_TEXT_SEC}">Location</div>
          <div style="font-size:16px;color:{CLR_TEXT};font-weight:600">{lat:.4f}, {lon:.4f}</div>
          <div style="margin-top:12px;font-size:14px;color:{CLR_TEXT_SEC}">Classification</div>
          <div style="font-size:22px;color:{cls_clr};font-weight:700">{cls_name}</div>
          <div style="margin-top:6px;color:{CLR_TEXT_SEC};font-size:12px">{cls_desc}</div>
          <div style="margin-top:12px;font-size:14px;color:{CLR_TEXT_SEC}">Radius</div>
          <div style="font-size:14px;color:{CLR_TEXT}">{radius:,} m ({radius/1000:.1f} km)</div>
        </div>""", unsafe_allow_html=True)

    # ── Dimension score cards ──
    st.markdown("### Dimension Scores")
    col_a, col_b = st.columns(2)
    for i, (lbl, sc, det) in enumerate(zip(DIM_LABELS, scores, details_all)):
        with (col_a if i % 2 == 0 else col_b):
            st.markdown(_render_metric_card(lbl, sc, det), unsafe_allow_html=True)

    # ── Radar chart ──
    st.markdown("### Radar Profile")
    st.image(_render_radar_chart(scores, DIM_NAMES), use_container_width=True)

    # ── Water balance chart ──
    st.markdown("### 30-Day Water Balance")
    wb_buf = _render_water_balance_chart(d3)
    if wb_buf:
        st.image(wb_buf, use_container_width=True)
        bal, ratio = d3.get("balance_mm"), d3.get("ratio")
        if bal is not None:
            fn = st.success if bal >= 0 else st.warning
            sign = "+" if bal >= 0 else ""
            fn(f"Water {'surplus' if bal >= 0 else 'deficit'}: "
               f"**{sign}{bal:.1f} mm** over 30 days (P/ET ratio: {ratio:.2f})")
    else:
        st.info("Precipitation data unavailable for this location.")

    # ── Interactive map ──
    st.markdown("### Water Features Map")
    wmap = _build_map(lat, lon, surface_data, gw_data, infra_data, contam_data)
    components.html(wmap._repr_html_(), height=520)

    # ── Summary table ──
    st.markdown("### Dimension Summary")
    rows = []
    for i, (lbl, sc) in enumerate(zip(DIM_LABELS, scores)):
        cn, _, _ = _classify(sc)
        rows.append({"Dimension": lbl, "Score": round(sc, 1), "Rating": cn,
                      "Weight": f"{DIM_WEIGHTS[i]*100:.0f}%",
                      "Contribution": round(sc * DIM_WEIGHTS[i], 2)})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                 key="watersec_summary_table")

    # ── Detailed expanders ──
    st.markdown("### Detailed Analysis")
    with st.expander("Surface Water Access"):
        nearest_m = d1.get("nearest_m")
        nearest_txt = f"{nearest_m:.0f} m" if nearest_m else "None detected"
        st.markdown(f"**Features found:** {d1['count']}  \n"
                    f"**Nearest source:** {nearest_txt}  \n"
                    f"**Score:** {s1:.1f} / 10")
        if d1["count"] == 0:
            st.warning("No surface water detected. Consider expanding the radius.")
    with st.expander("Groundwater Indicators"):
        sand_p = d2.get("sand_pct")
        perm_lbl = ("High" if sand_p and sand_p > 50 else "Moderate" if sand_p and sand_p > 30 else "Low") if sand_p else "N/A"
        st.markdown(f"**Wells/boreholes:** {d2.get('wells', 0)}  \n"
                    f"**Sand content:** {f'{sand_p:.1f}%' if sand_p else 'N/A'} ({perm_lbl} permeability)  \n"
                    f"**Score:** {s2:.1f} / 10")
    with st.expander("Precipitation Balance"):
        tp, te = d3.get("total_precip_mm"), d3.get("total_et_mm")
        if tp is not None:
            st.markdown(f"**Precipitation:** {tp:.1f} mm | **ET:** {te:.1f} mm | "
                        f"**Balance:** {d3.get('balance_mm', 0):.1f} mm  \n**Score:** {s3:.1f} / 10")
        else:
            st.markdown(f"**Score:** {s3:.1f} / 10 (data unavailable)")
    with st.expander("Water Infrastructure"):
        st.markdown(f"**Facilities:** {d4['total']} | **Towers:** {d4['towers']} | "
                    f"**Works:** {d4['works']} | **Drinking pts:** {d4['drinking_points']}  \n"
                    f"**Score:** {s4:.1f} / 10")
    with st.expander("Contamination Risk"):
        st.markdown(f"**Sources:** {d5['total_sources']} | **Industrial:** {d5['industrial']} | "
                    f"**Landfills:** {d5['landfills']} | **Sewage:** {d5['sewage']}  \n"
                    f"**Score:** {s5:.1f} / 10 *(higher = less contamination)*")
        if d5["total_sources"] > 3:
            st.error("High contamination risk detected in this area.")
    with st.expander("Drought Vulnerability"):
        dr = d6.get("drought_risk_raw", 0)
        st.markdown(f"**Precip:** {d6['30d_precip_mm']:.1f} mm | "
                    f"**Avg max temp:** {d6['avg_max_temp_c']:.1f} C | "
                    f"**Sand:** {d6['sand_pct']:.1f}%  \n**Score:** {s6:.1f} / 10")
        (st.error if dr > 6 else st.warning if dr > 3 else st.success)(
            f"{'High' if dr > 6 else 'Moderate' if dr > 3 else 'Low'} drought vulnerability "
            f"(risk index: {dr:.1f})")
    with st.expander("Flood Drainage Capacity"):
        elev_s = f"{d7['elevation_m']:.1f} m" if d7.get("elevation_m") else "N/A"
        st.markdown(f"**Elevation:** {elev_s} | **Slope:** {d7['slope_deg']:.2f} deg | "
                    f"**Sand:** {d7['sand_pct']:.1f}%  \n**Score:** {s7:.1f} / 10")

    # ── Recommendations ──
    st.markdown("### Recommendations")
    for rec in _generate_recommendations(scores, details_all):
        st.markdown(f"- {rec}")

    # ── Export ──
    st.markdown("---")
    export = {"location": {"latitude": lat, "longitude": lon}, "radius_m": radius,
              "overall_score": round(overall, 2), "classification": cls_name,
              "dimensions": {}}
    for i, (lbl, sc, det) in enumerate(zip(DIM_LABELS, scores, details_all)):
        safe = {k: v for k, v in det.items() if v is not None}
        export["dimensions"][lbl] = {"score": round(sc, 2),
                                      "weight": DIM_WEIGHTS[i], "details": safe}
    st.download_button("Download Report (JSON)",
                       data=json.dumps(export, indent=2, default=str),
                       file_name=f"water_security_{lat:.4f}_{lon:.4f}.json",
                       mime="application/json", key="watersec_download")
