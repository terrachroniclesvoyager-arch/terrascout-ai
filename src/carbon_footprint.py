"""
Carbon & Emissions Intelligence AI module for TerraScout AI.
Estimates carbon footprint and emissions profile of a geographic area by
combining soil organic carbon data, land-use / infrastructure density,
water-feature sinks, protected-area coverage, and elevation context.

Data sources (all free, no API key):
  - ISRIC SoilGrids   (soil organic carbon, SOC)
  - Open-Meteo        (weather / climate context)
  - Overpass API       (water features, land use, infrastructure, protected areas)
  - Open-Elevation     (terrain / elevation grid)
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
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
)


def _hex_rgba(hc, a=1.0):
    """Convert #RRGGBB + alpha float to rgba() for Plotly compatibility."""
    h = hc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CARBON METRIC DEFINITIONS
# ---------------------------------------------------------------------------

CARBON_METRICS = {
    "soil_carbon":          {"name": "Soil Carbon Storage",    "unit": "tC/ha",  "color": "#10b981"},
    "vegetation_carbon":    {"name": "Vegetation Carbon",      "unit": "proxy",  "color": "#22c55e"},
    "emission_intensity":   {"name": "Emission Intensity",     "unit": "0-100",  "color": "#ef4444"},
    "sink_capacity":        {"name": "Carbon Sink Capacity",   "unit": "0-100",  "color": "#06b6d4"},
    "sequestration_pot":    {"name": "Sequestration Potential", "unit": "0-100",  "color": "#8b5cf6"},
    "net_balance":          {"name": "Net Balance Score",      "unit": "0-100",  "color": "#f59e0b"},
}

# Emission factors (arbitrary normalised units per detected element)
_EMISSION_FACTOR_BUILDING   = 0.35
_EMISSION_FACTOR_ROAD       = 0.20
_EMISSION_FACTOR_INDUSTRIAL = 2.50

# Sink weight multipliers
_SINK_FOREST_WEIGHT    = 1.0
_SINK_WETLAND_WEIGHT   = 1.5
_SINK_PROTECTED_WEIGHT = 0.8


