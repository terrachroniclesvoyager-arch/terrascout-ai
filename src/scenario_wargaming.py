"""
Scenario Wargaming Engine for TerraScout AI.

Palantir-style "what-if" simulation engine that models cascading geospatial
effects across 10 intelligence domains.  Uses Markov chain-like state
transitions driven by an empirical influence matrix, random perturbation,
and greedy optimisation for intervention planning.

Only stdlib imports (math, random, logging).
"""

import logging
import math
import random

logger = logging.getLogger(__name__)

# ── Domain registry ────────────────────────────────────────────────────────
DOMAINS = [
    "habitability", "agriculture", "ecology", "hazard_safety",
    "water_resources", "infrastructure", "climate_comfort",
    "economic_potential", "air_environment", "geological_stability",
]

# ── Influence matrix ───────────────────────────────────────────────────────
# (source, target, coefficient) — coefficient fraction of source delta propagates.
INFLUENCE_MATRIX = [
    ("water_resources",      "agriculture",        0.40),
    ("agriculture",          "economic_potential",  0.30),
    ("infrastructure",       "economic_potential",  0.30),
    ("infrastructure",       "habitability",        0.20),
    ("hazard_safety",        "habitability",        0.30),
    ("hazard_safety",        "infrastructure",     -0.15),
    ("ecology",              "water_resources",     0.20),
    ("ecology",              "air_environment",     0.25),
    ("air_environment",      "habitability",        0.15),
    ("climate_comfort",      "agriculture",         0.20),
    ("geological_stability", "hazard_safety",       0.30),
    ("water_resources",      "ecology",             0.20),
    ("economic_potential",   "infrastructure",      0.15),
]

# Pre-build lookup: source -> [(target, coeff), ...]
_INFLUENCE_LOOKUP: dict = {}
for _src, _tgt, _coeff in INFLUENCE_MATRIX:
    _INFLUENCE_LOOKUP.setdefault(_src, []).append((_tgt, _coeff))


# ── Helpers ────────────────────────────────────────────────────────────────

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _overall(scores: dict) -> float:
    vals = [scores[d] for d in DOMAINS if d in scores]
    return round(sum(vals) / len(vals), 2) if vals else 0.0


def _normalise_scores(raw: dict) -> dict:
    return {d: _clamp(float(raw.get(d, 50.0))) for d in DOMAINS}


def _cascade_once(deltas: dict) -> dict:
    """One round of influence propagation (secondary deltas only)."""
    secondary: dict = {d: 0.0 for d in DOMAINS}
    for src in DOMAINS:
        src_delta = deltas.get(src, 0.0)
        if abs(src_delta) < 0.01:
            continue
        for tgt, coeff in _INFLUENCE_LOOKUP.get(src, []):
            secondary[tgt] += src_delta * coeff
    return secondary


def _describe_cascade(src: str, tgt: str, coeff: float, delta: float) -> str:
    direction = "boosted" if delta > 0 else "reduced"
    return (
        f"{src.replace('_', ' ').title()} change {direction} "
        f"{tgt.replace('_', ' ').title()} by {abs(round(delta, 1))} pts "
        f"({abs(round(coeff * 100))}% propagation)"
    )


# ── 1. run_scenario_wargame ───────────────────────────────────────────────

