"""
Fusion Engine — 8 Multi-Criteria Decision & Evidence Fusion Algorithms
for TerraScout AI Fusion Intelligence Console.

All functions are pure math — no API calls, no Streamlit dependencies.
Input: domain scores (dict), details (dict), analytics (dict) from data_hub
       + unified_intelligence.compute_advanced_analytics.
Output: structured dicts ready for UI rendering.

Algorithms:
1. Dempster-Shafer Evidence Fusion
2. TOPSIS Multi-Criteria Ranking
3. AHP Priority Synthesis
4. Risk Propagation Cascade
5. Composite Vulnerability Index (IPCC)
6. Anomaly Severity Ranking
7. Temporal Trend Synthesis
8. ELECTRE Outranking
"""

import math
from itertools import combinations

# ---------------------------------------------------------------------------
# 1. DEMPSTER-SHAFER EVIDENCE FUSION
# ---------------------------------------------------------------------------

def dempster_shafer_fusion(scores, confidence=0.8):
    """Combine 10 domain scores via Dempster-Shafer theory.

    Each domain produces a Basic Probability Assignment (BPA):
      m({favorable}) = score/100 * conf_weight
      m({unfavorable}) = (1-score/100) * conf_weight
      m({theta}) = 1 - conf_weight   (ignorance)

    Pairwise combination via D-S rule; returns fused belief/plausibility.
    """
    domains = sorted(scores.keys())
    if not domains:
        return {
            "fused_belief": 0.5, "fused_plausibility": 0.5,
            "conflict_level": 0, "uncertainty_gap": 0,
            "conflict_matrix": {}, "domain_beliefs": {},
        }

    conf_weight = max(0.1, min(1.0, confidence))

    # Build BPAs: each domain -> {fav, unfav, theta}
    bpas = {}
    for d in domains:
        s = max(0, min(100, scores[d])) / 100.0
        m_fav = s * conf_weight
        m_unfav = (1.0 - s) * conf_weight
        m_theta = 1.0 - conf_weight
        bpas[d] = {"fav": m_fav, "unfav": m_unfav, "theta": m_theta}

    # Pairwise conflict matrix
    conflict_matrix = {}
    for d1, d2 in combinations(domains, 2):
        b1, b2 = bpas[d1], bpas[d2]
        k = b1["fav"] * b2["unfav"] + b1["unfav"] * b2["fav"]
        conflict_matrix[(d1, d2)] = round(k, 4)
        conflict_matrix[(d2, d1)] = round(k, 4)

    # Sequential D-S combination of all domains
    combined_fav = bpas[domains[0]]["fav"]
    combined_unfav = bpas[domains[0]]["unfav"]
    combined_theta = bpas[domains[0]]["theta"]
    total_conflict = 0.0

    for d in domains[1:]:
        b = bpas[d]
        # Intersection combinations
        new_fav = (combined_fav * b["fav"]
                   + combined_fav * b["theta"]
                   + combined_theta * b["fav"])
        new_unfav = (combined_unfav * b["unfav"]
                     + combined_unfav * b["theta"]
                     + combined_theta * b["unfav"])
        k = (combined_fav * b["unfav"]
             + combined_unfav * b["fav"])
        new_theta = combined_theta * b["theta"]

        total_conflict = 1.0 - (1.0 - total_conflict) * (1.0 - k)

        norm = 1.0 - k
        if norm > 1e-10:
            combined_fav = new_fav / norm
            combined_unfav = new_unfav / norm
            combined_theta = new_theta / norm
        else:
            combined_fav = 0.5
            combined_unfav = 0.5
            combined_theta = 0.0

    # Belief = m(fav), Plausibility = m(fav) + m(theta)
    fused_belief = round(combined_fav, 4)
    fused_plausibility = round(combined_fav + combined_theta, 4)

    # Per-domain belief (for charts)
    domain_beliefs = {}
    for d in domains:
        domain_beliefs[d] = {
            "belief": round(bpas[d]["fav"], 4),
            "plausibility": round(bpas[d]["fav"] + bpas[d]["theta"], 4),
        }

    return {
        "fused_belief": fused_belief,
        "fused_plausibility": fused_plausibility,
        "conflict_level": round(total_conflict, 4),
        "uncertainty_gap": round(fused_plausibility - fused_belief, 4),
        "conflict_matrix": conflict_matrix,
        "domain_beliefs": domain_beliefs,
    }


