"""
Climate Forecast & Seasonal Prediction module for TerraScout AI.
16-day forecast, hourly detail, historical averages, temperature anomaly,
extreme weather alerts, and comfort index. Uses Open-Meteo free APIs only.
"""
import streamlit as st
import requests
import json
import math
import io
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ── Theme Colors ──────────────────────────────────────────────
CLR_BG, CLR_SURFACE, CLR_CARD = "#0a0e1a", "#111827", "#1a2235"
CLR_BORDER, CLR_TEXT, CLR_TEXT_SEC = "#2a3550", "#e8ecf4", "#8b97b0"
CLR_ACCENT, CLR_GRID = "#06b6d4", "#2a3550"
CLR_TMAX, CLR_TMIN, CLR_PRECIP = "#ef4444", "#3b82f6", "#8b5cf6"
CLR_WIND, CLR_COMFORT = "#f59e0b", "#10b981"

# ── WMO Weather Codes ────────────────────────────────────────
WMO_CODES = {
    0: ("Clear sky", "\u2600\ufe0f"), 1: ("Mainly clear", "\U0001f324\ufe0f"),
    2: ("Partly cloudy", "\u26c5"), 3: ("Overcast", "\u2601\ufe0f"),
    45: ("Fog", "\U0001f32b\ufe0f"), 48: ("Rime fog", "\U0001f32b\ufe0f"),
    51: ("Light drizzle", "\U0001f326\ufe0f"), 53: ("Moderate drizzle", "\U0001f326\ufe0f"),
    55: ("Dense drizzle", "\U0001f327\ufe0f"), 56: ("Freezing drizzle", "\U0001f327\ufe0f"),
    57: ("Heavy freezing drizzle", "\U0001f327\ufe0f"),
    61: ("Slight rain", "\U0001f327\ufe0f"), 63: ("Moderate rain", "\U0001f327\ufe0f"),
    65: ("Heavy rain", "\U0001f327\ufe0f"), 66: ("Freezing rain", "\U0001f327\ufe0f"),
    67: ("Heavy freezing rain", "\U0001f327\ufe0f"),
    71: ("Slight snow", "\U0001f328\ufe0f"), 73: ("Moderate snow", "\u2744\ufe0f"),
    75: ("Heavy snow", "\u2744\ufe0f"), 77: ("Snow grains", "\u2744\ufe0f"),
    80: ("Slight showers", "\U0001f326\ufe0f"), 81: ("Moderate showers", "\U0001f327\ufe0f"),
    82: ("Violent showers", "\u26c8\ufe0f"), 85: ("Snow showers", "\U0001f328\ufe0f"),
    86: ("Heavy snow showers", "\u2744\ufe0f"), 95: ("Thunderstorm", "\u26a1"),
    96: ("Thunderstorm + hail", "\u26a1\u2744\ufe0f"),
    99: ("Thunderstorm + heavy hail", "\u26a1\u2744\ufe0f"),
}
MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def _wmo_emoji(code: int) -> str:
    return WMO_CODES.get(code, ("Unknown", "\u2753"))[1]

# ── Chart Helpers ─────────────────────────────────────────────
def _style_ax(ax):
    ax.set_facecolor(CLR_SURFACE)
    ax.grid(True, color=CLR_GRID, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(axis="both", colors=CLR_TEXT_SEC, labelsize=8)
    for s in ax.spines.values():
        s.set_color(CLR_GRID)

def _new_fig(rows=1, cols=1, h=4.5, w=10):
    fig, axes = plt.subplots(rows, cols, figsize=(w, h))
    fig.patch.set_facecolor(CLR_BG)
    for ax in ([axes] if rows == 1 and cols == 1 else
               axes.flat if hasattr(axes, "flat") else [axes]):
        _style_ax(ax)
    return fig, axes

def _show_fig(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    buf.seek(0)
    st.image(buf, use_container_width=True)
    plt.close(fig)

def _legend(ax):
    ax.legend(facecolor=CLR_CARD, edgecolor=CLR_BORDER, labelcolor=CLR_TEXT_SEC, fontsize=8)

def _card(text, unsafe=True):
    st.markdown(text, unsafe_allow_html=unsafe)

def _safe(vals, default=float("nan")):
    return [v if v is not None else default for v in vals]

# ── API Functions (all cached, timeout=10, try/except) ────────
@st.cache_data(ttl=900)
def _fetch_16day(lat: float, lon: float) -> dict | None:
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 16,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,"
                     "wind_speed_10m_max,precipitation_probability_max,weathercode"})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

