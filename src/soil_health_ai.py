"""
Soil Health & Fertility AI module for TerraScout AI.
Comprehensive soil analysis with actionable recommendations for farming,
construction, and remediation. Free APIs: SoilGrids v2.0, Open-Meteo, Open-Elevation.
"""
import streamlit as st
import requests
import json
import math
import pandas as pd
try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
SOILGRIDS_URL = (
    "https://rest.isric.org/soilgrids/v2.0/properties/query"
    "?lon={lon}&lat={lat}"
    "&property=clay&property=sand&property=silt"
    "&property=soc&property=cec&property=nitrogen"
    "&property=phh2o&property=bdod"
    "&depth=0-5cm&depth=5-15cm&depth=15-30cm&depth=30-60cm"
    "&value=mean"
)
OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude={lat}&longitude={lon}"
    "&daily=temperature_2m_mean,precipitation_sum"
    "&timezone=auto&past_days=30&forecast_days=0"
)
OPEN_ELEVATION_URL = (
    "https://api.open-elevation.com/api/v1/lookup"
    "?locations={lat},{lon}"
)
DEPTH_LABELS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm"]

USDA_TEXTURE_CLASSES = {
    "Clay":            {"clay": (40, 100), "sand": (0, 45),  "silt": (0, 40)},
    "Silty Clay":      {"clay": (40, 60),  "sand": (0, 20),  "silt": (40, 60)},
    "Sandy Clay":      {"clay": (35, 55),  "sand": (45, 65), "silt": (0, 20)},
    "Clay Loam":       {"clay": (27, 40),  "sand": (20, 45), "silt": (15, 53)},
    "Silty Clay Loam": {"clay": (27, 40),  "sand": (0, 20),  "silt": (40, 73)},
    "Sandy Clay Loam": {"clay": (20, 35),  "sand": (45, 80), "silt": (0, 28)},
    "Loam":            {"clay": (7, 27),   "sand": (23, 52), "silt": (28, 50)},
    "Silt Loam":       {"clay": (0, 27),   "sand": (0, 50),  "silt": (50, 88)},
    "Silt":            {"clay": (0, 12),   "sand": (0, 20),  "silt": (80, 100)},
    "Sandy Loam":      {"clay": (0, 20),   "sand": (43, 85), "silt": (0, 50)},
    "Loamy Sand":      {"clay": (0, 15),   "sand": (70, 90), "silt": (0, 30)},
    "Sand":            {"clay": (0, 10),   "sand": (85, 100), "silt": (0, 15)},
}
TEXTURE_COLORS = {
    "Clay": "#c0392b", "Silty Clay": "#e74c3c", "Sandy Clay": "#d35400",
    "Clay Loam": "#e67e22", "Silty Clay Loam": "#f39c12",
    "Sandy Clay Loam": "#f1c40f", "Loam": "#27ae60", "Silt Loam": "#2ecc71",
    "Silt": "#1abc9c", "Sandy Loam": "#3498db", "Loamy Sand": "#2980b9",
    "Sand": "#9b59b6",
}
SOIL_HEALTH_PRESETS = {
    "Custom": None, "Iowa Black Soil, USA": (42.03, -93.47),
    "Ukraine Chernozem": (49.00, 32.00), "Amazon Basin, Brazil": (-3.10, -60.00),
    "Sahara Desert, Algeria": (27.00, 2.00), "Tuscany, Italy": (43.30, 11.30),
    "Nile Delta, Egypt": (30.90, 31.20), "Dutch Polders, Netherlands": (52.50, 5.00),
    "Java Volcanic, Indonesia": (-7.50, 110.40), "Pampas, Argentina": (-35.00, -60.00),
    "Punjab, India": (31.00, 75.00), "Loire Valley, France": (47.30, 1.00),
    "Canterbury Plains, NZ": (-43.50, 172.00), "Mekong Delta, Vietnam": (10.00, 106.00),
    "Great Plains, USA": (40.80, -99.70),
}

def _safe_get(url, timeout=10):
    """Shared GET with error wrapping."""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        return {"error": str(exc)}

@st.cache_data(ttl=900)
def _fetch_soilgrids(lat: float, lon: float) -> dict:
    return _safe_get(SOILGRIDS_URL.format(lat=lat, lon=lon))

@st.cache_data(ttl=900)
def _fetch_climate(lat: float, lon: float) -> dict:
    return _safe_get(OPEN_METEO_URL.format(lat=lat, lon=lon))

@st.cache_data(ttl=900)
def _fetch_elevation(lat: float, lon: float) -> dict:
    return _safe_get(OPEN_ELEVATION_URL.format(lat=lat, lon=lon))

