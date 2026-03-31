"""
Renewable Energy Potential AI for TerraScout AI.
Evaluates renewable energy generation potential across five sources:
Solar, Wind, Hydroelectric, Geothermal, and Biomass.
Combines weather, elevation, water features, and infrastructure data
into a unified energy potential assessment with estimated generation
figures and infrastructure readiness scores.
"""

import logging
import math

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_weather_data,
    fetch_elevation_grid,
    fetch_water_features,
    fetch_landuse_infrastructure,
)


def _hex_rgba(hc, a=1.0):
    """Convert #RRGGBB + alpha float to rgba() for Plotly compatibility."""
    h = hc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# ENERGY SOURCE METADATA
# ═══════════════════════════════════════════════════════════════

ENERGY_SOURCES = {
    "Solar": {
        "icon": "☀️",
        "color": "#f59e0b",
        "factors": ["Cloud cover", "Latitude", "Temperature", "Sunshine hours"],
    },
    "Wind": {
        "icon": "💨",
        "color": "#06b6d4",
        "factors": ["Wind speed", "Elevation exposure", "Terrain openness"],
    },
    "Hydroelectric": {
        "icon": "🌊",
        "color": "#3b82f6",
        "factors": ["Rivers/streams", "Elevation drop", "Rainfall"],
    },
    "Geothermal": {
        "icon": "🌋",
        "color": "#ef4444",
        "factors": ["Hot springs", "Volcanic proximity", "Deep heat estimate"],
    },
    "Biomass": {
        "icon": "🌿",
        "color": "#22c55e",
        "factors": ["Agricultural potential", "Organic matter", "Existing farmland"],
    },
}


# ═══════════════════════════════════════════════════════════════
# COMPUTE ENERGY POTENTIAL (CACHED)
# ═══════════════════════════════════════════════════════════════