@st.cache_data(ttl=900)
def _fetch_hourly(lat: float, lon: float) -> dict | None:
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_hours": 48,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,cloud_cover"})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

@st.cache_data(ttl=900)
def _fetch_archive(lat: float, lon: float, year: int = 2023) -> dict | None:
    try:
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=10, params={
            "latitude": lat, "longitude": lon, "timezone": "auto",
            "start_date": f"{year}-01-01", "end_date": f"{year}-12-31",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum"})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

@st.cache_data(ttl=900)
def _fetch_comfort_hourly(lat: float, lon: float) -> dict | None:
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
            "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": 16,
            "hourly": "relative_humidity_2m,wind_speed_10m"})
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

# ── Computation Helpers ───────────────────────────────────────
def _monthly_avgs(data: dict) -> list[dict]:
    daily = data.get("daily", {})
    dates, tmax, tmin = daily.get("time",[]), daily.get("temperature_2m_max",[]), daily.get("temperature_2m_min",[])
    precip = daily.get("precipitation_sum", [])
    buckets = {m: {"tx":[],"tn":[],"p":[]} for m in range(1,13)}
    for i, d in enumerate(dates):
        try: mo = int(d.split("-")[1])
        except (IndexError, ValueError): continue
        if i < len(tmax) and tmax[i] is not None: buckets[mo]["tx"].append(tmax[i])
        if i < len(tmin) and tmin[i] is not None: buckets[mo]["tn"].append(tmin[i])
        if i < len(precip) and precip[i] is not None: buckets[mo]["p"].append(precip[i])
    results = []
    for m in range(1, 13):
        b = buckets[m]
        results.append({
            "month": m, "name": MONTH_NAMES[m-1],
            "avg_tmax": round(sum(b["tx"])/len(b["tx"]),1) if b["tx"] else None,
            "avg_tmin": round(sum(b["tn"])/len(b["tn"]),1) if b["tn"] else None,
            "total_precip": round(sum(b["p"]),1) if b["p"] else 0,
        })
    return results

def _comfort_score(temp, hum, wind):
    t_s = max(0, 10 - abs(temp - 22) * 0.4)
    h_s = max(0, 10 - abs(hum - 50) * 0.1)
    w_s = min(10, wind * 0.8) if wind <= 12 else max(0, 10 - (wind - 12) * 0.2)
    return round(min(10, max(0, t_s*0.50 + h_s*0.25 + w_s*0.25)), 1)

def _find_extremes(data: dict) -> list[dict]:
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    tmax, tmin = daily.get("temperature_2m_max",[]), daily.get("temperature_2m_min",[])
    prec, wind = daily.get("precipitation_sum",[]), daily.get("wind_speed_10m_max",[])
    codes = daily.get("weathercode", [])
    alerts = []
    for i, d in enumerate(dates):
        day_a = []
        if i < len(tmax) and tmax[i] is not None and tmax[i] > 35:
            day_a.append({"severity":"danger","icon":"\U0001f525","message":f"Extreme heat: {tmax[i]:.1f}\u00b0C"})
        if i < len(tmin) and tmin[i] is not None and tmin[i] < -10:
            day_a.append({"severity":"danger","icon":"\u2744\ufe0f","message":f"Extreme cold: {tmin[i]:.1f}\u00b0C"})
        if i < len(prec) and prec[i] is not None and prec[i] > 20:
            sev = "danger" if prec[i] > 50 else "warning"
            day_a.append({"severity":sev,"icon":"\U0001f327\ufe0f","message":f"Heavy precipitation: {prec[i]:.1f}mm"})
        if i < len(wind) and wind[i] is not None and wind[i] > 60:
            sev = "danger" if wind[i] > 90 else "warning"
            day_a.append({"severity":sev,"icon":"\U0001f32c\ufe0f","message":f"Strong wind: {wind[i]:.1f}km/h"})
        if i < len(codes) and codes[i] is not None and codes[i] >= 95:
            day_a.append({"severity":"warning","icon":"\u26a1","message":"Thunderstorm expected"})
        if day_a:
            alerts.append({"date": d, "alerts": day_a})
    return alerts

