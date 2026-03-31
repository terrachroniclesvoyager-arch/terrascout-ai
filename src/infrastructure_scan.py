"""
Infrastructure Completeness Scan module for TerraScout AI.
Evaluates how complete the infrastructure is around a point -- what is there
and what is missing across 10 key categories (healthcare, education, emergency,
commercial, food & dining, transport, utilities, recreation, government,
religious).  All data is sourced from the Overpass API (free, no key required).

Part of TerraScout AI.
"""

import logging
import math
import requests
try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & category definitions
# ---------------------------------------------------------------------------

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

CATEGORIES = {
    "healthcare": {
        "icon": "\U0001f3e5", "label": "Healthcare", "radius": 5000,
        "color": "#ef4444",
        "tags": {
            "hospital": ("amenity", "hospital"), "clinic": ("amenity", "clinic"),
            "pharmacy": ("amenity", "pharmacy"), "dentist": ("amenity", "dentist"),
            "veterinary": ("amenity", "veterinary"),
        },
    },
    "education": {
        "icon": "\U0001f393", "label": "Education", "radius": 5000,
        "color": "#8b5cf6",
        "tags": {
            "school": ("amenity", "school"), "university": ("amenity", "university"),
            "kindergarten": ("amenity", "kindergarten"), "library": ("amenity", "library"),
        },
    },
    "emergency": {
        "icon": "\U0001f6a8", "label": "Emergency Services", "radius": 5000,
        "color": "#f97316",
        "tags": {
            "police": ("amenity", "police"), "fire_station": ("amenity", "fire_station"),
            "ambulance_station": ("emergency", "ambulance_station"),
        },
    },
    "commercial": {
        "icon": "\U0001f6d2", "label": "Commercial", "radius": 3000,
        "color": "#ec4899",
        "tags": {
            "supermarket": ("shop", "supermarket"), "mall": ("shop", "mall"),
            "bank": ("amenity", "bank"), "atm": ("amenity", "atm"),
            "fuel": ("amenity", "fuel"), "convenience": ("shop", "convenience"),
        },
    },
    "food_dining": {
        "icon": "\U0001f37d\ufe0f", "label": "Food & Dining", "radius": 3000,
        "color": "#f59e0b",
        "tags": {
            "restaurant": ("amenity", "restaurant"), "cafe": ("amenity", "cafe"),
            "fast_food": ("amenity", "fast_food"), "bakery": ("shop", "bakery"),
            "butcher": ("shop", "butcher"),
        },
    },
    "transport": {
        "icon": "\U0001f68c", "label": "Transport", "radius": 3000,
        "color": "#3b82f6",
        "tags": {
            "bus_stop": ("highway", "bus_stop"), "train_station": ("railway", "station"),
            "parking": ("amenity", "parking"), "taxi": ("amenity", "taxi"),
            "bicycle_rental": ("amenity", "bicycle_rental"),
        },
    },
    "utilities": {
        "icon": "\u26a1", "label": "Utilities", "radius": 5000,
        "color": "#06b6d4",
        "tags": {
            "power_line": ("power", "line"), "water_tower": ("man_made", "water_tower"),
            "substation": ("power", "substation"), "telecom_tower": ("man_made", "tower"),
        },
    },
    "recreation": {
        "icon": "\U0001f3de\ufe0f", "label": "Recreation", "radius": 3000,
        "color": "#22c55e",
        "tags": {
            "park": ("leisure", "park"), "sports_centre": ("leisure", "sports_centre"),
            "swimming_pool": ("leisure", "swimming_pool"), "cinema": ("amenity", "cinema"),
            "playground": ("leisure", "playground"),
        },
    },
    "government": {
        "icon": "\U0001f3db\ufe0f", "label": "Government", "radius": 5000,
        "color": "#64748b",
        "tags": {
            "townhall": ("amenity", "townhall"), "post_office": ("amenity", "post_office"),
            "courthouse": ("amenity", "courthouse"), "embassy": ("amenity", "embassy"),
        },
    },
    "religious": {
        "icon": "\U0001f54c", "label": "Religious", "radius": 3000,
        "color": "#a855f7",
        "tags": {"place_of_worship": ("amenity", "place_of_worship")},
    },
}

