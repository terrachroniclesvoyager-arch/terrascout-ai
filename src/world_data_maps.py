"""
World Data & Statistics Maps module for TerraScout AI.
Creates composite maps using free APIs (World Bank, REST Countries) to
visualize global statistics: GDP, internet, education, life expectancy,
population density, urbanization, CO2, renewables, military spending,
tourism, inequality, and healthcare.
All APIs are free and require no API keys.
"""

import io
import logging
import streamlit as st
import requests
import pandas as pd
import numpy as np
try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from html import escape

matplotlib.use("Agg")
logger = logging.getLogger(__name__)

# ===================================================================
# API ENDPOINTS
# ===================================================================
WB_API = "https://api.worldbank.org/v2/country/all/indicator"
REST_COUNTRIES_URL = "https://restcountries.com/v3.1/all?fields=name,latlng,population,area,cca2,region"

# ===================================================================
# MAP DEFINITIONS  (key -> label, indicator, colormap, unit, description)
# ===================================================================
MAP_TYPES = {
    "Cost of Living Index": {
        "indicator": "NY.GDP.PCAP.CD",
        "cmap": "RdYlGn",
        "unit": "USD",
        "date": "2022",
        "desc": "GDP per capita as a proxy for cost of living. Higher GDP/capita generally correlates with higher cost of living.",
    },
    "Internet Penetration": {
        "indicator": "IT.NET.USER.ZS",
        "cmap": "viridis",
        "unit": "%",
        "date": "2022",
        "desc": "Individuals using the Internet (% of population). Highlights the global digital divide.",
    },
    "Education & Literacy": {
        "indicator": "SE.ADT.LITR.ZS",
        "cmap": "RdYlGn",
        "unit": "%",
        "date": "2022",
        "desc": "Adult literacy rate (% of people ages 15+). Education is a key driver of development.",
        "secondary": "SE.XPD.TOTL.GD.ZS",
        "secondary_label": "Education Spending (% GDP)",
    },
    "Life Expectancy Map": {
        "indicator": "SP.DYN.LE00.IN",
        "cmap": "RdYlGn",
        "unit": "years",
        "date": "2022",
        "desc": "Life expectancy at birth (total years). A fundamental measure of population health.",
    },
    "Population Density Heatmap": {
        "indicator": None,
        "cmap": "plasma",
        "unit": "people/km\u00b2",
        "date": "",
        "desc": "Population per square kilometer. Computed from REST Countries API data.",
    },
    "Urbanization Rate": {
        "indicator": "SP.URB.TOTL.IN.ZS",
        "cmap": "magma",
        "unit": "%",
        "date": "2022",
        "desc": "Urban population (% of total). Shows how city-centric each country has become.",
    },
    "CO2 Emissions Per Capita": {
        "indicator": "EN.ATM.CO2E.PC",
        "cmap": "YlOrRd",
        "unit": "metric tons",
        "date": "2020",
        "desc": "CO2 emissions (metric tons per capita). Key indicator of environmental impact.",
    },
    "Renewable Energy Share": {
        "indicator": "EG.FEC.RNEW.ZS",
        "cmap": "Greens",
        "unit": "%",
        "date": "2021",
        "desc": "Renewable energy consumption (% of total final energy). Tracks the green transition.",
    },
    "Military Spending": {
        "indicator": "MS.MIL.XPND.GD.ZS",
        "cmap": "OrRd",
        "unit": "% of GDP",
        "date": "2022",
        "desc": "Military expenditure as percentage of GDP. Reflects defense priorities.",
    },
    "Tourism Arrivals": {
        "indicator": "ST.INT.ARVL",
        "cmap": "YlGnBu",
        "unit": "arrivals",
        "date": "2020",
        "desc": "International tourism, number of arrivals. Tourism is vital for many economies.",
    },
    "Inequality (Gini Index)": {
        "indicator": "SI.POV.GINI",
        "cmap": "RdYlGn_r",
        "unit": "Gini",
        "date": "2021",
        "desc": "Gini index (0=perfect equality, 100=maximum inequality). Higher means more unequal.",
    },
    "Healthcare Spending": {
        "indicator": "SH.XPD.CHEX.GD.ZS",
        "cmap": "BuPu",
        "unit": "% of GDP",
        "date": "2021",
        "desc": "Current health expenditure (% of GDP). Key to understanding healthcare access.",
    },
}

