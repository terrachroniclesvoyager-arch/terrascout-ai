"""
Temporal Analysis Dashboard for TerraScout AI.

Visualises how a location's intelligence profile changes over time using
predictive projections, scenario wargaming timelines, domain velocity
analysis, inflection-point detection, and intervention simulation.

Entry point: render_temporal_dashboard()
"""

import logging
import html as html_module

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
from src.predictive_engine import (
    compute_predictive_outlook,
    generate_early_warnings,
    compute_opportunity_windows,
    generate_prediction_narrative,
)
from src.scenario_wargaming import (
    run_scenario_wargame,
    get_predefined_scenarios,
    generate_wargame_narrative,
)
from src.unified_intelligence import (
    INTELLIGENCE_DOMAINS,
    compute_advanced_analytics,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Ops-center colour palette
# ---------------------------------------------------------------------------
OPS_BG = "#050510"
OPS_PANEL = "#0a0a18"
OPS_CYAN = "#00f0ff"
OPS_GREEN = "#00ff88"
OPS_AMBER = "#ffaa00"
OPS_RED = "#ff3344"
OPS_BLUE = "#4488ff"
OPS_PURPLE = "#aa55ff"
OPS_TEXT = "#e0e8f0"
OPS_TEXT_DIM = "#5a7090"

# Thresholds (mirrored from predictive_engine)
VIABLE_THRESHOLD = 60
CRITICAL_THRESHOLD = 30

# Time-horizon labels used across charts
_HORIZON_LABELS = ["Now", "3 mo", "1 yr", "5 yr"]
_HORIZON_KEYS = ["current", "short_term", "medium_term", "long_term"]

# Domain colour map (fallback to INTELLIGENCE_DOMAINS colours)
def _domain_color(domain: str) -> str:
    return INTELLIGENCE_DOMAINS.get(domain, {}).get("color", OPS_CYAN)


def _domain_name(domain: str) -> str:
    return INTELLIGENCE_DOMAINS.get(domain, {}).get("name", domain.replace("_", " ").title())


def _safe(val, default=0.0):
    """Return *val* if numeric, else *default*."""
    if isinstance(val, (int, float)):
        return float(val)
    return default


def _plotly_dark_layout(fig: go.Figure, title: str = "", height: int = 420):
    """Apply the standard dark ops-center layout to a Plotly figure."""
    fig.update_layout(
        title=dict(text=title, font=dict(color=OPS_TEXT, size=16)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=OPS_TEXT, size=12),
        height=height,
        margin=dict(l=50, r=30, t=50, b=40),
        legend=dict(
            font=dict(color=OPS_TEXT_DIM, size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            gridcolor="rgba(90,112,144,0.15)",
            zerolinecolor="rgba(90,112,144,0.25)",
        ),
        yaxis=dict(
            gridcolor="rgba(90,112,144,0.15)",
            zerolinecolor="rgba(90,112,144,0.25)",
        ),
    )


def _section_header(title: str, subtitle: str = ""):
    """Render a styled section header."""
    sub_html = f'<div style="color:{OPS_TEXT_DIM};font-size:13px;margin-top:2px;">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div style="border-left:3px solid {OPS_CYAN};padding:8px 16px;
                     margin:28px 0 12px 0;background:rgba(0,240,255,0.04);
                     border-radius:0 8px 8px 0;">
            <div style="color:{OPS_CYAN};font-size:18px;font-weight:700;
                         letter-spacing:1px;">{title}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===================================================================
# A. TEMPORAL OVERVIEW
# ===================================================================

def _render_temporal_overview(hub: dict, outlook: dict):
    """Current state summary + risk trajectory + overall score timeline."""
    try:
        _section_header("TEMPORAL OVERVIEW", "Current state and projected trajectory")

        overall_score = hub.get("overall_score", 0)
        overall_label = hub.get("overall_label", "Unknown")
        _conf_raw = hub.get("confidence", 0)
        confidence = float(_conf_raw.get("overall", 0)) if isinstance(_conf_raw, dict) else float(_conf_raw or 0)
        trajectory = outlook.get("risk_trajectory", "STABLE")
        overall_fc = outlook.get("overall_forecast", {})

        # Trajectory styling
        traj_colors = {
            "IMPROVING": OPS_GREEN,
            "STABLE": OPS_AMBER,
            "WORSENING": OPS_RED,
        }
        traj_icons = {
            "IMPROVING": "&#9650;",  # up triangle
            "STABLE": "&#9644;",     # horizontal bar
            "WORSENING": "&#9660;",  # down triangle
        }
        traj_color = traj_colors.get(trajectory, OPS_TEXT_DIM)
        traj_icon = traj_icons.get(trajectory, "")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""<div style="background:{OPS_PANEL};border-radius:12px;padding:18px;text-align:center;">
                    <div style="color:{OPS_TEXT_DIM};font-size:12px;text-transform:uppercase;">Overall Score</div>
                    <div style="color:{OPS_CYAN};font-size:36px;font-weight:800;">{overall_score:.1f}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f"""<div style="background:{OPS_PANEL};border-radius:12px;padding:18px;text-align:center;">
                    <div style="color:{OPS_TEXT_DIM};font-size:12px;text-transform:uppercase;">Classification</div>
                    <div style="color:{OPS_TEXT};font-size:22px;font-weight:700;margin-top:6px;">{overall_label}</div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"""<div style="background:{OPS_PANEL};border-radius:12px;padding:18px;text-align:center;">
                    <div style="color:{OPS_TEXT_DIM};font-size:12px;text-transform:uppercase;">Risk Trajectory</div>
                    <div style="color:{traj_color};font-size:22px;font-weight:700;margin-top:6px;">
                        {traj_icon} {trajectory}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                f"""<div style="background:{OPS_PANEL};border-radius:12px;padding:18px;text-align:center;">
                    <div style="color:{OPS_TEXT_DIM};font-size:12px;text-transform:uppercase;">Data Confidence</div>
                    <div style="color:{OPS_GREEN if confidence > 0.6 else OPS_AMBER};font-size:36px;font-weight:800;">
                        {confidence * 100:.0f}%
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

        # Timeline line chart: current -> 3mo -> 1yr -> 5yr
        vals = [
            _safe(overall_fc.get("current")),
            _safe(overall_fc.get("short_term")),
            _safe(overall_fc.get("medium_term")),
            _safe(overall_fc.get("long_term")),
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=_HORIZON_LABELS,
            y=vals,
            mode="lines+markers",
            line=dict(color=OPS_CYAN, width=3),
            marker=dict(size=10, color=OPS_CYAN),
            name="Overall Score",
        ))
        # Threshold lines
        fig.add_hline(y=VIABLE_THRESHOLD, line_dash="dash",
                      line_color=OPS_AMBER, opacity=0.5,
                      annotation_text="Viable (60)")
        fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dash",
                      line_color=OPS_RED, opacity=0.5,
                      annotation_text="Critical (30)")
        _plotly_dark_layout(fig, "Overall Score Trajectory", height=340)
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True, key="temp_overview_timeline")

    except Exception as exc:
        logger.error("Temporal overview error: %s", exc)
        st.error("Failed to render temporal overview.")


# ===================================================================
# B. DOMAIN TREND LINES
# ===================================================================

def _render_domain_trends(outlook: dict):
    """Multi-line chart per domain with uncertainty bands for overall."""
    try:
        _section_header("DOMAIN TREND LINES", "Projected score trajectories across all domains")

        domain_fc = outlook.get("domain_forecasts", {})
        overall_fc = outlook.get("overall_forecast", {})

        fig = go.Figure()

        # One line per domain
        for domain, fc in domain_fc.items():
            vals = [
                _safe(fc.get("current")),
                _safe(fc.get("short_term", {}).get("value") if isinstance(fc.get("short_term"), dict) else 0),
                _safe(fc.get("medium_term", {}).get("value") if isinstance(fc.get("medium_term"), dict) else 0),
                _safe(fc.get("long_term", {}).get("value") if isinstance(fc.get("long_term"), dict) else 0),
            ]
            fig.add_trace(go.Scatter(
                x=_HORIZON_LABELS,
                y=vals,
                mode="lines+markers",
                name=_domain_name(domain),
                line=dict(color=_domain_color(domain), width=2),
                marker=dict(size=6),
            ))

        # Uncertainty band for overall (P5-P95 approximation)
        overall_vals = [
            _safe(overall_fc.get("current")),
            _safe(overall_fc.get("short_term")),
            _safe(overall_fc.get("medium_term")),
            _safe(overall_fc.get("long_term")),
        ]

        # Compute approximate uncertainty bounds from domain forecasts
        unc_margins = [0, 3, 8, 18]  # growing uncertainty
        upper = [min(100, v + m) for v, m in zip(overall_vals, unc_margins)]
        lower = [max(0, v - m) for v, m in zip(overall_vals, unc_margins)]

        fig.add_trace(go.Scatter(
            x=_HORIZON_LABELS + _HORIZON_LABELS[::-1],
            y=upper + lower[::-1],
            fill="toself",
            fillcolor="rgba(0,240,255,0.08)",
            line=dict(color="rgba(0,0,0,0)"),
            name="Overall P5-P95",
            showlegend=True,
        ))

        # Threshold lines
        fig.add_hline(y=VIABLE_THRESHOLD, line_dash="dot",
                      line_color=OPS_AMBER, opacity=0.35)
        fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dot",
                      line_color=OPS_RED, opacity=0.35)

        _plotly_dark_layout(fig, "Domain Score Projections", height=480)
        fig.update_yaxes(range=[0, 100], title="Score")
        fig.update_xaxes(title="Time Horizon")
        st.plotly_chart(fig, use_container_width=True, key="temp_domain_trends")

    except Exception as exc:
        logger.error("Domain trends error: %s", exc)
        st.error("Failed to render domain trend lines.")


# ===================================================================
# C. EARLY WARNING SYSTEM
# ===================================================================

def _render_early_warnings(warnings: list):
    """List early warnings with severity styling."""
    try:
        _section_header("EARLY WARNING SYSTEM", "Detected risks requiring attention")

        if not warnings:
            st.info("No early warnings detected -- all domains within safe parameters.")
            return

        severity_styles = {
            "CRITICAL": (OPS_RED, "&#9888;"),       # warning sign
            "HIGH": (OPS_AMBER, "&#9888;"),
            "MODERATE": ("#eedd44", "&#9432;"),      # info circle
        }

        for w in warnings:
            sev = w.get("severity", "MODERATE")
            color, icon = severity_styles.get(sev, (OPS_TEXT_DIM, "&#8226;"))
            domain = w.get("domain", "unknown")
            msg = html_module.escape(w.get("message", ""))
            action = html_module.escape(w.get("recommended_action", ""))
            horizon = w.get("horizon", "")

            st.markdown(
                f"""<div style="background:{OPS_PANEL};border-left:4px solid {color};
                            border-radius:0 10px 10px 0;padding:14px 18px;margin:8px 0;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span style="color:{color};font-size:20px;">{icon}</span>
                        <span style="color:{color};font-weight:700;font-size:14px;text-transform:uppercase;">
                            {sev}
                        </span>
                        <span style="color:{OPS_TEXT_DIM};font-size:12px;margin-left:auto;">
                            {_domain_name(domain)} &middot; {horizon}
                        </span>
                    </div>
                    <div style="color:{OPS_TEXT};font-size:13px;margin-top:8px;">{msg}</div>
                    <div style="color:{OPS_TEXT_DIM};font-size:12px;margin-top:6px;font-style:italic;">
                        Recommended: {action}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    except Exception as exc:
        logger.error("Early warnings error: %s", exc)
        st.error("Failed to render early warning system.")


# ===================================================================
# D. SCENARIO COMPARISON TIMELINE
# ===================================================================

def _render_scenario_comparison(scores: dict):
    """Run 3 key scenarios and show timeline comparison."""
    try:
        _section_header("SCENARIO COMPARISON TIMELINE", "What-if projections for key events")

        predefined = get_predefined_scenarios()
        scenario_map = {s["name"]: s for s in predefined}

        # Pick 3 key scenarios
        target_names = ["Major Earthquake (M7)", "Severe Drought", "Green Energy Investment"]
        selected = [scenario_map[n] for n in target_names if n in scenario_map]

        if not selected:
            st.warning("No predefined scenarios available.")
            return

        fig = go.Figure()

        # Baseline line (current scores, no scenario)
        baseline_overall = sum(scores.values()) / max(len(scores), 1)
        max_duration = max(s.get("duration_years", 3) for s in selected)
        baseline_years = list(range(max_duration + 1))
        fig.add_trace(go.Scatter(
            x=baseline_years,
            y=[baseline_overall] * len(baseline_years),
            mode="lines",
            name="Baseline",
            line=dict(color=OPS_TEXT_DIM, width=2, dash="dash"),
        ))

        scenario_colors = [OPS_RED, OPS_AMBER, OPS_GREEN, OPS_BLUE, OPS_PURPLE]

        for idx, scenario in enumerate(selected):
            result = run_scenario_wargame(scores, scenario)
            timeline = result.get("timeline", [])
            years = [t["year"] for t in timeline]
            overalls = [t["overall"] for t in timeline]
            color = scenario_colors[idx % len(scenario_colors)]

            fig.add_trace(go.Scatter(
                x=years,
                y=overalls,
                mode="lines+markers",
                name=scenario["name"],
                line=dict(color=color, width=2),
                marker=dict(size=6),
            ))

        # Thresholds
        fig.add_hline(y=VIABLE_THRESHOLD, line_dash="dot",
                      line_color=OPS_AMBER, opacity=0.35)
        fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dot",
                      line_color=OPS_RED, opacity=0.35)

        _plotly_dark_layout(fig, "Scenario Impact Timelines", height=440)
        fig.update_xaxes(title="Year", dtick=1)
        fig.update_yaxes(title="Overall Score", range=[0, 100])
        st.plotly_chart(fig, use_container_width=True, key="temp_scenario_timelines")

        # Narrative summaries
        with st.expander("Scenario narratives", expanded=False):
            for scenario in selected:
                result = run_scenario_wargame(scores, scenario)
                narrative = generate_wargame_narrative(result)
                st.markdown(
                    f"""<div style="background:{OPS_PANEL};border-radius:8px;padding:12px 16px;margin:6px 0;">
                        <div style="color:{OPS_CYAN};font-weight:600;font-size:13px;">{scenario['name']}</div>
                        <div style="color:{OPS_TEXT_DIM};font-size:12px;margin-top:4px;">{narrative}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    except Exception as exc:
        logger.error("Scenario comparison error: %s", exc)
        st.error("Failed to render scenario comparison timeline.")


# ===================================================================
# E. DOMAIN VELOCITY MATRIX
# ===================================================================

def _render_velocity_matrix(outlook: dict):
    """Styled HTML table showing domain trends and projections."""
    try:
        _section_header("DOMAIN VELOCITY MATRIX", "Annual trends and 5-year projections per domain")

        domain_fc = outlook.get("domain_forecasts", {})
        if not domain_fc:
            st.info("No forecast data available.")
            return

        rows_html = ""
        for domain, fc in domain_fc.items():
            current = _safe(fc.get("current"))
            annual = _safe(fc.get("annual_trend"))
            long_val = _safe(fc.get("long_term", {}).get("value") if isinstance(fc.get("long_term"), dict) else 0)
            direction = fc.get("trend_direction", "STABLE")

            # Arrow and color for direction
            if direction == "IMPROVING":
                arrow = "&#9650;"
                dir_color = OPS_GREEN
            elif direction == "DECLINING":
                arrow = "&#9660;"
                dir_color = OPS_AMBER
            elif direction == "CRITICAL_DECLINE":
                arrow = "&#9660;&#9660;"
                dir_color = OPS_RED
            else:
                arrow = "&#9644;"
                dir_color = OPS_TEXT_DIM

            # Score color
            score_color = OPS_GREEN if current >= 70 else OPS_CYAN if current >= 50 else OPS_AMBER if current >= 30 else OPS_RED

            # Long-term score color
            lt_color = OPS_GREEN if long_val >= 70 else OPS_CYAN if long_val >= 50 else OPS_AMBER if long_val >= 30 else OPS_RED

            name = _domain_name(domain)
            d_color = _domain_color(domain)

            rows_html += f"""
            <tr style="border-bottom:1px solid rgba(90,112,144,0.15);">
                <td style="padding:10px 14px;">
                    <span style="color:{d_color};font-weight:600;">{name}</span>
                </td>
                <td style="padding:10px 14px;text-align:center;">
                    <span style="color:{score_color};font-weight:700;font-size:16px;">{current:.1f}</span>
                </td>
                <td style="padding:10px 14px;text-align:center;">
                    <span style="color:{dir_color};font-size:16px;">{arrow}</span>
                    <span style="color:{OPS_TEXT_DIM};font-size:12px;margin-left:4px;">
                        {annual:+.2f}/yr
                    </span>
                </td>
                <td style="padding:10px 14px;text-align:center;">
                    <span style="color:{lt_color};font-weight:700;font-size:16px;">{long_val:.1f}</span>
                </td>
                <td style="padding:10px 14px;text-align:center;">
                    <span style="color:{dir_color};font-weight:600;font-size:12px;
                                 background:rgba({",".join(_hex_to_rgb(dir_color))},0.15);
                                 padding:3px 10px;border-radius:12px;">
                        {direction}
                    </span>
                </td>
            </tr>"""

        st.markdown(
            f"""<div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;background:{OPS_PANEL};
                          border-radius:12px;overflow:hidden;">
                <thead>
                    <tr style="background:rgba(0,240,255,0.06);">
                        <th style="padding:12px 14px;text-align:left;color:{OPS_CYAN};
                                   font-size:12px;text-transform:uppercase;letter-spacing:1px;">Domain</th>
                        <th style="padding:12px 14px;text-align:center;color:{OPS_CYAN};
                                   font-size:12px;text-transform:uppercase;letter-spacing:1px;">Current</th>
                        <th style="padding:12px 14px;text-align:center;color:{OPS_CYAN};
                                   font-size:12px;text-transform:uppercase;letter-spacing:1px;">Annual Trend</th>
                        <th style="padding:12px 14px;text-align:center;color:{OPS_CYAN};
                                   font-size:12px;text-transform:uppercase;letter-spacing:1px;">5yr Projection</th>
                        <th style="padding:12px 14px;text-align:center;color:{OPS_CYAN};
                                   font-size:12px;text-transform:uppercase;letter-spacing:1px;">Classification</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            </div>""",
            unsafe_allow_html=True,
        )

    except Exception as exc:
        logger.error("Velocity matrix error: %s", exc)
        st.error("Failed to render domain velocity matrix.")


def _hex_to_rgb(hex_color: str) -> list:
    """Convert hex color to list of R,G,B strings."""
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return [str(int(h[i:i + 2], 16)) for i in (0, 2, 4)]
    except (ValueError, IndexError):
        return ["0", "240", "255"]


# ===================================================================
# F. INFLECTION POINT RADAR
# ===================================================================

def _render_inflection_radar(outlook: dict):
    """Bar chart showing domains near threshold crossings."""
    try:
        _section_header("INFLECTION POINT RADAR", "Domains approaching critical threshold crossings")

        domain_fc = outlook.get("domain_forecasts", {})
        inflection_points = outlook.get("inflection_points", [])

        # Calculate distance to each threshold for every domain
        near_threshold = []
        for domain, fc in domain_fc.items():
            current = _safe(fc.get("current"))
            long_val = _safe(fc.get("long_term", {}).get("value") if isinstance(fc.get("long_term"), dict) else 0)

            # Distance to viable threshold (60)
            dist_viable = current - VIABLE_THRESHOLD
            # Distance to critical threshold (30)
            dist_critical = current - CRITICAL_THRESHOLD

            # Only include domains within 25 points of a threshold
            min_dist = min(abs(dist_viable), abs(dist_critical))
            if min_dist <= 25:
                threshold_name = "Viable (60)" if abs(dist_viable) < abs(dist_critical) else "Critical (30)"
                threshold_val = VIABLE_THRESHOLD if abs(dist_viable) < abs(dist_critical) else CRITICAL_THRESHOLD
                distance = dist_viable if abs(dist_viable) < abs(dist_critical) else dist_critical
                near_threshold.append({
                    "domain": domain,
                    "distance": distance,
                    "threshold": threshold_name,
                    "threshold_val": threshold_val,
                    "current": current,
                    "projected": long_val,
                })

        if not near_threshold:
            st.info("No domains are near threshold crossings.")
            return

        # Sort by absolute distance (closest first)
        near_threshold.sort(key=lambda x: abs(x["distance"]))

        # Build bar chart
        fig = go.Figure()

        names = [_domain_name(nt["domain"]) for nt in near_threshold]
        distances = [nt["distance"] for nt in near_threshold]
        colors = [
            OPS_RED if d < 0 else OPS_GREEN if d > 15 else OPS_AMBER
            for d in distances
        ]
        threshold_labels = [nt["threshold"] for nt in near_threshold]

        fig.add_trace(go.Bar(
            x=names,
            y=distances,
            marker_color=colors,
            text=[f"{d:+.1f}" for d in distances],
            textposition="outside",
            textfont=dict(color=OPS_TEXT, size=11),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Distance to threshold: %{y:.1f}<br>"
                "<extra></extra>"
            ),
        ))

        # Zero line = threshold
        fig.add_hline(y=0, line_color=OPS_CYAN, line_width=2, opacity=0.6)

        _plotly_dark_layout(fig, "Distance to Nearest Threshold", height=380)
        fig.update_yaxes(title="Points Above/Below Threshold")
        fig.update_xaxes(title="Domain")
        st.plotly_chart(fig, use_container_width=True, key="temp_inflection")

        # Inflection point detail list
        if inflection_points:
            st.markdown(
                f'<div style="color:{OPS_TEXT_DIM};font-size:12px;margin-top:8px;">'
                f'Detected {len(inflection_points)} projected threshold crossing(s):</div>',
                unsafe_allow_html=True,
            )
            for ip in inflection_points[:6]:
                direction_icon = "&#9660;" if ip["direction"] == "below" else "&#9650;"
                ip_color = OPS_RED if ip["direction"] == "below" else OPS_GREEN
                st.markdown(
                    f"""<div style="background:{OPS_PANEL};border-left:3px solid {ip_color};
                                padding:8px 14px;margin:4px 0;border-radius:0 8px 8px 0;font-size:12px;">
                        <span style="color:{ip_color};">{direction_icon}</span>
                        <span style="color:{OPS_TEXT};font-weight:600;">
                            {_domain_name(ip['domain'])}
                        </span>
                        <span style="color:{OPS_TEXT_DIM};">
                            crossing {ip['threshold']} threshold {ip['direction']}
                            in {ip['horizon'].lower()}-term &rarr; projected {ip['projected_value']:.1f}
                        </span>
                    </div>""",
                    unsafe_allow_html=True,
                )

    except Exception as exc:
        logger.error("Inflection radar error: %s", exc)
        st.error("Failed to render inflection point radar.")