# ══════════════════════════════════════════════════════════════
# SECTION 1: 16-Day Forecast
# ══════════════════════════════════════════════════════════════
def _render_16day(lat, lon):
    st.markdown("### \U0001f4c5 16-Day Weather Forecast")
    data = _fetch_16day(lat, lon)
    if not data:
        st.error("Failed to fetch 16-day forecast."); return None
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    tmax, tmin = daily.get("temperature_2m_max",[]), daily.get("temperature_2m_min",[])
    prec, wind = daily.get("precipitation_sum",[]), daily.get("wind_speed_10m_max",[])
    prob, codes = daily.get("precipitation_probability_max",[]), daily.get("weathercode",[])
    if not dates:
        st.warning("No forecast data available."); return None
    # Weather icon cards
    parts = []
    for i, d in enumerate(dates):
        dt = datetime.strptime(d, "%Y-%m-%d")
        em = _wmo_emoji(codes[i]) if i < len(codes) else "\u2753"
        tx = f"{tmax[i]:.0f}" if i<len(tmax) and tmax[i] is not None else "--"
        tn = f"{tmin[i]:.0f}" if i<len(tmin) and tmin[i] is not None else "--"
        pr = f"{prec[i]:.1f}" if i<len(prec) and prec[i] is not None else "0.0"
        pb = f"{prob[i]:.0f}" if i<len(prob) and prob[i] is not None else "--"
        parts.append(
            f'<div style="min-width:95px;background:{CLR_CARD};border:1px solid {CLR_BORDER};'
            f'border-radius:8px;padding:8px 6px;text-align:center;flex-shrink:0;">'
            f'<div style="color:{CLR_TEXT_SEC};font-size:11px;">{dt.strftime("%a %b %d")}</div>'
            f'<div style="font-size:28px;margin:4px 0;">{em}</div>'
            f'<div style="color:{CLR_TMAX};font-weight:bold;font-size:14px;">{tx}\u00b0</div>'
            f'<div style="color:{CLR_TMIN};font-size:12px;">{tn}\u00b0</div>'
            f'<div style="color:{CLR_PRECIP};font-size:10px;margin-top:4px;">'
            f'\U0001f4a7 {pr}mm ({pb}%)</div></div>')
    _card(f'<div style="display:flex;gap:8px;overflow-x:auto;padding:8px 0;">{"".join(parts)}</div>')
    pd_dates = [datetime.strptime(d, "%Y-%m-%d") for d in dates]
    # Temperature chart
    st.markdown("#### Temperature Trend (\u00b0C)")
    fig, ax = _new_fig(h=4)
    ax.plot(pd_dates, _safe(tmax), color=CLR_TMAX, lw=2, marker="o", ms=4, label="Max Temp")
    ax.plot(pd_dates, _safe(tmin), color=CLR_TMIN, lw=2, marker="o", ms=4, label="Min Temp")
    ax.fill_between(pd_dates, _safe(tmin), _safe(tmax), color=CLR_ACCENT, alpha=0.1)
    ax.set_ylabel("Temperature (\u00b0C)", color=CLR_TEXT_SEC, fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30); _legend(ax); fig.tight_layout(); _show_fig(fig)
    # Precipitation chart
    st.markdown("#### Precipitation (mm)")
    fig, ax = _new_fig(h=3.5)
    vp = _safe(prec, 0)
    ax.bar(pd_dates, vp, color=[CLR_PRECIP if v<=20 else CLR_TMAX for v in vp], width=0.6, alpha=0.85)
    ax.axhline(y=20, color=CLR_TMAX, ls="--", lw=0.8, alpha=0.6, label="Heavy rain (20mm)")
    ax.set_ylabel("Precipitation (mm)", color=CLR_TEXT_SEC, fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30); _legend(ax); fig.tight_layout(); _show_fig(fig)
    # Wind chart
    st.markdown("#### Max Wind Speed (km/h)")
    fig, ax = _new_fig(h=3.5)
    vw = _safe(wind, 0)
    ax.fill_between(pd_dates, 0, vw, color=CLR_WIND, alpha=0.3)
    ax.plot(pd_dates, vw, color=CLR_WIND, lw=2, marker="D", ms=3)
    ax.axhline(y=60, color=CLR_TMAX, ls="--", lw=0.8, alpha=0.6, label="Strong wind (60km/h)")
    ax.set_ylabel("Wind Speed (km/h)", color=CLR_TEXT_SEC, fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30); _legend(ax); fig.tight_layout(); _show_fig(fig)
    return data

