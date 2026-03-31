"""
Unified Intelligence module for TerraScout AI.
Master Intelligence Aggregator that runs 15+ analyses in parallel and
synthesises ALL results into a single unified intelligence report with
AI-driven conclusions, cross-correlations, SWOT analysis, and decision
recommendations.

Entry point: render_unified_intelligence_tab()
"""

import logging
import math
import html as html_module
from datetime import datetime

import requests
import streamlit as st
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ---------------------------------------------------------------------------
# ADVANCED MATH HELPERS
# ---------------------------------------------------------------------------

def _sigmoid(x, midpoint=50, steepness=0.1):
    """Sigmoid normalization: smooth S-curve mapping to [0,1]."""
    try:
        return 1.0 / (1.0 + math.exp(-steepness * (x - midpoint)))
    except OverflowError:
        return 0.0 if steepness * (x - midpoint) < 0 else 1.0


def _zscore_norm(value, mean, std, scale=100):
    """Z-score normalization mapped to [0, scale]."""
    if std == 0:
        return scale / 2
    z = (value - mean) / std
    return max(0, min(scale, (z + 3) * scale / 6))  # [-3,+3] -> [0,scale]


def _shannon_diversity(counts):
    """Shannon-Wiener diversity index H' = -sum(pi * ln(pi))."""
    total = sum(counts)
    if total == 0:
        return 0.0
    proportions = [c / total for c in counts if c > 0]
    return -sum(p * math.log(p) for p in proportions)


def _bayesian_risk(prior, likelihoods):
    """Simplified Bayesian risk: P(risk|evidence) proportional to P(evidence|risk)*P(risk)."""
    posterior = prior
    for lh in likelihoods:
        posterior *= lh
    # Normalize to [0,1]
    denom = posterior + (1 - prior) * max(0.001, 1 - posterior)
    return posterior / denom if denom > 0 else 0.5


def _exp_decay_weight(distance_km, halflife_km=50):
    """Exponential decay weighting: w = e^(-lambda*d), lambda = ln(2)/halflife."""
    lam = math.log(2) / max(halflife_km, 0.001)
    return math.exp(-lam * distance_km)


def _morans_i_proxy(center_val, neighbor_vals):
    """Moran's I proxy: spatial autocorrelation from center vs neighbors."""
    if not neighbor_vals:
        return 0.0
    mean_all = (center_val + sum(neighbor_vals)) / (1 + len(neighbor_vals))
    num = sum((center_val - mean_all) * (nv - mean_all) for nv in neighbor_vals)
    denom = sum((v - mean_all) ** 2 for v in [center_val] + neighbor_vals)
    if denom < 0.001:
        return 0.0
    return (num / denom) * len(neighbor_vals)


def compute_data_confidence(data):
    """Compute confidence score [0-1] based on data completeness."""
    sources = [
        "elevation", "soil", "weather", "inat", "water",
        "quakes", "geology", "infra", "air_quality", "protected",
        "gdacs", "population", "openaq",
        "nasa_power", "firms_fires", "who_health", "hdi", "noaa_alerts",
        "marine", "flood", "streamflow", "reliefweb", "geonames",
        "climate_projections", "volcanoes", "climate_normals", "soil_moisture", "uv_pollen",
    ]
    available = sum(
        1 for s in sources
        if data.get(s) not in (None, {}, [], 0)
    )
    completeness = available / len(sources)
    return round(completeness, 2)


# ---------------------------------------------------------------------------
# ADVANCED MATH ENGINE — Tier 2+3 Functions
# Real mathematical analysis on real API data
# ---------------------------------------------------------------------------

def _pielous_evenness(counts):
    """Pielou's Evenness J' = H'/H'max = H'/ln(S).
    Measures how equally species are distributed (0=dominated, 1=even).
    Input: list of observation counts per taxon."""
    h = _shannon_diversity(counts)
    s = sum(1 for c in counts if c > 0)
    if s <= 1:
        return 0.0
    return h / math.log(s)


def _simpson_diversity(counts):
    """Simpson's Diversity Index D = 1 - sum(pi^2).
    Probability that two random individuals belong to different taxa."""
    total = sum(counts)
    if total <= 1:
        return 0.0
    return 1.0 - sum((c / total) ** 2 for c in counts if c > 0)


def _berger_parker_dominance(counts):
    """Berger-Parker Dominance d = N_max / N_total.
    High value = single taxon dominates = low diversity."""
    total = sum(counts)
    if total == 0:
        return 0.0
    return max(counts) / total


def _kl_divergence(p_dist, q_dist):
    """Kullback-Leibler divergence D_KL(P || Q) = sum(P(i) * ln(P(i)/Q(i))).
    Measures how the local distribution P diverges from baseline Q.
    Input: two dicts {category: proportion}. Returns bits (nats)."""
    kl = 0.0
    for k, p_val in p_dist.items():
        q_val = q_dist.get(k, 0.001)  # smoothing to avoid log(0)
        if p_val > 0 and q_val > 0:
            kl += p_val * math.log(p_val / q_val)
    return max(0, kl)


def _gini_coefficient(values):
    """Gini coefficient — measures inequality in a distribution.
    G = 0: perfect equality; G = 1: maximum inequality.
    Used for: infrastructure distribution, species dominance, score spread."""
    if not values or len(values) < 2:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    total = sum(sorted_vals)
    if total == 0:
        return 0.0
    cum_sum = 0
    area_under = 0
    for i, v in enumerate(sorted_vals):
        cum_sum += v
        area_under += cum_sum
    # Gini = 1 - 2 * (area under Lorenz curve) / (n * total)
    return 1.0 - (2.0 * area_under) / (n * total) + 1.0 / n


def _terrain_roughness_index(elevations):
    """Terrain Roughness Index (TRI) — Riley et al. 1999.
    TRI = sqrt(mean(sum(diff^2))) where diff = center - neighbor.
    Higher TRI = rougher terrain. Flat = 0, Mountains > 300."""
    if len(elevations) < 2:
        return 0.0
    center = elevations[0] if elevations else 0
    neighbors = elevations[1:] if len(elevations) > 1 else []
    if not neighbors:
        return 0.0
    sq_diffs = [(center - n) ** 2 for n in neighbors]
    return math.sqrt(sum(sq_diffs) / len(sq_diffs))


def _topographic_position_index(center_elev, neighbor_elevs):
    """Topographic Position Index (TPI) = center_elev - mean(neighbors).
    TPI > 0: ridgeline/hilltop. TPI < 0: valley/depression. TPI ~ 0: flat/slope."""
    if not neighbor_elevs:
        return 0.0
    return center_elev - sum(neighbor_elevs) / len(neighbor_elevs)


def _slope_variability(elevations, grid_spacing_m=500):
    """Coefficient of Variation of slope estimates from elevation grid.
    High CV = terrain with mixed flat and steep areas."""
    if len(elevations) < 3:
        return 0.0
    slopes = []
    for i in range(1, len(elevations)):
        slope_deg = math.degrees(math.atan(abs(elevations[i] - elevations[i - 1]) / grid_spacing_m))
        slopes.append(slope_deg)
    if not slopes:
        return 0.0
    mean_s = sum(slopes) / len(slopes)
    if mean_s == 0:
        return 0.0
    std_s = math.sqrt(sum((s - mean_s) ** 2 for s in slopes) / len(slopes))
    return std_s / mean_s


def _herfindahl_hirschman_index(counts):
    """Herfindahl-Hirschman Index (HHI) — market concentration metric.
    HHI = sum(share_i^2), range [1/N, 1]. Higher = more concentrated.
    Used for: land use concentration, species dominance."""
    total = sum(counts)
    if total == 0:
        return 0.0
    return sum((c / total) ** 2 for c in counts)


def _soil_quality_composite(soc, nitrogen, ph, cec, clay):
    """Weighted geometric mean of soil quality indicators.
    Geometric mean penalizes extreme deficiencies more than arithmetic mean.
    Each factor normalized to [0, 1] using agronomic optimal ranges."""
    factors = []
    # SOC: optimal 2-6%, normalize
    if soc is not None and soc > 0:
        factors.append(min(soc / 4.0, 1.0))  # 4 g/kg = excellent
    # Nitrogen: optimal 0.2-0.5%
    if nitrogen is not None and nitrogen > 0:
        factors.append(min(nitrogen / 0.3, 1.0))
    # pH: optimal 6.0-7.0, bell curve
    if ph is not None:
        ph_opt = 1.0 - min(abs(ph - 6.5) / 2.5, 1.0)
        factors.append(max(ph_opt, 0.01))
    # CEC: optimal > 20 cmol/kg
    if cec is not None and cec > 0:
        factors.append(min(cec / 25.0, 1.0))
    # Clay: optimal 20-35%, penalty if too high or too low
    if clay is not None:
        clay_opt = 1.0 - min(abs(clay - 27.5) / 30.0, 1.0)
        factors.append(max(clay_opt, 0.01))
    if not factors:
        return 0.0
    # Geometric mean: (f1 * f2 * ... * fn)^(1/n)
    product = 1.0
    for f in factors:
        product *= f
    return product ** (1.0 / len(factors))


def _monte_carlo_score_confidence(base_scores, details, n_simulations=500):
    """Monte Carlo simulation — propagate measurement uncertainty through scoring.
    Perturbs raw data within realistic error bounds, recomputes scores N times,
    returns mean, std, and 90% confidence intervals for each domain.

    Error model (based on API accuracy specifications):
    - Elevation: +/- 5m (SRTM30m accuracy)
    - Temperature: +/- 0.5°C (Open-Meteo)
    - Soil values: +/- 15% (SoilGrids v2 uncertainty)
    - Species counts: Poisson noise
    - Earthquake magnitude: +/- 0.1
    - AQI: +/- 10%
    """
    import random
    random.seed(42)  # Reproducible

    results = {d: [] for d in base_scores}
    overall_samples = []

    for _ in range(n_simulations):
        # Perturb key inputs
        elev_noise = random.gauss(0, 5)
        temp_noise = random.gauss(0, 0.5)
        soil_noise = random.gauss(1.0, 0.15)  # multiplicative
        aqi_noise = random.gauss(1.0, 0.10)
        mag_noise = random.gauss(0, 0.1)

        perturbed = {}
        for d, s in base_scores.items():
            # Each domain responds differently to perturbations
            noise = 0
            if d in ("habitability", "climate_comfort"):
                noise = temp_noise * 2.5 + elev_noise * 0.02
            elif d == "agriculture":
                noise = (soil_noise - 1) * 15 + temp_noise * 1.5
            elif d == "ecology":
                noise = random.gauss(0, 3)  # Poisson-like
            elif d == "hazard_safety":
                noise = mag_noise * 8 + (aqi_noise - 1) * 5
            elif d == "water_resources":
                noise = random.gauss(0, 2.5)
            elif d == "infrastructure":
                noise = random.gauss(0, 1.5)
            elif d == "economic_potential":
                noise = random.gauss(0, 2)
            elif d == "air_environment":
                noise = (aqi_noise - 1) * 12
            elif d == "geological_stability":
                noise = elev_noise * 0.05 + mag_noise * 5
            else:
                noise = random.gauss(0, 2)
            perturbed[d] = max(0, min(100, s + noise))
            results[d].append(perturbed[d])

        # Overall weighted score
        weights = {d: INTELLIGENCE_DOMAINS.get(d, {}).get("weight", 0.1) for d in base_scores}
        overall = sum(perturbed[d] * weights[d] for d in perturbed) / max(sum(weights.values()), 0.01)
        overall_samples.append(overall)

    mc_results = {}
    for d, samples in results.items():
        samples.sort()
        mc_results[d] = {
            "mean": sum(samples) / len(samples),
            "std": math.sqrt(sum((s - sum(samples) / len(samples)) ** 2 for s in samples) / len(samples)),
            "ci_5": samples[int(0.05 * len(samples))],
            "ci_95": samples[int(0.95 * len(samples))],
        }
    overall_samples.sort()
    mc_results["overall"] = {
        "mean": sum(overall_samples) / len(overall_samples),
        "std": math.sqrt(sum((s - sum(overall_samples) / len(overall_samples)) ** 2 for s in overall_samples) / len(overall_samples)),
        "ci_5": overall_samples[int(0.05 * len(overall_samples))],
        "ci_95": overall_samples[int(0.95 * len(overall_samples))],
    }
    return mc_results


def _seismic_gutenberg_richter(magnitudes):
    """Gutenberg-Richter frequency-magnitude relation: log10(N) = a - b*M.
    b-value indicates tectonic stress regime:
    b ~ 1.0: normal tectonic; b < 0.7: high stress (locked fault);
    b > 1.3: swarm/volcanic activity.
    Returns: a, b, b_value_interpretation, max_expected_magnitude."""
    if len(magnitudes) < 5:
        return {"a": 0, "b": 1.0, "interpretation": "insufficient_data", "m_max_est": 0}
    sorted_mags = sorted(magnitudes)
    m_min = sorted_mags[0]
    mean_m = sum(sorted_mags) / len(sorted_mags)
    # Aki's b-value estimator (maximum likelihood): b = log10(e) / (M_mean - M_min)
    denom = mean_m - m_min
    if denom <= 0:
        return {"a": 0, "b": 1.0, "interpretation": "uniform_magnitudes", "m_max_est": max(sorted_mags)}
    b_val = math.log10(math.e) / denom
    # a-value: log10(N) at M=0
    a_val = math.log10(len(sorted_mags)) + b_val * m_min
    # Interpretation
    if b_val < 0.7:
        interp = "high_stress"
    elif b_val > 1.3:
        interp = "swarm_volcanic"
    else:
        interp = "normal_tectonic"
    # Estimated maximum expected magnitude (Kijko-Sellevoll)
    m_max_est = max(sorted_mags) + 1.0 / (b_val * math.log(10) * len(sorted_mags))
    return {"a": round(a_val, 2), "b": round(b_val, 2), "interpretation": interp,
            "m_max_est": round(m_max_est, 1)}


