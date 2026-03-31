"""
Palantir Charts V2 — Phase 4 premium Plotly visualizations for TerraScout AI.
3D Globe, Gauge Dashboard, Bullet Charts, Polar Bar, Ridgeline Plot.

All charts use a dark ops-center theme consistent with the Palantir aesthetic.
Every public function returns a ``go.Figure`` or ``None`` on any failure.
"""

import math
import logging

logger = logging.getLogger(__name__)

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    go = None
    make_subplots = None

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
_CYAN = "#00f0ff"
_GREEN = "#00ff88"
_RED = "#ff3344"
_AMBER = "#ffaa00"
_BLUE = "#4488ff"
_PURPLE = "#aa44ff"
_PANEL = "#0a0a18"
_TEXT = "#e0e0e0"
_DIM = "#6a7a8a"

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
_DOMAINS = list(_DOMAIN_COLORS.keys())
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

# ---------------------------------------------------------------------------
# Shared layout helper
# ---------------------------------------------------------------------------

def _dark_layout(**overrides):
    """Return a base dark-theme layout dict, merged with *overrides*."""
    base = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=_PANEL,
        font=dict(family="Consolas, monospace", color=_TEXT, size=11),
        margin=dict(l=10, r=10, t=30, b=10),
    )
    base.update(overrides)
    return base


def _score_color(value: float) -> str:
    """Return traffic-light color string for a 0-100 score."""
    if value >= 70:
        return _GREEN
    if value >= 40:
        return _AMBER
    return _RED


def _safe_scores(scores: dict) -> dict:
    """Normalise *scores* so every domain has a numeric value in 0-100."""
    out = {}
    for d in _DOMAINS:
        raw = scores.get(d, 50) if isinstance(scores, dict) else 50
        try:
            v = float(raw)
        except (TypeError, ValueError):
            v = 50.0
        out[d] = max(0.0, min(100.0, v))
    return out


# ======================================================================== #
# A. 3-D Globe Visualization                                               #
# ======================================================================== #

def create_3d_globe(
    lat: float, lon: float, scores: dict, height: int = 400
) -> "go.Figure | None":
    """Orthographic globe centred on *(lat, lon)* with domain-coloured markers.

    Parameters
    ----------
    lat, lon : float
        Centre coordinates.
    scores : dict
        ``{domain_name: 0-100}`` scores used for colouring.
    height : int
        Figure pixel height.

    Returns
    -------
    go.Figure or None
    """
    if go is None:
        return None
    try:
        sc = _safe_scores(scores)
        avg_score = sum(sc.values()) / max(len(sc), 1)

        # Eight surrounding sample points (cardinal + diagonal, +-0.5 deg)
        offsets = [
            (0.5, 0.0), (-0.5, 0.0), (0.0, 0.5), (0.0, -0.5),
            (0.35, 0.35), (0.35, -0.35), (-0.35, 0.35), (-0.35, -0.35),
        ]
        surr_lats = [lat + dlat for dlat, _ in offsets]
        surr_lons = [lon + dlon for _, dlon in offsets]

        # Colour surrounding points by per-domain averages cycling through domains
        surr_colors = []
        domain_list = _DOMAINS[:8]
        for idx in range(8):
            d = domain_list[idx]
            surr_colors.append(_DOMAIN_COLORS.get(d, _CYAN))

        surr_hover = [
            f"Sample {i+1}<br>Score avg: {avg_score:.0f}"
            for i in range(8)
        ]

        fig = go.Figure()

        # Surrounding points
        fig.add_trace(go.Scattergeo(
            lat=surr_lats,
            lon=surr_lons,
            mode="markers",
            marker=dict(
                size=9,
                color=surr_colors,
                opacity=0.75,
                line=dict(width=1, color="rgba(255,255,255,0.3)"),
            ),
            text=surr_hover,
            hoverinfo="text",
            name="Sampling grid",
        ))

        # Main location — large pulsing marker
        fig.add_trace(go.Scattergeo(
            lat=[lat],
            lon=[lon],
            mode="markers+text",
            marker=dict(
                size=20,
                color=_CYAN,
                opacity=0.95,
                line=dict(width=2, color="rgba(0,240,255,0.5)"),
                symbol="circle",
            ),
            text=["TARGET"],
            textfont=dict(size=9, color=_CYAN),
            textposition="top center",
            hovertext=f"Lat {lat:.4f}, Lon {lon:.4f}<br>Overall: {avg_score:.0f}",
            hoverinfo="text",
            name="Target",
        ))

        # Outer glow ring around target
        fig.add_trace(go.Scattergeo(
            lat=[lat],
            lon=[lon],
            mode="markers",
            marker=dict(
                size=35,
                color="rgba(0,240,255,0.15)",
                line=dict(width=0),
            ),
            hoverinfo="skip",
            showlegend=False,
        ))

        fig.update_layout(
            **_dark_layout(
                height=height,
                showlegend=False,
                margin=dict(l=0, r=0, t=0, b=0),
                geo=dict(
                    bgcolor="rgba(5,5,16,1)",
                    landcolor="#0d1117",
                    oceancolor="#050510",
                    showocean=True,
                    showland=True,
                    showcountries=True,
                    countrycolor="rgba(255,255,255,0.1)",
                    showlakes=True,
                    lakecolor="#050510",
                    projection_type="orthographic",
                    projection_rotation=dict(lat=lat, lon=lon),
                    lonaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
                    lataxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.03)"),
                    framecolor="rgba(0,240,255,0.15)",
                    coastlinecolor="rgba(0,240,255,0.2)",
                ),
            )
        )
        return fig
    except Exception:
        logger.exception("create_3d_globe failed")
        return None


