"""
Next-Gen Algorithms — 4 game-changer analytical algorithms for TerraScout AI.

A. Fuzzy Logic Controller     — triangular MFs, 28 expert rules, centroid defuzz
B. Graph Centrality           — PageRank, betweenness, degree, eigenvector
C. DBSCAN Domain Clustering   — auto-tuned eps, Euclidean distance
D. Robust Anomaly Ensemble    — Z-score + IQR + Grubbs (2/3 vote)

Pure Python — no scipy/sklearn dependencies.
"""

import logging
import math
from collections import defaultdict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DOMAIN NAMES (canonical order)
# ---------------------------------------------------------------------------
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
# A. FUZZY LOGIC CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════

def _trimf(x, a, b, c):
    """Triangular membership function: rising from a to b, falling from b to c."""
    if x <= a or x >= c:
        return 0.0
    if a < x <= b:
        return (x - a) / (b - a) if b != a else 1.0
    return (c - x) / (c - b) if c != b else 1.0


def _fuzzify(value):
    """Fuzzify a 0-100 score into low/medium/high memberships."""
    return {
        "low": _trimf(value, 0, 0, 40),
        "medium": _trimf(value, 20, 50, 80),
        "high": _trimf(value, 60, 100, 100),
    }


def _defuzzify_centroid(memberships, universe_min=0, universe_max=100, steps=200):
    """Centroid defuzzification over the output universe.

    memberships: dict with keys low/medium/high and their activation levels.
    """
    dx = (universe_max - universe_min) / steps
    numerator = 0.0
    denominator = 0.0
    for i in range(steps + 1):
        x = universe_min + i * dx
        # Aggregate: max of clipped MFs
        mu_low = min(memberships.get("low", 0), _trimf(x, 0, 0, 40))
        mu_med = min(memberships.get("medium", 0), _trimf(x, 20, 50, 80))
        mu_high = min(memberships.get("high", 0), _trimf(x, 60, 100, 100))
        mu = max(mu_low, mu_med, mu_high)
        numerator += x * mu
        denominator += mu
    return numerator / denominator if denominator > 1e-9 else 50.0


# 28 expert inference rules
_FUZZY_RULES = [
    # (domain_a, level_a, domain_b, level_b, conclusion_key, conclusion_level)
    ("water_resources", "high", "agriculture", "medium", "irrigation_potential", "high"),
    ("water_resources", "high", "agriculture", "high", "irrigation_potential", "high"),
    ("water_resources", "low", "agriculture", "high", "drought_risk", "high"),
    ("water_resources", "low", "climate_comfort", "low", "arid_stress", "high"),
    ("hazard_safety", "low", "infrastructure", "low", "compound_risk", "high"),
    ("hazard_safety", "low", "geological_stability", "low", "critical_danger", "high"),
    ("hazard_safety", "high", "infrastructure", "high", "safe_development", "high"),
    ("ecology", "high", "air_environment", "high", "pristine_environment", "high"),
    ("ecology", "low", "air_environment", "low", "environmental_degradation", "high"),
    ("ecology", "high", "water_resources", "high", "ecosystem_health", "high"),
    ("economic_potential", "high", "infrastructure", "high", "development_ready", "high"),
    ("economic_potential", "high", "infrastructure", "low", "bottleneck_infra", "high"),
    ("economic_potential", "low", "infrastructure", "high", "underutilized_infra", "high"),
    ("climate_comfort", "high", "habitability", "high", "ideal_living", "high"),
    ("climate_comfort", "low", "habitability", "low", "harsh_conditions", "high"),
    ("climate_comfort", "medium", "habitability", "medium", "moderate_living", "medium"),
    ("geological_stability", "high", "infrastructure", "high", "build_confidence", "high"),
    ("geological_stability", "low", "infrastructure", "high", "seismic_risk_infra", "high"),
    ("habitability", "high", "economic_potential", "high", "investment_grade", "high"),
    ("habitability", "low", "hazard_safety", "low", "evacuation_priority", "high"),
    ("agriculture", "high", "ecology", "low", "monoculture_risk", "medium"),
    ("agriculture", "high", "ecology", "high", "sustainable_agri", "high"),
    ("air_environment", "low", "habitability", "medium", "health_risk", "high"),
    ("air_environment", "high", "climate_comfort", "high", "wellness_zone", "high"),
    ("water_resources", "medium", "agriculture", "medium", "balanced_use", "medium"),
    ("economic_potential", "medium", "habitability", "medium", "growth_potential", "medium"),
    ("hazard_safety", "medium", "geological_stability", "medium", "manageable_risk", "medium"),
    ("ecology", "medium", "water_resources", "medium", "stable_ecosystem", "medium"),
]