# Minimum expected counts per sub-type to reach 100% completeness
_EXPECTED_COUNTS = {
    "healthcare":  {"hospital": 1, "clinic": 2, "pharmacy": 3, "dentist": 1, "veterinary": 1},
    "education":   {"school": 3, "university": 1, "kindergarten": 2, "library": 1},
    "emergency":   {"police": 1, "fire_station": 1, "ambulance_station": 1},
    "commercial":  {"supermarket": 2, "mall": 1, "bank": 2, "atm": 3, "fuel": 2, "convenience": 2},
    "food_dining": {"restaurant": 3, "cafe": 2, "fast_food": 2, "bakery": 1, "butcher": 1},
    "transport":   {"bus_stop": 5, "train_station": 1, "parking": 3, "taxi": 1, "bicycle_rental": 1},
    "utilities":   {"power_line": 1, "water_tower": 1, "substation": 1, "telecom_tower": 1},
    "recreation":  {"park": 2, "sports_centre": 1, "swimming_pool": 1, "cinema": 1, "playground": 2},
    "government":  {"townhall": 1, "post_office": 1, "courthouse": 1, "embassy": 1},
    "religious":   {"place_of_worship": 2},
}

RATING_BANDS = [
    (85, 100, "Excellent", "#10b981"),
    (70, 84,  "Good",      "#22c55e"),
    (50, 69,  "Moderate",  "#f59e0b"),
    (30, 49,  "Weak",      "#f97316"),
    (0,  29,  "Poor",      "#ef4444"),
]

FOLIUM_COLORS = {
    "healthcare": "red", "education": "purple", "emergency": "orange",
    "commercial": "pink", "food_dining": "beige", "transport": "blue",
    "utilities": "lightblue", "recreation": "green", "government": "gray",
    "religious": "darkpurple",
}

_RECOMMENDATION_TEXT = {
    "healthcare": "Healthcare coverage is limited. Verify emergency medical response times and consider proximity to the nearest hospital or clinic outside the scanned radius.",
    "education": "Educational facilities are sparse. Online learning platforms or facilities in neighbouring areas may compensate.",
    "emergency": "Emergency services are lacking. Check response times for police, fire and ambulance before relying on local coverage.",
    "commercial": "Commercial services are thin. Plan for online ordering, bulk shopping trips, or delivery services.",
    "food_dining": "Food and dining options are limited. Grocery delivery or meal-prep services might be necessary.",
    "transport": "Public transport is weak. A personal vehicle or ride-sharing service may be essential for daily commutes.",
    "utilities": "Core utility infrastructure is sparse. Verify power reliability, water supply and mobile signal strength.",
    "recreation": "Recreational facilities are few. Look for nature reserves or parks beyond the scan radius for leisure activities.",
    "government": "Government offices are limited. Administrative tasks may require travel to a larger urban centre.",
    "religious": "Religious facilities are scarce or absent. Nearby towns may offer additional places of worship.",
}


# ---------------------------------------------------------------------------
# Data-fetching helpers
# ---------------------------------------------------------------------------

@st.cache_data(ttl=900)
def _query_overpass(lat: float, lon: float, body: str) -> list:
    """Execute an Overpass API query and return the elements list."""
    query = f"[out:json][timeout:25];\n(\n{body}\n);\nout center body;"
    try:
        resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=10)
        resp.raise_for_status()
        return resp.json().get("elements", [])
    except Exception as exc:
        logger.warning("Overpass query error: %s", exc)
        return []


@st.cache_data(ttl=900)
def _fetch_category(lat: float, lon: float, cat_key: str) -> list:
    """Fetch all features for one infrastructure category via Overpass."""
    cat = CATEGORIES[cat_key]
    radius = cat["radius"]
    lines = []
    for _sub_key, (tag_key, tag_val) in cat["tags"].items():
        lines.append(f'node["{tag_key}"="{tag_val}"](around:{radius},{lat},{lon});')
        lines.append(f'way["{tag_key}"="{tag_val}"](around:{radius},{lat},{lon});')
    return _query_overpass(lat, lon, "\n".join(lines))


@st.cache_data(ttl=900)
def _fetch_all_categories(lat: float, lon: float) -> dict:
    """Fetch infrastructure data for every category."""
    return {ck: _fetch_category(lat, lon, ck) for ck in CATEGORIES}


