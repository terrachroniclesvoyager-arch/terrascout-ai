"""
Disaster Resilience AI -- Evaluates how resilient a location is to various
natural disasters using multi-source geospatial data analysis.
Scores resilience across 6 disaster types: Earthquake, Flood, Wildfire,
Landslide, Storm, Drought.  Higher score = more resilient.
Uses: SoilGrids, Open-Meteo, Open Topo Data, Overpass, USGS Earthquakes.
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
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_earthquakes,
)


def _hex_rgba(hc, a=1.0):
    """Convert #RRGGBB + alpha float to rgba() for Plotly compatibility."""
    h = hc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

logger = logging.getLogger(__name__)

# ── Disaster type metadata ────────────────────────────────────────────────

DISASTER_TYPES = {
    "earthquake": {"name": "Earthquake Resilience", "color": "#ef4444", "weight": 0.20},
    "flood":      {"name": "Flood Resilience",      "color": "#3b82f6", "weight": 0.20},
    "wildfire":   {"name": "Wildfire Resilience",    "color": "#f97316", "weight": 0.15},
    "landslide":  {"name": "Landslide Resilience",   "color": "#a855f7", "weight": 0.15},
    "storm":      {"name": "Storm Resilience",       "color": "#06b6d4", "weight": 0.15},
    "drought":    {"name": "Drought Resilience",     "color": "#f59e0b", "weight": 0.15},
}


