"""
Decision Tree Engine for TerraScout AI.

Implements formal decision trees for land-use assessment across 8 scenarios:
residential, agriculture, commercial, conservation, tourism, energy,
emergency_shelter, and research_station.

Each tree walks through domain score thresholds and produces a GO / CAUTION /
NO_GO verdict with confidence, decision path, and improvement roadmap.

Pure Python -- only stdlib imports.
"""
import math
import logging

logger = logging.getLogger(__name__)

DOMAINS = [
    "habitability", "agriculture", "ecology", "hazard_safety",
    "water_resources", "infrastructure", "climate_comfort",
    "economic_potential", "air_environment", "geological_stability",
]


# -- Node constructors ------------------------------------------------------

def _b(nid, label, domain, threshold, t_branch, f_branch):
    """Branching node (condition uses >= by default)."""
    return {"id": nid, "label": label,
            "condition": f"{domain} >= {threshold}",
            "domain": domain, "op": ">=", "threshold": threshold,
            "true_branch": t_branch, "false_branch": f_branch}


def _t(nid, rec, verdict, conf, factors):
    """Terminal (leaf) node."""
    return {"id": nid, "recommendation": rec, "verdict": verdict,
            "confidence": conf, "key_factors": list(factors)}


def _or_b(nid, label, dom_a, th_a, dom_b, th_b, t_branch, f_branch):
    """Branching node with an OR condition across two domains."""
    return {"id": nid, "label": label,
            "condition": f"{dom_a} >= {th_a} OR {dom_b} >= {th_b}",
            "domain": dom_a, "domain_b": dom_b, "op": "OR",
            "threshold": th_a, "threshold_b": th_b,
            "true_branch": t_branch, "false_branch": f_branch}


# -- 1. build_decision_trees() ----------------------------------------------

