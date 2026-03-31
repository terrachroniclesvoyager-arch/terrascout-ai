"""
Global Health Explorer module for TerraScout AI.
Uses free APIs (no API key): disease.sh, WHO GHO OData, REST Countries, Overpass.
"""

import io, html
import streamlit as st
import requests
import pandas as pd
try:
    import folium
    from folium.plugins import MarkerCluster
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from src.overpass_client import query_overpass

# ── Constants ────────────────────────────────────────────
DISEASE_SH = "https://disease.sh/v3/covid-19"
WHO_API = "https://ghoapi.azureedge.net/api"
REST_COUNTRIES = "https://restcountries.com/v3.1/all"

WHO_INDICATORS = {
    "WHOSIS_000001": {"name": "Life Expectancy at Birth", "unit": "years"},
    "MDG_0000000026": {"name": "Maternal Mortality Ratio", "unit": "per 100k"},
    "WHS4_100": {"name": "Immunization Coverage (DTP3)", "unit": "%"},
    "MDG_0000000001": {"name": "Under-5 Mortality Rate", "unit": "per 1,000"},
    "HWF_0001": {"name": "Physicians per 10,000", "unit": "per 10k"},
    "UHC_INDEX_REPORTED": {"name": "UHC Service Coverage Index", "unit": "index"},
}

CITY_PRESETS = {
    "New York": {"lat": 40.7, "lon": -74.0},
    "London": {"lat": 51.5, "lon": -0.1},
    "Tokyo": {"lat": 35.7, "lon": 139.7},
    "Lagos": {"lat": 6.5, "lon": 3.4},
    "Mumbai": {"lat": 19.1, "lon": 72.9},
    "Sao Paulo": {"lat": -23.6, "lon": -46.6},
    "Sydney": {"lat": -33.9, "lon": 151.2},
    "Cairo": {"lat": 30.0, "lon": 31.2},
}

FACILITY_STYLES = {
    "hospital": {"color": "#ef4444", "radius": 8, "label": "Hospital"},
    "clinic": {"color": "#f59e0b", "radius": 6, "label": "Clinic"},
    "pharmacy": {"color": "#10b981", "radius": 5, "label": "Pharmacy"},
}