@st.cache_data(ttl=1800)
def compute_energy_potential(lat: float, lon: float) -> dict:
    """
    Evaluate renewable energy potential at a given location.
    Returns source scores, estimated generation, infrastructure readiness,
    best source, total potential, and recommendations.
    """
    # ── Fetch all data sources ──
    weather = fetch_weather_data(lat, lon) or {}
    elevation = fetch_elevation_grid(lat, lon, grid_size=6) or {}
    water = fetch_water_features(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}

    # ── Extract weather data ──
    daily = weather.get("daily", {})
    current = weather.get("current", {})

    temp_max_list = daily.get("temperature_2m_max", [])
    temp_min_list = daily.get("temperature_2m_min", [])
    precip_list = daily.get("precipitation_sum", [])

    valid_tmax = [t for t in temp_max_list if t is not None]
    valid_tmin = [t for t in temp_min_list if t is not None]
    valid_precip = [p for p in precip_list if p is not None]

    avg_tmax = sum(valid_tmax) / len(valid_tmax) if valid_tmax else 20.0
    avg_tmin = sum(valid_tmin) / len(valid_tmin) if valid_tmin else 10.0
    avg_temp = (avg_tmax + avg_tmin) / 2
    weekly_precip = sum(valid_precip) if valid_precip else 5.0
    annual_precip_est = weekly_precip * 52

    cloud_cover = current.get("cloud_cover", 50) or 50
    wind_speed = current.get("wind_speed_10m", 0) or 0
    humidity = current.get("relative_humidity_2m", 50) or 50

    # ── Extract water features ──
    w_elements = (water if isinstance(water, dict) else {}).get("elements", [])
    rivers = sum(1 for e in w_elements
                 if e.get("tags", {}).get("waterway") in ("river", "stream"))
    springs = sum(1 for e in w_elements
                  if e.get("tags", {}).get("natural") == "spring")
    hot_springs = sum(1 for e in w_elements
                      if e.get("tags", {}).get("natural") == "hot_spring")
    waterways_total = sum(1 for e in w_elements if e.get("tags", {}).get("waterway"))

    # ── Extract elevation data ──
    elevations = (elevation if isinstance(elevation, dict) else {}).get(
        "grid_elevations", []
    )
    valid_elevations = [e for e in elevations if e is not None]
    center_elev = elevation.get("center_elevation", 0) or 0
    max_elev = max(valid_elevations) if valid_elevations else 0
    min_elev = min(valid_elevations) if valid_elevations else 0
    relief = max_elev - min_elev if isinstance(max_elev, (int, float)) and isinstance(min_elev, (int, float)) else 0

    # ── Extract infrastructure data ──
    i_elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    buildings = sum(1 for e in i_elements if e.get("tags", {}).get("building"))
    roads = sum(1 for e in i_elements if e.get("tags", {}).get("highway"))
    farmlands = sum(1 for e in i_elements
                    if e.get("tags", {}).get("landuse") == "farmland")
    forests = sum(1 for e in i_elements
                  if e.get("tags", {}).get("landuse") in ("forest", "wood"))
    power_lines = sum(1 for e in i_elements
                      if e.get("tags", {}).get("power"))

    source_scores = {}
    estimated_generation = {}

    # ════════════════════════════════════════════════════════════
    # 1. SOLAR
    # ════════════════════════════════════════════════════════════
    sol = 20
    cloud_pct = cloud_cover if isinstance(cloud_cover, (int, float)) else 50

    if cloud_pct < 20:
        sol += 30
    elif cloud_pct < 40:
        sol += 22
    elif cloud_pct < 60:
        sol += 14
    elif cloud_pct < 80:
        sol += 6

    abs_lat = abs(lat)
    if abs_lat < 25:
        sol += 25
    elif abs_lat < 35:
        sol += 18
    elif abs_lat < 45:
        sol += 10
    elif abs_lat < 55:
        sol += 4

    if avg_temp > 25:
        sol += 10
    elif avg_temp > 15:
        sol += 6
    elif avg_temp > 5:
        sol += 2

    sunshine_est = max(0.0, (100 - cloud_pct) / 100.0 * 14)
    sol += min(15, int(sunshine_est))

    source_scores["Solar"] = max(0, min(100, round(sol)))

    kwh_m2_day = (100 - cloud_pct) * 0.06 * (1 + 0.01 * (35 - abs_lat))
    estimated_generation["Solar"] = {
        "kwh_m2_day": round(max(0.0, kwh_m2_day), 2),
        "sunshine_hours": round(sunshine_est, 1),
        "unit": "kWh/m2/day",
    }

    # ════════════════════════════════════════════════════════════
    # 2. WIND
    # ════════════════════════════════════════════════════════════
    wnd = 15
    ws = wind_speed if isinstance(wind_speed, (int, float)) else 0

    if ws >= 25:
        wnd += 35
    elif ws >= 15:
        wnd += 28
    elif ws >= 10:
        wnd += 22
    elif ws >= 6:
        wnd += 15
    elif ws >= 3:
        wnd += 8

    if center_elev > 800:
        wnd += 15
    elif center_elev > 400:
        wnd += 10
    elif center_elev > 100:
        wnd += 5

    if buildings < 5:
        wnd += 12
    elif buildings < 20:
        wnd += 6
    elif buildings < 50:
        wnd += 2

    if relief > 200:
        wnd += 8
    elif relief > 50:
        wnd += 4

    source_scores["Wind"] = max(0, min(100, round(wnd)))

    capacity_factor = min(100.0, ws / 15.0 * 100.0) if ws > 0 else 0.0
    estimated_generation["Wind"] = {
        "capacity_factor_pct": round(capacity_factor, 1),
        "wind_speed_kmh": round(ws, 1),
        "unit": "% capacity factor",
    }

    # ════════════════════════════════════════════════════════════
    # 3. HYDROELECTRIC
    # ════════════════════════════════════════════════════════════
    hydro = 10

    hydro += min(25, rivers * 8)
    hydro += min(10, waterways_total * 3)

    head = relief
    if head > 300:
        hydro += 25
    elif head > 150:
        hydro += 18
    elif head > 50:
        hydro += 12
    elif head > 20:
        hydro += 6

    if annual_precip_est > 1200:
        hydro += 20
    elif annual_precip_est > 800:
        hydro += 14
    elif annual_precip_est > 400:
        hydro += 8
    elif annual_precip_est > 200:
        hydro += 4

    source_scores["Hydroelectric"] = max(0, min(100, round(hydro)))

    head_m = round(head, 1) if isinstance(head, (int, float)) else 0
    estimated_generation["Hydroelectric"] = {
        "elevation_head_m": head_m,
        "rivers_streams": rivers,
        "annual_precip_mm": round(annual_precip_est),
        "unit": "m head / river count",
    }

    # ════════════════════════════════════════════════════════════
    # 4. GEOTHERMAL
    # ════════════════════════════════════════════════════════════
    geo = 10

    if hot_springs > 0:
        geo += min(25, hot_springs * 12)
    if springs > 0:
        geo += min(15, springs * 5)

    if center_elev > 2000:
        geo += 12
    elif center_elev > 1000:
        geo += 8
    elif center_elev > 500:
        geo += 4

    if relief > 500:
        geo += 12
    elif relief > 200:
        geo += 7
    elif relief > 100:
        geo += 3

    ring_of_fire = (
        (30 <= abs_lat <= 45) or
        (abs_lat < 10) or
        (55 <= abs_lat <= 67)
    )
    if ring_of_fire:
        geo += 12
    elif 10 <= abs_lat <= 30:
        geo += 6

    deep_heat_est = min(100, geo * 1.2)
    source_scores["Geothermal"] = max(0, min(100, round(geo)))

    estimated_generation["Geothermal"] = {
        "deep_heat_index": round(deep_heat_est, 1),
        "hot_springs_nearby": hot_springs + springs,
        "tectonic_zone": "Active" if ring_of_fire else "Moderate",
        "unit": "heat index (0-100)",
    }

    # ════════════════════════════════════════════════════════════
    # 5. BIOMASS
    # ════════════════════════════════════════════════════════════
    bio = 15

    if 10 <= avg_temp <= 30:
        bio += 15
    elif 5 <= avg_temp <= 35:
        bio += 8
    elif avg_temp > 0:
        bio += 3

    if annual_precip_est > 800:
        bio += 15
    elif annual_precip_est > 400:
        bio += 10
    elif annual_precip_est > 200:
        bio += 5

    if farmlands > 0:
        bio += min(20, farmlands * 5)
    if forests > 0:
        bio += min(10, forests * 3)

    if humidity > 60:
        bio += 8
    elif humidity > 40:
        bio += 4

    source_scores["Biomass"] = max(0, min(100, round(bio)))

    estimated_generation["Biomass"] = {
        "farmland_areas": farmlands,
        "forest_areas": forests,
        "climate_suitability": (
            "High" if avg_temp > 15 and annual_precip_est > 600
            else "Moderate" if avg_temp > 5 and annual_precip_est > 300
            else "Low"
        ),
        "unit": "suitability index",
    }

    # ════════════════════════════════════════════════════════════
    # INFRASTRUCTURE READINESS
    # ════════════════════════════════════════════════════════════
    infra_score = 10
    if power_lines > 0:
        infra_score += min(30, power_lines * 6)
    if roads > 5:
        infra_score += 25
    elif roads > 0:
        infra_score += 15
    if buildings > 10:
        infra_score += 15
    elif buildings > 0:
        infra_score += 8
    infra_score = max(0, min(100, infra_score))

    infrastructure_readiness = {
        "score": infra_score,
        "power_grid_nearby": power_lines > 0,
        "road_access": "Good" if roads > 5 else "Limited" if roads > 0 else "None",
        "power_lines": power_lines,
        "roads": roads,
        "buildings": buildings,
    }

    # ════════════════════════════════════════════════════════════
    # BEST SOURCE & TOTAL
    # ════════════════════════════════════════════════════════════
    all_scores = list(source_scores.values())
    total_potential = round(sum(all_scores) / len(all_scores)) if all_scores else 0

    sorted_sources = sorted(source_scores.items(), key=lambda x: x[1], reverse=True)
    best_source = sorted_sources[0] if sorted_sources else ("Solar", 0)

    # ════════════════════════════════════════════════════════════
    # RECOMMENDATIONS
    # ════════════════════════════════════════════════════════════
    recommendations = []
    best_name, best_score = best_source

    if best_score >= 70:
        recommendations.append(
            f"{best_name} energy shows excellent potential ({best_score}/100). "
            f"Consider large-scale {best_name.lower()} installation."
        )
    elif best_score >= 45:
        recommendations.append(
            f"{best_name} energy shows good potential ({best_score}/100). "
            f"A feasibility study for {best_name.lower()} is recommended."
        )
    else:
        recommendations.append(
            f"No single source exceeds 45/100. A hybrid micro-grid approach "
            f"combining multiple low-output sources may be viable."
        )

    viable = [name for name, sc in sorted_sources if sc >= 40]
    if len(viable) >= 2:
        recommendations.append(
            f"Hybrid opportunity: combine {viable[0]} + {viable[1]} for "
            f"diversified generation and improved reliability."
        )

    if infra_score < 30:
        recommendations.append(
            "Infrastructure is limited. Off-grid or standalone systems with "
            "battery storage would be required for deployment."
        )
    elif infra_score >= 60:
        recommendations.append(
            "Good existing infrastructure. Grid-tied installations can reduce "
            "capital costs and enable net metering."
        )

    if source_scores.get("Solar", 0) >= 50 and source_scores.get("Wind", 0) >= 40:
        recommendations.append(
            "Solar-wind complementarity detected. Daytime solar combined with "
            "evening/night wind generation can provide near-continuous output."
        )

    return {
        "source_scores": source_scores,
        "estimated_generation": estimated_generation,
        "infrastructure_readiness": infrastructure_readiness,
        "best_source": {"name": best_name, "score": best_score},
        "total_potential": total_potential,
        "recommendations": recommendations,
    }


