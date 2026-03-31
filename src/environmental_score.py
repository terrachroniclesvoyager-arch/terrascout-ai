"""
Environmental Score AI module for TerraScout AI.
Computes a comprehensive Environmental Sustainability Score (ESS) for
geographic locations, similar to an ESG rating but focused on environmental
and ecological health indicators.

Pillars:
  1. Natural Capital - biodiversity, species richness, protected areas
  2. Environmental Quality - air/water/soil quality indicators
  3. Climate Resilience - temperature stability, precipitation, extremes
  4. Land Integrity - natural vs developed land, erosion, soil health
  5. Sustainability Potential - renewable energy, water, carbon sequestration
"""

import logging
import html as html_module

import numpy as np
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_species_breakdown,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ESS PILLAR DEFINITIONS
# ---------------------------------------------------------------------------

ESS_PILLARS = {
    "Natural Capital": {
        "description": "Biodiversity, species richness, protected areas",
        "weight": 0.25,
        "color": "#22c55e",
    },
    "Environmental Quality": {
        "description": "Air/water/soil quality indicators",
        "weight": 0.25,
        "color": "#3b82f6",
    },
    "Climate Resilience": {
        "description": "Temperature stability, precipitation adequacy, extreme weather risk",
        "weight": 0.20,
        "color": "#f59e0b",
    },
    "Land Integrity": {
        "description": "Natural vs developed land, erosion risk, soil health",
        "weight": 0.15,
        "color": "#8b5cf6",
    },
    "Sustainability Potential": {
        "description": "Renewable energy potential, water resources, carbon sequestration",
        "weight": 0.15,
        "color": "#06b6d4",
    },
}

GRADE_COLORS = {
    "A+": "#10b981",
    "A": "#10b981",
    "B+": "#22c55e",
    "B": "#22c55e",
    "C": "#f59e0b",
    "D": "#f97316",
    "F": "#ef4444",
}

# ---------------------------------------------------------------------------
# SOIL HELPERS
# ---------------------------------------------------------------------------

def _extract_soil_value(soil_data, prop_name, divisor=10):
    """Return the mean value for *prop_name* from a SoilGrids v2.0 response."""
    try:
        raw_props = (soil_data if isinstance(soil_data, dict) else {}).get("properties", {})
        layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
        for layer in layers:
            if isinstance(layer, dict) and layer.get("name") == prop_name:
                depths = layer.get("depths", [])
                if depths and isinstance(depths[0], dict):
                    val = depths[0].get("values", {}).get("mean")
                    if val is not None:
                        return val / divisor
        return 0.0
    except Exception:
        return 0.0


