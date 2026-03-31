"""
Cross-Domain Correlation Intelligence Engine for TerraScout AI.

Analyzes relationships between the 10 intelligence domains to discover hidden
dependencies, influence networks, anomalous patterns, and actionable insights.
Pure Python -- only stdlib imports (math, logging).

Public API:
    compute_correlation_matrix(scores, details, raw_data)
    compute_influence_network(correlation_matrix, scores)
    detect_anomalous_relationships(correlation_matrix, scores)
    generate_correlation_insights(corr_result, influence_result, anomalies, scores)
    compute_full_correlation_analysis(scores, details, raw_data)
"""

import logging
import math

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

DOMAINS = [
    "habitability", "agriculture", "ecology", "hazard_safety",
    "water_resources", "infrastructure", "climate_comfort",
    "economic_potential", "air_environment", "geological_stability",
]

_DOMAIN_LABELS = {
    "habitability": "Habitability", "agriculture": "Agriculture",
    "ecology": "Ecology", "hazard_safety": "Hazard Safety",
    "water_resources": "Water Resources", "infrastructure": "Infrastructure",
    "climate_comfort": "Climate Comfort", "economic_potential": "Economic Potential",
    "air_environment": "Air & Environment",
    "geological_stability": "Geological Stability",
}

# Theoretical base correlation matrix -- known geospatial relationships.
# Tuples: (domain_a, domain_b, correlation). Built into dict below.
_BASE_PAIRS = [
    ("agriculture", "habitability", 0.65), ("climate_comfort", "habitability", 0.80),
    ("habitability", "water_resources", 0.70), ("air_environment", "habitability", 0.60),
    ("habitability", "infrastructure", 0.55), ("habitability", "economic_potential", 0.50),
    ("habitability", "ecology", 0.35), ("geological_stability", "habitability", 0.30),
    ("habitability", "hazard_safety", 0.40), ("agriculture", "water_resources", 0.85),
    ("agriculture", "ecology", 0.45), ("agriculture", "climate_comfort", 0.70),
    ("agriculture", "geological_stability", 0.75), ("agriculture", "air_environment", 0.30),
    ("agriculture", "economic_potential", 0.55), ("agriculture", "infrastructure", 0.35),
    ("agriculture", "hazard_safety", 0.20), ("ecology", "water_resources", 0.65),
    ("air_environment", "ecology", 0.60), ("ecology", "climate_comfort", 0.40),
    ("ecology", "geological_stability", 0.35), ("ecology", "hazard_safety", 0.15),
    ("ecology", "infrastructure", -0.20), ("ecology", "economic_potential", -0.10),
    ("geological_stability", "hazard_safety", 0.75), ("hazard_safety", "infrastructure", -0.30),
    ("climate_comfort", "hazard_safety", 0.25), ("hazard_safety", "water_resources", 0.20),
    ("air_environment", "hazard_safety", 0.15), ("economic_potential", "hazard_safety", -0.15),
    ("climate_comfort", "water_resources", 0.50), ("infrastructure", "water_resources", 0.40),
    ("economic_potential", "water_resources", 0.35), ("air_environment", "water_resources", 0.30),
    ("geological_stability", "water_resources", 0.25), ("economic_potential", "infrastructure", 0.80),
    ("climate_comfort", "infrastructure", 0.25), ("air_environment", "infrastructure", -0.15),
    ("geological_stability", "infrastructure", 0.30), ("air_environment", "climate_comfort", 0.55),
    ("climate_comfort", "economic_potential", 0.30), ("climate_comfort", "geological_stability", 0.10),
    ("air_environment", "economic_potential", -0.10), ("economic_potential", "geological_stability", 0.25),
    ("air_environment", "geological_stability", 0.15),
]
_BASE_CORRELATIONS = {(a, b): v for a, b, v in _BASE_PAIRS}