# ── Chart helper ─────────────────────────────────────────
def _dark_fig(figsize=(10, 5)):
    """Create a dark-themed matplotlib figure and axis."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
    ax.tick_params(axis="both", colors="#8b97b0", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    return fig, ax

# ── API functions ────────────────────────────────────────
@st.cache_data(ttl=1800)
def fetch_covid_countries() -> list:
    """Fetch COVID-19 data for all countries from disease.sh."""
    try:
        resp = requests.get(f"{DISEASE_SH}/countries", params={"sort": "cases"}, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []

@st.cache_data(ttl=1800)
def fetch_covid_global() -> dict:
    """Fetch global COVID-19 summary."""
    try:
        resp = requests.get(f"{DISEASE_SH}/all", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}

@st.cache_data(ttl=1800)
def fetch_covid_historical(days: int = 365) -> dict:
    """Fetch historical COVID-19 timeline (worldwide)."""
    try:
        resp = requests.get(f"{DISEASE_SH}/historical/all", params={"lastdays": days}, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}

@st.cache_data(ttl=1800)
def fetch_rest_countries() -> list:
    """Fetch country metadata from REST Countries API."""
    try:
        resp = requests.get(REST_COUNTRIES,
                            params={"fields": "name,population,region,subregion,latlng,cca2"},
                            timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return []

@st.cache_data(ttl=1800)
def fetch_who_indicator(indicator_code: str, country_code: str = None) -> list:
    """Fetch WHO GHO indicator, optionally filtered by country ISO code."""
    url = f"{WHO_API}/{indicator_code}"
    params = {}
    if country_code:
        params["$filter"] = f"SpatialDim eq '{country_code}'"
    try:
        resp = requests.get(url, params=params, timeout=25)
        resp.raise_for_status()
        return resp.json().get("value", [])
    except Exception:
        return []

@st.cache_data(ttl=1800)
def fetch_healthcare_overpass(lat: float, lon: float, radius: int = 5000) -> dict:
    """Query Overpass for hospitals, clinics, and pharmacies."""
    query = f"""[out:json][timeout:60];(
      node["amenity"="hospital"](around:{radius},{lat},{lon});
      way["amenity"="hospital"](around:{radius},{lat},{lon});
      node["amenity"="clinic"](around:{radius},{lat},{lon});
      way["amenity"="clinic"](around:{radius},{lat},{lon});
      node["amenity"="pharmacy"](around:{radius},{lat},{lon});
      way["amenity"="pharmacy"](around:{radius},{lat},{lon});
    );out center body;"""
    result = query_overpass(query)
    if result is None:
        return {"elements": [], "_error": "All Overpass servers unreachable"}
    if isinstance(result, dict) and result.get("_error"):
        return {"elements": [], "_error": result["_error"]}
    return result

def _latest_who_value(records: list):
    """Extract latest numeric value and year from WHO GHO records."""
    if not records:
        return None, None
    both = [r for r in records if r.get("Dim1") in ("BTSX", "SEX_BTSX", None, "")]
    pool = both if both else records
    pairs = []
    for r in pool:
        val, year = r.get("NumericValue"), r.get("TimeDim") or r.get("TimeDimensionValue")
        if val is not None:
            try:
                pairs.append((int(year) if year else 0, float(val)))
            except (ValueError, TypeError):
                continue
    if not pairs:
        return None, None
    pairs.sort(key=lambda x: x[0], reverse=True)
    return pairs[0][1], pairs[0][0]

# ── Mode 1: Disease Tracker ─────────────────────────────
def _render_disease_tracker():
    """COVID-19 tracking with global stats, world map, and historical trends."""
    st.markdown("#### Disease Tracker")
    st.caption("COVID-19 statistics from disease.sh with per-country map and historical trends.")
    if st.button("Load Disease Data", key="gh_load_disease", use_container_width=True):
        st.session_state["gh_disease_go"] = True
    if not st.session_state.get("gh_disease_go"):
        st.info("Click Load to fetch the latest global disease data.")
        return
    with st.spinner("Fetching global disease data..."):
        g = fetch_covid_global()
        countries = fetch_covid_countries()
        history = fetch_covid_historical(365)
    if not g:
        st.error("Failed to load global COVID data. The disease.sh API may be temporarily unavailable.")
        return
    # Global summary
    st.markdown("---")
    st.markdown("##### Global Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Cases", f"{g.get('cases', 0):,.0f}")
    with c2: st.metric("Total Deaths", f"{g.get('deaths', 0):,.0f}")
    with c3: st.metric("Recovered", f"{g.get('recovered', 0):,.0f}")
    with c4: st.metric("Active", f"{g.get('active', 0):,.0f}")
    # Historical trend chart
    if history:
        st.markdown("---")
        st.markdown("##### Historical Trends (Past Year)")
        cases_ts = history.get("cases", {})
        deaths_ts = history.get("deaths", {})
        if cases_ts:
            dates = list(cases_ts.keys())
            case_vals = list(cases_ts.values())
            death_vals = [deaths_ts.get(d, 0) for d in dates]
            fig, ax1 = _dark_fig(figsize=(11, 4))
            ax1.plot(range(len(dates)), case_vals, color="#06b6d4", linewidth=1.2, label="Cases")
            ax1.set_ylabel("Cumulative Cases", color="#06b6d4", fontsize=9)
            ax1.tick_params(axis="y", labelcolor="#06b6d4")
            ax2 = ax1.twinx()
            ax2.plot(range(len(dates)), death_vals, color="#ef4444", linewidth=1.2, label="Deaths")
            ax2.set_ylabel("Cumulative Deaths", color="#ef4444", fontsize=9)
            ax2.tick_params(axis="y", labelcolor="#ef4444")
            ax2.set_facecolor("#111827")
            for spine in ax2.spines.values():
                spine.set_color("#2a3550")
            step = max(1, len(dates) // 8)
            ax1.set_xticks(range(0, len(dates), step))
            ax1.set_xticklabels([dates[i] for i in range(0, len(dates), step)],
                                rotation=30, ha="right", color="#8b97b0", fontsize=7)
            ax1.set_title("COVID-19 Cumulative Trend", color="#e8ecf4", fontsize=12, fontweight="bold")
            h1, l1 = ax1.get_legend_handles_labels()
            h2, l2 = ax2.get_legend_handles_labels()
            ax1.legend(h1 + h2, l1 + l2, fontsize=8,
                       facecolor="#0a0e1a", edgecolor="#2a3550", labelcolor="#8b97b0")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
    # Per-country table and charts
    if not countries:
        return
    st.markdown("---")
    st.markdown("##### Top 20 Countries by Total Cases")
    rows = []
    for c in countries[:20]:
        rows.append({
            "Country": c.get("country", ""), "Cases": f"{c.get('cases', 0):,}",
            "Deaths": f"{c.get('deaths', 0):,}", "Recovered": f"{c.get('recovered', 0):,}",
            "Active": f"{c.get('active', 0):,}",
            "Cases/1M": f"{c.get('casesPerOneMillion', 0):,.0f}",
            "Deaths/1M": f"{c.get('deathsPerOneMillion', 0):,.0f}",
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    # Bar chart: top 10 active
    st.markdown("##### Top 10 by Active Cases")
    top10 = sorted(countries, key=lambda x: x.get("active", 0), reverse=True)[:10]
    names = [c.get("country", "") for c in top10]
    vals = [c.get("active", 0) for c in top10]
    fig, ax = _dark_fig(figsize=(10, 4))
    bars = ax.barh(range(len(names)), vals, color="#06b6d4", alpha=0.85)
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, color="#8b97b0", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Active Cases", color="#8b97b0", fontsize=10)
    ax.set_title("Active Cases by Country", color="#e8ecf4", fontsize=12, fontweight="bold")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_width() + max(vals) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{v:,.0f}", va="center", color="#8b97b0", fontsize=8)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    # World map
    st.markdown("---")
    st.markdown("##### World COVID-19 Map")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles=None)
    folium.TileLayer(tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                     attr="CartoDB Dark", name="Dark Base").add_to(m)
    cluster = MarkerCluster().add_to(m)
    for c in countries:
        info = c.get("countryInfo", {})
        lat, lon = info.get("lat"), info.get("long")
        if lat is None or lon is None:
            continue
        name = html.escape(str(c.get("country", "")))
        popup_html = (f"<div style='min-width:160px;'><strong>{name}</strong><br/>"
                      f"Cases: {c.get('cases', 0):,}<br/>Deaths: {c.get('deaths', 0):,}<br/>"
                      f"Active: {c.get('active', 0):,}</div>")
        folium.CircleMarker(
            location=[lat, lon], radius=max(3, min(18, (c.get("cases", 0) / 1_000_000) * 2)),
            color="#ef4444", fill=True, fill_color="#ef4444", fill_opacity=0.55, weight=1,
            popup=folium.Popup(popup_html, max_width=200),
        ).add_to(cluster)
    components.html(m._repr_html_(), height=480)
    # Download CSV
    st.markdown("---")
    dl = [{"country": c.get("country", ""), "cases": c.get("cases", 0),
           "deaths": c.get("deaths", 0), "recovered": c.get("recovered", 0),
           "active": c.get("active", 0), "cases_per_million": c.get("casesPerOneMillion", 0),
           "deaths_per_million": c.get("deathsPerOneMillion", 0),
           "tests": c.get("tests", 0), "population": c.get("population", 0),
           "continent": c.get("continent", "")} for c in countries]
    df_dl = pd.DataFrame(dl)
    buf = io.StringIO()
    df_dl.to_csv(buf, index=False)
    st.download_button(f"Download Disease Data ({len(dl)} countries, CSV)",
                       data=buf.getvalue(), file_name="disease_data.csv",
                       mime="text/csv", key="gh_dis_dl")

# ── Mode 2: Health Indicators ───────────────────────────
def _render_health_indicators():
    """WHO GHO health indicator explorer with country comparison charts."""
    st.markdown("#### Health Indicators")
    st.caption("WHO Global Health Observatory data -- select an indicator and countries to compare.")
    ind_code = st.selectbox("Indicator", list(WHO_INDICATORS.keys()),
                            format_func=lambda k: WHO_INDICATORS[k]["name"], key="gh_ind_sel")
    ind_meta = WHO_INDICATORS[ind_code]
    # Build country list from REST Countries
    rest_data = fetch_rest_countries()
    country_map = {}
    for entry in rest_data:
        cname = entry.get("name", {}).get("common", "")
        cca2 = entry.get("cca2", "")
        region = entry.get("region", "")
        latlng = entry.get("latlng", [0, 0])
        if cname and cca2:
            country_map[cname] = {"cca2": cca2, "region": region,
                                  "population": entry.get("population", 0),
                                  "lat": latlng[0] if latlng else 0,
                                  "lon": latlng[1] if len(latlng) > 1 else 0}
    sorted_names = sorted(country_map.keys())
    defaults = [n for n in ["United States", "Japan", "Brazil", "Nigeria", "Germany"]
                if n in sorted_names]
    selected = st.multiselect("Countries (2-6)", sorted_names, default=defaults[:4],
                              max_selections=6, key="gh_ind_countries")
    if len(selected) < 2:
        st.warning("Please select at least 2 countries.")
        return
    if st.button("Load Indicator Data", key="gh_ind_btn", use_container_width=True):
        st.session_state["gh_ind_go"] = selected
    if "gh_ind_go" not in st.session_state:
        st.info("Select countries and click Load to view WHO indicator data.")
        return
    chosen = st.session_state["gh_ind_go"]
    with st.spinner(f"Fetching WHO data for {ind_meta['name']}..."):
        results = {}
        for cname in chosen:
            cinfo = country_map.get(cname)
            if not cinfo:
                continue
            records = fetch_who_indicator(ind_code)
            matched = [r for r in records
                       if (r.get("SpatialDim", "")[:2] == cinfo["cca2"]
                           or r.get("SpatialDim", "") == cinfo["cca2"])]
            val, year = _latest_who_value(matched)
            results[cname] = {"value": val, "year": year, "region": cinfo["region"]}
    st.markdown("---")
    st.markdown(f"##### {ind_meta['name']} ({ind_meta['unit']})")
    # Metric cards
    cols = st.columns(min(len(chosen), 3))
    for i, cname in enumerate(chosen):
        r = results.get(cname, {})
        val, year = r.get("value"), r.get("year")
        disp = f"{val:.1f}" if val is not None else "N/A"
        yr = f"({year})" if year else ""
        with cols[i % len(cols)]:
            st.metric(f"{html.escape(cname)} {yr}", disp)
    # Comparison bar chart
    labels = [html.escape(n) for n in chosen]
    values = [results.get(n, {}).get("value") or 0 for n in chosen]
    bar_colors = ["#06b6d4", "#8b5cf6", "#f59e0b", "#ec4899", "#10b981", "#ef4444"]
    fig, ax = _dark_fig(figsize=(10, 4))
    ax.bar(range(len(labels)), values,
           color=[bar_colors[i % len(bar_colors)] for i in range(len(labels))], alpha=0.85)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, color="#8b97b0", fontsize=9, rotation=20, ha="right")
    ax.set_ylabel(ind_meta["unit"], color="#8b97b0", fontsize=10)
    ax.set_title(ind_meta["name"], color="#e8ecf4", fontsize=12, fontweight="bold")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
    # Region grouping
    region_vals = {}
    for cname in chosen:
        r = results.get(cname, {})
        reg, val = r.get("region", "Unknown"), r.get("value")
        if val is not None:
            region_vals.setdefault(reg, []).append(val)
    if region_vals:
        st.markdown("##### Average by Region")
        reg_names = list(region_vals.keys())
        reg_avgs = [np.mean(region_vals[r]) for r in reg_names]
        fig2, ax2 = _dark_fig(figsize=(8, 3))
        ax2.barh(range(len(reg_names)), reg_avgs, color="#8b5cf6", alpha=0.85)
        ax2.set_yticks(range(len(reg_names)))
        ax2.set_yticklabels(reg_names, color="#8b97b0", fontsize=9)
        ax2.invert_yaxis()
        ax2.set_xlabel(ind_meta["unit"], color="#8b97b0", fontsize=10)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)
    # Data table + download
    st.markdown("---")
    table_rows = []
    for cname in chosen:
        r = results.get(cname, {})
        table_rows.append({"Country": cname,
                           "Value": f"{r['value']:.1f}" if r.get("value") is not None else "N/A",
                           "Unit": ind_meta["unit"], "Year": r.get("year", ""),
                           "Region": r.get("region", "")})
    df_table = pd.DataFrame(table_rows)
    st.dataframe(df_table, width="stretch", hide_index=True)
    buf = io.StringIO()
    df_table.to_csv(buf, index=False)
    st.download_button("Download Indicator Data (CSV)", data=buf.getvalue(),
                       file_name="who_indicator_data.csv", mime="text/csv", key="gh_ind_dl")

# ── Mode 3: Healthcare Map ──────────────────────────────
def _render_healthcare_map():
    """Map hospitals, clinics, pharmacies near a location via Overpass API."""
    st.markdown("#### Healthcare Map")
    st.caption("Find hospitals, clinics, and pharmacies from OpenStreetMap.")
    preset = st.selectbox("Location Preset", ["Custom"] + list(CITY_PRESETS.keys()),
                          key="gh_map_preset")
    col1, col2, col3 = st.columns(3)
    default_lat = CITY_PRESETS.get(preset, {}).get("lat", 40.7)
    default_lon = CITY_PRESETS.get(preset, {}).get("lon", -74.0)
    with col1:
        lat = st.number_input("Latitude", value=default_lat, format="%.4f",
                              min_value=-90.0, max_value=90.0, key="gh_map_lat")
    with col2:
        lon = st.number_input("Longitude", value=default_lon, format="%.4f",
                              min_value=-180.0, max_value=180.0, key="gh_map_lon")
    with col3:
        radius = st.slider("Radius (m)", 1000, 20000, 5000, step=1000, key="gh_map_rad")
    if preset != "Custom" and preset in CITY_PRESETS:
        lat, lon = CITY_PRESETS[preset]["lat"], CITY_PRESETS[preset]["lon"]
    if st.button("Find Healthcare Facilities", key="gh_map_btn", use_container_width=True):
        st.session_state["gh_map_params"] = {"lat": lat, "lon": lon, "radius": radius}
    if "gh_map_params" not in st.session_state:
        st.info("Select a location and click Find to map nearby healthcare facilities.")
        return
    p = st.session_state["gh_map_params"]
    with st.spinner("Querying OpenStreetMap for healthcare facilities..."):
        data = fetch_healthcare_overpass(p["lat"], p["lon"], p["radius"])
    if data.get("_error"):
        st.error(f"Overpass error: {data['_error']}")
        return
    elements = data.get("elements", [])
    if not elements:
        st.warning("No healthcare facilities found. Try increasing the radius.")
        return
    # Classify elements
    buckets = {"hospital": [], "clinic": [], "pharmacy": []}
    for el in elements:
        tags = el.get("tags", {})
        amenity = tags.get("amenity", "")
        elat = el.get("lat") or el.get("center", {}).get("lat")
        elon = el.get("lon") or el.get("center", {}).get("lon")
        if elat is None or elon is None:
            continue
        name = tags.get("name", tags.get("name:en", "Unnamed"))
        if amenity in buckets:
            buckets[amenity].append({"lat": elat, "lon": elon, "name": name, "tags": tags})
    # Stats
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Hospitals", len(buckets["hospital"]))
    with c2: st.metric("Clinics", len(buckets["clinic"]))
    with c3: st.metric("Pharmacies", len(buckets["pharmacy"]))
    total = sum(len(v) for v in buckets.values())
    with c4: st.metric("Total", total)
    # Folium map with MarkerCluster
    st.markdown("---")
    st.markdown("##### Healthcare Facilities Map")
    st.markdown(
        '<div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:0.75rem;">'
        '<span style="color:#ef4444;font-size:0.8rem;">&#9679; Hospitals</span>'
        '<span style="color:#f59e0b;font-size:0.8rem;">&#9679; Clinics</span>'
        '<span style="color:#10b981;font-size:0.8rem;">&#9679; Pharmacies</span>'
        '</div>', unsafe_allow_html=True)
    m = folium.Map(location=[p["lat"], p["lon"]], zoom_start=13, tiles=None)
    folium.TileLayer(tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                     attr="CartoDB Dark", name="Dark Base").add_to(m)
    folium.Circle(location=[p["lat"], p["lon"]], radius=p["radius"],
                  color="#06b6d4", fill=True, fill_opacity=0.03, weight=1).add_to(m)
    cluster = MarkerCluster().add_to(m)
    for amenity_type, items in buckets.items():
        style = FACILITY_STYLES[amenity_type]
        for item in items:
            safe_name = html.escape(str(item["name"]))
            safe_addr = html.escape(str(item["tags"].get("addr:street", "")))
            popup_html = (f"<div style='max-width:200px;'><strong>{safe_name}</strong><br/>"
                          f"<span style='font-size:0.8rem;color:{style['color']};'>"
                          f"{style['label']}</span><br/>"
                          f"<span style='font-size:0.75rem;'>{safe_addr}</span></div>")
            folium.CircleMarker(
                location=[item["lat"], item["lon"]], radius=style["radius"],
                color=style["color"], fill=True, fill_color=style["color"],
                fill_opacity=0.7, weight=1,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(cluster)
    components.html(m._repr_html_(), height=500)
    # Data table and download
    st.markdown("---")
    all_fac = []
    for amenity_type, items in buckets.items():
        style = FACILITY_STYLES[amenity_type]
        for item in items:
            all_fac.append({"Name": item["name"], "Type": style["label"],
                            "Latitude": round(item["lat"], 5),
                            "Longitude": round(item["lon"], 5),
                            "Address": item["tags"].get("addr:street", ""),
                            "Phone": item["tags"].get("phone", "")})
    if all_fac:
        df_fac = pd.DataFrame(all_fac)
        with st.expander(f"Facility Data ({len(df_fac)} facilities)", expanded=False):
            st.dataframe(df_fac, width="stretch", hide_index=True)
        buf = io.StringIO()
        df_fac.to_csv(buf, index=False)
        st.download_button(f"Download {len(df_fac)} Facilities (CSV)", data=buf.getvalue(),
                           file_name="healthcare_facilities.csv", mime="text/csv", key="gh_map_dl")

# ── Main render ──────────────────────────────────────────
def render_global_health_tab():
    """Main entry point for the Global Health Explorer tab."""
    st.markdown(
        '<div class="tab-header pink">'
        "<h4>Global Health Explorer</h4>"
        "<p>Disease tracking, WHO health indicators, and healthcare infrastructure mapping "
        "&mdash; powered by free open APIs.</p>"
        "</div>", unsafe_allow_html=True)
    mode = st.radio("Mode", ["Disease Tracker", "Health Indicators", "Healthcare Map"],
                    horizontal=True, key="gh_mode")
    st.markdown("---")
    if mode == "Disease Tracker":
        _render_disease_tracker()
    elif mode == "Health Indicators":
        _render_health_indicators()
    elif mode == "Healthcare Map":
        _render_healthcare_map()
