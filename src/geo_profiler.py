"""
Geo Profiler AI — Creates comprehensive geographic profiles combining
terrain, climate, vegetation, and human activity into a unified assessment.
Generates location "DNA" with radar profiles and comparison scores.
Uses: Open-Meteo, Open Topo Data, ISRIC SoilGrids, Overpass, iNaturalist, GBIF, USGS.
"""

import math
import logging

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_elevation_grid,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_landuse_infrastructure,
    fetch_earthquakes,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_risk_assessment,
    compute_species_breakdown,
)

logger = logging.getLogger(__name__)

PROFILE_DIMENSIONS = [
    {"id": "elevation", "name": "Elevation", "color": "#8b5cf6"},
    {"id": "temperature", "name": "Temperature", "color": "#ef4444"},
    {"id": "precipitation", "name": "Precipitation", "color": "#3b82f6"},
    {"id": "wind", "name": "Wind", "color": "#06b6d4"},
    {"id": "soil_fertility", "name": "Soil Fertility", "color": "#10b981"},
    {"id": "water_access", "name": "Water Access", "color": "#0ea5e9"},
    {"id": "biodiversity", "name": "Biodiversity", "color": "#22c55e"},
    {"id": "urbanization", "name": "Urbanization", "color": "#f59e0b"},
    {"id": "seismic_risk", "name": "Seismic Risk", "color": "#ef4444"},
    {"id": "terrain_complexity", "name": "Terrain Complexity", "color": "#a855f7"},
]


