"""
Smart Insights AI for TerraScout AI.
Generates intelligent, actionable insights by cross-referencing all available
environmental data layers. Produces natural language summaries, opportunity
identification, risk alerts, and data-driven recommendations.
"""

import logging
import math
import pandas as pd
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_biodiversity,
    fetch_earthquakes,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_geology,
    compute_risk_assessment,
    compute_species_breakdown,
    compute_landuse_breakdown,
    fetch_gbif_occurrences,
    haversine_distance,
    classify_koppen,
    ANALYSIS_PRESETS,
)

logger = logging.getLogger(__name__)

try:
    from src.export_utils import render_export_buttons
    HAS_EXPORT = True
except ImportError:
    HAS_EXPORT = False


# ═══════════════════════════════════════════════════════════════
# INSIGHT CATEGORIES
# ═══════════════════════════════════════════════════════════════

INSIGHT_CATEGORIES = {
    "opportunity": {"icon": "OPPORTUNITY", "color": "#10b981", "priority": 1},
    "warning": {"icon": "WARNING", "color": "#f59e0b", "priority": 2},
    "risk": {"icon": "RISK", "color": "#ef4444", "priority": 3},
    "info": {"icon": "INFO", "color": "#06b6d4", "priority": 4},
    "recommendation": {"icon": "TIP", "color": "#8b5cf6", "priority": 5},
}