# ======================================================================== #
# B. Gauge Dashboard                                                        #
# ======================================================================== #

def create_gauge_dashboard(
    scores: dict, height: int = 500
) -> "go.Figure | None":
    """Ten-gauge dashboard (2 rows x 5 cols) showing all domain scores.

    Parameters
    ----------
    scores : dict
        ``{domain_name: 0-100}`` values.
    height : int
        Figure pixel height.

    Returns
    -------
    go.Figure or None
    """
    if go is None or make_subplots is None:
        return None
    try:
        sc = _safe_scores(scores)

        fig = make_subplots(
            rows=2,
            cols=5,
            specs=[[{"type": "indicator"}] * 5] * 2,
            horizontal_spacing=0.03,
            vertical_spacing=0.12,
        )

        for idx, domain in enumerate(_DOMAINS):
            row = idx // 5 + 1
            col = idx % 5 + 1
            val = sc[domain]
            bar_color = _score_color(val)
            display = _DOMAIN_LABELS.get(domain, domain)
            short_label = display.replace("Resources", "Res.").replace(
                "Stability", "Stab."
            ).replace("& Weather", "& Wthr").replace(
                "Natural Hazards", "Nat. Haz."
            ).replace("Economic Potential", "Econ. Pot.").replace(
                "Habitability", "Habit.")

            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=val,
                    number=dict(font=dict(size=16, color=_TEXT), suffix=""),
                    title=dict(
                        text=short_label,
                        font=dict(size=10, color=_DIM),
                    ),
                    gauge=dict(
                        axis=dict(
                            range=[0, 100],
                            tickwidth=1,
                            tickcolor=_DIM,
                            dtick=25,
                            tickfont=dict(size=7, color=_DIM),
                        ),
                        bar=dict(color=bar_color, thickness=0.6),
                        bgcolor="rgba(10,10,24,1)",
                        borderwidth=1,
                        bordercolor="rgba(255,255,255,0.08)",
                        steps=[
                            dict(range=[0, 40], color="rgba(255,51,68,0.15)"),
                            dict(range=[40, 70], color="rgba(255,170,0,0.12)"),
                            dict(range=[70, 100], color="rgba(0,255,136,0.10)"),
                        ],
                        threshold=dict(
                            line=dict(color=_TEXT, width=2),
                            thickness=0.75,
                            value=val,
                        ),
                    ),
                ),
                row=row,
                col=col,
            )

        fig.update_layout(
            **_dark_layout(
                height=height,
                margin=dict(l=20, r=20, t=30, b=10),
            )
        )
        return fig
    except Exception:
        logger.exception("create_gauge_dashboard failed")
        return None


# ======================================================================== #
# C. Bullet Chart Grid                                                      #
# ======================================================================== #