# ══════════════════════════════════════════════════════════════
# SECTION 2: Hourly Detail (48h)
# ══════════════════════════════════════════════════════════════
def _render_hourly(lat, lon):
    st.markdown("### \u23f0 48-Hour Hourly Detail")
    data = _fetch_hourly(lat, lon)
    if not data:
        st.error("Failed to fetch hourly data."); return
    h = data.get("hourly", {})
    times = h.get("time",[])
    if not times:
        st.warning("No hourly data available."); return
    pts = [datetime.strptime(t[:16], "%Y-%m-%dT%H:%M") for t in times]
    fig, (ax1, ax2) = _new_fig(rows=2, cols=1, h=7)
    # Top: temp + wind
    ax1.plot(pts, _safe(h.get("temperature_2m",[])), color=CLR_TMAX, lw=1.5, label="Temp (\u00b0C)")
    ax1t = ax1.twinx(); _style_ax(ax1t)
    ax1t.plot(pts, _safe(h.get("wind_speed_10m",[])), color=CLR_WIND, lw=1.2, ls="--", label="Wind (km/h)")
    ax1.set_ylabel("Temperature (\u00b0C)", color=CLR_TEXT_SEC, fontsize=9)
    ax1t.set_ylabel("Wind (km/h)", color=CLR_TEXT_SEC, fontsize=9)
    l1, lb1 = ax1.get_legend_handles_labels()
    l2, lb2 = ax1t.get_legend_handles_labels()
    ax1.legend(l1+l2, lb1+lb2, facecolor=CLR_CARD, edgecolor=CLR_BORDER,
               labelcolor=CLR_TEXT_SEC, fontsize=7, loc="upper right")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d %Hh"))
    ax1.set_title("Temperature & Wind", color=CLR_TEXT, fontsize=10, pad=8)
    # Bottom: humidity, clouds, precip
    ax2.plot(pts, _safe(h.get("relative_humidity_2m",[])), color=CLR_ACCENT, lw=1.5, label="Humidity (%)")
    ax2.plot(pts, _safe(h.get("cloud_cover",[])), color=CLR_TEXT_SEC, lw=1, ls=":", alpha=0.7, label="Clouds (%)")
    ax2t = ax2.twinx(); _style_ax(ax2t)
    ax2t.bar(pts, _safe(h.get("precipitation",[]), 0), color=CLR_PRECIP, alpha=0.6, width=0.03, label="Precip (mm)")
    ax2.set_ylabel("Percentage (%)", color=CLR_TEXT_SEC, fontsize=9)
    ax2t.set_ylabel("Precipitation (mm)", color=CLR_TEXT_SEC, fontsize=9)
    l3, lb3 = ax2.get_legend_handles_labels()
    l4, lb4 = ax2t.get_legend_handles_labels()
    ax2.legend(l3+l4, lb3+lb4, facecolor=CLR_CARD, edgecolor=CLR_BORDER,
               labelcolor=CLR_TEXT_SEC, fontsize=7, loc="upper right")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%b %d %Hh"))
    ax2.set_title("Humidity, Clouds & Precipitation", color=CLR_TEXT, fontsize=10, pad=8)
    fig.tight_layout(); _show_fig(fig)

