"""
Advanced Algorithms — 4 additional analytical engines for TerraScout AI Phase 3.

E. VIKOR Compromise Ranking — multi-criteria decision with ideal/anti-ideal solutions
F. Markov Chain Stability   — state transition probability, steady-state analysis
G. Entropy-Based Information— Shannon entropy, information gain per domain
H. Pareto Frontier          — multi-objective optimization, dominance analysis

Pure Python — no scipy/sklearn dependencies.
"""

import logging
import math
from collections import defaultdict

logger = logging.getLogger(__name__)

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
    "water_resources": "Water Resources",
    "infrastructure": "Infrastructure",
    "climate_comfort": "Climate Comfort",
    "economic_potential": "Economic Potential",
    "air_environment": "Air Environment",
    "geological_stability": "Geological Stability",
}


# ═══════════════════════════════════════════════════════════════════════════
# E. VIKOR COMPROMISE RANKING
# ═══════════════════════════════════════════════════════════════════════════

def vikor_compromise_ranking(scores, weights=None):
    """VIKOR multi-criteria compromise ranking.

    Evaluates how each domain performs relative to ideal and anti-ideal
    solutions across multiple perspectives (score, safety-weight, dev-weight).

    Args:
        scores: dict domain->score (0-100)
        weights: optional dict domain->weight (default: equal)

    Returns dict:
        rankings: list of {domain, label, S, R, Q, rank}
        ideal_solution: dict domain->best value
        anti_ideal: dict domain->worst value
        compromise_domain: str (best by Q)
        vikor_v: float (strategy weight used)
        stability_condition: bool
    """
    try:
        n = len(_DOMAINS)
        if weights is None:
            weights = {d: 1.0 / n for d in _DOMAINS}

        vals = {}
        for d in _DOMAINS:
            v = scores.get(d, 50)
            vals[d] = v if isinstance(v, (int, float)) else 50

        # Ideal (best) and anti-ideal (worst) per criterion
        # Here each domain IS a criterion AND an alternative
        # We evaluate domains against a multi-perspective matrix
        # Perspectives: raw_score, inverted_risk, normalized_deviation

        perspectives = {}
        all_vals = list(vals.values())
        mean_val = sum(all_vals) / len(all_vals) if all_vals else 50
        std_val = math.sqrt(sum((v - mean_val) ** 2 for v in all_vals) / len(all_vals)) if all_vals else 10

        for d in _DOMAINS:
            v = vals[d]
            perspectives[d] = {
                "raw": v,
                "risk_adjusted": v * (0.7 + 0.3 * (vals.get("hazard_safety", 50) / 100)),
                "deviation": 100 - abs(v - mean_val) / (std_val + 1) * 20,
            }

        criteria = ["raw", "risk_adjusted", "deviation"]
        nc = len(criteria)
        w = [1.0 / nc] * nc  # equal criterion weights

        # Find ideal (max) and anti-ideal (min) per criterion
        ideal = {}
        anti_ideal = {}
        for c in criteria:
            c_vals = [perspectives[d][c] for d in _DOMAINS]
            ideal[c] = max(c_vals)
            anti_ideal[c] = min(c_vals)

        # Compute S (Manhattan-like), R (Chebyshev-like), Q (compromise)
        S_vals = {}
        R_vals = {}
        for d in _DOMAINS:
            s_sum = 0.0
            r_max = 0.0
            for ci, c in enumerate(criteria):
                f_star = ideal[c]
                f_minus = anti_ideal[c]
                f_ij = perspectives[d][c]
                denom = f_star - f_minus if abs(f_star - f_minus) > 1e-9 else 1.0
                term = w[ci] * (f_star - f_ij) / denom
                s_sum += term
                r_max = max(r_max, term)
            S_vals[d] = s_sum
            R_vals[d] = r_max

        S_star = min(S_vals.values())
        S_minus = max(S_vals.values())
        R_star = min(R_vals.values())
        R_minus = max(R_vals.values())

        v = 0.5  # compromise strategy weight

        Q_vals = {}
        for d in _DOMAINS:
            s_term = (S_vals[d] - S_star) / (S_minus - S_star) if abs(S_minus - S_star) > 1e-9 else 0
            r_term = (R_vals[d] - R_star) / (R_minus - R_star) if abs(R_minus - R_star) > 1e-9 else 0
            Q_vals[d] = v * s_term + (1 - v) * r_term

        # Rank by Q (lower is better)
        ranked = sorted(_DOMAINS, key=lambda d: Q_vals[d])
        rankings = []
        for i, d in enumerate(ranked):
            rankings.append({
                "domain": d,
                "label": _DOMAIN_LABELS.get(d, d),
                "S": round(S_vals[d], 4),
                "R": round(R_vals[d], 4),
                "Q": round(Q_vals[d], 4),
                "rank": i + 1,
                "score": vals[d],
            })

        # Stability condition: Q(a2) - Q(a1) >= 1/(n-1)
        stability = True
        if len(ranked) >= 2:
            stability = (Q_vals[ranked[1]] - Q_vals[ranked[0]]) >= (1.0 / (n - 1))

        return {
            "rankings": rankings,
            "ideal_solution": {d: round(perspectives[d]["raw"], 1) for d in _DOMAINS},
            "anti_ideal": {d: round(anti_ideal.get("raw", 0), 1) for d in _DOMAINS},
            "compromise_domain": ranked[0],
            "compromise_label": _DOMAIN_LABELS.get(ranked[0], ranked[0]),
            "vikor_v": v,
            "stability_condition": stability,
        }
    except Exception as exc:
        logger.warning("VIKOR compromise ranking failed: %s", exc)
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# F. MARKOV CHAIN STABILITY ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def _build_transition_matrix(scores):
    """Build state transition matrix based on domain score dynamics.

    States: CRITICAL (0-30), WEAK (30-50), MODERATE (50-70), STRONG (70-100).
    Transitions are inferred from score clustering and domain interactions.
    """
    states = ["CRITICAL", "WEAK", "MODERATE", "STRONG"]
    ns = len(states)

    def _classify(score):
        if score < 30:
            return 0  # CRITICAL
        if score < 50:
            return 1  # WEAK
        if score < 70:
            return 2  # MODERATE
        return 3  # STRONG

    # Count domains in each state
    state_counts = [0] * ns
    for d in _DOMAINS:
        v = scores.get(d, 50)
        if not isinstance(v, (int, float)):
            v = 50
        state_counts[_classify(v)] += 1

    total = sum(state_counts) or 1

    # Build transition matrix based on empirical distributions + decay model
    # Domains tend to regress to mean (moderate) over time
    P = [[0.0] * ns for _ in range(ns)]

    # CRITICAL -> tends to improve (with some staying)
    P[0] = [0.40, 0.35, 0.20, 0.05]
    # WEAK -> tends to stay or improve
    P[1] = [0.10, 0.40, 0.35, 0.15]
    # MODERATE -> most stable
    P[2] = [0.05, 0.15, 0.55, 0.25]
    # STRONG -> slight regression to mean
    P[3] = [0.02, 0.08, 0.25, 0.65]

    # Adjust based on actual distribution (data-driven perturbation)
    for i in range(ns):
        current_frac = state_counts[i] / total
        if current_frac > 0.4:
            # If many domains in this state, increase self-transition
            P[i][i] = min(P[i][i] + 0.1, 0.85)
            # Renormalize
            others = sum(P[i][j] for j in range(ns) if j != i)
            if others > 0:
                scale = (1 - P[i][i]) / others
                for j in range(ns):
                    if j != i:
                        P[i][j] *= scale

    return P, states, state_counts