def _parse_soilgrids(soil: dict):
    """Parse SoilGrids v2.0 response. Returns (_sv helper, _layer_map, all_depths dict)."""
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

    # Build full depth profile: {property: {depth_label: raw_value}}
    all_depths = {}
    for prop_name, layer_data in _layer_map.items():
        if not isinstance(layer_data, dict):
            continue
        depths_list = layer_data.get("depths", [])
        depth_dict = {}
        for d in (depths_list if isinstance(depths_list, list) else []):
            label = d.get("label", "") if isinstance(d, dict) else ""
            raw_val = d.get("values", {}).get("mean") if isinstance(d, dict) else None
            depth_dict[label] = raw_val
        all_depths[prop_name] = depth_dict
    return _sv, _layer_map, all_depths

def _classify_texture(clay_pct, sand_pct, silt_pct):
    """Classify soil using USDA texture triangle rules."""
    if clay_pct is None or sand_pct is None or silt_pct is None:
        return "Unknown"
    total = clay_pct + sand_pct + silt_pct
    if total < 1:
        return "Unknown"
    c, sa, si = clay_pct / total * 100, sand_pct / total * 100, silt_pct / total * 100
    if c >= 40:
        if si >= 40:
            return "Silty Clay"
        if sa >= 45:
            return "Sandy Clay"
        return "Clay"
    if 27 <= c < 40:
        if 20 <= sa < 45:
            return "Clay Loam"
        if sa < 20 and si >= 40:
            return "Silty Clay Loam"
        if sa >= 45:
            return "Sandy Clay Loam"
        return "Clay Loam"
    if 20 <= c < 27 and sa >= 45:
        return "Sandy Clay Loam"
    if c < 7 and si >= 80:
        return "Silt"
    if si >= 50 and c < 27:
        return "Silt Loam"
    if 7 <= c < 27 and 23 <= sa <= 52 and si >= 28:
        return "Loam"
    if sa >= 85:
        return "Sand"
    if sa >= 70:
        return "Loamy Sand"
    if sa >= 43:
        return "Sandy Loam"
    return "Loam"

def _fertility_score(soc, cec, nitrogen, ph):
    """Compute composite fertility index 0-100."""
    scores = []
    if soc is not None:
        scores.append(min(soc / 5.0, 1.0) * 100)
    if cec is not None:
        scores.append(min(cec / 30.0, 1.0) * 100)
    if nitrogen is not None:
        scores.append(min(nitrogen / 3.0, 1.0) * 100)
    if ph is not None:
        if 6.0 <= ph <= 7.0:
            scores.append(100)
        elif 5.5 <= ph < 6.0 or 7.0 < ph <= 7.5:
            scores.append(80)
        elif 5.0 <= ph < 5.5 or 7.5 < ph <= 8.0:
            scores.append(60)
        elif 4.5 <= ph < 5.0 or 8.0 < ph <= 8.5:
            scores.append(40)
        else:
            scores.append(20)
    return round(sum(scores) / len(scores), 1) if scores else None

def _drainage_class(clay_pct, sand_pct, elevation, slope_est):
    """Classify drainage based on texture + terrain."""
    if clay_pct is None or sand_pct is None:
        return "Unknown", "grey"
    ratio = clay_pct / max(sand_pct, 0.1)
    bonus = 0
    if elevation is not None and elevation > 500:
        bonus += 0.5
    if slope_est is not None and slope_est > 5:
        bonus += 0.5
    effective = ratio - bonus * 0.3
    if effective > 2.0:
        return "Poorly Drained", "#e74c3c"
    elif effective > 1.0:
        return "Somewhat Poorly Drained", "#e67e22"
    elif effective > 0.5:
        return "Moderately Well Drained", "#f1c40f"
    elif effective > 0.2:
        return "Well Drained", "#2ecc71"
    else:
        return "Excessively Drained", "#3498db"

def _carbon_storage_potential(soc, mean_precip_mm, mean_temp_c):
    """Estimate carbon storage potential based on SOC + climate."""
    if soc is None:
        return None, "Unknown"
    precip_factor = 1.0
    if mean_precip_mm is not None:
        daily_avg = mean_precip_mm / 30.0 if mean_precip_mm > 0 else 0
        if daily_avg > 3:
            precip_factor = 1.3
        elif daily_avg > 1:
            precip_factor = 1.1
    temp_factor = 1.0
    if mean_temp_c is not None:
        if mean_temp_c < 5:
            temp_factor = 1.4
        elif mean_temp_c < 15:
            temp_factor = 1.2
        elif mean_temp_c > 25:
            temp_factor = 0.8
    potential = soc * precip_factor * temp_factor
    label = "High" if potential > 6 else "Moderate" if potential > 3 else "Low"
    return round(potential, 2), label

