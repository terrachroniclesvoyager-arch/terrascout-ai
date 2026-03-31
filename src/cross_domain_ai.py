"""
TerraScout AI - Cross-Domain AI Reasoning Module
Collects data from multiple sources and finds non-obvious connections,
contradictions, and hidden patterns between different domains.
"""

import streamlit as st
import requests
import json
import math
from datetime import datetime


# ---------------------------------------------------------------------------
# DATA COLLECTION (6 free APIs, cached, timeout=10)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def _fetch_elevation(lat: float, lon: float) -> dict:
    """Open Topo Data - elevation."""
    try:
        r = requests.get(
            f"https://api.opentopodata.org/v1/srtm90m?locations={lat},{lon}",
            timeout=10,
        )
        r.raise_for_status()
        results = r.json().get("results", [])
        if results:
            return {"elevation_m": results[0].get("elevation"), "status": "ok"}
        return {"elevation_m": None, "status": "no_data"}
    except Exception as e:
        return {"elevation_m": None, "status": f"error: {e}"}


@st.cache_data(ttl=900)
def _fetch_slope(lat: float, lon: float) -> dict:
    """Derive slope from 3 nearby elevation samples via Open Topo Data."""
    delta = 0.001
    url = (
        f"https://api.opentopodata.org/v1/srtm90m?locations="
        f"{lat},{lon}|{lat+delta},{lon}|{lat},{lon+delta}"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        results = r.json().get("results", [])
        if len(results) >= 3:
            e0, e1, e2 = [(x.get("elevation") or 0) for x in results[:3]]
            dx = delta * 111_320 * math.cos(math.radians(lat))
            dy = delta * 111_320
            sx = (e2 - e0) / dx if dx else 0
            sy = (e1 - e0) / dy if dy else 0
            return {"slope_deg": round(math.degrees(math.atan(math.sqrt(sx**2 + sy**2))), 2), "status": "ok"}
        return {"slope_deg": None, "status": "no_data"}
    except Exception as e:
        return {"slope_deg": None, "status": f"error: {e}"}


@st.cache_data(ttl=900)
def _fetch_soil(lat: float, lon: float) -> dict:
    """ISRIC SoilGrids v2.0 - clay, sand, SOC, pH, CEC."""
    url = (
        f"https://rest.isric.org/soilgrids/v2.0/properties/query"
        f"?lon={lon}&lat={lat}"
        f"&property=clay&property=sand&property=soc&property=phh2o&property=cec"
        f"&depth=0-5cm&value=mean"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soil = r.json()
        # --- CORRECT SoilGrids v2.0 parsing ---
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

        return {
            "clay_pct": _sv("clay"), "sand_pct": _sv("sand"), "soc_g_kg": _sv("soc"),
            "ph": _sv("phh2o"), "cec": _sv("cec"), "status": "ok",
        }
    except Exception as e:
        return {"clay_pct": None, "sand_pct": None, "soc_g_kg": None,
                "ph": None, "cec": None, "status": f"error: {e}"}


@st.cache_data(ttl=900)
def _fetch_weather(lat: float, lon: float) -> dict:
    """Open-Meteo - temperature, precipitation, wind, humidity."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
        f"&timezone=auto&forecast_days=7"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        cur = data.get("current", {})
        daily = data.get("daily", {})
        precip_sum = sum(v for v in (daily.get("precipitation_sum") or []) if v) if daily else 0
        t_maxes = daily.get("temperature_2m_max") or []
        t_mins = daily.get("temperature_2m_min") or []
        t_range = round(max(t_maxes) - min(t_mins), 1) if t_maxes and t_mins else 0
        return {
            "temp_c": cur.get("temperature_2m"), "humidity_pct": cur.get("relative_humidity_2m"),
            "precip_mm": cur.get("precipitation"), "wind_kmh": cur.get("wind_speed_10m"),
            "weekly_precip_mm": round(precip_sum, 1), "temp_range_c": t_range, "status": "ok",
        }
    except Exception as e:
        return {"temp_c": None, "humidity_pct": None, "precip_mm": None,
                "wind_kmh": None, "weekly_precip_mm": 0, "temp_range_c": 0, "status": f"error: {e}"}


@st.cache_data(ttl=900)
def _fetch_air_quality(lat: float, lon: float) -> dict:
    """Open-Meteo Air Quality - PM2.5, PM10, AQI."""
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={lat}&longitude={lon}&current=pm2_5,pm10,european_aqi"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        cur = r.json().get("current", {})
        return {"pm25": cur.get("pm2_5"), "pm10": cur.get("pm10"),
                "aqi": cur.get("european_aqi"), "status": "ok"}
    except Exception as e:
        return {"pm25": None, "pm10": None, "aqi": None, "status": f"error: {e}"}


@st.cache_data(ttl=900)
def _fetch_infrastructure(lat: float, lon: float) -> dict:
    """Overpass API - separate counts for buildings, water, vegetation, industry."""
    radius = 2000
    results = {"buildings": 0, "water_bodies": 0, "vegetation": 0,
               "industrial": 0, "amenities": 0, "roads": 0, "status": "ok"}
    queries = {
        "buildings": f'[out:json][timeout:10];way["building"](around:{radius},{lat},{lon});out count;',
        "water_bodies": f'[out:json][timeout:10];way["natural"="water"](around:{radius},{lat},{lon});out count;',
        "vegetation": f'[out:json][timeout:10];(way["landuse"="forest"](around:{radius},{lat},{lon});way["landuse"="meadow"](around:{radius},{lat},{lon}););out count;',
        "industrial": f'[out:json][timeout:10];way["landuse"="industrial"](around:{radius},{lat},{lon});out count;',
        "amenities": f'[out:json][timeout:10];node["amenity"](around:{radius},{lat},{lon});out count;',
        "roads": f'[out:json][timeout:10];way["highway"](around:{radius},{lat},{lon});out count;',
    }
    url = "https://overpass-api.de/api/interpreter"
    for key, q in queries.items():
        try:
            r = requests.post(url, data={"data": q}, timeout=10)
            r.raise_for_status()
            elems = r.json().get("elements", [])
            if elems:
                cnt = elems[0].get("tags", {}).get("total", 0)
                results[key] = int(cnt) if cnt else 0
        except Exception:
            pass
    return results


@st.cache_data(ttl=900)
def _fetch_seismic(lat: float, lon: float) -> dict:
    """USGS Earthquake API - recent seismic activity within 200 km."""
    url = (
        f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson"
        f"&latitude={lat}&longitude={lon}&maxradiuskm=200&minmagnitude=2"
        f"&limit=20&orderby=time"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        features = r.json().get("features", [])
        mags = [f.get("properties", {}).get("mag", 0) or 0 for f in features]
        return {
            "quake_count": len(features),
            "max_magnitude": max(mags) if mags else 0,
            "avg_magnitude": round(sum(mags) / len(mags), 1) if mags else 0,
            "status": "ok",
        }
    except Exception as e:
        return {"quake_count": 0, "max_magnitude": 0, "avg_magnitude": 0, "status": f"error: {e}"}


# ---------------------------------------------------------------------------
# CROSS-DOMAIN CORRELATION ENGINE (12 pattern detectors)
# ---------------------------------------------------------------------------

def _run_correlations(elev, slope, soil, weather, air, infra, seismic):
    """Return list of insight dicts from 12 cross-domain pattern detectors."""
    insights = []

    def _g(d, k, default=0):
        v = d.get(k)
        return v if v is not None else default

    elevation = _g(elev, "elevation_m")
    slope_deg = _g(slope, "slope_deg")
    clay, sand, soc = _g(soil, "clay_pct"), _g(soil, "sand_pct"), _g(soil, "soc_g_kg")
    ph, cec = _g(soil, "ph", 7), _g(soil, "cec")
    temp, humidity = _g(weather, "temp_c", 20), _g(weather, "humidity_pct", 50)
    wind = _g(weather, "wind_kmh")
    weekly_precip = _g(weather, "weekly_precip_mm")
    temp_range = _g(weather, "temp_range_c")
    pm25, pm10, aqi = _g(air, "pm25"), _g(air, "pm10"), _g(air, "aqi")
    buildings, water_bodies = _g(infra, "buildings"), _g(infra, "water_bodies")
    vegetation, industrial = _g(infra, "vegetation"), _g(infra, "industrial")
    amenities, roads = _g(infra, "amenities"), _g(infra, "roads")
    quakes, max_mag = _g(seismic, "quake_count"), _g(seismic, "max_magnitude")

    # 1. Soil-Climate Nexus
    if soc > 2 and weekly_precip > 30:
        conf = "HIGH" if soc > 4 and weekly_precip > 60 else "MEDIUM"
        insights.append({
            "id": "soil_climate_nexus", "title": "Carbon Sink Potential Detected",
            "icon": "leaf", "confidence": conf, "type": "opportunity",
            "description": (
                f"High soil organic carbon ({soc:.1f} g/kg) combined with substantial "
                f"precipitation ({weekly_precip:.0f} mm/week) suggests this area acts as "
                f"a natural carbon sink. Soil-climate coupling reinforces carbon storage."),
            "recommendation": "Preserve existing land cover to maintain carbon sequestration. "
                "Consider soil conservation programs and avoid deep tillage.",
            "domains": ["Soil", "Climate"],
            "score": min(soc * 10 + weekly_precip, 100),
        })

    # 2. Erosion Risk Triangle
    if slope_deg > 10 and clay > 25 and weekly_precip > 40:
        conf = "HIGH" if slope_deg > 20 and clay > 35 else "MEDIUM"
        insights.append({
            "id": "erosion_risk_triangle", "title": "Landslide / Erosion Alert",
            "icon": "warning", "confidence": conf, "type": "risk",
            "description": (
                f"Dangerous combination: steep slope ({slope_deg:.1f} deg), clay-rich soil "
                f"({clay:.0f}%), and heavy rainfall ({weekly_precip:.0f} mm/week). "
                f"Clay soils become unstable when saturated on steep terrain."),
            "recommendation": "Implement terracing or retaining structures. Monitor soil moisture. "
                "Avoid construction on slopes >15 deg in clay-rich zones.",
            "domains": ["Terrain", "Soil", "Climate"],
            "score": min(slope_deg * 2 + clay + weekly_precip * 0.5, 100),
        })

    # 3. Urban Heat Island
    if buildings > 200 and vegetation < 20:
        conf = "HIGH" if buildings > 500 and vegetation < 5 else "MEDIUM"
        insights.append({
            "id": "urban_heat_island", "title": "Urban Heat Island Effect",
            "icon": "thermometer", "confidence": conf, "type": "risk",
            "description": (
                f"Dense building coverage ({buildings} structures) with minimal green space "
                f"({vegetation} vegetation areas) creates urban heat island conditions, "
                f"amplifying local temperatures by 2-5 C."),
            "recommendation": "Increase urban tree canopy. Install green roofs and cool pavements. "
                "Create pocket parks to break heat-trapping surfaces.",
            "domains": ["Infrastructure", "Vegetation"],
            "score": min(buildings * 0.15 + (100 - vegetation * 5), 100),
        })

    # 4. Water Stress
    if weekly_precip < 10 and sand > 40 and water_bodies < 3:
        conf = "HIGH" if weekly_precip < 3 and sand > 60 else "MEDIUM"
        insights.append({
            "id": "water_stress", "title": "Water Stress / Drought Risk",
            "icon": "droplet", "confidence": conf, "type": "risk",
            "description": (
                f"Low precipitation ({weekly_precip:.1f} mm/week), sandy soil ({sand:.0f}%) "
                f"with poor water retention, and few water bodies ({water_bodies}) "
                f"indicate significant water stress."),
            "recommendation": "Develop rainwater harvesting. Plant drought-resistant species. "
                "Investigate groundwater reserves and implement water recycling.",
            "domains": ["Climate", "Soil", "Hydrology"],
            "score": min((100 - weekly_precip * 5) + sand * 0.5, 100),
        })

    # 5. Seismic-Infrastructure Risk
    if quakes > 3 and buildings > 100:
        conf = "HIGH" if max_mag > 4 and buildings > 300 else "MEDIUM"
        insights.append({
            "id": "seismic_infrastructure", "title": "Seismic Collapse Risk",
            "icon": "zap", "confidence": conf, "type": "risk",
            "description": (
                f"Active seismic zone ({quakes} recent earthquakes, max M{max_mag:.1f}) "
                f"with dense building stock ({buildings} structures) elevates structural "
                f"collapse risk significantly."),
            "recommendation": "Conduct seismic vulnerability assessments on critical buildings. "
                "Enforce earthquake-resistant codes. Prepare emergency response plans.",
            "domains": ["Seismic", "Infrastructure"],
            "score": min(quakes * 10 + max_mag * 15 + buildings * 0.1, 100),
        })

    # 6. Air-Vegetation Filtration Gap
    if vegetation < 10 and aqi > 40:
        conf = "HIGH" if aqi > 80 and vegetation < 3 else "MEDIUM"
        insights.append({
            "id": "air_vegetation_gap", "title": "Poor Natural Air Filtration",
            "icon": "wind", "confidence": conf, "type": "risk",
            "description": (
                f"Low vegetation ({vegetation} areas) with elevated AQI ({aqi}) means "
                f"natural filtration is insufficient. PM2.5={pm25}, PM10={pm10} ug/m3."),
            "recommendation": "Plant pollution-absorbing trees (London Plane, Silver Birch). "
                "Create green buffer zones along roads and industrial areas.",
            "domains": ["Air Quality", "Vegetation"],
            "score": min(aqi + (100 - vegetation * 10), 100),
        })

    # 7. Agriculture Paradox
    fertile = soc > 1.5 and cec > 10 and 5.5 < ph < 7.5
    poor_climate = temp_range > 20 or weekly_precip < 5 or temp > 40 or temp < 0
    if fertile and poor_climate:
        insights.append({
            "id": "agriculture_paradox", "title": "Agricultural Paradox - Wasted Potential",
            "icon": "sprout", "confidence": "MEDIUM", "type": "contradiction",
            "description": (
                f"Fertile soil (SOC={soc:.1f}, CEC={cec:.0f}, pH={ph:.1f}) but challenging "
                f"climate (range={temp_range:.0f} C, precip={weekly_precip:.0f} mm/week). "
                f"Good soil potential is underutilized."),
            "recommendation": "Consider greenhouse agriculture and irrigation systems. "
                "Select crop varieties adapted to extreme temperature ranges.",
            "domains": ["Soil", "Climate", "Agriculture"], "score": 65,
        })

    # 8. Renewable Energy Opportunity
    if wind > 15 and elevation > 200 and slope_deg < 10:
        conf = "HIGH" if wind > 25 and elevation > 500 else "MEDIUM"
        insights.append({
            "id": "energy_terrain", "title": "Wind Energy Opportunity",
            "icon": "turbine", "confidence": conf, "type": "opportunity",
            "description": (
                f"Strong winds ({wind:.0f} km/h) at elevation ({elevation:.0f} m) with "
                f"gentle slope ({slope_deg:.1f} deg) - ideal for wind turbines."),
            "recommendation": "Conduct 12-month wind resource assessment. "
                "Evaluate grid connection and zoning regulations.",
            "domains": ["Climate", "Terrain", "Energy"],
            "score": min(wind * 3 + elevation * 0.05, 100),
        })

    # 9. Biodiversity Corridor
    if water_bodies > 2 and vegetation > 10 and buildings < 50 and industrial < 2:
        conf = "HIGH" if vegetation > 30 and water_bodies > 5 else "MEDIUM"
        insights.append({
            "id": "biodiversity_corridor", "title": "Wildlife Corridor Potential",
            "icon": "paw", "confidence": conf, "type": "opportunity",
            "description": (
                f"Water features ({water_bodies}), vegetation ({vegetation} areas), and low "
                f"human impact ({buildings} buildings) create biodiversity corridor conditions."),
            "recommendation": "Designate as ecological corridor. Restrict new development. "
                "Install wildlife crossings. Monitor species diversity.",
            "domains": ["Hydrology", "Vegetation", "Infrastructure"],
            "score": min(water_bodies * 10 + vegetation * 3, 100),
        })

    # 10. Contamination Pathway
    if industrial > 2 and water_bodies > 0 and slope_deg > 2:
        conf = "HIGH" if industrial > 5 else "MEDIUM"
        insights.append({
            "id": "contamination_path", "title": "Pollution Pathway Detected",
            "icon": "alert-triangle", "confidence": conf, "type": "risk",
            "description": (
                f"Industrial sites ({industrial}) on sloped terrain ({slope_deg:.1f} deg) "
                f"with downhill water bodies ({water_bodies}) creates a contamination "
                f"pathway via surface runoff."),
            "recommendation": "Install downstream monitoring stations. Require spill containment. "
                "Create vegetative buffer strips between industry and waterways.",
            "domains": ["Infrastructure", "Terrain", "Hydrology"],
            "score": min(industrial * 15 + slope_deg * 3, 100),
        })

    # 11. Settlement Paradox
    good_services = amenities > 50 and roads > 100
    high_hazards = quakes > 5 or max_mag > 4 or (slope_deg > 15 and weekly_precip > 50)
    if good_services and high_hazards:
        insights.append({
            "id": "settlement_paradox", "title": "Risk-Benefit Tension in Settlement",
            "icon": "building", "confidence": "MEDIUM", "type": "contradiction",
            "description": (
                f"Well-served area ({amenities} amenities, {roads} roads) exposed to "
                f"significant hazards (quakes={quakes}, slope={slope_deg:.0f} deg). "
                f"People accept elevated risk for urban benefits."),
            "recommendation": "Develop hazard-aware urban planning. Ensure evacuation routes. "
                "Invest in early warning systems while maintaining service quality.",
            "domains": ["Infrastructure", "Seismic", "Terrain"], "score": 70,
        })

    # 12. Climate Adaptation Gap
    extreme_temps = temp > 38 or temp < -5 or temp_range > 25
    poor_infra = amenities < 10 and roads < 30
    if extreme_temps and poor_infra:
        insights.append({
            "id": "climate_adaptation_gap", "title": "Climate Vulnerability Gap",
            "icon": "shield-off", "confidence": "HIGH", "type": "risk",
            "description": (
                f"Extreme temperatures (current={temp:.1f} C, range={temp_range:.0f} C) "
                f"with limited infrastructure ({amenities} amenities, {roads} roads) "
                f"indicates a critical adaptation gap."),
            "recommendation": "Prioritize climate-resilient infrastructure investments. "
                "Establish cooling/warming centers. Improve road connectivity for emergencies.",
            "domains": ["Climate", "Infrastructure"], "score": 85,
        })

    return insights


# ---------------------------------------------------------------------------
# CONTRADICTION DETECTOR
# ---------------------------------------------------------------------------

def _find_contradictions(elev, slope, soil, weather, air, infra, seismic):
    """Detect when data sources provide conflicting signals."""
    contradictions = []
    elevation = (elev.get("elevation_m") or 0)
    temp = (weather.get("temp_c") or 20)
    humidity = (weather.get("humidity_pct") or 50)
    precip = (weather.get("weekly_precip_mm") or 0)
    aqi = (air.get("aqi") or 0)
    vegetation = (infra.get("vegetation") or 0)
    buildings = (infra.get("buildings") or 0)

    if elevation > 1500 and temp > 25:
        contradictions.append({
            "title": "Altitude-Temperature Mismatch",
            "description": f"Elevation {elevation:.0f}m but temp {temp:.1f} C. Normally drops "
                f"~6.5 C/1000m. Possible foehn effect or urban heat influence.",
            "domains": ["Terrain", "Climate"],
        })
    if vegetation > 20 and aqi > 60:
        contradictions.append({
            "title": "Green Area with Poor Air Quality",
            "description": f"Substantial vegetation ({vegetation} areas) yet AQI={aqi}. "
                f"Nearby pollution source may overwhelm natural filtration.",
            "domains": ["Vegetation", "Air Quality"],
        })
    if precip > 30 and humidity < 30:
        contradictions.append({
            "title": "Precipitation-Humidity Discrepancy",
            "description": f"Weekly precip {precip:.0f}mm but humidity only {humidity:.0f}%. "
                f"Possible rapid evaporation or recent weather shift.",
            "domains": ["Climate"],
        })
    if buildings > 200 and (infra.get("amenities") or 0) < 5:
        contradictions.append({
            "title": "Dense Development but Few Services",
            "description": f"High building density ({buildings}) but few amenities "
                f"({infra.get('amenities', 0)}). Possible dormitory suburb or OSM data gap.",
            "domains": ["Infrastructure"],
        })
    return contradictions


# ---------------------------------------------------------------------------
# CORRELATION MATRIX
# ---------------------------------------------------------------------------

def _build_correlation_matrix(elev, slope, soil, weather, air, infra, seismic):
    """Build domain-vs-domain interaction strength matrix."""
    domains = ["Terrain", "Soil", "Climate", "Air Quality", "Infrastructure", "Seismic"]

    def _norm(v, lo, hi):
        if v is None:
            return 50
        return max(0, min(100, (v - lo) / (hi - lo) * 100)) if hi != lo else 50

    scores = {
        "Terrain": _norm((slope.get("slope_deg") or 0), 0, 45),
        "Soil": _norm((soil.get("clay_pct") or 0), 0, 60),
        "Climate": _norm((weather.get("weekly_precip_mm") or 0), 0, 100),
        "Air Quality": _norm((air.get("aqi") or 0), 0, 100),
        "Infrastructure": _norm((infra.get("buildings") or 0), 0, 500),
        "Seismic": _norm((seismic.get("quake_count") or 0), 0, 20),
    }
    matrix = {}
    for d1 in domains:
        matrix[d1] = {}
        for d2 in domains:
            matrix[d1][d2] = 100 if d1 == d2 else round(math.sqrt(scores[d1] * scores[d2]), 1)
    return {"domains": domains, "scores": scores, "matrix": matrix}


# ---------------------------------------------------------------------------
# UI RENDERING HELPERS
# ---------------------------------------------------------------------------

def _status_html(status):
    if status == "ok":
        return '<span style="color:#22c55e;font-weight:700;">&#9679; Connected</span>'
    if status == "no_data":
        return '<span style="color:#eab308;font-weight:700;">&#9679; No Data</span>'
    return '<span style="color:#ef4444;font-weight:700;">&#9679; Error</span>'


def _confidence_badge(conf):
    colors = {"HIGH": "#ef4444", "MEDIUM": "#f59e0b", "LOW": "#3b82f6"}
    c = colors.get(conf, "#6b7280")
    return (f'<span style="background:{c};color:white;padding:2px 10px;'
            f'border-radius:12px;font-size:0.75rem;font-weight:700;">{conf}</span>')


def _type_badge(t):
    cfg = {"risk": ("#fee2e2", "#991b1b", "RISK"),
           "opportunity": ("#dcfce7", "#166534", "OPPORTUNITY"),
           "contradiction": ("#fef9c3", "#854d0e", "CONTRADICTION")}
    bg, fg, label = cfg.get(t, ("#f3f4f6", "#374151", t.upper()))
    return (f'<span style="background:{bg};color:{fg};padding:2px 10px;'
            f'border-radius:12px;font-size:0.75rem;font-weight:700;">{label}</span>')


_ICON_MAP = {
    "leaf": "&#127811;", "warning": "&#9888;&#65039;", "thermometer": "&#127777;&#65039;",
    "droplet": "&#128167;", "zap": "&#9889;", "wind": "&#127744;",
    "sprout": "&#127793;", "turbine": "&#9881;&#65039;", "paw": "&#128062;",
    "alert-triangle": "&#9888;&#65039;", "building": "&#127959;&#65039;",
    "shield-off": "&#128737;&#65039;",
}


def _render_insight_card(insight):
    """Render a styled card for one cross-domain insight."""
    bc = {"risk": "#ef4444", "opportunity": "#22c55e", "contradiction": "#eab308"}.get(
        insight["type"], "#6b7280")
    icon_html = _ICON_MAP.get(insight.get("icon", ""), "&#128269;")
    domains_str = " + ".join(insight.get("domains", []))
    st.markdown(f"""
    <div style="border-left:4px solid {bc};background:#1e1e2e;padding:16px 20px;
                 border-radius:8px;margin-bottom:12px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <span style="font-size:1.1rem;font-weight:700;color:#e2e8f0;">
                {icon_html} {insight['title']}</span>
            <span>{_confidence_badge(insight['confidence'])} {_type_badge(insight['type'])}</span>
        </div>
        <div style="color:#94a3b8;font-size:0.9rem;margin-bottom:8px;">
            <strong>Domains:</strong> {domains_str}</div>
        <div style="color:#cbd5e1;font-size:0.9rem;margin-bottom:10px;">
            {insight['description']}</div>
        <div style="background:#2d2d3f;padding:10px 14px;border-radius:6px;
                    color:#a5b4fc;font-size:0.85rem;">
            <strong>&#128161; Recommendation:</strong> {insight['recommendation']}</div>
    </div>""", unsafe_allow_html=True)


def _render_contradiction_card(c):
    """Render a contradiction alert card."""
    domains_str = " + ".join(c.get("domains", []))
    st.markdown(f"""
    <div style="border-left:4px solid #eab308;background:#1e1e2e;padding:14px 18px;
                 border-radius:8px;margin-bottom:10px;">
        <div style="font-size:1rem;font-weight:700;color:#fbbf24;margin-bottom:6px;">
            &#9888;&#65039; {c['title']}</div>
        <div style="color:#94a3b8;font-size:0.85rem;margin-bottom:4px;">
            <strong>Domains:</strong> {domains_str}</div>
        <div style="color:#cbd5e1;font-size:0.88rem;">{c['description']}</div>
    </div>""", unsafe_allow_html=True)


def _render_data_collection_panel(sources):
    """Show data source status with preview values."""
    st.markdown("### Data Collection Panel")
    cols = st.columns(3)
    labels = [
        ("Open Topo Data", "elevation"), ("ISRIC SoilGrids", "soil"),
        ("Open-Meteo Weather", "weather"), ("Open-Meteo Air Quality", "air"),
        ("Overpass / OSM", "infrastructure"), ("USGS Earthquakes", "seismic"),
    ]
    for idx, (label, key) in enumerate(labels):
        with cols[idx % 3]:
            src = sources.get(key, {})
            status = src.get("status", "error")
            st.markdown(f"**{label}**")
            st.markdown(_status_html(status), unsafe_allow_html=True)
            if status == "ok":
                preview = {k: v for k, v in src.items() if k != "status" and v is not None}
                if preview:
                    lines = []
                    for k, v in list(preview.items())[:4]:
                        lines.append(f"  {k}: {v:.2f}" if isinstance(v, float) else f"  {k}: {v}")
                    st.code("\n".join(lines), language="yaml")
            st.markdown("---")


def _render_correlation_heatmap(corr_data):
    """Render correlation matrix heatmap (plotly preferred, table fallback)."""
    st.markdown("### Correlation Matrix")
    domains = corr_data["domains"]
    matrix = corr_data["matrix"]
    try:
        import plotly.graph_objects as go
        z = [[matrix[d1][d2] for d2 in domains] for d1 in domains]
        fig = go.Figure(data=go.Heatmap(
            z=z, x=domains, y=domains, colorscale="RdYlGn",
            text=[[f"{matrix[d1][d2]:.0f}" for d2 in domains] for d1 in domains],
            texttemplate="%{text}",
            hovertemplate="<b>%{y}</b> x <b>%{x}</b><br>Coupling: %{z:.1f}<extra></extra>",
        ))
        fig.update_layout(
            height=420, margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e2e8f0"),
            title=dict(text="Domain Interaction Strength", font=dict(size=14)),
        )
        st.plotly_chart(fig, use_container_width=True, key="xdom_heatmap")
    except ImportError:
        import pandas as pd
        st.dataframe(pd.DataFrame(matrix).T.style.background_gradient(cmap="RdYlGn"),
                      use_container_width=True)


def _render_domain_stats(elev, slope, soil, weather, air, infra, seismic):
    """Compact overview of all domain values."""
    st.markdown("### Domain Data Overview")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Terrain**")
        st.metric("Elevation", f"{(elev.get('elevation_m') or 0):.0f} m")
        st.metric("Slope", f"{(slope.get('slope_deg') or 0):.1f} deg")
        st.markdown("**Soil**")
        st.metric("Clay", f"{(soil.get('clay_pct') or 0):.1f} %")
        st.metric("Sand", f"{(soil.get('sand_pct') or 0):.1f} %")
        st.metric("SOC", f"{(soil.get('soc_g_kg') or 0):.1f} g/kg")
        st.metric("pH", f"{(soil.get('ph') or 0):.1f}")
    with c2:
        st.markdown("**Climate**")
        st.metric("Temperature", f"{(weather.get('temp_c') or 0):.1f} C")
        st.metric("Humidity", f"{(weather.get('humidity_pct') or 0):.0f} %")
        st.metric("Wind", f"{(weather.get('wind_kmh') or 0):.0f} km/h")
        st.metric("Weekly Precip", f"{(weather.get('weekly_precip_mm') or 0):.1f} mm")
        st.markdown("**Air Quality**")
        st.metric("PM2.5", f"{(air.get('pm25') or 0):.1f} ug/m3")
        st.metric("AQI", f"{(air.get('aqi') or 0)}")
    with c3:
        st.markdown("**Infrastructure**")
        st.metric("Buildings", f"{infra.get('buildings', 0)}")
        st.metric("Water Bodies", f"{infra.get('water_bodies', 0)}")
        st.metric("Vegetation", f"{infra.get('vegetation', 0)}")
        st.metric("Industrial", f"{infra.get('industrial', 0)}")
        st.metric("Amenities", f"{infra.get('amenities', 0)}")
        st.markdown("**Seismic**")
        st.metric("Earthquakes (200km)", f"{seismic.get('quake_count', 0)}")
        st.metric("Max Magnitude", f"{(seismic.get('max_magnitude') or 0):.1f}")


def _render_summary_panel(insights, contradictions):
    """Key findings, opportunities, risks, and contradiction panels."""
    sorted_insights = sorted(insights, key=lambda x: x.get("score", 0), reverse=True)

    # Key Findings (top 5)
    st.markdown("### Key Findings")
    if not sorted_insights:
        st.info("No significant cross-domain patterns detected at this location.")
    else:
        for i, ins in enumerate(sorted_insights[:5], 1):
            st.markdown(
                f"**{i}.** {_type_badge(ins['type'])} {_confidence_badge(ins['confidence'])} "
                f"**{ins['title']}** &mdash; Score: {ins.get('score', 0):.0f}/100",
                unsafe_allow_html=True)

    st.markdown("---")
    opportunities = [i for i in sorted_insights if i["type"] == "opportunity"]
    risks = [i for i in sorted_insights if i["type"] == "risk"]
    contradiction_ins = [i for i in sorted_insights if i["type"] == "contradiction"]

    col_opp, col_risk = st.columns(2)
    with col_opp:
        st.markdown("### Opportunities")
        if opportunities:
            for opp in opportunities:
                st.markdown(
                    f'<div style="background:#052e16;padding:10px 14px;border-radius:8px;'
                    f'margin-bottom:8px;border-left:3px solid #22c55e;">'
                    f'<strong style="color:#86efac;">{opp["title"]}</strong><br>'
                    f'<span style="color:#bbf7d0;font-size:0.85rem;">{opp["recommendation"]}</span>'
                    f'</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#6b7280;font-style:italic;">No opportunities detected.</div>',
                        unsafe_allow_html=True)

    with col_risk:
        st.markdown("### Risks")
        if risks:
            for r in risks:
                st.markdown(
                    f'<div style="background:#450a0a;padding:10px 14px;border-radius:8px;'
                    f'margin-bottom:8px;border-left:3px solid #ef4444;">'
                    f'<strong style="color:#fca5a5;">{r["title"]}</strong><br>'
                    f'<span style="color:#fecaca;font-size:0.85rem;">{r["recommendation"]}</span>'
                    f'</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#6b7280;font-style:italic;">No significant risks detected.</div>',
                        unsafe_allow_html=True)

    # Contradiction alerts
    if contradictions or contradiction_ins:
        st.markdown("---")
        st.markdown("### Contradiction Alerts")
        st.caption("When data from different domains tells conflicting stories")
        for c in contradictions:
            _render_contradiction_card(c)
        for ci in contradiction_ins:
            _render_contradiction_card({
                "title": ci["title"], "description": ci["description"],
                "domains": ci.get("domains", []),
            })


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def render_cross_domain_ai_tab():
    """Main entry point for Cross-Domain AI Reasoning tab."""
    st.markdown("## Cross-Domain AI Reasoning")
    st.caption("Hidden patterns, contradictions & non-obvious connections across data domains")

    c1, c2 = st.columns(2)
    lat = c1.number_input("Latitude", value=41.9, format="%.4f", key="xdom_lat")
    lon = c2.number_input("Longitude", value=12.5, format="%.4f", key="xdom_lon")

    analysis_radius = st.select_slider(
        "Analysis Radius",
        options=["Local (2 km)", "District (5 km)", "Regional (10 km)"],
        value="Local (2 km)", key="xdom_radius",
    )

    if st.button("Analyze Cross-Domain Connections", key="xdom_btn", type="primary"):
        progress = st.progress(0, text="Initializing cross-domain analysis...")
        st.markdown("---")

        # Phase 1: Data collection
        progress.progress(5, text="Fetching elevation data...")
        elev_data = _fetch_elevation(lat, lon)
        progress.progress(15, text="Computing slope...")
        slope_data = _fetch_slope(lat, lon)
        progress.progress(25, text="Querying SoilGrids v2.0...")
        soil_data = _fetch_soil(lat, lon)
        progress.progress(40, text="Fetching weather data...")
        weather_data = _fetch_weather(lat, lon)
        progress.progress(50, text="Checking air quality...")
        air_data = _fetch_air_quality(lat, lon)
        progress.progress(60, text="Scanning infrastructure (Overpass)...")
        infra_data = _fetch_infrastructure(lat, lon)
        progress.progress(75, text="Querying USGS seismic data...")
        seismic_data = _fetch_seismic(lat, lon)
        progress.progress(85, text="Running cross-domain correlation engine...")

        sources = {
            "elevation": {**elev_data, **slope_data, "status": elev_data.get("status", "error")},
            "soil": soil_data, "weather": weather_data, "air": air_data,
            "infrastructure": infra_data, "seismic": seismic_data,
        }

        # Phase 2: Cross-domain analysis
        insights = _run_correlations(elev_data, slope_data, soil_data,
                                     weather_data, air_data, infra_data, seismic_data)
        contradictions = _find_contradictions(elev_data, slope_data, soil_data,
                                             weather_data, air_data, infra_data, seismic_data)
        corr_matrix = _build_correlation_matrix(elev_data, slope_data, soil_data,
                                                weather_data, air_data, infra_data, seismic_data)
        progress.progress(95, text="Rendering results...")

        # Phase 3: Render UI
        _render_data_collection_panel(sources)
        st.markdown("---")
        _render_domain_stats(elev_data, slope_data, soil_data,
                             weather_data, air_data, infra_data, seismic_data)
        st.markdown("---")
        _render_correlation_heatmap(corr_matrix)
        st.markdown("---")

        st.markdown("### Cross-Domain Insights")
        st.caption(f"Found **{len(insights)}** cross-domain patterns and "
                   f"**{len(contradictions)}** contradictions")
        if insights:
            for ins in sorted(insights, key=lambda x: x.get("score", 0), reverse=True):
                _render_insight_card(ins)
        else:
            st.info("No strong cross-domain correlations detected. This may indicate a "
                    "balanced environment or the location falls outside detector thresholds.")

        st.markdown("---")
        _render_summary_panel(insights, contradictions)

        # Analysis metadata
        st.markdown("---")
        st.markdown("### Analysis Metadata")
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Data Sources Queried", "6")
        mc2.metric("Pattern Detectors", "12")
        mc3.metric("Insights Generated", f"{len(insights) + len(contradictions)}")
        st.caption(f"Completed {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                   f"{lat:.4f}, {lon:.4f} | {analysis_radius}")
        progress.progress(100, text="Analysis complete.")
