"""
Location Comparator - Multi-Location Intelligence Comparison for TerraScout AI.
Palantir-style side-by-side analysis of 2-5 locations with radar overlay,
domain breakdowns, strengths/weaknesses matrix, head-to-head butterfly chart,
best-fit scenario heatmap, and exportable summary table.

Entry point: render_location_comparator()
"""

import html as html_module
import logging
import time

import streamlit as st
try:
    import plotly.graph_objects as go
except ImportError:
    go = None

from src.unified_intelligence import (
    collect_all_intelligence,
    compute_domain_scores,
    compute_cross_correlations,
    generate_swot,
    generate_recommendations,
    _compute_overall_score,
    _classify_score,
    compute_data_confidence,
    INTELLIGENCE_DOMAINS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OPS-CENTER COLOR PALETTE
# ---------------------------------------------------------------------------
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

LOC_COLORS = ["#00f0ff", "#00ff88", "#ff3344", "#aa55ff", "#ffaa00"]

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
# BEST-FIT SCENARIO WEIGHTS
# ---------------------------------------------------------------------------
COMPARATOR_SCENARIOS = {
    "Residence": {
        "habitability": 0.30, "water_resources": 0.20, "climate_comfort": 0.20,
        "infrastructure": 0.15, "hazard_safety": 0.15,
    },
    "Agriculture": {
        "agriculture": 0.35, "water_resources": 0.25, "climate_comfort": 0.20,
        "ecology": 0.10, "hazard_safety": 0.10,
    },
    "Commercial": {
        "economic_potential": 0.30, "infrastructure": 0.30, "habitability": 0.20,
        "climate_comfort": 0.10, "hazard_safety": 0.10,
    },
    "Conservation": {
        "ecology": 0.35, "water_resources": 0.20, "air_environment": 0.20,
        "geological_stability": 0.15, "hazard_safety": 0.10,
    },
    "Tourism": {
        "climate_comfort": 0.25, "ecology": 0.20, "habitability": 0.20,
        "infrastructure": 0.15, "water_resources": 0.10, "air_environment": 0.10,
    },
    "Energy": {
        "infrastructure": 0.25, "geological_stability": 0.20, "climate_comfort": 0.15,
        "water_resources": 0.15, "economic_potential": 0.15, "hazard_safety": 0.10,
    },
    "Shelter": {
        "hazard_safety": 0.25, "water_resources": 0.20, "habitability": 0.20,
        "infrastructure": 0.15, "climate_comfort": 0.10, "geological_stability": 0.10,
    },
    "Research": {
        "ecology": 0.25, "geological_stability": 0.20, "water_resources": 0.15,
        "air_environment": 0.15, "climate_comfort": 0.15, "infrastructure": 0.10,
    },
}

# Medal display helpers
_MEDALS = {0: "#FFD700", 1: "#C0C0C0", 2: "#CD7F32"}  # gold, silver, bronze


# ---------------------------------------------------------------------------
# DATA FETCH (does NOT overwrite the shared session-state cache)
# ---------------------------------------------------------------------------

def _fetch_location_hub(lat, lon):
    """Fetch hub-equivalent data for a location without clobbering ts_data_hub.

    Uses the same pipeline as data_hub.get_hub_data but returns the result
    directly instead of storing it in session state, so we can compare
    multiple locations without conflict.
    """
    try:
        raw_data = collect_all_intelligence(lat, lon)
    except Exception as exc:
        logger.warning("collect_all_intelligence failed for (%.4f, %.4f): %s", lat, lon, exc)
        raw_data = {}

    # Enhanced sources (best-effort)
    try:
        from src.enhanced_data_sources import fetch_all_enhanced_sources
        enhanced = fetch_all_enhanced_sources(lat, lon)
        raw_data["gdacs"] = enhanced.get("gdacs", [])
        raw_data["population"] = enhanced.get("population", {})
        raw_data["openaq"] = enhanced.get("openaq", [])
    except Exception:
        raw_data.setdefault("gdacs", [])
        raw_data.setdefault("population", {})
        raw_data.setdefault("openaq", [])

    # Geopolitical (best-effort)
    try:
        from src.geopolitical_engine import fetch_complete_geopolitical_profile
        geopolitical = fetch_complete_geopolitical_profile(lat, lon)
        raw_data["geopolitical"] = geopolitical
    except Exception:
        raw_data.setdefault("geopolitical", {})

    try:
        scores, details = compute_domain_scores(lat, lon, raw_data)
    except Exception:
        scores, details = {k: 50 for k in INTELLIGENCE_DOMAINS}, {}

    try:
        insights = compute_cross_correlations(scores, details)
    except Exception:
        insights = []

    try:
        swot = generate_swot(scores, details, insights)
    except Exception:
        swot = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}

    try:
        recommendations = generate_recommendations(scores, swot, insights)
    except Exception:
        recommendations = []

    overall_score = _compute_overall_score(scores)
    overall_label, overall_color = _classify_score(overall_score)
    confidence = compute_data_confidence(raw_data) if raw_data else 0.0

    return {
        "lat": lat,
        "lon": lon,
        "raw_data": raw_data,
        "scores": scores,
        "details": details,
        "insights": insights,
        "swot": swot,
        "recommendations": recommendations,
        "overall_score": overall_score,
        "overall_label": overall_label,
        "overall_color": overall_color,
        "confidence": confidence,
    }