_CLUSTER_DEFS = [
    ("Environmental Health", ["ecology", "water_resources", "air_environment"]),
    ("Human Development", ["habitability", "infrastructure", "economic_potential"]),
    ("Risk Factors", ["hazard_safety", "geological_stability"]),
    ("Agricultural Potential", ["agriculture", "water_resources", "climate_comfort"]),
]

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _ss(scores, d, default=50.0):
    """Safe score: return float score for domain *d*, defaulting to 50."""
    v = scores.get(d)
    if v is None:
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

def _key(a, b):
    return tuple(sorted((a, b)))

def _clamp(v, lo=-1.0, hi=1.0):
    return max(lo, min(hi, v))

def _label(d):
    return _DOMAIN_LABELS.get(d, d.replace("_", " ").title())

def compute_correlation_matrix(scores, details=None, raw_data=None):
    """Build a 10x10 correlation matrix estimating cross-domain relationships.

    Starts from predefined base correlations, then adjusts by score patterns:
    - Both domains >70 or both <30: strengthen by +0.10
    - One >70, other <30: weaken by -0.10
    - Clamp to [-1, 1]

    Returns dict with: matrix, domain_order, strongest_positive (top 5),
    strongest_negative (top 3), clusters.
    """
    # Initialise symmetric matrix (diagonal = 1.0, rest = 0.0)
    matrix = {d: {d2: (1.0 if d == d2 else 0.0) for d2 in DOMAINS} for d in DOMAINS}

    # Populate from base + score-based adjustments
    for (a, b), base_val in _BASE_CORRELATIONS.items():
        sa, sb = _ss(scores, a), _ss(scores, b)
        adj = 0.0
        if (sa > 70 and sb > 70) or (sa < 30 and sb < 30):
            adj = 0.10
        elif (sa > 70 and sb < 30) or (sb > 70 and sa < 30):
            adj = -0.10
        val = _clamp(base_val + adj)
        matrix[a][b] = val
        matrix[b][a] = val

    # Extract strongest positive / negative pairs
    scored_pairs, seen = [], set()
    for a in DOMAINS:
        for b in DOMAINS:
            if a == b:
                continue
            k = _key(a, b)
            if k in seen:
                continue
            seen.add(k)
            scored_pairs.append({"pair": (a, b), "correlation": matrix[a][b]})

    pos = sorted([p for p in scored_pairs if p["correlation"] > 0],
                 key=lambda p: p["correlation"], reverse=True)
    neg = sorted([p for p in scored_pairs if p["correlation"] < 0],
                 key=lambda p: p["correlation"])

    # Cluster identification
    clusters = []
    for cname, cdomains in _CLUSTER_DEFS:
        pair_vals = [matrix[da][db]
                     for i, da in enumerate(cdomains) for db in cdomains[i + 1:]]
        avg_corr = sum(pair_vals) / len(pair_vals) if pair_vals else 0.0
        qualifying = sum(1 for v in pair_vals if v > 0.5)
        if qualifying >= 1 and avg_corr > 0.40:
            clusters.append({"name": cname, "domains": cdomains,
                             "avg_correlation": round(avg_corr, 4)})

    log.debug("Correlation matrix: %d pos, %d neg links", len(pos), len(neg))
    return {
        "matrix": matrix, "domain_order": list(DOMAINS),
        "strongest_positive": pos[:5], "strongest_negative": neg[:3],
        "clusters": clusters,
    }

# ---------------------------------------------------------------------------
# 2. INFLUENCE NETWORK
# ---------------------------------------------------------------------------

