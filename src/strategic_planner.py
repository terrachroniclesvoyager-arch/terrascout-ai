"""
Strategic Action Planner — Page 9 for TerraScout AI.
Synthesises ALL intelligence into a concrete, phased action plan
with priority matrix, resource allocation, risk roadmap, and KPI framework.
"""

import html as html_module
import logging

import streamlit as st

logger = logging.getLogger(__name__)

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

# ── Palette ───────────────────────────────────────────────────────────────
_CYAN = "#00f0ff"
_GREEN = "#00ff88"
_RED = "#ff3344"
_AMBER = "#ffaa00"
_BLUE = "#4488ff"
_PURPLE = "#aa44ff"
_PANEL = "#0a0a18"
_TEXT = "#e0e0e0"
_DIM = "#6a7a8a"

_DOMAINS = [
    "water_resources", "geological_stability", "climate_comfort",
    "ecology", "agriculture", "infrastructure",
    "hazard_safety", "habitability", "air_environment", "economic_potential",
]

_DOMAIN_LABELS = {
    "water_resources": "Water Resources",
    "geological_stability": "Geological Stability",
    "climate_comfort": "Climate & Weather",
    "ecology": "Biodiversity",
    "agriculture": "Agriculture",
    "infrastructure": "Infrastructure",
    "hazard_safety": "Natural Hazards",
    "habitability": "Habitability",
    "air_environment": "Air Quality",
    "economic_potential": "Economic Potential",
}

_RISK_MITIGATIONS = {
    "water_resources": ("Water scarcity / contamination risk",
                        "Implement water quality monitoring, establish alternative supply routes, map groundwater sources"),
    "geological_stability": ("Seismic / subsidence risk",
                             "Conduct detailed geological survey, avoid construction in fault zones, deploy early warning systems"),
    "climate_comfort": ("Extreme weather exposure",
                        "Build climate-resilient infrastructure, establish weather monitoring, prepare emergency protocols"),
    "ecology": ("Ecosystem degradation",
                "Protect critical habitats, establish wildlife corridors, monitor invasive species"),
    "agriculture": ("Food security vulnerability",
                    "Diversify crop selection, implement irrigation systems, soil improvement program"),
    "infrastructure": ("Infrastructure deficit",
                       "Prioritize transport links, upgrade utilities, invest in telecommunications"),
    "hazard_safety": ("Multi-hazard exposure",
                      "Deploy early warning systems, reinforce structures, establish evacuation routes"),
    "habitability": ("Habitability degradation risk",
                     "Implement erosion control, improve living conditions, enhance soil quality"),
    "air_environment": ("Air pollution exposure",
                        "Monitor emission sources, establish buffer zones, promote clean energy"),
    "economic_potential": ("Low economic leverage",
                           "Develop unique assets, improve connectivity, attract investment"),
}

_KPI_INDICATORS = {
    "water_resources": "Water Quality Index (WQI)",
    "geological_stability": "Seismic Risk Score",
    "climate_comfort": "Climate Resilience Index",
    "ecology": "Species Diversity Index",
    "agriculture": "Crop Suitability Score",
    "infrastructure": "Infrastructure Density",
    "hazard_safety": "Multi-Hazard Risk Level",
    "habitability": "Habitability Score",
    "air_environment": "Air Quality Index (AQI)",
    "economic_potential": "Economic Advantage Score",
}


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _safe_score(scores, domain):
    v = scores.get(domain, 50)
    if not isinstance(v, (int, float)):
        return 50
    return max(0, min(100, v))


def _status_dot(score):
    if score < 40:
        return f'<span style="color:{_RED}">&#9679;</span>'
    if score < 70:
        return f'<span style="color:{_AMBER}">&#9679;</span>'
    return f'<span style="color:{_GREEN}">&#9679;</span>'