# ===================================================================
# G. OPPORTUNITY WINDOWS
# ===================================================================

def _render_opportunity_windows(opportunities: list):
    """List time-limited opportunities from predictive engine."""
    try:
        _section_header("OPPORTUNITY WINDOWS", "Time-limited action windows detected")

        if not opportunities:
            st.info("No time-limited opportunities identified at this time.")
            return

        window_colors = {
            "NOW": OPS_GREEN,
            "3_MONTHS": OPS_CYAN,
            "1_YEAR": OPS_BLUE,
        }
        window_labels = {
            "NOW": "ACT NOW",
            "3_MONTHS": "3-MONTH WINDOW",
            "1_YEAR": "1-YEAR WINDOW",
        }

        for opp in opportunities[:8]:
            window = opp.get("window", "1_YEAR")
            w_color = window_colors.get(window, OPS_TEXT_DIM)
            w_label = window_labels.get(window, window)
            domain = opp.get("domain", "unknown")
            conf = opp.get("confidence", 0)
            opportunity_text = html_module.escape(opp.get("opportunity", ""))
            action_text = html_module.escape(opp.get("action", ""))

            st.markdown(
                f"""<div style="background:{OPS_PANEL};border-radius:10px;padding:14px 18px;
                            margin:8px 0;border:1px solid rgba({",".join(_hex_to_rgb(w_color))},0.25);">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                        <span style="color:{w_color};font-weight:700;font-size:11px;
                                     background:rgba({",".join(_hex_to_rgb(w_color))},0.15);
                                     padding:3px 10px;border-radius:12px;letter-spacing:1px;">
                            {w_label}
                        </span>
                        <span style="color:{OPS_TEXT_DIM};font-size:12px;">
                            {_domain_name(domain)}
                        </span>
                        <span style="color:{OPS_TEXT_DIM};font-size:11px;margin-left:auto;">
                            Confidence: {conf:.0%}
                        </span>
                    </div>
                    <div style="color:{OPS_TEXT};font-size:13px;">{opportunity_text}</div>
                    <div style="color:{OPS_TEXT_DIM};font-size:12px;margin-top:6px;font-style:italic;">
                        Action: {action_text}
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

    except Exception as exc:
        logger.error("Opportunity windows error: %s", exc)
        st.error("Failed to render opportunity windows.")


# ===================================================================
# H. INTERVENTION SIMULATOR
# ===================================================================

def _render_intervention_simulator(scores: dict, outlook: dict):
    """Interactive slider to boost a domain and compare with baseline."""
    try:
        _section_header("INTERVENTION SIMULATOR", "Model the impact of targeted domain investment")

        domain_list = list(INTELLIGENCE_DOMAINS.keys())
        domain_display = [_domain_name(d) for d in domain_list]

        c1, c2 = st.columns([1.5, 1])
        with c1:
            selected_idx = st.selectbox(
                "Select domain to boost",
                range(len(domain_list)),
                format_func=lambda i: domain_display[i],
                key="temp_interv_domain",
            )
        with c2:
            boost_amount = st.slider(
                "Boost amount (points)",
                min_value=5,
                max_value=50,
                value=20,
                step=5,
                key="temp_interv_boost",
            )

        selected_domain = domain_list[selected_idx]

        # Build intervention scenario
        intervention = {
            "name": f"Boost {_domain_name(selected_domain)}",
            "description": f"+{boost_amount} investment in {_domain_name(selected_domain)}",
            "events": [{"domain": selected_domain, "impact": boost_amount, "timing": "immediate"}],
            "duration_years": 5,
        }

        result = run_scenario_wargame(scores, intervention)
        timeline = result.get("timeline", [])

        if not timeline:
            st.warning("Could not simulate intervention.")
            return

        fig = go.Figure()

        # Baseline (flat from current overall)
        baseline_overall = sum(scores.values()) / max(len(scores), 1)
        years = [t["year"] for t in timeline]

        fig.add_trace(go.Scatter(
            x=years,
            y=[baseline_overall] * len(years),
            mode="lines",
            name="Baseline",
            line=dict(color=OPS_TEXT_DIM, width=2, dash="dash"),
        ))

        # Intervention timeline
        fig.add_trace(go.Scatter(
            x=years,
            y=[t["overall"] for t in timeline],
            mode="lines+markers",
            name=f"+{boost_amount} {_domain_name(selected_domain)}",
            line=dict(color=_domain_color(selected_domain), width=3),
            marker=dict(size=8),
        ))

        # Thresholds
        fig.add_hline(y=VIABLE_THRESHOLD, line_dash="dot",
                      line_color=OPS_AMBER, opacity=0.3)
        fig.add_hline(y=CRITICAL_THRESHOLD, line_dash="dot",
                      line_color=OPS_RED, opacity=0.3)

        _plotly_dark_layout(fig, f"Intervention: +{boost_amount} to {_domain_name(selected_domain)}", height=380)
        fig.update_xaxes(title="Year", dtick=1)
        fig.update_yaxes(title="Overall Score", range=[0, 100])
        st.plotly_chart(fig, use_container_width=True, key="temp_intervention_chart")

        # Impact summary
        final_overall = result.get("final_overall", 0)
        overall_delta = result.get("overall_delta", 0)
        delta_map = result.get("delta_from_baseline", {})

        delta_sign = "+" if overall_delta > 0 else ""
        delta_color = OPS_GREEN if overall_delta > 0 else OPS_RED if overall_delta < -1 else OPS_AMBER

        st.markdown(
            f"""<div style="background:{OPS_PANEL};border-radius:10px;padding:16px 20px;margin-top:8px;">
                <div style="display:flex;gap:30px;flex-wrap:wrap;">
                    <div>
                        <div style="color:{OPS_TEXT_DIM};font-size:11px;text-transform:uppercase;">Final Overall</div>
                        <div style="color:{OPS_CYAN};font-size:24px;font-weight:700;">{final_overall:.1f}</div>
                    </div>
                    <div>
                        <div style="color:{OPS_TEXT_DIM};font-size:11px;text-transform:uppercase;">Overall Delta</div>
                        <div style="color:{delta_color};font-size:24px;font-weight:700;">{delta_sign}{overall_delta:.1f}</div>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        # Per-domain delta breakdown
        with st.expander("Per-domain impact breakdown", expanded=False):
            sorted_deltas = sorted(delta_map.items(), key=lambda kv: kv[1], reverse=True)
            for domain, delta in sorted_deltas:
                d_color = OPS_GREEN if delta > 0 else OPS_RED if delta < 0 else OPS_TEXT_DIM
                d_sign = "+" if delta > 0 else ""
                bar_width = min(100, abs(delta) * 3)
                st.markdown(
                    f"""<div style="display:flex;align-items:center;gap:10px;padding:4px 0;">
                        <div style="width:160px;color:{OPS_TEXT};font-size:12px;">{_domain_name(domain)}</div>
                        <div style="flex:1;background:rgba(90,112,144,0.1);border-radius:4px;height:14px;position:relative;">
                            <div style="width:{bar_width}%;background:{d_color};height:100%;border-radius:4px;
                                        opacity:0.7;"></div>
                        </div>
                        <div style="width:60px;text-align:right;color:{d_color};font-size:12px;font-weight:600;">
                            {d_sign}{delta:.1f}
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    except Exception as exc:
        logger.error("Intervention simulator error: %s", exc)
        st.error("Failed to render intervention simulator.")


# ===================================================================
# MAIN ENTRY POINT
# ===================================================================

def render_temporal_dashboard():
    """Main entry point for the Temporal Analysis Dashboard page."""

    # Inject page-level dark theme
    st.markdown(
        f"""<style>
        .stApp {{ background-color: {OPS_BG}; }}
        .stMarkdown, .stText {{ color: {OPS_TEXT}; }}
        [data-testid="stSidebar"] {{ background-color: {OPS_PANEL}; }}
        </style>""",
        unsafe_allow_html=True,
    )

    # Header banner
    st.markdown(
        f"""
        <div style="background:linear-gradient(135deg, {OPS_PANEL} 0%, rgba(0,240,255,0.06) 100%);
                    border:1px solid rgba(0,240,255,0.12);border-radius:16px;
                    padding:30px 36px;margin-bottom:20px;">
            <div style="color:{OPS_CYAN};font-size:28px;font-weight:800;letter-spacing:2px;">
                TEMPORAL ANALYSIS DASHBOARD
            </div>
            <div style="color:{OPS_TEXT_DIM};font-size:14px;margin-top:6px;">
                Time-based intelligence projections &middot; Trend analysis &middot; Scenario modelling
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Location context
    init_location_context()
    with st.expander("Location Selection", expanded=not has_location()):
        render_location_selector(key_prefix="temp_loc")

    if not has_location():
        st.info("Set a location above to begin temporal analysis.")
        return

    loc = get_location()
    lat, lon = loc["lat"], loc["lon"]
    short_name = get_short_name()

    st.markdown(
        f"""<div style="color:{OPS_TEXT_DIM};font-size:13px;margin-bottom:16px;">
            Analysing: <span style="color:{OPS_CYAN};font-weight:600;">{short_name}</span>
            &nbsp;({lat:.4f}, {lon:.4f})
        </div>""",
        unsafe_allow_html=True,
    )

    # Fetch hub data
    with st.spinner("Fetching intelligence data..."):
        try:
            hub = get_hub_data(lat, lon)
        except Exception as exc:
            logger.error("Data hub fetch failed: %s", exc)
            st.error("Failed to fetch intelligence data. Please try again.")
            return

    scores = hub.get("scores", {})
    details = hub.get("details", {})
    raw_data = hub.get("raw_data", {})

    if not scores:
        st.warning("No domain scores available for this location.")
        return

    # Compute analytics for predictive engine
    try:
        analytics = compute_advanced_analytics(scores, details, raw_data)
    except Exception as exc:
        logger.warning("Advanced analytics computation failed: %s", exc)
        analytics = {}

    # Run predictive engine
    try:
        outlook = compute_predictive_outlook(scores, details, analytics, raw_data)
    except Exception as exc:
        logger.error("Predictive outlook failed: %s", exc)
        st.error("Failed to compute predictive outlook.")
        return

    domain_fc = outlook.get("domain_forecasts", {})

    # Generate early warnings
    try:
        warnings = generate_early_warnings(domain_fc, scores)
    except Exception as exc:
        logger.warning("Early warnings generation failed: %s", exc)
        warnings = []

    # Compute opportunity windows
    try:
        opportunities = compute_opportunity_windows(domain_fc, scores)
    except Exception as exc:
        logger.warning("Opportunity windows computation failed: %s", exc)
        opportunities = []

    # Prediction narrative
    try:
        narrative = generate_prediction_narrative(outlook)
    except Exception as exc:
        logger.warning("Prediction narrative failed: %s", exc)
        narrative = ""

    if narrative:
        st.markdown(
            f"""<div style="background:{OPS_PANEL};border-radius:12px;padding:18px 22px;
                        margin-bottom:20px;border:1px solid rgba(0,240,255,0.08);">
                <div style="color:{OPS_CYAN};font-size:12px;text-transform:uppercase;
                            letter-spacing:1px;margin-bottom:8px;">Predictive Narrative</div>
                <div style="color:{OPS_TEXT};font-size:13px;line-height:1.7;">{narrative}</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Render all sections
    _render_temporal_overview(hub, outlook)

    _render_domain_trends(outlook)

    _render_early_warnings(warnings)

    _render_scenario_comparison(scores)

    _render_velocity_matrix(outlook)

    _render_inflection_radar(outlook)

    _render_opportunity_windows(opportunities)

    _render_intervention_simulator(scores, outlook)

    # Footer
    st.markdown(
        f"""<div style="text-align:center;color:{OPS_TEXT_DIM};font-size:11px;
                    margin-top:40px;padding:16px;border-top:1px solid rgba(90,112,144,0.15);">
            TerraScout AI &middot; Temporal Analysis Engine &middot;
            Projections are model-based estimates and should be validated with domain expertise.
        </div>""",
        unsafe_allow_html=True,
    )
