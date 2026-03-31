"""
Palantir Visualizations — Premium Plotly chart components for TerraScout AI.

1. Radar Spider Chart      — multi-domain comparison overlay
2. Sankey Influence Diagram — domain-to-domain influence flows
3. Parallel Coordinates     — multi-domain simultaneous comparison
4. Waterfall Decomposition  — score buildup from mean to each domain
5. Sunburst Hierarchy       — domain > sub-indicators drill-down

All functions return Plotly Figure objects for embedding via st.plotly_chart.
"""

import logging
import math

try:
    import plotly.graph_objects as go
except ImportError:
    go = None

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PALETTE
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

_DOMAINS = [
    "habitability", "agriculture", "ecology", "hazard_safety",
    "water_resources", "infrastructure", "climate_comfort",
    "economic_potential", "air_environment", "geological_stability",
]

_DOMAIN_LABELS = {
    "habitability": "Habitability",
    "agriculture": "Agriculture",
    "ecology": "Ecology",
    "hazard_safety": "Hazard Safety",
    "water_resources": "Water",
    "infrastructure": "Infra",
    "climate_comfort": "Climate",
    "economic_potential": "Economic",
    "air_environment": "Air",
    "geological_stability": "Geology",
}

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


# ═══════════════════════════════════════════════════════════════════════════
# 1. RADAR SPIDER CHART
# ═══════════════════════════════════════════════════════════════════════════

