"""
Proximity Scanner AI module for TerraScout AI.
Shows EVERYTHING discoverable near a given point: terrain, features, species,
infrastructure, hazards, resources -- all in one comprehensive radar sweep.
Uses free APIs: Open Topo Data, SoilGrids, Open-Meteo, iNaturalist, GBIF,
Overpass, Macrostrat, USGS Earthquakes, Open-Meteo Air Quality.
"""
import html as html_module
import json
import logging
import math
from datetime import datetime
import pandas as pd
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import requests
import streamlit as st
from src.deep_zone_analysis import (
    ANALYSIS_PRESETS, fetch_soil_data, fetch_weather_data, fetch_water_features,
    fetch_elevation_grid, fetch_landuse_infrastructure, fetch_protected_areas,
    fetch_biodiversity, fetch_gbif_occurrences, compute_species_breakdown,
    fetch_earthquakes,
)

logger = logging.getLogger(__name__)
MACROSTRAT_API = "https://macrostrat.org/api/v2"
AIR_QUALITY_API = "https://air-quality-api.open-meteo.com/v1/air-quality"
_PLOTLY_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(15,23,42,0.65)",
    font=dict(color="#e8ecf4", size=11), margin=dict(l=40, r=20, t=36, b=36),
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)
_PIE_COLORS = [
    "#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444",
    "#ec4899", "#3b82f6", "#14b8a6", "#f97316", "#84cc16",
    "#a855f7", "#22c55e", "#64748b", "#dc2626", "#0ea5e9",
]

# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL FETCH HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def fetch_air_quality_proximity(lat: float, lon: float) -> dict:
    """Fetch current air quality from Open-Meteo Air Quality API."""
    try:
        resp = requests.get(AIR_QUALITY_API, params={
            "latitude": lat, "longitude": lon,
            "current": "pm2_5,pm10,nitrogen_dioxide,ozone,sulphur_dioxide,carbon_monoxide,european_aqi",
        }, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Air quality fetch error: %s", exc)
        return {}

@st.cache_data(ttl=1800)
def fetch_geology_proximity(lat: float, lon: float) -> dict:
    """Fetch geological unit data from Macrostrat."""
    try:
        resp = requests.get(f"{MACROSTRAT_API}/geologic_units/map",
                            params={"lat": lat, "lng": lon, "response": "long"}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Macrostrat geology error: %s", exc)
        return {}

# ═══════════════════════════════════════════════════════════════════════════════
# EXTRACTION / CATEGORISATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def _extract_terrain(elevation: dict) -> dict:
    e = elevation if isinstance(elevation, dict) else {}
    center = e.get("center_elevation", 0) or 0
    mn = e.get("min_elevation", 0) or 0
    mx = e.get("max_elevation", 0) or 0
    avg = e.get("avg_elevation", 0) or 0
    rng = mx - mn
    if rng > 500:  tc = "Mountainous"
    elif rng > 100: tc = "Hilly"
    elif rng > 30:  tc = "Rolling"
    else:           tc = "Flat"
    return {"center_elevation": round(center, 1), "min_elevation": round(mn, 1),
            "max_elevation": round(mx, 1), "avg_elevation": round(avg, 1),
            "elevation_range": round(rng, 1), "slope_estimate_pct": round(rng / max(1, 11.1), 2),
            "terrain_class": tc}

def _extract_weather(weather: dict) -> dict:
    w = weather if isinstance(weather, dict) else {}
    cur = w.get("current", {}) if isinstance(w.get("current"), dict) else {}
    return {"temperature_c": cur.get("temperature_2m") or 0,
            "humidity_pct": cur.get("relative_humidity_2m") or 0,
            "wind_speed_kmh": cur.get("wind_speed_10m") or 0,
            "precipitation_mm": cur.get("precipitation") or 0,
            "cloud_cover_pct": cur.get("cloud_cover") or 0,
            "pressure_hpa": cur.get("surface_pressure") or 0}

def _extract_soil(soil: dict) -> dict:
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
                val = (depths[0].get("values", {}) if isinstance(depths[0], dict) else {}).get("mean")
                if val is not None:
                    return round(val / div, 2)
        return None
    clay, sand, silt = _sv("clay", 10), _sv("sand", 10), _sv("silt", 10)
    ph, soc, nitrogen = _sv("phh2o", 10), _sv("soc", 10), _sv("nitrogen", 100)
    texture = "Unknown"
    if clay is not None and sand is not None and silt is not None:
        if clay > 40:       texture = "Clay"
        elif sand > 65:     texture = "Sandy"
        elif silt > 45:     texture = "Silty"
        elif clay > 25:     texture = "Clay Loam"
        elif sand > 45:     texture = "Sandy Loam"
        else:               texture = "Loam"
    return {"clay_pct": clay, "sand_pct": sand, "silt_pct": silt, "ph": ph,
            "organic_carbon_g_kg": soc, "nitrogen_g_kg": nitrogen, "texture_class": texture}

def _categorize_water(water: dict) -> dict:
    els = (water if isinstance(water, dict) else {}).get("elements", [])
    els = els if isinstance(els, list) else []
    cats = {"rivers": 0, "streams": 0, "springs": 0, "wells": 0,
            "lakes": 0, "canals": 0, "dams": 0, "wetlands": 0, "other": 0}
    for el in els:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        ww, nat, mm = tags.get("waterway", ""), tags.get("natural", ""), tags.get("man_made", "")
        if ww == "river":       cats["rivers"] += 1
        elif ww == "stream":    cats["streams"] += 1
        elif ww == "canal":     cats["canals"] += 1
        elif ww == "dam":       cats["dams"] += 1
        elif nat == "spring":   cats["springs"] += 1
        elif nat == "water":    cats["lakes"] += 1
        elif nat == "wetland":  cats["wetlands"] += 1
        elif mm == "water_well": cats["wells"] += 1
        else:                   cats["other"] += 1
    return {"categories": cats, "total": sum(cats.values())}

def _categorize_infrastructure(infra: dict) -> dict:
    els = (infra if isinstance(infra, dict) else {}).get("elements", [])
    els = els if isinstance(els, list) else []
    buildings = {"total": 0, "residential": 0, "commercial": 0, "industrial": 0, "other": 0}
    roads = {"motorway": 0, "primary": 0, "secondary": 0, "tertiary": 0,
             "residential": 0, "track": 0, "other": 0}
    services = {"hospital": 0, "school": 0, "shop": 0, "restaurant": 0,
                "bank": 0, "police": 0, "fire_station": 0}
    utilities = {"power_line": 0, "substation": 0, "telecom_tower": 0, "water_works": 0}
    transport = {"bus_stop": 0, "rail_station": 0, "airport": 0}
    _bld_res = ("residential", "house", "apartments", "detached")
    _bld_com = ("commercial", "office", "retail")
    _bld_ind = ("industrial", "warehouse", "factory")
    _hw_map = {"motorway": "motorway", "motorway_link": "motorway",
               "primary": "primary", "primary_link": "primary",
               "secondary": "secondary", "secondary_link": "secondary",
               "tertiary": "tertiary", "tertiary_link": "tertiary",
               "residential": "residential", "living_street": "residential",
               "track": "track", "path": "track", "footway": "track"}
    for el in els:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        if "building" in tags:
            buildings["total"] += 1
            bt = tags.get("building", "yes")
            if bt in _bld_res:   buildings["residential"] += 1
            elif bt in _bld_com: buildings["commercial"] += 1
            elif bt in _bld_ind: buildings["industrial"] += 1
            else:                buildings["other"] += 1
        if "highway" in tags:
            roads[_hw_map.get(tags["highway"], "other")] += 1
        amenity = tags.get("amenity", "")
        if amenity == "hospital": services["hospital"] += 1
        elif amenity in ("school", "university", "college"): services["school"] += 1
        elif amenity in ("restaurant", "cafe", "fast_food"): services["restaurant"] += 1
        elif amenity == "bank": services["bank"] += 1
        elif amenity == "police": services["police"] += 1
        elif amenity == "fire_station": services["fire_station"] += 1
        if tags.get("shop"): services["shop"] += 1
        pw = tags.get("power", "")
        if pw == "line": utilities["power_line"] += 1
        elif pw == "substation": utilities["substation"] += 1
        if tags.get("man_made") == "tower" and tags.get("tower:type") == "communication":
            utilities["telecom_tower"] += 1
        if tags.get("man_made") == "water_works": utilities["water_works"] += 1
        if tags.get("public_transport") == "stop_position" or amenity == "bus_station":
            transport["bus_stop"] += 1
        if tags.get("railway") in ("station", "halt"): transport["rail_station"] += 1
        if tags.get("aeroway") in ("aerodrome", "airport"): transport["airport"] += 1
    return {"buildings": buildings, "roads": roads, "services": services,
            "utilities": utilities, "transport": transport}

def _categorize_nature(protected: dict, inat: dict, gbif: dict) -> dict:
    prot_els = (protected if isinstance(protected, dict) else {}).get("elements", [])
    prot_els = prot_els if isinstance(prot_els, list) else []
    prot_names = []
    for el in prot_els:
        name = (el.get("tags", {}) if isinstance(el, dict) else {}).get("name", "Unnamed Protected Area")
        if name not in prot_names:
            prot_names.append(name)
    bio = compute_species_breakdown(inat if isinstance(inat, dict) else {},
                                     gbif if isinstance(gbif, dict) else {})
    kc = bio.get("kingdom_counts", {}) if isinstance(bio, dict) else {}
    return {"species_count": sum(v for v in kc.values() if v),
            "kingdom_breakdown": kc,
            "top_species": (bio.get("top_species", []) if isinstance(bio, dict) else [])[:10],
            "protected_areas": prot_names[:15],
            "protected_area_count": len(prot_els)}

def _assess_hazards(quakes: dict, weather: dict, elevation: dict) -> dict:
    features = (quakes if isinstance(quakes, dict) else {}).get("features", [])
    features = features if isinstance(features, list) else []
    mags = [float(f.get("properties", {}).get("mag", 0))
            for f in features if isinstance(f, dict) and f.get("properties", {}).get("mag") is not None]
    e = elevation if isinstance(elevation, dict) else {}
    center_elev = e.get("center_elevation", 0) or 0
    rng = (e.get("max_elevation", 0) or 0) - (e.get("min_elevation", 0) or 0)
    flood = "High" if (center_elev < 10 and rng < 20) else ("Moderate" if center_elev < 50 else "Low")
    w = weather if isinstance(weather, dict) else {}
    wind = (w.get("current", {}) if isinstance(w.get("current"), dict) else {}).get("wind_speed_10m") or 0
    return {"earthquake_count": len(mags), "earthquake_max_mag": round(max(mags) if mags else 0, 1),
            "flood_indicator": flood, "high_wind": wind > 60,
            "wind_speed_kmh": round(wind, 1), "steep_terrain": rng > 300}

def _extract_air(air: dict) -> dict:
    cur = (air if isinstance(air, dict) else {}).get("current", {})
    cur = cur if isinstance(cur, dict) else {}
    return {"pm2_5": cur.get("pm2_5") or 0, "pm10": cur.get("pm10") or 0,
            "no2": cur.get("nitrogen_dioxide") or 0, "o3": cur.get("ozone") or 0,
            "so2": cur.get("sulphur_dioxide") or 0, "co": cur.get("carbon_monoxide") or 0,
            "aqi": cur.get("european_aqi") or 0}

def _extract_geology(geo: dict) -> dict:
    g = geo if isinstance(geo, dict) else {}
    dl = (g.get("success", {}) if isinstance(g.get("success"), dict) else {}).get("data", [])
    if not isinstance(dl, list) or not dl:
        return {"rock_type": "Unknown", "formation_age": "Unknown", "lithology": "Unknown",
                "age_ma": "Unknown", "environment": "Unknown", "color": "#8b97b0"}
    it = dl[0] if isinstance(dl[0], dict) else {}
    return {"rock_type": it.get("strat_name_long") or it.get("strat_name") or it.get("name") or "Unknown",
            "formation_age": it.get("t_int_name") or "Unknown",
            "lithology": it.get("lith") or "Unknown", "age_ma": it.get("t_age") or "Unknown",
            "environment": it.get("environ") or "Unknown", "color": it.get("color") or "#8b97b0"}

def _compute_summary_stats(terrain, infra, water, nature, hazards):
    bldgs = infra.get("buildings", {}).get("total", 0) or 0
    road_t = sum((v or 0) for v in infra.get("roads", {}).values())
    svc_t = sum((v or 0) for v in infra.get("services", {}).values())
    util_t = sum((v or 0) for v in infra.get("utilities", {}).values())
    trans_t = sum((v or 0) for v in infra.get("transport", {}).values())
    water_t = water.get("total", 0) or 0
    spec_t = nature.get("species_count", 0) or 0
    prot_t = nature.get("protected_area_count", 0) or 0
    eq_t = hazards.get("earthquake_count", 0) or 0
    total = bldgs + road_t + svc_t + util_t + trans_t + water_t + spec_t + prot_t + eq_t
    area = math.pi * 25.0  # ~5 km radius
    density = total / area if area > 0 else 0
    parts = []
    if bldgs > 200:   parts.append(f"{bldgs} buildings (dense urban)")
    elif bldgs > 50:  parts.append(f"{bldgs} buildings")
    if spec_t > 100:  parts.append(f"{spec_t} species observations")
    if eq_t > 10:     parts.append(f"{eq_t} earthquakes (seismically active)")
    if water_t > 20:  parts.append(f"{water_t} water features")
    if prot_t > 0:    parts.append(f"{prot_t} protected areas")
    if bldgs > 200 or density > 50:   char = "Urban"
    elif bldgs > 50 or density > 15:  char = "Suburban"
    elif bldgs > 5:                    char = "Rural"
    else:                              char = "Wilderness"
    return {"total_features": total, "feature_density_per_km2": round(density, 1),
            "most_notable": parts[0] if parts else "No standout features",
            "characterization": char,
            "breakdown": {"buildings": bldgs, "roads": road_t, "services": svc_t,
                          "utilities": util_t, "transport": trans_t,
                          "water_features": water_t, "species_observations": spec_t,
                          "protected_areas": prot_t, "earthquakes": eq_t}}

# ═══════════════════════════════════════════════════════════════════════════════
# MASTER SCAN FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def scan_proximity(lat: float, lon: float) -> dict:
    """Fetch ALL data sources and organise into categories."""
    soil = fetch_soil_data(lat, lon) or {}
    weather = fetch_weather_data(lat, lon) or {}
    water = fetch_water_features(lat, lon) or {}
    elevation = fetch_elevation_grid(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    protected = fetch_protected_areas(lat, lon) or {}
    inat = fetch_biodiversity(lat, lon) or {}
    gbif = fetch_gbif_occurrences(lat, lon) or {}
    quakes = fetch_earthquakes(lat, lon) or {}
    air = fetch_air_quality_proximity(lat, lon)
    geology = fetch_geology_proximity(lat, lon)
    terrain = _extract_terrain(elevation)
    weather_now = _extract_weather(weather)
    soil_profile = _extract_soil(soil)
    water_features = _categorize_water(water)
    infrastructure = _categorize_infrastructure(infra)
    nature = _categorize_nature(protected, inat, gbif)
    hazards = _assess_hazards(quakes, weather, elevation)
    air_quality = _extract_air(air)
    geo = _extract_geology(geology)
    summary_stats = _compute_summary_stats(terrain, infrastructure, water_features, nature, hazards)
    return {"terrain": terrain, "weather_now": weather_now, "soil_profile": soil_profile,
            "water_features": water_features, "infrastructure": infrastructure, "nature": nature,
            "hazards": hazards, "air_quality": air_quality, "geology": geo,
            "summary_stats": summary_stats}

# ═══════════════════════════════════════════════════════════════════════════════
# PLOTLY CHART BUILDERS
# ═══════════════════════════════════════════════════════════════════════════════
def _pie_chart(labels, values, title):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.45,
        marker=dict(colors=_PIE_COLORS[:len(labels)]), textinfo="label+percent",
        textfont=dict(size=10, color="#e8ecf4"), hovertemplate="%{label}: %{value}<extra></extra>"))
    fig.update_layout(title=dict(text=title, font=dict(size=13, color="#e8ecf4")),
                      showlegend=True, height=320, **_PLOTLY_DARK)
    return fig

def _bar_chart(labels, values, title, color="#06b6d4"):
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=color,
        text=values, textposition="auto", textfont=dict(color="#e8ecf4", size=10)))
    fig.update_layout(title=dict(text=title, font=dict(size=13, color="#e8ecf4")),
                      yaxis=dict(autorange="reversed"),
                      height=max(200, len(labels) * 32 + 80), **_PLOTLY_DARK)
    return fig

