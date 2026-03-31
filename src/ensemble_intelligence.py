"""
Ensemble Intelligence Engine -- Meta-Intelligence Brain of TerraScout AI.

Fuses ALL analytical engines (strategic synthesis, Monte Carlo, threat radar,
correlation intelligence, predictive outlook, decision trees, wargaming, BBN,
PCA, kriging) into a single unified ensemble assessment with cross-method
validation, definitive recommendations, and an executive verdict.

Pure Python -- only stdlib imports (math, logging).
"""
import math
import logging

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────

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
    "air_environment": "Air & Environment", "geological_stability": "Geological Stability",
}
_DEFAULT_WEIGHTS = {
    "domain_score": 0.25, "strategic_score": 0.20, "mc_expected": 0.15,
    "threat_adjusted": 0.15, "dt_viability": 0.10, "bbn_posterior": 0.10,
    "geopolitical": 0.05,
}
_CLASSIFICATIONS = [
    (80, "PRIME ASSET", "#00C853"), (65, "HIGH VALUE", "#00BCD4"),
    (50, "VIABLE", "#2196F3"), (35, "MARGINAL", "#FFC107"),
    (20, "CHALLENGED", "#FF9800"), (0, "CRITICAL", "#F44336"),
]
_ALGO_NAMES = {
    "domain_score": "Domain Scoring", "strategic_score": "Strategic Synthesis",
    "mc_expected": "Monte Carlo Simulation", "threat_adjusted": "Threat Assessment",
    "dt_viability": "Decision Tree Analysis", "bbn_posterior": "Bayesian Belief Network",
    "geopolitical": "Geopolitical Engine",
}
_ACTION_TEMPLATES = {
    "water_resources": "Develop water infrastructure (wells, reservoirs, treatment)",
    "infrastructure": "Invest in transport, power grid, and connectivity",
    "hazard_safety": "Implement disaster preparedness and early warning systems",
    "agriculture": "Enhance agricultural productivity through soil and irrigation",
    "habitability": "Improve housing, sanitation, and livability standards",
    "ecology": "Restore ecosystems and establish conservation corridors",
    "economic_potential": "Stimulate economic activity through investment incentives",
    "climate_comfort": "Deploy climate adaptation and resilience measures",
    "air_environment": "Reduce pollution sources and improve air quality monitoring",
    "geological_stability": "Conduct geotechnical surveys and reinforce structures",
}

# ── Helpers ───────────────────────────────────────────────────────────────

def _sg(obj, *keys, default=None):
    """Safe nested-dict get."""
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
        if cur is default:
            return default
    return cur

def _mean(v):
    return sum(v) / len(v) if v else 0.0

def _std(v, mu=None):
    if len(v) < 2:
        return 0.0
    mu = mu if mu is not None else _mean(v)
    return math.sqrt(sum((x - mu) ** 2 for x in v) / len(v))

def _clamp(val, lo=0.0, hi=100.0):
    return max(lo, min(hi, val))

def _classify(score):
    for th, label, color in _CLASSIFICATIONS:
        if score >= th:
            return label, color
    return "CRITICAL", "#F44336"

# ══════════════════════════════════════════════════════════════════════════
# 1. compute_ensemble_assessment  (MASTER FUNCTION)
# ══════════════════════════════════════════════════════════════════════════