def run_scenario_wargame(scores: dict, scenario: dict) -> dict:
    """Execute a wargaming scenario and return a detailed timeline."""
    random.seed(42)
    current = _normalise_scores(scores)
    baseline = dict(current)
    name = scenario.get("name", "Unnamed Scenario")
    duration = max(1, int(scenario.get("duration_years", 3)))
    events = scenario.get("events", [])

    immediate_events = [e for e in events if e.get("timing") == "immediate"]
    delayed_events = [e for e in events if e.get("timing") == "delayed"]
    timeline: list = []
    all_cascade_descriptions: list = []

    prev_scores = dict(current)  # Track previous year scores for marginal deltas

    for year in range(duration + 1):
        year_events: list = []
        year_deltas: dict = {d: 0.0 for d in DOMAINS}

        # Apply scenario events
        if year == 0:
            for ev in immediate_events:
                dom, impact = ev.get("domain", ""), float(ev.get("impact", 0))
                if dom in current:
                    year_deltas[dom] += impact
                    sign = "+" if impact > 0 else ""
                    year_events.append(
                        f"[Immediate] {dom.replace('_', ' ').title()} {sign}{impact}"
                    )
        if year == 1:
            for ev in delayed_events:
                dom, impact = ev.get("domain", ""), float(ev.get("impact", 0))
                if dom in current:
                    year_deltas[dom] += impact
                    sign = "+" if impact > 0 else ""
                    year_events.append(
                        f"[Delayed] {dom.replace('_', ' ').title()} {sign}{impact}"
                    )

        # Apply deltas
        for d in DOMAINS:
            current[d] = _clamp(current[d] + year_deltas[d])

        # Cascade propagation — use MARGINAL (year-over-year) deltas
        # to avoid excessive compounding over multi-year scenarios.
        if year > 0:
            marginal_deltas = {d: current[d] - prev_scores[d] for d in DOMAINS}
            secondary = _cascade_once(marginal_deltas)
            for d in DOMAINS:
                if abs(secondary[d]) >= 0.01:
                    current[d] = _clamp(current[d] + secondary[d])
            # Record cascade descriptions
            for src in DOMAINS:
                if abs(marginal_deltas.get(src, 0.0)) < 0.5:
                    continue
                for tgt, coeff in _INFLUENCE_LOOKUP.get(src, []):
                    propagated = marginal_deltas[src] * coeff
                    if abs(propagated) >= 0.25:
                        desc = _describe_cascade(src, tgt, coeff, propagated)
                        if desc not in all_cascade_descriptions:
                            all_cascade_descriptions.append(desc)
                        if desc not in year_events:
                            year_events.append(desc)

        # Random noise
        if year > 0:
            for d in DOMAINS:
                current[d] = _clamp(current[d] + random.gauss(0, 1.5))

        snapshot = {d: round(current[d], 2) for d in DOMAINS}
        timeline.append({
            "year": year, "scores": dict(snapshot),
            "overall": _overall(snapshot), "events": list(year_events),
        })

        # Update prev_scores for next year's marginal delta calculation
        prev_scores = dict(current)

    # Final analysis
    final_scores = {d: round(current[d], 2) for d in DOMAINS}
    delta_from_baseline = {d: round(final_scores[d] - baseline[d], 2) for d in DOMAINS}
    final_overall = _overall(final_scores)
    overall_delta = round(final_overall - _overall(baseline), 2)

    return {
        "scenario_name": name,
        "timeline": timeline,
        "final_scores": final_scores,
        "final_overall": final_overall,
        "delta_from_baseline": delta_from_baseline,
        "overall_delta": overall_delta,
        "worst_domain": min(DOMAINS, key=lambda d: final_scores[d]),
        "most_improved": max(DOMAINS, key=lambda d: delta_from_baseline[d]),
        "cascade_effects": all_cascade_descriptions,
    }


# ── 2. get_predefined_scenarios ───────────────────────────────────────────

def _sc(name, desc, events, duration=3):
    """Shorthand scenario builder."""
    return {"name": name, "description": desc, "events": events,
            "duration_years": duration}


def _ev(domain, impact, timing="immediate"):
    """Shorthand event builder."""
    return {"domain": domain, "impact": impact, "timing": timing}