def _classify_domains(scores):
    """Classify domains into priority-matrix quadrants."""
    quick_wins = []   # score 40-60 (improvable, not catastrophic)
    major_proj = []    # score < 40 (critical)
    fill_ins = []      # score 60-80
    deprioritize = []  # score >= 80
    for d in _DOMAINS:
        s = _safe_score(scores, d)
        if s < 40:
            major_proj.append((d, s))
        elif s < 60:
            quick_wins.append((d, s))
        elif s < 80:
            fill_ins.append((d, s))
        else:
            deprioritize.append((d, s))
    return quick_wins, major_proj, fill_ins, deprioritize


# ═══════════════════════════════════════════════════════════════════════════
# SECTION RENDERERS
# ═══════════════════════════════════════════════════════════════════════════

def _render_header():
    st.markdown('''<div class="exec-classified-header">
        <div class="exec-classification-badge">STRATEGIC // PLANNER</div>
        <div style="font-size:1.8rem;font-weight:800;letter-spacing:3px;margin:10px 0">
            STRATEGIC ACTION PLANNER</div>
        <div style="font-size:0.85rem;color:#6a7a8a">
            OPERATIONAL PLANNING DOCUMENT &mdash; PRIORITY ACTIONS &amp; RESOURCE ALLOCATION</div>
    </div>''', unsafe_allow_html=True)


def _render_situation(scores, overall_score, overall_label, loc_name):
    sorted_d = sorted(_DOMAINS, key=lambda d: _safe_score(scores, d), reverse=True)
    top3 = sorted_d[:3]
    bot3 = sorted_d[-3:]
    strengths = ", ".join(f"{_dl(d)} ({_safe_score(scores,d):.0f})" for d in top3)
    weaknesses = ", ".join(f"{_dl(d)} ({_safe_score(scores,d):.0f})" for d in bot3)

    para = (
        f"The target location at <strong>{html_module.escape(loc_name)}</strong> presents a "
        f"<strong>{overall_label}</strong> operational profile "
        f"(composite score: {overall_score:.0f}/100). "
        f"Primary strengths lie in {strengths}. "
        f"Critical attention required for {weaknesses}. "
        f"This strategic plan prioritises resource allocation toward the weakest domains "
        f"while preserving existing advantages."
    )
    st.markdown(f'''<div class="exec-summary-panel" style="border-left:3px solid {_CYAN}">
        <div style="font-size:0.75rem;color:{_DIM};margin-bottom:6px;letter-spacing:2px">
            SITUATION ASSESSMENT</div>
        <div style="color:{_TEXT};font-size:0.88rem;line-height:1.7">{para}</div>
    </div>''', unsafe_allow_html=True)


def _render_priority_matrix(scores):
    quick_wins, major_proj, fill_ins, deprioritize = _classify_domains(scores)

    def _quad_html(title, items, color, icon):
        body = ""
        if items:
            for d, s in sorted(items, key=lambda x: x[1]):
                body += f'<div style="color:{_TEXT};font-size:0.8rem;padding:2px 0">{icon} {_dl(d)} — <strong>{s:.0f}</strong></div>'
        else:
            body = f'<div style="color:{_DIM};font-size:0.78rem;font-style:italic">No domains in this quadrant</div>'
        return f'''<div style="background:rgba({_hex_to_rgb(color)},0.08);border:1px solid {color};
            border-radius:12px;padding:16px;min-height:140px">
            <div style="font-weight:700;color:{color};margin-bottom:8px;font-size:0.85rem;
                letter-spacing:1px">{title}</div>
            {body}
        </div>'''

    st.markdown(f'<div style="font-size:0.75rem;color:{_DIM};letter-spacing:2px;margin:24px 0 10px">'
                f'PRIORITY MATRIX &mdash; IMPACT vs EFFORT</div>', unsafe_allow_html=True)
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.markdown(_quad_html("HIGH IMPACT / LOW EFFORT — QUICK WINS", quick_wins, _GREEN, "&#9889;"),
                    unsafe_allow_html=True)
    with r1c2:
        st.markdown(_quad_html("HIGH IMPACT / HIGH EFFORT — MAJOR PROJECTS", major_proj, _RED, "&#9888;"),
                    unsafe_allow_html=True)
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.markdown(_quad_html("LOW IMPACT / LOW EFFORT — FILL-INS", fill_ins, _CYAN, "&#8226;"),
                    unsafe_allow_html=True)
    with r2c2:
        st.markdown(_quad_html("LOW IMPACT / HIGH EFFORT — DEPRIORITIZE", deprioritize, _DIM, "&#10003;"),
                    unsafe_allow_html=True)