# ---------------------------------------------------------------------------
# SECTION A: OVERALL RANKING
# ---------------------------------------------------------------------------

def _render_ranking(locations):
    """Display ranked locations with medal highlights."""
    st.markdown(
        '<div style="color:#00f0ff;font-size:0.65rem;letter-spacing:3px;'
        'margin-top:1.5rem;">SECTION A</div>'
        '<h3 style="color:#e0e8f0;margin:0.2rem 0 0.8rem 0;">OVERALL RANKING</h3>',
        unsafe_allow_html=True,
    )
    ranked = sorted(locations, key=lambda x: x["overall"], reverse=True)
    for idx, loc in enumerate(ranked):
        medal_color = _MEDALS.get(idx, OPS_TEXT_DIM)
        medal_label = {0: "1ST", 1: "2ND", 2: "3RD"}.get(idx, f"{idx+1}TH")
        is_winner = idx == 0
        border = f"2px solid {OPS_CYAN}" if is_winner else f"1px solid {OPS_TEXT_DIM}33"
        glow = f"box-shadow: 0 0 20px {OPS_CYAN}40;" if is_winner else ""
        score = loc["overall"]
        label = loc["label"]
        conf = loc["confidence"]
        name_esc = html_module.escape(loc["name"])

        st.markdown(
            f'<div style="background:{OPS_PANEL};border:{border};border-radius:8px;'
            f'padding:1rem 1.2rem;margin-bottom:0.5rem;{glow}'
            f'display:flex;align-items:center;gap:1rem;">'
            f'<div style="background:{medal_color};color:#000;font-weight:900;'
            f'border-radius:50%;width:38px;height:38px;display:flex;align-items:center;'
            f'justify-content:center;font-size:0.7rem;flex-shrink:0;">{medal_label}</div>'
            f'<div style="flex:1;">'
            f'<div style="color:{OPS_TEXT};font-size:1.1rem;font-weight:700;">{name_esc}</div>'
            f'<div style="color:{OPS_TEXT_DIM};font-size:0.75rem;">'
            f'{loc["lat"]:.4f}, {loc["lon"]:.4f}</div>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<div style="color:{loc["color"]};font-size:1.6rem;font-weight:900;'
            f'font-family:JetBrains Mono,monospace;">{score:.0f}</div>'
            f'<div style="color:{OPS_TEXT_DIM};font-size:0.7rem;">{label} &bull; '
            f'{int((float(conf.get("overall", 0)) if isinstance(conf, dict) else float(conf or 0)) * 100)}% conf</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# SECTION B: RADAR COMPARISON
# ---------------------------------------------------------------------------

def _render_radar(locations):
    """Overlay radar (Scatterpolar) chart for all locations."""
    st.markdown(
        '<div style="color:#00f0ff;font-size:0.65rem;letter-spacing:3px;'
        'margin-top:2rem;">SECTION B</div>'
        '<h3 style="color:#e0e8f0;margin:0.2rem 0 0.8rem 0;">RADAR COMPARISON</h3>',
        unsafe_allow_html=True,
    )
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())
    domain_names = [INTELLIGENCE_DOMAINS[k]["name"] for k in domain_keys]

    fig = go.Figure()
    for i, loc in enumerate(locations):
        vals = [loc["scores"].get(k, 0) for k in domain_keys]
        vals_closed = vals + [vals[0]]
        names_closed = domain_names + [domain_names[0]]
        color = LOC_COLORS[i % len(LOC_COLORS)]
        fig.add_trace(go.Scatterpolar(
            r=vals_closed,
            theta=names_closed,
            fill="toself",
            fillcolor=color + "18",
            line=dict(color=color, width=2),
            name=loc["name"],
            opacity=0.9,
        ))

    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True, range=[0, 100],
                tickfont=dict(color=OPS_TEXT_DIM, size=9),
                gridcolor=OPS_GRID,
            ),
            angularaxis=dict(
                tickfont=dict(color=OPS_TEXT, size=10),
                gridcolor=OPS_GRID,
            ),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=OPS_TEXT),
        legend=dict(
            font=dict(color=OPS_TEXT, size=11),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=OPS_TEXT_DIM,
            borderwidth=1,
        ),
        margin=dict(l=70, r=70, t=40, b=40),
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True, key="comp_radar_chart")


# ---------------------------------------------------------------------------
# SECTION C: DOMAIN-BY-DOMAIN BREAKDOWN
# ---------------------------------------------------------------------------