def get_predefined_scenarios() -> list:
    """Return 10 predefined wargaming scenarios."""
    return [
        _sc("Major Earthquake (M7)",
            "A magnitude-7.0 earthquake strikes the region, causing immediate "
            "structural damage, geological destabilisation, and delayed "
            "infrastructure degradation.",
            [_ev("hazard_safety", -40), _ev("geological_stability", -25),
             _ev("infrastructure", -20, "delayed")]),

        _sc("Severe Drought",
            "A multi-year drought depletes water resources, stresses agriculture, "
            "and degrades local ecosystems.",
            [_ev("water_resources", -35), _ev("agriculture", -25, "delayed"),
             _ev("ecology", -15, "delayed")]),

        _sc("Industrial Development",
            "A large industrial zone is established, boosting economic output and "
            "infrastructure but harming ecology and air quality.",
            [_ev("infrastructure", 30), _ev("economic_potential", 25, "delayed"),
             _ev("ecology", -15, "delayed"), _ev("air_environment", -10, "delayed")]),

        _sc("Conservation Program",
            "A government-backed conservation initiative protects ecosystems, "
            "improves water and air quality, with a small economic trade-off.",
            [_ev("ecology", 25), _ev("water_resources", 15, "delayed"),
             _ev("air_environment", 10, "delayed"),
             _ev("economic_potential", -5, "delayed")]),

        _sc("Major Flood Event",
            "Catastrophic flooding overwhelms drainage and emergency systems, "
            "damages crops, and threatens infrastructure.",
            [_ev("water_resources", -20), _ev("hazard_safety", -30),
             _ev("agriculture", -20, "delayed"),
             _ev("infrastructure", -15, "delayed")]),

        _sc("Green Energy Investment",
            "Major investment in renewable energy infrastructure improves the "
            "economy and environment simultaneously.",
            [_ev("infrastructure", 15), _ev("economic_potential", 20, "delayed"),
             _ev("air_environment", 15, "delayed"),
             _ev("climate_comfort", 5, "delayed")]),

        _sc("Urban Expansion",
            "Rapid urban sprawl expands infrastructure and commerce but encroaches "
            "on natural habitats and water sources.",
            [_ev("infrastructure", 25), _ev("economic_potential", 20),
             _ev("ecology", -20, "delayed"), _ev("water_resources", -10, "delayed"),
             _ev("air_environment", -10, "delayed")]),

        _sc("Climate Change (+2\u00b0C)",
            "A sustained 2 degree Celsius warming scenario plays out over 5 years, "
            "stressing agriculture, water, ecology and safety.",
            [_ev("climate_comfort", -15), _ev("water_resources", -10, "delayed"),
             _ev("agriculture", -15, "delayed"), _ev("ecology", -10, "delayed"),
             _ev("hazard_safety", -5, "delayed")],
            duration=5),

        _sc("Infrastructure Collapse",
            "Critical infrastructure fails catastrophically — roads, power, water "
            "networks — dragging down economy and liveability.",
            [_ev("infrastructure", -40), _ev("economic_potential", -25, "delayed"),
             _ev("habitability", -15, "delayed")]),

        _sc("Ecosystem Restoration",
            "A multi-year rewilding and habitat restoration programme gradually "
            "improves ecology, water, air and agriculture.",
            [_ev("ecology", 20), _ev("water_resources", 10, "delayed"),
             _ev("air_environment", 10, "delayed"),
             _ev("agriculture", 5, "delayed")]),
    ]


# ── 3. compare_scenarios ──────────────────────────────────────────────────