# ══════════════════════════════════════════════════════════════
# SECTION 3: Historical Monthly Averages
# ══════════════════════════════════════════════════════════════
def _render_historical(lat, lon):
    st.markdown("### \U0001f4ca Historical Monthly Averages (2023)")
    data = _fetch_archive(lat, lon, 2023)
    if not data:
        st.error("Failed to fetch historical data."); return None
    if "error" in data:
        st.error(f"Archive error: {data.get('reason','Unknown')}"); return None
    monthly = _monthly_avgs(data)
    # Summary cards
    cols = st.columns(6)
    for i, m in enumerate(monthly):
        tx = f"{m['avg_tmax']}\u00b0" if m["avg_tmax"] is not None else "--"
        tn = f"{m['avg_tmin']}\u00b0" if m["avg_tmin"] is not None else "--"
        cols[i%6].markdown(
            f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};border-radius:8px;'
            f'padding:8px;text-align:center;margin-bottom:8px;">'
            f'<div style="color:{CLR_ACCENT};font-weight:bold;font-size:13px;">{m["name"]}</div>'
            f'<div style="color:{CLR_TMAX};font-size:12px;">{tx}</div>'
            f'<div style="color:{CLR_TMIN};font-size:12px;">{tn}</div>'
            f'<div style="color:{CLR_PRECIP};font-size:10px;">\U0001f4a7 {m["total_precip"]}mm</div></div>',
            unsafe_allow_html=True)
    # Temperature bar chart
    fig, ax = _new_fig(h=4)
    mi = list(range(12)); bw = 0.35
    tx_v = [m["avg_tmax"] or 0 for m in monthly]
    tn_v = [m["avg_tmin"] or 0 for m in monthly]
    ax.bar([i-bw/2 for i in mi], tx_v, width=bw, color=CLR_TMAX, alpha=0.8, label="Avg Max")
    ax.bar([i+bw/2 for i in mi], tn_v, width=bw, color=CLR_TMIN, alpha=0.8, label="Avg Min")
    ax.set_xticks(mi); ax.set_xticklabels(MONTH_NAMES, fontsize=8, color=CLR_TEXT_SEC)
    ax.set_ylabel("Temperature (\u00b0C)", color=CLR_TEXT_SEC, fontsize=10)
    _legend(ax); fig.tight_layout(); _show_fig(fig)
    # Precipitation bar chart
    st.markdown("#### Monthly Precipitation (mm)")
    fig, ax = _new_fig(h=3.5)
    pv = [m["total_precip"] for m in monthly]
    ax.bar(mi, pv, color=[CLR_PRECIP if v<=100 else CLR_TMAX for v in pv], alpha=0.85)
    ax.set_xticks(mi); ax.set_xticklabels(MONTH_NAMES, fontsize=8, color=CLR_TEXT_SEC)
    ax.set_ylabel("Precipitation (mm)", color=CLR_TEXT_SEC, fontsize=10)
    fig.tight_layout(); _show_fig(fig)
    return monthly

# ══════════════════════════════════════════════════════════════
# SECTION 4: Temperature Anomaly
# ══════════════════════════════════════════════════════════════
def _render_anomaly(lat, lon, fc_data, hist_monthly):
    st.markdown("### \U0001f321\ufe0f Temperature Anomaly Analysis")
    if not fc_data:
        st.warning("Forecast data unavailable."); return
    if not hist_monthly:
        st.warning("Historical data unavailable."); return
    daily = fc_data.get("daily",{})
    dates = daily.get("time",[])
    tmax, tmin = daily.get("temperature_2m_max",[]), daily.get("temperature_2m_min",[])
    if not dates:
        st.warning("No forecast dates."); return
    hm = {m["month"]: m for m in hist_monthly}
    anom = []
    for i, d in enumerate(dates):
        try: dt = datetime.strptime(d, "%Y-%m-%d"); mo = dt.month
        except ValueError: continue
        h = hm.get(mo)
        if not h: continue
        ftx = tmax[i] if i<len(tmax) and tmax[i] is not None else None
        ftn = tmin[i] if i<len(tmin) and tmin[i] is not None else None
        amx = (ftx - h["avg_tmax"]) if ftx is not None and h["avg_tmax"] is not None else None
        amn = (ftn - h["avg_tmin"]) if ftn is not None and h["avg_tmin"] is not None else None
        anom.append({"dt": dt, "amx": amx or 0, "amn": amn or 0})
    if not anom:
        st.info("Cannot compute anomalies."); return
    # Anomaly bar chart
    fig, ax = _new_fig(h=4)
    ad = [a["dt"] for a in anom]
    amx_v = [a["amx"] for a in anom]; amn_v = [a["amn"] for a in anom]
    bw = timedelta(hours=8)
    ax.bar([d-bw for d in ad], amx_v, width=bw, alpha=0.8, label="Max Anomaly",
           color=[CLR_TMAX if v>=0 else CLR_TMIN for v in amx_v])
    ax.bar(ad, amn_v, width=bw, alpha=0.5, label="Min Anomaly",
           color=[CLR_TMAX if v>=0 else CLR_TMIN for v in amn_v])
    ax.axhline(y=0, color=CLR_TEXT_SEC, lw=0.8)
    ax.set_ylabel("Anomaly (\u00b0C)", color=CLR_TEXT_SEC, fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)
    ax.set_title("Forecast vs Historical Average", color=CLR_TEXT, fontsize=10, pad=8)
    _legend(ax); fig.tight_layout(); _show_fig(fig)
    # Summary cards
    avg_mx = sum(amx_v)/len(amx_v); avg_mn = sum(amn_v)/len(amn_v)
    max_dev = max(amx_v, key=abs) if amx_v else 0
    c1, c2, c3 = st.columns(3)
    for col, label, val in [(c1,"Avg Max Anomaly",avg_mx),(c2,"Avg Min Anomaly",avg_mn),(c3,"Max Deviation",max_dev)]:
        sgn = "+" if val >= 0 else ""
        clr = CLR_TMAX if val >= 0 else CLR_TMIN
        col.markdown(
            f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};border-radius:10px;'
            f'padding:16px;text-align:center;"><div style="color:{CLR_TEXT_SEC};font-size:12px;">'
            f'{label}</div><div style="color:{clr};font-size:24px;font-weight:bold;">'
            f'{sgn}{val:.1f}\u00b0C</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# SECTION 5: Extreme Weather Alerts