def _remediation_needs(ph, nitrogen, clay_pct, soc, cec):
    """Identify soil deficiencies and remediation actions."""
    issues = []
    if ph is not None:
        if ph < 5.5:
            issues.append(("Low pH (Acidic)", f"pH = {ph:.1f}",
                           "Apply agricultural lime (CaCO3) at 2-4 t/ha", "high"))
        elif ph > 8.0:
            issues.append(("High pH (Alkaline)", f"pH = {ph:.1f}",
                           "Apply sulfur or gypsum; use acidifying fertilisers", "high"))
    if nitrogen is not None and nitrogen < 1.0:
        issues.append(("Low Nitrogen", f"N = {nitrogen:.2f} g/kg",
                       "Apply nitrogen fertiliser or grow legume cover crops", "high"))
    if soc is not None and soc < 1.5:
        issues.append(("Low Organic Carbon", f"SOC = {soc:.1f} g/kg",
                       "Add compost, manure, or biochar; practice no-till", "medium"))
    if cec is not None and cec < 10:
        issues.append(("Low CEC", f"CEC = {cec:.1f} cmol/kg",
                       "Add organic matter to improve nutrient retention", "medium"))
    if clay_pct is not None and clay_pct > 50:
        issues.append(("Very High Clay", f"Clay = {clay_pct:.0f}%",
                       "Install drainage tiles; add sand/organic matter", "medium"))
    if clay_pct is not None and clay_pct < 5 and soc is not None and soc < 2:
        issues.append(("Very Sandy + Low Organic", f"Clay={clay_pct:.0f}%, SOC={soc:.1f}",
                       "Add clay amendments or biochar to improve water retention", "medium"))
    return issues

def _use_recommendations(texture_class, ph, soc, clay_pct, sand_pct, drainage_label):
    """Generate use-specific recommendations."""
    recs = {"crops": [], "construction": [], "remediation": []}
    if texture_class in ("Loam", "Silt Loam", "Clay Loam"):
        recs["crops"].extend(["Wheat", "Corn", "Soybeans", "Potatoes", "Sunflowers"])
    elif texture_class in ("Sandy Loam", "Loamy Sand"):
        recs["crops"].extend(["Carrots", "Peanuts", "Watermelon", "Sweet Potatoes"])
    elif texture_class in ("Clay", "Silty Clay", "Sandy Clay"):
        recs["crops"].extend(["Rice", "Cabbage", "Broccoli", "Wet-season crops"])
    elif texture_class == "Sand":
        recs["crops"].extend(["Cactus / Succulents", "Lavender", "Drought-tolerant grasses"])
    elif texture_class == "Silt":
        recs["crops"].extend(["Lettuce", "Onions", "Herbs"])
    else:
        recs["crops"].extend(["General vegetables", "Cover crops"])
    if ph is not None:
        if ph < 5.5:
            recs["crops"].append("Blueberries (acid-loving)")
        if 6.0 <= ph <= 7.0:
            recs["crops"].append("Most vegetables thrive")
    if clay_pct is not None and clay_pct > 35:
        recs["construction"].extend(["Poor for foundations (shrink-swell risk)",
                                      "Suitable for earthen dams / ponds"])
    elif sand_pct is not None and sand_pct > 70:
        recs["construction"].extend(["Good bearing capacity for foundations",
                                      "Poor water retention for landscaping"])
    else:
        recs["construction"].extend(["Moderate foundation suitability",
                                      "Adequate for general construction"])
    if drainage_label in ("Poorly Drained", "Somewhat Poorly Drained"):
        recs["construction"].append("Requires drainage system before building")
    if soc is not None and soc < 2:
        recs["remediation"].append("Priority: Increase organic matter (compost, mulch)")
    if ph is not None and ph < 5.5:
        recs["remediation"].append("Apply lime to raise pH to 6.0-6.5")
    if ph is not None and ph > 8.0:
        recs["remediation"].append("Apply elemental sulfur to lower pH")
    if drainage_label == "Poorly Drained":
        recs["remediation"].append("Install subsurface drainage tiles")
    if not recs["remediation"]:
        recs["remediation"].append("No urgent remediation needed")
    return recs