# ---------------------------------------------------------------------------
# Counting & classification helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in kilometres."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _classify_element(element: dict, cat_key: str) -> str | None:
    """Return the sub-type label for an element within a category, or None."""
    tags = element.get("tags", {})
    for sub_key, (tag_key, tag_val) in CATEGORIES[cat_key]["tags"].items():
        if tags.get(tag_key) == tag_val:
            return sub_key
    return None


def _count_subtypes(elements: list, cat_key: str) -> dict:
    """Count how many elements match each sub-type in a category."""
    counts: dict = {sub: 0 for sub in CATEGORIES[cat_key]["tags"]}
    for el in elements:
        sub = _classify_element(el, cat_key)
        if sub and sub in counts:
            counts[sub] += 1
    return counts


def _compute_category_score(counts: dict, cat_key: str) -> tuple:
    """Compute completeness score (0-100), found list, missing list."""
    expected = _EXPECTED_COUNTS.get(cat_key, {})
    if not expected:
        return 100, [], []
    found, missing, sub_scores = [], [], []
    for sub_key, min_needed in expected.items():
        actual = counts.get(sub_key, 0)
        nice_name = sub_key.replace("_", " ").title()
        if actual > 0:
            found.append((nice_name, actual))
            sub_scores.append(min(actual / max(min_needed, 1), 1.0))
        else:
            missing.append(nice_name)
            sub_scores.append(0.0)
    score = round((sum(sub_scores) / len(sub_scores)) * 100) if sub_scores else 0
    return score, found, missing


def _get_rating(score: float) -> tuple:
    """Return (label, color) for a percentage score."""
    for lo, hi, label, color in RATING_BANDS:
        if lo <= score <= hi:
            return label, color
    return "Poor", "#ef4444"


def _overall_score(category_scores: dict) -> float:
    """Average of all category scores."""
    vals = list(category_scores.values())
    return round(sum(vals) / len(vals), 1) if vals else 0.0


def _element_coords(el: dict) -> tuple | None:
    """Extract (lat, lon) from an Overpass element (node or way center)."""
    lat, lon = el.get("lat"), el.get("lon")
    if lat is not None and lon is not None:
        return (lat, lon)
    center = el.get("center", {})
    clat, clon = center.get("lat"), center.get("lon")
    if clat is not None and clon is not None:
        return (clat, clon)
    return None


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _render_overall_header(score: float):
    """Display the big overall infrastructure completeness score."""
    label, color = _get_rating(score)
    st.markdown(
        f"<div style='text-align:center; padding:24px 16px; "
        f"background:linear-gradient(135deg, {color}18, {color}08); "
        f"border:2px solid {color}44; border-radius:16px; margin-bottom:20px;'>"
        f"<div style='font-size:3.2rem; font-weight:800; color:{color};'>"
        f"{score:.0f}%</div>"
        f"<div style='font-size:1.15rem; font-weight:600; color:{color}; "
        f"margin-top:4px;'>Overall Infrastructure Completeness</div>"
        f"<div style='font-size:0.9rem; color:#6b7280; margin-top:6px;'>"
        f"Rating: <b>{label}</b> &mdash; across {len(CATEGORIES)} categories</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_category_cards(cat_scores, cat_counts, cat_found, cat_missing):
    """Render the 10 category cards with progress bars and missing highlights."""
    cols = st.columns(2)
    for idx, (cat_key, cat) in enumerate(CATEGORIES.items()):
        col = cols[idx % 2]
        score = cat_scores.get(cat_key, 0)
        _, bar_color = _get_rating(score)
        found_items = cat_found.get(cat_key, [])
        missing_items = cat_missing.get(cat_key, [])
        total_count = sum(cat_counts.get(cat_key, {}).values())
        with col:
            st.markdown(
                f"<div style='border:1px solid {cat['color']}44; border-radius:12px; "
                f"padding:14px 16px; margin-bottom:12px; background:{cat['color']}08;'>"
                f"<div style='display:flex; justify-content:space-between; "
                f"align-items:center; margin-bottom:6px;'>"
                f"<span style='font-size:1.05rem; font-weight:600;'>"
                f"{cat['icon']} {cat['label']}</span>"
                f"<span style='font-size:1.25rem; font-weight:700; color:{bar_color};'>"
                f"{score}%</span></div>"
                f"<div style='background:#e5e7eb; border-radius:6px; height:8px; "
                f"margin-bottom:8px;'>"
                f"<div style='background:{cat['color']}; width:{min(score, 100)}%; "
                f"height:100%; border-radius:6px;'></div></div>"
                f"<div style='font-size:0.78rem; color:#6b7280;'>"
                f"{total_count} feature(s) within {cat['radius'] / 1000:.0f} km</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            with st.expander(f"Details: {cat['label']}", expanded=False):
                if found_items:
                    st.markdown("**Found:**")
                    for name, cnt in found_items:
                        st.markdown(f"- :green[{name}] &mdash; {cnt} found")
                if missing_items:
                    st.markdown("**Missing:**")
                    for name in missing_items:
                        st.markdown(f"- :red[{name}] &mdash; **NOT FOUND**")
                if not found_items and not missing_items:
                    st.info("No sub-type data available.")


def _render_ranking_chart(cat_scores: dict):
    """Horizontal bar chart ranking categories by completeness."""
    sorted_cats = sorted(cat_scores.items(), key=lambda x: x[1])
    names, scores, colors = [], [], []
    for cat_key, score in sorted_cats:
        cat = CATEGORIES[cat_key]
        names.append(f"{cat['icon']} {cat['label']}")
        scores.append(score)
        colors.append(cat["color"])
    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h", marker_color=colors,
        text=[f"{s}%" for s in scores], textposition="outside",
    ))
    fig.update_layout(
        title="Infrastructure Completeness by Category",
        xaxis_title="Completeness (%)", xaxis=dict(range=[0, 110]),
        yaxis_title="", height=420,
        margin=dict(l=180, r=50, t=50, b=40),
    )
    st.plotly_chart(fig, use_container_width=True, key="infsca_pchart1")


