"""
Apex Algorithms -- Phase 4 intelligence algorithms for TerraScout AI.
Game Theory, Cellular Automata, Genetic Algorithm, Wavelet Analysis.
Pure Python -- no external dependencies beyond stdlib.
"""

import math
import random
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

_DOMAINS = [
    "water_resources", "geological_stability", "climate_comfort",
    "ecology", "agriculture", "infrastructure",
    "hazard_safety", "habitability", "air_environment", "economic_potential",
]
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
# Helpers
# ---------------------------------------------------------------------------

def _safe_scores(scores: dict) -> dict:
    """Return a sanitized scores dict with 0.0 defaults for missing domains."""
    if not isinstance(scores, dict):
        scores = {}
    return {d: float(scores.get(d, 0.0) or 0.0) for d in _DOMAINS}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* between *lo* and *hi*."""
    return max(lo, min(hi, value))


def _normalize_allocation(genome: list) -> list:
    """Normalize a list of non-negative floats so they sum to 1.0."""
    total = sum(abs(g) for g in genome)
    if total < 1e-12:
        n = len(genome)
        return [1.0 / n] * n
    return [abs(g) / total for g in genome]


def _shannon_entropy(distribution: list) -> float:
    """Shannon entropy for a list of non-negative ints / floats (counts)."""
    total = sum(distribution)
    if total <= 0:
        return 0.0
    ent = 0.0
    for v in distribution:
        if v > 0:
            p = v / total
            ent -= p * math.log2(p)
    return ent


# ===================================================================
# A. Game Theory Analysis (Nash Equilibrium + Shapley Values)
# ===================================================================

def game_theory_analysis(scores: dict, details: dict) -> dict:
    """Cooperative game-theory model over the 10 TerraScout domains.

    Each domain is a *player* choosing between **invest** and **neglect**.
    Payoffs depend on pairwise interactions.  The function computes a
    Nash Equilibrium via iterated best-response, then exact Shapley
    values over all 1024 coalitions.

    Parameters
    ----------
    scores : dict
        Domain name -> float (0-100).
    details : dict
        Domain name -> sub-indicator dict (currently unused beyond
        context, but kept for API symmetry).

    Returns
    -------
    dict
        See module docstring for full schema.
    """
    try:
        s = _safe_scores(scores)
        n = len(_DOMAINS)

        # ---- 1. Payoff matrix (10x10 per strategy pair) ---- #
        # payoff[i][j][si][sj]  si,sj in {0=neglect, 1=invest}
        # Returns payoff TO player i.
        def _payoff_i(i_idx, j_idx, si, sj):
            si_score = s[_DOMAINS[i_idx]]
            sj_score = s[_DOMAINS[j_idx]]
            avg = (si_score + sj_score) / 2.0
            if si == 1 and sj == 1:
                return avg * 1.2  # synergy
            elif si == 1 and sj == 0:
                return si_score * 0.8  # investor bears cost
            elif si == 0 and sj == 1:
                return si_score * 1.1  # free-riding
            else:
                return avg * 0.7  # mutual neglect

        # Aggregate payoff for domain i given full strategy vector
        def _total_payoff(i_idx, strategies):
            total = 0.0
            for j_idx in range(n):
                if j_idx == i_idx:
                    continue
                total += _payoff_i(i_idx, j_idx, strategies[i_idx], strategies[j_idx])
            return total

        # ---- 2. Iterated best response ---- #
        strategies = [1] * n  # start all invest
        converged = False
        iterations = 0
        max_iter = 100

        for it in range(1, max_iter + 1):
            changed = False
            for i_idx in range(n):
                pay_invest = _total_payoff(i_idx, strategies[:i_idx] + [1] + strategies[i_idx + 1:])
                pay_neglect = _total_payoff(i_idx, strategies[:i_idx] + [0] + strategies[i_idx + 1:])
                best = 1 if pay_invest >= pay_neglect else 0
                if best != strategies[i_idx]:
                    strategies[i_idx] = best
                    changed = True
            iterations = it
            if not changed:
                converged = True
                break

        nash_eq = {_DOMAINS[i]: ("invest" if strategies[i] == 1 else "neglect") for i in range(n)}
        free_riders = [_DOMAINS[i] for i in range(n) if strategies[i] == 0]

        # ---- 3. Shapley values ---- #
        # Coalition value function
        def _coalition_value(member_mask: int) -> float:
            members = [i for i in range(n) if (member_mask >> i) & 1]
            if not members:
                return 0.0
            base = sum(s[_DOMAINS[i]] for i in members)
            synergy = 1.0 + 0.15 * len(members) / n
            return base * synergy

        # Factorial helper
        def _fact(k):
            if k <= 1:
                return 1
            r = 1
            for x in range(2, k + 1):
                r *= x
            return r

        shapley = [0.0] * n
        fact_n = _fact(n)

        for i in range(n):
            total_marginal = 0.0
            i_bit = 1 << i
            # Iterate over all subsets S of N\{i}
            others_mask = ((1 << n) - 1) ^ i_bit
            subset = 0
            # We iterate via submask enumeration of others_mask
            # Start with empty set, then enumerate
            while True:
                s_size = bin(subset).count('1')
                weight = _fact(s_size) * _fact(n - s_size - 1)
                v_with = _coalition_value(subset | i_bit)
                v_without = _coalition_value(subset)
                total_marginal += weight * (v_with - v_without)
                if subset == others_mask:
                    break
                # Next submask of others_mask (including 0 -> first proper submask)
                if subset == 0:
                    subset = others_mask & (-others_mask) if others_mask else 0
                    if subset == 0:
                        break
                    # Actually, let's do it properly: enumerate all subsets of others_mask
                    # Reset and use the standard bitmask enumeration
                    break  # will redo below
                break  # fallback

            # Proper submask enumeration of others_mask (including empty set)
            total_marginal = 0.0
            # Collect all subsets of others_mask
            sub = others_mask
            subsets = []
            while sub > 0:
                subsets.append(sub)
                sub = (sub - 1) & others_mask
            subsets.append(0)  # empty set

            for subset in subsets:
                s_size = bin(subset).count('1')
                weight = _fact(s_size) * _fact(n - s_size - 1)
                v_with = _coalition_value(subset | i_bit)
                v_without = _coalition_value(subset)
                total_marginal += weight * (v_with - v_without)

            shapley[i] = total_marginal / fact_n

        # Normalize Shapley to 0-100
        shap_max = max(abs(v) for v in shapley) if shapley else 1.0
        if shap_max < 1e-12:
            shap_max = 1.0
        shapley_norm = {_DOMAINS[i]: round(_clamp(shapley[i] / shap_max * 100), 2) for i in range(n)}

        mvp = max(shapley_norm, key=lambda d: shapley_norm[d])

        # ---- 4. Cooperation bonus ---- #
        all_invest_payoff = sum(_total_payoff(i, [1] * n) for i in range(n))
        all_neglect_payoff = sum(_total_payoff(i, [0] * n) for i in range(n))
        coop_bonus = 0.0
        if abs(all_neglect_payoff) > 1e-6:
            coop_bonus = round((all_invest_payoff - all_neglect_payoff) / abs(all_neglect_payoff) * 100, 2)

        # ---- 5. Insight ---- #
        invest_count = sum(1 for v in nash_eq.values() if v == "invest")
        if invest_count == n:
            insight = (f"Full cooperation is the Nash Equilibrium -- all domains benefit from "
                       f"mutual investment.  {mvp} contributes the most value (Shapley).  "
                       f"Cooperation yields a {coop_bonus:.1f}% improvement over universal neglect.")
        elif invest_count == 0:
            insight = ("Universal neglect is the equilibrium, indicating weak inter-domain synergies "
                       "at current score levels.  Targeted external incentives are needed.")
        else:
            insight = (f"{invest_count}/{n} domains choose to invest at equilibrium.  "
                       f"Free-rider risk in: {', '.join(free_riders)}.  "
                       f"{mvp} is the most valuable player (highest Shapley value).")

        return {
            "nash_equilibrium": nash_eq,
            "equilibrium_stable": converged,
            "iterations_to_converge": iterations,
            "shapley_values": shapley_norm,
            "most_valuable_player": mvp,
            "free_rider_risk": free_riders,
            "cooperation_bonus": coop_bonus,
            "strategy_insight": insight,
        }

    except Exception as exc:
        logger.error("game_theory_analysis failed: %s", exc, exc_info=True)
        empty_eq = {d: "invest" for d in _DOMAINS}
        empty_shap = {d: 0.0 for d in _DOMAINS}
        return {
            "nash_equilibrium": empty_eq,
            "equilibrium_stable": False,
            "iterations_to_converge": 0,
            "shapley_values": empty_shap,
            "most_valuable_player": _DOMAINS[0],
            "free_rider_risk": [],
            "cooperation_bonus": 0.0,
            "strategy_insight": "Analysis could not be completed due to an internal error.",
        }


# ===================================================================
# B. Cellular Automata Simulation
# ===================================================================

# Adjacency / influence weights (symmetric)
_CA_STRONG_LINKS = {
    ("water_resources", "agriculture"),
    ("climate_comfort", "ecology"),
    ("infrastructure", "economic_potential"),
    ("hazard_safety", "geological_stability"),
    ("habitability", "agriculture"),
}
_CA_MODERATE_LINKS = {
    ("air_environment", "climate_comfort"),
}


def _ca_influence_weight(d1: str, d2: str) -> float:
    """Return influence weight between two domains for the CA."""
    pair = (d1, d2)
    pair_rev = (d2, d1)
    if pair in _CA_STRONG_LINKS or pair_rev in _CA_STRONG_LINKS:
        return 1.0
    if pair in _CA_MODERATE_LINKS or pair_rev in _CA_MODERATE_LINKS:
        return 0.6
    return 0.2  # weak default


def cellular_automata_simulation(scores: dict, details: dict) -> dict:
    """Simulate domain-quality evolution using a 1D cellular automaton.

    Each of the 10 domains is a cell with state 0-4 (Critical to
    Excellent).  Weighted neighbour averaging drives state transitions
    over 30 generations.

    Parameters
    ----------
    scores : dict
        Domain name -> float (0-100).
    details : dict
        Domain name -> sub-indicator dict (unused beyond context).

    Returns
    -------
    dict
        Full evolution history and derived metrics.
    """
    try:
        random.seed(42)
        s = _safe_scores(scores)
        n = len(_DOMAINS)

        # Map scores to states 0-4
        def _score_to_state(v):
            if v < 20:
                return 0
            elif v < 40:
                return 1
            elif v < 60:
                return 2
            elif v < 80:
                return 3
            return 4

        state_labels = {0: "Critical", 1: "Poor", 2: "Moderate", 3: "Good", 4: "Excellent"}

        states = [_score_to_state(s[d]) for d in _DOMAINS]
        initial = list(states)

        # Precompute neighbour weights (all-to-all, weighted)
        weights = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    weights[i][j] = _ca_influence_weight(_DOMAINS[i], _DOMAINS[j])

        evolution = [list(states)]
        generations = 30

        for _gen in range(generations):
            new_states = list(states)
            for i in range(n):
                # Weighted average of neighbour states
                w_sum = 0.0
                ws_sum = 0.0
                for j in range(n):
                    if i != j:
                        w_sum += weights[i][j] * states[j]
                        ws_sum += weights[i][j]
                if ws_sum > 1e-9:
                    neighbor_avg = w_sum / ws_sum
                else:
                    neighbor_avg = states[i]

                # Transition rule
                if neighbor_avg > states[i] + 1:
                    new_states[i] = min(states[i] + 1, 4)
                elif neighbor_avg < states[i] - 1:
                    new_states[i] = max(states[i] - 1, 0)
                # else: homeostasis

                # Random perturbation (5%)
                if random.random() < 0.05:
                    flip = random.choice([-1, 1])
                    new_states[i] = max(0, min(4, new_states[i] + flip))

            states = new_states
            evolution.append(list(states))

        final = list(states)

        # Stable domains: no change in last 10 generations
        stable = []
        for i in range(n):
            last_10 = [evolution[g][i] for g in range(max(0, len(evolution) - 10), len(evolution))]
            if len(set(last_10)) == 1:
                stable.append(_DOMAINS[i])

        improving = [_DOMAINS[i] for i in range(n) if final[i] > initial[i]]
        degrading = [_DOMAINS[i] for i in range(n) if final[i] < initial[i]]

        # System entropy of final state distribution
        state_counts = [0] * 5
        for v in final:
            state_counts[v] += 1
        entropy = round(_shannon_entropy(state_counts), 4)

        # Attractor detection: fixed point or 2-cycle in last 6 gens
        attractor = False
        if len(evolution) >= 3:
            if evolution[-1] == evolution[-2]:
                attractor = True  # fixed point
            elif len(evolution) >= 4 and evolution[-1] == evolution[-3]:
                attractor = True  # 2-cycle

        # Insight
        if attractor and evolution[-1] == evolution[-2]:
            pred = "The system has reached a stable fixed point."
        elif attractor:
            pred = "The system oscillates in a 2-cycle attractor."
        elif len(improving) > len(degrading):
            pred = f"Overall positive trend: {len(improving)} domains improving vs {len(degrading)} degrading."
        elif len(degrading) > len(improving):
            pred = f"Concerning negative trend: {len(degrading)} domains degrading."
        else:
            pred = "The system is in dynamic equilibrium with balanced changes."

        return {
            "initial_states": {_DOMAINS[i]: initial[i] for i in range(n)},
            "final_states": {_DOMAINS[i]: final[i] for i in range(n)},
            "state_labels": state_labels,
            "generations": generations,
            "evolution": evolution[1:],  # 30 rows (exclude initial)
            "domain_order": list(_DOMAINS),
            "stable_domains": stable,
            "improving_domains": improving,
            "degrading_domains": degrading,
            "system_entropy": entropy,
            "attractor_detected": attractor,
            "prediction_insight": pred,
        }

    except Exception as exc:
        logger.error("cellular_automata_simulation failed: %s", exc, exc_info=True)
        return {
            "initial_states": {d: 2 for d in _DOMAINS},
            "final_states": {d: 2 for d in _DOMAINS},
            "state_labels": {0: "Critical", 1: "Poor", 2: "Moderate", 3: "Good", 4: "Excellent"},
            "generations": 0,
            "evolution": [],
            "domain_order": list(_DOMAINS),
            "stable_domains": [],
            "improving_domains": [],
            "degrading_domains": [],
            "system_entropy": 0.0,
            "attractor_detected": False,
            "prediction_insight": "Simulation could not be completed due to an internal error.",
        }


# ===================================================================
# C. Genetic Algorithm Optimizer
# ===================================================================

def genetic_algorithm_optimizer(scores: dict, details: dict) -> dict:
    """Find optimal resource allocation across 10 domains via GA.

    A population of allocation vectors evolves through selection,
    crossover, and mutation to maximize a composite fitness score
    under budget constraints.

    Parameters
    ----------
    scores : dict
        Domain name -> float (0-100).
    details : dict
        Domain name -> sub-indicator dict (unused beyond context).

    Returns
    -------
    dict
        Optimal allocation, fitness curve, and strategic insight.
    """
    try:
        random.seed(42)
        s = _safe_scores(scores)
        n = len(_DOMAINS)
        boost_factor = 0.5
        pop_size = 80
        tournament_k = 5
        crossover_rate = 0.5
        mutation_rate = 0.15
        mutation_sigma = 0.05
        elitism_count = 5
        num_generations = 60

        # --- Fitness function --- #
        def _fitness(genome):
            alloc = _normalize_allocation(genome)
            base = sum(s[_DOMAINS[i]] * (1.0 + alloc[i] * boost_factor) for i in range(n))
            # Penalty for extreme imbalance
            penalty = 0.0
            if max(alloc) > 0.4:
                penalty = 10.0 * max(alloc)
            # Bonus for addressing weak domains
            bonus = 0.0
            for i in range(n):
                if s[_DOMAINS[i]] < 50 and alloc[i] > 0.15:
                    bonus += 5.0
            return base - penalty + bonus

        # --- Initialization --- #
        population = []
        for _ in range(pop_size):
            raw = [random.random() for _ in range(n)]
            population.append(_normalize_allocation(raw))

        def _tournament(pop, fitnesses):
            candidates = random.sample(range(len(pop)), min(tournament_k, len(pop)))
            best_idx = max(candidates, key=lambda idx: fitnesses[idx])
            return list(pop[best_idx])

        def _crossover(p1, p2):
            child = []
            for i in range(n):
                child.append(p1[i] if random.random() < crossover_rate else p2[i])
            return _normalize_allocation(child)

        def _mutate(genome):
            g = list(genome)
            indices = random.sample(range(n), min(2, n))
            for idx in indices:
                g[idx] += random.gauss(0, mutation_sigma)
                g[idx] = max(0.0, g[idx])
            return _normalize_allocation(g)

        # --- Baseline --- #
        equal_alloc = [1.0 / n] * n
        baseline_fitness = _fitness(equal_alloc)

        best_per_gen = []
        best_ever_fitness = -1e18
        best_ever_genome = list(equal_alloc)

        for gen in range(num_generations):
            fitnesses = [_fitness(ind) for ind in population]

            # Track best
            gen_best_idx = max(range(pop_size), key=lambda i: fitnesses[i])
            gen_best_fit = fitnesses[gen_best_idx]
            best_per_gen.append(round(gen_best_fit, 4))

            if gen_best_fit > best_ever_fitness:
                best_ever_fitness = gen_best_fit
                best_ever_genome = list(population[gen_best_idx])

            # Elitism
            sorted_indices = sorted(range(pop_size), key=lambda i: fitnesses[i], reverse=True)
            new_pop = [list(population[sorted_indices[i]]) for i in range(elitism_count)]

            # Fill rest via selection + crossover + mutation
            while len(new_pop) < pop_size:
                p1 = _tournament(population, fitnesses)
                p2 = _tournament(population, fitnesses)
                child = _crossover(p1, p2)
                if random.random() < mutation_rate:
                    child = _mutate(child)
                new_pop.append(child)

            population = new_pop

        # Final eval
        final_fitnesses = [_fitness(ind) for ind in population]
        final_best_idx = max(range(pop_size), key=lambda i: final_fitnesses[i])
        if final_fitnesses[final_best_idx] > best_ever_fitness:
            best_ever_fitness = final_fitnesses[final_best_idx]
            best_ever_genome = list(population[final_best_idx])

        opt_alloc = _normalize_allocation(best_ever_genome)
        opt_alloc_dict = {_DOMAINS[i]: round(opt_alloc[i], 4) for i in range(n)}
        improvement_pct = 0.0
        if abs(baseline_fitness) > 1e-6:
            improvement_pct = round((best_ever_fitness - baseline_fitness) / abs(baseline_fitness) * 100, 2)

        # Top priorities
        sorted_domains = sorted(range(n), key=lambda i: opt_alloc[i], reverse=True)
        top_priority = _DOMAINS[sorted_domains[0]]
        recommended = [_DOMAINS[sorted_domains[i]] for i in range(min(3, n))]

        # Convergence point: first gen reaching 99% of final fitness
        threshold = best_ever_fitness * 0.99
        gen_converge = num_generations
        for g, f in enumerate(best_per_gen):
            if f >= threshold:
                gen_converge = g + 1
                break

        # Diversity: average std of allocations across final population
        alloc_matrix = [_normalize_allocation(ind) for ind in population]
        means = [sum(alloc_matrix[j][i] for j in range(pop_size)) / pop_size for i in range(n)]
        diversity = 0.0
        for i in range(n):
            var = sum((alloc_matrix[j][i] - means[i]) ** 2 for j in range(pop_size)) / pop_size
            diversity += math.sqrt(var)
        diversity = round(diversity / n, 6)

        # Insight
        weak_domains = [_DOMAINS[i] for i in range(n) if s[_DOMAINS[i]] < 50]
        focus_on_weak = [d for d in recommended if d in weak_domains]
        if focus_on_weak:
            insight = (f"The optimizer recommends prioritizing {', '.join(recommended)}, "
                       f"achieving a {improvement_pct:.1f}% improvement over equal allocation.  "
                       f"Notably, {', '.join(focus_on_weak)} are currently weak and receive "
                       f"elevated investment to maximize recovery.")
        else:
            insight = (f"Optimal strategy focuses on {', '.join(recommended)} "
                       f"({improvement_pct:.1f}% improvement).  Convergence in "
                       f"{gen_converge} generations suggests a well-defined optimum.")

        return {
            "optimal_allocation": opt_alloc_dict,
            "optimal_fitness": round(best_ever_fitness, 4),
            "baseline_fitness": round(baseline_fitness, 4),
            "improvement_pct": improvement_pct,
            "top_priority": top_priority,
            "recommended_focus": recommended,
            "convergence": best_per_gen,
            "generations_to_converge": gen_converge,
            "diversity_final": diversity,
            "strategy_insight": insight,
        }

    except Exception as exc:
        logger.error("genetic_algorithm_optimizer failed: %s", exc, exc_info=True)
        equal = {d: round(1.0 / len(_DOMAINS), 4) for d in _DOMAINS}
        return {
            "optimal_allocation": equal,
            "optimal_fitness": 0.0,
            "baseline_fitness": 0.0,
            "improvement_pct": 0.0,
            "top_priority": _DOMAINS[0],
            "recommended_focus": list(_DOMAINS[:3]),
            "convergence": [],
            "generations_to_converge": 0,
            "diversity_final": 0.0,
            "strategy_insight": "Optimization could not be completed due to an internal error.",
        }


# ===================================================================
# D. Wavelet Transform Analysis (Haar)
# ===================================================================

def _haar_transform(signal: list) -> list:
    """In-place iterative Haar wavelet transform.

    The input length must be a power of 2.  Returns a list where
    the first element is the coarsest approximation coefficient and
    subsequent groups are detail coefficients from coarse to fine.
    """
    result = [float(x) for x in signal]
    length = len(result)
    temp = [0.0] * length
    while length > 1:
        half = length // 2
        for i in range(half):
            temp[i] = (result[2 * i] + result[2 * i + 1]) / math.sqrt(2)
            temp[half + i] = (result[2 * i] - result[2 * i + 1]) / math.sqrt(2)
        for i in range(length):
            result[i] = temp[i]
        length = half
    return result


def _haar_inverse(coeffs: list) -> list:
    """Inverse Haar wavelet transform (reconstruct signal)."""
    result = [float(x) for x in coeffs]
    n = len(result)
    length = 1
    temp = [0.0] * n
    while length < n:
        double = length * 2
        for i in range(length):
            a = result[i]
            d = result[length + i]
            temp[2 * i] = (a + d) / math.sqrt(2)
            temp[2 * i + 1] = (a - d) / math.sqrt(2)
        for i in range(double):
            result[i] = temp[i]
        length = double
    return result


def wavelet_analysis(scores: dict, details: dict, analytics: dict = None) -> dict:
    """Haar wavelet decomposition of the 10-domain score vector.

    Pads the signal to length 16 (next power of 2), decomposes into
    4 detail levels plus a single approximation coefficient, and
    computes energy, smoothness, and anomaly indicators.

    Parameters
    ----------
    scores : dict
        Domain name -> float (0-100).
    details : dict
        Domain name -> sub-indicator dict (unused beyond context).
    analytics : dict, optional
        Additional analytics context (unused but kept for API symmetry).

    Returns
    -------
    dict
        Wavelet coefficients, energy distribution, and interpretation.
    """
    try:
        s = _safe_scores(scores)
        n = len(_DOMAINS)

        # Build signal, pad to 16
        signal_raw = [s[d] for d in _DOMAINS]
        mean_val = sum(signal_raw) / n if n > 0 else 50.0
        padded_len = 16
        signal = list(signal_raw) + [mean_val] * (padded_len - n)

        # Transform
        coeffs = _haar_transform(signal)

        # Split into levels
        # For length 16: after transform the layout is:
        #   [approx(1), L4(1), L3(2), L2(4), L1(8)]
        approx_coeffs = [coeffs[0]]
        l4_coeffs = [coeffs[1]]
        l3_coeffs = coeffs[2:4]
        l2_coeffs = coeffs[4:8]
        l1_coeffs = coeffs[8:16]

        coeff_dict = {
            "L1": [round(c, 4) for c in l1_coeffs],
            "L2": [round(c, 4) for c in l2_coeffs],
            "L3": [round(c, 4) for c in l3_coeffs],
            "L4": [round(c, 4) for c in l4_coeffs],
            "approx": [round(c, 4) for c in approx_coeffs],
        }

        # Energy per level
        def _energy(clist):
            return sum(c ** 2 for c in clist)

        e1 = _energy(l1_coeffs)
        e2 = _energy(l2_coeffs)
        e3 = _energy(l3_coeffs)
        e4 = _energy(l4_coeffs)
        e_approx = _energy(approx_coeffs)
        total_energy = e1 + e2 + e3 + e4 + e_approx

        energy_by_level = {
            "L1": round(e1, 4),
            "L2": round(e2, 4),
            "L3": round(e3, 4),
            "L4": round(e4, 4),
        }

        # Energy distribution (detail levels only for % interpretation)
        detail_total = e1 + e2 + e3 + e4
        if detail_total < 1e-12:
            energy_dist = {"L1": 25.0, "L2": 25.0, "L3": 25.0, "L4": 25.0}
        else:
            energy_dist = {
                "L1": round(e1 / detail_total * 100, 2),
                "L2": round(e2 / detail_total * 100, 2),
                "L3": round(e3 / detail_total * 100, 2),
                "L4": round(e4 / detail_total * 100, 2),
            }

        # Dominant scale
        level_energies = {"L1": e1, "L2": e2, "L3": e3, "L4": e4}
        dominant = max(level_energies, key=lambda k: level_energies[k])

        interpretations = {
            "L1": "Fine domain-to-domain variation dominates -- scores differ sharply between neighbours.",
            "L2": "Sub-group patterns dominate -- clusters of 2-3 related domains drive variation.",
            "L3": "Broad category trends dominate -- large blocks of domains move together.",
            "L4": "Global tendency dominates -- the profile is split into a single high/low divide.",
        }

        # Smoothness: ratio of approximation energy to total
        smoothness = 0.0
        if total_energy > 1e-12:
            smoothness = round(e_approx / total_energy, 4)

        # Anomaly detection: large detail coefficients
        # Threshold: coefficient magnitude > 1.5 * std of all detail coefficients
        all_detail = list(l1_coeffs) + list(l2_coeffs) + list(l3_coeffs) + list(l4_coeffs)
        if all_detail:
            det_mean = sum(abs(c) for c in all_detail) / len(all_detail)
            det_var = sum((abs(c) - det_mean) ** 2 for c in all_detail) / len(all_detail)
            det_std = math.sqrt(det_var) if det_var > 0 else 0.0
            threshold = det_mean + 1.5 * det_std
        else:
            threshold = 1e18

        anomalies = []
        # Map L1 coefficients to domain pairs
        # L1 has 8 coefficients corresponding to pairs: (0,1),(2,3),(4,5),(6,7),(8,9),(10,11),(12,13),(14,15)
        # Only first 5 pairs map to actual domains (10 domains -> 5 pairs)
        domain_pairs_l1 = []
        for k in range(min(5, len(l1_coeffs))):
            d_idx = 2 * k
            if d_idx < n:
                domain_pairs_l1.append(_DOMAINS[d_idx])
            else:
                domain_pairs_l1.append(f"pad-{k}")

        for k, c in enumerate(l1_coeffs):
            if abs(c) > threshold and k < len(domain_pairs_l1):
                anomalies.append({
                    "domain": domain_pairs_l1[k],
                    "level": "L1",
                    "magnitude": round(abs(c), 4),
                })

        # L2: 4 coefficients -> groups of 4 values -> first ~2.5 domain groups
        domain_groups_l2 = []
        for k in range(min(len(l2_coeffs), 3)):
            d_idx = 4 * k
            if d_idx < n:
                domain_groups_l2.append(_DOMAINS[d_idx])
            else:
                domain_groups_l2.append(f"pad-group-{k}")

        for k, c in enumerate(l2_coeffs):
            if abs(c) > threshold and k < len(domain_groups_l2):
                anomalies.append({
                    "domain": domain_groups_l2[k],
                    "level": "L2",
                    "magnitude": round(abs(c), 4),
                })

        # L3/L4: coarse, map to first domain in block
        for k, c in enumerate(l3_coeffs):
            if abs(c) > threshold:
                d_idx = min(8 * k, n - 1)
                anomalies.append({
                    "domain": _DOMAINS[d_idx],
                    "level": "L3",
                    "magnitude": round(abs(c), 4),
                })
        for k, c in enumerate(l4_coeffs):
            if abs(c) > threshold:
                anomalies.append({
                    "domain": _DOMAINS[0],
                    "level": "L4",
                    "magnitude": round(abs(c), 4),
                })

        # Sort anomalies by magnitude desc
        anomalies.sort(key=lambda a: a["magnitude"], reverse=True)

        # Signal complexity
        # If energy is spread across levels => complex; concentrated => simple
        if detail_total < 1e-12:
            complexity = "Simple"
        else:
            # Normalized entropy of energy distribution across 4 levels
            fracs = [level_energies[lv] / detail_total for lv in ["L1", "L2", "L3", "L4"]]
            e_entropy = _shannon_entropy([f * 1000 for f in fracs])  # scale for int counts
            max_entropy = math.log2(4)  # max when uniform
            ratio = e_entropy / max_entropy if max_entropy > 0 else 0
            if ratio < 0.4:
                complexity = "Simple"
            elif ratio < 0.75:
                complexity = "Moderate"
            else:
                complexity = "Complex"

        # Insight
        insight_parts = [
            f"Dominant variation at {dominant} ({interpretations[dominant].split(' -- ')[0].lower()}).",
            f"Smoothness {smoothness:.2f} (1 = perfectly uniform, 0 = all variation).",
        ]
        if anomalies:
            top_anom = anomalies[0]
            insight_parts.append(
                f"Strongest anomaly near {top_anom['domain']} at level {top_anom['level']} "
                f"(magnitude {top_anom['magnitude']:.1f})."
            )
        if complexity == "Complex":
            insight_parts.append("The profile is complex with energy spread across all scales.")
        elif complexity == "Simple":
            insight_parts.append("The profile is simple, dominated by a single scale of variation.")

        return {
            "coefficients": coeff_dict,
            "energy_by_level": energy_by_level,
            "total_energy": round(total_energy, 4),
            "energy_distribution": energy_dist,
            "dominant_scale": dominant,
            "dominant_interpretation": interpretations[dominant],
            "smoothness": smoothness,
            "anomaly_coefficients": anomalies,
            "signal_complexity": complexity,
            "analysis_insight": "  ".join(insight_parts),
        }

    except Exception as exc:
        logger.error("wavelet_analysis failed: %s", exc, exc_info=True)
        empty_coeffs = {"L1": [], "L2": [], "L3": [], "L4": [], "approx": []}
        empty_energy = {"L1": 0.0, "L2": 0.0, "L3": 0.0, "L4": 0.0}
        return {
            "coefficients": empty_coeffs,
            "energy_by_level": empty_energy,
            "total_energy": 0.0,
            "energy_distribution": empty_energy,
            "dominant_scale": "L1",
            "dominant_interpretation": "Analysis incomplete.",
            "smoothness": 0.0,
            "anomaly_coefficients": [],
            "signal_complexity": "Simple",
            "analysis_insight": "Wavelet analysis could not be completed due to an internal error.",
        }