def create_radar_chart(scores, title="Domain Assessment Radar", height=400,
                       show_fill=True, comparison_scores=None):
    """Create a radar/spider chart showing all domain scores.

    Args:
        scores: dict domain->score
        title: chart title
        height: chart height in px
        show_fill: whether to fill the radar area
        comparison_scores: optional second dict for overlay comparison

    Returns: plotly Figure
    """
    if go is None:
        return None

    try:
        categories = [_DOMAIN_LABELS.get(d, d) for d in _DOMAINS]
        values = [scores.get(d, 0) for d in _DOMAINS]
        values = [v if isinstance(v, (int, float)) else 0 for v in values]

        # Close the polygon
        categories_closed = categories + [categories[0]]
        values_closed = values + [values[0]]

        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill="toself" if show_fill else "none",
            fillcolor="rgba(0, 240, 255, 0.08)",
            line=dict(color=_CYAN, width=2),
            marker=dict(size=6, color=_CYAN),
            name="Current",
            hovertemplate="%{theta}: %{r:.0f}<extra></extra>",
        ))

        if comparison_scores:
            comp_values = [comparison_scores.get(d, 0) for d in _DOMAINS]
            comp_values = [v if isinstance(v, (int, float)) else 0 for v in comp_values]
            comp_closed = comp_values + [comp_values[0]]
            fig.add_trace(go.Scatterpolar(
                r=comp_closed,
                theta=categories_closed,
                fill="toself" if show_fill else "none",
                fillcolor="rgba(170, 85, 255, 0.06)",
                line=dict(color=_PURPLE, width=2, dash="dash"),
                marker=dict(size=5, color=_PURPLE),
                name="Comparison",
                hovertemplate="%{theta}: %{r:.0f}<extra></extra>",
            ))

        fig.update_layout(
            polar=dict(
                bgcolor="rgba(5,5,16,0.6)",
                radialaxis=dict(
                    visible=True, range=[0, 100],
                    gridcolor="rgba(255,255,255,0.05)",
                    tickfont=dict(size=8, color=_DIM),
                    linecolor="rgba(255,255,255,0.05)",
                ),
                angularaxis=dict(
                    tickfont=dict(size=9, color=_TEXT),
                    gridcolor="rgba(255,255,255,0.05)",
                    linecolor="rgba(255,255,255,0.08)",
                ),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
            height=height,
            margin=dict(l=60, r=60, t=40, b=40),
            showlegend=comparison_scores is not None,
            legend=dict(font=dict(size=9, color=_DIM), x=0.5, y=-0.1,
                        xanchor="center", orientation="h"),
        )

        return fig
    except Exception as exc:
        logger.warning("Radar chart creation failed: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 2. SANKEY INFLUENCE DIAGRAM
# ═══════════════════════════════════════════════════════════════════════════

_INFLUENCE_FLOWS = {
    "water_resources": ["agriculture", "ecology", "habitability"],
    "climate_comfort": ["agriculture", "habitability", "ecology"],
    "hazard_safety": ["infrastructure", "habitability", "economic_potential"],
    "geological_stability": ["infrastructure", "hazard_safety"],
    "infrastructure": ["economic_potential", "habitability"],
    "air_environment": ["habitability", "ecology"],
    "ecology": ["water_resources", "air_environment"],
    "agriculture": ["economic_potential"],
    "economic_potential": ["infrastructure"],
}


def create_sankey_diagram(scores, height=420):
    """Create a Sankey diagram showing domain influence flows.

    Flow thickness = source_score * weight_factor.

    Returns: plotly Figure
    """
    if go is None:
        return None

    try:
        # Node indices
        idx = {d: i for i, d in enumerate(_DOMAINS)}
        labels = [_DOMAIN_LABELS.get(d, d) for d in _DOMAINS]
        colors = [_DOMAIN_COLORS.get(d, _CYAN) for d in _DOMAINS]

        sources = []
        targets = []
        values = []
        link_colors = []

        for src, tgts in _INFLUENCE_FLOWS.items():
            src_score = scores.get(src, 50)
            if not isinstance(src_score, (int, float)):
                src_score = 50
            src_idx = idx.get(src)
            if src_idx is None:
                continue
            for tgt in tgts:
                tgt_idx = idx.get(tgt)
                if tgt_idx is None:
                    continue
                flow = max(1, src_score / (len(tgts) * 2))
                sources.append(src_idx)
                targets.append(tgt_idx)
                values.append(round(flow, 1))
                c = _DOMAIN_COLORS.get(src, _CYAN)
                # Semi-transparent link
                link_colors.append(c)

        # Convert hex to rgba for links
        rgba_links = []
        for c in link_colors:
            if c.startswith("#"):
                r = int(c[1:3], 16)
                g = int(c[3:5], 16)
                b = int(c[5:7], 16)
                rgba_links.append(f"rgba({r},{g},{b},0.25)")
            else:
                rgba_links.append(c)

        fig = go.Figure(go.Sankey(
            node=dict(
                pad=20,
                thickness=25,
                line=dict(color="rgba(255,255,255,0.1)", width=1),
                label=labels,
                color=colors,
                hovertemplate="%{label}<br>Score: %{value:.0f}<extra></extra>",
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=rgba_links,
                hovertemplate="%{source.label} → %{target.label}<br>Flow: %{value:.1f}<extra></extra>",
            ),
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,5,16,0.6)",
            font=dict(color=_TEXT, size=10, family="JetBrains Mono, monospace"),
            height=height,
            margin=dict(l=20, r=20, t=20, b=20),
        )

        return fig
    except Exception as exc:
        logger.warning("Sankey diagram creation failed: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 3. PARALLEL COORDINATES
# ═══════════════════════════════════════════════════════════════════════════

def create_parallel_coordinates(scores, analytics=None, height=350):
    """Create parallel coordinates plot for multi-domain comparison.

    Each "line" represents a perspective (raw, safety-adjusted, etc.)

    Returns: plotly Figure
    """
    if go is None:
        return None

    try:
        raw_vals = [scores.get(d, 50) for d in _DOMAINS]
        raw_vals = [v if isinstance(v, (int, float)) else 50 for v in raw_vals]

        safety = scores.get("hazard_safety", 50) / 100 if isinstance(scores.get("hazard_safety"), (int, float)) else 0.5
        adjusted_vals = [v * (0.7 + 0.3 * safety) for v in raw_vals]
        inverted_vals = [100 - v for v in raw_vals]

        overall = sum(raw_vals) / len(raw_vals) if raw_vals else 50

        dimensions = []
        for i, d in enumerate(_DOMAINS):
            dimensions.append(dict(
                label=_DOMAIN_LABELS.get(d, d),
                values=[raw_vals[i], adjusted_vals[i], inverted_vals[i]],
                range=[0, 100],
            ))

        fig = go.Figure(go.Parcoords(
            line=dict(
                color=[overall, overall * safety, 100 - overall],
                colorscale=[[0, _RED], [0.3, _AMBER], [0.6, _CYAN], [1, _GREEN]],
                showscale=True,
                colorbar=dict(title=dict(text="Score", font=dict(size=9, color=_DIM)),
                              tickfont=dict(size=8, color=_DIM)),
            ),
            dimensions=dimensions,
            labelfont=dict(size=9, color=_TEXT),
            tickfont=dict(size=8, color=_DIM),
            rangefont=dict(size=8, color=_DIM),
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,5,16,0.6)",
            font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
            height=height,
            margin=dict(l=80, r=40, t=30, b=30),
        )

        return fig
    except Exception as exc:
        logger.warning("Parallel coordinates creation failed: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 4. WATERFALL DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════════════

def create_waterfall_chart(scores, height=380):
    """Create waterfall chart showing score buildup from mean.

    Shows how each domain contributes above or below the mean,
    building up to the final overall score.

    Returns: plotly Figure
    """
    if go is None:
        return None

    try:
        vals = {}
        for d in _DOMAINS:
            v = scores.get(d, 50)
            vals[d] = v if isinstance(v, (int, float)) else 50

        all_vals = list(vals.values())
        mean = sum(all_vals) / len(all_vals) if all_vals else 50

        # Sort by deviation from mean
        sorted_domains = sorted(_DOMAINS, key=lambda d: vals[d] - mean, reverse=True)

        labels = ["Baseline"]
        measures = ["absolute"]
        values_list = [round(mean, 1)]
        colors = [_DIM]

        for d in sorted_domains:
            delta = vals[d] - mean
            labels.append(_DOMAIN_LABELS.get(d, d))
            measures.append("relative")
            values_list.append(round(delta / len(_DOMAINS), 1))
            if delta >= 10:
                colors.append(_GREEN)
            elif delta >= 0:
                colors.append("rgba(0,255,136,0.5)")
            elif delta >= -10:
                colors.append("rgba(255,170,0,0.5)")
            else:
                colors.append(_RED)

        labels.append("Overall")
        measures.append("total")
        overall = sum(all_vals) / len(all_vals) if all_vals else 50
        values_list.append(round(overall, 1))
        colors.append(_CYAN)

        fig = go.Figure(go.Waterfall(
            x=labels,
            y=values_list,
            measure=measures,
            connector=dict(line=dict(color="rgba(255,255,255,0.1)", width=1)),
            increasing=dict(marker=dict(color=_GREEN)),
            decreasing=dict(marker=dict(color=_RED)),
            totals=dict(marker=dict(color=_CYAN)),
            textposition="outside",
            textfont=dict(size=8, color=_TEXT),
            text=[f"{v:+.1f}" if m == "relative" else f"{v:.1f}" for v, m in zip(values_list, measures)],
            hovertemplate="%{x}<br>Value: %{y:.1f}<extra></extra>",
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,5,16,0.6)",
            font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
            height=height,
            margin=dict(l=50, r=20, t=30, b=80),
            xaxis=dict(tickangle=-40, tickfont=dict(size=8, color=_DIM),
                       gridcolor="rgba(255,255,255,0.03)"),
            yaxis=dict(title="Score", gridcolor="rgba(255,255,255,0.03)",
                       tickfont=dict(size=9, color=_DIM)),
            showlegend=False,
        )

        return fig
    except Exception as exc:
        logger.warning("Waterfall chart creation failed: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 5. SUNBURST HIERARCHY
# ═══════════════════════════════════════════════════════════════════════════

_DOMAIN_SUBCATEGORIES = {
    "habitability": ["Living Quality", "Services Access", "Safety"],
    "agriculture": ["Soil Quality", "Irrigation", "Climate Suitability"],
    "ecology": ["Biodiversity", "Habitat Health", "Conservation"],
    "hazard_safety": ["Seismic Risk", "Weather Risk", "Fire Risk"],
    "water_resources": ["Availability", "Quality", "Infrastructure"],
    "infrastructure": ["Transport", "Utilities", "Digital"],
    "climate_comfort": ["Temperature", "Humidity", "Precipitation"],
    "economic_potential": ["Market Access", "Resources", "Workforce"],
    "air_environment": ["PM2.5 Levels", "AQI Score", "Industrial Impact"],
    "geological_stability": ["Tectonic Activity", "Soil Stability", "Erosion"],
}


def create_sunburst_chart(scores, details=None, height=420):
    """Create sunburst chart with domain > sub-indicator hierarchy.

    Returns: plotly Figure
    """
    if go is None:
        return None

    try:
        ids = ["TerraScout"]
        labels = ["Overall"]
        parents = [""]
        values = []
        colors_list = [_CYAN]

        all_vals = [scores.get(d, 50) for d in _DOMAINS]
        all_vals = [v if isinstance(v, (int, float)) else 50 for v in all_vals]
        overall = sum(all_vals) / len(all_vals) if all_vals else 50
        values.append(round(overall, 1))

        for d in _DOMAINS:
            score = scores.get(d, 50)
            if not isinstance(score, (int, float)):
                score = 50
            domain_id = f"domain_{d}"
            ids.append(domain_id)
            labels.append(_DOMAIN_LABELS.get(d, d))
            parents.append("TerraScout")
            values.append(round(score, 1))
            colors_list.append(_DOMAIN_COLORS.get(d, _CYAN))

            # Sub-categories
            subcats = _DOMAIN_SUBCATEGORIES.get(d, [])
            det = details.get(d, {}) if isinstance(details, dict) else {}
            if not isinstance(det, dict):
                det = {}

            # Distribute score among subcategories with some variance
            det_vals = [v for v in det.values() if isinstance(v, (int, float))]
            for si, sub in enumerate(subcats):
                sub_id = f"{domain_id}_{si}"
                ids.append(sub_id)
                labels.append(sub)
                parents.append(domain_id)
                # Use detail values if available, else derive from main score
                if si < len(det_vals):
                    sv = det_vals[si]
                    # Normalize to 0-100 range
                    if abs(sv) > 100:
                        sv = min(max(sv / 10, 0), 100)
                    elif abs(sv) <= 1:
                        sv = sv * 100
                    sv = max(0, min(100, sv))
                else:
                    variance = (si - 1) * 5
                    sv = max(0, min(100, score + variance))
                values.append(round(sv, 1))
                colors_list.append(_DOMAIN_COLORS.get(d, _CYAN))

        fig = go.Figure(go.Sunburst(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            branchvalues="total" if False else "remainder",
            marker=dict(
                colors=colors_list,
                line=dict(width=1, color=_PANEL),
            ),
            textfont=dict(size=10, color=_TEXT),
            hovertemplate="<b>%{label}</b><br>Score: %{value:.0f}<extra></extra>",
            insidetextorientation="radial",
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
            height=height,
            margin=dict(l=10, r=10, t=10, b=10),
        )

        return fig
    except Exception as exc:
        logger.warning("Sunburst chart creation failed: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# BONUS: TRANSITION HEATMAP (for Markov Chain)
# ═══════════════════════════════════════════════════════════════════════════

def create_transition_heatmap(transition_matrix, states, height=280):
    """Create heatmap of Markov transition probabilities.

    Returns: plotly Figure
    """
    if go is None:
        return None

    try:
        fig = go.Figure(go.Heatmap(
            z=transition_matrix,
            x=states,
            y=states,
            colorscale=[[0, _PANEL], [0.3, "#1a2040"], [0.6, "rgba(68,136,255,0.53)"], [1, _CYAN]],
            showscale=True,
            colorbar=dict(title=dict(text="P", font=dict(size=9, color=_DIM)),
                          tickfont=dict(size=8, color=_DIM)),
            text=[[f"{v:.2f}" for v in row] for row in transition_matrix],
            texttemplate="%{text}",
            textfont=dict(size=10, color=_TEXT),
            hoverongaps=False,
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,5,16,0.6)",
            font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
            height=height,
            margin=dict(l=80, r=20, t=20, b=50),
            xaxis=dict(title="To State", tickfont=dict(size=9, color=_DIM)),
            yaxis=dict(title="From State", tickfont=dict(size=9, color=_DIM)),
        )

        return fig
    except Exception as exc:
        logger.warning("Transition heatmap creation failed: %s", exc)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# BONUS: PARETO FRONTIER SCATTER
# ═══════════════════════════════════════════════════════════════════════════

def create_pareto_scatter(pareto_result, height=350):
    """Create scatter plot showing Pareto-optimal vs dominated domains.

    Returns: plotly Figure
    """
    if go is None:
        return None

    try:
        fig = go.Figure()

        # Pareto-optimal domains
        optimal = pareto_result.get("pareto_optimal", [])
        dominated = pareto_result.get("dominated", [])

        if optimal:
            fig.add_trace(go.Scatter(
                x=[d["score"] for d in optimal],
                y=[i for i in range(len(optimal))],
                mode="markers+text",
                marker=dict(size=16, color=_GREEN, symbol="star",
                            line=dict(width=2, color="rgba(255,255,255,0.3)")),
                text=[d["label"][:8] for d in optimal],
                textposition="middle right",
                textfont=dict(size=9, color=_GREEN),
                name="Pareto Optimal",
                hovertext=[f"{d['label']}: {d['score']:.0f}" for d in optimal],
                hoverinfo="text",
            ))

        if dominated:
            fig.add_trace(go.Scatter(
                x=[d["score"] for d in dominated],
                y=[i + len(optimal) for i in range(len(dominated))],
                mode="markers+text",
                marker=dict(size=12, color=_RED, symbol="circle",
                            line=dict(width=1, color="rgba(255,255,255,0.2)")),
                text=[d["label"][:8] for d in dominated],
                textposition="middle right",
                textfont=dict(size=9, color=_RED),
                name="Dominated",
                hovertext=[f"{d['label']}: {d['score']:.0f} (dom. by {d['dominated_by']})"
                           for d in dominated],
                hoverinfo="text",
            ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,5,16,0.6)",
            font=dict(color=_DIM, size=10, family="JetBrains Mono, monospace"),
            height=height,
            margin=dict(l=40, r=20, t=30, b=30),
            xaxis=dict(title="Score", range=[0, 105], gridcolor="rgba(255,255,255,0.03)"),
            yaxis=dict(visible=False),
            legend=dict(font=dict(size=9, color=_DIM), x=0.5, y=-0.12,
                        xanchor="center", orientation="h"),
        )

        return fig
    except Exception as exc:
        logger.warning("Pareto scatter creation failed: %s", exc)
        return None