def build_decision_trees():
    """Return a dict mapping scenario name to its decision tree."""
    trees = {}

    # A. RESIDENTIAL SUITABILITY
    trees["residential"] = {"name": "Residential Suitability", "root": "R1", "nodes": {
        "R1":  _b("R1", "Is hazard safety adequate?", "hazard_safety", 40, "R2", "RN1"),
        "R2":  _b("R2", "Are water resources sufficient?", "water_resources", 50, "R3", "RN2"),
        "R3":  _b("R3", "Is infrastructure adequate?", "infrastructure", 40, "R4", "RC1"),
        "R4":  _b("R4", "Is climate comfort acceptable?", "climate_comfort", 35, "RG1", "RC2"),
        "RG1": _t("RG1", "Suitable for residential development", "GO", 0.85,
                   ["hazard_safety", "water_resources", "infrastructure", "climate_comfort"]),
        "RC2": _t("RC2", "Climate challenges \u2014 consider seasonal use", "CAUTION", 0.60,
                   ["climate_comfort"]),
        "RC1": _t("RC1", "Limited infrastructure \u2014 pioneer settlement only", "CAUTION", 0.50,
                   ["infrastructure"]),
        "RN2": _t("RN2", "Insufficient water resources", "NO_GO", 0.90, ["water_resources"]),
        "RN1": _t("RN1", "Unacceptable hazard risk", "NO_GO", 0.95, ["hazard_safety"]),
    }}

    # B. AGRICULTURAL VIABILITY
    trees["agriculture"] = {"name": "Agricultural Viability", "root": "A1", "nodes": {
        "A1":  _b("A1", "Is water sufficient for irrigation?", "water_resources", 45, "A2", "AN1"),
        "A2":  _b("A2", "Is soil/terrain suitable?", "agriculture", 40, "A3", "AN2"),
        "A3":  _b("A3", "Is growing season adequate?", "climate_comfort", 30, "A4", "AC1"),
        "A4":  _b("A4", "Is hazard risk manageable?", "hazard_safety", 35, "AG1", "AC2"),
        "AG1": _t("AG1", "Viable for agricultural operations", "GO", 0.82,
                   ["water_resources", "agriculture", "climate_comfort", "hazard_safety"]),
        "AC2": _t("AC2", "Agricultural possible but hazard insurance required", "CAUTION", 0.55,
                   ["hazard_safety"]),
        "AC1": _t("AC1", "Limited growing season \u2014 greenhouse recommended", "CAUTION", 0.50,
                   ["climate_comfort"]),
        "AN2": _t("AN2", "Soil/terrain unsuitable for agriculture", "NO_GO", 0.88,
                   ["agriculture"]),
        "AN1": _t("AN1", "Insufficient water for irrigation", "NO_GO", 0.92,
                   ["water_resources"]),
    }}

    # C. COMMERCIAL DEVELOPMENT
    trees["commercial"] = {"name": "Commercial Development", "root": "C1", "nodes": {
        "C1":  _b("C1", "Is infrastructure sufficient?", "infrastructure", 50, "C2", "C5"),
        "C2":  _b("C2", "Is economic demand present?", "economic_potential", 45, "C3", "CC1"),
        "C3":  _b("C3", "Is hazard risk acceptable?", "hazard_safety", 40, "C4", "CC2"),
        "C4":  _b("C4", "Is habitability adequate for workforce?", "habitability", 40, "CG1", "CC3"),
        "C5":  _b("C5", "Is economic demand very high?", "economic_potential", 60, "CC4", "CN1"),
        "CG1": _t("CG1", "Strong commercial potential", "GO", 0.88,
                   ["infrastructure", "economic_potential", "hazard_safety", "habitability"]),
        "CC3": _t("CC3", "Commercial viable but workforce housing needed", "CAUTION", 0.60,
                   ["habitability"]),
        "CC2": _t("CC2", "High insurance costs \u2014 consider risk transfer", "CAUTION", 0.55,
                   ["hazard_safety"]),
        "CC1": _t("CC1", "Infrastructure present but economic demand weak", "CAUTION", 0.50,
                   ["economic_potential"]),
        "CC4": _t("CC4", "High demand but infrastructure investment needed", "CAUTION", 0.52,
                   ["infrastructure", "economic_potential"]),
        "CN1": _t("CN1", "Insufficient infrastructure and demand", "NO_GO", 0.90,
                   ["infrastructure", "economic_potential"]),
    }}

    # D. CONSERVATION AREA
    trees["conservation"] = {"name": "Conservation Area", "root": "D1", "nodes": {
        "D1":  _b("D1", "Is ecosystem quality high?", "ecology", 50, "D2", "D5"),
        "D2":  _b("D2", "Is hazard risk manageable?", "hazard_safety", 30, "D3", "DC1"),
        "D3":  _b("D3", "Is air quality acceptable?", "air_environment", 40, "D4", "DC2"),
        "D4":  _b("D4", "Are water resources adequate?", "water_resources", 40, "DG1", "DC3"),
        "D5":  _b("D5", "Is ecosystem partially viable?", "ecology", 30, "DC4", "DN1"),
        "DG1": _t("DG1", "Excellent conservation potential", "GO", 0.90,
                   ["ecology", "hazard_safety", "air_environment", "water_resources"]),
        "DC3": _t("DC3", "Conservation possible \u2014 water restoration needed", "CAUTION", 0.62,
                   ["water_resources"]),
        "DC2": _t("DC2", "Air quality concerns \u2014 monitor pollution sources", "CAUTION", 0.55,
                   ["air_environment"]),
        "DC1": _t("DC1", "Natural hazard area \u2014 consider managed retreat", "CAUTION", 0.48,
                   ["hazard_safety"]),
        "DC4": _t("DC4", "Degraded \u2014 restoration project viable", "CAUTION", 0.45,
                   ["ecology"]),
        "DN1": _t("DN1", "Severely degraded ecosystem", "NO_GO", 0.88, ["ecology"]),
    }}

    # E. TOURISM DESTINATION
    trees["tourism"] = {"name": "Tourism Destination", "root": "T1", "nodes": {
        "T1":  _b("T1", "Is climate comfortable for visitors?", "climate_comfort", 45, "T2", "TN1"),
        "T2":  _b("T2", "Is ecological appeal present?", "ecology", 40, "T3", "T5"),
        "T3":  _b("T3", "Is access infrastructure adequate?", "infrastructure", 35, "T4", "TC1"),
        "T4":  _b("T4", "Is hazard risk acceptable for visitors?", "hazard_safety", 40, "TG1", "TC2"),
        "T5":  _b("T5", "Is climate exceptionally attractive?", "climate_comfort", 60, "TC3", "TN2"),
        "TG1": _t("TG1", "Strong tourism destination potential", "GO", 0.87,
                   ["climate_comfort", "ecology", "infrastructure", "hazard_safety"]),
        "TC2": _t("TC2", "Tourism viable \u2014 adventure/extreme tourism niche", "CAUTION", 0.55,
                   ["hazard_safety"]),
        "TC1": _t("TC1", "Ecotourism potential \u2014 access improvements needed", "CAUTION", 0.52,
                   ["infrastructure"]),
        "TC3": _t("TC3", "Climate-focused tourism (resort potential)", "CAUTION", 0.58,
                   ["climate_comfort", "ecology"]),
        "TN2": _t("TN2", "Limited tourism appeal", "NO_GO", 0.85, ["ecology", "climate_comfort"]),
        "TN1": _t("TN1", "Climate unsuitable for tourism", "NO_GO", 0.90, ["climate_comfort"]),
    }}

    # F. ENERGY INFRASTRUCTURE
    trees["energy"] = {"name": "Energy Infrastructure", "root": "E1", "nodes": {
        "E1":  _b("E1", "Is geological foundation stable?", "geological_stability", 45, "E2", "EN1"),
        "E2":  _b("E2", "Is grid infrastructure present?", "infrastructure", 40, "E3", "E5"),
        "E3":  _b("E3", "Is hazard risk acceptable?", "hazard_safety", 35, "E4", "EC1"),
        "E4":  _b("E4", "Is climate manageable for operations?", "climate_comfort", 30, "EG1", "EC2"),
        "E5":  _b("E5", "Is economic demand sufficient to justify build?", "economic_potential", 50,
                   "EC3", "EN2"),
        "EG1": _t("EG1", "Suitable for energy infrastructure", "GO", 0.84,
                   ["geological_stability", "infrastructure", "hazard_safety", "climate_comfort"]),
        "EC2": _t("EC2", "Energy project viable \u2014 weather-hardened design needed", "CAUTION", 0.58,
                   ["climate_comfort"]),
        "EC1": _t("EC1", "Energy possible with enhanced safety measures", "CAUTION", 0.52,
                   ["hazard_safety"]),
        "EC3": _t("EC3", "Grid investment justified by economic demand", "CAUTION", 0.50,
                   ["infrastructure", "economic_potential"]),
        "EN2": _t("EN2", "Too remote for grid-connected energy", "NO_GO", 0.87,
                   ["infrastructure", "economic_potential"]),
        "EN1": _t("EN1", "Geological instability \u2014 site unsuitable", "NO_GO", 0.93,
                   ["geological_stability"]),
    }}

    # G. EMERGENCY SHELTER
    trees["emergency_shelter"] = {"name": "Emergency Shelter", "root": "S1", "nodes": {
        "S1":  _b("S1", "Is hazard risk at least minimal?", "hazard_safety", 25, "S2", "SN1"),
        "S2":  _b("S2", "Is water available on-site?", "water_resources", 35, "S3", "SC1"),
        "S3":  _b("S3", "Is the site habitable short-term?", "habitability", 30, "SG1", "SC2"),
        "SG1": _t("SG1", "Suitable for emergency shelter", "GO", 0.80,
                   ["hazard_safety", "water_resources", "habitability"]),
        "SC2": _t("SC2", "Emergency viable \u2014 environmental hardening needed", "CAUTION", 0.55,
                   ["habitability"]),
        "SC1": _t("SC1", "Water supply must be transported", "CAUTION", 0.50,
                   ["water_resources"]),
        "SN1": _t("SN1", "Active hazard zone \u2014 not safe for shelter", "NO_GO", 0.95,
                   ["hazard_safety"]),
    }}

    # H. RESEARCH STATION
    trees["research_station"] = {"name": "Research Station", "root": "X1", "nodes": {
        "X1":  _or_b("X1", "Does the site have research value (ecology or geology)?",
                      "ecology", 40, "geological_stability", 40, "X2", "XN1"),
        "X2":  _b("X2", "Is minimal water available?", "water_resources", 30, "X3", "XC1"),
        "X3":  _b("X3", "Is hazard risk manageable?", "hazard_safety", 30, "XG1", "XC2"),
        "XG1": _t("XG1", "Suitable for research station", "GO", 0.82,
                   ["ecology", "geological_stability", "water_resources", "hazard_safety"]),
        "XC2": _t("XC2", "Research possible with hazard protocols", "CAUTION", 0.55,
                   ["hazard_safety"]),
        "XC1": _t("XC1", "Research viable \u2014 water logistics needed", "CAUTION", 0.50,
                   ["water_resources"]),
        "XN1": _t("XN1", "Insufficient research value", "NO_GO", 0.88,
                   ["ecology", "geological_stability"]),
    }}

    return trees


