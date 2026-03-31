"""
Mining Suitability Assessment module for TerraScout AI.
Evaluates a location's suitability for mining operations by analyzing
geology (Macrostrat), terrain (Open Topo Data), soil composition (SoilGrids),
infrastructure access (Overpass), environmental constraints, climate (Open-Meteo),
and seismic risk (USGS Earthquakes). Produces a composite 0-100 suitability score
with GO / CAUTION / NO-GO verdict and recommended mining type.
All APIs are free and require no API keys.
"""

import streamlit as st
import requests
import json
import math

try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except Exception:
    HAS_FOLIUM = False

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except Exception:
    HAS_PLOTLY = False

# ═══════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════
MACROSTRAT_URL = "https://macrostrat.org/api/geologic_units/map"
OPEN_TOPO_URL = "https://api.opentopodata.org/v1/srtm30m"
SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
USGS_EQ_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# ═══════════════════════════════════════════════════
# ROCK CLASSIFICATIONS
# ═══════════════════════════════════════════════════
HIGH_MINERAL_ROCKS = {
    "granite", "gabbro", "diorite", "basalt", "rhyolite", "andesite",
    "peridotite", "kimberlite", "pegmatite", "porphyry", "syenite",
    "gneiss", "schist", "amphibolite", "eclogite", "migmatite",
    "serpentinite", "quartzite", "hornfels", "skarn", "greisen",
}
MODERATE_MINERAL_ROCKS = {
    "sandstone", "conglomerate", "breccia", "limestone", "dolomite",
    "marble", "slate", "phyllite", "chert", "iron formation",
    "laterite", "bauxite", "phosphorite",
}

# ═══════════════════════════════════════════════════
# PRESET LOCATIONS (famous mining districts)
# ═══════════════════════════════════════════════════
MINING_PRESETS = {
    "Custom": None,
    "Witwatersrand, South Africa": (-26.17, 27.90),
    "Pilbara, Australia": (-22.30, 119.80),
    "Sudbury Basin, Canada": (46.49, -81.00),
    "Atacama Desert, Chile": (-23.86, -69.14),
    "Norilsk, Russia": (69.35, 88.20),
    "Carajas, Brazil": (-6.06, -50.17),
    "Bingham Canyon, Utah": (40.52, -112.15),
    "Kimberley, South Africa": (-28.73, 24.76),
    "Mount Isa, Australia": (-20.73, 139.49),
    "Potosi, Bolivia": (-19.59, -65.75),
    "Kiruna, Sweden": (67.86, 20.22),
    "Broken Hill, Australia": (-31.95, 141.47),
    "Nevada Gold Belt, USA": (40.83, -117.48),
    "Zambian Copperbelt": (-12.80, 28.24),
    "Cornwall Tin District, UK": (50.26, -5.05),
}

# ═══════════════════════════════════════════════════
# API FUNCTIONS (cached, timeout=10, try/except)
# ═══════════════════════════════════════════════════

@st.cache_data(ttl=900)
def _fetch_geology(lat: float, lon: float) -> dict:
    try:
        r = requests.get(MACROSTRAT_URL, params={"lat": lat, "lng": lon, "response": "long"}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=900)
def _fetch_elevation(lat: float, lon: float) -> dict:
    try:
        r = requests.get(OPEN_TOPO_URL, params={"locations": f"{lat},{lon}"}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=900)
def _fetch_elevation_grid(lat: float, lon: float, step: float = 0.01, n: int = 5) -> dict:
    half = n // 2
    pts = [f"{lat + i*step},{lon + j*step}" for i in range(-half, half+1) for j in range(-half, half+1)]
    try:
        r = requests.get(OPEN_TOPO_URL, params={"locations": "|".join(pts)}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=900)