@st.cache_data(ttl=1800)
def build_geo_profile(lat: float, lon: float) -> dict:
    """Build comprehensive geographic profile."""
    weather = fetch_weather_data(lat, lon) or {}
    soil = fetch_soil_data(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.04, grid_size=6) or {}
    water = fetch_water_features(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    earthquakes = fetch_earthquakes(lat, lon, radius_km=100, days=365) or {}
    inat = fetch_biodiversity(lat, lon) or {}
    gbif = fetch_gbif_occurrences(lat, lon) or {}

    risk = compute_risk_assessment(earthquakes, water, weather, elev)
    species = compute_species_breakdown(inat, gbif)

    # ── Extract raw values ──
    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max = daily.get("temperature_2m_max", [])
    valid_tmax = [t for t in temp_max if t is not None]
    avg_temp = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 20

    precip = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip if p is not None]
    total_precip = sum(valid_precip) if valid_precip else 0

    wind_max = daily.get("wind_speed_10m_max", [])
    valid_wind = [w for w in wind_max if w is not None]
    avg_wind = sum(valid_wind) / len(valid_wind) if valid_wind else 10

    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    avg_elev = sum(valid_elevs) / len(valid_elevs) if valid_elevs else 100
    elev_range = (max(valid_elevs) - min(valid_elevs)) if len(valid_elevs) >= 2 else 0

    # Soil
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    soc = _sv("soc") or 10
    ph = _sv("phh2o") or 7.0
    nitrogen = _sv("nitrogen", 100) or 1.0

    # Water
    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    water_count = len(w_elements)

    # Infrastructure
    i_elements = infra.get("elements", []) if isinstance(infra, dict) else []
    buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))
    roads = sum(1 for e in i_elements if e.get("tags", {}).get("highway"))

    # Biodiversity
    total_species = species.get("gbif_unique_species", 0) + len(species.get("top_species", []))
    total_obs = species.get("inat_total", 0) + species.get("gbif_total", 0)

    # Seismic risk (flat dict)
    seismic_risk = risk.get("Seismic", 0) if isinstance(risk, dict) else 0

    # ── Normalize to 0-10 scale ──
    profile = {}
    profile["elevation"] = min(10, avg_elev / 500)  # 5000m = 10
    profile["temperature"] = min(10, avg_temp / 4.5)  # 45C = 10
    profile["precipitation"] = min(10, total_precip / 5)  # 50mm = 10
    profile["wind"] = min(10, avg_wind / 10)  # 100km/h = 10
    profile["soil_fertility"] = min(10, (soc / 5) + (8 - abs(ph - 6.5)) / 2 + nitrogen)
    profile["water_access"] = min(10, water_count / 3)
    profile["biodiversity"] = min(10, total_species / 5 + total_obs / 100)
    profile["urbanization"] = min(10, (buildings + roads) / 10)
    profile["seismic_risk"] = seismic_risk
    profile["terrain_complexity"] = min(10, elev_range / 50)

    for k in profile:
        profile[k] = round(max(0, min(10, profile[k])), 1)

    # ── Location character ──
    dominant_traits = sorted(profile.items(), key=lambda x: x[1], reverse=True)[:3]
    weak_traits = sorted(profile.items(), key=lambda x: x[1])[:3]

    # Generate character summary
    character = []
    if profile["elevation"] > 7:
        character.append("High-Altitude")
    elif profile["elevation"] < 2:
        character.append("Low-Lying")
    if profile["temperature"] > 7:
        character.append("Hot")
    elif profile["temperature"] < 3:
        character.append("Cold")
    if profile["precipitation"] > 6:
        character.append("Wet")
    elif profile["precipitation"] < 2:
        character.append("Arid")
    if profile["biodiversity"] > 6:
        character.append("Biodiverse")
    if profile["urbanization"] > 6:
        character.append("Urban")
    elif profile["urbanization"] < 2:
        character.append("Remote")
    if profile["seismic_risk"] > 5:
        character.append("Seismically Active")
    if profile["terrain_complexity"] > 6:
        character.append("Rugged")

    if not character:
        character = ["Temperate", "Moderate"]

    # ── Similarity to reference profiles ──
    reference_profiles = {
        "Mediterranean Coast": [2, 7, 3, 4, 6, 5, 5, 6, 3, 3],
        "Tropical Rainforest": [1, 8, 9, 3, 9, 8, 10, 2, 2, 3],
        "Alpine Region": [9, 3, 5, 7, 3, 5, 4, 2, 4, 9],
        "Desert": [3, 9, 1, 5, 2, 1, 2, 1, 2, 4],
        "Urban Metropolis": [1, 6, 4, 3, 3, 3, 3, 10, 2, 1],
        "Coastal Plain": [1, 6, 5, 6, 5, 7, 6, 4, 3, 1],
        "Volcanic Region": [5, 5, 5, 4, 6, 4, 5, 3, 8, 7],
    }

    profile_values = [profile[d["id"]] for d in PROFILE_DIMENSIONS]
    similarities = {}
    for ref_name, ref_values in reference_profiles.items():
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(profile_values, ref_values)))
        max_dist = math.sqrt(10 ** 2 * len(ref_values))
        similarity = round((1 - dist / max_dist) * 100, 1)
        similarities[ref_name] = similarity

    best_match = max(similarities, key=similarities.get)

    return {
        "profile": profile,
        "raw_values": {
            "elevation_m": round(avg_elev, 0),
            "temperature_c": round(avg_temp, 1),
            "precipitation_mm": round(total_precip, 1),
            "wind_kmh": round(avg_wind, 1),
            "soc_gkg": round(soc, 1),
            "ph": round(ph, 1),
            "water_features": water_count,
            "buildings": buildings,
            "species": total_species,
            "earthquakes": len(earthquakes.get("features", [])),
        },
        "character": character,
        "dominant_traits": dominant_traits,
        "weak_traits": weak_traits,
        "similarities": dict(sorted(similarities.items(), key=lambda x: x[1], reverse=True)),
        "best_match": best_match,
        "best_match_pct": similarities[best_match],
    }


# ── Rendering ───────────────────────────────────────────────────────────────