# -- Condition evaluation ---------------------------------------------------

def _eval_condition(node, scores):
    """Evaluate a node's condition against actual scores.
    Returns (bool, list_of_threshold_dicts).
    """
    checked = []
    if node.get("op") == "OR":
        da, db = node["domain"], node["domain_b"]
        ta, tb = node["threshold"], node["threshold_b"]
        va, vb = scores.get(da, 0), scores.get(db, 0)
        ma, mb = va >= ta, vb >= tb
        checked.append({"domain": da, "threshold": ta, "actual": va, "met": ma})
        checked.append({"domain": db, "threshold": tb, "actual": vb, "met": mb})
        return (ma or mb), checked

    domain, threshold = node["domain"], node["threshold"]
    actual = scores.get(domain, 0)
    op = node["op"]
    if op == ">=":
        met = actual >= threshold
    elif op == ">":
        met = actual > threshold
    elif op == "<=":
        met = actual <= threshold
    elif op == "<":
        met = actual < threshold
    elif op == "==":
        met = math.isclose(actual, threshold, abs_tol=0.01)
    else:
        logger.warning("Unknown operator '%s' in node %s", op, node.get("id"))
        met = actual >= threshold
    checked.append({"domain": domain, "threshold": threshold, "actual": actual, "met": met})
    return met, checked