def _fetch_soil(lat: float, lon: float) -> dict:
    try:
        r = requests.get(SOILGRIDS_URL, params={
            "lon": lon, "lat": lat,
            "property": ["clay", "sand", "silt", "soc", "bdod"],
            "depth": ["0-5cm", "5-15cm"], "value": "mean",
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=900)
def _fetch_infrastructure(lat: float, lon: float, radius_km: int = 25) -> dict:
    rm = radius_km * 1000
    query = f"""[out:json][timeout:25];(
      way["highway"~"motorway|trunk|primary|secondary"](around:{rm},{lat},{lon});
      way["railway"~"rail"](around:{rm},{lat},{lon});
      node["man_made"="mineshaft"](around:{rm},{lat},{lon});
      node["man_made"="adit"](around:{rm},{lat},{lon});
      way["landuse"="quarry"](around:{rm},{lat},{lon});
      node["landuse"="quarry"](around:{rm},{lat},{lon});
      way["landuse"="industrial"](around:{rm},{lat},{lon});
      node["leisure"="nature_reserve"](around:{rm},{lat},{lon});
      way["leisure"="nature_reserve"](around:{rm},{lat},{lon});
      way["boundary"="national_park"](around:{rm},{lat},{lon});
      relation["boundary"="national_park"](around:{rm},{lat},{lon});
      way["natural"="water"](around:{rm},{lat},{lon});
      node["natural"="water"](around:{rm},{lat},{lon});
      way["waterway"~"river|stream"](around:{rm},{lat},{lon});
    );out center body 200;"""
    try:
        r = requests.get(OVERPASS_URL, params={"data": query}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=900)
def _fetch_climate(lat: float, lon: float) -> dict:
    try:
        r = requests.get(OPEN_METEO_URL, params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,precipitation,wind_speed_10m",
            "daily": "precipitation_sum", "forecast_days": 14, "timezone": "auto",
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

@st.cache_data(ttl=900)
def _fetch_earthquakes(lat: float, lon: float) -> dict:
    try:
        r = requests.get(USGS_EQ_URL, params={
            "format": "geojson", "latitude": lat, "longitude": lon,
            "maxradiuskm": 150, "minmagnitude": 3, "limit": 50,
        }, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}

# ═══════════════════════════════════════════════════
# HELPER / ANALYSIS FUNCTIONS
# ═══════════════════════════════════════════════════

def _haversine(lat1, lon1, lat2, lon2):
    """Distance in km between two lat/lon points."""
    R = 6371.0
    rlat1, rlon1, rlat2, rlon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = rlat2 - rlat1, rlon2 - rlon1
    a = math.sin(dlat/2)**2 + math.cos(rlat1)*math.cos(rlat2)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _element_latlon(el):
    """Extract lat/lon from an Overpass element."""
    if el.get("type") == "node":
        return el.get("lat"), el.get("lon")
    c = el.get("center", {})
    return (c.get("lat"), c.get("lon")) if c else (None, None)

def _classify_elements(elements, lat, lon):
    """Classify Overpass elements into categories with distances."""
    cats = {k: [] for k in ("roads", "railways", "mines", "quarries",
                             "industrial", "protected", "water")}
    for el in elements:
        tags = el.get("tags", {})
        elat, elon = _element_latlon(el)
        if elat is None or elon is None:
            continue
        entry = {"lat": elat, "lon": elon, "dist_km": round(_haversine(lat, lon, elat, elon), 2), "tags": tags}
        if tags.get("highway"):
            cats["roads"].append(entry)
        elif tags.get("railway"):
            cats["railways"].append(entry)
        elif tags.get("man_made") in ("mineshaft", "adit"):
            cats["mines"].append(entry)
        elif tags.get("landuse") == "quarry":
            cats["quarries"].append(entry)
        elif tags.get("landuse") == "industrial":
            cats["industrial"].append(entry)
        elif tags.get("leisure") == "nature_reserve" or tags.get("boundary") == "national_park":
            cats["protected"].append(entry)
        elif tags.get("natural") == "water" or tags.get("waterway"):
            cats["water"].append(entry)
    for k in cats:
        cats[k].sort(key=lambda x: x["dist_km"])
    return cats

def _nearest(cat_list):
    """Distance to nearest feature, or None."""
    return cat_list[0]["dist_km"] if cat_list else None

def _compute_slope(elevations, step_m):
    """Average slope in degrees from elevation grid."""
    n = int(math.sqrt(len(elevations)))
    if n < 2:
        return 0.0
    slopes = []
    for i in range(n):
        for j in range(n):
            idx = i * n + j
            if j < n - 1:
                slopes.append(math.degrees(math.atan2(abs(elevations[idx] - elevations[idx+1]), step_m)))
            if i < n - 1:
                slopes.append(math.degrees(math.atan2(abs(elevations[idx] - elevations[idx+n]), step_m)))
    return sum(slopes) / len(slopes) if slopes else 0.0

def _terrain_roughness(elevations):
    """Terrain Roughness Index (std-dev of elevations)."""
    if len(elevations) < 2:
        return 0.0
    mu = sum(elevations) / len(elevations)
    return math.sqrt(sum((e - mu)**2 for e in elevations) / len(elevations))

# ── Scoring helpers ──

def _geology_score(geo_data):
    """Return (score, lithology, description, age)."""
    if "error" in geo_data:
        return 50, "Unknown", "No geological data available", "Unknown"
    features = geo_data.get("success", {}).get("data", [])
    if not features:
        return 50, "Unknown", "No geological units returned", "Unknown"
    unit = features[0]
    lith = (unit.get("lith") or "unknown").lower()
    age = unit.get("t_age") or unit.get("b_age") or "Unknown"
    desc = unit.get("descrip") or unit.get("name") or "No description"
    strat = unit.get("strat_name") or unit.get("name") or ""
    score = 40
    for rock in HIGH_MINERAL_ROCKS:
        if rock in lith:
            score = 85; break
    else:
        for rock in MODERATE_MINERAL_ROCKS:
            if rock in lith:
                score = 65; break
    if any(kw in lith for kw in ("igneous", "volcanic", "plutonic", "intrusive")):
        score = min(score + 10, 95)
    if any(kw in lith for kw in ("metamorphic", "metasedimentary", "metavolcanic")):
        score = min(score + 5, 95)
    full_desc = f"{strat}: {desc}" if strat else desc
    return score, lith.title(), full_desc, str(age)

def _terrain_score(avg_slope, roughness, center_elev):
    score = 80
    if avg_slope > 25: score -= 35
    elif avg_slope > 15: score -= 20
    elif avg_slope > 8: score -= 10
    if roughness > 200: score -= 15
    elif roughness > 100: score -= 8
    if center_elev is not None:
        if center_elev > 4000: score -= 15
        elif center_elev > 3000: score -= 8
        elif center_elev < -50: score -= 10
    return max(5, min(score, 100))

def _soil_score(clay, sand, bdod):
    score = 60
    if clay is not None:
        if clay > 50: score -= 20
        elif clay > 30: score -= 10
        elif clay < 15: score += 10
    if sand is not None and sand > 60: score += 10
    if bdod is not None:
        if bdod > 1.7: score -= 10
        elif bdod < 1.2: score += 5
    return max(5, min(score, 100))

def _infra_score(cats):
    score = 20
    rd = _nearest(cats["roads"])
    rl = _nearest(cats["railways"])
    mn = _nearest(cats["mines"])
    qr = _nearest(cats["quarries"])
    ind = _nearest(cats["industrial"])
    if rd is not None:
        score += 25 if rd < 2 else 20 if rd < 5 else 12 if rd < 15 else 5
    if rl is not None:
        score += 20 if rl < 5 else 12 if rl < 15 else 5
    if mn is not None and mn < 10: score += 15
    elif qr is not None and qr < 10: score += 10
    if ind is not None and ind < 10: score += 10
    return max(5, min(score, 100))

def _env_score(cats, eq_data):
    score = 85
    pd_ = _nearest(cats["protected"])
    wd = _nearest(cats["water"])
    if pd_ is not None:
        if pd_ < 1: score -= 50
        elif pd_ < 5: score -= 30
        elif pd_ < 10: score -= 15
    if wd is not None:
        if wd < 1: score -= 20
        elif wd < 5: score -= 10
    if "error" not in eq_data:
        feats = eq_data.get("features", [])
        if len(feats) > 30: score -= 20
        elif len(feats) > 15: score -= 12
        elif len(feats) > 5: score -= 5
        mx = max(((f.get("properties") or {}).get("mag") or 0) for f in feats) if feats else 0
        if mx >= 6: score -= 15
        elif mx >= 5: score -= 8
    return max(5, min(score, 100))

def _climate_score(climate_data):
    if "error" in climate_data:
        return 60, 0, []
    cur = climate_data.get("current", {})
    daily = climate_data.get("daily", {})
    ps = daily.get("precipitation_sum", [])
    dates = daily.get("time", [])
    temp, wind = cur.get("temperature_2m"), cur.get("wind_speed_10m")
    score = 75
    if temp is not None:
        if temp < -20: score -= 25
        elif temp < -10: score -= 15
        elif temp > 45: score -= 20
        elif temp > 38: score -= 10
    if wind is not None:
        if wind > 50: score -= 15
        elif wind > 30: score -= 8
    rainy = sum(1 for p in ps if p and p > 5)
    working = len(ps) - rainy
    if rainy > 10: score -= 20
    elif rainy > 7: score -= 12
    elif rainy > 4: score -= 5
    return max(5, min(score, 100)), working, list(zip(dates, ps))

def _composite(geo, ter, soil, inf, env, clim):
    return round(geo*0.25 + ter*0.15 + soil*0.10 + inf*0.20 + env*0.15 + clim*0.15, 1)

def _recommend_type(slope, elev, geo_sc, lith):
    ll = (lith or "").lower()
    if any(k in ll for k in ("alluvial","alluvium","gravel","sand","placer","fluvial")):
        return "Placer Mining"
    if slope > 20 or (elev is not None and elev > 3000):
        return "Underground Mining"
    if geo_sc > 75 and any(k in ll for k in ("granite","gabbro","peridotite","kimberlite","pegmatite")):
        return "Underground Mining"
    return "Surface Mining (Open Pit)"

def _verdict(score):
    if score >= 65: return "GO", "#10b981"
    if score >= 40: return "CAUTION", "#f59e0b"
    return "NO-GO", "#ef4444"

# ═══════════════════════════════════════════════════
# RENDER SECTIONS
# ═══════════════════════════════════════════════════

def _sec1_geology(geo_data):
    """Section 1: Geological Assessment."""
    st.subheader("1. Geological Assessment")
    geo_sc, lith, desc, age = _geology_score(geo_data)
    if "error" in geo_data:
        st.warning(f"Could not fetch geological data: {geo_data['error']}")
        return geo_sc, lith
    features = geo_data.get("success", {}).get("data", [])
    c1, c2, c3 = st.columns(3)
    c1.metric("Lithology", lith)
    c2.metric("Geological Age", age)
    c3.metric("Mineral Potential Score", f"{geo_sc}/100")
    st.markdown(f"**Formation Description:** {desc}")
    if features:
        st.markdown("**Geological Units at Location:**")
        for i, u in enumerate(features[:5]):
            nm = u.get("strat_name") or u.get("name") or f"Unit {i+1}"
            st.markdown(
                f"- **{nm}** -- Lithology: {u.get('lith','N/A')} | "
                f"Age: {u.get('t_age') or u.get('b_age','N/A')} | "
                f"Thickness: {u.get('t_thick') or u.get('max_thick','N/A')}"
            )
    if HAS_PLOTLY and features:
        names, scores = [], []
        for u in features[:8]:
            rn = (u.get("lith") or "unknown").lower()
            names.append(rn.title())
            s = 40
            for rock in HIGH_MINERAL_ROCKS:
                if rock in rn: s = 85; break
            else:
                for rock in MODERATE_MINERAL_ROCKS:
                    if rock in rn: s = 65; break
            scores.append(s)
        fig = go.Figure(go.Bar(
            x=names, y=scores,
            marker_color=["#10b981" if s >= 70 else "#f59e0b" if s >= 50 else "#ef4444" for s in scores],
            text=scores, textposition="outside",
        ))
        fig.update_layout(title="Mineral Potential by Rock Unit", yaxis_title="Score",
                          xaxis_title="Rock Type", height=350, margin=dict(t=40, b=40))
        st.plotly_chart(fig, use_container_width=True, key="mns_geo_bar")
    return geo_sc, lith

def _sec2_terrain(elev_data, grid_data, lat, lon):
    """Section 2: Terrain Analysis."""
    st.subheader("2. Terrain Analysis")
    center_elev = None
    if "error" not in elev_data:
        res = elev_data.get("results", [])
        if res:
            center_elev = res[0].get("elevation")
    grid_elevs = []
    if "error" not in grid_data:
        grid_elevs = [r.get("elevation") for r in grid_data.get("results", []) if r.get("elevation") is not None]
    step_m = 0.01 * 111_000
    avg_slope = _compute_slope(grid_elevs, step_m) if grid_elevs else 0.0
    roughness = _terrain_roughness(grid_elevs) if grid_elevs else 0.0
    t_sc = _terrain_score(avg_slope, roughness, center_elev)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Centre Elevation", f"{center_elev:.0f} m" if center_elev is not None else "N/A")
    c2.metric("Avg Slope", f"{avg_slope:.1f} deg")
    c3.metric("Roughness (TRI)", f"{roughness:.1f} m")
    c4.metric("Terrain Score", f"{t_sc}/100")
    if avg_slope < 8:
        st.info("Relatively flat terrain -- suitable for open-pit surface mining.")
    elif avg_slope < 20:
        st.info("Moderate slopes -- surface mining possible with terracing; underground feasible.")
    else:
        st.warning("Steep terrain -- underground mining recommended; surface operations difficult.")
    if HAS_PLOTLY and grid_elevs:
        n = int(math.sqrt(len(grid_elevs)))
        if n >= 2:
            z = [grid_elevs[i*n:(i+1)*n] for i in range(n)]
            fig = go.Figure(data=go.Heatmap(z=z, colorscale="Earth", colorbar=dict(title="Elevation (m)")))
            fig.update_layout(title="Elevation Grid (Slope Gradient Map)", height=400,
                              xaxis_title="Grid X", yaxis_title="Grid Y", margin=dict(t=40, b=40))
            st.plotly_chart(fig, use_container_width=True, key="mns_terrain_heatmap")
    return t_sc, avg_slope, center_elev

def _sec3_soil(soil_data):
    """Section 3: Soil Composition & Overburden."""
    st.subheader("3. Soil Composition & Overburden")
    if "error" in soil_data:
        st.warning(f"Could not fetch soil data: {soil_data['error']}")
        return 60
    # MANDATORY SoilGrids v2.0 parsing
    raw_props = (soil_data if isinstance(soil_data, dict) else {}).get("properties", {})
    layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {l.get("name", ""): l for l in layers if isinstance(l, dict) and l.get("name")}
    def _sv(name, div=10):
        p = _layer_map.get(name, {})
        depths = p.get("depths", []) if isinstance(p, dict) else []
        return (depths[0].get("values", {}).get("mean") or 0) / div if depths else None
    clay = _sv("clay", 10)
    sand = _sv("sand", 10)
    silt = _sv("silt", 10)
    soc = _sv("soc", 10)
    bdod = _sv("bdod", 100)
    s_sc = _soil_score(clay, sand, bdod)
    c1, c2, c3 = st.columns(3)
    c1.metric("Clay", f"{clay:.1f} %" if clay is not None else "N/A")
    c2.metric("Sand", f"{sand:.1f} %" if sand is not None else "N/A")
    c3.metric("Silt", f"{silt:.1f} %" if silt is not None else "N/A")
    c4, c5, c6 = st.columns(3)
    c4.metric("Bulk Density", f"{bdod:.2f} kg/dm3" if bdod is not None else "N/A")
    c5.metric("Organic Carbon", f"{soc:.1f} g/kg" if soc is not None else "N/A")
    c6.metric("Excavation Difficulty Score", f"{s_sc}/100")
    if clay is not None and clay > 40:
        st.warning("High clay content -- cohesive overburden may require heavy equipment for removal.")
    elif sand is not None and sand > 60:
        st.info("Sandy overburden -- easy to excavate but may pose slope stability issues.")
    else:
        st.info("Mixed soil composition -- moderate excavation difficulty expected.")
    if HAS_PLOTLY and clay is not None and sand is not None and silt is not None:
        fig = go.Figure(go.Pie(
            labels=["Clay", "Sand", "Silt"], values=[clay, sand, silt],
            marker_colors=["#f59e0b", "#ef4444", "#8b5cf6"], hole=0.35, textinfo="label+percent",
        ))
        fig.update_layout(title="Soil Texture Composition", height=350, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True, key="mns_soil_pie")
    return s_sc

def _sec4_infrastructure(cats, lat, lon):
    """Section 4: Infrastructure Access."""
    st.subheader("4. Infrastructure Access")
    i_sc = _infra_score(cats)
    rd = _nearest(cats["roads"])
    rl = _nearest(cats["railways"])
    mn = _nearest(cats["mines"])
    qr = _nearest(cats["quarries"])
    ind = _nearest(cats["industrial"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Nearest Road", f"{rd:.1f} km" if rd is not None else "> 25 km")
    c2.metric("Nearest Railway", f"{rl:.1f} km" if rl is not None else "> 25 km")
    c3.metric("Transport Score", f"{i_sc}/100")
    c4, c5, c6 = st.columns(3)
    c4.metric("Nearest Mine/Adit", f"{mn:.1f} km" if mn is not None else "None found")
    c5.metric("Nearest Quarry", f"{qr:.1f} km" if qr is not None else "None found")
    c6.metric("Nearest Industrial", f"{ind:.1f} km" if ind is not None else "None found")
    st.markdown(
        f"**Roads:** {len(cats['roads'])} | **Railways:** {len(cats['railways'])} | "
        f"**Mines/Adits:** {len(cats['mines'])} | **Quarries:** {len(cats['quarries'])}"
    )
    if HAS_FOLIUM:
        m = folium.Map(location=[lat, lon], zoom_start=11)
        folium.Marker([lat, lon], popup="Analysis Point",
                      icon=folium.Icon(color="red", icon="crosshairs", prefix="fa")).add_to(m)
        icons = {
            "roads": ("blue", "road"), "railways": ("darkblue", "train"),
            "mines": ("orange", "industry"), "quarries": ("beige", "cubes"),
            "industrial": ("gray", "building"), "protected": ("green", "tree"),
            "water": ("lightblue", "tint"),
        }
        for cat_name, items in cats.items():
            clr, ico = icons.get(cat_name, ("gray", "info"))
            for it in items[:15]:
                tag_nm = it["tags"].get("name", "")
                popup = f"{tag_nm} ({cat_name}) -- {it['dist_km']} km" if tag_nm else f"{cat_name.title()} -- {it['dist_km']} km"
                folium.Marker([it["lat"], it["lon"]], popup=popup,
                              icon=folium.Icon(color=clr, icon=ico, prefix="fa")).add_to(m)
        st_folium(m, width=700, height=450, key="mns_infra_map")
    else:
        st.info("Install folium and streamlit-folium to see the infrastructure map.")
    return i_sc

def _sec5_environment(cats, eq_data):
    """Section 5: Environmental Constraints."""
    st.subheader("5. Environmental Constraints")
    e_sc = _env_score(cats, eq_data)
    pd_ = _nearest(cats["protected"])
    wd = _nearest(cats["water"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Nearest Protected Area", f"{pd_:.1f} km" if pd_ is not None else "None within 25 km")
    c2.metric("Nearest Water Body", f"{wd:.1f} km" if wd is not None else "None within 25 km")
    c3.metric("Env. Impact Score", f"{e_sc}/100")
    if pd_ is not None and pd_ < 1:
        st.error(
            "CRITICAL: Site is inside or immediately adjacent to a protected area "
            "(nature reserve or national park). Mining would face severe regulatory barriers."
        )
    elif pd_ is not None and pd_ < 5:
        st.warning("Protected area nearby -- environmental impact assessments and buffer zones required.")
    if wd is not None and wd < 2:
        st.warning("Water body within 2 km -- contamination risk. Tailings management required.")
    st.markdown("---")
    st.markdown("**Seismic Risk Assessment**")
    if "error" in eq_data:
        st.info(f"Could not fetch earthquake data: {eq_data['error']}")
    else:
        feats = eq_data.get("features", [])
        eq_ct = len(feats)
        mx = max(((f.get("properties") or {}).get("mag") or 0) for f in feats) if feats else 0
        c1, c2 = st.columns(2)
        c1.metric("Earthquakes (M3+, 150 km)", eq_ct)
        c2.metric("Max Magnitude", f"{mx:.1f}" if mx > 0 else "None recorded")
        if eq_ct > 20:
            st.error("HIGH seismic risk -- frequent earthquake activity in the region.")
        elif eq_ct > 5:
            st.warning("MODERATE seismic risk -- some earthquake activity detected.")
        else:
            st.success("LOW seismic risk -- minimal earthquake activity.")
        if feats:
            st.markdown("**Recent Significant Earthquakes:**")
            for f in feats[:5]:
                p = f.get("properties", {})
                st.markdown(f"- M{p.get('mag',0):.1f} -- {p.get('place','Unknown')}")
    return e_sc

def _sec6_climate(climate_data):
    """Section 6: Climate & Operational Conditions."""
    st.subheader("6. Climate & Operational Conditions")
    c_sc, working, daily_p = _climate_score(climate_data)
    if "error" in climate_data:
        st.warning(f"Could not fetch climate data: {climate_data['error']}")
        return c_sc
    cur = climate_data.get("current", {})
    temp = cur.get("temperature_2m")
    precip = cur.get("precipitation")
    wind = cur.get("wind_speed_10m")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Temperature", f"{temp:.1f} C" if temp is not None else "N/A")
    c2.metric("Precipitation", f"{precip:.1f} mm" if precip is not None else "N/A")
    c3.metric("Wind Speed", f"{wind:.1f} km/h" if wind is not None else "N/A")
    c4.metric("Climate Score", f"{c_sc}/100")
    rainy = len(daily_p) - working
    st.markdown(f"**14-Day Forecast:** {working} working days, {rainy} days with significant precipitation (> 5 mm)")
    if temp is not None:
        if temp < -10:
            st.warning("Extreme cold -- frozen ground, equipment heating required.")
        elif temp > 40:
            st.warning("Extreme heat -- worker safety protocols and hydration critical.")
        else:
            st.info("Temperature within acceptable operating range.")
    if HAS_PLOTLY and daily_p:
        dates = [d[0] for d in daily_p]
        vals = [d[1] if d[1] is not None else 0 for d in daily_p]
        fig = go.Figure(go.Bar(
            x=dates, y=vals,
            marker_color=["#ef4444" if p > 5 else "#10b981" for p in vals],
            text=[f"{p:.1f}" for p in vals], textposition="outside",
        ))
        fig.add_hline(y=5, line_dash="dash", line_color="#f59e0b",
                      annotation_text="Work threshold (5 mm)")
        fig.update_layout(title="14-Day Precipitation Forecast (Operability)",
                          yaxis_title="Precipitation (mm)", xaxis_title="Date",
                          height=380, margin=dict(t=50, b=40))
        st.plotly_chart(fig, use_container_width=True, key="mns_climate_bar")
    return c_sc

def _sec7_composite(scores, avg_slope, center_elev, lith, geo_sc):
    """Section 7: Mining Suitability Score."""
    st.subheader("7. Mining Suitability Score")
    comp = _composite(scores["geology"], scores["terrain"], scores["soil"],
                      scores["infrastructure"], scores["environment"], scores["climate"])
    vtext, vcol = _verdict(comp)
    mtype = _recommend_type(avg_slope, center_elev, geo_sc, lith)
    st.markdown(
        f'<div style="text-align:center;padding:20px;border-radius:12px;'
        f'background:{vcol}22;border:3px solid {vcol};margin-bottom:20px;">'
        f'<h1 style="color:{vcol};margin:0;">{comp}/100</h1>'
        f'<h2 style="color:{vcol};margin:5px 0;">{vtext}</h2>'
        f'<p style="font-size:1.1em;margin:5px 0;">Recommended: <b>{mtype}</b></p></div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Composite Score", f"{comp}/100")
    c2.metric("Verdict", vtext)
    c3.metric("Mining Type", mtype)
    # Score breakdown with visual bars
    st.markdown("**Score Breakdown:**")
    labels = {"Geology (25%)": "geology", "Terrain (15%)": "terrain",
              "Soil/Overburden (10%)": "soil", "Infrastructure (20%)": "infrastructure",
              "Environment (15%)": "environment", "Climate (15%)": "climate"}
    for label, key in labels.items():
        v = scores[key]
        col = "#10b981" if v >= 65 else "#f59e0b" if v >= 40 else "#ef4444"
        st.markdown(
            f"**{label}:** {v}/100 "
            f'<div style="background:#e5e7eb;border-radius:4px;height:18px;width:100%;">'
            f'<div style="background:{col};border-radius:4px;height:18px;width:{v}%;"></div></div>',
            unsafe_allow_html=True,
        )
    # Radar chart
    if HAS_PLOTLY:
        cats_l = ["Geology", "Terrain", "Soil", "Infrastructure", "Environment", "Climate"]
        vals = [scores[k] for k in ("geology","terrain","soil","infrastructure","environment","climate")]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=vals + [vals[0]], theta=cats_l + [cats_l[0]],
            fill="toself", fillcolor="rgba(16,185,129,0.2)",
            line=dict(color="#10b981", width=2), name="Suitability",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            title="Mining Suitability Radar", showlegend=False,
            height=450, margin=dict(t=60, b=40),
        )
        st.plotly_chart(fig, use_container_width=True, key="mns_radar")
    # Interpretation
    st.markdown("---")
    st.markdown("**Interpretation & Recommendations:**")
    if comp >= 65:
        st.success(
            "This location shows GOOD overall suitability for mining operations. "
            "Geological conditions indicate mineral potential, infrastructure is adequate, "
            "and environmental constraints are manageable. A detailed feasibility study "
            "is recommended as the next step."
        )
    elif comp >= 40:
        st.warning(
            "This location shows MODERATE suitability. Some dimensions score well but "
            "others present challenges. Review individual scores to identify limiting factors. "
            "Targeted surveys and environmental impact assessments are necessary."
        )
    else:
        st.error(
            "This location is NOT RECOMMENDED for mining. Significant barriers exist "
            "(protected areas, extreme terrain, lack of infrastructure, or high "
            "environmental/seismic risk). Alternative sites should be considered."
        )
    st.markdown("**Dimension-Specific Notes:**")
    notes = {
        "geology": "Rock types have low mineral potential. Consider geophysical surveys for deeper targets.",
        "terrain": "Challenging topography. Underground methods or significant earthworks needed.",
        "soil": "Dense or cohesive overburden will increase stripping costs.",
        "infrastructure": "Remote location. Road/rail construction may be required, increasing CAPEX.",
        "environment": "Environmental constraints are significant. Legal review and EIAs are critical.",
        "climate": "Adverse weather will reduce operational windows and increase costs.",
    }
    for key, note in notes.items():
        if scores[key] < 50:
            st.markdown(f"- {key.title()}: {note}")
    return comp

# ═══════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════

def render_mining_suitability_tab():
    """Main entry point for the Mining Suitability Assessment module."""
    st.title("Mining Suitability Assessment")
    st.markdown(
        "Evaluate a location's suitability for mining operations based on geology, "
        "terrain, soil composition, infrastructure, environmental constraints, climate, "
        "and seismic risk. Produces a composite score with GO / CAUTION / NO-GO verdict."
    )
    st.markdown("---")
    cp, cl, cr = st.columns([2, 1, 1])
    with cp:
        preset = st.selectbox("Preset Mining Locations", list(MINING_PRESETS.keys()), key="mns_preset")
    dlat, dlon = 40.52, -112.15
    if preset != "Custom" and MINING_PRESETS.get(preset):
        dlat, dlon = MINING_PRESETS[preset]
    with cl:
        lat = st.number_input("Latitude", value=dlat, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="mns_lat")
    with cr:
        lon = st.number_input("Longitude", value=dlon, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="mns_lon")
    if not st.button("Analyse Mining Suitability", type="primary", key="mns_analyze"):
        st.info("Select a location and click **Analyse Mining Suitability** to begin.")
        return
    # Fetch all data
    with st.spinner("Fetching geological data..."):
        geo_data = _fetch_geology(lat, lon)
    with st.spinner("Fetching elevation data..."):
        elev_data = _fetch_elevation(lat, lon)
        grid_data = _fetch_elevation_grid(lat, lon)
    with st.spinner("Fetching soil data..."):
        soil_data = _fetch_soil(lat, lon)
    with st.spinner("Fetching infrastructure & environmental data..."):
        infra_data = _fetch_infrastructure(lat, lon)
    with st.spinner("Fetching climate data..."):
        climate_data = _fetch_climate(lat, lon)
    with st.spinner("Fetching seismic data..."):
        eq_data = _fetch_earthquakes(lat, lon)
    # Classify Overpass elements
    elements = infra_data.get("elements", []) if "error" not in infra_data else []
    cats = _classify_elements(elements, lat, lon)
    st.markdown("---")
    # Section 1
    geo_sc, lith = _sec1_geology(geo_data)
    st.markdown("---")
    # Section 2
    t_sc, avg_slope, center_elev = _sec2_terrain(elev_data, grid_data, lat, lon)
    st.markdown("---")
    # Section 3
    s_sc = _sec3_soil(soil_data)
    st.markdown("---")
    # Section 4
    i_sc = _sec4_infrastructure(cats, lat, lon)
    st.markdown("---")
    # Section 5
    e_sc = _sec5_environment(cats, eq_data)
    st.markdown("---")
    # Section 6
    c_sc = _sec6_climate(climate_data)
    st.markdown("---")
    # Section 7
    scores = {"geology": geo_sc, "terrain": t_sc, "soil": s_sc,
              "infrastructure": i_sc, "environment": e_sc, "climate": c_sc}
    _sec7_composite(scores, avg_slope, center_elev, lith, geo_sc)