def _gauge_chart(value, max_val, title, unit, color="#06b6d4"):
    if max_val <= 0: max_val = 100
    fig = go.Figure(go.Indicator(mode="gauge+number", value=value,
        number=dict(suffix=f" {unit}", font=dict(size=22, color="#e8ecf4")),
        title=dict(text=title, font=dict(size=12, color="#8b97b0")),
        gauge=dict(axis=dict(range=[0, max_val], tickcolor="#5a6580"),
                   bar=dict(color=color), bgcolor="#1a2235", borderwidth=0,
                   steps=[dict(range=[0, max_val * 0.33], color="#0f172a"),
                          dict(range=[max_val * 0.33, max_val * 0.66], color="#1e293b"),
                          dict(range=[max_val * 0.66, max_val], color="#2a3550")])))
    fig.update_layout(height=220, **_PLOTLY_DARK)
    return fig

def _elevation_line_chart(elevation):
    ns = elevation.get("ns_profile", []) if isinstance(elevation, dict) else []
    ew = elevation.get("ew_profile", []) if isinstance(elevation, dict) else []
    fig = go.Figure()
    if ns:
        fig.add_trace(go.Scatter(x=[f"{p.get('lat',0):.3f}" for p in ns],
            y=[p.get("elevation", 0) for p in ns], mode="lines+markers",
            name="N-S Profile", line=dict(color="#06b6d4", width=2), marker=dict(size=4)))
    if ew:
        fig.add_trace(go.Scatter(x=[f"{p.get('lon',0):.3f}" for p in ew],
            y=[p.get("elevation", 0) for p in ew], mode="lines+markers",
            name="E-W Profile", line=dict(color="#8b5cf6", width=2), marker=dict(size=4)))
    fig.update_layout(title=dict(text="Elevation Profile", font=dict(size=13, color="#e8ecf4")),
                      xaxis_title="Coordinate", yaxis_title="Elevation (m)",
                      height=300, **_PLOTLY_DARK)
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
# UI HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def _metric_card(label, value, color="#06b6d4"):
    sl, sv = html_module.escape(str(label)), html_module.escape(str(value))
    return (f'<div style="background:rgba(15,23,42,0.75);border:1px solid #2a3550;'
            f'border-radius:10px;padding:12px 14px;text-align:center;backdrop-filter:blur(16px);">'
            f'<div style="color:{color};font-size:20px;font-weight:bold;line-height:1.2;">{sv}</div>'
            f'<div style="color:#8b97b0;font-size:11px;margin-top:2px;">{sl}</div></div>')

