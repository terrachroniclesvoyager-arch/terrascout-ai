"""
Intelligence Dossier - Comprehensive Location Intelligence Report
TerraScout AI - Unified Intelligence Platform

Generates a full Palantir-style classified intelligence dossier
combining all data sources, fusion algorithms, Monte Carlo simulation,
threat assessment, correlation intelligence, and strategic synthesis
into a single narrative document.
"""

import html as html_module
import logging
from datetime import datetime

import streamlit as st

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


def _hex_rgba(hc, a=1.0):
    """Convert #RRGGBB + alpha float to rgba() for Plotly compatibility."""
    h = hc.lstrip("#")
    return f"rgba({int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)},{a})"

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

_DOMAIN_DISPLAY_NAMES = {
    "habitability": "Habitability",
    "agriculture": "Agriculture Potential",
    "ecology": "Ecological Value",
    "hazard_safety": "Hazard Safety",
    "water_resources": "Water Resources",
    "infrastructure": "Infrastructure",
    "climate_comfort": "Climate Comfort",
    "economic_potential": "Economic Potential",
    "air_environment": "Air & Environment",
    "geological_stability": "Geological Stability",
}

_THREAT_COLORS = {
    "CRITICAL": OPS_RED,
    "HIGH": "#ff6600",
    "ELEVATED": OPS_AMBER,
    "MODERATE": "#dddd00",
    "LOW": OPS_GREEN,
}


# ═══════════════════════════════════════════════════════════════════════════
# HELPER: Styled section container
# ═══════════════════════════════════════════════════════════════════════════

def _section_header(num, title, color=OPS_CYAN):
    """Render a styled section header."""
    st.markdown(f'''
    <div style="color: {color}; font-size: 0.7rem; letter-spacing: 3px; font-weight: 700;
        margin-bottom: 0.75rem; border-bottom: 1px solid #1a2035; padding-bottom: 0.5rem;">
        SECTION {num} &mdash; {title}</div>
    ''', unsafe_allow_html=True)


def _section_open():
    """Open a styled panel div."""
    st.markdown(f'''
    <div style="background: {OPS_PANEL}; border: 1px solid #1a2035; border-radius: 8px;
        padding: 1.5rem; margin: 1.5rem 0;">
    ''', unsafe_allow_html=True)


def _section_close():
    """Close the styled panel div."""
    st.markdown('</div>', unsafe_allow_html=True)


def _score_color(score):
    """Return color based on score threshold."""
    if score >= 70:
        return OPS_GREEN
    if score >= 40:
        return OPS_AMBER
    return OPS_RED


def _safe_get(d, *keys, default=None):
    """Safely traverse nested dicts."""
    val = d
    for k in keys:
        if not isinstance(val, dict):
            return default
        val = val.get(k, default)
    return val