# ---------------------------------------------------------------------------
# COMPUTE ENVIRONMENTAL SCORE (CACHED)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def compute_environmental_score(lat: float, lon: float) -> dict:
    """Fetch all data sources and compute the ESS rating for a location.

    Returns a dict with:
        ess_score, letter_grade, grade_color,
        pillar_scores, pillar_details,
        strengths, weaknesses, recommendations
    """
    # -- Fetch data --------------------------------------------------------
    soil = fetch_soil_data(lat, lon)
    weather = fetch_weather_data(lat, lon)
    water = fetch_water_features(lat, lon)
    elevation = fetch_elevation_grid(lat, lon)
    infra = fetch_landuse_infrastructure(lat, lon)
    protected = fetch_protected_areas(lat, lon)
    inat = fetch_biodiversity(lat, lon)
    gbif = fetch_gbif_occurrences(lat, lon)

    species = compute_species_breakdown(inat, gbif)

    # -- Derived values ----------------------------------------------------
    kingdom_counts = species.get("kingdom_counts", {})
    top_species = species.get("top_species", [])
    inat_total = species.get("inat_total", 0)
    gbif_total = species.get("gbif_total", 0)
    gbif_unique = species.get("gbif_unique_species", 0)

    protected_count = len(protected.get("elements", []))
    water_count = len(water.get("elements", []))
    kingdom_diversity = len(kingdom_counts)
    species_count = gbif_unique

    # Soil values
    ph_val = _extract_soil_value(soil, "phh2o")
    soc_val = _extract_soil_value(soil, "soc")
    clay_val = _extract_soil_value(soil, "clay")
    nitrogen_val = _extract_soil_value(soil, "nitrogen")

    # Weather values
    current = weather.get("current", {})
    daily = weather.get("daily", {})
    avg_temp = current.get("temperature_2m", 15.0)
    wind_speed = current.get("wind_speed_10m", 0.0)
    cloud_cover = current.get("cloud_cover", 50.0)
    humidity = current.get("relative_humidity_2m", 50.0)
    precip_now = current.get("precipitation", 0.0)
    daily_precip = daily.get("precipitation_sum", [])
    daily_max = [t for t in daily.get("temperature_2m_max", []) if t is not None]
    daily_min = [t for t in daily.get("temperature_2m_min", []) if t is not None]
    if daily_max and daily_min:
        avg_temp = float(np.mean(daily_max + daily_min))
    precip_weekly = float(np.sum(daily_precip)) if daily_precip else 0.0
    precip_adequacy = min(precip_weekly * 7.0, 100.0)  # rough annual proxy

    # Infrastructure breakdown
    building_count = 0
    road_count = 0
    industrial_count = 0
    park_count = 0
    for el in infra.get("elements", []):
        tags = el.get("tags", {})
        if "building" in tags:
            building_count += 1
        elif "highway" in tags:
            road_count += 1
        elif tags.get("landuse") == "industrial":
            industrial_count += 1
        elif tags.get("leisure") == "park":
            park_count += 1

    # Elevation / slope
    elev_range = elevation.get("max_elevation", 0) - elevation.get("min_elevation", 0)
    erosion_risk = min(elev_range / 10.0, 50.0)  # steeper = more erosion
    soil_health = min(soc_val * 3.0 + nitrogen_val * 5.0 + clay_val * 0.5, 60.0)

    # -- Pillar scores (0-100 each) ----------------------------------------

    # 1. Natural Capital
    nc_raw = (
        species_count * 3
        + inat_total / 20.0
        + protected_count * 20
        + kingdom_diversity * 10
    )
    nc_score = max(0.0, min(100.0, nc_raw))

    # 2. Environmental Quality
    ph_score = max(0.0, 40.0 - abs(ph_val - 6.5) * 15.0) if ph_val > 0 else 20.0
    soc_score = min(soc_val * 2.0, 30.0)
    eq_raw = ph_score + soc_score + water_count * 5 - industrial_count * 15
    eq_score = max(0.0, min(100.0, eq_raw))

    # 3. Climate Resilience
    wind_exposure = min(wind_speed * 1.5, 30.0)
    cr_raw = 100.0 - abs(avg_temp - 20.0) * 3.0 - wind_exposure + precip_adequacy * 0.3
    cr_score = max(0.0, min(100.0, cr_raw))

    # 4. Land Integrity
    li_raw = 100.0 - building_count * 2 - road_count - erosion_risk + soil_health
    li_score = max(0.0, min(100.0, li_raw))

    # 5. Sustainability Potential
    solar_potential = max(0.0, 100.0 - cloud_cover * 1.2)
    wind_potential = min(wind_speed * 3.0, 30.0)
    water_resources = min(water_count * 4.0, 25.0)
    carbon_seq = min(soc_val * 2.0, 20.0)
    sp_raw = solar_potential * 0.35 + wind_potential + water_resources + carbon_seq
    sp_score = max(0.0, min(100.0, sp_raw))

    pillar_scores = {
        "Natural Capital": round(nc_score, 1),
        "Environmental Quality": round(eq_score, 1),
        "Climate Resilience": round(cr_score, 1),
        "Land Integrity": round(li_score, 1),
        "Sustainability Potential": round(sp_score, 1),
    }

    pillar_details = {
        "Natural Capital": {
            "Species (GBIF unique)": gbif_unique,
            "Observations (iNat)": inat_total,
            "Protected areas": protected_count,
            "Kingdom diversity": kingdom_diversity,
        },
        "Environmental Quality": {
            "Soil pH": round(ph_val, 2) if ph_val else "N/A",
            "Organic carbon (g/kg)": round(soc_val, 2),
            "Water features": water_count,
            "Industrial zones": industrial_count,
        },
        "Climate Resilience": {
            "Avg temperature (C)": round(avg_temp, 1),
            "Wind speed (km/h)": round(wind_speed, 1),
            "Weekly precip (mm)": round(precip_weekly, 1),
            "Precip adequacy": round(precip_adequacy, 1),
        },
        "Land Integrity": {
            "Buildings": building_count,
            "Road segments": road_count,
            "Erosion risk": round(erosion_risk, 1),
            "Soil health index": round(soil_health, 1),
        },
        "Sustainability Potential": {
            "Solar potential": round(solar_potential, 1),
            "Wind potential": round(wind_potential, 1),
            "Water resources": round(water_resources, 1),
            "Carbon seq. index": round(carbon_seq, 1),
        },
    }

    # -- Overall ESS (weighted) --------------------------------------------
    ess_score = sum(
        pillar_scores[name] * ESS_PILLARS[name]["weight"]
        for name in ESS_PILLARS
    )
    ess_score = round(max(0.0, min(100.0, ess_score)), 1)

    # Letter grade
    if ess_score >= 90:
        letter_grade = "A+"
    elif ess_score >= 80:
        letter_grade = "A"
    elif ess_score >= 70:
        letter_grade = "B+"
    elif ess_score >= 60:
        letter_grade = "B"
    elif ess_score >= 50:
        letter_grade = "C"
    elif ess_score >= 40:
        letter_grade = "D"
    else:
        letter_grade = "F"

    grade_color = GRADE_COLORS.get(letter_grade, "#8b97b0")

    # Strengths / weaknesses
    sorted_pillars = sorted(pillar_scores.items(), key=lambda x: x[1], reverse=True)
    strengths = [{"pillar": p[0], "score": p[1]} for p in sorted_pillars[:2]]
    weaknesses = [{"pillar": p[0], "score": p[1]} for p in sorted_pillars[-2:]]

    # Recommendations
    recommendations = []
    if pillar_scores["Natural Capital"] < 50:
        recommendations.append(
            "Increase biodiversity monitoring; consider habitat restoration "
            "or establishing protected corridors."
        )
    if pillar_scores["Environmental Quality"] < 50:
        recommendations.append(
            "Address soil degradation and reduce industrial impacts; "
            "invest in water-quality monitoring."
        )
    if pillar_scores["Climate Resilience"] < 50:
        recommendations.append(
            "Develop climate-adaptation infrastructure such as flood barriers, "
            "heat-island mitigation, and drought-resistant landscaping."
        )
    if pillar_scores["Land Integrity"] < 50:
        recommendations.append(
            "Limit further land conversion; implement erosion-control measures "
            "and promote soil regeneration practices."
        )
    if pillar_scores["Sustainability Potential"] < 50:
        recommendations.append(
            "Explore renewable energy deployment (solar/wind); "
            "protect existing water resources and enhance carbon sinks."
        )
    if not recommendations:
        recommendations.append(
            "Location shows strong environmental indicators across all pillars. "
            "Continue monitoring to maintain sustainability levels."
        )

    return {
        "ess_score": ess_score,
        "letter_grade": letter_grade,
        "grade_color": grade_color,
        "pillar_scores": pillar_scores,
        "pillar_details": pillar_details,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
    }


