"""
Intelligence Briefing - Unified intelligence briefing module for TerraScout AI.
Combines unified_intelligence + decision_matrix + smart_insights into a single
comprehensive briefing with executive summary, all domain analyses, 8 decision
scenarios, cross-correlations, SWOT, and aggregated charts.
Ops-center palette + Math Transparency section.

Entry point: render_intelligence_briefing_tab()
"""

import html as html_module
import math
from datetime import datetime, timezone

import streamlit as st
try:
    import plotly.graph_objects as go
except ImportError:
    go = None

from src.location_context import get_short_name
from src.location_aware import render_module_location_input
from src.data_hub import get_hub_data
from src.unified_intelligence import (
    INTELLIGENCE_DOMAINS,
    _classify_score,
    _compute_overall_score,
)
from src.decision_matrix import (
    DECISION_SCENARIOS,
    VERDICT_GO,
    VERDICT_CAUTION,
    VERDICT_COLORS,
    _collect_location_data,
    _evaluate_scenario,
)

# Ops-center palette constants
OPS_BG = "#050510"
OPS_PANEL = "#0a0a18"
OPS_GRID = "#0d1225"
OPS_CYAN = "#00f0ff"
OPS_GREEN = "#00ff88"
OPS_AMBER = "#ffaa00"
OPS_RED = "#ff3344"
OPS_BLUE = "#4488ff"
OPS_PURPLE = "#aa55ff"
OPS_TEXT = "#e0e8f0"
OPS_TEXT_DIM = "#5a7090"

_DOMAIN_OPS_COLORS = {
    "habitability": OPS_BLUE,
    "agriculture": OPS_GREEN,
    "ecology": "#00cc66",
    "hazard_safety": OPS_RED,
    "water_resources": OPS_CYAN,
    "infrastructure": OPS_PURPLE,
    "climate_comfort": OPS_AMBER,
    "economic_potential": "#ff66aa",
    "air_environment": "#6688ff",
    "geological_stability": "#cc88ff",
}


# ---------------------------------------------------------------------------
# POLAR AREA CHART (replaces radar)
# ---------------------------------------------------------------------------

def _build_polar_area(scores):
    """Build a Barpolar chart for the briefing."""
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())
    names = [INTELLIGENCE_DOMAINS[k]["name"] for k in domain_keys]
    vals = [scores.get(k, 0) for k in domain_keys]
    colors = [_DOMAIN_OPS_COLORS.get(k, OPS_CYAN) for k in domain_keys]

    fig = go.Figure()
    fig.add_trace(go.Barpolar(
        r=vals, theta=names,
        marker_color=colors,
        marker_line_color=OPS_BG, marker_line_width=1,
        opacity=0.85,
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=OPS_BG,
            radialaxis=dict(visible=True, range=[0, 100],
                            tickfont=dict(color=OPS_TEXT_DIM, size=9), gridcolor=OPS_GRID),
            angularaxis=dict(tickfont=dict(color=OPS_TEXT, size=10), gridcolor=OPS_GRID),
        ),
        paper_bgcolor=OPS_BG, plot_bgcolor=OPS_BG,
        font=dict(color=OPS_TEXT), showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30), height=420,
    )
    return fig


# ---------------------------------------------------------------------------
# DOMAIN BAR CHART (ops palette)
# ---------------------------------------------------------------------------