def create_bullet_chart(
    scores: dict,
    benchmarks: dict = None,
    height: int = 400,
) -> "go.Figure | None":
    """Horizontal bullet chart comparing domain scores against benchmarks.

    Parameters
    ----------
    scores : dict
        ``{domain_name: 0-100}`` values.
    benchmarks : dict or None
        Optional benchmark per domain; defaults to 60 for each.
    height : int
        Figure pixel height.

    Returns
    -------
    go.Figure or None
    """
    if go is None:
        return None
    try:
        sc = _safe_scores(scores)
        if benchmarks is None:
            benchmarks = {d: 60 for d in _DOMAINS}

        # Sort domains by score descending
        sorted_domains = sorted(_DOMAINS, key=lambda d: sc[d], reverse=True)

        fig = go.Figure()

        y_labels = []
        for idx, domain in enumerate(sorted_domains):
            val = sc[domain]
            bench = float(benchmarks.get(domain, 60))
            dcolor = _DOMAIN_COLORS.get(domain, _CYAN)
            dlabel = _DOMAIN_LABELS.get(domain, domain)
            y_labels.append(dlabel)

            # Background ranges — red / amber / green bands (wide, faint)
            for rng_start, rng_end, rng_color in [
                (0, 40, "rgba(255,51,68,0.08)"),
                (40, 70, "rgba(255,170,0,0.06)"),
                (70, 100, "rgba(0,255,136,0.06)"),
            ]:
                fig.add_trace(go.Bar(
                    y=[dlabel],
                    x=[rng_end - rng_start],
                    base=rng_start,
                    orientation="h",
                    marker=dict(color=rng_color),
                    width=0.7,
                    showlegend=False,
                    hoverinfo="skip",
                ))

            # Actual score bar (narrower, solid)
            fig.add_trace(go.Bar(
                y=[dlabel],
                x=[val],
                orientation="h",
                marker=dict(color=dcolor, opacity=0.85),
                width=0.35,
                showlegend=False,
                hovertext=f"{dlabel}: {val:.0f}/100",
                hoverinfo="text",
            ))

            # Benchmark marker (vertical line)
            fig.add_trace(go.Scatter(
                x=[bench, bench],
                y=[dlabel, dlabel],
                mode="markers",
                marker=dict(
                    symbol="line-ns",
                    size=14,
                    line=dict(width=2, color=_TEXT),
                    color=_TEXT,
                ),
                showlegend=False,
                hovertext=f"Benchmark: {bench:.0f}",
                hoverinfo="text",
            ))

        fig.update_layout(
            **_dark_layout(
                height=max(height, len(sorted_domains) * 38),
                barmode="overlay",
                xaxis=dict(
                    range=[0, 105],
                    title=dict(text="Score", font=dict(size=10, color=_DIM)),
                    gridcolor="rgba(255,255,255,0.04)",
                    zeroline=False,
                    tickfont=dict(size=9, color=_DIM),
                ),
                yaxis=dict(
                    categoryorder="array",
                    categoryarray=list(reversed([_DOMAIN_LABELS.get(d, d) for d in sorted_domains])),
                    tickfont=dict(size=10, color=_TEXT),
                ),
                margin=dict(l=140, r=20, t=25, b=30),
            )
        )
        return fig
    except Exception:
        logger.exception("create_bullet_chart failed")
        return None


# ======================================================================== #
# D. Polar Bar Chart                                                        #
# ======================================================================== #

def create_polar_bar(
    scores: dict, height: int = 400
) -> "go.Figure | None":
    """Polar (radial) bar chart showing all domain scores in a circle.

    Parameters
    ----------
    scores : dict
        ``{domain_name: 0-100}`` values.
    height : int
        Figure pixel height.

    Returns
    -------
    go.Figure or None
    """
    if go is None:
        return None
    try:
        sc = _safe_scores(scores)

        n = len(_DOMAINS)
        theta_step = 360.0 / n
        theta_vals = [i * theta_step for i in range(n)]
        r_vals = [sc[d] for d in _DOMAINS]
        colors = [_DOMAIN_COLORS.get(d, _CYAN) for d in _DOMAINS]
        hover = [f"{_DOMAIN_LABELS.get(d, d)}: {sc[d]:.0f}/100" for d in _DOMAINS]

        fig = go.Figure()

        fig.add_trace(go.Barpolar(
            r=r_vals,
            theta=theta_vals,
            width=[theta_step - 4] * n,
            marker=dict(
                color=colors,
                opacity=0.82,
                line=dict(color="rgba(255,255,255,0.15)", width=1),
            ),
            text=hover,
            hoverinfo="text",
        ))

        # Short labels for angular ticks
        short_labels = []
        for d in _DOMAINS:
            dl = _DOMAIN_LABELS.get(d, d)
            label = dl.replace("Resources", "Res.").replace(
                "Stability", "Stab."
            ).replace("& Weather", "").replace("Natural ", "Nat. ")
            short_labels.append(label)

        fig.update_layout(
            **_dark_layout(
                height=height,
                showlegend=False,
                margin=dict(l=40, r=40, t=30, b=20),
                polar=dict(
                    bgcolor="rgba(5,5,16,0.8)",
                    radialaxis=dict(
                        range=[0, 100],
                        dtick=25,
                        gridcolor="rgba(255,255,255,0.05)",
                        tickfont=dict(size=8, color=_DIM),
                        linecolor="rgba(255,255,255,0.05)",
                        showline=False,
                    ),
                    angularaxis=dict(
                        tickvals=theta_vals,
                        ticktext=short_labels,
                        tickfont=dict(size=9, color=_DIM),
                        gridcolor="rgba(255,255,255,0.04)",
                        linecolor="rgba(255,255,255,0.06)",
                        direction="clockwise",
                    ),
                ),
            )
        )
        return fig
    except Exception:
        logger.exception("create_polar_bar failed")
        return None


