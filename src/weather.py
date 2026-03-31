"""
Weather tab module for Pocket GIS AI.
Uses Open-Meteo API for current conditions, 7-day forecast, and historical data.
"""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Rate limiting
try:
    from src.rate_limiter import rate_limiter, get_rate_limit_config
    from src.app_logger import log_api_call
except ImportError:
    rate_limiter = None
    log_api_call = lambda *args, **kwargs: None


# ---------------------------------------------------------------------------
# WMO Weather Code mapping: code -> (description, emoji)
# ---------------------------------------------------------------------------
WMO_CODES = {
    0:  ("Clear sky",        "\u2600\ufe0f"),
    1:  ("Mainly clear",     "\U0001f324\ufe0f"),
    2:  ("Partly cloudy",    "\u26c5"),
    3:  ("Overcast",         "\u2601\ufe0f"),
    45: ("Fog",              "\U0001f32b\ufe0f"),
    48: ("Rime fog",         "\U0001f32b\ufe0f"),
    51: ("Light drizzle",    "\U0001f326\ufe0f"),
    53: ("Moderate drizzle", "\U0001f326\ufe0f"),
    55: ("Dense drizzle",    "\U0001f327\ufe0f"),
    61: ("Slight rain",      "\U0001f327\ufe0f"),
    63: ("Moderate rain",    "\U0001f327\ufe0f"),
    65: ("Heavy rain",       "\U0001f327\ufe0f"),
    71: ("Slight snow",      "\U0001f328\ufe0f"),
    73: ("Moderate snow",    "\u2744\ufe0f"),
    75: ("Heavy snow",       "\u2744\ufe0f"),
    80: ("Slight showers",   "\U0001f326\ufe0f"),
    81: ("Moderate showers", "\U0001f327\ufe0f"),
    82: ("Violent showers",  "\u26c8\ufe0f"),
    95: ("Thunderstorm",     "\u26a1"),
    96: ("Thunderstorm + hail", "\u26a1\u2744\ufe0f"),
}


def _wmo_label(code: int) -> str:
    """Return 'emoji description' for a WMO weather code."""
    desc, emoji = WMO_CODES.get(code, ("Unknown", "\u2753"))
    return f"{emoji} {desc}"


# ---------------------------------------------------------------------------
# API helpers (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def search_location(query: str) -> list[dict]:
    """Geocoding search via Open-Meteo. Returns list of {name, lat, lon, country}."""
    # Rate limiting configuration
    if rate_limiter:
        api_config = get_rate_limit_config("open_meteo")
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": query, "count": 5}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return [
            {
                "name": r.get("name", ""),
                "lat": r["latitude"],
                "lon": r["longitude"],
                "country": r.get("country", ""),
            }
            for r in results
        ]
    except Exception:
        return []