def compute_ensemble_assessment(hub_data, strategic, threats, mc_result,
                                corr_intel, predictive, dt_results,
                                wargaming_intervention, bbn, pca, kriging):
    """Fuse ALL intelligence products into one unified ensemble assessment."""
    logger.info("Computing ensemble assessment")
    hub_data = hub_data or {}; strategic = strategic or {}
    threats = threats or {}; mc_result = mc_result or {}
    corr_intel = corr_intel or {}; predictive = predictive or {}
    dt_results = dt_results or {}; wargaming_intervention = wargaming_intervention or {}
    bbn = bbn or {}; pca = pca or {}; kriging = kriging or {}

    scores = hub_data.get("scores", {})
    _conf_raw = hub_data.get("confidence", 0.5)
    data_conf = float(_conf_raw.get("overall", 0.5)) if isinstance(_conf_raw, dict) else float(_conf_raw)

    # A. Multi-algorithm score fusion
    comp = _extract_component_scores(hub_data, strategic, threats, mc_result, dt_results, bbn)
    weights = compute_method_reliability_weights(mc_result, data_conf)
    ens, tw = 0.0, 0.0
    for k, w in weights.items():
        v = comp.get(k)
        if v is not None:
            ens += v * w; tw += w
    if tw > 0:
        ens /= tw
    ens = _clamp(ens)
    classification, color = _classify(ens)

    # B. Algorithm agreement index
    valid = [v for v in comp.values() if v is not None]
    agr_idx = _clamp(100.0 - _std(valid) * 3.0) if len(valid) >= 2 else 50.0
    if agr_idx < 40:
        agr_lbl = "CONFLICTING SIGNALS"
    elif agr_idx <= 70:
        agr_lbl = "PARTIAL AGREEMENT"
    else:
        agr_lbl = "STRONG CONSENSUS"

    # C. Meta-confidence
    mc = data_conf
    if agr_idx > 70: mc += 0.05
    if agr_idx < 40: mc -= 0.10
    if _sg(mc_result, "overall", "std", default=99.0) < 5: mc += 0.05
    mc = max(0.1, min(0.99, mc))

    # E. Cross-method validation
    unc_dom, cross_val = _cross_method_validation(scores, bbn, mc_result, predictive)

    # F. Definitive recommendations
    recs = _build_definitive_recommendations(
        scores, dt_results, wargaming_intervention, predictive, threats, corr_intel, comp)

    verdict = generate_executive_verdict(ens, classification, agr_lbl,
                                          threats, strategic, dt_results, predictive)
    liner = generate_one_liner(ens, classification, agr_lbl)

    return {
        "ensemble_score": round(ens, 2),
        "ensemble_classification": classification,
        "ensemble_color": color,
        "algorithm_agreement": round(agr_idx, 2),
        "agreement_label": agr_lbl,
        "meta_confidence": round(mc, 4),
        "component_scores": {k: (round(v, 2) if v is not None else None)
                             for k, v in comp.items()},
        "uncertain_domains": unc_dom,
        "cross_validation": cross_val,
        "definitive_recommendations": recs,
        "executive_verdict": verdict,
        "one_liner": liner,
    }


def _extract_component_scores(hub, strat, threats, mc, dt, bbn):
    """Pull normalised 0-100 score from each intelligence product."""
    ds = hub.get("overall_score")
    ds = float(ds) if ds is not None else None

    ss = strat.get("strategic_score")
    ss = float(ss) if ss is not None else None

    mce = _sg(mc, "overall", "mean")
    mce = float(mce) if mce is not None else None

    tr = threats.get("threat_score")
    ta = (100.0 - float(tr)) if tr is not None else None

    go = dt.get("go_scenarios", [])
    cau = dt.get("caution_scenarios", [])
    nog = dt.get("no_go_scenarios", [])
    tot = len(go) + len(cau) + len(nog)
    dtv = ((len(go) + 0.5 * len(cau)) / tot * 100.0) if tot > 0 else None

    post = bbn.get("posteriors", {})
    bp = None
    if post:
        pv = [float(v) for v in post.values() if v is not None]
        bp = _mean(pv) * 100.0 if pv else None

    geo = _sg(hub, "raw_data", "geopolitical")
    gp = None
    if isinstance(geo, dict):
        gs = geo.get("geopolitical_score")
        if gs is not None:
            gp = float(gs)

    return {"domain_score": ds, "strategic_score": ss, "mc_expected": mce,
            "threat_adjusted": ta, "dt_viability": dtv, "bbn_posterior": bp,
            "geopolitical": gp}

# ══════════════════════════════════════════════════════════════════════════
# Cross-method validation
# ══════════════════════════════════════════════════════════════════════════