def compare_scenarios(scores: dict, scenario_names: list) -> dict:
    """Run several predefined scenarios and compare outcomes."""
    predefined = {s["name"]: s for s in get_predefined_scenarios()}
    comparisons: list = []

    for sname in scenario_names:
        scenario = predefined.get(sname)
        if scenario is None:
            logger.warning("Scenario '%s' not found — skipping.", sname)
            continue
        result = run_scenario_wargame(scores, scenario)
        od = result["overall_delta"]
        if od > 5:
            risk = "significant improvement"
        elif od > 1:
            risk = "moderate improvement"
        elif od > -1:
            risk = "negligible change"
        elif od > -5:
            risk = "moderate degradation"
        else:
            risk = "significant degradation"
        comparisons.append({
            "name": sname, "final_overall": result["final_overall"],
            "overall_delta": od, "risk_change": risk,
        })

    if not comparisons:
        return {"comparisons": [], "best_outcome": "N/A",
                "worst_outcome": "N/A", "recommended": "N/A", "ranking": []}

    comparisons.sort(key=lambda c: c["final_overall"], reverse=True)
    ranking = [c["name"] for c in comparisons]
    positive = [c for c in comparisons if c["overall_delta"] > 0]
    if positive:
        recommended = max(positive, key=lambda c: c["final_overall"])["name"]
    else:
        recommended = max(comparisons, key=lambda c: c["overall_delta"])["name"]

    return {
        "comparisons": comparisons,
        "best_outcome": comparisons[0]["name"],
        "worst_outcome": comparisons[-1]["name"],
        "recommended": recommended,
        "ranking": ranking,
    }


# ── 4. compute_intervention_matrix ────────────────────────────────────────

def compute_intervention_matrix(scores: dict) -> dict:
    """Model the effect of a +20 boost to each domain on every other domain.

    Returns a 10x10 impact matrix plus rankings of the most effective
    single-domain interventions.
    """
    random.seed(42)
    base = _normalise_scores(scores)
    boost = 20.0
    impact_matrix: dict = {}
    rankings: list = []

    for i_dom in DOMAINS:
        scenario = {
            "name": f"Boost {i_dom}", "description": f"+{boost} to {i_dom}",
            "events": [{"domain": i_dom, "impact": boost, "timing": "immediate"}],
            "duration_years": 3,
        }
        result = run_scenario_wargame(base, scenario)
        deltas = result["delta_from_baseline"]
        row = {d: round(deltas.get(d, 0.0), 2) for d in DOMAINS}
        impact_matrix[i_dom] = row

        pos = sum(v for v in row.values() if v > 0)
        neg = sum(v for v in row.values() if v < 0)
        rankings.append({
            "domain": i_dom,
            "total_positive_impact": round(pos, 2),
            "total_negative_impact": round(neg, 2),
            "net_impact": round(pos + neg, 2),
        })

    rankings.sort(key=lambda r: r["net_impact"], reverse=True)
    return {
        "impact_matrix": impact_matrix,
        "most_impactful_intervention": rankings[0]["domain"] if rankings else "N/A",
        "intervention_rankings": rankings,
    }


# ── 5. find_optimal_intervention ──────────────────────────────────────────