def _build_ternary_plot(clay_pct, sand_pct, silt_pct, texture_class):
    """Build a Plotly ternary (soil texture triangle) diagram."""
    fig = go.Figure(go.Scatterternary(
        a=[clay_pct], b=[sand_pct], c=[silt_pct],
        mode="markers+text",
        marker=dict(size=16, color=TEXTURE_COLORS.get(texture_class, "#2ecc71"),
                    line=dict(width=2, color="black")),
        text=[texture_class], textposition="top center",
        textfont=dict(size=13, color="white"), name="Sample",
    ))
    for rc, rs, rsi, rname in [
        (60, 20, 20, "Clay"), (15, 65, 20, "Sandy Loam"),
        (15, 15, 70, "Silt Loam"), (20, 40, 40, "Loam"),
        (5, 90, 5, "Sand"), (5, 5, 90, "Silt"),
    ]:
        fig.add_trace(go.Scatterternary(
            a=[rc], b=[rs], c=[rsi], mode="text", text=[rname],
            textfont=dict(size=9, color="rgba(255,255,255,0.45)"),
            showlegend=False, hoverinfo="skip",
        ))
    fig.update_layout(
        ternary=dict(
            aaxis=dict(title="Clay %", min=0, linewidth=2, color="#e74c3c",
                       gridcolor="rgba(255,255,255,0.15)"),
            baxis=dict(title="Sand %", min=0, linewidth=2, color="#3498db",
                       gridcolor="rgba(255,255,255,0.15)"),
            caxis=dict(title="Silt %", min=0, linewidth=2, color="#2ecc71",
                       gridcolor="rgba(255,255,255,0.15)"),
            bgcolor="rgba(0,0,0,0)",
        ),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"), margin=dict(l=60, r=60, t=40, b=40),
        height=420, title=dict(text="USDA Soil Texture Triangle", font=dict(size=15)),
    )
    return fig

def _build_depth_profile_chart(all_depths):
    """Build grouped bar chart of soil properties across depths."""
    props_config = {
        "clay": ("Clay %", 10), "sand": ("Sand %", 10), "silt": ("Silt %", 10),
        "soc": ("SOC g/kg", 10), "phh2o": ("pH", 10), "nitrogen": ("N g/kg", 100),
        "cec": ("CEC cmol/kg", 10), "bdod": ("Bulk Dens. kg/dm3", 100),
    }
    rows = []
    for prop_name, (display, div) in props_config.items():
        if prop_name not in all_depths:
            continue
        for depth_label in DEPTH_LABELS:
            raw = all_depths[prop_name].get(depth_label)
            val = raw / div if raw is not None else None
            if val is not None:
                rows.append({"Property": display, "Depth": depth_label, "Value": val})
    if not rows:
        return None
    df = pd.DataFrame(rows)
    fig = px.bar(df, x="Depth", y="Value", color="Property", barmode="group",
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"), height=420,
        title=dict(text="Soil Properties by Depth", font=dict(size=15)),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
        legend=dict(bgcolor="rgba(0,0,0,0)"), margin=dict(l=50, r=20, t=50, b=40),
    )
    return fig

def _build_ph_gauge(ph_value):
    """Build a pH gauge chart."""
    if ph_value is None:
        return None
    bar_color = ("#2ecc71" if 6.0 <= ph_value <= 7.0 else
                 "#e67e22" if 5.0 <= ph_value <= 8.0 else "#e74c3c")
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=ph_value,
        number=dict(font=dict(size=36, color="white")),
        gauge=dict(
            axis=dict(range=[3, 10], tickwidth=2, tickcolor="white",
                      tickfont=dict(color="white")),
            bar=dict(color=bar_color), bgcolor="rgba(0,0,0,0)",
            steps=[
                dict(range=[3, 5], color="rgba(231,76,60,0.25)"),
                dict(range=[5, 6], color="rgba(230,126,34,0.25)"),
                dict(range=[6, 7], color="rgba(46,204,113,0.25)"),
                dict(range=[7, 8], color="rgba(230,126,34,0.25)"),
                dict(range=[8, 10], color="rgba(231,76,60,0.25)"),
            ],
            threshold=dict(line=dict(color="white", width=3),
                           thickness=0.8, value=ph_value),
        ),
        title=dict(text="Soil pH", font=dict(size=16, color="white")),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
        height=280, margin=dict(l=30, r=30, t=60, b=20),
    )
    return fig

def _build_fertility_radar(soc, cec, nitrogen, ph, clay_pct):
    """Build radar chart of fertility components."""
    categories, values = [], []
    if soc is not None:
        categories.append("Organic Carbon"); values.append(min(soc / 5.0 * 100, 100))
    if cec is not None:
        categories.append("CEC"); values.append(min(cec / 30.0 * 100, 100))
    if nitrogen is not None:
        categories.append("Nitrogen"); values.append(min(nitrogen / 3.0 * 100, 100))
    if ph is not None:
        categories.append("pH Optimality")
        values.append(100 if 6.0 <= ph <= 7.0 else 80 if 5.5 <= ph <= 7.5 else 50)
    if clay_pct is not None:
        categories.append("Texture Balance")
        values.append(100 if 15 <= clay_pct <= 35 else 70 if 10 <= clay_pct <= 45 else 40)
    if not categories:
        return None
    categories.append(categories[0]); values.append(values[0])
    fig = go.Figure(go.Scatterpolar(
        r=values, theta=categories, fill="toself",
        fillcolor="rgba(46,204,113,0.3)",
        line=dict(color="#2ecc71", width=2),
        marker=dict(size=6, color="#2ecc71"),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0, 100], gridcolor="rgba(255,255,255,0.15)",
                            tickfont=dict(color="white", size=9)),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.15)",
                             tickfont=dict(color="white", size=11)),
        ),
        paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
        height=380, margin=dict(l=60, r=60, t=40, b=40),
        title=dict(text="Fertility Radar", font=dict(size=15)), showlegend=False,
    )
    return fig