def _build_domain_bar_chart(scores):
    """Horizontal bar chart with ops-center colors."""
    sorted_domains = sorted(scores.items(), key=lambda x: x[1])
    names = [INTELLIGENCE_DOMAINS[k]["name"] for k, _ in sorted_domains]
    vals = [v for _, v in sorted_domains]
    bar_colors = [_DOMAIN_OPS_COLORS.get(k, OPS_CYAN) for k, _ in sorted_domains]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=vals, orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{v:.0f}" for v in vals], textposition="outside",
        textfont=dict(color=OPS_TEXT, size=12, family="JetBrains Mono, monospace"),
    ))
    fig.update_layout(
        paper_bgcolor=OPS_BG, plot_bgcolor=OPS_BG,
        font=dict(color=OPS_TEXT),
        xaxis=dict(range=[0, 110], gridcolor=OPS_GRID, tickfont=dict(color=OPS_TEXT_DIM)),
        yaxis=dict(tickfont=dict(color=OPS_TEXT, size=12)),
        margin=dict(l=160, r=40, t=20, b=30), height=380, showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# EXECUTIVE SUMMARY GENERATOR
# ---------------------------------------------------------------------------

def _generate_executive_summary(scores, details, insights, overall, overall_label, confidence):
    """Generate an algorithmic executive summary paragraph."""
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_strengths = [INTELLIGENCE_DOMAINS[k]["name"] for k, v in sorted_scores[:3] if v >= 50]
    top_weaknesses = [INTELLIGENCE_DOMAINS[k]["name"] for k, v in sorted_scores[-3:] if v < 50]
    opportunities = sum(1 for i in insights if i["type"] in ("opportunity", "synergy"))
    threats = sum(1 for i in insights if i["type"] in ("threat", "warning"))

    parts = [
        f"This location receives an overall intelligence score of **{overall:.0f}/100** "
        f"({overall_label}) with a data confidence of **{int(confidence * 100)}%** "
        f"({sum(1 for s in ['elevation','soil','weather','inat','water','quakes','geology','infra','air_quality','protected'] if details.get(s + '_count', 1))} sources active).",
    ]

    if top_strengths:
        parts.append(f"Key strengths include {', '.join(top_strengths)}.")
    if top_weaknesses:
        parts.append(f"Areas of concern: {', '.join(top_weaknesses)}.")
    if opportunities > 0:
        parts.append(f"{opportunities} opportunities/synergies detected.")
    if threats > 0:
        parts.append(f"{threats} threats/warnings identified.")

    elev = details.get("center_elev", 0)
    temp = details.get("temp_now", 0)
    parts.append(
        f"Elevation: {elev:.0f}m, current temperature: {temp:.1f}C, "
        f"estimated annual precipitation: {details.get('annual_precip_est', 0):.0f}mm."
    )
    return " ".join(parts)


# ---------------------------------------------------------------------------
# DOMAIN CORRELATION HEATMAP (ops palette)
# ---------------------------------------------------------------------------

def _build_correlation_heatmap(scores):
    """Build a 10x10 correlation heatmap with ops-center colorscale."""
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())
    domain_names = [INTELLIGENCE_DOMAINS[k]["name"] for k in domain_keys]
    n = len(domain_keys)
    values = [scores.get(k, 50) for k in domain_keys]
    mean_val = sum(values) / max(len(values), 1)

    matrix = []
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(1.0)
            else:
                di = values[i] - mean_val
                dj = values[j] - mean_val
                max_dev = max(abs(di), abs(dj), 1.0)
                corr = (di * dj) / (max_dev ** 2)
                row.append(round(corr, 2))
        matrix.append(row)

    # Custom ops-center colorscale
    colorscale = [
        [0, OPS_RED],
        [0.5, OPS_GRID],
        [1, OPS_GREEN],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=matrix, x=domain_names, y=domain_names,
        colorscale=colorscale, zmid=0, zmin=-1, zmax=1,
        text=[[f"{v:.2f}" for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont={"size": 9, "color": OPS_TEXT},
    ))
    fig.update_layout(
        paper_bgcolor=OPS_BG, plot_bgcolor=OPS_BG,
        font={"color": OPS_TEXT},
        xaxis={"tickfont": {"size": 9, "color": OPS_TEXT_DIM}, "tickangle": 45},
        yaxis={"tickfont": {"size": 9, "color": OPS_TEXT_DIM}},
        height=450, margin=dict(l=120, r=20, t=20, b=120),
    )
    return fig


# ---------------------------------------------------------------------------
# SCENARIO COMPARISON CHART (ops colors)
# ---------------------------------------------------------------------------

def _build_scenario_comparison(results):
    """Grouped bar chart comparing 8 scenario overall scores with ops colors."""
    names = [r["name"] for r in results]
    overall_scores = [r["overall_score"] for r in results]

    # Map verdict to ops colors
    ops_verdict_colors = {
        "GO": OPS_GREEN,
        "CAUTION": OPS_AMBER,
        "NO-GO": OPS_RED,
    }
    colors = [ops_verdict_colors.get(r["verdict"], OPS_TEXT_DIM) for r in results]

    fig = go.Figure(go.Bar(
        x=names, y=overall_scores,
        marker_color=colors,
        text=[f"{s:.0f}" for s in overall_scores], textposition="outside",
        textfont={"color": OPS_TEXT, "size": 11, "family": "JetBrains Mono, monospace"},
    ))
    fig.update_layout(
        paper_bgcolor=OPS_BG, plot_bgcolor=OPS_BG,
        font={"color": OPS_TEXT},
        xaxis={"tickfont": {"color": OPS_TEXT_DIM, "size": 10}, "tickangle": 30},
        yaxis={"range": [0, 110], "gridcolor": OPS_GRID, "tickfont": {"color": OPS_TEXT_DIM}},
        height=350, margin=dict(l=40, r=20, t=20, b=80), showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# ENVIRONMENT STACKED BAR (ops palette)
# ---------------------------------------------------------------------------

def _build_environment_stacked(scores):
    """Stacked bar chart with ops-center colors."""
    categories = ["Agriculture & Soil", "Water", "Air", "Ecology"]
    values = [
        scores.get("agriculture", 0),
        scores.get("water_resources", 0),
        scores.get("air_environment", 0),
        scores.get("ecology", 0),
    ]
    colors = [OPS_GREEN, OPS_CYAN, OPS_BLUE, "#00cc66"]

    fig = go.Figure()
    for cat, val, color in zip(categories, values, colors):
        fig.add_trace(go.Bar(
            x=[cat], y=[val], name=cat, marker_color=color,
            text=[f"{val:.0f}"], textposition="auto",
            textfont={"color": OPS_TEXT},
        ))
    fig.update_layout(
        paper_bgcolor=OPS_BG, plot_bgcolor=OPS_BG,
        font={"color": OPS_TEXT},
        yaxis={"range": [0, 110], "gridcolor": OPS_GRID, "title": "Score"},
        height=300, margin=dict(l=40, r=20, t=20, b=40), showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# MAIN RENDER FUNCTION
# ---------------------------------------------------------------------------

def render_intelligence_briefing_tab():
    """Render the Intelligence Briefing tab UI with ops-center style."""

    st.markdown(
        f'<div class="tab-header" style="border-left:4px solid {OPS_PURPLE};'
        f'background:rgba(170,85,255,0.06);padding:18px 24px;border-radius:12px;'
        f'margin-bottom:18px;">'
        f"<h4 style='color:{OPS_TEXT};margin:0;font-family:JetBrains Mono,monospace;'>"
        f"Intelligence Briefing</h4>"
        f"<p style='color:{OPS_TEXT_DIM};margin:6px 0 0 0;font-family:JetBrains Mono,monospace;"
        f"font-size:0.82rem;'>Unified briefing combining "
        f"all intelligence domains, 8 decision scenarios, cross-correlations, "
        f"SWOT analysis, and actionable recommendations.</p>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # ---- Location input ----
    lat, lon = render_module_location_input("ib", 41.90, 12.50)

    run = st.button(
        "Generate Intelligence Briefing",
        type="primary", key="ib_run", use_container_width=True,
    )

    if not run:
        st.markdown(
            f'<div class="ops-terminal">'
            f'<span class="ops-term-label">AWAITING COMMAND</span>'
            f'Set a location and click Generate Intelligence Briefing.'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    # ================================================================
    # DATA COLLECTION
    # ================================================================
    progress = st.progress(0, text="Collecting intelligence data...")
    progress.progress(10, text="Fetching from 12+ sources...")

    hub = get_hub_data(lat, lon)
    scores = hub.get("scores", {})
    details = hub.get("details", {})
    insights = hub.get("insights", [])
    swot = hub.get("swot", {})
    recommendations = hub.get("recommendations", [])
    overall = hub.get("overall_score", 50)
    overall_label = hub.get("overall_label", "Moderate")
    overall_color = hub.get("overall_color", "#fbbf24")
    _conf_raw = hub.get("confidence", 0)
    confidence = float(_conf_raw.get("overall", 0)) if isinstance(_conf_raw, dict) else float(_conf_raw or 0)

    progress.progress(50, text="Evaluating 8 decision scenarios...")

    raw_dm = _collect_location_data(lat, lon)
    scenario_results = []
    scenario_keys = list(DECISION_SCENARIOS.keys())
    for i, sk in enumerate(scenario_keys):
        progress.progress(
            50 + int((i + 1) / len(scenario_keys) * 40),
            text=f"Evaluating: {DECISION_SCENARIOS[sk]['name']}...",
        )
        result = _evaluate_scenario(
            sk, lat, lon,
            raw_dm["soil"], raw_dm["weather"], raw_dm["water"],
            raw_dm["elevation"], raw_dm["infrastructure"],
            raw_dm["protected"], raw_dm["species"], raw_dm["earthquakes"],
        )
        scenario_results.append(result)

    progress.progress(100, text="Briefing complete!")

    # ================================================================
    # SECTION 1: EXECUTIVE SUMMARY
    # ================================================================
    st.markdown(
        f'<div class="ops-section-header">'
        f'<span class="ops-section-label">BRIEF-01</span>'
        f'<span class="ops-section-title">Executive Summary</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    summary = _generate_executive_summary(scores, details, insights, overall, overall_label, confidence)
    loc_name = get_short_name() or f"{lat:.5f}, {lon:.5f}"
    safe_loc_name = html_module.escape(loc_name)

    # Score badge class
    if overall >= 65:
        badge_class = "ops-badge-green"
    elif overall >= 40:
        badge_class = "ops-badge-amber"
    else:
        badge_class = "ops-badge-red"

    st.markdown(
        f'<div style="background:{OPS_BG};border:1px solid {OPS_GRID};'
        f'border-radius:10px;padding:18px;margin:8px 0;">'
        f'<div style="display:flex;align-items:center;gap:16px;margin-bottom:12px;">'
        f'<div class="ops-badge ops-badge-lg {badge_class}">{overall:.0f}</div>'
        f'<div><h4 style="color:{OPS_TEXT};margin:0;font-family:JetBrains Mono,monospace;">'
        f'{safe_loc_name}</h4>'
        f'<p style="color:{OPS_CYAN};margin:2px 0 0;font-size:0.78rem;'
        f'font-family:JetBrains Mono,monospace;">{lat:.5f}, {lon:.5f}</p>'
        f'<p style="color:{overall_color};margin:4px 0 0;font-weight:600;'
        f'font-family:JetBrains Mono,monospace;">'
        f'{html_module.escape(overall_label)} | CONF: {int(confidence * 100)}%</p></div></div>'
        f'<p style="color:{OPS_TEXT};font-size:0.85rem;line-height:1.6;margin:0;">'
        f'{summary}</p></div>',
        unsafe_allow_html=True,
    )

    # ================================================================
    # SECTION 2: 12 KEY METRICS DASHBOARD
    # ================================================================
    st.markdown(
        f'<div class="ops-section-header">'
        f'<span class="ops-section-label">BRIEF-02</span>'
        f'<span class="ops-section-title">Key Metrics Dashboard</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    mc = st.columns(4)
    metrics = [
        ("ELEVATION", f"{details.get('center_elev', 0):.0f} m"),
        ("TEMPERATURE", f"{details.get('temp_now', 0):.1f}\u00b0C"),
        ("HUMIDITY", f"{details.get('humidity', 0):.0f}%"),
        ("ANNUAL PRECIP", f"{details.get('annual_precip_est', 0):.0f} mm"),
        ("WIND SPEED", f"{details.get('wind_speed', 0):.1f} km/h"),
        ("AQI", f"{details.get('aqi', 0)}"),
        ("PM2.5", f"{details.get('pm25', 0):.1f}"),
        ("SPECIES OBS", f"{details.get('total_species_obs', 0)}"),
        ("BUILDINGS", f"{details.get('building_count', 0)}"),
        ("ROADS", f"{details.get('road_count', 0)}"),
        ("EARTHQUAKES", f"{details.get('eq_count', 0)}"),
        ("MAX MAGNITUDE", f"{details.get('max_mag', 0):.1f}"),
    ]
    for i, (label, value) in enumerate(metrics):
        with mc[i % 4]:
            st.markdown(
                f'<div class="ops-metric">'
                f'<div class="ops-metric-value" style="font-size:1.3rem;">{value}</div>'
                f'<div class="ops-metric-label">{label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ================================================================
    # SECTION 3: 10 DOMAIN ANALYSIS
    # ================================================================
    st.markdown(
        f'<div class="ops-section-header">'
        f'<span class="ops-section-label">BRIEF-03</span>'
        f'<span class="ops-section-title">10-Domain Intelligence Analysis</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    col_r, col_b = st.columns(2)
    with col_r:
        st.plotly_chart(
            _build_polar_area(scores),
            key="ib_polar", use_container_width=True,
        )
    with col_b:
        st.plotly_chart(
            _build_domain_bar_chart(scores),
            key="ib_bars", use_container_width=True,
        )

    # Domain detail cards (2 rows of 5)
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())
    for row_start in range(0, 10, 5):
        cols = st.columns(5)
        for idx, key in enumerate(domain_keys[row_start:row_start + 5]):
            meta = INTELLIGENCE_DOMAINS[key]
            sc = scores.get(key, 0)
            sc_label, sc_color = _classify_score(sc)
            dom_color = _DOMAIN_OPS_COLORS.get(key, OPS_CYAN)
            with cols[idx]:
                st.markdown(
                    f'<div style="background:{OPS_BG};border:1px solid {dom_color}33;'
                    f'border-radius:8px;padding:10px;text-align:center;'
                    f'font-family:JetBrains Mono,monospace;">'
                    f'<div style="font-size:20px;">{meta["icon"]}</div>'
                    f'<div style="color:{OPS_TEXT};font-size:0.72rem;font-weight:600;">'
                    f'{html_module.escape(meta["name"])}</div>'
                    f'<div style="font-size:1.3rem;font-weight:bold;color:{dom_color};">'
                    f'{sc:.0f}</div>'
                    f'<div style="color:{OPS_TEXT_DIM};font-size:0.65rem;">{sc_label}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # ================================================================
    # SECTION 4: CROSS-CORRELATIONS
    # ================================================================
    st.markdown(
        f'<div class="ops-section-header">'
        f'<span class="ops-section-label">BRIEF-04</span>'
        f'<span class="ops-section-title">Cross-Correlation Insights</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if insights:
        type_groups = {}
        for ins in insights:
            t = ins.get("type", "info")
            type_groups.setdefault(t, []).append(ins)

        type_styles = {
            "opportunity": (OPS_GREEN, "OPPORTUNITIES"),
            "synergy": (OPS_CYAN, "SYNERGIES"),
            "warning": (OPS_AMBER, "WARNINGS"),
            "threat": (OPS_RED, "THREATS"),
        }

        for tkey, (color, group_name) in type_styles.items():
            group = type_groups.get(tkey, [])
            if not group:
                continue
            st.markdown(
                f'<span style="color:{color};font-family:JetBrains Mono,monospace;'
                f'font-size:0.78rem;font-weight:700;">{group_name}</span>'
                f' <span style="color:{OPS_TEXT_DIM};font-size:0.7rem;">({len(group)})</span>',
                unsafe_allow_html=True,
            )
            for ins in group:
                domains_str = ", ".join(
                    INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
                    for d in ins.get("domains", [])
                )
                st.markdown(
                    f'<div style="border-left:3px solid {color};padding:8px 12px;'
                    f'margin:4px 0;background:{OPS_BG};border-radius:0 8px 8px 0;'
                    f'font-family:JetBrains Mono,monospace;">'
                    f'<strong style="color:{color};font-size:0.78rem;">'
                    f'{html_module.escape(ins.get("title", ""))}</strong>'
                    f' <span style="color:{OPS_TEXT_DIM};font-size:0.68rem;">'
                    f'({ins.get("confidence", 0):.0%})</span><br/>'
                    f'<span style="color:{OPS_TEXT};font-size:0.75rem;">'
                    f'{html_module.escape(ins.get("text", ""))}</span><br/>'
                    f'<span style="color:{OPS_TEXT_DIM};font-size:0.65rem;">'
                    f'Domains: {html_module.escape(domains_str)}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("No cross-correlations detected.")

    # ================================================================
    # SECTION 5: SWOT ANALYSIS
    # ================================================================
    st.markdown(
        f'<div class="ops-section-header">'
        f'<span class="ops-section-label">BRIEF-05</span>'
        f'<span class="ops-section-title">SWOT Analysis</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    sw1, sw2 = st.columns(2)
    with sw1:
        s_items = swot.get("S", [])
        s_html = "".join(
            f'<li style="color:{OPS_GREEN};font-size:0.78rem;">{html_module.escape(s)}</li>'
            for s in s_items
        ) if s_items else f'<li style="color:{OPS_TEXT_DIM};">None identified</li>'
        st.markdown(
            f'<div style="background:rgba(0,255,136,0.04);border:1px solid {OPS_GREEN}44;'
            f'border-radius:8px;padding:14px;">'
            f'<h5 style="color:{OPS_GREEN};margin:0 0 8px;font-family:JetBrains Mono,monospace;'
            f'font-size:0.78rem;">STRENGTHS</h5>'
            f'<ul style="margin:0;padding-left:18px;">{s_html}</ul></div>',
            unsafe_allow_html=True,
        )
        o_items = swot.get("O", [])
        o_html = "".join(
            f'<li style="color:{OPS_CYAN};font-size:0.78rem;">{html_module.escape(o.get("title", ""))}</li>'
            for o in o_items
        ) if o_items else f'<li style="color:{OPS_TEXT_DIM};">None identified</li>'
        st.markdown(
            f'<div style="background:rgba(0,240,255,0.04);border:1px solid {OPS_CYAN}44;'
            f'border-radius:8px;padding:14px;margin-top:10px;">'
            f'<h5 style="color:{OPS_CYAN};margin:0 0 8px;font-family:JetBrains Mono,monospace;'
            f'font-size:0.78rem;">OPPORTUNITIES</h5>'
            f'<ul style="margin:0;padding-left:18px;">{o_html}</ul></div>',
            unsafe_allow_html=True,
        )

    with sw2:
        w_items = swot.get("W", [])
        w_html = "".join(
            f'<li style="color:{OPS_RED};font-size:0.78rem;">{html_module.escape(w)}</li>'
            for w in w_items
        ) if w_items else f'<li style="color:{OPS_TEXT_DIM};">None identified</li>'
        st.markdown(
            f'<div style="background:rgba(255,51,68,0.04);border:1px solid {OPS_RED}44;'
            f'border-radius:8px;padding:14px;">'
            f'<h5 style="color:{OPS_RED};margin:0 0 8px;font-family:JetBrains Mono,monospace;'
            f'font-size:0.78rem;">WEAKNESSES</h5>'
            f'<ul style="margin:0;padding-left:18px;">{w_html}</ul></div>',
            unsafe_allow_html=True,
        )
        t_items = swot.get("T", [])
        t_html = "".join(
            f'<li style="color:{OPS_AMBER};font-size:0.78rem;">{html_module.escape(t.get("title", ""))}</li>'
            for t in t_items
        ) if t_items else f'<li style="color:{OPS_TEXT_DIM};">None identified</li>'
        st.markdown(
            f'<div style="background:rgba(255,170,0,0.04);border:1px solid {OPS_AMBER}44;'
            f'border-radius:8px;padding:14px;margin-top:10px;">'
            f'<h5 style="color:{OPS_AMBER};margin:0 0 8px;font-family:JetBrains Mono,monospace;'
            f'font-size:0.78rem;">THREATS</h5>'
            f'<ul style="margin:0;padding-left:18px;">{t_html}</ul></div>',
            unsafe_allow_html=True,
        )

    # ================================================================
    # SECTION 6: 8 DECISION SCENARIOS
    # ================================================================
    st.markdown(
        f'<div class="ops-section-header">'
        f'<span class="ops-section-label">BRIEF-06</span>'
        f'<span class="ops-section-title">8 Decision Scenarios</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.plotly_chart(
        _build_scenario_comparison(scenario_results),
        key="ib_scenario_cmp", use_container_width=True,
    )

    ops_verdict_colors = {"GO": OPS_GREEN, "CAUTION": OPS_AMBER, "NO-GO": OPS_RED}
    sc_cols = st.columns(4)
    for idx, result in enumerate(scenario_results):
        v = result["verdict"]
        v_color = ops_verdict_colors.get(v, OPS_TEXT_DIM)
        with sc_cols[idx % 4]:
            st.markdown(
                f'<div style="text-align:center;padding:12px;border:2px solid {v_color};'
                f'border-radius:10px;margin:4px 0;background:{OPS_BG};'
                f'font-family:JetBrains Mono,monospace;">'
                f'<div style="font-size:24px;">{result.get("icon", "")}</div>'
                f'<div style="color:{OPS_TEXT_DIM};font-size:0.7rem;">'
                f'{html_module.escape(result["name"])}</div>'
                f'<div style="font-size:1.5rem;font-weight:bold;color:{v_color};">'
                f'{result["overall_score"]:.0f}</div>'
                f'<div style="font-size:0.78rem;font-weight:bold;color:{v_color};">{v}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    for result in scenario_results:
        v = result["verdict"]
        v_color = ops_verdict_colors.get(v, OPS_TEXT_DIM)
        with st.expander(f"{result.get('icon', '')} {result['name']} - {v} ({result['overall_score']:.0f})"):
            header = "| Criterion | Score | Weight |"
            sep = "|---|---|---|"
            rows_md = [header, sep]
            for crit in result["criteria"].values():
                s = crit["score"]
                dot = "+" if s >= VERDICT_GO else "~" if s >= VERDICT_CAUTION else "-"
                rows_md.append(
                    f"| {dot} {crit['label']} | {s:.0f} | {crit['weight']:.0%} |"
                )
            st.markdown("\n".join(rows_md))

            r_col, a_col = st.columns(2)
            with r_col:
                if result["risks"]:
                    st.markdown("**Risks:**")
                    for r in result["risks"][:5]:
                        st.markdown(f"- {r}")
            with a_col:
                if result["advantages"]:
                    st.markdown("**Advantages:**")
                    for a in result["advantages"][:5]:
                        st.markdown(f"- {a}")

    # ================================================================
    # SECTION 7: RECOMMENDATIONS
    # ================================================================
    st.markdown(
        f'<div class="ops-section-header">'
        f'<span class="ops-section-label">BRIEF-07</span>'
        f'<span class="ops-section-title">Recommendations</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if recommendations:
        for rank, rec in enumerate(recommendations, 1):
            conf = rec.get("confidence", "Medium")
            conf_colors = {"High": OPS_GREEN, "Medium": OPS_AMBER, "Low": OPS_TEXT_DIM}
            cc = conf_colors.get(conf, OPS_TEXT_DIM)
            st.markdown(
                f'<div style="background:{OPS_BG};border:1px solid {OPS_GRID};'
                f'border-radius:8px;padding:12px 16px;margin:6px 0;'
                f'font-family:JetBrains Mono,monospace;">'
                f'<span style="color:{OPS_TEXT_DIM};font-size:0.7rem;">#{rank}</span> '
                f'<span style="color:{OPS_TEXT};font-weight:bold;font-size:0.82rem;">'
                f'{html_module.escape(rec.get("action", ""))}</span>'
                f' <span style="color:{cc};font-size:0.68rem;background:rgba(0,0,0,0.3);'
                f'padding:2px 8px;border-radius:6px;">{html_module.escape(conf)}</span><br/>'
                f'<span style="color:{OPS_TEXT_DIM};font-size:0.72rem;">'
                f'{html_module.escape(rec.get("rationale", ""))}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Insufficient data for recommendations.")

    # ================================================================
    # SECTION 8: AGGREGATED CHARTS
    # ================================================================
    st.markdown(
        f'<div class="ops-section-header">'
        f'<span class="ops-section-label">BRIEF-08</span>'
        f'<span class="ops-section-title">Aggregated Analysis Charts</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    ch1, ch2 = st.columns(2)
    with ch1:
        st.markdown(
            f'<span style="color:{OPS_TEXT_DIM};font-family:JetBrains Mono,monospace;'
            f'font-size:0.7rem;text-transform:uppercase;">Domain Correlation Heatmap</span>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            _build_correlation_heatmap(scores),
            key="ib_heatmap", use_container_width=True,
        )

    with ch2:
        st.markdown(
            f'<span style="color:{OPS_TEXT_DIM};font-family:JetBrains Mono,monospace;'
            f'font-size:0.7rem;text-transform:uppercase;">Environment Composite</span>',
            unsafe_allow_html=True,
        )
        st.plotly_chart(
            _build_environment_stacked(scores),
            key="ib_env_stack", use_container_width=True,
        )

    # ================================================================
    # SECTION 9: MATH TRANSPARENCY
    # ================================================================
    st.markdown(
        f'<div class="ops-section-header">'
        f'<span class="ops-section-label">BRIEF-09</span>'
        f'<span class="ops-section-title">Mathematical Transparency</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Show the formulas used in scoring
    eq_count = details.get("eq_count", 0)
    max_mag = details.get("max_mag", 0)
    avg_temp = details.get("avg_temp", 20)
    humidity = details.get("humidity", 50)

    st.markdown(
        f'<div class="ops-terminal">'
        f'<span class="ops-term-label">SCORING ALGORITHMS</span>'
        f'<br>'
        f'<span style="color:{OPS_CYAN};">// Shannon-Wiener Diversity (Ecology)</span><br>'
        f"H' = -\u03A3(p_i * ln(p_i)) over kingdom proportions<br>"
        f"Normalized: H'/H'_max where H'_max = ln(5) = {math.log(5):.3f}<br>"
        f'<br>'
        f'<span style="color:{OPS_CYAN};">// Bayesian Risk Posterior (Hazard Safety)</span><br>'
        f'P(risk|evidence) = P(evidence|risk)*P(risk) / P(evidence)<br>'
        f'Prior: min(eq_count/100, 0.5) = {min(eq_count / 100.0, 0.5) if eq_count > 0 else 0.05:.3f}<br>'
        f'Likelihoods: seismic={min(max_mag / 9.0, 0.99):.3f}, flood, landslide, pollution<br>'
        f'<br>'
        f'<span style="color:{OPS_CYAN};">// Sigmoid Normalization (Climate Comfort)</span><br>'
        f'\u03C3(x) = 1 / (1 + e^(-k*(x-m)))<br>'
        f'temp_score = \u03C3({avg_temp:.1f}, midpoint=20, k=0.3) = '
        f'{1.0 / (1.0 + math.exp(-0.3 * (avg_temp - 20))):.3f}<br>'
        f'humid_score = \u03C3({humidity:.0f}, midpoint=50, k=0.15) = '
        f'{1.0 / (1.0 + math.exp(-0.15 * (humidity - 50))):.3f}<br>'
        f'<br>'
        f'<span style="color:{OPS_CYAN};">// Z-Score Confidence (Cross-Correlations)</span><br>'
        f'z = (score - mean) / std<br>'
        f'confidence = (z + 3) / 6, clamped to [0, 1]<br>'
        f'<br>'
        f"<span style=\"color:{OPS_CYAN};\">// Moran's I Proxy (Geological Stability)</span><br>"
        f"I = n * \u03A3((x_i - x\u0304)(x_j - x\u0304)) / \u03A3((x_k - x\u0304)\u00b2)<br>"
        f'High spatial autocorrelation = flat terrain = +stability bonus<br>'
        f'<br>'
        f'<span style="color:{OPS_CYAN};">// Data Confidence</span><br>'
        f'confidence = available_sources / total_sources = {int(confidence * 100)}%<br>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ---- Timestamp ----
    ts_loc_name = get_short_name() or f"{lat:.5f}, {lon:.5f}"
    st.markdown(
        f'<div style="text-align:center;color:{OPS_TEXT_DIM};font-size:0.68rem;'
        f'margin-top:20px;font-family:JetBrains Mono,monospace;">'
        f'INTELLIGENCE BRIEFING // '
        f'{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} UTC // '
        f'{html_module.escape(ts_loc_name)} ({lat:.5f}, {lon:.5f})</div>',
        unsafe_allow_html=True,
    )