# ---------------------------------------------------------------------------
# CACHED COMPUTATION
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def compute_carbon_profile(lat: float, lon: float) -> dict:
    """Compute a full carbon-footprint profile for *lat, lon*."""

    # -- Fetch all upstream data sources --------------------------------
    soil      = fetch_soil_data(lat, lon)              or {}
    weather   = fetch_weather_data(lat, lon)            or {}
    water     = fetch_water_features(lat, lon)          or {}
    elevation = fetch_elevation_grid(lat, lon)          or {}
    infra     = fetch_landuse_infrastructure(lat, lon)  or {}
    protected = fetch_protected_areas(lat, lon)         or {}

    # ================================================================
    # 1.  SOIL CARBON STORAGE  (tC/ha estimate)
    # ================================================================
    props = (soil if isinstance(soil, dict) else {}).get("properties", {})

    def _sv(name, div=10):
        layers = props.get("layers", [])
        for layer in (layers if isinstance(layers, list) else []):
            if isinstance(layer, dict) and layer.get("name") == name:
                depths = layer.get("depths", [])
                if depths:
                    return (depths[0].get("values", {}).get("mean") or 0) / div
        return None

    soc_gkg  = _sv("soc") or 10.0       # g/kg  (topsoil 0-5 cm)
    clay_pct = _sv("clay") or 20.0       # %
    nitrogen = _sv("nitrogen", 100) or 1.0

    # Rough conversion: SOC g/kg  ->  tC/ha  (assume bulk density ~1.3, depth 30 cm)
    bulk_density = 1.3
    depth_m      = 0.30
    carbon_storage_tCha = round(soc_gkg * bulk_density * depth_m * 10, 1)
    # depth factor:  clay-rich soils store more
    clay_bonus = clay_pct * 0.15
    carbon_storage_tCha = round(carbon_storage_tCha + clay_bonus, 1)

    # Soil carbon metric  (0-100 proxy where 100 = very high storage)
    soil_carbon_score = min(100, round(carbon_storage_tCha * 1.2))

    # ================================================================
    # 2.  VEGETATION CARBON  (proxy from SOC + land-cover context)
    # ================================================================
    elements = (infra if isinstance(infra, dict) else {}).get("elements", [])
    forest_count = sum(
        1 for e in elements
        if e.get("tags", {}).get("landuse") in ("forest", "meadow", "farmland")
        or e.get("tags", {}).get("natural") in ("wood", "scrub", "grassland")
    )
    veg_carbon_score = min(100, round(soc_gkg * 1.5 + forest_count * 6 + nitrogen * 8))

    # ================================================================
    # 3.  EMISSION SOURCES
    # ================================================================
    buildings  = sum(1 for e in elements if e.get("tags", {}).get("building"))
    roads      = sum(1 for e in elements if e.get("tags", {}).get("highway"))
    industrial = sum(
        1 for e in elements
        if e.get("tags", {}).get("landuse") in ("industrial", "commercial", "landfill", "quarry")
    )

    em_buildings  = buildings  * _EMISSION_FACTOR_BUILDING
    em_roads      = roads      * _EMISSION_FACTOR_ROAD
    em_industrial = industrial * _EMISSION_FACTOR_INDUSTRIAL
    total_emissions = em_buildings + em_roads + em_industrial

    emission_intensity = min(100, round(total_emissions * 1.5))

    emission_sources = {
        "Buildings":  round(em_buildings, 1),
        "Roads":      round(em_roads, 1),
        "Industrial": round(em_industrial, 1),
        "Total":      round(total_emissions, 1),
    }

    # ================================================================
    # 4.  CARBON SINKS  (forests + wetlands + protected areas)
    # ================================================================
    w_elements = (water if isinstance(water, dict) else {}).get("elements", [])
    wetland_count = sum(
        1 for e in w_elements
        if e.get("tags", {}).get("natural") == "wetland"
    )
    p_elements = (protected if isinstance(protected, dict) else {}).get("elements", [])
    protected_count = len(p_elements)

    sink_forest    = min(40, forest_count   * 4 * _SINK_FOREST_WEIGHT)
    sink_wetland   = min(35, wetland_count  * 8 * _SINK_WETLAND_WEIGHT)
    sink_protected = min(25, protected_count * 6 * _SINK_PROTECTED_WEIGHT)

    sink_capacity_score = min(100, round(sink_forest + sink_wetland + sink_protected))

    sink_details = {
        "Forests / vegetation": round(sink_forest, 1),
        "Wetlands":             round(sink_wetland, 1),
        "Protected areas":      round(sink_protected, 1),
        "Total":                round(sink_forest + sink_wetland + sink_protected, 1),
    }

    # ================================================================
    # 5.  NET CARBON BALANCE
    # ================================================================
    raw_balance = (sink_forest + sink_wetland + sink_protected) - total_emissions
    net_balance = round(raw_balance, 1)  # positive = net sink

    # Score 0-100 (50 = break-even, 100 = strong sink, 0 = heavy emitter)
    net_balance_score = min(100, max(0, round(50 + raw_balance * 1.2)))

    # ================================================================
    # 6.  SEQUESTRATION POTENTIAL
    # ================================================================
    soc_capacity      = max(0, 100 - soil_carbon_score)       # room to grow
    reforest_pot      = max(0, 100 - min(100, forest_count * 10))
    wetland_restore   = max(0, 100 - min(100, wetland_count * 15))
    seq_potential      = round((soc_capacity * 0.4 + reforest_pot * 0.35
                                + wetland_restore * 0.25))

    recommendations = []
    if reforest_pot > 50:
        recommendations.append(
            "Reforestation: Area has significant potential for new forest planting to "
            "increase carbon sequestration."
        )
    if wetland_restore > 60:
        recommendations.append(
            "Wetland restoration: Few wetlands detected; restoring or creating wetlands "
            "could enhance carbon capture and biodiversity."
        )
    if soc_capacity > 40:
        recommendations.append(
            "Soil carbon enrichment: Organic amendments, cover cropping, and reduced "
            "tillage could raise soil organic carbon levels."
        )
    if emission_intensity > 60:
        recommendations.append(
            "Emission reduction: High urbanisation footprint detected; transitioning to "
            "green infrastructure and renewable energy would lower emissions."
        )
    if not recommendations:
        recommendations.append(
            "Area shows a healthy carbon balance. Maintain existing forests and "
            "protected-area coverage to sustain sequestration capacity."
        )

    # ================================================================
    # 7.  BUILD METRICS DICT
    # ================================================================
    metrics = {
        "soil_carbon":        soil_carbon_score,
        "vegetation_carbon":  veg_carbon_score,
        "emission_intensity": emission_intensity,
        "sink_capacity":      sink_capacity_score,
        "sequestration_pot":  seq_potential,
        "net_balance":        net_balance_score,
    }

    # ── Overall class ─────────────────────────────────────────────
    avg = sum(metrics.values()) / len(metrics) if metrics else 0
    # Weight: penalise high emissions more
    weighted_avg = round(avg * 0.6 + net_balance_score * 0.4)

    if weighted_avg >= 70:
        overall_class = "Green"
        overall_color = "#10b981"
    elif weighted_avg >= 45:
        overall_class = "Neutral"
        overall_color = "#f59e0b"
    elif weighted_avg >= 25:
        overall_class = "Warning"
        overall_color = "#f97316"
    else:
        overall_class = "Critical"
        overall_color = "#ef4444"

    return {
        "overall_class":       overall_class,
        "overall_color":       overall_color,
        "metrics":             metrics,
        "carbon_storage_tCha": carbon_storage_tCha,
        "net_balance":         net_balance,
        "emission_sources":    emission_sources,
        "sink_capacity":       sink_details,
        "sequestration_pot":   seq_potential,
        "recommendations":     recommendations,
    }