# ══════════════════════════════════════════════════════════════
def _render_alerts(fc_data):
    st.markdown("### \u26a0\ufe0f Extreme Weather Alerts")
    if not fc_data:
        st.warning("Forecast data unavailable."); return
    alerts = _find_extremes(fc_data)
    if not alerts:
        _card(f'<div style="background:#064e3b;border:1px solid #10b981;border-radius:10px;'
              f'padding:20px;text-align:center;"><div style="font-size:32px;">\u2705</div>'
              f'<div style="color:#10b981;font-size:16px;font-weight:bold;margin-top:8px;">'
              f'All Clear</div><div style="color:{CLR_TEXT_SEC};font-size:13px;margin-top:4px;">'
              f'No extreme conditions in 16-day forecast.</div></div>')
        return
    SEV = {"danger": ("#450a0a","#ef4444","#fca5a5","#ef4444","#fff"),
           "warning": ("#451a03","#f59e0b","#fcd34d","#f59e0b","#000")}
    total = sum(len(a["alerts"]) for a in alerts)
    dng = sum(1 for a in alerts for al in a["alerts"] if al["severity"]=="danger")
    wrn = total - dng
    parts = []
    if dng: parts.append(f'<span style="color:#ef4444;font-weight:bold;">{dng} DANGER</span>')
    if wrn: parts.append(f'<span style="color:#f59e0b;font-weight:bold;">{wrn} WARNING</span>')
    _card(f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};border-radius:8px;'
          f'padding:12px;margin-bottom:12px;"><span style="color:{CLR_TEXT};font-size:14px;">'
          f'\U0001f6a8 {total} alert(s) across {len(alerts)} day(s): '
          f'{" &bull; ".join(parts)}</span></div>')
    for ad in alerts:
        dl = datetime.strptime(ad["date"], "%Y-%m-%d").strftime("%A, %B %d")
        for al in ad["alerts"]:
            bg, brd, txt, bbg, btx = SEV.get(al["severity"], SEV["warning"])
            badge = al["severity"].upper()
            _card(f'<div style="background:{bg};border-left:4px solid {brd};border-radius:6px;'
                  f'padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;gap:12px;">'
                  f'<div style="font-size:24px;">{al["icon"]}</div><div style="flex:1;">'
                  f'<div style="color:{txt};font-weight:bold;font-size:13px;">{al["message"]}</div>'
                  f'<div style="color:{CLR_TEXT_SEC};font-size:11px;">{dl}</div></div>'
                  f'<div style="background:{bbg};color:{btx};padding:2px 8px;border-radius:4px;'
                  f'font-size:10px;font-weight:bold;">{badge}</div></div>')