def _render_domain_bars(locations):
    """Grouped bar chart: X = domains, grouped bars = locations."""
    st.markdown(
        '<div style="color:#00f0ff;font-size:0.65rem;letter-spacing:3px;'
        'margin-top:2rem;">SECTION C</div>'
        '<h3 style="color:#e0e8f0;margin:0.2rem 0 0.8rem 0;">'
        'DOMAIN-BY-DOMAIN BREAKDOWN</h3>',
        unsafe_allow_html=True,
    )
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())
    domain_names = [INTELLIGENCE_DOMAINS[k]["name"] for k in domain_keys]

    fig = go.Figure()
    for i, loc in enumerate(locations):
        vals = [loc["scores"].get(k, 0) for k in domain_keys]
        color = LOC_COLORS[i % len(LOC_COLORS)]
        fig.add_trace(go.Bar(
            x=domain_names,
            y=vals,
            name=loc["name"],
            marker_color=color,
            text=[f"{v:.0f}" for v in vals],
            textposition="outside",
            textfont=dict(color=OPS_TEXT, size=9,
                          family="JetBrains Mono, monospace"),
        ))

    fig.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=OPS_TEXT),
        xaxis=dict(
            tickfont=dict(color=OPS_TEXT, size=9),
            tickangle=45,
            gridcolor=OPS_GRID,
        ),
        yaxis=dict(
            range=[0, 110],
            gridcolor=OPS_GRID,
            tickfont=dict(color=OPS_TEXT_DIM),
        ),
        legend=dict(
            font=dict(color=OPS_TEXT, size=11),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=OPS_TEXT_DIM,
            borderwidth=1,
        ),
        margin=dict(l=50, r=20, t=30, b=110),
        height=460,
    )
    st.plotly_chart(fig, use_container_width=True, key="comp_domain_bars")


# ---------------------------------------------------------------------------
# SECTION D: STRENGTHS & WEAKNESSES MATRIX
# ---------------------------------------------------------------------------