# -- 2. evaluate_decision_tree() --------------------------------------------

def evaluate_decision_tree(tree_name, scores):
    """Walk a named decision tree with actual domain scores.

    Parameters
    ----------
    tree_name : str  -- one of the 8 scenario keys.
    scores : dict    -- domain name -> float score (0-100).

    Returns dict with: scenario, verdict, recommendation, confidence,
        path, key_factors, critical_thresholds.
    """
    trees = build_decision_trees()
    if tree_name not in trees:
        return {"scenario": tree_name, "verdict": "NO_GO",
                "recommendation": f"Unknown scenario: {tree_name}",
                "confidence": 0.0, "path": [], "key_factors": [],
                "critical_thresholds": []}

    tree = trees[tree_name]
    nodes, current_id = tree["nodes"], tree["root"]
    path, all_thresh = [], []

    for _ in range(20):  # depth safety limit
        node = nodes.get(current_id)
        if node is None:
            logger.error("Node '%s' not found in tree '%s'", current_id, tree_name)
            break
        # Terminal?
        if "recommendation" in node:
            return {"scenario": tree["name"], "verdict": node["verdict"],
                    "recommendation": node["recommendation"],
                    "confidence": node["confidence"], "path": path,
                    "key_factors": node["key_factors"],
                    "critical_thresholds": all_thresh}
        # Branch -- evaluate
        result, thresh = _eval_condition(node, scores)
        all_thresh.extend(thresh)
        if node.get("op") == "OR":
            dv = max(scores.get(node["domain"], 0),
                     scores.get(node.get("domain_b", ""), 0))
        else:
            dv = scores.get(node["domain"], 0)
        path.append({"node": node["id"], "question": node["label"],
                     "answer": result, "value": round(dv, 2)})
        current_id = node["true_branch"] if result else node["false_branch"]

    logger.error("Max depth reached walking tree '%s'", tree_name)
    return {"scenario": tree.get("name", tree_name), "verdict": "NO_GO",
            "recommendation": "Decision tree evaluation exceeded maximum depth",
            "confidence": 0.0, "path": path, "key_factors": [],
            "critical_thresholds": all_thresh}


