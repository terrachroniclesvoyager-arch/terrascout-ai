"""
Climate Change Monitor module for TerraScout AI.
Tracks CO2 levels, global temperature anomalies, and historical climate data
using free APIs: global-warming.org and Open-Meteo Archive.
No API keys required.
"""

import io
import streamlit as st
import requests
import pandas as pd
import numpy as np
from html import escape
from datetime import date, timedelta

try:
    import folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False
import streamlit.components.v1 as components

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ═══════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════
GW_CO2_API = "https://global-warming.org/api/co2-api"
GW_TEMP_API = "https://global-warming.org/api/temperature-api"
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

# ═══════════════════════════════════════════
# THEME COLORS
# ═══════════════════════════════════════════
CLR_BG = "#0a0e1a"
CLR_SURFACE = "#111827"
CLR_CARD = "#1a2235"
CLR_BORDER = "#2a3550"
CLR_TEXT = "#e8ecf4"
CLR_TEXT_SEC = "#8b97b0"
CLR_TEXT_MUTED = "#5a6580"
CLR_ACCENT = "#06b6d4"
CLR_CO2 = "#06b6d4"
CLR_TEMP_POS = "#ef4444"
CLR_TEMP_NEG = "#3b82f6"
CLR_PRECIP = "#8b5cf6"
CLR_TREND = "#f59e0b"
CLR_GRID = "#2a3550"

# ═══════════════════════════════════════════
# LOCATION PRESETS FOR CLIMATE HISTORY
# ═══════════════════════════════════════════
CLIMATE_PRESETS = {
    "Arctic (Svalbard)": (78.2, 15.6),
    "Amazon (Manaus)": (-3.4, -60.0),
    "Sahara (Southern Egypt)": (23.4, 25.7),
    "Antarctic (McMurdo)": (-77.8, 166.7),
    "Great Barrier Reef": (-18.3, 147.7),
    "Greenland (Ilulissat)": (72.0, -40.0),
    "Siberia (Yakutsk)": (62.0, 130.0),
    "Maldives (Male)": (4.2, 73.5),
}

PRESET_DESCRIPTIONS = {
    "Arctic (Svalbard)": "High Arctic archipelago experiencing rapid warming",
    "Amazon (Manaus)": "Heart of the Amazon rainforest, largest tropical biome",
    "Sahara (Southern Egypt)": "World's largest hot desert, extreme arid climate",
    "Antarctic (McMurdo)": "McMurdo Station, Antarctica's most studied region",
    "Great Barrier Reef": "World's largest coral reef system, vulnerable to warming",
    "Greenland (Ilulissat)": "Near the Ilulissat Icefjord, rapid ice sheet melt zone",
    "Siberia (Yakutsk)": "Coldest major city on Earth, permafrost region",
    "Maldives (Male)": "Low-lying island nation threatened by sea-level rise",
}

PRESET_ICONS = {
    "Arctic (Svalbard)": "snowflake-o",
    "Amazon (Manaus)": "tree",
    "Sahara (Southern Egypt)": "sun-o",
    "Antarctic (McMurdo)": "snowflake-o",
    "Great Barrier Reef": "tint",
    "Greenland (Ilulissat)": "snowflake-o",
    "Siberia (Yakutsk)": "snowflake-o",
    "Maldives (Male)": "tint",
}