def fuzzy_logic_assessment(scores, details=None):
    """Run fuzzy logic assessment across all domains.

    Args:
        scores: dict domain->score (0-100)
        details: dict domain->detail_dict (optional, unused for now)

    Returns dict:
        fuzzy_domains: {domain: {low, medium, high}}
        fuzzy_overall: {value, linguistic, raw_memberships}
        fuzzy_interactions: list of fired rules with strengths
    """
    try:
        # Fuzzify all domains
        fuzzy_domains = {}
        for d in _DOMAINS:
            val = scores.get(d, 50)
            if not isinstance(val, (int, float)):
                val = 50
            fuzzy_domains[d] = _fuzzify(val)

        # Evaluate rules
        interactions = []
        output_memberships = {"low": 0.0, "medium": 0.0, "high": 0.0}
        for (da, la, db, lb, conclusion_key, conclusion_level) in _FUZZY_RULES:
            strength_a = fuzzy_domains.get(da, {}).get(la, 0)
            strength_b = fuzzy_domains.get(db, {}).get(lb, 0)
            firing_strength = min(strength_a, strength_b)  # AND = min
            if firing_strength > 0.05:
                interactions.append({
                    "rule": f"IF {_DOMAIN_LABELS.get(da, da)}={la} AND {_DOMAIN_LABELS.get(db, db)}={lb}",
                    "conclusion": conclusion_key.replace("_", " ").title(),
                    "level": conclusion_level,
                    "strength": round(firing_strength, 3),
                })
                output_memberships[conclusion_level] = max(
                    output_memberships[conclusion_level], firing_strength
                )

        interactions.sort(key=lambda r: r["strength"], reverse=True)

        # Defuzzify overall
        overall_value = _defuzzify_centroid(output_memberships)

        if overall_value >= 70:
            linguistic = "HIGHLY FAVORABLE"
        elif overall_value >= 55:
            linguistic = "FAVORABLE"
        elif overall_value >= 40:
            linguistic = "MODERATE"
        elif overall_value >= 25:
            linguistic = "UNFAVORABLE"
        else:
            linguistic = "CRITICAL"

        return {
            "fuzzy_domains": fuzzy_domains,
            "fuzzy_overall": {
                "value": round(overall_value, 1),
                "linguistic": linguistic,
                "raw_memberships": {k: round(v, 3) for k, v in output_memberships.items()},
            },
            "fuzzy_interactions": interactions[:20],
        }
    except Exception as exc:
        logger.warning("Fuzzy logic assessment failed: %s", exc)
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# B. GRAPH CENTRALITY & INFLUENCE NETWORK
# ═══════════════════════════════════════════════════════════════════════════

# Influence matrix: domain -> list of domains it influences
_INFLUENCE_MATRIX = {
    "water_resources": ["agriculture", "ecology", "habitability"],
    "climate_comfort": ["agriculture", "habitability", "ecology"],
    "hazard_safety": ["infrastructure", "habitability", "economic_potential"],
    "geological_stability": ["infrastructure", "hazard_safety", "economic_potential"],
    "infrastructure": ["economic_potential", "habitability"],
    "air_environment": ["habitability", "ecology", "climate_comfort"],
    "ecology": ["water_resources", "air_environment", "agriculture"],
    "agriculture": ["economic_potential", "ecology"],
    "economic_potential": ["infrastructure", "habitability"],
    "habitability": ["economic_potential"],
}