# -- 3. evaluate_all_scenarios() --------------------------------------------

def evaluate_all_scenarios(scores):
    """Run all 8 decision trees and return aggregated results.

    Returns dict with: results, go_scenarios, caution_scenarios,
        no_go_scenarios, best_use, summary.
    """
    trees = build_decision_trees()
    results, go_list, caution_list, no_go_list = {}, [], [], []

    for key in trees:
        ev = evaluate_decision_tree(key, scores)
        results[key] = ev
        {"GO": go_list, "CAUTION": caution_list}.get(ev["verdict"], no_go_list).append(key)

    # Best use = highest-confidence GO scenario
    best_use = max(go_list, key=lambda k: results[k]["confidence"]) if go_list else None
    summary = _build_summary(go_list, caution_list, no_go_list, best_use, results)

    return {"results": results, "go_scenarios": go_list,
            "caution_scenarios": caution_list, "no_go_scenarios": no_go_list,
            "best_use": best_use, "summary": summary}


def _build_summary(go_list, caution_list, no_go_list, best_use, results):
    """Generate a 2-3 sentence human-readable summary."""
    parts = []
    if go_list:
        names = [results[k]["scenario"] for k in go_list]
        if len(names) == 1:
            parts.append(f"This location is well-suited for {names[0]}.")
        else:
            parts.append(f"This location shows strong potential for "
                         f"{', '.join(names[:-1])} and {names[-1]}.")
    else:
        parts.append("No scenarios received an unqualified GO verdict.")

    if caution_list:
        cn = [results[k]["scenario"] for k in caution_list]
        label = ", ".join(cn) if len(cn) <= 3 else f"{len(cn)} scenarios"
        parts.append(f"{label} may be viable with targeted improvements or risk mitigation.")

    if no_go_list and not go_list:
        blockers = {}
        for k in no_go_list:
            for f in results[k].get("key_factors", []):
                blockers[f] = blockers.get(f, 0) + 1
        if blockers:
            top = max(blockers, key=blockers.get)
            parts.append(f"The primary limiting factor is {top.replace('_', ' ')}.")

    if best_use:
        parts.append(f"Recommended primary use: {results[best_use]['scenario']} "
                     f"(confidence {results[best_use]['confidence']:.0%}).")
    return " ".join(parts)


# -- 4. compute_threshold_gaps() --------------------------------------------