def compute_influence_network(correlation_matrix, scores):
    """Build directed influence network: higher-scored domain influences lower.

    For pairs with |correlation| > 0.3:
      strength = |correlation| * |score_diff| / 100
      direction: from higher-scored to lower-scored domain

    Returns dict with: nodes, edges, most_influential, most_dependent, hub_score.
    """
    matrix = correlation_matrix
    edges = []
    inf_out = {d: 0.0 for d in DOMAINS}
    inf_in = {d: 0.0 for d in DOMAINS}
    hub = {d: 0.0 for d in DOMAINS}
    seen = set()

    for a in DOMAINS:
        for b in DOMAINS:
            if a == b:
                continue
            k = _key(a, b)
            if k in seen:
                continue
            seen.add(k)
            corr = matrix[a][b]
            if abs(corr) <= 0.3:
                continue
            sa, sb = _ss(scores, a), _ss(scores, b)
            strength = round(abs(corr) * abs(sa - sb) / 100.0, 4)
            src, tgt = (a, b) if sa >= sb else (b, a)
            edges.append({"from": src, "to": tgt,
                          "strength": strength, "correlation": round(corr, 4)})
            inf_out[src] += strength
            inf_in[tgt] += strength
            hub[src] += strength
            hub[tgt] += strength

    nodes = [{"domain": d, "score": _ss(scores, d),
              "influence_out": round(inf_out[d], 4),
              "influence_in": round(inf_in[d], 4)} for d in DOMAINS]
    most_inf = max(DOMAINS, key=lambda d: inf_out[d])
    most_dep = max(DOMAINS, key=lambda d: inf_in[d])
    hub = {d: round(v, 4) for d, v in hub.items()}

    log.debug("Influence network: %d edges, driver=%s, dep=%s",
              len(edges), most_inf, most_dep)
    return {"nodes": nodes, "edges": edges, "most_influential": most_inf,
            "most_dependent": most_dep, "hub_score": hub}

# ---------------------------------------------------------------------------
# 3. ANOMALOUS RELATIONSHIP DETECTION
# ---------------------------------------------------------------------------

def detect_anomalous_relationships(correlation_matrix, scores):
    """Find pairs where observed scores contradict expected correlations.

    DIVERGENT:  expected positive corr (>0.4) but one >65, other <35.
    CONVERGENT: expected negative corr (<-0.3) but both >60 or both <40.

    Returns list of anomaly dicts sorted by priority (HIGH first).
    """
    matrix = correlation_matrix
    anomalies, seen = [], set()

    for a in DOMAINS:
        for b in DOMAINS:
            if a == b:
                continue
            k = _key(a, b)
            if k in seen:
                continue
            seen.add(k)
            corr = matrix[a][b]
            sa, sb = _ss(scores, a), _ss(scores, b)
            anomaly = None

            # DIVERGENT: positive correlation but scores pull apart
            if corr > 0.4 and ((sa > 65 and sb < 35) or (sb > 65 and sa < 35)):
                gap = abs(sa - sb)
                prio = "HIGH" if gap > 45 else ("MEDIUM" if gap > 30 else "LOW")
                anomaly = {
                    "domain_a": a, "domain_b": b,
                    "expected_correlation": round(corr, 4),
                    "score_a": sa, "score_b": sb, "anomaly_type": "DIVERGENT",
                    "explanation": (
                        f"{_label(a)} ({sa:.0f}) and {_label(b)} ({sb:.0f}) are "
                        f"expected to move together (r={corr:.2f}), but diverge by "
                        f"{gap:.0f} points. This may indicate a local anomaly -- "
                        f"perhaps an artificial intervention or unique feature."
                    ),
                    "investigation_priority": prio,
                }

            # CONVERGENT: negative correlation but scores agree
            if corr < -0.3:
                both_hi = sa > 60 and sb > 60
                both_lo = sa < 40 and sb < 40
                if both_hi or both_lo:
                    direction = "high" if both_hi else "low"
                    prio = "MEDIUM" if abs(corr) > 0.4 else "LOW"
                    anomaly = {
                        "domain_a": a, "domain_b": b,
                        "expected_correlation": round(corr, 4),
                        "score_a": sa, "score_b": sb, "anomaly_type": "CONVERGENT",
                        "explanation": (
                            f"{_label(a)} ({sa:.0f}) and {_label(b)} ({sb:.0f}) are "
                            f"expected to be inversely related (r={corr:.2f}), yet "
                            f"both score {direction}. This convergence may signal an "
                            f"unusual regional characteristic."
                        ),
                        "investigation_priority": prio,
                    }

            if anomaly is not None:
                anomalies.append(anomaly)

    prio_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    anomalies.sort(key=lambda x: prio_order.get(x["investigation_priority"], 9))
    log.debug("Anomaly detection: %d anomalies", len(anomalies))
    return anomalies