# ---------------------------------------------------------------------------
# 2. TOPSIS — Multi-Criteria Scenario Ranking
# ---------------------------------------------------------------------------

def topsis_scenario_ranking(scenario_results, scores):
    """Rank scenarios using TOPSIS (Technique for Order Preference
    by Similarity to Ideal Solution).

    scenario_results: dict {scenario_key: {overall_score, criteria: {name: score}}}
    scores: domain scores used to derive weights.
    Returns ranked list of scenarios with closeness coefficients.
    """
    if not scenario_results:
        return []

    scenario_keys = list(scenario_results.keys())
    # Collect all criteria names across scenarios
    all_criteria = set()
    for sr in scenario_results.values():
        for c in (sr.get("criteria") or {}):
            all_criteria.add(c)
    all_criteria = sorted(all_criteria)
    if not all_criteria:
        return []

    n_scenarios = len(scenario_keys)
    n_criteria = len(all_criteria)

    # Build decision matrix  rows=scenarios, cols=criteria
    matrix = []
    for sk in scenario_keys:
        row = []
        crit = scenario_results[sk].get("criteria", {})
        for c in all_criteria:
            val = crit.get(c, {}).get("score", 50) if isinstance(crit.get(c), dict) else 50
            row.append(val)
        matrix.append(row)

    # Normalize: r_ij = x_ij / sqrt(sum(x_ij^2))
    norm_matrix = []
    for i in range(n_scenarios):
        norm_row = []
        for j in range(n_criteria):
            col_sum_sq = sum(matrix[k][j] ** 2 for k in range(n_scenarios))
            denom = math.sqrt(col_sum_sq) if col_sum_sq > 0 else 1.0
            norm_row.append(matrix[i][j] / denom)
        norm_matrix.append(norm_row)

    # Equal weights (or could derive from scores)
    weights = [1.0 / n_criteria] * n_criteria

    # Weighted normalized matrix
    v = [[norm_matrix[i][j] * weights[j] for j in range(n_criteria)]
         for i in range(n_scenarios)]

    # Ideal (A+) and anti-ideal (A-) solutions
    a_plus = [max(v[i][j] for i in range(n_scenarios)) for j in range(n_criteria)]
    a_minus = [min(v[i][j] for i in range(n_scenarios)) for j in range(n_criteria)]

    # Distance from ideal and anti-ideal
    results = []
    for i in range(n_scenarios):
        s_plus = math.sqrt(sum((v[i][j] - a_plus[j]) ** 2 for j in range(n_criteria)))
        s_minus = math.sqrt(sum((v[i][j] - a_minus[j]) ** 2 for j in range(n_criteria)))
        denom = s_plus + s_minus
        closeness = s_minus / denom if denom > 0 else 0.5
        simple_avg = sum(matrix[i]) / n_criteria if n_criteria > 0 else 0
        results.append({
            "scenario": scenario_keys[i],
            "closeness": round(closeness, 4),
            "s_plus": round(s_plus, 4),
            "s_minus": round(s_minus, 4),
            "simple_score": round(simple_avg, 1),
            "overall": scenario_results[scenario_keys[i]].get("overall_score", 0),
        })

    results.sort(key=lambda x: x["closeness"], reverse=True)
    for rank, r in enumerate(results, 1):
        r["rank"] = rank
    return results


# ---------------------------------------------------------------------------
# 3. AHP — Analytic Hierarchy Process Priority Synthesis
# ---------------------------------------------------------------------------