def compute_threshold_gaps(scores):
    """For each scenario find unmet thresholds and compute gaps.

    Returns list of dicts sorted by smallest gap (easiest improvements first).
    Keys: scenario, domain, threshold, actual, gap, improvement_needed.
    """
    trees = build_decision_trees()
    gaps = []

    for skey, tree in trees.items():
        for node in tree["nodes"].values():
            if "recommendation" in node:
                continue  # skip terminals

            if node.get("op") == "OR":
                da, db = node["domain"], node.get("domain_b", "")
                ta, tb = node["threshold"], node.get("threshold_b", 0)
                va, vb = scores.get(da, 0), scores.get(db, 0)
                if va >= ta or vb >= tb:
                    continue  # OR satisfied
                ga, gb = ta - va, tb - vb
                if ga <= gb:
                    dom, thresh, actual, gap = da, ta, va, ga
                else:
                    dom, thresh, actual, gap = db, tb, vb, gb
                gaps.append({"scenario": skey, "domain": dom, "threshold": thresh,
                             "actual": round(actual, 2), "gap": round(gap, 2),
                             "improvement_needed":
                                 f"Increase {dom.replace('_', ' ')} by {gap:.1f} points "
                                 f"(from {actual:.1f} to {thresh})"})
            else:
                domain, threshold = node["domain"], node["threshold"]
                actual = scores.get(domain, 0)
                if actual < threshold:
                    gap = threshold - actual
                    gaps.append({"scenario": skey, "domain": domain,
                                 "threshold": threshold, "actual": round(actual, 2),
                                 "gap": round(gap, 2),
                                 "improvement_needed":
                                     f"Increase {domain.replace('_', ' ')} by {gap:.1f} "
                                     f"points (from {actual:.1f} to {threshold})"})

    gaps.sort(key=lambda g: g["gap"])
    return gaps


# -- 5. generate_improvement_roadmap() --------------------------------------

_DOMAIN_ADVICE = {
    "hazard_safety":
        "Implement hazard mitigation measures such as early-warning systems, "
        "structural reinforcement, and emergency preparedness planning.",
    "water_resources":
        "Develop water supply infrastructure including wells, rainwater "
        "harvesting, or pipeline connections to municipal sources.",
    "infrastructure":
        "Invest in road access, power grid connections, telecommunications, "
        "and essential service facilities.",
    "climate_comfort":
        "Address climate challenges through building design adaptation, "
        "HVAC systems, or seasonal operational planning.",
    "agriculture":
        "Improve soil quality through amendment programs, implement "
        "terracing or drainage, and establish irrigation systems.",
    "ecology":
        "Launch habitat restoration projects, establish wildlife corridors, "
        "and implement biodiversity monitoring programs.",
    "habitability":
        "Improve living conditions through shelter construction, sanitation "
        "infrastructure, and community service development.",
    "economic_potential":
        "Stimulate economic activity through market access improvements, "
        "business incentive programs, and workforce development.",
    "air_environment":
        "Reduce pollution sources, establish buffer zones from industrial "
        "areas, and implement air quality monitoring stations.",
    "geological_stability":
        "Conduct detailed geotechnical surveys, implement foundation "
        "engineering, and avoid construction on unstable formations.",
}


def generate_improvement_roadmap(all_results, scores):
    """Generate a prioritized improvement plan based on threshold gaps.

    Parameters
    ----------
    all_results : dict -- output of evaluate_all_scenarios().
    scores : dict      -- current domain scores.

    Returns list of dicts with: priority, domain, current_score, target_score,
        unlocks, effort, recommendation.
    """
    gaps = compute_threshold_gaps(scores)
    if not gaps:
        return []

    # Group gaps by domain
    domain_gaps = {}
    for g in gaps:
        d = g["domain"]
        if d not in domain_gaps:
            domain_gaps[d] = {"max_threshold": g["threshold"], "scenarios": []}
        entry = domain_gaps[d]
        if g["threshold"] > entry["max_threshold"]:
            entry["max_threshold"] = g["threshold"]
        if g["scenario"] not in entry["scenarios"]:
            entry["scenarios"].append(g["scenario"])

    blocked = set(all_results.get("caution_scenarios", [])
                  + all_results.get("no_go_scenarios", []))
    roadmap = []

    for domain, info in domain_gaps.items():
        current = scores.get(domain, 0)
        target = info["max_threshold"]
        gap = target - current
        if gap <= 0:
            continue

        effort = "LOW" if gap < 5 else ("MEDIUM" if gap < 15 else "HIGH")
        unlocks = [s for s in info["scenarios"] if s in blocked]

        dl = domain.replace("_", " ").title()
        severity = {"LOW": "minor", "MEDIUM": "moderate", "HIGH": "significant"}[effort]
        prefix = (f"{dl} needs a {severity} improvement of {gap:.1f} points "
                  f"(from {current:.1f} to {target}).")
        advice = _DOMAIN_ADVICE.get(domain, f"Improve {dl} score.")

        roadmap.append({"priority": 0, "domain": domain,
                        "current_score": round(current, 2),
                        "target_score": target, "unlocks": unlocks,
                        "effort": effort, "recommendation": f"{prefix} {advice}"})

    roadmap.sort(key=lambda r: (-len(r["unlocks"]), r["target_score"] - r["current_score"]))
    for i, item in enumerate(roadmap, 1):
        item["priority"] = i
    return roadmap