# ---------------------------------------------------------------------------
# 4. INSIGHT GENERATION
# ---------------------------------------------------------------------------

def generate_correlation_insights(corr_result, influence_result, anomalies, scores):
    """Generate 5-8 human-readable insights from the correlation analysis.

    Types: DEPENDENCY, DRIVER, CLUSTER, ANOMALY, LEVERAGE, VULNERABILITY, SYNERGY.

    Returns list of dicts with: type, title, description, domains_involved,
    actionability, confidence.
    """
    insights = []
    edges = influence_result["edges"]
    nodes = {n["domain"]: n for n in influence_result["nodes"]}

    # -- DEPENDENCY: domain with highest influence_in -----------------------
    dep_d = influence_result["most_dependent"]
    dep_n = nodes[dep_d]
    if dep_n["influence_in"] > 0.05:
        feeders = sorted([e for e in edges if e["to"] == dep_d],
                         key=lambda e: e["strength"], reverse=True)
        if feeders:
            top_f = feeders[0]["from"]
            insights.append({
                "type": "DEPENDENCY",
                "title": f"{_label(dep_d)} depends heavily on {_label(top_f)}",
                "description": (
                    f"{_label(dep_d)} receives the most cross-domain influence "
                    f"(inward strength {dep_n['influence_in']:.3f}), with "
                    f"{_label(top_f)} as the primary driver. Changes in "
                    f"{_label(top_f)} are likely to cascade into "
                    f"{_label(dep_d)} outcomes."
                ),
                "domains_involved": [dep_d, top_f],
                "actionability": "HIGH",
                "confidence": min(0.95, 0.6 + dep_n["influence_in"]),
            })

    # -- DRIVER: domain that drives 3+ others ------------------------------
    out_map = {}
    for e in edges:
        out_map.setdefault(e["from"], []).append(e["to"])
    for drv, targets in out_map.items():
        if len(targets) >= 3:
            tl = ", ".join(_label(t) for t in targets[:4])
            insights.append({
                "type": "DRIVER",
                "title": f"{_label(drv)} is a multi-domain driver",
                "description": (
                    f"{_label(drv)} influences {len(targets)} other domains "
                    f"({tl}). With a score of {_ss(scores, drv):.0f}, it acts "
                    f"as a keystone factor for this location's overall profile."
                ),
                "domains_involved": [drv] + targets[:4],
                "actionability": "HIGH",
                "confidence": min(0.90, 0.5 + len(targets) * 0.1),
            })
            break  # one DRIVER insight

    # -- CLUSTER insights ---------------------------------------------------
    for cluster in corr_result.get("clusters", []):
        cn, cd = cluster["name"], cluster["domains"]
        avg_s = sum(_ss(scores, d) for d in cd) / len(cd)
        sw = "strong" if avg_s > 60 else "weak"
        insights.append({
            "type": "CLUSTER",
            "title": f"{cn} cluster is {sw} (avg {avg_s:.0f})",
            "description": (
                f"The {cn} cluster ({', '.join(_label(d) for d in cd)}) has avg "
                f"inter-correlation {cluster['avg_correlation']:.2f} and avg score "
                f"{avg_s:.0f}. "
                f"{'These domains reinforce each other positively.' if avg_s > 60 else 'Improving any member may lift the entire cluster.'}"
            ),
            "domains_involved": cd,
            "actionability": "MEDIUM" if avg_s > 60 else "HIGH",
            "confidence": min(0.85, 0.5 + cluster["avg_correlation"] * 0.4),
        })

    # -- ANOMALY insights (up to 2) ----------------------------------------
    for anom in anomalies[:2]:
        insights.append({
            "type": "ANOMALY",
            "title": (f"Unexpected {anom['anomaly_type'].lower()} pattern: "
                      f"{_label(anom['domain_a'])} vs {_label(anom['domain_b'])}"),
            "description": anom["explanation"],
            "domains_involved": [anom["domain_a"], anom["domain_b"]],
            "actionability": "MEDIUM",
            "confidence": 0.70 if anom["investigation_priority"] == "HIGH" else 0.55,
        })

    # -- LEVERAGE: most influential domain with room to grow ----------------
    lever_d = influence_result["most_influential"]
    lever_s = _ss(scores, lever_d)
    if lever_s < 75:
        tgts = [e["to"] for e in edges if e["from"] == lever_d]
        if tgts:
            insights.append({
                "type": "LEVERAGE",
                "title": f"Improving {_label(lever_d)} would cascade benefits",
                "description": (
                    f"{_label(lever_d)} scores {lever_s:.0f} but has the highest "
                    f"outward influence. Raising it closer to 80+ could positively "
                    f"impact {', '.join(_label(t) for t in tgts[:3])}, creating a "
                    f"multiplier effect across domains."
                ),
                "domains_involved": [lever_d] + tgts[:3],
                "actionability": "HIGH", "confidence": 0.75,
            })

    # -- VULNERABILITY: weakest domain in a qualifying cluster --------------
    for cluster in corr_result.get("clusters", []):
        cd = cluster["domains"]
        weakest = min(cd, key=lambda d: _ss(scores, d))
        ws = _ss(scores, weakest)
        avg = sum(_ss(scores, d) for d in cd) / len(cd)
        if ws < avg - 15:
            insights.append({
                "type": "VULNERABILITY",
                "title": f"{_label(weakest)} is the weak link in {cluster['name']}",
                "description": (
                    f"Within the {cluster['name']} cluster (avg {avg:.0f}), "
                    f"{_label(weakest)} lags at {ws:.0f} -- {avg - ws:.0f} points "
                    f"below average. This imbalance may drag down correlated "
                    f"domains and warrants targeted attention."
                ),
                "domains_involved": [weakest] + [d for d in cd if d != weakest],
                "actionability": "HIGH", "confidence": 0.80,
            })
            break  # one vulnerability

    # -- SYNERGY: two high-scoring domains with strong positive correlation -
    synergy_found = False
    for pi in corr_result.get("strongest_positive", []):
        a, b = pi["pair"]
        sa, sb = _ss(scores, a), _ss(scores, b)
        if sa > 65 and sb > 65 and pi["correlation"] > 0.6:
            insights.append({
                "type": "SYNERGY",
                "title": f"{_label(a)} and {_label(b)} are mutually reinforcing",
                "description": (
                    f"Both {_label(a)} ({sa:.0f}) and {_label(b)} ({sb:.0f}) score "
                    f"well with a strong correlation of {pi['correlation']:.2f}. "
                    f"This synergy creates a virtuous cycle -- strength in one "
                    f"domain supports the other."
                ),
                "domains_involved": [a, b],
                "actionability": "LOW", "confidence": 0.85,
            })
            synergy_found = True
            break

    # -- Fill to minimum of 5 insights if needed ----------------------------
    if len(insights) < 5:
        all_s = [_ss(scores, d) for d in DOMAINS]
        spread = max(all_s) - min(all_s) if all_s else 0
        best = max(DOMAINS, key=lambda d: _ss(scores, d))
        worst = min(DOMAINS, key=lambda d: _ss(scores, d))
        if spread > 40:
            insights.append({
                "type": "VULNERABILITY",
                "title": f"Large imbalance: {_label(best)} vs {_label(worst)}",
                "description": (
                    f"The strongest domain ({_label(best)}, {_ss(scores, best):.0f}) "
                    f"and weakest ({_label(worst)}, {_ss(scores, worst):.0f}) differ "
                    f"by {spread:.0f} points. This imbalance can create cascading "
                    f"weaknesses through correlated domains."
                ),
                "domains_involved": [best, worst],
                "actionability": "MEDIUM", "confidence": 0.70,
            })
    if len(insights) < 5 and not synergy_found:
        best_d = max(DOMAINS, key=lambda d: _ss(scores, d))
        insights.append({
            "type": "DRIVER",
            "title": f"{_label(best_d)} anchors the location profile",
            "description": (
                f"At {_ss(scores, best_d):.0f}, {_label(best_d)} is the top domain "
                f"and likely exerts positive influence on correlated domains. It "
                f"serves as the foundation for further improvements."
            ),
            "domains_involved": [best_d],
            "actionability": "LOW", "confidence": 0.65,
        })

    insights = insights[:8]
    log.debug("Generated %d correlation insights", len(insights))
    return insights