def find_optimal_intervention(scores: dict, budget: int = 100) -> dict:
    """Find the best way to distribute *budget* score points across domains.

    Uses greedy hill-climbing (50 iterations) to maximise the overall score
    after a 1-year wargame simulation.
    """
    random.seed(42)
    base = _normalise_scores(scores)
    baseline_overall = _overall(base)
    n = len(DOMAINS)
    per_domain = budget / n
    allocation = {d: per_domain for d in DOMAINS}

    def _evaluate(alloc: dict) -> float:
        evts = [{"domain": d, "impact": alloc.get(d, 0.0), "timing": "immediate"}
                for d in DOMAINS if abs(alloc.get(d, 0.0)) > 0.01]
        random.seed(42)
        return run_scenario_wargame(base, {
            "name": "Intervention", "description": "Optimisation probe",
            "events": evts, "duration_years": 1,
        })["final_overall"]

    best_overall = _evaluate(allocation)
    best_alloc = dict(allocation)
    step = 5.0

    for _ in range(50):
        # Marginal contribution ranking
        marginals = []
        for d in DOMAINS:
            test = dict(best_alloc)
            test[d] += 1.0
            others = [x for x in DOMAINS if x != d]
            donor = min(others, key=lambda x: test[x])
            test[donor] -= 1.0
            if test[donor] < 0:
                marginals.append((d, best_overall))
                continue
            marginals.append((d, _evaluate(test)))
        marginals.sort(key=lambda m: m[1], reverse=True)

        best_dom, worst_dom = marginals[0][0], marginals[-1][0]
        if best_alloc[worst_dom] >= step:
            candidate = dict(best_alloc)
            candidate[worst_dom] -= step
            candidate[best_dom] += step
            val = _evaluate(candidate)
            if val > best_overall:
                best_overall = val
                best_alloc = candidate

    # Final cascade evaluation
    random.seed(42)
    final_evts = [{"domain": d, "impact": best_alloc[d], "timing": "immediate"}
                  for d in DOMAINS if abs(best_alloc[d]) > 0.01]
    final_result = run_scenario_wargame(base, {
        "name": "Optimal Intervention", "description": "Hill-climbing optimised",
        "events": final_evts, "duration_years": 1,
    })
    expected_after = final_result["final_overall"]

    # Key investments (above 1.5x average)
    avg = budget / n
    key_inv = []
    for d in DOMAINS:
        pts = best_alloc[d]
        if pts > avg * 1.5:
            key_inv.append(
                f"Invest {round(pts, 1)} pts in "
                f"{d.replace('_', ' ').title()} "
                f"(+{round(pts - avg, 1)} above average)"
            )
    if not key_inv:
        for d, pts in sorted(best_alloc.items(), key=lambda kv: kv[1], reverse=True)[:3]:
            key_inv.append(f"Invest {round(pts, 1)} pts in {d.replace('_', ' ').title()}")

    return {
        "optimal_allocation": {d: round(v, 2) for d, v in best_alloc.items()},
        "expected_overall": round(best_overall, 2),
        "improvement_over_baseline": round(best_overall - baseline_overall, 2),
        "expected_overall_after_cascade": round(expected_after, 2),
        "key_investments": key_inv,
    }


# ── 6. generate_wargame_narrative ─────────────────────────────────────────

def generate_wargame_narrative(wargame_result: dict) -> str:
    """Generate a 3-5 sentence narrative summary of a wargame result.

    Covers what happened, cascade effects, final state, and key takeaway.
    """
    name = wargame_result.get("scenario_name", "Unknown scenario")
    overall_delta = wargame_result.get("overall_delta", 0.0)
    final_overall = wargame_result.get("final_overall", 0.0)
    worst = wargame_result.get("worst_domain", "unknown")
    most_improved = wargame_result.get("most_improved", "unknown")
    cascades = wargame_result.get("cascade_effects", [])
    delta_map = wargame_result.get("delta_from_baseline", {})
    timeline = wargame_result.get("timeline", [])
    duration = len(timeline) - 1 if timeline else 0

    # Sentence 1: what happened
    if overall_delta > 5:
        trend = "significantly improved conditions"
    elif overall_delta > 0:
        trend = "a modest overall improvement"
    elif overall_delta > -5:
        trend = "a slight overall decline"
    else:
        trend = "a substantial overall deterioration"
    s1 = (
        f"The \"{name}\" scenario was simulated over {duration} year"
        f"{'s' if duration != 1 else ''}, resulting in {trend} "
        f"(overall delta: {'+' if overall_delta > 0 else ''}{overall_delta})."
    )

    # Sentence 2: cascade effects
    if cascades:
        s2 = (
            f"The simulation identified {len(cascades)} cascade "
            f"effect{'s' if len(cascades) != 1 else ''} across domains; "
            f"for example, {cascades[0].lower()}."
        )
    else:
        s2 = "No significant cascade effects were detected between domains."

    # Sentence 3: final state
    worst_score = wargame_result.get("final_scores", {}).get(worst, 0)
    mi_delta = delta_map.get(most_improved, 0)
    s3 = (
        f"The weakest domain at simulation end is "
        f"{worst.replace('_', ' ').title()} at {worst_score}, while "
        f"{most_improved.replace('_', ' ').title()} showed the greatest "
        f"positive change ({'+' if mi_delta > 0 else ''}{mi_delta})."
    )

    # Sentence 4: key takeaway
    worsened = [d for d, v in delta_map.items() if v < -2]
    improved = [d for d, v in delta_map.items() if v > 2]
    if len(worsened) > len(improved):
        s4 = (
            f"Key takeaway: this scenario is predominantly destructive, "
            f"degrading {len(worsened)} of 10 domains; mitigation "
            f"strategies should prioritise "
            f"{worst.replace('_', ' ').title()} recovery."
        )
    elif len(improved) > len(worsened):
        s4 = (
            f"Key takeaway: this is a net-positive scenario improving "
            f"{len(improved)} domains, though decision-makers should "
            f"monitor the {len(worsened)} domain"
            f"{'s' if len(worsened) != 1 else ''} that declined."
        )
    else:
        s4 = (
            "Key takeaway: the scenario produces a mixed outcome with "
            "roughly balanced improvements and degradations — careful "
            "trade-off analysis is recommended."
        )

    # Sentence 5: overall rating
    if final_overall >= 75:
        rating = "favourable"
    elif final_overall >= 50:
        rating = "moderate"
    elif final_overall >= 30:
        rating = "concerning"
    else:
        rating = "critical"
    s5 = (
        f"Final overall score of {final_overall}/100 places the location "
        f"in a {rating} state post-scenario."
    )

    return "  ".join([s1, s2, s3, s4, s5])