def _steady_state(P, iterations=200):
    """Compute steady-state distribution via power iteration."""
    n = len(P)
    pi = [1.0 / n] * n
    for _ in range(iterations):
        new_pi = [0.0] * n
        for j in range(n):
            for i in range(n):
                new_pi[j] += pi[i] * P[i][j]
        total = sum(new_pi) or 1
        pi = [p / total for p in new_pi]
    return pi


def _mean_first_passage(P, target_state=3, max_iter=200):
    """Estimate mean first passage time to target state from each state."""
    n = len(P)
    # Iterative computation
    mfpt = [0.0] * n
    mfpt[target_state] = 0.0

    for _ in range(max_iter):
        new_mfpt = [0.0] * n
        new_mfpt[target_state] = 0.0
        for i in range(n):
            if i == target_state:
                continue
            new_mfpt[i] = 1 + sum(P[i][j] * mfpt[j] for j in range(n))
        mfpt = new_mfpt

    return mfpt


def markov_chain_stability(scores):
    """Analyze location stability via Markov chain state transitions.

    Returns dict:
        transition_matrix: 4x4 probability matrix
        states: list of state names
        current_distribution: current state counts
        steady_state: long-term equilibrium distribution
        stability_index: 0-100 (how stable the system is)
        mean_passage_to_strong: expected steps to STRONG from each state
        system_trajectory: "IMPROVING", "STABLE", "DECLINING"
        entropy_rate: information entropy of the chain
    """
    try:
        P, states, state_counts = _build_transition_matrix(scores)
        ss = _steady_state(P)
        mfpt = _mean_first_passage(P, target_state=3)

        # Current distribution
        total = sum(state_counts) or 1
        current_dist = [c / total for c in state_counts]

        # Stability index: how close current is to steady state
        divergence = sum(abs(current_dist[i] - ss[i]) for i in range(len(states))) / 2
        stability_index = round((1 - divergence) * 100, 1)

        # System trajectory: compare weighted current vs steady state
        state_values = [15, 40, 60, 85]
        current_expected = sum(current_dist[i] * state_values[i] for i in range(len(states)))
        steady_expected = sum(ss[i] * state_values[i] for i in range(len(states)))

        if steady_expected > current_expected + 5:
            trajectory = "IMPROVING"
        elif steady_expected < current_expected - 5:
            trajectory = "DECLINING"
        else:
            trajectory = "STABLE"

        # Entropy rate
        entropy_rate = 0.0
        for i in range(len(states)):
            for j in range(len(states)):
                if ss[i] > 0 and P[i][j] > 0:
                    entropy_rate -= ss[i] * P[i][j] * math.log2(P[i][j])

        return {
            "transition_matrix": [[round(p, 4) for p in row] for row in P],
            "states": states,
            "current_distribution": [round(d, 3) for d in current_dist],
            "steady_state": [round(s, 3) for s in ss],
            "stability_index": stability_index,
            "mean_passage_to_strong": [round(m, 1) for m in mfpt],
            "system_trajectory": trajectory,
            "entropy_rate": round(entropy_rate, 3),
            "current_expected_value": round(current_expected, 1),
            "steady_expected_value": round(steady_expected, 1),
        }
    except Exception as exc:
        logger.warning("Markov chain stability analysis failed: %s", exc)
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# G. ENTROPY-BASED INFORMATION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def entropy_information_analysis(scores, details=None):
    """Analyze information content and entropy across domains.

    Returns dict:
        domain_entropy: dict per domain with entropy, information_gain, surprise_value
        system_entropy: overall Shannon entropy
        max_entropy: theoretical maximum
        redundancy: 1 - (H/Hmax)
        information_profile: "HIGH_INFO" / "MODERATE" / "LOW_INFO"
        most_informative: domain with highest information gain
        least_informative: domain with lowest information gain
        diversity_index: Simpson's diversity equivalent
    """
    try:
        vals = {}
        for d in _DOMAINS:
            v = scores.get(d, 50)
            vals[d] = v if isinstance(v, (int, float)) else 50

        all_vals = list(vals.values())
        total = sum(all_vals) or 1
        n = len(all_vals)

        # Normalize to probability distribution
        probs = [v / total for v in all_vals]

        # System Shannon entropy
        H = 0.0
        for p in probs:
            if p > 0:
                H -= p * math.log2(p)

        H_max = math.log2(n) if n > 0 else 0
        redundancy = 1 - (H / H_max) if H_max > 0 else 0

        # Per-domain entropy analysis
        mean_val = sum(all_vals) / n if n > 0 else 50
        std_val = math.sqrt(sum((v - mean_val) ** 2 for v in all_vals) / n) if n > 0 else 10

        domain_entropy = {}
        for i, d in enumerate(_DOMAINS):
            p = probs[i]

            # Self-information (surprise)
            surprise = -math.log2(p) if p > 0 else 0

            # Information gain: how much this domain deviates from uniform
            uniform_p = 1.0 / n
            if p > 0 and uniform_p > 0:
                info_gain = p * math.log2(p / uniform_p)
            else:
                info_gain = 0

            # Relative entropy contribution
            contrib = (-p * math.log2(p)) if p > 0 else 0
            contrib_pct = (contrib / H * 100) if H > 0 else 100 / n

            domain_entropy[d] = {
                "label": _DOMAIN_LABELS.get(d, d),
                "score": vals[d],
                "probability": round(p, 4),
                "surprise_value": round(surprise, 3),
                "information_gain": round(abs(info_gain), 4),
                "entropy_contribution": round(contrib, 4),
                "entropy_contribution_pct": round(contrib_pct, 1),
                "deviation_sigma": round((vals[d] - mean_val) / (std_val + 1e-9), 2),
            }

        # Sort by information gain
        sorted_by_ig = sorted(domain_entropy.items(),
                              key=lambda x: x[1]["information_gain"], reverse=True)
        most_info = sorted_by_ig[0][0] if sorted_by_ig else None
        least_info = sorted_by_ig[-1][0] if sorted_by_ig else None

        # Simpson's diversity index (1 - sum(p^2))
        simpson = 1 - sum(p * p for p in probs)

        # Profile
        if redundancy < 0.1:
            profile = "HIGH DIVERSITY"
        elif redundancy < 0.3:
            profile = "BALANCED"
        elif redundancy < 0.5:
            profile = "MODERATE CONCENTRATION"
        else:
            profile = "HIGH CONCENTRATION"

        return {
            "domain_entropy": domain_entropy,
            "system_entropy": round(H, 4),
            "max_entropy": round(H_max, 4),
            "redundancy": round(redundancy, 4),
            "information_profile": profile,
            "most_informative": most_info,
            "most_informative_label": _DOMAIN_LABELS.get(most_info, ""),
            "least_informative": least_info,
            "least_informative_label": _DOMAIN_LABELS.get(least_info, ""),
            "diversity_index": round(simpson, 4),
            "effective_domains": round(2 ** H, 1),
        }
    except Exception as exc:
        logger.warning("Entropy information analysis failed: %s", exc)
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# H. PARETO FRONTIER OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════

