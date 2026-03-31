"""
Vegetation & Biomass Index — TerraScout AI module.
Analyses vegetation density, health, and biomass around a geographic point
using exclusively free, keyless APIs: Overpass (OSM), ISRIC SoilGrids v2.0,
Open-Meteo, and iNaturalist.
Six dimensions are scored 0-10 and combined into a synthetic NDVI proxy (0-1).
"""

import math
import logging

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import folium
    from folium.plugins import HeatMap
except ImportError:
    folium = None
    HeatMap = None

try:
    from streamlit_folium import st_folium
except ImportError:
    st_folium = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
SOILGRIDS_URL = "https://rest.isric.org/soilgrids/v2.0/properties/query"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
INATURALIST_URL = "https://api.inaturalist.org/v1/observations"

DIMENSION_META = {
    "Green Cover": {"icon": "🌲", "color": "#22c55e",
                    "desc": "Forests, parks, gardens, orchards & vineyards within 5 km"},
    "Soil Organic Carbon": {"icon": "🪨", "color": "#a16207",
                            "desc": "SOC — proxy for historical vegetation productivity"},
    "Climate Suitability": {"icon": "🌡️", "color": "#f59e0b",
                            "desc": "Temperature, precipitation & growing degree-days (30 d)"},
    "Species Diversity": {"icon": "🌸", "color": "#ec4899",
                          "desc": "Plant observations in surrounding area (iNaturalist)"},
    "Tree Cover": {"icon": "🌳", "color": "#15803d",
                   "desc": "Individual trees & tree rows mapped within 3 km"},
    "Water Availability": {"icon": "💧", "color": "#3b82f6",
                           "desc": "Precipitation volume & proximity to water bodies"},
}

NDVI_CLASSES = [
    ("Lush", 0.7, 1.0, "#15803d"),
    ("Healthy", 0.5, 0.7, "#22c55e"),
    ("Moderate", 0.3, 0.5, "#f59e0b"),
    ("Sparse", 0.1, 0.3, "#f97316"),
    ("Barren", 0.0, 0.1, "#7f1d1d"),
]

NDVI_DESCRIPTIONS = {
    "Lush": "Dense, thriving vegetation with high biomass",
    "Healthy": "Good vegetation cover, active photosynthesis",
    "Moderate": "Mixed or transitional areas",
    "Sparse": "Limited plant cover, arid or disturbed",
    "Barren": "Virtually no vegetation detected",
}

DIMENSION_WEIGHTS = {
    "Green Cover": 0.25, "Tree Cover": 0.25,
    "Soil Organic Carbon": 0.15, "Climate Suitability": 0.15,
    "Species Diversity": 0.10, "Water Availability": 0.10,
}


def _clamp(v: float, lo: float = 0.0, hi: float = 10.0) -> float:
    return max(lo, min(hi, v))


def _ndvi_class(ndvi: float):
    """Return (label, color) for a given NDVI proxy value."""
    result_label, result_color = "Barren", "#7f1d1d"
    for label, lo, _hi, color in NDVI_CLASSES:
        if ndvi >= lo:
            result_label, result_color = label, color
    return result_label, result_color


# ---------------------------------------------------------------------------
# API fetchers — all cached with ttl=900, timeout=10, try/except
# ---------------------------------------------------------------------------
@st.cache_data(ttl=900)
def _fetch_green_cover(lat: float, lon: float) -> dict:
    """Count green land-use polygons within 5 km via Overpass."""
    query = f"""[out:json][timeout:15];(
      way["landuse"~"forest|meadow|orchard|vineyard|farmland"](around:5000,{lat},{lon});
      way["natural"~"wood|scrub|heath|grassland"](around:5000,{lat},{lon});
      way["leisure"~"park|garden"](around:5000,{lat},{lon});
    );out count;"""
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        r.raise_for_status()
        data = r.json()
        total = 0
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            total += int(tags.get("ways", 0)) + int(tags.get("total", 0))
        if total == 0:
            total = len(data.get("elements", []))
        return {"count": total}
    except Exception as e:
        logger.warning("Green cover fetch failed: %s", e)
        return {"count": 0, "error": str(e)}