def _render_map(lat: float, lon: float, all_elements: dict):
    """Render a folium map with infrastructure markers coloured by category."""
    try:
        import folium
        from streamlit_folium import st_folium
    except ImportError:
        st.info("Install folium and streamlit-folium for the interactive map.")
        return
    m = folium.Map(location=[lat, lon], zoom_start=14, tiles="CartoDB positron")
    folium.Marker(
        [lat, lon], popup="Target Location",
        icon=folium.Icon(color="red", icon="crosshairs", prefix="fa"),
    ).add_to(m)
    marker_count = 0
    for cat_key, elements in all_elements.items():
        cat = CATEGORIES[cat_key]
        for el in elements:
            if marker_count >= 200:
                break
            coords = _element_coords(el)
            if coords is None:
                continue
            el_lat, el_lon = coords
            tags = el.get("tags", {})
            name = tags.get("name", cat["label"])
            sub = _classify_element(el, cat_key) or ""
            folium.CircleMarker(
                [el_lat, el_lon], radius=5, color=cat["color"],
                fill=True, fill_color=cat["color"], fill_opacity=0.7,
                popup=f"{name} ({sub.replace('_', ' ')})",
            ).add_to(m)
            marker_count += 1
    folium.Circle([lat, lon], radius=3000, color="#3b82f6",
                  fill=False, dash_array="5", popup="3 km radius").add_to(m)
    folium.Circle([lat, lon], radius=5000, color="#8b5cf6",
                  fill=False, dash_array="10", popup="5 km radius").add_to(m)
    st_folium(m, width=None, height=500, key="infrascan_folium_map")


def _render_summary_table(cat_scores, cat_counts, cat_found, cat_missing):
    """Render a full summary markdown table with all categories."""
    st.markdown("### Summary Table")
    header = (
        "| # | Category | Score | Features | Found Types | Missing Types |\n"
        "|---|----------|-------|----------|-------------|---------------|\n"
    )
    rows = ""
    for idx, (cat_key, cat) in enumerate(CATEGORIES.items(), start=1):
        score = cat_scores.get(cat_key, 0)
        total = sum(cat_counts.get(cat_key, {}).values())
        found_names = [n for n, _ in cat_found.get(cat_key, [])]
        missing_names = cat_missing.get(cat_key, [])
        found_str = ", ".join(found_names) if found_names else "-"
        missing_str = ", ".join(missing_names) if missing_names else "-"
        rows += (
            f"| {idx} | {cat['icon']} {cat['label']} | {score}% "
            f"| {total} | {found_str} | {missing_str} |\n"
        )
    st.markdown(header + rows)