def _build_adjacency(scores):
    """Build weighted adjacency matrix from score correlations + influence matrix."""
    n = len(_DOMAINS)
    adj = [[0.0] * n for _ in range(n)]
    idx = {d: i for i, d in enumerate(_DOMAINS)}

    # Structural edges from influence matrix
    for src, targets in _INFLUENCE_MATRIX.items():
        si = idx.get(src)
        if si is None:
            continue
        for tgt in targets:
            ti = idx.get(tgt)
            if ti is None:
                continue
            src_score = scores.get(src, 50)
            tgt_score = scores.get(tgt, 50)
            if not isinstance(src_score, (int, float)):
                src_score = 50
            if not isinstance(tgt_score, (int, float)):
                tgt_score = 50
            # Weight based on scores + baseline structural weight
            weight = 0.3 + 0.7 * (src_score / 100)
            adj[si][ti] = max(adj[si][ti], weight)

    # Add weak correlation edges for similar scores
    for i in range(n):
        for j in range(i + 1, n):
            si = scores.get(_DOMAINS[i], 50)
            sj = scores.get(_DOMAINS[j], 50)
            if not isinstance(si, (int, float)):
                si = 50
            if not isinstance(sj, (int, float)):
                sj = 50
            similarity = 1.0 - abs(si - sj) / 100
            if similarity > 0.7 and adj[i][j] < 0.1:
                adj[i][j] = similarity * 0.3
                adj[j][i] = similarity * 0.3

    return adj


def _pagerank(adj, damping=0.85, iterations=50):
    """Pure Python PageRank."""
    n = len(adj)
    if n == 0:
        return []
    pr = [1.0 / n] * n
    for _ in range(iterations):
        new_pr = [(1 - damping) / n] * n
        for i in range(n):
            out_weight = sum(adj[i])
            if out_weight > 0:
                for j in range(n):
                    if adj[i][j] > 0:
                        new_pr[j] += damping * pr[i] * (adj[i][j] / out_weight)
        pr = new_pr
    return pr


def _betweenness_centrality(adj):
    """Simplified betweenness centrality via BFS on unweighted projection."""
    n = len(adj)
    bc = [0.0] * n

    for s in range(n):
        # BFS from s
        stack = []
        predecessors = [[] for _ in range(n)]
        sigma = [0.0] * n
        sigma[s] = 1.0
        dist = [-1] * n
        dist[s] = 0
        queue = [s]
        qi = 0

        while qi < len(queue):
            v = queue[qi]
            qi += 1
            stack.append(v)
            for w in range(n):
                if adj[v][w] > 0.1:  # edge exists
                    if dist[w] < 0:
                        dist[w] = dist[v] + 1
                        queue.append(w)
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]
                        predecessors[w].append(v)

        # Back-propagation
        delta = [0.0] * n
        while stack:
            w = stack.pop()
            for v in predecessors[w]:
                if sigma[w] > 0:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]

    # Normalize
    max_bc = max(bc) if bc else 1
    if max_bc > 0:
        bc = [b / max_bc for b in bc]
    return bc


def _degree_centrality(adj):
    """Compute in-degree + out-degree centrality."""
    n = len(adj)
    if n <= 1:
        return [1.0] * n
    dc = []
    for i in range(n):
        out_deg = sum(1 for j in range(n) if adj[i][j] > 0.1)
        in_deg = sum(1 for j in range(n) if adj[j][i] > 0.1)
        dc.append((out_deg + in_deg) / (2 * (n - 1)))
    return dc


