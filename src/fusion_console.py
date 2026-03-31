"""
Fusion Intelligence Console — Palantir-Style Decision Platform for TerraScout AI.

Multi-source evidence fusion & decision intelligence.  Takes ALL data from
data_hub + compute_advanced_analytics and processes it through 11+ fusion
algorithms plus 5 advanced engines (Kriging, PCA, BBN, Monte Carlo,
Correlation Intelligence) to produce actionable intelligence, not just data.

Sections:
0. Header + Location
1. Situation Assessment
2. Evidence Fusion Matrix
3. Threat Cascade Analysis
4. Decision Intelligence
5. Vulnerability Profile
6. Anomaly Intelligence
7. Temporal Outlook
8. Intelligence Summary
9. Geospatial Kriging
10. Factor Analysis (PCA)
11. Causal Network & What-If
12. Active Threats (GDACS + OpenAQ)
13. Unified Threat Radar
14. Strategic Intelligence Synthesis
15. Monte Carlo Risk Simulation
16. Cross-Domain Correlation Intelligence
17. Predictive Analytics & Forecasting
18. Decision Tree Assessment
19. Scenario Wargaming & Intervention
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
from src.decision_matrix import (
    DECISION_SCENARIOS,
    VERDICT_GO,
    VERDICT_CAUTION,
    VERDICT_COLORS,
    _collect_location_data,
    _evaluate_scenario,
)
from src.fusion_engine import (
    dempster_shafer_fusion,
    topsis_scenario_ranking,
    ahp_priority_synthesis,
    risk_propagation_cascade,
    composite_vulnerability_index,
    anomaly_severity_ranking,
    temporal_trend_synthesis,
    electre_outranking,
)
from src.advanced_fusion_algorithms import (
    kriging_interpolation,
    pca_domain_analysis,
    bayesian_belief_network,
    bayesian_what_if,
    prepare_kriging_data,
)
from src.strategic_synthesis import compute_strategic_assessment
from src.threat_radar import compute_threat_assessment
from src.monte_carlo_engine import monte_carlo_risk_simulation, sensitivity_analysis
from src.correlation_intelligence import compute_full_correlation_analysis
from src.predictive_engine import compute_predictive_outlook, generate_prediction_narrative
from src.decision_tree_engine import evaluate_all_scenarios as dt_evaluate_all, generate_improvement_roadmap
from src.scenario_wargaming import (
    run_scenario_wargame, get_predefined_scenarios,
    compute_intervention_matrix, generate_wargame_narrative,
)
from src.ensemble_intelligence import compute_ensemble_assessment, generate_executive_verdict
from src.satellite_intelligence import fetch_complete_satellite_profile
from src.next_gen_algorithms import (
    fuzzy_logic_assessment,
    graph_centrality_analysis,
    dbscan_domain_clustering,
    robust_anomaly_ensemble,
)
from src.advanced_algorithms import (
    vikor_compromise_ranking,
    markov_chain_stability,
    entropy_information_analysis,
    pareto_frontier_analysis,
)
from src.palantir_visualizations import (
    create_radar_chart,
    create_sankey_diagram,
    create_waterfall_chart,
    create_sunburst_chart,
    create_transition_heatmap,
    create_pareto_scatter,
)
from src.apex_algorithms import (
    game_theory_analysis,
    cellular_automata_simulation,
    genetic_algorithm_optimizer,
    wavelet_analysis,
)
from src.omniscient_engine import compute_omniscient_assessment, search_and_visualize
from src.palantir_charts_v2 import (
    create_3d_globe,
    create_gauge_dashboard,
    create_bullet_chart,
    create_polar_bar,
    create_ridgeline,
)

logger = logging.getLogger(__name__)


def _hex_rgba(hc, a=1.0):
    """Convert #RRGGBB + alpha float to rgba() for Plotly compatibility."""
    h = hc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"


# ---------------------------------------------------------------------------
# OPS-CENTER PALETTE (mirror of command_center)
# ---------------------------------------------------------------------------
_BG = "#050510"
_PANEL = "#0a0a18"
_GRID = "#0d1225"
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

_SEVERITY_COLORS = {"CRITICAL": _RED, "WARNING": _AMBER, "NOTABLE": _CYAN}


# ═══════════════════════════════════════════════════════════════════════════
# PLOTLY LAYOUT HELPER
# ═══════════════════════════════════════════════════════════════════════════

def _ops_layout(title="", height=350, **kwargs):
    """Return a Plotly layout dict in ops-center dark theme."""
    layout = dict(
        title=dict(text=title, font=dict(color=_TEXT, size=13, family="JetBrains Mono, monospace"),
                   x=0.01, y=0.97) if title else None,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5,5,16,0.6)",
        font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
        height=height,
        margin=dict(l=40, r=20, t=40 if title else 20, b=30),
    )
    layout.update(kwargs)
    return layout


