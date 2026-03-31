"""
World Demographics & Culture Explorer for TerraScout AI.
Population distribution, languages, religions, and cultural data worldwide.
Uses REST Countries, World Bank, and Overpass APIs -- all free, no API key.
"""

import io
import logging
import math
import requests
import streamlit as st
import pandas as pd
from html import escape

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.overpass_client import query_overpass

logger = logging.getLogger(__name__)

# =====================================================================
# API ENDPOINTS
# =====================================================================
REST_COUNTRIES_API = "https://restcountries.com/v3.1"
WORLD_BANK_API = "https://api.worldbank.org/v2"

REST_FIELDS = "name,population,languages,region,subregion,capital,area,borders,currencies,flags,latlng,cca2,cca3,timezones"

# =====================================================================
# WORLD BANK INDICATORS
# =====================================================================
WB_INDICATORS = {
    "Population": "SP.POP.TOTL",
    "Pop. Density (per km2)": "EN.POP.DNST",
    "Urban Pop. (%)": "SP.URB.TOTL.IN.ZS",
    "Life Expectancy": "SP.DYN.LE00.IN",
    "GDP per Capita (USD)": "NY.GDP.PCAP.CD",
    "Literacy Rate (%)": "SE.ADT.LITR.ZS",
}

# =====================================================================
# RELIGION COLORS & CITY PRESETS
# =====================================================================
RELIGION_COLORS = {
    "christian": "#3b82f6",
    "muslim": "#10b981",
    "jewish": "#f59e0b",
    "buddhist": "#f97316",
    "hindu": "#ef4444",
    "shinto": "#ec4899",
    "sikh": "#8b5cf6",
    "taoist": "#06b6d4",
}

CULTURE_TYPE_COLORS = {
    "museum": "#8b5cf6",
    "theatre": "#ec4899",
    "place_of_worship": "#f59e0b",
    "library": "#10b981",
    "historic": "#06b6d4",
}

CITY_PRESETS = {
    "Rome, Italy": (41.90, 12.50),
    "Paris, France": (48.86, 2.35),
    "London, UK": (51.51, -0.13),
    "Athens, Greece": (37.97, 23.73),
    "Istanbul, Turkey": (41.01, 28.98),
    "Jerusalem, Israel": (31.77, 35.23),
    "Cairo, Egypt": (30.04, 31.24),
    "Varanasi, India": (25.32, 83.01),
    "Kyoto, Japan": (35.01, 135.77),
    "Beijing, China": (39.91, 116.39),
    "Mexico City, Mexico": (19.43, -99.13),
    "Cusco, Peru": (-13.52, -71.97),
    "New York, USA": (40.71, -74.01),
    "Moscow, Russia": (55.76, 37.62),
    "Barcelona, Spain": (41.39, 2.17),
    "Berlin, Germany": (52.52, 13.40),
    "Vienna, Austria": (48.21, 16.37),
    "Prague, Czech Republic": (50.08, 14.44),
    "Florence, Italy": (43.77, 11.25),
    "Venice, Italy": (45.44, 12.32),
    "Marrakech, Morocco": (31.63, -8.01),
    "Bangkok, Thailand": (13.76, 100.50),
    "Fez, Morocco": (34.03, -5.00),
    "Havana, Cuba": (23.11, -82.37),
    "Buenos Aires, Argentina": (-34.60, -58.38),
    "Lima, Peru": (-12.05, -77.04),
    "Tokyo, Japan": (35.68, 139.69),
    "Seoul, South Korea": (37.57, 126.98),
    "Dubai, UAE": (25.20, 55.27),
    "Addis Ababa, Ethiopia": (9.02, 38.75),
}

REGIONS = ["Africa", "Americas", "Asia", "Europe", "Oceania"]

REGION_COLORS = {
    "Africa": "#f59e0b",
    "Americas": "#3b82f6",
    "Asia": "#ef4444",
    "Europe": "#10b981",
    "Oceania": "#8b5cf6",
}