# ═══════════════════════════════════════════════════════════════
# DATA COLLECTION
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def _gather_all_data(lat, lon):
    """Fetch all available data for comprehensive insight generation."""
    result = {"lat": lat, "lon": lon}

    # Elevation
    try:
        elev = fetch_elevation_grid(lat, lon, radius_deg=0.02, grid_size=5)
        result["elevation"] = elev
        result["center_elev"] = elev.get("center_elevation", 0)
        result["min_elev"] = elev.get("min_elevation", 0)
        result["max_elev"] = elev.get("max_elevation", 0)
        result["avg_elev"] = elev.get("avg_elevation", 0)
        for k in ("center_elev", "min_elev", "max_elev", "avg_elev"):
            if not isinstance(result[k], (int, float)):
                result[k] = 0
    except Exception:
        logger.warning("Smart Insights: elevation fetch failed")
        result["elevation"] = {}
        result["center_elev"] = result["min_elev"] = result["max_elev"] = result["avg_elev"] = 0

    # Weather
    try:
        wx = fetch_weather_data(lat, lon)
        result["weather"] = wx
        current = wx.get("current", {})
        result["temp"] = current.get("temperature_2m", 0) or 0
        result["humidity"] = current.get("relative_humidity_2m", 0) or 0
        result["wind"] = current.get("wind_speed_10m", 0) or 0
        result["precip"] = current.get("precipitation", 0) or 0

        daily = wx.get("daily", {})
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        precip_sum = daily.get("precipitation_sum", [])
        valid_tmax = [t for t in temps_max if t is not None]
        valid_tmin = [t for t in temps_min if t is not None]
        if valid_tmax and valid_tmin:
            result["temp_max_7d"] = max(valid_tmax)
            result["temp_min_7d"] = min(valid_tmin)
            paired = [(mx, mn) for mx, mn in zip(temps_max, temps_min) if mx is not None and mn is not None]
            result["temp_avg_7d"] = round(sum((mx + mn) / 2 for mx, mn in paired) / max(len(paired), 1), 1)
        if precip_sum:
            result["precip_7d_total"] = round(sum(p for p in precip_sum if p), 1)
            result["rainy_days"] = sum(1 for p in precip_sum if p and p > 1)
    except Exception:
        logger.warning("Smart Insights: weather fetch failed")
        result["weather"] = {}
        result["temp"] = result["humidity"] = result["wind"] = result["precip"] = 0

    # Soil
    try:
        soil = fetch_soil_data(lat, lon)
        result["soil_raw"] = soil
        result["soil"] = {}
        props = soil.get("properties", {}).get("layers", [])
        for layer in props:
            name = layer.get("name", "")
            depths = layer.get("depths", [])
            if depths:
                val = depths[0].get("values", {}).get("mean")
                if val is not None:
                    if name in ("clay", "sand", "silt"):
                        result["soil"][name] = round(val / 10, 1)
                    elif name == "phh2o":
                        result["soil"]["ph"] = round(val / 10, 1)
                    elif name == "soc":
                        result["soil"]["organic_c"] = round(val / 10, 1)
                    elif name == "nitrogen":
                        result["soil"]["nitrogen"] = round(val / 10, 1)
    except Exception:
        logger.warning("Smart Insights: soil fetch failed")
        result["soil"] = {}

    # Biodiversity
    try:
        inat = fetch_biodiversity(lat, lon, radius_km=10)
        gbif = fetch_gbif_occurrences(lat, lon, radius_m=10000)
        breakdown = compute_species_breakdown(inat, gbif)
        result["biodiversity"] = breakdown
        result["species_total"] = breakdown.get("gbif_unique_species", 0) + len(breakdown.get("top_species", []))
        result["observations"] = breakdown.get("inat_total", 0) + breakdown.get("gbif_total", 0)
    except Exception:
        logger.warning("Smart Insights: biodiversity fetch failed")
        result["biodiversity"] = {}
        result["species_total"] = 0
        result["observations"] = 0

    # Seismic
    try:
        eq = fetch_earthquakes(lat, lon, radius_km=100, days=365)
        result["earthquakes"] = eq
        result["quake_count"] = len(eq.get("features", []))
        if eq.get("features"):
            mags = [f.get("properties", {}).get("mag", 0) for f in eq["features"]]
            result["quake_max_mag"] = max(m for m in mags if m is not None) if mags else 0
    except Exception:
        logger.warning("Smart Insights: seismic fetch failed")
        result["earthquakes"] = {}
        result["quake_count"] = 0

    # Water
    try:
        water = fetch_water_features(lat, lon, radius=5000)
        result["water"] = water
        result["water_count"] = len(water.get("elements", []))
    except Exception:
        logger.warning("Smart Insights: water fetch failed")
        result["water"] = {}
        result["water_count"] = 0

    # Land use
    try:
        landuse = fetch_landuse_infrastructure(lat, lon, radius=3000)
        result["landuse"] = landuse
        lu_breakdown = compute_landuse_breakdown(landuse)
        result["landuse_breakdown"] = lu_breakdown
    except Exception:
        logger.warning("Smart Insights: land use fetch failed")
        result["landuse"] = {}
        result["landuse_breakdown"] = {}

    # Protected areas
    try:
        pa = fetch_protected_areas(lat, lon, radius=10000)
        result["protected_areas"] = pa
        result["protected_count"] = len(pa.get("elements", [])) if isinstance(pa, dict) else 0
    except Exception:
        result["protected_areas"] = {}
        result["protected_count"] = 0

    # Geology
    try:
        geo = fetch_geology(lat, lon)
        result["geology"] = geo
    except Exception:
        result["geology"] = {}

    # Risk assessment
    try:
        elev_data = {
            "center_elevation": result["center_elev"],
            "min_elevation": result["min_elev"],
            "max_elevation": result["max_elev"],
        }
        risk = compute_risk_assessment(
            result.get("earthquakes", {}),
            result.get("water", {}),
            result.get("landuse", {}),
            elev_data, lat, lon
        )
        result["risk"] = risk
    except Exception:
        logger.warning("Smart Insights: risk assessment failed")
        result["risk"] = {}

    # Climate classification
    try:
        daily = result.get("weather", {}).get("daily", {})
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        precip_sum = daily.get("precipitation_sum", [])
        if temps_max and temps_min:
            avg_t = sum((mx + mn) / 2 for mx, mn in zip(temps_max, temps_min)) / len(temps_max)
            max_t = max(temps_max)
            min_t = min(temps_min)
            annual_p = sum(p for p in precip_sum if p) * 52 if precip_sum else 0
            driest = min(p for p in precip_sum if p is not None) if precip_sum else 0
            result["koppen"] = classify_koppen(avg_t, annual_p, max_t, min_t, driest)
        else:
            result["koppen"] = "Unknown"
    except Exception:
        result["koppen"] = "Unknown"

    return result


