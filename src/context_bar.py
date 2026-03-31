"""
Context Bar - Persistent location context bar for TerraScout AI.
Displayed above every module page to show the current shared location
and key metrics at a glance. Ops-center style with monospace font,
LED pulse, and confidence indicator.
"""

import html as html_module
import streamlit as st

from src.location_context import get_location, has_location, get_short_name


def render_context_bar():
    """Render the persistent context bar above module content.

    Shows: [LED] LOCATION_NAME | coords | elev | temp | AQI | Score | Confidence
    If no location is set, shows a prompt to set one.
    """
    if not has_location():
        cb1, cb2 = st.columns([5, 1])
        with cb1:
            st.markdown(
                '<div class="context-bar-empty">'
                '<span style="color:#5a7090;">NO LOCATION SET</span> '
                '<span style="color:#00f0ff;">Set a location in the Command Center '
                'for cross-module analysis.</span>'
                '</div>',
                unsafe_allow_html=True,
            )
        with cb2:
            if st.button("Set Location", key="ctx_bar_set", use_container_width=True):
                st.session_state.current_page = "command_center"
                st.rerun()
        return

    loc = get_location()
    lat = loc["lat"]
    lon = loc["lon"]
    name = get_short_name() or f"{lat:.4f}, {lon:.4f}"

    # Try to get key metrics from data hub if available
    hub = st.session_state.get("ts_data_hub")
    metrics_html = ""
    if hub and hub.get("scores"):
        overall = hub.get("overall_score", 0)
        label = hub.get("overall_label", "")
        color = hub.get("overall_color", "#5a7090")
        details = hub.get("details", {})
        elev = details.get("center_elev", 0) or 0
        temp = details.get("temp_now", 0) or 0
        aqi = details.get("aqi", 0) or 0
        _conf_raw = hub.get("confidence", 0)
        confidence = float(_conf_raw.get("overall", 0)) if isinstance(_conf_raw, dict) else float(_conf_raw or 0)
        conf_pct = int(confidence * 100)

        # LED color based on overall score
        if overall >= 65:
            led_class = "ops-led-green"
        elif overall >= 40:
            led_class = "ops-led-amber"
        else:
            led_class = "ops-led-red"

        # Confidence bar color
        if conf_pct >= 70:
            conf_color = "#00ff88"
        elif conf_pct >= 40:
            conf_color = "#ffaa00"
        else:
            conf_color = "#ff3344"

        metrics_html = (
            f'<span class="ops-strip-item">'
            f'<span class="ops-strip-label">ELEV</span>'
            f'<span class="ops-strip-value">{elev:.0f}m</span>'
            f'</span>'
            f'<span class="ops-strip-item">'
            f'<span class="ops-strip-label">TEMP</span>'
            f'<span class="ops-strip-value">{temp:.1f}\u00b0C</span>'
            f'</span>'
            f'<span class="ops-strip-item">'
            f'<span class="ops-strip-label">AQI</span>'
            f'<span class="ops-strip-value">{aqi}</span>'
            f'</span>'
            f'<span class="ops-strip-item">'
            f'<span class="ops-strip-label">SCORE</span>'
            f'<span style="color:{color};font-weight:700;">{overall:.0f}</span>'
            f'<span style="color:#5a7090;font-size:0.65rem;">/{html_module.escape(label)}</span>'
            f'</span>'
            f'<span class="ops-strip-item" style="border-right:none;">'
            f'<span class="ops-strip-label">CONF</span>'
            f'<span style="color:{conf_color};font-weight:700;">{conf_pct}%</span>'
            f'</span>'
        )
    else:
        led_class = "ops-led-cyan"
        metrics_html = ""

    safe_name = html_module.escape(name)

    # Format coordinates as N/S E/W
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    coord_str = f"{abs(lat):.4f}{lat_dir} {abs(lon):.4f}{lon_dir}"

    st.markdown(
        f'<div class="ops-data-strip">'
        f'<span class="ops-strip-item">'
        f'<span class="{led_class} ops-led"></span>'
        f'<span style="color:#e0e8f0;font-weight:600;font-size:0.82rem;">{safe_name}</span>'
        f'</span>'
        f'<span class="ops-strip-item">'
        f'<span style="color:#00f0ff;font-size:0.75rem;">{coord_str}</span>'
        f'</span>'
        f'{metrics_html}'
        f'</div>',
        unsafe_allow_html=True,
    )