# =====================================================================
# DATA FETCHING FUNCTIONS
# =====================================================================
@st.cache_data(ttl=600)
def fetch_all_countries() -> list:
    """Fetch all countries with core fields from REST Countries."""
    try:
        resp = requests.get(
            f"{REST_COUNTRIES_API}/all",
            params={"fields": REST_FIELDS},
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("REST Countries fetch failed: %s", e)
        return []


@st.cache_data(ttl=600)
def fetch_countries_by_region(region: str) -> list:
    """Fetch countries in a specific region."""
    try:
        resp = requests.get(
            f"{REST_COUNTRIES_API}/region/{region}",
            params={"fields": REST_FIELDS},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("REST Countries region fetch failed: %s", e)
        return []


@st.cache_data(ttl=600)
def fetch_country_by_name(name: str) -> list:
    """Search country by name."""
    try:
        resp = requests.get(
            f"{REST_COUNTRIES_API}/name/{name}",
            params={"fields": REST_FIELDS},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error("Country search failed: %s", e)
        return []


@st.cache_data(ttl=900)
def fetch_wb_indicator(country_code: str, indicator: str) -> float | None:
    """Fetch the most recent value of a World Bank indicator for a country."""
    try:
        url = f"{WORLD_BANK_API}/country/{country_code}/indicator/{indicator}"
        resp = requests.get(url, params={"format": "json", "date": "2018:2024", "per_page": 10}, timeout=12)
        resp.raise_for_status()
        data = resp.json()
        if len(data) < 2 or not data[1]:
            return None
        for entry in data[1]:
            if entry.get("value") is not None:
                return entry["value"]
        return None
    except Exception:
        return None


def _build_worship_query(lat: float, lon: float, radius_km: float = 5) -> str:
    """Overpass query for places of worship."""
    return f"""
[out:json][timeout:30];
(
  node["amenity"="place_of_worship"](around:{radius_km * 1000},{lat},{lon});
  way["amenity"="place_of_worship"](around:{radius_km * 1000},{lat},{lon});
);
out center body;
"""


def _build_culture_query(lat: float, lon: float, radius_km: float = 5) -> str:
    """Overpass query for cultural heritage sites."""
    return f"""
[out:json][timeout:60];
(
  node["tourism"="museum"](around:{radius_km * 1000},{lat},{lon});
  node["amenity"="theatre"](around:{radius_km * 1000},{lat},{lon});
  node["amenity"="library"](around:{radius_km * 1000},{lat},{lon});
  node["historic"](around:{radius_km * 1000},{lat},{lon});
  way["tourism"="museum"](around:{radius_km * 1000},{lat},{lon});
  way["amenity"="theatre"](around:{radius_km * 1000},{lat},{lon});
  way["historic"](around:{radius_km * 1000},{lat},{lon});
);
out center body;
"""


def _extract_elements(data: dict) -> list:
    """Extract elements with coordinates from Overpass response."""
    if not data or "_error" in data:
        return []
    elements = data.get("elements", [])
    features = []
    for el in elements:
        tags = el.get("tags", {})
        if not tags:
            continue
        lat = el.get("lat") or (el.get("center", {}) or {}).get("lat")
        lon = el.get("lon") or (el.get("center", {}) or {}).get("lon")
        if lat is None or lon is None:
            continue
        features.append({"lat": lat, "lon": lon, "tags": tags, "osm_id": el.get("id")})
    return features


def _classify_worship(tags: dict) -> str:
    """Classify a place of worship by religion tag."""
    return tags.get("religion", "unknown").lower()


def _classify_culture(tags: dict) -> tuple:
    """Classify a cultural site. Returns (type, color)."""
    if tags.get("tourism") == "museum":
        return "museum", CULTURE_TYPE_COLORS["museum"]
    if tags.get("amenity") == "theatre":
        return "theatre", CULTURE_TYPE_COLORS["theatre"]
    if tags.get("amenity") == "library":
        return "library", CULTURE_TYPE_COLORS["library"]
    if tags.get("amenity") == "place_of_worship":
        return "place_of_worship", CULTURE_TYPE_COLORS["place_of_worship"]
    if tags.get("historic"):
        return "historic", CULTURE_TYPE_COLORS["historic"]
    return "other", "#8b97b0"


def _get_country_name(c: dict) -> str:
    """Extract common name from REST Countries entry."""
    return c.get("name", {}).get("common", "Unknown")


def _fmt_pop(val) -> str:
    """Format a population number with commas or magnitude."""
    if val is None:
        return "N/A"
    if isinstance(val, str):
        return val
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f}B"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val / 1_000:.1f}K"
    return f"{val:,.0f}"


def _dark_fig(figsize=(8, 4)):
    """Create a matplotlib figure with dark theme."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")
    ax.tick_params(colors="#8b97b0", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#2a3550")
    ax.spines["bottom"].set_color("#2a3550")
    ax.grid(axis="y", color="#2a3550", linewidth=0.5, alpha=0.5)
    ax.xaxis.label.set_color("#8b97b0")
    ax.yaxis.label.set_color("#8b97b0")
    ax.title.set_color("#e8ecf4")
    return fig, ax


def _render_folium_map(m, height: int = 480):
    """Render folium map via streamlit_folium or components.html fallback."""
    try:
        from streamlit_folium import st_folium
        st_folium(m, width=None, height=height, returned_objects=[], key="wdemo_folium_map")
    except ImportError:
        import streamlit.components.v1 as components
        components.html(m._repr_html_(), height=height)


# =====================================================================
# MODE 1 -- Country Explorer
# =====================================================================
def _render_country_explorer():
    import folium

    st.markdown("#### Country Explorer")
    all_countries = fetch_all_countries()
    if not all_countries:
        st.warning("Could not fetch country data from REST Countries API.")
        return

    country_names = sorted([_get_country_name(c) for c in all_countries])
    col_s, col_n = st.columns([2, 1])
    with col_s:
        selected = st.selectbox("Select a country", country_names, index=country_names.index("Italy") if "Italy" in country_names else 0, key="dem_country_sel")
    with col_n:
        search_q = st.text_input("Or search by name", key="dem_country_search")

    if search_q:
        matches = fetch_country_by_name(search_q)
        if matches:
            country = matches[0]
        else:
            st.warning(f"No country found for '{search_q}'.")
            return
    else:
        country = next((c for c in all_countries if _get_country_name(c) == selected), None)
        if not country:
            st.warning("Country not found.")
            return

    name = _get_country_name(country)
    official = country.get("name", {}).get("official", name)
    pop = country.get("population", 0)
    area = country.get("area", 0)
    density = pop / area if area else 0
    capital_list = country.get("capital", [])
    capital = ", ".join(capital_list) if capital_list else "N/A"
    region = country.get("region", "N/A")
    subregion = country.get("subregion", "N/A")
    latlng = country.get("latlng", [0, 0])
    languages = country.get("languages", {})
    currencies = country.get("currencies", {})
    borders = country.get("borders", [])
    timezones = country.get("timezones", [])
    flag_png = country.get("flags", {}).get("png", "")
    cca2 = country.get("cca2", "")
    cca3 = country.get("cca3", "")

    # Flag and title
    flag_html = f'<img src="{flag_png}" style="height:32px;border-radius:4px;vertical-align:middle;margin-right:10px;"/>' if flag_png else ""
    st.markdown(f"""
    <div style="display:flex;align-items:center;margin-bottom:0.5rem;">
        {flag_html}
        <span style="color:#e8ecf4;font-size:1.3rem;font-weight:700;">{escape(name)}</span>
        <span style="color:#5a6580;font-size:0.85rem;margin-left:10px;">({escape(official)})</span>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Population", _fmt_pop(pop))
    with m2:
        st.metric("Area (km2)", f"{area:,.0f}" if area else "N/A")
    with m3:
        st.metric("Density", f"{density:,.1f}/km2")
    with m4:
        st.metric("Capital", capital)

    m5, m6, m7, m8 = st.columns(4)
    with m5:
        st.metric("Region", region)
    with m6:
        st.metric("Subregion", subregion)
    with m7:
        lang_str = ", ".join(languages.values()) if languages else "N/A"
        st.metric("Languages", lang_str[:30] + ("..." if len(lang_str) > 30 else ""))
    with m8:
        curr_names = [v.get("name", k) for k, v in currencies.items()] if currencies else ["N/A"]
        st.metric("Currency", ", ".join(curr_names)[:30])

    # Extra info
    col_tz, col_bd = st.columns(2)
    with col_tz:
        st.markdown(f"**Timezones:** {', '.join(timezones) if timezones else 'N/A'}")
    with col_bd:
        st.markdown(f"**Border Codes:** {', '.join(borders) if borders else 'None (island/isolated)'}")

    if languages:
        st.markdown("**All Languages:** " + ", ".join(f"`{v}`" for v in languages.values()))

    # Small map
    lat_c = latlng[0] if len(latlng) > 0 else 0
    lon_c = latlng[1] if len(latlng) > 1 else 0
    zoom = 5 if area and area > 100000 else 7
    m = folium.Map(location=[lat_c, lon_c], zoom_start=zoom, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)
    folium.Marker(
        [lat_c, lon_c],
        popup=f"<b>{escape(name)}</b><br/>Pop: {_fmt_pop(pop)}",
        icon=folium.Icon(color="lightblue", icon="info-sign"),
    ).add_to(m)
    _render_folium_map(m, height=350)


# =====================================================================
# MODE 2 -- Population & Statistics
# =====================================================================
def _render_population_stats():
    st.markdown("#### Population & Statistics Comparison")

    all_countries = fetch_all_countries()
    if not all_countries:
        st.warning("Could not load country data.")
        return

    country_map = {_get_country_name(c): c for c in all_countries}
    names_sorted = sorted(country_map.keys())

    defaults = []
    for d in ["United States", "China", "India", "Brazil", "Germany", "Nigeria"]:
        if d in names_sorted:
            defaults.append(d)
    defaults = defaults[:6]

    selected = st.multiselect(
        "Compare countries (up to 6)",
        names_sorted, default=defaults, max_selections=6,
        key="dem_pop_select",
    )

    if not selected:
        st.info("Select at least one country to compare.")
        return

    if st.button("Fetch World Bank Statistics", key="dem_pop_fetch", width="stretch"):
        st.session_state.dem_pop_countries = selected

    if "dem_pop_countries" not in st.session_state:
        st.info("Select countries and click Fetch to load World Bank statistics.")
        return

    countries_to_show = st.session_state.dem_pop_countries

    # Gather data
    rows = []
    with st.spinner("Fetching World Bank indicators..."):
        for cname in countries_to_show:
            c = country_map.get(cname)
            if not c:
                continue
            code = c.get("cca2", "")
            if not code:
                continue
            row = {"Country": cname, "Code": code}
            row["Population (REST)"] = c.get("population", 0)
            for label, ind in WB_INDICATORS.items():
                val = fetch_wb_indicator(code, ind)
                row[label] = val
            rows.append(row)

    if not rows:
        st.warning("No data could be fetched.")
        return

    df = pd.DataFrame(rows)

    # Metrics overview
    st.markdown("##### Key Metrics")
    cols = st.columns(len(rows))
    for i, row in enumerate(rows):
        with cols[i]:
            st.markdown(f"**{row['Country']}**")
            st.metric("Population", _fmt_pop(row.get("Population")))
            le = row.get("Life Expectancy")
            st.metric("Life Expect.", f"{le:.1f} yr" if le else "N/A")
            gdp = row.get("GDP per Capita (USD)")
            st.metric("GDP/Cap", f"${gdp:,.0f}" if gdp else "N/A")

    # Bar charts
    chart_indicators = ["Population", "Pop. Density (per km2)", "Urban Pop. (%)", "Life Expectancy", "GDP per Capita (USD)"]
    for ind_label in chart_indicators:
        values = [r.get(ind_label) for r in rows]
        labels = [r["Country"] for r in rows]
        if all(v is None for v in values):
            continue
        clean_vals = [v if v is not None else 0 for v in values]

        fig, ax = _dark_fig(figsize=(7, 3))
        colors = ["#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#ec4899", "#ef4444"]
        bars = ax.barh(labels, clean_vals, color=[colors[i % len(colors)] for i in range(len(labels))], edgecolor="#2a3550", linewidth=0.5)
        ax.set_title(ind_label, fontsize=10, pad=8)
        for bar, val in zip(bars, clean_vals):
            if val > 0:
                fmt = _fmt_pop(val) if "Pop" in ind_label and "%" not in ind_label else (f"{val:.1f}" if val < 1000 else f"{val:,.0f}")
                ax.text(bar.get_width(), bar.get_y() + bar.get_height() / 2, f"  {fmt}", va="center", color="#e8ecf4", fontsize=7)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # Data table
    st.markdown("##### Full Data Table")
    st.dataframe(df, width="stretch", hide_index=True)

    # CSV download
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        "Download Comparison (CSV)", data=csv_buf.getvalue(),
        file_name="country_comparison.csv", mime="text/csv", key="dem_pop_dl",
    )


# =====================================================================
# MODE 3 -- Languages & Religions Map
# =====================================================================
def _render_languages_religions():
    import folium

    st.markdown("#### Languages & Religions")
    mode = st.radio("View", ["Regional Language Map", "City Religion Breakdown"], horizontal=True, key="dem_lr_mode")

    if mode == "Regional Language Map":
        region = st.selectbox("Region", REGIONS, key="dem_lr_region")
        if st.button("Load Region", key="dem_lr_load", width="stretch"):
            st.session_state.dem_lr_data = {"region": region}

        if "dem_lr_data" not in st.session_state:
            st.info("Select a region and click Load to see language distribution.")
            return

        with st.spinner("Fetching region data..."):
            countries = fetch_countries_by_region(st.session_state.dem_lr_data["region"])

        if not countries:
            st.warning("No data available.")
            return

        st.metric("Countries in Region", len(countries))

        # Language analysis
        lang_count = {}
        country_langs = []
        for c in countries:
            langs = c.get("languages", {})
            cname = _get_country_name(c)
            lang_list = list(langs.values()) if langs else ["N/A"]
            country_langs.append({"Country": cname, "Languages": ", ".join(lang_list), "Count": len(lang_list), "Population": c.get("population", 0)})
            for lang in lang_list:
                lang_count[lang] = lang_count.get(lang, 0) + 1

        top_langs = sorted(lang_count.items(), key=lambda x: -x[1])[:15]

        # Bar chart of top languages
        if top_langs:
            fig, ax = _dark_fig(figsize=(7, 4))
            lang_names = [l[0] for l in top_langs]
            lang_vals = [l[1] for l in top_langs]
            colors = ["#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#ec4899", "#ef4444", "#3b82f6", "#f97316", "#14b8a6", "#a855f7", "#64748b", "#38bdf8", "#22c55e", "#e879f9", "#facc15"]
            ax.barh(lang_names[::-1], lang_vals[::-1], color=[colors[i % len(colors)] for i in range(len(lang_names))][::-1], edgecolor="#2a3550", linewidth=0.5)
            ax.set_title(f"Most Common Languages in {st.session_state.dem_lr_data['region']}", fontsize=10, pad=8)
            ax.set_xlabel("Number of Countries")
            fig.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

        # Map with markers
        m = folium.Map(location=[20, 0], zoom_start=2, tiles=None)
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr="CartoDB Dark", name="Dark Base",
        ).add_to(m)

        lang_color_map = {}
        palette = ["#06b6d4", "#8b5cf6", "#10b981", "#f59e0b", "#ec4899", "#ef4444", "#3b82f6", "#f97316"]
        for i, (lang, _) in enumerate(top_langs[:8]):
            lang_color_map[lang] = palette[i % len(palette)]

        for c in countries:
            latlng = c.get("latlng", [])
            if len(latlng) < 2:
                continue
            cname = _get_country_name(c)
            langs = list((c.get("languages") or {}).values())
            primary = langs[0] if langs else "N/A"
            color = lang_color_map.get(primary, "#8b97b0")
            popup = f"<b>{escape(cname)}</b><br/>Languages: {escape(', '.join(langs[:5]))}<br/>Pop: {_fmt_pop(c.get('population', 0))}"
            folium.CircleMarker(
                location=[latlng[0], latlng[1]], radius=max(4, min(15, math.sqrt(c.get("population", 0) / 1_000_000))),
                color=color, fill=True, fill_color=color, fill_opacity=0.7, weight=1,
                popup=folium.Popup(popup, max_width=250),
            ).add_to(m)

        _render_folium_map(m, height=450)

        # Table
        df_cl = pd.DataFrame(country_langs).sort_values("Population", ascending=False)
        st.dataframe(df_cl, width="stretch", hide_index=True)

    else:
        # City religion breakdown
        col_city, col_rad = st.columns([2, 1])
        with col_city:
            city = st.selectbox("City Preset", list(CITY_PRESETS.keys()), key="dem_rel_city")
        with col_rad:
            radius = st.slider("Radius (km)", 1, 15, 5, key="dem_rel_radius")

        lat, lon = CITY_PRESETS[city]

        if st.button("Analyze Religions", key="dem_rel_fetch", width="stretch"):
            st.session_state.dem_rel_params = {"city": city, "lat": lat, "lon": lon, "radius": radius}

        if "dem_rel_params" not in st.session_state:
            st.info("Select a city and click Analyze to see religion breakdown from places of worship.")
            return

        p = st.session_state.dem_rel_params
        with st.spinner(f"Querying places of worship near {p['city']}..."):
            query = _build_worship_query(p["lat"], p["lon"], p["radius"])
            raw = query_overpass(query)

        elements = _extract_elements(raw)
        if not elements:
            st.warning("No places of worship found. Try a larger radius or different city.")
            return

        # Classify
        religion_counts = {}
        markers = []
        for el in elements:
            rel = _classify_worship(el["tags"])
            religion_counts[rel] = religion_counts.get(rel, 0) + 1
            name = el["tags"].get("name", el["tags"].get("name:en", "Unnamed"))
            color = RELIGION_COLORS.get(rel, "#8b97b0")
            markers.append({"lat": el["lat"], "lon": el["lon"], "name": name, "religion": rel, "color": color})

        st.metric("Total Places of Worship", len(elements))

        # Pie chart
        sorted_rels = sorted(religion_counts.items(), key=lambda x: -x[1])
        fig, ax = _dark_fig(figsize=(5, 5))
        labels = [r[0].title() for r in sorted_rels]
        sizes = [r[1] for r in sorted_rels]
        pie_colors = [RELIGION_COLORS.get(r[0], "#8b97b0") for r in sorted_rels]
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, colors=pie_colors, autopct="%1.1f%%", startangle=140,
            textprops={"color": "#e8ecf4", "fontsize": 8},
        )
        for t in autotexts:
            t.set_fontsize(7)
            t.set_color("#e8ecf4")
        ax.set_title(f"Religion Distribution: {p['city']}", fontsize=10, pad=12)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Map
        m = folium.Map(location=[p["lat"], p["lon"]], zoom_start=13, tiles=None)
        folium.TileLayer(
            tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
            attr="CartoDB Dark", name="Dark Base",
        ).add_to(m)
        for mk in markers:
            popup_html = f"<b>{escape(mk['name'])}</b><br/>Religion: {escape(mk['religion'].title())}"
            folium.CircleMarker(
                location=[mk["lat"], mk["lon"]], radius=5,
                color=mk["color"], fill=True, fill_color=mk["color"], fill_opacity=0.75, weight=1,
                popup=folium.Popup(popup_html, max_width=220),
            ).add_to(m)
        _render_folium_map(m, height=450)

        # Table
        df_rel = pd.DataFrame(sorted_rels, columns=["Religion", "Count"])
        df_rel["Pct"] = (df_rel["Count"] / df_rel["Count"].sum() * 100).round(1)
        st.dataframe(df_rel, width="stretch", hide_index=True)