# ===================================================================
# CACHED API FETCHERS
# ===================================================================

@st.cache_data(ttl=3600)
def _fetch_rest_countries() -> pd.DataFrame:
    """Fetch country coordinates, population, and area from REST Countries."""
    try:
        resp = requests.get(REST_COUNTRIES_URL, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.error("REST Countries fetch failed: %s", exc)
        return pd.DataFrame()

    rows = []
    for c in data:
        name = c.get("name", {}).get("common", "")
        cca2 = c.get("cca2", "")
        latlng = c.get("latlng", [None, None])
        pop = c.get("population", 0)
        area = c.get("area", 0)
        region = c.get("region", "")
        if cca2 and latlng and len(latlng) == 2 and latlng[0] is not None:
            rows.append({
                "country": name,
                "cca2": cca2,
                "lat": latlng[0],
                "lng": latlng[1],
                "population": pop,
                "area_km2": area,
                "region": region,
            })
    df = pd.DataFrame(rows)
    return df


@st.cache_data(ttl=3600)
def _fetch_wb_indicator(indicator: str, date: str = "2022") -> pd.DataFrame:
    """Generic World Bank indicator fetcher.

    Tries multiple years if the requested year returns no data
    (some indicators lag by 1-3 years).
    """
    years_to_try = [date]
    base_year = int(date)
    for offset in range(1, 6):
        years_to_try.append(str(base_year - offset))

    for yr in years_to_try:
        url = f"{WB_API}/{indicator}?format=json&per_page=300&date={yr}"
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            logger.error("World Bank fetch failed for %s (%s): %s", indicator, yr, exc)
            continue

        if not isinstance(payload, list) or len(payload) < 2:
            continue

        entries = payload[1]
        if not entries:
            continue

        rows = []
        for entry in entries:
            val = entry.get("value")
            iso = entry.get("countryiso3code", "")
            iso2 = entry.get("country", {}).get("id", "")
            name = entry.get("country", {}).get("value", "")
            if val is not None and iso2:
                rows.append({
                    "country": name,
                    "cca2": iso2,
                    "iso3": iso,
                    "value": float(val),
                    "year": entry.get("date", yr),
                })

        if rows:
            return pd.DataFrame(rows)

    return pd.DataFrame()


# ===================================================================
# MERGE HELPER
# ===================================================================

def _merge_with_coords(wb_df: pd.DataFrame, countries_df: pd.DataFrame) -> pd.DataFrame:
    """Merge World Bank data with REST Countries coords on cca2 code."""
    if wb_df.empty or countries_df.empty:
        return pd.DataFrame()
    merged = wb_df.merge(countries_df, on="cca2", how="inner", suffixes=("", "_rc"))
    if "country_rc" in merged.columns:
        merged.drop(columns=["country_rc"], inplace=True)
    return merged


# ===================================================================
# COLOR HELPERS
# ===================================================================

def _value_to_hex(value: float, vmin: float, vmax: float, cmap_name: str) -> str:
    """Map a numeric value to a hex color using a matplotlib colormap."""
    cmap = plt.get_cmap(cmap_name)
    if vmax == vmin:
        norm = 0.5
    else:
        norm = (value - vmin) / (vmax - vmin)
    norm = max(0.0, min(1.0, norm))
    rgba = cmap(norm)
    return mcolors.to_hex(rgba)


def _marker_radius(value: float, vmin: float, vmax: float,
                   rmin: float = 4.0, rmax: float = 18.0) -> float:
    """Scale value to a marker radius."""
    if vmax == vmin:
        return (rmin + rmax) / 2
    ratio = (value - vmin) / (vmax - vmin)
    ratio = max(0.0, min(1.0, ratio))
    return rmin + ratio * (rmax - rmin)


# ===================================================================
# CHART BUILDERS (dark theme matplotlib)
# ===================================================================

def _dark_bar_chart(df: pd.DataFrame, x_col: str, y_col: str,
                    title: str, color: str = "#06b6d4",
                    xlabel: str = "", ylabel: str = "",
                    horizontal: bool = True, top_n: int = 20) -> io.BytesIO:
    """Build a dark-themed bar chart and return as BytesIO PNG."""
    subset = df.nlargest(top_n, y_col).sort_values(y_col, ascending=True)
    fig, ax = plt.subplots(figsize=(7, max(4, top_n * 0.28)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")

    if horizontal:
        ax.barh(subset[x_col], subset[y_col], color=color, edgecolor="#2a3550")
        ax.set_xlabel(xlabel or y_col, color="#8b97b0", fontsize=9)
        ax.set_ylabel(ylabel or x_col, color="#8b97b0", fontsize=9)
    else:
        ax.bar(subset[x_col], subset[y_col], color=color, edgecolor="#2a3550")
        ax.set_ylabel(xlabel or y_col, color="#8b97b0", fontsize=9)
        ax.set_xlabel(ylabel or x_col, color="#8b97b0", fontsize=9)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(title, color="#e8ecf4", fontsize=11, pad=10)
    ax.tick_params(colors="#8b97b0", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x" if horizontal else "y", alpha=0.15, color="#5a6580")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="#0a0e1a", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _dark_bottom_bar_chart(df: pd.DataFrame, x_col: str, y_col: str,
                           title: str, color: str = "#ef4444",
                           bottom_n: int = 20) -> io.BytesIO:
    """Bar chart for the bottom-N countries."""
    subset = df.nsmallest(bottom_n, y_col).sort_values(y_col, ascending=True)
    fig, ax = plt.subplots(figsize=(7, max(4, bottom_n * 0.28)))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.barh(subset[x_col], subset[y_col], color=color, edgecolor="#2a3550")
    ax.set_title(title, color="#e8ecf4", fontsize=11, pad=10)
    ax.tick_params(colors="#8b97b0", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", alpha=0.15, color="#5a6580")
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="#0a0e1a", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _dark_pie_chart(labels: list, sizes: list, title: str,
                    colors: list = None) -> io.BytesIO:
    """Dark-themed pie chart."""
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#0a0e1a")
    if colors is None:
        cmap = plt.get_cmap("Set2")
        colors = [mcolors.to_hex(cmap(i / max(len(labels), 1))) for i in range(len(labels))]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="%1.1f%%",
        textprops={"color": "#e8ecf4", "fontsize": 8},
        pctdistance=0.75, startangle=90
    )
    for t in autotexts:
        t.set_color("#e8ecf4")
        t.set_fontsize(7)
    ax.set_title(title, color="#e8ecf4", fontsize=11, pad=10)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="#0a0e1a", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _regional_averages_chart(df: pd.DataFrame, value_col: str,
                             title: str, color: str = "#06b6d4") -> io.BytesIO:
    """Bar chart of average value by region."""
    regional = df.groupby("region")[value_col].mean().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    fig.patch.set_facecolor("#0a0e1a")
    ax.set_facecolor("#111827")
    ax.barh(regional.index, regional.values, color=color, edgecolor="#2a3550")
    ax.set_title(title, color="#e8ecf4", fontsize=11, pad=10)
    ax.tick_params(colors="#8b97b0", labelsize=8)
    for spine in ax.spines.values():
        spine.set_color("#2a3550")
    ax.grid(axis="x", alpha=0.15, color="#5a6580")
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="#0a0e1a", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


# ===================================================================
# MAP BUILDER
# ===================================================================

def _build_map(df: pd.DataFrame, value_col: str, cmap_name: str,
               label: str, unit: str, map_key: str,
               size_col: str = None) -> str:
    """Build a folium map with circle markers colored by value_col.

    Returns the HTML string for the map.
    """
    m = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
        attr="CartoDB",
    )

    if df.empty:
        return m._repr_html_()

    vmin = df[value_col].min()
    vmax = df[value_col].max()

    # Size column
    if size_col and size_col in df.columns:
        smin = df[size_col].min()
        smax = df[size_col].max()
    else:
        smin, smax = vmin, vmax
        size_col = value_col

    for _, row in df.iterrows():
        lat = row.get("lat")
        lng = row.get("lng")
        val = row.get(value_col)
        name = row.get("country", "")
        if pd.isna(lat) or pd.isna(lng) or pd.isna(val):
            continue

        color = _value_to_hex(val, vmin, vmax, cmap_name)
        size_val = row.get(size_col, val)
        if pd.isna(size_val):
            size_val = val
        radius = _marker_radius(size_val, smin, smax, 4, 18)

        # Format display value
        if abs(val) >= 1e9:
            display_val = f"{val / 1e9:,.1f}B"
        elif abs(val) >= 1e6:
            display_val = f"{val / 1e6:,.1f}M"
        elif abs(val) >= 1e3:
            display_val = f"{val:,.0f}"
        else:
            display_val = f"{val:,.2f}"

        popup_html = (
            f"<div style='font-family:sans-serif;min-width:160px;'>"
            f"<b style='font-size:13px;'>{escape(str(name))}</b><br>"
            f"<span style='color:#06b6d4;'>{escape(label)}</span>: "
            f"<b>{escape(display_val)}</b> {escape(unit)}<br>"
        )
        region = row.get("region", "")
        if region:
            popup_html += f"<span style='color:#8b97b0;'>Region: {escape(str(region))}</span><br>"
        popup_html += "</div>"

        folium.CircleMarker(
            location=[lat, lng],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{escape(str(name))}: {escape(display_val)} {escape(unit)}",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=1,
        ).add_to(m)

    return m._repr_html_()


# ===================================================================
# STATS ROW
# ===================================================================

def _display_stats(df: pd.DataFrame, value_col: str, unit: str, label: str):
    """Show st.metric row for global avg, highest, lowest, total countries."""
    if df.empty:
        st.warning("No data available to display statistics.")
        return

    total = len(df)
    avg_val = df[value_col].mean()
    max_row = df.loc[df[value_col].idxmax()]
    min_row = df.loc[df[value_col].idxmin()]

    def _fmt(v):
        if abs(v) >= 1e9:
            return f"{v / 1e9:,.1f}B"
        if abs(v) >= 1e6:
            return f"{v / 1e6:,.1f}M"
        if abs(v) >= 1e3:
            return f"{v:,.0f}"
        return f"{v:,.2f}"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Countries", f"{total}")
    c2.metric("Global Average", f"{_fmt(avg_val)} {unit}")
    c3.metric("Highest", f"{_fmt(max_row[value_col])} {unit}",
              help=str(max_row.get("country", "")))
    c4.metric("Lowest", f"{_fmt(min_row[value_col])} {unit}",
              help=str(min_row.get("country", "")))


# ===================================================================
# INDIVIDUAL MAP RENDERERS
# ===================================================================

def _render_cost_of_living(countries_df: pd.DataFrame):
    """Cost of Living Index (GDP per capita) map."""
    cfg = MAP_TYPES["Cost of Living Index"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch GDP per capita data. Please try again later.")
        return

    _display_stats(df, "value", cfg["unit"], "GDP per Capita")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "value", cfg["cmap"], "GDP per Capita", cfg["unit"],
                          "cost_of_living", size_col="population")
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - GDP per Capita (USD)",
                                 color="#10b981", xlabel="USD"),
                 use_container_width=True)
        st.image(_dark_bottom_bar_chart(df, "country", "value",
                                        "Bottom 20 - GDP per Capita (USD)"),
                 use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value", "population"]].copy()
        show_df.columns = ["Country", "Code", "Region", "GDP/Capita (USD)", "Population"]
        show_df = show_df.sort_values("GDP/Capita (USD)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")

        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "cost_of_living.csv", "text/csv")