def _badge_html(text, color="#06b6d4"):
    return (f'<span style="background:{color};color:#0a0e1a;padding:3px 10px;'
            f'border-radius:12px;font-size:11px;font-weight:bold;">'
            f'{html_module.escape(str(text))}</span>')

def _table_html(title, rows):
    """Build an HTML card with a title and list of (label, value) rows."""
    trs = "".join(f'<tr><td style="color:#8b97b0;padding:4px 0;">{html_module.escape(str(l))}</td>'
                  f'<td style="text-align:right;">{html_module.escape(str(v))}</td></tr>'
                  for l, v in rows)
    return (f'<div style="background:rgba(15,23,42,0.75);border:1px solid #2a3550;'
            f'border-radius:12px;padding:16px;backdrop-filter:blur(16px);">'
            f'<h5 style="color:#e8ecf4;margin:0 0 10px 0;">{html_module.escape(str(title))}</h5>'
            f'<table style="width:100%;color:#e8ecf4;font-size:13px;">{trs}</table></div>')

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TAB RENDERER
# ═══════════════════════════════════════════════════════════════════════════════
def render_proximity_scanner_tab():
    """Render the Proximity Scanner AI tab UI."""
    st.markdown(
        '<div class="tab-header violet"><h4>Proximity Scanner AI</h4>'
        '<p>Comprehensive radar sweep of ALL discoverable data near a point &mdash; '
        'terrain, species, infrastructure, hazards, resources, air quality &amp; geology</p></div>',
        unsafe_allow_html=True)

    # ── Controls ──
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        preset = st.selectbox("Preset Location", list(ANALYSIS_PRESETS.keys()), key="prox_preset")
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50
    with c2:
        lat = st.number_input("Latitude", value=default_lat, format="%.5f",
                              min_value=-90.0, max_value=90.0, key="prox_lat")
    with c3:
        lon = st.number_input("Longitude", value=default_lon, format="%.5f",
                              min_value=-180.0, max_value=180.0, key="prox_lon")
    run_scan = st.button("Run Proximity Scan", type="primary", key="prox_run",
                         use_container_width=True)
    if not run_scan:
        st.info("Set coordinates and click **Run Proximity Scan** to perform a "
                "full radar sweep of everything near this point.")
        return

    # ── Fetch all data ──
    progress = st.progress(0, text="Initialising proximity scan...")
    _steps = [
        (5, "terrain", lambda: fetch_elevation_grid(lat, lon) or {}),
        (12, "soil", lambda: fetch_soil_data(lat, lon) or {}),
        (20, "weather", lambda: fetch_weather_data(lat, lon) or {}),
        (28, "water", lambda: fetch_water_features(lat, lon) or {}),
        (36, "infra", lambda: fetch_landuse_infrastructure(lat, lon) or {}),
        (44, "protected", lambda: fetch_protected_areas(lat, lon) or {}),
        (52, "inat", lambda: fetch_biodiversity(lat, lon) or {}),
        (60, "gbif", lambda: fetch_gbif_occurrences(lat, lon) or {}),
        (68, "quakes", lambda: fetch_earthquakes(lat, lon) or {}),
        (76, "air", lambda: fetch_air_quality_proximity(lat, lon)),
        (84, "geology", lambda: fetch_geology_proximity(lat, lon)),
    ]
    _labels = {"terrain": "Fetching terrain...", "soil": "Fetching soil...",
               "weather": "Fetching weather...", "water": "Fetching water features...",
               "infra": "Fetching infrastructure...", "protected": "Fetching protected areas...",
               "inat": "Fetching iNaturalist...", "gbif": "Fetching GBIF...",
               "quakes": "Fetching earthquakes...", "air": "Fetching air quality...",
               "geology": "Fetching geology..."}
    raw = {}
    for pct, key, fn in _steps:
        progress.progress(pct, text=_labels.get(key, "Fetching..."))
        raw[key] = fn()
    progress.progress(92, text="Analysing and categorising...")

    # ── Process ──
    terrain = _extract_terrain(raw["terrain"])
    weather_now = _extract_weather(raw["weather"])
    soil_profile = _extract_soil(raw["soil"])
    water_cats = _categorize_water(raw["water"])
    infrastructure = _categorize_infrastructure(raw["infra"])
    nature = _categorize_nature(raw["protected"], raw["inat"], raw["gbif"])
    hazards = _assess_hazards(raw["quakes"], raw["weather"], raw["terrain"])
    air_quality = _extract_air(raw["air"])
    geo = _extract_geology(raw["geology"])
    summary = _compute_summary_stats(terrain, infrastructure, water_cats, nature, hazards)
    progress.progress(100, text="Proximity scan complete!")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 -- Scan Header
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    char = summary.get("characterization", "Unknown")
    cc = {"Urban": "#ef4444", "Suburban": "#f59e0b", "Rural": "#10b981", "Wilderness": "#06b6d4"}
    st.markdown(
        f'<div style="background:rgba(15,23,42,0.75);border:1px solid #2a3550;border-radius:14px;'
        f'padding:20px 24px;backdrop-filter:blur(16px);margin-bottom:16px;">'
        f'<h3 style="color:#e8ecf4;margin:0 0 8px 0;">Proximity Scan Complete</h3>'
        f'<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;">'
        f'<span style="color:#8b97b0;font-size:13px;">Total features: '
        f'<b style="color:#e8ecf4;">{summary.get("total_features",0)}</b></span>'
        f'<span style="color:#8b97b0;font-size:13px;">Density: '
        f'<b style="color:#e8ecf4;">{summary.get("feature_density_per_km2",0)}/km&sup2;</b></span>'
        f'<span style="color:#8b97b0;font-size:13px;">Coords: '
        f'<b style="color:#e8ecf4;">{lat:.4f}, {lon:.4f}</b></span>'
        f'{_badge_html(char, cc.get(char,"#8b97b0"))}</div>'
        f'<div style="color:#5a6580;font-size:12px;margin-top:6px;">'
        f'Notable: {html_module.escape(str(summary.get("most_notable","N/A")))}</div></div>',
        unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 -- Quick Stats (8 cards)
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Quick Stats")
    qs = st.columns(8)
    cards = [
        ("Elevation", f"{terrain.get('center_elevation',0):.0f} m", "#06b6d4"),
        ("Temperature", f"{weather_now.get('temperature_c',0):.1f} C", "#f59e0b"),
        ("AQI", f"{air_quality.get('aqi',0):.0f}", "#10b981"),
        ("Buildings", f"{infrastructure.get('buildings',{}).get('total',0)}", "#8b5cf6"),
        ("Roads", f"{sum((v or 0) for v in infrastructure.get('roads',{}).values())}", "#ec4899"),
        ("Species", f"{nature.get('species_count',0)}", "#14b8a6"),
        ("Water", f"{water_cats.get('total',0)}", "#3b82f6"),
        ("Earthquakes", f"{hazards.get('earthquake_count',0)}", "#ef4444"),
    ]
    for i, (lbl, val, clr) in enumerate(cards):
        with qs[i]:
            st.markdown(_metric_card(lbl, val, clr), unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 -- Terrain & Weather
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Terrain & Weather")
    tw1, tw2 = st.columns([1.3, 1])
    with tw1:
        st.plotly_chart(_elevation_line_chart(raw["terrain"]), use_container_width=True, key="prosca_pchart1")
        te = st.columns(4)
        te[0].metric("Center", f"{terrain.get('center_elevation',0):.0f} m")
        te[1].metric("Min", f"{terrain.get('min_elevation',0):.0f} m")
        te[2].metric("Max", f"{terrain.get('max_elevation',0):.0f} m")
        te[3].metric("Class", terrain.get("terrain_class", "N/A"))
    with tw2:
        wn = weather_now
        st.markdown(_table_html("Current Weather", [
            ("Temperature", f"{wn.get('temperature_c',0):.1f} C"),
            ("Humidity", f"{wn.get('humidity_pct',0):.0f}%"),
            ("Wind Speed", f"{wn.get('wind_speed_kmh',0):.1f} km/h"),
            ("Precipitation", f"{wn.get('precipitation_mm',0):.1f} mm"),
            ("Cloud Cover", f"{wn.get('cloud_cover_pct',0):.0f}%"),
            ("Pressure", f"{wn.get('pressure_hpa',0):.0f} hPa"),
        ]), unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 -- Infrastructure Breakdown
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Infrastructure Breakdown")
    with st.expander("Buildings", expanded=True):
        bldg = infrastructure.get("buildings", {})
        bc1, bc2 = st.columns(2)
        with bc1:
            bd = {k: v for k, v in bldg.items() if k != "total" and (v or 0) > 0}
            if bd:
                st.plotly_chart(_pie_chart(list(bd.keys()), list(bd.values()),
                    f"Building Types (Total: {bldg.get('total',0)})"), use_container_width=True, key="prosca_pchart2")
            else:
                st.info("No buildings found in the scan radius.")
        with bc2:
            st.metric("Total Buildings", bldg.get("total", 0))
            b1, b2 = st.columns(2)
            b1.metric("Residential", bldg.get("residential", 0))
            b2.metric("Commercial", bldg.get("commercial", 0))
            b3, b4 = st.columns(2)
            b3.metric("Industrial", bldg.get("industrial", 0))
            b4.metric("Other", bldg.get("other", 0))
    with st.expander("Road Network"):
        rd = {k: v for k, v in infrastructure.get("roads", {}).items() if (v or 0) > 0}
        if rd:
            st.plotly_chart(_bar_chart(list(rd.keys()), list(rd.values()),
                "Roads by Classification", "#8b5cf6"), use_container_width=True, key="prosca_pchart3")
        else:
            st.info("No road segments found in the scan radius.")
    with st.expander("Services Inventory"):
        sv = {k: v for k, v in infrastructure.get("services", {}).items() if (v or 0) > 0}
        if sv:
            st.dataframe(pd.DataFrame([{"Service": k.replace("_", " ").title(), "Count": v}
                for k, v in sv.items()]), use_container_width=True, hide_index=True)
        else:
            st.info("No services (hospitals, schools, shops, etc.) found.")
    with st.expander("Utilities & Transport"):
        ut = {k: v for k, v in infrastructure.get("utilities", {}).items() if (v or 0) > 0}
        tr = {k: v for k, v in infrastructure.get("transport", {}).items() if (v or 0) > 0}
        if ut or tr:
            for k, v in {**ut, **tr}.items():
                st.metric(k.replace("_", " ").title(), v)
        else:
            st.info("No utilities or transport infrastructure found.")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 -- Natural Environment
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Natural Environment")
    ne1, ne2 = st.columns([1, 1.2])
    with ne1:
        kc = {k: v for k, v in nature.get("kingdom_breakdown", {}).items() if k and (v or 0) > 0}
        if kc:
            st.plotly_chart(_pie_chart(list(kc.keys()), list(kc.values()),
                f"Species by Kingdom ({nature.get('species_count',0)} total)"),
                use_container_width=True, key="prosca_pchart4")
        else:
            st.info("No biodiversity observations found near this point.")
    with ne2:
        top_sp = nature.get("top_species", [])
        if top_sp:
            sp_rows = [{"Scientific Name": s[0] or "Unknown", "Count": s[1] or 0,
                         "Common Name": s[2] or ""}
                        for s in top_sp if isinstance(s, (list, tuple)) and len(s) >= 3]
            if sp_rows:
                st.markdown("**Top 10 Species**")
                st.dataframe(pd.DataFrame(sp_rows), use_container_width=True, hide_index=True)
        pa_list = nature.get("protected_areas", [])
        if pa_list:
            st.markdown("**Protected Areas**")
            for pn in pa_list[:10]:
                st.markdown(f"- {html_module.escape(str(pn))}", unsafe_allow_html=True)
        st.metric("Protected Area Count", nature.get("protected_area_count", 0))

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6 -- Water & Soil
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Water & Soil")
    ws1, ws2 = st.columns(2)
    with ws1:
        wc = {k: v for k, v in water_cats.get("categories", {}).items() if (v or 0) > 0}
        if wc:
            st.plotly_chart(_pie_chart(list(wc.keys()), list(wc.values()),
                f"Water Features by Type ({water_cats.get('total',0)} total)"),
                use_container_width=True, key="prosca_pchart5")
        else:
            st.info("No water features found in the scan radius.")
    with ws2:
        sp = soil_profile
        st.markdown(_table_html("Soil Profile (Surface Layer)", [
            ("Texture Class", sp.get("texture_class", "N/A")),
            ("Clay", f"{sp.get('clay_pct', 'N/A')}%"),
            ("Sand", f"{sp.get('sand_pct', 'N/A')}%"),
            ("Silt", f"{sp.get('silt_pct', 'N/A')}%"),
            ("pH", sp.get("ph", "N/A")),
            ("Organic Carbon", f"{sp.get('organic_carbon_g_kg', 'N/A')} g/kg"),
            ("Nitrogen", f"{sp.get('nitrogen_g_kg', 'N/A')} g/kg"),
        ]), unsafe_allow_html=True)
        soc_v, n_v = sp.get("organic_carbon_g_kg"), sp.get("nitrogen_g_kg")
        if soc_v is not None and n_v is not None:
            if soc_v > 30 and n_v > 2:   fert, fc = "High", "#10b981"
            elif soc_v > 15 or n_v > 1:  fert, fc = "Moderate", "#f59e0b"
            else:                          fert, fc = "Low", "#ef4444"
            st.markdown(f'<div style="text-align:center;margin-top:8px;">'
                        f'Fertility Indicator: {_badge_html(fert, fc)}</div>',
                        unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 7 -- Hazards & Air Quality
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Hazards & Air Quality")
    ha1, ha2 = st.columns(2)
    with ha1:
        hw_txt = (f'Yes ({hazards.get("wind_speed_kmh",0)} km/h)'
                  if hazards.get("high_wind") else "No")
        st.markdown(_table_html("Seismic & Environmental Hazards", [
            ("Earthquakes (1yr)", hazards.get("earthquake_count", 0)),
            ("Max Magnitude", hazards.get("earthquake_max_mag", 0)),
            ("Flood Indicator", hazards.get("flood_indicator", "N/A")),
            ("Steep Terrain", "Yes" if hazards.get("steep_terrain") else "No"),
            ("High Wind", hw_txt),
        ]), unsafe_allow_html=True)
        ind_c = infrastructure.get("buildings", {}).get("industrial", 0) or 0
        if ind_c > 0:
            st.warning(f"Industrial hazard: {ind_c} industrial building(s) in scan radius.")
    with ha2:
        aqi_val = air_quality.get("aqi", 0) or 0
        aqi_clr = "#10b981" if aqi_val < 50 else ("#f59e0b" if aqi_val < 100 else "#ef4444")
        st.plotly_chart(_gauge_chart(float(aqi_val), 150.0, "European AQI", "AQI", aqi_clr),
                        use_container_width=True, key="prosca_pchart6")
        aq_cols = st.columns(3)
        for idx, (nm, key, u) in enumerate([
            ("PM2.5", "pm2_5", "ug/m3"), ("PM10", "pm10", "ug/m3"),
            ("NO2", "no2", "ug/m3"), ("O3", "o3", "ug/m3"),
            ("SO2", "so2", "ug/m3"), ("CO", "co", "ug/m3"),
        ]):
            with aq_cols[idx % 3]:
                v = air_quality.get(key, 0) or 0
                st.metric(nm, f"{v:.1f} {u}")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 8 -- Geology
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Geology")
    gc = html_module.escape(str(geo.get("color", "#2a3550")))
    st.markdown(
        f'<div style="background:rgba(15,23,42,0.75);border-left:5px solid {gc};'
        f'border:1px solid #2a3550;border-radius:0 12px 12px 0;padding:16px 20px;'
        f'backdrop-filter:blur(16px);">'
        f'<table style="width:100%;color:#e8ecf4;font-size:13px;">'
        + "".join(f'<tr><td style="color:#8b97b0;padding:4px 0;">{html_module.escape(str(lb))}</td>'
                  f'<td style="text-align:right;{" font-weight:bold;" if i == 0 else ""}">'
                  f'{html_module.escape(str(vl))}</td></tr>'
                  for i, (lb, vl) in enumerate([
                      ("Rock Type / Formation", geo.get("rock_type", "Unknown")),
                      ("Formation Age / Period", geo.get("formation_age", "Unknown")),
                      ("Age (Ma)", geo.get("age_ma", "Unknown")),
                      ("Lithology", geo.get("lithology", "Unknown")),
                      ("Environment", geo.get("environment", "Unknown")),
                  ]))
        + '</table></div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 9 -- Feature Density Summary
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("### Feature Density Summary")
    bd = summary.get("breakdown", {})
    fd1, fd2 = st.columns([1.2, 1])
    with fd1:
        bf = {k.replace("_", " ").title(): v for k, v in bd.items() if (v or 0) > 0}
        if bf:
            st.plotly_chart(_bar_chart(list(bf.keys()), list(bf.values()),
                "Feature Counts by Category", "#06b6d4"), use_container_width=True, key="prosca_pchart7")
        else:
            st.info("No features detected in any category.")
    with fd2:
        st.metric("Total Features Found", summary.get("total_features", 0))
        st.metric("Feature Density", f"{summary.get('feature_density_per_km2',0)} / km2")
        st.metric("Characterization", summary.get("characterization", "Unknown"))
        st.metric("Most Notable", summary.get("most_notable", "N/A"))

    # ══════════════════════════════════════════════════════════════════════════
    # DOWNLOAD REPORT
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    report = {
        "scan_timestamp": datetime.utcnow().isoformat(),
        "coordinates": {"latitude": lat, "longitude": lon},
        "terrain": terrain, "weather_now": weather_now, "soil_profile": soil_profile,
        "water_features": water_cats, "infrastructure": infrastructure,
        "nature": {
            "species_count": nature.get("species_count", 0),
            "kingdom_breakdown": nature.get("kingdom_breakdown", {}),
            "top_species": [{"scientific": s[0], "count": s[1], "common": s[2]}
                            for s in nature.get("top_species", [])
                            if isinstance(s, (list, tuple)) and len(s) >= 3],
            "protected_areas": nature.get("protected_areas", []),
            "protected_area_count": nature.get("protected_area_count", 0),
        },
        "hazards": hazards, "air_quality": air_quality,
        "geology": geo, "summary_stats": summary,
    }
    st.download_button(
        label="Download Proximity Scan Report (JSON)",
        data=json.dumps(report, indent=2, ensure_ascii=False, default=str),
        file_name=f"proximity_scan_{lat:.4f}_{lon:.4f}.json",
        mime="application/json", use_container_width=True)
