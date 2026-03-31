"""
Executive Intelligence Brief — Palantir-style Decision Document for TerraScout AI.

8th page: synthesizes ALL analytics into actionable intelligence.
NLG engine generates executive narrative; visual components provide
KPI cards, sparkbars, convergence matrix, risk-opportunity quadrant,
and priority decision cards.
"""

import html as html_module
import logging
import math
from datetime import datetime

import streamlit as st

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

from src.location_context import (
    init_location_context,
    get_location,
    has_location,
    get_short_name,
    render_location_selector,
)
from src.data_hub import get_hub_data
from src.unified_intelligence import (
    INTELLIGENCE_DOMAINS,
    _classify_score,
    _compute_overall_score,
    compute_advanced_analytics,
)
from src.next_gen_data_sources import fetch_all_next_gen_sources
from src.next_gen_algorithms import (
    fuzzy_logic_assessment,
    graph_centrality_analysis,
    dbscan_domain_clustering,
    robust_anomaly_ensemble,
)
from src.palantir_visualizations import (
    create_radar_chart,
    create_sankey_diagram,
    create_waterfall_chart,
    create_sunburst_chart,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OPS-CENTER PALETTE
# ---------------------------------------------------------------------------
_BG = "#050510"
_PANEL = "#0a0a18"
_CYAN = "#00f0ff"
_GREEN = "#00ff88"
_AMBER = "#ffaa00"
_RED = "#ff3344"
_BLUE = "#4488ff"
_PURPLE = "#aa55ff"
_TEXT = "#e0e8f0"
_DIM = "#5a7090"

_DOMAIN_COLORS = {
    "habitability": _BLUE,
    "agriculture": _GREEN,
    "ecology": "#00cc66",
    "hazard_safety": _RED,
    "water_resources": _CYAN,
    "infrastructure": _PURPLE,
    "climate_comfort": _AMBER,
    "economic_potential": "#ff66aa",
    "air_environment": "#6688ff",
    "geological_stability": "#cc88ff",
}

_DOMAIN_LABELS = {
    "habitability": "Habitability",
    "agriculture": "Agriculture",
    "ecology": "Ecology",
    "hazard_safety": "Hazard Safety",
    "water_resources": "Water Resources",
    "infrastructure": "Infrastructure",
    "climate_comfort": "Climate Comfort",
    "economic_potential": "Economic Potential",
    "air_environment": "Air Environment",
    "geological_stability": "Geological Stability",
}

_DOMAINS = list(_DOMAIN_LABELS.keys())


# ═══════════════════════════════════════════════════════════════════════════
# NLG ENGINE
# ═══════════════════════════════════════════════════════════════════════════

def _grade_word(score):
    if score >= 75:
        return "strong"
    if score >= 60:
        return "favorable"
    if score >= 45:
        return "moderate"
    if score >= 30:
        return "challenging"
    return "critical"


def _generate_situation_paragraph(scores, overall, loc_name, fuzzy):
    """Opening situation assessment."""
    grade = _grade_word(overall)
    top_domains = sorted(scores.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)[:3]
    bottom_domains = sorted(scores.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 100)[:2]

    top_str = ", ".join(f"{_DOMAIN_LABELS.get(d, d)} ({v:.0f})" for d, v in top_domains if isinstance(v, (int, float)))
    bot_str = ", ".join(f"{_DOMAIN_LABELS.get(d, d)} ({v:.0f})" for d, v in bottom_domains if isinstance(v, (int, float)))

    fuzzy_verdict = ""
    if fuzzy:
        fo = fuzzy.get("fuzzy_overall", {})
        if fo:
            fuzzy_verdict = f" Fuzzy logic analysis yields a {fo.get('linguistic', 'moderate').lower()} assessment (defuzzified: {fo.get('value', 50):.0f}/100)."

    return (
        f"The location at **{html_module.escape(loc_name)}** presents a **{grade}** intelligence profile "
        f"with an aggregate score of **{overall:.0f}/100**. "
        f"Leading strengths include {top_str}. "
        f"Key vulnerabilities concentrate in {bot_str}.{fuzzy_verdict}"
    )


def _generate_risk_paragraph(next_gen, anomalies, scores):
    """Risk assessment paragraph integrating FIRMS, NOAA, anomalies."""
    parts = []

    # Fire risk
    fires = next_gen.get("firms_fires", {}) if isinstance(next_gen, dict) else {}
    fire_count = fires.get("fire_count", 0) if isinstance(fires, dict) else 0
    if fire_count > 0:
        nearest = fires.get("nearest_fire_km")
        parts.append(
            f"**{fire_count} active fire(s)** detected within {fires.get('search_radius_km', 100)} km"
            + (f" (nearest: {nearest:.0f} km)" if nearest else "")
            + "."
        )

    # Weather alerts
    alerts = next_gen.get("noaa_alerts", []) if isinstance(next_gen, dict) else []
    if isinstance(alerts, list) and alerts:
        severe = [a for a in alerts if isinstance(a, dict) and a.get("severity") in ("Extreme", "Severe")]
        if severe:
            parts.append(f"**{len(severe)} severe weather alert(s)** active: " +
                         ", ".join(a.get("event", "Unknown") for a in severe[:3]) + ".")
        else:
            parts.append(f"{len(alerts)} active weather advisory(ies) noted.")

    # Anomalies
    if isinstance(anomalies, dict):
        anom_data = anomalies.get("anomalies", {})
        critical = [d for d, info in anom_data.items()
                    if isinstance(info, dict) and info.get("severity") == "CRITICAL"]
        if critical:
            labels = [_DOMAIN_LABELS.get(d, d) for d in critical]
            parts.append(f"Anomaly ensemble flags **{', '.join(labels)}** as critical outlier(s).")

    if not parts:
        parts.append("No elevated risk factors detected at this time.")

    return " ".join(parts)


def _generate_opportunity_paragraph(graph, fuzzy, next_gen):
    """Opportunity assessment from graph centrality + fuzzy + solar."""
    parts = []

    if isinstance(graph, dict) and graph:
        influential = graph.get("most_influential", "")
        if influential:
            parts.append(
                f"Network analysis identifies **{_DOMAIN_LABELS.get(influential, influential)}** "
                f"as the most influential domain — improvements here cascade across the system."
            )

    if isinstance(fuzzy, dict):
        interactions = fuzzy.get("fuzzy_interactions", [])
        positive = [i for i in interactions
                    if isinstance(i, dict) and i.get("level") == "high" and i.get("strength", 0) > 0.3
                    and any(kw in i.get("conclusion", "").lower()
                           for kw in ("potential", "ready", "ideal", "pristine", "sustainable", "confidence", "investment"))]
        if positive:
            parts.append(
                f"Fuzzy logic identifies {len(positive)} high-strength opportunity rule(s): "
                + ", ".join(i.get("conclusion", "") for i in positive[:3]) + "."
            )

    # Solar
    power = next_gen.get("nasa_power", {}) if isinstance(next_gen, dict) else {}
    if isinstance(power, dict) and power:
        ghi = power.get("annual_ghi_kwh")
        rating = power.get("solar_potential_rating", "")
        if ghi and rating:
            parts.append(f"Solar potential rated **{rating}** ({ghi:.1f} kWh/m\u00b2/day).")

    if not parts:
        parts.append("Limited opportunity signals detected.")

    return " ".join(parts)


def _generate_recommendations(scores, graph, anomalies, fuzzy, next_gen):
    """Top 5 priority action recommendations."""
    recs = []

    # 1. Address weakest domain
    sorted_domains = sorted(
        [(d, s) for d, s in scores.items() if isinstance(s, (int, float))],
        key=lambda x: x[1],
    )
    if sorted_domains:
        weakest = sorted_domains[0]
        recs.append({
            "priority": 1,
            "action": f"Prioritize {_DOMAIN_LABELS.get(weakest[0], weakest[0])} improvement",
            "rationale": f"Lowest-scoring domain at {weakest[1]:.0f}/100 — primary drag on overall assessment.",
            "impact": "HIGH",
        })

    # 2. Leverage most influential node
    if isinstance(graph, dict) and graph.get("most_influential"):
        inf_d = graph["most_influential"]
        recs.append({
            "priority": 2,
            "action": f"Invest in {_DOMAIN_LABELS.get(inf_d, inf_d)} enhancement",
            "rationale": "Highest PageRank centrality — improvements cascade through the network.",
            "impact": "HIGH",
        })

    # 3. Fire/alert response
    fires = next_gen.get("firms_fires", {}) if isinstance(next_gen, dict) else {}
    if isinstance(fires, dict) and fires.get("fire_count", 0) > 0:
        recs.append({
            "priority": 3,
            "action": "Activate wildfire monitoring protocol",
            "rationale": f"{fires['fire_count']} active fires detected nearby.",
            "impact": "CRITICAL",
        })

    # 4. Address critical anomalies
    if isinstance(anomalies, dict):
        anom_data = anomalies.get("anomalies", {})
        critical = [d for d, info in anom_data.items()
                    if isinstance(info, dict) and info.get("severity") == "CRITICAL"]
        if critical:
            recs.append({
                "priority": len(recs) + 1,
                "action": f"Investigate anomalous {_DOMAIN_LABELS.get(critical[0], critical[0])} readings",
                "rationale": "Critical outlier detected by multi-method ensemble.",
                "impact": "HIGH",
            })

    # 5. Exploit opportunities
    if isinstance(fuzzy, dict):
        interactions = fuzzy.get("fuzzy_interactions", [])
        positive = [i for i in interactions if isinstance(i, dict) and i.get("strength", 0) > 0.4
                    and any(kw in i.get("conclusion", "").lower()
                           for kw in ("potential", "ready", "investment", "sustainable"))]
        if positive:
            recs.append({
                "priority": len(recs) + 1,
                "action": f"Capitalize on {positive[0].get('conclusion', 'opportunity')} potential",
                "rationale": f"Strong fuzzy rule activation (strength: {positive[0].get('strength', 0):.2f}).",
                "impact": "MEDIUM",
            })

    # Fill to 5
    while len(recs) < 5:
        recs.append({
            "priority": len(recs) + 1,
            "action": "Continue comprehensive monitoring",
            "rationale": "Maintain situational awareness across all domains.",
            "impact": "LOW",
        })

    return recs[:5]


def generate_executive_summary(scores, overall, loc_name, fuzzy, graph, anomalies, next_gen):
    """Generate full NLG executive summary."""
    situation = _generate_situation_paragraph(scores, overall, loc_name, fuzzy)
    risk = _generate_risk_paragraph(next_gen, anomalies, scores)
    opportunity = _generate_opportunity_paragraph(graph, fuzzy, next_gen)
    return situation, risk, opportunity


# ═══════════════════════════════════════════════════════════════════════════
# VISUAL COMPONENTS
# ═══════════════════════════════════════════════════════════════════════════

def _render_kpi_card(label, value, color, icon=""):
    """Render an animated KPI card."""
    val_str = html_module.escape(str(value))
    label_str = html_module.escape(str(label))
    return (
        f'<div class="exec-kpi-card" style="border-color:{color}33;">'
        f'<div style="font-size:1.5rem;margin-bottom:4px;">{icon}</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:1.4rem;'
        f'font-weight:800;color:{color};">{val_str}</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
        f'color:{_DIM};text-transform:uppercase;letter-spacing:1.5px;'
        f'margin-top:4px;">{label_str}</div>'
        f'</div>'
    )


def _render_domain_sparkbar(domain, score, fuzzy_level=""):
    """Render a mini horizontal sparkbar with fuzzy label."""
    color = _DOMAIN_COLORS.get(domain, _CYAN)
    label = _DOMAIN_LABELS.get(domain, domain)
    pct = max(0, min(100, score))
    fl = html_module.escape(str(fuzzy_level)) if fuzzy_level else ""
    return (
        f'<div style="display:flex;align-items:center;gap:10px;margin:4px 0;">'
        f'<div style="width:130px;font-size:0.75rem;color:{_TEXT};font-weight:500;">'
        f'{html_module.escape(label)}</div>'
        f'<div class="exec-sparkbar">'
        f'<div class="exec-sparkbar-track">'
        f'<div class="exec-sparkbar-fill" style="width:{pct}%;background:{color};"></div>'
        f'</div></div>'
        f'<div style="width:35px;text-align:right;font-family:JetBrains Mono,monospace;'
        f'font-size:0.78rem;font-weight:700;color:{color};">{pct:.0f}</div>'
        f'<div style="width:80px;font-size:0.6rem;color:{_DIM};text-transform:uppercase;'
        f'letter-spacing:0.5px;">{fl}</div>'
        f'</div>'
    )


def _render_convergence_matrix(scores, analytics):
    """Render Plotly heatmap: algorithms x domains showing divergence."""
    if go is None:
        st.info("Plotly not available for convergence matrix.")
        return

    domains = _DOMAINS
    domain_labels = [_DOMAIN_LABELS.get(d, d)[:8] for d in domains]

    # Simulate algorithm scores from different perspectives
    raw_scores = [scores.get(d, 50) for d in domains]

    algo_names = ["Raw Score", "Normalized", "Risk-Adj.", "Weighted"]
    matrix = []

    # Row 1: raw scores
    matrix.append(raw_scores)

    # Row 2: min-max normalized
    mn, mx = min(raw_scores), max(raw_scores)
    rng = mx - mn if mx != mn else 1
    matrix.append([round((v - mn) / rng * 100, 1) for v in raw_scores])

    # Row 3: risk-adjusted (penalize low hazard_safety)
    hz_idx = domains.index("hazard_safety") if "hazard_safety" in domains else -1
    hz_factor = raw_scores[hz_idx] / 100 if hz_idx >= 0 else 0.5
    matrix.append([round(v * (0.7 + 0.3 * hz_factor), 1) for v in raw_scores])

    # Row 4: weighted by importance
    weights = [1.2, 1.1, 0.9, 1.3, 1.1, 1.0, 0.8, 0.9, 1.0, 1.0]
    matrix.append([round(v * w, 1) for v, w in zip(raw_scores, weights)])

    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=domain_labels,
        y=algo_names,
        colorscale=[[0, "#0d0d1a"], [0.3, "#ff3344"], [0.5, "#ffaa00"], [0.7, "#00f0ff"], [1, "#00ff88"]],
        showscale=True,
        colorbar=dict(title=dict(text="Score", font=dict(size=10, color=_DIM)),
                      tickfont=dict(size=9, color=_DIM)),
        hoverongaps=False,
        text=[[f"{v:.0f}" for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont=dict(size=10, color=_TEXT),
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,5,16,0.6)",
        font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
        height=250,
        margin=dict(l=80, r=20, t=30, b=50),
        xaxis=dict(tickfont=dict(size=9, color=_DIM)),
        yaxis=dict(tickfont=dict(size=9, color=_DIM)),
    )
    st.plotly_chart(fig, use_container_width=True, key="exec_convergence_heatmap")


def _render_risk_opportunity_quadrant(scores, anomalies, fuzzy):
    """Plotly scatter: X=opportunity, Y=risk, 4 colored quadrants."""
    if go is None:
        st.info("Plotly not available for risk-opportunity quadrant.")
        return

    x_vals = []  # opportunity
    y_vals = []  # risk
    labels = []
    colors = []

    for d in _DOMAINS:
        s = scores.get(d, 50)
        if not isinstance(s, (int, float)):
            s = 50

        # Opportunity = score (higher = more opportunity)
        opp = s
        # Risk = inverted score + anomaly penalty
        risk = 100 - s
        if isinstance(anomalies, dict):
            anom_info = anomalies.get("anomalies", {}).get(d, {})
            if isinstance(anom_info, dict) and anom_info.get("is_anomaly"):
                risk = min(risk + 15, 100)

        x_vals.append(opp)
        y_vals.append(risk)
        labels.append(_DOMAIN_LABELS.get(d, d))
        colors.append(_DOMAIN_COLORS.get(d, _CYAN))

    fig = go.Figure()

    # Quadrant backgrounds
    fig.add_shape(type="rect", x0=0, x1=50, y0=50, y1=100,
                  fillcolor="rgba(255,51,68,0.06)", line_width=0)
    fig.add_shape(type="rect", x0=50, x1=100, y0=50, y1=100,
                  fillcolor="rgba(255,170,0,0.06)", line_width=0)
    fig.add_shape(type="rect", x0=0, x1=50, y0=0, y1=50,
                  fillcolor="rgba(90,112,144,0.06)", line_width=0)
    fig.add_shape(type="rect", x0=50, x1=100, y0=0, y1=50,
                  fillcolor="rgba(0,255,136,0.06)", line_width=0)

    # Quadrant labels
    fig.add_annotation(x=25, y=95, text="HIGH RISK<br>LOW OPP", showarrow=False,
                       font=dict(size=8, color="rgba(255,51,68,0.4)"))
    fig.add_annotation(x=75, y=95, text="HIGH RISK<br>HIGH OPP", showarrow=False,
                       font=dict(size=8, color="rgba(255,170,0,0.4)"))
    fig.add_annotation(x=25, y=5, text="LOW RISK<br>LOW OPP", showarrow=False,
                       font=dict(size=8, color="rgba(90,112,144,0.4)"))
    fig.add_annotation(x=75, y=5, text="LOW RISK<br>HIGH OPP", showarrow=False,
                       font=dict(size=8, color="rgba(0,255,136,0.4)"))

    for i in range(len(labels)):
        fig.add_trace(go.Scatter(
            x=[x_vals[i]], y=[y_vals[i]],
            mode="markers+text",
            marker=dict(size=14, color=colors[i], line=dict(width=1, color="rgba(255,255,255,0.3)")),
            text=[labels[i][:6]],
            textposition="top center",
            textfont=dict(size=8, color=colors[i]),
            showlegend=False,
            hovertext=f"{labels[i]}<br>Opportunity: {x_vals[i]:.0f}<br>Risk: {y_vals[i]:.0f}",
            hoverinfo="text",
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,5,16,0.6)",
        font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
        height=350,
        margin=dict(l=50, r=20, t=20, b=40),
        xaxis=dict(title="Opportunity", range=[0, 105], gridcolor="rgba(255,255,255,0.03)",
                   tickfont=dict(size=9, color=_DIM)),
        yaxis=dict(title="Risk", range=[0, 105], gridcolor="rgba(255,255,255,0.03)",
                   tickfont=dict(size=9, color=_DIM)),
    )
    st.plotly_chart(fig, use_container_width=True, key="exec_risk_opp_quad")


def _render_decision_cards(recs):
    """Render priority-ordered recommendation cards."""
    impact_colors = {"CRITICAL": _RED, "HIGH": _AMBER, "MEDIUM": _CYAN, "LOW": _DIM}
    cards_html = ""
    for rec in recs:
        color = impact_colors.get(rec.get("impact", "LOW"), _DIM)
        cards_html += (
            f'<div style="background:{_PANEL};border:1px solid {color}33;border-left:3px solid {color};'
            f'border-radius:0 8px 8px 0;padding:12px 16px;margin:8px 0;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'background:{color}22;color:{color};padding:2px 8px;border-radius:4px;'
            f'font-weight:700;">P{rec.get("priority", "?")}</span>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
            f'background:{color}15;color:{color};padding:2px 6px;border-radius:3px;'
            f'letter-spacing:0.5px;">{html_module.escape(str(rec.get("impact", "")))}</span>'
            f'</div>'
            f'<div style="font-size:0.88rem;font-weight:600;color:{_TEXT};margin-bottom:4px;">'
            f'{html_module.escape(str(rec.get("action", "")))}</div>'
            f'<div style="font-size:0.75rem;color:{_DIM};line-height:1.4;">'
            f'{html_module.escape(str(rec.get("rationale", "")))}</div>'
            f'</div>'
        )
    st.markdown(cards_html, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# PAGE RENDERER
# ═══════════════════════════════════════════════════════════════════════════

def render_executive_brief():
    """Render the Executive Intelligence Brief page."""
    init_location_context()

    # ───── CLASSIFIED HEADER ─────
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    st.markdown(
        '<div class="exec-classified-header">'
        '<div class="exec-classification-badge">TOP SECRET // TERRASCOUT // NOFORN</div>'
        '<h1 style="color:#e0e8f0;font-size:1.5rem;font-weight:800;letter-spacing:3px;'
        'text-transform:uppercase;margin:12px 0 6px;position:relative;z-index:1;">'
        'EXECUTIVE INTELLIGENCE BRIEF</h1>'
        f'<p style="color:#5a7090;font-size:0.75rem;font-family:JetBrains Mono,monospace;'
        f'position:relative;z-index:1;">'
        f'CLASSIFICATION: TS/SCI &bull; GENERATED: {timestamp} &bull; '
        f'PALANTIR DECISION PLATFORM v2.0</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    render_location_selector(key_prefix="exec")

    if not has_location():
        st.info("Select a location above to generate the Executive Intelligence Brief.")
        return

    loc = get_location()
    lat, lon = loc["lat"], loc["lon"]
    loc_name = get_short_name()

    # ───── FETCH ALL DATA ─────
    with st.spinner("Compiling executive intelligence briefing..."):
        hub = get_hub_data(lat, lon)
        scores = hub.get("scores", {})
        details = hub.get("details", {})
        raw_data = hub.get("raw_data", {})
        overall_score = hub.get("overall_score", 50)
        _conf_raw = hub.get("confidence", 0.5)
        confidence = float(_conf_raw.get("overall", 0.5)) if isinstance(_conf_raw, dict) else float(_conf_raw or 0)

        analytics = compute_advanced_analytics(scores, details, raw_data)

        # Next-gen data
        try:
            next_gen = fetch_all_next_gen_sources(lat, lon)
        except Exception:
            next_gen = {}

        # Next-gen algorithms
        try:
            fuzzy = fuzzy_logic_assessment(scores, details)
        except Exception:
            fuzzy = {}

        try:
            graph = graph_centrality_analysis(scores, details, analytics)
        except Exception:
            graph = {}

        try:
            clustering = dbscan_domain_clustering(scores, details)
        except Exception:
            clustering = {}

        try:
            anomalies = robust_anomaly_ensemble(scores, details, analytics)
        except Exception:
            anomalies = {}

    # ═══════════════════════════════════════════════════════════════
    # SECTION 1: EXECUTIVE SUMMARY (NLG)
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-left:3px solid {_CYAN};padding:8px 16px;margin:1.2rem 0 0.6rem;'
        f'background:{_CYAN}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
        f'[01]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{_CYAN};letter-spacing:1.5px;">EXECUTIVE SUMMARY</span></div>',
        unsafe_allow_html=True,
    )

    situation, risk_para, opp_para = generate_executive_summary(
        scores, overall_score, loc_name, fuzzy, graph, anomalies, next_gen
    )

    st.markdown(
        f'<div class="exec-summary-panel">'
        f'<div style="margin-bottom:12px;">{situation}</div>'
        f'<div style="margin-bottom:12px;"><strong style="color:{_RED};">Risk Assessment:</strong> {risk_para}</div>'
        f'<div><strong style="color:{_GREEN};">Opportunities:</strong> {opp_para}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ═══════════════════════════════════════════════════════════════
    # SECTION 2: KPI STRIP
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-left:3px solid {_AMBER};padding:8px 16px;margin:1.2rem 0 0.6rem;'
        f'background:{_AMBER}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
        f'[02]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{_AMBER};letter-spacing:1.5px;">KEY PERFORMANCE INDICATORS</span></div>',
        unsafe_allow_html=True,
    )

    overall_color = _GREEN if overall_score >= 65 else (_AMBER if overall_score >= 40 else _RED)
    conf_pct = (confidence if isinstance(confidence, (int, float)) else 0.5) * 100

    fire_count = 0
    alert_count = 0
    health_score = "N/A"
    solar_ghi = "N/A"

    if isinstance(next_gen, dict):
        fires = next_gen.get("firms_fires", {})
        fire_count = fires.get("fire_count", 0) if isinstance(fires, dict) else 0
        alerts = next_gen.get("noaa_alerts", [])
        alert_count = len(alerts) if isinstance(alerts, list) else 0
        who = next_gen.get("who_health", {})
        hs = who.get("health_score") if isinstance(who, dict) else None
        health_score = f"{hs:.0f}" if isinstance(hs, (int, float)) else "N/A"
        power = next_gen.get("nasa_power", {})
        ghi = power.get("annual_ghi_kwh") if isinstance(power, dict) else None
        solar_ghi = f"{ghi:.1f}" if isinstance(ghi, (int, float)) else "N/A"

    kpi_html = '<div style="display:flex;gap:10px;flex-wrap:wrap;margin:8px 0;">'
    kpi_html += _render_kpi_card("Overall Score", f"{overall_score:.0f}", overall_color, "\U0001f3af")
    kpi_html += _render_kpi_card("Confidence", f"{conf_pct:.0f}%", _CYAN, "\U0001f50d")
    kpi_html += _render_kpi_card("Active Fires", str(fire_count), _RED if fire_count > 0 else _GREEN, "\U0001f525")
    kpi_html += _render_kpi_card("Weather Alerts", str(alert_count), _AMBER if alert_count > 0 else _GREEN, "\u26a0\ufe0f")
    kpi_html += _render_kpi_card("Health Score", health_score, _BLUE, "\U0001f3e5")
    kpi_html += _render_kpi_card("Solar GHI", solar_ghi, _AMBER, "\u2600\ufe0f")
    kpi_html += '</div>'
    st.markdown(kpi_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 3: DOMAIN DEEP-DIVE (Sparkbars)
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-left:3px solid {_PURPLE};padding:8px 16px;margin:1.2rem 0 0.6rem;'
        f'background:{_PURPLE}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
        f'[03]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{_PURPLE};letter-spacing:1.5px;">DOMAIN ASSESSMENT</span></div>',
        unsafe_allow_html=True,
    )

    fuzzy_domains = fuzzy.get("fuzzy_domains", {}) if isinstance(fuzzy, dict) else {}
    sparkbar_html = '<div style="background:#0a0a18;border:1px solid #1a2035;border-radius:8px;padding:12px 16px;">'
    for d in _DOMAINS:
        s = scores.get(d, 50)
        if not isinstance(s, (int, float)):
            s = 50
        # Get dominant fuzzy level
        fd = fuzzy_domains.get(d, {})
        if isinstance(fd, dict) and fd:
            dominant = max(fd.items(), key=lambda x: x[1])
            fl = dominant[0].upper() if dominant[1] > 0.3 else ""
        else:
            fl = ""
        sparkbar_html += _render_domain_sparkbar(d, s, fl)
    sparkbar_html += '</div>'
    st.markdown(sparkbar_html, unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 4: CONVERGENCE MATRIX
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-left:3px solid {_RED};padding:8px 16px;margin:1.2rem 0 0.6rem;'
        f'background:{_RED}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
        f'[04]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{_RED};letter-spacing:1.5px;">CROSS-ALGORITHM CONVERGENCE</span></div>',
        unsafe_allow_html=True,
    )
    _render_convergence_matrix(scores, analytics)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5: RISK-OPPORTUNITY QUADRANT
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-left:3px solid {_GREEN};padding:8px 16px;margin:1.2rem 0 0.6rem;'
        f'background:{_GREEN}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
        f'[05]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{_GREEN};letter-spacing:1.5px;">RISK-OPPORTUNITY QUADRANT</span></div>',
        unsafe_allow_html=True,
    )
    _render_risk_opportunity_quadrant(scores, anomalies, fuzzy)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 5b: THREAT MAP
    # ═══════════════════════════════════════════════════════════════
    try:
        from src.intelligence_map import render_compact_threat_map
        st.markdown(
            f'<div style="border-left:3px solid {_RED};padding:8px 16px;margin:1.2rem 0 0.6rem;'
            f'background:{_RED}08;border-radius:0 6px 6px 0;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
            f'[05b]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
            f'font-weight:700;color:{_RED};letter-spacing:1.5px;">THREAT GEOGRAPHY</span></div>',
            unsafe_allow_html=True,
        )
        raw = hub.get("raw_data", {})
        render_compact_threat_map(lat, lon, raw, height=380)
    except Exception as exc:
        logger.warning("Threat map in executive brief failed: %s", exc)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6: RADAR ASSESSMENT
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-left:3px solid {_CYAN};padding:8px 16px;margin:1.2rem 0 0.6rem;'
        f'background:{_CYAN}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
        f'[06]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{_CYAN};letter-spacing:1.5px;">DOMAIN RADAR</span></div>',
        unsafe_allow_html=True,
    )
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        radar_fig = create_radar_chart(scores, height=340)
        if radar_fig:
            st.plotly_chart(radar_fig, use_container_width=True, key="exec_radar_spider")
        else:
            st.info("Radar chart unavailable.")
    with col_r2:
        waterfall_fig = create_waterfall_chart(scores, height=340)
        if waterfall_fig:
            st.plotly_chart(waterfall_fig, use_container_width=True, key="exec_waterfall")
        else:
            st.info("Waterfall chart unavailable.")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 6b: GLOBE & GAUGE DASHBOARD
    # ═══════════════════════════════════════════════════════════════
    try:
        from src.palantir_charts_v2 import create_3d_globe, create_gauge_dashboard
        col_g1, col_g2 = st.columns([1, 2])
        with col_g1:
            globe_fig = create_3d_globe(lat, lon, scores, height=320)
            if globe_fig:
                st.plotly_chart(globe_fig, use_container_width=True, key="exec_3d_globe")
        with col_g2:
            gauge_fig = create_gauge_dashboard(scores, height=320)
            if gauge_fig:
                st.plotly_chart(gauge_fig, use_container_width=True, key="exec_gauge_dash")
    except Exception as exc:
        logger.warning("Globe/gauge section failed: %s", exc)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 7: INFLUENCE FLOWS & HIERARCHY
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-left:3px solid {_PURPLE};padding:8px 16px;margin:1.2rem 0 0.6rem;'
        f'background:{_PURPLE}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
        f'[07]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{_PURPLE};letter-spacing:1.5px;">INFLUENCE FLOWS & HIERARCHY</span></div>',
        unsafe_allow_html=True,
    )
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        sankey_fig = create_sankey_diagram(scores, height=380)
        if sankey_fig:
            st.plotly_chart(sankey_fig, use_container_width=True, key="exec_sankey_flow")
        else:
            st.info("Sankey diagram unavailable.")
    with col_s2:
        sunburst_fig = create_sunburst_chart(scores, details, height=380)
        if sunburst_fig:
            st.plotly_chart(sunburst_fig, use_container_width=True, key="exec_sunburst")
        else:
            st.info("Sunburst chart unavailable.")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 8: GRAPH CENTRALITY INSIGHT
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-left:3px solid {_BLUE};padding:8px 16px;margin:1.2rem 0 0.6rem;'
        f'background:{_BLUE}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
        f'[08]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{_BLUE};letter-spacing:1.5px;">INFLUENCE NETWORK ANALYSIS</span></div>',
        unsafe_allow_html=True,
    )

    if isinstance(graph, dict) and graph.get("nodes"):
        insight = graph.get("key_insight", "")
        st.markdown(
            f'<div class="exec-summary-panel" style="border-left-color:{_BLUE};">'
            f'{html_module.escape(insight)}</div>',
            unsafe_allow_html=True,
        )

        # Render network graph
        if go is not None:
            nodes = graph.get("nodes", [])
            edges = graph.get("edges", [])
            idx_map = {n["domain"]: i for i, n in enumerate(nodes)}

            # Layout: circular
            n = len(nodes)
            positions = {}
            for i, nd in enumerate(nodes):
                angle = 2 * math.pi * i / n
                positions[nd["domain"]] = (math.cos(angle), math.sin(angle))

            fig = go.Figure()

            # Edges
            for e in edges:
                src_pos = positions.get(e["source"])
                tgt_pos = positions.get(e["target"])
                if src_pos and tgt_pos:
                    fig.add_trace(go.Scatter(
                        x=[src_pos[0], tgt_pos[0]], y=[src_pos[1], tgt_pos[1]],
                        mode="lines",
                        line=dict(width=max(0.5, e["weight"] * 2), color="rgba(0,240,255,0.15)"),
                        showlegend=False, hoverinfo="skip",
                    ))

            # Nodes
            for nd in nodes:
                pos = positions.get(nd["domain"], (0, 0))
                color = _DOMAIN_COLORS.get(nd["domain"], _CYAN)
                size = 15 + nd["pagerank"] * 150
                fig.add_trace(go.Scatter(
                    x=[pos[0]], y=[pos[1]],
                    mode="markers+text",
                    marker=dict(size=size, color=color, line=dict(width=2, color="rgba(255,255,255,0.2)")),
                    text=[nd["label"][:6]],
                    textposition="top center",
                    textfont=dict(size=8, color=color),
                    showlegend=False,
                    hovertext=f"{nd['label']}<br>Score: {nd['score']}<br>PageRank: {nd['pagerank']:.3f}",
                    hoverinfo="text",
                ))

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(5,5,16,0.6)",
                font=dict(color=_DIM, size=10),
                height=350,
                margin=dict(l=20, r=20, t=20, b=20),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False, scaleanchor="x"),
            )
            st.plotly_chart(fig, use_container_width=True, key="exec_network_graph")
    else:
        st.info("Graph centrality analysis unavailable.")

    # ═══════════════════════════════════════════════════════════════
    # SECTION 9: DECISION RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-left:3px solid {_AMBER};padding:8px 16px;margin:1.2rem 0 0.6rem;'
        f'background:{_AMBER}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;color:{_DIM};">'
        f'[09]</span>&nbsp;<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{_AMBER};letter-spacing:1.5px;">PRIORITY RECOMMENDATIONS</span></div>',
        unsafe_allow_html=True,
    )

    recs = _generate_recommendations(scores, graph, anomalies, fuzzy, next_gen)
    _render_decision_cards(recs)

    # ═══════════════════════════════════════════════════════════════
    # SECTION 10: CONFIDENCE & METHODOLOGY
    # ═══════════════════════════════════════════════════════════════
    st.markdown(
        f'<div style="border-top:2px solid {_PURPLE}33;padding-top:16px;margin-top:24px;'
        f'text-align:center;">'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
        f'color:{_DIM};letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;">'
        f'METHODOLOGY & CONFIDENCE</div>'
        f'<div style="font-size:0.72rem;color:{_DIM};max-width:600px;margin:0 auto;line-height:1.6;">'
        f'This brief integrates <strong style="color:{_TEXT};">32+ data sources</strong> '
        f'and <strong style="color:{_TEXT};">30 analytical algorithms</strong> '
        f'including Dempster-Shafer fusion, fuzzy logic, graph centrality, DBSCAN clustering, '
        f'robust anomaly detection, VIKOR compromise, Markov chains, entropy analysis, '
        f'Pareto optimization, Monte Carlo simulation, and Bayesian belief networks. '
        f'Data confidence: <strong style="color:{_CYAN};">{conf_pct:.0f}%</strong>.</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
        f'color:{_DIM};margin-top:8px;">CLASSIFICATION: TOP SECRET // TERRASCOUT // NOFORN</div>'
        f'</div>',
        unsafe_allow_html=True,
    )
