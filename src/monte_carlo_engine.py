"""
Monte Carlo Risk Simulation Engine for TerraScout AI.

Provides probabilistic risk analysis through Monte Carlo simulation,
stress testing, sensitivity analysis, and convergence diagnostics.
Uses only Python standard library (math, random, logging) -- no
external numerical packages required.

Functions
---------
monte_carlo_risk_simulation
    Run N iterations of triangular-sampled domain scores and produce
    a full probability distribution with percentiles and risk metrics.

scenario_stress_test
    Apply hypothetical shocks (e.g. earthquake, drought) and compare
    the resulting distributions against the baseline.

sensitivity_analysis
    Tornado-chart data: how much does zeroing or maxing each domain
    shift the overall score?

convergence_check
    Demonstrate that the chosen iteration count yields a stable mean.

generate_mc_summary
    Human-readable narrative summary of Monte Carlo results.
"""

import math
import random
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Domain weights -- mirrors unified_intelligence.INTELLIGENCE_DOMAINS
# ---------------------------------------------------------------------------
DOMAIN_WEIGHTS = {
    "habitability": 0.12,
    "agriculture": 0.10,
    "ecology": 0.10,
    "hazard_safety": 0.12,
    "water_resources": 0.10,
    "infrastructure": 0.10,
    "climate_comfort": 0.08,
    "economic_potential": 0.10,
    "air_environment": 0.08,
    "geological_stability": 0.10,
}

DOMAIN_DISPLAY_NAMES = {
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _triangular_sample(low, mode, high):
    """Sample a single value from a triangular distribution.

    Parameters
    ----------
    low : float
        Minimum of the triangle.
    mode : float
        Peak (most-likely value) of the triangle.
    high : float
        Maximum of the triangle.

    Returns
    -------
    float
        A random sample in [low, high].
    """
    if high <= low:
        return mode

    u = random.random()
    fc = (mode - low) / (high - low)

    if u < fc:
        return low + math.sqrt(u * (high - low) * (mode - low))
    else:
        return high - math.sqrt((1.0 - u) * (high - low) * (high - mode))


def _percentile(sorted_data, p):
    """Compute the *p*-th percentile of an already-sorted list.

    Uses linear interpolation between the two nearest data points,
    matching the ``exclusive`` method (similar to Excel PERCENTILE.EXC
    for large N).

    Parameters
    ----------
    sorted_data : list[float]
        Pre-sorted numeric values (ascending).
    p : float
        Percentile in 0-100 range.

    Returns
    -------
    float
        Interpolated percentile value.
    """
    if not sorted_data:
        return 0.0

    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]

    # Map p (0-100) to a fractional index
    k = (p / 100.0) * (n - 1)
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return sorted_data[int(k)]

    # Linear interpolation
    lower = sorted_data[int(f)]
    upper = sorted_data[int(c)]
    return lower + (upper - lower) * (k - f)


def _compute_std(values, mean):
    """Compute population standard deviation given pre-computed mean.

    Parameters
    ----------
    values : list[float]
        Numeric observations.
    mean : float
        Pre-computed arithmetic mean of *values*.

    Returns
    -------
    float
        Population standard deviation.
    """
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def _classify_risk(mean, std):
    """Assign a human-readable risk classification.

    Parameters
    ----------
    mean : float
        Mean overall score across iterations.
    std : float
        Standard deviation of overall scores.

    Returns
    -------
    str
        Classification label.
    """
    if mean >= 70 and std < 10:
        return "LOW RISK \u2014 High Confidence"
    if mean >= 70 and std >= 10:
        return "MODERATE RISK \u2014 Volatile Upside"
    if mean >= 50 and std < 15:
        return "MODERATE RISK \u2014 Stable Performance"
    if mean >= 50 and std >= 15:
        return "ELEVATED RISK \u2014 High Uncertainty"
    if mean >= 30:
        return "HIGH RISK \u2014 Marginal Viability"
    return "CRITICAL RISK \u2014 Significant Concerns"


def _weighted_average(domain_values, weights):
    """Compute a weighted average of domain scores.

    If a domain present in *domain_values* is missing from *weights*,
    equal weighting across all domains is used as fallback.

    Parameters
    ----------
    domain_values : dict[str, float]
        Domain name -> sampled score.
    weights : dict[str, float]
        Domain name -> weight (should sum to ~1.0).

    Returns
    -------
    float
        Weighted (or equally-weighted) average.
    """
    # Check that every domain has a weight; fall back to equal weights
    missing = [d for d in domain_values if d not in weights]
    if missing:
        n = len(domain_values)
        equal_w = 1.0 / n if n else 1.0
        return sum(v * equal_w for v in domain_values.values())

    total_weight = sum(weights[d] for d in domain_values)
    if total_weight == 0:
        return 0.0
    return sum(domain_values[d] * weights[d] for d in domain_values) / total_weight


