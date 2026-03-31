"""
Location Context - Shared location management for TerraScout AI.
Provides a single source of truth for the current analysis location
via st.session_state["ts_location"].
"""

import streamlit as st
from src.geocoder import forward_geocode, reverse_geocode
from src.deep_zone_analysis import ANALYSIS_PRESETS
from src.data_hub import invalidate_data_hub


# ---------------------------------------------------------------------------
# Session state key
# ---------------------------------------------------------------------------
_LOC_KEY = "ts_location"


def init_location_context():
    """Initialize the shared location context in session state."""
    if _LOC_KEY not in st.session_state:
        st.session_state[_LOC_KEY] = None


def set_location(lat, lon, source="manual"):
    """Set the shared location, reverse-geocode, and invalidate data hub cache."""
    geo = reverse_geocode(lat, lon)
    display_name = geo.get("display_name", "") if geo else ""
    address = geo.get("address", {}) if geo else {}

    st.session_state[_LOC_KEY] = {
        "lat": float(lat),
        "lon": float(lon),
        "display_name": display_name,
        "address": address,
        "source": source,
    }

    # Invalidate data hub when location changes
    invalidate_data_hub()


def get_location():
    """Return the current location dict or None."""
    return st.session_state.get(_LOC_KEY)


def has_location():
    """Check if a location is set."""
    loc = get_location()
    return loc is not None and loc.get("lat") is not None


def get_short_name():
    """Return a short display name for the current location."""
    loc = get_location()
    if not loc:
        return ""
    addr = loc.get("address", {})
    # Try city/town, then state, then country
    city = addr.get("city") or addr.get("town") or addr.get("village") or ""
    country = addr.get("country", "")
    if city and country:
        return f"{city}, {country}"
    if city:
        return city
    if country:
        return country
    # Fallback to truncated display name
    dn = loc.get("display_name", "")
    return dn[:50] + "..." if len(dn) > 50 else dn


# ---------------------------------------------------------------------------
# Location selector widget
# ---------------------------------------------------------------------------

def render_location_selector(key_prefix="loc"):
    """Render a unified location selector with search, lat/lon, presets, bookmarks.

    Returns True if location was changed.
    """
    changed = False

    # --- Search bar ---
    search_query = st.text_input(
        "Search location",
        placeholder="e.g. Roma, Italia or Central Park, New York",
        key=f"{key_prefix}_search",
    )

    c1, c2, c3 = st.columns([1.2, 1, 1])

    with c1:
        preset = st.selectbox(
            "Preset",
            list(ANALYSIS_PRESETS.keys()),
            key=f"{key_prefix}_preset",
        )

    p = ANALYSIS_PRESETS.get(preset)
    loc = get_location()
    default_lat = loc["lat"] if loc else (p.get("lat", 41.90) if p else 41.90)
    default_lon = loc["lon"] if loc else (p.get("lon", 12.50) if p else 12.50)

    # Apply preset coordinates: update session state directly so number_inputs sync
    # Compare by coordinates (not name) so re-selecting the same preset after manual
    # edits will correctly re-apply the preset values.
    last_preset_key = f"{key_prefix}_last_preset"
    if preset != "Custom" and p:
        default_lat = p["lat"]
        default_lon = p["lon"]
        last = st.session_state.get(last_preset_key)
        if last != (preset, default_lat, default_lon):
            st.session_state[f"{key_prefix}_lat"] = default_lat
            st.session_state[f"{key_prefix}_lon"] = default_lon
            st.session_state[last_preset_key] = (preset, default_lat, default_lon)
    else:
        st.session_state[last_preset_key] = None

    with c2:
        lat = st.number_input(
            "Latitude", value=default_lat, format="%.5f",
            min_value=-90.0, max_value=90.0, key=f"{key_prefix}_lat",
        )
    with c3:
        lon = st.number_input(
            "Longitude", value=default_lon, format="%.5f",
            min_value=-180.0, max_value=180.0, key=f"{key_prefix}_lon",
        )

    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("Set Location", key=f"{key_prefix}_set_btn",
                      type="primary", use_container_width=True):
            set_location(lat, lon, source="manual")
            changed = True

    with bc2:
        if search_query and st.button(
            "Search", key=f"{key_prefix}_search_btn", use_container_width=True
        ):
            results = forward_geocode(search_query.strip())
            if results:
                best = results[0]
                set_location(best["lat"], best["lon"], source="search")
                changed = True
            else:
                st.warning("No results found.")

    return changed