# ---------------------------------------------------------------------------
# 5. MASTER FUNCTION
# ---------------------------------------------------------------------------

def compute_full_correlation_analysis(scores, details=None, raw_data=None):
    """Run the complete cross-domain correlation analysis pipeline.

    Calls compute_correlation_matrix, compute_influence_network,
    detect_anomalous_relationships, and generate_correlation_insights,
    then builds a 2-3 sentence executive summary.

    Returns dict with: correlation_matrix, influence_network, anomalies,
    insights, summary.
    """
    details = details or {}
    raw_data = raw_data or {}
    full_scores = {d: _ss(scores, d) for d in DOMAINS}

    corr_result = compute_correlation_matrix(full_scores, details, raw_data)
    influence_result = compute_influence_network(corr_result["matrix"], full_scores)
    anomalies = detect_anomalous_relationships(corr_result["matrix"], full_scores)
    insights = generate_correlation_insights(
        corr_result, influence_result, anomalies, full_scores)
    summary = _build_summary(corr_result, influence_result, anomalies, full_scores)

    log.info("Correlation analysis: %d clusters, %d edges, %d anomalies, %d insights",
             len(corr_result["clusters"]), len(influence_result["edges"]),
             len(anomalies), len(insights))

    return {
        "correlation_matrix": corr_result,
        "influence_network": influence_result,
        "anomalies": anomalies,
        "insights": insights,
        "summary": summary,
    }

