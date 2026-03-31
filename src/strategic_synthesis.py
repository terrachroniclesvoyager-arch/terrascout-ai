"""
Strategic Synthesis Engine — The Intelligence Brain of TerraScout AI.

This is the CORE intelligence module that interpolates ALL subsystems
(11 fusion algorithms, 13+ data sources, 10 domain scores) and produces:
1. Strategic Assessment Matrix — multi-dimensional site evaluation
2. Decision Priority Queue — ranked actionable recommendations
3. Narrative Intelligence Brief — human-readable conclusions
4. Composite Decision Score — single weighted confidence metric
5. Opportunity-Risk Matrix — quadrant classification
6. Multi-Horizon Outlook — short/medium/long term projections

This module does NOT just aggregate data — it INTERPRETS it and tells
people WHAT TO DO, like a real intelligence analyst would.
"""

import math
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# STRATEGIC ASSESSMENT MATRIX
# ═══════════════════════════════════════════════════════════════════════════

def compute_strategic_assessment(scores, details, analytics, ds_fusion,
                                  cascade, cvi, anomalies, trends,
                                  topsis, bbn, raw_data):
    """Master strategic assessment combining ALL subsystems.

    Returns a comprehensive assessment dict with:
    - strategic_score: single 0-100 composite
    - strategic_grade: A+ to F letter grade
    - dimensions: {livability, productivity, resilience, sustainability, connectivity}
    - decision_priority_queue: ranked actions
    - narrative: list of intelligence paragraphs
    - opportunity_risk_quadrant: classification
    - multi_horizon: {short_term, medium_term, long_term}
    - key_insights: top 5 interpolated insights
    - confidence_level: overall confidence
    """
    if not scores:
        return _empty_assessment()

    # ─── STEP 1: Compute 5 Strategic Dimensions ───
    dims = _compute_strategic_dimensions(scores, details, analytics, cvi, cascade)

    # ─── STEP 2: Composite Strategic Score (weighted geometric mean) ───
    dim_weights = {
        "livability": 0.25,
        "productivity": 0.20,
        "resilience": 0.25,
        "sustainability": 0.15,
        "connectivity": 0.15,
    }
    weighted_product = 1.0
    total_w = 0
    for dim, weight in dim_weights.items():
        val = max(dims[dim]["score"], 1)  # avoid zero in geometric mean
        weighted_product *= val ** weight
        total_w += weight

    strategic_score = min(100, max(0, weighted_product))
    strategic_grade = _letter_grade(strategic_score)

    # ─── STEP 3: Decision Priority Queue ───
    dpq = _build_decision_priority_queue(
        scores, dims, anomalies, cascade, cvi, topsis, bbn, details
    )

    # ─── STEP 4: Narrative Intelligence Brief ───
    narrative = _generate_narrative(
        strategic_score, strategic_grade, dims, scores, anomalies,
        cascade, cvi, trends, details, ds_fusion, raw_data
    )

    # ─── STEP 5: Opportunity-Risk Matrix ───
    or_quadrant = _classify_opportunity_risk(scores, dims, cascade, cvi)

    # ─── STEP 6: Multi-Horizon Outlook ───
    horizons = _multi_horizon_outlook(scores, dims, trends, cascade, anomalies)

    # ─── STEP 7: Key Interpolated Insights ───
    insights = _generate_key_insights(
        scores, dims, analytics, ds_fusion, cascade, cvi, bbn, details, raw_data
    )

    # ─── STEP 8: Confidence ───
    belief = ds_fusion.get("fused_belief", 0.5) if ds_fusion else 0.5
    data_conf = raw_data.get("confidence", 0.5) if isinstance(raw_data, dict) else 0.5
    confidence = (belief * 0.6 + data_conf * 0.4)

    return {
        "strategic_score": round(strategic_score, 1),
        "strategic_grade": strategic_grade,
        "dimensions": dims,
        "decision_priority_queue": dpq,
        "narrative": narrative,
        "opportunity_risk_quadrant": or_quadrant,
        "multi_horizon": horizons,
        "key_insights": insights,
        "confidence_level": round(confidence, 3),
        "timestamp": datetime.now().isoformat(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# 5 STRATEGIC DIMENSIONS
# ═══════════════════════════════════════════════════════════════════════════

def _compute_strategic_dimensions(scores, details, analytics, cvi, cascade):
    """Compute 5 high-level strategic dimensions from domain scores."""

    # LIVABILITY: Can people live here comfortably?
    liv_score = (
        scores.get("habitability", 50) * 0.35 +
        scores.get("climate_comfort", 50) * 0.25 +
        scores.get("air_environment", 50) * 0.20 +
        scores.get("water_resources", 50) * 0.20
    )
    liv_factors = []
    if scores.get("habitability", 0) >= 60:
        liv_factors.append("Adequate housing potential")
    if scores.get("climate_comfort", 0) >= 60:
        liv_factors.append("Comfortable climate")
    if scores.get("air_environment", 0) < 40:
        liv_factors.append("Poor air quality is a concern")
    if scores.get("water_resources", 0) < 40:
        liv_factors.append("Water scarcity risk")

    # PRODUCTIVITY: Can this area generate economic value?
    prod_score = (
        scores.get("agriculture", 50) * 0.30 +
        scores.get("economic_potential", 50) * 0.35 +
        scores.get("infrastructure", 50) * 0.25 +
        scores.get("water_resources", 50) * 0.10
    )
    prod_factors = []
    if scores.get("agriculture", 0) >= 60:
        prod_factors.append("Good agricultural potential")
    if scores.get("economic_potential", 0) >= 60:
        prod_factors.append("Strong economic indicators")
    if scores.get("infrastructure", 0) < 40:
        prod_factors.append("Infrastructure deficit limits growth")

    # RESILIENCE: Can this area withstand shocks?
    sys_risk = cascade.get("systemic_score", 50) if cascade else 50
    cvi_score_val = cvi.get("cvi_score", 0.5) if cvi else 0.5
    res_score = (
        scores.get("hazard_safety", 50) * 0.30 +
        scores.get("geological_stability", 50) * 0.25 +
        (100 - sys_risk) * 0.25 +
        (1 - cvi_score_val) * 100 * 0.20
    )
    res_factors = []
    if scores.get("hazard_safety", 0) < 40:
        res_factors.append("High natural hazard exposure")
    if sys_risk > 50:
        res_factors.append("Systemic cascade risk is elevated")
    if cvi_score_val > 0.5:
        res_factors.append("Vulnerability exceeds tolerance threshold")
    if scores.get("geological_stability", 0) >= 70:
        res_factors.append("Stable geological foundation")

    # SUSTAINABILITY: Can this be maintained long-term?
    sus_score = (
        scores.get("ecology", 50) * 0.30 +
        scores.get("water_resources", 50) * 0.25 +
        scores.get("air_environment", 50) * 0.20 +
        scores.get("agriculture", 50) * 0.15 +
        scores.get("climate_comfort", 50) * 0.10
    )
    sus_factors = []
    if scores.get("ecology", 0) >= 60:
        sus_factors.append("Healthy ecosystem supports long-term use")
    if scores.get("water_resources", 0) >= 60:
        sus_factors.append("Sustainable water availability")
    if scores.get("ecology", 0) < 30:
        sus_factors.append("Ecosystem degradation threatens sustainability")

    # CONNECTIVITY: Infrastructure and access
    pop = details.get("population_density", 0)
    infra = scores.get("infrastructure", 50)
    conn_score = infra * 0.60 + scores.get("economic_potential", 50) * 0.25
    if pop > 100:
        conn_score += min(15, math.log10(pop) * 5)
    conn_score = min(100, conn_score)
    conn_factors = []
    if infra >= 60:
        conn_factors.append("Well-connected infrastructure")
    if pop > 500:
        conn_factors.append(f"Population density: {pop:.0f}/km²")
    if infra < 30:
        conn_factors.append("Remote location with limited access")

    return {
        "livability": {"score": round(liv_score, 1), "factors": liv_factors},
        "productivity": {"score": round(prod_score, 1), "factors": prod_factors},
        "resilience": {"score": round(res_score, 1), "factors": res_factors},
        "sustainability": {"score": round(sus_score, 1), "factors": sus_factors},
        "connectivity": {"score": round(conn_score, 1), "factors": conn_factors},
    }


# ═══════════════════════════════════════════════════════════════════════════
# DECISION PRIORITY QUEUE
# ═══════════════════════════════════════════════════════════════════════════

def _build_decision_priority_queue(scores, dims, anomalies, cascade, cvi,
                                     topsis, bbn, details):
    """Generate ranked list of actionable decisions with urgency & impact."""
    actions = []

    # Immediate threats
    if cascade and cascade.get("systemic_score", 0) > 60:
        chain = cascade.get("most_vulnerable_chain", [])
        chain_str = " -> ".join(chain[:3]) if chain else "multiple domains"
        actions.append({
            "priority": 1,
            "urgency": "IMMEDIATE",
            "action": f"Mitigate systemic cascade risk through {chain_str}",
            "impact": "HIGH",
            "category": "risk_mitigation",
            "rationale": f"Systemic risk score {cascade['systemic_score']:.0f}/100 "
                         "threatens all downstream domains",
        })

    # Critical anomalies
    critical_anomalies = [a for a in (anomalies or []) if a.get("severity") == "CRITICAL"]
    for a in critical_anomalies[:2]:
        actions.append({
            "priority": 2,
            "urgency": "IMMEDIATE",
            "action": a.get("action", f"Investigate {a.get('metric', 'anomaly')}"),
            "impact": "HIGH",
            "category": "anomaly_response",
            "rationale": f"{a.get('metric', '')} is {a.get('abs_z', 0):.1f} std devs "
                         f"from baseline",
        })

    # Vulnerability reduction
    if cvi and cvi.get("vulnerability_class") in ("HIGH", "EXTREME"):
        wl = cvi.get("weakest_link", "unknown").replace("_", " ").title()
        actions.append({
            "priority": 3,
            "urgency": "SHORT-TERM",
            "action": f"Strengthen {wl} to reduce vulnerability from "
                      f"{cvi['vulnerability_class']}",
            "impact": "HIGH",
            "category": "capacity_building",
            "rationale": f"CVI = {cvi.get('cvi_score', 0):.3f}, "
                         f"weakest dimension: {wl}",
        })

    # Low-scoring domains
    weak_domains = sorted(
        [(d, s) for d, s in scores.items() if s < 40],
        key=lambda x: x[1]
    )
    for d, s in weak_domains[:3]:
        from src.unified_intelligence import INTELLIGENCE_DOMAINS
        dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
        actions.append({
            "priority": 4,
            "urgency": "MEDIUM-TERM",
            "action": f"Improve {dname} (currently {s:.0f}/100)",
            "impact": "MEDIUM",
            "category": "domain_improvement",
            "rationale": f"Score below 40 indicates significant deficiency",
        })

    # BBN-informed: highest-influence interventions
    if bbn and bbn.get("node_importance"):
        top_nodes = sorted(bbn["node_importance"].items(),
                          key=lambda x: x[1], reverse=True)
        for d, imp in top_nodes[:2]:
            if scores.get(d, 100) < 60:
                from src.unified_intelligence import INTELLIGENCE_DOMAINS
                dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
                actions.append({
                    "priority": 5,
                    "urgency": "MEDIUM-TERM",
                    "action": f"Invest in {dname} — highest network influence "
                              f"(importance: {imp:.2f})",
                    "impact": "HIGH",
                    "category": "strategic_investment",
                    "rationale": "BBN analysis shows this domain has the highest "
                                 "causal influence on other domains",
                })

    # Opportunity exploitation
    strong_domains = sorted(
        [(d, s) for d, s in scores.items() if s >= 70],
        key=lambda x: x[1], reverse=True
    )
    for d, s in strong_domains[:2]:
        from src.unified_intelligence import INTELLIGENCE_DOMAINS
        dname = INTELLIGENCE_DOMAINS.get(d, {}).get("name", d)
        actions.append({
            "priority": 6,
            "urgency": "LONG-TERM",
            "action": f"Capitalize on strong {dname} ({s:.0f}/100)",
            "impact": "MEDIUM",
            "category": "opportunity",
            "rationale": f"Score above 70 indicates competitive advantage",
        })

    # Best scenario recommendation
    if topsis:
        from src.decision_matrix import DECISION_SCENARIOS, VERDICT_GO
        best = topsis[0]
        sc = DECISION_SCENARIOS.get(best.get("scenario", ""), {})
        if best.get("overall", 0) >= VERDICT_GO:
            actions.append({
                "priority": 3,
                "urgency": "SHORT-TERM",
                "action": f"Pursue {sc.get('name', 'top scenario')} — "
                          f"highest TOPSIS ranking (C*={best.get('closeness', 0):.3f})",
                "impact": "HIGH",
                "category": "strategic_direction",
                "rationale": "Multi-criteria analysis confirms viability",
            })

    # Active disasters
    active_disasters = details.get("active_disasters", 0)
    if active_disasters > 0:
        actions.insert(0, {
            "priority": 0,
            "urgency": "IMMEDIATE",
            "action": f"Monitor {active_disasters} active disaster(s) in area — "
                      "activate contingency plans",
            "impact": "CRITICAL",
            "category": "emergency",
            "rationale": "GDACS reports active events within operational radius",
        })

    # Sort by priority
    actions.sort(key=lambda x: x["priority"])
    return actions[:10]


# ═══════════════════════════════════════════════════════════════════════════
# NARRATIVE INTELLIGENCE BRIEF
# ═══════════════════════════════════════════════════════════════════════════

def _generate_narrative(strategic_score, grade, dims, scores, anomalies,
                         cascade, cvi, trends, details, ds_fusion, raw_data):
    """Generate human-readable intelligence paragraphs."""
    paragraphs = []
    belief = ds_fusion.get("fused_belief", 0.5) * 100 if ds_fusion else 50

    # Opening assessment
    if strategic_score >= 70:
        tone = "highly favorable"
        outlook = "Strong fundamentals support multiple development scenarios."
    elif strategic_score >= 50:
        tone = "moderately favorable with identified gaps"
        outlook = "Selective development is viable with targeted investments."
    elif strategic_score >= 30:
        tone = "challenging with significant risk factors"
        outlook = "Proceed with caution; substantial mitigation required."
    else:
        tone = "unfavorable for most operational scenarios"
        outlook = "Alternative locations should be evaluated."

    paragraphs.append(
        f"STRATEGIC ASSESSMENT: This location rates {strategic_score:.0f}/100 "
        f"(Grade {grade}), classified as {tone}. Multi-source evidence fusion "
        f"confirms {belief:.0f}% confidence across {len(scores)} analytical domains. "
        f"{outlook}"
    )

    # Dimension analysis
    dim_summary = []
    for name, data in sorted(dims.items(), key=lambda x: x[1]["score"], reverse=True):
        s = data["score"]
        label = name.replace("_", " ").title()
        if s >= 65:
            dim_summary.append(f"{label} ({s:.0f}) is a strength")
        elif s < 40:
            dim_summary.append(f"{label} ({s:.0f}) requires attention")

    if dim_summary:
        paragraphs.append(
            "DIMENSIONAL PROFILE: " + ". ".join(dim_summary) + "."
        )

    # Risk narrative
    sys_risk = cascade.get("systemic_score", 0) if cascade else 0
    vuln_class = cvi.get("vulnerability_class", "N/A") if cvi else "N/A"
    n_critical = len([a for a in (anomalies or []) if a.get("severity") == "CRITICAL"])

    risk_parts = []
    if sys_risk > 50:
        risk_parts.append(f"systemic cascade risk is elevated at {sys_risk:.0f}/100")
    if vuln_class in ("HIGH", "EXTREME"):
        risk_parts.append(f"vulnerability is {vuln_class}")
    if n_critical > 0:
        risk_parts.append(f"{n_critical} critical anomalies detected")

    active_disasters = details.get("active_disasters", 0)
    if active_disasters > 0:
        risk_parts.append(f"{active_disasters} active disaster event(s) in area")

    if risk_parts:
        paragraphs.append(
            "RISK ASSESSMENT: " + "; ".join(risk_parts).capitalize() +
            ". Recommend enhanced monitoring and contingency planning."
        )
    else:
        paragraphs.append(
            "RISK ASSESSMENT: No critical risks identified. Standard monitoring adequate."
        )

    # Trend outlook
    composite_trend = trends.get("composite_trend", "STABLE") if trends else "STABLE"
    paragraphs.append(
        f"TEMPORAL OUTLOOK: Composite trend is {composite_trend}. "
        f"Environmental conditions are "
        f"{'expected to improve' if composite_trend == 'IMPROVING' else 'expected to remain stable' if composite_trend == 'STABLE' else 'showing degradation signals'}."
    )

    # Population context
    pop = details.get("population_density", 0)
    if pop > 0:
        if pop > 5000:
            pop_ctx = f"Dense urban environment ({pop:.0f}/km²) with established infrastructure"
        elif pop > 500:
            pop_ctx = f"Moderately populated area ({pop:.0f}/km²) with developing infrastructure"
        elif pop > 50:
            pop_ctx = f"Rural area ({pop:.0f}/km²) with basic infrastructure"
        else:
            pop_ctx = f"Sparsely populated area ({pop:.0f}/km²) — remote operations likely"
        paragraphs.append(f"OPERATIONAL CONTEXT: {pop_ctx}.")

    return paragraphs


# ═══════════════════════════════════════════════════════════════════════════
# OPPORTUNITY-RISK MATRIX
# ═══════════════════════════════════════════════════════════════════════════

def _classify_opportunity_risk(scores, dims, cascade, cvi):
    """Classify location into opportunity-risk quadrant.

    Returns:
        {quadrant, opportunity_score, risk_score, recommendation}
    """
    # Opportunity = average of productivity + sustainability + connectivity
    opp = (dims["productivity"]["score"] +
           dims["sustainability"]["score"] +
           dims["connectivity"]["score"]) / 3

    # Risk = inverse of resilience + systemic risk + vulnerability
    sys_risk = cascade.get("systemic_score", 50) if cascade else 50
    cvi_val = cvi.get("cvi_score", 0.5) if cvi else 0.5
    risk = (sys_risk * 0.4 + cvi_val * 100 * 0.3 +
            (100 - dims["resilience"]["score"]) * 0.3)

    if opp >= 55 and risk < 45:
        quadrant = "PRIME"
        recommendation = "Ideal location — pursue aggressively with full resource commitment"
    elif opp >= 55 and risk >= 45:
        quadrant = "HIGH-REWARD/HIGH-RISK"
        recommendation = "Strong opportunity but significant risks — proceed with robust mitigation"
    elif opp < 55 and risk < 45:
        quadrant = "STABLE/LIMITED"
        recommendation = "Low-risk but limited opportunity — suitable for conservative operations"
    else:
        quadrant = "AVOID"
        recommendation = "High risk with limited opportunity — seek alternative locations"

    return {
        "quadrant": quadrant,
        "opportunity_score": round(opp, 1),
        "risk_score": round(risk, 1),
        "recommendation": recommendation,
    }


# ═══════════════════════════════════════════════════════════════════════════
# MULTI-HORIZON OUTLOOK
# ═══════════════════════════════════════════════════════════════════════════

def _multi_horizon_outlook(scores, dims, trends, cascade, anomalies):
    """Project assessment across 3 time horizons."""
    composite = trends.get("composite_trend", "STABLE") if trends else "STABLE"
    sys_risk = cascade.get("systemic_score", 0) if cascade else 0
    n_critical = len([a for a in (anomalies or []) if a.get("severity") == "CRITICAL"])

    # Short-term (0-3 months): mostly about current conditions
    if n_critical > 0 or sys_risk > 60:
        short = {"outlook": "CAUTION", "confidence": 0.8,
                 "narrative": "Immediate attention needed for active threats and anomalies"}
    elif dims["livability"]["score"] >= 50 and dims["resilience"]["score"] >= 50:
        short = {"outlook": "FAVORABLE", "confidence": 0.75,
                 "narrative": "Current conditions support normal operations"}
    else:
        short = {"outlook": "MIXED", "confidence": 0.65,
                 "narrative": "Some operational limitations expected"}

    # Medium-term (3-12 months): trends + adaptation
    if composite == "IMPROVING":
        medium = {"outlook": "IMPROVING", "confidence": 0.6,
                  "narrative": "Trend analysis shows positive trajectory across multiple domains"}
    elif composite == "DEGRADING":
        medium = {"outlook": "DEGRADING", "confidence": 0.6,
                  "narrative": "Declining trend detected — plan for adaptation or relocation"}
    else:
        medium = {"outlook": "STABLE", "confidence": 0.55,
                  "narrative": "No significant changes projected — maintain current strategy"}

    # Long-term (1-5 years): sustainability + systemic factors
    sus = dims["sustainability"]["score"]
    if sus >= 65 and sys_risk < 40:
        long_term = {"outlook": "SUSTAINABLE", "confidence": 0.4,
                     "narrative": "Long-term viability confirmed by ecological and resource analysis"}
    elif sus < 35 or sys_risk > 60:
        long_term = {"outlook": "AT RISK", "confidence": 0.45,
                     "narrative": "Long-term sustainability concerns require strategic planning"}
    else:
        long_term = {"outlook": "UNCERTAIN", "confidence": 0.35,
                     "narrative": "Insufficient data for confident long-term projection"}

    return {
        "short_term": short,
        "medium_term": medium,
        "long_term": long_term,
    }


# ═══════════════════════════════════════════════════════════════════════════
# KEY INTERPOLATED INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════

def _generate_key_insights(scores, dims, analytics, ds_fusion, cascade,
                            cvi, bbn, details, raw_data):
    """Generate top 5 cross-system insights from interpolation of all data."""
    insights = []

    # Insight 1: Water-Agriculture-Economy nexus
    water = scores.get("water_resources", 50)
    agri = scores.get("agriculture", 50)
    econ = scores.get("economic_potential", 50)
    if water > 60 and agri > 60:
        insights.append({
            "title": "WATER-AGRICULTURE SYNERGY",
            "text": f"Strong water resources ({water:.0f}) combined with agricultural "
                    f"potential ({agri:.0f}) creates a robust food-economy nexus. "
                    f"Economic potential ({econ:.0f}) can be amplified through "
                    "agri-industrial development.",
            "confidence": 0.82,
            "type": "opportunity",
        })
    elif water < 35 and agri > 50:
        insights.append({
            "title": "WATER BOTTLENECK",
            "text": f"Agricultural potential ({agri:.0f}) is constrained by water "
                    f"scarcity ({water:.0f}). Irrigation infrastructure investment "
                    "could unlock significant economic value.",
            "confidence": 0.78,
            "type": "constraint",
        })

    # Insight 2: Hazard-Infrastructure interdependency
    hazard = scores.get("hazard_safety", 50)
    infra = scores.get("infrastructure", 50)
    if hazard < 40 and infra > 50:
        amp = cascade.get("amplification", {}).get("hazard_safety", 1) if cascade else 1
        insights.append({
            "title": "INFRASTRUCTURE AT RISK",
            "text": f"Existing infrastructure ({infra:.0f}) is exposed to natural "
                    f"hazards ({hazard:.0f}). Cascade amplification factor: {amp:.2f}x. "
                    "Hardening investments have high ROI.",
            "confidence": 0.85,
            "type": "risk",
        })

    # Insight 3: Climate-Ecology balance
    climate = scores.get("climate_comfort", 50)
    ecology = scores.get("ecology", 50)
    air = scores.get("air_environment", 50)
    if ecology > 65 and air > 60:
        insights.append({
            "title": "ECOLOGICAL ASSET",
            "text": f"Biodiversity ({ecology:.0f}) and air quality ({air:.0f}) indicate "
                    "a healthy ecosystem. This is a strategic asset for conservation, "
                    "eco-tourism, and carbon credit markets.",
            "confidence": 0.75,
            "type": "opportunity",
        })

    # Insight 4: Geological stability foundation
    geo = scores.get("geological_stability", 50)
    if geo > 70:
        insights.append({
            "title": "STABLE FOUNDATION",
            "text": f"Geological stability ({geo:.0f}) provides a strong foundation "
                    "for long-term infrastructure investment. Construction costs are "
                    "likely below regional average.",
            "confidence": 0.7,
            "type": "strength",
        })
    elif geo < 30:
        insights.append({
            "title": "SEISMIC/GEOLOGICAL CONCERN",
            "text": f"Geological instability ({geo:.0f}) represents a fundamental "
                    "risk that constrains all development scenarios. Specialized "
                    "engineering required.",
            "confidence": 0.8,
            "type": "risk",
        })

    # Insight 5: Population-Infrastructure gap
    pop = details.get("population_density", 0)
    if pop > 1000 and infra < 45:
        insights.append({
            "title": "INFRASTRUCTURE GAP",
            "text": f"High population density ({pop:.0f}/km²) with low "
                    f"infrastructure score ({infra:.0f}) indicates an underserved "
                    "area with significant investment opportunity.",
            "confidence": 0.72,
            "type": "opportunity",
        })
    elif pop < 50 and infra > 60:
        insights.append({
            "title": "INFRASTRUCTURE SURPLUS",
            "text": f"Low population ({pop:.0f}/km²) with good infrastructure "
                    f"({infra:.0f}) suggests capacity for growth or strategic "
                    "operational deployment.",
            "confidence": 0.65,
            "type": "opportunity",
        })

    # Insight from BBN
    if bbn and bbn.get("conditional_updates"):
        updates = bbn["conditional_updates"]
        max_shift = max(updates.items(), key=lambda x: abs(x[1]), default=None)
        if max_shift and abs(max_shift[1]) > 2:
            from src.unified_intelligence import INTELLIGENCE_DOMAINS
            dname = INTELLIGENCE_DOMAINS.get(max_shift[0], {}).get("name", max_shift[0])
            direction = "improved" if max_shift[1] > 0 else "degraded"
            insights.append({
                "title": "CAUSAL NETWORK SIGNAL",
                "text": f"Bayesian causal analysis shows {dname} has {direction} by "
                        f"{abs(max_shift[1]):.1f}% due to inter-domain influences. "
                        "This reveals hidden dependencies not visible in raw scores.",
                "confidence": 0.68,
                "type": "insight",
            })

    # Disaster context
    active_d = details.get("active_disasters", 0)
    if active_d > 0:
        events = details.get("gdacs_events", [])
        nearest = events[0] if events else {}
        insights.insert(0, {
            "title": "ACTIVE THREAT ENVIRONMENT",
            "text": f"{active_d} active disaster event(s) detected within operational "
                    f"radius. Nearest: {nearest.get('name', 'Unknown')} "
                    f"({nearest.get('distance_km', '?')} km, "
                    f"alert: {nearest.get('alert_level', '?')}). "
                    "Activate situation monitoring protocols.",
            "confidence": 0.95,
            "type": "threat",
        })

    return insights[:7]


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _letter_grade(score):
    """Convert 0-100 score to letter grade."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B+"
    elif score >= 60:
        return "B"
    elif score >= 50:
        return "C+"
    elif score >= 40:
        return "C"
    elif score >= 30:
        return "D"
    else:
        return "F"


def _empty_assessment():
    return {
        "strategic_score": 0,
        "strategic_grade": "N/A",
        "dimensions": {},
        "decision_priority_queue": [],
        "narrative": [],
        "opportunity_risk_quadrant": {},
        "multi_horizon": {},
        "key_insights": [],
        "confidence_level": 0,
        "timestamp": datetime.now().isoformat(),
    }