def _cross_method_validation(scores, bbn, mc_result, predictive):
    """Compare methods per domain; flag >15-point disagreements."""
    posteriors = bbn.get("posteriors", {})
    mc_dists = mc_result.get("domain_distributions", {})
    dfc = predictive.get("domain_forecasts", {})
    uncertain, strengths, weaknesses, disputed = [], [], [], []

    for domain in DOMAINS:
        label = _DOMAIN_LABELS.get(domain, domain)
        ms = {}
        raw = scores.get(domain)
        if raw is not None: ms["domain_score"] = float(raw)
        bv = posteriors.get(domain)
        if bv is not None: ms["bbn_posterior"] = float(bv) * 100.0
        mcm = mc_dists.get(_DOMAIN_LABELS.get(domain, domain), {}).get("mean")
        if mcm is not None: ms["mc_mean"] = float(mcm)
        sv = _sg(dfc.get(domain, {}), "short_term", "value")
        if sv is not None: ms["predictive_forecast"] = float(sv)
        if len(ms) < 2:
            continue
        vals = list(ms.values())
        spread = max(vals) - min(vals)
        if spread > 15:
            uncertain.append({"domain": label,
                              "scores": {k: round(v, 2) for k, v in ms.items()},
                              "spread": round(spread, 2)})
            disputed.append(label)
        else:
            avg = _mean(vals)
            if avg >= 65: strengths.append(label)
            elif avg <= 35: weaknesses.append(label)

    return uncertain, {"validated_strengths": strengths,
                       "validated_weaknesses": weaknesses, "disputed": disputed}

# ══════════════════════════════════════════════════════════════════════════
# Definitive recommendations
# ══════════════════════════════════════════════════════════════════════════

def _build_definitive_recommendations(scores, dt_results, wg_int, predictive,
                                       threats, corr_intel, comp):
    """Top-5 recommendations ranked by multi-method support, impact, urgency."""
    d_support, d_impact, d_urgency = {}, {}, {}

    for domain in DOMAINS:
        sup, raw = 0, scores.get(domain, 50)
        if raw < 50: sup += 1
        for _, r in dt_results.get("results", {}).items():
            if domain in r.get("key_factors", []):
                sup += 1; break
        for t in threats.get("threats", []):
            if domain in t.get("affected_domains", []):
                sup += 1; break
        ins = corr_intel.get("insights", [])
        if isinstance(ins, list):
            for i in ins:
                txt = i if isinstance(i, str) else str(i)
                if domain.replace("_", " ") in txt.lower():
                    sup += 1; break
        df = predictive.get("domain_forecasts", {}).get(domain, {})
        lv = _sg(df, "long_term", "value")
        cur = df.get("current", raw)
        if lv is not None and float(lv) < float(cur) - 5: sup += 1
        d_support[domain] = min(sup, 5)

    ranks = wg_int.get("intervention_rankings", [])
    rmap = {r["domain"]: r for r in ranks if isinstance(r, dict)}
    for d in DOMAINS:
        net = rmap.get(d, {}).get("net_impact", 0)
        d_impact[d] = "HIGH" if net > 15 else ("MEDIUM" if net > 5 else "LOW")

    dfc = predictive.get("domain_forecasts", {})
    for d in DOMAINS:
        fc = dfc.get(d, {})
        sv = _sg(fc, "short_term", "value")
        c = float(fc.get("current", scores.get(d, 50)))
        if sv is not None and float(sv) < c - 10: d_urgency[d] = "IMMEDIATE"
        elif sv is not None and float(sv) < c - 3: d_urgency[d] = "SHORT_TERM"
        else:
            lv = _sg(fc, "long_term", "value")
            d_urgency[d] = "MEDIUM_TERM" if (lv is not None and float(lv) < c - 10) else "LONG_TERM"

    iv = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
    uv = {"IMMEDIATE": 4, "SHORT_TERM": 3, "MEDIUM_TERM": 2, "LONG_TERM": 1}
    cands = []
    for d in DOMAINS:
        s = d_support.get(d, 0)
        imp = d_impact.get(d, "LOW"); urg = d_urgency.get(d, "LONG_TERM")
        i_n = iv.get(imp, 1); u_n = uv.get(urg, 1)
        comp_sc = s * 3.0 + i_n * 2.0 + u_n * 1.5
        if s > 0 or i_n >= 2 or u_n >= 3:
            src = []
            if scores.get(d, 50) < 50: src.append("Domain Scoring")
            if s >= 2: src.append("Multi-Algorithm Cross-Check")
            if i_n >= 2: src.append("Wargaming Intervention Matrix")
            if u_n >= 3: src.append("Predictive Engine")
            if not src: src.append("Ensemble Analysis")
            cands.append({"action": _ACTION_TEMPLATES.get(d, f"Address {d} gaps"),
                          "multi_method_support": s, "impact": imp, "urgency": urg,
                          "source_algorithms": src, "_c": comp_sc})

    cands.sort(key=lambda c: c["_c"], reverse=True)
    result = []
    for rank, e in enumerate(cands[:5], 1):
        rec = dict(e); rec["rank"] = rank; rec.pop("_c", None)
        result.append(rec)
    if not result:
        result.append({"rank": 1,
                       "action": "Conduct comprehensive field validation to verify data",
                       "multi_method_support": 1, "impact": "MEDIUM",
                       "urgency": "SHORT_TERM", "source_algorithms": ["Ensemble Analysis"]})
    return result