# ═══════════════════════════════════════════════════════════════════════════
# COMPUTATION
# ═══════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_disaster_resilience(lat: float, lon: float) -> dict:
    """Compute disaster resilience scores across 6 disaster types."""
    soil = fetch_soil_data(lat, lon) or {}
    weather = fetch_weather_data(lat, lon) or {}
    water = fetch_water_features(lat, lon) or {}
    elev = fetch_elevation_grid(lat, lon, radius_deg=0.04, grid_size=7) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    protected = fetch_protected_areas(lat, lon) or {}
    quakes = fetch_earthquakes(lat, lon, radius_km=150, days=365)

    # ── Extract elevation data ──
    elevations = elev.get("grid_elevations", []) if isinstance(elev, dict) else []
    valid_elevs = [e for e in elevations if e is not None]
    center_elev = elev.get("center_elevation", 200) if isinstance(elev, dict) else 200
    elev_range = (max(valid_elevs) - min(valid_elevs)) if len(valid_elevs) >= 2 else 0
    avg_slope = elev_range / max(1, len(valid_elevs))

    # ── Extract soil data ──
    props = soil.get("properties", {}) if isinstance(soil, dict) else {}

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    clay = _sv("clay") or 20
    sand = _sv("sand") or 40
    silt = _sv("silt") or 30
    soc = _sv("soc") or 10
    ph = _sv("phh2o") or 7.0

    # ── Extract weather data ──
    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max_list = daily.get("temperature_2m_max", [])
    valid_tmax = [t for t in temp_max_list if t is not None]
    avg_temp = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 20

    humidity = current.get("relative_humidity_2m", 50) or 50
    wind_speed = current.get("wind_speed_10m", 15) or 15

    precip_list = daily.get("precipitation_sum", [])
    valid_precip = [p for p in precip_list if p is not None]
    total_precip = sum(valid_precip) if valid_precip else 0
    avg_precip = total_precip / len(valid_precip) if valid_precip else 2.0

    # ── Extract water features ──
    w_elements = water.get("elements", []) if isinstance(water, dict) else []
    springs = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "spring")
    wells = sum(1 for e in w_elements if e.get("tags", {}).get("man_made") == "water_well")
    rivers = sum(1 for e in w_elements if e.get("tags", {}).get("waterway") in ("river", "stream"))
    water_bodies = sum(1 for e in w_elements if e.get("tags", {}).get("natural") == "water")
    water_total = len(w_elements)

    # ── Extract infrastructure ──
    elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    buildings = sum(1 for e in elements if e.get("tags", {}).get("building"))
    roads = sum(1 for e in elements if e.get("tags", {}).get("highway"))
    parks = sum(1 for e in elements if e.get("tags", {}).get("leisure") == "park")
    forests = sum(1 for e in elements
                  if e.get("tags", {}).get("landuse") in ("forest", "meadow"))

    # ── Extract protected areas ──
    p_elements = protected.get("elements", []) if isinstance(protected, dict) else []
    protected_count = len(p_elements)

    # ── Extract earthquake data ──
    features = (quakes if isinstance(quakes, dict) else {}).get("features", [])
    magnitudes = [f["properties"]["mag"] for f in features
                  if f.get("properties", {}).get("mag") is not None]
    max_mag = max(magnitudes) if magnitudes else 0
    eq_count = len(features)
    avg_mag = sum(magnitudes) / len(magnitudes) if magnitudes else 0

    # ── Score each disaster type 0-100 (higher = more resilient) ──
    disaster_scores = {}

    # 1. EARTHQUAKE RESILIENCE
    #    Rock ground > clay (sand/silt = stable); distance from recent quakes; low infra density
    ground_stability = min(100, max(0, (sand + silt) * 1.2 - clay * 0.5))
    seismic_distance = max(0, 100 - eq_count * 3 - max_mag * 8)
    infra_exposure = max(0, 100 - buildings * 1.5)
    eq_resilience = ground_stability * 0.40 + seismic_distance * 0.40 + infra_exposure * 0.20
    disaster_scores["earthquake"] = round(max(0, min(100, eq_resilience)))

    # 2. FLOOD RESILIENCE
    #    Elevation above waterways, drainage capacity (slope + sandy soil), infra protection
    elev_above_water = min(100, max(0, center_elev / 5))
    drainage_capacity = min(100, sand * 1.2 + avg_slope * 5)
    flood_infra = min(100, max(0, 100 - rivers * 10 - water_bodies * 15 + roads * 2))
    flood_resilience = elev_above_water * 0.40 + drainage_capacity * 0.35 + flood_infra * 0.25
    disaster_scores["flood"] = round(max(0, min(100, flood_resilience)))

    # 3. WILDFIRE RESILIENCE
    #    Firebreaks (roads, rivers), low fuel load, firefighter access, moisture
    firebreaks = min(100, roads * 4 + rivers * 8)
    fuel_load = max(0, 100 - forests * 8)
    fire_access = min(100, roads * 5)
    moisture = min(100, humidity * 0.8 + avg_precip * 8)
    wildfire_resilience = (firebreaks * 0.25 + fuel_load * 0.25 +
                           fire_access * 0.20 + moisture * 0.30)
    disaster_scores["wildfire"] = round(max(0, min(100, wildfire_resilience)))

    # 4. LANDSLIDE RESILIENCE
    #    Low slope, stable soil (low clay), good drainage, vegetation (roots)
    slope_score = max(0, 100 - elev_range * 0.3)
    soil_stability = max(0, 100 - clay * 1.5 + sand * 0.3)
    ls_drainage = min(100, sand * 1.0 + soc * 2)
    vegetation_hold = min(100, forests * 10 + parks * 5 + protected_count * 15)
    landslide_resilience = (slope_score * 0.35 + soil_stability * 0.25 +
                            ls_drainage * 0.20 + vegetation_hold * 0.20)
    disaster_scores["landslide"] = round(max(0, min(100, landslide_resilience)))

    # 5. STORM RESILIENCE
    #    Low elevation exposure, shelter availability, wind break features
    elev_exposure = max(0, 100 - max(0, center_elev - 500) * 0.1)
    shelter = min(100, buildings * 2 + roads * 1.5)
    wind_breaks = min(100, forests * 8 + buildings * 1.5 + parks * 3)
    storm_resilience = (elev_exposure * 0.30 + shelter * 0.35 + wind_breaks * 0.35)
    disaster_scores["storm"] = round(max(0, min(100, storm_resilience)))

    # 6. DROUGHT RESILIENCE
    #    Water reserves (springs, wells), soil water capacity, rainfall adequacy
    water_reserves = min(100, springs * 15 + wells * 20 + water_bodies * 10 + rivers * 5)
    soil_water_cap = min(100, clay * 1.0 + soc * 3 + silt * 0.5)
    rainfall_adequacy = min(100, total_precip * 4)
    drought_resilience = (water_reserves * 0.35 + soil_water_cap * 0.30 +
                          rainfall_adequacy * 0.35)
    disaster_scores["drought"] = round(max(0, min(100, drought_resilience)))

    # ── Overall Resilience Index (weighted average) ──
    overall = sum(disaster_scores[k] * DISASTER_TYPES[k]["weight"]
                  for k in disaster_scores)
    overall = round(overall)

    # ── Classification ──
    if overall > 80:
        classification = "Highly Resilient"
        class_color = "#10b981"
    elif overall > 60:
        classification = "Resilient"
        class_color = "#22c55e"
    elif overall > 40:
        classification = "Moderate"
        class_color = "#f59e0b"
    elif overall > 20:
        classification = "Vulnerable"
        class_color = "#f97316"
    else:
        classification = "Highly Vulnerable"
        class_color = "#ef4444"

    # ── Weakest link / strongest asset ──
    weakest_key = min(disaster_scores, key=disaster_scores.get)
    strongest_key = max(disaster_scores, key=disaster_scores.get)

    # ── Adaptive capacity ──
    infra_cap = min(100, roads * 3 + buildings * 0.5)
    natural_cap = min(100, protected_count * 20 + forests * 5 + water_total * 3)
    response_cap = min(100, roads * 4 + springs * 5 + wells * 8)
    adaptive_capacity = round((infra_cap + natural_cap + response_cap) / 3)

    # ── Recommendations ──
    recommendations = []
    if disaster_scores["earthquake"] < 50:
        recommendations.append(
            "Seismic retrofitting recommended. Soil composition shows elevated clay "
            "content which amplifies ground shaking. Reinforce critical infrastructure.")
    if disaster_scores["flood"] < 50:
        recommendations.append(
            "Improve drainage systems and flood barriers. Low elevation and proximity "
            "to waterways increase flood exposure. Consider permeable surfaces.")
    if disaster_scores["wildfire"] < 50:
        recommendations.append(
            "Create defensible space and firebreaks. Low humidity and dense vegetation "
            "increase fire risk. Improve road access for emergency responders.")
    if disaster_scores["landslide"] < 50:
        recommendations.append(
            "Stabilize slopes with vegetation and retaining structures. High clay content "
            "and steep terrain create landslide conditions. Improve drainage on hillsides.")
    if disaster_scores["storm"] < 50:
        recommendations.append(
            "Reinforce shelters and install windbreak barriers. Exposed elevation and "
            "limited shelter increase storm vulnerability. Secure roofing and structures.")
    if disaster_scores["drought"] < 50:
        recommendations.append(
            "Develop water storage and conservation systems. Limited reserves and low "
            "rainfall make drought impacts severe. Consider rainwater harvesting.")
    if not recommendations:
        recommendations.append(
            "Location demonstrates strong overall resilience. Continue monitoring "
            "environmental conditions and maintain existing protective infrastructure.")

    return {
        "overall": overall,
        "classification": classification,
        "class_color": class_color,
        "disaster_scores": disaster_scores,
        "weakest_link": weakest_key,
        "strongest_asset": strongest_key,
        "adaptive_capacity": adaptive_capacity,
        "recommendations": recommendations,
    }