# =====================================================================
# MODE 4 -- Cultural Heritage Sites
# =====================================================================
def _render_cultural_heritage():
    import folium

    st.markdown("#### Cultural Heritage Sites")

    col_city, col_rad = st.columns([2, 1])
    with col_city:
        city = st.selectbox("City", list(CITY_PRESETS.keys()), key="dem_cult_city")
    with col_rad:
        radius = st.slider("Radius (km)", 1, 15, 5, key="dem_cult_radius")

    lat, lon = CITY_PRESETS[city]

    if st.button("Find Cultural Sites", key="dem_cult_fetch", width="stretch"):
        st.session_state.dem_cult_params = {"city": city, "lat": lat, "lon": lon, "radius": radius}

    if "dem_cult_params" not in st.session_state:
        st.info("Select a city and click Find to discover museums, theatres, libraries, and historic sites.")
        return

    p = st.session_state.dem_cult_params
    with st.spinner(f"Querying cultural sites near {p['city']}..."):
        query = _build_culture_query(p["lat"], p["lon"], p["radius"])
        raw = query_overpass(query)

    elements = _extract_elements(raw)
    if not elements:
        st.warning("No cultural sites found. Try a larger radius.")
        return

    # Classify and build features
    type_counts = {}
    features = []
    for el in elements:
        site_type, color = _classify_culture(el["tags"])
        type_counts[site_type] = type_counts.get(site_type, 0) + 1
        name = el["tags"].get("name", el["tags"].get("name:en", "Unnamed"))
        features.append({
            "name": name,
            "type": site_type,
            "color": color,
            "lat": el["lat"],
            "lon": el["lon"],
            "wikipedia": el["tags"].get("wikipedia", ""),
            "wikidata": el["tags"].get("wikidata", ""),
            "description": el["tags"].get("description", el["tags"].get("description:en", "")),
            "osm_id": el["osm_id"],
        })

    # Stats
    st.metric("Total Cultural Sites", len(features))
    stat_cols = st.columns(min(len(type_counts), 5))
    type_labels = {"museum": "Museums", "theatre": "Theatres", "library": "Libraries", "historic": "Historic Sites", "place_of_worship": "Places of Worship", "other": "Other"}
    for i, (t, cnt) in enumerate(sorted(type_counts.items(), key=lambda x: -x[1])):
        if i >= 5:
            break
        with stat_cols[i]:
            st.metric(type_labels.get(t, t.title()), cnt)

    # Map
    m = folium.Map(location=[p["lat"], p["lon"]], zoom_start=13, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    for f in features:
        desc = f"<b>{escape(f['name'])}</b><br/>Type: {escape(f['type'].title())}"
        if f["description"]:
            desc += f"<br/><em>{escape(f['description'][:120])}</em>"
        if f["wikipedia"]:
            wiki_url = f"https://en.wikipedia.org/wiki/{f['wikipedia'].split(':',1)[-1]}"
            desc += f'<br/><a href="{wiki_url}" target="_blank">Wikipedia</a>'
        folium.CircleMarker(
            location=[f["lat"], f["lon"]], radius=5,
            color=f["color"], fill=True, fill_color=f["color"], fill_opacity=0.75, weight=1,
            popup=folium.Popup(desc, max_width=250),
        ).add_to(m)

    # Legend
    legend_items = "".join(
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{c};margin-right:4px;"></span>{escape(type_labels.get(t, t.title()))}&nbsp;&nbsp;'
        for t, c in CULTURE_TYPE_COLORS.items()
    )
    st.markdown(f'<div style="margin-bottom:0.5rem;font-size:0.8rem;color:#8b97b0;">{legend_items}</div>', unsafe_allow_html=True)

    _render_folium_map(m, height=480)

    # Data table
    st.markdown("##### Site Details")
    df = pd.DataFrame([{
        "Name": f["name"], "Type": f["type"].title(), "Lat": round(f["lat"], 5),
        "Lon": round(f["lon"], 5), "Wikipedia": f["wikipedia"], "Wikidata": f["wikidata"],
    } for f in features]).sort_values("Type")
    st.dataframe(df, width="stretch", hide_index=True)

    # Download
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    st.download_button(
        f"Download {len(features)} Sites (CSV)", data=csv_buf.getvalue(),
        file_name=f"cultural_sites_{p['city'].split(',')[0].lower().replace(' ','_')}.csv",
        mime="text/csv", key="dem_cult_dl",
    )


# =====================================================================
# MODE 5 -- Regional Comparison
# =====================================================================
def _render_regional_comparison():
    import folium

    st.markdown("#### Regional Comparison")

    if st.button("Load All Regions", key="dem_reg_load", width="stretch"):
        st.session_state.dem_reg_loaded = True

    if not st.session_state.get("dem_reg_loaded"):
        st.info("Click Load to aggregate statistics for all world regions.")
        return

    with st.spinner("Fetching data for all regions..."):
        region_data = {}
        for region in REGIONS:
            countries = fetch_countries_by_region(region)
            if not countries:
                continue
            total_pop = sum(c.get("population", 0) for c in countries)
            total_area = sum(c.get("area", 0) for c in countries if c.get("area"))
            avg_density = total_pop / total_area if total_area else 0
            all_langs = set()
            for c in countries:
                for lang in (c.get("languages") or {}).values():
                    all_langs.add(lang)
            region_data[region] = {
                "Countries": len(countries),
                "Total Population": total_pop,
                "Total Area (km2)": total_area,
                "Avg Density": avg_density,
                "Languages": len(all_langs),
            }

    if not region_data:
        st.warning("Could not load region data.")
        return

    # Metric cards
    for region in REGIONS:
        if region not in region_data:
            continue
        rd = region_data[region]
        color = REGION_COLORS.get(region, "#8b97b0")
        st.markdown(f"""
        <div style="border-left:3px solid {color};padding-left:12px;margin-bottom:0.75rem;">
            <span style="color:{color};font-weight:700;font-size:1rem;">{escape(region)}</span>
        </div>
        """, unsafe_allow_html=True)
        mc = st.columns(5)
        with mc[0]:
            st.metric("Countries", rd["Countries"])
        with mc[1]:
            st.metric("Population", _fmt_pop(rd["Total Population"]))
        with mc[2]:
            st.metric("Area (km2)", _fmt_pop(rd["Total Area (km2)"]))
        with mc[3]:
            st.metric("Avg Density", f"{rd['Avg Density']:.1f}/km2")
        with mc[4]:
            st.metric("Languages", rd["Languages"])

    # Bar charts
    regions_list = [r for r in REGIONS if r in region_data]
    colors = [REGION_COLORS.get(r, "#8b97b0") for r in regions_list]

    chart_fields = [
        ("Total Population", "Total Population by Region"),
        ("Countries", "Number of Countries by Region"),
        ("Languages", "Distinct Languages by Region"),
        ("Avg Density", "Average Population Density by Region"),
    ]
    for field, title in chart_fields:
        vals = [region_data[r][field] for r in regions_list]
        fig, ax = _dark_fig(figsize=(7, 3))
        ax.barh(regions_list, vals, color=colors, edgecolor="#2a3550", linewidth=0.5)
        ax.set_title(title, fontsize=10, pad=8)
        for i, (v, r) in enumerate(zip(vals, regions_list)):
            fmt = _fmt_pop(v) if field == "Total Population" else (f"{v:.1f}" if isinstance(v, float) else str(v))
            ax.text(v, i, f"  {fmt}", va="center", color="#e8ecf4", fontsize=7)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    # World map
    st.markdown("##### World Regions Map")
    m = folium.Map(location=[20, 0], zoom_start=2, tiles=None)
    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark", name="Dark Base",
    ).add_to(m)

    all_countries = fetch_all_countries()
    for c in all_countries:
        latlng = c.get("latlng", [])
        if len(latlng) < 2:
            continue
        region = c.get("region", "")
        color = REGION_COLORS.get(region, "#8b97b0")
        cname = _get_country_name(c)
        pop = c.get("population", 0)
        radius = max(3, min(14, math.sqrt(pop / 500_000)))
        popup_text = f"<b>{escape(cname)}</b><br/>Region: {escape(region)}<br/>Pop: {_fmt_pop(pop)}"
        folium.CircleMarker(
            location=[latlng[0], latlng[1]], radius=radius,
            color=color, fill=True, fill_color=color, fill_opacity=0.65, weight=1,
            popup=folium.Popup(popup_text, max_width=220),
        ).add_to(m)

    _render_folium_map(m, height=450)

    # Summary table
    st.markdown("##### Summary Table")
    df_summary = pd.DataFrame([
        {"Region": r, **region_data[r]} for r in regions_list
    ])
    df_summary["Total Population"] = df_summary["Total Population"].apply(_fmt_pop)
    df_summary["Total Area (km2)"] = df_summary["Total Area (km2)"].apply(lambda x: f"{x:,.0f}")
    df_summary["Avg Density"] = df_summary["Avg Density"].apply(lambda x: f"{x:.1f}")
    st.dataframe(df_summary, width="stretch", hide_index=True)

    csv_buf = io.StringIO()
    df_summary.to_csv(csv_buf, index=False)
    st.download_button(
        "Download Region Comparison (CSV)", data=csv_buf.getvalue(),
        file_name="region_comparison.csv", mime="text/csv", key="dem_reg_dl",
    )


# =====================================================================
# MAIN RENDER FUNCTION
# =====================================================================
def render_world_demographics_tab():
    """Main render function for the World Demographics & Culture tab."""

    st.markdown("""
    <div class="tab-header pink">
        <h4>World Demographics & Culture</h4>
        <p>Explore global population, languages, religions, and cultural heritage. Data from REST Countries, World Bank, and OpenStreetMap &mdash; all free, no API key.</p>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio(
        "Explorer Mode",
        ["Country Explorer", "Population & Statistics", "Languages & Religions", "Cultural Heritage Sites", "Regional Comparison"],
        horizontal=True,
        key="dem_mode",
    )

    st.markdown("---")

    if mode == "Country Explorer":
        _render_country_explorer()
    elif mode == "Population & Statistics":
        _render_population_stats()
    elif mode == "Languages & Religions":
        _render_languages_religions()
    elif mode == "Cultural Heritage Sites":
        _render_cultural_heritage()
    elif mode == "Regional Comparison":
        _render_regional_comparison()