def _pct_bar(value, max_val=100, color=OPS_CYAN, height="6px"):
    """Return HTML for a thin percentage bar."""
    pct = min(100, max(0, (value / max(max_val, 0.01)) * 100))
    return (
        f'<div style="background: #1a2035; border-radius: 3px; height: {height}; '
        f'width: 100%; margin: 4px 0;">'
        f'<div style="background: {color}; height: 100%; border-radius: 3px; '
        f'width: {pct:.1f}%;"></div></div>'
    )


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def render_intelligence_dossier():
    """Main entry point -- renders the complete intelligence dossier page."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # --- Page background ---
    st.markdown(f'''
    <style>
        .stApp {{ background-color: {OPS_BG}; }}
        .stMarkdown p {{ color: {OPS_TEXT}; }}
    </style>
    ''', unsafe_allow_html=True)

    # --- HEADER ---
    st.markdown(f'''
    <div style="background: linear-gradient(135deg, #0a0a18 0%, #1a0a2e 50%, #0a0a18 100%);
        border: 2px solid {OPS_PURPLE}; border-radius: 12px; padding: 2rem; text-align: center;
        margin-bottom: 2rem;">
        <div style="color: {OPS_PURPLE}; font-size: 0.75rem; letter-spacing: 4px;
            margin-bottom: 0.5rem;">
            CLASSIFIED &mdash; INTELLIGENCE ASSESSMENT</div>
        <h1 style="color: {OPS_TEXT}; font-size: 2.2rem; margin: 0;">
            LOCATION INTELLIGENCE DOSSIER</h1>
        <p style="color: {OPS_TEXT_DIM}; margin-top: 0.5rem;">
            Comprehensive Multi-Source Analysis Report &bull; Generated {timestamp}</p>
    </div>
    ''', unsafe_allow_html=True)

    # --- LOCATION INPUT ---
    try:
        from src.location_context import (
            init_location_context, get_location, has_location,
            get_short_name, render_location_selector,
        )
        from src.data_hub import get_hub_data
    except ImportError as exc:
        st.error(f"Core modules unavailable: {exc}")
        return

    init_location_context()
    render_location_selector("dossier")

    if not has_location():
        st.markdown(f'''
        <div style="text-align: center; padding: 4rem 2rem; color: {OPS_TEXT_DIM};">
            <div style="font-size: 3rem; margin-bottom: 1rem;">&#128205;</div>
            <div style="font-size: 1.1rem;">Select a location to generate the intelligence dossier.</div>
            <div style="font-size: 0.85rem; margin-top: 0.5rem;">
                Use the search bar, enter coordinates, or choose a preset above.</div>
        </div>
        ''', unsafe_allow_html=True)
        return

    loc = get_location()
    lat, lon = loc["lat"], loc["lon"]
    location_name = get_short_name() or f"{lat:.4f}, {lon:.4f}"

    # --- FETCH HUB DATA ---
    with st.spinner("Collecting intelligence data..."):
        hub = get_hub_data(lat, lon)

    scores = hub.get("scores", {})
    details = hub.get("details", {})
    raw_data = hub.get("raw_data", {})
    _conf_raw = hub.get("confidence", 0.5)
    confidence = float(_conf_raw.get("overall", 0.5)) if isinstance(_conf_raw, dict) else float(_conf_raw or 0)

    # --- IMPORT ADVANCED MODULES (lazy, all optional) ---
    analytics = {}
    ds_fusion = {}
    cascade = {}
    cvi = {}
    bbn = {}
    pca = {}
    threats = {}
    mc_result = {}
    sensitivity = []
    correlation = []
    geopolitical = {}
    strategic = {}

    # compute_advanced_analytics
    try:
        from src.unified_intelligence import compute_advanced_analytics
        analytics = compute_advanced_analytics(scores, details, raw_data) or {}
    except Exception as exc:
        logger.warning("Advanced analytics unavailable: %s", exc)

    # Dempster-Shafer fusion
    try:
        from src.fusion_engine import dempster_shafer_fusion
        ds_fusion = dempster_shafer_fusion(scores) or {}
    except Exception as exc:
        logger.warning("DS fusion unavailable: %s", exc)

    # Risk propagation cascade
    try:
        from src.fusion_engine import risk_propagation_cascade
        cascade = risk_propagation_cascade(scores) or {}
    except Exception as exc:
        logger.warning("Risk cascade unavailable: %s", exc)

    # Composite vulnerability index
    try:
        from src.fusion_engine import composite_vulnerability_index
        cvi = composite_vulnerability_index(scores, details, analytics) or {}
    except Exception as exc:
        logger.warning("CVI unavailable: %s", exc)

    # Bayesian Belief Network
    try:
        from src.advanced_fusion_algorithms import bayesian_belief_network
        bbn = bayesian_belief_network(scores, details, analytics) or {}
    except Exception as exc:
        logger.warning("BBN unavailable: %s", exc)

    # PCA domain analysis
    try:
        from src.advanced_fusion_algorithms import pca_domain_analysis
        pca = pca_domain_analysis(scores, analytics) or {}
    except Exception as exc:
        logger.warning("PCA unavailable: %s", exc)

    # Threat assessment
    try:
        from src.threat_radar import compute_threat_assessment
        threats = compute_threat_assessment(raw_data, details, scores) or {}
    except Exception as exc:
        logger.warning("Threat assessment unavailable: %s", exc)

    # Monte Carlo simulation
    try:
        from src.monte_carlo_engine import monte_carlo_risk_simulation, sensitivity_analysis
        mc_result = monte_carlo_risk_simulation(scores, confidence) or {}
        sensitivity = sensitivity_analysis(scores, confidence) or []
    except Exception as exc:
        logger.warning("Monte Carlo unavailable: %s", exc)

    # Correlation intelligence (from unified_intelligence cross-correlations)
    correlation = hub.get("insights", [])

    # Geopolitical profile
    try:
        from src.geopolitical_engine import fetch_complete_geopolitical_profile
        geopolitical = fetch_complete_geopolitical_profile(lat, lon) or {}
    except Exception as exc:
        logger.warning("Geopolitical engine unavailable: %s", exc)

    # Strategic assessment
    try:
        from src.strategic_synthesis import compute_strategic_assessment
        cvi_val = cvi.get("cvi", 0.5) if isinstance(cvi, dict) else 0.5
        strategic = compute_strategic_assessment(
            scores, details, analytics, ds_fusion, cascade, cvi_val,
            [], {}, {}, bbn, raw_data,
        ) or {}
    except Exception as exc:
        logger.warning("Strategic assessment unavailable: %s", exc)

    # --- DOSSIER HEADER BADGE ---
    st.markdown(f'''
    <div style="background: {OPS_PANEL}; border: 1px solid #1a2035; border-radius: 8px;
        padding: 1rem 1.5rem; margin-bottom: 1.5rem; display: flex;
        justify-content: space-between; align-items: center; flex-wrap: wrap;">
        <div>
            <span style="color: {OPS_TEXT_DIM}; font-size: 0.7rem; letter-spacing: 2px;">
                SUBJECT LOCATION</span><br>
            <span style="color: {OPS_TEXT}; font-size: 1.2rem; font-weight: 700;">
                {html_module.escape(location_name)}</span>
        </div>
        <div style="text-align: right;">
            <span style="color: {OPS_TEXT_DIM}; font-size: 0.7rem; letter-spacing: 2px;">
                COORDINATES</span><br>
            <span style="color: {OPS_CYAN}; font-family: monospace; font-size: 1rem;">
                {lat:.5f}N, {lon:.5f}E</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # --- RENDER ALL SECTIONS ---
    _render_executive_summary(hub, threats, strategic, location_name)
    _render_geopolitical_context(geopolitical)
    _render_domain_analysis(scores)
    _render_threat_assessment(threats)
    _render_risk_simulation(mc_result, sensitivity, confidence)
    _render_correlation_intelligence(correlation, hub)
    _render_strategic_assessment(strategic)
    _render_data_confidence(confidence, raw_data)
    _render_classification_footer(lat, lon, timestamp)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

def _render_executive_summary(hub, threats, strategic, location_name):
    """Render the executive summary section."""
    _section_open()
    _section_header(1, "EXECUTIVE SUMMARY", OPS_CYAN)

    overall_score = hub.get("overall_score", 0)
    overall_label = hub.get("overall_label", "Unknown")
    overall_color = hub.get("overall_color", OPS_TEXT_DIM)
    threat_level = threats.get("threat_level", "UNKNOWN") if threats else "N/A"
    threat_color = _THREAT_COLORS.get(threat_level, OPS_TEXT_DIM)
    strat_grade = strategic.get("strategic_grade", "N/A") if strategic else "N/A"
    strat_score = strategic.get("strategic_score", 0) if strategic else 0

    # Key metrics row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f'''
        <div style="text-align: center; padding: 1rem;">
            <div style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px;
                margin-bottom: 0.3rem;">OVERALL SCORE</div>
            <div style="color: {overall_color}; font-size: 2.5rem; font-weight: 800;
                line-height: 1;">{overall_score:.1f}</div>
            <div style="color: {overall_color}; font-size: 0.8rem; margin-top: 0.2rem;">
                {overall_label}</div>
            {_pct_bar(overall_score, 100, overall_color)}
        </div>
        ''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''
        <div style="text-align: center; padding: 1rem;">
            <div style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px;
                margin-bottom: 0.3rem;">THREAT LEVEL</div>
            <div style="color: {threat_color}; font-size: 2rem; font-weight: 800;
                line-height: 1;">{threat_level}</div>
            <div style="color: {OPS_TEXT_DIM}; font-size: 0.8rem; margin-top: 0.2rem;">
                Score: {threats.get("threat_score", 0):.0f}/100</div>
        </div>
        ''', unsafe_allow_html=True)
    with c3:
        grade_color = OPS_GREEN if strat_score >= 70 else (OPS_AMBER if strat_score >= 40 else OPS_RED)
        st.markdown(f'''
        <div style="text-align: center; padding: 1rem;">
            <div style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px;
                margin-bottom: 0.3rem;">STRATEGIC GRADE</div>
            <div style="color: {grade_color}; font-size: 2.5rem; font-weight: 800;
                line-height: 1;">{strat_grade}</div>
            <div style="color: {OPS_TEXT_DIM}; font-size: 0.8rem; margin-top: 0.2rem;">
                Score: {strat_score:.1f}/100</div>
        </div>
        ''', unsafe_allow_html=True)

    # Executive narrative
    scores = hub.get("scores", {})
    strengths = [d for d, s in scores.items() if isinstance(s, (int, float)) and s >= 65]
    weaknesses = [d for d, s in scores.items() if isinstance(s, (int, float)) and s < 40]

    strength_text = ", ".join(_DOMAIN_DISPLAY_NAMES.get(d, d) for d in strengths[:3]) if strengths else "none identified"
    weakness_text = ", ".join(_DOMAIN_DISPLAY_NAMES.get(d, d) for d in weaknesses[:3]) if weaknesses else "none identified"

    narrative_paras = []
    narrative_paras.append(
        f"This intelligence dossier presents a comprehensive multi-source analysis of "
        f"<strong>{html_module.escape(location_name)}</strong>. The location has been assessed across 10 analytical "
        f"domains using {len([k for k in hub.get('raw_data', {}) if hub['raw_data'].get(k)])} "
        f"verified data sources, yielding an overall viability score of "
        f"<strong>{overall_score:.1f}</strong> ({overall_label})."
    )
    narrative_paras.append(
        f"Primary domain strengths include {strength_text}, while areas requiring attention "
        f"are {weakness_text}. The current threat assessment stands at "
        f"<strong>{threat_level}</strong>, and the strategic grade is "
        f"<strong>{strat_grade}</strong> ({strat_score:.1f}/100)."
    )

    # Add strategic narrative if available
    strat_narrative = strategic.get("narrative", []) if isinstance(strategic, dict) else []
    if strat_narrative and isinstance(strat_narrative, list) and len(strat_narrative) > 0:
        narrative_paras.append(str(strat_narrative[0]))

    for para in narrative_paras:
        st.markdown(
            f'<p style="color: {OPS_TEXT}; font-size: 0.9rem; line-height: 1.7; '
            f'margin-bottom: 0.8rem;">{para}</p>',
            unsafe_allow_html=True,
        )

    _section_close()


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: GEOPOLITICAL CONTEXT
# ═══════════════════════════════════════════════════════════════════════════

_COUNTRY_FLAG_FALLBACK = {
    "US": "🇺🇸", "GB": "🇬🇧", "IT": "🇮🇹", "DE": "🇩🇪", "FR": "🇫🇷",
    "ES": "🇪🇸", "JP": "🇯🇵", "CN": "🇨🇳", "IN": "🇮🇳", "BR": "🇧🇷",
    "AU": "🇦🇺", "CA": "🇨🇦", "RU": "🇷🇺", "ZA": "🇿🇦", "MX": "🇲🇽",
}


def _country_flag(code):
    """Generate flag emoji from ISO 3166-1 alpha-2 code."""
    if not code or len(code) != 2:
        return ""
    try:
        return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())
    except Exception:
        return _COUNTRY_FLAG_FALLBACK.get(code.upper(), "")


def _render_geopolitical_context(geopolitical):
    """Render the geopolitical context section."""
    _section_open()
    _section_header(2, "GEOPOLITICAL CONTEXT", OPS_PURPLE)

    if not geopolitical or not geopolitical.get("country"):
        st.markdown(
            f'<p style="color: {OPS_TEXT_DIM}; font-style: italic;">'
            f'Geopolitical data not available for this location.</p>',
            unsafe_allow_html=True,
        )
        _section_close()
        return

    country = geopolitical.get("country", {})
    indicators = geopolitical.get("indicators", {})
    geo_score = geopolitical.get("geopolitical_score", 0)
    geo_grade = geopolitical.get("geopolitical_grade", "N/A")
    geo_factors = geopolitical.get("geopolitical_factors", [])

    country_name = country.get("country_name", "Unknown")
    country_code = country.get("country_code", "")
    flag = _country_flag(country_code)
    region = country.get("region", "N/A")
    subregion = country.get("subregion", "N/A")
    capital = country.get("capital", "N/A")
    population = country.get("population", 0)

    # Country overview
    pop_str = f"{population:,.0f}" if population else "N/A"
    st.markdown(f'''
    <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1.2rem;">
        <span style="font-size: 2.5rem;">{flag}</span>
        <div>
            <div style="color: {OPS_TEXT}; font-size: 1.3rem; font-weight: 700;">
                {html_module.escape(country_name)}</div>
            <div style="color: {OPS_TEXT_DIM}; font-size: 0.8rem;">
                {html_module.escape(region)} &bull; {html_module.escape(subregion)} &bull; Capital: {html_module.escape(capital)} &bull;
                Pop: {pop_str}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Key indicators
    gdp = indicators.get("gdp_per_capita_usd")
    life_exp = indicators.get("life_expectancy")
    literacy = indicators.get("adult_literacy_pct")
    electricity = indicators.get("electricity_access_pct")

    ic1, ic2, ic3, ic4 = st.columns(4)
    _indicator_items = [
        (ic1, "GDP/CAPITA", f"${gdp:,.0f}" if gdp else "N/A", OPS_GREEN),
        (ic2, "LIFE EXPECTANCY", f"{life_exp:.1f} yr" if life_exp else "N/A", OPS_CYAN),
        (ic3, "LITERACY", f"{literacy:.1f}%" if literacy else "N/A", OPS_BLUE),
        (ic4, "ELECTRICITY", f"{electricity:.1f}%" if electricity else "N/A", OPS_AMBER),
    ]
    for col, label, value, color in _indicator_items:
        with col:
            st.markdown(f'''
            <div style="text-align: center; padding: 0.5rem;">
                <div style="color: {OPS_TEXT_DIM}; font-size: 0.6rem; letter-spacing: 2px;">
                    {label}</div>
                <div style="color: {color}; font-size: 1.3rem; font-weight: 700;">
                    {value}</div>
            </div>
            ''', unsafe_allow_html=True)

    # Geopolitical risk score
    geo_color = _score_color(geo_score)
    st.markdown(f'''
    <div style="margin-top: 1rem; padding: 0.8rem; background: #0d1225; border-radius: 6px;
        display: flex; justify-content: space-between; align-items: center;">
        <div>
            <span style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px;">
                GEOPOLITICAL STABILITY SCORE</span>
            <span style="color: {geo_color}; font-size: 1.4rem; font-weight: 800;
                margin-left: 1rem;">{geo_score:.1f}/100</span>
            <span style="color: {geo_color}; font-size: 0.85rem; margin-left: 0.5rem;">
                ({geo_grade})</span>
        </div>
        <div style="width: 200px;">{_pct_bar(geo_score, 100, geo_color)}</div>
    </div>
    ''', unsafe_allow_html=True)

    # Top factors
    if geo_factors:
        top_factors = geo_factors[:3] if isinstance(geo_factors, list) else []
        if top_factors:
            st.markdown(
                f'<div style="margin-top: 0.8rem; color: {OPS_TEXT_DIM}; font-size: 0.65rem; '
                f'letter-spacing: 2px;">KEY GEOPOLITICAL FACTORS</div>',
                unsafe_allow_html=True,
            )
            for factor in top_factors:
                fname = factor.get("name", "Unknown") if isinstance(factor, dict) else str(factor)
                fimpact = factor.get("impact", 0) if isinstance(factor, dict) else 0
                fdetail = factor.get("detail", "") if isinstance(factor, dict) else ""
                impact_color = OPS_GREEN if fimpact > 0 else OPS_RED if fimpact < 0 else OPS_TEXT_DIM
                impact_sign = "+" if fimpact > 0 else ""
                st.markdown(f'''
                <div style="padding: 0.3rem 0; display: flex; align-items: center; gap: 0.8rem;">
                    <span style="color: {impact_color}; font-weight: 700; font-size: 0.85rem;
                        min-width: 45px;">{impact_sign}{fimpact:.1f}</span>
                    <span style="color: {OPS_TEXT}; font-size: 0.85rem;">{html_module.escape(fname)}</span>
                    <span style="color: {OPS_TEXT_DIM}; font-size: 0.75rem; font-style: italic;">
                        {html_module.escape(fdetail)}</span>
                </div>
                ''', unsafe_allow_html=True)

    _section_close()


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: DOMAIN ANALYSIS MATRIX
# ═══════════════════════════════════════════════════════════════════════════

def _render_domain_analysis(scores):
    """Render the 10-domain analysis matrix with bar chart."""
    _section_open()
    _section_header(3, "DOMAIN ANALYSIS MATRIX", OPS_BLUE)

    if not scores:
        st.markdown(
            f'<p style="color: {OPS_TEXT_DIM}; font-style: italic;">Domain scores not available.</p>',
            unsafe_allow_html=True,
        )
        _section_close()
        return

    # Sort domains by score descending
    sorted_domains = sorted(scores.items(), key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)
    domain_keys = [d for d, _ in sorted_domains]
    domain_labels = [_DOMAIN_DISPLAY_NAMES.get(d, d) for d in domain_keys]
    domain_values = [scores[d] for d in domain_keys]
    domain_colors = [_score_color(s) for s in domain_values]

    if HAS_PLOTLY:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=domain_labels,
            x=domain_values,
            orientation="h",
            marker_color=domain_colors,
            text=[f"{v:.1f}" for v in domain_values],
            textposition="auto",
            textfont=dict(color=OPS_TEXT, size=11),
            hovertemplate="%{y}: %{x:.1f}/100<extra></extra>",
        ))
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=OPS_TEXT,
            margin=dict(l=20, r=20, t=40, b=20),
            height=400,
            xaxis=dict(
                range=[0, 105],
                gridcolor="#1a2035",
                tickfont=dict(color=OPS_TEXT_DIM),
                title="Score (0-100)",
                title_font=dict(color=OPS_TEXT_DIM, size=10),
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(color=OPS_TEXT, size=11),
            ),
            title=dict(
                text="Domain Score Distribution",
                font=dict(color=OPS_TEXT_DIM, size=12),
            ),
        )
        st.plotly_chart(fig, use_container_width=True, key="dossier_domain_bars")
    else:
        # Fallback: HTML bars
        for label, value in zip(domain_labels, domain_values):
            color = _score_color(value)
            st.markdown(
                f'<div style="color: {OPS_TEXT}; font-size: 0.85rem;">'
                f'{label}: <strong style="color: {color};">{value:.1f}</strong></div>'
                f'{_pct_bar(value, 100, color)}',
                unsafe_allow_html=True,
            )

    # Strengths and weaknesses
    strengths = [(d, s) for d, s in scores.items() if isinstance(s, (int, float)) and s >= 65]
    weaknesses = [(d, s) for d, s in scores.items() if isinstance(s, (int, float)) and s < 40]

    sc1, sc2 = st.columns(2)
    with sc1:
        st.markdown(
            f'<div style="color: {OPS_GREEN}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin-bottom: 0.5rem;">STRENGTHS (Score &ge; 65)</div>',
            unsafe_allow_html=True,
        )
        if strengths:
            for d, s in sorted(strengths, key=lambda x: x[1], reverse=True):
                name = _DOMAIN_DISPLAY_NAMES.get(d, d)
                interpretation = _domain_interpretation(d, s, "strength")
                st.markdown(f'''
                <div style="padding: 0.3rem 0; border-bottom: 1px solid #111828;">
                    <span style="color: {OPS_GREEN}; font-weight: 700;">{s:.1f}</span>
                    <span style="color: {OPS_TEXT}; margin-left: 0.5rem;">{name}</span>
                    <div style="color: {OPS_TEXT_DIM}; font-size: 0.75rem; margin-left: 2.5rem;">
                        {interpretation}</div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<p style="color: {OPS_TEXT_DIM}; font-style: italic;">No strong domains identified.</p>',
                unsafe_allow_html=True,
            )

    with sc2:
        st.markdown(
            f'<div style="color: {OPS_RED}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin-bottom: 0.5rem;">WEAKNESSES (Score &lt; 40)</div>',
            unsafe_allow_html=True,
        )
        if weaknesses:
            for d, s in sorted(weaknesses, key=lambda x: x[1]):
                name = _DOMAIN_DISPLAY_NAMES.get(d, d)
                interpretation = _domain_interpretation(d, s, "weakness")
                st.markdown(f'''
                <div style="padding: 0.3rem 0; border-bottom: 1px solid #111828;">
                    <span style="color: {OPS_RED}; font-weight: 700;">{s:.1f}</span>
                    <span style="color: {OPS_TEXT}; margin-left: 0.5rem;">{name}</span>
                    <div style="color: {OPS_TEXT_DIM}; font-size: 0.75rem; margin-left: 2.5rem;">
                        {interpretation}</div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<p style="color: {OPS_TEXT_DIM}; font-style: italic;">No critical weaknesses identified.</p>',
                unsafe_allow_html=True,
            )

    _section_close()


def _domain_interpretation(domain, score, category):
    """Generate a brief 1-sentence interpretation for a domain score."""
    interpretations = {
        "habitability": {
            "strength": "The area demonstrates strong livability conditions with adequate population infrastructure.",
            "weakness": "Habitability conditions are poor, suggesting limited residential suitability.",
        },
        "agriculture": {
            "strength": "Fertile soils and favorable climate indicate high agricultural productivity potential.",
            "weakness": "Agricultural potential is severely limited by soil or climate deficiencies.",
        },
        "ecology": {
            "strength": "Rich biodiversity and ecological integrity support a healthy natural environment.",
            "weakness": "Ecological value is low, indicating degraded natural habitats or limited biodiversity.",
        },
        "hazard_safety": {
            "strength": "The location shows minimal exposure to natural hazards and safety threats.",
            "weakness": "Significant natural hazard exposure poses risks to assets and personnel.",
        },
        "water_resources": {
            "strength": "Abundant water sources and proximity to water bodies ensure reliable supply.",
            "weakness": "Water scarcity is a critical concern requiring mitigation strategies.",
        },
        "infrastructure": {
            "strength": "Well-developed infrastructure supports operations and connectivity.",
            "weakness": "Infrastructure deficits present significant operational challenges.",
        },
        "climate_comfort": {
            "strength": "Climate conditions are favorable for sustained human activity and operations.",
            "weakness": "Extreme climate conditions limit operational windows and human comfort.",
        },
        "economic_potential": {
            "strength": "Strong economic indicators suggest viable commercial and development opportunities.",
            "weakness": "Economic conditions are unfavorable for investment or development activities.",
        },
        "air_environment": {
            "strength": "Air quality and environmental conditions meet healthy standards.",
            "weakness": "Poor air quality or environmental degradation poses health and operational risks.",
        },
        "geological_stability": {
            "strength": "Geologically stable terrain supports safe construction and operations.",
            "weakness": "Geological instability (seismic, volcanic, or terrain risks) is a major concern.",
        },
    }
    return interpretations.get(domain, {}).get(
        category, "Assessment data available for further analysis."
    )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: THREAT ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════

def _render_threat_assessment(threats):
    """Render the threat assessment section."""
    _section_open()
    _section_header(4, "THREAT ASSESSMENT", OPS_RED)

    if not threats:
        st.markdown(
            f'<p style="color: {OPS_TEXT_DIM}; font-style: italic;">Threat data not available.</p>',
            unsafe_allow_html=True,
        )
        _section_close()
        return

    threat_level = threats.get("threat_level", "UNKNOWN")
    threat_score = threats.get("threat_score", 0)
    threat_color = _THREAT_COLORS.get(threat_level, OPS_TEXT_DIM)
    proximity_alert = threats.get("proximity_alert", False)

    # Threat level banner
    st.markdown(f'''
    <div style="background: linear-gradient(90deg, {threat_color}22 0%, transparent 100%);
        border-left: 4px solid {threat_color}; padding: 1rem 1.5rem; margin-bottom: 1rem;
        border-radius: 0 6px 6px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="color: {OPS_TEXT_DIM}; font-size: 0.6rem; letter-spacing: 2px;">
                    CURRENT THREAT LEVEL</span><br>
                <span style="color: {threat_color}; font-size: 1.8rem; font-weight: 800;">
                    {threat_level}</span>
            </div>
            <div style="text-align: right;">
                <span style="color: {OPS_TEXT_DIM}; font-size: 0.6rem; letter-spacing: 2px;">
                    COMPOSITE THREAT SCORE</span><br>
                <span style="color: {threat_color}; font-size: 1.4rem; font-weight: 700;">
                    {threat_score:.0f}/100</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Proximity alert
    if proximity_alert:
        st.markdown(f'''
        <div style="background: {OPS_RED}22; border: 1px solid {OPS_RED}; border-radius: 6px;
            padding: 0.8rem 1rem; margin-bottom: 1rem;">
            <span style="color: {OPS_RED}; font-weight: 700;">&#9888; PROXIMITY ALERT:</span>
            <span style="color: {OPS_TEXT};">
                Active threats detected within close proximity to the target location.
                Immediate assessment recommended.</span>
        </div>
        ''', unsafe_allow_html=True)

    # Threat sources
    threat_sources = threats.get("threat_sources", [])
    if threat_sources and isinstance(threat_sources, list):
        st.markdown(
            f'<div style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin: 0.8rem 0 0.5rem;">IDENTIFIED THREAT SOURCES</div>',
            unsafe_allow_html=True,
        )
        _source_icons = {
            "fire": "&#128293;", "earthquake": "&#127754;", "seismic": "&#127754;",
            "disaster": "&#9888;", "air": "&#127787;", "flood": "&#127754;",
            "terrain": "&#9968;", "gdacs": "&#9888;",
        }
        for src in threat_sources:
            if not isinstance(src, dict):
                continue
            src_name = src.get("source", "Unknown")
            src_level = src.get("level", "N/A")
            src_count = src.get("count", 0)
            src_nearest = src.get("nearest_km", None)
            src_details = src.get("details", "")
            src_color = _THREAT_COLORS.get(src_level, OPS_TEXT_DIM)

            # Find matching icon
            icon = "&#9679;"
            for key, ico in _source_icons.items():
                if key in src_name.lower():
                    icon = ico
                    break

            nearest_text = f" | Nearest: {src_nearest:.1f} km" if src_nearest else ""
            count_text = f" | Count: {src_count}" if src_count else ""

            st.markdown(f'''
            <div style="padding: 0.5rem 0; border-bottom: 1px solid #111828;
                display: flex; align-items: center; gap: 0.8rem;">
                <span style="font-size: 1.2rem;">{icon}</span>
                <div style="flex: 1;">
                    <span style="color: {OPS_TEXT}; font-weight: 600;">{html_module.escape(src_name)}</span>
                    <span style="color: {src_color}; font-size: 0.75rem; margin-left: 0.5rem;
                        padding: 0.1rem 0.5rem; border: 1px solid {src_color};
                        border-radius: 3px;">{src_level}</span>
                    <div style="color: {OPS_TEXT_DIM}; font-size: 0.75rem;">
                        {html_module.escape(src_details)}{count_text}{nearest_text}</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown(
            f'<p style="color: {OPS_GREEN}; font-size: 0.85rem;">No active threat sources detected.</p>',
            unsafe_allow_html=True,
        )

    # Summary
    summary = threats.get("threat_summary", "")
    if summary:
        st.markdown(f'''
        <div style="margin-top: 1rem; padding: 0.8rem; background: #0d1225;
            border-radius: 6px;">
            <div style="color: {OPS_TEXT_DIM}; font-size: 0.6rem; letter-spacing: 2px;
                margin-bottom: 0.3rem;">THREAT SUMMARY</div>
            <div style="color: {OPS_TEXT}; font-size: 0.85rem; line-height: 1.6;">
                {html_module.escape(summary)}</div>
        </div>
        ''', unsafe_allow_html=True)

    _section_close()


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: RISK SIMULATION (Monte Carlo)
# ═══════════════════════════════════════════════════════════════════════════

def _render_risk_simulation(mc_result, sensitivity, confidence):
    """Render Monte Carlo risk simulation results."""
    _section_open()
    _section_header(5, "RISK SIMULATION (MONTE CARLO)", OPS_AMBER)

    if not mc_result or not isinstance(mc_result, dict) or "overall" not in mc_result:
        st.markdown(
            f'<p style="color: {OPS_TEXT_DIM}; font-style: italic;">'
            f'Monte Carlo simulation data not available.</p>',
            unsafe_allow_html=True,
        )
        _section_close()
        return

    overall = mc_result.get("overall", {})
    mc_mean = overall.get("mean", 0)
    mc_p5 = overall.get("p5", 0)
    mc_p95 = overall.get("p95", 0)
    mc_std = overall.get("std", 0)
    n_iter = mc_result.get("n_iterations", 0)
    risk_class = mc_result.get("risk_classification", "Unknown")
    histogram_bins = mc_result.get("histogram_bins", [])

    # Histogram
    if HAS_PLOTLY and histogram_bins:
        try:
            bin_edges = [b.get("bin_start", 0) for b in histogram_bins]
            bin_counts = [b.get("count", 0) for b in histogram_bins]
            bin_centers = [
                (b.get("bin_start", 0) + b.get("bin_end", b.get("bin_start", 0) + 5)) / 2
                for b in histogram_bins
            ]
            bin_colors = [_score_color(c) for c in bin_centers]

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=bin_centers,
                y=bin_counts,
                marker_color=bin_colors,
                marker_line_color="#1a2035",
                marker_line_width=1,
                hovertemplate="Score: %{x:.1f}<br>Frequency: %{y}<extra></extra>",
                width=[(histogram_bins[0].get("bin_end", 5) - histogram_bins[0].get("bin_start", 0))] * len(bin_centers) if histogram_bins else 5,
            ))
            # Add mean line
            fig.add_vline(x=mc_mean, line_dash="dash", line_color=OPS_CYAN, line_width=2)
            fig.add_annotation(
                x=mc_mean, y=max(bin_counts) * 0.95,
                text=f"Mean: {mc_mean:.1f}",
                font=dict(color=OPS_CYAN, size=10),
                showarrow=False,
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color=OPS_TEXT,
                margin=dict(l=20, r=20, t=40, b=20),
                height=300,
                xaxis=dict(title="Overall Score", gridcolor="#1a2035",
                           title_font=dict(color=OPS_TEXT_DIM, size=10)),
                yaxis=dict(title="Frequency", gridcolor="#1a2035",
                           title_font=dict(color=OPS_TEXT_DIM, size=10)),
                title=dict(
                    text=f"Score Distribution ({n_iter:,} iterations)",
                    font=dict(color=OPS_TEXT_DIM, size=12),
                ),
            )
            st.plotly_chart(fig, use_container_width=True, key="dossier_mc_histogram")
        except Exception as exc:
            logger.warning("MC histogram render failed: %s", exc)

    # Key stats row
    ks1, ks2, ks3, ks4 = st.columns(4)
    _mc_stats = [
        (ks1, "MEAN", f"{mc_mean:.1f}", OPS_CYAN),
        (ks2, "P5 (WORST)", f"{mc_p5:.1f}", OPS_RED),
        (ks3, "P95 (BEST)", f"{mc_p95:.1f}", OPS_GREEN),
        (ks4, "STD DEV", f"{mc_std:.2f}", OPS_PURPLE),
    ]
    for col, label, value, color in _mc_stats:
        with col:
            st.markdown(f'''
            <div style="text-align: center; padding: 0.5rem;">
                <div style="color: {OPS_TEXT_DIM}; font-size: 0.6rem; letter-spacing: 2px;">
                    {label}</div>
                <div style="color: {color}; font-size: 1.3rem; font-weight: 700;">{value}</div>
            </div>
            ''', unsafe_allow_html=True)

    # Probability metrics
    p_viable = overall.get("probability_above_60", 0)
    p_marginal = overall.get("probability_above_40", 0)
    p_critical = overall.get("probability_below_30", 0)

    st.markdown(f'''
    <div style="margin-top: 1rem; padding: 0.8rem; background: #0d1225; border-radius: 6px;">
        <div style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px;
            margin-bottom: 0.5rem;">PROBABILITY METRICS</div>
        <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
            <div>
                <span style="color: {OPS_GREEN};">P(Viable &gt; 60):</span>
                <span style="color: {OPS_TEXT}; font-weight: 700;"> {p_viable:.1f}%</span>
            </div>
            <div>
                <span style="color: {OPS_AMBER};">P(Marginal &gt; 40):</span>
                <span style="color: {OPS_TEXT}; font-weight: 700;"> {p_marginal:.1f}%</span>
            </div>
            <div>
                <span style="color: {OPS_RED};">P(Critical &lt; 30):</span>
                <span style="color: {OPS_TEXT}; font-weight: 700;"> {p_critical:.1f}%</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Risk classification badge
    risk_color = OPS_GREEN if "Low" in risk_class else (OPS_AMBER if "Moderate" in risk_class else OPS_RED)
    st.markdown(f'''
    <div style="margin-top: 0.8rem; display: flex; align-items: center; gap: 0.8rem;">
        <span style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px;">
            RISK CLASSIFICATION:</span>
        <span style="color: {risk_color}; font-weight: 800; font-size: 1.1rem;
            border: 2px solid {risk_color}; padding: 0.2rem 0.8rem; border-radius: 4px;">
            {html_module.escape(risk_class)}</span>
    </div>
    ''', unsafe_allow_html=True)

    # Sensitivity analysis (tornado chart)
    if sensitivity and isinstance(sensitivity, list) and HAS_PLOTLY:
        try:
            st.markdown(
                f'<div style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px; '
                f'margin-top: 1.5rem; margin-bottom: 0.5rem;">SENSITIVITY ANALYSIS (TORNADO)</div>',
                unsafe_allow_html=True,
            )
            domains_sa = [s.get("domain", "") for s in sensitivity[:10]]
            worst_vals = [s.get("worst_case_mean", 0) for s in sensitivity[:10]]
            best_vals = [s.get("best_case_mean", 0) for s in sensitivity[:10]]

            fig_sa = go.Figure()
            fig_sa.add_trace(go.Bar(
                y=domains_sa,
                x=[w - mc_mean for w in worst_vals],
                orientation="h",
                name="Worst Case",
                marker_color=OPS_RED,
                hovertemplate="%{y}: %{x:+.1f} from mean<extra>Worst</extra>",
            ))
            fig_sa.add_trace(go.Bar(
                y=domains_sa,
                x=[b - mc_mean for b in best_vals],
                orientation="h",
                name="Best Case",
                marker_color=OPS_GREEN,
                hovertemplate="%{y}: %{x:+.1f} from mean<extra>Best</extra>",
            ))
            fig_sa.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color=OPS_TEXT,
                margin=dict(l=20, r=20, t=40, b=20),
                height=350,
                barmode="overlay",
                xaxis=dict(title="Impact on Overall Score", gridcolor="#1a2035",
                           title_font=dict(color=OPS_TEXT_DIM, size=10),
                           zeroline=True, zerolinecolor="#334"),
                yaxis=dict(autorange="reversed",
                           tickfont=dict(color=OPS_TEXT, size=10)),
                legend=dict(font=dict(color=OPS_TEXT_DIM, size=10),
                            orientation="h", y=-0.15),
                title=dict(
                    text="Domain Impact on Overall Score",
                    font=dict(color=OPS_TEXT_DIM, size=12),
                ),
            )
            st.plotly_chart(fig_sa, use_container_width=True, key="dossier_sensitivity_tornado")
        except Exception as exc:
            logger.warning("Sensitivity chart render failed: %s", exc)

    _section_close()


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: CORRELATION INTELLIGENCE
# ═══════════════════════════════════════════════════════════════════════════

def _render_correlation_intelligence(correlation, hub):
    """Render correlation intelligence and cross-domain insights."""
    _section_open()
    _section_header(6, "CORRELATION INTELLIGENCE", OPS_CYAN)

    if not correlation or not isinstance(correlation, list):
        st.markdown(
            f'<p style="color: {OPS_TEXT_DIM}; font-style: italic;">'
            f'Cross-correlation data not available.</p>',
            unsafe_allow_html=True,
        )
        _section_close()
        return

    # Separate positive, negative, and anomalous insights
    positive = []
    negative = []
    anomalous = []
    general = []

    for insight in correlation:
        if not isinstance(insight, dict):
            # Might be a string-based insight
            general.append(str(insight))
            continue
        text = insight.get("text", insight.get("insight", str(insight)))
        conf = insight.get("confidence", 0.5)
        itype = insight.get("type", "")

        if "anomal" in itype.lower() or "anomal" in text.lower():
            anomalous.append((text, conf))
        elif conf >= 0.6 and ("strong" in text.lower() or "high" in text.lower()
                              or "positive" in text.lower() or "good" in text.lower()):
            positive.append((text, conf))
        elif "weak" in text.lower() or "low" in text.lower() or "negative" in text.lower():
            negative.append((text, conf))
        else:
            general.append((text, conf) if isinstance(conf, float) else text)

    # Positive correlations
    if positive:
        st.markdown(
            f'<div style="color: {OPS_GREEN}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin-bottom: 0.5rem;">POSITIVE CORRELATIONS</div>',
            unsafe_allow_html=True,
        )
        for text, conf in positive[:5]:
            st.markdown(f'''
            <div style="padding: 0.3rem 0; border-bottom: 1px solid #111828;">
                <span style="color: {OPS_GREEN}; font-size: 0.75rem; margin-right: 0.5rem;">
                    &#9650;</span>
                <span style="color: {OPS_TEXT}; font-size: 0.85rem;">{html_module.escape(text)}</span>
                <span style="color: {OPS_TEXT_DIM}; font-size: 0.7rem; margin-left: 0.5rem;">
                    (conf: {conf:.0%})</span>
            </div>
            ''', unsafe_allow_html=True)

    # Negative correlations
    if negative:
        st.markdown(
            f'<div style="color: {OPS_RED}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin: 1rem 0 0.5rem;">NEGATIVE CORRELATIONS</div>',
            unsafe_allow_html=True,
        )
        for text, conf in negative[:3]:
            st.markdown(f'''
            <div style="padding: 0.3rem 0; border-bottom: 1px solid #111828;">
                <span style="color: {OPS_RED}; font-size: 0.75rem; margin-right: 0.5rem;">
                    &#9660;</span>
                <span style="color: {OPS_TEXT}; font-size: 0.85rem;">{html_module.escape(text)}</span>
                <span style="color: {OPS_TEXT_DIM}; font-size: 0.7rem; margin-left: 0.5rem;">
                    (conf: {conf:.0%})</span>
            </div>
            ''', unsafe_allow_html=True)

    # Anomalous relationships
    if anomalous:
        st.markdown(
            f'<div style="color: {OPS_AMBER}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin: 1rem 0 0.5rem;">ANOMALOUS RELATIONSHIPS</div>',
            unsafe_allow_html=True,
        )
        for text, conf in anomalous[:3]:
            st.markdown(f'''
            <div style="padding: 0.3rem 0; border-bottom: 1px solid #111828;
                background: {OPS_AMBER}08;">
                <span style="color: {OPS_AMBER}; font-size: 0.75rem; margin-right: 0.5rem;">
                    &#9888;</span>
                <span style="color: {OPS_TEXT}; font-size: 0.85rem;">{html_module.escape(text)}</span>
                <span style="color: {OPS_TEXT_DIM}; font-size: 0.7rem; margin-left: 0.5rem;">
                    (conf: {conf:.0%})</span>
            </div>
            ''', unsafe_allow_html=True)

    # General insights
    all_insights = positive + negative + anomalous
    remaining = general if not all_insights else general[:5]
    if remaining:
        st.markdown(
            f'<div style="color: {OPS_BLUE}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin: 1rem 0 0.5rem;">KEY INSIGHTS</div>',
            unsafe_allow_html=True,
        )
        for item in remaining[:5]:
            text = item[0] if isinstance(item, tuple) else item
            conf = item[1] if isinstance(item, tuple) and len(item) > 1 else None
            conf_text = f' (conf: {conf:.0%})' if conf and isinstance(conf, (int, float)) else ""
            st.markdown(f'''
            <div style="padding: 0.3rem 0; border-bottom: 1px solid #111828;">
                <span style="color: {OPS_BLUE}; font-size: 0.75rem; margin-right: 0.5rem;">
                    &#8226;</span>
                <span style="color: {OPS_TEXT}; font-size: 0.85rem;">{html_module.escape(str(text))}</span>
                <span style="color: {OPS_TEXT_DIM}; font-size: 0.7rem;">{conf_text}</span>
            </div>
            ''', unsafe_allow_html=True)

    if not positive and not negative and not anomalous and not remaining:
        st.markdown(
            f'<p style="color: {OPS_TEXT_DIM}; font-style: italic;">'
            f'No significant cross-domain correlations detected.</p>',
            unsafe_allow_html=True,
        )

    _section_close()


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: STRATEGIC ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════

def _render_strategic_assessment(strategic):
    """Render strategic assessment with radar chart and decision queue."""
    _section_open()
    _section_header(7, "STRATEGIC ASSESSMENT", OPS_GREEN)

    if not strategic or not isinstance(strategic, dict):
        st.markdown(
            f'<p style="color: {OPS_TEXT_DIM}; font-style: italic;">'
            f'Strategic assessment data not available.</p>',
            unsafe_allow_html=True,
        )
        _section_close()
        return

    dimensions = strategic.get("dimensions", {})
    or_quadrant = strategic.get("opportunity_risk_quadrant", "Unknown")
    dpq = strategic.get("decision_priority_queue", [])
    multi_horizon = strategic.get("multi_horizon", {})
    strat_score = strategic.get("strategic_score", 0)

    # Radar chart of 5 strategic dimensions
    if dimensions and HAS_PLOTLY:
        try:
            dim_names = list(dimensions.keys())
            dim_values = [dimensions[d] if isinstance(dimensions[d], (int, float))
                          else dimensions[d].get("score", 50)
                          if isinstance(dimensions[d], dict) else 50
                          for d in dim_names]
            dim_labels = [d.replace("_", " ").title() for d in dim_names]

            # Close the polygon
            plot_labels = dim_labels + [dim_labels[0]]
            plot_values = dim_values + [dim_values[0]]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=plot_values,
                theta=plot_labels,
                fill="toself",
                fillcolor=_hex_rgba(OPS_CYAN, 0.13),
                line_color=OPS_CYAN,
                line_width=2,
                marker=dict(size=6, color=OPS_CYAN),
                hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
            ))
            fig_radar.update_layout(
                polar=dict(
                    bgcolor="rgba(0,0,0,0)",
                    radialaxis=dict(
                        visible=True, range=[0, 100],
                        gridcolor="#1a2035", tickfont=dict(color=OPS_TEXT_DIM, size=9),
                    ),
                    angularaxis=dict(
                        gridcolor="#1a2035", tickfont=dict(color=OPS_TEXT, size=10),
                    ),
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                font_color=OPS_TEXT,
                margin=dict(l=60, r=60, t=40, b=40),
                height=400,
                title=dict(
                    text="Strategic Dimensions Profile",
                    font=dict(color=OPS_TEXT_DIM, size=12),
                ),
            )
            st.plotly_chart(fig_radar, use_container_width=True, key="dossier_strategic_radar")
        except Exception as exc:
            logger.warning("Strategic radar chart failed: %s", exc)

    # Opportunity-Risk Quadrant badge
    quad_colors = {
        "High Opportunity / Low Risk": OPS_GREEN,
        "High Opportunity / High Risk": OPS_AMBER,
        "Low Opportunity / Low Risk": OPS_BLUE,
        "Low Opportunity / High Risk": OPS_RED,
    }
    quad_color = OPS_PURPLE
    for pattern, color in quad_colors.items():
        if pattern.lower() in str(or_quadrant).lower():
            quad_color = color
            break

    st.markdown(f'''
    <div style="text-align: center; margin: 1.5rem 0;">
        <div style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px;
            margin-bottom: 0.3rem;">OPPORTUNITY-RISK QUADRANT</div>
        <div style="display: inline-block; color: {quad_color}; font-size: 1.3rem;
            font-weight: 800; border: 2px solid {quad_color}; padding: 0.5rem 1.5rem;
            border-radius: 6px; background: {quad_color}11;">
            {html_module.escape(str(or_quadrant))}</div>
    </div>
    ''', unsafe_allow_html=True)

    # Decision Priority Queue
    if dpq and isinstance(dpq, list):
        st.markdown(
            f'<div style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin: 1rem 0 0.5rem;">DECISION PRIORITY QUEUE</div>',
            unsafe_allow_html=True,
        )
        for i, action in enumerate(dpq[:5], 1):
            if isinstance(action, dict):
                title = action.get("action", action.get("title", "Unnamed Action"))
                urgency = action.get("urgency", "medium")
                impact = action.get("impact", "medium")
                domain = action.get("domain", "")
            elif isinstance(action, str):
                title = action
                urgency = "medium"
                impact = "medium"
                domain = ""
            else:
                continue

            urgency_color = OPS_RED if "high" in str(urgency).lower() else (
                OPS_AMBER if "med" in str(urgency).lower() else OPS_GREEN)

            st.markdown(f'''
            <div style="padding: 0.5rem 0; border-bottom: 1px solid #111828;
                display: flex; align-items: flex-start; gap: 0.8rem;">
                <span style="color: {OPS_CYAN}; font-size: 1.1rem; font-weight: 800;
                    min-width: 24px;">#{i}</span>
                <div style="flex: 1;">
                    <span style="color: {OPS_TEXT}; font-weight: 600;">{html_module.escape(str(title))}</span>
                    <div style="margin-top: 0.2rem;">
                        <span style="color: {urgency_color}; font-size: 0.7rem;
                            border: 1px solid {urgency_color}; padding: 0.05rem 0.4rem;
                            border-radius: 3px;">Urgency: {html_module.escape(str(urgency))}</span>
                        <span style="color: {OPS_BLUE}; font-size: 0.7rem;
                            border: 1px solid {OPS_BLUE}; padding: 0.05rem 0.4rem;
                            border-radius: 3px; margin-left: 0.3rem;">Impact: {html_module.escape(str(impact))}</span>
                        {"<span style='color: " + OPS_TEXT_DIM + "; font-size: 0.7rem; margin-left: 0.3rem;'>" + html_module.escape(str(domain)) + "</span>" if domain else ""}
                    </div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

    # Multi-Horizon Outlook
    if multi_horizon and isinstance(multi_horizon, dict):
        st.markdown(
            f'<div style="color: {OPS_TEXT_DIM}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin: 1.5rem 0 0.5rem;">MULTI-HORIZON OUTLOOK</div>',
            unsafe_allow_html=True,
        )
        horizon_configs = [
            ("short_term", "SHORT TERM (0-6 months)", OPS_CYAN),
            ("medium_term", "MEDIUM TERM (6-24 months)", OPS_BLUE),
            ("long_term", "LONG TERM (2-5 years)", OPS_PURPLE),
        ]
        hc1, hc2, hc3 = st.columns(3)
        horizon_cols = [hc1, hc2, hc3]

        for col, (key, label, color) in zip(horizon_cols, horizon_configs):
            with col:
                horizon_data = multi_horizon.get(key, {})
                if isinstance(horizon_data, dict):
                    outlook = horizon_data.get("outlook", horizon_data.get("summary", "N/A"))
                    trend = horizon_data.get("trend", "")
                    conf_h = horizon_data.get("confidence", 0)
                elif isinstance(horizon_data, str):
                    outlook = horizon_data
                    trend = ""
                    conf_h = 0
                else:
                    outlook = "N/A"
                    trend = ""
                    conf_h = 0

                trend_icon = ""
                if "improv" in str(trend).lower() or "up" in str(trend).lower():
                    trend_icon = f'<span style="color: {OPS_GREEN};">&#9650;</span> '
                elif "declin" in str(trend).lower() or "down" in str(trend).lower():
                    trend_icon = f'<span style="color: {OPS_RED};">&#9660;</span> '
                elif trend:
                    trend_icon = f'<span style="color: {OPS_AMBER};">&#9654;</span> '

                st.markdown(f'''
                <div style="background: #0d1225; padding: 0.8rem; border-radius: 6px;
                    border-top: 2px solid {color}; height: 100%;">
                    <div style="color: {color}; font-size: 0.6rem; letter-spacing: 2px;
                        margin-bottom: 0.5rem;">{label}</div>
                    <div style="color: {OPS_TEXT}; font-size: 0.82rem; line-height: 1.5;">
                        {trend_icon}{html_module.escape(str(outlook))}</div>
                    {"<div style='color: " + OPS_TEXT_DIM + "; font-size: 0.7rem; margin-top: 0.3rem;'>Confidence: " + f"{conf_h:.0%}" + "</div>" if conf_h else ""}
                </div>
                ''', unsafe_allow_html=True)

    _section_close()


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: DATA CONFIDENCE
# ═══════════════════════════════════════════════════════════════════════════

def _render_data_confidence(confidence, raw_data):
    """Render data confidence gauge and source assessment."""
    _section_open()
    _section_header(8, "DATA CONFIDENCE", OPS_BLUE)

    confidence_pct = confidence * 100 if confidence <= 1 else confidence

    # Gauge chart
    if HAS_PLOTLY:
        try:
            gauge_color = OPS_GREEN if confidence_pct >= 70 else (
                OPS_AMBER if confidence_pct >= 40 else OPS_RED)

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=confidence_pct,
                number=dict(suffix="%", font=dict(color=gauge_color, size=40)),
                gauge=dict(
                    axis=dict(range=[0, 100], tickfont=dict(color=OPS_TEXT_DIM, size=10),
                              dtick=20),
                    bar=dict(color=gauge_color),
                    bgcolor="#0d1225",
                    borderwidth=0,
                    steps=[
                        dict(range=[0, 40], color=_hex_rgba(OPS_RED, 0.13)),
                        dict(range=[40, 70], color=_hex_rgba(OPS_AMBER, 0.13)),
                        dict(range=[70, 100], color=_hex_rgba(OPS_GREEN, 0.13)),
                    ],
                    threshold=dict(
                        line=dict(color=OPS_TEXT, width=2),
                        thickness=0.8,
                        value=confidence_pct,
                    ),
                ),
                title=dict(text="Data Completeness",
                           font=dict(color=OPS_TEXT_DIM, size=12)),
            ))
            fig_gauge.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color=OPS_TEXT,
                margin=dict(l=30, r=30, t=60, b=20),
                height=250,
            )
            st.plotly_chart(fig_gauge, use_container_width=True, key="dossier_confidence_gauge")
        except Exception as exc:
            logger.warning("Confidence gauge failed: %s", exc)

    # Data sources inventory
    _data_sources = [
        ("elevation", "Elevation / Terrain"),
        ("soil", "SoilGrids (Soil Properties)"),
        ("weather", "Weather / Climate"),
        ("inat", "Biodiversity (iNaturalist)"),
        ("water", "Water Resources"),
        ("quakes", "Seismic / Earthquakes"),
        ("geology", "Geological Data"),
        ("infra", "Infrastructure (Overpass)"),
        ("air_quality", "Air Quality"),
        ("protected", "Protected Areas"),
        ("gdacs", "GDACS Disaster Alerts"),
        ("population", "Population Density"),
        ("openaq", "OpenAQ Air Monitoring"),
    ]

    available = []
    missing = []
    for key, label in _data_sources:
        val = raw_data.get(key)
        if val not in (None, {}, [], 0):
            available.append(label)
        else:
            missing.append(label)

    dc1, dc2 = st.columns(2)
    with dc1:
        st.markdown(
            f'<div style="color: {OPS_GREEN}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin-bottom: 0.5rem;">AVAILABLE SOURCES ({len(available)}/{len(_data_sources)})</div>',
            unsafe_allow_html=True,
        )
        for src in available:
            st.markdown(
                f'<div style="color: {OPS_TEXT}; font-size: 0.8rem; padding: 0.15rem 0;">'
                f'<span style="color: {OPS_GREEN};">&#10003;</span> {src}</div>',
                unsafe_allow_html=True,
            )
    with dc2:
        st.markdown(
            f'<div style="color: {OPS_RED}; font-size: 0.65rem; letter-spacing: 2px; '
            f'margin-bottom: 0.5rem;">MISSING SOURCES ({len(missing)}/{len(_data_sources)})</div>',
            unsafe_allow_html=True,
        )
        if missing:
            for src in missing:
                st.markdown(
                    f'<div style="color: {OPS_TEXT_DIM}; font-size: 0.8rem; padding: 0.15rem 0;">'
                    f'<span style="color: {OPS_RED};">&#10007;</span> {src}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                f'<p style="color: {OPS_GREEN}; font-size: 0.85rem;">All sources available.</p>',
                unsafe_allow_html=True,
            )

    # Recommendation
    if confidence_pct < 50:
        rec_text = (
            "Data confidence is below 50%. Consider re-running the analysis after verifying "
            "network connectivity to all API endpoints. Missing data sources significantly "
            "reduce the reliability of domain scores and strategic assessments."
        )
        rec_color = OPS_RED
    elif confidence_pct < 75:
        rec_text = (
            "Data confidence is moderate. Some data sources are unavailable, which may affect "
            "the precision of certain domain scores. Results should be treated as indicative "
            "rather than definitive for the affected domains."
        )
        rec_color = OPS_AMBER
    else:
        rec_text = (
            "Data confidence is high. The majority of data sources are available and contributing "
            "to the analysis. Results across all domains are considered reliable for "
            "decision-making purposes."
        )
        rec_color = OPS_GREEN

    st.markdown(f'''
    <div style="margin-top: 1rem; padding: 0.8rem; background: #0d1225; border-radius: 6px;
        border-left: 3px solid {rec_color};">
        <div style="color: {rec_color}; font-size: 0.65rem; letter-spacing: 2px;
            margin-bottom: 0.3rem;">CONFIDENCE ASSESSMENT</div>
        <div style="color: {OPS_TEXT}; font-size: 0.85rem; line-height: 1.6;">{rec_text}</div>
    </div>
    ''', unsafe_allow_html=True)

    _section_close()


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: CLASSIFICATION FOOTER
# ═══════════════════════════════════════════════════════════════════════════

def _render_classification_footer(lat, lon, timestamp):
    """Render the classified document footer."""
    st.markdown(f'''
    <div style="margin-top: 3rem; border-top: 2px solid {OPS_PURPLE}; padding-top: 1.5rem;
        text-align: center;">
        <div style="color: {OPS_PURPLE}; font-size: 0.7rem; letter-spacing: 4px;
            font-weight: 700; margin-bottom: 0.5rem;">
            DOCUMENT CLASSIFICATION: INTERNAL &mdash; FOR AUTHORIZED ANALYSTS ONLY</div>
        <div style="color: {OPS_TEXT_DIM}; font-size: 0.75rem; margin-bottom: 0.3rem;">
            Generated by TerraScout AI Intelligence Platform</div>
        <div style="color: {OPS_TEXT_DIM}; font-size: 0.7rem;">
            Timestamp: {timestamp} &bull; Coordinates: {lat:.5f}N, {lon:.5f}E</div>
        <div style="color: #1a2035; font-size: 0.6rem; margin-top: 1rem;">
            &mdash; END OF DOSSIER &mdash;</div>
    </div>
    ''', unsafe_allow_html=True)