def _build_histogram(sorted_values, n_bins=20):
    """Build a simple histogram from sorted data.

    Parameters
    ----------
    sorted_values : list[float]
        Sorted numeric values.
    n_bins : int
        Number of equal-width bins.

    Returns
    -------
    list[tuple[float, int]]
        List of (bin_center, count) tuples.
    """
    if not sorted_values:
        return []

    lo = sorted_values[0]
    hi = sorted_values[-1]

    # Edge case: all values identical
    if hi == lo:
        return [(lo, len(sorted_values))]

    bin_width = (hi - lo) / n_bins
    bins = [0] * n_bins

    for v in sorted_values:
        idx = int((v - lo) / bin_width)
        if idx >= n_bins:
            idx = n_bins - 1
        bins[idx] += 1

    result = []
    for i in range(n_bins):
        center = lo + bin_width * (i + 0.5)
        result.append((round(center, 2), bins[i]))

    return result


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------


def monte_carlo_risk_simulation(scores, confidence, n_iterations=10000):
    """Run a Monte Carlo simulation over domain scores.

    Each iteration perturbs every domain score using a triangular
    distribution whose spread is governed by *confidence* (higher
    confidence = tighter spread).  The overall score per iteration is
    the weighted average of the perturbed domain scores.

    Parameters
    ----------
    scores : dict[str, float]
        Mapping of domain key -> deterministic score (0-100).
    confidence : float
        Data-confidence level in [0, 1].  A value of 1.0 means zero
        perturbation; 0.0 means maximum perturbation (+/- 50 points).
    n_iterations : int, optional
        Number of Monte Carlo iterations (default 10 000).

    Returns
    -------
    dict
        Full result payload including percentiles, histogram, domain
        distributions, and risk classification.  See module docstring
        for the complete schema.
    """
    random.seed(42)
    logger.info(
        "Starting Monte Carlo simulation: %d iterations, confidence=%.2f",
        n_iterations,
        confidence,
    )

    # Uncertainty half-width driven by confidence
    half_spread = (100.0 - confidence * 100.0) * 0.5

    # Storage
    overall_scores = []
    domain_samples = {d: [] for d in scores}

    # ---- Main loop --------------------------------------------------------
    for _ in range(n_iterations):
        sampled = {}
        for domain, score in scores.items():
            low = max(0.0, score - half_spread)
            high = min(100.0, score + half_spread)
            mode = float(score)
            sample = _triangular_sample(low, mode, high)
            sampled[domain] = sample
            domain_samples[domain].append(sample)

        overall = _weighted_average(sampled, DOMAIN_WEIGHTS)
        overall_scores.append(overall)

    # ---- Aggregate statistics ---------------------------------------------
    overall_scores.sort()
    n = len(overall_scores)
    mean = sum(overall_scores) / n
    std = _compute_std(overall_scores, mean)

    p5 = _percentile(overall_scores, 5)
    p25 = _percentile(overall_scores, 25)
    p50 = _percentile(overall_scores, 50)
    p75 = _percentile(overall_scores, 75)
    p95 = _percentile(overall_scores, 95)

    count_above_60 = sum(1 for v in overall_scores if v > 60)
    count_above_40 = sum(1 for v in overall_scores if v > 40)
    count_below_30 = sum(1 for v in overall_scores if v < 30)

    # ---- Per-domain distributions -----------------------------------------
    domain_distributions = {}
    for domain, samples in domain_samples.items():
        samples.sort()
        d_mean = sum(samples) / len(samples)
        d_std = _compute_std(samples, d_mean)
        d_p5 = _percentile(samples, 5)
        d_p50 = _percentile(samples, 50)
        d_p95 = _percentile(samples, 95)

        display = DOMAIN_DISPLAY_NAMES.get(domain, domain)
        domain_distributions[display] = {
            "mean": round(d_mean, 2),
            "std": round(d_std, 2),
            "p5": round(d_p5, 2),
            "p50": round(d_p50, 2),
            "p95": round(d_p95, 2),
            "spread": round(d_p95 - d_p5, 2),
        }

    # ---- Histogram --------------------------------------------------------
    histogram_bins = _build_histogram(overall_scores, n_bins=20)

    # ---- Risk classification ----------------------------------------------
    risk_class = _classify_risk(mean, std)

    logger.info(
        "Simulation complete: mean=%.2f, std=%.2f, classification=%s",
        mean,
        std,
        risk_class,
    )

    return {
        "overall": {
            "mean": round(mean, 2),
            "std": round(std, 2),
            "p5": round(p5, 2),
            "p25": round(p25, 2),
            "p50": round(p50, 2),
            "p75": round(p75, 2),
            "p95": round(p95, 2),
            "var_95": round(p5, 2),
            "probability_above_60": round(count_above_60 / n * 100, 2),
            "probability_above_40": round(count_above_40 / n * 100, 2),
            "probability_below_30": round(count_below_30 / n * 100, 2),
        },
        "domain_distributions": domain_distributions,
        "histogram_bins": histogram_bins,
        "n_iterations": n_iterations,
        "confidence_input": confidence,
        "risk_classification": risk_class,
    }