# ═══════════════════════════════════════════════════════════════
# INSIGHT ENGINE — generates all insights from data
# ═══════════════════════════════════════════════════════════════

def _generate_insights(data):
    """Generate all insights from collected data. Returns list of insight dicts."""
    insights = []

    temp = data.get("temp", 0)
    humidity = data.get("humidity", 0)
    wind = data.get("wind", 0)
    precip = data.get("precip", 0)
    elev = data.get("center_elev", 0)
    species = data.get("species_total", 0)
    quakes = data.get("quake_count", 0)
    water_count = data.get("water_count", 0)
    soil = data.get("soil", {})
    risk = data.get("risk", {})
    koppen = data.get("koppen", "Unknown")

    # ── Climate insights ──
    if koppen != "Unknown":
        insights.append({
            "category": "info",
            "title": f"Climate Classification: {koppen}",
            "body": f"This location falls under the {koppen} climate zone. "
                    f"Current conditions: {temp}C, {humidity}% humidity, {wind} km/h wind.",
            "confidence": 90,
            "tags": ["climate"],
        })

    if temp > 35:
        insights.append({
            "category": "warning",
            "title": "Extreme Heat Detected",
            "body": f"Current temperature is {temp}C — above comfort threshold. "
                    f"Heat stress risk for outdoor activities, crops, and livestock. "
                    f"Consider shade structures, irrigation scheduling, and heat-tolerant species.",
            "confidence": 95,
            "tags": ["climate", "health"],
        })
    elif temp < 0:
        insights.append({
            "category": "warning",
            "title": "Sub-Zero Temperature",
            "body": f"Current temperature is {temp}C — frost conditions active. "
                    f"Risk to exposed crops and infrastructure. Cold-hardy species recommended.",
            "confidence": 95,
            "tags": ["climate"],
        })

    if humidity < 20:
        insights.append({
            "category": "warning",
            "title": "Extremely Dry Conditions",
            "body": f"Humidity at {humidity}% — very dry air. Elevated fire risk, "
                    f"increased evapotranspiration, and drought stress likely.",
            "confidence": 85,
            "tags": ["climate", "fire"],
        })

    # ── Agriculture insights ──
    ph = soil.get("ph", 0)
    organic_c = soil.get("organic_c", 0)
    clay = soil.get("clay", 0)

    if ph > 0:
        if 5.5 <= ph <= 7.5:
            insights.append({
                "category": "opportunity",
                "title": "Excellent Soil pH for Agriculture",
                "body": f"Soil pH is {ph} — within the ideal range for most crops (5.5-7.5). "
                        f"Wide variety of crops can be grown without pH amendment.",
                "confidence": 85,
                "tags": ["agriculture", "soil"],
            })
        elif ph < 5.0:
            insights.append({
                "category": "recommendation",
                "title": "Acidic Soil — Lime Application Recommended",
                "body": f"Soil pH is {ph} — quite acidic. Consider lime application to raise pH. "
                        f"Suitable as-is for acid-loving crops: blueberries, potatoes, tea.",
                "confidence": 80,
                "tags": ["agriculture", "soil"],
            })
        elif ph > 8.0:
            insights.append({
                "category": "recommendation",
                "title": "Alkaline Soil — Limited Crop Range",
                "body": f"Soil pH is {ph} — alkaline. Consider sulfur amendment to lower pH. "
                        f"Currently suitable for: asparagus, beets, cabbage, date palms.",
                "confidence": 80,
                "tags": ["agriculture", "soil"],
            })

    if organic_c > 30:
        insights.append({
            "category": "opportunity",
            "title": "High Organic Carbon — Fertile Soil",
            "body": f"Soil organic carbon is {organic_c} g/kg — significantly above average. "
                    f"Indicates high soil fertility, good water retention, and healthy microbiome.",
            "confidence": 85,
            "tags": ["agriculture", "soil"],
        })
    elif organic_c > 0 and organic_c < 8:
        insights.append({
            "category": "warning",
            "title": "Low Soil Fertility",
            "body": f"Soil organic carbon is only {organic_c} g/kg — below healthy threshold. "
                    f"Recommend composting, cover cropping, or biochar amendment.",
            "confidence": 80,
            "tags": ["agriculture", "soil"],
        })

    # ── Energy insights ──
    if wind > 25:
        insights.append({
            "category": "opportunity",
            "title": "Strong Wind Energy Potential",
            "body": f"Wind speed is {wind} km/h — above the viability threshold for wind turbines. "
                    f"Consider wind resource assessment for renewable energy generation.",
            "confidence": 75,
            "tags": ["energy", "wind"],
        })

    # Solar potential (rough — based on latitude and cloud cover)
    abs_lat = abs(data.get("lat", 0))
    if abs_lat < 35 and humidity < 60:
        insights.append({
            "category": "opportunity",
            "title": "Good Solar Energy Potential",
            "body": f"Low latitude ({abs_lat:.1f}) with moderate humidity ({humidity}%) suggests "
                    f"above-average solar irradiance. Solar panel installation recommended.",
            "confidence": 70,
            "tags": ["energy", "solar"],
        })

    # ── Biodiversity insights ──
    if species > 200:
        insights.append({
            "category": "opportunity",
            "title": "Biodiversity Hotspot Detected",
            "body": f"{species} species recorded in this area — well above average. "
                    f"This area has high conservation value. Consider protected area designation.",
            "confidence": 85,
            "tags": ["biodiversity", "conservation"],
        })
    elif species > 100:
        insights.append({
            "category": "info",
            "title": "Moderate Biodiversity",
            "body": f"{species} species recorded — healthy biodiversity level. "
                    f"Habitat connectivity and corridors should be maintained.",
            "confidence": 80,
            "tags": ["biodiversity"],
        })
    elif 0 < species < 20:
        insights.append({
            "category": "warning",
            "title": "Low Biodiversity",
            "body": f"Only {species} species recorded — below expected levels. "
                    f"Could indicate habitat degradation, pollution, or data scarcity.",
            "confidence": 65,
            "tags": ["biodiversity"],
        })

    # ── Risk insights ──
    for risk_type in ("Seismic", "Flood", "Fire", "Landslide"):
        risk_data = risk.get(risk_type, 0)
        score = risk_data if isinstance(risk_data, (int, float)) else 0
        if score >= 7:
            insights.append({
                "category": "risk",
                "title": f"High {risk_type} Risk",
                "body": f"{risk_type} risk score is {score}/10 — significantly elevated. "
                        f"Mitigation measures and emergency planning strongly recommended.",
                "confidence": 90,
                "tags": ["risk", risk_type.lower()],
            })
        elif score >= 4:
            insights.append({
                "category": "warning",
                "title": f"Moderate {risk_type} Risk",
                "body": f"{risk_type} risk score is {score}/10 — moderate level. "
                        f"Standard precautions advised.",
                "confidence": 80,
                "tags": ["risk", risk_type.lower()],
            })

    # ── Water insights ──
    if water_count > 10:
        insights.append({
            "category": "opportunity",
            "title": "Water-Rich Area",
            "body": f"{water_count} water features within 5km — excellent water availability. "
                    f"Suitable for agriculture, aquaculture, and recreational development.",
            "confidence": 80,
            "tags": ["water", "agriculture"],
        })
    elif water_count == 0:
        insights.append({
            "category": "warning",
            "title": "No Water Features Detected",
            "body": "No rivers, lakes, or springs found within 5km. "
                    "Water supply may depend on groundwater or external sources.",
            "confidence": 70,
            "tags": ["water"],
        })

    # ── Terrain insights ──
    terrain_range = data.get("max_elev", 0) - data.get("min_elev", 0)
    if terrain_range > 500:
        insights.append({
            "category": "info",
            "title": "Highly Variable Terrain",
            "body": f"Elevation varies by {terrain_range}m within the analysis area. "
                    f"Steep terrain — consider erosion control, terracing for agriculture, "
                    f"and slope stability for construction.",
            "confidence": 85,
            "tags": ["terrain"],
        })

    if elev > 3000:
        insights.append({
            "category": "warning",
            "title": "High Altitude Location",
            "body": f"Elevation is {elev}m — high altitude effects: lower air pressure, "
                    f"reduced oxygen, UV exposure, shorter growing season.",
            "confidence": 90,
            "tags": ["terrain", "health"],
        })

    # ── Protected area insights ──
    if data.get("protected_count", 0) > 0:
        insights.append({
            "category": "info",
            "title": "Near Protected Area",
            "body": f"{data['protected_count']} protected areas within 10km. "
                    f"Development may be restricted. Environmental impact assessment may be required.",
            "confidence": 85,
            "tags": ["conservation", "regulation"],
        })

    # ── Geology insights ──
    geo = data.get("geology", {})
    if geo.get("success"):
        rock = geo.get("rocktype", "Unknown")
        age = geo.get("age", "Unknown")
        insights.append({
            "category": "info",
            "title": f"Geological Foundation: {rock}",
            "body": f"Bedrock type: {rock} (age: {age}). "
                    f"This affects groundwater, soil development, and construction foundation requirements.",
            "confidence": 75,
            "tags": ["geology"],
        })

    # ── Cross-domain recommendations ──
    # Agriculture recommendation
    good_soil = ph and 5.5 <= ph <= 7.5 and organic_c > 15
    good_water = water_count >= 3
    good_climate = 5 < temp < 30 and 30 < humidity < 80
    low_risk = all((risk.get(r, 0) if isinstance(risk.get(r, 0), (int, float)) else 0) < 4 for r in ("Seismic", "Flood", "Fire", "Landslide"))

    if good_soil and good_water and good_climate and low_risk:
        insights.append({
            "category": "opportunity",
            "title": "Ideal Agricultural Location",
            "body": "This location scores well across all agricultural criteria: "
                    "good soil pH and fertility, adequate water access, favorable climate, "
                    "and low natural hazard risk. Strong potential for farming operations.",
            "confidence": 80,
            "tags": ["agriculture", "recommendation"],
        })

    # Tourism recommendation
    scenic = terrain_range > 200 or elev > 1000 or species > 100
    safe = low_risk and quakes < 5
    if scenic and safe:
        insights.append({
            "category": "opportunity",
            "title": "Tourism Development Potential",
            "body": "Location combines scenic value (varied terrain, biodiversity) "
                    "with low risk profile. Suitable for eco-tourism, hiking, or nature reserves.",
            "confidence": 70,
            "tags": ["tourism", "recommendation"],
        })

    # Sort by priority then confidence
    insights.sort(key=lambda i: (
        INSIGHT_CATEGORIES[i["category"]]["priority"],
        -i["confidence"],
    ))

    return insights