def _render_gap_analysis(cat_scores: dict, cat_missing: dict):
    """Highlight critical and moderate infrastructure gaps."""
    critical, moderate = [], []
    for cat_key, score in cat_scores.items():
        missing = cat_missing.get(cat_key, [])
        cat = CATEGORIES[cat_key]
        if score < 30 and missing:
            critical.append((cat, missing, score))
        elif score < 60 and missing:
            moderate.append((cat, missing, score))

    st.markdown("### Infrastructure Gap Analysis")
    if critical:
        st.markdown(
            "<div style='background:#ef444418; border-left:4px solid #ef4444; "
            "padding:14px 16px; border-radius:8px; margin-bottom:12px;'>"
            "<h4 style='margin:0 0 8px 0; color:#ef4444;'>Critical Gaps</h4>",
            unsafe_allow_html=True,
        )
        for cat, missing, score in critical:
            st.markdown(
                f"- {cat['icon']} **{cat['label']}** ({score}%): "
                f"Missing -- {', '.join(missing)}"
            )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.success("No critical infrastructure gaps detected.")
    if moderate:
        st.markdown(
            "<div style='background:#f59e0b18; border-left:4px solid #f59e0b; "
            "padding:14px 16px; border-radius:8px; margin-bottom:12px;'>"
            "<h4 style='margin:0 0 8px 0; color:#f59e0b;'>Moderate Gaps</h4>",
            unsafe_allow_html=True,
        )
        for cat, missing, score in moderate:
            st.markdown(
                f"- {cat['icon']} **{cat['label']}** ({score}%): "
                f"Missing -- {', '.join(missing)}"
            )
        st.markdown("</div>", unsafe_allow_html=True)
    if not critical and not moderate:
        st.info("Infrastructure coverage is adequate across all categories.")


def _render_radar_chart(cat_scores: dict):
    """Radar/spider chart of all 10 category scores."""
    labels = [CATEGORIES[ck]["label"] for ck in CATEGORIES]
    values = [cat_scores.get(ck, 0) for ck in CATEGORIES]
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed, theta=labels_closed, fill="toself",
        fillcolor="rgba(59,130,246,0.15)",
        line=dict(color="#3b82f6", width=2), name="Completeness",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False, height=440,
        margin=dict(t=40, b=40, l=90, r=90), title="Infrastructure Radar",
    )
    st.plotly_chart(fig, use_container_width=True, key="infsca_pchart2")


def _render_strengths_weaknesses(cat_scores: dict):
    """Two-column display of top strengths and weaknesses."""
    sorted_cats = sorted(cat_scores.items(), key=lambda x: x[1], reverse=True)
    strengths = [(k, v) for k, v in sorted_cats if v >= 70]
    weaknesses = [(k, v) for k, v in sorted_cats if v < 50]
    col_s, col_w = st.columns(2)
    with col_s:
        st.markdown("**Strengths**")
        if strengths:
            for ck, sc in strengths[:5]:
                st.markdown(f"- {CATEGORIES[ck]['icon']} {CATEGORIES[ck]['label']}: **{sc}%**")
        else:
            st.markdown("_No strong categories detected._")
    with col_w:
        st.markdown("**Weaknesses**")
        if weaknesses:
            for ck, sc in weaknesses[:5]:
                st.markdown(f"- {CATEGORIES[ck]['icon']} {CATEGORIES[ck]['label']}: **{sc}%**")
        else:
            st.markdown("_No weak categories detected._")


def _render_nearest_analysis(lat: float, lon: float, all_elements: dict):
    """Show the nearest facility in each category with distance."""
    st.markdown("### Nearest Facility per Category")
    rows = []
    for cat_key, cat in CATEGORIES.items():
        nearest_name, nearest_dist, nearest_type = "-", None, "-"
        for el in all_elements.get(cat_key, []):
            coords = _element_coords(el)
            if coords is None:
                continue
            dist = _haversine_km(lat, lon, coords[0], coords[1])
            if nearest_dist is None or dist < nearest_dist:
                nearest_dist = dist
                nearest_name = el.get("tags", {}).get("name", "Unnamed")
                sub = _classify_element(el, cat_key)
                nearest_type = sub.replace("_", " ").title() if sub else "-"
        dist_str = f"{nearest_dist:.2f} km" if nearest_dist is not None else "N/A"
        rows.append(f"| {cat['icon']} {cat['label']} | {nearest_name} | {nearest_type} | {dist_str} |")
    header = "| Category | Nearest Facility | Type | Distance |\n|----------|------------------|------|----------|\n"
    st.markdown(header + "\n".join(rows))