def _render_internet_penetration(countries_df: pd.DataFrame):
    """Internet Penetration map."""
    cfg = MAP_TYPES["Internet Penetration"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch internet penetration data.")
        return

    _display_stats(df, "value", cfg["unit"], "Internet Users (%)")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "value", cfg["cmap"], "Internet Users", cfg["unit"],
                          "internet_penetration")
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - Internet Penetration (%)",
                                 color="#06b6d4", xlabel="%"),
                 use_container_width=True)
        if "region" in df.columns:
            st.image(_regional_averages_chart(df, "value",
                                              "Regional Average Internet Penetration",
                                              color="#06b6d4"),
                     use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value"]].copy()
        show_df.columns = ["Country", "Code", "Region", "Internet Users (%)"]
        show_df = show_df.sort_values("Internet Users (%)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "internet_penetration.csv", "text/csv")


def _render_education_literacy(countries_df: pd.DataFrame):
    """Education & Literacy dual-metric map."""
    cfg = MAP_TYPES["Education & Literacy"]
    wb_lit = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    wb_spend = _fetch_wb_indicator(cfg["secondary"], cfg["date"])

    df_lit = _merge_with_coords(wb_lit, countries_df)
    if df_lit.empty:
        st.error("Could not fetch literacy data.")
        return

    # Rename literacy value
    df_lit = df_lit.rename(columns={"value": "literacy"})

    # Merge spending data if available
    if not wb_spend.empty:
        spend_map = wb_spend.set_index("cca2")["value"].to_dict()
        df_lit["edu_spending"] = df_lit["cca2"].map(spend_map)
    else:
        df_lit["edu_spending"] = np.nan

    _display_stats(df_lit, "literacy", "%", "Adult Literacy Rate")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        # Build map colored by literacy, sized by spending if available
        size_col = "edu_spending" if df_lit["edu_spending"].notna().sum() > 10 else None
        html = _build_map(df_lit, "literacy", cfg["cmap"],
                          "Literacy Rate", "%", "education",
                          size_col=size_col)
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df_lit, "country", "literacy",
                                 "Top 20 - Literacy Rate (%)",
                                 color="#10b981", xlabel="%"),
                 use_container_width=True)
        if df_lit["edu_spending"].notna().sum() > 5:
            spend_df = df_lit.dropna(subset=["edu_spending"])
            st.image(_dark_bar_chart(spend_df, "country", "edu_spending",
                                     "Top 20 - Education Spending (% GDP)",
                                     color="#8b5cf6", xlabel="% GDP"),
                     use_container_width=True)

    with st.expander("Data Table", expanded=False):
        cols = ["country", "cca2", "region", "literacy"]
        names = ["Country", "Code", "Region", "Literacy (%)"]
        if df_lit["edu_spending"].notna().sum() > 0:
            cols.append("edu_spending")
            names.append("Edu Spending (% GDP)")
        show_df = df_lit[cols].copy()
        show_df.columns = names
        show_df = show_df.sort_values("Literacy (%)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "education_literacy.csv", "text/csv")


def _render_life_expectancy(countries_df: pd.DataFrame):
    """Life Expectancy map."""
    cfg = MAP_TYPES["Life Expectancy Map"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch life expectancy data.")
        return

    _display_stats(df, "value", cfg["unit"], "Life Expectancy")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "value", cfg["cmap"], "Life Expectancy",
                          cfg["unit"], "life_expectancy")
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - Life Expectancy (years)",
                                 color="#10b981", xlabel="years"),
                 use_container_width=True)
        if "region" in df.columns:
            st.image(_regional_averages_chart(df, "value",
                                              "Regional Average Life Expectancy",
                                              color="#06b6d4"),
                     use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value"]].copy()
        show_df.columns = ["Country", "Code", "Region", "Life Expectancy (years)"]
        show_df = show_df.sort_values("Life Expectancy (years)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "life_expectancy.csv", "text/csv")


def _render_population_density(countries_df: pd.DataFrame):
    """Population Density Heatmap from REST Countries data."""
    df = countries_df.copy()
    df = df[df["area_km2"] > 0].copy()
    df["density"] = df["population"] / df["area_km2"]
    df = df[df["density"].notna() & (df["density"] > 0)]

    if df.empty:
        st.error("Could not compute population density.")
        return

    cfg = MAP_TYPES["Population Density Heatmap"]
    _display_stats(df, "density", cfg["unit"], "Population Density")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "density", cfg["cmap"], "Density",
                          cfg["unit"], "pop_density",
                          size_col="population")
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "density",
                                 "Top 20 - Most Dense Countries",
                                 color="#f59e0b", xlabel="people/km\u00b2"),
                 use_container_width=True)
        st.image(_dark_bottom_bar_chart(df, "country", "density",
                                        "Bottom 20 - Least Dense Countries",
                                        color="#3b82f6"),
                 use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "population", "area_km2", "density"]].copy()
        show_df.columns = ["Country", "Code", "Region", "Population", "Area (km\u00b2)", "Density (ppl/km\u00b2)"]
        show_df = show_df.sort_values("Density (ppl/km\u00b2)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "population_density.csv", "text/csv")


def _render_urbanization(countries_df: pd.DataFrame):
    """Urbanization Rate map."""
    cfg = MAP_TYPES["Urbanization Rate"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch urbanization data.")
        return

    _display_stats(df, "value", cfg["unit"], "Urban Population (%)")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "value", cfg["cmap"], "Urban Population",
                          cfg["unit"], "urbanization")
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - Most Urbanized (%)",
                                 color="#ec4899", xlabel="%"),
                 use_container_width=True)
        if "region" in df.columns:
            st.image(_regional_averages_chart(df, "value",
                                              "Regional Average Urbanization",
                                              color="#ec4899"),
                     use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value"]].copy()
        show_df.columns = ["Country", "Code", "Region", "Urban Population (%)"]
        show_df = show_df.sort_values("Urban Population (%)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "urbanization.csv", "text/csv")


def _render_co2_emissions(countries_df: pd.DataFrame):
    """CO2 Emissions Per Capita map."""
    cfg = MAP_TYPES["CO2 Emissions Per Capita"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch CO2 emissions data.")
        return

    _display_stats(df, "value", cfg["unit"], "CO2 per Capita")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "value", cfg["cmap"], "CO2 Emissions",
                          cfg["unit"], "co2_emissions")
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - CO2 Emitters (metric tons/capita)",
                                 color="#ef4444", xlabel="metric tons"),
                 use_container_width=True)
        if "region" in df.columns:
            st.image(_regional_averages_chart(df, "value",
                                              "Regional Average CO2 per Capita",
                                              color="#f97316"),
                     use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value"]].copy()
        show_df.columns = ["Country", "Code", "Region", "CO2 (metric tons/capita)"]
        show_df = show_df.sort_values("CO2 (metric tons/capita)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "co2_emissions.csv", "text/csv")


def _render_renewable_energy(countries_df: pd.DataFrame):
    """Renewable Energy Share map."""
    cfg = MAP_TYPES["Renewable Energy Share"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch renewable energy data.")
        return

    _display_stats(df, "value", cfg["unit"], "Renewable Energy (%)")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "value", cfg["cmap"], "Renewable Energy",
                          cfg["unit"], "renewable_energy")
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - Renewable Energy Share (%)",
                                 color="#10b981", xlabel="%"),
                 use_container_width=True)
        # Pie chart: global split (average renewable vs non-renewable)
        avg_ren = df["value"].mean()
        avg_non = 100 - avg_ren
        st.image(_dark_pie_chart(
            ["Renewable", "Non-Renewable"],
            [avg_ren, avg_non],
            "Global Average Energy Mix",
            colors=["#10b981", "#ef4444"]
        ), use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value"]].copy()
        show_df.columns = ["Country", "Code", "Region", "Renewable Energy (%)"]
        show_df = show_df.sort_values("Renewable Energy (%)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "renewable_energy.csv", "text/csv")


def _render_military_spending(countries_df: pd.DataFrame):
    """Military Spending map."""
    cfg = MAP_TYPES["Military Spending"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch military spending data.")
        return

    _display_stats(df, "value", cfg["unit"], "Military Expenditure")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "value", cfg["cmap"], "Military Spending",
                          cfg["unit"], "military_spending")
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - Military Spending (% GDP)",
                                 color="#dc2626", xlabel="% of GDP"),
                 use_container_width=True)
        if "region" in df.columns:
            st.image(_regional_averages_chart(df, "value",
                                              "Regional Average Military Spending",
                                              color="#dc2626"),
                     use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value"]].copy()
        show_df.columns = ["Country", "Code", "Region", "Military Spending (% GDP)"]
        show_df = show_df.sort_values("Military Spending (% GDP)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "military_spending.csv", "text/csv")


def _render_tourism_arrivals(countries_df: pd.DataFrame):
    """Tourism Arrivals map."""
    cfg = MAP_TYPES["Tourism Arrivals"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch tourism arrivals data.")
        return

    _display_stats(df, "value", cfg["unit"], "Tourism Arrivals")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "value", cfg["cmap"], "Tourist Arrivals",
                          cfg["unit"], "tourism_arrivals")
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - Tourism Destinations (arrivals)",
                                 color="#3b82f6", xlabel="arrivals"),
                 use_container_width=True)
        if "region" in df.columns:
            # Regional total tourism
            regional = df.groupby("region")["value"].sum().sort_values(ascending=True)
            fig, ax = plt.subplots(figsize=(7, 3.5))
            fig.patch.set_facecolor("#0a0e1a")
            ax.set_facecolor("#111827")
            ax.barh(regional.index, regional.values, color="#3b82f6", edgecolor="#2a3550")
            ax.set_title("Total Tourism by Region", color="#e8ecf4", fontsize=11, pad=10)
            ax.tick_params(colors="#8b97b0", labelsize=8)
            for spine in ax.spines.values():
                spine.set_color("#2a3550")
            ax.grid(axis="x", alpha=0.15, color="#5a6580")
            buf = io.BytesIO()
            fig.tight_layout()
            fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                        facecolor="#0a0e1a", edgecolor="none")
            plt.close(fig)
            buf.seek(0)
            st.image(buf, use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value"]].copy()
        show_df.columns = ["Country", "Code", "Region", "Tourism Arrivals"]
        show_df = show_df.sort_values("Tourism Arrivals", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "tourism_arrivals.csv", "text/csv")


def _render_inequality(countries_df: pd.DataFrame):
    """Inequality (Gini Index) map."""
    cfg = MAP_TYPES["Inequality (Gini Index)"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch Gini index data.")
        return

    _display_stats(df, "value", cfg["unit"], "Gini Index")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        html = _build_map(df, "value", cfg["cmap"], "Gini Index",
                          cfg["unit"], "gini_inequality")
        components.html(html, height=600)

    with col_chart:
        # Most unequal (highest Gini)
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - Most Unequal (Gini)",
                                 color="#ef4444", xlabel="Gini Index"),
                 use_container_width=True)
        if "region" in df.columns:
            st.image(_regional_averages_chart(df, "value",
                                              "Regional Average Gini Index",
                                              color="#f59e0b"),
                     use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value"]].copy()
        show_df.columns = ["Country", "Code", "Region", "Gini Index"]
        show_df = show_df.sort_values("Gini Index", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "gini_inequality.csv", "text/csv")


def _render_healthcare_spending(countries_df: pd.DataFrame):
    """Healthcare Spending map."""
    cfg = MAP_TYPES["Healthcare Spending"]
    wb = _fetch_wb_indicator(cfg["indicator"], cfg["date"])
    df = _merge_with_coords(wb, countries_df)
    if df.empty:
        st.error("Could not fetch healthcare spending data.")
        return

    _display_stats(df, "value", cfg["unit"], "Health Expenditure")

    col_map, col_chart = st.columns([3, 2])
    with col_map:
        # Custom map with medical cross icons for top spenders
        m = folium.Map(
            location=[20, 0],
            zoom_start=2,
            tiles="CartoDB dark_matter",
            attr="CartoDB",
        )

        vmin = df["value"].min()
        vmax = df["value"].max()
        top_threshold = df["value"].quantile(0.9)

        for _, row in df.iterrows():
            lat = row.get("lat")
            lng = row.get("lng")
            val = row.get("value")
            name = row.get("country", "")
            if pd.isna(lat) or pd.isna(lng) or pd.isna(val):
                continue

            color = _value_to_hex(val, vmin, vmax, cfg["cmap"])
            radius = _marker_radius(val, vmin, vmax, 4, 18)

            popup_html = (
                f"<div style='font-family:sans-serif;min-width:160px;'>"
                f"<b style='font-size:13px;'>{escape(str(name))}</b><br>"
                f"<span style='color:#06b6d4;'>Health Spending</span>: "
                f"<b>{val:.2f}</b> % GDP<br>"
            )
            region = row.get("region", "")
            if region:
                popup_html += f"<span style='color:#8b97b0;'>Region: {escape(str(region))}</span><br>"
            popup_html += "</div>"

            folium.CircleMarker(
                location=[lat, lng],
                radius=radius,
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{escape(str(name))}: {val:.2f}% GDP",
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.7,
                weight=1,
            ).add_to(m)

            # Add a medical cross icon for high spenders
            if val >= top_threshold:
                folium.Marker(
                    location=[lat, lng],
                    icon=folium.DivIcon(
                        html=(
                            f"<div style='font-size:16px;color:#e8ecf4;"
                            f"text-shadow:0 0 4px #000;font-weight:bold;'>"
                            f"&#10010;</div>"
                        ),
                        icon_size=(20, 20),
                        icon_anchor=(10, 10),
                    ),
                ).add_to(m)

        html = m._repr_html_()
        components.html(html, height=600)

    with col_chart:
        st.image(_dark_bar_chart(df, "country", "value",
                                 "Top 20 - Healthcare Spending (% GDP)",
                                 color="#8b5cf6", xlabel="% of GDP"),
                 use_container_width=True)
        if "region" in df.columns:
            st.image(_regional_averages_chart(df, "value",
                                              "Regional Average Healthcare Spending",
                                              color="#8b5cf6"),
                     use_container_width=True)

    with st.expander("Data Table", expanded=False):
        show_df = df[["country", "cca2", "region", "value"]].copy()
        show_df.columns = ["Country", "Code", "Region", "Health Spending (% GDP)"]
        show_df = show_df.sort_values("Health Spending (% GDP)", ascending=False).reset_index(drop=True)
        st.dataframe(show_df, width="stretch")
        csv = show_df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "healthcare_spending.csv", "text/csv")