@st.cache_data(ttl=900)
def _fetch_soil_data(lat: float, lon: float) -> dict:
    """Fetch SOC and related soil properties from ISRIC SoilGrids v2.0."""
    try:
        params = {
            "lon": lon, "lat": lat,
            "property": ["soc", "nitrogen", "phh2o", "clay", "ocd"],
            "depth": ["0-5cm", "5-15cm", "15-30cm"], "value": "mean",
        }
        r = requests.get(SOILGRIDS_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("SoilGrids fetch failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_climate(lat: float, lon: float) -> dict:
    """Fetch 30-day climate data from Open-Meteo."""
    url = (f"{OPEN_METEO_URL}?latitude={lat}&longitude={lon}"
           f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum"
           f"&past_days=30&timezone=auto")
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Open-Meteo fetch failed: %s", e)
        return {"error": str(e)}


@st.cache_data(ttl=900)
def _fetch_plant_diversity(lat: float, lon: float) -> dict:
    """Count plant observations via iNaturalist."""
    try:
        params = {"lat": lat, "lng": lon, "radius": 10,
                  "iconic_taxa": "Plantae", "per_page": 0}
        r = requests.get(INATURALIST_URL, params=params, timeout=10)
        r.raise_for_status()
        return {"total": r.json().get("total_results", 0)}
    except Exception as e:
        logger.warning("iNaturalist fetch failed: %s", e)
        return {"total": 0, "error": str(e)}


@st.cache_data(ttl=900)
def _fetch_tree_cover(lat: float, lon: float) -> dict:
    """Count individual trees and tree rows within 3 km."""
    query = f"""[out:json][timeout:15];(
      node["natural"="tree"](around:3000,{lat},{lon});
      way["natural"="tree_row"](around:3000,{lat},{lon});
    );out count;"""
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        r.raise_for_status()
        data = r.json()
        total = 0
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            total += int(tags.get("nodes", 0)) + int(tags.get("ways", 0)) + int(tags.get("total", 0))
        if total == 0:
            total = len(data.get("elements", []))
        return {"count": total}
    except Exception as e:
        logger.warning("Tree cover fetch failed: %s", e)
        return {"count": 0, "error": str(e)}


@st.cache_data(ttl=900)
def _fetch_water_bodies(lat: float, lon: float) -> dict:
    """Count nearby water bodies within 5 km via Overpass."""
    query = f"""[out:json][timeout:15];(
      way["natural"="water"](around:5000,{lat},{lon});
      way["waterway"~"river|stream|canal"](around:5000,{lat},{lon});
      relation["natural"="water"](around:5000,{lat},{lon});
    );out count;"""
    try:
        r = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        r.raise_for_status()
        data = r.json()
        total = 0
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            total += int(tags.get("ways", 0)) + int(tags.get("relations", 0)) + int(tags.get("total", 0))
        if total == 0:
            total = len(data.get("elements", []))
        return {"count": total}
    except Exception as e:
        logger.warning("Water bodies fetch failed: %s", e)
        return {"count": 0, "error": str(e)}


# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------
def _parse_soil(soil: dict):
    """Parse SoilGrids v2.0 response using correct layer structure."""
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

    return {"soc": _sv("soc"), "nitrogen": _sv("nitrogen", div=100),
            "ocd": _sv("ocd"), "ph": _sv("phh2o")}


def _compute_climate_metrics(climate: dict) -> dict:
    """Derive growing degree-days, mean temp, total precipitation."""
    daily = climate.get("daily", {})
    tmax_list = daily.get("temperature_2m_max", [])
    tmin_list = daily.get("temperature_2m_min", [])
    precip_list = daily.get("precipitation_sum", [])
    gdd, temps = 0.0, []
    for tmax, tmin in zip(tmax_list, tmin_list):
        if tmax is not None and tmin is not None:
            avg = (tmax + tmin) / 2.0
            temps.append(avg)
            if avg > 10:
                gdd += avg - 10.0
    total_precip = sum(p for p in precip_list if p is not None)
    mean_temp = sum(temps) / len(temps) if temps else 0.0
    return {"gdd": round(gdd, 1), "mean_temp": round(mean_temp, 1),
            "total_precip": round(total_precip, 1), "days": len(temps)}


@st.cache_data(ttl=900)
def compute_vegetation_index(lat: float, lon: float) -> dict:
    """Compute all six vegetation dimensions and the NDVI proxy."""
    green = _fetch_green_cover(lat, lon)
    soil_raw = _fetch_soil_data(lat, lon)
    climate_raw = _fetch_climate(lat, lon)
    plants = _fetch_plant_diversity(lat, lon)
    trees = _fetch_tree_cover(lat, lon)
    water = _fetch_water_bodies(lat, lon)

    soil = _parse_soil(soil_raw)
    climate = _compute_climate_metrics(climate_raw)
    scores, details = {}, {}

    # 1. Green Cover Density (0-10)
    gc_count = green.get("count", 0)
    scores["Green Cover"] = round(_clamp(math.log1p(gc_count) * 1.8), 1)
    details["Green Cover"] = {"zones_found": gc_count}

    # 2. Soil Organic Carbon (0-10)
    soc_val, ocd_val = soil.get("soc") or 0, soil.get("ocd") or 0
    soc_score = _clamp(soc_val * 0.25 + ocd_val * 0.15) if (soc_val or ocd_val) else 0.0
    scores["Soil Organic Carbon"] = round(soc_score, 1)
    details["Soil Organic Carbon"] = {
        "soc_g_per_kg": round(soc_val, 2), "ocd": round(ocd_val, 2),
        "nitrogen": round(soil.get("nitrogen") or 0, 2),
        "ph": round(soil.get("ph") or 0, 1),
    }

    # 3. Climate Suitability (0-10)
    gdd = climate.get("gdd", 0)
    precip = climate.get("total_precip", 0)
    mean_t = climate.get("mean_temp", 0)
    gdd_s = _clamp(gdd / 40.0, 0, 4)
    precip_s = _clamp(precip / 25.0, 0, 3)
    temp_s = _clamp(3.0 - abs(mean_t - 20.0) * 0.2, 0, 3) if mean_t > 0 else 0.0
    scores["Climate Suitability"] = round(_clamp(gdd_s + precip_s + temp_s), 1)
    details["Climate Suitability"] = {
        "growing_degree_days": gdd, "total_precip_mm": precip,
        "mean_temp_C": mean_t, "days_analysed": climate.get("days", 0),
    }

    # 4. Species Diversity (0-10)
    plant_obs = plants.get("total", 0)
    scores["Species Diversity"] = round(_clamp(math.log1p(plant_obs) * 1.1), 1)
    details["Species Diversity"] = {"plant_observations": plant_obs}

    # 5. Tree Cover (0-10)
    tree_count = trees.get("count", 0)
    scores["Tree Cover"] = round(_clamp(math.log1p(tree_count) * 1.3), 1)
    details["Tree Cover"] = {"trees_and_rows": tree_count}

    # 6. Water Availability (0-10)
    water_count = water.get("count", 0)
    water_struct = _clamp(math.log1p(water_count) * 2.0, 0, 5)
    water_precip = _clamp(precip / 30.0, 0, 5)
    scores["Water Availability"] = round(_clamp(water_struct + water_precip), 1)
    details["Water Availability"] = {
        "water_bodies": water_count, "precip_component": round(water_precip, 1),
    }

    # Synthetic NDVI proxy (0-1)
    weighted_sum = sum(scores[k] * DIMENSION_WEIGHTS[k] for k in DIMENSION_WEIGHTS)
    ndvi_proxy = max(0.0, min(1.0, round(weighted_sum / 10.0, 3)))
    overall = round(sum(scores.values()) / len(scores), 1)
    label, color = _ndvi_class(ndvi_proxy)

    return {"scores": scores, "details": details, "ndvi_proxy": ndvi_proxy,
            "ndvi_label": label, "ndvi_color": color, "overall": overall,
            "lat": lat, "lon": lon}


# ---------------------------------------------------------------------------
# Visualisation helpers
# ---------------------------------------------------------------------------
def _build_ndvi_gauge(ndvi: float, label: str, color: str) -> go.Figure:
    """Create a gauge chart for synthetic NDVI."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=ndvi,
        number={"suffix": "", "font": {"size": 42, "color": "#e8ecf4"}},
        title={"text": f"Synthetic NDVI Proxy — {label}",
               "font": {"size": 16, "color": "#8b97b0"}},
        gauge={
            "axis": {"range": [0, 1], "tickwidth": 1, "tickcolor": "#2a3550",
                     "tickfont": {"color": "#5a6580"}},
            "bar": {"color": color, "thickness": 0.6},
            "bgcolor": "rgba(26,26,46,0.6)", "borderwidth": 0,
            "steps": [
                {"range": [0.0, 0.1], "color": "rgba(127,29,29,0.25)"},
                {"range": [0.1, 0.3], "color": "rgba(249,115,22,0.20)"},
                {"range": [0.3, 0.5], "color": "rgba(245,158,11,0.18)"},
                {"range": [0.5, 0.7], "color": "rgba(34,197,94,0.15)"},
                {"range": [0.7, 1.0], "color": "rgba(21,128,61,0.20)"},
            ],
            "threshold": {"line": {"color": "#e8ecf4", "width": 3},
                          "thickness": 0.8, "value": ndvi},
        },
    ))
    fig.update_layout(height=280, margin=dict(l=30, r=30, t=60, b=20),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#e8ecf4"))
    return fig


def _build_radar(scores: dict) -> go.Figure:
    """Create a radar chart of the six dimensions."""
    names = list(scores.keys())
    vals = [scores[n] for n in names]
    colors = [DIMENSION_META[n]["color"] for n in names]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=vals + [vals[0]], theta=names + [names[0]], fill="toself",
        fillcolor="rgba(34,197,94,0.13)", line=dict(color="#22c55e", width=2),
        marker=dict(size=7, color=colors + [colors[0]]), name="Vegetation",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(26,26,46,0.6)",
            radialaxis=dict(visible=True, range=[0, 10], gridcolor="#2a3550",
                            linecolor="#2a3550", tickfont=dict(color="#5a6580", size=10)),
            angularaxis=dict(gridcolor="#2a3550", linecolor="#2a3550",
                             tickfont=dict(color="#8b97b0", size=11)),
        ),
        showlegend=False, height=420, margin=dict(l=70, r=70, t=40, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e8ecf4"),
    )
    return fig


def _build_bar(scores: dict) -> go.Figure:
    """Horizontal bar chart of dimension scores."""
    sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    names = [i[0] for i in sorted_items]
    vals = [i[1] for i in sorted_items]
    colors = [DIMENSION_META[n]["color"] for n in names]
    fig = go.Figure(go.Bar(
        y=names, x=vals, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.1f}" for v in vals], textposition="outside",
        textfont=dict(color="#e8ecf4", size=12),
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 11], title="Score (0-10)", gridcolor="#2a3550",
                   zerolinecolor="#2a3550", tickfont=dict(color="#8b97b0"),
                   title_font=dict(color="#8b97b0")),
        yaxis=dict(tickfont=dict(color="#e8ecf4", size=12), autorange="reversed"),
        height=320, margin=dict(l=140, r=50, t=20, b=40),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(26,26,46,0.6)",
        font=dict(color="#e8ecf4"), bargap=0.3,
    )
    return fig


def _build_map(lat: float, lon: float, scores: dict):
    """Build a folium map with green overlay zones."""
    if folium is None or HeatMap is None:
        return None
    m = folium.Map(location=[lat, lon], zoom_start=13, tiles="CartoDB dark_matter")
    # Centre marker
    folium.Marker(
        [lat, lon],
        popup=f"Vegetation Index Centre<br>Overall: {scores.get('_overall', '?')}/10",
        icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
    ).add_to(m)
    # Scan radius circles
    for radius, clr, opacity, label, dash in [
        (5000, "#22c55e", 0.06, "Green Cover (5 km)", "6"),
        (3000, "#15803d", 0.08, "Tree Cover (3 km)", "4"),
        (5000, "#3b82f6", 0.04, "Water bodies (5 km)", "8"),
    ]:
        folium.Circle([lat, lon], radius=radius, color=clr, fill=True,
                       fill_opacity=opacity, popup=label, weight=1,
                       dash_array=dash).add_to(m)
    # Heatmap overlay
    overall = scores.get("_overall", 5)
    offsets = [(0, 0, 1.0), (0.01, 0.01, 0.7), (-0.01, -0.01, 0.7),
               (0.01, -0.01, 0.6), (-0.01, 0.01, 0.6),
               (0.02, 0, 0.4), (0, 0.02, 0.4), (-0.02, 0, 0.4), (0, -0.02, 0.4),
               (0.03, 0.03, 0.2), (-0.03, -0.03, 0.2)]
    heat_data = [[lat + dl, lon + dn, w * overall / 10.0] for dl, dn, w in offsets]
    HeatMap(heat_data, radius=40, blur=30, min_opacity=0.3,
            gradient={0.2: "#7f1d1d", 0.4: "#f97316", 0.6: "#f59e0b",
                      0.8: "#22c55e", 1.0: "#15803d"}).add_to(m)
    return m


# ---------------------------------------------------------------------------
# Interpretation helpers
# ---------------------------------------------------------------------------
def _generate_insights(result: dict) -> list:
    """Generate human-readable insights from the analysis."""
    insights = []
    details = result["details"]
    ndvi = result["ndvi_proxy"]

    # Overall assessment
    if ndvi >= 0.7:
        insights.append("This area shows **lush vegetation** with strong biomass "
                        "indicators. Ecosystem productivity is excellent.")
    elif ndvi >= 0.5:
        insights.append("Vegetation is **healthy** with good cover. The ecosystem "
                        "supports moderate-to-high biomass accumulation.")
    elif ndvi >= 0.3:
        insights.append("**Moderate vegetation** detected. Some areas may be "
                        "degraded or transitioning between land-use types.")
    elif ndvi >= 0.1:
        insights.append("Vegetation is **sparse**. The area may be arid, heavily "
                        "urbanised, or recently disturbed.")
    else:
        insights.append("**Barren** conditions detected. Very limited vegetation "
                        "— likely desert, ice, or densely built-up area.")

    # Green cover
    gc = details["Green Cover"]["zones_found"]
    if gc > 50:
        insights.append(f"Excellent green cover: {gc} vegetated zones within 5 km.")
    elif gc > 10:
        insights.append(f"Moderate green cover: {gc} vegetated zones within 5 km.")
    elif gc > 0:
        insights.append(f"Limited green cover: only {gc} vegetated zones within 5 km.")

    # SOC
    soc_val = details["Soil Organic Carbon"].get("soc_g_per_kg", 0)
    if soc_val > 30:
        insights.append(f"High soil organic carbon ({soc_val} g/kg) — fertile, productive soils.")
    elif soc_val > 10:
        insights.append(f"Moderate SOC ({soc_val} g/kg) — reasonable soil fertility.")
    elif soc_val > 0:
        insights.append(f"Low SOC ({soc_val} g/kg) — soils may lack organic matter.")

    # Climate
    gdd = details["Climate Suitability"].get("growing_degree_days", 0)
    if gdd > 300:
        insights.append(f"Strong growing conditions with {gdd} GDD in the past month.")
    elif gdd > 100:
        insights.append(f"Moderate growing season: {gdd} GDD in the past month.")
    else:
        insights.append(f"Cool conditions ({gdd} GDD) — growth may be limited or dormant.")

    # Trees
    tc = details["Tree Cover"]["trees_and_rows"]
    if tc > 200:
        insights.append(f"Dense tree cover: {tc} trees/rows mapped within 3 km.")
    elif tc > 20:
        insights.append(f"Some tree cover: {tc} trees/rows mapped within 3 km.")

    # Water
    wb = details["Water Availability"]["water_bodies"]
    if wb > 10:
        insights.append(f"Good water access: {wb} water features nearby.")
    elif wb > 0:
        insights.append(f"Limited water features ({wb}) — plants may rely on rainfall.")
    return insights


def _generate_recommendations(result: dict) -> list:
    """Generate management recommendations based on scores."""
    recs = []
    scores = result["scores"]
    ndvi = result["ndvi_proxy"]
    thresholds = [
        ("Green Cover", 4, "Increase green cover through afforestation or urban greening."),
        ("Soil Organic Carbon", 3, "Improve SOC with cover crops, mulching, or composting."),
        ("Climate Suitability", 3, "Consider drought-tolerant or cold-resistant species."),
        ("Species Diversity", 3, "Enhance biodiversity with native species and habitat restoration."),
        ("Tree Cover", 3, "Plant trees along roads, fields, and waterways."),
        ("Water Availability", 4, "Improve water harvesting, irrigation, or wetland restoration."),
    ]
    for dim, thresh, msg in thresholds:
        if scores[dim] < thresh:
            recs.append(msg)
    if ndvi >= 0.7:
        recs.append("Maintain current practices — the ecosystem is thriving.")
    if ndvi < 0.3:
        recs.append("Prioritise ecosystem restoration: scores below critical thresholds.")
    return recs if recs else ["No urgent recommendations — vegetation indicators are balanced."]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def render_vegetation_index_tab():
    """Render the Vegetation & Biomass Index tab."""
    st.markdown("## 🌿 Vegetation & Biomass Index")
    st.caption("Vegetation density, health & biomass estimation using free satellite-proxy APIs")
    st.markdown(
        '<p style="color:#8b97b0;font-size:13px;margin-bottom:18px;">'
        "Analyses green cover, soil carbon, climate suitability, species diversity, "
        "tree density, and water availability to compute a synthetic NDVI proxy (0-1)."
        "</p>", unsafe_allow_html=True,
    )

    # --- Input controls ---
    col_lat, col_lon, col_btn = st.columns([2, 2, 1])
    with col_lat:
        lat = st.number_input("Latitude", value=45.4642, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="vegidx_lat")
    with col_lon:
        lon = st.number_input("Longitude", value=9.1900, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="vegidx_lon")
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        run = st.button("Analyse Vegetation", key="vegidx_run",
                        type="primary", use_container_width=True)
    if not run:
        st.info("Enter coordinates and click **Analyse Vegetation** to begin.")
        return

    # --- Compute ---
    with st.spinner("Fetching vegetation data from free APIs..."):
        result = compute_vegetation_index(lat, lon)
    scores = result["scores"]
    details = result["details"]
    ndvi = result["ndvi_proxy"]
    ndvi_label = result["ndvi_label"]
    ndvi_color = result["ndvi_color"]
    overall = result["overall"]

    # --- NDVI gauge ---
    st.markdown("---")
    st.plotly_chart(_build_ndvi_gauge(ndvi, ndvi_label, ndvi_color, key="vegind_pchart1"),
                    use_container_width=True, key="vegidx_gauge_chart")

    # NDVI class legend
    legend_parts = []
    for lbl, lo, hi, clr in NDVI_CLASSES:
        legend_parts.append(
            f'<span style="background:{clr};color:#fff;padding:2px 10px;'
            f'border-radius:10px;font-size:11px;">{lbl} ({lo}-{hi})</span>')
    st.markdown(
        '<div style="display:flex;gap:8px;justify-content:center;margin:-10px 0 16px 0;">'
        + "".join(legend_parts) + "</div>", unsafe_allow_html=True)

    # Overall score header
    st.markdown(
        f'<div style="text-align:center;margin:10px 0 20px 0;">'
        f'<span style="color:#8b97b0;font-size:14px;">Overall Vegetation Score: </span>'
        f'<span style="color:{ndvi_color};font-size:22px;font-weight:700;">'
        f'{overall}/10</span></div>', unsafe_allow_html=True)

    # --- Six metric cards ---
    st.markdown("### Dimension Scores")
    dim_names = list(DIMENSION_META.keys())
    row1 = st.columns(3)
    row2 = st.columns(3)
    all_cols = row1 + row2
    for idx, dim in enumerate(dim_names):
        meta = DIMENSION_META[dim]
        score = scores[dim]
        pct = score / 10.0 * 100
        detail_items = details.get(dim, {})
        with all_cols[idx]:
            detail_str = " | ".join(
                f"{k.replace('_', ' ').title()}: {v}" for k, v in detail_items.items())
            st.markdown(
                f'<div style="background:rgba(26,26,46,0.6);border:1px solid {meta["color"]}33;'
                f'border-radius:12px;padding:16px;margin:6px 0;">'
                f'<div style="font-size:13px;color:#8b97b0;">{meta["icon"]} {dim}</div>'
                f'<div style="font-size:28px;font-weight:700;color:{meta["color"]};">'
                f'{score}/10</div>'
                f'<div style="background:rgba(255,255,255,0.08);border-radius:6px;'
                f'height:8px;margin:8px 0;">'
                f'<div style="width:{pct}%;background:{meta["color"]};height:100%;'
                f'border-radius:6px;transition:width 0.5s;"></div></div>'
                f'<div style="font-size:10px;color:#5a6580;margin-top:4px;">{meta["desc"]}</div>'
                f'<div style="font-size:10px;color:#6b7a94;margin-top:6px;">{detail_str}</div>'
                f'</div>', unsafe_allow_html=True)

    # --- Radar chart ---
    st.markdown("### Vegetation Radar")
    st.plotly_chart(_build_radar(scores, key="vegind_pchart2"), use_container_width=True,
                    key="vegidx_radar_chart")

    # --- Bar chart ---
    st.markdown("### Dimension Comparison")
    st.plotly_chart(_build_bar(scores, key="vegind_pchart3"), use_container_width=True,
                    key="vegidx_bar_chart")

    # --- Folium map ---
    st.markdown("### Vegetation Map")
    st.caption("Green overlay zones showing scan radii and estimated vegetation density")
    map_scores = dict(scores)
    map_scores["_overall"] = overall
    map_scores["_ndvi"] = ndvi
    _veg_map = _build_map(lat, lon, map_scores)
    if _veg_map is not None and st_folium is not None:
        st_folium(_veg_map, width=None, height=480,
                  key="vegidx_folium_map")
    else:
        st.warning("Install `folium` and `streamlit-folium` for interactive map: "
                   "`pip install folium streamlit-folium`")

    # --- Insights ---
    st.markdown("### Vegetation Insights")
    for ins in _generate_insights(result):
        st.markdown(
            f'<div style="background:rgba(34,197,94,0.07);border-left:4px solid #22c55e;'
            f'border-radius:0 10px 10px 0;padding:12px 18px;margin:8px 0;">'
            f'<span style="color:#c8d6e5;font-size:13px;">{ins}</span></div>',
            unsafe_allow_html=True)

    # --- Recommendations ---
    st.markdown("### Recommendations")
    for rec in _generate_recommendations(result):
        st.markdown(
            f'<div style="background:rgba(59,130,246,0.07);border-left:4px solid #3b82f6;'
            f'border-radius:0 10px 10px 0;padding:10px 16px;margin:6px 0;">'
            f'<span style="color:#a3b8d0;font-size:12px;">{rec}</span></div>',
            unsafe_allow_html=True)

    # --- Detailed data expander ---
    with st.expander("Raw Dimension Data", expanded=False):
        for dim in dim_names:
            st.markdown(f"**{DIMENSION_META[dim]['icon']} {dim}** — Score: {scores[dim]}/10")
            for k, v in details.get(dim, {}).items():
                st.markdown(f"- {k.replace('_', ' ').title()}: `{v}`")
        st.markdown("---")
        st.markdown(f"**Synthetic NDVI Proxy:** `{ndvi}`")
        st.markdown(f"**Classification:** {ndvi_label}")
        st.markdown(f"**Overall Score:** {overall}/10")

    # --- NDVI classification reference ---
    st.markdown("### NDVI Classification Reference")
    ref_data = []
    for lbl, lo, hi, _clr in NDVI_CLASSES:
        marker = " ◀" if lbl == ndvi_label else ""
        ref_data.append({"Class": f"{lbl}{marker}", "NDVI Range": f"{lo:.1f} – {hi:.1f}",
                         "Description": NDVI_DESCRIPTIONS.get(lbl, "")})
    st.table(ref_data)

    # --- Scoring methodology ---
    with st.expander("Scoring Methodology", expanded=False):
        st.markdown("The **Synthetic NDVI Proxy** is computed as a weighted average "
                    "of six normalised dimension scores:\n")
        for dim, w in DIMENSION_WEIGHTS.items():
            pct_w = int(w * 100)
            st.markdown(f"- **{dim}**: {pct_w}% weight (score {scores[dim]}/10 "
                        f"→ contribution {scores[dim] * w:.2f})")
        st.markdown(
            f"\n**Weighted sum / 10 = NDVI proxy = {ndvi}**\n\n"
            "Data sources: OpenStreetMap (Overpass), ISRIC SoilGrids v2.0, "
            "Open-Meteo, iNaturalist. All APIs are free and require no keys.")