def _gauge_chart(value, title, max_val=100, color=_CYAN, height=180):
    """Small gauge indicator."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title=dict(text=title, font=dict(size=11, color=_DIM)),
        number=dict(font=dict(size=22, color=color)),
        gauge=dict(
            axis=dict(range=[0, max_val], tickfont=dict(size=8, color=_DIM)),
            bar=dict(color=color, thickness=0.7),
            bgcolor=_GRID,
            borderwidth=0,
            steps=[
                dict(range=[0, max_val * 0.3], color="rgba(239,68,68,0.15)"),
                dict(range=[max_val * 0.3, max_val * 0.6], color="rgba(245,158,11,0.10)"),
                dict(range=[max_val * 0.6, max_val], color="rgba(0,240,255,0.08)"),
            ],
        ),
    ))
    fig.update_layout(**_ops_layout(height=height))
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# MAIN RENDERER
# ═══════════════════════════════════════════════════════════════════════════

def render_fusion_console():
    """Render the Fusion Intelligence Console page."""
    init_location_context()

    # ───── SECTION 0: ANIMATED HERO HEADER ─────
    st.markdown(
        '<div class="fusion-hero">'
        '<h1>FUSION INTELLIGENCE CONSOLE</h1>'
        '<p>MULTI-SOURCE EVIDENCE FUSION &amp; DECISION INTELLIGENCE &bull; '
        '34 ANALYTICAL SECTIONS &bull; 35 ALGORITHMS &bull; 40+ DATA SOURCES</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    render_location_selector(key_prefix="fic")

    if not has_location():
        st.info("Select a location above to activate the Fusion Intelligence Console.")
        return

    loc = get_location()
    lat, lon = loc["lat"], loc["lon"]
    loc_name = get_short_name()

    # ───── FETCH DATA ─────
    with st.spinner("Fusing multi-source intelligence..."):
        hub = get_hub_data(lat, lon)
        scores = hub.get("scores", {})
        details = hub.get("details", {})
        raw_data = hub.get("raw_data", {})
        swot = hub.get("swot", {})
        recommendations = hub.get("recommendations", [])
        _conf_raw = hub.get("confidence", 0.5)
        confidence = float(_conf_raw.get("overall", 0.5)) if isinstance(_conf_raw, dict) else float(_conf_raw or 0)

        # Inject real confidence into raw_data so strategic_synthesis can use it
        raw_data["confidence"] = confidence

        analytics = compute_advanced_analytics(scores, details, raw_data)

        # Run 8 fusion algorithms — each wrapped individually so one
        # failure does not crash the entire console.
        try:
            ds = dempster_shafer_fusion(scores, confidence)
        except Exception as exc:
            logger.warning("Dempster-Shafer fusion failed: %s", exc)
            ds = None

        try:
            cascade = risk_propagation_cascade(scores, details)
        except Exception as exc:
            logger.warning("Risk propagation cascade failed: %s", exc)
            cascade = None

        try:
            cvi = composite_vulnerability_index(scores, details, analytics)
        except Exception as exc:
            logger.warning("Composite vulnerability index failed: %s", exc)
            cvi = None

        try:
            anomalies = anomaly_severity_ranking(scores, details, analytics)
        except Exception as exc:
            logger.warning("Anomaly severity ranking failed: %s", exc)
            anomalies = None

        try:
            trends = temporal_trend_synthesis(raw_data, analytics, scores)
        except Exception as exc:
            logger.warning("Temporal trend synthesis failed: %s", exc)
            trends = None

        try:
            ahp = ahp_priority_synthesis(scores)
        except Exception as exc:
            logger.warning("AHP priority synthesis failed: %s", exc)
            ahp = None

        # Decision scenarios
        try:
            scenario_results = _build_scenario_results(lat, lon)
        except Exception as exc:
            logger.warning("Scenario results build failed: %s", exc)
            scenario_results = {}

        try:
            topsis = topsis_scenario_ranking(scenario_results, scores)
        except Exception as exc:
            logger.warning("TOPSIS ranking failed: %s", exc)
            topsis = None

        try:
            electre = electre_outranking(scenario_results)
        except Exception as exc:
            logger.warning("ELECTRE outranking failed: %s", exc)
            electre = None

        # Advanced algorithms
        try:
            krig_points, krig_values = prepare_kriging_data(scores, details, raw_data, lat, lon)
            kriging = kriging_interpolation(krig_points, krig_values, grid_size=15)
        except Exception as exc:
            logger.warning("Kriging interpolation failed: %s", exc)
            kriging = None

        try:
            pca = pca_domain_analysis(scores, analytics)
        except Exception as exc:
            logger.warning("PCA domain analysis failed: %s", exc)
            pca = None

        try:
            bbn = bayesian_belief_network(scores, details, analytics)
        except Exception as exc:
            logger.warning("Bayesian belief network failed: %s", exc)
            bbn = None

        # Strategic synthesis & threat radar
        try:
            strategic = compute_strategic_assessment(
                scores, details, analytics, ds, cascade, cvi,
                anomalies, trends, topsis, bbn, raw_data,
            )
        except Exception as exc:
            logger.warning("Strategic assessment failed: %s", exc)
            strategic = None

        try:
            threats = compute_threat_assessment(raw_data, details, scores)
        except Exception as exc:
            logger.warning("Threat assessment failed: %s", exc)
            threats = None

        # Monte Carlo risk simulation
        try:
            mc_sim = monte_carlo_risk_simulation(scores, confidence)
        except Exception as exc:
            logger.warning("Monte Carlo simulation failed: %s", exc)
            mc_sim = None

        try:
            mc_sensitivity = sensitivity_analysis(scores, confidence)
        except Exception as exc:
            logger.warning("Sensitivity analysis failed: %s", exc)
            mc_sensitivity = None

        # Cross-domain correlation intelligence
        try:
            corr_intel = compute_full_correlation_analysis(scores, details, raw_data)
        except Exception as exc:
            logger.warning("Correlation analysis failed: %s", exc)
            corr_intel = None

        # Predictive analytics
        try:
            predictive = compute_predictive_outlook(scores, details, analytics, raw_data)
        except Exception as exc:
            logger.warning("Predictive outlook failed: %s", exc)
            predictive = None

        # Decision trees
        try:
            dt_results = dt_evaluate_all(scores)
        except Exception as exc:
            logger.warning("Decision tree evaluation failed: %s", exc)
            dt_results = None

        try:
            dt_roadmap = generate_improvement_roadmap(dt_results, scores) if dt_results else None
        except Exception as exc:
            logger.warning("Improvement roadmap generation failed: %s", exc)
            dt_roadmap = None

        # Scenario wargaming
        try:
            wg_scenarios = get_predefined_scenarios()
        except Exception as exc:
            logger.warning("Predefined scenarios failed: %s", exc)
            wg_scenarios = None

        try:
            wg_intervention = compute_intervention_matrix(scores)
        except Exception as exc:
            logger.warning("Intervention matrix failed: %s", exc)
            wg_intervention = None

        # Satellite intelligence
        try:
            satellite_profile = fetch_complete_satellite_profile(lat, lon)
        except Exception as exc:
            logger.warning("Satellite intelligence failed: %s", exc)
            satellite_profile = None

        # Next-gen algorithms
        try:
            ng_fuzzy = fuzzy_logic_assessment(scores, details)
        except Exception as exc:
            logger.warning("Fuzzy logic assessment failed: %s", exc)
            ng_fuzzy = None

        try:
            ng_graph = graph_centrality_analysis(scores, details, analytics)
        except Exception as exc:
            logger.warning("Graph centrality analysis failed: %s", exc)
            ng_graph = None

        try:
            ng_clustering = dbscan_domain_clustering(scores, details)
        except Exception as exc:
            logger.warning("DBSCAN clustering failed: %s", exc)
            ng_clustering = None

        try:
            ng_anomaly = robust_anomaly_ensemble(scores, details, analytics)
        except Exception as exc:
            logger.warning("Robust anomaly ensemble failed: %s", exc)
            ng_anomaly = None

        # Phase 3 algorithms
        try:
            adv_vikor = vikor_compromise_ranking(scores)
        except Exception as exc:
            logger.warning("VIKOR ranking failed: %s", exc)
            adv_vikor = None

        try:
            adv_markov = markov_chain_stability(scores)
        except Exception as exc:
            logger.warning("Markov chain stability failed: %s", exc)
            adv_markov = None

        try:
            adv_entropy = entropy_information_analysis(scores, details)
        except Exception as exc:
            logger.warning("Entropy analysis failed: %s", exc)
            adv_entropy = None

        try:
            adv_pareto = pareto_frontier_analysis(scores, details)
        except Exception as exc:
            logger.warning("Pareto frontier failed: %s", exc)
            adv_pareto = None

        # Phase 4 — Apex algorithms
        try:
            apex_game = game_theory_analysis(scores, details)
        except Exception as exc:
            logger.warning("Game theory analysis failed: %s", exc)
            apex_game = None

        try:
            apex_ca = cellular_automata_simulation(scores, details)
        except Exception as exc:
            logger.warning("Cellular automata failed: %s", exc)
            apex_ca = None

        try:
            apex_ga = genetic_algorithm_optimizer(scores, details)
        except Exception as exc:
            logger.warning("Genetic algorithm failed: %s", exc)
            apex_ga = None

        try:
            apex_wavelet = wavelet_analysis(scores, details)
        except Exception as exc:
            logger.warning("Wavelet analysis failed: %s", exc)
            apex_wavelet = None

        # Ensemble meta-assessment (combines everything)
        try:
            ensemble = compute_ensemble_assessment(
                hub_data=hub,
                strategic=strategic,
                threats=threats,
                mc_result=mc_sim,
                corr_intel=corr_intel,
                predictive=predictive,
                dt_results=dt_results,
                wargaming_intervention=wg_intervention,
                bbn=bbn,
                pca=pca,
                kriging=kriging,
            )
        except Exception as exc:
            logger.warning("Ensemble assessment failed: %s", exc)
            ensemble = None

        # Omniscient synthesis (combines ALL algorithm results)
        try:
            omniscient = compute_omniscient_assessment(hub, {
                "ds_fusion": ds, "topsis": topsis, "cascade": cascade,
                "cvi": cvi, "anomalies": anomalies, "trends": trends,
                "strategic": strategic, "threats": threats, "mc_sim": mc_sim,
                "correlation": corr_intel, "predictive": predictive,
                "decision_trees": dt_results, "wargaming": wg_intervention,
                "bbn": bbn, "pca": pca, "kriging": kriging,
                "fuzzy": ng_fuzzy, "graph_centrality": ng_graph,
                "clustering": ng_clustering, "anomaly_ensemble": ng_anomaly,
                "ensemble": ensemble,
                "vikor": adv_vikor, "markov": adv_markov,
                "entropy": adv_entropy, "pareto": adv_pareto,
                "game_theory": apex_game, "cellular_automata": apex_ca,
                "genetic_algorithm": apex_ga, "wavelet": apex_wavelet,
            })
        except Exception as exc:
            logger.warning("Omniscient assessment failed: %s", exc)
            omniscient = None

    # ───── D-S BADGE ─────
    belief_pct = (ds["fused_belief"] * 100) if ds else 0
    badge_color = _GREEN if belief_pct >= 65 else (_AMBER if belief_pct >= 40 else _RED)
    if ds:
        st.markdown(
            f'<div style="text-align:center;padding:12px;margin:0.5rem 0 1rem 0;'
            f'border:1px solid {badge_color}33;border-radius:8px;'
            f'background:{badge_color}0a;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_DIM};letter-spacing:1px;">DEMPSTER-SHAFER FUSED BELIEF</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:2rem;'
            f'font-weight:700;color:{badge_color};">{belief_pct:.1f}%</span>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.7rem;'
            f'color:{_DIM};margin-left:8px;">for {html_module.escape(loc_name)}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("Dempster-Shafer fusion unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # INTELLIGENCE MAP — Interactive multi-layer geospatial visualization
    # ═══════════════════════════════════════════════════════════════════════
    try:
        from src.intelligence_map import build_intelligence_map
        st.markdown(
            f'<div style="font-size:0.72rem;color:{_DIM};letter-spacing:2px;margin:18px 0 8px">'
            f'INTERACTIVE INTELLIGENCE MAP</div>',
            unsafe_allow_html=True,
        )
        build_intelligence_map(lat, lon, hub, height=500)
    except Exception as exc:
        logger.warning("Intelligence map failed: %s", exc)

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 1: SITUATION ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("1", "SITUATION ASSESSMENT", _CYAN)

    # Situation status
    _cascade_systemic = cascade["systemic_score"] if cascade else 50
    if belief_pct >= 70 and _cascade_systemic < 30:
        sit_status, sit_color = "FAVORABLE", _GREEN
    elif belief_pct >= 45 and _cascade_systemic < 55:
        sit_status, sit_color = "MARGINAL", _AMBER
    elif belief_pct >= 25:
        sit_status, sit_color = "ADVERSE", "#ff8800"
    else:
        sit_status, sit_color = "CRITICAL", _RED

    st.markdown(
        f'<div style="text-align:center;padding:8px;border:1px solid {sit_color}44;'
        f'border-radius:6px;background:{sit_color}0d;margin-bottom:0.8rem;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
        f'color:{_DIM};">SITUATION STATUS</span>&nbsp;&nbsp;'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:1.1rem;'
        f'font-weight:700;color:{sit_color};letter-spacing:2px;">{sit_status}</span></div>',
        unsafe_allow_html=True,
    )

    # 5 metric strip
    _cvi_score = cvi["cvi_score"] if cvi else 0
    _anomaly_count = len(anomalies) if anomalies else 0
    m1, m2, m3, m4, m5 = st.columns(5)
    _metric_card(m1, "Fused Belief", f"{belief_pct:.1f}%", badge_color)
    _metric_card(m2, "Systemic Risk", f"{_cascade_systemic:.0f}",
                 _RED if _cascade_systemic > 50 else _AMBER)
    _metric_card(m3, "CVI Score", f"{_cvi_score:.2f}",
                 _RED if _cvi_score > 0.5 else _CYAN)
    _metric_card(m4, "Confidence", f"{confidence:.0%}", _CYAN)
    _metric_card(m5, "Anomalies", str(_anomaly_count),
                 _RED if _anomaly_count > 3 else _AMBER if _anomaly_count else _GREEN)

    # Gauges row
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(_gauge_chart(belief_pct, "Fused Belief", 100, badge_color, 200),
                        use_container_width=True, key="fic_gauge_belief")
    with g2:
        st.plotly_chart(_gauge_chart(_cascade_systemic, "Systemic Risk", 100, _RED, 200),
                        use_container_width=True, key="fic_gauge_risk")

    # Bullet chart: 10 domains with Monte Carlo CI bands
    mc = analytics.get("monte_carlo", {})
    _render_domain_bullet_chart(scores, mc)

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 2: EVIDENCE FUSION MATRIX
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("2", "EVIDENCE FUSION MATRIX", _PURPLE)
    if ds:
        _render_conflict_heatmap(ds, scores)
        _render_belief_vs_plausibility(ds, scores)
    else:
        st.warning("Evidence fusion matrix unavailable — Dempster-Shafer failed.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 3: THREAT CASCADE ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("3", "THREAT CASCADE ANALYSIS", _RED)
    if cascade:
        _render_cascade_sankey(cascade, scores)

        # Amplification table
        with st.expander("AMPLIFICATION FACTORS", expanded=False):
            amp = cascade.get("amplification", {})
            if amp:
                rows = sorted(amp.items(), key=lambda x: x[1], reverse=True)
                header = "| Domain | Amplification | Cascade Risk | Standalone |"
                sep = "|--------|--------------|-------------|------------|"
                lines = [header, sep]
                for d, a in rows:
                    cr = cascade["cascade_risk"].get(d, 0) * 100
                    sr = cascade["standalone_risk"].get(d, 0) * 100
                    dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
                    amp_str = f"**{a:.2f}x**" if a > 1.1 else f"{a:.2f}x"
                    lines.append(f"| {dname} | {amp_str} | {cr:.0f}% | {sr:.0f}% |")
                st.markdown("\n".join(lines))

        # Systemic risk gauge
        s1, s2 = st.columns([2, 3])
        with s1:
            st.plotly_chart(_gauge_chart(cascade["systemic_score"], "SYSTEMIC RISK", 100, _RED, 200),
                            use_container_width=True, key="fic_gauge_systemic")
        with s2:
            chain = cascade.get("most_vulnerable_chain", [])
            if chain:
                chain_names = [INTELLIGENCE_DOMAINS.get(d, {}).get("name", d) for d in chain]
                chain_str = " -> ".join(chain_names)
                st.markdown(
                    f'<div style="padding:12px;border:1px solid {_RED}33;border-radius:6px;'
                    f'background:{_RED}08;margin-top:0.5rem;">'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
                    f'color:{_DIM};letter-spacing:1px;">MOST VULNERABLE CHAIN</span><br/>'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:0.85rem;'
                    f'color:{_RED};">{chain_str}</span></div>',
                    unsafe_allow_html=True,
                )
    else:
        st.warning("Threat cascade analysis unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 4: DECISION INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("4", "DECISION INTELLIGENCE", _GREEN)
    if topsis is not None or electre is not None or ahp is not None:
        _render_decision_intelligence(topsis, electre, ahp, scenario_results, scores)
    else:
        st.warning("Decision intelligence unavailable — TOPSIS/ELECTRE/AHP all failed.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 5: VULNERABILITY PROFILE
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("5", "VULNERABILITY PROFILE", _AMBER)
    if cvi:
        _render_vulnerability_profile(cvi)
    else:
        st.warning("Vulnerability profile unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 6: ANOMALY INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("6", "ANOMALY INTELLIGENCE", "#ff66aa")
    if anomalies is not None:
        _render_anomaly_intelligence(anomalies)
    else:
        st.warning("Anomaly intelligence unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 7: TEMPORAL OUTLOOK
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("7", "TEMPORAL OUTLOOK", _BLUE)
    if trends is not None:
        _render_temporal_outlook(trends, analytics, scores)
    else:
        st.warning("Temporal outlook unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 8: INTELLIGENCE SUMMARY
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("8", "INTELLIGENCE SUMMARY", _CYAN)
    _render_intelligence_summary(
        ds, cascade, cvi, anomalies, trends, topsis, electre, ahp,
        swot, recommendations, scores, loc_name, confidence,
    )

    # Section divider
    st.markdown('<div class="fusion-section-divider"></div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 9: GEOSPATIAL KRIGING
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("9", "GEOSPATIAL KRIGING INTERPOLATION", _PURPLE)
    if kriging:
        _render_kriging_section(kriging, lat, lon)
    else:
        st.warning("Geospatial kriging unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 10: FACTOR ANALYSIS (PCA)
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("10", "FACTOR ANALYSIS (PCA)", _BLUE)
    if pca:
        _render_pca_section(pca)
    else:
        st.warning("PCA factor analysis unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 11: CAUSAL NETWORK & WHAT-IF
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("11", "CAUSAL NETWORK & WHAT-IF SIMULATION", _PURPLE)
    if bbn:
        _render_bayesian_section(bbn, scores)
    else:
        st.warning("Bayesian belief network unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 12: ACTIVE THREATS (GDACS + OpenAQ)
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("12", "ACTIVE THREATS & ENVIRONMENTAL MONITORING", _RED)
    _render_active_threats_section(details, raw_data)

    # Section divider
    st.markdown('<div class="fusion-section-divider"></div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 13: THREAT RADAR
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("13", "UNIFIED THREAT RADAR", _RED)
    if threats:
        _render_threat_radar_section(threats)
    else:
        st.warning("Threat radar unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 14: STRATEGIC SYNTHESIS
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("14", "STRATEGIC INTELLIGENCE SYNTHESIS", _GREEN)
    if strategic:
        _render_strategic_synthesis_section(strategic, scores)
    else:
        st.warning("Strategic synthesis unavailable.")

    # Section divider
    st.markdown('<div class="fusion-section-divider"></div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 15: MONTE CARLO RISK SIMULATION
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("15", "MONTE CARLO RISK SIMULATION", _PURPLE)
    if mc_sim is not None or mc_sensitivity is not None:
        _render_monte_carlo_section(mc_sim, mc_sensitivity)
    else:
        st.warning("Monte Carlo risk simulation unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 16: CROSS-DOMAIN CORRELATION INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("16", "CROSS-DOMAIN CORRELATION INTELLIGENCE", _CYAN)
    if corr_intel:
        _render_correlation_section(corr_intel, scores)
    else:
        st.warning("Cross-domain correlation intelligence unavailable.")

    # Section divider
    st.markdown('<div class="fusion-section-divider"></div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 17: PREDICTIVE ANALYTICS
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("17", "PREDICTIVE ANALYTICS & FORECASTING", _BLUE)
    if predictive:
        _render_predictive_section(predictive, scores)
    else:
        st.warning("Predictive analytics unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 18: DECISION TREES
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("18", "DECISION TREE ASSESSMENT", _GREEN)
    if dt_results is not None:
        _render_decision_tree_section(dt_results, dt_roadmap, scores)
    else:
        st.warning("Decision tree assessment unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 19: SCENARIO WARGAMING
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("19", "SCENARIO WARGAMING & INTERVENTION", _RED)
    if wg_scenarios is not None or wg_intervention is not None:
        _render_wargaming_section(scores, wg_scenarios, wg_intervention)
    else:
        st.warning("Scenario wargaming unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 20: SATELLITE INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("20", "SATELLITE INTELLIGENCE", _GREEN)
    if satellite_profile is not None:
        _render_satellite_section(satellite_profile)
    else:
        st.warning("Satellite intelligence unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 21: ENSEMBLE META-ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("21", "ENSEMBLE META-ASSESSMENT", _CYAN)
    if ensemble is not None:
        _render_ensemble_section(ensemble)
    else:
        st.warning("Ensemble meta-assessment unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 22: FUZZY LOGIC ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("22", "FUZZY LOGIC ASSESSMENT", _GREEN)
    if ng_fuzzy:
        _render_fuzzy_section(ng_fuzzy)
    else:
        st.warning("Fuzzy logic assessment unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 23: GRAPH CENTRALITY & INFLUENCE NETWORK
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("23", "GRAPH CENTRALITY & INFLUENCE NETWORK", _BLUE)
    if ng_graph:
        _render_graph_centrality_section(ng_graph)
    else:
        st.warning("Graph centrality analysis unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 24: DOMAIN CLUSTERING (DBSCAN)
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("24", "DOMAIN CLUSTERING (DBSCAN)", _PURPLE)
    if ng_clustering:
        _render_clustering_section(ng_clustering, scores)
    else:
        st.warning("DBSCAN clustering unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 25: ROBUST ANOMALY DETECTION
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("25", "ROBUST ANOMALY DETECTION", _RED)
    if ng_anomaly:
        _render_robust_anomaly_section(ng_anomaly)
    else:
        st.warning("Robust anomaly detection unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 26: VIKOR COMPROMISE RANKING
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("26", "VIKOR COMPROMISE RANKING", _AMBER)
    if adv_vikor:
        _render_vikor_section(adv_vikor)
    else:
        st.warning("VIKOR compromise ranking unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 27: MARKOV CHAIN STABILITY
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("27", "MARKOV CHAIN STABILITY", _CYAN)
    if adv_markov:
        _render_markov_section(adv_markov)
    else:
        st.warning("Markov chain stability unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 28: ENTROPY & INFORMATION ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("28", "ENTROPY & INFORMATION ANALYSIS", _PURPLE)
    if adv_entropy:
        _render_entropy_section(adv_entropy)
    else:
        st.warning("Entropy information analysis unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 29: PARETO FRONTIER OPTIMIZATION
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("29", "PARETO FRONTIER OPTIMIZATION", _GREEN)
    if adv_pareto:
        _render_pareto_section(adv_pareto)
    else:
        st.warning("Pareto frontier analysis unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 30: GAME THEORY — NASH EQUILIBRIUM & SHAPLEY VALUES
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("30", "GAME THEORY — NASH EQUILIBRIUM & SHAPLEY VALUES", _PURPLE)
    if apex_game:
        _render_game_theory_section(apex_game, scores)
    else:
        st.warning("Game theory analysis unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 31: CELLULAR AUTOMATA EVOLUTION
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("31", "CELLULAR AUTOMATA EVOLUTION SIMULATION", _AMBER)
    if apex_ca:
        _render_cellular_automata_section(apex_ca)
    else:
        st.warning("Cellular automata simulation unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 32: GENETIC ALGORITHM OPTIMIZER
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("32", "GENETIC ALGORITHM RESOURCE OPTIMIZER", _GREEN)
    if apex_ga:
        _render_genetic_algorithm_section(apex_ga, scores)
    else:
        st.warning("Genetic algorithm optimization unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 33: WAVELET MULTI-RESOLUTION ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("33", "WAVELET MULTI-RESOLUTION ANALYSIS", _CYAN)
    if apex_wavelet:
        _render_wavelet_section(apex_wavelet)
    else:
        st.warning("Wavelet analysis unavailable.")

    # ═══════════════════════════════════════════════════════════════════════
    # SECTION 34: OMNISCIENT INTELLIGENCE SYNTHESIS
    # ═══════════════════════════════════════════════════════════════════════
    _section_header("34", "OMNISCIENT INTELLIGENCE SYNTHESIS", _GREEN)
    if omniscient:
        _render_omniscient_section(omniscient, scores, details=details,
                                   raw_data=raw_data)
    else:
        st.warning("Omniscient synthesis unavailable.")


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _section_header(num, title, color):
    st.markdown(
        f'<div style="border-left:3px solid {color};padding:8px 16px;margin:1.2rem 0 0.6rem 0;'
        f'background:{color}08;border-radius:0 6px 6px 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
        f'color:{_DIM};">[{num}]</span>&nbsp;'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.9rem;'
        f'font-weight:700;color:{color};letter-spacing:1.5px;">{title}</span></div>',
        unsafe_allow_html=True,
    )


def _metric_card(col, label, value, color):
    col.markdown(
        f'<div style="text-align:center;padding:8px 4px;border:1px solid {color}22;'
        f'border-radius:6px;background:{color}08;">'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:0.58rem;'
        f'color:{_DIM};letter-spacing:0.5px;">{label}</div>'
        f'<div style="font-family:JetBrains Mono,monospace;font-size:1.1rem;'
        f'font-weight:700;color:{color};">{value}</div></div>',
        unsafe_allow_html=True,
    )


def _build_scenario_results(lat, lon):
    """Evaluate all decision scenarios and return results dict."""
    try:
        data = _collect_location_data(lat, lon)
    except Exception:
        return {}
    results = {}
    for sk in DECISION_SCENARIOS:
        try:
            r = _evaluate_scenario(
                sk, lat, lon,
                data.get("soil", {}),
                data.get("weather", {}),
                data.get("water", {}),
                data.get("elevation", {}),
                data.get("infrastructure", {}),
                data.get("protected", {}),
                data.get("species", {}),
                data.get("earthquakes", {}),
            )
            results[sk] = r
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# SECTION 1 HELPERS
# ---------------------------------------------------------------------------

def _render_domain_bullet_chart(scores, mc):
    """Horizontal bullet chart: 10 domains with Monte Carlo 90% CI."""
    domains = sorted(scores.keys())
    if not domains:
        return

    names = [INTELLIGENCE_DOMAINS.get(d, {}).get("name", d) for d in domains]
    vals = [scores.get(d, 0) for d in domains]
    colors = [_DOMAIN_COLORS.get(d, _CYAN) for d in domains]

    fig = go.Figure()

    # CI bands
    for i, d in enumerate(domains):
        mc_d = mc.get(d, {})
        ci5 = mc_d.get("ci_5", vals[i] - 5)
        ci95 = mc_d.get("ci_95", vals[i] + 5)
        fig.add_trace(go.Bar(
            y=[names[i]], x=[ci95 - ci5], base=ci5,
            orientation="h", marker=dict(color=colors[i], opacity=0.15),
            showlegend=False, hoverinfo="skip",
        ))

    # Score bars
    fig.add_trace(go.Bar(
        y=names, x=vals, orientation="h",
        marker=dict(color=colors, opacity=0.8),
        text=[f"{v:.0f}" for v in vals], textposition="outside",
        textfont=dict(size=9, color=_TEXT),
        showlegend=False,
    ))

    fig.update_layout(**_ops_layout(
        "DOMAIN SCORES (with 90% Monte Carlo CI)", height=350,
        xaxis=dict(range=[0, 105], gridcolor=_GRID, zeroline=False),
        yaxis=dict(autorange="reversed"),
        barmode="overlay",
    ))
    st.plotly_chart(fig, use_container_width=True, key="fic_bullet_domains")


# ---------------------------------------------------------------------------
# SECTION 2 HELPERS
# ---------------------------------------------------------------------------

def _render_conflict_heatmap(ds, scores):
    """10x10 D-S conflict heatmap."""
    domains = sorted(scores.keys())
    n = len(domains)
    if n < 2:
        return

    names = [INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)[:12] for d in domains]
    matrix = []
    for i, d1 in enumerate(domains):
        row = []
        for j, d2 in enumerate(domains):
            if i == j:
                row.append(0)
            else:
                row.append(ds["conflict_matrix"].get((d1, d2), 0))
        matrix.append(row)

    fig = go.Figure(go.Heatmap(
        z=matrix, x=names, y=names,
        colorscale=[[0, "#0d1225"], [0.3, "#06b6d4"], [0.6, "#f59e0b"], [1.0, "#ef4444"]],
        text=[[f"{v:.2f}" for v in row] for row in matrix],
        texttemplate="%{text}", textfont=dict(size=8),
        hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Conflict: %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(**_ops_layout("D-S CONFLICT MATRIX", height=400))
    st.plotly_chart(fig, use_container_width=True, key="fic_conflict_heatmap")

    # Top 3 conflicts
    conflict_pairs = sorted(
        [(k, v) for k, v in ds["conflict_matrix"].items()],
        key=lambda x: x[1], reverse=True,
    )
    seen = set()
    top_conflicts = []
    for (d1, d2), val in conflict_pairs:
        pair = tuple(sorted([d1, d2]))
        if pair not in seen:
            seen.add(pair)
            top_conflicts.append((d1, d2, val))
        if len(top_conflicts) >= 3:
            break

    if top_conflicts:
        st.markdown(
            f'<div style="padding:10px;border:1px solid {_AMBER}33;border-radius:6px;'
            f'background:{_AMBER}08;margin-bottom:0.8rem;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_AMBER};letter-spacing:1px;">CONFLICTING SIGNALS</span></div>',
            unsafe_allow_html=True,
        )
        for d1, d2, val in top_conflicts:
            n1 = INTELLIGENCE_DOMAINS.get(d1, {}).get("name", d1)
            n2 = INTELLIGENCE_DOMAINS.get(d2, {}).get("name", d2)
            st.markdown(
                f"- **{n1}** vs **{n2}** — conflict coefficient: `{val:.3f}`"
            )


def _render_belief_vs_plausibility(ds, scores):
    """Bar chart: Belief vs Plausibility per domain."""
    db = ds.get("domain_beliefs", {})
    if not db:
        return

    domains = sorted(db.keys())
    names = [INTELLIGENCE_DOMAINS.get(d, {}).get("name", d) for d in domains]
    beliefs = [db[d]["belief"] * 100 for d in domains]
    plaus = [db[d]["plausibility"] * 100 for d in domains]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Belief", y=names, x=beliefs, orientation="h",
        marker=dict(color=_CYAN, opacity=0.8),
    ))
    fig.add_trace(go.Bar(
        name="Plausibility", y=names, x=plaus, orientation="h",
        marker=dict(color=_PURPLE, opacity=0.4),
    ))
    fig.update_layout(**_ops_layout(
        "BELIEF vs PLAUSIBILITY (gap = uncertainty)", height=350,
        barmode="overlay",
        xaxis=dict(range=[0, 105], gridcolor=_GRID),
        yaxis=dict(autorange="reversed"),
        legend=dict(font=dict(size=9, color=_DIM), bgcolor="rgba(0,0,0,0)"),
    ))
    st.plotly_chart(fig, use_container_width=True, key="fic_belief_plaus")


# ---------------------------------------------------------------------------
# SECTION 3 HELPERS
# ---------------------------------------------------------------------------

def _render_cascade_sankey(cascade, scores):
    """Sankey diagram: risk propagation between domains."""
    from src.fusion_engine import _CASCADE_GRAPH

    domains = sorted(scores.keys())
    dom_idx = {d: i for i, d in enumerate(domains)}
    labels = [INTELLIGENCE_DOMAINS.get(d, {}).get("name", d) for d in domains]
    node_colors = []
    for d in domains:
        r = cascade["cascade_risk"].get(d, 0)
        if r > 0.5:
            node_colors.append(_RED)
        elif r > 0.3:
            node_colors.append(_AMBER)
        else:
            node_colors.append(_CYAN)

    sources, targets, values, link_colors = [], [], [], []
    for src_domain, tgt_list in _CASCADE_GRAPH.items():
        si = dom_idx.get(src_domain)
        if si is None:
            continue
        for tgt in tgt_list:
            ti = dom_idx.get(tgt)
            if ti is None:
                continue
            risk_val = cascade["cascade_risk"].get(src_domain, 0)
            flow = max(risk_val * 10, 0.5)
            sources.append(si)
            targets.append(ti)
            values.append(round(flow, 2))
            if risk_val > 0.5:
                link_colors.append("rgba(255,51,68,0.4)")
            elif risk_val > 0.3:
                link_colors.append("rgba(255,170,0,0.3)")
            else:
                link_colors.append("rgba(0,240,255,0.2)")

    if not sources:
        st.caption("No cascade links to display.")
        return

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15, thickness=18, label=labels,
            color=node_colors,
            line=dict(color=_GRID, width=0.5),
        ),
        link=dict(
            source=sources, target=targets, value=values,
            color=link_colors,
        ),
    ))
    fig.update_layout(**_ops_layout("RISK PROPAGATION CASCADE", height=420))
    st.plotly_chart(fig, use_container_width=True, key="fic_sankey_cascade")


# ---------------------------------------------------------------------------
# SECTION 4 HELPERS
# ---------------------------------------------------------------------------

def _render_decision_intelligence(topsis, electre, ahp, scenario_results, scores):
    """TOPSIS ranking, ELECTRE kernel, AHP weights."""

    # AHP Treemap
    ahp_weights = ahp.get("weights", {})
    if ahp_weights:
        labels_ahp = []
        values_ahp = []
        colors_ahp = []
        for d, w in sorted(ahp_weights.items(), key=lambda x: x[1], reverse=True):
            labels_ahp.append(INTELLIGENCE_DOMAINS.get(d, {}).get("name", d))
            values_ahp.append(w)
            colors_ahp.append(_DOMAIN_COLORS.get(d, _CYAN))

        fig_tree = go.Figure(go.Treemap(
            labels=labels_ahp,
            parents=[""] * len(labels_ahp),
            values=values_ahp,
            marker=dict(colors=colors_ahp),
            texttemplate="<b>%{label}</b><br>%{value:.1%}",
            textfont=dict(size=11),
        ))
        fig_tree.update_layout(**_ops_layout("AHP PRIORITY WEIGHTS", height=300))
        st.plotly_chart(fig_tree, use_container_width=True, key="fic_ahp_treemap")

        cr = ahp.get("consistency_ratio", 0)
        cr_ok = cr < 0.10
        st.markdown(
            f"Consistency Ratio: `{cr:.4f}` — {'CONSISTENT' if cr_ok else 'INCONSISTENT (CR > 0.10)'}"
        )

    if not topsis:
        st.caption("No scenario data available for TOPSIS/ELECTRE analysis.")
        return

    # TOPSIS table
    kernel = set(electre.get("kernel", []))
    st.markdown(
        f'<div style="padding:8px;border:1px solid {_GREEN}33;border-radius:6px;'
        f'background:{_GREEN}08;margin:0.6rem 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
        f'color:{_GREEN};letter-spacing:1px;">SCENARIO RANKING (TOPSIS + ELECTRE)</span></div>',
        unsafe_allow_html=True,
    )

    header = "| Rank | Scenario | TOPSIS C* | Simple Score | Verdict | ELECTRE |"
    sep = "|------|----------|-----------|-------------|---------|---------|"
    lines = [header, sep]
    for r in topsis:
        sk = r["scenario"]
        sc_name = DECISION_SCENARIOS.get(sk, {}).get("name", sk)
        sc_icon = DECISION_SCENARIOS.get(sk, {}).get("icon", "")
        ov = r.get("overall", 0)
        if ov >= VERDICT_GO:
            verdict = "GO"
        elif ov >= VERDICT_CAUTION:
            verdict = "CAUTION"
        else:
            verdict = "NO-GO"
        in_kernel = "KERNEL" if sk in kernel else ""
        lines.append(
            f"| {r['rank']} | {sc_icon} {sc_name} | {r['closeness']:.3f} | {r['simple_score']:.0f} | {verdict} | {in_kernel} |"
        )
    st.markdown("\n".join(lines))

    # Bar chart: TOPSIS vs Simple score
    fig_comp = go.Figure()
    scenario_names = [DECISION_SCENARIOS.get(r["scenario"], {}).get("name", r["scenario"])[:18] for r in topsis]
    fig_comp.add_trace(go.Bar(
        name="TOPSIS C*", x=scenario_names,
        y=[r["closeness"] * 100 for r in topsis],
        marker=dict(color=_CYAN),
    ))
    fig_comp.add_trace(go.Bar(
        name="Simple Avg", x=scenario_names,
        y=[r["simple_score"] for r in topsis],
        marker=dict(color=_DIM),
    ))
    fig_comp.update_layout(**_ops_layout(
        "TOPSIS vs SIMPLE WEIGHTED (divergence = analytical value)", height=320,
        barmode="group",
        xaxis=dict(tickangle=-30),
        yaxis=dict(title="Score", gridcolor=_GRID),
        legend=dict(font=dict(size=9, color=_DIM), bgcolor="rgba(0,0,0,0)"),
    ))
    st.plotly_chart(fig_comp, use_container_width=True, key="fic_topsis_vs_simple")

    # Top 3 with GO/CAUTION/NO-GO
    st.markdown(
        f'<div style="padding:8px;border:1px solid {_CYAN}33;border-radius:6px;'
        f'background:{_CYAN}08;margin:0.6rem 0;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
        f'color:{_CYAN};letter-spacing:1px;">TOP 3 RECOMMENDATIONS</span></div>',
        unsafe_allow_html=True,
    )
    for r in topsis[:3]:
        sk = r["scenario"]
        sc = DECISION_SCENARIOS.get(sk, {})
        ov = r.get("overall", 0)
        if ov >= VERDICT_GO:
            v_label, v_color = "GO", _GREEN
        elif ov >= VERDICT_CAUTION:
            v_label, v_color = "CAUTION", _AMBER
        else:
            v_label, v_color = "NO-GO", _RED
        conf = r["closeness"] * 100
        in_k = " | ELECTRE KERNEL" if sk in kernel else ""
        st.markdown(
            f"- **{sc.get('icon','')} {sc.get('name', sk)}** — "
            f"<span style='color:{v_color};font-weight:700;'>{v_label}</span> "
            f"(confidence: {conf:.0f}%{in_k})",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# SECTION 5 HELPERS
# ---------------------------------------------------------------------------

def _render_vulnerability_profile(cvi):
    """Radar chart: Exposure, Sensitivity, Adaptive Capacity."""
    exp = cvi["exposure"]
    sens = cvi["sensitivity"]
    ac = cvi["adaptive_capacity"]
    vclass = cvi["vulnerability_class"]

    # Badge
    v_colors = {"LOW": _GREEN, "MODERATE": _AMBER, "HIGH": "#ff8800", "EXTREME": _RED}
    vc = v_colors.get(vclass, _AMBER)
    st.markdown(
        f'<div style="text-align:center;padding:8px;border:1px solid {vc}44;'
        f'border-radius:6px;background:{vc}0d;margin-bottom:0.8rem;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
        f'color:{_DIM};">VULNERABILITY CLASS</span>&nbsp;&nbsp;'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:1.1rem;'
        f'font-weight:700;color:{vc};letter-spacing:2px;">{vclass}</span>'
        f'&nbsp;(CVI = {cvi["cvi_score"]:.3f})</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([3, 2])
    with c1:
        fig = go.Figure(go.Scatterpolar(
            r=[exp, sens, ac, exp],
            theta=["Exposure", "Sensitivity", "Adaptive Capacity", "Exposure"],
            fill="toself",
            fillcolor=_hex_rgba(vc, 0.13),
            line=dict(color=vc, width=2),
            marker=dict(size=8, color=vc),
        ))
        fig.update_layout(**_ops_layout(
            "VULNERABILITY DIMENSIONS", height=320,
            polar=dict(
                bgcolor="rgba(5,5,16,0.6)",
                radialaxis=dict(range=[0, 1], gridcolor=_GRID, tickfont=dict(size=8, color=_DIM)),
                angularaxis=dict(gridcolor=_GRID, tickfont=dict(size=10, color=_TEXT)),
            ),
        ))
        st.plotly_chart(fig, use_container_width=True, key="fic_vuln_radar")

    with c2:
        # Weakest link callout
        wl = cvi["weakest_link"]
        wl_label = wl.replace("_", " ").title()
        st.markdown(
            f'<div style="padding:12px;border:1px solid {_RED}33;border-radius:6px;'
            f'background:{_RED}08;margin-top:1rem;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1px;">WEAKEST LINK</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1rem;'
            f'font-weight:700;color:{_RED};">{wl_label}</span></div>',
            unsafe_allow_html=True,
        )

        # Dimension bars
        for label, val, color in [
            ("Exposure", exp, _RED),
            ("Sensitivity", sens, _AMBER),
            ("Adaptive Cap.", ac, _GREEN),
        ]:
            pct = val * 100
            st.markdown(
                f'<div style="margin:6px 0;">'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.62rem;'
                f'color:{_DIM};">{label}</span>'
                f'<div style="background:{_GRID};border-radius:3px;height:8px;margin-top:2px;">'
                f'<div style="background:{color};width:{pct:.0f}%;height:8px;border-radius:3px;">'
                f'</div></div>'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.58rem;'
                f'color:{color};">{val:.2f}</span></div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# SECTION 6 HELPERS
# ---------------------------------------------------------------------------

def _render_anomaly_intelligence(anomalies):
    """Anomaly table and scatter plot."""
    if not anomalies:
        st.caption("No significant anomalies detected (all metrics within normal range).")
        return

    # Table
    header = "| Severity | Metric | Value | Baseline | Z-Score | Domain |"
    sep = "|----------|--------|-------|----------|---------|--------|"
    lines = [header, sep]
    for a in anomalies:
        sev = a["severity"]
        color = _SEVERITY_COLORS.get(sev, _CYAN)
        dname = INTELLIGENCE_DOMAINS.get(a["domain"], {}).get("name", a["domain"])
        lines.append(
            f"| **{sev}** | {a['metric']} | {a['value']} | {a['baseline']} | {a['z_score']:+.1f} | {dname} |"
        )
    st.markdown("\n".join(lines))

    # Top 3 intelligence notes
    for a in anomalies[:3]:
        sev = a["severity"]
        color = _SEVERITY_COLORS.get(sev, _CYAN)
        with st.expander(f"{sev}: {a['metric']} (z={a['z_score']:+.1f})"):
            st.markdown(
                f"**Value**: {a['value']} (baseline: {a['baseline']})\n\n"
                f"**Direction**: {a['direction']} baseline by {a['abs_z']:.1f} standard deviations\n\n"
                f"**Recommended Action**: {a['action']}"
            )

    # Scatter: z-score vs impact weight
    if len(anomalies) >= 2:
        fig = go.Figure()
        for a in anomalies:
            color = _SEVERITY_COLORS.get(a["severity"], _CYAN)
            fig.add_trace(go.Scatter(
                x=[a["abs_z"]], y=[a["impact_weight"]],
                mode="markers+text",
                marker=dict(size=12, color=color, symbol="diamond"),
                text=[a["metric"][:15]],
                textposition="top center",
                textfont=dict(size=8, color=_TEXT),
                showlegend=False,
                hovertemplate=f"<b>{a['metric']}</b><br>Z={a['z_score']:+.1f}<br>Impact={a['impact_weight']:.2f}<extra></extra>",
            ))
        fig.update_layout(**_ops_layout(
            "ANOMALY SEVERITY vs IMPACT", height=320,
            xaxis=dict(title="Z-Score (absolute)", gridcolor=_GRID),
            yaxis=dict(title="Impact Weight", gridcolor=_GRID),
        ))
        # Quadrant lines
        fig.add_hline(y=1.0, line_dash="dot", line_color=_DIM, opacity=0.3)
        fig.add_vline(x=2.5, line_dash="dot", line_color=_DIM, opacity=0.3)
        st.plotly_chart(fig, use_container_width=True, key="fic_anomaly_scatter")


# ---------------------------------------------------------------------------
# SECTION 7 HELPERS
# ---------------------------------------------------------------------------

def _render_temporal_outlook(trends, analytics, scores):
    """Trend sparklines and composite outlook."""
    composite = trends.get("composite_trend", "STABLE")
    t_colors = {"IMPROVING": _GREEN, "STABLE": _CYAN, "DEGRADING": _RED}
    tc = t_colors.get(composite, _CYAN)

    st.markdown(
        f'<div style="text-align:center;padding:8px;border:1px solid {tc}44;'
        f'border-radius:6px;background:{tc}0d;margin-bottom:0.8rem;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
        f'color:{_DIM};">COMPOSITE OUTLOOK</span>&nbsp;&nbsp;'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:1.1rem;'
        f'font-weight:700;color:{tc};letter-spacing:2px;">{composite}</span></div>',
        unsafe_allow_html=True,
    )

    # Domain trend indicators
    dt = trends.get("domain_trends", {})
    trend_icons = {
        "warming": "^", "cooling": "v", "wetter": "^", "drier": "v",
        "drought_prone": "v", "flood_prone": "~", "balanced": "-",
        "increasing_hazard": "!", "decreasing_hazard": "+",
        "stable": "-", "no_data": "?",
    }
    trend_display_colors = {
        "warming": _AMBER, "cooling": _BLUE, "wetter": _CYAN, "drier": _RED,
        "drought_prone": _RED, "flood_prone": _AMBER, "balanced": _GREEN,
        "increasing_hazard": _RED, "decreasing_hazard": _GREEN,
        "stable": _CYAN, "no_data": _DIM,
    }

    cols = st.columns(min(len(dt), 5))
    for i, (d, trend) in enumerate(sorted(dt.items())):
        col = cols[i % len(cols)]
        icon = trend_icons.get(trend, "-")
        color = trend_display_colors.get(trend, _CYAN)
        dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)[:14]
        trend_label = trend.replace("_", " ").title()
        col.markdown(
            f'<div style="text-align:center;padding:6px;border:1px solid {color}22;'
            f'border-radius:4px;margin:2px 0;background:{color}08;">'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
            f'color:{_DIM};">{dname}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:1rem;'
            f'font-weight:700;color:{color};">{icon}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.5rem;'
            f'color:{color};">{trend_label}</div></div>',
            unsafe_allow_html=True,
        )

    # Markov stationary distribution
    markov_stat = trends.get("markov_stationary", [])
    if len(markov_stat) >= 3:
        fig_m = go.Figure(go.Pie(
            labels=["Dry", "Light Rain", "Heavy Rain"],
            values=markov_stat[:3],
            marker=dict(colors=[_AMBER, _CYAN, _BLUE]),
            textinfo="label+percent",
            textfont=dict(size=10, color=_TEXT),
            hole=0.4,
        ))
        fig_m.update_layout(**_ops_layout("MARKOV STATIONARY DISTRIBUTION (Precip.)", height=280))
        st.plotly_chart(fig_m, use_container_width=True, key="fic_markov_pie")

    # Weibull hazard rate
    wk = trends.get("weibull_k", 1.0)
    if wk > 0:
        if wk > 1.2:
            wk_label, wk_color = "INCREASING", _RED
        elif wk < 0.8:
            wk_label, wk_color = "DECREASING", _GREEN
        else:
            wk_label, wk_color = "CONSTANT", _CYAN
        st.markdown(
            f"Seismic Hazard Rate (Weibull k={wk:.2f}): "
            f"<span style='color:{wk_color};font-weight:700;'>{wk_label}</span>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# SECTION 8 HELPERS
# ---------------------------------------------------------------------------

def _render_intelligence_summary(ds, cascade, cvi, anomalies, trends, topsis,
                                 electre, ahp, swot, recommendations, scores,
                                 loc_name, confidence):
    """Final summary: SWOT, conclusions, next steps, export."""

    # SWOT 2x2
    if swot:
        st.markdown(
            f'<div style="padding:8px;border:1px solid {_CYAN}33;border-radius:6px;'
            f'background:{_CYAN}08;margin:0.4rem 0;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_CYAN};letter-spacing:1px;">SWOT ANALYSIS</span></div>',
            unsafe_allow_html=True,
        )
        s1, s2 = st.columns(2)
        with s1:
            st.markdown(f"**Strengths**")
            for s in (swot.get("strengths") or [])[:5]:
                st.markdown(f"- {s}")
            st.markdown(f"**Opportunities**")
            for o in (swot.get("opportunities") or [])[:5]:
                st.markdown(f"- {o}")
        with s2:
            st.markdown(f"**Weaknesses**")
            for w in (swot.get("weaknesses") or [])[:5]:
                st.markdown(f"- {w}")
            st.markdown(f"**Threats**")
            for t in (swot.get("threats") or [])[:5]:
                st.markdown(f"- {t}")

    # Top 5 actionable conclusions
    conclusions = _generate_conclusions(ds, cascade, cvi, anomalies, trends, topsis, scores, confidence)
    if conclusions:
        st.markdown(
            f'<div style="padding:8px;border:1px solid {_GREEN}33;border-radius:6px;'
            f'background:{_GREEN}08;margin:0.6rem 0;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_GREEN};letter-spacing:1px;">TOP 5 ACTIONABLE CONCLUSIONS</span></div>',
            unsafe_allow_html=True,
        )
        for i, (text, conf) in enumerate(conclusions[:5], 1):
            st.markdown(f"**{i}.** {text} *(confidence: {conf:.0f}%)*")

    # Next steps
    if recommendations:
        st.markdown(
            f'<div style="padding:8px;border:1px solid {_BLUE}33;border-radius:6px;'
            f'background:{_BLUE}08;margin:0.6rem 0;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_BLUE};letter-spacing:1px;">RECOMMENDED NEXT STEPS</span></div>',
            unsafe_allow_html=True,
        )
        for i, rec in enumerate(recommendations[:5], 1):
            if isinstance(rec, str):
                st.markdown(f"**{i}.** {rec}")
            elif isinstance(rec, dict):
                st.markdown(f"**{i}.** {rec.get('text', rec.get('recommendation', str(rec)))}")

    # Export
    report = _build_export_report(
        ds, cascade, cvi, anomalies, trends, topsis, electre, ahp,
        swot, recommendations, scores, loc_name, confidence, conclusions,
    )
    st.download_button(
        "Download Intelligence Report (.md)",
        data=report,
        file_name=f"fusion_report_{loc_name.replace(' ', '_').replace(',', '')}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
        mime="text/markdown",
        key="fic_download_report",
    )


# ---------------------------------------------------------------------------
# SECTION 9 HELPERS — KRIGING
# ---------------------------------------------------------------------------

def _render_kriging_section(kriging, lat, lon):
    """Render Kriging interpolation heatmap with variance overlay."""
    estimates = kriging.get("estimates", [])
    variance = kriging.get("variance", [])
    vario = kriging.get("semivariogram", {})

    if not estimates or not estimates[0]:
        st.caption("Insufficient spatial data for Kriging interpolation.")
        return

    st.markdown(
        '<div class="fusion-glass-card glow-purple">'
        '<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
        f'color:{_PURPLE};letter-spacing:1px;">KRIGING ESTIMATION SURFACE</span>'
        '<br/><span style="font-family:JetBrains Mono,monospace;font-size:0.58rem;'
        f'color:{_DIM};">Interpolated score surface with geostatistical variance overlay. '
        'Brighter areas = higher estimated quality. Red contours = high uncertainty.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    grid_x = kriging.get("grid_x", [])
    grid_y = kriging.get("grid_y", [])

    c1, c2 = st.columns(2)

    with c1:
        # Estimation heatmap
        fig = go.Figure(go.Heatmap(
            z=estimates, x=grid_x, y=grid_y,
            colorscale=[[0, "#0d1225"], [0.3, "#0ea5e9"], [0.6, "#10b981"], [1.0, "#00ff88"]],
            hovertemplate="Lon: %{x:.4f}<br>Lat: %{y:.4f}<br>Score: %{z:.1f}<extra></extra>",
            colorbar=dict(title="Score", tickfont=dict(size=8, color=_DIM)),
        ))
        # Data points overlay
        pts = kriging.get("data_points", [])
        if pts:
            fig.add_trace(go.Scatter(
                x=[p[0] for p in pts], y=[p[1] for p in pts],
                mode="markers",
                marker=dict(size=6, color=_CYAN, symbol="x", line=dict(width=1, color=_TEXT)),
                showlegend=False,
                hovertemplate="Known point<br>Score: %{text}<extra></extra>",
                text=[f"{p[2]:.1f}" for p in pts],
            ))
        fig.update_layout(**_ops_layout("ESTIMATED SCORE SURFACE", height=380,
            xaxis=dict(title="Longitude", gridcolor=_GRID),
            yaxis=dict(title="Latitude", gridcolor=_GRID, scaleanchor="x"),
        ))
        st.plotly_chart(fig, use_container_width=True, key="fic_kriging_est")

    with c2:
        # Variance heatmap
        fig_v = go.Figure(go.Heatmap(
            z=variance, x=grid_x, y=grid_y,
            colorscale=[[0, "#0d1225"], [0.4, "#ffaa00"], [0.7, "#ff5533"], [1.0, "#ff3344"]],
            hovertemplate="Lon: %{x:.4f}<br>Lat: %{y:.4f}<br>Variance: %{z:.2f}<extra></extra>",
            colorbar=dict(title="Variance", tickfont=dict(size=8, color=_DIM)),
        ))
        fig_v.update_layout(**_ops_layout("ESTIMATION VARIANCE (uncertainty)", height=380,
            xaxis=dict(title="Longitude", gridcolor=_GRID),
            yaxis=dict(title="Latitude", gridcolor=_GRID, scaleanchor="x"),
        ))
        st.plotly_chart(fig_v, use_container_width=True, key="fic_kriging_var")

    # Semivariogram info
    with st.expander("SEMIVARIOGRAM PARAMETERS"):
        v1, v2, v3, v4 = st.columns(4)
        _metric_card(v1, "Model", vario.get("model", "N/A").title(), _PURPLE)
        _metric_card(v2, "Sill", f"{vario.get('sill', 0):.2f}", _CYAN)
        _metric_card(v3, "Range", f"{vario.get('range', 0):.4f}", _AMBER)
        _metric_card(v4, "Nugget", f"{vario.get('nugget', 0):.3f}", _DIM)
        st.markdown(
            f"*Sill = total variance; Range = distance of spatial autocorrelation; "
            f"Nugget = measurement noise at zero distance.*"
        )


# ---------------------------------------------------------------------------
# SECTION 10 HELPERS — PCA
# ---------------------------------------------------------------------------

def _render_pca_section(pca):
    """Render PCA scree plot, biplot, and dominant factors."""
    components = pca.get("components", [])
    scree = pca.get("scree_data", {})
    biplot = pca.get("biplot_data", {})
    dominant = pca.get("dominant_factors", [])

    if not components:
        st.caption("Insufficient data for PCA analysis.")
        return

    st.markdown(
        '<div class="fusion-glass-card glow-green">'
        '<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
        f'color:{_BLUE};letter-spacing:1px;">PRINCIPAL COMPONENT ANALYSIS</span>'
        '<br/><span style="font-family:JetBrains Mono,monospace;font-size:0.58rem;'
        f'color:{_DIM};">Identifies which factors REALLY drive site quality. '
        'Reduces 10+ dimensions to 3-4 principal components.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    # Scree plot
    with c1:
        evr = scree.get("explained_variance_ratio", [])
        cumulative = scree.get("cumulative", [])
        idx = scree.get("component_idx", [])
        if evr:
            fig_s = go.Figure()
            fig_s.add_trace(go.Bar(
                x=[f"PC{i+1}" for i in idx], y=[v * 100 for v in evr],
                marker=dict(color=_BLUE, opacity=0.7),
                name="Individual",
            ))
            fig_s.add_trace(go.Scatter(
                x=[f"PC{i+1}" for i in idx], y=[v * 100 for v in cumulative],
                mode="lines+markers",
                line=dict(color=_CYAN, width=2),
                marker=dict(size=6, color=_CYAN),
                name="Cumulative",
            ))
            # 90% threshold line
            fig_s.add_hline(y=90, line_dash="dot", line_color=_AMBER, opacity=0.5,
                           annotation_text="90%", annotation_font=dict(size=9, color=_AMBER))
            fig_s.update_layout(**_ops_layout(
                "SCREE PLOT — Explained Variance", height=350,
                yaxis=dict(title="Variance %", gridcolor=_GRID, range=[0, 105]),
                legend=dict(font=dict(size=9, color=_DIM), bgcolor="rgba(0,0,0,0)"),
            ))
            st.plotly_chart(fig_s, use_container_width=True, key="fic_pca_scree")

    # Biplot
    with c2:
        loading_vecs = biplot.get("loading_vectors", [])
        if loading_vecs:
            fig_b = go.Figure()

            # Loading vectors (arrows)
            for lv in loading_vecs:
                pc1 = lv.get("pc1", 0)
                pc2 = lv.get("pc2", 0)
                magnitude = math.sqrt(pc1 ** 2 + pc2 ** 2)
                if magnitude < 0.05:
                    continue
                color = _CYAN if magnitude > 0.3 else _DIM
                fig_b.add_trace(go.Scatter(
                    x=[0, pc1], y=[0, pc2],
                    mode="lines+text",
                    line=dict(color=color, width=2),
                    text=["", lv["name"][:15]],
                    textposition="top center",
                    textfont=dict(size=8, color=_TEXT),
                    showlegend=False,
                    hovertemplate=f"<b>{lv['name']}</b><br>PC1: {pc1:.3f}<br>PC2: {pc2:.3f}<extra></extra>",
                ))
                # Arrowhead
                fig_b.add_trace(go.Scatter(
                    x=[pc1], y=[pc2], mode="markers",
                    marker=dict(size=8, color=color, symbol="arrow-up",
                               angle=math.degrees(math.atan2(pc2, pc1)) - 90),
                    showlegend=False, hoverinfo="skip",
                ))

            fig_b.update_layout(**_ops_layout(
                f"BIPLOT — PC1 ({biplot.get('pc1_var', 0):.0%}) vs PC2 ({biplot.get('pc2_var', 0):.0%})",
                height=350,
                xaxis=dict(title="PC1", gridcolor=_GRID, zeroline=True,
                          zerolinecolor=_DIM, zerolinewidth=1),
                yaxis=dict(title="PC2", gridcolor=_GRID, zeroline=True,
                          zerolinecolor=_DIM, zerolinewidth=1, scaleanchor="x"),
            ))
            st.plotly_chart(fig_b, use_container_width=True, key="fic_pca_biplot")

    # Dominant factors
    if dominant:
        st.markdown(
            f'<div style="padding:10px;border:1px solid {_BLUE}33;border-radius:6px;'
            f'background:{_BLUE}08;margin:0.6rem 0;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_BLUE};letter-spacing:1px;">DOMINANT FACTORS</span></div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(min(len(dominant), 5))
        for i, (name, imp) in enumerate(dominant[:5]):
            col = cols[i % len(cols)]
            pct = imp * 100
            color = _GREEN if imp > 0.3 else (_AMBER if imp > 0.15 else _DIM)
            col.markdown(
                f'<div style="text-align:center;padding:8px;border:1px solid {color}22;'
                f'border-radius:6px;background:{color}08;">'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{_DIM};">{name}</div>'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:1.1rem;'
                f'font-weight:700;color:{color};">{pct:.0f}%</div>'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.5rem;'
                f'color:{_DIM};">importance</div></div>',
                unsafe_allow_html=True,
            )

    # Total explained variance
    total = pca.get("total_explained", 0)
    st.markdown(
        f"*{pca.get('n_components', 0)} components explain {total:.0%} of total variance.*"
    )


# ---------------------------------------------------------------------------
# SECTION 11 HELPERS — BAYESIAN BELIEF NETWORK
# ---------------------------------------------------------------------------

def _render_bayesian_section(bbn, scores):
    """Render Bayesian Belief Network graph and what-if simulation."""
    posteriors = bbn.get("posteriors", {})
    priors = bbn.get("priors", {})
    edges = bbn.get("edge_strengths", [])
    node_importance = bbn.get("node_importance", {})
    cond_updates = bbn.get("conditional_updates", {})

    if not posteriors:
        st.caption("Insufficient data for Bayesian network analysis.")
        return

    st.markdown(
        '<div class="fusion-glass-card glow-purple">'
        '<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
        f'color:{_PURPLE};letter-spacing:1px;">BAYESIAN CAUSAL NETWORK</span>'
        '<br/><span style="font-family:JetBrains Mono,monospace;font-size:0.58rem;'
        f'color:{_DIM};">DAG-based causal inference. Nodes = domains, edges = influence. '
        'Use What-If to simulate interventions.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Network graph
    _render_bbn_network_graph(posteriors, edges, node_importance)

    # Conditional updates table
    if cond_updates:
        updated = sorted(cond_updates.items(), key=lambda x: abs(x[1]), reverse=True)
        with st.expander("POSTERIOR SHIFTS (vs prior)", expanded=False):
            header = "| Domain | Prior | Posterior | Shift |"
            sep = "|--------|-------|-----------|-------|"
            lines = [header, sep]
            for d, delta in updated:
                dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
                prior_pct = priors.get(d, 0) * 100
                post_pct = posteriors.get(d, 0) * 100
                sign = "+" if delta >= 0 else ""
                color = _GREEN if delta > 0 else (_RED if delta < 0 else _DIM)
                lines.append(
                    f"| {dname} | {prior_pct:.1f}% | {post_pct:.1f}% | {sign}{delta:.1f}% |"
                )
            st.markdown("\n".join(lines))

    # What-If Panel
    st.markdown(
        '<div class="fusion-whatif-panel">'
        '<div class="whatif-title">WHAT-IF SCENARIO SIMULATION</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    wi1, wi2 = st.columns([1, 2])
    with wi1:
        domain_names = sorted(scores.keys())
        domain_labels = {d: INTELLIGENCE_DOMAINS.get(d, {}).get("name", d) for d in domain_names}
        selected_domain = st.selectbox(
            "Intervention Domain",
            domain_names,
            format_func=lambda d: domain_labels.get(d, d),
            key="fic_whatif_domain",
        )
        current_val = scores.get(selected_domain, 50)
        new_val = st.slider(
            f"New value for {domain_labels.get(selected_domain, selected_domain)}",
            0, 100, int(current_val),
            key="fic_whatif_slider",
        )

    with wi2:
        if new_val != int(current_val):
            wi_result = bayesian_what_if(scores, selected_domain, new_val)
            deltas = wi_result.get("deltas", {})
            most_affected = wi_result.get("most_affected", [])

            if most_affected:
                # Bar chart of deltas
                domains_sorted = [d for d, _ in most_affected[:8]]
                delta_vals = [deltas.get(d, 0) for d in domains_sorted]
                names = [INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)[:14] for d in domains_sorted]
                colors = [_GREEN if v > 0 else _RED for v in delta_vals]

                fig_wi = go.Figure(go.Bar(
                    x=delta_vals, y=names, orientation="h",
                    marker=dict(color=colors, opacity=0.8),
                    text=[f"{v:+.1f}%" for v in delta_vals],
                    textposition="outside",
                    textfont=dict(size=9, color=_TEXT),
                ))
                fig_wi.update_layout(**_ops_layout(
                    f"IMPACT: {domain_labels.get(selected_domain, '')} "
                    f"{int(current_val)} -> {new_val}",
                    height=300,
                    xaxis=dict(title="Score Change (%)", gridcolor=_GRID,
                              zeroline=True, zerolinecolor=_DIM),
                    yaxis=dict(autorange="reversed"),
                ))
                st.plotly_chart(fig_wi, use_container_width=True, key="fic_whatif_chart")
        else:
            st.info("Move the slider to simulate an intervention.")


def _render_bbn_network_graph(posteriors, edges, node_importance):
    """Render interactive Plotly network graph for Bayesian Belief Network."""
    if not edges:
        return

    # Collect unique nodes
    nodes = sorted(posteriors.keys())
    n = len(nodes)
    node_idx = {d: i for i, d in enumerate(nodes)}

    # Layout: circular arrangement
    angle_step = 2 * math.pi / n if n > 0 else 0
    positions = {}
    for i, d in enumerate(nodes):
        angle = angle_step * i - math.pi / 2
        positions[d] = (math.cos(angle), math.sin(angle))

    # Edge traces
    edge_x, edge_y = [], []
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        if src in positions and tgt in positions:
            sx, sy = positions[src]
            tx, ty = positions[tgt]
            edge_x += [sx, tx, None]
            edge_y += [sy, ty, None]

    fig = go.Figure()

    # Edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y, mode="lines",
        line=dict(width=1.5, color="rgba(0,240,255,0.25)"),
        hoverinfo="none", showlegend=False,
    ))

    # Edge arrows (midpoints)
    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        w = e.get("weight", 0.1)
        if src in positions and tgt in positions:
            sx, sy = positions[src]
            tx, ty = positions[tgt]
            mx, my = (sx + tx) / 2, (sy + ty) / 2
            fig.add_annotation(
                x=mx, y=my, text=f"{w:.0%}", showarrow=False,
                font=dict(size=7, color=_DIM),
            )

    # Nodes
    node_x = [positions[d][0] for d in nodes]
    node_y = [positions[d][1] for d in nodes]
    node_colors = [_DOMAIN_COLORS.get(d, _CYAN) for d in nodes]
    node_sizes = [max(20, min(50, posteriors.get(d, 0.5) * 60)) for d in nodes]
    node_texts = [
        f"{INTELLIGENCE_DOMAINS.get(d, {}).get('name', d)[:12]}<br>"
        f"{posteriors.get(d, 0) * 100:.0f}%"
        for d in nodes
    ]
    hover_texts = [
        f"<b>{INTELLIGENCE_DOMAINS.get(d, {}).get('name', d)}</b><br>"
        f"Posterior: {posteriors.get(d, 0) * 100:.1f}%<br>"
        f"Importance: {node_importance.get(d, 0):.2f}"
        for d in nodes
    ]

    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        marker=dict(size=node_sizes, color=node_colors, opacity=0.85,
                   line=dict(width=2, color=_TEXT)),
        text=[INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)[:10] for d in nodes],
        textposition="bottom center",
        textfont=dict(size=8, color=_TEXT),
        hovertemplate="%{customdata}<extra></extra>",
        customdata=hover_texts,
        showlegend=False,
    ))

    fig.update_layout(**_ops_layout(
        "CAUSAL NETWORK GRAPH", height=450,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x"),
    ))
    st.plotly_chart(fig, use_container_width=True, key="fic_bbn_network")


# ---------------------------------------------------------------------------
# SECTION 12 HELPERS — ACTIVE THREATS
# ---------------------------------------------------------------------------

def _render_active_threats_section(details, raw_data):
    """Render GDACS disasters, OpenAQ stations, and population data."""

    # GDACS Events
    gdacs = details.get("gdacs_events", raw_data.get("gdacs", []))
    openaq = details.get("nearest_aq_stations", raw_data.get("openaq", []))
    pop_density = details.get("population_density", 0)
    active_count = details.get("active_disasters", 0)

    # Summary strip
    st.markdown(
        f'<div class="fusion-metric-strip">'
        f'<div class="fusion-strip-item">'
        f'<div class="fusion-strip-label">Active Disasters</div>'
        f'<div class="fusion-strip-value" style="color:{_RED if active_count > 0 else _GREEN};">'
        f'{active_count}</div></div>'
        f'<div class="fusion-strip-item">'
        f'<div class="fusion-strip-label">AQ Stations</div>'
        f'<div class="fusion-strip-value" style="color:{_CYAN};">'
        f'{len(openaq) if openaq else 0}</div></div>'
        f'<div class="fusion-strip-item">'
        f'<div class="fusion-strip-label">Pop. Density</div>'
        f'<div class="fusion-strip-value" style="color:{_AMBER};">'
        f'{pop_density:.0f}/km²</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    t1, t2 = st.columns(2)

    with t1:
        # GDACS events
        st.markdown(
            f'<div class="fusion-glass-card glow-red">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_RED};letter-spacing:1px;">GDACS ACTIVE EVENTS</span></div>',
            unsafe_allow_html=True,
        )
        if gdacs:
            for evt in gdacs[:5]:
                alert = evt.get("alert_level", "UNKNOWN")
                sev_color = _RED if alert == "RED" else (_AMBER if alert == "ORANGE" else _GREEN)
                badge_class = "critical" if alert == "RED" else ("warning" if alert == "ORANGE" else "safe")
                st.markdown(
                    f'<div style="padding:8px;border-left:3px solid {sev_color};'
                    f'margin:4px 0;background:{sev_color}08;border-radius:0 6px 6px 0;">'
                    f'<span class="fusion-severity-badge {badge_class}">{alert}</span>&nbsp;'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:0.78rem;'
                    f'color:{_TEXT};">{html_module.escape(evt.get("name", "Unknown"))}</span><br/>'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
                    f'color:{_DIM};">Type: {html_module.escape(str(evt.get("type", "?")))} | '
                    f'Distance: {evt.get("distance_km", "?")} km | '
                    f'Country: {html_module.escape(str(evt.get("country", "?")))}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<div style="text-align:center;padding:20px;color:{_GREEN};">'
                f'<span style="font-size:1.5rem;">&#10003;</span><br/>'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.75rem;">'
                f'No active disasters in range</span></div>',
                unsafe_allow_html=True,
            )

    with t2:
        # OpenAQ stations
        st.markdown(
            f'<div class="fusion-glass-card">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_CYAN};letter-spacing:1px;">NEAREST AQ MONITORING STATIONS</span></div>',
            unsafe_allow_html=True,
        )
        if openaq:
            header = "| Station | Dist | PM2.5 | PM10 |"
            sep = "|---------|------|-------|------|"
            lines = [header, sep]
            for s in openaq[:6]:
                pm25 = f"{s['pm25']:.1f}" if s.get("pm25") is not None else "-"
                pm10 = f"{s['pm10']:.1f}" if s.get("pm10") is not None else "-"
                name = s.get("station", "?")[:20]
                dist = s.get("distance_km", "?")
                lines.append(f"| {name} | {dist} km | {pm25} | {pm10} |")
            st.markdown("\n".join(lines))

            # PM2.5 bar chart if data available
            pm25_stations = [s for s in openaq if s.get("pm25") is not None]
            if len(pm25_stations) >= 2:
                names = [s.get("station", "?")[:15] for s in pm25_stations[:6]]
                pm25_vals = [s["pm25"] for s in pm25_stations[:6]]
                colors = []
                for v in pm25_vals:
                    if v <= 12:
                        colors.append(_GREEN)
                    elif v <= 35:
                        colors.append(_CYAN)
                    elif v <= 55:
                        colors.append(_AMBER)
                    else:
                        colors.append(_RED)

                fig_aq = go.Figure(go.Bar(
                    x=names, y=pm25_vals,
                    marker=dict(color=colors, opacity=0.8),
                    text=[f"{v:.1f}" for v in pm25_vals],
                    textposition="outside",
                    textfont=dict(size=9, color=_TEXT),
                ))
                # WHO guideline
                fig_aq.add_hline(y=15, line_dash="dot", line_color=_AMBER, opacity=0.6,
                               annotation_text="WHO 24h", annotation_font=dict(size=8, color=_AMBER))
                fig_aq.update_layout(**_ops_layout(
                    "PM2.5 by Station (µg/m³)", height=280,
                    yaxis=dict(title="PM2.5", gridcolor=_GRID),
                ))
                st.plotly_chart(fig_aq, use_container_width=True, key="fic_openaq_pm25")
        else:
            st.caption("No air quality monitoring stations found within range.")

    # Population density note
    if pop_density > 0:
        carrying = details.get("carrying_capacity_warning", False)
        if carrying:
            st.warning(f"Population density is very high ({pop_density:.0f}/km²). "
                      "Carrying capacity concerns should be evaluated.")
        elif pop_density > 1000:
            st.info(f"Dense urban area ({pop_density:.0f}/km²). "
                   "Good infrastructure likely but congestion possible.")


# ---------------------------------------------------------------------------
# SECTION 13 HELPERS — THREAT RADAR
# ---------------------------------------------------------------------------

def _render_threat_radar_section(threats):
    """Render unified threat radar with all threat sources."""
    level = threats.get("threat_level", "LOW")
    score = threats.get("threat_score", 0)
    sources = threats.get("threat_sources", [])
    summary = threats.get("threat_summary", "")
    proximity = threats.get("proximity_alert", False)

    level_colors = {
        "CRITICAL": _RED, "HIGH": "#ff8800", "ELEVATED": _AMBER,
        "MODERATE": _CYAN, "LOW": _GREEN,
    }
    lc = level_colors.get(level, _CYAN)

    # Threat level banner
    st.markdown(
        f'<div class="fusion-glass-card glow-red" style="text-align:center;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
        f'color:{_DIM};letter-spacing:2px;">UNIFIED THREAT LEVEL</span><br/>'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:2.5rem;'
        f'font-weight:800;color:{lc};letter-spacing:3px;">{level}</span><br/>'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.7rem;'
        f'color:{_DIM};">Score: {score:.0f}/100 | '
        f'{len(sources)} threat categories active</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    if proximity:
        st.markdown(
            f'<div class="fusion-severity-badge critical" '
            f'style="display:block;text-align:center;margin:0.5rem 0;padding:8px;">'
            f'PROXIMITY ALERT — Active threat within 25 km</div>',
            unsafe_allow_html=True,
        )

    if not sources:
        st.markdown(
            f'<div style="text-align:center;padding:20px;color:{_GREEN};">'
            f'<span style="font-size:2rem;">&#10003;</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.8rem;">'
            f'No active threats detected — all clear</span></div>',
            unsafe_allow_html=True,
        )
        return

    # Threat sources as horizontal radar
    if sources:
        fig = go.Figure()
        src_names = [s["source"] for s in sources]
        src_scores = [s["score_contribution"] for s in sources]
        src_colors = [level_colors.get(s["level"], _CYAN) for s in sources]

        fig.add_trace(go.Bar(
            x=src_names, y=src_scores,
            marker=dict(color=src_colors, opacity=0.85),
            text=[f"{s:.0f}" for s in src_scores],
            textposition="outside",
            textfont=dict(size=10, color=_TEXT),
        ))
        fig.update_layout(**_ops_layout(
            "THREAT CONTRIBUTION BY SOURCE", height=300,
            yaxis=dict(title="Threat Score", gridcolor=_GRID),
        ))
        st.plotly_chart(fig, use_container_width=True, key="fic_threat_radar_bar")

    # Source detail cards
    cols = st.columns(min(len(sources), 4))
    for i, src in enumerate(sources[:4]):
        col = cols[i % len(cols)]
        sc = level_colors.get(src["level"], _CYAN)
        col.markdown(
            f'<div style="text-align:center;padding:10px;border:1px solid {sc}33;'
            f'border-radius:8px;background:{sc}08;">'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
            f'color:{_DIM};letter-spacing:1px;">{html_module.escape(src["source"])}</div>'
            f'<div class="fusion-severity-badge {src["level"].lower()}" '
            f'style="margin:4px 0;">{html_module.escape(src["level"])}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
            f'color:{_TEXT};">{html_module.escape(src.get("detail", ""))}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Fire data table
    fires = threats.get("fire_data", [])
    if fires:
        with st.expander(f"ACTIVE FIRE HOTSPOTS ({len(fires)} detected)", expanded=False):
            header = "| Distance | Lat | Lon | Brightness | Confidence |"
            sep = "|----------|-----|-----|------------|------------|"
            lines = [header, sep]
            for f in fires[:10]:
                lines.append(
                    f"| {f.get('distance_km', '?')} km | "
                    f"{f.get('lat', 0):.4f} | {f.get('lon', 0):.4f} | "
                    f"{f.get('brightness', 0):.0f} | {f.get('confidence', '?')} |"
                )
            st.markdown("\n".join(lines))

    st.caption(summary)


# ---------------------------------------------------------------------------
# SECTION 14 HELPERS — STRATEGIC SYNTHESIS
# ---------------------------------------------------------------------------

def _render_strategic_synthesis_section(strategic, scores):
    """Render the strategic synthesis — the brain output."""
    grade = strategic.get("strategic_grade", "N/A")
    score = strategic.get("strategic_score", 0)
    dims = strategic.get("dimensions", {})
    dpq = strategic.get("decision_priority_queue", [])
    narrative = strategic.get("narrative", [])
    or_matrix = strategic.get("opportunity_risk_quadrant", {})
    horizons = strategic.get("multi_horizon", {})
    insights = strategic.get("key_insights", [])
    confidence = strategic.get("confidence_level", 0)

    # Grade color
    if score >= 70:
        gc = _GREEN
    elif score >= 50:
        gc = _CYAN
    elif score >= 30:
        gc = _AMBER
    else:
        gc = _RED

    # Strategic score + grade hero
    st.markdown(
        f'<div class="fusion-glass-card glow-green" style="text-align:center;">'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
        f'color:{_DIM};letter-spacing:2px;">STRATEGIC INTELLIGENCE GRADE</span><br/>'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:4rem;'
        f'font-weight:900;color:{gc};text-shadow:0 0 30px {gc}44;">{grade}</span><br/>'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:1rem;'
        f'color:{gc};">{score:.0f}/100</span>&nbsp;&nbsp;'
        f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
        f'color:{_DIM};">confidence: {confidence:.0%}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # 5 Strategic Dimensions radar
    if dims:
        dim_names = [n.replace("_", " ").title() for n in dims.keys()]
        dim_scores = [dims[d]["score"] if isinstance(dims[d], dict) else float(dims[d] or 0) for d in dims]
        # Close the polygon
        dim_names_closed = dim_names + [dim_names[0]]
        dim_scores_closed = dim_scores + [dim_scores[0]]

        c1, c2 = st.columns([3, 2])
        with c1:
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=dim_scores_closed,
                theta=dim_names_closed,
                fill="toself",
                fillcolor=_hex_rgba(gc, 0.08),
                line=dict(color=gc, width=2),
                marker=dict(size=8, color=gc),
                name="Strategic Profile",
            ))
            fig.update_layout(**_ops_layout(
                "STRATEGIC DIMENSIONS", height=380,
                polar=dict(
                    bgcolor="rgba(5,5,16,0.6)",
                    radialaxis=dict(range=[0, 100], gridcolor=_GRID,
                                   tickfont=dict(size=8, color=_DIM)),
                    angularaxis=dict(gridcolor=_GRID,
                                   tickfont=dict(size=10, color=_TEXT)),
                ),
            ))
            st.plotly_chart(fig, use_container_width=True, key="fic_strategic_radar")

        with c2:
            # Dimension scores
            for dim_key, data in sorted(dims.items(),
                                        key=lambda x: x[1]["score"], reverse=True):
                s = data["score"]
                label = dim_key.replace("_", " ").title()
                bar_color = _GREEN if s >= 65 else (_AMBER if s >= 40 else _RED)
                st.markdown(
                    f'<div style="margin:6px 0;">'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
                    f'color:{_TEXT};">{label}</span>'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
                    f'color:{bar_color};float:right;">{s:.0f}</span>'
                    f'<div style="background:{_GRID};border-radius:3px;height:6px;margin-top:3px;">'
                    f'<div style="background:{bar_color};width:{s:.0f}%;height:6px;'
                    f'border-radius:3px;"></div></div></div>',
                    unsafe_allow_html=True,
                )

            # Opportunity-Risk quadrant
            if or_matrix:
                quad = or_matrix.get("quadrant", "N/A")
                q_colors = {"PRIME": _GREEN, "HIGH-REWARD/HIGH-RISK": _AMBER,
                           "STABLE/LIMITED": _CYAN, "AVOID": _RED}
                qc = q_colors.get(quad, _CYAN)
                st.markdown(
                    f'<div style="text-align:center;padding:10px;margin-top:12px;'
                    f'border:1px solid {qc}44;border-radius:8px;background:{qc}0a;">'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                    f'color:{_DIM};">OPPORTUNITY-RISK QUADRANT</span><br/>'
                    f'<span style="font-family:JetBrains Mono,monospace;font-size:1rem;'
                    f'font-weight:700;color:{qc};letter-spacing:1px;">{quad}</span></div>',
                    unsafe_allow_html=True,
                )

    # Narrative Intelligence Brief
    if narrative:
        st.markdown(
            f'<div style="padding:10px;border:1px solid {_CYAN}33;border-radius:6px;'
            f'background:{_CYAN}05;margin:0.8rem 0;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_CYAN};letter-spacing:1px;">INTELLIGENCE NARRATIVE</span></div>',
            unsafe_allow_html=True,
        )
        for para in narrative:
            # Bold the first word/label
            if ":" in para:
                label, rest = para.split(":", 1)
                st.markdown(f"**{label}:**{rest}")
            else:
                st.markdown(para)

    # Key Insights
    if insights:
        st.markdown(
            f'<div style="padding:10px;border:1px solid {_GREEN}33;border-radius:6px;'
            f'background:{_GREEN}05;margin:0.8rem 0;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_GREEN};letter-spacing:1px;">KEY INTERPOLATED INSIGHTS</span></div>',
            unsafe_allow_html=True,
        )
        for ins in insights:
            type_colors = {"opportunity": _GREEN, "risk": _RED, "threat": _RED,
                          "constraint": _AMBER, "strength": _CYAN, "insight": _PURPLE}
            ic = type_colors.get(ins.get("type", ""), _CYAN)
            conf = ins.get("confidence", 0) * 100
            st.markdown(
                f'<div style="padding:10px;border-left:3px solid {ic};margin:6px 0;'
                f'background:{ic}06;border-radius:0 6px 6px 0;">'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.72rem;'
                f'font-weight:700;color:{ic};">{html_module.escape(ins.get("title", ""))}</span>'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{_DIM};float:right;">{conf:.0f}% confidence</span><br/>'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
                f'color:{_TEXT};line-height:1.5;">{html_module.escape(ins.get("text", ""))}</span></div>',
                unsafe_allow_html=True,
            )

    # Decision Priority Queue
    if dpq:
        st.markdown(
            f'<div style="padding:10px;border:1px solid {_AMBER}33;border-radius:6px;'
            f'background:{_AMBER}05;margin:0.8rem 0;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_AMBER};letter-spacing:1px;">DECISION PRIORITY QUEUE</span></div>',
            unsafe_allow_html=True,
        )
        urgency_colors = {
            "IMMEDIATE": _RED, "SHORT-TERM": _AMBER,
            "MEDIUM-TERM": _CYAN, "LONG-TERM": _BLUE,
        }
        for i, action in enumerate(dpq[:8], 1):
            uc = urgency_colors.get(action.get("urgency", ""), _CYAN)
            impact = action.get("impact", "MEDIUM")
            impact_color = _RED if impact == "CRITICAL" else (
                _AMBER if impact == "HIGH" else _CYAN)
            st.markdown(
                f'<div style="padding:8px 12px;border-left:3px solid {uc};margin:4px 0;'
                f'background:{uc}06;border-radius:0 6px 6px 0;">'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
                f'color:{uc};font-weight:700;">#{i} {action.get("urgency", "")}</span>'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{impact_color};float:right;">IMPACT: {impact}</span><br/>'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.72rem;'
                f'color:{_TEXT};">{html_module.escape(action.get("action", ""))}</span><br/>'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{_DIM};">{html_module.escape(action.get("rationale", ""))}</span></div>',
                unsafe_allow_html=True,
            )

    # Multi-Horizon Outlook
    if horizons:
        st.markdown(
            f'<div style="padding:10px;border:1px solid {_BLUE}33;border-radius:6px;'
            f'background:{_BLUE}05;margin:0.8rem 0;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
            f'color:{_BLUE};letter-spacing:1px;">MULTI-HORIZON OUTLOOK</span></div>',
            unsafe_allow_html=True,
        )
        h_cols = st.columns(3)
        for i, (period, label) in enumerate([
            ("short_term", "0-3 MONTHS"),
            ("medium_term", "3-12 MONTHS"),
            ("long_term", "1-5 YEARS"),
        ]):
            h = horizons.get(period, {})
            outlook = h.get("outlook", "N/A")
            conf = h.get("confidence", 0) * 100
            narr = h.get("narrative", "")
            o_colors = {"FAVORABLE": _GREEN, "IMPROVING": _GREEN,
                       "STABLE": _CYAN, "SUSTAINABLE": _GREEN,
                       "MIXED": _AMBER, "UNCERTAIN": _AMBER,
                       "CAUTION": _AMBER, "DEGRADING": _RED, "AT RISK": _RED}
            oc = o_colors.get(outlook, _CYAN)
            h_cols[i].markdown(
                f'<div style="text-align:center;padding:12px;border:1px solid {oc}33;'
                f'border-radius:8px;background:{oc}08;">'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{_DIM};letter-spacing:1px;">{label}</div>'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:1.1rem;'
                f'font-weight:700;color:{oc};margin:4px 0;">{outlook}</div>'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{_DIM};">conf: {conf:.0f}%</div>'
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.55rem;'
                f'color:{_TEXT};margin-top:4px;">{narr}</div></div>',
                unsafe_allow_html=True,
            )


def _generate_conclusions(ds, cascade, cvi, anomalies, trends, topsis, scores, confidence):
    """Generate top 5 actionable conclusions with confidence %."""
    conclusions = []
    belief_pct = ds["fused_belief"] * 100
    conf_base = confidence * 100

    # 1. Overall assessment
    if belief_pct >= 65:
        conclusions.append((
            f"Location shows strong fused favorability ({belief_pct:.0f}% D-S belief). "
            "Multi-source evidence broadly supports positive outcomes.",
            min(conf_base + 10, 95),
        ))
    elif belief_pct >= 40:
        conclusions.append((
            f"Location shows mixed signals ({belief_pct:.0f}% D-S belief). "
            "Proceed with targeted due diligence on weak domains.",
            conf_base,
        ))
    else:
        conclusions.append((
            f"Location shows unfavorable evidence fusion ({belief_pct:.0f}% D-S belief). "
            "Significant risk factors identified; recommend alternative sites.",
            min(conf_base + 15, 95),
        ))

    # 2. Systemic risk
    sys_risk = cascade["systemic_score"]
    if sys_risk > 50:
        chain = cascade.get("most_vulnerable_chain", [])
        chain_str = " -> ".join(chain[:3]) if chain else "multiple domains"
        conclusions.append((
            f"Systemic risk is elevated ({sys_risk:.0f}/100) with cascade "
            f"propagation through {chain_str}. Mitigate upstream risks first.",
            min(conf_base + 5, 90),
        ))
    else:
        conclusions.append((
            f"Systemic risk is manageable ({sys_risk:.0f}/100). "
            "No critical cascade amplification detected.",
            conf_base,
        ))

    # 3. Vulnerability
    vclass = cvi["vulnerability_class"]
    if vclass in ("HIGH", "EXTREME"):
        wl = cvi["weakest_link"].replace("_", " ").title()
        conclusions.append((
            f"Vulnerability is {vclass} (CVI={cvi['cvi_score']:.2f}). "
            f"Weakest dimension: {wl}. Invest in adaptive capacity.",
            min(conf_base + 5, 90),
        ))
    else:
        conclusions.append((
            f"Vulnerability is {vclass} (CVI={cvi['cvi_score']:.2f}). "
            "Location has reasonable adaptive capacity.",
            conf_base,
        ))

    # 4. Top scenario recommendation
    if topsis:
        best = topsis[0]
        sc_name = DECISION_SCENARIOS.get(best["scenario"], {}).get("name", best["scenario"])
        conclusions.append((
            f"Best-fit scenario: {sc_name} (TOPSIS closeness={best['closeness']:.3f}). "
            "This use case maximizes alignment with location characteristics.",
            best["closeness"] * 100,
        ))

    # 5. Critical anomalies
    critical = [a for a in anomalies if a["severity"] == "CRITICAL"]
    if critical:
        top_a = critical[0]
        conclusions.append((
            f"CRITICAL anomaly: {top_a['metric']} is {top_a['abs_z']:.1f} std devs "
            f"{'above' if top_a['z_score'] > 0 else 'below'} baseline. "
            f"Action: {top_a['action']}",
            min(85, conf_base + 10),
        ))
    elif anomalies:
        conclusions.append((
            f"{len(anomalies)} notable anomalies detected but none critical. "
            "Monitor during implementation phase.",
            conf_base,
        ))
    else:
        conclusions.append((
            "No significant anomalies detected. All metrics within normal range.",
            conf_base,
        ))

    return conclusions


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 15 HELPERS — MONTE CARLO RISK SIMULATION
# ═══════════════════════════════════════════════════════════════════════════

def _render_monte_carlo_section(mc_sim, mc_sensitivity):
    """Render Monte Carlo risk simulation results."""
    try:
        mc_sim = mc_sim or {}
        overall = mc_sim.get("overall", {})
        risk_class = mc_sim.get("risk_classification", "N/A")

        # Risk classification banner
        rc_color = _GREEN if "LOW" in risk_class else (
            _AMBER if "MODERATE" in risk_class else _RED
        )
        st.markdown(
            f'<div style="text-align:center;padding:12px;border:1px solid {rc_color}44;'
            f'border-radius:8px;background:{rc_color}0d;margin-bottom:1rem;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1px;">RISK CLASSIFICATION</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1.2rem;'
            f'font-weight:700;color:{rc_color};letter-spacing:2px;">{risk_class}</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.7rem;'
            f'color:{_DIM};">{mc_sim.get("n_iterations", 10000):,} iterations</span></div>',
            unsafe_allow_html=True,
        )

        # Key stats
        c1, c2, c3, c4 = st.columns(4)
        _metric_card(c1, "Expected Value", f"{overall.get('mean', 0):.1f}",
                     _GREEN if overall.get("mean", 0) >= 60 else _AMBER)
        _metric_card(c2, "Worst Case (P5)", f"{overall.get('p5', 0):.1f}",
                     _RED if overall.get("p5", 0) < 30 else _AMBER)
        _metric_card(c3, "Best Case (P95)", f"{overall.get('p95', 0):.1f}",
                     _GREEN if overall.get("p95", 0) >= 70 else _AMBER)
        _metric_card(c4, "Uncertainty (Std)", f"{overall.get('std', 0):.1f}",
                     _RED if overall.get("std", 0) > 15 else _CYAN)

        # Histogram
        hist_bins = mc_sim.get("histogram_bins", [])
        if hist_bins:
            bin_centers = [b[0] for b in hist_bins]
            counts = [b[1] for b in hist_bins]
            mean_val = overall.get("mean", 50)

            fig = go.Figure()
            colors = [_GREEN if x >= 60 else (_AMBER if x >= 40 else _RED) for x in bin_centers]
            fig.add_trace(go.Bar(
                x=bin_centers, y=counts,
                marker_color=colors, opacity=0.8,
                name="Simulation Distribution",
            ))
            # Mean line
            fig.add_vline(x=mean_val, line_dash="dash", line_color=_CYAN,
                          annotation_text=f"Mean: {mean_val:.1f}",
                          annotation_font_color=_CYAN)
            fig.update_layout(
                title=dict(text="OVERALL SCORE DISTRIBUTION", font=dict(size=13, color=_DIM)),
                xaxis_title="Score", yaxis_title="Frequency",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color=_TEXT,
                margin=dict(l=40, r=20, t=50, b=40),
                height=320,
            )
            fig.update_xaxes(gridcolor="#1a2035", range=[0, 100])
            fig.update_yaxes(gridcolor="#1a2035")
            st.plotly_chart(fig, use_container_width=True, key="fic_mc_histogram")

        # Probability metrics
        p1, p2, p3 = st.columns(3)
        with p1:
            pv = overall.get("probability_above_60", 0)
            st.markdown(
                f'<div style="text-align:center;padding:10px;border:1px solid {_GREEN}33;'
                f'border-radius:6px;background:{_GREEN}08;">'
                f'<div style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">P(VIABLE &gt; 60)</div>'
                f'<div style="font-size:1.5rem;font-weight:700;color:{_GREEN};">{pv:.0f}%</div></div>',
                unsafe_allow_html=True,
            )
        with p2:
            pm = overall.get("probability_above_40", 0)
            st.markdown(
                f'<div style="text-align:center;padding:10px;border:1px solid {_AMBER}33;'
                f'border-radius:6px;background:{_AMBER}08;">'
                f'<div style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">P(MARGINAL &gt; 40)</div>'
                f'<div style="font-size:1.5rem;font-weight:700;color:{_AMBER};">{pm:.0f}%</div></div>',
                unsafe_allow_html=True,
            )
        with p3:
            pc = overall.get("probability_below_30", 0)
            st.markdown(
                f'<div style="text-align:center;padding:10px;border:1px solid {_RED}33;'
                f'border-radius:6px;background:{_RED}08;">'
                f'<div style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">P(CRITICAL &lt; 30)</div>'
                f'<div style="font-size:1.5rem;font-weight:700;color:{_RED};">{pc:.0f}%</div></div>',
                unsafe_allow_html=True,
            )

        # Sensitivity analysis (tornado chart)
        if mc_sensitivity:
            with st.expander("SENSITIVITY ANALYSIS (TORNADO CHART)", expanded=True):
                domains = [s["domain"].replace("_", " ").title() for s in mc_sensitivity[:8]]
                worst = [s["worst_case_mean"] for s in mc_sensitivity[:8]]
                best = [s["best_case_mean"] for s in mc_sensitivity[:8]]
                swings = [s["swing"] for s in mc_sensitivity[:8]]
                base = overall.get("mean", 50)

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    y=domains, x=[w - base for w in worst],
                    base=base, orientation="h",
                    marker_color=_RED, opacity=0.7,
                    name="Worst Case (score=0)",
                ))
                fig.add_trace(go.Bar(
                    y=domains, x=[b - base for b in best],
                    base=base, orientation="h",
                    marker_color=_GREEN, opacity=0.7,
                    name="Best Case (score=100)",
                ))
                fig.add_vline(x=base, line_color=_CYAN, line_dash="dash")
                fig.update_layout(
                    title=dict(text="DOMAIN IMPACT ON OVERALL SCORE", font=dict(size=12, color=_DIM)),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color=_TEXT, barmode="overlay",
                    margin=dict(l=120, r=20, t=40, b=30),
                    height=300, showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                )
                fig.update_xaxes(gridcolor="#1a2035")
                fig.update_yaxes(gridcolor="#1a2035")
                st.plotly_chart(fig, use_container_width=True, key="fic_mc_tornado")

        # Domain uncertainty
        domain_dists = mc_sim.get("domain_distributions", {})
        if domain_dists:
            with st.expander("DOMAIN UNCERTAINTY ANALYSIS", expanded=False):
                rows = []
                for d, dd in sorted(domain_dists.items(), key=lambda x: x[1].get("spread", 0), reverse=True):
                    dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d.replace("_", " ").title())
                    spread = dd.get("spread", 0)
                    sp_color = _RED if spread > 30 else (_AMBER if spread > 15 else _GREEN)
                    rows.append(
                        f"| {dname} | {dd.get('mean', 0):.1f} | {dd.get('p5', 0):.1f} | "
                        f"{dd.get('p95', 0):.1f} | **{spread:.1f}** |"
                    )
                header = "| Domain | Mean | P5 | P95 | Spread |"
                sep = "|--------|------|-----|------|--------|"
                st.markdown("\n".join([header, sep] + rows))

    except Exception as e:
        logger.warning("Monte Carlo section render error: %s", e)
        st.info("Monte Carlo simulation data not available.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 16 HELPERS — CROSS-DOMAIN CORRELATION INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

def _render_correlation_section(corr_intel, scores):
    """Render cross-domain correlation intelligence."""
    try:
        corr_matrix = corr_intel.get("correlation_matrix", {})
        influence = corr_intel.get("influence_network", {})
        anomalies = corr_intel.get("anomalies", [])
        insights = corr_intel.get("insights", [])
        summary = corr_intel.get("summary", "")

        # Summary
        if summary:
            st.markdown(
                f'<div style="padding:12px;border:1px solid {_CYAN}33;border-radius:6px;'
                f'background:{_CYAN}08;margin-bottom:1rem;">'
                f'<span style="font-family:JetBrains Mono,monospace;font-size:0.75rem;'
                f'color:{_TEXT};">{summary}</span></div>',
                unsafe_allow_html=True,
            )

        # Correlation heatmap
        domain_order = corr_matrix.get("domain_order", [])
        matrix = corr_matrix.get("matrix", {})
        if domain_order and matrix:
            labels = [d.replace("_", " ").title()[:12] for d in domain_order]
            z_data = []
            for d1 in domain_order:
                row = []
                for d2 in domain_order:
                    row.append(matrix.get(d1, {}).get(d2, 0))
                z_data.append(row)

            fig = go.Figure(data=go.Heatmap(
                z=z_data, x=labels, y=labels,
                colorscale=[[0, _RED], [0.5, "#0a0a18"], [1, _GREEN]],
                zmin=-1, zmax=1,
                text=[[f"{v:.2f}" for v in row] for row in z_data],
                texttemplate="%{text}",
                textfont={"size": 9, "color": _TEXT},
                hovertemplate="<b>%{x}</b> vs <b>%{y}</b><br>Correlation: %{z:.2f}<extra></extra>",
            ))
            fig.update_layout(
                title=dict(text="DOMAIN CORRELATION MATRIX", font=dict(size=13, color=_DIM)),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color=_TEXT,
                margin=dict(l=100, r=20, t=50, b=80),
                height=420,
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_corr_heatmap")

        # Strongest correlations
        pos_corr = corr_matrix.get("strongest_positive", [])
        neg_corr = corr_matrix.get("strongest_negative", [])
        if pos_corr or neg_corr:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(
                    f'<div style="font-size:0.65rem;color:{_GREEN};letter-spacing:1px;'
                    f'font-weight:700;margin-bottom:4px;">STRONGEST POSITIVE</div>',
                    unsafe_allow_html=True,
                )
                for pc in pos_corr[:5]:
                    pair = pc.get("pair", ("", ""))
                    corr_val = pc.get("correlation", 0)
                    d1 = pair[0].replace("_", " ").title() if isinstance(pair, (list, tuple)) else str(pair)
                    d2 = pair[1].replace("_", " ").title() if isinstance(pair, (list, tuple)) and len(pair) > 1 else ""
                    st.markdown(
                        f'<div style="font-size:0.75rem;color:{_TEXT};padding:2px 0;">'
                        f'{d1} — {d2}: <span style="color:{_GREEN};font-weight:700;">'
                        f'{corr_val:+.2f}</span></div>',
                        unsafe_allow_html=True,
                    )
            with c2:
                st.markdown(
                    f'<div style="font-size:0.65rem;color:{_RED};letter-spacing:1px;'
                    f'font-weight:700;margin-bottom:4px;">STRONGEST NEGATIVE</div>',
                    unsafe_allow_html=True,
                )
                for nc in neg_corr[:3]:
                    pair = nc.get("pair", ("", ""))
                    corr_val = nc.get("correlation", 0)
                    d1 = pair[0].replace("_", " ").title() if isinstance(pair, (list, tuple)) else str(pair)
                    d2 = pair[1].replace("_", " ").title() if isinstance(pair, (list, tuple)) and len(pair) > 1 else ""
                    st.markdown(
                        f'<div style="font-size:0.75rem;color:{_TEXT};padding:2px 0;">'
                        f'{d1} — {d2}: <span style="color:{_RED};font-weight:700;">'
                        f'{corr_val:+.2f}</span></div>',
                        unsafe_allow_html=True,
                    )

        # Influence network
        nodes = influence.get("nodes", [])
        edges = influence.get("edges", [])
        most_influential = influence.get("most_influential", "")
        most_dependent = influence.get("most_dependent", "")

        if most_influential or most_dependent:
            mi1, mi2 = st.columns(2)
            with mi1:
                mi_name = most_influential.replace("_", " ").title() if most_influential else "N/A"
                st.markdown(
                    f'<div style="text-align:center;padding:10px;border:1px solid {_PURPLE}33;'
                    f'border-radius:6px;background:{_PURPLE}08;">'
                    f'<div style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">MOST INFLUENTIAL</div>'
                    f'<div style="font-size:1rem;font-weight:700;color:{_PURPLE};">{mi_name}</div></div>',
                    unsafe_allow_html=True,
                )
            with mi2:
                md_name = most_dependent.replace("_", " ").title() if most_dependent else "N/A"
                st.markdown(
                    f'<div style="text-align:center;padding:10px;border:1px solid {_AMBER}33;'
                    f'border-radius:6px;background:{_AMBER}08;">'
                    f'<div style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">MOST DEPENDENT</div>'
                    f'<div style="font-size:1rem;font-weight:700;color:{_AMBER};">{md_name}</div></div>',
                    unsafe_allow_html=True,
                )

        # Influence network graph
        if nodes and edges:
            fig = go.Figure()

            # Position nodes in a circle
            n_nodes = len(nodes)
            import math as _math
            node_positions = {}
            for i, n in enumerate(nodes):
                angle = 2 * _math.pi * i / n_nodes
                node_positions[n["domain"]] = (
                    _math.cos(angle), _math.sin(angle)
                )

            # Draw edges
            for edge in edges:
                x0, y0 = node_positions.get(edge["from"], (0, 0))
                x1, y1 = node_positions.get(edge["to"], (0, 0))
                strength = edge.get("strength", 0.1)
                fig.add_trace(go.Scatter(
                    x=[x0, x1, None], y=[y0, y1, None],
                    mode="lines",
                    line=dict(width=max(1, strength * 8), color=_hex_rgba(_CYAN, 0.27)),
                    showlegend=False, hoverinfo="skip",
                ))

            # Draw nodes
            nx = [node_positions[n["domain"]][0] for n in nodes]
            ny = [node_positions[n["domain"]][1] for n in nodes]
            sizes = [max(15, n.get("score", 50) * 0.4) for n in nodes]
            colors = [INTELLIGENCE_DOMAINS.get(n["domain"], {}).get("color", _CYAN) for n in nodes]
            labels = [n["domain"].replace("_", " ").title()[:10] for n in nodes]
            scores_text = [f"{n.get('score', 0):.0f}" for n in nodes]

            fig.add_trace(go.Scatter(
                x=nx, y=ny, mode="markers+text",
                marker=dict(size=sizes, color=colors, line=dict(width=2, color="#1a2035")),
                text=labels, textposition="top center",
                textfont=dict(size=9, color=_TEXT),
                hovertemplate="<b>%{text}</b><br>Score: %{customdata}<extra></extra>",
                customdata=scores_text,
                showlegend=False,
            ))

            fig.update_layout(
                title=dict(text="INFLUENCE NETWORK", font=dict(size=12, color=_DIM)),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color=_TEXT,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x"),
                margin=dict(l=20, r=20, t=40, b=20),
                height=380,
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_corr_network")

        # Anomalous relationships
        if anomalies:
            with st.expander(f"ANOMALOUS RELATIONSHIPS ({len(anomalies)})", expanded=True):
                for anom in anomalies[:5]:
                    a_color = _RED if anom.get("investigation_priority") == "HIGH" else _AMBER
                    da = anom.get("domain_a", "").replace("_", " ").title()
                    db = anom.get("domain_b", "").replace("_", " ").title()
                    st.markdown(
                        f'<div style="padding:8px;border-left:3px solid {a_color};'
                        f'background:{a_color}08;margin:4px 0;border-radius:0 4px 4px 0;">'
                        f'<span style="font-size:0.7rem;color:{a_color};font-weight:700;">'
                        f'[{anom.get("anomaly_type", "?")}]</span> '
                        f'<span style="font-size:0.78rem;color:{_TEXT};">'
                        f'{da} vs {db}</span><br/>'
                        f'<span style="font-size:0.7rem;color:{_DIM};">'
                        f'{anom.get("explanation", "")}</span></div>',
                        unsafe_allow_html=True,
                    )

        # Correlation insights
        if insights:
            with st.expander(f"CORRELATION INSIGHTS ({len(insights)})", expanded=True):
                for ins in insights[:6]:
                    i_color = {
                        "DRIVER": _GREEN, "DEPENDENCY": _AMBER,
                        "SYNERGY": _CYAN, "ANOMALY": _RED,
                        "LEVERAGE": _PURPLE, "VULNERABILITY": _RED,
                        "CLUSTER": _BLUE,
                    }.get(ins.get("type", ""), _DIM)
                    act_badge = ins.get("actionability", "")
                    conf = ins.get("confidence", 0)
                    st.markdown(
                        f'<div style="padding:8px;border:1px solid {i_color}22;'
                        f'background:{i_color}06;margin:4px 0;border-radius:6px;">'
                        f'<span style="font-size:0.6rem;color:{i_color};font-weight:700;'
                        f'letter-spacing:1px;">[{ins.get("type", "?")}]</span> '
                        f'<span style="font-size:0.6rem;color:{_DIM};float:right;">'
                        f'{act_badge} | {conf:.0%}</span><br/>'
                        f'<span style="font-size:0.82rem;color:{_TEXT};font-weight:600;">'
                        f'{ins.get("title", "")}</span><br/>'
                        f'<span style="font-size:0.72rem;color:{_DIM};">'
                        f'{ins.get("description", "")}</span></div>',
                        unsafe_allow_html=True,
                    )

        # Clusters
        clusters = corr_matrix.get("clusters", [])
        if clusters:
            with st.expander("DOMAIN CLUSTERS", expanded=False):
                for cl in clusters:
                    members = ", ".join(d.replace("_", " ").title() for d in cl.get("domains", []))
                    avg_c = cl.get("avg_correlation", 0)
                    st.markdown(
                        f'<div style="padding:6px;border:1px solid {_CYAN}22;margin:3px 0;'
                        f'border-radius:4px;">'
                        f'<span style="font-size:0.78rem;color:{_CYAN};font-weight:600;">'
                        f'{cl.get("name", "Cluster")}</span> '
                        f'<span style="font-size:0.65rem;color:{_DIM};">avg r={avg_c:.2f}</span><br/>'
                        f'<span style="font-size:0.72rem;color:{_TEXT};">{members}</span></div>',
                        unsafe_allow_html=True,
                    )

    except Exception as e:
        logger.warning("Correlation section render error: %s", e)
        st.info("Correlation intelligence data not available.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 17 HELPERS — PREDICTIVE ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════

def _render_predictive_section(predictive, scores):
    """Render predictive analytics and forecasting."""
    try:
        traj = predictive.get("risk_trajectory", "STABLE")
        traj_color = _GREEN if traj == "IMPROVING" else (_RED if traj == "WORSENING" else _AMBER)
        overall_fc = predictive.get("overall_forecast", {})

        # Trajectory banner
        st.markdown(
            f'<div style="text-align:center;padding:12px;border:1px solid {traj_color}44;'
            f'border-radius:8px;background:{traj_color}0d;margin-bottom:1rem;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1px;">RISK TRAJECTORY</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1.3rem;'
            f'font-weight:700;color:{traj_color};">{traj}</span></div>',
            unsafe_allow_html=True,
        )

        # Overall forecast timeline
        fc1, fc2, fc3, fc4 = st.columns(4)
        _metric_card(fc1, "Current", f"{overall_fc.get('current', 0):.1f}", _CYAN)
        _metric_card(fc2, "3 Months", f"{overall_fc.get('short_term', 0):.1f}",
                     _GREEN if overall_fc.get("short_term", 0) > overall_fc.get("current", 0) else _AMBER)
        _metric_card(fc3, "1 Year", f"{overall_fc.get('medium_term', 0):.1f}",
                     _GREEN if overall_fc.get("medium_term", 0) > overall_fc.get("current", 0) else _RED)
        _metric_card(fc4, "5 Years", f"{overall_fc.get('long_term', 0):.1f}",
                     _GREEN if overall_fc.get("long_term", 0) > overall_fc.get("current", 0) else _RED)

        # Domain forecast chart
        domain_fc = predictive.get("domain_forecasts", {})
        if domain_fc:
            domains_sorted = sorted(domain_fc.keys())
            fig = go.Figure()
            for horizon, color, name in [
                ("current", _CYAN, "Current"),
                ("short_term", _GREEN, "3 Months"),
                ("medium_term", _AMBER, "1 Year"),
                ("long_term", _RED, "5 Years"),
            ]:
                vals = []
                for d in domains_sorted:
                    fc = domain_fc[d]
                    if horizon == "current":
                        vals.append(fc.get("current", 0))
                    else:
                        h_data = fc.get(horizon, {})
                        vals.append(h_data.get("value", 0) if isinstance(h_data, dict) else 0)
                labels = [d.replace("_", " ").title()[:12] for d in domains_sorted]
                fig.add_trace(go.Bar(x=labels, y=vals, name=name, marker_color=color, opacity=0.7))

            fig.update_layout(
                title=dict(text="DOMAIN SCORE PROJECTIONS", font=dict(size=12, color=_DIM)),
                barmode="group",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color=_TEXT, margin=dict(l=40, r=20, t=40, b=60), height=320,
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            fig.update_xaxes(gridcolor="#1a2035", tickangle=45)
            fig.update_yaxes(gridcolor="#1a2035", range=[0, 100])
            st.plotly_chart(fig, use_container_width=True, key="fic_predictive_bars")

        # Early warnings
        inflection = predictive.get("inflection_points", [])
        if inflection:
            with st.expander(f"EARLY WARNINGS ({len(inflection)})", expanded=True):
                for ip in inflection:
                    w_color = _RED if "CRITICAL" in str(ip) else _AMBER
                    st.markdown(
                        f'<div style="padding:6px;border-left:3px solid {w_color};'
                        f'background:{w_color}08;margin:3px 0;border-radius:0 4px 4px 0;">'
                        f'<span style="font-size:0.75rem;color:{_TEXT};">{ip}</span></div>',
                        unsafe_allow_html=True,
                    )

        # Key projections
        key_proj = predictive.get("key_projections", [])
        if key_proj:
            with st.expander("KEY PROJECTIONS", expanded=False):
                for p in key_proj:
                    st.markdown(f'<div style="font-size:0.75rem;color:{_TEXT};padding:3px 0;">'
                                f'- {p}</div>', unsafe_allow_html=True)

        # Narrative
        narr = generate_prediction_narrative(predictive)
        if narr:
            st.markdown(
                f'<div style="padding:10px;border:1px solid {_BLUE}22;border-radius:6px;'
                f'background:{_BLUE}06;margin-top:0.8rem;">'
                f'<span style="font-size:0.6rem;color:{_BLUE};letter-spacing:1px;font-weight:700;">'
                f'PREDICTIVE NARRATIVE</span><br/>'
                f'<span style="font-size:0.73rem;color:{_TEXT};line-height:1.5;">{narr}</span></div>',
                unsafe_allow_html=True,
            )

    except Exception as e:
        logger.warning("Predictive section render error: %s", e)
        st.info("Predictive analytics data not available.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 18 HELPERS — DECISION TREES
# ═══════════════════════════════════════════════════════════════════════════

def _render_decision_tree_section(dt_results, dt_roadmap, scores):
    """Render decision tree assessment results."""
    try:
        go_list = dt_results.get("go_scenarios", [])
        caution_list = dt_results.get("caution_scenarios", [])
        nogo_list = dt_results.get("no_go_scenarios", [])
        best = dt_results.get("best_use", "N/A")

        # Summary strip
        d1, d2, d3, d4 = st.columns(4)
        _metric_card(d1, "GO Scenarios", str(len(go_list)), _GREEN)
        _metric_card(d2, "CAUTION", str(len(caution_list)), _AMBER)
        _metric_card(d3, "NO-GO", str(len(nogo_list)), _RED)
        _metric_card(d4, "Best Use", best.replace("_", " ").title()[:15], _CYAN)

        # Scenario verdicts
        results = dt_results.get("results", {})
        if results:
            verdict_cols = {"GO": _GREEN, "CAUTION": _AMBER, "NO_GO": _RED}
            rows = []
            for scenario_name, res in sorted(results.items()):
                v = res.get("verdict", "?")
                vc = verdict_cols.get(v, _DIM)
                conf = res.get("confidence", 0)
                rec = res.get("recommendation", "")[:80]
                scenario_label = scenario_name.replace("_", " ").title()
                rows.append(
                    f'<tr><td style="color:{_TEXT};font-size:0.75rem;">{scenario_label}</td>'
                    f'<td style="text-align:center;"><span style="color:{vc};font-weight:700;'
                    f'font-size:0.8rem;">{v.replace("_", " ")}</span></td>'
                    f'<td style="text-align:center;color:{_DIM};font-size:0.7rem;">{conf:.0f}%</td>'
                    f'<td style="color:{_DIM};font-size:0.65rem;">{rec}</td></tr>'
                )
            st.markdown(
                f'<table style="width:100%;border-collapse:collapse;">'
                f'<tr style="border-bottom:1px solid #1a2035;">'
                f'<th style="text-align:left;color:{_CYAN};font-size:0.6rem;padding:6px;">SCENARIO</th>'
                f'<th style="text-align:center;color:{_CYAN};font-size:0.6rem;">VERDICT</th>'
                f'<th style="text-align:center;color:{_CYAN};font-size:0.6rem;">CONF</th>'
                f'<th style="text-align:left;color:{_CYAN};font-size:0.6rem;">RECOMMENDATION</th></tr>'
                + "".join(rows) + '</table>',
                unsafe_allow_html=True,
            )

        # Improvement roadmap
        if dt_roadmap:
            with st.expander("IMPROVEMENT ROADMAP", expanded=True):
                for step in dt_roadmap[:5]:
                    effort_color = {
                        "LOW": _GREEN, "MEDIUM": _AMBER, "HIGH": _RED
                    }.get(step.get("effort", ""), _DIM)
                    unlocks = ", ".join(u.replace("_", " ").title() for u in step.get("unlocks", []))
                    st.markdown(
                        f'<div style="padding:8px;border:1px solid {effort_color}22;'
                        f'border-radius:6px;margin:4px 0;background:{effort_color}06;">'
                        f'<span style="font-size:0.65rem;color:{effort_color};font-weight:700;">'
                        f'STEP {step.get("priority", "?")}</span> '
                        f'<span style="font-size:0.8rem;color:{_TEXT};font-weight:600;">'
                        f'{step.get("domain", "").replace("_", " ").title()}</span> '
                        f'<span style="font-size:0.7rem;color:{_DIM};">'
                        f'{step.get("current_score", 0):.0f} → {step.get("target_score", 0):.0f}</span><br/>'
                        f'<span style="font-size:0.65rem;color:{_GREEN};">Unlocks: {unlocks}</span> '
                        f'<span style="font-size:0.6rem;color:{effort_color};float:right;">'
                        f'Effort: {step.get("effort", "?")}</span></div>',
                        unsafe_allow_html=True,
                    )

    except Exception as e:
        logger.warning("Decision tree section render error: %s", e)
        st.info("Decision tree assessment data not available.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 19 HELPERS — SCENARIO WARGAMING
# ═══════════════════════════════════════════════════════════════════════════

def _render_wargaming_section(scores, wg_scenarios, wg_intervention):
    """Render scenario wargaming and intervention analysis."""
    try:
        wg_intervention = wg_intervention or {}
        # Intervention impact ranking
        rankings = wg_intervention.get("intervention_rankings", [])
        most_impactful = wg_intervention.get("most_impactful_intervention", "")

        if most_impactful:
            st.markdown(
                f'<div style="text-align:center;padding:10px;border:1px solid {_GREEN}33;'
                f'border-radius:8px;background:{_GREEN}08;margin-bottom:1rem;">'
                f'<span style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">'
                f'HIGHEST IMPACT INTERVENTION</span><br/>'
                f'<span style="font-size:1.1rem;font-weight:700;color:{_GREEN};">'
                f'{most_impactful.replace("_", " ").title()}</span></div>',
                unsafe_allow_html=True,
            )

        # Intervention bar chart
        if rankings:
            domains = [r["domain"].replace("_", " ").title()[:12] for r in rankings]
            pos_imp = [r.get("total_positive_impact", 0) for r in rankings]
            neg_imp = [r.get("total_negative_impact", 0) for r in rankings]

            fig = go.Figure()
            fig.add_trace(go.Bar(y=domains, x=pos_imp, orientation="h",
                                 name="Positive Impact", marker_color=_GREEN, opacity=0.7))
            fig.add_trace(go.Bar(y=domains, x=neg_imp, orientation="h",
                                 name="Negative Impact", marker_color=_RED, opacity=0.7))
            fig.update_layout(
                title=dict(text="INTERVENTION IMPACT MATRIX (+20 BOOST PER DOMAIN)",
                           font=dict(size=11, color=_DIM)),
                barmode="relative",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color=_TEXT, margin=dict(l=100, r=20, t=40, b=20), height=320,
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            fig.update_xaxes(gridcolor="#1a2035")
            fig.update_yaxes(gridcolor="#1a2035")
            st.plotly_chart(fig, use_container_width=True, key="fic_wg_intervention")

        # Scenario selector — run top 3 predefined scenarios
        if wg_scenarios:
            with st.expander("SCENARIO WARGAME RESULTS (TOP 3)", expanded=True):
                wg_results = []
                for sc in wg_scenarios[:3]:
                    try:
                        wr = run_scenario_wargame(scores, sc)
                        wg_results.append(wr)
                    except Exception:
                        continue

                if wg_results:
                    for wr in wg_results:
                        delta = wr.get("overall_delta", 0)
                        dc = _GREEN if delta > 0 else (_RED if delta < -5 else _AMBER)
                        narr = generate_wargame_narrative(wr)
                        narr_text = narr if isinstance(narr, str) else " ".join(narr) if narr else ""
                        st.markdown(
                            f'<div style="padding:10px;border:1px solid {dc}22;'
                            f'border-radius:6px;margin:6px 0;background:{dc}06;">'
                            f'<span style="font-size:0.8rem;color:{_TEXT};font-weight:700;">'
                            f'{wr.get("scenario_name", "?")}</span> '
                            f'<span style="font-size:0.75rem;color:{dc};font-weight:700;float:right;">'
                            f'{delta:+.1f}</span><br/>'
                            f'<span style="font-size:0.65rem;color:{_DIM};">Final: '
                            f'{wr.get("final_overall", 0):.1f} | Worst: '
                            f'{wr.get("worst_domain", "?").replace("_", " ").title()} | '
                            f'Cascades: {len(wr.get("cascade_effects", []))}</span><br/>'
                            f'<span style="font-size:0.65rem;color:{_TEXT};line-height:1.4;">'
                            f'{narr_text[:200]}</span></div>',
                            unsafe_allow_html=True,
                        )

        # Interactive scenario slider
        st.markdown(
            f'<div style="font-size:0.65rem;color:{_PURPLE};letter-spacing:1px;'
            f'font-weight:700;margin-top:1rem;">CUSTOM INTERVENTION SIMULATOR</div>',
            unsafe_allow_html=True,
        )
        wg_domain = st.selectbox(
            "Boost domain:",
            list(scores.keys()),
            format_func=lambda x: x.replace("_", " ").title(),
            key="fic_wg_domain",
        )
        wg_boost = st.slider(
            "Boost amount:",
            min_value=-30, max_value=30, value=15,
            key="fic_wg_boost",
        )
        if st.button("RUN SIMULATION", key="fic_wg_run"):
            custom_scenario = {
                "name": f"Custom: {wg_domain.replace('_', ' ').title()} {wg_boost:+d}",
                "description": f"Custom intervention on {wg_domain}",
                "events": [{"domain": wg_domain, "impact": wg_boost, "timing": "immediate"}],
                "duration_years": 3,
            }
            try:
                custom_result = run_scenario_wargame(scores, custom_scenario)
                delta = custom_result.get("overall_delta", 0)
                dc = _GREEN if delta > 0 else _RED
                st.markdown(
                    f'<div style="padding:10px;border:2px solid {dc};border-radius:8px;'
                    f'background:{dc}0d;margin-top:0.5rem;">'
                    f'<span style="font-size:0.9rem;color:{dc};font-weight:700;">'
                    f'Result: {delta:+.1f} overall impact</span><br/>'
                    f'<span style="font-size:0.7rem;color:{_TEXT};">'
                    f'Final score: {custom_result.get("final_overall", 0):.1f} | '
                    f'Cascades: {len(custom_result.get("cascade_effects", []))}</span></div>',
                    unsafe_allow_html=True,
                )
            except Exception as ex:
                st.warning(f"Simulation error: {ex}")

    except Exception as e:
        logger.warning("Wargaming section render error: %s", e)
        st.info("Scenario wargaming data not available.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 20 HELPERS — SATELLITE INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

def _render_satellite_section(profile):
    """Render satellite intelligence data (NDVI, land cover, water)."""
    try:
        ndvi = profile.get("ndvi", {})
        land = profile.get("land_cover", {})
        water = profile.get("surface_water", profile.get("water", {}))
        _vs_raw = profile.get("vegetation_score", 0)
        veg_score = _vs_raw.get("vegetation_score", 0) if isinstance(_vs_raw, dict) else float(_vs_raw or 0)

        # Top-level metrics
        c1, c2, c3, c4 = st.columns(4)
        ndvi_val = ndvi.get("ndvi", 0)
        ndvi_class = ndvi.get("classification", "unknown")
        nc = _GREEN if ndvi_val > 0.5 else (_AMBER if ndvi_val > 0.2 else _RED)
        c1.markdown(
            f'<div style="text-align:center;padding:8px;border:1px solid {nc}33;'
            f'border-radius:6px;background:{nc}0a;">'
            f'<span style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">NDVI</span><br/>'
            f'<span style="font-size:1.3rem;font-weight:700;color:{nc};">{ndvi_val:.3f}</span><br/>'
            f'<span style="font-size:0.6rem;color:{_TEXT};">{ndvi_class.title()}</span></div>',
            unsafe_allow_html=True,
        )

        health = ndvi.get("health_assessment", "N/A")
        hc = _GREEN if "good" in health.lower() else (_AMBER if "moderate" in health.lower() else _RED)
        c2.markdown(
            f'<div style="text-align:center;padding:8px;border:1px solid {hc}33;'
            f'border-radius:6px;background:{hc}0a;">'
            f'<span style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">HEALTH</span><br/>'
            f'<span style="font-size:0.85rem;font-weight:700;color:{hc};">{html_module.escape(health)}</span></div>',
            unsafe_allow_html=True,
        )

        dom_cover = land.get("dominant_type", "Unknown")
        c3.markdown(
            f'<div style="text-align:center;padding:8px;border:1px solid {_BLUE}33;'
            f'border-radius:6px;background:{_BLUE}0a;">'
            f'<span style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">LAND COVER</span><br/>'
            f'<span style="font-size:0.85rem;font-weight:700;color:{_BLUE};">'
            f'{html_module.escape(str(dom_cover))}</span></div>',
            unsafe_allow_html=True,
        )

        vc = _GREEN if veg_score >= 65 else (_AMBER if veg_score >= 40 else _RED)
        c4.markdown(
            f'<div style="text-align:center;padding:8px;border:1px solid {vc}33;'
            f'border-radius:6px;background:{vc}0a;">'
            f'<span style="font-size:0.6rem;color:{_DIM};letter-spacing:1px;">VEG SCORE</span><br/>'
            f'<span style="font-size:1.3rem;font-weight:700;color:{vc};">{veg_score:.0f}</span></div>',
            unsafe_allow_html=True,
        )

        # Land cover distribution
        distribution = land.get("distribution", {})
        if distribution and go:
            labels = list(distribution.keys())
            values = list(distribution.values())
            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values,
                hole=0.5,
                marker=dict(colors=[_GREEN, _BLUE, _AMBER, _CYAN, _PURPLE, _RED]),
                textfont=dict(color=_TEXT, size=10),
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=_TEXT, family="JetBrains Mono, monospace"),
                height=300, margin=dict(l=20, r=20, t=30, b=20),
                showlegend=True, legend=dict(font=dict(size=9, color=_DIM)),
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_sat_land_cover")

        # Water proximity
        water_dist = water.get("nearest_distance_km")
        water_count = water.get("features_count", 0)
        if water_dist is not None:
            wc = _CYAN if water_dist < 5 else (_AMBER if water_dist < 20 else _RED)
            st.markdown(
                f'<div style="padding:8px;border:1px solid {wc}22;border-radius:6px;'
                f'background:{wc}06;margin:0.5rem 0;">'
                f'<span style="font-size:0.7rem;color:{wc};font-weight:700;">'
                f'WATER: {water_count} features within range | '
                f'Nearest: {water_dist:.1f} km</span></div>',
                unsafe_allow_html=True,
            )

    except Exception as e:
        logger.warning("Satellite section render error: %s", e)
        st.info("Satellite intelligence data not available.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 21 HELPERS — ENSEMBLE META-ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════

def _render_ensemble_section(ensemble):
    """Render the Ensemble Meta-Assessment — the definitive final verdict."""
    try:
        ens_score = ensemble.get("ensemble_score", 0)
        classification = ensemble.get("ensemble_classification", "UNKNOWN")
        cls_color = ensemble.get("ensemble_color", _AMBER)
        agreement = ensemble.get("agreement_label", "N/A")
        verdict = ensemble.get("executive_verdict", "")
        one_liner = ensemble.get("one_liner", "")
        convergence = ensemble.get("cross_validation", {})
        recs = ensemble.get("definitive_recommendations", [])
        component_scores = ensemble.get("component_scores", {})

        # Grand verdict badge
        st.markdown(
            f'<div style="text-align:center;padding:18px;margin:0.5rem 0 1rem 0;'
            f'border:2px solid {cls_color};border-radius:12px;'
            f'background:linear-gradient(135deg, {cls_color}15, {cls_color}05);">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
            f'color:{_DIM};letter-spacing:2px;">ENSEMBLE META-ASSESSMENT</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:2.8rem;'
            f'font-weight:700;color:{cls_color};">{ens_score:.1f}</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1rem;'
            f'font-weight:700;color:{cls_color};letter-spacing:3px;">{html_module.escape(classification)}</span><br/>'
            f'<span style="font-size:0.65rem;color:{_DIM};">'
            f'Algorithm Agreement: {html_module.escape(agreement)}</span></div>',
            unsafe_allow_html=True,
        )

        # One-liner
        if one_liner:
            st.markdown(
                f'<div style="text-align:center;padding:8px;margin:0 0 1rem 0;'
                f'font-style:italic;font-size:0.8rem;color:{_TEXT};">'
                f'{html_module.escape(one_liner)}</div>',
                unsafe_allow_html=True,
            )

        # Component scores radar
        if component_scores and go:
            labels = [k.replace("_", " ").title() for k in component_scores.keys()]
            vals = list(component_scores.values())
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=labels + [labels[0]],
                fill="toself",
                fillcolor=f"rgba(0,240,255,0.1)",
                line=dict(color=_CYAN, width=2),
                name="Component Scores",
            ))
            fig.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(range=[0, 100], showticklabels=True,
                                    tickfont=dict(size=8, color=_DIM),
                                    gridcolor=_hex_rgba(_DIM, 0.13)),
                    angularaxis=dict(tickfont=dict(size=8, color=_TEXT),
                                     gridcolor=_hex_rgba(_DIM, 0.13)),
                ),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color=_TEXT, family="JetBrains Mono, monospace"),
                height=380, margin=dict(l=40, r=40, t=30, b=30),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_ensemble_radar")

        # Convergence metrics — compute spread/CV from component_scores
        if component_scores:
            comp_vals = [v for v in component_scores.values() if isinstance(v, (int, float))]
            spread = (max(comp_vals) - min(comp_vals)) if comp_vals else 0
            mean_c = sum(comp_vals) / max(len(comp_vals), 1)
            std_c = (sum((v - mean_c) ** 2 for v in comp_vals) / max(len(comp_vals), 1)) ** 0.5
            cv = std_c / mean_c if mean_c > 0 else 0
            validated = len(convergence.get("validated_strengths", []))
            disputed = len(convergence.get("disputed", []))
            cc1, cc2, cc3, cc4 = st.columns(4)
            cc1.metric("Spread", f"{spread:.1f}")
            cc2.metric("Coeff. of Variation", f"{cv:.2f}")
            cc3.metric("Agreement", agreement)
            cc4.metric("Validated / Disputed", f"{validated} / {disputed}")

        # Definitive recommendations
        if recs:
            st.markdown(
                f'<div style="font-size:0.65rem;color:{_PURPLE};letter-spacing:1px;'
                f'font-weight:700;margin-top:0.8rem;">DEFINITIVE RECOMMENDATIONS</div>',
                unsafe_allow_html=True,
            )
            for i, rec in enumerate(recs[:6]):
                prio = rec.get("urgency", rec.get("impact", "MEDIUM"))
                pc = _RED if prio in ("CRITICAL", "IMMEDIATE") else (_AMBER if prio in ("HIGH", "SHORT_TERM") else _BLUE)
                st.markdown(
                    f'<div style="padding:8px;border-left:3px solid {pc};'
                    f'margin:4px 0;background:{pc}06;border-radius:0 6px 6px 0;">'
                    f'<span style="font-size:0.6rem;color:{pc};font-weight:700;">'
                    f'[{prio}]</span> '
                    f'<span style="font-size:0.75rem;color:{_TEXT};font-weight:600;">'
                    f'{html_module.escape(str(rec.get("action", "")))}</span><br/>'
                    f'<span style="font-size:0.65rem;color:{_DIM};">'
                    f'{html_module.escape(str(rec.get("rationale", "")))}</span></div>',
                    unsafe_allow_html=True,
                )

        # Executive verdict
        if verdict:
            st.markdown(
                f'<div style="padding:12px;border:1px solid {_PURPLE}33;border-radius:8px;'
                f'background:{_PURPLE}08;margin-top:0.8rem;">'
                f'<span style="font-size:0.6rem;color:{_PURPLE};letter-spacing:1px;'
                f'font-weight:700;">EXECUTIVE VERDICT</span><br/>'
                f'<span style="font-size:0.75rem;color:{_TEXT};line-height:1.5;">'
                f'{html_module.escape(verdict)}</span></div>',
                unsafe_allow_html=True,
            )

    except Exception as e:
        logger.warning("Ensemble section render error: %s", e)
        st.info("Ensemble meta-assessment data not available.")


def _build_export_report(ds, cascade, cvi, anomalies, trends, topsis, electre,
                         ahp, swot, recommendations, scores, loc_name,
                         confidence, conclusions):
    """Build a markdown export report."""
    lines = [
        f"# Fusion Intelligence Report — {loc_name}",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC*",
        f"*Confidence: {confidence:.0%}*",
        "",
        "## Situation Assessment",
        f"- **Dempster-Shafer Fused Belief**: {ds['fused_belief']*100:.1f}%",
        f"- **Fused Plausibility**: {ds['fused_plausibility']*100:.1f}%",
        f"- **Conflict Level**: {ds['conflict_level']:.3f}",
        f"- **Uncertainty Gap**: {ds['uncertainty_gap']:.3f}",
        f"- **Systemic Risk Score**: {cascade['systemic_score']:.0f}/100",
        f"- **Composite Vulnerability (CVI)**: {cvi['cvi_score']:.3f} ({cvi['vulnerability_class']})",
        "",
        "## Domain Scores",
    ]
    for d in sorted(scores):
        dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
        lines.append(f"- {dname}: **{scores[d]:.0f}**/100")

    lines += ["", "## Risk Cascade"]
    for d in sorted(cascade.get("cascade_risk", {})):
        dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
        cr = cascade["cascade_risk"][d] * 100
        amp = cascade["amplification"].get(d, 1)
        lines.append(f"- {dname}: {cr:.0f}% (amplification: {amp:.2f}x)")

    chain = cascade.get("most_vulnerable_chain", [])
    if chain:
        chain_str = " -> ".join(chain)
        lines.append(f"\n**Most Vulnerable Chain**: {chain_str}")

    lines += ["", "## Scenario Ranking (TOPSIS)"]
    kernel = set(electre.get("kernel", []))
    for r in (topsis or []):
        sc_name = DECISION_SCENARIOS.get(r["scenario"], {}).get("name", r["scenario"])
        k_tag = " [ELECTRE KERNEL]" if r["scenario"] in kernel else ""
        lines.append(f"{r['rank']}. **{sc_name}** — C*={r['closeness']:.3f}{k_tag}")

    lines += ["", "## Vulnerability Profile"]
    lines.append(f"- Exposure: {cvi['exposure']:.3f}")
    lines.append(f"- Sensitivity: {cvi['sensitivity']:.3f}")
    lines.append(f"- Adaptive Capacity: {cvi['adaptive_capacity']:.3f}")
    lines.append(f"- Weakest Link: {cvi['weakest_link']}")

    if anomalies:
        lines += ["", "## Anomalies"]
        for a in anomalies:
            lines.append(f"- **[{a['severity']}]** {a['metric']}: {a['value']} "
                         f"(baseline: {a['baseline']}, z={a['z_score']:+.1f})")

    lines += ["", "## Temporal Outlook"]
    lines.append(f"- Composite Trend: **{trends.get('composite_trend', 'N/A')}**")
    for d, t in sorted(trends.get("domain_trends", {}).items()):
        dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
        lines.append(f"- {dname}: {t}")

    if conclusions:
        lines += ["", "## Actionable Conclusions"]
        for i, (text, conf) in enumerate(conclusions[:5], 1):
            lines.append(f"{i}. {text} *(confidence: {conf:.0f}%)*")

    if swot:
        lines += ["", "## SWOT Analysis"]
        for section in ["strengths", "weaknesses", "opportunities", "threats"]:
            lines.append(f"\n### {section.title()}")
            for item in (swot.get(section) or [])[:5]:
                lines.append(f"- {item}")

    if recommendations:
        lines += ["", "## Recommended Next Steps"]
        for i, rec in enumerate(recommendations[:5], 1):
            if isinstance(rec, str):
                lines.append(f"{i}. {rec}")
            elif isinstance(rec, dict):
                lines.append(f"{i}. {rec.get('text', rec.get('recommendation', str(rec)))}")

    lines += [
        "",
        "---",
        "*Report generated by TerraScout AI Fusion Intelligence Console*",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 22 HELPERS — FUZZY LOGIC ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════

def _render_fuzzy_section(fuzzy):
    """Render fuzzy logic assessment section."""
    try:
        overall = fuzzy.get("fuzzy_overall", {})
        domains = fuzzy.get("fuzzy_domains", {})
        interactions = fuzzy.get("fuzzy_interactions", [])

        # Overall verdict badge
        val = overall.get("value", 50)
        linguistic = overall.get("linguistic", "MODERATE")
        color = _GREEN if val >= 60 else (_AMBER if val >= 40 else _RED)
        st.markdown(
            f'<div style="text-align:center;padding:12px;margin:0.5rem 0 1rem;'
            f'border:1px solid {color}33;border-radius:8px;background:{color}0a;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1.5px;">FUZZY LOGIC VERDICT</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1.8rem;'
            f'font-weight:700;color:{color};">{val:.0f}</span>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.8rem;'
            f'color:{_DIM};margin-left:8px;">{linguistic}</span></div>',
            unsafe_allow_html=True,
        )

        # Domain membership bars
        if domains and go is not None:
            domain_names = []
            low_vals = []
            med_vals = []
            high_vals = []
            for d in ("habitability", "agriculture", "ecology", "hazard_safety",
                      "water_resources", "infrastructure", "climate_comfort",
                      "economic_potential", "air_environment", "geological_stability"):
                fd = domains.get(d, {})
                if not fd:
                    continue
                domain_names.append(d.replace("_", " ").title()[:12])
                low_vals.append(round(fd.get("low", 0), 2))
                med_vals.append(round(fd.get("medium", 0), 2))
                high_vals.append(round(fd.get("high", 0), 2))

            fig = go.Figure()
            fig.add_trace(go.Bar(name="Low", x=domain_names, y=low_vals,
                                 marker_color=_RED, opacity=0.7))
            fig.add_trace(go.Bar(name="Medium", x=domain_names, y=med_vals,
                                 marker_color=_AMBER, opacity=0.7))
            fig.add_trace(go.Bar(name="High", x=domain_names, y=high_vals,
                                 marker_color=_GREEN, opacity=0.7))
            fig.update_layout(
                barmode="group",
                **_ops_layout("MEMBERSHIP FUNCTIONS", height=280),
                legend=dict(font=dict(size=9, color=_DIM), orientation="h",
                            x=0.5, xanchor="center", y=-0.15),
                xaxis=dict(tickangle=-35, tickfont=dict(size=8, color=_DIM)),
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_fuzzy_membership")

        # Fired rules
        if interactions:
            st.markdown(
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.7rem;'
                f'color:{_DIM};margin:8px 0 4px;letter-spacing:1px;">'
                f'FIRED RULES ({len(interactions)})</div>',
                unsafe_allow_html=True,
            )
            rules_html = ""
            for rule in interactions[:8]:
                strength = rule.get("strength", 0)
                scolor = _GREEN if strength > 0.5 else (_AMBER if strength > 0.25 else _DIM)
                rules_html += (
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'padding:4px 8px;margin:2px 0;background:rgba(0,240,255,0.03);'
                    f'border-radius:4px;font-size:0.72rem;">'
                    f'<span style="color:{scolor};font-weight:700;font-family:JetBrains Mono,monospace;'
                    f'min-width:40px;">{strength:.2f}</span>'
                    f'<span style="color:{_TEXT};">{html_module.escape(rule.get("rule", ""))}</span>'
                    f'<span style="color:{_CYAN};margin-left:auto;font-weight:600;">'
                    f'\u2192 {html_module.escape(rule.get("conclusion", ""))}</span></div>'
                )
            st.markdown(rules_html, unsafe_allow_html=True)
    except Exception as exc:
        logger.warning("Fuzzy section render failed: %s", exc)
        st.warning("Fuzzy logic rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 23 HELPERS — GRAPH CENTRALITY & INFLUENCE NETWORK
# ═══════════════════════════════════════════════════════════════════════════

def _render_graph_centrality_section(graph):
    """Render graph centrality and influence network section."""
    try:
        nodes = graph.get("nodes", [])
        edges = graph.get("edges", [])
        insight = graph.get("key_insight", "")

        if insight:
            st.markdown(
                f'<div style="background:rgba(68,136,255,0.06);border:1px solid rgba(68,136,255,0.15);'
                f'border-radius:8px;padding:10px 14px;margin:0.5rem 0;font-size:0.82rem;'
                f'color:{_TEXT};">{html_module.escape(insight)}</div>',
                unsafe_allow_html=True,
            )

        if nodes and go is not None:
            # Network graph with PageRank-sized nodes
            n = len(nodes)
            positions = {}
            for i, nd in enumerate(nodes):
                angle = 2 * math.pi * i / n
                positions[nd["domain"]] = (math.cos(angle), math.sin(angle))

            fig = go.Figure()

            # Draw edges
            for e in edges:
                sp = positions.get(e["source"])
                tp = positions.get(e["target"])
                if sp and tp:
                    fig.add_trace(go.Scatter(
                        x=[sp[0], tp[0]], y=[sp[1], tp[1]],
                        mode="lines",
                        line=dict(width=max(0.5, e["weight"] * 2.5),
                                  color="rgba(0,240,255,0.12)"),
                        showlegend=False, hoverinfo="skip",
                    ))

            # Draw nodes (PageRank determines size)
            for nd in nodes:
                pos = positions.get(nd["domain"], (0, 0))
                color = _DOMAIN_COLORS.get(nd["domain"], _CYAN)
                size = 18 + nd["pagerank"] * 180
                fig.add_trace(go.Scatter(
                    x=[pos[0]], y=[pos[1]],
                    mode="markers+text",
                    marker=dict(size=size, color=color,
                                line=dict(width=2, color="rgba(255,255,255,0.2)")),
                    text=[nd["label"][:7]],
                    textposition="top center",
                    textfont=dict(size=8, color=color),
                    showlegend=False,
                    hovertext=(f"{nd['label']}<br>Score: {nd['score']}<br>"
                               f"PageRank: {nd['pagerank']:.3f}<br>"
                               f"Betweenness: {nd['betweenness']:.3f}"),
                    hoverinfo="text",
                ))

            fig.update_layout(
                **_ops_layout(height=380),
                xaxis=dict(visible=False),
                yaxis=dict(visible=False, scaleanchor="x"),
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_graph_network")

        # Centrality ranking table
        if nodes:
            sorted_nodes = sorted(nodes, key=lambda x: x["pagerank"], reverse=True)
            table_html = (
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.68rem;'
                f'color:{_DIM};margin:8px 0 4px;letter-spacing:1px;">CENTRALITY RANKING</div>'
                f'<div style="background:{_PANEL};border:1px solid rgba(0,240,255,0.1);'
                f'border-radius:6px;padding:8px;font-size:0.72rem;">'
            )
            for i, nd in enumerate(sorted_nodes):
                color = _DOMAIN_COLORS.get(nd["domain"], _CYAN)
                table_html += (
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.03);">'
                    f'<span style="color:{_DIM};min-width:18px;">#{i+1}</span>'
                    f'<span style="color:{color};font-weight:600;min-width:100px;">'
                    f'{nd["label"]}</span>'
                    f'<span style="color:{_TEXT};min-width:50px;">PR:{nd["pagerank"]:.3f}</span>'
                    f'<span style="color:{_DIM};min-width:50px;">BC:{nd["betweenness"]:.3f}</span>'
                    f'<span style="color:{_DIM};">DC:{nd["degree"]:.3f}</span></div>'
                )
            table_html += '</div>'
            st.markdown(table_html, unsafe_allow_html=True)

    except Exception as exc:
        logger.warning("Graph centrality section render failed: %s", exc)
        st.warning("Graph centrality rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 24 HELPERS — DOMAIN CLUSTERING (DBSCAN)
# ═══════════════════════════════════════════════════════════════════════════

def _render_clustering_section(clustering, scores):
    """Render DBSCAN domain clustering section."""
    try:
        clusters = clustering.get("clusters", [])
        noise = clustering.get("noise_domains", [])
        sil = clustering.get("silhouette_score", 0)

        # Silhouette score badge
        sil_color = _GREEN if sil > 0.5 else (_AMBER if sil > 0.2 else _RED)
        st.markdown(
            f'<div style="text-align:center;padding:8px;margin:0.5rem 0;'
            f'border:1px solid {sil_color}33;border-radius:8px;background:{sil_color}0a;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1.5px;">SILHOUETTE SCORE</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1.5rem;'
            f'font-weight:700;color:{sil_color};">{sil:.3f}</span></div>',
            unsafe_allow_html=True,
        )

        # Treemap via Plotly
        if clusters and go is not None:
            labels = []
            parents = []
            values = []
            colors = []
            _cl_colors = [_CYAN, _GREEN, _PURPLE, _AMBER, _BLUE]
            for ci, cl in enumerate(clusters):
                cl_label = cl.get("label", f"Cluster {ci}")
                cl_color = _cl_colors[ci % len(_cl_colors)]
                labels.append(cl_label)
                parents.append("")
                values.append(cl.get("centroid_score", 50) * len(cl.get("members", [])))
                colors.append(cl_color)
                for member in cl.get("members", []):
                    labels.append(member)
                    parents.append(cl_label)
                    # Find score
                    domain_key = None
                    for dk, dl in (("habitability", "Habitability"),
                                   ("agriculture", "Agriculture"),
                                   ("ecology", "Ecology"),
                                   ("hazard_safety", "Hazard Safety"),
                                   ("water_resources", "Water Resources"),
                                   ("infrastructure", "Infrastructure"),
                                   ("climate_comfort", "Climate Comfort"),
                                   ("economic_potential", "Economic Potential"),
                                   ("air_environment", "Air Environment"),
                                   ("geological_stability", "Geological Stability")):
                        if dl == member:
                            domain_key = dk
                            break
                    s = scores.get(domain_key, 50) if domain_key else 50
                    if not isinstance(s, (int, float)):
                        s = 50
                    values.append(s)
                    colors.append(cl_color)

            fig = go.Figure(go.Treemap(
                labels=labels,
                parents=parents,
                values=values,
                marker=dict(
                    colors=colors,
                    line=dict(width=1, color=_PANEL),
                ),
                textfont=dict(size=11, color=_TEXT),
                hovertemplate="<b>%{label}</b><br>Value: %{value:.0f}<extra></extra>",
            ))
            fig.update_layout(
                **_ops_layout(height=300),
                margin=dict(l=5, r=5, t=5, b=5),
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_dbscan_treemap")

        # Cluster details
        for cl in clusters:
            char = cl.get("characterization", "")
            members = ", ".join(cl.get("members", []))
            coh = cl.get("coherence", 0)
            avg = cl.get("centroid_score", 0)
            color = _GREEN if avg >= 60 else (_AMBER if avg >= 40 else _RED)
            st.markdown(
                f'<div style="background:{_PANEL};border:1px solid {color}22;'
                f'border-left:3px solid {color};border-radius:0 6px 6px 0;'
                f'padding:8px 12px;margin:4px 0;font-size:0.78rem;">'
                f'<span style="color:{color};font-weight:700;">{cl.get("label", "")}</span>'
                f' &mdash; {html_module.escape(char)}'
                f'<br/><span style="color:{_DIM};font-size:0.7rem;">'
                f'Members: {html_module.escape(members)} | '
                f'Avg: {avg:.0f} | Coherence: {coh:.2f}</span></div>',
                unsafe_allow_html=True,
            )

        if noise:
            st.markdown(
                f'<div style="color:{_DIM};font-size:0.72rem;margin-top:4px;">'
                f'Noise domains: {", ".join(noise)}</div>',
                unsafe_allow_html=True,
            )

    except Exception as exc:
        logger.warning("Clustering section render failed: %s", exc)
        st.warning("Clustering rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 25 HELPERS — ROBUST ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════════════════════

def _render_robust_anomaly_section(anomaly_data):
    """Render robust anomaly detection ensemble section."""
    try:
        anomalies = anomaly_data.get("anomalies", {})
        stats = anomaly_data.get("baseline_stats", {})
        profile = anomaly_data.get("overall_profile", "")
        count = anomaly_data.get("anomaly_count", 0)

        # Profile badge
        prof_color = _GREEN if count == 0 else (_AMBER if count <= 2 else _RED)
        st.markdown(
            f'<div style="text-align:center;padding:10px;margin:0.5rem 0;'
            f'border:1px solid {prof_color}33;border-radius:8px;background:{prof_color}0a;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1.5px;">ANOMALY PROFILE</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.85rem;'
            f'font-weight:700;color:{prof_color};">{html_module.escape(profile)}</span></div>',
            unsafe_allow_html=True,
        )

        # Strip plot with IQR bands
        if anomalies and go is not None:
            mean = stats.get("mean", 50)
            q1 = stats.get("q1", 40)
            q3 = stats.get("q3", 60)
            iqr = stats.get("iqr", 20)

            domains_list = list(anomalies.keys())
            scores_list = [anomalies[d].get("score", 50) for d in domains_list]
            labels_list = [anomalies[d].get("label", d) for d in domains_list]
            sev_list = [anomalies[d].get("severity", "NORMAL") for d in domains_list]
            color_list = [_RED if s == "CRITICAL" else (_AMBER if s == "WARNING"
                         else (_CYAN if s == "NOTABLE" else _DIM)) for s in sev_list]

            fig = go.Figure()

            # IQR band
            fig.add_shape(type="rect", x0=-0.5, x1=len(domains_list) - 0.5,
                          y0=q1 - 1.5 * iqr, y1=q3 + 1.5 * iqr,
                          fillcolor="rgba(0,240,255,0.04)", line_width=0)
            # Q1-Q3 band
            fig.add_shape(type="rect", x0=-0.5, x1=len(domains_list) - 0.5,
                          y0=q1, y1=q3,
                          fillcolor="rgba(0,240,255,0.08)", line_width=0)
            # Mean line
            fig.add_hline(y=mean, line_dash="dash", line_color="rgba(0,240,255,0.3)",
                          line_width=1)

            # Points
            fig.add_trace(go.Scatter(
                x=list(range(len(domains_list))),
                y=scores_list,
                mode="markers+text",
                marker=dict(size=14, color=color_list,
                            line=dict(width=2, color="rgba(255,255,255,0.15)")),
                text=[f"{s:.0f}" for s in scores_list],
                textposition="top center",
                textfont=dict(size=8, color=_TEXT),
                showlegend=False,
                hovertext=[f"{l}<br>Score: {s:.0f}<br>Severity: {sv}"
                           for l, s, sv in zip(labels_list, scores_list, sev_list)],
                hoverinfo="text",
            ))

            fig.update_layout(
                **_ops_layout("ANOMALY STRIP PLOT", height=300),
                xaxis=dict(tickvals=list(range(len(domains_list))),
                           ticktext=[l[:8] for l in labels_list],
                           tickangle=-35, tickfont=dict(size=8, color=_DIM)),
                yaxis=dict(title="Score", gridcolor="rgba(255,255,255,0.03)"),
            )
            # Annotations
            fig.add_annotation(x=len(domains_list) - 0.3, y=mean,
                               text=f"Mean: {mean:.0f}", showarrow=False,
                               font=dict(size=8, color=_CYAN))

            st.plotly_chart(fig, use_container_width=True, key="fic_anomaly_strip")

        # Anomaly details
        for d, info in anomalies.items():
            if not isinstance(info, dict):
                continue
            sev = info.get("severity", "NORMAL")
            if sev == "NORMAL":
                continue
            sev_color = _RED if sev == "CRITICAL" else (_AMBER if sev == "WARNING" else _CYAN)
            label = info.get("label", d)
            votes = info.get("ensemble_votes", 0)
            z_val = info.get("z_value", 0)
            dev = info.get("deviation_from_mean", 0)
            methods = []
            if info.get("z_score_outlier"):
                methods.append("Z-Score")
            if info.get("iqr_outlier"):
                methods.append("IQR")
            if info.get("grubbs_outlier"):
                methods.append("Grubbs")

            st.markdown(
                f'<div style="background:{_PANEL};border:1px solid {sev_color}22;'
                f'border-left:3px solid {sev_color};border-radius:0 6px 6px 0;'
                f'padding:6px 12px;margin:3px 0;font-size:0.75rem;">'
                f'<span style="color:{sev_color};font-weight:700;">{sev}</span>'
                f' <span style="color:{_TEXT};font-weight:600;">{html_module.escape(label)}</span>'
                f' &mdash; Z={z_val:.1f}, \u0394={dev:+.0f}, '
                f'Methods: {", ".join(methods)} ({votes}/3)</div>',
                unsafe_allow_html=True,
            )

    except Exception as exc:
        logger.warning("Anomaly section render failed: %s", exc)
        st.warning("Anomaly detection rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 26 HELPERS — VIKOR COMPROMISE RANKING
# ═══════════════════════════════════════════════════════════════════════════

def _render_vikor_section(vikor):
    """Render VIKOR compromise ranking section."""
    try:
        rankings = vikor.get("rankings", [])
        compromise = vikor.get("compromise_label", "Unknown")
        stability = vikor.get("stability_condition", False)

        # Compromise badge
        st.markdown(
            f'<div style="text-align:center;padding:10px;margin:0.5rem 0;'
            f'border:1px solid {_AMBER}33;border-radius:8px;background:{_AMBER}0a;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1.5px;">VIKOR COMPROMISE SOLUTION</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1.2rem;'
            f'font-weight:700;color:{_AMBER};">{html_module.escape(compromise)}</span>'
            f'<br/><span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{"#00ff88" if stability else "#ff3344"};">'
            f'Stability: {"CONFIRMED" if stability else "UNSTABLE"}</span></div>',
            unsafe_allow_html=True,
        )

        # Rankings bar chart
        if rankings and go is not None:
            ranked = sorted(rankings, key=lambda r: r["Q"])
            labels = [r["label"][:10] for r in ranked]
            q_vals = [r["Q"] for r in ranked]
            s_vals = [r["S"] for r in ranked]
            colors = [_GREEN if r["rank"] <= 3 else (_AMBER if r["rank"] <= 6 else _RED) for r in ranked]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=labels, y=q_vals, name="Q (Compromise)",
                marker_color=colors, opacity=0.85,
                text=[f"{q:.3f}" for q in q_vals],
                textposition="outside", textfont=dict(size=8, color=_TEXT),
            ))
            fig.update_layout(
                **_ops_layout("VIKOR Q-VALUES (lower = better)", height=280),
                xaxis=dict(tickangle=-35, tickfont=dict(size=8, color=_DIM)),
                yaxis=dict(title="Q Value", gridcolor="rgba(255,255,255,0.03)"),
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_vikor_bar")

    except Exception as exc:
        logger.warning("VIKOR section render failed: %s", exc)
        st.warning("VIKOR rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 27 HELPERS — MARKOV CHAIN STABILITY
# ═══════════════════════════════════════════════════════════════════════════

def _render_markov_section(markov):
    """Render Markov chain stability section."""
    try:
        stability_idx = markov.get("stability_index", 50)
        trajectory = markov.get("system_trajectory", "STABLE")
        entropy_rate = markov.get("entropy_rate", 0)
        states = markov.get("states", [])
        ss = markov.get("steady_state", [])
        tm = markov.get("transition_matrix", [])

        traj_color = _GREEN if trajectory == "IMPROVING" else (_AMBER if trajectory == "STABLE" else _RED)
        st.markdown(
            f'<div style="text-align:center;padding:10px;margin:0.5rem 0;'
            f'border:1px solid {traj_color}33;border-radius:8px;background:{traj_color}0a;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1.5px;">SYSTEM TRAJECTORY</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1.3rem;'
            f'font-weight:700;color:{traj_color};">{trajectory}</span>'
            f'<br/><span style="font-size:0.72rem;color:{_DIM};">'
            f'Stability: {stability_idx:.0f}/100 | '
            f'Entropy Rate: {entropy_rate:.3f} bits</span></div>',
            unsafe_allow_html=True,
        )

        # Transition matrix heatmap
        if tm and states:
            fig = create_transition_heatmap(tm, states)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="fic_markov_heatmap")

        # Steady state distribution
        if ss and states and go is not None:
            state_colors = [_RED, _AMBER, _CYAN, _GREEN]
            fig = go.Figure(go.Bar(
                x=states, y=ss,
                marker_color=state_colors[:len(states)],
                text=[f"{v:.1%}" for v in ss],
                textposition="outside", textfont=dict(size=9, color=_TEXT),
            ))
            fig.update_layout(
                **_ops_layout("STEADY-STATE DISTRIBUTION", height=230),
                yaxis=dict(title="Probability", gridcolor="rgba(255,255,255,0.03)"),
                xaxis=dict(tickfont=dict(size=10, color=_TEXT)),
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_markov_ss")

    except Exception as exc:
        logger.warning("Markov section render failed: %s", exc)
        st.warning("Markov chain rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 28 HELPERS — ENTROPY & INFORMATION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def _render_entropy_section(entropy):
    """Render entropy and information analysis section."""
    try:
        H = entropy.get("system_entropy", 0)
        H_max = entropy.get("max_entropy", 0)
        redundancy = entropy.get("redundancy", 0)
        profile = entropy.get("information_profile", "")
        diversity = entropy.get("diversity_index", 0)
        effective = entropy.get("effective_domains", 0)
        most_info = entropy.get("most_informative_label", "")
        domain_data = entropy.get("domain_entropy", {})

        prof_color = _GREEN if "HIGH" in profile else (_AMBER if "BALANCED" in profile else _RED)
        st.markdown(
            f'<div style="text-align:center;padding:10px;margin:0.5rem 0;'
            f'border:1px solid {prof_color}33;border-radius:8px;background:{prof_color}0a;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1.5px;">INFORMATION PROFILE</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1.1rem;'
            f'font-weight:700;color:{prof_color};">{html_module.escape(profile)}</span>'
            f'<br/><span style="font-size:0.72rem;color:{_DIM};">'
            f'H={H:.3f} / H_max={H_max:.3f} | '
            f'Redundancy: {redundancy:.1%} | '
            f'Effective domains: {effective:.1f}</span></div>',
            unsafe_allow_html=True,
        )

        # Entropy contribution chart
        if domain_data and go is not None:
            sorted_domains = sorted(domain_data.items(),
                                    key=lambda x: x[1].get("entropy_contribution_pct", 0),
                                    reverse=True)
            labels = [v.get("label", k)[:10] for k, v in sorted_domains]
            contrib = [v.get("entropy_contribution_pct", 0) for _, v in sorted_domains]
            surprise = [v.get("surprise_value", 0) for _, v in sorted_domains]
            colors = [_DOMAIN_COLORS.get(k, _CYAN) for k, _ in sorted_domains]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=labels, y=contrib, name="Entropy %",
                marker_color=colors, opacity=0.8,
                text=[f"{c:.1f}%" for c in contrib],
                textposition="outside", textfont=dict(size=8, color=_TEXT),
            ))
            fig.update_layout(
                **_ops_layout("ENTROPY CONTRIBUTION PER DOMAIN", height=260),
                xaxis=dict(tickangle=-35, tickfont=dict(size=8, color=_DIM)),
                yaxis=dict(title="% Contribution", gridcolor="rgba(255,255,255,0.03)"),
            )
            st.plotly_chart(fig, use_container_width=True, key="fic_entropy_chart")

    except Exception as exc:
        logger.warning("Entropy section render failed: %s", exc)
        st.warning("Entropy analysis rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 29 HELPERS — PARETO FRONTIER OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════

def _render_pareto_section(pareto):
    """Render Pareto frontier optimization section."""
    try:
        optimal = pareto.get("pareto_optimal", [])
        dominated = pareto.get("dominated", [])
        efficiency = pareto.get("pareto_efficiency", 0)
        trade_offs = pareto.get("trade_off_insights", [])

        eff_color = _GREEN if efficiency >= 0.6 else (_AMBER if efficiency >= 0.3 else _RED)
        st.markdown(
            f'<div style="text-align:center;padding:10px;margin:0.5rem 0;'
            f'border:1px solid {eff_color}33;border-radius:8px;background:{eff_color}0a;">'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};letter-spacing:1.5px;">PARETO EFFICIENCY</span><br/>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:1.5rem;'
            f'font-weight:700;color:{eff_color};">{efficiency:.0%}</span>'
            f'<br/><span style="font-size:0.72rem;color:{_DIM};">'
            f'{len(optimal)} optimal / {len(dominated)} dominated</span></div>',
            unsafe_allow_html=True,
        )

        # Pareto scatter chart
        fig = create_pareto_scatter(pareto)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="fic_pareto_scatter")

        # Trade-off insights
        if trade_offs:
            st.markdown(
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.7rem;'
                f'color:{_DIM};margin:8px 0 4px;letter-spacing:1px;">TRADE-OFF INSIGHTS</div>',
                unsafe_allow_html=True,
            )
            for ti in trade_offs:
                st.markdown(
                    f'<div style="padding:4px 10px;margin:2px 0;font-size:0.75rem;'
                    f'color:{_TEXT};border-left:2px solid {_GREEN}33;">'
                    f'{html_module.escape(ti)}</div>',
                    unsafe_allow_html=True,
                )

        # Dominated domains with improvement vectors
        vectors = pareto.get("improvement_vectors", {})
        if vectors:
            for d, info in vectors.items():
                priority = info.get("priority", "LOW")
                pc = _RED if priority == "HIGH" else (_AMBER if priority == "MEDIUM" else _DIM)
                st.markdown(
                    f'<div style="background:{_PANEL};border:1px solid {pc}22;'
                    f'border-left:3px solid {pc};border-radius:0 6px 6px 0;'
                    f'padding:6px 12px;margin:3px 0;font-size:0.75rem;">'
                    f'<span style="color:{pc};font-weight:700;">{priority}</span> '
                    f'<span style="color:{_TEXT};font-weight:600;">'
                    f'{html_module.escape(info.get("label", d))}</span>'
                    f' &mdash; Current: {info.get("current", 0):.0f} \u2192 '
                    f'Target: {info.get("target", 0):.0f} '
                    f'(gap: {info.get("gap", 0):.0f})</div>',
                    unsafe_allow_html=True,
                )

    except Exception as exc:
        logger.warning("Pareto section render failed: %s", exc)
        st.warning("Pareto frontier rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 30 — GAME THEORY (NASH EQUILIBRIUM & SHAPLEY VALUES)
# ═══════════════════════════════════════════════════════════════════════════

def _render_game_theory_section(gt, scores):
    """Render game theory analysis: Nash equilibrium & Shapley values."""
    try:
        nash = gt.get("nash_equilibrium", {})
        shapley = gt.get("shapley_values", {})
        insight = gt.get("strategy_insight", "")
        mvp = gt.get("most_valuable_player", "")
        free_riders = gt.get("free_rider_risk", [])
        coop_bonus = gt.get("cooperation_bonus", 0)
        stable = gt.get("equilibrium_stable", False)
        iters = gt.get("iterations_to_converge", 0)

        # Insight panel
        if insight:
            st.markdown(
                f'<div style="background:{_PANEL};border:1px solid {_PURPLE}22;'
                f'padding:10px 14px;border-radius:8px;font-size:0.82rem;color:{_TEXT};'
                f'margin-bottom:12px;border-left:3px solid {_PURPLE}">{html_module.escape(insight)}</div>',
                unsafe_allow_html=True,
            )

        # KPI strip
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{_GREEN}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">MVP (Shapley)</div>'
                f'<div style="font-size:0.95rem;color:{_GREEN};font-weight:700">'
                f'{html_module.escape(mvp[:18])}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{_CYAN}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Cooperation Bonus</div>'
                f'<div style="font-size:0.95rem;color:{_CYAN};font-weight:700">'
                f'+{coop_bonus:.1f}%</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            eq_color = _GREEN if stable else _AMBER
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{eq_color}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Equilibrium</div>'
                f'<div style="font-size:0.95rem;color:{eq_color};font-weight:700">'
                f'{"Stable" if stable else "Unstable"} ({iters} iters)</div></div>',
                unsafe_allow_html=True,
            )
        with c4:
            fr_count = len(free_riders)
            fr_color = _RED if fr_count > 2 else (_AMBER if fr_count else _GREEN)
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{fr_color}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Free-Rider Risk</div>'
                f'<div style="font-size:0.95rem;color:{fr_color};font-weight:700">'
                f'{fr_count} domain(s)</div></div>',
                unsafe_allow_html=True,
            )

        # Shapley bar chart
        try:
            if shapley:
                sorted_shap = sorted(shapley.items(), key=lambda x: x[1], reverse=True)
                domains_s = [d for d, _ in sorted_shap]
                vals_s = [v for _, v in sorted_shap]
                colors = [_GREEN if nash.get(d) == "invest" else _RED for d in domains_s]
                fig = go.Figure(go.Bar(
                    x=vals_s, y=[INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)[:16] for d in domains_s], orientation="h",
                    marker=dict(color=colors, line=dict(width=0)),
                    hovertemplate="%{y}: %{x:.1f}<extra></extra>",
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(5,5,16,0.6)",
                    font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
                    height=280, margin=dict(l=120, r=20, t=10, b=30),
                    xaxis=dict(title="Shapley Value", gridcolor="rgba(255,255,255,0.03)"),
                    yaxis=dict(autorange="reversed"),
                )
                st.plotly_chart(fig, use_container_width=True, key="fc_game_shapley")
        except Exception:
            pass

    except Exception as exc:
        logger.warning("Game theory section render failed: %s", exc)
        st.warning("Game theory rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 31 — CELLULAR AUTOMATA EVOLUTION
# ═══════════════════════════════════════════════════════════════════════════

def _render_cellular_automata_section(ca):
    """Render cellular automata evolution heatmap."""
    try:
        evolution = ca.get("evolution", [])
        domain_order = ca.get("domain_order", [])
        initial = ca.get("initial_states", {})
        final = ca.get("final_states", {})
        improving = ca.get("improving_domains", [])
        degrading = ca.get("degrading_domains", [])
        stable = ca.get("stable_domains", [])
        attractor = ca.get("attractor_detected", False)
        insight = ca.get("prediction_insight", "")
        labels_map = ca.get("state_labels", {})

        if insight:
            st.markdown(
                f'<div style="background:{_PANEL};border:1px solid {_AMBER}22;'
                f'padding:10px 14px;border-radius:8px;font-size:0.82rem;color:{_TEXT};'
                f'margin-bottom:12px;border-left:3px solid {_AMBER}">{html_module.escape(insight)}</div>',
                unsafe_allow_html=True,
            )

        # Summary chips
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{_GREEN}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Improving</div>'
                f'<div style="font-size:0.95rem;color:{_GREEN};font-weight:700">'
                f'{len(improving)} domain(s)</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{_RED}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Degrading</div>'
                f'<div style="font-size:0.95rem;color:{_RED};font-weight:700">'
                f'{len(degrading)} domain(s)</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            att_color = _GREEN if attractor else _AMBER
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{att_color}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Attractor</div>'
                f'<div style="font-size:0.95rem;color:{att_color};font-weight:700">'
                f'{"Detected" if attractor else "None"}</div></div>',
                unsafe_allow_html=True,
            )

        # Evolution heatmap
        try:
            if evolution and domain_order:
                short_labels = [INTELLIGENCE_DOMAINS.get(d, {}).get("name", d).split()[0][:8] for d in domain_order]
                fig = go.Figure(go.Heatmap(
                    z=evolution,
                    x=short_labels,
                    y=[f"Gen {i}" for i in range(len(evolution))],
                    colorscale=[[0, _RED], [0.25, _AMBER], [0.5, "#555"], [0.75, _CYAN], [1, _GREEN]],
                    showscale=True,
                    colorbar=dict(title=dict(text="State", font=dict(size=9, color=_DIM)),
                                  tickfont=dict(size=8, color=_DIM)),
                    hoverongaps=False,
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(5,5,16,0.6)",
                    font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
                    height=350, margin=dict(l=60, r=20, t=10, b=40),
                    xaxis=dict(tickfont=dict(size=8)),
                    yaxis=dict(autorange="reversed", tickfont=dict(size=8)),
                )
                st.plotly_chart(fig, use_container_width=True, key="fc_ca_heatmap")
        except Exception:
            pass

    except Exception as exc:
        logger.warning("Cellular automata section render failed: %s", exc)
        st.warning("Cellular automata rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 32 — GENETIC ALGORITHM OPTIMIZER
# ═══════════════════════════════════════════════════════════════════════════

def _render_genetic_algorithm_section(ga, scores):
    """Render genetic algorithm resource optimization results."""
    try:
        alloc = ga.get("optimal_allocation", {})
        fitness = ga.get("optimal_fitness", 0)
        baseline = ga.get("baseline_fitness", 0)
        improvement = ga.get("improvement_pct", 0)
        top_priority = ga.get("top_priority", "")
        focus = ga.get("recommended_focus", [])
        convergence = ga.get("convergence", [])
        insight = ga.get("strategy_insight", "")

        if insight:
            st.markdown(
                f'<div style="background:{_PANEL};border:1px solid {_GREEN}22;'
                f'padding:10px 14px;border-radius:8px;font-size:0.82rem;color:{_TEXT};'
                f'margin-bottom:12px;border-left:3px solid {_GREEN}">{html_module.escape(insight)}</div>',
                unsafe_allow_html=True,
            )

        # KPI strip
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{_GREEN}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Top Priority</div>'
                f'<div style="font-size:0.9rem;color:{_GREEN};font-weight:700">'
                f'{html_module.escape(top_priority[:18])}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            imp_color = _GREEN if improvement > 5 else (_AMBER if improvement > 0 else _RED)
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{imp_color}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Improvement</div>'
                f'<div style="font-size:0.95rem;color:{imp_color};font-weight:700">'
                f'+{improvement:.1f}%</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{_CYAN}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Recommended Focus</div>'
                f'<div style="font-size:0.8rem;color:{_CYAN};font-weight:700">'
                f'{", ".join(INTELLIGENCE_DOMAINS.get(d, {}).get("name", d).split()[0] for d in focus[:3])}</div></div>',
                unsafe_allow_html=True,
            )

        col_alloc, col_conv = st.columns(2)

        # Allocation donut
        with col_alloc:
            try:
                if alloc:
                    sorted_a = sorted(alloc.items(), key=lambda x: x[1], reverse=True)
                    fig = go.Figure(go.Pie(
                        labels=[INTELLIGENCE_DOMAINS.get(d, {}).get("name", d).split()[0][:10] for d, _ in sorted_a],
                        values=[round(v * 100, 1) for _, v in sorted_a],
                        hole=0.5,
                        marker=dict(colors=[_DOMAIN_COLORS.get(d, _CYAN) for d, _ in sorted_a]),
                        textinfo="label+percent",
                        textfont=dict(size=8, color=_TEXT),
                    ))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color=_DIM, size=9),
                        height=260, margin=dict(l=10, r=10, t=10, b=10),
                        showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True, key="fc_ga_alloc")
            except Exception:
                pass

        # Convergence curve
        with col_conv:
            try:
                if convergence:
                    fig = go.Figure(go.Scatter(
                        x=list(range(len(convergence))),
                        y=convergence,
                        mode="lines",
                        line=dict(color=_GREEN, width=2),
                        fill="tozeroy",
                        fillcolor=f"rgba(0,255,136,0.08)",
                    ))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(5,5,16,0.6)",
                        font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
                        height=260, margin=dict(l=50, r=10, t=10, b=30),
                        xaxis=dict(title="Generation", gridcolor="rgba(255,255,255,0.03)"),
                        yaxis=dict(title="Fitness", gridcolor="rgba(255,255,255,0.03)"),
                    )
                    st.plotly_chart(fig, use_container_width=True, key="fc_ga_conv")
            except Exception:
                pass

    except Exception as exc:
        logger.warning("Genetic algorithm section render failed: %s", exc)
        st.warning("Genetic algorithm rendering error.")


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 33 — WAVELET MULTI-RESOLUTION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def _render_wavelet_section(wv):
    """Render wavelet multi-resolution analysis."""
    try:
        energy_dist = wv.get("energy_distribution", {})
        dominant = wv.get("dominant_scale", "")
        dom_interp = wv.get("dominant_interpretation", "")
        smoothness = wv.get("smoothness", 0)
        complexity = wv.get("signal_complexity", "Unknown")
        anomaly_coeffs = wv.get("anomaly_coefficients", [])
        insight = wv.get("analysis_insight", "")

        if insight:
            st.markdown(
                f'<div style="background:{_PANEL};border:1px solid {_CYAN}22;'
                f'padding:10px 14px;border-radius:8px;font-size:0.82rem;color:{_TEXT};'
                f'margin-bottom:12px;border-left:3px solid {_CYAN}">{html_module.escape(insight)}</div>',
                unsafe_allow_html=True,
            )

        # KPI strip
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{_CYAN}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Dominant Scale</div>'
                f'<div style="font-size:0.95rem;color:{_CYAN};font-weight:700">'
                f'{dominant}</div>'
                f'<div style="font-size:0.7rem;color:{_DIM}">{html_module.escape(dom_interp)}</div></div>',
                unsafe_allow_html=True,
            )
        with c2:
            sm_color = _GREEN if smoothness > 0.7 else (_AMBER if smoothness > 0.4 else _RED)
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{sm_color}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Smoothness</div>'
                f'<div style="font-size:0.95rem;color:{sm_color};font-weight:700">'
                f'{smoothness:.2f}</div></div>',
                unsafe_allow_html=True,
            )
        with c3:
            cx_color = _GREEN if complexity == "Simple" else (_AMBER if complexity == "Moderate" else _RED)
            st.markdown(
                f'<div class="exec-kpi-card" style="border-color:{cx_color}22">'
                f'<div style="font-size:0.65rem;color:{_DIM}">Complexity</div>'
                f'<div style="font-size:0.95rem;color:{cx_color};font-weight:700">'
                f'{complexity}</div></div>',
                unsafe_allow_html=True,
            )

        # Energy distribution bar chart
        try:
            if energy_dist:
                levels = sorted(energy_dist.keys())
                values = [energy_dist[l] for l in levels]
                colors_e = [_CYAN if l == dominant else _DIM for l in levels]
                fig = go.Figure(go.Bar(
                    x=levels, y=values,
                    marker=dict(color=colors_e, line=dict(width=0)),
                    text=[f"{v:.1f}%" for v in values],
                    textposition="outside",
                    textfont=dict(size=9, color=_TEXT),
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(5,5,16,0.6)",
                    font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
                    height=240, margin=dict(l=40, r=20, t=20, b=30),
                    xaxis=dict(title="Wavelet Level"),
                    yaxis=dict(title="Energy %", gridcolor="rgba(255,255,255,0.03)"),
                )
                st.plotly_chart(fig, use_container_width=True, key="fc_wavelet_energy")
        except Exception:
            pass

        # Anomaly coefficients
        if anomaly_coeffs:
            st.markdown(
                f'<div style="font-size:0.72rem;color:{_DIM};margin-top:8px;letter-spacing:1px">'
                f'ANOMALOUS WAVELET COEFFICIENTS</div>',
                unsafe_allow_html=True,
            )
            for ac in anomaly_coeffs[:5]:
                d_key = ac.get("domain", "?")
                d_name = INTELLIGENCE_DOMAINS.get(d_key, {}).get("name", d_key)
                level = ac.get("level", "?")
                mag = ac.get("magnitude", 0)
                mc = _RED if abs(mag) > 15 else _AMBER
                st.markdown(
                    f'<div style="font-size:0.78rem;color:{_TEXT};padding:2px 0">'
                    f'<span style="color:{mc};font-weight:700">{level}</span> '
                    f'{html_module.escape(d_name)} &mdash; magnitude {mag:.1f}</div>',
                    unsafe_allow_html=True,
                )

    except Exception as exc:
        logger.warning("Wavelet section render failed: %s", exc)
        st.warning("Wavelet analysis rendering error.")


# ---------------------------------------------------------------------------
# SECTION 34 HELPERS
# ---------------------------------------------------------------------------

def _render_omniscient_section(omniscient, scores, details=None, raw_data=None):
    """Render the Omniscient Intelligence Synthesis section with full analytics.
    Phase 3A: integrated search via search_and_visualize()."""
    try:
        # Phase 3A: Search integration at top
        search_query = st.text_input(
            "Search Intelligence",
            value="",
            placeholder="Search domains (e.g. water, soil, climate, hazard...)",
            key="fic_omniscient_search",
        )
        if search_query and search_query.strip():
            try:
                search_result = search_and_visualize(
                    search_query.strip(),
                    scores if isinstance(scores, dict) else {},
                    details if isinstance(details, dict) else {},
                    raw_data if isinstance(raw_data, dict) else {},
                )
                synthesis = search_result.get("synthesis", "")
                relevant_data = search_result.get("relevant_data", {})
                suggested_charts = search_result.get("suggested_charts", [])

                # Display synthesis
                if synthesis:
                    st.markdown(
                        f'<div style="border:1px solid {_CYAN}33;border-radius:8px;'
                        f'padding:12px;margin:8px 0;background:{_CYAN}05;'
                        f'font-family:JetBrains Mono,monospace;font-size:0.72rem;'
                        f'color:{_TEXT};line-height:1.6;">'
                        f'{html_module.escape(str(synthesis))}</div>',
                        unsafe_allow_html=True,
                    )

                # Display matched domains with scores and details
                if relevant_data:
                    for domain, info in relevant_data.items():
                        d_score = info.get("score", 0)
                        sc = _GREEN if d_score >= 70 else (_AMBER if d_score >= 40 else _RED)
                        d_name = html_module.escape(str(domain))
                        with st.expander(f"{d_name}: {d_score:.0f}/100", expanded=False):
                            # Domain details
                            d_details = info.get("details", {})
                            if d_details:
                                for k, v in list(d_details.items())[:10]:
                                    st.markdown(
                                        f'<span style="color:{_DIM};font-size:0.65rem;">'
                                        f'{html_module.escape(str(k))}:</span> '
                                        f'<span style="color:{_TEXT};font-size:0.68rem;">'
                                        f'{html_module.escape(str(v))}</span>',
                                        unsafe_allow_html=True,
                                    )

                # Mini suggested charts
                if suggested_charts and go is not None:
                    chart_cols = st.columns(min(3, len(suggested_charts)))
                    for ci, chart_info in enumerate(suggested_charts[:3]):
                        d = chart_info.get("domain", "")
                        ct = chart_info.get("chart_type", "bar")
                        d_name = chart_info.get("domain_name", d)
                        d_score = float((scores or {}).get(d, 0))
                        with chart_cols[ci % len(chart_cols)]:
                            if ct == "gauge":
                                fig_mini = _gauge_chart(d_score, d_name, 100,
                                                        _GREEN if d_score >= 60 else _AMBER,
                                                        160)
                                st.plotly_chart(fig_mini, use_container_width=True,
                                                key=f"fic_search_gauge_{ci}")
                            elif ct == "radar" and isinstance(scores, dict):
                                # Mini radar with just relevant domains
                                r_domains = list(relevant_data.keys())[:6]
                                r_vals = [float(scores.get(rd, 0)) for rd in r_domains]
                                if r_vals:
                                    r_domains_c = r_domains + [r_domains[0]]
                                    r_vals_c = r_vals + [r_vals[0]]
                                    fig_r = go.Figure(go.Scatterpolar(
                                        r=r_vals_c, theta=r_domains_c,
                                        fill="toself", fillcolor=_hex_rgba(_CYAN, 0.19),
                                        line=dict(color=_CYAN, width=2),
                                    ))
                                    fig_r.update_layout(
                                        height=180, margin=dict(l=20, r=20, t=20, b=20),
                                        paper_bgcolor=_BG, plot_bgcolor=_BG,
                                        polar=dict(bgcolor=_BG,
                                                   radialaxis=dict(visible=True,
                                                                   range=[0, 100],
                                                                   gridcolor=_hex_rgba(_DIM, 0.13))),
                                        showlegend=False,
                                    )
                                    st.plotly_chart(fig_r, use_container_width=True,
                                                    key=f"fic_search_radar_{ci}")
                            else:
                                # Default: simple bar
                                fig_b = go.Figure(go.Bar(
                                    x=[d_score], y=[d_name], orientation="h",
                                    marker=dict(color=_GREEN if d_score >= 60 else _AMBER),
                                    text=[f"{d_score:.0f}"], textposition="auto",
                                ))
                                fig_b.update_layout(
                                    height=100, margin=dict(l=10, r=10, t=10, b=10),
                                    paper_bgcolor=_BG, plot_bgcolor=_BG,
                                    xaxis=dict(range=[0, 100], showgrid=False),
                                    yaxis=dict(showticklabels=True),
                                )
                                st.plotly_chart(fig_b, use_container_width=True,
                                                key=f"fic_search_bar_{ci}")

                st.markdown("<hr style='border-color:#1a1f2e;margin:12px 0;'>",
                            unsafe_allow_html=True)
            except Exception as search_exc:
                logger.warning("Omniscient search failed: %s", search_exc)

        omni_score = omniscient.get("omniscient_score", 0)
        grade = omniscient.get("omniscient_grade", "?")
        ci = omniscient.get("confidence_interval", [0, 0])
        completeness = omniscient.get("data_completeness", 0)
        convergence = omniscient.get("convergence_map", {})
        insights = omniscient.get("key_insights", [])
        narrative = omniscient.get("narrative", "")
        component_scores = omniscient.get("component_scores", {})
        mcgdm = omniscient.get("mcgdm", {})
        er = omniscient.get("evidential_reasoning", {})
        copula_data = omniscient.get("copula", {})
        enhanced_ds = omniscient.get("enhanced_ds", {})

        # Grade color
        if omni_score >= 75:
            gc = _GREEN
        elif omni_score >= 50:
            gc = _AMBER
        else:
            gc = _RED

        # --- Row 1: Grade badge (centered) ---
        safe_grade = html_module.escape(str(grade))
        st.markdown(
            f'<div style="text-align:center;padding:16px;margin:0.5rem 0;'
            f'border:1px solid {gc}33;border-radius:10px;background:{gc}08;">'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.6rem;'
            f'color:{_DIM};letter-spacing:1.5px;">OMNISCIENT INTELLIGENCE GRADE</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:3rem;'
            f'font-weight:900;color:{gc};margin:4px 0;">{safe_grade}</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:1.2rem;'
            f'color:{gc};">{omni_score:.1f}/100</div>'
            f'<div style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{_DIM};margin-top:4px;">CI: [{ci[0]:.1f}, {ci[1]:.1f}]</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # --- Row 2: 5 KPI cards ---
        kpi_cols = st.columns(5)
        _metric_card(kpi_cols[0], "SCORE", f"{omni_score:.1f}", gc)
        _metric_card(kpi_cols[1], "CONFIDENCE", f"{ci[1] - ci[0]:.1f}", _CYAN)
        _metric_card(kpi_cols[2], "DATA COMPLETE", f"{completeness:.0f}%", _GREEN)
        _metric_card(kpi_cols[3], "CONSENSUS", f"{mcgdm.get('consensus_degree', 0):.0%}", _AMBER)
        _metric_card(kpi_cols[4], "IGNORANCE", f"{er.get('ignorance_level', 0):.2f}", _RED)

        # --- Row 3: Two columns — Radar chart + Algorithm bars ---
        if go is not None:
            r3c1, r3c2 = st.columns(2)

            # --- Chart 1: Domain Intelligence Profile (Radar / Scatterpolar) ---
            with r3c1:
                safe_scores = scores if isinstance(scores, dict) else {}
                domain_names = list(safe_scores.keys()) if safe_scores else []
                domain_vals = [float(safe_scores.get(k, 0)) for k in domain_names]
                if domain_names:
                    # Close the polygon by repeating the first point
                    radar_names = domain_names + [domain_names[0]]
                    radar_vals = domain_vals + [domain_vals[0]]
                    ideal_vals = [100] * len(radar_names)

                    fig_radar = go.Figure()
                    # Ideal reference ring
                    fig_radar.add_trace(go.Scatterpolar(
                        r=ideal_vals,
                        theta=radar_names,
                        fill="toself",
                        fillcolor=_hex_rgba(_DIM, 0.06),
                        line=dict(color=_hex_rgba(_DIM, 0.27), width=1, dash="dash"),
                        name="Ideal (100)",
                        hoverinfo="skip",
                    ))
                    # Actual domain scores
                    fig_radar.add_trace(go.Scatterpolar(
                        r=radar_vals,
                        theta=radar_names,
                        fill="toself",
                        fillcolor=_hex_rgba(_GREEN, 0.19),
                        line=dict(color=_GREEN, width=2),
                        name="Actual",
                        hovertemplate="<b>%{theta}</b>: %{r:.1f}<extra></extra>",
                    ))
                    fig_radar.update_layout(
                        height=370,
                        paper_bgcolor=_BG,
                        plot_bgcolor=_BG,
                        margin=dict(l=40, r=40, t=45, b=30),
                        title=dict(
                            text="DOMAIN INTELLIGENCE PROFILE",
                            font=dict(color=_CYAN, size=11,
                                      family="JetBrains Mono, monospace"),
                        ),
                        polar=dict(
                            bgcolor=_BG,
                            radialaxis=dict(
                                visible=True, range=[0, 100],
                                gridcolor=_hex_rgba(_DIM, 0.13),
                                tickfont=dict(size=8, color=_DIM),
                            ),
                            angularaxis=dict(
                                gridcolor=_hex_rgba(_DIM, 0.13),
                                tickfont=dict(size=8, color=_TEXT),
                            ),
                        ),
                        showlegend=False,
                        font=dict(color=_TEXT),
                    )
                    st.plotly_chart(fig_radar, use_container_width=True,
                                    key="fic_omniscient_radar")
                else:
                    st.caption("No domain scores available for radar chart.")

            # --- Chart 2: Horizontal bar — Algorithm Component Scores ---
            with r3c2:
                if component_scores:
                    sorted_comps = sorted(component_scores.items(),
                                          key=lambda x: float(x[1]), reverse=True)
                    comp_names = [c[0] for c in sorted_comps]
                    comp_vals = [float(c[1]) for c in sorted_comps]

                    # Color gradient: red (low) -> amber (mid) -> green (high)
                    bar_colors = []
                    for v in comp_vals:
                        if v >= 70:
                            bar_colors.append(_GREEN)
                        elif v >= 40:
                            bar_colors.append(_AMBER)
                        else:
                            bar_colors.append(_RED)

                    # Phase 3B: hover tooltips with breakdown detail
                    bar_customdata = []
                    for cn, cv in sorted_comps:
                        grade_val = "A" if cv >= 80 else "B" if cv >= 60 else "C" if cv >= 40 else "D"
                        bar_customdata.append([cn, cv, grade_val])

                    fig_bars = go.Figure(go.Bar(
                        x=comp_vals,
                        y=comp_names,
                        orientation="h",
                        marker=dict(color=bar_colors, line=dict(width=0)),
                        text=[f"{v:.0f}" for v in comp_vals],
                        textposition="auto",
                        textfont=dict(color=_TEXT, size=9,
                                      family="JetBrains Mono, monospace"),
                        customdata=bar_customdata,
                        hovertemplate=(
                            "<b>%{customdata[0]}</b><br>"
                            "Score: %{customdata[1]:.1f}/100<br>"
                            "Grade: %{customdata[2]}<extra></extra>"
                        ),
                    ))
                    # Phase 3B: vertical threshold line at x=75 (target score)
                    fig_bars.add_vline(
                        x=75, line_width=1, line_dash="dash",
                        line_color=_AMBER, opacity=0.6,
                        annotation_text="TARGET", annotation_position="top",
                        annotation=dict(font=dict(size=8, color=_AMBER)),
                    )
                    fig_bars.update_layout(
                        height=370,
                        paper_bgcolor=_BG,
                        plot_bgcolor=_BG,
                        margin=dict(l=10, r=10, t=45, b=30),
                        title=dict(
                            text="ALGORITHM COMPONENT SCORES",
                            font=dict(color=_CYAN, size=11,
                                      family="JetBrains Mono, monospace"),
                        ),
                        font=dict(color=_TEXT),
                    )
                    fig_bars.update_xaxes(
                        range=[0, 100], gridcolor=_hex_rgba(_DIM, 0.13),
                        tickfont=dict(size=8, color=_DIM),
                    )
                    fig_bars.update_yaxes(
                        tickfont=dict(size=8, color=_TEXT),
                        autorange="reversed",
                    )
                    st.plotly_chart(fig_bars, use_container_width=True,
                                    key="fic_omniscient_bars")
                else:
                    st.caption("No component scores available.")

        # --- Row 4: Convergence heatmap (full width, existing) ---
        if component_scores and go is not None:
            names = list(component_scores.keys())
            vals = list(component_scores.values())
            conv_labels = [convergence.get(n, "unknown") for n in names]
            conv_colors = {"converges": 0.9, "moderate": 0.5,
                           "diverges": 0.1, "unknown": 0.3}
            z_vals = [[conv_colors.get(cl, 0.3) for cl in conv_labels]]

            fig_conv = go.Figure(go.Heatmap(
                z=z_vals,
                x=names,
                y=["Convergence"],
                text=[[f"{v:.0f}" for v in vals]],
                texttemplate="%{text}",
                colorscale=[[0, _RED], [0.5, _AMBER], [1, _GREEN]],
                showscale=False,
                hovertemplate="<b>%{x}</b><br>Score: %{text}<br>"
                    "Status: %{z:.1f}<extra></extra>",
            ))
            fig_conv.update_layout(
                height=120,
                paper_bgcolor=_BG, plot_bgcolor=_BG,
                margin=dict(l=10, r=10, t=30, b=10),
                title=dict(
                    text="ALGORITHM CONVERGENCE",
                    font=dict(color=_CYAN, size=11,
                              family="JetBrains Mono, monospace"),
                ),
            )
            fig_conv.update_xaxes(color=_DIM, tickfont=dict(size=8))
            fig_conv.update_yaxes(color=_DIM, tickfont=dict(size=8))
            st.plotly_chart(fig_conv, use_container_width=True,
                            key="fic_omniscient_convergence")

        # --- Row 5: Two columns — Dependency heatmap + Evidence gauge ---
        if go is not None:
            corr_matrix = copula_data.get("correlation_matrix") if isinstance(
                copula_data, dict) else None
            conflict_level = (enhanced_ds.get("conflict_level", 0)
                              if isinstance(enhanced_ds, dict) else 0)
            has_deps = (corr_matrix is not None
                        and isinstance(corr_matrix, (list, dict))
                        and len(corr_matrix) > 0)
            has_gauge = isinstance(conflict_level, (int, float))

            if has_deps or has_gauge:
                r5c1, r5c2 = st.columns(2)

                # --- Chart 3: Inter-Domain Dependency Matrix (Phase 3C: enhanced) ---
                with r5c1:
                    if has_deps:
                        try:
                            # corr_matrix may be a dict of dicts or list of lists
                            if isinstance(corr_matrix, dict):
                                dep_labels = list(corr_matrix.keys())
                                z_dep = []
                                for row_key in dep_labels:
                                    row_data = corr_matrix[row_key]
                                    if isinstance(row_data, dict):
                                        z_dep.append([float(row_data.get(c, 0))
                                                      for c in dep_labels])
                                    else:
                                        z_dep.append([float(v) for v in row_data])
                            elif isinstance(corr_matrix, list):
                                z_dep = [[float(v) for v in row]
                                         for row in corr_matrix]
                                safe_sc = scores if isinstance(scores, dict) else {}
                                dep_labels = (list(safe_sc.keys())[:len(z_dep)]
                                              if safe_sc
                                              else [f"D{i}" for i in
                                                    range(len(z_dep))])
                            else:
                                z_dep = []
                                dep_labels = []

                            if z_dep and dep_labels:
                                # Phase 3C: toggle Matrix/Network view
                                dep_view = st.radio(
                                    "View", ["Matrix", "Network"],
                                    horizontal=True,
                                    key="fic_omniscient_dep_view",
                                )

                                if dep_view == "Matrix":
                                    # Phase 3C: text values on cells
                                    text_vals = [[f"{v:.2f}" for v in row] for row in z_dep]
                                    fig_dep = go.Figure(go.Heatmap(
                                        z=z_dep,
                                        x=dep_labels,
                                        y=dep_labels,
                                        text=text_vals,
                                        texttemplate="%{text}",
                                        textfont=dict(size=7, color=_TEXT),
                                        colorscale=[
                                            [0, "#3366ff"],
                                            [0.5, "#ffffff"],
                                            [1, _RED],
                                        ],
                                        zmin=-1, zmax=1,
                                        showscale=True,
                                        colorbar=dict(
                                            tickfont=dict(size=8, color=_DIM),
                                            len=0.8,
                                        ),
                                        hovertemplate=("<b>%{x}</b> vs <b>%{y}</b>"
                                            "<br>Corr: %{z:.2f}<extra></extra>"),
                                    ))
                                    fig_dep.update_layout(
                                        height=370,
                                        paper_bgcolor=_BG,
                                        plot_bgcolor=_BG,
                                        margin=dict(l=10, r=10, t=45, b=10),
                                        title=dict(
                                            text="INTER-DOMAIN DEPENDENCY MATRIX",
                                            font=dict(color=_CYAN, size=11,
                                                      family="JetBrains Mono, monospace"),
                                        ),
                                        font=dict(color=_TEXT),
                                    )
                                    fig_dep.update_xaxes(
                                        tickfont=dict(size=8, color=_TEXT),
                                        tickangle=45,
                                    )
                                    fig_dep.update_yaxes(
                                        tickfont=dict(size=8, color=_TEXT),
                                    )
                                    st.plotly_chart(fig_dep, use_container_width=True,
                                                    key="fic_omniscient_deps")
                                else:
                                    # Phase 3C: Network graph view
                                    fig_net = go.Figure()
                                    n = len(dep_labels)
                                    # Position nodes in a circle
                                    node_x = [math.cos(2 * math.pi * i / n) for i in range(n)]
                                    node_y = [math.sin(2 * math.pi * i / n) for i in range(n)]
                                    # Draw edges (correlation arcs)
                                    for i in range(n):
                                        for j in range(i + 1, n):
                                            corr_val = z_dep[i][j] if j < len(z_dep[i]) else 0
                                            if abs(corr_val) < 0.1:
                                                continue
                                            edge_color = _GREEN if corr_val > 0 else _RED
                                            fig_net.add_trace(go.Scatter(
                                                x=[node_x[i], node_x[j]],
                                                y=[node_y[i], node_y[j]],
                                                mode="lines",
                                                line=dict(
                                                    width=max(0.5, abs(corr_val) * 4),
                                                    color=edge_color,
                                                ),
                                                opacity=min(1.0, abs(corr_val) + 0.2),
                                                showlegend=False,
                                                hoverinfo="skip",
                                            ))
                                    # Draw nodes
                                    fig_net.add_trace(go.Scatter(
                                        x=node_x, y=node_y,
                                        mode="markers+text",
                                        marker=dict(size=20, color=_CYAN,
                                                    line=dict(width=1, color=_TEXT)),
                                        text=dep_labels,
                                        textposition="top center",
                                        textfont=dict(size=8, color=_TEXT),
                                        showlegend=False,
                                        hovertemplate="<b>%{text}</b><extra></extra>",
                                    ))
                                    fig_net.update_layout(
                                        height=370,
                                        paper_bgcolor=_BG,
                                        plot_bgcolor=_BG,
                                        margin=dict(l=10, r=10, t=45, b=10),
                                        title=dict(
                                            text="DEPENDENCY NETWORK",
                                            font=dict(color=_CYAN, size=11,
                                                      family="JetBrains Mono, monospace"),
                                        ),
                                        xaxis=dict(showgrid=False, zeroline=False,
                                                   showticklabels=False),
                                        yaxis=dict(showgrid=False, zeroline=False,
                                                   showticklabels=False),
                                        font=dict(color=_TEXT),
                                    )
                                    st.plotly_chart(fig_net, use_container_width=True,
                                                    key="fic_omniscient_network")

                                # Phase 3C: strongest/weakest dependency callout
                                strongest_val = -2.0
                                weakest_val = 2.0
                                strongest_pair = ("", "")
                                weakest_pair = ("", "")
                                for i in range(len(dep_labels)):
                                    for j in range(i + 1, len(dep_labels)):
                                        v = z_dep[i][j] if j < len(z_dep[i]) else 0
                                        if v > strongest_val:
                                            strongest_val = v
                                            strongest_pair = (dep_labels[i], dep_labels[j])
                                        if v < weakest_val:
                                            weakest_val = v
                                            weakest_pair = (dep_labels[i], dep_labels[j])
                                if strongest_pair[0]:
                                    st.markdown(
                                        f'<div style="font-size:0.65rem;margin-top:6px;">'
                                        f'<span style="color:{_GREEN};font-weight:700;">'
                                        f'STRONGEST:</span> '
                                        f'<span style="color:{_TEXT};">'
                                        f'{html_module.escape(strongest_pair[0])} &harr; '
                                        f'{html_module.escape(strongest_pair[1])} '
                                        f'({strongest_val:.2f})</span>'
                                        f'&nbsp;&nbsp;'
                                        f'<span style="color:{_RED};font-weight:700;">'
                                        f'WEAKEST:</span> '
                                        f'<span style="color:{_TEXT};">'
                                        f'{html_module.escape(weakest_pair[0])} &harr; '
                                        f'{html_module.escape(weakest_pair[1])} '
                                        f'({weakest_val:.2f})</span></div>',
                                        unsafe_allow_html=True,
                                    )
                            else:
                                st.caption("Dependency matrix data is empty.")
                        except Exception:
                            st.caption("Could not render dependency matrix.")
                    else:
                        st.caption("No copula correlation data available.")

                # --- Chart 4: Evidence Conflict Level Gauge ---
                with r5c2:
                    if has_gauge:
                        conflict_val = float(conflict_level)
                        # Clamp to [0, 1]
                        conflict_val = max(0.0, min(1.0, conflict_val))

                        fig_gauge = go.Figure(go.Indicator(
                            mode="gauge+number",
                            value=conflict_val,
                            number=dict(
                                font=dict(color=_TEXT, size=36,
                                          family="JetBrains Mono, monospace"),
                                valueformat=".3f",
                            ),
                            gauge=dict(
                                axis=dict(
                                    range=[0, 1],
                                    tickfont=dict(size=9, color=_DIM),
                                    tickcolor=_DIM,
                                ),
                                bar=dict(color=_CYAN, thickness=0.3),
                                bgcolor=_BG,
                                borderwidth=0,
                                steps=[
                                    dict(range=[0, 0.3], color=_hex_rgba(_GREEN, 0.2)),
                                    dict(range=[0.3, 0.6], color=_hex_rgba(_AMBER, 0.2)),
                                    dict(range=[0.6, 1.0], color=_hex_rgba(_RED, 0.2)),
                                ],
                                threshold=dict(
                                    line=dict(color=_RED, width=2),
                                    thickness=0.75,
                                    value=conflict_val,
                                ),
                            ),
                            title=dict(
                                text="EVIDENCE CONFLICT LEVEL",
                                font=dict(color=_CYAN, size=11,
                                          family="JetBrains Mono, monospace"),
                            ),
                        ))
                        fig_gauge.update_layout(
                            height=370,
                            paper_bgcolor=_BG,
                            plot_bgcolor=_BG,
                            margin=dict(l=30, r=30, t=60, b=10),
                            font=dict(color=_TEXT),
                        )
                        st.plotly_chart(fig_gauge, use_container_width=True,
                                        key="fic_omniscient_gauge")
                    else:
                        st.caption("No conflict level data available.")

        # --- Row 6: Key insights in 2 columns ---
        if insights:
            st.markdown(
                f'<div style="font-family:JetBrains Mono,monospace;font-size:0.7rem;'
                f'color:{_GREEN};font-weight:700;letter-spacing:1px;margin:12px 0 6px 0;">'
                f'KEY INSIGHTS</div>',
                unsafe_allow_html=True,
            )
            safe_insights = insights[:6]
            mid = (len(safe_insights) + 1) // 2
            left_insights = safe_insights[:mid]
            right_insights = safe_insights[mid:]
            ins_c1, ins_c2 = st.columns(2)
            with ins_c1:
                for i, insight in enumerate(left_insights):
                    st.markdown(
                        f'<div style="border-left:2px solid {_GREEN}44;padding:6px 12px;'
                        f'margin:4px 0;font-size:0.72rem;color:{_TEXT};'
                        f'background:{_GREEN}05;border-radius:0 4px 4px 0;">'
                        f'<span style="color:{_GREEN};font-weight:700;">[{i+1}]</span> '
                        f'{html_module.escape(str(insight))}</div>',
                        unsafe_allow_html=True,
                    )
            with ins_c2:
                for j, insight in enumerate(right_insights):
                    st.markdown(
                        f'<div style="border-left:2px solid {_GREEN}44;padding:6px 12px;'
                        f'margin:4px 0;font-size:0.72rem;color:{_TEXT};'
                        f'background:{_GREEN}05;border-radius:0 4px 4px 0;">'
                        f'<span style="color:{_GREEN};font-weight:700;">[{mid+j+1}]</span> '
                        f'{html_module.escape(str(insight))}</div>',
                        unsafe_allow_html=True,
                    )

        # --- Row 7: Narrative ---
        if narrative:
            st.markdown(
                f'<div style="border:1px solid {_GREEN}22;border-radius:8px;padding:14px;'
                f'margin:12px 0;background:{_GREEN}05;font-family:JetBrains Mono,monospace;'
                f'font-size:0.72rem;color:{_TEXT};line-height:1.65;white-space:pre-line;">'
                f'{html_module.escape(str(narrative))}</div>',
                unsafe_allow_html=True,
            )

    except Exception as exc:
        logger.warning("Omniscient section render failed: %s", exc)
        st.warning("Omniscient synthesis rendering error.")