# ═══════════════════════════════════════════════════════════════
# VISUALIZATION HELPERS
# ═══════════════════════════════════════════════════════════════

def _make_insight_radar(data):
    """Spider chart showing key environmental scores."""
    risk = data.get("risk", {})

    categories = [
        "Climate\nSuitability",
        "Soil\nFertility",
        "Water\nAccess",
        "Biodiversity",
        "Safety\n(inv. Risk)",
        "Terrain\nAccess",
    ]

    # Compute normalized scores (0-100)
    temp = data.get("temp", 15)
    climate_score = max(0, 100 - abs(temp - 20) * 4)

    soil = data.get("soil", {})
    ph = soil.get("ph", 7)
    oc = soil.get("organic_c", 15)
    soil_score = max(0, min(100, 50 + (7 - abs(ph - 6.5)) * 10 + min(oc, 30)))

    water_score = min(100, data.get("water_count", 0) * 15)

    bio_score = min(100, data.get("species_total", 0) / 2)

    avg_risk = sum(risk.get(r, 0) if isinstance(risk.get(r, 0), (int, float)) else 0 for r in ("Seismic", "Flood", "Fire", "Landslide")) / 4
    safety_score = max(0, 100 - avg_risk * 10)

    terrain_range = data.get("max_elev", 0) - data.get("min_elev", 0)
    terrain_score = max(0, 100 - terrain_range / 10)

    values = [climate_score, soil_score, water_score, bio_score, safety_score, terrain_score]
    values = [round(v) for v in values]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories + [categories[0]],
        fill="toself",
        name="Location Score",
        line_color="#06b6d4",
        fillcolor="rgba(6, 182, 212, 0.2)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        title="Environmental Score Profile",
        height=400,
        margin=dict(t=60, b=30),
    )
    return fig, values, categories