# ---------------------------------------------------------------------------
# SUMMARY BUILDER (internal)
# ---------------------------------------------------------------------------

def _build_summary(corr_result, influence_result, anomalies, scores):
    """Compose a 2-3 sentence executive summary."""
    parts = []

    # Strongest cluster
    clusters = corr_result.get("clusters", [])
    if clusters:
        best_c = max(clusters, key=lambda c: c["avg_correlation"])
        parts.append(f"The strongest domain cluster is {best_c['name']} "
                     f"(avg inter-correlation {best_c['avg_correlation']:.2f}).")
    else:
        parts.append("No strong domain clusters were identified at this location.")

    # Most influential domain
    driver = influence_result["most_influential"]
    ds = _ss(scores, driver)
    out_n = sum(1 for e in influence_result["edges"] if e["from"] == driver)
    parts.append(f"{_label(driver)} ({ds:.0f}) is the most influential domain, "
                 f"driving outcomes across {out_n} connected domains.")

    # Anomalies
    high_a = [a for a in anomalies if a["investigation_priority"] == "HIGH"]
    if high_a:
        a0 = high_a[0]
        parts.append(
            f"Critical anomaly detected: {_label(a0['domain_a'])} and "
            f"{_label(a0['domain_b'])} show an unexpected "
            f"{a0['anomaly_type'].lower()} pattern requiring investigation.")
    elif anomalies:
        parts.append(f"{len(anomalies)} minor anomalies were detected in "
                     f"cross-domain relationships.")
    else:
        parts.append("All cross-domain relationships are consistent with "
                     "expected patterns.")

    return " ".join(parts)