# ===================================================================
# MAP TYPE DISPATCH
# ===================================================================

_MAP_RENDERERS = {
    "Cost of Living Index": _render_cost_of_living,
    "Internet Penetration": _render_internet_penetration,
    "Education & Literacy": _render_education_literacy,
    "Life Expectancy Map": _render_life_expectancy,
    "Population Density Heatmap": _render_population_density,
    "Urbanization Rate": _render_urbanization,
    "CO2 Emissions Per Capita": _render_co2_emissions,
    "Renewable Energy Share": _render_renewable_energy,
    "Military Spending": _render_military_spending,
    "Tourism Arrivals": _render_tourism_arrivals,
    "Inequality (Gini Index)": _render_inequality,
    "Healthcare Spending": _render_healthcare_spending,
}


# ===================================================================
# MAIN RENDER FUNCTION
# ===================================================================

def render_world_data_maps_tab():
    """Main entry point: renders the World Data Maps tab content."""

    # Tab header (glassmorphism theme)
    st.markdown(
        '<div class="tab-header cyan">'
        "<h4>World Data Maps</h4>"
        "<p>Global statistics visualized on interactive maps</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Map type selector
    selected_map = st.selectbox(
        "Select Map Type",
        list(MAP_TYPES.keys()),
        index=0,
        help="Choose a global indicator to visualize on the map.",
    )

    # Description
    cfg = MAP_TYPES[selected_map]
    st.info(f"**{selected_map}** - {cfg['desc']}")

    # Fetch countries (shared across all map types)
    with st.spinner("Loading country data..."):
        countries_df = _fetch_rest_countries()

    if countries_df.empty:
        st.error(
            "Could not load country coordinates from REST Countries API. "
            "Please check your internet connection and try again."
        )
        return

    st.caption(f"Loaded coordinates for **{len(countries_df)}** countries.")

    # Render the selected map
    renderer = _MAP_RENDERERS.get(selected_map)
    if renderer:
        with st.spinner(f"Loading {selected_map} data..."):
            renderer(countries_df)
    else:
        st.error(f"No renderer found for '{selected_map}'.")