def _eigenvector_centrality(adj, iterations=50):
    """Power iteration eigenvector centrality."""
    n = len(adj)
    if n == 0:
        return []
    x = [1.0 / n] * n
    for _ in range(iterations):
        new_x = [0.0] * n
        for i in range(n):
            for j in range(n):
                new_x[i] += adj[j][i] * x[j]
        norm = math.sqrt(sum(v * v for v in new_x)) or 1.0
        x = [v / norm for v in new_x]
    return x


def graph_centrality_analysis(scores, details=None, analytics=None):
    """Compute graph centrality metrics for the domain influence network.

    Returns dict:
        nodes: list of {domain, label, score, pagerank, betweenness, degree, eigenvector}
        edges: list of {source, target, weight}
        most_influential: domain name
        most_vulnerable: domain name
        cluster_groups: list of clusters
        key_insight: str
    """
    try:
        adj = _build_adjacency(scores)
        pr = _pagerank(adj)
        bc = _betweenness_centrality(adj)
        dc = _degree_centrality(adj)
        ec = _eigenvector_centrality(adj)

        nodes = []
        for i, d in enumerate(_DOMAINS):
            val = scores.get(d, 50)
            if not isinstance(val, (int, float)):
                val = 50
            nodes.append({
                "domain": d,
                "label": _DOMAIN_LABELS.get(d, d),
                "score": round(val, 1),
                "pagerank": round(pr[i], 4),
                "betweenness": round(bc[i], 4),
                "degree": round(dc[i], 4),
                "eigenvector": round(ec[i], 4),
            })

        edges = []
        for i in range(len(_DOMAINS)):
            for j in range(len(_DOMAINS)):
                if adj[i][j] > 0.1:
                    edges.append({
                        "source": _DOMAINS[i],
                        "target": _DOMAINS[j],
                        "weight": round(adj[i][j], 3),
                    })

        # Most influential = highest PageRank
        most_influential = max(nodes, key=lambda n: n["pagerank"])
        # Most vulnerable = lowest score + high betweenness (bottleneck)
        vuln_score = [(n["betweenness"] * (100 - n["score"]) / 100, n) for n in nodes]
        most_vulnerable = max(vuln_score, key=lambda x: x[0])[1]

        # Simple clustering by score bands
        clusters = []
        for band_name, lo, hi in [("Strong", 65, 101), ("Moderate", 40, 65), ("Weak", 0, 40)]:
            members = [n for n in nodes if lo <= n["score"] < hi]
            if members:
                clusters.append({
                    "label": band_name,
                    "members": [m["label"] for m in members],
                    "avg_pagerank": round(sum(m["pagerank"] for m in members) / len(members), 4),
                })

        insight = (
            f"{most_influential['label']} is the most influential domain (PageRank: "
            f"{most_influential['pagerank']:.3f}), while {most_vulnerable['label']} "
            f"represents the key vulnerability bottleneck."
        )

        return {
            "nodes": nodes,
            "edges": edges,
            "most_influential": most_influential["domain"],
            "most_vulnerable": most_vulnerable["domain"],
            "cluster_groups": clusters,
            "key_insight": insight,
        }
    except Exception as exc:
        logger.warning("Graph centrality analysis failed: %s", exc)
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# C. DBSCAN DOMAIN CLUSTERING
# ═══════════════════════════════════════════════════════════════════════════

def _euclidean(a, b):
    """Euclidean distance between two feature vectors."""
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def _extract_features(scores, details):
    """Build feature matrix: each domain => [score, sub-indicator1, sub-indicator2]."""
    features = {}
    for d in _DOMAINS:
        s = scores.get(d, 50)
        if not isinstance(s, (int, float)):
            s = 50
        det = details.get(d, {}) if isinstance(details, dict) else {}
        if not isinstance(det, dict):
            det = {}
        # Extract up to 3 sub-features from detail dict
        sub_vals = []
        for k, v in list(det.items())[:5]:
            if isinstance(v, (int, float)) and not math.isnan(v) and not math.isinf(v):
                sub_vals.append(v)
        # Normalize sub-values to 0-100 range (approximate)
        norm_subs = []
        for v in sub_vals[:2]:
            if abs(v) > 1000:
                norm_subs.append(min(max(v / 100, 0), 100))
            elif abs(v) <= 1:
                norm_subs.append(v * 100)
            else:
                norm_subs.append(min(max(v, 0), 100))
        while len(norm_subs) < 2:
            norm_subs.append(s)  # pad with score
        features[d] = [s] + norm_subs
    return features