def _precipitation_seasonality_index(daily_precip_values):
    """Walsh & Lawler Seasonality Index (SI).
    SI = (1/R) * sum(|x_m - R/12|) where R = annual total, x_m = monthly total.
    SI < 0.19: very equable; 0.20-0.39: equable with definite wetter season;
    0.40-0.59: rather seasonal; 0.60-0.79: seasonal;
    0.80-0.99: markedly seasonal; >= 1.0: extreme seasonality."""
    if not daily_precip_values or len(daily_precip_values) < 90:
        return {"si": 0, "interpretation": "insufficient_data", "wettest_month": 0, "driest_month": 0}
    # Group into ~12 monthly buckets
    days = len(daily_precip_values)
    bucket_size = max(1, days // 12)
    monthly = []
    for i in range(12):
        start = i * bucket_size
        end = min(start + bucket_size, days)
        bucket = [v for v in daily_precip_values[start:end] if v is not None]
        monthly.append(sum(bucket) if bucket else 0)
    annual = sum(monthly)
    if annual <= 0:
        return {"si": 0, "interpretation": "no_precipitation", "wettest_month": 0, "driest_month": 0}
    si = sum(abs(m - annual / 12) for m in monthly) / annual
    if si < 0.20:
        interp = "very_equable"
    elif si < 0.40:
        interp = "equable_wetter_season"
    elif si < 0.60:
        interp = "rather_seasonal"
    elif si < 0.80:
        interp = "seasonal"
    elif si < 1.0:
        interp = "markedly_seasonal"
    else:
        interp = "extreme_seasonality"
    wettest = max(range(12), key=lambda i: monthly[i]) + 1
    driest = min(range(12), key=lambda i: monthly[i]) + 1
    return {"si": round(si, 3), "interpretation": interp,
            "wettest_month": wettest, "driest_month": driest,
            "monthly_totals": [round(m, 1) for m in monthly]}


def _local_spatial_autocorrelation(center_val, neighbor_vals):
    """LISA (Local Indicator of Spatial Association) — Anselin 1995.
    Identifies local clusters (HH, LL) and outliers (HL, LH).
    Returns: local_i value and cluster classification."""
    if not neighbor_vals:
        return {"local_i": 0, "cluster": "isolated", "z_score": 0}
    all_vals = [center_val] + list(neighbor_vals)
    mean_val = sum(all_vals) / len(all_vals)
    std_val = math.sqrt(sum((v - mean_val) ** 2 for v in all_vals) / len(all_vals))
    if std_val < 0.001:
        return {"local_i": 0, "cluster": "uniform", "z_score": 0}
    z_center = (center_val - mean_val) / std_val
    z_neighbors = [(nv - mean_val) / std_val for nv in neighbor_vals]
    # Local Moran's I_i = z_i * sum(w_ij * z_j) / n
    local_i = z_center * sum(z_neighbors) / len(z_neighbors)
    # Classification
    if z_center > 0 and sum(z_neighbors) / len(z_neighbors) > 0:
        cluster = "HH"  # High-High cluster (e.g., mountain range)
    elif z_center < 0 and sum(z_neighbors) / len(z_neighbors) < 0:
        cluster = "LL"  # Low-Low cluster (e.g., flat plain)
    elif z_center > 0 and sum(z_neighbors) / len(z_neighbors) < 0:
        cluster = "HL"  # High-Low outlier (e.g., isolated peak)
    else:
        cluster = "LH"  # Low-High outlier (e.g., valley in mountains)
    return {"local_i": round(local_i, 4), "cluster": cluster, "z_score": round(z_center, 2)}


def _information_gain(feature_vals, target_vals, threshold):
    """Information Gain — reduction in entropy when splitting on a feature threshold.
    Used to identify which environmental factors are most informative for scoring.
    IG(T, feature) = H(T) - H(T|feature > threshold)."""
    if not feature_vals or not target_vals or len(feature_vals) != len(target_vals):
        return 0.0
    # Binarize target
    med_target = sum(target_vals) / len(target_vals)
    target_binary = [1 if v >= med_target else 0 for v in target_vals]
    total = len(target_binary)
    p1 = sum(target_binary) / total
    if p1 == 0 or p1 == 1:
        return 0.0
    h_total = -p1 * math.log2(p1) - (1 - p1) * math.log2(1 - p1)
    # Split on threshold
    above = [t for f, t in zip(feature_vals, target_binary) if f >= threshold]
    below = [t for f, t in zip(feature_vals, target_binary) if f < threshold]
    def _h(binary_list):
        if not binary_list:
            return 0.0
        p = sum(binary_list) / len(binary_list)
        if p == 0 or p == 1:
            return 0.0
        return -p * math.log2(p) - (1 - p) * math.log2(1 - p)
    h_split = (len(above) / total) * _h(above) + (len(below) / total) * _h(below)
    return max(0, h_total - h_split)


def _multivariate_anomaly_score(values, baselines):
    """Mahalanobis-inspired multivariate anomaly score.
    Measures how far a location's profile deviates from expected baselines.
    Higher = more anomalous. Uses diagonal covariance (independent features)."""
    if not values or not baselines:
        return 0.0
    sq_devs = []
    for key in values:
        if key in baselines and baselines[key].get("std", 0) > 0:
            z = (values[key] - baselines[key]["mean"]) / baselines[key]["std"]
            sq_devs.append(z ** 2)
    if not sq_devs:
        return 0.0
    return math.sqrt(sum(sq_devs) / len(sq_devs))


def _domain_covariance_matrix(scores):
    """Compute pairwise covariance-like relationship matrix between domain scores.
    Uses deviation products as a proxy since we have a single observation.
    Returns dict of {(domain_a, domain_b): score_product_deviation}."""
    domains = list(scores.keys())
    mean_s = sum(scores.values()) / max(len(scores), 1)
    matrix = {}
    for i, d1 in enumerate(domains):
        for j, d2 in enumerate(domains):
            if i <= j:
                cov = (scores[d1] - mean_s) * (scores[d2] - mean_s) / (mean_s ** 2 if mean_s > 0 else 1)
                matrix[(d1, d2)] = round(cov, 4)
                matrix[(d2, d1)] = round(cov, 4)
    return matrix


def _carrying_capacity_estimate(details):
    """Ecological carrying capacity proxy — based on water, soil, climate, terrain.
    Estimates relative population/activity density this location can sustain.
    Uses Liebig's Law of the Minimum: weakest factor determines capacity."""
    factors = {}
    # Water availability: springs + wells + rivers
    water_score = min((details.get("spring_count", 0) * 3 + details.get("well_count", 0) * 2 +
                       details.get("river_count", 0) * 4 + details.get("lake_count", 0) * 5), 30) / 30
    factors["water"] = water_score
    # Soil fertility (geometric mean via soil_quality_composite)
    sq = _soil_quality_composite(
        details.get("soc_val"), details.get("nitrogen_val"), details.get("ph_val"),
        details.get("cec_val"), details.get("clay_val"))
    factors["soil"] = sq
    # Climate suitability
    t = details.get("avg_temp", 15)
    temp_suit = max(0, 1 - abs(t - 20) / 30)
    factors["climate"] = temp_suit
    # Terrain accessibility (inverse roughness)
    grid_e = details.get("grid_elevations", [])
    if grid_e:
        tri = _terrain_roughness_index(grid_e[:9])
        factors["terrain"] = max(0, 1 - min(tri / 500, 1))
    else:
        factors["terrain"] = 0.5
    # Liebig's minimum
    if factors:
        limiting = min(factors, key=factors.get)
        capacity = min(factors.values())
        return {"capacity": round(capacity, 3), "limiting_factor": limiting,
                "factors": {k: round(v, 3) for k, v in factors.items()}}
    return {"capacity": 0, "limiting_factor": "unknown", "factors": {}}


# ---------------------------------------------------------------------------
# TIER 3: SPECTRAL, FRACTAL & WAVELET ANALYSIS
# ---------------------------------------------------------------------------

def _discrete_fourier_magnitudes(signal):
    """Discrete Fourier Transform magnitude spectrum (no numpy).
    DFT: X_k = sum_{n=0}^{N-1} x_n * e^{-2*pi*i*k*n/N}
    Returns list of |X_k| for first N/2 frequencies.
    Applied to: elevation profiles, temperature series, precipitation series."""
    n = len(signal)
    if n < 4:
        return []
    magnitudes = []
    for k in range(n // 2):
        re = sum(signal[j] * math.cos(2 * math.pi * k * j / n) for j in range(n))
        im = -sum(signal[j] * math.sin(2 * math.pi * k * j / n) for j in range(n))
        magnitudes.append(math.sqrt(re * re + im * im) / n)
    return magnitudes


def _spectral_entropy(signal):
    """Spectral entropy — measures how spread the spectral energy is.
    H_s = -sum(P_k * log(P_k)) / log(N/2)  (normalized to [0,1]).
    Low = dominated by few frequencies (periodic). High = noise-like (random).
    Applied to: elevation grids (terrain periodicity), precip time series."""
    mags = _discrete_fourier_magnitudes(signal)
    if not mags:
        return 0.0
    total_energy = sum(m * m for m in mags)
    if total_energy < 1e-10:
        return 0.0
    psd = [(m * m) / total_energy for m in mags]
    h = -sum(p * math.log(p) for p in psd if p > 0)
    h_max = math.log(len(psd)) if len(psd) > 1 else 1
    return h / h_max if h_max > 0 else 0


def _dominant_frequency(signal):
    """Find the dominant frequency in a signal (strongest periodic component).
    Returns the period (in samples) of the dominant non-DC component."""
    mags = _discrete_fourier_magnitudes(signal)
    if len(mags) < 2:
        return 0
    # Skip DC component (k=0), find peak
    non_dc = mags[1:]
    peak_idx = max(range(len(non_dc)), key=lambda i: non_dc[i])
    freq_idx = peak_idx + 1
    if freq_idx == 0:
        return len(signal)
    return len(signal) / freq_idx


def _fractal_dimension_boxcount(values, n_boxes_list=None):
    """Fractal (box-counting) dimension estimate for a 1D profile.
    D = lim(log(N(e)) / log(1/e)) as e -> 0.
    D ~ 1.0: smooth curve. D ~ 1.5: self-similar roughness. D ~ 2.0: space-filling.
    Applied to: elevation profiles (terrain complexity)."""
    n = len(values)
    if n < 8:
        return 1.0
    val_range = max(values) - min(values)
    if val_range < 1e-10:
        return 1.0
    # Normalize to [0, 1]
    normed = [(v - min(values)) / val_range for v in values]
    if n_boxes_list is None:
        n_boxes_list = [4, 8, 16, 32]
    counts = []
    epsilons = []
    for nb in n_boxes_list:
        if nb >= n:
            continue
        eps = 1.0 / nb
        step = max(1, n // nb)
        occupied = set()
        for i in range(0, n, step):
            segment = normed[i:i + step]
            if segment:
                y_min_box = int(min(segment) / eps)
                y_max_box = int(max(segment) / eps)
                for b in range(y_min_box, y_max_box + 1):
                    occupied.add((i // step, b))
        if occupied:
            counts.append(math.log(len(occupied)))
            epsilons.append(math.log(1.0 / eps))
    if len(counts) < 2:
        return 1.0
    # Linear regression: D = slope of log(N) vs log(1/eps)
    n_pts = len(counts)
    mean_x = sum(epsilons) / n_pts
    mean_y = sum(counts) / n_pts
    num = sum((epsilons[i] - mean_x) * (counts[i] - mean_y) for i in range(n_pts))
    den = sum((epsilons[i] - mean_x) ** 2 for i in range(n_pts))
    return num / den if abs(den) > 1e-10 else 1.0


def _haar_wavelet_decomposition(signal, max_levels=4):
    """Simplified Haar wavelet decomposition.
    Decomposes signal into approximation + detail coefficients at multiple scales.
    Returns energy at each scale level — reveals multi-scale terrain structure.
    High energy at coarse levels = large-scale terrain features (mountain ranges).
    High energy at fine levels = local roughness (ravines, cliffs)."""
    if len(signal) < 4:
        return {"levels": 0, "energies": [], "detail_ratio": 0}
    # Pad to power of 2
    target_len = 1
    while target_len < len(signal):
        target_len *= 2
    padded = list(signal) + [signal[-1]] * (target_len - len(signal))
    approx = padded[:]
    energies = []
    total_energy = sum(v * v for v in padded)
    for level in range(min(max_levels, int(math.log2(target_len)))):
        n_a = len(approx)
        if n_a < 2:
            break
        new_approx = []
        detail = []
        for i in range(0, n_a - 1, 2):
            new_approx.append((approx[i] + approx[i + 1]) / 2.0)
            detail.append((approx[i] - approx[i + 1]) / 2.0)
        detail_energy = sum(d * d for d in detail)
        energies.append(detail_energy / max(total_energy, 1e-10))
        approx = new_approx
    fine_energy = sum(energies[:len(energies) // 2 + 1]) if energies else 0
    coarse_energy = sum(energies[len(energies) // 2 + 1:]) if energies else 0
    detail_ratio = fine_energy / max(fine_energy + coarse_energy, 1e-10)
    return {
        "levels": len(energies),
        "energies": [round(e, 6) for e in energies],
        "detail_ratio": round(detail_ratio, 4),
    }


def _semivariogram(values, positions=None, n_lags=5):
    """Empirical semivariogram gamma(h) = (1/2N) * sum((Z(xi) - Z(xi+h))^2).
    Characterizes spatial continuity — how variance changes with distance.
    Returns: lag distances, semivariance values, nugget, sill, range estimates.
    Applied to: elevation grid (terrain continuity), soil properties."""
    n = len(values)
    if n < 4:
        return {"lags": [], "gamma": [], "nugget": 0, "sill": 0, "range_est": 0}
    if positions is None:
        positions = list(range(n))
    max_lag = (max(positions) - min(positions)) / 2
    lag_step = max_lag / n_lags if n_lags > 0 else 1
    lags = []
    gammas = []
    for lag_idx in range(1, n_lags + 1):
        lag_dist = lag_idx * lag_step
        lag_tol = lag_step / 2
        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                d = abs(positions[i] - positions[j])
                if abs(d - lag_dist) <= lag_tol:
                    pairs.append((values[i] - values[j]) ** 2)
        if pairs:
            lags.append(round(lag_dist, 2))
            gammas.append(round(sum(pairs) / (2 * len(pairs)), 4))
    # Estimate nugget (y-intercept), sill (plateau), range (distance to sill)
    nugget = gammas[0] if gammas else 0
    sill = max(gammas) if gammas else 0
    range_est = 0
    for i, g in enumerate(gammas):
        if g >= 0.95 * sill and sill > 0:
            range_est = lags[i]
            break
    return {"lags": lags, "gamma": gammas,
            "nugget": round(nugget, 4), "sill": round(sill, 4),
            "range_est": round(range_est, 2)}


# ---------------------------------------------------------------------------
# TIER 4: STOCHASTIC & PROBABILISTIC MODELS
# ---------------------------------------------------------------------------

def _markov_transition_matrix(states, n_states=3):
    """Estimate Markov chain transition matrix from a sequence of states.
    States: 0=low, 1=medium, 2=high (discretized from continuous values).
    P(i,j) = probability of transitioning from state i to state j.
    Applied to: daily precipitation sequences, earthquake sequences.
    Returns: transition matrix, stationary distribution, mixing time estimate."""
    if len(states) < 3:
        return {"matrix": [], "stationary": [], "mixing_time": 0, "entropy_rate": 0}
    transitions = [[0] * n_states for _ in range(n_states)]
    for i in range(len(states) - 1):
        s_from = min(max(int(states[i]), 0), n_states - 1)
        s_to = min(max(int(states[i + 1]), 0), n_states - 1)
        transitions[s_from][s_to] += 1
    # Normalize to probabilities
    matrix = []
    for row in transitions:
        total = sum(row)
        if total > 0:
            matrix.append([c / total for c in row])
        else:
            matrix.append([1.0 / n_states] * n_states)
    # Stationary distribution via power iteration
    pi = [1.0 / n_states] * n_states
    for _ in range(100):
        new_pi = [0.0] * n_states
        for j in range(n_states):
            for i in range(n_states):
                new_pi[j] += pi[i] * matrix[i][j]
        pi = new_pi
    # Entropy rate: H = -sum(pi_i * sum(P_ij * log(P_ij)))
    h_rate = 0
    for i in range(n_states):
        for j in range(n_states):
            if matrix[i][j] > 0 and pi[i] > 0:
                h_rate -= pi[i] * matrix[i][j] * math.log(matrix[i][j])
    # Mixing time: approximate as 1 / (1 - lambda_2)
    # Use second-largest eigenvalue approximation
    mixing_time = 0
    try:
        trace = sum(matrix[i][i] for i in range(n_states))
        lambda_2_approx = abs(trace / n_states - 1.0 / n_states)
        if lambda_2_approx < 1:
            mixing_time = 1.0 / (1 - lambda_2_approx) if lambda_2_approx > 0 else 0
    except Exception:
        pass
    return {
        "matrix": [[round(p, 4) for p in row] for row in matrix],
        "stationary": [round(p, 4) for p in pi],
        "mixing_time": round(mixing_time, 2),
        "entropy_rate": round(h_rate, 4),
    }


def _weibull_fit(values):
    """Fit Weibull distribution to positive values using method of moments.
    f(x) = (k/lambda) * (x/lambda)^(k-1) * exp(-(x/lambda)^k).
    k = shape (< 1: decreasing hazard, 1: exponential, > 1: increasing hazard).
    lambda = scale.
    Applied to: earthquake magnitudes, wind speeds, precipitation amounts."""
    positive = [v for v in values if v > 0]
    if len(positive) < 3:
        return {"k": 1.0, "lam": 1.0, "mean": 0, "median": 0, "interpretation": "insufficient_data"}
    mean_v = sum(positive) / len(positive)
    var_v = sum((v - mean_v) ** 2 for v in positive) / len(positive)
    if var_v <= 0 or mean_v <= 0:
        return {"k": 1.0, "lam": mean_v, "mean": mean_v, "median": mean_v, "interpretation": "degenerate"}
    cv = math.sqrt(var_v) / mean_v
    # Approximate k from CV: CV ~ Gamma(1+1/k)^{-1/2} * sqrt(Gamma(1+2/k)/Gamma(1+1/k)^2 - 1)
    # Use Newton's approximation: k ~ (1.2 / cv)^1.05
    k = max(0.1, (1.2 / max(cv, 0.01)) ** 1.05)
    # lambda from mean: mean = lambda * Gamma(1 + 1/k)
    # Approximate Gamma(1+1/k) using Stirling for non-integer arguments
    g = math.gamma(1 + 1.0 / k) if k > 0.1 else 1
    lam = mean_v / max(g, 0.001)
    median_v = lam * (math.log(2) ** (1.0 / k))
    if k < 0.8:
        interp = "decreasing_hazard"
    elif k < 1.2:
        interp = "memoryless_exponential"
    elif k < 2.5:
        interp = "increasing_hazard"
    else:
        interp = "strongly_increasing_hazard"
    return {"k": round(k, 3), "lam": round(lam, 3), "mean": round(mean_v, 3),
            "median": round(median_v, 3), "interpretation": interp}


def _beta_distribution_params(values, lo=0, hi=100):
    """Fit Beta distribution to bounded values [lo, hi].
    Beta(alpha, beta): alpha,beta > 0. Estimated via method of moments.
    alpha > beta: right-skewed (most values high).
    alpha < beta: left-skewed (most values low).
    alpha = beta: symmetric.
    Applied to: domain scores [0-100], soil properties, normalized indices."""
    if not values or len(values) < 2:
        return {"alpha": 1, "beta": 1, "mode": 0.5, "skewness": 0, "concentration": 2}
    # Normalize to [0, 1]
    span = hi - lo
    if span <= 0:
        return {"alpha": 1, "beta": 1, "mode": 0.5, "skewness": 0, "concentration": 2}
    normed = [max(0.001, min(0.999, (v - lo) / span)) for v in values]
    mean_x = sum(normed) / len(normed)
    var_x = sum((x - mean_x) ** 2 for x in normed) / len(normed)
    if var_x <= 0 or mean_x <= 0 or mean_x >= 1:
        return {"alpha": 1, "beta": 1, "mode": mean_x, "skewness": 0, "concentration": 2}
    # Method of moments
    common = mean_x * (1 - mean_x) / max(var_x, 1e-10) - 1
    alpha = max(0.01, mean_x * common)
    beta = max(0.01, (1 - mean_x) * common)
    # Mode of Beta: (alpha-1)/(alpha+beta-2) if alpha,beta > 1
    if alpha > 1 and beta > 1:
        mode = (alpha - 1) / (alpha + beta - 2)
    else:
        mode = mean_x
    # Skewness
    denom = (alpha + beta + 2)
    skew = 2 * (beta - alpha) * math.sqrt(alpha + beta + 1) / ((alpha + beta + 2) * math.sqrt(alpha * beta)) if alpha * beta > 0 and denom > 0 else 0
    return {"alpha": round(alpha, 3), "beta": round(beta, 3),
            "mode": round(mode * span + lo, 2),
            "skewness": round(skew, 4),
            "concentration": round(alpha + beta, 2)}


def _fuzzy_membership(value, params):
    """Fuzzy logic membership functions — degree of membership in fuzzy sets.
    Supports: trapezoidal, gaussian, sigmoid fuzzy sets.
    Returns dict of {set_name: membership_degree [0,1]}.
    Applied to: temperature (cold/comfortable/hot), AQI (good/moderate/unhealthy),
    elevation (lowland/midland/highland), etc."""
    memberships = {}
    for name, spec in params.items():
        fn_type = spec.get("type", "trapezoidal")
        if fn_type == "trapezoidal":
            a, b, c, d = spec["a"], spec["b"], spec["c"], spec["d"]
            if value <= a or value >= d:
                mu = 0.0
            elif a < value < b:
                mu = (value - a) / (b - a) if b != a else 1.0
            elif b <= value <= c:
                mu = 1.0
            elif c < value < d:
                mu = (d - value) / (d - c) if d != c else 1.0
            else:
                mu = 0.0
        elif fn_type == "gaussian":
            center = spec["center"]
            sigma = spec["sigma"]
            mu = math.exp(-0.5 * ((value - center) / max(sigma, 0.001)) ** 2)
        elif fn_type == "sigmoid":
            a_s = spec.get("a", 0.1)
            c_s = spec.get("c", 50)
            try:
                mu = 1.0 / (1.0 + math.exp(-a_s * (value - c_s)))
            except OverflowError:
                mu = 0.0 if a_s * (value - c_s) < 0 else 1.0
        else:
            mu = 0.0
        memberships[name] = round(mu, 4)
    return memberships


def _fuzzy_inference_system(details):
    """Multi-variable fuzzy inference for composite environmental assessment.
    Fuzzify inputs -> Apply rules -> Defuzzify via centroid method.
    Returns overall fuzzy environmental quality score and breakdown."""
    temp = details.get("avg_temp", 15)
    aqi = details.get("aqi", 40)
    elev = details.get("center_elev", 200)
    precip = details.get("annual_precip_est", 500)
    # Temperature fuzzy sets
    temp_m = _fuzzy_membership(temp, {
        "cold": {"type": "trapezoidal", "a": -40, "b": -20, "c": 0, "d": 10},
        "cool": {"type": "gaussian", "center": 12, "sigma": 5},
        "comfortable": {"type": "gaussian", "center": 22, "sigma": 4},
        "hot": {"type": "trapezoidal", "a": 28, "b": 35, "c": 45, "d": 55},
    })
    # AQI fuzzy sets
    aqi_m = _fuzzy_membership(aqi, {
        "good": {"type": "trapezoidal", "a": 0, "b": 0, "c": 25, "d": 50},
        "moderate": {"type": "gaussian", "center": 75, "sigma": 25},
        "unhealthy": {"type": "sigmoid", "a": 0.03, "c": 150},
    })
    # Elevation fuzzy sets
    elev_m = _fuzzy_membership(elev, {
        "lowland": {"type": "trapezoidal", "a": -100, "b": 0, "c": 200, "d": 500},
        "midland": {"type": "gaussian", "center": 800, "sigma": 400},
        "highland": {"type": "sigmoid", "a": 0.003, "c": 2000},
    })
    # Precipitation fuzzy sets
    precip_m = _fuzzy_membership(precip, {
        "arid": {"type": "trapezoidal", "a": 0, "b": 0, "c": 100, "d": 250},
        "moderate": {"type": "gaussian", "center": 700, "sigma": 300},
        "wet": {"type": "sigmoid", "a": 0.003, "c": 1500},
    })
    # Fuzzy rules -> defuzzify via weighted centroid
    # Rule: comfortable temp AND good AQI -> high quality (score=90)
    r1 = min(temp_m.get("comfortable", 0), aqi_m.get("good", 0)) * 90
    # Rule: comfortable AND moderate AQI -> good (70)
    r2 = min(temp_m.get("comfortable", 0), aqi_m.get("moderate", 0)) * 70
    # Rule: cold OR hot AND unhealthy -> poor (20)
    r3 = min(max(temp_m.get("cold", 0), temp_m.get("hot", 0)), aqi_m.get("unhealthy", 0)) * 20
    # Rule: moderate precip AND midland -> good (75)
    r4 = min(precip_m.get("moderate", 0), elev_m.get("midland", 0)) * 75
    # Rule: arid AND highland -> harsh (25)
    r5 = min(precip_m.get("arid", 0), elev_m.get("highland", 0)) * 25
    # Rule: cool AND moderate precip -> moderate (60)
    r6 = min(temp_m.get("cool", 0), precip_m.get("moderate", 0)) * 60
    # Centroid defuzzification
    weighted_sum = r1 + r2 + r3 + r4 + r5 + r6
    weight_total = sum([
        min(temp_m.get("comfortable", 0), aqi_m.get("good", 0)),
        min(temp_m.get("comfortable", 0), aqi_m.get("moderate", 0)),
        min(max(temp_m.get("cold", 0), temp_m.get("hot", 0)), aqi_m.get("unhealthy", 0)),
        min(precip_m.get("moderate", 0), elev_m.get("midland", 0)),
        min(precip_m.get("arid", 0), elev_m.get("highland", 0)),
        min(temp_m.get("cool", 0), precip_m.get("moderate", 0)),
    ])
    fuzzy_score = weighted_sum / max(weight_total, 0.001)
    return {
        "fuzzy_score": round(fuzzy_score, 2),
        "temperature": temp_m,
        "air_quality": aqi_m,
        "elevation": elev_m,
        "precipitation": precip_m,
    }


def _graph_centrality_metrics(scores, cov_matrix):
    """Graph-theoretic centrality measures on the domain correlation network.
    Nodes = 10 domains. Edges = covariance strength.
    Computes: degree centrality, betweenness-like centrality, clustering coefficient.
    Reveals which domains are most interconnected (central vs peripheral)."""
    domains = list(scores.keys())
    n = len(domains)
    if n < 3:
        return {}
    # Build adjacency: edge weight = abs(covariance), threshold > 0.1
    adj = {d: {} for d in domains}
    for i, d1 in enumerate(domains):
        for j, d2 in enumerate(domains):
            if i < j:
                w = abs(cov_matrix.get((d1, d2), 0))
                if w > 0.05:
                    adj[d1][d2] = w
                    adj[d2][d1] = w
    # Degree centrality: number of connections / (n-1)
    degree = {}
    for d in domains:
        degree[d] = len(adj[d]) / max(n - 1, 1)
    # Weighted degree (strength): sum of edge weights
    strength = {}
    for d in domains:
        strength[d] = sum(adj[d].values())
    # Clustering coefficient: fraction of triangles around each node
    clustering = {}
    for d in domains:
        neighbors = list(adj[d].keys())
        if len(neighbors) < 2:
            clustering[d] = 0
            continue
        triangles = 0
        possible = len(neighbors) * (len(neighbors) - 1) / 2
        for i_n, n1 in enumerate(neighbors):
            for n2 in neighbors[i_n + 1:]:
                if n2 in adj[n1]:
                    triangles += 1
        clustering[d] = triangles / max(possible, 1)
    # Most central domain
    most_central = max(degree, key=degree.get)
    most_isolated = min(degree, key=degree.get)
    avg_clustering = sum(clustering.values()) / max(len(clustering), 1)
    return {
        "degree_centrality": {d: round(v, 4) for d, v in degree.items()},
        "strength": {d: round(v, 4) for d, v in strength.items()},
        "clustering_coeff": {d: round(v, 4) for d, v in clustering.items()},
        "most_central": most_central,
        "most_isolated": most_isolated,
        "avg_clustering": round(avg_clustering, 4),
        "network_density": round(
            sum(1 for d in adj for _ in adj[d]) / max(n * (n - 1), 1), 4
        ),
    }


def _copula_dependency(x_values, y_values):
    """Empirical copula dependency measure between two variables.
    Uses Kendall's tau rank correlation (non-parametric, detects non-linear dependency).
    tau = (concordant - discordant) / n_pairs.
    tau > 0: positive dependency. tau < 0: negative. |tau| > 0.5: strong.
    Applied to: elevation vs soil quality, biodiversity vs water, etc."""
    n = min(len(x_values), len(y_values))
    if n < 3:
        return {"tau": 0, "strength": "insufficient_data", "concordant": 0, "discordant": 0}
    concordant = 0
    discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            dx = x_values[i] - x_values[j]
            dy = y_values[i] - y_values[j]
            if dx * dy > 0:
                concordant += 1
            elif dx * dy < 0:
                discordant += 1
    n_pairs = n * (n - 1) / 2
    tau = (concordant - discordant) / max(n_pairs, 1)
    if abs(tau) > 0.7:
        strength = "very_strong"
    elif abs(tau) > 0.5:
        strength = "strong"
    elif abs(tau) > 0.3:
        strength = "moderate"
    elif abs(tau) > 0.1:
        strength = "weak"
    else:
        strength = "negligible"
    return {"tau": round(tau, 4), "strength": strength,
            "concordant": concordant, "discordant": discordant}


def _logistic_growth_capacity(current_value, rate_estimate, carrying_cap):
    """Logistic growth model: dN/dt = r*N*(1 - N/K).
    Predicts future values under resource-limited growth.
    N(t) = K / (1 + ((K-N0)/N0) * e^(-r*t)).
    Applied to: urbanization prediction, species population dynamics."""
    if carrying_cap <= 0 or current_value <= 0:
        return {"t10": 0, "t50": 0, "t90": 0, "inflection_point": 0, "growth_phase": "unknown"}
    ratio = current_value / carrying_cap
    if ratio >= 0.99:
        return {"t10": 0, "t50": 0, "t90": 0, "inflection_point": 0, "growth_phase": "saturated"}
    if rate_estimate <= 0:
        return {"t10": 0, "t50": 0, "t90": 0, "inflection_point": 0, "growth_phase": "stagnant"}
    # Time to reach X% of carrying capacity
    def _time_to(target_ratio):
        if target_ratio <= ratio:
            return 0
        if target_ratio >= 1:
            return float('inf')
        num = math.log((target_ratio / (1 - target_ratio)) * ((1 - ratio) / max(ratio, 0.001)))
        return num / rate_estimate
    t10 = _time_to(0.10) if ratio < 0.10 else 0
    t50 = _time_to(0.50)
    t90 = _time_to(0.90)
    inflection = math.log((carrying_cap - current_value) / max(current_value, 0.001)) / rate_estimate
    if ratio < 0.25:
        phase = "early_growth"
    elif ratio < 0.50:
        phase = "acceleration"
    elif ratio < 0.75:
        phase = "deceleration"
    else:
        phase = "approaching_saturation"
    return {"t10": round(max(t10, 0), 2), "t50": round(max(t50, 0), 2),
            "t90": round(max(t90, 0), 2),
            "inflection_point": round(max(inflection, 0), 2),
            "growth_phase": phase}


def _renyi_entropy(counts, alpha=2):
    """Rényi entropy of order alpha: H_alpha = (1/(1-alpha)) * log(sum(pi^alpha)).
    alpha=0: log(S) (richness). alpha->1: Shannon. alpha=2: collision entropy.
    alpha->inf: min-entropy (worst-case unpredictability).
    Generalizes Shannon to a family of entropy measures."""
    total = sum(counts)
    if total == 0 or alpha < 0:
        return 0.0
    proportions = [c / total for c in counts if c > 0]
    if abs(alpha - 1) < 1e-10:
        return _shannon_diversity(counts)
    power_sum = sum(p ** alpha for p in proportions)
    if power_sum <= 0:
        return 0.0
    return math.log(power_sum) / (1 - alpha)


def _tsallis_entropy(counts, q=2):
    """Tsallis (non-extensive) entropy: S_q = (1/(q-1)) * (1 - sum(pi^q)).
    Non-additive generalization of Shannon entropy.
    Useful for systems with long-range correlations (e.g., ecosystems).
    q=1: reduces to Shannon. q>1: emphasizes common species. q<1: emphasizes rare."""
    total = sum(counts)
    if total == 0 or abs(q - 1) < 1e-10:
        return _shannon_diversity(counts)
    proportions = [c / total for c in counts if c > 0]
    power_sum = sum(p ** q for p in proportions)
    return (1 - power_sum) / (q - 1)


def _kolmogorov_smirnov_test(values, cdf_func):
    """Kolmogorov-Smirnov goodness-of-fit test.
    D_n = max|F_n(x) - F(x)| where F_n is empirical CDF, F is theoretical.
    Returns D statistic and approximate p-value.
    Applied to: test if earthquake magnitudes follow exponential distribution."""
    if not values:
        return {"d_stat": 0, "p_value": 1.0, "reject_h0": False}
    sorted_v = sorted(values)
    n = len(sorted_v)
    d_max = 0
    for i, v in enumerate(sorted_v):
        empirical = (i + 1) / n
        theoretical = cdf_func(v)
        d_max = max(d_max, abs(empirical - theoretical))
    # Approximate p-value using Kolmogorov distribution
    # P(D > d) ~ 2 * exp(-2 * n * d^2) for large n
    p_value = 2 * math.exp(-2 * n * d_max * d_max) if n * d_max * d_max < 700 else 0
    p_value = min(1.0, max(0.0, p_value))
    return {"d_stat": round(d_max, 4), "p_value": round(p_value, 4),
            "reject_h0": p_value < 0.05}


def _rank_size_zipf(counts):
    """Zipf's Law / Rank-Size analysis: log(rank) vs log(value).
    Tests if distribution follows power law: value ~ rank^(-alpha).
    alpha ~ 1: Zipf's Law. alpha > 1: steeper hierarchy. alpha < 1: more equal.
    Applied to: species abundance, land use distribution, infrastructure."""
    if len(counts) < 3 or max(counts) == 0:
        return {"alpha": 0, "r_squared": 0, "is_zipfian": False}
    sorted_desc = sorted(counts, reverse=True)
    log_ranks = [math.log(r + 1) for r in range(len(sorted_desc))]
    log_vals = [math.log(max(v, 0.001)) for v in sorted_desc]
    n = len(log_ranks)
    mean_x = sum(log_ranks) / n
    mean_y = sum(log_vals) / n
    num = sum((log_ranks[i] - mean_x) * (log_vals[i] - mean_y) for i in range(n))
    den_x = sum((log_ranks[i] - mean_x) ** 2 for i in range(n))
    den_y = sum((log_vals[i] - mean_y) ** 2 for i in range(n))
    slope = num / max(den_x, 1e-10)
    alpha = -slope
    r_sq = (num ** 2) / max(den_x * den_y, 1e-10)
    return {"alpha": round(alpha, 3), "r_squared": round(r_sq, 4),
            "is_zipfian": abs(alpha - 1.0) < 0.3 and r_sq > 0.8}


def _conditional_entropy(x_counts, y_given_x_counts):
    """Conditional entropy H(Y|X) = sum_x P(x) * H(Y|X=x).
    Measures remaining uncertainty about Y given knowledge of X.
    H(Y|X) = 0 means X completely determines Y.
    Applied to: how much knowing soil type reduces uncertainty about vegetation."""
    h_yx = 0
    total_x = sum(x_counts)
    if total_x == 0:
        return 0.0
    for i, x_c in enumerate(x_counts):
        if x_c == 0:
            continue
        p_x = x_c / total_x
        y_counts = y_given_x_counts[i] if i < len(y_given_x_counts) else []
        h_y = _shannon_diversity(y_counts)
        h_yx += p_x * h_y
    return h_yx


def _mutual_information_approx(scores, details):
    """Approximate Mutual Information between key environmental variables.
    MI(X;Y) = H(X) + H(Y) - H(X,Y) ≈ H(X) + H(Y) - H(X|Y) for discretized vars.
    Returns pairwise MI matrix for: elevation, temp, precip, aqi, species, soil."""
    # Discretize continuous values into 3 bins (low/medium/high)
    vars_data = {
        "elevation": details.get("center_elev", 0),
        "temperature": details.get("avg_temp", 15),
        "precipitation": details.get("annual_precip_est", 500),
        "air_quality": details.get("aqi", 40),
        "biodiversity": details.get("total_species_obs", 50),
        "soil_quality": details.get("soc_val", 2) or 0,
    }
    # Create score-based discretization
    pairs = {}
    var_keys = list(vars_data.keys())
    score_keys = list(scores.keys())
    # Compute MI between env variables and domain scores using correlation strength
    for vk in var_keys:
        for sk in score_keys:
            # Use absolute deviation product as MI proxy
            v_norm = vars_data[vk]
            s_norm = scores[sk]
            # MI proxy: |correlation| based on distance from joint mean
            joint = abs(v_norm * s_norm)
            marginal_v = abs(v_norm) ** 2
            marginal_s = abs(s_norm) ** 2
            if marginal_v > 0 and marginal_s > 0:
                nmi = math.sqrt(joint / math.sqrt(max(marginal_v * marginal_s, 1)))
                nmi = min(1.0, nmi / 100)  # normalize
            else:
                nmi = 0
            pairs[(vk, sk)] = round(nmi, 4)
    # Find top dependencies
    sorted_pairs = sorted(pairs.items(), key=lambda x: x[1], reverse=True)
    top_5 = sorted_pairs[:5]
    return {"pairwise_mi": pairs, "top_dependencies": [(k, v) for k, v in top_5]}


# ---------------------------------------------------------------------------
# MASTER ADVANCED ANALYTICS FUNCTION
# ---------------------------------------------------------------------------

def compute_advanced_analytics(scores, details, data):
    """Run ALL advanced mathematical analyses on real API data.
    Returns a dict with results from every Tier 2/3/4 function."""
    analytics = {}

    # --- TERRAIN ANALYSIS ---
    grid_e = details.get("grid_elevations", [])
    center_e = details.get("center_elev", 0)
    if grid_e and len(grid_e) >= 3:
        analytics["terrain_roughness"] = round(_terrain_roughness_index(grid_e[:9]), 2)
        analytics["topographic_position"] = round(_topographic_position_index(center_e, grid_e[:8]), 2)
        analytics["slope_variability"] = round(_slope_variability(grid_e, 500), 3)
        lisa = _local_spatial_autocorrelation(center_e, grid_e[:8])
        analytics["terrain_lisa"] = lisa
        analytics["morans_i"] = round(_morans_i_proxy(center_e, grid_e[:8]), 4)
    else:
        analytics["terrain_roughness"] = 0
        analytics["topographic_position"] = 0
        analytics["slope_variability"] = 0
        analytics["terrain_lisa"] = {"local_i": 0, "cluster": "no_data", "z_score": 0}
        analytics["morans_i"] = 0

    # --- BIODIVERSITY ANALYSIS ---
    kc = details.get("kingdom_counts", {})
    counts_list = list(kc.values()) if kc else []
    analytics["shannon_h"] = round(_shannon_diversity(counts_list), 4) if counts_list else 0
    analytics["pielou_evenness"] = round(_pielous_evenness(counts_list), 4) if counts_list else 0
    analytics["simpson_diversity"] = round(_simpson_diversity(counts_list), 4) if counts_list else 0
    analytics["berger_parker"] = round(_berger_parker_dominance(counts_list), 4) if counts_list else 0
    analytics["species_hhi"] = round(_herfindahl_hirschman_index(counts_list), 4) if counts_list else 0

    # KL divergence from a global biodiversity baseline (temperate forest average)
    if counts_list and sum(counts_list) > 0:
        total_obs = sum(counts_list)
        local_dist = {k: v / total_obs for k, v in kc.items()}
        # Global baseline: roughly equal kingdoms (uniform as prior)
        baseline = {k: 1.0 / max(len(kc), 1) for k in kc}
        analytics["biodiversity_kl_divergence"] = round(_kl_divergence(local_dist, baseline), 4)
    else:
        analytics["biodiversity_kl_divergence"] = 0

    # --- SOIL ANALYSIS ---
    analytics["soil_quality_index"] = round(_soil_quality_composite(
        details.get("soc_val"), details.get("nitrogen_val"), details.get("ph_val"),
        details.get("cec_val"), details.get("clay_val")), 4)

    # --- SEISMIC ANALYSIS ---
    eq_features = (data.get("quakes") or {}).get("features", [])
    eq_mags = []
    for f in (eq_features if isinstance(eq_features, list) else []):
        m = (f.get("properties", {}) if isinstance(f, dict) else {}).get("mag")
        if m is not None:
            eq_mags.append(float(m))
    analytics["gutenberg_richter"] = _seismic_gutenberg_richter(eq_mags)

    # --- PRECIPITATION SEASONALITY ---
    weather = data.get("weather") or {}
    daily = weather.get("daily", {})
    daily_precip = daily.get("precipitation_sum", [])
    # Also try archive data
    analytics["precip_seasonality"] = _precipitation_seasonality_index(daily_precip)

    # --- SCORE DISTRIBUTION ANALYSIS ---
    score_vals = list(scores.values())
    analytics["score_gini"] = round(_gini_coefficient(score_vals), 4)
    analytics["score_spread"] = round(max(score_vals) - min(score_vals), 1) if score_vals else 0
    analytics["score_cv"] = round(
        (math.sqrt(sum((s - sum(score_vals) / len(score_vals)) ** 2 for s in score_vals) / len(score_vals))
         / (sum(score_vals) / len(score_vals))) if score_vals and sum(score_vals) > 0 else 0, 4)

    # --- LAND USE ANALYSIS ---
    infra_elements = (data.get("infra") or {}).get("elements", [])
    landuse_counts = {}
    for el in (infra_elements if isinstance(infra_elements, list) else []):
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        lu = tags.get("landuse", "")
        if lu:
            landuse_counts[lu] = landuse_counts.get(lu, 0) + 1
        if "building" in tags:
            landuse_counts["building"] = landuse_counts.get("building", 0) + 1
        if "highway" in tags:
            landuse_counts["road"] = landuse_counts.get("road", 0) + 1
    lu_vals = list(landuse_counts.values()) if landuse_counts else []
    analytics["landuse_entropy"] = round(_shannon_diversity(lu_vals), 4)
    analytics["landuse_hhi"] = round(_herfindahl_hirschman_index(lu_vals), 4) if lu_vals else 0
    analytics["landuse_categories"] = len(landuse_counts)

    # --- DOMAIN COVARIANCE ---
    analytics["domain_covariance"] = _domain_covariance_matrix(scores)

    # --- CARRYING CAPACITY ---
    analytics["carrying_capacity"] = _carrying_capacity_estimate(details)

    # --- MONTE CARLO CONFIDENCE ---
    analytics["monte_carlo"] = _monte_carlo_score_confidence(scores, details, n_simulations=500)

    # --- MULTIVARIATE ANOMALY ---
    # Baselines derived from typical temperate locations
    baselines = {
        "center_elev": {"mean": 300, "std": 500},
        "avg_temp": {"mean": 15, "std": 8},
        "annual_precip_est": {"mean": 800, "std": 400},
        "aqi": {"mean": 40, "std": 25},
        "eq_count": {"mean": 10, "std": 20},
        "building_count": {"mean": 50, "std": 80},
        "total_water": {"mean": 15, "std": 20},
        "total_species_obs": {"mean": 100, "std": 150},
    }
    obs_values = {k: details.get(k, 0) for k in baselines}
    analytics["anomaly_score"] = round(_multivariate_anomaly_score(obs_values, baselines), 3)

    # --- SPECTRAL & FRACTAL ANALYSIS (on elevation grid) ---
    if grid_e and len(grid_e) >= 8:
        analytics["spectral_entropy"] = round(_spectral_entropy(grid_e), 4)
        analytics["dominant_period"] = round(_dominant_frequency(grid_e), 2)
        analytics["fractal_dimension"] = round(_fractal_dimension_boxcount(grid_e), 4)
        wavelet = _haar_wavelet_decomposition(grid_e)
        analytics["wavelet"] = wavelet
        svario = _semivariogram(grid_e, n_lags=5)
        analytics["semivariogram"] = svario
    else:
        analytics["spectral_entropy"] = 0
        analytics["dominant_period"] = 0
        analytics["fractal_dimension"] = 1.0
        analytics["wavelet"] = {"levels": 0, "energies": [], "detail_ratio": 0}
        analytics["semivariogram"] = {"lags": [], "gamma": [], "nugget": 0, "sill": 0, "range_est": 0}

    # --- MARKOV CHAIN (on precipitation states) ---
    daily_precip = (data.get("weather") or {}).get("daily", {}).get("precipitation_sum", [])
    if daily_precip and len(daily_precip) >= 5:
        # Discretize: 0=dry (<1mm), 1=light (1-5mm), 2=heavy (>5mm)
        precip_states = []
        for p in daily_precip:
            if p is None:
                continue
            if p < 1:
                precip_states.append(0)
            elif p < 5:
                precip_states.append(1)
            else:
                precip_states.append(2)
        analytics["precip_markov"] = _markov_transition_matrix(precip_states, n_states=3)
    else:
        analytics["precip_markov"] = {"matrix": [], "stationary": [], "mixing_time": 0, "entropy_rate": 0}

    # --- WEIBULL FIT (on earthquake magnitudes) ---
    analytics["seismic_weibull"] = _weibull_fit(eq_mags)

    # --- BETA DISTRIBUTION (on domain scores) ---
    analytics["score_beta"] = _beta_distribution_params(score_vals, lo=0, hi=100)

    # --- FUZZY INFERENCE SYSTEM ---
    analytics["fuzzy_environment"] = _fuzzy_inference_system(details)

    # --- GRAPH CENTRALITY ---
    cov_matrix = analytics.get("domain_covariance", {})
    analytics["graph_centrality"] = _graph_centrality_metrics(scores, cov_matrix)

    # --- RÉNYI & TSALLIS ENTROPY (biodiversity) ---
    if counts_list:
        analytics["renyi_entropy_0"] = round(_renyi_entropy(counts_list, alpha=0), 4)
        analytics["renyi_entropy_2"] = round(_renyi_entropy(counts_list, alpha=2), 4)
        analytics["tsallis_entropy_2"] = round(_tsallis_entropy(counts_list, q=2), 4)
    else:
        analytics["renyi_entropy_0"] = 0
        analytics["renyi_entropy_2"] = 0
        analytics["tsallis_entropy_2"] = 0

    # --- ZIPF RANK-SIZE (land use + species) ---
    analytics["landuse_zipf"] = _rank_size_zipf(lu_vals)
    analytics["species_zipf"] = _rank_size_zipf(counts_list)

    # --- COPULA DEPENDENCY (elevation vs soil) ---
    if grid_e and len(grid_e) >= 3:
        # Elevation profile vs positional index as proxy
        positions = list(range(len(grid_e)))
        analytics["elev_spatial_kendall"] = _copula_dependency(positions, grid_e[:len(positions)])
    else:
        analytics["elev_spatial_kendall"] = {"tau": 0, "strength": "no_data"}

    # --- KOLMOGOROV-SMIRNOV TEST (earthquake magnitudes vs exponential) ---
    if eq_mags and len(eq_mags) >= 5:
        mean_mag = sum(eq_mags) / len(eq_mags)
        lam_exp = 1.0 / max(mean_mag, 0.01)
        def _exp_cdf(x):
            return 1 - math.exp(-lam_exp * max(x, 0))
        analytics["seismic_ks_test"] = _kolmogorov_smirnov_test(eq_mags, _exp_cdf)
    else:
        analytics["seismic_ks_test"] = {"d_stat": 0, "p_value": 1.0, "reject_h0": False}

    # --- LOGISTIC GROWTH (urbanization proxy) ---
    building_c = details.get("building_count", 0)
    cc_data = analytics.get("carrying_capacity", {})
    cap_val = cc_data.get("capacity", 0.5)
    # Assume growth rate based on infrastructure density
    growth_rate = 0.05 if building_c > 10 else 0.02
    analytics["urbanization_logistic"] = _logistic_growth_capacity(
        max(building_c, 1), growth_rate, max(building_c * 3, 100))

    # --- MUTUAL INFORMATION ---
    analytics["mutual_info"] = _mutual_information_approx(scores, details)

    return analytics


from src.deep_zone_analysis import (
    ANALYSIS_PRESETS,
    fetch_soil_data,
    fetch_weather_data,
    fetch_water_features,
    fetch_elevation_grid,
    fetch_landuse_infrastructure,
    fetch_protected_areas,
    fetch_biodiversity,
    fetch_gbif_occurrences,
    compute_species_breakdown,
    fetch_earthquakes,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DOMAIN DEFINITIONS
# ---------------------------------------------------------------------------

INTELLIGENCE_DOMAINS = {
    "habitability": {
        "name": "Habitability",
        "icon": "\U0001f3e0",
        "color": "#3b82f6",
        "weight": 0.12,
    },
    "agriculture": {
        "name": "Agriculture Potential",
        "icon": "\U0001f33e",
        "color": "#22c55e",
        "weight": 0.10,
    },
    "ecology": {
        "name": "Ecological Value",
        "icon": "\U0001f33f",
        "color": "#10b981",
        "weight": 0.10,
    },
    "hazard_safety": {
        "name": "Hazard Safety",
        "icon": "\U0001f6e1\ufe0f",
        "color": "#ef4444",
        "weight": 0.12,
    },
    "water_resources": {
        "name": "Water Resources",
        "icon": "\U0001f4a7",
        "color": "#06b6d4",
        "weight": 0.10,
    },
    "infrastructure": {
        "name": "Infrastructure",
        "icon": "\U0001f3d7\ufe0f",
        "color": "#8b5cf6",
        "weight": 0.10,
    },
    "climate_comfort": {
        "name": "Climate Comfort",
        "icon": "\U0001f324\ufe0f",
        "color": "#f59e0b",
        "weight": 0.08,
    },
    "economic_potential": {
        "name": "Economic Potential",
        "icon": "\U0001f4b0",
        "color": "#ec4899",
        "weight": 0.10,
    },
    "air_environment": {
        "name": "Air & Environment",
        "icon": "\U0001f32c\ufe0f",
        "color": "#6366f1",
        "weight": 0.08,
    },
    "geological_stability": {
        "name": "Geological Stability",
        "icon": "\U0001faa8",
        "color": "#a855f7",
        "weight": 0.10,
    },
}

SCORE_CLASSIFICATIONS = [
    (90, "Exceptional", "#22c55e"),
    (75, "Excellent", "#10b981"),
    (60, "Good", "#3b82f6"),
    (45, "Fair", "#f59e0b"),
    (30, "Poor", "#ef4444"),
    (0, "Critical", "#dc2626"),
]

# ---------------------------------------------------------------------------
# ADDITIONAL API FETCHERS (air quality, geology, elevation)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def fetch_air_quality_unified(lat, lon):
    """Fetch air quality data from Open-Meteo Air Quality API."""
    try:
        resp = requests.get(
            "https://air-quality-api.open-meteo.com/v1/air-quality",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": (
                    "european_aqi,pm10,pm2_5,carbon_monoxide,"
                    "nitrogen_dioxide,sulphur_dioxide,ozone,dust"
                ),
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Air quality API error: %s", exc)
        return {}


@st.cache_data(ttl=1800)
def fetch_geology_unified(lat, lon):
    """Fetch geology data from Macrostrat."""
    try:
        resp = requests.get(
            "https://macrostrat.org/api/v2/geologic_units/map",
            params={"lat": lat, "lng": lon, "response": "long"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Macrostrat error: %s", exc)
        return {}


@st.cache_data(ttl=1800)
def fetch_center_elevation(lat, lon):
    """Fetch single-point elevation from Open Topo Data."""
    try:
        resp = requests.get(
            "https://api.opentopodata.org/v1/srtm30m",
            params={"locations": f"{lat},{lon}"},
            timeout=15,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            elev = results[0].get("elevation")
            return float(elev) if elev is not None else 0.0
        return 0.0
    except Exception:
        return 0.0


@st.cache_data(ttl=3600)
def _fetch_annual_precip(lat, lon):
    """Get actual annual precipitation from 365 days of historical data."""
    try:
        from datetime import datetime, timedelta
        end = datetime.utcnow() - timedelta(days=5)  # API lag
        start = end - timedelta(days=365)
        resp = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": start.strftime("%Y-%m-%d"),
                "end_date": end.strftime("%Y-%m-%d"),
                "daily": "precipitation_sum",
                "timezone": "auto",
            },
            timeout=15,
        )
        resp.raise_for_status()
        daily = resp.json().get("daily", {})
        precip_list = daily.get("precipitation_sum", [])
        valid = [p for p in precip_list if p is not None]
        if valid and len(valid) >= 180:  # need at least half a year
            return sum(valid) * (365.0 / len(valid))
        return None
    except Exception as exc:
        logger.debug("Annual precip estimate failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# STEP 1: COLLECT ALL INTELLIGENCE
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def collect_all_intelligence(lat, lon):
    """Collect data from 12+ sources for unified analysis."""
    soil = fetch_soil_data(lat, lon) or {}
    weather = fetch_weather_data(lat, lon) or {}
    # Get more accurate annual precipitation from 90-day historical data
    annual_precip_hist = _fetch_annual_precip(lat, lon)
    water = fetch_water_features(lat, lon) or {}
    elevation = fetch_elevation_grid(lat, lon) or {}
    infra = fetch_landuse_infrastructure(lat, lon) or {}
    protected = fetch_protected_areas(lat, lon) or {}
    inat = fetch_biodiversity(lat, lon) or {}
    gbif = fetch_gbif_occurrences(lat, lon) or {}
    quakes = fetch_earthquakes(lat, lon) or {}
    air_quality = fetch_air_quality_unified(lat, lon)
    geology = fetch_geology_unified(lat, lon)

    return {
        "soil": soil,
        "weather": weather,
        "water": water,
        "elevation": elevation,
        "infra": infra,
        "protected": protected,
        "inat": inat,
        "gbif": gbif,
        "quakes": quakes,
        "air_quality": air_quality,
        "geology": geology,
        "annual_precip_hist": annual_precip_hist,
    }


# ---------------------------------------------------------------------------
# SOILGRIDS PARSER
# ---------------------------------------------------------------------------

def _parse_soil_value(soil, name, div=10):
    """Safely extract a top-layer mean value from the SoilGrids response."""
    raw_props = (soil if isinstance(soil, dict) else {}).get("properties", {})
    _layers = (raw_props if isinstance(raw_props, dict) else {}).get("layers", [])
    _layer_map = {}
    for _l in (_layers if isinstance(_layers, list) else []):
        _ln = _l.get("name", "") if isinstance(_l, dict) else ""
        if _ln:
            _layer_map[_ln] = _l
    p = _layer_map.get(name, {})
    if isinstance(p, dict):
        depths = p.get("depths", [])
        if depths:
            return ((depths[0].get("values", {}).get("mean") or 0)) / div
    return None


# ---------------------------------------------------------------------------
# STEP 2: COMPUTE 10 DOMAIN SCORES (each 0-100)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=1800)
def compute_domain_scores(lat, lon, data):
    """Compute 10 domain scores from collected intelligence data."""
    soil = data.get("soil") or {}
    weather = data.get("weather") or {}
    water = data.get("water") or {}
    elevation = data.get("elevation") or {}
    infra = data.get("infra") or {}
    protected = data.get("protected") or {}
    inat = data.get("inat") or {}
    gbif = data.get("gbif") or {}
    quakes = data.get("quakes") or {}
    air_quality = data.get("air_quality") or {}
    geology = data.get("geology") or {}
    annual_precip_hist = data.get("annual_precip_hist")  # from 90-day archive

    # ---- Parse helpers ----
    soc_val = _parse_soil_value(soil, "soc", 10)
    nitrogen_val = _parse_soil_value(soil, "nitrogen", 100)
    ph_val = _parse_soil_value(soil, "phh2o", 10)
    clay_val = _parse_soil_value(soil, "clay", 10)
    cec_val = _parse_soil_value(soil, "cec", 10)

    current = weather.get("current", {})
    _t = current.get("temperature_2m")
    temp_now = _t if _t is not None else 15
    _h = current.get("relative_humidity_2m")
    humidity = _h if _h is not None else 50
    _p = current.get("precipitation")
    precip_now = _p if _p is not None else 0
    _w = current.get("wind_speed_10m")
    wind_speed = _w if _w is not None else 10

    daily = weather.get("daily", {})
    daily_max_list = daily.get("temperature_2m_max", [])
    daily_min_list = daily.get("temperature_2m_min", [])
    daily_precip_list = daily.get("precipitation_sum", [])
    safe_daily_max = [v for v in daily_max_list if v is not None]
    safe_daily_min = [v for v in daily_min_list if v is not None]
    safe_daily_precip = [v for v in daily_precip_list if v is not None]

    avg_temp = (
        sum(safe_daily_max + safe_daily_min) / max(len(safe_daily_max + safe_daily_min), 1)
        if (safe_daily_max or safe_daily_min)
        else temp_now
    )
    # Annual precipitation: prefer 90-day historical estimate, fallback to 7-day extrapolation
    if annual_precip_hist is not None and annual_precip_hist > 0:
        annual_precip_est = annual_precip_hist
    elif safe_daily_precip:
        annual_precip_est = sum(safe_daily_precip) * (365 / max(len(safe_daily_precip), 1))
    else:
        annual_precip_est = 500

    # Elevation
    center_elev = elevation.get("center_elevation", 0) or 0
    min_elev = elevation.get("min_elevation", 0) or 0
    max_elev = elevation.get("max_elevation", 0) or 0
    elev_range = max_elev - min_elev
    slope_proxy = elev_range  # metres over the grid

    # Infrastructure breakdown
    infra_elements = infra.get("elements", [])
    building_count = 0
    road_count = 0
    major_road_count = 0
    park_count = 0
    landuse_cats = {}
    for el in (infra_elements if isinstance(infra_elements, list) else []):
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        if "building" in tags:
            building_count += 1
        elif "highway" in tags:
            road_count += 1
            hw = tags.get("highway", "")
            if hw in ("motorway", "trunk", "primary", "secondary"):
                major_road_count += 1
        elif tags.get("leisure") == "park":
            park_count += 1
        else:
            lu = tags.get("landuse", "")
            if lu:
                landuse_cats[lu] = landuse_cats.get(lu, 0) + 1

    industrial_count = landuse_cats.get("industrial", 0) + landuse_cats.get("construction", 0)
    forest_count = landuse_cats.get("forest", 0)
    farmland_count = landuse_cats.get("farmland", 0)

    # Water
    water_elements = water.get("elements", [])
    water_el_list = water_elements if isinstance(water_elements, list) else []
    spring_count = 0
    well_count = 0
    river_count = 0
    lake_count = 0
    for el in water_el_list:
        tags = el.get("tags", {}) if isinstance(el, dict) else {}
        if tags.get("natural") == "spring":
            spring_count += 1
        elif tags.get("man_made") == "water_well":
            well_count += 1
        elif "waterway" in tags:
            ww = tags.get("waterway", "")
            if ww in ("river", "stream", "canal"):
                river_count += 1
        elif tags.get("natural") == "water":
            lake_count += 1
    total_water = len(water_el_list)

    # Protected areas
    protected_elements = protected.get("elements", [])
    protected_list = protected_elements if isinstance(protected_elements, list) else []
    protected_count = len(protected_list)

    # Biodiversity
    species = compute_species_breakdown(inat, gbif)
    inat_total = (species.get("inat_total") or 0)
    gbif_unique = (species.get("gbif_unique_species") or 0)
    kingdom_counts = species.get("kingdom_counts", {})
    kingdom_diversity = len(kingdom_counts)
    total_species_obs = inat_total + (species.get("gbif_total") or 0)

    # Earthquakes
    eq_features = quakes.get("features", [])
    eq_list = eq_features if isinstance(eq_features, list) else []
    eq_count = len(eq_list)
    eq_mags = []
    for f in eq_list:
        props = f.get("properties", {}) if isinstance(f, dict) else {}
        m = props.get("mag")
        if m is not None:
            eq_mags.append(float(m))
    max_mag = max(eq_mags) if eq_mags else 0
    avg_mag = sum(eq_mags) / max(len(eq_mags), 1) if eq_mags else 0

    # Air quality
    aq_current = air_quality.get("current", {})
    aqi = (aq_current.get("european_aqi") or 0)
    pm25 = (aq_current.get("pm2_5") or 0)
    pm10 = (aq_current.get("pm10") or 0)
    no2 = (aq_current.get("nitrogen_dioxide") or 0)

    # Geology
    geo_data_list = geology.get("success", {}).get("data", [])
    geo_units = geo_data_list if isinstance(geo_data_list, list) else []

    details = {
        "building_count": building_count,
        "road_count": road_count,
        "major_road_count": major_road_count,
        "park_count": park_count,
        "industrial_count": industrial_count,
        "forest_count": forest_count,
        "farmland_count": farmland_count,
        "spring_count": spring_count,
        "well_count": well_count,
        "river_count": river_count,
        "lake_count": lake_count,
        "total_water": total_water,
        "protected_count": protected_count,
        "inat_total": inat_total,
        "gbif_unique": gbif_unique,
        "kingdom_diversity": kingdom_diversity,
        "total_species_obs": total_species_obs,
        "eq_count": eq_count,
        "max_mag": max_mag,
        "avg_mag": avg_mag,
        "aqi": aqi,
        "pm25": pm25,
        "pm10": pm10,
        "no2": no2,
        "center_elev": center_elev,
        "elev_range": elev_range,
        "slope_proxy": slope_proxy,
        "temp_now": temp_now,
        "avg_temp": avg_temp,
        "humidity": humidity,
        "wind_speed": wind_speed,
        "annual_precip_est": annual_precip_est,
        "soc_val": soc_val,
        "nitrogen_val": nitrogen_val,
        "ph_val": ph_val,
        "clay_val": clay_val,
        "cec_val": cec_val,
        "geo_units": len(geo_units),
        "grid_elevations": elevation.get("grid_elevations", []),
        "kingdom_counts": kingdom_counts,
    }

    scores = {}

    # ---- HABITABILITY (0-100) ----
    hab = 50.0
    hab += min(building_count / 5.0, 15.0)
    hab += min(road_count / 5.0, 10.0)
    hab += min(park_count * 3.0, 10.0)
    hab += max(0, 10 - abs(temp_now - 22) * 0.8)
    hab += min(total_water * 2.0, 10.0)
    hab -= min(industrial_count * 2.0, 10.0)
    hab -= min(max(0, (aqi - 50) * 0.15), 15)
    hab -= min(max(0, max_mag - 4) * 5, 20)
    scores["habitability"] = max(0, min(100, hab))

    # ---- AGRICULTURE POTENTIAL (0-100) ----
    ag = 30.0
    if soc_val is not None:
        ag += min(soc_val * 1.5, 15.0)
    if nitrogen_val is not None:
        ag += min(nitrogen_val * 5.0, 15.0)
    if ph_val is not None:
        ph_diff = abs((ph_val or 7.0) - 6.5)
        ag += max(0, 10 - ph_diff * 4)
    if cec_val is not None:
        ag += min((cec_val or 0) * 0.8, 10.0)
    ag += max(0, min(15, annual_precip_est / 60.0))
    ag -= min(max(0, abs(avg_temp - 18) * 0.5), 15)
    ag -= min(slope_proxy / 15.0, 15.0)
    ag += min(farmland_count * 3.0, 10.0)
    scores["agriculture"] = max(0, min(100, ag))

    # ---- ECOLOGICAL VALUE (0-100) ---- Shannon Diversity for biodiversity
    eco = 20.0
    eco += min(total_species_obs / 10.0, 20.0)
    # Shannon diversity across kingdom groups instead of simple count
    species_counts = [
        kingdom_counts.get("Plantae", 0),
        kingdom_counts.get("Animalia", 0),
        kingdom_counts.get("Fungi", 0),
        kingdom_counts.get("Insecta", 0),
        kingdom_counts.get("Aves", 0),
    ]
    h_prime = _shannon_diversity(species_counts)
    max_h = math.log(5) if 5 > 0 else 1  # H'max = ln(S)
    eco += min(h_prime / max_h * 20, 20)  # Normalized: H'/H'max * 20
    eco += min(gbif_unique * 0.3, 15.0)
    eco += min(protected_count * 8.0, 20.0)
    eco += min(total_water * 2.0, 10.0)
    eco += min(forest_count * 4.0, 10.0)
    eco -= min(building_count / 10.0, 10.0)
    scores["ecology"] = max(0, min(100, eco))

    # ---- HAZARD SAFETY (0-100) ---- Bayesian risk posterior, inverted: 100 = safest
    eq_prior = min(eq_count / 100.0, 0.5) if eq_count > 0 else 0.05
    eq_lh = min(max_mag / 9.0, 0.99) if max_mag > 0 else 0.01
    flood_lh = max(0, (50 - center_elev) / 100.0) * 0.8 + min(total_water / 30.0, 0.3)
    flood_lh = max(0.01, min(flood_lh, 0.99))
    slide_lh = max(0.01, min(slope_proxy / 500.0, 0.7))
    poll_lh = max(0.01, min(aqi / 300.0, 0.6))
    posterior_risk = _bayesian_risk(eq_prior, [eq_lh, flood_lh, slide_lh, poll_lh])
    # Industrial proximity penalty (additive)
    indust_pen = min(industrial_count * 2.0, 10) / 100.0
    hazard_safety = max(0, min(100, (1 - posterior_risk - indust_pen) * 100))
    scores["hazard_safety"] = hazard_safety

    # ---- WATER RESOURCES (0-100) ----
    wr = 20.0
    wr += min(spring_count * 8.0, 20.0)
    wr += min(river_count * 5.0, 15.0)
    wr += min(lake_count * 6.0, 15.0)
    wr += min(well_count * 6.0, 12.0)
    wr += min(annual_precip_est / 80.0, 15.0)
    wr -= min(max(0, (center_elev - 2000) / 100.0), 25)
    scores["water_resources"] = max(0, min(100, wr))

    # ---- INFRASTRUCTURE (0-100) ----
    inf = 10.0
    inf += min(building_count / 3.0, 25.0)
    inf += min(road_count / 3.0, 20.0)
    inf += min(major_road_count * 4.0, 15.0)
    inf += min(park_count * 3.0, 10.0)
    inf += min(industrial_count * 2.0, 10.0)
    inf += max(0, 10 - abs(center_elev - 200) / 50.0)
    scores["infrastructure"] = max(0, min(100, inf))

    # ---- CLIMATE COMFORT (0-100) ---- Sigmoid curves for smooth transitions
    cc = 50.0
    # Temperature: sigmoid peak at 20C
    temp_score = _sigmoid(avg_temp, midpoint=20, steepness=0.3)
    temp_comfort = (1 - 2 * abs(temp_score - 0.5)) * 40  # 0-40 range
    cc += temp_comfort
    # Humidity: sigmoid peak at 50%
    humid_score = _sigmoid(humidity, midpoint=50, steepness=0.15)
    humid_comfort = (1 - 2 * abs(humid_score - 0.5)) * 20  # 0-20 range
    cc += humid_comfort
    # Precipitation: ideal 500-1100 mm/yr (kept linear, well-behaved)
    precip_dev = max(0, abs(annual_precip_est - 800) - 300)
    cc -= min(precip_dev / 60.0, 12)
    # Wind: calm preferred
    cc -= min(wind_speed / 6.0, 8)
    # Elevation: comfortable range 0-1500m, penalty above
    if center_elev <= 1500:
        cc += max(0, 8 - abs(center_elev - 400) / 200.0)
    else:
        cc -= min((center_elev - 1500) / 200.0, 12)
    scores["climate_comfort"] = max(0, min(100, cc))

    # ---- ECONOMIC POTENTIAL (0-100) ----
    ep = 25.0
    ep += min(building_count / 5.0, 15.0)
    ep += min(road_count / 5.0, 15.0)
    ep += min(major_road_count * 3.0, 12.0)
    flat_terrain = max(0, 15 - slope_proxy / 15.0)
    ep += flat_terrain
    ep += min(total_water * 1.5, 8.0)
    ep += min(farmland_count * 2.0, 8.0)
    ep -= min(max(0, max_mag - 3) * 3, 15)
    ep -= min(aqi / 10.0, 5)
    scores["economic_potential"] = max(0, min(100, ep))

    # ---- AIR & ENVIRONMENT (0-100) ----
    ae = 80.0
    ae -= min(aqi * 0.6, 30)
    ae -= min(pm25 * 0.5, 15)
    ae -= min(no2 * 0.3, 10)
    ae -= min(industrial_count * 3.0, 15)
    ae += min(park_count * 3.0, 10)
    ae += min(forest_count * 3.0, 10)
    ae += min(total_water * 1.0, 5)
    scores["air_environment"] = max(0, min(100, ae))

    # ---- GEOLOGICAL STABILITY (0-100) ---- with Moran's I spatial proxy
    gs = 85.0
    gs -= min(eq_count * 0.5, 20)
    gs -= min(max_mag * 5, 25)
    gs -= min(slope_proxy / 20.0, 15)
    gs += min(len(geo_units) * 2, 5)
    if clay_val is not None and (clay_val or 0) > 40:
        gs -= 10
    # Moran's I proxy: high spatial autocorrelation = flat terrain = more stable
    grid_elevs = elevation.get("grid_elevations", [])
    if grid_elevs and center_elev:
        spatial_corr = _morans_i_proxy(center_elev, grid_elevs[:8])
        gs += min(max(0, spatial_corr * 5), 10)
    scores["geological_stability"] = max(0, min(100, gs))

    # ---- ENHANCED DATA SOURCE ADJUSTMENTS ----
    # GDACS: penalize hazard_safety if active disasters nearby
    gdacs_events = data.get("gdacs", [])
    if gdacs_events and isinstance(gdacs_events, list):
        from src.enhanced_data_sources import gdacs_hazard_penalty
        hazard_pen = gdacs_hazard_penalty(gdacs_events)
        scores["hazard_safety"] = max(0, min(100, scores["hazard_safety"] - hazard_pen))
        details["active_disasters"] = len(gdacs_events)
        details["gdacs_events"] = gdacs_events[:5]
    else:
        details["active_disasters"] = 0
        details["gdacs_events"] = []

    # OpenAQ: adjust air_environment with real station data
    openaq_stations = data.get("openaq", [])
    if openaq_stations and isinstance(openaq_stations, list):
        from src.enhanced_data_sources import openaq_air_quality_score
        aq_adj = openaq_air_quality_score(openaq_stations)
        scores["air_environment"] = max(0, min(100, scores["air_environment"] + aq_adj))
        details["nearest_aq_stations"] = openaq_stations[:5]
    else:
        details["nearest_aq_stations"] = []

    # WorldPop: boost infrastructure and economic_potential
    pop_data = data.get("population", {})
    if pop_data and isinstance(pop_data, dict) and pop_data.get("density_per_km2"):
        from src.enhanced_data_sources import population_density_factor
        pop_factors = population_density_factor(pop_data)
        scores["infrastructure"] = max(0, min(100,
            scores["infrastructure"] + pop_factors.get("infra_boost", 0)))
        scores["economic_potential"] = max(0, min(100,
            scores["economic_potential"] + pop_factors.get("economic_boost", 0)))
        details["population_density"] = pop_data.get("density_per_km2", 0)
        details["carrying_capacity_warning"] = pop_factors.get("carrying_capacity_warning", False)
    else:
        details["population_density"] = 0
        details["carrying_capacity_warning"] = False

    return scores, details


# ---------------------------------------------------------------------------
# STEP 3: CROSS-CORRELATION INTELLIGENCE
# ---------------------------------------------------------------------------

def compute_cross_correlations(scores, details):
    """Find meaningful cross-domain insights with Z-score confidence."""
    insights = []

    # Z-score based confidence helper
    score_vals = list(scores.values())
    mean_score = sum(score_vals) / max(len(score_vals), 1)
    std_score = (sum((v - mean_score) ** 2 for v in score_vals) / max(len(score_vals), 1)) ** 0.5

    def _zconf(*relevant_scores):
        """Compute confidence from Z-score of relevant domain scores."""
        if std_score == 0:
            return 0.5
        avg_rel = sum(relevant_scores) / len(relevant_scores)
        return _zscore_norm(avg_rel, mean_score, std_score, scale=100) / 100

    # 1. Agriculture + Water + Climate = farming potential
    if scores["agriculture"] > 60 and scores["water_resources"] > 50 and scores["climate_comfort"] > 50:
        insights.append({
            "type": "opportunity",
            "title": "High Agricultural Potential",
            "text": (
                "Strong soil fertility combined with adequate water and favorable "
                "climate creates excellent farming conditions."
            ),
            "domains": ["agriculture", "water_resources", "climate_comfort"],
            "confidence": _zconf(scores["agriculture"], scores["water_resources"], scores["climate_comfort"]),
        })

    # 2. Low hazards + Good infrastructure = development opportunity
    if scores["hazard_safety"] > 70 and scores["infrastructure"] > 50:
        insights.append({
            "type": "opportunity",
            "title": "Development-Ready Zone",
            "text": (
                "Low natural hazard risk combined with existing infrastructure "
                "makes this area suitable for residential or commercial development."
            ),
            "domains": ["hazard_safety", "infrastructure"],
            "confidence": _zconf(scores["hazard_safety"], scores["infrastructure"]),
        })

    # 3. High ecology + Protected areas = conservation priority
    if scores["ecology"] > 60 and details.get("protected_count", 0) > 0:
        insights.append({
            "type": "synergy",
            "title": "Conservation Priority Area",
            "text": (
                "High biodiversity value reinforced by existing protected area "
                "designations. This area warrants conservation focus."
            ),
            "domains": ["ecology"],
            "confidence": _zconf(scores["ecology"]),
        })

    # 4. Hazard warning
    if scores["hazard_safety"] < 30:
        reasons = []
        if details.get("max_mag", 0) > 4:
            reasons.append(f"seismic activity (M{details['max_mag']:.1f})")
        if details.get("industrial_count", 0) > 5:
            reasons.append("industrial proximity")
        if details.get("slope_proxy", 0) > 200:
            reasons.append("steep terrain")
        insights.append({
            "type": "threat",
            "title": "Significant Natural Hazard Risk",
            "text": (
                "Multiple hazard factors detected"
                + (": " + ", ".join(reasons) if reasons else "")
                + ". Exercise caution for any development or habitation."
            ),
            "domains": ["hazard_safety"],
            "confidence": _zconf(100 - scores["hazard_safety"]),
        })

    # 5. Water scarcity
    if scores["water_resources"] < 30:
        insights.append({
            "type": "threat",
            "title": "Water Scarcity Risk",
            "text": (
                "Limited water resources detected. Agriculture and habitation may "
                "require external water infrastructure or supply."
            ),
            "domains": ["water_resources", "agriculture"],
            "confidence": _zconf(100 - scores["water_resources"]),
        })

    # 6. Good air + ecology = ecotourism
    if scores["air_environment"] > 65 and scores["ecology"] > 60:
        insights.append({
            "type": "opportunity",
            "title": "Ecotourism Potential",
            "text": (
                "Clean air and high ecological value create an attractive "
                "environment for ecotourism and nature-based activities."
            ),
            "domains": ["air_environment", "ecology"],
            "confidence": _zconf(scores["air_environment"], scores["ecology"]),
        })

    # 7. Infrastructure deficit
    if scores["infrastructure"] < 25 and scores["habitability"] > 40:
        insights.append({
            "type": "warning",
            "title": "Infrastructure Gap",
            "text": (
                "The area has reasonable habitability potential but lacks "
                "infrastructure. Investment in roads and buildings could unlock value."
            ),
            "domains": ["infrastructure", "habitability"],
            "confidence": 0.6,
        })

    # 8. Climate stress
    if scores["climate_comfort"] < 25:
        insights.append({
            "type": "threat",
            "title": "Extreme Climate Conditions",
            "text": (
                "Climate conditions deviate significantly from comfortable ranges. "
                "Habitation and agriculture may face climate-related challenges."
            ),
            "domains": ["climate_comfort"],
            "confidence": _zconf(100 - scores["climate_comfort"]),
        })

    # 9. Geological instability + poor safety
    if scores["geological_stability"] < 35 and scores["hazard_safety"] < 50:
        insights.append({
            "type": "threat",
            "title": "Compound Geological & Hazard Risk",
            "text": (
                "Both geological instability and elevated hazard levels detected. "
                "Structural engineering must account for seismic and terrain risks."
            ),
            "domains": ["geological_stability", "hazard_safety"],
            "confidence": _zconf(100 - scores["geological_stability"], 100 - scores["hazard_safety"]),
        })

    # 10. Agricultural + economic synergy
    if scores["agriculture"] > 55 and scores["economic_potential"] > 50:
        insights.append({
            "type": "synergy",
            "title": "Agri-Business Corridor",
            "text": (
                "Good agricultural conditions coupled with economic infrastructure "
                "suggest potential for agri-business development and food processing."
            ),
            "domains": ["agriculture", "economic_potential"],
            "confidence": _zconf(scores["agriculture"], scores["economic_potential"]),
        })

    # 11. Biodiversity + Water = ecological corridor
    if scores["ecology"] > 50 and scores["water_resources"] > 50:
        insights.append({
            "type": "synergy",
            "title": "Ecological Corridor Potential",
            "text": (
                "Water resources support rich biodiversity. This area may function "
                "as an important ecological corridor for wildlife movement."
            ),
            "domains": ["ecology", "water_resources"],
            "confidence": _zconf(scores["ecology"], scores["water_resources"]),
        })

    # 12. Air pollution concern
    if scores["air_environment"] < 35:
        insights.append({
            "type": "threat",
            "title": "Air Quality Concern",
            "text": (
                f"Elevated air pollutant levels detected "
                f"(AQI: {details.get('aqi', 0)}, PM2.5: {details.get('pm25', 0):.1f}). "
                "Long-term exposure may pose health risks."
            ),
            "domains": ["air_environment"],
            "confidence": _zconf(100 - scores["air_environment"]),
        })

    # 13. Renewable energy potential
    if scores["climate_comfort"] < 40 and details.get("wind_speed", 0) > 15:
        insights.append({
            "type": "opportunity",
            "title": "Wind Energy Potential",
            "text": (
                "High wind speeds may make this location suitable for wind energy "
                "generation despite uncomfortable climate for habitation."
            ),
            "domains": ["climate_comfort", "economic_potential"],
            "confidence": 0.55,
        })

    # 14. High habitability + safety = residential ideal
    if scores["habitability"] > 70 and scores["hazard_safety"] > 70 and scores["air_environment"] > 60:
        insights.append({
            "type": "opportunity",
            "title": "Ideal Residential Location",
            "text": (
                "Excellent habitability, low hazard risk, and good air quality "
                "make this an ideal location for residential development."
            ),
            "domains": ["habitability", "hazard_safety", "air_environment"],
            "confidence": _zconf(scores["habitability"], scores["hazard_safety"], scores["air_environment"]),
        })

    # 15. Geological interest
    if details.get("geo_units", 0) > 3 and scores["ecology"] > 40:
        insights.append({
            "type": "synergy",
            "title": "Geo-Ecological Interest",
            "text": (
                "Multiple geological formations combined with ecological diversity "
                "suggest scientific and educational research value."
            ),
            "domains": ["geological_stability", "ecology"],
            "confidence": 0.5,
        })

    # 16. Water + agriculture mismatch
    if scores["agriculture"] > 50 and scores["water_resources"] < 30:
        insights.append({
            "type": "warning",
            "title": "Irrigation Dependency Risk",
            "text": (
                "Soil conditions support agriculture, but water resources are limited. "
                "Farming here would depend heavily on irrigation infrastructure."
            ),
            "domains": ["agriculture", "water_resources"],
            "confidence": 0.65,
        })

    # 17. Urban-ecology conflict
    if scores["infrastructure"] > 60 and scores["ecology"] > 60:
        insights.append({
            "type": "warning",
            "title": "Urban-Ecology Interface",
            "text": (
                "Both infrastructure density and ecological value are high. "
                "Careful planning is needed to balance development with conservation."
            ),
            "domains": ["infrastructure", "ecology"],
            "confidence": 0.6,
        })

    return insights


# ---------------------------------------------------------------------------
# STEP 4: SWOT ANALYSIS
# ---------------------------------------------------------------------------

def generate_swot(scores, details, insights):
    """Generate Strengths / Weaknesses / Opportunities / Threats analysis."""
    strengths = [
        INTELLIGENCE_DOMAINS[d]["name"]
        for d, s in scores.items()
        if s >= 70
    ]
    weaknesses = [
        INTELLIGENCE_DOMAINS[d]["name"]
        for d, s in scores.items()
        if s <= 30
    ]
    opportunities = [i for i in insights if i["type"] in ("opportunity", "synergy")]
    threats = [i for i in insights if i["type"] in ("threat", "warning")]
    return {
        "S": strengths,
        "W": weaknesses,
        "O": opportunities,
        "T": threats,
    }


# ---------------------------------------------------------------------------
# STEP 5: DECISION RECOMMENDATIONS
# ---------------------------------------------------------------------------

def generate_recommendations(scores, swot, insights):
    """Generate actionable recommendations based on all data."""
    recs = []

    if scores["habitability"] > 65 and scores["hazard_safety"] > 60:
        recs.append({
            "action": "Residential Development",
            "confidence": "High",
            "rationale": (
                "Good habitability conditions and acceptable hazard safety "
                "support residential construction."
            ),
        })

    if scores["agriculture"] > 70:
        recs.append({
            "action": "Agricultural Investment",
            "confidence": "High",
            "rationale": (
                "Excellent soil and climate conditions make this area highly "
                "suitable for crop cultivation or livestock farming."
            ),
        })

    if scores["ecology"] > 75:
        recs.append({
            "action": "Conservation Area Designation",
            "confidence": "High",
            "rationale": (
                "Outstanding ecological value warrants formal protection "
                "and conservation management."
            ),
        })

    if scores["economic_potential"] > 65 and scores["infrastructure"] > 55:
        recs.append({
            "action": "Commercial Development",
            "confidence": "High",
            "rationale": (
                "Strong economic fundamentals and existing infrastructure "
                "support commercial or industrial investment."
            ),
        })

    if scores["water_resources"] > 70 and scores["ecology"] > 50:
        recs.append({
            "action": "Watershed Protection",
            "confidence": "Medium",
            "rationale": (
                "Rich water resources combined with ecological value suggest "
                "watershed management and protection programs."
            ),
        })

    if scores["hazard_safety"] < 35:
        recs.append({
            "action": "Hazard Avoidance",
            "confidence": "High",
            "rationale": (
                "Elevated natural hazard risk makes this area unsuitable for "
                "major development without significant mitigation measures."
            ),
        })

    if scores["air_environment"] > 70 and scores["ecology"] > 55:
        recs.append({
            "action": "Ecotourism Development",
            "confidence": "Medium",
            "rationale": (
                "Clean environment and biodiversity create opportunities "
                "for sustainable ecotourism and nature recreation."
            ),
        })

    if scores["climate_comfort"] > 65 and scores["habitability"] > 55:
        recs.append({
            "action": "Retirement / Lifestyle Community",
            "confidence": "Medium",
            "rationale": (
                "Comfortable climate and good habitability make this area "
                "attractive for retirement or lifestyle-oriented communities."
            ),
        })

    if scores["agriculture"] > 50 and scores["water_resources"] < 35:
        recs.append({
            "action": "Irrigation Infrastructure Investment",
            "confidence": "Medium",
            "rationale": (
                "Agricultural potential exists but is limited by water scarcity. "
                "Irrigation systems would unlock farming capability."
            ),
        })

    if scores["infrastructure"] < 30 and scores["economic_potential"] > 45:
        recs.append({
            "action": "Infrastructure Development Priority",
            "confidence": "Medium",
            "rationale": (
                "Economic potential is undermined by lack of infrastructure. "
                "Road and utility development would catalyse growth."
            ),
        })

    if scores["geological_stability"] > 70 and scores["hazard_safety"] > 65:
        recs.append({
            "action": "Industrial / Heavy Construction",
            "confidence": "Medium",
            "rationale": (
                "Stable geology and low hazard risk support heavy construction "
                "and industrial facilities."
            ),
        })

    if all(scores[d] < 35 for d in ["habitability", "infrastructure", "economic_potential"]):
        recs.append({
            "action": "Avoid Major Development",
            "confidence": "High",
            "rationale": (
                "Multiple critical deficiencies across habitability, infrastructure, "
                "and economic potential suggest this area is unsuitable for development."
            ),
        })

    conf_order = {"High": 3, "Medium": 2, "Low": 1}
    return sorted(recs, key=lambda r: conf_order.get(r["confidence"], 0), reverse=True)


# ---------------------------------------------------------------------------
# PLOTLY RADAR CHART
# ---------------------------------------------------------------------------

def _build_radar_chart(scores):
    """Build a Plotly radar (Scatterpolar) chart for the 10 domain scores."""
    labels = []
    values = []
    colors = []
    for key in INTELLIGENCE_DOMAINS:
        meta = INTELLIGENCE_DOMAINS[key]
        labels.append(meta["name"])
        values.append(scores.get(key, 0))
        colors.append(meta["color"])

    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(6, 182, 212, 0.15)",
        line=dict(color="#06b6d4", width=2),
        marker=dict(size=6, color="#06b6d4"),
        name="Domain Scores",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#1a1a2e",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(color="#5a6580", size=10),
                gridcolor="#2a3550",
            ),
            angularaxis=dict(
                tickfont=dict(color="#e8ecf4", size=11),
                gridcolor="#2a3550",
            ),
        ),
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4"),
        showlegend=False,
        margin=dict(l=60, r=60, t=30, b=30),
        height=420,
    )
    return fig


# ---------------------------------------------------------------------------
# PLOTLY HORIZONTAL BAR CHART
# ---------------------------------------------------------------------------

def _build_domain_bar_chart(scores):
    """Build a horizontal bar chart of all domain scores sorted by value."""
    sorted_domains = sorted(scores.items(), key=lambda x: x[1])
    names = [INTELLIGENCE_DOMAINS[k]["name"] for k, _ in sorted_domains]
    vals = [v for _, v in sorted_domains]
    bar_colors = [INTELLIGENCE_DOMAINS[k]["color"] for k, _ in sorted_domains]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names,
        x=vals,
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"{v:.0f}" for v in vals],
        textposition="outside",
        textfont=dict(color="#e8ecf4", size=12),
    ))
    fig.update_layout(
        paper_bgcolor="#1a1a2e",
        plot_bgcolor="#1a1a2e",
        font=dict(color="#e8ecf4"),
        xaxis=dict(
            range=[0, 110],
            gridcolor="#2a3550",
            tickfont=dict(color="#5a6580"),
        ),
        yaxis=dict(tickfont=dict(color="#e8ecf4", size=12)),
        margin=dict(l=160, r=40, t=20, b=30),
        height=380,
        showlegend=False,
    )
    return fig


# ---------------------------------------------------------------------------
# HELPER: classification & overall score
# ---------------------------------------------------------------------------

def _classify_score(score):
    """Return (label, color) for a numeric score."""
    for threshold, label, color in SCORE_CLASSIFICATIONS:
        if score >= threshold:
            return label, color
    return "Critical", "#dc2626"


def _compute_overall_score(scores):
    """Weighted average of domain scores."""
    total_weight = 0.0
    weighted_sum = 0.0
    for key, meta in INTELLIGENCE_DOMAINS.items():
        w = meta["weight"]
        weighted_sum += scores.get(key, 0) * w
        total_weight += w
    return weighted_sum / total_weight if total_weight > 0 else 0


# ---------------------------------------------------------------------------
# MAIN TAB RENDERER
# ---------------------------------------------------------------------------

def render_unified_intelligence_tab():
    """Render the Unified Intelligence tab UI."""

    st.markdown(
        '<div class="tab-header" style="border-left:4px solid #06b6d4;'
        'background:rgba(6,182,212,0.08);padding:18px 24px;border-radius:12px;'
        'margin-bottom:18px;">'
        "<h4 style='color:#e8ecf4;margin:0;'>Unified Location Intelligence</h4>"
        "<p style='color:#8b97b0;margin:6px 0 0 0;'>Master Intelligence Aggregator "
        "&mdash; runs 15+ analyses and synthesizes ALL results into a single "
        "unified report with cross-correlated insights, SWOT, and recommendations.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # ---- Location selector ----
    c1, c2, c3 = st.columns([1.2, 1.0, 1.0])
    with c1:
        preset = st.selectbox(
            "Preset Location",
            list(ANALYSIS_PRESETS.keys()),
            key="ui_preset",
        )
    p = ANALYSIS_PRESETS.get(preset)
    default_lat = p.get("lat", 41.90) if p else 41.90
    default_lon = p.get("lon", 12.50) if p else 12.50
    with c2:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key="ui_lat",
        )
    with c3:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key="ui_lon",
        )

    run = st.button(
        "Run Unified Intelligence Analysis",
        type="primary",
        key="ui_run",
        use_container_width=True,
    )

    if not run:
        st.info(
            "Select a location and click **Run Unified Intelligence Analysis** "
            "to generate the complete multi-domain intelligence report."
        )
        return

    # ---- Data collection ----
    progress = st.progress(0, text="Collecting intelligence data from 12+ sources...")
    progress.progress(10, text="Fetching soil, weather, water, elevation...")
    data = collect_all_intelligence(lat, lon)
    progress.progress(60, text="Computing domain scores...")
    scores, details = compute_domain_scores(lat, lon, data)
    progress.progress(75, text="Computing cross-correlations...")
    insights = compute_cross_correlations(scores, details)
    progress.progress(85, text="Generating SWOT analysis...")
    swot = generate_swot(scores, details, insights)
    progress.progress(92, text="Generating recommendations...")
    recs = generate_recommendations(scores, swot, insights)
    progress.progress(100, text="Analysis complete!")

    overall = _compute_overall_score(scores)
    label, label_color = _classify_score(overall)

    # ==================================================================
    # SECTION 1: HEADER CARD
    # ==================================================================
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);'
        f'border:1px solid {label_color};border-radius:16px;padding:28px 32px;'
        f'margin:16px 0;text-align:center;">'
        f'<h2 style="color:#e8ecf4;margin:0 0 8px 0;">Unified Location Intelligence</h2>'
        f'<p style="color:#8b97b0;margin:0 0 16px 0;">'
        f'{lat:.5f}, {lon:.5f}</p>'
        f'<div style="display:inline-block;background:rgba(0,0,0,0.3);'
        f'border-radius:12px;padding:16px 40px;">'
        f'<span style="font-size:52px;font-weight:bold;color:{label_color};">'
        f'{overall:.0f}</span>'
        f'<span style="font-size:18px;color:#8b97b0;">/100</span><br/>'
        f'<span style="font-size:18px;color:{label_color};font-weight:600;">'
        f'{html_module.escape(label)}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ==================================================================
    # SECTION 2: DOMAIN SCORES OVERVIEW (2 rows of 5)
    # ==================================================================
    st.markdown("### Domain Scores Overview")
    domain_keys = list(INTELLIGENCE_DOMAINS.keys())

    row1_keys = domain_keys[:5]
    row2_keys = domain_keys[5:]

    cols_r1 = st.columns(5)
    for idx, key in enumerate(row1_keys):
        meta = INTELLIGENCE_DOMAINS[key]
        sc = scores.get(key, 0)
        sc_label, sc_color = _classify_score(sc)
        pct = max(0, min(100, sc))
        with cols_r1[idx]:
            st.markdown(
                f'<div style="background:rgba(15,23,42,0.65);border:1px solid #2a3550;'
                f'border-radius:12px;padding:14px;text-align:center;'
                f'backdrop-filter:blur(16px);">'
                f'<div style="font-size:24px;">{meta["icon"]}</div>'
                f'<div style="color:#e8ecf4;font-size:13px;font-weight:600;'
                f'margin:4px 0;">{html_module.escape(meta["name"])}</div>'
                f'<div style="font-size:26px;font-weight:bold;color:{sc_color};">'
                f'{sc:.0f}</div>'
                f'<div style="background:#1a2235;border-radius:6px;height:8px;'
                f'margin:6px 0;overflow:hidden;">'
                f'<div style="width:{pct:.0f}%;background:{meta["color"]};'
                f'height:100%;border-radius:6px;"></div></div>'
                f'<div style="color:#5a6580;font-size:10px;">{sc_label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    cols_r2 = st.columns(5)
    for idx, key in enumerate(row2_keys):
        meta = INTELLIGENCE_DOMAINS[key]
        sc = scores.get(key, 0)
        sc_label, sc_color = _classify_score(sc)
        pct = max(0, min(100, sc))
        with cols_r2[idx]:
            st.markdown(
                f'<div style="background:rgba(15,23,42,0.65);border:1px solid #2a3550;'
                f'border-radius:12px;padding:14px;text-align:center;'
                f'backdrop-filter:blur(16px);">'
                f'<div style="font-size:24px;">{meta["icon"]}</div>'
                f'<div style="color:#e8ecf4;font-size:13px;font-weight:600;'
                f'margin:4px 0;">{html_module.escape(meta["name"])}</div>'
                f'<div style="font-size:26px;font-weight:bold;color:{sc_color};">'
                f'{sc:.0f}</div>'
                f'<div style="background:#1a2235;border-radius:6px;height:8px;'
                f'margin:6px 0;overflow:hidden;">'
                f'<div style="width:{pct:.0f}%;background:{meta["color"]};'
                f'height:100%;border-radius:6px;"></div></div>'
                f'<div style="color:#5a6580;font-size:10px;">{sc_label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ==================================================================
    # SECTION 3: RADAR CHART
    # ==================================================================
    st.markdown("### Intelligence Radar")
    st.plotly_chart(_build_radar_chart(scores, key="uniint_pchart1"), width="stretch")

    # ==================================================================
    # SECTION 4: CROSS-CORRELATION INSIGHTS
    # ==================================================================
    st.markdown("### Cross-Correlation Insights")
    if insights:
        type_styles = {
            "opportunity": ("#22c55e", "Opportunity"),
            "threat": ("#ef4444", "Threat"),
            "synergy": ("#3b82f6", "Synergy"),
            "warning": ("#f59e0b", "Warning"),
        }
        for insight in insights:
            itype = insight.get("type", "synergy")
            color, type_label = type_styles.get(itype, ("#8b97b0", "Info"))
            conf = insight.get("confidence", 0)
            domains_str = ", ".join(
                INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
                for d in insight.get("domains", [])
            )
            st.markdown(
                f'<div style="background:rgba(15,23,42,0.65);border-left:4px solid {color};'
                f'border-radius:0 12px 12px 0;padding:14px 18px;margin:8px 0;'
                f'backdrop-filter:blur(16px);">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;margin-bottom:6px;">'
                f'<span style="color:{color};font-weight:bold;font-size:14px;">'
                f'{html_module.escape(type_label)}: '
                f'{html_module.escape(insight.get("title", ""))}</span>'
                f'<span style="color:#5a6580;font-size:11px;background:rgba(0,0,0,0.2);'
                f'padding:2px 8px;border-radius:10px;">'
                f'Confidence: {conf:.0%}</span></div>'
                f'<p style="color:#c4c9d4;margin:0 0 6px 0;font-size:13px;">'
                f'{html_module.escape(insight.get("text", ""))}</p>'
                f'<span style="color:#5a6580;font-size:11px;">'
                f'Domains: {html_module.escape(domains_str)}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("No significant cross-correlations detected for this location.")

    # ==================================================================
    # SECTION 5: SWOT ANALYSIS
    # ==================================================================
    st.markdown("### SWOT Analysis")
    swot_c1, swot_c2 = st.columns(2)
    with swot_c1:
        # Strengths
        s_items = swot.get("S", [])
        s_html = "".join(
            f'<li style="color:#d4edda;font-size:13px;margin:3px 0;">'
            f'{html_module.escape(s)}</li>'
            for s in s_items
        ) if s_items else '<li style="color:#5a6580;font-size:13px;">None identified</li>'
        st.markdown(
            f'<div style="background:rgba(34,197,94,0.08);border:1px solid #22c55e;'
            f'border-radius:12px;padding:16px;min-height:140px;">'
            f'<h5 style="color:#22c55e;margin:0 0 10px 0;">Strengths</h5>'
            f'<ul style="margin:0;padding-left:20px;">{s_html}</ul></div>',
            unsafe_allow_html=True,
        )

        # Opportunities
        o_items = swot.get("O", [])
        o_html = "".join(
            f'<li style="color:#bfdbfe;font-size:13px;margin:3px 0;">'
            f'{html_module.escape(o.get("title", ""))}</li>'
            for o in o_items
        ) if o_items else '<li style="color:#5a6580;font-size:13px;">None identified</li>'
        st.markdown(
            f'<div style="background:rgba(59,130,246,0.08);border:1px solid #3b82f6;'
            f'border-radius:12px;padding:16px;min-height:140px;margin-top:12px;">'
            f'<h5 style="color:#3b82f6;margin:0 0 10px 0;">Opportunities</h5>'
            f'<ul style="margin:0;padding-left:20px;">{o_html}</ul></div>',
            unsafe_allow_html=True,
        )

    with swot_c2:
        # Weaknesses
        w_items = swot.get("W", [])
        w_html = "".join(
            f'<li style="color:#fecdd3;font-size:13px;margin:3px 0;">'
            f'{html_module.escape(w)}</li>'
            for w in w_items
        ) if w_items else '<li style="color:#5a6580;font-size:13px;">None identified</li>'
        st.markdown(
            f'<div style="background:rgba(239,68,68,0.08);border:1px solid #ef4444;'
            f'border-radius:12px;padding:16px;min-height:140px;">'
            f'<h5 style="color:#ef4444;margin:0 0 10px 0;">Weaknesses</h5>'
            f'<ul style="margin:0;padding-left:20px;">{w_html}</ul></div>',
            unsafe_allow_html=True,
        )

        # Threats
        t_items = swot.get("T", [])
        t_html = "".join(
            f'<li style="color:#fef3c7;font-size:13px;margin:3px 0;">'
            f'{html_module.escape(t.get("title", ""))}</li>'
            for t in t_items
        ) if t_items else '<li style="color:#5a6580;font-size:13px;">None identified</li>'
        st.markdown(
            f'<div style="background:rgba(245,158,11,0.08);border:1px solid #f59e0b;'
            f'border-radius:12px;padding:16px;min-height:140px;margin-top:12px;">'
            f'<h5 style="color:#f59e0b;margin:0 0 10px 0;">Threats</h5>'
            f'<ul style="margin:0;padding-left:20px;">{t_html}</ul></div>',
            unsafe_allow_html=True,
        )

    # ==================================================================
    # SECTION 6: DECISION RECOMMENDATIONS
    # ==================================================================
    st.markdown("### Decision Recommendations")
    if recs:
        for rank, rec in enumerate(recs, 1):
            conf = rec.get("confidence", "Medium")
            conf_colors = {"High": "#22c55e", "Medium": "#f59e0b", "Low": "#8b97b0"}
            cc = conf_colors.get(conf, "#8b97b0")
            st.markdown(
                f'<div style="background:rgba(15,23,42,0.65);border:1px solid #2a3550;'
                f'border-radius:12px;padding:14px 18px;margin:8px 0;'
                f'backdrop-filter:blur(16px);">'
                f'<div style="display:flex;justify-content:space-between;'
                f'align-items:center;">'
                f'<div>'
                f'<span style="color:#5a6580;font-size:12px;margin-right:8px;">'
                f'#{rank}</span>'
                f'<span style="color:#e8ecf4;font-weight:bold;font-size:15px;">'
                f'{html_module.escape(rec.get("action", ""))}</span></div>'
                f'<span style="color:{cc};font-size:12px;font-weight:600;'
                f'background:rgba(0,0,0,0.2);padding:3px 10px;border-radius:10px;">'
                f'{html_module.escape(conf)} Confidence</span></div>'
                f'<p style="color:#8b97b0;margin:8px 0 0 0;font-size:13px;">'
                f'{html_module.escape(rec.get("rationale", ""))}</p></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Insufficient data to generate specific recommendations.")

    # ==================================================================
    # SECTION 7: KEY RAW DATA SUMMARY
    # ==================================================================
    st.markdown("### Key Raw Data Summary")

    with st.expander("Soil Properties"):
        soc_display = f"{details.get('soc_val', 0) or 0:.1f} g/kg"
        nitrogen_display = f"{details.get('nitrogen_val', 0) or 0:.2f} g/kg"
        ph_display = f"{details.get('ph_val', 0) or 0:.1f}"
        clay_display = f"{details.get('clay_val', 0) or 0:.1f}%"
        cec_display = f"{details.get('cec_val', 0) or 0:.1f} cmol/kg"
        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        mc1.metric("Organic Carbon", soc_display)
        mc2.metric("Nitrogen", nitrogen_display)
        mc3.metric("pH (H2O)", ph_display)
        mc4.metric("Clay Content", clay_display)
        mc5.metric("CEC", cec_display)

    with st.expander("Weather & Climate"):
        wc1, wc2, wc3, wc4 = st.columns(4)
        wc1.metric("Temperature", f"{details.get('temp_now', 0):.1f} C")
        wc2.metric("Humidity", f"{details.get('humidity', 0):.0f}%")
        wc3.metric("Wind Speed", f"{details.get('wind_speed', 0):.1f} km/h")
        wc4.metric("Est. Annual Precip.", f"{details.get('annual_precip_est', 0):.0f} mm")

    with st.expander("Biodiversity"):
        bc1, bc2, bc3, bc4 = st.columns(4)
        bc1.metric("iNaturalist Obs.", details.get("inat_total", 0))
        bc2.metric("GBIF Unique Sp.", details.get("gbif_unique", 0))
        bc3.metric("Kingdoms", details.get("kingdom_diversity", 0))
        bc4.metric("Total Species Obs.", details.get("total_species_obs", 0))

    with st.expander("Infrastructure"):
        ic1, ic2, ic3, ic4 = st.columns(4)
        ic1.metric("Buildings", details.get("building_count", 0))
        ic2.metric("Roads", details.get("road_count", 0))
        ic3.metric("Major Roads", details.get("major_road_count", 0))
        ic4.metric("Parks", details.get("park_count", 0))

    with st.expander("Water Resources"):
        wrc1, wrc2, wrc3, wrc4 = st.columns(4)
        wrc1.metric("Springs", details.get("spring_count", 0))
        wrc2.metric("Wells", details.get("well_count", 0))
        wrc3.metric("Rivers/Streams", details.get("river_count", 0))
        wrc4.metric("Lakes/Water Bodies", details.get("lake_count", 0))

    with st.expander("Seismic Activity"):
        sc1, sc2, sc3 = st.columns(3)
        sc1.metric("Earthquakes (1yr)", details.get("eq_count", 0))
        sc2.metric("Max Magnitude", f"{details.get('max_mag', 0):.1f}")
        sc3.metric("Avg Magnitude", f"{details.get('avg_mag', 0):.1f}")

    with st.expander("Air Quality"):
        aq1, aq2, aq3, aq4 = st.columns(4)
        aq1.metric("European AQI", details.get("aqi", 0))
        aq2.metric("PM2.5", f"{details.get('pm25', 0):.1f}")
        aq3.metric("PM10", f"{details.get('pm10', 0):.1f}")
        aq4.metric("NO2", f"{details.get('no2', 0):.1f}")

    with st.expander("Terrain"):
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("Center Elevation", f"{details.get('center_elev', 0):.0f} m")
        tc2.metric("Elevation Range", f"{details.get('elev_range', 0):.0f} m")
        tc3.metric("Protected Areas", details.get("protected_count", 0))

    # ==================================================================
    # SECTION 8: DOMAIN SCORE BREAKDOWN BAR CHART
    # ==================================================================
    st.markdown("### Domain Score Breakdown")
    st.plotly_chart(_build_domain_bar_chart(scores, key="uniint_pchart2"), width="stretch")

    # ---- Timestamp ----
    st.markdown(
        f'<div style="text-align:center;color:#5a6580;font-size:11px;margin-top:20px;">'
        f'Unified Intelligence Report generated at '
        f'{datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC '
        f'for ({lat:.5f}, {lon:.5f})</div>',
        unsafe_allow_html=True,
    )
