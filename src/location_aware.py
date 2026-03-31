"""
Location Aware - Helper for migrating modules to shared location context.
Provides convenience functions that auto-populate from the shared location
while maintaining backward compatibility with per-module inputs.
"""

import streamlit as st
from src.location_context import get_location


def render_module_location_input(prefix, default_lat=41.90, default_lon=12.50):
    """Render a standard lat/lon input that auto-populates from shared context.

    When the shared location changes (via Command Center), the widget values
    are updated to match on the next render.

    Args:
        prefix: Unique widget key prefix for this module
        default_lat: Fallback latitude if no shared location
        default_lon: Fallback longitude if no shared location

    Returns:
        (lat, lon) tuple
    """
    loc = get_location()
    synced_key = f"{prefix}_synced_loc"

    if loc and loc.get("lat") is not None:
        shared_lat = loc["lat"]
        shared_lon = loc["lon"]

        # Track what shared location we last synced to.
        # If it changed, push new values into session state so widgets update.
        last_synced = st.session_state.get(synced_key)
        if last_synced != (shared_lat, shared_lon):
            st.session_state[f"{prefix}_lat"] = shared_lat
            st.session_state[f"{prefix}_lon"] = shared_lon
            st.session_state[synced_key] = (shared_lat, shared_lon)

        default_lat = shared_lat
        default_lon = shared_lon

    c1, c2 = st.columns(2)
    with c1:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key=f"{prefix}_lat",
        )
    with c2:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key=f"{prefix}_lon",
        )
    return lat, lon