def _auto_eps(features, k=3):
    """Auto-tune eps from k-distance plot."""
    domains = list(features.keys())
    n = len(domains)
    if n < 2:
        return 20.0

    # Compute k-th nearest neighbor distance for each point
    k_dists = []
    for i in range(n):
        dists = []
        for j in range(n):
            if i != j:
                dists.append(_euclidean(features[domains[i]], features[domains[j]]))
        dists.sort()
        k_dists.append(dists[min(k - 1, len(dists) - 1)])

    k_dists.sort()
    # Use the "elbow" — approximate as median
    eps = k_dists[len(k_dists) // 2] if k_dists else 20.0
    return max(eps, 5.0)  # minimum eps


def _dbscan(features, eps, min_pts=2):
    """Pure Python DBSCAN clustering.

    Returns: dict domain -> cluster_id (-1 = noise)
    """
    domains = list(features.keys())
    n = len(domains)
    labels = {d: -1 for d in domains}  # -1 = unvisited/noise
    cluster_id = 0

    def _neighbors(point_idx):
        nbrs = []
        for j in range(n):
            if _euclidean(features[domains[point_idx]], features[domains[j]]) <= eps:
                nbrs.append(j)
        return nbrs

    visited = set()
    for i in range(n):
        if i in visited:
            continue
        visited.add(i)
        nbrs = _neighbors(i)
        if len(nbrs) < min_pts:
            labels[domains[i]] = -1  # noise
            continue

        labels[domains[i]] = cluster_id
        seed_set = set(nbrs) - {i}

        while seed_set:
            j = seed_set.pop()
            if j not in visited:
                visited.add(j)
                j_nbrs = _neighbors(j)
                if len(j_nbrs) >= min_pts:
                    seed_set.update(set(j_nbrs) - visited)
            if labels[domains[j]] == -1:
                labels[domains[j]] = cluster_id

        cluster_id += 1

    return labels


def _silhouette_score(features, labels):
    """Compute simplified silhouette score."""
    domains = list(features.keys())
    clusters = defaultdict(list)
    for d in domains:
        clusters[labels[d]].append(d)

    # Remove noise
    valid_clusters = {k: v for k, v in clusters.items() if k >= 0}
    if len(valid_clusters) < 2:
        return 0.0

    sil_scores = []
    for d in domains:
        if labels[d] < 0:
            continue
        # a(i) = avg distance to same cluster
        same = [dd for dd in valid_clusters[labels[d]] if dd != d]
        if not same:
            continue
        a_i = sum(_euclidean(features[d], features[dd]) for dd in same) / len(same)

        # b(i) = min avg distance to other clusters
        b_i = float("inf")
        for cid, members in valid_clusters.items():
            if cid == labels[d]:
                continue
            avg_d = sum(_euclidean(features[d], features[dd]) for dd in members) / len(members)
            b_i = min(b_i, avg_d)

        if b_i == float("inf"):
            continue

        denom = max(a_i, b_i)
        sil_scores.append((b_i - a_i) / denom if denom > 0 else 0)

    return round(sum(sil_scores) / len(sil_scores), 3) if sil_scores else 0.0


def dbscan_domain_clustering(scores, details=None):
    """Run DBSCAN clustering on domain feature space.

    Returns dict:
        clusters: list of {id, label, members, centroid_score, coherence, characterization}
        noise_domains: list
        silhouette_score: float
    """
    try:
        if details is None:
            details = {}
        features = _extract_features(scores, details)
        eps = _auto_eps(features)
        labels = _dbscan(features, eps, min_pts=2)
        sil = _silhouette_score(features, labels)

        # Build cluster info
        cluster_map = defaultdict(list)
        noise = []
        for d, cid in labels.items():
            if cid < 0:
                noise.append(_DOMAIN_LABELS.get(d, d))
            else:
                cluster_map[cid].append(d)

        clusters = []
        _CLUSTER_NAMES = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
        for cid, members in sorted(cluster_map.items()):
            member_scores = [scores.get(d, 50) for d in members]
            valid_scores = [s for s in member_scores if isinstance(s, (int, float))]
            avg = sum(valid_scores) / len(valid_scores) if valid_scores else 50
            spread = max(valid_scores) - min(valid_scores) if len(valid_scores) > 1 else 0

            # Characterization
            if avg >= 70:
                char = "High-performing cluster"
            elif avg >= 50:
                char = "Moderate-performing cluster"
            else:
                char = "At-risk cluster"

            clusters.append({
                "id": cid,
                "label": _CLUSTER_NAMES[cid] if cid < len(_CLUSTER_NAMES) else f"Cluster-{cid}",
                "members": [_DOMAIN_LABELS.get(d, d) for d in members],
                "member_domains": members,
                "centroid_score": round(avg, 1),
                "coherence": round(1 - spread / 100, 2) if spread <= 100 else 0.5,
                "characterization": char,
            })

        return {
            "clusters": clusters,
            "noise_domains": noise,
            "silhouette_score": sil,
            "eps_used": round(eps, 2),
        }
    except Exception as exc:
        logger.warning("DBSCAN clustering failed: %s", exc)
        return {}


# ═══════════════════════════════════════════════════════════════════════════
# D. ROBUST ANOMALY DETECTION ENSEMBLE
# ═══════════════════════════════════════════════════════════════════════════

# Precomputed t-critical values for Grubbs test at alpha=0.05
_T_CRIT = {
    3: 1.153, 4: 1.463, 5: 1.672, 6: 1.822, 7: 1.938,
    8: 2.032, 9: 2.110, 10: 2.176, 11: 2.234, 12: 2.285,
    15: 2.409, 20: 2.557, 25: 2.663, 30: 2.745,
}


def _get_t_crit(n):
    """Interpolate t-critical for Grubbs test."""
    if n in _T_CRIT:
        return _T_CRIT[n]
    keys = sorted(_T_CRIT.keys())
    if n < keys[0]:
        return _T_CRIT[keys[0]]
    if n > keys[-1]:
        return _T_CRIT[keys[-1]]
    for i in range(len(keys) - 1):
        if keys[i] <= n <= keys[i + 1]:
            frac = (n - keys[i]) / (keys[i + 1] - keys[i])
            return _T_CRIT[keys[i]] + frac * (_T_CRIT[keys[i + 1]] - _T_CRIT[keys[i]])
    return 2.176  # fallback for n=10


def _z_score_outliers(values, threshold=2.0):
    """Detect outliers via Z-score method."""
    if len(values) < 3:
        return {d: False for d in values}
    vals = list(values.values())
    mean = sum(vals) / len(vals)
    std = math.sqrt(sum((v - mean) ** 2 for v in vals) / len(vals))
    if std < 1e-9:
        return {d: False for d in values}
    return {d: abs((v - mean) / std) > threshold for d, v in values.items()}


def _iqr_outliers(values, factor=1.5):
    """Detect outliers via IQR method."""
    if len(values) < 4:
        return {d: False for d in values}
    sorted_vals = sorted(values.values())
    n = len(sorted_vals)
    q1 = sorted_vals[n // 4]
    q3 = sorted_vals[(3 * n) // 4]
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return {d: (v < lower or v > upper) for d, v in values.items()}


def _grubbs_outliers(values):
    """Detect outliers via Grubbs' test (two-sided)."""
    if len(values) < 3:
        return {d: False for d in values}
    vals = list(values.values())
    n = len(vals)
    mean = sum(vals) / n
    std = math.sqrt(sum((v - mean) ** 2 for v in vals) / (n - 1)) if n > 1 else 0
    if std < 1e-9:
        return {d: False for d in values}

    t_crit = _get_t_crit(n)
    g_crit = ((n - 1) / math.sqrt(n)) * math.sqrt(t_crit ** 2 / (n - 2 + t_crit ** 2))

    result = {}
    for d, v in values.items():
        g = abs(v - mean) / std
        result[d] = g > g_crit
    return result


def robust_anomaly_ensemble(scores, details=None, analytics=None):
    """Run 3-method anomaly detection ensemble.

    2/3 agreement = high confidence anomaly.

    Returns dict:
        anomalies: dict per domain with z_score, iqr, grubbs, ensemble_confidence, severity
        baseline_stats: {mean, std, q1, median, q3}
        overall_profile: str description
    """
    try:
        # Build values dict
        values = {}
        for d in _DOMAINS:
            v = scores.get(d, None)
            if isinstance(v, (int, float)):
                values[d] = v
            else:
                values[d] = 50

        z_out = _z_score_outliers(values)
        iqr_out = _iqr_outliers(values)
        grubbs_out = _grubbs_outliers(values)

        # Baseline stats
        vals = list(values.values())
        vals_sorted = sorted(vals)
        n = len(vals)
        mean = sum(vals) / n if n else 0
        std = math.sqrt(sum((v - mean) ** 2 for v in vals) / n) if n else 0
        q1 = vals_sorted[n // 4] if n >= 4 else (vals_sorted[0] if vals_sorted else 0)
        median = vals_sorted[n // 2] if n else 0
        q3 = vals_sorted[(3 * n) // 4] if n >= 4 else (vals_sorted[-1] if vals_sorted else 0)

        anomalies = {}
        anomaly_count = 0
        for d in _DOMAINS:
            z = z_out.get(d, False)
            iqr = iqr_out.get(d, False)
            grb = grubbs_out.get(d, False)
            votes = sum([z, iqr, grb])
            is_anomaly = votes >= 2

            if is_anomaly:
                anomaly_count += 1

            # Z-score for severity
            z_val = abs(values[d] - mean) / std if std > 1e-9 else 0

            severity = "NORMAL"
            if votes == 3:
                severity = "CRITICAL"
            elif votes == 2:
                severity = "WARNING"
            elif votes == 1:
                severity = "NOTABLE"

            anomalies[d] = {
                "label": _DOMAIN_LABELS.get(d, d),
                "score": values[d],
                "z_score_outlier": z,
                "iqr_outlier": iqr,
                "grubbs_outlier": grb,
                "ensemble_votes": votes,
                "ensemble_confidence": "HIGH" if votes >= 2 else ("LOW" if votes == 1 else "NONE"),
                "is_anomaly": is_anomaly,
                "severity": severity,
                "z_value": round(z_val, 2),
                "deviation_from_mean": round(values[d] - mean, 1),
            }

        # Overall profile
        if anomaly_count == 0:
            profile = "HOMOGENEOUS — No significant anomalies detected across domains."
        elif anomaly_count <= 2:
            profile = f"STABLE — {anomaly_count} domain(s) show outlier behavior."
        elif anomaly_count <= 4:
            profile = f"HETEROGENEOUS — {anomaly_count} domains flagged as anomalous."
        else:
            profile = f"VOLATILE — {anomaly_count} domains show significant deviation."

        return {
            "anomalies": anomalies,
            "baseline_stats": {
                "mean": round(mean, 1),
                "std": round(std, 1),
                "q1": round(q1, 1),
                "median": round(median, 1),
                "q3": round(q3, 1),
                "iqr": round(q3 - q1, 1),
            },
            "overall_profile": profile,
            "anomaly_count": anomaly_count,
        }
    except Exception as exc:
        logger.warning("Robust anomaly ensemble failed: %s", exc)
        return {}