# ── Convenience: run all predefined and summarise ─────────────────────────

def run_all_predefined(scores: dict) -> list:
    """Run every predefined scenario and return summary list."""
    results = []
    for scenario in get_predefined_scenarios():
        wg = run_scenario_wargame(scores, scenario)
        results.append({
            "name": wg["scenario_name"],
            "final_overall": wg["final_overall"],
            "overall_delta": wg["overall_delta"],
            "worst_domain": wg["worst_domain"],
            "most_improved": wg["most_improved"],
            "narrative": generate_wargame_narrative(wg),
        })
    return results


# ── Self-test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_scores = {
        "habitability": 65, "agriculture": 55, "ecology": 60,
        "hazard_safety": 50, "water_resources": 58, "infrastructure": 62,
        "climate_comfort": 70, "economic_potential": 48,
        "air_environment": 72, "geological_stability": 45,
    }

    print("=" * 70)
    print("TERRASCOUT AI — SCENARIO WARGAMING ENGINE")
    print("=" * 70)

    # Test 1: single scenario
    scenarios = get_predefined_scenarios()
    result = run_scenario_wargame(test_scores, scenarios[0])
    print(f"\n[1] {result['scenario_name']}")
    print(f"    Overall: {result['final_overall']} (delta {result['overall_delta']})")
    print(f"    Worst: {result['worst_domain']}  Best: {result['most_improved']}")
    print(f"    Cascades: {len(result['cascade_effects'])}")

    # Test 2: narrative
    print(f"\n[2] Narrative:\n    {generate_wargame_narrative(result)}")

    # Test 3: compare
    cmp = compare_scenarios(test_scores,
        ["Major Earthquake (M7)", "Green Energy Investment", "Urban Expansion"])
    print(f"\n[3] Best: {cmp['best_outcome']}  Worst: {cmp['worst_outcome']}")
    print(f"    Recommended: {cmp['recommended']}")

    # Test 4: intervention matrix
    mx = compute_intervention_matrix(test_scores)
    print(f"\n[4] Most impactful: {mx['most_impactful_intervention']}")

    # Test 5: optimal intervention
    opt = find_optimal_intervention(test_scores, budget=100)
    print(f"\n[5] Expected: {opt['expected_overall']} (+{opt['improvement_over_baseline']})")
    for inv in opt["key_investments"]:
        print(f"    - {inv}")

    print("\n" + "=" * 70 + "\nAll tests passed.")