# -- Convenience: quick site verdict ----------------------------------------

def quick_site_verdict(scores):
    """Return a one-line verdict string for a location based on all scenarios."""
    result = evaluate_all_scenarios(scores)
    n_go = len(result["go_scenarios"])
    n_cau = len(result["caution_scenarios"])
    n_no = len(result["no_go_scenarios"])
    best = result.get("best_use")

    if n_go == 0 and n_cau == 0:
        return "UNSUITABLE: No viable land-use scenarios identified."
    if n_go == 0:
        return f"LIMITED: {n_cau} scenario(s) viable with mitigation; none fully clear."
    if best:
        name = result["results"][best]["scenario"]
        conf = result["results"][best]["confidence"]
        return (f"VIABLE: {n_go} GO, {n_cau} CAUTION, {n_no} NO_GO. "
                f"Best use: {name} ({conf:.0%} confidence).")
    return f"VIABLE: {n_go} GO, {n_cau} CAUTION, {n_no} NO_GO."


# -- Self-test ---------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample = {
        "habitability": 55, "agriculture": 48, "ecology": 62,
        "hazard_safety": 45, "water_resources": 52, "infrastructure": 44,
        "climate_comfort": 50, "economic_potential": 38,
        "air_environment": 58, "geological_stability": 60,
    }

    print("=" * 70)
    print("TerraScout Decision Tree Engine \u2014 Self-Test")
    print("=" * 70)
    print(f"\nInput scores: {sample}\n")

    res = evaluate_all_scenarios(sample)
    for key, ev in res["results"].items():
        print(f"  {ev['scenario']:30s}  [{ev['verdict']:7s}]  "
              f"conf={ev['confidence']:.0%}  \u2014 {ev['recommendation']}")

    print(f"\n  GO:      {res['go_scenarios']}")
    print(f"  CAUTION: {res['caution_scenarios']}")
    print(f"  NO_GO:   {res['no_go_scenarios']}")
    print(f"  Best:    {res['best_use']}")
    print(f"\n  {res['summary']}")

    print("\n" + "-" * 70 + "\nThreshold Gaps (top 5):\n" + "-" * 70)
    for g in compute_threshold_gaps(sample)[:5]:
        print(f"  {g['scenario']:20s}  {g['domain']:25s}  "
              f"need {g['threshold']}, have {g['actual']}, gap={g['gap']}")

    print("\n" + "-" * 70 + "\nImprovement Roadmap:\n" + "-" * 70)
    for item in generate_improvement_roadmap(res, sample):
        print(f"  #{item['priority']}  [{item['effort']:6s}]  {item['domain']:25s}  "
              f"{item['current_score']} -> {item['target_score']}  unlocks={item['unlocks']}")
        print(f"         {item['recommendation'][:90]}...")

    print(f"\nQuick verdict: {quick_site_verdict(sample)}")
    print("=" * 70)