def _render_density_chart(cat_counts: dict):
    """Bar chart showing total feature count per category."""
    names, totals, colors = [], [], []
    for cat_key, cat in CATEGORIES.items():
        names.append(f"{cat['icon']} {cat['label']}")
        totals.append(sum(cat_counts.get(cat_key, {}).values()))
        colors.append(cat["color"])
    fig = go.Figure(go.Bar(
        x=names, y=totals, marker_color=colors,
        text=totals, textposition="outside",
    ))
    fig.update_layout(
        title="Feature Count by Category", yaxis_title="Count", xaxis_title="",
        height=380, margin=dict(l=40, r=30, t=50, b=100),
        xaxis=dict(tickangle=-40),
    )
    st.plotly_chart(fig, use_container_width=True, key="infsca_pchart3")


def _render_recommendations(cat_scores: dict):
    """Actionable recommendations based on detected gaps."""
    st.markdown("### Recommendations")
    recs = []
    for cat_key, msg in _RECOMMENDATION_TEXT.items():
        if cat_scores.get(cat_key, 100) < 50:
            cat = CATEGORIES[cat_key]
            recs.append(f"- {cat['icon']} **{cat['label']}**: {msg}")
    if recs:
        for r in recs:
            st.markdown(r)
    else:
        st.success("This location has good infrastructure coverage across all categories. No critical recommendations.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def render_infrastructure_scan_tab():
    """Render the Infrastructure Completeness Scan module."""
    st.markdown("## \U0001f3d7\ufe0f Infrastructure Completeness Scan")
    st.caption("What's here, what's missing & infrastructure gaps analysis")

    # -- Input controls -------------------------------------------------------
    col_lat, col_lon = st.columns(2)
    lat = col_lat.number_input("Latitude", value=41.9028, format="%.4f", key="infrascan_lat")
    lon = col_lon.number_input("Longitude", value=12.4964, format="%.4f", key="infrascan_lon")

    if not st.button("Run Infrastructure Scan", key="infrascan_btn", type="primary"):
        st.info("Enter coordinates and click **Run Infrastructure Scan** to begin.")
        return

    # -- Data fetching --------------------------------------------------------
    cat_scores: dict = {}
    cat_counts: dict = {}
    cat_found: dict = {}
    cat_missing: dict = {}
    all_elements: dict = {}

    progress_bar = st.progress(0, text="Starting infrastructure scan...")
    total_cats = len(CATEGORIES)

    for step, (cat_key, cat) in enumerate(CATEGORIES.items()):
        pct = int((step / total_cats) * 100)
        progress_bar.progress(
            pct,
            text=f"Scanning {cat['icon']} {cat['label']} ({cat['radius'] / 1000:.0f} km)...",
        )
        elements = _fetch_category(lat, lon, cat_key)
        all_elements[cat_key] = elements
        counts = _count_subtypes(elements, cat_key)
        cat_counts[cat_key] = counts
        score, found, missing = _compute_category_score(counts, cat_key)
        cat_scores[cat_key] = score
        cat_found[cat_key] = found
        cat_missing[cat_key] = missing

    progress_bar.progress(100, text="Scan complete.")
    overall = _overall_score(cat_scores)

    # -- Render results -------------------------------------------------------
    st.markdown("---")
    _render_overall_header(overall)

    st.markdown("---")
    st.markdown("### Category Breakdown")
    _render_category_cards(cat_scores, cat_counts, cat_found, cat_missing)

    st.markdown("---")
    col_radar, col_rank = st.columns(2)
    with col_radar:
        _render_radar_chart(cat_scores)
    with col_rank:
        _render_ranking_chart(cat_scores)

    st.markdown("---")
    _render_strengths_weaknesses(cat_scores)

    st.markdown("---")
    _render_gap_analysis(cat_scores, cat_missing)

    st.markdown("---")
    st.markdown("### Infrastructure Map")
    _render_map(lat, lon, all_elements)

    st.markdown("---")
    _render_density_chart(cat_counts)

    st.markdown("---")
    _render_nearest_analysis(lat, lon, all_elements)

    st.markdown("---")
    _render_summary_table(cat_scores, cat_counts, cat_found, cat_missing)

    st.markdown("---")
    _render_recommendations(cat_scores)