# ═══════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════
def _style_ax(ax):
    """Apply TerraScout dark theme to a matplotlib axis."""
    ax.set_facecolor(CLR_SURFACE)
    ax.grid(True, color=CLR_GRID, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", colors=CLR_TEXT_SEC, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(CLR_GRID)


def _new_fig(rows=1, cols=1, height=4.5, width=10):
    """Create a new dark-themed figure."""
    fig, axes = plt.subplots(rows, cols, figsize=(width, height))
    fig.patch.set_facecolor(CLR_BG)
    if rows == 1 and cols == 1:
        _style_ax(axes)
    else:
        for ax in (axes.flat if hasattr(axes, "flat") else [axes]):
            _style_ax(ax)
    return fig, axes


# ═══════════════════════════════════════════
# DATA FETCHING
# ═══════════════════════════════════════════
@st.cache_data(ttl=3600)
def _fetch_co2() -> list:
    """Fetch monthly CO2 data from global-warming.org."""
    try:
        resp = requests.get(GW_CO2_API, timeout=20)
        resp.raise_for_status()
        return resp.json().get("co2", [])
    except Exception as e:
        return [{"error": str(e)}]


@st.cache_data(ttl=3600)
def _fetch_temperature() -> list:
    """Fetch global temperature anomaly data from global-warming.org."""
    try:
        resp = requests.get(GW_TEMP_API, timeout=20)
        resp.raise_for_status()
        return resp.json().get("result", [])
    except Exception as e:
        return [{"error": str(e)}]


@st.cache_data(ttl=3600)
def _fetch_climate_history(lat: float, lon: float,
                           start_date: str, end_date: str) -> dict:
    """Fetch historical climate data from Open-Meteo Archive API."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean,precipitation_sum",
        "timezone": "auto",
    }
    try:
        resp = requests.get(OPEN_METEO_ARCHIVE, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def _parse_co2_data(raw: list) -> pd.DataFrame:
    """Parse raw CO2 API response into a clean DataFrame."""
    records = []
    for entry in raw:
        try:
            year = int(entry.get("year", 0))
            month = int(entry.get("month", 1))
            cycle = float(entry.get("cycle", 0))
            trend = float(entry.get("trend", 0))
            records.append({
                "year": year, "month": month,
                "cycle": cycle, "trend": trend,
            })
        except (ValueError, TypeError):
            continue
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    df = df.sort_values("date").reset_index(drop=True)
    return df


def _parse_temp_data(raw: list) -> pd.DataFrame:
    """Parse raw temperature anomaly API response into a clean DataFrame."""
    records = []
    for entry in raw:
        try:
            time_str = entry.get("time", "")
            station = float(entry.get("station", 0))
            land = float(entry.get("land", 0))
            records.append({"time": time_str, "station": station, "land": land})
        except (ValueError, TypeError):
            continue
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    try:
        df["decimal_year"] = df["time"].astype(float)
        df["year"] = df["decimal_year"].astype(int)
        df["month"] = ((df["decimal_year"] % 1) * 12 + 1).astype(int).clip(1, 12)
        df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))
    except Exception:
        df["date"] = pd.to_datetime(df["time"], errors="coerce")
        df = df.dropna(subset=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


# ═══════════════════════════════════════════
# MODE 1: CO2 LEVELS
# ═══════════════════════════════════════════
def _render_co2_levels():
    """Render CO2 Keeling Curve dashboard."""
    st.markdown("#### Atmospheric CO2 Levels (Mauna Loa)")

    with st.spinner("Fetching CO2 data from global-warming.org..."):
        raw = _fetch_co2()

    if not raw or (len(raw) == 1 and "error" in raw[0]):
        err = raw[0].get("error", "Unknown error") if raw else "No data returned"
        st.error(f"Could not fetch CO2 data: {escape(str(err))}")
        return

    df = _parse_co2_data(raw)
    if df.empty:
        st.warning("No valid CO2 records found in API response.")
        return

    latest = df.iloc[-1]
    latest_ppm = latest["trend"]
    latest_date = latest["date"].strftime("%b %Y")

    # Year-over-year change
    one_year_ago = df[df["date"] <= latest["date"] - pd.DateOffset(years=1)]
    yoy_change = latest_ppm - one_year_ago.iloc[-1]["trend"] if len(one_year_ago) > 0 else 0.0

    # Decade-over-decade
    ten_years_ago = df[df["date"] <= latest["date"] - pd.DateOffset(years=10)]
    decade_change = latest_ppm - ten_years_ago.iloc[-1]["trend"] if len(ten_years_ago) > 0 else 0.0

    # Pre-industrial comparison
    pre_industrial = 280.0
    increase = latest_ppm - pre_industrial

    # ── Metrics row ──
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Current CO2", f"{latest_ppm:.1f} ppm", delta=f"{yoy_change:+.1f} ppm/yr")
    with c2:
        st.metric("Data Date", latest_date)
    with c3:
        st.metric("Above Pre-Industrial", f"+{increase:.0f} ppm",
                   delta=f"{(increase / pre_industrial * 100):.1f}% above 280 ppm")
    with c4:
        st.metric("10-Year Change", f"+{decade_change:.1f} ppm")

    # ── Keeling Curve chart ──
    st.markdown("---")
    st.markdown("#### Keeling Curve -- Atmospheric CO2 Concentration")

    fig, ax = _new_fig(height=5)
    ax.plot(df["date"], df["cycle"], color=CLR_CO2, linewidth=0.6, alpha=0.4, label="Seasonal cycle")
    ax.plot(df["date"], df["trend"], color=CLR_CO2, linewidth=2.0, label="Trend")
    ax.fill_between(df["date"], df["trend"], alpha=0.08, color=CLR_CO2)

    # Milestone lines
    for ppm_level, label in [(350, "350 ppm (safe limit)"), (400, "400 ppm"), (420, "420 ppm")]:
        if df["trend"].max() >= ppm_level:
            ax.axhline(y=ppm_level, color=CLR_TEXT_MUTED, linestyle="--", linewidth=0.7, alpha=0.5)
            ax.text(df["date"].iloc[0], ppm_level + 1.5, label, color=CLR_TEXT_MUTED, fontsize=7)

    ax.set_ylabel("CO2 (ppm)", color=CLR_TEXT_SEC, fontsize=10)
    ax.set_xlabel("Year", color=CLR_TEXT_SEC, fontsize=10)
    ax.set_title("Atmospheric CO2 -- Mauna Loa Observatory", color=CLR_TEXT, fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, facecolor=CLR_BG, edgecolor=CLR_GRID, labelcolor=CLR_TEXT_SEC)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── Rate of change chart ──
    st.markdown("#### Annual Rate of CO2 Increase")
    annual = df.groupby("year")["trend"].last().reset_index()
    annual["change"] = annual["trend"].diff()
    annual = annual.dropna(subset=["change"])

    if len(annual) > 5:
        fig2, ax2 = _new_fig(height=3.5)
        colors = [CLR_TEMP_POS if v > annual["change"].mean() else CLR_CO2 for v in annual["change"]]
        ax2.bar(annual["year"], annual["change"], color=colors, alpha=0.7, width=0.8)
        avg_rate = annual["change"].mean()
        ax2.axhline(y=avg_rate, color=CLR_TREND, linestyle="--", linewidth=1.5, alpha=0.7)
        ax2.text(annual["year"].iloc[0], avg_rate + 0.1, f"Avg: {avg_rate:.2f} ppm/yr",
                 color=CLR_TREND, fontsize=8)
        ax2.set_ylabel("CO2 change (ppm/year)", color=CLR_TEXT_SEC, fontsize=9)
        ax2.set_title("Annual CO2 Increase Rate", color=CLR_TEXT, fontsize=11, fontweight="bold")
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    # ── Data table and download ──
    with st.expander(f"CO2 Data Table ({len(df)} records)", expanded=False):
        st.dataframe(
            df[["date", "cycle", "trend"]].rename(columns={
                "date": "Date", "cycle": "CO2 Seasonal (ppm)", "trend": "CO2 Trend (ppm)",
            }),
            width="stretch", hide_index=True,
        )

    csv_buf = io.StringIO()
    df[["date", "cycle", "trend"]].to_csv(csv_buf, index=False)
    st.download_button(
        "Download CO2 Data (CSV)", data=csv_buf.getvalue(),
        file_name="co2_keeling_curve.csv", mime="text/csv", key="clim_co2_csv",
    )


# ═══════════════════════════════════════════
# MODE 2: TEMPERATURE ANOMALY
# ═══════════════════════════════════════════
def _render_temperature_anomaly():
    """Render global temperature anomaly dashboard."""
    st.markdown("#### Global Temperature Anomaly")

    with st.spinner("Fetching temperature data from global-warming.org..."):
        raw = _fetch_temperature()

    if not raw or (len(raw) == 1 and "error" in raw[0]):
        err = raw[0].get("error", "Unknown error") if raw else "No data returned"
        st.error(f"Could not fetch temperature data: {escape(str(err))}")
        return

    df = _parse_temp_data(raw)
    if df.empty:
        st.warning("No valid temperature records found.")
        return

    latest = df.iloc[-1]
    latest_anomaly = latest["station"]
    latest_date = latest["date"].strftime("%b %Y")

    # Decade averages
    if "year" not in df.columns:
        df["year"] = df["date"].dt.year
    df["decade"] = (df["year"] // 10) * 10
    decade_avg = df.groupby("decade")["station"].mean()

    max_anomaly = df["station"].max()
    max_idx = df["station"].idxmax()
    max_date = df.loc[max_idx, "date"].strftime("%b %Y")

    # ── Metrics ──
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sign = "+" if latest_anomaly >= 0 else ""
        st.metric("Latest Anomaly", f"{sign}{latest_anomaly:.2f} degC", delta=latest_date)
    with c2:
        last_decade = decade_avg.iloc[-1] if len(decade_avg) > 0 else 0
        st.metric("Last Decade Avg", f"{last_decade:+.2f} degC")
    with c3:
        st.metric("Record High Anomaly", f"+{max_anomaly:.2f} degC", delta=max_date)
    with c4:
        recent_5yr = df.tail(60)["station"].mean() if len(df) >= 60 else df["station"].mean()
        st.metric("Recent 5-Year Avg", f"{recent_5yr:+.2f} degC")

    # ── Temperature anomaly chart with fill ──
    st.markdown("---")
    st.markdown("#### Temperature Anomaly Over Time")

    fig, ax = _new_fig(height=5)

    positive = df["station"].clip(lower=0)
    negative = df["station"].clip(upper=0)
    ax.fill_between(df["date"], 0, positive, color=CLR_TEMP_POS, alpha=0.25, label="Warming")
    ax.fill_between(df["date"], 0, negative, color=CLR_TEMP_NEG, alpha=0.25, label="Cooling")
    ax.plot(df["date"], df["station"], color=CLR_TEMP_POS, linewidth=0.6, alpha=0.5)

    # Linear trend
    x_num = (df["date"] - df["date"].iloc[0]).dt.days.values.astype(float)
    if len(x_num) > 2:
        coeffs = np.polyfit(x_num, df["station"].values, 1)
        trend_line = np.polyval(coeffs, x_num)
        ax.plot(df["date"], trend_line, color=CLR_TREND, linewidth=2, linestyle="--", label="Linear trend")
        warming_per_decade = coeffs[0] * 365.25 * 10
        st.info(f"Linear warming trend: **{warming_per_decade:+.3f} degC per decade**")

    ax.axhline(y=0, color=CLR_TEXT_MUTED, linewidth=1, alpha=0.5)
    ax.set_ylabel("Temperature Anomaly (degC)", color=CLR_TEXT_SEC, fontsize=10)
    ax.set_xlabel("Year", color=CLR_TEXT_SEC, fontsize=10)
    ax.set_title("Global Temperature Anomaly (relative to 1951-1980 baseline)",
                 color=CLR_TEXT, fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, facecolor=CLR_BG, edgecolor=CLR_GRID, labelcolor=CLR_TEXT_SEC)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── Decade averages bar chart ──
    st.markdown("#### Decade Averages")
    if len(decade_avg) > 2:
        fig2, ax2 = _new_fig(height=3.5)
        colors = [CLR_TEMP_POS if v >= 0 else CLR_TEMP_NEG for v in decade_avg.values]
        bars = ax2.bar(decade_avg.index.astype(str), decade_avg.values, color=colors, alpha=0.8, width=0.7)
        for bar_item, val in zip(bars, decade_avg.values):
            ax2.text(bar_item.get_x() + bar_item.get_width() / 2, val + 0.02 if val >= 0 else val - 0.06,
                     f"{val:+.2f}", ha="center", color=CLR_TEXT_SEC, fontsize=7)
        ax2.axhline(y=0, color=CLR_TEXT_MUTED, linewidth=0.8)
        ax2.set_ylabel("Avg Anomaly (degC)", color=CLR_TEXT_SEC, fontsize=9)
        ax2.set_title("Average Temperature Anomaly by Decade", color=CLR_TEXT, fontsize=11, fontweight="bold")
        ax2.tick_params(axis="x", rotation=45)
        fig2.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    # ── Data table and download ──
    with st.expander(f"Temperature Data ({len(df)} records)", expanded=False):
        st.dataframe(
            df[["date", "station", "land"]].rename(columns={
                "date": "Date", "station": "Station Anomaly (degC)", "land": "Land Anomaly (degC)",
            }),
            width="stretch", hide_index=True,
        )

    csv_buf = io.StringIO()
    df[["date", "station", "land"]].to_csv(csv_buf, index=False)
    st.download_button(
        "Download Temperature Data (CSV)", data=csv_buf.getvalue(),
        file_name="temperature_anomaly.csv", mime="text/csv", key="clim_temp_csv",
    )


# ═══════════════════════════════════════════
# MODE 3: CLIMATE HISTORY
# ═══════════════════════════════════════════
def _render_climate_history():
    """Render historical climate data for preset locations via Open-Meteo Archive."""
    st.markdown("#### Historical Climate Data (Open-Meteo Archive)")
    st.caption("Explore temperature and precipitation history for climate-sensitive locations worldwide.")

    # ── Location selection ──
    c1, c2 = st.columns([2, 1])
    with c1:
        preset_name = st.selectbox(
            "Location Preset", list(CLIMATE_PRESETS.keys()),
            key="clim_hist_preset",
        )
    with c2:
        lat, lon = CLIMATE_PRESETS[preset_name]
        st.markdown(f"**Lat:** {lat:.1f}  **Lon:** {lon:.1f}")

    desc = PRESET_DESCRIPTIONS.get(preset_name, "")
    if desc:
        st.markdown(f"*{escape(desc)}*")

    # ── Date range ──
    st.markdown("##### Date Range")
    d1, d2 = st.columns(2)
    with d1:
        start_dt = st.date_input(
            "Start Date", value=date(2020, 1, 1),
            min_value=date(1940, 1, 1), max_value=date.today() - timedelta(days=7),
            key="clim_hist_start",
        )
    with d2:
        end_dt = st.date_input(
            "End Date", value=date.today() - timedelta(days=2),
            min_value=date(1940, 1, 2), max_value=date.today() - timedelta(days=1),
            key="clim_hist_end",
        )

    if start_dt >= end_dt:
        st.warning("Start date must be before end date.")
        return

    if st.button("Fetch Climate History", key="clim_hist_btn", width="stretch"):
        st.session_state.clim_hist_params = {
            "name": preset_name, "lat": lat, "lon": lon,
            "start": start_dt.isoformat(), "end": end_dt.isoformat(),
        }

    if "clim_hist_params" not in st.session_state:
        # Show the preset location map even before fetching data
        _render_preset_map()
        st.info("Select a location and date range, then click 'Fetch Climate History'.")
        return

    params = st.session_state.clim_hist_params

    with st.spinner(f"Fetching climate history for {escape(params['name'])}..."):
        data = _fetch_climate_history(params["lat"], params["lon"], params["start"], params["end"])

    if data.get("error"):
        st.error(f"API Error: {escape(str(data['error']))}")
        return

    daily = data.get("daily", {})
    times = daily.get("time", [])
    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    temp_mean = daily.get("temperature_2m_mean", [])
    precip = daily.get("precipitation_sum", [])

    if not times:
        st.warning("No data returned for this location and date range.")
        return

    df = pd.DataFrame({
        "date": pd.to_datetime(times),
        "temp_max": temp_max,
        "temp_min": temp_min,
        "temp_mean": temp_mean,
        "precip": precip,
    })
    df = df.dropna(subset=["temp_mean"]).sort_values("date").reset_index(drop=True)
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    if df.empty:
        st.warning("No valid data points returned.")
        return

    # ── Summary metrics ──
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Avg Temperature", f"{df['temp_mean'].mean():.1f} degC")
    with c2:
        st.metric("Max Recorded", f"{df['temp_max'].max():.1f} degC")
    with c3:
        st.metric("Min Recorded", f"{df['temp_min'].min():.1f} degC")
    with c4:
        total_precip = df["precip"].sum()
        st.metric("Total Precipitation", f"{total_precip:.0f} mm")

    # ── Temperature chart ──
    st.markdown("---")
    st.markdown(f"#### Temperature History -- {escape(params['name'])}")

    fig, ax = _new_fig(height=5)
    ax.fill_between(df["date"], df["temp_min"], df["temp_max"], color=CLR_TEMP_POS, alpha=0.12, label="Min-Max range")
    ax.plot(df["date"], df["temp_mean"], color=CLR_ACCENT, linewidth=0.8, alpha=0.5)

    # Rolling mean for smoother visualization
    window = min(30, max(7, len(df) // 50))
    if len(df) > window:
        rolling_mean = df["temp_mean"].rolling(window=window, center=True).mean()
        ax.plot(df["date"], rolling_mean, color=CLR_ACCENT, linewidth=2.0, label=f"{window}-day rolling avg")

    # Overall trend
    x_num = (df["date"] - df["date"].iloc[0]).dt.days.values.astype(float)
    if len(x_num) > 30:
        coeffs = np.polyfit(x_num, df["temp_mean"].values, 1)
        trend_line = np.polyval(coeffs, x_num)
        ax.plot(df["date"], trend_line, color=CLR_TREND, linewidth=1.5, linestyle="--", label="Trend")
        years_span = (x_num[-1] - x_num[0]) / 365.25
        if years_span > 0:
            trend_per_decade = coeffs[0] * 365.25 * 10
            st.info(f"Temperature trend over this period: **{trend_per_decade:+.2f} degC/decade**")

    ax.set_ylabel("Temperature (degC)", color=CLR_TEXT_SEC, fontsize=10)
    ax.set_xlabel("Date", color=CLR_TEXT_SEC, fontsize=10)
    ax.set_title(f"Temperature History -- {escape(params['name'])}", color=CLR_TEXT, fontsize=12, fontweight="bold")
    ax.legend(fontsize=8, facecolor=CLR_BG, edgecolor=CLR_GRID, labelcolor=CLR_TEXT_SEC)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── Precipitation chart ──
    st.markdown(f"#### Precipitation History -- {escape(params['name'])}")

    fig2, ax2 = _new_fig(height=4)
    ax2.bar(df["date"], df["precip"], color=CLR_PRECIP, alpha=0.5, width=max(1, len(df) // 500))

    if len(df) > window:
        rolling_precip = df["precip"].rolling(window=window, center=True).mean()
        ax2.plot(df["date"], rolling_precip, color=CLR_PRECIP, linewidth=2.0, label=f"{window}-day rolling avg")

    ax2.set_ylabel("Precipitation (mm)", color=CLR_TEXT_SEC, fontsize=10)
    ax2.set_xlabel("Date", color=CLR_TEXT_SEC, fontsize=10)
    ax2.set_title(f"Daily Precipitation -- {escape(params['name'])}", color=CLR_TEXT, fontsize=12, fontweight="bold")
    ax2.legend(fontsize=8, facecolor=CLR_BG, edgecolor=CLR_GRID, labelcolor=CLR_TEXT_SEC)
    fig2.tight_layout()
    st.pyplot(fig2)
    plt.close(fig2)

    # ── Monthly averages ──
    st.markdown("#### Monthly Climate Summary")
    monthly = df.groupby("month").agg(
        avg_temp=("temp_mean", "mean"),
        avg_max=("temp_max", "mean"),
        avg_min=("temp_min", "mean"),
        avg_precip=("precip", "mean"),
        total_precip=("precip", "sum"),
    ).reset_index()

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    if len(monthly) > 0:
        fig3, (ax3a, ax3b) = _new_fig(rows=1, cols=2, height=4, width=12)

        x = np.arange(len(monthly))
        ax3a.bar(x, monthly["avg_max"], width=0.35, color=CLR_TEMP_POS, alpha=0.7, label="Avg Max")
        ax3a.bar(x + 0.35, monthly["avg_min"], width=0.35, color=CLR_TEMP_NEG, alpha=0.7, label="Avg Min")
        ax3a.set_xticks(x + 0.175)
        labels_temp = [month_names[m - 1] if m <= 12 else str(m) for m in monthly["month"]]
        ax3a.set_xticklabels(labels_temp, fontsize=7)
        ax3a.set_ylabel("Temperature (degC)", color=CLR_TEXT_SEC, fontsize=9)
        ax3a.set_title("Monthly Avg Temperatures", color=CLR_TEXT, fontsize=10, fontweight="bold")
        ax3a.legend(fontsize=7, facecolor=CLR_BG, edgecolor=CLR_GRID, labelcolor=CLR_TEXT_SEC)

        ax3b.bar(x, monthly["avg_precip"], color=CLR_PRECIP, alpha=0.7)
        labels_precip = [month_names[m - 1] if m <= 12 else str(m) for m in monthly["month"]]
        ax3b.set_xticks(x)
        ax3b.set_xticklabels(labels_precip, fontsize=7)
        ax3b.set_ylabel("Avg Daily Precip (mm)", color=CLR_TEXT_SEC, fontsize=9)
        ax3b.set_title("Monthly Avg Precipitation", color=CLR_TEXT, fontsize=10, fontweight="bold")

        fig3.tight_layout()
        st.pyplot(fig3)
        plt.close(fig3)

    # ── Preset locations map ──
    _render_preset_map(highlight=params["name"])

    # ── Data table and download ──
    with st.expander(f"Climate Data Table ({len(df)} days)", expanded=False):
        st.dataframe(
            df[["date", "temp_max", "temp_min", "temp_mean", "precip"]].rename(columns={
                "date": "Date", "temp_max": "Max Temp (degC)",
                "temp_min": "Min Temp (degC)", "temp_mean": "Mean Temp (degC)",
                "precip": "Precipitation (mm)",
            }),
            width="stretch", hide_index=True,
        )

    csv_buf = io.StringIO()
    df[["date", "temp_max", "temp_min", "temp_mean", "precip"]].to_csv(csv_buf, index=False)
    st.download_button(
        "Download Climate History (CSV)", data=csv_buf.getvalue(),
        file_name=f"climate_history_{params['name'].replace(' ', '_').lower()}.csv",
        mime="text/csv", key="clim_hist_csv",
    )


# ═══════════════════════════════════════════
# FOLIUM MAP OF PRESET LOCATIONS
# ═══════════════════════════════════════════
def _render_preset_map(highlight: str = None):
    """Render a folium map showing all climate-sensitive preset locations."""
    st.markdown("#### Climate-Sensitive Locations")

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")

    for name, (lat, lon) in CLIMATE_PRESETS.items():
        desc = PRESET_DESCRIPTIONS.get(name, "")
        icon_name = PRESET_ICONS.get(name, "info-sign")
        is_highlight = (highlight == name)

        popup_html = (
            f'<div style="min-width:180px;font-family:sans-serif;">'
            f'<b style="color:#06b6d4;font-size:13px;">{escape(name)}</b><br>'
            f'<span style="font-size:11px;color:#555;">{escape(desc)}</span><br>'
            f'<span style="font-size:10px;color:#888;">Lat: {lat:.1f}, Lon: {lon:.1f}</span>'
            f'</div>'
        )

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=escape(name),
            icon=folium.Icon(
                color="red" if is_highlight else "blue",
                icon=icon_name,
                prefix="fa",
            ),
        ).add_to(m)

        # Circle for visual emphasis
        folium.CircleMarker(
            location=[lat, lon],
            radius=10 if is_highlight else 6,
            color="#ef4444" if is_highlight else CLR_ACCENT,
            fill=True,
            fill_color="#ef4444" if is_highlight else CLR_ACCENT,
            fill_opacity=0.4 if is_highlight else 0.2,
            weight=2,
        ).add_to(m)

    map_html = m._repr_html_()
    components.html(map_html, height=420)


# ═══════════════════════════════════════════
# MAIN RENDER FUNCTION
# ═══════════════════════════════════════════
def render_climate_monitor_tab():
    """Main render function for the Climate Change Monitor tab."""

    # ── Header ──
    st.markdown("""
    <div class="tab-header emerald">
        <h4>Climate Change Monitor</h4>
        <p>Track atmospheric CO2 levels, global temperature anomalies, and historical climate data
        for climate-sensitive locations &mdash; powered by global-warming.org and Open-Meteo.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Mode selector ──
    mode = st.radio(
        "Select Dashboard",
        ["CO2 Levels", "Temperature Anomaly", "Climate History"],
        horizontal=True,
        key="clim_mode",
    )

    st.markdown("---")

    # ── Render selected mode ──
    if mode == "CO2 Levels":
        _render_co2_levels()
    elif mode == "Temperature Anomaly":
        _render_temperature_anomaly()
    elif mode == "Climate History":
        _render_climate_history()