# ═══════════════════════════════════════════════════════════════
# RENDER TAB
# ═══════════════════════════════════════════════════════════════

def render_energy_potential_tab():
    """Render the Renewable Energy Potential AI tab."""
    st.markdown("## Renewable Energy Potential AI")
    st.caption("Evaluate renewable energy generation potential across 5 sources")

    # ── Location selector ──
    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox(
            "Location", list(ANALYSIS_PRESETS.keys()), key="ep_preset"
        )
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input(
                "Lat", -90.0, 90.0,
                p.get("lat", 41.90) if p else 41.90,
                step=0.01, key="ep_lat", format="%.4f",
            )
        with c2:
            lon = st.number_input(
                "Lon", -180.0, 180.0,
                p.get("lon", 12.50) if p else 12.50,
                step=0.01, key="ep_lon", format="%.4f",
            )

    if not st.button("Assess Energy Potential", type="primary",
                     use_container_width=True):
        return

    with st.spinner("Evaluating renewable energy potential across 5 sources..."):
        result = compute_energy_potential(lat, lon)

    if not result:
        st.error("Energy potential assessment failed.")
        return

    scores = result["source_scores"]
    gen = result["estimated_generation"]
    infra_ready = result["infrastructure_readiness"]
    best = result["best_source"]
    total = result["total_potential"]
    recs = result["recommendations"]

    # ── Best energy source header ──
    best_meta = ENERGY_SOURCES.get(best["name"], {})
    best_color = best_meta.get("color", "#22c55e")
    best_icon = best_meta.get("icon", "⚡")

    st.markdown(f"""
    <div style="background:linear-gradient(135deg, {best_color}22, {best_color}44);
                border-left:5px solid {best_color}; border-radius:12px;
                padding:25px; margin:10px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#888; font-size:12px;">BEST ENERGY SOURCE</div>
                <div style="color:{best_color}; font-size:32px; font-weight:bold; margin:4px 0;">
                    {best_icon} {best["name"]}
                </div>
                <div style="color:#aaa; font-size:13px;">
                    Overall potential: {total}/100 &mdash; {lat:.4f}, {lon:.4f}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:56px; font-weight:bold; color:{best_color};">
                    {best["score"]}
                </div>
                <div style="color:#888; font-size:14px;">/100</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Energy source cards (5 columns) ──
    st.markdown("### Energy Source Scores")
    source_list = list(ENERGY_SOURCES.items())
    cols = st.columns(5)
    for idx, (src_name, src_meta) in enumerate(source_list):
        score = scores.get(src_name, 0)
        color = src_meta["color"]
        icon = src_meta["icon"]
        src_gen = gen.get(src_name, {})
        gen_label = ""
        if src_name == "Solar":
            gen_label = f"{src_gen.get('kwh_m2_day', 0)} kWh/m2/d"
        elif src_name == "Wind":
            gen_label = f"CF {src_gen.get('capacity_factor_pct', 0)}%"
        elif src_name == "Hydroelectric":
            gen_label = f"{src_gen.get('elevation_head_m', 0)}m head"
        elif src_name == "Geothermal":
            gen_label = f"Heat {src_gen.get('deep_heat_index', 0)}"
        elif src_name == "Biomass":
            gen_label = src_gen.get("climate_suitability", "N/A")

        if score >= 70:
            sc = "#10b981"
        elif score >= 40:
            sc = "#f59e0b"
        else:
            sc = "#ef4444"

        with cols[idx]:
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid {color}44;
                        border-radius:10px; padding:14px; margin:4px 0;
                        min-height:170px;">
                <div style="color:{color}; font-weight:bold; font-size:13px;
                            text-align:center;">
                    {icon} {src_name}
                </div>
                <div style="font-size:34px; font-weight:bold; color:{sc};
                            margin:8px 0; text-align:center;">
                    {score}<span style="font-size:12px; color:#888;">%</span>
                </div>
                <div style="background:#111827; border-radius:6px; height:6px;
                            margin:6px 0;">
                    <div style="background:{color}; height:6px; border-radius:6px;
                                width:{score}%;"></div>
                </div>
                <div style="color:#aaa; font-size:11px; text-align:center;
                            margin-top:6px;">
                    {gen_label}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Horizontal bar chart ──
    st.markdown("### Energy Source Ranking")
    sorted_src = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    bar_names = [s[0] for s in sorted_src]
    bar_values = [s[1] for s in sorted_src]
    bar_colors = [ENERGY_SOURCES[n]["color"] for n in bar_names]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=bar_values,
        y=bar_names,
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{v}%" for v in bar_values],
        textposition="outside",
        textfont=dict(size=12),
    ))
    fig_bar.update_layout(
        height=320,
        margin=dict(t=20, b=20, l=110, r=40),
        xaxis=dict(range=[0, 110], title="Score"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_bar, use_container_width=True, key="enepot_pchart1")

    # ── Radar chart ──
    st.markdown("### Energy Dimensions Radar")
    src_names = list(ENERGY_SOURCES.keys())
    src_values = [scores.get(s, 0) for s in src_names]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=src_values + [src_values[0]],
        theta=src_names + [src_names[0]],
        fill="toself",
        fillcolor=_hex_rgba(best_color, 0.13),
        line=dict(color=best_color, width=2),
        marker=dict(size=6, color=best_color),
        name="Energy Potential",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(size=10)),
            angularaxis=dict(tickfont=dict(size=11)),
        ),
        showlegend=False,
        height=420,
        margin=dict(t=40, b=40, l=80, r=80),
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="enepot_pchart2")

    # ── Infrastructure readiness ──
    st.markdown("### Infrastructure Readiness")
    inf_sc = infra_ready["score"]
    if inf_sc >= 60:
        inf_color = "#10b981"
        inf_label = "Good"
    elif inf_sc >= 35:
        inf_color = "#f59e0b"
        inf_label = "Moderate"
    else:
        inf_color = "#ef4444"
        inf_label = "Limited"

    st.markdown(f"""
    <div style="background:#1a1a2e; border:1px solid {inf_color}44;
                border-radius:10px; padding:18px; margin:8px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:{inf_color}; font-weight:bold; font-size:16px;">
                    Infrastructure: {inf_label}
                </div>
                <div style="color:#aaa; font-size:12px; margin-top:4px;">
                    Power grid: {"Yes" if infra_ready["power_grid_nearby"] else "No"}
                    &nbsp;|&nbsp; Road access: {infra_ready["road_access"]}
                    &nbsp;|&nbsp; Power lines: {infra_ready["power_lines"]}
                    &nbsp;|&nbsp; Roads: {infra_ready["roads"]}
                </div>
            </div>
            <div style="font-size:38px; font-weight:bold; color:{inf_color};">
                {inf_sc}<span style="font-size:12px; color:#888;">%</span>
            </div>
        </div>
        <div style="background:#111827; border-radius:6px; height:8px; margin-top:10px;">
            <div style="background:{inf_color}; height:8px; border-radius:6px;
                        width:{inf_sc}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Estimated generation metrics ──
    st.markdown("### Estimated Generation")
    gen_cols = st.columns(5)
    for idx, (src_name, src_meta) in enumerate(source_list):
        src_gen = gen.get(src_name, {})
        color = src_meta["color"]
        icon = src_meta["icon"]
        detail_lines = []
        for k, v in src_gen.items():
            if k == "unit":
                continue
            label = k.replace("_", " ").title()
            detail_lines.append(
                f'<div style="display:flex; justify-content:space-between; '
                f'padding:3px 0; border-bottom:1px solid #ffffff08;">'
                f'<span style="color:#aaa; font-size:11px;">{label}</span>'
                f'<span style="color:{color}; font-weight:bold; font-size:11px;">'
                f'{v}</span></div>'
            )
        detail_html = "".join(detail_lines)
        with gen_cols[idx]:
            st.markdown(f"""
            <div style="background:#1a1a2e; border:1px solid {color}33;
                        border-radius:8px; padding:12px; min-height:130px;">
                <div style="color:{color}; font-weight:bold; font-size:12px;
                            margin-bottom:8px; text-align:center;">
                    {icon} {src_name}
                </div>
                {detail_html}
            </div>
            """, unsafe_allow_html=True)

    # ── Recommendations ──
    st.markdown("### Recommendations")
    for i, rec in enumerate(recs):
        if i == 0:
            rec_color = best_color
        elif "hybrid" in rec.lower() or "combine" in rec.lower():
            rec_color = "#8b5cf6"
        elif "infrastructure" in rec.lower() or "off-grid" in rec.lower():
            rec_color = "#f97316"
        else:
            rec_color = "#06b6d4"

        st.markdown(f"""
        <div style="background:#1a1a2e; border-left:4px solid {rec_color};
                    border-radius:8px; padding:14px; margin:6px 0;">
            <div style="color:#e2e8f0; font-size:13px;">{rec}</div>
        </div>
        """, unsafe_allow_html=True)
