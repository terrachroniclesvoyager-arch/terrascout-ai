"""
AI Scoring Engine for TerraScout AI.
Multi-dimensional intelligent scoring system that evaluates any location on 5 axes:
  - Habitability (0-100): How suitable for human living
  - Agriculture (0-100): Farming & crop potential
  - Tourism (0-100): Tourism & scenic value
  - Ecology (0-100): Biodiversity & conservation value
  - Construction (0-100): Building suitability

Uses weighted multi-factor analysis combining elevation, climate, soil, biodiversity,
water, geology, seismic, and land use data from 9+ free APIs.
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
    fetch_geology,
    fetch_protected_areas,
    compute_risk_assessment,
    compute_species_breakdown,
    compute_landuse_breakdown,
    fetch_gbif_occurrences,
    haversine_distance,
    classify_koppen,
    ANALYSIS_PRESETS,
)

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# SCORING ALGORITHMS
# ═══════════════════════════════════════════════════════════════

def _clamp(val, lo=0, hi=100):
    return max(lo, min(hi, val))


def _parse_water(water):
    """Parse water features from Overpass elements into typed counts."""
    elements = water.get("elements", []) if isinstance(water, dict) else []
    springs = sum(1 for e in elements if e.get("tags", {}).get("natural") == "spring")
    wells = sum(1 for e in elements if e.get("tags", {}).get("man_made") == "water_well")
    waterways = sum(1 for e in elements if e.get("tags", {}).get("waterway"))
    water_bodies = sum(1 for e in elements if e.get("tags", {}).get("natural") == "water")
    return springs, wells, waterways, water_bodies


def _score_habitability(weather, elevation, water, landuse, risk, soil):
    """Score location for human habitability (0-100)."""
    score = 50  # Baseline

    # Temperature comfort (ideal: 15-25C)
    try:
        current = weather.get("current", {})
        temp = current.get("temperature_2m")
        if temp is not None:
            if 15 <= temp <= 25:
                score += 15
            elif 10 <= temp <= 30:
                score += 8
            elif 5 <= temp <= 35:
                score += 3
            else:
                score -= 10
        humidity = current.get("relative_humidity_2m")
        if humidity is not None:
            if 30 <= humidity <= 60:
                score += 5
            elif humidity > 85:
                score -= 5
    except Exception:
        pass

    # Water access
    try:
        springs, wells, waterways, _ = _parse_water(water)
        water_score = min(15, (springs * 3 + wells * 2 + waterways * 1))
        score += water_score
    except Exception:
        pass

    # Infrastructure
    try:
        lu = compute_landuse_breakdown(landuse) if landuse else {}
        buildings = lu.get("building_count", 0)
        roads = lu.get("road_segments", 0)
        if buildings > 50:
            score += 10
        elif buildings > 10:
            score += 5
        if roads > 5:
            score += 5
    except Exception:
        pass

    # Elevation (ideal: 100-1000m, penalize extremes)
    try:
        elev = elevation.get("center_elevation", 500)
        if isinstance(elev, (int, float)):
            if 100 <= elev <= 1000:
                score += 5
            elif elev > 3000:
                score -= 10
            elif elev < 5:
                score -= 5  # Flood risk
    except Exception:
        pass

    # Risk penalty
    try:
        for risk_name, risk_val in risk.items():
            rv = risk_val if isinstance(risk_val, (int, float)) else 0
            if rv > 7:
                score -= 8
            elif rv > 5:
                score -= 4
            elif rv > 3:
                score -= 2
    except Exception:
        pass

    # Soil pH (ideal 6-7.5 for general use)
    try:
        layers = soil.get("properties", {}).get("layers", [])
        for layer in layers:
            if layer.get("name") == "phh2o":
                depths = layer.get("depths", [])
                if depths:
                    ph = (depths[0].get("values", {}).get("mean", 65) or 65) / 10
                    if 6.0 <= ph <= 7.5:
                        score += 5
                    elif ph < 4.5 or ph > 8.5:
                        score -= 5
    except Exception:
        pass

    return _clamp(round(score))


def _score_agriculture(weather, elevation, soil, water, climate_class):
    """Score location for agricultural potential (0-100)."""
    score = 40

    # Soil quality
    try:
        layers = soil.get("properties", {}).get("layers", [])
        soil_vals = {}
        for layer in layers:
            name = layer.get("name", "")
            depths = layer.get("depths", [])
            if depths:
                val = depths[0].get("values", {}).get("mean")
                if val is not None:
                    soil_vals[name] = val

        # Organic carbon (higher = better)
        soc = soil_vals.get("soc", 0) / 10 if "soc" in soil_vals else 0
        if soc > 30:
            score += 15
        elif soc > 15:
            score += 10
        elif soc > 5:
            score += 5

        # pH (ideal 5.5-7.5)
        ph = soil_vals.get("phh2o", 65) / 10 if "phh2o" in soil_vals else 6.5
        if 5.5 <= ph <= 7.5:
            score += 10
        elif 4.5 <= ph <= 8.5:
            score += 3
        else:
            score -= 5

        # Nitrogen
        n = soil_vals.get("nitrogen", 0) / 100 if "nitrogen" in soil_vals else 0
        if n > 3:
            score += 8
        elif n > 1:
            score += 4

        # Clay-sand balance (loam ideal)
        clay = soil_vals.get("clay", 250) / 10 if "clay" in soil_vals else 25
        sand = soil_vals.get("sand", 400) / 10 if "sand" in soil_vals else 40
        if 20 <= clay <= 35 and 30 <= sand <= 50:
            score += 8  # Loamy soil
        elif clay > 60:
            score -= 5  # Too heavy
        elif sand > 80:
            score -= 5  # Too sandy
    except Exception:
        pass

    # Temperature & precipitation
    try:
        daily = weather.get("daily", {})
        temps = daily.get("temperature_2m_max", [])
        precip = daily.get("precipitation_sum", [])
        if temps:
            avg_temp = sum(t for t in temps if t is not None) / len([t for t in temps if t is not None])
            if 15 <= avg_temp <= 30:
                score += 8
            elif 5 <= avg_temp <= 35:
                score += 3
            else:
                score -= 5
        if precip:
            total_precip = sum(p for p in precip if p is not None)
            weekly_rate = total_precip  # 7-day total
            annual_est = weekly_rate * 52
            if 500 <= annual_est <= 1500:
                score += 8
            elif 300 <= annual_est <= 2000:
                score += 4
            elif annual_est < 200:
                score -= 8  # Arid
    except Exception:
        pass

    # Water availability
    try:
        springs, wells, waterways, _ = _parse_water(water)
        if waterways > 3 or springs > 2:
            score += 8
        elif waterways > 0 or springs > 0:
            score += 4
    except Exception:
        pass

    # Terrain (flat = better)
    try:
        elev_range = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
        if isinstance(elev_range, (int, float)):
            if elev_range < 50:
                score += 5
            elif elev_range > 500:
                score -= 8
    except Exception:
        pass

    return _clamp(round(score))


def _score_tourism(weather, elevation, biodiversity, geology, protected, water):
    """Score location for tourism & scenic value (0-100)."""
    score = 30

    # Biodiversity (more species = more interesting)
    try:
        total = biodiversity.get("gbif_unique_species", 0) + len(biodiversity.get("top_species", []))
        if total > 200:
            score += 20
        elif total > 100:
            score += 15
        elif total > 50:
            score += 10
        elif total > 10:
            score += 5
    except Exception:
        pass

    # Dramatic terrain
    try:
        elev_range = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
        center_elev = elevation.get("center_elevation", 0)
        if isinstance(elev_range, (int, float)):
            if elev_range > 1000:
                score += 15
            elif elev_range > 500:
                score += 10
            elif elev_range > 200:
                score += 5
        if isinstance(center_elev, (int, float)):
            if center_elev > 2000:
                score += 5  # Mountain tourism
    except Exception:
        pass

    # Weather (pleasant = better)
    try:
        current = weather.get("current", {})
        temp = current.get("temperature_2m")
        if temp is not None:
            if 18 <= temp <= 28:
                score += 10
            elif 10 <= temp <= 32:
                score += 5
    except Exception:
        pass

    # Geology (interesting formations)
    try:
        if geology:
            records = geology.get("success", {}).get("data", [])
            if records:
                score += min(10, len(records) * 2)
    except Exception:
        pass

    # Protected areas (national parks etc.)
    try:
        if protected:
            areas = protected.get("elements", [])
            if len(areas) > 5:
                score += 15
            elif len(areas) > 0:
                score += 10
    except Exception:
        pass

    # Water features (scenic)
    try:
        springs, _, waterways, water_bodies = _parse_water(water)
        if water_bodies > 3:
            score += 8
        elif water_bodies > 0 or waterways > 5:
            score += 5
    except Exception:
        pass

    return _clamp(round(score))


def _score_ecology(biodiversity, protected, water, landuse, elevation):
    """Score ecological & conservation value (0-100)."""
    score = 25

    # Species richness
    try:
        total = biodiversity.get("gbif_unique_species", 0) + len(biodiversity.get("top_species", []))
        obs = biodiversity.get("inat_total", 0) + biodiversity.get("gbif_total", 0)
        if total > 500:
            score += 25
        elif total > 200:
            score += 20
        elif total > 100:
            score += 15
        elif total > 50:
            score += 10
        elif total > 10:
            score += 5

        # Observation density (well-studied area)
        if obs > 1000:
            score += 5
    except Exception:
        pass

    # Protected areas
    try:
        if protected:
            areas = protected.get("elements", [])
            if len(areas) > 10:
                score += 20
            elif len(areas) > 3:
                score += 15
            elif len(areas) > 0:
                score += 10
    except Exception:
        pass

    # Water features (ecological corridors)
    try:
        _, _, waterways, water_bodies = _parse_water(water)
        if waterways + water_bodies > 10:
            score += 10
        elif waterways + water_bodies > 3:
            score += 5
    except Exception:
        pass

    # Low urbanization = higher ecology
    try:
        lu = compute_landuse_breakdown(landuse) if landuse else {}
        buildings = lu.get("building_count", 0)
        if buildings == 0:
            score += 10
        elif buildings < 10:
            score += 5
        elif buildings > 100:
            score -= 10
    except Exception:
        pass

    # Elevation diversity (habitat variety)
    try:
        elev_range = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
        if isinstance(elev_range, (int, float)):
            if elev_range > 500:
                score += 5
    except Exception:
        pass

    return _clamp(round(score))


def _score_construction(elevation, soil, weather, risk, water, landuse):
    """Score location for construction/building suitability (0-100)."""
    score = 50

    # Flat terrain
    try:
        elev_range = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
        if isinstance(elev_range, (int, float)):
            if elev_range < 20:
                score += 15
            elif elev_range < 50:
                score += 10
            elif elev_range < 100:
                score += 5
            elif elev_range > 500:
                score -= 15
    except Exception:
        pass

    # Soil stability (low clay = better for foundations)
    try:
        layers = soil.get("properties", {}).get("layers", [])
        for layer in layers:
            if layer.get("name") == "clay":
                depths = layer.get("depths", [])
                if depths:
                    clay = (depths[0].get("values", {}).get("mean", 250) or 250) / 10
                    if clay < 20:
                        score += 10
                    elif clay < 35:
                        score += 5
                    elif clay > 50:
                        score -= 10  # Expansive clay
    except Exception:
        pass

    # Low risk
    try:
        for risk_name, risk_info in risk.items():
            risk_val = risk_info if isinstance(risk_info, (int, float)) else 0
            if risk_val > 7:
                score -= 12
            elif risk_val > 5:
                score -= 6
            elif risk_val > 3:
                score -= 3
    except Exception:
        pass

    # Existing infrastructure (road access)
    try:
        lu = compute_landuse_breakdown(landuse) if landuse else {}
        roads = lu.get("road_segments", 0)
        if roads > 10:
            score += 10
        elif roads > 3:
            score += 5
        elif roads == 0:
            score -= 10  # No access
    except Exception:
        pass

    # Not in flood zone
    try:
        center_elev = elevation.get("center_elevation", 100)
        if isinstance(center_elev, (int, float)):
            if center_elev < 5:
                score -= 15
            elif center_elev < 20:
                score -= 5
    except Exception:
        pass

    # Weather (avoid extremes)
    try:
        daily = weather.get("daily", {})
        winds = daily.get("wind_speed_10m_max", [])
        if winds:
            max_wind = max(w for w in winds if w is not None) if any(w is not None for w in winds) else 0
            if max_wind > 80:
                score -= 10
            elif max_wind > 50:
                score -= 5
    except Exception:
        pass

    return _clamp(round(score))


# ═══════════════════════════════════════════════════════════════
# AI INSIGHT GENERATOR
# ═══════════════════════════════════════════════════════════════

def _generate_insights(scores, raw_data):
    """Generate AI insights based on scores and raw data."""
    insights = []

    # Overall assessment
    avg = sum(scores.values()) / len(scores)
    if avg > 75:
        insights.append(("star", "Exceptional Location", "This location scores above average across all dimensions. It's a rare combination of favorable conditions.", "#10b981"))
    elif avg > 50:
        insights.append(("check", "Good Location", "Solid overall profile with strengths in specific areas.", "#06b6d4"))
    elif avg > 30:
        insights.append(("info", "Mixed Profile", "This location has significant trade-offs. Check individual scores for details.", "#f59e0b"))
    else:
        insights.append(("warning", "Challenging Location", "Multiple limiting factors detected. Careful evaluation recommended.", "#ef4444"))

    # Specific insights
    if scores.get("habitability", 0) > 70:
        insights.append(("home", "Highly Livable", "Climate, water access, and infrastructure make this area comfortable for living.", "#10b981"))
    elif scores.get("habitability", 0) < 30:
        insights.append(("warning", "Low Habitability", "Extreme conditions, lack of infrastructure, or high risk factors limit livability.", "#ef4444"))

    if scores.get("agriculture", 0) > 70:
        insights.append(("seedling", "Excellent Farmland", "Soil composition, rainfall, and temperature are ideal for agriculture.", "#10b981"))
    elif scores.get("agriculture", 0) < 30:
        insights.append(("alert", "Poor Agriculture", "Soil quality, water scarcity, or extreme terrain limit farming potential.", "#ef4444"))

    if scores.get("tourism", 0) > 70:
        insights.append(("camera", "Tourism Hotspot", "Rich biodiversity, dramatic landscapes, and pleasant weather attract visitors.", "#8b5cf6"))

    if scores.get("ecology", 0) > 70:
        insights.append(("leaf", "Ecological Treasure", "High biodiversity and protected area density make this ecologically valuable.", "#10b981"))

    if scores.get("construction", 0) < 30:
        insights.append(("alert", "Construction Warning", "Unstable soil, steep terrain, or high natural hazard risk. Engineering challenges expected.", "#ef4444"))

    # Cross-dimension insights
    if scores.get("ecology", 0) > 70 and scores.get("construction", 0) > 60:
        insights.append(("balance", "Conflict Zone", "High ecological value AND construction suitability. Development would require careful environmental assessment.", "#f59e0b"))

    if scores.get("agriculture", 0) > 60 and scores.get("habitability", 0) > 60:
        insights.append(("star", "Settlement Potential", "Good for both living and farming. Historically, these conditions lead to thriving communities.", "#06b6d4"))

    return insights


def _score_color(score):
    if score >= 75:
        return "#10b981"
    elif score >= 50:
        return "#06b6d4"
    elif score >= 30:
        return "#f59e0b"
    else:
        return "#ef4444"


def _score_label(score):
    if score >= 90:
        return "EXCEPTIONAL"
    elif score >= 75:
        return "EXCELLENT"
    elif score >= 60:
        return "GOOD"
    elif score >= 45:
        return "MODERATE"
    elif score >= 30:
        return "FAIR"
    elif score >= 15:
        return "POOR"
    else:
        return "CRITICAL"


# ═══════════════════════════════════════════════════════════════
# MAIN RENDER
# ═══════════════════════════════════════════════════════════════

def render_ai_scoring_tab():
    """Main render function for AI Scoring Engine tab."""
    st.markdown("""
    <div class="tab-header cyan">
        <h4>🧠 AI Location Intelligence</h4>
        <p>Multi-dimensional AI scoring engine — evaluates any location across 5 axes using 9+ data sources</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location Preset", list(ANALYSIS_PRESETS.keys()), key="ais_preset")
    preset_data = ANALYSIS_PRESETS.get(preset)
    d_lat = preset_data["lat"] if preset_data else 41.90
    d_lon = preset_data["lon"] if preset_data else 12.50
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Latitude", -90.0, 90.0, d_lat, step=0.01, key="ais_lat", format="%.4f")
        with c2:
            lon = st.number_input("Longitude", -180.0, 180.0, d_lon, step=0.01, key="ais_lon", format="%.4f")

    if st.button("🧠 Run AI Analysis", type="primary", use_container_width=True):
        progress = st.progress(0, text="Initializing AI analysis...")

        # Fetch ALL data sources
        progress.progress(5, text="Fetching elevation data...")
        try:
            elevation = fetch_elevation_grid(lat, lon, radius_deg=0.03, grid_size=7)
        except Exception as e:
            logger.warning(f"Elevation error: {e}")
            elevation = {}

        progress.progress(15, text="Fetching weather data...")
        try:
            weather = fetch_weather_data(lat, lon)
        except Exception as e:
            logger.warning(f"Weather error: {e}")
            weather = {}

        progress.progress(25, text="Fetching soil data...")
        try:
            soil = fetch_soil_data(lat, lon)
        except Exception as e:
            logger.warning(f"Soil error: {e}")
            soil = {}

        progress.progress(35, text="Fetching biodiversity...")
        try:
            inat = fetch_biodiversity(lat, lon, radius_km=10)
            gbif = fetch_gbif_occurrences(lat, lon, radius_m=10000)
            bio_breakdown = compute_species_breakdown(inat, gbif)
        except Exception as e:
            logger.warning(f"Biodiversity error: {e}")
            bio_breakdown = {}

        progress.progress(45, text="Fetching water features...")
        try:
            water = fetch_water_features(lat, lon, radius=5000)
        except Exception as e:
            logger.warning(f"Water error: {e}")
            water = {}

        progress.progress(55, text="Fetching land use...")
        try:
            landuse = fetch_landuse_infrastructure(lat, lon, radius=3000)
        except Exception as e:
            logger.warning(f"Landuse error: {e}")
            landuse = {}

        progress.progress(65, text="Fetching geology...")
        try:
            geology = fetch_geology(lat, lon)
        except Exception as e:
            logger.warning(f"Geology error: {e}")
            geology = {}

        progress.progress(70, text="Fetching seismic data...")
        try:
            earthquakes = fetch_earthquakes(lat, lon, radius_km=100, days=365)
        except Exception as e:
            logger.warning(f"Earthquake error: {e}")
            earthquakes = {}

        progress.progress(75, text="Fetching protected areas...")
        try:
            protected = fetch_protected_areas(lat, lon, radius=10000)
        except Exception as e:
            logger.warning(f"Protected areas error: {e}")
            protected = {}

        progress.progress(80, text="Computing risk assessment...")
        try:
            risk = compute_risk_assessment(earthquakes, water, landuse, elevation, lat, lon)
        except Exception as e:
            logger.warning(f"Risk error: {e}")
            risk = {}

        progress.progress(85, text="Running AI scoring algorithms...")

        # Compute climate classification
        climate_class = ""
        try:
            current = weather.get("current", {})
            daily = weather.get("daily", {})
            temp = current.get("temperature_2m", 15)
            temps_max = daily.get("temperature_2m_max", [15])
            temps_min = daily.get("temperature_2m_min", [10])
            precip_days = daily.get("precipitation_sum", [0])
            if temps_max and temps_min:
                climate_class = classify_koppen(
                    temp or 15,
                    sum(p for p in precip_days if p is not None) * 52,
                    max(t for t in temps_max if t is not None) if any(t is not None for t in temps_max) else 25,
                    min(t for t in temps_min if t is not None) if any(t is not None for t in temps_min) else 5,
                    min(p for p in precip_days if p is not None) if any(p is not None for p in precip_days) else 0,
                )
        except Exception:
            pass

        # Calculate scores
        scores = {
            "habitability": _score_habitability(weather, elevation, water, landuse, risk, soil),
            "agriculture": _score_agriculture(weather, elevation, soil, water, climate_class),
            "tourism": _score_tourism(weather, elevation, bio_breakdown, geology, protected, water),
            "ecology": _score_ecology(bio_breakdown, protected, water, landuse, elevation),
            "construction": _score_construction(elevation, soil, weather, risk, water, landuse),
        }

        # Generate insights
        insights = _generate_insights(scores, {
            "weather": weather, "elevation": elevation, "soil": soil,
            "biodiversity": bio_breakdown, "water": water, "risk": risk,
        })

        progress.progress(100, text="AI analysis complete!")

        st.session_state["ais_results"] = {
            "scores": scores, "insights": insights, "lat": lat, "lon": lon,
            "risk": risk, "climate_class": climate_class,
        }

    # Display results
    if "ais_results" not in st.session_state:
        return

    r = st.session_state["ais_results"]
    scores = r["scores"]
    insights = r["insights"]
    lat_r, lon_r = r["lat"], r["lon"]

    st.markdown("---")

    # Overall score (weighted average)
    overall = round(
        scores["habitability"] * 0.25 +
        scores["agriculture"] * 0.15 +
        scores["tourism"] * 0.15 +
        scores["ecology"] * 0.20 +
        scores["construction"] * 0.25
    )
    overall_color = _score_color(overall)

    st.markdown(f"""
    <div style="text-align:center; padding:1.5rem; background:linear-gradient(135deg, #1e293b, #0f172a);
                border-radius:16px; border:2px solid {overall_color}; margin-bottom:1.5rem;">
        <div style="font-size:3.5rem; font-weight:900; color:{overall_color};">{overall}</div>
        <div style="font-size:1.3rem; color:{overall_color}; font-weight:600;">{_score_label(overall)}</div>
        <div style="color:#94a3b8; margin-top:0.5rem;">Overall Location Intelligence Score</div>
        <div style="color:#64748b; font-size:0.85rem;">({lat_r:.4f}, {lon_r:.4f}) | Climate: {r.get('climate_class', 'N/A')}</div>
    </div>
    """, unsafe_allow_html=True)

    # 5 score cards
    score_meta = {
        "habitability": {"icon": "🏠", "label": "Habitability", "desc": "Living comfort"},
        "agriculture": {"icon": "🌾", "label": "Agriculture", "desc": "Farming potential"},
        "tourism": {"icon": "📸", "label": "Tourism", "desc": "Scenic & visitor value"},
        "ecology": {"icon": "🌿", "label": "Ecology", "desc": "Biodiversity value"},
        "construction": {"icon": "🏗️", "label": "Construction", "desc": "Building suitability"},
    }

    cols = st.columns(5)
    for i, (key, meta) in enumerate(score_meta.items()):
        with cols[i]:
            s = scores[key]
            c = _score_color(s)
            st.markdown(f"""
            <div style="background:#1e293b; border-radius:12px; padding:1rem; text-align:center;
                        border-top:3px solid {c}; height:180px;">
                <div style="font-size:1.8rem;">{meta['icon']}</div>
                <div style="font-size:2rem; font-weight:800; color:{c};">{s}</div>
                <div style="font-weight:600; color:#e2e8f0; font-size:0.9rem;">{meta['label']}</div>
                <div style="color:#64748b; font-size:0.75rem;">{_score_label(s)}</div>
            </div>
            """, unsafe_allow_html=True)

    # Radar chart
    st.markdown("### Score Profile")
    categories = list(score_meta.keys())
    labels = [score_meta[k]["label"] for k in categories]
    values = [scores[k] for k in categories]
    values_closed = values + [values[0]]
    labels_closed = labels + [labels[0]]

    fig = go.Figure(data=go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        line_color="#06b6d4",
        fillcolor="rgba(6, 182, 212, 0.15)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=400,
        margin=dict(t=30, b=30, l=60, r=60),
    )
    st.plotly_chart(fig, use_container_width=True, key="aisco_pchart1")

    # AI Insights
    st.markdown("### AI Insights")
    for icon, title, desc, color in insights:
        st.markdown(f"""
        <div style="background:#1e293b; border-left:4px solid {color}; padding:1rem; margin:0.5rem 0;
                    border-radius:0 8px 8px 0;">
            <div style="color:{color}; font-weight:700; font-size:1rem;">{title}</div>
            <div style="color:#94a3b8; font-size:0.9rem; margin-top:0.3rem;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    # Risk summary from computed data
    risk = r.get("risk", {})
    if risk:
        st.markdown("### Risk Factors")
        risk_cols = st.columns(len(risk))
        risk_colors = {"Seismic": "#ef4444", "Flood": "#3b82f6", "Fire": "#f97316",
                       "Landslide": "#a855f7", "Pollution": "#64748b"}
        for i, (rname, rinfo) in enumerate(risk.items()):
            with risk_cols[i]:
                rs = rinfo if isinstance(rinfo, (int, float)) else 0
                rc = risk_colors.get(rname, "#64748b")
                st.markdown(f"""
                <div style="text-align:center; padding:0.8rem; background:#1e293b; border-radius:8px;">
                    <div style="color:{rc}; font-size:1.5rem; font-weight:800;">{rs}/10</div>
                    <div style="color:#94a3b8; font-size:0.8rem;">{rname}</div>
                </div>
                """, unsafe_allow_html=True)

    # Export
    st.markdown("---")
    export_data = {"Dimension": [], "Score": [], "Label": []}
    for key, meta in score_meta.items():
        export_data["Dimension"].append(meta["label"])
        export_data["Score"].append(scores[key])
        export_data["Label"].append(_score_label(scores[key]))
    df = pd.DataFrame(export_data)
    csv = df.to_csv(index=False)
    st.download_button("📥 Download AI Scores (CSV)", data=csv,
                       file_name=f"ai_scores_{lat_r:.2f}_{lon_r:.2f}.csv", mime="text/csv")