# ══════════════════════════════════════════════════════════════════════════
# 2. compute_algorithm_convergence
# ══════════════════════════════════════════════════════════════════════════

def compute_algorithm_convergence(component_scores):
    """Pairwise convergence analysis between all algorithms."""
    valid = {k: v for k, v in (component_scores or {}).items() if v is not None}
    keys = sorted(valid.keys())
    if len(keys) < 2:
        return {"pairs": [], "most_aligned": (None, None),
                "most_divergent": (None, None), "convergence_score": 0.0}

    pairs, min_d, max_d = [], float("inf"), float("-inf")
    aligned = (keys[0], keys[1]); divergent = (keys[0], keys[1])
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            d = abs(valid[a] - valid[b])
            agr = "STRONG" if d < 5 else ("MODERATE" if d < 15 else ("WEAK" if d < 25 else "DIVERGENT"))
            pairs.append({"algo_a": _ALGO_NAMES.get(a, a), "algo_b": _ALGO_NAMES.get(b, b),
                          "delta": round(d, 2), "agreement": agr})
            if d < min_d: min_d = d; aligned = (_ALGO_NAMES.get(a, a), _ALGO_NAMES.get(b, b))
            if d > max_d: max_d = d; divergent = (_ALGO_NAMES.get(a, a), _ALGO_NAMES.get(b, b))

    cs = _clamp(100.0 - _std(list(valid.values())) * 3.0)
    return {"pairs": pairs, "most_aligned": aligned, "most_divergent": divergent,
            "convergence_score": round(cs, 2)}

# ══════════════════════════════════════════════════════════════════════════
# 3. generate_executive_verdict
# ══════════════════════════════════════════════════════════════════════════

def generate_executive_verdict(ensemble_score, classification, agreement_label,
                                threats, strategic, dt_results, predictive):
    """3-4 sentence definitive verdict about the location."""
    threats = threats or {}; strategic = strategic or {}
    dt_results = dt_results or {}; predictive = predictive or {}

    s1 = (f"This location is classified as {classification} with an ensemble "
          f"score of {ensemble_score:.1f}/100 and {agreement_label} across "
          f"7 analytical methods.")

    dims = strategic.get("dimensions", {})
    if dims:
        def _dim_score(d):
            v = dims[d]
            return v.get("score", 0) if isinstance(v, dict) else float(v) if v is not None else 0
        best = max(dims, key=_dim_score)
        worst = min(dims, key=_dim_score)
        bs, ws = _dim_score(best), _dim_score(worst)
        s2 = (f"Primary strength is {best} ({bs:.0f}/100), "
              f"while {worst} ({ws:.0f}/100) is the "
              f"most significant constraint.")
    else:
        gl = dt_results.get("go_scenarios", [])
        nl = dt_results.get("no_go_scenarios", [])
        if gl: s2 = f"The location is viable for {len(gl)} assessed use-case scenario(s)."
        elif nl: s2 = f"Significant limitations: {len(nl)} scenario(s) received NO_GO verdicts."
        else: s2 = "Insufficient data to identify definitive strengths or weaknesses."

    ts = threats.get("threat_score", 0)
    tl = threats.get("threat_level", "UNKNOWN")
    df = predictive.get("domain_forecasts", {})
    dec = [d for d, f in df.items()
           if _sg(f, "long_term", "value", default=50) < f.get("current", 50) - 10]
    imp = [d for d, f in df.items()
           if _sg(f, "long_term", "value", default=50) > f.get("current", 50) + 5]

    if ts > 50:
        s3 = f"Active threat level is {tl} ({ts:.0f}/100), requiring immediate risk mitigation."
    elif dec:
        ns = [_DOMAIN_LABELS.get(d, d) for d in dec[:3]]
        s3 = f"Projected decline in {', '.join(ns)} warrants proactive intervention within 1-5 years."
    elif imp:
        ns = [_DOMAIN_LABELS.get(d, d) for d in imp[:3]]
        s3 = f"Positive trajectory in {', '.join(ns)} presents a development opportunity window."
    else:
        s3 = "Risk profile is moderate with no critical threats detected in the near term."

    if ensemble_score >= 80: s4 = "Recommended for priority development with standard monitoring."
    elif ensemble_score >= 65: s4 = "Proceed with targeted investment, addressing weaknesses first."
    elif ensemble_score >= 50: s4 = "Viable with conditions; field validation recommended first."
    elif ensemble_score >= 35: s4 = "Marginal viability; extensive feasibility study recommended."
    elif ensemble_score >= 20: s4 = "Significant challenges; only proceed with substantial support."
    else: s4 = "Not recommended without transformative intervention."

    return f"{s1} {s2} {s3} {s4}"