# ---------------------------------------------------------------------------
# Stress testing
# ---------------------------------------------------------------------------


def scenario_stress_test(scores, confidence, scenarios):
    """Run stress-test scenarios against a baseline.

    Each scenario modifies a single domain score by a signed delta,
    then re-runs the Monte Carlo simulation (at reduced iterations for
    speed) and reports the change in key metrics relative to the
    unmodified baseline.

    Parameters
    ----------
    scores : dict[str, float]
        Baseline domain scores (0-100).
    confidence : float
        Data-confidence level in [0, 1].
    scenarios : list[dict]
        Each dict must contain:
        - ``name`` (str): human-readable scenario label.
        - ``domain`` (str): key into *scores* to modify.
        - ``delta`` (float): signed change to apply.

    Returns
    -------
    dict
        ``baseline`` -- summary statistics for unmodified scores.
        ``scenarios`` -- list of per-scenario result dicts, each
        containing the scenario metadata plus ``result`` (MC output)
        and ``delta_mean`` / ``delta_p5`` showing shift from baseline.
    """
    logger.info("Running stress test with %d scenarios", len(scenarios))

    # Baseline at reduced iterations for consistency
    baseline = monte_carlo_risk_simulation(scores, confidence, n_iterations=2000)

    results = []
    for scenario in scenarios:
        name = scenario.get("name", "Unnamed")
        domain = scenario.get("domain", "")
        delta = scenario.get("delta", 0)

        if domain not in scores:
            logger.warning(
                "Scenario '%s' references unknown domain '%s'; skipping.",
                name,
                domain,
            )
            continue

        # Build modified scores
        modified = dict(scores)
        modified[domain] = max(0.0, min(100.0, modified[domain] + delta))

        mc_result = monte_carlo_risk_simulation(
            modified, confidence, n_iterations=2000
        )

        results.append(
            {
                "name": name,
                "domain": domain,
                "delta_applied": delta,
                "modified_score": modified[domain],
                "result": mc_result,
                "delta_mean": round(
                    mc_result["overall"]["mean"] - baseline["overall"]["mean"], 2
                ),
                "delta_p5": round(
                    mc_result["overall"]["p5"] - baseline["overall"]["p5"], 2
                ),
                "new_classification": mc_result["risk_classification"],
            }
        )

    logger.info("Stress test complete.")
    return {
        "baseline": baseline,
        "scenarios": results,
    }


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------


def sensitivity_analysis(scores, confidence):
    """Tornado-chart sensitivity analysis.

    For each domain, the score is set to its extreme values (0 and
    100) while all other domains remain at their baseline.  The swing
    (difference between best- and worst-case mean) quantifies how
    sensitive the overall score is to that domain.

    Parameters
    ----------
    scores : dict[str, float]
        Baseline domain scores (0-100).
    confidence : float
        Data-confidence level in [0, 1].

    Returns
    -------
    list[dict]
        Sorted (descending by swing) list of dicts with keys:
        ``domain``, ``worst_case_mean``, ``best_case_mean``, ``swing``.
    """
    logger.info("Running sensitivity analysis across %d domains", len(scores))
    results = []

    for domain in scores:
        # Worst case: domain score = 0
        worst_scores = dict(scores)
        worst_scores[domain] = 0.0
        worst_mc = monte_carlo_risk_simulation(
            worst_scores, confidence, n_iterations=1000
        )
        worst_mean = worst_mc["overall"]["mean"]

        # Best case: domain score = 100
        best_scores = dict(scores)
        best_scores[domain] = 100.0
        best_mc = monte_carlo_risk_simulation(
            best_scores, confidence, n_iterations=1000
        )
        best_mean = best_mc["overall"]["mean"]

        swing = best_mean - worst_mean
        display = DOMAIN_DISPLAY_NAMES.get(domain, domain)

        results.append(
            {
                "domain": display,
                "worst_case_mean": round(worst_mean, 2),
                "best_case_mean": round(best_mean, 2),
                "swing": round(swing, 2),
            }
        )

    # Sort by swing descending -- biggest influence first
    results.sort(key=lambda r: r["swing"], reverse=True)
    logger.info("Sensitivity analysis complete.")
    return results