def pareto_frontier_analysis(scores, details=None):
    """Multi-objective Pareto optimization across domain pairs.

    Identifies Pareto-optimal domains (not dominated in any objective pair)
    and dominated domains (improvement targets).

    Returns dict:
        pareto_optimal: list of non-dominated domains
        dominated: list of dominated domains with dominator info
        frontier_pairs: list of (objective1, objective2) frontier analyses
        improvement_vectors: dict per dominated domain -> suggested improvements
        pareto_efficiency: float 0-1 (fraction of Pareto-optimal domains)
        trade_off_insights: list of trade-off descriptions
    """
    try:
        vals = {}
        for d in _DOMAINS:
            v = scores.get(d, 50)
            vals[d] = v if isinstance(v, (int, float)) else 50

        n = len(_DOMAINS)

        # Define objective pairs (maximize both in each pair)
        objective_pairs = [
            ("habitability", "economic_potential", "Livability vs Growth"),
            ("ecology", "infrastructure", "Environment vs Development"),
            ("hazard_safety", "economic_potential", "Safety vs Opportunity"),
            ("water_resources", "agriculture", "Water vs Agriculture"),
            ("climate_comfort", "air_environment", "Climate vs Air Quality"),
        ]

        # Overall Pareto dominance: domain A dominates B if A >= B in ALL dimensions
        # We use 3 key objectives: score, safety-adjusted, network-value
        objectives = {}
        safety = vals.get("hazard_safety", 50) / 100
        for d in _DOMAINS:
            objectives[d] = [
                vals[d],                           # Obj 1: raw score
                vals[d] * (0.7 + 0.3 * safety),   # Obj 2: safety-adjusted
                vals[d] * 0.5 + 50 * 0.5,         # Obj 3: balanced baseline
            ]

        # Find Pareto-optimal set
        dominated_by = {}
        pareto_set = set(_DOMAINS)
        for i, d1 in enumerate(_DOMAINS):
            for j, d2 in enumerate(_DOMAINS):
                if i == j:
                    continue
                # Check if d2 dominates d1
                obj1 = objectives[d1]
                obj2 = objectives[d2]
                dom = all(obj2[k] >= obj1[k] for k in range(len(obj1))) and \
                      any(obj2[k] > obj1[k] for k in range(len(obj1)))
                if dom:
                    pareto_set.discard(d1)
                    dominated_by[d1] = d2
                    break

        pareto_optimal = sorted(pareto_set, key=lambda d: vals[d], reverse=True)
        dominated = []
        for d in _DOMAINS:
            if d not in pareto_set:
                dominator = dominated_by.get(d, "")
                dominated.append({
                    "domain": d,
                    "label": _DOMAIN_LABELS.get(d, d),
                    "score": vals[d],
                    "dominated_by": _DOMAIN_LABELS.get(dominator, dominator),
                    "gap": round(vals.get(dominator, 50) - vals[d], 1),
                })

        # Frontier pair analysis
        frontier_pairs = []
        for obj1_d, obj2_d, pair_name in objective_pairs:
            v1 = vals.get(obj1_d, 50)
            v2 = vals.get(obj2_d, 50)
            # Trade-off angle
            angle = math.degrees(math.atan2(v2 - 50, v1 - 50))
            balance = 100 - abs(v1 - v2)
            frontier_pairs.append({
                "name": pair_name,
                "objective_1": {"domain": obj1_d, "label": _DOMAIN_LABELS.get(obj1_d, obj1_d), "value": v1},
                "objective_2": {"domain": obj2_d, "label": _DOMAIN_LABELS.get(obj2_d, obj2_d), "value": v2},
                "balance": round(balance, 1),
                "trade_off_angle": round(angle, 1),
            })

        # Improvement vectors for dominated domains
        improvement_vectors = {}
        for item in dominated:
            d = item["domain"]
            target = max(vals[pd] for pd in pareto_optimal) if pareto_optimal else 75
            improvement_vectors[d] = {
                "label": _DOMAIN_LABELS.get(d, d),
                "current": vals[d],
                "target": round(target, 1),
                "gap": round(target - vals[d], 1),
                "priority": "HIGH" if target - vals[d] > 25 else ("MEDIUM" if target - vals[d] > 10 else "LOW"),
            }

        # Trade-off insights
        trade_offs = []
        for fp in frontier_pairs:
            v1 = fp["objective_1"]["value"]
            v2 = fp["objective_2"]["value"]
            l1 = fp["objective_1"]["label"]
            l2 = fp["objective_2"]["label"]
            if abs(v1 - v2) < 10:
                trade_offs.append(f"{l1} and {l2} are well-balanced (diff: {abs(v1-v2):.0f}).")
            elif v1 > v2:
                trade_offs.append(f"{l1} outperforms {l2} by {v1-v2:.0f} points — consider rebalancing.")
            else:
                trade_offs.append(f"{l2} outperforms {l1} by {v2-v1:.0f} points — consider rebalancing.")

        efficiency = len(pareto_optimal) / n if n > 0 else 0

        return {
            "pareto_optimal": [{
                "domain": d,
                "label": _DOMAIN_LABELS.get(d, d),
                "score": vals[d],
            } for d in pareto_optimal],
            "dominated": dominated,
            "frontier_pairs": frontier_pairs,
            "improvement_vectors": improvement_vectors,
            "pareto_efficiency": round(efficiency, 3),
            "trade_off_insights": trade_offs,
        }
    except Exception as exc:
        logger.warning("Pareto frontier analysis failed: %s", exc)
        return {}