def _render_strengths_weaknesses(locations):
    """For each location, list top 3 strengths and top 3 weaknesses."""
    st.markdown(
        '<div style="color:#00f0ff;font-size:0.65rem;letter-spacing:3px;'
        'margin-top:2rem;">SECTION D</div>'
        '<h3 style="color:#e0e8f0;margin:0.2rem 0 0.8rem 0;">'
        'STRENGTHS & WEAKNESSES MATRIX</h3>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(locations))
    for idx, loc in enumerate(locations):
        color = LOC_COLORS[idx % len(LOC_COLORS)]
        sorted_scores = sorted(
            loc["scores"].items(), key=lambda x: x[1], reverse=True,
        )
        strengths = sorted_scores[:3]
        weaknesses = sorted_scores[-3:]
        name_esc = html_module.escape(loc["name"])

        with cols[idx]:
            st.markdown(
                f'<div style="background:{OPS_PANEL};border:1px solid {color}40;'
                f'border-radius:8px;padding:1rem;min-height:320px;">'
                f'<div style="color:{color};font-weight:700;font-size:1rem;'
                f'margin-bottom:0.8rem;text-align:center;">{name_esc}</div>'
                f'<div style="color:{OPS_GREEN};font-size:0.7rem;'
                f'letter-spacing:2px;margin-bottom:0.4rem;">STRENGTHS</div>',
                unsafe_allow_html=True,
            )
            for domain_key, score in strengths:
                dname = INTELLIGENCE_DOMAINS.get(domain_key, {}).get("name", domain_key)
                st.markdown(
                    f'<div style="color:{OPS_TEXT};font-size:0.85rem;'
                    f'padding:0.15rem 0;">'
                    f'<span style="color:{OPS_GREEN};font-family:JetBrains Mono,'
                    f'monospace;font-weight:700;">{score:.0f}</span> {dname}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(
                f'<div style="color:{OPS_RED};font-size:0.7rem;'
                f'letter-spacing:2px;margin:0.8rem 0 0.4rem 0;">WEAKNESSES</div>',
                unsafe_allow_html=True,
            )
            for domain_key, score in weaknesses:
                dname = INTELLIGENCE_DOMAINS.get(domain_key, {}).get("name", domain_key)
                st.markdown(
                    f'<div style="color:{OPS_TEXT};font-size:0.85rem;'
                    f'padding:0.15rem 0;">'
                    f'<span style="color:{OPS_RED};font-family:JetBrains Mono,'
                    f'monospace;font-weight:700;">{score:.0f}</span> {dname}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SECTION E: HEAD-TO-HEAD (only when exactly 2 locations)
# ---------------------------------------------------------------------------

def _render_head_to_head(locations):
    """Butterfly chart comparing two locations domain by domain."""
    if len(locations) != 2:
        return

    st.markdown(
        '<div style="color:#00f0ff;font-size:0.65rem;letter-spacing:3px;'
        'margin-top:2rem;">SECTION E</div>'
        '<h3 style="color:#e0e8f0;margin:0.2rem 0 0.8rem 0;">'
        'HEAD-TO-HEAD COMPARISON</h3>',
        unsafe_allow_html=True,
    )

    loc_a, loc_b = locations[0], locations[1]
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())
    domain_names = [INTELLIGENCE_DOMAINS[k]["name"] for k in domain_keys]

    a_vals = [loc_a["scores"].get(k, 0) for k in domain_keys]
    b_vals = [loc_b["scores"].get(k, 0) for k in domain_keys]

    # Butterfly: A goes left (negative), B goes right (positive)
    a_display = [-v for v in a_vals]

    a_colors = []
    b_colors = []
    a_wins = 0
    b_wins = 0
    for av, bv in zip(a_vals, b_vals):
        if av >= bv:
            a_colors.append(OPS_GREEN)
            b_colors.append(OPS_TEXT_DIM + "88")
            a_wins += 1
        else:
            a_colors.append(OPS_TEXT_DIM + "88")
            b_colors.append(OPS_GREEN)
            b_wins += 1

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=domain_names,
        x=a_display,
        orientation="h",
        name=loc_a["name"],
        marker_color=a_colors,
        text=[f"{v:.0f}" for v in a_vals],
        textposition="inside",
        textfont=dict(color="#fff", size=11,
                      family="JetBrains Mono, monospace"),
        insidetextanchor="middle",
    ))
    fig.add_trace(go.Bar(
        y=domain_names,
        x=b_vals,
        orientation="h",
        name=loc_b["name"],
        marker_color=b_colors,
        text=[f"{v:.0f}" for v in b_vals],
        textposition="inside",
        textfont=dict(color="#fff", size=11,
                      family="JetBrains Mono, monospace"),
        insidetextanchor="middle",
    ))

    fig.update_layout(
        barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=OPS_TEXT),
        xaxis=dict(
            range=[-110, 110],
            zeroline=True,
            zerolinecolor=OPS_TEXT_DIM,
            zerolinewidth=2,
            showticklabels=False,
            gridcolor=OPS_GRID,
        ),
        yaxis=dict(
            tickfont=dict(color=OPS_TEXT, size=11),
        ),
        legend=dict(
            font=dict(color=OPS_TEXT, size=11),
            bgcolor="rgba(0,0,0,0)",
            bordercolor=OPS_TEXT_DIM,
            borderwidth=1,
            orientation="h",
            yanchor="bottom", y=1.02, xanchor="center", x=0.5,
        ),
        margin=dict(l=140, r=40, t=50, b=30),
        height=440,
    )
    st.plotly_chart(fig, use_container_width=True, key="comp_head2head_chart")

    # Verdict text
    name_a = html_module.escape(loc_a["name"])
    name_b = html_module.escape(loc_b["name"])

    # Identify which domains each wins
    a_winning_domains = []
    b_winning_domains = []
    for i, k in enumerate(domain_keys):
        dname = INTELLIGENCE_DOMAINS[k]["name"]
        if a_vals[i] >= b_vals[i]:
            a_winning_domains.append(dname)
        else:
            b_winning_domains.append(dname)

    a_str = ", ".join(a_winning_domains[:4]) if a_winning_domains else "none"
    b_str = ", ".join(b_winning_domains[:4]) if b_winning_domains else "none"

    overall_winner = name_a if loc_a["overall"] >= loc_b["overall"] else name_b
    overall_diff = abs(loc_a["overall"] - loc_b["overall"])
    margin_word = "narrow" if overall_diff < 5 else ("moderate" if overall_diff < 15 else "significant")

    st.markdown(
        f'<div style="background:{OPS_PANEL};border:1px solid {OPS_CYAN}30;'
        f'border-radius:8px;padding:1rem;margin-top:0.5rem;">'
        f'<div style="color:{OPS_CYAN};font-size:0.7rem;letter-spacing:2px;'
        f'margin-bottom:0.4rem;">VERDICT</div>'
        f'<div style="color:{OPS_TEXT};font-size:0.9rem;">'
        f'<b>{overall_winner}</b> leads overall by a <b>{margin_word}</b> margin '
        f'({overall_diff:.0f} pts).</div>'
        f'<div style="color:{OPS_TEXT_DIM};font-size:0.8rem;margin-top:0.3rem;">'
        f'<span style="color:{LOC_COLORS[0]};">{name_a}</span> excels in: {a_str}<br>'
        f'<span style="color:{LOC_COLORS[1]};">{name_b}</span> excels in: {b_str}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# SECTION F: BEST-FIT ANALYSIS (heatmap)
# ---------------------------------------------------------------------------

def _compute_scenario_fitness(scores, weights):
    """Compute weighted fitness score for a scenario."""
    total = 0.0
    for domain, w in weights.items():
        total += scores.get(domain, 0) * w
    return round(total, 1)


def _render_bestfit(locations):
    """Heatmap: rows = scenarios, columns = locations, cells = fitness score."""
    st.markdown(
        '<div style="color:#00f0ff;font-size:0.65rem;letter-spacing:3px;'
        'margin-top:2rem;">SECTION F</div>'
        '<h3 style="color:#e0e8f0;margin:0.2rem 0 0.8rem 0;">'
        'BEST-FIT SCENARIO ANALYSIS</h3>',
        unsafe_allow_html=True,
    )

    scenario_names = list(COMPARATOR_SCENARIOS.keys())
    loc_names = [loc["name"] for loc in locations]

    # Build matrix: rows = scenarios, cols = locations
    z_matrix = []
    text_matrix = []
    for scenario in scenario_names:
        weights = COMPARATOR_SCENARIOS[scenario]
        row = []
        text_row = []
        for loc in locations:
            fitness = _compute_scenario_fitness(loc["scores"], weights)
            row.append(fitness)
            text_row.append(f"{fitness:.0f}")
        z_matrix.append(row)
        text_matrix.append(text_row)

    # Highlight best location per scenario in annotations
    annotations = []
    for r_idx, row in enumerate(z_matrix):
        best_val = max(row)
        for c_idx, val in enumerate(row):
            is_best = abs(val - best_val) < 0.01
            font_size = 14 if is_best else 11
            font_color = OPS_CYAN if is_best else OPS_TEXT
            font_weight = "bold" if is_best else "normal"
            annotations.append(dict(
                x=loc_names[c_idx],
                y=scenario_names[r_idx],
                text=f"<b>{val:.0f}</b>" if is_best else f"{val:.0f}",
                showarrow=False,
                font=dict(color=font_color, size=font_size),
            ))

    colorscale = [
        [0, OPS_RED + "cc"],
        [0.35, OPS_AMBER + "88"],
        [0.5, OPS_PANEL],
        [0.75, OPS_GREEN + "88"],
        [1, OPS_GREEN],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=loc_names,
        y=scenario_names,
        colorscale=colorscale,
        zmin=0,
        zmax=100,
        showscale=True,
        colorbar=dict(
            tickfont=dict(color=OPS_TEXT_DIM, size=10),
            title=dict(text="Fitness", font=dict(color=OPS_TEXT_DIM, size=10)),
        ),
        hovertemplate="Location: %{x}<br>Scenario: %{y}<br>Fitness: %{z:.0f}<extra></extra>",
    ))
    fig.update_layout(
        annotations=annotations,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=OPS_TEXT),
        xaxis=dict(
            tickfont=dict(color=OPS_TEXT, size=11),
            side="top",
        ),
        yaxis=dict(
            tickfont=dict(color=OPS_TEXT, size=11),
            autorange="reversed",
        ),
        margin=dict(l=110, r=40, t=60, b=30),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True, key="comp_bestfit_heatmap")

    # Best-fit summary cards
    st.markdown(
        '<div style="color:#00f0ff;font-size:0.65rem;letter-spacing:2px;'
        'margin:1rem 0 0.5rem 0;">SCENARIO RECOMMENDATIONS</div>',
        unsafe_allow_html=True,
    )
    summary_cols = st.columns(min(len(scenario_names), 4))
    for s_idx, scenario in enumerate(scenario_names):
        col = summary_cols[s_idx % len(summary_cols)]
        row = z_matrix[s_idx]
        best_idx = row.index(max(row))
        best_name = html_module.escape(loc_names[best_idx])
        best_score = row[best_idx]
        loc_color = LOC_COLORS[best_idx % len(LOC_COLORS)]
        with col:
            st.markdown(
                f'<div style="background:{OPS_PANEL};border:1px solid {loc_color}30;'
                f'border-radius:6px;padding:0.6rem;margin-bottom:0.4rem;text-align:center;">'
                f'<div style="color:{OPS_TEXT_DIM};font-size:0.65rem;'
                f'letter-spacing:1px;">{scenario.upper()}</div>'
                f'<div style="color:{loc_color};font-size:1rem;font-weight:700;'
                f'margin-top:0.2rem;">{best_name}</div>'
                f'<div style="color:{OPS_TEXT_DIM};font-size:0.75rem;">'
                f'{best_score:.0f}/100</div></div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# SECTION G: SUMMARY TABLE & EXPORT
# ---------------------------------------------------------------------------

def _render_summary_table(locations):
    """Full comparison table with all data and export button."""
    st.markdown(
        '<div style="color:#00f0ff;font-size:0.65rem;letter-spacing:3px;'
        'margin-top:2rem;">SECTION G</div>'
        '<h3 style="color:#e0e8f0;margin:0.2rem 0 0.8rem 0;">'
        'FULL COMPARISON TABLE</h3>',
        unsafe_allow_html=True,
    )

    domain_keys = list(INTELLIGENCE_DOMAINS.keys())

    # Build HTML table
    header_cells = '<th style="padding:0.5rem;color:#00f0ff;border-bottom:1px solid #5a709040;">Metric</th>'
    for i, loc in enumerate(locations):
        color = LOC_COLORS[i % len(LOC_COLORS)]
        name_esc = html_module.escape(loc["name"])
        header_cells += (
            f'<th style="padding:0.5rem;color:{color};'
            f'border-bottom:1px solid #5a709040;">{name_esc}</th>'
        )

    rows_html = ""

    # Overall score row
    cells = '<td style="padding:0.4rem 0.5rem;color:#e0e8f0;font-weight:600;">Overall Score</td>'
    for loc in locations:
        cells += (
            f'<td style="padding:0.4rem 0.5rem;color:{loc["color"]};'
            f'font-family:JetBrains Mono,monospace;font-weight:700;">'
            f'{loc["overall"]:.0f} ({loc["label"]})</td>'
        )
    rows_html += f'<tr style="background:{OPS_PANEL};">{cells}</tr>'

    # Confidence row
    cells = '<td style="padding:0.4rem 0.5rem;color:#e0e8f0;">Data Confidence</td>'
    for loc in locations:
        _c = loc["confidence"]
        conf_pct = int((float(_c.get("overall", 0)) if isinstance(_c, dict) else float(_c or 0)) * 100)
        cells += (
            f'<td style="padding:0.4rem 0.5rem;color:{OPS_TEXT_DIM};'
            f'font-family:JetBrains Mono,monospace;">{conf_pct}%</td>'
        )
    rows_html += f'<tr>{cells}</tr>'

    # Coordinates row
    cells = '<td style="padding:0.4rem 0.5rem;color:#e0e8f0;">Coordinates</td>'
    for loc in locations:
        cells += (
            f'<td style="padding:0.4rem 0.5rem;color:{OPS_TEXT_DIM};'
            f'font-size:0.8rem;">{loc["lat"]:.4f}, {loc["lon"]:.4f}</td>'
        )
    rows_html += f'<tr style="background:{OPS_PANEL};">{cells}</tr>'

    # Domain scores
    for d_idx, dk in enumerate(domain_keys):
        dname = INTELLIGENCE_DOMAINS[dk]["name"]
        bg = OPS_PANEL if d_idx % 2 == 0 else "transparent"
        cells = f'<td style="padding:0.4rem 0.5rem;color:#e0e8f0;">{dname}</td>'
        # Find best score for this domain to highlight
        domain_scores = [loc["scores"].get(dk, 0) for loc in locations]
        best_in_domain = max(domain_scores) if domain_scores else 0
        for loc in locations:
            val = loc["scores"].get(dk, 0)
            is_best = abs(val - best_in_domain) < 0.01 and len(locations) > 1
            fw = "font-weight:700;" if is_best else ""
            fc = OPS_CYAN if is_best else OPS_TEXT
            cells += (
                f'<td style="padding:0.4rem 0.5rem;color:{fc};'
                f'font-family:JetBrains Mono,monospace;{fw}">{val:.0f}</td>'
            )
        rows_html += f'<tr style="background:{bg};">{cells}</tr>'

    # Scenario fitness scores
    for scenario_name, weights in COMPARATOR_SCENARIOS.items():
        cells = f'<td style="padding:0.4rem 0.5rem;color:#ffaa00;">{scenario_name} Fitness</td>'
        fitness_vals = [_compute_scenario_fitness(loc["scores"], weights) for loc in locations]
        best_fit = max(fitness_vals) if fitness_vals else 0
        for i, loc in enumerate(locations):
            fv = fitness_vals[i]
            is_best = abs(fv - best_fit) < 0.01 and len(locations) > 1
            fw = "font-weight:700;" if is_best else ""
            fc = OPS_GREEN if is_best else OPS_TEXT_DIM
            cells += (
                f'<td style="padding:0.4rem 0.5rem;color:{fc};'
                f'font-family:JetBrains Mono,monospace;{fw}">{fv:.0f}</td>'
            )
        rows_html += f'<tr style="background:{OPS_PANEL};">{cells}</tr>'

    st.markdown(
        f'<div style="overflow-x:auto;border:1px solid {OPS_TEXT_DIM}30;border-radius:8px;">'
        f'<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">'
        f'<thead><tr>{header_cells}</tr></thead>'
        f'<tbody>{rows_html}</tbody></table></div>',
        unsafe_allow_html=True,
    )

    # Export as Markdown
    md_lines = _build_export_markdown(locations, domain_keys)
    md_text = "\n".join(md_lines)

    st.download_button(
        label="EXPORT COMPARISON (Markdown)",
        data=md_text,
        file_name="terrascout_comparison.md",
        mime="text/markdown",
        key="comp_export_md_btn",
    )


def _build_export_markdown(locations, domain_keys):
    """Build a markdown comparison table for export."""
    lines = [
        "# TerraScout AI - Location Comparison Report",
        "",
        f"**Locations compared:** {len(locations)}",
        "",
    ]

    # Header row
    header = "| Metric |"
    sep = "|--------|"
    for loc in locations:
        header += f" {loc['name']} |"
        sep += "--------|"
    lines.append(header)
    lines.append(sep)

    # Overall
    row = "| Overall Score |"
    for loc in locations:
        row += f" {loc['overall']:.0f} ({loc['label']}) |"
    lines.append(row)

    # Confidence
    row = "| Data Confidence |"
    for loc in locations:
        _c = loc['confidence']
        row += f" {int((float(_c.get('overall', 0)) if isinstance(_c, dict) else float(_c or 0)) * 100)}% |"
    lines.append(row)

    # Coordinates
    row = "| Coordinates |"
    for loc in locations:
        row += f" {loc['lat']:.4f}, {loc['lon']:.4f} |"
    lines.append(row)

    # Domain scores
    for dk in domain_keys:
        dname = INTELLIGENCE_DOMAINS[dk]["name"]
        row = f"| {dname} |"
        for loc in locations:
            row += f" {loc['scores'].get(dk, 0):.0f} |"
        lines.append(row)

    # Scenario fitness
    lines.append("")
    lines.append("## Scenario Fitness Scores")
    lines.append("")
    header2 = "| Scenario |"
    sep2 = "|----------|"
    for loc in locations:
        header2 += f" {loc['name']} |"
        sep2 += "--------|"
    lines.append(header2)
    lines.append(sep2)
    for scenario_name, weights in COMPARATOR_SCENARIOS.items():
        row = f"| {scenario_name} |"
        for loc in locations:
            fv = _compute_scenario_fitness(loc["scores"], weights)
            row += f" {fv:.0f} |"
        lines.append(row)

    # Ranking
    lines.append("")
    lines.append("## Overall Ranking")
    lines.append("")
    ranked = sorted(locations, key=lambda x: x["overall"], reverse=True)
    for idx, loc in enumerate(ranked):
        lines.append(f"{idx+1}. **{loc['name']}** - Score: {loc['overall']:.0f} ({loc['label']})")

    return lines


# ---------------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------------

def render_location_comparator():
    """Main entry point for the Multi-Location Comparator page."""
    try:
        _render_comparator_impl()
    except Exception as exc:
        logger.exception("Location Comparator error: %s", exc)
        st.error(f"An error occurred in the Location Comparator: {exc}")


def _render_comparator_impl():
    """Internal implementation of the comparator page."""

    # -- Header banner --
    st.markdown(
        '<div style="background: linear-gradient(135deg, #0a0a18 0%, #0a1a2e 50%, #0a0a18 100%);'
        'border: 2px solid #00f0ff; border-radius: 12px; padding: 1.5rem; text-align: center;">'
        '<div style="color: #00f0ff; font-size: 0.7rem; letter-spacing: 4px;">'
        'MULTI-LOCATION INTELLIGENCE</div>'
        '<h1 style="color: #e0e8f0; font-size: 2rem; margin: 0.3rem 0;">'
        'LOCATION COMPARATOR</h1>'
        '<p style="color: #5a7090;">Side-by-Side Analysis &bull; Ranking &bull; '
        'Best-Fit Recommendation</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    # -- Location input --
    st.markdown(
        '<div style="color:#00f0ff;font-size:0.65rem;letter-spacing:3px;">'
        'LOCATION INPUT</div>'
        '<h3 style="color:#e0e8f0;margin:0.2rem 0 0.8rem 0;">'
        'Define Comparison Targets</h3>',
        unsafe_allow_html=True,
    )

    n_locs = st.number_input(
        "Number of locations",
        min_value=2,
        max_value=5,
        value=2,
        key="comp_n_locs",
    )

    input_cols = st.columns(int(n_locs))
    for i in range(int(n_locs)):
        loc_color = LOC_COLORS[i % len(LOC_COLORS)]
        with input_cols[i]:
            st.markdown(
                f'<div style="color:{loc_color};font-weight:700;font-size:0.85rem;'
                f'margin-bottom:0.3rem;">Location {i+1}</div>',
                unsafe_allow_html=True,
            )
            st.number_input(
                "Latitude",
                min_value=-90.0,
                max_value=90.0,
                value=0.0,
                format="%.4f",
                key=f"comp_loc_{i}_lat",
            )
            st.number_input(
                "Longitude",
                min_value=-180.0,
                max_value=180.0,
                value=0.0,
                format="%.4f",
                key=f"comp_loc_{i}_lon",
            )
            st.text_input(
                "Name (optional)",
                value="",
                key=f"comp_loc_{i}_name",
            )

    st.markdown('<div style="height:0.5rem;"></div>', unsafe_allow_html=True)

    analyze_clicked = st.button(
        "COMPARE LOCATIONS",
        key="comp_analyze_btn",
        use_container_width=True,
    )

    # Style the analyze button
    st.markdown(
        '<style>'
        'div[data-testid="stButton"] > button[kind="secondary"] {'
        '  background: linear-gradient(135deg, #00f0ff22, #0a0a18);'
        '  border: 1px solid #00f0ff; color: #00f0ff; font-weight: 700;'
        '  letter-spacing: 2px;'
        '}'
        '</style>',
        unsafe_allow_html=True,
    )

    # -- Analyze --
    if not analyze_clicked:
        st.markdown(
            f'<div style="background:{OPS_PANEL};border:1px solid {OPS_TEXT_DIM}30;'
            f'border-radius:8px;padding:2rem;text-align:center;margin-top:1rem;">'
            f'<div style="color:{OPS_TEXT_DIM};font-size:1rem;">Enter coordinates '
            f'for 2-5 locations and click <span style="color:{OPS_CYAN};">'
            f'COMPARE LOCATIONS</span> to begin analysis.</div></div>',
            unsafe_allow_html=True,
        )
        return

    # Validate inputs: at least check no duplicate exact coords
    n = int(n_locs)
    coord_list = []
    for i in range(n):
        lat_i = st.session_state.get(f"comp_loc_{i}_lat", 0.0)
        lon_i = st.session_state.get(f"comp_loc_{i}_lon", 0.0)
        coord_list.append((lat_i, lon_i))

    # Check for duplicates
    seen = set()
    has_dup = False
    for c in coord_list:
        key = (round(c[0], 4), round(c[1], 4))
        if key in seen:
            has_dup = True
        seen.add(key)

    if has_dup:
        st.warning("Duplicate coordinates detected. Each location should be unique.")

    # Fetch data for each location
    locations = []
    progress_bar = st.progress(0, text="Fetching intelligence data...")
    for i in range(n):
        lat_i = st.session_state.get(f"comp_loc_{i}_lat", 0.0)
        lon_i = st.session_state.get(f"comp_loc_{i}_lon", 0.0)
        name_i = st.session_state.get(f"comp_loc_{i}_name", "").strip()
        if not name_i:
            name_i = f"Location {i+1}"

        progress_bar.progress(
            (i) / n,
            text=f"Analyzing {name_i} ({lat_i:.4f}, {lon_i:.4f})...",
        )

        try:
            hub = _fetch_location_hub(lat_i, lon_i)
        except Exception as exc:
            logger.warning("Failed to fetch data for %s: %s", name_i, exc)
            st.error(f"Failed to fetch data for {name_i}: {exc}")
            continue

        locations.append({
            "name": name_i,
            "lat": lat_i,
            "lon": lon_i,
            "hub": hub,
            "scores": hub.get("scores", {}),
            "overall": hub.get("overall_score", 0),
            "label": hub.get("overall_label", "Unknown"),
            "color": hub.get("overall_color", OPS_TEXT_DIM),
            "confidence": hub.get("confidence", 0),
            "swot": hub.get("swot", {}),
            "details": hub.get("details", {}),
        })

    progress_bar.progress(1.0, text="Analysis complete.")

    if len(locations) < 2:
        st.error("Need at least 2 successfully analyzed locations to compare.")
        return

    # Store in session state for persistence across reruns
    st.session_state["comp_results"] = locations

    st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

    # Render all comparison sections
    try:
        _render_ranking(locations)
    except Exception as exc:
        logger.warning("Ranking section error: %s", exc)
        st.warning(f"Ranking section encountered an error: {exc}")

    try:
        _render_radar(locations)
    except Exception as exc:
        logger.warning("Radar section error: %s", exc)
        st.warning(f"Radar section encountered an error: {exc}")

    try:
        _render_domain_bars(locations)
    except Exception as exc:
        logger.warning("Domain bars section error: %s", exc)
        st.warning(f"Domain bars section encountered an error: {exc}")

    try:
        _render_strengths_weaknesses(locations)
    except Exception as exc:
        logger.warning("Strengths/weaknesses section error: %s", exc)
        st.warning(f"Strengths/weaknesses section encountered an error: {exc}")

    try:
        _render_head_to_head(locations)
    except Exception as exc:
        logger.warning("Head-to-head section error: %s", exc)
        st.warning(f"Head-to-head section encountered an error: {exc}")

    try:
        _render_bestfit(locations)
    except Exception as exc:
        logger.warning("Best-fit section error: %s", exc)
        st.warning(f"Best-fit section encountered an error: {exc}")

    try:
        _render_summary_table(locations)
    except Exception as exc:
        logger.warning("Summary table section error: %s", exc)
        st.warning(f"Summary table section encountered an error: {exc}")

    # Footer
    st.markdown(
        f'<div style="text-align:center;color:{OPS_TEXT_DIM};font-size:0.7rem;'
        f'margin-top:2rem;padding:1rem;border-top:1px solid {OPS_TEXT_DIM}20;">'
        f'TERRASCOUT AI &bull; MULTI-LOCATION COMPARATOR &bull; '
        f'{len(locations)} LOCATIONS ANALYZED</div>',
        unsafe_allow_html=True,
    )