def _build_location_map(lat, lon, texture_class, fertility, drainage_label):
    """Build folium map centred on the sample location."""
    m = folium.Map(location=[lat, lon], zoom_start=10, tiles="CartoDB dark_matter")
    popup_html = (
        f"<b>Soil Analysis</b><br>Texture: {texture_class}<br>"
        f"Fertility: {fertility}/100<br>Drainage: {drainage_label}<br>"
        f"Coords: {lat:.4f}, {lon:.4f}"
    )
    folium.Marker(
        [lat, lon], popup=folium.Popup(popup_html, max_width=250),
        icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
    ).add_to(m)
    folium.CircleMarker(
        [lat, lon], radius=40, color="#2ecc71", fill=True,
        fill_opacity=0.15, weight=1,
    ).add_to(m)
    return m

def render_soil_health_ai_tab():
    """Single entry point for the Soil Health & Fertility AI tab."""
    st.markdown("## Soil Health & Fertility AI")
    st.caption(
        "Comprehensive soil analysis with fertility scoring, drainage classification, "
        "carbon storage potential & actionable recommendations for farming, construction "
        "and remediation. Powered by ISRIC SoilGrids 250m + Open-Meteo."
    )

    # ── Location Input ──
    st.markdown("---")
    st.markdown("### Location")
    preset = st.selectbox(
        "Preset Locations", list(SOIL_HEALTH_PRESETS.keys()), key="soilh_preset",
        help="Choose a well-known soil location or enter custom coordinates.",
    )
    if preset != "Custom" and SOIL_HEALTH_PRESETS.get(preset):
        default_lat, default_lon = SOIL_HEALTH_PRESETS[preset]
    else:
        default_lat, default_lon = 43.30, 11.30

    col_lat, col_lon = st.columns(2)
    with col_lat:
        lat = st.number_input("Latitude", value=default_lat, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="soilh_lat")
    with col_lon:
        lon = st.number_input("Longitude", value=default_lon, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="soilh_lon")

    analyse_btn = st.button("Analyse Soil Health", key="soilh_analyse",
                            type="primary", use_container_width=True)
    if analyse_btn:
        st.session_state["soilh_run"] = {"lat": lat, "lon": lon}
    if "soilh_run" not in st.session_state:
        st.info("Select a location and click **Analyse Soil Health** to begin.")
        return

    run = st.session_state["soilh_run"]
    lat, lon = run["lat"], run["lon"]

    # ── Fetch all data ──
    with st.spinner("Querying ISRIC SoilGrids v2.0 ..."):
        soil_raw = _fetch_soilgrids(lat, lon)
    if soil_raw.get("error"):
        st.error(f"SoilGrids API error: {soil_raw['error']}")
        return

    _sv, _layer_map, all_depths = _parse_soilgrids(soil_raw)

    # Extract key values (top layer)
    clay_pct = _sv("clay", div=10)
    sand_pct = _sv("sand", div=10)
    silt_pct = _sv("silt", div=10)
    soc = _sv("soc", div=10)
    cec = _sv("cec", div=10)
    nitrogen = _sv("nitrogen", div=100)
    ph = _sv("phh2o", div=10)
    bdod = _sv("bdod", div=100)

    climate = _fetch_climate(lat, lon)
    elev_data = _fetch_elevation(lat, lon)

    # Parse climate
    mean_temp, total_precip = None, None
    if not climate.get("error"):
        daily = climate.get("daily", {})
        temps = [t for t in daily.get("temperature_2m_mean", []) if t is not None]
        precips = [p for p in daily.get("precipitation_sum", []) if p is not None]
        mean_temp = sum(temps) / len(temps) if temps else None
        total_precip = sum(precips) if precips else None

    # Parse elevation
    elevation = None
    if not elev_data.get("error"):
        results = elev_data.get("results", [])
        if results:
            elevation = results[0].get("elevation")

    # -- Section 1: Soil Texture Triangle --
    st.markdown("---")
    st.markdown("### 1. Soil Texture Classification")
    texture_class = _classify_texture(clay_pct, sand_pct, silt_pct)
    tex_color = TEXTURE_COLORS.get(texture_class, "#95a5a6")

    col_badge, col_vals = st.columns([1, 2])
    with col_badge:
        st.markdown(
            f'<div style="background:{tex_color}; padding:18px 24px; '
            f'border-radius:12px; text-align:center;">'
            f'<span style="font-size:28px; font-weight:700; color:white;">'
            f'{texture_class}</span><br>'
            f'<span style="color:rgba(255,255,255,0.8); font-size:13px;">'
            f'USDA Classification</span></div>',
            unsafe_allow_html=True,
        )
    with col_vals:
        mc1, mc2, mc3 = st.columns(3)
        mc1.metric("Clay", f"{clay_pct:.1f}%" if clay_pct is not None else "N/A")
        mc2.metric("Sand", f"{sand_pct:.1f}%" if sand_pct is not None else "N/A")
        mc3.metric("Silt", f"{silt_pct:.1f}%" if silt_pct is not None else "N/A")

    if clay_pct is not None and sand_pct is not None and silt_pct is not None:
        st.plotly_chart(_build_ternary_plot(clay_pct, sand_pct, silt_pct, texture_class, key="sha_pchart1"),
                        use_container_width=True, key="soilh_ternary")

    # -- Section 2: Fertility Index --
    st.markdown("---")
    st.markdown("### 2. Fertility Index")
    fertility = _fertility_score(soc, cec, nitrogen, ph)

    col_score, col_radar = st.columns([1, 2])
    with col_score:
        if fertility is not None:
            if fertility >= 70:
                fert_color, fert_label = "#2ecc71", "High Fertility"
            elif fertility >= 45:
                fert_color, fert_label = "#f39c12", "Moderate Fertility"
            else:
                fert_color, fert_label = "#e74c3c", "Low Fertility"
            st.markdown(
                f'<div style="background:{fert_color}; padding:20px; '
                f'border-radius:12px; text-align:center;">'
                f'<span style="font-size:42px; font-weight:800; color:white;">'
                f'{fertility}</span><br>'
                f'<span style="color:rgba(255,255,255,0.85); font-size:14px;">'
                f'{fert_label} (0-100)</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.warning("Insufficient data to compute fertility index.")
        st.markdown("")
        for name, (val, unit) in {"SOC": (soc, "g/kg"), "CEC": (cec, "cmol/kg"),
                                   "Nitrogen": (nitrogen, "g/kg"), "pH": (ph, "")}.items():
            if val is not None:
                st.markdown(f"**{name}:** {val:.2f} {unit}")
    with col_radar:
        radar_fig = _build_fertility_radar(soc, cec, nitrogen, ph, clay_pct)
        if radar_fig:
            st.plotly_chart(radar_fig, use_container_width=True, key="soilh_radar")

    # -- Section 3: Depth Profile --
    st.markdown("---")
    st.markdown("### 3. Depth Profile Analysis")
    st.caption("Properties across four depth layers: 0-5cm, 5-15cm, 15-30cm, 30-60cm")
    depth_fig = _build_depth_profile_chart(all_depths)
    if depth_fig:
        st.plotly_chart(depth_fig, use_container_width=True, key="soilh_depth")

    with st.expander("Raw Depth Data Table", expanded=False):
        props_div = {"clay": 10, "sand": 10, "silt": 10, "soc": 10,
                     "phh2o": 10, "nitrogen": 100, "cec": 10, "bdod": 100}
        table_rows = []
        for prop_name in ["clay", "sand", "silt", "soc", "phh2o", "nitrogen", "cec", "bdod"]:
            if prop_name not in all_depths:
                continue
            row = {"Property": prop_name}
            div = props_div.get(prop_name, 10)
            for dl in DEPTH_LABELS:
                raw = all_depths[prop_name].get(dl)
                row[dl] = round(raw / div, 2) if raw is not None else None
            table_rows.append(row)
        if table_rows:
            st.dataframe(pd.DataFrame(table_rows).set_index("Property"),
                         use_container_width=True, key="soilh_depth_table")

    # -- Section 4: pH + Drainage --
    st.markdown("---")
    col_ph, col_drain = st.columns(2)
    with col_ph:
        st.markdown("### 4a. pH Analysis")
        ph_fig = _build_ph_gauge(ph)
        if ph_fig:
            st.plotly_chart(ph_fig, use_container_width=True, key="soilh_ph_gauge")
            if ph is not None:
                if ph < 5.5:
                    st.warning(f"Strongly acidic (pH {ph:.1f}). Liming recommended.")
                elif ph < 6.0:
                    st.info(f"Slightly acidic (pH {ph:.1f}). Acceptable for most crops.")
                elif ph <= 7.0:
                    st.success(f"Optimal range (pH {ph:.1f}). Ideal for nutrient availability.")
                elif ph <= 8.0:
                    st.info(f"Slightly alkaline (pH {ph:.1f}). Monitor micronutrient availability.")
                else:
                    st.warning(f"Strongly alkaline (pH {ph:.1f}). Sulfur amendment recommended.")
        else:
            st.warning("pH data not available.")

    with col_drain:
        st.markdown("### 4b. Drainage Classification")
        slope_est = 2.0
        if elevation is not None and elevation > 200:
            slope_est = min(elevation / 100.0, 15.0)
        drainage_label, drain_color = _drainage_class(clay_pct, sand_pct, elevation, slope_est)
        st.markdown(
            f'<div style="background:{drain_color}; padding:20px; '
            f'border-radius:12px; text-align:center; margin-top:10px;">'
            f'<span style="font-size:22px; font-weight:700; color:white;">'
            f'{drainage_label}</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown("")
        drain_factors = []
        if clay_pct is not None and sand_pct is not None:
            drain_factors.append(f"Clay/Sand ratio: {clay_pct / max(sand_pct, 0.1):.2f}")
        if elevation is not None:
            drain_factors.append(f"Elevation: {elevation:.0f} m")
        drain_factors.append(f"Est. slope factor: {slope_est:.1f} deg")
        for f in drain_factors:
            st.markdown(f"- {f}")
        if drainage_label == "Poorly Drained":
            st.error("High waterlogging risk. Tile drainage or raised beds needed.")
        elif drainage_label == "Somewhat Poorly Drained":
            st.warning("Seasonal waterlogging possible. Consider surface contouring.")
        elif drainage_label == "Well Drained":
            st.success("Good natural drainage. Suitable for most uses.")
        elif drainage_label == "Excessively Drained":
            st.info("Water retention may be low. Irrigation likely needed.")
        else:
            st.info("Moderate drainage. Generally adequate.")

    # -- Section 5: Carbon Storage Potential --
    st.markdown("---")
    st.markdown("### 5. Carbon Storage Potential")
    carbon_potential, carbon_label = _carbon_storage_potential(soc, total_precip, mean_temp)

    col_cp1, col_cp2 = st.columns([1, 2])
    with col_cp1:
        if carbon_potential is not None:
            cp_colors = {"High": "#2ecc71", "Moderate": "#f39c12", "Low": "#e74c3c"}
            st.markdown(
                f'<div style="background:{cp_colors.get(carbon_label, "#95a5a6")}; '
                f'padding:20px; border-radius:12px; text-align:center;">'
                f'<span style="font-size:28px; font-weight:700; color:white;">'
                f'{carbon_label}</span><br>'
                f'<span style="color:rgba(255,255,255,0.85); font-size:13px;">'
                f'Score: {carbon_potential}</span></div>',
                unsafe_allow_html=True,
            )
        else:
            st.warning("SOC data unavailable for carbon analysis.")
    with col_cp2:
        st.markdown("**Factors influencing carbon storage:**")
        factors = []
        if soc is not None:
            factors.append(f"Soil Organic Carbon: {soc:.1f} g/kg")
        if mean_temp is not None:
            factors.append(f"Mean temperature (30d): {mean_temp:.1f} C")
        if total_precip is not None:
            factors.append(f"Total precipitation (30d): {total_precip:.1f} mm")
        if elevation is not None:
            factors.append(f"Elevation: {elevation:.0f} m")
        for f in factors:
            st.markdown(f"- {f}")
        st.markdown("**Strategies to increase carbon storage:**")
        strategies = [
            "Practice no-till / minimum tillage agriculture",
            "Plant cover crops during fallow periods",
            "Apply compost or biochar amendments",
            "Maintain permanent grass/forest cover where possible",
        ]
        if mean_temp is not None and mean_temp > 25:
            strategies.append("Use mulching to reduce decomposition in hot climate")
        if total_precip is not None and total_precip < 30:
            strategies.append("Irrigate to maintain microbial activity for carbon fixation")
        for s in strategies:
            st.markdown(f"  - {s}")

    # -- Section 6: Remediation Needs --
    st.markdown("---")
    st.markdown("### 6. Remediation Assessment")
    issues = _remediation_needs(ph, nitrogen, clay_pct, soc, cec)

    if issues:
        st.markdown(f"**{len(issues)} issue(s) identified:**")
        for issue_name, detail, action, severity in issues:
            sev_color = {"high": "#e74c3c", "medium": "#e67e22", "low": "#f1c40f"}
            st.markdown(
                f'<div style="border-left: 4px solid {sev_color.get(severity, "#95a5a6")}; '
                f'padding: 10px 16px; margin: 8px 0; '
                f'background: rgba(255,255,255,0.04); border-radius: 0 8px 8px 0;">'
                f'<strong style="color:{sev_color.get(severity, "#fff")};">'
                f'{issue_name}</strong> &mdash; {detail}<br>'
                f'<span style="color:rgba(255,255,255,0.7);">Recommendation: {action}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.success("No significant soil health issues detected. Soil is in good condition.")

    with st.expander("Remediation Priority Checklist", expanded=False):
        checklist_items = [
            ("Test pH and apply lime/sulfur if needed",
             ph is not None and (ph < 5.5 or ph > 8.0)),
            ("Add nitrogen fertiliser or legume cover crops",
             nitrogen is not None and nitrogen < 1.0),
            ("Increase organic matter with compost/biochar",
             soc is not None and soc < 2.0),
            ("Improve CEC with organic amendments",
             cec is not None and cec < 10),
            ("Address drainage issues",
             clay_pct is not None and clay_pct > 50),
            ("Improve water retention (sandy soils)",
             sand_pct is not None and sand_pct > 80),
        ]
        for item_text, is_needed in checklist_items:
            icon = "!!!" if is_needed else "OK "
            color = "#e74c3c" if is_needed else "#2ecc71"
            st.markdown(
                f'<span style="color:{color}; font-weight:600;">[{icon}]</span> {item_text}',
                unsafe_allow_html=True,
            )

    # -- Section 7: Use Recommendations --
    st.markdown("---")
    st.markdown("### 7. Use Recommendations")
    recs = _use_recommendations(texture_class, ph, soc, clay_pct, sand_pct, drainage_label)

    tab_crops, tab_const, tab_remed = st.tabs([
        "Best Crops", "Construction Suitability", "Remediation Plan"
    ])
    with tab_crops:
        st.markdown("**Recommended crops for this soil type:**")
        for crop in recs["crops"]:
            st.markdown(f"- {crop}")
        st.markdown("")
        st.markdown(f"*Based on {texture_class} texture, "
                    f"pH {ph:.1f if ph else 'N/A'}, drainage: {drainage_label}*")
    with tab_const:
        st.markdown("**Construction assessment:**")
        for item in recs["construction"]:
            st.markdown(f"- {item}")
        if bdod is not None:
            st.markdown(f"- Bulk density: {bdod:.2f} kg/dm3")
            if bdod > 1.6:
                st.markdown("  - High compaction detected; may affect excavation costs")
            elif bdod < 1.2:
                st.markdown("  - Low density; check for organic/peaty layers")
    with tab_remed:
        st.markdown("**Remediation plan:**")
        for item in recs["remediation"]:
            st.markdown(f"- {item}")
        st.markdown("")
        st.markdown("**Estimated effort levels:**")
        effort_map = {
            "Apply lime": "Low cost, seasonal application",
            "sulfur": "Low cost, seasonal application",
            "compost": "Medium cost, annual application",
            "drainage": "High cost, one-time installation",
            "No urgent": "Maintenance only",
        }
        for keyword, effort in effort_map.items():
            for item in recs["remediation"]:
                if keyword.lower() in item.lower():
                    st.markdown(f"  - *{effort}*")
                    break

    # -- Location Map --
    st.markdown("---")
    st.markdown("### Sample Location Map")
    soil_map = _build_location_map(lat, lon, texture_class, fertility, drainage_label)
    components.html(soil_map._repr_html_(), height=450)

    # -- Summary Card --
    st.markdown("---")
    st.markdown("### Analysis Summary")
    summary_items = [
        ("Location", f"{lat:.4f}, {lon:.4f}"),
        ("Elevation", f"{elevation:.0f} m" if elevation is not None else "N/A"),
        ("Soil Texture", texture_class),
        ("Fertility Score", f"{fertility}/100" if fertility is not None else "N/A"),
        ("pH", f"{ph:.1f}" if ph is not None else "N/A"),
        ("SOC", f"{soc:.1f} g/kg" if soc is not None else "N/A"),
        ("Nitrogen", f"{nitrogen:.2f} g/kg" if nitrogen is not None else "N/A"),
        ("CEC", f"{cec:.1f} cmol/kg" if cec is not None else "N/A"),
        ("Bulk Density", f"{bdod:.2f} kg/dm3" if bdod is not None else "N/A"),
        ("Drainage", drainage_label),
        ("Carbon Storage", f"{carbon_label} ({carbon_potential})"
         if carbon_potential is not None else "N/A"),
        ("Issues Found", str(len(issues))),
    ]
    col_s1, col_s2 = st.columns(2)
    for i, (label, value) in enumerate(summary_items):
        target = col_s1 if i % 2 == 0 else col_s2
        with target:
            st.markdown(
                f'<div style="display:flex; justify-content:space-between; '
                f'padding:6px 12px; margin:3px 0; '
                f'background:rgba(255,255,255,0.04); border-radius:6px;">'
                f'<span style="color:rgba(255,255,255,0.6);">{label}</span>'
                f'<span style="font-weight:600;">{value}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.caption(
        "Data sources: ISRIC SoilGrids v2.0 (250m resolution), "
        "Open-Meteo (climate), Open-Elevation (terrain). "
        "All data is indicative; confirm with local soil testing for critical decisions."
    )