# ======================================================================== #
# E. Ridgeline / Joy Plot                                                   #
# ======================================================================== #

def create_ridgeline(
    scores: dict,
    analytics: dict = None,
    height: int = 400,
) -> "go.Figure | None":
    """Ridgeline (joy) plot of Gaussian probability curves per domain.

    Each domain's score is rendered as a bell curve centred on its value,
    vertically offset so the curves overlap slightly for a dense, layered
    aesthetic.

    Parameters
    ----------
    scores : dict
        ``{domain_name: 0-100}`` values.
    analytics : dict or None
        Optional extra data (reserved for future use). Currently unused.
    height : int
        Figure pixel height.

    Returns
    -------
    go.Figure or None
    """
    if go is None:
        return None
    try:
        sc = _safe_scores(scores)
        n = len(_DOMAINS)
        row_gap = 0.3
        std = 10.0
        x_pts = 51
        x_vals = [i * 2.0 for i in range(x_pts)]  # 0 to 100

        fig = go.Figure()

        # Draw from top to bottom so the lowest domain overlaps on top
        for idx, domain in enumerate(reversed(_DOMAINS)):
            score = sc[domain]
            y_offset = idx * row_gap
            dcolor = _DOMAIN_COLORS.get(domain, _CYAN)

            # Gaussian bell curve
            y_raw = []
            for x in x_vals:
                exponent = -0.5 * ((x - score) / std) ** 2
                y_raw.append(math.exp(exponent))

            y_shifted = [y + y_offset for y in y_raw]
            y_baseline = [y_offset] * x_pts

            # Baseline trace (invisible, needed for fill='tonexty')
            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_baseline,
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            ))

            # Filled area curve
            # Convert hex domain color to rgba fill
            fill_rgba = _hex_to_rgba(dcolor, 0.35)
            line_rgba = _hex_to_rgba(dcolor, 0.9)

            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_shifted,
                mode="lines",
                line=dict(width=1.5, color=line_rgba),
                fill="tonexty",
                fillcolor=fill_rgba,
                name=_DOMAIN_LABELS.get(domain, domain),
                showlegend=False,
                hovertext=f"{_DOMAIN_LABELS.get(domain, domain)}: {score:.0f}/100",
                hoverinfo="text",
            ))

        # Y-axis tick labels at each row offset centre
        tick_vals = [i * row_gap for i in range(n)]
        tick_text = list(reversed([_DOMAIN_LABELS.get(d, d) for d in _DOMAINS]))

        fig.update_layout(
            **_dark_layout(
                height=max(height, n * 40),
                margin=dict(l=150, r=20, t=25, b=30),
                xaxis=dict(
                    title=dict(text="Score", font=dict(size=10, color=_DIM)),
                    range=[0, 100],
                    gridcolor="rgba(255,255,255,0.04)",
                    zeroline=False,
                    tickfont=dict(size=9, color=_DIM),
                ),
                yaxis=dict(
                    tickvals=tick_vals,
                    ticktext=tick_text,
                    tickfont=dict(size=9, color=_TEXT),
                    gridcolor="rgba(0,0,0,0)",
                    zeroline=False,
                    showgrid=False,
                ),
                showlegend=False,
            )
        )
        return fig
    except Exception:
        logger.exception("create_ridgeline failed")
        return None


# ---------------------------------------------------------------------------
# Internal colour utilities
# ---------------------------------------------------------------------------

def _hex_to_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """Convert a hex colour (``#RRGGBB``) to an ``rgba(r,g,b,a)`` string.

    Falls back to a semi-transparent white on malformed input.
    """
    try:
        h = hex_color.lstrip("#")
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        elif len(h) == 3:
            r, g, b = int(h[0] * 2, 16), int(h[1] * 2, 16), int(h[2] * 2, 16)
        else:
            return f"rgba(255,255,255,{alpha})"
        return f"rgba({r},{g},{b},{alpha})"
    except Exception:
        return f"rgba(255,255,255,{alpha})"