def ahp_priority_synthesis(scores):
    """Derive priority weights from domain score covariance
    using AHP-inspired pairwise comparison + power iteration.

    Returns priority weights, weighted composite, consistency ratio.
    """
    domains = sorted(scores.keys())
    n = len(domains)
    if n < 2:
        return {"weights": {}, "weighted_composite": 0, "consistency_ratio": 0}

    # Build pairwise comparison matrix from score ratios
    A = [[1.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            si = max(scores[domains[i]], 1)
            sj = max(scores[domains[j]], 1)
            ratio = si / sj
            # Clamp to Saaty scale [1/9, 9]
            ratio = max(1.0 / 9, min(9.0, ratio))
            A[i][j] = ratio
            A[j][i] = 1.0 / ratio

    # Power iteration for principal eigenvector
    w = [1.0 / n] * n
    for _ in range(50):
        new_w = [0.0] * n
        for i in range(n):
            for j in range(n):
                new_w[i] += A[i][j] * w[j]
        total = sum(new_w)
        if total > 0:
            w = [x / total for x in new_w]

    # Principal eigenvalue
    aw = [sum(A[i][j] * w[j] for j in range(n)) for i in range(n)]
    lambda_max = sum(aw[i] / w[i] if w[i] > 0 else n for i in range(n)) / n

    # Consistency Index & Ratio
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0
    # Random Index (Saaty) for n=1..15
    ri_table = [0, 0, 0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49, 1.51, 1.48, 1.56, 1.57, 1.59]
    ri = ri_table[min(n, len(ri_table) - 1)]
    cr = ci / ri if ri > 0 else 0

    # Weighted composite score
    weighted_composite = sum(w[i] * scores[domains[i]] for i in range(n))

    weights = {domains[i]: round(w[i], 4) for i in range(n)}
    return {
        "weights": weights,
        "weighted_composite": round(weighted_composite, 2),
        "consistency_ratio": round(cr, 4),
    }


# ---------------------------------------------------------------------------
# 4. RISK PROPAGATION CASCADE
# ---------------------------------------------------------------------------

_CASCADE_GRAPH = {
    "hazard_safety": ["geological_stability", "infrastructure", "economic_potential"],
    "geological_stability": ["hazard_safety", "infrastructure", "agriculture"],
    "water_resources": ["agriculture", "ecology", "habitability"],
    "climate_comfort": ["agriculture", "habitability", "ecology"],
    "agriculture": ["economic_potential", "water_resources"],
    "ecology": ["water_resources", "air_environment"],
    "infrastructure": ["economic_potential", "habitability"],
    "air_environment": ["habitability", "ecology"],
    "economic_potential": ["infrastructure"],
    "habitability": [],
}


def risk_propagation_cascade(scores, details=None):
    """Model systemic risk propagation through inter-domain dependencies.

    R0 = (100 - score) / 100 per domain (standalone risk).
    Iterative propagation: R(t+1) = alpha * P @ R(t) + (1-alpha) * R0
    alpha = 0.4 (propagation strength).
    """
    domains = sorted(scores.keys())
    n = len(domains)
    if n == 0:
        return {"cascade_risk": {}, "amplification": {}, "systemic_score": 0,
                "most_vulnerable_chain": []}

    dom_idx = {d: i for i, d in enumerate(domains)}
    alpha = 0.4

    # Standalone risk
    R0 = [(100 - max(0, min(100, scores.get(d, 50)))) / 100.0 for d in domains]

    # Propagation matrix P[i][j] = weight of domain j's risk propagating to i
    P = [[0.0] * n for _ in range(n)]
    for source, targets in _CASCADE_GRAPH.items():
        si = dom_idx.get(source)
        if si is None:
            continue
        for target in targets:
            ti = dom_idx.get(target)
            if ti is not None:
                # Weight inversely proportional to number of targets
                P[ti][si] = 1.0 / max(len(targets), 1)

    # Iterative cascade
    R = R0[:]
    for _ in range(20):
        new_R = [0.0] * n
        for i in range(n):
            propagated = sum(P[i][j] * R[j] for j in range(n))
            new_R[i] = alpha * propagated + (1.0 - alpha) * R0[i]
            new_R[i] = max(0, min(1, new_R[i]))
        # Check convergence
        if all(abs(new_R[i] - R[i]) < 1e-6 for i in range(n)):
            R = new_R
            break
        R = new_R

    # Amplification factors
    cascade_risk = {domains[i]: round(R[i], 4) for i in range(n)}
    amplification = {}
    for i in range(n):
        amp = R[i] / R0[i] if R0[i] > 0.01 else 1.0
        amplification[domains[i]] = round(amp, 3)

    # Systemic risk = weighted max-norm
    systemic_score = round(max(R) * 100, 1)

    # Most vulnerable chain: trace highest-risk propagation path
    chain = _trace_cascade_chain(domains, R, P, dom_idx)

    return {
        "cascade_risk": cascade_risk,
        "amplification": amplification,
        "systemic_score": systemic_score,
        "most_vulnerable_chain": chain,
        "standalone_risk": {domains[i]: round(R0[i], 4) for i in range(n)},
    }


def _trace_cascade_chain(domains, R, P, dom_idx):
    """Find the chain of highest-risk propagation."""
    if not domains:
        return []
    start = max(range(len(domains)), key=lambda i: R[i])
    chain = [domains[start]]
    visited = {start}
    current = start
    for _ in range(5):
        best_next = -1
        best_flow = 0
        for j in range(len(domains)):
            if j not in visited and P[current][j] > 0:
                flow = P[current][j] * R[j]
                if flow > best_flow:
                    best_flow = flow
                    best_next = j
        if best_next < 0:
            # Try outgoing
            for j in range(len(domains)):
                if j not in visited and P[j][current] > 0:
                    flow = P[j][current] * R[j]
                    if flow > best_flow:
                        best_flow = flow
                        best_next = j
        if best_next < 0:
            break
        chain.append(domains[best_next])
        visited.add(best_next)
        current = best_next
    return chain


# ---------------------------------------------------------------------------
# 5. COMPOSITE VULNERABILITY INDEX (IPCC Framework)
# ---------------------------------------------------------------------------

def composite_vulnerability_index(scores, details=None, analytics=None):
    """IPCC Vulnerability = f(Exposure, Sensitivity, Adaptive Capacity).

    Exposure: hazard inverse, geological instability, climate extremes.
    Sensitivity: soil erodibility, water dependency, ecological fragility.
    Adaptive Capacity: infrastructure, economic potential, water resources.

    V = (E * S) / max(AC, 0.1)   (geometric mean style)
    """
    details = details or {}
    analytics = analytics or {}

    # EXPOSURE (higher = more exposed to hazards)
    hazard_inv = (100 - scores.get("hazard_safety", 50)) / 100.0
    geo_inv = (100 - scores.get("geological_stability", 50)) / 100.0
    climate_ext = abs(scores.get("climate_comfort", 50) - 50) / 50.0  # deviation from moderate
    exposure = (hazard_inv * 0.45 + geo_inv * 0.35 + climate_ext * 0.20)

    # SENSITIVITY (higher = more sensitive to perturbations)
    water_dep = (100 - scores.get("water_resources", 50)) / 100.0
    eco_frag = (100 - scores.get("ecology", 50)) / 100.0
    # Soil erodibility proxy: low SOC + high clay = erodible
    soil_sens = (100 - scores.get("agriculture", 50)) / 100.0
    sensitivity = (water_dep * 0.35 + eco_frag * 0.35 + soil_sens * 0.30)

    # ADAPTIVE CAPACITY (higher = more resilient)
    infra = scores.get("infrastructure", 50) / 100.0
    econ = scores.get("economic_potential", 50) / 100.0
    water = scores.get("water_resources", 50) / 100.0
    adaptive_capacity = (infra * 0.40 + econ * 0.35 + water * 0.25)

    # CVI — geometric approach
    cvi = (exposure * sensitivity) / max(adaptive_capacity, 0.1)
    cvi = min(cvi, 1.0)  # cap at 1

    # Classification
    if cvi < 0.15:
        vclass = "LOW"
    elif cvi < 0.35:
        vclass = "MODERATE"
    elif cvi < 0.60:
        vclass = "HIGH"
    else:
        vclass = "EXTREME"

    # Weakest link
    dims = {"exposure": exposure, "sensitivity": sensitivity, "adaptive_capacity": adaptive_capacity}
    weakest = max(dims, key=lambda k: dims[k] if k != "adaptive_capacity" else 1 - dims[k])

    return {
        "cvi_score": round(cvi, 4),
        "exposure": round(exposure, 4),
        "sensitivity": round(sensitivity, 4),
        "adaptive_capacity": round(adaptive_capacity, 4),
        "vulnerability_class": vclass,
        "weakest_link": weakest,
    }


# ---------------------------------------------------------------------------
# 6. ANOMALY SEVERITY RANKING
# ---------------------------------------------------------------------------

# Global baselines for z-score computation
_BASELINES = {
    "center_elev": {"mean": 300, "std": 500, "domain": "geological_stability", "label": "Elevation"},
    "avg_temp": {"mean": 15, "std": 8, "domain": "climate_comfort", "label": "Temperature"},
    "annual_precip_est": {"mean": 800, "std": 400, "domain": "water_resources", "label": "Annual Precipitation"},
    "aqi": {"mean": 40, "std": 25, "domain": "air_environment", "label": "Air Quality Index"},
    "eq_count": {"mean": 10, "std": 20, "domain": "hazard_safety", "label": "Earthquake Count"},
    "building_count": {"mean": 50, "std": 80, "domain": "infrastructure", "label": "Building Density"},
    "total_water": {"mean": 15, "std": 20, "domain": "water_resources", "label": "Water Features"},
    "total_species_obs": {"mean": 100, "std": 150, "domain": "ecology", "label": "Species Observations"},
    "road_count": {"mean": 30, "std": 40, "domain": "infrastructure", "label": "Road Density"},
    "spring_count": {"mean": 3, "std": 5, "domain": "water_resources", "label": "Spring Count"},
    "ph_val": {"mean": 6.5, "std": 1.0, "domain": "agriculture", "label": "Soil pH"},
    "soc_val": {"mean": 2.0, "std": 1.5, "domain": "agriculture", "label": "Soil Organic Carbon"},
}


def anomaly_severity_ranking(scores, details=None, analytics=None):
    """Rank anomalies by severity (z-score) and impact weight.

    For each metric: z-score vs global baseline.
    Weight = domain_importance * |z-score| * confidence.
    Classification: CRITICAL (|z|>3), WARNING (|z|>2), NOTABLE (|z|>1.5), NORMAL.
    """
    details = details or {}
    analytics = analytics or {}
    anomalies = []

    for key, bl in _BASELINES.items():
        val = details.get(key)
        if val is None:
            continue
        if bl["std"] == 0:
            continue
        z = (val - bl["mean"]) / bl["std"]
        abs_z = abs(z)

        if abs_z < 1.5:
            continue  # NORMAL — skip

        if abs_z >= 3:
            severity = "CRITICAL"
            color = "#ef4444"
        elif abs_z >= 2:
            severity = "WARNING"
            color = "#f59e0b"
        else:
            severity = "NOTABLE"
            color = "#06b6d4"

        direction = "above" if z > 0 else "below"
        action = _anomaly_action(key, z, val, bl)

        anomalies.append({
            "metric": bl["label"],
            "key": key,
            "value": round(val, 2),
            "baseline": bl["mean"],
            "z_score": round(z, 2),
            "abs_z": round(abs_z, 2),
            "severity": severity,
            "color": color,
            "domain": bl["domain"],
            "direction": direction,
            "impact_weight": round(abs_z * 0.5, 2),
            "action": action,
        })

    anomalies.sort(key=lambda a: a["abs_z"], reverse=True)
    return anomalies


def _anomaly_action(key, z, val, bl):
    """Generate recommended action for an anomaly."""
    actions = {
        "center_elev": "Assess terrain accessibility and flood/landslide exposure",
        "avg_temp": "Evaluate thermal comfort and energy demand implications",
        "annual_precip_est": "Review water management and drainage capacity",
        "aqi": "Investigate pollution sources and health exposure risk",
        "eq_count": "Assess structural vulnerability and seismic preparedness",
        "building_count": "Evaluate urbanization pressure and infrastructure gaps",
        "total_water": "Review water resource dependency and drought resilience",
        "total_species_obs": "Evaluate biodiversity conservation priorities",
        "road_count": "Assess transportation connectivity and isolation risk",
        "spring_count": "Evaluate groundwater availability and aquifer status",
        "ph_val": "Assess soil amendment needs for target land use",
        "soc_val": "Evaluate soil carbon sequestration and fertility potential",
    }
    return actions.get(key, "Investigate further and assess operational impact")


# ---------------------------------------------------------------------------
# 7. TEMPORAL TREND SYNTHESIS
# ---------------------------------------------------------------------------

def temporal_trend_synthesis(raw_data=None, analytics=None, scores=None):
    """Synthesize temporal trends from forecast + statistical models.

    Sources:
    - Weather forecast 7-day trend (temperature, precipitation)
    - Markov stationary distribution (precipitation regime)
    - Weibull k (seismic hazard rate: increasing/decreasing)
    - Score-based domain direction inference
    """
    raw_data = raw_data or {}
    analytics = analytics or {}
    scores = scores or {}

    domain_trends = {}

    # --- Weather forecast trend ---
    weather = raw_data.get("weather") or {}
    daily = weather.get("daily", {})
    temps = [t for t in daily.get("temperature_2m_max", []) if t is not None]
    precip = [p for p in daily.get("precipitation_sum", []) if p is not None]

    if len(temps) >= 4:
        first_half = sum(temps[:len(temps) // 2]) / max(len(temps) // 2, 1)
        second_half = sum(temps[len(temps) // 2:]) / max(len(temps) - len(temps) // 2, 1)
        temp_delta = second_half - first_half
        if temp_delta > 2:
            domain_trends["climate_comfort"] = "warming"
        elif temp_delta < -2:
            domain_trends["climate_comfort"] = "cooling"
        else:
            domain_trends["climate_comfort"] = "stable"
    else:
        domain_trends["climate_comfort"] = "no_data"

    if len(precip) >= 4:
        first_p = sum(precip[:len(precip) // 2]) / max(len(precip) // 2, 1)
        second_p = sum(precip[len(precip) // 2:]) / max(len(precip) - len(precip) // 2, 1)
        precip_delta = second_p - first_p
        if precip_delta > 3:
            domain_trends["water_resources"] = "wetter"
        elif precip_delta < -3:
            domain_trends["water_resources"] = "drier"
        else:
            domain_trends["water_resources"] = "stable"
    else:
        domain_trends["water_resources"] = "no_data"

    # --- Markov stationary distribution ---
    markov = analytics.get("precip_markov", {})
    stationary = markov.get("stationary", [])
    if len(stationary) >= 3:
        # [dry, light, heavy]
        if stationary[0] > 0.6:
            domain_trends["agriculture"] = "drought_prone"
        elif stationary[2] > 0.3:
            domain_trends["agriculture"] = "flood_prone"
        else:
            domain_trends["agriculture"] = "balanced"
    else:
        domain_trends["agriculture"] = "no_data"

    # --- Weibull hazard rate ---
    weibull = analytics.get("seismic_weibull", {})
    k_shape = weibull.get("k", 1.0)
    if k_shape > 1.2:
        domain_trends["hazard_safety"] = "increasing_hazard"
    elif k_shape < 0.8:
        domain_trends["hazard_safety"] = "decreasing_hazard"
    else:
        domain_trends["hazard_safety"] = "stable"

    # --- Inferred trends for remaining domains ---
    for d in scores:
        if d not in domain_trends:
            domain_trends[d] = "stable"

    # Composite trend
    trend_values = {"warming": 0.5, "cooling": -0.5, "wetter": 0.3, "drier": -0.3,
                    "drought_prone": -0.5, "flood_prone": -0.3, "balanced": 0.2,
                    "increasing_hazard": -0.7, "decreasing_hazard": 0.5,
                    "stable": 0.0, "no_data": 0.0}
    trend_sum = sum(trend_values.get(t, 0) for t in domain_trends.values())
    if trend_sum > 0.5:
        composite = "IMPROVING"
    elif trend_sum < -0.5:
        composite = "DEGRADING"
    else:
        composite = "STABLE"

    return {
        "domain_trends": domain_trends,
        "composite_trend": composite,
        "markov_stationary": stationary,
        "weibull_k": k_shape,
        "trend_score": round(trend_sum, 2),
    }


# ---------------------------------------------------------------------------
# 8. ELECTRE OUTRANKING
# ---------------------------------------------------------------------------

def electre_outranking(scenario_results):
    """ELECTRE I outranking: concordance + discordance analysis.

    Concordance(a,b) = sum(w_j for criteria where a_j >= b_j)
    Discordance(a,b) = max((b_j - a_j) / range_j where b_j > a_j)
    Kernel = non-dominated scenarios.
    """
    if not scenario_results:
        return {"concordance_matrix": {}, "discordance_matrix": {}, "kernel": []}

    scenario_keys = list(scenario_results.keys())
    n = len(scenario_keys)
    if n < 2:
        return {"concordance_matrix": {}, "discordance_matrix": {}, "kernel": scenario_keys}

    # Collect criteria
    all_criteria = set()
    for sr in scenario_results.values():
        for c in (sr.get("criteria") or {}):
            all_criteria.add(c)
    all_criteria = sorted(all_criteria)
    nc = len(all_criteria)
    if nc == 0:
        return {"concordance_matrix": {}, "discordance_matrix": {}, "kernel": scenario_keys}

    # Build score matrix
    matrix = {}
    for sk in scenario_keys:
        crit = scenario_results[sk].get("criteria", {})
        row = {}
        for c in all_criteria:
            val = crit.get(c, {}).get("score", 50) if isinstance(crit.get(c), dict) else 50
            row[c] = val
        matrix[sk] = row

    # Equal weights
    w = {c: 1.0 / nc for c in all_criteria}

    # Ranges per criterion
    ranges = {}
    for c in all_criteria:
        vals = [matrix[sk][c] for sk in scenario_keys]
        r = max(vals) - min(vals)
        ranges[c] = r if r > 0 else 1

    # Concordance & Discordance
    concordance = {}
    discordance = {}
    for a in scenario_keys:
        for b in scenario_keys:
            if a == b:
                continue
            conc = sum(w[c] for c in all_criteria if matrix[a][c] >= matrix[b][c])
            concordance[(a, b)] = round(conc, 4)

            disc_vals = []
            for c in all_criteria:
                if matrix[b][c] > matrix[a][c]:
                    disc_vals.append((matrix[b][c] - matrix[a][c]) / ranges[c])
            discordance[(a, b)] = round(max(disc_vals) if disc_vals else 0, 4)

    # Thresholds (median-based)
    conc_vals = [v for v in concordance.values()]
    disc_vals = [v for v in discordance.values()]
    conc_threshold = sorted(conc_vals)[len(conc_vals) // 2] if conc_vals else 0.5
    disc_threshold = sorted(disc_vals)[len(disc_vals) // 2] if disc_vals else 0.5

    # Outranking: a outranks b if C(a,b) >= c_threshold and D(a,b) <= d_threshold
    outranks = {sk: set() for sk in scenario_keys}
    for a in scenario_keys:
        for b in scenario_keys:
            if a != b:
                if concordance.get((a, b), 0) >= conc_threshold and discordance.get((a, b), 1) <= disc_threshold:
                    outranks[a].add(b)

    # Kernel = scenarios not outranked by any other
    outranked_by_any = set()
    for a in scenario_keys:
        for b in outranks[a]:
            outranked_by_any.add(b)

    kernel = [sk for sk in scenario_keys if sk not in outranked_by_any]
    if not kernel:
        kernel = scenario_keys[:1]  # fallback

    return {
        "concordance_matrix": concordance,
        "discordance_matrix": discordance,
        "kernel": kernel,
    }