def _render_timeline(scores):
    quick_wins, major_proj, fill_ins, deprioritize = _classify_domains(scores)

    def _phase_html(num, title, timeframe, color, items_text):
        return f'''<div style="background:linear-gradient(180deg,rgba({_hex_to_rgb(color)},0.15),
            rgba(10,10,24,0.8));border:1px solid {color};border-radius:12px;padding:16px;min-height:200px">
            <div style="font-weight:700;color:{color};font-size:0.95rem">PHASE {num}</div>
            <div style="color:{_DIM};font-size:0.7rem;margin-bottom:10px">{title}<br>{timeframe}</div>
            <div style="font-size:0.78rem;color:{_TEXT};line-height:1.6">{items_text}</div>
        </div>'''

    # Phase 1: quick wins
    p1 = ""
    for d, s in quick_wins[:3]:
        p1 += f"&#9656; Address <strong>{_dl(d)}</strong> &mdash; {s:.0f} &#8594; {min(100,s+15):.0f}<br>"
    if not p1:
        p1 = "&#9656; No immediate quick wins identified &mdash; focus on maintenance<br>"

    # Phase 2: worst domains
    worst = sorted(_DOMAINS, key=lambda d: _safe_score(scores, d))[:3]
    p2 = ""
    for d in worst:
        s = _safe_score(scores, d)
        risk, _ = _RISK_MITIGATIONS.get(d, ("Unknown risk", "Investigate"))
        p2 += f"&#9656; <strong>{_dl(d)}</strong> ({s:.0f}) &mdash; {risk}<br>"

    # Phase 3: major projects
    p3 = ""
    for d, s in major_proj:
        p3 += f"&#9656; <strong>{_dl(d)}</strong> rehabilitation ({s:.0f} &#8594; 60+)<br>"
    if not p3:
        p3 = "&#9656; No critical domains &mdash; pursue cross-domain optimisation<br>"
    p3 += "&#9656; Cross-domain synergy initiatives<br>"

    # Phase 4: system-wide
    below_60 = sum(1 for d in _DOMAINS if _safe_score(scores, d) < 60)
    p4 = (f"&#9656; Target: all domains &gt;60<br>"
          f"&#9656; Currently {below_60} domain(s) below threshold<br>"
          f"&#9656; Continuous monitoring &amp; adaptive management<br>"
          f"&#9656; Annual strategic review cycle<br>")

    st.markdown(f'<div style="font-size:0.75rem;color:{_DIM};letter-spacing:2px;margin:24px 0 10px">'
                f'FOUR-PHASE STRATEGIC TIMELINE</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_phase_html(1, "IMMEDIATE", "0 — 30 DAYS", _RED, p1), unsafe_allow_html=True)
    with c2:
        st.markdown(_phase_html(2, "SHORT-TERM", "30 — 90 DAYS", _AMBER, p2), unsafe_allow_html=True)
    with c3:
        st.markdown(_phase_html(3, "MEDIUM-TERM", "90 — 180 DAYS", _CYAN, p3), unsafe_allow_html=True)
    with c4:
        st.markdown(_phase_html(4, "LONG-TERM", "180 — 365 DAYS", _GREEN, p4), unsafe_allow_html=True)


def _render_resource_allocation(scores):
    st.markdown(f'<div style="font-size:0.75rem;color:{_DIM};letter-spacing:2px;margin:24px 0 10px">'
                f'RECOMMENDED RESOURCE ALLOCATION</div>', unsafe_allow_html=True)

    weights = {}
    for d in _DOMAINS:
        s = _safe_score(scores, d)
        weights[d] = max(1, (100 - s) / 10)
    total_w = sum(weights.values())
    alloc = {d: round(w / total_w * 100, 1) for d, w in weights.items()}

    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        if go is not None:
            try:
                colors = [_domain_color(d) for d in _DOMAINS]
                fig = go.Figure(go.Pie(
                    labels=[_dl(d).split()[0] for d in _DOMAINS],
                    values=[alloc[d] for d in _DOMAINS],
                    hole=0.5,
                    marker=dict(colors=colors, line=dict(color="rgba(255,255,255,0.1)", width=1)),
                    textinfo="label+percent",
                    textfont=dict(size=9, color=_TEXT),
                    hovertemplate="%{label}: %{percent}<extra></extra>",
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color=_DIM, size=10),
                    height=320,
                    margin=dict(l=10, r=10, t=10, b=10),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True, key="sp_alloc_pie")
            except Exception as exc:
                logger.warning("Allocation pie failed: %s", exc)

    with col_table:
        rows = ""
        for d in sorted(_DOMAINS, key=lambda x: alloc[x], reverse=True):
            s = _safe_score(scores, d)
            target = min(100, s + 20)
            gap = target - s
            rows += (f'<tr style="border-bottom:1px solid rgba(255,255,255,0.04)">'
                     f'<td style="padding:5px 8px;color:{_TEXT};font-size:0.78rem">{_dl(d)}</td>'
                     f'<td style="padding:5px 8px;text-align:center;color:{_TEXT}">{s:.0f}</td>'
                     f'<td style="padding:5px 8px;text-align:center;color:{_CYAN}">{target:.0f}</td>'
                     f'<td style="padding:5px 8px;text-align:center;color:{_AMBER}">{gap:.0f}</td>'
                     f'<td style="padding:5px 8px;text-align:center;color:{_GREEN}">{alloc[d]:.1f}%</td>'
                     f'</tr>')
        st.markdown(f'''<table style="width:100%;border-collapse:collapse">
            <thead><tr style="border-bottom:1px solid rgba(255,255,255,0.1)">
                <th style="text-align:left;padding:6px 8px;color:{_DIM};font-size:0.72rem">Domain</th>
                <th style="text-align:center;padding:6px 8px;color:{_DIM};font-size:0.72rem">Current</th>
                <th style="text-align:center;padding:6px 8px;color:{_DIM};font-size:0.72rem">Target</th>
                <th style="text-align:center;padding:6px 8px;color:{_DIM};font-size:0.72rem">Gap</th>
                <th style="text-align:center;padding:6px 8px;color:{_DIM};font-size:0.72rem">Alloc %</th>
            </tr></thead><tbody>{rows}</tbody></table>''', unsafe_allow_html=True)


def _render_risk_roadmap(scores):
    at_risk = [(d, _safe_score(scores, d)) for d in _DOMAINS if _safe_score(scores, d) < 60]
    if not at_risk:
        st.markdown(f'<div style="color:{_GREEN};font-size:0.85rem;padding:12px">'
                    f'&#10003; All domains above 60 &mdash; no critical risks identified.</div>',
                    unsafe_allow_html=True)
        return

    st.markdown(f'<div style="font-size:0.75rem;color:{_DIM};letter-spacing:2px;margin:24px 0 10px">'
                f'RISK MITIGATION ROADMAP</div>', unsafe_allow_html=True)

    for d, s in sorted(at_risk, key=lambda x: x[1]):
        risk_title, mitigation = _RISK_MITIGATIONS.get(d, ("Unclassified risk", "Conduct further investigation"))
        target = min(100, s + 20)
        color = _RED if s < 40 else _AMBER
        st.markdown(f'''<div style="background:rgba({_hex_to_rgb(color)},0.06);border-left:3px solid {color};
            padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:8px">
            <div style="font-weight:700;color:{color};font-size:0.85rem">{_dl(d)} &mdash; {risk_title}</div>
            <div style="color:{_TEXT};font-size:0.8rem;margin-top:4px">
                Score: {s:.0f}/100 &ensp;|&ensp; Gap to target: {target - s:.0f}</div>
            <div style="color:{_DIM};font-size:0.78rem;margin-top:6px">&#9656; {mitigation}</div>
        </div>''', unsafe_allow_html=True)


def _render_kpi_framework(scores):
    st.markdown(f'<div style="font-size:0.75rem;color:{_DIM};letter-spacing:2px;margin:24px 0 10px">'
                f'KPI MONITORING FRAMEWORK</div>', unsafe_allow_html=True)

    rows = ""
    for d in _DOMAINS:
        s = _safe_score(scores, d)
        t90 = min(100, s + 10)
        t365 = min(100, s + 25)
        kpi = _KPI_INDICATORS.get(d, "Composite Index")
        dot = _status_dot(s)
        rows += (f'<tr style="border-bottom:1px solid rgba(255,255,255,0.04)">'
                 f'<td style="padding:5px 8px;color:{_TEXT};font-size:0.78rem">{_dl(d)}</td>'
                 f'<td style="padding:5px 8px;text-align:center">{s:.0f}</td>'
                 f'<td style="padding:5px 8px;text-align:center;color:{_AMBER}">{t90:.0f}</td>'
                 f'<td style="padding:5px 8px;text-align:center;color:{_GREEN}">{t365:.0f}</td>'
                 f'<td style="padding:5px 8px;color:{_DIM};font-size:0.75rem">{kpi}</td>'
                 f'<td style="padding:5px 8px;text-align:center">{dot}</td>'
                 f'</tr>')

    st.markdown(f'''<table style="width:100%;border-collapse:collapse">
        <thead><tr style="border-bottom:1px solid rgba(255,255,255,0.1)">
            <th style="text-align:left;padding:6px 8px;color:{_DIM};font-size:0.72rem">Domain</th>
            <th style="text-align:center;padding:6px 8px;color:{_DIM};font-size:0.72rem">Current</th>
            <th style="text-align:center;padding:6px 8px;color:{_DIM};font-size:0.72rem">90-Day Target</th>
            <th style="text-align:center;padding:6px 8px;color:{_DIM};font-size:0.72rem">365-Day Target</th>
            <th style="text-align:left;padding:6px 8px;color:{_DIM};font-size:0.72rem">KPI Indicator</th>
            <th style="text-align:center;padding:6px 8px;color:{_DIM};font-size:0.72rem">Status</th>
        </tr></thead><tbody>{rows}</tbody></table>''', unsafe_allow_html=True)


def _render_monitoring():
    st.markdown(f'<div style="font-size:0.75rem;color:{_DIM};letter-spacing:2px;margin:24px 0 10px">'
                f'MONITORING &amp; REVIEW PROTOCOL</div>', unsafe_allow_html=True)
    st.markdown(f'''<div class="exec-summary-panel" style="border-left:3px solid {_PURPLE}">
        <div style="color:{_TEXT};font-size:0.82rem;line-height:1.8">
            <strong>Review Cycle:</strong> Monthly reassessment of all KPI indicators<br>
            <strong>Data Refresh:</strong> Real-time (weather, AQ) &ensp;|&ensp; Daily (hazards, fires)
                &ensp;|&ensp; Weekly (infrastructure, land use)<br>
            <strong>Escalation Triggers:</strong> Any single domain drops below 30, OR 3+ domains
                simultaneously below 50<br>
            <strong>Reporting:</strong> Executive brief auto-generated on each assessment cycle<br>
            <strong>Stakeholders:</strong> Operations, Risk Management, Strategic Planning, Field Teams
        </div>
    </div>''', unsafe_allow_html=True)


def _render_confidence_footer(hub):
    confidence = hub.get("confidence", {})
    if isinstance(confidence, dict):
        conf_val = confidence.get("overall", 0)
        sources_ok = confidence.get("sources_available", 0)
        sources_total = confidence.get("sources_total", 0)
    elif isinstance(confidence, (int, float)):
        conf_val = confidence
        sources_ok = sources_total = 0
    else:
        conf_val = sources_ok = sources_total = 0

    pct = max(0, min(100, conf_val * 100 if conf_val <= 1 else conf_val))
    color = _GREEN if pct >= 70 else (_AMBER if pct >= 40 else _RED)

    st.markdown(f'''<div style="margin-top:32px;padding:16px;background:rgba(10,10,24,0.6);
        border:1px solid rgba(255,255,255,0.05);border-radius:12px">
        <div style="font-size:0.72rem;color:{_DIM};letter-spacing:2px;margin-bottom:8px">
            DATA CONFIDENCE &amp; METHODOLOGY</div>
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
            <div style="flex:1;height:6px;background:rgba(255,255,255,0.05);border-radius:3px">
                <div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:3px"></div>
            </div>
            <div style="color:{color};font-size:0.85rem;font-weight:700">{pct:.0f}%</div>
        </div>
        <div style="color:{_DIM};font-size:0.75rem;line-height:1.6">
            Data sources: {sources_ok}/{sources_total} responding &ensp;|&ensp;
            Algorithms: 30 analytical engines &ensp;|&ensp;
            Domains: 10 intelligence dimensions<br>
            This plan synthesises 32+ data sources, 30 algorithms, and multi-domain cross-correlation
            to produce actionable strategic recommendations. Confidence level reflects real-time
            data availability and cross-validation between independent sources.
        </div>
    </div>''', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# UTILITY
# ═══════════════════════════════════════════════════════════════════════════

_DOMAIN_COLORS = {
    "water_resources": _CYAN,
    "geological_stability": "#8B4513",
    "climate_comfort": _BLUE,
    "ecology": _GREEN,
    "agriculture": "#228B22",
    "infrastructure": _AMBER,
    "hazard_safety": _RED,
    "habitability": "#D2691E",
    "air_environment": _PURPLE,
    "economic_potential": "#FFD700",
}


def _domain_color(d):
    return _DOMAIN_COLORS.get(d, _CYAN)


def _dl(d):
    """Return display label for a snake_case domain key."""
    return _DOMAIN_LABELS.get(d, d)


def _hex_to_rgb(h):
    """Convert '#rrggbb' to 'r,g,b' string for CSS rgba()."""
    h = h.lstrip("#")
    if len(h) < 6:
        return "0,240,255"
    try:
        return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"
    except ValueError:
        return "0,240,255"


# ═══════════════════════════════════════════════════════════════════════════
# MAIN PAGE ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def render_strategic_planner():
    """Render the Strategic Action Planner page."""

    loc = st.session_state.get("ts_location") or {}
    lat = loc.get("lat")
    lon = loc.get("lon")
    loc_name = loc.get("name", "Unknown Location")

    if lat is None or lon is None:
        st.warning("Set a location from the Command Center to generate a strategic plan.")
        return

    from src.data_hub import get_hub_data

    with st.spinner("Compiling strategic action plan..."):
        hub = get_hub_data(lat, lon)

    scores = hub.get("scores", {})
    overall_score = hub.get("overall_score", 50)
    overall_label = hub.get("overall_label", "UNCLASSIFIED")

    # ── 1. Header ──
    _render_header()

    # ── 2. Situation Assessment ──
    _render_situation(scores, overall_score, overall_label, loc_name)

    # ── 3. Priority Matrix ──
    _render_priority_matrix(scores)

    # ── 4. Four-Phase Timeline ──
    _render_timeline(scores)

    # ── 5. Resource Allocation ──
    _render_resource_allocation(scores)

    # ── 6. Risk Mitigation Roadmap ──
    _render_risk_roadmap(scores)

    # ── 7. KPI Framework ──
    _render_kpi_framework(scores)

    # ── 8. Monitoring & Review ──
    _render_monitoring()

    # ── 9. Confidence Footer ──
    _render_confidence_footer(hub)