def _make_confidence_chart(insights):
    """Bar chart showing insight confidence levels."""
    if not insights:
        return None

    titles = [i["title"][:40] for i in insights[:12]]
    confidences = [i["confidence"] for i in insights[:12]]
    colors = [INSIGHT_CATEGORIES[i["category"]]["color"] for i in insights[:12]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=titles,
        x=confidences,
        orientation="h",
        marker_color=colors,
        text=[f"{c}%" for c in confidences],
        textposition="auto",
    ))
    fig.update_layout(
        title="Insight Confidence Levels",
        xaxis_title="Confidence %",
        height=max(300, len(titles) * 35 + 100),
        margin=dict(t=50, b=40, l=10),
        yaxis=dict(autorange="reversed"),
        xaxis=dict(range=[0, 100]),
    )
    return fig


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════

def render_smart_insights_tab():
    """Main render function for Smart Insights AI tab."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>Smart Insights AI</h4>
        <p>AI-powered cross-domain analysis — opportunities, risks, recommendations from all data layers</p>
    </div>
    """, unsafe_allow_html=True)

    # Location input
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        preset = st.selectbox("Preset Location",
                              ["Custom"] + [k for k in ANALYSIS_PRESETS.keys() if k != "Custom"],
                              key="si_preset")
        p = ANALYSIS_PRESETS.get(preset)
    with col2:
        d_lat = p["lat"] if p else 41.9028
        lat = st.number_input("Latitude", -90.0, 90.0, d_lat, step=0.01,
                              key="si_lat", format="%.4f")
    with col3:
        d_lon = p["lon"] if p else 12.4964
        lon = st.number_input("Longitude", -180.0, 180.0,
                              p["lon"] if p else d_lon, step=0.01,
                              key="si_lon", format="%.4f")

    # Analysis options
    with st.expander("Analysis Options", expanded=False):
        tag_filter = st.multiselect(
            "Focus Areas (leave empty for all)",
            ["climate", "agriculture", "soil", "energy", "biodiversity",
             "conservation", "risk", "water", "terrain", "geology", "health", "tourism"],
            key="si_tags",
        )

    if st.button("Generate Insights", type="primary", use_container_width=True):
        with st.spinner("Gathering environmental data (9 data sources)..."):
            all_data = _gather_all_data(lat, lon)

        with st.spinner("Generating AI insights..."):
            insights = _generate_insights(all_data)
            if tag_filter:
                insights = [i for i in insights if any(t in i["tags"] for t in tag_filter)]

        st.session_state["si_results"] = {
            "data": all_data,
            "insights": insights,
        }

    # Display results
    if "si_results" not in st.session_state:
        return

    results = st.session_state["si_results"]
    all_data = results["data"]
    insights = results["insights"]

    st.markdown("---")

    # Summary metrics
    st.markdown("### Analysis Summary")
    cat_counts = {}
    for i in insights:
        cat = i["category"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    m_cols = st.columns(5)
    for idx, (cat_name, cat_info) in enumerate(INSIGHT_CATEGORIES.items()):
        with m_cols[idx]:
            count = cat_counts.get(cat_name, 0)
            st.markdown(f"""
            <div style="text-align:center; padding: 8px; background: rgba(0,0,0,0.2);
                        border-radius: 8px; border-top: 3px solid {cat_info['color']};">
                <div style="font-size: 1.8em; font-weight: bold; color: {cat_info['color']};">{count}</div>
                <div style="color: #9ca3af; font-size: 0.85em;">{cat_info['icon']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Charts
    st.markdown("---")
    ch1, ch2 = st.columns(2)
    with ch1:
        radar_fig, scores, score_labels = _make_insight_radar(all_data)
        st.plotly_chart(radar_fig, use_container_width=True, key="smains_pchart1")
    with ch2:
        conf_fig = _make_confidence_chart(insights)
        if conf_fig:
            st.plotly_chart(conf_fig, use_container_width=True, key="smains_pchart2")
        else:
            st.info("No insights generated for this location.")

    # Score breakdown
    st.markdown("### Score Breakdown")
    score_cols = st.columns(len(scores))
    score_colors = ["#06b6d4", "#10b981", "#3b82f6", "#8b5cf6", "#f59e0b", "#f97316"]
    for i, (label, score) in enumerate(zip(score_labels, scores)):
        with score_cols[i]:
            color = score_colors[i % len(score_colors)]
            st.markdown(f"""
            <div style="text-align:center;">
                <div style="font-size: 1.5em; font-weight: bold; color: {color};">{score}</div>
                <div style="color: #9ca3af; font-size: 0.75em;">{label.replace(chr(10), ' ')}</div>
            </div>
            """, unsafe_allow_html=True)
            st.progress(score / 100)

    # Insight cards
    st.markdown("---")
    st.markdown("### Insights")

    if not insights:
        st.info("No significant insights detected for this location at current settings.")
    else:
        for i, insight in enumerate(insights):
            cat_info = INSIGHT_CATEGORIES[insight["category"]]
            tags_html = " ".join(
                f'<span style="background:rgba(255,255,255,0.1); padding:2px 8px; '
                f'border-radius:10px; font-size:0.75em; margin-right:4px;">{t}</span>'
                for t in insight["tags"]
            )
            st.markdown(f"""
            <div style="padding: 15px; background: rgba(0,0,0,0.15); border-radius: 10px;
                        border-left: 4px solid {cat_info['color']}; margin-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: {cat_info['color']}; font-weight: bold; font-size: 0.8em;">
                            [{cat_info['icon']}]
                        </span>
                        <strong style="margin-left: 8px;">{insight['title']}</strong>
                    </div>
                    <span style="color: #9ca3af; font-size: 0.8em;">
                        Confidence: {insight['confidence']}%
                    </span>
                </div>
                <p style="color: #d1d5db; margin: 8px 0 6px 0; font-size: 0.95em;">
                    {insight['body']}
                </p>
                <div>{tags_html}</div>
            </div>
            """, unsafe_allow_html=True)

    # Key data summary
    with st.expander("Raw Data Summary"):
        summary_data = {
            "Parameter": [],
            "Value": [],
        }
        display_keys = [
            ("Latitude", all_data.get("lat")),
            ("Longitude", all_data.get("lon")),
            ("Elevation", f"{all_data.get('center_elev', 0)} m"),
            ("Temperature", f"{all_data.get('temp', 0)} C"),
            ("Humidity", f"{all_data.get('humidity', 0)}%"),
            ("Wind", f"{all_data.get('wind', 0)} km/h"),
            ("Precipitation", f"{all_data.get('precip', 0)} mm"),
            ("Climate Zone", all_data.get("koppen", "Unknown")),
            ("Soil pH", all_data.get("soil", {}).get("ph", "N/A")),
            ("Soil Organic C", f"{all_data.get('soil', {}).get('organic_c', 'N/A')} g/kg"),
            ("Species Count", all_data.get("species_total", 0)),
            ("Observations", all_data.get("observations", 0)),
            ("Earthquake Count (1yr)", all_data.get("quake_count", 0)),
            ("Water Features", all_data.get("water_count", 0)),
            ("Protected Areas", all_data.get("protected_count", 0)),
        ]
        for name, val in display_keys:
            summary_data["Parameter"].append(name)
            summary_data["Value"].append(str(val))

        st.dataframe(pd.DataFrame(summary_data), use_container_width=True, hide_index=True)

    # Export
    st.markdown("---")
    st.markdown("### Export Insights")
    if insights:
        export_rows = []
        for insight in insights:
            export_rows.append({
                "Category": insight["category"].upper(),
                "Title": insight["title"],
                "Description": insight["body"],
                "Confidence": insight["confidence"],
                "Tags": ", ".join(insight["tags"]),
                "Latitude": all_data["lat"],
                "Longitude": all_data["lon"],
            })
        df_export = pd.DataFrame(export_rows)
        if HAS_EXPORT:
            render_export_buttons(df_export, prefix="insights", lat_col="Latitude", lon_col="Longitude")
        else:
            csv = df_export.to_csv(index=False)
            st.download_button("Download Insights (CSV)", data=csv,
                               file_name="smart_insights.csv", mime="text/csv")
    else:
        st.info("No insights to export.")