@st.cache_data(ttl=600)
def get_forecast(lat: float, lng: float) -> dict | None:
    """Fetch current weather + 7-day forecast from Open-Meteo."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code,apparent_temperature,precipitation",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


@st.cache_data(ttl=600)
def get_historical(lat: float, lng: float, start_date: str, end_date: str) -> dict | None:
    """Fetch historical daily data from Open-Meteo Archive API."""
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lng,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Chart rendering
# ---------------------------------------------------------------------------

def render_weather_chart(
    dates: list[str],
    temps_max: list[float],
    temps_min: list[float],
    precip: list[float],
) -> plt.Figure:
    """
    Dual-axis chart: temperature lines (left) + precipitation bars (right).
    Dark-theme styling consistent with the app.
    """
    parsed_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]

    fig, ax1 = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#0a0e1a")
    ax1.set_facecolor("#0a0e1a")

    # Temperature lines
    ax1.plot(parsed_dates, temps_max, color="#06b6d4", linewidth=2, marker="o",
             markersize=4, label="Max Temp")
    ax1.plot(parsed_dates, temps_min, color="#38bdf8", linewidth=2, marker="o",
             markersize=4, label="Min Temp")
    ax1.set_ylabel("Temperature (\u00b0C)", color="#8b97b0", fontsize=10)
    ax1.tick_params(axis="y", colors="#8b97b0")
    ax1.tick_params(axis="x", colors="#8b97b0")

    # Precipitation bars on secondary axis
    ax2 = ax1.twinx()
    ax2.bar(parsed_dates, precip, color="rgba(6,182,212,0.27)", width=0.6, label="Precipitation")
    ax2.set_ylabel("Precipitation (mm)", color="#8b97b0", fontsize=10)
    ax2.tick_params(axis="y", colors="#8b97b0")

    # Grid
    ax1.grid(True, color="#2a3550", linewidth=0.5, alpha=0.7)
    ax1.set_axisbelow(True)

    # Spine colors
    for ax in (ax1, ax2):
        for spine in ax.spines.values():
            spine.set_color("#2a3550")

    # Date formatting
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)

    # Legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
               fontsize=8, facecolor="#0a0e1a", edgecolor="#2a3550",
               labelcolor="#8b97b0")

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render_weather_tab():
    """Entry point rendered inside a Streamlit tab."""

    # ---- Session state defaults ----
    if "weather_locations" not in st.session_state:
        st.session_state.weather_locations = []
    if "weather_selected_idx" not in st.session_state:
        st.session_state.weather_selected_idx = 0

    # ---- Header ----
    st.markdown("""
    <div class="tab-header amber">
        <h4>Weather Data</h4>
        <p>Current conditions, 7-day forecast, and historical weather data from Open-Meteo &mdash; free, no API key.</p>
    </div>
    """, unsafe_allow_html=True)
    search_col, btn_col = st.columns([3, 1])
    with search_col:
        query = st.text_input(
            "City / Location",
            placeholder="e.g. Rome, Milan, New York ...",
            key="weather_search_input",
        )
    with btn_col:
        st.markdown("<div style='height:1.65rem'></div>", unsafe_allow_html=True)  # spacer to align button
        search_clicked = st.button("Search", key="weather_search_btn", width="stretch")

    if search_clicked and query:
        results = search_location(query)
        st.session_state.weather_locations = results
        st.session_state.weather_selected_idx = 0
        if not results:
            st.warning("No locations found. Try a different search term.")

    locations = st.session_state.weather_locations

    if not locations:
        st.info("Enter a city name above and press Search to view weather data.")
        return

    # ---- Location selector ----
    options = [
        f"{loc['name']}, {loc['country']} ({loc['lat']:.2f}, {loc['lon']:.2f})"
        for loc in locations
    ]
    selected_label = st.selectbox("Select location", options, key="weather_loc_select")
    sel_idx = options.index(selected_label) if selected_label in options else 0
    loc = locations[sel_idx]
    lat, lng = loc["lat"], loc["lon"]

    # ---- Sub-tabs ----
    tab_current, tab_historical = st.tabs(["Current & Forecast", "Historical"])

    # ==================================================================
    # CURRENT & FORECAST
    # ==================================================================
    with tab_current:
        forecast = get_forecast(lat, lng)
        if forecast is None:
            st.error("Failed to fetch forecast data. Please try again later.")
            return

        current = forecast.get("current", {})
        daily = forecast.get("daily", {})

        # ---- Current weather card ----
        code = current.get("weather_code", 0)
        desc, emoji = WMO_CODES.get(code, ("Unknown", "\u2753"))
        temp = current.get("temperature_2m", "--")
        feels = current.get("apparent_temperature", "--")
        humidity = current.get("relative_humidity_2m", "--")
        wind = current.get("wind_speed_10m", "--")
        precip_now = current.get("precipitation", 0)

        st.markdown(f"""
        <div class="glass-card" style="padding:1.5rem 2rem; margin-bottom:1rem;">
            <div style="display:flex; align-items:center; gap:1rem; flex-wrap:wrap;">
                <span style="font-size:3rem;">{emoji}</span>
                <div>
                    <h2 style="margin:0; color:#e8ecf4; font-size:2rem;">{temp}\u00b0C</h2>
                    <p style="margin:0.2rem 0 0; color:#8b97b0; font-size:1rem;">{desc}</p>
                </div>
                <div style="margin-left:auto; text-align:right;">
                    <p style="margin:0; color:#8b97b0;">Feels like <strong style="color:#38bdf8;">{feels}\u00b0C</strong></p>
                    <p style="margin:0; color:#8b97b0;">Humidity <strong style="color:#38bdf8;">{humidity}%</strong></p>
                    <p style="margin:0; color:#8b97b0;">Wind <strong style="color:#38bdf8;">{wind} km/h</strong></p>
                    <p style="margin:0; color:#8b97b0;">Precip <strong style="color:#38bdf8;">{precip_now} mm</strong></p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ---- 7-day forecast table ----
        st.markdown("#### 7-Day Forecast")
        if daily:
            dates = daily.get("time", [])
            codes = daily.get("weather_code", [])
            t_max = daily.get("temperature_2m_max", [])
            t_min = daily.get("temperature_2m_min", [])
            p_sum = daily.get("precipitation_sum", [])
            w_max = daily.get("wind_speed_10m_max", [])

            df_forecast = pd.DataFrame({
                "Date": dates,
                "Condition": [_wmo_label(c) for c in codes],
                "Max (\u00b0C)": t_max,
                "Min (\u00b0C)": t_min,
                "Precip (mm)": p_sum,
                "Wind max (km/h)": w_max,
            })
            st.dataframe(df_forecast, width="stretch", hide_index=True)

            # ---- Temperature chart ----
            st.markdown("#### Temperature & Precipitation")
            fig = render_weather_chart(dates, t_max, t_min, p_sum)
            st.pyplot(fig)
            plt.close(fig)

    # ==================================================================
    # HISTORICAL
    # ==================================================================
    with tab_historical:
        st.markdown("#### Historical Weather Data")

        default_end = datetime.now().date() - timedelta(days=1)
        default_start = default_end - timedelta(days=29)

        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input("Start date", value=default_start, key="weather_hist_start")
        with date_col2:
            end_date = st.date_input("End date", value=default_end, key="weather_hist_end")

        fetch_clicked = st.button("Fetch Historical", key="weather_hist_btn", width="stretch")

        if fetch_clicked:
            if start_date >= end_date:
                st.error("Start date must be before end date.")
            else:
                with st.spinner("Fetching historical data..."):
                    hist = get_historical(
                        lat, lng,
                        start_date.strftime("%Y-%m-%d"),
                        end_date.strftime("%Y-%m-%d"),
                    )

                if hist is None:
                    st.error("Failed to fetch historical data. Ensure the date range is within the archive (not future dates).")
                else:
                    hist_daily = hist.get("daily", {})
                    h_dates = hist_daily.get("time", [])
                    h_tmax = hist_daily.get("temperature_2m_max", [])
                    h_tmin = hist_daily.get("temperature_2m_min", [])
                    h_prec = hist_daily.get("precipitation_sum", [])

                    if h_dates:
                        # Store in session for persistence across reruns
                        st.session_state.weather_hist_data = {
                            "dates": h_dates,
                            "tmax": h_tmax,
                            "tmin": h_tmin,
                            "precip": h_prec,
                        }

        # Display persisted historical results
        if "weather_hist_data" in st.session_state:
            hd = st.session_state.weather_hist_data
            h_dates = hd["dates"]
            h_tmax = hd["tmax"]
            h_tmin = hd["tmin"]
            h_prec = hd["precip"]

            fig_hist = render_weather_chart(h_dates, h_tmax, h_tmin, h_prec)
            st.pyplot(fig_hist)
            plt.close(fig_hist)

            df_hist = pd.DataFrame({
                "Date": h_dates,
                "Max (\u00b0C)": h_tmax,
                "Min (\u00b0C)": h_tmin,
                "Precipitation (mm)": h_prec,
            })
            st.dataframe(df_hist, width="stretch", hide_index=True)

            # CSV download
            csv_buf = io.StringIO()
            df_hist.to_csv(csv_buf, index=False)
            st.download_button(
                "Download CSV",
                data=csv_buf.getvalue(),
                file_name=f"weather_history_{h_dates[0]}_{h_dates[-1]}.csv",
                mime="text/csv",
                key="weather_hist_download",
            )