# ---------------------------------------------------------------------------
# Convergence check
# ---------------------------------------------------------------------------


def convergence_check(scores, confidence):
    """Demonstrate that the simulation converges as iterations increase.

    Runs the Monte Carlo simulation at progressively larger iteration
    counts and records the mean and standard deviation at each step.

    Parameters
    ----------
    scores : dict[str, float]
        Domain scores (0-100).
    confidence : float
        Data-confidence level in [0, 1].

    Returns
    -------
    list[dict]
        List of ``{"iterations": int, "mean": float, "std": float}``
        for each tested iteration count.
    """
    logger.info("Running convergence check")
    steps = [100, 500, 1000, 2500, 5000, 10000]
    results = []

    for n in steps:
        mc = monte_carlo_risk_simulation(scores, confidence, n_iterations=n)
        results.append(
            {
                "iterations": n,
                "mean": mc["overall"]["mean"],
                "std": mc["overall"]["std"],
            }
        )

    logger.info(
        "Convergence check complete. Mean at 10k = %.2f", results[-1]["mean"]
    )
    return results


# ---------------------------------------------------------------------------
# Human-readable summary
# ---------------------------------------------------------------------------


def generate_mc_summary(mc_result):
    """Generate a concise narrative summary of Monte Carlo results.

    Parameters
    ----------
    mc_result : dict
        Output of :func:`monte_carlo_risk_simulation`.

    Returns
    -------
    list[str]
        3-5 sentences summarising the simulation outcome.
    """
    ov = mc_result["overall"]
    classification = mc_result["risk_classification"]
    domains = mc_result["domain_distributions"]

    sentences = []

    # 1 -- Expected outcome and confidence
    sentences.append(
        "The expected overall site score is {mean:.1f} (median {p50:.1f}) "
        "with a standard deviation of {std:.1f}, yielding a {cls} "
        "classification.".format(
            mean=ov["mean"],
            p50=ov["p50"],
            std=ov["std"],
            cls=classification,
        )
    )

    # 2 -- Worst-case scenario
    sentences.append(
        "Under worst-case conditions (5th percentile), the score drops to "
        "{p5:.1f}, while the best-case scenario (95th percentile) reaches "
        "{p95:.1f}.".format(p5=ov["p5"], p95=ov["p95"])
    )

    # 3 -- Probability thresholds
    if ov["probability_above_60"] > 0:
        sentences.append(
            "There is a {pct:.1f}% probability that the site achieves a "
            "viable score (above 60).".format(pct=ov["probability_above_60"])
        )
    elif ov["probability_above_40"] > 0:
        sentences.append(
            "The site has only a {pct:.1f}% chance of exceeding the "
            "marginal-viability threshold of 40.".format(
                pct=ov["probability_above_40"]
            )
        )
    else:
        sentences.append(
            "The site fails to exceed the marginal threshold of 40 in "
            "virtually all simulated scenarios."
        )

    # 4 -- Highest-uncertainty domains
    if domains:
        sorted_domains = sorted(
            domains.items(), key=lambda kv: kv[1]["spread"], reverse=True
        )
        top_uncertain = sorted_domains[:2]
        names = " and ".join(d[0] for d in top_uncertain)
        spreads = ", ".join(
            "{:.1f}".format(d[1]["spread"]) for d in top_uncertain
        )
        sentences.append(
            "The domains contributing most uncertainty are {names} "
            "(90% spreads of {spreads} points respectively).".format(
                names=names, spreads=spreads
            )
        )

    # 5 -- Risk narrative
    if ov["probability_below_30"] > 5:
        sentences.append(
            "Caution: there is a {pct:.1f}% probability of the site "
            "falling into the critical-risk zone (below 30).".format(
                pct=ov["probability_below_30"]
            )
        )
    elif ov["probability_above_60"] >= 90:
        sentences.append(
            "The site demonstrates strong resilience across simulated "
            "conditions, with over 90% of outcomes above the viability "
            "threshold."
        )

    return sentences