# ══════════════════════════════════════════════════════════════
# SECTION 6: Comfort Index
# ══════════════════════════════════════════════════════════════
def _render_comfort(lat, lon, fc_data):
    st.markdown("### \U0001f3d6\ufe0f Outdoor Comfort Index")
    h_data = _fetch_comfort_hourly(lat, lon)
    if not fc_data or not h_data:
        st.warning("Insufficient data for comfort calculation."); return
    daily = fc_data.get("daily",{})
    dates = daily.get("time",[]); tmax = daily.get("temperature_2m_max",[])
    tmin = daily.get("temperature_2m_min",[])
    h = h_data.get("hourly",{}); ht = h.get("time",[]); hh = h.get("relative_humidity_2m",[])
    hw = h.get("wind_speed_10m",[])
    if not dates or not ht:
        st.warning("Insufficient data."); return
    # Aggregate hourly to daily
    d_hum, d_wind = {}, {}
    for i, t in enumerate(ht):
        dk = t[:10]
        d_hum.setdefault(dk, []); d_wind.setdefault(dk, [])
        if i < len(hh) and hh[i] is not None: d_hum[dk].append(hh[i])
        if i < len(hw) and hw[i] is not None: d_wind[dk].append(hw[i])
    scores = []
    for i, d in enumerate(dates):
        tx = tmax[i] if i<len(tmax) and tmax[i] is not None else 20
        tn = tmin[i] if i<len(tmin) and tmin[i] is not None else 10
        avg_t = (tx + tn) / 2
        hl = d_hum.get(d, []); avg_h = sum(hl)/len(hl) if hl else 50
        wl = d_wind.get(d, []); avg_w = sum(wl)/len(wl) if wl else 10
        scores.append({"date": d, "score": _comfort_score(avg_t, avg_h, avg_w),
                        "temp": avg_t, "hum": avg_h, "wind": avg_w})
    # Area chart
    pd_d = [datetime.strptime(s["date"], "%Y-%m-%d") for s in scores]
    sv = [s["score"] for s in scores]
    fig, ax = _new_fig(h=4)
    ax.fill_between(pd_d, 0, sv, color=CLR_COMFORT, alpha=0.25)
    ax.plot(pd_d, sv, color=CLR_COMFORT, lw=2.5, marker="o", ms=5, zorder=5)
    ax.axhspan(0, 3, color=CLR_TMAX, alpha=0.05)
    ax.axhspan(3, 6, color=CLR_WIND, alpha=0.05)
    ax.axhspan(6, 10, color=CLR_COMFORT, alpha=0.05)
    ax.set_ylim(0, 10.5)
    ax.set_ylabel("Comfort Score (0-10)", color=CLR_TEXT_SEC, fontsize=10)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)
    ax.text(pd_d[0], 1.5, "Poor", color=CLR_TMAX, fontsize=8, alpha=0.6)
    ax.text(pd_d[0], 4.5, "Moderate", color=CLR_WIND, fontsize=8, alpha=0.6)
    ax.text(pd_d[0], 8.0, "Comfortable", color=CLR_COMFORT, fontsize=8, alpha=0.6)
    ax.set_title("Daily Outdoor Comfort Score", color=CLR_TEXT, fontsize=10, pad=8)
    fig.tight_layout(); _show_fig(fig)
    # Comfort cards (first 8 days)
    st.markdown("#### Day-by-Day Comfort")
    cols = st.columns(4)
    for i in range(min(8, len(scores))):
        cs = scores[i]; col = cols[i%4]
        dl = datetime.strptime(cs["date"], "%Y-%m-%d").strftime("%a %b %d")
        if cs["score"] >= 7: sc, sl, se = CLR_COMFORT, "Great", "\U0001f60e"
        elif cs["score"] >= 4: sc, sl, se = CLR_WIND, "Fair", "\U0001f610"
        else: sc, sl, se = CLR_TMAX, "Poor", "\U0001f975"
        col.markdown(
            f'<div style="background:{CLR_CARD};border:1px solid {CLR_BORDER};border-radius:10px;'
            f'padding:10px;text-align:center;margin-bottom:8px;">'
            f'<div style="color:{CLR_TEXT_SEC};font-size:11px;">{dl}</div>'
            f'<div style="font-size:24px;margin:4px 0;">{se}</div>'
            f'<div style="color:{sc};font-size:20px;font-weight:bold;">{cs["score"]}</div>'
            f'<div style="color:{sc};font-size:10px;">{sl}</div>'
            f'<div style="color:{CLR_TEXT_SEC};font-size:9px;margin-top:4px;">'
            f'\U0001f321\ufe0f {cs["temp"]:.0f}\u00b0 \U0001f4a7 {cs["hum"]:.0f}% '
            f'\U0001f32c\ufe0f {cs["wind"]:.0f}km/h</div></div>', unsafe_allow_html=True)
    _card(f'<div style="color:{CLR_TEXT_SEC};font-size:11px;padding:8px 0;">'
          f'Comfort based on temperature (optimal 22\u00b0C), humidity (50%), '
          f'and wind (8-12 km/h). Score: 0 (worst) to 10 (best).</div>')