# ═══════════════════════════════════════════════════════════════════════════
# RENDERING
# ═══════════════════════════════════════════════════════════════════════════

def _resilience_color(score: int) -> str:
    """Return green/amber/red colour for a resilience score."""
    if score >= 70:
        return "#10b981"
    if score >= 40:
        return "#f59e0b"
    return "#ef4444"


def render_disaster_resilience_tab():
    """Render the Disaster Resilience AI tab."""
    st.markdown("## Disaster Resilience AI")
    st.caption("Evaluate how resilient a location is to 6 natural disaster types")

    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox("Location", list(ANALYSIS_PRESETS.keys()), key="dr_preset")
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input("Lat", -90.0, 90.0,
                                  p.get("lat", 41.90) if p else 41.90,
                                  step=0.01, key="dr_lat", format="%.4f")
        with c2:
            lon = st.number_input("Lon", -180.0, 180.0,
                                  p.get("lon", 12.50) if p else 12.50,
                                  step=0.01, key="dr_lon", format="%.4f")

    if st.button("Assess Resilience", type="primary", use_container_width=True):
        with st.spinner("Assessing disaster resilience across 6 categories..."):
            result = compute_disaster_resilience(lat, lon)

        if not result:
            st.error("Resilience assessment failed.")
            return

        overall = result["overall"]
        classification = result["classification"]
        class_color = result["class_color"]
        scores = result["disaster_scores"]
        weakest = result["weakest_link"]
        strongest = result["strongest_asset"]
        adaptive = result["adaptive_capacity"]
        recs = result["recommendations"]

        # ── Overall Resilience Header ──
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, {class_color}22, {class_color}44);
                    border-left:5px solid {class_color}; border-radius:12px;
                    padding:25px; margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:#888; font-size:12px;">OVERALL DISASTER RESILIENCE</div>
                    <div style="color:{class_color}; font-size:36px; font-weight:bold; margin:4px 0;">
                        {classification}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:56px; font-weight:bold; color:{class_color};">
                        {overall}
                    </div>
                    <div style="color:#888; font-size:14px;">/100</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── 6 Disaster Resilience Cards (3x2 grid) ──
        st.markdown("### Resilience by Disaster Type")
        cols = st.columns(3)
        for idx, (d_key, d_info) in enumerate(DISASTER_TYPES.items()):
            score = scores[d_key]
            sc = _resilience_color(score)
            with cols[idx % 3]:
                st.markdown(f"""
                <div style="background:#1a1a2e; border:1px solid {d_info['color']}44;
                            border-radius:10px; padding:15px; margin:5px 0; min-height:120px;">
                    <div style="color:{d_info['color']}; font-weight:bold; font-size:13px;">
                        {d_info['name']}
                    </div>
                    <div style="font-size:32px; font-weight:bold; color:{sc}; margin:4px 0;">
                        {score}<span style="font-size:12px; color:#888;">%</span>
                    </div>
                    <div style="background:#2a2a3e; border-radius:4px; height:6px; margin-top:6px;">
                        <div style="background:{sc}; width:{score}%; height:6px;
                                    border-radius:4px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ── Radar Chart ──
        st.markdown("### Resilience Radar")
        radar_names = [DISASTER_TYPES[k]["name"] for k in scores]
        radar_values = [scores[k] for k in scores]

        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(
            r=radar_values + [radar_values[0]],
            theta=radar_names + [radar_names[0]],
            fill="toself",
            fillcolor=_hex_rgba(class_color, 0.13),
            line=dict(color=class_color, width=2),
            name="Resilience",
        ))
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100]),
                bgcolor="#1a1a2e",
            ),
            showlegend=False,
            height=420,
            margin=dict(t=30, b=30, l=80, r=80),
            paper_bgcolor="#1a1a2e",
            font=dict(color="#ccc"),
        )
        st.plotly_chart(fig_radar, use_container_width=True, key="disres_pchart1")

        # ── Weakest Link Alert ──
        w_score = scores[weakest]
        w_color = _resilience_color(w_score)
        w_name = DISASTER_TYPES[weakest]["name"]
        st.markdown(f"""
        <div style="background:#ef444422; border-left:5px solid #ef4444;
                    border-radius:10px; padding:18px; margin:10px 0;">
            <div style="color:#ef4444; font-size:12px; font-weight:bold;">
                WEAKEST LINK
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="color:#ff8888; font-size:20px; font-weight:bold; margin:4px 0;">
                    {w_name}
                </div>
                <div style="color:{w_color}; font-size:32px; font-weight:bold;">
                    {w_score}<span style="font-size:12px; color:#888;">%</span>
                </div>
            </div>
            <div style="color:#ccc; font-size:13px;">
                This is the most vulnerable disaster category for this location.
                Priority attention recommended.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Strongest Asset Highlight ──
        s_score = scores[strongest]
        s_color = _resilience_color(s_score)
        s_name = DISASTER_TYPES[strongest]["name"]
        st.markdown(f"""
        <div style="background:#10b98122; border-left:5px solid #10b981;
                    border-radius:10px; padding:18px; margin:10px 0;">
            <div style="color:#10b981; font-size:12px; font-weight:bold;">
                STRONGEST ASSET
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div style="color:#6ee7b7; font-size:20px; font-weight:bold; margin:4px 0;">
                    {s_name}
                </div>
                <div style="color:{s_color}; font-size:32px; font-weight:bold;">
                    {s_score}<span style="font-size:12px; color:#888;">%</span>
                </div>
            </div>
            <div style="color:#ccc; font-size:13px;">
                This disaster category shows the highest natural and structural resilience.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Horizontal Bar Chart (sorted by resilience score) ──
        st.markdown("### Resilience Ranking")
        sorted_keys = sorted(scores, key=scores.get, reverse=True)
        bar_names = [DISASTER_TYPES[k]["name"] for k in sorted_keys]
        bar_values = [scores[k] for k in sorted_keys]
        bar_colors = [_resilience_color(v) for v in bar_values]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=bar_values,
            y=bar_names,
            orientation="h",
            marker_color=bar_colors,
            text=[f"{v}%" for v in bar_values],
            textposition="auto",
            textfont=dict(color="white"),
        ))
        fig_bar.update_layout(
            height=max(250, len(bar_names) * 45),
            margin=dict(t=10, b=20, l=160, r=20),
            xaxis=dict(range=[0, 100], title="Resilience Score"),
            yaxis=dict(autorange="reversed"),
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#1a1a2e",
            font=dict(color="#ccc"),
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="disres_pchart2")

        # ── Adaptive Capacity ──
        st.markdown("### Adaptive Capacity")
        ac_color = _resilience_color(adaptive)
        st.markdown(f"""
        <div style="background:#1a1a2e; border:1px solid {ac_color}44;
                    border-radius:10px; padding:20px; margin:10px 0;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="color:#888; font-size:12px;">ADAPTIVE CAPACITY INDEX</div>
                    <div style="color:#ccc; font-size:13px; margin-top:6px;">
                        Measures the location's ability to respond, recover, and adapt
                        to disaster events based on infrastructure, natural buffers,
                        and emergency response access.
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:48px; font-weight:bold; color:{ac_color};">
                        {adaptive}
                    </div>
                    <div style="color:#888; font-size:13px;">/100</div>
                </div>
            </div>
            <div style="background:#2a2a3e; border-radius:4px; height:8px; margin-top:14px;">
                <div style="background:{ac_color}; width:{adaptive}%; height:8px;
                            border-radius:4px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Recommendations ──
        st.markdown("### Recommendations for Improving Resilience")
        for i, rec in enumerate(recs):
            rec_num = i + 1
            st.markdown(f"""
            <div style="background:#1a1a2e; border-left:4px solid #3b82f6;
                        border-radius:8px; padding:14px; margin:8px 0;">
                <div style="color:#60a5fa; font-size:12px; font-weight:bold;">
                    RECOMMENDATION {rec_num}
                </div>
                <div style="color:#ddd; font-size:14px; margin-top:4px;">
                    {rec}
                </div>
            </div>
            """, unsafe_allow_html=True)
