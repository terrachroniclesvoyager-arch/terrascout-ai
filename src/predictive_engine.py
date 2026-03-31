"""
Predictive Analytics Engine for TerraScout AI.

Generates forward-looking predictions and forecasts from current domain scores
and analytics data. Uses trend extrapolation, exponential smoothing, and
scenario modeling to project domain trajectories across three time horizons.

Pure Python implementation -- only stdlib imports (math, random, logging).
"""

import math
import random
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DOMAINS = [
    "habitability",
    "agriculture",
    "ecology",
    "hazard_safety",
    "water_resources",
    "infrastructure",
    "climate_comfort",
    "economic_potential",
    "air_environment",
    "geological_stability",
]

VIABLE_THRESHOLD = 60
CRITICAL_THRESHOLD = 30

# Domain-specific annual trend defaults (per-year change when no analytics
# data supplies a better estimate).  Positive = improvement, negative = decline.
_DEFAULT_ANNUAL_TRENDS: dict = {}  # populated dynamically per call

# Cross-domain influence weights used by the compound-effects model.
_CROSS_INFLUENCE = {
    "water_resources":    {"agriculture": 0.6, "ecology": 0.3, "habitability": 0.2},
    "infrastructure":     {"economic_potential": 0.4, "habitability": 0.3},
    "hazard_safety":      {"habitability": 0.3, "infrastructure": 0.2, "economic_potential": 0.15},
    "ecology":            {"water_resources": 0.25, "air_environment": 0.2, "climate_comfort": 0.1},
    "climate_comfort":    {"agriculture": 0.35, "habitability": 0.2},
    "economic_potential":  {"infrastructure": 0.25, "habitability": 0.15},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* between *lo* and *hi*."""
    return max(lo, min(hi, value))


def _trend_label(annual_trend: float) -> str:
    """Classify an annual trend value into a human-readable direction."""
    if annual_trend > 0.5:
        return "IMPROVING"
    if annual_trend < -2.0:
        return "CRITICAL_DECLINE"
    if annual_trend < -0.5:
        return "DECLINING"
    return "STABLE"


def _horizon_trend_label(delta: float, horizon_years: float) -> str:
    """Return a trend label for a single horizon based on absolute delta."""
    annual = delta / horizon_years if horizon_years else 0.0
    return _trend_label(annual)


def _safe_mean(values: list) -> float:
    """Return the arithmetic mean, or 0.0 for empty lists."""
    return sum(values) / len(values) if values else 0.0


def _extract_analytics_trend(analytics: dict, domain: str) -> float | None:
    """Try to pull a numeric trend for *domain* out of the analytics blob.

    Returns None when no usable trend is found, so the caller can fall back
    to domain-specific heuristics.
    """
    if not analytics or not isinstance(analytics, dict):
        return None
    trends = analytics.get("trends") or analytics.get("domain_trends") or {}
    if isinstance(trends, dict) and domain in trends:
        val = trends[domain]
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, dict):
            return float(val.get("annual", val.get("slope", 0.0)))
    return None


# ---------------------------------------------------------------------------
# 2. Exponential Smoothing Forecast
# ---------------------------------------------------------------------------

def exponential_smoothing_forecast(
    values: list,
    alpha: float = 0.3,
    periods: int = 4,
) -> list:
    """Simple exponential smoothing for time-series data.

    Parameters
    ----------
    values : list[float]
        Historical observations (oldest first).
    alpha : float
        Smoothing factor in (0, 1].  Higher values weight recent data more.
    periods : int
        Number of future values to project.

    Returns
    -------
    list[float]
        Projected future values (length == *periods*).
    """
    if not values:
        return [0.0] * periods

    # Holt double exponential smoothing for level and trend estimation.
    beta = 0.3  # trend smoothing parameter
    level = values[0]
    trend_per_period = 0.0
    if len(values) >= 2:
        for obs in values[1:]:
            new_level = alpha * obs + (1.0 - alpha) * (level + trend_per_period)
            new_trend = beta * (new_level - level) + (1.0 - beta) * trend_per_period
            level = new_level
            trend_per_period = new_trend

    forecasts = []
    for i in range(1, periods + 1):
        forecasts.append(level + trend_per_period * i)
    return forecasts


# ---------------------------------------------------------------------------
# 3. Compound Effects
# ---------------------------------------------------------------------------

def compute_compound_effects(
    scores: dict,
    forecast_deltas: dict,
) -> dict:
    """Model how projected changes compound across interdependent domains.

    Rules
    -----
    * Water drop -> agriculture drops (lagged 1 period).
    * Infrastructure growth -> economic_potential grows (lagged 2 periods).
    * hazard_safety < 30 -> all domains receive -5 penalty.
    * ecology < 25 -> water_resources receives -3 penalty.

    Parameters
    ----------
    scores : dict
        Current domain scores ``{domain: float}``.
    forecast_deltas : dict
        Projected change per domain ``{domain: float}`` (total, not per-year).

    Returns
    -------
    dict
        Adjusted *forecast_deltas* with compound effects folded in.
    """
    adjusted = {d: forecast_deltas.get(d, 0.0) for d in DOMAINS}

    # --- Water -> Agriculture (lag-1 factor 0.5) ---
    water_delta = forecast_deltas.get("water_resources", 0.0)
    if water_delta < 0:
        adjusted["agriculture"] = adjusted.get("agriculture", 0.0) + water_delta * 0.5

    # --- Infrastructure -> Economic Potential (lag-2 factor 0.35) ---
    infra_delta = forecast_deltas.get("infrastructure", 0.0)
    if infra_delta > 0:
        adjusted["economic_potential"] = adjusted.get("economic_potential", 0.0) + infra_delta * 0.35

    # --- Hazard safety critical collapse ---
    projected_hazard = scores.get("hazard_safety", 50) + forecast_deltas.get("hazard_safety", 0.0)
    if projected_hazard < CRITICAL_THRESHOLD:
        for d in DOMAINS:
            adjusted[d] = adjusted.get(d, 0.0) - 5.0

    # --- Ecology critical -> water penalty ---
    projected_ecology = scores.get("ecology", 50) + forecast_deltas.get("ecology", 0.0)
    if projected_ecology < 25:
        adjusted["water_resources"] = adjusted.get("water_resources", 0.0) - 3.0

    # --- Cross-influence propagation ---
    for source, targets in _CROSS_INFLUENCE.items():
        src_delta = forecast_deltas.get(source, 0.0)
        if abs(src_delta) < 0.1:
            continue
        for tgt, weight in targets.items():
            adjusted[tgt] = adjusted.get(tgt, 0.0) + src_delta * weight * 0.25

    return adjusted


# ---------------------------------------------------------------------------
# 1. Main Prediction Engine
# ---------------------------------------------------------------------------

def _domain_annual_trend(
    domain: str,
    score: float,
    scores: dict,
    analytics: dict,
) -> float:
    """Compute the annual trend (points per year) for a single domain.

    Uses analytics data when available; otherwise falls back to
    domain-specific heuristic models.
    """
    # Prefer analytics-supplied trend.
    analytics_trend = _extract_analytics_trend(analytics, domain)
    if analytics_trend is not None:
        return analytics_trend

    # --- Domain heuristics ---
    if domain == "hazard_safety":
        # Climate-change degradation pressure.
        return -0.5

    if domain == "infrastructure":
        econ = scores.get("economic_potential", 50)
        if econ > 50:
            return 0.3
        if econ < 30:
            return -0.5
        return 0.0

    if domain == "ecology":
        trend = 0.0
        if scores.get("infrastructure", 50) > 60:
            trend -= 0.3
        if scores.get("hazard_safety", 50) > 70:
            trend += 0.2
        return trend

    if domain == "water_resources":
        trend = 0.0
        if scores.get("climate_comfort", 50) < 40:
            trend -= 0.4
        # Seasonal adjustment: slight sine wave contribution (peak mid-year).
        random.seed(42)
        seasonal = 0.15 * math.sin(random.uniform(0, 2 * math.pi))
        return trend + seasonal

    if domain == "climate_comfort":
        # Very slow drift.
        return -0.1  # slight warming pressure globally

    if domain == "agriculture":
        water_trend = _domain_annual_trend("water_resources", scores.get("water_resources", 50), scores, analytics)
        climate_trend = _domain_annual_trend("climate_comfort", scores.get("climate_comfort", 50), scores, analytics)
        return (water_trend + climate_trend) / 2.0

    # Default: neighbor-influenced +-0.2/yr
    neighbor_avg = _safe_mean([s for d, s in scores.items() if d != domain and isinstance(s, (int, float))])
    if neighbor_avg > score + 10:
        return 0.2
    if neighbor_avg < score - 10:
        return -0.2
    return 0.0


def compute_predictive_outlook(
    scores: dict,
    details: dict,
    analytics: dict,
    raw_data: dict,
) -> dict:
    """Main prediction engine.

    Generates three-horizon forecasts for every domain, an overall outlook,
    risk trajectory, inflection points, and key projection narratives.

    Parameters
    ----------
    scores : dict
        Current domain scores ``{domain_name: float 0-100}``.
    details : dict
        Per-domain detail blobs (used for supplementary context).
    analytics : dict
        Analytical results (trends, seasonality, correlations).
    raw_data : dict
        Raw upstream data (may contain historical series).

    Returns
    -------
    dict
        Full predictive outlook structure.
    """
    random.seed(42)

    domain_forecasts: dict = {}
    inflection_points: list = []

    for domain in DOMAINS:
        current = float(scores.get(domain, 50))
        annual_trend = _domain_annual_trend(domain, current, scores, analytics)

        # --- Confidence heuristic (0-1) ---
        # Higher when we have analytics data; lower for pure heuristic.
        has_analytics = _extract_analytics_trend(analytics, domain) is not None
        confidence = 0.7 if has_analytics else 0.45

        # --- Noise & compound factors ---
        noise_med = random.uniform(-1.5, 1.5)
        noise_long = random.uniform(-3.0, 3.0)

        # --- Three horizons ---
        short_val = _clamp(current + annual_trend * 0.25)
        med_val = _clamp(current + annual_trend * 1.0 + noise_med)
        long_raw = current + annual_trend * 5.0 + noise_long

        # --- Compound effects for long-term ---
        long_deltas = {d: _domain_annual_trend(d, float(scores.get(d, 50)), scores, analytics) * 5.0
                       for d in DOMAINS}
        compound = compute_compound_effects(scores, long_deltas)
        long_compound_adj = compound.get(domain, 0.0) - long_deltas.get(domain, 0.0)
        long_val = _clamp(long_raw + long_compound_adj)

        # --- Uncertainty bounds ---
        unc_short = 5.0 - confidence * 4.0
        unc_med = 12.0 - confidence * 8.0
        unc_long = 25.0 - confidence * 15.0

        short_low = _clamp(short_val - unc_short)
        short_high = _clamp(short_val + unc_short)
        med_low = _clamp(med_val - unc_med)
        med_high = _clamp(med_val + unc_med)
        long_low = _clamp(long_val - unc_long)
        long_high = _clamp(long_val + unc_long)

        # --- Trend labels ---
        short_trend = _horizon_trend_label(short_val - current, 0.25)
        med_trend = _horizon_trend_label(med_val - current, 1.0)
        long_trend = _horizon_trend_label(long_val - current, 5.0)

        domain_forecasts[domain] = {
            "current": round(current, 2),
            "short_term": {
                "value": round(short_val, 2),
                "low": round(short_low, 2),
                "high": round(short_high, 2),
                "trend": short_trend,
            },
            "medium_term": {
                "value": round(med_val, 2),
                "low": round(med_low, 2),
                "high": round(med_high, 2),
                "trend": med_trend,
            },
            "long_term": {
                "value": round(long_val, 2),
                "low": round(long_low, 2),
                "high": round(long_high, 2),
                "trend": long_trend,
            },
            "annual_trend": round(annual_trend, 3),
            "trend_direction": _trend_label(annual_trend),
        }

        # --- Inflection-point detection ---
        for horizon_name, horizon_val, horizon_years in [
            ("SHORT", short_val, 0.25),
            ("MEDIUM", med_val, 1.0),
            ("LONG", long_val, 5.0),
        ]:
            # Crossing the viable threshold (60) from above or below.
            if (current >= VIABLE_THRESHOLD > horizon_val) or (current < VIABLE_THRESHOLD <= horizon_val):
                inflection_points.append({
                    "domain": domain,
                    "threshold": VIABLE_THRESHOLD,
                    "direction": "below" if horizon_val < VIABLE_THRESHOLD else "above",
                    "horizon": horizon_name,
                    "projected_value": round(horizon_val, 2),
                })
            # Crossing the critical threshold (30).
            if (current >= CRITICAL_THRESHOLD > horizon_val) or (current < CRITICAL_THRESHOLD <= horizon_val):
                inflection_points.append({
                    "domain": domain,
                    "threshold": CRITICAL_THRESHOLD,
                    "direction": "below" if horizon_val < CRITICAL_THRESHOLD else "above",
                    "horizon": horizon_name,
                    "projected_value": round(horizon_val, 2),
                })

    # --- Overall forecast (mean across domains) ---
    def _mean_forecast(key_path):
        vals = []
        for df in domain_forecasts.values():
            node = df
            for k in key_path:
                node = node[k]
            vals.append(node)
        return round(_safe_mean(vals), 2)

    overall_current = _mean_forecast(["current"])
    overall_short = _mean_forecast(["short_term", "value"])
    overall_med = _mean_forecast(["medium_term", "value"])
    overall_long = _mean_forecast(["long_term", "value"])

    # --- Risk trajectory ---
    overall_delta = overall_long - overall_current
    if overall_delta > 2:
        risk_trajectory = "IMPROVING"
    elif overall_delta < -2:
        risk_trajectory = "WORSENING"
    else:
        risk_trajectory = "STABLE"

    # --- Key projections (top 5 sentences) ---
    key_projections = _build_key_projections(domain_forecasts, inflection_points, risk_trajectory)

    return {
        "domain_forecasts": domain_forecasts,
        "overall_forecast": {
            "current": overall_current,
            "short_term": overall_short,
            "medium_term": overall_med,
            "long_term": overall_long,
        },
        "risk_trajectory": risk_trajectory,
        "inflection_points": inflection_points,
        "key_projections": key_projections,
    }


def _build_key_projections(
    domain_forecasts: dict,
    inflection_points: list,
    risk_trajectory: str,
) -> list:
    """Assemble the top 5 most important projection sentences."""
    projections: list = []

    # 1. Largest positive mover.
    best_domain = max(domain_forecasts, key=lambda d: domain_forecasts[d]["annual_trend"])
    best = domain_forecasts[best_domain]
    if best["annual_trend"] > 0:
        projections.append(
            f"{best_domain.replace('_', ' ').title()} is projected to improve by "
            f"{abs(best['annual_trend']):.1f} points/year, reaching "
            f"{best['long_term']['value']:.0f} in 5 years."
        )

    # 2. Largest negative mover.
    worst_domain = min(domain_forecasts, key=lambda d: domain_forecasts[d]["annual_trend"])
    worst = domain_forecasts[worst_domain]
    if worst["annual_trend"] < 0:
        projections.append(
            f"{worst_domain.replace('_', ' ').title()} faces the steepest decline at "
            f"{worst['annual_trend']:.1f} points/year, potentially reaching "
            f"{worst['long_term']['value']:.0f} by year 5."
        )

    # 3. Critical inflection.
    critical_inflections = [ip for ip in inflection_points if ip["threshold"] == CRITICAL_THRESHOLD and ip["direction"] == "below"]
    if critical_inflections:
        ci = critical_inflections[0]
        projections.append(
            f"WARNING: {ci['domain'].replace('_', ' ').title()} is projected to breach the "
            f"critical threshold ({CRITICAL_THRESHOLD}) within the {ci['horizon'].lower()}-term horizon."
        )

    # 4. Overall trajectory.
    projections.append(f"Overall risk trajectory is {risk_trajectory}.")

    # 5. Compound risk summary.
    declining = [d for d, f in domain_forecasts.items() if f["annual_trend"] < -0.3]
    if len(declining) >= 3:
        names = ", ".join(d.replace("_", " ").title() for d in declining[:4])
        projections.append(
            f"Compound risk detected: {names} are declining simultaneously, "
            f"which may amplify negative outcomes."
        )
    elif len(declining) == 0:
        projections.append("No significant compound decline risks detected across domains.")
    else:
        projections.append(
            f"Moderate attention warranted for "
            f"{', '.join(d.replace('_', ' ').title() for d in declining)}."
        )

    return projections[:5]


# ---------------------------------------------------------------------------
# 4. Early Warnings
# ---------------------------------------------------------------------------

def generate_early_warnings(
    domain_forecasts: dict,
    scores: dict,
) -> list:
    """Identify critical warnings from the forecast data.

    Returns a list of warning dicts, each containing *domain*,
    *warning_type*, *severity*, *horizon*, *message*, and
    *recommended_action*.
    """
    warnings: list = []

    # --- THRESHOLD_BREACH ---
    for domain, fc in domain_forecasts.items():
        current = fc["current"]
        for horizon_key, horizon_label in [("short_term", "SHORT"), ("medium_term", "MEDIUM"), ("long_term", "LONG")]:
            proj = fc[horizon_key]["value"]
            # Viable threshold crossing downward.
            if current >= VIABLE_THRESHOLD > proj:
                severity = "HIGH" if horizon_label == "SHORT" else "MODERATE"
                warnings.append({
                    "domain": domain,
                    "warning_type": "THRESHOLD_BREACH",
                    "severity": severity,
                    "horizon": horizon_label,
                    "message": (
                        f"{domain.replace('_', ' ').title()} projected to drop below "
                        f"viable threshold ({VIABLE_THRESHOLD}) to {proj:.1f} "
                        f"in the {horizon_label.lower()}-term."
                    ),
                    "recommended_action": (
                        f"Prioritize investment in {domain.replace('_', ' ')} to maintain viability."
                    ),
                })
            # Critical threshold crossing downward.
            if current >= CRITICAL_THRESHOLD > proj:
                warnings.append({
                    "domain": domain,
                    "warning_type": "THRESHOLD_BREACH",
                    "severity": "CRITICAL",
                    "horizon": horizon_label,
                    "message": (
                        f"CRITICAL: {domain.replace('_', ' ').title()} projected to breach "
                        f"critical threshold ({CRITICAL_THRESHOLD}) reaching {proj:.1f} "
                        f"in the {horizon_label.lower()}-term."
                    ),
                    "recommended_action": (
                        f"Immediate intervention required for {domain.replace('_', ' ')}."
                    ),
                })

    # --- RAPID_DECLINE ---
    for domain, fc in domain_forecasts.items():
        if fc["annual_trend"] < -2.0:
            warnings.append({
                "domain": domain,
                "warning_type": "RAPID_DECLINE",
                "severity": "CRITICAL",
                "horizon": "SHORT",
                "message": (
                    f"{domain.replace('_', ' ').title()} is declining at "
                    f"{fc['annual_trend']:.1f} points/year -- classified as critical decline."
                ),
                "recommended_action": (
                    f"Emergency assessment and remediation plan needed for "
                    f"{domain.replace('_', ' ')}."
                ),
            })

    # --- COMPOUND_RISK ---
    declining_domains = [
        d for d, fc in domain_forecasts.items() if fc["annual_trend"] < -0.3
    ]
    if len(declining_domains) >= 3:
        names = ", ".join(d.replace("_", " ").title() for d in declining_domains)
        warnings.append({
            "domain": "multiple",
            "warning_type": "COMPOUND_RISK",
            "severity": "HIGH",
            "horizon": "MEDIUM",
            "message": (
                f"Compound risk: {len(declining_domains)} domains declining simultaneously "
                f"({names}). Interdependencies may accelerate deterioration."
            ),
            "recommended_action": (
                "Conduct cross-domain impact assessment and prioritize the domain "
                "with the highest downstream influence."
            ),
        })

    # --- CRITICAL_CONVERGENCE ---
    converging_below_40: list = []
    for domain, fc in domain_forecasts.items():
        med_val = fc["medium_term"]["value"]
        if med_val < 40:
            converging_below_40.append(domain)
    if len(converging_below_40) >= 2:
        names = ", ".join(d.replace("_", " ").title() for d in converging_below_40)
        severity = "CRITICAL" if len(converging_below_40) >= 4 else "HIGH"
        warnings.append({
            "domain": "multiple",
            "warning_type": "CRITICAL_CONVERGENCE",
            "severity": severity,
            "horizon": "MEDIUM",
            "message": (
                f"Critical convergence: {len(converging_below_40)} domains converging "
                f"below 40 ({names}). Systemic failure risk is elevated."
            ),
            "recommended_action": (
                "Deploy coordinated intervention across converging domains; "
                "single-domain fixes will be insufficient."
            ),
        })

    # Sort by severity (CRITICAL first).
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2}
    warnings.sort(key=lambda w: severity_order.get(w["severity"], 3))

    return warnings


# ---------------------------------------------------------------------------
# 5. Opportunity Windows
# ---------------------------------------------------------------------------

def compute_opportunity_windows(
    domain_forecasts: dict,
    scores: dict,
) -> list:
    """Identify time-limited opportunities arising from the forecast.

    Returns a list of opportunity dicts with *opportunity*, *domain*,
    *window*, *confidence*, and *action*.
    """
    opportunities: list = []

    for domain, fc in domain_forecasts.items():
        current = fc["current"]
        annual_trend = fc["annual_trend"]
        short_val = fc["short_term"]["value"]
        med_val = fc["medium_term"]["value"]
        long_val = fc["long_term"]["value"]

        # --- Near-threshold trending up: "act now to secure" ---
        if 55 <= current <= 65 and annual_trend > 0.2:
            opportunities.append({
                "opportunity": (
                    f"{domain.replace('_', ' ').title()} is near the viability threshold "
                    f"and trending upward -- secure gains now."
                ),
                "domain": domain,
                "window": "NOW",
                "confidence": min(0.85, 0.5 + annual_trend * 0.15),
                "action": (
                    f"Invest in {domain.replace('_', ' ')} to lock in the positive trend "
                    f"before external factors shift."
                ),
            })

        # --- Temporary improvement window ---
        if short_val > current and med_val < current:
            opportunities.append({
                "opportunity": (
                    f"{domain.replace('_', ' ').title()} shows a short-term improvement "
                    f"window that closes within a year."
                ),
                "domain": domain,
                "window": "3_MONTHS",
                "confidence": 0.55,
                "action": (
                    f"Exploit the temporary uptick in {domain.replace('_', ' ')} "
                    f"for planning or resource allocation before the decline phase."
                ),
            })

        # --- Cross-domain synergy: compound growth ---
        if annual_trend > 0.3:
            # Check if downstream domains also benefit.
            targets = _CROSS_INFLUENCE.get(domain, {})
            beneficiaries = [
                t for t in targets
                if domain_forecasts.get(t, {}).get("annual_trend", 0) > 0.1
            ]
            if beneficiaries:
                names = ", ".join(b.replace("_", " ").title() for b in beneficiaries)
                opportunities.append({
                    "opportunity": (
                        f"Growth in {domain.replace('_', ' ').title()} is catalysing "
                        f"improvement in {names} -- leverage compound growth."
                    ),
                    "domain": domain,
                    "window": "1_YEAR",
                    "confidence": min(0.8, 0.4 + annual_trend * 0.1 * len(beneficiaries)),
                    "action": (
                        f"Coordinate investment in {domain.replace('_', ' ')} and its "
                        f"downstream beneficiaries to maximise compound returns."
                    ),
                })

        # --- Recovery opportunity: domain below critical but trending up ---
        if current < CRITICAL_THRESHOLD and annual_trend > 0:
            opportunities.append({
                "opportunity": (
                    f"{domain.replace('_', ' ').title()} is below critical but showing "
                    f"early recovery signals -- support the recovery trajectory."
                ),
                "domain": domain,
                "window": "NOW",
                "confidence": 0.40 + annual_trend * 0.1,
                "action": (
                    f"Accelerate recovery efforts in {domain.replace('_', ' ')} "
                    f"while momentum is positive."
                ),
            })

        # --- High-value domains nearing peak: maintain ---
        if current > 80 and annual_trend >= 0:
            opportunities.append({
                "opportunity": (
                    f"{domain.replace('_', ' ').title()} is high-performing -- "
                    f"protect this asset to sustain overall location quality."
                ),
                "domain": domain,
                "window": "1_YEAR",
                "confidence": 0.75,
                "action": (
                    f"Maintain current practices for {domain.replace('_', ' ')}; "
                    f"minimal intervention needed but monitoring should continue."
                ),
            })

    # Sort by confidence descending.
    opportunities.sort(key=lambda o: o["confidence"], reverse=True)
    return opportunities


# ---------------------------------------------------------------------------
# 6. Prediction Narrative
# ---------------------------------------------------------------------------

def generate_prediction_narrative(predictive_result: dict) -> str:
    """Generate a 4-6 sentence narrative summarizing the predictive outlook.

    Covers: overall trajectory, biggest risk, biggest opportunity,
    key inflection point, and recommended priority.

    Parameters
    ----------
    predictive_result : dict
        The full output from :func:`compute_predictive_outlook`.

    Returns
    -------
    str
        A plain-English narrative paragraph.
    """
    forecasts = predictive_result.get("domain_forecasts", {})
    overall = predictive_result.get("overall_forecast", {})
    trajectory = predictive_result.get("risk_trajectory", "STABLE")
    inflections = predictive_result.get("inflection_points", [])
    projections = predictive_result.get("key_projections", [])

    sentences: list = []

    # 1. Overall trajectory.
    ov_current = overall.get("current", 50)
    ov_long = overall.get("long_term", 50)
    delta = ov_long - ov_current
    if trajectory == "IMPROVING":
        sentences.append(
            f"The overall outlook is positive, with the composite score projected "
            f"to rise from {ov_current:.1f} to {ov_long:.1f} over the next five years."
        )
    elif trajectory == "WORSENING":
        sentences.append(
            f"The location faces a deteriorating outlook, with the composite score "
            f"projected to decline from {ov_current:.1f} to {ov_long:.1f} over five years."
        )
    else:
        sentences.append(
            f"The overall outlook is broadly stable, with the composite score "
            f"remaining near {ov_current:.1f} (projected {ov_long:.1f} in 5 years)."
        )

    # 2. Biggest risk.
    worst_domain = min(forecasts, key=lambda d: forecasts[d]["annual_trend"])
    worst_trend = forecasts[worst_domain]["annual_trend"]
    if worst_trend < -0.3:
        sentences.append(
            f"The biggest risk lies in {worst_domain.replace('_', ' ')}, which is "
            f"declining at {worst_trend:.1f} points per year and could reach "
            f"{forecasts[worst_domain]['long_term']['value']:.0f} within five years."
        )
    else:
        sentences.append(
            "No single domain presents a sharply declining risk at this time."
        )

    # 3. Biggest opportunity.
    best_domain = max(forecasts, key=lambda d: forecasts[d]["annual_trend"])
    best_trend = forecasts[best_domain]["annual_trend"]
    if best_trend > 0.2:
        sentences.append(
            f"The strongest opportunity is in {best_domain.replace('_', ' ')}, "
            f"trending upward at +{best_trend:.1f} per year with a projected "
            f"{forecasts[best_domain]['long_term']['value']:.0f} in the long term."
        )
    else:
        sentences.append(
            "No domain shows a strong upward trend; maintaining current levels "
            "should be the near-term priority."
        )

    # 4. Key inflection point.
    critical_inflections = [
        ip for ip in inflections
        if ip["threshold"] == CRITICAL_THRESHOLD and ip["direction"] == "below"
    ]
    if critical_inflections:
        ci = critical_inflections[0]
        sentences.append(
            f"A critical inflection point is anticipated: "
            f"{ci['domain'].replace('_', ' ').title()} may breach the critical "
            f"threshold of {CRITICAL_THRESHOLD} within the {ci['horizon'].lower()}-term horizon, "
            f"requiring proactive mitigation."
        )
    elif inflections:
        fi = inflections[0]
        sentences.append(
            f"An inflection point is projected for "
            f"{fi['domain'].replace('_', ' ').title()}, crossing the "
            f"{fi['threshold']} threshold in the {fi['horizon'].lower()} term."
        )
    else:
        sentences.append(
            "No major threshold crossings are projected within the forecast period."
        )

    # 5. Recommended priority.
    if worst_trend < -1.0:
        sentences.append(
            f"Recommended priority: focus resources on stabilizing "
            f"{worst_domain.replace('_', ' ')} before the decline becomes irreversible."
        )
    elif best_trend > 0.5:
        sentences.append(
            f"Recommended priority: capitalize on the momentum in "
            f"{best_domain.replace('_', ' ')} to drive broader improvements."
        )
    else:
        sentences.append(
            "Recommended priority: maintain balanced monitoring across all domains "
            "and address any domain approaching a threshold crossing."
        )

    return " ".join(sentences)