# ---------------------------------------------------------------------------
# RENDER TAB
# ---------------------------------------------------------------------------

def render_carbon_footprint_tab():
    """Render the Carbon & Emissions Intelligence AI tab."""

    st.markdown("## Carbon & Emissions Intelligence AI")
    st.caption(
        "Estimate the carbon footprint, emission sources, sink capacity, "
        "and sequestration potential of any geographic area."
    )

    # ── Location selector ─────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        preset = st.selectbox(
            "Location preset",
            list(ANALYSIS_PRESETS.keys()),
            key="cf_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    with col2:
        c1, c2 = st.columns(2)
        with c1:
            lat = st.number_input(
                "Lat", -90.0, 90.0,
                p.get("lat", 41.90) if p else 41.90,
                step=0.01, key="cf_lat", format="%.4f",
            )
        with c2:
            lon = st.number_input(
                "Lon", -180.0, 180.0,
                p.get("lon", 12.50) if p else 12.50,
                step=0.01, key="cf_lon", format="%.4f",
            )

    if not st.button("Analyze Carbon Profile", type="primary",
                     use_container_width=True):
        return

    with st.spinner("Analyzing carbon profile..."):
        result = compute_carbon_profile(lat, lon)

    if not result:
        st.error("Carbon analysis failed. Please try again.")
        return

    overall_class = result["overall_class"]
    overall_color = result["overall_color"]
    metrics       = result["metrics"]
    storage       = result["carbon_storage_tCha"]
    net_bal       = result["net_balance"]
    em_sources    = result["emission_sources"]
    sinks         = result["sink_capacity"]
    seq_pot       = result["sequestration_pot"]
    recs          = result["recommendations"]

    # ── Net balance header ────────────────────────────────────────
    bal_color = "#10b981" if net_bal >= 0 else "#ef4444"
    bal_label = "Net Carbon Sink" if net_bal >= 0 else "Net Carbon Emitter"
    sign      = "+" if net_bal >= 0 else ""

    st.markdown(f"""
    <div style="background:linear-gradient(135deg, {overall_color}22, {overall_color}44);
                border-left:5px solid {overall_color}; border-radius:12px;
                padding:25px; margin:10px 0;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <div style="color:#888; font-size:12px;">CARBON PROFILE</div>
                <div style="color:{overall_color}; font-size:36px; font-weight:bold;
                            margin:4px 0;">
                    {overall_class}
                </div>
                <div style="color:{bal_color}; font-size:16px; font-weight:600;">
                    {bal_label}: {sign}{net_bal}
                </div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:56px; font-weight:bold; color:{overall_color};">
                    {metrics['net_balance']}
                </div>
                <div style="color:#888; font-size:14px;">Net Balance /100</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Carbon storage big number ─────────────────────────────────
    st.markdown(f"""
    <div style="background:#1a1a2e; border:1px solid #10b98144;
                border-radius:12px; padding:20px; margin:10px 0;
                text-align:center;">
        <div style="color:#888; font-size:13px;">ESTIMATED SOIL CARBON STORAGE</div>
        <div style="font-size:52px; font-weight:bold; color:#10b981;
                    margin:6px 0;">{storage}
            <span style="font-size:18px; color:#888;">tC/ha</span>
        </div>
        <div style="color:#aaa; font-size:12px;">
            Topsoil (0-30 cm) organic carbon estimate
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 6 metric cards (3 x 2) ────────────────────────────────────
    keys = list(CARBON_METRICS.keys())
    for row_start in range(0, 6, 3):
        cols = st.columns(3)
        for i, col in enumerate(cols):
            idx = row_start + i
            if idx >= len(keys):
                break
            k = keys[idx]
            meta  = CARBON_METRICS[k]
            value = metrics[k]

            if value >= 70:
                val_color = "#10b981"
            elif value >= 40:
                val_color = "#f59e0b"
            else:
                val_color = "#ef4444"

            # For emission_intensity, invert color logic (lower is better)
            if k == "emission_intensity":
                if value <= 30:
                    val_color = "#10b981"
                elif value <= 60:
                    val_color = "#f59e0b"
                else:
                    val_color = "#ef4444"

            with col:
                st.markdown(f"""
                <div style="background:#1a1a2e; border:1px solid {meta['color']}44;
                            border-radius:10px; padding:15px; margin:5px 0;
                            min-height:120px;">
                    <div style="color:{meta['color']}; font-weight:bold;
                                font-size:13px;">{meta['name']}</div>
                    <div style="font-size:32px; font-weight:bold; color:{val_color};
                                margin:4px 0;">
                        {value}<span style="font-size:12px; color:#888;">
                        {' ' + meta['unit']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ── Pie chart: sources vs sinks ───────────────────────────────
    st.markdown("### Sources vs Sinks Breakdown")

    source_total = em_sources.get("Total", 0)
    sink_total   = sinks.get("Total", 0)
    pie_labels   = ["Emission Sources", "Carbon Sinks"]
    pie_values   = [max(0.1, source_total), max(0.1, sink_total)]
    pie_colors   = ["#ef4444", "#10b981"]

    fig_pie = go.Figure(data=[go.Pie(
        labels=pie_labels,
        values=pie_values,
        hole=0.45,
        marker=dict(colors=pie_colors),
        textinfo="label+percent",
        textfont=dict(color="#ffffff"),
    )])
    fig_pie.update_layout(
        height=340,
        margin=dict(t=20, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(font=dict(color="#cccccc")),
    )
    st.plotly_chart(fig_pie, use_container_width=True, key="carfoo_pchart1")

    # ── Horizontal bars: emission sources ─────────────────────────
    st.markdown("### Emission Sources Comparison")

    bar_labels = [k for k in em_sources if k != "Total"]
    bar_values = [em_sources[k] for k in bar_labels]
    bar_colors = ["#ef4444", "#f97316", "#dc2626"]

    if bar_values:
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            y=bar_labels,
            x=bar_values,
            orientation="h",
            marker=dict(color=bar_colors[:len(bar_labels)]),
            text=[f"{v:.1f}" for v in bar_values],
            textposition="outside",
            textfont=dict(color="#cccccc"),
        ))
        fig_bar.update_layout(
            height=250,
            margin=dict(t=10, b=10, l=10, r=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Emission units", color="#aaa", gridcolor="#333"),
            yaxis=dict(color="#ccc"),
        )
        st.plotly_chart(fig_bar, use_container_width=True, key="carfoo_pchart2")

    # ── Radar chart of 6 metrics ──────────────────────────────────
    st.markdown("### Carbon Metrics Radar")

    radar_names  = [CARBON_METRICS[k]["name"] for k in keys]
    radar_values = [metrics[k] for k in keys]

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=radar_values + [radar_values[0]],
        theta=radar_names + [radar_names[0]],
        fill="toself",
        fillcolor=_hex_rgba(overall_color, 0.13),
        line=dict(color=overall_color, width=2),
        name="Carbon Metrics",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], color="#666"),
            angularaxis=dict(color="#ccc"),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
        height=420,
        margin=dict(t=30, b=30, l=80, r=80),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_radar, use_container_width=True, key="carfoo_pchart3")

    # ── Sequestration recommendations ─────────────────────────────
    st.markdown("### Sequestration Recommendations")
    st.markdown(f"""
    <div style="background:#1a1a2e; border:1px solid #8b5cf644;
                border-radius:12px; padding:20px; margin:10px 0;">
        <div style="color:#8b5cf6; font-size:14px; font-weight:bold;
                    margin-bottom:12px;">
            Sequestration Potential Score:
            <span style="font-size:22px;">{seq_pot}</span>
            <span style="font-size:12px; color:#888;">/100</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    for rec in recs:
        title, _, body = rec.partition(":")
        body = body.strip() if body else rec
        st.markdown(f"""
        <div style="background:#1a1a2e; border-left:3px solid #10b981;
                    border-radius:8px; padding:14px 18px; margin:6px 0;">
            <div style="color:#10b981; font-weight:bold; font-size:13px;">
                {title}
            </div>
            <div style="color:#ccc; font-size:12px; margin-top:4px;">
                {body}
            </div>
        </div>
        """, unsafe_allow_html=True)