# ══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════
def render_climate_forecast_tab():
    """Main entry point for the Climate Forecast & Seasonal Prediction tab."""
    st.markdown("## \U0001f326\ufe0f Climate Forecast & Seasonal Prediction")
    _card(f'<div style="color:{CLR_TEXT_SEC};font-size:13px;margin-bottom:16px;">'
          f'16-day weather forecast, seasonal climate patterns, anomaly detection, '
          f'extreme weather alerts, and outdoor comfort analysis. '
          f'Powered by Open-Meteo free APIs.</div>')
    # Location input
    st.markdown("---")
    lc1, lc2, lc3 = st.columns([2, 1, 1])
    presets = {
        "Custom": (0.0, 0.0), "New York, USA": (40.71, -74.01),
        "London, UK": (51.51, -0.13), "Tokyo, Japan": (35.68, 139.69),
        "Sydney, Australia": (-33.87, 151.21), "Sao Paulo, Brazil": (-23.55, -46.63),
        "Cairo, Egypt": (30.04, 31.24), "Mumbai, India": (19.08, 72.88),
        "Moscow, Russia": (55.76, 37.62), "Nairobi, Kenya": (-1.29, 36.82),
        "Reykjavik, Iceland": (64.13, -21.90),
    }
    with lc1:
        sel = st.selectbox("Select a location", list(presets.keys()), key="climfc_preset_location")
    plat, plon = presets[sel]
    dlat, dlon = (41.90, 12.50) if sel == "Custom" else (plat, plon)
    with lc2:
        lat = st.number_input("Latitude", value=dlat, min_value=-90.0,
                              max_value=90.0, step=0.01, key="climfc_lat_input")
    with lc3:
        lon = st.number_input("Longitude", value=dlon, min_value=-180.0,
                              max_value=180.0, step=0.01, key="climfc_lon_input")
    _card(f'<div style="color:{CLR_TEXT_SEC};font-size:12px;">'
          f'\U0001f4cd Analyzing: {lat:.4f}\u00b0N, {lon:.4f}\u00b0E</div>')
    # Section selector
    st.markdown("---")
    sections = st.multiselect(
        "Select sections to display",
        ["16-Day Forecast", "48-Hour Hourly Detail", "Historical Monthly Averages",
         "Temperature Anomaly", "Extreme Weather Alerts", "Comfort Index"],
        default=["16-Day Forecast", "Extreme Weather Alerts", "Comfort Index"],
        key="climfc_section_selector")
    if not sections:
        st.info("Select at least one section."); return
    fc_data, hist_monthly = None, None
    # Section 1
    if "16-Day Forecast" in sections:
        st.markdown("---"); fc_data = _render_16day(lat, lon)
    # Ensure forecast data for dependent sections
    needs_fc = any(s in sections for s in ["Temperature Anomaly","Extreme Weather Alerts","Comfort Index"])
    if fc_data is None and needs_fc:
        fc_data = _fetch_16day(lat, lon)
    # Section 2
    if "48-Hour Hourly Detail" in sections:
        st.markdown("---"); _render_hourly(lat, lon)
    # Section 3
    if "Historical Monthly Averages" in sections:
        st.markdown("---"); hist_monthly = _render_historical(lat, lon)
    # Ensure historical for anomaly
    if hist_monthly is None and "Temperature Anomaly" in sections:
        hd = _fetch_archive(lat, lon, 2023)
        if hd and "error" not in hd:
            hist_monthly = _monthly_avgs(hd)
    # Section 4
    if "Temperature Anomaly" in sections:
        st.markdown("---"); _render_anomaly(lat, lon, fc_data, hist_monthly)
    # Section 5
    if "Extreme Weather Alerts" in sections:
        st.markdown("---"); _render_alerts(fc_data)
    # Section 6
    if "Comfort Index" in sections:
        st.markdown("---"); _render_comfort(lat, lon, fc_data)
    # Footer
    st.markdown("---")
    _card(f'<div style="color:{CLR_TEXT_SEC};font-size:11px;text-align:center;padding:8px 0;">'
          f'Data: <a href="https://open-meteo.com/" style="color:{CLR_ACCENT};">Open-Meteo</a> '
          f'free API. Models: ECMWF IFS, GFS, ICON. Archive: ERA5. Cache: 15 min.</div>')