# ══════════════════════════════════════════════════════════════════════════
# 4. generate_one_liner
# ══════════════════════════════════════════════════════════════════════════

def generate_one_liner(ensemble_score, classification, agreement_label):
    """Single sentence: 'CLASSIFICATION (SCORE/100) -- AGREEMENT'."""
    return f"{classification} ({ensemble_score:.1f}/100) -- {agreement_label}"

# ══════════════════════════════════════════════════════════════════════════
# 5. compute_method_reliability_weights
# ══════════════════════════════════════════════════════════════════════════

def compute_method_reliability_weights(mc_result, data_confidence):
    """Dynamically adjust algorithm weights based on MC volatility and
    data confidence. Returns re-normalised weight dict."""
    w = dict(_DEFAULT_WEIGHTS)
    mc_result = mc_result or {}

    mc_std = _sg(mc_result, "overall", "std", default=10.0)
    if mc_std > 15:
        shift = min(0.05, (mc_std - 15) * 0.005)
        w["mc_expected"] = max(0.02, w["mc_expected"] - shift)
        w["domain_score"] += shift * 0.6
        w["strategic_score"] += shift * 0.4
    elif mc_std < 3:
        w["mc_expected"] += 0.03; w["domain_score"] -= 0.03

    if data_confidence < 0.5:
        pen = (0.5 - data_confidence) * 0.15
        for k in ["domain_score", "threat_adjusted", "geopolitical"]:
            w[k] = max(0.02, w[k] - pen / 3)
        for k in ["bbn_posterior", "dt_viability", "mc_expected"]:
            w[k] += pen / 3
    elif data_confidence > 0.8:
        b = (data_confidence - 0.8) * 0.10
        w["domain_score"] += b; w["mc_expected"] -= b * 0.5; w["bbn_posterior"] -= b * 0.5

    for k in w: w[k] = max(0.01, w[k])
    t = sum(w.values())
    if t > 0: w = {k: v / t for k, v in w.items()}
    return w

# ══════════════════════════════════════════════════════════════════════════
# 6. rank_intelligence_products
# ══════════════════════════════════════════════════════════════════════════

def rank_intelligence_products(component_scores, agreement):
    """Rank products by reliability (closeness to ensemble consensus)."""
    valid = {k: v for k, v in (component_scores or {}).items() if v is not None}
    if not valid:
        return []
    consensus = _mean(list(valid.values()))
    o_std = _std(list(valid.values()))
    ranked = []
    for key, score in valid.items():
        dev = abs(score - consensus)
        name = _ALGO_NAMES.get(key, key)
        if o_std > 0:
            rel = max(0.1, min(1.0, 1.0 - (dev / max(o_std, 1.0)) * 0.25))
        else:
            rel = 0.9
        if agreement > 70 and dev < 10: rel = min(1.0, rel + 0.1)
        if dev < 5:
            rsn = f"Closely aligned with ensemble consensus ({consensus:.0f})"
        elif dev < 15:
            rsn = f"Moderate deviation ({dev:.1f} pts); acceptable range"
        elif score > consensus:
            rsn = f"More optimistic than consensus (+{dev:.1f} pts)"
        else:
            rsn = f"More pessimistic than consensus (-{dev:.1f} pts)"
        ranked.append({"product": name, "reliability": round(rel, 3), "reason": rsn})
    ranked.sort(key=lambda r: r["reliability"], reverse=True)
    return ranked