# ---------------------------------------------------------------------------
# RENDER TAB
# ---------------------------------------------------------------------------

def render_environmental_score_tab():
    """Render the Environmental Sustainability Score tab."""

    st.markdown(
        '<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);'
        "border:1px solid #2a3550;border-radius:14px;padding:22px 28px;"
        'margin-bottom:18px;">'
        '<h4 style="color:#22c55e;margin:0 0 4px 0;">Environmental Score AI</h4>'
        '<p style="color:#8b97b0;margin:0;font-size:13px;">'
        "Comprehensive Environmental Sustainability Score (ESS) &mdash; "
        "a multi-pillar rating for any geographic location.</p></div>",
        unsafe_allow_html=True,
    )

    # -- Location selector -------------------------------------------------
    c1, c2, c3 = st.columns([1.4, 1, 1])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="ess_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    with c2:
        lat = st.number_input(
            "Latitude",
            min_value=-90.0,
            max_value=90.0,
            value=p.get("lat", 41.90) if p else 41.90,
            format="%.5f",
            key="ess_lat",
        )
    with c3:
        lon = st.number_input(
            "Longitude",
            min_value=-180.0,
            max_value=180.0,
            value=p.get("lon", 12.50) if p else 12.50,
            format="%.5f",
            key="ess_lon",
        )

    run = st.button(
        "Compute ESS Rating",
        type="primary",
        key="ess_run",
        use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Compute ESS Rating** to generate "
            "the Environmental Sustainability Score."
        )
        return

    # -- Compute -----------------------------------------------------------
    with st.spinner("Fetching data and computing ESS rating..."):
        result = compute_environmental_score(lat, lon)

    ess = result["ess_score"]
    grade = result["letter_grade"]
    g_color = result["grade_color"]
    pillars = result["pillar_scores"]
    details = result["pillar_details"]
    strengths = result["strengths"]
    weaknesses = result["weaknesses"]
    recs = result["recommendations"]

    # -- Classification label ----------------------------------------------
    if ess >= 80:
        classification = "Excellent"
    elif ess >= 60:
        classification = "Good"
    elif ess >= 40:
        classification = "Moderate"
    else:
        classification = "Poor"

    # =====================================================================
    # 1. BIG ESS HEADER
    # =====================================================================
    st.markdown(
        f'<div style="background:#1a1a2e;border:2px solid {g_color};'
        f"border-radius:16px;padding:30px;text-align:center;"
        f'margin:18px 0 24px 0;">'
        f'<div style="font-size:82px;font-weight:900;color:{g_color};'
        f'line-height:1;">{html_module.escape(grade)}</div>'
        f'<div style="font-size:32px;color:#e8ecf4;margin-top:6px;">'
        f"{ess:.1f} / 100</div>"
        f'<div style="font-size:15px;color:#8b97b0;margin-top:4px;">'
        f"Environmental Sustainability Score &mdash; "
        f'<span style="color:{g_color};font-weight:600;">'
        f"{html_module.escape(classification)}</span></div></div>",
        unsafe_allow_html=True,
    )

    # =====================================================================
    # 2. PILLAR RADAR CHART
    # =====================================================================
    st.markdown("### Pillar Radar Profile")

    pillar_names = list(pillars.keys())
    pillar_values = [pillars[n] for n in pillar_names]
    pillar_colors = [ESS_PILLARS[n]["color"] for n in pillar_names]

    radar_fig = go.Figure()
    radar_fig.add_trace(go.Scatterpolar(
        r=pillar_values + [pillar_values[0]],
        theta=pillar_names + [pillar_names[0]],
        fill="toself",
        fillcolor="rgba(34,197,94,0.15)",
        line=dict(color="#22c55e", width=2),
        marker=dict(size=7, color=pillar_colors + [pillar_colors[0]]),
        name="ESS Pillars",
    ))
    radar_fig.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#2a3550", linecolor="#2a3550",
                tickfont=dict(color="#8b97b0", size=10),
            ),
            angularaxis=dict(
                gridcolor="#2a3550", linecolor="#2a3550",
                tickfont=dict(color="#e8ecf4", size=12),
            ),
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=420,
    )
    st.plotly_chart(radar_fig, use_container_width=True, key="envsco_pchart1")

    # =====================================================================
    # 3. PILLAR CARDS
    # =====================================================================
    st.markdown("### Pillar Breakdown")

    for pname in pillar_names:
        p_score = pillars[pname]
        p_meta = ESS_PILLARS[pname]
        p_color = p_meta["color"]
        p_detail = details.get(pname, {})

        metrics_html = ""
        for k, v in p_detail.items():
            safe_k = html_module.escape(str(k))
            safe_v = html_module.escape(str(v))
            metrics_html += (
                f'<span style="color:#8b97b0;font-size:12px;margin-right:16px;">'
                f"{safe_k}: "
                f'<b style="color:#e8ecf4;">{safe_v}</b></span>'
            )

        bar_pct = max(0.0, min(p_score, 100.0))
        st.markdown(
            f'<div style="background:#1a1a2e;border:1px solid #2a3550;'
            f"border-left:4px solid {p_color};border-radius:10px;"
            f'padding:14px 18px;margin-bottom:10px;">'
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;">'
            f'<span style="color:{p_color};font-weight:700;font-size:15px;">'
            f"{html_module.escape(pname)}</span>"
            f'<span style="color:#e8ecf4;font-weight:700;font-size:18px;">'
            f"{p_score:.1f}</span></div>"
            f'<div style="background:#0f172a;border-radius:6px;height:10px;'
            f'margin:8px 0;overflow:hidden;">'
            f'<div style="width:{bar_pct:.1f}%;background:{p_color};'
            f'height:100%;border-radius:6px;transition:width 0.6s;"></div>'
            f"</div>"
            f'<div style="margin-top:6px;">{metrics_html}</div></div>',
            unsafe_allow_html=True,
        )

    # =====================================================================
    # 4. STRENGTHS & WEAKNESSES
    # =====================================================================
    st.markdown("### Strengths & Weaknesses")
    sw_left, sw_right = st.columns(2)

    with sw_left:
        st.markdown(
            '<div style="background:#1a1a2e;border:1px solid #22c55e;'
            'border-radius:12px;padding:16px;">'
            '<h5 style="color:#22c55e;margin:0 0 10px 0;">Strengths</h5>',
            unsafe_allow_html=True,
        )
        for s in strengths:
            st.markdown(
                f'<div style="color:#e8ecf4;font-size:13px;margin:6px 0;">'
                f'<span style="color:#22c55e;margin-right:6px;">&#10003;</span>'
                f'{html_module.escape(s["pillar"])} '
                f'<span style="color:#22c55e;font-weight:700;">'
                f'({s["score"]:.1f})</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with sw_right:
        st.markdown(
            '<div style="background:#1a1a2e;border:1px solid #ef4444;'
            'border-radius:12px;padding:16px;">'
            '<h5 style="color:#ef4444;margin:0 0 10px 0;">Weaknesses</h5>',
            unsafe_allow_html=True,
        )
        for w in weaknesses:
            st.markdown(
                f'<div style="color:#e8ecf4;font-size:13px;margin:6px 0;">'
                f'<span style="color:#ef4444;margin-right:6px;">&#9888;</span>'
                f'{html_module.escape(w["pillar"])} '
                f'<span style="color:#ef4444;font-weight:700;">'
                f'({w["score"]:.1f})</span></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # =====================================================================
    # 5. HORIZONTAL STACKED BAR - PILLAR CONTRIBUTION
    # =====================================================================
    st.markdown("### Pillar Contribution to Overall Score")

    contributions = {
        name: round(pillars[name] * ESS_PILLARS[name]["weight"], 2)
        for name in pillar_names
    }

    bar_fig = go.Figure()
    for pname in pillar_names:
        bar_fig.add_trace(go.Bar(
            x=[contributions[pname]],
            y=["ESS"],
            orientation="h",
            name=pname,
            marker_color=ESS_PILLARS[pname]["color"],
            text=[f"{pname}: {contributions[pname]:.1f}"],
            textposition="inside",
            textfont=dict(color="#ffffff", size=11),
            hovertemplate=(
                f"{pname}<br>"
                f"Pillar score: {pillars[pname]:.1f}<br>"
                f"Weight: {ESS_PILLARS[pname]['weight']:.0%}<br>"
                f"Contribution: {contributions[pname]:.1f}"
                "<extra></extra>"
            ),
        ))
    bar_fig.update_layout(
        barmode="stack",
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        xaxis=dict(
            range=[0, 100], gridcolor="#2a3550", linecolor="#2a3550",
            tickfont=dict(color="#8b97b0"), title="Score points",
            title_font=dict(color="#8b97b0"),
        ),
        yaxis=dict(
            showticklabels=False, gridcolor="#2a3550", linecolor="#2a3550",
        ),
        legend=dict(
            font=dict(color="#e8ecf4", size=11),
            bgcolor="rgba(26,26,46,0.8)",
            bordercolor="#2a3550", borderwidth=1,
            orientation="h", yanchor="bottom", y=-0.35, x=0.5, xanchor="center",
        ),
        height=180,
        margin=dict(l=20, r=20, t=10, b=80),
    )
    st.plotly_chart(bar_fig, use_container_width=True, key="envsco_pchart2")

    # =====================================================================
    # 6. RECOMMENDATIONS
    # =====================================================================
    st.markdown("### Recommendations")

    recs_html = ""
    for idx, rec in enumerate(recs, 1):
        safe_rec = html_module.escape(rec)
        recs_html += (
            f'<div style="display:flex;align-items:flex-start;margin:10px 0;">'
            f'<span style="background:#22c55e;color:#1a1a2e;font-weight:700;'
            f"min-width:26px;height:26px;border-radius:50%;display:flex;"
            f"align-items:center;justify-content:center;font-size:13px;"
            f'margin-right:12px;flex-shrink:0;">{idx}</span>'
            f'<span style="color:#e8ecf4;font-size:13px;line-height:1.5;">'
            f"{safe_rec}</span></div>"
        )

    st.markdown(
        f'<div style="background:#1a1a2e;border:1px solid #2a3550;'
        f'border-radius:12px;padding:18px 22px;">{recs_html}</div>',
        unsafe_allow_html=True,
    )