def render_geo_profiler_tab():
    """Render the Geo Profiler AI tab."""
    st.markdown("## Geo Profiler AI")
    st.caption("Comprehensive geographic profiling with reference comparison")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="gp_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="gp_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="gp_lon", format="%.4f")

    if st.button("Build Geo Profile", type="primary", use_container_width=True):
        with st.spinner("Building geographic profile across 10 dimensions..."):
            result = build_geo_profile(lat, lon)

        if not result:
            st.error("Failed to build profile.")
            return

        profile = result["profile"]
        character = result["character"]
        best_match = result["best_match"]
        best_pct = result["best_match_pct"]

        # ── Header ──
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #1a1a2e, #16213e);
                    border:1px solid #333; border-radius:12px; padding:20px; margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:#888; font-size:12px;">LOCATION CHARACTER</div>
                    <div style="color:#eee; font-size:22px; font-weight:bold; margin:4px 0;">
                        {' | '.join(character)}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="color:#888; font-size:12px;">CLOSEST MATCH</div>
                    <div style="color:#8b5cf6; font-size:20px; font-weight:bold;">{best_match}</div>
                    <div style="color:#888; font-size:13px;">{best_pct}% similarity</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 10-Dimension radar chart ──
        st.markdown("### Geographic Profile Radar")
        dim_names = [d["name"] for d in PROFILE_DIMENSIONS]
        dim_values = [profile[d["id"]] for d in PROFILE_DIMENSIONS]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=dim_values + [dim_values[0]],
            theta=dim_names + [dim_names[0]],
            fill="toself",
            fillcolor="rgba(139,92,246,0.15)",
            line=dict(color="#8b5cf6", width=2),
            name="Profile",
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
            showlegend=False,
            height=420,
            margin=dict(t=30, b=30, l=70, r=70),
        )
        st.plotly_chart(fig, use_container_width=True, key="geopro_pchart1")

        # ── Dimension bars ──
        st.markdown("### Dimension Breakdown")
        dim_colors = [d["color"] for d in PROFILE_DIMENSIONS]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=dim_values,
            y=dim_names,
            orientation="h",
            marker_color=dim_colors,
            text=[f"{v}" for v in dim_values],
            textposition="auto",
        ))
        fig2.update_layout(
            height=max(350, len(dim_names) * 35),
            margin=dict(t=10, b=20, l=150),
            xaxis=dict(range=[0, 10], title="Score (0-10)"),
        )
        st.plotly_chart(fig2, use_container_width=True, key="geopro_pchart2")

        # ── Raw values ──
        st.markdown("### Raw Measurements")
        rv = result["raw_values"]
        mc = st.columns(5)
        mc[0].metric("Elevation", f"{rv['elevation_m']:.0f}m")
        mc[1].metric("Temperature", f"{rv['temperature_c']}C")
        mc[2].metric("Precipitation", f"{rv['precipitation_mm']}mm")
        mc[3].metric("Wind", f"{rv['wind_kmh']} km/h")
        mc[4].metric("Species", rv["species"])

        mc2 = st.columns(5)
        mc2[0].metric("SOC", f"{rv['soc_gkg']} g/kg")
        mc2[1].metric("pH", rv["ph"])
        mc2[2].metric("Water Features", rv["water_features"])
        mc2[3].metric("Buildings", rv["buildings"])
        mc2[4].metric("Earthquakes", rv["earthquakes"])

        # ── Similarity comparison ──
        st.markdown("### Reference Profile Similarity")
        sims = result["similarities"]
        sim_names = list(sims.keys())
        sim_values = list(sims.values())
        sim_colors = ["#8b5cf6" if v == max(sim_values) else "#3b82f6" for v in sim_values]

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=sim_values,
            y=sim_names,
            orientation="h",
            marker_color=sim_colors,
            text=[f"{v}%" for v in sim_values],
            textposition="auto",
        ))
        fig3.update_layout(
            height=max(300, len(sim_names) * 40),
            margin=dict(t=10, b=20, l=180),
            xaxis=dict(range=[0, 100], title="Similarity %"),
        )
        st.plotly_chart(fig3, use_container_width=True, key="geopro_pchart3")

        # ── Strengths and Weaknesses ──
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### Dominant Traits")
            for trait, score in result["dominant_traits"]:
                dim = next((d for d in PROFILE_DIMENSIONS if d["id"] == trait), {})
                st.markdown(f"""
                <div style="background:#10b98122; border-left:3px solid #10b981;
                            border-radius:6px; padding:8px 12px; margin:4px 0;">
                    <span style="color:#10b981; font-weight:bold;">
                        {dim.get('name', trait)}</span>
                    <span style="color:#888; margin-left:8px;">{score}/10</span>
                </div>
                """, unsafe_allow_html=True)

        with col_b:
            st.markdown("### Weak Dimensions")
            for trait, score in result["weak_traits"]:
                dim = next((d for d in PROFILE_DIMENSIONS if d["id"] == trait), {})
                st.markdown(f"""
                <div style="background:#ef444422; border-left:3px solid #ef4444;
                            border-radius:6px; padding:8px 12px; margin:4px 0;">
                    <span style="color:#ef4444; font-weight:bold;">
                        {dim.get('name', trait)}</span>
                    <span style="color:#888; margin-left:8px;">{score}/10</span>
                </div>
                """, unsafe_allow_html=True)
